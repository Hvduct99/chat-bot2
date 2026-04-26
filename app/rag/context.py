"""
Dynamic context builder — lấy dữ liệu live từ DB theo intent của câu hỏi.
Dữ liệu này (lịch của tôi, điểm cá nhân...) thay đổi liên tục nên không đưa vào vector store.
"""
from __future__ import annotations
from typing import List, Optional

from app.models import (
    User, Enrollment, current_semester, DAY_VN,
)
from app.rag.nlp import detect_intents


def build_user_context(user: Optional[User], message: str) -> str:
    """Sinh khối context riêng cho sinh viên đang hỏi."""
    parts: List[str] = []
    intents = detect_intents(message)

    if user and user.is_student:
        parts.append(_user_profile_block(user))

    sem = current_semester()
    if sem:
        parts.append(_semester_block(sem))

    if user and user.is_student and sem and "my_schedule" in intents:
        block = _my_enrollments_block(user.id, sem.id)
        if block:
            parts.append(block)

    if user and user.is_student and "grades" in intents:
        block = _my_grades_block(user.id)
        if block:
            parts.append(block)

    return "\n\n".join(parts)


def _user_profile_block(user: User) -> str:
    dept = user.department.name if user.department else "—"
    fac = user.faculty.name if user.faculty else "—"
    return (
        "THÔNG TIN SINH VIÊN HIỆN TẠI:\n"
        f"- Họ tên: {user.full_name}\n"
        f"- MSSV: {user.student_code or 'N/A'}\n"
        f"- Khoa: {fac}\n- Ngành: {dept}"
    )


def _semester_block(sem) -> str:
    return (
        f"HỌC KỲ HIỆN TẠI: {sem.name} {sem.academic_year}\n"
        f"- Thời gian học: {sem.start_date} đến {sem.end_date}\n"
        f"- Đăng ký tín chỉ: {sem.registration_start} đến {sem.registration_end}"
    )


def _my_enrollments_block(student_id: int, semester_id: int) -> str:
    rows = (Enrollment.query
            .filter_by(student_id=student_id, semester_id=semester_id, status="registered")
            .all())
    if not rows:
        return ""
    lines = [f"MÔN BẠN ĐÃ ĐĂNG KÝ HỌC KỲ NÀY ({len(rows)} môn):"]
    total_credits = 0
    for e in rows:
        cs = e.class_section
        c = cs.course
        day = DAY_VN.get(cs.day_of_week, cs.day_of_week)
        lines.append(
            f"- [{c.code}] {c.name} ({c.credits} TC) | Lớp {cs.section_code} "
            f"| GV: {cs.instructor_name} | {day} tiết {cs.start_period}-{cs.end_period} "
            f"| Phòng {cs.room}"
        )
        total_credits += c.credits
    lines.append(f"Tổng: {len(rows)} môn, {total_credits} tín chỉ.")
    return "\n".join(lines)


def _my_grades_block(student_id: int) -> str:
    rows = (Enrollment.query
            .filter(Enrollment.student_id == student_id,
                    Enrollment.total_score.isnot(None))
            .all())
    if not rows:
        return ""
    lines = ["KẾT QUẢ HỌC TẬP CỦA BẠN:"]
    for e in rows:
        c = e.class_section.course
        lines.append(
            f"- [{c.code}] {c.name} ({c.credits} TC) | GK: {e.midterm_score or '-'}"
            f" | CK: {e.final_score or '-'} | TB: {e.total_score or '-'}"
            f" | Xếp loại: {e.grade or '-'}"
        )
    return "\n".join(lines)
