"""
growthlens.backtest.simulate
=============================
Simulates fundraising OUTCOMES for a snapshot of companies, so the backtest
harness has something to score against.

READ THIS — the honesty boundary:
    The companies are synthetic and so are these outcomes. This module exists to
    EXERCISE the harness, not to validate the model against reality. We design
    the outcome on purpose so the test is meaningful but not circular:

      raised ~ Bernoulli( sigmoid( signal_the_model_can_see
                                   + a HIDDEN factor it cannot see
                                   + noise ) )

    Because growth/timing/team genuinely drive the simulated outcome, a good
    scorer SHOULD beat random — that's the harness working. Because a hidden
    factor and noise also drive it, the scorer CANNOT be perfect — that's
    realistic, and it's exactly why real outcome labels are needed for a real
    validation. See docs/methodology_whitepaper.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _z(s: pd.Series) -> pd.Series:
    """Standardize to mean 0 / std 1 (cohort-relative)."""
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _calibrate_intercept(linpred: np.ndarray, target_rate: float) -> float:
    """
    Find an intercept c such that mean(sigmoid(linpred - c)) ~= target_rate.
    Simple bisection — keeps the simulated base rate realistic and controllable.
    """
    lo, hi = -20.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        rate = _sigmoid(linpred - mid).mean()
        if rate > target_rate:
            lo = mid          # need higher threshold -> lower rate
        else:
            hi = mid
    return (lo + hi) / 2


def simulate_outcomes(
    df: pd.DataFrame,
    seed: int = 0,
    base_rate: float = 0.18,
    signal_strength: float = 1.0,
    hidden_strength: float = 0.8,
    noise_strength: float = 0.6,
) -> pd.Series:
    """
    Return a 0/1 Series ``raised_within_12m`` aligned to ``df``.

    Parameters
    ----------
    base_rate : float
        Target fraction of companies that raise within the window (realistic
        growth-stage follow-on rates sit roughly in the 0.10-0.25 range).
    signal_strength : float
        Weight on the model-observable drivers (growth, timing, team).
    hidden_strength : float
        Weight on an UNOBSERVED latent factor — caps achievable performance.
    noise_strength : float
        Pure noise — the irreducible part.
    """
    rng = np.random.default_rng(seed)

    # Observable drivers (these mirror real fundraising logic, so it is fair for
    # the model to capture them).
    growth = _z(df["rev_growth_yoy_pct"])
    timing = _z(-(df["months_since_last_round"] - 20).abs())  # closeness to ~20m
    team = _z(df["headcount_growth_6m_pct"])

    # The HIDDEN factor: e.g. founder network strength the model never observes.
    hidden = pd.Series(rng.normal(size=len(df)), index=df.index)
    noise = pd.Series(rng.normal(size=len(df)), index=df.index)

    linpred = (
        signal_strength * (0.9 * growth + 0.7 * timing + 0.5 * team)
        + hidden_strength * hidden
        + noise_strength * noise
    ).to_numpy()

    c = _calibrate_intercept(linpred, base_rate)
    prob = _sigmoid(linpred - c)
    raised = rng.binomial(1, prob)
    return pd.Series(raised, index=df.index, name="raised_within_12m")
