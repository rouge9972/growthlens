"""
growthlens.config
=================
Single source of truth for filesystem paths and tunable parameters.

Why a module just for this?
    A reproducible research pipeline should never hard-code "../data/x.csv"
    in fifteen places. Everything resolves from the repo root, and every
    tunable number is loaded from config/scoring_weights.yaml. Change the YAML,
    re-run, and the result is fully traceable to that input.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml

# Repo root = two levels up from this file (src/growthlens/config.py -> repo/)
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"
DOCS_DIR = ROOT / "docs"
CONFIG_PATH = ROOT / "config" / "scoring_weights.yaml"

# Generated artefacts
COMPANIES_RAW = RAW_DIR / "companies.csv"
COMPANIES_SCORED = PROCESSED_DIR / "companies_scored.csv"
SAMPLE_COMPANIES = SAMPLE_DIR / "companies_sample.csv"
MEMO_DIR = PROCESSED_DIR / "memos"
DIGEST_DIR = PROCESSED_DIR / "digests"

VERTICALS = [
    "fintech",
    "healthtech",
    "climatetech",
    "saas",
    "ai_ml",
    "cybersecurity",
    "proptech",
    "edtech",
]


@dataclass(frozen=True)
class ScoringConfig:
    """Typed view over the YAML so the rest of the code never touches raw dicts."""

    pillar_weights: dict
    sector_momentum: dict
    timing: dict
    capital_efficiency: dict
    bands: list
    public_comps: dict

    def validate(self) -> None:
        total = round(sum(self.pillar_weights.values()), 6)
        if total != 1.0:
            raise ValueError(
                f"pillar_weights must sum to 1.0, got {total}. "
                "Fix config/scoring_weights.yaml."
            )


def load_scoring_config(path: Path = CONFIG_PATH) -> ScoringConfig:
    """Load and validate the scoring configuration."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    cfg = ScoringConfig(
        pillar_weights=raw["pillar_weights"],
        sector_momentum=raw["sector_momentum"],
        timing=raw["timing"],
        capital_efficiency=raw["capital_efficiency"],
        bands=raw["bands"],
        public_comps=raw["public_comps"],
    )
    cfg.validate()
    return cfg


def ensure_dirs() -> None:
    """Create output directories if they do not yet exist."""
    for d in (RAW_DIR, PROCESSED_DIR, SAMPLE_DIR, MEMO_DIR, DIGEST_DIR):
        d.mkdir(parents=True, exist_ok=True)
