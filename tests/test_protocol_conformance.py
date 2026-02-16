"""[B-2] Protocol 적합성 테스트 — 구조적 서브타이핑 검증."""

from modules.protocols.agents import (
    ConstraintCompilerProtocol,
    DraftValidator,
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
