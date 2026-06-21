"""
growthlens.ingestion.macro_eurostat
====================================
Connector for the Eurostat dissemination API (JSON-stat 2.0). Free, no key.

Docs: https://ec.europa.eu/eurostat/web/main/data/web-services

Used for country-level real-economy context (default: real GDP growth),
which feeds the macro overlay on the dashboard and the "market" pillar prior.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import requests

_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def fetch_gdp_growth(timeout: int = 20) -> Optional[pd.DataFrame]:
    """
    Fetch real GDP growth (chain-linked volumes, % change) for EU members.

    Returns a tidy DataFrame [geo, period, gdp_growth] or None on failure.
    Dataset: namq_10_gdp (quarterly national accounts).
    """
    url = f"{_BASE}/namq_10_gdp"
    params = {
        "format": "JSON",
        "lang": "EN",
        "unit": "CLV_PCH_PRE",  # % change on previous period, chain-linked vols
        "s_adj": "SCA",
        "na_item": "B1GQ",
    }
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return None

    try:
        geo_dim = payload["dimension"]["geo"]["category"]["index"]
        time_dim = payload["dimension"]["time"]["category"]["index"]
        values = payload["value"]
    except (KeyError, TypeError):
        return None

    geo_rev = {v: k for k, v in geo_dim.items()}
    time_rev = {v: k for k, v in time_dim.items()}
    n_time = len(time_dim)

    records = []
    for flat_idx, val in values.items():
        idx = int(flat_idx)
        geo_i, time_i = divmod(idx, n_time)
        records.append(
            {
                "geo": geo_rev.get(geo_i),
                "period": time_rev.get(time_i),
                "gdp_growth": val,
            }
        )
    df = pd.DataFrame(records).dropna()
    return df if not df.empty else None


if __name__ == "__main__":
    g = fetch_gdp_growth()
    print(None if g is None else g.tail())
