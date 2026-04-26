"""
Chat blueprint — endpoint API và trang chat full-screen.
"""
import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user

from app.services.chat import answer

log = logging.getLogger(__name__)

bp = Blueprint("chat", __name__)


@bp.route("/chatbot")
def page():
    """Trang chat full-screen."""
    return render_template("chatbot.html")


@bp.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Thiếu nội dung tin nhắn."}), 400

    history = data.get("history") or []
    user = current_user if current_user.is_authenticated else None

    try:
        result = answer(message=message, history=history, user=user)
    except Exception as e:
        log.exception("Chat error")
        return jsonify({"error": f"Lỗi xử lý: {e}"}), 500

    return jsonify(result)
