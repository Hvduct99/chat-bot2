# =============================================================
# Makefile — quy ước lệnh hay dùng cho dev & deploy.
# Chạy: `make help`
# =============================================================
.PHONY: help up down logs build seed ingest check rebuild dev shell ps clean

DC ?= docker compose

help: ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ---------- Docker ----------

up: ## Build image + start toàn bộ stack (Ollama + app)
	$(DC) up -d --build

down: ## Stop & remove containers (giữ volumes)
	$(DC) down

build: ## Rebuild image app
	$(DC) build app

logs: ## Tail logs của app
	$(DC) logs -f app

logs-all: ## Tail logs của tất cả services
	$(DC) logs -f

ps: ## Liệt kê services đang chạy
	$(DC) ps

# ---------- App lifecycle ----------

seed: ## Khởi tạo DB + seed mẫu (chạy trong container app)
	$(DC) exec app flask seed

seed-reset: ## Drop & recreate DB rồi seed lại
	$(DC) exec app flask seed --reset

ingest: ## Build/rebuild vector index từ DB
	$(DC) exec app flask ingest

check: ## Health check Ollama + models đã pull
	$(DC) exec app flask check

shell: ## Shell vào container app
	$(DC) exec app /bin/sh

rebuild: down build up ## Stop + build lại + start

# ---------- Dev (không Docker) ----------

dev: ## Chạy Flask dev server (cần venv local)
	FLASK_APP=wsgi.py FLASK_DEBUG=1 flask run --host 0.0.0.0 --port 5000

dev-seed: ## Seed local DB
	FLASK_APP=wsgi.py flask seed

dev-ingest: ## Build index local
	FLASK_APP=wsgi.py flask ingest

# ---------- Cleanup ----------

clean: ## Stop + xóa containers + volumes (mất data!)
	$(DC) down -v
