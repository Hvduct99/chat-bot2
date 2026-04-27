"""
KnowledgeDocument — file (PDF/DOCX/TXT/MD) admin upload để bổ sung kho RAG.
Được index vào ChromaDB qua `flask ingest` hoặc tự động sau khi upload.
"""
from __future__ import annotations
from datetime import datetime

from app.extensions import db


class KnowledgeDocument(db.Model):
    __tablename__ = "knowledge_documents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(500), nullable=False)       # original name
    stored_path = db.Column(db.String(500), nullable=False)    # path on disk
    file_type = db.Column(db.String(20), nullable=False)        # pdf | docx | txt | md
    file_size = db.Column(db.Integer, default=0)                # bytes
    char_count = db.Column(db.Integer, default=0)               # tổng ký tự đã extract
    chunk_count = db.Column(db.Integer, default=0)              # số chunk sau split
    tags = db.Column(db.String(500))                            # csv tags

    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    indexed_at = db.Column(db.DateTime)                         # null = chưa index
    status = db.Column(db.String(20), default="active")         # active | archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship("User")

    @property
    def is_indexed(self) -> bool:
        return self.indexed_at is not None
