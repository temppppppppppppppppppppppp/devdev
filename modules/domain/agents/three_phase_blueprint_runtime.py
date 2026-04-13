"""
Three-phase blueprint runtime orchestration split.
"""
# utf8-hygiene: allow-file legacy mojibake literals remain in untouched runtime strings during readability campaign

import json
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from modules.core.constants import PatchModeThresholds
from modules.core.partial_fix_contract import build_partial_fix_eval, normalize_patch_target_records
from modules.models.blueprint import validate_blueprint
from modules.validation.threshold_helper import _threshold

from .base_agent import AgentErrorType

if TYPE_CHECKING:
    from .three_phase_blueprint_generator import ThreePhaseBlueprintGenerator

_STAGE3_REGENERATE_ONLY_BINDING_CATEGORIES = {
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
}
_STAGE3_INPLACE_ALIAS_REAUDIT_CATEGORIES = {
    "opening_transition",
}
_STAGE3_LOCAL_PATCH_TARGET_KINDS = {
    "dialogue",
    "entity_ref",
    "field_value",
    "local_phrase",
    "local_sentence",
    "scene_block",
}


@dataclass
class _ThreePhaseRetryState:
    cached_constraint_block: dict | None = None
    previous_best: dict | None = None
    prev_reject_score: int = 0
    prev_reject_feedback: str = ""
    prev_reject_strategy: str = ""
    prev_score_breakdown: dict = field(default_factory=dict)
    prev_selection_reason: str = ""
    prev_validation_warnings: list[str] = field(default_factory=list)
    prev_fix_scope: str = ""
    prev_fix_pack: dict = field(default_factory=dict)
    prev_repair_contract: dict = field(default_factory=dict)
    prev_scope_authority: dict = field(default_factory=dict)
    prev_local_patch_gate: dict = field(default_factory=dict)
    prev_reject_origin: str = ""
    prev_quality_gate_reject: bool = False
    prev_reject_signature: str = ""
    prev_binding_issue_count: int = 0
    repeated_reject_score_streak: int = 0
    repeated_reject_signature_streak: int = 0
    inplace_reject_streak: int = 0
    advisory_only_reject_streak: int = 0


@dataclass
class _ThreePhaseRuntimeBootstrap:
    genre: str
    protagonist_config: dict
    pipeline_result: dict
    initial_feedback: str
    retry_state: _ThreePhaseRetryState


@dataclass
class _ThreePhasePhase2Result:
    best_blueprint: dict | None
    all_candidates: list[dict]
    should_continue: bool = False
    should_break: bool = False


@dataclass
class _ThreePhasePhase3ValidationResult:
    best_blueprint: dict | None
    validation_result: dict
    verdict: str
    score: int
    selected_strategy: str
    should_continue: bool = False


@dataclass
class _ThreePhaseValidationEnvelope:
    best_blueprint: dict | None
    validation_result: dict
    verdict: str
    selected_strategy: str
    score: int


@dataclass
class _ThreePhasePassWithFixResult:
    best_blueprint: dict | None
    should_continue: bool = False


@dataclass
class _ThreePhasePassWithFixIterationResult:
    current_blueprint: dict | None
    current_validation: dict
    fix_ok: bool = False
    should_break: bool = False
    patch_attempted: bool = False


@dataclass
class _ThreePhaseRejectStateResult:
    feedback: str
    issues: list


@dataclass
class _ThreePhaseRetryCycleResult:
    best_blueprint: dict | None
    feedback: str
    should_continue: bool = False
    should_break: bool = False
    final_result: tuple[dict | None, dict] | None = None


@dataclass
class _Stage3RepairMaterial:
    requested_fix_scope: str = ""
    normalized_fix_pack: dict = field(default_factory=dict)
    advisory_fix_pack: dict = field(default_factory=dict)
    repair_contract: dict = field(default_factory=dict)
    scope_authority: dict = field(default_factory=dict)
    local_patch_gate: dict = field(default_factory=dict)
    binding_issue_count: int = 0
    regenerate_only_binding_categories: list[str] = field(default_factory=list)

    @property
    def effective_fix_pack(self) -> dict:
        return dict(self.normalized_fix_pack or self.advisory_fix_pack)

    @property
    def normalized_requested_fix_scope(self) -> str:
        return str(self.requested_fix_scope or "").strip().lower()

    @property
    def resolved_fix_scope(self) -> str:
        return (
            str(self.local_patch_gate.get("resolved_fix_scope", "") or self.normalized_requested_fix_scope)
            .strip()
            .lower()
        )


@dataclass
class _Stage3RepairRouteDecision:
    effective_fix_scope: str = ""
    resolved_fix_scope: str = ""
    use_inplace_patch: bool = False
    should_break_to_generate: bool = False
    inplace_retry_candidate: bool = False
    block_reasons: list[str] = field(default_factory=list)
    contract_block_reason: str = ""
    fix_scope_reasoning: str = ""
    regenerate_only_reason: str = ""


class _Stage3RepairRouter:
    @staticmethod
    def build_retry_material(retry_state: _ThreePhaseRetryState) -> _Stage3RepairMaterial:
        fix_scope = str(retry_state.prev_fix_scope or "").strip().lower()
        repair_contract = dict(retry_state.prev_repair_contract or {})
        scope_authority = dict(retry_state.prev_scope_authority or {})
        normalized_fix_pack = dict(retry_state.prev_fix_pack or {})
        local_patch_gate = _build_stage3_local_patch_gate(
            fix_scope=fix_scope,
            fix_pack=normalized_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
        )
        return _Stage3RepairMaterial(
            requested_fix_scope=fix_scope,
            normalized_fix_pack=normalized_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
            local_patch_gate=local_patch_gate,
            binding_issue_count=int(retry_state.prev_binding_issue_count or 0),
        )

    @staticmethod
    def build_validation_material(validation_result: dict | None) -> _Stage3RepairMaterial:
        payload = validation_result if isinstance(validation_result, dict) else {}
        requested_fix_scope = str(payload.get("fix_scope", "") or "")
        normalized_fix_pack = _normalize_stage3_fix_pack(payload)
        advisory_fix_pack = _normalize_stage3_advisory_fix_pack(payload)
        effective_fix_pack = normalized_fix_pack or advisory_fix_pack
        repair_contract = _normalize_stage3_repair_contract(payload, fix_pack=effective_fix_pack)
        scope_authority = _normalize_stage3_scope_authority(payload)
        local_patch_gate = _build_stage3_local_patch_gate(
            fix_scope=requested_fix_scope,
            fix_pack=effective_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
        )
        try:
            binding_issue_count = int(payload.get("binding_prevalidation_issue_count", 0) or 0)
        except (TypeError, ValueError):
            binding_issue_count = 0
        return _Stage3RepairMaterial(
            requested_fix_scope=requested_fix_scope,
            normalized_fix_pack=normalized_fix_pack,
            advisory_fix_pack=advisory_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
            local_patch_gate=local_patch_gate,
            binding_issue_count=binding_issue_count,
            regenerate_only_binding_categories=_extract_stage3_regenerate_only_binding_categories(payload),
        )

    @staticmethod
    def decide_phase2_retry(
        *,
        retry: int,
        retry_state: _ThreePhaseRetryState,
        material: _Stage3RepairMaterial,
        inplace_threshold: int,
    ) -> _Stage3RepairRouteDecision:
        resolved_fix_scope = material.resolved_fix_scope
        inplace_retry_candidate = (
            retry > 0
            and retry_state.previous_best is not None
            and retry_state.prev_reject_score >= inplace_threshold
            and resolved_fix_scope == "inplace"
        )
        inplace_patch_eligible = inplace_retry_candidate and bool(
            material.local_patch_gate.get("local_patch_ready", False)
        )
        contract_block_reason = ""
        if inplace_retry_candidate and not material.local_patch_gate.get("local_patch_ready", False):
            gate_reason = str(material.local_patch_gate.get("reason", "") or "").strip()
            if gate_reason:
                contract_block_reason = f"local_patch_contract:{gate_reason}"
        block_reasons = _build_stage3_retry_plateau_reasons(retry_state)
        if contract_block_reason and contract_block_reason not in block_reasons:
            block_reasons.append(contract_block_reason)
        use_inplace_patch = inplace_patch_eligible and not block_reasons
        return _Stage3RepairRouteDecision(
            effective_fix_scope=resolved_fix_scope or material.normalized_requested_fix_scope,
            resolved_fix_scope=resolved_fix_scope,
            use_inplace_patch=use_inplace_patch,
            inplace_retry_candidate=inplace_retry_candidate,
            block_reasons=list(block_reasons),
            contract_block_reason=contract_block_reason,
        )

    @staticmethod
    def decide_pass_with_fix(
        *,
        material: _Stage3RepairMaterial,
        score: int,
        inplace_threshold: int,
    ) -> _Stage3RepairRouteDecision:
        requested_fix_scope = material.requested_fix_scope
        resolved_fix_scope = material.resolved_fix_scope
        if material.regenerate_only_binding_categories or material.binding_issue_count > 0:
            regenerate_only_reason = (
                _build_stage3_regenerate_only_binding_reason(material.regenerate_only_binding_categories)
                if material.regenerate_only_binding_categories
                else (
                    "Structural binding prevalidation requires regenerate-only repair: "
                    f"unresolved_binding_issue_count={material.binding_issue_count}"
                )
            )
            return _Stage3RepairRouteDecision(
                effective_fix_scope="full",
                resolved_fix_scope=resolved_fix_scope,
                should_break_to_generate=True,
                fix_scope_reasoning=regenerate_only_reason,
                regenerate_only_reason=regenerate_only_reason,
            )
        if requested_fix_scope in ("partial", "full"):
            return _Stage3RepairRouteDecision(
                effective_fix_scope=requested_fix_scope,
                resolved_fix_scope=resolved_fix_scope,
                should_break_to_generate=True,
            )
        if material.local_patch_gate.get("contract_present") and not material.local_patch_gate.get(
            "local_patch_ready", False
        ):
            gate_reason = str(material.local_patch_gate.get("reason", "") or "").strip()
            effective_fix_scope = "partial" if resolved_fix_scope == "partial" else "full"
            return _Stage3RepairRouteDecision(
                effective_fix_scope=effective_fix_scope,
                resolved_fix_scope=resolved_fix_scope,
                should_break_to_generate=True,
                contract_block_reason=gate_reason,
                fix_scope_reasoning=(
                    "Contract-driven local patch gate blocked Blueprint inplace retry: "
                    f"{gate_reason or 'unknown_reason'}"
                ),
            )
        if not material.local_patch_gate.get("contract_present") and not material.local_patch_gate.get(
            "local_patch_ready", False
        ):
            gate_reason = str(material.local_patch_gate.get("reason", "") or "").strip()
            return _Stage3RepairRouteDecision(
                effective_fix_scope="full",
                resolved_fix_scope=resolved_fix_scope,
                should_break_to_generate=True,
                contract_block_reason=gate_reason,
                fix_scope_reasoning=(
                    "Contract-driven local patch gate blocked Blueprint inplace retry: "
                    f"{gate_reason or 'unknown_reason'}"
                ),
            )
        if not requested_fix_scope:
            effective_fix_scope = "inplace" if score >= inplace_threshold else "full"
            return _Stage3RepairRouteDecision(
                effective_fix_scope=effective_fix_scope,
                resolved_fix_scope=resolved_fix_scope,
                should_break_to_generate=effective_fix_scope in ("partial", "full"),
            )
        return _Stage3RepairRouteDecision(
            effective_fix_scope=requested_fix_scope,
            resolved_fix_scope=resolved_fix_scope,
            should_break_to_generate=requested_fix_scope in ("partial", "full"),
        )


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


def _extract_stage3_issue_categories(validation_result: dict | None) -> list[str]:
    if not isinstance(validation_result, dict):
        return []
    issues = validation_result.get("issues", [])
    if not isinstance(issues, list):
        return []

    categories: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        category = str(issue.get("category") or "").strip()
        if not category or category in seen:
            continue
        seen.add(category)
        categories.append(category)
    return categories


def _build_stage3_reject_signature(*, validation_result: dict | None, advisory_only: bool) -> str:
    if not isinstance(validation_result, dict):
        return ""

    fix_scope = str(validation_result.get("fix_scope") or "").strip().lower()
    categories = _extract_stage3_issue_categories(validation_result)
    if not categories:
        raw_binding_categories = validation_result.get("binding_regenerate_only_categories", [])
        if isinstance(raw_binding_categories, list):
            categories = [
                str(category or "").strip() for category in raw_binding_categories if str(category or "").strip()
            ][:4]

    category_token = ",".join(categories[:4]) if categories else "uncategorized"
    advisory_token = "advisory_only" if advisory_only else "substantive"
    scope_token = fix_scope or "none"
    return f"{scope_token}|{advisory_token}|{category_token}"


def _build_stage3_retry_plateau_reasons(retry_state: _ThreePhaseRetryState) -> list[str]:
    reasons: list[str] = []
    reject_origin = str(retry_state.prev_reject_origin or "").strip()
    if reject_origin == "pass_with_fix_unresolved":
        reasons.append("pass_with_fix_unresolved")
    if reject_origin == "quality_gate_reject" or bool(retry_state.prev_quality_gate_reject):
        reasons.append("quality_gate_reopen")
    if retry_state.prev_binding_issue_count > 0:
        reasons.append(f"binding_prevalidation_reopen:{retry_state.prev_binding_issue_count}")
    if (
        retry_state.inplace_reject_streak >= 2
        and retry_state.repeated_reject_score_streak >= 2
        and retry_state.prev_reject_score > 0
    ):
        reasons.append(f"inplace_score_plateau:{retry_state.prev_reject_score}")
    if (
        retry_state.inplace_reject_streak >= 2
        and retry_state.repeated_reject_signature_streak >= 2
        and retry_state.prev_reject_signature
    ):
        reasons.append(f"inplace_signature_plateau:{retry_state.prev_reject_signature}")
    if retry_state.advisory_only_reject_streak >= 2:
        reasons.append("advisory_only_residual_plateau")
    return reasons


def _extract_stage3_regenerate_only_binding_categories(validation_result: dict | None) -> list[str]:
    if not isinstance(validation_result, dict):
        return []
    raw_categories = validation_result.get("binding_prevalidation_categories", [])
    if not isinstance(raw_categories, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in raw_categories:
        category = str(raw or "").strip()
        if not category or category in seen:
            continue
        seen.add(category)
        if category in _STAGE3_REGENERATE_ONLY_BINDING_CATEGORIES:
            normalized.append(category)
    return normalized


def _is_stage3_inplace_alias_reaudit_eligible(
    validation_result: dict | None,
    *,
    requested_fix_scope: str,
    resolved_fix_scope: str,
) -> bool:
    if not isinstance(validation_result, dict):
        return False

    raw_categories = validation_result.get("binding_prevalidation_categories", [])
    if not isinstance(raw_categories, list):
        return False

    categories: list[str] = []
    seen: set[str] = set()
    for raw in raw_categories:
        category = str(raw or "").strip()
        if not category or category in seen:
            continue
        seen.add(category)
        categories.append(category)

    if len(categories) != 1 or categories[0] not in _STAGE3_INPLACE_ALIAS_REAUDIT_CATEGORIES:
        return False

    effective_scope = (
        str(resolved_fix_scope or requested_fix_scope or validation_result.get("fix_scope") or "").strip().lower()
    )
    if effective_scope != "inplace":
        return False

    reasoning = str(validation_result.get("fix_scope_reasoning", "") or "").strip()
    return "Opening-transition alias mismatch is the sole binding category" in reasoning


def _build_stage3_regenerate_only_binding_reason(categories: list[str]) -> str:
    if not categories:
        return ""
    return "Structural binding prevalidation requires regenerate-only repair: " + ", ".join(categories)


def _compact_stage3_contract_tokens(raw: object, *, limit: int = 4, item_limit: int = 120) -> list[str]:
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
    subtype = " ".join(str(source.get("subtype", "") or "").split()).strip()[:80]
    subtypes = _compact_stage3_contract_tokens(source.get("subtypes"), limit=4, item_limit=80)
    provenance = " ".join(str(source.get("provenance", "") or "").split()).strip()[:40]
    provenance_sources = _compact_stage3_contract_tokens(source.get("provenance_sources"), limit=4, item_limit=120)
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
    if subtype:
        normalized["subtype"] = subtype
    if subtypes:
        normalized["subtypes"] = subtypes
    if provenance:
        normalized["provenance"] = provenance
    if provenance_sources:
        normalized["provenance_sources"] = provenance_sources
    return normalized


def _normalize_stage3_advisory_fix_pack(raw_payload: object) -> dict:
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    advisory_fix_pack = payload.get("advisory_fix_pack")
    if not isinstance(advisory_fix_pack, dict):
        return {}
    return _normalize_stage3_fix_pack({"fix_pack": advisory_fix_pack})


def _normalize_stage3_repair_contract(raw_payload: object, *, fix_pack: dict | None = None) -> dict:
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    source = payload.get("repair_contract") if isinstance(payload.get("repair_contract"), dict) else {}
    normalized_fix_pack = fix_pack if isinstance(fix_pack, dict) else _normalize_stage3_fix_pack(payload)

    subtype = " ".join(str(source.get("subtype") or normalized_fix_pack.get("subtype") or "").split()).strip()[:80]
    subtypes = _compact_stage3_contract_tokens(
        source.get("subtypes") or normalized_fix_pack.get("subtypes"),
        limit=4,
        item_limit=80,
    )
    fix_scope = " ".join(str(source.get("fix_scope") or payload.get("fix_scope") or "").split()).strip()[:40]
    repair_scope = " ".join(str(source.get("repair_scope") or payload.get("repair_scope") or "").split()).strip()[:40]
    authoritative_fix_scope = " ".join(
        str(source.get("authoritative_fix_scope") or payload.get("authoritative_fix_scope") or "").split()
    ).strip()[:40]
    provenance = " ".join(str(source.get("provenance") or normalized_fix_pack.get("provenance") or "").split()).strip()[
        :40
    ]
    provenance_sources = _compact_stage3_contract_tokens(
        source.get("provenance_sources") or normalized_fix_pack.get("provenance_sources"),
        limit=4,
        item_limit=120,
    )
    target_kind = " ".join(
        str(source.get("target_kind") or normalized_fix_pack.get("target_kind") or "").split()
    ).strip()[:80]

    normalized: dict = {}
    if subtype:
        normalized["subtype"] = subtype
    elif subtypes:
        normalized["subtype"] = subtypes[0]
    if subtypes and (not subtype or len(subtypes) > 1):
        normalized["subtypes"] = subtypes
    if fix_scope:
        normalized["fix_scope"] = fix_scope
    if repair_scope:
        normalized["repair_scope"] = repair_scope
    if authoritative_fix_scope:
        normalized["authoritative_fix_scope"] = authoritative_fix_scope
    if provenance:
        normalized["provenance"] = provenance
    if provenance_sources:
        normalized["provenance_sources"] = provenance_sources
    if target_kind:
        normalized["target_kind"] = target_kind
    return normalized


def _normalize_stage3_scope_authority(raw_payload: object) -> dict:
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    source = payload.get("scope_authority") if isinstance(payload.get("scope_authority"), dict) else {}
    fix_scope = " ".join(str(source.get("fix_scope") or payload.get("fix_scope") or "").split()).strip()[:40]
    repair_scope = " ".join(str(source.get("repair_scope") or payload.get("repair_scope") or "").split()).strip()[:40]
    authoritative_fix_scope = " ".join(
        str(source.get("authoritative_fix_scope") or payload.get("authoritative_fix_scope") or "").split()
    ).strip()[:40]

    normalized: dict = {}
    if fix_scope:
        normalized["fix_scope"] = fix_scope
    if repair_scope:
        normalized["repair_scope"] = repair_scope
    if authoritative_fix_scope:
        normalized["authoritative_fix_scope"] = authoritative_fix_scope

    widened = source.get("widened")
    if isinstance(widened, bool):
        normalized["widened"] = widened
    elif fix_scope and authoritative_fix_scope:
        normalized["widened"] = fix_scope.lower() != authoritative_fix_scope.lower()
    return normalized


def _build_stage3_local_patch_gate(
    *,
    fix_scope: str = "",
    fix_pack: dict | None = None,
    repair_contract: dict | None = None,
    scope_authority: dict | None = None,
) -> dict:
    normalized_fix_scope = str(fix_scope or "").strip().lower()
    normalized_fix_pack = dict(fix_pack or {}) if isinstance(fix_pack, dict) else {}
    normalized_repair_contract = dict(repair_contract or {}) if isinstance(repair_contract, dict) else {}
    normalized_scope_authority = dict(scope_authority or {}) if isinstance(scope_authority, dict) else {}
    patch_targets = list(normalized_fix_pack.get("patch_targets") or [])
    patch_target_records = list(normalized_fix_pack.get("patch_target_records") or [])
    target_kind = (
        str(
            normalized_fix_pack.get("target_kind")
            or normalized_repair_contract.get("target_kind")
            or (
                patch_target_records[0].get("target_kind")
                if patch_target_records and isinstance(patch_target_records[0], dict)
                else ""
            )
            or ""
        )
        .strip()
        .lower()
    )
    authoritative_fix_scope = (
        str(
            normalized_scope_authority.get("authoritative_fix_scope")
            or normalized_repair_contract.get("authoritative_fix_scope")
            or ""
        )
        .strip()
        .lower()
    )
    repair_scope = (
        str(
            normalized_scope_authority.get("repair_scope")
            or normalized_repair_contract.get("repair_scope")
            or normalized_scope_authority.get("fix_scope")
            or normalized_repair_contract.get("fix_scope")
            or ""
        )
        .strip()
        .lower()
    )
    resolved_fix_scope = authoritative_fix_scope or repair_scope or normalized_fix_scope
    repair_contract_present = bool(
        normalized_repair_contract
        and (
            str(normalized_repair_contract.get("authoritative_fix_scope", "") or "").strip()
            or str(normalized_repair_contract.get("repair_scope", "") or "").strip()
            or str(normalized_repair_contract.get("target_kind", "") or "").strip()
            or str(normalized_repair_contract.get("subtype", "") or "").strip()
            or list(normalized_repair_contract.get("subtypes") or [])
        )
    )
    scope_authority_present = bool(
        normalized_scope_authority
        and (
            str(normalized_scope_authority.get("authoritative_fix_scope", "") or "").strip()
            or str(normalized_scope_authority.get("repair_scope", "") or "").strip()
            or isinstance(normalized_scope_authority.get("widened"), bool)
        )
    )
    contract_present = bool(normalized_fix_pack or repair_contract_present or scope_authority_present)
    patch_target_count = len(patch_targets)
    patch_target_record_count = len(patch_target_records)
    must_fix = list(normalized_fix_pack.get("must_fix") or [])
    success_condition = str(normalized_fix_pack.get("success_condition", "") or "").strip()

    if contract_present:
        if authoritative_fix_scope != "inplace":
            reason = (
                "missing_authoritative_fix_scope"
                if not authoritative_fix_scope
                else f"authoritative_scope:{authoritative_fix_scope}"
            )
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": len(must_fix),
                "has_success_condition": bool(success_condition),
                "reason": reason,
            }
        if resolved_fix_scope != "inplace":
            reason = f"contract_scope:{resolved_fix_scope or 'missing'}"
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": len(must_fix),
                "has_success_condition": bool(success_condition),
                "reason": reason,
            }
        if target_kind not in _STAGE3_LOCAL_PATCH_TARGET_KINDS:
            reason = f"unsupported_target_kind:{target_kind or 'missing'}"
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": len(must_fix),
                "has_success_condition": bool(success_condition),
                "reason": reason,
            }
        if patch_target_count <= 0:
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": 0,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": len(must_fix),
                "has_success_condition": bool(success_condition),
                "reason": "missing_patch_targets",
            }
        if patch_target_record_count <= 0:
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": 0,
                "must_fix_count": len(must_fix),
                "has_success_condition": bool(success_condition),
                "reason": "missing_patch_target_records",
            }
        if not must_fix:
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": 0,
                "has_success_condition": bool(success_condition),
                "reason": "missing_must_fix",
            }
        if not success_condition:
            return {
                "contract_present": True,
                "local_patch_ready": False,
                "resolved_fix_scope": resolved_fix_scope,
                "authoritative_fix_scope": authoritative_fix_scope,
                "repair_scope": repair_scope,
                "target_kind": target_kind,
                "patch_target_count": patch_target_count,
                "patch_target_record_count": patch_target_record_count,
                "must_fix_count": len(must_fix),
                "has_success_condition": False,
                "reason": "missing_success_condition",
            }
        return {
            "contract_present": True,
            "local_patch_ready": True,
            "resolved_fix_scope": resolved_fix_scope,
            "authoritative_fix_scope": authoritative_fix_scope,
            "repair_scope": repair_scope,
            "target_kind": target_kind,
            "patch_target_count": patch_target_count,
            "patch_target_record_count": patch_target_record_count,
            "must_fix_count": len(must_fix),
            "has_success_condition": True,
            "reason": "contract_local_patch_ready",
        }

    return {
        "contract_present": False,
        "local_patch_ready": False,
        "resolved_fix_scope": normalized_fix_scope,
        "authoritative_fix_scope": authoritative_fix_scope,
        "repair_scope": repair_scope,
        "target_kind": target_kind,
        "patch_target_count": patch_target_count,
        "patch_target_record_count": patch_target_record_count,
        "must_fix_count": len(must_fix),
        "has_success_condition": bool(success_condition),
        "reason": "missing_local_contract",
    }


def _build_stage3_fix_pack_guidance(fix_pack: dict | None) -> str:
    payload = fix_pack if isinstance(fix_pack, dict) else {}
    if not payload:
        return ""

    lines: list[str] = [
        "- authoritative_scope: listed patch targets are authoritative; preserve untouched scenes, entity names, chronology, and arc shell.",
        "- patch_mode: edit the anchored span first; do not rename or broaden scope unless the contract explicitly requires it.",
    ]
    patch_targets = list(payload.get("patch_targets") or [])
    if patch_targets:
        lines.append("- patch_targets: " + ", ".join(str(item) for item in patch_targets[:6]))
    patch_target_records = list(payload.get("patch_target_records") or [])
    if patch_target_records:
        record_lines: list[str] = []
        for record in patch_target_records[:3]:
            if not isinstance(record, dict):
                continue
            parts = [str(record.get("summary") or "").strip()]
            scene_id = str(record.get("scene_id") or "").strip()
            field_path = str(record.get("field_path") or "").strip()
            target_kind = str(record.get("target_kind") or "").strip()
            patch_target_id = str(record.get("patch_target_id") or "").strip()
            detail = ", ".join(part for part in (scene_id, field_path, target_kind, patch_target_id) if part)
            if detail:
                parts.append(f"({detail})")
            text_anchor = record.get("text_anchor")
            if isinstance(text_anchor, dict):
                anchor_bits = [
                    str(text_anchor.get("old_text") or "").strip()[:60],
                    str(text_anchor.get("anchor_before") or "").strip()[:60],
                    str(text_anchor.get("anchor_after") or "").strip()[:60],
                ]
                anchor_text = " / ".join(bit for bit in anchor_bits if bit)
            else:
                anchor_text = str(text_anchor or "").strip()[:80]
            if anchor_text:
                parts.append(f"anchor={anchor_text}")
            text = " ".join(part for part in parts if part).strip()
            if text:
                record_lines.append(text)
        if record_lines:
            lines.append("- patch_target_records: " + " | ".join(record_lines))
    must_fix = list(payload.get("must_fix") or [])
    if must_fix:
        lines.append("- must_fix: " + " | ".join(str(item) for item in must_fix[:4]))
    do_not_regress = list(payload.get("do_not_regress") or [])
    if do_not_regress:
        lines.append("- do_not_regress: " + " | ".join(str(item) for item in do_not_regress[:4]))
    success_condition = str(payload.get("success_condition", "") or "").strip()
    if success_condition:
        lines.append("- success_condition: " + success_condition)
    evidence_summary = str(payload.get("evidence_summary", "") or "").strip()
    if evidence_summary:
        lines.append("- evidence_summary: " + evidence_summary)
    if not lines:
        return ""
    return "[Stage3 partial-fix contract]\n" + "\n".join(lines)


def _build_stage3_partial_fix_eval(
    *,
    fix_pack: dict | None,
    patch_round: int,
    verdict: str = "",
    fallback_reason: str = "",
) -> dict:
    payload = fix_pack if isinstance(fix_pack, dict) else {}
    patch_target_records = list(payload.get("patch_target_records") or [])
    target_kind = str(payload.get("target_kind", "") or "").strip()
    normalized_verdict = str(verdict or "").strip().upper()
    must_fix_resolved = None
    do_not_regress_held = None
    success_condition_met = None
    if normalized_verdict in {"PASS", "PASS_WITH_WARNING"}:
        must_fix_resolved = True
        do_not_regress_held = True
        success_condition_met = True
    elif normalized_verdict == "PASS_WITH_FIX":
        must_fix_resolved = False
        success_condition_met = False
    elif normalized_verdict == "REJECT":
        must_fix_resolved = False
        do_not_regress_held = False
        success_condition_met = False
    return build_partial_fix_eval(
        patch_round=patch_round,
        is_patch_attempt=True,
        patch_target_records=patch_target_records,
        target_kind=target_kind,
        fallback_reason=fallback_reason,
        must_fix_resolved=must_fix_resolved,
        do_not_regress_held=do_not_regress_held,
        success_condition_met=success_condition_met,
    )


class ThreePhaseBlueprintRuntime:
    """Owns the per-episode three-phase blueprint pipeline."""

    def __init__(self, owner: "ThreePhaseBlueprintGenerator") -> None:
        self.owner = owner

    @staticmethod
    def _preview_feedback_lines(feedback: str, *, max_items: int = 3) -> list[str]:
        lines: list[str] = []
        seen: set[str] = set()
        for raw_line in str(feedback or "").splitlines():
            line = raw_line.strip().lstrip("-").strip()
            if not line or line in seen:
                continue
            seen.add(line)
            lines.append(line)
            if len(lines) >= max_items:
                break
        return lines

    @staticmethod
    def _preview_issue_lines(issues, *, max_items: int = 3) -> list[str]:
        if not isinstance(issues, list):
            return []
        lines: list[str] = []
        seen: set[str] = set()
        for issue in issues:
            if isinstance(issue, dict):
                severity = str(issue.get("severity", "") or "").strip()
                category = str(issue.get("category", "") or "").strip()
                text = str(issue.get("issue", "") or "").strip()
                parts = [part for part in (severity, category, text) if part]
                line = " | ".join(parts)
            else:
                line = str(issue or "").strip()
            if not line or line in seen:
                continue
            seen.add(line)
            lines.append(line)
            if len(lines) >= max_items:
                break
        return lines

    def _log_operator_retry_context(
        self,
        *,
        title: str,
        level: str = "info",
        meta: dict | None = None,
        feedback: str = "",
        issues=None,
        fix_scope: str = "",
    ) -> None:
        owner = self.owner
        payload = meta or {}
        self._emit_operator_progress(owner, title, level=level, meta=payload, force_console=True)
        if fix_scope:
            self._emit_operator_progress(
                owner, f"      fix_scope: {fix_scope}", level=level, meta=payload, force_console=True
            )
        for line in self._preview_feedback_lines(feedback):
            self._emit_operator_progress(owner, f"      사유: {line}", level=level, meta=payload, force_console=True)
        for line in self._preview_issue_lines(issues):
            self._emit_operator_progress(owner, f"      이슈: {line}", level=level, meta=payload, force_console=True)

    @staticmethod
    def _force_console_progress(message: str) -> None:
        text = str(message or "").strip()
        if not text:
            return
        try:
            sys.stderr.write(f"\n{text}\n")
            sys.stderr.flush()
        except Exception:
            pass

    def _emit_operator_progress(
        self,
        owner,
        message: str,
        *,
        level: str = "info",
        meta: dict | None = None,
        force_console: bool = False,
    ) -> None:
        payload = dict(meta or {})
        payload.setdefault("emit_console", True)
        owner._operator_log(message, level=level, meta=payload)
        if force_console:
            self._force_console_progress(message)

    @staticmethod
    def _format_operator_elapsed(elapsed_seconds: float) -> str:
        total_seconds = max(0, int(elapsed_seconds))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _call_with_operator_heartbeat(
        self,
        *,
        title: str,
        meta: dict | None,
        fn,
        interval_seconds: float = 30.0,
    ):
        owner = self.owner
        payload = dict(meta or {})
        started_at = time.perf_counter()
        stop_event = threading.Event()

        self._emit_operator_progress(owner, f"{title} 시작", meta=payload, force_console=True)

        def _heartbeat() -> None:
            heartbeat_index = 0
            while not stop_event.wait(interval_seconds):
                heartbeat_index += 1
                elapsed_text = self._format_operator_elapsed(time.perf_counter() - started_at)
                heartbeat_meta = dict(payload)
                heartbeat_meta["heartbeat_index"] = heartbeat_index
                heartbeat_meta["elapsed_text"] = elapsed_text
                self._emit_operator_progress(
                    owner,
                    f"{title} 대기 중... ({elapsed_text})",
                    meta=heartbeat_meta,
                    force_console=True,
                )

        heartbeat_thread = threading.Thread(target=_heartbeat, name="stage3_operator_heartbeat", daemon=True)
        heartbeat_thread.start()

        try:
            result = fn()
        except Exception:
            elapsed_text = self._format_operator_elapsed(time.perf_counter() - started_at)
            stop_event.set()
            heartbeat_thread.join(timeout=0.1)
            error_meta = dict(payload)
            error_meta["elapsed_text"] = elapsed_text
            self._emit_operator_progress(
                owner,
                f"{title} 예외 종료 ({elapsed_text})",
                level="warning",
                meta=error_meta,
                force_console=True,
            )
            raise

        elapsed_text = self._format_operator_elapsed(time.perf_counter() - started_at)
        stop_event.set()
        heartbeat_thread.join(timeout=0.1)
        done_meta = dict(payload)
        done_meta["elapsed_text"] = elapsed_text
        self._emit_operator_progress(owner, f"{title} 완료 ({elapsed_text})", meta=done_meta, force_console=True)
        return result

    def _bootstrap_runtime_context(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        semantic_context: str,
        external_feedback: str,
        protagonist_config: dict | None,
    ) -> _ThreePhaseRuntimeBootstrap:
        owner = self.owner
        genre = "wuxia"
        resolved_protagonist = dict(protagonist_config or {})

        try:
            bible = owner.context.db.load_anchor("bible") if getattr(owner.context, "db", None) else None
            if isinstance(bible, dict):
                genre = str(bible.get("_genre") or genre)
                if not resolved_protagonist:
                    resolved_protagonist = dict(
                        (bible.get("MasterBible", {}) or {}).get("protagonist_config", {})
                        or bible.get("protagonist_config", {})
                        or {}
                    )
        except Exception as exc:
            logging.warning(" [V60.80] bible bootstrap 로드 실패: %s", str(exc)[:80])

        if not resolved_protagonist:
            try:
                master_bible = getattr(owner.context, "master_bible", {}) or {}
                resolved_protagonist = dict(
                    (master_bible.get("MasterBible", {}) or {}).get("protagonist_config", {})
                    or master_bible.get("protagonist_config", {})
                    or {}
                )
            except Exception:
                resolved_protagonist = {}

        initial_feedback_parts = [str(semantic_context or "").strip(), str(external_feedback or "").strip()]
        initial_feedback = "\n\n".join(part for part in initial_feedback_parts if part)
        if external_feedback:
            logging.info(" [V60.80] 외부 피드백 주입 (%d자)", len(str(external_feedback)))

        pipeline_result = {
            "ep_num": ep_num,
            "arc_no": (arc_data or {}).get("arc_no", 0),
            "retries": 0,
            "patch_fallback": False,
            "asp_used": False,
            "quality_gate_failed": False,
            "quality_risk": False,
            "revision_required": False,
            "phases": {
                "constraint": {"status": "pending"},
                "generate": {"status": "pending"},
                "validate": {"status": "pending"},
            },
        }
        owner.stats["total_attempts"] += 1
        return _ThreePhaseRuntimeBootstrap(
            genre=genre,
            protagonist_config=resolved_protagonist,
            pipeline_result=pipeline_result,
            initial_feedback=initial_feedback,
            retry_state=_ThreePhaseRetryState(),
        )

    def _build_retry_strategy_feedback(self, retry_state: _ThreePhaseRetryState) -> str:
        parts: list[str] = []
        if retry_state.prev_reject_strategy:
            parts.append(f"[이전 당선 전략]\n{retry_state.prev_reject_strategy}")
        if retry_state.prev_selection_reason:
            parts.append(f"[이전 선택 근거]\n{retry_state.prev_selection_reason}")
        if retry_state.prev_reject_feedback:
            parts.append(f"[이전 REJECT 피드백]\n{retry_state.prev_reject_feedback}")
        if retry_state.prev_fix_scope:
            parts.append(f"[Director fix_scope]\n{retry_state.prev_fix_scope}")
        if retry_state.prev_local_patch_gate:
            local_patch_gate = retry_state.prev_local_patch_gate
            parts.append(
                "[Local patch gate]\n"
                + " | ".join(
                    part
                    for part in (
                        f"scope={str(local_patch_gate.get('resolved_fix_scope', '') or '').strip()}",
                        f"target_kind={str(local_patch_gate.get('target_kind', '') or '').strip()}",
                        f"ready={bool(local_patch_gate.get('local_patch_ready', False))}",
                        f"reason={str(local_patch_gate.get('reason', '') or '').strip()}",
                    )
                    if part and not part.endswith("=")
                )
            )
        if retry_state.prev_validation_warnings:
            warning_lines = "\n".join(f"- {warning}" for warning in retry_state.prev_validation_warnings[:10])
            parts.append(f"[이전 검증 경고]\n{warning_lines}")
        if retry_state.prev_score_breakdown:
            parts.append(
                "[이전 점수 분해]\n" + json.dumps(retry_state.prev_score_breakdown, ensure_ascii=False, indent=2)[:1200]
            )
        return "\n\n".join(part for part in parts if part)

    def _resolve_constraint_block(
        self,
        *,
        retry: int,
        ep_num: int,
        arc_data: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        genre: str,
        pipeline_result: dict,
        retry_state: _ThreePhaseRetryState,
        prev_manuscripts_text: str = "",
    ) -> dict:
        owner = self.owner
        reused_cache = retry > 0 and retry_state.cached_constraint_block is not None
        if reused_cache:
            constraint_block = retry_state.cached_constraint_block or {}
            owner._operator_log(
                "[Phase 1] 제약 블록 재사용",
                meta={"phase": "constraint", "retry_index": retry + 1, "cached": True},
            )
        else:
            # [pre-rerun] 직전 원고 말미 500자를 시간 진실 소스로 전달
            prev_manuscript_ending = ""
            if prev_manuscripts_text:
                prev_manuscript_ending = prev_manuscripts_text.strip()[-500:]
            constraint_block = self._call_with_operator_heartbeat(
                title="[Phase 1] 제약 수집",
                meta={
                    "phase": "constraint",
                    "retry_index": retry + 1,
                    "cached": False,
                    "previous_blueprint_present": bool(prev_blueprint),
                    "blueprint_window_count": len(prev_blueprints or []),
                    "prev_manuscript_ending_chars": len(prev_manuscript_ending),
                },
                fn=lambda: owner.constraint_compiler.compile(
                    arc_data=arc_data,
                    ep_num=ep_num,
                    prev_blueprint=prev_blueprint,
                    prev_blueprints=prev_blueprints,
                    genre=genre,
                    prev_manuscript_ending=prev_manuscript_ending,
                ),
            )
            retry_state.cached_constraint_block = constraint_block

        pipeline_result["phases"]["constraint"] = {
            "status": "complete",
            "cached": reused_cache,
            "arc_no": constraint_block.get("arc_no", (arc_data or {}).get("arc_no", 0)),
            "arc_position": constraint_block.get("arc_position", ""),
        }
        owner.stats["phase1_complete"] += 1
        return constraint_block

    def _append_asp_candidate(
        self,
        *,
        retry: int,
        ep_num: int,
        attempt_feedback: str,
        best_blueprint: dict | None,
        all_candidates: list[dict],
        adversarial_self_play,
        pipeline_result: dict,
    ) -> tuple[dict | None, list[dict]]:
        owner = self.owner
        if retry < 2 or not adversarial_self_play or not all_candidates:
            return best_blueprint, all_candidates

        try:
            asp_target = all_candidates[0]
            asp_result = adversarial_self_play.generate_with_adversary(
                initial_content=json.dumps(asp_target, ensure_ascii=False),
                content_type="blueprint",
                context={"ep_num": ep_num, "director_feedback": attempt_feedback},
            )
            asp_output = getattr(asp_result, "final_output", "") if asp_result else ""
            if not asp_output:
                return best_blueprint, all_candidates

            asp_blueprint = owner.ensemble._extract_json_robust(asp_output)
            if not isinstance(asp_blueprint, dict) or not asp_blueprint:
                try:
                    asp_blueprint = json.loads(asp_output)
                except (json.JSONDecodeError, TypeError, ValueError):
                    asp_blueprint = {}
            if not isinstance(asp_blueprint, dict) or not asp_blueprint:
                return best_blueprint, all_candidates

            original_meta = asp_target.get("_ensemble_meta", {})
            if original_meta and not asp_blueprint.get("_ensemble_meta"):
                asp_blueprint["_ensemble_meta"] = original_meta
            all_candidates[0] = asp_blueprint
            if best_blueprint is None or best_blueprint is asp_target:
                best_blueprint = asp_blueprint
            pipeline_result["asp_used"] = True
            logging.info("✅ [ASP] Stage3 Blueprint 교정 적용 (retry=%d)", retry)
        except Exception as exc:
            logging.warning(f"[SilentPass:Stage3:ASP] {exc!s:.120}")

        return best_blueprint, all_candidates

    def _handle_phase2_generation_failure(
        self,
        *,
        retry: int,
        ep_num: int,
        arc_data: dict,
        pipeline_result: dict,
        max_retries: int,
    ) -> _ThreePhasePhase2Result:
        owner = self.owner
        worker_error_types = getattr(owner.ensemble, "last_error_types", None) or []
        error_type = getattr(owner.ensemble, "last_error_type", None)
        if AgentErrorType.CANDIDATE_DISQUALIFIED in worker_error_types:
            error_type = AgentErrorType.CANDIDATE_DISQUALIFIED
        elif AgentErrorType.SCHEMA_INCOMPATIBLE in worker_error_types:
            error_type = AgentErrorType.SCHEMA_INCOMPATIBLE
        elif not error_type and worker_error_types:
            non_unknown = [
                candidate for candidate in worker_error_types if candidate and candidate != AgentErrorType.UNKNOWN
            ]
            error_type = non_unknown[0] if non_unknown else worker_error_types[0]
        pipeline_result["phases"]["generate"] = {"status": "failed"}
        if error_type:
            pipeline_result["phases"]["generate"]["error_type"] = error_type
            pipeline_result["failure_reason"] = error_type

        operator_feedback = "Ensemble 생성 실패. 다시 시도합니다."
        if error_type == AgentErrorType.SCHEMA_INCOMPATIBLE:
            operator_feedback = "schema_incompatible로 즉시 중단합니다."
        elif error_type == AgentErrorType.CANDIDATE_DISQUALIFIED:
            operator_feedback = "replay/authority/구조 계약 미달 후보만 생성되어 재시도합니다."

        logging.warning("❌ [Phase 2] Ensemble 생성 실패")
        self._log_operator_retry_context(
            title=f"[Phase 2] 후보 생성 실패 - retry {retry + 1}/{max_retries + 1}",
            level="warning",
            meta={
                "phase": "generate",
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "error_category": str(error_type or "generate_failed"),
            },
            feedback=operator_feedback,
        )
        if error_type == AgentErrorType.SCHEMA_INCOMPATIBLE:
            return _ThreePhasePhase2Result(None, [], should_break=True)

        owner._record_intermediate_reject(
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
            reject_reason=(
                "replay/authority/구조 계약 미달 후보만 생성됨. 다시 시도하세요."
                if error_type == AgentErrorType.CANDIDATE_DISQUALIFIED
                else "Ensemble 생성 실패. 다시 시도하세요."
            ),
            event_tag=(
                "generate_candidate_disqualified"
                if error_type == AgentErrorType.CANDIDATE_DISQUALIFIED
                else "generate_failed"
            ),
        )
        return _ThreePhasePhase2Result(None, [], should_continue=True)

    def _run_phase2_generation(
        self,
        *,
        retry: int,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        protagonist_name: str,
        protagonist_config: dict,
        state_tracker,
        prev_manuscripts_text: str,
        attempt_feedback: str,
        strategy_feedback: str,
        adversarial_self_play,
        pipeline_result: dict,
        retry_state: _ThreePhaseRetryState,
        max_retries: int,
    ) -> _ThreePhasePhase2Result:
        owner = self.owner
        best_blueprint: dict | None = None
        all_candidates: list[dict] = []
        rejected_strategy = retry_state.prev_reject_strategy if retry > 0 else ""
        single_strategy = ""
        repair_material = _Stage3RepairRouter.build_retry_material(retry_state)
        repair_route = _Stage3RepairRouter.decide_phase2_retry(
            retry=retry,
            retry_state=retry_state,
            material=repair_material,
            inplace_threshold=int(_threshold("patch_mode.inplace_below", PatchModeThresholds.INPLACE)),
        )
        resolved_fix_scope = repair_route.resolved_fix_scope or repair_material.normalized_requested_fix_scope

        if retry > 0 and resolved_fix_scope == "partial" and rejected_strategy:
            single_strategy = rejected_strategy

        if repair_route.inplace_retry_candidate and repair_route.block_reasons:
            logging.info(
                "[PF-EE] skip Stage3 inplace patch retry; reasons=%s",
                ", ".join(repair_route.block_reasons),
            )
            pipeline_result["inplace_plateau_block_reasons"] = list(repair_route.block_reasons)
            owner._operator_log(
                "[Phase 2] inplace patch blocked; switch back to full_ensemble",
                meta={
                    "phase": "generate",
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "mode": "full_ensemble",
                    "inplace_blocked": True,
                    "inplace_block_reasons": list(repair_route.block_reasons),
                    "prev_reject_score": retry_state.prev_reject_score,
                    "fix_scope": resolved_fix_scope or "",
                },
            )
        if repair_route.use_inplace_patch:
            logging.info(" [Patch Mode] retry=%d blueprint in-place patch 시도", retry)
            owner._operator_log(
                (
                    f"[Phase 2] patch mode 진입 "
                    f"(retry={retry + 1}/{max_retries + 1}, prev_score={retry_state.prev_reject_score}, "
                    f"fix_scope={resolved_fix_scope or '-'})"
                ),
                meta={
                    "phase": "generate",
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "mode": "inplace_patch",
                    "prev_reject_score": retry_state.prev_reject_score,
                    "fix_scope": resolved_fix_scope or "",
                },
            )
            try:
                best_blueprint = self._call_with_operator_heartbeat(
                    title="[Phase 2] in-place patch",
                    meta={
                        "phase": "generate",
                        "retry_index": retry + 1,
                        "max_retries": max_retries + 1,
                        "mode": "inplace_patch",
                        "feedback_chars": len(str(retry_state.prev_reject_feedback or "")),
                    },
                    fn=lambda: owner._inplace_patch_blueprint(
                        original_blueprint=retry_state.previous_best,
                        director_feedback=retry_state.prev_reject_feedback,
                        ep_num=ep_num,
                        arc_data=arc_data,
                        normalized_fix_pack=repair_material.effective_fix_pack,
                    ),
                )
            except Exception:
                logging.exception("[Patch Mode] Blueprint in-place patch 예외")
                best_blueprint = None

            if best_blueprint:
                all_candidates = [best_blueprint]
                pipeline_result["patch_fallback"] = False
            else:
                pipeline_result["patch_fallback"] = True
                logging.info("[Patch Mode] Blueprint in-place 패치 실패 → full rewrite 폴백")

        if not all_candidates:
            try:
                ensemble_kwargs = {
                    "ep_num": ep_num,
                    "arc_data": arc_data,
                    "constraint_block": constraint_block,
                    "prev_blueprint": prev_blueprint,
                    "feedback": attempt_feedback,
                    "strategy_specific_feedback": strategy_feedback,
                    "rejected_strategy": rejected_strategy,
                    "protagonist_name": protagonist_name,
                    "protagonist_config": protagonist_config,
                    "state_tracker": state_tracker,
                    "prev_blueprints": prev_blueprints,
                    "prev_manuscripts_text": prev_manuscripts_text,
                }
                if single_strategy:
                    ensemble_kwargs["single_strategy"] = single_strategy
                generation_mode = f"single_strategy:{single_strategy}" if single_strategy else "full_ensemble"
                best_blueprint, all_candidates = self._call_with_operator_heartbeat(
                    title=f"[Phase 2] 후보 생성 ({generation_mode})",
                    meta={
                        "phase": "generate",
                        "retry_index": retry + 1,
                        "max_retries": max_retries + 1,
                        "mode": generation_mode,
                        "feedback_chars": len(str(attempt_feedback or "")),
                        "strategy_feedback_chars": len(str(strategy_feedback or "")),
                        "previous_blueprint_present": bool(prev_blueprint),
                        "blueprint_window_count": len(prev_blueprints or []),
                        "prev_manuscript_chars": len(str(prev_manuscripts_text or "")),
                    },
                    fn=lambda: owner.ensemble.generate_ensemble(**ensemble_kwargs),
                )
            except Exception:
                logging.exception("[Phase 2] generate_ensemble 예외")
                best_blueprint, all_candidates = None, []

        if not all_candidates:
            return self._handle_phase2_generation_failure(
                retry=retry,
                ep_num=ep_num,
                arc_data=arc_data,
                pipeline_result=pipeline_result,
                max_retries=max_retries,
            )

        if best_blueprint is None and all_candidates:
            best_blueprint = all_candidates[0]

        best_blueprint, all_candidates = self._append_asp_candidate(
            retry=retry,
            ep_num=ep_num,
            attempt_feedback=attempt_feedback,
            best_blueprint=best_blueprint,
            all_candidates=all_candidates,
            adversarial_self_play=adversarial_self_play,
            pipeline_result=pipeline_result,
        )

        current_strategy = ""
        if isinstance(best_blueprint, dict):
            current_strategy = best_blueprint.get("_ensemble_meta", {}).get("strategy", "")
        pipeline_result.pop("failure_reason", None)
        pipeline_result["phases"]["generate"] = {
            "status": "complete",
            "candidates_count": len(all_candidates),
            "selected_strategy": current_strategy or "unknown",
        }
        owner.stats["phase2_complete"] += 1
        logging.info("✅ [Phase 2] Ensemble 완료 — %d개 후보 → Director 선택 대기", len(all_candidates))
        owner._operator_log(
            f"[Phase 2] 후보 생성 완료 ({len(all_candidates)}개, strategy={current_strategy or 'unknown'})",
            meta={
                "phase": "generate",
                "candidates_count": len(all_candidates),
                "selected_strategy": current_strategy or "unknown",
            },
        )
        return _ThreePhasePhase2Result(best_blueprint, all_candidates)

    def _run_phase3_validation(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        best_blueprint: dict | None,
        all_candidates: list[dict],
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        db,
        prev_hud: dict | None,
        retry_state: _ThreePhaseRetryState,
        pipeline_result: dict,
        retry: int,
        max_retries: int,
    ) -> _ThreePhasePhase3ValidationResult:
        owner = self.owner

        logging.info("[Phase 3] Director compare + judge")
        owner._operator_log("[Phase 3] Director compare + judge", meta={"phase": "validate"})

        continuity_reject = self._maybe_reject_phase3_continuity(
            ep_num=ep_num,
            arc_data=arc_data,
            best_blueprint=best_blueprint,
            director=director,
            db=db,
            retry_state=retry_state,
            retry=retry,
            max_retries=max_retries,
        )
        if continuity_reject is not None:
            return continuity_reject

        validation = self._run_phase3_validation_envelope(
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            best_blueprint=best_blueprint,
            all_candidates=all_candidates,
            director=director,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            prev_hud=prev_hud,
        )
        # [IFC] Scene obligation metadata completeness — affects handoff quality
        ifc_penalty = self._enforce_scene_obligation_completeness(validation.best_blueprint)
        effective_score = max(0, validation.score - ifc_penalty)

        self._record_phase3_validation_payload(
            pipeline_result=pipeline_result,
            validation_result=validation.validation_result,
            verdict=validation.verdict,
            selected_strategy=validation.selected_strategy,
            all_candidates=all_candidates,
            score=validation.score,
        )
        validate_phase = pipeline_result.setdefault("phases", {}).setdefault("validate", {})
        validate_phase["raw_score"] = validation.score
        validate_phase["ifc_penalty"] = ifc_penalty
        validate_phase["effective_score"] = effective_score
        self._record_phase3_contradictions(
            pipeline_result=pipeline_result,
            validation_result=validation.validation_result,
        )

        validation_result = validation.validation_result
        verdict = self._apply_phase3_quality_gate(
            verdict=validation.verdict,
            score=effective_score,
            validation_result=validation_result,
        )
        if validation.verdict == "PASS" and verdict == "REJECT":
            verdict, validation_result = self._annotate_or_accept_terminal_quality_gate_result(
                validation_verdict=validation.verdict,
                verdict=verdict,
                validation_result=validation_result,
                effective_score=effective_score,
                raw_score=validation.score,
                ifc_penalty=ifc_penalty,
                retry=retry,
                max_retries=max_retries,
                best_blueprint=validation.best_blueprint,
                pipeline_result=pipeline_result,
            )
            if verdict == "REJECT":
                self._log_operator_retry_context(
                    title=(
                        f"[QualityGate] effective_score={effective_score} "
                        f"(raw={validation.score}, ifc_penalty={ifc_penalty}) < threshold -> REJECT"
                    ),
                    level="warning",
                    meta={
                        "phase": "validate",
                        "score": effective_score,
                        "raw_score": validation.score,
                        "ifc_penalty": ifc_penalty,
                        "error_category": "quality_gate",
                    },
                    feedback=validation.validation_result.get("verdict_reason", "")
                    or validation.validation_result.get("feedback", ""),
                    issues=validation.validation_result.get("issues", []),
                    fix_scope=str(validation.validation_result.get("fix_scope", "") or ""),
                )

        return _ThreePhasePhase3ValidationResult(
            best_blueprint=validation.best_blueprint,
            validation_result=validation_result,
            verdict=verdict,
            score=effective_score,
            selected_strategy=validation.selected_strategy,
        )

    def _enforce_scene_obligation_completeness(self, blueprint: dict | None) -> int:
        """[IFC] Enforce blueprint scene obligation metadata completeness.

        Returns a bounded score penalty (0-15) that the quality gate applies.
        When more than half of scenes lack goal/summary, the penalty is large
        enough to push borderline-PASS blueprints into REJECT/retry.

        This is bounded and pragmatic:
        - 0 missing → 0 penalty
        - 1 missing out of many → 3 penalty (warning-level)
        - majority missing → up to 15 penalty (material handoff impact)
        """
        if not isinstance(blueprint, dict):
            return 0
        scenes = blueprint.get("scene_breakdown", {})
        if not isinstance(scenes, dict) or not scenes:
            return 0

        total = 0
        missing_count = 0
        missing_keys: list[str] = []
        for key, scene in scenes.items():
            if not isinstance(scene, dict):
                continue
            total += 1
            has_goal = bool(scene.get("goal") or scene.get("summary"))
            if not has_goal:
                missing_count += 1
                missing_keys.append(str(key))

        if missing_count == 0 or total == 0:
            return 0

        missing_ratio = missing_count / total

        # Bounded penalty: 3 per missing scene, capped at 15
        penalty = min(15, missing_count * 3)

        level = "warning" if missing_ratio < 0.5 else "error"
        logging.warning(
            "[IFC] Blueprint scene obligation metadata incomplete: %d/%d scenes missing goal/summary (%s) → penalty=%d",
            missing_count,
            total,
            ", ".join(missing_keys[:5]),
            penalty,
        )
        self.owner._operator_log(
            f"   {'⚠️' if level == 'warning' else '❌'} [IFC] 씬 메타데이터 불완전: "
            f"{missing_count}/{total} 씬에 goal/summary 없음 ({', '.join(missing_keys[:5])}) → 점수 -{penalty}",
            level=level,
            meta={"phase": "validate", "ifc_incomplete_scenes": missing_count, "ifc_penalty": penalty},
        )
        return penalty

    def _maybe_reject_phase3_continuity(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        best_blueprint: dict | None,
        director,
        db,
        retry_state: _ThreePhaseRetryState,
        retry: int,
        max_retries: int,
    ) -> _ThreePhasePhase3ValidationResult | None:
        owner = self.owner
        if not (director and db and ep_num > 1):
            return None

        continuity_result = self._call_with_operator_heartbeat(
            title="[Phase 3] 연속성 사전검사",
            meta={"phase": "validate", "retry_index": retry + 1, "max_retries": max_retries + 1},
            fn=lambda: director.check_blueprint_continuity_with_cache(
                new_blueprint=best_blueprint,
                ep_num=ep_num,
                db=db,
                limit=10,
            ),
        )
        if continuity_result.get("decision") != "REJECT":
            return None

        continuity_feedback = continuity_result.get("feedback", "")
        owner.stats["phase3_reject"] += 1
        retry_state.prev_reject_feedback = continuity_feedback
        retry_state.prev_reject_score = 0
        retry_state.prev_fix_scope = ""
        retry_state.prev_fix_pack = {}
        retry_state.prev_repair_contract = {}
        retry_state.prev_scope_authority = {}
        retry_state.prev_local_patch_gate = {}
        retry_state.prev_selection_reason = continuity_feedback
        retry_state.prev_validation_warnings = [continuity_feedback]
        if best_blueprint:
            retry_state.previous_best = best_blueprint
        logging.warning("[V61.5] Continuity check reject")
        self._log_operator_retry_context(
            title=f"[Phase 3] 연속성 검증 REJECT - retry {retry + 1}/{max_retries + 1}",
            level="warning",
            meta={
                "phase": "validate",
                "score": 0,
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "error_category": "continuity_reject",
            },
            feedback=continuity_feedback,
        )
        owner._record_intermediate_reject(
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
            reject_reason=continuity_feedback or "blueprint continuity reject",
            event_tag="continuity_reject",
        )
        return _ThreePhasePhase3ValidationResult(
            best_blueprint=best_blueprint,
            validation_result={},
            verdict="REJECT",
            score=0,
            selected_strategy="",
            should_continue=True,
        )

    def _run_phase3_validation_envelope(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        best_blueprint: dict | None,
        all_candidates: list[dict],
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
    ) -> _ThreePhaseValidationEnvelope:
        owner = self.owner
        verdict, validation_result = self._call_with_operator_heartbeat(
            title="[Phase 3] Director compare + judge",
            meta={
                "phase": "validate",
                "candidate_count": len(all_candidates or []),
                "previous_blueprint_present": bool(prev_blueprint),
            },
            fn=lambda: owner.validator.validate(
                blueprint=best_blueprint,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                director=director,
                working_ep=ep_num,
                arc_idx=arc_idx,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
                all_candidates=all_candidates,
                prev_hud=prev_hud,
            ),
        )

        if validation_result.get("selected_blueprint"):
            best_blueprint = validation_result["selected_blueprint"]
            selected_idx = validation_result.get("selected_index", 0)
            logging.info(f"[V60.85] Director selected candidate {selected_idx + 1}")
            owner._operator_log(
                f"[Phase 3] Director selected candidate {selected_idx + 1}",
                meta={"phase": "validate", "selected_index": selected_idx + 1},
            )

        selected_meta = best_blueprint.get("_ensemble_meta", {}) if isinstance(best_blueprint, dict) else {}
        selected_strategy = selected_meta.get("strategy", "")
        score_raw = validation_result.get("score", 0)
        try:
            score = int(score_raw)
        except (ValueError, TypeError):
            score = 0
        return _ThreePhaseValidationEnvelope(
            best_blueprint=best_blueprint,
            validation_result=validation_result,
            verdict=verdict,
            selected_strategy=selected_strategy,
            score=score,
        )

    def _record_phase3_validation_payload(
        self,
        *,
        pipeline_result: dict,
        validation_result: dict,
        verdict: str,
        selected_strategy: str,
        all_candidates: list[dict],
        score: int,
    ) -> None:
        validation_selection_reason = str(
            validation_result.get("selection_reason")
            or validation_result.get("summary")
            or validation_result.get("comparison_notes", "")
            or ""
        ).strip()
        validation_verdict_reason = str(
            validation_result.get("verdict_reason")
            or validation_result.get("summary")
            or validation_result.get("feedback", "")
            or validation_selection_reason
            or ""
        ).strip()
        validation_quality_risk = bool(validation_result.get("quality_risk", False))
        validation_revision_required = bool(
            validation_result.get("revision_required", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )
        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
            "confidence": validation_result.get("confidence", 0),
            "score": validation_result.get("score", 0),
            "phase": validation_result.get("phase", "unknown"),
            "selected_index": validation_result.get("selected_index", 0),
            "comparison_notes": validation_result.get("comparison_notes", ""),
            "selection_reason": validation_selection_reason,
            "verdict_reason": validation_verdict_reason,
            "fix_scope": validation_result.get("fix_scope", ""),
            "fix_scope_reasoning": validation_result.get("fix_scope_reasoning", ""),
            "quality_risk": validation_quality_risk,
            "revision_required": validation_revision_required,
            "candidate_count": validation_result.get(
                "candidate_count",
                len(all_candidates) if isinstance(all_candidates, list) else 1,
            ),
        }
        binding_issue_count = validation_result.get("binding_prevalidation_issue_count", 0)
        try:
            binding_issue_count = int(binding_issue_count or 0)
        except (TypeError, ValueError):
            binding_issue_count = 0
        if binding_issue_count > 0:
            pipeline_result["phases"]["validate"]["binding_prevalidation_issue_count"] = binding_issue_count
        binding_categories = validation_result.get("binding_prevalidation_categories", [])
        if isinstance(binding_categories, list):
            normalized_binding_categories = [
                str(item).strip() for item in binding_categories if str(item or "").strip()
            ]
            if normalized_binding_categories:
                pipeline_result["phases"]["validate"]["binding_prevalidation_categories"] = (
                    normalized_binding_categories[:6]
                )
        regenerate_only_categories = validation_result.get("binding_regenerate_only_categories", [])
        if isinstance(regenerate_only_categories, list):
            normalized_regenerate_only_categories = [
                str(item).strip() for item in regenerate_only_categories if str(item or "").strip()
            ]
            if normalized_regenerate_only_categories:
                pipeline_result["phases"]["validate"]["binding_regenerate_only_categories"] = (
                    normalized_regenerate_only_categories[:6]
                )
        regenerate_only_reason = str(validation_result.get("binding_regenerate_only_reason", "") or "").strip()
        if regenerate_only_reason:
            pipeline_result["phases"]["validate"]["binding_regenerate_only_reason"] = regenerate_only_reason
        candidate_advisories = validation_result.get("candidate_advisories", [])
        if isinstance(candidate_advisories, list) and candidate_advisories:
            pipeline_result["phases"]["validate"]["candidate_advisories"] = candidate_advisories[:3]
        selected_candidate_advisory = validation_result.get("selected_candidate_advisory", {})
        if isinstance(selected_candidate_advisory, dict) and selected_candidate_advisory:
            pipeline_result["phases"]["validate"]["selected_candidate_advisory"] = selected_candidate_advisory
        normalized_fix_pack = _normalize_stage3_fix_pack(validation_result)
        if normalized_fix_pack:
            pipeline_result["phases"]["validate"]["fix_pack"] = normalized_fix_pack
        advisory_fix_pack = _normalize_stage3_advisory_fix_pack(validation_result)
        if advisory_fix_pack:
            pipeline_result["phases"]["validate"]["advisory_fix_pack"] = advisory_fix_pack
        repair_contract = _normalize_stage3_repair_contract(
            validation_result,
            fix_pack=normalized_fix_pack or advisory_fix_pack,
        )
        if repair_contract:
            pipeline_result["phases"]["validate"]["repair_contract"] = repair_contract
        scope_authority = _normalize_stage3_scope_authority(validation_result)
        if scope_authority:
            pipeline_result["phases"]["validate"]["scope_authority"] = scope_authority
        local_patch_gate = _build_stage3_local_patch_gate(
            fix_scope=str(validation_result.get("fix_scope", "") or ""),
            fix_pack=normalized_fix_pack or advisory_fix_pack,
            repair_contract=repair_contract,
            scope_authority=scope_authority,
        )
        if isinstance(local_patch_gate, dict) and local_patch_gate:
            pipeline_result["phases"]["validate"]["local_patch_gate"] = dict(local_patch_gate)
        partial_fix_eval = validation_result.get("partial_fix_eval")
        if isinstance(partial_fix_eval, dict) and partial_fix_eval:
            pipeline_result["phases"]["validate"]["partial_fix_eval"] = dict(partial_fix_eval)
        if validation_quality_risk:
            pipeline_result["quality_risk"] = True
        if validation_revision_required:
            pipeline_result["revision_required"] = True
        pipeline_result["phases"]["generate"]["selected_strategy"] = selected_strategy or "unknown"
        pipeline_result["phases"]["generate"]["selected_score"] = score

    def _record_phase3_contradictions(
        self,
        *,
        pipeline_result: dict,
        validation_result: dict,
    ) -> None:
        contradictions = validation_result.get("contradictions", [])
        if not (isinstance(contradictions, list) and contradictions):
            return

        logging.warning(f"[Consistency] contradictions={len(contradictions)}")
        for contradiction in contradictions[:5]:
            logging.warning(f" {str(contradiction)[:150]}")
        pipeline_result["phases"]["validate"]["contradictions"] = contradictions

    @staticmethod
    def _has_only_advisory_residuals(validation_result: dict | None) -> bool:
        if not isinstance(validation_result, dict):
            return False
        if validation_result.get("quality_risk"):
            return False
        try:
            binding_issue_count = int(validation_result.get("binding_prevalidation_issue_count", 0) or 0)
        except (TypeError, ValueError):
            binding_issue_count = 0
        if binding_issue_count > 0:
            return False

        issues = validation_result.get("issues", [])
        if not isinstance(issues, list) or not issues:
            return False

        advisory_issues = [
            issue
            for issue in issues
            if isinstance(issue, dict) and (issue.get("advisory_only") or issue.get("director_focus") is False)
        ]
        substantive_issues = [
            issue
            for issue in issues
            if not (isinstance(issue, dict) and (issue.get("advisory_only") or issue.get("director_focus") is False))
        ]
        return bool(advisory_issues) and not substantive_issues

    @staticmethod
    def _collect_validation_issue_categories(validation_result: dict | None) -> list[str]:
        if not isinstance(validation_result, dict):
            return []
        issues = validation_result.get("issues", [])
        if not isinstance(issues, list):
            return []

        categories: list[str] = []
        seen: set[str] = set()
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            category = str(issue.get("category", "") or "").strip()
            if not category or category in seen:
                continue
            seen.add(category)
            categories.append(category)
        return categories[:6]

    @classmethod
    def _has_only_low_yield_advisory_residuals(cls, validation_result: dict | None) -> tuple[bool, list[str]]:
        if not cls._has_only_advisory_residuals(validation_result):
            return False, []
        categories = cls._collect_validation_issue_categories(validation_result)
        if not categories:
            return False, []
        low_yield_categories = {"scenario_density"}
        return set(categories).issubset(low_yield_categories), categories

    def _apply_phase3_quality_gate(self, *, verdict: str, score: int, validation_result: dict | None = None) -> str:
        quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        if verdict == "PASS" and score < quality_gate_score:
            if self._has_only_advisory_residuals(validation_result):
                logging.warning(
                    f"[QualityGate] Stage3 PASS below threshold ({score} < {quality_gate_score}) "
                    "but only advisory residuals remain; preserve PASS"
                )
                return verdict
            logging.warning(f"[QualityGate] Stage3 PASS but score={score} < {quality_gate_score}; force REJECT")
            return "REJECT"
        return verdict

    @staticmethod
    def _is_quality_gate_terminal_acceptance(validation_result: dict | None) -> bool:
        return bool(isinstance(validation_result, dict) and validation_result.get("quality_gate_terminal_acceptance"))

    def _annotate_or_accept_terminal_quality_gate_result(
        self,
        *,
        validation_verdict: str,
        verdict: str,
        validation_result: dict | None,
        effective_score: int,
        raw_score: int,
        ifc_penalty: int,
        retry: int,
        max_retries: int,
        best_blueprint: dict | None,
        pipeline_result: dict,
    ) -> tuple[str, dict]:
        if validation_verdict != "PASS" or verdict != "REJECT":
            return verdict, validation_result or {}

        normalized_validation = dict(validation_result or {})
        quality_gate_score = int(_threshold("scoring.quality_gate_score", 90))
        normalized_validation.setdefault("reject_origin", "quality_gate_reject")
        normalized_validation["quality_gate_score"] = quality_gate_score
        normalized_validation["quality_gate_effective_score"] = effective_score
        normalized_validation["quality_gate_raw_score"] = raw_score

        validate_phase = pipeline_result.setdefault("phases", {}).setdefault("validate", {})
        validate_phase["quality_gate_score"] = quality_gate_score
        validate_phase["quality_gate_effective_score"] = effective_score
        validate_phase["quality_gate_raw_score"] = raw_score

        terminal_retry = retry >= max_retries
        if terminal_retry and best_blueprint and effective_score >= PatchModeThresholds.REWRITE:
            normalized_validation["quality_gate_terminal_acceptance"] = True
            normalized_validation["quality_gate_terminal_acceptance_reason"] = "terminal_below_threshold_warning"
            normalized_validation["quality_gate_soft_override"] = True
            normalized_validation["quality_risk"] = True
            normalized_validation["revision_required"] = True
            normalized_validation["verdict"] = "PASS_WITH_WARNING"
            normalized_validation["decision"] = "PASS_WITH_WARNING"

            validate_phase["verdict"] = "PASS_WITH_WARNING"
            validate_phase["quality_risk"] = True
            validate_phase["revision_required"] = True
            validate_phase["quality_gate_terminal_acceptance"] = {
                "decision": "promote_to_pass_with_warning",
                "effective_score": effective_score,
                "quality_gate_score": quality_gate_score,
                "raw_score": raw_score,
                "ifc_penalty": ifc_penalty,
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
            }

            pipeline_result["quality_gate_failed"] = True
            pipeline_result["quality_risk"] = True
            pipeline_result["revision_required"] = True

            logging.warning(
                "[QualityGate] terminal PASS below threshold (%d < %d) on retry %d/%d -> accept PASS_WITH_WARNING",
                effective_score,
                quality_gate_score,
                retry + 1,
                max_retries + 1,
            )
            self._log_operator_retry_context(
                title=(
                    f"[QualityGate] effective_score={effective_score} "
                    f"(raw={raw_score}, ifc_penalty={ifc_penalty}) < threshold -> PASS_WITH_WARNING"
                ),
                level="warning",
                meta={
                    "phase": "validate",
                    "score": effective_score,
                    "raw_score": raw_score,
                    "ifc_penalty": ifc_penalty,
                    "retry_index": retry + 1,
                    "max_retries": max_retries + 1,
                    "error_category": "quality_gate_terminal_acceptance",
                },
                feedback=normalized_validation.get("verdict_reason", "") or normalized_validation.get("feedback", ""),
                issues=normalized_validation.get("issues", []),
                fix_scope=str(normalized_validation.get("fix_scope", "") or ""),
            )
            return "PASS_WITH_WARNING", normalized_validation

        return verdict, normalized_validation

    def _apply_validation_reject_state(
        self,
        *,
        validation_result: dict,
        retry_state: _ThreePhaseRetryState,
        score: int,
        selected_strategy: str,
        best_blueprint: dict | None,
    ) -> _ThreePhaseRejectStateResult:
        feedback = validation_result.get("feedback", "validation failed")
        normalized_score = int(score or 0)
        previous_score = int(retry_state.prev_reject_score or 0)
        previous_signature = str(retry_state.prev_reject_signature or "").strip()
        previous_inplace_streak = int(retry_state.inplace_reject_streak or 0)
        previous_advisory_streak = int(retry_state.advisory_only_reject_streak or 0)
        advisory_only_reject = self._has_only_advisory_residuals(validation_result)
        reject_signature = _build_stage3_reject_signature(
            validation_result=validation_result,
            advisory_only=advisory_only_reject,
        )
        reject_origin = str(validation_result.get("reject_origin") or "validation_reject").strip()
        quality_gate_reject = bool(
            reject_origin == "quality_gate_reject"
            or validation_result.get("quality_gate_effective_score") is not None
            or validation_result.get("quality_gate_score") is not None
        )
        resolved_fix_scope = str(validation_result.get("fix_scope", "") or "").strip().lower()
        try:
            retry_state.prev_binding_issue_count = int(
                validation_result.get("binding_prevalidation_issue_count", 0) or 0
            )
        except (TypeError, ValueError):
            retry_state.prev_binding_issue_count = 0

        retry_state.repeated_reject_score_streak = (
            retry_state.repeated_reject_score_streak + 1
            if normalized_score > 0 and normalized_score == previous_score
            else (1 if normalized_score > 0 else 0)
        )
        retry_state.repeated_reject_signature_streak = (
            retry_state.repeated_reject_signature_streak + 1
            if reject_signature and reject_signature == previous_signature
            else (1 if reject_signature else 0)
        )
        retry_state.inplace_reject_streak = previous_inplace_streak + 1 if resolved_fix_scope == "inplace" else 0
        retry_state.advisory_only_reject_streak = previous_advisory_streak + 1 if advisory_only_reject else 0
        retry_state.prev_reject_score = score
        retry_state.prev_reject_feedback = feedback
        retry_state.prev_reject_strategy = selected_strategy or ""
        retry_state.prev_fix_scope = validation_result.get("fix_scope", "")
        normalized_fix_pack = _normalize_stage3_fix_pack(validation_result)
        advisory_fix_pack = _normalize_stage3_advisory_fix_pack(validation_result)
        retry_state.prev_fix_pack = dict(normalized_fix_pack or advisory_fix_pack or {})
        retry_state.prev_repair_contract = _normalize_stage3_repair_contract(
            validation_result,
            fix_pack=normalized_fix_pack or advisory_fix_pack,
        )
        retry_state.prev_scope_authority = _normalize_stage3_scope_authority(validation_result)
        retry_state.prev_local_patch_gate = _build_stage3_local_patch_gate(
            fix_scope=str(retry_state.prev_fix_scope or ""),
            fix_pack=retry_state.prev_fix_pack,
            repair_contract=retry_state.prev_repair_contract,
            scope_authority=retry_state.prev_scope_authority,
        )
        retry_state.prev_reject_origin = reject_origin
        retry_state.prev_quality_gate_reject = quality_gate_reject
        retry_state.prev_reject_signature = reject_signature
        retry_state.prev_score_breakdown = (
            validation_result.get("score_breakdown", {})
            if isinstance(validation_result.get("score_breakdown", {}), dict)
            else {}
        )
        retry_state.prev_selection_reason = (
            validation_result.get("selection_reason")
            or validation_result.get("summary")
            or validation_result.get("comparison_notes", "")
            or str(validation_result.get("feedback", ""))
        )
        issues = validation_result.get("issues", [])
        retry_state.prev_validation_warnings = []
        regenerate_only_reason = str(validation_result.get("binding_regenerate_only_reason", "") or "").strip()
        if regenerate_only_reason:
            retry_state.prev_validation_warnings.append(f"binding_regenerate_only: {regenerate_only_reason}")
        local_patch_gate_reason = str(retry_state.prev_local_patch_gate.get("reason", "") or "").strip()
        if (
            retry_state.prev_local_patch_gate.get("contract_present")
            and local_patch_gate_reason
            and local_patch_gate_reason != "contract_local_patch_ready"
        ):
            retry_state.prev_validation_warnings.append(f"local_patch_gate: {local_patch_gate_reason}")
        if isinstance(issues, list):
            for issue in issues[:10]:
                if isinstance(issue, dict):
                    issue_category = issue.get("category", "issue")
                    issue_message = issue.get("issue", "")
                    retry_state.prev_validation_warnings.append(f"{issue_category}: {issue_message}".strip(": "))
                elif issue:
                    retry_state.prev_validation_warnings.append(str(issue))
        plateau_reasons = _build_stage3_retry_plateau_reasons(retry_state)
        if plateau_reasons:
            retry_state.prev_validation_warnings.append("retry_plateau: " + "; ".join(plateau_reasons))

        if retry_state.prev_reject_score >= PatchModeThresholds.REWRITE and best_blueprint:
            retry_state.previous_best = best_blueprint
        else:
            retry_state.previous_best = None

        return _ThreePhaseRejectStateResult(feedback=feedback, issues=issues)

    def _run_pass_with_fix_loop(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        best_blueprint: dict | None,
        validation_result: dict,
        score: int,
        quality_gate_score: int,
        selected_strategy: str,
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
        initial_feedback: str,
        retry_state: _ThreePhaseRetryState,
        pipeline_result: dict,
        retry: int,
        max_retries: int,
    ) -> _ThreePhasePassWithFixResult:
        owner = self.owner
        max_fix = 3
        current_blueprint = best_blueprint
        current_validation = validation_result
        prior_score = score  # [PF-EE] track for score-stall early-exit
        executed_patch_attempts = 0

        for fix_index in range(max_fix):
            iteration_result = self._run_pass_with_fix_iteration(
                ep_num=ep_num,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                pipeline_result=pipeline_result,
                score=score,
                quality_gate_score=quality_gate_score,
                director=director,
                arc_idx=arc_idx,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
                prev_hud=prev_hud,
                fix_index=fix_index,
                max_fix=max_fix,
            )
            current_blueprint = iteration_result.current_blueprint
            current_validation = iteration_result.current_validation
            if iteration_result.patch_attempted:
                executed_patch_attempts += 1
            if iteration_result.fix_ok:
                pipeline_result["final_verdict"] = "PASS"
                logging.info("[TF-32-V] Blueprint patch resolved -> PASS")
                return _ThreePhasePassWithFixResult(best_blueprint=current_blueprint)
            if iteration_result.should_break:
                break

            # ── [PF-EE] Score-stall early-exit guard ──
            new_score = current_validation.get("score")
            if new_score is not None:
                try:
                    new_score = int(new_score)
                except (ValueError, TypeError):
                    new_score = None
            if new_score is not None and new_score <= prior_score:
                logging.warning(
                    "[PF-EE] PWF score-stall early-exit: prior=%d current=%d; skipping remaining fix rounds",
                    prior_score,
                    new_score,
                )
                break
            if new_score is not None:
                prior_score = new_score

        return self._finalize_pass_with_fix_failure(
            best_blueprint=best_blueprint,
            current_blueprint=current_blueprint,
            current_validation=current_validation,
            validation_result=validation_result,
            score=score,
            selected_strategy=selected_strategy,
            initial_feedback=initial_feedback,
            max_fix=max_fix,
            executed_patch_attempts=executed_patch_attempts,
            retry_state=retry_state,
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
        )

    def _run_pass_with_fix_iteration(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        current_blueprint: dict | None,
        current_validation: dict,
        pipeline_result: dict,
        score: int,
        quality_gate_score: int,
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
        fix_index: int,
        max_fix: int,
    ) -> _ThreePhasePassWithFixIterationResult:
        owner = self.owner
        validate_phase = pipeline_result.setdefault("phases", {}).setdefault("validate", {})
        repair_material = _Stage3RepairRouter.build_validation_material(current_validation)
        if repair_material.normalized_fix_pack:
            validate_phase["fix_pack"] = dict(repair_material.normalized_fix_pack)
        if repair_material.advisory_fix_pack:
            validate_phase["advisory_fix_pack"] = dict(repair_material.advisory_fix_pack)
        if repair_material.repair_contract:
            validate_phase["repair_contract"] = dict(repair_material.repair_contract)
        if repair_material.scope_authority:
            validate_phase["scope_authority"] = dict(repair_material.scope_authority)
        validate_phase["local_patch_gate"] = dict(repair_material.local_patch_gate)
        current_validation["local_patch_gate"] = dict(repair_material.local_patch_gate)
        alias_reaudit_eligible = _is_stage3_inplace_alias_reaudit_eligible(
            current_validation,
            requested_fix_scope=repair_material.normalized_requested_fix_scope,
            resolved_fix_scope=repair_material.resolved_fix_scope,
        )
        repair_route = _Stage3RepairRouter.decide_pass_with_fix(
            material=repair_material,
            score=score,
            inplace_threshold=int(_threshold("patch_mode.inplace_below", 60)),
        )
        effective_fix_pack = repair_material.effective_fix_pack
        fix_scope = repair_route.effective_fix_scope
        if repair_route.regenerate_only_reason and not alias_reaudit_eligible:
            current_validation["fix_scope"] = "full"
            if repair_material.regenerate_only_binding_categories:
                current_validation["binding_regenerate_only_categories"] = list(
                    repair_material.regenerate_only_binding_categories
                )
            current_validation["binding_regenerate_only_reason"] = repair_route.regenerate_only_reason
            current_validation["fix_scope_reasoning"] = repair_route.fix_scope_reasoning
            logging.info(
                "[TF-33] binding_prevalidation_categories=%s block inplace; force full regenerate",
                repair_material.regenerate_only_binding_categories
                or [f"unresolved_binding_issue_count={repair_material.binding_issue_count}"],
            )
        elif repair_route.fix_scope_reasoning:
            current_validation["fix_scope"] = fix_scope
            current_validation["fix_scope_reasoning"] = repair_route.fix_scope_reasoning
            logging.info(
                "[TF-33C] contract-driven local patch gate blocks inplace; scope=%s reason=%s",
                repair_route.resolved_fix_scope or "missing",
                repair_route.contract_block_reason or "unknown_reason",
            )
        if not fix_scope:
            inplace_thresh = int(_threshold("patch_mode.inplace_below", 60))
            fix_scope = "inplace" if score >= inplace_thresh else "full"
            logging.warning("[PF-1] fix_scope missing; score=%d fallback=%s", score, fix_scope)
        if alias_reaudit_eligible:
            logging.info(
                "[TF-33A] opening_transition alias-only mismatch already normalized on current blueprint; "
                "skip local patch and re-audit current payload"
            )
            self._log_operator_retry_context(
                title=f"[TF-33A] opening_transition alias re-audit #{fix_index + 1}",
                meta={
                    "phase": "validate",
                    "patch_round": fix_index + 1,
                    "patch_max": max_fix,
                    "binding_categories": ["opening_transition"],
                    "path": "normalized_current_blueprint_reaudit",
                },
                feedback=current_validation.get("verdict_reason", "") or current_validation.get("feedback", ""),
                issues=current_validation.get("issues", []),
                fix_scope=str(fix_scope or ""),
            )
            patched_blueprint = current_blueprint
            patch_attempted = False
        elif repair_route.should_break_to_generate:
            logging.info(f"[TF-33] fix_scope={fix_scope!r} blocks inplace; delegate to generate loop")
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                should_break=True,
                patch_attempted=False,
            )
        else:
            fix_feedback = current_validation.get("re_slice_instruction", "") or current_validation.get("feedback", "")
            fix_pack_guidance = _build_stage3_fix_pack_guidance(effective_fix_pack)
            if fix_pack_guidance:
                fix_feedback = f"{fix_pack_guidance}\n\n{fix_feedback}".strip() if fix_feedback else fix_pack_guidance
            logging.info(f"[TF-32-V] Blueprint patch #{fix_index + 1}/{max_fix}")
            self._log_operator_retry_context(
                title=f"[TF-32-V] Blueprint patch #{fix_index + 1}/{max_fix}",
                meta={"phase": "validate", "patch_round": fix_index + 1, "patch_max": max_fix},
                feedback=fix_feedback,
                fix_scope=str(fix_scope or ""),
            )
            try:
                patched_blueprint = self._call_with_operator_heartbeat(
                    title=f"[TF-32-V] Blueprint patch #{fix_index + 1}/{max_fix}",
                    meta={
                        "phase": "validate",
                        "patch_round": fix_index + 1,
                        "patch_max": max_fix,
                        "fix_scope": str(fix_scope or ""),
                        "feedback_chars": len(str(fix_feedback or "")),
                    },
                    fn=lambda: owner._inplace_patch_blueprint(
                        original_blueprint=current_blueprint,
                        director_feedback=fix_feedback,
                        ep_num=ep_num,
                        arc_data=arc_data,
                        normalized_fix_pack=effective_fix_pack,
                    ),
                )
            except Exception:
                logging.exception("[TF-32-V] inplace_patch_blueprint exception")
                return _ThreePhasePassWithFixIterationResult(
                    current_blueprint=current_blueprint,
                    current_validation=current_validation,
                    should_break=True,
                    patch_attempted=True,
                )
            if not patched_blueprint:
                logging.warning("[TF-32-V] patch failed")
                partial_fix_eval = _build_stage3_partial_fix_eval(
                    fix_pack=effective_fix_pack,
                    patch_round=fix_index + 1,
                    fallback_reason="patch_generation_failed",
                )
                if partial_fix_eval:
                    validate_phase["partial_fix_eval"] = partial_fix_eval
                    current_validation["partial_fix_eval"] = partial_fix_eval
                self._log_operator_retry_context(
                    title=f"[TF-32-V] patch #{fix_index + 1} failed",
                    level="warning",
                    meta={"phase": "validate", "patch_round": fix_index + 1, "patch_max": max_fix},
                    feedback=fix_feedback,
                    fix_scope=str(fix_scope or ""),
                )
                return _ThreePhasePassWithFixIterationResult(
                    current_blueprint=current_blueprint,
                    current_validation=current_validation,
                    should_break=True,
                    patch_attempted=True,
                )
            patch_attempted = True

        try:
            from modules.core.constants import calc_patch_change_ratio, log_patch_diff

            original_json = json.dumps(current_blueprint, ensure_ascii=False)
            patched_json = json.dumps(patched_blueprint, ensure_ascii=False)
            log_patch_diff(
                "S3-Blueprint",
                json.dumps(current_blueprint, ensure_ascii=False, indent=2),
                json.dumps(patched_blueprint, ensure_ascii=False, indent=2),
            )
            change_ratio = calc_patch_change_ratio(original_json, patched_json)
            max_ratio = float(_threshold("patch_mode.inplace_max_change_ratio", 0.30))
            if change_ratio > max_ratio:
                logging.warning(
                    "[F-2] InPlace Blueprint change ratio %.1f%% > %.0f%% (S3)",
                    change_ratio * 100,
                    max_ratio * 100,
                )
        except Exception:
            pass

        try:
            re_verdict, re_validation = self._call_with_operator_heartbeat(
                title=f"[TF-32-V] re-audit #{fix_index + 1}",
                meta={
                    "phase": "validate",
                    "patch_round": fix_index + 1,
                    "patch_max": max_fix,
                    "candidate_count": 1,
                    "path": "normalized_current_blueprint_reaudit" if alias_reaudit_eligible else "post_patch_reaudit",
                },
                fn=lambda: owner.validator.validate(
                    blueprint=patched_blueprint,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                    prev_blueprint=prev_blueprint,
                    director=director,
                    working_ep=ep_num,
                    arc_idx=arc_idx,
                    entity_registry=entity_registry,
                    state_tracker=state_tracker,
                    all_candidates=None,
                    prev_hud=prev_hud,
                ),
            )
        except Exception:
            logging.exception("[TF-32-V] re-audit exception")
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                should_break=True,
                patch_attempted=patch_attempted,
            )

        logging.info(f"[TF-32-V] re-audit #{fix_index + 1}: {re_verdict} (score={re_validation.get('score', 0)})")
        owner._operator_log(
            f"[TF-32-V] re-audit #{fix_index + 1}: {re_verdict} (score={re_validation.get('score', 0)})",
            meta={
                "phase": "validate",
                "patch_round": fix_index + 1,
                "verdict": re_verdict,
                "score": re_validation.get("score", 0),
            },
        )
        partial_fix_eval = _build_stage3_partial_fix_eval(
            fix_pack=effective_fix_pack,
            patch_round=fix_index + 1,
            verdict=re_verdict,
            fallback_reason="still_requires_fix"
            if re_verdict == "PASS_WITH_FIX"
            else "re_audit_reject"
            if re_verdict not in {"PASS", "PASS_WITH_WARNING"}
            else "",
        )
        if partial_fix_eval:
            validate_phase["partial_fix_eval"] = partial_fix_eval
            re_validation["partial_fix_eval"] = partial_fix_eval
        if repair_material.normalized_fix_pack:
            re_validation.setdefault("fix_pack", dict(repair_material.normalized_fix_pack))
        if repair_material.advisory_fix_pack:
            re_validation.setdefault("advisory_fix_pack", dict(repair_material.advisory_fix_pack))
        if repair_material.repair_contract:
            re_validation.setdefault("repair_contract", dict(repair_material.repair_contract))
        if repair_material.scope_authority:
            re_validation.setdefault("scope_authority", dict(repair_material.scope_authority))
        if repair_material.local_patch_gate:
            re_validation.setdefault("local_patch_gate", dict(repair_material.local_patch_gate))
        if isinstance(re_validation, dict):
            re_validation.setdefault("verdict", re_verdict)
            re_validation.setdefault("decision", re_verdict)
        if re_verdict == "PASS":
            re_score = re_validation.get("score", 0)
            try:
                re_score = int(re_score)
            except (ValueError, TypeError):
                re_score = 0
            if re_score < quality_gate_score:
                if self._has_only_advisory_residuals(re_validation):
                    logging.warning(
                        f"[TF-35] re-audit PASS below threshold ({re_score} < {quality_gate_score}) "
                        "but only advisory residuals remain; preserve PASS"
                    )
                    self._log_operator_retry_context(
                        title=f"[TF-35] advisory-only residuals -> preserve PASS (score={re_score} < {quality_gate_score})",
                        level="warning",
                        meta={
                            "phase": "validate",
                            "patch_round": fix_index + 1,
                            "verdict": re_verdict,
                            "score": re_score,
                            "error_category": "quality_gate_advisory_only",
                        },
                        feedback=re_validation.get("verdict_reason", "") or re_validation.get("feedback", ""),
                        issues=re_validation.get("issues", []),
                        fix_scope=str(re_validation.get("fix_scope", "") or ""),
                    )
                    re_validation["quality_gate_soft_override"] = True
                    return _ThreePhasePassWithFixIterationResult(
                        current_blueprint=patched_blueprint,
                        current_validation=re_validation,
                        fix_ok=True,
                        patch_attempted=patch_attempted,
                    )
                logging.warning(f"[TF-35] re-audit PASS but score={re_score} < {quality_gate_score}; stop patch loop")
                self._log_operator_retry_context(
                    title=f"[TF-35] re-audit PASS but score={re_score} < {quality_gate_score}",
                    level="warning",
                    meta={
                        "phase": "validate",
                        "patch_round": fix_index + 1,
                        "verdict": re_verdict,
                        "score": re_score,
                        "error_category": "quality_gate",
                    },
                    feedback=re_validation.get("verdict_reason", "") or re_validation.get("feedback", ""),
                    issues=re_validation.get("issues", []),
                    fix_scope=str(re_validation.get("fix_scope", "") or ""),
                )
                return _ThreePhasePassWithFixIterationResult(
                    current_blueprint=patched_blueprint,
                    current_validation=re_validation,
                    should_break=True,
                    patch_attempted=patch_attempted,
                )
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=patched_blueprint,
                current_validation=re_validation,
                fix_ok=True,
                patch_attempted=patch_attempted,
            )
        if re_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"):
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=patched_blueprint,
                current_validation=re_validation,
                fix_ok=re_verdict == "PASS_WITH_WARNING",
                patch_attempted=patch_attempted,
            )
        return _ThreePhasePassWithFixIterationResult(
            current_blueprint=current_blueprint,
            current_validation=current_validation,
            should_break=True,
            patch_attempted=patch_attempted,
        )

    @staticmethod
    def _describe_pass_with_fix_failure(
        *,
        executed_patch_attempts: int,
        max_fix: int,
        current_validation: dict,
    ) -> tuple[str, str, str]:
        fix_scope = str(current_validation.get("fix_scope", "") or "").strip().lower()
        if executed_patch_attempts <= 0:
            if fix_scope == "full":
                return (
                    "rerouted_before_patch",
                    "[TF-32-V] PASS_WITH_FIX rerouted before local patch -> REJECT",
                    "PASS_WITH_FIX rerouted before local patch -> REJECT",
                )
            return (
                "zero_patch_attempts",
                "[TF-32-V] PASS_WITH_FIX ended before any executed local patch -> REJECT",
                "PASS_WITH_FIX ended before any executed local patch -> REJECT",
            )

        noun = "attempt" if executed_patch_attempts == 1 else "attempts"
        summary = f"PASS_WITH_FIX unresolved after {executed_patch_attempts} executed local patch {noun} -> REJECT"
        return (
            "patch_exhaustion",
            f"[TF-32-V] {summary}",
            summary,
        )

    def _finalize_pass_with_fix_failure(
        self,
        *,
        best_blueprint: dict | None,
        current_blueprint: dict | None,
        current_validation: dict,
        validation_result: dict,
        score: int,
        selected_strategy: str,
        initial_feedback: str,
        max_fix: int,
        executed_patch_attempts: int = 0,
        retry_state: _ThreePhaseRetryState,
        ep_num: int,
        arc_data: dict,
        retry: int,
        max_retries: int,
    ) -> _ThreePhasePassWithFixResult:
        owner = self.owner
        last_reaudit_verdict = current_validation.get("verdict", "") or current_validation.get("decision", "")
        effective_score = current_validation.get("score", score)
        try:
            effective_score = int(effective_score)
        except (ValueError, TypeError):
            effective_score = score
        if (
            last_reaudit_verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING")
            and current_blueprint != best_blueprint
        ):
            best_blueprint = current_blueprint
            validation_result["score"] = effective_score
            if last_reaudit_verdict == "PASS":
                logging.info(
                    "[PF-3] PASS below quality gate -> adopt latest patched blueprint for retry (score=%d)",
                    effective_score,
                )
            else:
                logging.info(
                    "[PF-3] PASS_WITH_FIX exhausted -> adopt latest patched blueprint (score=%d)", effective_score
                )

        failure_mode, operator_title, feedback_tail = self._describe_pass_with_fix_failure(
            executed_patch_attempts=executed_patch_attempts,
            max_fix=max_fix,
            current_validation=current_validation,
        )
        current_validation = dict(current_validation)
        current_validation["pass_with_fix_failure_mode"] = failure_mode
        current_validation["executed_patch_attempts"] = executed_patch_attempts

        logging.warning("[TF-32-V] Blueprint patch failed -> REJECT")
        self._log_operator_retry_context(
            title=operator_title,
            level="warning",
            meta={
                "phase": "validate",
                "score": effective_score,
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "error_category": "patch_retry_reject",
                "executed_patch_attempts": executed_patch_attempts,
                "configured_patch_budget": max_fix,
            },
            feedback=current_validation.get("verdict_reason", "") or current_validation.get("feedback", ""),
            issues=current_validation.get("issues", []),
            fix_scope=str(current_validation.get("fix_scope", "") or ""),
        )
        owner.stats["phase3_reject"] += 1
        feedback = initial_feedback + f"\n[TF-32-V] {feedback_tail}"
        regenerate_only_reason = str(current_validation.get("binding_regenerate_only_reason", "") or "").strip()
        if regenerate_only_reason:
            feedback = f"{feedback}\n[TF-33] {regenerate_only_reason}"
        current_validation.setdefault("reject_origin", "pass_with_fix_unresolved")
        self._apply_validation_reject_state(
            validation_result=current_validation,
            retry_state=retry_state,
            score=effective_score,
            selected_strategy=selected_strategy,
            best_blueprint=best_blueprint,
        )
        retry_state.prev_reject_feedback = feedback
        owner._record_intermediate_reject(
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
            reject_reason=feedback,
            event_tag="patch_retry_reject",
            candidate_key=selected_strategy or "",
        )
        return _ThreePhasePassWithFixResult(best_blueprint=best_blueprint, should_continue=True)

    def _handle_validation_reject(
        self,
        *,
        validation_result: dict,
        retry_state: _ThreePhaseRetryState,
        score: int,
        selected_strategy: str,
        best_blueprint: dict | None,
        ep_num: int,
        arc_data: dict,
        retry: int,
        max_retries: int,
    ) -> None:
        owner = self.owner
        if not validation_result.get("reject_origin"):
            validation_result = dict(validation_result)
            validation_result["reject_origin"] = "validation_reject"
        reject_state = self._apply_validation_reject_state(
            validation_result=validation_result,
            retry_state=retry_state,
            score=score,
            selected_strategy=selected_strategy,
            best_blueprint=best_blueprint,
        )

        if reject_state.issues:
            logging.warning("[Phase 3] REJECT - major issues:")
            for issue in reject_state.issues[:3]:
                severity = issue.get("severity", "?")
                category = issue.get("category", "?")
                text = issue.get("issue", "?")
                logging.info(f"[{severity}][{category}] {text}")

        logging.warning(f"[Phase 3] REJECT - retry {retry + 1}/{max_retries + 1}")
        self._log_operator_retry_context(
            title=f"[Phase 3] REJECT (score={score}) - retry {retry + 1}/{max_retries + 1}",
            level="warning",
            meta={"phase": "validate", "score": score, "retry_index": retry + 1, "max_retries": max_retries + 1},
            feedback=reject_state.feedback,
            issues=reject_state.issues,
            fix_scope=str(validation_result.get("fix_scope", "") or ""),
        )
        owner._record_intermediate_reject(
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
            reject_reason=reject_state.feedback,
            event_tag="validation_reject",
            candidate_key=selected_strategy or "",
        )

    def _finalize_terminal_failure(
        self,
        *,
        ep_num: int,
        max_retries: int,
        pipeline_result: dict,
        retry_state: _ThreePhaseRetryState,
        best_blueprint: dict | None,
        director,
        feedback: str,
    ) -> tuple[dict | None, dict]:
        last_score = retry_state.prev_reject_score
        final_feedback = retry_state.prev_reject_feedback or feedback

        if pipeline_result.get("failure_reason") == AgentErrorType.SCHEMA_INCOMPATIBLE:
            pipeline_result["final_verdict"] = "FAILED"
            logging.warning(f"[ThreePhase] ep{ep_num} schema_incompatible immediate failure")
            return None, pipeline_result

        if best_blueprint and director and last_score >= PatchModeThresholds.REWRITE:
            if retry_state.prev_binding_issue_count > 0:
                pipeline_result["final_verdict"] = "FAILED"
                logging.warning(
                    "[ThreePhase] ep%d emergency fallback blocked: unresolved binding issues=%d",
                    ep_num,
                    retry_state.prev_binding_issue_count,
                )
                return None, pipeline_result
            logging.warning(
                f" [ThreePhase] ep{ep_num} emergency fallback (score={last_score} >= {PatchModeThresholds.REWRITE})"
            )
            pipeline_result["final_verdict"] = "PASS_WITH_WARNING"
            pipeline_result["quality_gate_failed"] = True
            pipeline_result["quality_risk"] = True
            pipeline_result["revision_required"] = True
            pipeline_result["last_score"] = last_score
            best_blueprint = validate_blueprint(best_blueprint)
            return best_blueprint, pipeline_result

        pipeline_result["final_verdict"] = "FAILED"
        logging.warning(f"[ThreePhase] ep{ep_num} all retries failed ({max_retries + 1})")
        if final_feedback:
            logging.info(f"Last feedback: {final_feedback[:200]}...")
        return None, pipeline_result

    def _resolve_retry_cycle_result(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        best_blueprint: dict | None,
        validation_result: dict,
        verdict: str,
        score: int,
        selected_strategy: str,
        director,
        arc_idx: int,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
        initial_feedback: str,
        feedback: str,
        retry_state: _ThreePhaseRetryState,
        pipeline_result: dict,
        retry: int,
        max_retries: int,
    ) -> _ThreePhaseRetryCycleResult:
        owner = self.owner
        if verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING"):
            owner.stats["phase3_pass"] += 1
            pipeline_result["final_verdict"] = verdict
            pipeline_result["last_score"] = score
            if verdict == "PASS_WITH_WARNING" and self._is_quality_gate_terminal_acceptance(validation_result):
                pipeline_result["quality_gate_failed"] = True
                pipeline_result["quality_risk"] = True
                pipeline_result["revision_required"] = True
            logging.info(f"[Phase 3] {verdict} - ep{ep_num} blueprint finalized")
            owner._operator_log(
                f"[Phase 3] {verdict} (score={score})",
                meta={"phase": "validate", "verdict": verdict, "score": score},
            )

            if verdict == "PASS_WITH_FIX":
                low_yield_advisory_only, advisory_categories = self._has_only_low_yield_advisory_residuals(
                    validation_result
                )
                if low_yield_advisory_only:
                    logging.warning(
                        "[TF-35A] advisory-only residuals %s -> accept PASS_WITH_WARNING without local patch reopen",
                        ", ".join(advisory_categories),
                    )
                    self._log_operator_retry_context(
                        title="[TF-35A] advisory-only residuals -> accept PASS_WITH_WARNING",
                        level="warning",
                        meta={
                            "phase": "validate",
                            "verdict": verdict,
                            "score": score,
                            "error_category": "advisory_only_residual_acceptance",
                        },
                        feedback=validation_result.get("verdict_reason", "") or validation_result.get("feedback", ""),
                        issues=validation_result.get("issues", []),
                        fix_scope=str(validation_result.get("fix_scope", "") or ""),
                    )
                    validate_phase = pipeline_result.setdefault("phases", {}).setdefault("validate", {})
                    validate_phase["advisory_only_residual_acceptance"] = {
                        "decision": "promote_to_pass_with_warning",
                        "categories": advisory_categories,
                        "reason": "low_yield_advisory_local_patch",
                    }
                    pipeline_result["final_verdict"] = "PASS_WITH_WARNING"
                    best_blueprint = validate_blueprint(best_blueprint)
                    return _ThreePhaseRetryCycleResult(
                        best_blueprint=best_blueprint,
                        feedback=feedback,
                        final_result=(best_blueprint, pipeline_result),
                    )
                pass_fix_result = self._run_pass_with_fix_loop(
                    ep_num=ep_num,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                    prev_blueprint=prev_blueprint,
                    best_blueprint=best_blueprint,
                    validation_result=validation_result,
                    score=score,
                    quality_gate_score=int(_threshold("scoring.quality_gate_score", 90)),
                    selected_strategy=selected_strategy,
                    director=director,
                    arc_idx=arc_idx,
                    entity_registry=entity_registry,
                    state_tracker=state_tracker,
                    prev_hud=prev_hud,
                    initial_feedback=initial_feedback,
                    retry_state=retry_state,
                    pipeline_result=pipeline_result,
                    retry=retry,
                    max_retries=max_retries,
                )
                if pass_fix_result.should_continue:
                    return _ThreePhaseRetryCycleResult(
                        best_blueprint=pass_fix_result.best_blueprint,
                        feedback=feedback,
                        should_continue=True,
                    )
                best_blueprint = pass_fix_result.best_blueprint

            best_blueprint = validate_blueprint(best_blueprint)
            return _ThreePhaseRetryCycleResult(
                best_blueprint=best_blueprint,
                feedback=feedback,
                final_result=(best_blueprint, pipeline_result),
            )

        owner.stats["phase3_reject"] += 1
        self._handle_validation_reject(
            validation_result=validation_result,
            retry_state=retry_state,
            score=score,
            selected_strategy=selected_strategy,
            best_blueprint=best_blueprint,
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
        )
        return _ThreePhaseRetryCycleResult(
            best_blueprint=best_blueprint,
            feedback=retry_state.prev_reject_feedback or feedback,
        )

    def _run_retry_cycle(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        protagonist_name: str,
        protagonist_config: dict,
        state_tracker,
        db,
        prev_manuscripts_text: str,
        adversarial_self_play,
        director,
        arc_idx: int,
        entity_registry: dict | None,
        prev_hud: dict | None,
        initial_feedback: str,
        feedback: str,
        retry_state: _ThreePhaseRetryState,
        pipeline_result: dict,
        genre: str,
        current_best_blueprint: dict | None,
        retry: int,
        max_retries: int,
        log_retry: bool = True,
    ) -> _ThreePhaseRetryCycleResult:
        owner = self.owner
        if log_retry:
            owner._operator_log(
                f"[Retry {retry + 1}/{max_retries + 1}] Stage3 retry cycle 시작",
                meta={"retry_index": retry + 1, "max_retries": max_retries + 1, "ep_num": ep_num},
            )
        pipeline_result["retries"] = retry
        strategy_feedback = self._build_retry_strategy_feedback(retry_state)
        attempt_feedback = initial_feedback
        if strategy_feedback:
            attempt_feedback = f"{attempt_feedback}\n\n{strategy_feedback}" if attempt_feedback else strategy_feedback

        constraint_block = self._resolve_constraint_block(
            retry=retry,
            ep_num=ep_num,
            arc_data=arc_data,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            genre=genre,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            prev_manuscripts_text=prev_manuscripts_text,
        )

        phase2_result = self._run_phase2_generation(
            retry=retry,
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            state_tracker=state_tracker,
            prev_manuscripts_text=prev_manuscripts_text,
            attempt_feedback=attempt_feedback,
            strategy_feedback=strategy_feedback,
            adversarial_self_play=adversarial_self_play,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            max_retries=max_retries,
        )
        if phase2_result.should_break:
            return _ThreePhaseRetryCycleResult(
                best_blueprint=current_best_blueprint,
                feedback=feedback,
                should_break=True,
            )
        if phase2_result.should_continue:
            return _ThreePhaseRetryCycleResult(
                best_blueprint=current_best_blueprint,
                feedback=feedback,
                should_continue=True,
            )

        best_blueprint = phase2_result.best_blueprint
        phase3_result = self._run_phase3_validation(
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            best_blueprint=best_blueprint,
            all_candidates=phase2_result.all_candidates,
            director=director,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            db=db,
            prev_hud=prev_hud,
            retry_state=retry_state,
            pipeline_result=pipeline_result,
            retry=retry,
            max_retries=max_retries,
        )
        if phase3_result.should_continue:
            return _ThreePhaseRetryCycleResult(
                best_blueprint=phase3_result.best_blueprint,
                feedback=feedback,
                should_continue=True,
            )

        return self._resolve_retry_cycle_result(
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            best_blueprint=phase3_result.best_blueprint,
            validation_result=phase3_result.validation_result,
            verdict=phase3_result.verdict,
            score=phase3_result.score,
            selected_strategy=phase3_result.selected_strategy,
            director=director,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            prev_hud=prev_hud,
            initial_feedback=initial_feedback,
            feedback=feedback,
            retry_state=retry_state,
            pipeline_result=pipeline_result,
            retry=retry,
            max_retries=max_retries,
        )

    def generate(
        self,
        ep_num: int,
        arc_data: dict,
        prev_blueprint: dict | None = None,
        prev_blueprints: list[dict] | None = None,
        max_retries: int = 9,  # [TF-23b] 9 = total 10 tries (0~9)
        external_feedback: str = "",
        director=None,
        arc_idx: int = 0,
        entity_registry: dict | None = None,
        protagonist_name: str = "주인공",
        protagonist_config: dict | None = None,
        state_tracker=None,
        db=None,
        semantic_context: str = "",
        prev_manuscripts_text: str = "",
        adversarial_self_play=None,
        prev_hud: dict | None = None,
    ) -> tuple[dict | None, dict]:
        owner = self.owner
        bootstrap = self._bootstrap_runtime_context(
            ep_num=ep_num,
            arc_data=arc_data,
            semantic_context=semantic_context,
            external_feedback=external_feedback,
            protagonist_config=protagonist_config,
        )
        protagonist_config = bootstrap.protagonist_config
        pipeline_result = bootstrap.pipeline_result
        retry_state = bootstrap.retry_state
        genre = bootstrap.genre
        initial_feedback = bootstrap.initial_feedback
        best_blueprint: dict | None = None
        feedback = initial_feedback

        for retry in range(max_retries + 1):
            owner._operator_log(
                f"[Retry {retry + 1}/{max_retries + 1}] Blueprint 생성 중...",
                meta={"retry_index": retry + 1, "max_retries": max_retries + 1, "ep_num": ep_num},
            )
            retry_result = self._run_retry_cycle(
                ep_num=ep_num,
                arc_data=arc_data,
                prev_blueprint=prev_blueprint,
                prev_blueprints=prev_blueprints,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                state_tracker=state_tracker,
                db=db,
                prev_manuscripts_text=prev_manuscripts_text,
                adversarial_self_play=adversarial_self_play,
                director=director,
                arc_idx=arc_idx,
                entity_registry=entity_registry,
                prev_hud=prev_hud,
                initial_feedback=initial_feedback,
                feedback=feedback,
                retry_state=retry_state,
                pipeline_result=pipeline_result,
                genre=genre,
                current_best_blueprint=best_blueprint,
                retry=retry,
                max_retries=max_retries,
                log_retry=False,
            )
            best_blueprint = retry_result.best_blueprint
            feedback = retry_result.feedback
            if retry_result.should_break:
                break
            if retry_result.should_continue:
                continue
            if retry_result.final_result is not None:
                return retry_result.final_result

        return self._finalize_terminal_failure(
            ep_num=ep_num,
            max_retries=max_retries,
            pipeline_result=pipeline_result,
            retry_state=retry_state,
            best_blueprint=best_blueprint,
            director=director,
            feedback=feedback,
        )
