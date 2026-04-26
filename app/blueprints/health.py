"""
Healthcheck endpoints — kiểm tra app, Ollama, vector store.
Dùng cho Docker healthcheck + monitoring.
"""
from flask import Blueprint, jsonify

from app.rag import healthcheck

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz():
    """Liveness — app đang chạy."""
    return jsonify({"status": "ok"}), 200


@bp.get("/readyz")
def readyz():
    """Readiness — Ollama có sẵn + model đã pull."""
    h = healthcheck()
    ready = h["ollama"] == "ok" and not h["missing"]
    code = 200 if ready else 503
    return jsonify({"ready": ready, **h}), code


@bp.get("/api/health")
def api_health():
    """Alias cũ — vẫn hoạt động."""
    return jsonify(healthcheck())
