"""
Stage4 round-outcome governance runtime split.
"""

import copy
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

from modules.core.jsonl_io import append_jsonl_record
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.soft_failure import resolve_project_log_dir

if TYPE_CHECKING:
    from modules.core.stage4_orchestrator import Stage4Orchestrator


class Stage4OutcomeRuntime:
    """Owns pass/reject outcome governance for Stage 4 orchestrator."""

    def __init__(self, owner: "Stage4Orchestrator") -> None:
        self.owner = owner

    def _build_retry_attempt_key(self, *, ep_num: int, round_num: int, arc_num: int = 0) -> str:
        owner = self.owner
        interview_round = getattr(owner, "interview_round", None) or getattr(owner, "_interview_round", None)
        if interview_round is not None and hasattr(interview_round, "_build_round_attempt_key"):
            try:
                return str(
                    interview_round._build_round_attempt_key(next_ep=ep_num, round_num=round_num, arc_num=arc_num) or ""
                )
            except Exception:
                pass

        current_project = getattr(getattr(owner, "ctx", None), "current_project", None)
        session_id = resolve_logging_session_id(current_project)
        return str(
            build_attempt_key(
                stage=4,
                ep_num=ep_num,
                arc_num=arc_num,
                attempt_num=round_num + 1,
                session_id=session_id,
            )
        )

    def handle_pass_round_result(
        self,
        *,
        round_ctx,
        round_result,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        owner = self.owner
        owner.ctx.ui.log(
            f"   ✅ [Round {interview_round + 1}] {round_result.verdict}",
            stage="stage4",
            component="round_execution",
            ep_num=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            round_num=interview_round,
            event_kind="result",
            meta={"verdict": round_result.verdict},
        )
        final_manuscript = round_result.final_manuscript
        final_title = round_result.final_title
        final_state_updates = round_result.final_state_updates
        cove_disposition = self.run_cove_pass_verification(
            round_ctx=round_ctx,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            next_ep=next_ep,
            interview_round=interview_round,
            max_rounds=max_rounds,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )
        if cove_disposition is not None:
            return cove_disposition

        return SimpleNamespace(
            accepted=True,
            should_continue=False,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            director_feedback="",
            previous_attempt={},
        )

    def run_cove_pass_verification(
        self,
        *,
        round_ctx,
        final_manuscript: str,
        final_state_updates: dict,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        owner = self.owner
        cove = owner.ctx.get_module("chain_of_verification")
        if not cove or not final_manuscript:
            return None
        try:
            cove_context = self._build_cove_pass_context(
                prev_manuscripts_text=round_ctx.prev_manuscripts_text,
                blueprint=round_ctx.blueprint,
            )
            quick_ok, quick_msg = cove.quick_verify(final_manuscript, cove_context)
            if not quick_ok:
                owner.ctx.ui.log(f"   ⚠️ [CoVe] 사후검증 경고: {quick_msg}")
                cove_context["quick_verify_warnings"] = quick_msg
                return self.run_cove_llm_verification(
                    request=self._build_cove_llm_request(
                        cove=cove,
                        final_manuscript=final_manuscript,
                        final_state_updates=final_state_updates,
                        cove_context=cove_context,
                        quick_msg=quick_msg,
                        next_ep=next_ep,
                        interview_round=interview_round,
                        max_rounds=max_rounds,
                        pathology_counts=pathology_counts,
                        pathology_repeat_emitted=pathology_repeat_emitted,
                    )
                )
        except Exception as exc:
            self.handle_cove_runtime_failure(
                source="quick_verify",
                exc=exc,
                next_ep=next_ep,
                interview_round=interview_round,
                max_rounds=max_rounds,
            )
        return None

    @staticmethod
    def _build_cove_llm_request(
        *,
        cove: object,
        final_manuscript: str,
        final_state_updates: dict,
        cove_context: dict,
        quick_msg: str,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        return SimpleNamespace(
            cove=cove,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            cove_context=cove_context,
            quick_msg=quick_msg,
            next_ep=next_ep,
            interview_round=interview_round,
            max_rounds=max_rounds,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )

    def run_cove_llm_verification(self, *, request):
        owner = self.owner
        try:
            cove_result = request.cove.verify(
                request.final_manuscript,
                request.cove_context,
                content_type="manuscript",
            )
            return self._handle_cove_llm_verification_result(
                request=request,
                cove_result=cove_result,
            )
        except Exception as exc:
            self.handle_cove_runtime_failure(
                source="llm_verify",
                exc=exc,
                next_ep=request.next_ep,
                interview_round=request.interview_round,
                max_rounds=request.max_rounds,
                quick_warning=request.quick_msg,
            )
        return None

    def _handle_cove_llm_verification_result(self, *, request, cove_result):
        retry_kwargs = self._build_cove_retry_kwargs(
            request=request,
            cove_result=cove_result,
        )
        if retry_kwargs:
            return self._build_cove_retry_disposition(**retry_kwargs)
        self._log_cove_llm_issue_summary(cove_result)
        return None

    @staticmethod
    def _build_cove_retry_kwargs(*, request, cove_result) -> dict | None:
        if not cove_result.should_regenerate:
            return None
        return {
            **Stage4OutcomeRuntime._build_cove_retry_request_fields(request=request),
            "cove_result": cove_result,
            **Stage4OutcomeRuntime._build_cove_retry_state_fields(request=request),
        }

    @staticmethod
    def _build_cove_retry_request_fields(*, request) -> dict:
        return {
            "final_manuscript": request.final_manuscript,
            "final_state_updates": request.final_state_updates,
        }

    @staticmethod
    def _build_cove_retry_state_fields(*, request) -> dict:
        return {
            **Stage4OutcomeRuntime._build_cove_retry_episode_state_fields(request=request),
            **Stage4OutcomeRuntime._build_cove_retry_pathology_fields(request=request),
        }

    @staticmethod
    def _build_cove_retry_episode_state_fields(*, request) -> dict:
        return {
            "next_ep": request.next_ep,
            "interview_round": request.interview_round,
            "max_rounds": request.max_rounds,
        }

    @staticmethod
    def _build_cove_retry_pathology_fields(*, request) -> dict:
        return {
            "pathology_counts": request.pathology_counts,
            "pathology_repeat_emitted": request.pathology_repeat_emitted,
        }

    def _log_cove_llm_issue_summary(self, cove_result) -> None:
        if not cove_result.issues:
            return
        cove_warnings = "; ".join(
            str(i.description).strip() for i in cove_result.issues if str(getattr(i, "description", "")).strip()
        )
        self.owner.ctx.ui.log(f"   ⚠️ [CoVe] LLM 검증 경고 (비차단): {cove_warnings}")

    def handle_cove_runtime_failure(
        self,
        *,
        source: str,
        exc: Exception,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        quick_warning: str = "",
    ) -> None:
        source_label = self._resolve_cove_runtime_failure_label(source)
        self._emit_cove_runtime_failure_logs(
            source_label=source_label,
            exc=exc,
            next_ep=next_ep,
            interview_round=interview_round,
            max_rounds=max_rounds,
        )
        self._log_cove_runtime_advisory(
            ep_num=next_ep,
            round_num=interview_round,
            source=source,
            error=exc,
            quick_warning=quick_warning,
        )

    @staticmethod
    def _resolve_cove_runtime_failure_label(source: str) -> str:
        return "LLM" if source == "llm_verify" else "Quick"

    def _emit_cove_runtime_failure_logs(
        self,
        *,
        source_label: str,
        exc: Exception,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
    ) -> None:
        fail_closed_warning, ui_message = self._build_cove_runtime_failure_messages(
            source_label=source_label,
            exc=exc,
        )
        logging.warning(fail_closed_warning)
        self.owner.ctx.ui.log(ui_message)
        self._log_cove_runtime_failure_stage_warning(
            source_label=source_label,
            next_ep=next_ep,
            interview_round=interview_round,
            max_rounds=max_rounds,
        )

    @staticmethod
    def _build_cove_runtime_failure_messages(
        *,
        source_label: str,
        exc: Exception,
    ) -> tuple[str, str]:
        return (
            f"[FailClosed:CoVe:{source_label}] {exc!s}",
            f"   ⚠️ [CoVe] {source_label} 검증 런타임 실패 → Director PASS 유지",
        )

    @staticmethod
    def _log_cove_runtime_failure_stage_warning(
        *,
        source_label: str,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
    ) -> None:
        logging.warning(
            "[Stage4] ep=%d round=%d/%d CoVe %s runtime failure -> PASS preserved",
            *Stage4OutcomeRuntime._build_cove_runtime_stage_warning_args(
                source_label=source_label,
                next_ep=next_ep,
                interview_round=interview_round,
                max_rounds=max_rounds,
            ),
        )

    @staticmethod
    def _build_cove_runtime_stage_warning_args(
        *,
        source_label: str,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
    ) -> tuple[int, int, int, str]:
        return (
            *Stage4OutcomeRuntime._build_cove_runtime_round_fields(
                next_ep=next_ep,
                interview_round=interview_round,
                max_rounds=max_rounds,
            ),
            Stage4OutcomeRuntime._build_cove_runtime_source_field(source_label=source_label),
        )

    @staticmethod
    def _build_cove_runtime_round_fields(*, next_ep: int, interview_round: int, max_rounds: int) -> tuple[int, int, int]:
        return (
            next_ep,
            interview_round + 1,
            max_rounds,
        )

    @staticmethod
    def _build_cove_runtime_source_field(*, source_label: str) -> str:
        return source_label

    @staticmethod
    def _build_cove_pass_context(*, prev_manuscripts_text: str, blueprint: dict | None) -> dict:
        cove_context = {}
        prev_ms = prev_manuscripts_text or ""
        if prev_ms:
            cove_context["prev_manuscript"] = prev_ms[-1500:]
        if blueprint:
            cove_context["blueprint"] = blueprint
        return cove_context

    def _build_cove_retry_disposition(
        self,
        *,
        final_manuscript: str,
        final_state_updates: dict,
        cove_result,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        owner = self.owner
        owner.ctx.ui.log("   ⚠️ [CoVe] 치명적 모순 감지 -> REJECT 전환")
        cove_feedback = cove_result.correction_hints or cove_result.summary
        director_feedback = f"[CoVe 사후검증 실패]\n{cove_feedback}"
        previous_attempt = {
            "score": 90,
            "best_manuscript": final_manuscript,
            "rejection_reason": director_feedback,
            "state_updates": final_state_updates,
            "retry_pathology_source": "cove_fail_closed",
            "cove_fail_closed": True,
            "cove_runtime_failure": False,
            "provisional_pass_downgrade": True,
        }
        logging.warning(
            "[Stage4] ep=%d round=%d/%d CoVe LLM REJECT -> round retry",
            next_ep,
            interview_round + 1,
            max_rounds,
        )
        self.emit_retry_pathology_signal(
            ep_num=next_ep,
            round_num=interview_round,
            previous_attempt=previous_attempt,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )
        return SimpleNamespace(
            accepted=False,
            should_continue=True,
            final_manuscript=None,
            final_title=None,
            final_state_updates=final_state_updates,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
        )

    def _log_cove_runtime_advisory(
        self,
        *,
        ep_num: int,
        round_num: int,
        source: str,
        error: Exception,
        quick_warning: str = "",
    ) -> None:
        owner = self.owner
        current_project = getattr(owner.ctx, "current_project", None)
        logs_dir = resolve_project_log_dir(current_project)
        if logs_dir is None:
            project_name = getattr(current_project, "name", None)
            if not isinstance(project_name, str) or not project_name.strip() or "MagicMock" in project_name:
                project_name = "_unknown_project"
            logs_dir = Path("projects") / project_name / "logs"
        payload = {
            "event": "STAGE4_COVE_RUNTIME_ADVISORY",
            "ep": int(ep_num),  # [Lane4] normalized to authoritative ep key
            "round_num": int(round_num),
            "source": str(source or "").strip(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "director_pass_preserved": True,
            "quick_warning": str(quick_warning or "").strip(),
        }
        try:
            Path(logs_dir).mkdir(parents=True, exist_ok=True)
            append_jsonl_record(Path(logs_dir) / "episode_production.jsonl", payload)
        except Exception as exc:
            logging.warning("[Stage4] CoVe runtime advisory sink write skipped: %s", exc)

        audit_event = getattr(owner.ctx, "audit_event", None)
        if callable(audit_event):
            audit_event(
                "stage4_cove_runtime_advisory",
                "stage4 CoVe runtime advisory observed",
                dict(payload),
            )

    def handle_reject_round_result(
        self,
        *,
        round_ctx,
        round_result,
        next_ep: int,
        interview_round: int,
        max_rounds: int,
        logic_error_streak: int,
        inplace_attempted: bool,
        blueprint_regenerated: bool,
        prev_reject_bucket: str,
        bucket_streak: int,
        prev_dominant_contradiction: str,
        contradiction_type_streak: int,
        score_history: list[int],
        plateau_advisory_emitted: bool,
        tf29_advisory_emitted: bool,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        owner = self.owner
        director_feedback = round_result.director_feedback
        previous_attempt = round_result.previous_attempt
        owner.ctx.ui.log(
            f"   ❌ [Round {interview_round + 1}/{max_rounds}] REJECT → 다음 라운드",
            stage="stage4",
            component="round_execution",
            ep_num=next_ep,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            round_num=interview_round,
            event_kind="result",
            level="warning",
            meta={"verdict": "REJECT"},
        )
        reject_disposition = self.analyze_reject_round(
            round_result=round_result,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            next_ep=next_ep,
            interview_round=interview_round,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
            logic_error_streak=logic_error_streak,
            prev_reject_bucket=prev_reject_bucket,
            bucket_streak=bucket_streak,
            prev_dominant_contradiction=prev_dominant_contradiction,
            contradiction_type_streak=contradiction_type_streak,
            score_history=score_history,
            plateau_advisory_emitted=plateau_advisory_emitted,
            tf29_advisory_emitted=tf29_advisory_emitted,
            blueprint_regenerated=blueprint_regenerated,
        )
        escalation_disposition = self.apply_retry_repair_escalation(
            round_ctx=round_ctx,
            next_ep=next_ep,
            interview_round=interview_round,
            director_feedback=reject_disposition.director_feedback,
            previous_attempt=reject_disposition.previous_attempt,
            logic_error_streak=reject_disposition.logic_error_streak,
            inplace_attempted=inplace_attempted,
            blueprint_regenerated=blueprint_regenerated,
            tf29_advisory=reject_disposition.tf29_advisory,
            dominant_contradiction=reject_disposition.dominant_contradiction,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )
        return SimpleNamespace(
            round_ctx=escalation_disposition.round_ctx,
            director_feedback=escalation_disposition.director_feedback,
            previous_attempt=escalation_disposition.previous_attempt,
            logic_error_streak=escalation_disposition.logic_error_streak,
            inplace_attempted=escalation_disposition.inplace_attempted,
            blueprint_regenerated=escalation_disposition.blueprint_regenerated,
            prev_reject_bucket=reject_disposition.prev_reject_bucket,
            bucket_streak=reject_disposition.bucket_streak,
            prev_dominant_contradiction=reject_disposition.prev_dominant_contradiction,
            contradiction_type_streak=reject_disposition.contradiction_type_streak,
            score_history=reject_disposition.score_history,
            plateau_advisory_emitted=reject_disposition.plateau_advisory_emitted,
            tf29_advisory_emitted=reject_disposition.tf29_advisory_emitted,
        )

    def analyze_reject_round(
        self,
        *,
        round_result,
        director_feedback: str,
        previous_attempt: dict | None,
        logic_error_streak: int,
        prev_reject_bucket: str,
        bucket_streak: int,
        prev_dominant_contradiction: str,
        contradiction_type_streak: int,
        score_history: list[int],
        plateau_advisory_emitted: bool,
        tf29_advisory_emitted: bool,
        blueprint_regenerated: bool,
        next_ep: int = 0,
        interview_round: int = 0,
        arc_num: int = 0,
    ):
        owner = self.owner
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        score_history = list(score_history)
        score_trend = self._apply_reject_score_trend_advisory(
            previous_attempt=previous_attempt,
            director_feedback=director_feedback,
            score_history=score_history,
            plateau_advisory_emitted=plateau_advisory_emitted,
            next_ep=next_ep,
            interview_round=interview_round,
            arc_num=arc_num,
        )
        director_feedback = score_trend.director_feedback
        score_history = score_trend.score_history
        plateau_advisory_emitted = score_trend.plateau_advisory_emitted

        logic_error_streak = (
            logic_error_streak + 1
            if self._should_count_reject_as_logic_like(
                round_result=round_result,
                previous_attempt=previous_attempt,
            )
            else 0
        )

        bucket_disposition = self._apply_reject_bucket_advisory(
            previous_attempt=previous_attempt,
            director_feedback=director_feedback,
            prev_reject_bucket=prev_reject_bucket,
            bucket_streak=bucket_streak,
            blueprint_regenerated=blueprint_regenerated,
            tf29_advisory_emitted=tf29_advisory_emitted,
        )
        director_feedback = bucket_disposition.director_feedback
        prev_reject_bucket = bucket_disposition.prev_reject_bucket
        bucket_streak = bucket_disposition.bucket_streak
        tf29_advisory = bucket_disposition.tf29_advisory
        tf29_advisory_emitted = bucket_disposition.tf29_advisory_emitted

        contradiction_disposition = self._apply_reject_contradiction_advisory(
            previous_attempt=previous_attempt,
            director_feedback=director_feedback,
            logic_error_streak=logic_error_streak,
            prev_dominant_contradiction=prev_dominant_contradiction,
            contradiction_type_streak=contradiction_type_streak,
            blueprint_regenerated=blueprint_regenerated,
        )
        director_feedback = contradiction_disposition.director_feedback
        prev_dominant_contradiction = contradiction_disposition.prev_dominant_contradiction
        contradiction_type_streak = contradiction_disposition.contradiction_type_streak
        dominant_contradiction = contradiction_disposition.dominant_contradiction

        return SimpleNamespace(
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            prev_reject_bucket=prev_reject_bucket,
            bucket_streak=bucket_streak,
            prev_dominant_contradiction=prev_dominant_contradiction,
            contradiction_type_streak=contradiction_type_streak,
            score_history=score_history,
            plateau_advisory_emitted=plateau_advisory_emitted,
            tf29_advisory_emitted=tf29_advisory_emitted,
            tf29_advisory=tf29_advisory,
            dominant_contradiction=dominant_contradiction,
        )

    def _should_count_reject_as_logic_like(
        self,
        *,
        round_result,
        previous_attempt: dict,
    ) -> bool:
        owner = self.owner
        error_category = str(
            getattr(round_result, "error_category", "") or previous_attempt.get("error_category", "") or ""
        ).strip()
        if error_category == "LOGIC_ERROR":
            return True

        if self._is_ifc_quality_issue_logic_like(
            error_category=error_category,
            previous_attempt=previous_attempt,
        ):
            return True

        if self._is_continuity_quality_issue_logic_like(
            error_category=error_category,
            previous_attempt=previous_attempt,
        ):
            return True

        if not owner.get_stage4_policy_bool(
            "retry_escalation",
            "treat_post_select_conflict_as_logic_like",
            default=True,
        ):
            return False

        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        provisional_pass_downgrade = bool(previous_attempt.get("provisional_pass_downgrade", False))
        return bool(
            reject_bucket == "post_select_conflict"
            and (provisional_pass_downgrade or error_category.startswith("POST_SELECT_"))
        )

    @staticmethod
    def _is_ifc_quality_issue_logic_like(
        *,
        error_category: str,
        previous_attempt: dict,
    ) -> bool:
        if error_category != "QUALITY_ISSUE":
            return False

        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        if reject_bucket != "quality_issue":
            return False

        fix_scope_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
        if "[IFC]" not in fix_scope_reasoning:
            return False

        return bool(previous_attempt.get("plateau_detected", False))

    @staticmethod
    def _is_continuity_quality_issue_logic_like(
        *,
        error_category: str,
        previous_attempt: dict,
    ) -> bool:
        if error_category != "QUALITY_ISSUE":
            return False

        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        if reject_bucket != "quality_issue":
            return False

        contradiction_types = {
            str(item or "").strip().lower()
            for item in (previous_attempt.get("contradiction_types") or [])
            if str(item or "").strip()
        }
        continuity_types = {
            "scene_overlap",
            "event_ordering",
            "space_continuity",
            "timeline_arc_consistency",
            "opening_diversity",
            "opening_action_continuity",
        }
        if contradiction_types.intersection(continuity_types):
            return True

        signal_text = "\n".join(
            [
                str(previous_attempt.get("fix_scope_reasoning", "") or ""),
                str(previous_attempt.get("open_review", "") or ""),
                str(previous_attempt.get("rejection_reason", "") or ""),
                str(previous_attempt.get("firewall_reason", "") or ""),
            ]
        ).lower()
        continuity_markers = (
            "space continuity",
            "opening continuity",
            "opening duplication",
            "continuity replay",
            "flashback",
            "직전 화",
            "이전 화",
            "오프닝",
            "공간 연속성",
        )
        return any(marker in signal_text for marker in continuity_markers)

    def _apply_reject_score_trend_advisory(
        self,
        *,
        previous_attempt: dict,
        director_feedback: str,
        score_history: list[int],
        plateau_advisory_emitted: bool,
        next_ep: int = 0,
        interview_round: int = 0,
        arc_num: int = 0,
    ):
        owner = self.owner
        current_score = previous_attempt.get("score", 0)
        try:
            current_score = int(current_score)
        except (TypeError, ValueError):
            current_score = 0
        if current_score > 0:
            score_history.append(current_score)
            if not plateau_advisory_emitted:
                plateau_advisory = ""
                if len(score_history) >= 3 and score_history[-3] > score_history[-2] > score_history[-1]:
                    plateau_advisory = (
                        f"[⚠️ 점수 하락 추세] 최근 점수가 "
                        f"{score_history[-3]}→{score_history[-2]}→{score_history[-1]}로 3연속 하락했습니다. "
                        "현재 수정 루프로는 수렴하지 않고 있습니다. fix_scope를 rewrite 이상으로 넓히거나 "
                        "Blueprint/Arc 구조를 재검토하세요."
                    )
                elif len(score_history) >= 2 and score_history[-2] == score_history[-1]:
                    plateau_advisory = (
                        f"[⚠️ 점수 plateau] 최근 두 라운드의 점수가 {score_history[-1]}점으로 동일합니다. "
                        "동일 수정 루프를 반복 중일 수 있습니다. fix_scope 정책 또는 Blueprint 경계를 우선 검토하세요."
                    )

                if plateau_advisory:
                    attempt_key = self._build_retry_attempt_key(
                        ep_num=next_ep,
                        round_num=interview_round,
                        arc_num=arc_num,
                    )
                    plateau_advisory_emitted = True
                    director_feedback = plateau_advisory + "\n" + director_feedback
                    previous_attempt["score_history"] = list(score_history[-3:])
                    previous_attempt["plateau_detected"] = True
                    existing_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
                    previous_attempt["fix_scope_reasoning"] = (
                        f"{existing_reasoning}\n{plateau_advisory}".strip()
                        if existing_reasoning
                        else plateau_advisory
                    )
                    owner.ctx.ui.log(
                        f"   ⚠️ [QR-7] {str(plateau_advisory)}",
                        stage="stage4",
                        component="retry_lane",
                        ep_num=next_ep,
                        round_num=interview_round,
                        attempt_key=attempt_key,
                        event_kind="advisory",
                    )
        return SimpleNamespace(
            director_feedback=director_feedback,
            score_history=score_history,
            plateau_advisory_emitted=plateau_advisory_emitted,
        )

    def _apply_reject_bucket_advisory(
        self,
        *,
        previous_attempt: dict,
        director_feedback: str,
        prev_reject_bucket: str,
        bucket_streak: int,
        blueprint_regenerated: bool,
        tf29_advisory_emitted: bool,
    ):
        owner = self.owner
        tf29_advisory = ""
        current_bucket = previous_attempt.get("reject_bucket", "")
        if current_bucket and current_bucket == prev_reject_bucket:
            bucket_streak += 1
        else:
            bucket_streak = 1 if current_bucket else 0
        prev_reject_bucket = current_bucket

        if bucket_streak >= 3 and not blueprint_regenerated and not tf29_advisory_emitted:
            bucket_label = {
                "quality_issue": "연출",
                "constraint_violation": "제약 위반",
                "structure_error": "구조",
            }.get(prev_reject_bucket, prev_reject_bucket)
            owner.ctx.ui.log(
                f"   ⚠️ [TF-29] '{bucket_label}' 유형 REJECT {bucket_streak}연속"
                " → 블루프린트 단계 문제 가능성"
            )
            tf29_advisory = (
                f"[⚠️ 반복 실패 패턴 감지] '{bucket_label}' 유형 REJECT가 {bucket_streak}회 연속입니다. "
                "원고 수정만으로 해결되지 않을 가능성이 높습니다. "
                "블루프린트의 해당 영역을 근본적으로 재검토하세요."
            )
            director_feedback = tf29_advisory + "\n" + director_feedback
            tf29_advisory_emitted = True

        return SimpleNamespace(
            director_feedback=director_feedback,
            prev_reject_bucket=prev_reject_bucket,
            bucket_streak=bucket_streak,
            tf29_advisory=tf29_advisory,
            tf29_advisory_emitted=tf29_advisory_emitted,
        )

    def _apply_reject_contradiction_advisory(
        self,
        *,
        previous_attempt: dict,
        director_feedback: str,
        logic_error_streak: int,
        prev_dominant_contradiction: str,
        contradiction_type_streak: int,
        blueprint_regenerated: bool,
    ):
        owner = self.owner
        dominant_contradiction = ""
        contradiction_types = previous_attempt.get("contradiction_types", [])
        if contradiction_types:
            from collections import Counter

            counter = Counter(contradiction_types)
            dominant_contradiction = counter.most_common(1)[0][0] if counter else ""
        if dominant_contradiction and dominant_contradiction == prev_dominant_contradiction:
            contradiction_type_streak += 1
        else:
            contradiction_type_streak = 1 if dominant_contradiction else 0
        prev_dominant_contradiction = dominant_contradiction

        if contradiction_type_streak >= 2 and logic_error_streak >= 2 and not blueprint_regenerated:
            contradiction_label = {
                "타임라인": "시간 순서/연대기",
                "수치": "수치/금액 정합성",
                "생존": "생존/상태",
                "고유명사": "고유명사 충돌",
                "아이템": "아이템/장비",
                "상태": "캐릭터 상태",
            }.get(dominant_contradiction, dominant_contradiction)
            advisory = (
                f"[⚠️ A-4 구조 진단] '{contradiction_label}' 모순이 {contradiction_type_streak}라운드 연속. "
                "이는 Writer 문제가 아닌 Blueprint/Arc 설계의 구조적 결함 가능성이 높습니다. "
                "해당 영역의 Arc를 재검토하세요."
            )
            director_feedback = advisory + "\n" + director_feedback
            owner.ctx.ui.log(
                f"   ⚠️ [A-4] '{contradiction_label}' 모순 {contradiction_type_streak}연속 → Arc 구조 진단"
            )

        return SimpleNamespace(
            director_feedback=director_feedback,
            prev_dominant_contradiction=prev_dominant_contradiction,
            contradiction_type_streak=contradiction_type_streak,
            dominant_contradiction=dominant_contradiction,
        )

    def apply_retry_repair_escalation(
        self,
        *,
        round_ctx,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict | None,
        logic_error_streak: int,
        inplace_attempted: bool,
        blueprint_regenerated: bool,
        tf29_advisory: str,
        dominant_contradiction: str,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ):
        owner = self.owner
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}

        self.emit_retry_pathology_signal(
            ep_num=next_ep,
            round_num=interview_round,
            previous_attempt=previous_attempt,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )

        qr7_disposition = self._apply_qr7_bounded_escalation(
            round_ctx=round_ctx,
            next_ep=next_ep,
            interview_round=interview_round,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            inplace_attempted=inplace_attempted,
            blueprint_regenerated=blueprint_regenerated,
            pathology_counts=pathology_counts,
        )
        if qr7_disposition is not None:
            return qr7_disposition

        s3_meta = round_ctx.blueprint.get("_stage3_meta", {}) if isinstance(round_ctx.blueprint, dict) else {}
        quality_risk = bool(s3_meta.get("quality_risk", False))
        quality_risk_threshold = owner.get_stage4_policy_int(
            "retry_escalation",
            "quality_risk_inplace_threshold",
            default=1,
        )
        default_inplace_threshold = owner.get_stage4_policy_int(
            "retry_escalation",
            "default_inplace_threshold",
            default=2,
        )
        blueprint_regeneration_threshold = owner.get_stage4_policy_int(
            "retry_escalation",
            "blueprint_regeneration_after_inplace_streak",
            default=2,
        )
        v75d_threshold = quality_risk_threshold if quality_risk else default_inplace_threshold
        logging.info(
            "[V75-D] quality_risk=%s -> threshold=%d, streak=%d",
            quality_risk,
            v75d_threshold,
            logic_error_streak,
        )
        if logic_error_streak >= v75d_threshold and not inplace_attempted:
            return owner._apply_v75d_inplace_repair(
                round_ctx=round_ctx,
                next_ep=next_ep,
                interview_round=interview_round,
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                logic_error_streak=logic_error_streak,
                tf29_advisory=tf29_advisory,
                dominant_contradiction=dominant_contradiction,
            )
        if logic_error_streak >= blueprint_regeneration_threshold and inplace_attempted and not blueprint_regenerated:
            return owner._apply_v75b_blueprint_regeneration(
                round_ctx=round_ctx,
                next_ep=next_ep,
                interview_round=interview_round,
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                logic_error_streak=logic_error_streak,
                tf29_advisory=tf29_advisory,
                dominant_contradiction=dominant_contradiction,
            )

        return SimpleNamespace(
            round_ctx=round_ctx,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            inplace_attempted=inplace_attempted,
            blueprint_regenerated=blueprint_regenerated,
        )

    def _apply_qr7_bounded_escalation(
        self,
        *,
        round_ctx,
        next_ep: int,
        interview_round: int,
        director_feedback: str,
        previous_attempt: dict,
        logic_error_streak: int,
        inplace_attempted: bool,
        blueprint_regenerated: bool,
        pathology_counts: dict[str, int],
    ):
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        if not bool(previous_attempt.get("plateau_detected", False)):
            return None

        payload = self.build_retry_pathology_payload(
            ep_num=next_ep,
            round_num=interview_round,
            previous_attempt=previous_attempt,
        )
        fingerprint = str(payload.get("pathology_fingerprint", "") or "").strip()
        repeat_count = int(pathology_counts.get(fingerprint, 0) or 0)
        current_fix_scope = str(previous_attempt.get("fix_scope", "") or "").strip().lower()
        if repeat_count < 2 or current_fix_scope == "full":
            return None

        attempt_key = self._build_retry_attempt_key(
            ep_num=next_ep,
            round_num=interview_round,
            arc_num=round_ctx.arc_data.get("arc_no", 0),
        )
        notice = (
            f"[QR-7 escalation] 동일 retry pathology가 {repeat_count}회 반복되었습니다. "
            "추가 local retry를 억제하고 full rewrite 경로로 reroute합니다."
        )
        previous_attempt["fix_scope"] = "full"
        previous_attempt["repair_scope"] = "full"
        retry_budget_axes = previous_attempt.get("retry_budget_axes")
        if isinstance(retry_budget_axes, dict):
            retry_budget_axes = dict(retry_budget_axes)
            retry_budget_axes["repair"] = "rewrite_regenerate"
            previous_attempt["retry_budget_axes"] = retry_budget_axes
        previous_attempt["qr7_contract"] = {
            "mode": "rewrite_reroute",
            "reason": "repeat_plateau_same_pathology",
            "pathology_fingerprint": fingerprint,
            "repeat_count": repeat_count,
        }
        existing_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
        if notice not in existing_reasoning:
            previous_attempt["fix_scope_reasoning"] = (
                f"{existing_reasoning}\n{notice}".strip() if existing_reasoning else notice
            )

        scope_origin = previous_attempt.get("scope_origin")
        if not isinstance(scope_origin, dict):
            scope_origin = {}
        scope_origin["fix_scope"] = "qr7_plateau_override"
        scope_origin.setdefault("authoritative_fix_scope", "director_authoritative")
        scope_origin.setdefault("repair_scope", "runtime_lane")
        previous_attempt["scope_origin"] = scope_origin

        if notice not in director_feedback:
            director_feedback = f"{notice}\n{director_feedback}".strip()
        self.owner.ctx.ui.log(
            "   ⚠️ [QR-7] repeated plateau -> local retry 차단, full rewrite reroute",
            stage="stage4",
            component="retry_lane",
            ep_num=next_ep,
            round_num=interview_round,
            attempt_key=attempt_key,
            event_kind="policy",
            meta={
                "repeat_count": repeat_count,
                "pathology_fingerprint": fingerprint,
                "reroute_mode": "rewrite_reroute",
            },
        )
        return SimpleNamespace(
            round_ctx=round_ctx,
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            logic_error_streak=logic_error_streak,
            inplace_attempted=inplace_attempted,
            blueprint_regenerated=blueprint_regenerated,
        )

    def build_retry_pathology_payload(
        self,
        *,
        ep_num: int,
        round_num: int,
        previous_attempt: dict | None,
    ) -> dict[str, object]:
        owner = self.owner
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        fix_pack_contract = self._evaluate_retry_fix_pack_contract(previous_attempt)
        reject_bucket = str(previous_attempt.get("reject_bucket", "") or "").strip()
        contradiction_types = self._pathology_contradiction_types(previous_attempt)
        contradiction_type = self._pathology_contradiction_type(previous_attempt)
        gate_basis = str(previous_attempt.get("gate_basis", "") or "").strip()
        fix_scope = str(previous_attempt.get("fix_scope", "") or "").strip()
        authoritative_fix_scope = str(previous_attempt.get("authoritative_fix_scope", "") or "").strip()
        repair_scope = str(previous_attempt.get("repair_scope", "") or "").strip()
        error_category = str(previous_attempt.get("error_category", "") or "").strip()
        pathology_source = str(previous_attempt.get("retry_pathology_source", "") or "").strip()
        fix_scope_reasoning = str(previous_attempt.get("fix_scope_reasoning", "") or "").strip()
        open_review = str(previous_attempt.get("open_review", "") or "").strip()
        firewall_triggered = bool(previous_attempt.get("firewall_triggered", False))
        cove_fail_closed = bool(previous_attempt.get("cove_fail_closed", False))
        cove_runtime_failure = bool(previous_attempt.get("cove_runtime_failure", False))
        provisional_pass_downgrade = bool(previous_attempt.get("provisional_pass_downgrade", False))

        tags: list[str] = []
        if pathology_source:
            tags.append(pathology_source)
        if reject_bucket:
            tags.append(reject_bucket)
        if contradiction_type:
            tags.append(f"contradiction:{contradiction_type}")
        if firewall_triggered:
            tags.append("continuity_firewall")
        if provisional_pass_downgrade:
            tags.append("provisional_pass_downgrade")
        if cove_fail_closed:
            tags.append("cove_fail_closed")
        if cove_runtime_failure:
            tags.append("cove_runtime_failure")
        tags.append(
            "fix_pack_ready"
            if bool(fix_pack_contract.get("ready"))
            else f"fix_pack:{str(fix_pack_contract.get('reason', '') or 'not_ready')}"
        )

        fingerprint = "|".join(tag for tag in tags if tag) or "unclassified_retry_pathology"
        fix_pack_reason = (
            str(previous_attempt.get("fix_pack_reason", "") or "").strip()
            or str(fix_pack_contract.get("reason", "") or "").strip()
        )
        payload = {
            "ep": int(ep_num),  # [Lane4] normalized to authoritative ep key
            "round_num": int(round_num + 1),
            "pathology_fingerprint": fingerprint,
            "pathology_source": pathology_source,
            "reject_bucket": reject_bucket,
            "gate_basis": gate_basis,
            "fix_scope": fix_scope,
            "authoritative_fix_scope": authoritative_fix_scope,
            "repair_scope": repair_scope,
            "error_category": error_category,
            "contradiction_type": contradiction_type,
            "fix_pack_ready": bool(fix_pack_contract.get("ready")),
            "fix_pack_reason": fix_pack_reason,
            "provisional_pass_downgrade": provisional_pass_downgrade,
            "firewall_triggered": firewall_triggered,
            "cove_fail_closed": cove_fail_closed,
            "cove_runtime_failure": cove_runtime_failure,
            "plateau_detected": bool(previous_attempt.get("plateau_detected", False)),
            "score": int(previous_attempt.get("score", 0) or 0),
            "fix_scope_reasoning": fix_scope_reasoning,
            "open_review": open_review,
        }
        if contradiction_types:
            payload["contradiction_types"] = contradiction_types
            payload["dominant_contradiction_type"] = contradiction_type or contradiction_types[0]
        self._enrich_retry_pathology_payload(
            payload=payload,
            previous_attempt=previous_attempt,
            fix_scope=fix_scope,
            authoritative_fix_scope=authoritative_fix_scope,
        )
        return payload

    @staticmethod
    def _enrich_retry_pathology_payload(
        *,
        payload: dict[str, object],
        previous_attempt: dict | None,
        fix_scope: str,
        authoritative_fix_scope: str,
    ) -> None:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        attempt_key = str(previous_attempt.get("attempt_key", "") or "").strip()
        if attempt_key:
            payload["attempt_key"] = attempt_key
        content_hash = str(previous_attempt.get("content_hash", "") or "").strip()
        if content_hash:
            payload["content_hash"] = content_hash
        candidate_key = str(previous_attempt.get("candidate_key", "") or "").strip()
        if candidate_key:
            payload["candidate_key"] = candidate_key
        authoritative_fix_scope_violation = previous_attempt.get("authoritative_fix_scope_violation")
        if isinstance(authoritative_fix_scope_violation, dict):
            payload["authoritative_fix_scope_violation"] = authoritative_fix_scope_violation
        conflict_contract = previous_attempt.get("conflict_contract")
        if isinstance(conflict_contract, dict) and conflict_contract:
            payload["conflict_contract"] = conflict_contract
        # [SSS-T2] Persist reuse_contract to operator-facing sink
        reuse_contract_val = previous_attempt.get("reuse_contract")
        if isinstance(reuse_contract_val, dict) and reuse_contract_val:
            payload["reuse_contract"] = copy.deepcopy(reuse_contract_val)
        for key in ("repair_contract", "scope_authority", "fix_pack_origin"):
            value = previous_attempt.get(key)
            if isinstance(value, dict) and value:
                payload[key] = copy.deepcopy(value)
        # [SSS-T1] Scope origin metadata — distinguishes semantic layers in operator evidence
        existing_scope_origin = previous_attempt.get("scope_origin")
        if isinstance(existing_scope_origin, dict) and existing_scope_origin:
            payload["scope_origin"] = dict(existing_scope_origin)
            payload["scope_origin"].setdefault("authoritative_fix_scope", "director_authoritative")
            payload["scope_origin"].setdefault("repair_scope", "runtime_lane")
            payload["scope_origin"].setdefault(
                "fix_scope",
                (
                    "runtime_widened"
                    if fix_scope and authoritative_fix_scope.lower() != fix_scope.lower()
                    else "director_authoritative"
                ),
            )
        else:
            payload["scope_origin"] = {
                "fix_scope": (
                    "runtime_widened"
                    if fix_scope and authoritative_fix_scope.lower() != fix_scope.lower()
                    else "director_authoritative"
                ),
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            }
        # [SSS-T3] Rationale elision marker
        _rationale_blanked = previous_attempt.get("rationale_blanked_by")
        if _rationale_blanked:
            payload["rationale_blanked_by"] = _rationale_blanked

    def emit_retry_pathology_signal(
        self,
        *,
        ep_num: int,
        round_num: int,
        previous_attempt: dict | None,
        pathology_counts: dict[str, int],
        pathology_repeat_emitted: set[str],
    ) -> None:
        owner = self.owner
        payload = self.build_retry_pathology_payload(
            ep_num=ep_num,
            round_num=round_num,
            previous_attempt=previous_attempt,
        )
        entry = {"event": "STAGE4_RETRY_PATHOLOGY", **payload}
        current_project = getattr(owner.ctx, "current_project", None)
        logs_dir = resolve_project_log_dir(current_project)
        if logs_dir is None:
            project_name = getattr(current_project, "name", None)
            if not isinstance(project_name, str) or not project_name.strip() or "MagicMock" in project_name:
                project_name = "_unknown_project"
            logs_dir = Path("projects") / project_name / "logs"
        log_file = Path(logs_dir) / "episode_production.jsonl"
        try:
            Path(logs_dir).mkdir(parents=True, exist_ok=True)
            append_jsonl_record(log_file, entry)
        except Exception as exc:
            logging.warning("[Stage4] retry pathology sink write skipped: %s", exc)

        audit_event = getattr(owner.ctx, "audit_event", None)
        if callable(audit_event):
            audit_event(
                "stage4_retry_pathology_signal",
                "stage4 retry pathology observed",
                dict(payload),
            )

        fingerprint = str(payload.get("pathology_fingerprint", "") or "").strip()
        if not fingerprint:
            return
        pathology_counts[fingerprint] = int(pathology_counts.get(fingerprint, 0) or 0) + 1
        repeat_count = pathology_counts[fingerprint]
        if repeat_count < 2 or fingerprint in pathology_repeat_emitted:
            return

        repeat_payload = dict(payload)
        repeat_payload["repeat_count"] = repeat_count
        repeat_payload["event"] = "STAGE4_RETRY_PATHOLOGY_REPEAT"
        try:
            append_jsonl_record(log_file, repeat_payload)
        except Exception as exc:
            logging.warning("[Stage4] retry pathology repeat sink write skipped: %s", exc)
        if callable(audit_event):
            audit_event(
                "stage4_retry_pathology_repeat",
                "stage4 retry pathology repeated",
                dict(repeat_payload),
            )
        pathology_repeat_emitted.add(fingerprint)

    def _evaluate_retry_fix_pack_contract(self, previous_attempt: dict | None) -> dict[str, object]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        try:
            return self.owner.interview_round._evaluate_fix_pack_contract(previous_attempt.get("fix_pack"))
        except Exception:
            return {"ready": False, "reason": "contract_eval_failed", "fix_pack": {}}

    @staticmethod
    def _pathology_contradiction_types(previous_attempt: dict | None) -> list[str]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        contradiction_types = previous_attempt.get("contradiction_types") or []
        if not isinstance(contradiction_types, list):
            return []
        return [key for item in contradiction_types if (key := str(item or "").strip())]

    @staticmethod
    def _pathology_contradiction_type(previous_attempt: dict | None) -> str:
        contradiction_types = Stage4OutcomeRuntime._pathology_contradiction_types(previous_attempt)
        if not contradiction_types:
            return ""
        counts: dict[str, int] = {}
        for item in contradiction_types:
            counts[item] = counts.get(item, 0) + 1
        if not counts:
            return ""
        return max(counts.items(), key=lambda pair: pair[1])[0]
