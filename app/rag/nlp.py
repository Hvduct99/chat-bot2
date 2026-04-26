"""
Tiền xử lý NLP tiếng Việt — chuẩn hóa unicode, tách từ, phát hiện intent.
"""
from __future__ import annotations
import re
from typing import List
from unidecode import unidecode

try:
    from underthesea import word_tokenize as _uts_tokenize, text_normalize
    _HAS_UTS = True
except ImportError:
    _HAS_UTS = False


# Nhóm từ khóa → intent (label)
KEYWORD_GROUPS: dict[str, List[str]] = {
    "courses": [
        "môn học", "môn", "đăng ký", "tín chỉ", "lịch học", "lịch",
        "giảng viên", "thầy", "cô giáo", "lớp", "tiết", "phòng",
        "học phần", "register", "course",
    ],
    "materials": [
        "tài liệu", "document", "file", "bài giảng", "slide", "pdf",
        "download", "tải", "ebook", "giáo trình",
    ],
    "my_schedule": [
        "của tôi", "của em", "của mình", "đã đăng ký", "lịch của",
        "môn của", "tôi đăng ký", "em đăng ký", "mình đăng ký",
        "học gì", "đang học",
    ],
    "grades": ["điểm", "kết quả", "grade", "gpa", "trung bình", "xếp loại"],
    "notifications": ["thông báo", "tin tức", "mới nhất", "notification"],
}


def normalize_vi(text: str) -> str:
    """Chuẩn hóa diacritics + gộp khoảng trắng."""
    if not text:
        return ""
    if _HAS_UTS:
        try:
            text = text_normalize(text)
        except Exception:
            pass
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """Bỏ dấu + lower — để match từ khóa không phụ thuộc dấu."""
    return unidecode((text or "").lower())


def tokenize_vi(text: str) -> List[str]:
    """Tách từ tiếng Việt — fallback split() khi không có underthesea."""
    if _HAS_UTS:
        try:
            return _uts_tokenize(text, format="text").split()
        except Exception:
            pass
    return text.split()


def detect_intents(message: str) -> List[str]:
    """Trả về danh sách intent đụng tới (multi-label, dựa keyword fold dấu)."""
    folded = fold(message)
    hits: List[str] = []
    for group, keywords in KEYWORD_GROUPS.items():
        if any(fold(kw) in folded for kw in keywords):
            hits.append(group)
    return hits
