"""
[V60.11] Arc Ensemble Generator
병렬로 다수 Arc 후보를 생성하고 최적 후보를 선택

Strategy:
1. 3개의 서로 다른 전략으로 Arc 후보 생성 (병렬)
2. 각 후보를 빠르게 검증 (Python 기반)
3. 점수가 가장 높은 후보 선택
4. 모든 후보가 실패하면 피드백 통합하여 재생성

Cost: ~3x single generation (but higher pass rate)
"""

# utf8-hygiene: allow-file regex quantifier literals in compiled patterns are intentional and not mojibake evidence.

import ast
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.constants import AIModels, GenreTypes, Stage2Limits, smart_truncate
from modules.core.genre_schema_builder import (
    build_state_constraints_schema,
    build_status_shadow_schema,
    get_item_suffixes,
    is_wuxia,
)
from modules.core.investment_arithmetic_checker import InvestmentArithmeticChecker
from modules.core.non_wuxia_recovery_policy import (
    has_hard_injury_signal,
    has_hard_recovery_action,
    has_vague_recovery_signal,
)
from modules.core.prompt_loader import PromptLoader
from modules.core.response_schemas import ARC_DESIGN_SCHEMA  # [TF11] response_schema 확대
from modules.core.scene_obligation_heuristics import has_actionable_obligation_text
from modules.core.stage2_location_contract import is_verbose_stage2_location_label

from .base_agent import _SYSTEM_CFG, BaseAgent

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


_ITEM_SUFFIXES_ALL = get_item_suffixes("")
_ITEM_SUFFIX_GROUP = "|".join(sorted((re.escape(s) for s in _ITEM_SUFFIXES_ALL), key=len, reverse=True)) or r"아이템"
_FORBIDDEN_ITEM_RE = re.compile(
    rf"([가-힣A-Za-z0-9][가-힣A-Za-z0-9\s]{{0,30}}(?:{_ITEM_SUFFIX_GROUP}))"
)  # utf8-hygiene: allow-line regex quantifier
_ARC_MIN_EP_COUNT = 2
_ARC_MAX_EP_COUNT = 6


def _extract_carryover_authority_packet(prev_arc_context: str) -> dict[str, str]:
    """Extract the carryover authority packet block from prev-arc context."""
    if not isinstance(prev_arc_context, str) or "[Carryover Authority Packet]" not in prev_arc_context:
        return {}

    packet: dict[str, str] = {}
    in_packet = False
    for raw_line in prev_arc_context.splitlines():
        line = raw_line.strip()
        if line == "[Carryover Authority Packet]":
            in_packet = True
            continue
        if not in_packet:
            continue
        if not line:
            if packet:
                break
            continue
        if line.startswith("[") or line.startswith("###") or line.startswith("="):
            break
        if not line.startswith("- "):
            continue
        key, sep, value = line[2:].partition(":")
        if sep and key.strip() and value.strip():
            packet[key.strip()] = value.strip()
    return packet


def _normalize_carryover_packet_list(raw_value: object) -> list[str]:
    """Normalize packet list values written as Python or JSON-like literals."""
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]

    text = str(raw_value or "").strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        parsed = None

    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]

    trimmed = text.strip("[]")
    if not trimmed:
        return []
    return [part.strip().strip("'\"") for part in trimmed.split(",") if part.strip().strip("'\"")]


def _render_carryover_authority_packet(prev_arc_context: str) -> str:
    """Render a stable packet block for prompt injection and prompt tests."""
    packet = _extract_carryover_authority_packet(prev_arc_context)
    if not packet:
        return ""

    ordered_keys = [
        "next_arc_start_location",
        "next_arc_start_equipment",
        "next_arc_start_injuries",
        "next_arc_start_internal_energy",
        "next_arc_start_capital",
        "next_arc_start_total_assets",
        "next_arc_start_portfolio_position",
        "carryover_world_joint",
    ]
    lines = ["[Carryover Authority Packet]"]
    emitted: set[str] = set()
    for key in ordered_keys:
        value = packet.get(key)
        if value:
            lines.append(f"- {key}: {value}")
            emitted.add(key)
    for key, value in packet.items():
        if key not in emitted:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _normalize_episode_detail_lines(raw_value: object) -> list[str]:
    """Normalize detail lines into a compact, non-empty string list."""
    if isinstance(raw_value, str):
        raw_items = [raw_value]
    elif isinstance(raw_value, list):
        raw_items = raw_value
    else:
        return []

    lines: list[str] = []
    for raw_item in raw_items:
        text = re.sub(r"\s+", " ", str(raw_item or "")).strip().strip("-•*")
        if text:
            lines.append(text)
    return lines[:5]


def _normalize_episode_details(
    raw_value: object,
    *,
    ep_start: int | None = None,
    ep_end: int | None = None,
) -> list[dict[str, object]]:
    """Normalize episode_details into a sorted, per-episode mission packet."""
    if not isinstance(raw_value, list):
        return []

    normalized: list[dict[str, object]] = []
    seen_eps: set[int] = set()
    for raw_item in raw_value:
        if not isinstance(raw_item, dict):
            continue
        raw_ep_num = raw_item.get("ep_num")
        try:
            ep_num = int(raw_ep_num)
        except (TypeError, ValueError):
            continue
        if ep_start is not None and ep_num < ep_start:
            continue
        if ep_end is not None and ep_num > ep_end:
            continue
        details = _normalize_episode_detail_lines(raw_item.get("details"))
        if not details or ep_num in seen_eps:
            continue
        seen_eps.add(ep_num)
        normalized.append({"ep_num": ep_num, "details": details})

    normalized.sort(key=lambda item: int(item["ep_num"]))
    return normalized


def _extract_episode_detail_map_from_beats(
    beat_sequence: object,
    *,
    ep_start: int,
    ep_end: int,
) -> dict[int, list[str]]:
    """Derive per-episode mission lines from beat_sequence when episode_details are missing."""
    if isinstance(beat_sequence, list):
        raw_beats = beat_sequence
    elif isinstance(beat_sequence, str):
        raw_beats = [line for line in beat_sequence.splitlines() if str(line).strip()]
    else:
        raw_beats = []

    beat_map: dict[int, list[str]] = {}
    for idx, ep_num in enumerate(range(ep_start, ep_end + 1)):
        if idx >= len(raw_beats):
            break
        raw_item = raw_beats[idx]
        if isinstance(raw_item, dict):
            for key in ("details", "summary", "content", "beat", "title", "event"):
                details = _normalize_episode_detail_lines(raw_item.get(key))
                if details:
                    beat_map[ep_num] = details
                    break
            continue
        details = _normalize_episode_detail_lines(raw_item)
        if details:
            beat_map[ep_num] = details
    return beat_map


def _extract_episode_detail_map_from_tactical_doc(
    tactical_doc: object,
    *,
    ep_start: int,
    ep_end: int,
) -> dict[int, list[str]]:
    """Extract a bounded per-episode mission map from tactical_doc headers."""
    text = str(tactical_doc or "")
    if not text:
        return {}

    header_re = re.compile(
        r"(?:^|\n)\s*(?:\[)?제\s*(\d+)\s*화[^\n:：\]]*(?:[:：\]-]\s*|\]\s*)([^\n]+)"  # utf8-hygiene: allow-line regex header markers
    )
    detail_map: dict[int, list[str]] = {}
    for match in header_re.finditer(text):
        try:
            ep_num = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if ep_num < ep_start or ep_num > ep_end or ep_num in detail_map:
            continue
        details = _normalize_episode_detail_lines(match.group(2))
        if details:
            detail_map[ep_num] = details
    return detail_map


def _build_canonical_episode_details(result: dict, *, ep_start: int, ep_end: int) -> list[dict[str, object]]:
    """Build the canonical mission packet, preferring explicit episode_details and bounded fallbacks."""
    canonical_map: dict[int, list[str]] = {
        int(item["ep_num"]): list(item["details"])
        for item in _normalize_episode_details(result.get("episode_details"), ep_start=ep_start, ep_end=ep_end)
    }
    beat_map = _extract_episode_detail_map_from_beats(result.get("beat_sequence"), ep_start=ep_start, ep_end=ep_end)
    tactical_map = _extract_episode_detail_map_from_tactical_doc(
        result.get("tactical_doc", ""),
        ep_start=ep_start,
        ep_end=ep_end,
    )

    for ep_num in range(ep_start, ep_end + 1):
        if ep_num in canonical_map:
            continue
        if ep_num in beat_map:
            canonical_map[ep_num] = beat_map[ep_num]
            continue
        if ep_num in tactical_map:
            canonical_map[ep_num] = tactical_map[ep_num]

    return [{"ep_num": ep_num, "details": canonical_map[ep_num]} for ep_num in sorted(canonical_map)]


def _collect_episode_detail_actionability_issues(canonical_episode_details: list[dict[str, object]]) -> list[str]:
    """Flag mission packets that are present but still too generic to guide downstream generation."""
    issues: list[str] = []
    for item in canonical_episode_details:
        ep_num = int(item.get("ep_num") or 0)
        raw_details = item.get("details")
        if isinstance(raw_details, list):
            details = [str(detail or "").strip() for detail in raw_details if str(detail or "").strip()]
        elif raw_details:
            details = [str(raw_details).strip()]
        else:
            details = []

        if not any(has_actionable_obligation_text(detail) for detail in details):
            issues.append(f"episode_details mission beat too generic: ep{ep_num}")

    return issues


def _coerce_episode_number(value: object, default: int) -> int:
    """Coerce episode numbers without applying arc-size bounds."""
    if isinstance(value, bool):
        value = default
    if isinstance(value, str):
        match = re.search(r"(\d+)", value)
        value = int(match.group(1)) if match else default
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(1, value)


def _normalize_state_contract_list(raw_value: object) -> list[str]:
    """Normalize state/joint inventory arrays into compact string lists."""
    if isinstance(raw_value, list):
        raw_items = raw_value
    elif isinstance(raw_value, str):
        raw_items = [chunk.strip() for chunk in re.split(r"[,/]", raw_value) if chunk.strip()]
    else:
        return []

    normalized: list[str] = []
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            text = raw_item.get("name") or raw_item.get("item") or raw_item.get("value") or ""
        else:
            text = str(raw_item or "")
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            normalized.append(text)
    return normalized[:20]


def _looks_like_verbose_state_field(text: object, *, max_chars: int = 80) -> bool:
    """Detect sentence-like state field payloads that should be compact labels instead."""
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return False
    if len(normalized) > max_chars:
        return True
    if any(token in normalized for token in (".", "!", "?", "시계는", "창밖", "냄새")):
        return True
    return normalized.count(",") >= 2


def _collect_state_contract_vocabulary_issues(candidate: dict) -> list[str]:
    """Collect Stage2 state-field vocabulary issues that should be solved at generation time."""
    issues: list[str] = []
    tactical = str(candidate.get("tactical_doc", "") or "")
    if re.search(r"\b(?:Arc|Block|Stage)\b", tactical):
        issues.append("tactical_doc meta vocabulary leak: Arc/Block/Stage")

    state_constraints = candidate.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        return issues

    joint_docs = candidate.get("joint_docs", {})
    if not isinstance(joint_docs, dict):
        joint_docs = {}

    arc_start = state_constraints.get("arc_start_state", {})
    if not isinstance(arc_start, dict):
        arc_start = {}

    arc_end = state_constraints.get("arc_end_state", {})
    if not isinstance(arc_end, dict):
        arc_end = {}

    start_location = str(arc_start.get("location", "") or "").strip()
    final_location = str(joint_docs.get("final_location", "") or "").strip()
    end_location = str(arc_end.get("location", "") or "").strip()
    if start_location and is_verbose_stage2_location_label(start_location):
        issues.append("arc_start_state.location must be a short canonical label")
    if final_location and _looks_like_verbose_state_field(final_location):
        issues.append("joint_docs.final_location must be a short canonical label")
    if end_location and _looks_like_verbose_state_field(end_location):
        issues.append("arc_end_state.location must be a short canonical label")
    if final_location and end_location and final_location != end_location:
        if final_location not in end_location and end_location not in final_location:
            issues.append("joint_docs.final_location / arc_end_state.location mismatch")

    inventory_fields = [
        ("arc_start_state.equipment", (state_constraints.get("arc_start_state", {}) or {}).get("equipment", [])),
        ("arc_end_state.equipment", arc_end.get("equipment", [])),
        ("joint_docs.physical_inventory", joint_docs.get("physical_inventory", [])),
    ]
    for label, raw_items in inventory_fields:
        for item in _normalize_state_contract_list(raw_items)[:5]:
            if _looks_like_verbose_state_field(item):
                issues.append(f"{label} contains sentence-style inventory blob")
                break

    return issues


def _collect_non_wuxia_state_noise_issues(candidate: dict, genre: str) -> list[str]:
    """Collect wuxia-only state fields that should not appear in non-wuxia Stage2 arcs."""
    if is_wuxia(genre):
        return []

    state_constraints = candidate.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        return []

    issues: list[str] = []
    wuxia_only_keys = ("internal_energy", "realm", "qi_nature", "martial_arts")
    for section_key in ("arc_start_state", "arc_end_state"):
        section = state_constraints.get(section_key, {})
        if not isinstance(section, dict):
            continue
        leaked = [key for key in wuxia_only_keys if key in section]
        if leaked:
            issues.append(f"{section_key} contains non-wuxia state noise: {', '.join(leaked)}")
    return issues


def _collect_non_wuxia_recovery_issues(candidate: dict, genre: str) -> list[str]:
    """Penalize vague hard-injury recovery while allowing natural healing for soft non-wuxia fatigue."""
    if is_wuxia(genre):
        return []

    tactical_doc = re.sub(r"\s+", " ", str(candidate.get("tactical_doc", "") or "")).strip()
    episode_details = candidate.get("episode_details")
    first_episode_bits: list[str] = []
    if isinstance(episode_details, list) and episode_details:
        first_episode = episode_details[0]
        if isinstance(first_episode, dict):
            raw_details = first_episode.get("details")
            if isinstance(raw_details, list):
                first_episode_bits = [str(item or "").strip() for item in raw_details[:3] if str(item or "").strip()]
            elif raw_details:
                first_episode_bits = [str(raw_details).strip()]

    opening_text = " ".join(part for part in ([tactical_doc[:700]] + first_episode_bits) if part).lower()
    if not opening_text:
        return []

    if not has_hard_injury_signal(opening_text):
        return []

    if has_hard_recovery_action(opening_text):
        return []
    if has_vague_recovery_signal(opening_text):
        return ["opening recovery beat too implicit for non-wuxia carryover fatigue"]
    return []


def _collect_investment_arithmetic_issues(candidate: dict, prev_arc_context: str, arc_no: int) -> list[dict]:
    """Collect arithmetic warnings for investment-like Stage2 candidates before selection."""
    state_constraints = candidate.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        return []

    arc_start = state_constraints.get("arc_start_state", {})
    arc_end = state_constraints.get("arc_end_state", {})
    investment_calc = state_constraints.get("investment_calc")
    has_financial_state = any(
        isinstance(section, dict) and any(section.get(key) for key in ("capital", "total_assets", "portfolio_position"))
        for section in (arc_start, arc_end)
    )
    if not isinstance(investment_calc, dict) and not has_financial_state:
        return []

    packet = _extract_carryover_authority_packet(prev_arc_context)
    prev_arc_end_state: dict[str, str] = {}
    if packet.get("next_arc_start_capital"):
        prev_arc_end_state["capital"] = packet["next_arc_start_capital"]
    if packet.get("next_arc_start_total_assets"):
        prev_arc_end_state["total_assets"] = packet["next_arc_start_total_assets"]

    checker = InvestmentArithmeticChecker.from_yaml()
    return checker.check(
        candidate,
        candidate.get("arc_no") or arc_no,
        prev_arc_end_state=prev_arc_end_state or None,
    )


def _score_candidate_contract_health(
    candidate: dict,
    prev_arc_context: str,
    *,
    genre: str,
    candidate_arc_no: int,
    candidate_ep_start: int,
    candidate_ep_end: int,
) -> tuple[int, list[str]]:
    penalty = 0
    issues: list[str] = []

    canonical_episode_details = _normalize_episode_details(
        candidate.get("episode_details"),
        ep_start=candidate_ep_start,
        ep_end=candidate_ep_end,
    )
    covered_eps = {int(item["ep_num"]) for item in canonical_episode_details}
    expected_eps = list(range(candidate_ep_start, candidate_ep_end + 1))
    missing_eps = [ep_num for ep_num in expected_eps if ep_num not in covered_eps]
    if not canonical_episode_details:
        penalty += 12
        issues.append("canonical mission packet missing: episode_details")
    elif missing_eps:
        penalty += min(10, 4 + len(missing_eps) * 2)
        issues.append(
            "episode_details mission packet coverage 부족: " + ", ".join(f"ep{ep_num}" for ep_num in missing_eps[:3])
        )

    actionability_issues = _collect_episode_detail_actionability_issues(canonical_episode_details)
    if actionability_issues:
        penalty += min(8, len(actionability_issues) * 4)
        issues.extend(actionability_issues[:2])

    vocabulary_issues = _collect_state_contract_vocabulary_issues(candidate)
    if vocabulary_issues:
        penalty += min(12, len(vocabulary_issues) * 4)
        issues.extend(vocabulary_issues[:3])

    non_wuxia_noise_issues = _collect_non_wuxia_state_noise_issues(candidate, genre)
    if non_wuxia_noise_issues:
        penalty += min(8, len(non_wuxia_noise_issues) * 4)
        issues.extend(non_wuxia_noise_issues[:2])

    recovery_issues = _collect_non_wuxia_recovery_issues(candidate, genre)
    if recovery_issues:
        penalty += min(6, len(recovery_issues) * 6)
        issues.extend(recovery_issues[:1])

    arithmetic_warnings = _collect_investment_arithmetic_issues(
        candidate,
        prev_arc_context,
        candidate_arc_no or candidate_ep_start,
    )
    if arithmetic_warnings:
        arithmetic_penalty = 0
        for warning in arithmetic_warnings:
            severity = str(warning.get("severity", "") or "").upper()
            if severity == "CRITICAL":
                arithmetic_penalty += 10
            elif severity == "MAJOR":
                arithmetic_penalty += 6
            else:
                arithmetic_penalty += 3
        penalty += min(18, arithmetic_penalty)
        issues.extend(
            f"investment arithmetic warning: {smart_truncate(str(warning.get('text', '')), max_chars=120)}"
            for warning in arithmetic_warnings[:2]
        )

    return penalty, issues


def _has_generic_episode_detail_issue(candidate: dict) -> bool:
    issues = candidate.get("_issues", [])
    return any(str(issue).startswith("episode_details mission beat too generic") for issue in issues)


def _extract_forbidden_items(constraint_block: str) -> list[str]:
    """constraint_block의 ❌ 라인에서 금지 아이템명을 추출한다."""
    if not isinstance(constraint_block, str) or not constraint_block:
        return []

    items: list[str] = []
    seen: set[str] = set()

    for raw in re.findall(r"❌\s*([^\n❌]+)", constraint_block):
        clean = re.sub(r"\s*\(Arc\s*\d+.*?\)", "", str(raw))
        clean = re.sub(r"[│┤├─+|]", "", clean).strip()
        if not clean:
            continue
        if "다음 아이템" in clean or "다음 수여물" in clean or clean.startswith("다음 "):
            continue

        # 메타 정보(" - Arc n에서 ...")는 제거 후 핵심명만 추출
        head = re.split(r"\s*-\s*", clean, maxsplit=1)[0].strip()
        matched = _FORBIDDEN_ITEM_RE.search(head)
        if matched:
            item = matched.group(1).strip()
        else:
            item = head

        if item and item not in seen:
            seen.add(item)
            items.append(item)

    return items


def _build_block_event_guard(curr_block: dict | None, max_field_len: int = 260) -> str:
    """현재 블록의 핵심 사건 요약을 추출해 블록 경계 가이드를 강화한다."""
    if not isinstance(curr_block, dict):
        return ""

    content = curr_block.get("content")
    if not isinstance(content, dict):
        content = {}

    lines: list[str] = []
    for key in ("context", "event_villain", "solution", "reward"):
        raw = content.get(key)
        if raw is None:
            raw = curr_block.get(key)
        if raw is None:
            continue
        text = re.sub(r"\s+", " ", str(raw)).strip()
        if not text:
            continue
        if len(text) > max_field_len:
            text = _fit_arc_prompt_context(text, max_field_len)
        lines.append(f"- {key}: {text}")

    if not lines:
        return ""

    return (
        "### [이번 Arc에서 다룰 블록 핵심 사건 목록]\n"
        "아래 항목은 현재 블록에서만 허용되는 사건 출처입니다:\n" + "\n".join(lines)
    )


def _format_curr_block_authority(curr_block: dict | None, max_field_len: int = 220) -> str:
    """Current-block DNA를 raw JSON 대신 hierarchy-friendly packet으로 정리한다."""
    if not isinstance(curr_block, dict):
        return "{}"

    def _stringify(value: object, *, max_chars: int = max_field_len) -> str:
        if value is None:
            return ""
        if isinstance(value, dict | list):
            raw = json.dumps(value, ensure_ascii=False)
        else:
            raw = str(value)
        text = re.sub(r"\s+", " ", raw).strip()
        if not text:
            return ""
        return _fit_arc_prompt_context(text, max_chars) if len(text) > max_chars else text

    content = curr_block.get("content")
    if not isinstance(content, dict):
        content = {}

    lines: list[str] = [
        "[Context Priority Contract]",
        "CURRENT BLOCK DNA > BLOCK EVENT GUARD > PREVIOUS ARC CONTEXT > OPTIONAL EXTENSIONS",
        "",
        "[Current Block Authority Packet]",
    ]

    for label, raw in (
        ("block_id", curr_block.get("block_id")),
        ("title", curr_block.get("title")),
        ("ep_count", curr_block.get("ep_count")),
    ):
        text = _stringify(raw, max_chars=120)
        if text:
            lines.append(f"- {label}: {text}")

    premise = _stringify(content.get("context") or curr_block.get("context"), max_chars=320)
    if premise:
        lines.append(f"- block_premise: {premise}")

    metadata_lines = []
    for label, raw in (
        ("block_theme", curr_block.get("block_theme")),
        ("emotional_beat", curr_block.get("emotional_beat")),
        ("tension_level", curr_block.get("tension_level")),
        ("foreshadow", curr_block.get("foreshadow")),
        ("callback", curr_block.get("callback")),
    ):
        text = _stringify(raw)
        if text:
            metadata_lines.append(f"- {label}: {text}")
    if metadata_lines:
        lines.append("")
        lines.append("[Current Block Metadata]")
        lines.extend(metadata_lines)

    genre_ext = curr_block.get("genre_ext") or (curr_block.get("raw_data") or {}).get("genre_ext")
    genre_ext_text = _stringify(genre_ext, max_chars=320)
    if genre_ext_text:
        lines.append("")
        lines.append("[Genre Extension Targets]")
        lines.append(f"- genre_ext: {genre_ext_text}")

    return "\n".join(lines)


def _fit_arc_prompt_context(value: object, max_chars: int, *, head_ratio: float = 0.55) -> str:
    raw = str(value or "")
    if len(raw) <= max_chars:
        return raw
    head_chars = max(0, min(int(max_chars * head_ratio), max_chars - 80))
    return smart_truncate(raw, max_chars=max_chars, head_chars=head_chars)


# ── [장르별 에너지 시스템 블록] ──────────────────────────────────────
_WUXIA_ENERGY_BLOCK = """\
  ### [V62.2] 🩹 주인공 자연 회복 원칙 (무협 전용)
  - 주인공은 소설 주인공이다. 힐링팩터가 있다. 절대 약해지지 않는다.
  - 아크 시작: 부상="없음", 내공=이전 Arc 종료값 (최소 90%). 자연 회복 적용.
  - 화별 내공 규칙:
    · 한 화 안에서 긴장/전투로 소모 가능 (최저 60%까지만)
    · 다음 화 시작 시 반드시 90% 이상으로 회복
    · 내공이 화를 거듭하며 떨어지기만 하는 것은 절대 금지
    · 주인공은 점점 강해진다. 내공은 우상향이 기본이다.
  - 부상: Arc 내 일시적 피로/타박 허용, 다음 화면 회복됨. 만성화 금지.
  - arc_end_state: injuries="없음", internal_energy=최소 90 (이전 Arc 종료값 기반)
  - status_shadow: expected_injuries="없음", internal_energy_loss="자연 회복 적용"

  ### [V60.40] 화간 상태 체크포인트 필수
  각 화는 반드시 시작 상태와 종료 상태를 명시하라:
  - 시작 상태: 위치, 내공%, 부상, 소지품 (이전 화 종료 상태 기반 + 자연 회복 적용)
  - 종료 상태: 위치, 내공%, 부상, 획득/소모 아이템
  - ⚠️ 내공이 화를 넘기며 계속 떨어지는 패턴은 REJECT 사유임"""


def _build_non_wuxia_energy_block(genre: str, critical_keys: list[str] | None = None) -> str:
    """비무협 장르용 에너지 시스템 블록 동적 생성."""
    _ck = critical_keys or []
    _sc_field = build_state_constraints_schema(genre, _ck)
    # 장르 핵심 수치 라벨 추출 (예: "capital"→"자본금")
    _key_label = _sc_field.split(":")[0].strip().strip('"') if ":" in _sc_field else "핵심 수치"
    _desc = _sc_field.split(":", 1)[1].strip().strip('"') if ":" in _sc_field else "현재 상태"
    return f"""\
  ### [V62.2] 🩹 주인공 자연 회복 원칙
  - 주인공은 소설 주인공이다. 절대 약해지지 않는다.
  - 아크 시작: 부상="없음". 예외 없음.
  - ⚠️ 이 장르는 내공/기력 시스템이 없음. "내공" 표현 절대 금지.

  ### [NR-1] 정신적 피로 자연 회복 원칙 (비무협 장르)
  - 정신적 마모/스트레스/피로는 물리적 부상이 아니다. 일상적 활동으로 자연 회복된다.
  - 회복 경로: 수면, 식사, 산책, 대화, 취미, 음주, 휴식 등 — 1문장 언급이면 충분.
  - opening beat에서 일상 회복 행동이 직접 보이면 가장 좋지만, 비무협 soft fatigue는 시간 경과나 일상 흐름상 자연 회복으로 읽혀도 허용된다.
  - "시간이 지나며 회복했다" 같은 추상 문장도 soft fatigue에는 허용된다. 다만 직전 화의 피로를 즉시 "최상의 컨디션"으로 뒤집는 식의 노골적 모순은 금지한다.
  - Arc 내에서 정신적 피로가 화를 거듭하며 악화만 하는 것은 피하고, 필요하면 회복 구간을 설계하라.
  - soft fatigue 누적은 경고/감점 사유가 될 수 있지만 자동 REJECT 기준으로 고정하지 않는다.
  - 병원/정신과 방문은 선택사항이지 필수가 아니다. 일상적 회복이 기본이다.

  ### [V60.40] 화간 상태 체크포인트 필수
  각 화는 반드시 시작 상태와 종료 상태를 명시하라:
  - 시작 상태: 위치, {_key_label}({_desc}), 부상, 소지품
  - 종료 상태: 위치, {_key_label}({_desc}), 부상, 획득/소모 아이템
  - ⚠️ "내공", "기력", "내력" 등 무협 용어 사용 시 REJECT"""


# 다양한 생성 전략
GENERATION_STRATEGIES = [
    {
        "name": "conservative",
        "temperature": 0.3,
        "focus": "안정성과 연속성 우선. 이전 Arc 상태를 정확히 계승하고, 새로운 요소는 최소화.",
        "style": "기존 설정 활용 중심",
    },
    {
        "name": "balanced",
        "temperature": 0.5,
        "focus": "연속성과 새로움의 균형. 이전 상태를 계승하면서 적절한 새 갈등 도입.",
        "style": "균형 잡힌 전개",
    },
    {
        "name": "creative",
        "temperature": 0.7,
        "focus": "서사적 흥미 우선. 연속성을 유지하면서 예상치 못한 전개 시도.",
        "style": "창의적 전개",
    },
]


class ArcEnsembleGenerator(BaseAgent):
    """
    [V60.11] Arc Ensemble Generator

    병렬로 3개 Arc 후보 생성 후 최적 선택
    """

    # [V61.3→TF-26] 앙상블 타임아웃 — system.yaml ensemble_timeouts.arc 참조
    _TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("arc", {})
    ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)
    SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)

    def __init__(
        self, context, client, model_tier: str = AIModels.DEFAULT_ARCHITECT
    ):  # [SSOT-P2] 호출부(main_a.py:L1513)가 model_tier 인자를 명시 전달
        # [V62.4] gemini-2.5-pro로 변경 - 3-pro 쿼터 소진 문제 방지
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent 자동 설정, 현재 gemini-2.5-pro 직접 사용)
        self._prompt_loader = PromptLoader()
        self.strategies = GENERATION_STRATEGIES
        self.max_workers = 3

    def _load_strategy_bias(self, strategy_names: list[str], *, lookback: int = 30) -> dict[str, float]:
        """Stage 2 PASS 선택 비중을 전략별로 로드한다."""
        db_candidates = []
        for db in (
            self._resolve_logging_db(),
            getattr(self.context, "db", None),
        ):
            if db is None or not hasattr(db, "get_strategy_win_rates"):
                continue
            if any(existing is db for existing in db_candidates):
                continue
            db_candidates.append(db)

        for db in db_candidates:
            try:
                stats = db.get_strategy_win_rates(
                    lookback=lookback,
                    selected_label="",
                    allowed_strategies=tuple(strategy_names),
                )
            except Exception as bias_err:
                logging.debug("[QR-3] Arc 전략 비중 조회 실패 (비치명): %s", bias_err)
                continue

            if not isinstance(stats, dict) or int(stats.get("total", 0) or 0) <= 0:
                continue
            return {name: float(stats.get(name, 0.0) or 0.0) for name in strategy_names}
        return {}

    def _build_strategy_execution_plan(self, strategies: list[dict]) -> list[dict]:
        """최근 PASS 비중을 반영해 전략 temperature를 미세 조정한다."""
        strategy_names = [
            str(strategy.get("name", "") or "").strip() for strategy in strategies if strategy.get("name")
        ]
        shares = self._load_strategy_bias(strategy_names)
        if not shares or all(shares.get(name, 0.0) <= 0 for name in strategy_names):
            return [dict(strategy) for strategy in strategies]

        ordered = sorted(strategies, key=lambda strategy: shares.get(strategy.get("name", ""), 0.0), reverse=True)
        adjusted: list[dict] = []
        for strategy in ordered:
            strategy_copy = dict(strategy)
            name = str(strategy_copy.get("name", "") or "")
            base_temp = float(strategy_copy.get("temperature", 0.5) or 0.5)
            share = shares.get(name, 0.0)
            adjusted_temp = base_temp
            if share >= 0.5:
                adjusted_temp = max(0.1, round(base_temp - 0.05, 2))
            elif share <= 0.15:
                adjusted_temp = min(1.0, round(base_temp + 0.1, 2))
            elif share <= 0.3:
                adjusted_temp = min(1.0, round(base_temp + 0.05, 2))
            strategy_copy["temperature"] = adjusted_temp
            strategy_copy["_recent_share"] = share
            adjusted.append(strategy_copy)

        logging.info(
            "[QR-3] Arc 전략 비중 적용: %s",
            ", ".join(f"{strategy['name']}={int(shares.get(strategy['name'], 0.0) * 100)}%" for strategy in adjusted),
        )
        return adjusted

    @staticmethod
    def _build_char_ngrams(text: str, n: int = 3) -> set[str]:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if not normalized:
            return set()
        if len(normalized) < n:
            return {normalized}
        return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}

    @staticmethod
    def _compose_diversity_text(candidate: dict) -> str:
        tactical = candidate.get("tactical_doc", "")
        tactical = tactical if isinstance(tactical, str) else str(tactical or "")
        joint_docs = candidate.get("joint_docs", {})
        if isinstance(joint_docs, dict):
            joint_text = json.dumps(joint_docs, ensure_ascii=False)
        else:
            joint_text = str(joint_docs or "")
        return (tactical + "\n" + joint_text).strip()

    def _summarize_candidate_diversity(self, candidates: list[dict], *, threshold: float = 0.7) -> dict:
        indexed_texts: list[tuple[int, str]] = []
        for idx, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            combined = self._compose_diversity_text(candidate)
            if combined:
                indexed_texts.append((idx, combined))

        if len(indexed_texts) < 2:
            return {}

        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        pairwise = []
        high_similarity_pairs = []
        max_similarity = 0.0
        for left_pos in range(len(indexed_texts)):
            left_idx, left_text = indexed_texts[left_pos]
            left_grams = self._build_char_ngrams(left_text)
            if not left_grams:
                continue
            for right_pos in range(left_pos + 1, len(indexed_texts)):
                right_idx, right_text = indexed_texts[right_pos]
                right_grams = self._build_char_ngrams(right_text)
                if not right_grams:
                    continue
                union = left_grams | right_grams
                similarity = (len(left_grams & right_grams) / len(union)) if union else 0.0
                similarity = round(similarity, 2)
                pair_label = f"{labels[left_idx]}-{labels[right_idx]}"
                pairwise.append({"pair": pair_label, "similarity": similarity})
                max_similarity = max(max_similarity, similarity)
                if similarity >= threshold:
                    high_similarity_pairs.append({"pair": pair_label, "similarity": similarity})

        warning = ""
        if high_similarity_pairs:
            pairs_text = ", ".join(
                f"{pair['pair']} {int(pair['similarity'] * 100)}%" for pair in high_similarity_pairs[:3]
            )
            warning = f"[후보 다양성 경고] Arc 후보 유사도 높음: {pairs_text}"

        return {
            "pairwise": pairwise,
            "max_similarity": round(max_similarity, 2),
            "high_similarity_pairs": high_similarity_pairs,
            "warning": warning,
        }

    def generate_ensemble(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        prev_equipment: list[str] | None = None,
        forbidden_items: list[str] | None = None,
        assets: dict = None,
        feedback: str = "",
        strategy_specific_feedback: str = "",
        rejected_strategy: str = "",
        protagonist_name: str = "주인공",
        protagonist_config: dict = None,
        entity_registry: dict = None,
        ep_count: int = None,
        pacing_signals: dict | None = None,
        ep_count_suggestion: int = None,
        retry: int = 0,
        single_strategy: str = "",
    ) -> tuple[dict | None, list[dict]]:
        """Generate multiple arc candidates and return the Director-owned shortlist."""
        ep_count_suggestion, ep_end, pacing_signal_guide = self._resolve_ensemble_generation_inputs(
            ep_start=ep_start,
            curr_block=curr_block,
            ep_count=ep_count,
            ep_count_suggestion=ep_count_suggestion,
            pacing_signals=pacing_signals,
        )
        genre = self._load_ensemble_genre(GenreTypes.WUXIA)
        cache_name = self._resolve_ensemble_cache_name(
            arc_no=arc_no,
            prev_arc_context=prev_arc_context,
            constraint_block=constraint_block,
        )
        started_at = time.monotonic()
        candidates = self._run_ensemble_generation_fanout(
            arc_no=arc_no,
            ep_start=ep_start,
            ep_end=ep_end,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            prev_arc_context=prev_arc_context,
            constraint_block=constraint_block,
            assets=assets,
            feedback=feedback,
            strategy_specific_feedback=strategy_specific_feedback,
            rejected_strategy=rejected_strategy,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            entity_registry=entity_registry,
            genre=genre,
            ep_count_suggestion=ep_count_suggestion,
            pacing_signal_guide=pacing_signal_guide,
            retry=retry,
            single_strategy=single_strategy,
            cache_name=cache_name,
            started_at=started_at,
        )
        try:
            logging.warning(f"[PerfTimer:ArcEnsemble] arc_{arc_no}_ensemble={time.monotonic() - started_at:.2f}s")
        except Exception as _e:
            logging.debug("[ArcEnsemble] PerfTimer logging failed (ignored): %s", _e)

        if not candidates:
            return None, []

        qualified_candidates = self._qualify_candidates_by_tactical_length(candidates, ep_count_suggestion)
        scored_candidates, director_candidates, diversity_summary = self._score_candidates_for_director(
            qualified_candidates,
            prev_arc_context,
            constraint_block,
            prev_equipment=prev_equipment,
            forbidden_items=forbidden_items,
        )
        self._log_scored_candidates(
            scored_candidates,
            director_candidates,
            total_candidates=len(candidates),
        )
        self._apply_ensemble_metadata(director_candidates, scored_candidates, diversity_summary)
        return None, director_candidates

    def _resolve_ensemble_generation_inputs(
        self,
        *,
        ep_start: int,
        curr_block: dict,
        ep_count: int | None,
        ep_count_suggestion: int | None,
        pacing_signals: dict | None,
    ) -> tuple[int, int, str]:
        if ep_count_suggestion is None:
            ep_count_suggestion = ep_count
        if ep_count_suggestion is None:
            ep_count_suggestion = (
                curr_block.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
                if isinstance(curr_block, dict)
                else Stage2Limits.DEFAULT_EP_COUNT
            )
        ep_count_suggestion = self._coerce_ep_count(ep_count_suggestion, Stage2Limits.DEFAULT_EP_COUNT)
        ep_end = ep_start + ep_count_suggestion - 1
        pacing_signal_guide = self._build_pacing_signal_guide(curr_block, ep_count_suggestion, pacing_signals or {})
        return ep_count_suggestion, ep_end, pacing_signal_guide

    def _load_ensemble_genre(self, default_genre: str = GenreTypes.WUXIA) -> str:
        genre = default_genre
        try:
            if hasattr(self, "context") and hasattr(self.context, "db"):
                bible = self.context.db.load_anchor("bible")
                if bible:
                    genre = bible.get("_genre", default_genre)
        except Exception as e:
            logging.warning(f" [V61.3] genre preload failed: {str(e)[:50]}")
        return genre

    def _resolve_ensemble_cache_name(self, *, arc_no: int, prev_arc_context: str, constraint_block: str) -> str:
        shared_context = f"{prev_arc_context or ''}\n\n{constraint_block or ''}"
        cache_info = self._get_or_create_context_cache(
            cache_type="arc_ensemble",
            content=shared_context,
            ttl_seconds=600,
            project_name=self._context_cache_project_namespace("arc", arc_no),
        )
        return cache_info.get("cache_name")

    def _select_active_strategies(self, single_strategy: str) -> list[dict]:
        active_strategies = self.strategies
        if single_strategy:
            filtered = [strategy for strategy in self.strategies if strategy.get("name") == single_strategy]
            if filtered:
                active_strategies = filtered
        return self._build_strategy_execution_plan(active_strategies)

    def _run_ensemble_generation_fanout(
        self,
        *,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        assets: dict,
        feedback: str,
        strategy_specific_feedback: str,
        rejected_strategy: str,
        protagonist_name: str,
        protagonist_config: dict | None,
        entity_registry: dict | None,
        genre: str,
        ep_count_suggestion: int,
        pacing_signal_guide: str,
        retry: int,
        single_strategy: str,
        cache_name: str,
        started_at: float,
    ) -> list[dict]:
        candidates: list[dict] = []
        active_strategies = self._select_active_strategies(single_strategy)
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for strategy in active_strategies:
                    strategy_name = str(strategy.get("name", "") or "")
                    strategy_feedback = (
                        strategy_specific_feedback
                        if (strategy_name == rejected_strategy and strategy_specific_feedback)
                        else ""
                    )
                    future = executor.submit(
                        self._generate_single,
                        arc_no=arc_no,
                        ep_start=ep_start,
                        ep_end=ep_end,
                        vol_strategy=vol_strategy,
                        curr_block=curr_block,
                        prev_arc_context=prev_arc_context,
                        constraint_block=constraint_block,
                        assets=assets,
                        feedback=feedback,
                        strategy_feedback=strategy_feedback,
                        strategy=strategy,
                        protagonist_name=protagonist_name,
                        protagonist_config=protagonist_config,
                        entity_registry=entity_registry,
                        genre=genre,
                        ep_count_suggestion=ep_count_suggestion,
                        pacing_signal_guide=pacing_signal_guide,
                        retry=retry,
                        cache_name=cache_name,
                    )
                    futures[future] = strategy_name

                strategy_names = ", ".join(futures.values())
                self._operator_log(
                    f"[Arc] Generating {len(futures)} ensemble candidates ({strategy_names})...",
                    meta={"candidate_count": len(futures), "strategies": list(futures.values())},
                )
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy_name = futures[future]
                        try:
                            result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            if result:
                                result["_strategy"] = strategy_name
                                candidates.append(result)
                                elapsed = round(time.monotonic() - started_at, 1)
                                self._operator_log(
                                    f"[Arc] '{strategy_name}' finished ({elapsed:.0f}s)",
                                    meta={"strategy": strategy_name, "elapsed_seconds": elapsed},
                                )
                        except FutureTimeoutError:
                            logging.warning(
                                "[V61.3] %s strategy timed out (%ss)",
                                strategy_name,
                                self.SINGLE_CANDIDATE_TIMEOUT,
                            )
                            self._operator_log(
                                f"[Arc] '{strategy_name}' timed out",
                                level="warning",
                                meta={"strategy": strategy_name, "timeout_seconds": self.SINGLE_CANDIDATE_TIMEOUT},
                            )
                        except Exception as e:
                            logging.warning("[Ensemble] %s strategy failed: %s", strategy_name, str(e)[:50])
                            self._operator_log(
                                f"[Arc] '{strategy_name}' failed",
                                level="warning",
                                meta={"strategy": strategy_name},
                            )
                except FutureTimeoutError:
                    logging.warning(
                        "[V61.3] Arc ensemble timed out (%ss); using %s completed candidates",
                        self.ENSEMBLE_TIMEOUT,
                        len(candidates),
                    )
                except Exception as e:
                    logging.warning("[V61.3] Arc ensemble loop failed: %s", str(e)[:80])
                finally:
                    for f in futures:
                        f.cancel()
        except Exception as e:
            import traceback

            logging.error("[V61.3] Arc ensemble fan-out failed: %s", str(e)[:100])
            logging.error(traceback.format_exc())
        return candidates

    def _qualify_candidates_by_tactical_length(
        self,
        candidates: list[dict],
        fallback_ep_count: int,
    ) -> list[dict]:
        valid_candidates = []
        for candidate in candidates:
            tactical = self._safe_tactical_str(candidate.get("tactical_doc", ""))
            candidate["tactical_doc"] = tactical
            tactical_len = len(tactical)
            candidate_ep_count = self._resolve_candidate_ep_count(candidate, fallback_ep_count)
            min_tactical_length = candidate_ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
            if tactical_len >= min_tactical_length:
                valid_candidates.append(candidate)
                continue

            logging.info(
                "[Ensemble] %s filtered: tactical_doc %s < %s (ep_count=%s)",
                candidate.get("_strategy", "?"),
                tactical_len,
                min_tactical_length,
                candidate_ep_count,
            )
            self._operator_log(
                f"[Arc] '{candidate.get('_strategy', '?')}' tactical length below minimum",
                level="warning",
                meta={
                    "strategy": candidate.get("_strategy", "?"),
                    "tactical_chars": tactical_len,
                    "min_required_chars": min_tactical_length,
                    "ep_count": candidate_ep_count,
                },
            )

        if valid_candidates:
            return valid_candidates

        def safe_tactical_len(candidate: dict) -> int:
            tactical = candidate.get("tactical_doc", "")
            return len(tactical) if isinstance(tactical, str) else len(str(tactical)) if tactical else 0

        candidates.sort(key=safe_tactical_len, reverse=True)
        longest = candidates[0]
        longest_len = safe_tactical_len(longest)
        longest_ep_count = self._resolve_candidate_ep_count(longest, fallback_ep_count)
        min_required = longest_ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
        if longest_len < min_required * 0.6:
            logging.warning(
                "[Ensemble] all candidates are severely short: %s < %s",
                longest_len,
                int(min_required * 0.6),
            )
            logging.warning("[Ensemble] downstream Director/Critic rejection risk is high")
        else:
            logging.warning("[Ensemble] all candidates were short; keeping longest tactical_doc candidate")
        return candidates[:1]

    def _score_candidates_for_director(
        self,
        candidates: list[dict],
        prev_arc_context: str,
        constraint_block: str,
        *,
        prev_equipment: list[str] | None = None,
        forbidden_items: list[str] | None = None,
    ) -> tuple[list[dict], list[dict], dict]:
        scored_candidates = []
        for candidate in candidates:
            score, issues = self._evaluate_candidate(
                candidate,
                prev_arc_context,
                constraint_block,
                prev_equipment=prev_equipment,
                forbidden_items=forbidden_items,
            )
            candidate["_score"] = score
            candidate["_issues"] = issues
            scored_candidates.append(candidate)

        scored_candidates.sort(key=lambda item: item.get("_score", 0), reverse=True)
        structural_min_score = 50
        director_candidates = [item for item in scored_candidates if item.get("_score", 0) >= structural_min_score]
        if not director_candidates:
            director_candidates = scored_candidates[:1]
        cleaner_director_candidates = [
            item for item in director_candidates if not _has_generic_episode_detail_issue(item)
        ]
        if cleaner_director_candidates:
            director_candidates = cleaner_director_candidates
        diversity_summary = self._summarize_candidate_diversity(director_candidates)
        return scored_candidates, director_candidates, diversity_summary

    def _log_scored_candidates(
        self,
        scored_candidates: list[dict],
        director_candidates: list[dict],
        *,
        total_candidates: int,
    ) -> None:
        logging.warning("[Ensemble] candidate scores:")
        filtered_count = total_candidates - len(scored_candidates)
        filter_note = f" ({filtered_count} short candidates filtered)" if filtered_count > 0 else ""
        self._operator_log(
            f"[Arc] {len(scored_candidates)}/{total_candidates} candidates scored{filter_note}",
            meta={
                "scored_candidates": len(scored_candidates),
                "total_candidates": total_candidates,
                "filtered_count": filtered_count,
            },
        )
        for candidate in scored_candidates:
            strategy = candidate.get("_strategy", "?")
            score = candidate.get("_score", 0)
            issues = candidate.get("_issues", [])
            issue_summary = f" - {issues[0][:40]}..." if issues else ""
            marker = "selected" if candidate in director_candidates else "held"
            logging.info("%s %s: %s%s", marker, strategy, score, issue_summary)
            self._operator_log(
                f"[Arc] {marker} {strategy}: {score}{issue_summary}",
                meta={"strategy": strategy, "score": score, "qualified": candidate in director_candidates},
            )
        logging.info(
            "[TF-S2] Python scored %d candidates and defers final selection to Director",
            len(director_candidates),
        )

    def _apply_ensemble_metadata(
        self,
        director_candidates: list[dict],
        scored_candidates: list[dict],
        diversity_summary: dict,
    ) -> None:
        all_scores = [(candidate.get("_strategy", "?"), candidate.get("_score", 0)) for candidate in scored_candidates]
        for idx, candidate in enumerate(director_candidates):
            candidate["_ensemble_meta"] = {
                "best_strategy": candidate.get("_strategy", "unknown"),
                "best_score": candidate.get("_score", 0),
                "all_scores": all_scores,
                "total_candidates": len(director_candidates),
                "candidate_index": idx,
                "strategy": candidate.get("_strategy", "unknown"),
                "score": candidate.get("_score", 0),
                "diversity": diversity_summary,
            }

        for candidate in scored_candidates:
            candidate.pop("_score", None)
            candidate.pop("_issues", None)

    def _coerce_ep_count(self, value: object, default: int) -> int:
        if isinstance(value, bool):
            value = default
        if isinstance(value, str):
            match = re.search(r"(\d+)", value)
            value = int(match.group(1)) if match else default
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = default
        return max(_ARC_MIN_EP_COUNT, min(_ARC_MAX_EP_COUNT, value))

    def _normalize_pace_mode(self, raw_mode: object) -> str:
        mode = str(raw_mode or "").strip().lower()
        if not mode:
            return ""
        if "compressed" in mode or "blitz" in mode:
            return "compressed"
        if "expanded" in mode or "epic" in mode:
            return "expanded"
        if "standard" in mode:
            return "standard"
        return ""

    def _pace_mode_bounds(self, pace_mode: str) -> tuple[int, int]:
        if pace_mode == "compressed":
            return 2, 3
        if pace_mode == "expanded":
            return 6, 6
        return 4, 5

    def _infer_pace_mode(self, ep_count: int) -> str:
        if ep_count <= 3:
            return "compressed"
        if ep_count >= 6:
            return "expanded"
        return "standard"

    def _resolve_candidate_ep_count(self, candidate: dict, fallback_ep_count: int) -> int:
        raw_ep_count = candidate.get("ep_count") if isinstance(candidate, dict) else fallback_ep_count
        return self._coerce_ep_count(raw_ep_count, fallback_ep_count)

    def _build_pacing_signal_guide(
        self,
        curr_block: dict | None,
        ep_count_suggestion: int,
        pacing_signals: dict,
    ) -> str:
        pace_mode = pacing_signals.get("suggested_pace_mode") or self._infer_pace_mode(ep_count_suggestion)
        content_len = pacing_signals.get("content_len", 0)
        sentence_count = pacing_signals.get("sentence_count", 0)
        tension_level = pacing_signals.get("tension_level", "")
        item_hint_count = pacing_signals.get("item_hint_count", 0)
        reward_present = pacing_signals.get("reward_present", False)
        solution_present = pacing_signals.get("solution_present", False)
        low_resource_block = pacing_signals.get("low_resource_block", False)
        pacing_reason = pacing_signals.get("pacing_reason", "")
        block_title = curr_block.get("title", "") if isinstance(curr_block, dict) else ""

        lines = [
            "### [Pacing Signals - Python collected, LLM decides final ep_count]",
            f"- suggested_ep_count: {ep_count_suggestion}",
            f"- suggested_pace_mode: {pace_mode}",
            f"- content_len_chars: {content_len}",
            f"- sentence_count: {sentence_count}",
            f"- item_hint_count: {item_hint_count}",
            f"- reward_present: {bool(reward_present)}",
            f"- solution_present: {bool(solution_present)}",
            f"- low_resource_block: {bool(low_resource_block)}",
        ]
        if tension_level not in ("", None):
            lines.append(f"- tension_level: {tension_level}")
        if block_title:
            lines.append(f"- block_title: {block_title}")
        if pacing_reason:
            lines.append(f"- suggestion_reason: {pacing_reason}")

        lines.extend(
            [
                "",
                "### [Pacing Ownership Rules]",
                "- 최종 ep_count 판단은 Python이 아니라 너의 책임이다.",
                "- suggested_ep_count는 참고값으로만 보고, 최종 ep_count와 pace_mode를 함께 결정하라.",
                "- 자원(item/reward/solution)이 적으면 설명을 늘이지 말고 tactical progression을 더 촘촘하게 압축하라.",
                "- 각 화마다 상태, 압박, 관계, 회수 중 최소 1개의 의미 있는 변화가 반드시 있어야 한다.",
                "- 하드 자원이 적을수록 감정 설명 반복과 준비 동작만 있는 beat를 줄여라.",
                "- item이나 reward가 적을수록 callback, foreshadow, payoff 밀도를 더 높여라.",
            ]
        )
        return "\n".join(lines)

    def _normalize_pacing_contract(self, result: dict, ep_start: int, ep_count_suggestion: int) -> dict:
        pacing_decision = result.get("pacing_decision")
        if not isinstance(pacing_decision, dict):
            pacing_decision = {}

        pace_mode = self._normalize_pace_mode(pacing_decision.get("pace_mode") or pacing_decision.get("chosen_pacing"))
        ep_count = self._coerce_ep_count(result.get("ep_count"), ep_count_suggestion)

        if pace_mode:
            min_ep, max_ep = self._pace_mode_bounds(pace_mode)
            if ep_count < min_ep or ep_count > max_ep:
                logging.warning(
                    " [Stage2-Pacing] pace_mode=%s but ep_count=%s -> clamp to %s~%s",
                    pace_mode,
                    ep_count,
                    min_ep,
                    max_ep,
                )
            ep_count = max(min_ep, min(max_ep, ep_count))
        else:
            pace_mode = self._infer_pace_mode(ep_count)

        result["ep_start"] = ep_start
        result["ep_count"] = ep_count
        result["ep_end"] = ep_start + ep_count - 1
        pacing_decision["pace_mode"] = pace_mode
        pacing_decision.setdefault("ep_count_reasoning", "")
        pacing_decision.setdefault("density_focus", "")
        result["pacing_decision"] = pacing_decision
        return result

    def _merge_single_arc_feedback(self, feedback: str, strategy_feedback: str) -> str:
        """전략별 피드백을 Arc 생성용 payload로 병합한다."""
        merged_feedback = feedback or ""
        if not strategy_feedback:
            return merged_feedback
        if merged_feedback:
            return f"{merged_feedback}\n\n[전략별 보정 피드백]\n{strategy_feedback}"
        return f"[전략별 보정 피드백]\n{strategy_feedback}"

    def _build_single_arc_protagonist_instructions(
        self,
        protagonist_config: dict | None,
        genre: str,
    ) -> str:
        """주인공 설정을 Arc prompt block으로 정리한다."""
        if not protagonist_config:
            return ""

        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")
        lines = [f"- 세계 출신: {world_origin}", f"- 환생 유형: {incarnation_type}"]

        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                lines.append(
                    get_primitive_constraint_section(
                        protagonist_config,
                        genre=genre,
                        length="medium",
                    )
                )
            else:
                lines.append("⚠️ [원시인 모드] 현대 용어 절대 금지!")
        else:
            lines.append("📝 주인공은 현대 사회를 알고 있음")

        if incarnation_type == "회귀자":
            lines.append("🔄 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)")
        elif incarnation_type == "빙의자":
            lines.append("👤 원래 인물의 기억/관계를 의식")
        elif incarnation_type == "환생자":
            lines.append("👶 전생의 기억이 있음")

        return "\n[🌍 주인공 설정]\n" + "\n".join(lines)

    def _build_single_arc_generation_context(
        self,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        protagonist_config: dict | None,
        entity_registry: dict | None,
        genre: str,
    ) -> dict:
        """Arc 생성 prompt에 필요한 block/setting guide bundle을 구성한다."""
        prompt_context = {
            "prohibition_summary": self._generate_prohibition_summary(prev_arc_context, constraint_block),
            "protagonist_instructions": self._build_single_arc_protagonist_instructions(
                protagonist_config,
                genre,
            ),
            "entity_registry_section": self._format_entity_registry(entity_registry) if entity_registry else "",
            "genre_ext_guide": "",
            "extended_block_guide": "",
            "block_event_guard": _build_block_event_guard(curr_block),
            "curr_block_authority": _format_curr_block_authority(curr_block),
            "carryover_authority_packet": _render_carryover_authority_packet(prev_arc_context),
        }

        if isinstance(curr_block, dict):
            genre_ext = curr_block.get("genre_ext") or (curr_block.get("raw_data") or {}).get("genre_ext")
            if genre_ext and isinstance(genre_ext, dict):
                genre_ext_lines = [
                    "### [장르 특화 정보 - genre_ext]",
                    "아래 값은 Arc tactical_doc/state_constraints에 반드시 반영해야 합니다:",
                ]
                if genre_ext.get("capital_after"):
                    genre_ext_lines.append(
                        f"- [필수] arc_end_state의 capital/total_assets는 target `{genre_ext.get('capital_after')}`"
                        "와 크게 괴리되지 않게 유지하세요 (권장 ±30%)."
                    )
                    genre_ext_lines.append(
                        "- [금지] 블록 DNA에 없는 대규모 자금 유입/차입으로 수치를 임의 상향하지 마세요."
                    )
                for key, value in genre_ext.items():
                    genre_ext_lines.append(f"- **{key}**: {value}")
                prompt_context["genre_ext_guide"] = "\n".join(genre_ext_lines)

        block_standard_fields = {"block_id", "title", "content", "genre_ext", "regression_ext", "raw_data"}
        if isinstance(curr_block, dict):
            extended_block_parts = []
            for key, value in curr_block.items():
                if key in block_standard_fields or not value:
                    continue
                if isinstance(value, list):
                    serialized = ", ".join(str(item) for item in value) if value else ""
                elif isinstance(value, dict):
                    serialized = json.dumps(value, ensure_ascii=False)
                else:
                    serialized = str(value)
                if serialized:
                    extended_block_parts.append(f"- **{key}**: {serialized}")
            if extended_block_parts:
                prompt_context["extended_block_guide"] = (
                    "### [블록 확장 메타데이터 - 반드시 Arc에 반영]\n"
                    "아래는 treatment 설계 시 포함된 핵심 연출 데이터입니다. "
                    "모든 항목을 Arc tactical_doc에 반영하세요.\n"
                    "특히 foreshadow는 tactical_doc 씬에 직접 심고, "
                    "callback은 이전 복선이 회수되는 씬을 명시하고, "
                    "emotional_beat/tension_level은 화별 감정 밀도 설계에 반영하세요:\n"
                    + "\n".join(extended_block_parts)
                )

        return prompt_context

    def _build_single_arc_prompt_bundle(
        self,
        strategy: dict,
        prompt_context: dict,
        constraint_block: str,
        prev_arc_context: str,
        curr_block: dict,
        pacing_signal_guide: str,
        vol_strategy: str,
        assets: dict,
        merged_feedback: str,
        protagonist_name: str,
        genre: str,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        cache_name: str,
    ) -> tuple[str | None, str]:
        """cached prompt와 full fallback prompt를 함께 조립한다."""
        critical_keys = []
        try:
            if (
                hasattr(self, "context")
                and hasattr(self.context, "sys")
                and hasattr(self.context.sys, "hud")
                and self.context.sys.hud
            ):
                critical_keys = self.context.sys.hud.get_critical_keys()
        except Exception as e:
            logging.debug("[TF-26] critical_keys lookup failed: %s", str(e)[:100])

        use_cached_context = bool(cache_name)
        cached_context_stub = "[context cached: refer to cached_content]"
        state_constraints_genre_field = self._escape_braces(build_state_constraints_schema(genre, critical_keys))
        status_shadow_schema = self._escape_braces(build_status_shadow_schema(genre, critical_keys))
        vol_strategy_prompt = _fit_arc_prompt_context(vol_strategy, 6000) if vol_strategy else "(없음)"
        assets_prompt = _fit_arc_prompt_context(json.dumps(assets, ensure_ascii=False), 6000) if assets else "{}"
        feedback_prompt = _fit_arc_prompt_context(merged_feedback, 9000) if merged_feedback else "(없음)"

        prompt_kwargs = {
            "strategy_name": strategy["name"].upper(),
            "strategy_focus": strategy["focus"],
            "strategy_style": strategy["style"],
            "prohibition_summary": self._escape_braces(prompt_context["prohibition_summary"]),
            "protagonist_name": self._escape_braces(protagonist_name),
            "protagonist_instructions": self._escape_braces(prompt_context["protagonist_instructions"]),
            "curr_block": self._escape_braces(prompt_context["curr_block_authority"]),
            "pacing_signal_guide": self._escape_braces(pacing_signal_guide or ""),
            "block_event_guard": self._escape_braces(prompt_context["block_event_guard"]),
            "carryover_authority_packet": self._escape_braces(
                prompt_context["carryover_authority_packet"] or "(first arc or no explicit carryover packet)"
            ),
            "genre_ext_guide": self._escape_braces(prompt_context["genre_ext_guide"]),
            "extended_block_guide": self._escape_braces(prompt_context["extended_block_guide"]),
            "vol_strategy": self._escape_braces(vol_strategy_prompt),
            "assets": self._escape_braces(assets_prompt),
            "feedback": self._escape_braces(feedback_prompt),
            "entity_registry_section": self._escape_braces(prompt_context["entity_registry_section"]),
            "energy_system_block": self._escape_braces(self._get_energy_system_block(genre, critical_keys)),
            "state_constraints_genre_field": state_constraints_genre_field,
            "status_shadow_schema": status_shadow_schema,
            "arc_no": arc_no,
            "ep_start": ep_start,
            "ep_end": ep_end,
        }

        prompt = self._prompt_loader.load(
            "ensemble",
            "ENSEMBLE_ARC_PROMPT",
            constraint_block=self._escape_braces(
                cached_context_stub if use_cached_context else (constraint_block or "(없음)")
            ),
            prev_arc_context=self._escape_braces(
                cached_context_stub if use_cached_context else (prev_arc_context or "시작점")
            ),
            **prompt_kwargs,
        )

        full_prompt_fallback = prompt
        if use_cached_context:
            full_prompt_fallback = self._prompt_loader.load(
                "ensemble",
                "ENSEMBLE_ARC_PROMPT",
                constraint_block=self._escape_braces(constraint_block or "(없음)"),
                prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
                **prompt_kwargs,
            )
            if not full_prompt_fallback:
                full_prompt_fallback = prompt

        return prompt, full_prompt_fallback

    def _request_single_arc_candidate(
        self,
        strategy: dict,
        prompt: str | None,
        cache_name: str,
        full_prompt_fallback: str,
        retry: int,
    ) -> dict | None:
        """LLM 요청과 JSON normalization을 담당한다."""
        if not prompt:
            logging.warning("[ArcEnsemble] ENSEMBLE_ARC_PROMPT not found in prompt loader")
            return None

        thinking = "high" if retry == 0 else "medium"
        result = self._ask_with_cached_context(
            cache_name=cache_name,
            prompt=prompt,
            temperature=strategy["temperature"],
            thinking_level=thinking,
            full_prompt_fallback=full_prompt_fallback,
            response_schema=ARC_DESIGN_SCHEMA,
        )

        if isinstance(result, str):
            result = self._extract_json_robust(result)
        if not isinstance(result, dict) or result.get("parsing_error"):
            return None
        return result

    def _finalize_single_arc_candidate(
        self,
        result: dict,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        ep_count_suggestion: int | None,
    ) -> dict:
        """Arc 응답을 pacing contract와 required fields 기준으로 마감한다."""
        normalized = self._normalize_pacing_contract(
            result,
            ep_start,
            ep_count_suggestion or Stage2Limits.DEFAULT_EP_COUNT,
        )
        return self._ensure_required_fields(
            normalized,
            arc_no,
            ep_start,
            normalized.get("ep_end", ep_end),
        )

    def _generate_single(
        self,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        assets: dict,
        feedback: str,
        strategy_feedback: str = "",  # [EnsembleFB] 전략별 보정 피드백
        strategy: dict = None,
        protagonist_name: str = "주인공",  # [V60.18]
        protagonist_config: dict = None,  # [V60.88]
        entity_registry: dict = None,  # [V60.92]
        genre: str = GenreTypes.WUXIA,  # [V61.3] 미리 로드한 genre (thread-safety)
        ep_count_suggestion: int = None,
        pacing_signal_guide: str = "",
        retry: int = 0,  # [V61.5] 재시도 횟수
        cache_name: str = "",  # [Tier4-11] shared context cache name
    ) -> dict | None:
        """단일 전략으로 Arc 생성"""
        try:
            merged_feedback = self._merge_single_arc_feedback(feedback, strategy_feedback)
            prompt_context = self._build_single_arc_generation_context(
                curr_block,
                prev_arc_context,
                constraint_block,
                protagonist_config,
                entity_registry,
                genre,
            )
            prompt, full_prompt_fallback = self._build_single_arc_prompt_bundle(
                strategy,
                prompt_context,
                constraint_block,
                prev_arc_context,
                curr_block,
                pacing_signal_guide,
                vol_strategy,
                assets,
                merged_feedback,
                protagonist_name,
                genre,
                arc_no,
                ep_start,
                ep_end,
                cache_name,
            )
            result = self._request_single_arc_candidate(
                strategy,
                prompt,
                cache_name,
                full_prompt_fallback,
                retry,
            )
            if result is None:
                return None
            return self._finalize_single_arc_candidate(
                result,
                arc_no,
                ep_start,
                ep_end,
                ep_count_suggestion,
            )

        except Exception as e:
            # [V61.3] stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] ArcEnsemble _generate_single 크래시: {str(e)[:80]}")
            logging.error(traceback.format_exc())
            return None

    def _evaluate_candidate(
        self,
        candidate: dict,
        prev_arc_context: str,
        constraint_block: str,
        prev_equipment: list[str] | None = None,
        forbidden_items: list[str] | None = None,
    ) -> tuple[int, list[str]]:
        """
        후보 평가 (100점 만점)

        평가 기준:
        - 필수 필드 완성도 (20점)
        - 제약 조건 준수 (30점)
        - 연속성 (25점)
        - tactical_doc 품질 (25점)
        """
        score = 100
        issues = []
        candidate_arc_no = _coerce_episode_number(candidate.get("arc_no"), 0)
        candidate_ep_count = self._resolve_candidate_ep_count(candidate, Stage2Limits.DEFAULT_EP_COUNT)
        candidate_ep_start = _coerce_episode_number(candidate.get("ep_start"), 1)
        candidate_ep_end = candidate_ep_start + candidate_ep_count - 1

        # 1. 필수 필드 완성도 (20점)
        # [V61] state_changes 추가
        required_fields = ["arc_no", "ep_count", "tactical_doc", "joint_docs", "state_constraints", "state_changes"]
        for field in required_fields:
            if field not in candidate or not candidate[field]:
                score -= 4
                issues.append(f"필수 필드 누락: {field}")

        contract_penalty, contract_issues = _score_candidate_contract_health(
            candidate,
            prev_arc_context,
            genre=getattr(self, "_genre", ""),
            candidate_arc_no=candidate_arc_no,
            candidate_ep_start=candidate_ep_start,
            candidate_ep_end=candidate_ep_end,
        )
        score -= contract_penalty
        issues.extend(contract_issues)

        # 2. 제약 조건 준수 (30점)
        if constraint_block or forbidden_items or candidate.get("_forbidden_items"):
            # 획득 금지 아이템 검사
            # [BUG-F] protagonist_items 우선 폴백
            _sc = candidate.get("state_constraints", {})
            items_acquired = _sc.get("protagonist_items") or _sc.get("items_acquired", [])
            tactical = candidate.get("tactical_doc", "")
            # [V60.37] 타입 안전성
            if not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""

            # Tier 1: 구조적 금지 아이템 (호출자 주입) 우선
            _forbidden_structured = forbidden_items
            if _forbidden_structured is None:
                _forbidden_structured = candidate.get("_forbidden_items", [])

            if _forbidden_structured:
                forbidden_items = [str(item).strip() for item in _forbidden_structured if str(item).strip()]
            else:
                # Tier 3: 문자열 regex 폴백
                forbidden_items = _extract_forbidden_items(constraint_block)
            # [V70] items_acquired를 str 리스트로 변환 (substring 오탐 방지)
            _acq_strs = [str(i).strip() for i in items_acquired] if isinstance(items_acquired, list) else []

            # [BUG-A] 기존 소지품 화이트리스트 — 이미 보유 중인 아이템은 금지 체크 스킵
            _existing_equip: set[str] = set()
            _start_eq = candidate.get("state_constraints", {}).get("arc_start_state", {}).get("equipment", [])
            if isinstance(_start_eq, list):
                _existing_equip.update(str(e).strip() for e in _start_eq if str(e).strip())
            _prev_eq = prev_equipment
            if _prev_eq is None:
                _prev_eq = candidate.get("_prev_equipment", [])
            if isinstance(_prev_eq, list):
                _existing_equip.update(str(e).strip() for e in _prev_eq if str(e).strip())

            for item in forbidden_items:
                if item in _existing_equip:
                    continue  # 이미 보유 중인 아이템은 스킵
                if item in _acq_strs or ("획득" in tactical and item in tactical):
                    score -= 15
                    issues.append(f"금지 아이템 획득 시도: {item}")

        # 3. 연속성 (25점)
        if (
            (prev_arc_context and prev_arc_context != "서사 시작점")
            or prev_equipment
            or candidate.get("_prev_equipment")
        ):
            # 시작 위치 검사
            start_state = candidate.get("state_constraints", {}).get("arc_start_state", {})
            carryover_packet = _extract_carryover_authority_packet(prev_arc_context)
            packet_location = str(carryover_packet.get("next_arc_start_location", "") or "").strip()
            if packet_location:
                curr_loc = start_state.get("location", "")
                if curr_loc and packet_location not in curr_loc and curr_loc not in packet_location:
                    score -= 12
                    issues.append(f"carryover authority 시작 위치 불일치: expected={packet_location}, 현재={curr_loc}")
            elif isinstance(prev_arc_context, str) and "위치" in prev_arc_context:
                prev_loc_match = re.search(r"위치[:\]]\s*([가-힣\w\s]+)", prev_arc_context)
                if prev_loc_match:
                    prev_loc = prev_loc_match.group(1).strip()[:20]
                    curr_loc = start_state.get("location", "")
                    if prev_loc and curr_loc and prev_loc not in curr_loc and curr_loc not in prev_loc:
                        score -= 10
                        issues.append(f"시작 위치 불일치: 이전={prev_loc}, 현재={curr_loc}")

            # 소지품 계승 검사
            curr_equip = start_state.get("equipment", [])
            prev_equipment_items: list[str] = []

            # Tier 1: 구조적 이전 Arc 소지품 (호출자 주입) 우선
            _prev_structured = prev_equipment
            if _prev_structured is None:
                _prev_structured = candidate.get("_prev_equipment", [])
            if _prev_structured:
                prev_equipment_items = [str(item).strip() for item in _prev_structured if str(item).strip()]

            if not prev_equipment_items:
                prev_equipment_items = _normalize_carryover_packet_list(
                    carryover_packet.get("next_arc_start_equipment", [])
                )

            # Tier 3: 문자열 컨텍스트 폴백
            if not prev_equipment_items and isinstance(prev_arc_context, str) and "소지품" in prev_arc_context:
                prev_inv_match = re.search(r"소지품[:\]]\s*([^\n]+)", prev_arc_context)
                if prev_inv_match:
                    prev_equipment_items = [x.strip() for x in prev_inv_match.group(1).split(",") if x.strip()]

            if prev_equipment_items and not curr_equip:
                score -= 10
                issues.append("carryover authority 시작 소지품 누락")
            elif prev_equipment_items and curr_equip:
                for item in prev_equipment_items[:5]:
                    if not any(item in str(ce) or str(ce) in item for ce in curr_equip):
                        score -= 5
                        issues.append(f"소지품 미계승: {item}")

        # 4. tactical_doc 품질 (25점) - [V60.73] 가변 페이싱 기준 (화당 500자)
        tactical = candidate.get("tactical_doc", "")
        # [V60.37] 타입 안전성
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""
        min_length = candidate_ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 3화=1500자, 4화=2000자, 6화=3000자
        recommended_length = candidate_ep_count * 600  # 권장: 화당 600자
        if len(tactical) < min_length:
            score -= 40  # 최소 기준 미달은 사실상 실격
            issues.append(
                f"[CRITICAL] tactical_doc 분량 심각 부족: {len(tactical)}자 (최소 {min_length}자, ep_count={candidate_ep_count})"
            )
        elif len(tactical) < recommended_length:
            score -= 10
            issues.append(f"tactical_doc 분량 미흡: {len(tactical)}자 (권장 {recommended_length}자)")
        elif len(tactical) < candidate_ep_count * 700:
            score -= 5
            issues.append(f"tactical_doc 분량 보통: {len(tactical)}자")

        # 화수별 구분 검사
        ep_mentions = len(re.findall(r"제\s*\d+\s*화", tactical))
        if ep_mentions < candidate_ep_count:
            score -= 5
            issues.append(f"화수 구분 부족: {ep_mentions}/{candidate_ep_count}")

        return max(0, score), issues

    def _ensure_required_fields(self, result: dict, arc_no: int, ep_start: int, ep_end: int) -> dict:
        """필수 필드 보장"""
        if "arc_no" not in result:
            result["arc_no"] = arc_no
        if "ep_start" not in result:
            result["ep_start"] = ep_start
        if "ep_end" not in result:
            result["ep_end"] = ep_end
        if "ep_count" not in result:
            result["ep_count"] = ep_end - ep_start + 1
        result["episode_details"] = _build_canonical_episode_details(result, ep_start=ep_start, ep_end=ep_end)

        # [Sweep47] 타입도 검증 — LLM이 list/string 반환 시 AttributeError 방지
        if "state_constraints" not in result or not isinstance(result["state_constraints"], dict):
            result["state_constraints"] = {
                "arc_start_state": {"location": "이전 Arc 종료 위치", "equipment": []},
                "arc_end_state": {"location": "알 수 없음", "equipment": []},
                "items_acquired": [],
                "items_consumed": [],
            }

        if "joint_docs" not in result:
            result["joint_docs"] = {"final_location": "알 수 없음", "physical_inventory": [], "world_joint": ""}
        joint_docs = result["joint_docs"] if isinstance(result.get("joint_docs"), dict) else {}
        state_constraints = result["state_constraints"] if isinstance(result.get("state_constraints"), dict) else {}
        arc_start_state = state_constraints.get("arc_start_state", {}) if isinstance(state_constraints, dict) else {}
        arc_end_state = state_constraints.get("arc_end_state", {}) if isinstance(state_constraints, dict) else {}
        if isinstance(arc_start_state, dict):
            arc_start_state["equipment"] = _normalize_state_contract_list(arc_start_state.get("equipment", []))
            state_constraints["arc_start_state"] = arc_start_state
        if isinstance(arc_end_state, dict):
            arc_end_state["equipment"] = _normalize_state_contract_list(arc_end_state.get("equipment", []))
            state_constraints["arc_end_state"] = arc_end_state
        joint_inventory = _normalize_state_contract_list(joint_docs.get("physical_inventory", []))
        if not joint_inventory and isinstance(arc_end_state, dict):
            joint_inventory = list(arc_end_state.get("equipment", []) or [])
        joint_docs["physical_inventory"] = joint_inventory
        end_location = re.sub(r"\s+", " ", str((arc_end_state or {}).get("location", "") or "")).strip()
        joint_location = re.sub(r"\s+", " ", str(joint_docs.get("final_location", "") or "")).strip()
        if not joint_location and end_location:
            joint_docs["final_location"] = end_location
        elif not end_location and joint_location and isinstance(arc_end_state, dict):
            arc_end_state["location"] = joint_location
            state_constraints["arc_end_state"] = arc_end_state
        result["joint_docs"] = joint_docs
        result["state_constraints"] = state_constraints

        if "status_shadow" not in result:
            result["status_shadow"] = {
                "key_stat_change": "변동 없음",
                "expected_injuries": "없음",
                "item_consumption": [],
            }
        # backward-compat: 기존 소비자가 internal_energy_loss를 읽으므로 key_stat_change에서 복사
        _ss = result["status_shadow"]
        if "key_stat_change" in _ss and "internal_energy_loss" not in _ss:
            _ss["internal_energy_loss"] = _ss["key_stat_change"]

        # [V61] state_changes 필드 보장
        if "state_changes" not in result:
            result["state_changes"] = {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            }
        else:
            # 하위 필드 보장
            sc = result["state_changes"]
            if "timeline" not in sc:
                sc["timeline"] = {"start": {}, "end": {}}
            elif not isinstance(sc["timeline"], dict):
                sc["timeline"] = {"start": {}, "end": {}}
            else:
                if "start" not in sc["timeline"]:
                    sc["timeline"]["start"] = {}
                if "end" not in sc["timeline"]:
                    sc["timeline"]["end"] = {}
            if "npc_deaths" not in sc:
                sc["npc_deaths"] = []
            if "skill_acquisitions" not in sc:
                sc["skill_acquisitions"] = []
            if "relationship_changes" not in sc:
                sc["relationship_changes"] = []
            if "major_items" not in sc:
                sc["major_items"] = []
            if "resolved_plots" not in sc:
                sc["resolved_plots"] = []

        return result

    def _safe_tactical_str(self, tactical) -> str:
        """
        [V60.74] tactical_doc을 안전하게 문자열로 변환

        Args:
            tactical: str, dict, list, None 등 다양한 타입

        Returns:
            str: 변환된 문자열
        """
        if isinstance(tactical, str):
            return tactical
        if tactical is None:
            return ""
        if isinstance(tactical, dict):
            # dict라면 값들을 조인 (content, text 등 우선 시도)
            if "content" in tactical:
                return str(tactical["content"])
            if "text" in tactical:
                return str(tactical["text"])
            # 그 외에는 모든 값 조인
            return "\n".join(str(v) for v in tactical.values() if v)
        if isinstance(tactical, list):
            return "\n".join(str(item) for item in tactical if item)
        # 기타 타입
        return str(tactical)

    def _generate_prohibition_summary(self, prev_arc_context: str, constraint_block: str) -> str:
        """
        [V60.13] 최우선 금지 사항 요약 생성

        프롬프트 최상단에 배치하여 LLM이 절대 무시할 수 없도록 함
        """
        lines = []
        carryover_packet = _extract_carryover_authority_packet(prev_arc_context)
        carryover_location = str(carryover_packet.get("next_arc_start_location", "") or "").strip()
        carryover_equipment = _normalize_carryover_packet_list(carryover_packet.get("next_arc_start_equipment", []))
        carryover_injuries = str(carryover_packet.get("next_arc_start_injuries", "") or "").strip()
        carryover_energy = str(carryover_packet.get("next_arc_start_internal_energy", "") or "").strip()

        # 1. 시작 상태 추출 (prev_arc_context에서)
        if prev_arc_context:
            if carryover_location:
                lines.append(f"✅ 시작 위치: {carryover_location} (Carryover Authority Packet 기준으로 시작해야 함!)")
            if carryover_equipment:
                lines.append(f"✅ 시작 소지품: {carryover_equipment} (Carryover Authority Packet 기준으로 계승!)")
            if carryover_injuries:
                lines.append(f"✅ 시작 부상: {carryover_injuries} (Carryover Authority Packet 기준으로 시작!)")
            if carryover_energy:
                lines.append(f"✅ 시작 내공: {carryover_energy} (Carryover Authority Packet 기준으로 시작!)")
            # 내공 추출
            energy_match = re.search(r"내공[:\s]*(\d+)%", prev_arc_context)
            if energy_match:
                lines.append(f"✅ 시작 내공: {energy_match.group(1)}% (이 수치로 시작해야 함!)")

            # 부상 추출
            injury_patterns = ["완치", "없음", "중상", "경상", "부상"]
            for pattern in injury_patterns:
                if pattern in prev_arc_context:
                    if pattern in ["완치", "없음"]:
                        lines.append("✅ 시작 부상: 없음 (건강한 상태로 시작!)")
                    else:
                        lines.append(f"✅ 시작 부상: {pattern} (이 상태로 시작!)")
                    break

        # 2. 금지 아이템 추출 (constraint_block에서)
        if constraint_block:
            # ❌ 패턴 추출
            forbidden = _extract_forbidden_items(constraint_block)
            if forbidden:
                lines.append("")
                lines.append("🚫 절대 다시 획득/수여 금지 (잔고·수량이 달라도 동일 아이템으로 간주):")
                for item in forbidden[:10]:
                    # 박스 문자, 패딩, Arc 출처 주석 제거 → 핵심 아이템명만 추출
                    clean_item = str(item).strip()[:60]
                    if clean_item:
                        lines.append(f"   ❌ {clean_item}")
                lines.append("   ⚠️ items_acquired에 위 아이템명이 포함되면 즉시 REJECT됩니다.")

        # 3. 기본 경고
        if not lines:
            lines.append("(금지 사항 없음 - 첫 Arc)")

        return "\n".join(lines)

    # [V61.5] _escape_braces 오버라이드 제거 → BaseAgent의 이중 이스케이프 방지 로직 사용

    @staticmethod
    def _get_energy_system_block(genre: str, critical_keys: list[str] | None = None) -> str:
        """장르별 에너지(내공) 시스템 규칙 블록. 무협만 내공 규칙 포함."""
        if genre in ("wuxia", "무협"):
            return _WUXIA_ENERGY_BLOCK
        return _build_non_wuxia_energy_block(genre, critical_keys)

    def _format_entity_registry(self, entity_registry: dict) -> str:
        """
        [V60.92] Entity Registry를 프롬프트용 문자열로 변환
        NPC 명칭 일관성을 위해 등록된 이름만 사용하도록 안내
        """
        if not entity_registry:
            return ""

        lines = [
            "### [V60.92] 🏷️ Entity Registry - 명칭 일관성 필수!",
            "╔══════════════════════════════════════════════════════════════════╗",
            "║ ⚠️ 아래 등록된 이름만 사용하세요! 다른 명칭/별명 사용 금지!      ║",
            "╚══════════════════════════════════════════════════════════════════╝",
        ]

        categories = [
            ("characters", "👤 캐릭터"),
            ("organizations", "🏛️ 조직/문파"),
            ("locations", "📍 장소"),
            ("objects", "🗡️ 아이템/물건"),
            ("concepts", "📜 개념/기술"),
        ]

        has_content = False
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                has_content = True
                lines.append(f"\n{label}:")
                for item in items[:20]:  # 최대 20개
                    if isinstance(item, dict):
                        name = item.get("name", item.get("이름", str(item)))
                        alias = item.get("alias", item.get("별칭", ""))
                        if alias:
                            lines.append(f"  • {name} (={alias})")
                        else:
                            lines.append(f"  • {name}")
                    else:
                        lines.append(f"  • {item}")

        if not has_content:
            return ""

        lines.append("\n→ 위 목록에 없는 새 NPC/조직 등장 시 반드시 명확한 이름 부여!")
        return "\n".join(lines)


def create_ensemble_generator(
    context, client, model_tier: str = AIModels.DEFAULT_ARCHITECT
):  # [SSOT-P2] 호출부(main_a.py:L1513)가 model_tier 인자를 명시 전달
    """[V62.4] ArcEnsembleGenerator 생성 헬퍼 - gemini-2.5-pro 사용"""
    return ArcEnsembleGenerator(context, client, model_tier)
