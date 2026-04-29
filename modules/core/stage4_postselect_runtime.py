"""
Stage4 post-select validation/runtime orchestration split.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.core.final_accepted_context import load_final_accepted_manuscript_row

if TYPE_CHECKING:
    from modules.core.stage4_interview_round import Stage4InterviewRound


_POST_SELECT_QUOTED_TOKEN_RE = re.compile(r"'([^']+)'")
_POST_SELECT_GROUP_TOKEN_RE = re.compile(r"([A-Za-z0-9가-힣]+그룹)")
_POST_SELECT_ASSET_AMOUNT_RE = re.compile(r"(\d[\d,]*(\.\d+){0,1}\s*억(\s*원){0,1}(\s*규모의){0,1}\s*개인 명의 자산)")


def _normalize_post_select_truth_pin_value(value: object) -> str:
    return str(value or "").strip()


def _append_post_select_truth_pin(
    truth_pins: list[dict[str, str]],
    *,
    pin_key: str,
    family: str,
    expected: str,
    observed: str,
    source_line: str,
) -> None:
    normalized_expected = _normalize_post_select_truth_pin_value(expected)
    normalized_observed = _normalize_post_select_truth_pin_value(observed)
    normalized_source = _normalize_post_select_truth_pin_value(source_line)
    if not (pin_key and family and normalized_expected):
        return
    candidate = {
        "pin_key": pin_key,
        "family": family,
        "expected": normalized_expected,
        "observed": normalized_observed,
        "source_line": normalized_source,
    }
    if candidate not in truth_pins:
        truth_pins.append(candidate)


def _extract_post_select_truth_pins(
    *,
    conflicts: list[str] | None,
    contradiction_details: list[str] | None,
) -> list[dict[str, str]]:
    truth_pins: list[dict[str, str]] = []
    for raw_line in list(conflicts or []) + list(contradiction_details or []):
        line = str(raw_line or "").strip()
        if not line:
            continue

        quoted_tokens = [token.strip() for token in _POST_SELECT_QUOTED_TOKEN_RE.findall(line) if token.strip()]
        group_tokens: list[str] = []
        for token in quoted_tokens:
            match = _POST_SELECT_GROUP_TOKEN_RE.search(token)
            if match:
                group_name = match.group(1).strip()
                if group_name and group_name not in group_tokens:
                    group_tokens.append(group_name)
        if len(group_tokens) >= 2:
            _append_post_select_truth_pin(
                truth_pins,
                pin_key="family_group_name",
                family="proper_noun_group",
                expected=group_tokens[0],
                observed=group_tokens[1],
                source_line=line,
            )

        if "개인 명의 자산" not in line:
            continue
        expected = "개인 명의 자산 없음" if "자산이 없" in line else ""
        observed = ""
        observed_match = _POST_SELECT_ASSET_AMOUNT_RE.search(line)
        if observed_match:
            observed = observed_match.group(1).strip()
        elif expected and ("보유" in line or "현금화" in line):
            observed = "개인 명의 자산 보유"
        if expected and observed:
            _append_post_select_truth_pin(
                truth_pins,
                pin_key="protagonist_personal_assets",
                family="asset_state",
                expected=expected,
                observed=observed,
                source_line=line,
            )
    return truth_pins


def _collect_post_select_rewrite_required_reasons(
    *,
    conflict_types: list[str] | None,
    contradiction_types: list[str] | None,
    truth_pins: list[dict[str, str]] | None,
    completed_event_replay: bool = False,
) -> list[str]:
    reasons: list[str] = []
    normalized_conflict_types = {
        str(item or "").strip().lower() for item in (conflict_types or []) if str(item or "").strip()
    }
    normalized_contradiction_types = {
        str(item or "").strip().lower() for item in (contradiction_types or []) if str(item or "").strip()
    }
    if {"continuity", "history"}.issubset(normalized_conflict_types | normalized_contradiction_types):
        reasons.append("dual_conflict_continuity_history")
    if completed_event_replay:
        reasons.append("completed_event_replay")
    if "proper_noun" in normalized_contradiction_types:
        reasons.append("proper_noun_truth_drift")
    for pin in truth_pins or []:
        family = str(pin.get("family", "") or "").strip().lower()
        if family == "proper_noun_group" and "proper_noun_group_truth_drift" not in reasons:
            reasons.append("proper_noun_group_truth_drift")
        elif family == "asset_state" and "asset_state_truth_drift" not in reasons:
            reasons.append("asset_state_truth_drift")
    return reasons


def _should_allow_bounded_post_select_local_fix(
    *,
    conflict_types: list[str] | None,
    contradiction_types: list[str] | None,
    truth_pins: list[dict[str, str]] | None,
    target_kind: str,
    fix_pack_ready: bool,
) -> bool:
    normalized_target_kind = str(target_kind or "").strip().lower()
    if not fix_pack_ready or normalized_target_kind not in {"entity_ref", "local_phrase", "local_sentence"}:
        return False

    rewrite_required_reasons = _collect_post_select_rewrite_required_reasons(
        conflict_types=conflict_types,
        contradiction_types=contradiction_types,
        truth_pins=truth_pins,
        completed_event_replay=False,
    )
    if rewrite_required_reasons:
        return False

    effective_types = {
        str(item or "").strip().lower()
        for item in list(conflict_types or []) + list(contradiction_types or [])
        if str(item or "").strip()
    }
    return bool(effective_types) and effective_types.issubset(
        {
            "continuity",
            "timeline",
            "movement",
            "location",
            "facing",
            "dialogue",
            "opening_action_continuity",
        }
    )


def _build_post_select_conflict_fingerprint(
    *,
    conflict_types: list[str] | None,
    contradiction_types: list[str] | None,
    truth_pins: list[dict[str, str]] | None,
) -> str:
    tags = ["post_select_conflict"]
    normalized_types = sorted(
        {
            str(item or "").strip().lower()
            for item in list(conflict_types or []) + list(contradiction_types or [])
            if str(item or "").strip()
        }
    )
    tags.extend(f"type:{token}" for token in normalized_types)
    for pin in truth_pins or []:
        pin_key = str(pin.get("pin_key", "") or "").strip().lower()
        expected = re.sub(r"\s+", "_", str(pin.get("expected", "") or "").strip().lower())
        observed = re.sub(r"\s+", "_", str(pin.get("observed", "") or "").strip().lower())
        if pin_key and expected:
            tags.append(f"pin:{pin_key}:{expected}->{observed or 'blank'}")
    return "|".join(tags)


def _build_post_select_fix_scope_reasoning(conflict_contract: dict | None) -> str:
    if not isinstance(conflict_contract, dict) or not conflict_contract:
        return ""
    reasons = [
        str(item or "").strip()
        for item in (conflict_contract.get("rewrite_required_reasons") or [])
        if str(item or "").strip()
    ]
    truth_pins = conflict_contract.get("truth_pins") or []
    lines: list[str] = []
    if reasons:
        lines.append("[post-select truth-pin reroute] local patch 금지: " + ", ".join(reasons))
    if conflict_contract.get("completed_event_replay"):
        lines.append(
            "[completed-event replay reroute] 직전/이전 회차에서 이미 완료된 사건을 현재 opening/live action으로 "
            "재연하지 말고 aftermath, consequence, or new transition으로 다시 설계해야 한다."
        )
    if isinstance(truth_pins, list):
        for pin in truth_pins[:4]:
            if not isinstance(pin, dict):
                continue
            pin_key = str(pin.get("pin_key", "") or "").strip()
            expected = str(pin.get("expected", "") or "").strip()
            observed = str(pin.get("observed", "") or "").strip()
            if pin_key and expected:
                lines.append(f"- preserve {pin_key}={expected} (reject drift={observed or 'unknown'})")
    return "\n".join(lines).strip()


def _build_post_select_conflict_contract(
    conflicts: list[str] | None,
    *,
    conflict_types: list[str] | None = None,
    contradiction_types: list[str] | None = None,
    contradiction_details: list[str] | None = None,
    bounded_local_fix_hint: bool = False,
    target_kind: str = "",
    truth_pins: list[dict[str, str]] | None = None,
    conflict_fingerprint: str = "",
    rewrite_required_reasons: list[str] | None = None,
    completed_event_replay: bool = False,
    completed_event_replay_evidence: list[str] | None = None,
) -> dict[str, object]:
    entries: list[dict[str, str]] = []
    if not isinstance(conflicts, list):
        return {}

    for raw_line in conflicts:
        line = str(raw_line or "").strip()
        if not line:
            continue
        if "Continuity" in line:
            conflict_type = "continuity"
        elif "History" in line:
            conflict_type = "history"
        else:
            conflict_type = "check_error"
        detail = line.split("]", 1)[1].strip() if "]" in line else line
        expected_truth = detail.split(":", 1)[1].strip() if ":" in detail else detail
        entries.append(
            {
                "conflict_type": conflict_type,
                "conflict_detail": detail,
                "source_episode": "",
                "expected_truth": expected_truth,
            }
        )

    if not entries:
        return {}

    contract: dict[str, object] = {
        "contract_type": "post_select_conflict",
        "mode": "rewrite_with_best_manuscript_reuse",
        "conflicts": entries,
    }
    normalized_contradiction_types: list[str] = []
    for item in contradiction_types or []:
        token = str(item or "").strip()
        if token and token not in normalized_contradiction_types:
            normalized_contradiction_types.append(token)
    if normalized_contradiction_types:
        contract["contradiction_types"] = normalized_contradiction_types
    normalized_contradiction_details: list[str] = []
    for item in contradiction_details or []:
        line = str(item or "").strip()
        if line and line not in normalized_contradiction_details:
            normalized_contradiction_details.append(line)
    if normalized_contradiction_details:
        contract["contradiction_details"] = normalized_contradiction_details
    normalized_target_kind = str(target_kind or "").strip().lower()
    if normalized_target_kind:
        contract["target_kind"] = normalized_target_kind
    if bounded_local_fix_hint:
        contract["bounded_local_fix_hint"] = True
    normalized_truth_pins = [dict(item) for item in truth_pins or [] if isinstance(item, dict)]
    if normalized_truth_pins:
        contract["truth_pins"] = normalized_truth_pins
    normalized_conflict_fingerprint = str(conflict_fingerprint or "").strip()
    if normalized_conflict_fingerprint:
        contract["conflict_fingerprint"] = normalized_conflict_fingerprint
    normalized_rewrite_required_reasons = []
    for item in rewrite_required_reasons or []:
        token = str(item or "").strip()
        if token and token not in normalized_rewrite_required_reasons:
            normalized_rewrite_required_reasons.append(token)
    if normalized_rewrite_required_reasons:
        contract["rewrite_required_reasons"] = normalized_rewrite_required_reasons
    if completed_event_replay:
        contract["completed_event_replay"] = True
        evidence_lines: list[str] = []
        for item in completed_event_replay_evidence or []:
            line = str(item or "").strip()
            if line and line not in evidence_lines:
                evidence_lines.append(line)
        if evidence_lines:
            contract["completed_event_replay_evidence"] = evidence_lines[:5]
    return contract


def _detect_completed_event_replay_contract(
    *,
    conflicts: list[str] | None,
    contradiction_types: list[str] | None,
    contradiction_details: list[str] | None,
) -> tuple[bool, list[str]]:
    type_tokens = {str(item or "").strip().lower() for item in (contradiction_types or []) if str(item or "").strip()}
    if "completed_event_replay" in type_tokens:
        return True, ["contradiction_type=completed_event_replay"]

    evidence: list[str] = []
    completed_markers = (
        "completed_event_replay",
        "completed event",
        "already completed",
        "already resolved",
        "prior event replay",
        "continuity replay",
        "replay",
        "이미 완료",
        "이미 끝난",
        "완료 사건",
        "이전 화",
        "이전 회차",
        "직전 화",
        "중복 묘사",
        "반복",
        "재연",
        "다시",
        "타임라인",
    )
    conflict_markers = ("History Conflict", "Continuity Conflict", "history", "continuity", "[V67")
    for raw_line in list(conflicts or []) + list(contradiction_details or []):
        line = str(raw_line or "").strip()
        if not line:
            continue
        lowered = line.lower()
        has_completed_marker = any(marker.lower() in lowered for marker in completed_markers)
        has_conflict_marker = any(marker.lower() in lowered for marker in conflict_markers)
        if has_completed_marker and has_conflict_marker:
            evidence.append(line[:240])
        elif has_completed_marker and any(token in {"history", "continuity"} for token in type_tokens):
            evidence.append(line[:240])

    return bool(evidence), list(dict.fromkeys(evidence))


def _extract_opening_continuity_pin_metadata(blueprint: dict | None) -> tuple[list[str], list[str]]:
    if not isinstance(blueprint, dict):
        return [], []

    contradiction_types: list[str] = []
    contradiction_details: list[str] = []
    for item in blueprint.get("_continuity_pins") or []:
        if not isinstance(item, dict):
            continue
        pin_type = str(item.get("type", "") or "").strip().lower()
        if pin_type != "opening_action_continuity_pin":
            continue
        if "opening_action_continuity" not in contradiction_types:
            contradiction_types.append("opening_action_continuity")
        before = str(item.get("before", "") or "").strip()
        expected = str(item.get("expected", "") or "").strip()
        observed = str(item.get("observed", "") or "").strip()
        detail_parts = ["opening continuity pin"]
        if before:
            detail_parts.append(f"previous={before}")
        if expected:
            detail_parts.append(f"expected={expected}")
        if observed:
            detail_parts.append(f"observed={observed}")
        detail = " | ".join(detail_parts)
        if detail not in contradiction_details:
            contradiction_details.append(detail)
    return contradiction_types, contradiction_details


def _emit_stage4_ui_log(
    ui,
    message: str,
    *,
    component: str,
    event_kind: str,
    level: str = "warning",
    ep_num: int | None = None,
    round_num: int | None = None,
    meta: dict[str, object] | None = None,
) -> None:
    logger = getattr(ui, "log", None)
    if not callable(logger):
        return
    kwargs: dict[str, object] = {
        "stage": "stage4",
        "component": component,
        "event_kind": event_kind,
        "level": level,
    }
    if ep_num is not None:
        kwargs["ep_num"] = ep_num
    if round_num is not None:
        kwargs["round_num"] = round_num
    if meta:
        kwargs["meta"] = meta
    logger(message, **kwargs)


@dataclass
class _PostSelectConflictClassification:
    conflict_types: list[str]
    has_continuity: bool
    has_history: bool


@dataclass
class _PostSelectContradictionPayload:
    contradiction_types: list[str]
    raw_contradiction_details: list[str]
    compact_contradiction_details: list[str]
    conflict_contract: dict[str, object]


class Stage4PostSelectRuntime:
    """Owns post-select continuity/history downgrade handling for Stage 4."""

    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def build_manuscript_history_for_check(self, prev_manuscripts_text: str, next_ep: int) -> list:
        owner = self.owner
        import re as _re_hist

        history_for_check = []
        for block in str(prev_manuscripts_text or "").split("\n\n---\n\n"):
            match = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\s*", block)
            if match:
                episode = int(match.group(1))
                text = block[match.end() :]
                if text and len(text) > 100:
                    history_for_check.append({"ep_num": episode, "text": text})

        if not history_for_check:
            for prev_ep in range(max(1, next_ep - 30), next_ep):
                try:
                    prev_ms_data = load_final_accepted_manuscript_row(owner.ctx.current_project.db, prev_ep)
                    if prev_ms_data:
                        content = (
                            prev_ms_data.get("content", "") if isinstance(prev_ms_data, dict) else str(prev_ms_data)
                        )
                        if content:
                            history_for_check.append({"ep_num": prev_ep, "text": content})
                except Exception as exc:
                    logging.warning(
                        "[SilentPass:InterviewRound] ep%s history load failed: %s",
                        prev_ep,
                        str(exc)[:100],
                    )

        return history_for_check

    def run_post_select_checks(
        self,
        *,
        verdict: str,
        final_manuscript: str,
        final_state_updates: dict,
        next_ep: int,
        round_num: int,
        round_ctx,
        director_result: dict,
        director_feedback: str,
        score: int,
        error_category: str,
        previous_attempt: dict | None,
        stage4_spinner,
        director_memory_context: str,
    ) -> tuple:
        post_select_conflicts = self._collect_post_select_conflicts(
            final_manuscript=final_manuscript,
            next_ep=next_ep,
            round_ctx=round_ctx,
            stage4_spinner=stage4_spinner,
            director_memory_context=director_memory_context,
        )
        if not post_select_conflicts:
            return verdict, director_feedback, previous_attempt, error_category

        classification = self._classify_post_select_conflicts(post_select_conflicts)
        self._emit_post_select_conflict_logs(
            post_select_conflicts=post_select_conflicts,
            classification=classification,
            next_ep=next_ep,
            round_num=round_num,
        )

        verdict = "REJECT"
        authoritative_fix_scope = str(
            director_result.get("authoritative_fix_scope") or director_result.get("fix_scope") or "full"
        ).strip()
        director_result = self.owner._apply_director_gate_update(
            director_result,
            final_verdict="REJECT",
            gate_basis="post_select_conflict",
            repair_scope="full",
        )
        director_result["authoritative_fix_scope"] = authoritative_fix_scope or "full"
        director_result["fix_scope"] = "full"
        error_category = self._derive_post_select_error_category(classification)
        director_feedback += "\n" + "\n".join(post_select_conflicts)

        contradiction_payload = self._build_post_select_contradiction_payload(
            director_result=director_result,
            round_ctx=round_ctx,
            post_select_conflicts=post_select_conflicts,
            classification=classification,
        )
        previous_attempt = self._build_post_select_previous_attempt(
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            score=score,
            director_result=director_result,
            director_feedback=director_feedback,
            prior_attempt=previous_attempt,
            error_category=error_category,
            classification=classification,
            contradiction_payload=contradiction_payload,
        )
        return verdict, director_feedback, previous_attempt, error_category

    def _collect_post_select_conflicts(
        self,
        *,
        final_manuscript: str,
        next_ep: int,
        round_ctx,
        stage4_spinner,
        director_memory_context: str,
    ) -> list[str]:
        owner = self.owner
        post_select_conflicts: list[str] = []
        prev_manuscripts_text = round_ctx.prev_manuscripts_text
        story_context = round_ctx.story_context
        director_agent = owner.ctx.agents.get("director", None)
        run_continuity = next_ep > 1 and final_manuscript
        run_history = (
            prev_manuscripts_text and final_manuscript and hasattr(director_agent, "check_manuscript_history_conflicts")
        )
        if not (run_continuity or run_history):
            return post_select_conflicts

        stage4_spinner.update_detail(f"Ep {next_ep} · post-select checks (parallel)")
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="postselect") as executor:
            fut_continuity = None
            fut_history = None

            if run_continuity:
                fut_continuity = executor.submit(
                    owner.ctx.agents["director"].check_manuscript_continuity_with_cache,
                    new_manuscript=final_manuscript,
                    ep_num=next_ep,
                    db=owner.ctx.current_project.db,
                    limit=10,
                    story_context=story_context,
                    memory_context=director_memory_context,
                )

            if run_history:
                history_for_check = self.build_manuscript_history_for_check(prev_manuscripts_text, next_ep)
                if history_for_check:
                    fut_history = executor.submit(
                        owner.ctx.agents["director"].check_manuscript_history_conflicts,
                        ep_num=next_ep,
                        current_manuscript=final_manuscript,
                        manuscript_history=history_for_check,
                        use_summary=False,
                        story_context=story_context,
                        memory_context=director_memory_context,
                    )

            if fut_continuity is not None:
                try:
                    continuity_check = fut_continuity.result(timeout=120)
                    if continuity_check.get("decision") == "CONFLICT":
                        conflict_msg = continuity_check.get("summary", "Continuity conflict detected")
                        post_select_conflicts.append(f"[Continuity Conflict] {conflict_msg}")
                        owner.ctx.ui.log(f"   [A-3] Post-select continuity conflict: {conflict_msg}")
                except Exception as exc:
                    logging.warning("[FailClosed:SC:PostSelectContinuity] %s", str(exc)[:100])
                    post_select_conflicts.append(f"[Continuity Check Error] 검증 실패 (fail-closed): {exc!s}")

            if fut_history is not None:
                try:
                    conflict_result = fut_history.result(timeout=120)
                    if conflict_result.get("decision") == "CONFLICT":
                        conflict_msg = conflict_result.get("summary", "History conflict detected")
                        post_select_conflicts.append(f"[V67] History Conflict: {conflict_msg}")
                        owner.ctx.ui.log(f"   [A-3] Post-select history conflict: {conflict_msg}")
                except Exception as exc:
                    logging.warning("[FailClosed:SC:PostSelectHistory] %s", str(exc)[:100])
                    post_select_conflicts.append(f"[History Check Error] 검증 실패 (fail-closed): {exc!s}")

        return post_select_conflicts

    @staticmethod
    def _classify_post_select_conflicts(
        post_select_conflicts: list[str],
    ) -> _PostSelectConflictClassification:
        conflict_types: list[str] = []
        for line in post_select_conflicts:
            if "Continuity" in line:
                conflict_types.append("continuity")
            elif "History" in line:
                conflict_types.append("history")
            else:
                conflict_types.append("check_error")
        return _PostSelectConflictClassification(
            conflict_types=conflict_types,
            has_continuity="continuity" in conflict_types,
            has_history="history" in conflict_types,
        )

    def _emit_post_select_conflict_logs(
        self,
        *,
        post_select_conflicts: list[str],
        classification: _PostSelectConflictClassification,
        next_ep: int,
        round_num: int,
    ) -> None:
        owner = self.owner
        for conflict_detail, conflict_type in zip(post_select_conflicts, classification.conflict_types):
            _emit_stage4_ui_log(
                owner.ctx.ui,
                f"   [TF-3 detail] {conflict_detail}",
                component="post_select_validation",
                event_kind="detail",
                ep_num=next_ep,
                round_num=round_num,
                meta={
                    "conflict_type": conflict_type,
                    "conflict_detail": conflict_detail,
                    "conflict_count": len(post_select_conflicts),
                },
            )
        _emit_stage4_ui_log(
            owner.ctx.ui,
            "   [TF-3] Provisional PASS → REJECT downgrade: "
            f"{len(post_select_conflicts)} post-select conflicts ({', '.join(classification.conflict_types)})",
            component="post_select_validation",
            event_kind="policy",
            ep_num=next_ep,
            round_num=round_num,
            meta={
                "conflict_types": list(classification.conflict_types),
                "conflict_count": len(post_select_conflicts),
                "conflict_details": list(post_select_conflicts),
            },
        )

    @staticmethod
    def _derive_post_select_error_category(
        classification: _PostSelectConflictClassification,
    ) -> str:
        if classification.has_continuity and classification.has_history:
            return "POST_SELECT_CONTINUITY_AND_HISTORY"
        if classification.has_continuity:
            return "POST_SELECT_CONTINUITY_CONFLICT"
        if classification.has_history:
            return "POST_SELECT_HISTORY_CONFLICT"
        return "POST_SELECT_CHECK_ERROR"

    def _build_post_select_contradiction_payload(
        self,
        *,
        director_result: dict,
        round_ctx,
        post_select_conflicts: list[str],
        classification: _PostSelectConflictClassification,
    ) -> _PostSelectContradictionPayload:
        owner = self.owner
        contradiction_types: list[str] = []
        for item in director_result.get("contradiction_types", []):
            token = str(item or "").strip()
            if token and token not in contradiction_types:
                contradiction_types.append(token)

        pin_contradiction_types, pin_contradiction_details = (
            _extract_opening_continuity_pin_metadata(getattr(round_ctx, "blueprint", None))
            if classification.has_continuity
            else ([], [])
        )
        for token in pin_contradiction_types:
            if token not in contradiction_types:
                contradiction_types.append(token)

        raw_contradiction_details = list(director_result.get("contradiction_details", []) or [])
        compact_contradiction_details = owner._compact_contradiction_detail_lines(
            raw_contradiction_details,
            max_items=None,
            line_limit=160,
        )
        for line in pin_contradiction_details:
            if line not in compact_contradiction_details:
                compact_contradiction_details.append(line)
        if not compact_contradiction_details:
            compact_contradiction_details = [
                str(item or "").strip() for item in post_select_conflicts if str(item or "").strip()
            ]

        fix_pack_contract = owner._evaluate_fix_pack_contract(director_result.get("fix_pack"))
        normalized_fix_pack = fix_pack_contract.get("fix_pack", {})
        truth_pins = _extract_post_select_truth_pins(
            conflicts=post_select_conflicts,
            contradiction_details=compact_contradiction_details,
        )
        completed_event_replay, completed_event_replay_evidence = _detect_completed_event_replay_contract(
            conflicts=post_select_conflicts,
            contradiction_types=contradiction_types or classification.conflict_types,
            contradiction_details=compact_contradiction_details,
        )
        if completed_event_replay and "completed_event_replay" not in contradiction_types:
            contradiction_types.append("completed_event_replay")
        rewrite_required_reasons = _collect_post_select_rewrite_required_reasons(
            conflict_types=classification.conflict_types,
            contradiction_types=contradiction_types,
            truth_pins=truth_pins,
            completed_event_replay=completed_event_replay,
        )
        conflict_fingerprint = _build_post_select_conflict_fingerprint(
            conflict_types=classification.conflict_types,
            contradiction_types=contradiction_types,
            truth_pins=truth_pins,
        )
        conflict_contract = _build_post_select_conflict_contract(
            post_select_conflicts,
            conflict_types=classification.conflict_types,
            contradiction_types=contradiction_types,
            contradiction_details=compact_contradiction_details,
            bounded_local_fix_hint=_should_allow_bounded_post_select_local_fix(
                conflict_types=classification.conflict_types,
                contradiction_types=contradiction_types,
                truth_pins=truth_pins,
                target_kind=str(normalized_fix_pack.get("target_kind", "") or ""),
                fix_pack_ready=bool(fix_pack_contract.get("ready")),
            ),
            target_kind=str(normalized_fix_pack.get("target_kind", "") or ""),
            truth_pins=truth_pins,
            conflict_fingerprint=conflict_fingerprint,
            rewrite_required_reasons=rewrite_required_reasons,
            completed_event_replay=completed_event_replay,
            completed_event_replay_evidence=completed_event_replay_evidence,
        )

        if contradiction_types:
            director_result["contradiction_types"] = list(contradiction_types)
        elif classification.conflict_types:
            director_result["contradiction_types"] = list(dict.fromkeys(classification.conflict_types))
        if raw_contradiction_details:
            director_result["contradiction_details"] = list(raw_contradiction_details)
        elif compact_contradiction_details:
            director_result["contradiction_details"] = list(compact_contradiction_details)

        return _PostSelectContradictionPayload(
            contradiction_types=contradiction_types,
            raw_contradiction_details=raw_contradiction_details,
            compact_contradiction_details=compact_contradiction_details,
            conflict_contract=conflict_contract,
        )

    def _build_post_select_previous_attempt(
        self,
        *,
        final_manuscript: str,
        final_state_updates: dict,
        score: int,
        director_result: dict,
        director_feedback: str,
        prior_attempt: dict | None,
        error_category: str,
        classification: _PostSelectConflictClassification,
        contradiction_payload: _PostSelectContradictionPayload,
    ) -> dict:
        owner = self.owner
        authoritative_fix_scope = str(
            director_result.get("authoritative_fix_scope") or director_result.get("fix_scope") or ""
        )
        selected_candidate = director_result.get("selected_candidate") or {}
        if not isinstance(selected_candidate, dict):
            selected_candidate = {}
        selected_strategy_key = selected_candidate.get("strategy", "") or selected_candidate.get("strategy_name", "")
        selection_reason = str(director_result.get("selection_reason", "") or "")
        verdict_reason = str(director_result.get("verdict_reason", "") or "")

        previous_attempt = {
            "best_manuscript": final_manuscript,
            "state_updates": final_state_updates,
            "score": score,
            "fix_scope": "full",
            "authoritative_fix_scope": authoritative_fix_scope,
            "rejection_reason": director_feedback,
            "selected_strategy": director_result.get("selected_strategy", ""),
            "selected_strategy_key": selected_strategy_key,
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "director_verdict": director_result.get("director_verdict", ""),
            "final_verdict": director_result.get("final_verdict", "REJECT"),
            "runtime_route_payload_version": director_result.get("runtime_route_payload_version", ""),
            "runtime_route_verdict": director_result.get("runtime_route_verdict", ""),
            "runtime_route_action": director_result.get("runtime_route_action", ""),
            "runtime_route_reason": director_result.get("runtime_route_reason", ""),
            "runtime_route_taxonomy": director_result.get("runtime_route_taxonomy", ""),
            "gate_basis": director_result.get("gate_basis", "post_select_conflict"),
            "repair_scope": director_result.get("repair_scope", "full"),
            "reject_bucket": "post_select_conflict",
            "retry_pathology_source": "post_select_conflict",
            "provisional_pass_downgrade": True,
            "score_breakdown": director_result.get("score_breakdown", {}),
            "consistency_checklist": director_result.get("consistency_checklist", {}),
            "error_category": error_category,
            "open_review": director_result.get("open_review", ""),
            "fix_pack": owner._build_fix_pack_payload(director_result),
            "action_items": list(director_result.get("action_items", []) or []),
            "prior_attempts": owner._inherit_attempt_history(prior_attempt),
        }
        if contradiction_payload.contradiction_types:
            previous_attempt["contradiction_types"] = list(contradiction_payload.contradiction_types)
        elif classification.conflict_types:
            previous_attempt["contradiction_types"] = list(dict.fromkeys(classification.conflict_types))
        if contradiction_payload.raw_contradiction_details:
            previous_attempt["contradiction_details"] = list(contradiction_payload.raw_contradiction_details)
        elif contradiction_payload.compact_contradiction_details:
            previous_attempt["contradiction_details"] = list(contradiction_payload.compact_contradiction_details)
        if contradiction_payload.conflict_contract:
            previous_attempt["conflict_contract"] = contradiction_payload.conflict_contract
            conflict_fingerprint = str(
                contradiction_payload.conflict_contract.get("conflict_fingerprint", "") or ""
            ).strip()
            if conflict_fingerprint:
                previous_attempt["conflict_fingerprint"] = conflict_fingerprint

        previous_attempt["reuse_contract"] = {
            "mode": "best_manuscript_baseline",
            "baseline_field": "best_manuscript",
            "conflict_field": "conflict_contract",
            "preserve_rationale": True,
        }
        previous_attempt["scope_origin"] = {
            "fix_scope": "post_select_conflict_override",
            "authoritative_fix_scope": "director_authoritative",
            "repair_scope": "runtime_lane",
        }

        repair_contract = owner._build_repair_contract_payload_from_parts(
            gate_semantics={
                "repair_scope": str(previous_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(previous_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(previous_attempt.get("scope_origin") or {}),
            },
            fix_pack=previous_attempt.get("fix_pack") or {},
            source=director_result,
        )
        if repair_contract:
            previous_attempt["repair_contract"] = repair_contract

        scope_authority = owner._build_scope_authority_payload_from_parts(
            gate_semantics={
                "repair_scope": str(previous_attempt.get("repair_scope", "") or ""),
                "authoritative_fix_scope": str(previous_attempt.get("authoritative_fix_scope", "") or ""),
                "scope_origin": dict(previous_attempt.get("scope_origin") or {}),
            },
            source=previous_attempt,
        )
        if scope_authority:
            previous_attempt["scope_authority"] = scope_authority

        fix_scope_reasoning = _build_post_select_fix_scope_reasoning(previous_attempt.get("conflict_contract"))
        if fix_scope_reasoning:
            previous_attempt["fix_scope_reasoning"] = fix_scope_reasoning

        return previous_attempt
