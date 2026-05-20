# NYSC Chatbot Backend

FastAPI backend for the NYSC assistant.

## What It Does

- Loads local markdown documents from `../rag`
- Indexes chunks into SQLite FTS5
- Retrieves top NYSC context chunks per question
- Calls a configured LLM provider when available
- Falls back to retrieved source sections when no provider is available
- Stores conversations, messages, feedback, document metadata, and eval results in SQLite

## Run

```bash
pip install -r backend/requirements.txt
python backend/scripts/index_rag.py
uvicorn backend.app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /api/chat`
- `POST /api/feedback`
- `POST /api/reload`
- `POST /api/translate`

See the root `README.md` for full setup, evaluation, and deployment notes.

