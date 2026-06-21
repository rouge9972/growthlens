# GrowthLens — Real Validation Protocol

This is the method for turning the backtest *harness* into a *real* test, using
only free public data and a few hours of hand-collection. Follow it in order.
The single most important part is Step 2 (avoiding survivorship bias) — get that
wrong and every number you produce is meaningless.

---

## Step 1 — Fix the cutoff and outcome window

Pick a **historical cutoff date** far enough back that a full 12-month outcome
window has elapsed. As of mid-2026, a clean choice is **~Q4 2024** (e.g.
1 December 2024). Your outcome window is then Dec 2024 → Dec 2025, fully in the
past, so every company's "did they raise?" is already knowable.

Define **"raised"** precisely and apply it consistently. A defensible definition:
*a priced equity round at the next stage or larger, announced within 12 months of
the cutoff.* Decide up front whether bridges, extensions, and debt count — then
treat every company the same way. Write your definition at the top of your sheet.

## Step 2 — Build the sampling frame WITHOUT survivorship bias  ⚠️

This is the part that makes or breaks the exercise.

**Wrong way (guarantees a garbage result):** list companies you've *heard of*.
You only hear about winners, so your sample is pre-selected for success and the
model can't be tested — everyone "raised".

**Right way:** define a frame *as of the cutoff*, then track **every** company in
it forward — winners and losers alike. Concretely:

> Take a complete list of companies that announced a **Seed or Series A** round in
> a specific **window** (e.g. "all European fintech + SaaS Seed/Series A rounds
> announced in October 2024") from a roundup source, and include **all of them**.

You are sampling on the *entry event* (they raised an early round), not on the
*outcome* (whether they later raised again). That's what makes it fair. Aim for
30–50 companies; one or two monthly roundups usually gets you there.

**Free sources for the frame** (funding roundups by month/region):
- EU-Startups funding roundups
- Tech.eu / Sifted free articles
- Crunchbase free search filtered by announce date (you can see *that* a round
  happened and its date, even on the free tier)
- National startup-association and accelerator portfolio pages

## Step 3 — Collect the observable features (as of the cutoff)

For each company, fill the columns in `companies_real_TEMPLATE.csv`. Record values
**as they were at the cutoff**, not today. Leave a cell **blank** if you can't find
it for free — the loader imputes blanks neutrally and they won't bias the ranking.

| Column | How to find it (free) | Notes |
|---|---|---|
| `vertical` | The roundup / company site | Map to one of GrowthLens's verticals |
| `country` | Company site | |
| `last_round_stage` | The funding announcement | Seed / Series A / … |
| `last_round_eur_m` | The announcement | Convert to € millions |
| `months_since_last_round` | Cutoff date − round date | The strongest observable signal |
| `founder_track_record` | Founder bio / news | 0 = first-time, 1 = prior startup, 2 = prior exit |
| `tam_eur_bn` | Market-size reports, the pitch | A rough estimate is fine |
| `patents` | Google Patents / EPO (free) | Count granted/filed; 0 is common |
| `is_regulated` | Derive from vertical | 1 for fintech/healthtech usually |
| `network_effect` | Judgment from the business model | 0/1 |
| `headcount` | Company "About"/jobs page | A rough number is fine |
| `rev_growth_yoy_pct` | **usually blank** | Not public — leave empty |
| `traffic_growth_yoy_pct` | **usually blank** | Optional; SimilarWeb free is rough |
| `headcount_growth_6m_pct` | **usually blank** | Needs two snapshots; leave empty |
| `burn_multiple` | **usually blank** | Not public — leave empty |

> **Do not scrape LinkedIn.** Looking up a public headcount figure by hand is
> fine; running a scraper is against their terms and a credibility risk. If
> headcount isn't easy to find, leave it blank.

## Step 4 — Record the outcome

Set `raised_within_12m` to **1** if the company raised a qualifying round within
your window, else **0**. This is the one field you must get right for every row,
and it's the most publicly findable (announcements, news, Crunchbase free).

## Step 5 — Run it

Save your sheet as `data/real/companies_real.csv` and run:
```bash
python scripts/run_real_backtest.py --csv data/real/companies_real.csv
```
You'll get precision@K, lift, AUC, and an **observability coverage** table, plus a
full report in `data/processed/backtest/`.

## Step 6 — Read it honestly

- With 30–50 companies, the error bars are wide. This is *directional evidence*,
  not proof. Say so.
- The model runs **without its heaviest pillar** (revenue growth). An AUC above
  0.5 on observable features alone is a real but bounded result.
- The headline insight: the gap between this real AUC and the full-feature
  synthetic backtest estimates **what a paid data subscription actually buys**.
  That sentence is the most analyst-grade thing in your whole project.

---

### Why this is worth a weekend
A working model is common. A model you **tested on real outcomes**, while being
precise about the limits of free data, is rare — and it's the difference between
a project that *looks* like analyst work and one that *is* analyst work. It is
also a natural LinkedIn post: "I tested my startup-scoring model on 40 real
European rounds — here's what free data can and can't tell you."
