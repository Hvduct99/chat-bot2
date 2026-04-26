"""
Đăng ký tất cả blueprints vào Flask app.
"""
from flask import Flask

from app.blueprints.auth import bp as auth_bp
from app.blueprints.forum import bp as forum_bp
from app.blueprints.student import bp as student_bp
from app.blueprints.chat import bp as chat_bp
from app.blueprints.health import bp as health_bp


def register_blueprints(app: Flask) -> None:
    for bp in (auth_bp, forum_bp, student_bp, chat_bp, health_bp):
        app.register_blueprint(bp)
