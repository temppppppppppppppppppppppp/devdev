"""
Stage4 director-review/prevalidation runtime orchestration split.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modules.core.constants import smart_truncate
from modules.core.context_advisor import RetrievalSources

if TYPE_CHECKING:
    from modules.core.stage4_interview_round import Stage4InterviewRound


@dataclass
class _DirectorInputPackResult:
    mandatory_context: str
    decision_core: str
    candidate_evidence: str
    reference_appendix: str
    advisory_summary: dict[str, int]


@dataclass
class _DirectorCandidateEvidencePayload:
    parts: list[str]
    advisory_summary: dict[str, int]


@dataclass
class _DirectorAdvisoryPayload:
    parts: list[str]
    summary: dict[str, int]


@dataclass
class _DirectorRetrievalPayload:
    director_memory_context: str
    plan: object | None
    work_focus: dict[str, object]
    work_focus_summary: str


@dataclass
class _DirectorReviewPhaseResult:
    director_result: dict
    director_mandatory_context: str
    selected: str
    verdict: str
    score: int
    reason: str
    error_category: str
    attempt_key: str
    selection_artifact_meta: dict[str, str]


@dataclass
class _DirectorDecisionPayload:
    director_result: dict
    advisory_summary: dict[str, int]
    director_mandatory_context: str
    selected: str
    verdict: str
    score: int
    selection_reason: str
    verdict_reason: str
    reason: str
    error_category: str
    attempt_key: str


@dataclass
class _DirectorDecisionInvocationPayload:
    director_result: dict
    advisory_summary: dict[str, int]
    director_mandatory_context: str


class Stage4DirectorRuntime:
    """Owns Director review and prevalidation runtime orchestration for Stage 4."""

    def __init__(self, owner: "Stage4InterviewRound") -> None:
        self.owner = owner

    def run_pre_director_validation(
        self,
        *,
        candidates: list,
        next_ep: int,
        blueprint: dict,
        prev_text: str,
        hud_report,
        genre_name: str,
        manuscript_validator,
        consistency_validator,
        blocking_validator,
        continuity_validator,
        stage4_spinner=None,
        round_num: int = 0,
        arc_pos: int = 0,
        total_ep_in_arc: int = 0,
        arc_data: dict | None = None,
        prev_manuscript: str = "",
    ) -> tuple[list[dict], str]:
        owner = self.owner
        if arc_data is None:
            arc_data = {}

        if stage4_spinner is not None and hasattr(stage4_spinner, "update_detail"):
            stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · Python 검증")
        owner.ctx.ui.log("   🔍 Python 사전 검증 중...")

        recent_manuscripts = []
        try:
            recent_manuscripts = owner.ctx.current_project.db.get_recent_manuscripts(before_ep=next_ep, limit=5)
        except (AttributeError, Exception) as exc:
            owner.ctx.ui.log(f"   ⚠️ [V64.P4] 최근 원고 로드 실패 (교차검증 약화): {str(exc)[:60]}")

        validation_results = manuscript_validator.validate_all_candidates(
            candidates=candidates,
            blueprint=blueprint,
            prev_manuscript=prev_text,
            hud_report=hud_report,
            recent_manuscripts=recent_manuscripts,
        )

        for index, validation_result in enumerate(validation_results):
            strategy = candidates[index].get("strategy_name", f"후보{index + 1}") if index < len(candidates) else f"후보{index + 1}"
            owner.ctx.ui.log(
                f"      • {strategy}: 경고 {validation_result.get('warning_count', 0)}개, 분량 {validation_result.get('metrics', {}).get('length', 0)}자"
            )

        self.run_director_core_validation_modules(
            candidates=candidates,
            validation_results=validation_results,
            next_ep=next_ep,
            round_num=round_num,
            genre_name=genre_name,
            blueprint=blueprint,
            arc_data=arc_data,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
        )

        director_memory_context = self.collect_director_retrieval_context(
            validation_results=validation_results,
            next_ep=next_ep,
            round_num=round_num,
            blueprint=blueprint,
            prev_text=prev_text,
            genre_name=genre_name,
            arc_pos=arc_pos,
            total_ep_in_arc=total_ep_in_arc,
        )

        self.run_director_optional_validation_modules(
            candidates=candidates,
            validation_results=validation_results,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
        )

        return validation_results, director_memory_context

    def run_director_core_validation_modules(
        self,
        *,
        candidates: list,
        validation_results: list[dict],
        next_ep: int,
        round_num: int,
        genre_name: str,
        blueprint: dict,
        arc_data: dict,
        consistency_validator,
        blocking_validator,
        continuity_validator,
    ) -> None:
        owner = self.owner
        try:
            cv_context = self.build_cv_context(next_ep, genre_name, blueprint, arc_data)
            for candidate_index, candidate in enumerate(candidates):
                candidate_manuscript = candidate.get("manuscript", "")
                if not candidate_manuscript or candidate_index >= len(validation_results):
                    continue
                cv_result = consistency_validator.validate(candidate_manuscript, cv_context)
                cv_violations = cv_result.get("violations", [])
                cv_penalty = cv_result.get("score_penalty", 0)
                if cv_violations:
                    if "structured_violations" not in validation_results[candidate_index]:
                        validation_results[candidate_index]["structured_violations"] = []
                    for violation in cv_violations:
                        reason = violation.get("reason", str(violation))
                        severity = violation.get("severity", "")
                        tagged = f"[{severity}] {reason}" if severity else reason
                        validation_results[candidate_index]["warnings"].append(f"[V63.2] 일관성: {tagged}")
                        validation_results[candidate_index]["structured_violations"].append(violation)
                    validation_results[candidate_index]["warning_count"] = len(
                        validation_results[candidate_index]["warnings"]
                    )
                    validation_results[candidate_index]["focus_points"].append(
                        f"일관성 위반 {len(cv_violations)}건 (감점 {cv_penalty})"
                    )
                    owner.ctx.ui.log(f"      ⚠️ 후보{candidate_index + 1} 일관성 위반 {len(cv_violations)}건")
        except Exception as exc:
            owner.ctx.ui.log(f"      ⚠️ [V63.2] ConsistencyValidator 실행 실패: {str(exc)[:60]}")
            cv_context = {}

        owner._run_blocking_validator_advisories(
            candidates=candidates,
            validation_results=validation_results,
            next_ep=next_ep,
            round_num=round_num,
            cv_context=cv_context,
            blocking_validator=blocking_validator,
        )
        owner._run_director_continuity_and_state_tracker_advisories(
            candidates=candidates,
            validation_results=validation_results,
            next_ep=next_ep,
            cv_context=cv_context,
            continuity_validator=continuity_validator,
        )
        return

    def run_director_optional_validation_modules(
        self,
        *,
        candidates: list,
        validation_results: list[dict],
        blueprint: dict,
        prev_manuscript: str,
    ) -> None:
        owner = self.owner
        pdcl = owner.ctx.get_module("pre_director_checklist")
        if pdcl is None:
            logging.debug("get_module('pre_director_checklist') returned None, skipping")
        if pdcl:
            try:
                checklist_ctx = {}
                if blueprint:
                    checklist_ctx["blueprint"] = blueprint
                if prev_manuscript:
                    checklist_ctx["prev_manuscript"] = prev_manuscript
                try:
                    from modules.core.project_support import resolve_style_dialogue_ratio_target

                    style_target = resolve_style_dialogue_ratio_target(
                        project=getattr(owner.ctx, "current_project", None)
                    )
                    if style_target is not None:
                        checklist_ctx["style_dialogue_ratio_target"] = style_target
                except Exception as exc:
                    logging.debug("[Stage4] style dialogue target load 실패 (비치명): %s", exc)
                for candidate_index, candidate in enumerate(candidates):
                    manuscript = candidate.get("manuscript", "")
                    if not manuscript or candidate_index >= len(validation_results):
                        continue
                    checklist_result = pdcl.check(manuscript, "manuscript", context=checklist_ctx)
                    if not checklist_result.passed:
                        for blocking_reason in checklist_result.blocking_reasons:
                            validation_results[candidate_index]["warnings"].append(f"[PreCheck] {blocking_reason}")
                        validation_results[candidate_index]["warning_count"] = len(validation_results[candidate_index]["warnings"])
                        owner.ctx.ui.log(f"   ⚠️ [PreCheck] 후보{candidate_index + 1}: {checklist_result.summary[:60]}...")
            except Exception as exc:
                logging.warning(f"[SilentPass:PreDirectorChecklist] {exc!s:.100}")

        confidence_calibrator = owner.ctx.get_module("confidence_calibrator")
        if confidence_calibrator is None:
            logging.debug("get_module('confidence_calibrator') returned None, skipping")
        if confidence_calibrator:
            try:
                for candidate_index, candidate in enumerate(candidates):
                    manuscript = candidate.get("manuscript", "")
                    if not manuscript or candidate_index >= len(validation_results):
                        continue
                    confidence = confidence_calibrator.assess(
                        manuscript,
                        "manuscript",
                        context={"blueprint": blueprint, "prev_manuscript": prev_manuscript},
                    )
                    if confidence.concerns:
                        for concern in confidence.concerns[:3]:
                            validation_results[candidate_index]["warnings"].append(
                                f"[Confidence:{confidence.level.value}] {concern}"
                            )
                        validation_results[candidate_index]["warning_count"] = len(validation_results[candidate_index]["warnings"])
            except Exception as exc:
                logging.warning(f"[SilentPass:ConfidenceCalibrator] {exc!s:.100}")

        cross_verifier = owner.ctx.get_module("cross_verifier")
        if cross_verifier is None:
            logging.debug("get_module('cross_verifier') returned None, skipping")
        if cross_verifier and blueprint:
            try:
                from modules.core.cross_agent_verifier import ComplianceLevel

                for candidate_index, candidate in enumerate(candidates):
                    manuscript = candidate.get("manuscript", "")
                    if not manuscript or candidate_index >= len(validation_results):
                        continue
                    compliance = cross_verifier.verify_writer_compliance(
                        manuscript=manuscript,
                        blueprint=blueprint,
                        use_llm=False,
                    )
                    if compliance.level == ComplianceLevel.VIOLATION:
                        for violation in compliance.violations[:5]:
                            violation_msg = violation.get("reason", str(violation)) if isinstance(violation, dict) else str(violation)
                            validation_results[candidate_index]["warnings"].append(
                                f"[CrossVerify:VIOLATION] {violation_msg}"
                            )
                        validation_results[candidate_index]["warning_count"] = len(validation_results[candidate_index]["warnings"])
                    elif compliance.warnings:
                        for warning in compliance.warnings[:3]:
                            warning_msg = warning.get("reason", str(warning)) if isinstance(warning, dict) else str(warning)
                            validation_results[candidate_index]["warnings"].append(
                                f"[CrossVerify:WARNING] {warning_msg}"
                            )
                        validation_results[candidate_index]["warning_count"] = len(validation_results[candidate_index]["warnings"])
            except Exception as exc:
                logging.warning(f"[SilentPass:CrossAgentVerifier] {exc!s:.100}")

        shared_failure_warnings = owner._detect_shared_failure_warnings(validation_results)
        if shared_failure_warnings:
            for result in validation_results:
                if isinstance(result, dict):
                    result["shared_failure_warnings"] = list(shared_failure_warnings)
            logging.info("[QR-6] 전원 동일 위반 감지: %s", ", ".join(shared_failure_warnings))

    def build_cv_context(self, next_ep: int, genre_name: str, blueprint, arc_data=None) -> dict:
        owner = self.owner
        cv_context = {
            "mode": "MANUSCRIPT",
            "genre": genre_name,
            "martial_hud": {},
            "karma_matrix": {},
            "asset_library": {},
            "npc_profiles": owner._resolve_npc_profiles(arc_data),
            "prev_episode_events": [],
            "ep_num": next_ep,
            "blueprint": blueprint if isinstance(blueprint, dict) else {},
            "blueprint_text": str(blueprint or "")[:8000],
        }
        cv_context.update(owner._build_cv_identity_context(next_ep=next_ep, genre_name=genre_name))
        cv_context.update(owner._build_cv_state_tracker_context())
        cv_context.update(owner._build_cv_role_context(next_ep=next_ep))
        return cv_context

    def run_director_review_phase(
        self,
        *,
        stage4_spinner,
        round_num: int,
        round_ctx,
        candidates: list[dict],
        validation_results: list[dict],
        mandatory_context: str,
        writing_directive: str,
        director_feedback: str,
        is_patch: bool,
        is_patch_fallback: bool,
        prev_score: int,
    ) -> _DirectorReviewPhaseResult:
        owner = self.owner
        next_ep = round_ctx.next_ep
        arc_num = round_ctx.arc_data.get("arc_no", 0)

        self._log_director_review_prelude(
            stage4_spinner=stage4_spinner,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            candidates=candidates,
            validation_results=validation_results,
        )

        decision = self._run_director_decision_and_log_summary(
            round_ctx=round_ctx,
            round_num=round_num,
            next_ep=next_ep,
            arc_num=arc_num,
            candidates=candidates,
            validation_results=validation_results,
            mandatory_context=mandatory_context,
            writing_directive=writing_directive,
            director_feedback=director_feedback,
        )

        selection_artifact_meta = owner._persist_director_selection(
            round_ctx=round_ctx,
            next_ep=next_ep,
            round_num=round_num,
            candidates=candidates,
            validation_results=validation_results,
            director_result=decision.director_result,
            advisory_summary=decision.advisory_summary,
            selected=decision.selected,
            verdict=decision.verdict,
            score=decision.score,
            selection_reason=decision.selection_reason,
            verdict_reason=decision.verdict_reason,
            attempt_key=decision.attempt_key,
            is_patch=is_patch,
            is_patch_fallback=is_patch_fallback,
            prev_score=prev_score,
        )
        return _DirectorReviewPhaseResult(
            director_result=decision.director_result,
            director_mandatory_context=decision.director_mandatory_context,
            selected=decision.selected,
            verdict=decision.verdict,
            score=decision.score,
            reason=decision.reason,
            error_category=decision.error_category,
            attempt_key=decision.attempt_key,
            selection_artifact_meta=selection_artifact_meta,
        )

    def _log_director_review_prelude(
        self,
        *,
        stage4_spinner,
        next_ep: int,
        round_num: int,
        arc_num: int,
        candidates: list[dict],
        validation_results: list[dict],
    ) -> None:
        owner = self.owner
        stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · Director 심사")
        owner.ctx.ui.log("   🎬 Director 면담 중...")
        owner._log_attempt_event(
            logging.INFO,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            message=f"director_review_start candidates={len(candidates)}",
        )
        owner.ctx.ui.log(
            f"\n   {'=' * 56}",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="section",
        )
        owner.ctx.ui.log(
            f"   🎬 Director 면담 시작 (제{next_ep}화, {round_num + 1}차)",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="progress",
        )
        owner.ctx.ui.log(
            f"   후보 수: {len(candidates)}개",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="summary",
            meta={"candidate_count": len(candidates)},
        )
        for payload_index, validation_result in enumerate(validation_results):
            warnings = validation_result.get("warnings", [])
            label = ["A", "B", "C"][payload_index] if payload_index < 3 else str(payload_index + 1)
            owner.ctx.ui.log(
                f"   후보 {label}: 경고 {len(warnings)}건, 분량 {len(candidates[payload_index].get('manuscript', ''))}자",
                stage="stage4",
                component="director_review",
                ep_num=next_ep,
                arc_num=arc_num,
                round_num=round_num,
                event_kind="summary",
                meta={
                    "candidate_label": label,
                    "warning_count": len(warnings),
                    "manuscript_length": len(candidates[payload_index].get("manuscript", "")),
                },
            )
            for warning in warnings[:5]:
                owner.ctx.ui.log(
                    f"      - {warning}",
                    stage="stage4",
                    component="director_review",
                    ep_num=next_ep,
                    arc_num=arc_num,
                    round_num=round_num,
                    event_kind="warning",
                    level="warning",
                    meta={"candidate_label": label},
                )
        owner.ctx.ui.log(
            f"   {'=' * 56}",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="section",
        )

    def _run_director_decision_and_log_summary(
        self,
        *,
        round_ctx,
        round_num: int,
        next_ep: int,
        arc_num: int,
        candidates: list[dict],
        validation_results: list[dict],
        mandatory_context: str,
        writing_directive: str,
        director_feedback: str,
    ) -> _DirectorDecisionPayload:
        invocation = self._invoke_director_review(
            round_ctx=round_ctx,
            round_num=round_num,
            next_ep=next_ep,
            candidates=candidates,
            validation_results=validation_results,
            mandatory_context=mandatory_context,
            writing_directive=writing_directive,
            director_feedback=director_feedback,
        )
        decision = self._build_director_decision_payload(
            director_result=invocation.director_result,
            advisory_summary=invocation.advisory_summary,
            director_mandatory_context=invocation.director_mandatory_context,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
        )
        self._log_director_decision_summary(
            decision=decision,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
        )
        return decision

    def _invoke_director_review(
        self,
        *,
        round_ctx,
        round_num: int,
        next_ep: int,
        candidates: list[dict],
        validation_results: list[dict],
        mandatory_context: str,
        writing_directive: str,
        director_feedback: str,
    ) -> _DirectorDecisionInvocationPayload:
        owner = self.owner
        try:
            owner.ctx.perf_timer.start(f"s4_ep{next_ep}_director_r{round_num}")
        except Exception as exc:
            logging.debug("[PerfTimer] start director: %s", exc)

        director_input_pack = self.build_director_input_pack(
            candidates=candidates,
            validation_results=validation_results,
            round_ctx=round_ctx,
            next_ep=next_ep,
            round_num=round_num,
            genre_name=round_ctx.genre_name,
            mandatory_context=mandatory_context,
            writing_directive=writing_directive,
            director_feedback=director_feedback,
            preflight_advisory=round_ctx.preflight_advisory,
        )
        advisory_summary = dict(director_input_pack.advisory_summary)
        director_mandatory_context = director_input_pack.mandatory_context
        advisory_total = sum(int(value or 0) for value in advisory_summary.values())

        # Keep the live console heartbeat separate from durable attempt/audit sinks.
        owner.ctx.ui.log(
            f"   ⏳ Director 판정 대기: 후보 {len(candidates)}개 / advisory {advisory_total}건 / "
            "LLM 응답 대기 중...",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            round_num=round_num,
            event_kind="heartbeat",
            meta={
                "candidate_count": len(candidates),
                "advisory_total": advisory_total,
                "wait_state": "director_llm_review",
            },
        )
        director_result = owner.ctx.agents["director"].select_and_judge_ensemble(
            ep_num=next_ep,
            candidates=candidates,
            validation_results=validation_results,
            blueprint=round_ctx.blueprint,
            previous_ending=round_ctx.prev_ending,
            arc_pos=round_ctx.arc_pos,
            total_eps=round_ctx.total_ep_in_arc,
            retry_count=round_num,
            episode_digest=round_ctx.episode_digest,
            mandatory_context=director_mandatory_context,
            decision_core=director_input_pack.decision_core,
            candidate_evidence=director_input_pack.candidate_evidence,
            reference_appendix=director_input_pack.reference_appendix,
            prev_manuscripts_text=round_ctx.prev_manuscripts_text,
            story_context=round_ctx.story_context,
        )
        director_result = owner._normalize_director_gate_semantics(director_result)
        director_result = owner._enforce_pass_with_fix_contract(director_result)
        try:
            owner.ctx.perf_timer.stop(f"s4_ep{next_ep}_director_r{round_num}")
        except Exception as exc:
            logging.debug("[PerfTimer] stop director: %s", exc)

        return _DirectorDecisionInvocationPayload(
            director_result=director_result,
            advisory_summary=advisory_summary,
            director_mandatory_context=director_mandatory_context,
        )

    def _build_director_decision_payload(
        self,
        *,
        director_result: dict,
        advisory_summary: dict[str, int],
        director_mandatory_context: str,
        next_ep: int,
        round_num: int,
        arc_num: int,
    ) -> _DirectorDecisionPayload:
        owner = self.owner
        selected = director_result.get("selected", "A")
        verdict = director_result.get("final_verdict", director_result.get("verdict", "REJECT"))
        score = director_result.get("score", 0)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
        selection_reason = director_result.get("selection_reason") or ""
        verdict_reason = director_result.get("verdict_reason") or selection_reason or ""
        reason = verdict_reason
        error_category = director_result.get("error_category", "")
        attempt_key = owner._build_round_attempt_key(next_ep=next_ep, round_num=round_num, arc_num=arc_num)

        return _DirectorDecisionPayload(
            director_result=director_result,
            advisory_summary=advisory_summary,
            director_mandatory_context=director_mandatory_context,
            selected=selected,
            verdict=verdict,
            score=score,
            selection_reason=selection_reason,
            verdict_reason=verdict_reason,
            reason=reason,
            error_category=error_category,
            attempt_key=attempt_key,
        )

    def _log_director_decision_summary(
        self,
        *,
        decision: _DirectorDecisionPayload,
        next_ep: int,
        round_num: int,
        arc_num: int,
    ) -> None:
        owner = self.owner
        director_verdict = decision.director_result.get(
            "director_verdict",
            decision.director_result.get("original_verdict", "REJECT"),
        )
        # [TF-3] PASS/PASS_WITH_FIX는 post-select 전까지 provisional 표시
        _provisional_tag = " [provisional — post-select 미완료]" if decision.verdict in ("PASS", "PASS_WITH_FIX") else ""
        owner.ctx.ui.log(
            f"   📊 Director 판정: {decision.verdict}{_provisional_tag} (초기: {director_verdict}, 점수: {decision.score}, 선택: 후보 {decision.selected})"
        )
        owner.ctx.ui.log(f"      └─ 사유: {decision.reason[:80]}...")
        owner._log_attempt_event(
            logging.INFO,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            message="director_verdict=%s final_verdict=%s gate_basis=%s score=%s selected=%s error_category=%s reason=%s",
            args=(
                director_verdict,
                decision.verdict,
                decision.director_result.get("gate_basis", "-"),
                decision.score,
                decision.selected,
                decision.error_category or "-",
                decision.reason[:120],
            ),
        )
        owner.ctx.ui.log(
            "\n   📊 Director 판정 결과:",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="section",
        )
        owner.ctx.ui.log(
            f"      판정: {decision.verdict} | 초기: {director_verdict} | gate: {decision.director_result.get('gate_basis', '-')} | 점수: {decision.score} | 선택: 후보 {decision.selected}",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="result",
            meta={
                "verdict": decision.verdict,
                "director_verdict": director_verdict,
                "gate_basis": decision.director_result.get("gate_basis", ""),
                "score": decision.score,
                "selected_candidate": decision.selected,
            },
        )
        if decision.selection_reason and decision.selection_reason != decision.reason:
            owner.ctx.ui.log(
                f"      선택 사유: {decision.selection_reason[:120]}",
                stage="stage4",
                component="director_review",
                ep_num=next_ep,
                arc_num=arc_num,
                round_num=round_num,
                event_kind="summary",
                meta={"selection_reason": decision.selection_reason[:120]},
            )
        owner.ctx.ui.log(
            f"      판정 근거: gate={decision.director_result.get('gate_basis', '-')} | "
            f"error={decision.error_category or '-'}",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="summary",
            meta={
                "gate_basis": decision.director_result.get("gate_basis", ""),
                "error_category": decision.error_category or "",
            },
        )
        owner.ctx.ui.log(
            f"      사유: {decision.reason[:120]}",
            stage="stage4",
            component="director_review",
            ep_num=next_ep,
            arc_num=arc_num,
            round_num=round_num,
            event_kind="summary",
        )
        action_items = decision.director_result.get("action_items", [])
        if action_items:
            owner.ctx.ui.log(
                "      지시사항:",
                stage="stage4",
                component="director_review",
                ep_num=next_ep,
                arc_num=arc_num,
                round_num=round_num,
                event_kind="summary",
            )
            for action_item in action_items[:5]:
                owner.ctx.ui.log(
                    f"         - {action_item}",
                    stage="stage4",
                    component="director_review",
                    ep_num=next_ep,
                    arc_num=arc_num,
                    round_num=round_num,
                    event_kind="instruction",
                )

    def collect_director_retrieval_context(
        self,
        *,
        validation_results: list[dict],
        next_ep: int,
        round_num: int,
        blueprint: dict,
        prev_text: str,
        genre_name: str,
        arc_pos: int,
        total_ep_in_arc: int,
    ) -> str:
        owner = self.owner
        owner.ctx.ui.log(
            "      ⏳ [SC-5] Director 벡터 메모리 수집 중...",
            stage="stage4",
            component="director_vector_memory",
            ep_num=next_ep,
            round_num=round_num,
            event_kind="progress",
        )
        director_memory_context = ""
        plan = None
        work_focus: dict[str, object] = {}
        work_focus_summary = ""
        sc5_perf_key = f"sc_director_ep{next_ep}_retrieval"
        try:
            owner.ctx.perf_timer.start(sc5_perf_key)
        except Exception as exc:
            logging.debug("[InterviewRound] perf_timer.start 실패 (무시): %s", exc)
        try:
            retrieval_payload = self._build_director_retrieval_payload(
                next_ep=next_ep,
                round_num=round_num,
                blueprint=blueprint,
                prev_text=prev_text,
                genre_name=genre_name,
                arc_pos=arc_pos,
                total_ep_in_arc=total_ep_in_arc,
            )
            director_memory_context = retrieval_payload.director_memory_context
            plan = retrieval_payload.plan
            work_focus = retrieval_payload.work_focus
            work_focus_summary = retrieval_payload.work_focus_summary
        except Exception as exc:
            logging.warning(f"[SilentPass:SC:Director] 벡터 메모리 조립 실패: {exc!s:.100}")
            director_memory_context = ""
        finally:
            try:
                owner.ctx.perf_timer.stop(sc5_perf_key)
            except Exception:
                pass

        source_counts = owner._summarize_retrieval_sources(plan)
        coverage_warnings: list[str] = []
        if work_focus and not work_focus_summary:
            coverage_warnings.append("missing_work_slot_summary")
        if work_focus and plan and not any(
            str(getattr(slot, "category", "")).startswith("work_")
            for slot in (getattr(plan, "slots", []) or [])
        ):
            coverage_warnings.append("work_focus_without_slots")
        if source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0 and "[관계 의미 질의]" not in director_memory_context:
            coverage_warnings.append("missing_relation_slice")
        if coverage_warnings:
            for result in validation_results:
                if isinstance(result, dict):
                    result["coverage_warnings"] = list(coverage_warnings)

        owner._record_retrieval_observation(
            ep_num=next_ep,
            stage="director",
            observation={
                "work_focus_present": bool(work_focus),
                "tracking_slots_count": len(work_focus.get("tracking_slots") or []) if isinstance(work_focus, dict) else 0,
                "scene_engines_count": len(work_focus.get("mandatory_scene_engines") or [])
                if isinstance(work_focus, dict)
                else 0,
                "registry_profiles_count": len(work_focus.get("registry_profiles") or [])
                if isinstance(work_focus, dict)
                else 0,
                "planned_slots_count": len(getattr(plan, "slots", []) or []) if plan else 0,
                "advisor_path_used": bool(plan),
                "work_slot_summary_included": "[작품 추적 슬롯 요약]" in director_memory_context,
                "relation_slice_included": "[관계 의미 질의]" in director_memory_context,
                "source_counts": source_counts,
                "coverage_warnings": coverage_warnings,
                "vector_context_chars": len(director_memory_context),
            },
        )
        return director_memory_context

    def _build_director_retrieval_payload(
        self,
        *,
        next_ep: int,
        round_num: int,
        blueprint: dict,
        prev_text: str,
        genre_name: str,
        arc_pos: int,
        total_ep_in_arc: int,
    ) -> _DirectorRetrievalPayload:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        advisor = getattr(owner.ctx, "context_advisor", None)
        vec_mem = getattr(owner.ctx, "memory", None)
        if not (
            advisor
            and vec_mem
            and next_ep > 1
            and _threshold("smart_retrieval.enabled", True)
            and _threshold("smart_retrieval.director_enabled", True)
        ):
            return _DirectorRetrievalPayload(
                director_memory_context="",
                plan=None,
                work_focus={},
                work_focus_summary="",
            )

        npc_roster = owner._extract_blueprint_npc_roster(blueprint)
        is_arc_boundary = (arc_pos == 1) or (total_ep_in_arc > 0 and arc_pos == total_ep_in_arc)
        is_reject_retry = round_num > 0
        protagonist_name = owner._resolve_director_protagonist_name(genre_name)
        work_focus = owner._resolve_director_work_focus(
            blueprint=blueprint or {},
            prev_ending=prev_text,
            npc_roster=npc_roster,
        )
        work_focus_summary = owner._build_director_work_focus_summary(
            work_focus=work_focus,
            blueprint=blueprint or {},
            protagonist_name=protagonist_name,
        )
        plan = advisor.plan_director_retrieval(
            manuscript="",
            blueprint=blueprint or {},
            current_ep=next_ep,
            npc_roster=npc_roster,
            is_arc_boundary=is_arc_boundary,
            is_reject_retry=is_reject_retry,
            work_focus=work_focus,
        )
        director_memory_context = self._build_director_memory_context_from_plan(
            plan=plan,
            next_ep=next_ep,
            round_num=round_num,
            npc_roster=npc_roster,
            protagonist_name=protagonist_name,
            work_focus_summary=work_focus_summary,
        )
        return _DirectorRetrievalPayload(
            director_memory_context=director_memory_context,
            plan=plan,
            work_focus=work_focus,
            work_focus_summary=work_focus_summary,
        )

    def _build_director_memory_context_from_plan(
        self,
        *,
        plan,
        next_ep: int,
        round_num: int,
        npc_roster: list[str],
        protagonist_name: str,
        work_focus_summary: str,
    ) -> str:
        from modules.validation.threshold_helper import _threshold

        owner = self.owner
        max_results = int(_threshold("context.vector_max_results_s4", 50))
        default_slot_max = int(_threshold("smart_retrieval.slot_max_chars_default", 3000))
        max_npcs_per_slot = int(_threshold("smart_retrieval.max_npcs_per_slot", 5))
        memory_parts = []
        if work_focus_summary:
            memory_parts.append(work_focus_summary)
        memory_parts.extend(
            self._collect_director_slot_memory_parts(
                plan=plan,
                next_ep=next_ep,
                npc_roster=npc_roster,
                protagonist_name=protagonist_name,
                max_results=max_results,
                default_slot_max=default_slot_max,
                max_npcs_per_slot=max_npcs_per_slot,
            )
        )
        if not memory_parts:
            return ""

        budget = int(_threshold("smart_retrieval.director_total_budget", 300000))
        director_memory_context = "\n\n".join(memory_parts)
        if budget > 0 and len(director_memory_context) > budget:
            director_memory_context = smart_truncate(
                director_memory_context,
                max_chars=budget,
                head_chars=max(0, min(int(budget * 0.55), budget - 80)),
            )
        logging.info("[SC-5] Director 벡터 메모리 %s건, %s자", len(memory_parts), len(director_memory_context))
        owner.ctx.ui.log(
            f"      ✅ [SC-5] {len(memory_parts)}건 수집 완료",
            stage="stage4",
            component="director_vector_memory",
            ep_num=next_ep,
            round_num=round_num,
            event_kind="result",
            meta={"memory_part_count": len(memory_parts)},
        )
        return director_memory_context

    def _collect_director_slot_memory_parts(
        self,
        *,
        plan,
        next_ep: int,
        npc_roster: list[str],
        protagonist_name: str,
        max_results: int,
        default_slot_max: int,
        max_npcs_per_slot: int,
    ) -> list[str]:
        memory_parts: list[str] = []
        for slot in getattr(plan, "slots", []) or []:
            slot_part = self._build_director_slot_memory_part(
                slot=slot,
                next_ep=next_ep,
                npc_roster=npc_roster,
                protagonist_name=protagonist_name,
                max_results=max_results,
                default_slot_max=default_slot_max,
                max_npcs_per_slot=max_npcs_per_slot,
            )
            if slot_part:
                memory_parts.append(slot_part)
        return memory_parts

    def _build_director_slot_memory_part(
        self,
        *,
        slot,
        next_ep: int,
        npc_roster: list[str],
        protagonist_name: str,
        max_results: int,
        default_slot_max: int,
        max_npcs_per_slot: int,
    ) -> str:
        owner = self.owner
        vec_mem = getattr(owner.ctx, "memory", None)
        slot_source = str(getattr(slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY)
        slot_category = str(getattr(slot, "category", "director_context") or "director_context")
        slot_query = str(getattr(slot, "query", "") or "").strip()
        if not slot_query:
            return ""

        try:
            slot_max = int(getattr(slot, "max_chars", 0) or 0) or default_slot_max
            if slot_source == RetrievalSources.DB_NPC_HISTORY and hasattr(vec_mem, "retrieve_npc_context"):
                slot_npcs = self._resolve_director_slot_npcs(
                    npc_roster=npc_roster,
                    slot_query=slot_query,
                    max_npcs_per_slot=max_npcs_per_slot,
                )
                if not slot_npcs:
                    return ""
                npc_text = vec_mem.retrieve_npc_context(
                    npc_names=slot_npcs,
                    current_ep=next_ep,
                    max_results=max_results,
                )
                if npc_text:
                    return "[SC:npc]\n" + smart_truncate(
                        str(npc_text),
                        max_chars=slot_max,
                        head_chars=max(0, min(int(slot_max * 0.55), slot_max - 80)),
                    )
                return ""
            if slot_source == RetrievalSources.DB_NPC_RELATIONSHIP:
                rel_text = owner._build_director_relationship_context(
                    db=getattr(owner.ctx.current_project, "db", None),
                    npc_names=npc_roster,
                    protagonist_name=protagonist_name,
                )
                if rel_text:
                    return f"[SC:{slot_category}]\n" + smart_truncate(
                        str(rel_text),
                        max_chars=slot_max,
                        head_chars=max(0, min(int(slot_max * 0.55), slot_max - 80)),
                    )
                return ""
            vec_text = vec_mem.retrieve_multi_query_context(
                queries=[slot_query],
                current_ep=next_ep,
                n_per_query=3,
                max_results=max_results,
            )
            if vec_text:
                return f"[SC:{slot_category}]\n" + smart_truncate(
                    str(vec_text),
                    max_chars=slot_max,
                    head_chars=max(0, min(int(slot_max * 0.55), slot_max - 80)),
                )
        except Exception as exc:
            logging.warning(f"[SilentPass:SC:Director] 슬롯 {slot_category} 실패: {exc!s:.100}")
        return ""

    @staticmethod
    def _resolve_director_slot_npcs(
        *,
        npc_roster: list[str],
        slot_query: str,
        max_npcs_per_slot: int,
    ) -> list[str]:
        slot_npcs = list(npc_roster[:max_npcs_per_slot])
        if slot_npcs:
            return slot_npcs

        slot_npcs = []
        for token in slot_query.replace("|", " ").replace("/", " ").replace(",", " ").split():
            token = token.strip()
            if len(token) < 2:
                continue
            if token not in slot_npcs:
                slot_npcs.append(token)
            if len(slot_npcs) >= max_npcs_per_slot:
                break
        return slot_npcs

    def build_director_input_pack(
        self,
        *,
        candidates: list[dict],
        validation_results: list[dict],
        round_ctx,
        next_ep: int,
        round_num: int,
        genre_name: str,
        mandatory_context,
        writing_directive,
        director_feedback: str,
        preflight_advisory: str,
    ) -> _DirectorInputPackResult:
        owner = self.owner
        decision_core_parts = self._build_director_decision_core_parts(
            round_ctx=round_ctx,
            validation_results=validation_results,
            mandatory_context=mandatory_context,
            writing_directive=writing_directive,
        )
        candidate_evidence_payload = self._build_director_candidate_evidence_parts(
            candidates=candidates,
            validation_results=validation_results,
            round_ctx=round_ctx,
            next_ep=next_ep,
            round_num=round_num,
            genre_name=genre_name,
            preflight_advisory=preflight_advisory,
            director_feedback=director_feedback,
        )
        reference_appendix_parts = self._build_director_reference_appendix_parts(
            candidates=candidates,
            next_ep=next_ep,
        )

        decision_core = owner._format_director_pack("Decision Core", decision_core_parts)
        candidate_evidence = owner._format_director_pack("Candidate Evidence", candidate_evidence_payload.parts)
        reference_appendix = owner._format_director_pack("Reference Appendix", reference_appendix_parts)
        director_mandatory_context = owner._join_director_pack_parts(
            [decision_core, candidate_evidence, reference_appendix]
        )
        return _DirectorInputPackResult(
            mandatory_context=director_mandatory_context,
            decision_core=decision_core,
            candidate_evidence=candidate_evidence,
            reference_appendix=reference_appendix,
            advisory_summary=candidate_evidence_payload.advisory_summary,
        )

    def _build_director_decision_core_parts(
        self,
        *,
        round_ctx,
        validation_results: list[dict],
        mandatory_context,
        writing_directive,
    ) -> list[str]:
        owner = self.owner
        mandatory_text = mandatory_context if isinstance(mandatory_context, str) else str(mandatory_context or "")
        decision_core_parts = [mandatory_text] if mandatory_text else []
        shared_failure_warnings = []

        for validation_result in validation_results:
            shared_failure_warnings = validation_result.get("shared_failure_warnings", [])
            if shared_failure_warnings:
                break
        if shared_failure_warnings:
            decision_core_parts.insert(0, "\n".join(shared_failure_warnings))

        s3_meta = round_ctx.blueprint.get("_stage3_meta", {}) if isinstance(round_ctx.blueprint, dict) else {}
        if s3_meta.get("quality_risk"):
            decision_core_parts.append(
                f"[S3-META 경고] 이 Blueprint는 Stage 3에서 quality_risk로 판정됨 "
                f"(verdict={s3_meta.get('final_verdict', '?')}, score={s3_meta.get('last_score', '?')}). "
                "로직 모순·연속성 결함 가능성 높음. 원고의 논리적 일관성을 중점 검토하세요."
            )
            logging.info("[S3-META] quality_risk=True → Director advisory 주입 (score=%s)", s3_meta.get("last_score"))
        elif s3_meta.get("revision_required"):
            decision_core_parts.append(
                f"[S3-META 주의] 이 Blueprint는 Stage 3에서 추가 손질이 필요한 상태로 통과됨 "
                f"(verdict={s3_meta.get('final_verdict', '?')}, score={s3_meta.get('last_score', '?')}). "
                "치명 리스크로 간주할 필요는 없지만, 서술 밀도·표현 정리 필요성을 염두에 두고 검토하세요."
            )
            logging.info(
                "[S3-META] revision_required=True → Director soft advisory 주입 (score=%s)",
                s3_meta.get("last_score"),
            )

        if not writing_directive.is_empty():
            writing_directive_lines = ["[WritingDirective]"]
            if writing_directive.ending_style:
                writing_directive_lines.append(f"- ending_style: {writing_directive.ending_style}")
            if writing_directive.expression_ban:
                writing_directive_lines.append(f"- expression_ban: {', '.join(writing_directive.expression_ban)}")
            if writing_directive.emotion_required:
                writing_directive_lines.append(f"- emotion_required: {writing_directive.emotion_required}")
            decision_core_parts.insert(0, "\n".join(writing_directive_lines))

        try:
            master_bible = getattr(owner.ctx.current_project, "master_bible", None) or {}
            master_bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
            protagonist_config = master_bible_root.get("protagonist_config", {}) or {}
            pov = str(protagonist_config.get("pov", "") or "").strip()
            external_policy = str(protagonist_config.get("external_pov_insert_policy", "") or "").strip()
            if pov:
                decision_core_parts.insert(0, f"[작품 시점]\n- 기본 POV: {pov}")
            if external_policy:
                decision_core_parts.insert(0, f"[타자 시점 삽입 정책]\n- policy: {external_policy}")
        except Exception as exc:
            logging.debug("[QI-POV] Director POV 주입 실패 (비치명): %s", exc)

        return decision_core_parts

    def _build_director_candidate_evidence_parts(
        self,
        *,
        candidates: list[dict],
        validation_results: list[dict],
        round_ctx,
        next_ep: int,
        round_num: int,
        genre_name: str,
        preflight_advisory: str,
        director_feedback: str,
    ) -> _DirectorCandidateEvidencePayload:
        advisory_payload = self._build_director_advisory_payload(
            candidates=candidates,
            validation_results=validation_results,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            genre_name=genre_name,
        )
        candidate_evidence_parts = list(advisory_payload.parts)
        candidate_evidence_parts.extend(
            self._build_director_temporal_evidence_parts(
                candidates=candidates,
                round_ctx=round_ctx,
            )
        )
        candidate_evidence_parts.extend(
            self._build_director_validation_feedback_evidence_parts(
                validation_results=validation_results,
                preflight_advisory=preflight_advisory,
                director_feedback=director_feedback,
            )
        )
        return _DirectorCandidateEvidencePayload(
            parts=candidate_evidence_parts,
            advisory_summary=advisory_payload.summary,
        )

    def _build_director_advisory_payload(
        self,
        *,
        candidates: list[dict],
        validation_results: list[dict],
        next_ep: int,
        round_num: int,
        arc_num: int,
        genre_name: str,
    ) -> _DirectorAdvisoryPayload:
        owner = self.owner
        advisory_parts = owner._run_advisory_chain(candidates, validation_results, next_ep, genre_name, round_num=round_num)
        advisory_parts = owner._suppress_conflicting_advisories(advisory_parts or [])
        advisory_summary: dict[str, int] = {}
        for advisory in advisory_parts or []:
            advisory_text = str(advisory)
            if "[TruthGate" in advisory_text:
                advisory_summary["truth_gate"] = 1
            if "[LM-B]" in advisory_text or "NpcDrift" in advisory_text:
                advisory_summary["npc_drift"] = 1
            if "[LM-C]" in advisory_text or "NumericDrift" in advisory_text:
                advisory_summary["numeric_drift"] = 1
            if "[LM-D]" in advisory_text or "RelDrift" in advisory_text:
                advisory_summary["rel_drift"] = 1
            if "[LM-E]" in advisory_text or "Flashback" in advisory_text:
                advisory_summary["flashback"] = 1
            if "[LM-F]" in advisory_text or "InfoParadox" in advisory_text:
                advisory_summary["info_paradox"] = 1
            if "[LM-P1]" in advisory_text or "LongTerm" in advisory_text:
                advisory_summary["long_term_rep"] = 1
            if "StyleSignal" in advisory_text:
                advisory_summary["style_signal"] = 1
        owner._last_advisory_summary = dict(advisory_summary)

        formatted_advisory_parts: list[str] = []
        for advisory in advisory_parts or []:
            advisory_text = str(advisory or "").strip()
            if not advisory_text:
                continue
            if "이상 없음" in advisory_text or "경고 0건" in advisory_text:
                short_name = advisory_text.split("]")[0].replace("[", "").strip() if "]" in advisory_text else "Advisory"
                formatted_advisory_parts.append(f"[{short_name}] 이상 없음")
                continue
            if "[TruthGate" in advisory_text:
                body = (
                    advisory_text.replace("[TruthGate Advisory — CRITICAL 경고 시 반드시 REJECT]", "")
                    .replace("[TruthGate Advisory]", "")
                    .replace("[TruthGate]", "")
                    .strip()
                )
                formatted_advisory_parts.append(
                    f"[CRITICAL · TruthGate] {body}" if body else "[CRITICAL · TruthGate]"
                )
                continue
            if any(tag in advisory_text for tag in ("[LM-B]", "NpcDrift")):
                formatted_advisory_parts.append(f"[MAJOR · NpcDrift] {advisory_text}")
                continue
            if any(tag in advisory_text for tag in ("[LM-D]", "RelDrift", "RelationshipDrift")):
                formatted_advisory_parts.append(f"[MAJOR · RelDrift] {advisory_text}")
                continue
            if any(tag in advisory_text for tag in ("[LM-E]", "Flashback")):
                formatted_advisory_parts.append(f"[MAJOR · Flashback] {advisory_text}")
                continue
            if any(tag in advisory_text for tag in ("[LM-F]", "InfoParadox")):
                formatted_advisory_parts.append(f"[MAJOR · InfoParadox] {advisory_text}")
                continue
            if "StyleSignal" in advisory_text:
                formatted_advisory_parts.append(f"[MAJOR · StyleSignal] {advisory_text}")
                continue
            formatted_advisory_parts.append(f"[INFO] {advisory_text}")
        owner._last_advisory_details = list(formatted_advisory_parts)
        owner._log_attempt_event(
            logging.INFO,
            next_ep=next_ep,
            round_num=round_num,
            arc_num=arc_num,
            message="advisory_chain_complete warnings=%d flags=%s",
            args=(
                len(formatted_advisory_parts),
                ",".join(sorted(advisory_summary.keys())) if advisory_summary else "-",
            ),
        )
        return _DirectorAdvisoryPayload(parts=formatted_advisory_parts, summary=advisory_summary)

    def _build_director_temporal_evidence_parts(
        self,
        *,
        candidates: list[dict],
        round_ctx,
    ) -> list[str]:
        owner = self.owner
        candidate_evidence_parts: list[str] = []
        try:
            world_state = getattr(owner.ctx, "world_state", None)
            if world_state:
                cumulative_elapsed = getattr(world_state, "_state", {}).get("cumulative_elapsed") if hasattr(world_state, "_state") else None
                if cumulative_elapsed:
                    from modules.core.narrative_context_formatter import NarrativeContextFormatter

                    time_string = NarrativeContextFormatter.format_cumulative_time(cumulative_elapsed)
                    if time_string:
                        candidate_evidence_parts.append(f"[Timeline] 현재까지 경과 시간: {time_string}")
        except Exception as exc:
            logging.debug("[NC-2] cumulative_elapsed 주입 실패 (비치명): %s", exc)

        try:
            from modules.core.stage4_interview_round import _ns4_extract_time_markers

            ns4_arc_no = int(round_ctx.arc_data.get("arc_no", 0) or 0)
            ns4_arc_idx = ns4_arc_no - 1
            if ns4_arc_idx > 0:
                all_arcs = getattr(owner.ctx.current_project, "arcs", []) or []
                if len(all_arcs) > ns4_arc_idx:
                    prev_arc = all_arcs[ns4_arc_idx - 1]
                    cur_arc = all_arcs[ns4_arc_idx]
                    prev_markers = _ns4_extract_time_markers(prev_arc)
                    cur_markers = _ns4_extract_time_markers(cur_arc)
                    if prev_markers or cur_markers:
                        ns4_lines = ["[Arc 시간 연속성 참고]"]
                        if prev_markers:
                            ns4_lines.append(f"이전 Arc 종료 시점 마커: {', '.join(prev_markers)}")
                        if cur_markers:
                            ns4_lines.append(f"현재 Arc 시간 마커: {', '.join(cur_markers)}")
                        ns4_lines.append(
                            "※ 원고에서 과거 사건 언급 시 '며칠 전'/'얼마 전' 같은 표현이 위 시간 간격과 일치하는지 확인하세요."
                        )
                        candidate_evidence_parts.append("\n".join(ns4_lines))
                        logging.info(
                            "[NS-4-S4] Arc 시간 마커 Director 주입: arc_no=%d, prev=%s, cur=%s",
                            ns4_arc_no,
                            prev_markers,
                            cur_markers,
                        )
        except Exception as exc:
            logging.debug("[NS-4-S4] Director 시간 마커 주입 실패 (비차단): %s", exc)

        try:
            recent_scene_keywords = getattr(round_ctx, "recent_scene_keywords", [])
            if recent_scene_keywords and candidates:
                from modules.core.stage4_context_builder import Stage4ContextBuilder

                for candidate in candidates:
                    candidate_manuscript = candidate.get("manuscript", "") if isinstance(candidate, dict) else ""
                    if candidate_manuscript:
                        similarity_advisory = Stage4ContextBuilder.compute_scene_similarity_advisory(
                            candidate_manuscript,
                            recent_scene_keywords,
                        )
                        if similarity_advisory:
                            candidate_evidence_parts.append(similarity_advisory)
                        break
        except Exception as exc:
            logging.debug("[NC-2] 씬 유사도 advisory 실패 (비치명): %s", exc)

        return candidate_evidence_parts

    def _build_director_validation_feedback_evidence_parts(
        self,
        *,
        validation_results: list[dict],
        preflight_advisory: str,
        director_feedback: str,
    ) -> list[str]:
        candidate_evidence_parts: list[str] = []
        if preflight_advisory:
            candidate_evidence_parts.append(f"🔍 {preflight_advisory}")

        validation_warnings_for_director = []
        for validation_index, validation_result in enumerate(validation_results):
            validation_warnings = validation_result.get("warnings", [])
            if validation_warnings:
                label = ["A", "B", "C"][validation_index] if validation_index < 3 else f"{validation_index + 1}"
                validation_warnings_for_director.append(
                    f"[후보 {label} Python 감지 경고]\n" + "\n".join(validation_warnings[:30])
                )
        if validation_warnings_for_director:
            candidate_evidence_parts.append(
                "[V66.3] Python 사전 검증 결과 (Director 참고용)\n" + "\n\n".join(validation_warnings_for_director)
            )
        if director_feedback and director_feedback.strip():
            candidate_evidence_parts.append(
                "🚨 [V69.1] Python 감지된 원고 충돌 경고 (참고용)\n" + director_feedback.strip()
            )

        return candidate_evidence_parts

    def _build_director_reference_appendix_parts(
        self,
        *,
        candidates: list[dict],
        next_ep: int,
    ) -> list[str]:
        owner = self.owner
        reference_appendix_parts: list[str] = []
        diversity_advisory = owner._build_candidate_diversity_advisory(candidates)
        if diversity_advisory:
            reference_appendix_parts.append(diversity_advisory)

        db = getattr(getattr(owner.ctx, "current_project", None), "db", None)
        reference_only_parts: list[str] = []
        for db_advisory in (
            owner._build_db_pacing_advisory(db, next_ep),
            owner._build_db_satisfaction_advisory(db, next_ep),
            owner._build_db_reveals_advisory(db, next_ep),
            owner._build_db_reflexion_advisory(next_ep),
        ):
            if db_advisory:
                reference_only_parts.append(db_advisory)

        try:
            if db is not None and hasattr(db, "get_strategy_win_rates"):
                win_rates = db.get_strategy_win_rates()
                if win_rates and win_rates.get("total", 0) > 0:
                    win_rate_lines = [f"[TF7-P1-04] 전략별 최근 PASS 선택 비중 (최근 {win_rates['total']}건 기준)"]
                    for key, value in win_rates.items():
                        if key != "total":
                            win_rate_lines.append(f"  - {key}: {int(value * 100)}%")
                    reference_only_parts.append("\n".join(win_rate_lines))
        except Exception as exc:
            logging.debug("[TF7-P1-04] win_rates fetch 실패 (비치명): %s", exc)

        try:
            if db is not None and hasattr(db, "get_fix_scope_stats"):
                fix_scope_stats = db.get_fix_scope_stats()
                if fix_scope_stats and any(row.get("cnt", 0) > 0 for row in fix_scope_stats):
                    fix_scope_lines = ["[A-3] fix_scope 전략별 합격률"]
                    for row in fix_scope_stats:
                        scope = row.get("fix_scope", "?")
                        verdict = row.get("verdict", "?")
                        count = row.get("cnt", 0)
                        if count > 0:
                            fix_scope_lines.append(f"  - {scope} + {verdict}: {count}건")
                    reference_only_parts.append("\n".join(fix_scope_lines))
        except Exception as exc:
            logging.debug("[A-3] fix_scope stats fetch 실패 (비치명): %s", exc)

        reference_only_block = owner._build_reference_only_block(reference_only_parts)
        if reference_only_block:
            reference_appendix_parts.append(reference_only_block)

        try:
            guard = getattr(getattr(owner.ctx, "sys", None), "guard", None)
            if guard and hasattr(guard, "get_director_review_advisory"):
                work_review_advisory = str(guard.get_director_review_advisory() or "").strip()
                if work_review_advisory:
                    reference_appendix_parts.append(work_review_advisory)
        except Exception as exc:
            logging.debug("[Stage4] work review advisory 주입 실패: %s", exc)

        return reference_appendix_parts
