from __future__ import annotations

from dataclasses import dataclass

import httpx

from .graph_sharepoint import GraphUnavailable


@dataclass(frozen=True)
class OwnerAbsenceSignal:
    status: str
    starts_at: str | None
    ends_at: str | None
    source: str = "owner's own Outlook automatic replies"


class OwnerScopedOutlook:
    """Read only the signed-in knowledge owner's own absence setting; no mailbox messages."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client or httpx.AsyncClient(base_url="https://graph.microsoft.com/v1.0",
                                                  timeout=15.0)

    async def own_absence(self, owners_graph_token: str) -> OwnerAbsenceSignal:
        try:
            response = await self.client.get(
                "/me/mailboxSettings/automaticRepliesSetting",
                headers={"Authorization": f"Bearer {owners_graph_token}"},
            )
            response.raise_for_status()
            value = response.json()
        except httpx.HTTPError as exc:
            raise GraphUnavailable("Owner availability could not be confirmed.") from exc
        # Return only the status and schedule. The automatic reply text is deliberately discarded.
        return OwnerAbsenceSignal(
            status=value.get("status", "disabled"),
            starts_at=(value.get("scheduledStartDateTime") or {}).get("dateTime"),
            ends_at=(value.get("scheduledEndDateTime") or {}).get("dateTime"),
        )

    async def close(self) -> None:
        await self.client.aclose()
