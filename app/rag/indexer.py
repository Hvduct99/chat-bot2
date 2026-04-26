"""
Indexer — đọc DB, chuẩn hóa, split thành chunk, embed và lưu vào ChromaDB.
"""
from __future__ import annotations
import logging
from typing import List, Tuple

from flask import current_app
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models import (
    Course, ClassSection, Material, Notification, Semester,
    ForumThread, current_semester, DAY_VN,
)
from app.rag.clients import get_embeddings, get_vectorstore, reset_clients
from app.rag.nlp import normalize_vi

log = logging.getLogger(__name__)


def _doc(text: str, **meta) -> Document:
    return Document(page_content=normalize_vi(text), metadata=meta)


# ---------------------------------------------------------------------------
# Document collectors — mỗi nhóm một hàm
# ---------------------------------------------------------------------------

def _collect_courses() -> List[Document]:
    docs = []
    for c in Course.query.all():
        dept = c.department.name if c.department else ""
        text = (
            f"MÔN HỌC [{c.code}] {c.name}\n"
            f"Số tín chỉ: {c.credits}. "
            f"Lý thuyết {c.theory_hours}h, thực hành {c.practice_hours}h. "
            f"Khoa/Ngành: {dept}.\n"
            f"Mô tả: {c.description or ''}"
        )
        docs.append(_doc(text, type="course", code=c.code, course_id=c.id, name=c.name))
    return docs


def _collect_class_sections() -> List[Document]:
    sem = current_semester()
    if not sem:
        return []
    docs = []
    for s in ClassSection.query.filter_by(semester_id=sem.id).all():
        day = DAY_VN.get(s.day_of_week, s.day_of_week)
        text = (
            f"LỚP HỌC PHẦN [{s.section_code}] — môn {s.course.code} {s.course.name} ({s.course.credits} TC).\n"
            f"Giảng viên: {s.instructor_name}. "
            f"{day}, tiết {s.start_period}-{s.end_period} "
            f"({s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}). "
            f"Phòng {s.room}. "
            f"Sĩ số {s.current_students}/{s.max_students}. "
            f"Trạng thái: {'mở' if s.status == 'open' else 'đóng'}. "
            f"Học kỳ {sem.name} {sem.academic_year}."
        )
        docs.append(_doc(
            text, type="class_section", section_code=s.section_code,
            course_code=s.course.code, instructor=s.instructor_name,
            semester=f"{sem.name} {sem.academic_year}",
        ))
    return docs


def _collect_semesters() -> List[Document]:
    docs = []
    for s in Semester.query.all():
        text = (
            f"HỌC KỲ {s.name} năm học {s.academic_year}.\n"
            f"Thời gian học: {s.start_date} đến {s.end_date}.\n"
            f"Đăng ký tín chỉ: {s.registration_start} đến {s.registration_end}.\n"
            f"{'Đây là học kỳ hiện tại.' if s.is_current else ''}"
        )
        docs.append(_doc(text, type="semester", name=s.name, year=s.academic_year))
    return docs


def _collect_materials() -> List[Document]:
    docs = []
    for m in Material.query.filter_by(status="active").all():
        c = m.course
        text = (
            f"TÀI LIỆU \"{m.title}\" của môn [{c.code}] {c.name}.\n"
            f"Loại: {m.file_type}. Lượt tải: {m.download_count}.\n"
            f"Mô tả: {m.description or ''}\n"
            f"Đường dẫn tải: {m.file_path}"
        )
        docs.append(_doc(text, type="material", title=m.title, course_code=c.code))
    return docs


def _collect_notifications() -> List[Document]:
    docs = []
    rows = (Notification.query
            .order_by(Notification.is_pinned.desc(), Notification.created_at.desc())
            .all())
    for n in rows:
        text = (
            f"THÔNG BÁO ({n.type}): {n.title}\n"
            f"Ngày: {n.created_at.strftime('%d/%m/%Y')}.\n"
            f"Nội dung: {n.content}"
        )
        docs.append(_doc(text, type="notification", title=n.title))
    return docs


def _collect_forum_threads() -> List[Document]:
    docs = []
    for t in ForumThread.query.all():
        text = (
            f"BÀI VIẾT DIỄN ĐÀN — chuyên mục \"{t.category.name}\":\n"
            f"Tiêu đề: {t.title}\n{t.content}"
        )
        docs.append(_doc(text, type="forum_thread", title=t.title,
                         category=t.category.name))
    return docs


def _static_knowledge() -> List[Document]:
    """Knowledge cứng không có trong DB — quy chế, công thức, sitemap."""
    items: List[Tuple[str, dict]] = [
        ("Cách đăng ký tín chỉ trên UniReg:\n"
         "1. Đăng nhập tại /auth/login.\n"
         "2. Vào trang /student/registration.\n"
         "3. Tìm môn học theo mã hoặc tên, xem các lớp đang mở.\n"
         "4. Bấm \"Đăng ký\" — hệ thống tự kiểm tra trùng lịch, lớp đầy, trùng môn.\n"
         "5. Muốn hủy: bấm \"Hủy\" bên cạnh môn đã đăng ký.",
         {"type": "guide", "topic": "registration"}),
        ("Công thức tính điểm môn học:\n"
         "Điểm trung bình = Điểm giữa kỳ × 40% + Điểm cuối kỳ × 60%.\n"
         "Xếp loại điểm chữ:\n"
         "- A+: ≥ 9.0\n- A: ≥ 8.5\n- B+: ≥ 8.0\n- B: ≥ 7.0\n"
         "- C+: ≥ 6.5\n- C: ≥ 5.5\n- D+: ≥ 5.0\n- D: ≥ 4.0\n- F: < 4.0",
         {"type": "guide", "topic": "grading"}),
        ("Bản đồ trang UniReg cho sinh viên:\n"
         "- /student/dashboard — tổng quan môn đã DK, GPA, thông báo.\n"
         "- /student/registration — đăng ký tín chỉ.\n"
         "- /student/schedule — thời khóa biểu.\n"
         "- /student/materials — tài liệu học tập.\n"
         "- /student/grades — điểm và kết quả.\n"
         "- /student/profile — hồ sơ cá nhân.\n"
         "- / — diễn đàn sinh viên.\n"
         "- /chatbot — trang chat đầy đủ với UniBot.",
         {"type": "guide", "topic": "sitemap"}),
    ]
    return [_doc(text, **meta) for text, meta in items]


COLLECTORS = [
    _collect_courses,
    _collect_class_sections,
    _collect_semesters,
    _collect_materials,
    _collect_notifications,
    _collect_forum_threads,
    _static_knowledge,
]


def collect_documents() -> List[Document]:
    """Gọi tất cả collectors."""
    docs: List[Document] = []
    for fn in COLLECTORS:
        items = fn()
        log.info("Collected %d docs from %s", len(items), fn.__name__)
        docs.extend(items)
    return docs


# ---------------------------------------------------------------------------
# Build index
# ---------------------------------------------------------------------------

def build_index() -> int:
    """Reset collection và rebuild toàn bộ vector store. Trả về số chunks đã index."""
    cfg = current_app.config
    docs = collect_documents()
    log.info("Total documents: %d", len(docs))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["RAG_CHUNK_SIZE"],
        chunk_overlap=cfg["RAG_CHUNK_OVERLAP"],
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    log.info("After splitting: %d chunks", len(chunks))

    # Reset collection cũ
    vs = get_vectorstore()
    try:
        vs.delete_collection()
        log.info("Cleared existing collection")
    except Exception as e:
        log.warning("Cannot delete collection: %s", e)

    reset_clients()  # buộc khởi tạo lại
    vs = get_vectorstore()
    vs.add_documents(chunks)
    log.info("Indexed %d chunks into ChromaDB at %s", len(chunks), cfg["CHROMA_DIR"])
    return len(chunks)
