"""
Bounded Stage3 semantic envelope builder helpers.
"""

from __future__ import annotations

import logging as _logging

from modules.core.constants import ContextLimits, smart_truncate


class Stage3EnvelopeBuilder:
    def __init__(self, orchestrator, *, anchor_selector_fn, history_cache_limit: int) -> None:
        self.orchestrator = orchestrator
        self.anchor_selector_fn = anchor_selector_fn
        self.history_cache_limit = history_cache_limit

    def build_blueprint_semantic_bundle(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprints,
        entity_registry,
        protagonist_name,
    ) -> dict[str, object]:
        blueprint_window = self.anchor_selector_fn(prev_blueprints)
        # `blueprint_window` is already bounded and anchor-aware; do not
        # collapse retrieval back to a blind recent tail before Stage3 planning.
        focus_window = list(blueprint_window) if blueprint_window else []
        smart_bundle = self.orchestrator._collect_stage3_smart_retrieval_bundle(
            working_ep=working_ep,
            arc_data=arc_data,
            prev_blueprints=focus_window,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
        )
        semantic_ctx = str(smart_bundle.get("semantic_ctx", "") or "")
        work_focus = dict(smart_bundle.get("work_focus") or {})
        plan = smart_bundle.get("plan")
        return self.build_legacy_blueprint_semantic_bundle_tail(
            working_ep=working_ep,
            arc_data=arc_data,
            arc_idx=arc_idx,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
            semantic_ctx=semantic_ctx,
            work_focus=work_focus,
            plan=plan,
            blueprint_window=blueprint_window,
            focus_window=focus_window,
        )

    def build_legacy_blueprint_semantic_bundle_tail(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        entity_registry,
        protagonist_name,
        semantic_ctx: str,
        work_focus: dict[str, object],
        plan,
        blueprint_window: list,
        focus_window: list,
    ) -> dict[str, object]:
        semantic_ctx = self.orchestrator._inject_stage3_treatment_block_context(
            semantic_ctx=semantic_ctx,
            working_ep=working_ep,
            arc_data=arc_data,
            arc_idx=arc_idx,
        )
        semantic_ctx = self.orchestrator._inject_stage3_timeline_advisory(
            semantic_ctx=semantic_ctx,
            arc_idx=arc_idx,
            arc_data=arc_data,
        )
        return self.orchestrator._finalize_stage3_blueprint_semantic_bundle(
            semantic_ctx=semantic_ctx,
            work_focus=work_focus,
            plan=plan,
            working_ep=working_ep,
            arc_data=arc_data,
            entity_registry=entity_registry,
            protagonist_name=protagonist_name,
            blueprint_window=blueprint_window,
            focus_window=focus_window,
        )

    def _build_prev_manuscript_text(self, *, working_ep: int) -> tuple[list[str], list[dict], str]:
        ctx = self.orchestrator.ctx
        prev_ms_for_bp: list[str] = []
        recent_manuscripts = ctx.current_project.db.get_recent_manuscripts(
            before_ep=working_ep,
            limit=self.history_cache_limit,
        )
        selected_manuscripts = self.anchor_selector_fn(recent_manuscripts)
        for ms_row in selected_manuscripts:
            ms_text = ms_row.get("content", "")
            ms_ep_num = ms_row.get("ep_num", 0)
            if ms_text:
                prev_ms_for_bp.append(f"━━━ 제{ms_ep_num}화 원고 ━━━\n{ms_text}")
        prev_ms_text_for_bp = "\n\n".join(prev_ms_for_bp) if prev_ms_for_bp else ""
        if len(prev_ms_text_for_bp) > ContextLimits.MAX_CONTEXT_CHARS:
            prev_ms_text_for_bp = smart_truncate(
                prev_ms_text_for_bp,
                max_chars=ContextLimits.MAX_CONTEXT_CHARS,
                head_chars=max(
                    0,
                    min(int(ContextLimits.MAX_CONTEXT_CHARS * 0.55), ContextLimits.MAX_CONTEXT_CHARS - 80),
                ),
            )
        return prev_ms_for_bp, recent_manuscripts, prev_ms_text_for_bp

    def _resolve_prev_hud(self):
        ctx = self.orchestrator.ctx
        if not (hasattr(ctx, "sys") and ctx.sys and hasattr(ctx.sys, "hud") and ctx.sys.hud):
            return None
        try:
            prev_hud = ctx.sys.hud.pro_root
            return prev_hud if isinstance(prev_hud, dict) else None
        except Exception:
            return None

    def run_blueprint_generation_handoff(
        self,
        *,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprint,
        protagonist_name,
        protagonist_config,
        entity_registry,
        semantic_bundle: dict[str, object],
    ):
        ctx = self.orchestrator.ctx
        from modules.core.spinners import StageSpinner

        blueprint_window = list(semantic_bundle.get("blueprint_window") or [])
        semantic_ctx = str(semantic_bundle.get("semantic_ctx", "") or "")

        with StageSpinner(3, f"제{working_ep}화") as spinner:
            prev_ms_for_bp, recent_manuscripts, prev_ms_text_for_bp = self._build_prev_manuscript_text(
                working_ep=working_ep
            )
            if prev_ms_for_bp:
                _logging.info(
                    " [V67] Blueprint용 이전 원고 %d/%d개 로드 (%d자)",
                    len(prev_ms_for_bp),
                    len(recent_manuscripts),
                    len(prev_ms_text_for_bp),
                )

            bp_prev_hud = self._resolve_prev_hud()

            spinner.update_detail(f"제{working_ep}화 · Blueprint 생성")
            ctx.ui.log(
                f"      ⏳ 제{working_ep}화 Blueprint 생성 시작 (최대 10회 시도)...",
                stage="stage3",
                component="blueprint_generation",
                ep_num=working_ep,
                arc_num=arc_idx,
                event_kind="progress",
            )
            ctx.ui.log(
                f"      ⏳ 제{working_ep}화 Blueprint 대기: ThreePhase runtime 호출 중 "
                f"(anchors={len(prev_ms_for_bp)}, window={len(blueprint_window)}, "
                f"semantic_ctx={len(semantic_ctx)}자)",
                stage="stage3",
                component="blueprint_generation",
                ep_num=working_ep,
                arc_num=arc_idx,
                event_kind="heartbeat",
                meta={
                    "anchor_count": len(prev_ms_for_bp),
                    "blueprint_window_count": len(blueprint_window),
                    "semantic_ctx_chars": len(semantic_ctx),
                    "prev_manuscript_chars": len(prev_ms_text_for_bp),
                    "wait_state": "three_phase_blueprint_runtime",
                },
            )
            blueprint, pipeline_result = ctx.agents["three_phase_bp"].generate(
                ep_num=working_ep,
                arc_data=arc_data,
                prev_blueprint=prev_blueprint,
                prev_blueprints=blueprint_window,
                max_retries=9,
                director=ctx.agents["director"],
                arc_idx=arc_idx,
                entity_registry=entity_registry,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                state_tracker=ctx.state_tracker,
                db=ctx.current_project.db,
                semantic_context=semantic_ctx,
                prev_manuscripts_text=prev_ms_text_for_bp,
                adversarial_self_play=ctx.adversarial_self_play,
                prev_hud=bp_prev_hud,
            )
            blueprint, pipeline_result = self.orchestrator._apply_stage3_dead_npc_precheck(
                blueprint=blueprint,
                pipeline_result=pipeline_result,
                working_ep=working_ep,
                arc_data=arc_data,
            )
            verdict = pipeline_result.get("final_verdict", "UNKNOWN")
            attempt_num = self.orchestrator._extract_stage3_attempt_num(pipeline_result)
            bp_score = pipeline_result.get(
                "last_score",
                pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0),
            )
            ctx.ui.log(
                f"      📊 제{working_ep}화 Blueprint 결과: {verdict} (attempt={attempt_num}, score={bp_score})",
                stage="stage3",
                component="blueprint_generation",
                ep_num=working_ep,
                arc_num=arc_idx,
                event_kind="result",
                meta={"verdict": verdict, "score": bp_score, "attempt_num": attempt_num},
            )
            selected_strategy = pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy")
            if selected_strategy:
                ctx.ui.log(
                    f"      └─ 선택 전략: {selected_strategy}",
                    stage="stage3",
                    component="blueprint_generation",
                    ep_num=working_ep,
                    arc_num=arc_idx,
                    event_kind="summary",
                    meta={"selected_strategy": selected_strategy},
                )
            for line in self.orchestrator._build_stage3_success_operator_lines(pipeline_result):
                ctx.ui.log(
                    line,
                    stage="stage3",
                    component="blueprint_generation",
                    ep_num=working_ep,
                    arc_num=arc_idx,
                    event_kind="summary",
                    meta={
                        "verdict": verdict,
                        "score": bp_score,
                        "selected_strategy": selected_strategy or "",
                    },
                )
            return blueprint, pipeline_result
