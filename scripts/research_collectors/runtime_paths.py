from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = PROJECT_ROOT / "material_ssot" / "10_research"
MARKET_SNAPSHOTS_ROOT = RESEARCH_ROOT / "40_analysis" / "market_snapshots"
RAW_INGEST_ROOT = RESEARCH_ROOT / "80_ingest_raw"


def ensure_dated_analysis_bucket(run_day: str) -> Path:
    bucket = MARKET_SNAPSHOTS_ROOT / run_day
    bucket.mkdir(parents=True, exist_ok=True)
    return bucket


def ensure_dated_raw_bucket(run_day: str) -> Path:
    bucket = RAW_INGEST_ROOT / run_day
    bucket.mkdir(parents=True, exist_ok=True)
    return bucket
