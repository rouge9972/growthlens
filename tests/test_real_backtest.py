"""
Tests for the real-data backtest path (loader + runner).

Run: pytest -q tests/test_real_backtest.py
"""
from __future__ import annotations

import pandas as pd
import pytest

from growthlens.config import SAMPLE_DIR  # noqa: F401 (kept for path conventions)
from growthlens.backtest.real import load_real_csv, NEUTRAL_DEFAULTS
from growthlens.backtest.real_run import run_real_backtest

TEMPLATE = "data/real/companies_real_TEMPLATE.csv"


def test_loader_imputes_unobservable_and_reports_coverage():
    df, coverage = load_real_csv(TEMPLATE)
    # The four typically-unobservable features are blank in the template -> 0% coverage
    for col in ["rev_growth_yoy_pct", "traffic_growth_yoy_pct",
                "headcount_growth_6m_pct", "burn_multiple"]:
        assert coverage[col] == 0.0
        assert df[col].notna().all()  # filled with neutral default
    # Observable ones are present
    assert coverage["months_since_last_round"] > 0.9


def test_loader_rejects_missing_outcome(tmp_path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"company_id": ["A"], "name": ["x"], "vertical": ["saas"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError):
        load_real_csv(bad)


def test_real_runner_end_to_end():
    res = run_real_backtest(TEMPLATE)
    assert res["n"] == 12
    assert 0.0 <= res["auc"] <= 1.0
    assert 0.0 < res["base_rate"] < 1.0
    assert "report_path" in res
