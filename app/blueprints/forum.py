from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import (
    ForumCategory, ForumThread, User, Notification, current_semester,
)
from app.services import forum as forum_svc

bp = Blueprint("forum", __name__)


@bp.route("/")
def index():
    cats = ForumCategory.query.order_by(ForumCategory.sort_order).all()
    stats = forum_svc.category_stats()
    pinned_notifs = (Notification.query
                     .order_by(Notification.is_pinned.desc(),
                               Notification.created_at.desc())
                     .limit(3).all())
    recent_threads = (ForumThread.query
                      .order_by(ForumThread.updated_at.desc()).limit(5).all())

    return render_template(
        "forum/index.html",
        categories=cats,
        stats=stats,
        online_count=User.query.filter_by(status="active").count(),
        total_threads=ForumThread.query.count(),
        total_users=User.query.count(),
        pinned_notifs=pinned_notifs,
        recent_threads=recent_threads,
        current_sem=current_semester(),
    )


@bp.route("/c/<slug>")
def category(slug):
    cat = ForumCategory.query.filter_by(slug=slug).first_or_404()
    page = request.args.get("page", 1, type=int)
    pagination = (ForumThread.query.filter_by(category_id=cat.id)
                  .order_by(ForumThread.is_pinned.desc(),
                            ForumThread.updated_at.desc())
                  .paginate(page=page, per_page=15, error_out=False))
    return render_template("forum/category.html",
                           category=cat, pagination=pagination)


@bp.route("/t/<int:thread_id>", methods=["GET", "POST"])
def thread(thread_id):
    t = ForumThread.query.get_or_404(thread_id)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Vui lòng đăng nhập để trả lời.", "error")
            return redirect(url_for("auth.login"))
        content = request.form.get("content", "").strip()
        if content:
            forum_svc.create_post(t.id, current_user.id, content)
            flash("Đã đăng phản hồi.", "success")
        return redirect(url_for("forum.thread", thread_id=t.id))

    forum_svc.increment_views(t)
    posts = sorted(t.posts, key=lambda p: p.created_at)
    return render_template("forum/thread.html", thread=t, posts=posts)


@bp.route("/c/<slug>/new", methods=["GET", "POST"])
@login_required
def new_thread(slug):
    cat = ForumCategory.query.filter_by(slug=slug).first_or_404()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Cần nhập tiêu đề và nội dung.", "error")
        else:
            t = forum_svc.create_thread(cat.id, current_user.id, title, content)
            return redirect(url_for("forum.thread", thread_id=t.id))
    return render_template("forum/new_thread.html", category=cat)
