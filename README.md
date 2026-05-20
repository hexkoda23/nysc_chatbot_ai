# NYSC Chatbot AI

Production-light NYSC assistant built with a Next.js frontend, FastAPI backend, local markdown RAG, SQLite persistence, citations, and free/cheap LLM provider support.

## Architecture

- Frontend: Next.js 14 in `web/`
- Backend: FastAPI in `backend/app/`
- Knowledge base: local markdown files in `rag/`
- Retrieval: SQLite FTS5 with lexical scoring, semantic keyword expansion, and conversation-aware follow-up rewriting
- Persistence: SQLite database from `DATABASE_URL`
- LLM providers: Groq, Gemini, OpenRouter, or OpenAI, selected server-side
- Fallback mode: works without any LLM API key by returning a source-based answer from retrieved documents

The backend never exposes API keys to the frontend.

## Install

Use Node.js 20.9 or newer for the frontend.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

npm --prefix web install
```

Copy `.env.example` to `.env` and fill only the keys you want to use. The app works without an LLM key in source-based fallback mode.

## Add NYSC Documents

Add markdown files under `rag/` by topic, for example:

```text
rag/
  registration/
  relocation/
  camp/
  ppa/
  cds/
  saed/
  allowance/
  exemption/
  portal/
  clearance/
  security/
  faq/
```

Each `.md` file should start with metadata:

```markdown
---
title: NYSC Registration Guide
source: Local curated guide from project NYSC documents
source_url: https://portal.nysc.org.ng
topic: registration
last_checked: 2026-05-20
official: false
---
```

Use `official: true` only for text copied or summarized from a verified official NYSC source.

## Index Documents

```bash
npm run index-rag
```

or:

```bash
python backend/scripts/index_rag.py
```

The script rebuilds the SQLite document and chunk index, skips duplicate chunks, and prints metadata warnings.

## Run Backend

```bash
uvicorn backend.app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

## Run Frontend

```bash
npm --prefix web run dev
```

Open `http://localhost:5180`. Set `NEXT_PUBLIC_API_URL` in `web/.env.local` if your backend URL is not `http://localhost:8000`.

## LLM Configuration

Provider selection is automatic:

1. `GROQ_API_KEY`
2. `GEMINI_API_KEY`
3. `OPENROUTER_API_KEY`
4. `OPENAI_API_KEY`
5. fallback mode

Optional model variables:

```env
GROQ_MODEL=llama-3.1-8b-instant
GEMINI_MODEL=gemini-1.5-flash
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENAI_MODEL=gpt-4o-mini
```

Model names can change by provider. If an API returns a model error, update the matching model variable.

## Fallback Mode

If no API key is configured, or an API call fails, the chatbot remains usable. It returns:

- a short source-based answer
- practical key points where available
- source titles and official URLs where available

This keeps the project usable without GPU hosting, paid databases, or paid vector databases.

## Citations

Every grounded answer includes sources from retrieved chunks. The frontend shows source titles and external URLs where available. Internal markdown file paths are kept out of the user-facing chat.

Example:

```text
Sources:
1. NYSC Relocation and Redeployment Guide - https://portal.nysc.org.ng
```

## Evaluations

The 100-question NYSC eval set is in `evals/nysc_questions.json`.
These questions are not used to train or fine-tune any model. They are a test suite for retrieval, citations, fallback behavior, and topic coverage.

Run:

```bash
npm run eval
```

or:

```bash
python backend/scripts/run_evals.py
```

The eval checks source retrieval, topic match, fallback usage, low-confidence answers, and failed retrievals. Results are written to SQLite and `evals/eval_results_latest.json`.

## Conversation Memory

The backend stores chat messages in SQLite and uses recent messages to understand short follow-ups. For example, if a user asks about redeployment and then asks "what are the steps", the backend rewrites the retrieval query with the previous redeployment question before searching the local NYSC documents. This is lightweight session memory, not model training.

## Security Basics

- Backend validates request size and empty messages.
- Backend applies simple per-IP rate limiting.
- LLM calls happen only on the backend.
- CORS is configured through `CORS_ORIGINS`.
- Errors returned to the frontend are intentionally safe and generic.
- Feedback and messages are stored in SQLite.

## Production-light Deployment

Recommended low-budget setup:

- Frontend: Vercel free tier, root directory `web`
- Backend: Render, Railway, or Fly.io low-cost/free tier
- Database: SQLite file on the backend instance

For Render, the repo includes `render.yaml`. If configuring manually, use:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python start.py
Health Check Path: /health
```

The backend opens the port first and warms the local RAG index in the background, so Render should not time out while waiting for startup tasks.

SQLite warning: free hosting filesystems can be ephemeral. Back up `nysc_chatbot.db` regularly, or mount persistent storage if your host supports it. Later, the persistence layer can be migrated to PostgreSQL without changing the frontend contract.

## Useful Commands

```bash
npm run index-rag
npm run eval
npm run backend
npm run frontend
```
