"""
RAG package — pipeline retrieval-augmented generation cho UniBot.

Public API:
    from app.rag import answer, build_index, healthcheck
"""
from app.rag.pipeline import answer
from app.rag.indexer import build_index
from app.rag.ollama_client import healthcheck

__all__ = ["answer", "build_index", "healthcheck"]
