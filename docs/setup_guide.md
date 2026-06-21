# GrowthLens — Setup Guide

Goal: clone, install, and run the full pipeline + dashboard in **under 30 minutes**,
with **zero paid services**. Everything below works offline on synthetic data;
network only matters if you opt into live comps/macro.

## 0. Prerequisites
- Python **3.10+** (`python --version`)
- `git`
- ~5 minutes for the dependency install

## 1. Clone and create a virtual environment
```bash
git clone https://github.com/<your-username>/growthlens.git
cd growthlens

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

## 2. Install (editable, with dev tools)
```bash
pip install -e ".[dev]"
```
This installs GrowthLens and its dependencies and registers the `growthlens`
package so imports like `from growthlens.scoring...` resolve.

## 3. Run the test suite (≈1 second)
```bash
pytest -q
```
Five tests confirm the weights are well-formed, scores stay in `[0,100]`, ranks are
complete, the timing pillar behaves, and score attribution reconciles to the total.

## 4. Run the pipeline (offline, synthetic)
```bash
python scripts/run_pipeline.py --n 200
```
Produces:
- `data/processed/companies_scored.csv` — full ranked universe
- `data/processed/memos/*.md` — top-20 investment memos
- `data/processed/digests/pulse_<date>.md` — Market Pulse digest

Useful flags:
```bash
python scripts/run_pipeline.py --n 350 --memos 30   # bigger universe, more memos
python scripts/run_pipeline.py --comps              # live public comps (needs network)
python scripts/run_pipeline.py --macro              # ECB macro overlay (needs network)
```

## 5. Launch the dashboard
```bash
streamlit run app/dashboard.py
```
Opens at `http://localhost:8501` with four tabs: Universe, Company, Sectors, Macro.

## 6. (Optional) Enable live data sources — all free
| Source | How to enable |
|---|---|
| ECB policy rate / Eurostat GDP | Nothing to do — no key required (needs internet). |
| Public comps (Yahoo) | Nothing to do — `yfinance` needs internet only. |
| UK Companies House | Free key at <https://developer.company-information.service.gov.uk/>, then `export COMPANIES_HOUSE_API_KEY="yourkey"`. |

If any live source is unreachable, the pipeline logs a graceful fallback and keeps
running on synthetic data — it never hard-fails.

## 7. Deploy free on Streamlit Community Cloud
1. Push the repo to GitHub.
2. Go to <https://share.streamlit.io>, connect the repo.
3. Set the entry point to `app/dashboard.py`.
4. Deploy. (Add `COMPANIES_HOUSE_API_KEY` under *Secrets* if you want live UK data.)

## Troubleshooting
- **`ModuleNotFoundError: growthlens`** → you skipped `pip install -e .`, or the
  venv isn't activated.
- **`pillar_weights must sum to 1.0`** → you edited `config/scoring_weights.yaml`;
  make the six weights sum to exactly 1.0.
- **Dashboard macro tab empty** → you're offline; expected, everything else works.
