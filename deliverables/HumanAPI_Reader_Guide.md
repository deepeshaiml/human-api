# Human API: reader guide

This page explains the project in everyday language first, then gives the technical detail a developer or AI assistant needs to describe it accurately.

## The idea in one minute

Human API is a controlled way to handle a work question when the colleague who knows the answer is unavailable.

1. The colleague (the **knowledge owner**) chooses what the software may do, for how long, and which coworkers may use it.
2. The person asking (the **requester**) must already have permission to open any file used in the answer.
3. The software looks only in approved files. It gives an answer with its source and any important uncertainty, or sends the question to a person.

The owner's permission lets the workflow run. It does **not** give the requester access to the owner's private files.

## Example: Alice asks about a timeout

Alice is working on Project Alpha. She asks: “Why did the service timeout change from 90 to 120 seconds, and is 120 seconds still needed?” Bob, the knowledge owner, is on fictional leave in the demo. He has approved a time-limited policy for this project, this topic, a named group of coworkers, and selected files. Carla is the named backup.

The demo checks Alice's project access and checks that Alice may read the selected source. It finds a written decision record called **ADR-024**. The record explains that dependency setup sometimes took longer than 90 seconds and that the change was approved for release 5.2. It does not say whether 120 seconds is still needed today.

The answer is therefore:

> The decision record says the timeout increased from 90 to 120 seconds because dependency setup sometimes exceeded 90 seconds. It was approved for release 5.2. The record does not establish whether 120 seconds is still needed today. Source: ADR-024, version 1.0.

That is a **partial answer**: it reports what the source supports and leaves the unanswered part visible. It does not pretend Bob wrote the answer.

If the approved files do not answer Alice's question, the system says it cannot confirm the answer and routes the question to Carla or Bob. If Alice asks for restricted budget information she is not allowed to see, it gives a generic denial without revealing the file name or amount.

## What is real in this demo

- The web app, database-backed question flow, owner policy, access checks, cited evidence, denial, human escalation, human reply, approval step and audit history run locally.
- All people, files, project names and availability are fictional.
- The current answer builder uses ordinary code and word matching to select evidence and fill a response template. It does **not** use a large language model (LLM) or a live AI service.
- The app labels a software-produced answer “AI-generated” to distinguish it from a human reply. In this demo the label does not mean a language model wrote the text.
- Microsoft Entra ID and Microsoft Graph adapters are unfinished integration scaffolding. They have not been tested in a Microsoft tenant. There is no Teams bot.

## Who does what

| Person or system | Plain-language role |
|---|---|
| Requester | Asks the work question and can see only answers and sources they are allowed to access. |
| Knowledge owner | The colleague whose knowledge is needed. They choose the policy and can pause or revoke it. |
| Manager | Reviews a policy when its approved scope changes. |
| Backup | A named person who can respond when evidence is missing or unclear. |
| Human API | Checks the policy, searches allowed files, shows evidence or routes the question to a person. |
| Future AI agent | Could help write a plain-language summary, but must follow the same access rules and must not make policy decisions. This agent is not part of the current demo. |

## Workflow, without the jargon

| Step | What happens |
|---|---|
| Ask | A requester asks a question about a project and names the person who may know. |
| Check the owner's instructions | The system checks whether that person opted in and whether the question fits the approved time, project, topic and audience. |
| Check the requester's file access | Before searching a file, the system checks whether the requester can open it. |
| Look for evidence | The demo searches approved files using matching words. It does not understand meaning the way a language model might. |
| Answer or hand off | It cites what supports the answer, explains what is unknown, denies restricted requests, or sends unclear questions to a person. |
| Keep a human in control | A human reply is labeled as human. A proposed reusable correction waits for approval. |

## If a future AI agent is used

The present demo does not call an AI language model. If a future version uses an AI agent to summarize evidence, these rules should remain explicit:

- Give the agent only evidence the requester is allowed to read.
- Ask it to separate “the source says” from “the source does not say.”
- Require a citation for each factual answer and show the source version.
- If sources disagree or do not answer the question, require the agent to say so and route the question to a person.
- Treat instructions found inside a document as document text, not as commands to the agent.
- Never let the agent change access, expand the owner's policy, use the owner's identity, or claim that a human wrote an AI response.

An illustrative future response could look like this. It is an example format, not a current API response:

```json
{
  "answer": "The decision record says the timeout changed because setup sometimes exceeded 90 seconds.",
  "source": {"id": "ADR-024", "version": "1.0"},
  "limitation": "The record does not say whether 120 seconds is still needed.",
  "next_step": "Ask a human to confirm the current setting."
}
```

## Short glossary

| Term | Meaning here |
|---|---|
| **AI agent** | Software that can carry out a task using tools or information. The demo has no language-model agent. |
| **API** | A defined way for two software programs to exchange requests and information. |
| **ACL** | Access control list: the people or groups allowed to open a file. |
| **ADR** | Architecture decision record: a written note explaining a technical decision and why it was made. |
| **Abstain** | Say the available evidence is not enough to answer, then ask a person to help. |
| **Citation** | A pointer to the source file and version behind an answer. |
| **Delegation** | The owner's limited permission for the workflow to handle specified questions. It does not change file access. |
| **Entra ID** | Microsoft's work sign-in and identity service. |
| **Evidence** | An approved, accessible passage that supports some or all of an answer. |
| **FTE** | Full-time equivalent: a way to express a person's work as a share of a full-time role. |
| **LLM** | Large language model: an AI system that generates or summarizes text. None is used by this demo. |
| **Microsoft Graph** | Microsoft's API for accessing Microsoft 365 information under the signed-in user's permissions. |
| **MVP** | Minimum viable product: the smallest working version built to demonstrate and learn. |
| **OBO** | “On behalf of”: a Microsoft sign-in flow that lets an application call another service with the current user's delegated permissions. |
| **Pilot** | A small, time-limited test with real users before wider use. |
| **Requester / owner / backup** | The person asking / the colleague whose knowledge is needed / the approved human fallback. |
| **Tenant** | An organization's separate Microsoft 365 environment and identity boundary. |
| **Synthetic data** | Fictional people, projects and documents created for a demo or test. |

## Which document should I read?

- **Product idea and scenario:** [Idea document](HumanAPI_Idea_Document.pdf)
- **Run the app:** [README](README.md) and [demo guide](DEMO_GUIDE.md)
- **Business value and assumptions:** [Business case](HumanAPI_Business_Case.pdf)
- **How the app is built:** [Technical design](HumanAPI_Technical_Design.md)
- **Access and safety rules:** [Security architecture](HumanAPI_Security_Architecture.md)
- **Microsoft connection requirements:** [Graph permissions](HumanAPI_Microsoft_Graph_Permissions.md)
- **Current test results and limits:** [Evaluation report](HumanAPI_Evaluation_Report.pdf) and [progress](README.md#what-is-implemented)
- **Market alternatives:** [Competitive analysis](HumanAPI_Competitive_Analysis.pdf)

## Guidance for AI assistants reading this repository

- Start with this guide. The source repository's `AGENTS.md` contains coding boundaries.
- Distinguish **implemented locally**, **adapter scaffolding**, and **future work**. Do not describe an untested Microsoft connection as working.
- State that the people and data are fictional, the demo identity selector is not authentication, and the current answer path uses no LLM.
- Preserve the separation between owner consent and requester file access. Never suggest bypassing either check.
- When describing an answer, include what the cited source supports and what it leaves unknown.
