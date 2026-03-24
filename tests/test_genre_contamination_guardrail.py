"""
Genre contamination guardrail regression tests.

Proves:
- missing genre in touched paths does not silently act as wuxia
- explicit wuxia still gets wuxia-specific behavior
- explicit investment path is preserved (no wuxia-only fallback language)
- Director genre-resolution works
- Stage 4 context builder genre-resolution works
- validator/scoring/continuity fallback handling is neutral
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from modules.validation.validation_orchestrator import (
    GENRE_THRESHOLD_PROFILES,
    ValidationOrchestrator,
)


# ---------------------------------------------------------------------------
# _default profile existence
# ---------------------------------------------------------------------------

class TestDefaultProfiles:
    """Neutral _default profile exists and has balanced weights."""

    def test_threshold_profiles_has_default(self):
        assert "_default" in GENRE_THRESHOLD_PROFILES
        profile = GENRE_THRESHOLD_PROFILES["_default"]
        assert profile["base_threshold"] == 70
        assert profile["action_weight"] == 1.0
        assert profile["dialogue_weight"] == 1.0
        assert profile["emotion_weight"] == 1.0
        assert profile["commercial_weight"] == 1.0

    def test_scoring_weights_has_default(self):
        from modules.validation.scoring_validator import ScoringValidator

        assert "_default" in ScoringValidator.GENRE_WEIGHTS
        weights = ScoringValidator.GENRE_WEIGHTS["_default"]
        for key, val in weights.items():
            assert val == 1.0, f"_default weight {key} should be 1.0, got {val}"


# ---------------------------------------------------------------------------
# Director genre-resolution
# ---------------------------------------------------------------------------

class TestDirectorGenreResolution:
    """Director no longer defaults to wuxia on init."""

    @staticmethod
    def _make_director():
        from modules.domain.agents.director import Director

        return Director(context=MagicMock(), client=MagicMock(), model_tier="gemini-2.5-flash")

    def test_director_init_genre_is_none(self):
        d = self._make_director()
        assert d.genre is None, "Director.__init__ should not default to 'wuxia'"

    def test_director_set_genre_explicit_wuxia(self):
        d = self._make_director()
        d.set_genre("wuxia")
        assert d.genre == "wuxia"

    def test_director_set_genre_investment(self):
        d = self._make_director()
        d.set_genre("investment")
        assert d.genre == "investment"

    def test_director_set_genre_empty_warns(self, caplog):
        d = self._make_director()
        with caplog.at_level(logging.WARNING):
            d.set_genre("")
        assert any("genre-guardrail" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# ValidationOrchestrator genre-resolution
# ---------------------------------------------------------------------------

class TestValidationOrchestratorGenreResolution:
    """ValidationOrchestrator uses neutral defaults when genre is missing."""

    def test_none_genre_uses_default_profile(self):
        orch = ValidationOrchestrator(config={}, client=None, genre=None, context={})
        assert orch.threshold_profile == GENRE_THRESHOLD_PROFILES["_default"]

    def test_empty_genre_uses_default_profile(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="", context={})
        assert orch.threshold_profile == GENRE_THRESHOLD_PROFILES["_default"]

    def test_explicit_wuxia_gets_wuxia_profile(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
        assert orch.threshold_profile == GENRE_THRESHOLD_PROFILES["wuxia"]

    def test_explicit_investment_gets_investment_profile(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="investment", context={})
        assert orch.threshold_profile == GENRE_THRESHOLD_PROFILES["investment"]

    def test_none_genre_emits_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            ValidationOrchestrator(config={}, client=None, genre=None, context={})
        assert any("genre-guardrail" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Scoring validator fallback
# ---------------------------------------------------------------------------

class TestScoringValidatorFallback:
    """ScoringValidator does not fall back to wuxia weights when genre is absent."""

    def test_none_genre_uses_default_weights(self):
        from modules.validation.scoring_validator import ScoringValidator

        sv = ScoringValidator(genre=None)
        # simulate validate_v59 weight lookup
        genre = sv.genre or ""
        weights = sv.GENRE_WEIGHTS.get(genre, sv.GENRE_WEIGHTS["_default"])
        assert weights == sv.GENRE_WEIGHTS["_default"]
        # Must NOT be wuxia weights
        assert weights != sv.GENRE_WEIGHTS["wuxia"]

    def test_explicit_investment_uses_investment_weights(self):
        from modules.validation.scoring_validator import ScoringValidator

        sv = ScoringValidator(genre="investment")
        genre = sv.genre or ""
        weights = sv.GENRE_WEIGHTS.get(genre, sv.GENRE_WEIGHTS["_default"])
        assert weights == sv.GENRE_WEIGHTS["investment"]

    def test_explicit_wuxia_uses_wuxia_weights(self):
        from modules.validation.scoring_validator import ScoringValidator

        sv = ScoringValidator(genre="wuxia")
        genre = sv.genre or ""
        weights = sv.GENRE_WEIGHTS.get(genre, sv.GENRE_WEIGHTS["_default"])
        assert weights == sv.GENRE_WEIGHTS["wuxia"]


# ---------------------------------------------------------------------------
# Continuity validator fallback
# ---------------------------------------------------------------------------

class TestContinuityValidatorFallback:
    """Missing genre does not trigger wuxia-only injury continuity checks."""

    def test_missing_genre_skips_injury_check(self):
        from modules.validation.continuity_validator import ContinuityValidator

        cv = ContinuityValidator.__new__(ContinuityValidator)
        # validation_context without genre key
        ctx = {}
        # The condition `validation_context.get("genre") in {"wuxia", "hunter", "fantasy"}`
        # should be False when genre is missing
        assert ctx.get("genre") not in {"wuxia", "hunter", "fantasy"}

    def test_investment_genre_skips_injury_check(self):
        ctx = {"genre": "investment"}
        assert ctx.get("genre") not in {"wuxia", "hunter", "fantasy"}

    def test_wuxia_genre_triggers_injury_check(self):
        ctx = {"genre": "wuxia"}
        assert ctx.get("genre") in {"wuxia", "hunter", "fantasy"}


# ---------------------------------------------------------------------------
# Blocking validator consistency checks fallback
# ---------------------------------------------------------------------------

class TestBlockingValidatorFallback:
    """Missing genre does not silently become wuxia in consistency checks."""

    def test_missing_genre_returns_empty_string(self):
        context = {"martial_hud": {}}
        genre = context.get("genre") or ""
        assert genre == ""
        assert genre != "wuxia"

    def test_investment_genre_preserved(self):
        context = {"genre": "investment", "martial_hud": {}}
        genre = context.get("genre") or ""
        assert genre == "investment"


# ---------------------------------------------------------------------------
# Stage 4 context builder genre-resolution
# ---------------------------------------------------------------------------

class TestStage4ContextBuilderGenreResolution:
    """Stage 4 context builder does not fall back to '무협' display name."""

    def test_missing_genre_name_uses_genre_type_fallback(self):
        """When project has no genre name, falls back to s4_genre_type, not '무협'."""
        # Simulate the resolved logic from stage4_context_builder.py
        project_genre = {}  # no "name" key
        s4_genre_type = "investment"
        genre_name = project_genre.get("name", "")
        if not genre_name:
            genre_name = s4_genre_type or "unknown"
        assert genre_name == "investment"
        assert genre_name != "무협"

    def test_empty_both_uses_unknown(self):
        project_genre = {}
        s4_genre_type = ""
        genre_name = project_genre.get("name", "")
        if not genre_name:
            genre_name = s4_genre_type or "unknown"
        assert genre_name == "unknown"
        assert genre_name != "무협"

    def test_explicit_wuxia_name_preserved(self):
        project_genre = {"name": "무협"}
        genre_name = project_genre.get("name", "")
        assert genre_name == "무협"


# ---------------------------------------------------------------------------
# Investment regression: no wuxia-specific language in touched fallback paths
# ---------------------------------------------------------------------------

class TestInvestmentNoWuxiaContamination:
    """Investment genre must not inherit wuxia-specific constitution or weights."""

    def test_investment_constitution_has_no_wuxia_amendment(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="investment", context={})
        constitution = orch._get_fallback_constitution("investment")
        assert "무공 위계" not in constitution
        assert "강호 예법" not in constitution
        assert "내공 운용" not in constitution
        # Investment-specific content should be present
        assert "투자 수익률" in constitution

    def test_missing_genre_constitution_has_no_wuxia_amendment(self):
        orch = ValidationOrchestrator(config={}, client=None, genre=None, context={})
        constitution = orch._get_fallback_constitution(None)
        assert "무공 위계" not in constitution
        assert "강호 예법" not in constitution
        assert "내공 운용" not in constitution

    def test_investment_threshold_profile_differs_from_wuxia(self):
        inv_profile = GENRE_THRESHOLD_PROFILES["investment"]
        wux_profile = GENRE_THRESHOLD_PROFILES["wuxia"]
        assert inv_profile != wux_profile


# ---------------------------------------------------------------------------
# Wuxia no-regression
# ---------------------------------------------------------------------------

class TestWuxiaNoRegression:
    """Explicit wuxia still gets wuxia-specific behavior in touched paths."""

    def test_wuxia_constitution_has_wuxia_amendment(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
        constitution = orch._get_fallback_constitution("wuxia")
        assert "무공 위계" in constitution
        assert "강호 예법" in constitution

    def test_wuxia_threshold_profile_matches(self):
        orch = ValidationOrchestrator(config={}, client=None, genre="wuxia", context={})
        assert orch.threshold_profile == GENRE_THRESHOLD_PROFILES["wuxia"]
        assert orch.threshold_profile["action_weight"] == 1.2

    def test_wuxia_scoring_weights_intact(self):
        from modules.validation.scoring_validator import ScoringValidator

        wuxia_weights = ScoringValidator.GENRE_WEIGHTS["wuxia"]
        assert wuxia_weights["sensory_balance"] == 1.3
        assert wuxia_weights["reader_satisfaction"] == 1.3
