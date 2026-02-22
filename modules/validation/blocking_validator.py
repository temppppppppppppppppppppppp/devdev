"""
[V0128] TIER 1: BLOCKING Validator
Python-based mandatory validation pipeline.

[R5-2a] Split into 3 submodules:
- entity_checks
- scene_checks
- consistency_checks
"""

import logging

from modules.validation.threshold_helper import _threshold as _threshold  # noqa: F401


class BlockingValidator:
    """Tier-1 blocking validator facade."""

    def __init__(self, context=None, enable_justification_checks=True) -> None:
        self.context = context
        self.enable_justification_checks = enable_justification_checks
        self._entity_checks = None
        self._scene_checks = None
        self._consistency_checks = None
        self._degraded_count = 0  # [I-C03] degraded 검증 누적 카운터
        if not enable_justification_checks:
            logging.getLogger(__name__).warning(
                "[V66.1] BlockingValidator: justification checks disabled - "
                "physical capability and authority checks will be skipped"
            )

    @property
    def entity_checks(self):
        if self._entity_checks is None:
            from modules.validation.blocking_validator_entity_checks import BlockingValidatorEntityChecks

            self._entity_checks = BlockingValidatorEntityChecks(self)
        return self._entity_checks

    @property
    def scene_checks(self):
        if self._scene_checks is None:
            from modules.validation.blocking_validator_scene_checks import BlockingValidatorSceneChecks

            self._scene_checks = BlockingValidatorSceneChecks(self)
        return self._scene_checks

    @property
    def consistency_checks(self):
        if self._consistency_checks is None:
            from modules.validation.blocking_validator_consistency_checks import BlockingValidatorConsistencyChecks

            self._consistency_checks = BlockingValidatorConsistencyChecks(self)
        return self._consistency_checks

    def validate(self, manuscript: str, validation_context: dict) -> dict:
        failures = []
        warnings = []

        dead_npc_check = self._check_dead_npc_resurrection(manuscript, validation_context)
        if not dead_npc_check["passed"]:
            failures.append(dead_npc_check)

        unowned_item_check = self._check_unowned_item_usage(manuscript, validation_context)
        if not unowned_item_check["passed"]:
            failures.append(unowned_item_check)

        destroyed_location_check = self._check_destroyed_location_visit(manuscript, validation_context)
        if not destroyed_location_check["passed"]:
            failures.append(destroyed_location_check)

        length_check = self._check_minimum_length(manuscript, validation_context)
        if not length_check["passed"]:
            failures.append(length_check)

        if validation_context.get("mode") == "MANUSCRIPT":
            scene_check = self._check_required_scenes(manuscript, validation_context)
            if not scene_check["passed"]:
                failures.append(scene_check)

        if validation_context.get("mode") == "MANUSCRIPT":
            scope_check = self._check_scope_overflow(manuscript, validation_context)
            if not scope_check["passed"]:
                failures.append(scope_check)

        damaged_item_check = self._check_damaged_item_usage(manuscript, validation_context)
        if not damaged_item_check["passed"]:
            failures.append(damaged_item_check)

        relationship_check = self._check_relationship_consistency(manuscript, validation_context)
        degraded_checks = []
        if relationship_check.get("degraded"):
            degraded_checks.append(relationship_check.get("check", "relationship_consistency"))
            logging.warning(
                f"[BlockingValidator] {relationship_check.get('check', 'relationship_consistency')} 검증 degraded: {relationship_check.get('error', '')}"
            )
            warnings.append(f"degraded: {relationship_check.get('check', 'relationship_consistency')}")
        if not relationship_check["passed"]:
            failures.append(relationship_check)

        information_check = self._check_information_consistency(manuscript, validation_context)
        if information_check.get("degraded"):
            degraded_checks.append(information_check.get("check", "information_consistency"))
            logging.warning(
                f"[BlockingValidator] {information_check.get('check', 'information_consistency')} 검증 degraded: {information_check.get('error', '')}"
            )
            warnings.append(f"degraded: {information_check.get('check', 'information_consistency')}")
        if not information_check["passed"]:
            failures.append(information_check)

        # [I-C03] 모든 일관성 검증이 degraded면 경고
        if len(degraded_checks) >= 2:
            self._degraded_count += 1
            logging.warning(
                f"[C-03] ALL consistency checks degraded ({self._degraded_count}회 누적): {degraded_checks}"
            )

        if self.enable_justification_checks:
            physical_check = self._check_physical_capability(manuscript, validation_context)
            if not physical_check["passed"]:
                failures.append(physical_check)

        if self.enable_justification_checks:
            authority_check = self._check_authority_exercise(manuscript, validation_context)
            if not authority_check["passed"]:
                failures.append(authority_check)

        if validation_context.get("mode") == "MANUSCRIPT":
            scene_completeness_check = self._check_scene_completeness(manuscript, validation_context)
            if not scene_completeness_check["passed"]:
                failures.append(scene_completeness_check)

        if validation_context.get("mode") == "MANUSCRIPT":
            cliffhanger_check = self._check_cliffhanger_ending(manuscript, validation_context)
            if not cliffhanger_check["passed"]:
                failures.append(cliffhanger_check)

        result = {
            "tier": "BLOCKING",
            "passed": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "message": f"REJECT - 차단 검증 실패 ({len(failures)}건)" if failures else "PASS",
            "failure_count": len(failures),
        }
        if degraded_checks:
            result["degraded_checks"] = degraded_checks
        return result

    # Backward-compatible wrappers for existing tests/callers.
    def _check_dead_npc_resurrection(self, manuscript: str, context: dict) -> dict:
        return self.entity_checks._check_dead_npc_resurrection(manuscript, context)

    def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
        return self.entity_checks._check_unowned_item_usage(manuscript, context)

    def _check_damaged_item_usage(self, manuscript: str, context: dict) -> dict:
        return self.entity_checks._check_damaged_item_usage(manuscript, context)

    def _check_destroyed_location_visit(self, manuscript: str, context: dict) -> dict:
        return self.entity_checks._check_destroyed_location_visit(manuscript, context)

    def _check_minimum_length(self, manuscript: str, context: dict) -> dict:
        return self.scene_checks._check_minimum_length(manuscript, context)

    def _check_required_scenes(self, manuscript: str, context: dict) -> dict:
        return self.scene_checks._check_required_scenes(manuscript, context)

    def _check_scope_overflow(self, manuscript: str, context: dict) -> dict:
        return self.scene_checks._check_scope_overflow(manuscript, context)

    def _check_physical_capability(self, manuscript: str, context: dict) -> dict:
        return self.consistency_checks._check_physical_capability(manuscript, context)

    def _check_authority_exercise(self, manuscript: str, context: dict) -> dict:
        return self.consistency_checks._check_authority_exercise(manuscript, context)

    def _check_relationship_consistency(self, manuscript: str, context: dict) -> dict:
        try:
            return self.consistency_checks._check_relationship_consistency(manuscript, context)
        except (ImportError, TypeError, AttributeError):
            raise  # [V-I4] 프로그래밍 오류는 조기 발견을 위해 re-raise
        except (ValueError, KeyError, RuntimeError) as e:
            logging.warning(f"[C-3] relationship consistency check failed (degraded): {e}")
            return {"check": "relationship_consistency", "passed": True, "degraded": True, "error": str(e)}

    def _check_information_consistency(self, manuscript: str, context: dict) -> dict:
        try:
            return self.consistency_checks._check_information_consistency(manuscript, context)
        except (ImportError, TypeError, AttributeError):
            raise  # [V-I4] 프로그래밍 오류는 조기 발견을 위해 re-raise
        except (ValueError, KeyError, RuntimeError) as e:
            logging.warning(f"[C-3] information consistency check failed (degraded): {e}")
            return {"check": "information_consistency", "passed": True, "degraded": True, "error": str(e)}

    def _check_scene_completeness(self, manuscript: str, context: dict) -> dict:
        return self.scene_checks._check_scene_completeness(manuscript, context)

    def _check_cliffhanger_ending(self, manuscript: str, context: dict) -> dict:
        return self.scene_checks._check_cliffhanger_ending(manuscript, context)

    def _extract_keywords(self, text: str, max_keywords: int = 3) -> list[str]:
        return self.consistency_checks._extract_keywords(text, max_keywords=max_keywords)

    def _calculate_cliffhanger_strength(
        self, ending_text: str, matched_patterns: list[str], blueprint_hint: str
    ) -> int:
        return self.scene_checks._calculate_cliffhanger_strength(ending_text, matched_patterns, blueprint_hint)

    def _get_strength_grade(self, score: int) -> str:
        return self.scene_checks._get_strength_grade(score)
