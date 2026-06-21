"""
Tests for the backtest harness.

These assert the *machinery* is correct and that, on a simulation with real
signal, the model beats random. They use a fixed seed to stay deterministic.

Run: pytest -q tests/test_backtest.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from growthlens.ingestion.synthetic import generate_companies
from growthlens.cleaning.normalize import clean_companies
from growthlens.backtest.simulate import simulate_outcomes
from growthlens.backtest.metrics import (
    base_rate, precision_at_k, lift_at_k, rank_auc,
)
from growthlens.backtest.run import run_backtest


@pytest.fixture(scope="module")
def snap():
    return clean_companies(generate_companies(n=400, seed=42))


def test_simulated_base_rate_near_target(snap):
    out = simulate_outcomes(snap, seed=43, base_rate=0.18)
    assert 0.12 < base_rate(out) < 0.24  # bisection should land near 0.18


def test_metrics_edge_cases():
    # A perfectly ordered outcome: all raisers ranked first.
    sorted_out = pd.Series([1] * 20 + [0] * 80)
    assert precision_at_k(sorted_out, 10) == 1.0
    assert lift_at_k(sorted_out, 10) > 1.0
    # Perfect ordering -> AUC = 1.0
    scores = pd.Series(np.arange(100)[::-1])  # highest score first
    assert rank_auc(scores, sorted_out) == 1.0


def test_random_ranking_has_auc_near_half():
    rng = np.random.default_rng(0)
    outcomes = pd.Series(rng.binomial(1, 0.2, size=2000))
    scores = pd.Series(rng.normal(size=2000))  # unrelated to outcomes
    assert 0.42 < rank_auc(scores, outcomes) < 0.58


def test_model_beats_random_on_signal():
    # End-to-end: with real signal present, the score must beat random.
    res = run_backtest(n_companies=400, seed=42, base_rate_target=0.18, signal_strength=1.0)
    assert res["auc"] > 0.6                       # clearly better than 0.5
    assert res["curve"].iloc[0]["lift_at_K"] > 1.3  # top-K concentrates raisers
