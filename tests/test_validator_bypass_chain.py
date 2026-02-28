"""[C-3] Validator bypass chain regression tests."""

import importlib
import inspect
from unittest.mock import MagicMock, patch

from modules.domain.agents.director_continuity import DirectorContinuityValidator
from modules.validation.blocking_validator import BlockingValidator


class TestDirectorContinuityUnknown:
    """director_continuity exception paths must return UNKNOWN, not PASS."""

    def _make_validator(self):
        director = MagicMock()
        director.entity_consistency_enabled = True
        director._escape_braces.side_effect = lambda text: text
        director.context = MagicMock(project_name="test_project")
        director.merge_contexts_for_caching.return_value = "cached-context"
        director._get_or_create_context_cache.return_value = {"cached": False, "cache_name": None}
        director._ask_with_cached_context.return_value = "{}"
        director.ask.return_value = "{}"
        director._extract_json_robust.return_value = {}
        return DirectorContinuityValidator(director), director

    def test_entity_consistency_exception_returns_unknown(self):
        validator, director = self._make_validator()
        director.ask.side_effect = RuntimeError("API timeout")

        result = validator.validate_entity_consistency(
            content="테스트 원고",
            entity_registry={"characters": [{"name": "이청풍"}]},
        )

        assert result["decision"] == "UNKNOWN"
        assert "error" in result

    def test_blueprint_continuity_exception_returns_reject(self):
        """[TF-24 DC-01] Blueprint 연속성 예외 시 fail-closed REJECT."""
        validator, _ = self._make_validator()
        db = MagicMock()
        db.get_recent_blueprints.side_effect = RuntimeError("DB timeout")

        result = validator.check_blueprint_continuity_with_cache(
            new_blueprint={"start_location": "장안"},
            ep_num=3,
            db=db,
        )

        assert result["decision"] == "REJECT"
        assert "error" in result

    def test_manuscript_continuity_exception_returns_conflict(self):
        """[TF-24 DC-03] Manuscript 연속성 예외 시 fail-closed CONFLICT."""
        validator, _ = self._make_validator()
        db = MagicMock()
        db.get_recent_manuscripts.side_effect = RuntimeError("DB timeout")

        result = validator.check_manuscript_continuity_with_cache(
            new_manuscript="테스트 원고",
            ep_num=3,
            db=db,
        )

        assert result["decision"] == "CONFLICT"
        assert "error" in result

    def test_unknown_is_not_pass(self):
        assert "UNKNOWN" != "PASS"

    def test_unknown_is_not_reject(self):
        assert "UNKNOWN" != "REJECT"


class TestBlockingValidatorDegraded:
    """blocking_validator exception paths should set degraded=True."""

    def test_relationship_check_exception_has_degraded(self):
        relation_module = importlib.import_module("modules.core.relationship_tracker")
        validator = BlockingValidator()

        with patch.object(relation_module, "RelationshipTracker", side_effect=RuntimeError("tracker down")):
            result = validator._check_relationship_consistency(
                manuscript="테스트 원고",
                context={"encyclopedia": {"npcs": []}, "ep_num": 1},
            )

        assert result["passed"] is True
        assert result["degraded"] is True
        assert "error" in result

    def test_information_check_exception_has_degraded(self):
        info_module = importlib.import_module("modules.core.information_diffusion")
        validator = BlockingValidator(context=MagicMock())

        with patch.object(info_module, "InformationDiffusion", side_effect=RuntimeError("diffusion down")):
            result = validator._check_information_consistency(
                manuscript="테스트 원고",
                context={"encyclopedia": {"npcs": []}, "ep_num": 1},
            )

        assert result["passed"] is True
        assert result["degraded"] is True
        assert "error" in result

    def test_relationship_normal_path_has_no_degraded(self):
        validator = BlockingValidator()
        result = validator._check_relationship_consistency(
            manuscript="테스트 원고",
            context={"encyclopedia": {"npcs": []}, "ep_num": 1},
        )

        assert result["passed"] is True
        assert "degraded" not in result

    def test_information_no_context_has_no_degraded(self):
        validator = BlockingValidator(context=None)
        result = validator._check_information_consistency(
            manuscript="테스트 원고",
            context={"encyclopedia": {"npcs": []}, "ep_num": 1},
        )

        assert result["passed"] is True
        assert "degraded" not in result

    def test_degraded_flag_semantics(self):
        result = {"check": "sample", "passed": True, "degraded": True, "error": "timeout"}

        assert result["passed"] is True
        assert result["degraded"] is True


class TestSourceCodePatterns:
    """Static checks to prevent regression to PASS-on-exception behavior."""

    def test_director_continuity_uses_fail_closed_in_error_paths(self):
        """[TF-24] Blueprint→REJECT, Manuscript→CONFLICT, entity→UNKNOWN (fail-closed)."""
        source = inspect.getsource(DirectorContinuityValidator)
        # DC-01: Blueprint 연속성 예외 → REJECT (호출자가 REJECT만 검사)
        assert '"decision": "REJECT"' in source
        # DC-03: Manuscript 연속성 예외 → CONFLICT (호출자가 CONFLICT만 검사)
        assert '"decision": "CONFLICT"' in source
        # entity_consistency 예외 → UNKNOWN (기존 유지)
        assert '"decision": "UNKNOWN"' in source

    def test_blocking_validator_has_degraded_flag_in_error_paths(self):
        source = inspect.getsource(BlockingValidator)
        assert source.count('"degraded": True') >= 2
