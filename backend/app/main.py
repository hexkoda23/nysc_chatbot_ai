from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from typing import Any, Deque, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .database import init_db, insert_feedback, insert_message, upsert_conversation
from .language import LANG_CODES, detect_language, translate_texts
from .rag_engine import ensure_index, rebuild_index, run_nysc_agent


load_dotenv()

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
REQUEST_LOG: Dict[str, Deque[float]] = defaultdict(deque)
logger = logging.getLogger("nysc_chatbot.startup")


def check_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = REQUEST_LOG[client]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment and try again.")
    bucket.append(now)


def cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    defaults = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "https://nysc-ai-chatbot.vercel.app",
        "https://nysc-chatbot-ai.vercel.app",
    ]
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return configured or defaults


async def warm_rag_index() -> None:
    try:
        await asyncio.to_thread(ensure_index)
        from .rag.bm25_retriever import retrieve as bm25_retrieve

        await asyncio.to_thread(bm25_retrieve, "NYSC registration", 1)
        logger.info("RAG and BM25 indexes are ready.")
    except Exception:
        logger.exception("RAG index warm-up failed. It will be retried on the next chat request.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    index_task = asyncio.create_task(warm_rag_index())
    try:
        yield
    finally:
        if not index_task.done():
            index_task.cancel()
            with suppress(asyncio.CancelledError):
                await index_task


class Source(BaseModel):
    source: str
    snippet: str
    title: Optional[str] = None
    filepath: Optional[str] = None
    source_url: Optional[str] = None
    topic: Optional[str] = None
    last_checked: Optional[str] = None
    official: Optional[bool] = None
    score: Optional[float] = None


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=2000)
    language: Optional[str] = None
    selectedLang: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    detected_language: Optional[str] = None
    detected_language_name: Optional[str] = None
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    is_fallback: bool = False
    provider: Optional[str] = None
    confidence: Optional[float] = None
    low_confidence: bool = False


class TranslateRequest(BaseModel):
    target_lang: str = Field(..., min_length=2, max_length=5)
    texts: List[str] = Field(default_factory=list, max_length=50)
    source_lang: Optional[str] = None


class TranslateResponse(BaseModel):
    translations: List[str]


class FeedbackRequest(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=128)
    rating: str = Field(..., min_length=3, max_length=4)
    comment: Optional[str] = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    status: str
    id: int


app = FastAPI(
    title="NYSC AI Assistant",
    description="Production-light NYSC assistant with local markdown RAG, SQLite persistence, citations, and LLM fallback.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request. Check required fields and message length."},
    )


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "NYSC AI Assistant API",
        "health": "/health",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "rag": "local-bm25-sqlite"}


@app.get("/api/health")
def api_health() -> Dict[str, Any]:
    return health()


@app.post("/api/reload")
def reload_documents(request: Request) -> Dict[str, Any]:
    check_rate_limit(request)
    try:
        stats = rebuild_index()
        return {"status": "success", **stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not rebuild the local document index.") from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    check_rate_limit(request)
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    raw_selected = (payload.selectedLang or payload.language or "").strip().lower()
    detected = detect_language(message)
    target = raw_selected if raw_selected in LANG_CODES else detected
    names = {"en": "English", "yo": "Yoruba", "ig": "Igbo", "ha": "Hausa"}

    title = " ".join(message.split()[:8]) or "NYSC chat"
    try:
        upsert_conversation(payload.session_id, title=title)
        insert_message(payload.session_id, "user", message)
        result = run_nysc_agent(message=message, session_id=payload.session_id, target_lang=target)
        sources = result.get("sources", [])
        assistant_id = insert_message(payload.session_id, "assistant", result.get("answer", ""), sources)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The assistant could not process that question right now.") from exc

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=[Source(**source) for source in sources],
        detected_language=target,
        detected_language_name=names.get(target, "English"),
        message_id=assistant_id,
        conversation_id=payload.session_id,
        is_fallback=bool(result.get("is_fallback", False)),
        provider=result.get("provider"),
        confidence=result.get("confidence"),
        low_confidence=bool(result.get("low_confidence", False)),
    )


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(request: Request, payload: FeedbackRequest) -> FeedbackResponse:
    check_rate_limit(request)
    rating = payload.rating.lower()
    if rating not in {"good", "bad"}:
        raise HTTPException(status_code=422, detail="Rating must be 'good' or 'bad'.")
    try:
        feedback_id = insert_feedback(payload.message_id, rating, payload.comment)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not save feedback for that message.") from exc
    return FeedbackResponse(status="success", id=feedback_id)


@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    return TranslateResponse(translations=translate_texts(req.texts, req.target_lang, req.source_lang))
