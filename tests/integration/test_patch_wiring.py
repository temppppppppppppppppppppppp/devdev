"""Integration wiring verification — TF-7R DI chain signal-flow tests.

These tests verify that TF-7R patches are correctly wired through DI contexts
in the actual pipeline.  Each test exercises the DI *chain* (orchestrator →
receiver) rather than component logic in isolation.

NO real DB connections, NO real files, NO LLM calls.  Every I/O boundary is
mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Test 1 — Stage4PostProcessor calls emotion_tracker after PASS
# ---------------------------------------------------------------------------


class TestEmotionTrackerCalledOnPass:
    """Verify Stage4PostProcessor.process_pass_result() calls emotion_tracker
    add_episode_emotion() and save_to_db() when v50_modules_available=True and
    ctx.emotion_tracker is set (TF7-P2-06 wiring, lines ~291-298 of
    stage4_post_processor.py)."""

    def _make_ctx(self, emotion_tracker_mock):
        """Build a minimal Stage4Context-like mock wired with a real emotion_tracker."""
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.emotion_tracker = emotion_tracker_mock

        # DB mock — save_manuscript / update_martial_tracker succeed, commit OK
        db = MagicMock()
        db.conn = MagicMock()
        db.conn.commit = MagicMock()
        db.conn.rollback = MagicMock()
        db.save_manuscript = MagicMock()
        db.update_martial_tracker = MagicMock()
        db.load_anchor = MagicMock(return_value=None)
        db.save_episode_bible = MagicMock()
        db.save_state_log_with_summary = MagicMock()
        db.save_cost_record = MagicMock()
        db.find_repeated_sentence_hashes = MagicMock(return_value=[])
        db.store_sentence_hashes = MagicMock()

        project = MagicMock()
        project.db = db
        project.name = "test_project"
        project.master_bible = {}
        project.latest_state = {}

        ctx.current_project = project

        # agents
        manager = MagicMock()
        manager.update_state_and_lore_v20.return_value = {}
        director = MagicMock()
        director.on_approve_workflow.return_value = {}
        state_extractor = MagicMock()
        state_extractor.extract_satisfaction_tag.return_value = None
        ctx.agents = {
            "manager": manager,
            "director": director,
            "state_extractor": state_extractor,
        }

        # sys / hud
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}

        # optional modules
        ctx.memory = None
        ctx.failure_learner = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.quality_dashboard = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.pacing_analyzer = None
        ctx.get_protagonist_name = None

        # callbacks
        ctx.generate_narrative_summary = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.perf_timer = MagicMock()

        return ctx

    def test_emotion_tracker_add_episode_emotion_called(self, tmp_path):
        """add_episode_emotion(ep_num, ...) is called during a PASS run."""
        from modules.core.stage4_post_processor import Stage4PostProcessor

        emotion_mock = MagicMock()
        ctx = self._make_ctx(emotion_mock)

        pp = Stage4PostProcessor(ctx)

        output_dir = tmp_path

        with (
            patch("modules.core.stage4_post_processor.get_metrics_collector", return_value=None),
            patch("modules.core.stage4_post_processor.os.makedirs"),
        ):
            pp.process_pass_result(
                next_ep=5,
                final_manuscript="원고 내용 " * 50,
                final_title="테스트 제목",
                final_state_updates={},
                blueprint={},
                arc_data={"arc_no": 1},
                output_dir=output_dir,
                v50_modules_available=True,
            )

        emotion_mock.add_episode_emotion.assert_called_once_with(5, "neutral", 0.5)

    def test_emotion_tracker_save_to_db_called(self, tmp_path):
        """save_to_db(db) is called with the project DB after add_episode_emotion."""
        from modules.core.stage4_post_processor import Stage4PostProcessor

        emotion_mock = MagicMock()
        ctx = self._make_ctx(emotion_mock)

        pp = Stage4PostProcessor(ctx)
        output_dir = tmp_path

        with (
            patch("modules.core.stage4_post_processor.get_metrics_collector", return_value=None),
            patch("modules.core.stage4_post_processor.os.makedirs"),
        ):
            pp.process_pass_result(
                next_ep=7,
                final_manuscript="원고 내용 " * 50,
                final_title="테스트 제목",
                final_state_updates={},
                blueprint={},
                arc_data={"arc_no": 2},
                output_dir=output_dir,
                v50_modules_available=True,
            )

        emotion_mock.save_to_db.assert_called_once_with(ctx.current_project.db)


# ---------------------------------------------------------------------------
# Test 2 — Stage3Orchestrator._handle_success records stage=3 PASS
# ---------------------------------------------------------------------------


class TestStage3HandleSuccessQualityDashboard:
    """Verify _handle_success() calls quality_dashboard.record_validation
    with stage=3 and decision="PASS" (P6-02 wiring, lines ~620-636 of
    stage3_orchestrator.py)."""

    def _make_orchestrator(self, quality_dashboard_mock):
        from modules.core.stage3_orchestrator import Stage3Orchestrator

        app = MagicMock()
        app.quality_dashboard = quality_dashboard_mock

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.validate_blueprint_integrity = MagicMock(return_value=True)
        ctx.safe_commit = MagicMock(return_value=True)
        ctx.audit_event = MagicMock()
        ctx.current_project = MagicMock()
        ctx.current_project.save_episode_blueprint = MagicMock()

        orch = Stage3Orchestrator(app, context=ctx)
        return orch

    def test_record_validation_called_with_pass(self):
        qd = MagicMock()
        orch = self._make_orchestrator(qd)

        pipeline_result = {
            "final_verdict": "PASS",
            "last_score": 85,
            "phases": {"generate": {"selected_score": 85, "selected_strategy": "ensemble"}},
        }
        prev_blueprints: list = []
        blueprint = {"ep_num": 1, "title": "테스트"}

        orch._handle_success(
            working_ep=1,
            arc_no=1,
            arc_data={},
            blueprint=blueprint,
            pipeline_result=pipeline_result,
            prev_blueprints=prev_blueprints,
            success_count=0,
            fail_count=0,
        )

        qd.record_validation.assert_called_once()
        call_kwargs = qd.record_validation.call_args
        assert call_kwargs.kwargs.get("stage") == 3 or (len(call_kwargs.args) >= 3 and call_kwargs.args[2] == 3)
        result_arg = call_kwargs.kwargs.get("result") or call_kwargs.args[1]
        assert result_arg["decision"] == "PASS"

    def test_record_validation_ep_num_correct(self):
        qd = MagicMock()
        orch = self._make_orchestrator(qd)

        pipeline_result = {"final_verdict": "PASS", "last_score": 75}
        orch._handle_success(
            working_ep=42,
            arc_no=3,
            arc_data={},
            blueprint={"ep_num": 42},
            pipeline_result=pipeline_result,
            prev_blueprints=[],
            success_count=5,
            fail_count=0,
        )

        call_kwargs = qd.record_validation.call_args
        ep_arg = call_kwargs.kwargs.get("ep_num") or call_kwargs.args[0]
        assert ep_arg == 42


# ---------------------------------------------------------------------------
# Test 3 — Stage3Orchestrator._handle_failure records stage=3 REJECT
# ---------------------------------------------------------------------------


class TestStage3HandleFailureQualityDashboard:
    """Verify _handle_failure() calls quality_dashboard.record_validation
    with stage=3 and decision="REJECT" (P6-02 wiring, lines ~678-693 of
    stage3_orchestrator.py)."""

    def _make_orchestrator(self, quality_dashboard_mock):
        from modules.core.stage3_orchestrator import Stage3Orchestrator

        app = MagicMock()
        app.quality_dashboard = quality_dashboard_mock

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.audit_event = MagicMock()
        ctx.current_project = MagicMock()
        ctx.current_project.db = MagicMock()
        ctx.current_project.db.save_cost_record = MagicMock()

        orch = Stage3Orchestrator(app, context=ctx)
        return orch

    def test_record_validation_called_with_reject(self):
        qd = MagicMock()
        orch = self._make_orchestrator(qd)

        pipeline_result = {
            "final_verdict": "FAIL",
            "last_score": 30,
            "quality_gate_failed": False,
        }
        orch._handle_failure(
            working_ep=5,
            pipeline_result=pipeline_result,
            success_count=3,
            fail_count=0,
        )

        qd.record_validation.assert_called_once()
        call_kwargs = qd.record_validation.call_args
        assert call_kwargs.kwargs.get("stage") == 3 or (len(call_kwargs.args) >= 3 and call_kwargs.args[2] == 3)
        result_arg = call_kwargs.kwargs.get("result") or call_kwargs.args[1]
        assert result_arg["decision"] == "REJECT"

    def test_handle_failure_returns_break_true(self):
        qd = MagicMock()
        orch = self._make_orchestrator(qd)

        result = orch._handle_failure(
            working_ep=3,
            pipeline_result={"final_verdict": "FAIL", "last_score": 0},
            success_count=0,
            fail_count=0,
        )
        assert result.get("break") is True


# ---------------------------------------------------------------------------
# Test 4 — ValidationOrchestrator BLOCKING fail → FailureLearner.record_failure(stage=4)
# ---------------------------------------------------------------------------


class TestValidationOrchestratorFailureLearnerWiring:
    """Verify that when ValidationOrchestrator runs TIER1 BLOCKING and fails,
    _failure_learner.record_failure(stage=4, ...) is called (P6-01 wiring,
    lines ~362-373 of validation_orchestrator.py)."""

    def _make_orchestrator(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_threshold": 70,
            "use_self_consistency": False,
            "use_retrospective": False,
            "use_reflexion": False,
            "use_pre_llm": False,
            "use_adaptive_threshold": False,
        }
        # No client needed — we mock everything
        orch = ValidationOrchestrator(config=config, client=None, genre="wuxia")
        return orch

    def test_failure_learner_record_failure_called_on_blocking_fail(self):
        orch = self._make_orchestrator()

        failure_learner = MagicMock()
        validation_context = {
            "_failure_learner": failure_learner,
            "ep_num": 10,
        }

        # Mock the blocking validator to fail
        orch.blocking = MagicMock()
        orch.blocking.validate.return_value = {
            "passed": False,
            "failure_count": 1,
            "failures": [
                {
                    "type": "DECEASED_NPC_ACTIVE",
                    "reason": "사망한 NPC가 행동함",
                    "description": "사망한 NPC가 행동함",
                }
            ],
        }

        # Also mock continuity to pass (so we reach BLOCKING)
        orch.continuity = MagicMock()
        orch.continuity.validate.return_value = {
            "passed": True,
            "violations": [],
            "warning_count": 0,
        }

        # Mock pre-LLM to pass
        orch.pre_llm = None
        orch.use_pre_llm = False

        result = orch.validate(
            ep_num=10,
            manuscript="테스트 원고 내용 " * 20,
            validation_context=validation_context,
        )

        assert result["final_decision"] == "REJECT"
        failure_learner.record_failure.assert_called()

        # At least one call must have stage=4
        stage4_calls = [c for c in failure_learner.record_failure.call_args_list if c.kwargs.get("stage") == 4]
        assert len(stage4_calls) >= 1, (
            f"Expected record_failure(stage=4, ...) but got: {failure_learner.record_failure.call_args_list}"
        )

    def test_failure_learner_not_called_when_not_in_context(self):
        """If _failure_learner is absent from validation_context, no AttributeError."""
        orch = self._make_orchestrator()

        orch.blocking = MagicMock()
        orch.blocking.validate.return_value = {
            "passed": False,
            "failure_count": 1,
            "failures": [{"type": "TEST", "reason": "test failure", "description": "test"}],
        }
        orch.continuity = MagicMock()
        orch.continuity.validate.return_value = {"passed": True, "violations": [], "warning_count": 0}
        orch.pre_llm = None
        orch.use_pre_llm = False

        # No _failure_learner key at all
        result = orch.validate(ep_num=1, manuscript="원고 내용 " * 10, validation_context={})
        assert result["final_decision"] == "REJECT"


# ---------------------------------------------------------------------------
# Test 5 — ProjectService.rollback_episode calls emotion_tracker.rollback_to
# ---------------------------------------------------------------------------


class TestProjectServiceEmotionTrackerRollback:
    """Verify rollback_episode() calls emotion_tracker_fn() and then
    emotion_tracker.rollback_to(target_ep) (TF-7-P0-01 wiring, lines ~257-261
    of project_service.py)."""

    def _make_service(self, emotion_tracker_mock, target_ep: int = 3):
        """Build a ProjectService with all DB/file/vector operations mocked."""
        from modules.core.services.project_service import ProjectService

        # Set up project mock
        project = MagicMock()
        project.get_latest_episode_number.return_value = target_ep + 1  # current = target + 1

        db = MagicMock()
        db.cursor = MagicMock()
        db.cursor.execute = MagicMock()
        db.cursor.fetchone.return_value = None  # no HUD state to restore
        db.conn = MagicMock()
        db.conn.commit = MagicMock()
        db.conn.rollback = MagicMock()
        db.delete_episode_bibles_after = MagicMock(return_value=0)
        project.db = db

        paths_mock = MagicMock()
        paths_mock.drafts = MagicMock()
        paths_mock.drafts.glob.return_value = []
        project.paths = paths_mock
        project._load_from_db = MagicMock()

        # emotion_tracker_fn returns emotion_tracker_mock
        emotion_tracker_fn = MagicMock(return_value=emotion_tracker_mock)

        service = ProjectService(
            project_fn=MagicMock(return_value=project),
            ui=MagicMock(),
            safe_commit_fn=MagicMock(return_value=True),
            genre_fn=MagicMock(return_value=None),
            memory_fn=MagicMock(return_value=None),
            state_tracker_invalidator=None,
            world_state_fn=None,
            fact_ledger_fn=None,
            preset_registry_restorer=None,
            emotion_tracker_fn=emotion_tracker_fn,
            state_delta_tracker_fn=None,
        )
        return service, project

    def test_emotion_tracker_fn_called(self):
        emotion_mock = MagicMock()
        service, _project = self._make_service(emotion_mock, target_ep=3)

        with patch("builtins.input", side_effect=["3", "y", ""]):
            service.rollback_episode()

        service._emotion_tracker_fn.assert_called()

    def test_emotion_tracker_rollback_to_called_with_target_ep(self):
        emotion_mock = MagicMock()
        emotion_mock.rollback_to = MagicMock()

        service, _project = self._make_service(emotion_mock, target_ep=3)

        with patch("builtins.input", side_effect=["3", "y", ""]):
            service.rollback_episode()

        emotion_mock.rollback_to.assert_called_once_with(3)


# ---------------------------------------------------------------------------
# Test 6 — ProjectService.rollback_episode calls state_delta_tracker.rollback_to
# ---------------------------------------------------------------------------


class TestProjectServiceStateDeltaTrackerRollback:
    """Verify rollback_episode() calls state_delta_tracker_fn() and then
    state_delta_tracker.rollback_to(target_ep) (TF-7-P0-01 wiring,
    lines ~262-265 of project_service.py)."""

    def _make_service(self, state_delta_tracker_mock, target_ep: int = 5):
        from modules.core.services.project_service import ProjectService

        project = MagicMock()
        project.get_latest_episode_number.return_value = target_ep + 1

        db = MagicMock()
        db.cursor = MagicMock()
        db.cursor.execute = MagicMock()
        db.cursor.fetchone.return_value = None
        db.conn = MagicMock()
        db.conn.commit = MagicMock()
        db.conn.rollback = MagicMock()
        db.delete_episode_bibles_after = MagicMock(return_value=0)
        project.db = db

        paths_mock = MagicMock()
        paths_mock.drafts = MagicMock()
        paths_mock.drafts.glob.return_value = []
        project.paths = paths_mock
        project._load_from_db = MagicMock()

        sdt_fn = MagicMock(return_value=state_delta_tracker_mock)

        service = ProjectService(
            project_fn=MagicMock(return_value=project),
            ui=MagicMock(),
            safe_commit_fn=MagicMock(return_value=True),
            genre_fn=MagicMock(return_value=None),
            memory_fn=MagicMock(return_value=None),
            state_tracker_invalidator=None,
            world_state_fn=None,
            fact_ledger_fn=None,
            preset_registry_restorer=None,
            emotion_tracker_fn=None,
            state_delta_tracker_fn=sdt_fn,
        )
        return service, project

    def test_state_delta_tracker_rollback_to_called(self):
        sdt_mock = MagicMock()
        sdt_mock.rollback_to = MagicMock()

        service, _project = self._make_service(sdt_mock, target_ep=5)

        with patch("builtins.input", side_effect=["5", "y", ""]):
            service.rollback_episode()

        sdt_mock.rollback_to.assert_called_once_with(5)

    def test_state_delta_tracker_fn_invoked(self):
        sdt_mock = MagicMock()
        service, _project = self._make_service(sdt_mock, target_ep=2)

        with patch("builtins.input", side_effect=["2", "y", ""]):
            service.rollback_episode()

        service._state_delta_tracker_fn.assert_called()


# ---------------------------------------------------------------------------
# Test 7 — Stage4InterviewRound builds _cv_context with protagonist_name
# ---------------------------------------------------------------------------


class TestInterviewRoundProtagonistNameWiring:
    """Verify that when Stage4InterviewRound builds _cv_context it injects
    protagonist_name from master_bible when found (P3-02 wiring,
    lines ~312-330 of stage4_interview_round.py)."""

    def _make_round_ctx(self, protagonist_name: str):
        """Build a minimal ctx with master_bible populated."""
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.perf_timer = MagicMock()

        ctx.current_project = MagicMock()
        ctx.current_project.master_bible = {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"protagonist": protagonist_name}},
            },
        }

        # state_tracker — no NPC registry
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.npc_registry = {}

        ctx.get_module = MagicMock(return_value=None)
        ctx.failure_learner = None

        return ctx

    def test_protagonist_name_injected_into_cv_context(self):
        """protagonist_name from master_bible appears in _cv_context."""
        from modules.core.stage4_interview_round import Stage4InterviewRound

        prot_name = "테스트주인공"
        ctx = self._make_round_ctx(prot_name)

        ir = Stage4InterviewRound(ctx)

        # We don't run full round — we exercise just the _cv_context-building
        # block that is executed inside run() after validation_results are made.
        # We inspect by calling the internal code path through a mock round_ctx.
        captured_cv_context: dict = {}

        original_consistency_validate = MagicMock(return_value={"violations": [], "score_penalty": 0})
        original_blocking_validate = MagicMock(return_value={"passed": True, "failures": []})

        round_ctx = MagicMock()
        round_ctx.chief_writer = MagicMock()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "원고 내용 " * 30, "strategy_name": "test"}
        ]
        round_ctx.manuscript_validator = MagicMock()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "metrics": {"length": 600}, "focus_points": []}
        ]
        round_ctx.consistency_validator = MagicMock()
        round_ctx.consistency_validator.validate.side_effect = lambda ms, cv: captured_cv_context.update(cv) or {
            "violations": [],
            "score_penalty": 0,
        }
        round_ctx.blocking_validator = MagicMock()
        round_ctx.blocking_validator.validate.return_value = {"passed": True, "failures": []}
        round_ctx.continuity_validator = MagicMock()
        round_ctx.continuity_validator.validate.return_value = {"passed": True, "violations": []}

        # Fill out all round_ctx attributes used in run()
        round_ctx.next_ep = 1
        round_ctx.blueprint = {}
        round_ctx.arc_data = {"arc_no": 1}
        round_ctx.arc_pos = 0
        round_ctx.total_ep_in_arc = 5
        round_ctx.arc_tactical = {}
        round_ctx.prev_text = ""
        round_ctx.prev_ending = ""
        round_ctx.prev_manuscripts_text = ""
        round_ctx.episode_digest = ""
        round_ctx.hud_report = ""
        round_ctx.current_inventory = []
        round_ctx.current_martial_arts = []
        round_ctx.dead_npcs = []
        round_ctx.item_acquisition_timeline = ""
        round_ctx.chain_link_section = ""
        round_ctx.world_state_summary = ""
        round_ctx.purism_prompt = ""
        round_ctx.genre_name = "wuxia"
        round_ctx.npc_equipment_summary = ""
        round_ctx.effective_anti_trope = ""
        round_ctx.intro_dna = ""
        round_ctx.story_context = ""
        round_ctx.style_guide = ""
        round_ctx.reference_anchor_prompt = ""
        round_ctx.mandatory_context = ""
        round_ctx.justification_prompt = ""
        round_ctx.reflexion_prompt = ""

        spinner = MagicMock()
        spinner.update_detail = MagicMock()

        # Patch away _record_s4_attempt (needs DB)
        with patch.object(ir, "_record_s4_attempt", MagicMock()):
            ir.run(
                round_num=0,
                stage4_spinner=spinner,
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert "protagonist_name" in captured_cv_context, (
            f"protagonist_name not in _cv_context. Keys: {list(captured_cv_context.keys())}"
        )
        assert captured_cv_context["protagonist_name"] == prot_name

    def test_protagonist_name_from_protagonist_config(self):
        """protagonist_name also resolves via CoreIdentity.protagonist path."""
        from modules.core.stage4_interview_round import Stage4InterviewRound

        prot_name = "주인공이름"
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.perf_timer = MagicMock()
        ctx.current_project = MagicMock()
        # Use the CoreIdentity.protagonist path (HUDKeys 0순위)
        ctx.current_project.master_bible = {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"protagonist": prot_name}},
            }
        }
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.npc_registry = {}
        ctx.get_module = MagicMock(return_value=None)
        ctx.failure_learner = None

        ir = Stage4InterviewRound(ctx)

        captured: dict = {}

        round_ctx = MagicMock()
        round_ctx.chief_writer = MagicMock()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "원고 내용 " * 30, "strategy_name": "test"}
        ]
        round_ctx.manuscript_validator = MagicMock()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "metrics": {"length": 600}, "focus_points": []}
        ]
        round_ctx.consistency_validator = MagicMock()
        round_ctx.consistency_validator.validate.side_effect = lambda ms, cv: captured.update(cv) or {
            "violations": [],
            "score_penalty": 0,
        }
        round_ctx.blocking_validator = MagicMock()
        round_ctx.blocking_validator.validate.return_value = {"passed": True, "failures": []}
        round_ctx.continuity_validator = MagicMock()
        round_ctx.continuity_validator.validate.return_value = {"passed": True, "violations": []}
        round_ctx.next_ep = 2
        round_ctx.blueprint = {}
        round_ctx.arc_data = {"arc_no": 1}
        round_ctx.arc_pos = 0
        round_ctx.total_ep_in_arc = 5
        round_ctx.arc_tactical = {}
        round_ctx.prev_text = ""
        round_ctx.prev_ending = ""
        round_ctx.prev_manuscripts_text = ""
        round_ctx.episode_digest = ""
        round_ctx.hud_report = ""
        round_ctx.current_inventory = []
        round_ctx.current_martial_arts = []
        round_ctx.dead_npcs = []
        round_ctx.item_acquisition_timeline = ""
        round_ctx.chain_link_section = ""
        round_ctx.world_state_summary = ""
        round_ctx.purism_prompt = ""
        round_ctx.genre_name = "wuxia"
        round_ctx.npc_equipment_summary = ""
        round_ctx.effective_anti_trope = ""
        round_ctx.intro_dna = ""
        round_ctx.story_context = ""
        round_ctx.style_guide = ""
        round_ctx.reference_anchor_prompt = ""
        round_ctx.mandatory_context = ""
        round_ctx.justification_prompt = ""
        round_ctx.reflexion_prompt = ""

        spinner = MagicMock()
        spinner.update_detail = MagicMock()

        with patch.object(ir, "_record_s4_attempt", MagicMock()):
            ir.run(
                round_num=0,
                stage4_spinner=spinner,
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert "protagonist_name" in captured, (
            f"protagonist_name not found in _cv_context keys: {list(captured.keys())}"
        )
        assert captured["protagonist_name"] == prot_name


# ---------------------------------------------------------------------------
# Test 8 — Stage4InterviewRound builds _cv_context with _failure_learner
# ---------------------------------------------------------------------------


class TestInterviewRoundFailureLearnerWiring:
    """Verify that when Stage4InterviewRound builds _cv_context it injects
    ctx.failure_learner as _failure_learner (P6-01 wiring,
    line ~332 of stage4_interview_round.py)."""

    def test_failure_learner_key_present_in_cv_context(self):
        from modules.core.stage4_interview_round import Stage4InterviewRound

        failure_learner_mock = MagicMock()

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.perf_timer = MagicMock()
        ctx.current_project = MagicMock()
        ctx.current_project.master_bible = {}
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.npc_registry = {}
        ctx.get_module = MagicMock(return_value=None)
        ctx.failure_learner = failure_learner_mock

        ir = Stage4InterviewRound(ctx)

        captured: dict = {}

        round_ctx = MagicMock()
        round_ctx.chief_writer = MagicMock()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "원고 내용 " * 30, "strategy_name": "test"}
        ]
        round_ctx.manuscript_validator = MagicMock()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "metrics": {"length": 600}, "focus_points": []}
        ]
        round_ctx.consistency_validator = MagicMock()
        round_ctx.consistency_validator.validate.side_effect = lambda ms, cv: captured.update(cv) or {
            "violations": [],
            "score_penalty": 0,
        }
        round_ctx.blocking_validator = MagicMock()
        round_ctx.blocking_validator.validate.return_value = {"passed": True, "failures": []}
        round_ctx.continuity_validator = MagicMock()
        round_ctx.continuity_validator.validate.return_value = {"passed": True, "violations": []}
        round_ctx.next_ep = 3
        round_ctx.blueprint = {}
        round_ctx.arc_data = {"arc_no": 1}
        round_ctx.arc_pos = 0
        round_ctx.total_ep_in_arc = 5
        round_ctx.arc_tactical = {}
        round_ctx.prev_text = ""
        round_ctx.prev_ending = ""
        round_ctx.prev_manuscripts_text = ""
        round_ctx.episode_digest = ""
        round_ctx.hud_report = ""
        round_ctx.current_inventory = []
        round_ctx.current_martial_arts = []
        round_ctx.dead_npcs = []
        round_ctx.item_acquisition_timeline = ""
        round_ctx.chain_link_section = ""
        round_ctx.world_state_summary = ""
        round_ctx.purism_prompt = ""
        round_ctx.genre_name = "wuxia"
        round_ctx.npc_equipment_summary = ""
        round_ctx.effective_anti_trope = ""
        round_ctx.intro_dna = ""
        round_ctx.story_context = ""
        round_ctx.style_guide = ""
        round_ctx.reference_anchor_prompt = ""
        round_ctx.mandatory_context = ""
        round_ctx.justification_prompt = ""
        round_ctx.reflexion_prompt = ""

        spinner = MagicMock()
        spinner.update_detail = MagicMock()

        with patch.object(ir, "_record_s4_attempt", MagicMock()):
            ir.run(
                round_num=0,
                stage4_spinner=spinner,
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert "_failure_learner" in captured, (
            f"_failure_learner not found in _cv_context keys: {list(captured.keys())}"
        )
        # The injected value must be the same object as ctx.failure_learner
        assert captured["_failure_learner"] is failure_learner_mock

    def test_failure_learner_none_when_ctx_has_none(self):
        """When ctx.failure_learner is None, _cv_context['_failure_learner'] == None."""
        from modules.core.stage4_interview_round import Stage4InterviewRound

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.perf_timer = MagicMock()
        ctx.current_project = MagicMock()
        ctx.current_project.master_bible = {}
        ctx.state_tracker = None
        ctx.get_module = MagicMock(return_value=None)
        # Explicitly None — getattr(ctx, "failure_learner", None) should return None
        del ctx.failure_learner
        ctx.configure_mock(**{"failure_learner": None})

        ir = Stage4InterviewRound(ctx)

        captured: dict = {}

        round_ctx = MagicMock()
        round_ctx.chief_writer = MagicMock()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "원고 내용 " * 30, "strategy_name": "test"}
        ]
        round_ctx.manuscript_validator = MagicMock()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "metrics": {"length": 600}, "focus_points": []}
        ]
        round_ctx.consistency_validator = MagicMock()
        round_ctx.consistency_validator.validate.side_effect = lambda ms, cv: captured.update(cv) or {
            "violations": [],
            "score_penalty": 0,
        }
        round_ctx.blocking_validator = MagicMock()
        round_ctx.blocking_validator.validate.return_value = {"passed": True, "failures": []}
        round_ctx.continuity_validator = MagicMock()
        round_ctx.continuity_validator.validate.return_value = {"passed": True, "violations": []}
        round_ctx.next_ep = 4
        round_ctx.blueprint = {}
        round_ctx.arc_data = {"arc_no": 1}
        round_ctx.arc_pos = 0
        round_ctx.total_ep_in_arc = 5
        round_ctx.arc_tactical = {}
        round_ctx.prev_text = ""
        round_ctx.prev_ending = ""
        round_ctx.prev_manuscripts_text = ""
        round_ctx.episode_digest = ""
        round_ctx.hud_report = ""
        round_ctx.current_inventory = []
        round_ctx.current_martial_arts = []
        round_ctx.dead_npcs = []
        round_ctx.item_acquisition_timeline = ""
        round_ctx.chain_link_section = ""
        round_ctx.world_state_summary = ""
        round_ctx.purism_prompt = ""
        round_ctx.genre_name = "wuxia"
        round_ctx.npc_equipment_summary = ""
        round_ctx.effective_anti_trope = ""
        round_ctx.intro_dna = ""
        round_ctx.story_context = ""
        round_ctx.style_guide = ""
        round_ctx.reference_anchor_prompt = ""
        round_ctx.mandatory_context = ""
        round_ctx.justification_prompt = ""
        round_ctx.reflexion_prompt = ""

        spinner = MagicMock()
        spinner.update_detail = MagicMock()

        with patch.object(ir, "_record_s4_attempt", MagicMock()):
            ir.run(
                round_num=0,
                stage4_spinner=spinner,
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        # Key must be present even if None
        assert "_failure_learner" in captured
        assert captured["_failure_learner"] is None
