"""
growthlens.ingestion.macro_ecb
==============================
Connector for the ECB Data Portal (SDMX 2.1 REST API). Completely free, no key.

Docs: https://data.ecb.europa.eu/help/api/overview

We pull the macro context that frames every growth-equity decision:
the policy rate environment. A rising-rate regime compresses growth multiples
and lengthens fundraising cycles; the dashboard overlays this on sector trends.

Default series: the ECB Main Refinancing Operations (MRO) fixed rate.
"""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import requests

_BASE = "https://data-api.ecb.europa.eu/service/data"

# Flow + key for the MRO fixed rate (FM dataset). Documented, stable series.
_MRO_FLOW = "FM"
_MRO_KEY = "D.U2.EUR.4F.KR.MRR_FR.LEV"


def fetch_policy_rate(start: str = "2019-01-01", timeout: int = 20) -> Optional[pd.DataFrame]:
    """
    Fetch the ECB main refinancing rate as a tidy DataFrame [date, policy_rate].

    Returns None on any network failure so the pipeline stays runnable offline.
    """
    url = f"{_BASE}/{_MRO_FLOW}/{_MRO_KEY}"
    try:
        resp = requests.get(
            url,
            params={"startPeriod": start, "format": "csvdata"},
            headers={"Accept": "text/csv"},
            timeout=timeout,
        )
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    except (requests.RequestException, ValueError):
        return None

    # SDMX csvdata returns TIME_PERIOD / OBS_VALUE columns.
    if not {"TIME_PERIOD", "OBS_VALUE"}.issubset(df.columns):
        return None
    out = (
        df[["TIME_PERIOD", "OBS_VALUE"]]
        .rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": "policy_rate"})
        .assign(date=lambda d: pd.to_datetime(d["date"]))
        .sort_values("date")
        .reset_index(drop=True)
    )
    return out


def latest_policy_rate() -> Optional[float]:
    """Convenience: the most recent policy rate, or None if unavailable."""
    df = fetch_policy_rate()
    if df is None or df.empty:
        return None
    return float(df["policy_rate"].iloc[-1])


if __name__ == "__main__":
    r = latest_policy_rate()
    print(f"Latest ECB MRO rate: {r}")
