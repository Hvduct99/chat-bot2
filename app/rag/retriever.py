"""
Retriever — vector search wrappers.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from flask import current_app
from langchain_core.documents import Document

from app.rag.clients import get_vectorstore
from app.rag.nlp import normalize_vi

log = logging.getLogger(__name__)


def retrieve(query: str, k: Optional[int] = None) -> List[Document]:
    """Trả về top-k document khớp query. Trả mảng rỗng khi lỗi."""
    if k is None:
        k = current_app.config["RAG_TOP_K"]
    try:
        return get_vectorstore().similarity_search(normalize_vi(query), k=k)
    except Exception as e:
        log.error("Retrieve failed: %s", e)
        return []


def format_retrieved(docs: List[Document]) -> str:
    """Render docs thành text để nhét vào prompt."""
    if not docs:
        return "(Không tìm thấy thông tin liên quan trong cơ sở tri thức.)"
    chunks = []
    for i, d in enumerate(docs, 1):
        meta = " ".join(
            f"{k}={d.metadata[k]}"
            for k in ("type", "code", "section_code", "title", "topic")
            if k in d.metadata
        )
        chunks.append(f"[#{i}] {meta}\n{d.page_content}")
    return "\n\n".join(chunks)


def extract_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    """Sources hiển thị trên UI — dedup theo title/code/section_code."""
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for d in docs:
        key = d.metadata.get("title") or d.metadata.get("code") \
              or d.metadata.get("section_code")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({
            "type": d.metadata.get("type"),
            "title": key,
            "snippet": d.page_content[:140],
        })
    return out
