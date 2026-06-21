"""
growthlens.backtest.real
========================
Run the ACTUAL GE Readiness model against REAL companies and REAL outcomes that
you hand-collected, so the backtest measures real-world discriminative power
(within the limits of free public data).

The honest mechanic:
    Most of the model's inputs are unobservable for private companies (revenue
    growth, burn multiple, headcount growth). You leave those blank. This loader
    fills any fully-missing feature with a NEUTRAL constant. After cohort
    normalization a constant column maps to 0.5 for everyone — so those pillars
    add a flat offset and contribute ZERO to the ranking. The companies are thus
    ranked only on what you could actually observe. The report states exactly
    which features were observed vs imputed ("observability coverage"), so the
    result is never overstated.

This is the bridge from "harness demo" to "tested on reality". See
docs/real_validation_protocol.md for how to collect the data without
survivorship bias.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Neutral fill values for features that are typically NOT publicly observable.
# Exact values don't affect ranking when a column is fully imputed (constant ->
# 0.5 after scaling); they're documented mid-points for transparency.
NEUTRAL_DEFAULTS = {
    "last_round_eur_m": 15.0,
    "months_since_last_round": 18,
    "rev_growth_yoy_pct": 40.0,
    "traffic_growth_yoy_pct": 25.0,
    "headcount": 80,
    "headcount_growth_6m_pct": 15.0,
    "founder_track_record": 1,
    "tam_eur_bn": 15.0,
    "burn_multiple": 1.8,
    "patents": 1,
    "is_regulated": 0,
    "network_effect": 0,
}

# Which features a diligent person CAN realistically collect for free, as of a
# historical cutoff. The rest are the "data gap" the report highlights.
TYPICALLY_OBSERVABLE = {
    "months_since_last_round", "last_round_eur_m", "founder_track_record",
    "tam_eur_bn", "patents", "is_regulated", "network_effect", "headcount",
}
TYPICALLY_UNOBSERVABLE = {
    "rev_growth_yoy_pct", "traffic_growth_yoy_pct",
    "headcount_growth_6m_pct", "burn_multiple",
}

REQUIRED_META = ["company_id", "name", "vertical", "raised_within_12m"]


def load_real_csv(path: str | Path) -> tuple[pd.DataFrame, dict]:
    """
    Load a hand-collected CSV and return (dataframe_ready_to_score, coverage).

    ``coverage`` maps each feature to the fraction of rows where you actually
    observed it (0.0 = fully imputed). Raises a clear error if the required
    identifier/outcome columns are missing.
    """
    df = pd.read_csv(path)

    missing_meta = [c for c in REQUIRED_META if c not in df.columns]
    if missing_meta:
        raise ValueError(
            f"CSV is missing required columns: {missing_meta}. "
            f"Required: {REQUIRED_META}."
        )

    # Outcome must be 0/1.
    df["raised_within_12m"] = pd.to_numeric(df["raised_within_12m"], errors="coerce")
    if not df["raised_within_12m"].dropna().isin([0, 1]).all():
        raise ValueError("raised_within_12m must contain only 0 or 1.")

    coverage = {}
    for col, default in NEUTRAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
            coverage[col] = 0.0
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
        coverage[col] = float(df[col].notna().mean())
        if df[col].isna().all():
            df[col] = default
        # Partial gaps are median-filled downstream by clean_companies.

    return df, coverage


def observed_pillars_note(coverage: dict) -> str:
    """Human-readable summary of which features drove the ranking."""
    observed = [c for c, v in coverage.items() if v > 0]
    imputed = [c for c, v in coverage.items() if v == 0]
    return (
        f"Observed (drove ranking): {', '.join(sorted(observed)) or 'none'}. "
        f"Fully imputed (no ranking effect): {', '.join(sorted(imputed)) or 'none'}."
    )
