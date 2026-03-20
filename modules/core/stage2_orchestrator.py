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
from typing import Any, Literal, NotRequired, TypedDict

from modules.core.constants import VolumeSettings, smart_truncate
from modules.core.stage2_contracts import TACTICAL_DOC_DUPLICATE_THRESHOLD

DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC


class Stage2BootstrapPayload(TypedDict):
    ready: bool
    bible_root: NotRequired[dict[str, Any]]
    arcs_source: NotRequired[list[Any]]
    volumes_strategy: NotRequired[list[Any]]
    protagonist_name: NotRequired[str | None]
    grand_obj: NotRequired[str]
    all_refined_arcs: NotRequired[list[Any]]
    done_count: NotRequired[int]
    total_count: NotRequired[int]
    target_limit: NotRequired[int]
    constraint_db: NotRequired[Any]
    genre_for_tracker: NotRequired[str]
    last_refined_context: NotRequired[str]
    sem: NotRequired[asyncio.Semaphore]


class Stage2BatchEnrichmentPayload(TypedDict):
    action: Literal["stop", "continue"]
    last_refined_context: str
    enriched_batch: list[tuple[int, dict[str, Any]]]


class Stage2FinalizeTransitionPayload(TypedDict):
    action: Literal["break", "retry", "next"]
    last_refined_context: str
    current_ep_start: int
    current_feedback: str
    director_feedback_for_fourphase: str
    st_snapshot: Any
    previous_attempt: dict[str, Any] | None


class Stage2ArcFailurePayload(TypedDict):
    action: Literal["skip", "retry", "abort"]
    current_ep_start: NotRequired[int]
    current_feedback: NotRequired[str]
    constraint_block: NotRequired[str]


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

    def _fit_prompt_text(self, value: object, max_chars: int, head_ratio: float = 0.55) -> str:
        text = "" if value is None else str(value)
        if len(text) <= max_chars:
            return text
        head_chars = max(200, min(max_chars - 50, int(max_chars * head_ratio)))
        return smart_truncate(text, max_chars=max_chars, head_chars=head_chars)

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

    def _set_agent_telemetry_context(self, *, ep_num: int | None = None) -> None:
        """[LOG-Phase2] BaseAgent llm_calls stage/ep 메타데이터 주입."""
        agents = getattr(self.ctx, "agents", None)
        if not isinstance(agents, dict):
            return

        _ep_value = None
        if ep_num is not None:
            try:
                _ep_value = max(0, int(ep_num))
            except (TypeError, ValueError):
                _ep_value = None

        # 서브 에이전트 포함 전체 순회 (four_phase 내부 인스턴스는 agents dict와 별개)
        _all_agents = list(agents.values())
        _four_phase = agents.get("four_phase")
        if _four_phase is not None:
            for _sub_name in ("preflight", "ensemble", "validator"):
                _sub = getattr(_four_phase, _sub_name, None)
                if _sub is not None:
                    _all_agents.append(_sub)

        for agent in _all_agents:
            if agent is None:
                continue
            try:
                setattr(agent, "_current_stage", 2)
            except Exception:
                pass
            if _ep_value is not None:
                try:
                    setattr(agent, "_current_ep_num", _ep_value)
                except Exception:
                    pass

    def _compose_rejection_pattern_feedback(self, arc_rejections: list, global_arc_no: int) -> str:
        """Return retry-pattern feedback or an explicit diagnostic fallback."""
        if not arc_rejections:
            return ""

        callback = getattr(self.ctx, "analyze_rejection_pattern_v60", None)
        if callable(callback):
            try:
                return callback(arc_rejections, global_arc_no) or ""
            except Exception as exc:
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "stage2_rejection_pattern_error",
                        "analyze_rejection_pattern_v60 callback failed",
                        {"arc_no": global_arc_no, "error": str(exc)[:120]},
                    )
                reason_suffix = f"callback_error={type(exc).__name__}"
            else:
                reason_suffix = ""
        else:
            reason_suffix = "callback_missing"

        reason_counts = {}
        specific_issues = []
        for reject in arc_rejections:
            reason = str(reject.get("reason", "사유 미상") or "사유 미상")[:120]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            issue = str(reject.get("specific_issue", "") or "").strip()
            if issue and issue not in specific_issues:
                specific_issues.append(issue[:120])

        top_reasons = sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
        lines = [
            "",
            "=" * 60,
            f"⚠️ [V60.10] Arc {global_arc_no} 반복 REJECT 진단",
            "=" * 60,
            "retry pattern helper를 사용할 수 없어 raw rejection history를 직접 요약합니다.",
        ]
        if reason_suffix:
            lines.append(f"진단 상태: {reason_suffix}")
        lines.append("")
        lines.append(f"📊 총 {len(arc_rejections)}회 REJECT 발생")
        for reason, count in top_reasons:
            lines.append(f"   - {reason}: {count}회")
        if specific_issues:
            lines.append("")
            lines.append("📋 반복된 구체 지시:")
            for issue in specific_issues[:3]:
                lines.append(f"   - {issue}")
        lines.append("")
        lines.append("💡 다음 재시도에서는 위 사유와 구체 지시를 Arc 설계 제약으로 직접 반영하세요.")
        lines.extend(["", "=" * 60, ""])
        return "\n".join(lines)

    def _resolve_arc_number_for_episode(self, ep_num: int) -> int:
        """Resolve manuscript frontier to an arc number even when DI callback is absent."""
        try:
            ep_num = int(ep_num)
        except (TypeError, ValueError):
            return 0
        if ep_num <= 0:
            return 0

        calc_cb = getattr(self.ctx, "calculate_arc_from_episode", None)
        if callable(calc_cb):
            try:
                resolved = int(calc_cb(ep_num))
                if resolved > 0:
                    return resolved
            except Exception as exc:
                self.ctx.ui.log(f"⚠️ [Stage2] arc mapping callback 실패 - fallback 사용: {exc}")
        else:
            self.ctx.ui.log("⚠️ [Stage2] arc mapping callback 부재 - fallback 사용")

        def _safe_int(value) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        arcs = getattr(getattr(self.ctx, "current_project", None), "arcs", None)
        if isinstance(arcs, list):
            for idx, arc in enumerate(arcs, start=1):
                if not isinstance(arc, dict):
                    continue
                ep_start = _safe_int(
                    arc.get("ep_start") or arc.get("start_ep") or arc.get("episode_start") or arc.get("start_episode")
                )
                ep_end = _safe_int(arc.get("ep_end") or arc.get("end_ep") or arc.get("episode_end"))
                if ep_start > 0 and ep_end <= 0:
                    ep_count = _safe_int(arc.get("ep_count"))
                    if ep_count > 0:
                        ep_end = ep_start + ep_count - 1
                if ep_start > 0 and ep_end > 0 and ep_start <= ep_num <= ep_end:
                    return _safe_int(arc.get("arc_no")) or idx

        return (ep_num - 1) // DEFAULT_EP_COUNT + 1

    def _bootstrap_stage2_arc_pipeline(
        self, *, target_arc_count: int | None
    ) -> Stage2BootstrapPayload:
        """Prepare Stage 2 startup state before entering batch orchestration."""
        from modules.core.constants import HUDKeys
        from modules.core.constraint_db import ConstraintDB
        from modules.core.stage0_handoff import check_plot_roadmap_ready
        from modules.domain.agents.state_tracker import StateTracker

        self.ctx.ui.log("🔞 [Stage 2] 0124 매니페스트 정합 엔진 및 멀티 공정 기동...")

        if not self.ctx.current_project.master_bible:
            self.ctx.current_project.master_bible = self.ctx.current_project.db.load_anchor("bible")
        if not self.ctx.current_project.volumes:
            self.ctx.current_project.volumes = self.ctx.current_project.db.load_anchor("volumes")

        bible_data = self.ctx.current_project.master_bible
        if not bible_data:
            self.ctx.ui.log("❌ [Stage 2] Bible 데이터를 찾을 수 없습니다. Stage 0-1을 먼저 실행하세요.")
            return {"ready": False}

        volumes_strategy = self.ctx.current_project.volumes or []
        if not volumes_strategy:
            self.ctx.ui.log("⚠️ [Notice] Volume 전략이 없습니다. 기본값으로 Arc 단계를 진행합니다.")

        bible_root = bible_data.get("MasterBible", bible_data)
        arcs_source = bible_root.get("plot_roadmap", [])
        roadmap_status = check_plot_roadmap_ready(arcs_source, source="stage2_entry")
        if not roadmap_status.ready:
            self.ctx.ui.log("❌ [Stage 2] plot_roadmap가 비어 있거나 Stage 2 준비 필드를 충족하지 않습니다.")
            if roadmap_status.warnings:
                self.ctx.ui.log("   " + "; ".join(roadmap_status.warnings[:3]))
            return {"ready": False}
        arcs_source = roadmap_status.roadmap

        protagonist_name = None
        genre = ""
        try:
            genre = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
            protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            if protagonist_name and protagonist_name != "주인공":
                self.ctx.ui.log(f"📝 [V42] 주인공 이름 락: {protagonist_name}")
        except Exception as e:
            self.ctx.ui.log(f"⚠️ [V42] 주인공 이름 추출 실패: {e}")

        project_data = bible_root.get("ProjectData", {})
        meta_info = project_data.get("MetaInfo", {}) if isinstance(project_data, dict) else {}
        grand_obj = meta_info.get("grand_objective", "천하제일") if isinstance(meta_info, dict) else "천하제일"

        all_refined_arcs = self.ctx.current_project.db.load_anchor("arcs") or []
        done_count = len(all_refined_arcs)
        total_count = len(arcs_source)

        existing_tracker_arcs = self.ctx.state_tracker_loaded_arcs or 0
        if self.ctx.state_tracker is None or existing_tracker_arcs == 0 or existing_tracker_arcs > len(all_refined_arcs):
            self.ctx.state_tracker = StateTracker(
                preset_registry=self.ctx.preset_registry,
                llm_client=self.ctx.sys.api_client,
            )
            self.ctx.state_tracker.bind_db(self.ctx.current_project.db)
            self.ctx.state_tracker.bind_world_state(getattr(self.ctx, "world_state", None))
            existing_tracker_arcs = 0
            saved_financial_registry = self.ctx.current_project.load_v20_anchor("financial_registry", default=None)
            if saved_financial_registry:
                self.ctx.state_tracker.import_financial_registry(saved_financial_registry)

        new_arcs_to_load = all_refined_arcs[existing_tracker_arcs:]
        genre_for_tracker = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
        self.ctx.state_tracker.full_extract_from_arcs(new_arcs_to_load, genre=genre_for_tracker)
        self.ctx.state_tracker_loaded_arcs = len(all_refined_arcs)

        if genre_for_tracker == "investment" and self.ctx.state_tracker.financial_number_registry:
            self.ctx.current_project.save_v20_anchor(
                "financial_registry",
                self.ctx.state_tracker.export_financial_registry(),
            )

        if self.ctx.state_tracker.npc_registry:
            dead_count = sum(1 for info in self.ctx.state_tracker.npc_registry.values() if info.get("status") == "dead")
            total_npcs = len(self.ctx.state_tracker.npc_registry)
            loaded_msg = f"(신규 {len(new_arcs_to_load)}개)" if new_arcs_to_load else "(캐시 재사용)"
            self.ctx.ui.log(
                f"      🧠 [V62.5] StateTracker: NPC {total_npcs}명 로드 (사망: {dead_count}명) {loaded_msg}"
            )

        existing_ms_max_ep = (
            self.ctx.get_max_episode_from_manuscripts()
            if callable(getattr(self.ctx, "get_max_episode_from_manuscripts", None))
            else 0
        )
        if existing_ms_max_ep > 0:
            skip_arc_no = self._resolve_arc_number_for_episode(existing_ms_max_ep)
            if skip_arc_no > done_count:
                self.ctx.ui.log(f"📚 [Manuscript Detected] 기존 원고 {existing_ms_max_ep}화까지 발견")
                self.ctx.ui.log(
                    f"⚠️  [Warning] Arc {skip_arc_no}까지 필요하지만 Arc {done_count}까지만 DB에 존재합니다."
                )
                self.ctx.ui.log(f"🔕 [Info] Arc {done_count + 1}부터 단계를 시작합니다. (원고→Arc 역추적 필요)")

        if done_count >= total_count:
            self.ctx.ui.log("✅ 모든 아크 단계가 이미 완료되었습니다.")
            return {"ready": False}

        self.ctx.ui.log(f"📤 현재 단계 완료: {done_count} / {total_count} 아크")
        self.ctx.ui.log("🔕 Tip: 결과를 직접 보기 위해 1~10개(권장 2개 내외) 진행을 권장합니다.")

        if target_arc_count is not None:
            target_limit = min(done_count + target_arc_count, total_count)
        else:
            default_limit = min(done_count + 5, total_count)
            if callable(getattr(self.ctx, "get_int_input", None)):
                target_limit = self.ctx.get_int_input(
                    f"🎛 몇 번 아크까지 단계하시겠습니까? (현재 {done_count + 1} ~ 최대 {total_count}): ",
                    default=default_limit,
                    min_val=done_count + 1,
                    max_val=total_count,
                )
            else:
                target_limit = default_limit
        target_limit = max(done_count + 1, min(target_limit, total_count))

        constraint_db = ConstraintDB(self.ctx.current_project)
        self.ctx.ui.log(f"📝 [V49.4] ConstraintDB 초기화 완료 (기존 Arc: {len(constraint_db.arc_states)}개)")

        self.ctx.cumulative_state_cache = None
        self.ctx.cumulative_state_cache_key = None

        return {
            "ready": True,
            "bible_root": bible_root,
            "arcs_source": arcs_source,
            "volumes_strategy": volumes_strategy,
            "protagonist_name": protagonist_name,
            "grand_obj": grand_obj,
            "all_refined_arcs": all_refined_arcs,
            "done_count": done_count,
            "total_count": total_count,
            "target_limit": target_limit,
            "constraint_db": constraint_db,
            "genre_for_tracker": genre_for_tracker,
            "last_refined_context": "",
            "sem": asyncio.Semaphore(5),
        }

    async def _run_stage2_batch_enrichment(
        self,
        *,
        batch_start: int,
        batch_end: int,
        arcs_source: list,
        all_refined_arcs: list,
        last_refined_context: str,
        total_count: int,
        sem: asyncio.Semaphore,
    ) -> Stage2BatchEnrichmentPayload:
        """Run Stage 2 batch enrichment, sanitize results, and recover failed items."""
        from modules.core.constants import RecoveryLimits
        from modules.core.spinners import StageSpinner
        import time as _time_mod

        with StageSpinner(2, f"Batch {batch_start + 1}~{batch_end} batch enrich") as spinner:
            self.ctx.ui.log(f"[Batch] {batch_start + 1}~{batch_end} range enrich start")

            if callable(getattr(self.ctx, "generate_arc_context_v60", None)):
                last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)
            if all_refined_arcs:
                self.ctx.ui.log(f"      [V60.10] StateExtractor: {len(all_refined_arcs)} arcs extracted")

            enrich_done = 0
            enrich_total = batch_end - batch_start
            batch_ep_estimate = 1 if not all_refined_arcs else max(1, all_refined_arcs[-1].get("ep_end", 0) + 1)
            self._set_agent_telemetry_context(ep_num=batch_ep_estimate)

            async def throttled_enrich(idx):
                nonlocal enrich_done
                async with sem:
                    prev_b = arcs_source[idx - 1] if idx > 0 else None
                    curr_b = arcs_source[idx]
                    bid = curr_b.get("block_id", f"Block {idx + 1}")
                    self.ctx.ui.log(f"      [Enrich] {bid} task start")
                    next_b_safe = (
                        {
                            "block_id": arcs_source[idx + 1].get("block_id", f"Block {idx + 2}"),
                            "title": arcs_source[idx + 1].get("title", "untitled"),
                        }
                        if idx < total_count - 1
                        else {"title": "final block"}
                    )
                    result = await self.ctx.agents["analyst"].enrich_raw_block_async(
                        curr_b, prev_b, next_b_safe, [], transfused_history=last_refined_context
                    )
                    enrich_done += 1
                    spinner.update_detail(f"Batch {batch_start + 1}~{batch_end} LLM enrich ({enrich_done}/{enrich_total})")
                    self.ctx.ui.log(f"      [Enrich] {bid} task done ({enrich_done}/{enrich_total})")
                    return result

            enrichment_tasks = [throttled_enrich(i) for i in range(batch_start, batch_end)]
            spinner.update_detail(f"Batch {batch_start + 1}~{batch_end} LLM enrich in progress (0/{enrich_total})...")
            enrich_phase_t0 = _time_mod.time()
            enriched_batch = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            enrich_phase_elapsed = _time_mod.time() - enrich_phase_t0
            self.ctx.ui.log(
                f"      [Enrich Phase] Batch {batch_start + 1}~{batch_end} completed: {enrich_phase_elapsed:.1f}s ({enrich_total} items)"
            )

        indexed_batch = []
        failed_indices = []
        for idx, item in enumerate(enriched_batch):
            source_arc_idx = batch_start + idx
            if isinstance(item, Exception):
                self.ctx.ui.log(f"[Enrich] parallel task failed (idx={source_arc_idx}): {item}")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("enrich_error", "batch enrich failed", {"error": str(item), "arc_idx": source_arc_idx})
                failed_indices.append(source_arc_idx)
                continue
            if not isinstance(item, dict):
                self.ctx.ui.log(f"[Enrich] invalid data type (idx={source_arc_idx}): {type(item)}")
                failed_indices.append(source_arc_idx)
                continue
            indexed_batch.append((source_arc_idx, item))

        enriched_batch = indexed_batch

        if failed_indices and len(enriched_batch) < (batch_end - batch_start):
            self.ctx.ui.log(f"[Recovery] retrying {len(failed_indices)} failed items...")
            recovery_map = {}

            for failed_idx in failed_indices[: RecoveryLimits.MAX_PARALLEL_RECOVERY]:
                try:
                    prev_b = arcs_source[failed_idx - 1] if failed_idx > 0 else None
                    curr_b = arcs_source[failed_idx]
                    next_b_safe = (
                        {
                            "block_id": arcs_source[failed_idx + 1].get("block_id", f"Block {failed_idx + 2}"),
                            "title": arcs_source[failed_idx + 1].get("title", "untitled"),
                        }
                        if failed_idx < total_count - 1
                        else {"title": "final block"}
                    )
                    recovered_item = await self.ctx.agents["analyst"].enrich_raw_block_async(
                        curr_b, prev_b, next_b_safe, [], transfused_history=last_refined_context
                    )
                    if isinstance(recovered_item, dict):
                        recovery_map[failed_idx] = recovered_item
                        self.ctx.ui.log(f"[Recovery] idx={failed_idx} recovered")
                except Exception as retry_err:
                    self.ctx.ui.log(f"[Recovery] idx={failed_idx} failed: {retry_err}")

            if recovery_map:
                original_batch_data = {orig_idx: arc_data for orig_idx, arc_data in enriched_batch if arc_data}
                original_batch_data.update(recovery_map)
                enriched_batch = []
                for idx in range(batch_start, batch_end):
                    if idx in original_batch_data:
                        enriched_batch.append((idx, original_batch_data[idx]))
                    else:
                        self.ctx.ui.log(f"[Recovery] idx={idx} data missing - arc skipped")
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event("data_missing", "arc data not recovered", {"arc_idx": idx})

        if not enriched_batch:
            self.ctx.ui.log("[Critical] enrichment result is empty; stopping Stage 2 batch processing.")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("enrich_error", "empty batch after sanitize and recovery")
            return {"action": "stop", "last_refined_context": last_refined_context, "enriched_batch": []}

        return {
            "action": "continue",
            "last_refined_context": last_refined_context,
            "enriched_batch": enriched_batch,
        }

    def _handle_stage2_finalize_transition(
        self,
        *,
        fin: dict[str, Any],
        global_arc_no: int,
        attempt: int,
        last_refined_context: str,
        current_ep_start: int,
        current_feedback: str,
        director_feedback_for_fourphase: str,
        st_snapshot,
    ) -> Stage2FinalizeTransitionPayload:
        """Apply Stage 2 finalizer outcome updates and return next-loop state."""
        from modules.core.constants import PatchModeThresholds

        action = fin.get("action", "")
        last_refined_context = fin.get("last_refined_context", last_refined_context)
        current_ep_start = fin.get("current_ep_start", current_ep_start)
        current_feedback = fin.get("current_feedback", current_feedback)
        director_feedback_for_fourphase = fin.get(
            "director_feedback_for_fourphase", director_feedback_for_fourphase
        )
        st_snapshot = fin.get("st_snapshot", st_snapshot)

        session_logger = getattr(self.ctx, "session_logger", None)
        if session_logger:
            try:
                stage2_verdict = "PASS" if action == "break" else "REJECT"
                session_logger.log_decision(
                    stage="stage2",
                    ep_num=0,
                    round_num=attempt,
                    decision_type="arc_design",
                    result=stage2_verdict,
                    score=fin.get("score", 0),
                    arc_no=global_arc_no,
                    fix_scope=fin.get("fix_scope", ""),
                )
            except Exception as log_err:
                logging.debug("[SilentPass:Stage2:SessionLog] %s", log_err)

        try:
            rejected_score = int(fin.get("score", 0))
        except (ValueError, TypeError):
            rejected_score = 0

        rejected_arc = fin.get("rejected_arc")
        if action != "break" and rejected_score >= PatchModeThresholds.REWRITE and rejected_arc:
            previous_attempt = {
                "score": rejected_score,
                "best_arc": rejected_arc,
                "rejection_reason": fin.get("director_feedback_for_fourphase", ""),
                "score_breakdown": fin.get("score_breakdown", {}),
                "selection_reason": fin.get("selection_reason", ""),
                "validation_warnings": fin.get("validation_warnings", []),
                "fix_scope": fin.get("fix_scope", ""),
                "selected_strategy": rejected_arc.get("_ensemble_meta", {}).get("best_strategy", ""),
            }
        else:
            previous_attempt = None

        if action in {"retry", "next"}:
            try:
                state_extractor = self.ctx.agents.get("state_extractor") if self.ctx.agents else None
                if state_extractor and hasattr(state_extractor, "invalidate_cache"):
                    state_extractor.invalidate_cache(global_arc_no)
            except Exception as cache_err:
                logging.warning(
                    "[Sweep5-D] state_extractor cache invalidation failed (arc=%s): %s",
                    global_arc_no,
                    cache_err,
                )

        return {
            "action": action,
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
            "previous_attempt": previous_attempt,
        }

    async def _handle_stage2_arc_failure(
        self,
        *,
        global_arc_no: int,
        batch_start: int,
        batch_end: int,
        all_refined_arcs: list,
        arcs_source: list,
        constraint_db,
        refined_arc: dict | None,
        current_ep_start: int,
    ) -> Stage2ArcFailurePayload:
        """Write Stage 2 failure report and handle operator recovery choice."""
        self.ctx.ui.log(f"⚠ [Critical] Arc {global_arc_no} 최종 설계 실패.")
        if callable(getattr(self.ctx, "audit_event", None)):
            self.ctx.audit_event(
                "arc_design_failed",
                "max retries exhausted",
                {"arc_no": global_arc_no, "batch_start": batch_start, "batch_end": batch_end},
            )

        failure_report_path = self.ctx.current_project.paths.root / "logs" / f"arc_{global_arc_no}_failure_report.txt"
        failure_report_path.parent.mkdir(parents=True, exist_ok=True)

        arc_rejects = (
            [r for r in self.ctx.stage_rejection_history if r.get("stage") == 2 and r.get("arc_no") == global_arc_no]
            if self.ctx.stage_rejection_history
            else []
        )
        current_constraints = self._fit_prompt_text(
            constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A",
            6000,
        )

        prev_items = []
        for prev_arc in all_refined_arcs:
            state_constraints = prev_arc.get("state_constraints", {})
            items = state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", [])
            if items:
                prev_items.extend(items if isinstance(items, list) else [items])

        report_lines = [
            f"{'=' * 60}",
            f"Arc {global_arc_no} 실패 리포트",
            f"{'=' * 60}",
            "",
            "[REJECT 히스토리]",
        ]
        for idx, reject_entry in enumerate(arc_rejects, 1):
            report_lines.append(f"  시도 {reject_entry.get('attempt', idx)}: {reject_entry.get('reason', 'N/A')}")

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
                f"  items_acquired: {refined_arc.get('state_constraints', {}).get('protagonist_items') or refined_arc.get('state_constraints', {}).get('items_acquired', [])}"
            )

        report_content = "\n".join(report_lines)

        def _write_failure_report(path, content):
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)

        await asyncio.to_thread(_write_failure_report, failure_report_path, report_content)

        logging.info(f"\n{'=' * 60}")
        logging.warning(f" [V60.46] Arc {global_arc_no} 실패 분석 리포트")
        logging.info(f"{'=' * 60}")
        logging.warning(f"\n REJECT 사유 ({len(arc_rejects)}회):")
        for reject_entry in arc_rejects[-3:]:
            logging.info(f"- {reject_entry.get('reason', 'N/A')[:100]}")
        logging.info(f"\n 중복 획득 금지 아이템 ({len(prev_items)}개):")
        for item in prev_items[:5]:
            logging.info(f"- {item}")
        if len(prev_items) > 5:
            logging.info(f"... 외 {len(prev_items) - 5}개")
        logging.info(f"\n 전체 리포트: {failure_report_path}")
        logging.info(f"{'=' * 60}\n")

        if all_refined_arcs:
            self.ctx.ui.log(f"💾 [Auto-Save] 현재까지 {len(all_refined_arcs)}개 Arc 저장 완료.")

        while True:
            logging.info("[1] 건너뛰고 계속")
            logging.info("[2] 중단")
            logging.info("[3] 다시 하기 (자동)")
            logging.info(" [4] 수동 개입 (리포트 확인 후 재시도)")
            try:
                user_choice = (await asyncio.to_thread(input, "   선택 (기본: 2): ")).strip()
            except (EOFError, KeyboardInterrupt, ValueError):
                user_choice = "2"

            if user_choice == "1":
                self.ctx.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                skip_ep_raw = (
                    arcs_source[global_arc_no - 1].get("ep_count", DEFAULT_EP_COUNT)
                    if global_arc_no <= len(arcs_source)
                    else DEFAULT_EP_COUNT
                )
                try:
                    skip_ep = int(skip_ep_raw)
                except (TypeError, ValueError):
                    skip_ep = DEFAULT_EP_COUNT
                return {"action": "skip", "current_ep_start": current_ep_start + skip_ep}

            if user_choice == "3":
                self.ctx.ui.log(f"🔄 Arc {global_arc_no} 다시 시도합니다...")
                return {
                    "action": "retry",
                    "current_feedback": "",
                    "constraint_block": constraint_db.generate_constraint_block(global_arc_no),
                }

            if user_choice == "4":
                logging.info(f"\n 리포트 파일을 확인하세요: {failure_report_path}")
                logging.info(" 문제가 된 아이템이나 표현을 확인 후, 아래 옵션을 선택하세요.")
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
                    skip_ep_raw = (
                        arcs_source[global_arc_no - 1].get("ep_count", DEFAULT_EP_COUNT)
                        if global_arc_no <= len(arcs_source)
                        else DEFAULT_EP_COUNT
                    )
                    try:
                        skip_ep = int(skip_ep_raw)
                    except (TypeError, ValueError):
                        skip_ep = DEFAULT_EP_COUNT
                    return {"action": "skip", "current_ep_start": current_ep_start + skip_ep}

                if manual_input == "quit":
                    self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                    return {"action": "abort"}

                self.ctx.ui.log(f"🔄 Arc {global_arc_no} 수동 확인 후 재시도...")
                return {
                    "action": "retry",
                    "current_feedback": f"[사용자 수동 확인 완료] 이전 Arc에서 획득한 아이템: {', '.join(prev_items[:5])} 등 {len(prev_items)}개. 이 아이템들은 절대 다시 획득하면 안 됩니다!",
                    "constraint_block": constraint_db.generate_constraint_block(global_arc_no),
                }

            self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
            return {"action": "abort"}
    # ═══════════════════════════════════════════════════════════════════════
    # 메인 파이프라인
    # ═══════════════════════════════════════════════════════════════════════

    async def stage_2_arcs_async_logic(self, *, target_arc_count: int | None = None):
        """
        [V37 S-Grade: 260124 매니페스토]
        0124 욕망 엔진(Desire Engine) 통합 파이프라인 완전판
        """
        # [V64.P3] lazy imports (main_a.py dependency split retained)
        from modules.core.constants import VolumeSettings
        from modules.core.slack_bot import notifier
        from modules.core.spinners import StageSpinner  # [V65] spinner (cycle-safe import)

        startup: Stage2BootstrapPayload = self._bootstrap_stage2_arc_pipeline(target_arc_count=target_arc_count)
        if not startup.get("ready"):
            return

        bible_root = startup["bible_root"]
        arcs_source = startup["arcs_source"]
        volumes_strategy = startup["volumes_strategy"]
        protagonist_name = startup["protagonist_name"]
        grand_obj = startup["grand_obj"]
        all_refined_arcs = startup["all_refined_arcs"]
        done_count = startup["done_count"]
        total_count = startup["total_count"]
        target_limit = startup["target_limit"]
        sem = startup["sem"]
        constraint_db = startup["constraint_db"]
        _genre_for_tracker = startup["genre_for_tracker"]
        genre = _genre_for_tracker
        last_refined_context = startup["last_refined_context"]

        # 2. Batch processing loop
        for batch_start in range(done_count, target_limit, 5):
            batch_end = min(batch_start + 5, target_limit)
            batch_start_count = len(all_refined_arcs)
            batch_result: Stage2BatchEnrichmentPayload = await self._run_stage2_batch_enrichment(
                batch_start=batch_start,
                batch_end=batch_end,
                arcs_source=arcs_source,
                all_refined_arcs=all_refined_arcs,
                last_refined_context=last_refined_context,
                total_count=total_count,
                sem=sem,
            )
            last_refined_context = batch_result["last_refined_context"]
            enriched_batch = batch_result["enriched_batch"]
            if batch_result["action"] == "stop":
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
            _design_total = len(enriched_batch)
            _design_spinner = StageSpinner(2, f"Arc 순차 설계 (총 {_design_total}개)")
            _design_spinner.__enter__()
            while idx < len(enriched_batch):
                _design_spinner.update_detail(f"Arc {idx + 1}/{_design_total} 설계 중...")
                source_arc_idx, enriched_block = enriched_batch[idx]
                global_arc_no = source_arc_idx + 1
                vol_no = ((global_arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME) + 1
                self._set_agent_telemetry_context(ep_num=current_ep_start)
                default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}
                current_vol_strategy = next(
                    (v for v in volumes_strategy if v.get("vol_no") == vol_no),
                    default_vol_strategy,
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
                _base_constraint_block = constraint_block  # [TF-47] retry 간 누적 방지

                while attempt < max_attempts:
                    constraint_block = _base_constraint_block  # [TF-47] retry마다 원본으로 초기화
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
                            pattern_analysis = self._compose_rejection_pattern_feedback(arc_rejections, global_arc_no)
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
                    # [TF-25-09] ArcAutoCorrector 수정 내역을 Director advisory로 전달
                    _corrections = _val.get("corrections_made", [])
                    if _corrections:
                        _corr_text = " / ".join(str(c)[:80] for c in _corrections[:5])
                        constraint_block = (
                            constraint_block or ""
                        ) + f"\n[Python 자동 수정 {len(_corrections)}건] {_corr_text}"
                    # [TF-25-08] Python Pre-Director advisory를 Director에 전달
                    _advisories = _val.get("python_advisories", [])
                    if _advisories:
                        _adv_text = "\n".join(
                            f"[{a['source']}:{a['severity']}] {a['message'][:200]}" for a in _advisories[:5]
                        )
                        constraint_block = (
                            constraint_block or ""
                        ) + f"\n\n[Python Pre-Director advisory {len(_advisories)}건]\n{_adv_text}"

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
                    transition: Stage2FinalizeTransitionPayload = self._handle_stage2_finalize_transition(
                        fin=_fin,
                        global_arc_no=global_arc_no,
                        attempt=attempt,
                        last_refined_context=last_refined_context,
                        current_ep_start=current_ep_start,
                        current_feedback=current_feedback,
                        director_feedback_for_fourphase=director_feedback_for_fourphase,
                        st_snapshot=_st_snapshot,
                    )
                    last_refined_context = transition["last_refined_context"]
                    current_ep_start = transition["current_ep_start"]
                    current_feedback = transition["current_feedback"]
                    director_feedback_for_fourphase = transition["director_feedback_for_fourphase"]
                    _st_snapshot = transition["st_snapshot"]
                    _previous_attempt = transition["previous_attempt"]

                    if transition["action"] == "break":
                        passed = True
                        break
                    if transition["action"] == "retry":
                        attempt += 1
                        continue
                    elif transition["action"] == "next":
                        attempt += 1
                        continue

                    attempt += 1

                if not passed:
                    failure_result: Stage2ArcFailurePayload = await self._handle_stage2_arc_failure(
                        global_arc_no=global_arc_no,
                        batch_start=batch_start,
                        batch_end=batch_end,
                        all_refined_arcs=all_refined_arcs,
                        arcs_source=arcs_source,
                        constraint_db=constraint_db,
                        refined_arc=refined_arc,
                        current_ep_start=current_ep_start,
                    )
                    if failure_result["action"] == "abort":
                        _design_spinner.__exit__(None, None, None)
                        return
                    if failure_result["action"] == "skip":
                        current_ep_start = failure_result["current_ep_start"]
                    elif failure_result["action"] == "retry":
                        attempt = 0
                        passed = False
                        current_feedback = failure_result["current_feedback"]
                        constraint_block = failure_result["constraint_block"]
                        continue

                # [V60.45] 다음 Arc로
                idx += 1

            _design_spinner.__exit__(None, None, None)
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
        threshold: float = TACTICAL_DOC_DUPLICATE_THRESHOLD,
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
