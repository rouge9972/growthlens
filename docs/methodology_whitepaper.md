# GrowthLens — Methodology White Paper
### The GE Readiness Score: a transparent framework for screening European growth-stage companies

**Author:** Alessandro · **Version:** 0.1 · **Status:** Internal methodology note

---

## 1. Purpose and scope

GrowthLens is a private-market intelligence tool that screens European growth-stage
companies for their readiness to raise a Growth Equity (GE) round, and benchmarks
them against public growth-equity comparables. It is built to mirror the *first
screen* a junior GE analyst performs before a partner commits diligence hours:
a structured, repeatable filter that turns a noisy universe into a ranked shortlist
with an auditable rationale.

This note documents the **GE Readiness Score (GRS)** — its construction, inputs,
assumptions, and limitations — to the standard expected of an internal investment
process. The central claim is not that the GRS predicts returns. It is that the GRS
makes a screening judgement **explicit, consistent, and contestable**, which is
precisely what a qualitative-only process fails to do at scale.

## 2. Why a transparent composite, not a machine-learning model

A supervised model trained to predict "raises next round" would be the obvious
quant instinct. We deliberately reject it at this stage, for three reasons.

1. **Label scarcity and survivorship bias.** Reliable outcome labels (who raised,
   at what valuation, who quietly died) are exactly the data that is paywalled and
   incomplete. A model trained on the visible survivors would encode survivorship
   bias and present it with false confidence.
2. **Interrogability.** An investment committee must be able to ask "why is this
   company ranked third?" and receive a decomposable answer. A gradient-boosted
   model answers with feature importances; a weighted composite answers with a
   line-item attribution that sums to the score. The latter is defensible in a
   memo; the former is not.
3. **Honest calibration.** With a small, partially synthetic universe, a
   transparent rules-based composite states its assumptions openly rather than
   laundering them through opaque fitted weights.

The GRS is therefore a **weighted, cohort-relative composite of six pillars**, with
every weight and threshold stored in configuration (`config/scoring_weights.yaml`),
not code. The code computes; the configuration decides. Re-running with a changed
weight produces a fully traceable change in the ranking.

## 3. The six pillars

Each pillar is normalised to `[0, 1]` **within the analysed cohort** — the GRS
answers "most ready relative to the peers we can observe", not a false absolute.
Continuous inputs are winsorised at the 5th/95th percentiles before scaling so a
single outlier cannot compress the rest of the distribution.

| Pillar | Weight | Inputs | Rationale |
|---|---:|---|---|
| **Growth signal** | 0.28 | Revenue YoY (70%), web-traffic YoY (30%) | Growth is the single most predictive screen for GE readiness; it carries the heaviest weight. |
| **Timing** | 0.18 | Months since last round | GE rounds (Series B+) typically arrive 14–26 months after the prior round; readiness peaks inside that window and decays on either side. |
| **Team** | 0.16 | Headcount growth 6m (65%), founder track record (35%) | Sustained hiring is a leading indicator of commercial traction; founder pedigree de-risks execution. |
| **Market** | 0.20 | TAM (55%), sector momentum prior (45%) | GE underwrites durable category growth; a large TAM in a tailwind sector expands the outcome space. |
| **Capital efficiency** | 0.10 | Burn multiple (net burn / net new ARR) | Distinguishes growth that compounds from growth that is purchased; rewards discipline. |
| **Moat** | 0.08 | Patents, regulatory barrier, network effects | Proxies for defensibility, weighted lowest because the proxies are the noisiest. |

**Timing curve.** Rather than a linear "newer is better", the timing pillar uses a
triangular readiness curve: score `= 0` below a 4-month floor (too soon to raise)
and above a 48-month ceiling (likely flat/down or distressed), `= 1.0` inside the
14–26 month ideal window, and linearly ramped between. This encodes the actual
cadence of growth rounds rather than a naive recency bias.

**Score and bands.** The headline GRS is the weighted sum scaled to 0–100.
Companies are banded into Tier 1 (≥80, priority diligence), Tier 2 (≥65, active
watch), Tier 3 (≥50, monitor), and Tier 4 (pass for now). Tier 1 is intentionally
demanding: clearing 80 requires near-simultaneous strength across most pillars, so
an empty Tier 1 on a given run is a feature, not a defect — it reflects that
genuinely round-ready outliers are rare.

## 4. Data sources and provenance

GrowthLens separates *methodology* from *data feed*. The methodology is
data-source-agnostic; the quality of the output scales with the quality of the
feed plugged into the ingestion layer.

| Source | Status | What it provides | Honest limitation |
|---|---|---|---|
| **Synthetic generator** | Built-in, runs offline | Full universe with all scored fields | Invented (but plausible) data; labelled `data_provenance = synthetic` throughout. |
| **UK Companies House API** | Real, free, official | Incorporation date, status, SIC codes for UK companies | UK-only; **no** funding, revenue, or headcount. |
| **ECB Data Portal** | Real, free, no key | Policy-rate macro overlay | Macro context only. |
| **Eurostat** | Real, free, no key | Country GDP growth | Macro context only. |
| **Yahoo Finance (yfinance)** | Real, free, unofficial | Public-comps EV/Revenue, growth, margins | Unofficial wrapper; can break on Yahoo changes. |

**The deliberate omission.** GrowthLens does **not** scrape Crunchbase or LinkedIn.
Crunchbase's free tier does not expose structured funding-round data — that data is
its paid product, alongside PitchBook and Dealroom. LinkedIn scraping violates its
terms of service, sits in contested legal territory, and is technically fragile.
Building growth signals on either would be both unreliable and a credibility risk.
The honest design is to treat real private-market funding and people data as a
**premium feed to be slotted in later** (via a licensed API), while the synthetic
generator supplies those same fields today so the pipeline is complete and runnable.
The headcount-growth field is the clearest example: it is a first-class model input,
populated synthetically now and intended to be sourced from a licensed people-data
API in production — never from scraping.

## 5. Comparison to qualitative diligence

A traditional first screen is a partner's pattern recognition: fast, high-variance,
and unauditable. The GRS does not replace that judgement; it **structures the funnel
before it**. Its advantages are consistency (the same inputs always produce the same
rank), coverage (it ranks 200–500 companies in seconds), and attribution (every
score decomposes into named drivers). Its disadvantages are equally explicit: it
sees only quantifiable proxies, it is blind to the qualitative signals a partner
would catch in a single founder call, and it inherits any bias in its inputs. The
correct framing is **augmentation**: the GRS decides where the analyst spends the
next hour, not where the fund deploys capital.

## 6. Limitations and roadmap

- **Cohort-relative scores are not comparable across runs** unless the universe is
  held fixed; week-over-week deltas (Market Pulse) are computed on a stable ID join.
- **Sector-momentum priors are currently hand-set**; the roadmap computes them from
  rolling VC-deployment data in the ingestion layer.
- **Backtest harness built; real validation pending labels.** A precision-at-K
  backtest harness now ships with the project (`growthlens.backtest`). On the
  synthetic universe it runs against *simulated* outcomes — outcomes deliberately
  driven partly by signals the model sees and partly by a hidden factor and noise
  it does not. This validates the harness and demonstrates discriminative power
  against a known target (rank AUC well above 0.5, top-K lift above 1), but it is
  **not** evidence the model predicts real fundraising. Real validation requires
  real labels: of the top-20 companies at time *t*, how many raised a qualifying
  round by *t + 12 months*? The harness accepts a real-labels join without any
  change to the metrics code — only the data source changes.
- **Weights are priors, not fitted.** They encode a defensible thesis and are meant
  to be challenged in review — which is the entire point of keeping them in a
  visible config file.

---

*This document accompanies the GrowthLens codebase. The GRS is a screening aid, not
an investment recommendation. All synthetic data is labelled as such end-to-end.*
