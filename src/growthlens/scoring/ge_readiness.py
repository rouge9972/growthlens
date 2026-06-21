"""
growthlens.scoring.ge_readiness
===============================
The GE Readiness Score (GRS): a transparent, six-pillar composite that ranks
private growth-stage companies by their readiness for a Growth Equity round.

Design principles (see docs/methodology_whitepaper.md for the full argument):
    1. Transparency over black-box ML. Every point in a company's score can be
       attributed to a specific pillar and input. An IC can interrogate it.
    2. Cohort-relative. Scores are normalized *within the analysed universe*,
       so the GRS answers "who is most ready, relative to peers we can see?"
       rather than asserting a false absolute.
    3. Config-driven. All weights/curves live in config/scoring_weights.yaml.
       The code computes; the YAML decides. This is what makes it auditable.

The six pillars
    growth_signal      revenue + traffic growth (the single heaviest pillar)
    timing             distance from the typical 14-26 month raise window
    team               headcount growth + founder track record
    market             TAM + sector momentum
    capital_efficiency burn discipline (burn multiple)
    moat               IP, regulation barriers, network effects

Output: a 0-100 score per company plus the per-pillar sub-scores (for the memo
and the dashboard's score-attribution bar).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from growthlens.config import ScoringConfig
from growthlens.cleaning.normalize import min_max_scale, winsorize


# --------------------------------------------------------------------------- #
# Individual pillar computations. Each returns a pd.Series in [0,1].
# --------------------------------------------------------------------------- #
def _pillar_growth(df: pd.DataFrame) -> pd.Series:
    """Blend revenue growth (70%) and traffic growth (30%), winsorized."""
    rev = min_max_scale(winsorize(df["rev_growth_yoy_pct"]))
    traffic = min_max_scale(winsorize(df["traffic_growth_yoy_pct"]))
    return 0.70 * rev + 0.30 * traffic


def _pillar_timing(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    """
    Triangular readiness curve over months-since-last-round.

    Peaks (=1.0) inside the ideal window, decays linearly to the hard floor
    (too soon) and hard ceiling (too stale). Outside those -> ~0.
    """
    t = cfg.timing
    m = df["months_since_last_round"].astype(float)

    def score_one(x: float) -> float:
        if x < t["hard_floor_months"] or x > t["hard_ceiling_months"]:
            return 0.0
        if t["ideal_min_months"] <= x <= t["ideal_max_months"]:
            return 1.0
        if x < t["ideal_min_months"]:  # ramp up
            return (x - t["hard_floor_months"]) / (t["ideal_min_months"] - t["hard_floor_months"])
        # ramp down
        return (t["hard_ceiling_months"] - x) / (t["hard_ceiling_months"] - t["ideal_max_months"])

    return m.map(score_one).clip(0, 1)


def _pillar_team(df: pd.DataFrame) -> pd.Series:
    """Headcount growth (65%) + founder track record (35%)."""
    hc = min_max_scale(winsorize(df["headcount_growth_6m_pct"]))
    founder = df["founder_track_record"].astype(float) / 2.0  # 0,1,2 -> 0,0.5,1
    return 0.65 * hc + 0.35 * founder


def _pillar_market(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    """TAM (55%) + sector momentum prior (45%)."""
    tam = min_max_scale(winsorize(df["tam_eur_bn"]))
    momentum = df["vertical"].map(cfg.sector_momentum).fillna(0.5).astype(float)
    return 0.55 * tam + 0.45 * momentum


def _pillar_capital_efficiency(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    """
    Map burn multiple to [0,1] where lower burn = higher score.
    good -> 1.0, bad -> 0.0, linear in between (then clipped).
    """
    ce = cfg.capital_efficiency
    good, bad = ce["burn_multiple_good"], ce["burn_multiple_bad"]
    bm = df["burn_multiple"].astype(float)
    score = (bad - bm) / (bad - good)
    return score.clip(0, 1)


def _pillar_moat(df: pd.DataFrame) -> pd.Series:
    """Patents (scaled) + regulation barrier + network effect, blended."""
    patents = min_max_scale(winsorize(df["patents"]))
    reg = df["is_regulated"].astype(float)
    net = df["network_effect"].astype(float)
    return (0.4 * patents + 0.3 * reg + 0.3 * net).clip(0, 1)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
PILLAR_FUNCS = {
    "growth_signal": lambda df, cfg: _pillar_growth(df),
    "timing": lambda df, cfg: _pillar_timing(df, cfg),
    "team": lambda df, cfg: _pillar_team(df),
    "market": lambda df, cfg: _pillar_market(df, cfg),
    "capital_efficiency": lambda df, cfg: _pillar_capital_efficiency(df, cfg),
    "moat": lambda df, cfg: _pillar_moat(df),
}


def score_companies(df: pd.DataFrame, cfg: ScoringConfig) -> pd.DataFrame:
    """
    Compute the GE Readiness Score for every company.

    Returns the input frame plus:
        - one ``pillar_<name>`` column per pillar (0..1 sub-scores)
        - ``ge_readiness_score`` (0..100)
        - ``tier`` (label from config bands)
        - ``rank`` (1 = most ready)
    """
    out = df.copy()

    weighted = pd.Series(0.0, index=out.index)
    for name, func in PILLAR_FUNCS.items():
        sub = func(out, cfg).astype(float)
        out[f"pillar_{name}"] = sub.round(4)
        weighted += cfg.pillar_weights[name] * sub

    out["ge_readiness_score"] = (weighted * 100).round(1)
    out["tier"] = out["ge_readiness_score"].map(lambda s: _band_label(s, cfg))
    out["rank"] = out["ge_readiness_score"].rank(ascending=False, method="first").astype(int)
    return out.sort_values("ge_readiness_score", ascending=False).reset_index(drop=True)


def _band_label(score: float, cfg: ScoringConfig) -> str:
    for band in cfg.bands:  # bands are ordered high -> low in YAML
        if score >= band["min"]:
            return band["label"]
    return cfg.bands[-1]["label"]


def explain_score(row: pd.Series, cfg: ScoringConfig) -> pd.DataFrame:
    """
    Per-company attribution table: how many of the 100 points each pillar
    contributed. Used in memos and the dashboard. Points sum to the GRS.
    """
    records = []
    for name in PILLAR_FUNCS:
        sub = row[f"pillar_{name}"]
        contribution = cfg.pillar_weights[name] * sub * 100
        records.append(
            {
                "pillar": name,
                "sub_score_0_1": round(sub, 3),
                "weight": cfg.pillar_weights[name],
                "points": round(contribution, 1),
            }
        )
    return pd.DataFrame(records).sort_values("points", ascending=False)
