"""
Application factory.
"""
from __future__ import annotations
import logging
import markdown as md
from datetime import datetime
from flask import Flask, redirect, url_for, render_template

from app.extensions import db, login_manager
from app.settings import BaseConfig, get_config
from app.log_config import configure_logging

log = logging.getLogger(__name__)


def create_app(config: type[BaseConfig] | None = None) -> Flask:
    """Tạo Flask app theo cấu trúc factory."""
    cfg = config or get_config()
    configure_logging(cfg.LOG_LEVEL)

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(cfg)

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _register_root_routes(app)

    log.info("App created (env=%s, ollama=%s, llm=%s)",
             app.config.get("DEBUG") and "dev" or "prod",
             app.config["OLLAMA_BASE_URL"],
             app.config["OLLAMA_LLM_MODEL"])
    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(uid: str):
        return db.session.get(User, int(uid))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints import register_blueprints
    register_blueprints(app)


def _register_cli(app: Flask) -> None:
    from app.cli import register_cli
    register_cli(app)


def _register_template_helpers(app: Flask) -> None:
    from app.models import ForumCategory

    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": app.config["APP_NAME"],
            "nav_categories": ForumCategory.query.order_by(ForumCategory.sort_order).all(),
        }

    @app.template_filter("dt")
    def format_dt(value, fmt="%d/%m/%Y %H:%M"):
        return value.strftime(fmt) if value else ""

    @app.template_filter("relative")
    def relative_time(value):
        if not value:
            return ""
        delta = datetime.utcnow() - value
        s = int(delta.total_seconds())
        if s < 60:    return f"{s}s trước"
        if s < 3600:  return f"{s // 60} phút trước"
        if s < 86400: return f"{s // 3600} giờ trước"
        return f"{s // 86400} ngày trước"

    @app.template_filter("md")
    def markdown_filter(text):
        return md.markdown(text or "", extensions=["nl2br", "fenced_code"])


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Unhandled error: %s", e)
        return render_template("errors/500.html"), 500


def _register_root_routes(app: Flask) -> None:
    @app.route("/")
    def home():
        return redirect(url_for("forum.index"))
