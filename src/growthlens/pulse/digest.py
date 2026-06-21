"""
growthlens.pulse.digest
========================
The "Market Pulse" module: a weekly digest of what moved in the universe.

In a live deployment this diffs two consecutive scored snapshots and surfaces:
    - companies that newly entered Tier 1/2,
    - the largest week-over-week GRS movers,
    - sector-level momentum shifts,
    - the current macro overlay (ECB policy rate).

With a single snapshot (first run) it emits a "baseline" digest. Output is
Markdown (and optional PDF), written to data/processed/digests/.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from growthlens.config import DIGEST_DIR
from growthlens.ingestion.macro_ecb import latest_policy_rate


def build_digest(
    current: pd.DataFrame,
    previous: Optional[pd.DataFrame] = None,
    include_macro: bool = False,
) -> str:
    """Render the weekly Market Pulse digest as Markdown."""
    today = date.today().isoformat()
    lines = [f"# GrowthLens — Market Pulse · {today}", ""]

    # Macro overlay
    if include_macro:
        rate = latest_policy_rate()
        rate_txt = f"{rate:.2f}%" if rate is not None else "unavailable (offline)"
        lines += [f"**Macro overlay** — ECB main refinancing rate: **{rate_txt}**.", ""]

    # Tier-1 leaders this week (fall back to top-of-universe if none clear 80)
    tier1 = current[current["ge_readiness_score"] >= 80]
    if tier1.empty:
        lines += ["## Top of universe (no Tier 1 ≥ 80 this run)", ""]
        leaders = current.head(10)
    else:
        lines += ["## Tier 1 — Priority diligence", ""]
        leaders = tier1.head(10)
    for _, r in leaders.iterrows():
        lines.append(
            f"- **{r['name']}** ({r['vertical']}, {r['country']}) — "
            f"{r['ge_readiness_score']:.1f}"
        )
    lines.append("")

    # Movers (needs a prior snapshot)
    if previous is not None:
        merged = current.merge(
            previous[["company_id", "ge_readiness_score"]],
            on="company_id",
            suffixes=("", "_prev"),
        )
        merged["delta"] = (merged["ge_readiness_score"] - merged["ge_readiness_score_prev"]).round(1)
        movers = merged.reindex(merged["delta"].abs().sort_values(ascending=False).index)
        lines += ["## Biggest GRS movers (week over week)", ""]
        for _, r in movers.head(8).iterrows():
            arrow = "▲" if r["delta"] >= 0 else "▼"
            lines.append(f"- {arrow} **{r['name']}** {r['delta']:+.1f} → {r['ge_readiness_score']:.1f}")
        lines.append("")
    else:
        lines += ["## Movers", "", "_Baseline snapshot — movers appear from the second run onward._", ""]

    # Sector momentum (mean GRS by vertical)
    sect = (
        current.groupby("vertical")["ge_readiness_score"]
        .mean().round(1).sort_values(ascending=False)
    )
    lines += ["## Sector readiness (mean GRS)", ""]
    for vertical, val in sect.items():
        lines.append(f"- {vertical}: {val}")
    lines.append("")

    lines += ["---", "*Automated digest. Synthetic-data universe unless connectors are configured.*"]
    return "\n".join(lines)


def write_digest(markdown: str, out_dir: Path = DIGEST_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pulse_{date.today().isoformat()}.md"
    path.write_text(markdown, encoding="utf-8")
    return path
