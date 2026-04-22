"""
utf8-hygiene: allow-file -- Korean regex patterns in S3-FL/CC/TC prevalidation checks; bounded additions.
[V60.80] Unified Blueprint Validator
Stage 3 사전검사기 + Director 최종 판정

철학:
- "디렉터주권주의" - 최종 결정권은 Director에게 있다
- 사전검사는 Director 호출 전 자가점검 수준

구조:
1. Python 사전검사 (무료, 빠름) - 경고만, REJECT 권한 없음
   - 분량 체크 (integrated_scenario 길이)
   - 필수 필드 체크 (scene_breakdown, integrated_scenario)
   - 정지선 위반 체크 (다음 화 내용 침범)
   - 연속성 체크 (위치, 시간)
   - [V60.96] 죽은 NPC 등장 체크 (CRITICAL 경고 → Director에게 전달)
2. Director 최종 판정 (audit_manuscript)
   - Arc 준수, 서사 개연성, 캐릭터 논리 검증
   - Director의 verdict가 최종 결정
   - [V60.96] 죽은 NPC 경고 포함 시 REJECT 권고
"""

import calendar
import json
import logging
import re
from pathlib import Path

from modules.core.constants import AIModels, Stage2Limits
from modules.core.genre_guards.work_guard import WorkGuardConfigError, load_work_guard_config
from modules.core.partial_fix_contract import normalize_patch_target_records
from modules.core.scene_obligation_heuristics import build_blueprint_scene_profile
from modules.core.stage_cross_stage_contract import (
    apply_opening_transition_contract,
    read_declared_opening_transition_type,
)
from modules.core.tactical_intrusion_contract import collect_tactical_surface_text, detect_tactical_intrusion_signature
from modules.core.tactical_utils import extract_episode_tactical

from .base_agent import _get_agent_default_model

# Blueprint 검증용 최소 분량
BLUEPRINT_MIN_CHARS = 800  # integrated_scenario 최소 길이
_STOP_LINE_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,}")
_STOP_LINE_SPLIT_RE = re.compile(r"[\n;,.!?/]+")
_STOP_LINE_COMMON_TOKENS = {
    "다음",
    "다음화",
    "이번",
    "에피소드",
    "장면",
    "주인공",
    "블루프린트",
    "시나리오",
    "계획",
    "전개",
    "준비",
    "상황",
    "현재",
    "이후",
    "화",
}
_BINDING_PREVALIDATION_CATEGORIES = {
    "scene_completeness",
    "episode_progression",
    "arc_compliance",
    "arc_timeline",
    "capital_unit",
    "dead_npc",
    "fact_lock_item",
    "fact_lock_location",
    "fact_lock_provenance",
    "opening_anchor",
    "mission_clarity",
    "timeline_specificity",
    "protagonist_state",
    "fact_lock_institution",
    "tactical_semantic_fidelity",
    "opening_transition",
    "work_identity_opening",
}
# MAJOR/CRITICAL binding prevalidation issues are structural contract breaches.
# They should never be routed through local faux-inplace repair.
_BINDING_PREVALIDATION_REGENERATE_CATEGORIES = set(_BINDING_PREVALIDATION_CATEGORIES)
# T7.H3 / Tranche 1 sub-edit 1.5: opening_transition alias mismatch는 구조적 binding 위반이
# 아니라 type 라벨만 정규화하면 되는 1-line 수정 가능 케이스이다. 다른 binding category가
# 동시에 firing되지 않고 opening_transition alias가 유일한 binding 위반이면 inplace 허용.
_BINDING_PREVALIDATION_INPLACE_ALIAS_CATEGORIES = frozenset({"opening_transition"})


_TEMPORAL_DEICTIC_RE = re.compile(r"(\d+)\s*(?:년|개월|달|주|일)\s*(?:전|후|뒤)")
_TEMPORAL_MEMORY_RE = re.compile(
    r"(\d+)\s*(?:년|개월)\s*(?:전|후|뒤)"
    r".{0,20}"
    r"(?:기억|회상|추억|떠올리|떠올렸|생각나)"
)
_TEMPORAL_MEMORY_CUES = ("기억", "회상", "추억", "떠올", "생각나")
_TEMPORAL_REGRESSOR_CUES = ("회귀", "전생", "미래 기억", "미래의 기억", "18년 치 기억", "18년 후의 기억")
_SCENARIO_DENSITY_ENTITY_SUFFIXES = (
    "증권",
    "은행",
    "투자",
    "인베스트먼트",
    "회관",
    "사무실",
    "저택",
    "공원",
    "거리",
    "빌딩",
    "호텔",
    "병원",
    "학교",
    "본부",
    "본점",
    "객잔",
    "약방",
    "산장",
    "무관",
    "서재",
    "거실",
    "지점",
    "센터",
    "VIP룸",
)
_DIRECT_OPENING_REENTRY_KR_CUES = (
    "들어온",
    "들어오",
    "들어왔",
    "들어서",
    "들어선",
    "입장",
    "문을 열고 들어",
    "안으로 들어",
    "걸어 들어",
    "따라 들어",
)
_DIRECT_OPENING_REENTRY_EN_CUES = (
    "re-enter",
    "re enters",
    "enter",
    "walk in",
    "walks in",
    "walked in",
    "step in",
    "steps in",
    "stepped in",
    "come in",
    "comes in",
    "came in",
    "arrive",
    "arrives",
    "arrived",
)


def _safe_int(value, default=0):
    """LLM 반환값을 안전하게 int로 변환한다."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _compact_stage3_fix_list(raw: object, *, limit: int = 6, item_limit: int = 180) -> list[str]:
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = list(raw)
    else:
        items = []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(str(item or "").split()).strip()[:item_limit]
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if len(normalized) >= limit:
            break
    return normalized


def _iter_temporal_deictic_truth_strings(*sources: object) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()

    def _walk(value: object, *, depth: int = 0) -> None:
        if depth > 5 or value is None:
            return
        if isinstance(value, str):
            text = " ".join(value.split()).strip()
            if text and text not in seen:
                seen.add(text)
                texts.append(text)
            return
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key or "").strip().lower()
                if key_text in {
                    "integrated_scenario",
                    "scene_breakdown",
                    "ending_hook",
                    "comparison_notes",
                    "feedback",
                }:
                    continue
                _walk(item, depth=depth + 1)
            return
        if isinstance(value, list):
            for item in value[:24]:
                _walk(item, depth=depth + 1)

    for source in sources:
        _walk(source)
    return texts


def _extract_temporal_deictic_allowlist_numbers(*sources: object) -> set[int]:
    allowlist: set[int] = set()
    for text in _iter_temporal_deictic_truth_strings(*sources):
        lowered = text.casefold()
        if not any(marker in lowered for marker in _TEMPORAL_REGRESSOR_CUES):
            continue
        for pattern in (_TEMPORAL_DEICTIC_RE, _TEMPORAL_MEMORY_RE):
            for match in pattern.finditer(text):
                try:
                    allowlist.add(int(match.group(1)))
                except (TypeError, ValueError):
                    continue
    return allowlist


def _is_temporal_deictic_diegetic_anchor(
    *,
    text: str,
    num: int,
    arc_data: dict | None,
    constraint_block: dict | None,
) -> bool:
    if num < 5:
        return False
    lowered = str(text or "").casefold()
    if not any(marker in lowered for marker in _TEMPORAL_MEMORY_CUES):
        return False
    allowlist = _extract_temporal_deictic_allowlist_numbers(arc_data, constraint_block)
    if num in allowlist:
        return True
    # Regressor identity alone is not enough. Large numeric offsets must match an
    # explicit canonical anchor in arc/constraint truth to bypass drift detection.
    return False


def _normalize_stage3_fix_pack(raw_payload: object) -> dict:
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    source = payload.get("fix_pack") if isinstance(payload.get("fix_pack"), dict) else payload
    if not isinstance(source, dict):
        return {}

    target_kind = str(source.get("target_kind") or payload.get("target_kind") or "").strip()
    patch_targets, patch_target_records = normalize_patch_target_records(
        source.get("patch_target_records") or source.get("patch_targets"),
        stage="stage3",
        container_kind="blueprint",
        container_id="stage3_blueprint",
        default_target_kind=target_kind,
    )
    must_fix = _compact_stage3_fix_list(source.get("must_fix"), limit=6, item_limit=180)
    do_not_regress = _compact_stage3_fix_list(source.get("do_not_regress"), limit=6, item_limit=180)
    success_condition = " ".join(str(source.get("success_condition", "") or "").split()).strip()[:220]
    evidence_summary = " ".join(str(source.get("evidence_summary", "") or "").split()).strip()[:220]
    normalized: dict = {}
    if patch_targets:
        normalized["patch_targets"] = patch_targets
    if patch_target_records:
        normalized["patch_target_records"] = patch_target_records
    resolved_target_kind = target_kind or str((patch_target_records or [{}])[0].get("target_kind") or "").strip()
    if resolved_target_kind:
        normalized["target_kind"] = resolved_target_kind
    if must_fix:
        normalized["must_fix"] = must_fix
    if do_not_regress:
        normalized["do_not_regress"] = do_not_regress
    if success_condition:
        normalized["success_condition"] = success_condition
    if evidence_summary:
        normalized["evidence_summary"] = evidence_summary
    return normalized


def _merge_stage3_fix_packs(raw_packs: list[object]) -> dict:
    normalized_packs = [_normalize_stage3_fix_pack(item) for item in list(raw_packs or [])]
    normalized_packs = [item for item in normalized_packs if item]
    if not normalized_packs:
        return {}

    raw_targets: list[object] = []
    must_fix: list[str] = []
    do_not_regress: list[str] = []
    success_conditions: list[str] = []
    evidence_summaries: list[str] = []
    target_kind = ""

    for payload in normalized_packs:
        raw_targets.extend(list(payload.get("patch_target_records") or payload.get("patch_targets") or []))
        must_fix.extend(list(payload.get("must_fix") or []))
        do_not_regress.extend(list(payload.get("do_not_regress") or []))
        success_condition = str(payload.get("success_condition", "") or "").strip()
        if success_condition and success_condition not in success_conditions:
            success_conditions.append(success_condition)
        evidence_summary = str(payload.get("evidence_summary", "") or "").strip()
        if evidence_summary and evidence_summary not in evidence_summaries:
            evidence_summaries.append(evidence_summary)
        if not target_kind:
            target_kind = str(payload.get("target_kind", "") or "").strip()

    patch_targets, patch_target_records = normalize_patch_target_records(
        raw_targets,
        stage="stage3",
        container_kind="blueprint",
        container_id="stage3_blueprint",
        default_target_kind=target_kind,
    )
    merged: dict = {}
    if patch_targets:
        merged["patch_targets"] = patch_targets
    if patch_target_records:
        merged["patch_target_records"] = patch_target_records
    resolved_target_kind = target_kind or str((patch_target_records or [{}])[0].get("target_kind") or "").strip()
    if resolved_target_kind:
        merged["target_kind"] = resolved_target_kind
    compact_must_fix = _compact_stage3_fix_list(must_fix, limit=6, item_limit=180)
    compact_do_not_regress = _compact_stage3_fix_list(do_not_regress, limit=6, item_limit=180)
    if compact_must_fix:
        merged["must_fix"] = compact_must_fix
    if compact_do_not_regress:
        merged["do_not_regress"] = compact_do_not_regress
    if success_conditions:
        merged["success_condition"] = " / ".join(success_conditions[:2])[:220]
    if evidence_summaries:
        merged["evidence_summary"] = " | ".join(evidence_summaries[:2])[:220]
    return merged


class UnifiedBlueprintValidator:
    """
    [V60.80] 통합 Blueprint 검증기

    역할:
    1. Python 사전검사 (무료)
    2. Director 호출 중개 (최종 판정)
    """

    def __init__(self, context, client, model_tier: str = None):
        self.context = context
        self.client = client
        self.model_tier = (
            model_tier or _get_agent_default_model("unified_blueprint_validator") or AIModels.FLASH_ANALYSIS_MODEL
        )
        self.min_chars = BLUEPRINT_MIN_CHARS
        self._work_guard_cache: dict[str, dict] = {}

    def _safe_causal_history(self) -> str:
        """get_causal_history_summary()를 안전하게 호출한다 (DB 오류 시 빈 문자열)."""
        if not hasattr(self.context, "get_causal_history_summary"):
            return ""
        try:
            return str(self.context.get_causal_history_summary())
        except Exception as e:
            logging.warning(f"[S3-P1-2] get_causal_history_summary DB 오류: {e!s:.100}")
            return ""

    def _load_active_work_guard_data(self) -> dict:
        current_project = getattr(self.context, "current_project", None)
        project_paths = getattr(current_project, "paths", None)
        root = getattr(project_paths, "root", None)
        if not isinstance(root, str | Path):
            return {}

        work_guard_path = Path(root) / "config" / "work_guard.yaml"
        cache_key = str(work_guard_path)
        cached = self._work_guard_cache.get(cache_key)
        if cached is not None:
            return cached
        if not work_guard_path.exists():
            self._work_guard_cache[cache_key] = {}
            return {}

        try:
            loaded = load_work_guard_config(work_guard_path)
        except (OSError, WorkGuardConfigError) as exc:
            logging.debug("[Stage3] work_guard load failed during opening doctrine check: %s", exc)
            loaded = {}

        normalized = loaded if isinstance(loaded, dict) else {}
        self._work_guard_cache[cache_key] = normalized
        return normalized

    def _collect_work_identity_opening_issues(
        self,
        *,
        integrated: str,
        scenes: dict,
        scene_count: int,
        working_ep: int,
    ) -> list[dict]:
        if working_ep <= 0 or working_ep > 4 or scene_count < 2 or not isinstance(scenes, dict):
            return []

        work_guard_data = self._load_active_work_guard_data()
        if not isinstance(work_guard_data, dict) or not work_guard_data:
            return []

        work_identity = work_guard_data.get("work_identity", {})
        if not isinstance(work_identity, dict):
            work_identity = {}
        evaluation_contract = work_identity.get("evaluation_contract", {})
        if not isinstance(evaluation_contract, dict):
            evaluation_contract = {}

        contract_fragments = [
            str(work_identity.get("one_line_truth", "") or "").strip(),
            *[str(item or "").strip() for item in work_identity.get("tracking_slots", []) or []],
            *[str(item or "").strip() for item in work_identity.get("mandatory_scene_engines", []) or []],
            *[str(item or "").strip() for item in work_guard_data.get("custom_rules", []) or []],
            *[str(item or "").strip() for item in evaluation_contract.get("episode_loop_contract", []) or []],
            str(evaluation_contract.get("minimum_acceptance_rule", "") or "").strip(),
        ]
        contract_text = " ".join(fragment for fragment in contract_fragments if fragment).casefold()
        if not contract_text:
            return []

        if not all(token in contract_text for token in ("public proof", "private receipt", "next gate")):
            return []
        if not any(token in contract_text for token in ("observer shift", "visible pressure", "execution")):
            return []

        def _scene_text(scene: dict) -> str:
            if not isinstance(scene, dict):
                return ""
            parts = [
                str(scene.get("title", "") or "").strip(),
                str(scene.get("goal", "") or "").strip(),
                str(scene.get("summary", "") or "").strip(),
                str(scene.get("type", "") or "").strip(),
            ]
            key_events = scene.get("key_events", [])
            if isinstance(key_events, list):
                parts.extend(str(item or "").strip() for item in key_events if str(item or "").strip())
            return " ".join(part for part in parts if part)

        def _normalize_location(raw: object) -> str:
            return re.sub(r"\s+", " ", str(raw or "").strip().casefold())

        blueprint_text = " ".join(
            fragment
            for fragment in [
                str(integrated or "").strip(),
                *[_scene_text(scene) for scene in scenes.values() if isinstance(scene, dict)],
            ]
            if fragment
        ).casefold()
        if not blueprint_text:
            return []

        def _has_positive_contract_token(tokens: tuple[str, ...]) -> bool:
            negation_markers = (
                "no ",
                "not ",
                "without ",
                "does not ",
                "did not ",
                "never ",
                "?놁씠",
                "?놁떎",
                "?딆쓬",
                "?꾨땺",
                "?ㅼ쓬",
                "誘몄젙",
                "臾?",
            )
            for token in tokens:
                start = blueprint_text.find(token)
                while start != -1:
                    window_start = max(0, start - 24)
                    window_end = min(len(blueprint_text), start + len(token) + 24)
                    window = blueprint_text[window_start:window_end]
                    if not any(marker in window for marker in negation_markers):
                        return True
                    start = blueprint_text.find(token, start + len(token))
            return False

        unique_locations = {
            _normalize_location(scene.get("location", ""))
            for scene in scenes.values()
            if isinstance(scene, dict) and _normalize_location(scene.get("location", ""))
        }
        receipt_tokens = (
            "private receipt",
            "access shift",
            "seat-equivalent",
            "seat equivalent",
            "seat",
            "access",
            "접근권",
            "응답권",
            "우선 응답권",
            "예외 계좌",
            "명함",
            "라인",
            "pb tone shift",
        )
        observer_shift_tokens = (
            "observer shift",
            "tone shift",
            "gatekeeper",
            "observer",
            "witness",
            "태도 변화",
            "시선 변화",
            "재평가",
            "경외",
            "허용",
        )
        next_gate_tokens = (
            "next gate",
            "next-cycle ticket",
            "next cycle",
            "ticket",
            "signboard",
            "다음 gate",
            "다음 단계",
            "다음 사이클",
            "입장권",
            "후속 연결",
            "다음 연결",
            "사인보드",
        )

        has_receipt = _has_positive_contract_token(receipt_tokens)
        has_observer_shift = _has_positive_contract_token(observer_shift_tokens)
        has_next_gate = _has_positive_contract_token(next_gate_tokens)
        if has_receipt and has_observer_shift and has_next_gate:
            return []

        return [
            {
                "severity": "MAJOR",
                "category": "work_identity_opening",
                "issue": (
                    "opening authority drift: work_guard requires the early loop to move beyond public proof "
                    "into private receipt / observer shift / next gate, but the current blueprint stays under-surfaced"
                ),
                "evidence": (
                    f"ep={working_ep}; unique_locations={len(unique_locations)}; "
                    f"receipt_visible={int(has_receipt)}; observer_shift_visible={int(has_observer_shift)}; "
                    f"next_gate_visible={int(has_next_gate)}"
                ),
                "fix_hint": (
                    "opening scenes must surface at least one private receipt/access-shift beat and one visible "
                    "next gate instead of closing on isolated internal proof only"
                ),
            }
        ]

    def _apply_dead_npc_advisory(
        self,
        pre_result: dict,
        *,
        blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_no: int,
    ) -> list[dict]:
        """Keep dead-NPC checks advisory-only and reusable across compare flows."""
        if not state_tracker or not isinstance(blueprint, dict):
            return []

        dead_npc_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, working_ep, arc_no)
        if not dead_npc_violations:
            return []

        violation_names = [v["npc_name"] for v in dead_npc_violations]
        pre_result.setdefault("issues", []).append(
            {
                "severity": "CRITICAL",
                "category": "dead_npc",
                "issue": f"죽은 NPC 등장: {', '.join(violation_names)}",
                "evidence": dead_npc_violations[0]["reason"],
                "fix_hint": "죽은 NPC는 회상/언급만 허용",
            }
        )
        pre_result["has_critical"] = True
        return dead_npc_violations

    def _build_python_warning_entries(self, issues: list) -> tuple[list[dict], bool]:
        """Compact Python findings so Director sees bounded evidence, not raw dumps."""
        if not isinstance(issues, list):
            return [], False

        entries: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            if issue.get("director_focus") is False or issue.get("advisory_only"):
                continue
            severity = str(issue.get("severity", "MINOR") or "MINOR").upper()
            category = str(issue.get("category", "issue") or "issue").strip()[:40]
            message = str(issue.get("issue") or issue.get("evidence") or "").strip()
            if not message:
                continue
            key = (severity, category, message[:160])
            if key in seen:
                continue
            seen.add(key)
            entry = {
                "source": "python_prevalidate",
                "severity": severity,
                "category": category,
                "message": message[:160],
            }
            focus = str(issue.get("fix_hint", "") or "").strip()
            if focus:
                entry["focus"] = focus[:120]
            entries.append(entry)
            if len(entries) >= 4:
                break

        return entries, bool(entries)

    def _build_advisory_fix_pack(self, issues: list) -> dict:
        if not isinstance(issues, list):
            return {}
        advisory_packs: list[object] = []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            if not (issue.get("advisory_only") or issue.get("director_focus") is False):
                continue
            fix_pack = issue.get("fix_pack")
            if isinstance(fix_pack, dict) and fix_pack:
                advisory_packs.append(fix_pack)
        return _merge_stage3_fix_packs(advisory_packs)

    @staticmethod
    def _build_issue_fix_pack(issues: list) -> dict:
        if not isinstance(issues, list):
            return {}
        issue_packs: list[object] = []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            fix_pack = issue.get("fix_pack")
            if isinstance(fix_pack, dict) and fix_pack:
                issue_packs.append(fix_pack)
        return _merge_stage3_fix_packs(issue_packs)

    @staticmethod
    def _coerce_episode_marker(value: object) -> int | None:
        try:
            marker = int(value)
        except (TypeError, ValueError):
            return None
        return marker if marker > 0 else None

    @staticmethod
    def _relationship_name_variants(name: object) -> set[str]:
        raw = str(name or "").strip()
        if len(raw) < 2:
            return set()

        variants = {raw}
        squashed = re.sub(r"\s+", "", raw)
        if len(squashed) >= 2:
            variants.add(squashed)

        trimmed = re.sub(r"\([^)]*\)", "", raw).strip()
        trimmed = re.sub(r"\s+", " ", trimmed)
        if len(trimmed) >= 2:
            variants.add(trimmed)
            variants.add(re.sub(r"\s+", "", trimmed))

        if len(squashed) >= 3 and re.fullmatch(r"[가-힣]+", squashed):
            variants.add(squashed[-2:])

        return {variant for variant in variants if len(variant) >= 2}

    @classmethod
    def _relationship_visible_in_episode(cls, relationship: object, ep_num: int | None) -> bool:
        if not isinstance(relationship, dict) or not ep_num or ep_num <= 0:
            return True

        for key in ("episode", "ep_num", "ep", "target_episode", "target_ep"):
            marker = cls._coerce_episode_marker(relationship.get(key))
            if marker is not None:
                return marker <= ep_num

        for key in ("visible_from_episode", "start_episode", "from_episode"):
            marker = cls._coerce_episode_marker(relationship.get(key))
            if marker is not None:
                return marker <= ep_num

        return True

    @staticmethod
    def _collect_binding_prevalidation_issues(issues: list[dict]) -> list[dict]:
        if not isinstance(issues, list):
            return []
        binding_issues: list[dict] = []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            category = str(issue.get("category", "") or "").strip()
            severity = str(issue.get("severity", "MINOR") or "MINOR").upper()
            if category not in _BINDING_PREVALIDATION_CATEGORIES:
                continue
            if severity not in {"MAJOR", "CRITICAL"}:
                continue
            binding_issues.append(issue)
        return binding_issues

    @staticmethod
    def _summarize_binding_prevalidation_categories(binding_issues: list[dict]) -> list[str]:
        if not isinstance(binding_issues, list):
            return []
        categories: list[str] = []
        seen: set[str] = set()
        for issue in binding_issues:
            if not isinstance(issue, dict):
                continue
            category = str(issue.get("category", "") or "").strip()
            if not category or category in seen:
                continue
            seen.add(category)
            categories.append(category)
        return categories[:6]

    def _apply_binding_prevalidation_contract(
        self,
        *,
        verdict: str,
        issues: list[dict],
        feedback: str,
        verdict_reason: str,
        fix_scope: str,
        fix_scope_reasoning: str,
    ) -> tuple[str, str, str, str, str, list[dict]]:
        binding_issues = self._collect_binding_prevalidation_issues(issues)
        if verdict == "REJECT" or not binding_issues:
            return verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues

        binding_categories = self._summarize_binding_prevalidation_categories(binding_issues)
        regenerate_only_categories = self._extract_binding_regenerate_only_categories(binding_categories)
        regenerate_only_reason = (
            "Structural binding prevalidation requires regenerate-only repair: " + ", ".join(regenerate_only_categories)
            if regenerate_only_categories
            else ""
        )
        regenerate_categories = [
            category for category in binding_categories if category in _BINDING_PREVALIDATION_REGENERATE_CATEGORIES
        ]
        # T7.H3 / Tranche 1 sub-edit 1.5: opening_transition alias mismatch는 1-line 수정으로
        # 충분하다. opening_transition이 유일한 binding category이면 inplace 허용으로 격하한다.
        # 다른 binding category가 함께 발생하면(예: opening_transition + protagonist_state)
        # 구조적 위반으로 간주하여 기존대로 full regenerate를 강제한다.
        opening_transition_inplace_eligible = (
            len(regenerate_categories) == 1
            and regenerate_categories[0] in _BINDING_PREVALIDATION_INPLACE_ALIAS_CATEGORIES
        )
        snippets = [
            str(issue.get("issue") or issue.get("evidence") or "").strip()
            for issue in binding_issues
            if str(issue.get("issue") or issue.get("evidence") or "").strip()
        ]
        summary = "; ".join(snippets[:2])[:240]
        binding_note = (
            f"[Binding prevalidation] {summary}"
            if summary
            else "[Binding prevalidation] structured invariant repair required"
        )
        merged_feedback = f"{feedback}\n{binding_note}".strip() if feedback else binding_note
        merged_reason = f"{verdict_reason}; binding prevalidation repair required".strip("; ")
        if opening_transition_inplace_eligible:
            merged_scope = str(fix_scope or "inplace")
            merged_scope_reasoning = (
                "Opening-transition alias mismatch is the sole binding category; "
                "routing to inplace alias normalization instead of full regenerate."
            )
        elif regenerate_categories:
            merged_scope = "full"
            regenerate_summary = ", ".join(regenerate_categories)
            merged_scope_reasoning = (
                f"Structural binding prevalidation categories require regenerate-only repair: {regenerate_summary}."
            )
        else:
            merged_scope = str(fix_scope or "inplace")
            merged_scope_reasoning = str(
                fix_scope_reasoning
                or "Binding Python prevalidation invariants require bounded repair before plain PASS."
            )
        merged_verdict = "PASS_WITH_FIX" if verdict in {"PASS", "PASS_WITH_WARNING"} else verdict
        return merged_verdict, merged_feedback, merged_reason, merged_scope, merged_scope_reasoning, binding_issues

    @staticmethod
    def _extract_binding_regenerate_only_categories(binding_categories: list[str]) -> list[str]:
        if not isinstance(binding_categories, list):
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in binding_categories:
            category = str(raw or "").strip()
            if not category or category in seen:
                continue
            seen.add(category)
            if category in _BINDING_PREVALIDATION_REGENERATE_CATEGORIES:
                normalized.append(category)
        return normalized

    @staticmethod
    def _extract_stop_line_clauses(text: str) -> list[str]:
        if not isinstance(text, str):
            return []
        clauses: list[str] = []
        seen: set[str] = set()
        for raw in _STOP_LINE_SPLIT_RE.split(text):
            clause = " ".join(str(raw).strip().split())
            if len(clause) < 8:
                continue
            lowered = clause.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            clauses.append(clause)
        return clauses

    @staticmethod
    def _extract_significant_stop_tokens(text: str) -> set[str]:
        if not isinstance(text, str):
            return set()
        tokens: set[str] = set()
        for token in _STOP_LINE_TOKEN_RE.findall(text.lower()):
            if token.isdigit():
                continue
            if token in _STOP_LINE_COMMON_TOKENS:
                continue
            tokens.add(token)
        return tokens

    def _detect_stop_line_violation(self, stop_content: str, integrated: str) -> dict | None:
        if not isinstance(stop_content, str) or not isinstance(integrated, str):
            return None

        integrated_norm = " ".join(integrated.lower().split())
        if not integrated_norm:
            return None
        integrated_tokens = self._extract_significant_stop_tokens(integrated_norm)

        for clause in self._extract_stop_line_clauses(stop_content):
            clause_norm = " ".join(clause.lower().split())
            if len(clause_norm) >= 12 and clause_norm in integrated_norm:
                return {"mode": "clause_substring", "evidence": clause[:120]}

            clause_tokens = self._extract_significant_stop_tokens(clause_norm)
            if len(clause_tokens) < 3:
                continue
            overlap = clause_tokens & integrated_tokens
            overlap_ratio = len(overlap) / max(len(clause_tokens), 1)
            if len(overlap) >= 3 and overlap_ratio >= 0.75:
                return {
                    "mode": "token_overlap",
                    "evidence": clause[:120],
                    "overlap_tokens": sorted(overlap)[:5],
                }

        return None

    def _prepare_compare_candidate(
        self,
        candidate: dict,
        *,
        candidate_index: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> tuple[dict, dict]:
        """Attach bounded prevalidation evidence before Director compare selection."""
        if not isinstance(candidate, dict):
            return {"issues": [], "has_critical": False}, {
                "candidate_index": candidate_index,
                "quality_risk": False,
            }

        pre_result = self._python_pre_validate(
            candidate,
            constraint_block,
            prev_blueprint,
            state_tracker,
            arc_data=arc_data,
            working_ep_override=working_ep,
        )
        candidate_arc_no = arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else arc_idx
        if candidate_arc_no <= 0:
            candidate_arc_no = arc_idx
        self._apply_dead_npc_advisory(
            pre_result,
            blueprint=candidate,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_no=candidate_arc_no,
        )

        python_warnings, quality_risk = self._build_python_warning_entries(pre_result.get("issues", []))
        advisory_fix_pack = self._build_advisory_fix_pack(pre_result.get("issues", []))
        meta = candidate.get("_ensemble_meta", {})
        if not isinstance(meta, dict):
            meta = {}
        meta["python_warnings"] = python_warnings
        meta["quality_risk"] = quality_risk
        meta["prevalidation_issue_count"] = len(pre_result.get("issues", []))
        if advisory_fix_pack:
            meta["advisory_fix_pack"] = advisory_fix_pack
        candidate["_ensemble_meta"] = meta

        advisory = {
            "candidate_index": candidate_index,
            "strategy": str(meta.get("strategy", "") or "")[:60],
            "issue_count": len(pre_result.get("issues", [])),
            "quality_risk": quality_risk,
        }
        if python_warnings:
            advisory["python_warnings"] = python_warnings
        if advisory_fix_pack:
            advisory["advisory_fix_pack"] = advisory_fix_pack
            advisory["advisory_target_kind"] = str(advisory_fix_pack.get("target_kind", "") or "").strip()
        return pre_result, advisory

    def _run_compare_validation(
        self,
        *,
        all_candidates: list[dict],
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        director,
        entity_registry: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> tuple[str, dict]:
        logging.warning(f"[V60.85] Director compare mode with {len(all_candidates)} candidates")

        compare_pre_results: list[dict] = []
        candidate_advisories: list[dict] = []
        for idx, candidate in enumerate(all_candidates):
            pre_result, advisory = self._prepare_compare_candidate(
                candidate,
                candidate_index=idx,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                state_tracker=state_tracker,
                working_ep=working_ep,
                arc_idx=arc_idx,
            )
            compare_pre_results.append(pre_result)
            candidate_advisories.append(advisory)

        compare_result = director.compare_and_select_blueprint(
            candidates=all_candidates,
            arc_data=arc_data,
            ep_num=working_ep,
            prev_blueprint=prev_blueprint,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
        )

        selected_idx = _safe_int(compare_result.get("selected_index", 0), 0)
        if selected_idx < 0 or selected_idx >= len(all_candidates):
            selected_idx = 0
        selected_bp = compare_result.get("selected_blueprint")
        if not isinstance(selected_bp, dict) and 0 <= selected_idx < len(all_candidates):
            selected_bp = all_candidates[selected_idx]

        contradictions = compare_result.get("contradictions", [])
        if not isinstance(contradictions, list):
            contradictions = []

        if 0 <= selected_idx < len(compare_pre_results):
            selected_pre_result = compare_pre_results[selected_idx]
        else:
            selected_pre_result = {"issues": [], "has_critical": False}
        selected_candidate_advisory = (
            candidate_advisories[selected_idx]
            if 0 <= selected_idx < len(candidate_advisories)
            else {"candidate_index": selected_idx, "quality_risk": False}
        )

        verdict = compare_result.get("decision", "REJECT")
        quality_risk = bool(
            compare_result.get("quality_risk", False) or selected_candidate_advisory.get("quality_risk", False)
        )
        feedback = str(compare_result.get("feedback", "") or "")
        revision_required = bool(
            compare_result.get("revision_required", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )
        selection_reason = str(compare_result.get("selection_reason") or compare_result.get("reason", "") or "")
        verdict_reason = str(compare_result.get("verdict_reason") or selection_reason or "")
        fix_scope = str(compare_result.get("fix_scope", "") or "")
        fix_scope_reasoning = str(compare_result.get("fix_scope_reasoning", "") or "")
        (
            verdict,
            feedback,
            verdict_reason,
            fix_scope,
            fix_scope_reasoning,
            binding_issues,
        ) = self._apply_binding_prevalidation_contract(
            verdict=verdict,
            issues=selected_pre_result.get("issues", []),
            feedback=feedback,
            verdict_reason=verdict_reason,
            fix_scope=fix_scope,
            fix_scope_reasoning=fix_scope_reasoning,
        )
        binding_categories = self._summarize_binding_prevalidation_categories(binding_issues)
        regenerate_only_categories = self._extract_binding_regenerate_only_categories(binding_categories)
        regenerate_only_reason = (
            "Structural binding prevalidation requires regenerate-only repair: " + ", ".join(regenerate_only_categories)
            if regenerate_only_categories
            else ""
        )
        revision_required = bool(revision_required or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"))
        issue_fix_pack = self._build_issue_fix_pack(selected_pre_result.get("issues", []))
        fix_pack = _normalize_stage3_fix_pack(compare_result) or issue_fix_pack
        advisory_fix_pack = self._build_advisory_fix_pack(selected_pre_result.get("issues", []))

        result = {
            "verdict": verdict,
            "phase": "director_compare+python_prevalidate",
            "issues": selected_pre_result.get("issues", []),
            "summary": selection_reason,
            "score": compare_result.get("score", 0),
            "feedback": feedback,
            "confidence": 0.9 if _safe_int(compare_result.get("score", 0), 0) >= 70 else 0.6,
            "selected_index": selected_idx,
            "selected_blueprint": selected_bp,
            "comparison_notes": compare_result.get("comparison_notes", ""),
            "contradictions": contradictions,
            "fix_scope": fix_scope,
            "fix_scope_reasoning": fix_scope_reasoning,
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "quality_risk": quality_risk,
            "revision_required": revision_required,
            "candidate_count": len(all_candidates),
            "candidate_advisories": candidate_advisories,
            "selected_candidate_advisory": selected_candidate_advisory,
            "binding_prevalidation_issue_count": len(binding_issues),
            "binding_prevalidation_categories": binding_categories,
        }
        if regenerate_only_categories:
            result["binding_regenerate_only_categories"] = regenerate_only_categories
            result["binding_regenerate_only_reason"] = regenerate_only_reason
        repair_contract = compare_result.get("repair_contract")
        repair_contract = dict(repair_contract) if isinstance(repair_contract, dict) and repair_contract else {}
        scope_authority = compare_result.get("scope_authority")
        scope_authority = dict(scope_authority) if isinstance(scope_authority, dict) and scope_authority else {}
        repair_scope = str(
            compare_result.get("repair_scope", "")
            or repair_contract.get("repair_scope", "")
            or scope_authority.get("repair_scope", "")
            or ""
        ).strip()
        if repair_scope:
            result["repair_scope"] = repair_scope
        authoritative_fix_scope = str(
            compare_result.get("authoritative_fix_scope", "")
            or repair_contract.get("authoritative_fix_scope", "")
            or scope_authority.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        if authoritative_fix_scope:
            result["authoritative_fix_scope"] = authoritative_fix_scope
        if repair_contract:
            result["repair_contract"] = repair_contract
        if scope_authority:
            result["scope_authority"] = scope_authority
        if fix_pack:
            result["fix_pack"] = fix_pack
        if advisory_fix_pack:
            result["advisory_fix_pack"] = advisory_fix_pack

        status = "PASS" if verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING") else "REJECT"
        logging.info(
            f"[{status}] Director selected candidate {selected_idx + 1} with score {compare_result.get('score', 0)}"
        )
        return verdict, result

    def _run_python_prevalidation_phase(
        self,
        *,
        blueprint: dict,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> dict:
        pre_result = self._python_pre_validate(
            blueprint,
            constraint_block,
            prev_blueprint,
            state_tracker,
            arc_data=arc_data,
            working_ep_override=working_ep,
        )

        arc_no = arc_data.get("arc_no", 0) if arc_data else arc_idx
        if arc_no <= 0:
            arc_no = arc_idx

        dead_npc_violations = self._apply_dead_npc_advisory(
            pre_result,
            blueprint=blueprint,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_no=arc_no,
        )
        if dead_npc_violations:
            violation_names = [v["npc_name"] for v in dead_npc_violations]
            logging.warning(f"[V60.96] Dead NPC advisory forwarded to Director: {', '.join(violation_names)}")

        if pre_result["has_critical"]:
            logging.warning("[PreValidator] Critical Python findings deferred to Director")
            for issue in pre_result["issues"]:
                if issue.get("severity") == "CRITICAL":
                    logging.warning(f"- {issue.get('issue', '?')}")
        elif pre_result["issues"]:
            logging.warning(f"[PreValidator] Python findings forwarded: {len(pre_result['issues'])}")

        return pre_result

    def _build_no_director_validation_result(self, pre_result: dict) -> tuple[str, dict]:
        logging.error("[FailClosed] Director missing during blueprint validation")
        return "REJECT", {
            "verdict": "REJECT",
            "phase": "no_director",
            "issues": pre_result["issues"],
            "summary": "Director unavailable during blueprint validation",
            "feedback": "Blueprint validation requires a Director decision.",
            "score": 0,
        }

    def _build_blueprint_validation_context(self, *, state_tracker, prev_hud: dict | None) -> dict:
        validation_context = {"skip_continuity": True, "mode": "BLUEPRINT"}
        if state_tracker:
            encyclopedia_npcs = []
            for npc_name, npc_info in getattr(state_tracker, "npc_registry", {}).items():
                encyclopedia_npcs.append(
                    {
                        "name": npc_name,
                        "status": npc_info.get("status", "alive"),
                        "death_arc": npc_info.get("death_arc"),
                        "aliases": npc_info.get("aliases", []),
                    }
                )
            validation_context["encyclopedia"] = {"npcs": encyclopedia_npcs}

        if isinstance(prev_hud, dict) and prev_hud:
            validation_context["prev_hud"] = prev_hud
            validation_context["martial_hud"] = prev_hud
        return validation_context

    def _prepare_director_validation_payload(
        self,
        *,
        blueprint: dict,
        arc_data: dict,
        prev_blueprint: dict | None,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
        working_ep: int,
    ) -> dict:
        integrated_scenario = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated_scenario, str):
            integrated_scenario = str(integrated_scenario) if integrated_scenario else ""

        arc_tactical_doc = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical_doc, dict):
            arc_tactical_doc = json.dumps(arc_tactical_doc, ensure_ascii=False)

        prev_ms_ending = ""
        if prev_blueprint:
            prev_ms_ending = prev_blueprint.get("ending_hook", "")

        ep_start = arc_data.get("ep_start", working_ep)
        arc_pos = working_ep - ep_start + 1
        total_eps = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)

        ensemble_meta = blueprint.get("_ensemble_meta", {})
        python_warnings = ensemble_meta.get("python_warnings", [])
        if python_warnings:
            focus_header = "[Director Focus Header]\n"
            for warning in python_warnings:
                focus_header += f"  - {warning.get('message', '?')}: {warning.get('focus', '')}\n"
            focus_header += "\n[Blueprint Under Review]\n"
            manuscript_with_focus = focus_header + integrated_scenario
        else:
            manuscript_with_focus = integrated_scenario

        return {
            "ep_num": working_ep,
            "manuscript": manuscript_with_focus,
            "arc_doc": arc_tactical_doc,
            "history_summary": self._safe_causal_history(),
            "prev_full_text": prev_ms_ending,
            "arc_pos": arc_pos,
            "total_eps": total_eps,
            "target_len": self.min_chars,
            "retry_count": 0,
            "entity_registry": entity_registry,
            "state_tracker": state_tracker,
            "validation_context": self._build_blueprint_validation_context(
                state_tracker=state_tracker,
                prev_hud=prev_hud,
            ),
        }

    def _build_director_validation_result(
        self,
        *,
        blueprint: dict,
        pre_result: dict,
        director_result: dict,
    ) -> tuple[str, dict]:
        director_verdict = director_result.get("decision", "PASS")
        director_reason = director_result.get("reason", "")
        director_feedback = director_result.get("feedback", "")
        director_score = _safe_int(director_result.get("score", 50), 50)

        all_issues = pre_result["issues"][:]
        if director_verdict == "REJECT":
            all_issues.append(
                {
                    "severity": "MAJOR",
                    "category": "director",
                    "issue": f"Director REJECT: {director_reason}",
                    "evidence": director_feedback,
                    "fix_hint": director_feedback,
                }
            )

        final_verdict = director_verdict
        python_warnings, quality_risk = self._build_python_warning_entries(pre_result["issues"])
        advisory_fix_pack = self._build_advisory_fix_pack(pre_result["issues"])
        (
            final_verdict,
            director_feedback,
            director_reason,
            fix_scope,
            fix_scope_reasoning,
            binding_issues,
        ) = self._apply_binding_prevalidation_contract(
            verdict=final_verdict,
            issues=pre_result["issues"],
            feedback=director_feedback,
            verdict_reason=director_reason,
            fix_scope=str(director_result.get("fix_scope", "") or ""),
            fix_scope_reasoning=str(director_result.get("fix_scope_reasoning", "") or ""),
        )
        binding_categories = self._summarize_binding_prevalidation_categories(binding_issues)
        regenerate_only_categories = self._extract_binding_regenerate_only_categories(binding_categories)
        regenerate_only_reason = (
            "Structural binding prevalidation requires regenerate-only repair: " + ", ".join(regenerate_only_categories)
            if regenerate_only_categories
            else ""
        )
        self._sync_prevalidation_ensemble_meta(
            blueprint if isinstance(blueprint, dict) else None,
            python_warnings=python_warnings,
            advisory_fix_pack=advisory_fix_pack,
            quality_risk=quality_risk,
        )

        result = {
            "verdict": final_verdict,
            "phase": "director",
            "issues": all_issues,
            "summary": director_reason,
            "score": director_score,
            "score_breakdown": {
                "director_score": director_score,
                "pre_issues_count": len(pre_result["issues"]),
            },
            "feedback": director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else "",
            "pre_issues": len(pre_result["issues"]),
            "confidence": 0.9 if director_score >= 70 else 0.6,
            "fix_scope": fix_scope,
            "fix_scope_reasoning": fix_scope_reasoning,
            "re_slice_instruction": director_result.get("re_slice_instruction", ""),
            "selection_reason": director_result.get("selection_reason", "") or director_reason,
            "verdict_reason": director_result.get("verdict_reason", "") or director_reason,
            "quality_risk": quality_risk,
            "revision_required": final_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"),
            "candidate_count": 1,
            "binding_prevalidation_issue_count": len(binding_issues),
            "binding_prevalidation_categories": binding_categories,
        }
        if regenerate_only_categories:
            result["binding_regenerate_only_categories"] = regenerate_only_categories
            result["binding_regenerate_only_reason"] = regenerate_only_reason
        repair_contract = director_result.get("repair_contract")
        repair_contract = dict(repair_contract) if isinstance(repair_contract, dict) and repair_contract else {}
        scope_authority = director_result.get("scope_authority")
        scope_authority = dict(scope_authority) if isinstance(scope_authority, dict) and scope_authority else {}
        repair_scope = str(
            director_result.get("repair_scope", "")
            or repair_contract.get("repair_scope", "")
            or scope_authority.get("repair_scope", "")
            or ""
        ).strip()
        if repair_scope:
            result["repair_scope"] = repair_scope
        authoritative_fix_scope = str(
            director_result.get("authoritative_fix_scope", "")
            or repair_contract.get("authoritative_fix_scope", "")
            or scope_authority.get("authoritative_fix_scope", "")
            or ""
        ).strip()
        if authoritative_fix_scope:
            result["authoritative_fix_scope"] = authoritative_fix_scope
        issue_fix_pack = self._build_issue_fix_pack(pre_result["issues"])
        fix_pack = _normalize_stage3_fix_pack(director_result) or issue_fix_pack
        if fix_pack:
            result["fix_pack"] = fix_pack
        if repair_contract:
            result["repair_contract"] = repair_contract
        if scope_authority:
            result["scope_authority"] = scope_authority
        if advisory_fix_pack:
            result["advisory_fix_pack"] = advisory_fix_pack

        status = "PASS" if final_verdict in ("PASS", "PASS_WITH_FIX") else "REJECT"
        logging.warning(f"[{status}] Director score={director_score} reason={(director_reason or '')[:50]}")
        return final_verdict, result

    def _build_director_error_result(self, pre_result: dict, exc: Exception) -> tuple[str, dict]:
        return "REJECT", {
            "verdict": "REJECT",
            "phase": "director_error",
            "issues": pre_result["issues"],
            "summary": "Director validation error - retry required",
            "feedback": (
                f"[Director error triggered retry]\nerror: {str(exc)[:100]}\nplease regenerate and review again"
            ),
        }

    def validate(
        self,
        blueprint: dict,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        director=None,  # final Director authority
        working_ep: int = 1,
        arc_idx: int = 0,
        entity_registry: dict | None = None,
        state_tracker=None,
        all_candidates: list[dict] | None = None,
        prev_hud: dict | None = None,
    ) -> tuple[str, dict]:
        """Run Python prevalidation and then defer the final verdict to Director."""
        if all_candidates and len(all_candidates) > 1 and director:
            return self._run_compare_validation(
                all_candidates=all_candidates,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                director=director,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
                working_ep=working_ep,
                arc_idx=arc_idx,
            )

        pre_result = self._run_python_prevalidation_phase(
            blueprint=blueprint,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_idx=arc_idx,
        )
        if director is None:
            return self._build_no_director_validation_result(pre_result)

        logging.warning("[Director] Blueprint audit started")
        try:
            director_result = director.audit_manuscript(
                **self._prepare_director_validation_payload(
                    blueprint=blueprint,
                    arc_data=arc_data,
                    prev_blueprint=prev_blueprint,
                    entity_registry=entity_registry,
                    state_tracker=state_tracker,
                    prev_hud=prev_hud,
                    working_ep=working_ep,
                )
            )
            return self._build_director_validation_result(
                blueprint=blueprint,
                pre_result=pre_result,
                director_result=director_result,
            )
        except Exception as e:
            logging.warning(f"[Director] audit error: {str(e)[:50]}")
            return self._build_director_error_result(pre_result, e)

    @staticmethod
    def _normalize_integrated_scenario(integrated) -> str:
        if isinstance(integrated, str):
            return integrated
        return str(integrated) if integrated else ""

    @staticmethod
    def _count_scene_entries(scenes) -> int:
        if isinstance(scenes, dict | list):
            return len(scenes)
        return 0

    @staticmethod
    def _iter_scene_entries(scenes):
        if isinstance(scenes, dict):
            return scenes.values()
        if isinstance(scenes, list):
            return scenes
        return ()

    @staticmethod
    def _extract_prev_blueprint_end_location(prev_blueprint: dict | None) -> str:
        if not isinstance(prev_blueprint, dict):
            return ""

        prev_end_location = prev_blueprint.get("end_location", "")
        if prev_end_location:
            return prev_end_location

        prev_scenes = prev_blueprint.get("scene_breakdown", {})
        if prev_scenes and isinstance(prev_scenes, dict):
            scene_keys = sorted(prev_scenes.keys())
            if scene_keys:
                last_scene = prev_scenes.get(scene_keys[-1], {})
                if isinstance(last_scene, dict):
                    return last_scene.get("location", "")
        return ""

    def _collect_structure_prevalidation_issues(
        self,
        *,
        blueprint: dict,
        integrated: str,
        scenes,
        scene_count: int,
    ) -> list[dict]:
        issues: list[dict] = []

        required_fields = ["scene_breakdown", "integrated_scenario"]
        for field in required_fields:
            if field not in blueprint or not blueprint[field]:
                issues.append(
                    {
                        "severity": "MAJOR",
                        "category": "structure",
                        "issue": f"필수 필드 누락: {field}",
                        "evidence": f"{field} 필드가 없거나 비어있음",
                        "fix_hint": f"{field} 필드를 올바르게 작성",
                    }
                )

        if len(integrated) < self.min_chars:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"분량 부족: {len(integrated)}자 < {self.min_chars}자",
                    "evidence": "integrated_scenario 길이 부족",
                    "fix_hint": f"최소 {self.min_chars}자 이상 작성",
                }
            )

        if scene_count <= 1:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"씬 부족: {scene_count}개 < 2개",
                    "evidence": f"scene_breakdown에 {scene_count}개 씬만 있음",
                    "fix_hint": "최소 2개 이상의 씬으로 구성",
                }
            )

        if scene_count <= 0:
            return issues

        shallow_count = 0
        for scene_value in self._iter_scene_entries(scenes):
            if isinstance(scene_value, str):
                shallow_count += 1
                continue
            if not isinstance(scene_value, dict):
                shallow_count += 1
                continue
            has_goal = bool(
                scene_value.get("goal")
                or scene_value.get("목표")
                or scene_value.get("summary")
                or scene_value.get("요약")
            )
            if not has_goal:
                shallow_count += 1

        if shallow_count > 0:
            issues.append(
                {
                    "severity": "MINOR",
                    "category": "structure",
                    "issue": f"씬 구조 미비: {shallow_count}/{scene_count}개 씬에 goal/summary 없음",
                    "evidence": "scene_breakdown 항목에 goal 또는 summary 필드 필요",
                    "fix_hint": "각 씬에 goal/summary를 명시하여 intent를 보존",
                }
            )

        return issues

    def _collect_fidelity_prevalidation_issues(
        self, *, integrated: str, arc_data, ep_num: int | None = None
    ) -> list[dict]:
        if not arc_data or not integrated:
            return []

        arc_state_constraints = (arc_data.get("state_constraints") or {}) if isinstance(arc_data, dict) else {}
        arc_relationship_changes = arc_state_constraints.get("relationship_changes") or []
        arc_npcs: list[str] = []
        normalized_integrated = re.sub(r"\s+", "", str(integrated or ""))
        for relationship in arc_relationship_changes:
            if isinstance(relationship, dict):
                if not self._relationship_visible_in_episode(relationship, ep_num):
                    continue
                npc_name = relationship.get("target") or relationship.get("npc")
                if npc_name and isinstance(npc_name, str) and len(npc_name) >= 2 and npc_name not in arc_npcs:
                    arc_npcs.append(npc_name)

        if not arc_npcs:
            return []

        mentioned_count = 0
        matched_variants: dict[str, list[str]] = {}
        missing_npcs: list[str] = []
        for npc_name in arc_npcs:
            variants = self._relationship_name_variants(npc_name)
            matched = [
                variant for variant in sorted(variants) if variant in integrated or variant in normalized_integrated
            ]
            if matched:
                mentioned_count += 1
                matched_variants[npc_name] = matched[:4]
            else:
                missing_npcs.append(npc_name)
        if mentioned_count > 0:
            return []

        return [
            {
                "severity": "MINOR",
                "category": "fidelity",
                "issue": f"intent 불일치: Arc 관계 변화 NPC {len(arc_npcs)}명 blueprint 미언급",
                "evidence": f"NPC: {', '.join(list(arc_npcs)[:3])}",
                "fix_hint": "Arc 관계 변화 NPC가 blueprint 시나리오에 등장해야 함",
                "advisory_only": True,
                "director_focus": False,
                "advisory_code": "relationship_change_visibility",
                "advisory_packet": {
                    "visible_relationship_count": len(arc_npcs),
                    "mentioned_relationship_count": mentioned_count,
                    "missing_npcs": missing_npcs[:6],
                    "matched_variants": matched_variants,
                },
                "fix_pack": {
                    "patch_target_records": [
                        {
                            "summary": "integrated_scenario",
                            "field_path": "integrated_scenario",
                            "target_kind": "local_sentence",
                        }
                    ],
                    "must_fix": [
                        "Arc 관계 변화 핵심 인물을 현재 화 시나리오/회상/계획에 명시: " + ", ".join(missing_npcs[:3])
                    ],
                    "do_not_regress": [
                        "현재 화 tactical authority, opening-state, 엔딩 훅은 유지",
                    ],
                    "success_condition": "integrated_scenario가 Arc 관계 변화 인물 중 최소 1명을 현재 화 맥락으로 명시한다",
                    "evidence_summary": "missing_relationship_npcs=" + ", ".join(missing_npcs[:3]),
                },
            }
        ]

    def _collect_arc_compliance_prevalidation_issues(self, *, constraint_block: dict, integrated: str) -> list[dict]:
        stop_line = constraint_block.get("stop_line", {}) if isinstance(constraint_block, dict) else {}
        stop_content = stop_line.get("content", "") if isinstance(stop_line, dict) else ""
        if not stop_content or len(stop_content) <= 10:
            return []

        stop_violation = self._detect_stop_line_violation(stop_content, integrated)
        if not stop_violation:
            return []

        evidence = stop_violation.get("evidence", "") or stop_content[:30].strip()
        overlap_tokens = stop_violation.get("overlap_tokens") or []
        evidence_suffix = ""
        if overlap_tokens:
            evidence_suffix = f" (overlap: {', '.join(overlap_tokens)})"

        return [
            {
                "severity": "CRITICAL",
                "category": "arc_compliance",
                "issue": "정지선 위반: 다음 화 내용 포함",
                "evidence": f"'{evidence}...'가 본문에서 발견됨{evidence_suffix}",
                "fix_hint": "다음 화 내용을 제거하고 이번 화 범위 내에서만 작성",
            }
        ]

    @staticmethod
    def _is_authorized_opening_location_shift(
        *,
        constraint_block: dict | None,
        curr_start_location: str,
        normalized_opening_transition: dict | None,
    ) -> bool:
        if not isinstance(constraint_block, dict):
            return False

        episode_state_packet = constraint_block.get("episode_state_packet", {})
        if not isinstance(episode_state_packet, dict):
            return False
        opening_truth = episode_state_packet.get("opening_truth", {})
        if not isinstance(opening_truth, dict):
            return False

        expectation = str(opening_truth.get("opening_transition_expectation", "") or "").strip().casefold()
        if "do not declare direct_continuation" not in expectation:
            return False

        normalized_opening_transition = (
            normalized_opening_transition if isinstance(normalized_opening_transition, dict) else {}
        )
        normalized_transition_type = str(normalized_opening_transition.get("type", "") or "").strip().casefold()
        if normalized_transition_type not in {"explicit_transition", "jump_opening"}:
            return False

        authoritative_location = str(opening_truth.get("location", "") or "").strip()
        return bool(authoritative_location) and authoritative_location == curr_start_location

    @staticmethod
    def _extract_scene_one_payload(blueprint: dict) -> dict:
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, list):
            scenes = {f"scene_{idx + 1}": scene for idx, scene in enumerate(scenes) if isinstance(scene, dict)}
        if not isinstance(scenes, dict) or not scenes:
            return {}

        scene_one = scenes.get("scene_1")
        if isinstance(scene_one, dict):
            return scene_one

        first_scene = next((scene for scene in scenes.values() if isinstance(scene, dict)), None)
        return first_scene if isinstance(first_scene, dict) else {}

    @staticmethod
    def _collect_scene_surface_text(scene: dict) -> str:
        if not isinstance(scene, dict):
            return ""
        key_events = scene.get("key_events", [])
        event_text = ""
        if isinstance(key_events, list):
            event_text = " ".join(str(item or "").strip() for item in key_events if str(item or "").strip())
        return " ".join(
            part
            for part in (
                str(scene.get("title", "") or "").strip(),
                str(scene.get("goal", "") or "").strip(),
                str(scene.get("summary", "") or "").strip(),
                event_text,
                str(scene.get("type", "") or "").strip(),
            )
            if part
        )

    @staticmethod
    def _scene_implies_character_reentry(scene_text: str, character: str) -> bool:
        normalized_text = re.sub(r"\s+", " ", str(scene_text or "").strip())
        normalized_character = str(character or "").strip()
        if not normalized_text or not normalized_character:
            return False

        def _contains_character_near_cue(text: str, cue: str) -> bool:
            start = text.find(cue)
            while start != -1:
                window_start = max(0, start - 48)
                window_end = min(len(text), start + len(cue) + 24)
                if normalized_character in text[window_start:window_end]:
                    return True
                start = text.find(cue, start + len(cue))
            return False

        for cue in _DIRECT_OPENING_REENTRY_KR_CUES:
            if _contains_character_near_cue(normalized_text, cue):
                return True

        lowered_text = normalized_text.casefold()
        lowered_character = normalized_character.casefold()
        for cue in _DIRECT_OPENING_REENTRY_EN_CUES:
            start = lowered_text.find(cue)
            while start != -1:
                window_start = max(0, start - 48)
                window_end = min(len(lowered_text), start + len(cue) + 24)
                if lowered_character in lowered_text[window_start:window_end]:
                    return True
                start = lowered_text.find(cue, start + len(cue))
        return False

    def _collect_direct_opening_active_character_reentry_issues(
        self,
        *,
        blueprint: dict,
        constraint_block: dict | None,
        normalized_opening_transition: dict | None,
    ) -> list[dict]:
        if not isinstance(constraint_block, dict):
            return []

        normalized_opening_transition = (
            normalized_opening_transition if isinstance(normalized_opening_transition, dict) else {}
        )
        normalized_transition_type = str(normalized_opening_transition.get("type", "") or "").strip().casefold()
        if normalized_transition_type != "direct_continuation":
            return []

        episode_state_packet = constraint_block.get("episode_state_packet", {})
        if not isinstance(episode_state_packet, dict):
            return []
        opening_truth = episode_state_packet.get("opening_truth", {})
        if not isinstance(opening_truth, dict):
            return []

        active_characters = [
            str(item or "").strip()
            for item in (opening_truth.get("active_characters") or [])
            if str(item or "").strip()
        ]
        if not active_characters:
            return []

        scene_one = self._extract_scene_one_payload(blueprint)
        if not scene_one:
            return []

        scene_text = self._collect_scene_surface_text(scene_one)
        if not scene_text:
            return []

        scene_characters_raw = scene_one.get("characters", [])
        if isinstance(scene_characters_raw, str):
            scene_characters = {scene_characters_raw.strip()} if scene_characters_raw.strip() else set()
        elif isinstance(scene_characters_raw, list):
            scene_characters = {str(item or "").strip() for item in scene_characters_raw if str(item or "").strip()}
        else:
            scene_characters = set()

        conflicted_names: list[str] = []
        for name in active_characters:
            if name not in scene_characters and name not in scene_text:
                continue
            if self._scene_implies_character_reentry(scene_text, name):
                conflicted_names.append(name)

        if not conflicted_names:
            return []

        opening_location = str(opening_truth.get("location", "") or "").strip()
        scene_location = str(
            scene_one.get("location", "") or blueprint.get("start_location", "") or blueprint.get("location", "") or ""
        ).strip()
        return [
            {
                "severity": "CRITICAL",
                "category": "opening_transition",
                "issue": (
                    "direct_continuation opening에서 carryover active character를 다시 입장시키고 있음: "
                    + ", ".join(conflicted_names[:3])
                ),
                "evidence": (
                    f"opening.active_characters={active_characters[:4]}; "
                    f"opening.location={opening_location or scene_location}; "
                    f"scene_1_text={scene_text[:160]}"
                ),
                "fix_hint": (
                    "direct_continuation이면 carryover active character를 이미 현장에 있는 상태로 열고, "
                    "새 입장/재입장은 explicit_transition 또는 jump_opening에서만 선언"
                ),
            }
        ]

    def _collect_continuity_prevalidation_issues(
        self,
        *,
        blueprint: dict,
        prev_blueprint: dict | None,
        constraint_block: dict | None = None,
        normalized_opening_transition: dict | None = None,
    ) -> list[dict]:
        if not isinstance(prev_blueprint, dict):
            return []

        prev_end_location = self._extract_prev_blueprint_end_location(prev_blueprint)
        curr_start_location = blueprint.get("start_location", blueprint.get("location", ""))
        issues = self._collect_direct_opening_active_character_reentry_issues(
            blueprint=blueprint,
            constraint_block=constraint_block,
            normalized_opening_transition=normalized_opening_transition,
        )

        if not prev_end_location or not curr_start_location:
            return issues
        if prev_end_location == curr_start_location:
            return issues
        if self._is_location_transition_valid(prev_end_location, curr_start_location):
            return issues
        if self._is_authorized_opening_location_shift(
            constraint_block=constraint_block,
            curr_start_location=str(curr_start_location or "").strip(),
            normalized_opening_transition=normalized_opening_transition,
        ):
            return issues

        issues.append(
            {
                "severity": "MAJOR",
                "category": "continuity",
                "issue": f"위치 불연속: {prev_end_location} → {curr_start_location}",
                "evidence": "이전 화 종료 위치와 현재 화 시작 위치 불일치",
                "fix_hint": "위치 이동 경위를 설명하거나 시작 위치 수정",
            }
        )
        return issues

    @staticmethod
    def _build_python_prevalidation_result(issues: list[dict]) -> dict:
        has_critical = any(issue["severity"] == "CRITICAL" for issue in issues)
        major_count = sum(1 for issue in issues if issue["severity"] == "MAJOR")
        critical_items = [issue["issue"] for issue in issues if issue["severity"] == "CRITICAL"]
        return {
            "issues": issues,
            "has_critical": has_critical,
            "has_major_excess": major_count >= 3,
            "critical_summary": "; ".join(critical_items) if critical_items else "",
        }

    @staticmethod
    def _sync_prevalidation_ensemble_meta(
        blueprint: dict | None,
        *,
        python_warnings: list[dict],
        advisory_fix_pack: dict,
        quality_risk: bool,
    ) -> None:
        if not isinstance(blueprint, dict):
            return

        ensemble_meta = blueprint.get("_ensemble_meta", {})
        if not isinstance(ensemble_meta, dict):
            ensemble_meta = {}

        if python_warnings:
            ensemble_meta["python_warnings"] = python_warnings
        else:
            ensemble_meta.pop("python_warnings", None)

        if advisory_fix_pack:
            ensemble_meta["advisory_fix_pack"] = advisory_fix_pack
        else:
            ensemble_meta.pop("advisory_fix_pack", None)

        if quality_risk:
            ensemble_meta["quality_risk"] = True
        else:
            ensemble_meta.pop("quality_risk", None)

        if ensemble_meta:
            blueprint["_ensemble_meta"] = ensemble_meta
        else:
            blueprint.pop("_ensemble_meta", None)

    def _python_pre_validate(
        self,
        blueprint: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker=None,  # [V60.95] 고밀도 HUD 검증용
        arc_data=None,  # [ValidationHardening] intent fidelity check용
        working_ep_override: int | None = None,
    ) -> dict:
        """Python 사전검사 (무료, 빠름)"""
        blueprint = blueprint if isinstance(blueprint, dict) else {}
        declared_opening_transition_type = read_declared_opening_transition_type(blueprint)
        normalized_opening_transition = apply_opening_transition_contract(blueprint, prev_blueprint=prev_blueprint)
        integrated = self._normalize_integrated_scenario(blueprint.get("integrated_scenario", ""))
        scenes = blueprint.get("scene_breakdown", {})
        scene_count = self._count_scene_entries(scenes)
        working_ep = 0
        for candidate in (blueprint.get("ep_num"), blueprint.get("episode_number"), constraint_block.get("ep_num")):
            marker = self._coerce_episode_marker(candidate)
            if marker is not None:
                working_ep = marker
                break
        if working_ep <= 0:
            override_marker = self._coerce_episode_marker(working_ep_override)
            if override_marker is not None:
                working_ep = override_marker

        issues: list[dict] = []
        issues.extend(
            self._collect_structure_prevalidation_issues(
                blueprint=blueprint,
                integrated=integrated,
                scenes=scenes,
                scene_count=scene_count,
            )
        )
        issues.extend(
            self._collect_fidelity_prevalidation_issues(
                integrated=integrated,
                arc_data=arc_data,
                ep_num=working_ep,
            )
        )
        issues.extend(
            self._collect_arc_compliance_prevalidation_issues(
                constraint_block=constraint_block,
                integrated=integrated,
            )
        )
        issues.extend(
            self._collect_work_identity_opening_issues(
                integrated=integrated,
                scenes=scenes,
                scene_count=scene_count,
                working_ep=working_ep,
            )
        )
        issues.extend(
            self._collect_continuity_prevalidation_issues(
                blueprint=blueprint,
                prev_blueprint=prev_blueprint,
                constraint_block=constraint_block,
                normalized_opening_transition=normalized_opening_transition,
            )
        )
        # [S3-FL] Fact reconciliation checks against fact-lock and capital-continuity packets
        issues.extend(
            self._collect_fact_lock_drift_issues(
                blueprint=blueprint,
                integrated=integrated,
                constraint_block=constraint_block,
            )
        )
        issues.extend(
            self._collect_capital_state_drift_issues(
                integrated=integrated,
                constraint_block=constraint_block,
            )
        )
        issues.extend(
            self._collect_capital_unit_alignment_issues(
                blueprint=blueprint,
                integrated=integrated,
                constraint_block=constraint_block,
            )
        )
        issues.extend(
            self._collect_temporal_deictic_drift_issues(
                blueprint=blueprint,
                arc_data=arc_data,
                constraint_block=constraint_block,
            )
        )
        # [Wave1-B] Scene-specificity and scenario-density prevalidation
        issues.extend(
            self._collect_scene_specificity_issues(
                scenes=scenes,
                scene_count=scene_count,
            )
        )
        issues.extend(
            self._collect_scene_characters_issues(
                scenes=scenes,
                scene_count=scene_count,
            )
        )
        issues.extend(
            self._collect_arc_timeline_alignment_issues(
                blueprint=blueprint,
                arc_data=arc_data,
            )
        )
        issues.extend(
            self._collect_tactical_semantic_fidelity_issues(
                blueprint=blueprint,
                integrated=integrated,
                arc_data=arc_data,
                constraint_block=constraint_block,
            )
        )
        issues.extend(
            self._collect_stage4_readiness_contract_issues(
                blueprint=blueprint,
                scenes=scenes,
                scene_count=scene_count,
                prev_blueprint=prev_blueprint,
                declared_opening_transition_type=declared_opening_transition_type,
                normalized_opening_transition=normalized_opening_transition,
            )
        )
        issues.extend(
            self._collect_episode_progression_issues(
                blueprint=blueprint,
                prev_blueprint=prev_blueprint,
                constraint_block=constraint_block,
                normalized_opening_transition=normalized_opening_transition,
            )
        )
        issues.extend(
            self._collect_scenario_density_issues(
                integrated=integrated,
                scenes=scenes,
                scene_count=scene_count,
            )
        )
        return self._build_python_prevalidation_result(issues)

    # ── [S3-FL] Fact-Lock Drift Detection ──

    @staticmethod
    def _collect_fact_lock_drift_issues(
        *,
        blueprint: dict,
        integrated: str,
        constraint_block: dict,
    ) -> list[dict]:
        """Detect provenance drift and item-state drift against the fact-lock packet."""
        if not isinstance(constraint_block, dict):
            return []
        fact_lock = constraint_block.get("fact_lock_packet", {})
        if not isinstance(fact_lock, dict) or not fact_lock.get("anchors"):
            return []

        issues: list[dict] = []
        integrated_lower = integrated.lower() if integrated else ""

        for anchor in fact_lock["anchors"]:
            if not isinstance(anchor, dict):
                continue
            category = anchor.get("category", "")
            fact = anchor.get("fact", "")
            if not fact:
                continue

            # ── Location drift: blueprint start_location contradicts prev end_location ──
            if category == "위치":
                prev_loc = ""
                # Extract location from the fact text
                if "직전 종료 위치:" in fact:
                    prev_loc = fact.split("직전 종료 위치:")[-1].strip()[:60]
                if prev_loc:
                    bp_start = str(blueprint.get("start_location", blueprint.get("location", "")) or "").strip()
                    if bp_start and prev_loc and prev_loc not in bp_start and bp_start not in prev_loc:
                        # Check if the areas share a common prefix
                        prev_area = prev_loc[:3] if len(prev_loc) >= 3 else prev_loc
                        bp_area = bp_start[:3] if len(bp_start) >= 3 else bp_start
                        if prev_area != bp_area:
                            issues.append(
                                {
                                    "severity": "MAJOR",
                                    "category": "fact_lock_location",
                                    "issue": f"위치 사실잠금 위반: 확정 위치 '{prev_loc}' → blueprint 시작 '{bp_start}'",
                                    "evidence": fact,
                                    "fix_hint": "이전 화 종료 위치에서 시작하거나 이동 경위를 명시",
                                }
                            )

            # ── Item storage drift: item placed in location X, blueprint moves it ──
            if category == "아이템위치":
                # Extract item name and location from fact
                if "'" in fact:
                    parts = fact.split("'")
                    if len(parts) >= 4:
                        item_name = parts[1]
                        stored_loc = parts[3]
                        if item_name and stored_loc and integrated_lower:
                            # Check if blueprint mentions the item in a different location
                            item_lower = item_name.lower()
                            if item_lower in integrated_lower:
                                stored_lower = stored_loc.lower()
                                # If the stored location is NOT mentioned near the item, flag it
                                idx = integrated_lower.find(item_lower)
                                context_window = integrated_lower[max(0, idx - 80) : idx + len(item_lower) + 80]
                                if stored_lower not in context_window:
                                    issues.append(
                                        {
                                            "severity": "MAJOR",
                                            "category": "fact_lock_item",
                                            "issue": f"아이템 위치 사실잠금 위반: '{item_name}'은 '{stored_loc}'에 확정, blueprint에서 다른 위치 언급",
                                            "evidence": fact,
                                            "fix_hint": f"'{item_name}'의 위치를 '{stored_loc}'로 유지하거나 이동 장면 포함",
                                        }
                                    )

            # ── Ending hook provenance drift ──
            if category == "엔딩훅":
                # The ending hook describes how the prev ep ended; if the blueprint's
                # opening scenario contradicts the emotional/physical state, flag it
                if "직전 화 엔딩:" in fact:
                    hook_text = fact.split("직전 화 엔딩:")[-1].strip()[:150]
                    if hook_text and integrated_lower:
                        # Check for trust/provenance keywords in the hook that are negated in blueprint
                        _trust_keywords = ["신뢰", "믿", "의심", "배신", "경계", "불신"]
                        for keyword in _trust_keywords:
                            if keyword in hook_text:
                                # Check if the opposite sentiment appears in early blueprint
                                early_text = integrated_lower[:500]
                                opposites = {
                                    "신뢰": ["불신", "의심", "배신"],
                                    "믿": ["불신", "의심"],
                                    "의심": ["신뢰", "깊은 믿음"],
                                    "배신": ["신뢰", "충성"],
                                    "경계": ["안심", "마음을 놓"],
                                    "불신": ["신뢰", "믿"],
                                }
                                for opp in opposites.get(keyword, []):
                                    if opp in early_text:
                                        issues.append(
                                            {
                                                "severity": "CRITICAL",
                                                "category": "fact_lock_provenance",
                                                "issue": f"출처 사실잠금 위반: 직전 엔딩 '{keyword}' 맥락 → blueprint 초반 '{opp}' 반전",
                                                "evidence": f"엔딩훅: ...{hook_text[:80]}... / blueprint: ...{early_text[:80]}...",
                                                "fix_hint": "이전 화 엔딩 감정/신뢰 맥락을 이어받아 시작",
                                            }
                                        )
                                        break
                                break  # one keyword check per anchor

            # ── Institution/venue authority drift [NPC-CF-C] ──
            if category == "기관":
                if "확정 기관/장소:" in fact:
                    inst_name = fact.split("확정 기관/장소:")[-1].strip()
                    if inst_name and len(inst_name) >= 4 and integrated:
                        # Check if the locked institution appears in the blueprint
                        if inst_name not in integrated:
                            # Find the SHORTEST matching suffix for broad drift detection
                            # e.g. HMC투자증권 → shortest suffix is 증권, not 투자증권
                            # so competing 한미증권 (also ends with 증권) is caught
                            _inst_suffixes = (
                                "투자증권",
                                "자산운용",
                                "인베스트먼트",
                                "PB센터",
                                "증권",
                                "은행",
                                "캐피탈",
                                "보험",
                                "병원",
                                "센터",
                                "그룹",
                                "재단",
                                "협회",
                                "연구소",
                                "본사",
                                "지점",
                                "사무실",
                            )
                            _matching = [s for s in _inst_suffixes if inst_name.endswith(s)]
                            _matched_suffix = min(_matching, key=len) if _matching else ""
                            if _matched_suffix:
                                # Check if a competing institution with the same suffix appears
                                _competing_re = re.compile(
                                    r"([\w가-힣A-Za-z]{2,15}" + re.escape(_matched_suffix) + r")"
                                )
                                competing = set()
                                for cm in _competing_re.finditer(integrated):
                                    cname = cm.group(1).strip()
                                    if cname != inst_name and len(cname) >= 4:
                                        competing.add(cname)
                                if competing:
                                    issues.append(
                                        {
                                            "severity": "CRITICAL",
                                            "category": "fact_lock_institution",
                                            "issue": (
                                                f"기관 사실잠금 위반: 확정 '{inst_name}'"
                                                f" → blueprint '{', '.join(sorted(competing)[:2])}' 사용"
                                            ),
                                            "evidence": fact,
                                            "fix_hint": f"'{inst_name}' 명칭을 유지하거나 정당한 변경 경위를 명시",
                                        }
                                    )

        return issues[:6]  # bounded output

    @staticmethod
    def _collect_capital_state_drift_issues(
        *,
        integrated: str,
        constraint_block: dict,
    ) -> list[dict]:
        """Detect capital/deployment contradictions against capital-continuity packet."""
        if not isinstance(constraint_block, dict):
            return []
        capital_pkt = constraint_block.get("capital_continuity_packet", {})
        if not isinstance(capital_pkt, dict) or not capital_pkt.get("fields"):
            return []

        if not integrated:
            return []

        issues: list[dict] = []
        integrated_lower = integrated.lower()

        # Contradiction patterns: "still available" / "freshly deploy" after already committed
        _contradiction_patterns = [
            (re.compile(r"아직\s*(?:여유|남은|잔여)\s*(?:자금|자본|돈|금액)"), "아직 여유 자금 언급"),
            (re.compile(r"새로\s*(?:투입|투자|매수|배치)"), "신규 투입 언급"),
            (re.compile(r"전액\s*(?:투입|투자|매수|배치)"), "전액 투입 언급"),
            (re.compile(r"(?:모든|전부|전체)\s*(?:자금|자본|돈)\s*(?:을|를)?\s*(?:투입|투자)"), "전체 자본 투입 언급"),
        ]

        for pattern, desc in _contradiction_patterns:
            if pattern.search(integrated_lower):
                issues.append(
                    {
                        "severity": "CRITICAL",
                        "category": "capital_state",
                        "issue": f"자본 상태 모순: {desc} (이전 화에서 이미 확정된 자본 상태 존재)",
                        "evidence": f"blueprint에서 '{desc}' 패턴 감지",
                        "fix_hint": "이전 화 확정 자본 상태를 기준으로 수정",
                    }
                )

        # ── Phantom capital drift: deployed capital reappearing as available [NPC-CF-C] ──
        _deployed_amounts: list[str] = []
        for field in capital_pkt["fields"]:
            if not isinstance(field, dict):
                continue
            label = str(field.get("label", ""))
            value = str(field.get("value", ""))
            if any(kw in label or kw in value for kw in ("투입 확정", "투입/체결", "투입 완료", "가용 아님", "매수")):
                _amount_re = re.compile(r"(\d[\d,.]*\s*(?:억|만|천만|백만)?\s*(?:원|달러|만원))")
                am = _amount_re.search(value)
                if am:
                    _deployed_amounts.append(am.group(1).strip())

        if _deployed_amounts:
            normalized_integrated = integrated.replace(",", "").replace(" ", "")
            _avail_ctx_re = re.compile(
                r"(?:"
                r"예치|보유|잔고|잔액|가용(?:현금|자금)?|"
                r"여유(?:현금|자금|잔고|돈)?|"
                r"남은(?:현금|자금|잔고|돈)|"
                r"현금(?:이|은|을|으로)?(?:계좌|잔고|수익)?|"
                r"계좌(?:에|로)?(?:꽂|들어|입금|찍)"
                r")"
            )
            _position_ctx_re = re.compile(r"(?:포지션|홀딩|잔여홀딩|잔여포지션|레버리지|계약|선물|롱|숏|증거금|미실현)")
            for amount in _deployed_amounts:
                amount_norm = amount.replace(",", "").replace(" ", "")
                if not amount_norm:
                    continue

                search_from = 0
                while True:
                    idx = normalized_integrated.find(amount_norm, search_from)
                    if idx < 0:
                        break
                    search_from = idx + len(amount_norm)

                    ctx_start = max(0, idx - 28)
                    ctx_end = min(len(normalized_integrated), idx + len(amount_norm) + 48)
                    context_window = normalized_integrated[ctx_start:ctx_end]
                    local_prefix = normalized_integrated[max(0, idx - 8) : idx]
                    local_suffix = normalized_integrated[
                        idx + len(amount_norm) : min(len(normalized_integrated), idx + len(amount_norm) + 20)
                    ]

                    # Remaining deployed positions such as "남은 7.5억 원의 레버리지 포지션" are not
                    # phantom cash drift, even if a nearby clause also mentions separate realized cash.
                    if _position_ctx_re.search(local_prefix) or _position_ctx_re.search(local_suffix):
                        continue
                    if _avail_ctx_re.search(context_window):
                        issues.append(
                            {
                                "severity": "MAJOR",
                                "category": "phantom_capital",
                                "issue": f"유령 자본: 투입 확정 '{amount}'이 가용/예치 상태로 재등장",
                                "evidence": "capital packet에서 투입 확정, blueprint에서 amount-bound 예치/보유 맥락 감지",
                                "fix_hint": "이미 투입/체결된 자본은 가용 자본에서 제외",
                            }
                        )
                        break  # one phantom issue is enough signal
                if any(issue.get("category") == "phantom_capital" for issue in issues):
                    break

        return issues[:3]

    def _collect_capital_unit_alignment_issues(
        self,
        *,
        blueprint: dict,
        integrated: str,
        constraint_block: dict,
    ) -> list[dict]:
        """Detect USD deployment amounts drifting into KRW-authoritative capital arcs."""
        if not isinstance(constraint_block, dict) or not integrated:
            return []
        capital_pkt = constraint_block.get("capital_continuity_packet", {})
        if not isinstance(capital_pkt, dict):
            return []
        fields = capital_pkt.get("fields", [])
        if not isinstance(fields, list) or not fields:
            return []

        capital_label_hints = ("자본", "투입", "잔고", "보유")
        krw_amount_re = re.compile(
            r"\d[\d,.]*\s*(?:억(?:\s*\d[\d,.]*\s*(?:천만|백만|만))?|천만|백만|만)?\s*(?:원|만원|만\s*원)"
        )
        usd_amount_re = re.compile(r"\d[\d,.]*\s*(?:억|천만|백만|만)?\s*달러")
        capital_ctx_re = re.compile(
            r"(?:증거금|투입|추가\s*증거금|예치|잔고|잔액|가용\s*현금|가용\s*자금|총자산|자산|유동성|자본|청산\s*대금)"
        )
        price_ctx_re = re.compile(r"(?:온스당|호가|가격|지표|금리|FOMC)")
        price_prefix_re = re.compile(
            r"(?:WTI|브렌트|유가(?:가)?|원유(?:가)?|금값(?:이)?|은값(?:이)?|배럴당|온스당|호가(?:창)?|선물가)\s*$"
        )
        price_suffix_re = re.compile(
            r"^\s*(?:선|선을|선이|를\s*향해|를\s*돌파|를\s*뚫고|돌파하는|붕괴|돌파|급락|급등|하락|상승|수직\s*상승|향해)"
        )

        authoritative_krw_fields: list[str] = []
        authoritative_usd_fields: list[str] = []
        for field in fields[:8]:
            if not isinstance(field, dict):
                continue
            label = str(field.get("label", "") or "").strip()
            value = str(field.get("value", "") or "").strip()
            combined = f"{label}: {value}".strip(": ")
            if not combined or not any(hint in label for hint in capital_label_hints):
                continue
            if krw_amount_re.search(combined) and "달러" not in combined:
                authoritative_krw_fields.append(combined[:120])
            elif usd_amount_re.search(combined):
                authoritative_usd_fields.append(combined[:120])

        if not authoritative_krw_fields or authoritative_usd_fields:
            return []

        text_blocks: list[tuple[str, str]] = [("integrated_scenario", integrated)]
        for scene_value in self._iter_scene_entries(blueprint.get("scene_breakdown", {})):
            if not isinstance(scene_value, dict):
                continue
            for key in ("summary", "content", "description"):
                value = str(scene_value.get(key, "") or "").strip()
                if value:
                    text_blocks.append((f"scene.{key}", value))

        for source, text in text_blocks:
            for match in usd_amount_re.finditer(text):
                amount = match.group(0).strip()
                ctx_start = max(0, match.start() - 28)
                ctx_end = min(len(text), match.end() + 56)
                context_window = text[ctx_start:ctx_end]
                local_prefix = text[max(0, match.start() - 12) : match.start()]
                local_suffix = text[match.end() : min(len(text), match.end() + 12)]
                if not capital_ctx_re.search(context_window):
                    continue
                if (
                    price_ctx_re.search(context_window)
                    or price_prefix_re.search(local_prefix)
                    or price_suffix_re.search(local_suffix)
                ):
                    continue
                authority = "; ".join(authoritative_krw_fields[:2])
                return [
                    {
                        "severity": "MAJOR",
                        "category": "capital_unit",
                        "issue": f"자본 단위 불일치: KRW 기준 arc/state에 USD 투입 금액 '{amount}' 등장",
                        "evidence": f"source={source}; authority={authority}; context={context_window[:160]}",
                        "fix_hint": "capital_continuity_packet 기준 단위를 유지하고 투입/증거금/총자산 수치를 arc/state packet과 정합시킬 것",
                    }
                ]

        return []

    @staticmethod
    def _collect_temporal_deictic_drift_issues(
        *,
        blueprint: dict,
        arc_data: dict | None = None,
        constraint_block: dict | None = None,
    ) -> list[dict]:
        """Detect temporal-deictic ending-hook drift (e.g., '18년 전' class errors)."""
        if not isinstance(blueprint, dict):
            return []

        issues: list[dict] = []
        ending_hook = str(blueprint.get("ending_hook", "") or "")
        if ending_hook:
            for match in _TEMPORAL_DEICTIC_RE.finditer(ending_hook):
                try:
                    num = int(match.group(1))
                except (ValueError, TypeError):
                    continue
                if num < 5 or _is_temporal_deictic_diegetic_anchor(
                    text=ending_hook,
                    num=num,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                ):
                    continue
                issues.append(
                    {
                        "severity": "MAJOR",
                        "category": "temporal_deictic",
                        "issue": f"시간 지시어 위험: ending_hook에 '{match.group(0)}' 등 절대 시간 참조",
                        "evidence": f"ending_hook: {ending_hook[:120]}",
                        "fix_hint": "ending_hook에서 절대 시간 참조 대신 상대적 표현 사용 또는 제거",
                    }
                )
                if len(issues) >= 2:
                    break

        # Also check integrated_scenario ending portion for deictic issues
        integrated = str(blueprint.get("integrated_scenario", "") or "")
        if integrated:
            # Check only the last 500 chars (ending portion)
            tail = integrated[-500:]
            for match in _TEMPORAL_MEMORY_RE.finditer(tail):
                num = int(match.group(1))
                if num < 5 or _is_temporal_deictic_diegetic_anchor(
                    text=match.group(0),
                    num=num,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                ):
                    continue
                issues.append(
                    {
                        "severity": "MAJOR",
                        "category": "temporal_deictic",
                        "issue": f"시간 지시어 위험: 시나리오 말미에 '{match.group(0)}' 회상/기억 패턴 감지",
                        "evidence": f"...{tail[max(0, match.start() - 30) : match.end() + 30]}...",
                        "fix_hint": "미래-기억 맥락의 절대 시간 참조를 제거하거나 상대적 표현으로 교체",
                    }
                )
                break

        return issues[:2]

    # ── [Wave1-B] Scene-Specificity + Scenario-Density Prevalidation ──

    def _collect_scene_specificity_issues(
        self,
        *,
        scenes,
        scene_count: int,
    ) -> list[dict]:
        """Detect structurally present but narratively thin scenes."""
        if scene_count <= 0:
            return []
        issues: list[dict] = []
        thin_goal_count = 0
        no_events_count = 0
        _GOAL_MIN_CHARS = 8
        for scene_value in self._iter_scene_entries(scenes):
            if not isinstance(scene_value, dict):
                continue
            goal = str(scene_value.get("goal", "") or scene_value.get("목표", "") or "").strip()
            summary = str(scene_value.get("summary", "") or scene_value.get("요약", "") or "").strip()
            if max(len(goal), len(summary)) < _GOAL_MIN_CHARS:
                thin_goal_count += 1
            key_events = scene_value.get("key_events") or []
            if isinstance(key_events, list) and len(key_events) == 0:
                no_events_count += 1
        if thin_goal_count >= 2:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "scene_specificity",
                    "issue": f"씬 목표 미흡: {thin_goal_count}/{scene_count}개 씬의 goal/summary가 {_GOAL_MIN_CHARS}자 미만",
                    "evidence": f"thin_goal_count={thin_goal_count}",
                    "fix_hint": "각 씬의 goal/summary에 구체적 사건·행동·장소를 명시",
                }
            )
        if no_events_count >= 2:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "scene_completeness",
                    "issue": f"scene.key_events 누락: {no_events_count}/{scene_count}개 씬에서 key_events가 비어 있음",
                    "evidence": f"no_events_count={no_events_count}",
                    "missing_fields": ["key_events"],
                    "fix_hint": "각 씬에 최소 1개의 key_event를 명시",
                }
            )
        return issues[:2]

    def _collect_scene_characters_issues(
        self,
        *,
        scenes,
        scene_count: int,
    ) -> list[dict]:
        """Detect systemic empty scene character rosters in structured scene data."""
        if scene_count <= 0:
            return []
        empty_count = 0
        for scene_value in self._iter_scene_entries(scenes):
            if not isinstance(scene_value, dict):
                continue
            characters = scene_value.get("characters", [])
            if isinstance(characters, str):
                if not characters.strip():
                    empty_count += 1
                continue
            if isinstance(characters, list):
                normalized = [str(item).strip() for item in characters if str(item).strip()]
                if not normalized:
                    empty_count += 1
                continue
            empty_count += 1
        if empty_count < 2:
            return []
        return [
            {
                "severity": "MAJOR",
                "category": "scene_completeness",
                "issue": f"scene.characters 누락: {empty_count}/{scene_count}개 씬에서 characters가 비어 있음",
                "evidence": f"empty_scene_characters={empty_count}",
                "missing_fields": ["characters"],
                "fix_hint": "각 scene에 실제 참여 인물을 최소 정확 집합으로 채우기",
            }
        ]

    def _collect_stage4_readiness_contract_issues(
        self,
        *,
        blueprint: dict,
        scenes,
        scene_count: int,
        prev_blueprint: dict | None,
        declared_opening_transition_type: str = "",
        normalized_opening_transition: dict | None = None,
    ) -> list[dict]:
        """Flag missing Stage4-readiness contract fields before Director compare."""
        issues: list[dict] = []

        first_scene = None
        if isinstance(scenes, dict):
            candidate = scenes.get("scene_1")
            if isinstance(candidate, dict):
                first_scene = candidate
            else:
                for scene_value in scenes.values():
                    if isinstance(scene_value, dict):
                        first_scene = scene_value
                        break
        elif isinstance(scenes, list):
            for scene_value in scenes:
                if isinstance(scene_value, dict):
                    first_scene = scene_value
                    break

        start_location = str(blueprint.get("start_location", "") or blueprint.get("location", "") or "").strip()
        time_flow = str(blueprint.get("time_flow", "") or "").strip()
        first_title = str((first_scene or {}).get("title", "") or "").strip()
        first_location = str((first_scene or {}).get("location", "") or "").strip()
        opening_missing: list[str] = []
        if not start_location:
            opening_missing.append("start_location")
        if not time_flow:
            opening_missing.append("time_flow")
        if scene_count > 0 and not first_title:
            opening_missing.append("scene_1.title")
        if scene_count > 0 and not first_location:
            opening_missing.append("scene_1.location")
        if opening_missing:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "opening_anchor",
                    "issue": f"opening anchor 계약 누락: {', '.join(opening_missing)}",
                    "evidence": f"missing_fields={opening_missing}",
                    "fix_hint": "start_location, time_flow, scene_1.title, scene_1.location을 구조적으로 채우기",
                }
            )

        normalized_opening_transition = (
            normalized_opening_transition if isinstance(normalized_opening_transition, dict) else {}
        )
        normalized_transition_type = str(normalized_opening_transition.get("type", "") or "").strip()
        if (
            isinstance(prev_blueprint, dict)
            and declared_opening_transition_type
            and normalized_transition_type
            and declared_opening_transition_type != normalized_transition_type
        ):
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "opening_transition",
                    "issue": (
                        "opening_transition.type mismatch: "
                        f"declared '{declared_opening_transition_type}' "
                        f"vs normalized '{normalized_transition_type}'"
                    ),
                    "evidence": (
                        f"declared={declared_opening_transition_type}; normalized={normalized_transition_type}"
                    ),
                    "fix_hint": (
                        "opening_transition.type을 prev ending anchor와 "
                        "start_location/time_flow/scene_1 contract에 맞게 정규화"
                    ),
                }
            )

        core_tension = str(blueprint.get("core_tension", "") or "").strip()
        expected_ending = str(blueprint.get("expected_ending", "") or blueprint.get("ending_hook", "") or "").strip()
        target_beat = str(blueprint.get("target_beat", "") or "").strip()
        if max(len(core_tension), len(expected_ending), len(target_beat)) < 8:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "mission_clarity",
                    "issue": "episode mission 불명확: core_tension/expected_ending/target_beat가 모두 약하거나 비어 있음",
                    "evidence": "missing_mission_contract=true",
                    "fix_hint": "이번 화 핵심 갈등과 도착점을 core_tension 또는 expected_ending에 명시",
                }
            )

        ending_state = blueprint.get("ending_state", {})
        ending_timeline = ""
        if isinstance(ending_state, dict):
            raw_timeline = ending_state.get("timeline", {})
            if isinstance(raw_timeline, dict):
                ending_timeline = str(
                    raw_timeline.get("표현") or raw_timeline.get("expression") or raw_timeline.get("text") or ""
                ).strip()
            else:
                ending_timeline = str(raw_timeline or "").strip()
        timeline_specific = bool(
            re.search(r"\d{4}년|\d{1,2}월|오전|오후|새벽|아침|점심|저녁|밤|심야|중순|초|말", time_flow)
        )
        if not timeline_specific and not ending_timeline:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "timeline_specificity",
                    "issue": "timeline specificity 부족: time_flow가 모호하고 ending_state.timeline도 비어 있음",
                    "evidence": f"time_flow={time_flow!r}, ending_timeline={ending_timeline!r}",
                    "fix_hint": "time_flow 또는 ending_state.timeline에 구체적 시간대를 명시",
                }
            )

        protagonist_state = blueprint.get("protagonist_state", {})
        informative_slots = 0
        if isinstance(protagonist_state, dict):
            for value in protagonist_state.values():
                if isinstance(value, str) and value.strip():
                    informative_slots += 1
                elif isinstance(value, list) and any(str(item or "").strip() for item in value):
                    informative_slots += 1
                elif isinstance(value, dict) and value:
                    informative_slots += 1
                elif value not in ("", None, [], {}):
                    informative_slots += 1
        if informative_slots == 0:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "protagonist_state",
                    "issue": "protagonist_state 비어 있음: 현재 주인공 상태가 구조적으로 전달되지 않음",
                    "evidence": "informative_slots=0",
                    "fix_hint": "mood, injuries, equipment, objective 등 현재 상태를 최소 1개 이상 명시",
                }
            )

        return issues

    @staticmethod
    def _collect_episode_progression_issues(
        *,
        blueprint: dict,
        prev_blueprint: dict | None,
        constraint_block: dict,
        normalized_opening_transition: dict | None = None,
    ) -> list[dict]:
        """Detect replay of prior-episode scene families that should have progressed forward."""
        if not isinstance(prev_blueprint, dict) or not isinstance(constraint_block, dict):
            return []

        progression_packet = constraint_block.get("episode_progression_packet", {})
        if not isinstance(progression_packet, dict):
            return []
        blocked_families = progression_packet.get("blocked_scene_families", [])
        if not isinstance(blocked_families, list) or not blocked_families:
            return []

        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, list):
            scenes = {f"scene_{idx + 1}": scene for idx, scene in enumerate(scenes) if isinstance(scene, dict)}
        if not isinstance(scenes, dict) or not scenes:
            return []

        must_focus = ""
        raw_must_focus = constraint_block.get("must_focus", {})
        if isinstance(raw_must_focus, dict):
            must_focus = str(raw_must_focus.get("content", "") or "").strip()
        lawful_window = progression_packet.get("lawful_repetition_window", {})
        if not isinstance(lawful_window, dict):
            lawful_window = {}
        episode_state_packet = constraint_block.get("episode_state_packet", {})
        if not isinstance(episode_state_packet, dict):
            episode_state_packet = {}
        opening_truth = episode_state_packet.get("opening_truth", {})
        if not isinstance(opening_truth, dict):
            opening_truth = {}
        normalized_opening_transition = (
            normalized_opening_transition if isinstance(normalized_opening_transition, dict) else {}
        )
        normalized_transition_type = str(normalized_opening_transition.get("type", "") or "").strip().casefold()
        opening_transition_expectation = str(opening_truth.get("opening_transition_expectation", "") or "").strip()
        lawful_tokens = [
            str(token or "").strip().casefold()
            for token in lawful_window.get("escalation_tokens", []) or []
            if str(token or "").strip()
        ]

        def _normalize_location_variants(raw: object) -> set[str]:
            location = str(raw or "").strip()
            if not location:
                return set()
            parts = [part.strip() for part in re.split(r"[,/|>→]+", location) if part.strip()]
            variants = {location}
            variants.update(parts[-2:])
            if parts:
                variants.add(parts[0])
            return {variant for variant in variants if len(variant) >= 2}

        def _normalize_characters(raw: object) -> set[str]:
            if isinstance(raw, str):
                return {raw.strip()} if raw.strip() else set()
            if not isinstance(raw, list):
                return set()
            return {str(item or "").strip() for item in raw if str(item or "").strip()}

        def _extract_target_families(raw: object) -> set[str]:
            text = str(raw or "").casefold()
            if not text:
                return set()
            families = {
                "oil": ("wti", "유가", "원유", "오일", "브렌트", "텍사스산"),
                "gold": ("금 가격", "금값", "금 시장", "금 선물", "골드", "gold"),
                "equity": ("주식", "증시", "코스피", "코스닥", "나스닥", "종목"),
                "fx": ("환율", "달러", "엔화", "외환", "환시장", "fx"),
                "crypto": ("비트코인", "이더리움", "가상자산", "코인", "btc", "eth"),
            }
            return {family for family, tokens in families.items() if any(token in text for token in tokens)}

        def _scene_goal_text(scene: dict) -> str:
            if not isinstance(scene, dict):
                return ""
            key_events = scene.get("key_events", [])
            event_text = ""
            if isinstance(key_events, list):
                event_text = " ".join(str(item or "").strip() for item in key_events if str(item or "").strip())
            return " ".join(
                part
                for part in (
                    str(scene.get("title", "") or "").strip(),
                    str(scene.get("goal", "") or "").strip(),
                    str(scene.get("summary", "") or "").strip(),
                    event_text,
                    str(scene.get("type", "") or "").strip(),
                )
                if part
            ).casefold()

        def _is_authorized_opening_shift(scene_key: str) -> bool:
            if str(scene_key or "").strip().casefold() != "scene_1":
                return False
            expectation = opening_transition_expectation.casefold()
            if not expectation:
                return False
            if "do not declare direct_continuation" in expectation:
                return True
            if normalized_transition_type not in {"explicit_transition", "jump_opening"}:
                return False
            return "explicit_transition" in expectation or "jump_opening" in expectation

        def _is_lawful_repetition(scene: dict, family: dict) -> bool:
            if lawful_window.get("mode") != "allow_escalated_repeat":
                return False

            scene_text = _scene_goal_text(scene)
            if not scene_text:
                return False

            family_type = str(family.get("type", "") or "").strip().casefold()
            scene_type = str(scene.get("type", "") or "").strip().casefold()
            family_text = " ".join(
                part
                for part in (
                    str(family.get("label", "") or "").strip(),
                    str(family.get("location", "") or "").strip(),
                    family_type,
                )
                if part
            ).casefold()

            signal_count = 0
            if scene_type and family_type and scene_type != family_type:
                signal_count += 1
            if lawful_tokens and any(token in scene_text for token in lawful_tokens):
                signal_count += 1
            if any(
                token in scene_text
                for token in (
                    "단언",
                    "예언",
                    "결정",
                    "확정",
                    "압박",
                    "경고",
                    "조정",
                    "하락",
                    "돌파",
                    "버텨",
                    "예측",
                    "청산",
                    "익절",
                    "진입",
                    "매수",
                    "매도",
                    "체결",
                    "주문",
                    "전담",
                    "직통",
                    "핫라인",
                    "라인",
                    "명함",
                    "개설",
                    "격상",
                    "권한",
                    "경외",
                    "역전",
                    "돌변",
                    "예외 계좌",
                    "접견실",
                    "전용",
                )
            ):
                signal_count += 1
            if any(
                token in scene_text
                for token in (
                    "관망",
                    "버틴",
                    "보유",
                    "유지",
                    "기다리",
                    "대기",
                    "초조",
                    "불안",
                    "평온",
                    "심리",
                    "시장",
                    "추이",
                    "흐름",
                )
            ):
                signal_count += 1
            scene_targets = _extract_target_families(scene_text)
            family_targets = _extract_target_families(family_text)
            if scene_targets and set(scene_targets) - set(family_targets):
                signal_count += 1
            if (
                lawful_window.get("allow_same_channel_if_decision_escalates")
                and any(token in scene_text for token in ("전화", "콜", "핫라인", "직통", "통화"))
                and any(
                    token in scene_text
                    for token in ("단언", "결정", "압박", "경고", "예언", "전담", "직통", "명함", "개설", "격상")
                )
            ):
                signal_count += 1
            return signal_count >= 2

        matched_families: list[str] = []
        seen_family_keys: set[str] = set()
        opening_direct_replay = False

        for scene_key, scene_value in scenes.items():
            if not isinstance(scene_value, dict):
                continue
            current_location_variants = _normalize_location_variants(scene_value.get("location", ""))
            current_characters = _normalize_characters(scene_value.get("characters", []))
            if not current_location_variants or not current_characters:
                continue

            for family in blocked_families:
                if not isinstance(family, dict):
                    continue
                family_key = str(
                    family.get("scene_key", "") or family.get("label", "") or family.get("location", "")
                ).strip()
                if not family_key or family_key in seen_family_keys:
                    continue

                family_location_variants = {
                    str(item or "").strip()
                    for item in family.get("location_variants", []) or []
                    if str(item or "").strip()
                }
                if not family_location_variants:
                    family_location_variants = _normalize_location_variants(family.get("location", ""))
                family_characters = _normalize_characters(family.get("characters", []))
                if not family_location_variants or not family_characters:
                    continue

                location_match = any(
                    left in right or right in left
                    for left in current_location_variants
                    for right in family_location_variants
                )
                overlap_count = len(current_characters & family_characters)
                min_overlap = 1 if min(len(current_characters), len(family_characters)) <= 1 else 2
                if not location_match or overlap_count < min_overlap:
                    continue

                family_label = str(family.get("label", "") or family.get("location", "") or family_key).strip()
                family_location = str(family.get("location", "") or "").strip()
                if _is_authorized_opening_shift(scene_key):
                    continue
                if must_focus and any(token and token in must_focus for token in (family_label, family_location)):
                    continue
                if _is_lawful_repetition(scene_value, family):
                    continue

                matched_families.append(
                    f"{scene_key}->{family_key} ({family_location or family_label}; overlap={overlap_count})"
                )
                if scene_key.strip().casefold() == "scene_1" and normalized_transition_type == "direct_continuation":
                    opening_direct_replay = True
                seen_family_keys.add(family_key)
                break

        if len(matched_families) < 2 and not opening_direct_replay:
            return []

        must_focus_excerpt = must_focus[:160] if must_focus else "(must_focus unavailable)"
        issue_prefix = (
            "direct_continuation opening이 직전 화에서 이미 소비한 scene family를 다시 시작함"
            if opening_direct_replay
            else "직전 화에서 이미 소비한 scene family를 이번 화에서 다시 재연함"
        )
        return [
            {
                "severity": "CRITICAL",
                "category": "episode_progression",
                "issue": f"{issue_prefix}: {'; '.join(matched_families[:3])}",
                "evidence": f"matched_replay_families={matched_families[:3]}; must_focus={must_focus_excerpt}",
                "fix_hint": (
                    "직전 화의 opening carryover를 다시 열지 말고, 이미 현장에 있는 인물/상태에서 바로 이어서 전진하거나 "
                    "필요하면 explicit_transition/jump_opening으로 새 전환을 선언하라. "
                    "직전 화의 서재 대치/식사/방 TV 같은 완료 장면을 반복하지 말고 "
                    "현재 화 MUST_FOCUS의 새 사건 축으로 전진"
                ),
            }
        ]

    @staticmethod
    def _infer_relative_month_day(text: str, *, pick: str, year: int = 0, month: int = 0) -> int:
        source = str(text or "").strip()
        if not source or month <= 0:
            return 0

        if re.search(r"\d{1,2}월\s*(초|초반|상순)", source):
            return 1 if pick == "start" else 10
        if re.search(r"\d{1,2}월\s*(중순|중반)", source):
            return 15
        if re.search(r"\d{1,2}월\s*(말|말미|하순|후반)", source):
            last_day = calendar.monthrange(year or 2000, month)[1]
            return max(21, last_day - 7) if pick == "start" else last_day
        return 0

    @staticmethod
    def _parse_timeline_point(raw, *, pick: str) -> tuple[int, int, int] | None:
        if isinstance(raw, dict):
            year = raw.get("year")
            month = raw.get("month")
            if year is not None and month is not None:
                try:
                    day = raw.get("day")
                    year_value = int(year)
                    month_value = int(month)
                    if day not in (None, ""):
                        return year_value, month_value, int(day)
                    raw_text = raw.get("표현") or raw.get("expression") or raw.get("text") or raw.get("raw") or ""
                    inferred_day = UnifiedBlueprintValidator._infer_relative_month_day(
                        str(raw_text),
                        pick=pick,
                        year=year_value,
                        month=month_value,
                    )
                    return year_value, month_value, inferred_day
                except (TypeError, ValueError):
                    return None
            raw = raw.get("표현") or raw.get("expression") or raw.get("text") or raw.get("raw") or ""
        text = str(raw or "").strip()
        if not text:
            return None
        year_match = re.search(r"(\d{4})년", text)
        months = [int(value) for value in re.findall(r"(\d{1,2})월", text)]
        if not months:
            return None
        days = [int(value) for value in re.findall(r"(\d{1,2})일", text)]
        if (
            pick == "end"
            and len(months) > 1
            and re.match(r"\s*(\d{4})년\s*(\d{1,2})월", text)
            and any(marker in text for marker in ("앞둔", "앞두고", "대비", "준비", "예고", "구상"))
        ):
            month = months[0]
        else:
            month = months[0] if pick == "start" else months[-1]
        year = int(year_match.group(1)) if year_match else 0
        if pick == "start" and days:
            day = days[0]
        elif days:
            day = days[-1]
        else:
            day = UnifiedBlueprintValidator._infer_relative_month_day(
                text,
                pick=pick,
                year=year,
                month=month,
            )
        return year, month, day

    def _collect_arc_timeline_alignment_issues(
        self,
        *,
        blueprint: dict,
        arc_data: dict | None,
    ) -> list[dict]:
        """Detect ending-state timeline drift against authoritative arc timeline window.

        For non-terminal episodes inside a multi-episode arc, the blueprint end must
        stay within the arc window rather than exactly matching the arc terminal end.
        Exact terminal-end matching is reserved for the arc's last episode (or
        single-point timelines where start/end collapse to the same bucket).
        """
        if not isinstance(arc_data, dict):
            return []
        timeline = arc_data.get("state_changes", {}).get("timeline", {})
        if not isinstance(timeline, dict):
            return []
        arc_start = self._parse_timeline_point(timeline.get("start"), pick="start")
        arc_end = self._parse_timeline_point(timeline.get("end"), pick="end")
        if arc_start is None and arc_end is None:
            return []
        ending_state = blueprint.get("ending_state", {})
        if not isinstance(ending_state, dict):
            return []
        bp_timeline = ending_state.get("timeline", {})
        bp_end = self._parse_timeline_point(bp_timeline, pick="end")
        if bp_end is None:
            return []
        ep_num = _safe_int(blueprint.get("ep_num") or blueprint.get("episode_number"), 0)
        arc_end_ep = _safe_int(arc_data.get("ep_end"), 0)
        bp_expr = bp_timeline.get("표현") if isinstance(bp_timeline, dict) else ""
        if not bp_expr:
            bp_expr = bp_timeline.get("expression") if isinstance(bp_timeline, dict) else ""
        bp_expr = str(bp_expr or bp_timeline or "").strip()

        def _render_timeline_expr(raw: object) -> str:
            if isinstance(raw, dict):
                return str(raw.get("표현") or raw.get("expression") or raw).strip()
            return str(raw or "").strip()

        arc_start_expr = _render_timeline_expr(timeline.get("start"))
        arc_expr = _render_timeline_expr(timeline.get("end"))
        integrated_scenario = str(blueprint.get("integrated_scenario", "") or "").strip()

        def _build_fix_pack(*, authoritative_expr: str, reason_label: str) -> dict:
            patch_target_records: list[dict[str, object]] = [
                {
                    "summary": "ending_state.timeline",
                    "field_path": "ending_state.timeline",
                    "target_kind": "field_value",
                },
                {
                    "summary": "time_flow",
                    "field_path": "time_flow",
                    "target_kind": "field_value",
                },
            ]
            must_fix = [
                f"ending_state.timeline을 Arc 권위 시점 '{authoritative_expr}'에 정렬",
                f"time_flow를 Arc 권위 시점 '{authoritative_expr}'과 모순되지 않게 정규화",
            ]
            if integrated_scenario and any(
                token in integrated_scenario for token in ("새해 첫날", "1월 1일", "2006년 1월 1일")
            ):
                patch_target_records.append(
                    {
                        "summary": "integrated_scenario timeline cue",
                        "field_path": "integrated_scenario",
                        "target_kind": "field_value",
                    }
                )
                must_fix.append("integrated_scenario의 선행 날짜/새해 첫날 단서를 제거")
            return {
                "target_kind": "field_value",
                "patch_target_records": patch_target_records,
                "must_fix": must_fix,
                "do_not_regress": [
                    "Arc 핵심 사건과 인물 관계는 유지",
                    "시간축 외의 장면 구조는 불필요하게 넓히지 말 것",
                ],
                "success_condition": (
                    f"ending_state.timeline과 time_flow가 '{authoritative_expr}' 권위 시점과 정렬되고 "
                    "조기 날짜 단서가 남지 않는다"
                )[:220],
                "evidence_summary": f"{reason_label}: authoritative_timeline={authoritative_expr}"[:220],
            }

        require_terminal_exact_match = bool(
            arc_end is not None
            and (arc_start is None or arc_start == arc_end or (ep_num > 0 and arc_end_ep > 0 and ep_num >= arc_end_ep))
        )

        if require_terminal_exact_match:
            if bp_end == arc_end:
                return []
            return [
                {
                    "severity": "MAJOR",
                    "category": "arc_timeline",
                    "issue": f"ending_state.timeline 불일치: blueprint '{bp_expr}' vs arc '{arc_expr}'",
                    "evidence": f"blueprint_timeline={bp_end}, arc_timeline={arc_end}",
                    "fix_hint": "ending_state.timeline과 time_flow를 arc state_changes.timeline 종료 시점에 맞추기",
                    "fix_pack": _build_fix_pack(
                        authoritative_expr=arc_expr or arc_start_expr or "arc timeline",
                        reason_label="terminal_arc_timeline_mismatch",
                    ),
                }
            ]

        if arc_start is not None and bp_end < arc_start:
            return [
                {
                    "severity": "MAJOR",
                    "category": "arc_timeline",
                    "issue": (
                        f"ending_state.timeline 범위 이탈: blueprint '{bp_expr}' "
                        f"starts before arc window '{arc_start_expr} -> {arc_expr}'"
                    ),
                    "evidence": f"blueprint_timeline={bp_end}, arc_start={arc_start}, arc_end={arc_end}",
                    "fix_hint": "ending_state.timeline과 time_flow를 arc state_changes.timeline 시작 이후 범위에 맞추기",
                    "fix_pack": _build_fix_pack(
                        authoritative_expr=arc_start_expr or arc_expr or "arc timeline window",
                        reason_label="arc_timeline_before_window",
                    ),
                }
            ]
        if arc_end is not None and bp_end > arc_end:
            return [
                {
                    "severity": "MAJOR",
                    "category": "arc_timeline",
                    "issue": (
                        f"ending_state.timeline 범위 이탈: blueprint '{bp_expr}' "
                        f"exceeds arc window '{arc_start_expr} -> {arc_expr}'"
                    ),
                    "evidence": f"blueprint_timeline={bp_end}, arc_start={arc_start}, arc_end={arc_end}",
                    "fix_hint": "ending_state.timeline과 time_flow를 arc state_changes.timeline 종료 이전 범위에 맞추기",
                    "fix_pack": _build_fix_pack(
                        authoritative_expr=arc_expr or arc_start_expr or "arc timeline window",
                        reason_label="arc_timeline_after_window",
                    ),
                }
            ]
        return []

    def _collect_tactical_semantic_fidelity_issues(
        self,
        *,
        blueprint: dict,
        integrated: str,
        arc_data: dict | None,
        constraint_block: dict,
    ) -> list[dict]:
        """Flag unauthorized physical-threat/action invention that is absent from current episode tactical authority."""
        if not integrated:
            return []

        ep_num = _safe_int(blueprint.get("ep_num") or blueprint.get("episode_number"), 0)
        must_focus = constraint_block.get("must_focus", {}) if isinstance(constraint_block, dict) else {}
        tactical_excerpt = str(must_focus.get("content", "") or "").strip() if isinstance(must_focus, dict) else ""
        if not tactical_excerpt and isinstance(arc_data, dict) and ep_num > 0:
            tactical_excerpt = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
                fallback_full=False,
            ).strip()
        if not tactical_excerpt:
            return []

        tactical_lower = tactical_excerpt.lower()
        if detect_tactical_intrusion_signature(tactical_lower):
            return []

        combined_lower = collect_tactical_surface_text(blueprint).lower()
        signature = detect_tactical_intrusion_signature(combined_lower)
        if not signature:
            return []
        entry_hits = signature.get("entry_hits", [])
        conflict_hits = signature.get("conflict_hits", [])

        entry_summary = ", ".join(entry_hits[:3])
        conflict_summary = ", ".join(conflict_hits[:3])
        return [
            {
                "severity": "CRITICAL",
                "category": "tactical_semantic_fidelity",
                "issue": ("episode tactical authority에 없는 물리 위협/난입 이벤트가 blueprint에 새로 삽입됨"),
                "evidence": (
                    f"entry_markers={entry_summary}; conflict_markers={conflict_summary}; "
                    f"tactical_excerpt={tactical_excerpt[:120]}"
                ),
                "fix_hint": "현재 화 tactical authority에 없는 난입/괴한/물리 충돌 이벤트를 제거하고 지정된 핵심 사건 축으로 정렬",
            }
        ]

    def _collect_scenario_density_issues(
        self,
        *,
        integrated: str,
        scenes,
        scene_count: int,
    ) -> list[dict]:
        """Detect low-density integrated_scenario that clears char floor but lacks substance."""
        if not integrated or scene_count <= 0:
            return []
        issues: list[dict] = []
        scene_profile = build_blueprint_scene_profile({"scene_breakdown": scenes if isinstance(scenes, dict) else {}})
        # Check 1: Per-scene proportional coverage — flag if scenario is long enough
        # but too thin relative to scene count. Low-scene blueprints are judged by
        # obligation specificity and anchor density instead of a rigid chars-per-scene floor.
        avg_chars_per_scene = len(integrated) / scene_count if scene_count > 0 else 0
        _AVG_MIN = 200
        if len(integrated) >= self.min_chars and scene_count > 3 and avg_chars_per_scene < _AVG_MIN:
            issues.append(
                {
                    "severity": "MINOR",
                    "category": "scenario_density",
                    "issue": (
                        f"시나리오 밀도 부족: 평균 {avg_chars_per_scene:.0f}자/씬 "
                        f"< {_AVG_MIN}자/씬 ({scene_count}개 씬, 총 {len(integrated)}자)"
                    ),
                    "evidence": (
                        f"avg_chars_per_scene={avg_chars_per_scene:.0f}; scene_keywords={scene_profile.total_keywords}"
                    ),
                    "fix_hint": "씬 수를 기계적으로 늘리기보다 각 planning anchor의 goal/key_events를 구체적으로 전개",
                    "advisory_code": "scene_specificity_band",
                    "advisory_packet": {
                        "avg_chars_per_scene": round(avg_chars_per_scene, 1),
                        "scene_count": scene_count,
                        "scene_keyword_count": int(scene_profile.total_keywords),
                    },
                    "fix_pack": {
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "must_fix": [
                            f"{scene_count}개 씬 기준 planning anchor의 goal/key_events를 행동/대사로 더 구체화"
                        ],
                        "do_not_regress": [
                            "Arc shell, opening-state, ending hook은 유지",
                        ],
                        "success_condition": "integrated_scenario가 각 planning anchor를 더 구체적인 행동/장면 단서로 드러낸다",
                        "evidence_summary": (
                            f"avg_chars_per_scene={avg_chars_per_scene:.0f}; scene_keywords={scene_profile.total_keywords}"
                        ),
                    },
                }
            )
        # Check 2: Concrete anchor density — count location/institution/number tokens
        suffix_union = "|".join(re.escape(suffix) for suffix in _SCENARIO_DENSITY_ENTITY_SUFFIXES)
        contiguous_anchor_re = re.compile(rf"[A-Za-z가-힣]{{2,12}}(?:{suffix_union})")
        spaced_anchor_re = re.compile(
            rf"(?:[A-Za-z]{{1,8}}|[가-힣]{{2,8}})(?:\s+(?:[A-Za-z]{{1,12}}|[가-힣]{{1,8}})){{0,2}}\s+(?:{suffix_union})"
        )
        numeric_anchor_re = re.compile(r"\d[\d,.]*\s*(?:억|만|천만|백만|원|달러|골드|냥|전|관|kg|km|명|세|층|동|호)")
        anchors: list[str] = []
        seen_anchors: set[str] = set()
        for pattern in (contiguous_anchor_re, spaced_anchor_re, numeric_anchor_re):
            for match in pattern.finditer(integrated):
                anchor = " ".join(str(match.group(0) or "").split()).strip()
                if not anchor or anchor in seen_anchors:
                    continue
                seen_anchors.add(anchor)
                anchors.append(anchor)
        _ANCHOR_MIN = 5
        if len(integrated) >= self.min_chars and len(anchors) < _ANCHOR_MIN:
            issues.append(
                {
                    "severity": "MINOR",
                    "category": "scenario_density",
                    "issue": (
                        f"시나리오 구체성 부족: 구체적 앵커(기관/인물/수치) {len(anchors)}개 "
                        f"< {_ANCHOR_MIN}개 ({len(integrated)}자 중)"
                    ),
                    "evidence": f"anchor_count={len(anchors)}",
                    "fix_hint": "구체적 기관명, 인물명, 수치를 포함하여 시나리오 밀도 향상",
                    "advisory_only": True,
                    "director_focus": False,
                    "advisory_code": "anchor_density",
                    "advisory_packet": {
                        "anchor_count": len(anchors),
                        "anchor_min": _ANCHOR_MIN,
                        "sample_anchors": anchors[:5],
                        "scene_keyword_count": int(scene_profile.total_keywords),
                    },
                    "fix_pack": {
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "must_fix": [f"기관명/인물명/수치 anchor를 1~2개 이상 보강 (현재 {len(anchors)}개)"],
                        "do_not_regress": [
                            "Arc shell, opening-state, ending hook은 유지",
                        ],
                        "success_condition": "integrated_scenario가 구체적 기관명, 인물명, 수치 anchor를 추가한다",
                        "evidence_summary": f"anchor_count={len(anchors)}; sample_anchors={', '.join(anchors[:3])}",
                    },
                }
            )
        return issues[:2]

    def _is_location_transition_valid(self, prev_loc: str, curr_loc: str) -> bool:
        """위치 전환이 유효한지 체크"""
        prev_area = self._extract_area(prev_loc)
        curr_area = self._extract_area(curr_loc)

        if prev_area and curr_area and prev_area == curr_area:
            return True

        if prev_loc in curr_loc or curr_loc in prev_loc:
            return True

        return False

    def _extract_area(self, location: str) -> str:
        """위치에서 대분류 지역 추출"""
        match = re.search(r"^([가-힣]{2,5})", location)
        return match.group(1) if match else ""


def create_unified_blueprint_validator(context, client, model_tier: str = "gemini-2.5-flash"):
    """UnifiedBlueprintValidator 생성 헬퍼"""
    return UnifiedBlueprintValidator(context, client, model_tier)
