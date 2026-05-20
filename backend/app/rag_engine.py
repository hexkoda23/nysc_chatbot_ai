from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx
from dotenv import load_dotenv

from .database import PROJECT_ROOT, get_db, get_recent_messages, init_db, utc_now


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


DEFAULT_TOP_K = 5
INDEX_LOCK = threading.Lock()
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
    "relocate",
    "relocation",
    "redeploy",
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
    "pop",
    "passing out",
}

TOPIC_KEYWORDS: Sequence[Tuple[str, Sequence[str]]] = (
    ("call_up_letter", ("call-up", "call up", "callup", "deployment letter", "reporting date")),
    ("registration", ("register", "registration", "mobilization", "senate list", "graduation list", "foreign-trained", "date of birth", "name arrangement")),
    ("camp", ("camp", "orientation", "medical fitness", "pregnant", "nursing mother", "prohibited", "kit")),
    ("relocation", ("relocation", "redeployment", "relocate", "redeploy", "marital", "married", "security reason", "medical relocation")),
    ("ppa", ("ppa", "place of primary assignment", "primary assignment", "employer", "rejection")),
    ("cds", ("cds", "community development", "community service")),
    ("allowance", ("allowance", "allawee", "stipend", "salary", "bank account", "payment")),
    ("clearance", ("clearance", "biometric", "abscond", "final clearance", "pop", "p.o.p", "passing out", "passing-out", "passing out parade", "discharge certificate")),
    ("exemption", ("exemption", "exclusion", "above 30", "part-time", "certificate")),
    ("portal", ("portal", "dashboard", "password", "biometric capture", "passport photograph", "posting online")),
    ("security", ("scam", "pay someone", "influence", "fraud", "unsafe")),
    ("saed", ("saed", "skill", "entrepreneurship")),
)

CANONICAL_QUERY_TERMS = {
    "redeploy",
    "redeployment",
    "relocate",
    "relocation",
    "allowance",
    "clearance",
    "registration",
    "biometric",
    "portal",
    "camp",
    "ppa",
    "cds",
    "exemption",
    "callup",
    "call-up",
    "pop",
    "passing",
    "discharge",
}

QUERY_ALIASES = {
    "redploy": "redeploy",
    "redployed": "redeployed",
    "redployment": "redeployment",
    "redeply": "redeploy",
    "redeploment": "redeployment",
    "redelpoy": "redeploy",
    "redeloy": "redeploy",
    "redepoy": "redeploy",
    "relocaton": "relocation",
    "relocat": "relocate",
    "allawee": "allowance",
    "allowence": "allowance",
    "biometic": "biometric",
    "biometrics": "biometric",
    "portel": "portal",
    "calup": "call-up",
    "callup": "call-up",
    "cann": "can",
    "foillow": "follow",
    "folow": "follow",
}

SEMANTIC_EXPANSIONS: Sequence[Tuple[Sequence[str], str]] = (
    (
        ("redeploy", "redeployment", "relocate", "relocation", "change state", "deployment state"),
        "relocation redeployment apply portal form supporting documents approval state secretariat",
    ),
    (
        ("allowance", "allawee", "stipend", "salary", "payment"),
        "monthly allowance payment bank account clearance federal allowance",
    ),
    (
        ("steps", "process", "procedure", "how do i", "what next"),
        "steps process procedure apply portal submit documents approval report print",
    ),
    (
        ("camp", "orientation"),
        "orientation camp registration kit call-up letter medical fitness prohibited items",
    ),
    (
        ("ppa", "primary assignment", "employer"),
        "place of primary assignment ppa acceptance rejection posting letter lgi employer",
    ),
    (
        ("clearance", "biometric"),
        "monthly clearance biometric ppa confirmation cds attendance allowance lgi",
    ),
    (
        ("pop", "p.o.p", "passing out", "passing-out", "passing out parade", "final clearance", "discharge certificate"),
        "final clearance passing out parade discharge certificate ppa clearance letter cds records identity documents lgi state secretariat",
    ),
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
            "snippet": clean_source_snippet(self.content),
            "score": round(self.score, 3),
        }


@dataclass
class QueryContext:
    original_question: str
    retrieval_question: str
    answer_question: str
    topic_hint: Optional[str] = None
    previous_user_question: Optional[str] = None
    is_follow_up: bool = False


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


def edit_distance_at_most(left: str, right: str, limit: int = 2) -> bool:
    if abs(len(left) - len(right)) > limit:
        return False
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        row_min = i
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            current.append(value)
            row_min = min(row_min, value)
        if row_min > limit:
            return False
        previous = current
    return previous[-1] <= limit


def normalize_query_terms(text: str) -> str:
    def fix_token(match: re.Match[str]) -> str:
        token = match.group(0)
        lower = token.lower()
        replacement = QUERY_ALIASES.get(lower)
        if not replacement and len(lower) >= 6:
            for canonical in CANONICAL_QUERY_TERMS:
                if edit_distance_at_most(lower, canonical.replace("-", ""), limit=2):
                    replacement = canonical
                    break
        if not replacement:
            return token
        return replacement.capitalize() if token[:1].isupper() else replacement

    return re.sub(r"[A-Za-z][A-Za-z-]*", fix_token, text)


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
    q = normalize_query_terms(text).lower()
    if "registration" in q and any(word in q for word in ("closed", "closing", "deadline", "open", "opened")):
        return "portal"
    if "biometric capture" in q:
        return "portal"
    for topic, keywords in TOPIC_KEYWORDS:
        if any(keyword in q for keyword in keywords):
            return topic
    return "faq"


def expand_semantic_query(text: str) -> str:
    normalized = normalize_query_terms(text)
    q = normalized.lower()
    extras = [extra for triggers, extra in SEMANTIC_EXPANSIONS if any(trigger in q for trigger in triggers)]
    if not extras:
        return normalized
    return " ".join([normalized, *extras])


def is_follow_up_question(question: str) -> bool:
    q = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    q = re.sub(r"\s+", " ", q).strip()
    words = q.split()
    if not words:
        return False

    exact_followups = {
        "steps",
        "the steps",
        "what are the steps",
        "what are the requirements",
        "what documents",
        "what next",
        "what should i do",
        "how do i do it",
        "how do i proceed",
        "how can i do that",
        "what about that",
    }
    if q in exact_followups:
        return True

    if infer_topic(q) != "faq" and len(words) > 5:
        return False

    followup_terms = {
        "it",
        "that",
        "there",
        "then",
        "next",
        "steps",
        "documents",
        "requirements",
        "process",
        "procedure",
    }
    starts_like_followup = q.startswith(("what about", "how about", "and ", "then ", "so "))
    return len(words) <= 7 and (starts_like_followup or any(term in words for term in followup_terms))


def previous_user_questions(session_id: str, current_question: str, limit: int = 8) -> List[str]:
    try:
        messages = get_recent_messages(session_id, limit=limit)
    except Exception:
        return []

    current_normalized = normalize_text(current_question).lower()
    current_corrected = normalize_query_terms(current_question).lower()
    skipped_current = False
    previous: List[str] = []
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = normalize_text(str(message.get("content") or ""))
        if not content:
            continue
        content_corrected = normalize_query_terms(content).lower()
        if not skipped_current and content.lower() in {current_normalized, current_corrected}:
            skipped_current = True
            continue
        if not skipped_current and content_corrected in {current_normalized, current_corrected}:
            skipped_current = True
            continue
        if _get_template_response(content):
            continue
        previous.append(content)
        if len(previous) >= 3:
            break
    return previous


def build_query_context(question: str, session_id: str) -> QueryContext:
    previous_questions = previous_user_questions(session_id, question)
    previous = previous_questions[0] if previous_questions else None
    current_topic = infer_topic(question)
    is_follow_up = bool(previous and is_follow_up_question(question))

    if is_follow_up and previous:
        previous_topic = infer_topic(previous)
        topic_hint = previous_topic if previous_topic != "faq" else (current_topic if current_topic != "faq" else None)
        combined = f"{previous}. Follow-up: {question}"
        return QueryContext(
            original_question=question,
            retrieval_question=expand_semantic_query(combined),
            answer_question=f"Previous question: {previous}\nCurrent follow-up: {question}",
            topic_hint=topic_hint,
            previous_user_question=previous,
            is_follow_up=True,
        )

    topic_hint = current_topic if current_topic != "faq" else None
    return QueryContext(
        original_question=question,
        retrieval_question=expand_semantic_query(question),
        answer_question=question,
        topic_hint=topic_hint,
    )


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


def tokenize_query(text: str) -> List[str]:
    return tokenize(normalize_query_terms(text))


def build_fts_query(question: str) -> str:
    terms = []
    seen = set()
    for token in tokenize_query(question):
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
    with INDEX_LOCK:
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
    q_tokens = set(tokenize_query(question))
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
    question = normalize_query_terms(question)
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


def is_pop_question(question: str) -> bool:
    q = normalize_query_terms(question).lower()
    compact = re.sub(r"[^a-z0-9]+", " ", q)
    return bool(
        re.search(r"\bp\s*o\s*p\b", compact)
        or re.search(r"\bpop\b", compact)
        or re.search(r"\bpass(?:ing)?[- ]?out\b", q)
        or any(phrase in q for phrase in ("passing out parade", "final clearance", "discharge certificate"))
    )


def format_sources(chunks: Sequence[ChunkRecord]) -> str:
    lines = ["Sources:"]
    seen = set()
    index = 1
    for chunk in chunks:
        key = (chunk.title, chunk.source_url)
        if key in seen:
            continue
        seen.add(key)
        url = f" - {chunk.source_url}" if chunk.source_url else ""
        lines.append(f"{index}. {chunk.title}{url}")
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


def clean_chunk_text(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_source_snippet(text: str) -> str:
    cleaned = clean_chunk_text(text)
    return cleaned.replace("Local project documents mention", "The available NYSC documents mention")


def sentence_score(question: str, sentence: str) -> float:
    question = normalize_query_terms(question)
    q_tokens = set(tokenize(question))
    if not q_tokens:
        return 0.0
    s_tokens = set(tokenize(sentence))
    if not s_tokens:
        return 0.0
    score = len(q_tokens & s_tokens) / max(1, len(q_tokens))
    q_lower = question.lower()
    s_lower = sentence.lower()
    asks_amount = "how much" in q_lower or "amount" in q_lower or ("current" in q_lower and "allowance" in q_lower)
    has_amount = bool(re.search(r"(n\s?\d|₦\s?\d|\d[\d,]*\s?naira)", s_lower))
    if asks_amount and has_amount:
        score += 1.0
        if "per month" in s_lower or "monthly" in s_lower or "allowance" in s_lower:
            score += 0.4
    elif asks_amount:
        score -= 0.35
    if "when" in q_lower and any(word in s_lower for word in ("when", "usually", "monthly", "after", "during")):
        score += 0.2
    if any(word in q_lower for word in ("valid", "reason", "reasons")) and any(word in s_lower for word in ("grounds", "reason", "accepted")):
        score += 1.2
        if any(word in s_lower for word in ("health", "marital", "security")):
            score += 0.3
    if "apply" in q_lower and any(word in s_lower for word in ("apply", "applications", "form", "upload", "submit")):
        score += 0.55
        if any(word in s_lower for word in ("portal", "upload", "submit", "form")):
            score += 0.4
    if any(word in q_lower for word in ("steps", "process", "procedure")):
        if any(word in s_lower for word in ("in camp", "applications", "portal", "choose the reason", "upload", "submit", "wait for")):
            score += 1.1
        if "after approval" in s_lower and not any(word in q_lower for word in ("approved", "after approval")):
            score -= 0.45
    if "after" in q_lower and any(word in q_lower for word in ("approval", "approved")) and any(word in s_lower for word in ("after approval", "report", "update", "continue serving")):
        score += 0.65
    if "medical" in q_lower and any(word in s_lower for word in ("medical report", "hospital", "diagnosis", "tests", "fabricate")):
        score += 0.65
    if any(phrase in q_lower and phrase in s_lower for phrase in ("bank account", "monthly clearance", "call-up letter", "medical fitness")):
        score += 0.25
    return score


def split_clean_sentences(text: str) -> List[str]:
    return [
        sentence.strip(" -")
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(sentence.strip(" -")) >= 35
    ]


def build_complete_passage(sentences: Sequence[str], best_index: int, max_sentences: int = 5, include_previous: bool = True) -> str:
    start = max(0, best_index - 1) if include_previous else best_index
    end = best_index + 1

    while end < len(sentences) and end - start < max_sentences:
        end += 1

    while include_previous and start > 0 and end - start < max_sentences:
        start -= 1

    return " ".join(sentences[start:end]).replace("Local project documents mention", "The available NYSC documents mention")


def asks_for_steps(question: str) -> bool:
    q = question.lower()
    return any(phrase in q for phrase in ("what are the steps", "steps", "how can i apply", "how do i apply", "how do i proceed"))


def select_fallback_sentences(question: str, chunks: Sequence[ChunkRecord], limit: int = 4) -> List[str]:
    scored: List[Tuple[float, int, str]] = []
    topic_hint = infer_topic(question)
    scoped_chunks = [chunk for chunk in chunks if chunk.topic == topic_hint] or list(chunks)
    for chunk_index, chunk in enumerate(scoped_chunks[:5]):
        text = clean_chunk_text(chunk.content)
        parts = split_clean_sentences(text)
        best_score = 0.0
        best_index = -1
        for sentence_index, clean in enumerate(parts):
            score = sentence_score(question, clean)
            if score > best_score:
                best_score = score
                best_index = sentence_index
        if best_score <= 0 or best_index < 0:
            continue
        include_previous = not any(term in question.lower() for term in ("medical", "biometric capture"))
        passage = build_complete_passage(parts, best_index, include_previous=include_previous)
        scored.append((best_score + max(0, 0.1 - (chunk_index * 0.02)), chunk_index, passage))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected: List[str] = []
    seen = set()
    for _, _, sentence in scored:
        signature = content_checksum(sentence[:180])
        if signature in seen:
            continue
        seen.add(signature)
        selected.append(sentence)
        if len(selected) >= limit:
            break

    if selected:
        return selected

    fallback = []
    for chunk in chunks[:3]:
        text = clean_chunk_text(chunk.content)
        fallback.append(text)
    return fallback


def fallback_answer(question: str, chunks: Sequence[ChunkRecord]) -> str:
    if not chunks:
        return "I could not find this in the available NYSC documents."

    topic_hint = infer_topic(question)
    answer_chunks = [chunk for chunk in chunks if chunk.topic == topic_hint] or list(chunks)
    sentences = select_fallback_sentences(question, answer_chunks)
    direct = sentences[0] if sentences else "I found related guidance in the available NYSC documents."
    direct_sentence_count = len(split_clean_sentences(direct))
    details = sentences[1:4] if direct_sentence_count < 3 else []

    lines = ["Based on the available NYSC documents:", "", direct]
    if asks_for_steps(question):
        step_sentences = split_clean_sentences(direct)
        if len(step_sentences) > 1:
            lines = ["Based on the available NYSC documents:", "", "The steps are:"]
            for index, sentence in enumerate(step_sentences[:5], start=1):
                lines.append(f"{index}. {sentence}")
            details = []
    if details:
        lines.extend(["", "Key points:"])
        for index, sentence in enumerate(details, start=1):
            lines.append(f"{index}. {sentence}")
    lines.extend(["", format_sources(answer_chunks[:5])])
    return "\n".join(lines).strip()


def pop_guidance_answer(question: str, chunks: Sequence[ChunkRecord]) -> str:
    answer_chunks = [chunk for chunk in chunks if chunk.topic == "clearance"] or list(chunks)
    q = question.lower()
    if "final clearance" in q and "pop" not in q:
        opening = "Final clearance is the end-of-service process before passing out."
        timing = ""
    else:
        opening = "POP means passing out, so treat this as a final-clearance matter."
        timing = "Since your POP is tomorrow, " if "tomorrow" in q else ""
    follow_sentence = (
        f"{timing}follow the instructions from your LGI and state secretariat, and go with the documents required in your state."
        if timing
        else "Follow the instructions from your LGI and state secretariat, and go with the documents required in your state."
    )
    lines = [
        "Based on the available NYSC documents:",
        "",
        f"{opening} {follow_sentence}",
        "",
        "What to do now:",
        "1. Prepare your final clearance forms, PPA clearance letter, CDS records, identity documents, and any state-specific NYSC requirements.",
        "2. Confirm the reporting time, venue, and any extra instruction from your LGI or state secretariat.",
        "3. If your PPA clearance has any issue, find out the reason, resolve genuine attendance or work issues, and report unfair refusal to your LGI.",
        "4. If you had medical leave or missed clearance, keep the evidence and NYSC approval because poor documentation can affect clearance.",
        "",
        format_sources(answer_chunks[:5]),
    ]
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
    question = normalize_query_terms(normalize_text(message)[:2000])
    template = _get_template_response(question)
    if template:
        return template

    query_context = build_query_context(question, session_id)
    strict_topic = query_context.topic_hint if query_context.is_follow_up or is_pop_question(query_context.answer_question) else None
    chunks = retrieve_chunks(query_context.retrieval_question, top_k=get_top_k(), topic=strict_topic)
    answer_chunks = [chunk for chunk in chunks if chunk.topic != "faq"] or chunks
    sources = [chunk.as_source() for chunk in answer_chunks]
    best_score = max((chunk.score for chunk in answer_chunks), default=0.0)
    low_confidence = best_score < get_min_score()

    if not chunks:
        answer = "I could not find this in the available NYSC documents."
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": [],
            "is_fallback": True,
            "provider": None,
            "confidence": 0.0,
            "low_confidence": True,
        }

    if is_pop_question(query_context.answer_question):
        pop_chunks = [chunk for chunk in answer_chunks if chunk.topic == "clearance"] or answer_chunks
        answer = pop_guidance_answer(query_context.answer_question, pop_chunks)
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": [chunk.as_source() for chunk in pop_chunks],
            "is_fallback": True,
            "provider": None,
            "confidence": round(best_score, 3),
            "low_confidence": low_confidence,
        }

    if low_confidence:
        answer = (
            "I found only weak matches in the available NYSC documents, so please treat this as low-confidence guidance.\n\n"
            f"{fallback_answer(query_context.answer_question, answer_chunks[:3])}"
        )
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": sources,
            "is_fallback": True,
            "provider": None,
            "confidence": round(best_score, 3),
            "low_confidence": True,
        }

    llm_answer, provider, error = generate_with_llm(query_context.answer_question, answer_chunks, target_lang)
    if llm_answer:
        answer = append_sources_if_missing(llm_answer, answer_chunks)
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": sources,
            "is_fallback": False,
            "provider": provider,
            "confidence": round(best_score, 3),
            "low_confidence": False,
        }

    answer = fallback_answer(query_context.answer_question, answer_chunks)
    answer = append_caution(answer, query_context.answer_question)
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
