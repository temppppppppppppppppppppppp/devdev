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


class WorkGuardConfigError(ValueError):
    """Raised when a present work_guard.yaml cannot be trusted."""


_ROOT_SCALAR_LIST_FIELDS = (
    "extra_forbidden_terms",
    "extra_allowed_terms",
    "extra_mandatory_concepts",
    "custom_rules",
)
_WORK_IDENTITY_SCALAR_LIST_FIELDS = (
    "tracking_slots",
    "mandatory_scene_engines",
    "forbidden_flattenings",
    "mandatory_lexicon",
    "protagonist_weapon",
    "business_axes",
    "control_axes",
)
_PROTAGONIST_EVAL_SCALAR_LIST_FIELDS = (
    "admiration_axes",
    "forbidden_praise_patterns",
    "observer_tiers",
    "evaluation_thresholds",
)


def _raise_config_error(path: Path, message: str) -> None:
    raise WorkGuardConfigError(f"{path}: {message}")


def _validate_scalar_list_field(value: Any, *, path: Path, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        _raise_config_error(path, f"'{field_name}' must be a list")
    for idx, item in enumerate(value):
        if isinstance(item, (dict, list)):
            _raise_config_error(path, f"'{field_name}[{idx}]' must be a scalar value")


def _validate_list_field(value: Any, *, path: Path, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        _raise_config_error(path, f"'{field_name}' must be a list")


def _validate_character_constraints(value: Any, *, path: Path) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        _raise_config_error(path, "'character_constraints' must be a mapping")
    for key, constraints in value.items():
        if not isinstance(constraints, list):
            _raise_config_error(path, f"'character_constraints.{key}' must be a list")
        for idx, item in enumerate(constraints):
            if isinstance(item, (dict, list)):
                _raise_config_error(path, f"'character_constraints.{key}[{idx}]' must be a scalar value")


def validate_work_guard_config(data: Any, yaml_path: Path | str) -> dict[str, Any]:
    path = Path(yaml_path)
    if data is None:
        return {}
    if not isinstance(data, dict):
        _raise_config_error(path, "top-level YAML must be a mapping")

    for field_name in _ROOT_SCALAR_LIST_FIELDS:
        _validate_scalar_list_field(data.get(field_name), path=path, field_name=field_name)

    _validate_list_field(data.get("extra_forbidden_patterns"), path=path, field_name="extra_forbidden_patterns")
    _validate_character_constraints(data.get("character_constraints"), path=path)

    work_identity = data.get("work_identity")
    if work_identity is not None:
        if not isinstance(work_identity, dict):
            _raise_config_error(path, "'work_identity' must be a mapping")
        for field_name in _WORK_IDENTITY_SCALAR_LIST_FIELDS:
            _validate_scalar_list_field(
                work_identity.get(field_name),
                path=path,
                field_name=f"work_identity.{field_name}",
            )
        _validate_list_field(
            work_identity.get("registry_profiles"),
            path=path,
            field_name="work_identity.registry_profiles",
        )
        _validate_list_field(
            work_identity.get("role_fit_constraints"),
            path=path,
            field_name="work_identity.role_fit_constraints",
        )

        protagonist_eval = work_identity.get("protagonist_evaluation")
        if protagonist_eval is not None:
            if not isinstance(protagonist_eval, dict):
                _raise_config_error(path, "'work_identity.protagonist_evaluation' must be a mapping")
            for field_name in _PROTAGONIST_EVAL_SCALAR_LIST_FIELDS:
                _validate_scalar_list_field(
                    protagonist_eval.get(field_name),
                    path=path,
                    field_name=f"work_identity.protagonist_evaluation.{field_name}",
                )

    return data


def load_work_guard_config(yaml_path: Path | str) -> dict[str, Any]:
    path = Path(yaml_path)
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise WorkGuardConfigError(f"{path}: YAML parse failed ({exc.__class__.__name__})") from exc
    except Exception as exc:
        raise WorkGuardConfigError(f"{path}: YAML load failed ({exc.__class__.__name__})") from exc
    return validate_work_guard_config(data, path)


class WorkGuard(BaseGuard):
    """작품별 work_guard.yaml 기반 추가 검증 래퍼."""

    _FOCUS_STOPWORDS = {
        "단순",
        "흐르기",
        "흐름",
        "반복",
        "대신",
        "없이",
        "처럼",
        "확인",
        "재배치",
        "의사결정",
        "장면",
        "엔진",
        "현장성",
        "승부",
        "보기",
        "이번",
        "현재",
        "핵심",
        "주요",
        "generic",
        "investment",
        "work",
        "identity",
        "drift",
    }
    _GENERIC_FINANCE_TERMS = (
        "지표",
        "자금",
        "수익률",
        "회수",
        "밸류",
        "밸류에이션",
        "멀티플",
        "ebitda",
        "ir",
        "주식",
        "지분",
        "투자",
        "차트",
        "수치",
        "계산",
        "per",
        "pbr",
        "엑싯",
        "딜",
        "m&a",
        "계약서",
        "포트폴리오",
    )

    @staticmethod
    def _normalize_str_list(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        normalized: list[str] = []
        for item in values:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    @staticmethod
    def _normalize_registry_profiles(values: Any) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            return []
        profiles: list[dict[str, Any]] = []
        for item in values:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            purpose = str(item.get("purpose", "")).strip()
            required_fields = WorkGuard._normalize_str_list(item.get("required_fields", []))
            if not name:
                continue
            profiles.append(
                {
                    "name": name,
                    "purpose": purpose,
                    "required_fields": required_fields,
                }
            )
        return profiles

    @staticmethod
    def _normalize_role_fit_constraints(values: Any) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            return []
        constraints: list[dict[str, Any]] = []
        for item in values:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "") or "").strip()
            role = str(item.get("role", "") or "").strip()
            disallowed_actions = WorkGuard._normalize_str_list(item.get("disallowed_actions", []))
            exceptions = WorkGuard._normalize_str_list(item.get("exceptions", []))
            if not name or not role or not disallowed_actions:
                continue
            constraints.append(
                {
                    "name": name,
                    "role": role,
                    "disallowed_actions": disallowed_actions,
                    "exceptions": exceptions,
                }
            )
        return constraints

    @staticmethod
    def _tokenize_focus_text(value: Any) -> set[str]:
        text = str(value or "").strip().lower()
        if not text:
            return set()
        tokens: set[str] = set()
        for token in re.split(r"[\s,|/:;()\[\]{}<>\"'`~!@#$%^&*+=?!.…-]+", text):  # utf8-hygiene: allow-line regex quantifier
            token = token.strip()
            if len(token) < 2:
                continue
            tokens.add(token)
        return tokens

    @classmethod
    def _extract_signal_keywords(cls, value: str) -> list[str]:
        raw_tokens = cls._tokenize_focus_text(value)
        keywords = [token for token in raw_tokens if token not in cls._FOCUS_STOPWORDS]
        if keywords:
            return keywords
        lowered = str(value or "").strip().lower()
        return [lowered] if lowered else []

    @staticmethod
    def _contains_any_phrase(manuscript: str, phrases: list[str]) -> bool:
        lowered = str(manuscript or "").lower()
        return any(str(phrase or "").strip().lower() in lowered for phrase in phrases if str(phrase or "").strip())

    @classmethod
    def _count_keyword_hits(cls, manuscript: str, keywords: list[str]) -> int:
        lowered = str(manuscript or "").lower()
        hits = 0
        for keyword in keywords:
            token = str(keyword or "").strip().lower()
            if not token:
                continue
            if token in lowered:
                hits += 1
        return hits

    @classmethod
    def _score_focus_item(cls, item: str, focus_text: str, focus_tokens: set[str]) -> int:
        normalized = str(item or "").strip().lower()
        if not normalized:
            return 0

        score = 0
        if normalized in focus_text:
            score += 5

        item_tokens = cls._tokenize_focus_text(normalized)
        overlap = item_tokens & focus_tokens
        score += len(overlap) * 2
        return score

    @classmethod
    def _select_relevant_strings(cls, items: list[str], focus_text: str, limit: int) -> list[str]:
        if not items or limit <= 0:
            return []

        normalized_items = [str(item).strip() for item in items if str(item).strip()]
        if not normalized_items:
            return []

        lowered_focus = str(focus_text or "").lower()
        focus_tokens = cls._tokenize_focus_text(lowered_focus)
        scored = [
            (cls._score_focus_item(item, lowered_focus, focus_tokens), idx, item)
            for idx, item in enumerate(normalized_items)
        ]
        matched = [item for score, _, item in scored if score > 0]
        if matched:
            matched_sorted = [
                item for score, _, item in sorted(scored, key=lambda row: (-row[0], row[1])) if score > 0
            ]
            return matched_sorted[:limit]
        return normalized_items[:limit]

    @classmethod
    def _select_relevant_profiles(
        cls,
        profiles: list[dict[str, Any]],
        focus_text: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not profiles or limit <= 0:
            return []

        lowered_focus = str(focus_text or "").lower()
        focus_tokens = cls._tokenize_focus_text(lowered_focus)
        scored: list[tuple[int, int, dict[str, Any]]] = []
        for idx, profile in enumerate(profiles):
            if not isinstance(profile, dict):
                continue
            haystack = " ".join(
                [
                    str(profile.get("name", "") or ""),
                    str(profile.get("purpose", "") or ""),
                    " ".join(str(x or "") for x in profile.get("required_fields", []) or []),
                ]
            )
            score = cls._score_focus_item(haystack, lowered_focus, focus_tokens)
            scored.append((score, idx, profile))

        matched = [profile for score, _, profile in scored if score > 0]
        if matched:
            return [
                profile
                for score, _, profile in sorted(scored, key=lambda row: (-row[0], row[1]))
                if score > 0
            ][:limit]
        return [profile for _, _, profile in scored[:limit]]

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
        self._work_identity = self._config.get("work_identity", {})
        if not isinstance(self._work_identity, dict):
            self._work_identity = {}
        self._tracking_slots = self._normalize_str_list(self._work_identity.get("tracking_slots", []))
        self._mandatory_scene_engines = self._normalize_str_list(
            self._work_identity.get("mandatory_scene_engines", [])
        )
        self._forbidden_flattenings = self._normalize_str_list(
            self._work_identity.get("forbidden_flattenings", [])
        )
        self._mandatory_lexicon = self._normalize_str_list(self._work_identity.get("mandatory_lexicon", []))
        self._registry_profiles = self._normalize_registry_profiles(self._work_identity.get("registry_profiles", []))
        self._role_fit_constraints = self._normalize_role_fit_constraints(
            self._work_identity.get("role_fit_constraints", [])
        )

        # protagonist_evaluation (optional compact mini bible note)
        _raw_protag_eval = self._work_identity.get("protagonist_evaluation")
        if isinstance(_raw_protag_eval, dict):
            self._protagonist_evaluation = {
                "admiration_axes": self._normalize_str_list(_raw_protag_eval.get("admiration_axes", [])),
                "forbidden_praise_patterns": self._normalize_str_list(_raw_protag_eval.get("forbidden_praise_patterns", [])),
                "observer_tiers": self._normalize_str_list(_raw_protag_eval.get("observer_tiers", [])),
                "evaluation_thresholds": self._normalize_str_list(_raw_protag_eval.get("evaluation_thresholds", [])),
            }
        else:
            self._protagonist_evaluation: dict[str, list[str]] = {}

        _logger.info(
            "[WorkGuard] 초기화: +forbidden=%d, +allowed=%d, +patterns=%d, custom_rules=%d, char_constraints=%d, tracking_slots=%d, registry_profiles=%d, role_fit=%d",
            len(extra_forbidden),
            len(extra_allowed),
            len(self._extra_patterns),
            len(self._custom_rules),
            len(self._char_constraints),
            len(self._tracking_slots),
            len(self._registry_profiles),
            len(self._role_fit_constraints),
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

    @staticmethod
    def _load_yaml(yaml_path: Path | str) -> dict:
        return load_work_guard_config(yaml_path)

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

        if self._work_identity:
            identity_lines = []

            work_type = str(self._work_identity.get("work_type", "")).strip()
            if work_type:
                identity_lines.append(f"- 작품 유형: {work_type}")

            one_line_truth = str(self._work_identity.get("one_line_truth", "")).strip()
            if one_line_truth:
                identity_lines.append(f"- 한 줄 진실: {one_line_truth}")

            protagonist_weapon = self._normalize_str_list(self._work_identity.get("protagonist_weapon", []))
            if protagonist_weapon:
                identity_lines.append(f"- 주인공 무기: {', '.join(protagonist_weapon)}")

            business_axes = self._normalize_str_list(self._work_identity.get("business_axes", []))
            if business_axes:
                identity_lines.append(f"- 핵심 사업축: {', '.join(business_axes)}")

            control_axes = self._normalize_str_list(self._work_identity.get("control_axes", []))
            if control_axes:
                identity_lines.append(f"- 장악 축: {', '.join(control_axes)}")

            if self._mandatory_scene_engines:
                identity_lines.append(f"- 반드시 살아 있어야 할 장면 엔진: {', '.join(self._mandatory_scene_engines)}")

            if self._forbidden_flattenings:
                identity_lines.append(f"- 평탄화 금지: {', '.join(self._forbidden_flattenings)}")

            if self._mandatory_lexicon:
                identity_lines.append(f"- 작품 핵심 어휘: {', '.join(self._mandatory_lexicon)}")

            if self._protagonist_evaluation:
                pe = self._protagonist_evaluation
                if pe.get("admiration_axes"):
                    identity_lines.append(f"- 주인공 감탄 축: {', '.join(pe['admiration_axes'])}")
                if pe.get("forbidden_praise_patterns"):
                    identity_lines.append(f"- 칭찬 금지 패턴: {', '.join(pe['forbidden_praise_patterns'])}")
                if pe.get("observer_tiers"):
                    identity_lines.append(f"- 관찰자 계층: {', '.join(pe['observer_tiers'])}")
                if pe.get("evaluation_thresholds"):
                    identity_lines.append(f"- 평가 임계값: {', '.join(pe['evaluation_thresholds'])}")

            if identity_lines:
                sections.append("[작품 정체성 SSOT]\n" + "\n".join(identity_lines))

        if self._tracking_slots:
            sections.append("[우선 추적 슬롯]\n" + "\n".join(f"- {slot}" for slot in self._tracking_slots))

        if self._registry_profiles:
            registry_lines = []
            for profile in self._registry_profiles:
                line = f"- {profile['name']}"
                if profile.get("purpose"):
                    line += f": {profile['purpose']}"
                required_fields = profile.get("required_fields", [])
                if required_fields:
                    line += f" | required_fields={', '.join(required_fields)}"
                registry_lines.append(line)
            if registry_lines:
                sections.append("[레지스트리 프로파일]\n" + "\n".join(registry_lines))

        if self._role_fit_constraints:
            role_lines = [
                "- 공통 원칙: 인물은 직업/역할/훈련 이력에 맞게 행동해야 하며, 별도 빌드업 없는 직업 밖 전문 행동은 금지."
            ]
            for rule in self._role_fit_constraints[:8]:
                role_line = (
                    f"- {rule['name']} ({rule['role']}): "
                    f"금지={', '.join(rule['disallowed_actions'][:4])}"
                )
                if rule.get("exceptions"):
                    role_line += f" | 예외={', '.join(rule['exceptions'][:3])}"
                role_lines.append(role_line)
            sections.append("[직업 적합성 가드]\n" + "\n".join(role_lines))

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

    def get_retrieval_contract_prompt(self, stage: str = "generic") -> str:
        if not (self._tracking_slots or self._mandatory_scene_engines or self._registry_profiles):
            return ""

        stage_map = {
            "volume": "Stage 1 권역 전략",
            "arc": "Stage 2 Arc 설계",
            "blueprint": "Stage 3 Blueprint 설계",
            "block": "Block 농축",
            "manuscript": "Stage 4 원고 집필",
        }
        stage_label = stage_map.get(stage, stage or "현재 단계")
        lines = [f"[작품 메모리 소비 계약 - {stage_label}]"]
        lines.append("- recency만으로 relevant 정보를 고르지 말고, 현재 갈등축과 작품 정체성에 직접 연결된 슬롯만 우선 소비하세요.")

        if self._tracking_slots:
            lines.append(f"- 우선 tracking_slots: {', '.join(self._tracking_slots)}")
        if self._mandatory_scene_engines:
            lines.append(f"- 반드시 재등장해야 할 장면 엔진: {', '.join(self._mandatory_scene_engines)}")
        if self._registry_profiles:
            lines.append(
                "- 참고 registry_profiles: "
                + ", ".join(profile["name"] for profile in self._registry_profiles if profile.get("name"))
            )

        if stage == "volume":
            lines.append("- 이번 권에서는 tracking_slots 2~4개만 핵심 축으로 채택하고, 권 전체를 그 슬롯 중심으로 설계하세요.")
        elif stage == "arc":
            lines.append("- 이번 Arc는 어떤 tracking_slots가 실제로 움직이는지 먼저 고르고, 각 화가 그 슬롯 변화에 기여하도록 설계하세요.")
        elif stage == "blueprint":
            lines.append("- 각 씬은 mandatory_scene_engines 중 최소 하나와 연결되게 설계하고, 추적 슬롯이 씬 단위로 어떻게 드러나는지 명시하세요.")
            if self._protagonist_evaluation:
                pe = self._protagonist_evaluation
                if pe.get("admiration_axes"):
                    lines.append(f"- 주인공 감탄 축: {', '.join(pe['admiration_axes'])}. 씬에서 감탄을 유발할 때 이 축 중 하나를 선택하세요.")
                if pe.get("forbidden_praise_patterns"):
                    lines.append(f"- 칭찬 금지 패턴: {', '.join(pe['forbidden_praise_patterns'])}. 이 패턴은 Blueprint에서 배치하지 마세요.")
                if pe.get("observer_tiers"):
                    lines.append(f"- 관찰자 계층: {', '.join(pe['observer_tiers'])}. 씬별 관찰자를 이 계층에서 골라 배치하세요.")
                if pe.get("evaluation_thresholds"):
                    lines.append(f"- 평가 임계값: {', '.join(pe['evaluation_thresholds'])}. 감탄 반응의 강도와 빈도를 이 기준으로 조절하세요.")
        elif stage == "block":
            lines.append("- 블록 농축 시 현재 블록과 직접 연결되는 tracking_slots와 scene engine만 증폭하고, 관련 없는 registry는 끌어오지 마세요.")
        elif stage == "manuscript":
            lines.append("- 이번 화/씬에 필요한 tracking_slots 1~3개만 전면에 올리고, registry의 세부 상태는 relevant한 것만 짧게 소환하세요.")

        return "\n".join(lines)

    def select_retrieval_focus(
        self,
        *,
        stage: str = "generic",
        focus_text: str = "",
        slot_limit: int = 3,
        engine_limit: int = 2,
        registry_limit: int = 2,
    ) -> dict[str, Any]:
        selected_slots = self._select_relevant_strings(self._tracking_slots, focus_text, slot_limit)
        selected_engines = self._select_relevant_strings(
            self._mandatory_scene_engines,
            focus_text,
            engine_limit,
        )
        selected_profiles = self._select_relevant_profiles(
            self._registry_profiles,
            focus_text,
            registry_limit,
        )

        return {
            "stage": stage,
            "tracking_slots": selected_slots,
            "mandatory_scene_engines": selected_engines,
            "registry_profiles": selected_profiles,
            "focus_terms": sorted(self._tokenize_focus_text(focus_text))[:20],
        }

    def get_director_review_advisory(self) -> str:
        if not (
            self._mandatory_scene_engines
            or self._forbidden_flattenings
            or self._tracking_slots
            or self._role_fit_constraints
        ):
            return ""

        lines = ["[작품 정체성 감리 기준]"]
        lines.append("- 아래 기준은 hard gate가 아니라 open_review/advisory용입니다. 원고가 작품 정체성을 놓치면 반드시 open_review에 적으세요.")
        if self._mandatory_scene_engines:
            lines.append(f"- mandatory_scene_engines: {', '.join(self._mandatory_scene_engines)}")
            lines.append("- 위 장면 엔진이 이번 화에서 전혀 보이지 않거나 약해졌다면 `work identity drift`로 지적하세요.")
        if self._forbidden_flattenings:
            lines.append(f"- forbidden_flattenings: {', '.join(self._forbidden_flattenings)}")
            lines.append("- 원고가 위 평탄화 금지 방향으로 미끄러지면 `flattened_to_generic_investment` 또는 유사 표현으로 지적하세요.")
        if self._tracking_slots:
            lines.append(f"- 핵심 tracking_slots: {', '.join(self._tracking_slots)}")
            lines.append("- 지금 화와 직접 연결되는 tracking_slots가 통째로 사라졌다면 open_review에 누락 사실을 적으세요.")
        if self._role_fit_constraints:
            lines.append("- 직업 적합성: 설정된 직업/역할과 맞지 않는 전문 행동이 빌드업 없이 튀어나오면 open_review에 적으세요.")
            for rule in self._role_fit_constraints[:4]:
                preview = ", ".join(rule["disallowed_actions"][:3])
                lines.append(f"- {rule['name']}({rule['role']}): {preview}")
        return "\n".join(lines)

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
            rf"{re.escape(char_name)}[^\n]{{0,24}}?(\d{{1,2}})세",  # utf8-hygiene: allow-line regex optional quantifier
            rf"(\d{{1,2}})세[^\n]{{0,24}}?{re.escape(char_name)}",  # utf8-hygiene: allow-line regex optional quantifier
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

    def _check_mandatory_lexicon(self, manuscript: str) -> list[dict[str, Any]]:
        if not self._mandatory_lexicon:
            return []
        if any(term in manuscript for term in self._mandatory_lexicon):
            return []
        preview = ", ".join(self._mandatory_lexicon[:5])
        return [
            {
                "type": "work_identity_lexicon_missing",
                "severity": "WARNING",
                "message": f"[Work] 작품 핵심 어휘가 거의 보이지 않음: {preview}",
            }
        ]

    def _check_mandatory_scene_engines(self, manuscript: str) -> list[dict[str, Any]]:
        if not self._mandatory_scene_engines:
            return []

        matched_engines: list[str] = []
        engine_keyword_map: dict[str, list[str]] = {}
        for engine in self._mandatory_scene_engines:
            keywords = self._extract_signal_keywords(engine)
            engine_keyword_map[str(engine)] = keywords
            hit_count = self._count_keyword_hits(manuscript, keywords)
            threshold = 1 if len(keywords) <= 2 else 2
            if str(engine).strip().lower() in str(manuscript or "").lower() or hit_count >= threshold:
                matched_engines.append(engine)

        if matched_engines:
            return []

        preview = ", ".join(self._mandatory_scene_engines[:4])
        return [
            {
                "type": "work_identity_scene_engine_missing",
                "severity": "WARNING",
                "expected_scene_engines": list(self._mandatory_scene_engines),
                "matched_scene_engines": matched_engines,
                "scene_engine_keywords": engine_keyword_map,
                "message": f"[Work] 필수 장면 엔진이 희미함: {preview}",
            }
        ]

    def _check_forbidden_flattenings(self, manuscript: str) -> list[dict[str, Any]]:
        if not self._forbidden_flattenings:
            return []

        lowered = str(manuscript or "").lower()
        finance_hits = self._count_keyword_hits(lowered, list(self._GENERIC_FINANCE_TERMS))
        lexicon_present = any(term in manuscript for term in self._mandatory_lexicon) if self._mandatory_lexicon else False
        warnings: list[dict[str, Any]] = []

        for flattening in self._forbidden_flattenings:
            text = str(flattening or "").strip()
            if not text:
                continue
            keywords = self._extract_signal_keywords(text)
            keyword_hits = self._count_keyword_hits(lowered, keywords)
            should_warn = False

            if self._contains_any_phrase(lowered, [text]):
                should_warn = True
            elif any(token in text.lower() for token in ("m&a", "주식", "매매")):
                should_warn = finance_hits >= 2 and keyword_hits >= 1
            elif "숫자" in text or "투자 용어" in text or "현장성" in text:
                should_warn = finance_hits >= 3 and not lexicon_present
            else:
                should_warn = keyword_hits >= max(1, min(2, len(keywords)))

            if should_warn:
                warnings.append(
                    {
                        "type": "work_identity_flattening_warning",
                        "severity": "WARNING",
                        "flattening": text,
                        "keyword_hits": keyword_hits,
                        "finance_term_hits": finance_hits,
                        "lexicon_present": lexicon_present,
                        "message": f"[Work] 작품 평탄화 경고: {text} (`flattened_to_generic_investment` 가능성)",
                    }
                )

        return warnings

    @staticmethod
    def _has_nearby_phrase(manuscript: str, name: str, phrase: str, window: int = 80) -> bool:
        escaped_name = re.escape(str(name or "").strip())
        escaped_phrase = re.escape(str(phrase or "").strip())
        if not escaped_name or not escaped_phrase:
            return False
        patterns = [
            rf"{escaped_name}[^\n]{{0,{window}}}{escaped_phrase}",
            rf"{escaped_phrase}[^\n]{{0,{window}}}{escaped_name}",
        ]
        return any(re.search(pattern, manuscript) for pattern in patterns)

    def _check_role_fit_constraints(self, manuscript: str) -> list[dict[str, Any]]:
        if not self._role_fit_constraints:
            return []

        warnings: list[dict[str, Any]] = []
        for rule in self._role_fit_constraints:
            name = str(rule.get("name", "") or "").strip()
            role = str(rule.get("role", "") or "").strip()
            disallowed_actions = [str(x).strip() for x in rule.get("disallowed_actions", []) if str(x).strip()]
            exceptions = [str(x).strip() for x in rule.get("exceptions", []) if str(x).strip()]
            if not name or not role or name not in manuscript:
                continue

            exception_hit = any(
                self._has_nearby_phrase(manuscript, name, exception) or exception in manuscript for exception in exceptions
            )
            if exception_hit:
                continue

            for action in disallowed_actions:
                if self._has_nearby_phrase(manuscript, name, action):
                    warnings.append(
                        {
                            "type": "work_role_fit_warning",
                            "severity": "WARNING",
                            "character": name,
                            "role": role,
                            "action": action,
                            "exceptions_considered": exceptions,
                            "exception_hit": exception_hit,
                            "message": f"[Work] 직업 적합성 확인 필요: {name}({role})가 '{action}' 수행 묘사",
                        }
                    )
                    break

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
        warning_violations.extend(self._check_mandatory_lexicon(manuscript))
        warning_violations.extend(self._check_mandatory_scene_engines(manuscript))
        warning_violations.extend(self._check_forbidden_flattenings(manuscript))
        warning_violations.extend(self._check_role_fit_constraints(manuscript))

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
