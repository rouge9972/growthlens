"""
growthlens.cleaning.normalize
==============================
Cleaning + feature-normalization layer.

Separation of concerns: ingestion produces *raw* fields in their natural units
(%, EUR millions, counts). The scoring layer needs everything on a common 0..1
scale. This module is the only place that translation happens, so the scoring
code stays pure and readable.

Two normalizers are provided:
    - min_max_scale: linear scaling to [0,1] within the cohort.
    - winsorize: clip extreme outliers before scaling so one rocket-ship doesn't
      flatten everyone else (standard practice in quant ranking).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def winsorize(s: pd.Series, lower: float = 0.05, upper: float = 0.95) -> pd.Series:
    """Clip a series to its [lower, upper] quantiles."""
    lo, hi = s.quantile(lower), s.quantile(upper)
    return s.clip(lo, hi)


def min_max_scale(s: pd.Series) -> pd.Series:
    """Scale a series to [0,1]. Constant series -> 0.5 (neutral)."""
    s = s.astype(float)
    rng = s.max() - s.min()
    if rng == 0 or np.isnan(rng):
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / rng


def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and tidy a raw companies frame.

    - Drops exact duplicate company_ids.
    - Coerces numeric columns, fills the few NaNs with cohort medians.
    - Guarantees the columns the scorer expects all exist.
    """
    df = df.drop_duplicates(subset="company_id").copy()

    numeric_cols = [
        "last_round_eur_m", "months_since_last_round", "rev_growth_yoy_pct",
        "traffic_growth_yoy_pct", "headcount", "headcount_growth_6m_pct",
        "founder_track_record", "tam_eur_bn", "burn_multiple",
        "patents", "is_regulated", "network_effect",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            raise KeyError(f"Required column missing from raw data: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    return df.reset_index(drop=True)
