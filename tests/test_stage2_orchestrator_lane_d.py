from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage2_orchestrator import Stage2Orchestrator


class _DummySpinner:
    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def update_detail(self, _detail):
        return None


def _make_ctx():
    ui = MagicMock()
    ui.log = MagicMock()
    analyst = MagicMock()
    lore = MagicMock()
    return SimpleNamespace(
        ui=ui,
        agents={"analyst": analyst},
        sys=SimpleNamespace(lore=lore),
        stage_rejection_history=[],
        current_project=SimpleNamespace(name="proj"),
    )


def test_run_stage2_joint_stitching_updates_repaired_context_and_anchors():
    ctx = _make_ctx()
    ctx.agents["analyst"].stitch_joints.return_value = {
        "status": "REPAIRED",
        "repaired_joint_b": "patched-context",
        "entity_anchors": {"npc": "anchor"},
    }
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)
    enriched_batch = [
        (0, {"joint_docs": {"a": 1}, "content": {"context": "left"}}),
        (1, {"joint_docs": {"b": 2}, "content": {"context": "right"}}),
    ]

    orch._run_stage2_joint_stitching(
        enriched_batch=enriched_batch,
        batch_start=0,
        batch_end=2,
        stage_spinner_cls=_DummySpinner,
    )

    assert enriched_batch[1][1]["content"]["context"] == "patched-context"
    ctx.sys.lore.update_v20_assets.assert_called_once_with({"Temporary_Anchors": {"npc": "anchor"}})
    ctx.ui.log.assert_any_call("   🧶 Arc 1-2 인과율 용접 완료.")


def test_apply_stage2_validation_advisories_merges_corrections_and_python_advisories():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())

    result = orch._apply_stage2_validation_advisories(
        constraint_block="seed",
        corrections_made=["fix one", "fix two"],
        python_advisories=[
            {"source": "flow", "severity": "warn", "message": "message one"},
            {"source": "dup", "severity": "info", "message": "message two"},
        ],
    )

    assert "seed" in result
    assert "[Python 자동 수정 2건]" in result
    assert "fix one" in result
    assert "[Python Pre-Director advisory 2건]" in result
    assert "[flow:warn] message one" in result
    assert "[dup:info] message two" in result


def test_augment_stage2_feedback_from_rejections_prefixes_pattern_feedback():
    ctx = _make_ctx()
    ctx.stage_rejection_history = [
        {"stage": 2, "arc_no": 3, "reason": "x"},
        {"stage": 2, "arc_no": 3, "reason": "y"},
        {"stage": 4, "arc_no": 3, "reason": "skip"},
    ]
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)
    orch._compose_rejection_pattern_feedback = MagicMock(return_value="[pattern]")

    result = orch._augment_stage2_feedback_from_rejections(
        current_feedback="base feedback",
        attempt=1,
        global_arc_no=3,
    )

    assert result == "[pattern]\nbase feedback"
    ctx.ui.log.assert_any_call("      🔍 [V60.10] REJECT 패턴 분석 주입 (2건)")


def test_resolve_stage2_current_vol_strategy_falls_back_when_volume_missing():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx())

    result = orch._resolve_stage2_current_vol_strategy(
        volumes_strategy=[{"vol_no": 1, "strategy_doc": "vol1"}],
        global_arc_no=7,
    )

    assert result == {"vol_no": 2, "strategy_doc": ""}
