"""[B-1-1] Stage4PostProcessor unit tests."""

from unittest.mock import MagicMock, patch

from modules.core.stage4_orchestrator import Stage4Orchestrator
from modules.core.stage4_post_processor import Stage4PostProcessor


class TestPostProcessorInit:
    def test_init_with_ctx(self):
        ctx = MagicMock()
        pp = Stage4PostProcessor(ctx)
        assert pp.ctx is ctx

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

        result = pp.process_pass_result(
            next_ep=1,
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

    def test_returns_false_on_db_failure(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.side_effect = RuntimeError("DB error")

        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        assert result is False

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

    def test_chain_link_fn_called(self, tmp_path):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        mock_fn = MagicMock(return_value={"cliffhanger": "test"})

        pp.process_pass_result(
            next_ep=5,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=mock_fn,
        )

        mock_fn.assert_called_once_with(5, "테스트 원고 " * 500, {"scene_breakdown": []})

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

            def shutdown(self, wait=False):
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


class TestRunPostEpisodeTasks:
    def test_vector_sync_called_when_operational(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = True
        pp = Stage4PostProcessor(ctx)

        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()

        ctx.memory.sync_v20_drafts.assert_called_once()

    def test_vector_sync_skipped_when_not_operational(self):
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = False
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
        ws.update_from_state_changes = MagicMock()
        ws.update_protagonist_state = MagicMock()
        ws.save = MagicMock()
        ctx.world_state = ws

        fl = MagicMock()
        fl.update_from_state_changes = MagicMock()
        fl.update_from_bible_delta = MagicMock()
        fl.save = MagicMock()
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


class TestModuleStructure:
    def test_import(self):
        assert Stage4PostProcessor is not None

    def test_orchestrator_has_post_processor_property(self):
        assert hasattr(Stage4Orchestrator, "post_processor")

    def test_orchestrator_no_legacy_post_methods(self):
        assert not hasattr(Stage4Orchestrator, "_process_pass_result")
        assert not hasattr(Stage4Orchestrator, "_run_post_episode_tasks")
