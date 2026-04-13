import copy
from dataclasses import dataclass

from modules.core.logging_keys import build_attempt_key


@dataclass(slots=True)
class Stage4PassEpisodeLogParts:
    base_fields: dict
    feedback_provenance: dict[str, str]
    artifact_fields: dict[str, str | int]


@dataclass(slots=True)
class Stage4PassEpisodeLogRequest:
    ep_num: int
    round_num: int
    arc_num: int
    director_result: dict
    director_feedback: str
    trace_verdict_reason: str | None
    initial_verdict: str
    initial_score: int
    final_verdict: str
    final_score: int
    is_patch: bool
    is_patch_fallback: bool
    tot_used: bool
    mad_used: bool
    asp_used: bool
    model_tier: str | None
    validation_warnings: list[str]
    final_warnings: list[str]
    patch_trace: dict | None
    session_runtime_advisory: str
    session_retry_directives: str
    log_artifact_meta: dict[str, str]
    selection_artifact_meta: dict
    session_id: str | None


@dataclass(slots=True)
class Stage4RejectEpisodeLogRequest:
    ep_num: int
    round_num: int
    arc_num: int
    sink_source: dict
    initial_verdict: str
    initial_score: int
    final_verdict: str
    final_score: int
    is_patch: bool
    is_patch_fallback: bool
    tot_used: bool
    mad_used: bool
    asp_used: bool
    model: str | None
    reject_bucket: str
    validation_warnings: list
    feedback_provenance: dict[str, str]
    patch_trace: dict | None
    reject_artifact_meta: dict[str, str]
    selection_artifact_meta: dict[str, str]
    attempt_key: str


def build_pass_episode_log_payload(*, request: Stage4PassEpisodeLogRequest) -> dict:
    parts = build_pass_episode_log_parts(request=request)
    return assemble_pass_episode_log_payload(
        base_fields=parts.base_fields,
        feedback_provenance=parts.feedback_provenance,
        artifact_fields=parts.artifact_fields,
    )


def build_pass_episode_log_parts(*, request: Stage4PassEpisodeLogRequest) -> Stage4PassEpisodeLogParts:
    return Stage4PassEpisodeLogParts(
        base_fields=build_pass_episode_log_base_fields(request=request),
        feedback_provenance=build_pass_feedback_provenance(request=request),
        artifact_fields=build_pass_episode_log_artifact_fields(request=request),
    )


def assemble_pass_episode_log_payload(
    *,
    base_fields: dict,
    feedback_provenance: dict[str, str],
    artifact_fields: dict[str, str | int],
) -> dict:
    return {
        **base_fields,
        "feedback_provenance": feedback_provenance,
        **artifact_fields,
    }


def build_pass_episode_log_base_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        **build_pass_episode_log_round_fields(request=request),
        **build_pass_episode_log_status_fields(request=request),
    }


def build_pass_episode_log_round_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        "ep_num": request.ep_num,
        "round_num": request.round_num,
        "director_result": request.director_result,
        "initial_verdict": request.initial_verdict,
        "initial_score": request.initial_score,
        "final_verdict": request.final_verdict,
        "final_score": request.final_score,
    }


def build_pass_episode_log_status_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        **build_pass_episode_log_usage_fields(request=request),
        **build_pass_episode_log_warning_fields(request=request),
    }


def build_pass_episode_log_usage_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        **build_pass_episode_log_usage_flag_fields(request=request),
        **build_pass_episode_log_model_field(request=request),
    }


def build_pass_episode_log_usage_flag_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        "is_patch": request.is_patch,
        "patch_fallback": request.is_patch_fallback,
        "tot_used": request.tot_used,
        "mad_used": request.mad_used,
        "asp_used": request.asp_used,
    }


def build_pass_episode_log_model_field(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {"model": request.model_tier}


def build_pass_episode_log_warning_fields(*, request: Stage4PassEpisodeLogRequest) -> dict:
    return {
        "reject_bucket": "",
        "validation_warnings": request.validation_warnings,
        "final_warnings": request.final_warnings,
        "patch_trace": request.patch_trace,
    }


def build_stage4_feedback_provenance(
    *,
    director_feedback: str,
    runtime_advisory: str,
    retry_directives: str,
) -> dict[str, str]:
    normalized_director_feedback = str(director_feedback or "")
    return {
        "director_feedback": normalized_director_feedback,
        "director_feedback_text": normalized_director_feedback,
        "runtime_advisory": str(runtime_advisory or ""),
        "retry_directives": str(retry_directives or ""),
    }


def build_pass_feedback_provenance(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str]:
    return build_stage4_feedback_provenance(
        director_feedback=str(request.trace_verdict_reason or request.director_feedback),
        runtime_advisory=request.session_runtime_advisory,
        retry_directives=request.session_retry_directives,
    )


def build_stage4_episode_log_carryover_contracts(*, gate_semantics: dict | None) -> dict[str, dict] | None:
    gate_payload = gate_semantics if isinstance(gate_semantics, dict) else {}
    carryover: dict[str, dict] = {}
    for key in ("conflict_resolution_linkage", "reuse_contract"):
        value = gate_payload.get(key)
        if isinstance(value, dict):
            carryover[key] = copy.deepcopy(value)
    return carryover or None


def build_pass_episode_log_append_kwargs(
    *,
    request: Stage4PassEpisodeLogRequest,
    selection_reason: str,
    verdict_reason: str,
    gate_semantics: dict | None,
    fix_pack: dict | None,
    runtime_advisory: str,
    retry_directives: str,
) -> dict[str, object]:
    gate_payload = dict(gate_semantics or {}) if isinstance(gate_semantics, dict) else {}
    return {
        **build_pass_episode_log_payload(request=request),
        "selection_reason": str(selection_reason or ""),
        "verdict_reason": str(verdict_reason or ""),
        "gate_semantics": gate_payload,
        "fix_pack": dict(fix_pack or {}),
        "runtime_advisory": str(runtime_advisory or ""),
        "retry_directives": str(retry_directives or ""),
        "carryover_contracts": build_stage4_episode_log_carryover_contracts(gate_semantics=gate_payload),
    }


def build_reject_episode_log_append_kwargs(
    *,
    request: Stage4RejectEpisodeLogRequest,
    selection_reason: str,
    verdict_reason: str,
    gate_semantics: dict | None,
    fix_pack: dict | None,
    runtime_advisory: str,
    retry_directives: str,
) -> dict[str, object]:
    gate_payload = dict(gate_semantics or {}) if isinstance(gate_semantics, dict) else {}
    reject_artifact_meta = request.reject_artifact_meta or {}
    selection_artifact_meta = request.selection_artifact_meta or {}
    return {
        "ep_num": request.ep_num,
        "round_num": request.round_num,
        "director_result": request.sink_source,
        "initial_verdict": request.initial_verdict,
        "initial_score": request.initial_score,
        "final_verdict": request.final_verdict,
        "final_score": request.final_score,
        "is_patch": request.is_patch,
        "patch_fallback": request.is_patch_fallback,
        "tot_used": request.tot_used,
        "mad_used": request.mad_used,
        "asp_used": request.asp_used,
        "model": request.model,
        "reject_bucket": request.reject_bucket,
        "validation_warnings": request.validation_warnings,
        "feedback_provenance": dict(request.feedback_provenance or {}),
        "patch_trace": request.patch_trace,
        "arc_num": request.arc_num,
        "candidate_key": str(reject_artifact_meta.get("candidate_key", "") or ""),
        "content_hash": str(reject_artifact_meta.get("content_hash", "") or ""),
        "artifact_path": str(reject_artifact_meta.get("artifact_path", "") or ""),
        "selection_candidate_key": str(selection_artifact_meta.get("candidate_key", "") or ""),
        "selection_content_hash": str(selection_artifact_meta.get("content_hash", "") or ""),
        "selection_artifact_path": str(selection_artifact_meta.get("artifact_path", "") or ""),
        "attempt_key": str(request.attempt_key or ""),
        "selection_reason": str(selection_reason or ""),
        "verdict_reason": str(verdict_reason or ""),
        "gate_semantics": gate_payload,
        "fix_pack": dict(fix_pack or {}),
        "runtime_advisory": str(runtime_advisory or ""),
        "retry_directives": str(retry_directives or ""),
        "carryover_contracts": build_stage4_episode_log_carryover_contracts(gate_semantics=gate_payload),
    }


def build_pass_episode_log_artifact_fields(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str | int]:
    return {
        **build_pass_episode_log_artifact_core_fields(request=request),
        **build_pass_episode_log_selection_artifact_fields(request=request),
    }


def build_pass_episode_log_artifact_core_fields(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str | int]:
    return {
        **build_pass_episode_log_attempt_fields(request=request),
        **build_pass_episode_log_logged_artifact_fields(request=request),
    }


def build_pass_episode_log_attempt_fields(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str | int]:
    return {
        "arc_num": request.arc_num,
        "attempt_key": build_attempt_key(
            stage=4,
            ep_num=request.ep_num,
            arc_num=request.arc_num,
            attempt_num=request.round_num + 1,
            session_id=request.session_id,
        ),
    }


def build_pass_episode_log_logged_artifact_fields(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str]:
    return {
        "candidate_key": request.log_artifact_meta["candidate_key"],
        "content_hash": request.log_artifact_meta["content_hash"],
        "artifact_path": request.log_artifact_meta["artifact_path"],
    }


def build_pass_episode_log_selection_artifact_fields(*, request: Stage4PassEpisodeLogRequest) -> dict[str, str]:
    return {
        "selection_candidate_key": str(request.selection_artifact_meta.get("candidate_key", "") or ""),
        "selection_content_hash": str(request.selection_artifact_meta.get("content_hash", "") or ""),
        "selection_artifact_path": str(request.selection_artifact_meta.get("artifact_path", "") or ""),
    }
