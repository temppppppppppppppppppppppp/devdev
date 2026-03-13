"""
[D-3] 문체 기반 Guard 래퍼 — StyleGuide에서 추출한 규칙으로 추가 검증.

기존 장르 Guard를 래핑하여:
1. 장르 검증 (기존 100% 유지)
2. + anti_ai_patterns 위반 감지 (MEDIUM)
3. + forbidden_expressions 위반 감지 (MEDIUM)
4. + 문장 길이 분포 편차 경고 (LOW)
"""

import logging
import re
from typing import Any

from .base_guard import BaseGuard

_logger = logging.getLogger(__name__)

_SENTENCE_SPLIT = re.compile(r"[.!?。]+\s*")


class StyleGuard(BaseGuard):
    """[D-3] StyleGuide 기반 추가 검증 래퍼."""

    def __init__(self, base_guard: BaseGuard, style_guide) -> None:
        super().__init__()
        self._base = base_guard
        self._sg = style_guide

        # base guard 속성 복사 (직접 접근 호환)
        self.FORBIDDEN_TERMS = base_guard.FORBIDDEN_TERMS
        self.ALLOWED_TERMS = base_guard.ALLOWED_TERMS
        self.MANDATORY_CONCEPTS = base_guard.MANDATORY_CONCEPTS

        self._anti_ai = [p for p in (style_guide.anti_ai_patterns or []) if len(p) >= 4]
        self._forbidden_expr = [e for e in (style_guide.forbidden_expressions or []) if len(e) >= 2]
        self._target_sentence_length = style_guide.sentence_length or "medium"

        _logger.info(
            "[D-3] StyleGuard 초기화: anti_ai=%d, forbidden=%d, target_len=%s",
            len(self._anti_ai),
            len(self._forbidden_expr),
            self._target_sentence_length,
        )

    def get_genre_name(self) -> str:
        base_name = self._base.get_genre_name()
        return f"{base_name}+Style"

    def get_v20_purism_prompt(self) -> str:
        return self._base.get_v20_purism_prompt()

    def get_impossible_actions(self, current_state: dict = None) -> list[dict]:
        return self._base.get_impossible_actions(current_state or {})

    def get_justification_patterns(self) -> list[str]:
        return self._base.get_justification_patterns()

    def get_hierarchy_rules(self) -> dict:
        return self._base.get_hierarchy_rules()

    def check_state_action_consistency(self, manuscript: str, current_state: dict) -> dict:
        return self._base.check_state_action_consistency(manuscript, current_state)

    # [V46.1] 권위/갈등/빌런 응답 검증 메서드 위임
    def get_authority_hierarchy(self) -> dict[str, Any]:
        return self._base.get_authority_hierarchy()

    def get_delegation_patterns(self) -> list[str]:
        return self._base.get_delegation_patterns()

    def check_authority_delegation(self, manuscript: str, context: dict[str, Any]) -> dict[str, Any]:
        return self._base.check_authority_delegation(manuscript, context)

    def get_hostile_action_types(self) -> list[str]:
        return self._base.get_hostile_action_types()

    def get_resolution_patterns(self) -> list[str]:
        return self._base.get_resolution_patterns()

    def check_unresolved_conflict(self, manuscript: str, karma_matrix: dict[str, Any], ep_num: int) -> dict[str, Any]:
        return self._base.check_unresolved_conflict(manuscript, karma_matrix, ep_num)

    def get_protagonist_victory_patterns(self) -> list[str]:
        return self._base.get_protagonist_victory_patterns()

    def get_villain_response_patterns(self) -> list[str]:
        return self._base.get_villain_response_patterns()

    def check_villain_response(
        self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]
    ) -> dict[str, Any]:
        return self._base.check_villain_response(manuscript, villain_context, recent_events)

    def __getattr__(self, name):
        """미구현 메서드는 base guard로 위임."""
        return getattr(self._base, name)

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """기존 장르 검증 + 문체 기반 추가 검증."""
        result = self._base.run_deep_validation(manuscript, current_state)
        violations = result.get("violations", [])
        warning_violations = list(result.get("warning_violations", []) or [])
        has_warning = bool(result.get("has_warning", False))
        warning_summary = str(result.get("warning_summary", "") or "")

        for pattern in self._anti_ai:
            if pattern in manuscript:
                violations.append(
                    {
                        "type": "style_anti_ai",
                        "severity": "MEDIUM",
                        "message": f"[Style] AI 패턴 감지: '{pattern}'",
                    }
                )

        for expr in self._forbidden_expr:
            if expr in manuscript:
                violations.append(
                    {
                        "type": "style_forbidden_expression",
                        "severity": "MEDIUM",
                        "message": f"[Style] 금지 표현 감지: '{expr}'",
                    }
                )

        length_warning = self._check_sentence_length_distribution(manuscript)
        if length_warning:
            violations.append(
                {
                    "type": "style_length_deviation",
                    "severity": "LOW",
                    "message": length_warning,
                }
            )

        has_critical = any(v.get("severity") in ("HIGH", "CRITICAL") for v in violations)
        summary_parts = [v.get("message", "") for v in violations[:5]]
        summary = "; ".join(summary_parts) if summary_parts else "검증 통과"
        feedback = ""
        if violations:
            feedback = f"[{self.get_genre_name()} Guard] {len(violations)}건 위반 발견: {summary}"

        return {
            "has_critical": has_critical,
            "has_warning": has_warning,
            "violations": violations,
            "warning_violations": warning_violations,
            "warning_summary": warning_summary,
            "summary": summary,
            "feedback": feedback,
        }

    def _check_sentence_length_distribution(self, manuscript: str) -> str:
        """문장 길이 분포가 StyleGuide 목표에서 크게 벗어나면 경고."""
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(manuscript) if len(s.strip()) >= 5]
        if len(sentences) < 10:
            return ""

        avg_len = sum(len(s) for s in sentences) / len(sentences)
        targets = {
            "short": (10, 25),
            "medium": (20, 45),
            "long": (35, 70),
        }
        target_range = targets.get(self._target_sentence_length, (20, 45))

        if avg_len < target_range[0] * 0.6:
            return f"[Style] 문장 평균 길이({avg_len:.0f}자)가 목표({self._target_sentence_length})보다 지나치게 짧음"
        if avg_len > target_range[1] * 1.5:
            return f"[Style] 문장 평균 길이({avg_len:.0f}자)가 목표({self._target_sentence_length})보다 지나치게 긺"

        return ""
