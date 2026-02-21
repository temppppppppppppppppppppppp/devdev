"""[B-1-8] Unit tests for Stage2PreflightAnalysis extracted from Stage2Orchestrator."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot
from modules.core.stage2_preflight import Stage2PreflightAnalysis


@pytest.fixture
def preflight_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.audit_event = MagicMock()

    weaver = MagicMock()
    weaver.generate_arc_drive.return_value = {"desire_vector": "grow", "status": "ok"}

    preflight_agent = MagicMock()
    preflight_agent.analyze.return_value = {
        "item_timeline": [1],
        "absolute_prohibitions": [],
        "relationship_map": {"A": 1},
    }
    preflight_agent.generate_analyst_injection.return_value = "preflight injection"

    state_extractor = MagicMock()
    state_extractor.extract_cumulative_state.return_value = {"entity_registry": {"npc": {"role": "ally"}}}

    four_phase = MagicMock()
    four_phase.generate.return_value = (None, {"final_verdict": "REJECT", "phases": {"validate": {"issues_count": 1}}})

    ctx.agents = {
        "weaver": weaver,
        "preflight": preflight_agent,
        "state_extractor": state_extractor,
        "four_phase": four_phase,
    }

    tracker = MagicMock()
    tracker.get_resolved_plots_summary.return_value = "resolved"
    tracker.resolved_plots = []
    ctx.state_tracker = tracker

    ctx.constraint_compiler = None
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0

    ctx.quality_dashboard = None
    ctx.stage2_optimizer = None
    ctx.quality_amplifier = None
    ctx.agent_intelligence = None
    ctx.failure_learner = None
    ctx.constitutional_checker = None
    ctx.stage_rejection_history = []
    ctx.generate_reverse_feedback_stage3_to_2 = MagicMock(return_value="reverse")
    ctx.build_minimal_arc_context = MagicMock(return_value="minimal context")
    ctx.fix_entity_registry_protagonist = MagicMock(side_effect=lambda registry, _name: registry)

    ctx.memory = None
    ctx.context_advisor = None
    ctx.semantic_plot_guard = None
    ctx.current_project = MagicMock()

    return ctx


@pytest.fixture
def preflight(preflight_ctx):
    host = MagicMock()
    host.ctx = preflight_ctx
    return Stage2PreflightAnalysis(host)


def _state_setup_kwargs(**overrides):
    defaults = {
        "all_refined_arcs": [],
        "arcs_source": [{"arc_no": 1}],
        "arc_idx": 0,
        "lack_report": {"lack": []},
        "grand_obj": "goal",
        "global_arc_no": 1,
        "constraint_db": MagicMock(generate_constraint_block=MagicMock(return_value="block")),
    }
    defaults.update(overrides)
    return defaults


def _arc_analysis_kwargs(**overrides):
    defaults = {
        "attempt": 0,
        "current_feedback": "",
        "constraint_block": "constraint block",
        "last_refined_context": "last context",
        "all_refined_arcs": [],
        "protagonist_name": "hero",
        "global_arc_no": 1,
        "cached_preflight_injection": "cached inj",
        "cached_preflight_result": {"k": 1},
    }
    defaults.update(overrides)
    return defaults


def _enrichment_kwargs(**overrides):
    defaults = {
        "attempt": 0,
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_vol_strategy": {"strategy_doc": "doc"},
        "enriched_block": {"block_theme": "theme", "joint_docs": {}, "status_shadow": {}},
        "all_refined_arcs": [],
        "bible_root": {"AssetLibrary": {}},
        "protagonist_name": "hero",
        "director_feedback_for_fourphase": "",
        "entity_registry_for_director": {},
        "genre_for_tracker": "wuxia",
    }
    defaults.update(overrides)
    return defaults


class TestPreflightStructure:
    def test_init_requires_host_for_ctx(self):
        p = Stage2PreflightAnalysis(None)
        with pytest.raises(AttributeError):
            _ = p.ctx

    def test_ctx_proxy(self, preflight, preflight_ctx):
        assert preflight.ctx is preflight_ctx

    def test_methods_exist(self, preflight):
        assert hasattr(preflight, "_preflight_state_setup")
        assert hasattr(preflight, "_preflight_arc_analysis")
        assert hasattr(preflight, "_preflight_enrichment")


class TestPreflightStateSetup:
    def test_returns_all_required_keys(self, preflight):
        out = preflight._preflight_state_setup(**_state_setup_kwargs())
        required = {
            "arc_drive",
            "cached_preflight_injection",
            "cached_preflight_result",
            "passed",
            "current_feedback",
            "constraint_block",
            "attempt",
            "max_attempts",
            "director_feedback_for_fourphase",
            "st_snapshot",
        }
        assert required == set(out.keys())

    def test_parallel_execution_runs_both_tasks(self, preflight):
        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        preflight.ctx.agents["weaver"].generate_arc_drive.assert_called_once()
        preflight.ctx.agents["preflight"].analyze.assert_called_once()
        assert out["cached_preflight_injection"] == "preflight injection"

    def test_weaver_error_returns_error_drive(self, preflight):
        preflight.ctx.agents["weaver"].generate_arc_drive.side_effect = RuntimeError("boom")
        out = preflight._preflight_state_setup(**_state_setup_kwargs())
        assert out["arc_drive"]["status"] == "error"
        preflight.ctx.audit_event.assert_called()

    def test_constraint_compiler_integration(self, preflight):
        compiler = MagicMock()
        compiler.compile.return_value = "compiled constraints"
        preflight.ctx.constraint_compiler = compiler

        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        assert "compiled constraints" in out["constraint_block"]

    def test_state_extractor_exception_non_propagating(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(return_value="compiled"))
        preflight.ctx.agents["state_extractor"].extract_cumulative_state.side_effect = RuntimeError("err")

        out = preflight._preflight_state_setup(**_state_setup_kwargs(all_refined_arcs=[{"arc_no": 0}]))
        assert isinstance(out, dict)
        preflight.ctx.audit_event.assert_called()


class TestPreflightArcAnalysis:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_returns_all_required_keys(self, preflight):
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs())
        required = {
            "refined_arc",
            "generation_method",
            "constraint_block",
            "entity_registry_for_director",
        }
        assert required == set(out.keys())

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_focus_mode_on_retry(self, preflight):
        out = preflight._preflight_arc_analysis(
            **_arc_analysis_kwargs(attempt=1, current_feedback="fix this", constraint_block="")
        )
        assert out["generation_method"] == "analyst"
        preflight.ctx.build_minimal_arc_context.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_quality_trend_injected(self, preflight):
        preflight.ctx.quality_dashboard = MagicMock()
        preflight.ctx.quality_dashboard.get_score_trend_summary.return_value = {
            "trend": "up",
            "summary": "?덉쭏 異붿꽭 ?곸듅",
        }
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(constraint_block=""))
        preflight.ctx.quality_dashboard.get_score_trend_summary.assert_called_once_with(stage=2)
        assert "enhanced_context" not in out

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_constraint_compiler_sets_entity_registry(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(return_value="cc"))
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=[{"arc_no": 1}]))
        # [Sweep48] constraint_block은 입력값 그대로 보존 (setup에서 이미 병합됨)
        assert out["constraint_block"] == "constraint block"
        assert out["entity_registry_for_director"] == {"npc": {"role": "ally"}}

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_entity_registry_default_is_dict_on_exception(self, preflight):
        preflight.ctx.constraint_compiler = MagicMock(compile=MagicMock(side_effect=RuntimeError("err")))
        preflight.ctx.agents.pop("state_extractor", None)
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=[{"arc_no": 1}]))
        assert out["entity_registry_for_director"] == {}

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_recent_patterns_collected(self, preflight):
        arcs = [
            {"hybrid_composition": {"primary": "p1"}},
            {"hybrid_composition": {"primary": "p2"}},
            {"hybrid_composition": {}},
        ]
        out = preflight._preflight_arc_analysis(**_arc_analysis_kwargs(all_refined_arcs=arcs))
        assert "recent_patterns" not in out


class TestPreflightEnrichment:
    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_no_fourphase_returns_defaults(self, preflight):
        preflight.ctx.agents = {}
        out = preflight._preflight_enrichment(**_enrichment_kwargs())
        assert out["four_phase_passed"] is False
        assert out["refined_arc"] is None
        assert out["generation_method"] == "analyst"

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_fourphase_exception_non_propagating(self, preflight):
        preflight.ctx.agents["four_phase"].generate.side_effect = RuntimeError("fail")
        out = preflight._preflight_enrichment(**_enrichment_kwargs())
        assert out["four_phase_passed"] is False
        assert "FourPhase" in out["director_feedback_for_fourphase"]
        assert "fail" in out["director_feedback_for_fourphase"]

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_fourphase_pass_triggers_state_tracker_enrichment(self, preflight):
        tracker = MagicMock()
        tracker.npc_registry = {"npc": {"status": "alive"}}
        tracker.resolved_plots = []
        tracker.entity_destructions = []
        tracker.protagonist_skills = set()
        tracker.skill_acquisitions = []
        tracker.npc_npc_relationships = {}
        tracker.item_state_registry = {}
        tracker.active_plots = []
        tracker.npc_dialogue_profiles = {}
        tracker.in_world_timeline = []
        tracker.current_companions = []
        tracker.pending_commitments = []
        tracker.protagonist_emotion = {}
        tracker.extract_npc_deaths_from_arc.return_value = ["npc1"]
        tracker.extract_skill_acquisitions_from_arc.return_value = ["skill1"]
        tracker.extract_npc_info_from_arc.return_value = [{"name": "npc1"}]
        tracker.check_suspended_plots.return_value = []
        tracker.generate_arc_summary.return_value = {"summary": "ok"}
        tracker.cleanup_npc_registry_with_llm.return_value = []
        preflight.ctx.state_tracker = tracker

        refined_arc = {
            "tactical_doc": "x" * 1600,
            "joint_docs": {},
            "status_shadow": {},
        }
        preflight.ctx.agents["four_phase"].generate.return_value = (
            refined_arc,
            {"final_verdict": "PASS", "phases": {"generate": {"candidates_count": 3, "selected_strategy": "s"}}},
        )

        out = preflight._preflight_enrichment(**_enrichment_kwargs(global_arc_no=5, all_refined_arcs=[{"arc_no": 1}]))
        assert out["four_phase_passed"] is True
        assert out["generation_method"] == "four_phase"
        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        preflight.ctx.current_project.save_v20_anchor.assert_called()

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_legacy_vector_fallback_without_advisor(self, preflight):
        preflight.ctx.context_advisor = None
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context.return_value = "legacy vector block"
        preflight.ctx.memory.retrieve_multi_query_context = MagicMock()
        preflight.ctx.memory.retrieve_npc_context = MagicMock()

        preflight._preflight_enrichment(**_enrichment_kwargs(current_ep_start=3))

        preflight.ctx.memory.retrieve_high_res_context.assert_called_once()
        assert not preflight.ctx.memory.retrieve_multi_query_context.called
        assert not preflight.ctx.memory.retrieve_npc_context.called
        call_kwargs = preflight.ctx.agents["four_phase"].generate.call_args.kwargs
        assert call_kwargs["vector_context"] == "legacy vector block"

    @patch("modules.core.spinners.StageSpinner", MagicMock())
    def test_advisor_plan_dispatches_vec_and_npc_sources(self, preflight):
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_high_res_context = MagicMock(return_value="legacy")
        preflight.ctx.memory.retrieve_multi_query_context = MagicMock(side_effect=["vec one", "vec two"])
        preflight.ctx.memory.retrieve_npc_context = MagicMock(return_value="npc one")
        preflight.ctx.context_advisor = MagicMock()
        preflight.ctx.context_advisor.plan_stage2_retrieval.return_value = RetrievalPlan(
            stage="stage2",
            episode_num=3,
            slots=[
                RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_recent", query="alice bob", source="db_npc_history", priority=1),
                RetrievalSlot(category="arc_tactical", query="tactical query", source="vec_memory", priority=2),
            ],
            total_budget_chars=2000,
        )

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.stage2_enabled":
                return True
            if key == "context.vector_max_results_s2":
                return 8
            return default

        with patch("modules.core.stage2_preflight._threshold", side_effect=threshold_side_effect):
            preflight._preflight_enrichment(
                **_enrichment_kwargs(
                    current_ep_start=3,
                    enriched_block={
                        "block_theme": "theme",
                        "tactical_doc": "tactical",
                        "npc_roster": ["alice", "bob"],
                        "joint_docs": {},
                        "status_shadow": {},
                    },
                )
            )

        preflight.ctx.context_advisor.plan_stage2_retrieval.assert_called_once()
        assert preflight.ctx.memory.retrieve_multi_query_context.call_count == 2
        preflight.ctx.memory.retrieve_npc_context.assert_called_once()
        preflight.ctx.memory.retrieve_high_res_context.assert_not_called()

        npc_call = preflight.ctx.memory.retrieve_npc_context.call_args.kwargs
        assert npc_call["npc_names"][:2] == ["alice", "bob"]

        vector_context = preflight.ctx.agents["four_phase"].generate.call_args.kwargs["vector_context"]
        assert "[SC:block_theme]" in vector_context
        assert "[SC:npc_recent]" in vector_context
        assert "[SC:arc_tactical]" in vector_context


class TestGlobalBudgetTruncation:
    """P1-3: stage2 글로벌 예산 가드 검증."""

    def test_global_budget_truncation(self, preflight):
        """결합 텍스트가 total_budget_chars 초과 시 절단."""
        preflight.ctx.memory = MagicMock()
        preflight.ctx.memory.retrieve_multi_query_context.return_value = "x" * 5000
        preflight.ctx.memory.retrieve_npc_context.return_value = "y" * 5000

        plan = RetrievalPlan(
            stage="stage2",
            episode_num=5,
            slots=[
                RetrievalSlot(category="block_theme", query="theme query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_recent", query="npc query", source="db_npc_history", priority=2),
            ],
            total_budget_chars=100,
        )

        result = preflight._execute_stage2_retrieval_plan(plan, current_ep=5)
        assert len(result) <= 100
