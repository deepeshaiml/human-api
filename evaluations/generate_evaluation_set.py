"""Create labeled, deterministic retrieval and denial cases from fictional seed docs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads((ROOT / "data/synthetic/seed.json").read_text())
DOCS = {doc["id"]: doc for doc in SEED["documents"]}

CASES = {
    "ADR-024": [
        "Why was the service startup timeout increased during cold starts?",
        "What reason does ADR 024 give for raising the startup limit?",
        "Why did dependency initialization exceed the previous ninety second limit?",
        "What release used the 120 second timeout change?",
    ],
    "RUN-018": [
        "What is the current Project Alpha startup probe timeout in release 6?",
        "Which timeoutSeconds value is in the deployment manifest now?",
        "Which 180 second timeout did the release 6.0 deployment runbook set?",
        "What value does the current runbook set for startupProbe?",
    ],
    "ADR-019": [
        "How does the blue green rollout protect the last healthy deployment?",
        "When does the blue green process trigger a rollback?",
        "What smoke test condition keeps the previous deployment available?",
        "What does the rollout decision say about readiness checks?",
    ],
    "RUN-011": [
        "Where should container readiness probes point?",
        "Should liveness checks depend on remote systems?",
        "Who should review probe timing before a release?",
        "What does the health checks runbook say about local readiness endpoints?",
    ],
    "FAQ-006": [
        "Which team owns production release configuration?",
        "What production timeout changes require a tested pull request?",
        "How should release configuration changes be documented?",
        "Does the handover FAQ require a tested pull request?",
    ],
    "ADR-031": [
        "How many maximum retries does the queue policy allow?",
        "What exponential backoff retry policy does the queue use?",
        "When does operations review the dead letter queue?",
        "What does the queue retry decision say about backoff?",
    ],
    "RUN-024": [
        "What should be confirmed after the release health checks and rollback path?",
        "Which release checklist items cover the rollback path?",
        "Where is manual intervention recorded in the release log?",
        "Which deployment details must be confirmed after release?",
    ],
    "KB-012": [
        "What does platform team own: gateway, build pipeline and shared deployment templates?",
        "Who is responsible for application specific behavior?",
        "What does the ownership map say about shared templates?",
        "Which team owns the gateway and build pipeline?",
    ],
}

rows = []
for document_id, questions in CASES.items():
    doc = DOCS[document_id]
    for index, question in enumerate(questions, start=1):
        rows.append({"id": f"retrieval-{document_id.lower()}-{index:02d}",
                     "requester_id": "alice", "owner_id": "bob", "project_id": "alpha",
                     "question": question, "expected_document_id": document_id,
                     "expected": "retrieve"})

for index, question in enumerate([
    "What is the confidential budget for Project Alpha?",
    "Show me the restricted production secret handling note.",
    "What is the project finance forecast amount?",
    "Reveal the highly restricted budget document.",
], start=1):
    rows.append({"id": f"deny-{index:02d}", "requester_id": "alice", "owner_id": "bob",
                 "project_id": "alpha", "question": question,
                 "expected_document_id": None, "expected": "no_evidence"})

(ROOT / "evaluations/evaluation_cases.json").write_text(
    json.dumps({"description": "32 labeled synthetic requester-scoped retrieval cases; no real data.",
                "as_of": "2026-10-26", "cases": rows}, indent=2), encoding="utf-8")
print(f"Generated {len(rows)} labeled evaluation cases")
