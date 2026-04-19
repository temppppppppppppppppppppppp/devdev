"""[Phase 4C-1a] Stage3Orchestrator 단위 테스트

추출 대상: _stage_3_batch_blueprinting (main_a.py → stage3_orchestrator.py)
"""

import json
import logging
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from modules.core.session_logger import SessionLogger
from modules.core.stage3_context import Stage3Context
from modules.core.stage3_orchestrator import (
    Stage3AttemptEvidencePacket,
    Stage3Orchestrator,
    _build_stage3_source_anchor_summary,
    _build_stage3_work_focus_advisory,
    _select_stage3_anchor_recent_window,
)

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def app_mock():
    """SovereignApp 모의 객체 — Stage 3에 필요한 최소 인터페이스"""
    app = MagicMock()

    # UI
    app.ui.log = MagicMock()

    # Project
    app.current_project.arcs = [
        {"arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 5, "tactical_doc": "x" * 600, "beat_sequence": [1, 2]},
    ]
    app.current_project.name = "TestProject"
    app.current_project.db.load_anchor.return_value = []
    app.current_project.db.get_latest_blueprint_number.return_value = 0
    app.current_project.db.get_manuscript.return_value = None
    app.current_project.get_blueprint.return_value = None
    app.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}

    # Agents
    app.agents = {
        "three_phase_bp": MagicMock(),
        "director": MagicMock(),
        "state_extractor": MagicMock(),
    }
    app.agents["three_phase_bp"].generate.return_value = (
        {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}},
        {"final_verdict": "PASS", "phases": {"generate": {"selected_strategy": "A", "selected_score": 85}}},
    )
    app.agents["three_phase_bp"].get_stats.return_value = {"pass_rate": "100%"}

    # Config
    app.selected_genre = {"type": "wuxia"}
    app.sys.api_client = MagicMock()
    app.preset_registry = MagicMock()
    app.memory = None
    app.context_advisor = None
    app._session_logger = MagicMock()

    # V68 lazy init (already initialized)
    app.state_tracker = MagicMock()
    app.state_tracker.npc_registry = {}
    app.world_state = MagicMock()
    app.fact_ledger = MagicMock()
    app.pass_rate_monitor = MagicMock()
    app.stage_rejection_history = []

    # Facade methods
    app._audit_event = MagicMock()
    app._get_int_input.return_value = 5
    app._get_max_episode_from_manuscripts.return_value = 0
    app._get_arc_context_for_episode.return_value = (0, app.current_project.arcs[0])
    app._get_protagonist_name.return_value = "장무기"
    app._fix_entity_registry_protagonist.return_value = {"characters": ["장무기"]}
    app._validate_arc_data_fields.return_value = app.current_project.arcs[0]
    app._validate_blueprint_integrity.return_value = True
    app._safe_commit = MagicMock()
    app._write_audit_summary = MagicMock()

    # Entity cache sentinel (not on app, on orchestrator)

    return app


@pytest.fixture
def orch(app_mock):
    return Stage3Orchestrator(app=app_mock)


# ── Constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_app_reference_stored(self, orch, app_mock):
        assert orch.app is app_mock

    def test_entity_cache_initialized(self, orch):
        assert orch._entity_cache_arc_idx == -1
        assert orch._cached_entity_registry is None


class TestStage3AnchorRecentWindow:
    def test_select_stage3_anchor_recent_window_keeps_older_anchors_and_recent_tail(self):
        selected = _select_stage3_anchor_recent_window(list(range(1, 41)))

        assert selected[:6] == [1, 4, 7, 10, 13, 16]
        assert selected[6:] == list(range(17, 41))


# ── V68 Lazy Init ────────────────────────────────────────────


class TestInitStateTrackerIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        """state_tracker가 이미 있으면 재초기화하지 않음"""
        app_mock.state_tracker = MagicMock()
        orch._init_state_tracker_if_needed()
        # Should NOT import StateTracker
        app_mock.current_project.db.load_anchor.assert_not_called()

    def test_creates_when_none_stub(self, orch, app_mock):
        """state_tracker가 None이면 초기화 (stub 호출 확인)"""
        app_mock.state_tracker = None
        with patch("modules.core.stage3_orchestrator.Stage3Orchestrator._init_state_tracker_if_needed") as mock_init:
            mock_init(orch)  # Just verifying it can be called

    def test_creates_when_none(self, app_mock):
        """state_tracker가 None이면 초기화 (실제 StateTracker import를 패치)"""
        app_mock.state_tracker = None
        app_mock.current_project.db.load_anchor.return_value = []
        orch = Stage3Orchestrator(app=app_mock)
        with patch("modules.domain.agents.state_tracker.StateTracker") as MockST:
            mock_st = MagicMock(npc_registry={})
            MockST.return_value = mock_st
            orch._init_state_tracker_if_needed()
        assert app_mock.state_tracker is mock_st


class TestInitWorldStateIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        app_mock.world_state = MagicMock()
        orch._init_world_state_if_needed()
        # No error, no new assignment

    def test_creates_when_none(self, orch, app_mock):
        app_mock.world_state = None
        with patch("modules.core.world_state.WorldStateManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.last_updated_ep = 0
            MockWS.return_value = mock_ws
            orch._init_world_state_if_needed()
        assert app_mock.world_state is mock_ws

    def test_failure_is_non_blocking(self, orch, app_mock):
        app_mock.world_state = None
        with patch("modules.core.world_state.WorldStateManager", side_effect=RuntimeError("DB error")):
            orch._init_world_state_if_needed()
        assert app_mock.world_state is None
        app_mock.ui.log.assert_called()


class TestInitFactLedgerIfNeeded:
    def test_skip_if_already_initialized(self, orch, app_mock):
        app_mock.fact_ledger = MagicMock()
        orch._init_fact_ledger_if_needed()

    def test_creates_when_none(self, orch, app_mock):
        app_mock.fact_ledger = None
        with patch("modules.core.fact_ledger.FactLedger") as MockFL:
            mock_fl = MagicMock()
            mock_fl.last_updated_ep = 5
            mock_fl.get_stats.return_value = {"characters": 3, "items": 2}
            MockFL.return_value = mock_fl
            orch._init_fact_ledger_if_needed()
        assert app_mock.fact_ledger is mock_fl

    def test_failure_is_non_blocking(self, orch, app_mock):
        app_mock.fact_ledger = None
        with patch("modules.core.fact_ledger.FactLedger", side_effect=RuntimeError("DB error")):
            orch._init_fact_ledger_if_needed()
        assert app_mock.fact_ledger is None


class TestDetectInventoryGaps:
    def test_uses_previous_blueprint_equipment_as_fallback_owned_inventory(self, app_mock):
        app_mock.world_state.get_owned_items.return_value = []
        app_mock.current_project.db.get_previous_blueprint.return_value = {
            "protagonist_state": {"equipment": ["가죽 수첩", "만년필", "폴더폰", "OTP 카드"]}
        }
        app_mock.constraint_db = None
        orch = Stage3Orchestrator(app=app_mock)

        blueprint = {
            "protagonist_state": {
                "equipment": [
                    "가죽 수첩",
                    "만년필",
                    "폴더폰",
                    "OTP 카드",
                    "WTI 6월물 절반 청산 및 잔여 홀딩 내역서",
                ]
            }
        }
        arc_data = {"arc_no": 3, "state_constraints": {}, "tactical_doc": ""}

        gaps = orch._detect_inventory_gaps(blueprint, arc_data, working_ep=17)

        assert gaps == [
            {
                "item": "WTI 6월물 절반 청산 및 잔여 홀딩 내역서",
                "source": "protagonist_state",
                "note": "현재 미보유 — 획득 장면 필요",
            }
        ]

    def test_suppresses_gap_for_current_arc_planned_item_when_narrative_seeds_acquisition(self, app_mock):
        app_mock.world_state.get_owned_items.return_value = []
        app_mock.current_project.db.get_previous_blueprint.return_value = {
            "protagonist_state": {"equipment": ["가죽 수첩", "만년필", "폴더폰", "OTP 카드"]}
        }
        app_mock.constraint_db = None
        orch = Stage3Orchestrator(app=app_mock)

        blueprint = {
            "protagonist_state": {
                "equipment": [
                    "가죽 수첩",
                    "만년필",
                    "폴더폰",
                    "OTP 카드",
                    "한미증권 'Exception Account' 승인 문서 사본",
                ]
            },
            "integrated_scenario": (
                "박성호는 한미증권 최상위 VIP조차 받기 힘든 예외 계좌 승인 문서 사본을 두 손으로 바쳤다."
            ),
        }
        arc_data = {
            "arc_no": 3,
            "state_constraints": {
                "protagonist_items": ["한미증권 리스크관리팀 발행 'Exception Account' 승인 문서 사본"]
            },
            "tactical_doc": "",
        }

        gaps = orch._detect_inventory_gaps(blueprint, arc_data, working_ep=17)

        assert gaps == []

    def test_uses_previous_blueprint_aliases_even_when_authoritative_inventory_is_long_form(self, app_mock):
        app_mock.world_state.get_owned_items.return_value = [
            "18년 치 매크로 이벤트가 암호화되어 적힌 양장 수첩",
            "20억 원이 예치된 개인 계좌 OTP 카드",
            "SW인베스트먼트 법인 계좌 보안 매체",
        ]
        app_mock.current_project.db.get_previous_blueprint.return_value = {
            "protagonist_state": {"equipment": ["가죽 수첩", "만년필", "폴더폰", "OTP 카드"]}
        }
        app_mock.constraint_db = None
        orch = Stage3Orchestrator(app=app_mock)

        blueprint = {
            "protagonist_state": {"equipment": ["가죽 수첩", "만년필", "폴더폰", "OTP 카드"]},
            "integrated_scenario": (
                "한시우는 가죽 수첩을 펼치고 만년필을 들었다. 곧이어 폴더폰을 집어 들고 OTP 카드 버튼을 눌렀다."
            ),
        }
        arc_data = {"arc_no": 4, "state_constraints": {}, "tactical_doc": ""}

        gaps = orch._detect_inventory_gaps(blueprint, arc_data, working_ep=18)

        assert gaps == []


# ── Entity Registry Cache ────────────────────────────────────


class TestGetEntityRegistry:
    def test_first_call_extracts(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        result = orch._get_entity_registry(arc_idx=0)
        assert result is not None
        assert orch._entity_cache_arc_idx == 0

    def test_cached_on_same_arc(self, orch, app_mock):
        # First call
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        orch._get_entity_registry(arc_idx=0)

        # Second call — should use cache
        app_mock.agents["state_extractor"].extract_cumulative_state.reset_mock()
        result = orch._get_entity_registry(arc_idx=0)
        app_mock.agents["state_extractor"].extract_cumulative_state.assert_not_called()

    def test_refreshes_on_new_arc(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.return_value = {
            "entity_registry": {"characters": ["A"]}
        }
        orch._get_entity_registry(arc_idx=0)
        orch._get_entity_registry(arc_idx=1)
        assert orch._entity_cache_arc_idx == 1

    def test_failure_non_blocking(self, orch, app_mock):
        app_mock.agents["state_extractor"].extract_cumulative_state.side_effect = RuntimeError("LLM error")
        result = orch._get_entity_registry(arc_idx=0)
        assert result is None
        assert orch._entity_cache_arc_idx == 0  # [P0] 실패한 arc_idx 캐싱 — 동일 arc 무한 재시도 방지


# ── Blueprint Helpers ────────────────────────────────────────


class TestStageAttemptObservability:
    def test_build_stage3_source_anchor_summary_surfaces_prev_bp_and_start_state(self):
        summary = _build_stage3_source_anchor_summary(
            {
                "ep_start": 2,
                "joint_docs": {"final_location": "SW인베스트먼트 사무실"},
                "semantic_carryover": {"continuity_checkpoints": ["회귀 사실 유지"]},
                "state_constraints": {
                    "arc_start_state": {
                        "location": "SW인베스트먼트 사무실",
                        "equipment": ["법인 인감", "CME 계좌 증빙"],
                    }
                },
            },
            [
                {
                    "ep_num": 1,
                    "end_location": "서재 앞 복도",
                    "opening_transition": {"type": "direct_continuation"},
                }
            ],
        )

        assert summary["previous_blueprint_ep"] == 1
        assert summary["previous_blueprint_end_location"] == "서재 앞 복도"
        assert summary["previous_blueprint_opening_transition_type"] == "direct_continuation"
        assert summary["current_arc_start_location"] == "SW인베스트먼트 사무실"
        assert summary["current_arc_start_inventory_count"] == 2
        assert "anchor_surfaces" in summary

    def test_build_stage3_source_anchor_summary_hides_stale_arc_start_mid_arc(self):
        summary = _build_stage3_source_anchor_summary(
            {
                "ep_start": 7,
                "joint_docs": {"final_location": "본가 개인 서재"},
                "state_constraints": {
                    "arc_start_state": {
                        "location": "본가 개인 서재",
                        "equipment": ["가죽 서류가방", "삼성 애니콜 SGH-D600"],
                    }
                },
            },
            [
                {
                    "ep_num": 8,
                    "end_location": "한미증권 청담동 지점 15층 VIP룸",
                    "opening_transition": {"type": "direct_continuation"},
                }
            ],
        )

        assert summary["previous_blueprint_ep"] == 8
        assert summary["previous_blueprint_end_location"] == "한미증권 청담동 지점 15층 VIP룸"
        assert "current_arc_start_location" not in summary
        assert "current_arc_start_inventory_count" not in summary
        assert "arc_start_location" not in summary.get("anchor_surfaces", [])

    def test_handle_success_persists_semantic_context_metadata(self, orch, app_mock):
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 88,
            "phases": {
                "generate": {"selected_strategy": "balanced", "selected_score": 88},
                "validate": {
                    "runtime_advisory": "semantic context drift warning",
                    "retry_directives": "keep the anchor packet stable on the next pass",
                },
            },
            "_stage3_duration_ms": 4321,
            "_stage3_observability": {
                "semantic_ctx_chars": 1234,
                "source_counts": {"vec_memory": 2, "db_npc_relationship": 1},
                "coverage_warnings": ["missing_relation_slice"],
                "advisor_path_used": True,
                "planned_slots_count": 3,
                "work_focus_present": True,
                "provenance_ledger": {"source_pack": "stage3", "dropped_at": "stage3"},
                "budget_ledger": {"budget_bucket": "smart_retrieval.stage3_total_budget", "configured_cap": 2400},
                "source_anchor_summary": {
                    "previous_blueprint_ep": 1,
                    "previous_blueprint_end_location": "서재 앞 복도",
                    "current_arc_start_location": "SW인베스트먼트 사무실",
                },
                "episode_state_packet_summary": {
                    "opening_location": "한미증권 청담동 지점 15층 VIP룸",
                    "opening_location_source": "prev_blueprint.scene_breakdown.last.location",
                    "dropped_conflict_count": 1,
                    "rewrite_required_reasons": ["mid_arc_arc_start_location_override_blocked"],
                },
                "prompt_envelope": {
                    "total_chars": 4820,
                    "budget_ledger": {"budget_bucket": "stage3.prompt_envelope_total_chars"},
                },
            },
        }

        orch._handle_success(
            working_ep=1,
            arc_no=1,
            arc_data={"arc_no": 1},
            blueprint={"integrated_scenario": "ok"},
            pipeline_result=pipeline_result,
            prev_blueprints=[],
            success_count=0,
            fail_count=0,
        )

        kwargs = app_mock.current_project.db.save_stage_attempt.call_args.kwargs
        assert kwargs["duration_ms"] == 4321
        assert kwargs["advisory_flags"]["semantic_ctx_chars"] == 1234
        assert kwargs["advisory_flags"]["semantic_ctx_sources"] == ["db_npc_relationship", "vec_memory"]
        assert kwargs["advisory_flags"]["provenance_ledger"]["source_pack"] == "stage3"
        assert kwargs["advisory_flags"]["budget_ledger"]["budget_bucket"] == "smart_retrieval.stage3_total_budget"
        assert (
            kwargs["advisory_flags"]["source_anchor_summary"]["current_arc_start_location"] == "SW인베스트먼트 사무실"
        )
        assert (
            kwargs["advisory_flags"]["episode_state_packet_summary"]["opening_location"]
            == "한미증권 청담동 지점 15층 VIP룸"
        )
        assert kwargs["advisory_flags"]["episode_state_packet_summary"]["dropped_conflict_count"] == 1
        assert kwargs["advisory_flags"]["prompt_envelope"]["total_chars"] == 4820
        assert kwargs["runtime_advisory"] == "semantic context drift warning"
        assert kwargs["retry_directives"] == "keep the anchor packet stable on the next pass"
        assert any("source_anchor:" in str(call.args[0]) for call in app_mock.ui.log.call_args_list if call.args)

    def test_handle_failure_persists_failure_category_and_observability(self, orch, app_mock):
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": 52,
            "quality_gate_failed": True,
            "phases": {
                "generate": {"selected_strategy": "balanced", "selected_score": 52},
                "validate": {
                    "issues_count": 2,
                    "runtime_advisory": "continuity drift needs review",
                    "retry_directives": "repair the opening continuity before the next retry",
                },
            },
            "_stage3_duration_ms": 987,
            "_stage3_observability": {
                "semantic_ctx_chars": 222,
                "source_counts": {"legacy_semantic_context": 1},
                "coverage_warnings": [],
                "advisor_path_used": False,
                "planned_slots_count": 0,
                "work_focus_present": False,
            },
        }

        orch._handle_failure(
            working_ep=1,
            pipeline_result=pipeline_result,
            success_count=0,
            fail_count=0,
            arc_no=1,
        )

        kwargs = app_mock.current_project.db.save_stage_attempt.call_args.kwargs
        assert kwargs["failure_category"] == "quality_gate"
        assert kwargs["duration_ms"] == 987
        assert kwargs["advisory_flags"]["semantic_ctx_sources"] == ["legacy_semantic_context"]
        assert kwargs["runtime_advisory"] == "continuity drift needs review"
        assert kwargs["retry_directives"] == "repair the opening continuity before the next retry"

    def test_finalize_stage3_pipeline_result_promotes_episode_state_packet_summary(self, orch):
        pipeline_result = {
            "final_verdict": "PASS",
            "phases": {
                "constraint": {
                    "episode_state_packet_summary": {
                        "opening_location": "한미증권 청담동 지점 15층 VIP룸",
                        "opening_location_source": "prev_blueprint.scene_breakdown.last.location",
                        "dropped_conflict_count": 1,
                    }
                }
            },
        }

        result = orch._finalize_stage3_blueprint_pipeline_result(
            pipeline_result=pipeline_result,
            started_at=time.perf_counter(),
            started_cost_usd=0.0,
            semantic_bundle={
                "semantic_ctx": "short semantic ctx",
                "source_counts": {"vec_memory": 1},
                "coverage_warnings": [],
                "work_focus": {},
                "observation": {},
            },
        )

        summary = result["_stage3_observability"]["episode_state_packet_summary"]
        assert summary["opening_location"] == "한미증권 청담동 지점 15층 VIP룸"
        assert summary["dropped_conflict_count"] == 1

    def test_finalize_stage3_pipeline_result_promotes_prompt_envelope(self, orch):
        pipeline_result = {
            "final_verdict": "PASS",
            "phases": {
                "generate": {
                    "prompt_envelope": {
                        "total_chars": 4820,
                        "budget_ledger": {"budget_bucket": "stage3.prompt_envelope_total_chars"},
                    }
                }
            },
        }

        result = orch._finalize_stage3_blueprint_pipeline_result(
            pipeline_result=pipeline_result,
            started_at=time.perf_counter(),
            started_cost_usd=0.0,
            semantic_bundle={
                "semantic_ctx": "short semantic ctx",
                "source_counts": {"vec_memory": 1},
                "coverage_warnings": [],
                "work_focus": {},
                "observation": {},
            },
        )

        prompt_envelope = result["_stage3_observability"]["prompt_envelope"]
        assert prompt_envelope["total_chars"] == 4820
        assert prompt_envelope["budget_ledger"]["budget_bucket"] == "stage3.prompt_envelope_total_chars"

    def test_handle_success_persists_stage3_director_selection(self, orch, app_mock, tmp_path):
        app_mock.current_project.paths = MagicMock()
        app_mock.current_project.paths.root = tmp_path
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 91,
            "phases": {
                "generate": {"selected_strategy": "dialogue_focused", "selected_score": 91},
                "validate": {
                    "phase": "director_compare",
                    "selected_index": 1,
                    "comparison_notes": "후보 2가 전술 반영과 연속성에서 가장 안정적",
                    "verdict": "PASS",
                },
            },
            "_stage3_duration_ms": 1500,
            "_stage3_observability": {
                "semantic_ctx_chars": 1200,
                "source_counts": {"vec_memory": 2, "db_npc_history": 1},
                "advisor_path_used": True,
                "planned_slots_count": 3,
            },
        }

        orch._handle_success(
            working_ep=2,
            arc_no=1,
            arc_data={"arc_no": 1},
            blueprint={"integrated_scenario": "ok", "scene_breakdown": {"s1": "scene"}},
            pipeline_result=pipeline_result,
            prev_blueprints=[],
            success_count=0,
            fail_count=0,
        )

        ds_kw = app_mock.current_project.db.save_director_selection.call_args.kwargs
        sa_kw = app_mock.current_project.db.save_stage_attempt.call_args.kwargs
        assert ds_kw["stage"] == 3
        assert ds_kw["selected_label"] == "B"
        assert ds_kw["selected_strategy"] == "dialogue_focused"
        assert ds_kw["verdict"] == "PASS"
        assert ds_kw["selection_reason"] == ""
        assert ds_kw["advisory_warnings"]["comparison_notes"] == "후보 2가 전술 반영과 연속성에서 가장 안정적"
        assert ds_kw["attempt_key"] == sa_kw["attempt_key"]
        assert ds_kw["candidate_key"] == sa_kw["candidate_key"]
        assert ds_kw["artifact_path"] == sa_kw["artifact_path"]

    def test_handle_failure_persists_stage3_director_selection(self, orch, app_mock, tmp_path):
        app_mock.current_project.paths = MagicMock()
        app_mock.current_project.paths.root = tmp_path
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": 44,
            "phases": {
                "generate": {"selected_strategy": "action_focused", "selected_score": 44},
                "validate": {
                    "phase": "director_compare",
                    "selected_index": 0,
                    "comparison_notes": "후보 1이 상대적으로 낫지만 전면 재설계가 필요함",
                    "verdict": "REJECT",
                    "feedback": "전술 사건 재배치 필요",
                    "fix_scope": "full",
                    "runtime_advisory": "timeline mismatch detected",
                    "retry_directives": "repair the timeline anchors before the next retry",
                    "contradictions": ["timeline mismatch"],
                },
            },
            "_stage3_duration_ms": 987,
            "_stage3_observability": {
                "semantic_ctx_chars": 222,
                "source_counts": {"legacy_semantic_context": 1},
                "advisor_path_used": False,
            },
        }

        orch._handle_failure(
            working_ep=3,
            pipeline_result=pipeline_result,
            success_count=0,
            fail_count=0,
            arc_no=1,
            blueprint={"integrated_scenario": "candidate", "scene_breakdown": {"s1": "scene"}},
        )

        ds_kw = app_mock.current_project.db.save_director_selection.call_args.kwargs
        assert ds_kw["stage"] == 3
        assert ds_kw["selected_label"] == "A"
        assert ds_kw["selected_strategy"] == "action_focused"
        assert ds_kw["verdict"] == "REJECT"
        assert ds_kw["fix_scope"] == "full"
        assert ds_kw["artifact_path"].endswith("selected_blueprint__action_focused.json")
        assert (tmp_path / ds_kw["artifact_path"]).exists()
        assert ds_kw["advisory_warnings"]["contradictions"] == ["timeline mismatch"]
        assert ds_kw["runtime_advisory"] == "timeline mismatch detected"
        assert ds_kw["retry_directives"] == "repair the timeline anchors before the next retry"

    def test_handle_success_writes_session_decision_row_with_join_metadata(self, orch, app_mock, tmp_path):
        app_mock.current_project.paths = MagicMock()
        app_mock.current_project.paths.root = tmp_path
        session_logger = SessionLogger(tmp_path / "logs" / "session", enabled=True)
        app_mock._session_logger = session_logger
        orch.ctx.session_logger = session_logger
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 93,
            "phases": {
                "generate": {"selected_strategy": "dialogue_focused", "selected_score": 93},
                "validate": {
                    "verdict": "PASS",
                    "selection_reason": "후보 B가 감정선과 연속성 연결이 가장 안정적",
                    "verdict_reason": "구조 리스크 없이 바로 사용 가능",
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "runtime_advisory": "keep the opening continuity packet visible",
                    "retry_directives": "preserve the opening continuity packet on the next pass",
                    "fix_pack": {
                        "patch_targets": ["scene_1.summary"],
                        "target_kind": "scene_block",
                        "subtype": "movement",
                        "provenance": "director_authored",
                    },
                    "repair_contract": {
                        "subtype": "movement",
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "provenance": "director_authored",
                        "target_kind": "scene_block",
                    },
                    "scope_authority": {
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "widened": False,
                    },
                },
            },
        }

        orch._handle_success(
            working_ep=4,
            arc_no=1,
            arc_data={"arc_no": 1},
            blueprint={"integrated_scenario": "ok", "scene_breakdown": {"s1": "scene"}},
            pipeline_result=pipeline_result,
            prev_blueprints=[],
            success_count=0,
            fail_count=0,
        )

        decisions_path = tmp_path / "logs" / "session" / "decisions.jsonl"
        rows = [json.loads(line) for line in decisions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        row = rows[-1]
        meta = row["meta"]

        assert row["stage"] == "stage3"
        assert row["result"] == "PASS"
        assert meta["attempt_key"].startswith("s3:ep4:arc1:a")
        assert meta["candidate_key"] == "dialogue_focused"
        assert meta["content_hash"]
        assert meta["artifact_path"].endswith("final_blueprint__dialogue_focused.json")
        assert meta["reason"] == "구조 리스크 없이 바로 사용 가능"
        assert meta["selection_reason"] == "후보 B가 감정선과 연속성 연결이 가장 안정적"
        assert meta["verdict_reason"] == "구조 리스크 없이 바로 사용 가능"
        assert meta["fix_scope"] == "inplace"
        assert meta["repair_scope"] == "inplace"
        assert meta["authoritative_fix_scope"] == "inplace"
        assert meta["runtime_advisory"] == "keep the opening continuity packet visible"
        assert meta["retry_directives"] == "preserve the opening continuity packet on the next pass"
        assert meta["fix_pack"]["subtype"] == "movement"
        assert meta["repair_contract"]["provenance"] == "director_authored"
        assert meta["scope_authority"]["widened"] is False
        assert (tmp_path / meta["artifact_path"]).exists()

    def test_build_stage3_director_selection_kwargs_keeps_500_char_rationale(self):
        selection_reason = "r" * 450
        payload = Stage3Orchestrator._build_stage3_director_selection_kwargs(
            {
                "final_verdict": "PASS",
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selected_index": 1,
                        "selection_reason": selection_reason,
                    }
                },
            },
            ep_num=4,
            attempt_num=1,
            attempt_key="s3:ep4:arc1:a1",
            selected_strategy="dialogue_focused",
            score=93,
            candidate_key="dialogue_focused",
        )

        assert payload is not None
        assert payload["selection_reason"] == selection_reason

    def test_build_stage3_director_selection_kwargs_keeps_quality_risk_advisory(self):
        payload = Stage3Orchestrator._build_stage3_director_selection_kwargs(
            {
                "final_verdict": "PASS",
                "quality_risk": True,
                "revision_required": True,
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selected_index": 1,
                        "selection_reason": "candidate 2 edges out the field",
                        "comparison_notes": "candidate 2 keeps continuity cleaner than candidate 1",
                        "quality_risk": True,
                        "revision_required": True,
                        "selected_candidate_advisory": {
                            "candidate_index": 1,
                            "quality_risk": True,
                            "python_warnings": [{"message": "Arc NPC mention is thin"}],
                        },
                    }
                },
            },
            ep_num=4,
            attempt_num=1,
            attempt_key="s3:ep4:arc1:a1",
            selected_strategy="dialogue_focused",
            score=93,
            candidate_key="dialogue_focused",
        )

        assert payload is not None
        assert payload["advisory_warnings"]["quality_risk"] is True
        assert payload["advisory_warnings"]["revision_required"] is True
        assert "selected_candidate_advisory" not in payload["advisory_warnings"]
        assert (
            payload["advisory_warnings"]["comparison_notes"] == "candidate 2 keeps continuity cleaner than candidate 1"
        )
        assert payload["advisory_warnings"]["selected_candidate_advisory_struct"]["candidate_index"] == 1
        assert payload["advisory_warnings"]["selected_candidate_advisory_struct"]["quality_risk"] is True

    def test_build_stage3_director_selection_kwargs_keeps_selection_reason_independent_from_comparison_notes(self):
        payload = Stage3Orchestrator._build_stage3_director_selection_kwargs(
            {
                "final_verdict": "PASS",
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selected_index": 1,
                        "comparison_notes": "candidate 2 keeps continuity cleaner than candidate 1",
                    }
                },
            },
            ep_num=4,
            attempt_num=1,
            attempt_key="s3:ep4:arc1:a1",
            selected_strategy="dialogue_focused",
            score=93,
            candidate_key="dialogue_focused",
        )

        assert payload is not None
        assert payload["selection_reason"] == ""
        assert (
            payload["advisory_warnings"]["comparison_notes"] == "candidate 2 keeps continuity cleaner than candidate 1"
        )

    def test_build_stage3_director_selection_kwargs_preserves_partial_fix_contract(self):
        payload = Stage3Orchestrator._build_stage3_director_selection_kwargs(
            {
                "final_verdict": "PASS",
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selected_index": 0,
                        "selection_reason": "candidate 1 closes the local repair cleanly",
                        "fix_pack": {
                            "patch_targets": ["scene_2.summary"],
                            "target_kind": "scene_block",
                            "must_fix": ["scene 2 summary must reflect the repaired reveal"],
                            "subtype": "movement",
                            "provenance": "director_authored",
                        },
                        "repair_contract": {
                            "subtype": "movement",
                            "fix_scope": "inplace",
                            "repair_scope": "inplace",
                            "authoritative_fix_scope": "inplace",
                            "provenance": "director_authored",
                            "target_kind": "scene_block",
                        },
                        "scope_authority": {
                            "fix_scope": "inplace",
                            "repair_scope": "inplace",
                            "authoritative_fix_scope": "inplace",
                            "widened": False,
                        },
                        "partial_fix_eval": {
                            "patch_round": 1,
                            "patch_target_id": "pt:scene2",
                            "target_kind": "scene_block",
                            "must_fix_resolved": True,
                            "do_not_regress_held": True,
                            "success_condition_met": True,
                        },
                    }
                },
            },
            ep_num=4,
            attempt_num=1,
            attempt_key="s3:ep4:arc1:a1",
            selected_strategy="dialogue_focused",
            score=93,
            candidate_key="dialogue_focused",
        )

        assert payload is not None
        assert payload["advisory_warnings"]["fix_pack"]["patch_targets"] == ["scene_2.summary"]
        assert payload["advisory_warnings"]["fix_pack"]["subtype"] == "movement"
        assert payload["advisory_warnings"]["fix_pack"]["provenance"] == "director_authored"
        assert payload["advisory_warnings"]["repair_contract"]["subtype"] == "movement"
        assert payload["advisory_warnings"]["repair_contract"]["provenance"] == "director_authored"
        assert payload["advisory_warnings"]["scope_authority"]["widened"] is False
        assert payload["advisory_warnings"]["partial_fix_eval"]["patch_target_id"] == "pt:scene2"

    def test_annotate_stage3_success_blueprint_preserves_binding_meta(self, orch):
        blueprint = {}

        result = orch._annotate_stage3_success_blueprint(
            working_ep=1,
            arc_data={},
            blueprint=blueprint,
            pipeline_result={
                "last_score": 88,
                "phases": {
                    "validate": {
                        "binding_prevalidation_issue_count": 2,
                        "binding_prevalidation_categories": ["dead_npc", "fact_lock_location"],
                        "binding_regenerate_only_categories": ["opening_anchor"],
                        "binding_regenerate_only_reason": (
                            "Structural binding prevalidation requires regenerate-only repair: opening_anchor"
                        ),
                        "fix_pack": {
                            "patch_targets": ["scene_2.summary"],
                            "target_kind": "scene_block",
                            "must_fix": ["scene 2 summary must reflect the repaired reveal"],
                            "success_condition": "scene 2 now states the reveal without rewriting the arc shell",
                            "subtype": "movement",
                            "provenance": "director_authored",
                            "provenance_sources": ["director_compare"],
                        },
                        "repair_contract": {
                            "subtype": "movement",
                            "fix_scope": "inplace",
                            "repair_scope": "inplace",
                            "authoritative_fix_scope": "inplace",
                            "provenance": "director_authored",
                            "target_kind": "scene_block",
                        },
                        "scope_authority": {
                            "fix_scope": "inplace",
                            "repair_scope": "inplace",
                            "authoritative_fix_scope": "inplace",
                            "widened": False,
                        },
                        "partial_fix_eval": {
                            "patch_round": 1,
                            "patch_target_id": "pt:scene2",
                            "target_kind": "scene_block",
                            "must_fix_resolved": True,
                            "do_not_regress_held": True,
                            "success_condition_met": True,
                        },
                    }
                },
            },
            final_verdict="PASS_WITH_FIX",
            quality_gate_failed=False,
            quality_risk=False,
            revision_required=True,
        )

        assert result["_stage3_meta"]["final_verdict"] == "PASS_WITH_FIX"
        assert result["_stage3_meta"]["revision_required"] is True
        assert result["_stage3_meta"]["binding_prevalidation_issue_count"] == 2
        assert result["_stage3_meta"]["binding_prevalidation_categories"] == ["dead_npc", "fact_lock_location"]
        assert result["_stage3_meta"]["binding_regenerate_only_categories"] == ["opening_anchor"]
        assert "opening_anchor" in result["_stage3_meta"]["binding_regenerate_only_reason"]
        assert result["_stage3_meta"]["fix_pack"]["patch_targets"] == ["scene_2.summary"]
        assert result["_stage3_meta"]["fix_pack"]["subtype"] == "movement"
        assert result["_stage3_meta"]["fix_pack"]["provenance"] == "director_authored"
        assert result["_stage3_meta"]["repair_contract"]["subtype"] == "movement"
        assert result["_stage3_meta"]["repair_contract"]["provenance"] == "director_authored"
        assert result["_stage3_meta"]["scope_authority"]["widened"] is False
        assert result["_stage3_meta"]["partial_fix_eval"]["patch_target_id"] == "pt:scene2"


class TestLoadPrevBlueprint:
    def test_returns_none_for_ep1(self, orch):
        result = orch._load_prev_blueprint(1)
        assert result is None

    def test_returns_prev_for_ep2(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = {"ep": 1}
        result = orch._load_prev_blueprint(2)
        assert result == {"ep": 1}

    def test_crash_returns_none(self, orch, app_mock):
        app_mock.current_project.get_blueprint.side_effect = RuntimeError("DB crash")
        result = orch._load_prev_blueprint(5)
        assert result is None


class TestGetProtagonistNameSafe:
    def test_returns_name(self, orch, app_mock):
        app_mock._get_protagonist_name.return_value = "소림사"
        assert orch._get_protagonist_name_safe() == "소림사"

    def test_crash_returns_default(self, orch, app_mock):
        app_mock._get_protagonist_name.side_effect = RuntimeError("crash")
        assert orch._get_protagonist_name_safe() == "주인공"


class TestNs4TimelineHelpers:
    def test_extract_timeline_start_end_from_range_string(self, orch):
        arc_data = {
            "state_changes": {
                "timeline": {
                    "start": "2006년 5월~8월",
                    "end": "2006년 5월~8월",
                }
            }
        }
        start, end = orch._extract_timeline_start_end(arc_data)
        assert start == (2006, 5)
        assert end == (2006, 8)

    def test_timeline_start_end_raw_equal(self, orch):
        arc_data = {
            "state_changes": {
                "timeline": {
                    "start": "2006년 5월~8월",
                    "end": "2006년 5월~8월",
                }
            }
        }
        assert orch._timeline_start_end_raw_equal(arc_data) is True


class TestGenerateBlueprint:
    @patch("modules.core.spinners.StageSpinner")
    def test_generate_blueprint_uses_anchor_recent_blueprint_window(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        prev_blueprints = [
            {"ep_num": ep, "integrated_scenario": f"blueprint {ep}", "scene_breakdown": {"s1": f"scene {ep}"}}
            for ep in range(1, 41)
        ]

        orch._generate_blueprint(
            working_ep=40,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=prev_blueprints[-1],
            prev_blueprints=prev_blueprints,
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        passed_prev_blueprints = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["prev_blueprints"]
        assert [bp["ep_num"] for bp in passed_prev_blueprints[:6]] == [1, 4, 7, 10, 13, 16]
        assert [bp["ep_num"] for bp in passed_prev_blueprints[6:]] == list(range(17, 41))

    @patch("modules.core.spinners.StageSpinner")
    def test_generate_blueprint_uses_anchor_recent_manuscript_window(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = [
            {"ep_num": ep, "title": f"제{ep}화", "content": f"원고 {ep}"} for ep in range(1, 37)
        ]

        orch._generate_blueprint(
            working_ep=40,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        prev_manuscripts_text = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["prev_manuscripts_text"]
        assert "━━━ 제1화 원고 ━━━" in prev_manuscripts_text
        assert "━━━ 제36화 원고 ━━━" in prev_manuscripts_text
        assert "━━━ 제2화 원고 ━━━" not in prev_manuscripts_text

    @patch("modules.core.spinners.StageSpinner")
    def test_world_state_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.world_state.get_summary.return_value = "주인공 상태=긴장, 진행 플롯=적대적 인수합병"

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[WorldState 핵심 요약]" in semantic_context
        assert "진행 플롯=적대적 인수합병" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_fact_ledger_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.current_project.db.load_anchor.side_effect = lambda key: (
            {"numbers": {"자본금": {"value": "10억", "unit": "원", "last_ep": 12}}} if key == "fact_ledger" else []
        )

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[팩트 원장 핵심 수치]" in semantic_context
        assert "자본금" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_treatment_block_is_injected_into_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {},
                "plot_roadmap": [
                    {
                        "title": "시장 선점",
                        "event_villain": "유동성 위기",
                        "solution": "리스크 관리",
                        "content": {"context": "기관 매도 공세"},
                    }
                ],
            }
        }

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        # [W1] header changed from "원본 Treatment Block" to "Arc 개요"
        assert "[Arc 개요" in semantic_context
        assert "시장 선점" in semantic_context  # title: safe arc-framing field
        assert "기관 매도 공세" in semantic_context  # content.context: safe field
        # [W1] event_villain is now quarantined — must NOT appear
        assert "유동성 위기" not in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_style_guide_advisory_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.current_project.load_v20_anchor.return_value = {
            "tone": "건조함",
            "pov": "3인칭",
            "sentence_length": "short",
            "paragraph_style": "mixed",
            "anti_ai_patterns": ["그의 눈동자가 흔들렸다"],
        }

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[StyleGuide 문체/anti-AI 참고]" in semantic_context
        assert "그의 눈동자가 흔들렸다" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_generate_blueprint_crash_returns_error_pipeline_and_audits(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.agents["three_phase_bp"].generate.side_effect = RuntimeError("boom")

        blueprint, pipeline_result = orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
            protagonist_config={},
        )

        assert blueprint is None
        assert pipeline_result["final_verdict"] == "ERROR"
        assert "boom" in pipeline_result["error"]
        app_mock._audit_event.assert_any_call("blueprint_gen_error", "boom", {"ep_num": 1})

    @patch("modules.core.spinners.StageSpinner")
    def test_work_focus_summary_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["인재 발굴"],
            "registry_profiles": [
                {
                    "name": "talent_registry",
                    "required_fields": ["name", "status", "fan_reaction"],
                }
            ],
        }

        orch._generate_blueprint(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={"characters": ["윤서아", "강이현"]},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        assert "[작품 추적 슬롯 요약]" in semantic_context
        assert "핵심 배우 라인" in semantic_context
        assert "talent_registry" in semantic_context

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_advisor_receives_work_focus(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.context_advisor = MagicMock()
        app_mock.memory = MagicMock()
        app_mock.memory.retrieve_multi_query_context.return_value = "vec context"
        app_mock.memory.retrieve_npc_context.return_value = "npc context"
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": ["팬덤 반응"],
            "registry_profiles": [{"name": "talent_registry", "required_fields": ["name", "heat"]}],
        }
        app_mock.context_advisor.plan_stage3_retrieval.return_value = MagicMock(
            slots=[
                MagicMock(category="work_tracking_slot_1", query="slot query", source="db_npc_history", max_chars=400),
                MagicMock(category="genre_context_1", query="genre query", source="vec_memory", max_chars=400),
            ]
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage3_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 8
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect):
            orch._generate_blueprint(
                working_ep=1,
                arc_data=app_mock.current_project.arcs[0],
                arc_idx=0,
                prev_blueprint=None,
                prev_blueprints=[],
                entity_registry={"characters": [{"name": "윤서아"}, {"name": "강이현"}]},
                protagonist_name="장무기",
                protagonist_config={},
            )

        app_mock.context_advisor.plan_stage3_retrieval.assert_called_once()
        call_kwargs = app_mock.context_advisor.plan_stage3_retrieval.call_args.kwargs
        assert call_kwargs["work_focus"]["tracking_slots"] == ["핵심 배우 라인"]

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_advisor_uses_ctx_services_not_hidden_app(self, MockSpinner, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }

        ctx_advisor = MagicMock()
        ctx_memory = MagicMock()
        ctx_memory.retrieve_multi_query_context.return_value = "vec context"
        ctx_advisor.plan_stage3_retrieval.return_value = MagicMock(
            slots=[MagicMock(category="genre_context_1", query="genre query", source="vec_memory", max_chars=400)]
        )

        ctx = Stage3Context.from_app(app_mock)
        ctx.context_advisor = ctx_advisor
        ctx.memory = ctx_memory

        app_mock.context_advisor = None
        app_mock.memory = None

        orch = Stage3Orchestrator(app=app_mock, context=ctx)

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage3_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 8
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect):
            orch._generate_blueprint(
                working_ep=1,
                arc_data=app_mock.current_project.arcs[0],
                arc_idx=0,
                prev_blueprint=None,
                prev_blueprints=[],
                entity_registry={"characters": [{"name": "윤서아"}]},
                protagonist_name="장무기",
                protagonist_config={},
            )

        ctx_advisor.plan_stage3_retrieval.assert_called_once()
        assert ctx_advisor.plan_stage3_retrieval.call_args.kwargs["genre"] == "wuxia"

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_work_focus_relation_slice_included_in_semantic_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.quality_dashboard = MagicMock()
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        app_mock.world_state.get_state_dict.return_value = {"relationships": {"연홍": "죽마고우"}}
        app_mock.fact_ledger._ledger = {
            "characters": {"연홍": {"relationship": "소꿉친구", "established_ep": 3, "history": []}}
        }
        app_mock.current_project.db.get_npc_relationship_edges.return_value = [
            {"npc1": "장무기", "npc2": "연홍", "relation": "죽마고우", "updated_ep": 3}
        ]
        app_mock.current_project.db.get_relationship_history.return_value = [
            {"old_relation": "친구", "new_relation": "죽마고우", "change_ep": 3}
        ]

        orch._generate_blueprint(
            working_ep=1,
            arc_data={
                **app_mock.current_project.arcs[0],
                "constraint_summary": "연홍과의 소꿉친구 관계를 회복한다",
            },
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={"characters": ["연홍"]},
            protagonist_name="장무기",
            protagonist_config={},
        )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        app_mock.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = app_mock.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "stage3"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert kwargs["observation"]["provenance_ledger"]["source_pack"] == "stage3"
        assert kwargs["observation"]["budget_ledger"]["budget_bucket"] == "smart_retrieval.stage3_total_budget"
        assert "[관계 의미 질의]" in semantic_context
        assert "연홍" in semantic_context

    def test_build_stage3_blueprint_semantic_bundle_marks_legacy_source_when_only_advisories_exist(
        self, orch, app_mock
    ):
        app_mock.quality_dashboard = MagicMock()
        app_mock.world_state.get_summary.return_value = "진행 플롯=인수합병"

        bundle = orch._build_stage3_blueprint_semantic_bundle(
            working_ep=1,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprints=[],
            entity_registry={},
            protagonist_name="장무기",
        )

        assert bundle["source_counts"] == {"legacy_semantic_context": 1}
        assert bundle["plan"] is None
        assert bundle["observation"]["advisor_path_used"] is False
        app_mock.quality_dashboard.record_retrieval_observation.assert_called_once()

    @patch("modules.core.spinners.StageSpinner")
    def test_run_stage3_blueprint_generation_handoff_preserves_tail_and_prev_hud(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = [
            {"ep_num": ep, "title": f"제{ep}화", "content": f"원고 {ep}"} for ep in range(1, 37)
        ]
        app_mock.sys.hud = SimpleNamespace(pro_root={"focus": "hud"})
        app_mock.agents["three_phase_bp"].generate.return_value = (
            {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}},
            {
                "final_verdict": "PASS",
                "last_score": 85,
                "phases": {
                    "generate": {"selected_strategy": "A", "selected_score": 85},
                    "validate": {
                        "verdict": "PASS",
                        "selection_reason": "후보 A가 감정선과 장면 연결이 가장 안정적",
                        "verdict_reason": "서사 리스크 없이 바로 사용 가능",
                        "open_review": "감정 여운을 한 템포 더 눌러주면 완성도가 올라간다",
                    },
                },
            },
        )
        semantic_bundle = {"semantic_ctx": "[ctx]", "blueprint_window": [{"ep_num": 1}, {"ep_num": 4}]}

        blueprint, pipeline_result = orch._run_stage3_blueprint_generation_handoff(
            working_ep=40,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            protagonist_name="장무기",
            protagonist_config={},
            entity_registry={},
            semantic_bundle=semantic_bundle,
        )

        kwargs = app_mock.agents["three_phase_bp"].generate.call_args.kwargs
        assert kwargs["prev_blueprints"] == semantic_bundle["blueprint_window"]
        assert "━━━ 제1화 원고 ━━━" in kwargs["prev_manuscripts_text"]
        assert "━━━ 제36화 원고 ━━━" in kwargs["prev_manuscripts_text"]
        assert "━━━ 제2화 원고 ━━━" not in kwargs["prev_manuscripts_text"]
        assert kwargs["prev_hud"] == {"focus": "hud"}
        assert blueprint == {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        assert pipeline_result["final_verdict"] == "PASS"
        log_texts = [call.args[0] for call in app_mock.ui.log.call_args_list if call.args]
        assert any("Blueprint 대기: ThreePhase runtime 호출 중" in text for text in log_texts)
        assert any("선택 전략: A" in text for text in log_texts)
        assert any("Director 판정: 서사 리스크 없이 바로 사용 가능" in text for text in log_texts)
        assert any("선택 근거: 후보 A가 감정선과 장면 연결이 가장 안정적" in text for text in log_texts)
        assert any("자유 리뷰: 감정 여운을 한 템포 더 눌러주면 완성도가 올라간다" in text for text in log_texts)

    def test_generate_blueprint_rejects_when_dead_npc_precheck_fails(self, orch, app_mock):
        app_mock.state_tracker = MagicMock()
        app_mock.state_tracker.check_dead_npc_in_blueprint.return_value = [
            {"npc_name": "흑풍", "reason": "deceased NPC scheduled for active present-time action"}
        ]

        app_mock.agents["three_phase_bp"].generate.return_value = (
            {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}},
            {
                "final_verdict": "PASS",
                "phases": {
                    "generate": {"selected_strategy": "A", "selected_score": 88},
                    "validate": {"verdict": "PASS", "issues_count": 0},
                },
            },
        )

        blueprint, pipeline_result = orch._run_stage3_blueprint_generation_handoff(
            working_ep=12,
            arc_data={"arc_no": 1, "title": "도입"},
            arc_idx=0,
            prev_blueprint=None,
            protagonist_name="장무기",
            protagonist_config={},
            entity_registry={},
            semantic_bundle={"semantic_ctx": "", "blueprint_window": []},
        )

        assert blueprint["integrated_scenario"] == "test"
        assert pipeline_result["final_verdict"] == "REJECT"
        assert pipeline_result["phases"]["validate"]["verdict"] == "REJECT"
        assert "dead_npc_precheck" in pipeline_result["reject_reason"]
        assert "흑풍" in pipeline_result["reject_reason"]
        assert pipeline_result["precheck_failures"][0]["npc_name"] == "흑풍"
        assert "dead_npc_precheck" in pipeline_result["phases"]["validate"]["contradictions"][0]

    def test_build_stage3_reject_reason_prefers_explicit_reject_reason(self):
        reason = Stage3Orchestrator._build_stage3_reject_reason(
            {
                "reject_reason": "dead_npc_precheck: deceased NPC '흑풍' assigned active present-time role in blueprint",
                "phases": {
                    "validate": {
                        "verdict": "REJECT",
                        "issues_count": 1,
                        "contradictions": [
                            "dead_npc_precheck: deceased NPC '흑풍' assigned active present-time role in blueprint"
                        ],
                    }
                },
            }
        )

        assert "dead_npc_precheck" in reason
        assert "흑풍" in reason
        assert "validate_verdict=REJECT" in reason
        assert "issues=1" in reason

    def test_build_stage3_success_operator_lines_includes_advisory_without_caps(self):
        lines = Stage3Orchestrator._build_stage3_success_operator_lines(
            {
                "final_verdict": "PASS",
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selection_reason": "후보 B가 감정선 연결과 액션 템포를 가장 안정적으로 살린다",
                        "verdict_reason": "구조 리스크 없이 바로 채택 가능",
                        "comparison_notes": "후보 C보다 감정 전이가 자연스럽다",
                        "fix_scope_reasoning": "마지막 비트의 여운만 후속 원고에서 더 밀어주면 된다",
                        "selected_candidate_advisory": {
                            "python_warnings": [{"message": "Arc NPC 언급 밀도가 낮아 후반 회상 씬에서 보강 권장"}]
                        },
                    }
                },
            }
        )

        assert "      └─ Director 판정: 구조 리스크 없이 바로 채택 가능" in lines
        assert "      선택 근거: 후보 B가 감정선 연결과 액션 템포를 가장 안정적으로 살린다" in lines
        assert "      비교 메모: 후보 C보다 감정 전이가 자연스럽다" in lines
        assert "      보완 포인트: 마지막 비트의 여운만 후속 원고에서 더 밀어주면 된다" in lines
        assert "      주의: Arc NPC 언급 밀도가 낮아 후반 회상 씬에서 보강 권장" in lines

    def test_finalize_stage3_blueprint_pipeline_result_normalizes_non_dict_result(self, orch):
        semantic_bundle = {
            "semantic_ctx": "[ctx]",
            "work_focus": {"tracking_slots": ["핵심 배우 라인"]},
            "plan": SimpleNamespace(slots=["a", "b"]),
            "source_counts": {"vec_memory": 2, "db_npc_relationship": 1, "bad": "skip"},
            "coverage_warnings": ["missing_relation_slice"],
            "observation": {
                "provenance_ledger": {"source_pack": "stage3"},
                "budget_ledger": {"budget_bucket": "smart_retrieval.stage3_total_budget"},
                "source_anchor_summary": {
                    "previous_blueprint_ep": 1,
                    "current_arc_start_location": "SW인베스트먼트 사무실",
                },
            },
        }

        with (
            patch("modules.core.stage3_orchestrator._time.perf_counter", return_value=11.5),
            patch("modules.core.stage3_orchestrator._peek_scope_total_cost_usd", return_value=1.75),
        ):
            result = orch._finalize_stage3_blueprint_pipeline_result(
                pipeline_result=None,
                started_at=10.0,
                started_cost_usd=1.25,
                semantic_bundle=semantic_bundle,
            )

        assert result["final_verdict"] == "ERROR"
        assert result["error"] == "invalid_pipeline_result"
        assert result["_stage3_duration_ms"] == 1500
        assert result["_stage3_token_cost_usd"] == 0.5
        assert result["_stage3_observability"]["source_counts"] == {
            "vec_memory": 2,
            "db_npc_relationship": 1,
        }
        assert result["_stage3_observability"]["planned_slots_count"] == 2
        assert result["_stage3_observability"]["provenance_ledger"]["source_pack"] == "stage3"
        assert result["_stage3_observability"]["source_anchor_summary"]["previous_blueprint_ep"] == 1


# ── Single Episode Processing ────────────────────────────────


class TestProcessSingleEpisode:
    def test_skip_existing_blueprint(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = {"existing": True}
        result = orch._process_single_episode(1, 5, [], 0, 0)
        assert result["next_ep"] == 2

    def test_continuity_block(self, orch, app_mock):
        """직전 화 Blueprint 없으면 중단"""

        # ep 1 exists, ep 2 does not
        def get_bp(ep):
            if ep == 1:
                return None  # ep 1 missing (for ep=2 check)
            return None

        app_mock.current_project.get_blueprint.side_effect = get_bp
        result = orch._process_single_episode(2, 5, [], 0, 0)
        assert result.get("break") is True

    def test_no_arc_context_breaks(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = None
        app_mock._get_arc_context_for_episode.return_value = (None, None)
        result = orch._process_single_episode(1, 5, [], 0, 0)
        assert result.get("break") is True

    def test_pass_with_fix_uses_success_path(self, orch, app_mock):
        app_mock.current_project.get_blueprint.return_value = None
        orch._get_entity_registry = MagicMock(return_value={"characters": []})
        orch._load_prev_blueprint = MagicMock(return_value=None)
        orch._get_protagonist_name_safe = MagicMock(return_value="주인공")
        orch._generate_blueprint = MagicMock(
            return_value=(
                {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}},
                {"final_verdict": "PASS_WITH_FIX"},
            )
        )
        orch._handle_success = MagicMock(return_value={"path": "success"})
        orch._handle_failure = MagicMock(return_value={"path": "failure"})

        result = orch._process_single_episode(1, 5, [], 0, 0)

        assert result == {"path": "success"}
        orch._handle_success.assert_called_once()
        orch._handle_failure.assert_not_called()

    def test_stage3_success_records_pass_rate_monitor(self, orch, app_mock):
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 87,
            "retries": 1,
            "phases": {
                "generate": {"selected_score": 87, "selected_strategy": "A"},
                "validate": {
                    "selected_candidate_advisory": {"issue_count": 4},
                    "binding_prevalidation_issue_count": 1,
                },
            },
            "_stage3_duration_ms": 4321,
            "_stage3_token_cost_usd": 0.123,
        }

        orch._handle_success(3, 1, {}, blueprint, pipeline_result, [], 0, 0)

        kw = app_mock.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["stage"] == 3
        assert kw["success"] is True
        assert kw["final_verdict"] == "PASS"
        assert kw["attempt_key"] == "s3:ep3:arc1:a2"
        assert kw["duration_ms"] == 4321
        assert kw["token_cost"] == 0.123
        app_mock.pass_rate_monitor._save_records.assert_called_once()
        log_texts = [call.args[0] for call in app_mock.ui.log.call_args_list if call.args]
        assert any("blueprint success (verdict=PASS, strategy=A, score=87)" in text for text in log_texts)
        assert any(
            "[Stage3 Summary] ep 3 | verdict=PASS | score=87 | attempt=2 | prevalidation=4 | binding=1 | TF-49=0 | PinGuard=0"
            in text
            for text in log_texts
        )

    def test_stage3_success_records_pass_rate_monitor_for_pass_with_fix(self, orch, app_mock):
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {
            "final_verdict": "PASS_WITH_FIX",
            "last_score": 89,
            "revision_required": True,
            "phases": {
                "generate": {"selected_score": 89, "selected_strategy": "A"},
                "validate": {
                    "verdict": "PASS_WITH_FIX",
                    "fix_pack": {
                        "must_fix": ["preserve the opening continuity packet"],
                        "success_condition": "the opening packet survives the patch pass",
                    },
                },
            },
        }

        orch._handle_success(3, 1, {}, blueprint, pipeline_result, [], 0, 0)

        kw = app_mock.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["stage"] == 3
        assert kw["success"] is True
        assert kw["final_verdict"] == "PASS_WITH_FIX"

    def test_stage3_failure_records_pass_rate_monitor(self, orch, app_mock):
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": 41,
            "phases": {"generate": {"selected_score": 41, "selected_strategy": "B"}},
            "_stage3_duration_ms": 987,
            "_stage3_token_cost_usd": 0.456,
        }

        orch._handle_failure(4, pipeline_result, 0, 0, arc_no=2)

        kw = app_mock.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["stage"] == 3
        assert kw["success"] is False
        assert kw["final_verdict"] == "REJECT"
        assert kw["attempt_key"] == "s3:ep4:arc2:a1"
        assert kw["duration_ms"] == 987
        assert kw["token_cost"] == 0.456
        app_mock.pass_rate_monitor._save_records.assert_called_once()
        log_texts = [call.args[0] for call in app_mock.ui.log.call_args_list if call.args]
        assert any("REJECT 사유:" in text for text in log_texts)
        assert any("category=" in text and "strategy=B" in text for text in log_texts)

    def test_stage3_reject_cost_record_uses_metrics_session_id_when_available(self, orch, app_mock):
        app_mock.current_project.metrics_session_id = "sess_stage3_reject"
        pipeline_result = {"final_verdict": "REJECT", "last_score": 41, "phases": {"generate": {"selected_score": 41}}}

        orch._handle_failure(4, pipeline_result, 0, 0, arc_no=2)

        cost_kw = app_mock.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kw["session_id"] == "sess_stage3_reject"

    def test_stage3_failure_appends_rejection_history_for_stage3_to_2_feedback(self, orch, app_mock):
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": 41,
            "specific_issue": "scene order drift",
            "fix_scope": "arc",
            "phases": {
                "generate": {"selected_strategy": "B", "selected_score": 41},
                "validate": {
                    "issues_count": 2,
                    "score_breakdown": {"scene_flow": 8, "note": "ignore"},
                },
            },
        }

        orch._handle_failure(4, pipeline_result, 0, 0, arc_no=2)

        assert len(app_mock.stage_rejection_history) == 1
        entry = app_mock.stage_rejection_history[0]
        assert entry["stage"] == 3
        assert entry["arc_no"] == 2
        assert entry["attempt"] == 1
        assert entry["specific_issue"] == "scene order drift"
        assert entry["failure_category"] == "validation_issue"
        assert entry["fix_scope"] == "arc"
        assert entry["score_breakdown"] == {"scene_flow": 8}
        assert "score=41" in entry["reason"]
        assert "strategy=B" in entry["reason"]

    def test_stage3_attempt_key_uses_metrics_session_id_when_available(self, orch, app_mock):
        app_mock.current_project.metrics_session_id = "sess_stage3"
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {"final_verdict": "PASS", "last_score": 87, "phases": {"generate": {"selected_score": 87}}}

        orch._handle_success(3, 1, {}, blueprint, pipeline_result, [], 0, 0)

        kw = app_mock.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["attempt_key"] == "s3:ep3:arc1:a1:sess_stage3"
        db_kw = app_mock.current_project.db.save_stage_attempt.call_args.kwargs
        assert db_kw["attempt_key"] == "s3:ep3:arc1:a1:sess_stage3"
        assert db_kw["session_id"] == "sess_stage3"

    def test_stage3_success_persists_artifact_linkage(self, orch, app_mock, tmp_path):
        app_mock.current_project.paths = MagicMock()
        app_mock.current_project.paths.root = tmp_path
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 87,
            "phases": {"generate": {"selected_strategy": "A", "selected_score": 87}},
        }

        orch._handle_success(3, 1, {}, blueprint, pipeline_result, [], 0, 0)

        prm_kw = app_mock.pass_rate_monitor.record_attempt.call_args.kwargs
        db_kw = app_mock.current_project.db.save_stage_attempt.call_args.kwargs

        assert prm_kw["candidate_key"] == "A"
        assert prm_kw["content_hash"]
        assert prm_kw["artifact_path"].endswith("final_blueprint__A.json")
        assert (tmp_path / prm_kw["artifact_path"]).exists()
        assert db_kw["artifact_path"] == prm_kw["artifact_path"]

    def test_stage3_success_logs_episode_summary(self, orch, app_mock, caplog):
        app_mock.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "3인칭", "external_pov_insert_policy": "제한적 허용"}}
        }
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 87,
            "_stage3_observability": {"work_focus_present": True, "planned_slots_count": 2},
            "phases": {"generate": {"selected_strategy": "A", "selected_score": 87}},
        }

        with caplog.at_level(logging.INFO):
            orch._handle_success(3, 1, {}, blueprint, pipeline_result, [], 0, 0)

        assert "[STAGE3_EPISODE_SUMMARY]" in caplog.text
        assert "attempt_key=s3:ep3:arc1:a1" in caplog.text
        assert "strategy=A" in caplog.text
        assert "candidate_key=A" in caplog.text
        assert "primary_pov=3인칭" in caplog.text
        assert "external_pov_insert_policy=제한적 허용" in caplog.text
        assert "style_guide_extracted_pov=-" in caplog.text

    def test_stage3_failure_logs_episode_summary(self, orch, app_mock, caplog):
        app_mock.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "1인칭", "external_pov_insert_policy": "금지"}}
        }
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": 41,
            "reject_reason": "continuity problem",
            "_stage3_observability": {"work_focus_present": True},
            "phases": {"generate": {"selected_strategy": "B", "selected_score": 41}},
        }

        with caplog.at_level(logging.INFO):
            orch._handle_failure(4, pipeline_result, 0, 0, arc_no=2)

        assert "[STAGE3_EPISODE_SUMMARY]" in caplog.text
        assert "attempt_key=s3:ep4:arc2:a1" in caplog.text
        assert "failure=continuity" in caplog.text
        assert "candidate_key=B" in caplog.text
        assert "primary_pov=1인칭" in caplog.text
        assert "external_pov_insert_policy=금지" in caplog.text
        assert "style_guide_extracted_pov=-" in caplog.text

    def test_stage3_attempt_evidence_packet_normalizes_shared_runtime_fields(self, orch, app_mock):
        blueprint = {"integrated_scenario": "test", "scene_breakdown": {"s1": "scene"}}
        pipeline_result = {
            "final_verdict": "REJECT",
            "last_score": "41",
            "quality_risk": True,
            "phases": {
                "generate": {"selected_strategy": "B", "selected_score": 41},
                "validate": {
                    "verdict": "REJECT",
                    "selection_reason": "후보 B가 그나마 구조적으로 읽힌다",
                    "verdict_reason": "opening continuity drift",
                    "fix_scope": "targeted",
                },
            },
        }

        packet = orch._build_stage3_attempt_evidence_packet(
            working_ep=4,
            arc_no=2,
            blueprint=blueprint,
            pipeline_result=pipeline_result,
            observability_flags={"semantic_ctx_chars": 120},
            artifact_kind="selected_blueprint",
            reject_reason="opening continuity drift",
        )

        assert isinstance(packet, Stage3AttemptEvidencePacket)
        assert packet.attempt_key == "s3:ep4:arc2:a1"
        assert packet.candidate_key == "B"
        assert packet.score == 41
        assert packet.selection_kwargs["attempt_key"] == packet.attempt_key
        assert packet.selection_kwargs["runtime_advisory"] == "opening continuity drift"
        assert packet.retry_directives == "opening continuity drift"
        assert packet.artifact_meta["candidate_key"] == "B"
        assert packet.selection_kwargs["verdict"] == "REJECT"

    def test_stage3_director_selection_kwargs_preserve_initial_verdict_over_final_override(self, orch):
        payload = Stage3Orchestrator._build_stage3_director_selection_kwargs(
            {
                "final_verdict": "REJECT",
                "phases": {
                    "validate": {
                        "verdict": "PASS",
                        "selection_reason": "candidate B is structurally strongest",
                        "verdict_reason": "quality gate downgraded later",
                        "selected_index": 1,
                        "candidate_count": 2,
                    }
                },
            },
            ep_num=9,
            attempt_num=2,
            attempt_key="s3:ep9:arc2:a2",
            selected_strategy="B",
            score=84,
            candidate_key="B",
        )

        assert payload is not None
        assert payload["verdict"] == "PASS"

    def test_stage3_sink_payload_builders_share_packet_contract(self, orch):
        packet = Stage3AttemptEvidencePacket(
            db=MagicMock(),
            attempt_num=2,
            session_id="stage3-session",
            attempt_key="s3:ep6:arc3:a2",
            score=87,
            selected_strategy="B",
            candidate_key="B",
            artifact_meta={
                "candidate_key": "B",
                "content_hash": "hash-stage3",
                "artifact_path": "logs/artifacts/stage3/ep006.json",
            },
            selection_kwargs={
                "selection_reason": "후보 B가 opening continuity를 가장 안정적으로 유지",
                "verdict_reason": "local repair로 충분",
                "fix_scope": "inplace",
                "fix_scope_reasoning": "opening continuity와 수치 앵커만 보강",
            },
            runtime_advisory="opening continuity drift review",
            retry_directives="preserve the opening continuity packet on the next retry",
        )

        decision_kwargs = orch._build_stage3_session_decision_kwargs(
            ep_num=6,
            verdict="PASS_WITH_FIX",
            score=87,
            arc_no=3,
            quality_risk=True,
            packet=packet,
            validate={
                "fix_pack": {
                    "patch_targets": ["scene_2.summary"],
                    "target_kind": "scene_block",
                    "subtype": "movement",
                    "provenance": "director_authored",
                },
                "repair_contract": {
                    "subtype": "movement",
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "provenance": "director_authored",
                    "target_kind": "scene_block",
                },
                "scope_authority": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "widened": False,
                },
                "comparison_notes": "후보 B가 opening continuity와 자본 패킷 계승을 가장 안정적으로 유지",
                "selected_candidate_advisory": {
                    "candidate_index": 1,
                    "quality_risk": True,
                    "python_warnings": [{"category": "continuity", "message": "opening beat needs a tighter relay"}],
                },
            },
            reason="local repair로 충분",
            selection_reason=packet.selection_kwargs["selection_reason"],
            verdict_reason=packet.selection_kwargs["verdict_reason"],
            fix_scope=packet.selection_kwargs["fix_scope"],
        )
        stage_attempt_kwargs = orch._build_stage3_stage_attempt_kwargs(
            ep_num=6,
            arc_no=3,
            verdict="PASS_WITH_FIX",
            packet=packet,
            model="gpt-test",
            prompt_version="stage3.vtest",
            duration_ms=3210,
            advisory_flags={"semantic_ctx_chars": 1440},
            validate={
                "verdict": "PASS_WITH_FIX",
                "open_review": "opening continuity 재검토",
                "fix_pack": {
                    "patch_targets": ["scene_2.summary"],
                    "target_kind": "scene_block",
                    "subtype": "movement",
                    "provenance": "director_authored",
                },
                "repair_contract": {
                    "subtype": "movement",
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "provenance": "director_authored",
                    "target_kind": "scene_block",
                },
                "scope_authority": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "widened": False,
                },
                "comparison_notes": "후보 B가 opening continuity와 자본 패킷 계승을 가장 안정적으로 유지",
                "selected_candidate_advisory": {
                    "candidate_index": 1,
                    "quality_risk": True,
                    "python_warnings": [{"category": "continuity", "message": "opening beat needs a tighter relay"}],
                },
            },
            failure_category="quality_gate",
            reject_reason="opening continuity drift",
        )
        pass_rate_kwargs = orch._build_stage3_pass_rate_attempt_kwargs(
            working_ep=6,
            arc_no=3,
            packet=packet,
            success=False,
            duration_ms=3210,
            token_cost=0.123,
            final_verdict="REJECT",
            score_breakdown={"continuity": 62},
            reject_reason="opening continuity drift",
        )

        assert decision_kwargs["attempt_key"] == packet.attempt_key
        assert decision_kwargs["candidate_key"] == "B"
        assert decision_kwargs["runtime_advisory"] == packet.runtime_advisory
        assert decision_kwargs["retry_directives"] == packet.retry_directives
        assert decision_kwargs["artifact_path"] == "logs/artifacts/stage3/ep006.json"
        assert decision_kwargs["repair_scope"] == "inplace"
        assert decision_kwargs["authoritative_fix_scope"] == "inplace"
        assert decision_kwargs["repair_contract"]["subtype"] == "movement"
        assert decision_kwargs["scope_authority"]["widened"] is False
        assert (
            decision_kwargs["comparison_notes"] == "후보 B가 opening continuity와 자본 패킷 계승을 가장 안정적으로 유지"
        )
        assert decision_kwargs["selected_candidate_advisory_struct"]["quality_risk"] is True
        assert stage_attempt_kwargs["session_id"] == packet.session_id
        assert stage_attempt_kwargs["attempt_key"] == packet.attempt_key
        assert stage_attempt_kwargs["candidate_key"] == packet.candidate_key
        assert stage_attempt_kwargs["selection_reason"] == packet.selection_kwargs["selection_reason"]
        assert stage_attempt_kwargs["runtime_advisory"] == packet.runtime_advisory
        assert stage_attempt_kwargs["retry_directives"] == packet.retry_directives
        assert stage_attempt_kwargs["failure_category"] == "quality_gate"
        assert stage_attempt_kwargs["reject_reason"] == "opening continuity drift"
        assert stage_attempt_kwargs["open_review"] == "opening continuity 재검토"
        assert stage_attempt_kwargs["initial_verdict"] == "PASS_WITH_FIX"
        assert (
            stage_attempt_kwargs["advisory_flags"]["comparison_notes"]
            == "후보 B가 opening continuity와 자본 패킷 계승을 가장 안정적으로 유지"
        )
        assert stage_attempt_kwargs["advisory_flags"]["selected_candidate_advisory_struct"]["candidate_index"] == 1
        assert stage_attempt_kwargs["advisory_flags"]["fix_pack"]["subtype"] == "movement"
        assert stage_attempt_kwargs["advisory_flags"]["repair_contract"]["provenance"] == "director_authored"
        assert stage_attempt_kwargs["advisory_flags"]["gate_semantics"]["repair_contract"]["subtype"] == "movement"
        assert stage_attempt_kwargs["advisory_flags"]["scope_authority"]["widened"] is False
        assert pass_rate_kwargs["attempt_key"] == packet.attempt_key
        assert pass_rate_kwargs["candidate_key"] == packet.candidate_key
        assert pass_rate_kwargs["content_hash"] == packet.artifact_meta["content_hash"]
        assert pass_rate_kwargs["artifact_path"] == packet.artifact_meta["artifact_path"]
        assert pass_rate_kwargs["success"] is False
        assert pass_rate_kwargs["reject_reason"] == "opening continuity drift"
        assert pass_rate_kwargs["score_breakdown"] == {"continuity": 62}


# ── Result Handlers ──────────────────────────────────────────


class TestHandleSuccess:
    def test_saves_and_increments(self, orch, app_mock):
        bp = {"integrated_scenario": "text", "scene_breakdown": {"s1": "scene"}}
        pr = {"phases": {"generate": {"selected_strategy": "A", "selected_score": 85}}}
        prev_bps = []
        result = orch._handle_success(3, 1, {}, bp, pr, prev_bps, 2, 1)
        assert result["next_ep"] == 4
        assert result["success_count"] == 3
        assert result["fail_count"] == 0
        app_mock.current_project.save_episode_blueprint.assert_called_once_with(3, bp)
        app_mock._safe_commit.assert_called_once()

    def test_integrity_fail_skips(self, orch, app_mock):
        app_mock._validate_blueprint_integrity.return_value = False
        bp = {"bad": True}
        pr = {}
        result = orch._handle_success(3, 1, {}, bp, pr, [], 2, 0)
        assert result["fail_count"] == 1
        app_mock.current_project.save_episode_blueprint.assert_not_called()

    def test_unresolved_continuity_pins_do_not_discard_blueprint(self, orch, app_mock):
        bp = {"integrated_scenario": "text", "scene_breakdown": {"s1": "scene"}}
        pr = {"phases": {"generate": {"selected_strategy": "A", "selected_score": 85}}}

        with patch(
            "modules.core.stage3_orchestrator.apply_continuity_pins",
            return_value={"blueprint": bp, "changes": [], "unresolved": [{"type": "proper_noun_pin"}]},
        ):
            result = orch._handle_success(3, 1, {"tactical_doc": ""}, bp, pr, [], 0, 0)

        assert result["success_count"] == 1
        assert bp["_continuity_pin_unresolved"][0]["type"] == "proper_noun_pin"
        app_mock.current_project.save_episode_blueprint.assert_called_once_with(3, bp)
        app_mock._audit_event.assert_called()


class TestHandleFailure:
    def test_increments_fail_count(self, orch, app_mock):
        pr = {"final_verdict": "FAIL"}
        result = orch._handle_failure(3, pr, 2, 1)
        assert result["fail_count"] == 2

    def test_three_consecutive_fails_breaks(self, orch, app_mock):
        pr = {"final_verdict": "FAIL"}
        result = orch._handle_failure(3, pr, 0, 2)  # 2 + 1 = 3
        assert result["fail_count"] == 3
        assert result.get("break") is True


# ── Main Entry Point ─────────────────────────────────────────


class TestStage3BatchBlueprintingEntryPoint:
    def test_no_arcs_returns_early(self, app_mock):
        app_mock.current_project.arcs = []
        orch = Stage3Orchestrator(app=app_mock)
        orch.stage_3_batch_blueprinting()
        app_mock._write_audit_summary.assert_not_called()

    def test_full_run_single_episode(self, orch, app_mock):
        """1화짜리 전체 플로우 — 성공 경로"""
        # target_ep=5, production_head=0 → working_ep=1
        # _get_int_input returns 1 (1화만 생성)
        app_mock._get_int_input.return_value = 1

        with patch("modules.core.spinners.StageSpinner"):
            orch.stage_3_batch_blueprinting()

        app_mock._write_audit_summary.assert_called_once_with("stage3_complete")
        app_mock.current_project.save_episode_blueprint.assert_called_once()

    def test_break_path_does_not_write_completion_summary(self, app_mock):
        app_mock._get_int_input.return_value = 1
        orch = Stage3Orchestrator(app=app_mock)
        orch._process_single_episode = MagicMock(
            return_value={"next_ep": 1, "success_count": 0, "fail_count": 1, "break": True}
        )

        orch.stage_3_batch_blueprinting()

        app_mock._write_audit_summary.assert_not_called()

    def test_completion_stats_separate_session_and_cumulative_pass_rates(self, app_mock):
        app_mock._get_int_input.return_value = 1
        app_mock.agents["three_phase_bp"].get_stats.return_value = {"pass_rate": "50.0%"}
        orch = Stage3Orchestrator(app=app_mock)
        orch._process_single_episode = MagicMock(
            return_value={"next_ep": 2, "success_count": 1, "fail_count": 0, "break": False}
        )

        with patch("modules.core.spinners.StageSpinner"):
            orch.stage_3_batch_blueprinting()

        log_texts = [call.args[0] for call in app_mock.ui.log.call_args_list]
        assert any("이번 실행 통과율: 100.0%" in text for text in log_texts)
        assert any("누적 통과율: 50.0%" in text for text in log_texts)


def test_stage3_work_focus_advisory_preserves_tail_context(app_mock):
    app_mock.current_project.db.get_relationship_history.return_value = []

    with patch("modules.core.stage3_orchestrator.SemanticQueryBroker") as broker_cls:
        broker_cls.return_value.build_relation_slice.return_value = "[관계 의미 질의]\n" + ("R" * 220) + "TAIL-REL"
        text = _build_stage3_work_focus_advisory(
            {
                "tracking_slots": ["head-slot"],
                "mandatory_scene_engines": ["scene-engine"],
                "registry_profiles": [],
            },
            arc_data={"constraint_summary": "conflict"},
            entity_registry={"characters": [{"name": "alice"}, {"name": "bob"}]},
            ctx=app_mock,
            protagonist_name="hero",
            max_chars=180,
        )

    assert len(text) <= 180
    assert "TAIL-REL" in text

    def test_target_prompt_uses_hybrid_project_head(self, app_mock):
        app_mock.current_project.db.get_latest_blueprint_number.return_value = 0
        app_mock.current_project.get_latest_episode_number = MagicMock(return_value=4)
        app_mock._get_max_episode_from_manuscripts.return_value = 0
        app_mock._get_int_input.return_value = 4

        orch = Stage3Orchestrator(app=app_mock)
        orch._process_single_episode = MagicMock(
            return_value={"next_ep": 5, "success_count": 1, "fail_count": 0, "break": True}
        )

        orch.stage_3_batch_blueprinting()

        call = app_mock._get_int_input.call_args
        assert "현재 3화" in call.args[0]
        assert call.kwargs["min_val"] == 4
        assert call.kwargs["max_val"] == 5

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_prev_manuscripts_preserve_recent_tail_context(self, MockSpinner, orch, app_mock, monkeypatch):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = [
            {"ep_num": 1, "content": "HEAD-MS\n" + ("M" * 500) + "\nTAIL-MS"}
        ]

        import modules.core.stage3_orchestrator as mod

        monkeypatch.setattr(mod.ContextLimits, "MAX_CONTEXT_CHARS", 220)

        orch._generate_blueprint(
            working_ep=2,
            arc_data=app_mock.current_project.arcs[0],
            arc_idx=0,
            prev_blueprint=None,
            prev_blueprints=[],
            entity_registry={"characters": [{"name": "윤서아"}]},
            protagonist_name="장무기",
            protagonist_config={},
        )

        prev_ms = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["prev_manuscripts_text"]
        assert len(prev_ms) <= 220
        assert "TAIL-MS" in prev_ms

    @patch("modules.core.spinners.StageSpinner")
    def test_stage3_slot_max_preserves_recent_tail_context(self, MockSpinner, orch, app_mock):
        spinner = MagicMock()
        spinner.update_detail = MagicMock()
        MockSpinner.return_value.__enter__.return_value = spinner
        app_mock.current_project.db.get_recent_manuscripts.return_value = []
        app_mock.context_advisor = MagicMock()
        app_mock.memory = MagicMock()
        app_mock.memory.retrieve_multi_query_context.return_value = "HEAD-S3 " + ("S" * 260) + " TAIL-S3"
        app_mock.sys.guard = MagicMock()
        app_mock.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["핵심 배우 라인"],
            "mandatory_scene_engines": [],
            "registry_profiles": [],
        }
        app_mock.context_advisor.plan_stage3_retrieval.return_value = MagicMock(
            slots=[MagicMock(category="genre_context_1", query="genre query", source="vec_memory", max_chars=120)]
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage3_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 8
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect):
            orch._generate_blueprint(
                working_ep=1,
                arc_data=app_mock.current_project.arcs[0],
                arc_idx=0,
                prev_blueprint=None,
                prev_blueprints=[],
                entity_registry={"characters": [{"name": "윤서아"}]},
                protagonist_name="장무기",
                protagonist_config={},
            )

        semantic_context = app_mock.agents["three_phase_bp"].generate.call_args.kwargs["semantic_context"]
        sc_block = (
            semantic_context.split("[SC:genre_context_1]\n")[-1] if "[SC:genre_context_1]" in semantic_context else ""
        )
        assert len(sc_block) <= 120
        assert "TAIL-S3" in sc_block


# ── [Phase 4C-4] Stage3Context DI 테스트 ─────────────────────


class TestStage3ContextDI:
    def test_ctx_none_by_default(self, app_mock):
        """초기 _ctx=None"""
        orch = Stage3Orchestrator(app=app_mock)
        assert orch._ctx is None

    def test_ctx_auto_builds_from_app(self, app_mock):
        """property 접근 시 app에서 자동 빌드"""
        orch = Stage3Orchestrator(app=app_mock)
        ctx = orch.ctx
        assert isinstance(ctx, Stage3Context)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project

    def test_ctx_injected_at_init(self, app_mock):
        """context= 키워드로 주입"""
        ctx = Stage3Context(ui=app_mock.ui, current_project=app_mock.current_project)
        orch = Stage3Orchestrator(app=app_mock, context=ctx)
        assert orch.ctx is ctx

    def test_ctx_setter_replaces_context(self, app_mock):
        """ctx setter로 교체"""
        ctx = Stage3Context(ui=app_mock.ui, current_project=app_mock.current_project)
        orch = Stage3Orchestrator(app=app_mock)
        orch.ctx = ctx
        assert orch.ctx is ctx
        assert orch._ctx is ctx

    def test_get_protagonist_name_safe_uses_ctx(self, app_mock):
        """_get_protagonist_name_safe가 ctx.get_protagonist_name 경유"""
        cb = MagicMock(return_value="장무기")
        ctx = Stage3Context(
            ui=app_mock.ui,
            current_project=app_mock.current_project,
            get_protagonist_name=cb,
        )
        orch = Stage3Orchestrator(app=app_mock, context=ctx)
        result = orch._get_protagonist_name_safe()
        cb.assert_called_once()
        assert result == "장무기"

    def test_from_app_all_slots(self):
        """from_app이 Stage3Context 슬롯 전부 매핑하는지 확인"""
        fake_app = SimpleNamespace(
            ui=MagicMock(),
            current_project=MagicMock(),
            agents={"three_phase_bp": MagicMock()},
            sys=MagicMock(),
            state_tracker=MagicMock(),
            memory=MagicMock(),
            context_advisor=MagicMock(),
            world_state=MagicMock(),
            fact_ledger=MagicMock(),
            adversarial_self_play=MagicMock(),
            preset_registry=MagicMock(),
            selected_genre={"type": "wuxia"},
            pass_rate_monitor=MagicMock(),
            _get_protagonist_name=MagicMock(),
            _audit_event=MagicMock(),
            _write_audit_summary=MagicMock(),
            _get_arc_context_for_episode=MagicMock(),
            _get_max_episode_from_manuscripts=MagicMock(),
            _get_int_input=MagicMock(),
            _safe_commit=MagicMock(),
            _validate_arc_data_fields=MagicMock(),
            _validate_blueprint_integrity=MagicMock(),
            _fix_entity_registry_protagonist=MagicMock(),
            _session_logger=MagicMock(),
        )
        ctx = Stage3Context.from_app(fake_app)
        assert ctx.ui is fake_app.ui
        assert ctx.current_project is fake_app.current_project
        assert ctx.agents is fake_app.agents
        assert ctx.sys is fake_app.sys
        assert ctx.state_tracker is fake_app.state_tracker
        assert ctx.memory is fake_app.memory
        assert ctx.context_advisor is fake_app.context_advisor
        assert ctx.world_state is fake_app.world_state
        assert ctx.fact_ledger is fake_app.fact_ledger
        assert ctx.adversarial_self_play is fake_app.adversarial_self_play
        assert ctx.preset_registry is fake_app.preset_registry
        assert ctx.selected_genre is fake_app.selected_genre
        assert ctx.pass_rate_monitor is fake_app.pass_rate_monitor
        assert ctx.get_protagonist_name is fake_app._get_protagonist_name
        assert ctx.audit_event is fake_app._audit_event
        assert ctx.write_audit_summary is fake_app._write_audit_summary
        assert ctx.get_arc_context_for_episode is fake_app._get_arc_context_for_episode
        assert ctx.get_max_episode_from_manuscripts is fake_app._get_max_episode_from_manuscripts
        assert ctx.get_int_input is fake_app._get_int_input
        assert ctx.safe_commit is fake_app._safe_commit
        assert ctx.validate_arc_data_fields is fake_app._validate_arc_data_fields
        assert ctx.validate_blueprint_integrity is fake_app._validate_blueprint_integrity
        assert ctx.fix_entity_registry_protagonist is fake_app._fix_entity_registry_protagonist
        assert ctx.session_logger is fake_app._session_logger

    def test_from_app_binds_real_validation_methods(self):
        class RealApp:
            def __init__(self):
                self.ui = MagicMock()
                self.current_project = MagicMock()
                self.agents = {"three_phase_bp": MagicMock()}
                self.sys = MagicMock()
                self.state_tracker = MagicMock()
                self.validation_calls = []
                self.blueprint_calls = []

            def _validate_arc_data_fields(self, arc_data, arc_idx):
                self.validation_calls.append((arc_idx, arc_data.get("arc_no")))
                return {**arc_data, "arc_no": arc_idx}

            def _validate_blueprint_integrity(self, blueprint):
                self.blueprint_calls.append(blueprint.get("integrated_scenario"))
                return True

        app = RealApp()

        ctx = Stage3Context.from_app(app)

        assert ctx.validate_arc_data_fields.__self__ is app
        assert ctx.validate_blueprint_integrity.__self__ is app
        assert ctx.validate_arc_data_fields({"arc_no": 99}, 4)["arc_no"] == 4
        assert ctx.validate_blueprint_integrity({"integrated_scenario": "ok"}) is True
        assert app.validation_calls == [(4, 99)]
        assert app.blueprint_calls == ["ok"]

    def test_slots_count_20(self):
        """__slots__ 개수 검증"""
        assert len(Stage3Context.__slots__) == 24  # memory + context_advisor + session_logger

    def test_ctx_sync_after_lazy_init(self, app_mock):
        """lazy init 후 state_tracker/world_state/fact_ledger가 ctx에 sync되는지 확인"""
        app_mock.state_tracker = None
        app_mock.world_state = None
        app_mock.fact_ledger = None
        app_mock._get_int_input.return_value = 1

        orch = Stage3Orchestrator(app=app_mock)

        with (
            patch("modules.domain.agents.state_tracker.StateTracker") as MockST,
            patch("modules.core.world_state.WorldStateManager") as MockWS,
            patch("modules.core.fact_ledger.FactLedger") as MockFL,
            patch("modules.core.spinners.StageSpinner"),
        ):
            mock_st = MagicMock(npc_registry={})
            MockST.return_value = mock_st
            mock_ws = MagicMock(last_updated_ep=0)
            MockWS.return_value = mock_ws
            mock_fl = MagicMock(last_updated_ep=0)
            MockFL.return_value = mock_fl

            orch.stage_3_batch_blueprinting()

        assert orch.ctx.state_tracker is mock_st
        assert orch.ctx.world_state is mock_ws
        assert orch.ctx.fact_ledger is mock_fl

    def test_backward_compat_app_still_works(self, app_mock):
        """self.app 접근 유지 (레거시 호환)"""
        orch = Stage3Orchestrator(app=app_mock)
        assert orch.app is app_mock

    def test_none_callbacks_do_not_raise_type_error(self, app_mock):
        """[G-1] DI 콜백이 None이어도 callable 가드로 TypeError 없이 종료."""
        ctx = Stage3Context.from_app(app_mock)
        ctx.get_max_episode_from_manuscripts = None
        ctx.get_int_input = None
        ctx.write_audit_summary = None
        ctx.get_arc_context_for_episode = None
        ctx.get_protagonist_name = None
        orch = Stage3Orchestrator(app=app_mock, context=ctx)

        orch.stage_3_batch_blueprinting()

        app_mock._write_audit_summary.assert_not_called()


def test_stage3_failure_attempt_survives_session_logger_failure(orch, app_mock, tmp_path):
    app_mock._session_logger.log_decision.side_effect = RuntimeError("logger down")
    app_mock.current_project.paths = MagicMock()
    app_mock.current_project.paths.root = tmp_path
    pipeline_result = {
        "final_verdict": "REJECT",
        "last_score": 44,
        "phases": {
            "generate": {"selected_strategy": "action_focused", "selected_score": 44},
            "validate": {
                "phase": "director_compare",
                "selected_index": 0,
                "comparison_notes": "후보 1이 상대적으로 낫지만 전면 재설계가 필요함",
                "verdict": "REJECT",
                "feedback": "전술 사건 재배치 필요",
                "fix_scope": "full",
                "contradictions": ["timeline mismatch"],
            },
        },
        "_stage3_duration_ms": 987,
        "_stage3_observability": {
            "work_focus_present": True,
            "semantic_ctx_chars": 222,
            "source_counts": {"legacy_semantic_context": 1},
            "advisor_path_used": False,
        },
    }

    orch._handle_failure(
        working_ep=4,
        pipeline_result=pipeline_result,
        success_count=0,
        fail_count=0,
        arc_no=2,
        blueprint={"integrated_scenario": "candidate", "scene_breakdown": {"s1": "scene"}},
    )

    app_mock.pass_rate_monitor.record_attempt.assert_called_once()
    app_mock.current_project.db.save_stage_attempt.assert_called_once()
    app_mock.current_project.db.save_director_selection.assert_called_once()
