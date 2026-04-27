"""
Admin blueprint — quản lý knowledge documents (RAG sources).
Chỉ user role=admin truy cập được.
"""
from functools import wraps
import logging

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
)
from flask_login import login_required, current_user

from app.models import KnowledgeDocument
from app.services import documents as docs_svc
from app.services.documents import DocumentError

log = logging.getLogger(__name__)

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@bp.route("/knowledge")
@admin_required
def knowledge():
    """Danh sách knowledge documents + form upload."""
    items = docs_svc.list_documents()
    return render_template("admin/knowledge.html", items=items)


@bp.post("/knowledge/upload")
@admin_required
def upload():
    f = request.files.get("file")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    tags = request.form.get("tags", "").strip()
    auto_index = request.form.get("auto_index") == "on"

    try:
        doc = docs_svc.ingest_document(
            title=title,
            description=description,
            storage=f,
            uploaded_by=current_user.id,
            tags=tags,
            auto_index=auto_index,
        )
    except DocumentError as e:
        flash(str(e), "error")
        return redirect(url_for("admin.knowledge"))
    except Exception as e:
        log.exception("Upload failed")
        flash(f"Lỗi không xác định: {e}", "error")
        return redirect(url_for("admin.knowledge"))

    msg = f"Đã upload \"{doc.title}\""
    if auto_index and doc.is_indexed:
        msg += f" và index {doc.chunk_count} chunks."
    elif auto_index:
        msg += " nhưng index thất bại — thử re-index sau."
    flash(msg, "success")
    return redirect(url_for("admin.knowledge"))


@bp.post("/knowledge/<int:doc_id>/reindex")
@admin_required
def reindex(doc_id):
    doc = KnowledgeDocument.query.get_or_404(doc_id)
    try:
        n = docs_svc.reindex_document(doc)
        flash(f"Đã re-index \"{doc.title}\" — {n} chunks.", "success")
    except Exception as e:
        log.exception("Reindex failed")
        flash(f"Lỗi: {e}", "error")
    return redirect(url_for("admin.knowledge"))


@bp.post("/knowledge/<int:doc_id>/delete")
@admin_required
def delete(doc_id):
    doc = KnowledgeDocument.query.get_or_404(doc_id)
    title = doc.title
    try:
        docs_svc.delete_document(doc)
        flash(f"Đã xóa \"{title}\".", "success")
    except Exception as e:
        log.exception("Delete failed")
        flash(f"Lỗi: {e}", "error")
    return redirect(url_for("admin.knowledge"))
