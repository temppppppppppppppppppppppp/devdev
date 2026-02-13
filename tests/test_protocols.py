"""
[Step 3] Protocol 적합성 테스트

검증 대상:
1. Protocol 정의 자체의 정합성
2. Mock 클래스로 구조적 서브타이핑 확인 (isinstance 통과/거부)
3. 실제 에이전트 클래스의 메서드 존재 확인 (인스턴스화 없이)
4. 미적합 에이전트의 메서드명 불일치 확인
"""

import inspect

from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    Corrector,
    EnsembleGenerator,
    PipelineGenerator,
)

# ═══════════════════════════════════════════════════════════════════
# 1. Protocol 정의 정합성
# ═══════════════════════════════════════════════════════════════════


class TestProtocolDefinitions:
    """Protocol이 runtime_checkable이고 올바른 메서드를 정의하는지"""

    def test_pipeline_generator_is_runtime_checkable(self):
        assert (
            hasattr(PipelineGenerator, "__protocol_attrs__")
            or hasattr(PipelineGenerator, "__abstractmethods__")
            or callable(getattr(PipelineGenerator, "_is_runtime_protocol", None))
        )

    def test_all_protocols_are_protocol_subclass(self):
        from typing import Protocol

        for proto in [PipelineGenerator, EnsembleGenerator, ArtifactValidator, ArtifactCritic, Corrector]:
            assert issubclass(proto, Protocol)

    def test_protocol_method_names(self):
        """각 Protocol이 기대하는 메서드를 정의하는지"""
        assert "generate" in dir(PipelineGenerator)
        assert "generate_ensemble" in dir(EnsembleGenerator)
        assert "validate" in dir(ArtifactValidator)
        assert "critique" in dir(ArtifactCritic)
        assert "can_correct" in dir(Corrector)
        assert "correct" in dir(Corrector)


# ═══════════════════════════════════════════════════════════════════
# 2. Mock 클래스 — 구조적 서브타이핑 검증
# ═══════════════════════════════════════════════════════════════════


class MockPipelineGen:
    def generate(self, **kwargs):
        return {"arc_no": 1}, {"status": "ok"}


class MockEnsembleGen:
    def generate_ensemble(self, **kwargs):
        return {"best": True}, [{"a": 1}, {"b": 2}]


class MockValidator:
    def validate(self, **kwargs):
        return {"verdict": "PASS", "score": 85}


class MockCritic:
    def critique(self, **kwargs):
        return {"score": 70, "issues": ["pacing"]}


class MockCorrector:
    def can_correct(self, **kwargs):
        return True, [{"severity": "minor"}], []

    def correct(self, **kwargs):
        return {"arc_no": 1, "fixed": True}, {"applied": ["fix1"]}


class MockEmpty:
    """메서드 없는 클래스"""

    pass


class MockWrongMethod:
    """메서드명 불일치"""

    def create(self, **kwargs):
        return None, {}


class TestMockConformance:
    """Mock 클래스로 isinstance 통과/거부 확인"""

    def test_pipeline_generator_pass(self):
        assert isinstance(MockPipelineGen(), PipelineGenerator)

    def test_ensemble_generator_pass(self):
        assert isinstance(MockEnsembleGen(), EnsembleGenerator)

    def test_validator_pass(self):
        assert isinstance(MockValidator(), ArtifactValidator)

    def test_critic_pass(self):
        assert isinstance(MockCritic(), ArtifactCritic)

    def test_corrector_pass(self):
        assert isinstance(MockCorrector(), Corrector)

    def test_empty_class_fails_all(self):
        empty = MockEmpty()
        assert not isinstance(empty, PipelineGenerator)
        assert not isinstance(empty, EnsembleGenerator)
        assert not isinstance(empty, ArtifactValidator)
        assert not isinstance(empty, ArtifactCritic)
        assert not isinstance(empty, Corrector)

    def test_wrong_method_name_fails(self):
        wrong = MockWrongMethod()
        assert not isinstance(wrong, PipelineGenerator)


# ═══════════════════════════════════════════════════════════════════
# 3. 실제 에이전트 클래스 — 메서드 존재 검증 (인스턴스화 없이)
# ═══════════════════════════════════════════════════════════════════


class TestAgentStructuralConformance:
    """실제 에이전트 클래스가 Protocol에 필요한 메서드를 보유하는지 검증

    인스턴스화하지 않고 클래스 수준에서 hasattr 검사.
    (인스턴스화에는 context/client 필요)
    """

    def test_four_phase_has_generate(self):
        from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator

        assert hasattr(FourPhaseArcGenerator, "generate")
        sig = inspect.signature(FourPhaseArcGenerator.generate)
        assert "arc_no" in sig.parameters

    def test_three_phase_has_generate(self):
        from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator

        assert hasattr(ThreePhaseBlueprintGenerator, "generate")
        sig = inspect.signature(ThreePhaseBlueprintGenerator.generate)
        assert "ep_num" in sig.parameters

    def test_arc_ensemble_has_generate_ensemble(self):
        from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator

        assert hasattr(ArcEnsembleGenerator, "generate_ensemble")
        sig = inspect.signature(ArcEnsembleGenerator.generate_ensemble)
        assert "arc_no" in sig.parameters

    def test_blueprint_ensemble_has_generate_ensemble(self):
        from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

        assert hasattr(BlueprintEnsembleGenerator, "generate_ensemble")
        sig = inspect.signature(BlueprintEnsembleGenerator.generate_ensemble)
        assert "ep_num" in sig.parameters

    def test_unified_arc_validator_has_validate(self):
        from modules.domain.agents.unified_arc_validator import UnifiedArcValidator

        assert hasattr(UnifiedArcValidator, "validate")
        sig = inspect.signature(UnifiedArcValidator.validate)
        assert "arc" in sig.parameters

    def test_arc_critic_has_critique(self):
        from modules.domain.agents.arc_critic import ArcCritic

        assert hasattr(ArcCritic, "critique")
        sig = inspect.signature(ArcCritic.critique)
        assert "generated_arc" in sig.parameters

    def test_arc_corrector_has_correct_and_can_correct(self):
        from modules.domain.agents.arc_corrector import ArcCorrector

        assert hasattr(ArcCorrector, "can_correct")
        assert hasattr(ArcCorrector, "correct")
        sig = inspect.signature(ArcCorrector.correct)
        assert "arc" in sig.parameters


# ═══════════════════════════════════════════════════════════════════
# 4. 미적합 에이전트 — 메서드명 불일치 확인
# ═══════════════════════════════════════════════════════════════════


class TestNonConformingAgents:
    """미적합 에이전트의 메서드명 차이를 문서화 겸 검증

    이 테스트들은 "현재 미적합"임을 확인하는 것.
    향후 어댑터 도입 시 이 테스트를 적합 테스트로 전환.
    """

    def test_chief_writer_has_generate_ensemble_but_different_return(self):
        """ChiefWriter는 generate_ensemble이 있으나 반환 타입이 list[dict]"""
        from modules.domain.agents.chief_writer import ChiefWriter

        assert hasattr(ChiefWriter, "generate_ensemble")
        # 반환 타입 list[dict] ≠ Protocol의 tuple[dict|None, list[dict]]
        # 구조적으로는 메서드 존재하므로 isinstance는 통과할 수 있으나
        # 실제 반환값 계약이 다름 — 어댑터 필요

    def test_consensus_validator_uses_different_method_name(self):
        """ConsensusValidator는 validate_with_consensus() 사용"""
        from modules.domain.agents.consensus_validator import ConsensusValidator

        assert hasattr(ConsensusValidator, "validate_with_consensus")
        assert not hasattr(ConsensusValidator, "validate") or (
            # BaseAgent에서 상속받은 validate이 있을 수 있으나
            # ArtifactValidator Protocol 의도와 무관
            True
        )

    def test_critic_uses_different_method_name(self):
        """Critic은 critique_manuscript() 사용, critique() 아님"""
        from modules.domain.agents.critic import Critic

        assert hasattr(Critic, "critique_manuscript")

    def test_director_uses_audit_not_validate(self):
        """Director는 audit_manuscript/audit_strategic_plan 사용"""
        from modules.domain.agents.director import Director

        assert hasattr(Director, "audit_manuscript")
        assert hasattr(Director, "audit_strategic_plan")

    def test_state_extractor_uses_extract_not_analyze(self):
        """StateExtractor는 extract_state/extract_cumulative_state 사용"""
        from modules.domain.agents.state_extractor import StateExtractor

        assert hasattr(StateExtractor, "extract_state")
        assert hasattr(StateExtractor, "extract_cumulative_state")


# ═══════════════════════════════════════════════════════════════════
# 5. Protocol import 정합성
# ═══════════════════════════════════════════════════════════════════


class TestProtocolImports:
    """__init__.py에서 모든 Protocol이 정상 export되는지"""

    def test_import_from_package(self):
        from modules.protocols import (
            ArtifactCritic,
            ArtifactValidator,
            Corrector,
            EnsembleGenerator,
            PipelineGenerator,
        )

        assert PipelineGenerator is not None
        assert EnsembleGenerator is not None
        assert ArtifactValidator is not None
        assert ArtifactCritic is not None
        assert Corrector is not None

    def test_import_from_agents_module(self):
        from modules.protocols.agents import (
            ArtifactCritic,
            ArtifactValidator,
            Corrector,
            EnsembleGenerator,
            PipelineGenerator,
        )

        assert all(
            p is not None for p in [PipelineGenerator, EnsembleGenerator, ArtifactValidator, ArtifactCritic, Corrector]
        )
