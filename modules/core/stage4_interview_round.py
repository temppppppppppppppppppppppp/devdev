"""
[B-1-3] Stage4 Interview Round — 단일 면담 라운드 실행.
"""

import logging


class Stage4InterviewRound:
    """[B-1-3] Stage4 단일 면담 라운드 실행 모듈."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.time_warnings = []

    def run(
        self,
        *,
        round_num: int,
        stage4_spinner,
        director_feedback: str,
        previous_attempt: dict,
        round_ctx,
    ):
        """[4-R1-e-1] Single interview round: generation, validation, judgment."""
        from modules.core.stage4_types import _PATCH_REWRITE_THRESHOLD, _InterviewRoundResult
        from modules.validation.threshold_helper import _threshold

        # [4-R2-b] Unpack round context
        chief_writer = round_ctx.chief_writer
        manuscript_validator = round_ctx.manuscript_validator
        consistency_validator = round_ctx.consistency_validator
        blocking_validator = round_ctx.blocking_validator
        continuity_validator = round_ctx.continuity_validator
        next_ep = round_ctx.next_ep
        blueprint = round_ctx.blueprint
        arc_data = round_ctx.arc_data
        arc_pos = round_ctx.arc_pos
        total_ep_in_arc = round_ctx.total_ep_in_arc
        arc_tactical = round_ctx.arc_tactical
        prev_text = round_ctx.prev_text
        prev_ending = round_ctx.prev_ending
        _prev_manuscripts_text = round_ctx.prev_manuscripts_text
        _episode_digest = round_ctx.episode_digest
        hud_report = round_ctx.hud_report
        current_inventory = round_ctx.current_inventory
        current_martial_arts = round_ctx.current_martial_arts
        dead_npcs = round_ctx.dead_npcs
        item_acquisition_timeline = round_ctx.item_acquisition_timeline
        _chain_link_section = round_ctx.chain_link_section
        _world_state_summary = round_ctx.world_state_summary
        purism_prompt = round_ctx.purism_prompt
        genre_name = round_ctx.genre_name
        npc_equipment_summary = round_ctx.npc_equipment_summary
        _effective_anti_trope = round_ctx.effective_anti_trope
        intro_dna = round_ctx.intro_dna
        _story_context = round_ctx.story_context
        style_guide = round_ctx.style_guide
        reference_anchor_prompt = round_ctx.reference_anchor_prompt
        mandatory_context = round_ctx.mandatory_context
        justification_prompt = round_ctx.justification_prompt
        reflexion_prompt = round_ctx.reflexion_prompt

        if type(director_feedback) is not str:
            director_feedback = str(director_feedback or "")
        if type(mandatory_context) is not str:
            mandatory_context = str(mandatory_context or "")

        # [TF-T4] 24개 공통 kwargs — 4개 호출부에서 재사용
        _common_writer_kwargs = {
            "ep_num": next_ep,
            "blueprint": blueprint,
            "prev_manuscript": prev_text,
            "hud_report": hud_report,
            "arc_doc": arc_tactical,
            "master_bible": self.ctx.current_project.master_bible,
            "style_guide": style_guide,
            "current_inventory": current_inventory,
            "current_martial_arts": current_martial_arts,
            "dead_npcs": dead_npcs,
            "item_acquisition_timeline": item_acquisition_timeline,
            "reference_anchor_prompt": reference_anchor_prompt,
            "mandatory_context": mandatory_context,
            "anti_trope_prompt": _effective_anti_trope,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
            "genre_name": genre_name,
            "npc_equipment_summary": npc_equipment_summary,
            "intro_dna": intro_dna,
            "purism_prompt": purism_prompt,
            "state_tracker": self.ctx.state_tracker,
            "prev_manuscripts_text": _prev_manuscripts_text,
            "world_state_summary": _world_state_summary,
            "chain_link_section": _chain_link_section,
        }

        stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · 앙상블 생성")
        self.ctx.ui.log(f"\n🎬 [{round_num + 1}차 면담] Chief Writer 앙상블 생성 중...")

        # Phase 2: Chief Writer 앙상블 생성
        # [V65] PerfTimer: 원고 생성 측정
        try:
            self.ctx.perf_timer.start(f"s4_ep{next_ep}_generate_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] start generate: {e}")
        _is_patch = False
        _is_patch_fallback = False
        _prev_score = 0
        _prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
        _tot_used = bool(previous_attempt.get("_tot_used", False)) if previous_attempt else False
        _mad_used = bool(previous_attempt.get("_mad_used", False)) if previous_attempt else False

        _weighted_injection = ""
        _pw = self.ctx.get_module("prompt_weighter")
        if _pw:
            try:
                _weighted_injection = _pw.get_weighted_prompt("writer", 4, top_n=3)
            except Exception as e:
                logging.warning(f"[SilentPass:PromptWeighter] {e!s:.100}")
        if _weighted_injection:
            director_feedback = (
                (_weighted_injection + "\n\n" + director_feedback) if director_feedback else _weighted_injection
            )

        if round_num == 0:
            candidates = chief_writer.generate_ensemble(**_common_writer_kwargs)
        else:
            # [Phase 3-5B] 점수 기반 분기: 패치 모드 vs 전면 재작성
            try:
                _prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0
            except (ValueError, TypeError):
                _prev_score = 0
            _patch_enabled = bool(_threshold("feature_flags.enable_patch_mode", 1))
            _use_patch = _patch_enabled and _prev_score >= _PATCH_REWRITE_THRESHOLD and _prev_manuscript
            _is_patch = bool(_use_patch)

            if _use_patch:
                logging.info(f"[Phase 3-5B] 패치 모드 진입 (score={_prev_score}, round={round_num})")
                self.ctx.ui.log(f"   🔧 [Phase 3-5B] 패치 모드: score={_prev_score}, 원본 보존 수정")
                candidates = chief_writer.patch_with_feedback(
                    **_common_writer_kwargs,
                    original_manuscript=_prev_manuscript,
                    director_feedback=director_feedback,
                    previous_attempt=previous_attempt,
                    attempt_number=round_num + 1,
                )
                if not candidates:
                    _is_patch_fallback = True
                    # [Phase 3-5B] 패치 실패 → full rewrite 폴백
                    logging.warning("[Phase 3-5B] 패치 실패, full rewrite 폴백")
                    self.ctx.ui.log("   ⚠️ [Phase 3-5B] 패치 실패 → 전면 재작성 폴백")
                    candidates = chief_writer.regenerate_with_feedback(
                        **_common_writer_kwargs,
                        director_feedback=director_feedback,
                        previous_attempt=previous_attempt,
                        attempt_number=round_num + 1,
                    )
            else:
                candidates = chief_writer.regenerate_with_feedback(
                    **_common_writer_kwargs,
                    director_feedback=director_feedback,
                    previous_attempt=previous_attempt,
                    attempt_number=round_num + 1,
                )

        _asp_manuscript = None
        _asp = self.ctx.get_module("adversarial_self_play")
        if round_num >= 2 and _asp and previous_attempt:
            try:
                if _prev_manuscript:
                    self.ctx.ui.log(f"   🔥 [ASP] 레드팀 교정 발동 (재시도 {round_num + 1}회차)")
                    _asp_ctx = {}
                    if blueprint:
                        _asp_ctx["blueprint"] = blueprint
                    if director_feedback:
                        _asp_ctx["director_feedback"] = director_feedback
                    _asp_result = _asp.generate_with_adversary(
                        initial_content=_prev_manuscript,
                        content_type="manuscript",
                        context=_asp_ctx,
                    )
                    if _asp_result and hasattr(_asp_result, "final_output") and _asp_result.final_output:
                        _asp_manuscript = _asp_result.final_output
                        self.ctx.ui.log(
                            f"   ✅ [ASP] 교정 완료 (delta: +{getattr(_asp_result, 'improvement_delta', '?')})"
                        )
            except Exception as e:
                logging.warning(f"[SilentPass:ASP] {e!s:.200}")
        if _asp_manuscript:
            candidates.append({"manuscript": _asp_manuscript, "strategy": "asp_correction"})

        # [V65] PerfTimer: 원고 생성 종료
        try:
            self.ctx.perf_timer.stop(f"s4_ep{next_ep}_generate_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] stop generate: {e}")

        # [TF-R2-S4-I01] 빈 원고 후보 필터링
        candidates = [c for c in candidates if c.get("manuscript", "").strip()]

        # [V66.3] C-3: 빈 candidates 방어 — 모든 후보 생성 실패 시 다음 면담으로 스킵
        if not candidates:
            logging.error(f"[Stage4] 제{next_ep}화 {round_num + 1}차 면담: candidates 빈 배열 — 모든 후보 생성 실패")
            self.ctx.ui.log(
                f"   🚨 [V66.3] 모든 후보 생성 실패 — {'최종 실패 처리' if round_num >= 4 else '다음 면담으로 진행'}"
            )
            director_feedback += "\n[시스템] 모든 후보 생성 실패. 재시도 필요."
            previous_attempt = {
                "strategy": "none",
                "rejection_reason": "모든 후보 생성 실패",
                "action_items": [],
                "score": 0,
                "_tot_used": _tot_used,
                "_mad_used": _mad_used,
            }
            self._record_s4_attempt(
                episode=next_ep,
                round_num=round_num,
                success=False,
                score=0,
                is_patch=_is_patch,
                prev_score=_prev_score,
                patch_fallback=_is_patch_fallback,
                arc=round_ctx.arc_data.get("arc_no", 0),
            )
            return _InterviewRoundResult(
                verdict="EMPTY",
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
            )

        # Phase 3: Python 사전 검증
        stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · Python 검증")
        self.ctx.ui.log("   🔍 Python 사전 검증 중...")
        _recent_ms = []
        try:
            _recent_ms = self.ctx.current_project.db.get_recent_manuscripts(before_ep=next_ep, limit=5)
        except (
            AttributeError,
            Exception,
        ) as e:  # [V64.P4] IMPORTANT: recent manuscripts for cross-ep validation
            self.ctx.ui.log(f"   ⚠️ [V64.P4] 최근 원고 로드 실패 (교차검증 약화): {str(e)[:60]}")
        validation_results = manuscript_validator.validate_all_candidates(
            candidates=candidates,
            blueprint=blueprint,
            prev_manuscript=prev_text,
            hud_report=hud_report,
            recent_manuscripts=_recent_ms,
        )

        for i, vr in enumerate(validation_results):
            strategy = candidates[i].get("strategy_name", f"후보{i + 1}") if i < len(candidates) else f"후보{i + 1}"
            self.ctx.ui.log(
                f"      • {strategy}: 경고 {vr.get('warning_count', 0)}개, 분량 {vr.get('metrics', {}).get('length', 0)}자"
            )

        # [V63.2] ConsistencyValidator
        try:
            _cv_context = {
                "mode": "MANUSCRIPT",
                "martial_hud": {},
                "karma_matrix": {},
                "asset_library": {},
                "npc_profiles": {},
                "prev_episode_events": [],
                "ep_num": next_ep,
            }
            # [V67.1] incarnation_type 주입 — Validator 오탐 방지
            _incarnation_type = ""
            try:
                _bible_root = self.ctx.current_project.master_bible.get(
                    "MasterBible", self.ctx.current_project.master_bible
                )
                _incarnation_type = _bible_root.get("protagonist_config", {}).get("incarnation_type", "")
            except Exception as e:
                logging.warning(f"[SilentPass:InterviewRound] incarnation_type 로드 실패: {e!s:.100}")
            _cv_context["incarnation_type"] = _incarnation_type
            # [V66.2] C-1: BlockingValidator dead NPC 감지 활성화
            _encyclopedia_npcs = []
            if self.ctx.state_tracker:
                for _npc_name, _npc_info in getattr(self.ctx.state_tracker, "npc_registry", {}).items():
                    _encyclopedia_npcs.append(
                        {
                            "name": _npc_name,
                            "status": _npc_info.get("status", "alive"),
                            "death_arc": _npc_info.get("death_arc"),
                            "aliases": _npc_info.get("aliases", []),
                        }
                    )
            _cv_context["encyclopedia"] = {"npcs": _encyclopedia_npcs}
            # [V66.1] 시간선 경고를 검증 컨텍스트에 주입
            _cv_context["time_warnings"] = self.time_warnings
            # [V66.1] BlockingValidator/ContinuityValidator에 추적 데이터 전달
            if self.ctx.state_tracker:
                _cv_context["item_states"] = (
                    {
                        name: info.get("condition", "정상")
                        for name, info in self.ctx.state_tracker.item_state_registry.items()
                    }
                    if hasattr(self.ctx.state_tracker, "item_state_registry")
                    else {}
                )
                _cv_context["npc_personalities"] = (
                    {
                        name: {
                            "traits": info.get("personality_traits", ""),
                            "motivation": info.get("primary_motivation", ""),
                        }
                        for name, info in self.ctx.state_tracker.npc_registry.items()
                        if info.get("personality_traits")
                    }
                    if hasattr(self.ctx.state_tracker, "npc_registry")
                    else {}
                )
                # [Phase 3-5A-2] NPC 이력 데이터 검증 컨텍스트 주입
                if hasattr(self.ctx.state_tracker, "get_npc_change_history") and self.ctx.state_tracker.npc_registry:
                    _npc_history = {}
                    for _hn in self.ctx.state_tracker.npc_registry:
                        _hh = self.ctx.state_tracker.get_npc_change_history(_hn, limit=10)
                        if _hh:
                            _npc_history[_hn] = _hh
                    if _npc_history:
                        _cv_context["npc_history"] = _npc_history
            for ci, cand in enumerate(candidates):
                _cv_ms = cand.get("manuscript", "")
                if _cv_ms and ci < len(validation_results):
                    cv_result = consistency_validator.validate(_cv_ms, _cv_context)
                    cv_violations = cv_result.get("violations", [])
                    cv_penalty = cv_result.get("score_penalty", 0)
                    if cv_violations:
                        if "structured_violations" not in validation_results[ci]:
                            validation_results[ci]["structured_violations"] = []
                        for v in cv_violations:
                            reason = v.get("reason", str(v))
                            severity = v.get("severity", "")
                            tagged = f"[{severity}] {reason}" if severity else reason
                            validation_results[ci]["warnings"].append(f"[V63.2] 일관성: {tagged}")
                            validation_results[ci]["structured_violations"].append(v)
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        validation_results[ci]["focus_points"].append(
                            f"일관성 위반 {len(cv_violations)}건 (감점 {cv_penalty})"
                        )
                        self.ctx.ui.log(f"      ⚠️ 후보{ci + 1} 일관성 위반 {len(cv_violations)}건")
        except Exception as _cv_err:
            self.ctx.ui.log(f"      ⚠️ [V63.2] ConsistencyValidator 실행 실패: {str(_cv_err)[:60]}")

        # [V66.1] BlockingValidator — item_states 기반 파손 아이템 사용 체크
        try:
            for ci, cand in enumerate(candidates):
                _bv_ms = cand.get("manuscript", "")
                if _bv_ms and ci < len(validation_results):
                    bv_result = blocking_validator.validate(_bv_ms, _cv_context)
                    bv_failures = bv_result.get("failures", [])
                    if bv_failures:
                        for f in bv_failures:
                            reason = f.get("reason", str(f))
                            validation_results[ci]["warnings"].append(f"[V66.1] BLOCKING: {reason}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        validation_results[ci]["focus_points"].append(f"BLOCKING 위반 {len(bv_failures)}건")
                        self.ctx.ui.log(f"      ⚠️ 후보{ci + 1} BLOCKING 위반 {len(bv_failures)}건")
        except Exception as _bv_err:
            self.ctx.ui.log(f"      ⚠️ [V66.1] BlockingValidator 실행 실패: {str(_bv_err)[:60]}")

        # [V66.1] ContinuityValidator — npc_personalities, time_warnings 라우팅
        try:
            for ci, cand in enumerate(candidates):
                _ct_ms = cand.get("manuscript", "")
                if _ct_ms and ci < len(validation_results):
                    ct_result = continuity_validator.validate(next_ep, _ct_ms, _cv_context)
                    ct_violations = ct_result.get("violations", [])
                    ct_warnings = ct_result.get("warnings", [])
                    if ct_violations:
                        for v in ct_violations:
                            reason = v.get("reason", str(v))
                            validation_results[ci]["warnings"].append(f"[V66.1] 연속성: {reason}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        validation_results[ci]["focus_points"].append(f"연속성 위반 {len(ct_violations)}건")
                        self.ctx.ui.log(f"      ⚠️ 후보{ci + 1} 연속성 위반 {len(ct_violations)}건")
                    if ct_warnings:
                        for w in ct_warnings:
                            w_msg = w.get("reason", str(w)) if isinstance(w, dict) else str(w)
                            validation_results[ci]["warnings"].append(f"[V66.1] 연속성 경고: {w_msg}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
        except Exception as _ct_err:
            self.ctx.ui.log(f"      ⚠️ [V66.1] ContinuityValidator 실행 실패: {str(_ct_err)[:60]}")

        # [D Step 4] 좌절-보상 타이머 — Director에 advisory 전달
        try:
            _frust_warnings = continuity_validator.check_frustration_streak(next_ep)
            if _frust_warnings:
                for ci in range(len(validation_results)):
                    for _fw in _frust_warnings:
                        validation_results[ci]["warnings"].append(f"[D Step 4] {_fw}")
                    validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                for _fw in _frust_warnings:
                    self.ctx.ui.log(f"      ⚠️ {_fw}")
        except Exception as _frust_err:
            logging.warning("[D Step 4] 좌절-보상 타이머 실패 (비차단): %s", _frust_err)

        # [V66.2] C-4: 파괴 엔티티 감지 → Director에 경고 전달
        try:
            if self.ctx.state_tracker:
                for ci, cand in enumerate(candidates):
                    _de_ms = cand.get("manuscript", "")
                    if _de_ms and ci < len(validation_results):
                        _de_warnings = self.ctx.state_tracker.check_destroyed_entity_in_manuscript(_de_ms)
                        if _de_warnings:
                            for _dw in _de_warnings:
                                _dw_msg = _dw.get("message", str(_dw)) if isinstance(_dw, dict) else str(_dw)
                                validation_results[ci]["warnings"].append(f"[V66.2] 파괴된 엔티티 등장: {_dw_msg}")
                            validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
        except (KeyError, ValueError, TypeError) as _de_err:
            logging.warning(f"⚠️ [V66.2] 파괴 엔티티 검사 오류: {_de_err}")

        # [V61.5] 캐시 기반 연속성 검사
        if round_num == 0 and next_ep > 1 and candidates:
            stage4_spinner.update_detail(f"제{next_ep}화 · 연속성 검사")
            _continuity_conflicts = []
            for ci, cand in enumerate(candidates):
                _ms = cand.get("manuscript", "")
                if not _ms:
                    continue

                continuity_check = self.ctx.agents["director"].check_manuscript_continuity_with_cache(
                    new_manuscript=_ms,
                    ep_num=next_ep,
                    db=self.ctx.current_project.db,
                    limit=10,
                    story_context=_story_context,
                )
                if continuity_check.get("decision") == "CONFLICT":
                    conflict_summary = continuity_check.get("summary", "연속성 충돌 감지")
                    self.ctx.ui.log(f"   ⚠️ [V61.5] 후보{ci + 1} 연속성: {conflict_summary[:50]}...")
                    if ci < len(validation_results):
                        validation_results[ci]["warnings"].append(f"[연속성 충돌] {conflict_summary}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                    _continuity_conflicts.append(f"후보{ci + 1}: {conflict_summary[:80]}")

            if _continuity_conflicts:
                director_feedback += "\n[연속성 충돌]\n" + "\n".join(_continuity_conflicts)

        # [V67] 명시적 모순 검사 — 이전 원고와 비교
        if _prev_manuscripts_text and hasattr(
            self.ctx.agents.get("director", None), "check_manuscript_history_conflicts"
        ):
            _ms_history_for_check = []
            for _prev_ep in range(max(1, next_ep - 30), next_ep):
                try:
                    _prev_ms_data = self.ctx.current_project.db.get_manuscript(_prev_ep)
                    if _prev_ms_data:
                        _content = (
                            _prev_ms_data.get("content", "") if isinstance(_prev_ms_data, dict) else str(_prev_ms_data)
                        )
                        _ms_history_for_check.append({"ep_num": _prev_ep, "text": _content})
                except Exception as e:
                    logging.warning(f"[SilentPass:InterviewRound] 제{_prev_ep}화 원고 이력 로드 실패: {e!s:.100}")

            # [V67.1] story_context 포함하여 모순 검사 호출
            if _ms_history_for_check and candidates:
                _history_conflicts = []
                for ci, cand in enumerate(candidates):
                    _cand_ms = cand.get("manuscript", "")
                    if not _cand_ms:
                        continue
                    try:
                        _conflict_result = self.ctx.agents["director"].check_manuscript_history_conflicts(
                            ep_num=next_ep,
                            current_manuscript=_cand_ms,
                            manuscript_history=_ms_history_for_check,
                            use_summary=False,
                            story_context=_story_context,
                        )
                        if _conflict_result.get("decision") == "CONFLICT":
                            _conflict_summary = _conflict_result.get("summary", "모순 감지")
                            self.ctx.ui.log(f"   ⚠️ [V67] 후보{ci + 1} 역사 충돌: {_conflict_summary[:80]}")
                            if ci < len(validation_results):
                                validation_results[ci]["warnings"].append(f"[V67 역사 충돌] {_conflict_summary}")
                                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                            _history_conflicts.append(f"후보{ci + 1}: {_conflict_summary[:80]}")
                    except Exception as _hc_err:
                        logging.warning(f"⚠️ [V67] 후보{ci + 1} 역사 충돌 검사 실패: {_hc_err}")

                if _history_conflicts:
                    director_feedback += "\n[V67 원고 역사 충돌]\n" + "\n".join(_history_conflicts)

        _pdcl = self.ctx.get_module("pre_director_checklist")
        if _pdcl:
            try:
                _checklist_ctx = {}
                if blueprint:
                    _checklist_ctx["blueprint"] = blueprint
                if _prev_manuscript:
                    _checklist_ctx["prev_manuscript"] = _prev_manuscript
                for ci, cand in enumerate(candidates):
                    _ms = cand.get("manuscript", "")
                    if not _ms or ci >= len(validation_results):
                        continue
                    _cl_result = _pdcl.check(_ms, "manuscript", context=_checklist_ctx)
                    if not _cl_result.passed:
                        for _br in _cl_result.blocking_reasons:
                            validation_results[ci]["warnings"].append(f"[PreCheck] {_br}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        self.ctx.ui.log(f"   ⚠️ [PreCheck] 후보{ci + 1}: {_cl_result.summary[:60]}...")
            except Exception as e:
                logging.warning(f"[SilentPass:PreDirectorChecklist] {e!s:.100}")

        _cc = self.ctx.get_module("confidence_calibrator")
        if _cc:
            try:
                for ci, cand in enumerate(candidates):
                    _ms = cand.get("manuscript", "")
                    if not _ms or ci >= len(validation_results):
                        continue
                    _conf = _cc.assess(
                        _ms, "manuscript", context={"blueprint": blueprint, "prev_manuscript": _prev_manuscript}
                    )
                    if _conf.concerns:
                        for _c in _conf.concerns[:3]:
                            validation_results[ci]["warnings"].append(f"[Confidence:{_conf.level.value}] {_c}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
            except Exception as e:
                logging.warning(f"[SilentPass:ConfidenceCalibrator] {e!s:.100}")

        _cv = self.ctx.get_module("cross_verifier")
        if _cv and blueprint:
            try:
                from modules.core.cross_agent_verifier import ComplianceLevel

                for ci, cand in enumerate(candidates):
                    _ms = cand.get("manuscript", "")
                    if not _ms or ci >= len(validation_results):
                        continue
                    _compliance = _cv.verify_writer_compliance(manuscript=_ms, blueprint=blueprint, use_llm=False)
                    if _compliance.level == ComplianceLevel.VIOLATION:
                        for _v in _compliance.violations[:5]:
                            _v_msg = _v.get("reason", str(_v)) if isinstance(_v, dict) else str(_v)
                            validation_results[ci]["warnings"].append(f"[CrossVerify:VIOLATION] {_v_msg}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                    elif _compliance.warnings:
                        for _w in _compliance.warnings[:3]:
                            _w_msg = _w.get("reason", str(_w)) if isinstance(_w, dict) else str(_w)
                            validation_results[ci]["warnings"].append(f"[CrossVerify:WARNING] {_w_msg}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
            except Exception as e:
                logging.warning(f"[SilentPass:CrossAgentVerifier] {e!s:.100}")

        # Phase 4: Director 면담
        stage4_spinner.update_detail(f"제{next_ep}화 · {round_num + 1}차 면담 · Director 심사")
        self.ctx.ui.log("   🎬 Director 면담 중...")
        # [V65] PerfTimer: Director 대면 측정
        try:
            self.ctx.perf_timer.start(f"s4_ep{next_ep}_director_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] start director: {e}")
        # [V66.3] C-1: mandatory_context + Python 검증 경고를 Director에 전달
        # validation_results에서 경고를 추출하여 mandatory_context에 병합
        _mandatory_text = mandatory_context if isinstance(mandatory_context, str) else str(mandatory_context or "")
        _director_mc_parts = [_mandatory_text] if _mandatory_text else []
        _vr_warnings_for_director = []
        for _vr_idx, _vr in enumerate(validation_results):
            _vr_warns = _vr.get("warnings", [])
            if _vr_warns:
                _label = ["A", "B", "C"][_vr_idx] if _vr_idx < 3 else f"{_vr_idx + 1}"
                _vr_warnings_for_director.append(f"[후보 {_label} Python 감지 경고]\n" + "\n".join(_vr_warns[:30]))
        if _vr_warnings_for_director:
            _director_mc_parts.append(
                "[V66.3] Python 사전 검증 결과 (Director 참고용)\n" + "\n\n".join(_vr_warnings_for_director)
            )
        # [V69.1] V67 원고 역사 충돌 + 연속성 충돌 경고를 Director에 전달
        if director_feedback and director_feedback.strip():
            _director_mc_parts.append(
                "🚨 [V69.1] Python 감지된 원고 충돌 경고 (반드시 반영하세요)\n" + director_feedback.strip()
            )
        _director_mandatory_context = "\n\n".join(str(x) for x in _director_mc_parts if x is not None)

        director_result = self.ctx.agents["director"].select_and_judge_ensemble(
            ep_num=next_ep,
            candidates=candidates,
            validation_results=validation_results,
            blueprint=blueprint,
            previous_ending=prev_ending,
            arc_pos=arc_pos,
            total_eps=total_ep_in_arc,
            retry_count=round_num,
            episode_digest=_episode_digest,
            mandatory_context=_director_mandatory_context,
            prev_manuscripts_text=_prev_manuscripts_text,  # [V67]
            story_context=_story_context,  # [V67.1]
        )
        try:
            self.ctx.perf_timer.stop(f"s4_ep{next_ep}_director_r{round_num}")
        except Exception as e:
            logging.debug(f"[PerfTimer] stop director: {e}")

        selected = director_result.get("selected", "A")
        verdict = director_result.get("verdict", "REJECT")
        score = director_result.get("score", 0)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
        reason = director_result.get("selection_reason") or ""

        self.ctx.ui.log(f"   📊 Director 판정: {verdict} (점수: {score}, 선택: 후보 {selected})")
        self.ctx.ui.log(f"      └─ 사유: {reason[:80]}...")

        # [D-4] Director 선택 기록 (비차단)
        try:
            _selection_reason = reason
            if _is_patch:
                _tag = "patch-fallback" if _is_patch_fallback else "patch"
                _selection_reason = (
                    f"[{_tag}|score={_prev_score}] {reason}" if reason else f"[{_tag}|score={_prev_score}]"
                )
            _sel_candidate = director_result.get("selected_candidate", {})
            if not isinstance(_sel_candidate, dict):
                _sel_candidate = {}
            _sel_strategy = _sel_candidate.get("strategy_name", "") or _sel_candidate.get("strategy", "")
            self.ctx.current_project.db.save_director_selection(
                ep_num=next_ep,
                round_num=round_num,
                selected_label=selected,
                selected_strategy=_sel_strategy,
                verdict=verdict,
                score=score,
                selection_reason=_selection_reason,
                candidate_count=len(candidates) if candidates else 0,
            )
        except Exception as e:
            logging.warning(f"[D-4] Director 선택 기록 실패 (비차단): {e!s:.100}")

        _quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        if verdict == "PASS" and score < _quality_gate_score:
            self.ctx.ui.log(f"   ⚠️ [QualityGate] PASS 판정이나 score={score} < {_quality_gate_score} → 패치 모드")
            verdict = "REJECT"
            director_feedback += (
                f"\n[Quality Gate] Director PASS 판정이나 점수 {score}점으로 {_quality_gate_score}점 미달. "
                "품질 개선 후 재제출."
            )

        if verdict == "PASS":
            selected_candidate = director_result.get("selected_candidate") or {}
            final_manuscript = selected_candidate.get("manuscript", "")
            final_title = selected_candidate.get("title", f"제{next_ep}화")
            final_state_updates = director_result.get("state_updates", {})

            # [V66.1] F-1: 시간선 일관성 체크 → 검증 파이프라인에 경고 전달
            if self.ctx.state_tracker:
                try:
                    _time_warnings = self.ctx.state_tracker.check_time_consistency(
                        final_manuscript, self.ctx.state_tracker.in_world_timeline
                    )
                    if _time_warnings:
                        for tw in _time_warnings:
                            self.ctx.ui.log(f"   ⏰ [V66.1] 시간선 경고: {tw}")
                        # [V66.1] 검증 파이프라인용 경고 저장
                        self.time_warnings.extend(_time_warnings)
                except (KeyError, ValueError, TypeError) as _tc_err:
                    logging.warning(f"⚠️ [V66.1] 시간선 검사 오류: {_tc_err}")

            self.ctx.ui.log(f"   ✅ {round_num + 1}차 면담 PASS!")
            self._record_s4_attempt(
                episode=next_ep,
                round_num=round_num,
                success=True,
                score=score,
                is_patch=_is_patch,
                prev_score=_prev_score,
                patch_fallback=_is_patch_fallback,
                arc=round_ctx.arc_data.get("arc_no", 0),
            )
            return _InterviewRoundResult(
                verdict="PASS",
                director_feedback=director_feedback,
                previous_attempt=previous_attempt,
                final_manuscript=final_manuscript,
                final_title=final_title,
                final_state_updates=final_state_updates,
            )
        else:
            # [TF-R2-S4-03] 시스템 감지 라인 보존 (REJECT 시 덮어쓰기 전 추출)
            _system_prefixes = ("[연속성 충돌]", "[V67]", "[CoVe]", "[ToT", "[MAD")
            _prev_system_lines = (
                [
                    line
                    for line in director_feedback.split("\n")
                    if any(line.strip().startswith(p) for p in _system_prefixes)
                ]
                if director_feedback
                else []
            )

            feedback = director_result.get("feedback") or {}
            action_items = director_result.get("action_items") or []
            # [Sweep52] str([]) → "[]" 방지 — issues를 개별 join
            _issues = feedback.get("issues", []) if isinstance(feedback, dict) else []
            director_feedback = (
                "\n".join(action_items) if action_items else ("\n".join(str(i) for i in _issues) if _issues else "")
            )
            if _prev_system_lines:  # [TF-R2-S4-03] 시스템 감지 라인 복원
                director_feedback = "\n".join(_prev_system_lines) + "\n" + director_feedback
            _reject_text = f"{director_feedback}\n" + "\n".join(str(a) for a in action_items)
            _reject_lower = _reject_text.lower()
            _reject_bucket = "quality_issue"
            if any(k in _reject_lower for k in ("constraint", "제약", "충돌", "금지", "모순", "consistency", "검증")):
                _reject_bucket = "constraint_violation"
            elif any(k in _reject_lower for k in ("구조", "structure", "흐름", "flow", "씬", "전개", "페이싱")):
                _reject_bucket = "structure_error"

            _seed_manuscript = (director_result.get("selected_candidate") or {}).get(
                "manuscript", ""
            ) or _prev_manuscript
            _tot = self.ctx.get_module("tree_of_thoughts")
            if _reject_bucket == "structure_error" and _tot and not _tot_used and _seed_manuscript:
                try:
                    _tot_result = _tot.explore(
                        task=f"원고 구조 개선: {director_feedback}",
                        context={"manuscript": _seed_manuscript[:3000], "blueprint": blueprint},
                    )
                    _best_path = getattr(_tot_result, "best_path", None)
                    _tot_output = getattr(_best_path, "output", "") if _best_path else ""
                    if _tot_output:
                        director_feedback += f"\n[ToT 구조 개선 지침]\n{_tot_output[:1000]}"
                        _tot_used = True
                except Exception as e:
                    logging.warning(f"[SilentPass:ToT] {e!s:.120}")
            _mad = self.ctx.get_module("multi_agent_deliberation")
            if _reject_bucket == "constraint_violation" and _mad and not _mad_used and _seed_manuscript:
                try:
                    _mad_result = _mad.deliberate(
                        content=_seed_manuscript,
                        content_type="manuscript",
                        context={"blueprint": blueprint, "director_feedback": director_feedback},
                    )
                    _mad_output = getattr(_mad_result, "consensus_output", "") if _mad_result else ""
                    if _mad_output:
                        director_feedback += f"\n[MAD 제약/합의 개선 지침]\n{_mad_output[:1000]}"
                        _mad_used = True
                except Exception as e:
                    logging.warning(f"[SilentPass:MAD] {e!s:.120}")

            _sel_candidate = director_result.get("selected_candidate", {})
            if not isinstance(_sel_candidate, dict):
                _sel_candidate = {}
            _sel_strategy_key = _sel_candidate.get("strategy", "") or _sel_candidate.get("strategy_name", "")
            previous_attempt = {
                "strategy": selected,
                "selected_strategy_key": _sel_strategy_key,
                "rejection_reason": director_feedback,
                "action_items": action_items,
                "score": score,
                # [Phase 3-5B] 패치 모드용 원본 원고 보존
                "best_manuscript": (director_result.get("selected_candidate") or {}).get("manuscript", ""),
                "score_breakdown": director_result.get("score_breakdown", {}),
                "selection_reason": director_result.get("selection_reason", ""),
                "validation_warnings": [w for vr in validation_results for w in vr.get("warnings", [])][:20],
                "reject_bucket": _reject_bucket,
                "_tot_used": _tot_used,
                "_mad_used": _mad_used,
            }
            try:
                self.ctx.current_project.db.save_cost_record(
                    session_id=f"ep_{next_ep}",
                    scope_type="episode",
                    scope_id=int(next_ep),
                    total_calls=0,
                    total_tokens=0,
                    total_cost_usd=0.0,
                    model_breakdown={
                        "event": "stage4_reject",
                        "bucket": _reject_bucket,
                        "score": score,
                        "round": round_num,
                        "strategy": selected,
                        "intelligence_used": {
                            "asp": bool(_asp_manuscript),
                            "tot": _tot_used,
                            "mad": _mad_used,
                        },
                    },
                )
            except Exception as e:
                logging.warning(f"[SilentPass:Stage4RejectMetric] {e!s:.120}")
            self.ctx.ui.log(f"   ❌ {round_num + 1}차 면담 REJECT. 피드백: {director_feedback[:100]}...")
        self._record_s4_attempt(
            episode=next_ep,
            round_num=round_num,
            success=False,
            score=score,
            is_patch=_is_patch,
            prev_score=_prev_score,
            patch_fallback=_is_patch_fallback,
            arc=round_ctx.arc_data.get("arc_no", 0),
        )
        return _InterviewRoundResult(
            verdict="REJECT",
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
        )

    # ── Stage 4 PassRateMonitor 기록 ──────────────────────────────

    def _record_s4_attempt(
        self,
        *,
        episode: int,
        round_num: int,
        success: bool,
        score: int = 0,
        is_patch: bool = False,
        prev_score: float = 0,
        patch_fallback: bool = False,
        arc: int = 0,
    ) -> None:
        """Stage 4 시도 결과를 PassRateMonitor에 기록 (비차단)."""
        if not getattr(self.ctx, "pass_rate_monitor", None):
            return
        try:
            self.ctx.pass_rate_monitor.record_attempt(
                stage=4,
                episode=episode,
                arc=arc,
                attempt_num=round_num + 1,
                success=success,
                reject_reason="" if success else f"score={score}",
                generation_method="patch" if is_patch and not patch_fallback else "ensemble",
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
            )
        except Exception:
            pass
