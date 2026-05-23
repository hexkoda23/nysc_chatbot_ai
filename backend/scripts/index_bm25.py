from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def main() -> int:
    try:
        from backend.app.rag import bm25_retriever, document_loader

        chunks = document_loader.load_chunks()
        index = bm25_retriever.build_index(chunks)
        report = document_loader.get_last_load_report()

        missing_title = report.get("missing_title_files", [])
        missing_source_url = report.get("missing_source_url_files", [])
        print("=== NYSC BM25 Index Build Report ===")
        print(f"Files loaded       : {report.get('files_loaded', index.n_files)}")
        print(f"Total chunks       : {len(index.chunks)}")
        print(f"Duplicates skipped : {report.get('duplicates_skipped', 0)}")
        print(f"Chunks with missing title      : {report.get('missing_title_chunks', 0)} -> {missing_title}")
        print(f"Chunks with missing source_url : {report.get('missing_source_url_chunks', 0)} -> {missing_source_url}")
        print("=== Done. BM25 index ready. ===")
        return 0
    except Exception as exc:
        print(f"BM25 index build failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
