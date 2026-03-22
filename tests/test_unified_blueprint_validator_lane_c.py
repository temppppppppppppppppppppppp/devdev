from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator


def test_lane_c_run_compare_validation_normalizes_selected_payload():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    candidates = [{"name": "alpha"}, {"name": "beta"}]
    validator._prepare_compare_candidate = Mock(
        side_effect=[
            ({"issues": [{"issue": "warn-a"}], "has_critical": False}, {"candidate_index": 0, "quality_risk": True}),
            ({"issues": [{"issue": "warn-b"}], "has_critical": False}, {"candidate_index": 1, "quality_risk": False}),
        ]
    )
    director = SimpleNamespace(
        compare_and_select_blueprint=Mock(
            return_value={
                "decision": "PASS_WITH_WARNING",
                "selected_index": 9,
                "selected_blueprint": None,
                "score": "68",
                "selection_reason": "bounded compare",
                "comparison_notes": "note",
                "quality_risk": False,
                "revision_required": False,
            }
        )
    )

    verdict, result = validator._run_compare_validation(
        all_candidates=candidates,
        arc_data={"arc_no": 2},
        constraint_block={},
        prev_blueprint=None,
        director=director,
        entity_registry=None,
        state_tracker=None,
        working_ep=3,
        arc_idx=2,
    )

    assert verdict == "PASS_WITH_WARNING"
    assert result["selected_index"] == 0
    assert result["selected_blueprint"] is candidates[0]
    assert result["issues"] == [{"issue": "warn-a"}]
    assert result["quality_risk"] is True
    assert result["revision_required"] is True
    assert result["candidate_count"] == 2
    assert result["selected_candidate_advisory"]["candidate_index"] == 0


def test_lane_c_prepare_director_validation_payload_injects_focus_and_hud_context():
    context = MagicMock()
    context.get_causal_history_summary.return_value = "causal-history"
    validator = UnifiedBlueprintValidator(context=context, client=None)
    state_tracker = SimpleNamespace(
        npc_registry={
            "Master": {
                "status": "dead",
                "death_arc": 4,
                "aliases": ["사부"],
            }
        }
    )

    payload = validator._prepare_director_validation_payload(
        blueprint={
            "integrated_scenario": "core scenario",
            "_ensemble_meta": {
                "python_warnings": [
                    {"message": "dead npc risk", "focus": "flashback-only"}
                ]
            },
        },
        arc_data={"tactical_doc": {"goal": "protect"}, "ep_start": 3, "ep_count": 7},
        prev_blueprint={"ending_hook": "prev ending"},
        entity_registry={"npc": "registry"},
        state_tracker=state_tracker,
        prev_hud={"qi": 9},
        working_ep=5,
    )

    assert payload["ep_num"] == 5
    assert payload["prev_full_text"] == "prev ending"
    assert payload["arc_pos"] == 3
    assert payload["total_eps"] == 7
    assert payload["history_summary"] == "causal-history"
    assert "dead npc risk" in payload["manuscript"]
    assert "flashback-only" in payload["manuscript"]
    assert payload["manuscript"].endswith("core scenario")
    assert payload["arc_doc"].startswith("{")
    assert payload["validation_context"]["prev_hud"] == {"qi": 9}
    assert payload["validation_context"]["martial_hud"] == {"qi": 9}
    assert payload["validation_context"]["encyclopedia"]["npcs"][0]["name"] == "Master"


def test_lane_c_build_director_validation_result_keeps_pass_with_fix_contract():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}
    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MINOR",
                    "category": "structure",
                    "issue": "minor issue",
                    "fix_hint": "tighten shell",
                }
            ]
        },
        director_result={
            "decision": "PASS_WITH_FIX",
            "reason": "needs repair",
            "feedback": "patch the issue",
            "score": "72",
            "fix_scope": "scene",
            "fix_scope_reasoning": "reasoned",
            "re_slice_instruction": "slice again",
            "selection_reason": "selected after review",
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["feedback"] == "patch the issue"
    assert result["score"] == 72
    assert result["revision_required"] is True
    assert result["score_breakdown"] == {"director_score": 72, "pre_issues_count": 1}
    assert result["selection_reason"] == "selected after review"
    assert result["verdict_reason"] == "needs repair"
    assert result["quality_risk"] is True
    assert blueprint["_ensemble_meta"]["python_warnings"][0]["source"] == "python_prevalidate"


def test_lane_c_validate_without_director_fail_closes_after_python_prevalidation():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    validator._run_python_prevalidation_phase = Mock(
        return_value={"issues": [{"severity": "MAJOR", "issue": "missing scene"}], "has_critical": False}
    )

    verdict, result = validator.validate(
        blueprint={"scene_breakdown": {"s1": "x"}, "integrated_scenario": "body"},
        arc_data={"arc_no": 1},
        constraint_block={},
        director=None,
        working_ep=1,
        arc_idx=1,
    )

    assert verdict == "REJECT"
    assert result["phase"] == "no_director"
    assert result["issues"] == [{"severity": "MAJOR", "issue": "missing scene"}]
    assert result["score"] == 0


def test_lane_c_python_pre_validate_reports_structure_issues_in_stable_order():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={},
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data=None,
    )

    issue_labels = [issue["issue"] for issue in pre_result["issues"]]

    assert issue_labels[:4] == [
        "필수 필드 누락: scene_breakdown",
        "필수 필드 누락: integrated_scenario",
        f"분량 부족: 0자 < {validator.min_chars}자",
        "씬 부족: 0개 < 3개",
    ]
    assert pre_result["has_critical"] is False
    assert pre_result["has_major_excess"] is True
    assert pre_result["critical_summary"] == ""


def test_lane_c_python_pre_validate_combines_structure_fidelity_and_continuity():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": [
                "짧은 도입",
                {"title": "추적"},
            ],
            "integrated_scenario": "주인공이 흔적을 따라간다.",
            "start_location": "부산 항",
        },
        constraint_block={},
        prev_blueprint={"end_location": "서울 북문"},
        state_tracker=None,
        arc_data={"state_constraints": {"relationship_changes": [{"target": "연화"}, {"npc": "독호"}]}},
    )

    categories = [issue["category"] for issue in pre_result["issues"]]

    assert categories == ["structure", "structure", "structure", "fidelity", "continuity"]
    assert pre_result["has_critical"] is False
    assert pre_result["has_major_excess"] is True
    assert pre_result["critical_summary"] == ""


def test_lane_c_python_pre_validate_flags_stop_line_leak_as_critical():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {"scene_1": {}, "scene_2": {}, "scene_3": {}},
            "integrated_scenario": "주인공은 황실 경매장 잠입 계획을 실행하고 독호와 재회해 은장도를 확보한다. " * 30,
        },
        constraint_block={"stop_line": {"content": "황실 경매장 잠입 계획을 실행하고 독호와 재회해 은장도를 확보한다"}},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert pre_result["has_critical"] is True
    assert pre_result["critical_summary"] == "정지선 위반: 다음 화 내용 포함"
    assert any(issue["category"] == "arc_compliance" for issue in pre_result["issues"])
