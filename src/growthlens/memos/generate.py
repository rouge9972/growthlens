"""
growthlens.memos.generate
==========================
Generates one-page, IC-style investment memos for the top-ranked companies.

The memo is deterministic and data-driven — no LLM in the loop — so every claim
traces to a field in the dataset. Structure mirrors a junior GE analyst's
first-screen memo: overview, market, growth signals, score attribution, public
comps benchmark, and a diligence checklist.

Output: Markdown files (portable, render on GitHub) under data/processed/memos/.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from jinja2 import Template

from growthlens.config import ScoringConfig, MEMO_DIR
from growthlens.scoring.ge_readiness import explain_score
from growthlens.ingestion.comps_yfinance import median_ev_revenue

_MEMO_TEMPLATE = Template(
    """# Investment Screen — {{ r['name'] }}

*GrowthLens automated first-screen memo · generated {{ today }} · **data: {{ r.data_provenance }}***

| | |
|---|---|
| **GE Readiness Score** | **{{ "%.1f"|format(r.ge_readiness_score) }} / 100** ({{ r.tier }}) |
| **Rank in universe** | #{{ r["rank"] }} of {{ universe_n }} |
| **Vertical** | {{ r.vertical }} |
| **HQ** | {{ r.city }}, {{ r.country }} |
| **Founded** | {{ r.founded_year }} |
| **Last round** | {{ r.last_round_stage }} · €{{ "%.1f"|format(r.last_round_eur_m) }}m · {{ r.months_since_last_round }} months ago |

## 1. Company overview
{{ r['name'] }} is a {{ r.vertical }} company headquartered in {{ r.city }}, {{ r.country }},
founded in {{ r.founded_year }}. It last raised a {{ r.last_round_stage }} round of
€{{ "%.1f"|format(r.last_round_eur_m) }}m, {{ r.months_since_last_round }} months ago, and
currently employs ~{{ r.headcount }} people.

## 2. Market opportunity
Estimated addressable market of **€{{ "%.1f"|format(r.tam_eur_bn) }}bn**. The {{ r.vertical }}
vertical carries a sector-momentum prior of **{{ "%.2f"|format(sector_momentum) }}** (0–1),
reflecting recent VC deployment trend. {{ moat_line }}

## 3. Growth signals
- Revenue growth (YoY): **{{ "%.0f"|format(r.rev_growth_yoy_pct) }}%**
- Web-traffic growth (YoY): **{{ "%.0f"|format(r.traffic_growth_yoy_pct) }}%**
- Headcount growth (6m): **{{ "%.0f"|format(r.headcount_growth_6m_pct) }}%**
- Burn multiple (net burn / net new ARR): **{{ "%.2f"|format(r.burn_multiple) }}** {{ burn_flag }}
- Founder track record: **{{ founder_label }}**

## 4. Score attribution
How the {{ "%.1f"|format(r.ge_readiness_score) }} points break down by pillar:

| Pillar | Sub-score (0–1) | Weight | Points |
|---|---:|---:|---:|
{% for _, p in attribution.iterrows() -%}
| {{ p.pillar }} | {{ "%.3f"|format(p.sub_score_0_1) }} | {{ "%.2f"|format(p.weight) }} | {{ "%.1f"|format(p.points) }} |
{% endfor %}

## 5. Public-market benchmark
{{ comps_line }}

## 6. Recommended diligence checklist
- [ ] Confirm revenue figures and growth durability (cohort retention, NRR)
- [ ] Validate the €{{ "%.1f"|format(r.last_round_eur_m) }}m round terms and cap table
- [ ] Pressure-test the €{{ "%.1f"|format(r.tam_eur_bn) }}bn TAM bottom-up
- [ ] Reference founder track record and key-person risk
- [ ] Unit economics: gross margin, CAC payback, burn multiple trajectory
{% if r.is_regulated == 1 %}- [ ] Regulatory exposure review ({{ r.vertical }} is a regulated vertical)
{% endif %}- [ ] Competitive map and defensibility of the moat thesis

---
*Methodology: docs/methodology_whitepaper.md. This is an automated first screen,
not an investment recommendation. Synthetic-data rows are labelled as such.*
"""
)

_FOUNDER_LABELS = {0: "First-time founder", 1: "Prior startup experience", 2: "Prior exit"}


def _moat_line(r: pd.Series) -> str:
    bits = []
    if r["patents"] > 0:
        bits.append(f"{int(r['patents'])} patent(s) on file")
    if r["is_regulated"] == 1:
        bits.append("operates behind a regulatory barrier")
    if r["network_effect"] == 1:
        bits.append("exhibits network-effect dynamics")
    return ("Moat signals: " + "; ".join(bits) + ".") if bits else "Limited explicit moat signals identified."


def _burn_flag(bm: float) -> str:
    if bm <= 1.0:
        return "✅ efficient"
    if bm >= 3.0:
        return "🔴 capital-intensive"
    return "🟡 moderate"


def build_memo(
    row: pd.Series,
    cfg: ScoringConfig,
    universe_n: int,
    fetch_comps: bool = False,
) -> str:
    """Render a single memo to a Markdown string."""
    attribution = explain_score(row, cfg)

    comps_line = (
        "Public comparables benchmark skipped (offline mode). "
        "Run with --comps to pull live EV/Revenue medians from public peers."
    )
    if fetch_comps:
        tickers = cfg.public_comps.get(row["vertical"], [])
        med = median_ev_revenue(tickers) if tickers else None
        if med is not None:
            comps_line = (
                f"Public peers in {row['vertical']} "
                f"({', '.join(tickers)}) trade at a median **EV/Revenue of "
                f"{med:.1f}x**. Use this as the anchor for an implied private "
                f"valuation, applying an illiquidity/scale discount."
            )

    return _MEMO_TEMPLATE.render(
        r=row,
        today=date.today().isoformat(),
        universe_n=universe_n,
        attribution=attribution,
        sector_momentum=cfg.sector_momentum.get(row["vertical"], 0.5),
        moat_line=_moat_line(row),
        burn_flag=_burn_flag(row["burn_multiple"]),
        founder_label=_FOUNDER_LABELS.get(int(row["founder_track_record"]), "n/a"),
        comps_line=comps_line,
    )


def generate_memos(
    scored: pd.DataFrame,
    cfg: ScoringConfig,
    top_n: int = 20,
    fetch_comps: bool = False,
    out_dir: Path = MEMO_DIR,
) -> list[Path]:
    """Generate memos for the top ``top_n`` companies; return file paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    universe_n = len(scored)
    paths = []
    for _, row in scored.head(top_n).iterrows():
        md = build_memo(row, cfg, universe_n, fetch_comps=fetch_comps)
        path = out_dir / f"{row['rank']:02d}_{row['company_id']}_{_slug(row['name'])}.md"
        path.write_text(md, encoding="utf-8")
        paths.append(path)
    return paths


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name).strip("-").lower()
