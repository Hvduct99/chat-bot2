from __future__ import annotations
from datetime import datetime

from app.extensions import db


class ForumCategory(db.Model):
    __tablename__ = "forum_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    description = db.Column(db.String(400))
    icon = db.Column(db.String(50), default="fa-comments")
    color = db.Column(db.String(20), default="blue")
    sort_order = db.Column(db.Integer, default=0, index=True)


class ForumThread(db.Model):
    __tablename__ = "forum_threads"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("forum_categories.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, index=True)

    category = db.relationship("ForumCategory", backref="threads")
    user = db.relationship("User")


class ForumPost(db.Model):
    __tablename__ = "forum_posts"
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("forum_threads.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    thread = db.relationship("ForumThread", backref="posts")
    user = db.relationship("User")
