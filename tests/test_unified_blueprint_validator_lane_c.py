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
