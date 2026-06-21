"""
growthlens.ingestion.comps_yfinance
====================================
Pulls public growth-equity comparables via the ``yfinance`` library, which
reads Yahoo Finance's public data. Free, no key.

Caveat (documented in the white paper): yfinance is an *unofficial* wrapper and
can break when Yahoo changes its endpoints. The functions here degrade
gracefully to None so the pipeline never hard-fails on a comps lookup.

What we extract per ticker: EV/Revenue (the canonical growth multiple),
revenue growth, gross margins and market cap — the fields a GE analyst uses to
benchmark a private target's implied valuation.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError:  # keep import-safe even if not installed
    yf = None


def fetch_comp(ticker: str) -> Optional[dict]:
    """Return a dict of valuation/growth metrics for one ticker, or None."""
    if yf is None:
        return None
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:  # noqa: BLE001 — yfinance raises many opaque errors
        return None
    if not info:
        return None
    return {
        "ticker": ticker,
        "name": info.get("shortName"),
        "market_cap": info.get("marketCap"),
        "ev_to_revenue": info.get("enterpriseToRevenue"),
        "revenue_growth": info.get("revenueGrowth"),
        "gross_margins": info.get("grossMargins"),
    }


def fetch_comps_for_vertical(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch comps for a list of tickers. Always returns a DataFrame (possibly
    empty), so downstream code can rely on the shape.
    """
    rows = [c for t in tickers if (c := fetch_comp(t)) is not None]
    cols = ["ticker", "name", "market_cap", "ev_to_revenue",
            "revenue_growth", "gross_margins"]
    return pd.DataFrame(rows, columns=cols)


def median_ev_revenue(tickers: list[str]) -> Optional[float]:
    """Median EV/Revenue across the peer set — the headline benchmark multiple."""
    df = fetch_comps_for_vertical(tickers)
    if df.empty or df["ev_to_revenue"].dropna().empty:
        return None
    return float(df["ev_to_revenue"].dropna().median())


if __name__ == "__main__":
    print(fetch_comps_for_vertical(["CRM", "NOW", "DDOG"]))
