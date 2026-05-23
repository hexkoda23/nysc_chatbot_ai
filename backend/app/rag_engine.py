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
from .web_search import WebSearchResult, is_official_url, search_web, web_search_enabled


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


DEFAULT_TOP_K = 5
INDEX_LOCK = threading.Lock()
ALLOWED_FILES = {
    "call_up.md",
    "cds.md",
    "corrections.md",
    "decree.md",
    "faq.md",
    "posting.md",
    "redeployment.md",
    "registration.md",
    "saed.md",
    "safety.md",
    "nysc_allowance_2024.txt",
    "nysc_current_information_2024_2025.txt",
    "nysc_policy_on_sexual_harassment.txt",
    "nyscdecree.txt",
    "bye-law pfd_103222.txt",
}
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
    "certificate",
    "callup",
    "call-up",
    "pop",
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
    "clearnce": "clearance",
    "certificaate": "certificate",
    "certifcate": "certificate",
    "allawee": "allowance",
    "allowence": "allowance",
    "biometic": "biometric",
    "biometrics": "biometric",
    "portel": "portal",
    "calup": "call-up",
    "callup": "call-up",
    "cann": "can",
    "didnt": "did not",
    "foillow": "follow",
    "folow": "follow",
}

QUERY_ALIASES.update(
    {
        "clearence": "clearance",
        "clerance": "clearance",
        "clearnace": "clearance",
        "clearanse": "clearance",
        "clearanc": "clearance",
        "clearancee": "clearance",
        "clrearance": "clearance",
        "clearancr": "clearance",
        "cearance": "clearance",
        "finalclearance": "final clearance",
        "certificte": "certificate",
        "certficate": "certificate",
        "certificat": "certificate",
        "certicate": "certificate",
        "cerificate": "certificate",
        "certifiicate": "certificate",
        "certifiacte": "certificate",
        "certifcatee": "certificate",
        "dischage": "discharge",
        "relocatee": "relocate",
        "relocatte": "relocate",
        "relocatn": "relocation",
        "relocationn": "relocation",
        "relocetion": "relocation",
        "reloction": "relocation",
        "relocasion": "relocation",
        "relocashun": "relocation",
        "redeplloy": "redeploy",
        "redeplyment": "redeployment",
        "redeploymnt": "redeployment",
        "redeploymen": "redeployment",
        "redeployement": "redeployment",
        "redployement": "redeployment",
        "redepployment": "redeployment",
        "redeployd": "redeployed",
        "reloacte": "relocate",
        "portall": "portal",
        "potral": "portal",
        "protal": "portal",
        "portla": "portal",
        "dashbord": "dashboard",
        "dasboard": "dashboard",
        "passwrod": "password",
        "pasword": "password",
        "registation": "registration",
        "regstration": "registration",
        "registraton": "registration",
        "registeration": "registration",
        "regisration": "registration",
        "mobilisation": "mobilization",
        "mobiliztion": "mobilization",
        "mobilsation": "mobilization",
        "senete": "senate",
        "sennate": "senate",
        "call-upletter": "call-up letter",
        "allowanc": "allowance",
        "allowanse": "allowance",
        "alowance": "allowance",
        "alowanse": "allowance",
        "allowee": "allowance",
        "alawee": "allowance",
        "allawance": "allowance",
        "allowancce": "allowance",
        "stipendd": "stipend",
        "biomtric": "biometric",
        "biometri": "biometric",
        "biometeric": "biometric",
        "biometrc": "biometric",
        "thumbprit": "thumbprint",
        "thumbprintt": "thumbprint",
        "thumprint": "thumbprint",
        "fingerprit": "fingerprint",
        "fingerprintt": "fingerprint",
        "ppaa": "ppa",
        "pppa": "ppa",
        "primaryassignmnt": "primary assignment",
        "assignmnt": "assignment",
        "emplyer": "employer",
        "employeer": "employer",
        "cdss": "cds",
        "communitydevelopmnt": "community development",
        "developmnt": "development",
        "saeed": "saed",
        "sade": "saed",
        "saaed": "saed",
        "campregistration": "camp registration",
        "orientaion": "orientation",
        "orintation": "orientation",
        "oriention": "orientation",
        "campregistraton": "camp registration",
        "excemption": "exemption",
        "exemtion": "exemption",
        "exemptn": "exemption",
        "exclussion": "exclusion",
        "exlusions": "exclusion",
        "securty": "security",
        "scamm": "scam",
        "fraudd": "fraud",
        "absconde": "abscond",
        "abscondng": "absconding",
    }
)

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
        ("steps", "process", "procedure", "what next"),
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
    fallback_data = PROJECT_ROOT / "backend" / "data"
    if not path.exists() and path.name.lower() == "rag" and fallback_data.exists():
        return fallback_data
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


def get_bm25_min_score() -> float:
    raw = os.getenv("MIN_BM25_SCORE", os.getenv("MIN_RETRIEVAL_SCORE", "0.2"))
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.2


def get_deep_search_top_k() -> int:
    try:
        return max(1, min(8, int(os.getenv("WEB_SEARCH_RESULTS", "5"))))
    except ValueError:
        return 5


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_text(text: str) -> str:
    return normalize_text(text)


def _infer_topic_from_filename(filename: str) -> str:
    name = Path(filename).name.lower()
    compact = name.replace("-", "_").replace(" ", "_")
    if "call_up" in compact or "callup" in compact:
        return "call_up"
    if "redeployment" in compact or "relocation" in compact:
        return "redeployment"
    if "allowance" in compact or "allowee" in compact or "allawee" in compact:
        return "allowance"
    if "cds" in compact or "community_development" in compact:
        return "cds"
    if "registration" in compact or "mobilization" in compact:
        return "registration"
    if "posting" in compact:
        return "posting"
    if "saed" in compact or "skills_acquisition" in compact:
        return "saed"
    if "safety" in compact or "harassment" in compact or "security" in compact:
        return "security"
    if "faq" in compact:
        return "faq"
    if "exemption" in compact or "exclusion" in compact:
        return "exemption"
    if "decree" in compact or "bye_law" in compact or "policy" in compact:
        return "general"
    return infer_topic(name)


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

    followup_phrases = (
        "the date",
        "that date",
        "date has passed",
        "deadline has passed",
        "it has passed",
        "it passed",
        "i did not know",
        "i didnt know",
        "i didn t know",
        "i missed it",
        "missed the date",
        "missed that date",
        "am i late",
        "too late",
        "can i still",
        "what happens now",
        "what do i do now",
        "does it affect me",
        "will it affect me",
        "will that affect me",
        "does that affect me",
        "can i still do it",
        "can i still apply",
        "can i still go",
        "can i still submit",
        "can i still print it",
        "can i still collect it",
        "can i still receive it",
        "can i still report",
        "can i still correct it",
        "can i still change it",
        "can i still upload it",
        "can i still use it",
        "can i still attend",
        "can i still serve",
        "can i still clear",
        "can i still proceed",
        "what if it is late",
        "what if i am late",
        "what if i missed it",
        "what if i missed the deadline",
        "what if i missed the date",
        "what if the portal closed",
        "what if the date passed",
        "what if approval is not out",
        "what if they rejected it",
        "what if it was rejected",
        "what if i was not aware",
        "what if i did not know",
        "what if i forgot",
        "what if i could not go",
        "what if i could not attend",
        "what if i could not submit",
        "what if i could not print it",
        "what if i could not upload it",
        "what if i could not register",
        "what if i cannot access it",
        "i was not aware",
        "i was not informed",
        "i just found out",
        "i only just found out",
        "i forgot about it",
        "i forgot the date",
        "i missed my chance",
        "i missed the deadline",
        "i missed the portal date",
        "i missed the reporting date",
        "i missed the camp date",
        "i missed clearance",
        "i missed final clearance",
        "i missed biometric",
        "i missed monthly clearance",
        "i missed cds",
        "i missed ppa reporting",
        "i missed registration",
        "i missed call up printing",
        "i missed document upload",
        "the portal closed",
        "the portal is closed",
        "the portal has closed",
        "the deadline passed",
        "the deadline is gone",
        "the reporting date passed",
        "the camp date passed",
        "the clearance date passed",
        "the biometric date passed",
        "the registration date passed",
        "the upload date passed",
        "the printing date passed",
        "the approval is late",
        "the approval has not come",
        "they rejected it",
        "it was rejected",
        "it is still pending",
        "it has not been approved",
        "it has not come out",
        "it did not show",
        "it is not showing",
        "it is showing wrong",
        "it is not opening",
        "it failed again",
        "it did not work",
        "it was not accepted",
        "it was not approved",
        "it was not signed",
        "they did not sign it",
        "my ppa did not sign",
        "my lgi said no",
        "my lgi rejected it",
        "my dashboard is wrong",
        "my dashboard changed",
        "my state is wrong there",
        "my posting is wrong there",
        "what should happen now",
        "what should i tell them",
        "where should i go now",
        "who should i meet now",
    )
    if any(phrase in q for phrase in followup_phrases):
        return True

    if infer_topic(q) != "faq" and len(words) > 5:
        return False

    followup_terms = {
        "it",
        "that",
        "there",
        "date",
        "deadline",
        "late",
        "missed",
        "passed",
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

    bm25_chunks: Optional[int] = None
    try:
        from .rag.bm25_retriever import rebuild_index as rebuild_bm25_index

        bm25_chunks = rebuild_bm25_index()
    except Exception as exc:
        warnings.append(f"BM25 rebuild skipped: {type(exc).__name__}: {str(exc)[:160]}")

    stats: Dict[str, Any] = {
        "documents": len(documents),
        "chunks": chunk_count,
        "duplicates": duplicate_chunks,
        "warnings": warnings,
    }
    if bm25_chunks is not None:
        stats["bm25_chunks"] = bm25_chunks
    return stats


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


def topic_matches(actual: str, expected: Optional[str]) -> bool:
    if not expected:
        return True
    actual_clean = (actual or "").lower()
    expected_clean = expected.lower()
    equivalents = {
        "relocation": {"relocation", "redeployment"},
        "redeployment": {"relocation", "redeployment"},
        "call_up_letter": {"call_up_letter", "call_up"},
        "call_up": {"call_up_letter", "call_up"},
    }
    return actual_clean in equivalents.get(expected_clean, {expected_clean})


def bm25_result_to_chunk(result: Dict[str, Any]) -> ChunkRecord:
    file_path = str(result.get("file_path") or result.get("source") or "")
    try:
        filepath = Path(file_path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        filepath = file_path or str(result.get("source") or "")
    content = str(result.get("text") or "")
    return ChunkRecord(
        id=str(result.get("chunk_id") or content_checksum(content)),
        filepath=filepath,
        title=str(result.get("title") or result.get("source") or filepath),
        topic=str(result.get("topic") or "faq"),
        source_url=str(result.get("source_url") or ""),
        last_checked=str(result.get("last_checked") or ""),
        official=bool(result.get("official", False)),
        content=content,
        checksum=content_checksum(content),
        score=float(result.get("score") or 0.0),
    )


def retrieve_chunks(question: str, top_k: Optional[int] = None, topic: Optional[str] = None) -> List[ChunkRecord]:
    ensure_index()
    question = normalize_query_terms(question)
    top_k = top_k or get_top_k()
    topic_hint = topic or infer_topic(question)
    try:
        from .rag.bm25_retriever import retrieve as bm25_retrieve

        bm25_results = bm25_retrieve(question, top_k=max(top_k * 3, top_k), min_score=get_bm25_min_score())
        bm25_chunks: List[ChunkRecord] = []
        for result in bm25_results:
            chunk = bm25_result_to_chunk(result)
            if not topic_matches(chunk.topic, topic):
                continue
            if topic_hint and topic_matches(chunk.topic, topic_hint):
                chunk.score += 5.0 if topic_hint == "portal" else 0.25
            bm25_chunks.append(chunk)

        if topic_hint == "portal":
            preferred = [chunk for chunk in bm25_chunks if topic_matches(chunk.topic, topic_hint)]
            if preferred:
                bm25_chunks = preferred + [chunk for chunk in bm25_chunks if chunk not in preferred]

        deduped_bm25: List[ChunkRecord] = []
        seen_bm25 = set()
        for chunk in sorted(bm25_chunks, key=lambda c: c.score, reverse=True):
            signature = content_checksum(chunk.content[:700])
            if signature in seen_bm25:
                continue
            seen_bm25.add(signature)
            deduped_bm25.append(chunk)
            if len(deduped_bm25) >= top_k:
                break
        return deduped_bm25
    except Exception:
        pass

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


def _is_low_confidence(results: List[Dict[str, Any]]) -> bool:
    """Return True if the best BM25 result is below the confidence threshold."""
    if not results:
        return True
    top_score = float(results[0].get("score") or 0.0)
    return top_score < get_bm25_min_score()


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


SYSTEM_PROMPT = """You are an NYSC assistant for Nigerian corps members. Answer only using the provided NYSC context and web search snippets. If the context does not contain enough information, say you cannot confirm from the available sources. Do not invent rules, dates, fees, portal instructions, staff names, phone numbers, or relocation requirements. Always include source references from the retrieved documents or web results. Use simple Nigerian English. Be helpful, clear, and practical."""


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

Retrieved NYSC context and web search snippets:
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
    if "registration" in q_lower and any(word in q_lower for word in ("closed", "closing", "close", "deadline")):
        if any(word in s_lower for word in ("open", "close", "closed", "batch", "stream", "official announcements")):
            score += 1.0
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
        include_previous = not any(
            term in question.lower()
            for term in ("medical", "biometric capture", "registration has closed", "registration closed")
        )
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

    lines = [direct]
    if asks_for_steps(question):
        step_sentences = split_clean_sentences(direct)
        if len(step_sentences) > 1:
            lines = ["The steps are:"]
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
    missed_clearance = any(
        phrase in q
        for phrase in (
            "did not do final clearance",
            "didnt do final clearance",
            "did not do final clearance",
            "date has passed",
            "deadline has passed",
            "missed the date",
            "i did not know",
            "i didn t know",
            "too late",
            "can i still collect",
        )
    )
    if missed_clearance:
        lines = [
            (
                "I cannot confirm from the available documents that you can collect your discharge certificate "
                "without resolving final clearance first. Final clearance is the end-of-service process before "
                "passing out, and poor or unresolved clearance documentation can affect certificate collection."
            ),
            "",
            "What to do now:",
            "1. Contact your LGI or state secretariat immediately and explain that the final-clearance date has passed.",
            "2. Ask the official officer what late-clearance or rescheduling process applies in your state.",
            "3. Go with your final clearance forms, PPA clearance letter, CDS records, identity documents, and any evidence explaining why you missed the date.",
            "4. Do not rely on unofficial promises or pay anyone to process certificate collection for you.",
            "",
            format_sources(answer_chunks[:5]),
        ]
        return "\n".join(lines).strip()

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


def strip_redundant_leadin(answer: str) -> str:
    leadin = "Based on the available NYSC documents:"
    stripped = answer.lstrip()
    if stripped.lower().startswith(leadin.lower()):
        return stripped[len(leadin) :].lstrip()
    return answer


def append_caution(answer: str, question: str) -> str:
    answer = strip_redundant_leadin(answer)
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


def is_current_or_specific_lookup(question: str) -> bool:
    q = normalize_query_terms(question).lower()
    q = re.sub(r"[^a-z0-9\s-]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    if not q:
        return False

    def has_term(term: str) -> bool:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", q))

    local_office_terms = (
        "lgi",
        "local government inspector",
        "state coordinator",
        "zonal inspector",
        "secretariat",
        "office address",
        "phone number",
        "contact number",
        "contact details",
    )
    direct_lookup_starts = ("who is", "who's", "who are", "where is", "where can i find", "what is the address")
    current_terms = (
        "current",
        "latest",
        "today",
        "this week",
        "this month",
        "this batch",
        "this stream",
        "now",
        "right now",
        "closing date",
        "deadline date",
    )

    if any(has_term(term) for term in local_office_terms) and (
        q.startswith(direct_lookup_starts) or any(has_term(word) for word in ("name", "contact", "phone", "address", "mowe"))
    ):
        return True
    return any(has_term(term) for term in current_terms)


def is_specific_office_lookup(question: str) -> bool:
    q = normalize_query_terms(question).lower()
    q = re.sub(r"[^a-z0-9\s-]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    if not q:
        return False

    def has_term(term: str) -> bool:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", q))

    office_terms = (
        "lgi",
        "local government inspector",
        "state coordinator",
        "zonal inspector",
        "office address",
        "phone number",
        "contact number",
        "contact details",
    )
    return any(has_term(term) for term in office_terms) and (
        q.startswith(("who is", "who's", "who are", "where is", "where can i find", "what is the address"))
        or any(has_term(word) for word in ("name", "contact", "phone", "address", "mowe"))
    )


def should_run_deep_search(question: str, chunks: Sequence[ChunkRecord], low_confidence: bool) -> bool:
    if is_specific_office_lookup(question):
        return True
    if not web_search_enabled():
        return False
    if is_current_or_specific_lookup(question):
        return True
    return low_confidence or not chunks


def extract_lookup_place(question: str) -> str:
    q = normalize_query_terms(question)
    place_match = re.search(r"\b(?:in|at|for)\s+([a-z0-9][a-z0-9\s-]{1,50})", q, flags=re.IGNORECASE)
    if not place_match:
        return ""
    place = re.sub(r"\b(nysc|lgi|local government inspector|official|please|now)\b", " ", place_match.group(1), flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", place).strip()


def state_hint_for_place(place: str) -> str:
    normalized = place.strip().lower()
    hints = {
        "mowe": "Ogun",
        "ibafo": "Ogun",
        "sagamu": "Ogun",
        "abeokuta": "Ogun",
    }
    return hints.get(normalized, "")


def build_web_search_query(question: str) -> str:
    q = normalize_query_terms(question)
    lower = q.lower()
    if "lgi" in lower:
        place = extract_lookup_place(q)
        return f'"NYSC" "LGI" {place.title() if place else "local government inspector"}'
    if "allowance" in lower and any(term in lower for term in ("current", "latest", "today", "now")):
        return '"NYSC allowance" "current" Nigeria official'
    if "secretariat" in lower or "state coordinator" in lower:
        return f"{q} NYSC Nigeria official"
    if any(term in lower for term in ("current", "latest", "today", "this batch", "this stream", "closing date", "deadline")):
        return f"{q} NYSC Nigeria official latest"
    return f"{q} NYSC Nigeria official"


def build_web_search_queries(question: str) -> List[str]:
    primary = build_web_search_query(question)
    queries = [primary]
    if is_specific_office_lookup(question):
        place = extract_lookup_place(question)
        state_hint = state_hint_for_place(place)
        if place:
            queries.append(f'"NYSC" "{place.title()}"')
        if state_hint:
            queries.append(f'"NYSC" "{state_hint}" "state secretariat"')
            queries.append(f'"NYSC" "{state_hint}" "state coordinator"')
        queries.append('"NYSC" "state secretariat" contact')
    return list(dict.fromkeys(query for query in queries if query.strip()))


def web_result_to_chunk(result: WebSearchResult, index: int) -> ChunkRecord:
    content = ". ".join(part for part in (result.title, result.snippet) if part).strip()
    if not content:
        content = result.url
    checksum = content_checksum(f"{result.url}|{content}")
    return ChunkRecord(
        id=f"web_{checksum[:16]}_{index}",
        filepath=result.url,
        title=result.title or result.source or "Web search result",
        topic="web",
        source_url=result.url,
        last_checked=utc_now()[:10],
        official=is_official_url(result.url),
        content=content,
        checksum=checksum,
        score=result.score,
    )


def run_deep_search(question: str) -> List[ChunkRecord]:
    seen_urls = set()
    results: List[WebSearchResult] = []
    for query in build_web_search_queries(question):
        for result in search_web(query, max_results=get_deep_search_top_k()):
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            results.append(result)
            if len(results) >= get_deep_search_top_k():
                break
        if len(results) >= get_deep_search_top_k():
            break

    chunks = [web_result_to_chunk(result, index) for index, result in enumerate(results, start=1)]
    chunks.sort(key=lambda chunk: (chunk.official, chunk.score), reverse=True)
    return chunks


def web_search_unavailable_answer(question: str) -> str:
    if web_search_enabled():
        return (
            "I could not confirm this from the local NYSC documents, and web search did not return a reliable result right now. "
            "Please confirm through the official NYSC portal, the NYSC state secretariat, or your LGI before acting."
        )
    return (
        "I could not confirm this from the local NYSC documents. Web search is not enabled on this deployment, "
        "so please confirm through the official NYSC portal, the NYSC state secretariat, or your LGI."
    )


def web_fallback_answer(question: str, web_chunks: Sequence[ChunkRecord]) -> str:
    if not web_chunks:
        return web_search_unavailable_answer(question)

    opening = (
        "I could not confirm the exact current or location-specific detail from the local NYSC documents. "
        "I searched the web and found these possibly relevant sources."
        if is_current_or_specific_lookup(question)
        else "I searched beyond the local NYSC documents because the local match was weak."
    )
    lines = [
        opening,
        "",
        "What I found:",
    ]
    for index, chunk in enumerate(web_chunks[:5], start=1):
        snippet = clean_source_snippet(chunk.content)
        lines.append(f"{index}. {chunk.title}: {snippet}")
    lines.extend(
        [
            "",
            "I cannot verify details beyond these sources, so confirm with official NYSC channels before acting.",
            "",
            format_sources(web_chunks[:5]),
        ]
    )
    return "\n".join(lines).strip()


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
    deep_search_needed = should_run_deep_search(query_context.answer_question, answer_chunks, low_confidence)
    web_chunks: List[ChunkRecord] = []
    if deep_search_needed:
        web_chunks = run_deep_search(query_context.answer_question)

    if web_chunks:
        use_web_only = is_specific_office_lookup(query_context.answer_question) or low_confidence
        context_chunks = web_chunks if use_web_only else [*answer_chunks[:3], *web_chunks[:3]]
        web_sources = [chunk.as_source() for chunk in context_chunks]
        llm_answer, provider, error = generate_with_llm(query_context.answer_question, context_chunks, target_lang)
        if llm_answer:
            answer = append_sources_if_missing(llm_answer, context_chunks)
            answer = append_caution(answer, query_context.answer_question)
            return {
                "answer": answer,
                "sources": web_sources,
                "is_fallback": False,
                "provider": provider,
                "confidence": round(max((chunk.score for chunk in context_chunks), default=0.0), 3),
                "low_confidence": False,
            }

        answer = web_fallback_answer(query_context.answer_question, web_chunks) if use_web_only else fallback_answer(query_context.answer_question, answer_chunks[:3])
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": web_sources,
            "is_fallback": True,
            "provider": provider,
            "confidence": round(max((chunk.score for chunk in web_chunks), default=0.0), 3),
            "low_confidence": False,
        }

    if not chunks:
        answer = web_search_unavailable_answer(query_context.answer_question) if deep_search_needed else "I could not find this in the available NYSC documents."
        answer = append_caution(answer, query_context.answer_question)
        return {
            "answer": answer,
            "sources": [],
            "is_fallback": True,
            "provider": None,
            "confidence": 0.0,
            "low_confidence": True,
        }

    if deep_search_needed and is_specific_office_lookup(query_context.answer_question):
        answer = web_search_unavailable_answer(query_context.answer_question)
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
