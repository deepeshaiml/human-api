# Progress

Last updated: 2026-10-27 (Asia/Dubai)

For a plain-language explanation, example and glossary, start with [the reader guide](docs/READER_GUIDE.md).

## Delivered

- Local Human API MVP: FastAPI/SQLAlchemy modular monolith, SQLite demo mode, PostgreSQL-ready persistence, Alembic migration, React/TypeScript/Vite UI, and reproducible synthetic fixtures (20 employees, 4 teams, 5 projects, 55 documents).
- Governed workflow: owner consent and scope, requester-first authorization, document ACL checks before retrieval, cited deterministic answers, abstention/escalation, timeout handling, human response, correction approval, revocation, audit events, and idempotent question submission.
- Entra/Graph adapter scaffolding and permission notes; enterprise mode remains tenant-dependent and is not enabled by default. No live Teams bot or inbox/history ingestion is included.
- Submission package in `deliverables/`: 10-page DOCX/PDF idea document, 15-slide editable PPTX with notes and matching 16:9 PDF, architecture SVG, business case, competitive analysis, evaluation report, technical/security/Graph/dependency notes, README, demo guide and application screenshot.
- Reproducible build and QA scripts, Makefile, pinned dependencies, and Docker Compose PostgreSQL setup.

## Validation on 2026-10-27

- Backend suite: **17 passed, 0 failed**. The installed Starlette TestClient emits one upstream deprecation warning about its current `httpx` integration.
- Frontend TypeScript check and Vite production build: **passed**.
- Synthetic retrieval suite: **36/36 passed** (32 expected retrievals, 4 expected no-evidence outcomes). This measures the deterministic lexical retrieval/ACL fixture only; it is not an LLM-quality or production-security benchmark.
- SQLite Alembic upgrade: **passed** on a scratch database.
- Docker image build: **passed**. Isolated PostgreSQL 18.6 Compose smoke run returned healthy API status and a demo dashboard response; temporary container, network and volume were removed afterward.
- `pip check`: no broken requirements. `pip-audit`: no known vulnerabilities. Frontend and presentation `npm audit`: **0 vulnerabilities** each.
- Rendered and visually reviewed all **36 PDF pages**: pitch deck 15, idea document 10, business case 4, competitive analysis 4, evaluation report 3. No blank pages. PPTX/DOCX ZIP integrity, all 15 slide notes, and architecture SVG XML were verified.

## Limits and next gate

- A live Entra tenant, registered app and consent were not supplied, so Graph calls and identity mapping are not tenant-tested. No Teams app or bot endpoint is implemented.
- The demo selector is synthetic identity, not authentication. Answers are deterministic templates; no LLM is used. No enterprise-ready, certification, measured productivity, or customer outcome claim is made.
- A pilot still needs security review, representative evaluation, production retention/deletion controls, encryption key management, rate limits, observability, operational recovery, and measured value baselines.
