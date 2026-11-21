"""Evaluate the review agent on eval/samples.json.

  python -m eval.run_eval            # uses the LLM if ANTHROPIC_API_KEY is set, else the rule-based baseline
  python -m eval.run_eval --no-llm   # rule-based baseline only

Writes eval/results.json and prints a markdown table for the README.
The expected labels in samples.json were written by the project author: review and adjust them to
your own judgement before quoting the numbers.
"""
import argparse
import json
import os
import time
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///./eval.db")

from app import agent  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import ChangeRequest, Policy, User  # noqa: E402
from app.observability import metrics  # noqa: E402
from app.policies_seed import SEED_POLICIES  # noqa: E402

HERE = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    samples = json.loads((HERE / "samples.json").read_text())
    client = None if args.no_llm else agent.get_client()
    mode = "llm" if client else "rule-based baseline"
    if not args.no_llm and client is None:
        print("ANTHROPIC_API_KEY not set: evaluating the rule-based baseline only.\n")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    rows = []
    with SessionLocal() as db:
        db.add_all(Policy(**p) for p in SEED_POLICIES)
        db.add(User(name="Eval", email="eval@example.com", password_hash="x", role="engineer"))
        db.commit()
        for i, s in enumerate(samples, 1):
            req = ChangeRequest(requester_id=1, type=s["type"], target=s["target"],
                                justification=s["justification"], risk_level=s["risk_level"])
            db.add(req)
            db.commit()
            start = time.monotonic()
            review = agent.review_request(db, req, client)
            db.commit()
            rows.append({"n": i, "target": s["target"], "expected_risk": s["expected_risk"],
                         "got_risk": review.risk_assessment, "expected_rec": s["expected_recommendation"],
                         "got_rec": review.recommendation, "status": review.status,
                         "seconds": round(time.monotonic() - start, 2)})
            print(f"{i:>2}. {s['expected_risk']:>6}->{review.risk_assessment:<6} "
                  f"{s['expected_recommendation']:>8}->{review.recommendation:<8} {review.status}")

    n = len(rows)
    risk_ok = sum(r["expected_risk"] == r["got_risk"] for r in rows)
    rec_ok = sum(r["expected_rec"] == r["got_rec"] for r in rows)
    tp = sum(r["expected_risk"] == "high" and r["got_risk"] == "high" for r in rows)
    predicted_high = sum(r["got_risk"] == "high" for r in rows)
    actual_high = sum(r["expected_risk"] == "high" for r in rows)
    failed = sum(r["status"] == "failed" for r in rows)
    result = {
        "mode": mode, "samples": n,
        "risk_accuracy_pct": round(100 * risk_ok / n, 1),
        "recommendation_accuracy_pct": round(100 * rec_ok / n, 1),
        "high_risk_precision_pct": round(100 * tp / predicted_high, 1) if predicted_high else None,
        "high_risk_recall_pct": round(100 * tp / actual_high, 1) if actual_high else None,
        "fallback_rate_pct": round(100 * failed / n, 1),
        "avg_seconds_per_review": round(sum(r["seconds"] for r in rows) / n, 2),
        "llm_tokens": {"input": metrics.snapshot()["llm_input_tokens"], "output": metrics.snapshot()["llm_output_tokens"]},
        "rows": rows,
    }
    (HERE / "results.json").write_text(json.dumps(result, indent=2))
    print(f"\n| Metric | Result ({mode}) |\n|---|---|")
    for key in ("samples", "risk_accuracy_pct", "recommendation_accuracy_pct", "high_risk_precision_pct",
                "high_risk_recall_pct", "fallback_rate_pct", "avg_seconds_per_review"):
        print(f"| {key} | {result[key]} |")


if __name__ == "__main__":
    main()
