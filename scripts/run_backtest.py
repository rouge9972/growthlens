"""
scripts/run_backtest.py
=======================
Run a simulated backtest of the GE Readiness Score.

    python scripts/run_backtest.py
    python scripts/run_backtest.py --n 600 --base-rate 0.15 --signal 1.2

Remember: outcomes are SIMULATED on synthetic data. This exercises the harness
and shows discriminative power against a known target — it is not real-world
validation. See the printed report's "Path to real validation" section.
"""
from __future__ import annotations

import argparse

from growthlens.backtest.run import run_backtest


def main() -> None:
    p = argparse.ArgumentParser(description="Run a simulated GE Readiness backtest.")
    p.add_argument("--n", type=int, default=400, help="universe size")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--base-rate", type=float, default=0.18, help="target raise rate")
    p.add_argument("--signal", type=float, default=1.0, help="observable signal strength")
    args = p.parse_args()

    res = run_backtest(
        n_companies=args.n, seed=args.seed,
        base_rate_target=args.base_rate, signal_strength=args.signal,
    )

    print("\n=== Backtest (SIMULATED outcomes on synthetic data) ===")
    print(f"Universe: {res['n']}  |  base rate: {res['base_rate']:.1%}  |  AUC: {res['auc']:.3f}")
    print("\nPrecision@K:")
    print(res["curve"].to_string(index=False))
    print("\nDecile lift:")
    print(res["deciles"].to_string(index=False))
    print(f"\nReport: {res['report_path']}")


if __name__ == "__main__":
    main()
