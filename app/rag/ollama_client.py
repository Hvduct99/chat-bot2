"""
Ollama health check + tiện ích kiểm tra model đã được pull.
"""
from __future__ import annotations
import logging
from typing import Dict, List

import requests
from flask import current_app

log = logging.getLogger(__name__)


def list_models() -> List[str]:
    """Trả về tên các model Ollama đã pull. Mảng rỗng nếu không kết nối được."""
    base = current_app.config["OLLAMA_BASE_URL"]
    try:
        r = requests.get(f"{base}/api/tags", timeout=3)
        if r.ok:
            return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception as e:
        log.warning("Cannot reach Ollama at %s: %s", base, e)
    return []


def healthcheck() -> Dict:
    """Trả về status của Ollama + model required."""
    cfg = current_app.config
    base = cfg["OLLAMA_BASE_URL"]
    required = {cfg["OLLAMA_LLM_MODEL"], cfg["OLLAMA_EMBED_MODEL"]}
    status = {"ollama": "unknown", "models": [], "missing": list(required), "base_url": base}
    try:
        r = requests.get(f"{base}/api/tags", timeout=3)
        if r.ok:
            installed = [m.get("name", "") for m in r.json().get("models", [])]
            status["ollama"] = "ok"
            status["models"] = installed
            # Match cả prefix (qwen2.5:7b vs qwen2.5:7b-instruct-q4_K_M)
            installed_set = set(installed)
            missing = []
            for needed in required:
                if needed in installed_set:
                    continue
                if any(name.startswith(needed.split(":")[0]) for name in installed):
                    continue
                missing.append(needed)
            status["missing"] = missing
        else:
            status["ollama"] = f"http {r.status_code}"
    except Exception as e:
        status["ollama"] = f"error: {e}"
    return status
