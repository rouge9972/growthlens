"""
scripts/make_sample_data.py
===========================
Writes the committed 50-company sample dataset (data/sample/companies_sample.csv)
so the repo runs end-to-end even with zero network access. Re-run only if you
want to regenerate the sample.
"""
from __future__ import annotations

from growthlens import config as C
from growthlens.ingestion.synthetic import generate_companies


def main() -> None:
    C.ensure_dirs()
    df = generate_companies(n=50, seed=7)
    df.to_csv(C.SAMPLE_COMPANIES, index=False)
    print(f"Wrote {len(df)} sample companies -> {C.SAMPLE_COMPANIES}")


if __name__ == "__main__":
    main()
