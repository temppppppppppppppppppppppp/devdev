"""Stage3 mock smoke runner for the 코덱스_테스트 project.

Runs Stage3 with mocked LLM agents, persists blueprints to the real project DB,
and exports blueprint JSON files under plans/blueprints/.

Validation tier: focused_mutation
Mutation boundary: writes fixture-project DB and blueprint artifacts.

Usage:
    python scripts/run_stage3_smoke.py
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.stage3_context import Stage3Context  # noqa: E402
from modules.core.stage3_orchestrator import Stage3Orchestrator  # noqa: E402
from modules.models.blueprint import Blueprint  # noqa: E402
from scripts.regression_validation_tiers import FOCUSED_MUTATION  # noqa: E402

PROJECT_NAME = "\ucf54\ub371\uc2a4_\ud14c\uc2a4\ud2b8"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME
DB_PATH = PROJECT_DIR / "project_data.db"
BP_OUTPUT_DIR = PROJECT_DIR / "plans" / "blueprints"
VALIDATION_TIER = FOCUSED_MUTATION
MUTATES_PROJECT_STATE = True


@contextmanager
def _noop_spinner(*_args, **_kwargs):
    yield


def _normalize_arcs(raw_arcs: object) -> list[dict]:
    """Normalize DB anchor arcs into a list[dict]."""
    if isinstance(raw_arcs, list):
        return [arc for arc in raw_arcs if isinstance(arc, dict)]
    if isinstance(raw_arcs, dict):
        values = [arc for arc in raw_arcs.values() if isinstance(arc, dict)]
        return sorted(values, key=lambda arc: arc.get("ep_start", 0) if isinstance(arc.get("ep_start"), int) else 0)
    return []


def _make_mock_blueprint(ep_num: int, arc_data: dict | None = None) -> dict:
    """Create a valid Blueprint payload using arc content for readable story output."""
    content = arc_data.get("content", {}) if isinstance(arc_data, dict) else {}
    if not isinstance(content, dict):
        content = {}

    context = str(content.get("context", "market pressure rises"))
    villain = str(content.get("event_villain", "liquidity crunch"))
    solution = str(content.get("solution", "risk control execution"))
    reward = str(content.get("reward", "capital recovery"))

    return Blueprint(
        episode_number=ep_num,
        integrated_scenario=f"Episode {ep_num}: {context[:180]}",
        scene_breakdown={
            "scene_1": {"summary": context[:120], "location": "office"},
            "scene_2": {"summary": villain[:120], "location": "exchange"},
            "scene_3": {"summary": solution[:120], "location": "war-room"},
            "scene_4": {"summary": reward[:120], "location": "office"},
        },
        pacing_notes="fast, escalating pressure",
        target_beat=f"arc pressure episode {ep_num}",
        core_tension=villain[:100],
        expected_ending=reward[:100],
        start_location="office",
        location="office",
    ).model_dump()


def _build_mock_app(db: DBManager, bible: dict, arcs: list[dict]) -> MagicMock:
    """Build a mock app with all Stage3Orchestrator dependencies satisfied."""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()

    project = MagicMock()
    project.db = db
    project.arcs = arcs
    project.master_bible = bible
    project.name = PROJECT_NAME

    generated_blueprints: dict[int, dict] = {}

    def _get_blueprint(ep_num: int):
        return generated_blueprints.get(ep_num)

    def _save_blueprint(ep_num: int, bp_data: dict):
        generated_blueprints[ep_num] = bp_data
        db.save_blueprint(ep_num, bp_data)

    project.get_blueprint = MagicMock(side_effect=_get_blueprint)
    project.save_episode_blueprint = MagicMock(side_effect=_save_blueprint)
    project._generated_blueprints = generated_blueprints

    app.current_project = project
    app.current_project.db.get_latest_blueprint_number = MagicMock(return_value=0)

    app._get_max_episode_from_manuscripts = MagicMock(return_value=0)
    app._get_int_input = MagicMock(
        side_effect=lambda _prompt, default=None, min_val=1, max_val=3, **_kw: min(max_val, min_val + 2)
    )

    def _get_arc_context_for_episode(ep_num: int):
        for idx, arc in enumerate(arcs):
            ep_start = arc.get("ep_start")
            ep_end = arc.get("ep_end")
            if isinstance(ep_start, int) and isinstance(ep_end, int) and ep_start <= ep_num <= ep_end:
                return idx, arc
        return None, None

    app._get_arc_context_for_episode = MagicMock(side_effect=_get_arc_context_for_episode)
    app._validate_arc_data_fields = MagicMock(side_effect=lambda arc, _idx: arc)
    app._validate_blueprint_integrity = MagicMock(
        side_effect=lambda bp: isinstance(bp, dict)
        and isinstance(bp.get("integrated_scenario"), str)
        and isinstance(bp.get("scene_breakdown"), dict)
    )
    app._get_protagonist_name = MagicMock(return_value="\uc2dc\uc724")
    app._fix_entity_registry_protagonist = MagicMock(side_effect=lambda registry, _name: registry)
    app._safe_commit = MagicMock(side_effect=lambda: db.conn.commit())
    app._audit_event = MagicMock()
    app._write_audit_summary = MagicMock()

    app.selected_genre = {"type": "investment", "name": "investment"}
    app.state_tracker = MagicMock()
    app.world_state = MagicMock()
    app.fact_ledger = MagicMock()
    app.preset_registry = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()

    def _mock_generate(**kwargs):
        ep_num = int(kwargs.get("ep_num", 1))
        arc_data = kwargs.get("arc_data", {})
        blueprint = _make_mock_blueprint(ep_num, arc_data if isinstance(arc_data, dict) else None)
        result = {
            "final_verdict": "PASS",
            "phases": {
                "generate": {
                    "selected_strategy": "momentum",
                    "selected_score": 85,
                }
            },
        }
        return blueprint, result

    app.agents = {
        "three_phase_bp": MagicMock(
            generate=MagicMock(side_effect=_mock_generate),
            get_stats=MagicMock(return_value={"pass_rate": "100%"}),
        ),
        "director": MagicMock(),
        "state_extractor": MagicMock(
            extract_cumulative_state=MagicMock(return_value={"entity_registry": {"characters": [{"name": "mentor"}]}})
        ),
    }

    return app


def _export_blueprints(db: DBManager, episode_numbers: list[int]) -> int:
    """Export generated blueprints to JSON files."""
    BP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exported = 0
    for ep_num in sorted(set(episode_numbers)):
        bp_data = db.get_blueprint(ep_num)
        if not bp_data:
            continue
        out_path = BP_OUTPUT_DIR / f"bp_ep_{ep_num}.json"
        out_path.write_text(json.dumps(bp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[FILE] saved {out_path.name}")
        exported += 1
    return exported


def main() -> None:
    assert DB_PATH.exists(), f"DB not found: {DB_PATH}"

    db = DBManager(DB_PATH)
    try:
        bible = db.load_anchor("bible")
        arcs = _normalize_arcs(db.load_anchor("arcs"))
        assert bible, "Bible is empty"
        assert len(arcs) >= 3, f"arcs must be >= 3, got {len(arcs)}"
        print(f"[OK] data loaded: arcs={len(arcs)}")

        app = _build_mock_app(db, bible, arcs)
        ctx = Stage3Context(
            ui=app.ui,
            current_project=app.current_project,
            get_protagonist_name=lambda: "\uc2dc\uc724",
        )

        print("[RUN] Stage3 start (3 episodes, mock LLM)...")
        with patch("modules.core.spinners.StageSpinner", _noop_spinner):
            orchestrator = Stage3Orchestrator(app=app, context=ctx)
            orchestrator.stage_3_batch_blueprinting()
        print("[OK] Stage3 complete")

        generated_eps = sorted(app.current_project._generated_blueprints.keys())
        if not generated_eps:
            raise RuntimeError("No blueprints were generated")

        exported = _export_blueprints(db, generated_eps)
        if exported == 0:
            raise RuntimeError("Blueprint JSON export failed: no files written")

        print(f"[DONE] blueprints={len(generated_eps)} in DB and JSON={exported} at {BP_OUTPUT_DIR}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
