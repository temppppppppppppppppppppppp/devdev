"""[B-1-7] Stage2 finalizer extracted from Stage2Orchestrator.

utf8-hygiene: allow-file -- legacy Korean regex and prompt strings predate this patch; item 1 changes are ASCII-bounded.
"""

import json
import logging
import re
import time
from copy import deepcopy
from typing import Any, Literal, NotRequired, TypedDict

from modules.core.artifact_logging import build_candidate_key, snapshot_logged_artifact
from modules.core.constants import VolumeSettings
from modules.core.genre_schema_builder import is_wuxia
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.metrics_collector import get_metrics_collector
from modules.core.numeric_consistency_checker import NumericConsistencyChecker
from modules.core.stage2_contracts import merge_stage2_authoritative_packet
from modules.core.stage2_entity_contract import normalize_stage2_arc_entity_contract
from modules.core.stage2_location_contract import collapse_stage2_location_label
from modules.core.stage2_partial_fix_contract import build_stage2_partial_fix_eval, normalize_stage2_fix_pack
from modules.models.arc import StateChangesDict, validate_arc


def _peek_scope_total_cost_usd() -> float:
    """Return the current metrics scope cost without resetting it."""
    try:
        collector = get_metrics_collector()
        if collector is None or not hasattr(collector, "peek_scope"):
            return 0.0
        scope = collector.peek_scope() or {}
        return float(scope.get("total_cost_usd", 0.0) or 0.0)
    except Exception as exc:
        logging.debug("[Stage2] metrics scope peek failed (non-blocking): %s", exc)
        return 0.0

_DB_ADVISORY_NOTICE = "(Python 자동 감지 — 오탐 가능, 참고용)"
_TACTICAL_EPISODE_HEADER_RE = re.compile(r"(?:^|\n)\s*(?:\[\s*)?제\s*\d+\s*화[^\n]*", re.MULTILINE)
_TACTICAL_START_STATE_LINE_RE = re.compile(r"^\s*\[시작 상태\].*$", re.MULTILINE)
_BLOCKING_ARC_PATCH_SIGNAL_CODES = frozenset({"episode_start_future_artifact"})
_NON_WUXIA_STATE_NOISE_KEYS = ("internal_energy", "realm", "qi_nature", "martial_arts")


def _extract_first_tactical_episode_section(tactical_doc: str) -> str:
    text = str(tactical_doc or "").strip()
    if not text:
        return ""

    matches = list(_TACTICAL_EPISODE_HEADER_RE.finditer(text))
    if not matches:
        return text

    first = matches[0].start()
    second = matches[1].start() if len(matches) > 1 else len(text)
    return text[first:second].strip()


def _extract_future_artifact_asset_keywords(start_state_line: str, matched_artifact: str) -> tuple[str, ...]:
    if not start_state_line or not matched_artifact:
        return ()

    artifact_idx = start_state_line.find(matched_artifact)
    if artifact_idx < 0:
        return ()

    asset_window = start_state_line[max(0, artifact_idx - 40) : artifact_idx]
    keywords: list[str] = []
    if "WTI" in asset_window:
        keywords.extend(["WTI", "원유"])
    if "금" in asset_window:
        keywords.append("금")
    if "코스피" in asset_window:
        keywords.append("코스피")

    deduped: list[str] = []
    for keyword in keywords:
        if keyword and keyword not in deduped:
            deduped.append(keyword)
    return tuple(deduped)


def _strip_non_wuxia_state_noise_for_persistence(refined_arc: dict, *, genre: str) -> list[str]:
    if not isinstance(refined_arc, dict) or is_wuxia(str(genre or "").strip()):
        return []

    state_constraints = refined_arc.get("state_constraints")
    if not isinstance(state_constraints, dict):
        return []

    removed_sections: list[str] = []
    for section_key in ("arc_start_state", "arc_end_state"):
        section = state_constraints.get(section_key)
        if not isinstance(section, dict):
            continue
        removed_keys = [key for key in _NON_WUXIA_STATE_NOISE_KEYS if key in section]
        if not removed_keys:
            continue
        for key in removed_keys:
            section.pop(key, None)
        removed_sections.append(f"{section_key}: {', '.join(removed_keys)}")

    refined_arc["state_constraints"] = state_constraints
    return removed_sections


def _log_non_wuxia_state_cleanup(ctx, *, global_arc_no: int, removed_sections: list[str], phase: str) -> None:
    if not removed_sections:
        return
    summary = "; ".join(removed_sections)
    ctx.ui.log(f"      🔧 [Non-Wuxia State Cleanup] Arc {global_arc_no} {phase}: {summary}")
    if callable(getattr(ctx, "audit_event", None)):
        ctx.audit_event(
            "field_repair",
            "non-wuxia persistence state noise removed",
            {"arc_no": global_arc_no, "phase": phase, "fields": removed_sections},
        )


def _find_future_artifact_action_sentence(body: str, action_terms: tuple[str, ...]) -> tuple[str, str]:
    if not body:
        return "", ""

    sentences = re.split(r"(?<=[.!?\n])\s+", body)
    for sentence in sentences:
        normalized = sentence.strip()
        if not normalized:
            continue
        matched_action = next((term for term in action_terms if term in normalized), "")
        if matched_action:
            return matched_action, normalized
    return "", ""


def _detect_episode_start_future_artifact_signal(tactical_doc: str) -> dict[str, str] | None:
    section = _extract_first_tactical_episode_section(tactical_doc)
    if not section:
        return None

    start_state_match = _TACTICAL_START_STATE_LINE_RE.search(section)
    if not start_state_match:
        return None

    start_state_line = start_state_match.group(0)
    body = section[start_state_match.end() :].replace("\n", " ")
    episode_header = section.splitlines()[0].strip() if section.splitlines() else "first_episode"

    rulebook = (
        (
            ("최종 매도 체결 확인서", "매도 체결 확인서"),
            ("전량 익절 청산", "전량 청산", "청산했다", "청산한다", "매도 주문", "매도했다", "매도한다"),
        ),
        (
            ("매수 체결 확인서",),
            ("매수 주문", "주문을 실행", "주문을 넣", "매수했다", "매입했다", "진입했다"),
        ),
    )
    for artifact_terms, action_terms in rulebook:
        matched_artifact = next((term for term in artifact_terms if term in start_state_line), "")
        if not matched_artifact:
            continue
        matched_action, action_sentence = _find_future_artifact_action_sentence(body, action_terms)
        if not matched_action:
            continue
        asset_keywords = _extract_future_artifact_asset_keywords(start_state_line, matched_artifact)
        if asset_keywords and not any(keyword in action_sentence for keyword in asset_keywords):
            continue
        return {
            "code": "episode_start_future_artifact",
            "detail": f"{episode_header}: {matched_artifact} precedes later action '{matched_action}'",
        }
    return None


def _render_start_state_field_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return json.dumps([value], ensure_ascii=False)
    return ""


def _replace_or_append_start_state_field(line: str, label: str, value: object) -> str:
    rendered = _render_start_state_field_value(value)
    if label == "위치":
        rendered = collapse_stage2_location_label(rendered) or rendered
    if not rendered:
        return line

    pattern = rf"({re.escape(label)}\s*:\s*)(.*?)(?=(?:,\s*[가-힣A-Za-z_ ]+\s*:|/\s*[가-힣A-Za-z_ ]+\s*:|$))"
    if re.search(pattern, line):
        return re.sub(pattern, lambda m: f"{m.group(1)}{rendered}", line, count=1)

    separator = " / " if "/" in line else ", "
    return f"{line}{separator}{label}: {rendered}"


def _build_start_state_line_from_structured_state(start_state: dict[str, Any]) -> str:
    line = "[시작 상태]"
    for label, key in (
        ("위치", "location"),
        ("소지품", "equipment"),
        ("부상", "injuries"),
        ("내공", "internal_energy"),
    ):
        rendered = _render_start_state_field_value(start_state.get(key))
        if not rendered:
            continue
        line = f"{line} {label}: {rendered}" if line == "[시작 상태]" else f"{line}, {label}: {rendered}"
    return line


def _sync_first_episode_start_state_line(tactical_doc: str, start_state: dict[str, Any]) -> str:
    text = str(tactical_doc or "")
    if not text or not isinstance(start_state, dict) or not start_state:
        return text

    episode_matches = list(_TACTICAL_EPISODE_HEADER_RE.finditer(text))
    if not episode_matches:
        return text

    first_start = episode_matches[0].start()
    first_end = episode_matches[1].start() if len(episode_matches) > 1 else len(text)
    first_section = text[first_start:first_end]
    start_state_match = _TACTICAL_START_STATE_LINE_RE.search(first_section)

    if start_state_match:
        synced_line = start_state_match.group(0).strip()
        synced_line = _replace_or_append_start_state_field(synced_line, "위치", start_state.get("location"))
        synced_line = _replace_or_append_start_state_field(synced_line, "소지품", start_state.get("equipment"))
        synced_line = _replace_or_append_start_state_field(synced_line, "부상", start_state.get("injuries"))
        synced_line = _replace_or_append_start_state_field(synced_line, "내공", start_state.get("internal_energy"))
        first_section = first_section[: start_state_match.start()] + synced_line + first_section[start_state_match.end() :]
    else:
        header_match = _TACTICAL_EPISODE_HEADER_RE.search(first_section)
        if not header_match:
            return text
        insert_pos = header_match.end()
        generated_line = _build_start_state_line_from_structured_state(start_state)
        suffix = "" if generated_line.endswith("\n") else "\n"
        first_section = first_section[:insert_pos] + "\n" + generated_line + suffix + first_section[insert_pos:]

    return text[:first_start] + first_section + text[first_end:]


def _coerce_inventory_items(raw: Any) -> list[Any]:
    if isinstance(raw, str):
        text = raw.strip()
        if not text or text == "[]":
            return []
        if text[:1] in {"[", "{"}:
            try:
                parsed = json.loads(text)
            except (TypeError, ValueError):
                return [raw]
            return _coerce_inventory_items(parsed)
        return [raw]
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, dict):
        return [raw] if raw else []
    return []


def _inventory_item_key(item: Any) -> str:
    if isinstance(item, dict):
        candidate = item.get("name") or item.get("item") or item.get("title") or ""
    else:
        candidate = item
    return str(candidate or "").strip()


def _inventory_item_dedupe_key(item: Any) -> str:
    key = _inventory_item_key(item)
    if key:
        return key
    if isinstance(item, dict):
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    return str(item)


def _compute_inventory_carryover(prev_inventory: Any, consumed: Any, acquired: Any) -> list[Any]:
    prev_items = _coerce_inventory_items(prev_inventory)
    acquired_items = _coerce_inventory_items(acquired)
    consumed_names = {
        name
        for name in (_inventory_item_key(item) for item in _coerce_inventory_items(consumed))
        if name
    }

    inherited: list[Any] = []
    seen_keys: set[str] = set()
    for item in prev_items:
        item_name = _inventory_item_key(item)
        if item_name and item_name in consumed_names:
            continue
        dedupe_key = _inventory_item_dedupe_key(item)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        inherited.append(item)

    for item in acquired_items:
        dedupe_key = _inventory_item_dedupe_key(item)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        inherited.append(item)

    return inherited


def _sync_stage2_end_state_inventory_contract(
    refined_arc: dict,
    prev_arc: dict | None,
) -> tuple[list[Any], bool, bool]:
    """Align arc_end_state.equipment and joint_docs.physical_inventory to one end-inventory truth."""
    state_constraints = refined_arc.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        state_constraints = {}
        refined_arc["state_constraints"] = state_constraints

    arc_end_state = state_constraints.get("arc_end_state", {})
    if not isinstance(arc_end_state, dict):
        arc_end_state = {}
        state_constraints["arc_end_state"] = arc_end_state

    joint_docs = refined_arc.get("joint_docs", {})
    if not isinstance(joint_docs, dict):
        joint_docs = {}
        refined_arc["joint_docs"] = joint_docs

    end_inventory = _coerce_inventory_items(arc_end_state.get("equipment", []))
    joint_inventory = _coerce_inventory_items(joint_docs.get("physical_inventory", []))

    canonical_inventory = end_inventory
    if not canonical_inventory and prev_arc:
        prev_joint = prev_arc.get("joint_docs", {}) or {}
        curr_status = refined_arc.get("status_shadow", {}) or {}
        canonical_inventory = _compute_inventory_carryover(
            prev_joint.get("physical_inventory", []),
            curr_status.get("item_consumption", []),
            state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", []),
        )
    if not canonical_inventory:
        canonical_inventory = joint_inventory

    joint_changed = joint_inventory != canonical_inventory
    end_changed = end_inventory != canonical_inventory
    if joint_changed:
        joint_docs["physical_inventory"] = canonical_inventory
    if end_changed:
        arc_end_state["equipment"] = canonical_inventory

    state_constraints["arc_end_state"] = arc_end_state
    refined_arc["state_constraints"] = state_constraints
    refined_arc["joint_docs"] = joint_docs
    return canonical_inventory, joint_changed, end_changed


def _sync_stage2_end_location_contract(refined_arc: dict) -> tuple[str, bool, bool]:
    """Align arc_end_state.location and joint_docs.final_location to the same canonical location."""
    state_constraints = refined_arc.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        state_constraints = {}
        refined_arc["state_constraints"] = state_constraints

    arc_end_state = state_constraints.get("arc_end_state", {})
    if not isinstance(arc_end_state, dict):
        arc_end_state = {}
        state_constraints["arc_end_state"] = arc_end_state

    joint_docs = refined_arc.get("joint_docs", {})
    if not isinstance(joint_docs, dict):
        joint_docs = {}
        refined_arc["joint_docs"] = joint_docs

    raw_end_location = str(arc_end_state.get("location") or "").strip()
    raw_final_location = str(joint_docs.get("final_location") or "").strip()
    end_location = collapse_stage2_location_label(raw_end_location)
    final_location = collapse_stage2_location_label(raw_final_location)
    canonical_location = end_location or final_location

    joint_changed = bool(canonical_location) and raw_final_location != canonical_location
    end_changed = bool(canonical_location) and raw_end_location != canonical_location
    if joint_changed:
        joint_docs["final_location"] = canonical_location
    if end_changed:
        arc_end_state["location"] = canonical_location

    state_constraints["arc_end_state"] = arc_end_state
    refined_arc["state_constraints"] = state_constraints
    refined_arc["joint_docs"] = joint_docs
    return canonical_location, joint_changed, end_changed


class Stage2PassPreparationResult(TypedDict):
    action: Literal["retry", "continue"]
    current_feedback: NotRequired[str]
    refined_arc: NotRequired[dict[str, Any]]


class Stage2PassFinalizeTailResult(TypedDict):
    action: Literal["retry", "break"]
    current_feedback: str
    last_refined_context: NotRequired[str]
    current_ep_start: NotRequired[int]
    director_feedback_for_fourphase: NotRequired[str]
    st_snapshot: NotRequired[Any]


class Stage2PassWithFixLoopResult(TypedDict):
    refined_arc: dict[str, Any]
    audit: dict[str, Any]
    decision: Literal["PASS", "REJECT"]
    score: int


def _build_stage2_prompt_version(*, generation_method: str, is_patch: bool = False) -> str | None:
    try:
        from modules.core.prompt_loader import PromptLoader

        method = str(generation_method or "").strip().lower()
        domains = ["analyst"] if "analyst" in method else ["ensemble"]
        if is_patch:
            domains.append("arc_generator")
        domains.append("director")
        return PromptLoader().compose_version_tag(*domains)
    except Exception as _e:
        logging.debug("[Stage2] prompt_version 계산 실패 (비차단): %s", _e)
        return None


def _to_num_with_korean_units(raw: object) -> float | None:
    """'23억', '1.2조', '+3만' 형식 텍스트 → float 변환."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None

    text = re.sub(r"\([^)]*\)", "", raw).strip()
    text = text.replace(",", "")
    if not text:
        return None

    sign = 1.0
    if text[0] in "+-":
        if text[0] == "-":
            sign = -1.0
        text = text[1:].strip()

    unit_map = (
        ("조", 1e12),
        ("억", 1e8),
        ("만", 1e4),
    )
    total = 0.0
    matched_unit = False

    for unit, mult in unit_map:
        value_pattern = rf"([0-9]+(?:\.[0-9]+)?)\s*{re.escape(unit)}"
        for value in re.findall(value_pattern, text):
            try:
                total += float(value) * mult
                matched_unit = True
            except ValueError:
                return None
        text = re.sub(value_pattern, "", text)

    if matched_unit:
        tail = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
        if tail:
            try:
                total += float(tail.group(1))
            except ValueError:
                return None
        return sign * total

    plain = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if not plain:
        return None
    try:
        return sign * float(plain.group(1))
    except ValueError:
        return None


def _relative_error(stated: float, actual: float) -> float:
    if actual == 0:
        return 0.0 if stated == 0 else float("inf")
    return abs(stated - actual) / abs(actual)


def _format_eok(value: float) -> str:
    return f"{value / 1e8:.1f}" + "억"


def _trim_hierarchical_summary(text: object, max_chars: int) -> str:
    """Hierarchical summary hard cap for long-serial anchors."""
    summary = str(text or "").strip()
    if not summary:
        return ""
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 12].rstrip() + "\n...(요약 절삭)"


def _check_tactical_arithmetic(tactical_doc: str) -> list[str]:
    """
    [NS-1-P] Verify arithmetic claims in tactical_doc with pure Python checks.
    Returns warning strings when mismatch is over 5%.
    """
    if not tactical_doc:
        return []

    tolerance = 0.05
    issues: list[str] = []

    num_with_unit = r"[\d,]+(?:\.[\d]+)?(?:조|억|만)?"
    mul_op = r"(?:[xX×*]|곱)"
    eq_op = r"(?:=|는|은|:)"
    bae = "배"

    mult_pattern = re.compile(
        rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
        rf"(?P<n>[\d,]+(?:\.[\d]+)?)\s*{bae}?\s*{eq_op}\s*"
        rf"(?P<c>{num_with_unit})"
    )
    pct_pattern = re.compile(
        rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
        rf"(?P<p>[\d,]+(?:\.[\d]+)?)%\s*{eq_op}\s*"
        rf"(?P<c>{num_with_unit})"
    )

    for match in mult_pattern.finditer(tactical_doc):
        a = _to_num_with_korean_units(match.group("a"))
        n = _to_num_with_korean_units(match.group("n"))
        stated = _to_num_with_korean_units(match.group("c"))
        if None in (a, n, stated):
            continue
        actual = a * n
        if _relative_error(stated, actual) > tolerance:
            issues.append(
                f"Arithmetic mismatch: {match.group(0).strip()} "
                f"(stated={match.group('c')}, actual={_format_eok(actual)})"
            )

    for match in pct_pattern.finditer(tactical_doc):
        a = _to_num_with_korean_units(match.group("a"))
        pct = _to_num_with_korean_units(match.group("p"))
        stated = _to_num_with_korean_units(match.group("c"))
        if None in (a, pct, stated):
            continue
        actual = a * (pct / 100.0)
        if _relative_error(stated, actual) > tolerance:
            issues.append(
                f"Arithmetic mismatch: {match.group(0).strip()} "
                f"(stated={match.group('c')}, actual={_format_eok(actual)})"
            )

    return issues


def _check_cross_arc_asset_continuity(tactical_doc: str, prev_arcs: list) -> list[str]:
    """[TF-57-C] 직전 Arc 자산 수치 → 현재 Arc 첫 에피소드 자산 연속성 advisory.

    직전 Arc arc_end_state 또는 tactical_doc 종료 상태에서 총자산 수치를 추출하고
    현재 tactical_doc에서 언급된 첫 자산 수치와 ±20% 이상 차이 시 advisory 반환.
    advisory-only — REJECT 강제 없음.
    """
    if not tactical_doc or not prev_arcs:
        return []

    import re as _re57c

    _asset_re = _re57c.compile(r"총자산\s*약?\s*(\d[\d.,]*)\s*억")

    # 직전 Arc 자산 추출 (arc_end_state 우선, tactical_doc 폴백)
    prev_arc = prev_arcs[-1]
    prev_asset: float | None = None

    _prev_end = prev_arc.get("state_constraints", {}).get("arc_end_state", {})
    for _key in ("total_assets", "asset", "assets"):
        _val = _prev_end.get(_key)
        if isinstance(_val, int | float) and _val > 0:
            prev_asset = float(_val)
            break

    if prev_asset is None:
        _prev_td = prev_arc.get("tactical_doc", "")
        _prev_matches = _asset_re.findall(_prev_td)  # 마지막 언급 = [-1]
        if _prev_matches:
            try:
                prev_asset = float(_prev_matches[-1].replace(",", "")) * 1e8
            except ValueError:
                pass

    if prev_asset is None or prev_asset <= 0:
        return []

    # 현재 Arc 첫 자산 언급 추출
    _curr_m = _asset_re.search(tactical_doc[:2000])  # 첫 2000자
    if not _curr_m:
        return []

    try:
        curr_asset = float(_curr_m.group(1).replace(",", "")) * 1e8
    except ValueError:
        return []

    if curr_asset <= 0:
        return []

    delta_pct = abs(curr_asset - prev_asset) / prev_asset
    if delta_pct > 0.20:
        return [
            f"[TF-57-C 자산 연속성 advisory] 직전 Arc 종료 자산 {prev_asset / 1e8:.1f}억 대비 "
            f"현재 Arc 첫 언급 자산 {curr_asset / 1e8:.1f}억 — {delta_pct * 100:.0f}% 차이 (허용 20% 초과). "
            "직전 Arc 계산과 정합하는지 확인하세요."
        ]
    return []


def _check_block_worldstate_alignment(
    enriched_block: dict,
    refined_arc: dict,
    arc_no: int,
    threshold_pct: float = 0.30,
) -> list[str]:
    """
    [NS-2] Compare treatment block goal numbers with arc_end_state values.
    Advisory-only warning (no forced reject).
    """
    warnings: list[str] = []

    if not isinstance(enriched_block, dict) or not isinstance(refined_arc, dict):
        return warnings

    genre_ext = enriched_block.get("genre_ext")
    if not isinstance(genre_ext, dict):
        return warnings

    state_constraints = refined_arc.get("state_constraints")
    if not isinstance(state_constraints, dict):
        return warnings

    arc_end_state = state_constraints.get("arc_end_state")
    if not isinstance(arc_end_state, dict):
        return warnings

    target_capital = _to_num_with_korean_units(genre_ext.get("capital_after"))
    if target_capital in (None, 0):
        return warnings

    actual_capital = None
    actual_key = None
    for key in ("total_assets", "assets", "capital", "total_capital"):
        value = _to_num_with_korean_units(arc_end_state.get(key))
        if value is not None:
            actual_capital = value
            actual_key = key
            break

    if actual_capital is None:
        return warnings

    divergence = abs(target_capital - actual_capital) / abs(target_capital)
    if divergence > threshold_pct:
        warnings.append(
            f"[NS-2] Arc {arc_no} capital divergence: "
            f"target={genre_ext.get('capital_after')} vs arc_end_state.{actual_key}={_format_eok(actual_capital)} "
            f"(delta={divergence * 100:.0f}%)"
        )

    return warnings


def _build_arc_dependency_advisory(db, arc_no: int) -> str:
    """Arc 의존성 요약을 Director story_context에 넣을 문자열로 반환한다."""
    getter = getattr(db, "get_arc_dependencies", None)
    if not callable(getter):
        return ""

    try:
        current_arc_no = int(arc_no)
    except (TypeError, ValueError):
        return ""

    try:
        deps = getter(current_arc_no)
        if not isinstance(deps, list) or not deps:
            return ""

        dep_lines: list[str] = []
        for dep in deps[:5]:
            if not isinstance(dep, dict):
                continue
            from_arc = dep.get("from_arc_no", "?")
            to_arc = dep.get("to_arc_no", "?")
            dep_type = dep.get("dep_type", "causes")
            desc = str(dep.get("description", "") or "")[:80]
            try:
                if int(to_arc) == current_arc_no:
                    dep_lines.append(f"  Arc {from_arc} → 현재: {dep_type} ({desc})")
                else:
                    dep_lines.append(f"  현재 → Arc {to_arc}: {dep_type} ({desc})")
            except (TypeError, ValueError):
                dep_lines.append(f"  Arc {from_arc} ↔ Arc {to_arc}: {dep_type} ({desc})")

        if not dep_lines:
            return ""
        return f"[DB-3 Arc 의존성] {_DB_ADVISORY_NOTICE}\n" + "\n".join(dep_lines)
    except Exception as dep_err:
        logging.debug("[DB-3] arc_dependencies advisory 실패 (비치명): %s", dep_err)
        return ""


def _build_character_voice_advisory(db) -> str:
    """NPC 말투 프로필 요약을 Director story_context용 문자열로 반환한다."""
    getter = getattr(db, "get_all_character_voices", None)
    if not callable(getter):
        return ""

    try:
        voices = getter()
        if not isinstance(voices, list) or not voices:
            return ""

        voice_lines: list[str] = []
        for voice in voices[:8]:
            if not isinstance(voice, dict):
                continue
            name = str(voice.get("npc_name", "") or "").strip()
            profile = voice.get("profile_data", {})
            if isinstance(profile, str):
                try:
                    profile = json.loads(profile) if profile else {}
                except json.JSONDecodeError:
                    profile = {}
            if not isinstance(profile, dict):
                continue
            tone = str(profile.get("tone", "") or "").strip()
            speech = str(profile.get("speech_pattern", "") or "").strip()
            profile_summary = ", ".join(part for part in (tone, speech) if part)
            if name and profile_summary:
                voice_lines.append(f"  {name}: {profile_summary}"[:80])

        if not voice_lines:
            return ""
        return f"[DB-7 NPC 말투 참고] {_DB_ADVISORY_NOTICE}\n" + "\n".join(voice_lines)
    except Exception as voice_err:
        logging.debug("[DB-7] character_voice advisory 실패 (비치명): %s", voice_err)
        return ""


def _clip_text(value: object, limit: int) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _normalize_checkpoint(value: object, limit: int = 80) -> str:
    if isinstance(value, dict):
        for key in ("checkpoint", "description", "summary", "event", "name"):
            clipped = _clip_text(value.get(key, ""), limit)
            if clipped:
                return clipped
        return _clip_text(json.dumps(value, ensure_ascii=False), limit)
    return _clip_text(value, limit)


def _build_semantic_carryover(state_constraints: dict | None, state_changes: StateChangesDict | None) -> dict:
    payload: dict[str, object] = {}
    sc = state_constraints if isinstance(state_constraints, dict) else {}
    changes = state_changes if isinstance(state_changes, dict) else {}

    relationship_rationale: list[dict[str, str]] = []
    rel_changes = sc.get("relationship_changes") or changes.get("relationship_changes") or []
    if isinstance(rel_changes, list):
        for entry in rel_changes[:5]:
            if not isinstance(entry, dict):
                continue
            trigger = _clip_text(entry.get("trigger", ""), 120)
            justification = _clip_text(entry.get("justification", ""), 120)
            if not (trigger or justification):
                continue
            npc = _clip_text(entry.get("target") or entry.get("npc") or entry.get("name") or "", 40)
            row: dict[str, str] = {}
            if npc:
                row["npc"] = npc
            if trigger:
                row["trigger"] = trigger
            if justification:
                row["justification"] = justification
            if row:
                relationship_rationale.append(row)
    if relationship_rationale:
        payload["relationship_rationale"] = relationship_rationale

    power_changes = sc.get("power_changes", {})
    if isinstance(power_changes, dict):
        growth = _clip_text(power_changes.get("growth_justification", ""), 140)
        if growth:
            payload["growth_justification"] = growth

    foreshadow_anchors: list[str] = []
    foreshadowings = sc.get("foreshadowings", [])
    if isinstance(foreshadowings, list):
        for entry in foreshadowings[:3]:
            if isinstance(entry, dict):
                anchor = _clip_text(entry.get("description", "") or entry.get("summary", ""), 120)
            else:
                anchor = _clip_text(entry, 120)
            if anchor:
                foreshadow_anchors.append(anchor)
    if foreshadow_anchors:
        payload["foreshadow_anchors"] = foreshadow_anchors

    continuity_checkpoints: list[str] = []
    checkpoints = sc.get("continuity_checkpoints", [])
    if isinstance(checkpoints, list):
        for entry in checkpoints[:4]:
            checkpoint = _normalize_checkpoint(entry)
            if checkpoint:
                continuity_checkpoints.append(checkpoint)
    if continuity_checkpoints:
        payload["continuity_checkpoints"] = continuity_checkpoints

    return payload


def _build_rationale_digest_from_carryover(semantic_carryover: dict | None) -> str:
    payload = semantic_carryover if isinstance(semantic_carryover, dict) else {}
    if not payload:
        return ""

    parts: list[str] = []
    for entry in payload.get("relationship_rationale", []) or []:
        if not isinstance(entry, dict):
            continue
        npc = _clip_text(entry.get("npc", ""), 40) or "?"
        cue = _clip_text(entry.get("trigger", ""), 120) or _clip_text(entry.get("justification", ""), 120)
        if cue:
            parts.append(f"관계({npc}): {cue}")

    growth = _clip_text(payload.get("growth_justification", ""), 120)
    if growth:
        parts.append(f"성장근거: {growth}")

    for entry in (payload.get("foreshadow_anchors", []) or [])[:3]:
        anchor = _clip_text(entry, 120)
        if anchor:
            parts.append(f"복선: {anchor}")

    checkpoints = [_clip_text(entry, 60) for entry in (payload.get("continuity_checkpoints", []) or [])[:3]]
    checkpoints = [entry for entry in checkpoints if entry]
    if checkpoints:
        parts.append(f"연속성: {'; '.join(checkpoints)}")

    return "\n".join(parts[:8])


class Stage2Finalizer:
    """Director audit + PASS/REJECT post-processing for Stage 2."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

    def _prepare_stage2_finalize_audit_state(
        self,
        *,
        refined_arc: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        last_refined_context: str,
        bible_root: dict,
        genre: str,
        protagonist_name: str,
        constraint_block: str,
        current_feedback: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        draft_validator_passed: bool,
        consensus_passed: bool,
        attempt: int,
        generation_method: str,
        constraint_db,
    ) -> dict[str, Any]:
        """Director audit 전 snapshot, story_context, audit bundle을 준비한다."""
        cdb_snapshot = None
        if constraint_db and hasattr(constraint_db, "snapshot"):
            try:
                cdb_snapshot = constraint_db.snapshot()
            except Exception:
                pass

        refined_arc, entity_contract_changed = normalize_stage2_arc_entity_contract(
            refined_arc,
            entity_registry_for_director,
        )
        if entity_contract_changed:
            self.ctx.ui.log("      🔧 [Entity Canonicalization] Director 심사 전 명칭 계약 동기화")

        if self.ctx.semantic_plot_guard:
            try:
                tactical_text = refined_arc.get("tactical_doc", "")
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if spg_warnings:
                    spg_text = self.ctx.semantic_plot_guard.format_warnings(spg_warnings)
                    logging.warning(f"⚠️ [V66] {spg_text}")
                    current_feedback = f"{current_feedback}\n{spg_text}" if current_feedback else spg_text
            except (AttributeError, TypeError, RuntimeError) as exc:
                logging.warning(f"⚠️ [V64.P4-fix] 플롯 중복 감지 실패: {exc}")

        expanded_prev_context, story_context = self._build_stage2_director_story_context(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            last_refined_context=last_refined_context,
            bible_root=bible_root,
            genre=genre,
            protagonist_name=protagonist_name,
            constraint_block=constraint_block,
        )

        audit, director_duration_ms, decision, score = self._audit_stage2_director(
            refined_arc=refined_arc,
            expanded_prev_context=expanded_prev_context,
            enriched_block=enriched_block,
            protagonist_name=protagonist_name,
            suspected_duplicates=suspected_duplicates,
            entity_registry_for_director=entity_registry_for_director,
            story_context=story_context,
            global_arc_no=global_arc_no,
            draft_validator_passed=draft_validator_passed,
            consensus_passed=consensus_passed,
        )

        tactical_doc = refined_arc.get("tactical_doc", "")
        tactical_doc_len = len(str(tactical_doc)) if isinstance(tactical_doc, dict) else len(tactical_doc or "")

        from modules.validation.threshold_helper import _threshold

        quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        self._log_stage2_session_decision(
            audit=audit,
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            score=score,
        )
        return {
            "cdb_snapshot": cdb_snapshot,
            "current_feedback": current_feedback,
            "expanded_prev_context": expanded_prev_context,
            "story_context": story_context,
            "audit": audit,
            "director_duration_ms": director_duration_ms,
            "decision": decision,
            "score": score,
            "tactical_doc_len": tactical_doc_len,
            "quality_gate_score": quality_gate_score,
        }

    async def _handle_stage2_finalize_pass_branch(
        self,
        *,
        refined_arc: dict,
        audit: dict,
        decision: str,
        score: int,
        tactical_doc_len: int,
        quality_gate_score: int,
        st_snapshot,
        generation_method: str,
        cdb_snapshot,
        constraint_db,
        global_arc_no: int,
        attempt: int,
        is_patch: bool,
        prev_score: float,
        patch_fallback: bool,
        arc_drive: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        current_feedback: str,
        constraint_block: str,
        genre: str,
        last_refined_context: str,
        current_ep_start: int,
        director_feedback_for_fourphase: str,
        director_duration_ms: int | None,
    ) -> dict:
        """PASS/PASS_WITH_FIX 공통 finalize tail을 처리한다."""
        quality_gate_result = self._maybe_reject_stage2_pass_for_quality_gate(
            refined_arc=refined_arc,
            audit=audit,
            decision=decision,
            score=score,
            tactical_doc_len=tactical_doc_len,
            quality_gate_score=quality_gate_score,
            st_snapshot=st_snapshot,
            generation_method=generation_method,
            cdb_snapshot=cdb_snapshot,
            constraint_db=constraint_db,
            global_arc_no=global_arc_no,
            attempt=attempt,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
        )
        if quality_gate_result:
            return quality_gate_result

        prepared_result: Stage2PassPreparationResult = self._prepare_stage2_pass_arc_for_persistence(
            refined_arc=refined_arc,
            arc_drive=arc_drive,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            current_feedback=current_feedback,
            generation_method=generation_method,
            st_snapshot=st_snapshot,
            cdb_snapshot=cdb_snapshot,
            constraint_db=constraint_db,
            constraint_block=constraint_block,
            genre=genre,
        )
        if prepared_result.get("action") == "retry":
            return prepared_result

        return await self._finalize_stage2_pass_persistence_and_tail(
            refined_arc=prepared_result["refined_arc"],
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            current_feedback=current_feedback,
            st_snapshot=st_snapshot,
            cdb_snapshot=cdb_snapshot,
            constraint_db=constraint_db,
            last_refined_context=last_refined_context,
            current_ep_start=current_ep_start,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            attempt=attempt,
            generation_method=generation_method,
            audit=audit,
            director_duration_ms=director_duration_ms,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
        )

    async def run_finalize(
        self,
        *,
        refined_arc: dict,
        enriched_block: dict,
        arc_drive: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_ep_start: int,
        current_feedback: str,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        constraint_block: str,
        draft_validator_passed: bool,
        consensus_passed: bool,
        attempt: int,
        generation_method: str,
        st_snapshot,
        director_feedback_for_fourphase: str,
        last_refined_context: str,
        bible_root: dict,
        genre: str,
        constraint_db,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> dict:
        """[4-R3-e] Director audit and post-audit finalize.

        Handles SemanticPlotGuard, Director context/audit,
        PASS finalization (DB save, metrics, volume summary),
        and REJECT handling (rollback, feedback).

        Returns dict with action='break'|'retry'|'next'.
        """
        audit_state = self._prepare_stage2_finalize_audit_state(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            last_refined_context=last_refined_context,
            bible_root=bible_root,
            genre=genre,
            protagonist_name=protagonist_name,
            constraint_block=constraint_block,
            current_feedback=current_feedback,
            suspected_duplicates=suspected_duplicates,
            entity_registry_for_director=entity_registry_for_director,
            draft_validator_passed=draft_validator_passed,
            consensus_passed=consensus_passed,
            attempt=attempt,
            generation_method=generation_method,
            constraint_db=constraint_db,
        )
        current_feedback = audit_state["current_feedback"]
        audit = audit_state["audit"]
        _d_decision = audit_state["decision"]
        _score = audit_state["score"]
        _expanded_prev_context = audit_state["expanded_prev_context"]
        _story_context = audit_state["story_context"]
        _director_duration_ms = audit_state["director_duration_ms"]
        _cdb_snapshot = audit_state["cdb_snapshot"]
        _td_len = audit_state["tactical_doc_len"]
        _quality_gate_score = audit_state["quality_gate_score"]

        # [TF-32-VERIFY] PASS_WITH_FIX → patch + Director 재심사 반복 (최대 3회)
        if _d_decision == "PASS_WITH_FIX":
            _pwf_result: Stage2PassWithFixLoopResult = self._run_stage2_pass_with_fix_loop(
                refined_arc=refined_arc,
                audit=audit,
                expanded_prev_context=_expanded_prev_context,
                enriched_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry_for_director=entity_registry_for_director,
                story_context=_story_context,
                global_arc_no=global_arc_no,
                score=_score,
            )
            refined_arc = _pwf_result["refined_arc"]
            audit = _pwf_result["audit"]
            _d_decision = _pwf_result["decision"]
            _score = _pwf_result["score"]

        if _d_decision in ("PASS", "PASS_WITH_FIX"):  # [TF-R4-S2-01] [TF-32-S2] PASS/PASS_WITH_FIX 수용
            return await self._handle_stage2_finalize_pass_branch(
                refined_arc=refined_arc,
                audit=audit,
                decision=_d_decision,
                score=_score,
                tactical_doc_len=_td_len,
                quality_gate_score=_quality_gate_score,
                st_snapshot=st_snapshot,
                generation_method=generation_method,
                cdb_snapshot=_cdb_snapshot,
                constraint_db=constraint_db,
                global_arc_no=global_arc_no,
                attempt=attempt,
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
                arc_drive=arc_drive,
                enriched_block=enriched_block,
                all_refined_arcs=all_refined_arcs,
                current_feedback=current_feedback,
                constraint_block=constraint_block,
                genre=genre,
                last_refined_context=last_refined_context,
                current_ep_start=current_ep_start,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                director_duration_ms=_director_duration_ms,
            )
        return self._handle_stage2_reject_path(
            refined_arc=refined_arc,
            audit=audit,
            attempt=attempt,
            generation_method=generation_method,
            st_snapshot=st_snapshot,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            last_refined_context=last_refined_context,
            current_ep_start=current_ep_start,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            global_arc_no=global_arc_no,
            current_feedback=current_feedback,
            director_duration_ms=_director_duration_ms,
        )

    def _restore_stage2_state_snapshots(
        self,
        *,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
        success_log: str | None = None,
        failure_log: str | None = None,
    ) -> None:
        if st_snapshot:
            try:
                tracker = self.ctx.state_tracker
                for key, value in st_snapshot.items():
                    if hasattr(tracker, key):
                        setattr(tracker, key, value)
                if success_log:
                    logging.info(success_log)
            except Exception as rollback_err:
                if failure_log:
                    logging.warning("%s: %s", failure_log, rollback_err)
        if cdb_snapshot and constraint_db and hasattr(constraint_db, "restore"):
            constraint_db.restore(cdb_snapshot)

    def _build_stage2_pass_retry_result(
        self,
        *,
        current_feedback: str,
        st_snapshot,
        generation_method: str,
        cdb_snapshot,
        constraint_db,
    ) -> Stage2PassPreparationResult:
        if st_snapshot and generation_method.startswith("four_phase"):
            self._restore_stage2_state_snapshots(
                st_snapshot=st_snapshot,
                cdb_snapshot=cdb_snapshot,
                constraint_db=constraint_db,
            )
        return {"action": "retry", "current_feedback": current_feedback}

    def _prepare_stage2_pass_arc_for_persistence(
        self,
        *,
        refined_arc: dict,
        arc_drive: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_feedback: str,
        generation_method: str,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
        constraint_block: str,
        genre: str = "",
    ) -> Stage2PassPreparationResult:
        refined_arc["arc_drive"] = arc_drive if arc_drive else {}
        refined_arc["joint_docs"] = merge_stage2_authoritative_packet(
            refined_arc.get("joint_docs"),
            enriched_block.get("joint_docs"),
        )
        refined_arc["status_shadow"] = merge_stage2_authoritative_packet(
            refined_arc.get("status_shadow"),
            enriched_block.get("status_shadow"),
        )
        removed_state_noise = _strip_non_wuxia_state_noise_for_persistence(refined_arc, genre=genre)
        _log_non_wuxia_state_cleanup(
            self.ctx,
            global_arc_no=global_arc_no,
            removed_sections=removed_state_noise,
            phase="pre-persistence shell",
        )
        repair_result = self._repair_stage2_pass_arc_structure(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            current_feedback=current_feedback,
            generation_method=generation_method,
            st_snapshot=st_snapshot,
            cdb_snapshot=cdb_snapshot,
            constraint_db=constraint_db,
        )
        if repair_result["action"] != "continue":
            return repair_result
        refined_arc = repair_result["refined_arc"]
        return self._finalize_stage2_pass_arc_preparation(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            constraint_block=constraint_block,
            enriched_block=enriched_block,
            genre=genre,
        )

    def _repair_stage2_pass_arc_structure(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_feedback: str,
        generation_method: str,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
    ) -> Stage2PassPreparationResult:
        from modules.core.constants import RecoveryLimits
        if callable(getattr(self.ctx, "validate_arc_data_fields", None)):
            repaired_arc = self.ctx.validate_arc_data_fields(refined_arc, global_arc_no)
            if repaired_arc is None:
                current_feedback = "Arc 데이터 기본 구조를 복구하지 못했습니다. 완전한 JSON 구조로 다시 설계하라."
                return self._build_stage2_pass_retry_result(
                    current_feedback=current_feedback,
                    st_snapshot=st_snapshot,
                    generation_method=generation_method,
                    cdb_snapshot=cdb_snapshot,
                    constraint_db=constraint_db,
                )
            refined_arc = repaired_arc

        critical_missing = []
        if not refined_arc.get("hybrid_composition"):
            self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] 패턴 구성(hybrid_composition) 누락 - 기본값 주입")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("field_repair", "hybrid_composition default injected", {"arc_no": global_arc_no})
            refined_arc["hybrid_composition"] = {
                "primary": "standard_progression",
                "secondary": [],
                "mixing_logic": "기본 전개",
            }
            critical_missing.append("hybrid_composition")

        if not refined_arc.get("joint_docs"):
            self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] joint_docs 누락 - 기본값 주입")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("field_repair", "joint_docs default injected", {"arc_no": global_arc_no})
            refined_arc["joint_docs"] = {
                "final_location": "위치 미정",
                "physical_inventory": ["물품 미정"],
                "world_joint": "변화 없음",
            }
            critical_missing.append("joint_docs")

        curr_joint = refined_arc.get("joint_docs", {})
        curr_inventory = _coerce_inventory_items(curr_joint.get("physical_inventory", []))
        if all_refined_arcs:
            prev_joint = all_refined_arcs[-1].get("joint_docs", {})
            curr_status = refined_arc.get("status_shadow", {}) or {}
            state_constraints = refined_arc.get("state_constraints", {}) or {}
            inherited = _compute_inventory_carryover(
                prev_joint.get("physical_inventory", []),
                curr_status.get("item_consumption", []),
                state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", []),
            )
            if curr_inventory != inherited:
                refined_arc["joint_docs"]["physical_inventory"] = inherited
                self.ctx.ui.log(
                    f"      🔄 [V49.6] physical_inventory deterministic carryover 적용: "
                    f"{inherited[:3]}{'...' if len(inherited) > 3 else ''}"
                )
        elif curr_inventory != curr_joint.get("physical_inventory", []):
            refined_arc["joint_docs"]["physical_inventory"] = curr_inventory

        canonical_end_inventory, joint_inventory_changed, end_inventory_changed = _sync_stage2_end_state_inventory_contract(
            refined_arc,
            all_refined_arcs[-1] if all_refined_arcs else None,
        )
        if joint_inventory_changed and not all_refined_arcs:
            self.ctx.ui.log(
                f"      🔧 [End Inventory Sync] Arc {global_arc_no} joint_docs 종료 소지품 → "
                f"state_constraints 기준으로 동기화 ({len(canonical_end_inventory)}개 아이템)"
            )
        if end_inventory_changed:
            self.ctx.ui.log(f"      🔧 [End Equipment Sync] Arc {global_arc_no} 종료 소지품 상태 동기화")

        canonical_end_location, joint_location_changed, end_location_changed = _sync_stage2_end_location_contract(
            refined_arc
        )
        if joint_location_changed or end_location_changed:
            self.ctx.ui.log(
                f"      🔧 [End Location Sync] Arc {global_arc_no} 종료 위치 → {canonical_end_location or '위치 미정'}"
            )

        if not refined_arc.get("status_shadow"):
            self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] status_shadow 누락 - 기본값 주입")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("field_repair", "status_shadow default injected", {"arc_no": global_arc_no})
            refined_arc["status_shadow"] = {
                "internal_energy_loss": "0%",
                "expected_injuries": "없음",
                "item_consumption": [],
            }
            critical_missing.append("status_shadow")

        if len(critical_missing) >= RecoveryLimits.CRITICAL_MISSING_THRESHOLD:
            self.ctx.ui.log(f"🚨 [Arc {global_arc_no}] 핵심 데이터 과다 누락({len(critical_missing)}개)")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "integrity_fail",
                    "critical fields missing beyond repair threshold",
                    {"arc_no": global_arc_no, "missing": critical_missing},
                )
            current_feedback = f"필수 키 누락: {', '.join(critical_missing)}. 완전한 JSON 구조로 재설계하라."
            if st_snapshot and generation_method.startswith("four_phase") and self.ctx.state_tracker:
                for key, value in st_snapshot.items():
                    if hasattr(self.ctx.state_tracker, key):
                        setattr(self.ctx.state_tracker, key, value)
                if cdb_snapshot and constraint_db and hasattr(constraint_db, "restore"):
                    constraint_db.restore(cdb_snapshot)
            return {"action": "retry", "current_feedback": current_feedback}

        if callable(getattr(self.ctx, "validate_arc_integrity", None)) and not self.ctx.validate_arc_integrity(
            refined_arc
        ):
            current_feedback = "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
            if st_snapshot and generation_method.startswith("four_phase") and self.ctx.state_tracker:
                for key, value in st_snapshot.items():
                    if hasattr(self.ctx.state_tracker, key):
                        setattr(self.ctx.state_tracker, key, value)
                if cdb_snapshot and constraint_db and hasattr(constraint_db, "restore"):
                    constraint_db.restore(cdb_snapshot)
            return {"action": "retry", "current_feedback": current_feedback}
        return {"action": "continue", "refined_arc": refined_arc}

    def _finalize_stage2_pass_arc_preparation(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        constraint_block: str,
        enriched_block: dict,
        genre: str = "",
    ) -> Stage2PassPreparationResult:

        if constraint_block:
            constraint_lines = constraint_block.strip().split("\n")
            must_not = [line.strip() for line in constraint_lines if "금지" in line or "MUST NOT" in line or "절대" in line]
            refined_arc["constraint_summary"] = "\n".join(must_not[:10]) if must_not else ""

        rationale_parts: list[str] = []
        rationale_sc = refined_arc.get("state_constraints", {})
        rationale_rels = (
            rationale_sc.get("relationship_changes")
            or refined_arc.get("state_changes", {}).get("relationship_changes")
            or []
        )
        for relation_change in rationale_rels[:5]:
            if isinstance(relation_change, dict):
                trigger = relation_change.get("trigger", "")
                justification = relation_change.get("justification", "")
                if trigger or justification:
                    npc = relation_change.get("target") or relation_change.get("npc") or "?"
                    rationale_parts.append(f"관계({npc}): {trigger or justification}")
        rationale_pc = rationale_sc.get("power_changes", {})
        if isinstance(rationale_pc, dict) and rationale_pc.get("growth_justification"):
            rationale_parts.append(f"성장근거: {rationale_pc['growth_justification']}")
        rationale_fs = rationale_sc.get("foreshadowings", [])
        if isinstance(rationale_fs, list):
            for foreshadow in rationale_fs:
                if isinstance(foreshadow, dict) and foreshadow.get("description"):
                    rationale_parts.append(f"복선: {foreshadow['description']}")
        rationale_cc = rationale_sc.get("continuity_checkpoints", [])
        if isinstance(rationale_cc, list) and rationale_cc:
            rationale_parts.append(f"연속성: {'; '.join(str(item) for item in rationale_cc)}")
        refined_arc["rationale_digest"] = "\n".join(rationale_parts[:8]) if rationale_parts else ""

        semantic_carryover = _build_semantic_carryover(
            refined_arc.get("state_constraints"),
            refined_arc.get("state_changes"),
        )
        refined_arc["semantic_carryover"] = semantic_carryover
        refined_arc["rationale_digest"] = _build_rationale_digest_from_carryover(semantic_carryover)

        if all_refined_arcs:
            prev_arc = all_refined_arcs[-1]
            prev_constraints = prev_arc.get("state_constraints", {}) or {}
            correct_equip = _compute_inventory_carryover(
                prev_arc.get("joint_docs", {}).get("physical_inventory", []),
                prev_arc.get("status_shadow", {}).get("item_consumption", []),
                prev_constraints.get("protagonist_items") or prev_constraints.get("items_acquired", []),
            )

            curr_sc = refined_arc.get("state_constraints", {})
            curr_start = curr_sc.get("arc_start_state", {})
            old_equip = _coerce_inventory_items(curr_start.get("equipment", []))
            if old_equip != correct_equip:
                curr_start["equipment"] = correct_equip
                curr_sc["arc_start_state"] = curr_start
                refined_arc["state_constraints"] = curr_sc
                self.ctx.ui.log(
                    f"      🔧 [Equipment Sync] Arc {global_arc_no} 시작 소지품 → "
                    f"이전 Arc 종료 소지품으로 동기화 ({len(correct_equip)}개 아이템)"
                )

            synced_tactical_doc = _sync_first_episode_start_state_line(
                refined_arc.get("tactical_doc", ""),
                curr_start,
            )
            if synced_tactical_doc != refined_arc.get("tactical_doc", ""):
                refined_arc["tactical_doc"] = synced_tactical_doc
                self.ctx.ui.log(f"      🔧 [State Sync] Arc {global_arc_no} 첫 화 시작 상태 텍스트 동기화")

        if isinstance(refined_arc, dict) and "arc_no" not in refined_arc:
            refined_arc["arc_no"] = global_arc_no
        refined_arc = validate_arc(refined_arc)
        removed_state_noise = _strip_non_wuxia_state_noise_for_persistence(refined_arc, genre=genre)
        _log_non_wuxia_state_cleanup(
            self.ctx,
            global_arc_no=global_arc_no,
            removed_sections=removed_state_noise,
            phase="post-validate shell",
        )

        ns2_warnings = _check_block_worldstate_alignment(enriched_block, refined_arc, global_arc_no)
        if ns2_warnings:
            for warn in ns2_warnings:
                logging.warning(warn)

        return {"action": "continue", "refined_arc": refined_arc}

    async def _persist_stage2_pass_arc_commit(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_feedback: str,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
    ) -> Stage2PassFinalizeTailResult | None:
        all_refined_arcs.append(refined_arc)
        try:
            self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
            if callable(getattr(self.ctx, "safe_commit_async", None)):
                commit_ok = await self.ctx.safe_commit_async()
                if not commit_ok:
                    raise RuntimeError("safe_commit_async returned False")
        except (OSError, RuntimeError) as commit_err:
            try:
                conn = self.ctx.current_project.db.conn
                if conn.in_transaction:
                    conn.rollback()
                    logging.info("[TF-C09] DB rollback 완료 (Arc %d)", global_arc_no)
            except Exception as rollback_err:
                logging.warning("[TF-C09] DB rollback 실패: %s", rollback_err)
            self.ctx.ui.log(f"[DB] Arc {global_arc_no} 저장 실패: {commit_err}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "db_commit_error",
                    "arc save failed in async",
                    {"arc_no": global_arc_no, "error": str(commit_err)},
                )
            all_refined_arcs.pop()
            if st_snapshot:
                self._restore_stage2_state_snapshots(
                    st_snapshot=st_snapshot,
                    cdb_snapshot=cdb_snapshot,
                    constraint_db=constraint_db,
                    success_log="[V70] DB 롤백 StateTracker 복원 완료",
                    failure_log="[V70] DB 롤백 StateTracker 복원 실패",
                )
            return {"action": "retry", "current_feedback": current_feedback}
        return None
    def _upsert_stage2_pass_arc_dependencies(
        self,
        *,
        refined_arc: dict,
        global_arc_no: int,
    ) -> None:
        arc_no = global_arc_no
        if arc_no <= 1 or not getattr(self.ctx, "current_project", None):
            return
        try:
            desc = refined_arc.get("theme", "") or refined_arc.get("title", "")
            self.ctx.current_project.db.upsert_arc_dependency(
                from_arc=arc_no - 1,
                to_arc=arc_no,
                dep_type="causes",
                description=str(desc)[:200],
            )
            for prereq in refined_arc.get("prerequisite_arcs") or []:
                if isinstance(prereq, int) and prereq != arc_no:
                    self.ctx.current_project.db.upsert_arc_dependency(prereq, arc_no, "requires", "")
        except (AttributeError, TypeError) as dep_err:
            logging.debug("[Stage2] arc_dependency 저장 실패 (비치명): %s", dep_err)

    def _update_stage2_pass_constraint_db(self, *, refined_arc: dict, constraint_db) -> None:
        try:
            constraint_db.update_arc_state(refined_arc)
            self.ctx.ui.log(f"      [V49.4] ConstraintDB 업데이트 완료 (총 {len(constraint_db.arc_states)}개 Arc)")
        except (AttributeError, TypeError, RuntimeError) as cdb_err:
            logging.warning("[B4-P1-1] constraint_db.update_arc_state 실패 (best-effort): %s", cdb_err)
    def _maybe_generate_stage2_volume_summaries(self, *, global_arc_no: int) -> None:
        arcs_per_volume = max(1, int(VolumeSettings.ARCS_PER_VOLUME))
        if global_arc_no <= 0 or global_arc_no % arcs_per_volume != 0:
            return
        try:
            volume_no = global_arc_no // arcs_per_volume
            arc_summaries_for_volume = []
            for arc_idx in range(global_arc_no - (arcs_per_volume - 1), global_arc_no + 1):
                arc_summary = self.ctx.current_project.load_v20_anchor(f"arc_summary_{arc_idx}")
                if not arc_summary:
                    continue
                if isinstance(arc_summary, dict):
                    arc_summary_text = arc_summary.get("summary", "") or arc_summary.get("text", "")
                    if not arc_summary_text:
                        summary_parts = []
                        npc_status = arc_summary.get("npc_status")
                        if isinstance(npc_status, dict) and npc_status:
                            summary_parts.append(
                                "NPC: "
                                + ", ".join(
                                    f"{name}({value.get('status', '')})"
                                    for name, value in npc_status.items()
                                )
                            )
                        if arc_summary.get("world_changes"):
                            summary_parts.append(
                                "세계 변화: " + "; ".join(str(item) for item in arc_summary["world_changes"][:5])
                            )
                        if arc_summary.get("resolved_plots"):
                            summary_parts.append(
                                "해결 플롯: " + "; ".join(str(item) for item in arc_summary["resolved_plots"][:5])
                            )
                        if arc_summary.get("active_plots"):
                            summary_parts.append(
                                "진행 플롯: " + "; ".join(str(item) for item in arc_summary["active_plots"][:5])
                            )
                        if arc_summary.get("destroyed_entities"):
                            summary_parts.append(
                                "파괴 대상: " + "; ".join(str(item) for item in arc_summary["destroyed_entities"][:3])
                            )
                        arc_summary_text = " | ".join(summary_parts) if summary_parts else str(arc_summary)
                else:
                    arc_summary_text = str(arc_summary)
                if arc_summary_text:
                    arc_summaries_for_volume.append(f"Arc {arc_idx}: {arc_summary_text}")

            if not arc_summaries_for_volume:
                return

            volume_prompt = (
                f"아래 {arcs_per_volume}개 아크 요약을 하나의 볼륨 요약으로 압축해주세요.\n"
                "핵심 사건, 주요 인물 변화, 관계와 상태 변화를 중심으로 정리해주세요.\n"
                "반드시 아래 3개 섹션으로만 정리해주세요.\n"
                "[인물 아크]\n[핵심 갈등]\n[미해결 복선]\n"
                "전체 2000자 이내로 작성해주세요.\n\n"
                + "\n".join(arc_summaries_for_volume)
                + f"\n\n볼륨 {volume_no} 요약:"
            )
            volume_result = self.ctx.agents["director"].ask(volume_prompt, temperature=0.2)
            if not (volume_result and isinstance(volume_result, str) and len(volume_result) > 20):
                logging.warning("[V68] 볼륨 요약 LLM 응답 불충분으로 건너뜀")
                return

            volume_result = _trim_hierarchical_summary(volume_result, 2000)
            self.ctx.current_project.save_v20_anchor(f"volume_summary_{volume_no}", volume_result)
            logging.info("[V68] 볼륨 %s 요약 저장 완료 (%s자)", volume_no, len(volume_result))

            try:
                existing_series = self.ctx.current_project.load_v20_anchor("series_summary") or ""
                if isinstance(existing_series, dict):
                    existing_series = existing_series.get("summary", "") or str(existing_series)
                series_prompt = (
                    "아래는 기존 시리즈 요약과 새 볼륨 요약입니다.\n"
                    "이를 통합하여 전체 시리즈 요약을 갱신해주세요.\n"
                    "반드시 아래 3개 섹션으로만 정리해주세요.\n"
                    "[인물 아크]\n[핵심 갈등]\n[미해결 복선]\n"
                    "핵심 사건, 주요 인물 변화, 관계와 상태 변화를 중심으로 전체 5000자 이내로 작성해주세요.\n\n"
                    f"기존 시리즈 요약:\n{existing_series or '(아직 없음)'}\n\n"
                    f"새 볼륨 {volume_no} 요약:\n{volume_result}\n\n"
                    "갱신된 시리즈 요약:"
                )
                series_result = self.ctx.agents["director"].ask(series_prompt, temperature=0.2)
                if series_result and isinstance(series_result, str) and len(series_result) > 20:
                    series_result = _trim_hierarchical_summary(series_result, 5000)
                    self.ctx.current_project.save_v20_anchor("series_summary", series_result)
                    logging.info("[V68] 시리즈 요약 갱신 완료 (%s자)", len(series_result))
            except Exception as series_err:
                logging.warning("[V68] 시리즈 요약 갱신 실패 (best-effort: %s)", series_err)
        except Exception as volume_err:
            logging.warning("[V68] 볼륨 요약 생성 실패 (best-effort: %s)", volume_err)
    def _advance_stage2_pass_persistence_state(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        last_refined_context: str,
    ) -> dict[str, Any]:
        self._upsert_stage2_pass_arc_dependencies(
            refined_arc=refined_arc,
            global_arc_no=global_arc_no,
        )
        if callable(getattr(self.ctx, "generate_arc_context_v60", None)):
            last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, global_arc_no + 1)
        return {
            "last_refined_context": last_refined_context,
            "current_ep_start": refined_arc["ep_end"] + 1,
        }

    def _persist_stage2_pass_cost_record(self, *, global_arc_no: int) -> None:
        try:
            collector = get_metrics_collector()
            if collector and self.ctx.current_project and hasattr(self.ctx.current_project, "db"):
                scope = collector.snapshot_and_reset_scope()
                if (
                    scope.get("total_calls", 0) > 0
                    or scope.get("total_tokens", 0) > 0
                    or scope.get("total_cost_usd", 0.0) > 0
                ):
                    self.ctx.current_project.db.save_cost_record(
                        session_id=collector.session_id,
                        scope_type="arc",
                        scope_id=global_arc_no,
                        total_calls=scope.get("total_calls", 0),
                        total_tokens=scope.get("total_tokens", 0),
                        total_cost_usd=scope.get("total_cost_usd", 0.0),
                        model_breakdown=scope.get("model_breakdown", "{}"),
                    )
        except (OSError, RuntimeError, TypeError) as cost_err:
            logging.warning("[Phase 6] Arc 비용 기록 실패 (비차단): %s", cost_err)

    async def _finalize_stage2_pass_persistence_and_tail(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_feedback: str,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
        last_refined_context: str,
        current_ep_start: int,
        director_feedback_for_fourphase: str,
        attempt: int,
        generation_method: str,
        audit: dict,
        director_duration_ms: int | None,
        is_patch: bool,
        prev_score: float,
        patch_fallback: bool,
    ) -> Stage2PassFinalizeTailResult:
        commit_result = await self._persist_stage2_pass_arc_commit(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            current_feedback=current_feedback,
            st_snapshot=st_snapshot,
            cdb_snapshot=cdb_snapshot,
            constraint_db=constraint_db,
        )
        if commit_result is not None:
            return commit_result

        st_snapshot = None
        cdb_snapshot = None
        self.ctx.cumulative_state_cache = None
        self.ctx.cumulative_state_cache_key = None
        self._update_stage2_pass_constraint_db(refined_arc=refined_arc, constraint_db=constraint_db)
        post_commit_state = self._advance_stage2_pass_persistence_state(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            last_refined_context=last_refined_context,
        )
        last_refined_context = post_commit_state["last_refined_context"]
        current_ep_start = int(post_commit_state["current_ep_start"])
        self._record_s2_pass_metrics(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=(
                refined_arc.get("_ensemble_meta", {}).get("best_strategy")
                or refined_arc.get("_strategy", "")
                or generation_method
            )
            if isinstance(refined_arc, dict)
            else generation_method,
            audit=audit,
            duration_ms=director_duration_ms,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            artifact_payload=refined_arc if isinstance(refined_arc, dict) else None,
        )
        self._persist_stage2_pass_cost_record(global_arc_no=global_arc_no)
        self._maybe_generate_stage2_volume_summaries(global_arc_no=global_arc_no)
        return {
            "action": "break",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
        }

    async def _legacy_stage2_pass_persistence_and_tail_body(
        self,
        *,
        refined_arc: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_feedback: str,
        st_snapshot,
        cdb_snapshot,
        constraint_db,
        last_refined_context: str,
        current_ep_start: int,
        director_feedback_for_fourphase: str,
        attempt: int,
        generation_method: str,
        audit: dict,
        director_duration_ms: int | None,
        is_patch: bool,
        prev_score: float,
        patch_fallback: bool,
    ) -> Stage2PassFinalizeTailResult:
        self._update_stage2_pass_constraint_db(refined_arc=refined_arc, constraint_db=constraint_db)
        post_commit_state = self._advance_stage2_pass_persistence_state(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            last_refined_context=last_refined_context,
        )
        last_refined_context = post_commit_state["last_refined_context"]
        current_ep_start = int(post_commit_state["current_ep_start"])
        self._record_s2_pass_metrics(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=(
                refined_arc.get("_ensemble_meta", {}).get("best_strategy")
                or refined_arc.get("_strategy", "")
                or generation_method
            )
            if isinstance(refined_arc, dict)
            else generation_method,
            audit=audit,
            duration_ms=director_duration_ms,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            artifact_payload=refined_arc if isinstance(refined_arc, dict) else None,
        )
        self._persist_stage2_pass_cost_record(global_arc_no=global_arc_no)
        self._maybe_generate_stage2_volume_summaries(global_arc_no=global_arc_no)
        return {
            "action": "break",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
        }

    def _maybe_reject_stage2_pass_for_quality_gate(
        self,
        *,
        refined_arc: dict,
        audit: dict,
        decision: str,
        score: int,
        tactical_doc_len: int,
        quality_gate_score: int,
        st_snapshot,
        generation_method: str,
        cdb_snapshot,
        constraint_db,
        global_arc_no: int,
        attempt: int,
        is_patch: bool,
        prev_score: float,
        patch_fallback: bool,
    ) -> dict | None:
        if decision not in ("PASS", "PASS_WITH_FIX") or tactical_doc_len < 1500 or score >= quality_gate_score:
            return None

        self.ctx.ui.log(f"      ⚠️ [QualityGate] {decision} 판정이나 score={score} < {quality_gate_score} → REJECT 전환")
        audit["decision"] = "REJECT"
        audit["reason"] = (audit.get("reason") or "") + (
            f"\n[Quality Gate] score {score}점으로 {quality_gate_score}점 미달."
        )
        audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "품질 개선 후 재제출"
        director_feedback_for_fourphase = (
            f"[QualityGate REJECT] score {score}점 < {quality_gate_score}점.\n"
            f"{audit.get('reason', '')}\n"
            f"[수정 지시] {audit.get('re_slice_instruction', '품질 개선 후 재제출')}"
        )

        if st_snapshot and generation_method.startswith("four_phase"):
            tracker = self.ctx.state_tracker
            if tracker:
                for key, value in st_snapshot.items():
                    if hasattr(tracker, key):
                        setattr(tracker, key, value)
            if cdb_snapshot and constraint_db and hasattr(constraint_db, "restore"):
                constraint_db.restore(cdb_snapshot)

        self._record_s2_reject_metrics(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=(
                refined_arc.get("_ensemble_meta", {}).get("best_strategy")
                or refined_arc.get("_strategy", "")
                or generation_method
            )
            if isinstance(refined_arc, dict)
            else generation_method,
            audit=audit,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            artifact_payload=refined_arc if isinstance(refined_arc, dict) else None,
        )
        return {
            "action": "retry",
            "current_feedback": audit["reason"],
            "score": score,
            "rejected_arc": refined_arc,
            "score_breakdown": {},
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "fix_scope": audit.get("fix_scope", ""),
        }

    def _handle_stage2_reject_path(
        self,
        *,
        refined_arc: dict,
        audit: dict,
        attempt: int,
        generation_method: str,
        st_snapshot,
        director_feedback_for_fourphase: str,
        last_refined_context: str,
        current_ep_start: int,
        is_patch: bool,
        prev_score: float,
        patch_fallback: bool,
        global_arc_no: int,
        current_feedback: str,
        director_duration_ms: int | None,
    ) -> dict:
        rejected_arc = refined_arc
        base_feedback = audit.get("re_slice_instruction") or "밀도 보강 필요"
        reject_reason = audit.get("reason") or "사유 미상"
        score_breakdown = {}
        self_consistency = audit.get("self_consistency", {})
        if isinstance(self_consistency, dict):
            for key in ("votes", "pass_votes", "median_score"):
                value = self_consistency.get(key)
                if isinstance(value, int | float):
                    score_breakdown[key] = value

        if callable(getattr(self.ctx, "get_adaptive_feedback_intensity", None)):
            adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
            intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
        else:
            intensity_guide = ""

        self.ctx.ui.log(f"      🎬 [Director REJECT] {reject_reason}")
        self.ctx.ui.log(f"      📋 피드백: {base_feedback}")

        if st_snapshot and generation_method.startswith("four_phase"):
            try:
                tracker = self.ctx.state_tracker
                for key, value in st_snapshot.items():
                    if hasattr(tracker, key):
                        setattr(tracker, key, value)
                logging.info("🔄 [V70] StateTracker 롤백 완료 (Director REJECT)")
            except Exception as rollback_err:
                logging.warning(f"⚠️ [V70] StateTracker 롤백 실패 (비차단): {rollback_err}")
            st_snapshot = None

        director_feedback_for_fourphase = f"""[Director REJECT 사유]
{reject_reason}

[수정 지시]
{base_feedback}

[재시도 가이드]
{intensity_guide}
"""
        rejected_arc = refined_arc if isinstance(refined_arc, dict) else None
        self.ctx.ui.log(f"      🔄 [V60.77] Director 피드백 → FourPhase 대면 {min(attempt + 2, 5)}/5")

        self._record_s2_reject_metrics(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=(
                rejected_arc.get("_ensemble_meta", {}).get("best_strategy")
                or rejected_arc.get("_strategy", "")
                or generation_method
            )
            if isinstance(rejected_arc, dict)
            else generation_method,
            audit=audit,
            duration_ms=director_duration_ms,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            artifact_payload=rejected_arc,
        )

        return {
            "action": "retry",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
            "score": audit.get("score", 0),
            "rejected_arc": rejected_arc,
            "score_breakdown": score_breakdown,
            "selection_reason": reject_reason,
            "validation_warnings": [reject_reason, base_feedback],
            "fix_scope": audit.get("fix_scope", ""),
            "fix_scope_reasoning": audit.get("fix_scope_reasoning", ""),
        }

    def _build_stage2_director_story_context(
        self,
        *,
        refined_arc: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        last_refined_context: str,
        bible_root: dict,
        genre: str,
        protagonist_name: str,
        constraint_block: str,
    ) -> tuple[str, str]:
        from modules.core.constants import ContextLimits

        expanded_prev_context = last_refined_context
        if all_refined_arcs:
            prev_arc_docs = []
            prev_start = max(0, len(all_refined_arcs) - 30)
            for prev_arc_idx in range(prev_start, len(all_refined_arcs)):
                prev_arc = all_refined_arcs[prev_arc_idx]
                prev_arc_no = prev_arc.get("arc_no", prev_arc_idx + 1)
                prev_tactical = prev_arc.get("tactical_doc", "")
                if isinstance(prev_tactical, dict):
                    prev_tactical = json.dumps(prev_tactical, ensure_ascii=False)
                if prev_tactical:
                    prev_ep_start = prev_arc.get("ep_start", "?")
                    prev_ep_end = prev_arc.get("ep_end", "?")
                    prev_arc_docs.append(
                        f"━━━ Arc {prev_arc_no} (제{prev_ep_start}화~제{prev_ep_end}화) ━━━\n{prev_tactical}"
                    )
            if prev_arc_docs:
                full_arc_history = "\n\n".join(prev_arc_docs)
                if len(full_arc_history) > ContextLimits.MAX_CONTEXT_CHARS:
                    full_arc_history = full_arc_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (1M자 절삭)"
                expanded_prev_context = (
                    f"[V67] ═══ 이전 Arc 전술서 전문 ({len(prev_arc_docs)}개) ═══\n"
                    f"{full_arc_history}\n\n"
                    f"═══ 상태 요약 ═══\n{last_refined_context}"
                )
                logging.info(
                    "📚 [V67] Director 컨텍스트 확장: %d개 Arc (%d자)",
                    len(prev_arc_docs),
                    len(expanded_prev_context),
                )

        story_context = ""
        try:
            prot_config = bible_root.get("protagonist_config", {})
            sc_parts = [f"- 장르: {genre}"]
            if prot_config:
                sc_parts.append(f"- 주인공: {prot_config.get('name', protagonist_name or '미상')}")
                incarnation = prot_config.get("incarnation_type", "미상")
                sc_parts.append(f"- 환생 유형: {incarnation}")
                if incarnation == "회귀자":
                    sc_parts.append("→ 회귀자: 미래를 알고 역사를 변경하려 함. 이것은 모순이 아님.")
                elif incarnation == "빙의자":
                    sc_parts.append("→ 빙의자: 원래 인물과 다른 인격.")
                elif incarnation == "환생자":
                    sc_parts.append("→ 환생자: 전생 기억 보유.")
            story_context = "\n".join(sc_parts)
        except (KeyError, TypeError, AttributeError) as exc:
            logging.warning(f"[SilentPass:Stage2Finalizer] 스토리 컨텍스트 생성 실패: {exc!s:.100}")
            story_context = ""

        if isinstance(enriched_block, dict):
            genre_ext = enriched_block.get("genre_ext", {})
            if isinstance(genre_ext, dict):
                target_capital = genre_ext.get("capital_after")
                if target_capital:
                    story_context += (
                        f"\n\n[NS-2 참고] Treatment 블록 목표 자본: {target_capital}. "
                        "Arc 설계 자본이 목표에서 과도하게 벗어나지 않도록 주의하십시오."
                    )

        if constraint_block and "[Python 자동 수정" in constraint_block:
            corr_start = constraint_block.find("[Python 자동 수정")
            corr_end = constraint_block.find("\n\n[Python Pre-Director advisory", corr_start)
            corr_advisory = constraint_block[corr_start:corr_end] if corr_end > 0 else constraint_block[corr_start:]
            story_context += f"\n\n⚠️ {corr_advisory}"

        if constraint_block and "[Python Pre-Director advisory" in constraint_block:
            adv_start = constraint_block.find("[Python Pre-Director advisory")
            adv_text = constraint_block[adv_start:]
            story_context += f"\n\n⚠️ {adv_text}"

        tactical_doc = refined_arc.get("tactical_doc", "") if isinstance(refined_arc, dict) else ""
        cross_arc_issues = _check_cross_arc_asset_continuity(tactical_doc, all_refined_arcs)
        if cross_arc_issues:
            story_context += "\n\n" + "\n".join(cross_arc_issues)
            logging.info("[TF-57-C] 크로스-Arc 자산 연속성 advisory 주입: %d건", len(cross_arc_issues))

        if tactical_doc:
            try:
                checker = NumericConsistencyChecker()
                warns = checker.check_tactical_doc(tactical_doc, global_arc_no)
                if warns:
                    nc1_text = "\n".join(f"  - [{w['severity']}] {w['text']}" for w in warns)
                    story_context += (
                        f"\n\n[NC-1-S2 산술 검증 경고]\n{nc1_text}\n위 경고를 참고하여 수치 정합성을 검증하세요."
                    )
                    logging.info("[TF-60] NC-1-S2 advisory 주입: %d건", len(warns))
            except Exception as nc1_err:
                logging.debug("[TF-60] NC-1-S2 검사 실패 (비치명): %s", nc1_err)

        if tactical_doc:
            try:
                arithmetic_issues = _check_tactical_arithmetic(str(tactical_doc))
                if arithmetic_issues:
                    arithmetic_warn = "\n".join(f"  - {item}" for item in arithmetic_issues)
                    logging.warning("[NS-1-P/S2] 첫 생성 arithmetic warning:\n%s", arithmetic_warn)
                    story_context += (
                        f"\n\n[NS-1-P arithmetic warning]\n{arithmetic_warn}\n"
                        "Please verify tactical_doc arithmetic before approving."
                    )
            except Exception as arithmetic_err:
                logging.debug("[TF-60] _check_tactical_arithmetic 실패 (비치명): %s", arithmetic_err)

        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        arc_dep_advisory = _build_arc_dependency_advisory(db, refined_arc.get("arc_no") or global_arc_no)
        if arc_dep_advisory:
            story_context = f"{story_context}\n\n{arc_dep_advisory}" if story_context else arc_dep_advisory

        voice_advisory = _build_character_voice_advisory(db)
        if voice_advisory:
            story_context = f"{story_context}\n\n{voice_advisory}" if story_context else voice_advisory

        return expanded_prev_context, story_context

    def _audit_stage2_director(
        self,
        *,
        refined_arc: dict,
        expanded_prev_context: str,
        enriched_block: dict,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        story_context: str,
        global_arc_no: int,
        draft_validator_passed: bool,
        consensus_passed: bool,
    ) -> tuple[dict, int, str, int]:
        director_duration_ms = None
        director_t0 = time.monotonic()
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_director")
        except (AttributeError, TypeError) as exc:
            logging.debug(f"[PerfTimer] start s2 director: {exc}")

        self.ctx.ui.log("      🤔 [Director] 전략적 무결성 검수 중 (LLM 호출, 1~3분 소요)...")
        try:
            audit = self.ctx.agents["director"].audit_strategic_plan(
                refined_arc,
                expanded_prev_context,
                curr_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry=entity_registry_for_director,
                story_context=story_context,
            )
        except (RuntimeError, OSError, ValueError) as dir_err:
            logging.warning(f"[G7] Director 심사 호출 실패: {dir_err!s:.100}")
            self.ctx.ui.log("      ⚠️ [Director] 심사 호출 실패 — 폴백 REJECT")
            audit = {
                "decision": "REJECT",
                "score": 50,
                "reason": "Director 호출 실패 — 폴백 REJECT",
                "self_consistency": {},
            }

        try:
            elapsed = self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_director")
            if elapsed and elapsed > 0:
                director_duration_ms = max(0, int(elapsed * 1000))
        except (AttributeError, TypeError) as exc:
            logging.debug(f"[PerfTimer] stop s2 director: {exc}")
        if director_duration_ms is None:
            director_duration_ms = max(0, int((time.monotonic() - director_t0) * 1000))

        decision = audit.get("decision", "?")
        decision_score = audit.get("score", "?")
        reason = audit.get("reason", "")
        self.ctx.ui.log(f"\n      🎬 [Director] {decision} (score={decision_score})")
        if reason:
            for idx in range(0, len(str(reason)), 80):
                self.ctx.ui.log(f"         {str(reason)[idx : idx + 80]}")
        contradictions = audit.get("contradictions", [])
        if contradictions and not isinstance(contradictions, list):
            contradictions = [contradictions] if contradictions else []
        if contradictions:
            self.ctx.ui.log(f"         📌 모순 {len(contradictions)}건:")
            for contradiction in contradictions:
                self.ctx.ui.log(f"            ▸ {contradiction!s}")
        if decision == "REJECT" and audit.get("re_slice_instruction"):
            self.ctx.ui.log(f"         🔧 수정지시: {audit['re_slice_instruction']!s}")
        director_thinking = audit.get("_director_thinking", "")
        if director_thinking:
            self.ctx.ui.log("      💭 [Director Thinking]")
            self.ctx.ui.log(director_thinking)

        if audit.get("decision") == "REJECT" and draft_validator_passed and consensus_passed:
            self_consistency = audit.get("self_consistency", {})
            scores = self_consistency.get("scores", [])
            all_default_50 = len(scores) >= 2 and all(s == 50 for s in scores)
            zero_count = sum(1 for s in scores if s == 0)
            many_zeros = len(scores) >= 2 and zero_count >= len(scores) // 2
            is_quota_failure = all_default_50 or many_zeros
            if is_quota_failure:
                logging.warning(
                    "[TF-25-07] V60.43 API 쿼터 실패 패턴 감지 — Director REJECT 유지 (score=0이 %d/%d개)",
                    zero_count,
                    len(scores),
                )
                audit["v60_43_api_warning"] = True

        score_raw = audit.get("score", 0)
        try:
            score = int(score_raw)
        except (ValueError, TypeError):
            score = 0

        return audit, director_duration_ms, decision, score

    def _log_stage2_session_decision(
        self,
        *,
        audit: dict,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        score: int,
    ) -> None:
        session_logger = getattr(self.ctx, "session_logger", None)
        if session_logger:
            try:
                session_logger.log_decision(
                    stage="stage2",
                    ep_num=global_arc_no,
                    round_num=attempt,
                    decision_type="arc",
                    result=audit.get("decision", "UNKNOWN"),
                    score=score,
                    generation_method=generation_method,
                    reason=str(audit.get("reason", ""))[:500],
                )
            except (AttributeError, TypeError) as exc:
                logging.debug("[SilentPass:S2:SessionLog] %s", exc)

    def _prepare_stage2_pass_fix_iteration(
        self,
        *,
        four_phase,
        current_arc: dict,
        current_audit: dict,
        global_arc_no: int,
        fix_i: int,
        max_fix: int,
        applied_patches: list[str],
        patch_pressure_exceeded: bool,
    ) -> dict[str, Any] | None:
        from modules.validation.threshold_helper import _threshold

        fix_scope = current_audit.get("fix_scope", "")
        if not fix_scope:
            logging.warning("[PF-1] fix_scope 누락 → local patch authority 없음, retry 경로 위임")
            self.ctx.ui.log("      🔀 [PF-1] fix_scope 누락 → inplace 권한 없음, retry 경로 위임")
            return None
        if fix_scope in ("partial", "full"):
            self.ctx.ui.log(f"      🔀 [TF-33] fix_scope={fix_scope!r} → inplace 불가, retry 경로 위임")
            return None

        fix_instr = current_audit.get("re_slice_instruction", "")
        self.ctx.ui.log(f"      🔧 [TF-32-V] PASS_WITH_FIX patch #{fix_i + 1}/{max_fix} (fix: {fix_instr!s})")
        if not (four_phase and hasattr(four_phase, "_inplace_patch_arc")):
            logging.warning("[TF-32-V] four_phase 에이전트 미등록 → REJECT")
            return None

        try:
            patched = four_phase._inplace_patch_arc(
                original_arc=current_arc,
                director_feedback=fix_instr,
                arc_no=global_arc_no,
            )
        except (RuntimeError, ValueError, OSError):
            logging.exception("[TF-32-V] inplace_patch_arc 예외")
            return None
        if not patched:
            logging.warning("[TF-32-V] patch 실패 → REJECT")
            return None

        patch_guard_signals = self._collect_arc_patch_guard_signals(
            original_arc=current_arc,
            patched_arc=patched,
        )
        if patch_guard_signals:
            signal_state = self._merge_patch_guard_signals(
                current_audit,
                patch_guard_signals,
                attempt=fix_i + 1,
            )
            signal_codes = ", ".join(signal_state.get("codes", []))
            logging.warning(
                "[S2-ArcPatchSignals] attempt=%s arc=%s codes=%s",
                fix_i + 1,
                global_arc_no,
                signal_codes,
            )
            self.ctx.ui.log(f"      ⚠️ [S2-ArcSignals] attempt={fix_i + 1} codes={signal_codes or 'n/a'}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "patch_guard_signal",
                    "stage2 arc patch signals observed",
                    {
                        "arc_no": global_arc_no,
                        "attempt": fix_i + 1,
                        "codes": list(signal_state.get("codes", [])),
                        "count": int(signal_state.get("count", 0) or 0),
                        "items": list(patch_guard_signals),
                    },
                )

        arith_patch_ctx = ""
        tactical_patched = patched.get("tactical_doc", "") if isinstance(patched, dict) else ""
        if tactical_patched:
            arithmetic_issues = _check_tactical_arithmetic(str(tactical_patched))
            if arithmetic_issues:
                arithmetic_warn = "\n".join(f"  - {item}" for item in arithmetic_issues)
                logging.warning("[NS-1-P] arithmetic warning detected in inplace patch:\n%s", arithmetic_warn)
                arith_patch_ctx = (
                    "\n\n[NS-1-P arithmetic warning in inplace patch]\n"
                    f"{arithmetic_warn}\n"
                    "Please verify the patched tactical_doc arithmetic before approving."
                )

        try:
            from modules.core.constants import calc_patch_change_ratio, log_patch_diff

            orig_json = json.dumps(current_arc, ensure_ascii=False)
            patch_json = json.dumps(patched, ensure_ascii=False)
            log_patch_diff(
                "S2-Arc",
                json.dumps(current_arc, ensure_ascii=False, indent=2),
                json.dumps(patched, ensure_ascii=False, indent=2),
            )
            change_ratio = calc_patch_change_ratio(orig_json, patch_json)
            max_ratio = float(_threshold("patch_mode.inplace_max_change_ratio", 0.30))
            if change_ratio > max_ratio:
                patch_pressure_exceeded = True
                patch_pressure = current_audit.setdefault("patch_pressure", {})
                patch_pressure["exceeded"] = True
                patch_pressure["count"] = int(patch_pressure.get("count", 0)) + 1
                patch_pressure["change_ratio"] = round(float(change_ratio), 4)
                patch_pressure["max_ratio"] = round(float(max_ratio), 4)
                patch_pressure["attempt"] = fix_i + 1
                logging.warning(
                    "[F-2] InPlace Arc 변경 비율 %.1f%% > %.0f%% (S2)",
                    change_ratio * 100,
                    max_ratio * 100,
                )
        except Exception as exc:
            logging.debug("[S2-Finalizer] change_ratio 계산 실패: %s", exc)

        if fix_instr:
            applied_patches.append(str(fix_instr))

        return {
            "patched": patched,
            "patch_guard_signals": patch_guard_signals,
            "arith_patch_ctx": arith_patch_ctx,
            "patch_pressure_exceeded": patch_pressure_exceeded,
        }

    def _build_stage2_pass_fix_story_context(
        self,
        *,
        story_context: str,
        arith_patch_ctx: str,
        patch_guard_signals: list[dict],
        current_audit: dict,
        applied_patches: list[str],
        fix_i: int,
    ) -> str:
        patch_ctx = arith_patch_ctx
        if patch_guard_signals:
            patch_ctx += self._format_patch_guard_signal_notice(
                patch_guard_signals,
                attempt=fix_i + 1,
            )
        if isinstance(current_audit.get("patch_pressure"), dict) and current_audit["patch_pressure"].get("exceeded"):
            patch_pressure = dict(current_audit.get("patch_pressure") or {})
            patch_ctx += (
                "\n\n[F-2 advisory — high Arc patch pressure]\n"
                f"change_ratio={float(patch_pressure.get('change_ratio', 0.0)):.1%}, "
                f"threshold={float(patch_pressure.get('max_ratio', 0.0)):.0%}, "
                f"attempt={int(patch_pressure.get('attempt', fix_i + 1))}\n"
                "이 local Arc patch는 국소 수정 범위를 넘어설 수 있습니다. "
                "구조 일관성과 변경 정당성이 충분하면 PASS를 허용할 수 있지만, "
                "광범위 재작성처럼 보이면 PASS_WITH_FIX 또는 REJECT를 유지하세요."
            )
        if applied_patches:
            patch_lines = "\n".join(f"- {patch}" for patch in applied_patches)
            patch_ctx += (
                "\n\n[PASS_WITH_FIX 재심사 — 이미 적용된 패치]\n"
                f"{patch_lines}\n"
                "위 항목은 tactical_doc에 이미 반영되었습니다. "
                "curr_block 문서에서 동일 오류가 보여도 tactical_doc에서 수정되었으면 승인하세요."
            )
        return (story_context or "") + patch_ctx

    def _merge_stage2_pass_fix_reaudit(
        self,
        *,
        current_audit: dict,
        re_audit: dict,
    ) -> dict:
        if isinstance(current_audit.get("fix_pack"), dict):
            re_audit["fix_pack"] = deepcopy(current_audit["fix_pack"])
        if isinstance(current_audit.get("partial_fix_eval"), dict):
            re_audit["partial_fix_eval"] = deepcopy(current_audit["partial_fix_eval"])
        if isinstance(current_audit.get("patch_pressure"), dict):
            re_audit["patch_pressure"] = deepcopy(current_audit["patch_pressure"])
        if isinstance(current_audit.get("patch_guard_signals"), dict):
            re_audit["patch_guard_signals"] = deepcopy(current_audit["patch_guard_signals"])
        return re_audit

    def _finalize_stage2_pass_fix_success(
        self,
        *,
        refined_arc: dict,
        current_arc: dict,
        current_audit: dict,
        re_score: int,
    ) -> Stage2PassWithFixLoopResult:
        refined_arc.clear()
        refined_arc.update(current_arc)
        audit = current_audit
        decision = "PASS"
        score = re_score
        if isinstance(audit.get("patch_pressure"), dict) and audit["patch_pressure"].get("exceeded"):
            audit["decision"] = "PASS"
            audit["reason"] = (
                f"{str(audit.get('reason', '')).strip()}\n"
                "[PatchPressure Advisory] In-place patch ratio exceeded threshold; "
                "Director re-audit cleared this Arc with explicit warning context."
            ).strip()
            patch_pressure = audit.setdefault("patch_pressure", {})
            patch_pressure["director_advisory_only"] = True
            patch_pressure["cleared_verdict"] = "PASS"
            self.ctx.ui.log("      ⚠️ [TF-32-V] Patch pressure exceeded -> advisory only, PASS 유지")
        else:
            audit["decision"] = "PASS"
            self.ctx.ui.log("      ✅ [TF-32-V] Arc 수정 완료 → PASS 확정")
        return {"refined_arc": refined_arc, "audit": audit, "decision": decision, "score": score}

    def _finalize_stage2_pass_fix_reject(
        self,
        *,
        refined_arc: dict,
        current_arc: dict,
        current_audit: dict,
        audit: dict,
        score: int,
        max_fix: int,
    ) -> Stage2PassWithFixLoopResult:
        audit["decision"] = "REJECT"
        decision = "REJECT"
        last_decision = current_audit.get("decision", "")
        if last_decision == "PASS_WITH_FIX" and current_arc != dict(refined_arc):
            refined_arc.clear()
            refined_arc.update(current_arc)
            patch_fix_score = current_audit.get("score", score)
            try:
                patch_fix_score = int(patch_fix_score)
            except (ValueError, TypeError):
                patch_fix_score = score
            audit["score"] = patch_fix_score
            self.ctx.ui.log(f"      📈 [PF-3] PASS_WITH_FIX 소진 → 패치본 채택 (score={patch_fix_score})")
            score = patch_fix_score
        last_fix_scope = current_audit.get("fix_scope", "")
        if last_fix_scope:
            audit["fix_scope"] = last_fix_scope
        last_fix_scope_reasoning = current_audit.get("fix_scope_reasoning", "")
        if last_fix_scope_reasoning:
            audit["fix_scope_reasoning"] = last_fix_scope_reasoning
        if isinstance(current_audit.get("fix_pack"), dict):
            audit["fix_pack"] = deepcopy(current_audit["fix_pack"])
        if isinstance(current_audit.get("partial_fix_eval"), dict):
            audit["partial_fix_eval"] = deepcopy(current_audit["partial_fix_eval"])
        if isinstance(current_audit.get("patch_pressure"), dict):
            audit["patch_pressure"] = deepcopy(current_audit["patch_pressure"])
        if isinstance(current_audit.get("patch_guard_signals"), dict):
            audit["patch_guard_signals"] = deepcopy(current_audit["patch_guard_signals"])
        audit["reason"] = (audit.get("reason", "") or "") + f"\n[TF-32-V] PASS_WITH_FIX 수정 {max_fix}회 내 미해결 → REJECT"
        audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "지적사항 미해결 — 재설계 필요"
        self.ctx.ui.log("      ❌ [TF-32-V] 수정 실패 → REJECT 전환")
        return {"refined_arc": refined_arc, "audit": audit, "decision": decision, "score": score}

    def _run_stage2_pass_with_fix_loop(
        self,
        *,
        refined_arc: dict,
        audit: dict,
        expanded_prev_context: str,
        enriched_block: dict,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        story_context: str,
        global_arc_no: int,
        score: int,
    ) -> Stage2PassWithFixLoopResult:
        max_fix = 3
        four_phase = self.ctx.agents.get("four_phase")
        current_arc = dict(refined_arc)
        current_audit = audit
        fix_ok = False
        applied_patches: list[str] = []
        patch_pressure_exceeded = False
        re_score = score
        loop_state = self._execute_stage2_pass_fix_iterations(
            four_phase=four_phase,
            current_arc=current_arc,
            current_audit=current_audit,
            expanded_prev_context=expanded_prev_context,
            enriched_block=enriched_block,
            protagonist_name=protagonist_name,
            suspected_duplicates=suspected_duplicates,
            entity_registry_for_director=entity_registry_for_director,
            story_context=story_context,
            global_arc_no=global_arc_no,
            max_fix=max_fix,
            fix_ok=fix_ok,
            applied_patches=applied_patches,
            patch_pressure_exceeded=patch_pressure_exceeded,
            re_score=re_score,
        )
        current_arc = loop_state["current_arc"]
        current_audit = loop_state["current_audit"]
        fix_ok = bool(loop_state["fix_ok"])
        patch_pressure_exceeded = bool(loop_state["patch_pressure_exceeded"])
        re_score = int(loop_state["re_score"])
        if fix_ok:
            return self._finalize_stage2_pass_fix_success(
                refined_arc=refined_arc,
                current_arc=current_arc,
                current_audit=current_audit,
                re_score=re_score,
            )
        return self._finalize_stage2_pass_fix_reject(
            refined_arc=refined_arc,
            current_arc=current_arc,
            current_audit=current_audit,
            audit=audit,
            score=score,
            max_fix=max_fix,
        )

    def _resolve_stage2_pass_fix_instruction(
        self,
        *,
        current_audit: dict,
        fix_i: int,
        max_fix: int,
    ) -> str | None:
        """PASS_WITH_FIX loop에서 local patch 가능 여부와 fix instruction을 정리한다."""
        fix_scope = current_audit.get("fix_scope", "")
        if not fix_scope:
            logging.warning("[PF-1] fix_scope 누락 → local patch authority 없음, retry 경로 위임")
            self.ctx.ui.log("      🔀 [PF-1] fix_scope 누락 → inplace 권한 없음, retry 경로 위임")
            return None
        if fix_scope in ("partial", "full"):
            self.ctx.ui.log(f"      🔀 [TF-33] fix_scope={fix_scope!r} → inplace 불가, retry 경로 위임")
            return None

        fix_instr = current_audit.get("re_slice_instruction", "")
        self.ctx.ui.log(
            f"      🔧 [TF-32-V] PASS_WITH_FIX patch #{fix_i + 1}/{max_fix} (fix: {fix_instr!s})"
        )
        return fix_instr

    def _apply_stage2_pass_fix_patch(
        self,
        *,
        four_phase,
        current_arc: dict,
        fix_instr: str,
        global_arc_no: int,
        fix_pack: dict | None = None,
    ) -> dict | None:
        """inplace patch authority 호출과 예외/실패 처리를 감싼다."""
        if not (four_phase and hasattr(four_phase, "_inplace_patch_arc")):
            logging.warning("[TF-32-V] four_phase 에이전트 미등록 → REJECT")
            return None
        try:
            patched = four_phase._inplace_patch_arc(
                original_arc=current_arc,
                director_feedback=fix_instr,
                arc_no=global_arc_no,
                fix_pack=fix_pack,
            )
        except (RuntimeError, ValueError, OSError):
            logging.exception("[TF-32-V] inplace_patch_arc 예외")
            return None
        if not patched:
            logging.warning("[TF-32-V] patch 실패 → REJECT")
            return None
        return patched

    def _analyze_stage2_pass_fix_patch(
        self,
        *,
        current_arc: dict,
        current_audit: dict,
        patched: dict,
        fix_instr: str,
        global_arc_no: int,
        fix_i: int,
        applied_patches: list[str],
        patch_pressure_exceeded: bool,
    ) -> dict[str, Any]:
        """patched arc의 guard/arithmetic/pressure signals를 수집한다."""
        from modules.validation.threshold_helper import _threshold

        patch_guard_signals = self._collect_arc_patch_guard_signals(
            original_arc=current_arc,
            patched_arc=patched,
        )
        if patch_guard_signals:
            signal_state = self._merge_patch_guard_signals(
                current_audit,
                patch_guard_signals,
                attempt=fix_i + 1,
            )
            signal_codes = ", ".join(signal_state.get("codes", []))
            logging.warning(
                "[S2-ArcPatchSignals] attempt=%s arc=%s codes=%s",
                fix_i + 1,
                global_arc_no,
                signal_codes,
            )
            self.ctx.ui.log(f"      ⚠️ [S2-ArcSignals] attempt={fix_i + 1} codes={signal_codes or 'n/a'}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "patch_guard_signal",
                    "stage2 arc patch signals observed",
                    {
                        "arc_no": global_arc_no,
                        "attempt": fix_i + 1,
                        "codes": list(signal_state.get("codes", [])),
                        "count": int(signal_state.get("count", 0) or 0),
                        "items": list(patch_guard_signals),
                    },
                )

        blocking_patch_guard_signals = [
            signal for signal in patch_guard_signals if str(signal.get("code", "")).strip() in _BLOCKING_ARC_PATCH_SIGNAL_CODES
        ]
        if blocking_patch_guard_signals:
            blocking_codes = ", ".join(str(signal.get("code", "")).strip() for signal in blocking_patch_guard_signals)
            logging.warning(
                "[S2-ArcPatchSignals] blocking attempt=%s arc=%s codes=%s",
                fix_i + 1,
                global_arc_no,
                blocking_codes,
            )
            self.ctx.ui.log(f"      ⛔ [S2-ArcSignals] blocking attempt={fix_i + 1} codes={blocking_codes or 'n/a'}")

        arith_patch_ctx = ""
        tactical_patched = patched.get("tactical_doc", "") if isinstance(patched, dict) else ""
        if tactical_patched:
            arithmetic_issues = _check_tactical_arithmetic(str(tactical_patched))
            if arithmetic_issues:
                arithmetic_warn = "\n".join(f"  - {item}" for item in arithmetic_issues)
                logging.warning("[NS-1-P] arithmetic warning detected in inplace patch:\n%s", arithmetic_warn)
                arith_patch_ctx = (
                    "\n\n[NS-1-P arithmetic warning in inplace patch]\n"
                    f"{arithmetic_warn}\n"
                    "Please verify the patched tactical_doc arithmetic before approving."
                )

        try:
            from modules.core.constants import calc_patch_change_ratio, log_patch_diff

            orig_json = json.dumps(current_arc, ensure_ascii=False)
            patch_json = json.dumps(patched, ensure_ascii=False)
            log_patch_diff(
                "S2-Arc",
                json.dumps(current_arc, ensure_ascii=False, indent=2),
                json.dumps(patched, ensure_ascii=False, indent=2),
            )
            change_ratio = calc_patch_change_ratio(orig_json, patch_json)
            max_ratio = float(_threshold("patch_mode.inplace_max_change_ratio", 0.30))
            if change_ratio > max_ratio:
                patch_pressure_exceeded = True
                patch_pressure = current_audit.setdefault("patch_pressure", {})
                patch_pressure["exceeded"] = True
                patch_pressure["count"] = int(patch_pressure.get("count", 0)) + 1
                patch_pressure["change_ratio"] = round(float(change_ratio), 4)
                patch_pressure["max_ratio"] = round(float(max_ratio), 4)
                patch_pressure["attempt"] = fix_i + 1
                logging.warning(
                    "[F-2] InPlace Arc 변경 비율 %.1f%% > %.0f%% (S2)",
                    change_ratio * 100,
                    max_ratio * 100,
                )
        except Exception as exc:
            logging.debug("[S2-Finalizer] change_ratio 계산 실패: %s", exc)

        return {
            "patch_guard_signals": patch_guard_signals,
            "blocking_patch_guard_signals": blocking_patch_guard_signals,
            "patch_pressure_exceeded": patch_pressure_exceeded,
            "arith_patch_ctx": arith_patch_ctx,
        }

    def _build_stage2_pass_fix_reaudit_story_context(
        self,
        *,
        story_context: str,
        arith_patch_ctx: str,
        patch_guard_signals: list[dict],
        patch_pressure_exceeded: bool,
        current_audit: dict,
        applied_patches: list[str],
        fix_i: int,
    ) -> str:
        """re-audit용 story_context tail advisory를 조립한다."""
        patch_ctx = arith_patch_ctx
        if patch_guard_signals:
            patch_ctx += self._format_patch_guard_signal_notice(
                patch_guard_signals,
                attempt=fix_i + 1,
            )
        if patch_pressure_exceeded and isinstance(current_audit.get("patch_pressure"), dict):
            patch_pressure = dict(current_audit.get("patch_pressure") or {})
            patch_ctx += (
                "\n\n[F-2 advisory — high Arc patch pressure]\n"
                f"change_ratio={float(patch_pressure.get('change_ratio', 0.0)):.1%}, "
                f"threshold={float(patch_pressure.get('max_ratio', 0.0)):.0%}, "
                f"attempt={int(patch_pressure.get('attempt', fix_i + 1))}\n"
                "이 local Arc patch는 국소 수정 범위를 넘어설 수 있습니다. "
                "구조 일관성과 변경 정당성이 충분하면 PASS를 허용할 수 있지만, "
                "광범위 재작성처럼 보이면 PASS_WITH_FIX 또는 REJECT를 유지하세요."
            )
        if applied_patches:
            patch_lines = "\n".join(f"- {patch}" for patch in applied_patches)
            patch_ctx += (
                "\n\n[PASS_WITH_FIX 재심사 — 이미 적용된 패치]\n"
                f"{patch_lines}\n"
                "위 항목은 tactical_doc에 이미 반영되었습니다. "
                "curr_block 문서에서 동일 오류가 보여도 tactical_doc에서 수정되었으면 승인하세요."
            )
        return (story_context or "") + patch_ctx

    def _run_stage2_pass_fix_reaudit(
        self,
        *,
        patched: dict,
        expanded_prev_context: str,
        enriched_block: dict,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        story_context: str,
        fix_i: int,
    ) -> dict[str, Any] | None:
        """patched arc를 director에게 재심사시킨다."""
        self.ctx.ui.log(f"      🔄 [TF-38] Director 재심사 #{fix_i + 1} 호출 중...")
        try:
            re_audit = self.ctx.agents["director"].audit_strategic_plan(
                patched,
                expanded_prev_context,
                curr_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry=entity_registry_for_director,
                story_context=story_context,
            )
        except (RuntimeError, ValueError, OSError):
            logging.exception("[TF-32-V] 재심사 예외")
            return None

        re_decision = re_audit.get("decision", "REJECT")
        re_score = re_audit.get("score", 0)
        try:
            re_score = int(re_score)
        except (ValueError, TypeError):
            re_score = 0
        self.ctx.ui.log(f"      🎬 [TF-32-V] 재심사 #{fix_i + 1}: {re_decision} (score={re_score})")
        return {
            "audit": re_audit,
            "decision": re_decision,
            "score": re_score,
        }

    def _apply_stage2_pass_fix_reaudit_result(
        self,
        *,
        patched: dict,
        current_arc: dict,
        current_audit: dict,
        fix_ok: bool,
        re_audit: dict,
        re_decision: str,
        re_score: int,
    ) -> dict[str, Any]:
        """re-audit verdict를 loop state로 반영한다."""
        from modules.validation.threshold_helper import _threshold

        if re_decision == "PASS":
            quality_gate_score = _threshold("scoring.quality_gate_score", 90)
            if re_score < quality_gate_score:
                self.ctx.ui.log(
                    f"      ⚠️ [TF-35] 재심사 PASS이나 score={re_score} < {quality_gate_score} → patch 종료"
                )
                return {
                    "current_arc": current_arc,
                    "current_audit": current_audit,
                    "fix_ok": fix_ok,
                    "re_score": re_score,
                    "action": "break",
                }
            return {
                "current_arc": patched,
                "current_audit": self._merge_stage2_pass_fix_reaudit(
                    current_audit=current_audit,
                    re_audit=re_audit,
                ),
                "fix_ok": True,
                "re_score": re_score,
                "action": "break",
            }
        if re_decision == "PASS_WITH_FIX":
            return {
                "current_arc": patched,
                "current_audit": self._merge_stage2_pass_fix_reaudit(
                    current_audit=current_audit,
                    re_audit=re_audit,
                ),
                "fix_ok": fix_ok,
                "re_score": re_score,
                "action": "continue",
            }
        return {
            "current_arc": current_arc,
            "current_audit": current_audit,
            "fix_ok": fix_ok,
            "re_score": re_score,
            "action": "break",
        }

    def _execute_stage2_pass_fix_iterations(
        self,
        *,
        four_phase,
        current_arc: dict,
        current_audit: dict,
        expanded_prev_context: str,
        enriched_block: dict,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        story_context: str,
        global_arc_no: int,
        max_fix: int,
        fix_ok: bool,
        applied_patches: list[str],
        patch_pressure_exceeded: bool,
        re_score: int,
    ) -> dict[str, Any]:
        for fix_i in range(max_fix):
            fix_instr = self._resolve_stage2_pass_fix_instruction(
                current_audit=current_audit,
                fix_i=fix_i,
                max_fix=max_fix,
            )
            if fix_instr is None:
                break
            fix_pack = normalize_stage2_fix_pack(
                current_audit,
                default_fix_instruction=fix_instr,
            )
            if fix_pack:
                current_audit["fix_pack"] = dict(fix_pack)
            patched = self._apply_stage2_pass_fix_patch(
                four_phase=four_phase,
                current_arc=current_arc,
                fix_instr=fix_instr,
                global_arc_no=global_arc_no,
                fix_pack=fix_pack,
            )
            if patched is None:
                break
            patch_state = self._analyze_stage2_pass_fix_patch(
                current_arc=current_arc,
                current_audit=current_audit,
                patched=patched,
                fix_instr=fix_instr,
                global_arc_no=global_arc_no,
                fix_i=fix_i,
                applied_patches=applied_patches,
                patch_pressure_exceeded=patch_pressure_exceeded,
            )
            patch_pressure_exceeded = bool(patch_state["patch_pressure_exceeded"])
            blocking_patch_guard_signals = list(patch_state.get("blocking_patch_guard_signals") or [])
            if blocking_patch_guard_signals:
                blocking_lines = "; ".join(
                    f"{str(signal.get('code', '')).strip()}: {str(signal.get('detail', '')).strip()}"
                    for signal in blocking_patch_guard_signals
                    if str(signal.get("code", "")).strip()
                )
                blocking_hint = (
                    "Do not place an episode-end outcome artifact inside [시작 상태]. "
                    "Move confirmation/proof items to the later causal beat or [종료 상태]."
                )
                if blocking_lines:
                    blocking_hint = f"{blocking_hint} Observed patch guard: {blocking_lines}"
                current_fix_instr = str(current_audit.get("re_slice_instruction", "") or "").strip()
                if blocking_hint not in current_fix_instr:
                    current_audit["re_slice_instruction"] = "\n".join(
                        part for part in (current_fix_instr, blocking_hint) if part
                    )
                current_audit["decision"] = "PASS_WITH_FIX"
                self.ctx.ui.log("      ↩️ [TF-32-V] blocking Arc patch signal -> 재감리 생략, 다음 patch 시도")
                continue
            if fix_instr:
                applied_patches.append(str(fix_instr))
            re_story_context = self._build_stage2_pass_fix_reaudit_story_context(
                story_context=story_context,
                arith_patch_ctx=patch_state["arith_patch_ctx"],
                patch_guard_signals=patch_state["patch_guard_signals"],
                patch_pressure_exceeded=patch_pressure_exceeded,
                current_audit=current_audit,
                applied_patches=applied_patches,
                fix_i=fix_i,
            )
            re_state = self._run_stage2_pass_fix_reaudit(
                patched=patched,
                expanded_prev_context=expanded_prev_context,
                enriched_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry_for_director=entity_registry_for_director,
                story_context=re_story_context,
                fix_i=fix_i,
            )
            if re_state is None:
                break
            if fix_pack:
                re_state["audit"]["fix_pack"] = dict(fix_pack)
            partial_fix_eval = build_stage2_partial_fix_eval(
                fix_pack=fix_pack,
                patch_round=fix_i + 1,
                verdict=re_state["decision"],
            )
            if partial_fix_eval:
                re_state["audit"]["partial_fix_eval"] = partial_fix_eval
            loop_state = self._apply_stage2_pass_fix_reaudit_result(
                patched=patched,
                current_arc=current_arc,
                current_audit=current_audit,
                fix_ok=fix_ok,
                re_audit=re_state["audit"],
                re_decision=re_state["decision"],
                re_score=int(re_state["score"]),
            )
            current_arc = loop_state["current_arc"]
            current_audit = loop_state["current_audit"]
            fix_ok = bool(loop_state["fix_ok"])
            re_score = int(loop_state["re_score"])
            if loop_state["action"] == "continue":
                continue
            break
        return {
            "current_arc": current_arc,
            "current_audit": current_audit,
            "fix_ok": fix_ok,
            "patch_pressure_exceeded": patch_pressure_exceeded,
            "re_score": re_score,
        }

    def _legacy_stage2_pass_with_fix_loop_outcome(
        self,
        *,
        refined_arc: dict,
        audit: dict,
        current_arc: dict,
        current_audit: dict,
        fix_ok: bool,
        patch_pressure_exceeded: bool,
        re_score: int,
        score: int,
        max_fix: int,
    ) -> Stage2PassWithFixLoopResult:
        if fix_ok:
            refined_arc.clear()
            refined_arc.update(current_arc)
            audit = current_audit
            decision = "PASS"
            score = re_score
            if patch_pressure_exceeded:
                audit["decision"] = "PASS"
                audit["reason"] = (
                    f"{str(audit.get('reason', '')).strip()}\n"
                    "[PatchPressure Advisory] In-place patch ratio exceeded threshold; "
                    "Director re-audit cleared this Arc with explicit warning context."
                ).strip()
                patch_pressure = audit.setdefault("patch_pressure", {})
                patch_pressure["director_advisory_only"] = True
                patch_pressure["cleared_verdict"] = "PASS"
                self.ctx.ui.log("      ⚠️ [TF-32-V] Patch pressure exceeded -> advisory only, PASS 유지")
            else:
                audit["decision"] = "PASS"
                self.ctx.ui.log("      ✅ [TF-32-V] Arc 수정 완료 → PASS 확정")
            return {"refined_arc": refined_arc, "audit": audit, "decision": decision, "score": score}

        audit["decision"] = "REJECT"
        decision = "REJECT"
        last_decision = current_audit.get("decision", "")
        if last_decision == "PASS_WITH_FIX" and current_arc != dict(refined_arc):
            refined_arc.clear()
            refined_arc.update(current_arc)
            patch_fix_score = current_audit.get("score", score)
            try:
                patch_fix_score = int(patch_fix_score)
            except (ValueError, TypeError):
                patch_fix_score = score
            audit["score"] = patch_fix_score
            self.ctx.ui.log(f"      📈 [PF-3] PASS_WITH_FIX 소진 → 패치본 채택 (score={patch_fix_score})")
            score = patch_fix_score
        last_fix_scope = current_audit.get("fix_scope", "")
        if last_fix_scope:
            audit["fix_scope"] = last_fix_scope
        last_fix_scope_reasoning = current_audit.get("fix_scope_reasoning", "")
        if last_fix_scope_reasoning:
            audit["fix_scope_reasoning"] = last_fix_scope_reasoning
        if isinstance(current_audit.get("patch_pressure"), dict):
            audit["patch_pressure"] = deepcopy(current_audit["patch_pressure"])
        if isinstance(current_audit.get("patch_guard_signals"), dict):
            audit["patch_guard_signals"] = deepcopy(current_audit["patch_guard_signals"])
        audit["reason"] = (audit.get("reason", "") or "") + f"\n[TF-32-V] PASS_WITH_FIX 수정 {max_fix}회 내 미해결 → REJECT"
        audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "지적사항 미해결 — 재설계 필요"
        self.ctx.ui.log("      ❌ [TF-32-V] 수정 실패 → REJECT 전환")
        return {"refined_arc": refined_arc, "audit": audit, "decision": decision, "score": score}

    def _record_s2_pass_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        selected_strategy: str = "",
        audit: dict,
        duration_ms: int | None = None,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
        artifact_payload: dict | None = None,
    ) -> None:
        """[4-R3-f] Record Stage 2 PASS metrics (PassRateMonitor, Dashboard, Optimizer, PerfTimer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        _session_id = resolve_logging_session_id(getattr(self.ctx, "current_project", None))
        attempt_key = build_attempt_key(
            stage=2,
            ep_num=global_arc_no,
            arc_num=global_arc_no,
            attempt_num=attempt + 1,
            session_id=_session_id,
        )
        _candidate_key = build_candidate_key(strategy=selected_strategy, fallback=generation_method)
        _artifact_meta = snapshot_logged_artifact(
            getattr(self.ctx, "current_project", None),
            stage=2,
            arc_num=global_arc_no,
            attempt_num=attempt + 1,
            candidate_key=_candidate_key,
            artifact_kind="final_arc",
            payload=artifact_payload,
        )
        _token_cost = _peek_scope_total_cost_usd()

        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
            try:
                self.ctx.pass_rate_monitor.record_attempt(
                    stage=2,
                    episode=global_arc_no,
                    arc=global_arc_no,
                    attempt_num=attempt + 1,
                    success=True,
                    generation_method=generation_method,
                    duration_ms=duration_ms or 0,
                    token_cost=_token_cost,
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                    attempt_key=attempt_key,
                    final_verdict=str(audit.get("decision", "PASS")),
                    candidate_key=_candidate_key,
                    content_hash=_artifact_meta["content_hash"],
                    artifact_path=_artifact_meta["artifact_path"],
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (success): {e}")

        try:
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if _db and hasattr(_db, "save_stage_attempt"):
                _score = audit.get("score", 0)
                if not isinstance(_score, int):
                    try:
                        _score = int(_score)
                    except (ValueError, TypeError):
                        _score = 0
                _director = getattr(getattr(self.ctx, "agents", {}), "get", lambda *_: None)("director")
                _model = getattr(_director, "primary_model", None) if _director else None
                _failure_category = self._extract_failure_category(audit)
                _advisory_flags = self._extract_advisory_flags(audit)
                _prompt_version = _build_stage2_prompt_version(
                    generation_method=generation_method,
                    is_patch=is_patch,
                )
                _db.save_stage_attempt(
                    stage=2,
                    verdict=str(audit.get("decision", "PASS")),
                    attempt_num=attempt + 1,
                    ep_num=global_arc_no,
                    arc_num=global_arc_no,
                    score=_score,
                    failure_category=_failure_category,
                    fix_scope=str(audit.get("fix_scope", "") or ""),
                    model=str(_model) if _model else None,
                    duration_ms=duration_ms,
                    advisory_flags=_advisory_flags,
                    session_id=_session_id,
                    attempt_key=attempt_key,
                    generation_method=generation_method,
                    prompt_version=_prompt_version,
                    candidate_key=_candidate_key,
                    content_hash=_artifact_meta["content_hash"],
                    artifact_path=_artifact_meta["artifact_path"],
                    selection_reason=str(audit.get("selection_reason", "") or ""),
                    verdict_reason=str(audit.get("verdict_reason", "") or ""),
                    fix_scope_reasoning=str(audit.get("fix_scope_reasoning", "") or ""),
                    open_review=str(audit.get("open_review", "") or ""),
                    runtime_advisory="",
                    retry_directives="",
                )
                # [TF-60] Stage 2 director_selections 기록
                if hasattr(_db, "save_director_selection"):
                    try:
                        _db.save_director_selection(
                            ep_num=global_arc_no,
                            round_num=attempt + 1,
                            selected_label="",
                            selected_strategy=selected_strategy or generation_method or "",
                            verdict=str(audit.get("decision", "PASS")),
                            stage=2,
                            score=_score,
                            selection_reason=str(audit.get("reason", "")),
                            fix_scope=str(audit.get("fix_scope", "") or ""),
                            advisory_warnings=_advisory_flags,
                            attempt_key=attempt_key,
                            candidate_key=_candidate_key,
                            content_hash=_artifact_meta["content_hash"],
                            artifact_path=_artifact_meta["artifact_path"],
                            director_thinking=str(audit.get("_director_thinking", "") or ""),
                        )
                    except Exception as _ds_err:
                        logging.debug("[director_selections] Stage2 PASS 기록 실패: %s", _ds_err)
        except Exception as _sa_err:
            logging.debug("[stage_attempts] Stage2 PASS 기록 실패 (비차단): %s", _sa_err)

        if V50_MODULES_AVAILABLE and self.ctx.quality_dashboard:
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=global_arc_no,
                    result={
                        "decision": "PASS",
                        "score": audit.get("score", 80),
                        "violations": [],
                        "warnings": [],
                    },
                    stage=2,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: dashboard metrics
                logging.debug(f"[SILENT] dashboard metrics (PASS): {e}")

        if self.ctx.stage2_optimizer:
            try:
                self.ctx.stage2_optimizer.failure_memory.clear_arc_failures(global_arc_no)
                self.ctx.ui.log(f"      ✨ [V60.25] Arc {global_arc_no} 최종 성공 - 실패 메모리 클리어")
            except Exception as e:  # [V64.P4] OPTIONAL: optimizer memory clear
                logging.debug(f"[SILENT] optimizer memory clear: {e}")

        try:
            self.ctx.perf_timer.log_summary()
            self.ctx.perf_timer.reset()
        except Exception as e:
            logging.debug(f"[PerfTimer] s2 summary/reset: {e}")

    def _build_stage2_reject_metric_context(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        selected_strategy: str,
        artifact_payload: dict | None,
    ) -> dict[str, Any]:
        session_id = resolve_logging_session_id(getattr(self.ctx, "current_project", None))
        attempt_key = build_attempt_key(
            stage=2,
            ep_num=global_arc_no,
            arc_num=global_arc_no,
            attempt_num=attempt + 1,
            session_id=session_id,
        )
        candidate_key = build_candidate_key(strategy=selected_strategy, fallback=generation_method)
        artifact_meta = snapshot_logged_artifact(
            getattr(self.ctx, "current_project", None),
            stage=2,
            arc_num=global_arc_no,
            attempt_num=attempt + 1,
            candidate_key=candidate_key,
            artifact_kind="rejected_arc",
            payload=artifact_payload,
        )
        return {
            "session_id": session_id,
            "attempt_key": attempt_key,
            "candidate_key": candidate_key,
            "artifact_meta": artifact_meta,
            "token_cost": _peek_scope_total_cost_usd(),
        }

    def _persist_stage2_reject_attempt_records(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        selected_strategy: str,
        audit: dict,
        duration_ms: int | None,
        is_patch: bool,
        metric_context: dict[str, Any],
    ) -> None:
        try:
            db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if not (db and hasattr(db, "save_stage_attempt")):
                return

            score = audit.get("score", 0)
            if not isinstance(score, int):
                try:
                    score = int(score)
                except (ValueError, TypeError):
                    score = 0
            director = getattr(getattr(self.ctx, "agents", {}), "get", lambda *_: None)("director")
            model = getattr(director, "primary_model", None) if director else None
            failure_category = self._extract_failure_category(audit)
            advisory_flags = self._extract_advisory_flags(audit)
            prompt_version = _build_stage2_prompt_version(
                generation_method=generation_method,
                is_patch=is_patch,
            )
            db.save_stage_attempt(
                stage=2,
                verdict=str(audit.get("decision", "REJECT")),
                attempt_num=attempt + 1,
                ep_num=global_arc_no,
                arc_num=global_arc_no,
                score=score,
                failure_category=failure_category,
                reject_reason=str(audit.get("reason", "")),
                fix_scope=str(audit.get("fix_scope", "") or ""),
                selection_reason=str(audit.get("selection_reason", "") or ""),
                verdict_reason=str(audit.get("verdict_reason", "") or audit.get("reason", "")),
                fix_scope_reasoning=str(audit.get("fix_scope_reasoning", "") or ""),
                open_review=str(audit.get("open_review", "") or ""),
                runtime_advisory="",
                retry_directives="",
                model=str(model) if model else None,
                duration_ms=duration_ms,
                advisory_flags=advisory_flags,
                session_id=metric_context["session_id"],
                attempt_key=metric_context["attempt_key"],
                generation_method=generation_method,
                prompt_version=prompt_version,
                candidate_key=metric_context["candidate_key"],
                content_hash=metric_context["artifact_meta"]["content_hash"],
                artifact_path=metric_context["artifact_meta"]["artifact_path"],
            )
            if hasattr(db, "save_director_selection"):
                try:
                    db.save_director_selection(
                        ep_num=global_arc_no,
                        round_num=attempt + 1,
                        selected_label="",
                        selected_strategy=selected_strategy or generation_method or "",
                        verdict=str(audit.get("decision", "REJECT")),
                        stage=2,
                        score=score,
                        selection_reason=str(audit.get("reason", "")),
                        fix_scope=str(audit.get("fix_scope", "") or ""),
                        advisory_warnings=advisory_flags,
                        attempt_key=metric_context["attempt_key"],
                        candidate_key=metric_context["candidate_key"],
                        content_hash=metric_context["artifact_meta"]["content_hash"],
                        artifact_path=metric_context["artifact_meta"]["artifact_path"],
                        director_thinking=str(audit.get("_director_thinking", "") or ""),
                    )
                except Exception as director_selection_err:
                    logging.debug("[director_selections] Stage2 REJECT 기록 실패: %s", director_selection_err)
        except Exception as stage_attempt_err:
            logging.debug("[stage_attempts] Stage2 REJECT 기록 실패 (비치명): %s", stage_attempt_err)

    def _save_stage2_reject_cost_record(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        audit: dict,
        is_patch: bool,
        patch_fallback: bool,
    ) -> None:
        try:
            score = audit.get("score", 0)
            if not isinstance(score, int):
                try:
                    score = int(score)
                except (ValueError, TypeError):
                    score = 0
            self.ctx.current_project.db.save_cost_record(
                session_id=resolve_logging_session_id(
                    getattr(self.ctx, "current_project", None),
                    fallback=f"arc_{global_arc_no}",
                ),
                scope_type="arc",
                scope_id=int(global_arc_no),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage2_reject",
                    "score": score,
                    "attempt": attempt + 1,
                    "generation_method": generation_method,
                    "is_patch": is_patch,
                    "patch_fallback": patch_fallback,
                },
            )
        except (OSError, RuntimeError, TypeError) as exc:
            logging.warning(f"[SilentPass:Stage2RejectMetric] {exc!s:.120}")

    def _record_stage2_reject_side_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        audit: dict,
    ) -> None:
        from modules.core.spinners import V50_MODULES_AVAILABLE

        if V50_MODULES_AVAILABLE and self.ctx.quality_dashboard:
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=global_arc_no,
                    result={
                        "decision": "REJECT",
                        "score": audit.get("score", 0),
                        "violations": [
                            {
                                "type": "director_reject",
                                "description": str(audit.get("reason", ""))[:200],
                            }
                        ],
                        "warnings": [],
                    },
                    stage=2,
                )
            except Exception as dashboard_err:
                logging.debug(f"[SILENT] dashboard metrics (REJECT): {dashboard_err}")

        if self.ctx.stage_rejection_history is not None:
            failure_category = self._extract_failure_category(audit)
            score_breakdown = audit.get("score_breakdown", {})
            if not isinstance(score_breakdown, dict):
                score_breakdown = {}
            self.ctx.stage_rejection_history.append(
                {
                    "stage": 2,
                    "arc_no": global_arc_no,
                    "reason": str(audit.get("reason", "")),
                    "attempt": attempt + 1,
                    "specific_issue": str(audit.get("re_slice_instruction", "") or ""),
                    "failure_category": failure_category or "",
                    "fix_scope": str(audit.get("fix_scope", "") or ""),
                    "score_breakdown": {
                        str(key): value
                        for key, value in list(score_breakdown.items())[:5]
                        if isinstance(value, int | float)
                    },
                }
            )

        if self.ctx.stage2_optimizer:
            try:
                self.ctx.stage2_optimizer.failure_memory.record_failure(
                    arc_no=global_arc_no,
                    failure_type="director_reject",
                    details=str(audit.get("reason", "")),
                )
            except Exception as optimizer_err:
                logging.debug(f"[SILENT] optimizer failure recording: {optimizer_err}")

    def _record_s2_reject_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        selected_strategy: str = "",
        audit: dict,
        duration_ms: int | None = None,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
        artifact_payload: dict | None = None,
    ) -> None:
        """[4-R3-f] Record Stage 2 REJECT metrics (PassRateMonitor, Dashboard, History, Optimizer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        metric_context = self._build_stage2_reject_metric_context(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=selected_strategy,
            artifact_payload=artifact_payload,
        )

        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
            try:
                self.ctx.pass_rate_monitor.record_attempt(
                    stage=2,
                    episode=global_arc_no,
                    arc=global_arc_no,
                    attempt_num=attempt + 1,
                    success=False,
                    reject_reason=str(audit.get("reason", ""))[:100],
                    generation_method=generation_method,
                    duration_ms=duration_ms or 0,
                    token_cost=metric_context["token_cost"],
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                    attempt_key=metric_context["attempt_key"],
                    final_verdict=str(audit.get("decision", "REJECT")),
                    candidate_key=metric_context["candidate_key"],
                    content_hash=metric_context["artifact_meta"]["content_hash"],
                    artifact_path=metric_context["artifact_meta"]["artifact_path"],
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (reject): {e}")
        self._persist_stage2_reject_attempt_records(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            selected_strategy=selected_strategy,
            audit=audit,
            duration_ms=duration_ms,
            is_patch=is_patch,
            metric_context=metric_context,
        )
        self._save_stage2_reject_cost_record(
            global_arc_no=global_arc_no,
            attempt=attempt,
            generation_method=generation_method,
            audit=audit,
            is_patch=is_patch,
            patch_fallback=patch_fallback,
        )
        self._record_stage2_reject_side_metrics(
            global_arc_no=global_arc_no,
            attempt=attempt,
            audit=audit,
        )

    @staticmethod
    def _extract_failure_category(audit: dict) -> str | None:
        """Best-effort category extraction without fabricating missing fields."""
        if not isinstance(audit, dict):
            return None
        for key in ("error_category", "failure_category", "reject_category"):
            value = audit.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:80]
        contradiction_types = audit.get("contradiction_types")
        if isinstance(contradiction_types, list):
            for item in contradiction_types:
                if isinstance(item, str) and item.strip():
                    return item.strip()[:80]
        return None

    @staticmethod
    def _collect_arc_patch_guard_signals(*, original_arc: dict, patched_arc: dict) -> list[dict]:
        """Return narrow, observational Arc patch signals for post-hoc review."""
        if not isinstance(original_arc, dict) or not isinstance(patched_arc, dict):
            return []

        signals: list[dict] = []

        original_tactical = str(original_arc.get("tactical_doc", "") or "").strip()
        patched_tactical = str(patched_arc.get("tactical_doc", "") or "").strip()
        if original_tactical and not patched_tactical:
            signals.append(
                {
                    "code": "missing_tactical_doc",
                    "detail": "patched tactical_doc is blank",
                }
            )

        dropped_sections: list[str] = []
        type_drift_sections: list[str] = []
        for field in ("state_changes", "joint_docs", "status_shadow", "hybrid_composition"):
            original_value = original_arc.get(field)
            patched_value = patched_arc.get(field)
            if isinstance(original_value, dict) and original_value:
                if field not in patched_arc or not isinstance(patched_value, dict) or not patched_value:
                    dropped_sections.append(field)
            if field in patched_arc and patched_value not in (None, "") and not isinstance(patched_value, dict):
                type_drift_sections.append(f"{field}:{type(patched_value).__name__}")

        if dropped_sections:
            signals.append(
                {
                    "code": "structured_section_dropped",
                    "detail": ", ".join(dropped_sections),
                }
            )
        if type_drift_sections:
            signals.append(
                {
                    "code": "structured_section_type_drift",
                    "detail": ", ".join(type_drift_sections),
                }
            )

        original_arc_no = original_arc.get("arc_no")
        patched_arc_no = patched_arc.get("arc_no")
        if original_arc_no not in (None, "") and patched_arc_no not in (None, "", original_arc_no):
            signals.append(
                {
                    "code": "arc_identity_drift",
                    "detail": f"arc_no {original_arc_no} -> {patched_arc_no}",
                }
            )

        span_detail = Stage2Finalizer._describe_episode_span_signal(patched_arc)
        if span_detail:
            signals.append({"code": "episode_span_inconsistent", "detail": span_detail})

        future_artifact_signal = _detect_episode_start_future_artifact_signal(patched_tactical)
        if future_artifact_signal:
            signals.append(future_artifact_signal)

        return signals

    @staticmethod
    def _describe_episode_span_signal(arc: dict) -> str | None:
        if not isinstance(arc, dict):
            return None
        try:
            ep_start = int(arc.get("ep_start"))
            ep_end = int(arc.get("ep_end"))
            ep_count = int(arc.get("ep_count"))
        except (TypeError, ValueError):
            return "ep_start/ep_end/ep_count not all numeric"
        if ep_end < ep_start:
            return f"ep_end({ep_end}) < ep_start({ep_start})"
        expected_count = (ep_end - ep_start) + 1
        if ep_count != expected_count:
            return f"ep_count({ep_count}) != expected({expected_count})"
        return None

    @staticmethod
    def _merge_patch_guard_signals(audit: dict, signals: list[dict], *, attempt: int) -> dict:
        state = audit.setdefault("patch_guard_signals", {})
        items = state.setdefault("items", [])
        for signal in signals:
            code = str(signal.get("code", "")).strip()
            detail = str(signal.get("detail", "")).strip()
            if not code:
                continue
            items.append({"attempt": int(attempt), "code": code, "detail": detail})
        seen: set[str] = set()
        compact_codes: list[str] = []
        for item in items:
            code = str(item.get("code", "")).strip()
            if code and code not in seen:
                seen.add(code)
                compact_codes.append(code)
        state["count"] = len(items)
        state["codes"] = compact_codes[:5]
        state["attempt"] = int(attempt)
        return state

    @staticmethod
    def _format_patch_guard_signal_notice(signals: list[dict], *, attempt: int) -> str:
        if not signals:
            return ""
        lines = []
        for signal in signals[:4]:
            code = str(signal.get("code", "")).strip()
            detail = str(signal.get("detail", "")).strip()
            if not code:
                continue
            line = f"- {code}"
            if detail:
                line += f": {detail}"
            lines.append(line)
        if not lines:
            return ""
        return (
            "\n\n[S2 Arc patch signals]\n"
            f"attempt={int(attempt)}\n"
            f"{chr(10).join(lines)}\n"
            "These are runtime-observed structural signals for post-hoc review. "
            "They are advisory unless another blocking rule says otherwise."
        )

    @staticmethod
    def _extract_advisory_flags(audit: dict) -> dict | None:
        """Collect advisory-like metadata already available in Director audit output."""
        if not isinstance(audit, dict):
            return None

        flags: dict = {}
        if audit.get("v60_43_api_warning"):
            flags["v60_43_api_warning"] = 1

        contradictions = audit.get("contradictions")
        if isinstance(contradictions, list):
            flags["contradictions_count"] = len(contradictions)

        contradiction_types = audit.get("contradiction_types")
        if isinstance(contradiction_types, list):
            compact_types = [str(t)[:40] for t in contradiction_types[:5] if str(t).strip()]
            if compact_types:
                flags["contradiction_types"] = compact_types

        self_consistency = audit.get("self_consistency")
        if isinstance(self_consistency, dict):
            votes = self_consistency.get("votes")
            pass_votes = self_consistency.get("pass_votes")
            if isinstance(votes, int):
                flags["votes"] = votes
            if isinstance(pass_votes, int):
                flags["pass_votes"] = pass_votes

        patch_pressure = audit.get("patch_pressure")
        if isinstance(patch_pressure, dict):
            if patch_pressure.get("exceeded"):
                flags["patch_pressure_exceeded"] = 1
            count = patch_pressure.get("count")
            if isinstance(count, int):
                flags["patch_pressure_count"] = count

        patch_guard_signals = audit.get("patch_guard_signals")
        if isinstance(patch_guard_signals, dict):
            count = patch_guard_signals.get("count")
            if isinstance(count, int):
                flags["arc_patch_signal_count"] = count
            codes = patch_guard_signals.get("codes")
            if isinstance(codes, list):
                compact_codes = [str(code)[:40] for code in codes[:5] if str(code).strip()]
                if compact_codes:
                    flags["arc_patch_signal_codes"] = compact_codes

        fix_pack = normalize_stage2_fix_pack(audit.get("fix_pack"))
        if fix_pack:
            flags["fix_pack"] = fix_pack

        partial_fix_eval = audit.get("partial_fix_eval")
        if isinstance(partial_fix_eval, dict) and partial_fix_eval:
            flags["partial_fix_eval"] = dict(partial_fix_eval)

        return flags or None
