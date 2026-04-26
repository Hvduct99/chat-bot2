"""
Cấu hình ứng dụng — đọc từ biến môi trường (.env), có default cho dev.
Tách thành 3 profile: BaseConfig, DevConfig, ProductionConfig.
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "chroma").mkdir(exist_ok=True)
(DATA_DIR / "uploads").mkdir(exist_ok=True)


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class BaseConfig:
    # ---- Flask ----
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(DATA_DIR / 'unireg.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    JSON_AS_ASCII = False  # giữ tiếng Việt trong JSON

    # ---- App metadata ----
    APP_NAME: str = "UniBot Forum"
    SITE_DOMAIN: str = os.getenv("SITE_DOMAIN", "http://localhost:5000")
    ITEMS_PER_PAGE: int = int(os.getenv("ITEMS_PER_PAGE", "15"))

    # ---- Ollama ----
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    # ---- RAG ----
    DATA_DIR: Path = DATA_DIR
    CHROMA_DIR: str = str(DATA_DIR / "chroma")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "unireg_kb")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "6"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "600"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "80"))

    # ---- Chat ----
    CHAT_MAX_HISTORY: int = int(os.getenv("CHAT_MAX_HISTORY", "12"))
    CHAT_MAX_INPUT_LENGTH: int = int(os.getenv("CHAT_MAX_INPUT_LENGTH", "1000"))

    # ---- Logging ----
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


class DevConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def get_config() -> type[BaseConfig]:
    """Chọn config theo biến FLASK_ENV (development | production)."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return ProductionConfig if env == "production" else DevConfig
