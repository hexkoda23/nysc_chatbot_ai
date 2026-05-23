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

## BM25 Retrieval

The backend now ranks local NYSC document chunks with BM25. At startup, the app warms the existing SQLite document index and the in-memory BM25 index. `/api/reload` rebuilds both indexes so newly edited documents are searchable without restarting the server.

BM25 reads the configured RAG document path from `RAG_DOCS_PATH`. In this repo the production knowledge base lives in `../rag`; the legacy `backend/data` corpus is also supported when `RAG_DOCS_PATH=./data` is used. For `backend/data`, only filenames listed in `ALLOWED_FILES` in `backend/app/rag_engine.py` are indexed so large research files do not slow the app down.

To add new NYSC documents, drop a `.md` or `.txt` file into the configured document folder. For the curated markdown knowledge base, include frontmatter with `title`, `topic`, `source_url`, `last_checked`, and `official`. For `backend/data`, add the lowercase filename to `ALLOWED_FILES`, then call `POST /api/reload` or restart the backend.

Build the BM25 index report:

```bash
python backend/scripts/index_bm25.py
```

Run the chatbot backend:

```bash
uvicorn backend.app.main:app --reload
```

Run BM25 retrieval evals:

```bash
python backend/scripts/eval_bm25.py
```

Configuration:

```env
TOP_K=5
MIN_BM25_SCORE=0.2
RAG_DOCS_PATH=./rag
```

Fallback mode still works without a Groq, Gemini, OpenRouter, or OpenAI key. If answer generation is unavailable, the API returns a source-based answer from the top BM25 chunks and still includes source metadata for the frontend citations panel.
