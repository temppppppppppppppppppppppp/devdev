import textwrap
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


def test_lane_c_prepare_compare_candidate_attaches_advisory_fix_pack():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    validator._python_pre_validate = Mock(
        return_value={
            "issues": [
                {
                    "severity": "MINOR",
                    "category": "scenario_density",
                    "issue": "anchor density is thin",
                    "advisory_only": True,
                    "director_focus": False,
                    "fix_pack": {
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "must_fix": ["add a concrete financial anchor"],
                        "do_not_regress": ["keep the opening move"],
                        "success_condition": "integrated scenario adds a concrete anchor",
                        "evidence_summary": "anchor_count=0",
                    },
                }
            ],
            "has_critical": False,
        }
    )
    validator._apply_dead_npc_advisory = Mock()
    candidate = {"integrated_scenario": "draft"}

    pre_result, advisory = validator._prepare_compare_candidate(
        candidate,
        candidate_index=0,
        arc_data={"arc_no": 1},
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        working_ep=1,
        arc_idx=1,
    )

    assert pre_result["has_critical"] is False
    assert advisory["advisory_fix_pack"]["target_kind"] == "local_sentence"
    assert advisory["advisory_fix_pack"]["patch_targets"] == ["integrated_scenario"]
    assert advisory["advisory_target_kind"] == "local_sentence"
    assert candidate["_ensemble_meta"]["advisory_fix_pack"]["evidence_summary"] == "anchor_count=0"


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
            "_ensemble_meta": {"python_warnings": [{"message": "dead npc risk", "focus": "flashback-only"}]},
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


def test_lane_c_python_warning_entries_skip_advisory_only_issues():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    entries, quality_risk = validator._build_python_warning_entries(
        [
            {
                "severity": "MINOR",
                "category": "scenario_density",
                "issue": "시나리오 구체성 부족: 구체적 앵커 0개 < 5개",
                "fix_hint": "기관명 보강",
                "advisory_only": True,
                "director_focus": False,
            }
        ]
    )

    assert entries == []
    assert quality_risk is False


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
            "repair_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "fix_scope_reasoning": "reasoned",
            "re_slice_instruction": "slice again",
            "selection_reason": "selected after review",
            "repair_contract": {
                "subtype": "movement",
                "fix_scope": "scene",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "target_kind": "scene_block",
                "provenance": "director_authored",
                "provenance_sources": ["director_compare"],
            },
            "scope_authority": {
                "fix_scope": "scene",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "widened": True,
            },
            "patch_target_records": [
                {
                    "summary": "scene_2.summary",
                    "scene_id": "scene_2",
                    "field_path": "scene_breakdown.scene_2.summary",
                    "target_kind": "scene_block",
                }
            ],
            "must_fix": ["scene 2 summary must reflect the repaired reveal"],
            "do_not_regress": ["scene 1 opening cadence must stay intact"],
            "success_condition": "scene 2 now states the reveal without rewriting the arc shell",
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
    assert result["repair_scope"] == "inplace"
    assert result["authoritative_fix_scope"] == "inplace"
    assert result["repair_contract"]["subtype"] == "movement"
    assert result["repair_contract"]["provenance"] == "director_authored"
    assert result["scope_authority"]["widened"] is True
    assert result["fix_pack"]["patch_targets"] == ["scene_2.summary"]
    assert result["fix_pack"]["patch_target_records"][0]["scene_id"] == "scene_2"
    assert result["fix_pack"]["target_kind"] == "scene_block"
    assert result["fix_pack"]["must_fix"] == ["scene 2 summary must reflect the repaired reveal"]
    assert result["fix_pack"]["success_condition"] == "scene 2 now states the reveal without rewriting the arc shell"
    assert blueprint["_ensemble_meta"]["python_warnings"][0]["source"] == "python_prevalidate"


def test_lane_c_build_director_validation_result_surfaces_advisory_fix_pack():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MINOR",
                    "category": "scenario_density",
                    "issue": "anchor density is thin",
                    "advisory_only": True,
                    "director_focus": False,
                    "fix_pack": {
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "must_fix": ["add a named market anchor"],
                        "do_not_regress": ["keep the opening move"],
                        "success_condition": "integrated scenario adds a named market anchor",
                        "evidence_summary": "anchor_count=0",
                    },
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "fine after director review",
            "feedback": "",
            "score": "91",
        },
    )

    assert verdict == "PASS"
    assert result["advisory_fix_pack"]["target_kind"] == "local_sentence"
    assert result["advisory_fix_pack"]["patch_targets"] == ["integrated_scenario"]
    assert blueprint["_ensemble_meta"]["advisory_fix_pack"]["evidence_summary"] == "anchor_count=0"
    assert "python_warnings" not in blueprint["_ensemble_meta"]


def test_lane_c_build_director_validation_result_synthesizes_v61_entity_patch_contract():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={"issues": []},
        director_result={
            "decision": "REJECT",
            "reason": "Entity Registry에 등록된 정식 명칭으로 통일하십시오.",
            "feedback": "[V61] Entity 일관성 오류",
            "score": 40,
            "v61_entity_check": {
                "decision": "REJECT",
                "fix_instructions": "'한태성'은 '한정호'으로 수정해야 합니다.",
                "mismatches": [
                    {
                        "category": "character",
                        "registered_name": "한정호",
                        "found_variant": "한태성",
                        "severity": "MAJOR",
                    }
                ],
            },
        },
    )

    assert verdict == "REJECT"
    assert result["fix_pack"]["target_kind"] == "entity_ref"
    assert result["fix_pack"]["patch_targets"] == ["한태성->한정호"]
    assert result["fix_pack"]["patch_target_records"][0]["text_anchor"]["old_text"] == "한태성"
    assert result["fix_pack"]["must_fix"] == ["Replace Entity Registry variant '한태성' with canonical '한정호'."]
    assert result["repair_contract"]["authoritative_fix_scope"] == "inplace"
    assert result["repair_contract"]["target_kind"] == "entity_ref"
    assert result["scope_authority"]["widened"] is False


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

    categories = [issue["category"] for issue in pre_result["issues"]]

    assert categories[:4] == ["structure", "structure", "structure", "structure"]
    assert pre_result["has_critical"] is False
    assert pre_result["has_major_excess"] is True
    assert pre_result["critical_summary"] == ""


def test_lane_c_python_pre_validate_combines_structure_fidelity_and_continuity():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": [
                "direct string scene",
                {"title": "추적"},
            ],
            "integrated_scenario": "주인공이 표적을 따라간다.",
            "start_location": "부산",
        },
        constraint_block={},
        prev_blueprint={"end_location": "서울 북문"},
        state_tracker=None,
        arc_data={"state_constraints": {"relationship_changes": [{"target": "도화"}, {"npc": "상호"}]}},
    )

    categories = [issue["category"] for issue in pre_result["issues"]]

    assert categories[:2] == ["structure", "structure"]
    assert "opening_anchor" in categories
    assert "mission_clarity" in categories
    assert "timeline_specificity" in categories
    assert "protagonist_state" in categories
    assert pre_result["has_critical"] is False
    assert pre_result["has_major_excess"] is True
    assert pre_result["critical_summary"] == ""


def test_lane_c_python_pre_validate_normalizes_opening_transition_contract():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {
        "scene_breakdown": {
            "scene_1": {
                "title": "직후 후속 비트",
                "summary": "통화를 마친 직후 숨을 고른다.",
                "location": "서재 앞 복도",
            }
        },
        "integrated_scenario": "한시우가 통화를 마친 직후 서재 앞 복도에서 숨을 고른다. " * 20,
        "start_location": "서재 앞 복도",
        "time_flow": "직후",
        "core_tension": "통화 후 대응",
        "expected_ending": "현관으로 이동한다",
        "target_beat": "후속 비트",
        "protagonist_state": {"mood": "긴장"},
    }

    pre_result = validator._python_pre_validate(
        blueprint=blueprint,
        constraint_block={},
        prev_blueprint={"end_location": "서재 앞 복도", "time_flow": "직후"},
        state_tracker=None,
        arc_data={},
    )

    assert blueprint["opening_transition"]["type"] == "direct_continuation"
    assert not any(issue["category"] == "opening_transition" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_declared_opening_transition_mismatch():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {
        "scene_breakdown": {
            "scene_1": {
                "title": "새 미팅",
                "summary": "한시우는 PB센터 상담실에서 새 회의를 시작한다. " * 8,
                "location": "강남 PB센터 상담실",
            }
        },
        "integrated_scenario": "한시우는 PB센터 상담실에서 새 회의를 시작한다. " * 30,
        "start_location": "강남 PB센터 상담실",
        "time_flow": "다음 날 아침",
        "core_tension": "새 투자 협상",
        "expected_ending": "협상 카드 확보",
        "target_beat": "새 국면 진입",
        "protagonist_state": {"mood": "냉정"},
        "opening_transition": {"type": "direct_continuation"},
    }

    pre_result = validator._python_pre_validate(
        blueprint=blueprint,
        constraint_block={},
        prev_blueprint={"end_location": "본가 저택 서재 앞 복도", "time_flow": "직후"},
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "opening_transition")
    assert "declared 'direct_continuation'" in issue["issue"]
    assert blueprint["opening_transition"]["type"] == "jump_opening"


def test_lane_c_python_pre_validate_skips_continuity_for_authorized_opening_shift():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "Arrival beat",
                    "summary": "The lead arrives at Packet Hall and locks the new footing immediately." * 6,
                    "location": "Packet Hall",
                }
            },
            "integrated_scenario": (
                "The lead arrives at Packet Hall under a declared cut and advances the plan. " * 20
            ),
            "start_location": "Packet Hall",
            "time_flow": "Later that afternoon",
            "core_tension": "The lead must survive the moved opening without losing initiative.",
            "expected_ending": "The new hall arrival settles into a controlled escalation.",
            "target_beat": "State the arrival and pivot into the next pressure move.",
            "protagonist_state": {"mood": "guarded"},
            "opening_transition": {"type": "explicit_transition"},
        },
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "Packet Hall",
                    "opening_transition_expectation": (
                        "current episode tactical start state moved from the previous ending location; "
                        "do not declare direct_continuation. "
                        "Use explicit_transition or jump_opening and state the new arrival immediately."
                    ),
                }
            }
        },
        prev_blueprint={"end_location": "Prev Blueprint Room", "time_flow": "Moments earlier"},
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "continuity" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_keeps_continuity_when_authorized_shift_location_mismatches_blueprint():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "Wrong arrival",
                    "summary": "The lead opens in an unmatched room without honoring the authorized location." * 6,
                    "location": "Wrong Room",
                }
            },
            "integrated_scenario": ("The lead opens in the wrong room despite the packet pointing elsewhere. " * 20),
            "start_location": "Wrong Room",
            "time_flow": "Later that afternoon",
            "core_tension": "The opening drifts away from the authorized location anchor.",
            "expected_ending": "The mismatch should remain visible to validation.",
            "target_beat": "Expose the mismatch.",
            "protagonist_state": {"mood": "uneasy"},
            "opening_transition": {"type": "explicit_transition"},
        },
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "Packet Hall",
                    "opening_transition_expectation": (
                        "current episode tactical start state moved from the previous ending location; "
                        "do not declare direct_continuation. "
                        "Use explicit_transition or jump_opening and state the new arrival immediately."
                    ),
                }
            }
        },
        prev_blueprint={"end_location": "Prev Blueprint Room", "time_flow": "Moments earlier"},
        state_tracker=None,
        arc_data={},
    )

    assert any(issue["category"] == "continuity" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_direct_opening_active_character_reentry():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "VIP룸 문이 다시 열린다",
                    "goal": "박성호와 함께 리스크관리팀장이 VIP룸으로 들어온다.",
                    "summary": "한시우가 전화를 끊자 박성호와 함께 리스크관리팀장이 VIP룸으로 들어온다.",
                    "characters": ["한시우", "박성호", "리스크관리팀장"],
                    "key_events": ["박성호와 함께 리스크관리팀장이 VIP룸으로 들어온다."],
                    "location": "여의도 한미증권 VIP룸",
                    "type": "opening_hook",
                },
                "scene_2": {
                    "title": "방 안 압박이 이어진다",
                    "goal": "VIP룸 안 압박이 바로 이어진다.",
                    "summary": "한시우가 VIP룸 안에서 리스크관리팀장의 압박을 받는다.",
                    "characters": ["한시우", "박성호", "리스크관리팀장"],
                    "key_events": ["VIP룸 안 압박이 끊기지 않고 이어진다."],
                    "location": "여의도 한미증권 VIP룸",
                    "type": "tension_build",
                },
            },
            "integrated_scenario": ("한시우가 전화를 끊자 박성호와 함께 리스크관리팀장이 VIP룸으로 들어온다. " * 20),
            "start_location": "여의도 한미증권 VIP룸",
            "time_flow": "그날 밤 직후",
            "core_tension": "전화를 받은 직후의 연속성을 유지해야 한다.",
            "expected_ending": "VIP룸 안의 압박이 바로 이어진다.",
            "target_beat": "direct_continuation opening을 유지한다.",
            "protagonist_state": {"mood": "guarded"},
            "opening_transition": {"type": "direct_continuation"},
        },
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "여의도 한미증권 VIP룸",
                    "active_characters": ["한시우", "박성호"],
                    "opening_transition_expectation": (
                        "same location and same-night carryover; direct_continuation is allowed if the active cast "
                        "remains on stage without re-entry."
                    ),
                }
            }
        },
        prev_blueprint={"end_location": "여의도 한미증권 VIP룸", "time_flow": "그날 밤"},
        state_tracker=None,
        arc_data={},
    )

    assert any(
        issue["category"] == "opening_transition" and "박성호" in issue["issue"] for issue in pre_result["issues"]
    )


def test_lane_c_python_pre_validate_flags_stop_line_leak_as_critical():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {"scene_1": {}, "scene_2": {}, "scene_3": {}},
            "integrated_scenario": "주인공이 정산 경매장에 잠입 계획을 실행하고 상호가 사회자 동선을 정보로 준다. "
            * 30,
        },
        constraint_block={
            "stop_line": {"content": "정산 경매장에 잠입 계획을 실행하고 상호가 사회자 동선을 정보로 준다"}
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert pre_result["has_critical"] is True
    assert any(issue["category"] == "arc_compliance" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_empty_scene_characters_as_major():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": []},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["Hero"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ""},
                "scene_4": {"goal": "g4", "summary": "s4", "characters": ["PB"]},
            },
            "integrated_scenario": "A" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    issue = next(
        issue
        for issue in pre_result["issues"]
        if issue["category"] == "scene_completeness" and "scene.characters 누락" in issue["issue"]
    )
    assert issue["severity"] == "MAJOR"
    assert "2/4" in issue["issue"]
    assert issue["missing_fields"] == ["characters"]


def test_lane_c_python_pre_validate_flags_empty_key_events_as_major_scene_completeness():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"], "key_events": []},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["PB"], "key_events": []},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero", "PB"], "key_events": ["turn"]},
                "scene_4": {"goal": "g4", "summary": "s4", "characters": ["PB"], "key_events": []},
            },
            "integrated_scenario": "A" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["issue"].startswith("scene.key_events 누락"))
    assert issue["category"] == "scene_completeness"
    assert issue["severity"] == "MAJOR"
    assert "3/4" in issue["issue"]
    assert issue["missing_fields"] == ["key_events"]


def test_lane_c_python_pre_validate_allows_two_scene_structure_floor():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                    "summary": "매수 실행",
                    "characters": ["Hero"],
                },
                "scene_2": {
                    "goal": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                    "summary": "압박 도착",
                    "characters": ["PB"],
                },
            },
            "integrated_scenario": "A" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "structure" and "씬 부족" in issue["issue"] for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_arc_timeline_drift_as_major():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["Hero"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero"]},
            },
            "integrated_scenario": "A" * 900,
            "ending_state": {
                "timeline": {"표현": "2006년 4월 중순 심야"},
            },
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 5},
                    "end": {"year": 2006, "month": 5},
                }
            }
        },
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "arc_timeline")
    assert issue["severity"] == "MAJOR"
    assert "2006년 4월 중순 심야" in issue["issue"]


def test_lane_c_parse_timeline_point_interprets_relative_month_day_markers():
    assert UnifiedBlueprintValidator._parse_timeline_point({"표현": "2006년 2월 초 오후"}, pick="end") == (2006, 2, 10)
    assert UnifiedBlueprintValidator._parse_timeline_point({"표현": "2006년 2월 초 오후"}, pick="start") == (2006, 2, 1)
    assert UnifiedBlueprintValidator._parse_timeline_point({"표현": "2006년 2월 말 심야"}, pick="end") == (2006, 2, 28)
    assert UnifiedBlueprintValidator._parse_timeline_point({"표현": "2006년 4월 중순 새벽"}, pick="end") == (
        2006,
        4,
        15,
    )


def test_lane_c_python_pre_validate_accepts_relative_month_phrase_inside_arc_window():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "episode_number": 5,
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["한시우"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["한시우"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["한시우"]},
            },
            "integrated_scenario": "A" * 900,
            "time_flow": "2006년 2월 초 오후",
            "ending_state": {
                "timeline": {"표현": "2006년 2월 초 오후"},
            },
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={
            "ep_start": 5,
            "ep_end": 9,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 2, "day": 1, "description": "2006년 2월 초, 법인 설립 마무리"},
                    "end": {
                        "year": 2006,
                        "month": 2,
                        "day": 28,
                        "description": "2006년 2월 말, 이란 핵 농축 재개 선언 직후",
                    },
                }
            },
        },
    )

    assert not any(issue["category"] == "arc_timeline" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_episode_progression_replay_as_critical():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "첫 번째 전화",
                    "goal": "법인 설립용 미팅 확보",
                    "summary": "다음 날 아침, 한시우가 자신의 방에서 변호사에게 전화를 건다.",
                    "characters": ["한시우"],
                    "key_events": ["방에서 휴대폰으로 미팅을 성사시킨다."],
                    "location": "성북동 본가, 한시우의 방",
                    "type": "opening_hook",
                },
                "scene_4": {
                    "title": "가장 비싼 좌석",
                    "goal": "아버지의 추궁에 응수한다.",
                    "summary": "서재에서 한정호와 다시 맞서며 계획을 암시한다.",
                    "characters": ["한시우", "한정호"],
                    "key_events": ["서재에서 다시 아버지와 대치한다."],
                    "location": "성북동 본가, 서재",
                    "type": "cliffhanger",
                },
            },
            "integrated_scenario": "A" * 900,
        },
        constraint_block={
            "must_focus": {"content": "광화문 로펌에서 법인 설립을 의뢰하고, PB센터에서 자산 현금화를 요청한다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "독립 선언",
                        "location": "한정호 회장의 서재",
                        "location_variants": ["한정호 회장의 서재", "서재"],
                        "characters": ["한시우", "한정호"],
                        "type": "dialogue_duel",
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "전장의 서막",
                        "location": "한시우의 방",
                        "location_variants": ["한시우의 방", "성북동 본가", "방"],
                        "characters": ["한시우"],
                        "type": "cliffhanger",
                    },
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {
                    "location": "한정호 회장의 서재",
                    "characters": ["한시우", "한정호"],
                },
                "scene_4": {
                    "location": "한시우의 방",
                    "characters": ["한시우"],
                },
            }
        },
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "episode_progression")
    assert issue["severity"] == "CRITICAL"
    assert "scene_1->scene_4" in issue["issue"] or "scene_4->scene_2" in issue["issue"]


def test_lane_c_python_pre_validate_flags_work_identity_opening_drift(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "work_guard.yaml").write_text(
        textwrap.dedent(
            """\
            work_identity:
              tracking_slots:
                - visible pressure -> execution -> public proof -> private receipt -> observer shift -> next gate
              mandatory_scene_engines:
                - first proof must lock into private receipt and next gate
            custom_rules:
              - first proof must not end at public proof only
            """
        ),
        encoding="utf-8",
    )
    context = MagicMock()
    context.current_project.paths.root = tmp_path
    validator = UnifiedBlueprintValidator(context=context, client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "ep_num": 1,
            "scene_breakdown": {
                "scene_1": {
                    "title": "Regression shock",
                    "goal": "Sort the memory flood alone in the bedroom.",
                    "summary": "He stays in the bedroom and decides to think before acting.",
                    "characters": ["Lead"],
                    "key_events": ["Lead stares at the calendar in silence."],
                    "location": "Private bedroom",
                    "type": "opening_hook",
                },
                "scene_2": {
                    "title": "Internal vow",
                    "goal": "Promise to use the knowledge later.",
                    "summary": "The lead makes a private vow but opens no outside line.",
                    "characters": ["Lead"],
                    "key_events": ["No outside observer or gate opens here."],
                    "location": "Private bedroom",
                    "type": "decision_lock",
                },
            },
            "integrated_scenario": "A" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "work_identity_opening")
    assert issue["severity"] == "MAJOR"
    assert "private receipt" in issue["issue"]


def test_lane_c_python_pre_validate_accepts_work_identity_opening_when_receipt_shift_and_next_gate_visible(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "work_guard.yaml").write_text(
        textwrap.dedent(
            """\
            work_identity:
              tracking_slots:
                - visible pressure -> execution -> public proof -> private receipt -> observer shift -> next gate
            custom_rules:
              - first proof must not end at public proof only
            """
        ),
        encoding="utf-8",
    )
    context = MagicMock()
    context.current_project.paths.root = tmp_path
    validator = UnifiedBlueprintValidator(context=context, client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "ep_num": 2,
            "scene_breakdown": {
                "scene_1": {
                    "title": "Public proof",
                    "goal": "Take the first visible execution step on the trading floor.",
                    "summary": "The market move becomes public proof in front of the PB desk.",
                    "characters": ["Lead", "PB"],
                    "key_events": ["The PB acknowledges the first proof."],
                    "location": "Trading floor",
                    "type": "execution_visible",
                },
                "scene_2": {
                    "title": "Private receipt",
                    "goal": "Lock the proof into private receipt and observer shift.",
                    "summary": "A private receipt opens an access shift and the PB tone shift becomes visible.",
                    "characters": ["Lead", "PB"],
                    "key_events": ["The PB opens a priority-response line for the lead."],
                    "location": "PB room",
                    "type": "authority_capture",
                },
                "scene_3": {
                    "title": "Next gate",
                    "goal": "Fix the next gate before the episode closes.",
                    "summary": "The next gate is a signed follow-up line and a next-cycle ticket.",
                    "characters": ["Lead", "PB"],
                    "key_events": ["The follow-up line is fixed before close."],
                    "location": "PB room",
                    "type": "next_gate_visible",
                },
            },
            "integrated_scenario": "B" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "work_identity_opening" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_work_identity_opening_drift_for_multi_location_partial_progression(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "work_guard.yaml").write_text(
        textwrap.dedent(
            """\
            work_identity:
              tracking_slots:
                - visible pressure -> execution -> public proof -> private receipt -> observer shift -> next gate
              mandatory_scene_engines:
                - first proof must lock into private receipt and next gate
            custom_rules:
              - first proof must not end at public proof only
            """
        ),
        encoding="utf-8",
    )
    context = MagicMock()
    context.current_project.paths.root = tmp_path
    validator = UnifiedBlueprintValidator(context=context, client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "ep_num": 4,
            "scene_breakdown": {
                "scene_1": {
                    "title": "Hallway pressure",
                    "goal": "Move fast after the previous ending.",
                    "summary": "Public proof starts in the hallway.",
                    "characters": ["Lead", "PB"],
                    "key_events": ["The lead pushes the first move into the open."],
                    "location": "Hallway",
                    "type": "execution_visible",
                },
                "scene_2": {
                    "title": "VIP room paperwork",
                    "goal": "Secure private receipt language without a real observer shift.",
                    "summary": "A private receipt is mentioned, but the PB does not reevaluate the lead.",
                    "characters": ["Lead", "PB"],
                    "key_events": ["The paperwork stays procedural and no observer shift lands."],
                    "location": "VIP room",
                    "type": "dialogue_duel",
                },
                "scene_3": {
                    "title": "Temporary office setup",
                    "goal": "Keep moving without locking a visible next gate.",
                    "summary": "The setup keeps moving, but no signboard or next-cycle ticket is fixed.",
                    "characters": ["Lead"],
                    "key_events": ["The route changes again without locking the authority ladder."],
                    "location": "Temporary office",
                    "type": "setup_motion",
                },
            },
            "integrated_scenario": "C" * 900,
        },
        constraint_block={},
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "work_identity_opening")
    assert issue["severity"] == "MAJOR"
    assert "next gate" in issue["issue"]


def test_lane_c_python_pre_validate_allows_authorized_scene1_anchor_shift_without_replay_false_positive():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "explicit_transition"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "Cut to the packet hall",
                    "goal": "Open on the new packet-authorized location.",
                    "summary": "An explicit transition moves the opening into Packet Hall.",
                    "characters": ["lead", "pb"],
                    "key_events": ["The opening anchor is deliberately shifted."],
                    "location": "Packet Hall",
                    "type": "opening_hook",
                },
                "scene_2": {
                    "title": "Desk confirmation",
                    "goal": "Confirm the same PB line one more time.",
                    "summary": "The lead and PB reuse the same office pressure beat.",
                    "characters": ["lead", "pb"],
                    "key_events": ["The same office pressure beat returns."],
                    "location": "PB Office",
                    "type": "decision_lock",
                },
            },
            "integrated_scenario": "C" * 900,
        },
        constraint_block={
            "must_focus": {"content": "Move the opening to Packet Hall and then confirm the office line."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_4",
                        "label": "old hall pressure",
                        "location": "Packet Hall",
                        "location_variants": ["Packet Hall"],
                        "characters": ["lead", "pb"],
                        "type": "dialogue_duel",
                    },
                    {
                        "scene_key": "scene_5",
                        "label": "office pressure",
                        "location": "PB Office",
                        "location_variants": ["PB Office"],
                        "characters": ["lead", "pb"],
                        "type": "decision_lock",
                    },
                ]
            },
            "episode_state_packet": {
                "opening_truth": {
                    "opening_transition_expectation": (
                        "This arc opening moved from Prev Blueprint Room to Packet Hall; "
                        "do not declare direct_continuation. Use explicit_transition."
                    )
                }
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_4": {"location": "Packet Hall", "characters": ["lead", "pb"]},
                "scene_5": {"location": "PB Office", "characters": ["lead", "pb"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_allows_authorized_scene1_time_cut_without_replay_false_positive():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "jump_opening"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "2주 뒤의 재입장",
                    "goal": "같은 VIP룸이라도 2주 뒤 새 압박 국면에 진입한다.",
                    "summary": "한시우가 4월 중순의 VIP룸에서 다시 압박을 받는다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["4월 중순으로 점프한 opening time cut을 먼저 선언한다."],
                    "location": "한미증권 VIP룸",
                    "type": "opening_hook",
                },
                "scene_2": {
                    "title": "버티기 압박",
                    "goal": "같은 방에서 익절 압박을 받는다.",
                    "summary": "박성호가 익절 압박을 건네지만 한시우는 아직 버틴다고 말한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["박성호가 익절 압박을 전달한다."],
                    "location": "한미증권 VIP룸",
                    "type": "tension_build",
                },
            },
            "integrated_scenario": "D" * 900,
        },
        constraint_block={
            "must_focus": {"content": "약 2주 후, 같은 VIP룸에서 박성호의 익절 압박을 받되 아직 버틴다고 단언한다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_3",
                        "label": "직통 라인 확보",
                        "location": "한미증권 VIP룸",
                        "location_variants": ["한미증권 VIP룸", "VIP룸"],
                        "characters": ["한시우", "박성호"],
                        "type": "authority_capture",
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "다음 타깃 포착",
                        "location": "한미증권 VIP룸",
                        "location_variants": ["한미증권 VIP룸", "VIP룸"],
                        "characters": ["한시우", "박성호"],
                        "type": "cliffhanger",
                    },
                ]
            },
            "episode_state_packet": {
                "opening_truth": {
                    "opening_transition_expectation": (
                        "opening time jumped beyond the previous ending time while reusing the same anchor; "
                        "do not declare direct_continuation. "
                        "Use explicit_transition or jump_opening and state the time cut immediately."
                    )
                }
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {"location": "한미증권 VIP룸", "characters": ["한시우", "박성호"]},
                "scene_4": {"location": "한미증권 VIP룸", "characters": ["한시우", "박성호"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_direct_opening_single_replay_family():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "direct_continuation"},
            "start_location": "한미증권 VIP룸",
            "time_flow": "그날 밤 직후",
            "core_tension": "새 압박으로 전진해야 한다.",
            "expected_ending": "새 결정으로 이어진다.",
            "target_beat": "직전 화 장면 반복을 피하고 전진해야 한다.",
            "scene_breakdown": {
                "scene_1": {
                    "title": "같은 VIP룸에서 같은 압박을 다시 시작한다",
                    "goal": "직전 화에서 끝난 VIP룸 압박 장면을 그대로 다시 반복한다.",
                    "summary": "한시우와 박성호가 같은 VIP룸에서 같은 압박을 다시 주고받는다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["VIP룸 압박 장면을 다시 반복한다."],
                    "location": "한미증권 VIP룸",
                    "type": "dialogue_duel",
                },
                "scene_2": {
                    "title": "압박을 한 번 더 되풀이한다",
                    "goal": "새 사건 없이 같은 압박을 되풀이한다.",
                    "summary": "같은 정보와 같은 결정을 다시 주고받는다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["같은 압박을 되풀이한다."],
                    "location": "한미증권 VIP룸",
                    "type": "dialogue_duel",
                },
            },
            "integrated_scenario": "같은 VIP룸 압박을 다시 반복한다. " * 40,
            "protagonist_state": {"mood": "rigid"},
        },
        constraint_block={
            "must_focus": {"content": "새로운 외부 압박과 다음 결정을 전진시켜야 한다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_4",
                        "label": "VIP룸 압박",
                        "location": "한미증권 VIP룸",
                        "location_variants": ["한미증권 VIP룸", "VIP룸"],
                        "characters": ["한시우", "박성호"],
                        "type": "dialogue_duel",
                    }
                ]
            },
            "episode_state_packet": {
                "opening_truth": {
                    "opening_transition_expectation": "same-room carryover; direct_continuation only if the scene advances.",
                }
            },
        },
        prev_blueprint={
            "end_location": "한미증권 VIP룸",
            "time_flow": "그날 밤",
            "scene_breakdown": {
                "scene_4": {"location": "한미증권 VIP룸", "characters": ["한시우", "박성호"]},
            },
        },
        state_tracker=None,
        arc_data={},
    )

    assert any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_flags_completed_prior_event_replay_in_scene_1():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "direct_continuation"},
            "start_location": "한정호 회장의 서재",
            "time_flow": "직후",
            "core_tension": "독립 선언 이후의 후폭풍으로 전진해야 한다.",
            "expected_ending": "새 외부 변수로 이어진다.",
            "target_beat": "완료된 아버지 자금 지원 연락처 수령을 반복하지 않는다.",
            "scene_breakdown": {
                "scene_1": {
                    "title": "아버지 연락처를 다시 받는다",
                    "goal": "한시우가 아버지 앞에서 자금 지원 연락처를 다시 받아 챙긴다.",
                    "summary": "직전 화에서 끝난 독립 선언과 아버지 자금 지원 연락처 수령을 다시 재연한다.",
                    "characters": ["한시우", "한정호"],
                    "key_events": ["아버지 자금 지원 연락처를 다시 받아 챙긴다."],
                    "location": "한정호 회장의 서재",
                    "type": "dialogue_duel",
                }
            },
            "integrated_scenario": "아버지 자금 지원 연락처를 다시 받아 챙긴다. " * 40,
        },
        constraint_block={
            "must_focus": {"content": "독립 선언 이후 외부 자금 라인과 새 법인 설립으로 전진해야 한다."},
            "episode_progression_packet": {
                "completed_prior_events": [
                    {
                        "location": "한정호 회장의 서재",
                        "events": ["한시우가 독립 선언을 마친다.", "아버지 자금 지원 연락처를 받아 챙긴다."],
                    }
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {
                    "location": "한정호 회장의 서재",
                    "characters": ["한시우", "한정호"],
                }
            }
        },
        state_tracker=None,
        arc_data={},
    )

    episode_issues = [issue for issue in pre_result["issues"] if issue["category"] == "episode_progression"]

    assert episode_issues
    assert "이미 완료된 사건" in episode_issues[0]["issue"]
    assert "completed_event_replays" in episode_issues[0]["evidence"]


def test_lane_c_python_pre_validate_allows_parent_location_shift_to_new_room():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "direct_continuation"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "호출",
                    "goal": "아버지의 부름에 응하여 서재로 향한다.",
                    "summary": "가정부의 안내에 따라 한시우가 거실에서 서재로 가는 복도를 지난다.",
                    "characters": ["한시우", "가정부"],
                    "key_events": ["한시우가 2층 서재로 이동한다."],
                    "location": "성북동 본가, 거실에서 서재로 가는 복도",
                    "type": "tension_build",
                },
                "scene_2": {
                    "title": "선언",
                    "goal": "가족들 앞에서 독립 투자 법인 설립을 선언한다.",
                    "summary": "한시우가 서재에서 한정호와 형들 앞에 선다.",
                    "characters": ["한시우", "한정호"],
                    "key_events": ["독립 투자 법인 설립 의사를 밝힌다."],
                    "location": "성북동 본가, 서재",
                    "type": "dialogue_duel",
                },
            },
            "integrated_scenario": "가정부의 안내에 따라 복도를 지나 서재에 들어선다. " * 40,
        },
        constraint_block={
            "must_focus": {
                "content": "아버지 한정호 회장의 서재로 호출된다. 가족들 앞에서 독립 투자 법인 설립을 선언한다."
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "한시우의 방",
                        "location": "성북동 본가, 한시우의 방",
                        "location_variants": ["성북동 본가, 한시우의 방", "한시우의 방"],
                        "characters": ["한시우"],
                    },
                    {
                        "scene_key": "scene_3",
                        "label": "거실 TV 확인",
                        "location": "성북동 본가, 거실",
                        "location_variants": ["성북동 본가, 거실", "거실"],
                        "characters": ["한시우"],
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "가정부 호출",
                        "location": "성북동 본가, 거실",
                        "location_variants": ["성북동 본가, 거실", "거실"],
                        "characters": ["한시우", "가정부"],
                    },
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "성북동 본가, 한시우의 방", "characters": ["한시우"]},
                "scene_3": {"location": "성북동 본가, 거실", "characters": ["한시우"]},
                "scene_4": {"location": "성북동 본가, 거실", "characters": ["한시우", "가정부"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not [issue for issue in pre_result["issues"] if issue["category"] == "episode_progression"]


def test_lane_c_python_pre_validate_does_not_match_household_parent_variants_as_replay():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "jump_opening"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "서재 요청",
                    "goal": "한시우가 아버지 한정호에게 서재 대화를 요청한다.",
                    "summary": "거실에서 TV를 끈 한시우가 한정호에게 서재에서 따로 이야기하자고 말한다.",
                    "characters": ["한시우", "한정호"],
                    "key_events": ["한시우가 한정호에게 서재 면담을 요청한다."],
                    "location": "성북동 본가, 거실",
                    "type": "opening_hook",
                },
                "scene_2": {
                    "title": "독립 선언",
                    "goal": "아버지 앞에서 독립 투자 법인 설립을 선언한다.",
                    "summary": "한정호의 서재에서 한시우가 그룹 승계 포기와 독립 투자 사업을 선언한다.",
                    "characters": ["한시우", "한정호", "한태준", "한태민"],
                    "key_events": ["독립 투자 사업 선언이 서재에서 이뤄진다."],
                    "location": "성북동 본가, 한정호의 서재",
                    "type": "dialogue_duel",
                },
            },
            "integrated_scenario": "거실에서 서재로 이동해 독립 투자 사업을 선언한다. " * 40,
        },
        constraint_block={
            "must_focus": {"content": "아버지 한정호의 서재에서 독립을 선언"},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "한시우의 방",
                        "location": "성북동 본가, 한시우의 방",
                        "location_variants": ["성북동 본가, 한시우의 방", "한시우의 방", "성북동 본가"],
                        "characters": ["한시우"],
                    },
                    {
                        "scene_key": "scene_3",
                        "label": "가족 식사",
                        "location": "성북동 본가, 다이닝 룸",
                        "location_variants": ["성북동 본가, 다이닝 룸", "다이닝 룸", "성북동 본가"],
                        "characters": ["한시우", "한정호", "한태준", "한태민"],
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "거실 뉴스",
                        "location": "성북동 본가, 거실",
                        "location_variants": ["성북동 본가, 거실", "거실", "성북동 본가"],
                        "characters": ["한시우"],
                    },
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "성북동 본가, 한시우의 방", "characters": ["한시우"]},
                "scene_3": {
                    "location": "성북동 본가, 다이닝 룸",
                    "characters": ["한시우", "한정호", "한태준", "한태민"],
                },
                "scene_4": {"location": "성북동 본가, 거실", "characters": ["한시우"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not [issue for issue in pre_result["issues"] if issue["category"] == "episode_progression"]


def test_lane_c_python_pre_validate_ignores_weak_completed_event_overlap_for_new_action():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "direct_continuation"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "서재로 향하는 호출",
                    "goal": "한시우가 아버지 한정호의 서재로 향해 독립 투자 사업 선언을 준비한다.",
                    "summary": "가정부의 호출을 받은 한시우가 거실을 떠나 서재 앞 복도로 이동한다.",
                    "characters": ["한시우", "가정부"],
                    "key_events": [
                        "한시우가 거실에서 일어나 2층 서재로 향한다.",
                        "한시우는 독립 투자 사업을 선언할 문장을 정리한다.",
                    ],
                    "location": "성북동 본가, 거실에서 서재로 가는 복도",
                    "type": "tension_build",
                }
            },
            "integrated_scenario": "가정부의 호출을 받은 한시우가 거실을 떠나 서재로 향한다. " * 40,
        },
        constraint_block={
            "must_focus": {"content": "아버지 한정호의 서재로 가 독립 투자 사업을 선언한다."},
            "episode_progression_packet": {
                "completed_prior_events": [
                    {
                        "location": "성북동 본가, 거실",
                        "events": ["가정부가 한시우에게 아버지 한정호가 찾는다고 말한다."],
                    }
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_4": {"location": "성북동 본가, 거실", "characters": ["한시우", "가정부"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not [issue for issue in pre_result["issues"] if issue["category"] == "episode_progression"]


def test_lane_c_python_pre_validate_ignores_weak_pb_hallway_overlap_for_asset_forward_motion():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "opening_transition": {"type": "direct_continuation"},
            "scene_breakdown": {
                "scene_1": {
                    "title": "현관을 나서며",
                    "goal": "한시우가 PB를 통해 개인 자산 현금화를 실행하기 위해 움직인다.",
                    "summary": "성북동 본가 현관에서 경호원을 지나친 한시우는 곧바로 PB센터에 연락해 자신의 개인 자산 정리를 지시한다.",
                    "characters": ["한시우", "경호원"],
                    "key_events": [
                        "한시우가 현관을 지나 PB센터에 연락한다.",
                        "한시우가 개인 자산 현금화 절차를 시작한다.",
                    ],
                    "location": "성북동 본가 현관",
                    "type": "opening_hook",
                }
            },
            "integrated_scenario": "현관을 지나 PB센터에 연락해 개인 자산 현금화를 시작한다. " * 40,
        },
        constraint_block={
            "must_focus": {"content": "PB를 통해 과거 자신의 모든 개인 자산을 현금화."},
            "episode_progression_packet": {
                "completed_prior_events": [
                    {
                        "location": "성북동 본가 현관",
                        "events": ["한시우가 경호원 앞에서 자신이 곧바로 나가겠다고 말한다."],
                    }
                ]
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {"location": "성북동 본가 현관", "characters": ["한시우", "경호원"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not [issue for issue in pre_result["issues"] if issue["category"] == "episode_progression"]


def test_lane_c_python_pre_validate_allows_lawful_repetition_when_goal_escalates():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "패닉콜을 받다",
                    "goal": "박성호의 패닉콜에 응답하며 유가는 80달러까지 간다고 단언한다.",
                    "summary": "여의도 본점 PB실에서 같은 핫라인 전화를 받지만 이번에는 하락장을 버티라는 결정이 핵심이다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["직통 핫라인으로 유가 80달러 전망을 단언한다."],
                    "location": "여의도 본점 PB실",
                    "type": "authority_escalation",
                },
                "scene_2": {
                    "title": "리스크팀을 압박하다",
                    "goal": "같은 본점에서 리스크팀을 눌러 다음 조치를 막는다.",
                    "summary": "박성호가 연결한 본점 라인으로 버티기 결정을 고정한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["같은 채널에서 결정을 확정한다."],
                    "location": "여의도 본점 PB실",
                    "type": "decision_lock",
                },
            },
            "integrated_scenario": "B" * 900,
        },
        constraint_block={
            "must_focus": {
                "content": "WTI가 68달러까지 조정받는 와중에도 박성호 패닉콜을 받고 유가는 80달러까지 간다고 단언한다."
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_3",
                        "label": "핫라인 압박",
                        "location": "여의도 본점 PB실",
                        "location_variants": ["여의도 본점 PB실", "여의도 본점", "PB실"],
                        "characters": ["한시우", "박성호"],
                        "type": "phone_pressure",
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "본점 설득",
                        "location": "여의도 본점 PB실",
                        "location_variants": ["여의도 본점 PB실", "여의도 본점", "PB실"],
                        "characters": ["한시우", "박성호"],
                        "type": "dialogue_duel",
                    },
                ],
                "lawful_repetition_window": {
                    "mode": "allow_escalated_repeat",
                    "allow_same_location_if_goal_changes": True,
                    "allow_same_counterparty_if_goal_changes": True,
                    "allow_same_channel_if_decision_escalates": True,
                    "escalation_tokens": ["단언", "압박", "조정"],
                },
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {
                    "location": "여의도 본점 PB실",
                    "characters": ["한시우", "박성호"],
                },
                "scene_4": {
                    "location": "여의도 본점 PB실",
                    "characters": ["한시우", "박성호"],
                },
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_allows_lawful_repetition_when_authority_capture_escalates():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "직통 명함 전달",
                    "goal": "같은 VIP룸에서 박성호가 전담 라인과 직통 명함을 건네며 권한 역전을 확정한다.",
                    "summary": "한미증권 본점 VIP룸에서 박성호가 경외심 속에 전담 라인 개설과 직통 핫라인 명함 전달을 보고한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["박성호가 전담 VIP 라인 개설과 직통 명함 획득을 보고한다."],
                    "location": "한미증권 본점 VIP룸",
                    "type": "authority_capture",
                },
                "scene_2": {
                    "title": "권한 역전 확인",
                    "goal": "같은 방에서 관계 역전을 확인하고 다음 지시 체계를 고정한다.",
                    "summary": "박성호가 경외심 속에 같은 공간에서 보고선 변경을 수용한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["박성호가 앞으로 한시우의 직통 전담 채널을 최우선으로 두겠다고 확인한다."],
                    "location": "한미증권 본점 VIP룸",
                    "type": "relationship_shift",
                },
            },
            "integrated_scenario": "C" * 900,
        },
        constraint_block={
            "must_focus": {
                "content": "박성호 PB의 태도 돌변과 경외, 전담 VIP 라인 개설, 직통 핫라인 명함 획득을 통해 권한 역전을 확정한다."
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_3",
                        "label": "수익 확인 전화",
                        "location": "한미증권 본점 VIP룸",
                        "location_variants": ["한미증권 본점 VIP룸", "VIP룸", "한미증권 본점"],
                        "characters": ["한시우", "박성호"],
                        "type": "dialogue_duel",
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "수익 보고",
                        "location": "한미증권 본점 VIP룸",
                        "location_variants": ["한미증권 본점 VIP룸", "VIP룸", "한미증권 본점"],
                        "characters": ["한시우", "박성호"],
                        "type": "tension_build",
                    },
                ],
                "lawful_repetition_window": {
                    "mode": "allow_escalated_repeat",
                    "allow_same_location_if_goal_changes": True,
                    "allow_same_counterparty_if_goal_changes": True,
                    "allow_same_channel_if_decision_escalates": True,
                    "escalation_tokens": ["전담", "직통", "명함", "경외", "격상"],
                },
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {
                    "location": "한미증권 본점 VIP룸",
                    "characters": ["한시우", "박성호"],
                },
                "scene_4": {
                    "location": "한미증권 본점 VIP룸",
                    "characters": ["한시우", "박성호"],
                },
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_allows_lawful_repetition_when_execution_rotates_same_room():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "원유 전량 청산",
                    "goal": "같은 VIP 상담실에서 남은 원유 롱 포지션을 전량 청산한다.",
                    "summary": "한시우가 같은 방에서 남은 원유 포지션을 정리하며 자금을 확보한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["남은 원유 롱 포지션을 전량 청산한다.", "청산 확인서를 회수한다."],
                    "location": "서울 강남, SW인베스트먼트 VIP 상담실",
                    "type": "execution_rotation",
                },
                "scene_2": {
                    "title": "금 선물 체결",
                    "goal": "같은 방에서 확보 자금으로 금 선물 15억 원 매수에 즉시 진입한다.",
                    "summary": "예외 계좌 권한으로 즉각 체결을 밀어붙인다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["금 선물 15억 원 매수 주문을 넣는다.", "체결 확인서를 받는다."],
                    "location": "서울 강남, SW인베스트먼트 VIP 상담실",
                    "type": "execution_lock",
                },
            },
            "integrated_scenario": "E" * 900,
        },
        constraint_block={
            "must_focus": {
                "content": (
                    "예외 계좌 승인 직후 남은 원유 롱 포지션을 전량 청산하고 "
                    "확보된 자금 15억 원으로 금 선물 레버리지 매수에 즉시 진입한다."
                )
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_3",
                        "label": "예외 계좌 승인",
                        "location": "서울 강남, SW인베스트먼트 VIP 상담실",
                        "location_variants": ["서울 강남, SW인베스트먼트 VIP 상담실", "VIP 상담실"],
                        "characters": ["한시우", "박성호"],
                        "type": "authority_capture",
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "승인 문서 수령",
                        "location": "서울 강남, SW인베스트먼트 VIP 상담실",
                        "location_variants": ["서울 강남, SW인베스트먼트 VIP 상담실", "VIP 상담실"],
                        "characters": ["한시우", "박성호"],
                        "type": "relationship_shift",
                    },
                ],
                "lawful_repetition_window": {
                    "mode": "allow_escalated_repeat",
                    "allow_same_location_if_goal_changes": True,
                    "allow_same_counterparty_if_goal_changes": True,
                    "allow_same_channel_if_decision_escalates": True,
                    "escalation_tokens": ["청산", "매수", "진입", "체결"],
                },
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_3": {"location": "서울 강남, SW인베스트먼트 VIP 상담실", "characters": ["한시우", "박성호"]},
                "scene_4": {"location": "서울 강남, SW인베스트먼트 VIP 상담실", "characters": ["한시우", "박성호"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_allows_post_execution_monitoring_same_room():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {
                    "title": "시장 관망",
                    "goal": "같은 VIP룸에서 시장 추이를 관망하며 보유 유지 이유를 정리한다.",
                    "summary": "박성호는 초조해하고 한시우는 평온을 유지한 채 포지션을 계속 들고 간다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["박성호가 초조하게 반응한다.", "한시우가 관망과 보유 유지를 선언한다."],
                    "location": "여의도 한미증권 VIP룸",
                    "type": "market_watch",
                },
                "scene_2": {
                    "title": "압박 유지",
                    "goal": "같은 방에서 압박의 수위 변화와 심리 비대칭을 드러낸다.",
                    "summary": "재주문은 없지만 박성호의 불안과 한시우의 평온이 정면충돌한다.",
                    "characters": ["한시우", "박성호"],
                    "key_events": ["익절 압박이 거세지지만 한시우는 아직 버틴다."],
                    "location": "여의도 한미증권 VIP룸",
                    "type": "pressure_hold",
                },
            },
            "integrated_scenario": "F" * 900,
        },
        constraint_block={
            "must_focus": {
                "content": "투자 집행 후 같은 VIP룸에서 박성호는 초조해하고 한시우는 평온을 유지하며 시장을 관망한다."
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "주문 대치",
                        "location": "여의도 한미증권 VIP룸",
                        "location_variants": ["여의도 한미증권 VIP룸", "VIP룸"],
                        "characters": ["한시우", "박성호"],
                        "type": "dialogue_duel",
                    },
                    {
                        "scene_key": "scene_3",
                        "label": "주문 체결",
                        "location": "여의도 한미증권 VIP룸",
                        "location_variants": ["여의도 한미증권 VIP룸", "VIP룸"],
                        "characters": ["한시우", "박성호"],
                        "type": "execution_lock",
                    },
                ],
                "lawful_repetition_window": {
                    "mode": "allow_escalated_repeat",
                    "allow_same_location_if_goal_changes": True,
                    "allow_same_counterparty_if_goal_changes": True,
                    "allow_same_channel_if_decision_escalates": True,
                    "escalation_tokens": ["초조", "평온", "유지", "관망"],
                },
            },
        },
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "여의도 한미증권 VIP룸", "characters": ["한시우", "박성호"]},
                "scene_3": {"location": "여의도 한미증권 VIP룸", "characters": ["한시우", "박성호"]},
            }
        },
        state_tracker=None,
        arc_data={},
    )

    assert not any(issue["category"] == "episode_progression" for issue in pre_result["issues"])


def test_lane_c_build_director_validation_result_escalates_binding_issue_to_pass_with_fix():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MAJOR",
                    "category": "scene_completeness",
                    "issue": "scene.characters 누락: 4/4개 씬에서 characters가 비어 있음",
                    "fix_hint": "fill characters",
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 78,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["verdict"] == "PASS_WITH_FIX"
    assert result["director_verdict"] == "PASS"
    assert result["runtime_route_verdict"] == "PASS_WITH_FIX"
    assert result["runtime_gate_basis"] == "binding_prevalidation_contract"
    assert result["runtime_route_action"] == "regenerate_required"
    assert result["final_judgment_authority"] == "director_llm"
    assert result["runtime_gate_authority"] == "python_runtime_routing_gate"
    assert result["revision_required"] is True
    assert result["fix_scope"] == "full"
    assert "regenerate-only repair" in result["fix_scope_reasoning"]
    assert result["binding_prevalidation_issue_count"] == 1
    assert result["binding_prevalidation_categories"] == ["scene_completeness"]
    assert result["binding_regenerate_only_categories"] == ["scene_completeness"]
    assert "scene_completeness" in result["binding_regenerate_only_reason"]
    assert "[Binding prevalidation]" in result["feedback"]


def test_lane_c_build_director_validation_result_escalates_missing_key_events_to_full_regenerate():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MAJOR",
                    "category": "scene_completeness",
                    "issue": "scene.key_events 누락: 4/4개 씬에서 key_events가 비어 있음",
                    "fix_hint": "fill key_events",
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 79,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_categories"] == ["scene_completeness"]
    assert "regenerate-only repair" in result["fix_scope_reasoning"]
    assert result["binding_regenerate_only_categories"] == ["scene_completeness"]


def test_lane_c_build_director_validation_result_escalates_opening_anchor_to_full_regenerate():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MAJOR",
                    "category": "opening_anchor",
                    "issue": "opening contract anchor missing: scene_1.title",
                    "fix_hint": "scene_1 title and opening anchor를 복원",
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 80,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_categories"] == ["opening_anchor"]
    assert result["binding_regenerate_only_categories"] == ["opening_anchor"]
    assert "opening_anchor" in result["fix_scope_reasoning"]


def test_lane_c_build_director_validation_result_escalates_episode_progression_to_full_regenerate():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "CRITICAL",
                    "category": "episode_progression",
                    "issue": "직전 화에서 이미 소비한 scene family를 이번 화에서 다시 재연함",
                    "fix_hint": "현재 화 MUST_FOCUS의 새 사건 축으로 전진",
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 83,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_categories"] == ["episode_progression"]
    assert result["binding_regenerate_only_categories"] == ["episode_progression"]
    assert "episode_progression" in result["fix_scope_reasoning"]


def test_lane_c_build_director_validation_result_escalates_dead_npc_and_fact_lock_binding_categories():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "CRITICAL",
                    "category": "dead_npc",
                    "issue": "죽은 NPC 등장: 흑풍",
                    "fix_hint": "죽은 NPC는 회상/언급만 허용",
                },
                {
                    "severity": "MAJOR",
                    "category": "fact_lock_location",
                    "issue": "위치 사실잠금 위반: 확정 위치 '북문' -> blueprint 시작 '남문'",
                    "fix_hint": "이전 화 종료 위치에서 시작하거나 이동 경위를 명시",
                },
                {
                    "severity": "CRITICAL",
                    "category": "arc_compliance",
                    "issue": "정지선 위반: 다음 화 내용 포함",
                    "fix_hint": "이번 화 범위 내에서만 작성",
                },
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 84,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["binding_prevalidation_issue_count"] == 3
    assert result["binding_prevalidation_categories"] == [
        "dead_npc",
        "fact_lock_location",
        "arc_compliance",
    ]


def test_lane_c_python_pre_validate_flags_capital_unit_drift_as_major():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["PB"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero", "PB"]},
            },
            "integrated_scenario": (
                "한시우는 WTI 익절로 확보한 500만 달러를 추가 증거금으로 즉각 투입한다. " + "A" * 900
            ),
        },
        constraint_block={
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "15억 원 (투입/체결 완료 — 가용 아님)"},
                    {"label": "보유 자본", "value": "20억 원 (예치/보유 상태)"},
                ]
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    issue = next(issue for issue in pre_result["issues"] if issue["category"] == "capital_unit")
    assert issue["severity"] == "MAJOR"
    assert "500만 달러" in issue["issue"]


def test_lane_c_python_pre_validate_skips_price_only_dollar_mentions_for_capital_unit():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["PB"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero", "PB"]},
            },
            "integrated_scenario": ("그해 8월 8일 FOMC 이후 금값은 온스당 700달러를 향해 폭등했다. " + "A" * 900),
        },
        constraint_block={
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "15억 원 (투입/체결 완료 — 가용 아님)"},
                    {"label": "보유 자본", "value": "20억 원 (예치/보유 상태)"},
                ]
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert all(issue["category"] != "capital_unit" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_skips_wti_price_drop_mentions_for_capital_unit():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["PB"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero", "PB"]},
            },
            "integrated_scenario": (
                "WTI 6월물 호가창이 무너지고 유가는 68달러 선을 붕괴한다. "
                "박성호는 포지션을 정리하자고 애원하지만, 한시우는 80달러까지 간다고 단언한다. " + "A" * 900
            ),
        },
        constraint_block={
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "15억 원 (투입/체결 완료 — 가용 아님)"},
                    {"label": "보유 자본", "value": "20억 원 (예치/보유 상태)"},
                ]
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert all(issue["category"] != "capital_unit" for issue in pre_result["issues"])


def test_lane_c_python_pre_validate_skips_oil_price_rally_mentions_for_capital_unit():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    pre_result = validator._python_pre_validate(
        blueprint={
            "scene_breakdown": {
                "scene_1": {"goal": "g1", "summary": "s1", "characters": ["Hero"]},
                "scene_2": {"goal": "g2", "summary": "s2", "characters": ["PB"]},
                "scene_3": {"goal": "g3", "summary": "s3", "characters": ["Hero", "PB"]},
            },
            "integrated_scenario": (
                "유가가 75달러를 향해 수직 상승하기 시작하자 시장 전체가 패닉 바잉에 빠졌다. "
                "모두가 매수 버튼을 누르는 바로 그 순간 한시우는 절반 익절만 지시했다. " + "A" * 900
            ),
        },
        constraint_block={
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "15억 원 (투입/체결 완료 — 가용 아님)"},
                    {"label": "보유 자본", "value": "20억 원 (예치/보유 상태)"},
                ]
            }
        },
        prev_blueprint=None,
        state_tracker=None,
        arc_data={},
    )

    assert all(issue["category"] != "capital_unit" for issue in pre_result["issues"])


def test_lane_c_build_director_validation_result_escalates_capital_unit_issue_to_pass_with_fix():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {}

    verdict, result = validator._build_director_validation_result(
        blueprint=blueprint,
        pre_result={
            "issues": [
                {
                    "severity": "MAJOR",
                    "category": "capital_unit",
                    "issue": "자본 단위 불일치: KRW 기준 arc/state에 USD 투입 금액 '500만 달러' 등장",
                    "fix_hint": "capital packet 기준 단위를 유지할 것",
                }
            ]
        },
        director_result={
            "decision": "PASS",
            "reason": "narrative quality okay",
            "feedback": "",
            "score": 81,
        },
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["verdict"] == "PASS_WITH_FIX"
    assert result["director_verdict"] == "PASS"
    assert result["runtime_route_verdict"] == "PASS_WITH_FIX"
    assert result["runtime_gate_basis"] == "binding_prevalidation_contract"
    assert result["runtime_route_action"] == "regenerate_required"
    assert result["revision_required"] is True
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_issue_count"] == 1
    assert result["binding_prevalidation_categories"] == ["capital_unit"]
    assert result["binding_regenerate_only_categories"] == ["capital_unit"]
    assert "capital_unit" in result["fix_scope_reasoning"]
    assert "[Binding prevalidation]" in result["feedback"]


def test_lane_c_run_compare_validation_escalates_binding_issue_to_pass_with_fix():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    candidates = [{"name": "alpha"}, {"name": "beta"}]
    validator._prepare_compare_candidate = Mock(
        side_effect=[
            (
                {
                    "issues": [
                        {
                            "severity": "MAJOR",
                            "category": "arc_timeline",
                            "issue": "ending_state.timeline 불일치",
                        }
                    ],
                    "has_critical": False,
                },
                {"candidate_index": 0, "quality_risk": True},
            ),
            ({"issues": [], "has_critical": False}, {"candidate_index": 1, "quality_risk": False}),
        ]
    )
    director = SimpleNamespace(
        compare_and_select_blueprint=Mock(
            return_value={
                "decision": "PASS",
                "selected_index": 0,
                "selected_blueprint": None,
                "score": 82,
                "selection_reason": "best candidate",
                "comparison_notes": "note",
                "quality_risk": False,
                "revision_required": False,
            }
        )
    )

    verdict, result = validator._run_compare_validation(
        all_candidates=candidates,
        arc_data={"arc_no": 4},
        constraint_block={},
        prev_blueprint=None,
        director=director,
        entity_registry=None,
        state_tracker=None,
        working_ep=15,
        arc_idx=4,
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["verdict"] == "PASS_WITH_FIX"
    assert result["revision_required"] is True
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_issue_count"] == 1
    assert result["binding_prevalidation_categories"] == ["arc_timeline"]
    assert result["binding_regenerate_only_categories"] == ["arc_timeline"]
    assert "arc_timeline" in result["fix_scope_reasoning"]
    assert "[Binding prevalidation]" in result["feedback"]


def test_lane_c_run_compare_validation_escalates_capital_unit_issue_to_pass_with_fix():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    candidates = [{"name": "alpha"}, {"name": "beta"}]
    validator._prepare_compare_candidate = Mock(
        side_effect=[
            (
                {
                    "issues": [
                        {
                            "severity": "MAJOR",
                            "category": "capital_unit",
                            "issue": "자본 단위 불일치: KRW 기준 arc/state에 USD 투입 금액 '500만 달러' 등장",
                        }
                    ],
                    "has_critical": False,
                },
                {"candidate_index": 0, "quality_risk": True},
            ),
            ({"issues": [], "has_critical": False}, {"candidate_index": 1, "quality_risk": False}),
        ]
    )
    director = SimpleNamespace(
        compare_and_select_blueprint=Mock(
            return_value={
                "decision": "PASS",
                "selected_index": 0,
                "selected_blueprint": None,
                "score": 84,
                "selection_reason": "best candidate",
                "comparison_notes": "note",
                "quality_risk": False,
                "revision_required": False,
            }
        )
    )

    verdict, result = validator._run_compare_validation(
        all_candidates=candidates,
        arc_data={"arc_no": 4},
        constraint_block={},
        prev_blueprint=None,
        director=director,
        entity_registry=None,
        state_tracker=None,
        working_ep=17,
        arc_idx=4,
    )

    assert verdict == "PASS_WITH_FIX"
    assert result["verdict"] == "PASS_WITH_FIX"
    assert result["revision_required"] is True
    assert result["fix_scope"] == "full"
    assert result["binding_prevalidation_issue_count"] == 1
    assert result["binding_prevalidation_categories"] == ["capital_unit"]
    assert result["binding_regenerate_only_categories"] == ["capital_unit"]
    assert "capital_unit" in result["fix_scope_reasoning"]
    assert "[Binding prevalidation]" in result["feedback"]


def test_lane_c_arc_timeline_allows_intra_arc_episode_window():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    issues = validator._collect_arc_timeline_alignment_issues(
        blueprint={
            "ep_num": 7,
            "ending_state": {
                "timeline": {
                    "표현": "2006년 2월 16일 오전 9시 30분",
                }
            },
        },
        arc_data={
            "ep_start": 7,
            "ep_end": 12,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 2, "day": 1},
                    "end": {"year": 2006, "month": 3, "week": 1},
                }
            },
        },
    )

    assert issues == []


def test_lane_c_arc_timeline_requires_terminal_episode_to_match_arc_end():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    issues = validator._collect_arc_timeline_alignment_issues(
        blueprint={
            "ep_num": 12,
            "ending_state": {
                "timeline": {
                    "표현": "2006년 2월 16일 오전 9시 30분",
                }
            },
        },
        arc_data={
            "ep_start": 7,
            "ep_end": 12,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 2, "day": 1},
                    "end": {"year": 2006, "month": 3, "week": 1},
                }
            },
        },
    )

    assert len(issues) == 1
    assert issues[0]["category"] == "arc_timeline"


def test_lane_c_arc_timeline_preserves_same_month_day_window_for_non_terminal_episode():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    issues = validator._collect_arc_timeline_alignment_issues(
        blueprint={
            "ep_num": 5,
            "ending_state": {
                "timeline": {
                    "표현": "2006년 2월 20일 오후",
                }
            },
        },
        arc_data={
            "ep_start": 5,
            "ep_end": 9,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 2, "day": 15},
                    "end": {"year": 2006, "month": 2, "day": 28},
                }
            },
        },
    )

    assert issues == []


def test_lane_c_arc_timeline_uses_arc_description_when_day_missing():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    issues = validator._collect_arc_timeline_alignment_issues(
        blueprint={
            "ep_num": 5,
            "ending_state": {
                "timeline": {
                    "표현": "2006년 2월 말",
                }
            },
        },
        arc_data={
            "ep_start": 5,
            "ep_end": 9,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 2, "description": "2월 초"},
                    "end": {"year": 2006, "month": 2, "description": "2월 말"},
                }
            },
        },
    )

    assert issues == []


def test_lane_c_arc_timeline_ignores_future_foreshadow_month_in_terminal_expression():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)

    issues = validator._collect_arc_timeline_alignment_issues(
        blueprint={
            "ep_num": 17,
            "ending_state": {
                "timeline": {
                    "표현": "2006년 5월, 7월의 위기를 앞둔 폭풍 전야",
                }
            },
        },
        arc_data={
            "ep_start": 13,
            "ep_end": 17,
            "state_changes": {
                "timeline": {
                    "start": {"year": 2006, "month": 5},
                    "end": {"year": 2006, "month": 5, "description": "2006년 5월 말, 에콰도르 쇼크 직후"},
                }
            },
        },
    )

    assert issues == []


# ===========================================================================
# Tranche 1 (2026-04-14): Opening-Transition Vocabulary Coherence
# ===========================================================================


def test_lane_c_opening_transition_marker_calibration_no_fp_on_arrow_time_flow():
    """Tranche 1 sub-edit 1.1: '->'와 '→'를 TIME_SHIFT_MARKERS에서 제거했으므로
    같은 위치에 시작하는 episode가 time_flow에 '오전 → 저녁' 형태의 화살표를 써도
    direct_continuation이 explicit_transition으로 강제 정규화되지 않아야 한다."""
    from modules.core.stage_cross_stage_contract import (
        OPENING_TRANSITION_DIRECT,
        infer_opening_transition_contract,
    )

    contract = infer_opening_transition_contract(
        {
            "start_location": "강남구 한미증권 본사",
            "time_flow": "진각 오전 → 진각 저녁",
            "scene_breakdown": {
                "scene_1": {
                    "location": "강남구 한미증권 본사",
                    "summary": "한시우가 박성호를 설득한다",
                }
            },
        },
        prev_blueprint={
            "end_location": "강남구 한미증권 본사",
            "time_flow": "진각 오전",
        },
    )
    assert contract.get("type") == OPENING_TRANSITION_DIRECT, (
        "time_flow 화살표는 시간 전이 마커가 아니라 duration span이므로 direct_continuation이어야 한다"
    )


def test_lane_c_opening_transition_marker_calibration_no_fp_on_diegetic_jin_ip():
    """Tranche 1 sub-edit 1.1: '진입'/'향해'/'향하'를 SCENE_MARKERS에서 제거했으므로
    scene_1 description에 인물의 diegetic '진입' (방으로 들어가는 행위)이 있어도
    explicit_transition이 강제 정규화되지 않아야 한다."""
    from modules.core.stage_cross_stage_contract import (
        OPENING_TRANSITION_DIRECT,
        infer_opening_transition_contract,
    )

    contract = infer_opening_transition_contract(
        {
            "start_location": "한미증권 청담동 지점 15층 VIP룸",
            "time_flow": "진각 오후",
            "scene_breakdown": {
                "scene_1": {
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "summary": "박성호가 VIP룸으로 진입하여 한시우를 향해 자리에 앉는다",
                }
            },
        },
        prev_blueprint={
            "end_location": "한미증권 청담동 지점 15층 VIP룸",
            "time_flow": "진각 오후",
        },
    )
    assert contract.get("type") == OPENING_TRANSITION_DIRECT, (
        "diegetic '진입'/'향해'는 인물 행동 묘사이므로 scene transition cue로 분류되면 안 된다"
    )


def test_lane_c_opening_transition_inplace_eligible_when_alias_only():
    """Tranche 1 sub-edit 1.5: opening_transition이 유일한 binding category이면
    full regenerate 대신 inplace alias 정규화가 허용되어야 한다."""
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues = (
        validator._apply_binding_prevalidation_contract(
            verdict="PASS",
            issues=[
                {
                    "severity": "MAJOR",
                    "category": "opening_transition",
                    "issue": "opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'",
                    "fix_hint": "선언과 정규화 일치",
                }
            ],
            feedback="",
            verdict_reason="ok",
            fix_scope="inplace",
            fix_scope_reasoning="",
        )
    )

    assert verdict == "PASS_WITH_FIX"
    assert fix_scope == "inplace", "opening_transition alias-only는 inplace 허용"
    assert "Opening-transition alias mismatch is the sole binding category" in fix_scope_reasoning
    assert binding_issues[0]["category"] == "opening_transition"


def test_lane_c_opening_transition_full_when_co_fires_with_other_binding():
    """Tranche 1 sub-edit 1.5: opening_transition이 다른 binding category와 함께
    firing되면 inplace 격하가 아니라 기존대로 full regenerate를 강제해야 한다."""
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues = (
        validator._apply_binding_prevalidation_contract(
            verdict="PASS",
            issues=[
                {
                    "severity": "MAJOR",
                    "category": "opening_transition",
                    "issue": "opening_transition.type mismatch",
                    "fix_hint": "fix",
                },
                {
                    "severity": "MAJOR",
                    "category": "protagonist_state",
                    "issue": "protagonist_state 비어 있음",
                    "fix_hint": "fill",
                },
            ],
            feedback="",
            verdict_reason="ok",
            fix_scope="inplace",
            fix_scope_reasoning="",
        )
    )

    assert verdict == "PASS_WITH_FIX"
    assert fix_scope == "full", "opening_transition + protagonist_state co-fire는 full regenerate"
    assert "Structural binding prevalidation categories require regenerate-only repair" in fix_scope_reasoning
    categories = {issue["category"] for issue in binding_issues}
    assert categories == {"opening_transition", "protagonist_state"}


def test_lane_c_sync_prevalidation_ensemble_meta_clears_stale_warning_residue():
    validator = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    blueprint = {
        "_ensemble_meta": {
            "python_warnings": [{"category": "opening_transition", "message": "stale"}],
            "advisory_fix_pack": {"patch_targets": ["integrated_scenario"]},
            "quality_risk": True,
        }
    }

    validator._sync_prevalidation_ensemble_meta(
        blueprint,
        python_warnings=[],
        advisory_fix_pack={},
        quality_risk=False,
    )

    assert "_ensemble_meta" not in blueprint
