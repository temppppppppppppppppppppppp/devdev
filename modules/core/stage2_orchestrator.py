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
import os
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

from modules.core.constants import VolumeSettings, smart_truncate
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
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


class Stage2SingleArcAttemptPayload(TypedDict):
    action: str
    next_attempt: int
    current_feedback: str
    director_feedback_for_fourphase: str
    st_snapshot: Any
    last_refined_context: str
    current_ep_start: int
    previous_attempt: dict[str, Any] | None
    refined_arc: dict[str, Any] | None


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

    def _stage2_failure_prompt_policy(self) -> str:
        raw_policy = str(os.environ.get("GEULDOBI_STAGE2_FAILURE_POLICY") or "").strip().lower()
        if raw_policy in {"abort", "prompt"}:
            return raw_policy

        raw_headless = str(os.environ.get("GEULDOBI_STAGE2_HEADLESS") or "").strip().lower()
        if raw_headless in {"1", "true", "yes", "on"}:
            return "abort"

        return "prompt"

    def _stage2_should_suppress_prompts(self) -> bool:
        # Keep interactive and desktop prompt flows intact by default.
        # Only explicit Stage2 headless runs may suppress failure / pause prompts.
        return self._stage2_failure_prompt_policy() == "abort"

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
        retry_directives = []
        runtime_advisories = []
        for reject in arc_rejections:
            reason = str(reject.get("reason", "사유 미상") or "사유 미상")[:120]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            issue = str(reject.get("specific_issue", "") or "").strip()
            if issue and issue not in specific_issues:
                specific_issues.append(issue[:120])
            retry_directive = str(reject.get("retry_directives", "") or "").strip()
            if retry_directive and retry_directive not in retry_directives:
                retry_directives.append(retry_directive[:160])
            runtime_advisory = str(reject.get("runtime_advisory", "") or "").strip()
            if runtime_advisory and runtime_advisory not in runtime_advisories:
                runtime_advisories.append(runtime_advisory[:160])

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
        if retry_directives:
            lines.append("")
            lines.append("🧭 보존된 재시도 지시:")
            for directive in retry_directives[:3]:
                lines.append(f"   - {directive}")
        if runtime_advisories:
            lines.append("")
            lines.append("🛡️ 런타임 주의:")
            for advisory in runtime_advisories[:3]:
                lines.append(f"   - {advisory}")
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

    def _bootstrap_stage2_arc_pipeline(self, *, target_arc_count: int | None) -> Stage2BootstrapPayload:
        """Prepare Stage 2 startup state before entering batch orchestration."""
        from modules.core.constants import HUDKeys
        from modules.core.constraint_db import ConstraintDB
        from modules.core.stage0_handoff import build_stage0_runtime_handoff_summary, check_plot_roadmap_ready
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

        stage0_handoff = build_stage0_runtime_handoff_summary(bible_data)
        self.ctx.ui.log(
            "      [Stage0 Contract] "
            f"runtime_handoff_owner={stage0_handoff.get('runtime_handoff_owner')}; "
            f"stage2_surface={stage0_handoff.get('runtime_handoff_surface')}; "
            f"stage2_consumer_mode={stage0_handoff.get('stage2_consumer_mode')}; "
            f"projection_source={stage0_handoff.get('projection_source')}; "
            f"plot_roadmap_authority={stage0_handoff.get('plot_roadmap_authority')}; "
            f"force_sync_bridge={stage0_handoff.get('compatibility_bridges', {}).get('force_sync_v25_dna')}"
        )

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
        if (
            self.ctx.state_tracker is None
            or existing_tracker_arcs == 0
            or existing_tracker_arcs > len(all_refined_arcs)
        ):
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
        import time as _time_mod

        from modules.core.constants import RecoveryLimits
        from modules.core.spinners import StageSpinner

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
                    spinner.update_detail(
                        f"Batch {batch_start + 1}~{batch_end} LLM enrich ({enrich_done}/{enrich_total})"
                    )
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
                    self.ctx.audit_event(
                        "enrich_error", "batch enrich failed", {"error": str(item), "arc_idx": source_arc_idx}
                    )
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
        director_feedback_for_fourphase = fin.get("director_feedback_for_fourphase", director_feedback_for_fourphase)
        st_snapshot = fin.get("st_snapshot", st_snapshot)

        session_logger = getattr(self.ctx, "session_logger", None)
        if session_logger:
            try:
                if action == "break":
                    stage2_verdict = "PASS"
                elif action in {"retry", "continue"}:
                    stage2_verdict = "RETRY"
                else:
                    stage2_verdict = "REJECT"
                attempt_key = build_attempt_key(
                    stage=2,
                    ep_num=global_arc_no,
                    arc_num=global_arc_no,
                    attempt_num=attempt + 1,
                    session_id=resolve_logging_session_id(getattr(self.ctx, "current_project", None)),
                )
                session_logger.log_decision(
                    stage="stage2",
                    ep_num=global_arc_no,
                    round_num=attempt + 1,
                    decision_type="arc_design",
                    result=stage2_verdict,
                    score=fin.get("score", 0),
                    arc_no=global_arc_no,
                    fix_scope=fin.get("fix_scope", ""),
                    attempt_key=attempt_key,
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
        failure_report_path = self._resolve_stage2_arc_failure_report_path(global_arc_no=global_arc_no)
        failure_context = self._build_stage2_arc_failure_report_context(
            global_arc_no=global_arc_no,
            all_refined_arcs=all_refined_arcs,
            constraint_db=constraint_db,
        )
        self.ctx.ui.log(f"⚠ [Critical] Arc {global_arc_no} 최종 설계 실패.")
        if callable(getattr(self.ctx, "audit_event", None)):
            self.ctx.audit_event(
                "arc_design_failed",
                "max retries exhausted",
                {"arc_no": global_arc_no, "batch_start": batch_start, "batch_end": batch_end},
            )
        report_lines = self._build_stage2_arc_failure_report_lines(
            global_arc_no=global_arc_no,
            refined_arc=refined_arc,
            arc_rejects=failure_context["arc_rejects"],
            prev_items=failure_context["prev_items"],
            current_constraints=failure_context["current_constraints"],
        )
        await self._write_stage2_arc_failure_report(
            failure_report_path=failure_report_path,
            report_lines=report_lines,
        )
        self._log_stage2_arc_failure_summary(
            global_arc_no=global_arc_no,
            failure_report_path=failure_report_path,
            arc_rejects=failure_context["arc_rejects"],
            prev_items=failure_context["prev_items"],
        )

        if all_refined_arcs:
            self.ctx.ui.log(f"💾 [Auto-Save] 현재까지 {len(all_refined_arcs)}개 Arc 저장 완료.")

        if self._stage2_should_suppress_prompts():
            self.ctx.ui.log("⏹️ [Stage2 Headless] 실패 리포트 저장 후 자동 중단합니다.")
            return {"action": "abort"}

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
                return self._build_stage2_arc_failure_skip_payload(
                    global_arc_no=global_arc_no,
                    arcs_source=arcs_source,
                    current_ep_start=current_ep_start,
                )

            if user_choice == "3":
                self.ctx.ui.log(f"🔄 Arc {global_arc_no} 다시 시도합니다...")
                return self._build_stage2_arc_failure_retry_payload(
                    global_arc_no=global_arc_no,
                    constraint_db=constraint_db,
                    current_feedback="",
                )

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
                    return self._build_stage2_arc_failure_skip_payload(
                        global_arc_no=global_arc_no,
                        arcs_source=arcs_source,
                        current_ep_start=current_ep_start,
                    )

                if manual_input == "quit":
                    self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                    return {"action": "abort"}

                self.ctx.ui.log(f"🔄 Arc {global_arc_no} 수동 확인 후 재시도...")
                return self._build_stage2_arc_failure_retry_payload(
                    global_arc_no=global_arc_no,
                    constraint_db=constraint_db,
                    current_feedback=(
                        f"[사용자 수동 확인 완료] 이전 Arc에서 획득한 아이템: "
                        f"{', '.join(failure_context['prev_items'][:5])} 등 {len(failure_context['prev_items'])}개. "
                        "이 아이템들은 절대 다시 획득하면 안 됩니다!"
                    ),
                )

            self.ctx.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
            return {"action": "abort"}

    def _resolve_stage2_arc_failure_report_path(self, *, global_arc_no: int) -> Path:
        failure_report_path = self.ctx.current_project.paths.root / "logs" / f"arc_{global_arc_no}_failure_report.txt"
        failure_report_path.parent.mkdir(parents=True, exist_ok=True)
        return failure_report_path

    def _build_stage2_arc_failure_report_context(
        self,
        *,
        global_arc_no: int,
        all_refined_arcs: list[Any],
        constraint_db,
    ) -> dict[str, Any]:
        arc_rejects = (
            [r for r in self.ctx.stage_rejection_history if r.get("stage") == 2 and r.get("arc_no") == global_arc_no]
            if self.ctx.stage_rejection_history
            else []
        )
        current_constraints = self._fit_prompt_text(
            constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A",
            6000,
        )
        prev_items: list[Any] = []
        for prev_arc in all_refined_arcs:
            state_constraints = prev_arc.get("state_constraints", {})
            items = state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", [])
            if items:
                prev_items.extend(items if isinstance(items, list) else [items])
        return {
            "arc_rejects": arc_rejects,
            "current_constraints": current_constraints,
            "prev_items": prev_items,
        }

    def _build_stage2_arc_failure_report_lines(
        self,
        *,
        global_arc_no: int,
        refined_arc: dict | None,
        arc_rejects: list[dict[str, Any]],
        prev_items: list[Any],
        current_constraints: str,
    ) -> list[str]:
        report_lines = [
            f"{'=' * 60}",
            f"Arc {global_arc_no} 실패 리포트",
            f"{'=' * 60}",
            "",
            "[REJECT 히스토리]",
        ]
        for idx, reject_entry in enumerate(arc_rejects, 1):
            report_lines.append(f"  시도 {reject_entry.get('attempt', idx)}: {reject_entry.get('reason', 'N/A')}")
        report_lines.extend(["", "[이전 Arc에서 이미 획득한 아이템 - 중복 획득 금지]"])
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
        return report_lines

    async def _write_stage2_arc_failure_report(
        self,
        *,
        failure_report_path: Path,
        report_lines: list[str],
    ) -> None:
        report_content = "\n".join(report_lines)

        def _write_failure_report(path: Path, content: str) -> None:
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)

        await asyncio.to_thread(_write_failure_report, failure_report_path, report_content)

    def _log_stage2_arc_failure_summary(
        self,
        *,
        global_arc_no: int,
        failure_report_path: Path,
        arc_rejects: list[dict[str, Any]],
        prev_items: list[Any],
    ) -> None:
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

    def _build_stage2_arc_failure_skip_payload(
        self,
        *,
        global_arc_no: int,
        arcs_source: list[Any],
        current_ep_start: int,
    ) -> Stage2ArcFailurePayload:
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

    def _build_stage2_arc_failure_retry_payload(
        self,
        *,
        global_arc_no: int,
        constraint_db,
        current_feedback: str,
    ) -> Stage2ArcFailurePayload:
        return {
            "action": "retry",
            "current_feedback": current_feedback,
            "constraint_block": constraint_db.generate_constraint_block(global_arc_no),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 메인 파이프라인
    # ═══════════════════════════════════════════════════════════════════════

    async def stage_2_arcs_async_logic(self, *, target_arc_count: int | None = None):
        """
        [V37 S-Grade: 260124 매니페스토]
        0124 욕망 엔진(Desire Engine) 통합 파이프라인 완전판
        """
        # [V64.P3] lazy imports (main_a.py dependency split retained)
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

            self._run_stage2_joint_stitching(
                enriched_batch=enriched_batch,
                batch_start=batch_start,
                batch_end=batch_end,
                stage_spinner_cls=StageSpinner,
            )
            batch_design = await self._run_stage2_batch_design_loop(
                enriched_batch=enriched_batch,
                batch_start=batch_start,
                batch_end=batch_end,
                all_refined_arcs=all_refined_arcs,
                arcs_source=arcs_source,
                volumes_strategy=volumes_strategy,
                protagonist_name=protagonist_name,
                grand_obj=grand_obj,
                bible_root=bible_root,
                constraint_db=constraint_db,
                genre=genre,
                last_refined_context=last_refined_context,
                stage_spinner_cls=StageSpinner,
            )
            if batch_design["action"] == "abort":
                return
            last_refined_context = batch_design["last_refined_context"]

            self._handle_stage2_batch_completion(
                batch_start=batch_start,
                batch_end=batch_end,
                batch_start_count=batch_start_count,
                all_refined_arcs=all_refined_arcs,
                notifier=notifier,
            )

        # EOFError/KeyboardInterrupt input tail handling remains inside the completion helper.
        await self._complete_stage2_pipeline(target_arc_count=target_arc_count)

    def _run_stage2_joint_stitching(
        self,
        *,
        enriched_batch: list[tuple[int, dict[str, Any]]],
        batch_start: int,
        batch_end: int,
        stage_spinner_cls,
    ) -> None:
        """Batch post-weld 단계에서 analyst joint repair와 anchor handoff를 수행한다."""
        with stage_spinner_cls(2, f"Arc {batch_start + 1}~{batch_end} 인과율 용접"):
            for index in range(len(enriched_batch) - 1):
                arc_a_idx, arc_a = enriched_batch[index]
                arc_b_idx, arc_b = enriched_batch[index + 1]
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
                    if "content" in arc_b and isinstance(arc_b["content"], dict):
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

    async def _run_stage2_batch_design_loop(
        self,
        *,
        enriched_batch: list[tuple[int, dict[str, Any]]],
        batch_start: int,
        batch_end: int,
        all_refined_arcs: list[Any],
        arcs_source: list[Any],
        volumes_strategy: list[Any],
        protagonist_name: str | None,
        grand_obj: str,
        bible_root: dict[str, Any],
        constraint_db,
        genre: str,
        last_refined_context: str,
        stage_spinner_cls,
    ) -> dict[str, Any]:
        """배치 단위 순차 설계를 담당하고 abort/next 상태만 외부로 반환한다."""
        current_ep_start = 1 if not all_refined_arcs else max(1, all_refined_arcs[-1].get("ep_end", 0) + 1)
        idx = 0
        design_total = len(enriched_batch)
        with stage_spinner_cls(2, f"Arc 순차 설계 (총 {design_total}개)") as design_spinner:
            while idx < len(enriched_batch):
                design_spinner.update_detail(f"Arc {idx + 1}/{design_total} 설계 중...")
                source_arc_idx, enriched_block = enriched_batch[idx]
                arc_result = await self._run_stage2_single_arc_design(
                    source_arc_idx=source_arc_idx,
                    enriched_block=enriched_block,
                    batch_start=batch_start,
                    batch_end=batch_end,
                    all_refined_arcs=all_refined_arcs,
                    arcs_source=arcs_source,
                    volumes_strategy=volumes_strategy,
                    protagonist_name=protagonist_name,
                    grand_obj=grand_obj,
                    bible_root=bible_root,
                    constraint_db=constraint_db,
                    genre=genre,
                    last_refined_context=last_refined_context,
                    current_ep_start=current_ep_start,
                )
                if arc_result["action"] == "abort":
                    return {"action": "abort", "last_refined_context": last_refined_context}

                current_ep_start = arc_result["current_ep_start"]
                last_refined_context = arc_result["last_refined_context"]
                idx += 1

        return {"action": "continue", "last_refined_context": last_refined_context}

    async def _run_stage2_single_arc_design(
        self,
        *,
        source_arc_idx: int,
        enriched_block: dict[str, Any],
        batch_start: int,
        batch_end: int,
        all_refined_arcs: list[Any],
        arcs_source: list[Any],
        volumes_strategy: list[Any],
        protagonist_name: str | None,
        grand_obj: str,
        bible_root: dict[str, Any],
        constraint_db,
        genre: str,
        last_refined_context: str,
        current_ep_start: int,
    ) -> dict[str, Any]:
        """단일 Arc의 preflight/generate/validate/finalize 재시도 루프를 감싼다."""
        global_arc_no = source_arc_idx + 1
        current_vol_strategy = self._resolve_stage2_current_vol_strategy(volumes_strategy, global_arc_no)
        setup = self._prepare_stage2_single_arc_state(
            source_arc_idx=source_arc_idx,
            all_refined_arcs=all_refined_arcs,
            arcs_source=arcs_source,
            grand_obj=grand_obj,
            global_arc_no=global_arc_no,
            constraint_db=constraint_db,
            genre=genre,
            current_ep_start=current_ep_start,
        )
        passed = setup["passed"]
        current_feedback = setup["current_feedback"]
        attempt = setup["attempt"]
        max_attempts = setup["max_attempts"]
        director_feedback_for_fourphase = setup["director_feedback_for_fourphase"]
        st_snapshot = setup["st_snapshot"]
        previous_attempt = None
        refined_arc = None

        while attempt < max_attempts:
            attempt_result = await self._run_stage2_single_arc_attempt(
                global_arc_no=global_arc_no,
                attempt=attempt,
                max_attempts=max_attempts,
                setup=setup,
                enriched_block=enriched_block,
                all_refined_arcs=all_refined_arcs,
                current_vol_strategy=current_vol_strategy,
                protagonist_name=protagonist_name,
                bible_root=bible_root,
                constraint_db=constraint_db,
                genre=genre,
                last_refined_context=last_refined_context,
                current_ep_start=current_ep_start,
                current_feedback=current_feedback,
                director_feedback_for_fourphase=director_feedback_for_fourphase,
                st_snapshot=st_snapshot,
                previous_attempt=previous_attempt,
            )
            attempt = attempt_result["next_attempt"]
            refined_arc = attempt_result["refined_arc"]
            current_feedback = attempt_result["current_feedback"]
            director_feedback_for_fourphase = attempt_result["director_feedback_for_fourphase"]
            st_snapshot = attempt_result["st_snapshot"]
            last_refined_context = attempt_result["last_refined_context"]
            current_ep_start = attempt_result["current_ep_start"]
            previous_attempt = attempt_result["previous_attempt"]

            if attempt_result["action"] == "break":
                passed = True
                break

        if not passed:
            failure_state = await self._handle_stage2_single_arc_failure(
                global_arc_no=global_arc_no,
                batch_start=batch_start,
                batch_end=batch_end,
                all_refined_arcs=all_refined_arcs,
                arcs_source=arcs_source,
                constraint_db=constraint_db,
                refined_arc=refined_arc,
                current_ep_start=current_ep_start,
                last_refined_context=last_refined_context,
            )
            if failure_state["action"] == "abort":
                return failure_state
            current_ep_start = failure_state["current_ep_start"]

        return {"action": "next", "current_ep_start": current_ep_start, "last_refined_context": last_refined_context}

    async def _run_stage2_single_arc_attempt(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        max_attempts: int,
        setup: dict[str, Any],
        enriched_block: dict[str, Any],
        all_refined_arcs: list[Any],
        current_vol_strategy: dict[str, Any],
        protagonist_name: str | None,
        bible_root: dict[str, Any],
        constraint_db,
        genre: str,
        last_refined_context: str,
        current_ep_start: int,
        current_feedback: str,
        director_feedback_for_fourphase: str,
        st_snapshot,
        previous_attempt: dict[str, Any] | None,
    ) -> Stage2SingleArcAttemptPayload:
        """Execute one single-arc attempt and return the next loop state."""
        # Keep a lightweight operator heartbeat ahead of the four-phase call so a
        # long LLM wait reads as "in progress" instead of a silent stall.
        self.ctx.ui.log(
            f"      ⏳ [Stage 2] Arc {global_arc_no} attempt {attempt + 1}/{max_attempts}: "
            "preflight/four-phase tactical generation 대기...",
            stage="stage2",
            component="single_arc_attempt",
            ep_num=global_arc_no,
            arc_num=global_arc_no,
            event_kind="heartbeat",
            meta={
                "attempt": attempt + 1,
                "max_attempts": max_attempts,
                "current_ep_start": current_ep_start,
                "wait_state": "preflight_four_phase_generation",
            },
        )
        attempt_state = self._run_stage2_single_arc_preflight(
            global_arc_no=global_arc_no,
            attempt=attempt,
            setup=setup,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            last_refined_context=last_refined_context,
            current_feedback=current_feedback,
            current_ep_start=current_ep_start,
            current_vol_strategy=current_vol_strategy,
            enriched_block=enriched_block,
            bible_root=bible_root,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            genre=genre,
            previous_attempt=previous_attempt,
        )
        if self._log_stage2_four_phase_retry(attempt_state["refined_arc"], attempt, max_attempts):
            return self._build_stage2_single_arc_retry_payload(
                attempt=attempt,
                current_feedback=attempt_state["current_feedback"],
                director_feedback_for_fourphase=attempt_state["director_feedback_for_fourphase"],
                st_snapshot=attempt_state["st_snapshot"],
                last_refined_context=last_refined_context,
                current_ep_start=current_ep_start,
                previous_attempt=previous_attempt,
                refined_arc=attempt_state["refined_arc"],
            )

        self.ctx.ui.log(
            f"      🔎 [Stage 2] Arc {global_arc_no} attempt {attempt + 1}: "
            f"generation={attempt_state['generation_method']} · validation 진입",
            stage="stage2",
            component="single_arc_attempt",
            ep_num=global_arc_no,
            arc_num=global_arc_no,
            event_kind="progress",
            meta={
                "attempt": attempt + 1,
                "current_ep_start": current_ep_start,
                "generation_method": attempt_state["generation_method"],
                "four_phase_passed": bool(attempt_state["four_phase_passed"]),
                "draft_validator_passed": bool(attempt_state["draft_validator_passed"]),
                "consensus_passed": bool(attempt_state["consensus_passed"]),
            },
        )
        validation_state = self._run_stage2_single_arc_validation(
            global_arc_no=global_arc_no,
            attempt=attempt,
            refined_arc=attempt_state["refined_arc"],
            four_phase_passed=attempt_state["four_phase_passed"],
            all_refined_arcs=all_refined_arcs,
            entity_registry_for_director=attempt_state["entity_registry_for_director"],
            current_ep_start=current_ep_start,
            current_feedback=attempt_state["current_feedback"],
            generation_method=attempt_state["generation_method"],
            constraint_block=attempt_state["constraint_block"],
            enriched_block=enriched_block,
            draft_validator_passed=attempt_state["draft_validator_passed"],
            consensus_passed=attempt_state["consensus_passed"],
            protagonist_name=protagonist_name,
            constraint_db=constraint_db,
            st_snapshot=attempt_state["st_snapshot"],
            last_refined_context=last_refined_context,
            previous_attempt=previous_attempt,
        )
        if validation_state["action"] == "retry":
            return validation_state["payload"]

        return await self._finalize_stage2_single_arc_attempt(
            global_arc_no=global_arc_no,
            attempt=attempt,
            setup=setup,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            bible_root=bible_root,
            constraint_db=constraint_db,
            genre=genre,
            last_refined_context=last_refined_context,
            current_ep_start=current_ep_start,
            director_feedback_for_fourphase=attempt_state["director_feedback_for_fourphase"],
            refined_arc=validation_state["refined_arc"],
            current_feedback=attempt_state["current_feedback"],
            suspected_duplicates=validation_state["suspected_duplicates"],
            entity_registry_for_director=attempt_state["entity_registry_for_director"],
            constraint_block=validation_state["constraint_block"],
            draft_validator_passed=validation_state["draft_validator_passed"],
            consensus_passed=validation_state["consensus_passed"],
            generation_method=attempt_state["generation_method"],
            was_patch=attempt_state["was_patch"],
            prev_score=attempt_state["prev_score"],
            patch_fallback=attempt_state["patch_fallback"],
            st_snapshot=attempt_state["st_snapshot"],
        )

    def _run_stage2_single_arc_preflight(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        setup: dict[str, Any],
        all_refined_arcs: list[Any],
        protagonist_name: str | None,
        last_refined_context: str,
        current_feedback: str,
        current_ep_start: int,
        current_vol_strategy: dict[str, Any],
        enriched_block: dict[str, Any],
        bible_root: dict[str, Any],
        director_feedback_for_fourphase: str,
        genre: str,
        previous_attempt: dict[str, Any] | None,
    ) -> dict[str, Any]:
        current_feedback = self._augment_stage2_feedback_from_rejections(
            current_feedback=current_feedback,
            attempt=attempt,
            global_arc_no=global_arc_no,
        )
        analysis = self.preflight._preflight_arc_analysis(
            attempt=attempt,
            current_feedback=current_feedback,
            constraint_block=setup["constraint_block"],
            last_refined_context=last_refined_context,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            global_arc_no=global_arc_no,
            cached_preflight_injection=setup["cached_preflight_injection"],
            cached_preflight_result=setup["cached_preflight_result"],
        )
        enrichment = self.preflight._preflight_enrichment(
            attempt=attempt,
            global_arc_no=global_arc_no,
            current_ep_start=current_ep_start,
            current_vol_strategy=current_vol_strategy,
            enriched_block=enriched_block,
            all_refined_arcs=all_refined_arcs,
            bible_root=bible_root,
            protagonist_name=protagonist_name,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            entity_registry_for_director=analysis["entity_registry_for_director"],
            genre_for_tracker=genre,
            previous_attempt=previous_attempt,
        )
        return {
            "current_feedback": current_feedback,
            "refined_arc": enrichment["refined_arc"],
            "generation_method": enrichment["generation_method"],
            "constraint_block": analysis["constraint_block"],
            "entity_registry_for_director": analysis["entity_registry_for_director"],
            "four_phase_passed": enrichment["four_phase_passed"],
            "draft_validator_passed": enrichment["draft_validator_passed"],
            "consensus_passed": enrichment["consensus_passed"],
            "st_snapshot": enrichment["st_snapshot"],
            "director_feedback_for_fourphase": enrichment["director_feedback_for_fourphase"],
            "was_patch": enrichment.get("was_patch", False),
            "patch_fallback": enrichment.get("patch_fallback", False),
            "prev_score": enrichment.get("prev_score", 0),
        }

    def _build_stage2_single_arc_retry_payload(
        self,
        *,
        attempt: int,
        current_feedback: str,
        director_feedback_for_fourphase: str,
        st_snapshot,
        last_refined_context: str,
        current_ep_start: int,
        previous_attempt: dict[str, Any] | None,
        refined_arc: dict[str, Any] | None,
    ) -> Stage2SingleArcAttemptPayload:
        return {
            "action": "retry",
            "next_attempt": attempt + 1,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "previous_attempt": previous_attempt,
            "refined_arc": refined_arc,
        }

    def _run_stage2_single_arc_validation(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        refined_arc: dict[str, Any] | None,
        four_phase_passed: bool,
        all_refined_arcs: list[Any],
        entity_registry_for_director,
        current_ep_start: int,
        current_feedback: str,
        generation_method: str,
        constraint_block: str,
        enriched_block: dict[str, Any],
        draft_validator_passed: bool,
        consensus_passed: bool,
        protagonist_name: str | None,
        constraint_db,
        st_snapshot,
        last_refined_context: str,
        previous_attempt: dict[str, Any] | None,
    ) -> dict[str, Any]:
        validation = self.validation_pipeline.run_validation(
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
        if validation["action"] == "retry":
            retry_feedback = validation["current_feedback"]
            return {
                "action": "retry",
                "payload": self._build_stage2_single_arc_retry_payload(
                    attempt=attempt,
                    current_feedback=retry_feedback,
                    director_feedback_for_fourphase=retry_feedback,
                    st_snapshot=st_snapshot,
                    last_refined_context=last_refined_context,
                    current_ep_start=current_ep_start,
                    previous_attempt=previous_attempt,
                    refined_arc=refined_arc,
                ),
            }
        return {
            "action": "continue",
            "refined_arc": validation["refined_arc"],
            "draft_validator_passed": validation["draft_validator_passed"],
            "consensus_passed": validation["consensus_passed"],
            "suspected_duplicates": validation["suspected_duplicates"],
            "constraint_block": self._apply_stage2_validation_advisories(
                constraint_block=constraint_block,
                corrections_made=validation.get("corrections_made", []),
                python_advisories=validation.get("python_advisories", []),
            ),
        }

    async def _finalize_stage2_single_arc_attempt(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        setup: dict[str, Any],
        enriched_block: dict[str, Any],
        all_refined_arcs: list[Any],
        protagonist_name: str | None,
        bible_root: dict[str, Any],
        constraint_db,
        genre: str,
        last_refined_context: str,
        current_ep_start: int,
        director_feedback_for_fourphase: str,
        refined_arc: dict[str, Any],
        current_feedback: str,
        suspected_duplicates: list[Any],
        entity_registry_for_director,
        constraint_block: str,
        draft_validator_passed: bool,
        consensus_passed: bool,
        generation_method: str,
        was_patch: bool,
        prev_score: int | float,
        patch_fallback: bool,
        st_snapshot,
    ) -> Stage2SingleArcAttemptPayload:
        finalize_result = await self.finalizer.run_finalize(
            refined_arc=refined_arc,
            enriched_block=enriched_block,
            arc_drive=setup["arc_drive"],
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
            is_patch=was_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            st_snapshot=st_snapshot,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            last_refined_context=last_refined_context,
            bible_root=bible_root,
            genre=genre,
            constraint_db=constraint_db,
        )
        transition: Stage2FinalizeTransitionPayload = self._handle_stage2_finalize_transition(
            fin=finalize_result,
            global_arc_no=global_arc_no,
            attempt=attempt,
            last_refined_context=last_refined_context,
            current_ep_start=current_ep_start,
            current_feedback=current_feedback,
            director_feedback_for_fourphase=director_feedback_for_fourphase,
            st_snapshot=st_snapshot,
        )
        transition_state = self._apply_stage2_finalize_transition_state(transition)
        return {
            "action": transition["action"],
            "next_attempt": attempt if transition["action"] == "break" else attempt + 1,
            "current_feedback": transition_state["current_feedback"],
            "director_feedback_for_fourphase": transition_state["director_feedback_for_fourphase"],
            "st_snapshot": transition_state["st_snapshot"],
            "last_refined_context": transition_state["last_refined_context"],
            "current_ep_start": transition_state["current_ep_start"],
            "previous_attempt": transition_state["previous_attempt"],
            "refined_arc": refined_arc,
        }

    def _prepare_stage2_single_arc_state(
        self,
        *,
        source_arc_idx: int,
        all_refined_arcs: list[Any],
        arcs_source: list[Any],
        grand_obj: str,
        global_arc_no: int,
        constraint_db,
        genre: str,
        current_ep_start: int,
    ) -> dict[str, Any]:
        """단일 Arc 시도 루프에 필요한 analyst lack report와 preflight setup을 준비한다."""
        self._set_agent_telemetry_context(ep_num=current_ep_start)
        try:
            lack_report = self.ctx.agents["analyst"].get_lack_report(self.ctx.sys.hud.pro_root)
        except Exception as lack_err:
            self.ctx.ui.log(f"⚠️ [Analyst] 결핍 리포트 생성 실패: {lack_err}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "analyst_error",
                    "get_lack_report failed",
                    {"arc_no": global_arc_no, "error": str(lack_err)},
                )
            lack_report = {"martial_deficit": "분석 실패", "status": "error"}

        return self.preflight._preflight_state_setup(
            all_refined_arcs=all_refined_arcs,
            arcs_source=arcs_source,
            arc_idx=source_arc_idx,
            lack_report=lack_report,
            grand_obj=grand_obj,
            global_arc_no=global_arc_no,
            constraint_db=constraint_db,
            genre=genre,
        )

    def _resolve_stage2_current_vol_strategy(self, volumes_strategy: list[Any], global_arc_no: int) -> dict[str, Any]:
        """현재 Arc 번호에 대응하는 권별 전략 문서를 고른다."""
        vol_no = ((global_arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME) + 1
        default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}
        return next(
            (strategy for strategy in volumes_strategy if strategy.get("vol_no") == vol_no), default_vol_strategy
        )

    def _augment_stage2_feedback_from_rejections(
        self, *, current_feedback: str, attempt: int, global_arc_no: int
    ) -> str:
        """이전 REJECT 패턴을 현재 feedback 앞단에만 덧붙인다."""
        if attempt < 1 or not self.ctx.stage_rejection_history:
            return current_feedback

        arc_rejections = [
            entry
            for entry in self.ctx.stage_rejection_history
            if entry.get("stage") == 2 and entry.get("arc_no") == global_arc_no
        ]
        if not arc_rejections:
            return current_feedback

        pattern_analysis = self._compose_rejection_pattern_feedback(arc_rejections, global_arc_no)
        if not pattern_analysis:
            return current_feedback

        self.ctx.ui.log(f"      🔍 [V60.10] REJECT 패턴 분석 주입 ({len(arc_rejections)}건)")
        return pattern_analysis + "\n" + current_feedback

    def _apply_stage2_finalize_transition_state(
        self, transition: Stage2FinalizeTransitionPayload
    ) -> Stage2FinalizeTransitionPayload:
        """Finalize transition payload를 현재 Arc 루프 상태 형태로 그대로 전달한다."""
        return transition

    async def _handle_stage2_single_arc_failure(
        self,
        *,
        global_arc_no: int,
        batch_start: int,
        batch_end: int,
        all_refined_arcs: list[Any],
        arcs_source: list[Any],
        constraint_db,
        refined_arc: dict[str, Any] | None,
        current_ep_start: int,
        last_refined_context: str,
    ) -> dict[str, Any]:
        """단일 Arc 시도 소진 후 abort/skip 경계만 정리한다."""
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
            return {
                "action": "abort",
                "current_ep_start": current_ep_start,
                "last_refined_context": last_refined_context,
            }
        if failure_result["action"] == "skip":
            current_ep_start = failure_result["current_ep_start"]
        return {"action": "next", "current_ep_start": current_ep_start, "last_refined_context": last_refined_context}

    def _apply_stage2_validation_advisories(
        self,
        *,
        constraint_block: str,
        corrections_made: list[Any],
        python_advisories: list[dict[str, Any]],
    ) -> str:
        """Python-side advisory를 Director constraint block에 선형으로 병합한다."""
        updated_constraint_block = constraint_block or ""
        if corrections_made:
            correction_text = " / ".join(str(correction)[:80] for correction in corrections_made[:5])
            updated_constraint_block += f"\n[Python 자동 수정 {len(corrections_made)}건] {correction_text}"
        if python_advisories:
            advisory_text = "\n".join(
                f"[{advisory['source']}:{advisory['severity']}] {advisory['message'][:200]}"
                for advisory in python_advisories[:5]
            )
            updated_constraint_block += (
                f"\n\n[Python Pre-Director advisory {len(python_advisories)}건]\n{advisory_text}"
            )
        return updated_constraint_block

    def _log_stage2_four_phase_retry(self, refined_arc: dict[str, Any] | None, attempt: int, max_attempts: int) -> bool:
        """FourPhase 생성 실패 시 재시도 로그를 남기고 continue 여부를 반환한다."""
        if refined_arc is not None:
            return False
        self.ctx.ui.log(
            f"      🔄 [V60.77] FourPhase 실패 → Director 대면 {min(attempt + 2, max_attempts)}/{max_attempts} 재시도"
        )
        return True

    def _handle_stage2_batch_completion(
        self,
        *,
        batch_start: int,
        batch_end: int,
        batch_start_count: int,
        all_refined_arcs: list[Any],
        notifier,
    ) -> None:
        """배치 완료 로그와 Slack side effect를 한곳에 묶는다."""
        self.ctx.ui.log(f"✅ 배치({batch_start + 1}~{batch_end}) 욕망 엔진 이식 및 용접 완료.")
        try:
            batch_results_count = len(all_refined_arcs) - batch_start_count
            notifier.send_notification(
                title=f"✅ [Arc] 제 {batch_start + 1}~{batch_end}번 아크 설계 완료",
                message=f"프로젝트: {self.ctx.current_project.name}\n설계된 아크 수: {batch_results_count}개",
                key_metrics={"완료 구간": f"{batch_start + 1} ~ {batch_end} Arc", "생성 수": batch_results_count},
            )
        except Exception as slack_err:
            self.ctx.ui.log(f"⚠️ [Slack] 알림 전송 실패 (무시하고 계속): {slack_err}")

    async def _complete_stage2_pipeline(self, *, target_arc_count: int | None) -> None:
        """Stage 2 전체 완료 후 tail side effect를 마무리한다."""
        self.ctx.ui.log("✨ [Success] 0124 매니페스토 기반 전술 설계 전 공정 완료.")
        if callable(getattr(self.ctx, "write_audit_summary", None)):
            self.ctx.write_audit_summary("stage2_complete")
        if target_arc_count is None and not self._stage2_should_suppress_prompts():
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
