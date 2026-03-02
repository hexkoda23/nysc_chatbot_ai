import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()   # MUST be before os.getenv
 



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lightweight startup that warms the local corpus for instant retrieval."""
    try:
        from .rag_engine import _load_corpus  # type: ignore
        _ = _load_corpus()
    except Exception:
        pass
    yield


class Source(BaseModel):
    source: str
    snippet: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    # Accept both 'language' (legacy) and 'selectedLang' (new frontend field).
    # 'selectedLang' takes priority when both are present.
    language: Optional[str] = None      # legacy / fallback
    selectedLang: Optional[str] = None  # preferred field from frontend


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    detected_language: Optional[str] = None
    detected_language_name: Optional[str] = None

class TranslateRequest(BaseModel):
    target_lang: str
    texts: List[str]
    source_lang: Optional[str] = None

class TranslateResponse(BaseModel):
    translations: List[str]


app = FastAPI(
    title="NYSC AI Assistant",
    description="Agentic RAG assistant to help Nigerian youths navigate NYSC.",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5179",
        "http://127.0.0.1:5179",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        # Production — Vercel
        "https://*.vercel.app",
        "https://nysc-chatbot-ai.vercel.app",  # update after deploy
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reload")
def reload_documents() -> Dict[str, str]:
    """
    Reload documents and clear vector store cache.
    Call this after adding new documents to the data directory.
    """
    try:
        from .rag_engine import _load_corpus  # type: ignore
        # Warm corpus cache
        _load_corpus.cache_clear()
        docs = _load_corpus()
        return {
            "status": "success",
            "message": f"Reloaded {len(docs)} document chunks",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for the NYSC assistant.

    The same `session_id` should be reused by the frontend to preserve context.
    """
    try:
        from .language import detect_language, translate_to_english, translate_from_english, LANG_CODES
        from .rag_engine import run_nysc_agent

        # --- Priority: selectedLang > language (legacy) ---
        raw_selected = request.selectedLang or request.language
        print(f"[CHAT] ── incoming ──────────────────────────────────────")
        print(f"[CHAT] message = {request.message[:80]!r}")
        print(f"[CHAT] selectedLang={request.selectedLang!r}  language={request.language!r}  → raw_selected={raw_selected!r}")

        # Normalise 'auto' → None
        override = raw_selected if (raw_selected and raw_selected != "auto") else None

        # Step 1: Detect language
        try:
            detected = detect_language(request.message)
        except Exception as de:
            print(f"[CHAT] WARN detect_language failed: {de}. Defaulting to 'en'.")
            detected = "en"
        print(f"[CHAT] detected={detected!r}")

        # Step 2: Decide target (selectedLang wins over auto-detection)
        if override and override in LANG_CODES:
            target = override
        else:
            target = detected
        print(f"[CHAT] final_target={target!r}  (override={override!r})")

        # Step 3: Translate user message → English for RAG
        #   Failure must NOT be swallowed — log loudly, fall back to original text.
        try:
            msg_en = translate_to_english(request.message, detected)
            print(f"[CHAT] translate_to_english OK → {msg_en[:80]!r}")
        except Exception as te:
            print(f"[CHAT] ERROR translate_to_english: {te}. Sending original message to RAG.")
            import traceback; traceback.print_exc()
            msg_en = request.message   # RAG will receive Yoruba, but we still translate the answer back

        # Step 4: Run RAG agent on English text but pass target_lang for language-specific footers
        result = run_nysc_agent(message=msg_en, session_id=request.session_id, target_lang=target)
        ans_en = result.get("answer", "")
        sources = result.get("sources", [])
        print(f"[CHAT] RAG answer ({len(ans_en)} chars): {ans_en[:80]!r}")

        # Since we use cross-lingual RAG now, the RAG agent generates the entire 
        # response natively in the target language. We skip post-translation entirely.
        final_answer = ans_en
        print(f"[CHAT] ── done ──────────────────────────────────────────")

        names = {"en": "English", "yo": "Yoruba", "ig": "Igbo", "ha": "Hausa"}
        return ChatResponse(
            answer=final_answer,
            sources=[Source(**s) for s in sources],
            detected_language=target,
            detected_language_name=names.get(target, "English"),
        )

    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        # Fallback: try to answer and still respect the question language as much as possible
        try:
            from .rag_engine import run_nysc_agent
            from .language import detect_language, translate_from_english, LANG_CODES

            try:
                # We put the run_nysc_agent call inside the fallback handler here too just in case
                result = run_nysc_agent(message=request.message, session_id=request.session_id, target_lang=target)
                final_answer = result.get("answer", f"[BACKEND ERROR] {error_msg}")
                sources = result.get("sources", [])
            except Exception as te:
                print(f"[CHAT-FALLBACK] RAG error: {te}")
                final_answer = f"[BACKEND ERROR] {error_msg}"

            names = {"en": "English", "yo": "Yoruba", "ig": "Igbo", "ha": "Hausa"}
            return ChatResponse(
                answer=final_answer,
                sources=[Source(**s) for s in sources],
                detected_language=target,
                detected_language_name=names.get(target, "English"),
            )
        except Exception:
            return ChatResponse(
                answer=f"[BACKEND ERROR] {error_msg}",
                sources=[],
            )

@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    try:
        from .language import translate_from_english, _translate
        out: List[str] = []
        for t in req.texts:
            if req.source_lang and req.source_lang != "en":
                out.append(_translate(t, req.target_lang, req.source_lang))
            else:
                out.append(translate_from_english(t, req.target_lang))
        return TranslateResponse(translations=out)
    except Exception as e:
        return TranslateResponse(translations=req.texts)

