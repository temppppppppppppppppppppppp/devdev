"""
Three-phase blueprint runtime orchestration split.
"""
# utf8-hygiene: allow-file legacy mojibake literals remain in untouched runtime strings during readability campaign

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from modules.core.constants import PatchModeThresholds
from modules.models.blueprint import validate_blueprint
from modules.validation.threshold_helper import _threshold

from .base_agent import AgentErrorType

if TYPE_CHECKING:
    from .three_phase_blueprint_generator import ThreePhaseBlueprintGenerator


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
        owner._operator_log(title, level=level, meta=payload)
        if fix_scope:
            owner._operator_log(f"      fix_scope: {fix_scope}", level=level, meta=payload)
        for line in self._preview_feedback_lines(feedback):
            owner._operator_log(f"      사유: {line}", level=level, meta=payload)
        for line in self._preview_issue_lines(issues):
            owner._operator_log(f"      이슈: {line}", level=level, meta=payload)

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
        else:
            # [pre-rerun] 직전 원고 말미 500자를 시간 진실 소스로 전달
            prev_manuscript_ending = ""
            if prev_manuscripts_text:
                prev_manuscript_ending = prev_manuscripts_text.strip()[-500:]
            constraint_block = owner.constraint_compiler.compile(
                arc_data=arc_data,
                ep_num=ep_num,
                prev_blueprint=prev_blueprint,
                prev_blueprints=prev_blueprints,
                genre=genre,
                prev_manuscript_ending=prev_manuscript_ending,
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
        error_type = (
            AgentErrorType.SCHEMA_INCOMPATIBLE
            if AgentErrorType.SCHEMA_INCOMPATIBLE in worker_error_types
            else getattr(owner.ensemble, "last_error_type", None)
        )
        pipeline_result["phases"]["generate"] = {"status": "failed"}
        if error_type:
            pipeline_result["phases"]["generate"]["error_type"] = error_type
            pipeline_result["failure_reason"] = error_type

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
            feedback="Ensemble 생성 실패. 다시 시도합니다."
            if error_type != AgentErrorType.SCHEMA_INCOMPATIBLE
            else "schema_incompatible로 즉시 중단합니다.",
        )
        if error_type == AgentErrorType.SCHEMA_INCOMPATIBLE:
            return _ThreePhasePhase2Result(None, [], should_break=True)

        owner._record_intermediate_reject(
            ep_num=ep_num,
            arc_data=arc_data,
            retry=retry,
            max_retries=max_retries,
            reject_reason="Ensemble 생성 실패. 다시 시도하세요.",
            event_tag="generate_failed",
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
        fix_scope = str(retry_state.prev_fix_scope or "").strip().lower()
        inplace_threshold = int(_threshold("patch_mode.inplace_below", PatchModeThresholds.INPLACE))

        if retry > 0 and fix_scope == "partial" and rejected_strategy:
            single_strategy = rejected_strategy

        use_inplace_patch = (
            retry > 0
            and fix_scope not in ("partial", "full")
            and retry_state.previous_best is not None
            and retry_state.prev_reject_score >= inplace_threshold
        )
        if use_inplace_patch:
            logging.info(" [Patch Mode] retry=%d blueprint in-place patch 시도", retry)
            try:
                best_blueprint = owner._inplace_patch_blueprint(
                    original_blueprint=retry_state.previous_best,
                    director_feedback=retry_state.prev_reject_feedback,
                    ep_num=ep_num,
                    arc_data=arc_data,
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
                best_blueprint, all_candidates = owner.ensemble.generate_ensemble(**ensemble_kwargs)
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

        verdict = self._apply_phase3_quality_gate(
            verdict=validation.verdict,
            score=effective_score,
        )
        if validation.verdict == "PASS" and verdict == "REJECT":
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
            validation_result=validation.validation_result,
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

        continuity_result = director.check_blueprint_continuity_with_cache(
            new_blueprint=best_blueprint,
            ep_num=ep_num,
            db=db,
            limit=10,
        )
        if continuity_result.get("decision") != "REJECT":
            return None

        continuity_feedback = continuity_result.get("feedback", "")
        owner.stats["phase3_reject"] += 1
        retry_state.prev_reject_feedback = continuity_feedback
        retry_state.prev_reject_score = 0
        retry_state.prev_fix_scope = ""
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
        verdict, validation_result = owner.validator.validate(
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
        candidate_advisories = validation_result.get("candidate_advisories", [])
        if isinstance(candidate_advisories, list) and candidate_advisories:
            pipeline_result["phases"]["validate"]["candidate_advisories"] = candidate_advisories[:3]
        selected_candidate_advisory = validation_result.get("selected_candidate_advisory", {})
        if isinstance(selected_candidate_advisory, dict) and selected_candidate_advisory:
            pipeline_result["phases"]["validate"]["selected_candidate_advisory"] = selected_candidate_advisory
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

    def _apply_phase3_quality_gate(self, *, verdict: str, score: int) -> str:
        quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        if verdict == "PASS" and score < quality_gate_score:
            logging.warning(f"[QualityGate] Stage3 PASS but score={score} < {quality_gate_score}; force REJECT")
            return "REJECT"
        return verdict

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
        retry_state.prev_reject_score = score
        retry_state.prev_reject_feedback = feedback
        retry_state.prev_reject_strategy = selected_strategy or ""
        retry_state.prev_fix_scope = validation_result.get("fix_scope", "")
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
        if isinstance(issues, list):
            for issue in issues[:10]:
                if isinstance(issue, dict):
                    issue_category = issue.get("category", "issue")
                    issue_message = issue.get("issue", "")
                    retry_state.prev_validation_warnings.append(f"{issue_category}: {issue_message}".strip(": "))
                elif issue:
                    retry_state.prev_validation_warnings.append(str(issue))

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

        for fix_index in range(max_fix):
            iteration_result = self._run_pass_with_fix_iteration(
                ep_num=ep_num,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                current_blueprint=current_blueprint,
                current_validation=current_validation,
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
                    "[PF-EE] PWF score-stall early-exit: prior=%d current=%d; "
                    "skipping remaining fix rounds",
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
        fix_scope = current_validation.get("fix_scope", "")
        if not fix_scope:
            inplace_thresh = int(_threshold("patch_mode.inplace_below", 60))
            fix_scope = "inplace" if score >= inplace_thresh else "full"
            logging.warning("[PF-1] fix_scope missing; score=%d fallback=%s", score, fix_scope)
        if fix_scope in ("partial", "full"):
            logging.info(f"[TF-33] fix_scope={fix_scope!r} blocks inplace; delegate to generate loop")
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                should_break=True,
            )

        fix_feedback = current_validation.get("re_slice_instruction", "") or current_validation.get("feedback", "")
        logging.info(f"[TF-32-V] Blueprint patch #{fix_index + 1}/{max_fix}")
        self._log_operator_retry_context(
            title=f"[TF-32-V] Blueprint patch #{fix_index + 1}/{max_fix}",
            meta={"phase": "validate", "patch_round": fix_index + 1, "patch_max": max_fix},
            feedback=fix_feedback,
            fix_scope=str(fix_scope or ""),
        )
        try:
            patched_blueprint = owner._inplace_patch_blueprint(
                original_blueprint=current_blueprint,
                director_feedback=fix_feedback,
                ep_num=ep_num,
                arc_data=arc_data,
            )
        except Exception:
            logging.exception("[TF-32-V] inplace_patch_blueprint exception")
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                should_break=True,
            )
        if not patched_blueprint:
            logging.warning("[TF-32-V] patch failed")
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
            )

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
            re_verdict, re_validation = owner.validator.validate(
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
            )
        except Exception:
            logging.exception("[TF-32-V] re-audit exception")
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=current_blueprint,
                current_validation=current_validation,
                should_break=True,
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
        if re_verdict == "PASS":
            re_score = re_validation.get("score", 0)
            try:
                re_score = int(re_score)
            except (ValueError, TypeError):
                re_score = 0
            if re_score < quality_gate_score:
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
                    current_blueprint=current_blueprint,
                    current_validation=current_validation,
                    should_break=True,
                )
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=patched_blueprint,
                current_validation=current_validation,
                fix_ok=True,
            )
        if re_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"):
            return _ThreePhasePassWithFixIterationResult(
                current_blueprint=patched_blueprint,
                current_validation=re_validation,
                fix_ok=re_verdict == "PASS_WITH_WARNING",
            )
        return _ThreePhasePassWithFixIterationResult(
            current_blueprint=current_blueprint,
            current_validation=current_validation,
            should_break=True,
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
        retry_state: _ThreePhaseRetryState,
        ep_num: int,
        arc_data: dict,
        retry: int,
        max_retries: int,
    ) -> _ThreePhasePassWithFixResult:
        owner = self.owner
        last_reaudit_verdict = current_validation.get("verdict", "") or current_validation.get("decision", "")
        if last_reaudit_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING") and current_blueprint != best_blueprint:
            best_blueprint = current_blueprint
            pass_fix_score = current_validation.get("score", score)
            try:
                pass_fix_score = int(pass_fix_score)
            except (ValueError, TypeError):
                pass_fix_score = score
            validation_result["score"] = pass_fix_score
            logging.info("[PF-3] PASS_WITH_FIX exhausted -> adopt latest patched blueprint (score=%d)", pass_fix_score)

        logging.warning("[TF-32-V] Blueprint patch failed -> REJECT")
        self._log_operator_retry_context(
            title=f"[TF-32-V] PASS_WITH_FIX unresolved after {max_fix} patch attempts -> REJECT",
            level="warning",
            meta={
                "phase": "validate",
                "score": score,
                "retry_index": retry + 1,
                "max_retries": max_retries + 1,
                "error_category": "patch_retry_reject",
            },
            feedback=current_validation.get("verdict_reason", "") or current_validation.get("feedback", ""),
            issues=current_validation.get("issues", []),
            fix_scope=str(current_validation.get("fix_scope", "") or ""),
        )
        owner.stats["phase3_reject"] += 1
        feedback = initial_feedback + f"\n[TF-32-V] PASS_WITH_FIX unresolved after {max_fix} patch attempts -> REJECT"
        self._apply_validation_reject_state(
            validation_result=current_validation,
            retry_state=retry_state,
            score=score,
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
        if verdict in ("PASS", "PASS_WITH_FIX"):
            owner.stats["phase3_pass"] += 1
            pipeline_result["final_verdict"] = verdict
            pipeline_result["last_score"] = score
            logging.info(f"[Phase 3] {verdict} - ep{ep_num} blueprint finalized")
            owner._operator_log(
                f"[Phase 3] {verdict} (score={score})",
                meta={"phase": "validate", "verdict": verdict, "score": score},
            )

            if verdict == "PASS_WITH_FIX":
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
                f"[Retry {retry + 1}/{max_retries + 1}] Blueprint ?앹꽦 以?..",
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
