from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import insert_eval_result
from backend.app.rag_engine import run_nysc_agent


QUESTIONS_PATH = PROJECT_ROOT / "evals" / "nysc_questions.json"
RESULTS_PATH = PROJECT_ROOT / "evals" / "eval_results_latest.json"


def load_questions() -> List[Dict[str, Any]]:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_answer(question: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    sources = result.get("sources") or []
    answer = result.get("answer") or ""
    low_confidence = bool(result.get("low_confidence"))
    fallback = bool(result.get("is_fallback"))
    failed_retrieval = "I could not find this in the available NYSC documents" in answer
    has_sources = len(sources) > 0
    topic_hit = any(source.get("topic") == question["topic"] for source in sources)
    refuses_when_missing = failed_retrieval or "cannot" in answer.lower() or has_sources
    passed = bool(has_sources and topic_hit and refuses_when_missing)
    notes = []
    if not has_sources:
        notes.append("no sources")
    if not topic_hit:
        notes.append("expected topic not in retrieved sources")
    if low_confidence:
        notes.append("low confidence")
    if fallback:
        notes.append("fallback")
    if failed_retrieval:
        notes.append("failed retrieval")
    return {
        "id": question["id"],
        "topic": question["topic"],
        "question": question["question"],
        "answer": answer,
        "sources": sources,
        "passed": passed,
        "notes": ", ".join(notes) or "ok",
        "is_fallback": fallback,
        "low_confidence": low_confidence,
        "failed_retrieval": failed_retrieval,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NYSC chatbot retrieval/eval checks.")
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N questions.")
    args = parser.parse_args()

    questions = load_questions()
    if args.limit:
        questions = questions[: args.limit]

    results = []
    for item in questions:
        print(f"[{item['id']:03d}] {item['topic']}: {item['question']}")
        result = run_nysc_agent(item["question"], session_id=f"eval-{item['id']}", target_lang="en")
        evaluated = evaluate_answer(item, result)
        results.append(evaluated)
        insert_eval_result(
            question=item["question"],
            expected_topic=item["topic"],
            answer=evaluated["answer"],
            passed=evaluated["passed"],
            notes=evaluated["notes"],
        )

    summary = {
        "total_questions": len(results),
        "answered_with_sources": sum(1 for r in results if r["sources"]),
        "fallback_answers": sum(1 for r in results if r["is_fallback"]),
        "low_confidence_answers": sum(1 for r in results if r["low_confidence"]),
        "failed_retrievals": sum(1 for r in results if r["failed_retrieval"]),
        "passed": sum(1 for r in results if r["passed"]),
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    print("\nSummary")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"Results written to: {RESULTS_PATH}")
    return 0 if summary["passed"] == summary["total_questions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

