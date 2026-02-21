"""[B-1-7] Stage2 finalizer extracted from Stage2Orchestrator."""

import json
import logging

from modules.core.metrics_collector import get_metrics_collector
from modules.models.arc import validate_arc


class Stage2Finalizer:
    """Director audit + PASS/REJECT post-processing for Stage 2."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

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
        from modules.core.constants import ContextLimits, RecoveryLimits

        # [V66] SemanticPlotGuard 중복 검사
        if self.ctx.semantic_plot_guard:
            try:
                tactical_text = refined_arc.get("tactical_doc", "")
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if spg_warnings:
                    spg_text = self.ctx.semantic_plot_guard.format_warnings(spg_warnings)
                    logging.warning(f"⚠️ [V66] {spg_text}")
                    # Director 피드백에 추가
                    if current_feedback:
                        current_feedback = f"{current_feedback}\n{spg_text}"
                    else:
                        current_feedback = spg_text
            except Exception as e:
                logging.warning(f"⚠️ [V64.P4-fix] 플롯 중복 감지 실패: {e}")

        # [V65] PerfTimer: Director 대면 측정
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_director")
        except Exception as e:
            logging.debug(f"[PerfTimer] start s2 director: {e}")

        # [V67] Director 컨텍스트 확장: 이전 30개 Arc tactical_doc 전문 전달
        _expanded_prev_context = last_refined_context
        if all_refined_arcs:
            _prev_arc_docs = []
            _prev_start = max(0, len(all_refined_arcs) - 30)
            for _pa_idx in range(_prev_start, len(all_refined_arcs)):
                _pa = all_refined_arcs[_pa_idx]
                _pa_no = _pa.get("arc_no", _pa_idx + 1)
                _pa_td = _pa.get("tactical_doc", "")
                if isinstance(_pa_td, dict):
                    _pa_td = json.dumps(_pa_td, ensure_ascii=False)
                if _pa_td:
                    _pa_ep_s = _pa.get("ep_start", "?")
                    _pa_ep_e = _pa.get("ep_end", "?")
                    _prev_arc_docs.append(f"━━━ Arc {_pa_no} (제{_pa_ep_s}화~제{_pa_ep_e}화) ━━━\n{_pa_td}")
            if _prev_arc_docs:
                _full_arc_history = "\n\n".join(_prev_arc_docs)
                # 200K자 상한 (Gemini 대용량 컨텍스트 윈도우 활용)
                if len(_full_arc_history) > ContextLimits.MAX_CONTEXT_CHARS:
                    _full_arc_history = _full_arc_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
                _expanded_prev_context = (
                    f"[V67] ═══ 이전 Arc 전술서 전문 ({len(_prev_arc_docs)}개) ═══\n"
                    f"{_full_arc_history}\n\n"
                    f"═══ 상태 요약 ═══\n{last_refined_context}"
                )
                logging.warning(
                    f"📚 [V67] Director 컨텍스트 확장: {len(_prev_arc_docs)}개 Arc ({len(_expanded_prev_context)}자)"
                )

        # [V67.1] story_context 조립
        _story_context = ""
        try:
            _prot_config = bible_root.get("protagonist_config", {})
            _sc_parts = [f"- 장르: {genre}"]
            if _prot_config:
                _sc_parts.append(f"- 주인공: {_prot_config.get('name', protagonist_name or '미상')}")
                _incarnation = _prot_config.get("incarnation_type", "미상")
                _sc_parts.append(f"- 환생 유형: {_incarnation}")
                if _incarnation == "회귀자":
                    _sc_parts.append("→ 회귀자: 미래를 알고 역사를 변경하려 함. 이것은 모순이 아님.")
                elif _incarnation == "빙의자":
                    _sc_parts.append("→ 빙의자: 원래 인물과 다른 인격.")
                elif _incarnation == "환생자":
                    _sc_parts.append("→ 환생자: 전생 기억 보유.")
            _story_context = "\n".join(_sc_parts)
        except Exception as e:
            logging.warning(f"[SilentPass:Stage2Finalizer] 스토리 컨텍스트 생성 실패: {e!s:.100}")
            _story_context = ""

        # [G7] Director 심사 호출 크래시 방어
        try:
            audit = self.ctx.agents["director"].audit_strategic_plan(
                refined_arc,
                _expanded_prev_context,
                curr_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry=entity_registry_for_director,
                story_context=_story_context,  # [V67.1]
            )
        except Exception as _dir_err:
            logging.warning(f"[G7] Director 심사 호출 실패: {_dir_err!s:.100}")
            audit = {
                "decision": "REJECT",
                "score": 50,
                "reason": "Director 호출 실패 — 폴백 REJECT",
                "self_consistency": {},
            }
        try:
            self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_director")
        except Exception as e:
            logging.debug(f"[PerfTimer] stop s2 director: {e}")

        # ═══════════════════════════════════════════════════════════════
        # [V60.43] API 할당량 오류 시 폴백 로직
        # ═══════════════════════════════════════════════════════════════
        if audit.get("decision") == "REJECT" and draft_validator_passed and consensus_passed:
            self_consistency = audit.get("self_consistency", {})
            scores = self_consistency.get("scores", [])
            all_default_50 = len(scores) >= 2 and all(s == 50 for s in scores)
            zero_count = sum(1 for s in scores if s == 0)
            many_zeros = len(scores) >= 2 and zero_count >= len(scores) // 2
            is_quota_failure = all_default_50 or many_zeros

            if is_quota_failure:
                self.ctx.ui.log(f"      ⚠️ [V60.43] API 할당량 오류 감지 (score=0이 {zero_count}/{len(scores)}개)")
                self.ctx.ui.log("      ✅ [V60.43] DraftValidator + Consensus 통과로 PASS 오버라이드")
                audit["decision"] = "PASS"
                audit["v60_43_override"] = True
                audit["original_decision"] = "REJECT"
                audit["override_reason"] = "api_quota_exhausted_fallback"
                self.ctx.audit_event(
                    "v60_43_quota_override",
                    "Arc accepted due to quota exhaustion",
                    {"arc_no": global_arc_no, "scores": scores, "zero_count": zero_count},
                )

        from modules.validation.threshold_helper import _threshold

        _quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        _score_raw = audit.get("score", 0)
        try:
            _score = int(_score_raw)
        except (ValueError, TypeError):
            _score = 0

        _td = refined_arc.get("tactical_doc", "")
        _td_len = len(str(_td)) if isinstance(_td, dict) else len(_td or "")
        if audit.get("decision") == "PASS":  # [TF-R4-S2-01] PASS/REJECT 분리 (short tactical_doc REJECT 방지)
            if _td_len >= 1500 and _score < _quality_gate_score:
                self.ctx.ui.log(
                    f"      ⚠️ [QualityGate] PASS 판정이나 score={_score} < {_quality_gate_score} → REJECT 전환"
                )
                audit["decision"] = "REJECT"
                audit["reason"] = (audit.get("reason") or "") + (
                    f"\n[Quality Gate] score {_score}점으로 {_quality_gate_score}점 미달."
                )
                audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "품질 개선 후 재제출"
                return {"action": "retry", "current_feedback": audit["reason"]}

            ### [0124 핵심 3] 욕망 데이터 및 HUD 그림자 물리적 박제
            refined_arc["arc_drive"] = arc_drive if arc_drive else {}
            refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
            refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

            critical_missing = []
            if not refined_arc.get("hybrid_composition"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] 패턴 구성(hybrid_composition) 누락 - 기본값 주입")
                self.ctx.audit_event("data_missing", "hybrid_composition missing", {"arc_no": global_arc_no})
                refined_arc["hybrid_composition"] = {
                    "primary": "standard_progression",
                    "secondary": [],
                    "mixing_logic": "기본 전개",
                }
                critical_missing.append("hybrid_composition")

            if not refined_arc.get("joint_docs"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] joint_docs 누락 - 기본값 주입")
                self.ctx.audit_event("data_missing", "joint_docs missing", {"arc_no": global_arc_no})
                refined_arc["joint_docs"] = {
                    "final_location": "위치 미정",
                    "physical_inventory": ["물품 미정"],
                    "world_joint": "변화 없음",
                }
                critical_missing.append("joint_docs")

            # [V49.6 NEW] physical_inventory 계승
            curr_joint = refined_arc.get("joint_docs", {})
            curr_inventory = curr_joint.get("physical_inventory", [])
            if not curr_inventory or curr_inventory == [] or curr_inventory == "[]":
                if all_refined_arcs:
                    prev_joint = all_refined_arcs[-1].get("joint_docs", {})
                    prev_inventory = prev_joint.get("physical_inventory", [])
                    # [TF-R3-S2-02] 문자열 직렬화된 인벤토리 → 리스트 변환
                    if isinstance(prev_inventory, str):
                        try:
                            import json as _json

                            prev_inventory = _json.loads(prev_inventory)
                        except (ValueError, TypeError):
                            prev_inventory = []
                    if prev_inventory and prev_inventory != [] and prev_inventory != "[]":
                        curr_status = refined_arc.get("status_shadow", {})
                        consumed_raw = curr_status.get("item_consumption", [])
                        if isinstance(consumed_raw, str):
                            consumed_names = [consumed_raw] if consumed_raw else []
                        elif isinstance(consumed_raw, list):
                            consumed_names = []
                            for consumed_item in consumed_raw:
                                if isinstance(consumed_item, str):
                                    consumed_names.append(consumed_item)
                                elif isinstance(consumed_item, dict):
                                    consumed_names.append(consumed_item.get("name", consumed_item.get("item", "")))
                        else:
                            consumed_names = []
                        state_constraints = refined_arc.get("state_constraints", {})
                        acquired = state_constraints.get("items_acquired", [])
                        if isinstance(acquired, str):
                            acquired = [acquired] if acquired else []
                        elif not isinstance(acquired, list):
                            # [TF-R3-S2-03] dict 등 비-리스트 타입 방어
                            acquired = [acquired] if acquired else []
                        if isinstance(prev_inventory, list):
                            # [Sweep45] dict 아이템도 consumed 비교 가능하도록 이름 추출
                            def _item_name(it):
                                if isinstance(it, dict):
                                    return it.get("name", it.get("item", ""))
                                return str(it)

                            inherited = [item for item in prev_inventory if _item_name(item) not in consumed_names]
                            inherited.extend(acquired)
                            refined_arc["joint_docs"]["physical_inventory"] = inherited
                            self.ctx.ui.log(
                                f"      🔄 [V49.6] physical_inventory 이전 Arc에서 계승: {inherited[:3]}{'...' if len(inherited) > 3 else ''}"
                            )

            if not refined_arc.get("status_shadow"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] status_shadow 누락 - 기본값 주입")
                self.ctx.audit_event("data_missing", "status_shadow missing", {"arc_no": global_arc_no})
                refined_arc["status_shadow"] = {
                    "internal_energy_loss": "0%",
                    "expected_injuries": "없음",
                    "item_consumption": [],
                }
                critical_missing.append("status_shadow")

            if len(critical_missing) >= RecoveryLimits.CRITICAL_MISSING_THRESHOLD:
                self.ctx.ui.log(f"🚨 [Arc {global_arc_no}] 핵심 데이터 과다 누락({len(critical_missing)}개)")
                current_feedback = f"필수 키 누락: {', '.join(critical_missing)}. 완전한 JSON 구조로 재설계하라."
                refined_arc = None
                return {"action": "retry", "current_feedback": current_feedback}

            if not self.ctx.validate_arc_integrity(refined_arc):
                current_feedback = "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
                refined_arc = None
                return {"action": "retry", "current_feedback": current_feedback}

            # [TF-S2-03] 중복 check_new_arc() 제거 — L58-74의 첫 번째 호출이 이미 처리

            # [V63] constraint_summary 저장
            if constraint_block:
                _constraint_lines = constraint_block.strip().split("\n")
                _must_not = [ln.strip() for ln in _constraint_lines if "금지" in ln or "MUST NOT" in ln or "절대" in ln]
                refined_arc["constraint_summary"] = "\n".join(_must_not[:10]) if _must_not else ""

            refined_arc = validate_arc(refined_arc)  # [Step2] Pydantic ingress+egress
            all_refined_arcs.append(refined_arc)

            ### [0124 핵심 4] DB 원자적 커밋
            try:
                self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
                # [Codex-fix] safe_commit_async는 실패 시 예외 대신 False 반환
                _commit_ok = await self.ctx.safe_commit_async()
                if not _commit_ok:
                    raise RuntimeError("safe_commit_async returned False")
            except Exception as commit_err:
                # [TF-C09] DB 트랜잭션 롤백 — 반쪽 커밋 방지
                try:
                    _conn = self.ctx.current_project.db.conn
                    if _conn.in_transaction:
                        _conn.rollback()
                        logging.warning("🔄 [TF-C09] DB rollback 완료 (Arc %d)", global_arc_no)
                except Exception as _rb:
                    logging.warning("⚠️ [TF-C09] DB rollback 실패: %s", _rb)
                self.ctx.ui.log(f"🚨 [DB] Arc {global_arc_no} 저장 실패: {commit_err}")
                self.ctx.audit_event(
                    "db_commit_error",
                    "arc save failed in async",
                    {"arc_no": global_arc_no, "error": str(commit_err)},
                )
                all_refined_arcs.pop()
                # [Sweep52] DB 실패 시 StateTracker 롤백 (st_snapshot 보존)
                if st_snapshot:
                    try:
                        _st = self.ctx.state_tracker
                        for _k, _v in st_snapshot.items():
                            setattr(_st, _k, _v)
                        logging.warning("🔄 [V70] DB 실패 StateTracker 롤백 완료")
                    except Exception as _rb_err:
                        logging.warning(f"⚠️ [V70] DB 실패 StateTracker 롤백 실패: {_rb_err}")
                return {"action": "retry", "current_feedback": current_feedback}

            st_snapshot = None  # [V70] DB 커밋 성공 후 스냅샷 해제
            self.ctx.cumulative_state_cache = None
            self.ctx.cumulative_state_cache_key = None  # [S-08] 센티넬 (0은 유효한 키일 수 있음)

            constraint_db.update_arc_state(refined_arc)
            self.ctx.ui.log(f"      🔒 [V49.4] ConstraintDB 업데이트 완료 (총 {len(constraint_db.arc_states)}개 Arc)")

            last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, global_arc_no + 1)
            current_ep_start = refined_arc["ep_end"] + 1
            passed = True

            # [4-R3-f] PASS 메트릭 기록
            self._record_s2_pass_metrics(
                global_arc_no=global_arc_no,
                attempt=attempt,
                generation_method=generation_method,
                audit=audit,
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
            )

            # [Phase 6] Arc 단위 비용 스냅샷 저장 (비차단)
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
            except Exception as cost_err:
                logging.warning("[Phase 6] Arc 비용 기록 실패 (비차단): %s", cost_err)

            # [V68] 계층적 요약 피라미드 — 볼륨 요약 (10 Arc마다)
            if global_arc_no > 0 and global_arc_no % 10 == 0:
                try:
                    _vol_no = global_arc_no // 10
                    _arc_summaries_for_vol = []
                    for _ai in range(global_arc_no - 9, global_arc_no + 1):
                        _as = self.ctx.current_project.load_v20_anchor(f"arc_summary_{_ai}")
                        if _as:
                            # arc_summary는 dict 또는 str일 수 있음
                            if isinstance(_as, dict):
                                _as_text = _as.get("summary", "") or _as.get("text", "")
                                if not _as_text:
                                    # [V70] arc_summary dict를 읽기 좋은 텍스트로 변환
                                    _parts = []
                                    if _as.get("npc_status") and isinstance(_as["npc_status"], dict):
                                        _parts.append(
                                            "NPC: "
                                            + ", ".join(
                                                f"{n}({v.get('status', '')})" for n, v in _as["npc_status"].items()
                                            )
                                        )
                                    if _as.get("world_changes"):
                                        _parts.append(
                                            "세계변화: " + "; ".join(str(w) for w in _as["world_changes"][:5])
                                        )
                                    if _as.get("resolved_plots"):
                                        _parts.append(
                                            "해결플롯: " + "; ".join(str(p) for p in _as["resolved_plots"][:5])
                                        )
                                    if _as.get("active_plots"):
                                        _parts.append("진행플롯: " + "; ".join(str(p) for p in _as["active_plots"][:5]))
                                    if _as.get("destroyed_entities"):
                                        _parts.append(
                                            "파괴: " + "; ".join(str(d) for d in _as["destroyed_entities"][:3])
                                        )
                                    _as_text = " | ".join(_parts) if _parts else str(_as)
                            else:
                                _as_text = str(_as)
                            if _as_text:
                                _arc_summaries_for_vol.append(f"Arc {_ai}: {_as_text}")

                    if _arc_summaries_for_vol:
                        _vol_prompt = (
                            "아래 10개 아크 요약을 하나의 볼륨 요약으로 합쳐주세요.\n"
                            "핵심 사건, 주요 인물 변화, 세계 상태 변화에 집중하세요.\n"
                            "1000자 이내로 작성하세요.\n\n"
                            + "\n".join(_arc_summaries_for_vol)
                            + f"\n\n볼륨 {_vol_no} 요약:"
                        )
                        _vol_result = self.ctx.agents["director"].ask(_vol_prompt, temperature=0.2)
                        if _vol_result and isinstance(_vol_result, str) and len(_vol_result) > 20:
                            self.ctx.current_project.save_v20_anchor(f"volume_summary_{_vol_no}", _vol_result)
                            logging.info(f"📖 [V68] 볼륨 {_vol_no} 요약 저장 완료 ({len(_vol_result)}자)")

                            # [V68] 시리즈 요약 갱신 — 기존 + 새 볼륨 통합
                            try:
                                _existing_series = self.ctx.current_project.load_v20_anchor("series_summary") or ""
                                if isinstance(_existing_series, dict):
                                    _existing_series = _existing_series.get("summary", "") or str(_existing_series)
                                _series_prompt = (
                                    "아래는 기존 시리즈 요약과 새 볼륨 요약입니다.\n"
                                    "이를 통합하여 전체 시리즈 요약을 1000자 이내로 갱신하세요.\n"
                                    "핵심 사건, 주요 인물 변화, 세계 상태 변화에 집중하세요.\n\n"
                                    f"기존 시리즈 요약:\n{_existing_series or '(아직 없음)'}\n\n"
                                    f"새 볼륨 {_vol_no} 요약:\n{_vol_result}\n\n"
                                    "갱신된 시리즈 요약:"
                                )
                                _series_result = self.ctx.agents["director"].ask(_series_prompt, temperature=0.2)
                                if _series_result and isinstance(_series_result, str) and len(_series_result) > 20:
                                    self.ctx.current_project.save_v20_anchor("series_summary", _series_result)
                                    logging.info(f"📚 [V68] 시리즈 요약 갱신 완료 ({len(_series_result)}자)")
                            except Exception as _se:
                                logging.warning(f"⚠️ [V68] 시리즈 요약 갱신 실패 (비차단): {_se}")
                        else:
                            logging.warning("⚠️ [V68] 볼륨 요약 LLM 응답 불충분 — 건너뜀")
                except Exception as _ve:
                    logging.warning(f"⚠️ [V68] 볼륨 요약 생성 실패 (비차단): {_ve}")

            return {
                "action": "break",
                "last_refined_context": last_refined_context,
                "current_ep_start": current_ep_start,
                "current_feedback": current_feedback,
                "director_feedback_for_fourphase": director_feedback_for_fourphase,
                "st_snapshot": st_snapshot,
            }
        else:
            # [V60.77] Director REJECT
            _rejected_arc = refined_arc  # [Patch Mode] REJECT된 Arc 보존 (패치 모드 판단용)
            base_feedback = audit.get("re_slice_instruction") or "밀도 보강 필요"
            reject_reason = audit.get("reason") or "사유 미상"
            _score_breakdown = {}
            _self_consistency = audit.get("self_consistency", {})
            if isinstance(_self_consistency, dict):
                for _k in ("votes", "pass_votes", "median_score"):
                    _v = _self_consistency.get(_k)
                    if isinstance(_v, int | float):
                        _score_breakdown[_k] = _v

            adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
            intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"

            self.ctx.ui.log(f"      🎬 [Director REJECT] {reject_reason[:100]}")
            self.ctx.ui.log(f"      📋 피드백: {base_feedback[:100]}")

            # [V70] StateTracker 롤백: FourPhase PASS → Director REJECT 시 팬텀 데이터 제거
            if st_snapshot and generation_method.startswith("four_phase"):  # [TF-R2-S2-11] ASP 포함
                try:
                    _st = self.ctx.state_tracker
                    for _k, _v in st_snapshot.items():
                        setattr(_st, _k, _v)
                    logging.warning("🔄 [V70] StateTracker 롤백 완료 (Director REJECT)")
                except Exception as _rb_err:
                    logging.warning(f"⚠️ [V70] StateTracker 롤백 실패 (비차단): {_rb_err}")
                st_snapshot = None

            director_feedback_for_fourphase = f"""[Director REJECT 사유]
{reject_reason}

[수정 지시]
{base_feedback}

[재시도 가이드]
{intensity_guide}
"""
            refined_arc = None
            self.ctx.ui.log(f"      🔄 [V60.77] Director 피드백 → FourPhase 대면 {min(attempt + 2, 5)}/5")

            # [4-R3-f] REJECT 메트릭 기록
            self._record_s2_reject_metrics(
                global_arc_no=global_arc_no,
                attempt=attempt,
                generation_method=generation_method,
                audit=audit,
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
            )

        return {
            "action": "next",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
            "score": audit.get("score", 0),  # [Patch Mode] Director 점수
            "rejected_arc": _rejected_arc,  # [Patch Mode] REJECT된 Arc (패치 입력용)
            "score_breakdown": _score_breakdown,
            "selection_reason": reject_reason,
            "validation_warnings": [reject_reason, base_feedback],
        }

    def _record_s2_pass_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        audit: dict,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> None:
        """[4-R3-f] Record Stage 2 PASS metrics (PassRateMonitor, Dashboard, Optimizer, PerfTimer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
            try:
                self.ctx.pass_rate_monitor.record_attempt(
                    stage=2,
                    episode=global_arc_no,
                    arc=global_arc_no,
                    attempt_num=attempt + 1,
                    success=True,
                    generation_method=generation_method,
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (success): {e}")

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

    def _record_s2_reject_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        audit: dict,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> None:
        """[4-R3-f] Record Stage 2 REJECT metrics (PassRateMonitor, Dashboard, History, Optimizer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

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
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (reject): {e}")

        try:
            _score = audit.get("score", 0)
            if not isinstance(_score, int):
                try:
                    _score = int(_score)
                except (ValueError, TypeError):
                    _score = 0
            self.ctx.current_project.db.save_cost_record(
                session_id=f"arc_{global_arc_no}",
                scope_type="arc",
                scope_id=int(global_arc_no),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage2_reject",
                    "score": _score,
                    "attempt": attempt + 1,
                    "generation_method": generation_method,
                    "is_patch": is_patch,
                    "patch_fallback": patch_fallback,
                },
            )
        except Exception as e:
            logging.warning(f"[SilentPass:Stage2RejectMetric] {e!s:.120}")

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
            except Exception as e:  # [V64.P4] OPTIONAL: dashboard metrics
                logging.debug(f"[SILENT] dashboard metrics (REJECT): {e}")

        if self.ctx.stage_rejection_history is not None:  # [Sweep4] None 가드
            self.ctx.stage_rejection_history.append(
                {
                    "stage": 2,
                    "arc_no": global_arc_no,
                    "reason": str(audit.get("reason", ""))[:200],
                    "attempt": attempt + 1,
                }
            )

        if self.ctx.stage2_optimizer:
            try:
                self.ctx.stage2_optimizer.failure_memory.record_failure(
                    arc_no=global_arc_no,
                    failure_type="director_reject",
                    details=str(audit.get("reason", ""))[:200],
                )
            except Exception as e:  # [V64.P4] OPTIONAL: optimizer failure recording
                logging.debug(f"[SILENT] optimizer failure recording: {e}")
