# Microsoft Graph permissions and integration contracts

Verified against Microsoft Learn on 26 October 2026. The Graph adapters are **not tenant-tested** and are not wired into the enterprise question path. User consent, tenant policies, workload licensing, app registration and admin approval remain customer-specific.

## For readers who do not work with Microsoft APIs

Microsoft Graph is the service applications use to access Microsoft 365 files and settings. **Delegated access** means a request runs with the signed-in person's permissions. The owner may approve Human API to handle a question, but the file search must still run as the person asking.

**Example:** Alice signs in and asks about a Project Alpha decision. The future integration would search SharePoint as Alice. If Alice cannot open a file in SharePoint, Human API must not use or reveal that file—even if Bob, the knowledge owner, can open it. The current code has early integration pieces, but the complete sign-in and search flow is not connected or tenant-tested.

The table below names the Microsoft permissions needed for possible future connections. A permission is not proof that the feature works: a Microsoft tenant owner must register the app, review consent, and test the exact access behavior. The [reader guide](READER_GUIDE.md) defines “requester,” “owner,” “delegation” and “OBO.”

## First integration boundary

| Purpose | Endpoint | Permission model | Status / notes |
|---|---|---|---|
| Search files visible to requester | `POST /v1.0/search/query`, `entityTypes: ["driveItem"]` | Delegated `Files.Read.All` or `Sites.Read.All` as documented for driveItem search; consent may require admin depending on tenant. | Adapter exists. Microsoft states search runs as signed-in user and applies item ACLs. Search scope is broad in permission name; validate least-privilege tenant options before deployment. |
| Fetch selected SharePoint item | `GET /v1.0/drives/{drive-id}/items/{item-id}/content` | Delegated `Files.Read` is the documented least-privileged scope; the signed-in user must already be able to access the item. | Adapter exists; requires requester token. Not called by enterprise API yet. |
| Read owner's own automatic replies | `GET /v1.0/me/mailboxSettings/automaticRepliesSetting` | Delegated `MailboxSettings.Read`; Microsoft lists delegated admin consent as not required by default. Tenant user-consent policy can still block it. Use `/me` with the owner's own signed-in token, never an application-wide mailbox token. | Adapter exists. It retains only status/schedule and discards response text. Must not read inbox. |
| Teams bot messaging | Teams SDK bot messaging endpoint (not a Graph endpoint) | Teams app/bot registration and platform permissions; Graph permissions depend on optional calls. | Not implemented. Current Teams SDK quickstart requires Node 22.12+, app registration, public HTTPS endpoint/tunnel, M365 tenant and custom app upload enabled. |
| Presence | Graph presence endpoints | Permission varies by endpoint (commonly `Presence.Read.All`); tenant/admin consent and policy apply. | Not used. Busy state is not delegation consent. Prefer explicit owner policy/OOO signal. |

The SharePoint Search API documentation lists `Files.Read.All` and `Sites.Read.All` scopes for driveItem search and states that results run in the signed-in user's delegated context, with ACL enforcement. It does not mean Human API should request both: select and validate the narrowest available permission in the target tenant. Delegated permission grants and admin-consent behavior depend on the scope and tenant consent policy. `Files.Read` is the documented least-privilege permission for the content download endpoint. Never substitute owner-level delegated credentials or app-only tenant-wide access for requester authorization.

## Sign-in and delegated access flow

1. The employee signs in with the organization's Microsoft work account.
2. Human API checks the sign-in token and confirms that the employee is registered for the service. Demo identity headers are disabled.
3. The app exchanges the employee's sign-in proof for a short-lived Microsoft Graph token. This “on behalf of” (OBO) step keeps the employee's permissions in place.
4. Graph searches as that employee. Any file the employee cannot open is excluded before evidence is processed.
5. Access errors stop the answer path. Tokens stay in memory for the request; raw tokens are not saved or logged.

The current Entra validator and OBO helper are scaffolding. They need a tenant app registration and security review; they have no live tenant proof.

## API behavior and operational constraints

- Graph REST v1.0 is the target for all listed calls. No beta endpoint is part of the integration plan.
- Handle `401` by refreshing/reacquiring through MSAL; `403` as access denied; `404` without disclosing item existence; `429` using `Retry-After`; and `5xx` with bounded retry and escalation.
- Graph throttling limits vary by resource/workload; do not hard-code a universal request-per-second claim. Apply bounded concurrency, honor `Retry-After`, use delta/change notifications only after validating workload, consent and revocation semantics.
- Search text/highlights and error payloads can contain sensitive content. Do not log them. Avoid persistent content indexing in first integration; if later needed, maintain per-user ACLs, version, deletion and revocation propagation.
- Teams message collection, Outlook inbox access, and owner-level search are excluded.

## Source references

- [Microsoft Search API overview and permissions](https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview?view=graph-rest-1.0)
- [Download driveItem content permissions](https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0)
- [Get mailbox settings v1.0](https://learn.microsoft.com/en-us/graph/api/user-get-mailboxsettings?view=graph-rest-1.0)
- [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference?view=graph-rest-1.0)
- [Teams SDK register app quickstart](https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/get-started/quickstart-register)
- [Copilot Studio licensing](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-licensing)
