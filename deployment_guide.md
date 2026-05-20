# Production-light Deployment Guide

## Frontend on Vercel

1. Import the repo into Vercel.
2. Set root directory to `web`.
3. Keep the framework preset as `Next.js`.
4. Add:

```env
NEXT_PUBLIC_API_URL=https://your-backend.example.com
```

5. Deploy.

## Backend on Render, Railway, or Fly.io

Recommended Render settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python start.py
Health Check Path: /health
```

The repository also includes `render.yaml` with these defaults. The FastAPI app opens the web port first and warms the local RAG index in the background so Render can detect the service quickly.

Environment variables:

```env
DATABASE_URL=sqlite:///./nysc_chatbot.db
RAG_DOCS_PATH=./rag
LLM_PROVIDER=auto
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
OPENAI_API_KEY=
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

## SQLite Persistence Warning

SQLite is low-cost and simple, but many free hosts use ephemeral disks. If the host does not provide persistent storage, conversation history, feedback, and eval results can disappear after redeploys or restarts.

Back up `nysc_chatbot.db` regularly. If usage grows, migrate the persistence layer to managed PostgreSQL while keeping local SQLite FTS for documents or replacing it with PostgreSQL full-text search.

## RAG Refresh

After adding or editing markdown documents:

```bash
python backend/scripts/index_rag.py
```

You can also call `POST /api/reload` after deployment.

Docker is not required. Add it only if your host or workflow needs it.
