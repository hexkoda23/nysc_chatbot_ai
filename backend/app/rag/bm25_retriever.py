from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence

from rank_bm25 import BM25Okapi

from .document_loader import get_last_load_report, load_chunks


DOMAIN_TERMS = {"ppa", "cds", "saed", "nysc", "lga", "lgi"}
FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
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
SYNONYM_MAP = {
    "posting state": "relocation redeployment",
    "redeployment": "relocation redeployment",
    "place of primary assignment": "ppa",
    "community development service": "cds",
    "monthly clearance": "clearance",
    "camp registration": "orientation camp registration",
    "allowee": "allowance monthly federal amount",
    "allawee": "allowance monthly federal amount",
    "how much": "amount monthly allowance federal",
    "callup": "call-up",
    "call up letter": "call-up letter",
    "stipend": "allowance",
    "redeploy": "relocate redeployment",
    "transfer": "redeployment relocation",
    "orientation": "orientation camp",
    "mobilization": "mobilization registration",
    "pay someone": "scam fraud unofficial payment security",
    "influence posting": "scam fraud unofficial payment security",
    "influence my nysc posting": "scam fraud unofficial payment security",
}


def _load_stopwords() -> set[str]:
    try:
        from nltk.corpus import stopwords

        return set(stopwords.words("english")) - DOMAIN_TERMS
    except Exception:
        return FALLBACK_STOPWORDS - DOMAIN_TERMS


STOPWORDS = _load_stopwords()


@dataclass(frozen=True)
class BM25Index:
    chunks: List[Dict[str, Any]]
    tokenized_corpus: List[List[str]]
    model: BM25Okapi
    n_files: int


_INDEX_LOCK = threading.RLock()
_INDEX: Optional[BM25Index] = None


def _expand_query(text: str) -> str:
    expanded = text
    lowered = text.lower()
    additions: List[str] = []
    for source, replacement in SYNONYM_MAP.items():
        if source in lowered:
            additions.append(replacement)
    if additions:
        expanded = " ".join([text, *additions])
    return expanded


def tokenize(text: str, *, expand_synonyms: bool = False) -> List[str]:
    value = _expand_query(text) if expand_synonyms else text
    value = value.lower()
    value = re.sub(r"(?<![a-z0-9])[-_]+|[-_]+(?![a-z0-9])", " ", value)
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", value)
    return [token for token in tokens if token in DOMAIN_TERMS or (len(token) > 1 and token not in STOPWORDS)]


def build_index(chunks: Sequence[Dict[str, Any]]) -> BM25Index:
    chunk_list = list(chunks)
    tokenized = [tokenize(str(chunk.get("text", ""))) for chunk in chunk_list]
    model = BM25Okapi(tokenized or [["__empty__"]])
    n_files = len({str(chunk.get("source", "")) for chunk in chunk_list if chunk.get("source")})
    return BM25Index(chunks=chunk_list, tokenized_corpus=tokenized, model=model, n_files=n_files)


def _build_from_documents() -> BM25Index:
    chunks = load_chunks()
    index = build_index(chunks)
    print(f"[BM25] Index built: {len(index.chunks)} chunks from {index.n_files} files")
    return index


@lru_cache(maxsize=1)
def _cached_index() -> BM25Index:
    return _build_from_documents()


def _get_index() -> BM25Index:
    global _INDEX
    with _INDEX_LOCK:
        if _INDEX is None:
            _INDEX = _cached_index()
        return _INDEX


def retrieve(query: str, top_k: int = 5, min_score: float = 0.2) -> List[Dict[str, Any]]:
    if top_k <= 0:
        top_k = 5
    index = _get_index()
    if not index.chunks:
        return []

    query_tokens = tokenize(query, expand_synonyms=True)
    if not query_tokens:
        return []

    scores = index.model.get_scores(query_tokens)
    ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)
    results: List[Dict[str, Any]] = []
    for chunk_index, score in ranked:
        raw_score = float(score)
        if raw_score < min_score:
            continue
        chunk = index.chunks[chunk_index]
        results.append(
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "score": raw_score,
                "source": chunk["source"],
                "file_path": chunk["file_path"],
                "title": chunk["title"],
                "topic": chunk["topic"],
                "doc_type": chunk.get("doc_type", "guide"),
                "source_url": chunk.get("source_url", ""),
                "last_checked": chunk.get("last_checked", ""),
                "official": bool(chunk.get("official", False)),
            }
        )
        if len(results) >= top_k:
            break
    return results


def rebuild_index() -> int:
    """Force rebuild of BM25 index. Returns number of chunks indexed."""
    global _INDEX
    with _INDEX_LOCK:
        _cached_index.cache_clear()
        _INDEX = _build_from_documents()
        return len(_INDEX.chunks)


def index_report() -> Dict[str, Any]:
    index = _get_index()
    report = get_last_load_report()
    return {
        **report,
        "total_chunks": len(index.chunks),
        "files_loaded": index.n_files,
    }


try:
    _get_index()
except Exception as exc:
    print(f"[BM25] Warning: index was not built at import time: {exc}")
