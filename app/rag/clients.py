"""
LangChain client singletons — embedding, vectorstore, LLM.
Lazy init theo config hiện tại của Flask app.
"""
from __future__ import annotations
from typing import Optional

from flask import current_app
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma


_embeddings: Optional[OllamaEmbeddings] = None
_vectorstore: Optional[Chroma] = None
_llm: Optional[ChatOllama] = None


def get_embeddings() -> OllamaEmbeddings:
    global _embeddings
    if _embeddings is None:
        cfg = current_app.config
        _embeddings = OllamaEmbeddings(
            model=cfg["OLLAMA_EMBED_MODEL"],
            base_url=cfg["OLLAMA_BASE_URL"],
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        cfg = current_app.config
        _vectorstore = Chroma(
            collection_name=cfg["CHROMA_COLLECTION"],
            embedding_function=get_embeddings(),
            persist_directory=cfg["CHROMA_DIR"],
        )
    return _vectorstore


def get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        cfg = current_app.config
        _llm = ChatOllama(
            model=cfg["OLLAMA_LLM_MODEL"],
            base_url=cfg["OLLAMA_BASE_URL"],
            temperature=cfg["OLLAMA_TEMPERATURE"],
            num_ctx=cfg["OLLAMA_NUM_CTX"],
        )
    return _llm


def reset_clients() -> None:
    """Reset singleton — gọi khi cần re-init (vd: build lại index)."""
    global _embeddings, _vectorstore, _llm
    _embeddings = None
    _vectorstore = None
    _llm = None
