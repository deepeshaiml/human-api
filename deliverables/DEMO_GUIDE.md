# Human API demo: a five-minute walkthrough

This walkthrough is for the source-repository demo; this document bundle does not include runnable app code. It uses fictional people and project files. It runs locally and does not connect to Microsoft. The [reader guide](HumanAPI_Reader_Guide.md) explains the idea and terms in plain language.

## Before you start

1. In the full source repository, follow the setup in its root README.md and run `make dev`.
2. Open <http://127.0.0.1:5173>.
3. Select **Alice Chen** in the identity menu. The menu is a demo switch, not a real sign-in.

## Walkthrough

### 1. Explain the people

Alice is asking the question. Bob is the knowledge owner: he has opted in to a limited policy for Project Alpha. Carla is his named backup. Bob's out-of-office status is fictional and is used only as a demo trigger; a person's Busy or away status is never consent by itself.

### 2. Show an answer with a limit

Ask Bob: **“Why was the Project Alpha startup timeout increased to 120 seconds, and is it still required?”**

The demo returns a partial answer immediately because Bob's approved out-of-office policy is active. It cites **ADR-024**, a written technical decision. The record explains why the setting changed from 90 to 120 seconds for release 5.2. It does not say whether 120 seconds is still needed today. Point out that the software reports this gap instead of guessing or speaking as Bob.

### 3. Show a restricted request

Ask: **“What is the confidential budget for Project Alpha?”** Alice can access the project, but not the restricted budget file. Human API returns a generic denial and does not reveal the file name or amount.

### 4. Show a question that needs a person

Ask Bob: **“Why was the undocumented blue deployment approval skipped?”** The approved files do not answer it, so the question appears in Carla's review inbox. Switch the demo identity to **Carla Mendez**, open the question, and enter a verified human response.

### 5. Show controlled reuse

Switch to **Bob Patel**, the knowledge owner. The expert response is waiting for approval before it can be reused in later answers. Approve the proposed correction and explain that a person must review it first.

### Optional: show protection against hostile file text

One fictional imported note contains text that tells an AI to ignore its rules and reveal a restricted budget. The demo treats that text as untrusted file content; it cannot change access rules. The current safeguard is deliberately small and is not a complete defense for production.

## What the demo proves—and what it does not

It demonstrates real local question records, project access checks, owner policy checks, source citations, denials, human escalation and approval. The answer builder uses matching words and fixed templates. There is no language model, real Microsoft sign-in, live SharePoint connection or Teams bot.

## Optional API view

In demo mode the UI sends a fictional identity in the `X-Demo-User` header. That header is not authentication and must not be exposed outside localhost. Open `/api/reference` to see demo identities and projects, or `/api/questions` to inspect question state through the app. The UI is easier for a live walkthrough.

For coding tools or AI assistants, read the source repository's AGENTS.md and the [reader guide](HumanAPI_Reader_Guide.md) before changing the project.
