"""
Main RAG pipeline — answer(message, history, user) → reply + sources.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Dict, List, Optional, Iterable

from flask import current_app
from langchain_core.messages import HumanMessage, AIMessage

from app.models import User
from app.rag.clients import get_llm
from app.rag.context import build_user_context
from app.rag.nlp import detect_intents
from app.rag.prompt import CHAT_PROMPT, SYSTEM_PROMPT
from app.rag.retriever import retrieve, format_retrieved, extract_sources

log = logging.getLogger(__name__)


def _format_history(history: Iterable[Dict], max_len: int) -> List:
    out = []
    for msg in history or []:
        role = msg.get("role")
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        out.append(HumanMessage(content=text) if role == "user"
                   else AIMessage(content=text))
    return out[-max_len:]


def answer(message: str,
           history: Optional[List[Dict]] = None,
           user: Optional[User] = None) -> Dict:
    """
    Sinh câu trả lời cho UniBot.

    Returns:
        {
            "reply": str,
            "sources": [{type, title, snippet}, ...],
            "intents": [str, ...],
        }
    """
    cfg = current_app.config
    message = (message or "").strip()
    if not message:
        return {"reply": "Mình chưa nhận được câu hỏi. Bạn hỏi gì nhé?",
                "sources": [], "intents": []}

    if len(message) > cfg["CHAT_MAX_INPUT_LENGTH"]:
        message = message[:cfg["CHAT_MAX_INPUT_LENGTH"]]

    intents = detect_intents(message)
    user_ctx = build_user_context(user, message)
    docs = retrieve(message)

    chain = CHAT_PROMPT | get_llm()
    try:
        response = chain.invoke({
            "system": SYSTEM_PROMPT,
            "user_ctx": user_ctx or "(Không có dữ liệu cá nhân — sinh viên chưa đăng nhập hoặc câu hỏi không yêu cầu.)",
            "retrieved": format_retrieved(docs),
            "today": datetime.now().strftime("%d/%m/%Y"),
            "history": _format_history(history, cfg["CHAT_MAX_HISTORY"]),
            "question": message,
        })
        reply = (response.content or "").strip() or \
                "Xin lỗi, mình chưa trả lời được câu này. Bạn diễn đạt lại giúp mình nhé!"
    except Exception as e:
        log.exception("LLM error")
        reply = (f"⚠️ Không kết nối được Ollama hoặc model `{cfg['OLLAMA_LLM_MODEL']}` "
                 f"chưa được pull. Lỗi: {e}")

    return {
        "reply": reply,
        "sources": extract_sources(docs),
        "intents": intents,
    }
