from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.rag_engine import get_rag_docs_path, rebuild_index


def main() -> int:
    stats = rebuild_index()
    print(f"RAG docs path: {get_rag_docs_path()}")
    print(f"Documents indexed: {stats['documents']}")
    print(f"Chunks indexed: {stats['chunks']}")
    print(f"Duplicate chunks skipped: {stats['duplicates']}")
    warnings = stats.get("warnings") or []
    if warnings:
        print("Metadata warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Metadata warnings: none")
    return 0 if stats["chunks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

