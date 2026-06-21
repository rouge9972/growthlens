"""
growthlens.pipeline
====================
End-to-end orchestration: ingest -> clean -> score -> memos -> digest.

This is the single function the CLI and the dashboard both call, so there is
exactly one definition of "run GrowthLens". Each stage is logged so the run is
legible when you demo it live.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from growthlens import config as C
from growthlens.ingestion.synthetic import generate_companies
from growthlens.cleaning.normalize import clean_companies
from growthlens.scoring.ge_readiness import score_companies
from growthlens.memos.generate import generate_memos
from growthlens.pulse.digest import build_digest, write_digest

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("growthlens")


@dataclass
class PipelineResult:
    scored: pd.DataFrame
    memo_paths: list[Path]
    digest_path: Path
    scored_csv: Path


def run_pipeline(
    n_companies: int = 200,
    seed: int = 42,
    top_n_memos: int = 20,
    fetch_comps: bool = False,
    include_macro: bool = False,
) -> PipelineResult:
    """Run the full GrowthLens pipeline on synthetic data and persist outputs."""
    C.ensure_dirs()
    cfg = C.load_scoring_config()

    log.info("Stage 1/5 — ingest: generating %d synthetic companies", n_companies)
    raw = generate_companies(n=n_companies, seed=seed)
    raw.to_csv(C.COMPANIES_RAW, index=False)

    log.info("Stage 2/5 — clean: normalizing and validating")
    clean = clean_companies(raw)

    log.info("Stage 3/5 — score: computing GE Readiness Score")
    scored = score_companies(clean, cfg)
    scored.to_csv(C.COMPANIES_SCORED, index=False)
    log.info("   top company: %s (%.1f)", scored.iloc[0]["name"], scored.iloc[0]["ge_readiness_score"])

    log.info("Stage 4/5 — memos: generating top-%d investment memos", top_n_memos)
    memo_paths = generate_memos(scored, cfg, top_n=top_n_memos, fetch_comps=fetch_comps)

    log.info("Stage 5/5 — pulse: building Market Pulse digest")
    digest_md = build_digest(scored, previous=None, include_macro=include_macro)
    digest_path = write_digest(digest_md)

    log.info("Done. Scored %d companies, wrote %d memos.", len(scored), len(memo_paths))
    return PipelineResult(
        scored=scored,
        memo_paths=memo_paths,
        digest_path=digest_path,
        scored_csv=C.COMPANIES_SCORED,
    )
