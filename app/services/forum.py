"""
Forum service — query thống kê, tạo thread/post.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from sqlalchemy import func

from app.extensions import db
from app.models import ForumCategory, ForumThread, ForumPost


@dataclass
class CategoryStats:
    threads: int
    posts: int
    last_thread: Optional[ForumThread]


def category_stats() -> Dict[int, CategoryStats]:
    """Map category_id → stats. Một query gom + một query last-thread."""
    rows = (db.session.query(
                ForumThread.category_id,
                func.count(ForumThread.id).label("threads"),
            )
            .group_by(ForumThread.category_id).all())
    threads_map = {cid: t for cid, t in rows}

    posts_rows = (db.session.query(
                    ForumThread.category_id,
                    func.count(ForumPost.id).label("posts"),
                  )
                  .outerjoin(ForumPost, ForumPost.thread_id == ForumThread.id)
                  .group_by(ForumThread.category_id).all())
    posts_map = {cid: p for cid, p in posts_rows}

    out: Dict[int, CategoryStats] = {}
    for cat in ForumCategory.query.all():
        last = (ForumThread.query
                .filter_by(category_id=cat.id)
                .order_by(ForumThread.updated_at.desc()).first())
        threads = threads_map.get(cat.id, 0)
        posts = posts_map.get(cat.id, 0) + threads  # bài đăng = thread + post
        out[cat.id] = CategoryStats(threads=threads, posts=posts, last_thread=last)
    return out


def create_thread(category_id: int, user_id: int, title: str, content: str) -> ForumThread:
    t = ForumThread(category_id=category_id, user_id=user_id,
                    title=title.strip(), content=content.strip())
    db.session.add(t)
    db.session.commit()
    return t


def create_post(thread_id: int, user_id: int, content: str) -> ForumPost:
    p = ForumPost(thread_id=thread_id, user_id=user_id, content=content.strip())
    db.session.add(p)
    # đụng updated_at của thread để bump bài cuối
    t = db.session.get(ForumThread, thread_id)
    if t:
        t.updated_at = db.func.now()
    db.session.commit()
    return p


def increment_views(thread: ForumThread) -> None:
    thread.views = (thread.views or 0) + 1
    db.session.commit()
