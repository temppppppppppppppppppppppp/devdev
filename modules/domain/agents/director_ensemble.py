"""
[V64 P2-1] Director EnsembleSelector — 앙상블 선택 전담 모듈

Director God Object 분해의 세 번째 단계.
Blueprint/Manuscript 후보 비교, 선택, 판정을 담당.
Director reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등) 접근.
"""

from dataclasses import dataclass
import json
import logging

from modules.core.constants import ContextLimits, ManuscriptLimits, smart_truncate  # [V64.P4]
from modules.core.prompt_loader import PromptLoader
from modules.core.tactical_utils import extract_episode_tactical
from modules.validation.threshold_helper import _threshold


def _safe_int(value, default=0):
    """LLM 반환값을 안전하게 int로 변환한다."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _prompt_cap(name: str, default: int) -> int:
    """Context cap lookup with sane lower bound."""
    try:
        return max(0, int(_threshold(name, default)))
    except (TypeError, ValueError):
        return default


def _prompt_snippet(text: str, *, cap_name: str, default: int, head_ratio: float = 0.6) -> str:
    """Stage 2/4 prompt snippets preserve both head and tail when trimmed."""
    raw = text if isinstance(text, str) else str(text or "")
    cap = _prompt_cap(cap_name, default)
    if cap <= 0:
        return ""
    head_chars = min(cap, max(0, int(cap * head_ratio)))
    return smart_truncate(raw, max_chars=cap, head_chars=head_chars)


_CANONICAL_SCORE_KEYS = (
    "continuity_contradiction",
    "blueprint_coverage",
    "quality_engagement",
    "length",
    "python_warnings",
)

_NC3_CHECKLIST_KEYS = (
    "numeric_accuracy",
    "arithmetic",
    "title_consistency",
    "scene_overlap",
    "percent_calculation",
    "event_ordering",
    "space_continuity",
    "npc_identity",
    "time_progression",
    "opening_diversity",
    "timeline_arc_consistency",
    "fiction_term_leak",
    "scene_variety",
    "pacing_quality",
    "dialogue_naturalness",
    "pov_discipline",
    "emotional_authenticity",
    "npc_knowledge_boundary",
    "secret_consistency",
    "identity_consistency",
)


def _canonical_score_breakdown(raw: dict | None = None, *, length_score: int = 0) -> dict[str, int]:
    base = {key: 0 for key in _CANONICAL_SCORE_KEYS}
    if isinstance(raw, dict):
        for key in _CANONICAL_SCORE_KEYS:
            base[key] = _safe_int(raw.get(key, base[key]), base[key])
    if length_score:
        base["length"] = _safe_int(length_score, base["length"])
    return base


def _normalize_quality_gate_reasons(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _short_text(value: object, limit: int = 200) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:limit]


def _normalize_python_warning_entries(raw: object, *, limit: int = 4) -> list[dict]:
    if not isinstance(raw, list):
        return []

    entries: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for item in raw:
        if isinstance(item, dict):
            severity = _short_text(item.get("severity", "MINOR"), 16).upper() or "MINOR"
            category = _short_text(item.get("category", "issue"), 40) or "issue"
            message = _short_text(item.get("message") or item.get("issue") or item.get("evidence"), 160)
            focus = _short_text(item.get("focus") or item.get("fix_hint"), 120)
        else:
            severity = "MINOR"
            category = "issue"
            message = _short_text(item, 160)
            focus = ""
        if not message:
            continue
        key = (severity, category, message)
        if key in seen:
            continue
        seen.add(key)
        entry = {"severity": severity, "category": category, "message": message}
        if focus:
            entry["focus"] = focus
        entries.append(entry)
        if len(entries) >= limit:
            break
    return entries


def _format_compare_python_warning_block(meta: dict | None) -> str:
    if not isinstance(meta, dict):
        return ""

    warning_entries = _normalize_python_warning_entries(meta.get("python_warnings", []), limit=3)
    issue_count = _safe_int(meta.get("prevalidation_issue_count", len(warning_entries)), 0)
    quality_risk = bool(meta.get("quality_risk", False) or warning_entries)
    if not warning_entries and not issue_count and not quality_risk:
        return ""

    lines: list[str] = []
    if issue_count:
        lines.append(f"- issue_count: {issue_count}")
    if quality_risk:
        lines.append("- quality_risk: true")
    for entry in warning_entries:
        line = f"- [{entry['severity']}/{entry['category']}] {entry['message']}"
        focus = entry.get("focus", "")
        if focus:
            line += f" | focus: {focus}"
        lines.append(line)
    return "\n".join(lines)


def _collect_compare_candidate_advisories(candidates: list) -> list[dict]:
    advisories: list[dict] = []
    for idx, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            advisories.append({"candidate_index": idx, "quality_risk": False})
            continue
        meta = candidate.get("_ensemble_meta", {})
        if not isinstance(meta, dict):
            meta = {}
        item = {
            "candidate_index": idx,
            "strategy": _short_text(meta.get("strategy", f"candidate_{idx + 1}"), 60),
            "issue_count": _safe_int(meta.get("prevalidation_issue_count", 0), 0),
            "quality_risk": bool(meta.get("quality_risk", False)),
        }
        warning_entries = _normalize_python_warning_entries(meta.get("python_warnings", []), limit=3)
        if warning_entries:
            item["python_warnings"] = warning_entries
            item["quality_risk"] = True
        advisories.append(item)
    return advisories


def _normalize_repair_scope(value: object) -> str:
    scope = str(value or "").strip().lower()
    return scope if scope in {"inplace", "partial", "full"} else "none"


def _normalize_fix_target_kind(value: object) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "entity": "entity_ref",
        "entityref": "entity_ref",
        "named_entity": "entity_ref",
        "phrase": "local_phrase",
        "localphrase": "local_phrase",
        "sentence": "local_sentence",
        "localsentence": "local_sentence",
        "scene": "scene_model",
        "scenelevel": "scene_model",
        "scene_level": "scene_model",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in {"entity_ref", "local_phrase", "local_sentence", "scene_model"} else ""


def _resolve_primary_fix_target_kind(kinds: list[str]) -> str:
    normalized = [_normalize_fix_target_kind(item) for item in kinds]
    cleaned = [item for item in normalized if item]
    if not cleaned:
        return ""
    if "scene_model" in cleaned:
        return "scene_model"
    if "local_sentence" in cleaned:
        return "local_sentence"
    if "local_phrase" in cleaned:
        return "local_phrase"
    return "entity_ref"


def _normalize_fix_pack_list(raw: object, *, limit: int = 5, item_limit: int = 160) -> list[str]:
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(str(item or "").split()).strip()
        if not text:
            continue
        text = text[:item_limit]
        if text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _normalize_fix_pack(raw: object) -> dict:
    payload = raw if isinstance(raw, dict) else {}
    patch_targets = _normalize_fix_pack_list(payload.get("patch_targets"), limit=6, item_limit=80)
    must_fix = _normalize_fix_pack_list(payload.get("must_fix"), limit=6, item_limit=180)
    do_not_regress = _normalize_fix_pack_list(payload.get("do_not_regress"), limit=6, item_limit=180)
    success_condition = _short_text(payload.get("success_condition", ""), limit=220)
    evidence_summary = _short_text(payload.get("evidence_summary", ""), limit=220)

    raw_kinds = payload.get("target_kinds")
    if isinstance(raw_kinds, str):
        raw_kinds = [part.strip() for part in raw_kinds.split(",")]
    elif not isinstance(raw_kinds, list):
        raw_kinds = []
    if payload.get("target_kind"):
        raw_kinds = [payload.get("target_kind"), *raw_kinds]
    target_kinds = []
    for item in raw_kinds:
        kind = _normalize_fix_target_kind(item)
        if kind and kind not in target_kinds:
            target_kinds.append(kind)
    target_kind = _resolve_primary_fix_target_kind(target_kinds)

    normalized = {
        "patch_targets": patch_targets,
        "must_fix": must_fix,
        "do_not_regress": do_not_regress,
        "success_condition": success_condition,
        "target_kind": target_kind,
    }
    if target_kinds:
        normalized["target_kinds"] = target_kinds
    if evidence_summary:
        normalized["evidence_summary"] = evidence_summary

    has_payload = any(
        normalized.get(key)
        for key in (
            "patch_targets",
            "must_fix",
            "do_not_regress",
            "success_condition",
            "target_kind",
            "evidence_summary",
        )
    )
    return normalized if has_payload else {}


def _derive_gate_basis(
    *,
    director_verdict: object,
    final_verdict: object,
    firewall_triggered: bool = False,
) -> str:
    director = str(director_verdict or "").strip().upper()
    final = str(final_verdict or "").strip().upper()
    if firewall_triggered:
        return "continuity_firewall"
    if final == "REJECT" and director in {"PASS", "PASS_WITH_FIX"} and director != final:
        return "quality_floor_fail"
    if final == "PASS":
        return "director_primary_pass"
    if final == "PASS_WITH_FIX":
        return "director_primary_pass_with_fix"
    return "director_primary_reject"


def _normalize_director_prompt_packs(
    *,
    mandatory_context: object = "",
    decision_core: object = "",
    candidate_evidence: object = "",
    reference_appendix: object = "",
) -> dict[str, str]:
    raw_mandatory = str(mandatory_context or "").strip()
    raw_decision_core = str(decision_core or "").strip() or raw_mandatory
    raw_candidate_evidence = str(candidate_evidence or "").strip()
    raw_reference_appendix = str(reference_appendix or "").strip()
    return {
        "decision_core": _prompt_snippet(
            raw_decision_core,
            cap_name="context.director_mandatory_max",
            default=400000,
        ),
        "candidate_evidence": _prompt_snippet(
            raw_candidate_evidence,
            cap_name="context.director_candidate_evidence_max",
            default=220000,
        ),
        "reference_appendix": _prompt_snippet(
            raw_reference_appendix,
            cap_name="context.director_reference_appendix_max",
            default=120000,
        ),
    }


_FIXABLE_FIREWALL_TYPE_TOKENS = {
    "고유명사",
    "이름",
    "이름불일치",
    "이름드리프트",
    "고유명사일관성",
    "propernoun",
    "propername",
    "namedrift",
    "nameconsistency",
    "직급",
    "직함",
    "호칭",
    "rank",
    "title",
    "role",
    "rankdrift",
    "위치명",
    "지명",
    "장소명",
    "장소",
    "locationname",
    "locationdrift",
    "placename",
    "금지표현",
    "금칙표현",
    "fictiontermleak",
    "fictionterm",
    "forbiddenterm",
    "bannedexpression",
}

_FIXABLE_FIREWALL_TEXT_MARKERS = (
    "고유명사",
    "이름",
    "직급",
    "직함",
    "호칭",
    "위치명",
    "지명",
    "장소명",
    "금지 표현",
    "금칙 표현",
    "fiction term",
    "banned expression",
    "proper noun",
    "rank drift",
    "title drift",
)


def _normalize_firewall_token(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("_", "").replace("-", "").replace("/", "")


def _normalize_contradiction_entries(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _compact_contradiction_details(entries: list[dict], *, limit: int = 5) -> list[dict]:
    details: list[dict] = []
    for item in entries[:limit]:
        detail: dict[str, str] = {}
        for key, cap in (
            ("severity", 40),
            ("type", 80),
            ("current_violation", 240),
            ("description", 240),
            ("expected_truth", 240),
            ("fix_suggestion", 200),
        ):
            value = str(item.get(key, "") or "").strip()
            if value:
                detail[key] = value[:cap]
        if detail:
            details.append(detail)
    return details


def _is_fixable_firewall_contradiction(detail: dict) -> bool:
    if not isinstance(detail, dict) or not detail:
        return False

    if _normalize_firewall_token(detail.get("type")) in _FIXABLE_FIREWALL_TYPE_TOKENS:
        return True

    combined = " ".join(
        str(detail.get(key, "") or "")
        for key in ("type", "current_violation", "description", "expected_truth", "fix_suggestion")
    ).lower()
    return any(marker in combined for marker in _FIXABLE_FIREWALL_TEXT_MARKERS)


def _build_contradiction_summary_lines(details: list[dict], *, limit: int = 3) -> list[str]:
    lines: list[str] = []
    for detail in details[:limit]:
        severity = str(detail.get("severity", "") or "").strip().upper() or "ISSUE"
        kind = str(detail.get("type", "") or "모순").strip()
        body = (
            str(detail.get("current_violation", "") or "").strip()
            or str(detail.get("description", "") or "").strip()
            or str(detail.get("expected_truth", "") or "").strip()
        )
        fix = str(detail.get("fix_suggestion", "") or "").strip()
        line = f"[{severity}] {kind}: {body}".strip()
        if fix:
            line = f"{line} -> {fix}"
        lines.append(line)
    return lines


def _classify_firewall_mode(
    *,
    contradictions: list[dict],
    original_verdict: str,
    score: int,
    score_breakdown: dict | None,
) -> tuple[str, str]:
    if original_verdict not in ("PASS", "PASS_WITH_FIX"):
        return "reject", ""
    if score < 80:
        return "reject", ""
    if not contradictions or len(contradictions) > 3:
        return "reject", ""
    continuity_score = _safe_int((score_breakdown or {}).get("continuity_contradiction", 0), 0)
    if continuity_score < 30:
        return "reject", ""
    if not all(_is_fixable_firewall_contradiction(detail) for detail in contradictions):
        return "reject", ""

    type_labels = [
        str(detail.get("type", "") or "").strip() for detail in contradictions if str(detail.get("type", "")).strip()
    ]
    type_summary = ", ".join(dict.fromkeys(type_labels[:3]))
    reason = f"Fixable Contradiction Firewall: local contradiction {len(contradictions)}건"
    if type_summary:
        reason += f" ({type_summary})"
    return "pass_with_fix", reason


def _log_director_frame(
    *,
    stage: str,
    ep_num: int,
    decision: str,
    score: int,
    selected_label: str,
    director_verdict: str = "",
    gate_basis: str = "",
    selection_reason: str = "",
    verdict_reason: str = "",
    comparison_notes: str = "",
    contradictions: list | None = None,
    fix_scope: str = "",
    repair_scope: str = "",
    open_review: str = "",
    thinking: str = "",
) -> None:
    _director_verdict = str(director_verdict or "").strip()
    _gate_basis = str(gate_basis or "").strip()
    _selection_reason = str(selection_reason or "").strip()
    _verdict_reason = str(verdict_reason or "").strip()
    _comparison_notes = str(comparison_notes or "").strip()
    _open_review = str(open_review or "").strip()
    _thinking = str(thinking or "").strip()
    _contradictions = list(contradictions or [])

    logging.info(
        "[DirectorFrame] stage=%s ep=%s verdict=%s director_verdict=%s gate_basis=%s score=%s selected=%s fix_scope=%s repair_scope=%s contradictions=%d",
        stage,
        ep_num,
        decision,
        _director_verdict or "",
        _gate_basis or "",
        score,
        selected_label,
        fix_scope or "",
        repair_scope or "",
        len(_contradictions),
    )
    if _selection_reason:
        logging.info("[DirectorFrame] stage=%s ep=%s selection_reason=%s", stage, ep_num, _selection_reason)
    if _verdict_reason and _verdict_reason != _selection_reason:
        logging.info("[DirectorFrame] stage=%s ep=%s verdict_reason=%s", stage, ep_num, _verdict_reason)
    if _comparison_notes:
        logging.info("[DirectorFrame] stage=%s ep=%s comparison=%s", stage, ep_num, _comparison_notes)
    if _open_review:
        logging.info("[DirectorFrame] stage=%s ep=%s open_review=%s", stage, ep_num, _open_review)
    if _contradictions:
        logging.warning("[DirectorFrame] stage=%s ep=%s contradiction_count=%d", stage, ep_num, len(_contradictions))
        for idx, contradiction in enumerate(_contradictions, 1):
            logging.warning("[DirectorFrame] stage=%s ep=%s contradiction_%d=%s", stage, ep_num, idx, contradiction)
    if _thinking:
        logging.debug("[DirectorThinking] stage=%s ep=%s %s", stage, ep_num, _thinking)


def _apply_candidate_quality_gate(result: dict, quality_flag: dict | None) -> dict:
    if not isinstance(result, dict) or not isinstance(quality_flag, dict) or not quality_flag:
        return result

    decision = str(result.get("decision", "REJECT") or "REJECT")
    score = _safe_int(result.get("score", 0), 0)
    feedback = str(result.get("feedback", "") or "")
    reasons = list(_normalize_quality_gate_reasons(result.get("quality_gate_reasons")))

    score_cap = quality_flag.get("score_cap")
    if isinstance(score_cap, (int, float)):
        score = min(score, int(score_cap))

    reasons.extend(_normalize_quality_gate_reasons(quality_flag.get("reasons")))
    gate_feedback = str(quality_flag.get("feedback", "") or "").strip()

    if quality_flag.get("force_reject"):
        decision = "REJECT"
        if gate_feedback:
            feedback = f"{gate_feedback}\n{feedback}".strip() if feedback else gate_feedback
    elif quality_flag.get("force_pass_with_fix") and decision == "PASS":
        decision = "PASS_WITH_FIX"
        if gate_feedback:
            feedback = f"{gate_feedback}\n{feedback}".strip() if feedback else gate_feedback

    result["decision"] = decision
    result["score"] = score
    result["feedback"] = feedback if decision != "PASS" else ""
    result["quality_gate_triggered"] = bool(
        quality_flag.get("force_reject")
        or quality_flag.get("force_pass_with_fix")
        or isinstance(score_cap, (int, float))
    )
    result["quality_gate_reasons"] = reasons
    return result


def _arc_compare_fallback_result(candidates: list[dict]) -> dict:
    best = candidates[0] if candidates else None
    return {
        "decision": "REJECT",
        "selected_index": 0,
        "selected_arc": best,
        "score": 0,
        "contradictions": [],
        "reason": "Director compare unavailable; retry required",
        "feedback": "Director compare failed before a trustworthy selection was made.",
        "comparison_notes": "Fallback reject (compare failed)",
        "fix_scope": "",
        "fallback_triggered": True,
        "quality_gate_triggered": True,
        "quality_gate_reasons": ["director_compare_fallback"],
    }


@dataclass(frozen=True)
class _EnsembleCandidateEnvelope:
    candidates: list[dict]
    validation_results: list[dict]
    qualified_indices: list[int]
    scm_single_candidate: bool


@dataclass(frozen=True)
class _EnsemblePromptRequest:
    combined_context: str
    stable_context: str
    variable_prompt: str | None
    fallback_prompt: str | None


@dataclass(frozen=True)
class _EnsemblePromptResponse:
    response: str
    prompt_error: bool = False


@dataclass
class _EnsembleSelectionState:
    """Mutable state carrier for quality gate chain.

    Gate-mutated fields: score, firewall_triggered, firewall_fixable,
    firewall_reason, contradiction_details.
    Inputs (set once): selected_letter, selected_idx, selected_candidate,
    original_verdict, pre_firewall_score, score_breakdown_raw,
    contradiction_check, numeric_consistency_review, consistency_checklist,
    v60_97_swapped.
    """

    selected_letter: str
    selected_idx: int
    selected_candidate: dict
    original_verdict: str
    score: int
    pre_firewall_score: int
    score_breakdown_raw: dict
    contradiction_check: dict
    numeric_consistency_review: list
    consistency_checklist: dict
    v60_97_swapped: bool
    firewall_triggered: bool = False
    firewall_fixable: bool = False
    firewall_reason: str = ""
    contradiction_details: list[dict] | None = None


class DirectorEnsembleSelector:
    """
    [V64 P2-1] Director에서 분리된 앙상블 선택 모듈

    담당:
    - compare_and_select_blueprint(): Blueprint 후보 비교 선택
    - select_and_judge_ensemble(): 3개 원고 후보 선택 + PASS/REJECT
    - quick_judge_single(): 냉동인간 Writer용 간소 검토
    """

    def __init__(self, director) -> None:
        """
        Args:
            director: Director 인스턴스 (BaseAgent 상속, ask/extract/escape 접근용)
        """
        self._d = director
        self._prompt_loader = PromptLoader()

    def _normalize_ensemble_candidates(
        self,
        candidates: list,
        validation_results: list,
    ) -> _EnsembleCandidateEnvelope:
        normalized_candidates = list(candidates)
        while len(normalized_candidates) < 3:
            normalized_candidates.append(
                {
                    "strategy": f"fallback_{len(normalized_candidates)}",
                    "strategy_name": "fallback",
                    "manuscript": "",
                    "title": "",
                    "state_updates": {},
                }
            )

        normalized_validation = list(validation_results)
        while len(normalized_validation) < 3:
            normalized_validation.append({"warnings": ["missing candidate"], "focus_points": ["empty candidate"]})

        qualified_indices = [
            idx
            for idx, candidate in enumerate(normalized_candidates)
            if len(candidate.get("manuscript") or "") >= ManuscriptLimits.MIN_LENGTH
        ]
        return _EnsembleCandidateEnvelope(
            candidates=normalized_candidates,
            validation_results=normalized_validation,
            qualified_indices=qualified_indices,
            scm_single_candidate=len(qualified_indices) == 1,
        )

    def _build_ensemble_length_guard_result(self, candidates: list[dict]) -> dict:
        lengths = [len(candidate.get("manuscript", "")) for candidate in candidates]
        best_idx = lengths.index(max(lengths))
        return {
            "selected": ["A", "B", "C"][best_idx],
            "selected_candidate": candidates[best_idx],
            "verdict": "REJECT",
            "director_verdict": "REJECT",
            "final_verdict": "REJECT",
            "original_verdict": "REJECT",
            "gate_basis": "director_primary_reject",
            "repair_scope": "none",
            "score": 30,
            "feedback": {
                "issues": [
                    f"All candidates are below the manuscript length floor: {lengths} (minimum {ManuscriptLimits.MIN_LENGTH} required)"
                ],
                "action_items": [
                    "Expand the manuscript above the minimum length floor.",
                    "Ensure scene-level detail and dramatic beats are materially developed.",
                ],
            },
            "state_updates": candidates[best_idx].get("state_updates", {}),
            "action_items": [f"Length expansion required (minimum {ManuscriptLimits.MIN_LENGTH})."],
            "length_violation": True,
            "selection_reason": f"[length_guard] Chose the longest candidate as fallback ({max(lengths)})",
            "verdict_reason": (
                f"All candidates are below the manuscript length floor: {lengths} "
                f"(minimum {ManuscriptLimits.MIN_LENGTH} required)"
            ),
            "reject_reason": (
                f"All candidates are below the manuscript length floor: {lengths} "
                f"(minimum {ManuscriptLimits.MIN_LENGTH} required)"
            ),
            "score_breakdown": _canonical_score_breakdown(length_score=30),
        }

    def _build_ensemble_prompt_request(
        self,
        *,
        candidates: list[dict],
        validation_results: list[dict],
        blueprint: dict,
        previous_ending: str,
        episode_digest: str,
        mandatory_context: str,
        decision_core: str,
        candidate_evidence: str,
        reference_appendix: str,
        prev_manuscripts_text: str,
        story_context: str,
    ) -> _EnsemblePromptRequest:
        blueprint_str = json.dumps(blueprint, ensure_ascii=False, indent=2) if isinstance(blueprint, dict) else str(blueprint)

        def _candidate_prompt_info(idx: int) -> dict:
            candidate = candidates[idx] if idx < len(candidates) else {}
            validation = validation_results[idx] if idx < len(validation_results) else {}
            return {
                "strategy": candidate.get("strategy_name", candidate.get("strategy", f"candidate{idx + 1}")),
                "manuscript": candidate.get("manuscript", ""),
                "warnings": "\n".join(validation.get("warnings", [])) or "(no warnings)",
            }

        info_a = _candidate_prompt_info(0)
        info_b = _candidate_prompt_info(1)
        info_c = _candidate_prompt_info(2)

        prev_manuscripts = smart_truncate(
            prev_manuscripts_text if prev_manuscripts_text else "(previous manuscripts unavailable)"
        )
        blueprint_esc = self._d._escape_braces(blueprint_str)
        digest_esc = self._d._escape_braces(episode_digest) if episode_digest else "(episode digest unavailable)"
        ending_esc = self._d._escape_braces(previous_ending if previous_ending else "")
        prev_manuscripts_esc = self._d._escape_braces(prev_manuscripts)
        story_context_esc = self._d._escape_braces(story_context) if story_context else "(story context unavailable)"

        prompt_packs = _normalize_director_prompt_packs(
            mandatory_context=mandatory_context,
            decision_core=decision_core,
            candidate_evidence=candidate_evidence,
            reference_appendix=reference_appendix,
        )
        combined_context = "\n\n".join(part for part in prompt_packs.values() if part)
        decision_core_esc = self._d._escape_braces(prompt_packs["decision_core"])
        candidate_evidence_esc = self._d._escape_braces(prompt_packs["candidate_evidence"])
        reference_appendix_esc = self._d._escape_braces(prompt_packs["reference_appendix"])

        stable_context = self._prompt_loader.load(
            "director",
            "ENSEMBLE_STABLE_CONTEXT",
            blueprint=blueprint_esc,
            episode_digest=digest_esc,
            previous_ending=ending_esc,
            prev_manuscripts_text=prev_manuscripts_esc,
            story_context=story_context_esc,
        )
        variable_prompt = (
            self._prompt_loader.load(
                "director",
                "ENSEMBLE_VARIABLE_PROMPT",
                strategy_a=info_a["strategy"],
                manuscript_a=self._d._escape_braces(info_a["manuscript"]),
                warnings_a=self._d._escape_braces(info_a["warnings"]),
                strategy_b=info_b["strategy"],
                manuscript_b=self._d._escape_braces(info_b["manuscript"]),
                warnings_b=self._d._escape_braces(info_b["warnings"]),
                strategy_c=info_c["strategy"],
                manuscript_c=self._d._escape_braces(info_c["manuscript"]),
                warnings_c=self._d._escape_braces(info_c["warnings"]),
                decision_core=decision_core_esc,
                candidate_evidence=candidate_evidence_esc,
                reference_appendix=reference_appendix_esc,
            )
            if stable_context
            else None
        )

        fallback_prompt = None
        if not stable_context or not variable_prompt:
            fallback_prompt = self._prompt_loader.load(
                "director",
                "ENSEMBLE_SELECTION_PROMPT",
                blueprint=blueprint_esc,
                episode_digest=digest_esc,
                previous_ending=ending_esc,
                prev_manuscripts_text=prev_manuscripts_esc,
                story_context=story_context_esc,
                strategy_a=info_a["strategy"],
                manuscript_a=self._d._escape_braces(info_a["manuscript"]),
                warnings_a=self._d._escape_braces(info_a["warnings"]),
                strategy_b=info_b["strategy"],
                manuscript_b=self._d._escape_braces(info_b["manuscript"]),
                warnings_b=self._d._escape_braces(info_b["warnings"]),
                strategy_c=info_c["strategy"],
                manuscript_c=self._d._escape_braces(info_c["manuscript"]),
                warnings_c=self._d._escape_braces(info_c["warnings"]),
                decision_core=decision_core_esc,
                candidate_evidence=candidate_evidence_esc,
                reference_appendix=reference_appendix_esc,
            )

        return _EnsemblePromptRequest(
            combined_context=combined_context,
            stable_context=stable_context or "",
            variable_prompt=variable_prompt,
            fallback_prompt=fallback_prompt,
        )

    def _request_ensemble_selection_response(
        self,
        *,
        ep_num: int,
        prompt_request: _EnsemblePromptRequest,
    ) -> _EnsemblePromptResponse:
        if not prompt_request.stable_context or not prompt_request.variable_prompt:
            if not prompt_request.fallback_prompt:
                logging.warning("[Director] ENSEMBLE_SELECTION_PROMPT not found in prompt loader")
                return _EnsemblePromptResponse(response="", prompt_error=True)
            try:
                response = self._d.ask(prompt_request.fallback_prompt, temperature=0.1, thinking_level="high")
            except Exception as ask_err:
                logging.warning("[Director] select_and_judge_ensemble ask() failed: %s", ask_err)
                response = ""
            return _EnsemblePromptResponse(response=response)

        gate = int(getattr(self._d, "MAX_CONTEXT_CHARS", None) or ContextLimits.MAX_CONTEXT_CHARS)
        stable_budget = max(0, gate - len(prompt_request.variable_prompt) - 2)
        stable_for_fallback = (
            smart_truncate(
                prompt_request.stable_context,
                max_chars=stable_budget,
                head_chars=max(0, min(int(stable_budget * 0.55), stable_budget - 80)),
            )
            if len(prompt_request.stable_context) > stable_budget
            else prompt_request.stable_context
        )
        full_fallback = stable_for_fallback + "\n\n" + prompt_request.variable_prompt

        cache_name = None
        try:
            cache_info = self._d._get_or_create_context_cache(
                cache_type="director_ensemble",
                content=prompt_request.stable_context,
                ttl_seconds=600,
                project_name=self._d._context_cache_project_namespace("ep", ep_num),
            )
            cache_name = cache_info.get("cache_name")
            was_cached = cache_info.get("cached", False)
            logging.info(
                f" [Director-CACHE] {'HIT' if was_cached else 'MISS(new)'}: "
                f"stable={len(prompt_request.stable_context):,} chars / "
                f"variable={len(prompt_request.variable_prompt):,} chars"
            )
        except Exception as cache_err:
            logging.debug(f"[SILENT] director context caching: {cache_err}")

        try:
            if cache_name:
                logging.info(
                    f" [Director] cache route: variable_prompt only ({len(prompt_request.variable_prompt):,} chars)"
                )
                response = self._d._ask_with_cached_context(
                    cache_name=cache_name,
                    prompt=prompt_request.variable_prompt,
                    temperature=0.1,
                    thinking_level="high",
                    full_prompt_fallback=full_fallback,
                )
            else:
                logging.info(f" [Director] fallback route: full prompt ({len(full_fallback):,} chars)")
                response = self._d.ask(full_fallback, temperature=0.1, thinking_level="high")
        except Exception as ask_err:
            logging.warning("[Director] select_and_judge_ensemble ask() failed: %s", ask_err)
            response = ""
        return _EnsemblePromptResponse(response=response)

    def _resolve_ensemble_selection_state(
        self,
        *,
        result: dict,
        candidates: list[dict],
        qualified_indices: list[int],
    ) -> _EnsembleSelectionState:
        selected_letter = str(result.get("selected", "A")).strip().upper()
        selected_idx = {"A": 0, "B": 1, "C": 2}.get(selected_letter, 0)

        v60_97_swapped = False
        if selected_idx not in qualified_indices and qualified_indices:
            old_selection = selected_letter
            selected_idx = max(qualified_indices, key=lambda i: len(candidates[i].get("manuscript", "")))
            selected_letter = ["A", "B", "C"][min(selected_idx, 2)]
            v60_97_swapped = True
            logging.warning(f" [V60.97] LLM 선택 {old_selection} → {selected_letter}로 교체 (분량 기준)")
            original_reason = result.get("selection_reason", "")
            result["selection_reason"] = f"[V60.97 자동 교체: {old_selection}→{selected_letter} (분량 기준)] {original_reason}"

        selected_candidate = candidates[selected_idx] if selected_idx < len(candidates) else candidates[0]
        original_verdict = result.get("verdict", "REJECT")
        score = _safe_int(result.get("score", 50), 50)
        pre_firewall_score = score

        score_breakdown_raw = result.get("score_breakdown", {})
        if isinstance(score_breakdown_raw, dict) and score_breakdown_raw:
            breakdown_sum = sum(v for v in score_breakdown_raw.values() if isinstance(v, int | float))
            if breakdown_sum != score and breakdown_sum > 0:
                _pre_nc3b = score
                logging.warning(
                    "[NC-3B] score_breakdown 합산 불일치: breakdown=%d, score=%d → breakdown 우선",
                    breakdown_sum,
                    score,
                )
                score = max(0, min(100, breakdown_sum))
                if hasattr(self._d, "_operator_log"):
                    self._d._operator_log(
                        f"[NC-3B] 점수 조정: {_pre_nc3b}→{score} (breakdown 합산 우선)",
                        meta={"component": "Director", "event_kind": "score_provenance"},
                    )

        if v60_97_swapped:
            _pre_swap = score
            score = 50
            original_verdict = "CONDITIONAL_PASS"
            if hasattr(self._d, "_operator_log"):
                self._d._operator_log(
                    f"[V60.97] 후보 교체 → 점수 리셋: {_pre_swap}→50, verdict→CONDITIONAL_PASS",
                    meta={"component": "Director", "event_kind": "score_provenance"},
                )

        contradiction_check = result.get("contradiction_check", {})
        if not isinstance(contradiction_check, dict):
            contradiction_check = {}

        numeric_consistency_review = result.get("numeric_consistency_review") or []
        if not isinstance(numeric_consistency_review, list):
            numeric_consistency_review = []

        consistency_checklist = result.get("consistency_checklist") or {}
        if not isinstance(consistency_checklist, dict):
            consistency_checklist = {}

        return _EnsembleSelectionState(
            selected_letter=selected_letter,
            selected_idx=selected_idx,
            selected_candidate=selected_candidate,
            original_verdict=str(original_verdict or "REJECT"),
            score=score,
            pre_firewall_score=pre_firewall_score,
            score_breakdown_raw=score_breakdown_raw if isinstance(score_breakdown_raw, dict) else {},
            contradiction_check=contradiction_check,
            numeric_consistency_review=numeric_consistency_review,
            consistency_checklist=consistency_checklist,
            v60_97_swapped=v60_97_swapped,
            contradiction_details=[],
        )

    def _apply_ensemble_quality_gates(
        self,
        *,
        result: dict,
        state: _EnsembleSelectionState,
        scm_single_candidate: bool,
        combined_context: str,
        mandatory_context: str,
        arc_pos: int,
        total_eps: int,
        retry_count: int,
        ep_type: str = "normal",
    ) -> tuple[str, dict]:
        self._apply_scm_single_candidate_cap(state=state, scm_single_candidate=scm_single_candidate)  # Mutates: state.score
        self._apply_contradiction_firewall_gate(state=state)  # Mutates: state.firewall_triggered/mode/reason, state.contradiction_details
        self._log_numeric_consistency_gate(
            state=state,
            combined_context=combined_context,
            mandatory_context=mandatory_context,
        )
        self._apply_nc3_consistency_penalty(result=result, state=state)  # Mutates: state.score
        return self._resolve_adaptive_ensemble_verdict(  # Mutates: state.score (potentially)
            state=state,
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count,
            ep_type=ep_type,
        )

    def _apply_scm_single_candidate_cap(
        self,
        *,
        state: _EnsembleSelectionState,
        scm_single_candidate: bool,
    ) -> None:
        if not (scm_single_candidate and state.score >= 95):
            return

        scm_old = state.score
        state.score = min(state.score, 90)
        logging.info(f"[SCM] 단일 후보 점수 보정: {scm_old} → {state.score}")
        if hasattr(self._d, "_operator_log"):
            self._d._operator_log(
                f"[SCM] 단일 후보 점수 보정: {scm_old}→{state.score}",
                meta={"component": "Director", "event_kind": "score_provenance"},
            )

    def _apply_contradiction_firewall_gate(
        self,
        *,
        state: _EnsembleSelectionState,
    ) -> None:
        found_contradictions = state.contradiction_check.get("found_contradictions", [])
        if not isinstance(found_contradictions, list) or not found_contradictions:
            return

        normalized_contradictions = _normalize_contradiction_entries(found_contradictions)
        state.contradiction_details = _compact_contradiction_details(normalized_contradictions)
        critical_count = sum(
            1 for item in normalized_contradictions if str(item.get("severity", "")).upper() == "CRITICAL"
        )
        major_count = sum(
            1 for item in normalized_contradictions if str(item.get("severity", "")).upper() == "MAJOR"
        )

        if critical_count >= 1 or major_count >= 2:
            firewall_mode, fixable_reason = _classify_firewall_mode(
                contradictions=state.contradiction_details,
                original_verdict=str(state.original_verdict or ""),
                score=state.score,
                score_breakdown=state.score_breakdown_raw or None,
            )
            selected_manuscript = (
                str(state.selected_candidate.get("manuscript", "") or "")
                if isinstance(state.selected_candidate, dict)
                else ""
            )
            if firewall_mode == "pass_with_fix" and selected_manuscript:
                _pre_fw = state.score
                state.firewall_fixable = True
                state.firewall_reason = fixable_reason
                state.original_verdict = "PASS_WITH_FIX"
                state.score = min(state.score, 97)
                logging.warning(" [V75-C] %s → PASS_WITH_FIX", state.firewall_reason)
                if hasattr(self._d, "_operator_log"):
                    self._d._operator_log(
                        f"[V75-C Firewall] {state.firewall_reason} → PASS_WITH_FIX (점수: {_pre_fw}→{state.score})",
                        meta={"component": "Director", "event_kind": "score_provenance"},
                    )
            else:
                state.firewall_triggered = True
                if critical_count >= 1:
                    state.firewall_reason = f"Contradiction Firewall: CRITICAL {critical_count}건"
                    logging.warning(f" [V75-C] {state.firewall_reason} → REJECT 강제")
                else:
                    state.firewall_reason = f"Contradiction Firewall: MAJOR {major_count}건"
                    logging.warning(f" [V75-C] {state.firewall_reason} → REJECT 강제")

        if state.firewall_triggered:
            state.original_verdict = "REJECT"
            state.pre_firewall_score = state.score
            state.score = min(state.score, 44)
            if hasattr(self._d, "_operator_log"):
                self._d._operator_log(
                    f"[V75-C Firewall] {state.firewall_reason} → REJECT 강제 (점수: {state.pre_firewall_score}→{state.score})",
                    meta={"component": "Director", "event_kind": "score_provenance"},
                )

        if state.firewall_triggered or state.firewall_fixable:
            for line in _build_contradiction_summary_lines(
                state.contradiction_details or [],
                limit=len(state.contradiction_details or []),
            ):
                logging.warning(" %s", line)

    def _log_numeric_consistency_gate(
        self,
        *,
        state: _EnsembleSelectionState,
        combined_context: str,
        mandatory_context: str,
    ) -> None:
        if state.numeric_consistency_review:
            agree_count = 0
            for review in state.numeric_consistency_review:
                if not isinstance(review, dict):
                    continue
                review_verdict = str(review.get("verdict", "")).upper()
                review_id = review.get("id", "?")
                review_reason = str(review.get("reason", ""))
                if review_verdict == "AGREE":
                    agree_count += 1
                    logging.warning("[NC-1] Director AGREE: %s — %s", review_id, review_reason)
                elif review_verdict == "DISMISS":
                    logging.info("[NC-1] Director DISMISS: %s — %s", review_id, review_reason)
                else:
                    logging.warning("[NC-1] Director 미판정: %s (verdict=%s)", review_id, review_verdict)
            if agree_count > 0:
                logging.warning(
                    "[NC-1] Director가 %d건 수치 모순 인정. continuity_contradiction에 직접 반영 여부는 Director 자율.",
                    agree_count,
                )
            return

        merged_context = combined_context or mandatory_context or ""
        if "[NumericConsistency" in merged_context and "[NC-" in merged_context:
            logging.debug("[NC-1] Director가 numeric_consistency_review를 생략함 (선택사항, 감점 없음)")

    def _apply_nc3_consistency_penalty(
        self,
        *,
        result: dict,
        state: _EnsembleSelectionState,
    ) -> None:
        if state.consistency_checklist:
            issue_count = sum(
                1 for key in _NC3_CHECKLIST_KEYS if str(state.consistency_checklist.get(key, "")).upper() == "ISSUE"
            )
            if issue_count > 0:
                logging.warning(
                    "[NC-3] consistency_checklist ISSUE %d건 감지: %s",
                    issue_count,
                    [key for key in _NC3_CHECKLIST_KEYS if str(state.consistency_checklist.get(key, "")).upper() == "ISSUE"],
                )
            if issue_count >= 3 and isinstance(state.score_breakdown_raw, dict):
                python_warnings = state.score_breakdown_raw.get("python_warnings", 10)
                if isinstance(python_warnings, int | float) and python_warnings > 3:
                    _pre_nc3 = state.score
                    logging.info("[NC-3] python_warnings %d → 3 (ISSUE %d건)", python_warnings, issue_count)
                    state.score_breakdown_raw["python_warnings"] = 3
                    new_total = sum(v for v in state.score_breakdown_raw.values() if isinstance(v, int | float))
                    if new_total < state.score:
                        state.score = new_total
                        if hasattr(self._d, "_operator_log"):
                            self._d._operator_log(
                                f"[NC-3] ISSUE {issue_count}건 → python_warnings 감점: {_pre_nc3}→{state.score}",
                                meta={"component": "Director", "event_kind": "score_provenance"},
                            )
            result["score_breakdown"] = state.score_breakdown_raw
            return

        logging.info("[NC-3] Director가 consistency_checklist를 생략함 — 감점 없음 (안정화 기간)")

    def _resolve_adaptive_ensemble_verdict(
        self,
        *,
        state: _EnsembleSelectionState,
        arc_pos: int,
        total_eps: int,
        retry_count: int,
        ep_type: str,
    ) -> tuple[str, dict]:
        try:
            adaptive_result = self._d.apply_adaptive_decision(
                score=state.score,
                original_decision=state.original_verdict,
                arc_pos=arc_pos,
                total_eps=total_eps,
                retry_count=retry_count,
                ep_type=ep_type,
            )
        except Exception as _adp_exc:
            logging.warning("[Q3-T1] apply_adaptive_decision 예외 → 원본 verdict 유지: %s", _adp_exc)
            adaptive_result = {
                "decision": state.original_verdict,
                "adjusted": False,
                "reason": f"grading_error: {_adp_exc}",
            }

        final_verdict = adaptive_result["decision"]
        _adaptive_branch = ""
        if final_verdict == "CONDITIONAL_PASS":
            if state.original_verdict == "REJECT":
                final_verdict = "REJECT"
                _adaptive_branch = "CONDITIONAL_PASS→REJECT (original=REJECT)"
            elif state.v60_97_swapped:
                _v97_threshold = adaptive_result.get("threshold_used", 60)
                if state.score >= _v97_threshold:
                    final_verdict = "PASS"
                    _adaptive_branch = f"CONDITIONAL_PASS→PASS (V60.97 swap, score={state.score}≥threshold={_v97_threshold})"
                else:
                    final_verdict = "REJECT"
                    _adaptive_branch = f"CONDITIONAL_PASS→REJECT (V60.97 swap, score={state.score}<threshold={_v97_threshold})"
            elif adaptive_result.get("adjusted") and state.original_verdict in ("PASS", "PASS_WITH_FIX"):
                final_verdict = state.original_verdict
                _adaptive_branch = f"CONDITIONAL_PASS→{final_verdict} (adjusted pass-through)"
            else:
                final_verdict = "PASS"
                _adaptive_branch = "CONDITIONAL_PASS→PASS (fallback)"

        if _adaptive_branch and hasattr(self._d, "_operator_log"):
            self._d._operator_log(
                f"[Adaptive] {_adaptive_branch}",
                meta={"component": "Director", "event_kind": "verdict_provenance"},
            )

        return final_verdict, adaptive_result

    def _build_ensemble_decision_payload(
        self,
        *,
        ep_num: int,
        result: dict,
        state: _EnsembleSelectionState,
        final_verdict: str,
        adaptive_result: dict,
    ) -> dict:
        feedback = result.get("feedback", {})
        if isinstance(feedback, str):
            feedback = {"issues": [feedback]}
        elif not isinstance(feedback, dict):
            feedback = {}

        selection_reason = str(result.get("selection_reason", "") or "")
        verdict_reason = str(result.get("verdict_reason") or result.get("reject_reason") or "").strip()
        if not verdict_reason and (state.firewall_triggered or state.firewall_fixable) and state.firewall_reason:
            verdict_reason = state.firewall_reason
        if not verdict_reason and isinstance(feedback, dict):
            feedback_issues = feedback.get("issues", []) or []
            if feedback_issues:
                verdict_reason = str(feedback_issues[0])
        if not verdict_reason:
            verdict_reason = selection_reason

        fix_scope = str(result.get("fix_scope", "") or "").strip()
        fix_scope_reasoning = str(result.get("fix_scope_reasoning", "") or "").strip()
        fix_pack = _normalize_fix_pack(result.get("fix_pack"))
        repair_scope = _normalize_repair_scope(fix_scope)
        selected_manuscript = (
            str(state.selected_candidate.get("manuscript", "") or "")
            if isinstance(state.selected_candidate, dict)
            else ""
        )
        contradiction_summary_lines = _build_contradiction_summary_lines(
            state.contradiction_details or [],
            limit=len(state.contradiction_details or []),
        )
        if (state.firewall_triggered or state.firewall_fixable) and selected_manuscript:
            if fix_scope not in ("partial", "full"):
                fix_scope = "inplace"
            if not fix_scope_reasoning:
                fix_scope_reasoning = state.firewall_reason
                if contradiction_summary_lines:
                    fix_scope_reasoning = f"{fix_scope_reasoning}\n" + "\n".join(contradiction_summary_lines)

        if contradiction_summary_lines:
            feedback_issues = [str(item).strip() for item in (feedback.get("issues") or []) if str(item).strip()]
            for line in contradiction_summary_lines:
                issue = f"[Contradiction] {line}"
                if issue not in feedback_issues:
                    feedback_issues.append(issue)
            if feedback_issues:
                feedback["issues"] = feedback_issues

        if state.firewall_fixable:
            action_items = [str(item).strip() for item in (feedback.get("action_items") or []) if str(item).strip()]
            for detail in (state.contradiction_details or []):
                hint = str(detail.get("fix_suggestion", "") or "").strip()
                if not hint:
                    kind = str(detail.get("type", "") or "모순").strip()
                    hint = f"{kind} 항목만 국소 정정하고 나머지 구조는 유지"
                if hint and hint not in action_items:
                    action_items.append(hint)
            if action_items:
                feedback["action_items"] = action_items

        open_review = result.get("open_review", "")
        if state.v60_97_swapped and open_review:
            open_review = f"[V60.97 교체 전 후보 리뷰] {open_review}"
        if open_review and open_review not in ("특이사항 없음", "없음", "") and isinstance(feedback, dict):
            existing_issues = feedback.get("issues", [])
            existing_issues.append(f"[자유 리뷰] {open_review}")
            feedback["issues"] = existing_issues

        logging.info(
            f"[Stage4 Director] 판정: {final_verdict} (점수: {state.score}) 후보{state.selected_letter} | 원래: {state.original_verdict}"
        )
        gate_basis = _derive_gate_basis(
            director_verdict=state.original_verdict,
            final_verdict=final_verdict,
            firewall_triggered=state.firewall_triggered,
        )
        issues = feedback.get("issues", []) if isinstance(feedback, dict) else []
        _log_director_frame(
            stage="stage4",
            ep_num=ep_num,
            decision=final_verdict,
            score=state.score,
            selected_label=str(state.selected_letter),
            director_verdict=str(state.original_verdict or ""),
            gate_basis=gate_basis,
            selection_reason=selection_reason,
            verdict_reason=verdict_reason,
            contradictions=issues,
            fix_scope=fix_scope,
            repair_scope=repair_scope,
            open_review=open_review,
            thinking=getattr(self._d, "_last_thinking", ""),
        )
        operator_lines = [
            f"[Stage4 Director] 원고 앙상블 판정: {final_verdict} (점수: {state.score})",
            f"선택: 후보 {state.selected_letter} | 원래 판정: {state.original_verdict}",
        ]
        if selection_reason:
            operator_lines.append(f"선택 사유: {selection_reason}")
        if verdict_reason and verdict_reason != selection_reason:
            operator_lines.append(f"verdict_reason: {verdict_reason}")
        score_breakdown = _canonical_score_breakdown(result.get("score_breakdown", {}))
        if score_breakdown:
            score_breakdown_str = ", ".join(
                f"{key}={value}" for key, value in score_breakdown.items() if isinstance(value, int | float)
            )
            if score_breakdown_str:
                operator_lines.append(f"점수 분해: {score_breakdown_str}")
        if issues:
            for issue in issues:
                operator_lines.append(f"이슈: {issue!s}")
        if open_review and open_review not in ("특이사항 없음", "없음", ""):
            operator_lines.append(f"자유 리뷰: {open_review}")
        if adaptive_result.get("reason"):
            operator_lines.append(f"적응형: {adaptive_result['reason']}")
        thinking = getattr(self._d, "_last_thinking", "")
        if thinking:
            operator_lines.append(f"💭 [Director Thinking]\n{thinking}")
        for line in operator_lines:
            self._d._operator_log(
                line,
                meta={"component": "Director", "stage": "stage4", "ep_num": ep_num, "score": state.score},
            )

        # ── Verdict-field precedence contract (authoritative return boundary) ──
        # Consumers MUST use these fields in this precedence order:
        #   1. final_verdict  — the durable adjudication after all post-gates
        #   2. verdict        — alias of final_verdict (backward compat)
        #   3. director_verdict / original_verdict — raw upstream Director
        #      result BEFORE post-gates (quality floor, firewall, etc.)
        #   4. gate_basis     — explains WHICH post-gate produced the delta
        #      between original_verdict and final_verdict (empty when equal)
        # All other fields are supplementary context, not adjudication truth.
        return {
            "selected": state.selected_letter,
            "selected_candidate": state.selected_candidate,
            "verdict": final_verdict,
            "director_verdict": state.original_verdict,
            "final_verdict": final_verdict,
            "original_verdict": state.original_verdict,
            "gate_basis": gate_basis,
            "score": state.score,
            "pre_firewall_score": state.pre_firewall_score,
            "score_breakdown": _canonical_score_breakdown(result.get("score_breakdown", {})),
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "reject_reason": verdict_reason,
            "firewall_triggered": state.firewall_triggered,
            "firewall_fixable": state.firewall_fixable,
            "firewall_reason": state.firewall_reason,
            "feedback": feedback,
            "state_updates": result.get("state_updates") or state.selected_candidate.get("state_updates") or {},
            "action_items": feedback.get("action_items", []) if isinstance(feedback, dict) else [],
            "other_candidates_notes": result.get("other_candidates_notes", {}),
            "open_review": open_review,
            "adaptive_threshold": adaptive_result.get("threshold_used", 65),
            "adaptive_reason": adaptive_result.get("reason", ""),
            "repair_scope": repair_scope,
            "error_category": result.get("error_category", ""),
            "fix_scope": fix_scope,
            "fix_scope_reasoning": fix_scope_reasoning,
            "fix_pack": fix_pack,
            "numeric_consistency_review": state.numeric_consistency_review,
            "consistency_checklist": state.consistency_checklist,
            "contradiction_details": state.contradiction_details or [],
            "contradiction_types": [
                item.get("type", "")
                for item in (
                    state.contradiction_check.get("found_contradictions", [])
                    if isinstance(state.contradiction_check, dict)
                    else []
                )
                if isinstance(item, dict)
            ],
            "_director_thinking": thinking,
        }

    def compare_and_select_blueprint(
        self,
        candidates: list,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict = None,
        entity_registry: dict = None,
        state_tracker=None,
    ) -> dict:
        """[V60.85] 여러 Blueprint 후보 중 최적 선택 + PASS/REJECT 판정"""
        if not candidates:
            return {
                "decision": "REJECT",
                "selected_index": -1,
                "selected_blueprint": None,
                "score": 0,
                "reason": "후보 없음",
                "feedback": "Blueprint 후보가 없습니다.",
                "comparison_notes": "",
            }

        if len(candidates) == 1:
            single_result = self._evaluate_single_blueprint(
                candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
            )
            single_result["selected_index"] = 0
            single_result["selected_blueprint"] = candidates[0]
            single_result["comparison_notes"] = "단일 후보"
            return single_result

        logging.info(f" [Director] {len(candidates)}개 후보 비교 중...")
        comparison_prompt = self._build_blueprint_compare_prompt(
            candidates=candidates,
            arc_data=arc_data,
            ep_num=ep_num,
            prev_blueprint=prev_blueprint,
        )
        result = self._request_blueprint_compare_result(
            comparison_prompt=comparison_prompt,
            candidates=candidates,
            arc_data=arc_data,
            ep_num=ep_num,
            prev_blueprint=prev_blueprint,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
        )
        if result.get("selected_blueprint") in candidates:
            return result
        return self._build_blueprint_compare_result_payload(
            result=result,
            candidates=candidates,
            ep_num=ep_num,
        )

    def _evaluate_single_blueprint(
        self, blueprint: dict, arc_data: dict, ep_num: int, prev_blueprint: dict, entity_registry: dict, state_tracker
    ) -> dict:
        """단일 Blueprint 평가 (기존 audit_manuscript 간소화 버전)"""
        integrated = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)

        arc_no = arc_data.get("arc_no", 0) if arc_data else 0

        if state_tracker:
            dead_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, ep_num, arc_no)
            if dead_violations:
                names = [v["npc_name"] for v in dead_violations]
                return {
                    "decision": "REJECT",
                    "score": 20,
                    "reason": f"죽은 NPC 등장: {', '.join(names)}",
                    "feedback": f"사망한 NPC가 등장합니다: {', '.join(names)}. 회상/언급만 허용됩니다.",
                }

        _sb = blueprint.get("scene_breakdown", {})
        scene_count = len(_sb) if isinstance(_sb, dict | list) else 0  # [TF-R2-S3-01]
        if scene_count < 4:
            return {
                "decision": "REJECT",
                "score": 30,
                "pre_firewall_score": 30,
                "firewall_triggered": False,
                "firewall_reason": "",
                "reason": f"씬 개수 부족: {scene_count}개",
                "feedback": "최소 4개 이상의 씬이 필요합니다.",
            }

        if len(integrated) < 800:
            return {
                "decision": "REJECT",
                "score": 40,
                "reason": f"분량 부족: {len(integrated)}자",
                "feedback": "시나리오가 800자 이상이어야 합니다.",
            }

        # [TF-36] Director 주권: 단일 후보라도 LLM 검토 없이 자동 PASS하지 않는다.
        logging.warning(" [대원칙3] _evaluate_single_blueprint: Director LLM 미호출 — fail closed")
        return {
            "decision": "REJECT",
            "score": 55,
            "reason": "Director LLM 미호출 상태의 단일 후보 자동 PASS 금지",
            "feedback": "단일 후보는 Director 비교/재평가 없이 자동 승인할 수 없습니다.",
        }

    def _fallback_first_candidate(
        self, candidates: list, arc_data: dict, ep_num: int, prev_blueprint: dict, entity_registry: dict, state_tracker
    ) -> dict:
        """폴백: 첫 번째 후보 선택 (비교 실패 시)"""
        logging.warning(" [Director] 폴백 - 첫 번째 후보 평가")
        result = self._evaluate_single_blueprint(
            candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
        )
        result["selected_index"] = 0
        result["selected_blueprint"] = candidates[0]
        result["comparison_notes"] = "폴백 선택 (비교 실패)"
        return result

    def _build_blueprint_compare_prompt(
        self,
        *,
        candidates: list[dict],
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict | None,
    ) -> str:
        arc_tactical_ep = extract_episode_tactical(
            arc_data.get("tactical_doc", ""),
            ep_num,
            episode_details=arc_data.get("episode_details"),
        )[:6000]

        prev_ending = ""
        if prev_blueprint:
            prev_ending = prev_blueprint.get("ending_hook", "")
            prev_location = prev_blueprint.get("end_location", "")
            if prev_location:
                prev_ending = f"위치: {prev_location}, 훅: {prev_ending}"

        candidate_summaries = []
        for idx, blueprint in enumerate(candidates):
            meta = blueprint.get("_ensemble_meta", {})
            strategy = meta.get("strategy", f"후보{idx + 1}")
            scene_count = meta.get("scene_count", len(blueprint.get("scene_breakdown", {})))
            length = meta.get("length", len(blueprint.get("integrated_scenario", "")))
            advisory_block = _format_compare_python_warning_block(meta)

            integrated = blueprint.get("integrated_scenario", "")
            if not isinstance(integrated, str):
                integrated = str(integrated) if integrated else ""

            summary = f"""
[후보 {idx + 1}: {strategy}]
- 씬 개수: {scene_count}개
- 분량: {length}자
- 시작 위치: {blueprint.get("start_location", "?")}
- 종료 위치: {blueprint.get("end_location", "?")}
- 시간 흐름: {blueprint.get("time_flow", "?")}
- 엔딩 훅: {str(blueprint.get("ending_hook") or "?")[:100]}
{
                f'''

[Python Advisory]
{advisory_block}
'''
                if advisory_block
                else ""
            }

[시나리오 전문]
{integrated}
"""
            candidate_summaries.append(summary)

        return f"""[Blueprint 비교 선택 + 일관성·모순 판정]

당신은 웹소설 시리즈의 품질 관리 감독입니다.
제{ep_num}화 Blueprint 후보 {len(candidates)}개를 **각각 절대 기준으로 독립 평가**한 뒤, 최적 후보를 선택하고 최종 판정하세요.

### Arc 전술서 (이번 화 기준)
{arc_tactical_ep}

### 이전 화 정보
{prev_ending if prev_ending else "(1화 또는 이전 정보 없음)"}

### 후보 목록
{"".join(candidate_summaries)}

### Python Advisory 해석 원칙
- 위 Python Advisory는 구조/연속성/intent 관련 bounded factual hints다.
- 자동 탈락 규칙이 아니며, 최종 선택/판단 권한은 Director에게 있다.
- 다만 동급 후보라면 unresolved advisory/fidelity risk가 더 적은 후보를 우선하라.

### 🔍 일관성·모순 체크 항목 (각 후보를 아래 항목으로 반드시 검사)
1. **사망·부재 NPC 활동**: 이전 화에서 사망하거나 퇴장한 NPC가 활동하는가?
2. **수치·사실 모순**: 금액, 지분율, 날짜, 회사명, 직함 등 확립된 수치·사실과 충돌하는가?
3. **인물 관계·설정 모순**: 기존에 확립된 인물 관계, 직함, 성격과 다른가?
4. **장소·시간 모순**: 이전 화 종료 위치·상황과 공간적·시간적으로 불가능한 변화가 있는가?
5. **내부 모순**: 시나리오 내 앞뒤 내용이 서로 충돌하는가? (한 씬에서 A를 했는데 다음 씬에서 A를 안 한 것처럼 묘사 등)

### 🚨 즉시 REJECT 조건 (하나라도 해당 시 해당 후보 탈락)
- 모순 체크 항목에서 **명백한 모순이 1건 이상** 발견됨
- Arc 전술서에서 지정한 핵심 사건이 **단 하나도** 반영되지 않음
- 이전 화 종료 위치·상황과 **공간적·시간적 모순** 발생
- 통합 시나리오 **1000자 미만** (서사 밀도 부족)
- 엔딩 훅 **누락** 또는 내용 없음

### 📊 점수 기준 (절대 평가 — 상대 비교 아님)
- **90~100**: 모순 없음 + Arc 핵심 사건 전부 반영 + 연속성 완벽 + 강한 훅
- **80~89**: 모순 없음 + Arc 주요 사건 반영 + 연속성 양호 + 훅 존재
- **70~79**: 경미한 모순 의심 1건 또는 Arc 사건 일부 누락 또는 연속성 어색
- **60~69**: 모순 2건 이상 또는 Arc 사건 절반 이상 누락
- **60 미만**: 반드시 REJECT

⚠️ **핵심 원칙**: 3개 후보 중 상대적으로 가장 낫더라도, **절대 점수 80점 미만이면 REJECT**하세요.

🎯 **[TF-27] 100점 지향 원칙 — 절대 물러서지 마라**
목표는 항상 **100점(모순 0건)**이다. 경미한 모순이라도 그냥 넘기지 마라.
- 국소 수정으로 해결 가능하면 **PASS_WITH_FIX + fix_scope="inplace"** + feedback에 구체적 수정 지시.
- 일부 씬 재구성이 필요하면 **REJECT + fix_scope="partial"**.
- 전면 재설계가 필요하면 **REJECT + fix_scope="full"**.
Architect가 repair loop에서 처리 가능한 범위라면 PASS_WITH_FIX를 사용하되, 그냥 PASS로 흘려보내지는 마라.

### 평가 기준 (가중치)
1. **일관성·모순 없음** (40%): 확립된 사실·수치·관계·설정과 모순이 없는가?
2. **Arc 준수** (35%): 전술서의 이번 화 핵심 사건을 충실히 반영하는가?
3. **연속성** (15%): 이전 화 종료 상태에서 자연스럽게 이어지는가?
4. **다음 화 연결** (10%): 적절한 훅으로 마무리하는가?

### 출력 형식 (JSON)
{{
    "selected_index": 0,
    "decision": "PASS" | "PASS_WITH_FIX" | "REJECT",
    "fix_scope": "inplace" | "partial" | "full",
    "score": 0-100,
    "contradictions": ["모순 설명 (구체적 — 어떤 사실과 무엇이 충돌하는지)", ...],
    "reason": "선택/판정 이유 (50자 이내)",
    "comparison_notes": "후보별 비교 분석 (각 후보의 장단점)",
    "feedback": "PASS_WITH_FIX/REJECT인 경우 구체적 수정 지침",
    "fix_scope_reasoning": "왜 이 수정 범위가 맞는지 근거"
}}

[TF-23] fix_scope: 수정 범위 판단. inplace=국소수정, partial=일부씬재작성, full=전면재설계. PASS 계열은 보통 "inplace".

반드시 유효한 JSON만 출력하세요.
"""

    def _request_blueprint_compare_result(
        self,
        *,
        comparison_prompt: str,
        candidates: list[dict],
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict | None,
        entity_registry: dict | None,
        state_tracker,
    ) -> dict:
        try:
            response = self._d.ask(comparison_prompt, temperature=0.3, thinking_level="high")
            result = self._d._extract_json_robust(response)
            if not isinstance(result, dict):
                logging.warning(" [Director] 비교 응답 파싱 실패")
                return self._fallback_first_candidate(
                    candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
                )
            return result
        except Exception as exc:
            logging.warning(f" [Director] 비교 오류: {str(exc)[:50]}")
            return self._fallback_first_candidate(
                candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
            )

    def _build_blueprint_compare_result_payload(
        self,
        *,
        result: dict,
        candidates: list[dict],
        ep_num: int,
    ) -> dict:
        selected_idx = _safe_int(result.get("selected_index", 0), 0)
        if selected_idx < 0 or selected_idx >= len(candidates):
            selected_idx = 0

        decision = result.get("decision", "PASS")
        score = _safe_int(result.get("score", 70), 70)
        comparison_notes = str(result.get("comparison_notes", ""))
        reason = str(result.get("reason", ""))
        contradictions = result.get("contradictions", [])
        if not isinstance(contradictions, list):
            contradictions = []
        candidate_advisories = _collect_compare_candidate_advisories(candidates)
        selected_candidate_advisory = (
            candidate_advisories[selected_idx]
            if 0 <= selected_idx < len(candidate_advisories)
            else {"candidate_index": selected_idx, "quality_risk": False}
        )
        quality_risk = bool(result.get("quality_risk", False) or selected_candidate_advisory.get("quality_risk", False))
        revision_required = bool(
            result.get("revision_required", False) or decision in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )

        logging.info(f" [Director] 후보 {selected_idx + 1} 선택 ({decision}, 점수: {score})")
        if contradictions:
            logging.warning(f" [Director] 모순 {len(contradictions)}건 발견:")
            for contradiction in contradictions:
                logging.warning(f" {str(contradiction)}")
        else:
            logging.info("✅ [Director] 모순·일관성 이상 없음")
        if comparison_notes:
            logging.info(f" 비교: {comparison_notes}{'...' if len(comparison_notes) > 150 else ''}")
        if reason:
            logging.info(f" 이유: {reason}")

        logging.info(
            f"[Stage3 Director] Blueprint {decision} (점수: {score}) 후보{selected_idx + 1} | {reason if reason else ''}"
        )
        _log_director_frame(
            stage="stage3",
            ep_num=ep_num,
            decision=decision,
            score=score,
            selected_label=str(selected_idx + 1),
            selection_reason=reason,
            verdict_reason=reason,
            comparison_notes=comparison_notes,
            contradictions=contradictions,
            fix_scope=str(result.get("fix_scope", "") or ""),
            thinking=getattr(self._d, "_last_thinking", ""),
        )
        operator_lines = [
            f"[Stage3 Director] Blueprint {decision} (점수: {score})",
            f"선택: 후보 {selected_idx + 1}",
        ]
        if reason:
            operator_lines.append(f"사유: {reason}")
        if comparison_notes:
            operator_lines.append(f"비교: {comparison_notes}")
        if contradictions:
            operator_lines.extend(f"모순: {item!s}" for item in contradictions)
        blueprint_feedback = result.get("feedback", "")
        if decision in ("REJECT", "PASS_WITH_FIX") and blueprint_feedback:
            operator_lines.append(f"피드백: {blueprint_feedback!s}")
        thinking = getattr(self._d, "_last_thinking", "")
        if thinking:
            operator_lines.append(f"💭 [Director Thinking]\n{thinking}")
        if hasattr(self._d, "_operator_log"):
            for line in operator_lines:
                self._d._operator_log(
                    line,
                    meta={"component": "Director", "stage": "stage3", "ep_num": ep_num, "score": score},
                )

        return {
            "decision": decision,
            "selected_index": selected_idx,
            "selected_blueprint": candidates[selected_idx],
            "score": score,
            "contradictions": contradictions,
            "reason": result.get("reason", ""),
            "feedback": result.get("feedback", "") if decision in ("REJECT", "PASS_WITH_FIX") else "",
            "comparison_notes": result.get("comparison_notes", ""),
            "fix_scope": result.get("fix_scope", ""),
            "fix_scope_reasoning": result.get("fix_scope_reasoning", ""),
            "selection_reason": result.get("selection_reason", "") or reason,
            "verdict_reason": result.get("verdict_reason", "") or reason,
            "quality_risk": quality_risk,
            "revision_required": revision_required,
            "candidate_advisories": candidate_advisories,
            "selected_candidate_advisory": selected_candidate_advisory,
            "_director_thinking": thinking,
        }

    # ═══════════════════════════════════════════════════════════════
    # [TF-47] Arc 후보 비교 선택 — Director LLM 비교로 전환
    # ═══════════════════════════════════════════════════════════════

    def _build_arc_compare_prompt(
        self,
        *,
        candidates: list[dict],
        arc_no: int,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        advisory: str,
    ) -> str:
        candidate_summaries = []
        for idx, arc in enumerate(candidates):
            strategy = arc.get("_strategy", f"후보{idx + 1}")
            tactical = arc.get("tactical_doc", "")
            if not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""
            joint = arc.get("joint_docs", {})
            joint_str = json.dumps(joint, ensure_ascii=False) if isinstance(joint, dict) else str(joint) if joint else ""
            state_constraints = arc.get("state_constraints", {})
            state_constraints_str = (
                json.dumps(state_constraints, ensure_ascii=False)
                if isinstance(state_constraints, dict)
                else str(state_constraints) if state_constraints else ""
            )
            state_constraints_prompt = _prompt_snippet(
                state_constraints_str,
                cap_name="context.director_arc_state_constraints_max",
                default=4000,
                head_ratio=0.55,
            )
            joint_prompt = _prompt_snippet(
                joint_str,
                cap_name="context.director_arc_joint_docs_max",
                default=4000,
                head_ratio=0.55,
            )

            ep_count = arc.get("ep_count", "?")
            meta = arc.get("_ensemble_meta", {}) if isinstance(arc.get("_ensemble_meta", {}), dict) else {}
            diversity = meta.get("diversity", {}) if isinstance(meta.get("diversity", {}), dict) else {}
            diversity_warning = str(diversity.get("warning", "") or "").strip()
            summary = (
                f"[후보 {idx + 1}: {strategy}]\n"
                f"- 화수: {ep_count}\n"
                f"- tactical_doc 분량: {len(tactical)}자\n"
                f"- state_constraints: {state_constraints_prompt}\n"
                f"- joint_docs: {joint_prompt}\n"
            )
            if diversity_warning:
                summary += f"- 다양성 경고: {diversity_warning}\n"
            summary += f"\n[tactical_doc 전문]\n{tactical}\n"
            candidate_summaries.append(summary)

        block_summary = ""
        if isinstance(curr_block, dict):
            block_summary = _prompt_snippet(
                json.dumps(curr_block, ensure_ascii=False),
                cap_name="context.director_arc_block_summary_max",
                default=12000,
                head_ratio=0.65,
            )
        prev_arc_prompt = _prompt_snippet(
            prev_arc_context,
            cap_name="context.director_arc_prev_context_max",
            default=24000,
            head_ratio=0.55,
        )
        constraint_prompt = _prompt_snippet(
            constraint_block,
            cap_name="context.director_arc_constraint_max",
            default=12000,
            head_ratio=0.6,
        )
        advisory_prompt = _prompt_snippet(
            advisory,
            cap_name="context.director_arc_advisory_max",
            default=12000,
            head_ratio=0.55,
        )
        logging.info(
            "[CTX-P0-1] arc prompt slices block=%d prev=%d constraint=%d advisory=%d",
            len(block_summary),
            len(prev_arc_prompt),
            len(constraint_prompt),
            len(advisory_prompt),
        )

        return f"""[Arc 후보 비교 선택 + 일관성·모순 판정]

당신은 웹소설 시리즈 Arc 설계 감독입니다.
Arc {arc_no}번 후보 {len(candidates)}개를 **각각 절대 기준으로 독립 평가**한 뒤, 최적 후보를 선택하고 최종 판정하세요.

### 블록 DNA (이번 Arc 원본 설계)
{block_summary}

### 이전 Arc 맥락
{prev_arc_prompt if prev_arc_prompt else "(첫 Arc)"}

### 제약 조건
{constraint_prompt if constraint_prompt else "(없음)"}

### Python 사실 검증 Advisory (NS-3-B)
{advisory_prompt if advisory_prompt else "(없음)"}
- 이 advisory는 수치 비교 기반 사실 검증입니다.
- 큰 수치 괴리 경고가 있으면 PASS를 피하고 PASS_WITH_FIX 또는 REJECT로 판정하세요.

### 후보 목록
{"".join(candidate_summaries)}

### 🔍 일관성·모순 체크 항목 (각 후보를 아래 항목으로 반드시 검사)
1. **사망 NPC 부활**: 이전 Arc에서 사망한 NPC가 활동하는가?
2. **수치·사실 모순**: 내공, 레벨, 금액, 소지품 등 확립된 수치와 충돌하는가?
3. **상태 연속성**: 이전 Arc 종료 상태(위치, 부상, 소지품)에서 자연스럽게 이어지는가?
4. **tactical_doc 밀도**: 화별 전개가 구체적이고 충분한 분량인가?
5. **에피소드 배분**: 화수별 사건이 균형 있게 배분되었는가?
6. **블록 DNA 준수**: treatment 설계의 핵심 사건/복선/감정선이 반영되었는가?

### 🚨 즉시 REJECT 조건 (하나라도 해당 시 해당 후보 탈락)
- 사망 NPC가 활동으로 등장
- 이전 Arc 종료 상태와 명백한 모순
- tactical_doc 분량이 해당 화수 × 500자 미만
- 블록 DNA 핵심 사건 전혀 미반영

### 📊 점수 기준 (절대 평가)
- **90~100**: 모순 없음 + 블록 DNA 핵심 전부 반영 + 상태 연속성 완벽 + 충분한 밀도
- **80~89**: 모순 없음 + 주요 사건 반영 + 연속성 양호 → PASS_WITH_FIX
- **70~79**: 경미한 모순 의심 1건 또는 사건 일부 누락
- **70 미만**: 반드시 REJECT

⚠️ **핵심 원칙**: 후보 중 상대적으로 낫더라도, **절대 점수 80점 미만이면 REJECT**하세요.

🎯 **100점 지향 원칙** — 경미한 모순만 있는 후보 → **PASS_WITH_FIX + fix_scope="inplace"** + feedback에 구체적 수정 지시.

### 평가 기준 (가중치)
1. **일관성·모순 없음** (35%): 확립된 사실·수치·상태와 모순이 없는가?
2. **블록 DNA 준수** (30%): treatment 핵심 사건·복선·감정선 반영도?
3. **서사 밀도** (20%): tactical_doc 구체성, 화별 전개 밀도?
4. **상태 연속성** (15%): 이전 Arc 종료 → 이번 Arc 시작 자연스러움?

### 출력 형식 (JSON)
{{
    "selected_index": 0,
    "decision": "PASS" | "REJECT" | "PASS_WITH_FIX",
    "fix_scope": "inplace" | "partial" | "full",
    "score": 0-100,
    "contradictions": ["모순 설명 (구체적)", ...],
    "reason": "선택/판정 이유 (50자 이내)",
    "comparison_notes": "후보별 비교 분석 (각 후보의 장단점)",
    "feedback": "REJECT/PASS_WITH_FIX인 경우 구체적 수정 지침"
}}

fix_scope: REJECT 시 수정 범위 판단. inplace=국소수정, partial=일부재설계, full=전면재설계. PASS 시 "inplace".

반드시 유효한 JSON만 출력하세요.
"""

    def _request_arc_compare_result(self, *, comparison_prompt: str, candidates: list[dict]) -> dict:
        try:
            response = self._d.ask(comparison_prompt, temperature=0.3, thinking_level="high")
            result = self._d._extract_json_robust(response)
            if not isinstance(result, dict):
                logging.warning(" [TF-47] Arc 비교 응답 파싱 실패 → Python 폴백")
                return _arc_compare_fallback_result(candidates)
            return result
        except Exception as exc:
            logging.warning(f" [TF-47] Arc 비교 오류: {str(exc)[:80]} → Python 폴백")
            return _arc_compare_fallback_result(candidates)

    def _build_arc_compare_result_payload(
        self,
        *,
        result: dict,
        candidates: list[dict],
        arc_no: int,
        candidate_quality_flags: list[dict] | None,
    ) -> dict:
        selected_idx = _safe_int(result.get("selected_index", 0), 0)
        if selected_idx < 0 or selected_idx >= len(candidates):
            selected_idx = 0

        decision = result.get("decision", "REJECT")
        if decision not in ("PASS", "REJECT", "PASS_WITH_FIX"):
            decision = "REJECT"
        score = _safe_int(result.get("score", 70), 70)
        contradictions = result.get("contradictions", [])
        if not isinstance(contradictions, list):
            contradictions = []
        comparison_notes = str(result.get("comparison_notes", ""))
        reason = str(result.get("reason", ""))
        quality_flag = None
        if isinstance(candidate_quality_flags, list) and 0 <= selected_idx < len(candidate_quality_flags):
            quality_flag = candidate_quality_flags[selected_idx]

        logging.info(f" [TF-47] 후보 {selected_idx + 1} 선택 ({decision}, 점수: {score})")
        if contradictions:
            logging.warning(f" [TF-47] 모순 {len(contradictions)}건 발견:")
            for contradiction in contradictions:
                logging.warning(f" {str(contradiction)}")
        else:
            logging.info("✅ [TF-47] 모순·일관성 이상 없음")

        logging.info(
            f"[Stage2 Director] Arc {decision} (점수: {score}) 후보{selected_idx + 1} | {reason if reason else ''}"
        )
        _log_director_frame(
            stage="stage2",
            ep_num=arc_no,
            decision=decision,
            score=score,
            selected_label=f"{selected_idx + 1}:{candidates[selected_idx].get('_strategy', '?')}",
            selection_reason=reason,
            verdict_reason=reason,
            comparison_notes=comparison_notes,
            contradictions=contradictions,
            fix_scope=str(result.get("fix_scope", "") or ""),
            thinking=getattr(self._d, "_last_thinking", ""),
        )
        operator_lines = [
            f"[Stage2 Director] Arc 비교 판정: {decision} (점수: {score})",
            f"선택: 후보 {selected_idx + 1} ({candidates[selected_idx].get('_strategy', '?')})",
        ]
        if reason:
            operator_lines.append(f"사유: {reason}")
        if comparison_notes:
            operator_lines.append(f"비교: {comparison_notes}")
        if contradictions:
            operator_lines.extend(f"모순: {item!s}" for item in contradictions)
        feedback = result.get("feedback", "")
        if decision != "PASS" and feedback:
            operator_lines.append(f"피드백: {feedback!s}")
        thinking = getattr(self._d, "_last_thinking", "")
        if thinking:
            operator_lines.append(f"💭 [Director Thinking]\n{thinking}")
        if hasattr(self._d, "_operator_log"):
            for line in operator_lines:
                self._d._operator_log(
                    line,
                    meta={"component": "Director", "stage": "stage2", "ep_num": arc_no, "score": score},
                )

        final_result = {
            "decision": decision,
            "selected_index": selected_idx,
            "selected_arc": candidates[selected_idx],
            "score": score,
            "contradictions": contradictions,
            "reason": reason,
            "feedback": feedback if decision != "PASS" else "",
            "comparison_notes": comparison_notes,
            "fix_scope": result.get("fix_scope", ""),
            "quality_gate_triggered": False,
            "quality_gate_reasons": [],
            "_director_thinking": thinking,
        }
        return _apply_candidate_quality_gate(final_result, quality_flag)

    def compare_and_select_arc(
        self,
        candidates: list[dict],
        arc_no: int,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str = "",
        advisory: str = "",
        candidate_quality_flags: list[dict] | None = None,
    ) -> dict:
        """[TF-47] Arc 후보 비교 선택 + PASS/REJECT/PASS_WITH_FIX 판정.

        Returns:
            {
                "decision": "PASS" | "REJECT" | "PASS_WITH_FIX",
                "selected_index": int,
                "selected_arc": dict,
                "score": int,
                "contradictions": list,
                "reason": str,
                "feedback": str,
                "comparison_notes": str,
                "fix_scope": str,
            }
        """
        _empty_result = {
            "decision": "REJECT",
            "selected_index": -1,
            "selected_arc": None,
            "score": 0,
            "contradictions": [],
            "reason": "후보 없음",
            "feedback": "Arc 후보가 없습니다.",
            "comparison_notes": "",
            "fix_scope": "",
        }

        if not candidates:
            return _empty_result

        logging.info(
            f" [TF-47] Director Arc {'단독 평가' if len(candidates) == 1 else '비교'}: {len(candidates)}개 후보"
        )
        comparison_prompt = self._build_arc_compare_prompt(
            candidates=candidates,
            arc_no=arc_no,
            curr_block=curr_block,
            prev_arc_context=prev_arc_context,
            constraint_block=constraint_block,
            advisory=advisory,
        )
        result = self._request_arc_compare_result(comparison_prompt=comparison_prompt, candidates=candidates)
        if result.get("selected_arc") in candidates:
            return result
        return self._build_arc_compare_result_payload(
            result=result,
            candidates=candidates,
            arc_no=arc_no,
            candidate_quality_flags=candidate_quality_flags,
        )

    @staticmethod
    def _fallback_arc_selection(candidates: list[dict]) -> dict:
        """[TF-47] LLM 실패 시 Python 폴백 — 첫 번째 후보 PASS 반환."""
        logging.warning(" [TF-47] 폴백 — 첫 번째 후보 선택 (Python)")
        return _arc_compare_fallback_result(candidates)
        best = candidates[0] if candidates else None
        return {
            "decision": "PASS",
            "selected_index": 0,
            "selected_arc": best,
            "score": 75,
            "contradictions": [],
            "reason": "LLM 비교 실패 → Python 폴백 선택",
            "feedback": "",
            "comparison_notes": "폴백 선택 (비교 실패)",
            "fix_scope": "",
        }

    def select_and_judge_ensemble(
        self,
        ep_num: int,
        candidates: list,
        validation_results: list,
        blueprint: dict,
        previous_ending: str,
        arc_pos: int = 1,
        total_eps: int = 5,
        retry_count: int = 0,
        episode_digest: str = "",
        mandatory_context: str = "",
        decision_core: str = "",
        candidate_evidence: str = "",
        reference_appendix: str = "",
        prev_manuscripts_text: str = "",
        story_context: str = "",
        ep_type: str = "normal",
    ) -> dict:
        """[V60.80] 3개 후보 중 최선 선택 + PASS/REJECT 판정"""
        candidate_state = self._normalize_ensemble_candidates(candidates, validation_results)
        candidates = candidate_state.candidates
        validation_results = candidate_state.validation_results
        qualified_indices = candidate_state.qualified_indices
        MIN_MANUSCRIPT_LENGTH = ManuscriptLimits.MIN_LENGTH

        if not qualified_indices:
            logging.warning(f" [V60.97] 모든 후보 분량 미달 (최소 {MIN_MANUSCRIPT_LENGTH}자 기준)")
            return self._build_ensemble_length_guard_result(candidates)

        logging.info(
            f"✅ [V60.97] 분량 통과 후보: {len(qualified_indices)}개 "
            f"({[chr(65 + i) if i < len(candidates) else f'#{i}' for i in qualified_indices]})"
        )

        _scm_single_candidate = candidate_state.scm_single_candidate
        prompt_request = self._build_ensemble_prompt_request(
            candidates=candidates,
            validation_results=validation_results,
            blueprint=blueprint,
            previous_ending=previous_ending,
            episode_digest=episode_digest,
            mandatory_context=mandatory_context,
            decision_core=decision_core,
            candidate_evidence=candidate_evidence,
            reference_appendix=reference_appendix,
            prev_manuscripts_text=prev_manuscripts_text,
            story_context=story_context,
        )
        _combined_context = prompt_request.combined_context
        prompt_response = self._request_ensemble_selection_response(
            ep_num=ep_num,
            prompt_request=prompt_request,
        )
        if prompt_response.prompt_error:
            return {
                "selected": "A",
                "selected_candidate": candidates[0] if candidates else {},
                "verdict": "REJECT",
                "director_verdict": "REJECT",
                "final_verdict": "REJECT",
                "original_verdict": "REJECT",
                "gate_basis": "director_primary_reject",
                "repair_scope": "none",
                "score": 50,
                "feedback": {"issues": ["Prompt loading failed: ENSEMBLE_SELECTION_PROMPT"]},
                "state_updates": (candidates[0].get("state_updates") or {}) if candidates else {},
                "action_items": ["Prompt loader configuration must be fixed."],
                "prompt_error": True,
            }
        result = self._d._extract_json_robust(prompt_response.response)

        if not result or result.get("parsing_error"):
            logging.warning(" [Director] 앙상블 선택 파싱 실패 - 첫 번째 후보 기본 선택")
            return {
                "selected": "A",
                "selected_candidate": candidates[0] if candidates else {},
                "verdict": "REJECT",
                "score": 0,  # [P0-3] 파싱 실패 시 적응형 승격 방지
                "feedback": {"issues": ["Director 판정 파싱 실패"]},
                "state_updates": (candidates[0].get("state_updates") or {})
                if candidates
                else {},  # [TF-R4] LLM null 방어
                "action_items": ["재생성 필요"],
                "parsing_error": True,
                "director_verdict": "REJECT",
                "final_verdict": "REJECT",
                "original_verdict": "REJECT",
                "gate_basis": "director_primary_reject",
                "repair_scope": "none",
            }

        selection_state = self._resolve_ensemble_selection_state(
            result=result,
            candidates=candidates,
            qualified_indices=qualified_indices,
        )
        final_verdict, adaptive_result = self._apply_ensemble_quality_gates(
            result=result,
            state=selection_state,
            scm_single_candidate=_scm_single_candidate,
            combined_context=_combined_context,
            mandatory_context=mandatory_context,
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count,
            ep_type=ep_type,
        )
        return self._build_ensemble_decision_payload(
            ep_num=ep_num,
            result=result,
            state=selection_state,
            final_verdict=final_verdict,
            adaptive_result=adaptive_result,
        )

    def quick_judge_single(
        self, ep_num: int, manuscript: str, blueprint: dict, previous_ending: str, retry_count: int = 0
    ) -> dict:
        """[V60.80] 냉동인간 Writer용 간소 검토"""
        if len(manuscript) < 3500:
            return {"verdict": "REJECT", "score": 20, "reason": f"분량 심각 부족: {len(manuscript)}자 (최소 3,500자)"}

        _manuscript_snippet = _prompt_snippet(
            manuscript,
            cap_name="context.director_emergency_manuscript_max",
            default=6000,
            head_ratio=0.55,
        )
        _blueprint_snippet = _prompt_snippet(
            str(blueprint),
            cap_name="context.director_emergency_blueprint_max",
            default=5000,
            head_ratio=0.55,
        )

        prompt = f"""
[Role] 편집장 (Emergency Review)
[Task] 냉동인간 Writer가 생성한 원고를 빠르게 검토하라.

### 원고 (제{ep_num}화)
{self._d._escape_braces(_manuscript_snippet)}

### Blueprint 요약
{self._d._escape_braces(_blueprint_snippet)}

### 판정 기준 (완화됨)
1. 분량 3,500자 이상: OK
2. 치명적 설정 오류 없음: OK
3. 최소한의 서사 진행: OK

[Output Format] JSON Only
{{
    "verdict": "PASS" 또는 "REJECT",
    "score": 0-100,
    "reason": "판정 사유",
    "critical_issues": ["치명적 문제 (있을 경우)"]
}}
"""

        response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
        result = self._d._extract_json_robust(response)

        if not result or result.get("parsing_error"):
            if len(manuscript) >= 3500:
                return {
                    "verdict": "REJECT",
                    "score": 45,
                    "reason": "간소 검토 파싱 실패 - 분량 충족이나 품질 검증 불가로 REJECT",
                    "forced": True,
                }
            return {"verdict": "REJECT", "score": 30, "reason": "간소 검토 파싱 실패 + 분량 미달"}

        # [G5] critical_issues가 list가 아닐 수 있음 (LLM 응답 안전성)
        _issues = result.get("critical_issues", [])
        if not isinstance(_issues, list):
            _issues = [_issues] if _issues else []

        return {
            "verdict": result.get("verdict", "REJECT"),
            "score": result.get("score", 50),
            "reason": result.get("reason", ""),
            "critical_issues": _issues,
        }
