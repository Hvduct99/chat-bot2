"""
Chat service — wrapper mỏng quanh RAG pipeline.
Tách lớp này để blueprint không phụ thuộc trực tiếp vào module rag.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from app.models import User
from app.rag import answer as _rag_answer


def answer(message: str,
           history: Optional[List[Dict]] = None,
           user: Optional[User] = None) -> Dict:
    return _rag_answer(message=message, history=history, user=user)
