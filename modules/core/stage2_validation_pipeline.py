"""[B-1-6] Stage2 validation pipeline extracted from Stage2Orchestrator."""

import hashlib
import json
import logging
import re
from difflib import SequenceMatcher

from modules.core.constants import AIModels

_JACCARD_SIMILARITY_THRESHOLD = 0.50  # [TF-S2-04] Jaccard 전용 (SemanticPlotGuard.SIMILARITY_THRESHOLD와 분리)


class Stage2ValidationPipeline:
    """Pre-Director validation chain for Stage 2."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

    def run_validation(
        self,
        *,
        refined_arc,
        four_phase_passed: bool,
        all_refined_arcs: list,
        entity_registry_for_director,
        global_arc_no: int,
        current_ep_start: int,
        current_feedback: str,
        generation_method: str,
        constraint_block: str,
        enriched_block: dict,
        draft_validator_passed: bool,
        consensus_passed: bool,
        attempt: int,
        protagonist_name: str,
        constraint_db,
    ) -> dict:
        """[4-R3-d] Pre-Director validation chain.

        Runs DraftValidator, SelfReflector, Consensus, Flow Guard,
        Duplicate Guard, ArcCorrector, and ContinuityInspector.

        Returns dict with action='proceed' or action='retry'.
        """
        from modules.core.spinners import V50_MODULES_AVAILABLE, rich_console

        self.ctx.ui.log("      🔍 [TF-38] Pre-Director 검증 체인 시작")
        _auto_corrections = []  # [TF-25-09] ArcAutoCorrector 수정 내역 추적
        _python_advisories = []  # [TF-25-08] Pre-Director REJECT → advisory 전환
        ReflectionTarget = None
        if V50_MODULES_AVAILABLE:
            try:
                from modules.core.self_reflection import ReflectionTarget as _RT

                ReflectionTarget = _RT
            except ImportError:
                pass

        # [B-1-9b-B1] Pre-validation checks (DraftValidator 1st + SelfReflector + Consensus + Mapping + AutoCorrector)
        b1_result = self._run_pre_validation_checks(
            refined_arc=refined_arc,
            four_phase_passed=four_phase_passed,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            current_ep_start=current_ep_start,
            current_feedback=current_feedback,
            generation_method=generation_method,
            constraint_block=constraint_block,
            enriched_block=enriched_block,
            consensus_passed=consensus_passed,
            attempt=attempt,
            constraint_db=constraint_db,
            V50_MODULES_AVAILABLE=V50_MODULES_AVAILABLE,
            ReflectionTarget=ReflectionTarget,
            rich_console=rich_console,
            _python_advisories=_python_advisories,
            _auto_corrections=_auto_corrections,
        )
        refined_arc = b1_result["refined_arc"]
        consensus_passed = b1_result["consensus_passed"]
        current_feedback = b1_result["current_feedback"]
        suspected_duplicates = b1_result["suspected_duplicates"]
        if b1_result["early_return"] is not None:
            return b1_result["early_return"]

        # [B-1-9b-B2] Flow Guard + Duplicate Guard + data validation
        b2_result = self._run_flow_and_duplicate_guards(
            refined_arc=refined_arc,
            all_refined_arcs=all_refined_arcs,
            global_arc_no=global_arc_no,
            enriched_block=enriched_block,
            attempt=attempt,
            _python_advisories=_python_advisories,
        )
        if b2_result["early_return"] is not None:
            return b2_result["early_return"]

        # [B-1-9b-B3] Full DraftValidator + ArcCorrector
        b3_result = self._run_draft_validator_full(
            refined_arc=refined_arc,
            four_phase_passed=four_phase_passed,
            all_refined_arcs=all_refined_arcs,
            constraint_block=constraint_block,
            global_arc_no=global_arc_no,
            draft_validator_passed=draft_validator_passed,
            _python_advisories=_python_advisories,
        )
        refined_arc = b3_result["refined_arc"]
        draft_validator_passed = b3_result["draft_validator_passed"]

        # [B-1-9b-B4] ContinuityInspector + feedback assembly
        b4_result = self._run_continuity_inspection(
            refined_arc=refined_arc,
            four_phase_passed=four_phase_passed,
            all_refined_arcs=all_refined_arcs,
            entity_registry_for_director=entity_registry_for_director,
            enriched_block=enriched_block,
            global_arc_no=global_arc_no,
            current_ep_start=current_ep_start,
            generation_method=generation_method,
            attempt=attempt,
            protagonist_name=protagonist_name,
            V50_MODULES_AVAILABLE=V50_MODULES_AVAILABLE,
            rich_console=rich_console,
            _python_advisories=_python_advisories,
        )
        refined_arc = b4_result["refined_arc"]

        self.ctx.ui.log("      ✅ [TF-38] Pre-Director 검증 완료 → Director 심사 대기")
        return {
            "action": "proceed",
            "refined_arc": refined_arc,
            "draft_validator_passed": draft_validator_passed,
            "consensus_passed": consensus_passed,
            "suspected_duplicates": suspected_duplicates,
            "corrections_made": _auto_corrections,  # [TF-25-09]
            "python_advisories": _python_advisories,  # [TF-25-08]
        }

    # ─────────────────────────────────────────────────────────────
    # [B-1-9b] Extracted private methods from run_validation()
    # ─────────────────────────────────────────────────────────────

    def _run_pre_validation_checks(
        self,
        *,
        refined_arc,
        four_phase_passed: bool,
        all_refined_arcs: list,
        global_arc_no: int,
        current_ep_start: int,
        current_feedback: str,
        generation_method: str,
        constraint_block: str,
        enriched_block: dict,
        consensus_passed: bool,
        attempt: int,
        constraint_db,
        V50_MODULES_AVAILABLE: bool,
        ReflectionTarget,
        rich_console,
        _python_advisories: list,
        _auto_corrections: list,
    ) -> dict:
        """[B-1-9b-B1] DraftValidator 1st + SelfReflector + Consensus + Arc Mapping + AutoCorrector + Pre-Validation.

        Mutates ``_python_advisories`` and ``_auto_corrections`` in-place.
        Returns dict with refined_arc, consensus_passed, current_feedback,
        suspected_duplicates, and optional early_return.
        """
        # ─────────────────────────────────────────────────────────────
        # [무기 #3] DraftValidator - 정보 수집용
        # ─────────────────────────────────────────────────────────────
        python_advisory = []
        if not four_phase_passed and refined_arc and self.ctx.arc_draft_validator:
            try:
                logging.info(" [무기 #3] DraftValidator 사전 검증...")
                draft_result = self.ctx.arc_draft_validator.validate(
                    arc=refined_arc,
                    prev_arcs=all_refined_arcs,
                    state_tracker=self.ctx.state_tracker,
                )
                advisory_issues = draft_result.get("advisory_issues", [])
                if advisory_issues:
                    logging.info(f" [V60.56] DraftValidator advisory {len(advisory_issues)}개 발견 - LLM에게 전달")
                    for issue in advisory_issues[:3]:
                        if isinstance(issue, dict):
                            logging.info(f"- {issue.get('message', str(issue))[:60]}")
                        else:
                            logging.info(f"- {str(issue)[:60]}")
                    python_advisory.extend(advisory_issues)
                logging.info("✅ [DraftValidator] 사전 검증 통과!")
                # [S2-P1-4] draft_validator_passed는 2차 호출(L256)에서만 설정
                # 1차 호출은 Consensus용 advisory 수집 전용
            except (RuntimeError, ValueError, OSError) as dv_err:
                logging.warning(f" [DraftValidator] 스킵: {str(dv_err)[:50]}")

        # ─────────────────────────────────────────────────────────────
        # [V60.36] SelfReflector
        # ─────────────────────────────────────────────────────────────
        if (
            V50_MODULES_AVAILABLE
            and self.ctx.self_reflector
            and refined_arc
            and generation_method == "analyst"
            and ReflectionTarget
        ):
            self.ctx.ui.log("      🪞 [TF-38] SelfReflector 자기 비판 중...")
            try:
                logging.info(" [SelfReflector] Analyst 자기 비판 시작...")
                arc_str = json.dumps(refined_arc, ensure_ascii=False, indent=2)
                context_str = f"Arc {global_arc_no} 설계. 피드백: {current_feedback or '없음'}"

                reflection_result = self.ctx.self_reflector.reflect_and_improve(
                    output=arc_str, context=context_str, target=ReflectionTarget.ANALYST, force=False
                )

                if reflection_result and reflection_result.improved != arc_str:
                    try:
                        improved_arc = json.loads(reflection_result.improved)
                        # [Sweep55] list 반환 시 dict 보장
                        if isinstance(improved_arc, list):
                            improved_arc = (
                                improved_arc[0] if improved_arc and isinstance(improved_arc[0], dict) else None
                            )
                        if isinstance(improved_arc, dict):
                            refined_arc = improved_arc
                            logging.info(f"✅ [SelfReflector] 자기 개선 완료 (점수: {getattr(reflection_result, 'improvement_score', '?')})"
                            )
                        else:
                            logging.warning(" [SelfReflector] 개선 결과가 dict가 아님, 원본 유지")
                    except json.JSONDecodeError:
                        logging.warning(" [SelfReflector] 개선 결과 파싱 실패, 원본 유지")
                else:
                    logging.info("ℹ [SelfReflector] 개선 불필요")
            except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as sr_err:
                logging.warning(f" [SelfReflector] 스킵: {str(sr_err)[:50]}")

        # ─────────────────────────────────────────────────────────────
        # [V60.36] Consensus 검증
        # ─────────────────────────────────────────────────────────────
        if not four_phase_passed and refined_arc and "consensus" in self.ctx.agents:
            self.ctx.ui.log("      🗳️ [TF-38] Consensus 3-LLM 합의 검증 중...")
            try:
                logging.info(" [Consensus] 3-LLM 합의 검증 시작...")
                with rich_console.status("[bold magenta]🗳️ Consensus 3-LLM 검증 중...[/]", spinner="dots"):
                    consensus_verdict, consensus_result = self.ctx.agents["consensus"].validate_with_consensus(
                        arc=refined_arc,
                        prev_arcs=all_refined_arcs,
                        constraints=constraint_block or "",  # [TF-39] P1-6
                        python_advisory=python_advisory,
                    )

                vote_summary = consensus_result.get("vote_summary", {})
                logging.info(f"- 투표 결과: PASS {vote_summary.get('pass', 0)} / REJECT {vote_summary.get('reject', 0)}"
                )

                if consensus_verdict == "REJECT":
                    critical_issues = consensus_result.get("critical_issues", [])
                    all_issues = consensus_result.get("all_issues", [])
                    logging.warning("❌ [Consensus] REJECT!")
                    logging.warning(f"- CRITICAL: {len(critical_issues)}개")
                    logging.info(f"- 전체 이슈: {len(all_issues)}개")
                    for ci in critical_issues[:3]:
                        logging.warning(f" [{ci.get('category', '?')}] {(ci.get('issue', '?') or '?')[:80]}")

                    feedback_parts = [f"[{ci.get('category')}] {ci.get('issue')}" for ci in critical_issues[:3]]
                    _advisory_msg = "Consensus 검증 실패: " + "; ".join(feedback_parts)
                    _python_advisories.append(
                        {
                            "source": "consensus",
                            "severity": "CRITICAL",
                            "message": _advisory_msg,
                        }
                    )
                    logging.info(f" [TF-25-08] Consensus REJECT → Director advisory: {_advisory_msg[:100]}...")
                else:
                    logging.info("✅ [Consensus] PASS!")
                    consensus_passed = True
                    passed_checks = consensus_result.get("passed_checks", [])
                    if passed_checks:
                        logging.info(f"- 통과 항목: {passed_checks[:3]}")
            except (RuntimeError, ValueError, OSError) as cv_err:
                logging.warning(f" [Consensus] 검증 스킵: {str(cv_err)[:50]}")

        # [데이터 검증]
        if not refined_arc or not isinstance(refined_arc, dict):
            self.ctx.ui.log(f"🚨 [Analyst Error] Arc {global_arc_no} 설계 결과가 유효하지 않음: {type(refined_arc)}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "analyst_error",
                    "invalid response type",
                    {"arc_no": global_arc_no, "type": str(type(refined_arc))},
                )
            current_feedback = "Analyst가 유효한 딕셔너리를 반환하지 않았습니다. JSON 규격을 확인하라."
            return {
                "refined_arc": refined_arc,
                "consensus_passed": consensus_passed,
                "current_feedback": current_feedback,
                "suspected_duplicates": [],
                "early_return": {"action": "retry", "current_feedback": current_feedback},
            }

        # 🧭 [Mapping Validation]
        _pre_mapping_arc = refined_arc
        if callable(getattr(self.ctx, "validate_arc_mapping", None)):
            refined_arc = self.ctx.validate_arc_mapping(refined_arc, enriched_block, global_arc_no, current_ep_start)
            # [B3-P1-5] validate_arc_mapping 반환값이 dict가 아니면 원본 유지
            if not isinstance(refined_arc, dict):
                refined_arc = _pre_mapping_arc

        # ⚡ [V60.25] Auto-Corrector
        if self.ctx.stage2_optimizer:
            try:
                refined_arc, corrections = self.ctx.stage2_optimizer.post_process_arc(
                    arc=refined_arc, prev_arcs=all_refined_arcs
                )
                if corrections:
                    _auto_corrections.extend(corrections)  # [TF-25-09]
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event(
                            "v60_25_auto_correct",
                            "arc auto-corrected",
                            {"arc_no": global_arc_no, "corrections": corrections[:5]},
                        )
            except (RuntimeError, ValueError, TypeError) as ac_err:
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("v60_25_auto_correct_error", str(ac_err)[:100])

        # 🔒 [V49.4] Pre-Validation
        suspected_duplicates = []
        if not four_phase_passed:
            pre_validation = constraint_db.validate_arc_design(refined_arc)
            if not pre_validation["valid"]:
                self.ctx.ui.log("      🔍 [V60.76] 의심 아이템 감지 (Director LLM 재검증 예정)")
                for v in pre_validation["violations"][:2]:
                    self.ctx.ui.log(f"         {v}")
                suspected_duplicates = pre_validation["violations"][:3]
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "constraint_suspected",
                        "suspected duplicates for LLM review",
                        {"arc_no": global_arc_no, "suspected": suspected_duplicates},
                    )

            if pre_validation.get("warnings"):
                for w in pre_validation["warnings"][:2]:
                    self.ctx.ui.log(f"      ⚠️ [V49.4 Warning] {w}")

        return {
            "refined_arc": refined_arc,
            "consensus_passed": consensus_passed,
            "current_feedback": current_feedback,
            "suspected_duplicates": suspected_duplicates,
            "early_return": None,
        }

    def _run_flow_and_duplicate_guards(
        self,
        *,
        refined_arc,
        all_refined_arcs: list,
        global_arc_no: int,
        enriched_block: dict,
        attempt: int,
        _python_advisories: list,
    ) -> dict:
        """[B-1-9b-B2] FlowGuard + DuplicateGuard + 2nd data validation.

        Mutates ``_python_advisories`` in-place.
        Returns dict with optional early_return (action='retry' or None).
        """
        # 🚨 [Stage2 Flow Guard]
        flow_guard = self._stage2_flow_guard(refined_arc)
        if flow_guard.get("status") == "REJECT":
            self.ctx.ui.log(f"   🚨 [Flow Guard] {flow_guard.get('reason')}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("flow_guard", flow_guard.get("reason"), {"arc_no": global_arc_no})

            # 구조적 피드백 조립
            diag = flow_guard.get("diagnostics", {})
            diag_type = diag.get("type", "unknown")
            base_feedback = flow_guard.get("feedback", "서사 폭주/정체 위험이 감지되었습니다.")

            structured_parts = [f"[Flow Guard REJECT — {flow_guard.get('reason', '?')}]"]

            if diag_type == "beat_condensed":
                structured_parts.append(
                    f"측정치: 평균 {diag.get('avg_words', '?')}단어/비트 "
                    f"(최소 기준: {diag.get('min_avg_words', '?')}단어)"
                )
                failing = diag.get("failing_beats", [])
                if failing:
                    structured_parts.append("문제 비트:")
                    for fb in failing:
                        structured_parts.append(
                            f"  - 비트 {fb['idx']} ({fb['words']}단어): "
                            f'"{fb["text"]}" ← 최소 {diag.get("min_word_per_beat", 4)}단어 필요'
                        )
                structured_parts.append("")
                structured_parts.append("[수정 지침]")
                structured_parts.append(
                    "beat_sequence에는 에피소드 제목이 아닌, 각 비트의 '사건 → 행동 → 반응' 트리플릿을 작성해야 합니다."
                )
                structured_parts.append(
                    '나쁜 예: "제11화: 붉은 파도"  →  '
                    '좋은 예: "제11화: 유가 폭등 속 공매도 포지션 위기, '
                    '손절 대신 역베팅 결단, 시장 반전으로 수익 확보"'
                )

            elif diag_type == "beat_count":
                structured_parts.append(
                    f"현재 비트 수: {diag.get('beat_count', '?')}개 / "
                    f"필요: 최소 {diag.get('min_beats', '?')}개 (에피소드 {diag.get('ep_count', '?')}화분)"
                )
                structured_parts.append("[수정 지침] 각 화마다 최소 1개의 독립 비트를 배정하라.")

            elif diag_type == "empty_beats":
                structured_parts.append(
                    f"유효 비트: {diag.get('normalized_count', '?')}개 / 전체 비트: {diag.get('total_beats', '?')}개"
                )
                structured_parts.append("[수정 지침] 비어 있는 비트에 구체적 사건/행동을 기술하라.")

            else:
                structured_parts.append(base_feedback)

            # 재시도 가이드 추가
            if callable(getattr(self.ctx, "get_adaptive_feedback_intensity", None)):
                adaptive = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
                structured_parts.append(f"\n[재시도 {attempt + 1}회차] {adaptive['guidance']}")

            _fg_feedback = "\n".join(structured_parts)

            logging.warning("[TF-25-08] Flow Guard REJECT → Director advisory 전달")
            _python_advisories.append(
                {
                    "source": "flow_guard",
                    "severity": "CRITICAL",
                    "message": _fg_feedback[:2000],
                }
            )

        # 🛡️ [Duplicate Guard]
        if all_refined_arcs:
            prev_tactical = all_refined_arcs[-1].get("tactical_doc", "")
            if self._is_tactical_doc_duplicate(refined_arc.get("tactical_doc", ""), [prev_tactical]):
                self.ctx.ui.log("   🚨 [Duplicate Guard] 전술 설계가 직전 아크와 중복됩니다. 재생성합니다.")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "duplicate_guard",
                        "arc tactical_doc duplicated",
                        {"arc_no": global_arc_no, "prev_arc_no": all_refined_arcs[-1].get("arc_no")},
                    )
                _python_advisories.append(
                    {
                        "source": "duplicate_guard",
                        "severity": "CRITICAL",
                        "message": "직전 아크와 동일한 전술 설계입니다. 사건/공간/인과를 완전히 새로 구성해야 합니다.",
                    }
                )
                logging.info("[TF-25-08] Duplicate Guard REJECT → Director advisory 전달")

        # [안전성 패치] Director 호출 전 필수 데이터 검증
        if not refined_arc or not isinstance(refined_arc, dict):
            self.ctx.ui.log("🚨 [Data Error] refined_arc가 유효하지 않습니다")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("data_validation_error", "refined_arc invalid", {"arc_no": global_arc_no})
            current_feedback = "설계 데이터 구조 오류. 전술 설계를 완전한 JSON으로 재작성하라."
            return {"early_return": {"action": "retry", "current_feedback": current_feedback}}

        if not enriched_block or not isinstance(enriched_block, dict):
            self.ctx.ui.log("🚨 [Data Error] enriched_block이 유효하지 않습니다")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("data_validation_error", "enriched_block invalid", {"arc_no": global_arc_no})
            current_feedback = "농축 데이터 누락. 블록 정보를 포함하여 재설계하라."
            return {"early_return": {"action": "retry", "current_feedback": current_feedback}}

        return {"early_return": None}

    def _run_draft_validator_full(
        self,
        *,
        refined_arc,
        four_phase_passed: bool,
        all_refined_arcs: list,
        constraint_block: str,
        global_arc_no: int,
        draft_validator_passed: bool,
        _python_advisories: list,
    ) -> dict:
        """[B-1-9b-B3] Full DraftValidator + ArcCorrector integration.

        Mutates ``_python_advisories`` in-place.
        Returns dict with refined_arc, draft_validator_passed.
        """
        if not four_phase_passed and self.ctx.arc_draft_validator:
            # [G6] DraftValidator 호출 크래시 방어
            try:
                draft_result = self.ctx.arc_draft_validator.validate(
                    arc=refined_arc,
                    prev_arcs=all_refined_arcs,
                    constraint_block=constraint_block or "",
                    state_tracker=self.ctx.state_tracker,
                )
            except (RuntimeError, ValueError, OSError) as _dv_err:
                logging.warning(f"[G6] DraftValidator 호출 실패 — fail-closed: {_dv_err!s:.100}")
                draft_result = {
                    "valid": False,
                    "score": 0,
                    "advisory_issues": [],
                    "critical_issues": [f"DraftValidator crash: {_dv_err!s:.100}"],
                    "warnings": [],
                }  # [A5-P1-4] fail-closed: crash → REJECT (was synthetic PASS)

            advisory_issues = draft_result.get("advisory_issues", [])
            if advisory_issues:
                self.ctx.ui.log(f"      📋 [V60.56 DraftValidator] Advisory {len(advisory_issues)}개 - LLM이 최종 판단")
                for issue in advisory_issues[:3]:
                    self.ctx.ui.log(f"         📝 {issue}")

            if not draft_result["valid"]:
                self.ctx.ui.log(f"      🚨 [V60.11 DraftValidator] 사전 검증 실패 (점수: {draft_result['score']})")
                for issue in draft_result["critical_issues"][:3]:
                    self.ctx.ui.log(f"         ❌ {issue}")

                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "draft_validation_reject",
                        "draft validation failed",
                        {
                            "arc_no": global_arc_no,
                            "score": draft_result["score"],
                            "critical_count": len(draft_result["critical_issues"]),
                        },
                    )

                # [Sweep53] ArcDraftValidator 반환 키에 맞춤 (issues→critical_issues/warnings)
                critical_only = draft_result.get("critical_issues", [])
                major_only = [{"message": w, "severity": "WARNING"} for w in draft_result.get("warnings", [])]

                if not critical_only and major_only and self.ctx.arc_corrector and self.ctx.use_arc_corrector:
                    self.ctx.ui.log(
                        f"      🔧 [V60.42] CRITICAL 없음, MAJOR {len(major_only)}개 - ArcCorrector 부분 수정 시도"
                    )

                    try:
                        can_correct, correctable_issues, uncorrectable_issues = self.ctx.arc_corrector.can_correct(
                            major_only
                        )

                        if can_correct:
                            corrected_arc, correction_log = self.ctx.arc_corrector.correct(
                                arc=refined_arc, issues=major_only, prev_arcs=all_refined_arcs
                            )

                            if corrected_arc and correction_log.get("success"):
                                refined_arc = corrected_arc
                                corrections_made = correction_log.get("corrections_made", [])
                                corrections_failed = correction_log.get("corrections_failed", [])
                                self.ctx.ui.log(
                                    f"      ✅ [V60.42] ArcCorrector 수정 완료 ({len(corrections_made)}개 수정)"
                                )
                                for fix in corrections_made[:3]:
                                    fix_summary = fix.get("change_summary", fix.get("issue", "")[:50])
                                    self.ctx.ui.log(f"         🔨 {fix_summary}")

                                if callable(getattr(self.ctx, "audit_event", None)):
                                    self.ctx.audit_event(
                                        "arc_corrector_success",
                                        "arc partially corrected",
                                        {
                                            "arc_no": global_arc_no,
                                            "corrections": len(corrections_made),
                                            "failed": len(corrections_failed),
                                        },
                                    )

                                revalidation = self.ctx.arc_draft_validator.validate(
                                    arc=refined_arc,
                                    prev_arcs=all_refined_arcs,
                                    constraint_block=constraint_block or "",
                                    state_tracker=self.ctx.state_tracker,
                                )

                                if revalidation["valid"]:
                                    self.ctx.ui.log(
                                        f"      ✅ [V60.42] 수정 후 재검증 통과 (점수: {revalidation['score']})"
                                    )
                                else:
                                    self.ctx.ui.log("      ⚠️ [V60.42] 수정 후에도 검증 실패")
                                    issues_str = "\n".join([f"- {i}" for i in revalidation["critical_issues"][:3]])
                                    _python_advisories.append(
                                        {
                                            "source": "arc_corrector_revalidation",
                                            "severity": "CRITICAL",
                                            "message": f"ArcCorrector 수정 후에도 실패:\n{issues_str}",
                                        }
                                    )
                            else:
                                reason = correction_log.get("reason", "알 수 없음")
                                self.ctx.ui.log(f"      ⚠️ [V60.42] ArcCorrector 수정 실패: {reason}")
                                if callable(getattr(self.ctx, "audit_event", None)):
                                    self.ctx.audit_event("arc_corrector_fail", reason, {"arc_no": global_arc_no})
                                issues_str = "\n".join([f"- {i.get('message', str(i))}" for i in major_only[:3]])
                                _python_advisories.append(
                                    {
                                        "source": "arc_corrector_fail",
                                        "severity": "CRITICAL",
                                        "message": f"V60.42 수정 불가:\n{issues_str}",
                                    }
                                )
                        else:
                            uncorr_msgs = [(i.get("message", "") or "")[:30] for i in uncorrectable_issues[:2]]
                            self.ctx.ui.log(f"      ⚠️ [V60.42] 수정 불가: {', '.join(uncorr_msgs)}")
                            issues_str = "\n".join([f"- {i.get('message', str(i))}" for i in major_only[:3]])
                            _python_advisories.append(
                                {
                                    "source": "arc_corrector_uncorrectable",
                                    "severity": "CRITICAL",
                                    "message": f"수정 불가:\n{issues_str}",
                                }
                            )

                    except (RuntimeError, ValueError) as corr_err:
                        self.ctx.ui.log(f"      ⚠️ [V60.42] ArcCorrector 오류: {str(corr_err)[:50]}")
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event("arc_corrector_error", str(corr_err)[:100])
                        issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                        _python_advisories.append(
                            {
                                "source": "arc_corrector_error",
                                "severity": "CRITICAL",
                                "message": f"V60.11 검증 실패 + Corrector 오류:\n{issues_str}",
                            }
                        )
                else:
                    issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                    _python_advisories.append(
                        {
                            "source": "draft_validator",
                            "severity": "CRITICAL",
                            "message": (
                                f"V60.11 DraftValidator 사전 검증 실패 (점수: {draft_result['score']}/100)\n"
                                f"문제점:\n{issues_str}"
                            ),
                        }
                    )
            else:
                self.ctx.ui.log(f"      ✅ [V60.11 DraftValidator] 사전 검증 통과 (점수: {draft_result['score']})")
                draft_validator_passed = True  # [감리] 2차 DraftValidator 통과 시 플래그 설정
                if draft_result["warnings"]:
                    for w in draft_result["warnings"][:2]:
                        self.ctx.ui.log(f"         ⚠️ {w}")

        return {
            "refined_arc": refined_arc,
            "draft_validator_passed": draft_validator_passed,
        }

    def _run_continuity_inspection(
        self,
        *,
        refined_arc,
        four_phase_passed: bool,
        all_refined_arcs: list,
        entity_registry_for_director,
        enriched_block: dict,
        global_arc_no: int,
        current_ep_start: int,
        generation_method: str,
        attempt: int,
        protagonist_name: str,
        V50_MODULES_AVAILABLE: bool,
        rich_console,
        _python_advisories: list,
    ) -> dict:
        """[B-1-9b-B4] ContinuityInspector + feedback assembly + failure recording.

        Mutates ``_python_advisories`` in-place.
        Returns dict with refined_arc.
        """
        if not four_phase_passed and "continuity_inspector" in self.ctx.agents:
            self.ctx.ui.log(f"      🔍 [V49] Arc {global_arc_no} 연속성 검증 중...")

            refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
            refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

            try:  # [S2-001] ContinuityInspector 예외 전파 차단 → retry 변환
                with rich_console.status(f"[bold yellow]🔍 Arc {global_arc_no} 연속성 검증 중...[/]", spinner="dots"):
                    continuity_result = self.ctx.agents["continuity_inspector"].inspect_arc(
                        current_arc=refined_arc,
                        prev_arcs=all_refined_arcs,
                        entity_registry=entity_registry_for_director,
                    )
            except (RuntimeError, ValueError, OSError) as _ci_err:
                logging.warning("[TF-39] ContinuityInspector 예외 → advisory 전환: %s", str(_ci_err)[:100])
                _python_advisories.append(
                    {
                        "source": "continuity_inspector_error",
                        "severity": "MAJOR",
                        "message": f"연속성 검증 런타임 오류 ({type(_ci_err).__name__}). Director가 직접 연속성 검증 필요.",
                    }
                )
                continuity_result = {
                    "decision": "PASS",
                    "severity": "UNKNOWN",
                    "violations": [],
                    "warnings": [f"CI runtime error: {_ci_err}"],
                }

            if continuity_result.get("decision") == "REJECT":
                severity = continuity_result.get("severity", "UNKNOWN")
                violations = continuity_result.get("violations", [])

                self.ctx.ui.log(f"      🚨 [V49 REJECT] Arc 연속성 위반 감지 (심각도: {severity})")
                for v in violations[:3]:
                    self.ctx.ui.log(f"         - {v.get('type', 'unknown')}: {(v.get('description') or '')[:100]}")

                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "arc_continuity_reject",
                        "continuity violation detected",
                        {"arc_no": global_arc_no, "severity": severity, "violations_count": len(violations)},
                    )

                # [V51.4] 실패 기록
                if V50_MODULES_AVAILABLE and self.ctx.failure_learner:
                    for v in violations[:3]:
                        self.ctx.failure_learner.record_failure(
                            stage=2,
                            episode=current_ep_start,
                            arc=global_arc_no,
                            reason=f"{v.get('type', 'unknown')}: {(v.get('description') or '')[:150]}",
                            details={"severity": severity, "violation": v},
                        )

                # [V60.2] PassRateMonitor
                if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
                    try:
                        self.ctx.pass_rate_monitor.record_attempt(
                            stage=2,
                            episode=global_arc_no,
                            arc=global_arc_no,
                            attempt_num=attempt + 1,
                            success=False,
                            reject_reason=f"ContinuityInspector: {severity} - {violations[0].get('type', '') if violations else 'unknown'}",
                            generation_method=generation_method,
                        )
                    except Exception as e:  # [V64.P4] OPTIONAL: metrics recording
                        logging.debug(f"[SILENT] metrics recording: {e}")
                        pass  # PassRateMonitor failure is non-blocking

                # [V60.25] Stage2Optimizer
                if self.ctx.stage2_optimizer:
                    try:
                        for v in violations[:3]:
                            self.ctx.stage2_optimizer.failure_memory.record_failure(
                                arc_no=global_arc_no,
                                failure_type=v.get("type", "unknown"),
                                details=v.get("description", "")[:200],
                            )
                    except Exception as e:
                        self.ctx.ui.log(f"      ⚠️ [V60.25] 실패 기록 오류 (무시): {str(e)[:50]}")

                # [V49.6] 구체적 위반 내용을 피드백에 포함
                violation_details = []
                banned_items = []

                for v in violations[:3]:
                    v_type = v.get("type", "unknown")
                    v_desc = v.get("description", "")[:200]
                    violation_details.append(f"[{v_type}] {v_desc}")
                    if v_type == "duplicate_acquisition":
                        item_name = v.get("item_or_subject", "")
                        if item_name:
                            banned_items.append(item_name)

                banned_items_warning = ""
                if banned_items:
                    banned_list = ", ".join(banned_items)
                    banned_items_warning = (
                        f"\n\n🚫🚫🚫 [획득 금지 아이템 - 절대 준수] 🚫🚫🚫\n"
                        f"다음 아이템들은 이미 이전 Arc에서 획득했습니다:\n"
                        f"  → {banned_list}\n\n"
                        f"[필수 조치]\n"
                        f"1. 위 아이템을 '획득'하는 장면을 설계하지 마세요.\n"
                        f"2. 대신 '이미 소지 중'인 상태로 시작하여 '사용'하세요.\n"
                        f"3. 예: '허리에 찬 백근 대도를 뽑아 들었다' (O)\n"
                        f"4. 예: '백근 대도를 새로 획득했다' (X - REJECT됨)"
                    )

                prev_state_reminder = ""
                if all_refined_arcs:
                    last = all_refined_arcs[-1]
                    last_joint = last.get("joint_docs", {})
                    last_status = last.get("status_shadow", {})
                    _energy_loss = last_status.get("internal_energy_loss", "?")
                    _energy_line = f"- 내공 소모: {_energy_loss}\n" if _energy_loss not in ("해당없음", "") else ""
                    prev_state_reminder = (
                        f"\n\n📌 [직전 Arc {last.get('arc_no', '?')} 확정 상태 - 반드시 계승할 것]:\n"
                        f"- 위치: {last_joint.get('final_location', '?')}\n"
                        f"- 소지품: {last_joint.get('physical_inventory', '?')}\n"
                        f"{_energy_line}"
                        f"- 부상: {last_status.get('expected_injuries', '?')}"
                    )

                if callable(getattr(self.ctx, "generate_structured_arc_feedback", None)):
                    structured_feedback = self.ctx.generate_structured_arc_feedback(
                        continuity_result=continuity_result, prev_arcs=all_refined_arcs, arc_no=global_arc_no
                    )
                else:
                    structured_feedback = ""

                if callable(getattr(self.ctx, "get_adaptive_feedback_intensity", None)):
                    adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
                    intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
                else:
                    intensity_guide = ""

                if callable(getattr(self.ctx, "build_strong_kind_feedback", None)):
                    strong_kind_feedback = self.ctx.build_strong_kind_feedback(
                        violations=violations, attempt=attempt, protagonist_name=protagonist_name or "주인공"
                    )
                else:
                    strong_kind_feedback = ""

                if callable(getattr(self.ctx, "build_focused_context", None)):
                    focused_context = self.ctx.build_focused_context(
                        violations=violations,
                        prev_arcs=all_refined_arcs,
                        protagonist_name=protagonist_name or "주인공",
                    )
                else:
                    focused_context = ""

                # [TF-25-08] ContinuityInspector REJECT → Director advisory 전환
                _ci_feedback = (
                    f"{strong_kind_feedback}\n\n"
                    f"{focused_context}{structured_feedback or ''}{banned_items_warning}{prev_state_reminder}"
                )

                _python_advisories.append(
                    {
                        "source": "continuity_inspector",
                        "severity": "CRITICAL",
                        "message": _ci_feedback[:3000],
                    }
                )
                self.ctx.ui.log(
                    f"      📋 [TF-25-08] ContinuityInspector REJECT → Director advisory ({len(_ci_feedback)}자)"
                )
            else:
                corrected_joint_docs = continuity_result.get("corrected_joint_docs")
                if corrected_joint_docs:
                    refined_arc["joint_docs"] = corrected_joint_docs
                    enriched_block["joint_docs"] = corrected_joint_docs
                    self.ctx.ui.log("      🔧 [V49.2] joint_docs 자동 수정 반영됨")

                corrected_state = continuity_result.get("corrected_state_constraints")
                if corrected_state:
                    refined_arc["state_constraints"] = corrected_state
                    self.ctx.ui.log("      🔧 [V60.13] state_constraints 자동 수정 반영됨")

                warnings = continuity_result.get("warnings", [])
                if warnings:
                    self.ctx.ui.log(f"      ⚠️ [V49] Arc 연속성 경고 {len(warnings)}개 (PASS)")
                else:
                    self.ctx.ui.log("      ✅ [V49] Arc 연속성 검증 통과")

                if self.ctx.stage2_optimizer:
                    try:
                        self.ctx.stage2_optimizer.example_manager.add_successful_arc(
                            arc=refined_arc  # [V70] arc_no 불필요 kwarg 제거
                        )
                        self.ctx.ui.log("      📚 [V60.25] 성공 Arc 예시 저장됨")
                    except Exception as e:  # [V64.P4] OPTIONAL: success example storage
                        logging.debug(f"[SILENT] success example storage: {e}")
                        pass  # Stage2Optimizer example save failure is non-blocking

        return {"refined_arc": refined_arc}

    def _normalize_tactical_text(self, text: str) -> str:
        """[V64.P3] 전술서 텍스트 정규화"""
        if not isinstance(text, str):
            return ""
        normalized = text
        for _ in range(2):
            normalized = normalized.replace("\\\\n", "\\n").replace("\\\\t", "\\t")
        normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _is_tactical_doc_duplicate(
        self, candidate_text: str, reference_texts: list, threshold: float = 0.92
    ) -> bool:  # [TF-39] P2-1
        """[V64.P3] 전술서 중복 감지"""

        candidate = self._normalize_tactical_text(candidate_text)
        if not candidate:
            return False
        recent_refs = reference_texts[-3:] if len(reference_texts) > 3 else reference_texts
        candidate_hash = hashlib.md5(candidate.encode("utf-8"), usedforsecurity=False).hexdigest()
        ref_hashes = set()
        for ref_text in recent_refs:
            ref = self._normalize_tactical_text(ref_text)
            if not ref:
                continue
            ref_hashes.add(hashlib.md5(ref.encode("utf-8"), usedforsecurity=False).hexdigest())
            if candidate == ref:
                return True
        if candidate_hash in ref_hashes:
            return True
        for ref_text in recent_refs:
            ref = self._normalize_tactical_text(ref_text)
            if not ref:
                continue
            if SequenceMatcher(None, candidate, ref).ratio() >= threshold:
                return True
        return False

    def _normalize_flow_text(self, text: str) -> str:
        """[V64.P3] Flow Guard용 텍스트 정규화"""
        if not isinstance(text, str):
            return ""
        normalized = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", text)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        return normalized

    def _stage2_flow_guard(self, refined_arc: dict) -> dict:
        """
        [V60.15] Stage2: 진짜 서사 구조 분석 기반 Flow Guard
        """
        from modules.validation.threshold_helper import _threshold

        _SUMMARY_MODEL = AIModels.SUMMARY_MODEL
        _min_beats_floor = int(_threshold("scope.min_beats_floor", 1))
        _min_avg_words = int(_threshold("scope.min_avg_words", 6))
        _min_word_per_beat = int(_threshold("scope.min_word_per_beat", 4))
        _min_diversity = float(_threshold("scope.min_diversity", 0.6))

        beats = refined_arc.get("beat_sequence", [])
        # [Sweep-Codex] ep_count가 문자열일 수 있음 (SelfReflector 경로)
        try:
            ep_count = int(refined_arc.get("ep_count", 0))
        except (ValueError, TypeError):
            ep_count = 0

        _min_beats = max(_min_beats_floor, ep_count)  # [TF-E-1] 단일 에피소드 아크 허용
        if not isinstance(beats, list) or len(beats) < _min_beats:
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 수가 화수보다 부족",
                "feedback": "각 화마다 고유 사건을 분리해 비트를 늘려라.",
                "diagnostics": {
                    "type": "beat_count",
                    "beat_count": len(beats) if isinstance(beats, list) else 0,
                    "min_beats": _min_beats,
                    "ep_count": ep_count,
                },
            }

        # dict 형태 비트도 처리 (LLM이 {"beat": "...", "ep": 1} 반환 시)
        def _extract_beat_text(b):
            if isinstance(b, str):
                return b
            if isinstance(b, dict):
                return b.get("beat") or b.get("description") or b.get("content") or ""
            return ""

        normalized = [
            nt for nt in (self._normalize_flow_text(t) for t in (_extract_beat_text(b) for b in beats) if t) if nt
        ]
        if len(normalized) < 2:
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 내용이 비어 있음",
                "feedback": "각 화의 비트를 구체적 사건/행동으로 작성하라.",
                "diagnostics": {
                    "type": "empty_beats",
                    "normalized_count": len(normalized),
                    "total_beats": len(beats) if isinstance(beats, list) else 0,
                },
            }

        # 1) 서사 폭주 감지 — "제N화" 접두사 제거 후 실제 서사 내용만 측정
        _ep_prefix = re.compile(r"^제\s*\d+화\s*")
        stripped = [_ep_prefix.sub("", t).strip() for t in normalized if t]
        word_counts = [len(t.split()) for t in stripped if t]
        avg_words = sum(word_counts) / max(1, len(word_counts))
        # 에피소드 제목만 있는 비트 감지
        title_only_count = sum(1 for t in stripped if len(t.split()) <= 2)
        is_title_only = title_only_count > len(stripped) // 2

        if avg_words < _min_avg_words or any(c < _min_word_per_beat for c in word_counts):
            failing_beats = []
            for i, (wc, text) in enumerate(zip(word_counts, stripped)):
                if wc < _min_word_per_beat:
                    failing_beats.append({"idx": i + 1, "words": wc, "text": text[:50]})
            reason = (
                "서사 폭주 위험: beat_sequence에 에피소드 제목만 기재됨"
                if is_title_only
                else "서사 폭주 위험: 비트가 과도하게 축약됨"
            )
            feedback = (
                "beat_sequence에 에피소드 제목이 아닌 구체적 서사 비트를 작성하라. "
                "각 비트는 '사건 → 행동 → 반응'을 포함해야 한다."
                if is_title_only
                else "각 화마다 사건/행동/반응을 최소 1개씩 명시하라."
            )
            return {
                "status": "REJECT",
                "reason": reason,
                "feedback": feedback,
                "diagnostics": {
                    "type": "beat_condensed",
                    "avg_words": round(avg_words, 1),
                    "min_avg_words": _min_avg_words,
                    "min_word_per_beat": _min_word_per_beat,
                    "total_beats": len(word_counts),
                    "failing_beats": failing_beats[:5],
                    "word_counts": word_counts,
                },
            }

        # 2) [V60.15] 진짜 서사 구조 분석
        try:
            from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer

            analyzer = NarrativeStructureAnalyzer(client=self.ctx.sys.api_client, model=_SUMMARY_MODEL)

            # [Sweep45] dict 혼합 beats 방지 — normalized (문자열만) 전달
            result = analyzer.analyze(normalized[:5])

            if result.get("status") == "STAGNATION":
                stagnation_type = result.get("stagnation_type", "unknown")
                pattern = result.get("pattern", "")
                recommendation = result.get("recommendation", "")

                logging.warning(f" [V60.15] 진짜 서사 정체 감지: {stagnation_type}")
                logging.info(f"패턴: {pattern}")

                return {
                    "status": "REJECT",
                    "reason": f"서사 정체 감지: {stagnation_type} 반복 ({pattern})",
                    "feedback": recommendation,
                }

            if result.get("status") == "WARNING":
                warning_type = result.get("warning_type", "")
                pattern = result.get("pattern", "")
                logging.warning(f" [V60.15] 서사 경고: {warning_type} - {pattern}")

            diversity = result.get("diversity_score", 1.0)
            if diversity < _min_diversity:
                logging.warning(f" [V60.15] 서사 다양성: {diversity:.0%} (개선 권장)")

            return {"status": "PASS", "diversity_score": diversity}

        except ImportError:
            logging.warning(" [V60.15] NarrativeStructureAnalyzer 로드 실패, 폴백")
            return self._stage2_flow_guard_legacy(normalized)
        except Exception as e:
            logging.warning(f" [V60.15] 서사 분석 오류 (비차단): {e}")
            return {"status": "PASS", "fallback": True}

    def _stage2_flow_guard_legacy(self, normalized: list) -> dict:
        """[V60.15] 레거시 Flow Guard (폴백용)"""
        from modules.validation.threshold_helper import _threshold

        _max_stagnation_hits = int(_threshold("scope.max_stagnation_hits", 3))

        # [S2-P2-1] str → list 타입 방어 (SelfReflector 경로 등)
        if isinstance(normalized, str):
            normalized = [normalized]
        if not isinstance(normalized, list):
            normalized = list(normalized) if normalized else []

        def jaccard(a, b) -> float:
            sa, sb = set(a.split()), set(b.split())
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        stagnation_hits = 0
        for i in range(1, len(normalized)):
            sim = jaccard(normalized[i - 1], normalized[i])
            if sim >= _JACCARD_SIMILARITY_THRESHOLD:  # [TF-S2-04] Jaccard 전용 상수
                stagnation_hits += 1

        if stagnation_hits >= _max_stagnation_hits:
            return {
                "status": "REJECT",
                "reason": "서사 정체 감지: 유사 비트가 연속 반복",
                "feedback": "연속 회차의 사건/공간/행동을 분리하여 변주하라.",
            }

        return {"status": "PASS"}
