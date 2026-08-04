"""Read-only HERO-Stammdaten-Suche (Projekte/Kontakte) — analog zum
Wärmebrücken-Tool (`HeroProjectPicker`). Die Web-App selbst hat keinen MCP-
Zugriff, deshalb wird direkt gegen die HERO GraphQL API gesprochen (nicht
über den hero-mcp-server).

Query-Feldnamen und Endpoint gegen das Live-Schema verifiziert (2026-08-04,
`__type(name: "PartnerQuery")`-Introspektion: `project_matches` hat ein
`search: String`-Argument).

Env:
    HERO_URL   — GraphQL-Endpoint, Default = offizieller HERO-Endpoint
    HERO_TOKEN — API-Key (identisch mit dem HERO_API_KEY des hero-mcp-server,
                 wird beim Deploy als Stack-Env injiziert, siehe README)
"""

from __future__ import annotations

import os
from typing import Any

import httpx

HERO_URL = os.environ.get("HERO_URL") or "https://login.hero-software.de/api/external/v7/graphql"
HERO_TOKEN = os.environ.get("HERO_TOKEN", "")

SEARCH_QUERY = """
query SearchProjects($search: String, $limit: Int) {
  project_matches(search: $search, first: $limit) {
    id
    display_id
    project_nr
    measure { name }
    current_project_match_status { name }
    contact { first_name last_name company_name }
    address { street city zipcode }
  }
}
"""


def configured() -> bool:
    return bool(HERO_TOKEN)


async def search_projects(query: str, limit: int = 15) -> list[dict[str, Any]]:
    if not configured() or not query.strip():
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            HERO_URL,
            json={"query": SEARCH_QUERY, "variables": {"search": query, "limit": limit}},
            headers={
                "Authorization": f"Bearer {HERO_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))

    matches = (data.get("data") or {}).get("project_matches") or []
    results = []
    for m in matches:
        contact = m.get("contact") or {}
        address = m.get("address") or {}
        name = contact.get("company_name") or " ".join(
            t for t in [contact.get("first_name"), contact.get("last_name")] if t
        )
        results.append({
            "hero_ref": m.get("display_id") or m.get("project_nr") or "",
            "kunde": name,
            "strasse": address.get("street") or "",
            "plz": address.get("zipcode") or "",
            "ort": address.get("city") or "",
            "measure": (m.get("measure") or {}).get("name") or "",
            "status": (m.get("current_project_match_status") or {}).get("name") or "",
        })
    return results
