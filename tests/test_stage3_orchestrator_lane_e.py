from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.core.stage3_orchestrator import Stage3Orchestrator, _select_stage3_anchor_recent_window


@pytest.fixture
def orch():
    app = SimpleNamespace(stage_rejection_history=[])
    ctx = SimpleNamespace(ui=SimpleNamespace(log=MagicMock()))
    return Stage3Orchestrator(app=app, context=ctx)


def test_build_stage3_blueprint_semantic_bundle_shell_delegates_to_helper_family(orch):
    prev_blueprints = [{"ep_num": ep} for ep in range(1, 9)]
    expected_window = _select_stage3_anchor_recent_window(prev_blueprints)
    expected_focus_window = expected_window
    smart_bundle = {"semantic_ctx": "[sc]", "work_focus": {"focus": "npc"}, "plan": object()}
    final_bundle = {
        "semantic_ctx": "[final]",
        "work_focus": smart_bundle["work_focus"],
        "plan": smart_bundle["plan"],
        "source_counts": {},
        "coverage_warnings": [],
        "observation": {},
        "blueprint_window": expected_window,
    }
    orch._collect_stage3_smart_retrieval_bundle = MagicMock(return_value=smart_bundle)
    orch._inject_stage3_treatment_block_context = MagicMock(return_value="[tb]")
    orch._inject_stage3_timeline_advisory = MagicMock(return_value="[timeline]")
    orch._finalize_stage3_blueprint_semantic_bundle = MagicMock(return_value=final_bundle)

    result = orch._build_stage3_blueprint_semantic_bundle(
        working_ep=8,
        arc_data={"ep_start": 8, "ep_end": 10},
        arc_idx=1,
        prev_blueprints=prev_blueprints,
        entity_registry={"characters": [{"name": "Seo"}]},
        protagonist_name="Seo",
    )

    assert result == final_bundle
    orch._collect_stage3_smart_retrieval_bundle.assert_called_once_with(
        working_ep=8,
        arc_data={"ep_start": 8, "ep_end": 10},
        prev_blueprints=expected_focus_window,
        entity_registry={"characters": [{"name": "Seo"}]},
        protagonist_name="Seo",
    )
    orch._inject_stage3_treatment_block_context.assert_called_once_with(
        semantic_ctx="[sc]",
        working_ep=8,
        arc_data={"ep_start": 8, "ep_end": 10},
        arc_idx=1,
    )
    orch._inject_stage3_timeline_advisory.assert_called_once_with(
        semantic_ctx="[tb]",
        arc_idx=1,
        arc_data={"ep_start": 8, "ep_end": 10},
    )
    orch._finalize_stage3_blueprint_semantic_bundle.assert_called_once()
    finalize_kwargs = orch._finalize_stage3_blueprint_semantic_bundle.call_args.kwargs
    assert finalize_kwargs["semantic_ctx"] == "[timeline]"
    assert finalize_kwargs["work_focus"] == smart_bundle["work_focus"]
    assert finalize_kwargs["plan"] == smart_bundle["plan"]
    assert finalize_kwargs["blueprint_window"] == expected_window
    assert finalize_kwargs["focus_window"] == expected_focus_window


def test_append_stage3_rejection_history_keeps_stage3_payload_shape(orch):
    pipeline_result = {
        "retry_count": 1,
        "final_verdict": "REJECT",
        "specific_issue": "scene order drift",
        "fix_scope": "scene",
        "phases": {
            "validate": {
                "score_breakdown": {
                    "continuity": 62,
                    "pacing": 71,
                    "note": "ignored",
                }
            }
        },
    }

    orch._append_stage3_rejection_history(pipeline_result=pipeline_result, arc_no=4)

    assert len(orch.app.stage_rejection_history) == 1
    entry = orch.app.stage_rejection_history[0]
    assert entry["stage"] == 3
    assert entry["arc_no"] == 4
    assert entry["attempt"] == 1
    assert entry["specific_issue"] == "scene order drift"
    assert entry["fix_scope"] == "scene"
    assert entry["score_breakdown"] == {"continuity": 62, "pacing": 71}


def test_handle_failure_shell_uses_new_helper_family_and_returns_break(orch):
    orch._record_stage3_failure_attempt = MagicMock()
    orch._append_stage3_rejection_history = MagicMock()
    orch._record_stage3_failure_audit_metrics = MagicMock()
    orch._record_stage3_failure_quality_dashboard = MagicMock()

    result = orch._handle_failure(
        4,
        {"final_verdict": "REJECT"},
        success_count=2,
        fail_count=1,
        arc_no=3,
        blueprint={"scene_breakdown": {}},
    )

    assert orch.ctx.ui.log.call_count == 3
    assert "Blueprint 생성 실패" in orch.ctx.ui.log.call_args_list[0].args[0]
    orch._record_stage3_failure_attempt.assert_called_once_with(
        working_ep=4,
        pipeline_result={"final_verdict": "REJECT"},
        arc_no=3,
        blueprint={"scene_breakdown": {}},
    )
    orch._append_stage3_rejection_history.assert_called_once_with(
        pipeline_result={"final_verdict": "REJECT"},
        arc_no=3,
    )
    orch._record_stage3_failure_audit_metrics.assert_called_once_with(
        working_ep=4,
        pipeline_result={"final_verdict": "REJECT"},
    )
    orch._record_stage3_failure_quality_dashboard.assert_called_once_with(working_ep=4)
    assert result == {"next_ep": 4, "success_count": 2, "fail_count": 2, "break": True}
