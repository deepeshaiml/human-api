# Human API — project instructions

## Reader context
- Use `docs/READER_GUIDE.md` for plain-language definitions and the canonical Alice/Bob/Carla example.
- Describe features as `implemented locally`, `adapter scaffolding`, or `future work`; do not blur those states.
- The demo uses fictional people/files and no language model. The local identity selector is not authentication.
- If explaining an answer, state both what its source supports and what it does not establish.

## Product and safety boundaries
- This is a local hackathon MVP with fictional people and sources. The demo identity selector is not production authentication.
- All authorization decisions are deterministic and happen before retrieval. A knowledge owner's consent does not grant a requester access to that owner's private sources.
- The model may only receive snippets already authorized for the requester. It cannot grant access, decide policy, or infer missing facts.
- Every software-produced answer is visibly labeled (the current interface says “AI-generated”); the local text uses fixed templates and no language model. Unsupported, conflicting, restricted, or stale evidence must be denied or escalated.
- Do not read private mail, scrape Teams chats, treat Busy presence as consent, send real notifications, or impersonate a person.
- Never put credentials, access tokens, or real employee data in source control, fixtures, logs, or generated artifacts.

## Implementation
- Keep the MVP a modular monolith with a deterministic, database-backed workflow.
- Keep demo mode self-contained and runnable without Microsoft credentials or external AI services.
- Enterprise adapters are disabled by default and must use least-privilege, requester-scoped authorization.
- Keep fictional seed data reproducible and permission-scoped.
- Record architecture and progress in DECISIONS.md and PROGRESS.md.
- Do not claim enterprise readiness, certification, customer outcomes, or live Microsoft integration without evidence.

## Validation
- Add focused unit and API tests for authorization, lifecycle races, revocation, prompt injection, escalation, and supported answers.
- Never send Teams or Outlook messages during local tests.
- Document exact test/build results and limitations in the evaluation report.
