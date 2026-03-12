from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.db_manager import DBManager
from modules.core.quality_sidecar_bootstrap import bootstrap_quality_sidecars, inspect_quality_sidecar_health


def _project_root() -> Path:
    return ROOT / "projects"


def _iter_project_dirs(projects_root: Path, project_name: str | None) -> list[Path]:
    if project_name:
        return [projects_root / project_name]
    return [path for path in sorted(projects_root.iterdir()) if path.is_dir()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill quality sidecar tables from legacy logs/manuscripts.")
    parser.add_argument("--project", help="Single project name under ./projects", default="")
    args = parser.parse_args()

    projects_root = _project_root()
    project_dirs = _iter_project_dirs(projects_root, args.project.strip() or None)
    if not project_dirs:
        print("No project directories found.")
        return 0

    for project_dir in project_dirs:
        db_path = project_dir / "project_data.db"
        if not db_path.exists():
            continue
        db = DBManager(db_path)
        try:
            report = bootstrap_quality_sidecars(project_dir, db)
            health = inspect_quality_sidecar_health(project_dir, db)
        finally:
            db.close()

        print(f"[{project_dir.name}]")
        print(
            "  backfilled:",
            f"labels={report['backfilled_labels']}",
            f"signals={report['backfilled_signals']}",
            f"missing_manuscripts={len(report['missing_manuscript_eps'])}",
        )
        print(
            "  health:",
            f"stage4_eps={health['stage4_validation_eps']}",
            f"labels={health['quality_label_rows']}",
            f"signals={health['quality_signal_rows']}",
            f"retrieval_obs={health['retrieval_observation_rows']}",
            f"manual_reviews={health['manual_review_rows']}",
            f"role_fit={health['role_fit_constraints']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
