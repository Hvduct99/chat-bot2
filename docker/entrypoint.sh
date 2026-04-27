#!/bin/sh
# =============================================================
# Entrypoint cho container app.
# - Chờ Ollama healthy
# - Chạy seed nếu DB rỗng
# - Build vector index nếu chưa có
# - Forward sang CMD (gunicorn / flask cli ...)
# =============================================================
set -e

OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"

echo "[entrypoint] OLLAMA_BASE_URL=${OLLAMA_URL}"
echo "[entrypoint] OLLAMA_LLM_MODEL=${OLLAMA_LLM_MODEL:-qwen2.5:7b}"
echo "[entrypoint] OLLAMA_EMBED_MODEL=${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
echo "[entrypoint] DATA_DIR=${DATA_DIR:-/app/data}"

# Chờ Ollama sẵn sàng (tối đa 60s)
echo "[entrypoint] Waiting for Ollama..."
i=0
until curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge 30 ]; then
        echo "[entrypoint] ⚠ Ollama không trả lời sau 60s — vẫn tiếp tục."
        break
    fi
    sleep 2
done
[ "$i" -lt 30 ] && echo "[entrypoint] ✓ Ollama OK."

# Tạo DB nếu chưa có (idempotent: seed chỉ chạy khi rỗng)
echo "[entrypoint] Running seed (skip nếu đã có data)..."
flask seed || echo "[entrypoint] ⚠ seed failed (sẽ thử lại lần sau)."

# Build vector index nếu chưa có chunk nào
INDEX_MARKER="${DATA_DIR:-/app/data}/chroma/.indexed"
if [ ! -f "$INDEX_MARKER" ]; then
    echo "[entrypoint] Building vector index lần đầu..."
    if flask ingest; then
        touch "$INDEX_MARKER"
        echo "[entrypoint] ✓ Index built."
    else
        echo "[entrypoint] ⚠ Build index thất bại — admin có thể chạy 'flask ingest' sau."
    fi
fi

echo "[entrypoint] Starting: $*"
exec "$@"
