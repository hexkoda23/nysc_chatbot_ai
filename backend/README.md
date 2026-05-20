# NYSC Chatbot Backend

FastAPI backend for the NYSC assistant.

## What It Does

- Loads local markdown documents from `../rag`
- Indexes chunks into SQLite FTS5
- Retrieves top NYSC context chunks per question with semantic keyword expansion
- Uses recent SQLite chat history to resolve short follow-up questions
- Calls a configured LLM provider when available
- Falls back to retrieved source sections when no provider is available
- Stores conversations, messages, feedback, document metadata, and eval results in SQLite

The 100 NYSC questions in `../evals/nysc_questions.json` are not training data. They are regression tests used to check retrieval, citations, fallback behavior, and topic coverage.

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
