import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage4_post_processor import Stage4PostProcessor


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/2026-03-13/stage4-pass-artifact-contract.json"
SOURCE_PATHS = (
    ROOT / "modules/core/stage4_post_processor.py",
    ROOT / "modules/core/stage4_post_pass_runtime.py",
)


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _soft_failure_ops(tmp_path: Path) -> list[str]:
    path = tmp_path / "logs" / "soft_failures.jsonl"
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [row["operation"] for row in rows if row.get("component") == "stage4_post_processor"]


def _derive_completeness_status(result: bool, soft_ops: list[str]) -> str:
    if not result:
        return "hard_incomplete"
    if soft_ops:
        return "hard_complete_soft_degraded"
    return "hard_complete_soft_clean"


def _make_processor(tmp_path: Path, *, with_world_state: bool = False) -> Stage4PostProcessor:
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.sys = MagicMock()
    ctx.sys.hud = MagicMock()
    ctx.sys.hud.snapshot.return_value = {}
    ctx.sys.hud.bulk_update = MagicMock()

    director = MagicMock()
    director.on_approve_workflow.return_value = {}
    manager = MagicMock()
    manager.update_state_and_lore_v20.return_value = {
        "state_updates": {
            "time_passed": "1일",
            "public_reputation": {"market": "stable"},
        }
    }
    state_extractor = MagicMock()
    state_extractor.extract_satisfaction_tag.return_value = None
    ctx.agents = {
        "director": director,
        "manager": manager,
        "state_extractor": state_extractor,
    }
    ctx.audit_event = MagicMock()

    db = MagicMock()
    db.conn = MagicMock()
    db.get_episode_bible.return_value = {}
    db.load_anchor.return_value = []
    db.transaction.return_value.__enter__ = MagicMock(return_value=None)
    db.transaction.return_value.__exit__ = MagicMock(return_value=False)

    project = MagicMock()
    project.db = db
    project.name = "demo"
    project.latest_state = {}
    project.seed_tracker = None
    project.karma_matrix = {}
    project.master_bible = {
        "MasterBible": {
            "AssetLibrary": {"KeyNPCs": []},
            "protagonist_config": {"name": "mc"},
        },
        "npc_registry": {},
    }
    project.paths = SimpleNamespace(root=tmp_path)
    ctx.current_project = project

    if with_world_state:
        ws = MagicMock()
        ws.update_from_state_changes = MagicMock()
        ws.update_protagonist_state = MagicMock()
        ws.save = MagicMock()
        ctx.world_state = ws

        fl = MagicMock()
        fl.update_from_state_changes = MagicMock()
        fl.update_from_bible_delta = MagicMock()
        fl.save = MagicMock()
        fl.get_stats.return_value = {"characters": 1, "items": 1}
        ctx.fact_ledger = fl
    else:
        ctx.world_state = None
        ctx.fact_ledger = None

    ctx.memory = None
    ctx.state_tracker = None
    ctx.character_voice = None
    ctx.foreshadow_tracker = None
    ctx.failure_learner = None
    ctx.quality_dashboard = None
    ctx.perf_timer = MagicMock()
    ctx.flush_audit_buffer = MagicMock()
    ctx.get_protagonist_name = lambda: "mc"
    ctx.generate_narrative_summary = MagicMock()
    ctx.emotion_tracker = None
    ctx.session_logger = None

    return Stage4PostProcessor(ctx)


def _run_pass(pp: Stage4PostProcessor, tmp_path: Path) -> bool:
    return pp.process_pass_result(
        next_ep=3,
        final_manuscript="stage4 manuscript " * 400,
        final_title="episode title",
        final_state_updates={"warning_count": 0},
        blueprint={"scene_breakdown": []},
        arc_data={"arc_no": 1},
        output_dir=tmp_path,
        v50_modules_available=False,
        extract_chain_link_fn=lambda *_args, **_kwargs: {},
    )


def test_stage4_pass_artifact_contract_matches_source_markers() -> None:
    contract = _load_contract()
    source = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS)

    assert contract["contract_id"] == "stage4-pass-artifact-contract-v1"
    assert "save_manuscript(" in source
    assert "save_episode_bible" in source
    assert "_meta_save_failed" in source
    assert 'operation="save_state_log_with_summary"' in source
    assert 'operation="save_world_state_atomic"' in source
    assert 'operation="save_episode_quality_label"' in source
    assert 'operation="save_episode_quality_signal"' in source
    assert "file_path.write_text" in source


def test_hard_incomplete_when_episode_bible_save_fails(tmp_path: Path) -> None:
    pp = _make_processor(tmp_path)
    pp.ctx.current_project.db.save_episode_bible.side_effect = RuntimeError("bible write failed")

    result = _run_pass(pp, tmp_path)
    soft_ops = _soft_failure_ops(tmp_path)

    assert result is False
    assert _derive_completeness_status(result, soft_ops) == "hard_incomplete"
    pp.ctx.audit_event.assert_any_call("episode_bible_save_failed", "save_episode_bible 실패", {"ep": 3})


def test_soft_degraded_when_state_log_save_fails(tmp_path: Path) -> None:
    pp = _make_processor(tmp_path)
    pp.ctx.current_project.db.save_state_log_with_summary.side_effect = RuntimeError("state log busy")

    result = _run_pass(pp, tmp_path)
    soft_ops = _soft_failure_ops(tmp_path)

    assert result is True
    assert "save_state_log_with_summary" in soft_ops
    assert _derive_completeness_status(result, soft_ops) == "hard_complete_soft_degraded"


def test_soft_degraded_when_world_state_atomic_save_fails(tmp_path: Path) -> None:
    pp = _make_processor(tmp_path, with_world_state=True)
    pp.ctx.fact_ledger.save.side_effect = RuntimeError("fact ledger write failed")

    result = _run_pass(pp, tmp_path)
    soft_ops = _soft_failure_ops(tmp_path)

    assert result is True
    assert "save_world_state_atomic" in soft_ops
    assert _derive_completeness_status(result, soft_ops) == "hard_complete_soft_degraded"


def test_soft_clean_when_no_stage4_soft_failures_exist(tmp_path: Path) -> None:
    pp = _make_processor(tmp_path)

    result = _run_pass(pp, tmp_path)
    soft_ops = _soft_failure_ops(tmp_path)

    assert result is True
    assert soft_ops == []
    assert _derive_completeness_status(result, soft_ops) == "hard_complete_soft_clean"
