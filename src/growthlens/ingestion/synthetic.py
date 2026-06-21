"""
growthlens.ingestion.synthetic
==============================
Generates a realistic, *clearly synthetic* dataset of European growth-stage
startups so the entire pipeline runs end-to-end with zero API keys.

IMPORTANT — data provenance honesty:
    These rows are SYNTHETIC. They are statistically plausible but invented.
    The project's value is the *methodology* (scoring, memos, benchmarking),
    which is data-source-agnostic. The real connectors in this package
    (companies_house.py, macro_ecb.py, macro_eurostat.py, comps_yfinance.py)
    pull genuinely free/open data; private funding data is paywalled industry-
    wide (Crunchbase Pro / PitchBook / Dealroom) and is NOT scraped here.

Every generated field maps to an input the GE Readiness Score actually uses, so
the synthetic data is a faithful stand-in for what a paid feed would supply.
"""
from __future__ import annotations

from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker

from growthlens.config import VERTICALS

# Stable, well-known European startup hubs (country -> typical HQ cities)
_HUBS = {
    "United Kingdom": ["London", "Cambridge", "Manchester"],
    "Germany": ["Berlin", "Munich", "Hamburg"],
    "France": ["Paris", "Lyon"],
    "Netherlands": ["Amsterdam", "Rotterdam"],
    "Sweden": ["Stockholm"],
    "Spain": ["Barcelona", "Madrid"],
    "Italy": ["Milan"],
    "Ireland": ["Dublin"],
    "Estonia": ["Tallinn"],
}

_STAGE_BY_LAST_ROUND = ["Seed", "Series A", "Series B", "Series C"]

# Plausible last-round size ranges (EUR millions) by stage
_ROUND_SIZE_EUR_M = {
    "Seed": (0.5, 4),
    "Series A": (4, 18),
    "Series B": (18, 60),
    "Series C": (60, 180),
}


def _suffix(rng: np.random.Generator) -> str:
    return rng.choice(["AI", "Labs", "ly", "io", "flow", "stack", "hub", "core", "wise"])


def generate_companies(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Build a DataFrame of ``n`` synthetic European startups.

    Parameters
    ----------
    n : int
        Number of companies to generate.
    seed : int
        Reproducibility seed (controls both numpy and Faker).

    Returns
    -------
    pandas.DataFrame
        One row per company with all fields the scoring model consumes.
    """
    rng = np.random.default_rng(seed)
    fake = Faker()
    Faker.seed(seed)

    today = date.today()
    rows = []

    for i in range(n):
        vertical = rng.choice(VERTICALS)
        country = rng.choice(list(_HUBS.keys()))
        city = rng.choice(_HUBS[country])

        # Last round stage skews toward A/B (the GE feeder stages)
        stage = rng.choice(_STAGE_BY_LAST_ROUND, p=[0.20, 0.40, 0.30, 0.10])
        lo, hi = _ROUND_SIZE_EUR_M[stage]
        last_round_eur_m = round(float(rng.uniform(lo, hi)), 1)

        # Time since last round (months). Mixture: most 6-30m, a stale tail.
        months_since = int(np.clip(rng.normal(20, 9), 1, 54))
        last_round_date = today - timedelta(days=int(months_since * 30.4))

        founded_year = today.year - int(np.clip(rng.normal(6, 3), 1, 18))

        # --- Growth signals -------------------------------------------------
        # Revenue growth YoY (%). Heavy-tailed: a few rockets, many mediocre.
        rev_growth_yoy = round(float(np.clip(rng.gamma(2.0, 35), 5, 400)), 1)
        # Web traffic growth as an independent demand proxy (%).
        traffic_growth_yoy = round(float(np.clip(rng.normal(rev_growth_yoy * 0.6, 25), -20, 350)), 1)

        # --- Team -----------------------------------------------------------
        headcount = int(np.clip(rng.lognormal(mean=4.0, sigma=0.7), 8, 1200))
        # 6-month headcount growth (%). NOTE: in production this is the field a
        # paid people-data API would fill; we do NOT scrape LinkedIn for it.
        headcount_growth_6m = round(float(np.clip(rng.normal(18, 20), -30, 150)), 1)
        # Founder track record: 0=first-time, 1=prior startup, 2=prior exit.
        founder_track = int(rng.choice([0, 1, 2], p=[0.55, 0.30, 0.15]))

        # --- Market ---------------------------------------------------------
        tam_eur_bn = round(float(np.clip(rng.gamma(2.0, 8), 1, 120)), 1)

        # --- Capital efficiency --------------------------------------------
        # Burn multiple = net cash burned / net new ARR. Lower is better.
        burn_multiple = round(float(np.clip(rng.normal(1.8, 0.9), 0.2, 6.0)), 2)

        # --- Moat proxies ---------------------------------------------------
        patents = int(np.clip(rng.poisson(1.2), 0, 30))
        is_regulated = int(rng.random() < (0.5 if vertical in {"fintech", "healthtech"} else 0.1))
        network_effect = int(rng.random() < 0.35)

        name = f"{fake.unique.company().split(',')[0].split(' ')[0]}{_suffix(rng)}"

        rows.append(
            {
                "company_id": f"GL{i:04d}",
                "name": name,
                "vertical": vertical,
                "country": country,
                "city": city,
                "founded_year": founded_year,
                "last_round_stage": stage,
                "last_round_eur_m": last_round_eur_m,
                "last_round_date": last_round_date.isoformat(),
                "months_since_last_round": months_since,
                "rev_growth_yoy_pct": rev_growth_yoy,
                "traffic_growth_yoy_pct": traffic_growth_yoy,
                "headcount": headcount,
                "headcount_growth_6m_pct": headcount_growth_6m,
                "founder_track_record": founder_track,
                "tam_eur_bn": tam_eur_bn,
                "burn_multiple": burn_multiple,
                "patents": patents,
                "is_regulated": is_regulated,
                "network_effect": network_effect,
                "data_provenance": "synthetic",  # honesty flag carried through pipeline
            }
        )

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":  # quick manual smoke test
    demo = generate_companies(10)
    print(demo[["name", "vertical", "rev_growth_yoy_pct", "months_since_last_round"]])
