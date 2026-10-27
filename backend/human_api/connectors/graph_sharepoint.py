from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx


class GraphUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SharePointHit:
    item_id: str
    drive_id: str
    title: str
    web_url: str
    last_modified: str | None


class DelegatedSharePointSearch:
    """Search and fetch using a short-lived OBO token for the signed-in requester."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client or httpx.AsyncClient(base_url="https://graph.microsoft.com/v1.0",
                                                  timeout=20.0)

    async def search(self, requester_graph_token: str, query: str, size: int = 20) -> list[SharePointHit]:
        body = {"requests": [{"entityTypes": ["driveItem"], "query": {"queryString": query},
                              "from": 0, "size": max(1, min(size, 100)),
                              "fields": ["name", "id", "webUrl", "lastModifiedDateTime", "parentReference"]}]}
        try:
            response = await self.client.post("/search/query", json=body,
                                              headers={"Authorization": f"Bearer {requester_graph_token}"})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            # Keep Graph error bodies, which may contain protected names, out of logs and UI.
            raise GraphUnavailable("SharePoint search is temporarily unavailable.") from exc
        hits: list[SharePointHit] = []
        for group in data.get("value", []):
            for container in group.get("hitsContainers", []):
                for row in container.get("hits", []):
                    item = row.get("resource", {})
                    parent = item.get("parentReference", {})
                    if item.get("id") and parent.get("driveId"):
                        hits.append(SharePointHit(item["id"], parent["driveId"],
                                                  item.get("name", "SharePoint document"),
                                                  item.get("webUrl", ""),
                                                  item.get("lastModifiedDateTime")))
        return hits

    async def download(self, requester_graph_token: str, hit: SharePointHit) -> bytes:
        drive_id, item_id = quote(hit.drive_id, safe=""), quote(hit.item_id, safe="")
        try:
            response = await self.client.get(
                f"/drives/{drive_id}/items/{item_id}/content",
                headers={"Authorization": f"Bearer {requester_graph_token}"}, follow_redirects=True,
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as exc:
            raise GraphUnavailable("The requested SharePoint item is unavailable.") from exc

    async def close(self) -> None:
        await self.client.aclose()
