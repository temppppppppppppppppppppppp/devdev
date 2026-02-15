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
import concurrent.futures  # [V66.1] arc_drive + preflight 병렬화
import json
import logging
import re
import time

from modules.models.arc import validate_arc

_perf_logger = logging.getLogger(__name__)  # [V65] PerfTimer 로깅


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
        self._ctx = context  # [Phase 4C-3] DI 컨텍스트

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

    # ═══════════════════════════════════════════════════════════════════════
    # 메인 파이프라인
    # ═══════════════════════════════════════════════════════════════════════

    async def stage_2_arcs_async_logic(self):
        """
        [V37 S-Grade: 260124 매니페스토]
        0124 욕망 엔진(Desire Engine) 통합 파이프라인 완전판
        """
        # [V64.P3] lazy imports (main_a.py 스코프 밖이므로)
        from modules.core.constants import (
            AIModels,
            HUDKeys,
            RecoveryLimits,
            VolumeSettings,
        )
        from modules.core.constraint_db import ConstraintDB
        from modules.core.slack_bot import notifier
        from modules.domain.agents.state_tracker import StateTracker

        # [V65] 모델명 상수 — constants.py AIModels SSOT
        _SUMMARY_MODEL = AIModels.SUMMARY_MODEL

        # [V65] 스피너 & 전역 상수 → spinners 모듈에서 직접 import (순환 참조 해소)
        from modules.core.spinners import V50_MODULES_AVAILABLE, StageSpinner, rich_console

        ReflectionTarget = None
        if V50_MODULES_AVAILABLE:
            try:
                from modules.core.self_reflection import ReflectionTarget as _RT

                ReflectionTarget = _RT
            except ImportError:
                pass

        ### [0124 핵심] 욕망 엔진 가동 로고 및 로그 출력
        self.ctx.ui.log("🎯 [Stage 2] 0124 매니페스토: 욕망 엔진 및 인과율 용접 공정 기동...")

        # 1. 기초 데이터 확보 및 무결성 점검
        if not self.ctx.current_project.master_bible:
            self.ctx.current_project.master_bible = self.ctx.current_project.db.load_anchor("bible")
        if not self.ctx.current_project.volumes:
            self.ctx.current_project.volumes = self.ctx.current_project.db.load_anchor("volumes")

        bible_data = self.ctx.current_project.master_bible
        # [V41 Patch] Stage 1 스킵 시 빈 volumes 안전 처리
        volumes_strategy = self.ctx.current_project.volumes or []
        if not volumes_strategy:
            self.ctx.ui.log("⚠️ [Notice] Volume 전략이 없습니다. 기본값으로 Arc 설계를 진행합니다.")
        bible_root = bible_data.get("MasterBible", bible_data)
        arcs_source = bible_root.get("plot_roadmap", [])

        # [V42] 주인공 이름 추출 (PROTAGONIST IDENTITY LOCK)
        # [V61.2 Fix] 장르별 HUD 탐색으로 변경
        protagonist_name = None
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
        existing_tracker_arcs = getattr(self.app, "_state_tracker_loaded_arcs", 0)
        if (
            self.ctx.state_tracker is None
            or existing_tracker_arcs == 0
            or existing_tracker_arcs > len(all_refined_arcs)
        ):  # [V62.5] Arc 삭제 감지 → 리셋
            self.ctx.state_tracker = StateTracker(
                preset_registry=self.ctx.preset_registry, llm_client=self.ctx.sys.api_client
            )
            existing_tracker_arcs = 0
            # [V63.4 P0] DB에서 금융 레지스트리 복원 (투자물)
            _saved_fin = self.ctx.current_project.load_v20_anchor("financial_registry", default=None)
            if _saved_fin:
                self.ctx.state_tracker.import_financial_registry(_saved_fin)

        new_arcs_to_load = all_refined_arcs[existing_tracker_arcs:]
        _genre_for_tracker = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
        for prev_arc in new_arcs_to_load:
            self.ctx.state_tracker.extract_npc_deaths_from_arc(prev_arc)
            self.ctx.state_tracker.extract_skill_acquisitions_from_arc(prev_arc)
            self.ctx.state_tracker.extract_npc_info_from_arc(
                prev_arc, genre=_genre_for_tracker
            )  # [V60.95] NPC 무장/수준 정보 [V66.2] F-1 장르 가드
            self.ctx.state_tracker.extract_resolved_plots_from_arc(prev_arc)  # [V62.7] 완결된 플롯
            # [V66.1] F-1: 시간선 마커 추출
            try:
                self.ctx.state_tracker.extract_time_markers_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.1] 시간선 추출 실패 (무시): {e}")
            # [V66.1] F-8: NPC 신체 변화 추출
            try:
                self.ctx.state_tracker.extract_permanent_injuries_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.1] 신체 변화 추출 실패 (무시): {e}")
            # [V66.1] 동행자 변경 추출
            try:
                self.ctx.state_tracker.update_companions_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.1] 동행자 추출 실패 (무시): {e}")
            # [V66.1] 약속/맹세 추출
            try:
                self.ctx.state_tracker.extract_commitments_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.1] 약속 추출 실패 (무시): {e}")
            # [V66.1] 주인공 감정 추출
            try:
                self.ctx.state_tracker.extract_protagonist_emotion_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.1] 감정 추출 실패 (무시): {e}")
            # [V66.2] H-1~H-5: 재시작 시 V66 확장 데이터 복원
            try:
                self.ctx.state_tracker.extract_item_states_from_arc(prev_arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning(f"[V66.3] Init load 복원 실패 (major_items): {e}")
            try:
                self.ctx.state_tracker.extract_entity_destructions_from_arc(prev_arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning(f"[V66.3] Init load 복원 실패 (entity_destructions): {e}")
            try:
                self.ctx.state_tracker.extract_npc_personality_from_arc(prev_arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning(f"[V66.3] Init load 복원 실패 (npc_personality): {e}")
            try:
                self.ctx.state_tracker.extract_npc_npc_relationships_from_arc(prev_arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning(f"[V66.3] Init load 복원 실패 (npc_npc_relationships): {e}")
            try:
                self.ctx.state_tracker.extract_npc_dialogue_styles_from_arc(prev_arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning(f"[V66.3] Init load 복원 실패 (dialogue_profiles): {e}")
            # [V66.2] D-1,2,3: 관계/부상/이동 추출 연결
            try:
                self.ctx.state_tracker.extract_relationship_changes_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.2] 관계 변화 추출 실패 (무시): {e}")
            try:
                self.ctx.state_tracker.extract_npc_injuries_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.2] NPC 부상 추출 실패 (무시): {e}")
            try:
                self.ctx.state_tracker.extract_npc_movements_from_arc(prev_arc)
            except Exception as e:
                logging.warning(f"[V66.2] NPC 이동 추출 실패 (무시): {e}")
            # [V63.1] 투자물: 금융 이벤트 추출
            if _genre_for_tracker == "investment":
                self.ctx.state_tracker.extract_financial_events_from_arc(prev_arc)
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
        existing_ms_max_ep = self.ctx.get_max_episode_from_manuscripts()
        if existing_ms_max_ep > 0:
            skip_arc_no = self.ctx.calculate_arc_from_episode(existing_ms_max_ep)
            if skip_arc_no <= done_count:
                pass
            elif skip_arc_no > done_count:
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

        default_limit = min(done_count + 5, total_count)
        target_limit = self.ctx.get_int_input(
            f"👉 몇 번 아크까지 설계하시겠습니까? (현재 {done_count + 1} ~ 최대 {total_count}): ",
            default=default_limit,
            min_val=done_count + 1,
            max_val=total_count,
        )
        target_limit = max(done_count + 1, min(target_limit, total_count))

        sem = asyncio.Semaphore(5)
        full_roadmap_str = json.dumps(arcs_source, ensure_ascii=False)

        # [V49.4] Pre-Generation Constraint DB 초기화
        constraint_db = ConstraintDB(self.ctx.current_project)
        self.ctx.ui.log(f"🔒 [V49.4] ConstraintDB 초기화 완료 (기존 Arc: {len(constraint_db.arc_states)}개)")

        # [V62.5] extract_cumulative_state 배치 캐시
        self.ctx.cumulative_state_cache = None
        self.ctx.cumulative_state_cache_key = 0

        # 2. 배치(Batch) 처리 루프 시작
        for batch_start in range(done_count, target_limit, 5):
            batch_end = min(batch_start + 5, target_limit)
            batch_start_count = len(all_refined_arcs)

            # [V61.2] 배치 전체를 스피너로 감싸기
            with StageSpinner(2, f"Batch {batch_start + 1}~{batch_end} 준비 및 농축"):
                self.ctx.ui.log(f"📦 [Batch] {batch_start + 1}~{batch_end}번 구간 욕망 수혈 공정 가동...")

                # [V60.10] 수혈 맥락 준비 - StateExtractor 활용
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
            sanitized_batch = []
            failed_indices = []
            for idx, item in enumerate(enriched_batch):
                if isinstance(item, Exception):
                    self.ctx.ui.log(f"⚠️ [Enrich] 병렬 농축 실패 (idx={batch_start + idx}): {item}")
                    self.ctx.audit_event(
                        "enrich_error", "batch enrich failed", {"error": str(item), "arc_idx": batch_start + idx}
                    )
                    failed_indices.append(batch_start + idx)
                    continue
                if not isinstance(item, dict):
                    self.ctx.ui.log(f"⚠️ [Enrich] 잘못된 데이터 타입 (idx={batch_start + idx}): {type(item)}")
                    failed_indices.append(batch_start + idx)
                    continue
                sanitized_batch.append(item)

            enriched_batch = sanitized_batch

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
                    _success_indices = sorted(set(range(batch_start, batch_end)) - set(failed_indices))
                    original_batch_data = {}
                    for _si, _orig_idx in enumerate(_success_indices):
                        if _si < len(enriched_batch) and enriched_batch[_si]:
                            original_batch_data[_orig_idx] = enriched_batch[_si]
                    original_batch_data.update(recovery_map)
                    enriched_batch = []
                    for idx in range(batch_start, batch_end):
                        if idx in original_batch_data:
                            enriched_batch.append(original_batch_data[idx])
                        else:
                            self.ctx.ui.log(f"⚠️ [Recovery] idx={idx} 데이터 누락 - 해당 Arc 스킵")
                            self.ctx.audit_event("data_missing", "arc data not recovered", {"arc_idx": idx})

            if not enriched_batch:
                self.ctx.ui.log("❌ [Critical] 농축 결과가 비어 있습니다. 공정을 중단합니다.")
                self.ctx.audit_event("enrich_error", "empty batch after sanitize and recovery")
                return

            ### [B. 사후 용접 및 고유 명사 앵커링]
            with StageSpinner(2, f"Arc {batch_start + 1}~{batch_end} 인과율 용접"):
                for i in range(len(enriched_batch) - 1):
                    arc_a = enriched_batch[i]
                    arc_b = enriched_batch[i + 1]
                    try:
                        stitch_res = self.ctx.agents["analyst"].stitch_joints(
                            arc_a.get("joint_docs", {}),
                            arc_b.get("joint_docs", {}),
                            arc_b.get("content", {}).get("context", ""),
                        )
                    except Exception as stitch_err:
                        self.ctx.ui.log(
                            f"⚠️ [Analyst] Arc {batch_start + i + 1}-{batch_start + i + 2} 용접 실패: {stitch_err}"
                        )
                        self.ctx.audit_event(
                            "analyst_error",
                            "stitch_joints failed",
                            {"arc_pair": f"{batch_start + i + 1}-{batch_start + i + 2}", "error": str(stitch_err)},
                        )
                        continue

                    if stitch_res and isinstance(stitch_res, dict) and stitch_res.get("status") == "REPAIRED":
                        if "content" in arc_b and isinstance(arc_b["content"], dict):  # [V70] str 타입 방어
                            arc_b["content"]["context"] = stitch_res.get(
                                "repaired_joint_b", arc_b["content"].get("context", "")
                            )
                        if stitch_res.get("entity_anchors"):
                            try:
                                self.ctx.sys.lore.update_v20_assets({"Temporary_Anchors": stitch_res["entity_anchors"]})
                                self.ctx.ui.log(
                                    f"      ⚓ Arc {batch_start + i + 1}-{batch_start + i + 2} 고유 명사 앵커링 완료."
                                )
                            except Exception as lore_err:
                                self.ctx.ui.log(f"⚠️ [Lore] 앵커링 실패: {lore_err}")
                        self.ctx.ui.log(f"   🧶 Arc {batch_start + i + 1}-{batch_start + i + 2} 인과율 용접 완료.")

            # C. [순차 설계 단계]
            current_ep_start = 1 if not all_refined_arcs else all_refined_arcs[-1].get("ep_end", 0) + 1

            # [V60.45] while 루프로 변경 - "다시 하기" 지원
            idx = 0
            while idx < len(enriched_batch):
                enriched_block = enriched_batch[idx]
                global_arc_no = batch_start + idx + 1
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
                    self.ctx.audit_event(
                        "analyst_error", "get_lack_report failed", {"arc_no": global_arc_no, "error": str(lack_err)}
                    )
                    lack_report = {"martial_deficit": "분석 실패", "status": "error"}

                ### [4-R3-a] Preflight 상태 초기화
                _setup = self._preflight_state_setup(
                    all_refined_arcs=all_refined_arcs,
                    arcs_source=arcs_source,
                    arc_idx=batch_start + idx,
                    lack_report=lack_report,
                    grand_obj=grand_obj,
                    global_arc_no=global_arc_no,
                    constraint_db=constraint_db,
                )
                arc_drive = _setup["arc_drive"]
                _cached_preflight_injection = _setup["cached_preflight_injection"]
                _cached_preflight_result = _setup["cached_preflight_result"]
                passed = _setup["passed"]
                current_feedback = _setup["current_feedback"]
                constraint_block = _setup["constraint_block"]
                attempt = _setup["attempt"]
                max_fourphase_attempts = _setup["max_fourphase_attempts"]
                max_attempts = _setup["max_attempts"]
                director_feedback_for_fourphase = _setup["director_feedback_for_fourphase"]
                use_analyst_fallback = _setup["use_analyst_fallback"]
                _st_snapshot = _setup["st_snapshot"]

                while attempt < max_attempts:
                    draft_validator_passed = False
                    consensus_passed = False

                    if attempt == max_fourphase_attempts:
                        use_analyst_fallback = True
                        self.ctx.ui.log(
                            f"   ⏸️ [V60.77] FourPhase {max_fourphase_attempts}회 실패. Analyst 최후의 기회..."
                        )
                        self.ctx.audit_event(
                            "stage2_analyst_fallback",
                            f"FourPhase {max_fourphase_attempts} rejects, Analyst last chance",
                            {"arc_no": global_arc_no, "attempt": attempt},
                        )
                        time.sleep(1)  # [V66.1] 5→1초 축소 (폴백 전 불필요 대기 제거)
                        current_feedback = f"[🚨 최종 시도] FourPhase 3회 모두 Director REJECT. Analyst가 근본적 재설계 필요.\n{director_feedback_for_fourphase}"

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
                    _analysis = self._preflight_arc_analysis(
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
                    enhanced_context = _analysis["enhanced_context"]
                    recent_patterns = _analysis["recent_patterns"]
                    refined_arc = _analysis["refined_arc"]
                    generation_method = _analysis["generation_method"]
                    preflight_injection = _analysis["preflight_injection"]
                    constraint_block = _analysis["constraint_block"]
                    entity_registry_for_director = _analysis["entity_registry_for_director"]

                    # ─────────────────────────────────────────────────────────────
                    # [V60.77] FourPhaseArcGenerator
                    # ─────────────────────────────────────────────────────────────
                    four_phase_passed = False

                    if "four_phase" in self.ctx.agents and not use_analyst_fallback:
                        try:
                            self.ctx.ui.log(f"      🎯 [V60.77] FourPhase-Director 대면 {attempt + 1}/3")
                            with StageSpinner(2, f"Arc {global_arc_no}"):
                                # [V63.3] Stage 2 벡터 검색
                                _s2_vector_ctx = ""
                                try:
                                    if self.ctx.memory and current_ep_start > 1:
                                        _s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
                                            enriched_block.get("block_theme", ""), current_ep_start, n_results=2
                                        )
                                except Exception as e:  # [V64.P4] OPTIONAL: vector search — non-blocking
                                    self.ctx.audit_event("s2_vector_search_failed", str(e)[:100])
                                # [V65] PerfTimer: Arc 생성 측정
                                try:
                                    self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
                                except Exception:
                                    pass
                                four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].generate(
                                    arc_no=global_arc_no,
                                    ep_start=current_ep_start,
                                    vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                                    curr_block=enriched_block,
                                    prev_arcs=all_refined_arcs,
                                    assets=bible_root.get("AssetLibrary", {}),
                                    max_internal_retries=4,
                                    protagonist_name=protagonist_name or "주인공",
                                    director_feedback=director_feedback_for_fourphase,
                                    entity_registry=entity_registry_for_director,
                                    state_tracker=self.ctx.state_tracker,
                                    vector_context=_s2_vector_ctx,
                                )
                                try:
                                    self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_generate")
                                except Exception:
                                    pass

                            if four_phase_arc and pipeline_result.get("final_verdict") == "PASS":
                                refined_arc = four_phase_arc
                                generation_method = "four_phase"
                                four_phase_passed = True
                                draft_validator_passed = True
                                consensus_passed = True

                                refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
                                refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

                                logging.info(
                                    f"✅ [V60.77] FourPhase 성공! (내부 재시도: {pipeline_result.get('retries', 0)}회)"
                                )

                                # [V70] Director REJECT 시 롤백을 위한 StateTracker 핵심 레지스트리 스냅샷
                                import copy as _copy

                                _st = self.ctx.state_tracker
                                _st_snapshot = {
                                    "npc_registry": _copy.deepcopy(_st.npc_registry),
                                    "resolved_plots": _copy.deepcopy(_st.resolved_plots),
                                    "entity_destructions": _copy.deepcopy(_st.entity_destructions),
                                    "protagonist_skills": _copy.deepcopy(
                                        _st.protagonist_skills
                                    ),  # [V70] shallow→deep (set/list 내부 변형 방어)
                                    "skill_acquisitions": _copy.deepcopy(
                                        _st.skill_acquisitions
                                    ),  # [V70] shallow→deep (list of dicts)
                                    "npc_npc_relationships": _copy.deepcopy(_st.npc_npc_relationships),
                                    "item_state_registry": _copy.deepcopy(_st.item_state_registry),
                                    "active_plots": _copy.deepcopy(_st.active_plots),
                                    # [V70] 누락 필드 추가 (lines 770-818에서 수정되는 필드들)
                                    "npc_dialogue_profiles": _copy.deepcopy(_st.npc_dialogue_profiles),
                                    "in_world_timeline": _copy.deepcopy(_st.in_world_timeline),
                                    "current_companions": _copy.deepcopy(_st.current_companions),
                                    "pending_commitments": _copy.deepcopy(_st.pending_commitments),
                                    "protagonist_emotion": _copy.deepcopy(_st.protagonist_emotion),
                                }

                                # [V60.94] NPC 사망/무공 습득 추출 및 StateTracker 업데이트
                                dead_npcs = self.ctx.state_tracker.extract_npc_deaths_from_arc(refined_arc)
                                learned_skills = self.ctx.state_tracker.extract_skill_acquisitions_from_arc(refined_arc)
                                npc_info = self.ctx.state_tracker.extract_npc_info_from_arc(
                                    refined_arc, genre=_genre_for_tracker
                                )  # [V66.2] F-1 장르 가드
                                self.ctx.state_tracker.extract_resolved_plots_from_arc(refined_arc)
                                # [V66] 조직/장소 파괴, NPC 성격, NPC-NPC 관계 추출
                                self.ctx.state_tracker.extract_entity_destructions_from_arc(refined_arc)
                                self.ctx.state_tracker.extract_npc_personality_from_arc(refined_arc)
                                self.ctx.state_tracker.extract_npc_npc_relationships_from_arc(refined_arc)
                                # [V66] 아이템 상태 추출
                                self.ctx.state_tracker.extract_item_states_from_arc(refined_arc)
                                # [V66] 플롯 서스펜션 추적
                                self.ctx.state_tracker.update_plot_mentions_from_arc(refined_arc)
                                _suspended = self.ctx.state_tracker.check_suspended_plots(global_arc_no)
                                if _suspended:
                                    for sw in _suspended:
                                        logging.info(f"⚠️ [V66] {sw['message']}")
                                # [V66] 장르별 레지스트리 업데이트
                                try:
                                    self.ctx.state_tracker._populate_genre_registries_from_arc(refined_arc)
                                except Exception:
                                    pass
                                if _genre_for_tracker == "investment":
                                    self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)
                                    self.ctx.current_project.save_v20_anchor(
                                        "financial_registry", self.ctx.state_tracker.export_financial_registry()
                                    )

                                # [V66] SemanticPlotGuard 인덱싱
                                if (
                                    getattr(self.app, "semantic_plot_guard", None)
                                    and self.ctx.state_tracker.resolved_plots
                                ):
                                    try:
                                        indexed = self.ctx.semantic_plot_guard.index_resolved_plots(
                                            self.ctx.state_tracker.resolved_plots
                                        )
                                        if indexed > 0:
                                            logging.info(f"📊 [V66] SemanticPlotGuard: {indexed}개 플롯 인덱싱")
                                    except Exception:
                                        pass

                                # [V66] NPC 대화 스타일 추출
                                try:
                                    self.ctx.state_tracker.extract_npc_dialogue_styles_from_arc(refined_arc)
                                except Exception:
                                    pass  # [V66] OPTIONAL: 대화 스타일 추출 실패 비차단

                                # [V66.1] F-1: 시간선 마커 추출
                                try:
                                    self.ctx.state_tracker.extract_time_markers_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.1] 시간선 추출 실패 (무시): {e}")

                                # [V66.1] F-8: NPC 신체 변화 추출
                                try:
                                    self.ctx.state_tracker.extract_permanent_injuries_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.1] 신체 변화 추출 실패 (무시): {e}")

                                # [V66.1] 동행자 변경 추출
                                try:
                                    self.ctx.state_tracker.update_companions_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.1] 동행자 추출 실패 (무시): {e}")

                                # [V66.1] 약속/맹세 추출
                                try:
                                    self.ctx.state_tracker.extract_commitments_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.1] 약속 추출 실패 (무시): {e}")

                                # [V66.1] 주인공 감정 추출
                                try:
                                    self.ctx.state_tracker.extract_protagonist_emotion_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.1] 감정 추출 실패 (무시): {e}")

                                # [V66.2] D-1,2,3: 관계/부상/이동 추출 연결
                                try:
                                    self.ctx.state_tracker.extract_relationship_changes_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.2] 관계 변화 추출 실패 (무시): {e}")
                                try:
                                    self.ctx.state_tracker.extract_npc_injuries_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.2] NPC 부상 추출 실패 (무시): {e}")
                                try:
                                    self.ctx.state_tracker.extract_npc_movements_from_arc(refined_arc)
                                except Exception as e:
                                    logging.warning(f"[V66.2] NPC 이동 추출 실패 (무시): {e}")

                                # [V66] 멀티-Arc 요약 생성 및 저장
                                try:
                                    arc_summary = self.ctx.state_tracker.generate_arc_summary(
                                        global_arc_no, refined_arc
                                    )
                                    self.ctx.current_project.save_v20_anchor(
                                        f"arc_summary_{global_arc_no}", arc_summary
                                    )
                                    logging.info(f"\U0001f4ca [V66] Arc {global_arc_no} 요약 저장 완료")
                                except Exception as e:
                                    logging.warning(f"\u26a0\ufe0f [V66] Arc 요약 저장 실패 (비차단): {e}")

                                # [V69] 5 Arc마다 NPC 레지스트리 LLM 정리
                                if global_arc_no > 0 and global_arc_no % 5 == 0:
                                    try:
                                        removed = self.ctx.state_tracker.cleanup_npc_registry_with_llm(global_arc_no)
                                        if removed:
                                            logging.info(
                                                f"\U0001f9f9 [V69] NPC 레지스트리 정리: {len(removed)}개 오탐 제거 ({', '.join(removed[:5])})"
                                            )
                                    except Exception as e:
                                        logging.warning(f"\u26a0\ufe0f [V69] NPC 레지스트리 정리 실패 (비차단): {e}")

                                # [V61.3] 동적 장르 감지
                                tactical_doc = refined_arc.get("tactical_doc", "")
                                if tactical_doc and hasattr(self.ctx.state_tracker, "check_and_expand_genre"):
                                    new_genre = self.ctx.state_tracker.check_and_expand_genre(tactical_doc)
                                    if new_genre:
                                        logging.info(f"- 🎭 새 장르 감지: {new_genre}")

                                if dead_npcs:
                                    logging.info(f"- 💀 사망 NPC 기록: {', '.join(dead_npcs)}")
                                if learned_skills:
                                    logging.info(f"- 🥋 무공 습득 기록: {', '.join(learned_skills)}")
                                if npc_info:
                                    logging.info(f"- 👤 NPC 정보 기록: {len(npc_info)}건")

                                phases = pipeline_result.get("phases", {})
                                if phases.get("generate"):
                                    logging.info(f"- 후보 수: {phases['generate'].get('candidates_count', '?')}개")
                                    logging.info(f"- 선택 전략: {phases['generate'].get('selected_strategy', '?')}")
                            else:
                                logging.warning("⚠️ [V60.77] FourPhase 내부 검증 실패")
                                if pipeline_result.get("phases", {}).get("validate"):
                                    issues = pipeline_result["phases"]["validate"].get("issues_count", 0)
                                    logging.info(f"- 검증 이슈: {issues}개")
                                director_feedback_for_fourphase = "FourPhase 내부 검증 실패. 구조적 문제 해결 필요."
                        except Exception as fp_err:
                            logging.warning(f"❌ [V60.77] FourPhase 오류: {str(fp_err)[:80]}")
                            self.ctx.audit_event("four_phase_error", str(fp_err)[:100], {"arc_no": global_arc_no})
                            director_feedback_for_fourphase = f"FourPhase 오류 발생: {str(fp_err)[:100]}"

                    # ─────────────────────────────────────────────────────────────
                    # [V60.77] FourPhase 실패 시 다음 대면으로
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc is None and not use_analyst_fallback:
                        self.ctx.ui.log(f"      🔄 [V60.77] FourPhase 실패 → Director 대면 {attempt + 2}/3 재시도")
                        attempt += 1
                        continue

                    # ─────────────────────────────────────────────────────────────
                    # [V60.77] Analyst 호출 - 최후의 기회
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc is None and use_analyst_fallback:
                        try:
                            self.ctx.ui.log(f"      🆘 [V60.77] Analyst 최후의 기회! Arc {global_arc_no} 설계 시작...")

                            enhanced_arc_context = enhanced_context
                            if preflight_injection:
                                enhanced_arc_context = preflight_injection + "\n\n" + enhanced_arc_context
                            if constraint_block:
                                enhanced_arc_context = constraint_block + "\n\n" + enhanced_arc_context

                            logging.info(f"- 컨텍스트 크기: {len(enhanced_arc_context)}자")
                            logging.info(f"- 피드백: {current_feedback[:100] if current_feedback else '없음'}...")

                            with rich_console.status(
                                f"[bold cyan]🤖 Arc {global_arc_no} LLM 생성 중...[/]", spinner="dots"
                            ):
                                refined_arc = self.ctx.agents["analyst"].plan_single_arc_v20(
                                    arc_no=global_arc_no,
                                    vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                                    prev_block=None,
                                    curr_block=enriched_block,
                                    next_block=None,
                                    ep_start=current_ep_start,
                                    prev_arc_context=enhanced_arc_context,
                                    assets=bible_root.get("AssetLibrary", {}),
                                    full_roadmap=full_roadmap_str,
                                    assigned_seeds=[],
                                    feedback=current_feedback,
                                    recent_patterns=recent_patterns,
                                    protagonist_name=protagonist_name or "주인공",
                                    state_tracker=getattr(self.app, "state_tracker", None),
                                )
                            generation_method = "analyst"
                            logging.info("✅ [Analyst] Arc 생성 완료!")

                            if refined_arc:
                                logging.info(f"- tactical_doc: {len(refined_arc.get('tactical_doc', ''))}자")
                                logging.info(f"- ep_count: {refined_arc.get('ep_count', '?')}화")
                                logging.info(
                                    f"- items_acquired: {refined_arc.get('state_constraints', {}).get('items_acquired', [])}"
                                )
                        except Exception as analyst_err:
                            logging.warning(f"❌ [Analyst] 에러: {str(analyst_err)[:100]}")
                            self.ctx.audit_event(
                                "analyst_error",
                                "plan_single_arc_v20 failed",
                                {"arc_no": global_arc_no, "error": str(analyst_err)},
                            )
                            current_feedback = (
                                f"Analyst 엔진 오류: {str(analyst_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                            )
                            attempt += 1
                            continue

                    # ─────────────────────────────────────────────────────────────
                    # [무기 #3] DraftValidator - 정보 수집용
                    # ─────────────────────────────────────────────────────────────
                    python_advisory = []
                    if not four_phase_passed and refined_arc and self.ctx.arc_draft_validator:
                        try:
                            logging.info("🔬 [무기 #3] DraftValidator 사전 검증...")
                            draft_result = self.ctx.arc_draft_validator.validate(
                                arc=refined_arc,
                                prev_arcs=all_refined_arcs,
                                state_tracker=getattr(self.app, "state_tracker", None),
                            )
                            advisory_issues = draft_result.get("advisory_issues", [])
                            if advisory_issues:
                                logging.info(
                                    f"📋 [V60.56] DraftValidator advisory {len(advisory_issues)}개 발견 - LLM에게 전달"
                                )
                                for issue in advisory_issues[:3]:
                                    if isinstance(issue, dict):
                                        logging.info(f"- {issue.get('message', str(issue))[:60]}")
                                    else:
                                        logging.info(f"- {str(issue)[:60]}")
                                python_advisory.extend(advisory_issues)
                            logging.info("✅ [DraftValidator] 사전 검증 통과!")
                            draft_validator_passed = True
                        except Exception as dv_err:
                            logging.info(f"⚠️ [DraftValidator] 스킵: {str(dv_err)[:50]}")

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
                        try:
                            logging.info("🪞 [SelfReflector] Analyst 자기 비판 시작...")
                            arc_str = json.dumps(refined_arc, ensure_ascii=False, indent=2)
                            context_str = f"Arc {global_arc_no} 설계. 피드백: {current_feedback or '없음'}"

                            reflection_result = self.ctx.self_reflector.reflect_and_improve(
                                output=arc_str, context=context_str, target=ReflectionTarget.ANALYST, force=False
                            )

                            if reflection_result and reflection_result.improved != arc_str:
                                try:
                                    improved_arc = json.loads(reflection_result.improved)
                                    refined_arc = improved_arc
                                    logging.info(
                                        f"✅ [SelfReflector] 자기 개선 완료 (점수: {getattr(reflection_result, 'improvement_score', '?')})"
                                    )
                                except json.JSONDecodeError:
                                    logging.warning("⚠️ [SelfReflector] 개선 결과 파싱 실패, 원본 유지")
                            else:
                                logging.info("ℹ️ [SelfReflector] 개선 불필요")
                        except Exception as sr_err:
                            logging.info(f"⚠️ [SelfReflector] 스킵: {str(sr_err)[:50]}")

                    # ─────────────────────────────────────────────────────────────
                    # [V60.36] Consensus 검증
                    # ─────────────────────────────────────────────────────────────
                    if not four_phase_passed and refined_arc and "consensus" in self.ctx.agents:
                        try:
                            logging.info("🗳️ [Consensus] 3-LLM 합의 검증 시작...")
                            with rich_console.status("[bold magenta]🗳️ Consensus 3-LLM 검증 중...[/]", spinner="dots"):
                                consensus_verdict, consensus_result = self.ctx.agents[
                                    "consensus"
                                ].validate_with_consensus(
                                    arc=refined_arc,
                                    prev_arcs=all_refined_arcs,
                                    constraints="",
                                    python_advisory=python_advisory,
                                )

                            vote_summary = consensus_result.get("vote_summary", {})
                            logging.warning(
                                f"- 투표 결과: PASS {vote_summary.get('pass', 0)} / REJECT {vote_summary.get('reject', 0)}"
                            )

                            if consensus_verdict == "REJECT":
                                critical_issues = consensus_result.get("critical_issues", [])
                                all_issues = consensus_result.get("all_issues", [])
                                logging.warning("❌ [Consensus] REJECT!")
                                logging.warning(f"- CRITICAL: {len(critical_issues)}개")
                                logging.info(f"- 전체 이슈: {len(all_issues)}개")
                                for ci in critical_issues[:3]:
                                    logging.warning(f"🚨 [{ci.get('category', '?')}] {ci.get('issue', '?')[:80]}")

                                feedback_parts = [
                                    f"[{ci.get('category')}] {ci.get('issue')}" for ci in critical_issues[:3]
                                ]
                                current_feedback = "Consensus 검증 실패: " + "; ".join(feedback_parts)
                                refined_arc = None
                                logging.info(f"🔄 재시도 피드백: {current_feedback[:100]}...")
                                attempt += 1
                                continue
                            else:
                                logging.info("✅ [Consensus] PASS!")
                                consensus_passed = True
                                passed_checks = consensus_result.get("passed_checks", [])
                                if passed_checks:
                                    logging.info(f"- 통과 항목: {passed_checks[:3]}")
                        except Exception as cv_err:
                            logging.info(f"⚠️ [Consensus] 검증 스킵: {str(cv_err)[:50]}")

                    # [데이터 검증]
                    if not refined_arc or not isinstance(refined_arc, dict):
                        self.ctx.ui.log(
                            f"🚨 [Analyst Error] Arc {global_arc_no} 설계 결과가 유효하지 않음: {type(refined_arc)}"
                        )
                        self.ctx.audit_event(
                            "analyst_error",
                            "invalid response type",
                            {"arc_no": global_arc_no, "type": str(type(refined_arc))},
                        )
                        current_feedback = "Analyst가 유효한 딕셔너리를 반환하지 않았습니다. JSON 규격을 확인하라."
                        attempt += 1
                        continue

                    # 🧭 [Mapping Validation]
                    refined_arc = self.ctx.validate_arc_mapping(
                        refined_arc, enriched_block, global_arc_no, current_ep_start
                    )

                    # ⚡ [V60.25] Auto-Corrector
                    if self.ctx.stage2_optimizer:
                        try:
                            refined_arc, corrections = self.ctx.stage2_optimizer.post_process_arc(
                                arc=refined_arc, prev_arcs=all_refined_arcs
                            )
                            if corrections:
                                self.ctx.audit_event(
                                    "v60_25_auto_correct",
                                    "arc auto-corrected",
                                    {"arc_no": global_arc_no, "corrections": corrections[:5]},
                                )
                        except Exception as ac_err:
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
                            self.ctx.audit_event(
                                "constraint_suspected",
                                "suspected duplicates for LLM review",
                                {"arc_no": global_arc_no, "suspected": suspected_duplicates},
                            )

                        if pre_validation.get("warnings"):
                            for w in pre_validation["warnings"][:2]:
                                self.ctx.ui.log(f"      ⚠️ [V49.4 Warning] {w}")

                    # 🚨 [Stage2 Flow Guard]
                    flow_guard = self._stage2_flow_guard(refined_arc)
                    if flow_guard.get("status") == "REJECT":
                        self.ctx.ui.log(f"   🚨 [Flow Guard] {flow_guard.get('reason')}")
                        self.ctx.audit_event("flow_guard", flow_guard.get("reason"), {"arc_no": global_arc_no})
                        current_feedback = flow_guard.get("feedback", "서사 폭주/정체 위험이 감지되었습니다.")
                        attempt += 1
                        continue

                    # 🛡️ [Duplicate Guard]
                    if all_refined_arcs:
                        prev_tactical = all_refined_arcs[-1].get("tactical_doc", "")
                        if self._is_tactical_doc_duplicate(refined_arc.get("tactical_doc", ""), [prev_tactical]):
                            self.ctx.ui.log("   🚨 [Duplicate Guard] 전술 설계가 직전 아크와 중복됩니다. 재생성합니다.")
                            self.ctx.audit_event(
                                "duplicate_guard",
                                "arc tactical_doc duplicated",
                                {"arc_no": global_arc_no, "prev_arc_no": all_refined_arcs[-1].get("arc_no")},
                            )
                            current_feedback = (
                                "직전 아크와 동일한 전술 설계입니다. 사건/공간/인과를 완전히 새로 구성하십시오."
                            )
                            refined_arc = None
                            attempt += 1
                            continue

                    # [안전성 패치] Director 호출 전 필수 데이터 검증
                    if not refined_arc or not isinstance(refined_arc, dict):
                        self.ctx.ui.log("🚨 [Data Error] refined_arc가 유효하지 않습니다")
                        self.ctx.audit_event("data_validation_error", "refined_arc invalid", {"arc_no": global_arc_no})
                        current_feedback = "설계 데이터 구조 오류. 전술 설계를 완전한 JSON으로 재작성하라."
                        attempt += 1
                        continue

                    if not enriched_block or not isinstance(enriched_block, dict):
                        self.ctx.ui.log("🚨 [Data Error] enriched_block이 유효하지 않습니다")
                        self.ctx.audit_event(
                            "data_validation_error", "enriched_block invalid", {"arc_no": global_arc_no}
                        )
                        current_feedback = "농축 데이터 누락. 블록 정보를 포함하여 재설계하라."
                        attempt += 1
                        continue

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.56] Arc Draft 정보 수집
                    # ═══════════════════════════════════════════════════════════════
                    if not four_phase_passed and self.ctx.arc_draft_validator:
                        draft_result = self.ctx.arc_draft_validator.validate(
                            arc=refined_arc,
                            prev_arcs=all_refined_arcs,
                            constraint_block=constraint_block or "",
                            state_tracker=getattr(self.app, "state_tracker", None),
                        )

                        advisory_issues = draft_result.get("advisory_issues", [])
                        if advisory_issues:
                            self.ctx.ui.log(
                                f"      📋 [V60.56 DraftValidator] Advisory {len(advisory_issues)}개 - LLM이 최종 판단"
                            )
                            for issue in advisory_issues[:3]:
                                self.ctx.ui.log(f"         📝 {issue}")

                        if not draft_result["valid"]:
                            self.ctx.ui.log(
                                f"      🚨 [V60.11 DraftValidator] 사전 검증 실패 (점수: {draft_result['score']})"
                            )
                            for issue in draft_result["critical_issues"][:3]:
                                self.ctx.ui.log(f"         ❌ {issue}")

                            self.ctx.audit_event(
                                "draft_validation_reject",
                                "draft validation failed",
                                {
                                    "arc_no": global_arc_no,
                                    "score": draft_result["score"],
                                    "critical_count": len(draft_result["critical_issues"]),
                                },
                            )

                            all_issues = draft_result.get("issues", [])
                            critical_only = [i for i in all_issues if i.get("severity") == "CRITICAL"]
                            major_only = [i for i in all_issues if i.get("severity") in ["MAJOR", "WARNING"]]

                            if (
                                not critical_only
                                and major_only
                                and self.ctx.arc_corrector
                                and self.ctx.use_arc_corrector
                            ):
                                self.ctx.ui.log(
                                    f"      🔧 [V60.42] CRITICAL 없음, MAJOR {len(major_only)}개 - ArcCorrector 부분 수정 시도"
                                )

                                try:
                                    can_correct, correctable_issues, uncorrectable_issues = (
                                        self.ctx.arc_corrector.can_correct(major_only)
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
                                                state_tracker=getattr(self.app, "state_tracker", None),
                                            )

                                            if revalidation["valid"]:
                                                self.ctx.ui.log(
                                                    f"      ✅ [V60.42] 수정 후 재검증 통과 (점수: {revalidation['score']})"
                                                )
                                            else:
                                                self.ctx.ui.log("      ⚠️ [V60.42] 수정 후에도 검증 실패 - 재생성 필요")
                                                issues_str = "\n".join(
                                                    [f"- {i}" for i in revalidation["critical_issues"][:3]]
                                                )
                                                current_feedback = f"[ArcCorrector 수정 후에도 실패]\n{issues_str}"
                                                refined_arc = None
                                                attempt += 1
                                                continue
                                        else:
                                            reason = correction_log.get("reason", "알 수 없음")
                                            self.ctx.ui.log(f"      ⚠️ [V60.42] ArcCorrector 수정 실패: {reason}")
                                            self.ctx.audit_event(
                                                "arc_corrector_fail", reason, {"arc_no": global_arc_no}
                                            )
                                            issues_str = "\n".join(
                                                [f"- {i.get('message', str(i))}" for i in major_only[:3]]
                                            )
                                            current_feedback = f"[V60.42 수정 불가]\n{issues_str}\n재설계 필요."
                                            refined_arc = None
                                            attempt += 1
                                            continue
                                    else:
                                        uncorr_msgs = [i.get("message", "")[:30] for i in uncorrectable_issues[:2]]
                                        self.ctx.ui.log(f"      ⚠️ [V60.42] 수정 불가: {', '.join(uncorr_msgs)}")
                                        issues_str = "\n".join(
                                            [f"- {i.get('message', str(i))}" for i in major_only[:3]]
                                        )
                                        current_feedback = f"[수정 불가]\n{issues_str}"
                                        refined_arc = None
                                        attempt += 1
                                        continue

                                except Exception as corr_err:
                                    self.ctx.ui.log(f"      ⚠️ [V60.42] ArcCorrector 오류: {str(corr_err)[:50]}")
                                    self.ctx.audit_event("arc_corrector_error", str(corr_err)[:100])
                                    issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                                    current_feedback = f"[V60.11 검증 실패 + Corrector 오류]\n{issues_str}"
                                    refined_arc = None
                                    attempt += 1
                                    continue
                            else:
                                issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                                current_feedback = (
                                    f"[V60.11 DraftValidator 사전 검증 실패]\n"
                                    f"점수: {draft_result['score']}/100\n"
                                    f"문제점:\n{issues_str}\n\n"
                                    f"위 문제를 해결하고 다시 설계하세요."
                                )
                                refined_arc = None
                                attempt += 1
                                continue
                        else:
                            self.ctx.ui.log(
                                f"      ✅ [V60.11 DraftValidator] 사전 검증 통과 (점수: {draft_result['score']})"
                            )
                            if draft_result["warnings"]:
                                for w in draft_result["warnings"][:2]:
                                    self.ctx.ui.log(f"         ⚠️ {w}")

                    # ═══════════════════════════════════════════════════════════════
                    # [V49 NEW] Arc 수준 연속성 검증
                    # ═══════════════════════════════════════════════════════════════
                    if not four_phase_passed and "continuity_inspector" in self.ctx.agents:
                        self.ctx.ui.log(f"      🔍 [V49] Arc {global_arc_no} 연속성 검증 중...")

                        refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
                        refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

                        with rich_console.status(
                            f"[bold yellow]🔍 Arc {global_arc_no} 연속성 검증 중...[/]", spinner="dots"
                        ):
                            continuity_result = self.ctx.agents["continuity_inspector"].inspect_arc(
                                current_arc=refined_arc,
                                prev_arcs=all_refined_arcs,
                                entity_registry=entity_registry_for_director,
                            )

                        if continuity_result.get("decision") == "REJECT":
                            severity = continuity_result.get("severity", "UNKNOWN")
                            fix_instructions = continuity_result.get("fix_instructions", "")
                            violations = continuity_result.get("violations", [])

                            self.ctx.ui.log(f"      🚨 [V49 REJECT] Arc 연속성 위반 감지 (심각도: {severity})")
                            for v in violations[:3]:
                                self.ctx.ui.log(
                                    f"         - {v.get('type', 'unknown')}: {v.get('description', '')[:100]}"
                                )

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
                                        reason=f"{v.get('type', 'unknown')}: {v.get('description', '')[:150]}",
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

                            detailed_feedback = "\n".join(violation_details)

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
                                prev_state_reminder = (
                                    f"\n\n📌 [직전 Arc {last.get('arc_no', '?')} 확정 상태 - 반드시 계승할 것]:\n"
                                    f"- 위치: {last_joint.get('final_location', '?')}\n"
                                    f"- 소지품: {last_joint.get('physical_inventory', '?')}\n"
                                    f"- 내공 소모: {last_status.get('internal_energy_loss', '?')}\n"
                                    f"- 부상: {last_status.get('expected_injuries', '?')}"
                                )

                            structured_arc_feedback = self.ctx.generate_structured_arc_feedback(
                                continuity_result=continuity_result, prev_arcs=all_refined_arcs, arc_no=global_arc_no
                            )

                            adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
                            intensity_guide = (
                                f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
                            )

                            strong_kind_feedback = self.ctx.build_strong_kind_feedback(
                                violations=violations, attempt=attempt, protagonist_name=protagonist_name or "주인공"
                            )

                            focused_context = self.ctx.build_focused_context(
                                violations=violations,
                                prev_arcs=all_refined_arcs,
                                protagonist_name=protagonist_name or "주인공",
                            )

                            current_feedback = f"{strong_kind_feedback}\n\n{focused_context}"

                            feedback_size = len(current_feedback)
                            self.ctx.ui.log(f"      📋 [V60.21] 집중 피드백 주입 ({feedback_size}자, 목표: <500자)")
                            refined_arc = None
                            attempt += 1
                            continue
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

                    # [V66] SemanticPlotGuard 중복 검사
                    if getattr(self.app, "semantic_plot_guard", None):
                        try:
                            tactical_text = refined_arc.get("tactical_doc", "")
                            if isinstance(tactical_text, dict):
                                tactical_text = str(tactical_text)
                            spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                            if spg_warnings:
                                spg_text = self.ctx.semantic_plot_guard.format_warnings(spg_warnings)
                                logging.info(f"⚠️ [V66] {spg_text}")
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
                    except Exception:
                        pass

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
                            if len(_full_arc_history) > 200000:
                                _full_arc_history = _full_arc_history[:200000] + "\n... (200K자 절삭)"
                            _expanded_prev_context = (
                                f"[V67] ═══ 이전 Arc 전술서 전문 ({len(_prev_arc_docs)}개) ═══\n"
                                f"{_full_arc_history}\n\n"
                                f"═══ 상태 요약 ═══\n{last_refined_context}"
                            )
                            logging.info(
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
                    except Exception:
                        _story_context = ""

                    audit = self.ctx.agents["director"].audit_strategic_plan(
                        refined_arc,
                        _expanded_prev_context,
                        curr_block=enriched_block,
                        protagonist_name=protagonist_name,
                        suspected_duplicates=suspected_duplicates,
                        entity_registry=entity_registry_for_director,
                        story_context=_story_context,  # [V67.1]
                    )
                    try:
                        self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_director")
                    except Exception:
                        pass

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
                            self.ctx.ui.log(
                                f"      ⚠️ [V60.43] API 할당량 오류 감지 (score=0이 {zero_count}/{len(scores)}개)"
                            )
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

                    if audit.get("decision") == "PASS" and len(refined_arc.get("tactical_doc", "")) >= 1500:
                        ### [0124 핵심 3] 욕망 데이터 및 HUD 그림자 물리적 박제
                        refined_arc["arc_drive"] = arc_drive if arc_drive else {}
                        refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
                        refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

                        critical_missing = []
                        if not refined_arc.get("hybrid_composition"):
                            self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] 패턴 구성(hybrid_composition) 누락 - 기본값 주입")
                            self.ctx.audit_event(
                                "data_missing", "hybrid_composition missing", {"arc_no": global_arc_no}
                            )
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
                                "physical_inventory": "물품 미정",
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
                                if prev_inventory and prev_inventory != [] and prev_inventory != "[]":
                                    curr_status = refined_arc.get("status_shadow", {})
                                    consumed = curr_status.get("item_consumption", [])
                                    if isinstance(consumed, str):
                                        consumed = [consumed] if consumed else []
                                    state_constraints = refined_arc.get("state_constraints", {})
                                    acquired = state_constraints.get("items_acquired", [])
                                    if isinstance(acquired, str):
                                        acquired = [acquired] if acquired else []
                                    if isinstance(prev_inventory, list):
                                        inherited = [item for item in prev_inventory if item not in consumed]
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
                            self.ctx.ui.log(
                                f"🚨 [Arc {global_arc_no}] 핵심 데이터 과다 누락({len(critical_missing)}개)"
                            )
                            current_feedback = (
                                f"필수 키 누락: {', '.join(critical_missing)}. 완전한 JSON 구조로 재설계하라."
                            )
                            refined_arc = None
                            attempt += 1
                            continue

                        if not self.ctx.validate_arc_integrity(refined_arc):
                            current_feedback = (
                                "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
                            )
                            refined_arc = None
                            attempt += 1
                            continue

                        # [V66] SemanticPlotGuard 중복 체크 (중앙 인스턴스)
                        _spg = getattr(self.app, "semantic_plot_guard", None)
                        if _spg and _spg._resolved_embeddings:
                            try:
                                _new_tactical = refined_arc.get("tactical_doc", "")
                                _spg_warnings = _spg.check_new_arc(tactical_doc=_new_tactical)
                                if _spg_warnings:
                                    _warn_str = _spg.format_warnings(_spg_warnings)
                                    self.ctx.ui.log(f"      {_warn_str}")
                                    self.ctx.audit_event("v66_semantic_plot_warning", _warn_str[:300])
                            except Exception as e:  # [V64.P4] IMPORTANT: plot dedup check — log but continue
                                self.ctx.audit_event("semantic_plot_check_failed", str(e)[:100])

                        # [V63] constraint_summary 저장
                        if constraint_block:
                            _constraint_lines = constraint_block.strip().split("\n")
                            _must_not = [
                                ln.strip()
                                for ln in _constraint_lines
                                if "금지" in ln or "MUST NOT" in ln or "절대" in ln
                            ]
                            refined_arc["constraint_summary"] = "\n".join(_must_not[:10]) if _must_not else ""

                        refined_arc = validate_arc(refined_arc)  # [Step2] Pydantic ingress+egress
                        all_refined_arcs.append(refined_arc)
                        _st_snapshot = None  # [V70] Director PASS 확정 — 스냅샷 불필요
                        self.ctx.cumulative_state_cache = None
                        self.ctx.cumulative_state_cache_key = 0

                        ### [0124 핵심 4] DB 원자적 커밋
                        try:
                            self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
                            await self.ctx.safe_commit_async()
                        except Exception as commit_err:
                            self.ctx.ui.log(f"🚨 [DB] Arc {global_arc_no} 저장 실패: {commit_err}")
                            self.ctx.audit_event(
                                "db_commit_error",
                                "arc save failed in async",
                                {"arc_no": global_arc_no, "error": str(commit_err)},
                            )
                            all_refined_arcs.pop()
                            attempt += 1
                            continue

                        constraint_db.update_arc_state(refined_arc)
                        self.ctx.ui.log(
                            f"      🔒 [V49.4] ConstraintDB 업데이트 완료 (총 {len(constraint_db.arc_states)}개 Arc)"
                        )

                        last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, global_arc_no + 1)
                        current_ep_start = refined_arc["ep_end"] + 1
                        passed = True

                        # [V55.3] PassRateMonitor: Stage 2 성공 기록
                        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
                            try:
                                self.ctx.pass_rate_monitor.record_attempt(
                                    stage=2,
                                    episode=global_arc_no,
                                    arc=global_arc_no,
                                    attempt_num=attempt + 1,
                                    success=True,
                                    generation_method=generation_method,
                                )
                            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                                logging.debug(f"[SILENT] metrics (success): {e}")
                                pass

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
                                pass

                        if self.ctx.stage2_optimizer:
                            try:
                                self.ctx.stage2_optimizer.failure_memory.clear_arc_failures(global_arc_no)
                                self.ctx.ui.log(f"      ✨ [V60.25] Arc {global_arc_no} 최종 성공 - 실패 메모리 클리어")
                            except Exception as e:  # [V64.P4] OPTIONAL: optimizer memory clear
                                logging.debug(f"[SILENT] optimizer memory clear: {e}")
                                pass

                        # [V65] PerfTimer: Arc 완료 시 요약 로그
                        try:
                            self.ctx.perf_timer.log_summary()
                            self.ctx.perf_timer.reset()
                        except Exception:
                            pass

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
                                                if _as.get("npc_status"):
                                                    _parts.append(
                                                        "NPC: "
                                                        + ", ".join(
                                                            f"{n}({v.get('status', '')})"
                                                            for n, v in _as["npc_status"].items()
                                                        )
                                                    )
                                                if _as.get("world_changes"):
                                                    _parts.append(
                                                        "세계변화: "
                                                        + "; ".join(str(w) for w in _as["world_changes"][:5])
                                                    )
                                                if _as.get("resolved_plots"):
                                                    _parts.append(
                                                        "해결플롯: "
                                                        + "; ".join(str(p) for p in _as["resolved_plots"][:5])
                                                    )
                                                if _as.get("active_plots"):
                                                    _parts.append(
                                                        "진행플롯: "
                                                        + "; ".join(str(p) for p in _as["active_plots"][:5])
                                                    )
                                                if _as.get("destroyed_entities"):
                                                    _parts.append(
                                                        "파괴: "
                                                        + "; ".join(str(d) for d in _as["destroyed_entities"][:3])
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
                                        self.ctx.current_project.save_v20_anchor(
                                            f"volume_summary_{_vol_no}", _vol_result
                                        )
                                        logging.info(f"📖 [V68] 볼륨 {_vol_no} 요약 저장 완료 ({len(_vol_result)}자)")

                                        # [V68] 시리즈 요약 갱신 — 기존 + 새 볼륨 통합
                                        try:
                                            _existing_series = (
                                                self.ctx.current_project.load_v20_anchor("series_summary") or ""
                                            )
                                            if isinstance(_existing_series, dict):
                                                _existing_series = _existing_series.get("summary", "") or str(
                                                    _existing_series
                                                )
                                            _series_prompt = (
                                                "아래는 기존 시리즈 요약과 새 볼륨 요약입니다.\n"
                                                "이를 통합하여 전체 시리즈 요약을 1000자 이내로 갱신하세요.\n"
                                                "핵심 사건, 주요 인물 변화, 세계 상태 변화에 집중하세요.\n\n"
                                                f"기존 시리즈 요약:\n{_existing_series or '(아직 없음)'}\n\n"
                                                f"새 볼륨 {_vol_no} 요약:\n{_vol_result}\n\n"
                                                "갱신된 시리즈 요약:"
                                            )
                                            _series_result = self.ctx.agents["director"].ask(
                                                _series_prompt, temperature=0.2
                                            )
                                            if (
                                                _series_result
                                                and isinstance(_series_result, str)
                                                and len(_series_result) > 20
                                            ):
                                                self.ctx.current_project.save_v20_anchor(
                                                    "series_summary", _series_result
                                                )
                                                logging.info(
                                                    f"📚 [V68] 시리즈 요약 갱신 완료 ({len(_series_result)}자)"
                                                )
                                        except Exception as _se:
                                            logging.warning(f"⚠️ [V68] 시리즈 요약 갱신 실패 (비차단): {_se}")
                                    else:
                                        logging.info("⚠️ [V68] 볼륨 요약 LLM 응답 불충분 — 건너뜀")
                            except Exception as _ve:
                                logging.warning(f"⚠️ [V68] 볼륨 요약 생성 실패 (비차단): {_ve}")

                        break
                    else:
                        # [V60.77] Director REJECT
                        base_feedback = audit.get("re_slice_instruction") or "밀도 보강 필요"
                        reject_reason = audit.get("reason") or "사유 미상"

                        adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
                        intensity_guide = (
                            f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
                        )

                        self.ctx.ui.log(f"      🎬 [Director REJECT] {reject_reason[:100]}")
                        self.ctx.ui.log(f"      📋 피드백: {base_feedback[:100]}")

                        # [V70] StateTracker 롤백: FourPhase PASS → Director REJECT 시 팬텀 데이터 제거
                        if _st_snapshot and generation_method == "four_phase":
                            try:
                                _st = self.ctx.state_tracker
                                for _k, _v in _st_snapshot.items():
                                    setattr(_st, _k, _v)
                                logging.warning("🔄 [V70] StateTracker 롤백 완료 (Director REJECT)")
                            except Exception as _rb_err:
                                logging.warning(f"⚠️ [V70] StateTracker 롤백 실패 (비차단): {_rb_err}")
                            _st_snapshot = None

                        if not use_analyst_fallback:
                            director_feedback_for_fourphase = f"""[Director REJECT 사유]
{reject_reason}

[수정 지시]
{base_feedback}

[재시도 가이드]
{intensity_guide}
"""
                            refined_arc = None
                            self.ctx.ui.log(f"      🔄 [V60.77] Director 피드백 → FourPhase 대면 {attempt + 2}/3")
                        else:
                            current_feedback = f"{base_feedback}{intensity_guide}"
                            refined_arc = None
                            self.ctx.ui.log(
                                f"      ❌ [V60.77] Analyst 최후 기회도 REJECT → Arc {global_arc_no} 최종 실패"
                            )

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
                                )
                            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                                logging.debug(f"[SILENT] metrics (reject): {e}")
                                pass

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
                                pass

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
                                pass

                    attempt += 1

                if not passed:
                    self.ctx.ui.log(f"🚨 [Critical] Arc {global_arc_no} 최종 설계 실패.")
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

                    arc_rejects = [
                        r
                        for r in self.ctx.stage_rejection_history
                        if r.get("stage") == 2 and r.get("arc_no") == global_arc_no
                    ]
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
                            str(current_constraints)[:2000] if current_constraints else "없음",
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

                    with open(failure_report_path, "w", encoding="utf-8") as f:
                        f.write(report_content)

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
                        print("   [4] 수동 개입 (리포트 확인 후 재시도)")
                        user_choice = input("   선택 (기본: 2): ").strip()

                        if user_choice == "1":
                            self.ctx.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                            _skip_ep = (
                                arcs_source[global_arc_no - 1].get("ep_count", 5)
                                if global_arc_no <= len(arcs_source)
                                else 5
                            )  # [V70] 하드코딩 5 → 실제 ep_count
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
                            print("   💡 문제가 된 아이템이나 표현을 확인 후, 아래 옵션을 선택하세요.")
                            manual_input = (
                                input("   준비되면 [Enter]로 재시도, 'skip'으로 건너뛰기, 'quit'으로 중단: ")
                                .strip()
                                .lower()
                            )
                            if manual_input == "skip":
                                self.ctx.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                                _skip_ep2 = (
                                    arcs_source[global_arc_no - 1].get("ep_count", 5)
                                    if global_arc_no <= len(arcs_source)
                                    else 5
                                )  # [V70]
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
        self.ctx.write_audit_summary("stage2_complete")
        input("\n[Enter] 메뉴로 돌아가기")

    # ═══════════════════════════════════════════════════════════════════════
    # Stage 2 헬퍼 메서드
    # ═══════════════════════════════════════════════════════════════════════

    def _preflight_state_setup(
        self,
        *,
        all_refined_arcs: list,
        arcs_source: list,
        arc_idx: int,
        lack_report: dict,
        grand_obj: str,
        global_arc_no: int,
        constraint_db,
    ) -> dict:
        """[4-R3-a] Pre-attempt-loop state initialization.

        Computes arc_drive, preflight analysis (parallel), constraint block,
        and initializes attempt loop variables.

        Returns dict of computed values for the attempt loop.
        """
        ### [V66.1] arc_drive + preflight 병렬 실행 (ThreadPoolExecutor)
        # arc_drive: LLM 호출 (lack_report 의존, lack_report는 위에서 즉시 완료)
        # preflight: LLM 호출 (독립적 — all_refined_arcs만 사용)
        # 두 호출이 독립적이므로 병렬 실행하여 15-30s 절감

        def _compute_arc_drive() -> dict:
            """Weaver 욕망 드라이브 생성 (LLM)"""
            try:
                return self.ctx.agents["weaver"].generate_arc_drive(
                    current_arc_dna=arcs_source[arc_idx],
                    analyst_lack_report=lack_report,
                    grand_objective=grand_obj,
                )
            except Exception as weaver_err:
                self.ctx.ui.log(f"⚠️ [Weaver] 욕망 드라이브 생성 실패: {weaver_err}")
                self.ctx.audit_event(
                    "weaver_error",
                    "generate_arc_drive failed",
                    {"arc_no": global_arc_no, "error": str(weaver_err)},
                )
                return {"desire_vector": "생성 실패", "status": "error"}

        def _compute_preflight() -> tuple:
            """Preflight 분석 (LLM) — 결과를 attempt 루프에서 재사용"""
            _pf_injection = ""
            _pf_result = None
            if "preflight" in self.ctx.agents and all_refined_arcs:
                try:
                    _resolved_plots = ""
                    if self.ctx.state_tracker:
                        _resolved_plots = self.ctx.state_tracker.get_resolved_plots_summary()
                    _pf_result = self.ctx.agents["preflight"].analyze(
                        all_refined_arcs, resolved_plots_summary=_resolved_plots
                    )
                    if _pf_result:
                        _pf_injection = self.ctx.agents["preflight"].generate_analyst_injection(_pf_result)
                except Exception as pf_err:
                    logging.info(f"⚠️ [Preflight] 스킵: {str(pf_err)[:50]}")
            return _pf_injection, _pf_result

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
            _fut_drive = _parallel_exec.submit(_compute_arc_drive)
            _fut_preflight = _parallel_exec.submit(_compute_preflight)
            arc_drive = _fut_drive.result()
            _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result()

        if _cached_preflight_result:
            logging.info("✅ [V66.1] arc_drive + preflight 병렬 완료")
            logging.info(f"- 아이템 타임라인: {len(_cached_preflight_result.get('item_timeline', []))}개")
            logging.info(f"- 금지 사항: {len(_cached_preflight_result.get('absolute_prohibitions', []))}개")
            logging.info(f"- 관계 맵: {len(_cached_preflight_result.get('relationship_map', {}))}명")

        passed = False
        current_feedback = ""

        # [V49.4] Pre-Generation Constraint 생성
        constraint_block = constraint_db.generate_constraint_block(global_arc_no)
        if constraint_block:
            self.ctx.ui.log(f"      🔒 [V49.4] Arc {global_arc_no} 제약 조건 주입됨")

        # [V60.11] ConstraintCompiler로 구조화된 체크리스트 생성
        if self.ctx.constraint_compiler and all_refined_arcs:
            try:
                state_result = None
                if "state_extractor" in self.ctx.agents:
                    try:
                        arc_count = len(all_refined_arcs)
                        if (
                            self.ctx.cumulative_state_cache is not None
                            and self.ctx.cumulative_state_cache_key == arc_count
                        ):
                            state_result = self.ctx.cumulative_state_cache
                        else:
                            state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
                            self.ctx.cumulative_state_cache = state_result
                            self.ctx.cumulative_state_cache_key = arc_count
                    except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
                        self.ctx.ui.log(
                            f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}"
                        )
                        self.ctx.audit_event("critical_state_extraction_failed", str(e)[:200])

                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                compiled_constraints = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                constraint_block = compiled_constraints + "\n\n" + (constraint_block or "")
                self.ctx.ui.log("      📋 [V60.11] ConstraintCompiler 체크리스트 생성 완료")

                # [V66] SemanticPlotGuard — 중앙 인스턴스 사용
                if _resolved and len(_resolved) >= 2 and getattr(self.app, "semantic_plot_guard", None):
                    try:
                        self.ctx.semantic_plot_guard.index_resolved_plots(_resolved)
                    except Exception as e:  # [V64.P4] SPG init — OPTIONAL
                        self.ctx.audit_event("semantic_plot_guard_index_failed", str(e)[:100])
            except Exception as cc_err:
                self.ctx.audit_event("v60_11_constraint_compiler_error", str(cc_err)[:100])

        # [V60.77] FourPhase-Director 대면 루프
        attempt = 0
        max_fourphase_attempts = 5  # [V62.4]
        max_attempts = max_fourphase_attempts + 1
        director_feedback_for_fourphase = ""
        use_analyst_fallback = False

        _st_snapshot = None  # [V70] StateTracker 롤백용 스냅샷

        return {
            "arc_drive": arc_drive,
            "cached_preflight_injection": _cached_preflight_injection,
            "cached_preflight_result": _cached_preflight_result,
            "passed": passed,
            "current_feedback": current_feedback,
            "constraint_block": constraint_block,
            "attempt": attempt,
            "max_fourphase_attempts": max_fourphase_attempts,
            "max_attempts": max_attempts,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "use_analyst_fallback": use_analyst_fallback,
            "st_snapshot": _st_snapshot,
        }

    def _preflight_arc_analysis(
        self,
        *,
        attempt: int,
        current_feedback: str,
        constraint_block: str,
        last_refined_context: str,
        all_refined_arcs: list,
        protagonist_name: str,
        global_arc_no: int,
        cached_preflight_injection: str,
        cached_preflight_result,
    ) -> dict:
        """[4-R3-b] Per-attempt context building and weapons preparation.

        Builds enhanced_context (constraints, optimizer, V51, focus mode,
        stage 3->2 feedback) and prepares analyst weapons (preflight cache,
        constraint compiler, entity registry).

        Returns dict of analysis results for the generation phase.
        """
        from modules.core.constants import Emojis, RetryLimits
        from modules.core.spinners import V50_MODULES_AVAILABLE

        self.ctx.ui.log(
            f"   {Emojis.BRAIN} [Arc {global_arc_no}] 전술 설계 중 (시도 {attempt + 1}/{RetryLimits.ANALYST_MAX_ATTEMPTS})..."
        )

        recent_patterns = [
            a.get("hybrid_composition", {}).get("primary")
            for a in all_refined_arcs
            if a.get("hybrid_composition", {}).get("primary")
        ]

        # [V49.4] 제약 블록을 prev_arc_context에 주입
        enhanced_context = last_refined_context
        if constraint_block:
            enhanced_context = constraint_block + "\n" + last_refined_context

        # [V60.25] Stage 2 Optimizer 주입
        if self.ctx.stage2_optimizer:
            try:
                optimizer_prompt = self.ctx.stage2_optimizer.generate_optimized_prompt(
                    prev_arcs=all_refined_arcs,
                    protagonist_name=protagonist_name or "주인공",
                    include_examples=(attempt == 0),
                )
                enhanced_context = optimizer_prompt + "\n\n" + enhanced_context
                if attempt == 0:
                    self.ctx.ui.log("      ⚡ [V60.25] Stage 2 Optimizer 프롬프트 주입 완료")
            except Exception as opt_err:
                self.ctx.audit_event("v60_25_optimizer_error", str(opt_err)[:100])

        # [V60.21] Focus Mode
        is_retry = attempt > 0 and current_feedback

        # [V51] Analyst 지능 향상 주입
        v51_analyst_injection = ""
        if V50_MODULES_AVAILABLE and not is_retry:
            try:
                if self.ctx.quality_amplifier:
                    analyst_constraints = self.ctx.quality_amplifier.generate_analyst_constraints(
                        arc_num=global_arc_no, prev_arcs=all_refined_arcs
                    )
                    v51_analyst_injection += analyst_constraints + "\n\n"

                if self.ctx.agent_intelligence:
                    intel_prompt = self.ctx.agent_intelligence.get_analyst_enhancement(
                        arc_num=global_arc_no, prev_arcs=all_refined_arcs
                    )
                    v51_analyst_injection += intel_prompt + "\n\n"

                if self.ctx.failure_learner:
                    learned_constraints = self.ctx.failure_learner.generate_constraint_prompt(stage=2)
                    if learned_constraints:
                        v51_analyst_injection += learned_constraints

                if self.ctx.constitutional_checker:
                    constitutional_prompt = self.ctx.constitutional_checker.get_full_injection(
                        stage=2, context={"prev_arcs": all_refined_arcs, "feedback": current_feedback}
                    )
                    v51_analyst_injection = constitutional_prompt + "\n\n" + v51_analyst_injection

                if v51_analyst_injection:
                    enhanced_context = v51_analyst_injection + "\n\n" + enhanced_context
                    self.ctx.ui.log("      🧠 [V51+V55.2] Analyst 지능 향상 + Constitutional 주입 완료")
            except Exception as v51_err:
                self.ctx.ui.log(f"      ⚠️ [V51] Analyst 향상 실패: {v51_err}")

        # [V60.21] Focus Mode: 재시도 시 컨텍스트 대폭 축소
        if is_retry:
            minimal_prev_context = self.ctx.build_minimal_arc_context(all_refined_arcs, protagonist_name or "주인공")
            enhanced_context = f"{current_feedback}\n\n{minimal_prev_context}"
            context_size = len(enhanced_context)
            self.ctx.ui.log(f"      📢 [V60.21] Focus Mode 활성화 - 컨텍스트 {context_size}자 (최소화)")

        # [V60.9] Stage 3→2 역방향 피드백 주입
        try:
            if self.ctx.stage_rejection_history:
                arc_stage3_failures = [
                    r
                    for r in self.ctx.stage_rejection_history
                    if r.get("stage") == 3 and r.get("arc_no") == global_arc_no
                ]
                if len(arc_stage3_failures) >= 3:
                    reverse_feedback_3to2 = self.ctx.generate_reverse_feedback_stage3_to_2(
                        architect_failures=arc_stage3_failures, arc_no=global_arc_no
                    )
                    if reverse_feedback_3to2:
                        stage3_warning = "\n\n🔄 [V60.9 Stage 3→2 역방향 피드백]\n"
                        stage3_warning += f"이 Arc(#{global_arc_no})에서 Blueprint 설계가 {len(arc_stage3_failures)}회 실패했습니다.\n"
                        stage3_warning += "Arc 구조 자체에 문제가 있을 수 있습니다.\n\n"
                        stage3_warning += f"[Blueprint 실패 패턴 분석]\n{reverse_feedback_3to2}\n"
                        enhanced_context = stage3_warning + "\n" + enhanced_context
                        self.ctx.ui.log(
                            f"      🔄 [V60.9] Stage 3→2 역방향 피드백 주입 ({len(arc_stage3_failures)}회 실패 기반)"
                        )
        except Exception as rf32_err:
            self.ctx.audit_event(
                "v60_9_stage3to2_error", "stage 3→2 reverse feedback failed", {"error": str(rf32_err)[:100]}
            )

        # ═══════════════════════════════════════════════════════════════
        # [V60.36] Analyst 강화 - Director 검수 통과를 위한 무장
        # ═══════════════════════════════════════════════════════════════
        refined_arc = None
        generation_method = "analyst"
        analyst_weapons = {}

        logging.info(f"\n      {'=' * 60}")
        logging.info(f"[V60.36] Arc {global_arc_no} 생성 시작 (attempt {attempt + 1})")
        logging.info(f"{'=' * 60}")

        # ─────────────────────────────────────────────────────────────
        # [무기 #1] Preflight 분석 — [V66.1] 병렬 실행 캐시 재사용
        # ─────────────────────────────────────────────────────────────
        preflight_injection = cached_preflight_injection
        if cached_preflight_result:
            analyst_weapons["preflight"] = cached_preflight_result

        # ─────────────────────────────────────────────────────────────
        # [무기 #2] ConstraintCompiler
        # ─────────────────────────────────────────────────────────────
        constraint_block = ""
        entity_registry_for_director = None
        if self.ctx.constraint_compiler and all_refined_arcs:
            try:
                logging.info("📋 [무기 #2] ConstraintCompiler 컴파일 중...")
                state_result = None
                if "state_extractor" in self.ctx.agents:
                    arc_count = len(all_refined_arcs)
                    if self.ctx.cumulative_state_cache is not None and self.ctx.cumulative_state_cache_key == arc_count:
                        state_result = self.ctx.cumulative_state_cache
                    else:
                        state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
                        self.ctx.cumulative_state_cache = state_result
                        self.ctx.cumulative_state_cache_key = arc_count
                    entity_registry_for_director = state_result.get("entity_registry") if state_result else None
                    if entity_registry_for_director:
                        entity_registry_for_director = self.ctx.fix_entity_registry_protagonist(
                            entity_registry_for_director, protagonist_name
                        )
                        logging.info("🏷️ [V61] Entity Registry 추출됨 (Director용)")
                _resolved = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
                constraint_block = self.ctx.constraint_compiler.compile(
                    all_refined_arcs, state_result, resolved_plots=_resolved
                )
                analyst_weapons["constraints"] = constraint_block
                logging.info(f"✅ [Constraints] 제약 블록 생성 완료 ({len(constraint_block)}자)")
            except Exception as cc_err:
                logging.info(f"⚠️ [Constraints] 스킵: {str(cc_err)[:50]}")

        return {
            "enhanced_context": enhanced_context,
            "recent_patterns": recent_patterns,
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "preflight_injection": preflight_injection,
            "constraint_block": constraint_block,
            "entity_registry_for_director": entity_registry_for_director,
        }

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

    def _is_tactical_doc_duplicate(self, candidate_text: str, reference_texts: list, threshold: float = 0.98) -> bool:
        """[V64.P3] 전술서 중복 감지"""
        import hashlib
        from difflib import SequenceMatcher

        candidate = self._normalize_tactical_text(candidate_text)
        if not candidate:
            return False
        recent_refs = reference_texts[-3:] if len(reference_texts) > 3 else reference_texts
        candidate_hash = hashlib.md5(candidate.encode("utf-8")).hexdigest()
        ref_hashes = set()
        for ref_text in recent_refs:
            ref = self._normalize_tactical_text(ref_text)
            if not ref:
                continue
            ref_hashes.add(hashlib.md5(ref.encode("utf-8")).hexdigest())
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
        from modules.core.constants import AIModels  # [V65] SSOT

        _SUMMARY_MODEL = AIModels.SUMMARY_MODEL

        beats = refined_arc.get("beat_sequence", [])
        ep_count = refined_arc.get("ep_count", 0)

        if not isinstance(beats, list) or len(beats) < max(3, ep_count):
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 수가 화수보다 부족",
                "feedback": "각 화마다 고유 사건을 분리해 비트를 늘려라.",
            }

        normalized = [self._normalize_flow_text(b) for b in beats if isinstance(b, str)]
        if len(normalized) < 2:
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 내용이 비어 있음",
                "feedback": "각 화의 비트를 구체적 사건/행동으로 작성하라.",
            }

        # 1) 서사 폭주 감지
        word_counts = [len(t.split()) for t in normalized if t]
        avg_words = sum(word_counts) / max(1, len(word_counts))
        if avg_words < 6 or any(c < 4 for c in word_counts):
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트가 과도하게 축약됨",
                "feedback": "각 화마다 사건/행동/반응을 최소 1개씩 명시하라.",
            }

        # 2) [V60.15] 진짜 서사 구조 분석
        try:
            from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer

            analyzer = NarrativeStructureAnalyzer(client=self.ctx.sys.api_client, model=_SUMMARY_MODEL)

            result = analyzer.analyze(beats[:5])

            if result.get("status") == "STAGNATION":
                stagnation_type = result.get("stagnation_type", "unknown")
                pattern = result.get("pattern", "")
                recommendation = result.get("recommendation", "")

                logging.info(f"🔍 [V60.15] 진짜 서사 정체 감지: {stagnation_type}")
                logging.info(f"패턴: {pattern}")

                return {
                    "status": "REJECT",
                    "reason": f"서사 정체 감지: {stagnation_type} 반복 ({pattern})",
                    "feedback": recommendation,
                }

            if result.get("status") == "WARNING":
                warning_type = result.get("warning_type", "")
                pattern = result.get("pattern", "")
                logging.info(f"⚠️ [V60.15] 서사 경고: {warning_type} - {pattern}")

            diversity = result.get("diversity_score", 1.0)
            if diversity < 0.6:
                logging.info(f"📊 [V60.15] 서사 다양성: {diversity:.0%} (개선 권장)")

            return {"status": "PASS", "diversity_score": diversity}

        except ImportError:
            logging.warning("⚠️ [V60.15] NarrativeStructureAnalyzer 로드 실패, 폴백")
            return self._stage2_flow_guard_legacy(normalized)
        except Exception as e:
            logging.warning(f"⚠️ [V60.15] 서사 분석 오류 (비차단): {e}")
            return {"status": "PASS", "fallback": True}

    def _stage2_flow_guard_legacy(self, normalized: str) -> dict:
        """[V60.15] 레거시 Flow Guard (폴백용)"""

        def jaccard(a, b) -> float:
            sa, sb = set(a.split()), set(b.split())
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        stagnation_hits = 0
        for i in range(1, len(normalized)):
            sim = jaccard(normalized[i - 1], normalized[i])
            if sim >= 0.85:
                stagnation_hits += 1

        if stagnation_hits >= 3:
            return {
                "status": "REJECT",
                "reason": "서사 정체 감지: 유사 비트가 연속 반복",
                "feedback": "연속 회차의 사건/공간/행동을 분리하여 변주하라.",
            }

        return {"status": "PASS"}
