"""
scripts/run_pipeline.py
=======================
Command-line entry point. Examples:

    python scripts/run_pipeline.py                 # 200 cos, offline, 20 memos
    python scripts/run_pipeline.py --n 350 --comps # bigger universe + live comps
    python scripts/run_pipeline.py --macro         # include ECB macro overlay

Run from the repo root after `pip install -e .` (see docs/setup_guide.md).
"""
from __future__ import annotations

import argparse

from growthlens.pipeline import run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="Run the GrowthLens pipeline.")
    p.add_argument("--n", type=int, default=200, help="number of companies")
    p.add_argument("--seed", type=int, default=42, help="reproducibility seed")
    p.add_argument("--memos", type=int, default=20, help="number of top memos")
    p.add_argument("--comps", action="store_true", help="fetch live public comps (needs network)")
    p.add_argument("--macro", action="store_true", help="include ECB macro overlay (needs network)")
    args = p.parse_args()

    result = run_pipeline(
        n_companies=args.n,
        seed=args.seed,
        top_n_memos=args.memos,
        fetch_comps=args.comps,
        include_macro=args.macro,
    )

    print("\n=== Top 10 by GE Readiness Score ===")
    cols = ["rank", "name", "vertical", "country", "ge_readiness_score", "tier"]
    print(result.scored[cols].head(10).to_string(index=False))
    print(f"\nMemos:  {result.memo_paths[0].parent}")
    print(f"Digest: {result.digest_path}")
    print(f"Scored: {result.scored_csv}")


if __name__ == "__main__":
    main()
