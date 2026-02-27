"""
[B-1-3] Stage4 Interview Round — 단일 면담 라운드 실행.
"""

import logging

from modules.core.context_advisor import RetrievalSources


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
        story_context = round_ctx.story_context
        style_guide = round_ctx.style_guide
        reference_anchor_prompt = round_ctx.reference_anchor_prompt
        mandatory_context = round_ctx.mandatory_context
        justification_prompt = round_ctx.justification_prompt
        reflexion_prompt = round_ctx.reflexion_prompt

        if type(director_feedback) is not str:
            director_feedback = str(director_feedback or "")
        if type(mandatory_context) is not str:
            mandatory_context = str(mandatory_context or "")

        # [TF-T4] 25개 공통 kwargs — 4개 호출부에서 재사용
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
            # episode_digest는 Director 전용 — L713에서 별도 전달
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
            _patch_enabled = bool(_threshold("feature_flags.enable_patch_mode", True))
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
            # [TF-7-P0-04] EMPTY → QualityDashboard 집계
            if getattr(self.ctx, "quality_dashboard", None):
                try:
                    self.ctx.quality_dashboard.record_validation(
                        ep_num=next_ep,
                        result={
                            "decision": "REJECT",
                            "score": 0,
                            "violations": [{"type": "empty_candidates"}],
                            "warnings": [],
                        },
                        stage=4,
                    )
                except Exception as _qd_err:
                    logging.debug(f"[SILENT] quality_dashboard EMPTY: {_qd_err}")
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
                "genre": genre_name,
                "martial_hud": {},
                "karma_matrix": {},
                "asset_library": {},
                "npc_profiles": {},
                "prev_episode_events": [],
                "ep_num": next_ep,
                "blueprint": blueprint if isinstance(blueprint, dict) else {},
                "blueprint_text": str(blueprint or "")[:3000],
            }
            # [P1-FIX] prev_hud 주입 — ContinuityValidator 연속성 검증 활성화
            _prev_hud = {}
            if next_ep > 1:
                try:
                    if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                        _prev_hud = self.ctx.sys.hud.pro_root
                        if not isinstance(_prev_hud, dict):
                            _prev_hud = {}
                except Exception as _hud_err:
                    logging.warning(f"[SilentPass:InterviewRound] prev_hud 로드 실패: {_hud_err!s:.100}")
            _cv_context["prev_hud"] = _prev_hud
            # martial_hud도 동일 소스 (하위 호환)
            if _prev_hud:
                _cv_context["martial_hud"] = _prev_hud
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
            # [P3-02] protagonist_name 항상 주입 — POV 검사 민감도 보장
            if "protagonist_name" not in _cv_context:
                _proto_name = ""
                try:
                    from modules.core.constants import HUDKeys

                    _mb = self.ctx.current_project.master_bible or {}
                    _mb_root = _mb.get("MasterBible", _mb)
                    _proto_name = HUDKeys.get_protagonist_name(_mb_root, genre_name)
                except Exception:
                    pass
                if _proto_name and _proto_name != "주인공":
                    _cv_context["protagonist_name"] = _proto_name
                else:
                    logging.warning("[Stage4] protagonist_name 주입 실패 — POV 검사 민감도 저하 가능")
            # [P6-01] FailureLearner 주입 — ValidationOrchestrator가 BLOCKING 실패 시 환류할 수 있도록
            _cv_context["_failure_learner"] = getattr(self.ctx, "failure_learner", None)
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
            # [P2-FIX] karma_matrix 조립 — ConsistencyValidator unresolved_conflict 활성화
            _karma_dict = {}
            try:
                if next_ep > 1:
                    _prev_bible = self.ctx.current_project.db.get_episode_bible(next_ep - 1)
                    _raw_karma = _prev_bible.get("karma_matrix", []) if _prev_bible else []
                    if isinstance(_raw_karma, list):
                        for _k in _raw_karma:
                            if isinstance(_k, dict) and _k.get("target"):
                                _tgt = _k["target"]
                                if _tgt not in _karma_dict:
                                    _karma_dict[_tgt] = {"relation_type": _k.get("relation", ""), "events": []}
                                _karma_dict[_tgt]["events"].append(
                                    {
                                        "type": _k.get("type", ""),
                                        "description": _k.get("description", ""),
                                    }
                                )
            except Exception as _km_err:
                logging.warning(f"[SilentPass:InterviewRound] karma_matrix 조립 실패: {_km_err!s:.100}")
            if _karma_dict:
                _cv_context["karma_matrix"] = _karma_dict
            # [P2-FIX] villain_context 조립 — ConsistencyValidator villain_response 활성화
            _villain_ctx = {}
            try:
                _mb = self.ctx.current_project.master_bible or {}
                _mb_root = _mb.get("MasterBible", _mb)
                _key_npcs = _mb_root.get("AssetLibrary", {}).get("KeyNPCs", [])
                if not _key_npcs:
                    _key_npcs = _mb_root.get("AssetLibrary", {}).get("Key_NPCs", [])
                _VILLAIN_KEYWORDS = ("빌런", "적대", "악역", "antagonist", "주적", "숙적", "원수")
                for _npc in _key_npcs or []:
                    if not isinstance(_npc, dict):
                        continue
                    _role = str(_npc.get("role", ""))
                    if any(kw in _role for kw in _VILLAIN_KEYWORDS):
                        _vname = _npc.get("name", "")
                        if _vname:
                            # 사망 빌런은 스킵 → 다음 빌런 후보 탐색
                            if self.ctx.state_tracker and hasattr(self.ctx.state_tracker, "npc_registry"):
                                _v_info = self.ctx.state_tracker.npc_registry.get(_vname, {})
                                if _v_info.get("status") == "deceased":
                                    continue
                            _villain_ctx = {
                                "villain_name": _vname,
                                "villain_role": _role,
                                "is_aware": True,
                            }
                            break
            except Exception as _vc_err:
                logging.warning(f"[SilentPass:InterviewRound] villain_context 조립 실패: {_vc_err!s:.100}")
            if _villain_ctx:
                _cv_context["villain_context"] = _villain_ctx
            # [P2-FIX] authority_context 조립 — ConsistencyValidator authority_delegation 활성화
            _auth_ctx = {}
            try:
                _mb = self.ctx.current_project.master_bible or {}
                _mb_root = _mb.get("MasterBible", _mb)
                _key_npcs = _mb_root.get("AssetLibrary", {}).get("KeyNPCs", [])
                if not _key_npcs:
                    _key_npcs = _mb_root.get("AssetLibrary", {}).get("Key_NPCs", [])
                _SUPERIOR_KEYWORDS = (
                    "상사",
                    "상관",
                    "사부",
                    "스승",
                    "사형",
                    "문주",
                    "장문인",
                    "회장",
                    "대표",
                    "사장",
                    "원장",
                    "교수",
                )
                for _npc in _key_npcs or []:
                    if not isinstance(_npc, dict):
                        continue
                    _role = str(_npc.get("role", ""))
                    if any(kw in _role for kw in _SUPERIOR_KEYWORDS):
                        _sname = _npc.get("name", "")
                        if _sname:
                            # 사망 상사는 스킵 → 다음 상사 후보 탐색
                            if self.ctx.state_tracker and hasattr(self.ctx.state_tracker, "npc_registry"):
                                _s_info = self.ctx.state_tracker.npc_registry.get(_sname, {})
                                if _s_info.get("status") == "deceased":
                                    continue
                            _auth_ctx = {
                                "protagonist_position": _mb_root.get("protagonist_config", {}).get("position", ""),
                                "superior_alive": True,
                                "superior_name": _sname,
                                "superior_position": _npc.get("position", _role),
                            }
                            break
            except Exception as _ac_err:
                logging.warning(f"[SilentPass:InterviewRound] authority_context 조립 실패: {_ac_err!s:.100}")
            if _auth_ctx:
                _cv_context["authority_context"] = _auth_ctx
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

        # [V66.1] BlockingValidator — advisory 경고 수집 (Director 전달용)
        # [V70.1] 대원칙 준수: Python은 수집만, 판단은 Director(LLM)가.
        #   기존 TF7-P0-02 즉시 제외 → advisory 경고로 변환, Director에게 전달.
        try:
            for ci, cand in enumerate(candidates):
                _bv_ms = cand.get("manuscript", "")
                if _bv_ms and ci < len(validation_results):
                    bv_result = blocking_validator.validate(_bv_ms, _cv_context)
                    if not bv_result.get("passed", True):
                        bv_failures = bv_result.get("failures", [])
                        for f in bv_failures:
                            reason = f.get("reason", str(f))
                            severity = f.get("severity", "HIGH")
                            validation_results[ci]["warnings"].append(f"[Python검증-{severity}] {reason}")
                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                        validation_results[ci]["focus_points"].append(
                            f"Python 검증 경고 {len(bv_failures)}건 (Director 판단 필요)"
                        )
                        print(f"      ⚠️ 후보{ci + 1} Python 검증 경고 {len(bv_failures)}건 → Director에 전달")
                        for f in bv_failures:
                            print(f"         - [{f.get('severity', '?')}] {f.get('reason', '?')}")
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

        # [SC-5] Director 벡터 메모리 컨텍스트 조립 (후보 공통 1회)
        _director_memory_context = ""
        _sc5_perf_key = f"sc_director_ep{next_ep}_retrieval"
        try:
            self.ctx.perf_timer.start(_sc5_perf_key)
        except Exception as _e:
            logging.debug("[InterviewRound] perf_timer.start 실패 (무시): %s", _e)
        try:
            _advisor = getattr(self.ctx, "context_advisor", None)
            _vec_mem = getattr(self.ctx, "memory", None)
            _use_advisor_path = False
            if (
                _advisor
                and _vec_mem
                and next_ep > 1
                and _threshold("smart_retrieval.enabled", False)
                and _threshold("smart_retrieval.director_enabled", False)
            ):
                _npc_roster = []
                if isinstance(blueprint, dict):
                    _raw_chars = blueprint.get("characters") or blueprint.get("npcs") or []
                    if isinstance(_raw_chars, list):
                        for _char in _raw_chars:
                            _name = _char.get("name", "") if isinstance(_char, dict) else str(_char or "")
                            _name = _name.strip()
                            if _name and _name not in _npc_roster:
                                _npc_roster.append(_name)
                    elif isinstance(_raw_chars, str):
                        for _char in _raw_chars.replace("|", ",").split(","):
                            _name = _char.strip()
                            if _name and _name not in _npc_roster:
                                _npc_roster.append(_name)

                _is_arc_boundary = (arc_pos == 1) or (total_ep_in_arc > 0 and arc_pos == total_ep_in_arc)
                _is_reject_retry = round_num > 0
                _plan = _advisor.plan_director_retrieval(
                    manuscript="",
                    blueprint=blueprint or {},
                    current_ep=next_ep,
                    npc_roster=_npc_roster,
                    is_arc_boundary=_is_arc_boundary,
                    is_reject_retry=_is_reject_retry,
                )

                _max_results = int(_threshold("context.vector_max_results_s4", 20))
                _default_slot_max = int(_threshold("smart_retrieval.slot_max_chars_default", 1500))
                _max_npcs_per_slot = int(_threshold("smart_retrieval.max_npcs_per_slot", 5))
                _mem_parts = []
                for _slot in getattr(_plan, "slots", []) or []:
                    _slot_source = str(
                        getattr(_slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY
                    )
                    _slot_category = str(getattr(_slot, "category", "director_context") or "director_context")
                    _slot_query = str(getattr(_slot, "query", "") or "").strip()
                    if not _slot_query:
                        continue

                    try:
                        _slot_max = int(getattr(_slot, "max_chars", 0) or 0) or _default_slot_max
                        if _slot_source == RetrievalSources.DB_NPC_HISTORY and hasattr(
                            _vec_mem, "retrieve_npc_context"
                        ):
                            _slot_npcs = _npc_roster[:_max_npcs_per_slot]
                            if not _slot_npcs:
                                _slot_npcs = []
                                for _tok in _slot_query.replace("|", " ").replace("/", " ").replace(",", " ").split():
                                    _tok = _tok.strip()
                                    if len(_tok) < 2:
                                        continue
                                    if _tok not in _slot_npcs:
                                        _slot_npcs.append(_tok)
                                    if len(_slot_npcs) >= _max_npcs_per_slot:
                                        break
                            if not _slot_npcs:
                                continue
                            _npc_text = _vec_mem.retrieve_npc_context(
                                npc_names=_slot_npcs,
                                current_ep=next_ep,
                                max_results=_max_results,
                            )
                            if _npc_text:
                                _mem_parts.append(f"[SC:npc]\n{str(_npc_text)[:_slot_max]}")
                        else:
                            _vec_text = _vec_mem.retrieve_multi_query_context(
                                queries=[_slot_query],
                                current_ep=next_ep,
                                n_per_query=3,
                                max_results=_max_results,
                            )
                            if _vec_text:
                                _mem_parts.append(f"[SC:{_slot_category}]\n{str(_vec_text)[:_slot_max]}")
                    except Exception as _slot_err:
                        logging.warning(f"[SilentPass:SC:Director] 슬롯 {_slot_category} 실패: {_slot_err!s:.100}")

                if _mem_parts:
                    _budget = int(_threshold("smart_retrieval.director_total_budget", 20000))
                    _director_memory_context = "\n\n".join(_mem_parts)
                    if _budget > 0 and len(_director_memory_context) > _budget:
                        _director_memory_context = _director_memory_context[:_budget]
                    logging.info(f"[SC-5] Director 벡터 메모리 {len(_mem_parts)}건, {len(_director_memory_context)}자")
                    _use_advisor_path = True
            if not _use_advisor_path:
                _director_memory_context = ""
        except Exception as _sc5_err:
            logging.warning(f"[SilentPass:SC:Director] 벡터 메모리 조립 실패: {_sc5_err!s:.100}")
            _director_memory_context = ""
        finally:
            try:
                self.ctx.perf_timer.stop(_sc5_perf_key)
            except Exception:
                pass

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
        print(f"\n{'=' * 60}")
        print(f"   🎬 Director 면담 시작 (제{next_ep}화, {round_num + 1}차)")
        print(f"   후보 수: {len(candidates)}개")
        for _pi, _pv in enumerate(validation_results):
            _pw = _pv.get("warnings", [])
            _label = ["A", "B", "C"][_pi] if _pi < 3 else str(_pi + 1)
            print(f"   후보 {_label}: 경고 {len(_pw)}건, 분량 {len(candidates[_pi].get('manuscript', ''))}자")
            for _pwi in _pw[:5]:
                print(f"      - {_pwi}")
        print(f"{'=' * 60}")
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
        # [TF7-P1-04] 전략별 최근 통과율을 Director 선택 프롬프트에 주입
        try:
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if _db is not None and hasattr(_db, "get_strategy_win_rates"):
                _win_rates = _db.get_strategy_win_rates()
                if _win_rates and _win_rates.get("total", 0) > 0:
                    _wr_lines = [f"[TF7-P1-04] 전략별 최근 통과율 (최근 {_win_rates['total']}건 기준)"]
                    for _k, _v in _win_rates.items():
                        if _k != "total":
                            _wr_lines.append(f"  - {_k}: {int(_v * 100)}%")
                    _director_mc_parts.append("\n".join(_wr_lines))
        except Exception as _wr_err:
            logging.debug(f"[TF7-P1-04] win_rates fetch 실패 (비치명): {_wr_err}")
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
            story_context=story_context,  # [V67.1]
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
        error_category = director_result.get("error_category", "")  # [V75-B]

        self.ctx.ui.log(f"   📊 Director 판정: {verdict} (점수: {score}, 선택: 후보 {selected})")
        self.ctx.ui.log(f"      └─ 사유: {reason[:80]}...")
        print("\n   📊 Director 판정 결과:")
        print(f"      판정: {verdict} | 점수: {score} | 선택: 후보 {selected}")
        print(f"      사유: {reason[:120]}")
        _action_items = director_result.get("action_items", [])
        if _action_items:
            print("      지시사항:")
            for _ai in _action_items[:5]:
                print(f"         - {_ai}")
        print()

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

        # [V76] 라운드별 생산 로그 (JSONL)
        self._append_episode_log(
            ep_num=next_ep,
            round_num=round_num,
            director_result=director_result,
            is_patch=_is_patch,
            patch_fallback=_is_patch_fallback,
            tot_used=_tot_used,
            mad_used=_mad_used,
            asp_used=bool(_asp_manuscript),
            validation_warnings=[w for vr in validation_results for w in vr.get("warnings", [])][:10],
        )

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
            final_title = selected_candidate.get("title", f"\uc81c{next_ep}\ud654")
            final_state_updates = director_result.get("state_updates", {})

            # [Phase A-3] Post-select validation: run LLM checks on selected candidate only
            _post_select_conflicts = []

            # (a) Continuity check for selected candidate only
            if round_num == 0 and next_ep > 1 and final_manuscript:
                stage4_spinner.update_detail(f"Ep {next_ep} · post-select continuity check")
                try:
                    continuity_check = self.ctx.agents["director"].check_manuscript_continuity_with_cache(
                        new_manuscript=final_manuscript,
                        ep_num=next_ep,
                        db=self.ctx.current_project.db,
                        limit=10,
                        story_context=story_context,
                        memory_context=_director_memory_context,
                    )
                    if continuity_check.get("decision") == "CONFLICT":
                        _conflict_msg = continuity_check.get("summary", "Continuity conflict detected")
                        _post_select_conflicts.append(f"[Continuity Conflict] {_conflict_msg}")
                        self.ctx.ui.log(f"   [A-3] Post-select continuity conflict: {_conflict_msg[:80]}")
                except Exception as _cont_err:
                    logging.warning(f"[FailClosed:SC:PostSelectContinuity] {_cont_err!s:.100}")
                    _post_select_conflicts.append(
                        f"[Continuity Check Error] 검증 실패 (fail-closed): {str(_cont_err)[:80]}"
                    )

            # (b) History conflict check for selected candidate only
            if (
                _prev_manuscripts_text
                and final_manuscript
                and hasattr(self.ctx.agents.get("director", None), "check_manuscript_history_conflicts")
            ):
                stage4_spinner.update_detail(f"Ep {next_ep} · post-select history conflict check")
                try:
                    _ms_history_for_check = self._build_manuscript_history_for_check(_prev_manuscripts_text, next_ep)
                    if _ms_history_for_check:
                        _conflict_result = self.ctx.agents["director"].check_manuscript_history_conflicts(
                            ep_num=next_ep,
                            current_manuscript=final_manuscript,
                            manuscript_history=_ms_history_for_check,
                            use_summary=False,
                            story_context=story_context,
                            memory_context=_director_memory_context,
                        )
                        if _conflict_result.get("decision") == "CONFLICT":
                            _conflict_msg = _conflict_result.get("summary", "History conflict detected")
                            _post_select_conflicts.append(f"[V67] History Conflict: {_conflict_msg}")
                            self.ctx.ui.log(f"   [A-3] Post-select history conflict: {_conflict_msg[:80]}")
                except Exception as _hist_err:
                    logging.warning(f"[FailClosed:SC:PostSelectHistory] {_hist_err!s:.100}")
                    _post_select_conflicts.append(
                        f"[History Check Error] 검증 실패 (fail-closed): {str(_hist_err)[:80]}"
                    )

            # (c) Downgrade PASS to REJECT if post-select validation found conflicts
            if _post_select_conflicts:
                self.ctx.ui.log(
                    f"   [A-3] {len(_post_select_conflicts)} post-select conflicts detected -> downgrade to REJECT"
                )
                verdict = "REJECT"
                director_feedback += "\n" + "\n".join(_post_select_conflicts)
                # [P0-D3] 다운그레이드 시 previous_attempt 갱신 — 다음 라운드 패치 모드용
                previous_attempt = {
                    "best_manuscript": final_manuscript,
                    "state_updates": final_state_updates,
                    "score": score,
                }

            if verdict == "PASS":
                # [V66.1] F-1: time consistency check -> forward warnings to validator context
                if self.ctx.state_tracker:
                    try:
                        _time_warnings = self.ctx.state_tracker.check_time_consistency(
                            final_manuscript, self.ctx.state_tracker.in_world_timeline
                        )
                        if _time_warnings:
                            for tw in _time_warnings:
                                self.ctx.ui.log(f"   [V66.1] Time warning: {tw}")
                            # [V66.1] save warnings for validator context
                            self.time_warnings.extend(_time_warnings)
                    except (KeyError, ValueError, TypeError) as _tc_err:
                        logging.warning(f"[V66.1] Time consistency check failed: {_tc_err}")

                self.ctx.ui.log(f"   Round {round_num + 1} PASS!")
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
                    error_category=error_category,  # [V75-B]
                )
        if verdict != "PASS":
            # [TF-R2-S4-03] 시스템 감지 라인 보존 (REJECT 시 덮어쓰기 전 추출)
            _system_prefixes = ("[연속성 충돌]", "[Continuity Conflict]", "[V67]", "[CoVe]", "[ToT", "[MAD")
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
                "state_updates": director_result.get("state_updates", {}),  # [TF-R4-S4-01] 폴백 시 HUD 복구용
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
        # [TF7-P1-06] FailureLearner Stage4 REJECT 기록 (Stage2 stage2_validation_pipeline.py:425~433 동일 패턴)
        try:
            _fl = getattr(self.ctx, "failure_learner", None)
            if _fl is not None and hasattr(_fl, "record_failure"):
                _fl.record_failure(
                    stage=4,
                    episode=next_ep,
                    arc=round_ctx.arc_data.get("arc_no", 0),
                    reason=f"{_reject_bucket}: {director_feedback[:150]}",
                    details={"bucket": _reject_bucket, "score": score, "round": round_num},
                )
        except Exception as _fl_err:
            logging.debug(f"[TF7-P1-06] failure_learner Stage4 기록 실패 (비치명): {_fl_err}")
        # [TF7-P1-05] AdaptiveRetryManager Stage4 REJECT 연결 — 다음 라운드 프롬프트 주입용
        try:
            _adaptive_mgr = getattr(self.ctx, "adaptive_manager", None)
            if _adaptive_mgr is not None and hasattr(_adaptive_mgr, "record_failure"):
                _adaptive_mgr.record_failure(
                    ep_num=next_ep,
                    agent="director",
                    error_info={"reason": director_feedback[:200], "bucket": _reject_bucket},
                    attempt=round_num + 1,
                )
                if hasattr(_adaptive_mgr, "get_injection_prompt"):
                    _injection = _adaptive_mgr.get_injection_prompt(
                        ep_num=next_ep, agent="director", current_attempt=round_num + 1
                    )
                    if _injection:
                        director_feedback = director_feedback + "\n" + _injection
        except Exception as _am_err:
            logging.debug(f"[TF7-P1-05] adaptive_manager REJECT 기록 실패 (비치명): {_am_err}")
        # [TF-7-P0-04] REJECT → QualityDashboard 집계 (Stage2 동일 패턴)
        if getattr(self.ctx, "quality_dashboard", None):
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=next_ep,
                    result={
                        "decision": "REJECT",
                        "score": score,
                        "violations": [{"type": "director_reject", "description": str(director_feedback)[:200]}],
                        "warnings": [],
                    },
                    stage=4,
                )
            except Exception as _qd_err:
                logging.debug(f"[SILENT] quality_dashboard REJECT: {_qd_err}")
        return _InterviewRoundResult(
            verdict="REJECT",
            director_feedback=director_feedback,
            previous_attempt=previous_attempt,
            error_category=error_category,  # [V75-B]
        )

    # ── Stage 4 PassRateMonitor 기록 ──────────────────────────────

    def _build_manuscript_history_for_check(self, prev_manuscripts_text: str, next_ep: int) -> list:
        """[Phase A-3] Build manuscript-history records for conflict checks."""
        _ms_history_for_check = []
        import re as _re_hist

        if prev_manuscripts_text:
            for _block in prev_manuscripts_text.split("\n\n---\n\n"):
                _m = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\s*", _block)
                if _m:
                    _ep = int(_m.group(1))
                    _text = _block[_m.end() :]
                    if _text and len(_text) > 100:
                        _ms_history_for_check.append({"ep_num": _ep, "text": _text})

        if not _ms_history_for_check:
            for _prev_ep in range(max(1, next_ep - 30), next_ep):
                try:
                    _prev_ms_data = self.ctx.current_project.db.get_manuscript(_prev_ep)
                    if _prev_ms_data:
                        _content = (
                            _prev_ms_data.get("content", "") if isinstance(_prev_ms_data, dict) else str(_prev_ms_data)
                        )
                        if _content:
                            _ms_history_for_check.append({"ep_num": _prev_ep, "text": _content})
                except Exception as e:
                    logging.warning(f"[SilentPass:InterviewRound] ep{_prev_ep} history load failed: {e!s:.100}")

        return _ms_history_for_check

    def _append_episode_log(
        self,
        *,
        ep_num,
        round_num,
        director_result,
        is_patch,
        patch_fallback,
        tot_used,
        mad_used,
        asp_used,
        validation_warnings,
    ):
        """[V76] 라운드별 생산 로그를 JSONL로 기록."""
        try:
            import datetime
            import json
            import os

            logs_dir = os.path.join("projects", self.ctx.current_project.name, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            _sel_candidate = director_result.get("selected_candidate") or {}
            if not isinstance(_sel_candidate, dict):
                _sel_candidate = {}

            try:
                _log_score = int(director_result.get("score", 0))
            except (ValueError, TypeError):
                _log_score = 0

            entry = {
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "ep": ep_num,
                "round": round_num,
                "verdict": director_result.get("verdict", ""),
                "score": _log_score,
                "selected": director_result.get("selected", ""),
                "strategy": _sel_candidate.get("strategy", "") or _sel_candidate.get("strategy_name", ""),
                "error_category": director_result.get("error_category", ""),
                "reason": (director_result.get("selection_reason") or "")[:500],
                "action_items": (director_result.get("action_items") or [])[:5],
                "score_breakdown": director_result.get("score_breakdown", {}),
                "open_review": (director_result.get("open_review") or "")[:300],
                "flags": {
                    "patch_mode": is_patch,
                    "patch_fallback": patch_fallback,
                    "tot": tot_used,
                    "mad": mad_used,
                    "asp": asp_used,
                },
                "warnings": validation_warnings[:10],
            }

            log_path = os.path.join(logs_dir, "episode_production.jsonl")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logging.warning("[V76] episode_production log 실패 (비차단): %s", e)

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
        except Exception as _e:
            logging.debug("[InterviewRound] PassRateMonitor 기록 실패 (무시): %s", _e)
