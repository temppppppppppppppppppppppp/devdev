"""
[WorkGuard] 작품별 커스텀 규칙 Guard 래퍼.

프로젝트별 work_guard.yaml로 작품 전용 규칙을 선언하고,
장르 Guard 위에 추가 적용한다.

Guard 합성 체인: GenreGuard → WorkGuard → StyleGuard
"""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .base_guard import BaseGuard

_logger = logging.getLogger(__name__)


class WorkGuard(BaseGuard):
    """작품별 work_guard.yaml 기반 추가 검증 래퍼."""

    def __init__(self, base_guard: BaseGuard, yaml_path: Path | str) -> None:
        super().__init__()
        self._base = base_guard
        self._config = self._load_yaml(yaml_path)

        # base guard 속성 병합
        base_forbidden_set = set(base_guard.FORBIDDEN_TERMS)
        extra_forbidden = set(self._config.get("extra_forbidden_terms", []))
        extra_allowed = set(self._config.get("extra_allowed_terms", []))

        self.FORBIDDEN_TERMS = [
            t for t in list(base_guard.FORBIDDEN_TERMS) + list(extra_forbidden) if t not in extra_allowed
        ]
        self.ALLOWED_TERMS = list(set(base_guard.ALLOWED_TERMS) | extra_allowed)
        self.MANDATORY_CONCEPTS = list(
            set(base_guard.MANDATORY_CONCEPTS) | set(self._config.get("extra_mandatory_concepts", []))
        )

        # run_deep_validation에서 추가로 검사할 금기어 (base에 없는 것만)
        self._added_forbidden = [t for t in self.FORBIDDEN_TERMS if t not in base_forbidden_set]

        # 추가 검증용 데이터
        self._extra_patterns = self._config.get("extra_forbidden_patterns", [])
        self._custom_rules = self._config.get("custom_rules", [])
        self._char_constraints = self._config.get("character_constraints", {})

        _logger.info(
            "[WorkGuard] 초기화: +forbidden=%d, +allowed=%d, +patterns=%d, custom_rules=%d, char_constraints=%d",
            len(extra_forbidden),
            len(extra_allowed),
            len(self._extra_patterns),
            len(self._custom_rules),
            len(self._char_constraints),
        )

    @staticmethod
    def _load_yaml(yaml_path: Path | str) -> dict:
        path = Path(yaml_path)
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            _logger.warning("[WorkGuard] YAML 로드 실패: %s", path)
            return {}

    # ── 위임 메서드 (StyleGuard 패턴 동일) ────────────────────

    def get_genre_name(self) -> str:
        return f"{self._base.get_genre_name()}+Work"

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

    # ── 핵심 오버라이드 ────────────────────────────────────────

    def get_v20_purism_prompt(self) -> str:
        """기존 프롬프트 + 작품 전용 규칙/캐릭터 제약 섹션 추가."""
        base_prompt = self._base.get_v20_purism_prompt()

        sections = []

        if self._custom_rules:
            lines = "\n".join(f"- {r}" for r in self._custom_rules)
            sections.append(f"[작품 전용 규칙]\n{lines}")

        if self._char_constraints:
            char_lines = []
            for char_name, constraints in self._char_constraints.items():
                if isinstance(constraints, list):
                    for c in constraints:
                        char_lines.append(f"- {char_name}: {c}")
            if char_lines:
                sections.append("[캐릭터별 제약]\n" + "\n".join(char_lines))

        if not sections:
            return base_prompt

        return base_prompt + "\n\n" + "\n\n".join(sections)

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """기존 장르 검증 + 추가 금기어 + extra_forbidden_patterns regex 검사."""
        result = self._base.run_deep_validation(manuscript, current_state)
        violations = result.get("violations", [])

        # 추가 금기어 검사 (base에서 이미 체크한 것 외)
        for term in self._added_forbidden:
            if term in manuscript:
                violations.append(
                    {
                        "type": "forbidden_term",
                        "term": term,
                        "severity": "HIGH",
                        "message": f"[Work] 작품 금기어 '{term}' 발견",
                    }
                )

        for entry in self._extra_patterns:
            if not isinstance(entry, dict):
                continue
            pattern = entry.get("pattern", "")
            reason = entry.get("reason", "작품 규칙 위반")
            if not pattern:
                continue
            try:
                if re.search(pattern, manuscript):
                    violations.append(
                        {
                            "type": "work_forbidden_pattern",
                            "severity": "HIGH",
                            "message": f"[Work] {reason} (패턴: {pattern})",
                        }
                    )
            except re.error:
                _logger.warning("[WorkGuard] 잘못된 정규식: %s", pattern)

        has_critical = any(v.get("severity") in ("HIGH", "CRITICAL") for v in violations)
        summary_parts = [v.get("message", "") for v in violations[:5]]
        summary = "; ".join(summary_parts) if summary_parts else "검증 통과"
        feedback = ""
        if violations:
            feedback = f"[{self.get_genre_name()} Guard] {len(violations)}건 위반 발견: {summary}"

        return {
            "has_critical": has_critical,
            "violations": violations,
            "summary": summary,
            "feedback": feedback,
        }
