"""
Re-export tất cả models để có thể `from app.models import User, Course, ...`.
"""
from app.models.auth import User
from app.models.academic import (
    Faculty, Department, Semester, Course, ClassSection, Enrollment,
    DAY_VN, calc_grade, current_semester,
)
from app.models.content import Material, Notification
from app.models.forum import ForumCategory, ForumThread, ForumPost
from app.models.knowledge import KnowledgeDocument

__all__ = [
    "User",
    "Faculty", "Department", "Semester", "Course", "ClassSection", "Enrollment",
    "DAY_VN", "calc_grade", "current_semester",
    "Material", "Notification",
    "ForumCategory", "ForumThread", "ForumPost",
    "KnowledgeDocument",
]
