# Architecture and product decisions

## 2026-10-26 — Start as a Microsoft 365 extension
**Decision:** Position Human API as a governed employee-specific continuity workflow that can be embedded in Teams/Copilot/SharePoint, not as another broad enterprise search index.

**Why:** Microsoft and competitors already offer enterprise knowledge search, agents, citations/grounded responses, access-aware retrieval, and human escalation. Microsoft Scout/Autopilot also extends proactive continuity in a personal-agent model. The defensible MVP hypothesis is the policy workflow: owner opt-in, explicit response windows, requester authorization, evidence checks, backup routing, and approved knowledge correction as one auditable interaction.

**Status:** Research-backed hypothesis, not proof of uniqueness. Must validate against vendor roadmaps and pilot users.

## 2026-10-26 — Modular monolith and deterministic workflow
Use one API and relational store for the MVP. State transitions, consent, access checks, timeout rules and escalation are deterministic. A local demo answer provider uses authorized evidence snippets and templates. LangGraph is not justified for this finite state machine; an optional model call adds no value to authorization and is not required to demonstrate workflow correctness.

## 2026-10-26 — Demo identity is a demo-only boundary
The local role picker selects fictional identities. It must never be described as Entra authentication. Production requires OIDC validation and requester-scoped delegated Graph access.

## 2026-10-26 — No mailbox or Teams-history ingestion
The MVP will only read explicitly approved synthetic documents. Microsoft mailbox content and historical Teams messages remain out of scope. An explicit OOO status may be an opt-in signal only when the enterprise integration has consented access and a separate delegation policy is already enabled.
