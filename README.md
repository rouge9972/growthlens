# GrowthLens 📈

**European growth-stage private-market intelligence.** GrowthLens ranks growth-stage
startups by their readiness to raise a Growth Equity round, auto-generates one-page
investment memos, benchmarks them against public comparables, and tracks weekly
market shifts — all from a modular, tested Python pipeline with a Streamlit dashboard.

> **Data honesty up front:** the universe is **synthetic** by default (labelled as
> such everywhere). Private funding data is paywalled across the industry
> (Crunchbase Pro / PitchBook / Dealroom) and GrowthLens does **not** scrape it or
> LinkedIn. It ships real, free connectors for the sources that *are* open
> (UK Companies House, ECB, Eurostat, public comps via Yahoo) and is designed to
> accept a licensed feed without changing the scoring code. See
> [`docs/methodology_whitepaper.md`](docs/methodology_whitepaper.md).

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                                   # 5 tests, ~1s
python scripts/run_pipeline.py --n 200      # ingest → score → memos → digest
streamlit run app/dashboard.py              # interactive dashboard
```
Full instructions: [`docs/setup_guide.md`](docs/setup_guide.md).

## The GE Readiness Score
A transparent, cohort-relative composite of six weighted pillars. Every weight and
threshold lives in [`config/scoring_weights.yaml`](config/scoring_weights.yaml) — the
code computes, the config decides, so every ranking is auditable and reproducible.

| Pillar | Weight | Captures |
|---|---:|---|
| Growth signal | 0.28 | Revenue + traffic growth |
| Market | 0.20 | TAM + sector momentum |
| Timing | 0.18 | Distance from the typical 14–26m raise window |
| Team | 0.16 | Headcount growth + founder track record |
| Capital efficiency | 0.10 | Burn discipline |
| Moat | 0.08 | IP, regulation, network effects |

Each company's score decomposes into a per-pillar attribution that sums back to the
total — so you can always answer "why is it ranked here?".

## Repository structure
```
growthlens/
├── config/scoring_weights.yaml      # all tunable weights/thresholds (auditable)
├── src/growthlens/
│   ├── config.py                    # paths + typed config loader
│   ├── ingestion/
│   │   ├── synthetic.py             # synthetic universe (runs offline)
│   │   ├── companies_house.py       # real free UK API connector
│   │   ├── macro_ecb.py             # real free ECB connector
│   │   ├── macro_eurostat.py        # real free Eurostat connector
│   │   └── comps_yfinance.py        # public comps via Yahoo
│   ├── cleaning/normalize.py        # winsorize + min-max scaling
│   ├── scoring/ge_readiness.py      # the six-pillar model  ← core
│   ├── memos/generate.py            # automated IC-style memos
│   ├── pulse/digest.py              # weekly Market Pulse digest
│   ├── backtest/                    # precision@K / lift / AUC harness
│   │   ├── simulate.py              # honest simulated outcomes (demo)
│   │   ├── metrics.py               # precision@K, lift, rank AUC, decile lift
│   │   └── run.py                   # backtest orchestration + report
│   └── pipeline.py                  # end-to-end orchestration
├── app/dashboard.py                 # Streamlit dashboard
├── scripts/
│   ├── run_pipeline.py              # CLI entry point
│   ├── run_backtest.py              # simulated backtest CLI
│   └── make_sample_data.py          # writes the 50-company sample
├── docs/
│   ├── methodology_whitepaper.md    # the methodology, argued in full
│   ├── setup_guide.md               # run locally in <30 min
│   └── presentation_guide.md        # essay / interview / CV framing
├── tests/test_scoring.py            # property tests on the model
├── data/sample/companies_sample.csv # committed 50-company sample
├── pyproject.toml · requirements.txt · LICENSE · .gitignore
```

## Validation
A precision-at-K backtest harness ships in `growthlens.backtest`:
```bash
python scripts/run_backtest.py --n 400
```
It scores a point-in-time snapshot, then measures how well the ranking concentrates
eventual raisers at the top — **precision@K**, **lift@K**, **rank AUC**, and
**decile lift**. On the synthetic universe it runs against *simulated* outcomes
(driven partly by signals the model sees, partly by a hidden factor + noise it
does not), so it validates the **harness** and the score's discriminative power —
**not** real-world prediction. Swap the simulator for real outcome labels and the
same metrics become a real validation. See the generated report's "Path to real
validation" section.

## Outputs
- `data/processed/companies_scored.csv` — full ranked universe
- `data/processed/memos/*.md` — top-N investment memos
- `data/processed/digests/pulse_<date>.md` — weekly digest

## License
MIT — see [`LICENSE`](LICENSE).

---
*GrowthLens is a screening aid, not investment advice. Built as a portfolio project
at the intersection of finance, data, and engineering.*
