"""
WSGI entry point — gunicorn / production.
"""
from app import create_app

app = create_app()
