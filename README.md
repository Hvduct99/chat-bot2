# UniBot Forum (chat-BotPy)

Flask + LangChain + Ollama (Qwen) + ChromaDB. RAG chatbot trợ lý sinh viên,
diễn đàn kiểu [diendan.vnedu.vn](https://diendan.vnedu.vn/), upload tài liệu (PDF/DOCX/TXT/MD)
để bổ sung kho tri thức cho UniBot.

## Tính năng

- **Diễn đàn sinh viên** — chuyên mục, chủ đề, trả lời (forum-style).
- **Cổng học vụ** — đăng ký tín chỉ, lịch học, tài liệu, điểm, dashboard, profile.
- **UniBot RAG** — trả lời tiếng Việt sát dữ liệu hệ thống:
  - Vector search (ChromaDB) trên môn học, lớp, tài liệu, thông báo, knowledge docs.
  - Dynamic context: lịch của tôi, điểm cá nhân khi câu hỏi yêu cầu.
  - LLM: **Qwen 2.5** (mặc định), embedding `nomic-embed-text` qua Ollama.
  - NLP tiếng Việt: `underthesea` + intent detection bằng diacritic folding.
- **Knowledge Base admin** — upload PDF/DOCX/TXT/MD, auto-parse, chia chunk, embed
  vào ChromaDB; re-index, xóa, tag.
- **Widget chat nổi** + **trang `/chatbot`** full-screen.

## Stack

| Layer | Công nghệ |
|-------|-----------|
| Web | Flask 3, Flask-Login, Jinja2 |
| ORM | SQLAlchemy 2 + SQLite |
| LLM | Ollama (Qwen 2.5) |
| Embedding | Ollama (`nomic-embed-text`) |
| Vector DB | ChromaDB (persistent local) |
| RAG pipeline | LangChain (`langchain-ollama`, `langchain-chroma`) |
| File loaders | `pypdf`, `python-docx`, plain text |
| NLP VI | `underthesea`, `unidecode` |
| UI | TailwindCSS (CDN) + FontAwesome 6 |
| Container | Docker + Docker Compose |
| WSGI | Gunicorn (gthread workers) + Tini |

## Cấu trúc dự án

```
chat-BotPy/
├── docker-compose.yml          # Ollama + app + ollama-pull
├── Dockerfile                  # Multi-stage Python 3.11-slim
├── docker/entrypoint.sh        # Wait Ollama → seed → ingest → gunicorn
├── Makefile                    # make up | seed | ingest | logs ...
├── .env.example
├── requirements.txt
├── wsgi.py                     # Gunicorn entry
├── app/
│   ├── __init__.py             # Application factory
│   ├── settings.py             # Config (Dev/Prod profile)
│   ├── extensions.py           # db, login_manager
│   ├── logging.py
│   ├── models/                 # SQLAlchemy models theo domain
│   │   ├── auth.py             # User
│   │   ├── academic.py         # Faculty/Department/Course/Section/Enrollment
│   │   ├── content.py          # Material, Notification
│   │   ├── forum.py            # ForumCategory/Thread/Post
│   │   └── knowledge.py        # KnowledgeDocument (file upload)
│   ├── services/               # Business logic — tách khỏi blueprint
│   │   ├── enrollment.py       # enroll/drop with validation
│   │   ├── chat.py             # wrapper RAG
│   │   ├── forum.py            # category stats, create thread/post
│   │   └── documents.py        # upload, parse, index file
│   ├── rag/                    # RAG package
│   │   ├── pipeline.py         # answer()
│   │   ├── indexer.py          # build_index()
│   │   ├── retriever.py        # vector search
│   │   ├── context.py          # dynamic DB context
│   │   ├── prompt.py           # ChatPromptTemplate + system prompt
│   │   ├── clients.py          # LangChain Ollama/Chroma singletons
│   │   ├── loaders.py          # PDF/DOCX/TXT/MD parsers
│   │   ├── nlp.py              # underthesea, intent detection
│   │   └── ollama_client.py    # health check, model list
│   ├── blueprints/             # Flask routes
│   │   ├── auth.py | forum.py | student.py | chat.py | admin.py | health.py
│   ├── cli/                    # flask seed | ingest | check
│   ├── templates/
│   │   ├── base.html, partials/, errors/
│   │   ├── auth/, forum/, student/, admin/, chatbot.html
│   └── static/css|js
└── data/                       # mounted volume: SQLite + ChromaDB + uploads
```

## Quick start — Docker (khuyến nghị, Ubuntu/Debian/macOS/Windows)

### Yêu cầu
- Docker ≥ 24, Docker Compose plugin
- ~10 GB free disk (Qwen 2.5 7B ≈ 5 GB + nomic-embed ≈ 270 MB)

### Bước 1 — clone & cấu hình
```bash
git clone <repo> chat-BotPy && cd chat-BotPy
cp .env.example .env
# Sửa .env nếu cần đổi model: OLLAMA_LLM_MODEL=qwen2.5:3b (cho máy yếu)
```

### Bước 2 — build & start
```bash
make up                 # = docker compose up -d --build
# Hoặc:
docker compose up -d --build
```

Hệ thống tự động:
1. Khởi động `ollama` service.
2. Service `ollama-pull` pull `qwen2.5:7b` + `nomic-embed-text` (lần đầu mất ~5-10 phút tùy mạng).
3. App chạy entrypoint: chờ Ollama → `flask seed` → `flask ingest` → `gunicorn`.

Truy cập: <http://localhost:5000>

### Bước 3 — kiểm tra
```bash
make ps                  # services up?
make logs                # tail logs app
make check               # health check Ollama + models
```

### Tài khoản mẫu
| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| Admin | `admin@unireg.edu.vn` | `admin123` |
| Sinh viên | `sv001@student.edu.vn` | `123456` |

## Lệnh thường dùng

```bash
make help            # liệt kê tất cả lệnh
make up              # build + start
make down            # stop (giữ volumes)
make logs            # tail logs app
make seed            # seed lại DB (idempotent)
make seed-reset      # drop & recreate DB
make ingest          # rebuild vector index từ DB + knowledge docs
make check           # kiểm tra Ollama
make shell           # vào container app
make rebuild         # down + build + up
make clean           # XÓA volumes (mất hết data!)
```

## Quản lý Knowledge Base (file PDF/DOCX/...)

1. Đăng nhập admin (`admin@unireg.edu.vn`).
2. Vào menu **Knowledge Base** ở thanh nav.
3. Upload file (PDF/DOCX/TXT/MD, ≤ 25 MB).
4. Hệ thống tự parse → chia chunk → embed → ChromaDB.
5. UniBot tự động dùng tri thức này để trả lời sinh viên.

Có thể **re-index** từng file (sau khi sửa) hoặc rebuild toàn bộ qua `make ingest`.

## Dev không Docker

```bash
python -m venv .venv
source .venv/bin/activate         # Linux/Mac
# .venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Cần Ollama chạy local:
# curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b nomic-embed-text

cp .env.example .env
# Sửa OLLAMA_BASE_URL=http://localhost:11434 (vì không chạy trong Docker network)

export FLASK_APP=wsgi.py
flask seed
flask ingest
flask run --host 0.0.0.0 --port 5000
```

## Kiến trúc RAG

```
              Câu hỏi tiếng Việt
                     │
                     ▼
            ┌────────────────┐
            │  NLP normalize │  underthesea + fold dấu
            │  intent detect │
            └───────┬────────┘
                    │
       ┌────────────┴─────────────┐
       ▼                          ▼
┌────────────┐          ┌────────────────────┐
│  Dynamic   │          │  Vector retrieval  │
│  DB ctx    │          │  ChromaDB top-k=6  │
│ (lịch của  │          │  - courses/sections│
│  tôi, điểm)│          │  - materials       │
└─────┬──────┘          │  - notifications   │
      │                 │  - forum threads   │
      │                 │  - knowledge docs  │
      │                 │  - static guides   │
      │                 └─────────┬──────────┘
      └─────────┬─────────────────┘
                ▼
       ┌────────────────┐
       │ ChatPrompt     │
       │ system + ctx + │
       │ history + Q    │
       └────────┬───────┘
                ▼
        ┌─────────────┐
        │ Ollama Qwen │ → reply (markdown VI) + sources
        └─────────────┘
```

## Endpoints quan trọng

| Path | Mô tả |
|------|-------|
| `GET  /` | Diễn đàn (forum index) |
| `GET  /chatbot` | Trang chat full-screen |
| `POST /api/chat` | API RAG (`{message, history}` → `{reply, sources, intents}`) |
| `GET  /healthz` | Liveness (cho Docker) |
| `GET  /readyz` | Readiness (Ollama + models) |
| `GET  /admin/knowledge` | Quản lý knowledge docs (admin only) |
| `POST /admin/knowledge/upload` | Upload file mới |

## Tùy chỉnh

- **Đổi model LLM**: sửa `OLLAMA_LLM_MODEL` trong `.env` (vd `qwen2.5:3b`, `qwen2.5:14b`, `qwen3:8b`, `llama3.1:8b`...) → `make rebuild`.
- **Đổi top-k**: `RAG_TOP_K=8` trong `.env`.
- **Thêm tri thức tĩnh**: chỉnh `_static_knowledge()` trong [app/rag/indexer.py](app/rag/indexer.py) → `make ingest`.
- **Đổi system prompt**: sửa `SYSTEM_PROMPT` trong [app/rag/prompt.py](app/rag/prompt.py).
- **Bật GPU cho Ollama**: bỏ comment block `deploy.resources` trong `docker-compose.yml`.

## Test API

```bash
# Health
curl -s http://localhost:5000/readyz | jq

# Chat
curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Học kỳ này có những giảng viên nào dạy KTPM?","history":[]}' | jq
```

## Triển khai production trên Ubuntu

```bash
# Cài Docker (nếu chưa có)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

# Clone & start
git clone <repo> /opt/unibot && cd /opt/unibot
cp .env.example .env
# Đặt SECRET_KEY mạnh: openssl rand -hex 32
make up

# Reverse proxy (Nginx) cho HTTPS — không kèm trong repo, tự cấu hình.
```

Mở port 5000 (app) và 11434 (Ollama, chỉ nếu cần truy cập từ ngoài) trong `ufw`.

## License

MIT.
