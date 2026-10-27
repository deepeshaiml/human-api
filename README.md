# Human API

**A governed way to answer work questions when the colleague who knows is unavailable.**

Eureka hackathon project · Future of Work @ Presight · Concept stage

## In one minute

A knowledge owner can choose a limited set of questions that a software workflow may help with. The person asking still needs permission to open each source file. Human API shows an answer with its source and limits, or routes the question to a person.

**Example:** Alice asks why a service timeout changed from 90 to 120 seconds. Bob has opted in for questions about that project. The demo finds a written decision record Alice can read. It explains why the change happened, but does not say whether 120 seconds is still needed. Human API shows that partial answer with a citation; it does not pretend Bob wrote it.

**Current demo:** local web app, fictional people and files, deterministic word matching and answer templates. It uses no language model and is not connected to a Microsoft tenant. See the [plain-language reader guide](docs/READER_GUIDE.md) for an example, a glossary, and guidance for AI assistants reading the project.

## Run the demo

Prerequisites: Python 3.12 or later, Node.js 22.12 or later, and npm. Docker is optional.

```bash
cp .env.example .env
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock
cd frontend && npm ci && cd ..
make dev
```

Open <http://127.0.0.1:5173>. Use the identity selector to switch between fictional people. It is a demo convenience, **not sign-in or authentication**. The API runs on port 8000.

For the five-minute walkthrough, see [DEMO_GUIDE.md](DEMO_GUIDE.md). The main example shows a supported answer, a restricted request, a question without enough evidence, and a human correction that needs approval before reuse.

## Useful commands

```bash
# Run the API or web interface separately
make backend
cd frontend && npm run dev

# Type-check and build the web interface
make build

# Run backend checks and the labeled synthetic search evaluation
make test
make eval

# Apply the database schema to a configured database
DATABASE_URL=sqlite:///./backend/data/migrated_demo.db make migrate

# Optional: build and run the app with PostgreSQL in Docker
make compose

# Optional: render submission PDFs to page images and contact sheets
pip install -r scripts/requirements-qa.txt
python scripts/render_deliverables.py
```

The demo database lives at `backend/data/human_api_demo.db`; it is ignored by Git. Remove that file to reset the local demo. Use fictional data only.

## What is implemented

| Part | Status |
|---|---|
| Local web app | Runs with fictional identities and project files. |
| Question workflow | Saves questions, checks the owner's approved scope, checks the requester's access, then answers or sends the question to a person. |
| Human review | An expert can reply; a correction must be approved before it can be reused. |
| Microsoft sign-in and file access | Adapter scaffolding only; not tested in a real Microsoft tenant. |
| Teams bot | Not implemented. |
| Large language model | Not used. The demo matches words in approved files and uses fixed answer templates. |

## Safety boundary

Owner consent lets the workflow handle only the approved kind of question, for the approved audience and dates. It **does not** give the requester permission to see the owner's files. The app checks the requester's project and file access before using evidence, and checks access again before showing a saved answer.

The identity selector and availability status are fictional. Do not expose demo mode outside localhost or import real employee or Microsoft data. This prototype does not provide production encryption-key management, retention/deletion controls, sensitivity-label integration, rate limits, multi-server job coordination or a security certification.

## Microsoft connection status

The code includes early adapters for Microsoft Entra ID (work sign-in), Microsoft Graph (access to Microsoft 365 data) and Outlook out-of-office status. They are not wired into the enterprise question path and have not been tenant-tested. No inbox messages or Teams history are read. No Teams messages are sent. Busy presence is never treated as consent.

Before any pilot, the team needs a registered app, tenant-specific permission review, security/privacy review and tests proving that file access stays within the signed-in requester's permissions. See [Microsoft Graph permissions](docs/MICROSOFT_GRAPH_PERMISSIONS.md).

## Project map

- `docs/READER_GUIDE.md` — plain-language explanation, example, glossary and AI-assistant guidance.
- `backend/human_api/` — API, policy checks, evidence search and question workflow.
- `frontend/` — React and TypeScript web interface.
- `data/synthetic/seed.json` — reproducible fictional people, projects, policies and documents.
- `tests/` and `evaluations/` — workflow/security checks and labeled synthetic search cases.
- `docs/` — technical design, safety, Microsoft permissions, dependencies and competitive review.
- `deliverables/` — editable and PDF submissions, architecture diagram and app screenshot.

## Product direction

General enterprise search, citations and permission-aware answers already exist. Human API's narrower idea is the controlled handoff around one unanswered question: owner opt-in, clear limits, evidence, and a human path when the answer is incomplete. The research review also considers Microsoft's announced Autopilot and SharePoint team knowledge work; no claim of uniqueness has been proven. See [competitive analysis](docs/COMPETITIVE_ANALYSIS.md).

## Key terms

- **Requester:** the coworker asking the question.
- **Knowledge owner:** the coworker whose knowledge is needed.
- **Backup:** a named person who can answer when the system cannot.
- **Evidence:** an approved source passage that supports an answer.
- **Abstain:** say the evidence is not enough and hand the question to a person.
- **Synthetic data:** fictional records created for the demo.

The [reader guide](docs/READER_GUIDE.md) defines the technical terms too.
