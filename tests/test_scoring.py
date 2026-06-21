"""
Tests for the GE Readiness scoring model.

These assert the *properties* an investment process must hold:
    - weights are well-formed,
    - scores live in [0,100],
    - the timing pillar peaks inside the ideal window,
    - score attribution sums back to the headline score.

Run: pytest -q
"""
from __future__ import annotations

import pandas as pd
import pytest

from growthlens.config import load_scoring_config
from growthlens.ingestion.synthetic import generate_companies
from growthlens.cleaning.normalize import clean_companies
from growthlens.scoring.ge_readiness import score_companies, explain_score


@pytest.fixture(scope="module")
def cfg():
    return load_scoring_config()


@pytest.fixture(scope="module")
def scored(cfg):
    raw = generate_companies(n=60, seed=1)
    return score_companies(clean_companies(raw), cfg)


def test_weights_sum_to_one(cfg):
    assert round(sum(cfg.pillar_weights.values()), 6) == 1.0


def test_scores_in_range(scored):
    assert scored["ge_readiness_score"].between(0, 100).all()


def test_ranks_are_unique_and_complete(scored):
    assert sorted(scored["rank"].tolist()) == list(range(1, len(scored) + 1))


def test_attribution_reconciles_to_score(scored, cfg):
    row = scored.iloc[0]
    attribution = explain_score(row, cfg)
    assert abs(attribution["points"].sum() - row["ge_readiness_score"]) < 0.2


def test_timing_pillar_peaks_in_window(cfg):
    # Two companies identical except months-since-round: 20 (ideal) vs 50 (stale).
    base = generate_companies(n=2, seed=3)
    base.loc[0, "months_since_last_round"] = 20
    base.loc[1, "months_since_last_round"] = 50
    s = score_companies(clean_companies(base), cfg)
    ideal = s[s["months_since_last_round"] == 20]["pillar_timing"].iloc[0]
    stale = s[s["months_since_last_round"] == 50]["pillar_timing"].iloc[0]
    assert ideal > stale
