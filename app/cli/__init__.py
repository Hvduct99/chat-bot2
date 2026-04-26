"""
CLI commands — đăng ký vào Flask app:
    flask seed       → khởi tạo DB + dữ liệu mẫu
    flask ingest     → build vector index từ DB
    flask check      → kiểm tra Ollama + models
"""
import logging

import click
from flask import Flask
from flask.cli import with_appcontext

log = logging.getLogger(__name__)


@click.command("seed")
@click.option("--reset", is_flag=True, help="Drop & recreate tables trước khi seed.")
@with_appcontext
def seed_cmd(reset: bool):
    """Khởi tạo DB + dữ liệu mẫu."""
    from app.cli.seed_data import run
    run(reset=reset)


@click.command("ingest")
@with_appcontext
def ingest_cmd():
    """Build/rebuild vector index từ DB."""
    from app.rag import build_index
    click.echo("→ Đang xây dựng vector index...")
    n = build_index()
    click.echo(f"✓ Đã index {n} chunks vào ChromaDB.")


@click.command("check")
@with_appcontext
def check_cmd():
    """Kiểm tra Ollama + models."""
    from app.rag import healthcheck
    h = healthcheck()
    click.echo(f"Ollama:    {h['ollama']}")
    click.echo(f"Base URL:  {h['base_url']}")
    click.echo(f"Models:    {', '.join(h['models']) or '(none)'}")
    if h["missing"]:
        click.echo(f"⚠ Missing: {', '.join(h['missing'])}", err=True)
        raise SystemExit(1)
    click.echo("✓ All required models are present.")


def register_cli(app: Flask) -> None:
    app.cli.add_command(seed_cmd)
    app.cli.add_command(ingest_cmd)
    app.cli.add_command(check_cmd)
