"""[B-3-3] 서브모듈 호스트 참조 패턴 검증.

12개 서브모듈이 올바른 호스트 참조 속성을 유지하는지 확인.
- StateTracker     → _npc, _financial, _plots     → self.tracker
- ContinuityInspector → _arc, _blueprint, _manuscript, _tracker → self._ci
- BlockingValidator → entity_checks, scene_checks, consistency_checks → self.host
- PreDirectorChecklist → narrative_checker, style_checker → self.host
"""


# ──────────────────────────────────────────────────────────────
# StateTracker — self.tracker
# ──────────────────────────────────────────────────────────────


class TestStateTrackerSubmodules:
    """StateTracker 3개 서브모듈이 self.tracker로 호스트를 참조."""

    def _make_tracker(self):
        from modules.domain.agents.state_tracker import StateTracker

        return StateTracker()

    def test_npc_has_tracker_ref(self):
        st = self._make_tracker()
        assert hasattr(st._npc, "tracker")
        assert st._npc.tracker is st

    def test_financial_has_tracker_ref(self):
        st = self._make_tracker()
        assert hasattr(st._financial, "tracker")
        assert st._financial.tracker is st

    def test_plots_has_tracker_ref(self):
        st = self._make_tracker()
        assert hasattr(st._plots, "tracker")
        assert st._plots.tracker is st


# ──────────────────────────────────────────────────────────────
# ContinuityInspector — self._ci
# ──────────────────────────────────────────────────────────────


class TestContinuityInspectorSubmodules:
    """ContinuityInspector 4개 서브모듈이 self._ci로 호스트를 참조.

    BaseAgent 서브클래스라 직접 인스턴스화 불가 → sentinel 호스트로 검증.
    """

    def test_arc_validator_has_ci_ref(self):
        from modules.domain.agents.continuity_arc import ContinuityArcValidator

        sentinel = object()
        sub = ContinuityArcValidator(sentinel)
        assert hasattr(sub, "_ci")
        assert sub._ci is sentinel

    def test_blueprint_validator_has_ci_ref(self):
        from modules.domain.agents.continuity_blueprint import ContinuityBlueprintValidator

        sentinel = object()
        sub = ContinuityBlueprintValidator(sentinel)
        assert hasattr(sub, "_ci")
        assert sub._ci is sentinel

    def test_manuscript_validator_has_ci_ref(self):
        from modules.domain.agents.continuity_manuscript import ContinuityManuscriptValidator

        sentinel = object()
        sub = ContinuityManuscriptValidator(sentinel)
        assert hasattr(sub, "_ci")
        assert sub._ci is sentinel

    def test_tracker_integration_has_ci_ref(self):
        from modules.domain.agents.continuity_tracker import ContinuityTrackerIntegration

        sentinel = object()
        sub = ContinuityTrackerIntegration(sentinel)
        assert hasattr(sub, "_ci")
        assert sub._ci is sentinel


# ──────────────────────────────────────────────────────────────
# BlockingValidator — self.host
# ──────────────────────────────────────────────────────────────


class TestBlockingValidatorSubmodules:
    """BlockingValidator 3개 서브모듈이 self.host로 호스트를 참조."""

    def _make_validator(self):
        from modules.validation.blocking_validator import BlockingValidator

        return BlockingValidator()

    def test_entity_checks_has_host_ref(self):
        bv = self._make_validator()
        assert hasattr(bv.entity_checks, "host")
        assert bv.entity_checks.host is bv

    def test_scene_checks_has_host_ref(self):
        bv = self._make_validator()
        assert hasattr(bv.scene_checks, "host")
        assert bv.scene_checks.host is bv

    def test_consistency_checks_has_host_ref(self):
        bv = self._make_validator()
        assert hasattr(bv.consistency_checks, "host")
        assert bv.consistency_checks.host is bv


# ──────────────────────────────────────────────────────────────
# PreDirectorChecklist — self.host
# ──────────────────────────────────────────────────────────────


class TestPreDirectorChecklistSubmodules:
    """PreDirectorChecklist 2개 서브모듈이 self.host로 호스트를 참조."""

    def _make_checklist(self):
        from modules.core.pre_director_checklist import PreDirectorChecklist

        return PreDirectorChecklist()

    def test_narrative_checker_has_host_ref(self):
        pdc = self._make_checklist()
        assert hasattr(pdc.narrative_checker, "host")
        assert pdc.narrative_checker.host is pdc

    def test_style_checker_has_host_ref(self):
        pdc = self._make_checklist()
        assert hasattr(pdc.style_checker, "host")
        assert pdc.style_checker.host is pdc
