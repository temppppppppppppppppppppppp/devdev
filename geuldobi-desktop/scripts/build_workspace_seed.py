from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DIST_SEED = ROOT / "dist" / "workspace-seed"
SAMPLE_PROJECT_SOURCE = ROOT / "projects" / "0"
SAMPLE_PROJECT_TARGET = "investment_canary_demo"


def _require_single(pattern_root: Path, pattern: str) -> Path:
    matches = sorted(pattern_root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one match for {pattern_root / pattern}, found {len(matches)}")
    return matches[0]


def _reset_seed_dir() -> None:
    if DIST_SEED.exists():
        shutil.rmtree(DIST_SEED)
    DIST_SEED.mkdir(parents=True, exist_ok=True)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _count_files(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file())


def _stage_project_seed(project_dest: Path) -> dict:
    if SAMPLE_PROJECT_SOURCE.exists():
        _copy_tree(SAMPLE_PROJECT_SOURCE, project_dest)
        return {
            "source": str(SAMPLE_PROJECT_SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "packaged": str(project_dest.relative_to(DIST_SEED)).replace("\\", "/"),
            "file_count": _count_files(project_dest),
            "mode": "copied",
        }

    project_dest.mkdir(parents=True, exist_ok=True)
    placeholder = project_dest / "README.txt"
    placeholder.write_text(
        "Sample project source was missing at build time.\n"
        "Create a new project from the desktop app after first launch.\n",
        encoding="utf-8",
    )
    return {
        "source": None,
        "packaged": str(project_dest.relative_to(DIST_SEED)).replace("\\", "/"),
        "file_count": _count_files(project_dest),
        "mode": "placeholder",
        "reason": f"sample project source missing: {SAMPLE_PROJECT_SOURCE}",
    }


def main() -> None:
    bible_source = _require_single(ROOT / "bible", "01_bi_*.json")
    treatment_source = _require_single(ROOT / "treatments", "01_tr_*.json")

    _reset_seed_dir()

    bible_dest = DIST_SEED / "bible" / bible_source.name
    treatment_dest = DIST_SEED / "treatments" / treatment_source.name
    project_dest = DIST_SEED / "projects" / SAMPLE_PROJECT_TARGET

    _copy_file(bible_source, bible_dest)
    _copy_file(treatment_source, treatment_dest)
    project_record = _stage_project_seed(project_dest)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_kind": "desktop_workspace_seed_v1",
        "materials": {
            "bible": [
                {
                    "source": str(bible_source.relative_to(ROOT)).replace("\\", "/"),
                    "packaged": str(bible_dest.relative_to(DIST_SEED)).replace("\\", "/"),
                }
            ],
            "treatments": [
                {
                    "source": str(treatment_source.relative_to(ROOT)).replace("\\", "/"),
                    "packaged": str(treatment_dest.relative_to(DIST_SEED)).replace("\\", "/"),
                }
            ],
            "projects": [
                project_record
            ],
        },
    }
    (DIST_SEED / "seed-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"workspace seed staged at {DIST_SEED}")


if __name__ == "__main__":
    main()
