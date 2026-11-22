# CLAUDE.md — GrowthLens

> This file is automatically read by Claude Code at the start of every session.
> Keep it updated as the project evolves.

---

## Project Overview

- **Name:** GrowthLens
- **Purpose:** European growth-stage private-market intelligence. Ranks startups by readiness to raise a Growth Equity (Series B+) round via a transparent six-pillar "GE Readiness Score", auto-generates IC-style memos, benchmarks against public comps, and produces a weekly Market Pulse digest. Portfolio project at the intersection of finance, data and engineering.
- **Status:** In progress — core pipeline, dashboard, simulated + real-data backtest harnesses done
- **Live demo:** https://growthlens.streamlit.app/ (Streamlit Community Cloud, deploys from `main`)

---

## Tech Stack

- **Language:** Python 3.14 (local venv at `growthlens/.venv`)
- **Framework:** Streamlit (dashboard)
- **Libraries:** pandas, numpy, plotly, PyYAML, requests, yfinance, pytest
- **Database:** none — CSV in/out (`data/`)
- **Other tools:** free public APIs (UK Companies House, ECB, Eurostat, Yahoo Finance)

---

## Project Structure

```
Growthlens/                         (outer folder: original zips + .claude/launch.json)
└── growthlens/                     (the git repo)
    ├── config/scoring_weights.yaml — every weight/threshold (the "config decides")
    ├── src/growthlens/
    │   ├── config.py               — paths + typed config loader
    │   ├── ingestion/              — synthetic universe + real free connectors
    │   ├── cleaning/normalize.py   — winsorize + min-max scaling
    │   ├── scoring/ge_readiness.py — six-pillar model (core)
    │   ├── memos/generate.py       — one-page memos
    │   ├── pulse/digest.py         — weekly digest
    │   ├── backtest/               — precision@K / lift / AUC; simulated + real
    │   └── pipeline.py             — end-to-end orchestration
    ├── assets/                     — logo SVGs (dark/light/icon/badge), favicon PNG/ICO
    ├── .streamlit/config.toml      — brand theme (navy #0B1220, emerald #34D399)
    ├── app/dashboard.py            — Streamlit dashboard (Universe/Company/Sectors/Macro tabs)
    ├── scripts/                    — run_pipeline, run_backtest, run_real_backtest, make_sample_data
    ├── docs/                       — methodology whitepaper, setup, presentation, real validation protocol
    ├── data/sample/                — committed 50-company sample; data/raw & data/processed are gitignored
    └── tests/                      — 12 tests (scoring, backtest, real backtest)
```

---

## Architecture & Key Decisions

- Pipeline: ingest (synthetic by default) → clean → score → memos → digest. Dashboard reads/re-runs the same modules.
- Score = weighted sum of six cohort-relative pillars (growth 0.28, market 0.20, timing 0.18, team 0.16, capital efficiency 0.10, moat 0.08). Per-pillar attribution sums back to the total — chosen over black-box ML for auditability.
- All weights in YAML, not code, so rankings are reproducible.
- Synthetic data by default because private funding data is paywalled; no scraping of Crunchbase/PitchBook/LinkedIn. Designed to accept a licensed feed without changing scoring code.
- Real backtest neutrally imputes unobservable features (they contribute nothing to ranking) and reports observability coverage.

---

## Current State

Pipeline, memos, digest, dashboard, simulated backtest (AUC 0.72, 2.16× top-10 lift on synthetic) and real-data backtest harness all work. 12/12 tests pass. Dashboard live on Streamlit Cloud. Run locally: `.venv\Scripts\python.exe -m streamlit run app/dashboard.py`.

---

## Known Issues & Limitations

- Real backtest report (12 companies, AUC 0.71) appears to be run on the template's example rows — not statistically meaningful; `data/real/companies_real.csv` not yet collected.
- Growth pillar (heaviest, 0.28) is 0% observable from free data in the real backtest.
- `sector_momentum` values in the YAML are hand-set priors — need sourcing or clear labelling.
- If the project folder moves, the venv's editable install breaks → rerun `pip install -e ".[dev]"`.

---

## Next Steps

- [x] Logo / branding (done 2026-11-22)
- [ ] Check why Seed-stage companies can rank #1 in a growth-stage screen
- [ ] Hand-collect 30–50 real companies per `docs/real_validation_protocol.md` and rerun the real backtest
- [ ] Source or label the sector momentum priors

---

## Git

- **Local repo:** Initialized ✅
- **Remote:** https://github.com/rouge9972/growthlens
- **Main branch:** main

---

## Session Log

### 2026-11-22 — Session 1
Reviewed project. Fixed venv editable install (pointed at pre-move path), tests 12/12. Re-ran pipeline, launched dashboard locally. Added live demo link + corrected test count in README, gitignored `ruvector.db`, created this file. Logo designed and shipped: lens + breakout trend line (merge of concepts A + C), lowercase two-tone wordmark "growth" white + "lens" emerald. Files in assets/; wired into dashboard via st.logo + page_icon, brand theme in .streamlit/config.toml, README header uses <picture> for light/dark.
