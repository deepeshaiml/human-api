"""Run the labeled synthetic evaluation against the actual retrieval/ACL functions."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from human_api.db import initialize, make_engine, make_session_factory
from human_api.knowledge import retrieve_authorized
from human_api.models import DelegationPolicy
from human_api.seed import seed_demo

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "evaluations/evaluation_cases.json").read_text())["cases"]
engine = make_engine("sqlite:///:memory:")
initialize(engine)
factory = make_session_factory(engine)
results = []
with factory() as session:
    seed_demo(session)
    policy = session.get(DelegationPolicy, "bob")
    for case in CASES:
        evidence = retrieve_authorized(session, case["requester_id"], case["owner_id"],
                                       case["project_id"], case["question"], policy)
        found_ids = [item.document_id for item in evidence]
        if case["expected"] == "retrieve":
            passed = case["expected_document_id"] in found_ids
        else:
            passed = not found_ids
        results.append({"id": case["id"], "expected": case["expected"], "retrieved": found_ids,
                        "pass": passed})

counts = Counter(item["expected"] for item in CASES)
hits = sum(item["pass"] for item in results)
retrieval_count = counts["retrieve"]
denial_count = counts["no_evidence"]
retrieval_hits = sum(item["pass"] for item in results if item["expected"] == "retrieve")
denial_hits = sum(item["pass"] for item in results if item["expected"] == "no_evidence")
report = {
    "evaluation": "Human API synthetic retrieval ACL suite",
    "cases": len(results), "passed": hits, "failed": len(results) - hits,
    "retrieval_cases": retrieval_count,
    "retrieval_hit_rate": round(retrieval_hits / retrieval_count, 4),
    "no_evidence_cases": denial_count,
    "no_evidence_rate": round(denial_hits / denial_count, 4),
    "scope": "synthetic deterministic lexical retrieval; not LLM answer quality or production security",
    "results": results,
}
(ROOT / "evaluations/latest_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
engine.dispose()
raise SystemExit(0 if hits == len(results) else 1)
