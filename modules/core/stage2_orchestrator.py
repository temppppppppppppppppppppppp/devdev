"""
[V64.P3] Stage2Orchestrator — SovereignApp의 Stage 2 Arc 오케스트레이션 로직 캡슐화

SovereignApp에서 분리된 Stage 2 관련 메서드:
- stage_2_arcs_async_logic(): 메인 Arc 설계 비동기 파이프라인 (~1679줄)
- _normalize_tactical_text(): 전술서 텍스트 정규화
- _is_tactical_doc_duplicate(): 전술서 중복 감지
- _normalize_flow_text(): Flow Guard용 텍스트 정규화
- _stage2_flow_guard(): 서사 구조 분석 기반 Flow Guard
- _stage2_flow_guard_legacy(): 레거시 Flow Guard (폴백용)

모든 SovereignApp 속성은 self.app를 통해 접근.
"""

import asyncio
import logging

from modules.core.constants import VolumeSettings

DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC


class Stage2Orchestrator:
    """
    [V64.P3] SovereignApp의 Stage 2 Arc 오케스트레이션 로직 캡슐화

    [Phase 4C-3] self.ctx = Stage2Context DI 컨텍스트
    """

    def __init__(self, app, *, context=None) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (레거시 호환)
            context: Stage2Context DI 컨텍스트 (미주입 시 자동 빌드)
        """
        self.app = app
        self._ctx = context  # [Phase 4C-3] DI context
        self._validation_pipeline = None  # [B-1-6] lazy init
        self._preflight = None  # [B-1-8] lazy init
        self._finalizer = None  # [B-1-7] lazy init

    @property
    def ctx(self):
        """[Phase 4C-3] DI 컨텍스트 (미주입 시 app에서 자동 빌드)"""
        if self._ctx is None:
            from modules.core.stage2_context import Stage2Context

            self._ctx = Stage2Context.from_app(self.app)
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value

    @property
    def validation_pipeline(self):
        """[B-1-6] Validation chain sub-module (lazy init)."""
        if self._validation_pipeline is None:
            from modules.core.stage2_validation_pipeline import Stage2ValidationPipeline

            self._validation_pipeline = Stage2ValidationPipeline(self)
        return self._validation_pipeline

    @property
    def preflight(self):
        """[B-1-8] Preflight sub-module (lazy init)."""
        if self._preflight is None:
            from modules.core.stage2_preflight import Stage2PreflightAnalysis

            self._preflight = Stage2PreflightAnalysis(self)
        return self._preflight

    @property
    def finalizer(self):
        """[B-1-7] Finalizer sub-module (lazy init)."""
        if self._finalizer is None:
            from modules.core.stage2_finalizer import Stage2Finalizer

            self._finalizer = Stage2Finalizer(self)
        return self._finalizer

    # ═══════════════════════════════════════════════════════════════════════
    # 메인 파이프라인
    # ═══════════════════════════════════════════════════════════════════════

    async def stage_2_arcs_async_logic(self, *, target_arc_count: int | None = None):
        """
        [V37 S-Grade: 260124 매니페스토]
        0124 욕망 엔진(Desire Engine) 통합 파이프라인 완전판
        """
        # [V64.P3] lazy imports (main_a.py 스코프 밖이므로)
        from modules.core.constants import (
            HUDKeys,
            PatchModeThresholds,
            RecoveryLimits,
            VolumeSettings,
        )
        from modules.core.constraint_db import ConstraintDB
        from modules.core.slack_bot import notifier
        from modules.core.spinners import StageSpinner  # [V65] 스피너 (순환 참조 해소)
        from modules.domain.agents.state_tracker import StateTracker

        ### [0124 핵심] 욕망 엔진 가동 로고 및 로그 출력
        self.ctx.ui.log("🎯 [Stage 2] 0124 매니페스토: 욕망 엔진 및 인과율 용접 공정 기동...")

        # 1. 기초 데이터 확보 및 무결성 점검
        if not self.ctx.current_project.master_bible:
            self.ctx.current_project.master_bible = self.ctx.current_project.db.load_anchor("bible")
        if not self.ctx.current_project.volumes:
            self.ctx.current_project.volumes = self.ctx.current_project.db.load_anchor("volumes")

        bible_data = self.ctx.current_project.master_bible
        if not bible_data:
            self.ctx.ui.log("❌ [Stage 2] Bible 데이터를 찾을 수 없습니다. Stage 0-1을 먼저 실행하세요.")
            return
        # [V41 Patch] Stage 1 스킵 시 빈 volumes 안전 처리
        volumes_strategy = self.ctx.current_project.volumes or []
        if not volumes_strategy:
            self.ctx.ui.log("⚠️ [Notice] Volume 전략이 없습니다. 기본값으로 Arc 설계를 진행합니다.")
        bible_root = bible_data.get("MasterBible", bible_data)
        arcs_source = bible_root.get("plot_roadmap", [])

        # [V42] 주인공 이름 추출 (PROTAGONIST IDENTITY LOCK)
        # [V61.2 Fix] 장르별 HUD 탐색으로 변경
        protagonist_name = None
        genre = ""
        try:
            genre = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
            protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            if protagonist_name and protagonist_name != "주인공":
                self.ctx.ui.log(f"🔒 [V42] 주인공 이름 락: {protagonist_name}")
        except Exception as e:
            self.ctx.ui.log(f"⚠️ [V42] 주인공 이름 추출 실패: {e}")

        ### [V38 패치] 안전한 북극성 추출
        project_data = bible_root.get("ProjectData", {})
        meta_info = project_data.get("MetaInfo", {}) if isinstance(project_data, dict) else {}
        grand_obj = meta_info.get("grand_objective", "천하제일") if isinstance(meta_info, dict) else "천하제일"

        all_refined_arcs = self.ctx.current_project.db.load_anchor("arcs") or []
        done_count = len(all_refined_arcs)
        total_count = len(arcs_source)

        # [V60.94] StateTracker 초기화 - NPC 생사/무공 습득/정보 추적
        # [V62.5] 증분 업데이트: 기존 StateTracker가 있으면 재사용, 새 Arc만 추가
        existing_tracker_arcs = self.ctx.state_tracker_loaded_arcs or 0
        if (
            self.ctx.state_tracker is None
            or existing_tracker_arcs == 0
            or existing_tracker_arcs > len(all_refined_arcs)
        ):  # [V62.5] Arc 삭제 감지 → 리셋
            self.ctx.state_tracker = StateTracker(
                preset_registry=self.ctx.preset_registry, llm_client=self.ctx.sys.api_client
            )
            self.ctx.state_tracker.bind_db(self.ctx.current_project.db)  # [NPC-L1] NPC 이력 DB 배선
            existing_tracker_arcs = 0
            # [V63.4 P0] DB에서 금융 레지스트리 복원 (투자물)
            _saved_fin = self.ctx.current_project.load_v20_anchor("financial_registry", default=None)
            if _saved_fin:
                self.ctx.state_tracker.import_financial_registry(_saved_fin)

        new_arcs_to_load = all_refined_arcs[existing_tracker_arcs:]
        _genre_for_tracker = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
        self.ctx.state_tracker.full_extract_from_arcs(new_arcs_to_load, genre=_genre_for_tracker)
        self.ctx.state_tracker_loaded_arcs = len(all_refined_arcs)

        # [V63.4 P0] 금융 레지스트리 DB 영구 저장 (투자물)
        if _genre_for_tracker == "investment" and self.ctx.state_tracker.financial_number_registry:
            self.ctx.current_project.save_v20_anchor(
                "financial_registry", self.ctx.state_tracker.export_financial_registry()
            )

        if self.ctx.state_tracker.npc_registry:
            dead_count = sum(1 for info in self.ctx.state_tracker.npc_registry.values() if info.get("status") == "dead")
            total_npcs = len(self.ctx.state_tracker.npc_registry)
            loaded_msg = f"(신규 {len(new_arcs_to_load)}개)" if new_arcs_to_load else "(캐시 재사용)"
            self.ctx.ui.log(
                f"      👤 [V62.5] StateTracker: NPC {total_npcs}명 로드 (사망: {dead_count}명) {loaded_msg}"
            )

        # [V40.1 Smart Skip] 기존 원고가 있다면 해당 Arc까지 자동 건너뛰기
        existing_ms_max_ep = (
            self.ctx.get_max_episode_from_manuscripts()
            if callable(getattr(self.ctx, "get_max_episode_from_manuscripts", None))
            else 0
        )
        if existing_ms_max_ep > 0:
            skip_arc_no = self.ctx.calculate_arc_from_episode(existing_ms_max_ep)
            if skip_arc_no > done_count:
                self.ctx.ui.log(f"📂 [Manuscript Detected] 기존 원고 {existing_ms_max_ep}화까지 발견")
                self.ctx.ui.log(
                    f"⚠️  [Warning] Arc {skip_arc_no}까지 필요하지만 Arc {done_count}까지만 DB에 존재합니다."
                )
                self.ctx.ui.log(f"💡 [Info] Arc {done_count + 1}부터 설계를 시작합니다. (원고와 Arc 동기화 필요)")

        if done_count >= total_count:
            self.ctx.ui.log("✅ 모든 아크 설계가 이미 완료되었습니다.")
            return

        ### [UI 세이프티 가드 복구] 사용자 경험 및 인과율 안정성 확보
        self.ctx.ui.log(f"📊 현재 설계 완료: {done_count} / {total_count} 아크")
        self.ctx.ui.log("💡 Tip: 인과율 정밀 용접을 위해 1회 10개(2개 배치) 이내 진행을 권장합니다.")

        if target_arc_count is not None:
            # [OneStop] 프로그래밍 호출: 지정 개수만큼만 생성
            target_limit = min(done_count + target_arc_count, total_count)
        else:
            default_limit = min(done_count + 5, total_count)
            if callable(getattr(self.ctx, "get_int_input", None)):
                target_limit = self.ctx.get_int_input(
                    f"👉 몇 번 아크까지 설계하시겠습니까? (현재 {done_count + 1} ~ 최대 {total_count}): ",
                    default=default_limit,
                    min_val=done_count + 1,
                    max_val=total_count,
                )
            else:
                target_limit = default_limit
        target_limit = max(done_count + 1, min(target_limit, total_count))

        sem = asyncio.Semaphore(5)

        # [V49.4] Pre-Generation Constraint DB 초기화
        constraint_db = ConstraintDB(self.ctx.current_project)
        self.ctx.ui.log(f"🔒 [V49.4] ConstraintDB 초기화 완료 (기존 Arc: {len(constraint_db.arc_states)}개)")

        # [V62.5] extract_cumulative_state 배치 캐시
        self.ctx.cumulative_state_cache = None
        self.ctx.cumulative_state_cache_key = None  # [S-08] 센티넬
        last_refined_context = ""  # [감리] UnboundLocalError 방지 — generate_arc_context_v60 비활성 시 폴백

        # 2. 배치(Batch) 처리 루프 시작
        for batch_start in range(done_count, target_limit, 5):
            batch_end = min(batch_start + 5, target_limit)
            batch_start_count = len(all_refined_arcs)

            # [V61.2] 배치 전체를 스피너로 감싸기
            with StageSpinner(2, f"Batch {batch_start + 1}~{batch_end} 준비 및 농축"):
                self.ctx.ui.log(f"📦 [Batch] {batch_start + 1}~{batch_end}번 구간 욕망 수혈 공정 가동...")

                # [V60.10] 수혈 맥락 준비 - StateExtractor 활용
                if callable(getattr(self.ctx, "generate_arc_context_v60", None)):
                    last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)
                if all_refined_arcs:
                    self.ctx.ui.log(f"      🧠 [V60.10] StateExtractor: {len(all_refined_arcs)}개 Arc 상태 추출 완료")

                # A. [병렬 농축 단계]
                async def throttled_enrich(idx):
                    async with sem:
                        prev_b = arcs_source[idx - 1] if idx > 0 else None
                        curr_b = arcs_source[idx]
                        next_b_safe = (
                            {
                                "block_id": arcs_source[idx + 1].get("block_id", f"Block {idx + 2}"),
                                "title": arcs_source[idx + 1].get("title", "미정"),
                            }
                            if idx < total_count - 1
                            else {"title": "최종 블록"}
                        )
                        return await self.ctx.agents["analyst"].enrich_raw_block_async(
                            curr_b, prev_b, next_b_safe, [], transfused_history=last_refined_context
                        )

                enrichment_tasks = [throttled_enrich(i) for i in range(batch_start, batch_end)]
                enriched_batch = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

            # [안전성 패치] 실패한 항목에 대한 재시도 메커니즘
            indexed_batch = []
            failed_indices = []
            for idx, item in enumerate(enriched_batch):
                source_arc_idx = batch_start + idx
                if isinstance(item, Exception):
                    self.ctx.ui.log(f"⚠️ [Enrich] 병렬 농축 실패 (idx={source_arc_idx}): {item}")
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event(
                            "enrich_error", "batch enrich failed", {"error": str(item), "arc_idx": source_arc_idx}
                        )
                    failed_indices.append(source_arc_idx)
                    continue
                if not isinstance(item, dict):
                    self.ctx.ui.log(f"⚠️ [Enrich] 잘못된 데이터 타입 (idx={source_arc_idx}): {type(item)}")
                    failed_indices.append(source_arc_idx)
                    continue
                indexed_batch.append((source_arc_idx, item))

            enriched_batch = indexed_batch

            # [V40.1 Critical Fix] 복구 시도
            if failed_indices and len(enriched_batch) < (batch_end - batch_start):
                self.ctx.ui.log(f"🔄 [Recovery] {len(failed_indices)}개 항목 순차 재시도 중...")
                recovery_map = {}

                for failed_idx in failed_indices[: RecoveryLimits.MAX_PARALLEL_RECOVERY]:
                    try:
                        prev_b = arcs_source[failed_idx - 1] if failed_idx > 0 else None
                        curr_b = arcs_source[failed_idx]
                        next_b_safe = (
                            {
                                "block_id": arcs_source[failed_idx + 1].get("block_id", f"Block {failed_idx + 2}"),
                                "title": arcs_source[failed_idx + 1].get("title", "미정"),
                            }
                            if failed_idx < total_count - 1
                            else {"title": "최종 블록"}
                        )
                        recovered_item = await self.ctx.agents["analyst"].enrich_raw_block_async(
                            curr_b, prev_b, next_b_safe, [], transfused_history=last_refined_context
                        )
                        if isinstance(recovered_item, dict):
                            recovery_map[failed_idx] = recovered_item
                            self.ctx.ui.log(f"✅ [Recovery] idx={failed_idx} 복구 성공")
                    except Exception as retry_err:
                        self.ctx.ui.log(f"🚨 [Recovery] idx={failed_idx} 복구 실패: {retry_err}")

                # [V43 Fix] 원래 위치에 삽입하여 순서 보장
                if recovery_map:
                    # [V70] compacted enriched_batch → 원본 인덱스 복원 (failed_indices 간격 반영)
                    original_batch_data = {orig_idx: arc_data for orig_idx, arc_data in enriched_batch if arc_data}
                    original_batch_data.update(recovery_map)
                    enriched_batch = []
                    for idx in range(batch_start, batch_end):
                        if idx in original_batch_data:
                            enriched_batch.append((idx, original_batch_data[idx]))
                        else:
                            self.ctx.ui.log(f"⚠️ [Recovery] idx={idx} 데이터 누락 - 해당 Arc 스킵")
                            if callable(getattr(self.ctx, "audit_event", None)):
                                self.ctx.audit_event("data_missing", "arc data not recovered", {"arc_idx": idx})

            if not enriched_batch:
                self.ctx.ui.log("❌ [Critical] 농축 결과가 비어 있습니다. 공정을 중단합니다.")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("enrich_error", "empty batch after sanitize and recovery")
                return

            ### [B. 사후 용접 및 고유 명사 앵커링]
            with StageSpinner(2, f"Arc {batch_start + 1}~{batch_end} 인과율 용접"):
                for i in range(len(enriched_batch) - 1):
                    arc_a_idx, arc_a = enriched_batch[i]
                    arc_b_idx, arc_b = enriched_batch[i + 1]
                    try:
                        stitch_res = self.ctx.agents["analyst"].stitch_joints(
                            arc_a.get("joint_docs", {}),
                            arc_b.get("joint_docs", {}),
                            arc_b.get("content", {}).get("context", ""),
                        )
                    except Exception as stitch_err:
                        self.ctx.ui.log(f"⚠️ [Analyst] Arc {arc_a_idx + 1}-{arc_b_idx + 1} 용접 실패: {stitch_err}")
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event(
                                "analyst_error",
                                "stitch_joints failed",
                                {"arc_pair": f"{arc_a_idx + 1}-{arc_b_idx + 1}", "error": str(stitch_err)},
                            )
                        continue

                    if stitch_res and isinstance(stitch_res, dict) and stitch_res.get("status") == "REPAIRED":
                        if "content" in arc_b and isinstance(arc_b["content"], dict):  # [V70] str 타입 방어
                            arc_b["content"]["context"] = stitch_res.get(
                                "repaired_joint_b", arc_b["content"].get("context", "")
                            )
                        if stitch_res.get("entity_anchors") and getattr(self.ctx.sys, "lore", None):
                            try:
                                self.ctx.sys.lore.update_v20_assets({"Temporary_Anchors": stitch_res["entity_anchors"]})
                                self.ctx.ui.log(f"      ⚓ Arc {arc_a_idx + 1}-{arc_b_idx + 1} 고유 명사 앵커링 완료.")
                            except Exception as lore_err:
                                self.ctx.ui.log(f"⚠️ [Lore] 앵커링 실패: {lore_err}")
                        self.ctx.ui.log(f"   🧶 Arc {arc_a_idx + 1}-{arc_b_idx + 1} 인과율 용접 완료.")

            # C. [순차 설계 단계]
            # [B3-P1-1] ep_end가 음수/0일 수 있으므로 max(1, ...) 경계값 방어
            current_ep_start = 1 if not all_refined_arcs else max(1, all_refined_arcs[-1].get("ep_end", 0) + 1)

            # [V60.45] while 루프로 변경 - "다시 하기" 지원
            idx = 0
            while idx < len(enriched_batch):
                source_arc_idx, enriched_block = enriched_batch[idx]
                global_arc_no = source_arc_idx + 1
                vol_no = ((global_arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME) + 1
                default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}
                current_vol_strategy = next(
                    (v for v in volumes_strategy if v.get("vol_no") == vol_no),
                    volumes_strategy[0] if volumes_strategy else default_vol_strategy,
                )

                ### [0124 핵심 1] Analyst: 결핍 리포트 생성 (순수 Python, 즉시 완료)
                try:
                    lack_report = self.ctx.agents["analyst"].get_lack_report(self.ctx.sys.hud.pro_root)
                except Exception as lack_err:
                    self.ctx.ui.log(f"⚠️ [Analyst] 결핍 리포트 생성 실패: {lack_err}")
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event(
                            "analyst_error", "get_lack_report failed", {"arc_no": global_arc_no, "error": str(lack_err)}
                        )
                    lack_report = {"martial_deficit": "분석 실패", "status": "error"}

                ### [4-R3-a] Preflight 상태 초기화
                _setup = self.preflight._preflight_state_setup(
                    all_refined_arcs=all_refined_arcs,
                    arcs_source=arcs_source,
                    arc_idx=source_arc_idx,
                    lack_report=lack_report,
                    grand_obj=grand_obj,
                    global_arc_no=global_arc_no,
                    constraint_db=constraint_db,
                    genre=_genre_for_tracker,
                )
                arc_drive = _setup["arc_drive"]
                _cached_preflight_injection = _setup["cached_preflight_injection"]
                _cached_preflight_result = _setup["cached_preflight_result"]
                passed = _setup["passed"]
                current_feedback = _setup["current_feedback"]
                constraint_block = _setup["constraint_block"]
                attempt = _setup["attempt"]
                max_attempts = _setup["max_attempts"]
                director_feedback_for_fourphase = _setup["director_feedback_for_fourphase"]
                _st_snapshot = _setup["st_snapshot"]

                _previous_attempt = None  # [Patch Mode] Arc 패치 모드를 위한 이전 시도 추적

                while attempt < max_attempts:
                    draft_validator_passed = False
                    consensus_passed = False

                    # [V60.10] 이전 시도 REJECT 패턴 분석
                    if attempt >= 1 and self.ctx.stage_rejection_history:
                        arc_rejections = [
                            r
                            for r in self.ctx.stage_rejection_history
                            if r.get("stage") == 2 and r.get("arc_no") == global_arc_no
                        ]
                        if arc_rejections:
                            pattern_analysis = self.ctx.analyze_rejection_pattern_v60(arc_rejections, global_arc_no)
                            if pattern_analysis:
                                current_feedback = pattern_analysis + "\n" + current_feedback
                                self.ctx.ui.log(f"      🔍 [V60.10] REJECT 패턴 분석 주입 ({len(arc_rejections)}건)")

                    ### [4-R3-b] Arc 분석 + 무기 준비
                    _analysis = self.preflight._preflight_arc_analysis(
                        attempt=attempt,
                        current_feedback=current_feedback,
                        constraint_block=constraint_block,
                        last_refined_context=last_refined_context,
                        all_refined_arcs=all_refined_arcs,
                        protagonist_name=protagonist_name,
                        global_arc_no=global_arc_no,
                        cached_preflight_injection=_cached_preflight_injection,
                        cached_preflight_result=_cached_preflight_result,
                    )
                    refined_arc = _analysis["refined_arc"]
                    generation_method = _analysis["generation_method"]
                    constraint_block = _analysis["constraint_block"]
                    entity_registry_for_director = _analysis["entity_registry_for_director"]

                    ### [4-R3-c] FourPhase 생성 + 상태 보강
                    _enrichment = self.preflight._preflight_enrichment(
                        attempt=attempt,
                        global_arc_no=global_arc_no,
                        current_ep_start=current_ep_start,
                        current_vol_strategy=current_vol_strategy,
                        enriched_block=enriched_block,
                        all_refined_arcs=all_refined_arcs,
                        bible_root=bible_root,
                        protagonist_name=protagonist_name,
                        director_feedback_for_fourphase=director_feedback_for_fourphase,
                        entity_registry_for_director=entity_registry_for_director,
                        genre_for_tracker=_genre_for_tracker,
                        previous_attempt=_previous_attempt,
                    )
                    four_phase_passed = _enrichment["four_phase_passed"]
                    refined_arc = _enrichment["refined_arc"]
                    generation_method = _enrichment["generation_method"]
                    draft_validator_passed = _enrichment["draft_validator_passed"]
                    consensus_passed = _enrichment["consensus_passed"]
                    _st_snapshot = _enrichment["st_snapshot"]
                    director_feedback_for_fourphase = _enrichment["director_feedback_for_fourphase"]
                    _was_patch = _enrichment.get("was_patch", False)
                    _patch_fallback = _enrichment.get("patch_fallback", False)
                    _prev_score = _enrichment.get("prev_score", 0)

                    # ─────────────────────────────────────────────────────────────
                    # [V60.77] FourPhase 실패 시 다음 대면으로
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc is None:
                        self.ctx.ui.log(
                            f"      🔄 [V60.77] FourPhase 실패 → Director 대면 {min(attempt + 2, max_attempts)}/{max_attempts} 재시도"
                        )
                        attempt += 1
                        continue

                    ### [4-R3-d] Pre-Director 검증 체인
                    _val = self.validation_pipeline.run_validation(
                        refined_arc=refined_arc,
                        four_phase_passed=four_phase_passed,
                        all_refined_arcs=all_refined_arcs,
                        entity_registry_for_director=entity_registry_for_director,
                        global_arc_no=global_arc_no,
                        current_ep_start=current_ep_start,
                        current_feedback=current_feedback,
                        generation_method=generation_method,
                        constraint_block=constraint_block,
                        enriched_block=enriched_block,
                        draft_validator_passed=draft_validator_passed,
                        consensus_passed=consensus_passed,
                        attempt=attempt,
                        protagonist_name=protagonist_name,
                        constraint_db=constraint_db,
                    )
                    if _val["action"] == "retry":
                        current_feedback = _val["current_feedback"]
                        # [FlowGuard→FourPhase] 검증 피드백을 FourPhase 경로에도 전달
                        director_feedback_for_fourphase = current_feedback
                        attempt += 1
                        continue
                    refined_arc = _val["refined_arc"]
                    draft_validator_passed = _val["draft_validator_passed"]
                    consensus_passed = _val["consensus_passed"]
                    suspected_duplicates = _val["suspected_duplicates"]

                    ### [4-R3-e] Director 심사 + 최종 처리
                    _fin = await self.finalizer.run_finalize(
                        refined_arc=refined_arc,
                        enriched_block=enriched_block,
                        arc_drive=arc_drive,
                        all_refined_arcs=all_refined_arcs,
                        global_arc_no=global_arc_no,
                        current_ep_start=current_ep_start,
                        current_feedback=current_feedback,
                        protagonist_name=protagonist_name,
                        suspected_duplicates=suspected_duplicates,
                        entity_registry_for_director=entity_registry_for_director,
                        constraint_block=constraint_block,
                        draft_validator_passed=draft_validator_passed,
                        consensus_passed=consensus_passed,
                        attempt=attempt,
                        generation_method=generation_method,
                        is_patch=_was_patch,
                        prev_score=_prev_score,
                        patch_fallback=_patch_fallback,
                        st_snapshot=_st_snapshot,
                        director_feedback_for_fourphase=director_feedback_for_fourphase,
                        last_refined_context=last_refined_context,
                        bible_root=bible_root,
                        genre=genre,
                        constraint_db=constraint_db,
                    )
                    # [Sweep45] 조기 retry 리턴 시 누락 키 방어 (.get 폴백)
                    last_refined_context = _fin.get("last_refined_context", last_refined_context)
                    current_ep_start = _fin.get("current_ep_start", current_ep_start)
                    current_feedback = _fin.get("current_feedback", current_feedback)
                    director_feedback_for_fourphase = _fin.get(
                        "director_feedback_for_fourphase", director_feedback_for_fourphase
                    )
                    _st_snapshot = _fin.get("st_snapshot", _st_snapshot)

                    # [Patch Mode] REJECT 시 previous_attempt 갱신 (패치 모드 판단용)
                    try:
                        _rej_score = int(_fin.get("score", 0))
                    except (ValueError, TypeError):
                        _rej_score = 0
                    _rej_arc = _fin.get("rejected_arc")
                    if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
                        _previous_attempt = {
                            "score": _rej_score,
                            "best_arc": _rej_arc,
                            "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
                            "score_breakdown": _fin.get("score_breakdown", {}),
                            "selection_reason": _fin.get("selection_reason", ""),
                            "validation_warnings": _fin.get("validation_warnings", []),
                        }
                    else:
                        _previous_attempt = None

                    if _fin["action"] == "break":
                        passed = True
                        break
                    if _fin["action"] in {"retry", "next"}:
                        # [Sweep4-D1] 동일 arc_no 재생성 시 StateExtractor 스탈 캐시 방지
                        try:
                            _se = self.ctx.agents.get("state_extractor") if self.ctx.agents else None
                            if _se and hasattr(_se, "invalidate_cache"):
                                _se.invalidate_cache(global_arc_no)
                        except Exception as cache_err:
                            logging.warning(
                                "[Sweep5-D] state_extractor cache invalidation failed (arc=%s): %s",
                                global_arc_no,
                                cache_err,
                            )
                    if _fin["action"] == "retry":
                        attempt += 1
                        continue
                    elif _fin["action"] == "next":
                        break

                    attempt += 1

                if not passed:
                    self.ctx.ui.log(f"🚨 [Critical] Arc {global_arc_no} 최종 설계 실패.")
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event(
                            "arc_design_failed",
                            "max retries exhausted",
                            {"arc_no": global_arc_no, "batch_start": batch_start, "batch_end": batch_end},
                        )

                    # [V60.46] 실패 리포트 생성 및 출력
                    failure_report_path = (
                        self.ctx.current_project.paths.root / "logs" / f"arc_{global_arc_no}_failure_report.txt"
                    )
                    failure_report_path.parent.mkdir(parents=True, exist_ok=True)

                    # [Sweep300-R2] None 가드 — L420 패턴과 일치
                    arc_rejects = (
                        [
                            r
                            for r in self.ctx.stage_rejection_history
                            if r.get("stage") == 2 and r.get("arc_no") == global_arc_no
                        ]
                        if self.ctx.stage_rejection_history
                        else []
                    )
                    current_constraints = (
                        constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A"
                    )

                    prev_items = []
                    for prev_arc in all_refined_arcs:
                        items = prev_arc.get("state_constraints", {}).get("items_acquired", [])
                        if items:
                            prev_items.extend(items if isinstance(items, list) else [items])

                    report_lines = [
                        f"{'=' * 60}",
                        f"Arc {global_arc_no} 실패 리포트",
                        f"{'=' * 60}",
                        "",
                        "[REJECT 히스토리]",
                    ]
                    for i, rej in enumerate(arc_rejects, 1):
                        report_lines.append(f"  시도 {rej.get('attempt', i)}: {rej.get('reason', 'N/A')}")

                    report_lines.extend(
                        [
                            "",
                            "[이전 Arc에서 이미 획득한 아이템 - 중복 획득 금지]",
                        ]
                    )
                    for item in prev_items:
                        report_lines.append(f"  ❌ {item}")

                    report_lines.extend(
                        [
                            "",
                            "[현재 제약 조건]",
                            str(current_constraints)[:6000] if current_constraints else "없음",
                            "",
                            "[마지막 생성된 Arc 데이터]",
                        ]
                    )
                    if refined_arc:
                        report_lines.append(f"  tactical_doc 길이: {len(refined_arc.get('tactical_doc', ''))}자")
                        report_lines.append(
                            f"  items_acquired: {refined_arc.get('state_constraints', {}).get('items_acquired', [])}"
                        )

                    report_content = "\n".join(report_lines)

                    def _write_failure_report(path, content):
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)

                    await asyncio.to_thread(_write_failure_report, failure_report_path, report_content)

                    logging.info(f"\n{'=' * 60}")
                    logging.warning(f"📋 [V60.46] Arc {global_arc_no} 실패 분석 리포트")
                    logging.info(f"{'=' * 60}")
                    logging.warning(f"\n🔴 REJECT 사유 ({len(arc_rejects)}회):")
                    for rej in arc_rejects[-3:]:
                        logging.info(f"- {rej.get('reason', 'N/A')[:100]}")
                    logging.info(f"\n🚫 중복 획득 금지 아이템 ({len(prev_items)}개):")
                    for item in prev_items[:5]:
                        logging.info(f"- {item}")
                    if len(prev_items) > 5:
                        logging.info(f"... 외 {len(prev_items) - 5}개")
                    logging.info(f"\n📁 전체 리포트: {failure_report_path}")
                    logging.info(f"{'=' * 60}\n")

                    if all_refined_arcs:
                        self.ctx.ui.log(f"💾 [Auto-Save] 현재까지 {len(all_refined_arcs)}개 Arc 저장 완료.")

                    # [V60.45] 다시 하기 옵션
                    while True:
                        logging.info("[1] 건너뛰고 계속")
                        logging.info("[2] 중단")
                        logging.info("[3] 다시 하기 (자동)")
                        logging.info("   [4] 수동 개입 (리포트 확인 후 재시도)")
                        try:
                            user_choice = (await asyncio.to_thread(input, "   선택 (기본: 2): ")).strip()
                        except (EOFError, KeyboardInterrupt, ValueError):
                            user_choice = "2"

                        if user_choice == "1":
                            self.ctx.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                            _skip_ep_raw = (
                                arcs_source[global_arc_no - 1].get("ep_count", DEFAULT_EP_COUNT)
                                if global_arc_no <= len(arcs_source)
                                else DEFAULT_EP_COUNT
                            )
                            try:
                                _skip_ep = int(_skip_ep_raw)
                            except (TypeError, ValueError):
                                _skip_ep = DEFAULT_EP_COUNT
                            current_ep_start += _skip_ep
                            break
                        elif user_choice == "3":
                            self.ctx.ui.log(f"🔄 Arc {global_arc_no} 다시 시도합니다...")
                            attempt = 0
                            passed = False
                            current_feedback = ""
                            constraint_block = constraint_db.generate_constraint_block(global_arc_no)
                            break
                        elif user_choice == "4":
                            logging.info(f"\n   📝 리포트 파일을 확인하세요: {failure_report_path}")
                            logging.info("   💡 문제가 된 아이템이나 표현을 확인 후, 아래 옵션을 선택하세요.")
                            try:
                                manual_input = (
                                    (
                                        await asyncio.to_thread(
                                            input,
                                            "   준비되면 [Enter]로 재시도, 'skip'으로 건너뛰기, 'quit'으로 중단: ",
                                        )
                                    )
                                    .strip()
                                    .lower()
                                )
                            except (EOFError, KeyboardInterrupt, ValueError):
                                manual_input = "quit"
                            if manual_input == "skip":
                                self.ctx.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                                _skip_ep2_raw = (
                                    arcs_source[global_arc_no - 1].get("ep_count", DEFAULT_EP_COUNT)
                                    if global_arc_no <= len(arcs_source)
                                    else DEFAULT_EP_COUNT
                                )
                                try:
                                    _skip_ep2 = int(_skip_ep2_raw)
                                except (TypeError, ValueError):
                                    _skip_ep2 = DEFAULT_EP_COUNT
                                current_ep_start += _skip_ep2
                                break
                            elif manual_input == "quit":
                                self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                                return
                            else:
                                self.ctx.ui.log(f"🔄 Arc {global_arc_no} 수동 확인 후 재시도...")
                                attempt = 0
                                passed = False
                                current_feedback = f"[사용자 수동 확인 완료] 이전 Arc에서 획득한 아이템: {', '.join(prev_items[:5])} 등 {len(prev_items)}개. 이 아이템들은 절대 다시 획득하면 안 됩니다!"
                                constraint_block = constraint_db.generate_constraint_block(global_arc_no)
                                break
                        else:
                            self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                            return

                    if user_choice == "3":
                        continue
                    if user_choice == "4" and manual_input not in ("skip",):
                        continue

                # [V60.45] 다음 Arc로
                idx += 1

            self.ctx.ui.log(f"✅ 배치({batch_start + 1}~{batch_end}) 욕망 엔진 이식 및 용접 완료.")

            # [V40] Slack 알림 전송
            try:
                batch_results_count = len(all_refined_arcs) - batch_start_count
                notifier.send_notification(
                    title=f"✅ [Arc] 제 {batch_start + 1}~{batch_end}번 아크 설계 완료",
                    message=f"프로젝트: {self.ctx.current_project.name}\n설계된 아크 수: {batch_results_count}개",
                    key_metrics={"완료 구간": f"{batch_start + 1} ~ {batch_end} Arc", "생성 수": batch_results_count},
                )
            except Exception as slack_err:
                self.ctx.ui.log(f"⚠️ [Slack] 알림 전송 실패 (무시하고 계속): {slack_err}")

        self.ctx.ui.log("✨ [Success] 0124 매니페스토 기반 전술 설계 전 공정 완료.")
        if callable(getattr(self.ctx, "write_audit_summary", None)):
            self.ctx.write_audit_summary("stage2_complete")
        if target_arc_count is None:  # [OneStop] 프로그래밍 호출 시 대기 건너뛰기
            try:
                await asyncio.to_thread(input, "\n[Enter] 메뉴로 돌아가기")
            except (EOFError, KeyboardInterrupt, ValueError):
                pass

    # ═══════════════════════════════════════════════════════════════════════
    # Stage 2 헬퍼 메서드
    # ═══════════════════════════════════════════════════════════════════════

    def _preflight_state_setup(self, **kwargs):
        """[B-1-8] Thin wrapper for backward compatibility."""
        return self.preflight._preflight_state_setup(**kwargs)

    def _preflight_arc_analysis(self, **kwargs):
        """[B-1-8] Thin wrapper for backward compatibility."""
        return self.preflight._preflight_arc_analysis(**kwargs)

    def _preflight_enrichment(self, **kwargs):
        """[B-1-8] Thin wrapper for backward compatibility."""
        return self.preflight._preflight_enrichment(**kwargs)

    async def _preflight_finalize(self, **kwargs):
        """[B-1-7] Thin wrapper for backward compatibility."""
        return await self.finalizer.run_finalize(**kwargs)

    def _preflight_validation(self, **kwargs):
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline.run_validation(**kwargs)

    def _record_s2_pass_metrics(self, **kwargs):
        """[B-1-7] Thin wrapper for backward compatibility."""
        return self.finalizer._record_s2_pass_metrics(**kwargs)

    def _record_s2_reject_metrics(self, **kwargs):
        """[B-1-7] Thin wrapper for backward compatibility."""
        return self.finalizer._record_s2_reject_metrics(**kwargs)

    def _normalize_tactical_text(self, text: str) -> str:
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline._normalize_tactical_text(text)

    def _is_tactical_doc_duplicate(
        self,
        candidate_text: str,
        reference_texts: list,
        threshold: float = 0.98,
    ) -> bool:
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline._is_tactical_doc_duplicate(candidate_text, reference_texts, threshold)

    def _normalize_flow_text(self, text: str) -> str:
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline._normalize_flow_text(text)

    def _stage2_flow_guard(self, refined_arc: dict) -> dict:
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline._stage2_flow_guard(refined_arc)

    def _stage2_flow_guard_legacy(self, normalized: list | str) -> dict:
        """[B-1-6] Thin wrapper for backward compatibility."""
        return self.validation_pipeline._stage2_flow_guard_legacy(normalized)
