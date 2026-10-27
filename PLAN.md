# Human API implementation plan

## Status — delivered 27 October 2026

Phases 0–6 are implemented for the local synthetic-data MVP. The requested app, workflow, test/evaluation suite, rendered submission package, and reproducible build are in the workspace. Validation details and the live-tenant limitations are recorded in [PROGRESS.md](PROGRESS.md). Entra/Graph and Teams remain integration contracts until a tenant and app registration are available; this is an explicit external validation gate, not a claim of live integration.

For everyday-language definitions of the project and its terms, start with [the reader guide](docs/READER_GUIDE.md).

## Acceptance target
Deliver a runnable local web demo with synthetic identities and data, persistent question lifecycle, explicit delegation policies, requester-first authorization, evidence-backed answers, abstention/escalation, human correction and approval, revocation, audit records, tests, and the requested Eureka submission package. Enterprise Microsoft access remains explicitly disabled unless a tenant supplies reviewed configuration and consent.

## Phase 0 — Research and decisions
- Inspect the empty workspace and record project guardrails.
- Verify current Microsoft Copilot, SharePoint agents, Copilot Studio, Microsoft Scout/Autopilot, Graph and Teams integration facts from primary sources.
- Verify the current stable package candidates and their licenses before pinning.
- Decide whether the product should be an extension of Microsoft 365 workflows rather than a new enterprise-search platform.

## Phase 1 — Architecture and data
- Modular monolith: FastAPI API, SQLite in demo, PostgreSQL-ready schema, React/Vite client.
- Implement deterministic policy and state transitions separately from answer text generation.
- Seed a fictional 20-person, four-team, five-project company and 55 permission-scoped documents.
- Include the eight named security and quality scenarios.

## Phase 2 — Working demo backend
- Synthetic demo sign-in, roles and requester/project memberships.
- Persistent question submission, deadline processing, OOO consent, cancel-on-human-answer, revocation, review, correction, feedback and audit.
- Enforce project/source ACLs before retrieval; do not reveal restricted source metadata.
- Lexical retrieval and evidence templates for the fully offline demo; model adapter remains optional and cannot decide access.
- Durable deadline scanner, idempotent transitions and transactional race handling.

## Phase 3 — Working client
- Responsive dashboard, ask flow, answer evidence, delegate policy settings, escalations, review/approval and governance view.
- Display simulated status and AI-generated labeling prominently.
- UI reflects API state rather than invented metrics.

## Phase 4 — Microsoft integration contracts
- Document supported Graph and Teams adapter boundaries, permissions, consent and licensing.
- Keep the live adapters disabled without Entra configuration; mark mocks and untested interfaces honestly.
- No inbox content or Teams history connector in MVP.

## Phase 5 — Verification and evaluation
- Run the requested backend security and workflow tests plus frontend build/type checks.
- Evaluate the labeled synthetic suite and report measured results, limits and baselines.
- Render/inspect documents and slides when local tooling permits; fix layout problems.

## Phase 6 — Submission package
- Produce requested DOCX/PDF, 15-slide PPTX/PDF with substantial notes, SVG diagram, design/security/Graph docs, competitive analysis, ROI/business case, evaluation report, README and demo guide.
- Check every expected file and openable format.

## Scope discipline
No tenant credentials or external account authorization are assumed. No production security accreditation or productivity benefit is claimed. A local hackathon demo is the initial acceptance environment.
