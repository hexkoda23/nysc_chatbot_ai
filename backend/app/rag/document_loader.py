from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..database import BACKEND_DIR, PROJECT_ROOT
from ..rag_engine import ALLOWED_FILES, _infer_topic_from_filename, _normalize_text


CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n#", "\n\n", "\n", ". "]
LAST_LOAD_REPORT: Dict[str, Any] = {}


def _normalize_filename(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower()).strip()


NORMALIZED_ALLOWED_FILES = {_normalize_filename(name) for name in ALLOWED_FILES}


def _resolve_data_dir(data_dir: Optional[str | Path] = None) -> Path:
    raw = str(data_dir or os.getenv("RAG_DOCS_PATH", "")).strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists() and Path(raw).name.lower() == "data":
            path = BACKEND_DIR / "data"
        if not path.exists() and Path(raw).name.lower() == "rag" and (BACKEND_DIR / "data").exists():
            path = BACKEND_DIR / "data"
        return path.resolve()

    rag_path = PROJECT_ROOT / "rag"
    return rag_path.resolve() if rag_path.exists() else (BACKEND_DIR / "data").resolve()


def _parse_frontmatter(raw: str) -> Tuple[Dict[str, Any], str]:
    text = raw.lstrip()
    if not text.startswith("---"):
        return {}, raw
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, raw

    metadata: Dict[str, Any] = {}
    for line in parts[1].splitlines():
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
    return metadata, parts[2].strip()


def _infer_doc_type(path: Path, topic: str) -> str:
    name = path.name.lower()
    if topic == "faq" or "faq" in name:
        return "faq"
    if topic in {"registration", "redeployment", "relocation", "posting", "call_up", "call_up_letter"}:
        return "process"
    if topic in {"security", "general"} or any(term in name for term in ("policy", "decree", "bye-law", "law")):
        return "policy"
    return "guide"


def _recursive_split(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = _normalize_text(text)
    if not text:
        return []

    chunks: List[str] = []

    def split_block(block: str, separators: List[str]) -> List[str]:
        block = block.strip()
        if len(block) <= chunk_size or not separators:
            return [block] if block else []
        separator = separators[0]
        parts = block.split(separator)
        if len(parts) == 1:
            return split_block(block, separators[1:])

        output: List[str] = []
        current = ""
        for index, part in enumerate(parts):
            if not part.strip():
                continue
            piece = (separator if index > 0 and separator.startswith("\n") else "") + part.strip()
            if current and len(current) + len(piece) + 1 > chunk_size:
                output.extend(split_block(current, separators[1:]))
                current = ""
            current = f"{current}\n{piece}".strip() if current else piece
        if current:
            output.extend(split_block(current, separators[1:]))
        return output

    for chunk in split_block(text, SEPARATORS):
        clean = _normalize_text(chunk)
        if len(clean) >= 20:
            chunks.append(clean)
    return chunks


def _iter_source_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    files = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".txt"}]
    if root.name.lower() != "data":
        return sorted(files)
    return sorted(path for path in files if _normalize_filename(path.name) in NORMALIZED_ALLOWED_FILES)


def load_chunks(data_dir: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    root = _resolve_data_dir(data_dir)
    chunks: List[Dict[str, Any]] = []
    seen_hashes = set()
    duplicate_count = 0
    warnings: List[str] = []
    missing_title: Dict[str, int] = {}
    missing_topic: Dict[str, int] = {}
    missing_source_url: Dict[str, int] = {}
    loaded_files = 0

    for path in _iter_source_files(root):
        raw = path.read_text(encoding="utf-8", errors="replace")
        metadata, body = _parse_frontmatter(raw) if path.suffix.lower() == ".md" else ({}, raw)
        text = _normalize_text(body)
        if not text:
            continue

        loaded_files += 1
        filename = path.name
        title = str(metadata.get("title") or path.stem.replace("_", " ").replace("-", " ").title()).strip()
        topic = str(metadata.get("topic") or _infer_topic_from_filename(filename)).strip()
        source_url = str(metadata.get("source_url") or "").strip()
        last_checked = str(metadata.get("last_checked") or "").strip()
        official = bool(metadata.get("official", True))
        doc_type = str(metadata.get("doc_type") or _infer_doc_type(path, topic)).strip()

        for index, chunk_text in enumerate(_recursive_split(text)):
            chunk_text = _normalize_text(chunk_text)
            if len(chunk_text) < 20:
                continue
            digest = hashlib.md5(chunk_text.strip().encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                duplicate_count += 1
                warning = f"duplicate chunk skipped: {filename}#{index}"
                print(f"[RAG Loader] Warning: {warning}")
                warnings.append(warning)
                continue
            seen_hashes.add(digest)

            if not title:
                missing_title[filename] = missing_title.get(filename, 0) + 1
            if not topic:
                missing_topic[filename] = missing_topic.get(filename, 0) + 1
            if not source_url:
                missing_source_url[filename] = missing_source_url.get(filename, 0) + 1

            chunk = {
                "chunk_id": f"{path.stem.lower().replace(' ', '_')}_{index:04d}",
                "text": chunk_text,
                "source": filename,
                "file_path": str(path.resolve()),
                "topic": topic or "general",
                "doc_type": doc_type or "guide",
                "title": title or path.stem,
                "source_url": source_url,
                "last_checked": last_checked,
                "official": official,
            }
            for field in ("title", "topic", "source_url"):
                if not chunk.get(field):
                    warning = f"{filename}#{index}: missing {field}"
                    print(f"[RAG Loader] Warning: {warning}")
                    warnings.append(warning)
            chunks.append(chunk)

    global LAST_LOAD_REPORT
    LAST_LOAD_REPORT = {
        "root": str(root),
        "files_loaded": loaded_files,
        "total_chunks": len(chunks),
        "duplicates_skipped": duplicate_count,
        "warnings": warnings,
        "missing_title_files": sorted(missing_title),
        "missing_topic_files": sorted(missing_topic),
        "missing_source_url_files": sorted(missing_source_url),
        "missing_title_chunks": sum(missing_title.values()),
        "missing_topic_chunks": sum(missing_topic.values()),
        "missing_source_url_chunks": sum(missing_source_url.values()),
    }
    return chunks


def get_last_load_report() -> Dict[str, Any]:
    return dict(LAST_LOAD_REPORT)
