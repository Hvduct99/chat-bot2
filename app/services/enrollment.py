"""
Enrollment service — đóng gói nghiệp vụ đăng ký/hủy tín chỉ.
Tách khỏi blueprint để dễ test & tái sử dụng.
"""
from __future__ import annotations
from dataclasses import dataclass

from app.extensions import db
from app.models import ClassSection, Enrollment, current_semester


class EnrollmentError(Exception):
    """Lỗi nghiệp vụ khi đăng ký môn."""


@dataclass
class EnrollResult:
    section: ClassSection
    enrollment: Enrollment


def enroll(student_id: int, section_id: int) -> EnrollResult:
    """
    Đăng ký một lớp cho sinh viên. Raise EnrollmentError nếu vi phạm.

    Quy tắc:
    - Lớp phải thuộc học kỳ hiện tại.
    - Sinh viên chưa đăng ký lớp này.
    - Lớp chưa đầy.
    - Sinh viên chưa đăng ký lớp khác cho cùng môn (course_id).
    """
    sem = current_semester()
    if not sem:
        raise EnrollmentError("Hiện không có học kỳ đang hoạt động.")

    cs = db.session.get(ClassSection, section_id)
    if not cs:
        raise EnrollmentError("Không tìm thấy lớp học phần.")

    if cs.semester_id != sem.id:
        raise EnrollmentError("Lớp không thuộc học kỳ hiện tại.")

    existing = Enrollment.query.filter_by(
        student_id=student_id, class_section_id=cs.id
    ).first()
    if existing and existing.status == "registered":
        raise EnrollmentError("Bạn đã đăng ký lớp này rồi.")

    if cs.is_full:
        raise EnrollmentError("Lớp đã đầy.")

    same_course = (db.session.query(Enrollment)
                   .join(ClassSection)
                   .filter(Enrollment.student_id == student_id,
                           Enrollment.semester_id == sem.id,
                           Enrollment.status == "registered",
                           ClassSection.course_id == cs.course_id)
                   .first())
    if same_course:
        raise EnrollmentError(f"Bạn đã đăng ký lớp khác cho môn {cs.course.code}.")

    if existing:
        existing.status = "registered"
        enrollment = existing
    else:
        enrollment = Enrollment(
            student_id=student_id,
            class_section_id=cs.id,
            semester_id=sem.id,
            status="registered",
        )
        db.session.add(enrollment)
    cs.current_students += 1
    db.session.commit()
    return EnrollResult(section=cs, enrollment=enrollment)


def drop(student_id: int, section_id: int) -> ClassSection:
    """Hủy đăng ký. Raise EnrollmentError nếu không tồn tại."""
    e = Enrollment.query.filter_by(
        student_id=student_id, class_section_id=section_id, status="registered"
    ).first()
    if not e:
        raise EnrollmentError("Bạn chưa đăng ký lớp này.")

    e.status = "dropped"
    if e.class_section.current_students > 0:
        e.class_section.current_students -= 1
    db.session.commit()
    return e.class_section
