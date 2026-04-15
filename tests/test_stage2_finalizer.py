"""[B-1-7] Unit tests for Stage2Finalizer extracted from Stage2Orchestrator."""

import asyncio
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage2_context import Stage2Context
from modules.core.cross_stage_authority_packet import (
    CROSS_STAGE_AUTHORITY_PACKET_VERSION,
    build_cross_stage_authority_packet,
)
from modules.core.stage2_finalizer import (
    Stage2Finalizer,
    _build_stage2_carryover_authority_summary,
    _compute_inventory_carryover,
    _sync_first_episode_start_state_line,
    _sync_stage2_end_state_inventory_contract,
    _sync_stage2_end_location_contract,
)


@pytest.fixture
def finalizer_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.pass_rate_monitor = MagicMock()
    ctx.quality_dashboard = MagicMock()
    ctx.stage2_optimizer = MagicMock()
    ctx.stage2_optimizer.failure_memory = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.stage_rejection_history = []
    ctx.audit_event = MagicMock()
    ctx.semantic_plot_guard = None
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.validate_arc_data_fields = None
    ctx.current_project = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
    ctx.state_tracker = SimpleNamespace(foo=0, bar=0)

    director = MagicMock()
    director.audit_strategic_plan.return_value = {"decision": "PASS", "score": 95, "reason": "ok"}
    director.ask.return_value = "volume summary text long enough"
    ctx.agents = {"director": director}
    return ctx


@pytest.fixture
def finalizer(finalizer_ctx):
    host = MagicMock()
    host.ctx = finalizer_ctx
    return Stage2Finalizer(host)


@pytest.fixture
def valid_refined_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "A" * 1600,
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {
            "primary": "standard_progression",
            "secondary": [],
            "mixing_logic": "default",
        },
        "joint_docs": {
            "final_location": "market",
            "physical_inventory": [],
            "world_joint": "stable",
        },
        "status_shadow": {
            "internal_energy_loss": "10%",
            "expected_injuries": "none",
            "item_consumption": [],
        },
        "state_constraints": {"items_acquired": []},
    }


def _make_finalize_kwargs(refined_arc, **overrides):
    constraint_db = overrides.pop("constraint_db", MagicMock(arc_states=[]))
    defaults = {
        "refined_arc": refined_arc,
        "enriched_block": {
            "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
            "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
            "joint_docs_brief": "brief",
        },
        "arc_drive": {"desire_vector": "test"},
        "all_refined_arcs": [],
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_feedback": "",
        "protagonist_name": "hero",
        "suspected_duplicates": [],
        "entity_registry_for_director": {},
        "constraint_block": "",
        "draft_validator_passed": True,
        "consensus_passed": True,
        "attempt": 0,
        "generation_method": "four_phase",
        "st_snapshot": None,
        "director_feedback_for_fourphase": "",
        "last_refined_context": "prev context",
        "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "회귀자"}},
        "genre": "fantasy",
        "constraint_db": constraint_db,
    }
    defaults.update(overrides)
    return defaults


def test_build_stage2_carryover_authority_summary_surfaces_start_end_and_finance():
    refined_arc = {
        "joint_docs": {"final_location": "강남 오피스", "physical_inventory": ["법인 인감", "노트북"]},
        "semantic_carryover": {"continuity_checkpoints": ["회귀 유지"], "foreshadow_anchors": ["유가 급등"]},
        "state_constraints": {
            "arc_start_state": {
                "location": "성북동 본가",
                "equipment": ["구형 폴더폰", "지갑"],
                "total_assets": "약 20억원",
            },
            "arc_end_state": {
                "location": "강남 오피스",
                "equipment": ["법인 인감", "노트북"],
                "total_assets": "20억원",
                "capital": "20억원",
            },
            "investment_calc": {"final_total_assets": 2000000000, "final_cash": 2000000000},
        },
    }

    summary = _build_stage2_carryover_authority_summary(refined_arc)

    assert summary["start_location"] == "성북동 본가"
    assert summary["start_inventory_count"] == 2
    assert summary["end_location"] == "강남 오피스"
    assert summary["end_inventory_count"] == 2
    assert summary["investment_calc_final_total_assets"] == 2000000000
    assert "semantic_carryover_keys" in summary


def test_build_cross_stage_authority_packet_surfaces_stage2_transport_families():
    refined_arc = {
        "arc_no": 3,
        "ep_start": 8,
        "ep_end": 10,
        "joint_docs": {
            "final_location": "강남 오피스",
            "physical_inventory": ["법인 인감", "노트북"],
            "world_joint": "에콰도르 기사와 WTI 가격을 계속 추적 중",
        },
        "state_constraints": {
            "arc_end_state": {
                "location": "강남 오피스",
                "equipment": ["법인 인감", "노트북"],
                "injuries": "없음",
                "internal_energy": 100,
                "capital": "23억",
                "total_assets": "30억",
                "portfolio_position": "WTI long",
            },
            "investment_calc": {
                "final_total_assets": 3000000000,
                "final_cash": 2300000000,
            },
        },
    }

    packet = build_cross_stage_authority_packet(refined_arc)

    assert packet["contract_version"] == CROSS_STAGE_AUTHORITY_PACKET_VERSION
    assert packet["opening_carryover"]["location"] == "강남 오피스"
    assert packet["opening_carryover"]["world_joint"] == "에콰도르 기사와 WTI 가격을 계속 추적 중"
    assert packet["protagonist_carryover"]["equipment"] == ["법인 인감", "노트북"]
    assert packet["protagonist_carryover"]["injuries"] == "없음"
    assert packet["numeric_carryover"]["capital"] == "23억"
    assert packet["numeric_carryover"]["investment_calc_final_total_assets"] == 3000000000
    assert packet["source_precedence"]["opening_carryover"][0] == "state_constraints.arc_end_state.location"
    assert packet["provenance"]["emitted_by"] == "Stage2Finalizer"


def test_build_cross_stage_authority_packet_preserves_authoritative_empty_equipment_clear():
    refined_arc = {
        "joint_docs": {"physical_inventory": ["stale-bag"]},
        "state_constraints": {
            "arc_end_state": {
                "equipment": [],
            }
        },
    }

    packet = build_cross_stage_authority_packet(refined_arc)

    assert packet["protagonist_carryover"]["equipment"] == []
    assert packet["protagonist_carryover"]["equipment_source"] == "state_constraints.arc_end_state.equipment"


def test_build_stage2_carryover_authority_summary_preserves_authoritative_empty_end_inventory_clear():
    refined_arc = {
        "joint_docs": {"final_location": "강남 오피스", "physical_inventory": ["stale-bag"]},
        "state_constraints": {
            "arc_end_state": {
                "location": "강남 오피스",
                "equipment": [],
            }
        },
    }

    summary = _build_stage2_carryover_authority_summary(refined_arc)

    assert summary["end_location"] == "강남 오피스"
    assert "end_inventory_count" not in summary
    assert "end_inventory_preview" not in summary


def test_sync_stage2_end_inventory_contract_preserves_authoritative_empty_clear_against_prev_arc():
    refined_arc = {
        "joint_docs": {"physical_inventory": ["Ghost token"]},
        "status_shadow": {"item_consumption": []},
        "state_constraints": {
            "arc_end_state": {"equipment": []},
            "items_acquired": [],
        },
    }
    prev_arc = {"joint_docs": {"physical_inventory": ["Ghost token"]}}

    canonical_inventory, joint_changed, end_changed = _sync_stage2_end_state_inventory_contract(refined_arc, prev_arc)

    assert canonical_inventory == []
    assert joint_changed is True
    assert end_changed is False
    assert refined_arc["joint_docs"]["physical_inventory"] == []
    assert refined_arc["state_constraints"]["arc_end_state"]["equipment"] == []


class TestFinalizerStructure:
    def test_host_is_required_for_ctx_proxy(self):
        f = Stage2Finalizer(None)
        with pytest.raises(AttributeError):
            _ = f.ctx


class TestCommitSemantics:
    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda arc: arc)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_safe_commit_async_false_returns_retry_and_audit(self, _validate, finalizer, valid_refined_arc):
        finalizer.ctx.safe_commit_async = AsyncMock(return_value=False)
        finalizer.ctx.current_project.db.conn.in_transaction = False

        result = asyncio.run(finalizer.run_finalize(**_make_finalize_kwargs(valid_refined_arc)))

        assert result["action"] == "retry"
        assert any("Arc 1 저장 실패" in call.args[0] for call in finalizer.ctx.ui.log.call_args_list if call.args)
        finalizer.ctx.audit_event.assert_any_call(
            "db_commit_error",
            "arc save failed in async",
            {"arc_no": 1, "error": "safe_commit_async returned False"},
        )

    def test_prepare_stage2_pass_arc_for_persistence_strips_nonwuxia_state_noise_from_saved_arc(
        self,
        finalizer,
        valid_refined_arc,
    ):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {
                "location": "여의도 HQ",
                "equipment": [],
                "injuries": "없음",
                "internal_energy": 80,
                "realm": "후천",
            },
            "arc_end_state": {
                "location": "강남 HQ",
                "equipment": [],
                "injuries": "없음",
                "qi_nature": "청명",
                "martial_arts": ["비검술"],
            },
            "items_acquired": [],
        }

        result = finalizer._prepare_stage2_pass_arc_for_persistence(
            refined_arc=refined_arc,
            arc_drive={"desire_vector": "test"},
            enriched_block={
                "joint_docs": {"final_location": "강남 HQ", "physical_inventory": [], "world_joint": "stable"},
                "status_shadow": {
                    "internal_energy_loss": "5%",
                    "expected_injuries": "none",
                    "item_consumption": [],
                },
                "joint_docs_brief": "brief",
            },
            all_refined_arcs=[],
            global_arc_no=1,
            current_feedback="",
            generation_method="four_phase",
            st_snapshot=None,
            cdb_snapshot=None,
            constraint_db=MagicMock(arc_states=[]),
            constraint_block="",
            genre="investment",
        )

        assert result["action"] == "continue"
        saved_arc = result["refined_arc"]["state_constraints"]
        assert "internal_energy" not in saved_arc["arc_start_state"]
        assert "realm" not in saved_arc["arc_start_state"]
        assert "internal_energy" not in saved_arc["arc_end_state"]
        assert "qi_nature" not in saved_arc["arc_end_state"]
        assert "martial_arts" not in saved_arc["arc_end_state"]
        assert any(
            "[Non-Wuxia State Cleanup]" in call.args[0] for call in finalizer.ctx.ui.log.call_args_list if call.args
        )

    def test_prepare_stage2_pass_arc_for_persistence_keeps_wuxia_state_fields(
        self,
        finalizer,
        valid_refined_arc,
    ):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {
                "location": "청풍산장",
                "equipment": ["검"],
                "injuries": "없음",
                "internal_energy": 80,
                "realm": "후천",
            },
            "arc_end_state": {
                "location": "청풍산장 후원",
                "equipment": ["검"],
                "injuries": "경미한 타박상",
                "internal_energy": 65,
                "qi_nature": "청명",
                "martial_arts": ["비검술"],
            },
            "items_acquired": [],
        }

        result = finalizer._prepare_stage2_pass_arc_for_persistence(
            refined_arc=refined_arc,
            arc_drive={"desire_vector": "test"},
            enriched_block={
                "joint_docs": {"final_location": "청풍산장 후원", "physical_inventory": ["검"], "world_joint": "긴장"},
                "status_shadow": {
                    "internal_energy_loss": "15%",
                    "expected_injuries": "경미한 타박상",
                    "item_consumption": [],
                },
                "joint_docs_brief": "brief",
            },
            all_refined_arcs=[],
            global_arc_no=1,
            current_feedback="",
            generation_method="four_phase",
            st_snapshot=None,
            cdb_snapshot=None,
            constraint_db=MagicMock(arc_states=[]),
            constraint_block="",
            genre="wuxia",
        )

        assert result["action"] == "continue"
        saved_arc = result["refined_arc"]["state_constraints"]
        assert saved_arc["arc_start_state"]["internal_energy"] == 80
        assert saved_arc["arc_start_state"]["realm"] == "후천"
        assert saved_arc["arc_end_state"]["internal_energy"] == 65
        assert saved_arc["arc_end_state"]["qi_nature"] == "청명"
        assert saved_arc["arc_end_state"]["martial_arts"] == ["비검술"]
        assert not any(
            "[Non-Wuxia State Cleanup]" in call.args[0] for call in finalizer.ctx.ui.log.call_args_list if call.args
        )

    def test_ctx_proxy(self, finalizer, finalizer_ctx):
        assert finalizer.ctx is finalizer_ctx

    def test_methods_exist(self, finalizer):
        assert hasattr(finalizer, "run_finalize")
        assert hasattr(finalizer, "_record_s2_pass_metrics")
        assert hasattr(finalizer, "_record_s2_reject_metrics")


class TestDirectorAuditPreparation:
    def test_prepare_audit_state_normalizes_entity_aliases_before_director(self, finalizer, valid_refined_arc):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["tactical_doc"] = (
            "WTI 원유 6월물 포지션을 정리하고 금 가격 차트를 보며 SW인베스트먼트 오피스로 이동해 PDA를 확인한다."
        )
        refined_arc["joint_docs"]["final_location"] = "SW인베스트먼트 오피스"
        refined_arc["joint_docs"]["physical_inventory"] = ["PDA"]
        refined_arc["state_constraints"] = {
            "arc_start_state": {
                "location": "SW인베스트먼트 오피스",
                "equipment": ["PDA"],
            },
            "arc_end_state": {
                "location": "SW인베스트먼트 오피스",
                "equipment": ["WTI 원유 6월물 메모"],
            },
            "items_acquired": [],
        }
        refined_arc["episode_details"] = [
            {"ep_num": 1, "details": ["SW인베스트먼트 오피스에서 PDA를 열고 금 가격 차트를 확인한다."]}
        ]

        entity_registry = {
            "locations": [{"name": "SW 인베스트먼트 임시 오피스텔"}],
            "objects": [
                {"name": "WTI 원유 선물 6월물"},
                {"name": "금(XAU/USD) 10년 치 가격 차트"},
                {"name": "개인용 PDA 단말기"},
            ],
        }

        finalizer._build_stage2_director_story_context = MagicMock(return_value=("prev", "story"))
        finalizer._audit_stage2_director = MagicMock(return_value=({"decision": "PASS", "score": 95}, 0, "PASS", 95))
        finalizer._log_stage2_session_decision = MagicMock()

        finalizer._prepare_stage2_finalize_audit_state(
            refined_arc=refined_arc,
            enriched_block={},
            all_refined_arcs=[],
            global_arc_no=3,
            last_refined_context="prev context",
            bible_root={"protagonist_config": {"name": "hero", "incarnation_type": "회귀자"}},
            genre="investment",
            protagonist_name="hero",
            constraint_block="",
            current_feedback="",
            suspected_duplicates=[],
            entity_registry_for_director=entity_registry,
            draft_validator_passed=True,
            consensus_passed=True,
            attempt=1,
            generation_method="four_phase",
            constraint_db=None,
        )

        audited_arc = finalizer._audit_stage2_director.call_args.kwargs["refined_arc"]
        assert "WTI 원유 선물 6월물" in audited_arc["tactical_doc"]
        assert "금(XAU/USD) 10년 치 가격 차트" in audited_arc["tactical_doc"]
        assert "SW 인베스트먼트 임시 오피스텔" in audited_arc["tactical_doc"]
        assert "개인용 PDA 단말기" in audited_arc["tactical_doc"]
        assert audited_arc["joint_docs"]["final_location"] == "SW 인베스트먼트 임시 오피스텔"
        assert audited_arc["joint_docs"]["physical_inventory"] == ["개인용 PDA 단말기"]
        finalizer.ctx.ui.log.assert_any_call("      🔧 [Entity Canonicalization] Director 심사 전 명칭 계약 동기화")


class TestMetricsRecording:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_with_monitor(self, finalizer):
        collector = MagicMock()
        collector.peek_scope.return_value = {"total_cost_usd": 0.0123}
        with patch("modules.core.stage2_finalizer.get_metrics_collector", return_value=collector):
            finalizer._record_s2_pass_metrics(
                global_arc_no=1, attempt=0, generation_method="analyst", audit={"score": 88}
            )
        kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is True
        assert kw["stage"] == 2
        assert kw["attempt_key"] == "s2:ep1:arc1:a1"
        assert kw["final_verdict"] == "PASS"
        assert kw["token_cost"] == 0.0123
        qd_kw = finalizer.ctx.quality_dashboard.record_validation.call_args[1]
        assert qd_kw["result"]["decision"] == "PASS"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_record_monitor_even_when_v50_flag_false(self, finalizer):
        finalizer._record_s2_pass_metrics(global_arc_no=1, attempt=0, generation_method="analyst", audit={"score": 88})

        finalizer.ctx.pass_rate_monitor.record_attempt.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_without_monitor(self, finalizer):
        finalizer.ctx.pass_rate_monitor = None
        finalizer.ctx.quality_dashboard = None
        finalizer._record_s2_pass_metrics(global_arc_no=2, attempt=1, generation_method="analyst", audit={"score": 80})
        finalizer.ctx.perf_timer.log_summary.assert_called_once()
        finalizer.ctx.perf_timer.reset.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_clears_optimizer_failures(self, finalizer):
        finalizer._record_s2_pass_metrics(global_arc_no=3, attempt=0, generation_method="analyst", audit={})
        finalizer.ctx.stage2_optimizer.failure_memory.clear_arc_failures.assert_called_once_with(3)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_with_monitor(self, finalizer):
        collector = MagicMock()
        collector.peek_scope.return_value = {"total_cost_usd": 0.0456}
        with patch("modules.core.stage2_finalizer.get_metrics_collector", return_value=collector):
            finalizer._record_s2_reject_metrics(
                global_arc_no=4,
                attempt=1,
                generation_method="analyst",
                audit={"score": 42, "reason": "bad structure", "re_slice_instruction": "장면 순서를 재배치"},
            )
        kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is False
        assert kw["attempt_key"] == "s2:ep4:arc4:a2"
        assert kw["final_verdict"] == "REJECT"
        assert kw["token_cost"] == 0.0456
        assert len(finalizer.ctx.stage_rejection_history) == 1
        assert finalizer.ctx.stage_rejection_history[0]["arc_no"] == 4
        assert finalizer.ctx.stage_rejection_history[0]["specific_issue"] == "장면 순서를 재배치"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_without_monitor(self, finalizer):
        finalizer.ctx.pass_rate_monitor = None
        finalizer.ctx.quality_dashboard = None
        finalizer._record_s2_reject_metrics(
            global_arc_no=5,
            attempt=0,
            generation_method="analyst",
            audit={"reason": "x"},
        )
        assert len(finalizer.ctx.stage_rejection_history) == 1

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_records_optimizer_failure(self, finalizer):
        finalizer._record_s2_reject_metrics(
            global_arc_no=6,
            attempt=0,
            generation_method="analyst",
            audit={"reason": "reject reason"},
        )
        finalizer.ctx.stage2_optimizer.failure_memory.record_failure.assert_called_once()


class TestConstraintDbLogging:
    def test_update_stage2_pass_constraint_db_logs_clean_message(self, finalizer):
        constraint_db = MagicMock()
        constraint_db.arc_states = [1]

        finalizer._update_stage2_pass_constraint_db(
            refined_arc={"arc_no": 1, "title": "Arc 1"},
            constraint_db=constraint_db,
        )

        constraint_db.update_arc_state.assert_called_once_with({"arc_no": 1, "title": "Arc 1"})
        finalizer.ctx.ui.log.assert_any_call("      [V49.4] ConstraintDB 업데이트 완료 (총 1개 Arc)")

    def test_stage2_finalizer_source_keeps_only_single_live_duplicate_prone_defs(self):
        src = (PROJECT_ROOT / "modules" / "core" / "stage2_finalizer.py").read_text(encoding="utf-8")

        assert src.count("async def _persist_stage2_pass_arc_commit(") == 1
        assert src.count("def _maybe_generate_stage2_volume_summaries(") == 1
        assert "ConstraintDB 업데이트 완료" in src

    def test_reject_metric_context_persists_artifact_linkage(self, finalizer, valid_refined_arc, tmp_path):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path

        context = finalizer._build_stage2_reject_metric_context(
            global_arc_no=7,
            attempt=1,
            generation_method="analyst",
            selected_strategy="defensive",
            artifact_payload=valid_refined_arc,
        )

        assert context["attempt_key"] == "s2:ep7:arc7:a2"
        assert context["candidate_key"] == "defensive"
        assert context["artifact_meta"]["content_hash"]
        assert context["artifact_meta"]["artifact_path"].endswith("rejected_arc__defensive.json")
        assert (tmp_path / context["artifact_meta"]["artifact_path"]).exists()

    def test_merge_stage2_pass_fix_reaudit_copies_patch_advisories(self, finalizer):
        current_audit = {
            "patch_pressure": {"exceeded": True, "count": 2},
            "patch_guard_signals": {"codes": ["missing_tactical_doc"], "count": 1},
        }
        re_audit = {"decision": "PASS", "score": 95}

        merged = finalizer._merge_stage2_pass_fix_reaudit(
            current_audit=current_audit,
            re_audit=re_audit,
        )

        assert merged["patch_pressure"] == current_audit["patch_pressure"]
        assert merged["patch_guard_signals"] == current_audit["patch_guard_signals"]
        assert merged["patch_pressure"] is not current_audit["patch_pressure"]
        assert merged["patch_guard_signals"] is not current_audit["patch_guard_signals"]

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_attempt_key_uses_metrics_session_id_when_available(self, finalizer):
        finalizer.ctx.current_project.metrics_session_id = "sess_stage2"

        finalizer._record_s2_pass_metrics(global_arc_no=1, attempt=0, generation_method="analyst", audit={"score": 88})

        kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["attempt_key"] == "s2:ep1:arc1:a1:sess_stage2"
        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert db_kw["attempt_key"] == "s2:ep1:arc1:a1:sess_stage2"
        assert db_kw["session_id"] == "sess_stage2"

    def test_intermediate_stage2_session_decision_logs_attempt_key(self, finalizer):
        finalizer.ctx.current_project.metrics_session_id = "sess_stage2"

        finalizer._log_stage2_session_decision(
            audit={"decision": "PASS", "reason": "stable"},
            global_arc_no=2,
            attempt=0,
            generation_method="four_phase",
            score=91,
        )

        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs
        assert log_kw["decision_type"] == "arc"
        assert log_kw["attempt_key"] == "s2:ep2:arc2:a1:sess_stage2"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_persist_artifact_linkage(self, finalizer, valid_refined_arc, tmp_path):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path

        finalizer._record_s2_pass_metrics(
            global_arc_no=1,
            attempt=0,
            generation_method="analyst",
            selected_strategy="creative",
            audit={"score": 88},
            artifact_payload=valid_refined_arc,
        )

        prm_kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        ds_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs

        assert prm_kw["candidate_key"] == "creative"
        assert prm_kw["content_hash"]
        assert prm_kw["artifact_path"].endswith("final_arc__creative.json")
        assert (tmp_path / prm_kw["artifact_path"]).exists()
        assert db_kw["artifact_path"] == prm_kw["artifact_path"]
        assert ds_kw["artifact_path"] == prm_kw["artifact_path"]

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_fall_back_to_director_compare_meta_for_selection_reason(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path
        payload = deepcopy(valid_refined_arc)
        payload["_director_compare_meta"] = {
            "selection_reason": "후보 3은 블록 DNA를 가장 충실하게 반영했다.",
            "feedback": "auto-correct pressure cleared after compare gate",
        }

        finalizer._record_s2_pass_metrics(
            global_arc_no=2,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="balanced",
            audit={"score": 96, "decision": "PASS"},
            artifact_payload=payload,
        )

        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        ds_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        assert db_kw["selection_reason"] == "후보 3은 블록 DNA를 가장 충실하게 반영했다."
        assert db_kw["verdict_reason"] == "auto-correct pressure cleared after compare gate"
        assert ds_kw["selection_reason"] == "후보 3은 블록 DNA를 가장 충실하게 반영했다."
        assert ds_kw["verdict_reason"] == "auto-correct pressure cleared after compare gate"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_drop_escalatory_verdict_reason_when_final_decision_is_pass(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path
        payload = deepcopy(valid_refined_arc)
        payload["_director_compare_meta"] = {
            "selection_reason": "후보 2가 carryover contract를 가장 안정적으로 유지한다.",
            "feedback": "수치 정합성이 재감리에서 해소되어 Stage3 handoff가 가능하다.",
        }

        finalizer._record_s2_pass_metrics(
            global_arc_no=2,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="balanced",
            audit={
                "score": 95,
                "decision": "PASS",
                "reason": (
                    "Major investment advisory requires at least PASS_WITH_FIX.\n"
                    "[F-1] Arc 2: 총자산 합산 불일치. 계산 2.05억 vs 서술 1.05억"
                ),
            },
            artifact_payload=payload,
        )

        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        ds_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs

        assert db_kw["verdict_reason"] == "수치 정합성이 재감리에서 해소되어 Stage3 handoff가 가능하다."
        assert ds_kw["verdict_reason"] == "수치 정합성이 재감리에서 해소되어 Stage3 handoff가 가능하다."
        assert log_kw["verdict_reason"] == "수치 정합성이 재감리에서 해소되어 Stage3 handoff가 가능하다."
        assert "PASS_WITH_FIX" not in db_kw["verdict_reason"]

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_refresh_stale_compare_meta_after_pass_fix_resolution(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path
        payload = deepcopy(valid_refined_arc)
        payload["_director_compare_meta"] = {
            "selection_reason": "치명적 설정 모순이 존재하나, 수정 후 통과가 적합.",
            "comparison_notes": "후보 1이 가장 안정적이다.",
            "director_decision": "PASS_WITH_FIX",
            "feedback": "제9화의 30만원 선금 지출 과정을 수정해야 합니다.",
            "fix_scope": "inplace",
            "quality_gate_triggered": True,
            "quality_gate_reasons": ["investment-major:[F-1]"],
        }

        finalizer._record_s2_pass_metrics(
            global_arc_no=2,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="balanced",
            audit={
                "score": 95,
                "decision": "PASS",
                "fix_scope": "inplace",
                "fix_scope_reasoning": "전술서의 논리적 무결성과 수치 정합성이 재감리에서 모두 해소되었다.",
            },
            artifact_payload=payload,
        )

        compare_meta = payload["_director_compare_meta"]
        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs
        artifact_path = tmp_path / db_kw["artifact_path"]
        artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))

        assert compare_meta["director_decision"] == "PASS"
        assert compare_meta["feedback"] == "전술서의 논리적 무결성과 수치 정합성이 재감리에서 모두 해소되었다."
        assert compare_meta["quality_gate_triggered"] is False
        assert compare_meta["quality_gate_reasons"] == []
        assert db_kw["verdict_reason"] == "전술서의 논리적 무결성과 수치 정합성이 재감리에서 모두 해소되었다."
        assert log_kw["verdict_reason"] == "전술서의 논리적 무결성과 수치 정합성이 재감리에서 모두 해소되었다."
        assert artifact_payload["_director_compare_meta"]["director_decision"] == "PASS"
        assert artifact_payload["_director_compare_meta"]["feedback"] == (
            "전술서의 논리적 무결성과 수치 정합성이 재감리에서 모두 해소되었다."
        )

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_reject_metrics_persist_verdict_reason_to_director_selection(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path

        finalizer._record_s2_reject_metrics(
            global_arc_no=4,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="defensive",
            audit={
                "decision": "REJECT",
                "score": 42,
                "reason": "bad structure",
                "verdict_reason": "carryover anchor breaks before blueprint handoff",
                "runtime_advisory": "다음 시도에서는 carryover authority를 먼저 검증하라.",
                "re_slice_instruction": "핵심 carryover packet을 다시 설계하라.",
                "fix_scope": "rewrite",
            },
            artifact_payload=deepcopy(valid_refined_arc),
        )

        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        ds_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs
        assert db_kw["verdict_reason"] == "carryover anchor breaks before blueprint handoff"
        assert db_kw["runtime_advisory"] == "다음 시도에서는 carryover authority를 먼저 검증하라."
        assert db_kw["retry_directives"] == "핵심 carryover packet을 다시 설계하라."
        assert ds_kw["verdict_reason"] == "carryover anchor breaks before blueprint handoff"
        assert ds_kw["runtime_advisory"] == "다음 시도에서는 carryover authority를 먼저 검증하라."
        assert ds_kw["retry_directives"] == "핵심 carryover packet을 다시 설계하라."
        assert log_kw["runtime_advisory"] == "다음 시도에서는 carryover authority를 먼저 검증하라."
        assert log_kw["retry_directives"] == "핵심 carryover packet을 다시 설계하라."

    def test_pass_metrics_promote_verdict_reason_to_runtime_advisory_when_missing(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path
        payload = deepcopy(valid_refined_arc)
        payload["_director_compare_meta"] = {
            "selection_reason": "candidate B keeps the opening bridge stable",
            "feedback": "carryover authority remains aligned",
        }

        finalizer._record_s2_pass_metrics(
            global_arc_no=5,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="balanced",
            audit={"score": 89, "decision": "PASS_WITH_FIX", "fix_scope": "inplace"},
            artifact_payload=payload,
        )

        db_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        ds_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs
        assert db_kw["runtime_advisory"] == "carryover authority remains aligned"
        assert ds_kw["runtime_advisory"] == "carryover authority remains aligned"
        assert log_kw["runtime_advisory"] == "carryover authority remains aligned"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_emit_authoritative_session_decision_with_artifact_linkage(
        self,
        finalizer,
        valid_refined_arc,
        tmp_path,
    ):
        finalizer.ctx.current_project.paths = MagicMock()
        finalizer.ctx.current_project.paths.root = tmp_path
        payload = deepcopy(valid_refined_arc)
        payload["_director_compare_meta"] = {
            "selection_reason": "후보 1이 가장 안정적으로 후속 전개를 이어 준다.",
            "feedback": "carryover anchor remains intact",
        }

        finalizer._record_s2_pass_metrics(
            global_arc_no=3,
            attempt=0,
            generation_method="four_phase",
            selected_strategy="balanced",
            audit={"score": 94, "decision": "PASS"},
            artifact_payload=payload,
        )

        log_kw = finalizer.ctx.session_logger.log_decision.call_args.kwargs
        assert log_kw["decision_type"] == "arc_final"
        assert log_kw["attempt_key"] == "s2:ep3:arc3:a1"
        assert log_kw["candidate_key"] == "balanced"
        assert "session_id" in log_kw
        assert log_kw["selection_reason"] == "후보 1이 가장 안정적으로 후속 전개를 이어 준다."
        assert log_kw["verdict_reason"] == "carryover anchor remains intact"
        assert log_kw["artifact_path"].endswith("final_arc__balanced.json")


class TestDeterministicCarryover:
    def test_compute_inventory_carryover_removes_consumed_and_dedupes_acquired(self):
        carried = _compute_inventory_carryover(
            prev_inventory=["검", "망령패"],
            consumed=["망령패"],
            acquired=["검", "부적"],
        )

        assert carried == ["검", "부적"]


class TestRunFinalize:
    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_director_pass_returns_break(self, _validate, finalizer, valid_refined_arc):
        kwargs = _make_finalize_kwargs(valid_refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        assert result["current_ep_start"] == 11
        assert len(kwargs["all_refined_arcs"]) == 1
        finalizer.ctx.current_project.save_v20_anchor.assert_called()

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_run_finalize_normalizes_compare_meta_before_arcs_anchor_save(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        saved_arcs_payloads = []

        def _capture_save(key, payload):
            if key == "arcs":
                saved_arcs_payloads.append(deepcopy(payload))

        finalizer.ctx.current_project.save_v20_anchor.side_effect = _capture_save
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "PASS",
            "score": 95,
            "fix_scope": "inplace",
            "fix_scope_reasoning": "재감리에서 모든 수정 지시가 해소되었다.",
        }
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["_director_compare_meta"] = {
            "director_decision": "PASS_WITH_FIX",
            "selection_reason": "후보 2는 수정 후 통과가 적합하다.",
            "feedback": "장면 9의 선금 지출을 수정해야 한다.",
            "fix_scope": "inplace",
            "quality_gate_triggered": True,
            "quality_gate_reasons": ["investment-major:[F-1]"],
        }

        result = asyncio.run(finalizer.run_finalize(**_make_finalize_kwargs(refined_arc)))

        assert result["action"] == "break"
        assert saved_arcs_payloads
        saved_meta = saved_arcs_payloads[0][0]["_director_compare_meta"]
        assert saved_meta["director_decision"] == "PASS"
        assert saved_meta["feedback"] == "재감리에서 모든 수정 지시가 해소되었다."
        assert saved_meta["quality_gate_triggered"] is False
        assert saved_meta["quality_gate_reasons"] == []

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_run_finalize_persists_structured_semantic_carryover(self, _validate, finalizer, valid_refined_arc):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "relationship_changes": [
                {
                    "target": "Han",
                    "trigger": "Han hides the ledger",
                    "justification": "Hero now distrusts the missing entries",
                }
            ],
            "power_changes": {"growth_justification": "Hero earns leverage after exposing the forged trade"},
            "foreshadowings": [{"description": "The sealed vault entry will matter again"}],
            "continuity_checkpoints": ["Keep Han's missing-ledger suspicion active"],
        }
        kwargs = _make_finalize_kwargs(refined_arc)

        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][0]
        assert saved_arc["semantic_carryover"]["relationship_rationale"][0]["npc"] == "Han"
        assert saved_arc["semantic_carryover"]["growth_justification"].startswith("Hero earns leverage")
        assert "foreshadow_anchors" in saved_arc["semantic_carryover"]
        assert "continuity_checkpoints" in saved_arc["semantic_carryover"]
        assert "Han" in saved_arc["rationale_digest"]

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_overrides_stale_joint_docs_inventory_with_deterministic_carryover(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        prev_arc = {
            "joint_docs": {
                "final_location": "market",
                "physical_inventory": ["검", "망령패"],
                "world_joint": "stable",
            },
            "status_shadow": {
                "internal_energy_loss": "0%",
                "expected_injuries": "none",
                "item_consumption": [],
            },
            "state_constraints": {"arc_end_state": {"equipment": ["검", "망령패"]}, "items_acquired": []},
        }
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {"location": "market", "equipment": ["검", "망령패"]},
            "items_acquired": ["부적"],
        }
        kwargs = _make_finalize_kwargs(
            refined_arc,
            all_refined_arcs=[prev_arc],
            global_arc_no=2,
            current_ep_start=11,
            enriched_block={
                "joint_docs": {
                    "final_location": "market",
                    "physical_inventory": ["검", "망령패"],
                    "world_joint": "stable",
                },
                "status_shadow": {
                    "internal_energy_loss": "5%",
                    "expected_injuries": "none",
                    "item_consumption": ["망령패"],
                },
                "joint_docs_brief": "brief",
            },
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][1]
        assert saved_arc["joint_docs"]["physical_inventory"] == ["검", "부적"]

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_preserves_refined_arc_packets_over_enriched_block(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["joint_docs"] = {
            "final_location": "llm-city",
            "physical_inventory": ["천풍검"],
            "world_joint": "llm-world",
        }
        refined_arc["status_shadow"] = {
            "internal_energy_loss": "10%",
            "expected_injuries": "llm-wound",
            "item_consumption": ["천풍검"],
            "key_stat_change": "llm-stat",
        }
        kwargs = _make_finalize_kwargs(
            refined_arc,
            enriched_block={
                "joint_docs": {
                    "final_location": "block-city",
                    "physical_inventory": [],
                    "world_joint": "stale-world",
                },
                "status_shadow": {
                    "internal_energy_loss": "5%",
                    "expected_injuries": "stale-wound",
                    "item_consumption": [],
                    "key_stat_change": "stale-stat",
                },
                "joint_docs_brief": "brief",
            },
        )

        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][0]
        assert saved_arc["joint_docs"]["final_location"] == "llm-city"
        assert saved_arc["joint_docs"]["world_joint"] == "llm-world"
        assert saved_arc["status_shadow"]["expected_injuries"] == "llm-wound"
        assert saved_arc["status_shadow"]["item_consumption"] == ["천풍검"]
        assert saved_arc["status_shadow"]["key_stat_change"] == "llm-stat"

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_syncs_start_equipment_from_prev_arc_deterministic_carryover(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        prev_arc = {
            "joint_docs": {
                "final_location": "market",
                "physical_inventory": ["검", "망령패"],
                "world_joint": "stable",
            },
            "status_shadow": {
                "internal_energy_loss": "0%",
                "expected_injuries": "none",
                "item_consumption": ["망령패"],
            },
            "state_constraints": {
                "arc_end_state": {"equipment": ["검", "망령패"]},
                "items_acquired": ["부적"],
            },
        }
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {"location": "market", "equipment": ["검", "망령패"]},
            "items_acquired": [],
        }

        kwargs = _make_finalize_kwargs(refined_arc, all_refined_arcs=[prev_arc], global_arc_no=2, current_ep_start=11)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][1]
        assert saved_arc["state_constraints"]["arc_start_state"]["equipment"] == ["검", "부적"]

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_syncs_start_location_and_finance_from_prev_arc_end_state(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        prev_arc = {
            "joint_docs": {
                "final_location": "headquarters",
                "physical_inventory": ["ledger"],
                "world_joint": "stable",
            },
            "status_shadow": {
                "internal_energy_loss": "0%",
                "expected_injuries": "none",
                "item_consumption": [],
            },
            "state_constraints": {
                "arc_end_state": {
                    "location": "headquarters",
                    "equipment": ["ledger"],
                    "total_assets": "30억원",
                    "capital": "17.5억원",
                    "portfolio_position": "WTI 12.5억원 롱",
                },
                "items_acquired": [],
            },
        }
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {
                "location": "stale-office",
                "equipment": ["ledger"],
                "total_assets": "10억원",
                "capital": "5억원",
                "portfolio_position": "없음",
            },
            "items_acquired": [],
        }

        kwargs = _make_finalize_kwargs(refined_arc, all_refined_arcs=[prev_arc], global_arc_no=2, current_ep_start=11)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][1]
        start_state = saved_arc["state_constraints"]["arc_start_state"]
        assert start_state["location"] == "headquarters"
        assert start_state["total_assets"] == "30억원"
        assert start_state["capital"] == "17.5억원"
        assert start_state["portfolio_position"] == "WTI 12.5억원 롱"
        assert any("[Carryover Sync]" in str(call.args[0]) for call in finalizer.ctx.ui.log.call_args_list if call.args)

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_syncs_joint_docs_inventory_from_arc_end_state_authority(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["joint_docs"]["physical_inventory"] = ["Ghost token"]
        refined_arc["state_constraints"] = {
            "arc_end_state": {"equipment": ["검", "부적"]},
            "items_acquired": [],
        }

        kwargs = _make_finalize_kwargs(refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][0]
        assert saved_arc["joint_docs"]["physical_inventory"] == ["검", "부적"]
        assert saved_arc["state_constraints"]["arc_end_state"]["equipment"] == ["검", "부적"]

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_syncs_joint_docs_final_location_from_arc_end_state_authority(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["joint_docs"]["final_location"] = "Yeouido Office"
        refined_arc["state_constraints"] = {
            "arc_end_state": {"location": "Gangnam HQ"},
            "items_acquired": [],
        }

        kwargs = _make_finalize_kwargs(refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        saved_arc = kwargs["all_refined_arcs"][0]
        assert saved_arc["joint_docs"]["final_location"] == "Gangnam HQ"
        assert saved_arc["state_constraints"]["arc_end_state"]["location"] == "Gangnam HQ"

    def test_sync_stage2_end_location_contract_collapses_verbose_scene_label(self):
        refined_arc = {
            "joint_docs": {
                "final_location": "서울 강남, SW인베스트먼트 오피스, 아직 서류 상자와 모니터가 널린 임시 작업 공간"
            },
            "state_constraints": {"arc_end_state": {"location": ""}},
        }

        canonical_location, joint_changed, end_changed = _sync_stage2_end_location_contract(refined_arc)

        assert canonical_location == "서울 강남, SW인베스트먼트 오피스"
        assert joint_changed is True
        assert end_changed is True
        assert refined_arc["joint_docs"]["final_location"] == "서울 강남, SW인베스트먼트 오피스"
        assert refined_arc["state_constraints"]["arc_end_state"]["location"] == "서울 강남, SW인베스트먼트 오피스"

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_director_pass_records_arc_cost(self, _validate, finalizer, valid_refined_arc):
        collector = MagicMock()
        collector.session_id = "sess_test"
        collector.snapshot_and_reset_scope.return_value = {
            "total_calls": 2,
            "total_tokens": 1500,
            "total_cost_usd": 0.0123,
            "model_breakdown": "{}",
        }

        kwargs = _make_finalize_kwargs(valid_refined_arc)
        with patch("modules.core.stage2_finalizer.get_metrics_collector", return_value=collector):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        finalizer.ctx.current_project.db.save_cost_record.assert_called_once()
        cost_kw = finalizer.ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kw["session_id"] == "sess_test"

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_uses_validate_arc_data_fields_before_missing_field_audit(
        self,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        repaired_arc = dict(valid_refined_arc)
        repaired_arc.pop("hybrid_composition", None)
        repaired_arc.pop("joint_docs", None)
        repaired_arc.pop("status_shadow", None)

        finalizer.ctx.validate_arc_data_fields = MagicMock(
            return_value={
                **repaired_arc,
                "hybrid_composition": {
                    "primary": "standard_progression",
                    "secondary": [],
                    "mixing_logic": "default",
                },
                "joint_docs": {
                    "final_location": "market",
                    "physical_inventory": [],
                    "world_joint": "stable",
                },
                "status_shadow": {
                    "internal_energy_loss": "10%",
                    "expected_injuries": "none",
                    "item_consumption": [],
                },
            }
        )

        kwargs = _make_finalize_kwargs(repaired_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        finalizer.ctx.validate_arc_data_fields.assert_called_once()
        calls = [call.args[:2] for call in finalizer.ctx.audit_event.call_args_list]
        assert ("data_missing", "hybrid_composition missing") not in calls
        assert ("data_missing", "joint_docs missing") not in calls
        assert ("data_missing", "status_shadow missing") not in calls

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_real_app_context_invokes_bound_validate_arc_data_fields(self, _validate, valid_refined_arc):
        class RealApp:
            def __init__(self):
                self.ui = MagicMock()
                self.ui.log = MagicMock()
                self.current_project = MagicMock()
                self.agents = {"director": MagicMock()}
                self.agents["director"].audit_strategic_plan.return_value = {
                    "decision": "PASS",
                    "score": 95,
                    "reason": "ok",
                }
                self.agents["director"].ask.return_value = "volume summary text long enough"
                self.sys = MagicMock()
                self.state_tracker = SimpleNamespace(foo=0, bar=0)
                self.pass_rate_monitor = MagicMock()
                self.quality_dashboard = MagicMock()
                self.stage2_optimizer = MagicMock()
                self.stage2_optimizer.failure_memory = MagicMock()
                self.perf_timer = MagicMock()
                self.stage_rejection_history = []
                self.semantic_plot_guard = None
                self._audit_event = MagicMock()
                self._write_audit_summary = MagicMock()
                self._safe_commit_async = AsyncMock(return_value=True)
                self._generate_arc_context_v60 = MagicMock(return_value="context_text")
                self._get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
                self._state_tracker_loaded_arcs = 0
                self.repair_calls = []

            def _validate_arc_data_fields(self, arc_data, arc_idx):
                self.repair_calls.append((arc_idx, arc_data.get("arc_no")))
                repaired = dict(arc_data)
                repaired.setdefault(
                    "hybrid_composition",
                    {"primary": "standard_progression", "secondary": [], "mixing_logic": "default"},
                )
                repaired.setdefault(
                    "joint_docs",
                    {"final_location": "market", "physical_inventory": [], "world_joint": "stable"},
                )
                repaired.setdefault(
                    "status_shadow",
                    {"internal_energy_loss": "10%", "expected_injuries": "none", "item_consumption": []},
                )
                return repaired

            def _validate_arc_integrity(self, arc_data):
                return True

        app = RealApp()
        host = SimpleNamespace(ctx=Stage2Context.from_app(app))
        finalizer = Stage2Finalizer(host)

        repaired_arc = dict(valid_refined_arc)
        repaired_arc.pop("hybrid_composition", None)
        repaired_arc.pop("joint_docs", None)
        repaired_arc.pop("status_shadow", None)

        result = asyncio.run(finalizer.run_finalize(**_make_finalize_kwargs(repaired_arc)))

        assert result["action"] == "break"
        assert app.repair_calls == [(1, 1)]
        calls = [call.args[:2] for call in app._audit_event.call_args_list]
        assert ("data_missing", "hybrid_composition missing") not in calls

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_finalize_fallback_repairs_emit_field_repair(self, _validate, finalizer, valid_refined_arc):
        repaired_arc = dict(valid_refined_arc)
        repaired_arc["hybrid_composition"] = {}
        finalizer.ctx.validate_arc_data_fields = MagicMock(return_value=repaired_arc)

        kwargs = _make_finalize_kwargs(repaired_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        calls = [call.args[:2] for call in finalizer.ctx.audit_event.call_args_list]
        assert ("field_repair", "hybrid_composition default injected") in calls

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_ns2_advisory_injected_to_director_story_context(self, _validate, finalizer, valid_refined_arc):
        kwargs = _make_finalize_kwargs(
            valid_refined_arc,
            enriched_block={
                "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
                "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
                "joint_docs_brief": "brief",
                "genre_ext": {"capital_after": "77억"},
            },
        )

        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        story_context = finalizer.ctx.agents["director"].audit_strategic_plan.call_args.kwargs["story_context"]
        assert "[NS-2 참고]" in story_context
        assert "77억" in story_context

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.constants.log_patch_diff")
    @patch("modules.core.constants.calc_patch_change_ratio", return_value=0.75)
    def test_pass_with_fix_high_patch_pressure_is_advisory_only(
        self,
        _ratio,
        _log_diff,
        _validate,
        finalizer,
        valid_refined_arc,
    ):
        patched_arc = dict(valid_refined_arc)
        patched_arc["tactical_doc"] = valid_refined_arc["tactical_doc"] + " patched"
        finalizer.ctx.agents["four_phase"] = MagicMock()
        finalizer.ctx.agents["four_phase"]._inplace_patch_arc.return_value = patched_arc
        finalizer.ctx.agents["director"].audit_strategic_plan.side_effect = [
            {
                "decision": "PASS_WITH_FIX",
                "score": 93,
                "reason": "needs local fix",
                "re_slice_instruction": "tighten numbers",
                "fix_scope": "inplace",
            },
            {
                "decision": "PASS",
                "score": 95,
                "reason": "looks good",
            },
        ]

        kwargs = _make_finalize_kwargs(valid_refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        save_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert save_kw["verdict"] == "PASS"
        assert save_kw["advisory_flags"]["patch_pressure_exceeded"] == 1
        assert save_kw["advisory_flags"]["patch_pressure_count"] == 1
        selection_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        assert "[PatchPressure Advisory]" in selection_kw["selection_reason"]
        story_context = finalizer.ctx.agents["director"].audit_strategic_plan.call_args_list[1].kwargs["story_context"]
        assert "[F-2 advisory — high Arc patch pressure]" in story_context

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_with_fix_records_arc_patch_guard_signals(self, _validate, finalizer, valid_refined_arc):
        patched_arc = dict(valid_refined_arc)
        patched_arc["tactical_doc"] = ""
        patched_arc["joint_docs"] = {}
        patched_arc["ep_count"] = 99
        finalizer.ctx.agents["four_phase"] = MagicMock()
        finalizer.ctx.agents["four_phase"]._inplace_patch_arc.return_value = patched_arc
        finalizer.ctx.agents["director"].audit_strategic_plan.side_effect = [
            {
                "decision": "PASS_WITH_FIX",
                "score": 93,
                "reason": "needs local fix",
                "re_slice_instruction": "tighten structure",
                "fix_scope": "inplace",
            },
            {
                "decision": "PASS",
                "score": 95,
                "reason": "accepted with warning visibility",
            },
        ]

        kwargs = _make_finalize_kwargs(valid_refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        save_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert save_kw["advisory_flags"]["arc_patch_signal_count"] == 3
        assert "missing_tactical_doc" in save_kw["advisory_flags"]["arc_patch_signal_codes"]
        assert "structured_section_dropped" in save_kw["advisory_flags"]["arc_patch_signal_codes"]
        assert "episode_span_inconsistent" in save_kw["advisory_flags"]["arc_patch_signal_codes"]
        story_context = finalizer.ctx.agents["director"].audit_strategic_plan.call_args_list[1].kwargs["story_context"]
        assert "[S2 Arc patch signals]" in story_context
        assert "missing_tactical_doc" in story_context
        assert "episode_span_inconsistent" in story_context
        finalizer.ctx.audit_event.assert_any_call(
            "patch_guard_signal",
            "stage2 arc patch signals observed",
            {
                "arc_no": 1,
                "attempt": 1,
                "codes": [
                    "missing_tactical_doc",
                    "structured_section_dropped",
                    "episode_span_inconsistent",
                ],
                "count": 3,
                "items": [
                    {"code": "missing_tactical_doc", "detail": "patched tactical_doc is blank"},
                    {"code": "structured_section_dropped", "detail": "joint_docs"},
                    {"code": "episode_span_inconsistent", "detail": "ep_count(99) != expected(10)"},
                ],
            },
        )

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_with_fix_persists_fix_pack_and_partial_fix_eval(self, _validate, finalizer, valid_refined_arc):
        patched_arc = deepcopy(valid_refined_arc)
        patched_arc["state_constraints"] = {
            "arc_end_state": {"location": "Gangnam HQ"},
            "items_acquired": [],
        }
        finalizer.ctx.agents["four_phase"] = MagicMock()
        finalizer.ctx.agents["four_phase"]._inplace_patch_arc.return_value = patched_arc
        finalizer.ctx.agents["director"].audit_strategic_plan.side_effect = [
            {
                "decision": "PASS_WITH_FIX",
                "score": 93,
                "reason": "needs bounded local fix",
                "re_slice_instruction": "repair the ending venue only",
                "fix_scope": "inplace",
                "fix_pack": {
                    "patch_targets": [
                        {
                            "summary": "state_constraints.arc_end_state.location",
                            "field_path": "state_constraints.arc_end_state.location",
                            "target_kind": "field_value",
                        }
                    ],
                    "must_fix": ["set arc_end_state.location to Gangnam HQ"],
                    "do_not_regress": ["keep the tactical_doc flow unchanged"],
                    "success_condition": "arc_end_state.location now matches the repaired venue",
                },
            },
            {
                "decision": "PASS",
                "score": 95,
                "reason": "looks good",
            },
        ]

        kwargs = _make_finalize_kwargs(valid_refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        patch_kw = finalizer.ctx.agents["four_phase"]._inplace_patch_arc.call_args.kwargs
        assert patch_kw["fix_pack"]["patch_targets"] == ["state_constraints.arc_end_state.location"]
        assert (
            patch_kw["fix_pack"]["patch_target_records"][0]["field_path"] == "state_constraints.arc_end_state.location"
        )
        assert patch_kw["fix_pack"]["target_kind"] == "field_value"

        save_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert save_kw["advisory_flags"]["fix_pack"]["patch_targets"] == ["state_constraints.arc_end_state.location"]
        assert (
            save_kw["advisory_flags"]["fix_pack"]["patch_target_records"][0]["field_path"]
            == "state_constraints.arc_end_state.location"
        )
        assert save_kw["advisory_flags"]["partial_fix_eval"]["patch_round"] == 1
        assert save_kw["advisory_flags"]["partial_fix_eval"]["target_kind"] == "field_value"
        assert save_kw["advisory_flags"]["partial_fix_eval"]["must_fix_resolved"] is True
        assert save_kw["advisory_flags"]["partial_fix_eval"]["success_condition_met"] is True
        assert save_kw["advisory_flags"]["partial_fix_eval"]["patch_target_id"].startswith("pt:")

        selection_kw = finalizer.ctx.current_project.db.save_director_selection.call_args.kwargs
        assert selection_kw["advisory_warnings"]["fix_pack"]["patch_targets"] == [
            "state_constraints.arc_end_state.location"
        ]
        assert selection_kw["advisory_warnings"]["partial_fix_eval"]["patch_target_id"].startswith("pt:")

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_pass_metrics_persist_carryover_authority_summary(self, _validate, finalizer, valid_refined_arc):
        refined_arc = deepcopy(valid_refined_arc)
        refined_arc["state_constraints"] = {
            "arc_start_state": {
                "location": "성북동 본가",
                "equipment": ["구형 폴더폰", "지갑"],
                "total_assets": "약 20억원",
            },
            "arc_end_state": {
                "location": "강남 오피스",
                "equipment": ["법인 인감", "노트북"],
                "total_assets": "20억원",
            },
            "investment_calc": {"final_total_assets": 2000000000},
            "items_acquired": [],
        }
        refined_arc["joint_docs"] = {
            "final_location": "강남 오피스",
            "physical_inventory": ["법인 인감", "노트북"],
            "world_joint": "stable",
        }
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "PASS",
            "score": 95,
            "reason": "ok",
        }

        result = asyncio.run(finalizer.run_finalize(**_make_finalize_kwargs(refined_arc)))

        assert result["action"] == "break"
        save_kw = finalizer.ctx.current_project.db.save_stage_attempt.call_args.kwargs
        summary = save_kw["advisory_flags"]["carryover_authority"]
        assert summary["start_location"] == "성북동 본가"
        assert summary["end_location"] == "강남 오피스"
        assert summary["investment_calc_final_total_assets"] == 2000000000
        cross_stage_packet = save_kw["advisory_flags"]["cross_stage_authority_packet"]
        assert cross_stage_packet["contract_version"] == CROSS_STAGE_AUTHORITY_PACKET_VERSION
        assert cross_stage_packet["opening_carryover"]["location"] == "강남 오피스"
        assert cross_stage_packet["numeric_carryover"]["total_assets"] == "20억원"
        saved_arcs = finalizer.ctx.current_project.save_v20_anchor.call_args_list[0].args[1]
        assert saved_arcs[-1]["cross_stage_authority_packet"]["provenance"]["emitted_by"] == "Stage2Finalizer"
        ui_event_kw = finalizer.ctx.current_project.db.save_ui_event.call_args.kwargs
        assert ui_event_kw["event_kind"] == "carryover_authority"
        assert ui_event_kw["attempt_key"] == save_kw["attempt_key"]
        assert ui_event_kw["meta"]["end_location"] == "강남 오피스"
        assert ui_event_kw["meta"]["cross_stage_authority_packet_version"] == CROSS_STAGE_AUTHORITY_PACKET_VERSION
        assert any(
            "[Stage2 Carryover Authority]" in str(call.args[0])
            for call in finalizer.ctx.ui.log.call_args_list
            if call.args
        )

    def test_collect_arc_patch_guard_signals_flags_future_artifact_in_first_episode_start_state(
        self,
        finalizer,
        valid_refined_arc,
    ):
        patched_arc = dict(valid_refined_arc)
        patched_arc["tactical_doc"] = (
            "제 15화 돌아온 방향타\n"
            '[시작 상태] 위치: 여의도 사무실 / 소지품 ["WTI 6월물 최종 매도 체결 확인서", "금 가격 추이 분석 리포트"]\n'
            "주인공은 장 마감 직전 남은 WTI 포지션을 전량 익절 청산한다.\n"
            '[종료 상태] 위치: 여의도 사무실 / 소지품 ["WTI 6월물 최종 매도 체결 확인서"]\n'
            "제 16화 중간 자산\n"
            "[시작 상태] 위치: 여의도 사무실 / 소지품 []\n"
        )

        signals = finalizer._collect_arc_patch_guard_signals(
            original_arc=valid_refined_arc,
            patched_arc=patched_arc,
        )

        assert {
            "code": "episode_start_future_artifact",
            "detail": "제 15화 돌아온 방향타: 최종 매도 체결 확인서 precedes later action '전량 익절 청산'",
        } in signals

    def test_collect_arc_patch_guard_signals_ignores_other_asset_liquidation_carryover(
        self,
        finalizer,
        valid_refined_arc,
    ):
        patched_arc = dict(valid_refined_arc)
        patched_arc["tactical_doc"] = (
            "제 20화 700달러의 도달과 은밀한 이전\n"
            '[시작 상태] 위치: 여의도 사무실 / 소지품 ["WTI 6월물 최종 매도 체결 확인서", "금 선물 절반 매도 체결 확인서"]\n'
            "주인공은 금 선물이 700달러를 돌파하자 잔여 포지션을 전량 익절 청산한다.\n"
            '[종료 상태] 위치: 강남 룸 / 소지품 ["금 선물 최종 매도 체결 확인서"]\n'
        )

        signals = finalizer._collect_arc_patch_guard_signals(
            original_arc=valid_refined_arc,
            patched_arc=patched_arc,
        )

        assert not any(signal.get("code") == "episode_start_future_artifact" for signal in signals)

    def test_director_reject_returns_retry(self, finalizer, valid_refined_arc):
        finalizer.ctx.current_project.metrics_session_id = "sess_stage2_reject"
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 30,
            "reason": "reject reason",
            "re_slice_instruction": "fix structure",
        }
        kwargs = _make_finalize_kwargs(
            valid_refined_arc,
            draft_validator_passed=False,
            consensus_passed=False,
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert "reject reason" in result["director_feedback_for_fourphase"]
        cost_kw = finalizer.ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kw["session_id"] == "sess_stage2_reject"

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_quota_fallback_warning_only(self, _validate, finalizer, valid_refined_arc):
        """[TF-25-07] V60.43 API 쿼터 실패 패턴 감지 시 REJECT 유지 + 경고만."""
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 0,
            "reason": "quota",
            "self_consistency": {"scores": [50, 50]},
        }
        kwargs = _make_finalize_kwargs(valid_refined_arc, draft_validator_passed=True, consensus_passed=True)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        # [TF-25-07] Director REJECT 유지 — Python이 판정을 변경하지 않음
        assert result["action"] == "retry"  # REJECT → retry (오케스트레이터 재시도)
        audit = finalizer.ctx.agents["director"].audit_strategic_plan.return_value
        assert audit.get("v60_43_api_warning") is True

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_missing_critical_data_returns_retry(self, finalizer, valid_refined_arc):
        arc = dict(valid_refined_arc)
        arc.pop("hybrid_composition", None)
        arc.pop("joint_docs", None)
        arc.pop("status_shadow", None)
        kwargs = _make_finalize_kwargs(
            arc,
            enriched_block={"joint_docs": {}, "status_shadow": {}},
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert "current_feedback" in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_state_tracker_rollback_on_reject(self, finalizer, valid_refined_arc):
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 20,
            "reason": "rollback needed",
            "re_slice_instruction": "retry",
        }
        finalizer.ctx.state_tracker = SimpleNamespace(foo=0, bar=0)
        kwargs = _make_finalize_kwargs(
            valid_refined_arc,
            generation_method="four_phase",
            st_snapshot={"foo": 9, "bar": 3},
            draft_validator_passed=False,
            consensus_passed=False,
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert finalizer.ctx.state_tracker.foo == 9
        assert finalizer.ctx.state_tracker.bar == 3
        assert result["st_snapshot"] is None

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_volume_summary_generation(self, _validate, finalizer, valid_refined_arc):
        def _load_anchor(key):
            if key.startswith("arc_summary_"):
                return "arc summary"
            if key == "series_summary":
                return "series summary"
            return None

        finalizer.ctx.current_project.load_v20_anchor.side_effect = _load_anchor
        finalizer.ctx.agents["director"].ask.return_value = "summary result long enough"

        kwargs = _make_finalize_kwargs(valid_refined_arc, global_arc_no=5)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        save_calls = [call.args[0] for call in finalizer.ctx.current_project.save_v20_anchor.call_args_list]
        assert "volume_summary_1" in save_calls
        assert "series_summary" in save_calls
        prompts = [call.args[0] for call in finalizer.ctx.agents["director"].ask.call_args_list]
        assert any("[인물 아크]" in prompt and "2000자 이내" in prompt for prompt in prompts)
        assert any("[미해결 복선]" in prompt and "5000자 이내" in prompt for prompt in prompts)


def test_sync_first_episode_start_state_line_rewrites_stale_equipment_and_inserts_missing_fields():
    tactical_doc = (
        "제 40화: 귀환과 정적\n"
        '[시작 상태] 위치: 홍콩, 소지품: ["검", "망령패"], 부상: 없음\n'
        "본문\n"
        "[종료 상태] 위치: 서울"
    )

    synced = _sync_first_episode_start_state_line(
        tactical_doc,
        {
            "location": "홍콩",
            "equipment": ["검"],
            "injuries": "편두통",
            "internal_energy": 30,
            "total_assets": "30억원",
            "capital": "17.5억원",
            "portfolio_position": "WTI 12.5억원 롱",
        },
    )

    assert '소지품: ["검"]' in synced
    assert "부상: 편두통" in synced
    assert "내공: 30" in synced
    assert "총자산: 30억원" in synced
    assert "자본: 17.5억원" in synced
    assert "포지션: WTI 12.5억원 롱" in synced
