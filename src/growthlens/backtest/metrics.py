"""
growthlens.backtest.metrics
============================
The metrics that turn a ranking + outcomes into an evidence table.

All functions take a frame already SORTED best-to-worst by the model score,
with a binary outcome column. None of them peek at the future — point-in-time
discipline is enforced upstream (the scorer only sees snapshot features).

Definitions
    base_rate        overall fraction of companies that raised. The "random
                     dartboard" benchmark.
    precision@K      fraction of the top-K ranked companies that raised.
    lift@K           precision@K / base_rate. >1 means the model concentrates
                     winners at the top. This is the headline number.
    rank AUC         probability a random raiser is ranked above a random
                     non-raiser. 0.5 = coin flip, 1.0 = perfect ordering.
    decile lift      lift within each 10% slice of the ranking — shows whether
                     signal is monotonic (strongest at the top) or noisy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def base_rate(outcomes: pd.Series) -> float:
    return float(outcomes.mean())


def precision_at_k(sorted_outcomes: pd.Series, k: int) -> float:
    k = min(k, len(sorted_outcomes))
    if k == 0:
        return float("nan")
    return float(sorted_outcomes.iloc[:k].mean())


def lift_at_k(sorted_outcomes: pd.Series, k: int) -> float:
    br = base_rate(sorted_outcomes)
    if br == 0:
        return float("nan")
    return precision_at_k(sorted_outcomes, k) / br


def precision_curve(sorted_outcomes: pd.Series, ks: list[int]) -> pd.DataFrame:
    rows = [
        {
            "K": k,
            "precision_at_K": round(precision_at_k(sorted_outcomes, k), 3),
            "lift_at_K": round(lift_at_k(sorted_outcomes, k), 2),
        }
        for k in ks
    ]
    return pd.DataFrame(rows)


def rank_auc(scores: pd.Series, outcomes: pd.Series) -> float:
    """
    Mann-Whitney / probabilistic AUC computed from ranks (no sklearn needed).
    Equivalent to the area under the ROC curve.
    """
    order = scores.rank(method="average")
    pos = outcomes == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    sum_ranks_pos = order[pos].sum()
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(auc)


def decile_lift(sorted_outcomes: pd.Series) -> pd.DataFrame:
    """Lift within each 10% slice of the ranking (slice 1 = top)."""
    n = len(sorted_outcomes)
    br = base_rate(sorted_outcomes)
    rows = []
    for d in range(10):
        start, end = int(d * n / 10), int((d + 1) * n / 10)
        slice_outcomes = sorted_outcomes.iloc[start:end]
        prec = float(slice_outcomes.mean()) if len(slice_outcomes) else float("nan")
        rows.append(
            {
                "decile": d + 1,
                "n": len(slice_outcomes),
                "raise_rate": round(prec, 3),
                "lift": round(prec / br, 2) if br else float("nan"),
            }
        )
    return pd.DataFrame(rows)
