"""
Knowledge document service — upload, lưu file, parse, đẩy vào ChromaDB.
"""
from __future__ import annotations
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from flask import current_app
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import KnowledgeDocument
from app.rag.clients import get_vectorstore
from app.rag.loaders import (
    SUPPORTED_EXTS, UnsupportedFileType,
    detect_type, extract_text,
)
from app.rag.nlp import normalize_vi

log = logging.getLogger(__name__)

MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB


class DocumentError(Exception):
    """Lỗi nghiệp vụ khi upload/parse document."""


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def _uploads_dir() -> Path:
    d = Path(current_app.config["DATA_DIR"]) / "uploads" / "knowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_uploaded_file(storage: FileStorage) -> tuple[Path, str, int]:
    """Validate + lưu file lên đĩa. Trả về (path, file_type, size)."""
    if not storage or not storage.filename:
        raise DocumentError("Không có file được tải lên.")

    try:
        ext = detect_type(storage.filename)
    except UnsupportedFileType as e:
        raise DocumentError(str(e)) from e

    # Đọc rồi seek về 0 để lưu
    storage.stream.seek(0, 2)  # tới cuối
    size = storage.stream.tell()
    storage.stream.seek(0)
    if size > MAX_FILE_BYTES:
        raise DocumentError(
            f"File quá lớn ({size / 1024 / 1024:.1f} MB). "
            f"Tối đa {MAX_FILE_BYTES // 1024 // 1024} MB."
        )
    if size == 0:
        raise DocumentError("File rỗng.")

    safe_name = secure_filename(storage.filename) or f"file{ext}"
    unique = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    target = _uploads_dir() / unique
    storage.save(str(target))
    log.info("Saved upload: %s (%d bytes)", target, size)
    return target, ext.lstrip("."), size


def ingest_document(
    *,
    title: str,
    description: Optional[str],
    storage: FileStorage,
    uploaded_by: int,
    tags: Optional[str] = None,
    auto_index: bool = True,
) -> KnowledgeDocument:
    """
    Lưu file + tạo record + (tùy chọn) index ngay vào vector store.
    """
    title = (title or "").strip()
    if not title:
        raise DocumentError("Cần nhập tiêu đề tài liệu.")

    path, file_type, size = save_uploaded_file(storage)

    # Extract text trước khi commit DB để fail-fast nếu file hỏng
    try:
        text = extract_text(path)
    except Exception as e:
        path.unlink(missing_ok=True)
        log.exception("Extract failed")
        raise DocumentError(f"Không đọc được nội dung file: {e}") from e

    if not text.strip():
        path.unlink(missing_ok=True)
        raise DocumentError("File không có nội dung text trích xuất được.")

    doc = KnowledgeDocument(
        title=title,
        description=(description or "").strip() or None,
        filename=storage.filename,
        stored_path=str(path),
        file_type=file_type,
        file_size=size,
        char_count=len(text),
        tags=(tags or "").strip() or None,
        uploaded_by=uploaded_by,
    )
    db.session.add(doc)
    db.session.commit()

    if auto_index:
        try:
            chunks = index_document(doc, text=text)
            doc.chunk_count = chunks
            doc.indexed_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            log.exception("Auto-index failed for doc %d", doc.id)
            # Vẫn giữ record để admin có thể re-index thủ công
    return doc


# ---------------------------------------------------------------------------
# Indexing — đẩy vào ChromaDB
# ---------------------------------------------------------------------------

def _chunks_for(doc: KnowledgeDocument, text: str) -> List[Document]:
    """Split text → langchain Document với metadata trỏ về KnowledgeDocument."""
    cfg = current_app.config
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["RAG_CHUNK_SIZE"],
        chunk_overlap=cfg["RAG_CHUNK_OVERLAP"],
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    parts = splitter.split_text(normalize_vi(text))
    return [
        Document(
            page_content=p,
            metadata={
                "type": "knowledge",
                "title": doc.title,
                "doc_id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "tags": doc.tags or "",
            },
        )
        for p in parts if p.strip()
    ]


def index_document(doc: KnowledgeDocument, *, text: Optional[str] = None) -> int:
    """Index một document vào ChromaDB. Trả về số chunks đã thêm."""
    if text is None:
        text = extract_text(doc.stored_path)
    chunks = _chunks_for(doc, text)
    if not chunks:
        return 0

    vs = get_vectorstore()
    # Xóa chunk cũ của doc này (tránh duplicate khi re-index)
    try:
        vs.delete(where={"doc_id": doc.id})
    except Exception:
        pass

    vs.add_documents(chunks)
    log.info("Indexed %d chunks for doc #%d (%s)", len(chunks), doc.id, doc.title)
    return len(chunks)


def reindex_document(doc: KnowledgeDocument) -> int:
    """Re-index một document đã có (sau khi sửa nội dung file)."""
    n = index_document(doc)
    doc.chunk_count = n
    doc.indexed_at = datetime.utcnow()
    db.session.commit()
    return n


def delete_document(doc: KnowledgeDocument) -> None:
    """Xóa file, xóa chunks khỏi ChromaDB, xóa record DB."""
    try:
        get_vectorstore().delete(where={"doc_id": doc.id})
    except Exception as e:
        log.warning("Cannot delete chunks for doc %d: %s", doc.id, e)

    try:
        Path(doc.stored_path).unlink(missing_ok=True)
    except Exception as e:
        log.warning("Cannot remove file %s: %s", doc.stored_path, e)

    db.session.delete(doc)
    db.session.commit()


def list_documents() -> List[KnowledgeDocument]:
    return (KnowledgeDocument.query
            .order_by(KnowledgeDocument.created_at.desc()).all())
