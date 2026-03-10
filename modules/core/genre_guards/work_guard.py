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
        _raw_config = self._load_yaml(yaml_path)
        self._config = _raw_config if isinstance(_raw_config, dict) else {}

        # base guard 속성 병합
        def _ensure_str(v):
            return str(v) if isinstance(v, dict) else v

        base_forbidden_set = set(base_guard.FORBIDDEN_TERMS)
        extra_forbidden = {_ensure_str(x) for x in self._config.get("extra_forbidden_terms", [])}
        extra_allowed = {_ensure_str(x) for x in self._config.get("extra_allowed_terms", [])}

        self.FORBIDDEN_TERMS = [
            t for t in list(base_guard.FORBIDDEN_TERMS) + list(extra_forbidden) if t not in extra_allowed
        ]
        self.ALLOWED_TERMS = list(set(base_guard.ALLOWED_TERMS) | extra_allowed)
        self.MANDATORY_CONCEPTS = list(
            set(base_guard.MANDATORY_CONCEPTS)
            | {_ensure_str(x) for x in self._config.get("extra_mandatory_concepts", [])}
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
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
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

    @staticmethod
    def _extract_age_bounds(constraint: str) -> tuple[int | None, int | None]:
        range_match = re.search(r"(\d{1,2})\s*[~\-]\s*(\d{1,2})\s*세", constraint)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))

        lower_match = re.search(r"(\d{1,2})\s*세\s*이상", constraint)
        upper_match = re.search(r"(\d{1,2})\s*세\s*이하", constraint)
        lower = int(lower_match.group(1)) if lower_match else None
        upper = int(upper_match.group(1)) if upper_match else None
        return lower, upper

    @staticmethod
    def _find_character_ages(manuscript: str, char_name: str) -> list[int]:
        patterns = [
            rf"{re.escape(char_name)}[^\n]{{0,24}}?(\d{{1,2}})세",
            rf"(\d{{1,2}})세[^\n]{{0,24}}?{re.escape(char_name)}",
        ]
        ages: list[int] = []
        for pattern in patterns:
            for match in re.finditer(pattern, manuscript):
                try:
                    ages.append(int(match.group(1)))
                except (TypeError, ValueError):
                    continue
        return ages

    def _check_character_constraints(self, manuscript: str, current_state: dict[str, Any] | None) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        if not isinstance(self._char_constraints, dict) or not self._char_constraints:
            return warnings

        current_state = current_state or {}
        protagonist_config = current_state.get("protagonist_config", {})
        protagonist_name = str(current_state.get("protagonist_name", "") or "").strip()
        incarnation_type = str(protagonist_config.get("incarnation_type", "") or "").strip()

        for char_name, constraints in self._char_constraints.items():
            name = str(char_name or "").strip()
            if not name or name not in manuscript or not isinstance(constraints, list):
                continue

            for raw_constraint in constraints:
                constraint = str(raw_constraint or "").strip()
                if not constraint:
                    continue

                lower_age, upper_age = self._extract_age_bounds(constraint)
                if lower_age is not None or upper_age is not None:
                    is_protagonist_constraint = name in {"주인공", protagonist_name} if protagonist_name else name == "주인공"
                    if is_protagonist_constraint and incarnation_type in {"빙의자", "환생자", "회귀자"}:
                        continue

                    for age in self._find_character_ages(manuscript, name):
                        if (lower_age is not None and age < lower_age) or (upper_age is not None and age > upper_age):
                            warnings.append(
                                {
                                    "type": "work_character_constraint",
                                    "severity": "WARNING",
                                    "character": name,
                                    "constraint": constraint,
                                    "message": f"[Work] 캐릭터 제약 확인 필요: {name} 나이 {age}세 ↔ {constraint}",
                                }
                            )
                            break
                    continue

                if "장님" in constraint:
                    if re.search(rf"{re.escape(name)}[^\n]{{0,24}}(봤|바라봤|응시|시선을|눈으로)", manuscript):
                        warnings.append(
                            {
                                "type": "work_character_constraint",
                                "severity": "WARNING",
                                "character": name,
                                "constraint": constraint,
                                "message": f"[Work] 캐릭터 제약 확인 필요: {name}에게 시각 기반 묘사 가능성 ({constraint})",
                            }
                        )
                    continue

                if "왼손잡이" in constraint:
                    if re.search(rf"{re.escape(name)}[^\n]{{0,24}}오른손", manuscript):
                        warnings.append(
                            {
                                "type": "work_character_constraint",
                                "severity": "WARNING",
                                "character": name,
                                "constraint": constraint,
                                "message": f"[Work] 캐릭터 제약 확인 필요: {name} 오른손 사용 묘사 감지 ({constraint})",
                            }
                        )
                    continue

                if "검만 사용" in constraint:
                    if re.search(rf"{re.escape(name)}[^\n]{{0,24}}(창|도|활|총|망치|도끼|단검)", manuscript):
                        warnings.append(
                            {
                                "type": "work_character_constraint",
                                "severity": "WARNING",
                                "character": name,
                                "constraint": constraint,
                                "message": f"[Work] 캐릭터 제약 확인 필요: {name} 검 외 무기 사용 묘사 감지 ({constraint})",
                            }
                        )
                    continue
        return warnings

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """기존 장르 검증 + 추가 금기어 + extra_forbidden_patterns regex 검사."""
        result = self._base.run_deep_validation(manuscript, current_state)
        violations = result.get("violations", [])
        warning_violations = list(result.get("warning_violations", []) or [])

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

        warning_violations.extend(self._check_character_constraints(manuscript, current_state))

        has_critical = any(v.get("severity") in ("HIGH", "CRITICAL") for v in violations)
        summary_parts = [v.get("message", "") for v in violations[:5]]
        summary = "; ".join(summary_parts) if summary_parts else "검증 통과"
        warning_parts = [v.get("message", "") for v in warning_violations[:5]]
        warning_summary = "; ".join(warning_parts) if warning_parts else ""
        feedback = ""
        if violations:
            feedback = f"[{self.get_genre_name()} Guard] {len(violations)}건 위반 발견: {summary}"

        return {
            "has_critical": has_critical,
            "has_warning": bool(warning_violations),
            "violations": violations,
            "warning_violations": warning_violations,
            "summary": summary,
            "warning_summary": warning_summary,
            "feedback": feedback,
        }
