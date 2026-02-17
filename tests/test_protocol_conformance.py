"""[B-2 / B-3-2] Protocol 적합성 테스트 — 구조적 서브타이핑 검증."""

from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    ConstraintCompilerProtocol,
    Corrector,
    DraftValidator,
    EnsembleGenerator,
    PipelineGenerator,
    StateAggregator,
)


class TestDraftValidatorConformance:
    def test_arc_draft_validator_conforms(self):
        from modules.domain.agents.arc_draft_validator import ArcDraftValidator

        adv = ArcDraftValidator()
        assert isinstance(adv, DraftValidator)

    def test_manuscript_validator_conforms(self):
        from modules.domain.agents.manuscript_validator import ManuscriptValidator

        mv = ManuscriptValidator()
        assert isinstance(mv, DraftValidator)

    def test_manuscript_validator_validate_alias(self):
        from modules.domain.agents.manuscript_validator import ManuscriptValidator

        mv = ManuscriptValidator()
        assert hasattr(mv, "validate")
        assert mv.validate.__func__ is mv.validate_candidate.__func__


class TestConstraintCompilerConformance:
    def test_constraint_compiler_conforms(self):
        from modules.domain.agents.constraint_compiler import ConstraintCompiler

        cc = ConstraintCompiler()
        assert isinstance(cc, ConstraintCompilerProtocol)

    def test_blueprint_constraint_compiler_conforms(self):
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler

        bcc = BlueprintConstraintCompiler()
        assert isinstance(bcc, ConstraintCompilerProtocol)


class TestStateAggregatorConformance:
    def test_state_tracker_conforms(self):
        from modules.domain.agents.state_tracker import StateTracker

        st = StateTracker()
        assert isinstance(st, StateAggregator)

    def test_state_tracker_has_required_methods(self):
        from modules.domain.agents.state_tracker import StateTracker

        st = StateTracker()
        assert hasattr(st, "load_arc_design")
        assert hasattr(st, "validate_timeline")
        assert hasattr(st, "extract_all_state_changes")
        assert hasattr(st, "generate_arc_summary")
        assert callable(st.load_arc_design)
        assert callable(st.validate_timeline)


class TestExistingProtocolsStillWork:
    def test_pipeline_generator_still_conforms(self):
        from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
        from modules.protocols.agents import PipelineGenerator

        gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
        assert isinstance(gen, PipelineGenerator)

    def test_corrector_still_conforms(self):
        from modules.domain.agents.arc_corrector import ArcCorrector
        from modules.protocols.agents import Corrector

        ac = ArcCorrector.__new__(ArcCorrector)
        assert isinstance(ac, Corrector)


# ──────────────────────────────────────────────────────────────
# [B-3-2] EnsembleGenerator — instance 적합성
# ──────────────────────────────────────────────────────────────


class TestEnsembleGeneratorConformance:
    def test_arc_ensemble_conforms(self):
        from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator

        gen = ArcEnsembleGenerator.__new__(ArcEnsembleGenerator)
        assert isinstance(gen, EnsembleGenerator)

    def test_blueprint_ensemble_conforms(self):
        from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

        gen = BlueprintEnsembleGenerator.__new__(BlueprintEnsembleGenerator)
        assert isinstance(gen, EnsembleGenerator)

    def test_non_conforming(self):
        class NoGenerateEnsemble:
            def generate(self, **kwargs):
                return None, []

        assert not isinstance(NoGenerateEnsemble(), EnsembleGenerator)


# ──────────────────────────────────────────────────────────────
# [B-3-2] ArtifactValidator — instance 적합성
# ──────────────────────────────────────────────────────────────


class TestArtifactValidatorInstanceConformance:
    def test_unified_arc_validator_conforms(self):
        from modules.domain.agents.unified_arc_validator import UnifiedArcValidator

        uav = UnifiedArcValidator.__new__(UnifiedArcValidator)
        assert isinstance(uav, ArtifactValidator)

    def test_non_conforming(self):
        class NoValidate:
            def check(self, **kwargs):
                return {}

        assert not isinstance(NoValidate(), ArtifactValidator)


# ──────────────────────────────────────────────────────────────
# [B-3-2] ArtifactCritic — instance 적합성
# ──────────────────────────────────────────────────────────────


class TestArtifactCriticInstanceConformance:
    def test_arc_critic_conforms(self):
        from modules.domain.agents.arc_critic import ArcCritic

        ac = ArcCritic.__new__(ArcCritic)
        assert isinstance(ac, ArtifactCritic)

    def test_non_conforming(self):
        class NoCritique:
            def review(self, **kwargs):
                return {}

        assert not isinstance(NoCritique(), ArtifactCritic)


# ──────────────────────────────────────────────────────────────
# [B-3-2] PipelineGenerator — negative 추가
# ──────────────────────────────────────────────────────────────


class TestPipelineGeneratorNegative:
    def test_non_conforming(self):
        class NoGenerate:
            def create(self, **kwargs):
                return None, {}

        assert not isinstance(NoGenerate(), PipelineGenerator)


# ──────────────────────────────────────────────────────────────
# [B-3-2] Corrector — negative 추가
# ──────────────────────────────────────────────────────────────


class TestCorrectorNegative:
    def test_missing_can_correct(self):
        class OnlyCorrect:
            def correct(self, **kwargs):
                return None, {}

        assert not isinstance(OnlyCorrect(), Corrector)

    def test_missing_correct(self):
        class OnlyCanCorrect:
            def can_correct(self, **kwargs):
                return False, [], []

        assert not isinstance(OnlyCanCorrect(), Corrector)
