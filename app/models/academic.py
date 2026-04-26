from __future__ import annotations
from datetime import datetime
from typing import Optional

from app.extensions import db


DAY_VN = {
    "Monday":    "Thứ Hai",
    "Tuesday":   "Thứ Ba",
    "Wednesday": "Thứ Tư",
    "Thursday":  "Thứ Năm",
    "Friday":    "Thứ Sáu",
    "Saturday":  "Thứ Bảy",
    "Sunday":    "Chủ Nhật",
}


def calc_grade(score: float) -> str:
    """Quy đổi điểm số (0-10) sang điểm chữ."""
    thresholds = [
        (9.0, "A+"), (8.5, "A"), (8.0, "B+"), (7.0, "B"),
        (6.5, "C+"), (5.5, "C"), (5.0, "D+"), (4.0, "D"),
    ]
    for th, grade in thresholds:
        if score >= th:
            return grade
    return "F"


def current_semester() -> Optional["Semester"]:
    """Lấy học kỳ đang diễn ra (is_current=True), fallback học kỳ mới nhất."""
    sem = Semester.query.filter_by(is_current=True).first()
    if sem:
        return sem
    return Semester.query.order_by(Semester.start_date.desc()).first()


class Faculty(db.Model):
    __tablename__ = "faculties"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    total_credits = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    faculty = db.relationship("Faculty", backref="departments")


class Semester(db.Model):
    __tablename__ = "semesters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    registration_start = db.Column(db.Date, nullable=False)
    registration_end = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False, index=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    credits = db.Column(db.Integer, default=3)
    theory_hours = db.Column(db.Integer, default=0)
    practice_hours = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship("Department")


class ClassSection(db.Model):
    __tablename__ = "class_sections"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    section_code = db.Column(db.String(30), nullable=False)
    instructor_name = db.Column(db.String(100), nullable=False)
    max_students = db.Column(db.Integer, default=50)
    current_students = db.Column(db.Integer, default=0)
    room = db.Column(db.String(50))
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    start_period = db.Column(db.Integer)
    end_period = db.Column(db.Integer)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course")
    semester = db.relationship("Semester")

    @property
    def is_full(self) -> bool:
        return self.current_students >= self.max_students


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    class_section_id = db.Column(db.Integer, db.ForeignKey("class_sections.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="registered")  # registered | dropped | completed
    midterm_score = db.Column(db.Float)
    final_score = db.Column(db.Float)
    total_score = db.Column(db.Float)
    grade = db.Column(db.String(5))

    student = db.relationship("User")
    class_section = db.relationship("ClassSection")
    semester = db.relationship("Semester")

    __table_args__ = (
        db.UniqueConstraint("student_id", "class_section_id", name="uq_enrollment"),
    )
