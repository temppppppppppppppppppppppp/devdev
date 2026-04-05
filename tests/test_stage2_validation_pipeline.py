"""[B-1-6] Unit tests for Stage2ValidationPipeline."""

import builtins
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from modules.core.stage2_contracts import TACTICAL_DOC_DUPLICATE_THRESHOLD
from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.core.stage2_validation_pipeline import Stage2ValidationPipeline


@pytest.fixture
def orchestrator_with_ctx():
    app = MagicMock()
    orchestrator = Stage2Orchestrator(app=app)

    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.audit_event = MagicMock()
    ctx.state_tracker = None
    ctx.arc_draft_validator = None
    ctx.self_reflector = None
    ctx.arc_corrector = None
    ctx.continuity_inspector = None
    ctx.semantic_plot_guard = None
    ctx.failure_learner = None
    ctx.pass_rate_monitor = None
    ctx.stage2_optimizer = None
    ctx.use_arc_corrector = False
    ctx.agents = {}
    ctx.validate_arc_mapping = MagicMock(side_effect=lambda arc, *a, **kw: arc)
    ctx.build_strong_kind_feedback = MagicMock(return_value="strong")
    ctx.build_focused_context = MagicMock(return_value="focused")

    orchestrator._ctx = ctx
    return orchestrator


@pytest.fixture
def pipeline(orchestrator_with_ctx):
    return orchestrator_with_ctx.validation_pipeline


@pytest.fixture
def valid_refined_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 5,
        "ep_count": 5,
        "tactical_doc": "주인공이 천풍대전에서 단서를 확보하고 대치를 만든다. " * 50,
        "beat_sequence": [
            "첫 번째 비트에서 주인공은 단서를 얻고 다음 행동의 이유를 확인한다." * 2,
            "두 번째 비트에서 조력자와 충돌하며 위험 신호를 탐지한다." * 2,
            "세 번째 비트에서 반전이 드러나고 대립이 전진한다." * 2,
            "네 번째 비트에서 손실과 대가를 확인하며 결정을 강행한다." * 2,
            "다섯 번째 비트에서 목표를 향해 전투를 시작한다." * 2,
        ],
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {"primary": "standard_progression", "secondary": [], "mixing_logic": "기본"},
        "joint_docs": {"final_location": "천풍대전", "physical_inventory": ["천풍검"], "world_joint": "변화 없음"},
        "status_shadow": {"internal_energy_loss": "10%", "expected_injuries": "없음", "item_consumption": []},
    }


class TestValidationPipelineStructure:
    def test_init_requires_host(self, orchestrator_with_ctx):
        pipe = Stage2ValidationPipeline(orchestrator_with_ctx)
        assert pipe.host is orchestrator_with_ctx

    def test_ctx_proxy(self, orchestrator_with_ctx):
        pipe = Stage2ValidationPipeline(orchestrator_with_ctx)
        assert pipe.ctx is orchestrator_with_ctx.ctx

    def test_all_methods_exist(self, pipeline):
        assert hasattr(pipeline, "run_validation")
        assert hasattr(pipeline, "_normalize_tactical_text")
        assert hasattr(pipeline, "_is_tactical_doc_duplicate")
        assert hasattr(pipeline, "_normalize_flow_text")
        assert hasattr(pipeline, "_stage2_flow_guard")
        assert hasattr(pipeline, "_stage2_flow_guard_legacy")

    def test_legacy_flow_guard_annotation_is_list(self):
        ann = Stage2ValidationPipeline._stage2_flow_guard_legacy.__annotations__
        assert ann.get("normalized") is list


class TestTextUtils:
    def test_normalize_tactical_basic(self, pipeline):
        assert pipeline._normalize_tactical_text("전술   문서  내용") == "전술 문서 내용"

    def test_normalize_tactical_none(self, pipeline):
        assert pipeline._normalize_tactical_text(None) == ""
        assert pipeline._normalize_tactical_text(123) == ""

    def test_normalize_flow_basic(self, pipeline):
        out = pipeline._normalize_flow_text("테스트!@#$% 문자")
        assert "!" not in out
        assert out == out.lower()

    def test_is_duplicate_exact_match(self, pipeline):
        text = "동일한 전술 문서"
        assert pipeline._is_tactical_doc_duplicate(text, [text]) is True

    def test_is_duplicate_empty(self, pipeline):
        assert pipeline._is_tactical_doc_duplicate("", ["참조"]) is False
        assert pipeline._is_tactical_doc_duplicate("텍스트", []) is False

    def test_duplicate_threshold_matches_shared_contract(self, pipeline, orchestrator_with_ctx):
        candidate = "alpha beta gamma delta epsilon zeta eta theta"
        reference = "alpha beta gamma delta epsilon zeta eta iota"

        assert TACTICAL_DOC_DUPLICATE_THRESHOLD == 0.92
        assert pipeline._is_tactical_doc_duplicate(candidate, [reference]) is True
        assert orchestrator_with_ctx._is_tactical_doc_duplicate(candidate, [reference]) is True


class TestFlowGuard:
    def test_reject_insufficient_beats(self, pipeline):
        arc = {"ep_count": 5, "beat_sequence": ["a", "b"]}
        result = pipeline._stage2_flow_guard(arc)
        assert result["status"] == "REJECT"

    def test_reject_short_beats(self, pipeline):
        arc = {"ep_count": 3, "beat_sequence": ["짧음", "짧음", "짧음"]}
        result = pipeline._stage2_flow_guard(arc)
        assert result["status"] == "REJECT"

    def test_legacy_fallback_stagnation(self, pipeline):
        normalized = [
            "주인공 전투 개시",
            "주인공 전투 개시",
            "주인공 전투 개시",
            "주인공 전투 개시",
        ]
        result = pipeline._stage2_flow_guard_legacy(normalized)
        assert result["status"] == "REJECT"

    def test_legacy_pass(self, pipeline):
        normalized = [
            "주인공이 정보원을 만난다",
            "적대 세력의 함정을 발견한다",
            "동료와 갈등을 조정한다",
            "대치를 준비하며 이동한다",
        ]
        result = pipeline._stage2_flow_guard_legacy(normalized)
        assert result["status"] == "PASS"

    def test_runtime_exception_uses_legacy_fallback(self, pipeline, valid_refined_arc, monkeypatch):
        class BoomAnalyzer:
            def __init__(self, *args, **kwargs):
                pass

            def analyze(self, _beats):
                raise RuntimeError("boom")

        fake_module = SimpleNamespace(NarrativeStructureAnalyzer=BoomAnalyzer)
        monkeypatch.setitem(sys.modules, "modules.core.narrative_structure_analyzer", fake_module)

        result = pipeline._stage2_flow_guard(valid_refined_arc)

        assert result["fallback"] is True
        assert result["fallback_mode"] == "legacy_flow_guard"
        assert result["fallback_reason"] == "runtime_error"
        assert result["status"] == pipeline._stage2_flow_guard_legacy(
            [pipeline._normalize_flow_text(beat) for beat in valid_refined_arc["beat_sequence"]]
        )["status"]

    def test_import_error_uses_legacy_fallback(self, pipeline, valid_refined_arc, monkeypatch):
        real_import = builtins.__import__

        def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "modules.core.narrative_structure_analyzer":
                raise ImportError("missing")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        monkeypatch.delitem(sys.modules, "modules.core.narrative_structure_analyzer", raising=False)

        result = pipeline._stage2_flow_guard(valid_refined_arc)

        assert result["fallback"] is True
        assert result["fallback_mode"] == "legacy_flow_guard"
        assert result["fallback_reason"] == "import_error"


class TestRunValidation:
    @staticmethod
    def _base_kwargs(valid_refined_arc):
        return {
            "refined_arc": valid_refined_arc,
            "four_phase_passed": True,
            "all_refined_arcs": [],
            "entity_registry_for_director": None,
            "global_arc_no": 1,
            "current_ep_start": 1,
            "current_feedback": "",
            "generation_method": "analyst",
            "constraint_block": "",
            "enriched_block": {"block_theme": "test", "joint_docs": {}, "status_shadow": {}},
            "draft_validator_passed": True,
            "consensus_passed": True,
            "attempt": 0,
            "protagonist_name": "이청풍",
            "constraint_db": MagicMock(
                validate_arc_design=MagicMock(return_value={"valid": True, "violations": [], "warnings": []})
            ),
        }

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_invalid_arc_returns_retry(self, pipeline):
        kwargs = self._base_kwargs(valid_refined_arc={})
        kwargs["refined_arc"] = None
        result = pipeline.run_validation(**kwargs)
        assert result["action"] == "retry"
        assert "current_feedback" in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_flow_guard_reject_becomes_advisory(self, pipeline, valid_refined_arc):
        """[TF-25-08] Flow Guard REJECT → advisory로 전환, Director까지 도달."""
        pipeline._stage2_flow_guard = MagicMock(
            return_value={"status": "REJECT", "reason": "stagnation", "feedback": "flow retry"}
        )
        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)
        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "flow_guard" for a in advisories)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_duplicate_guard_reject_becomes_advisory(self, pipeline, valid_refined_arc):
        """[TF-25-08] Duplicate Guard REJECT → advisory로 전환."""
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        pipeline._is_tactical_doc_duplicate = MagicMock(return_value=True)
        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["all_refined_arcs"] = [{"arc_no": 0, "tactical_doc": "이전 전술"}]
        result = pipeline.run_validation(**kwargs)
        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "duplicate_guard" for a in advisories)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_happy_path_no_four_phase(self, pipeline, valid_refined_arc):
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)
        assert result["action"] == "proceed"
        assert isinstance(result["refined_arc"], dict)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_stage2_optimizer_receives_genre(self, pipeline, valid_refined_arc):
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        pipeline.ctx.stage2_optimizer = MagicMock()
        pipeline.ctx.stage2_optimizer.post_process_arc.return_value = (valid_refined_arc, [])
        pipeline.ctx.selected_genre = {"type": "investment"}

        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)

        assert result["action"] == "proceed"
        assert pipeline.ctx.stage2_optimizer.post_process_arc.call_args.kwargs["genre"] == "investment"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_auto_correct_pressure_becomes_advisory(self, pipeline, valid_refined_arc):
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        pipeline.ctx.stage2_optimizer = MagicMock()
        pipeline.ctx.stage2_optimizer.post_process_arc.return_value = (
            valid_refined_arc,
            [
                {"category": "continuity", "change_summary": "fix continuity"},
                {"category": "numbers", "change_summary": "fix numbers"},
                {"category": "entity", "change_summary": "fix entity"},
            ],
        )
        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        pressure = [a for a in advisories if a["source"] == "auto_correct_pressure"]
        assert len(pressure) == 1
        assert "threshold=3" in pressure[0]["message"]
        assert "continuity" in pressure[0]["message"]

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_auto_correct_summary_is_mirrored_to_ui_log(self, pipeline, valid_refined_arc):
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        pipeline.ctx.stage2_optimizer = MagicMock()
        pipeline.ctx.stage2_optimizer.post_process_arc.return_value = (
            valid_refined_arc,
            [
                {"category": "continuity", "change_summary": "fix continuity"},
                {"category": "numbers", "change_summary": "fix numbers"},
                {"category": "entity", "change_summary": "fix entity"},
            ],
        )

        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)

        assert result["action"] == "proceed"
        pipeline.ctx.ui.log.assert_any_call(
            "      [S2-OBS] Auto-correct arc 1: fix continuity, fix numbers, fix entity"
        )

    def test_consensus_reject_becomes_advisory(self, pipeline, valid_refined_arc):
        """[TF-25-08] Consensus REJECT → advisory로 전환."""
        consensus = MagicMock()
        consensus.validate_with_consensus.return_value = (
            "REJECT",
            {
                "vote_summary": {"pass": 1, "reject": 2},
                "critical_issues": [{"category": "plot_hole", "issue": "연결 누락"}],
                "all_issues": [{"category": "plot_hole", "issue": "연결 누락"}],
            },
        )
        pipeline.ctx.agents = {"consensus": consensus}
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = False
        kwargs["consensus_passed"] = False
        result = pipeline.run_validation(**kwargs)
        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "consensus" and "Consensus" in a["message"] for a in advisories)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_proceed_contains_required_keys(self, pipeline, valid_refined_arc):
        """[TF-25-08] proceed 반환에 python_advisories + corrections_made 포함."""
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        kwargs = self._base_kwargs(valid_refined_arc)
        result = pipeline.run_validation(**kwargs)
        required = {
            "action",
            "refined_arc",
            "draft_validator_passed",
            "consensus_passed",
            "suspected_duplicates",
            "corrections_made",
            "python_advisories",
        }
        assert required == set(result.keys())

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_continuity_reject_becomes_advisory_with_feedback(self, pipeline, valid_refined_arc):
        """[TF-25-08] ContinuityInspector REJECT → advisory로 전환, 구조화된 피드백 포함."""
        continuity_inspector = MagicMock()
        continuity_inspector.inspect_arc.return_value = {
            "decision": "REJECT",
            "severity": "MAJOR",
            "violations": [{"type": "state_conflict", "description": "state issue", "item_or_subject": "item"}],
        }

        pipeline.ctx.agents = {"continuity_inspector": continuity_inspector}
        pipeline.ctx.generate_structured_arc_feedback = MagicMock(return_value="\n[STRUCTURED_FEEDBACK]")
        pipeline.ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "keep consistency"})
        pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})

        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = False
        kwargs["all_refined_arcs"] = [{"arc_no": 0, "joint_docs": {}, "status_shadow": {}}]

        result = pipeline.run_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        ci_advisories = [a for a in advisories if a["source"] == "continuity_inspector"]
        assert len(ci_advisories) == 1
        assert "[STRUCTURED_FEEDBACK]" in ci_advisories[0]["message"]


class TestExtractedHelperFamilies:
    def test_build_invalid_refined_arc_retry_returns_retry_payload(self, pipeline):
        result = pipeline._build_invalid_refined_arc_retry(
            refined_arc=None,
            global_arc_no=7,
            consensus_passed=False,
            current_feedback="old",
        )

        assert result is not None
        assert result["early_return"]["action"] == "retry"
        assert "JSON" in result["current_feedback"]

    def test_collect_pre_validation_duplicates_records_suspected_duplicates(self, pipeline, valid_refined_arc):
        constraint_db = MagicMock()
        constraint_db.validate_arc_design.return_value = {
            "valid": False,
            "violations": ["중복 의심 A", "중복 의심 B", "중복 의심 C"],
            "warnings": ["warning"],
        }

        duplicates = pipeline._collect_pre_validation_duplicates(
            refined_arc=valid_refined_arc,
            four_phase_passed=False,
            constraint_db=constraint_db,
            global_arc_no=3,
        )

        assert duplicates == ["중복 의심 A", "중복 의심 B", "중복 의심 C"]
        pipeline.ctx.audit_event.assert_called_once()

    def test_build_continuity_reject_feedback_includes_banned_items_and_intensity(self, pipeline):
        pipeline.ctx.generate_structured_arc_feedback = MagicMock(return_value="\n[STRUCTURED_FEEDBACK]")
        pipeline.ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "retry carefully"})
        pipeline.ctx.build_strong_kind_feedback = MagicMock(return_value="strong-kind")
        pipeline.ctx.build_focused_context = MagicMock(return_value="focused-context")

        feedback = pipeline._build_continuity_reject_feedback(
            continuity_result={"decision": "REJECT"},
            violations=[
                {
                    "type": "duplicate_acquisition",
                    "description": "same sword",
                    "item_or_subject": "백근 대도",
                }
            ],
            all_refined_arcs=[{"arc_no": 2, "joint_docs": {}, "status_shadow": {}}],
            attempt=1,
            protagonist_name="주인공",
            global_arc_no=3,
        )

        assert "백근 대도" in feedback
        assert "retry carefully" in feedback
        assert "[STRUCTURED_FEEDBACK]" in feedback
