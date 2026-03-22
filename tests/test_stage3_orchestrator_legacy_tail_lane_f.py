from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage3_orchestrator import Stage3Orchestrator


def test_legacy_stage3_blueprint_semantic_bundle_tail_delegates_to_split_helpers():
    orch = Stage3Orchestrator.__new__(Stage3Orchestrator)
    orch.ctx = SimpleNamespace()
    plan = SimpleNamespace(slots=[], total_budget_chars=0)
    orch._inject_stage3_treatment_block_context = MagicMock(return_value="after_treatment")
    orch._inject_stage3_timeline_advisory = MagicMock(return_value="after_timeline")
    orch._finalize_stage3_blueprint_semantic_bundle = MagicMock(
        return_value={"semantic_ctx": "after_timeline", "coverage_warnings": []}
    )

    result = Stage3Orchestrator._legacy_stage3_blueprint_semantic_bundle_tail(
        orch,
        working_ep=7,
        arc_data={"ep_start": 7, "ep_end": 9},
        arc_idx=2,
        entity_registry={"npc": {}},
        protagonist_name="Seo",
        semantic_ctx="seed",
        work_focus={"slot": "core"},
        plan=plan,
        blueprint_window=[{"ep": 6}],
        focus_window=[{"ep": 6}],
    )

    assert result["semantic_ctx"] == "after_timeline"
    orch._inject_stage3_treatment_block_context.assert_called_once_with(
        semantic_ctx="seed",
        working_ep=7,
        arc_data={"ep_start": 7, "ep_end": 9},
        arc_idx=2,
    )
    orch._inject_stage3_timeline_advisory.assert_called_once_with(
        semantic_ctx="after_treatment",
        arc_idx=2,
        arc_data={"ep_start": 7, "ep_end": 9},
    )
    orch._finalize_stage3_blueprint_semantic_bundle.assert_called_once_with(
        semantic_ctx="after_timeline",
        work_focus={"slot": "core"},
        plan=plan,
        working_ep=7,
        arc_data={"ep_start": 7, "ep_end": 9},
        entity_registry={"npc": {}},
        protagonist_name="Seo",
        blueprint_window=[{"ep": 6}],
        focus_window=[{"ep": 6}],
    )
