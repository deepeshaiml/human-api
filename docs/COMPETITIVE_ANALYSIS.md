# Competitive analysis: Human API

**Checked:** 26 October 2026. Vendor product and licensing details change; this is a capability comparison from public sources, not a procurement or feature parity assessment. “Not evidenced” means the cited public material did not establish a feature; it is not proof that the vendor cannot provide it.

## The finding in plain language

Many products already search company files, summarize them and respect file permissions. Human API should not be presented as a new search engine. Its narrower idea is to manage one unanswered question: the knowledge owner opts in, a clear response window applies, the requester can open every source, and a human takes over if the evidence is weak.

For example, Alice asks why a project setting changed. Bob has allowed that topic and project. Human API can show a source Alice may read, say what it does and does not establish, and route the question to Carla if the current value is unclear. Whether teams need this extra workflow when Microsoft tools can be configured is still an open question; a pilot and customer interviews should decide.

For terms such as “requester,” “owner” and “evidence,” see the [reader guide](READER_GUIDE.md).

## Capability comparison

| Capability | Human API MVP | Microsoft 365 Copilot | Copilot Studio | SharePoint agents | Microsoft Autopilot (formerly Scout) | Glean | Moveworks |
|---|---|---|---|---|---|---|---|
| Enterprise search / grounded answers | Synthetic documents; lexical match | Yes, grounded in Microsoft 365 work context | Can connect knowledge and actions | SharePoint-scoped knowledge | Microsoft announced Microsoft IQ grounding | Yes, cross-app search and citations | Yes, search and summarization |
| Check who can open each file | Demo checks requester access before search | Existing Microsoft permissions | Depends on configured connectors/identity | Existing per-source access enforced | Announced tenant identity, permissions and governance | Connector permissions personalize results | Connector and tenant configuration; implementation-specific |
| Persistent/proactive agent | No | New Cowork/Autopilot direction overlaps | Workflow/agent building | Scoped source agent | Announced persistent, proactive agent; private preview at end Sep 2026 | Agents/workflows | Ambient agents and event/schedule capabilities |
| Employee-specific delegated knowledge | Owner policy per person in demo | Personal/contextual Copilot; no public direct match to this exact workflow established | Could build an explicit owner-consent workflow | Per-agent access controls; not the same as unanswered request lifecycle | Personal agent with own identity; significant conceptual overlap | People graph and agents; exact time-boxed owner policy not evidenced | Assistant plus handoff; exact employee-delegation pattern not evidenced |
| Configurable unanswered-question timeout | Yes (demo workflow) | Not evidenced in cited overview | Could be implemented with workflow/trigger logic | Not documented as native behavior | Persistent follow-up described; specific unanswered-question deadline not established | Workflows can be configured; specific employee timeout not evidenced | Handoff exists; exact owner-specific timeout not evidenced |
| Human escalation | Backup/owner queue | Existing collaboration/human follow-up | Human assistance nodes supported | Not central to source agent | Agent governance and follow-up; exact Human API queue not established | Workflow/approval capabilities | Smart handoff and ticket/agent options |
| Human correction and controlled knowledge reuse | Yes, approval gate | Copilot feedback/content editing; not same lifecycle | Can model approval and knowledge updates | Owner-created source content | Product's own persistent memory; external correction workflow not established | Agent workflows; exact lifecycle varies | Feedback does not automatically change behavior per docs |
| Integration direction | Web demo; Teams/Graph scaffold | Best initial host surface | Strong candidate for workflow prototype | Good for site-specific knowledge | Direct product overlap to monitor | Cross-platform suite | Enterprise assistant suite |
| Public price | None | License and eligible base plans; current quote/plan dependent | User/tenant/capacity or usage-based terms | Some licensing/usage requirements | Announced usage-based billing for agentic capabilities; private preview status | Quote-based; no comparable public rate verified | Quote-based; no comparable public rate verified |

## Competitive findings

Enterprise search, source citations, permission-aware results, agents, background workflows and human handoff are already available in the market. Microsoft, Glean and Moveworks each describe some of these capabilities. Microsoft also announced Autopilot (previously Scout) as a proactive persistent agent and a Copilot-curated SharePoint team knowledge base. These developments make a broad “AI delegate while a colleague is absent” uniqueness claim difficult to defend.

The possible distinction is the whole question-handling sequence: an employee asks; the owner limits which questions can be handled and for how long; the requester can still access every source; the answer shows its evidence or stops; a named person can take over; and a correction needs approval before reuse. This is a product hypothesis, not a proven unique feature. Compare it with configurable Microsoft workflows and customer needs before investing further.

## Recommendation

Build a Teams/Copilot Studio extension or agent workflow first, using Microsoft 365 permissions and identity, rather than building a general enterprise search product. Prototype the continuity policy and audit/correction loop as the differentiator. Only invest in a standalone platform if pilot users need cross-platform workflows or governance that existing Copilot, SharePoint agents, Glean or Moveworks cannot configure economically. Treat Autopilot as an active competitor and partner surface; reassess capabilities after preview access and customer testing.

## Licenses, admin controls, and integration

- Microsoft 365 Copilot features require eligible user/base licensing. Agentic use may have separate usage-based billing and organizational controls; verify the tenant's current licensing SKU and contract.
- Copilot Studio requires tenant/user authorization and may incur capacity or pay-as-you-go consumption; admin enablement and environment governance matter.
- SharePoint agent access follows source permissions and requires applicable licensing/usage setup.
- Teams app needs tenant custom app upload/sideloading and a public HTTPS bot endpoint; Graph scopes need delegated consent and sometimes admin consent.
- Glean and Moveworks public technical material does not establish comparable list pricing; get a vendor quote.
- Microsoft Autopilot announcement says private preview expanding at end of September 2026, not general availability. Enterprise access/status is tenant-specific.

## Sources

- Microsoft [Copilot with Home, Code and Autopilot announcement](https://blogs.microsoft.com/blog/2026/09/25/introducing-the-new-copilot-with-home-code-and-autopilot/) (25 Sep 2026)
- Microsoft [M365 agents FAQ](https://learn.microsoft.com/en-us/microsoft-365/copilot/agent-essentials/m365-agents-faq)
- Microsoft [SharePoint agents access](https://learn.microsoft.com/en-us/sharepoint/manage-access-agents-in-sharepoint)
- Microsoft [Copilot Studio human assistance node](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-node-workflow)
- Microsoft [Copilot Studio licensing](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-licensing)
- Microsoft [SharePoint Copilot overview](https://learn.microsoft.com/sharepoint/copilot-in-sharepoint-get-started)
- Microsoft [team knowledge base curated by Copilot and agents](https://techcommunity.microsoft.com/blog/spblog/introducing-a-team-knowledge-base-curated-by-copilot-and-agents/4564203) (14 Oct 2026)
- Microsoft [What's new in Copilot in SharePoint: October 2026](https://techcommunity.microsoft.com/blog/spblog/what%E2%80%99s-new-in-copilot-in-sharepoint-october-2026/4535423) (GA rollout started 30 Sep 2026)
- Glean [What is Glean?](https://docs.glean.com/user-guide/about/what-is-glean), [information access](https://docs.glean.com/user-guide/assistant/how-glean-accesses-info), [agents](https://docs.glean.com/agents)
- Moveworks [Assistant capabilities](https://help.moveworks.com/ai-assistant/capabilities), [Assistant overview](https://help.moveworks.com/ai-assistant/overview)

All sources accessed 26 October 2026.
