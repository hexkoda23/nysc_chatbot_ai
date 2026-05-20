from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx
from dotenv import load_dotenv

from .database import PROJECT_ROOT, get_db, init_db, utc_now


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


DEFAULT_TOP_K = 5
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
}

SENSITIVE_TERMS = {
    "medical",
    "health",
    "relocation",
    "redeployment",
    "payment",
    "allowance",
    "portal",
    "discipline",
    "legal",
    "security",
    "unsafe",
    "scam",
    "abscond",
    "certificate",
    "clearance",
}

TOPIC_KEYWORDS: Sequence[Tuple[str, Sequence[str]]] = (
    ("call_up_letter", ("call-up", "call up", "callup", "deployment letter", "reporting date")),
    ("registration", ("register", "registration", "mobilization", "senate list", "graduation list", "foreign-trained", "date of birth", "name arrangement")),
    ("camp", ("camp", "orientation", "medical fitness", "pregnant", "nursing mother", "prohibited", "kit")),
    ("relocation", ("relocation", "redeployment", "relocate", "redeploy", "marital", "married", "security reason", "medical relocation")),
    ("ppa", ("ppa", "place of primary assignment", "primary assignment", "employer", "rejection")),
    ("cds", ("cds", "community development", "community service")),
    ("allowance", ("allowance", "allawee", "stipend", "salary", "bank account", "payment")),
    ("clearance", ("clearance", "biometric", "abscond", "final clearance")),
    ("exemption", ("exemption", "exclusion", "above 30", "part-time", "certificate")),
    ("portal", ("portal", "dashboard", "password", "biometric capture", "passport photograph", "posting online")),
    ("security", ("scam", "pay someone", "influence", "fraud", "unsafe")),
    ("saed", ("saed", "skill", "entrepreneurship")),
)


@dataclass
class DocumentRecord:
    filepath: str
    title: str
    source: str
    source_url: str
    topic: str
    last_checked: str
    official: bool
    content: str
    checksum: str
    metadata: Dict[str, Any]


@dataclass
class ChunkRecord:
    id: str
    filepath: str
    title: str
    topic: str
    source_url: str
    last_checked: str
    official: bool
    content: str
    checksum: str
    score: float = 0.0

    def as_source(self) -> Dict[str, Any]:
        return {
            "source": self.title or self.filepath,
            "title": self.title,
            "filepath": self.filepath,
            "source_url": self.source_url,
            "topic": self.topic,
            "last_checked": self.last_checked,
            "official": self.official,
            "snippet": self.content[:500],
            "score": round(self.score, 3),
        }


CONVERSATION_HISTORY: Dict[str, List[Tuple[str, str]]] = {}


def get_rag_docs_path() -> Path:
    raw = os.getenv("RAG_DOCS_PATH", "./rag").strip() or "./rag"
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def get_top_k() -> int:
    try:
        return max(1, min(10, int(os.getenv("TOP_K", str(DEFAULT_TOP_K)))))
    except ValueError:
        return DEFAULT_TOP_K


def get_min_score() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("MIN_RETRIEVAL_SCORE", "0.2"))))
    except ValueError:
        return 0.2


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_checksum(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_frontmatter(raw: str) -> Tuple[Dict[str, Any], str, List[str]]:
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}
    text = raw.lstrip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2]
            for line in fm.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, value = line.split(":", 1)
                clean = value.strip().strip('"').strip("'")
                if clean.lower() == "true":
                    metadata[key.strip()] = True
                elif clean.lower() == "false":
                    metadata[key.strip()] = False
                else:
                    metadata[key.strip()] = clean
            return metadata, body.strip(), warnings

    warnings.append("missing frontmatter")
    return metadata, raw, warnings


def infer_topic(text: str) -> str:
    q = text.lower()
    if "registration" in q and any(word in q for word in ("closed", "closing", "deadline", "open", "opened")):
        return "portal"
    for topic, keywords in TOPIC_KEYWORDS:
        if any(keyword in q for keyword in keywords):
            return topic
    return "faq"


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


def build_fts_query(question: str) -> str:
    terms = []
    seen = set()
    for token in tokenize(question):
        if token in seen:
            continue
        seen.add(token)
        terms.append(f"{token}*" if len(token) > 3 else token)
        if len(terms) >= 12:
            break
    return " OR ".join(terms)


def split_markdown(content: str, chunk_size: int = 900, overlap: int = 0) -> List[str]:
    content = normalize_text(re.sub(r"^---.*?---", "", content, flags=re.DOTALL))
    if not content:
        return []

    sections = re.split(r"(?=^#{1,3}\s+)", content, flags=re.MULTILINE)
    chunks: List[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        clean = normalize_text(current)
        if clean:
            chunks.append(clean)
        current = ""

    for section in sections:
        section = normalize_text(section)
        if not section:
            continue
        if len(section) > chunk_size:
            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
        else:
            paragraphs = [section]

        for para in paragraphs:
            if len(para) > chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
            else:
                sentences = [para]

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if current and len(current) + len(sentence) + 2 > chunk_size:
                    flush()
                    if chunks and overlap:
                        tail = chunks[-1][-overlap:]
                        current = tail + "\n\n"
                current += sentence + "\n\n"
    flush()

    deduped: List[str] = []
    seen = set()
    for chunk in chunks:
        checksum = content_checksum(chunk)
        if checksum in seen or len(chunk.strip()) < 40:
            continue
        seen.add(checksum)
        deduped.append(chunk)
    return deduped


def load_markdown_documents(docs_path: Optional[Path] = None) -> Tuple[List[DocumentRecord], List[str]]:
    root = docs_path or get_rag_docs_path()
    warnings: List[str] = []
    documents: List[DocumentRecord] = []
    if not root.exists():
        warnings.append(f"RAG docs path does not exist: {root}")
        return documents, warnings

    required = ("title", "source", "source_url", "topic", "last_checked", "official")
    for path in sorted(root.rglob("*.md")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        metadata, body, fm_warnings = parse_frontmatter(raw)
        relpath = path.relative_to(PROJECT_ROOT).as_posix()
        for warning in fm_warnings:
            warnings.append(f"{relpath}: {warning}")
        missing = [key for key in required if key not in metadata or metadata.get(key) in ("", None)]
        if missing:
            warnings.append(f"{relpath}: missing metadata: {', '.join(missing)}")

        content = normalize_text(body)
        if not content:
            warnings.append(f"{relpath}: empty document body")
            continue

        documents.append(
            DocumentRecord(
                filepath=relpath,
                title=str(metadata.get("title") or path.stem.replace("-", " ").title()),
                source=str(metadata.get("source") or "Local NYSC knowledge base"),
                source_url=str(metadata.get("source_url") or ""),
                topic=str(metadata.get("topic") or infer_topic(path.as_posix())),
                last_checked=str(metadata.get("last_checked") or ""),
                official=bool(metadata.get("official", False)),
                content=content,
                checksum=content_checksum(content),
                metadata=metadata,
            )
        )
    return documents, warnings


def rebuild_index(docs_path: Optional[Path] = None) -> Dict[str, Any]:
    init_db()
    documents, warnings = load_markdown_documents(docs_path)
    duplicate_chunks = 0
    chunk_count = 0
    now = utc_now()

    with get_db() as conn:
        conn.execute("DELETE FROM rag_chunks")
        conn.execute("DELETE FROM documents")
        try:
            conn.execute("DELETE FROM rag_chunks_fts")
        except sqlite3.OperationalError:
            pass

        seen_chunk_checksums = set()
        for doc in documents:
            cur = conn.execute(
                """
                INSERT INTO documents
                    (filepath, title, topic, source_url, last_checked, official, checksum, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.filepath,
                    doc.title,
                    doc.topic,
                    doc.source_url,
                    doc.last_checked,
                    1 if doc.official else 0,
                    doc.checksum,
                    now,
                ),
            )
            document_id = int(cur.lastrowid)
            for idx, chunk in enumerate(split_markdown(doc.content)):
                checksum = content_checksum(chunk)
                if checksum in seen_chunk_checksums:
                    duplicate_chunks += 1
                    continue
                seen_chunk_checksums.add(checksum)
                chunk_id = hashlib.sha1(f"{doc.filepath}:{idx}:{checksum}".encode("utf-8")).hexdigest()
                metadata_json = json.dumps(doc.metadata, ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO rag_chunks
                        (id, document_id, chunk_index, content, title, topic, filepath,
                         source_url, last_checked, official, checksum, metadata_json, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        document_id,
                        idx,
                        chunk,
                        doc.title,
                        doc.topic,
                        doc.filepath,
                        doc.source_url,
                        doc.last_checked,
                        1 if doc.official else 0,
                        checksum,
                        metadata_json,
                        now,
                    ),
                )
                try:
                    conn.execute(
                        """
                        INSERT INTO rag_chunks_fts (chunk_id, content, title, topic, filepath)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (chunk_id, chunk, doc.title, doc.topic, doc.filepath),
                    )
                except sqlite3.OperationalError:
                    pass
                chunk_count += 1

    return {
        "documents": len(documents),
        "chunks": chunk_count,
        "duplicates": duplicate_chunks,
        "warnings": warnings,
    }


def ensure_index() -> None:
    init_db()
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM rag_chunks").fetchone()
        count = int(row["count"] if row else 0)
    if count == 0:
        rebuild_index()


def row_to_chunk(row: sqlite3.Row, score: float = 0.0) -> ChunkRecord:
    return ChunkRecord(
        id=row["id"],
        filepath=row["filepath"],
        title=row["title"] or row["filepath"],
        topic=row["topic"] or "faq",
        source_url=row["source_url"] or "",
        last_checked=row["last_checked"] or "",
        official=bool(row["official"]),
        content=row["content"],
        checksum=row["checksum"],
        score=score,
    )


def lexical_score(question: str, chunk: ChunkRecord, topic_hint: Optional[str]) -> float:
    q_tokens = set(tokenize(question))
    if not q_tokens:
        return 0.0
    content_tokens = set(tokenize(chunk.content))
    overlap = len(q_tokens & content_tokens)
    score = overlap / max(1, len(q_tokens))

    q_lower = question.lower()
    c_lower = chunk.content.lower()
    if len(q_lower) > 8 and q_lower in c_lower:
        score += 0.25
    for phrase in ("date of birth", "senate list", "call-up", "call up", "monthly clearance", "medical fitness", "bank account"):
        if phrase in q_lower and phrase in c_lower:
            score += 0.18
    if topic_hint and chunk.topic == topic_hint:
        score += 0.25
    if chunk.official:
        score += 0.03
    return min(score, 1.0)


def fetch_chunks_by_ids(conn: sqlite3.Connection, ids: Sequence[str]) -> List[sqlite3.Row]:
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(f"SELECT * FROM rag_chunks WHERE id IN ({placeholders})", tuple(ids)).fetchall()
    by_id = {row["id"]: row for row in rows}
    return [by_id[i] for i in ids if i in by_id]


def retrieve_chunks(question: str, top_k: Optional[int] = None, topic: Optional[str] = None) -> List[ChunkRecord]:
    ensure_index()
    top_k = top_k or get_top_k()
    topic_hint = topic or infer_topic(question)
    fts_query = build_fts_query(question)
    candidates: List[ChunkRecord] = []

    with get_db() as conn:
        rows: List[sqlite3.Row] = []
        if fts_query:
            try:
                fts_rows = conn.execute(
                    """
                    SELECT chunk_id
                    FROM rag_chunks_fts
                    WHERE rag_chunks_fts MATCH ?
                    ORDER BY bm25(rag_chunks_fts)
                    LIMIT 40
                    """,
                    (fts_query,),
                ).fetchall()
                rows = fetch_chunks_by_ids(conn, [r["chunk_id"] for r in fts_rows])
            except sqlite3.OperationalError:
                rows = []

        if not rows:
            rows = conn.execute("SELECT * FROM rag_chunks LIMIT 1000").fetchall()

    for row in rows:
        chunk = row_to_chunk(row)
        if topic and chunk.topic != topic:
            continue
        chunk.score = lexical_score(question, chunk, topic_hint)
        if chunk.score > 0:
            candidates.append(chunk)

    candidates.sort(key=lambda c: c.score, reverse=True)
    min_score = get_min_score()
    filtered = [c for c in candidates if c.score >= min_score]
    if not filtered and candidates:
        filtered = candidates[: min(3, top_k)]

    deduped: List[ChunkRecord] = []
    seen = set()
    for chunk in filtered:
        signature = content_checksum(chunk.content[:700])
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(chunk)
        if len(deduped) >= top_k:
            break
    return deduped


def is_sensitive_question(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in SENSITIVE_TERMS)


def format_sources(chunks: Sequence[ChunkRecord]) -> str:
    lines = ["Sources:"]
    seen = set()
    index = 1
    for chunk in chunks:
        key = (chunk.title, chunk.filepath)
        if key in seen:
            continue
        seen.add(key)
        url = f" ({chunk.source_url})" if chunk.source_url else ""
        lines.append(f"{index}. {chunk.title} - {chunk.filepath}{url}")
        index += 1
    return "\n".join(lines)


SYSTEM_PROMPT = """You are an NYSC assistant for Nigerian corps members. Answer only using the provided NYSC context. If the context does not contain enough information, say you cannot confirm from the available documents. Do not invent rules, dates, fees, portal instructions, or relocation requirements. Always include source references from the retrieved documents. Use simple Nigerian English. Be helpful, clear, and practical."""


def build_grounded_prompt(question: str, chunks: Sequence[ChunkRecord], target_lang: str = "en") -> Tuple[str, str]:
    language_note = {
        "yo": "Write the answer in clear Yoruba while keeping official terms like NYSC, PPA, CDS and portal names unchanged.",
        "ig": "Write the answer in clear Igbo while keeping official terms like NYSC, PPA, CDS and portal names unchanged.",
        "ha": "Write the answer in clear Hausa while keeping official terms like NYSC, PPA, CDS and portal names unchanged.",
    }.get(target_lang, "Write the answer in simple Nigerian English.")

    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {i}] {chunk.title}",
                    f"File: {chunk.filepath}",
                    f"Topic: {chunk.topic}",
                    f"Last checked: {chunk.last_checked or 'not stated'}",
                    f"URL: {chunk.source_url or 'not stated'}",
                    "Context:",
                    chunk.content,
                ]
            )
        )

    user_prompt = f"""Question: {question}

{language_note}

Retrieved NYSC context:
{chr(10).join(context_blocks)}

Required answer structure:
- Direct answer
- Steps or key points if applicable
- Caution or uncertainty if needed
- Sources used, matching the source numbers above

If the retrieved context is not enough, say so plainly and do not guess."""
    return SYSTEM_PROMPT, user_prompt


def select_provider() -> Optional[str]:
    requested = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    providers = {
        "groq": os.getenv("GROQ_API_KEY"),
        "gemini": os.getenv("GEMINI_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
    }
    if requested in providers:
        return requested if providers[requested] else None
    for provider in ("groq", "gemini", "openrouter", "openai"):
        if providers[provider]:
            return provider
    return None


def call_openai_compatible(
    *,
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5180")
        headers["X-Title"] = "NYSC Chatbot AI"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 900,
    }
    with httpx.Client(timeout=25.0) as client:
        response = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def call_gemini(api_key: str, system_prompt: str, user_prompt: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 900},
    }
    with httpx.Client(timeout=25.0) as client:
        response = client.post(url, params={"key": api_key}, json=payload)
        response.raise_for_status()
        data = response.json()
    parts = data["candidates"][0]["content"].get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip()


def generate_with_llm(question: str, chunks: Sequence[ChunkRecord], target_lang: str = "en") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    provider = select_provider()
    if not provider:
        return None, None, "No LLM API key configured"

    system_prompt, user_prompt = build_grounded_prompt(question, chunks, target_lang)
    try:
        if provider == "groq":
            answer = call_openai_compatible(
                provider=provider,
                api_key=os.environ["GROQ_API_KEY"],
                base_url=os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1"),
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        elif provider == "openrouter":
            answer = call_openai_compatible(
                provider=provider,
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
                model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        elif provider == "openai":
            answer = call_openai_compatible(
                provider=provider,
                api_key=os.environ["OPENAI_API_KEY"],
                base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        else:
            answer = call_gemini(os.environ["GEMINI_API_KEY"], system_prompt, user_prompt)
        return answer, provider, None
    except Exception as exc:
        return None, provider, f"{type(exc).__name__}: {str(exc)[:200]}"


def fallback_answer(chunks: Sequence[ChunkRecord]) -> str:
    if not chunks:
        return "I could not find this in the available NYSC documents."

    lines = [
        "I could not generate a full AI answer right now, but I found these relevant NYSC document sections.",
        "",
    ]
    for i, chunk in enumerate(chunks[:5], start=1):
        snippet = re.sub(r"\s+", " ", chunk.content).strip()
        if len(snippet) > 550:
            snippet = snippet[:547].rstrip() + "..."
        lines.append(f"{i}. {chunk.title} ({chunk.filepath})")
        lines.append(snippet)
        lines.append("")
    lines.append(format_sources(chunks[:5]))
    return "\n".join(lines).strip()


def append_caution(answer: str, question: str) -> str:
    if is_sensitive_question(question):
        caution = "Please confirm critical issues with the official NYSC portal or your state secretariat."
        if caution.lower() not in answer.lower():
            return f"{answer.rstrip()}\n\nCaution: {caution}"
    return answer


def append_sources_if_missing(answer: str, chunks: Sequence[ChunkRecord]) -> str:
    if not chunks:
        return answer
    if "sources:" in answer.lower():
        return answer
    return f"{answer.rstrip()}\n\n{format_sources(chunks)}"


def _get_template_response(message: str) -> Optional[Dict[str, Any]]:
    text = message.strip().lower()
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if text in greetings:
        return {
            "answer": (
                "Hello. I can help with NYSC questions using the available local documents. "
                "Ask about registration, camp, relocation, PPA, CDS, allowance, clearance, exemption, portal issues, or safety."
            ),
            "sources": [],
            "is_fallback": False,
            "provider": None,
            "confidence": 1.0,
            "low_confidence": False,
        }
    return None


def run_nysc_agent(message: str, session_id: str, target_lang: str = "en") -> Dict[str, Any]:
    question = normalize_text(message)[:2000]
    template = _get_template_response(question)
    if template:
        return template

    chunks = retrieve_chunks(question, top_k=get_top_k())
    sources = [chunk.as_source() for chunk in chunks]
    best_score = max((chunk.score for chunk in chunks), default=0.0)
    low_confidence = best_score < get_min_score()

    if not chunks:
        answer = "I could not find this in the available NYSC documents."
        answer = append_caution(answer, question)
        return {
            "answer": answer,
            "sources": [],
            "is_fallback": True,
            "provider": None,
            "confidence": 0.0,
            "low_confidence": True,
        }

    if low_confidence:
        answer = (
            "I found only weak matches in the available NYSC documents, so I cannot answer confidently.\n\n"
            f"{fallback_answer(chunks[:3])}"
        )
        answer = append_caution(answer, question)
        return {
            "answer": answer,
            "sources": sources,
            "is_fallback": True,
            "provider": None,
            "confidence": round(best_score, 3),
            "low_confidence": True,
        }

    llm_answer, provider, error = generate_with_llm(question, chunks, target_lang)
    if llm_answer:
        answer = append_sources_if_missing(llm_answer, chunks)
        answer = append_caution(answer, question)
        return {
            "answer": answer,
            "sources": sources,
            "is_fallback": False,
            "provider": provider,
            "confidence": round(best_score, 3),
            "low_confidence": False,
        }

    answer = fallback_answer(chunks)
    if error:
        answer = f"{answer}\n\nAI provider note: {error}"
    answer = append_caution(answer, question)
    return {
        "answer": answer,
        "sources": sources,
        "is_fallback": True,
        "provider": provider,
        "confidence": round(best_score, 3),
        "low_confidence": False,
    }


def search_local_docs(query: str, k: int = 5) -> List[Dict[str, Any]]:
    return [chunk.as_source() for chunk in retrieve_chunks(query, top_k=k)]
