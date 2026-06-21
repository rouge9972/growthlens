"""
growthlens.ingestion.companies_house
=====================================
Connector for the UK Companies House public API — a *genuinely free*,
official government API (registration required for a free key, no payment).

Docs: https://developer.company-information.service.gov.uk/

Scope & honesty:
    - This returns real, statutory filing data (registered office, incorporation
      date, SIC codes, officers) for UK-registered companies only.
    - It does NOT provide funding rounds, revenue, or headcount. No free source
      does at scale — that data is paywalled (Crunchbase Pro / PitchBook /
      Dealroom). The white paper documents this limitation explicitly.
    - Use this to *enrich* and *verify* the existence/age of UK targets, not to
      build growth signals.

Set your key in the environment:  export COMPANIES_HOUSE_API_KEY="..."
"""
from __future__ import annotations

import os
from typing import Optional

import requests

_BASE = "https://api.company-information.service.gov.uk"


def _auth() -> Optional[tuple[str, str]]:
    key = os.environ.get("COMPANIES_HOUSE_API_KEY")
    # Companies House uses HTTP Basic auth with the key as username, blank pw.
    return (key, "") if key else None


def search_company(query: str, items: int = 5, timeout: int = 15) -> list[dict]:
    """
    Search the register by company name.

    Returns a list of light-weight match dicts, or [] if no key / no network.
    Never raises on network failure — the pipeline must survive offline.
    """
    auth = _auth()
    if auth is None:
        return []
    try:
        resp = requests.get(
            f"{_BASE}/search/companies",
            params={"q": query, "items_per_page": items},
            auth=auth,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.RequestException:
        return []


def get_company_profile(company_number: str, timeout: int = 15) -> Optional[dict]:
    """
    Fetch the full statutory profile for a company number.

    Returns the profile dict, or None on any failure.
    """
    auth = _auth()
    if auth is None:
        return None
    try:
        resp = requests.get(
            f"{_BASE}/company/{company_number}",
            auth=auth,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def enrich_uk_company(name: str) -> dict:
    """
    Best-effort enrichment: resolve a name to its registered incorporation date
    and status. Returns {} when offline or unmatched, so callers can fall back
    cleanly to synthetic / manual values.
    """
    hits = search_company(name, items=1)
    if not hits:
        return {}
    top = hits[0]
    number = top.get("company_number")
    profile = get_company_profile(number) if number else None
    if not profile:
        return {"company_number": number, "ch_matched_title": top.get("title")}
    return {
        "company_number": number,
        "ch_matched_title": profile.get("company_name"),
        "ch_date_of_creation": profile.get("date_of_creation"),
        "ch_status": profile.get("company_status"),
        "ch_sic_codes": profile.get("sic_codes", []),
    }


if __name__ == "__main__":
    # Manual check (requires COMPANIES_HOUSE_API_KEY). Prints {} if unset.
    print(enrich_uk_company("Monzo"))
