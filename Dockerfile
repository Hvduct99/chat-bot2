# =============================================================
# UniBot Forum — Flask + RAG + LangChain
# Multi-stage build, Ubuntu/Debian based, slim cuối ~400 MB
# =============================================================

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Ho_Chi_Minh

# System deps cần cho lxml, pypdf, sqlite, healthcheck (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates tini libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# Stage 1: builder — cài deps vào virtualenv
# -------------------------------------------------------------
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc g++ libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# -------------------------------------------------------------
# Stage 2: runtime
# -------------------------------------------------------------
FROM base AS runtime

# Tạo user không-root
RUN groupadd -r unibot && useradd -r -g unibot -d /app -s /usr/sbin/nologin unibot

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --chown=unibot:unibot . .

# Folder dữ liệu — sẽ mount volume vào
RUN mkdir -p /app/data/chroma /app/data/uploads/knowledge \
    && chown -R unibot:unibot /app/data

# Healthcheck endpoint của Flask
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

USER unibot
EXPOSE 5000

# Tini làm PID 1 để xử lý signal đúng cách (gunicorn graceful shutdown)
ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", \
     "--threads", "4", "--worker-class", "gthread", \
     "--timeout", "180", "--access-logfile", "-", "--error-logfile", "-", \
     "wsgi:app"]
