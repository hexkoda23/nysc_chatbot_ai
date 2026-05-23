from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


QUESTIONS_PATH = PROJECT_ROOT / "evals" / "nysc_bm25_test_questions.json"


def load_questions() -> List[Dict[str, Any]]:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    try:
        from backend.app.rag.bm25_retriever import retrieve
    except Exception as exc:
        print(f"Could not import BM25 retriever: {type(exc).__name__}: {exc}")
        return 1

    questions = load_questions()
    failures: List[str] = []
    passed = 0

    for item in questions:
        question = item["question"]
        expected = item["topic"]
        results = retrieve(question, top_k=5)
        top = results[0] if results else {}
        got = str(top.get("topic") or "none")
        score = float(top.get("score") or 0.0)
        source = str(top.get("source") or "none")
        ok = got == expected
        if ok:
            passed += 1
        else:
            failures.append(f"  - [topic: {expected}] {question} -> got '{got}' from {source} (score {score:.2f})")
        print(f"{'PASS' if ok else 'FAIL'} | expected={expected} got={got} score={score:.2f} source={source} | {question}")

    total = len(questions)
    failed = total - passed
    pct = (passed / total * 100) if total else 0.0
    print("\n=== BM25 Eval Summary ===")
    print(f"Total : {total}")
    print(f"Pass  : {passed} ({pct:.1f}%)")
    print(f"Fail  : {failed}")
    if failures:
        print("Failed questions:")
        for failure in failures:
            print(failure)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
