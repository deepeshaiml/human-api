# Dependency and license review

## In plain language

This page lists the software used to build and run the project, its version, and its published license. A **direct dependency** is a package this project intentionally uses. A **transitive dependency** is a package those tools install for themselves. Lockfiles record exact versions so another developer can rebuild the same setup. A clean vulnerability scan does not replace a security or legal review.

Package versions and license metadata were checked on 26 October 2026. This is an implementation inventory, not legal clearance. A Presight legal/security review is still required before distribution.

## Direct Python dependencies

| Package | Pin | Reported license | Use |
|---|---:|---|---|
| FastAPI | 0.162.0 | MIT | HTTP API |
| Pydantic | 2.14.1 | MIT | Request/data validation |
| SQLAlchemy | 2.1.6 | MIT | Persistence and ORM |
| Alembic | 1.20.1 | MIT | Schema migrations |
| Uvicorn | 0.54.0 | BSD-3-Clause | ASGI server |
| HTTPX | 0.28.1 | BSD-3-Clause | Microsoft Graph adapter HTTP |
| pytest | 9.1.1 | MIT | Test runner |
| python-docx | 1.2.0 | MIT | DOCX deliverable generator |
| ReportLab | 5.1.0 | BSD-style | PDF deliverable generator |
| MSAL | 1.39.0 | MIT | Entra / OBO adapter scaffolding |
| PyJWT | 2.15.1 | MIT | Entra JWT verification |
| psycopg + binary | 3.3.6 | LGPL-3.0-only | PostgreSQL driver |

The direct Python set is pinned in `backend/requirements.txt`; the transitive exact-version lock is `backend/requirements.lock`. The lock was generated from Python 3.12 on macOS ARM64 and should be regenerated for materially different supported environments.

## Direct JavaScript dependencies

| Package | Pin | Reported license | Use |
|---|---:|---|---|
| React / React DOM | 19.3.1 | MIT | UI |
| Lucide React | 1.61.0 | ISC | Icons |
| Vite | 8.3.5 | MIT | Frontend build/dev server |
| TypeScript | 7.0.2 | Apache-2.0 | Type checking |
| `@vitejs/plugin-react` | 6.1.2 | MIT | Vite integration |
| PptxGenJS | 4.0.1 | MIT | PowerPoint deck |
| image-size (override) | 2.0.4 | MIT | PptxGenJS transitive image metadata |

`frontend/package-lock.json` and `presentations/package-lock.json` pin transitive npm packages. The presentation lock overrides `image-size` to 2.0.4 because PptxGenJS 4.0.1's declared range otherwise resolves a version covered by advisories GHSA-5p2g-fcmc-qvqq and GHSA-w3rx-r6r6-pgpr. The deck generation was run with the override active.

Optional PDF render and contact-sheet QA uses `pypdfium2==5.14.0` (BSD-3-Clause/Apache-2.0; its PDFium binary also ships third-party license notices) and `Pillow==13.0.0` (MIT-CMU), pinned in `scripts/requirements-qa.txt`. These are not application-container dependencies.

## Advisory scan

On 26 October 2026, `pip-audit -r backend/requirements.txt` reported **no known vulnerabilities**. `npm audit` reported **0 vulnerabilities** for both `frontend/` and `presentations/` after the override. These registry-based scans do not guarantee package quality, eliminate undisclosed vulnerabilities, or replace a managed software composition analysis tool.

## Platform and data note

PostgreSQL is under the PostgreSQL License. Microsoft Entra ID, Graph, Teams, SharePoint and Copilot are proprietary hosted platform services. No model weights or model license are included; a future model must have a separate license, data residency, security and use-case review.
