"""
scripts/run_real_backtest.py
============================
Run the backtest against a hand-collected CSV of REAL companies + outcomes.

    python scripts/run_real_backtest.py --csv data/real/companies_real.csv

Start from the template at data/real/companies_real_TEMPLATE.csv. The collection
method (and how to avoid survivorship bias) is in docs/real_validation_protocol.md.
"""
from __future__ import annotations

import argparse

from growthlens.backtest.real_run import run_real_backtest


def main() -> None:
    p = argparse.ArgumentParser(description="Real-data GE Readiness backtest.")
    p.add_argument("--csv", required=True, help="path to your hand-collected CSV")
    args = p.parse_args()

    res = run_real_backtest(args.csv)

    print("\n=== REAL-DATA backtest ===")
    print(f"N: {res['n']}  |  base rate: {res['base_rate']:.1%}  |  AUC: {res['auc']:.3f}")
    print(f"\n{res['coverage_note']}")
    print("\nPrecision@K:")
    print(res["curve"].to_string(index=False))
    print(f"\nReport: {res['report_path']}")


if __name__ == "__main__":
    main()
