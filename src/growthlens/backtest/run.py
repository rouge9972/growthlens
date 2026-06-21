"""
growthlens.backtest.run
=======================
Orchestrates one backtest: build a point-in-time snapshot, simulate outcomes,
score with the live model, and emit an evidence report.

Point-in-time discipline (the part that matters for credibility):
    - The snapshot represents the universe AS OF time t.
    - Outcomes are realised over (t, t + 12 months].
    - The scorer sees ONLY snapshot features — never the outcome. So there is no
      look-ahead leakage: the ranking is formed before any outcome is known.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from growthlens import config as C
from growthlens.ingestion.synthetic import generate_companies
from growthlens.cleaning.normalize import clean_companies
from growthlens.scoring.ge_readiness import score_companies
from growthlens.backtest.simulate import simulate_outcomes
from growthlens.backtest.metrics import (
    base_rate, precision_curve, rank_auc, decile_lift,
)

BACKTEST_DIR = C.PROCESSED_DIR / "backtest"


def run_backtest(
    n_companies: int = 400,
    seed: int = 42,
    base_rate_target: float = 0.18,
    signal_strength: float = 1.0,
    ks: list[int] | None = None,
) -> dict:
    """Run one simulated backtest; return a results dict and write a report."""
    ks = ks or [10, 20, 50, 100]
    cfg = C.load_scoring_config()

    # 1. Snapshot as of t (features only)
    snapshot = clean_companies(generate_companies(n=n_companies, seed=seed))

    # 2. Outcomes over (t, t+12m] — simulated, NEVER shown to the scorer
    outcomes = simulate_outcomes(
        snapshot, seed=seed + 1,
        base_rate=base_rate_target, signal_strength=signal_strength,
    )

    # 3. Score using snapshot features only, then attach outcomes and sort.
    #    The scorer never sees the outcome — ranking is formed first.
    scored = score_companies(snapshot, cfg)
    outcome_by_id = dict(zip(snapshot["company_id"], outcomes.values))
    scored = scored.assign(
        raised_within_12m=scored["company_id"].map(outcome_by_id)
    ).sort_values("ge_readiness_score", ascending=False).reset_index(drop=True)

    sorted_outcomes = scored["raised_within_12m"].astype(int)

    # 4. Metrics
    results = {
        "n": n_companies,
        "base_rate": round(base_rate(sorted_outcomes), 3),
        "auc": round(rank_auc(scored["ge_readiness_score"], sorted_outcomes), 3),
        "curve": precision_curve(sorted_outcomes, ks),
        "deciles": decile_lift(sorted_outcomes),
    }

    report_path = _write_report(results)
    results["report_path"] = report_path
    return results


def _write_report(results: dict, out_dir: Path = BACKTEST_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    br = results["base_rate"]
    auc = results["auc"]
    top = results["curve"].iloc[0]

    lines = [
        f"# GrowthLens — Backtest report · {date.today().isoformat()}",
        "",
        "> **Simulated outcomes on synthetic data.** This validates the backtest "
        "*harness* and the score's discriminative power against a known target. "
        "It is **not** evidence the model predicts real fundraising — that requires "
        "real outcome labels (see 'Path to real validation' below).",
        "",
        "## Headline",
        f"- Universe: **{results['n']}** companies",
        f"- Base rate (random benchmark): **{br:.1%}** raised within 12 months",
        f"- Rank AUC: **{auc:.3f}** (0.5 = random, 1.0 = perfect ordering)",
        f"- Top-{int(top['K'])} precision: **{top['precision_at_K']:.1%}** "
        f"→ **{top['lift_at_K']:.2f}× lift** over the base rate",
        "",
        "## Precision@K",
        "",
        "| K | precision@K | lift@K |",
        "|---:|---:|---:|",
    ]
    for _, r in results["curve"].iterrows():
        lines.append(f"| {int(r['K'])} | {r['precision_at_K']:.1%} | {r['lift_at_K']:.2f}× |")

    lines += ["", "## Decile lift (slice 1 = top of ranking)", "",
              "| Decile | n | raise rate | lift |", "|---:|---:|---:|---:|"]
    for _, r in results["deciles"].iterrows():
        lines.append(f"| {int(r['decile'])} | {int(r['n'])} | {r['raise_rate']:.1%} | {r['lift']:.2f}× |")

    lines += [
        "",
        "## How to read this",
        "- **Lift@K > 1** means the model concentrates eventual raisers near the "
        "top of the ranking — the whole point of a screening tool.",
        "- **AUC** between 0.5 and 1.0 measures overall ordering quality. It is "
        "capped below 1.0 here on purpose: the simulated outcome includes a hidden "
        "factor and noise the model cannot see, mirroring reality.",
        "- **Decile lift** should fall from decile 1 downward if the signal is "
        "monotonic — strongest at the very top.",
        "",
        "## Path to real validation",
        "1. Pick a historical cutoff (e.g. 18 months ago) and assemble a list of "
        "real companies that were growth-stage *as of then*.",
        "2. Record the one fact you need: did each raise a qualifying round in the "
        "following 12 months? (Hand-collectable from news / press releases for "
        "30-50 companies, or from a licensed feed at scale.)",
        "3. Re-run this exact harness with those real labels in place of the "
        "simulator. The metrics code does not change — only the data source does.",
        "",
        "*Harness is reusable as-is; swap `simulate_outcomes` for a real labels join.*",
    ]
    path = out_dir / f"backtest_{date.today().isoformat()}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
