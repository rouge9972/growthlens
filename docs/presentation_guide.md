# GrowthLens — How to Present This

The single rule running through this guide: **claim exactly what you built, and
frame it well.** The version of GrowthLens that wins rooms is the one whose author
understands the data landscape — including its paywalls and its legal lines — not
the one who pretends those don't exist. Sophisticated readers (GE associates,
quant-literate adcoms) reward that judgement. Overclaiming ("I pulled live
Crunchbase funding data") is the fastest way to lose credibility with the exact
people you're trying to impress.

What you can truthfully say you built:
- A modular Python pipeline (ingestion → cleaning → scoring → memo/digest generation
  → dashboard) structured as a real open-source repository with tests.
- A transparent, six-pillar **GE Readiness Score** with a documented, config-driven
  methodology and per-company score attribution.
- An automated investment-memo generator and a weekly Market Pulse digest.
- Real, free connectors (Companies House, ECB, Eurostat, public comps) plus a
  synthetic data engine that makes the whole thing reproducible offline.
- A methodology white paper that argues its own design choices and states its limits.

---

## 1. The CV line

> **GrowthLens — Private-market intelligence tool (Python).** Built a modular data
> pipeline and a transparent six-pillar "GE Readiness Score" that ranks 200+
> European growth-stage companies and auto-generates investment memos benchmarked
> against public comparables. Documented the methodology in a white paper;
> deployed an interactive dashboard. [GitHub link]

Keep it to two lines. Lead with the noun ("intelligence tool"), then the
intellectual artefact (the score), then proof of rigour (white paper, deployed).

## 2. The application essay (≈150-word block you can adapt)

> I wanted to understand how growth-equity investors decide where to look before
> they decide where to invest, so I built GrowthLens — a tool that ranks European
> growth-stage startups by their readiness to raise. The interesting problem
> wasn't the code; it was the judgement. Real funding data is paywalled across the
> entire industry, and the obvious shortcuts — scraping LinkedIn, claiming a free
> Crunchbase feed — are both unreliable and a credibility risk. So I designed the
> system to separate methodology from data: a defensible, six-pillar scoring model
> that runs today on a transparent synthetic dataset and slots in a licensed feed
> tomorrow. I wrote the methodology as a white paper that argues its own
> assumptions and states where it would fail. GrowthLens taught me that in finance,
> being explicit about what you don't know is itself a form of rigour.

Why this works for HEC / Bocconi / Oxbridge: it shows initiative, domain awareness,
and — the rarest signal at your stage — intellectual honesty about limits. That
last beat is what separates "ambitious student" from "thinks like an analyst".

## 3. The interview (when they say "walk me through it")

Structure your answer in four beats, ~2 minutes total:

1. **Problem (15s).** "GE investors triage a huge private universe before
   committing diligence. I built a tool to structure that first screen."
2. **What you built (30s).** "A pipeline that ingests company data, scores each
   company on a six-pillar readiness model, and auto-writes a one-page memo with
   public-comp benchmarks."
3. **The hard judgement (45s) — this is the part that scores points.** "The
   honest constraint is data. Funding data is paywalled industry-wide; scraping
   LinkedIn is against ToS and legally contested. So rather than fake it, I made
   the methodology data-source-agnostic and documented the limitation in the white
   paper. The model runs on synthetic data now and takes a licensed feed later
   without changing a line of scoring code."
4. **What you'd do next (30s).** "Backtest precision-at-K once I had outcome
   labels: of my top-20, how many actually raised within twelve months."

**Likely follow-ups — be ready:**
- *"Why a weighted composite, not ML?"* → Label scarcity, survivorship bias, and
  the need for an interrogable score an IC can question. (See white paper §2.)
- *"Why those weights?"* → They're priors encoding a thesis, kept in a visible
  config file precisely so they can be challenged — not fitted on biased data.
- *"How would you make money from it?"* → It's a sourcing tool, not a product; the
  value is analyst hours saved and earlier access to round-ready companies.
- *"What's the weakest part?"* → The synthetic data and hand-set sector priors —
  and you say so before they do.

## 4. Three ways to extend visibility

1. **Open-source it with a strong README and the white paper front-and-centre.**
   A repo that *teaches* its methodology reads as far more senior than one that
   just dumps code. Pin it on your GitHub and link it from your CV and LinkedIn.
2. **Write a 3-part LinkedIn / Substack series.** (a) "Why private-market data is
   so hard to get for free" — the data-landscape piece that demonstrates domain
   fluency; (b) "Designing a defensible scoring model" — the methodology;
   (c) "What the model gets wrong" — the limitations piece that signals maturity.
   The third post will outperform the first two with finance readers.
3. **Pitch it to a student investment club or a UniBo finance society** as a live
   sourcing tool, and run one real session with it. "I built it *and* people used
   it" is a stronger story than "I built it." If you later get trial access to a
   licensed feed (some offer student/academic tiers), swap it in and write the
   before/after.

---

*One closing note: when you eventually plug in a real licensed data feed, update
this guide and the white paper to say so — and keep the synthetic mode as the
reproducible demo. The honesty is the brand.*
