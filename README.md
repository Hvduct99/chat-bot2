# chat-BotPy — UniReg Forum + UniBot RAG

Phiên bản Python của hệ thống `chat-Bot` (gốc PHP). Tích hợp **chatbot RAG** trên nền **Ollama (Qwen) + LangChain + ChromaDB**, giao diện diễn đàn lấy cảm hứng từ [diendan.vnedu.vn](https://diendan.vnedu.vn/).

## Tính năng chính

- **Forum sinh viên** kiểu vnedu: chuyên mục, chủ đề, trả lời, ghim bài, breadcrumbs.
- **Cổng học vụ**: đăng ký tín chỉ (kiểm tra trùng lịch / lớp đầy / trùng môn), lịch học, tài liệu, điểm, dashboard.
- **UniBot RAG**: trả lời tiếng Việt sát dữ liệu thật của hệ thống.
  - Vector search trong ChromaDB (đã embed sẵn môn học, lớp, học kỳ, tài liệu, thông báo, hướng dẫn).
  - Dynamic context: tự bơm thông tin SV, lịch của tôi, điểm khi câu hỏi đụng tới.
  - LLM: **Qwen 2.5** (mặc định, có thể đổi qua biến môi trường).
  - Embeddings: `nomic-embed-text` qua Ollama.
  - NLP tiếng Việt: `underthesea` cho normalize, intent detection bằng keyword + diacritic folding.
- **Widget chat nổi** trên mọi trang + **trang `/chatbot`** full-screen.

## Stack

| Lớp | Công nghệ |
|-----|-----------|
| Web | Flask 3, Flask-Login, Jinja2 |
| ORM | SQLAlchemy 2 + SQLite |
| LLM | Ollama (Qwen 2.5 mặc định) |
| Embedding | Ollama (`nomic-embed-text`) |
| Vector DB | ChromaDB (persistent, local) |
| Pipeline | LangChain (`langchain-ollama`, `langchain-chroma`) |
| NLP VI | underthesea, unidecode |
| UI | TailwindCSS (CDN) + FontAwesome 6 |

## Yêu cầu

- Python **3.10+**
- [Ollama](https://ollama.com/) đã cài và chạy ở `localhost:11434`
- Pull sẵn 2 model:
  ```bash
  ollama pull qwen2.5:7b           # hoặc qwen2.5:3b nếu máy yếu, qwen3:8b nếu muốn
  ollama pull nomic-embed-text
  ```

> Người dùng nói "Qwen 3.5" — hiện tại Ollama không có tag tên đó.
> Gia đình Qwen mới nhất bao gồm `qwen2.5:*` và `qwen3:*`. Mặc định dùng `qwen2.5:7b`,
> đổi qua biến `OLLAMA_LLM_MODEL` trong `.env` nếu muốn dùng tag khác.

## Cài đặt

```bash
cd chat-BotPy

# 1) Tạo venv
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/Mac

# 2) Cài deps
pip install -r requirements.txt

# 3) Sao chép env
copy .env.example .env             # Windows
# cp .env.example .env             # Linux/Mac

# 4) Khởi tạo DB + seed dữ liệu mẫu
python seed.py

# 5) Build vector index từ DB (gọi Ollama embed — cần Ollama đang chạy)
python ingest.py

# 6) Chạy app
python app.py
```

Mở trình duyệt: <http://localhost:5000>

### Tài khoản mẫu

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| Admin | `admin@unireg.edu.vn` | `admin123` |
| Sinh viên | `sv001@student.edu.vn` | `123456` |
| Sinh viên | `sv002@student.edu.vn` | `123456` |

## Kiến trúc RAG

```
                 ┌────────────┐
   Câu hỏi  ──▶  │ NLP Vi     │  (underthesea, fold dấu, detect intent)
                 └─────┬──────┘
                       │
        ┌──────────────┴───────────────┐
        ▼                              ▼
┌─────────────┐                ┌──────────────────┐
│ Dynamic     │                │ Vector Search    │
│ DB Context  │                │ ChromaDB top-k=6 │
│ (lịch của   │                │ (môn, lớp, tài   │
│  tôi, điểm) │                │  liệu, thông báo)│
└──────┬──────┘                └────────┬─────────┘
       └───────────┬───────────────────┘
                   ▼
          ┌────────────────┐
          │  ChatPrompt    │
          │  System+Ctx+   │
          │  history+Q     │
          └────────┬───────┘
                   ▼
            ┌─────────────┐
            │ Ollama Qwen │  → trả về reply (tiếng Việt + markdown)
            └─────────────┘
```

### File quan trọng

| File | Vai trò |
|------|---------|
| `config.py` | Cấu hình tập trung (Ollama, model, chunk size, top-k, system prompt) |
| `core/db.py` | SQLAlchemy models (mirror `database.sql` của bản PHP) |
| `core/nlp.py` | Tiền xử lý tiếng Việt + phát hiện intent |
| `core/rag.py` | Build index, retrieve, generate (LangChain) |
| `seed.py` | Tạo DB và nạp dữ liệu mẫu |
| `ingest.py` | Build/rebuild ChromaDB từ DB |
| `app.py` | Flask entry, đăng ký blueprints |
| `routes/chat.py` | API `/api/chat` + trang `/chatbot` |
| `routes/forum.py` | Forum index, category, thread, new thread |
| `routes/student.py` | Dashboard, đăng ký TC, lịch, tài liệu, điểm |
| `routes/auth.py` | Login / Register / Logout |
| `templates/` | Jinja2 + Tailwind |

## Cập nhật dữ liệu

Mỗi khi bạn thêm môn, lớp, tài liệu, thông báo trong DB → chạy lại:

```bash
python ingest.py
```

để cập nhật vector store. (Có thể tự động hóa trong production bằng cron / hook commit.)

## Test API

```bash
curl -s http://localhost:5000/api/health | python -m json.tool

curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Học kỳ này có những giảng viên nào dạy KTPM?","history":[]}' | python -m json.tool
```

## Tùy chỉnh

- **Đổi model LLM**: sửa `OLLAMA_LLM_MODEL` trong `.env`. Ví dụ `qwen2.5:14b`, `qwen3:8b`, `llama3.1:8b`...
- **Đổi top-k**: `RAG_TOP_K=8` trong `.env`.
- **Thêm tri thức tĩnh**: chỉnh sửa hàm `_static_knowledge()` trong [core/rag.py](core/rag.py) rồi chạy lại `python ingest.py`.
- **Đổi system prompt**: sửa `SYSTEM_PROMPT` trong [config.py](config.py).

## So sánh với chat-Bot (PHP)

| | chat-Bot (PHP) | chat-BotPy (Python) |
|-|----------------|---------------------|
| Backend | PHP + MySQL | Flask + SQLite |
| LLM | Groq Cloud (LLaMA 3.3 70B) | **Ollama local (Qwen 2.5)** |
| Context | SQL build động | **RAG (vector) + SQL động** |
| Embedding | — | **nomic-embed-text** |
| Vector DB | — | **ChromaDB persistent** |
| NLP VI | string match | **underthesea + intent detection** |
| Pipeline | cURL trực tiếp | **LangChain** (history, prompt template) |
| UI | Tailwind + Vanilla JS | Tailwind + Jinja + Vanilla JS — **forum style** |
