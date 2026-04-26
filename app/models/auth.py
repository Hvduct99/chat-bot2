from __future__ import annotations
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(255))
    role = db.Column(db.String(20), default="student", nullable=False)  # admin | student
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    academic_year = db.Column(db.String(20))
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    faculty = db.relationship("Faculty")
    department = db.relationship("Department")

    def set_password(self, raw: str) -> None:
        self.password = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password, raw)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
