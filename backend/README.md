NYSC AI Assistant – Backend
===========================

This backend exposes a FastAPI service that powers an **agentic RAG assistant** for Nigerian youths
going through the NYSC programme. It uses **LangGraph**, **LangChain**, and **OpenAI** to retrieve
relevant NYSC guidance documents and generate grounded answers with citations.

Quick start
-----------

1. Create and activate a virtual environment (already created as `.venv` in this project):

   ```bash
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Create a `.env` file in the project root with your OpenAI API key:

   ```bash
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   ```

4. Run the API:

   ```bash
   uvicorn backend.app.main:app --reload
   ```

5. Open the interactive docs at:

   - `http://127.0.0.1:8000/docs`

RAG / LangGraph overview
------------------------

- NYSC-related documents are stored under `backend/data/` (for now, a small sample file is included).
- At startup, the backend:
  - Loads and chunks these documents.
  - Builds a FAISS vector store using OpenAI embeddings.
- A LangGraph **ReAct agent** is created with one main tool: `retrieve_nysc_docs`.
  - The agent decides **when** to call the retrieval tool based on user questions.
  - Retrieved snippets and their `source` metadata are exposed back to the frontend as **citations**.

API contract
------------

- `POST /api/chat`
  - Request:
    - `session_id` (string): a stable id per user/session to preserve conversation context.
    - `message` (string): user question or follow-up.
  - Response:
    - `answer` (string): assistant’s response.
    - `sources` (array of `{ source, snippet }`): citations used for the answer.

