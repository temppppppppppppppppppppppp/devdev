"""
utf8-hygiene: allow-file -- legacy Korean prompt text in this generator predates the structured carryover patch.
[V60.80] Blueprint Ensemble Generator
병렬로 3개 Blueprint 후보 생성 후 최적 선택

전략:
- Strategy A: 액션 중심 (긴장도 높음, 전투/추격/대결)
- Strategy B: 감정 중심 (캐릭터 심리, 갈등/화해/성장)
- Strategy C: 대화 중심 (관계 발전, 정보 교환, 음모)

내부적으로 Two-Phase 방식 적용:
1. 구조 생성 (scene_breakdown)
2. 상세화 (integrated_scenario)
"""

import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path

from modules.core.artifact_logging import build_candidate_key, snapshot_logged_artifact
from modules.core.constants import AIModels, GenreTypes, smart_truncate
from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.project_support import normalize_external_pov_insert_policy
from modules.core.prompt_loader import PromptLoader
from modules.core.response_schemas import (
    BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS,
    BLUEPRINT_OPENING_TRANSITION_TYPES,
    BLUEPRINT_SCHEMA,
)
from modules.core.scene_obligation_heuristics import has_actionable_obligation_text, has_meaningful_state_value
from modules.core.stage_cross_stage_contract import (
    apply_opening_transition_contract,
    read_declared_opening_transition_type,
)
from modules.core.tactical_intrusion_contract import collect_tactical_surface_text, detect_tactical_intrusion_signature
from modules.core.tactical_utils import extract_episode_tactical

from .base_agent import _SYSTEM_CFG, AgentErrorType, BaseAgent
from .scene_cardinality_contract import evaluate_stage3_scene_cardinality
from .stage3_prompt_envelope import (
    build_stage3_archive_appendix,
    build_stage3_prompt_envelope_meta,
    build_stage3_recent_carryover_digest,
)

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


GENRE_STRATEGY_CONTRACT_SCHEMA_VERSION = "genre-strategy-contract-v1"


def _normalize_genre_value(value: object) -> str:
    return str(value or "").strip().lower()


def _is_investment_business_power_genre(genre: object) -> bool:
    normalized = _normalize_genre_value(genre)
    if normalized in {
        GenreTypes.INVESTMENT,
        "investment",
        "invest",
        "투자",
        "투자물",
        "business-power",
        "business_power",
        "investment_family_office_control",
    }:
        return True
    return "investment" in normalized or "투자" in normalized


def _contains_investment_like_signal(value: object) -> bool:
    if value is None:
        return False
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict | list) else str(value)
    except Exception:
        text = str(value)
    return _is_investment_business_power_genre(text)


def build_genre_strategy_contract(genre: object, strategy_name: object) -> dict:
    """Build a route-level genre strategy contract without judging narrative quality."""
    normalized_genre = _normalize_genre_value(genre)
    normalized_strategy = str(strategy_name or "").strip() or "unknown"
    if not (_is_investment_business_power_genre(normalized_genre) and normalized_strategy == "action_focused"):
        return {}

    contract = {
        "schema_version": GENRE_STRATEGY_CONTRACT_SCHEMA_VERSION,
        "contract_id": "investment_business_power.action_focused.v1",
        "authority_level": "route",
        "authority_source": "stage3_genre_strategy_contract",
        "genre_type": GenreTypes.INVESTMENT,
        "genre_family": "investment_business_power",
        "strategy_name": normalized_strategy,
        "factsheet_mutation": False,
        "material_mutation": False,
        "director_visible": True,
        "action_semantics": [
            "decisive business move",
            "capital exposure",
            "institutional pressure",
            "governance or legal next gate",
        ],
        "tension_semantics": [
            "deadline pressure",
            "counterparty risk",
            "liquidity or margin limit",
            "reputation and access risk",
        ],
        "forbidden_defaults": [
            "combat",
            "chase",
            "intruder",
            "vehicle attack",
            "physical crisis",
            "thriller infiltration",
        ],
    }
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True)
    contract["contract_hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return contract


def format_genre_strategy_contract_prompt(contract: dict) -> str:
    if not contract:
        return ""
    return f"""
[Genre Strategy Contract - {contract.get("contract_id")}]
- contract_hash: {contract.get("contract_hash")}
- authority_level: route; Director-visible advisory context only, not Python verdict authority.
- action_focused means business execution pressure: position entry/exit, capital exposure, institutional confrontation, governance/legal gate, proof/receipt, and next decision gate.
- tension means deadline pressure, counterparty risk, liquidity/margin limits, reputation/access risk, and family or institutional control pressure.
- ending_hook should turn on deal break, approval hold, reputation exposure, capital freeze, legal next gate, or counterparty condition change.
- Do not default to combat, chase, intruder, vehicle attack, physical crisis, or thriller infiltration unless the tactical authority explicitly supports it.
""".strip()


def _build_strategy_directive_for_genre(strategy: dict, *, genre: str, extra_directive: str) -> tuple[str, dict]:
    strategy_name = strategy.get("name", "")
    contract = build_genre_strategy_contract(genre, strategy_name)
    directive = format_genre_strategy_contract_prompt(contract) if contract else strategy["directive"]
    return directive + AI_TELL_BLUEPRINT_GUARDRAIL + extra_directive, contract


# Blueprint 생성 전략
BLUEPRINT_STRATEGIES = [
    {
        "name": "action_focused",
        "display": "액션 중심",
        "directive": """
[전략: 액션 중심]
- 긴장도를 높게 유지하세요 (7-9/10)
- 전투, 추격, 대결 씬을 중심으로 구성하세요
- 빠른 템포와 역동적인 전개를 강조하세요
- 감정 묘사는 최소화하고 행동으로 보여주세요
- [QI-1-A6] ending_hook은 물리적 위기/액션 클리프행어로 끝낼 것
""",
        "tension_range": (7, 9),
    },
    {
        "name": "emotion_focused",
        "display": "감정 중심",
        "directive": """
[전략: 감정 중심]
- 캐릭터의 내면 심리를 깊이 있게 다루세요
- 갈등, 화해, 성장의 순간을 부각하세요
- 대화 속 감정의 미묘한 변화를 묘사하세요
- 긴장도는 중간 수준으로 유지하세요 (4-6/10)
- [QI-1-A6] ending_hook은 감정적 반전/내면 갈등 여운으로 끝낼 것
""",
        "tension_range": (4, 6),
    },
    {
        "name": "dialogue_focused",
        "display": "대화 중심",
        "directive": """
[전략: 대화 중심]
- 캐릭터 간 대화를 통해 이야기를 전개하세요
- 정보 교환, 음모, 협상 씬을 중심으로 구성하세요
- 대사를 통해 캐릭터 성격과 관계를 드러내세요
- 서브텍스트(말 속에 숨겨진 의미)를 활용하세요
- [QI-1-A6] ending_hook은 대사 중단/대화 반전으로 끝낼 것
""",
        "tension_range": (3, 7),
    },
]

AI_TELL_BLUEPRINT_GUARDRAIL = """
[AI 티 회피 지침]
- Blueprint는 downstream scene authority이지 브리핑 문서나 회차 요약문이 아닙니다.
- integrated_scenario에 독자 대상 설명문, recap, 메타 해설을 끼워 넣지 마세요.
- scene_breakdown의 summary/description/goal/content에는 "직전 화", "이전 화", "이번 화", "이번 에피소드" 같은 회차 메타어를 쓰지 말고 실제 현재 장면의 행동/대사/결정으로만 작성하세요.
- 상태창/HUD/시스템 메시지/홀로그램 같은 게임식 UI를 정본 근거 없이 새로 발명하지 마세요.
- 장면 말미를 설명문으로 기계적으로 요약하지 마세요.
- 감정 반응을 상투적인 반응구 반복으로 처리하지 말고 행동·대사·구체 감각으로 드러내세요.
- 정보 전달만 수행하는 대사가 길게 이어지지 않게 하세요.
- 매 씬의 도입과 종결 리듬을 같게 반복하지 마세요.
- 독자가 "익숙한 AI 문장"이라고 느낄 만한 접속구·감탄구 남용을 피하세요.
"""


def _extract_year_month(text: object) -> tuple[int, int] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    match = re.search(r"(?P<year>20\d{2}|19\d{2})\s*년\D{0,8}(?P<month>1[0-2]|0?[1-9])\s*월", raw)
    if not match:
        return None
    try:
        return int(match.group("year")), int(match.group("month"))
    except (TypeError, ValueError):
        return None


def _year_month_conflicts(left: object, right: object) -> bool:
    left_point = _extract_year_month(left)
    right_point = _extract_year_month(right)
    return bool(left_point is not None and right_point is not None and left_point != right_point)


def _extract_year_month_day(raw: object) -> tuple[int, int, int] | None:
    if isinstance(raw, dict):
        year = raw.get("year")
        month = raw.get("month")
        if year not in (None, "") and month not in (None, ""):
            try:
                day = raw.get("day")
                day_value = int(day) if day not in (None, "") else 0
                return int(year), int(month), day_value
            except (TypeError, ValueError):
                return None
        for key in ("표현", "expression", "text", "description"):
            value = raw.get(key)
            if value not in (None, ""):
                raw = value
                break
        else:
            raw = ""

    text = str(raw or "").strip()
    if not text:
        return None
    year_match = re.search(r"(?P<year>20\d{2}|19\d{2})\s*년", text)
    month_match = re.search(r"(?P<month>1[0-2]|0?[1-9])\s*월", text)
    if not month_match:
        return None
    day_match = re.search(r"(?P<day>[12]\d|3[01]|0?[1-9])\s*일", text)
    year = int(year_match.group("year")) if year_match else 0
    month = int(month_match.group("month"))
    day = int(day_match.group("day")) if day_match else 0
    return year, month, day


def _resolve_authoritative_opening_time_context(constraint_block: dict | None) -> str:
    payload = constraint_block if isinstance(constraint_block, dict) else {}
    episode_state_packet = payload.get("episode_state_packet")
    if isinstance(episode_state_packet, dict):
        opening_truth = episode_state_packet.get("opening_truth")
        if isinstance(opening_truth, dict):
            time_context = str(opening_truth.get("time_context", "") or "").strip()
            if time_context:
                return time_context
    episode_progression_packet = payload.get("episode_progression_packet")
    if isinstance(episode_progression_packet, dict):
        truths = episode_progression_packet.get("time_truths", [])
        if isinstance(truths, list):
            for truth in truths:
                truth_text = str(truth or "").strip()
                if truth_text:
                    return truth_text
    return ""


_BLUEPRINT_SYSTEM_UI_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "HUD",
        "상태창",
        "상태 창",
        "status window",
        "홀로그램 창",
        "홀로그램",
        "hologram window",
        "퀘스트 창",
        "퀘스트",
        "quest window",
        "알림창",
        "notification window",
        "시스템 메시지",
        "system message",
        "스탯창",
        "스테이터스 창",
        "[👤",
        "[💰",
        "[🎯",
        "[HP",
        "[MP",
        "[LV",
        "[SYSTEM",
    )
)

_BLUEPRINT_META_RECAP_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "직전 화",
        "이전 화",
        "이번 화",
        "이번 에피소드",
    )
)

_RETRY_FEEDBACK_DROP_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "[작품 추적 슬롯 요약]",
        "[관계 의미 질의]",
        "[styleguide",
        "[arc 시간 연속성 참고]",
        "[arc 개요",
        "[context tier",
        "[hud convenience state]",
        "[등장 가능 npc]",
        "[v60.98 씬 프리셋",
        "[주인공 고평가 연출 가이드]",
    )
)

_RETRY_FEEDBACK_OUTPUT_REWRITES = (
    ("직전 화", "직전 장면"),
    ("이전 화", "이전 사건"),
    ("이번 화", "현재 장면"),
    ("이번 에피소드", "현재 장면"),
)


def _sanitize_retry_feedback_for_blueprint_prompt(text: str) -> str:
    sanitized = str(text or "")
    for source, replacement in _RETRY_FEEDBACK_OUTPUT_REWRITES:
        sanitized = sanitized.replace(source, replacement)
    return sanitized


def _build_stage3_retry_repair_guidance(fix_pack: dict | None, repair_contract: dict | None) -> str:
    payload = fix_pack if isinstance(fix_pack, dict) else {}
    contract = repair_contract if isinstance(repair_contract, dict) else {}
    lines: list[str] = []
    must_fix = [str(item).strip() for item in (payload.get("must_fix") or []) if str(item or "").strip()]
    if must_fix:
        lines.append("- must_fix: " + " | ".join(must_fix[:4]))
    do_not_regress = [str(item).strip() for item in (payload.get("do_not_regress") or []) if str(item or "").strip()]
    if do_not_regress:
        lines.append("- do_not_regress: " + " | ".join(do_not_regress[:4]))
    success_condition = str(payload.get("success_condition", "") or "").strip()
    if success_condition:
        lines.append("- success_condition: " + success_condition)
    patch_targets = [str(item).strip() for item in (payload.get("patch_targets") or []) if str(item or "").strip()]
    if patch_targets:
        lines.append("- patch_targets: " + ", ".join(patch_targets[:4]))
    target_kind = str(contract.get("target_kind", "") or payload.get("target_kind", "") or "").strip()
    if target_kind:
        lines.append(f"- target_kind: {target_kind}")
    repair_scope = str(contract.get("repair_scope", "") or contract.get("fix_scope", "") or "").strip()
    if repair_scope:
        lines.append(f"- repair_scope: {repair_scope}")
    if not lines:
        return ""
    return "[Stage3 retry repair contract]\n" + "\n".join(lines)


_RETRY_FEEDBACK_SECTION_WINDOWS = (
    ("[binding prevalidation]", 6),
    ("[python advisory]", 6),
    ("[strategy feedback]", 3),
)
_RETRY_FEEDBACK_PRIORITY_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "candidate_disqualified",
        "episode_progression",
        "temporal_deictic",
        "opening_transition",
        "scene_completeness",
        "scene_breakdown",
        "protagonist_state",
        "schema_incompatible",
        "tactical",
        "binding",
        "regenerate",
        "replay",
        "must_focus",
        "stop line",
        "critical",
        "major",
        "reject",
    )
)


# [V60.98] 씬 프리셋 정의 - 장면/화자 전환 연출
SCENE_PRESETS = {
    "opening_hook": "화 시작, 독자 유입용. 시각 중심, 임팩트 있는 오프닝.",
    "daily_routine": "일상 묘사, 세계관 노출. 여유로운 호흡.",
    "tension_build": "긴장감 축적. 불안한 분위기, 짧은 문장.",
    "action_peak": "장르별 고강도 실행/압박 클라이맥스. 핵심 선택과 결과를 선명하게 제시.",
    "emotional_reveal": "감정 폭발, 내면 묘사. 느린 호흡, 대사/독백 중심.",
    "dialogue_duel": "설전/협상/대립. 대사 중심, 긴장감 있는 대화.",
    "villain_scheme": "★악역 시점 전환★ 음모/계략 노출. 독자에게 위협 암시.",
    "side_glimpse": "★조연 시점 전환★ 주인공 부재 상황, '저 사람 대단해!' 반응.",
    "flashback": "과거 회상. 몽환적 전환, 과거 시제.",
    "omniscient_hint": "★전지적 시점★ 복선/떡밥 암시. '그는 아직 몰랐다...'",
    "cliffhanger": "화 끝 훅. 급박한 전개, 긴장 최고조에서 끊기.",
    "resolution": "갈등 해소, 정리. 여운 있는 마무리.",
}


def build_external_pov_policy_constraint(primary_pov: str, external_pov_insert_policy: str, *, genre: str = "") -> str:
    pov = str(primary_pov or "").strip()
    policy = normalize_external_pov_insert_policy(external_pov_insert_policy, primary_pov=pov, genre=genre)

    if pov == "1인칭":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 주인공 부재 장면 금지
- villain_scheme, side_glimpse, omniscient_hint 프리셋 사용 금지
- 모든 씬은 주인공이 직접 관찰/행동 가능한 범위 안에서만 설계"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- 기본은 1인칭 유지
- side_glimpse만 씬 전환(***) 뒤 1회성 짧은 반응 컷으로 허용
- villain_scheme, omniscient_hint는 사용 금지
- 외부 시점 컷이 본편 POV를 대체하지 않게 설계"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 기본은 1인칭 유지하되, 씬 전환(***) 뒤 외부 시점 컷을 전략적으로 허용
- side_glimpse, villain_scheme, omniscient_hint를 짧은 삽입 컷으로만 사용
- 동일 씬 내부 시점 혼합은 금지"""

    if pov == "3인칭":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 주인공 중심 3인칭만 유지
- villain_scheme, side_glimpse, omniscient_hint 프리셋 사용 금지"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- villain_scheme, side_glimpse는 씬 전환(***) 뒤 짧게만 사용 (1-2문단)
- omniscient_hint는 화당 1회 이내로 제한
- 외부 시점은 반응/위협 암시/정보 경제에만 사용"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 3인칭 본류를 유지하되 외부 시점 컷을 scene-level로 허용
- villain_scheme, side_glimpse, omniscient_hint를 아크 흐름에 맞춰 사용
- 같은 장면 안에서 시점을 뒤섞지 말고 씬 경계(***)를 명확히 둘 것"""

    if pov == "전지적":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 전지적 서술은 허용하되 별도 외부 POV 프리셋은 사용 금지
- 시점 전환 효과를 남용하지 말고 핵심 서술자 관점을 유지"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- 전지적 서술을 본류로 유지
- side_glimpse, villain_scheme, omniscient_hint는 장면 효과용으로만 절제 사용"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 전지적 서술을 기반으로 scene-level 외부 POV 컷을 자유롭게 설계 가능
- 단, 과도한 빈도와 중복 설명은 금지"""

    if pov == "혼합":
        if policy == "금지":
            return """### [V-POV] 혼합 시점 + 외부 시점 금지
- 혼합은 허용하되 외부 반응 컷/악역 컷/전지적 힌트 프리셋은 사용 금지
- 선택된 시점 전환 외 추가 삽입 컷을 넣지 말 것"""
        if policy == "제한적 허용":
            return """### [V-POV] 혼합 시점 + 제한적 외부 시점
- scene-level switching은 허용
- 외부 삽입 컷은 reaction/foreshadowing 용도로만 제한 사용
- 같은 씬 내부 시점 혼합은 금지"""
        return """### [V-POV] 혼합 시점 + 적극적 외부 시점
- 혼합 시점 작품으로 설계하되 scene 경계를 명확히 둘 것
- side_glimpse, villain_scheme, omniscient_hint를 전략적으로 사용할 수 있음
- 동일 씬 내부 시점 혼합과 불필요한 churn은 금지"""

    return ""


def _fit_compact_context(value: object, max_chars: int, *, head_ratio: float = 0.55) -> str:
    raw = str(value or "")
    if len(raw) <= max_chars:
        return raw
    head_chars = max(0, min(int(max_chars * head_ratio), max_chars - 80))
    return smart_truncate(raw, max_chars=max_chars, head_chars=head_chars)


def _append_constraint_section(lines: list[str], header: str, band_lines: list[str]) -> None:
    if not band_lines:
        return
    lines.append(header)
    lines.extend(band_lines)
    lines.append("")


def _is_concrete_opening_location(location: str) -> bool:
    normalized = str(location or "").strip().casefold()
    if not normalized:
        return False
    placeholder_locations = {
        "n/a",
        "none",
        "unknown",
        "미정",
        "불명",
        "서사 시작",
        "서사 시작점",
        "시작점",
    }
    return normalized not in placeholder_locations


def _should_hard_bind_opening_location(opening_truth: dict) -> bool:
    if not isinstance(opening_truth, dict):
        return False
    location = str(opening_truth.get("location", "") or "").strip()
    if not _is_concrete_opening_location(location):
        return False
    source = str(opening_truth.get("location_source", "") or "").strip()
    return source.startswith("prev_blueprint") or "cross_stage_authority_packet" in source


def _format_episode_state_packet_lines(packet: dict | None) -> list[str]:
    payload = packet if isinstance(packet, dict) else {}
    if not payload:
        return []
    packet_lines: list[str] = [
        "[EpisodeStatePacket - authoritative pre-generation carryover]",
        "  이 packet이 Stage3의 단일 carryover truth surface다. 아래 legacy continuity/state는 이 packet에서 파생된 값으로 읽어라.",
    ]
    opening_truth = payload.get("opening_truth") if isinstance(payload.get("opening_truth"), dict) else {}
    protagonist_truth = payload.get("protagonist_truth") if isinstance(payload.get("protagonist_truth"), dict) else {}
    location = str(opening_truth.get("location", "") or "").strip()
    if location:
        packet_lines.append(f"  - opening.location: {_fit_compact_context(location, 120)}")
        if _should_hard_bind_opening_location(opening_truth):
            packet_lines.append(
                "    JSON start_location and scene_breakdown.scene_1.location must equal opening.location exactly; "
                "move elsewhere only after an explicit transition inside scene_1 or a later scene."
            )
    location_source = str(opening_truth.get("location_source", "") or "").strip()
    if location_source:
        packet_lines.append(f"    source: {_fit_compact_context(location_source, 100)}")
    time_context = str(opening_truth.get("time_context", "") or "").strip()
    if time_context:
        packet_lines.append(f"  - opening.time_context: {_fit_compact_context(time_context, 120)}")
    time_source = str(opening_truth.get("time_source", "") or "").strip()
    if time_source:
        packet_lines.append(f"    source: {_fit_compact_context(time_source, 100)}")
    transition_expectation = str(opening_truth.get("opening_transition_expectation", "") or "").strip()
    if transition_expectation:
        packet_lines.append(f"  - opening.transition_expectation: {_fit_compact_context(transition_expectation, 120)}")
    active_characters = opening_truth.get("active_characters") or []
    if isinstance(active_characters, list):
        active_character_text = ", ".join(
            str(item or "").strip() for item in active_characters[:5] if str(item or "").strip()
        )
    else:
        active_character_text = str(active_characters or "").strip()
    if active_character_text:
        packet_lines.append(f"  - opening.active_characters: {_fit_compact_context(active_character_text, 120)}")
        if "do not declare direct_continuation" not in transition_expectation.casefold():
            packet_lines.append(
                "    direct_continuation이면 opening.active_characters는 이미 현장에 있는 상태로 간주하고 재입장 동선을 새로 쓰지 마라."
            )
    protagonist_sources = protagonist_truth.get("sources") if isinstance(protagonist_truth.get("sources"), dict) else {}
    equipment = protagonist_truth.get("equipment")
    if equipment:
        if isinstance(equipment, list):
            equipment_text = ", ".join(str(item or "").strip() for item in equipment[:5] if str(item or "").strip())
        else:
            equipment_text = str(equipment or "").strip()
        if equipment_text:
            packet_lines.append(f"  - protagonist.equipment: {_fit_compact_context(equipment_text, 120)}")
    injuries = str(protagonist_truth.get("injuries", "") or "").strip()
    if injuries:
        packet_lines.append(f"  - protagonist.injuries: {_fit_compact_context(injuries, 120)}")
    if isinstance(protagonist_sources, dict):
        for key in ("equipment", "injuries", "mood", "companions", "internal_energy"):
            source_text = str(protagonist_sources.get(key, "") or "").strip()
            if source_text:
                packet_lines.append(f"    {key}.source: {_fit_compact_context(source_text, 100)}")
    dropped_conflicts = payload.get("dropped_conflicts") or []
    if isinstance(dropped_conflicts, list) and dropped_conflicts:
        packet_lines.append("  - dropped_conflicts:")
        for item in dropped_conflicts[:3]:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field", "") or "").strip()
            reason = str(item.get("reason", "") or "").strip()
            dropped_value = str(item.get("dropped_value", "") or "").strip()
            line_parts = [part for part in [field, reason, dropped_value] if part]
            if line_parts:
                packet_lines.append(f"    · {_fit_compact_context(' | '.join(line_parts), 120)}")
    rewrite_required = payload.get("rewrite_required_reasons") or []
    if isinstance(rewrite_required, list) and rewrite_required:
        packet_lines.append(
            f"  - rewrite_required_reasons: {', '.join(_fit_compact_context(item, 40) for item in rewrite_required[:5])}"
        )
    return packet_lines


class BlueprintEnsembleGenerator(BaseAgent):
    """
    [V60.80] Blueprint Ensemble Generator

    병렬로 3개 Blueprint 후보 생성 후 최적 선택
    """

    # [V61.3→TF-26] 앙상블 타임아웃 — system.yaml ensemble_timeouts.blueprint 참조
    _TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("blueprint", {})
    ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)
    SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        self._prompt_loader = PromptLoader()
        self.strategies = BLUEPRINT_STRATEGIES
        self.max_workers = 3
        self.last_error_types: list[str] = []
        self.last_disqualified_candidates: list[dict] = []

    @staticmethod
    def _select_generate_error_type(error_types: list[str]) -> str | None:
        """Collapse worker failures into one fast-fail hint for the caller."""
        if not error_types:
            return None
        if AgentErrorType.CANDIDATE_DISQUALIFIED in error_types:
            return AgentErrorType.CANDIDATE_DISQUALIFIED
        if AgentErrorType.SCHEMA_INCOMPATIBLE in error_types:
            return AgentErrorType.SCHEMA_INCOMPATIBLE
        non_unknown = [error_type for error_type in error_types if error_type and error_type != AgentErrorType.UNKNOWN]
        if non_unknown:
            return non_unknown[0]
        return error_types[0]

    @staticmethod
    def _error_type_from_agent_error_response(result: dict) -> str | None:
        if not isinstance(result, dict) or result.get("error") is not True:
            return None
        error_type = str(result.get("error_type", "") or "").strip()
        known_error_types = {
            AgentErrorType.TIMEOUT,
            AgentErrorType.QUOTA_EXCEEDED,
            AgentErrorType.MALFORMED_RESPONSE,
            AgentErrorType.NETWORK_ERROR,
            AgentErrorType.SCHEMA_INCOMPATIBLE,
            AgentErrorType.CANDIDATE_DISQUALIFIED,
            AgentErrorType.UNKNOWN,
        }
        return error_type if error_type in known_error_types else AgentErrorType.UNKNOWN

    def _resolve_blueprint_arc_focus(self, ep_num: int, arc_data: dict, constraint_block: dict) -> str:
        arc_focus = constraint_block.get("must_focus", {}).get("content", "")
        if not arc_focus:
            # Stage3 producer-input 전용: tactical_doc shadowing 방지를 위해 prefer_full_doc 모드 사용.
            # episode_details bullet TL;DR과 per-episode tactical_doc slice를 함께 결합한다.
            # 다른 12개 호출자(Stage4/Director/continuity/ToT/prompt_builder 등)는 default(False)를 유지.
            arc_focus = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
                prefer_full_doc=True,
            )

        episode_details = arc_data.get("episode_details") or []
        if isinstance(episode_details, list):
            for item in episode_details:
                if isinstance(item, dict) and item.get("ep_num") == ep_num:
                    details = item.get("details") or []
                    if isinstance(details, list) and details:
                        detail_text = "\n".join(f"  - {detail}" for detail in details if isinstance(detail, str))
                        arc_focus = f"[{ep_num}화 추가 사건 (Arc 단계 보강)]\n{detail_text}\n\n{arc_focus}"
                    break

        return smart_truncate(
            arc_focus,
            max_chars=15000,
            head_chars=max(0, min(int(15000 * 0.55), 15000 - 80)),
        )

    def _resolve_blueprint_ensemble_genre(self) -> str:
        genre_signals: list[tuple[str, object]] = []
        weak_investment_sources: list[str] = []
        try:
            if hasattr(self, "context") and hasattr(self.context, "db"):
                bible = self.context.db.load_anchor("bible")
                if isinstance(bible, dict):
                    genre_signals.append(("bible._genre", bible.get("_genre")))
                    if _contains_investment_like_signal(bible):
                        weak_investment_sources.append("bible")
                style_guide = self.context.db.load_anchor("style_guide")
                if isinstance(style_guide, dict):
                    genre_signals.append(("style_guide.genre", style_guide.get("genre")))
                    if _contains_investment_like_signal(style_guide):
                        weak_investment_sources.append("style_guide")
                if isinstance(bible, dict):
                    meta_info = (
                        bible.get("MasterBible", {}).get("ProjectData", {}).get("MetaInfo", {})
                        if isinstance(bible.get("MasterBible"), dict)
                        else {}
                    )
                    if isinstance(meta_info, dict):
                        genre_signals.append(
                            (
                                "bible.MasterBible.ProjectData.MetaInfo.genre_archetype",
                                meta_info.get("genre_archetype"),
                            )
                        )
        except Exception as exc:
            logging.warning(f" [V61.3] genre 사전 로드 실패: {str(exc)[:50]}")

        stage0_genre = self._load_stage0_style_guide_genre()
        genre_signals.append(("stage0_output/style_guide.json", stage0_genre))
        if _contains_investment_like_signal(stage0_genre):
            weak_investment_sources.append("stage0_output/style_guide.json")
        for _source, value in genre_signals:
            if _normalize_genre_value(value):
                return GenreTypes.INVESTMENT if _is_investment_business_power_genre(value) else str(value)

        if weak_investment_sources:
            logging.warning(
                "[BPEnsemble] genre defaulted to wuxia; detected unresolved investment-like genre signal at %s",
                weak_investment_sources[0],
            )
        return GenreTypes.WUXIA

    def _load_stage0_style_guide_genre(self) -> str:
        try:
            root = getattr(getattr(getattr(self, "context", None), "current_project", None), "paths", None)
            root_path = getattr(root, "root", None)
            if not root_path:
                return ""
            style_path = Path(root_path) / "stage0_output" / "style_guide.json"
            if not style_path.exists():
                return ""
            payload = json.loads(style_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return str(payload.get("genre") or "")
        except Exception as exc:
            logging.debug("[BPEnsemble] stage0 style guide genre fallback failed: %s", exc)
        return ""

    def _prepare_blueprint_ensemble_context(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        prev_manuscripts_text: str,
        state_tracker,
    ) -> dict:
        arc_focus = self._resolve_blueprint_arc_focus(ep_num, arc_data, constraint_block)
        genre = self._resolve_blueprint_ensemble_genre()
        constraints_str = self._format_constraints(constraint_block, genre=genre)
        must_focus = constraint_block.get("must_focus", {}) if isinstance(constraint_block, dict) else {}
        tactical_excerpt = str(must_focus.get("content", "") or "").strip() if isinstance(must_focus, dict) else ""
        if not tactical_excerpt:
            tactical_excerpt = str(arc_focus or "").strip()
        archive_appendix_text, archive_appendix_meta = build_stage3_archive_appendix(prev_manuscripts_text)
        authoritative_time_context = _resolve_authoritative_opening_time_context(constraint_block)
        prev_info = self._format_prev_info_expanded(
            prev_blueprint,
            prev_blueprints,
            prev_manuscripts_text,
            archive_appendix_text=archive_appendix_text,
            authoritative_time_context=authoritative_time_context,
        )
        hud_context = self._build_hud_context(state_tracker, ep_num)

        try:
            guard = getattr(self.context, "guard", None)
            if guard and hasattr(guard, "get_retrieval_contract_prompt"):
                guard.get_retrieval_contract_prompt("blueprint")
        except Exception as exc:
            logging.debug("[BPEnsemble] work retrieval contract 로드 실패: %s", exc)

        shared_context = f"{constraints_str or ''}\n\n{arc_focus or ''}\n\n{prev_info or ''}\n\n{hud_context or ''}"
        cache_info = self._get_or_create_context_cache(
            cache_type="blueprint_ensemble",
            content=shared_context,
            ttl_seconds=600,
            project_name=self._context_cache_project_namespace("ep", ep_num),
        )
        return {
            "arc_focus": arc_focus,
            "genre": genre,
            "constraints_str": constraints_str,
            "tactical_excerpt": tactical_excerpt,
            "prev_info": prev_info,
            "hud_context": hud_context,
            "cache_name": cache_info.get("cache_name"),
            "constraint_block": constraint_block if isinstance(constraint_block, dict) else {},
            "archive_appendix_meta": archive_appendix_meta,
        }

    def _select_blueprint_ensemble_strategies(self, single_strategy: str) -> list[dict]:
        if not single_strategy:
            return self.strategies

        filtered = [strategy for strategy in self.strategies if strategy.get("name") == single_strategy]
        return filtered or self.strategies

    @staticmethod
    def _build_blueprint_strategy_feedback(
        strategy_name: str,
        rejected_strategy: str,
        strategy_specific_feedback: str,
    ) -> str:
        if strategy_name == rejected_strategy and strategy_specific_feedback:
            return strategy_specific_feedback
        if strategy_specific_feedback:
            return f"[이전 시도 문제 요약]\n{strategy_specific_feedback}"
        return ""

    @staticmethod
    def _compress_retry_feedback(feedback: str, *, max_lines: int = 18, max_chars: int = 1400) -> str:
        raw = str(feedback or "").strip()
        if not raw:
            return ""

        kept: list[str] = []
        fallback: list[str] = []
        seen: set[str] = set()
        preserve_following = 0

        def _append(line: str, bucket: list[str]) -> None:
            if line and line not in seen:
                seen.add(line)
                bucket.append(line)

        for raw_line in raw.splitlines():
            line = _sanitize_retry_feedback_for_blueprint_prompt(raw_line.strip())
            if not line:
                continue

            lowered = line.casefold()
            window = next((count for marker, count in _RETRY_FEEDBACK_SECTION_WINDOWS if marker in lowered), 0)
            if window:
                _append(line, kept)
                preserve_following = max(preserve_following, window)
                if len(kept) >= max_lines:
                    break
                continue

            if any(marker in lowered for marker in _RETRY_FEEDBACK_DROP_MARKERS):
                preserve_following = 0
                continue

            if preserve_following > 0:
                _append(line, kept)
                preserve_following -= 1
                if len(kept) >= max_lines:
                    break
                continue

            if any(marker in lowered for marker in _RETRY_FEEDBACK_PRIORITY_MARKERS):
                _append(line, kept)
                if len(kept) >= max_lines:
                    break
                continue

            if len(fallback) < 8:
                _append(line, fallback)

        selected = kept or fallback
        if not selected:
            return ""

        return smart_truncate(
            "\n".join(selected),
            max_chars=max_chars,
            head_chars=max(0, min(int(max_chars * 0.7), max_chars - 80)),
        )

    @staticmethod
    def _collect_episode_progression_replay_issues(
        candidate: dict,
        *,
        prev_blueprint: dict | None,
        constraint_block: dict | None,
    ) -> list[dict]:
        if not isinstance(candidate, dict) or not isinstance(constraint_block, dict):
            return []

        from .unified_blueprint_validator import UnifiedBlueprintValidator

        return UnifiedBlueprintValidator._collect_episode_progression_issues(
            blueprint=candidate,
            prev_blueprint=prev_blueprint,
            constraint_block=constraint_block,
        )

    def _run_blueprint_ensemble_workers(
        self,
        *,
        ep_num: int,
        active_strategies: list[dict],
        arc_focus: str,
        constraints_str: str,
        tactical_excerpt: str,
        prev_info: str,
        feedback: str,
        strategy_specific_feedback: str,
        rejected_strategy: str,
        protagonist_name: str,
        protagonist_config: dict | None,
        hud_context: str,
        genre: str,
        cache_name: str,
        prev_blueprint: dict | None,
        constraint_block: dict | None,
        fix_pack: dict | None,
        repair_contract: dict | None,
    ) -> tuple[list[dict], list[str]]:
        candidates: list[dict] = []
        worker_error_types: list[str] = []
        screened_disqualified_details: list[dict] = []
        timer_started_at = time.monotonic()

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                strategy_ordinals: dict[str, int] = {}
                for strategy_index, strategy in enumerate(active_strategies):
                    strategy_name = strategy["name"]
                    strategy_ordinals[strategy_name] = strategy_index
                    future = executor.submit(
                        self._generate_single,
                        ep_num=ep_num,
                        arc_focus=arc_focus,
                        constraints_str=constraints_str,
                        tactical_excerpt=tactical_excerpt,
                        prev_info=prev_info,
                        strategy=strategy,
                        feedback=feedback,
                        strategy_feedback=self._build_blueprint_strategy_feedback(
                            strategy_name,
                            rejected_strategy,
                            strategy_specific_feedback,
                        ),
                        protagonist_name=protagonist_name,
                        protagonist_config=protagonist_config,
                        hud_context=hud_context,
                        genre=genre,
                        cache_name=cache_name,
                        prev_blueprint=prev_blueprint,
                        constraint_block=constraint_block,
                        fix_pack=fix_pack,
                        repair_contract=repair_contract,
                    )
                    futures[future] = strategy_name
                    self._operator_log(
                        f"🔡 [Blueprint] 전략 '{strategy_name}' 생성 시작",
                        meta={"strategy": strategy_name},
                    )

                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy_name = futures[future]
                        try:
                            future_output = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            worker_error_type = None
                            result = future_output
                            if (
                                isinstance(future_output, tuple)
                                and len(future_output) == 2
                                and future_output[0] is None
                                and isinstance(future_output[1], str)
                            ):
                                result = future_output[0]
                                worker_error_type = future_output[1]
                            if worker_error_type:
                                worker_error_types.append(worker_error_type)
                                if worker_error_type == AgentErrorType.CANDIDATE_DISQUALIFIED:
                                    screened_disqualified_details.append(
                                        {
                                            "strategy": strategy_name,
                                            "scene_count": 0,
                                            "integrated_len": 0,
                                            "contract_reason": "screening_disqualified",
                                            "ordinal": strategy_ordinals.get(strategy_name, len(strategy_ordinals)),
                                        }
                                    )
                            if result and isinstance(result, dict):
                                result["_strategy"] = strategy_name
                                candidates.append(result)
                                logging.info(f" {strategy_name} 생성 완료")
                                self._operator_log(
                                    f"✅ [Blueprint] '{strategy_name}' 생성 완료 ({time.monotonic() - timer_started_at:.0f}초)",
                                    meta={
                                        "strategy": strategy_name,
                                        "elapsed_seconds": round(time.monotonic() - timer_started_at, 1),
                                    },
                                )
                        except FutureTimeoutError:
                            logging.warning(
                                f" [V61.3] {strategy_name} 개별 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)"
                            )
                            worker_error_types.append(AgentErrorType.TIMEOUT)
                            self._operator_log(
                                f"⚠️ [Blueprint] '{strategy_name}' 개별 타임아웃",
                                level="warning",
                                meta={"strategy": strategy_name, "timeout_seconds": self.SINGLE_CANDIDATE_TIMEOUT},
                            )
                        except Exception as exc:
                            logging.warning(f" {strategy_name} 실패: {str(exc)[:50]}")
                            worker_error_types.append(self._classify_error(exc))
                            self._operator_log(
                                f"⚠️ [Blueprint] '{strategy_name}' 실패",
                                level="warning",
                                meta={"strategy": strategy_name},
                            )
                except FutureTimeoutError:
                    logging.warning(
                        f" [V61.3] 블루프린트 전체 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
                    )
                except Exception as exc:
                    logging.warning(f" [V61.3] 병렬 루프 예외: {str(exc)[:80]}")
                finally:
                    for f in futures:
                        f.cancel()
        except Exception as exc:
            import traceback

            logging.error(f" [V61.3] 병렬 처리 불능 방어: {str(exc)[:100]}")
            logging.error(traceback.format_exc())

        try:
            logging.info(
                f"[PerfTimer:BlueprintEnsemble] bp_ep{ep_num}_ensemble={time.monotonic() - timer_started_at:.2f}s"
            )
        except Exception as exc:
            logging.debug("[BlueprintEnsemble] PerfTimer 기록 실패 (무시): %s", exc)

        if screened_disqualified_details:
            screened_disqualified_details.sort(key=lambda item: int(item.get("ordinal") or 0))
            self.last_disqualified_candidates = screened_disqualified_details

        return candidates, worker_error_types

    def _qualify_blueprint_candidates(self, candidates: list[dict]) -> tuple[list[dict], list[tuple[str, int, int]]]:
        qualified_candidates: list[dict] = []
        disqualified: list[tuple[str, int, int]] = []
        disqualified_details: list[dict] = []

        for candidate in candidates:
            strategy_name = candidate.get("_strategy", "unknown")
            scenes = candidate.get("scene_breakdown", {})
            integrated = candidate.get("integrated_scenario", "")
            integrated_len = len(integrated) if isinstance(integrated, str) else 0
            scene_gate_passed, scene_count, _, _ = evaluate_stage3_scene_cardinality(scenes, integrated)
            contract_reason = self._blueprint_contract_admission_reason(candidate)

            if (
                scene_gate_passed
                and integrated_len >= BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS
                and not contract_reason
            ):
                candidate["_qualified"] = True
                candidate["_scene_count"] = scene_count
                candidate["_length"] = integrated_len
                qualified_candidates.append(candidate)
                logging.info(f" {strategy_name}: 통과 (씬 {scene_count}개, {integrated_len}자)")
            else:
                disqualified.append((strategy_name, scene_count, integrated_len))
                disqualified_details.append(
                    {
                        "strategy": strategy_name,
                        "scene_count": scene_count,
                        "integrated_len": integrated_len,
                        "contract_reason": contract_reason or "",
                    }
                )
                reason_suffix = f", 사유={contract_reason}" if contract_reason else ""
                logging.info(f" {strategy_name}: 탈락 (씬 {scene_count}개, {integrated_len}자{reason_suffix})")

        existing_screened_disqualified = [
            item for item in (self.last_disqualified_candidates or []) if isinstance(item, dict)
        ]
        self.last_disqualified_candidates = existing_screened_disqualified + disqualified_details
        return qualified_candidates, disqualified

    def _finalize_blueprint_candidates(
        self,
        qualified_candidates: list[dict],
        disqualified: list[tuple[str, int, int]],
        *,
        ep_num: int,
        arc_data: dict,
        attempt_num: int | None = None,
        prompt_envelope_meta: dict | None = None,
    ) -> tuple[dict, list[dict]]:
        self._operator_log(
            f"🧥 [Blueprint] {len(qualified_candidates)}개 후보 통과 -> Director 선택 대기",
            meta={"qualified_candidates": len(qualified_candidates)},
        )

        for idx, candidate in enumerate(qualified_candidates):
            strategy_name = candidate.get("_strategy", "unknown")
            if attempt_num:
                snapshot_payload = {
                    key: value
                    for key, value in candidate.items()
                    if key not in {"_qualified", "_scene_count", "_length"}
                }
                snapshot_meta = snapshot_logged_artifact(
                    getattr(self.context, "current_project", None),
                    stage=3,
                    ep_num=ep_num,
                    arc_num=int((arc_data or {}).get("arc_no", 0) or 0) if isinstance(arc_data, dict) else 0,
                    attempt_num=max(1, int(attempt_num or 1)),
                    candidate_key=build_candidate_key(strategy=strategy_name, fallback="stage3_candidate"),
                    artifact_kind="candidate_blueprint",
                    payload=snapshot_payload,
                )
                if isinstance(snapshot_meta, dict):
                    candidate["_candidate_artifact_meta"] = snapshot_meta
            candidate["_ensemble_meta"] = {
                "candidate_index": idx,
                "strategy": strategy_name,
                "scene_count": candidate.get("_scene_count", 0),
                "length": candidate.get("_length", 0),
                "total_candidates": len(qualified_candidates),
                "disqualified": disqualified,
                "prompt_envelope": dict(prompt_envelope_meta or {}),
            }
            genre_strategy_contract = candidate.get("_genre_strategy_contract")
            if isinstance(genre_strategy_contract, dict) and genre_strategy_contract:
                candidate["_ensemble_meta"]["genre_strategy_contract"] = dict(genre_strategy_contract)
            candidate.pop("_strategy", None)
            candidate.pop("_qualified", None)
            candidate.pop("_scene_count", None)
            candidate.pop("_length", None)
            candidate.pop("_genre_strategy_contract", None)

        return qualified_candidates[0], qualified_candidates

    def generate_ensemble(
        self,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        feedback: str = "",
        strategy_specific_feedback: str = "",
        rejected_strategy: str = "",
        single_strategy: str = "",
        protagonist_name: str = "주인공",  # [V61] 주인공 이름 (필수!)
        protagonist_config: dict = None,  # [V60.90] 주인공 설정 (world_origin, incarnation_type)
        state_tracker=None,  # [V60.95] StateTracker (고밀도 HUD 전달)
        prev_blueprints: list[dict] | None = None,  # [V67] 이전 Blueprint 리스트
        prev_manuscripts_text: str = "",  # [V67] 이전 원고 전문 (모순 방지)
        fix_pack: dict | None = None,
        repair_contract: dict | None = None,
        attempt_num: int | None = None,
    ) -> tuple[dict | None, list[dict]]:
        """
        앙상블 Blueprint 생성

        Args:
            ep_num: 에피소드 번호
            arc_data: Arc 데이터
            constraint_block: 제약 조건 블록
            prev_blueprint: 직전 Blueprint
            feedback: 이전 REJECT 피드백
            protagonist_name: [V61] 주인공 이름 (환각 방지)
            protagonist_config: [V60.90] 주인공 설정 {world_origin, incarnation_type}
            state_tracker: [V60.95] StateTracker (고밀도 HUD - 17+ 필드, NPC 레지스트리)
            prev_blueprints: [V67] 이전 Blueprint 리스트 (전문 전달)
            prev_manuscripts_text: [V67] 이전 원고 전문 (모순 방지)

        Returns:
            (best_blueprint, all_candidates) - 최적 Blueprint와 모든 후보 리스트
        """
        context_bundle = self._prepare_blueprint_ensemble_context(
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            prev_manuscripts_text=prev_manuscripts_text,
            state_tracker=state_tracker,
        )
        # Source guard note: genre resolution still defaults through GenreTypes.WUXIA in the prep helper.

        logging.warning(f" [BPEnsemble] 3개 후보 병렬 생성 중... (주인공: {protagonist_name})")
        active_strategies = self._select_blueprint_ensemble_strategies(single_strategy)
        self.last_error_type = None
        self.last_error_types = []
        self.last_disqualified_candidates = []
        feedback_context = str(feedback or "").strip()
        repair_guidance = _build_stage3_retry_repair_guidance(fix_pack, repair_contract)
        if repair_guidance:
            feedback_context = (
                f"{repair_guidance}\n\n{feedback_context}".strip() if feedback_context else repair_guidance
            )
        feedback_context = self._compress_retry_feedback(feedback_context)
        prompt_envelope_meta = build_stage3_prompt_envelope_meta(
            constraints_str=context_bundle["constraints_str"],
            arc_focus=context_bundle["arc_focus"],
            prev_info=context_bundle["prev_info"],
            hud_context=context_bundle["hud_context"],
            feedback_context=feedback_context,
            archive_appendix_meta=context_bundle.get("archive_appendix_meta"),
        )
        strategy_feedback_chars = len(str(strategy_specific_feedback or ""))
        if strategy_feedback_chars > 0:
            prompt_envelope_meta["strategy_feedback_chars"] = strategy_feedback_chars
        genre_strategy_contracts = [
            {
                "strategy_name": contract.get("strategy_name"),
                "contract_id": contract.get("contract_id"),
                "contract_hash": contract.get("contract_hash"),
                "authority_level": contract.get("authority_level"),
            }
            for strategy in active_strategies
            if (contract := build_genre_strategy_contract(context_bundle["genre"], strategy.get("name", "")))
        ]
        if genre_strategy_contracts:
            prompt_envelope_meta["genre_strategy_contracts"] = genre_strategy_contracts
        top_lanes = ", ".join(
            f"{item['lane']}={item['chars']}" for item in (prompt_envelope_meta.get("dominant_lanes") or [])[:3]
        )
        self._operator_log(
            f"[Blueprint] prompt envelope total={prompt_envelope_meta.get('total_chars', 0)}자"
            + (f" ({top_lanes})" if top_lanes else ""),
            meta={"phase": "generate", "prompt_envelope": prompt_envelope_meta},
        )

        candidates, worker_error_types = self._run_blueprint_ensemble_workers(
            ep_num=ep_num,
            active_strategies=active_strategies,
            arc_focus=context_bundle["arc_focus"],
            constraints_str=context_bundle["constraints_str"],
            tactical_excerpt=context_bundle["tactical_excerpt"],
            prev_info=context_bundle["prev_info"],
            feedback=feedback,
            strategy_specific_feedback=strategy_specific_feedback,
            rejected_strategy=rejected_strategy,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            hud_context=context_bundle["hud_context"],
            genre=context_bundle["genre"],
            cache_name=context_bundle["cache_name"],
            prev_blueprint=prev_blueprint,
            constraint_block=context_bundle["constraint_block"],
            fix_pack=fix_pack,
            repair_contract=repair_contract,
        )

        self.last_error_types = list(worker_error_types)
        self.last_error_type = self._select_generate_error_type(worker_error_types)

        if not candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 생성 실패")
            return None, []

        qualified_candidates, disqualified = self._qualify_blueprint_candidates(candidates)
        if not qualified_candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 최소 기준 미달")
            return None, []

        logging.info(f" [BPEnsemble] {len(qualified_candidates)}개 후보 → Director 선택 대기")
        return self._finalize_blueprint_candidates(
            qualified_candidates,
            disqualified,
            ep_num=ep_num,
            arc_data=arc_data,
            attempt_num=attempt_num,
            prompt_envelope_meta=prompt_envelope_meta,
        )

    def _generate_single(
        self,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        tactical_excerpt: str,
        prev_info: str,
        strategy: dict,
        feedback: str = "",
        strategy_feedback: str = "",
        protagonist_name: str = "protagonist",
        protagonist_config: dict = None,
        hud_context: str = "",
        genre: str = GenreTypes.WUXIA,
        cache_name: str = "",
        prev_blueprint: dict | None = None,
        constraint_block: dict | None = None,
        fix_pack: dict | None = None,
        repair_contract: dict | None = None,
    ) -> dict | tuple[None, str] | None:
        """Generate a single blueprint candidate."""
        try:
            extra_directive = ""
            merged_feedback = feedback or ""
            repair_guidance = _build_stage3_retry_repair_guidance(fix_pack, repair_contract)
            if repair_guidance:
                merged_feedback = (
                    f"{repair_guidance}\n\n{merged_feedback}".strip() if merged_feedback else repair_guidance
                )
            if strategy_feedback:
                merged_feedback = (
                    f"{merged_feedback}\n\n[Strategy feedback]\n{strategy_feedback}"
                    if merged_feedback
                    else f"[Strategy feedback]\n{strategy_feedback}"
                )
            merged_feedback = self._compress_retry_feedback(merged_feedback)
            if merged_feedback:
                extra_directive = (
                    "\n\n"
                    "[CRITICAL] Director reject feedback\n"
                    f"{merged_feedback}\n"
                    "Apply the feedback directly. Repeating the same failure will be rejected again.\n"
                )

            protagonist_instructions = self._build_protagonist_instructions(protagonist_config, genre=genre)
            pov = protagonist_config.get("pov", "") if isinstance(protagonist_config, dict) else ""
            external_pov_insert_policy = (
                protagonist_config.get("external_pov_insert_policy", "") if isinstance(protagonist_config, dict) else ""
            )
            pov_constraint = build_external_pov_policy_constraint(
                pov,
                external_pov_insert_policy,
                genre=genre,
            )
            reader_feedback = self._build_reader_feedback_context(ep_num)
            prompt_bundle = self._build_blueprint_prompt_bundle(
                ep_num=ep_num,
                arc_focus=arc_focus,
                constraints_str=constraints_str,
                prev_info=prev_info,
                strategy=strategy,
                protagonist_name=protagonist_name,
                protagonist_instructions=protagonist_instructions,
                extra_directive=extra_directive,
                hud_context=hud_context,
                pov_constraint=pov_constraint,
                reader_feedback=reader_feedback,
                cache_name=cache_name,
                genre=genre,
            )
            prompt, full_prompt_fallback = prompt_bundle[:2]
            genre_strategy_contract = prompt_bundle[2] if len(prompt_bundle) > 2 else {}
            if not prompt:
                return None, AgentErrorType.UNKNOWN

            strategy_name = strategy.get("name", "unknown")
            self._operator_log(
                f"[Blueprint] '{strategy_name}' LLM request",
                meta={"strategy": strategy_name},
            )
            return self._request_blueprint_generation(
                cache_name=cache_name,
                prompt=prompt,
                full_prompt_fallback=full_prompt_fallback,
                strategy_name=strategy_name,
                genre=genre,
                genre_strategy_contract=genre_strategy_contract,
                tactical_excerpt=tactical_excerpt,
                prev_blueprint=prev_blueprint,
                constraint_block=constraint_block,
            )
        except Exception as e:
            import traceback

            logging.error("[BPEnsemble] _generate_single failed: %s", str(e)[:80])
            logging.error(traceback.format_exc())
            return None, self._classify_error(e)

    def _build_blueprint_prompt_bundle(
        self,
        *,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        prev_info: str,
        strategy: dict,
        protagonist_name: str,
        protagonist_instructions: str,
        extra_directive: str,
        hud_context: str,
        pov_constraint: str,
        reader_feedback: str,
        cache_name: str,
        genre: str = GenreTypes.WUXIA,
    ) -> tuple[str | None, str, dict]:
        work_retrieval_contract = ""
        try:
            guard = getattr(self.context, "guard", None)
            if guard and hasattr(guard, "get_retrieval_contract_prompt"):
                work_retrieval_contract = str(guard.get_retrieval_contract_prompt("blueprint") or "").strip()
        except Exception as exc:
            logging.debug("[BPEnsemble] work retrieval contract load failed: %s", exc)

        use_cached_context = bool(cache_name)
        cached_context_stub = "[context cached: refer to cached_content]"
        directive_text, genre_strategy_contract = _build_strategy_directive_for_genre(
            strategy,
            genre=genre,
            extra_directive=extra_directive,
        )
        strategy_directive = self._escape_braces(
            directive_text + (f"\n\n{work_retrieval_contract}" if work_retrieval_contract else "")
        )
        prompt = self._prompt_loader.load(
            "ensemble",
            "BLUEPRINT_GENERATION_PROMPT",
            strategy_display=strategy["display"],
            ep_num=ep_num,
            protagonist_name=self._escape_braces(protagonist_name),
            protagonist_instructions=self._escape_braces(protagonist_instructions),
            arc_focus=self._escape_braces(cached_context_stub if use_cached_context else arc_focus),
            constraints=self._escape_braces(cached_context_stub if use_cached_context else constraints_str),
            strategy_directive=strategy_directive,
            prev_info=self._escape_braces(cached_context_stub if use_cached_context else prev_info),
            hud_context=(
                self._escape_braces(cached_context_stub if use_cached_context else hud_context)
                if hud_context
                else "(no HUD context)"
            ),
            pov_constraint=self._escape_braces(pov_constraint),
            reader_feedback=self._escape_braces(reader_feedback) if reader_feedback else "",
        )
        full_prompt_fallback = prompt
        if use_cached_context:
            full_prompt_fallback = self._prompt_loader.load(
                "ensemble",
                "BLUEPRINT_GENERATION_PROMPT",
                strategy_display=strategy["display"],
                ep_num=ep_num,
                protagonist_name=self._escape_braces(protagonist_name),
                protagonist_instructions=self._escape_braces(protagonist_instructions),
                arc_focus=self._escape_braces(arc_focus),
                constraints=self._escape_braces(constraints_str),
                strategy_directive=strategy_directive,
                prev_info=self._escape_braces(prev_info),
                hud_context=self._escape_braces(hud_context) if hud_context else "(no HUD context)",
                pov_constraint=self._escape_braces(pov_constraint),
                reader_feedback=self._escape_braces(reader_feedback) if reader_feedback else "",
            )
            if not full_prompt_fallback:
                full_prompt_fallback = prompt
        if not prompt:
            logging.warning("[BPEnsemble] BLUEPRINT_GENERATION_PROMPT not found in prompt loader")
        return prompt, full_prompt_fallback or "", genre_strategy_contract

    def _request_blueprint_generation(
        self,
        *,
        cache_name: str,
        prompt: str,
        full_prompt_fallback: str,
        strategy_name: str,
        genre: str,
        genre_strategy_contract: dict | None = None,
        tactical_excerpt: str = "",
        prev_blueprint: dict | None = None,
        constraint_block: dict | None = None,
    ) -> dict | tuple[None, str]:
        try:
            response = self._ask_with_cached_context(
                cache_name=cache_name,
                prompt=prompt,
                temperature=0.7,
                thinking_level="medium",
                full_prompt_fallback=full_prompt_fallback,
                response_schema=BLUEPRINT_SCHEMA,
            )
        except Exception as exc:
            if not self._is_blueprint_schema_numeric_overflow(exc):
                raise
            self._operator_log(
                f"[Blueprint] '{strategy_name}' schema numeric overflow -> retry without response_schema",
                level="warning",
                meta={
                    "strategy": strategy_name,
                    "fallback_reason": "schema_numeric_overflow",
                },
            )
            response = self._ask_with_cached_context(
                cache_name=cache_name,
                prompt=prompt,
                temperature=0.7,
                thinking_level="medium",
                full_prompt_fallback=full_prompt_fallback,
                response_schema=None,
            )
        self._operator_log(
            f"[Blueprint] '{strategy_name}' response received ({len(response):,} chars)",
            meta={"strategy": strategy_name, "response_chars": len(response)},
        )
        result = self._extract_json_robust(response)
        if not isinstance(result, dict):
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE
        agent_error_type = self._error_type_from_agent_error_response(result)
        if agent_error_type:
            return None, agent_error_type
        if "scene_breakdown" not in result or "integrated_scenario" not in result:
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE
        sanitized = self._sanitize_blueprint_candidate(
            result,
            strategy_name=strategy_name,
            genre=genre,
            tactical_excerpt=tactical_excerpt,
            prev_blueprint=prev_blueprint,
            constraint_block=constraint_block,
        )
        if isinstance(sanitized, dict) and genre_strategy_contract:
            sanitized["_genre_strategy_contract"] = dict(genre_strategy_contract)
        return sanitized

    @staticmethod
    def _is_blueprint_schema_numeric_overflow(error: Exception) -> bool:
        message = str(error or "").lower()
        if not message:
            return False
        if "integer string conversion" in message:
            return True
        if "int_max_str_digits" in message:
            return True
        return "exceeds the limit" in message and "digits" in message and "integer" in message

    @staticmethod
    def _scene_has_meaningful_payload(scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False

        for field_name in ("summary", "description", "goal", "content"):
            if has_actionable_obligation_text(scene.get(field_name, "")):
                return True

        raw_events = scene.get("key_events", [])
        if isinstance(raw_events, str):
            raw_events = [raw_events]
        if isinstance(raw_events, list):
            if any(has_actionable_obligation_text(event) for event in raw_events):
                return True

        return False

    @staticmethod
    def _scene_has_actionable_key_events(scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False

        raw_events = scene.get("key_events", [])
        if isinstance(raw_events, str):
            raw_events = [raw_events]
        if not isinstance(raw_events, list):
            return False
        return any(has_actionable_obligation_text(event) for event in raw_events)

    @classmethod
    def _scene_is_contract_complete(cls, scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False
        return cls._scene_has_meaningful_payload(scene) and cls._scene_has_actionable_key_events(scene)

    @staticmethod
    def _has_meaningful_protagonist_state(protagonist_state: object) -> bool:
        if not isinstance(protagonist_state, dict):
            return False

        for value in protagonist_state.values():
            if has_meaningful_state_value(value):
                return True

        return False

    def _blueprint_contract_admission_reason(self, candidate: dict) -> str:
        opening_transition = candidate.get("opening_transition")
        if not isinstance(opening_transition, dict):
            return "missing_opening_transition"

        opening_type = str(opening_transition.get("type", "") or "").strip()
        if opening_type not in BLUEPRINT_OPENING_TRANSITION_TYPES:
            return "invalid_opening_transition"

        if not self._has_meaningful_protagonist_state(candidate.get("protagonist_state")):
            return "missing_protagonist_state"

        scene_breakdown = candidate.get("scene_breakdown")
        if isinstance(scene_breakdown, list):
            scene_iter = scene_breakdown
        elif isinstance(scene_breakdown, dict):
            scene_iter = scene_breakdown.values()
        else:
            return "missing_scene_breakdown"

        incomplete_scene_count = sum(1 for scene in scene_iter if not self._scene_is_contract_complete(scene))
        if incomplete_scene_count:
            return f"scene_completeness:{incomplete_scene_count}"

        informative_scene_count = sum(1 for scene in scene_iter if self._scene_has_meaningful_payload(scene))
        if informative_scene_count < 2:
            return f"insufficient_scene_payload:{informative_scene_count}"

        return ""

    @staticmethod
    def _collect_candidate_tactical_surface(candidate: dict) -> str:
        return collect_tactical_surface_text(candidate)

    def _detect_unauthorized_tactical_intrusion(self, candidate: dict, *, tactical_excerpt: str) -> str:
        authority_text = str(tactical_excerpt or "").strip().lower()
        if not authority_text:
            return ""
        if detect_tactical_intrusion_signature(authority_text):
            return ""

        candidate_text = self._collect_candidate_tactical_surface(candidate).lower()
        if not candidate_text:
            return ""

        signature = detect_tactical_intrusion_signature(candidate_text)
        if not signature:
            return ""
        entry_hits = signature.get("entry_hits", [])
        conflict_hits = signature.get("conflict_hits", [])
        return f"entry={entry_hits[0]}; conflict={conflict_hits[0]}"

    @staticmethod
    def _normalize_opening_transition_contract(candidate: dict, *, prev_blueprint: dict | None) -> str:
        """opening_transition contract 정규화 + 출처 라벨 반환.

        Return values:
          - ``""``: LLM이 이미 유효한 type을 직접 선언했고 정규화 불필요
          - ``"declared"``: LLM이 alias 형태로 선언, canonical type으로 정규화 후 mutation
          - ``"inferred"``: LLM 미선언, prev_blueprint/scene/time_flow 단서로 추론 + mutation
          - ``"missing"``: LLM 미선언 AND 추론 단서 부재 → cheap admission fail-closed 신호

        ``"missing"``은 cheap admission이 차단해야 하는 신호이며, 호출자는 이 값에 대해
        후보를 폐기해야 한다. T4.H1 (cheap gate disarmed by upstream normalization)을 닫는다.
        """
        raw_contract = candidate.get("opening_transition")
        declared_type = read_declared_opening_transition_type(candidate)
        if declared_type:
            raw_type = str(raw_contract.get("type", "") or "").strip() if isinstance(raw_contract, dict) else ""
            inferred_contract = apply_opening_transition_contract(candidate, prev_blueprint=prev_blueprint)
            inferred_type = (
                str(inferred_contract.get("type", "") or "").strip() if isinstance(inferred_contract, dict) else ""
            )
            if raw_type == declared_type and isinstance(raw_contract, dict):
                if inferred_type and inferred_type != declared_type:
                    normalized_contract = dict(raw_contract)
                    normalized_contract["type"] = inferred_type
                    if inferred_contract.get("signals") and not normalized_contract.get("signals"):
                        normalized_contract["signals"] = inferred_contract.get("signals")
                    candidate["opening_transition"] = normalized_contract
                    return "inferred"
                return ""
            normalized_contract = dict(raw_contract) if isinstance(raw_contract, dict) else {}
            normalized_contract["type"] = declared_type
            candidate["opening_transition"] = normalized_contract
            return "declared"

        raw_type = str(raw_contract.get("type", "") or "").strip() if isinstance(raw_contract, dict) else ""
        if raw_type in BLUEPRINT_OPENING_TRANSITION_TYPES:
            return ""

        inferred_contract = apply_opening_transition_contract(candidate, prev_blueprint=prev_blueprint)
        if inferred_contract:
            return "inferred"
        return "missing"

    @staticmethod
    def _normalize_hard_bound_opening_location(candidate: dict, *, constraint_block: dict | None) -> str:
        if not isinstance(candidate, dict) or not isinstance(constraint_block, dict):
            return ""
        episode_state_packet = constraint_block.get("episode_state_packet", {})
        opening_truth = (
            episode_state_packet.get("opening_truth")
            if isinstance(episode_state_packet, dict) and isinstance(episode_state_packet.get("opening_truth"), dict)
            else {}
        )
        opening_location = str(opening_truth.get("location", "") or "").strip()
        if not _should_hard_bind_opening_location(opening_truth) or not opening_location:
            return ""

        def _location_parts(raw: object) -> list[str]:
            text = re.sub(r"\s+", " ", str(raw or "").strip())
            if not text:
                return []
            parts = [part.strip() for part in re.split(r"\s*(?:,|/|\||>|→|및)\s*", text) if part.strip()]
            return parts or [text]

        def _is_same_terminal_location(actual: object) -> bool:
            actual_text = re.sub(r"\s+", " ", str(actual or "").strip())
            expected_text = re.sub(r"\s+", " ", opening_location)
            if not actual_text:
                return False
            if actual_text == expected_text:
                return True
            expected_parts = _location_parts(expected_text)
            actual_parts = _location_parts(actual_text)
            if not expected_parts or not actual_parts:
                return False
            return (
                len(actual_parts) >= 2
                and expected_parts[0] == actual_parts[0]
                and expected_parts[-1] == actual_parts[-1]
            )

        normalized_fields: list[str] = []
        start_location = str(candidate.get("start_location", candidate.get("location", "")) or "").strip()
        if start_location and start_location != opening_location and _is_same_terminal_location(start_location):
            candidate["start_location"] = opening_location
            normalized_fields.append("start_location")

        scenes = candidate.get("scene_breakdown", {})
        scene_one = scenes.get("scene_1") if isinstance(scenes, dict) else None
        if isinstance(scene_one, dict):
            scene_one_location = str(scene_one.get("location", "") or "").strip()
            if (
                scene_one_location
                and scene_one_location != opening_location
                and _is_same_terminal_location(scene_one_location)
            ):
                scene_one["location"] = opening_location
                normalized_fields.append("scene_1.location")

        return ", ".join(normalized_fields)

    @staticmethod
    def _resolve_prev_blueprint_time_flow_fallback(prev_blueprint: dict | None) -> str:
        if not isinstance(prev_blueprint, dict):
            return ""

        ending_state = prev_blueprint.get("ending_state", {})
        if isinstance(ending_state, dict):
            raw_timeline = ending_state.get("timeline", {})
            if isinstance(raw_timeline, dict):
                for key in ("표현", "expression", "text"):
                    value = str(raw_timeline.get(key, "") or "").strip()
                    if value:
                        return value
            else:
                value = str(raw_timeline or "").strip()
                if value:
                    return value

        return str(prev_blueprint.get("time_flow", "") or "").strip()

    @classmethod
    def _resolve_constraint_time_flow_fallback(cls, constraint_block: dict | None) -> str:
        if not isinstance(constraint_block, dict):
            return ""

        episode_progression = constraint_block.get("episode_progression_packet", {})
        if isinstance(episode_progression, dict):
            for raw in episode_progression.get("time_truths") or []:
                text = str(raw or "").strip()
                if not text:
                    continue
                match = re.search(
                    r"((?:\d{4}년\s*)?\d{1,2}월(?:\s*\d{1,2}일)?(?:\s*(?:초|중순|말))?(?:\s*(?:오전|오후|새벽|아침|점심|저녁|밤|심야|자정|정오))?)",
                    text,
                )
                if match:
                    return match.group(1).strip()

        episode_state_packet = constraint_block.get("episode_state_packet", {})
        opening_truth = episode_state_packet.get("opening_truth") if isinstance(episode_state_packet, dict) else {}
        if isinstance(opening_truth, dict):
            time_context = str(opening_truth.get("time_context", "") or "").strip()
            if re.search(r"\d{4}년|\d{1,2}월|오전|오후|새벽|아침|점심|저녁|밤|심야", time_context):
                return time_context

        continuity = constraint_block.get("continuity", {})
        if isinstance(continuity, dict):
            time_context = str(continuity.get("time_context", "") or "").strip()
            if re.search(r"\d{4}년|\d{1,2}월|오전|오후|새벽|아침|점심|저녁|밤|심야", time_context):
                return time_context

        return ""

    @classmethod
    def _normalize_direct_continuation_time_flow(
        cls,
        candidate: dict,
        *,
        prev_blueprint: dict | None,
        constraint_block: dict | None = None,
    ) -> str:
        """Fill a missing opening time anchor only for safe direct-continuation carryover.

        We keep ``opening_anchor`` structurally strict in the validator, but when the
        candidate already resolved to ``direct_continuation`` we can safely inherit the
        prior episode's terminal time anchor instead of forcing a replay/regenerate loop.
        """
        if not isinstance(candidate, dict):
            return ""
        if str(candidate.get("time_flow", "") or "").strip():
            return ""

        opening_transition = candidate.get("opening_transition", {})
        opening_type = (
            str(opening_transition.get("type", "") or "").strip() if isinstance(opening_transition, dict) else ""
        )
        if opening_type != "direct_continuation":
            return ""

        fallback = cls._resolve_constraint_time_flow_fallback(constraint_block)
        if not fallback:
            fallback = cls._resolve_prev_blueprint_time_flow_fallback(prev_blueprint)
        if not fallback:
            return ""

        candidate["time_flow"] = fallback
        return fallback

    @staticmethod
    def _normalize_terminal_arc_ending_timeline(candidate: dict, *, constraint_block: dict | None = None) -> str:
        if not isinstance(candidate, dict) or not isinstance(constraint_block, dict):
            return ""

        lock = constraint_block.get("terminal_timeline_lock", {})
        if not isinstance(lock, dict) or lock.get("mode") != "exact_terminal_match":
            return ""

        authoritative_text = str(lock.get("expression", "") or "").strip()
        authoritative_timeline = lock.get("timeline")
        authoritative_point = _extract_year_month_day(authoritative_timeline or authoritative_text)
        if not authoritative_text and authoritative_point is None:
            return ""

        ending_state = candidate.get("ending_state")
        if not isinstance(ending_state, dict):
            ending_state = {}
            candidate["ending_state"] = ending_state

        current_timeline = ending_state.get("timeline")
        if not current_timeline:
            ending_state["timeline"] = authoritative_timeline or {"표현": authoritative_text}
            return authoritative_text

        current_point = _extract_year_month_day(current_timeline)
        if authoritative_point is None:
            if not _year_month_conflicts(current_timeline, authoritative_text):
                ending_state["timeline"] = authoritative_timeline or {"표현": authoritative_text}
                return authoritative_text
            return ""

        if current_point is None:
            if not _year_month_conflicts(current_timeline, authoritative_text):
                ending_state["timeline"] = authoritative_timeline or {"표현": authoritative_text}
                return authoritative_text
            return ""

        same_year_month = current_point[:2] == authoritative_point[:2]
        day_is_underspecified = current_point[2] == 0
        exact_match = current_point == authoritative_point
        if same_year_month and (day_is_underspecified or exact_match):
            ending_state["timeline"] = authoritative_timeline or {"표현": authoritative_text}
            return authoritative_text

        return ""

    def _build_protagonist_instructions(self, protagonist_config: dict, genre: str = "wuxia") -> str:
        """
        [V60.90] protagonist_config 기반 프롬프트 지시사항 생성

        Args:
            protagonist_config: {world_origin: '원시인'|'현대인', incarnation_type: '회귀자'|'빙의자'|'환생자'}
            genre: [V61.3] 미리 로드한 장르 (thread-safety 위해 파라미터로 전달)

        Returns:
            프롬프트에 삽입할 지시사항 문자열
        """
        if not protagonist_config:
            return "║ (주인공 설정 정보 없음)"

        lines = []
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")

        # [V61.3] genre는 이제 파라미터로 전달받음 (DB 접근 제거 - thread-safety)

        # [V60.96] world_origin 기반 지시 (장르별 JSON 기반 PrimitiveGuard)
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                prim_section = get_primitive_constraint_section(protagonist_config, genre=genre, length="short")
                lines.append(f"║ {prim_section}")
            else:
                lines.append("║ ⚠️ [원시인 모드] 현대 용어 절대 금지!")
        else:
            lines.append("║ 📝 [현대인 모드] 주인공은 현대 사회를 알고 있음")

        # incarnation_type 기반 지시
        if incarnation_type == "회귀자":
            lines.append("║ 🔄 [회귀자] 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)")
        elif incarnation_type == "빙의자":
            lines.append("║ 👤 [빙의자] 원래 인물의 기억/관계를 의식")
        elif incarnation_type == "환생자":
            lines.append("║ 👶 [환생자] 전생의 기억이 있음")

        return "\n".join(lines) if lines else "║ (주인공 설정 정보 없음)"

    def _build_reader_feedback_context(self, ep_num: int) -> str:
        """[TF-I23/I24] 독자 만족도 + 호흡 분석 추이 → advisory 컨텍스트 생성.

        Python은 데이터만 수집/포맷. Blueprint LLM이 활용 여부 판단.
        """
        parts = []
        try:
            db = getattr(self.context, "db", None)
            if not db:
                return ""

            # ── I-23: 만족도 추이 ──
            try:
                sat_tags = db.get_recent_satisfaction_tags(before_ep=ep_num, lookback=5)
            except Exception as _e:
                logging.debug("[BlueprintEnsemble] sat_tags 조회 실패: %s", _e)
                sat_tags = []
            if sat_tags:
                parts.append("[독자 만족도 추이 (최근 5화)]")
                consecutive_frustration = 0
                for tag in sat_tags:
                    score = tag.get("satisfaction_score", 5)
                    frust = "불만" if tag.get("frustration_flag") else ""
                    agency = tag.get("protagonist_agency", "자력")
                    extras = ", ".join(filter(None, [agency, frust]))
                    parts.append(
                        f"  제{tag.get('ep_num', 0)}화: {tag.get('primary_tag', '미분류')} ({score}/10, {extras})"
                    )
                    if tag.get("frustration_flag"):
                        consecutive_frustration += 1
                    else:
                        consecutive_frustration = 0
                if consecutive_frustration >= 2:
                    parts.append("  ⚠️ 연속 좌절감 — 주인공 능동적 활약 씬 필수")

            # ── I-24: 호흡 분석 추이 ──
            try:
                pacing_records = db.get_recent_pacing_records(before_ep=ep_num, lookback=5)
            except Exception as _e:
                logging.debug("[BlueprintEnsemble] pacing_records 조회 실패: %s", _e)
                pacing_records = []
            if pacing_records:
                parts.append("[호흡 분석 추이 (최근 5화)]")
                for rec in pacing_records:
                    _dr = rec.get("dialogue_ratio")
                    dial_pct = f"{_dr:.0%}" if _dr is not None else "0%"
                    parts.append(
                        f"  제{rec.get('ep_num', 0)}화: 점수 {rec.get('pacing_score', 0)}/100, "
                        f"대화 {dial_pct}, 장면전환 {rec.get('scene_break_count', 0)}회"
                    )
                # 최근 평균 호흡 경고
                avg_dial = sum(r.get("dialogue_ratio") or 0 for r in pacing_records) / len(pacing_records)
                avg_score = sum(r.get("pacing_score") or 50 for r in pacing_records) / len(pacing_records)
                if avg_dial < 0.15:
                    parts.append("  ⚠️ 대화 비율 저조 — 캐릭터 상호작용 씬 추가 고려")
                if avg_score < 40:
                    parts.append("  ⚠️ 호흡 점수 낮음 — 문장 길이 다양화 및 장면 전환 고려")

        except Exception as e:
            logging.warning("[TF-I23/I24] 독자 피드백 컨텍스트 생성 실패: %s", e)
            return ""

        return "\n".join(parts) if parts else ""

    def _format_constraints(self, constraint_block: dict, *, genre: str = "wuxia") -> str:
        """Format blueprint constraints with explicit 4-tier authority banding.

        Band hierarchy (conflict resolution order):
          IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY
        """
        episode_state_packet = (
            constraint_block.get("episode_state_packet")
            if isinstance(constraint_block.get("episode_state_packet"), dict)
            else {}
        )
        # ── Band 1: IMMUTABLE (확정 사실, 변경 불가) ──
        immutable_lines: list[str] = []

        fact_lock = constraint_block.get("fact_lock_packet", {})
        if isinstance(fact_lock, dict) and fact_lock.get("anchors"):
            immutable_lines.append("[FACT-LOCK: 확정 사실 — 변경 금지]")
            for anchor in fact_lock["anchors"]:
                if isinstance(anchor, dict) and anchor.get("fact"):
                    cat = anchor.get("category", "")
                    prefix = f"[{cat}] " if cat else ""
                    immutable_lines.append(f"  - {prefix}{anchor['fact']}")

        capital_pkt = constraint_block.get("capital_continuity_packet", {})
        if isinstance(capital_pkt, dict) and capital_pkt.get("fields"):
            immutable_lines.append("[CAPITAL-LOCK: 자본 상태 연속성 — 변경 금지]")
            for field in capital_pkt["fields"]:
                if isinstance(field, dict) and field.get("label") and field.get("value"):
                    immutable_lines.append(f"  - {field['label']}: {field['value']}")

        # ── Band 2: HARD CONSTRAINT (필수 준수, 위반 시 REJECT) ──
        hard_lines: list[str] = []

        must_focus = constraint_block.get("must_focus", {})
        if isinstance(must_focus, dict):
            arc_title = str(must_focus.get("arc_title", "") or "").strip()
            if arc_title:
                hard_lines.append("[이번 화 제목]")
                hard_lines.append(f"  {_fit_compact_context(arc_title, 120)}")
            key_events = must_focus.get("key_events") or []
            if isinstance(key_events, list) and key_events:
                hard_lines.append("[이번 화 필수 이벤트]")
                for event in key_events[:5]:
                    text = str(event or "").strip()
                    if text:
                        hard_lines.append(f"  - {_fit_compact_context(text, 120)}")
            content = str(must_focus.get("content", "") or "").strip()
            if content and not key_events:
                hard_lines.append("[이번 화 핵심 초점]")
                hard_lines.append(f"  {_fit_compact_context(content, 500)}")

        stop_line = constraint_block.get("stop_line", {})
        if isinstance(stop_line, dict) and not stop_line.get("is_arc_finale"):
            if stop_line.get("content"):
                hard_lines.append("[Stop Line]")
                _next_ep = stop_line.get("next_ep", "?")
                hard_lines.append(
                    f"  [제{_next_ep}화] 다음 화 내용 금지: {_fit_compact_context(stop_line['content'], 150)}"
                )
                for _fe in stop_line.get("future_eps") or []:
                    if isinstance(_fe, dict) and _fe.get("content"):
                        hard_lines.append(
                            f"  [제{_fe.get('ep', '?')}화] 금지: {_fit_compact_context(_fe['content'], 150)}"
                        )
                _cur_ep = constraint_block.get("ep_num", "?")
                hard_lines.append(
                    f"  *** 제{_cur_ep}화 이후 모든 에피소드 사건/NPC/전개를 "
                    f"이번 화에서 소비하거나 언급하면 즉시 REJECT ***"
                )

        terminal_timeline_lock = constraint_block.get("terminal_timeline_lock", {})
        if isinstance(terminal_timeline_lock, dict) and terminal_timeline_lock.get("mode") == "exact_terminal_match":
            end_text = str(terminal_timeline_lock.get("expression", "") or "").strip()
            if not end_text and isinstance(terminal_timeline_lock.get("timeline"), dict):
                end_text = json.dumps(terminal_timeline_lock["timeline"], ensure_ascii=False)
            if end_text:
                hard_lines.append("[TERMINAL TIMELINE LOCK - Arc 마지막 화]")
                hard_lines.append(
                    "  - 이번 화는 Arc 마지막 화입니다. ending_state.timeline은 아래 종료 시점과 정확히 맞아야 합니다."
                )
                hard_lines.append(f"  - authoritative arc end: {_fit_compact_context(end_text, 160)}")
                hard_lines.append("  - 같은 월/같은 날의 vague 표현만 두고 정확한 종료 시점을 비워 두지 마세요.")

        progression_pkt = constraint_block.get("episode_progression_packet", {})
        if isinstance(progression_pkt, dict):
            progression_lines: list[str] = []
            for truth in progression_pkt.get("time_truths", [])[:3]:
                text = str(truth or "").strip()
                if text:
                    progression_lines.append(f"  - 시간 truth: {_fit_compact_context(text, 120)}")
            for truth in progression_pkt.get("institution_truths", [])[:4]:
                text = str(truth or "").strip()
                if text:
                    progression_lines.append(f"  - 기관 truth: {_fit_compact_context(text, 80)}")
            blocked_families = progression_pkt.get("blocked_scene_families", [])
            if isinstance(blocked_families, list) and blocked_families:
                progression_lines.append(
                    "  - 직전 화에 이미 소비한 scene family를 같은 장소/같은 인물축으로 다시 재연하지 말 것"
                )
                for family in blocked_families[:3]:
                    if not isinstance(family, dict):
                        continue
                    label = str(family.get("label", "") or "").strip()
                    location = str(family.get("location", "") or "").strip()
                    scene_type = str(family.get("type", "") or "").strip()
                    characters = family.get("characters", [])
                    char_text = ", ".join(str(item or "").strip() for item in characters if str(item or "").strip())
                    parts = []
                    if label:
                        parts.append(_fit_compact_context(label, 50))
                    if location:
                        parts.append(f"장소:{_fit_compact_context(location, 60)}")
                    if char_text:
                        parts.append(f"등장:{_fit_compact_context(char_text, 60)}")
                    if scene_type:
                        parts.append(f"type:{_fit_compact_context(scene_type, 24)}")
                    if parts:
                        progression_lines.append(f"    · {' | '.join(parts)}")
                progression_lines.append(
                    "  - MUST_FOCUS의 새 사건 축으로 전진하고 직전 대치 장면을 길게 반복하지 말 것"
                )
            completed_events = progression_pkt.get("completed_prior_events", [])
            if isinstance(completed_events, list) and completed_events:
                progression_lines.append(
                    "  - 직전 화에서 이미 완료된 사건을 scene_1/live objective로 다시 재연하지 말 것"
                )
                for event_row in completed_events[:3]:
                    if not isinstance(event_row, dict):
                        continue
                    location = str(event_row.get("location", "") or "").strip()
                    events = [
                        str(item or "").strip() for item in (event_row.get("events") or []) if str(item or "").strip()
                    ]
                    if not events:
                        continue
                    prefix = f"장소:{_fit_compact_context(location, 50)} | " if location else ""
                    progression_lines.append(f"    · {prefix}{_fit_compact_context('; '.join(events[:2]), 120)}")
            next_gate_strength = progression_pkt.get("next_gate_strength_mode", {})
            if isinstance(next_gate_strength, dict) and next_gate_strength.get("mode") == "foreshadow_only":
                introduced = ", ".join(
                    str(item or "").strip() for item in next_gate_strength.get("introduced_target_families", [])[:3]
                )
                reserved = ", ".join(
                    str(item or "").strip() for item in next_gate_strength.get("reserved_target_families", [])[:3]
                )
                progression_lines.append(
                    "  - 새 타깃 handoff는 foreshadow 수준으로만 남기고, 현재 미해결 타깃 압박을 먼저 정리할 것"
                )
                if introduced or reserved:
                    progression_lines.append(
                        "    · "
                        + _fit_compact_context(
                            f"introduced={introduced or '-'} / reserved={reserved or '-'}",
                            120,
                        )
                    )
            lawful_window = progression_pkt.get("lawful_repetition_window", {})
            if isinstance(lawful_window, dict) and lawful_window.get("mode") == "allow_escalated_repeat":
                progression_lines.append(
                    "  - 같은 장소/같은 상대라도 장면 목표나 권력 위계가 달라지면 lawful repetition으로 전진 가능"
                )
                if lawful_window.get("allow_same_channel_if_decision_escalates"):
                    progression_lines.append(
                        "    · 동일 통화/동일 채널도 결정·단언·압박 수위가 올라가면 replay로만 보지 말 것"
                    )
            surface_guidance = progression_pkt.get("surface_guidance", [])
            if isinstance(surface_guidance, list) and surface_guidance:
                progression_lines.append("  - 같은 축 반복 방지용 진행 surface 가이드")
                for guidance in surface_guidance[:6]:
                    text = str(guidance or "").strip()
                    if text:
                        progression_lines.append(f"    · {_fit_compact_context(text, 120)}")
            future_reservations = progression_pkt.get("future_beat_reservations", [])
            if isinstance(future_reservations, list) and future_reservations:
                progression_lines.append("  - 다음 화 reserved beat 선소비 금지")
                for guidance in future_reservations[:4]:
                    text = str(guidance or "").strip()
                    if text:
                        progression_lines.append(f"    · {_fit_compact_context(text, 120)}")
            if progression_lines:
                hard_lines.append("[Episode Progression - 직전 화 replay 금지]")
                hard_lines.extend(progression_lines)

        arc_summary = constraint_block.get("arc_constraint_summary")
        if arc_summary:
            hard_lines.append("[Arc 제약 - MUST NOT DRIFT]")
            if isinstance(arc_summary, str):
                hard_lines.append(f"  {_fit_compact_context(arc_summary, 500)}")
            elif isinstance(arc_summary, dict):
                for key, value in list(arc_summary.items())[:10]:
                    hard_lines.append(f"  {key}: {_fit_compact_context(value, 100)}")

        # ── Band 3: EXPECTED CONTINUITY (계승 필수, 불일치 시 경고) ──
        continuity_lines: list[str] = []

        if episode_state_packet:
            continuity_lines.extend(_format_episode_state_packet_lines(episode_state_packet))

        continuity = constraint_block.get("continuity", {})
        if isinstance(continuity, dict):
            _cont_items: list[str] = []
            if continuity.get("location"):
                _cont_items.append(f"  이전 종료 위치: {_fit_compact_context(continuity['location'], 120)}")
            if continuity.get("time_context"):
                _cont_items.append(f"  시간 맥락: {_fit_compact_context(continuity['time_context'], 100)}")
            conflicts = continuity.get("ongoing_conflicts") or []
            if isinstance(conflicts, list):
                for item in conflicts[:5]:
                    text = str(item or "").strip()
                    if text:
                        _cont_items.append(f"  - 진행 중 갈등: {_fit_compact_context(text, 80)}")
            elif conflicts:
                _cont_items.append(f"  - 진행 중 갈등: {_fit_compact_context(conflicts, 200)}")
            active = continuity.get("active_characters") or []
            if isinstance(active, list) and active:
                names = [
                    _fit_compact_context(str(item or "").strip(), 20) for item in active[:10] if str(item or "").strip()
                ]
                if names:
                    _cont_items.append(f"  등장 캐릭터: {', '.join(names)}")
            elif active:
                _cont_items.append(f"  등장 캐릭터: {_fit_compact_context(active, 200)}")
            if _cont_items:
                continuity_lines.append("[연속성]")
                continuity_lines.extend(_cont_items)

        inherited = constraint_block.get("inherited_state", {})
        if isinstance(inherited, dict):
            inherited_items: list[str] = []
            equip = inherited.get("equipment")
            if equip:
                if isinstance(equip, list):
                    equip = ", ".join(str(x) if not isinstance(x, dict) else str(x.get("name", x)) for x in equip[:5])
                inherited_items.append(f"  장비: {_fit_compact_context(equip, 200)}")
            injuries = inherited.get("injuries")
            if injuries:
                if isinstance(injuries, list):
                    inherited_items.append(f"  부상: {', '.join(_fit_compact_context(i, 40) for i in injuries[:5])}")
                else:
                    inherited_items.append(f"  부상: {_fit_compact_context(injuries, 200)}")
            if genre == "wuxia" and inherited.get("internal_energy") is not None:
                inherited_items.append(f"  내공/에너지: {_fit_compact_context(inherited['internal_energy'], 80)}")
            if inherited.get("mood"):
                inherited_items.append(f"  심리 상태: {_fit_compact_context(inherited['mood'], 100)}")
            if inherited_items:
                continuity_lines.append("[계승 상태]")
                continuity_lines.extend(inherited_items)

        # ── Band 4: ADVISORY (참고용, 필수 아님) ──
        advisory_lines: list[str] = []

        sc_summary = constraint_block.get("state_changes_summary")
        if sc_summary:
            advisory_lines.append("[상태 변경 요약]")
            if isinstance(sc_summary, str):
                advisory_lines.append(f"  {_fit_compact_context(sc_summary, 800)}")
            elif isinstance(sc_summary, dict):
                deaths = sc_summary.get("npc_deaths", [])
                if deaths:
                    names = [
                        d.get("name", d.get("npc", str(d))) if isinstance(d, dict) else str(d) for d in deaths[:10]
                    ]
                    advisory_lines.append(f"  사망 NPC: {', '.join(names)}")
                skills = sc_summary.get("skill_acquisitions", [])
                if skills:
                    names = [
                        s.get("name", s.get("skill", str(s))) if isinstance(s, dict) else str(s) for s in skills[:10]
                    ]
                    advisory_lines.append(f"  획득 기술: {', '.join(names)}")
                resolved = sc_summary.get("resolved_plots", [])
                if resolved:
                    names = [
                        r.get("plot", r.get("description", str(r))) if isinstance(r, dict) else str(r)
                        for r in resolved[:10]
                    ]
                    advisory_lines.append(f"  해결 플롯: {', '.join(names)}")
                permanent = sc_summary.get("permanent_injuries", [])
                if permanent:
                    descs = [
                        _fit_compact_context(p, 50)
                        if not isinstance(p, dict)
                        else _fit_compact_context(p.get("description", str(p)), 50)
                        for p in permanent[:5]
                    ]
                    advisory_lines.append(f"  영구 부상: {', '.join(descs)}")

        semantic_carryover = constraint_block.get("semantic_carryover")
        if isinstance(semantic_carryover, dict) and semantic_carryover:
            advisory_lines.append("[Future Semantic Advisory — 이번 화 obligation 아님]")
            advisory_lines.append(
                "  아래 항목은 미래 화/관계 맥락 참고용이다. 이번 화에서 반드시 모두 소비할 필요는 없다."
            )
            for entry in semantic_carryover.get("relationship_rationale", []) or []:
                if not isinstance(entry, dict):
                    continue
                npc = str(entry.get("npc", "") or "").strip() or "?"
                cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()
                if cue:
                    advisory_lines.append(f"  relationship {npc}: {_fit_compact_context(cue, 120)}")
            # [W2] growth_justification: suppressed (arc-end achievement fuel)
            # [W2] continuity_checkpoints: suppressed (arc-end completion state)
            for anchor in (semantic_carryover.get("foreshadow_anchors", []) or [])[:3]:
                text = str(anchor or "").strip()
                if text:
                    advisory_lines.append(f"  [미래 복선 참고용] foreshadow: {_fit_compact_context(text, 120)}")

        lines = [
            "[\uc81c\uc57d \uc6b0\uc120\uc21c\uc704: IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY]",
            "\ucda9\ub3cc \uc2dc \uc0c1\uc704 \ub4f1\uae09\uc774 \ud558\uc704 \ub4f1\uae09\uc744 \ubb34\uc870\uac74 \uc6b0\uc120\ud569\ub2c8\ub2e4.",
            "",
        ]
        for header, band_lines in (
            (
                "\u2550\u2550\u2550 IMMUTABLE (\ud655\uc815 \uc0ac\uc2e4 \u2014 \uc808\ub300 \ubcc0\uacbd \uae08\uc9c0) \u2550\u2550\u2550",
                immutable_lines,
            ),
            (
                "\u2500\u2500\u2500 HARD CONSTRAINT (\ud544\uc218 \uc900\uc218 \u2014 \uc704\ubc18 \uc2dc REJECT) \u2500\u2500\u2500",
                hard_lines,
            ),
            (
                "\u2500\u2500\u2500 EXPECTED CONTINUITY (\uacc4\uc2b9 \uae30\ub300 \u2014 \ubd88\uc77c\uce58 \uc2dc \uacbd\uace0) \u2500\u2500\u2500",
                continuity_lines,
            ),
            (
                "\u00b7\u00b7\u00b7 ADVISORY (\ucc38\uace0\uc6a9 \u2014 \ud544\uc218 \uc544\ub2d8) \u00b7\u00b7\u00b7",
                advisory_lines,
            ),
        ):
            _append_constraint_section(lines, header, band_lines)
        if lines[-1] == "":
            lines.pop()

        return "\n".join(lines) if lines else "(constraints unavailable)"

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (blueprint variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="blueprint")

    def _format_prev_info(
        self,
        prev_blueprint: dict | None,
        *,
        authoritative_time_context: str = "",
    ) -> str:
        """이전 Blueprint 정보 포맷팅 (레거시 - 단일 Blueprint)"""
        if not prev_blueprint:
            return "(첫 에피소드 - 이전 화 없음)"

        lines = []

        # [V61.5] 이전 에피소드 종료 상태 섹션 강화
        lines.append("━━━━━ [V61.5] 이전 에피소드 종료 상태 ━━━━━")
        lines.append("⚠️ 아래 상태에서 시작해야 합니다. 위치/시점 불연속 금지!")

        ending_hook = prev_blueprint.get("ending_hook", "")
        if ending_hook:
            lines.append(f"엔딩 훅: {ending_hook}")

        end_location = prev_blueprint.get("end_location", "")
        if end_location:
            lines.append(f"종료 위치: {end_location}")

        time_flow = prev_blueprint.get("time_flow", "")
        normalized_authoritative_time = str(authoritative_time_context or "").strip()

        # [V61.5] ending_state 필드 (있으면)
        ending_state = prev_blueprint.get("ending_state", {})
        ending_timeline_text = ""
        if isinstance(ending_state, dict) and ending_state.get("timeline"):
            tl = ending_state["timeline"]
            if isinstance(tl, dict):
                ending_timeline_text = ", ".join(f"{k}:{v}" for k, v in tl.items())
            else:
                ending_timeline_text = str(tl)

        time_conflict = bool(normalized_authoritative_time) and (
            _year_month_conflicts(time_flow, normalized_authoritative_time)
            or _year_month_conflicts(ending_timeline_text, normalized_authoritative_time)
        )
        if normalized_authoritative_time:
            lines.append(f"현재 화 opening time truth: {normalized_authoritative_time}")
            if time_conflict:
                lines.append(
                    "⚠️ 직전 Blueprint의 시간 표기는 현재 화 opening truth와 충돌하여 direct-prev 권위에서 제외됨"
                )
        if time_flow and not time_conflict:
            lines.append(f"시간 흐름: {time_flow}")

        if ending_state:
            if ending_state.get("location"):
                lines.append(f"종료 위치 (상세): {ending_state['location']}")
            if ending_timeline_text and not time_conflict:
                lines.append(f"종료 시점: {ending_timeline_text}")
            if ending_state.get("protagonist_status"):
                lines.append(f"주인공 상태: {ending_state['protagonist_status']}")

        protag_state = prev_blueprint.get("protagonist_state", {})
        if protag_state:
            mood = protag_state.get("mood", "")
            injuries = protag_state.get("injuries", "")
            equipment = protag_state.get("equipment", [])
            if mood:
                lines.append(f"감정 상태: {mood}")
            if injuries and injuries != "없음":
                lines.append(f"부상: {injuries}")
            if equipment:
                equip_str = (
                    ", ".join(str(x) if isinstance(x, dict) else x for x in equipment[:5])
                    if isinstance(equipment, list)
                    else str(equipment)
                )
                lines.append(f"소지품: {equip_str}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(lines) if len(lines) > 3 else "(이전 화 정보 없음)"

    @staticmethod
    def _genre_allows_explicit_system_ui(genre: str) -> bool:
        return genre in {GenreTypes.HUNTER, GenreTypes.FANTASY}

    def _detect_blueprint_text_contamination(self, text: object, *, allow_system_ui: bool) -> str | None:
        raw = str(text or "").strip()
        if not raw:
            return None

        lowered = raw.casefold()
        if any(marker in lowered for marker in _BLUEPRINT_META_RECAP_MARKERS):
            return "meta_recap_register"
        if not allow_system_ui and any(marker in lowered for marker in _BLUEPRINT_SYSTEM_UI_MARKERS):
            return "system_ui_register"
        return None

    def _sanitize_blueprint_candidate(
        self,
        candidate: dict,
        *,
        strategy_name: str,
        genre: str,
        tactical_excerpt: str = "",
        prev_blueprint: dict | None = None,
        constraint_block: dict | None = None,
    ) -> dict | tuple[None, str]:
        allow_system_ui = self._genre_allows_explicit_system_ui(genre)
        integrated_reason = self._detect_blueprint_text_contamination(
            candidate.get("integrated_scenario", ""),
            allow_system_ui=allow_system_ui,
        )
        if integrated_reason:
            logging.warning(
                "[BPEnsemble] rejecting contaminated blueprint candidate (%s): %s",
                strategy_name,
                integrated_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' 오염 후보 폐기",
                level="warning",
                meta={"strategy": strategy_name, "reason": integrated_reason, "event_kind": "candidate_screening"},
            )
            return None, AgentErrorType.CANDIDATE_DISQUALIFIED

        scene_breakdown = candidate.get("scene_breakdown")
        if isinstance(scene_breakdown, list):
            scene_iter = [(f"scene_{idx}", scene) for idx, scene in enumerate(scene_breakdown, start=1)]
        elif isinstance(scene_breakdown, dict):
            scene_iter = list(scene_breakdown.items())
        else:
            scene_iter = []

        sanitized_key_events = 0
        for scene_key, scene in scene_iter:
            if not isinstance(scene, dict):
                continue

            for field_name in ("summary", "description", "goal", "content"):
                reason = self._detect_blueprint_text_contamination(
                    scene.get(field_name, ""),
                    allow_system_ui=allow_system_ui,
                )
                if reason:
                    logging.warning(
                        "[BPEnsemble] rejecting contaminated scene field (%s/%s/%s): %s",
                        strategy_name,
                        scene_key,
                        field_name,
                        reason,
                    )
                    self._operator_log(
                        f"⚠️ [Blueprint] '{strategy_name}' 오염 씬 폐기",
                        level="warning",
                        meta={
                            "strategy": strategy_name,
                            "scene": scene_key,
                            "field": field_name,
                            "reason": reason,
                            "event_kind": "candidate_screening",
                        },
                    )
                    return None, AgentErrorType.CANDIDATE_DISQUALIFIED

            raw_events = scene.get("key_events", [])
            if isinstance(raw_events, str):
                raw_events = [raw_events]
            if not isinstance(raw_events, list):
                continue

            filtered_events = []
            dropped_events = 0
            for event in raw_events:
                reason = self._detect_blueprint_text_contamination(event, allow_system_ui=allow_system_ui)
                if reason:
                    dropped_events += 1
                    continue
                filtered_events.append(event)

            if dropped_events and not filtered_events:
                logging.warning(
                    "[BPEnsemble] rejecting blueprint candidate (%s): scene %s lost all key_events to contamination",
                    strategy_name,
                    scene_key,
                )
                self._operator_log(
                    f"⚠️ [Blueprint] '{strategy_name}' key_events 오염 후보 폐기",
                    level="warning",
                    meta={"strategy": strategy_name, "scene": scene_key, "event_kind": "candidate_screening"},
                )
                return None, AgentErrorType.CANDIDATE_DISQUALIFIED

            if dropped_events:
                scene["key_events"] = filtered_events
                sanitized_key_events += dropped_events

        if sanitized_key_events:
            logging.info(
                "[BPEnsemble] sanitized %d contaminated key_events from %s",
                sanitized_key_events,
                strategy_name,
            )
            self._operator_log(
                f"🧹 [Blueprint] '{strategy_name}' key_events 오염 정리",
                meta={"strategy": strategy_name, "removed_key_events": sanitized_key_events},
            )

        opening_transition_route = self._normalize_opening_transition_contract(
            candidate,
            prev_blueprint=prev_blueprint,
        )
        if opening_transition_route == "missing":
            # T4.H1: cheap gate disarmed 닫기 — LLM이 opening_transition을 선언하지 않았고
            # prev_blueprint/scene/time_flow에서도 추론할 단서가 없으면 즉시 폐기.
            # 이전에는 normalizer가 빈 string을 반환해 admission gate가 통과시켜 버렸다.
            logging.warning(
                "[BPEnsemble] rejecting candidate (%s): opening_transition pure omission with no inference anchor",
                strategy_name,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' opening_transition 부재 + 추론 불가 후보 폐기",
                level="warning",
                meta={
                    "strategy": strategy_name,
                    "reason": "missing_opening_transition_pure_omission",
                    "event_kind": "candidate_screening",
                },
            )
            return None, AgentErrorType.CANDIDATE_DISQUALIFIED
        if opening_transition_route in ("declared", "inferred"):
            logging.info(
                "[BPEnsemble] normalized opening_transition contract for %s via %s path",
                strategy_name,
                opening_transition_route,
            )
            self._operator_log(
                f"[Blueprint] '{strategy_name}' opening_transition contract normalized",
                meta={"strategy": strategy_name, "route": opening_transition_route},
            )
        normalized_opening_location = self._normalize_hard_bound_opening_location(
            candidate,
            constraint_block=constraint_block,
        )
        if normalized_opening_location:
            logging.info(
                "[BPEnsemble] normalized hard-bound opening location for %s: %s",
                strategy_name,
                normalized_opening_location,
            )
            self._operator_log(
                f"[Blueprint] '{strategy_name}' hard-bound opening location normalized",
                meta={"strategy": strategy_name, "fields": normalized_opening_location},
            )
        inherited_time_flow = self._normalize_direct_continuation_time_flow(
            candidate,
            prev_blueprint=prev_blueprint,
            constraint_block=constraint_block,
        )
        if inherited_time_flow:
            logging.info(
                "[BPEnsemble] inherited direct-continuation time_flow for %s: %s",
                strategy_name,
                inherited_time_flow,
            )
            self._operator_log(
                f"[Blueprint] '{strategy_name}' direct_continuation time_flow inherited",
                meta={"strategy": strategy_name, "time_flow": inherited_time_flow[:120]},
            )
        normalized_terminal_timeline = self._normalize_terminal_arc_ending_timeline(
            candidate,
            constraint_block=constraint_block,
        )
        if normalized_terminal_timeline:
            logging.info(
                "[BPEnsemble] normalized terminal arc ending timeline for %s: %s",
                strategy_name,
                normalized_terminal_timeline,
            )
            self._operator_log(
                f"[Blueprint] '{strategy_name}' terminal ending timeline normalized",
                meta={"strategy": strategy_name, "timeline": normalized_terminal_timeline[:120]},
            )

        tactical_intrusion_reason = self._detect_unauthorized_tactical_intrusion(
            candidate,
            tactical_excerpt=tactical_excerpt,
        )
        if tactical_intrusion_reason:
            logging.warning(
                "[BPEnsemble] rejecting unauthorized tactical intrusion candidate (%s): %s",
                strategy_name,
                tactical_intrusion_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' tactical authority 미달 후보 폐기",
                level="warning",
                meta={
                    "strategy": strategy_name,
                    "reason": tactical_intrusion_reason,
                    "event_kind": "candidate_screening",
                },
            )
            return None, AgentErrorType.CANDIDATE_DISQUALIFIED

        progression_issues = self._collect_episode_progression_replay_issues(
            candidate,
            prev_blueprint=prev_blueprint,
            constraint_block=constraint_block,
        )
        if progression_issues:
            issue = progression_issues[0]
            replay_reason = str(issue.get("evidence", "") or issue.get("issue", "") or "episode_progression").strip()
            logging.warning(
                "[BPEnsemble] rejecting replayed episode-progression candidate (%s): %s",
                strategy_name,
                replay_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' 직전 화 replay 후보 폐기",
                level="warning",
                meta={
                    "strategy": strategy_name,
                    "reason": "episode_progression",
                    "evidence": replay_reason[:240],
                    "event_kind": "candidate_screening",
                },
            )
            return None, AgentErrorType.CANDIDATE_DISQUALIFIED

        contract_reason = self._blueprint_contract_admission_reason(candidate)
        if contract_reason:
            logging.warning(
                "[BPEnsemble] rejecting under-structured blueprint candidate (%s): %s",
                strategy_name,
                contract_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' 구조 계약 미달 후보 폐기",
                level="warning",
                meta={"strategy": strategy_name, "reason": contract_reason, "event_kind": "candidate_screening"},
            )
            return None, AgentErrorType.CANDIDATE_DISQUALIFIED

        return candidate

    def _format_prev_blueprint_carryover(self, bp: dict) -> str:
        bp_ep = bp.get("ep_num", "?")
        bp_title = bp.get("title", "")
        lines = [f"\n━━━ 제{bp_ep}화 '{bp_title}' ━━━"]

        carryover_fields = (
            ("시작위치", bp.get("start_location", "")),
            ("종료위치", bp.get("end_location", "")),
            ("시간흐름", bp.get("time_flow", "")),
            ("핵심긴장", bp.get("core_tension", "")),
            ("결말방향", bp.get("expected_ending", "")),
            ("엔딩훅", bp.get("ending_hook", "")),
        )
        for label, value in carryover_fields:
            if value:
                lines.append(f"[{label}] {_fit_compact_context(value, 160)}")

        protagonist_state = bp.get("protagonist_state", {})
        if isinstance(protagonist_state, dict):
            state_parts = []
            mood = protagonist_state.get("mood", "")
            injuries = protagonist_state.get("injuries", "")
            equipment = protagonist_state.get("equipment", [])
            if mood:
                state_parts.append(f"감정:{_fit_compact_context(mood, 60)}")
            if injuries and injuries != "없음":
                state_parts.append(f"부상:{_fit_compact_context(injuries, 60)}")
            if isinstance(equipment, list) and equipment:
                equipment_text = ", ".join(str(item or "").strip() for item in equipment[:5] if str(item or "").strip())
                if equipment_text:
                    state_parts.append(f"장비:{_fit_compact_context(equipment_text, 100)}")
            elif equipment:
                state_parts.append(f"장비:{_fit_compact_context(equipment, 100)}")
            if state_parts:
                lines.append(f"[주인공상태] {' | '.join(state_parts)}")

        scenes = bp.get("scene_breakdown", {})
        if isinstance(scenes, list):
            scenes = {f"scene_{i + 1}": scene for i, scene in enumerate(scenes) if isinstance(scene, dict)}
        if isinstance(scenes, dict):
            for scene_key, scene_value in scenes.items():
                if not isinstance(scene_value, dict):
                    continue
                scene_title = _fit_compact_context(scene_value.get("title", ""), 80)
                scene_location = _fit_compact_context(scene_value.get("location", ""), 60)
                scene_summary = scene_value.get("summary", "") or scene_value.get("description", "")
                scene_summary = _fit_compact_context(scene_summary, 120) if scene_summary else ""
                scene_chars = scene_value.get("characters", [])
                scene_events = scene_value.get("key_events", [])
                if isinstance(scene_chars, str):
                    scene_chars = [scene_chars]
                if isinstance(scene_events, str):
                    scene_events = [scene_events]
                chars_str = (
                    _fit_compact_context(
                        ", ".join(str(item or "").strip() for item in scene_chars if str(item or "").strip()),
                        120,
                    )
                    if scene_chars
                    else ""
                )
                events_str = (
                    _fit_compact_context(
                        "; ".join(str(item or "").strip() for item in scene_events if str(item or "").strip()),
                        180,
                    )
                    if scene_events
                    else ""
                )
                scene_parts = [f"[{scene_key}] {scene_title}"]
                if scene_location:
                    scene_parts.append(f"장소: {scene_location}")
                if chars_str:
                    scene_parts.append(f"등장: {chars_str}")
                if scene_summary:
                    scene_parts.append(f"요약: {scene_summary}")
                if events_str:
                    scene_parts.append(f"이벤트: {events_str}")
                lines.append(" | ".join(scene_parts))

        return "\n".join(lines)

    def _format_prev_info_expanded(
        self,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None = None,
        prev_manuscripts_text: str = "",
        *,
        archive_appendix_text: str | None = None,
        authoritative_time_context: str = "",
    ) -> str:
        """[V67] 이전 Blueprint/원고 확장 정보 포맷팅 (Gemini 대용량 컨텍스트 활용)"""
        sections = []

        # ── 직전 Blueprint 상세 (필수 계승) ──
        direct_prev = self._format_prev_info(
            prev_blueprint,
            authoritative_time_context=authoritative_time_context,
        )
        sections.append("[Context Tier 1 - Direct Previous Episode Truth]")
        sections.append(direct_prev)

        # ── [V67] 이전 Blueprint 전문 (최대 30개) ──
        if prev_blueprints and len(prev_blueprints) > 0:
            bp_lines = ["[Context Tier 2 - Structured Previous Blueprint Carryover]"]
            bp_lines.append(f"\n[V67] ═══ 이전 Blueprint 전문 ({len(prev_blueprints)}개) ═══")
            bp_lines.append("이전 에피소드의 구조화된 계승 정보입니다. 모순되는 내용을 절대 생성하지 마세요.")
            for bp in prev_blueprints:
                bp_lines.append(self._format_prev_blueprint_carryover(bp))

            bp_full = "\n".join(bp_lines)
            # 400K자 상한 (Gemini 1.05M 토큰 입력 여유)
            if len(bp_full) > 400000:
                bp_full = smart_truncate(
                    bp_full,
                    max_chars=400000,
                    head_chars=max(0, min(int(400000 * 0.55), 400000 - 80)),
                )
            sections.append(bp_full)

        # ── [pre-rerun] 직전 원고 말미 → 시간 진실 소스 ──
        if prev_manuscripts_text:
            carryover_digest = build_stage3_recent_carryover_digest(prev_manuscripts_text)
            if carryover_digest:
                sections.append("[Context Tier 3A - Recent Carryover Orders / Pending Actions]")
                sections.append(
                    "\n[carryover] ═══ 최근 원고 기준 미해결 지시 / 대기 과업 ═══\n"
                    "아래는 이미 내려졌거나 진행 중인 지시입니다.\n"
                    "direct_continuation이나 same-night opening에서는 이를 새 지시처럼 다시 시작하지 말고,\n"
                    "진행 상태 보고, 압박의 변화, 우선순위 조정, 새 결과 surface로만 전진하세요.\n\n"
                    f"{carryover_digest}"
                )
            sections.append("[Context Tier 3 - Manuscript Ending Truth]")
            ending_excerpt = prev_manuscripts_text.strip()[-800:]
            sections.append(
                "\n[pre-rerun] ═══ 직전 원고 실제 종료 상황 (원고 기준 — Blueprint 메타데이터보다 우선) ═══\n"
                "⚠️ 아래 원고 말미가 실제 종료 시점/위치/상황의 진실 소스입니다.\n"
                "Blueprint의 time_flow나 ending_state.timeline과 다를 경우, 원고 내용을 따르세요.\n\n"
                f"{ending_excerpt}"
            )

        # ── [V67] 이전 원고 전문 ──
        archive_appendix = archive_appendix_text
        if archive_appendix is None:
            archive_appendix, _ = build_stage3_archive_appendix(prev_manuscripts_text)
        if archive_appendix:
            ms_section = (
                "\n[Context Tier 4 - Archive Appendix / lower priority than Tier 1-3]\n"
                f"\n[V67] ═══ 이전 원고 전문 ═══\n"
                f"아래는 이전 에피소드의 최종 원고입니다. 이 내용과 모순되는 Blueprint를 절대 생성하지 마세요.\n"
                f"기본 경로에서는 overload 방지를 위해 archive appendix가 demotion/truncation될 수 있습니다.\n"
                f"특히: 사망한 캐릭터 재등장, 이미 일어난 이벤트 반복, 위치/시간 불연속에 주의하세요.\n\n"
                f"{archive_appendix}"
            )
            # 400K자 상한 (Gemini 1.05M 토큰 입력 여유)
            if len(ms_section) > 400000:
                ms_section = smart_truncate(
                    ms_section,
                    max_chars=400000,
                    head_chars=max(0, min(int(400000 * 0.55), 400000 - 80)),
                )
            sections.append(ms_section)

        result = "\n\n".join(sections)
        return smart_truncate(result)


def create_blueprint_ensemble(context, client, model_tier: str = AIModels.DEFAULT_ARCHITECT):
    """BlueprintEnsembleGenerator 생성 헬퍼"""
    return BlueprintEnsembleGenerator(context, client, model_tier)
