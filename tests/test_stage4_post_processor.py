"""[B-1-1] Stage4PostProcessor unit tests."""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.core.stage4_orchestrator import Stage4Orchestrator
from modules.core.stage4_post_pass_runtime import Stage4PostPassRuntime, _build_state_truth_owner_contract
from modules.core.stage4_post_processor import Stage4PostProcessor


class TestPostProcessorInit:
    def test_init_with_ctx(self):
        ctx = MagicMock()
        pp = Stage4PostProcessor(ctx)
        assert pp.ctx is ctx
        assert isinstance(pp.post_pass_runtime, Stage4PostPassRuntime)
        assert pp.post_pass_runtime.owner is pp

    def test_lazy_init_via_orchestrator(self):
        app = MagicMock()
        ctx = MagicMock()
        orch = Stage4Orchestrator(app, context=ctx)

        pp = orch.post_processor

        assert isinstance(pp, Stage4PostProcessor)
        assert pp.ctx is ctx

    def test_lazy_init_singleton(self):
        app = MagicMock()
        ctx = MagicMock()
        orch = Stage4Orchestrator(app, context=ctx)

        pp1 = orch.post_processor
        pp2 = orch.post_processor

        assert pp1 is pp2


class TestProcessPassResult:
    def _make_pp(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.sys.hud.bulk_update = MagicMock()

        director = MagicMock()
        director.on_approve_workflow.return_value = {}
        manager = MagicMock()
        manager.update_state_and_lore_v20.return_value = {}
        state_extractor = MagicMock()
        state_extractor.extract_satisfaction_tag.return_value = None

        ctx.agents = {
            "director": director,
            "manager": manager,
            "state_extractor": state_extractor,
        }

        db = MagicMock()
        db.conn = MagicMock()
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []

        project = MagicMock()
        project.db = db
        project.name = "test_project"
        project.metrics_session_id = "sess-post-pass"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [],
                },
                "protagonist_config": {"name": "주인공"},
            },
            "npc_registry": {},
        }
        ctx.current_project = project

        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "주인공"
        ctx.generate_narrative_summary = MagicMock()

        return Stage4PostProcessor(ctx)

    def test_returns_true_on_success(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        manuscript = "테스트 원고 " * 500
        normalized_manuscript = pp._normalize_reader_facing_manuscript(manuscript)

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript=manuscript,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        assert (tmp_path / "ep_0001.settlement.json").exists()
        assert (tmp_path / "ep_0001.txt").exists()
        settlement = json.loads((tmp_path / "ep_0001.settlement.json").read_text(encoding="utf-8"))
        assert settlement["packet_version"] == "stage4_settlement_packet_v1"
        assert settlement["ep_num"] == 1
        assert settlement["manuscript"]["char_count"] == len(normalized_manuscript)
        assert settlement["settlement"]["meta_save_failed"] is False
        assert settlement["artifacts"]["human_facing_txt_path"].endswith("ep_0001.txt")

    def test_returns_false_on_db_failure(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.side_effect = RuntimeError("DB error")
        manuscript = "테스트 원고 " * 500

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript=manuscript,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is False
        dump_path = tmp_path / "emergency_ep_0001.txt"
        assert dump_path.exists()
        dump_text = dump_path.read_text(encoding="utf-8")
        assert "# 테스트" in dump_text
        assert manuscript[:40] in dump_text

    def test_returns_false_and_logs_when_meta_save_fails(self, tmp_path):
        pp = self._make_pp()
        pp._save_pass_result_primary_db = MagicMock(return_value=True)
        pp._save_pass_result_quality_sidecars = MagicMock(return_value={})
        pp._run_pass_result_local_side_effects = MagicMock()
        pp._run_pass_result_post_pass_pipeline = MagicMock(
            return_value={"actual_truth": {"location": "gate"}, "bible_delta": {}, "meta_save_failed": True}
        )
        pp._persist_stage4_settlement_packet = MagicMock()
        pp._write_human_facing_manuscript_export = MagicMock()
        pp._finalize_pass_result_session = MagicMock()

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 9},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is False
        log_texts = [call.args[0] for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("후처리 메타 저장 실패" in text for text in log_texts)
        pp._persist_stage4_settlement_packet.assert_not_called()
        pp._write_human_facing_manuscript_export.assert_not_called()
        pp._finalize_pass_result_session.assert_not_called()

    def test_returns_false_when_settlement_packet_save_fails(self, tmp_path):
        pp = self._make_pp()
        pp._save_pass_result_primary_db = MagicMock(return_value=True)
        pp._save_pass_result_quality_sidecars = MagicMock(return_value={})
        pp._run_pass_result_local_side_effects = MagicMock()
        pp._run_pass_result_post_pass_pipeline = MagicMock(
            return_value={"actual_truth": {"location": "gate"}, "bible_delta": {}, "meta_save_failed": False}
        )
        pp._persist_stage4_settlement_packet = MagicMock(side_effect=RuntimeError("packet write failed"))
        pp._write_human_facing_manuscript_export = MagicMock()
        pp._finalize_pass_result_session = MagicMock()

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 9},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is False
        pp.ctx.audit_event.assert_called_once_with(
            "stage4_settlement_packet_save_failed",
            "stage4 settlement packet save failed",
            {"ep": 3},
        )
        pp._write_human_facing_manuscript_export.assert_not_called()
        pp._finalize_pass_result_session.assert_not_called()

    def test_returns_false_when_human_facing_export_fails(self, tmp_path):
        pp = self._make_pp()
        pp._save_pass_result_primary_db = MagicMock(return_value=True)
        pp._save_pass_result_quality_sidecars = MagicMock(return_value={})
        pp._run_pass_result_local_side_effects = MagicMock()
        pp._run_pass_result_post_pass_pipeline = MagicMock(
            return_value={"actual_truth": {"location": "gate"}, "bible_delta": {}, "meta_save_failed": False}
        )
        pp._persist_stage4_settlement_packet = MagicMock(return_value=tmp_path / "ep_0003.settlement.json")
        pp._write_human_facing_manuscript_export = MagicMock(side_effect=RuntimeError("txt write failed"))
        pp._finalize_pass_result_session = MagicMock()

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 9},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is False
        pp._persist_stage4_settlement_packet.assert_called_once()
        pp.ctx.audit_event.assert_called_once_with(
            "stage4_human_facing_export_failed",
            "stage4 human-facing txt export failed",
            {"ep": 3},
        )
        pp._finalize_pass_result_session.assert_not_called()

    def test_hud_update_called(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.agents["director"].on_approve_workflow.return_value = {"applied_updates": {"hp": 100}}

        pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={"hp": 100},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        pp.ctx.agents["director"].on_approve_workflow.assert_called_once()

    def test_quality_labels_saved_via_sidecar_table(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={
                "_director_quality_labels": {
                    "score": 94,
                    "verdict": "PASS",
                    "selection_reason": "연속성 우수",
                    "score_breakdown": {"continuity_contradiction": 39},
                    "consistency_checklist": {"pacing_quality": "OK"},
                }
            },
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.current_project.db.save_episode_quality_label.assert_called_once()

    def test_quality_signals_saved_via_sidecar_table(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True

        result = pp.process_pass_result(
            next_ep=2,
            final_manuscript="그야말로 숨을 삼켰다. 어느새 입을 열었다. " * 120,
            final_title="테스트",
            final_state_updates={
                "_director_quality_labels": {
                    "score": 91,
                    "verdict": "PASS",
                    "consistency_checklist": {"scene_variety": "ISSUE"},
                },
                "warnings": ["길이 편차"],
            },
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.current_project.db.save_episode_quality_signal.assert_called_once()
        saved_signals = pp.ctx.current_project.db.save_episode_quality_signal.call_args.args[1]
        assert saved_signals["ced_score"] > 0
        assert saved_signals["ai_slop_score"] > 0

    def test_save_pass_result_primary_db_returns_false_and_writes_dump(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.side_effect = RuntimeError("db down")

        result = pp._save_pass_result_primary_db(
            next_ep=3,
            final_manuscript="test manuscript",
            final_title="episode title",
            final_state_updates={},
            output_dir=tmp_path,
        )

        assert result is False
        dump_path = tmp_path / "emergency_ep_0003.txt"
        assert dump_path.exists()
        assert "test manuscript" in dump_path.read_text(encoding="utf-8")

    def test_save_pass_result_quality_sidecars_returns_signal_bundle(self):
        pp = self._make_pp()

        quality_signals = pp._save_pass_result_quality_sidecars(
            next_ep=4,
            final_manuscript="coherent manuscript body " * 60,
            final_state_updates={"warnings": ["short warning"]},
            quality_labels={
                "score": 95,
                "verdict": "PASS",
                "consistency_checklist": {"scene_variety": "ISSUE"},
            },
        )

        assert quality_signals["ced_score"] > 0
        pp.ctx.current_project.db.save_episode_quality_label.assert_called_once()
        pp.ctx.current_project.db.save_episode_quality_signal.assert_called_once()

    def test_run_pass_result_local_side_effects_updates_hud_runs_summary_and_defers_txt_export(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.agents["director"].on_approve_workflow.return_value = {"applied_updates": {"hp": 77}}
        pp._reconcile_capital = MagicMock()

        pp._run_pass_result_local_side_effects(
            next_ep=5,
            final_manuscript="test manuscript",
            final_title="episode title",
            final_state_updates={"hp": 77},
            output_dir=tmp_path,
            v50_modules_available=False,
        )

        pp.ctx.sys.hud.bulk_update.assert_called_once_with({"hp": 77})
        pp.ctx.generate_narrative_summary.assert_called_once_with(5)
        pp._reconcile_capital.assert_called_once_with("test manuscript", 5, final_state_updates={"hp": 77})
        assert not (tmp_path / "ep_0005.txt").exists()

    def test_run_pass_result_post_pass_pipeline_delegates_to_runtime(self):
        pp = self._make_pp()
        pp.post_pass_runtime._submit_manager_async = MagicMock(
            return_value={
                "bible_future": None,
                "current_state": {"state": "snapshot"},
                "lore_list": ["lore"],
                "active_seeds": ["seed-1"],
                "causal_history": "history",
            }
        )
        pp.post_pass_runtime._memorize_and_validate = MagicMock()
        pp.post_pass_runtime._collect_manager_and_build_delta = MagicMock(
            return_value={
                "bible_delta": {"relationship_changes": []},
                "actual_truth": {"location": "gate"},
                "state_truth_owner_contract": {"field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}},
                "meta_save_failed": True,
            }
        )
        pp.post_pass_runtime._save_world_state_atomic = MagicMock()
        pp.post_pass_runtime._run_post_pass_advisories = MagicMock()

        result = pp._run_pass_result_post_pass_pipeline(
            next_ep=6,
            final_manuscript="test manuscript",
            final_title="episode title",
            final_state_updates={"hp": 10},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 2},
            extract_chain_link_fn=lambda *_args, **_kwargs: {"cliffhanger": "next hook"},
            quality_labels={"score": 94},
            quality_signals={"ced_score": 0.5},
            detect_npc_overexposure_fn=lambda *_args, **_kwargs: None,
            detect_cross_episode_repetition_fn=lambda *_args, **_kwargs: None,
            v50_modules_available=False,
        )

        assert result == {
            "bible_delta": {"relationship_changes": []},
            "actual_truth": {"location": "gate"},
            "state_truth_owner_contract": {"field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}},
            "meta_save_failed": True,
        }
        pp.ctx.current_project.db.save_anchor.assert_called_once_with(
            "chain_link_6",
            {
                "cliffhanger": "next hook",
                "pending_actions": [],
                "physical_state": "정상",
            },
        )
        pp.post_pass_runtime._save_world_state_atomic.assert_called_once_with(
            next_ep=6,
            actual_truth={"location": "gate"},
            final_state_updates={"hp": 10},
            bible_delta={"relationship_changes": []},
        )
        pp.post_pass_runtime._run_post_pass_advisories.assert_called_once()
        assert (
            pp.post_pass_runtime._run_post_pass_advisories.call_args.kwargs["state_truth_owner_contract"]
            == {"field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}}
        )

    def test_run_pass_result_post_pass_pipeline_normalizes_nonwuxia_soft_chain_link_before_save(self):
        pp = self._make_pp()
        pp.ctx.selected_genre = {"type": "investment"}
        pp.post_pass_runtime._submit_manager_async = MagicMock(
            return_value={
                "bible_future": None,
                "current_state": {"state": "snapshot"},
                "lore_list": ["lore"],
                "active_seeds": ["seed-1"],
                "causal_history": "history",
            }
        )
        pp.post_pass_runtime._memorize_and_validate = MagicMock()
        pp.post_pass_runtime._collect_manager_and_build_delta = MagicMock(
            return_value={
                "bible_delta": {"relationship_changes": []},
                "actual_truth": {"location": "gate"},
                "state_truth_owner_contract": {},
                "meta_save_failed": False,
            }
        )
        pp.post_pass_runtime._save_world_state_atomic = MagicMock()
        pp.post_pass_runtime._run_post_pass_advisories = MagicMock()

        pp._run_pass_result_post_pass_pipeline(
            next_ep=6,
            final_manuscript="test manuscript",
            final_title="episode title",
            final_state_updates={"hp": 10},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 2},
            extract_chain_link_fn=lambda *_args, **_kwargs: {
                "cliffhanger": "전화가 오기 직전 멈칫했다.",
                "pending_actions": ["전화를 받기", "현관으로 이동하기"],
                "emotional_state": "긴장",
                "physical_state": "신경계 피로 Moderate",
                "location": "서재 앞 복도",
                "time_marker": "직후",
            },
            quality_labels={"score": 94},
            quality_signals={"ced_score": 0.5},
            detect_npc_overexposure_fn=lambda *_args, **_kwargs: None,
            detect_cross_episode_repetition_fn=lambda *_args, **_kwargs: None,
            v50_modules_available=False,
        )

        pp.ctx.current_project.db.save_anchor.assert_called_once_with(
            "chain_link_6",
            {
                "cliffhanger": "전화가 오기 직전 멈칫했다.",
                "pending_actions": [],
                "emotional_state": "긴장",
                "physical_state": "정상",
                "location": "서재 앞 복도",
                "time_marker": "직후",
                "soft_pending_actions": ["전화를 받기", "현관으로 이동하기"],
                "soft_physical_state": "신경계 피로 Moderate",
            },
        )

    def test_finalize_pass_result_session_saves_costs_and_flushes(self):
        pp = self._make_pp()
        collector = MagicMock()
        collector.session_id = "sess_ep"
        collector.snapshot_and_reset_scope.return_value = {
            "total_calls": 2,
            "total_tokens": 1800,
            "total_cost_usd": 0.017,
            "model_breakdown": "{\"gpt\": 2}",
        }

        with patch("modules.core.stage4_post_processor.get_metrics_collector", return_value=collector):
            pp._finalize_pass_result_session(
                next_ep=8,
                final_title="episode title",
                final_manuscript="test manuscript " * 200,
                arc_data={"arc_no": 3},
            )

        pp.ctx.current_project.db.save_cost_record.assert_called_once()
        pp.ctx.flush_audit_buffer.assert_called_once()
        pp.ctx.perf_timer.log_summary.assert_called_once()
        pp.ctx.perf_timer.reset.assert_called_once()

    def test_run_post_pass_satisfaction_and_pacing_saves_sidecars(self):
        pp = self._make_pp()
        pp.ctx.agents["state_extractor"].extract_satisfaction_tag.return_value = {
            "primary_tag": "immersive",
            "satisfaction_score": 9,
            "protagonist_agency": "high",
        }
        pp.ctx.pacing_analyzer = MagicMock()
        pp.ctx.pacing_analyzer.analyze.return_value = SimpleNamespace(
            pacing_score=88,
            dialogue_ratio=0.32,
            scene_break_count=4,
            avg_sentence_length=18.4,
            short_sentence_ratio=0.25,
            long_sentence_ratio=0.14,
            issues=["minor pacing dip"],
        )

        pp.post_pass_runtime._run_post_pass_satisfaction_and_pacing(
            next_ep=10,
            final_manuscript="test manuscript " * 120,
        )

        pp.ctx.current_project.db.save_satisfaction_tag.assert_called_once_with(
            10,
            {
                "primary_tag": "immersive",
                "satisfaction_score": 9,
                "protagonist_agency": "high",
            },
        )
        pp.ctx.current_project.db.save_pacing_record.assert_called_once()

    def test_record_post_pass_quality_dashboard_records_coverage_and_regression(self):
        pp = self._make_pp()
        pp.ctx.quality_dashboard = MagicMock()
        pp.ctx.quality_dashboard.detect_score_regression.return_value = {
            "is_regression": True,
            "delta": -4,
            "severity": "warning",
        }
        pp.ctx.agents["director"]._validate_blueprint_completeness_v60.return_value = {
            "valid": False,
            "scene_coverage": 75.0,
        }

        pp.post_pass_runtime._record_post_pass_quality_dashboard(
            next_ep=11,
            final_manuscript="test manuscript " * 140,
            blueprint={"scene_breakdown": ["a", "b", "c", "d"]},
            final_state_updates={"director_score": 92},
            quality_labels={"score": 94},
            quality_signals={"ced_score": 0.7},
            state_truth_owner_contract={
                "field_families": {
                    "numeric_carryover_authority": {
                        "fields": ["capital", "total_assets"],
                    }
                }
            },
        )

        pp.ctx.quality_dashboard.record_blueprint_coverage.assert_called_once()
        pp.ctx.quality_dashboard.record_validation.assert_called_once()
        record_kwargs = pp.ctx.quality_dashboard.record_validation.call_args.kwargs
        assert record_kwargs["result"]["state_truth_owner_contract"] == {
            "field_families": {
                "numeric_carryover_authority": {
                    "fields": ["capital", "total_assets"],
                }
            }
        }
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("품질 회귀" in text for text in log_calls)

    def test_run_post_pass_npc_and_repetition_guards_logs_warnings_and_stores_hashes(self):
        pp = self._make_pp()
        pp.ctx.state_tracker = MagicMock()
        pp.ctx.state_tracker.npc_registry = {"수호": {}, "세령": {}}
        pp.ctx.current_project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {"KeyNPCs": [{"name": "수호"}]},
            }
        }
        pp.ctx.current_project.db.find_repeated_sentence_hashes.return_value = ["hash-1"]

        def _threshold_side_effect(key, default=None):
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            with patch(
                "modules.core.repetition_guard.RepetitionGuard.extract_sentence_fingerprints",
                return_value=[("hash-1", "repeat sentence")],
            ):
                pp.post_pass_runtime._run_post_pass_npc_and_repetition_guards(
                    next_ep=12,
                    final_manuscript="repeat sentence",
                    detect_npc_overexposure_fn=lambda *_args, **_kwargs: {"warning": "npc warning"},
                    detect_cross_episode_repetition_fn=lambda *_args, **_kwargs: {"warning": "repeat warning"},
                )

        pp.ctx.current_project.db.store_sentence_hashes.assert_called_once_with(
            12,
            [("hash-1", "repeat sentence")],
        )
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("npc warning" in text for text in log_calls)
        assert any("repeat warning" in text for text in log_calls)

    def test_chain_link_fn_called(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        mock_fn = MagicMock(return_value={"cliffhanger": "test"})
        manuscript = "테스트 원고 " * 500

        pp.process_pass_result(
            next_ep=5,
            final_manuscript=manuscript,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=mock_fn,
        )

        mock_fn.assert_called_once_with(
            5,
            Stage4PostProcessor._normalize_reader_facing_manuscript(manuscript),
            {"scene_breakdown": []},
        )

    def test_records_episode_cost_when_scope_has_usage(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True

        collector = MagicMock()
        collector.session_id = "sess_ep"
        collector.snapshot_and_reset_scope.return_value = {
            "total_calls": 3,
            "total_tokens": 2400,
            "total_cost_usd": 0.021,
            "model_breakdown": "{}",
        }

        with patch("modules.core.stage4_post_processor.get_metrics_collector", return_value=collector):
            result = pp.process_pass_result(
                next_ep=2,
                final_manuscript="테스트 원고 " * 500,
                final_title="테스트",
                final_state_updates={},
                blueprint={"scene_breakdown": []},
                arc_data={"arc_no": 1},
                output_dir=tmp_path,
                v50_modules_available=False,
                extract_chain_link_fn=lambda *_args, **_kwargs: {},
            )

        assert result is True
        pp.ctx.current_project.db.save_cost_record.assert_called_once()
        cost_kw = pp.ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kw["scope_type"] == "episode"
        assert cost_kw["scope_id"] == 2
        assert cost_kw["total_calls"] == 3

    def test_logs_episode_summary_after_cost_snapshot(self, tmp_path, caplog):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "3인칭", "external_pov_insert_policy": "제한적 허용"}}
        }

        collector = MagicMock()
        collector.session_id = "sess_ep"
        collector.snapshot_and_reset_scope.return_value = {
            "total_calls": 4,
            "total_tokens": 3600,
            "total_cost_usd": 0.034,
            "model_breakdown": "{}",
        }

        with patch("modules.core.stage4_post_processor.get_metrics_collector", return_value=collector):
            with caplog.at_level(logging.INFO):
                result = pp.process_pass_result(
                    next_ep=4,
                    final_manuscript="test manuscript " * 400,
                    final_title="episode title",
                    final_state_updates={},
                    blueprint={"scene_breakdown": []},
                    arc_data={"arc_no": 2},
                    output_dir=tmp_path,
                    v50_modules_available=False,
                    extract_chain_link_fn=lambda *_args, **_kwargs: {},
                )

        assert result is True
        assert "[EPISODE_SUMMARY]" in caplog.text
        assert "stage=4 ep=4 arc=2" in caplog.text
        assert "total_calls=4" in caplog.text
        assert "total_tokens=3600" in caplog.text
        assert "primary_pov=3인칭" in caplog.text
        assert "external_pov_insert_policy=제한적 허용" in caplog.text
        assert "style_guide_extracted_pov=-" in caplog.text

    def test_bible_delta_time_passed_uses_time_passed_field(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "state_updates": {
                "time_passed": "3일",
                "location": "무당산",
            }
        }

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.current_project.db.save_episode_bible.assert_called_once()
        _args, _kwargs = pp.ctx.current_project.db.save_episode_bible.call_args
        bible_delta = _args[1]
        assert bible_delta["time_passed"] == "3일"

    def test_resolve_manager_audit_retries_after_future_failure(self):
        pp = self._make_pp()
        future = MagicMock()
        future.result.side_effect = RuntimeError("future boom")
        future.cancel = MagicMock()
        expected_audit = {"state_updates": {"location": "무당산"}}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = expected_audit

        result = pp.post_pass_runtime._resolve_manager_audit(
            next_ep=7,
            final_manuscript="후처리 테스트 원고",
            bible_future=future,
            current_state={"actual_truth": {}},
            lore_list=[],
            active_seeds=[],
            causal_history="",
            genre_type="wuxia",
            critical_keys=["독", "추격"],
        )

        assert result == expected_audit
        future.cancel.assert_called_once_with()
        pp.ctx.agents["manager"].update_state_and_lore_v20.assert_called_once()
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("Manager 정산 대기" in text for text in log_calls)
        assert any("동기 재시도 전환" in text for text in log_calls)
        assert any("Manager 동기 재시도 성공" in text for text in log_calls)

    def test_prepare_manager_delta_context_normalizes_inventory_and_pressure_vectors(self):
        pp = self._make_pp()
        pp.ctx.current_project.latest_state = {
            "actual_truth": {
                "inventory_counts": {"은자": 1},
                "active_pressure_vectors": [{"text": "추격대가 다가온다.", "source": "ending_hook"}],
            }
        }

        result = pp.post_pass_runtime._prepare_manager_delta_context(
            audit={
                "state_updates": {
                    "actual_truth": {
                        "equipment": ["은자 3개", "독수리 비검"],
                    }
                }
            },
            genre_type="wuxia",
        )

        assert result["prev_pressure_vectors"][0]["text"] == "추격대가 다가온다."
        assert result["curr_inventory_counts"] == {"독수리 비검": 1, "은자": 3}
        assert result["actual_truth"]["inventory_counts"] == {"독수리 비검": 1, "은자": 3}
        assert {"name": "은자", "from": 1, "to": 3, "delta": 2} in result["inventory_count_deltas"]

    def test_collect_manager_and_build_delta_normalizes_dict_martial_arts(self):
        pp = self._make_pp()
        pp.ctx.current_project.latest_state = {
            "actual_truth": {
                "martial_arts": [{"name": "Storm Palm"}],
            }
        }
        pp.post_pass_runtime._resolve_manager_audit = MagicMock(
            return_value={
                "state_updates": {
                    "actual_truth": {
                        "martial_arts": [
                            {"name": "Storm Palm"},
                            {"name": "Cloud Step", "realm": "Peak"},
                            {"main_technique": "Heavenly Blade"},
                            {"unknown": "ignored"},
                        ]
                    }
                }
            }
        )
        pp.post_pass_runtime._build_manager_delta_collections = MagicMock(
            return_value={
                "new_npc_names": [],
                "npc_deaths": [],
                "relationship_changes": [],
                "karma_matrix": [],
                "reveal_list": [],
            }
        )
        pp.post_pass_runtime._apply_state_text_and_pressure_vectors = MagicMock(
            side_effect=lambda **kwargs: {
                "actual_truth": kwargs["actual_truth"],
                "active_pressure_vectors": [],
                "pressure_vectors_changed": False,
            }
        )
        pp.post_pass_runtime._persist_manager_delta_outputs = MagicMock(
            return_value={
                "bible_delta": {"state_changes": {}},
                "state_truth_owner_contract": {"field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}},
                "meta_save_failed": False,
            }
        )

        result = pp.post_pass_runtime._collect_manager_and_build_delta(
            next_ep=11,
            final_manuscript="test manuscript",
            bible_future=None,
            current_state={"actual_truth": {}},
            lore_list=[],
            active_seeds=[],
            causal_history="",
            genre_type="wuxia",
            critical_keys=[],
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={},
        )

        assert result["meta_save_failed"] is False
        assert result["bible_delta"] == {"state_changes": {}}
        assert result["state_truth_owner_contract"] == {
            "field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}
        }
        assert set(pp.post_pass_runtime._persist_manager_delta_outputs.call_args.kwargs["all_new_items"]) == {
            "Cloud Step",
            "Heavenly Blade",
        }

    def test_prepare_manager_delta_context_parses_stringified_martial_arts_list(self):
        pp = self._make_pp()

        result = pp.post_pass_runtime._prepare_manager_delta_context(
            audit={
                "state_updates": {
                    "actual_truth": {
                        "martial_arts": '["Storm Palm", {"name": "Cloud Step"}, "Storm Palm"]'
                    }
                }
            },
            genre_type="wuxia",
        )

        assert result["actual_truth"]["martial_arts"] == ["Storm Palm", "Cloud Step"]

    def test_merge_manager_key_npcs_into_master_bible_merges_existing_and_new_entries(self):
        pp = self._make_pp()
        pp.ctx.current_project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "윤호", "role": "문지기"},
                    ]
                }
            }
        }

        pp.post_pass_runtime._merge_manager_key_npcs_into_master_bible(
            next_ep=8,
            key_npcs=[
                {"name": "윤호", "position": "수문장"},
                {"name": "서린", "role": "밀사"},
            ],
        )

        merged_npcs = pp.ctx.current_project.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"]
        assert merged_npcs[0]["position"] == "수문장"
        assert any(npc.get("name") == "서린" for npc in merged_npcs)

    def test_build_manager_delta_collections_builds_relationships_deaths_and_reveals(self):
        pp = self._make_pp()
        pp.post_pass_runtime._merge_manager_key_npcs_into_master_bible = MagicMock()

        result = pp.post_pass_runtime._build_manager_delta_collections(
            next_ep=9,
            key_npcs=[
                {"name": "윤호", "NPC_Martial_HUD": {"current_status": "사망"}},
                {"name": "서린", "NPC_Martial_HUD": {"current_status": "생존"}},
            ],
            knowledge_map={"new_witnesses": ["윤호"], "new_misled": ["서린"]},
            state_updates_from_audit={
                "karma_matrix": [
                    {"target": "서린", "obsession": 80, "value": 20},
                    {"target": "도현", "obsession": 10, "value": 70},
                ]
            },
            recovered=[{"seed_id": "seed-01"}, "seed-02"],
        )

        assert result["new_npc_names"] == ["윤호", "서린"]
        assert result["npc_deaths"] == ["윤호"]
        assert {"npc": "윤호", "to": "목격자", "from": ""} in result["relationship_changes"]
        assert {"npc": "서린", "to": "집착80/오해20", "from": ""} in result["relationship_changes"]
        assert result["reveal_list"] == ["seed-01", "seed-02"]
        pp.post_pass_runtime._merge_manager_key_npcs_into_master_bible.assert_called_once_with(
            next_ep=9,
            key_npcs=[
                {"name": "윤호", "NPC_Martial_HUD": {"current_status": "사망"}},
                {"name": "서린", "NPC_Martial_HUD": {"current_status": "생존"}},
            ],
        )


    def test_apply_state_text_and_pressure_vectors_injects_pressure_vector_snapshot(self):
        pp = self._make_pp()
        pp.post_pass_runtime._build_active_pressure_vectors = MagicMock(
            return_value=[{"text": "pressure vector", "source": "ending_hook"}]
        )
        pp.post_pass_runtime._filter_active_pressure_vectors_by_manuscript = MagicMock(
            return_value=[{"text": "pressure vector", "source": "ending_hook"}]
        )

        result = pp.post_pass_runtime._apply_state_text_and_pressure_vectors(
            actual_truth={"location": "gate"},
            final_manuscript="test manuscript",
            genre_type="wuxia",
            critical_keys=["gate"],
            blueprint={"ending_hook": "pressure vector"},
            prev_pressure_vectors=[],
        )

        assert result["active_pressure_vectors"] == [{"text": "pressure vector", "source": "ending_hook"}]
        assert result["pressure_vectors_changed"] is True
        assert result["actual_truth"]["active_pressure_vectors"] == [{"text": "pressure vector", "source": "ending_hook"}]

    def test_apply_state_text_and_pressure_vectors_clears_unsupported_pressure_vectors(self):
        pp = self._make_pp()

        result = pp.post_pass_runtime._apply_state_text_and_pressure_vectors(
            actual_truth={"location": "gate"},
            final_manuscript="강민철은 계약서를 접어 재킷 안주머니에 넣고 자리에서 일어섰다. 그는 PB의 시선을 피하지 않았다.",
            genre_type="investment",
            critical_keys=["gate"],
            blueprint={"ending_hook": "정체불명의 그림자가 들이닥치기 시작했다."},
            prev_pressure_vectors=[{"text": "정체불명의 그림자가 들이닥치기 시작했다.", "source": "ending_hook"}],
        )

        assert result["active_pressure_vectors"] == []
        assert result["pressure_vectors_changed"] is True
        assert result["actual_truth"]["active_pressure_vectors"] == []

    def test_persist_manager_delta_outputs_saves_bible_and_delegates_side_effect_sinks(self):
        pp = self._make_pp()
        pp.post_pass_runtime._sync_world_state_positions = MagicMock()
        pp.post_pass_runtime._persist_manager_causal_side_effects = MagicMock()
        pp.post_pass_runtime._persist_manager_state_log = MagicMock()
        pp.post_pass_runtime._persist_karma_status = MagicMock()
        pp.post_pass_runtime._log_manager_delta_summary = MagicMock()
        pp.post_pass_runtime._emit_post_pass_contract_signal = MagicMock()
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger.get_numbers.return_value = {
            "capital": {"value": 1000000000, "unit": "won", "authority_scope": "carryover_baseline"},
            "total_assets": {"value": 2000000000, "unit": "won", "authority_scope": "carryover_baseline"},
            "debt": {"value": 0, "unit": "won", "authority_scope": "runtime_overlay"},
        }

        result = pp.post_pass_runtime._persist_manager_delta_outputs(
            next_ep=10,
            key_npcs=[{"name": "npc-a"}],
            actual_truth={"location": "gate"},
            final_state_updates={"hp": 90},
            arc_data={},
            state_updates_from_audit={"time_passed": "3h"},
            knowledge_map={"new_witnesses": ["npc-a"]},
            karma_matrix=[{"target": "npc-b", "obsession": 70, "value": 10}],
            curr_inventory_counts={"sword": 2},
            inventory_count_deltas=[{"name": "sword", "from": 1, "to": 2, "delta": 1}],
            relationship_changes=[{"npc": "npc-b", "to": "obsession70/misread10", "from": ""}],
            active_pressure_vectors=[{"text": "pressure vector", "source": "ending_hook"}],
            pressure_vectors_changed=True,
            causal_links=[{"cause": "seed", "effect": "payoff"}],
            all_new_items=["sword"],
            lost_items_from_equip=[],
            new_npc_names=["npc-a"],
            npc_deaths=[],
            reveal_list=["seed-01"],
        )

        assert result["meta_save_failed"] is False

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["active_pressure_vectors"] == [{"text": "pressure vector", "source": "ending_hook"}]
        assert saved_bible["inventory_count_deltas"] == [{"name": "sword", "from": 1, "to": 2, "delta": 1}]
        owner_contract = saved_bible["state_truth_owner_contract"]
        assert owner_contract["actual_truth_primary_owner"] == "manager_actual_truth"
        assert owner_contract["field_families"]["inventory_counts"]["owner"] == "runtime_storage_overlay"
        assert owner_contract["field_families"]["active_pressure_vectors"]["owner"] == "runtime_blueprint_overlay"
        assert owner_contract["field_families"]["numeric_carryover_authority"] == {
            "owner": "fact_ledger_carryover_baseline",
            "surfaces": [
                "fact_ledger",
                "episode_bible.state_truth_owner_contract",
                "state_log.state_truth_owner_contract",
            ],
            "fields": ["capital", "total_assets"],
            "authority_scope": "carryover_baseline",
            "provenance": "fact_ledger_authority_scope",
        }
        state_log_contract = pp.post_pass_runtime._persist_manager_state_log.call_args.kwargs["state_truth_owner_contract"]
        assert state_log_contract["field_families"]["numeric_carryover_authority"]["fields"] == ["capital", "total_assets"]
        pp.post_pass_runtime._sync_world_state_positions.assert_called_once_with(
            next_ep=10,
            key_npcs=[{"name": "npc-a"}],
        )
        pp.post_pass_runtime._persist_manager_causal_side_effects.assert_called_once_with(
            next_ep=10,
            causal_links=[{"cause": "seed", "effect": "payoff"}],
        )
        pp.post_pass_runtime._persist_manager_state_log.assert_called_once()
        pp.post_pass_runtime._persist_karma_status.assert_called_once()
        pp.post_pass_runtime._log_manager_delta_summary.assert_called_once()
        pp.post_pass_runtime._emit_post_pass_contract_signal.assert_called_once_with(
            next_ep=10,
            state_truth_owner_contract=owner_contract,
        )

    def test_log_numeric_carryover_authority_summary_emits_ui_note(self):
        pp = self._make_pp()

        pp.post_pass_runtime._log_numeric_carryover_authority_summary(
            state_truth_owner_contract={
                "field_families": {
                    "numeric_carryover_authority": {
                        "fields": ["capital", "total_assets"],
                        "authority_scope": "carryover_baseline",
                        "provenance": "fact_ledger_authority_scope",
                    }
                }
            }
        )

        pp.ctx.ui.log.assert_any_call(
            "      [numeric carryover authority] capital, total_assets [carryover_baseline] (fact_ledger_authority_scope)"
        )

    def test_emit_post_pass_contract_signal_persists_jsonl_and_audit(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.audit_event = MagicMock()
        pp.ctx.current_project.name = "postpass-demo"
        pp.ctx.current_project.paths = type("Paths", (), {"root": tmp_path})()

        pp.post_pass_runtime._emit_post_pass_contract_signal(
            next_ep=4,
            state_truth_owner_contract={
                "actual_truth_primary_owner": "manager_actual_truth",
                "field_families": {
                    "numeric_carryover_authority": {
                        "fields": ["capital", "total_assets"],
                        "authority_scope": "carryover_baseline",
                        "provenance": "fact_ledger_authority_scope",
                    }
                },
            },
        )

        log_path = tmp_path / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        contract_rows = [row for row in rows if row.get("event") == "STAGE4_POST_PASS_CONTRACT"]
        assert len(contract_rows) == 1
        assert contract_rows[0]["ep"] == 4
        assert contract_rows[0]["session_id"] == "sess-post-pass"
        assert contract_rows[0]["numeric_carryover_authority"]["fields"] == ["capital", "total_assets"]
        assert contract_rows[0]["numeric_carryover_summary"] == {
            "owner": "",
            "fields": ["capital", "total_assets"],
            "authority_scope": "carryover_baseline",
            "provenance": "fact_ledger_authority_scope",
            "ui_note": "capital, total_assets [carryover_baseline] (fact_ledger_authority_scope)",
            "operator_note": (
                "numeric_carryover_authority owns capital, total_assets "
                "[carryover_baseline] (fact_ledger_authority_scope)"
            ),
        }
        assert contract_rows[0]["state_truth_owner_contract"]["actual_truth_primary_owner"] == "manager_actual_truth"
        pp.ctx.audit_event.assert_any_call(
            "stage4_post_pass_contract_signal",
            "stage4 post-pass contract persisted",
            contract_rows[0],
        )

    def test_persist_manager_delta_outputs_merges_npc_martial_state_changes_from_arc_data(self):
        pp = self._make_pp()
        pp.post_pass_runtime._sync_world_state_positions = MagicMock()
        pp.post_pass_runtime._persist_manager_causal_side_effects = MagicMock()
        pp.post_pass_runtime._persist_manager_state_log = MagicMock()
        pp.post_pass_runtime._persist_karma_status = MagicMock()
        pp.post_pass_runtime._log_manager_delta_summary = MagicMock()

        result = pp.post_pass_runtime._persist_manager_delta_outputs(
            next_ep=10,
            key_npcs=[],
            actual_truth={"location": "gate"},
            final_state_updates={},
            arc_data={
                "state_changes": {
                    "npc_martial_state_changes": [
                        {
                            "name": "Chief Han",
                            "episode": 10,
                            "realm": "Peak",
                            "techniques_learned": ["Storm Palm"],
                        }
                    ]
                }
            },
            state_updates_from_audit={},
            knowledge_map={},
            karma_matrix=[],
            curr_inventory_counts={},
            inventory_count_deltas=[],
            relationship_changes=[],
            active_pressure_vectors=[],
            pressure_vectors_changed=False,
            causal_links=[],
            all_new_items=[],
            lost_items_from_equip=[],
            new_npc_names=[],
            npc_deaths=[],
            reveal_list=[],
        )

        assert result["meta_save_failed"] is False
        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["location"] == "gate"
        assert saved_bible["state_changes"]["npc_martial_state_changes"] == [
            {
                "name": "Chief Han",
                "episode": 10,
                "realm": "Peak",
                "techniques_learned": ["Storm Palm"],
            }
        ]
        owner_contract = saved_bible["state_truth_owner_contract"]
        assert owner_contract["field_families"]["npc_martial_state_changes"]["owner"] == "arc_state_changes_world_only"

    def test_overexposure_receives_empty_protagonist_name_when_callback_returns_none(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.state_tracker = MagicMock()
        pp.ctx.state_tracker.npc_registry = {"조연": {"status": "alive"}}
        pp.ctx.get_protagonist_name = lambda: None

        detector = MagicMock(return_value=None)

        result = pp.process_pass_result(
            next_ep=4,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
            detect_npc_overexposure_fn=detector,
        )

        assert result is True
        detector.assert_called_once()
        assert detector.call_args.args[2] == ""

    def test_vector_memory_summary_normalized_to_four_slots(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.memory = MagicMock()
        pp.ctx.memory.is_operational.return_value = True

        result = pp.process_pass_result(
            next_ep=2,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트 타이틀",
            final_state_updates={
                "npc_deaths": [{"name": "철수"}],
                "relationship_changes": [{"npc": "영희", "change": "적대"}],
                "major_items": [{"name": "청룡검"}],
            },
            blueprint={"end_location": "서울", "ending_hook": "다음 화에서 반격"},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.memory.memorize_v20_episode.assert_called_once()
        kwargs = pp.ctx.memory.memorize_v20_episode.call_args.kwargs
        summary = kwargs["summary"]
        assert "사건:" in summary
        assert "인물:" in summary
        assert "장소:" in summary
        assert "결말:" in summary
        assert "서울" in summary
        assert "다음 화에서 반격" in summary
        assert "death" in kwargs["event_types"]
        assert "철수" in kwargs["entity_names"]

    def test_vector_memory_summary_fallback_when_blueprint_and_entities_empty(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.memory = MagicMock()
        pp.ctx.memory.is_operational.return_value = True

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="테스트 원고 " * 500,
            final_title="",
            final_state_updates={},
            blueprint={},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.memory.memorize_v20_episode.assert_called_once()
        kwargs = pp.ctx.memory.memorize_v20_episode.call_args.kwargs
        assert kwargs["summary"] == "사건: 제3화"
        assert kwargs["event_types"] == []
        assert kwargs["entity_names"] == []

    def test_manager_sync_retry_runs_when_async_future_fails(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {},
            "causal_links": [],
        }

        class _BrokenFuture:
            def result(self, timeout=None):
                raise TimeoutError("async manager timeout")

        class _BrokenExecutor:
            def __init__(self, *args, **kwargs):
                pass

            def submit(self, *args, **kwargs):
                return _BrokenFuture()

            def shutdown(self, wait=False, cancel_futures=False):
                return None

        with patch("concurrent.futures.ThreadPoolExecutor", _BrokenExecutor):
            result = pp.process_pass_result(
                next_ep=6,
                final_manuscript="테스트 원고 " * 500,
                final_title="테스트",
                final_state_updates={},
                blueprint={"scene_breakdown": []},
                arc_data={"arc_no": 1},
                output_dir=tmp_path,
                v50_modules_available=False,
                extract_chain_link_fn=lambda *_args, **_kwargs: {},
            )

        assert result is True
        assert pp.ctx.agents["manager"].update_state_and_lore_v20.call_count == 1
        assert any("Manager 동기 재시도 성공" in str(c.args[0]) for c in pp.ctx.ui.log.call_args_list)

    def test_records_stage4_validation_when_quality_dashboard_present(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.quality_dashboard = MagicMock()
        pp.ctx.quality_dashboard.detect_score_regression.return_value = {"is_regression": False, "severity": "none"}

        result = pp.process_pass_result(
            next_ep=7,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.quality_dashboard.record_validation.assert_called_once()
        record_kwargs = pp.ctx.quality_dashboard.record_validation.call_args.kwargs
        assert record_kwargs["ep_num"] == 7
        assert record_kwargs["stage"] == 4
        assert record_kwargs["result"]["decision"] == "PASS"
        assert "state_truth_owner_contract" in record_kwargs["result"]

    def test_records_quality_signals_on_dashboard_validation(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.quality_dashboard = MagicMock()
        pp.ctx.quality_dashboard.detect_score_regression.return_value = {"is_regression": False, "severity": "none"}

        result = pp.process_pass_result(
            next_ep=8,
            final_manuscript="그야말로 숨을 삼켰다. 말 그대로 시선을 돌렸다. " * 120,
            final_title="테스트",
            final_state_updates={
                "_director_quality_labels": {
                    "score": 95,
                    "verdict": "PASS",
                    "consistency_checklist": {"pacing_quality": "ISSUE"},
                }
            },
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        record_kwargs = pp.ctx.quality_dashboard.record_validation.call_args.kwargs
        assert record_kwargs["result"]["score"] == 95
        assert record_kwargs["result"]["quality_signals"]["ced_score"] > 0

    def test_records_blueprint_coverage_on_dashboard(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.quality_dashboard = MagicMock()
        pp.ctx.quality_dashboard.detect_score_regression.return_value = {"is_regression": False, "severity": "none"}
        pp.ctx.agents["director"]._validate_blueprint_completeness_v60.return_value = {
            "valid": False,
            "scene_coverage": 62.5,
            "expected_scenes": 4,
            "reflected_scenes": 2,
            "warnings": ["씬 반영률 62.5%"],
        }

        result = pp.process_pass_result(
            next_ep=9,
            final_manuscript="장면 하나만 짧게 스치고 지나갔다. " * 120,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": ["scene1", "scene2", "scene3", "scene4"]},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.ctx.quality_dashboard.record_blueprint_coverage.assert_called_once()
        kwargs = pp.ctx.quality_dashboard.record_blueprint_coverage.call_args.kwargs
        assert kwargs["ep_num"] == 9
        assert kwargs["coverage_result"]["scene_coverage"] == 62.5

    def test_inventory_counts_flow_into_state_log_and_state_sinks(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {
            "actual_truth": {"equipment": ["트레이딩용 컴퓨터 2대", "모니터 2대"]}
        }
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "actual_truth": {
                    "equipment": ["트레이딩용 컴퓨터 3대", {"name": "모니터", "count": 2}],
                }
            },
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 2}

        result = pp.process_pass_result(
            next_ep=6,
            final_manuscript="사무실 안에는 트레이딩용 컴퓨터 3대와 모니터 2대가 켜져 있었다. " * 120,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 2},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        assert saved_state_log["actual_truth"]["inventory_counts"] == {
            "모니터": 2,
            "트레이딩용 컴퓨터": 3,
        }
        assert saved_state_log["inventory_count_deltas"] == [
            {"name": "트레이딩용 컴퓨터", "from": 2, "to": 3, "delta": 1},
        ]

        world_state_changes = pp.ctx.world_state.update_from_state_changes.call_args.args[1]
        assert world_state_changes["inventory_counts"] == {
            "모니터": 2,
            "트레이딩용 컴퓨터": 3,
        }
        assert world_state_changes["inventory_count_deltas"] == [
            {"name": "트레이딩용 컴퓨터", "from": 2, "to": 3, "delta": 1},
        ]

        fact_ledger_changes = pp.ctx.fact_ledger.update_from_state_changes.call_args.args[1]
        assert fact_ledger_changes["inventory_counts"] == {
            "모니터": 2,
            "트레이딩용 컴퓨터": 3,
        }

    def test_relationship_changes_flow_into_state_log_and_state_sinks(self, tmp_path):
        """relationship_changes가 dict 형식으로 state_log, world_state, fact_ledger에 전달되는지 검증."""
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {
                "new_witnesses": ["박영호"],
                "new_misled": ["이서연"],
            },
            "recovered_seeds": [],
            "state_updates": {},
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 2, "items": 0}

        result = pp.process_pass_result(
            next_ep=3,
            final_manuscript="박영호는 그 장면을 목격했다. 이서연은 아직 진실을 모른다. " * 120,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True

        # state_log에 relationship_changes 존재
        pp.ctx.current_project.db.save_state_log_with_summary.assert_called_once()
        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        rel_in_log = saved_state_log["relationship_changes"]
        assert len(rel_in_log) == 2
        assert all(isinstance(r, dict) for r in rel_in_log)
        assert rel_in_log[0] == {"npc": "박영호", "to": "목격자", "from": ""}
        assert rel_in_log[1] == {"npc": "이서연", "to": "오해 대상", "from": ""}

        # world_state에 relationship_changes 전달
        ws_changes = pp.ctx.world_state.update_from_state_changes.call_args.args[1]
        assert "relationship_changes" in ws_changes
        assert ws_changes["relationship_changes"][0]["npc"] == "박영호"

        # fact_ledger에 relationship_changes 전달
        fl_changes = pp.ctx.fact_ledger.update_from_state_changes.call_args.args[1]
        assert "relationship_changes" in fl_changes
        assert fl_changes["relationship_changes"][1]["npc"] == "이서연"

    def test_karma_matrix_flows_into_karma_status_table(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.current_project.karma_status = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "karma_matrix": [
                    {"target": "npc_a", "value": 61, "obsession": 12},
                    {"npc_name": "npc_b", "misunderstanding": 7, "obsession": 3},
                    {"obsession": 99},
                ]
            },
            "causal_links": [],
        }

        result = pp.process_pass_result(
            next_ep=4,
            final_manuscript="karma sink test " * 120,
            final_title="test",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        assert pp.ctx.current_project.db.update_karma.call_count == 2
        assert pp.ctx.current_project.db.update_karma.call_args_list[0].args == ("npc_a", 61, 12, 4)
        assert pp.ctx.current_project.db.update_karma.call_args_list[1].args == ("npc_b", 7, 3, 4)
        assert pp.ctx.current_project.karma_status["npc_a"]["last_updated_ep"] == 4
        assert pp.ctx.current_project.karma_status["npc_b"]["misunderstanding"] == 7

    def test_active_pressure_vectors_flow_into_state_log_bible_and_world_state(self, tmp_path):
        """ending_hook/cliffhanger가 active_pressure_vectors로 persisted canonical path에 들어가는지 검증."""
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {},
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 0}

        result = pp.process_pass_result(
            next_ep=4,
            final_manuscript="독이 퍼지기 시작했다. 해독제가 필요하다. 흑풍회의 추격대가 문 앞에 도착했다. " * 120,
            final_title="테스트",
            final_state_updates={},
            blueprint={
                "scene_breakdown": [],
                "ending_hook": "독이 퍼지기 시작했다. 해독제가 필요하다.",
                "cliffhanger": "흑풍회의 추격대가 문 앞에 도착했다.",
            },
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True

        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        owner_contract = saved_state_log["state_truth_owner_contract"]
        assert owner_contract["actual_truth_primary_owner"] == "manager_actual_truth"
        assert owner_contract["field_families"]["active_pressure_vectors"]["owner"] == "runtime_blueprint_overlay"
        assert owner_contract["field_families"]["active_pressure_vectors"]["provenance"] == "blueprint_filtered_by_manuscript"
        assert saved_state_log["actual_truth"]["active_pressure_vectors"][0]["source"] == "ending_hook"
        assert saved_state_log["active_pressure_vectors"][1]["text"] == "흑풍회의 추격대가 문 앞에 도착했다."

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["active_pressure_vectors"][0]["text"] == "독이 퍼지기 시작했다. 해독제가 필요하다."

        ws_changes = pp.ctx.world_state.update_from_state_changes.call_args.args[1]
        assert ws_changes["active_pressure_vectors"][1]["text"] == "흑풍회의 추격대가 문 앞에 도착했다."

        pp.ctx.fact_ledger.update_from_state_changes.assert_not_called()

    def test_process_pass_result_clears_unsupported_pressure_vectors_from_persistence(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {
            "actual_truth": {
                "active_pressure_vectors": [{"text": "정체불명의 그림자가 들이닥치기 시작했다.", "source": "ending_hook"}]
            }
        }
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {},
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 0}

        result = pp.process_pass_result(
            next_ep=4,
            final_manuscript="강민철은 계약서를 접어 재킷 안주머니에 넣고 자리에서 일어섰다. 그는 PB의 시선을 피하지 않았다. " * 40,
            final_title="테스트",
            final_state_updates={},
            blueprint={
                "scene_breakdown": [],
                "ending_hook": "정체불명의 그림자가 들이닥치기 시작했다.",
                "cliffhanger": "철문 손잡이가 거칠게 돌아가기 시작했다.",
            },
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True

        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        assert saved_state_log["actual_truth"]["active_pressure_vectors"] == []
        assert saved_state_log["active_pressure_vectors"] == []

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["active_pressure_vectors"] == []

        ws_changes = pp.ctx.world_state.update_from_state_changes.call_args.args[1]
        assert ws_changes["active_pressure_vectors"] == []


    def test_process_pass_result_normalizes_martial_arts_before_stv_and_persistence(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "actual_truth": {
                    "martial_arts": [
                        {"name": "Storm Palm", "origin": "legacy manager shape"},
                        {"main_technique": "Cloud Step"},
                        "Storm Palm",
                        {"ignored": "drop me"},
                    ]
                }
            },
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 0}

        captured = {}

        def _threshold_side_effect(key, default=None):
            if key == "feature_flags.enable_state_text_verifier":
                return True
            return default

        def _verify_side_effect(_self, manuscript, actual_truth):
            captured["martial_arts"] = actual_truth.get("martial_arts")
            return {"verified": True, "mismatches": [], "corrections": {}, "blocking": False}

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect),
            patch(
                "modules.core.state_text_verifier.StateTextVerifier.verify",
                autospec=True,
                side_effect=_verify_side_effect,
            ),
        ):
            result = pp.process_pass_result(
                next_ep=5,
                final_manuscript="The manuscript explicitly references Storm Palm and Cloud Step. " * 120,
                final_title="test title",
                final_state_updates={},
                blueprint={"scene_breakdown": []},
                arc_data={"arc_no": 1},
                output_dir=tmp_path,
                v50_modules_available=False,
                extract_chain_link_fn=lambda *_args, **_kwargs: {},
            )

        assert result is True
        assert captured["martial_arts"] == ["Storm Palm", "Cloud Step"]

        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        assert saved_state_log["actual_truth"]["martial_arts"] == ["Storm Palm", "Cloud Step"]

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["martial_arts"] == ["Storm Palm", "Cloud Step"]

    def test_normalize_reader_facing_manuscript_strips_scene_headers_and_brackets(self):
        manuscript = (
            "### 씬 1: 2024년의 끝, 2006년의 시작\n\n"
            "[2024년 12월, 서울 외곽의 좁은 원룸]\n\n"
            "첫 문장이다.\n\n"
            "### 씬 2: 귀환\n\n"
            "[2006년 1월, 한성그룹 본가 시우의 방]\n\n"
            "둘째 문장이다."
        )

        normalized = Stage4PostProcessor._normalize_reader_facing_manuscript(manuscript)

        assert "### 씬" not in normalized
        assert "[2024년 12월, 서울 외곽의 좁은 원룸]" not in normalized
        assert "[2006년 1월, 한성그룹 본가 시우의 방]" not in normalized
        assert "2024년 12월, 서울 외곽의 좁은 원룸." in normalized
        assert "2006년 1월, 한성그룹 본가 시우의 방." in normalized
        assert "***" in normalized

    def test_process_pass_result_persists_normalized_reader_facing_manuscript(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        manuscript = (
            "### 씬 1: 시작\n\n"
            "[2024년 12월, 서울 외곽의 좁은 원룸]\n\n"
            "첫 문장이다.\n\n"
            "### 씬 2: 전환\n\n"
            "[2006년 1월, 한성그룹 본가 시우의 방]\n\n"
            "둘째 문장이다."
        )

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript=manuscript,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        saved_content = pp.ctx.current_project.db.save_manuscript.call_args.kwargs["content"]
        assert "### 씬" not in saved_content
        assert "[2024년 12월, 서울 외곽의 좁은 원룸]" not in saved_content
        assert "2024년 12월, 서울 외곽의 좁은 원룸." in saved_content
        file_text = (tmp_path / "ep_0001.txt").read_text(encoding="utf-8")
        assert "### 씬" not in file_text
        assert "***" in file_text

    def test_process_pass_result_re_normalizes_stringified_stv_martial_arts_correction(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "actual_truth": {
                    "martial_arts": [{"name": "Storm Palm"}],
                }
            },
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 0}

        captured = {}

        def _threshold_side_effect(key, default=None):
            if key == "feature_flags.enable_state_text_verifier":
                return True
            return default

        def _verify_side_effect(_self, manuscript, actual_truth):
            captured["before_correction"] = actual_truth.get("martial_arts")
            return {
                "verified": False,
                "mismatches": [
                    {
                        "field": "martial_arts",
                        "extracted": ["Storm Palm"],
                        "evidence": "No technique was actually learned here.",
                        "corrected": "[]",
                    }
                ],
                "corrections": {"martial_arts": "[]"},
                "blocking": False,
            }

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect),
            patch(
                "modules.core.state_text_verifier.StateTextVerifier.verify",
                autospec=True,
                side_effect=_verify_side_effect,
            ),
        ):
            result = pp.process_pass_result(
                next_ep=6,
                final_manuscript="The manuscript explicitly says the protagonist has not learned any technique yet. " * 90,
                final_title="test title",
                final_state_updates={},
                blueprint={"scene_breakdown": []},
                arc_data={"arc_no": 1},
                output_dir=tmp_path,
                v50_modules_available=False,
                extract_chain_link_fn=lambda *_args, **_kwargs: {},
            )

        assert result is True
        assert captured["before_correction"] == ["Storm Palm"]

        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        assert saved_state_log["actual_truth"]["martial_arts"] == []

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["martial_arts"] == []

    def test_process_pass_result_treats_stv_none_marker_for_martial_arts_as_empty_list(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "actual_truth": {
                    "martial_arts": [{"name": "Storm Palm"}],
                }
            },
            "causal_links": [],
        }

        pp.ctx.world_state = MagicMock()
        pp.ctx.world_state._state = {}
        pp.ctx.fact_ledger = MagicMock()
        pp.ctx.fact_ledger._ledger = {}
        pp.ctx.fact_ledger.get_stats.return_value = {"characters": 0, "items": 0}

        def _threshold_side_effect(key, default=None):
            if key == "feature_flags.enable_state_text_verifier":
                return True
            return default

        def _verify_side_effect(_self, manuscript, actual_truth):
            return {
                "verified": False,
                "mismatches": [
                    {
                        "field": "martial_arts",
                        "extracted": ["Storm Palm"],
                        "evidence": "The manuscript explicitly says no martial art was learned.",
                        "corrected": "없음",
                    }
                ],
                "corrections": {"martial_arts": "없음"},
                "blocking": False,
            }

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect),
            patch(
                "modules.core.state_text_verifier.StateTextVerifier.verify",
                autospec=True,
                side_effect=_verify_side_effect,
            ),
        ):
            result = pp.process_pass_result(
                next_ep=7,
                final_manuscript="The manuscript explicitly says no martial art was learned here. " * 90,
                final_title="test title",
                final_state_updates={},
                blueprint={"scene_breakdown": []},
                arc_data={"arc_no": 1},
                output_dir=tmp_path,
                v50_modules_available=False,
                extract_chain_link_fn=lambda *_args, **_kwargs: {},
            )

        assert result is True

        saved_state_log = pp.ctx.current_project.db.save_state_log_with_summary.call_args.args[1]
        assert saved_state_log["actual_truth"]["martial_arts"] == []

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["martial_arts"] == []


class TestRunPostEpisodeTasks:
    def test_vector_sync_called_when_operational(self, tmp_path):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = True
        ctx.current_project = MagicMock()
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.drafts = tmp_path
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()

        ctx.memory.sync_v20_drafts.assert_called_once_with(drafts_path=tmp_path)

    def test_skip_pause_bypasses_menu_return_input(self, tmp_path):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = True
        ctx.current_project = MagicMock()
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.drafts = Path(tmp_path)
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", side_effect=AssertionError("input should be skipped")) as mocked_input:
            pp.run_post_episode_tasks(skip_pause=True)

        mocked_input.assert_not_called()
        ctx.memory.sync_v20_drafts.assert_called_once_with(drafts_path=tmp_path)

    def test_vector_sync_skipped_when_not_operational(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = False
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()

        ctx.memory.sync_v20_drafts.assert_not_called()

    def test_vector_sync_skipped_when_drafts_path_missing(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = True
        ctx.current_project = MagicMock()
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.drafts = None
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()

        ctx.memory.sync_v20_drafts.assert_not_called()

    def test_no_memory_safe(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = None
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()


class TestStateTruthOwnerContract:
    def test_marks_director_fallback_when_manager_truth_missing(self):
        contract = _build_state_truth_owner_contract(
            actual_truth={},
            final_state_updates={"location": "archive", "_director_quality_labels": {"score": 95}},
            curr_inventory_counts={},
            inventory_count_deltas=[],
            relationship_changes=[],
            active_pressure_vectors=[],
            arc_data={},
        )

        assert contract["actual_truth_primary_owner"] == "director_state_updates_fallback"
        assert contract["actual_truth_fallback_used"] is True
        assert contract["actual_truth_fallback_reason"] == "manager_actual_truth_empty"
        assert contract["field_families"]["actual_truth_surface"]["fields"] == ["location"]
        assert contract["field_families"]["final_state_updates"]["owner"] == "director_state_updates"

    def test_marks_fact_ledger_carryover_numeric_authority_family(self):
        contract = _build_state_truth_owner_contract(
            actual_truth={"location": "archive"},
            final_state_updates={},
            curr_inventory_counts={},
            inventory_count_deltas=[],
            relationship_changes=[],
            active_pressure_vectors=[],
            arc_data={},
            fact_ledger_carryover_fields=["capital", "total_assets"],
        )

        assert contract["field_families"]["numeric_carryover_authority"] == {
            "owner": "fact_ledger_carryover_baseline",
            "surfaces": [
                "fact_ledger",
                "episode_bible.state_truth_owner_contract",
                "state_log.state_truth_owner_contract",
            ],
            "fields": ["capital", "total_assets"],
            "authority_scope": "carryover_baseline",
            "provenance": "fact_ledger_authority_scope",
        }

    def test_marks_promoted_numeric_carryover_refresh_sources(self):
        contract = _build_state_truth_owner_contract(
            actual_truth={"capital": "200억 원"},
            final_state_updates={"total_assets": 25_000_000_000},
            curr_inventory_counts={},
            inventory_count_deltas=[],
            relationship_changes=[],
            active_pressure_vectors=[],
            arc_data={},
            fact_ledger_carryover_fields=["capital", "total_assets"],
            numeric_carryover_refresh_plan={
                "promoted_fields": ["capital", "total_assets"],
                "promotion_sources": {
                    "capital": "actual_truth",
                    "total_assets": "director_state_updates_fallback",
                },
            },
        )

        assert contract["field_families"]["numeric_carryover_authority"]["promotion_rule"] == (
            "post_pass_structured_numeric_refresh_v1"
        )
        assert contract["field_families"]["numeric_carryover_authority"]["promoted_fields"] == [
            "capital",
            "total_assets",
        ]
        assert contract["field_families"]["numeric_carryover_authority"]["promotion_sources"] == {
            "capital": "actual_truth",
            "total_assets": "director_state_updates_fallback",
        }


class TestAtomicMetadataSave:
    """[TF-C10] WorldState + FactLedger 원자적 저장 테스트"""

    def _make_pp_with_metadata(self):
        """WorldState + FactLedger가 활성화된 PP 생성"""
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.sys.hud.bulk_update = MagicMock()

        director = MagicMock()
        director.on_approve_workflow.return_value = {}
        manager = MagicMock()
        manager.update_state_and_lore_v20.return_value = {}
        state_extractor = MagicMock()
        state_extractor.extract_satisfaction_tag.return_value = None

        ctx.agents = {
            "director": director,
            "manager": manager,
            "state_extractor": state_extractor,
        }

        db = MagicMock()
        db.conn = MagicMock()
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []
        # transaction() 컨텍스트 매니저 mock
        db.transaction.return_value.__enter__ = MagicMock(return_value=None)
        db.transaction.return_value.__exit__ = MagicMock(return_value=False)

        project = MagicMock()
        project.db = db
        project.name = "test_project"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {"KeyNPCs": []},
                "protagonist_config": {"name": "주인공"},
            },
            "npc_registry": {},
        }
        ctx.current_project = project

        # WorldState + FactLedger mock
        ws = MagicMock()
        ws._state = {"last_updated_ep": 0}
        ws.update_from_state_changes = MagicMock()
        ws.update_protagonist_state = MagicMock()
        ws.save = MagicMock()
        ws.rollback_to = MagicMock()
        ctx.world_state = ws

        fl = MagicMock()
        fl._ledger = {"last_updated_ep": 0}
        fl.update_from_state_changes = MagicMock()
        fl.update_from_bible_delta = MagicMock()
        fl.save = MagicMock()
        fl.rollback_to = MagicMock()
        fl.get_stats.return_value = {"characters": 5, "items": 3}
        ctx.fact_ledger = fl

        ctx.memory = None
        ctx.state_tracker = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "주인공"
        ctx.generate_narrative_summary = MagicMock()

        return Stage4PostProcessor(ctx)

    def test_transaction_wraps_both_saves(self, tmp_path):
        """[TF-C10] WorldState.save + FactLedger.save가 트랜잭션 안에서 호출"""
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db.save_manuscript.return_value = True

        pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1, "state_changes": {"power_level": 50}},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        # transaction() 호출 확인
        pp.ctx.current_project.db.transaction.assert_called_once()
        # 양쪽 save 호출 확인
        pp.ctx.world_state.save.assert_called_once()
        pp.ctx.fact_ledger.save.assert_called_once()

    def test_transaction_rollback_on_failure(self, tmp_path):
        """[TF-C10] FactLedger.save 실패 시 전체 트랜잭션 롤백 (비차단)"""
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.fact_ledger.save.side_effect = RuntimeError("DB write error")

        # 비차단 — 원고는 이미 저장됨, 전체 프로세스는 True 반환
        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1, "state_changes": {}},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True  # 원고 저장은 성공 → True
        pp.ctx.world_state.rollback_to.assert_not_called()

    def test_sequential_mode_rolls_back_persisted_world_state(self):
        """[TF-C10] transaction() 부재 시 부분 커밋된 WorldState를 rollback_to로 복구"""
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db = object()  # transaction() 미지원 경로
        pp.ctx.world_state.save.return_value = True
        pp.ctx.fact_ledger.save.side_effect = RuntimeError("DB write error")

        pp.post_pass_runtime._save_world_state_atomic(
            next_ep=3,
            actual_truth={},
            final_state_updates={"inventory_counts": {"gold": 1}},
            bible_delta={},
        )

        pp.ctx.world_state.rollback_to.assert_called_once_with(3)
        pp.ctx.fact_ledger.rollback_to.assert_not_called()
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("메타데이터 트랜잭션 없음: 순차 저장 복구 모드" in text for text in log_calls)
        assert any("WorldState 순차 저장 롤백 복구 완료" in text for text in log_calls)
        assert any("메타데이터 원자적 저장 실패" in text for text in log_calls)

    def test_build_atomic_state_payloads_merges_inventory_relationship_and_pressure(self):
        pp = self._make_pp_with_metadata()

        result = pp.post_pass_runtime._build_atomic_state_payloads(
            actual_truth={},
            final_state_updates={"hp": 10},
            bible_delta={
                "inventory_counts": {"gold": 3},
                "inventory_count_deltas": [{"name": "gold", "delta": 2}],
                "relationship_changes": [{"npc": "수호", "to": "경계"}],
                "state_changes": {"active_pressure_vectors": [{"text": "압박", "source": "ending_hook"}]},
            },
        )

        assert result["world_state_changes"]["hp"] == 10
        assert result["world_state_changes"]["inventory_counts"] == {"gold": 3}
        assert result["world_state_changes"]["relationship_changes"] == [{"npc": "수호", "to": "경계"}]
        assert result["world_state_changes"]["active_pressure_vectors"] == [{"text": "압박", "source": "ending_hook"}]
        assert "active_pressure_vectors" not in result["fact_ledger_changes"]
        assert result["fact_ledger_changes"]["inventory_count_deltas"] == [{"name": "gold", "delta": 2}]

    def test_build_atomic_state_payloads_keeps_npc_martial_state_world_only(self):
        pp = self._make_pp_with_metadata()

        result = pp.post_pass_runtime._build_atomic_state_payloads(
            actual_truth={},
            final_state_updates={"hp": 10},
            bible_delta={
                "state_changes": {
                    "npc_martial_state_changes": [
                        {
                            "name": "Chief Han",
                            "episode": 4,
                            "realm": "Peak",
                            "techniques_learned": ["Storm Palm"],
                        }
                    ]
                }
            },
        )

        assert result["world_state_changes"]["npc_martial_state_changes"] == [
            {
                "name": "Chief Han",
                "episode": 4,
                "realm": "Peak",
                "techniques_learned": ["Storm Palm"],
            }
        ]
        assert "npc_martial_state_changes" not in result["fact_ledger_changes"]

    def test_build_atomic_state_payloads_promotes_actual_truth_numeric_carryover_into_fact_ledger(self):
        pp = self._make_pp_with_metadata()
        pp.ctx.fact_ledger.get_numbers.return_value = {
            "capital": {
                "value": 10_000_000_000,
                "unit": "won",
                "last_ep": 5,
                "authority_scope": "carryover_baseline",
            },
            "total_assets": {
                "value": 12_000_000_000,
                "unit": "won",
                "last_ep": 5,
                "authority_scope": "carryover_baseline",
            },
            "bonus_pool": {
                "value": 300_000_000,
                "unit": "won",
                "last_ep": 5,
                "authority_scope": "scene_local",
            },
        }

        result = pp.post_pass_runtime._build_atomic_state_payloads(
            actual_truth={
                "capital": 20_000_000_000,
                "total_assets": 25_000_000_000,
                "bonus_pool": 900_000_000,
                "location": "vault",
            },
            final_state_updates={"hp": 10},
            bible_delta={},
        )

        assert result["world_state_changes"] == {"hp": 10}
        assert result["fact_ledger_changes"]["hp"] == 10
        assert result["fact_ledger_changes"]["capital"] == 20_000_000_000
        assert result["fact_ledger_changes"]["total_assets"] == 25_000_000_000
        assert "bonus_pool" not in result["fact_ledger_changes"]
        assert "location" not in result["fact_ledger_changes"]

    def test_build_atomic_state_payloads_promotes_string_and_director_fallback_numeric_carryover(self):
        pp = self._make_pp_with_metadata()
        pp.ctx.fact_ledger.get_numbers.return_value = {
            "capital": {
                "value": 10_000_000,
                "unit": "won",
                "last_ep": 1,
                "authority_scope": "carryover_baseline",
            },
            "total_assets": {
                "value": 20_000_000,
                "unit": "won",
                "last_ep": 1,
                "authority_scope": "carryover_baseline",
            },
        }

        result = pp.post_pass_runtime._build_atomic_state_payloads(
            actual_truth={
                "capital": "200억 원",
            },
            final_state_updates={
                "hp": 10,
                "total_assets": "250억 원",
            },
            bible_delta={},
        )

        assert result["world_state_changes"] == {"hp": 10, "total_assets": "250억 원"}
        assert result["fact_ledger_changes"]["hp"] == 10
        assert result["fact_ledger_changes"]["capital"] == "200억 원"
        assert result["fact_ledger_changes"]["total_assets"] == "250억 원"

    def test_process_pass_result_bridges_arc_npc_martial_state_changes_into_world_state_only(self, tmp_path):
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.current_project.latest_state = {}
        pp.ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {
                "actual_truth": {
                    "location": "gate",
                }
            },
            "causal_links": [],
        }

        result = pp.process_pass_result(
            next_ep=4,
            final_manuscript="arc-bridged npc martial state test " * 120,
            final_title="test",
            final_state_updates={"hp": 10},
            blueprint={"scene_breakdown": []},
            arc_data={
                "arc_no": 1,
                "state_changes": {
                    "npc_martial_state_changes": [
                        {
                            "name": "Chief Han",
                            "episode": 4,
                            "realm": "Peak",
                            "techniques_learned": ["Storm Palm"],
                        }
                    ]
                },
            },
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True

        saved_bible = pp.ctx.current_project.db.save_episode_bible.call_args.args[1]
        assert saved_bible["state_changes"]["location"] == "gate"
        assert saved_bible["state_changes"]["npc_martial_state_changes"] == [
            {
                "name": "Chief Han",
                "episode": 4,
                "realm": "Peak",
                "techniques_learned": ["Storm Palm"],
            }
        ]

        world_state_changes = pp.ctx.world_state.update_from_state_changes.call_args.args[1]
        assert world_state_changes["hp"] == 10
        assert world_state_changes["npc_martial_state_changes"] == [
            {
                "name": "Chief Han",
                "episode": 4,
                "realm": "Peak",
                "techniques_learned": ["Storm Palm"],
            }
        ]

        fact_ledger_changes = pp.ctx.fact_ledger.update_from_state_changes.call_args.args[1]
        assert fact_ledger_changes["hp"] == 10
        assert "npc_martial_state_changes" not in fact_ledger_changes

    def test_persist_atomic_world_state_updates_and_logs(self):
        pp = self._make_pp_with_metadata()

        result = pp.post_pass_runtime._persist_atomic_world_state(
            next_ep=4,
            world_state_changes={"hp": 20, "inventory_counts": {"gold": 2}},
        )

        assert result is True
        pp.ctx.world_state.update_from_state_changes.assert_called_once_with(
            4,
            {"hp": 20, "inventory_counts": {"gold": 2}},
        )
        pp.ctx.world_state.update_protagonist_state.assert_called_once()
        pp.ctx.world_state.save.assert_called_once()

    def test_persist_atomic_fact_ledger_updates_delta_and_logs(self):
        pp = self._make_pp_with_metadata()

        result = pp.post_pass_runtime._persist_atomic_fact_ledger(
            next_ep=5,
            fact_ledger_changes={"relationship_changes": [{"npc": "수호", "to": "경계"}]},
            bible_delta={"relationship_changes": [{"npc": "수호", "to": "경계"}]},
        )

        assert result is True
        pp.ctx.fact_ledger.update_from_state_changes.assert_called_once_with(
            5,
            {"relationship_changes": [{"npc": "수호", "to": "경계"}]},
        )
        pp.ctx.fact_ledger.update_from_bible_delta.assert_called_once_with(
            5,
            {"relationship_changes": [{"npc": "수호", "to": "경계"}]},
        )
        pp.ctx.fact_ledger.save.assert_called_once()

    def test_process_pass_result_delegates_world_state_settlement_to_runtime(self, tmp_path):
        pp = self._make_pp_with_metadata()
        pp.post_pass_runtime._submit_manager_async = MagicMock(
            return_value={
                "bible_future": None,
                "current_state": {},
                "lore_list": [],
                "active_seeds": [],
                "causal_history": "",
            }
        )
        pp.post_pass_runtime._memorize_and_validate = MagicMock()
        pp.post_pass_runtime._collect_manager_and_build_delta = MagicMock(
            return_value={
                "bible_delta": {"relationship_changes": []},
                "actual_truth": {},
                "state_truth_owner_contract": {"field_families": {"numeric_carryover_authority": {"fields": ["capital"]}}},
                "meta_save_failed": False,
            }
        )
        pp.post_pass_runtime._save_world_state_atomic = MagicMock()
        pp.post_pass_runtime._run_post_pass_advisories = MagicMock()

        result = pp.process_pass_result(
            next_ep=7,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={"inventory_counts": {"gold": 2}},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1, "state_changes": {}},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        pp.post_pass_runtime._save_world_state_atomic.assert_called_once_with(
            next_ep=7,
            actual_truth={},
            final_state_updates={"inventory_counts": {"gold": 2}},
            bible_delta={"relationship_changes": []},
        )

    def test_world_state_save_false_surfaces_last_save_error(self, tmp_path):
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.world_state.save.return_value = False
        pp.ctx.world_state.last_save_error = "world write fail"

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1, "state_changes": {}},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("WorldState save 실패: world write fail" in text for text in log_calls)
        assert any("메타데이터 원자적 저장 실패" in text for text in log_calls)

    def test_fact_ledger_save_false_surfaces_last_save_error(self, tmp_path):
        pp = self._make_pp_with_metadata()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.fact_ledger.save.return_value = False
        pp.ctx.fact_ledger.last_save_error = "ledger write fail"

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1, "state_changes": {}},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        log_calls = [str(call.args[0]) for call in pp.ctx.ui.log.call_args_list if call.args]
        assert any("FactLedger save 실패: ledger write fail" in text for text in log_calls)
        assert any("메타데이터 원자적 저장 실패" in text for text in log_calls)


class TestCapitalReconciliation:
    """[V73] 확정 원고 기준 자본금 역동기화 테스트"""

    def test_extract_capital_basic(self):
        assert Stage4PostProcessor._extract_capital_from_manuscript("잔고 131억 원") == 131.0

    def test_extract_capital_with_comma(self):
        assert Stage4PostProcessor._extract_capital_from_manuscript("자본금 1,200억") == 1200.0

    def test_extract_capital_man_unit(self):
        result = Stage4PostProcessor._extract_capital_from_manuscript("예수금 5000만 원")
        assert result is not None
        assert abs(result - 0.5) < 0.01  # 5000만 = 0.5억

    def test_extract_capital_reverse_pattern(self):
        assert Stage4PostProcessor._extract_capital_from_manuscript("80억의 자본") == 80.0

    def test_extract_capital_returns_last(self):
        text = "잔고 80억이었으나 실탄 57억으로 줄었다"
        result = Stage4PostProcessor._extract_capital_from_manuscript(text)
        assert result == 57.0

    def test_extract_capital_cross_pattern_position_order(self):
        """[감리P0] 패턴1+2 교차 시 문서 뒤쪽 값 반환"""
        text = "80억의 실탄을 모아 자본금 56억만 남았다"
        result = Stage4PostProcessor._extract_capital_from_manuscript(text)
        assert result == 56.0  # 문서 뒤쪽 "자본금 56억"이 정답

    def test_extract_capital_decimal(self):
        """[재감리P2] 소수점 자본금 '1.5억' 정확 추출"""
        assert Stage4PostProcessor._extract_capital_from_manuscript("자본금 1.5억") == 1.5

    def test_extract_capital_none_when_no_match(self):
        assert Stage4PostProcessor._extract_capital_from_manuscript("검을 뽑았다") is None

    def test_reconcile_advisory_only_on_mismatch(self):
        """[V73-B] 불일치 시 HUD 수정 없이 advisory 경고만 출력"""
        from modules.core.genre_hud_manager import FinanceHUDManager

        ctx = MagicMock()
        ctx.ui = MagicMock()
        hud = MagicMock(spec=FinanceHUDManager)
        hud.pro_data = {"capital": "80억 원"}
        hud.update_physical_status = MagicMock()
        ctx.sys.hud = hud

        pp = Stage4PostProcessor(ctx)
        pp._reconcile_capital("잔고 57억 원의 실탄이 남았다", ep_num=11)

        # [V73-B] HUD 수정 안 함 — Director state_updates에 위임
        hud.update_physical_status.assert_not_called()
        # advisory 메시지는 출력
        ctx.ui.log.assert_called()

    def test_reconcile_skips_when_within_threshold(self):
        from modules.core.genre_hud_manager import FinanceHUDManager

        ctx = MagicMock()
        ctx.ui = MagicMock()
        hud = MagicMock(spec=FinanceHUDManager)
        hud.pro_data = {"capital": "80억 원"}
        ctx.sys.hud = hud

        pp = Stage4PostProcessor(ctx)
        pp._reconcile_capital("잔고 82억 원", ep_num=5)

        hud.update_physical_status.assert_not_called()

    def test_reconcile_skips_when_no_financial_mention(self):
        from modules.core.genre_hud_manager import FinanceHUDManager

        ctx = MagicMock()
        ctx.ui = MagicMock()
        hud = MagicMock(spec=FinanceHUDManager)
        hud.pro_data = {"capital": "80억 원"}
        ctx.sys.hud = hud

        pp = Stage4PostProcessor(ctx)
        pp._reconcile_capital("무림맹주가 검을 뽑았다", ep_num=5)

        hud.update_physical_status.assert_not_called()

    def test_reconcile_skips_for_non_finance_genre(self):
        """[감리P1] 비투자물 장르에서는 실행 안 함"""
        ctx = MagicMock()
        ctx.ui = MagicMock()
        hud = MagicMock()  # not FinanceHUDManager
        hud.pro_data = {"wealth": "은자 100냥"}
        ctx.sys.hud = hud

        pp = Stage4PostProcessor(ctx)
        pp._reconcile_capital("잔고 80억 원의 현금을 보유", ep_num=5)

        hud.update_physical_status.assert_not_called()

    def test_reconcile_exception_does_not_crash_process(self, tmp_path):
        """[재감리P1] reconcile 예외가 process_pass_result를 중단시키지 않음"""
        from modules.core.genre_hud_manager import FinanceHUDManager

        ctx = MagicMock()
        ctx.ui = MagicMock()
        hud = MagicMock(spec=FinanceHUDManager)
        hud.pro_data = {"capital": "80억 원"}
        hud.update_physical_status.side_effect = RuntimeError("bible save failed")
        ctx.sys.hud = hud

        director = MagicMock()
        director.on_approve_workflow.return_value = {}
        manager = MagicMock()
        manager.update_state_and_lore_v20.return_value = {}
        state_ext = MagicMock()
        state_ext.extract_satisfaction_tag.return_value = None
        ctx.agents = {"director": director, "manager": manager, "state_extractor": state_ext}

        db = MagicMock()
        db.conn = MagicMock()
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []
        db.save_manuscript.return_value = True

        project = MagicMock()
        project.db = db
        project.name = "test"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {"AssetLibrary": {"KeyNPCs": []}, "protagonist_config": {"name": "mc"}},
            "npc_registry": {},
        }
        ctx.current_project = project
        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "mc"
        ctx.generate_narrative_summary = MagicMock()

        pp = Stage4PostProcessor(ctx)
        result = pp.process_pass_result(
            next_ep=11,
            final_manuscript="가" * 400 + "잔고 57억 원의 실탄",
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True  # reconcile 실패해도 전체 프로세스는 성공


class TestModuleStructure:
    def test_import(self):
        assert Stage4PostProcessor is not None

    def test_orchestrator_has_post_processor_property(self):
        assert hasattr(Stage4Orchestrator, "post_processor")

    def test_orchestrator_no_legacy_post_methods(self):
        assert not hasattr(Stage4Orchestrator, "_process_pass_result")
        assert not hasattr(Stage4Orchestrator, "_run_post_episode_tasks")


class TestSoftFailureLogging:
    def test_quality_signal_save_failure_is_logged_as_soft_failure(self, tmp_path):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.agents = {"director": MagicMock()}
        ctx.agents["director"].on_approve_workflow.return_value = {}
        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "주인공"
        ctx.generate_narrative_summary = MagicMock()
        ctx.audit_event = MagicMock()

        db = MagicMock()
        db.conn = MagicMock()
        db.save_episode_quality_signal.side_effect = RuntimeError("signal table busy")
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []

        project = MagicMock()
        project.db = db
        project.name = "demo"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {"AssetLibrary": {"KeyNPCs": []}, "protagonist_config": {"name": "주인공"}},
            "npc_registry": {},
        }
        project.paths = type("Paths", (), {"root": tmp_path})()
        ctx.current_project = project

        pp = Stage4PostProcessor(ctx)
        result = pp.process_pass_result(
            next_ep=2,
            final_manuscript="그야말로 숨을 삼켰다. " * 120,
            final_title="테스트",
            final_state_updates={"_director_quality_labels": {"score": 92, "verdict": "PASS"}},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        soft_failures = tmp_path / "logs" / "soft_failures.jsonl"
        assert soft_failures.exists()
        rows = [json.loads(line) for line in soft_failures.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(row["operation"] == "save_episode_quality_signal" for row in rows)

    def test_karma_status_save_failure_is_logged_as_soft_failure(self, tmp_path):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.agents = {
            "director": MagicMock(),
            "manager": MagicMock(),
            "state_extractor": MagicMock(),
        }
        ctx.agents["director"].on_approve_workflow.return_value = {}
        ctx.agents["manager"].update_state_and_lore_v20.return_value = {
            "new_lore": {},
            "knowledge_map_updates": {},
            "recovered_seeds": [],
            "state_updates": {"karma_matrix": [{"target": "npc_a", "value": 14, "obsession": 9}]},
            "causal_links": [],
        }
        ctx.agents["state_extractor"].extract_satisfaction_tag.return_value = None
        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "mc"
        ctx.generate_narrative_summary = MagicMock()
        ctx.audit_event = MagicMock()

        db = MagicMock()
        db.conn = MagicMock()
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []
        db.save_manuscript.return_value = True
        db.update_karma.side_effect = RuntimeError("karma table busy")

        project = MagicMock()
        project.db = db
        project.name = "demo"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {"AssetLibrary": {"KeyNPCs": []}, "protagonist_config": {"name": "mc"}},
            "npc_registry": {},
        }
        project.paths = type("Paths", (), {"root": tmp_path})()
        ctx.current_project = project

        pp = Stage4PostProcessor(ctx)
        result = pp.process_pass_result(
            next_ep=2,
            final_manuscript="karma soft failure " * 120,
            final_title="test",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is True
        soft_failures = tmp_path / "logs" / "soft_failures.jsonl"
        assert soft_failures.exists()
        rows = [json.loads(line) for line in soft_failures.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(row["operation"] == "update_karma" for row in rows)
        assert any(row["extra"].get("table") == "karma_status" for row in rows if isinstance(row.get("extra"), dict))

    def test_report_soft_failure_ignores_magicmock_root_without_db_path(self, tmp_path):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.agents = {"director": MagicMock()}
        ctx.agents["director"].on_approve_workflow.return_value = {}
        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "주인공"
        ctx.generate_narrative_summary = MagicMock()
        ctx.audit_event = MagicMock()

        project = MagicMock()
        project.paths.root = MagicMock()
        project.db = MagicMock()
        project.db.db_path = None
        ctx.current_project = project

        pp = Stage4PostProcessor(ctx)

        assert pp._resolve_project_log_dir() is None
        pp._report_soft_failure(operation="mock_root", message="should not persist", exc=RuntimeError("boom"))
        assert not (tmp_path / "logs" / "soft_failures.jsonl").exists()
