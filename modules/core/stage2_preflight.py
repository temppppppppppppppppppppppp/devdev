"""[B-1-8] Stage2 preflight analysis extracted from Stage2Orchestrator."""

import concurrent.futures
import json
import logging
import re
import threading
from dataclasses import dataclass, field

from modules.core.constants import smart_truncate
from modules.core.context_advisor import RetrievalSources, build_context_budget_ledger, build_context_observation
from modules.core.fact_ledger import summarize_fact_ledger_numbers_block
from modules.core.project_support import build_style_guide_summary
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.validation.threshold_helper import _threshold


@dataclass(slots=True)
class Stage2PatchModeDecision:
    fix_scope: str
    prev_score: int | float
    has_best_arc: bool
    use_inplace: bool
    use_patch: bool
    was_patch: bool


@dataclass(slots=True)
class Stage2PatchModeLabels:
    enter_log: str
    enter_ui: str
    fallback_log: str
    fallback_ui: str


@dataclass(slots=True)
class Stage2FourPhaseAttemptResult:
    four_phase_arc: dict | None = None
    pipeline_result: dict = field(default_factory=lambda: {"final_verdict": None})
    prev_score: int | float = 0
    was_patch: bool = False
    patch_fallback: bool = False


@dataclass(slots=True)
class Stage2FourPhaseGenerationPlan:
    fix_scope: str = ""
    prev_score: int | float = 0
    was_patch: bool = False
    use_inplace: bool = False
    use_patch: bool = False
    four_phase_arc: dict | None = None
    pipeline_result: dict = field(default_factory=lambda: {"final_verdict": None})


@dataclass(slots=True)
class Stage2FourPhaseGenerationRequest:
    attempt: int
    global_arc_no: int
    current_ep_start: int
    current_vol_strategy: dict
    enriched_block: dict
    all_refined_arcs: list
    bible_root: dict
    protagonist_name: str
    director_feedback_for_fourphase: str
    entity_registry_for_director: object
    previous_attempt: dict | None
    s2_spinner: object
    s2_vector_ctx: str
    generation_plan: Stage2FourPhaseGenerationPlan


@dataclass(slots=True)
class Stage2AnalystWeaponsPayload:
    analyst_weapons: dict = field(default_factory=dict)
    entity_registry_for_director: dict = field(default_factory=dict)


@dataclass(slots=True)
class Stage2ArcAnalysisContextPayload:
    enhanced_context: str
    narrative_enriched: bool = False


@dataclass(slots=True)
class Stage2FourPhasePassPayload:
    refined_arc: dict
    generation_method: str
    four_phase_passed: bool
    draft_validator_passed: bool
    consensus_passed: bool
    st_snapshot: dict | None


@dataclass(slots=True)
class Stage2FourPhaseTrackerPayload:
    st_snapshot: dict | None
    dead_npcs: list = field(default_factory=list)
    learned_skills: list = field(default_factory=list)
    npc_info: list = field(default_factory=list)


@dataclass(slots=True)
class Stage2FourPhaseCyclePayload:
    director_feedback_for_fourphase: str
    four_phase_passed: bool = False
    refined_arc: dict | None = None
    generation_method: str = "analyst"
    draft_validator_passed: bool = False
    consensus_passed: bool = False
    st_snapshot: dict | None = None
    was_patch: bool = False
    patch_fallback: bool = False
    prev_score: int | float = 0


@dataclass(slots=True)
class Stage2PreflightParallelPayload:
    arc_drive: dict = field(default_factory=dict)
    cached_preflight_injection: str = ""
    cached_preflight_result: dict = field(default_factory=dict)
    constraint_block: str = ""


class Stage2PreflightAnalysis:
    """State setup, arc analysis, and enrichment for Stage 2 preflight."""

    def __init__(self, host) -> None:
        self.host = host
        from modules.core.stage2_preflight_runtime import Stage2PreflightRuntime

        self.runtime = Stage2PreflightRuntime(self)

    @property
    def ctx(self):
        return self.host.ctx

    @staticmethod
    def _extract_npc_tokens(query: str) -> list[str]:
        """Extract candidate NPC tokens from retrieval query text."""
        if not query:
            return []

        stopwords = {
            "npc",
            "history",
            "context",
            "query",
            "past",
            "state",
            "change",
            "relation",
            "event",
            "continuity",
            "recent",
            "block",
            "theme",
            "arc",
        }
        tokens: list[str] = []
        for token in re.split(r"[\s,|/:;()\[\]{}]+", str(query)):
            text = token.strip()
            if len(text) < 2:
                continue
            if text.lower() in stopwords:
                continue
            if text not in tokens:
                tokens.append(text)
        return tokens[:20]

    @staticmethod
    def _collect_npc_roster(enriched_block: dict | None) -> list[str]:
        """Collect NPC candidates from Stage2 enriched block."""
        if not isinstance(enriched_block, dict):
            return []

        names: list[str] = []

        def _add_name(value) -> None:
            text = str(value or "").strip()
            if text and text not in names:
                names.append(text)

        def _consume(raw) -> None:
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        for key in ("name", "npc", "source", "target", "npc_name", "character"):
                            if item.get(key):
                                _add_name(item.get(key))
                    else:
                        _add_name(item)
            elif isinstance(raw, dict):
                for key in ("name", "npc", "source", "target", "npc_name", "character"):
                    if raw.get(key):
                        _add_name(raw.get(key))
            elif isinstance(raw, str):
                for part in re.split(r"[,\n/|]+", raw):
                    _add_name(part)

        for key in ("npc_roster", "assigned_npcs", "key_npcs", "characters", "npcs"):
            _consume(enriched_block.get(key))

        for container_key in ("state_changes", "status_shadow", "joint_docs"):
            container = enriched_block.get(container_key)
            if not isinstance(container, dict):
                continue
            for key in ("npc_deaths", "relationship_changes", "npc_injuries", "npcs", "characters"):
                _consume(container.get(key))

        return names[:50]

    @staticmethod
    def _build_stage3_to_2_reverse_feedback_fallback(
        arc_stage3_failures: list[dict],
        global_arc_no: int,
        *,
        status: str,
    ) -> str:
        reason_counts = {}
        detail_lines = []
        for failure in arc_stage3_failures:
            reason = str(failure.get("reason", "사유 미상") or "사유 미상")[:120]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            issue = str(failure.get("specific_issue", "") or "").strip()
            if issue and issue not in detail_lines:
                detail_lines.append(issue[:120])

        lines = [
            "",
            "=" * 50,
            f"[V60.9 Arc {global_arc_no} Blueprint 반복 실패 - fallback]",
            "=" * 50,
            f"Stage3->2 reverse feedback helper 상태: {status}",
            f"Blueprint 설계 실패 {len(arc_stage3_failures)}회 누적.",
            "다음 Arc 재시도에서는 아래 실패 사유를 직접 구조 제약으로 승격하세요.",
        ]
        for reason, count in sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))[:3]:
            lines.append(f"  - {reason}: {count}회")
        if detail_lines:
            lines.append("")
            lines.append("반복된 구체 지시:")
            for issue in detail_lines[:3]:
                lines.append(f"  - {issue}")
        lines.extend(
            [
                "",
                "권장 조치:",
                "  1. 핵심 갈등 축을 줄여 Blueprint 의존성을 단순화할 것",
                "  2. 아이템/NPC 배치 시점을 명시해 설정 충돌을 줄일 것",
                "  3. 직전 실패 사유가 반복된 장면은 Arc 구조에서 제거 또는 재배치할 것",
                "",
                "=" * 50,
                "",
            ]
        )
        return "\n".join(lines)

    def _execute_stage2_retrieval_plan(
        self,
        plan,
        *,
        current_ep: int,
        npc_roster: list[str] | None = None,
        current_arc_no: int | None = None,
        protagonist_name: str = "",
    ) -> str:
        """Execute Stage2 retrieval plan and return merged context text."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return ""

        max_results = int(_threshold("context.vector_max_results_s2", 40))
        sections: list[str] = []
        ordered_slots = sorted(plan.slots, key=lambda slot: getattr(slot, "priority", 2))
        _VM = RetrievalSources.VEC_MEMORY
        vec_slot_count = sum(1 for slot in ordered_slots if str(getattr(slot, "source", _VM) or _VM) == _VM)
        fallback_names = [str(name).strip() for name in (npc_roster or []) if str(name).strip()]

        for slot in ordered_slots:
            source = str(getattr(slot, "source", _VM) or _VM)
            category = str(getattr(slot, "category", "context") or "context")
            query_text = str(getattr(slot, "query", "") or "").strip()
            if not query_text:
                continue

            try:
                if source == RetrievalSources.DB_NPC_HISTORY:
                    npc_names = fallback_names or self._extract_npc_tokens(query_text)
                    result = memory.retrieve_npc_context(
                        npc_names=npc_names,
                        current_ep=current_ep,
                        max_results=max_results,
                    )
                elif source == RetrievalSources.DB_NPC_RELATIONSHIP:
                    npc_names = fallback_names or self._extract_npc_tokens(query_text)
                    result = self._build_relationship_context(
                        npc_names=npc_names,
                        protagonist_name=protagonist_name,
                    )
                else:
                    # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
                    _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
                    if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                        result = memory.retrieve_hybrid_context(
                            query=query_text,
                            current_ep=current_ep,
                            dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                            sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                            rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                        )
                    elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                        _fts = memory._fts_search(query_text, current_ep, n_results=max_results)
                        result = (
                            "\n\n".join(f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}" for r in _fts)
                            if _fts
                            else ""
                        )
                    elif vec_slot_count <= 1:
                        result = memory.retrieve_high_res_context(
                            query_text,
                            current_ep,
                            n_results=max_results,
                        )
                    else:
                        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
                            logging.warning(
                                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                                _retrieval_mode,
                            )
                        result = memory.retrieve_multi_query_context(
                            queries=[query_text],
                            current_ep=current_ep,
                            n_per_query=3,
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                        )
            except Exception as exc:  # OPTIONAL: retrieval failure should not block generation
                audit_cb = getattr(self.ctx, "audit_event", None)
                if callable(audit_cb):
                    audit_cb("s2_vector_search_failed", str(exc)[:100])
                continue

            if not result:
                continue

            slot_max = int(getattr(slot, "max_chars", 0) or 0)
            if slot_max > 0 and len(result) > slot_max:
                result = smart_truncate(
                    result,
                    max_chars=slot_max,
                    head_chars=max(0, min(int(slot_max * 0.55), slot_max - 80)),
                )

            sections.append(f"[SC:{category}]\n{result}")

        logging.info(f"[SC] stage2 retrieval: {len(sections)} sections from {len(plan.slots)} slots")
        joined = "\n\n".join(sections)
        budget = int(getattr(plan, "total_budget_chars", 0) or 0)
        if budget > 0 and len(joined) > budget:
            joined = smart_truncate(
                joined,
                max_chars=budget,
                head_chars=max(0, min(int(budget * 0.55), budget - 80)),
            )
            logging.info(f"[SC] stage2 budget truncation → {budget}자")
        return joined

    def _build_relationship_context(
        self,
        *,
        npc_names: list[str],
        protagonist_name: str = "",
        limit: int = 6,
    ) -> str:
        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        if not db or not hasattr(db, "get_relationship_history"):
            return ""

        clean_names = [str(name).strip() for name in (npc_names or []) if str(name).strip()]
        if protagonist_name:
            protagonist_name = str(protagonist_name).strip()

        seen: set[tuple[str, str]] = set()
        lines: list[str] = []

        def _add_pair(n1: str, n2: str) -> None:
            if not n1 or not n2 or n1 == n2:
                return
            pair = tuple(sorted((n1, n2)))
            if pair in seen:
                return
            seen.add(pair)
            try:
                rows = db.get_relationship_history(pair[0], pair[1], limit=3)
            except Exception as rel_err:
                logging.debug("[Stage2Preflight] relationship history 조회 실패 (비치명): %s", rel_err)
                rows = []
            if not rows:
                return
            for row in rows[:2]:
                if not isinstance(row, dict):
                    continue
                old_relation = str(row.get("old_relation", "") or "").strip()
                new_relation = str(row.get("new_relation", "") or "").strip()
                change_ep = row.get("change_ep", "?")
                transition = " -> ".join(part for part in (old_relation, new_relation) if part)
                if transition:
                    lines.append(f"EP{change_ep} {pair[0]}-{pair[1]}: {transition}")

        if protagonist_name:
            for name in clean_names[:5]:
                _add_pair(protagonist_name, name)
        for idx, name in enumerate(clean_names[:4]):
            for other in clean_names[idx + 1 : idx + 4]:
                _add_pair(name, other)

        return "\n".join(lines[:limit])

    @staticmethod
    def _summarize_retrieval_sources(plan) -> dict[str, int]:
        counts: dict[str, int] = {}
        if not plan or not getattr(plan, "slots", None):
            return counts
        for slot in getattr(plan, "slots", []) or []:
            source = str(getattr(slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY)
            counts[source] = counts.get(source, 0) + 1
        return counts

    def _record_retrieval_observation(self, *, ep_num: int, stage: str, observation: dict) -> None:
        dashboard = getattr(self.ctx, "quality_dashboard", None)
        if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
            return
        try:
            dashboard.record_retrieval_observation(ep_num=ep_num, stage=stage, observation=observation)
        except Exception as exc:
            logging.debug("[Stage2Preflight] retrieval observation record failed: %s", exc)

    def _build_fact_ledger_context(self, *, max_items: int = 10) -> str:
        """Stage 2 Arc 생성기에 전달할 핵심 수치 요약."""
        try:
            db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if not db:
                return ""
            ledger = db.load_anchor("fact_ledger")
            return summarize_fact_ledger_numbers_block(
                ledger,
                header="[팩트 원장 핵심 수치]",
                max_items=max_items,
            )
        except Exception as fact_err:
            logging.debug("[TF-DB-B1] Stage2 FactLedger 요약 실패 (비치명): %s", fact_err)
            return ""

    def _build_style_guide_summary(self, *, max_chars: int = 1200) -> str:
        """Stage 2 Analyst용 compact StyleGuide 요약."""
        project = getattr(self.ctx, "current_project", None)
        return build_style_guide_summary(
            project,
            heading="[문체 가이드 요약]",
            max_chars=max_chars,
            include_dialogue_ratio=True,
            secondary_style_key="description_style",
            secondary_style_label="묘사",
        )

    def _build_protagonist_config_summary(self) -> str:
        """Stage 2 enhanced_context 상단용 compact protagonist_config 요약."""
        project = getattr(self.ctx, "current_project", None)
        if project is None:
            return ""

        master_bible = getattr(project, "master_bible", None)
        if not isinstance(master_bible, dict):
            return ""

        bible_root = master_bible.get("MasterBible", master_bible)
        protagonist_config = bible_root.get("protagonist_config", {}) if isinstance(bible_root, dict) else {}
        if not isinstance(protagonist_config, dict) or not protagonist_config:
            return ""

        world_origin = str(protagonist_config.get("world_origin", "") or "").strip()
        incarnation_type = str(protagonist_config.get("incarnation_type", "") or "").strip()
        pov = str(protagonist_config.get("pov", "") or "").strip()
        external_pov_insert_policy = str(protagonist_config.get("external_pov_insert_policy", "") or "").strip()

        if not any([world_origin, incarnation_type, pov, external_pov_insert_policy]):
            return ""

        lines = ["[주인공 설정 요약]"]
        parts = []
        if world_origin:
            parts.append(f"세계 출신={world_origin}")
        if incarnation_type:
            parts.append(f"환생 유형={incarnation_type}")
        if pov:
            parts.append(f"시점={pov}")
        if external_pov_insert_policy:
            parts.append(f"외부 시점 삽입={external_pov_insert_policy}")
        if parts:
            lines.append("- " + ", ".join(parts))
        if pov == "1인칭":
            lines.append("- 1인칭 유지: 주인공 부재 장면/타인 내면 직서술 금지")
        elif pov == "3인칭":
            lines.append("- 3인칭 유지: 주인공 중심 시점, 전지적 개입 최소화")

        return "\n".join(lines)

    def _compose_work_focus_text(self, enriched_block: dict | None, *, current_vol_strategy: dict | None = None) -> str:
        if not isinstance(enriched_block, dict):
            return ""

        parts: list[str] = []
        for key in ("block_theme", "tactical_doc", "arc_tactical", "constraint_summary"):
            value = str(enriched_block.get(key, "") or "").strip()
            if value:
                parts.append(value)

        plot_suspension = enriched_block.get("plot_suspension", []) or []
        if isinstance(plot_suspension, list) and plot_suspension:
            parts.append(" ".join(str(item).strip() for item in plot_suspension[:4] if str(item).strip()))

        npc_roster = self._collect_npc_roster(enriched_block)
        if npc_roster:
            parts.append(" ".join(npc_roster[:8]))

        for container_key in ("joint_docs", "status_shadow"):
            container = enriched_block.get(container_key)
            if not isinstance(container, dict):
                continue
            for key in ("constraint_summary", "core_conflict", "status_summary", "active_threads"):
                value = container.get(key)
                if isinstance(value, list):
                    text = " ".join(str(item).strip() for item in value[:4] if str(item).strip())
                else:
                    text = str(value or "").strip()
                if text:
                    parts.append(text)

        if isinstance(current_vol_strategy, dict):
            strategy_doc = str(current_vol_strategy.get("strategy_doc", "") or "").strip()
            if strategy_doc:
                parts.append(strategy_doc[:400])

        combined = "\n".join(part for part in parts if part)
        return combined[:1800]

    def _resolve_work_retrieval_focus(
        self,
        enriched_block: dict | None,
        *,
        current_vol_strategy: dict | None = None,
    ) -> dict[str, object]:
        guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if not guard or not hasattr(guard, "select_retrieval_focus"):
            return {}

        focus_text = self._compose_work_focus_text(enriched_block, current_vol_strategy=current_vol_strategy)
        if not focus_text:
            return {}

        try:
            focus = guard.select_retrieval_focus(stage="block", focus_text=focus_text)
        except Exception as focus_err:
            logging.debug("[Stage2Preflight] work_focus 선택 실패 (비치명): %s", focus_err)
            return {}

        return focus if isinstance(focus, dict) else {}

    def _build_work_identity_slot_summary(
        self,
        focus: dict[str, object],
        enriched_block: dict | None,
        *,
        protagonist_name: str = "",
        max_chars: int = 1200,
    ) -> str:
        if not isinstance(focus, dict) or not focus:
            return ""

        tracking_slots = [str(item).strip() for item in (focus.get("tracking_slots") or []) if str(item).strip()]
        scene_engines = [
            str(item).strip() for item in (focus.get("mandatory_scene_engines") or []) if str(item).strip()
        ]
        registry_profiles = [item for item in (focus.get("registry_profiles") or []) if isinstance(item, dict)]

        if not any([tracking_slots, scene_engines, registry_profiles]):
            return ""

        lines = ["[작품 추적 슬롯 요약]"]
        if tracking_slots:
            lines.append(f"- 이번 블록 우선 tracking_slots: {', '.join(tracking_slots[:3])}")
        if scene_engines:
            lines.append(f"- 이번 블록 scene engines: {', '.join(scene_engines[:2])}")
        if registry_profiles:
            rendered_profiles = []
            for profile in registry_profiles[:2]:
                name = str(profile.get("name", "") or "").strip()
                fields = [str(item).strip() for item in (profile.get("required_fields") or []) if str(item).strip()]
                if not name:
                    continue
                rendered_profiles.append(name + (f"(fields={', '.join(fields[:4])})" if fields else ""))
            if rendered_profiles:
                lines.append(f"- registry focus: {', '.join(rendered_profiles)}")

        if isinstance(enriched_block, dict):
            block_theme = str(enriched_block.get("block_theme", "") or "").strip()
            if block_theme:
                lines.append(f"- 현재 블록 중심축: {block_theme[:140]}")
            constraint_summary = str(enriched_block.get("constraint_summary", "") or "").strip()
            if constraint_summary:
                lines.append(f"- 갈등 요약: {constraint_summary[:160]}")

        try:
            focus_text = " ".join(
                [
                    ", ".join(tracking_slots),
                    ", ".join(scene_engines),
                    " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                    str((enriched_block or {}).get("constraint_summary", "") or ""),
                    str((enriched_block or {}).get("block_theme", "") or ""),
                ]
            ).strip()
            broker = SemanticQueryBroker(
                db=getattr(getattr(self.ctx, "current_project", None), "db", None),
                world_state=getattr(self.ctx, "world_state", None),
                fact_ledger=getattr(self.ctx, "fact_ledger", None),
                state_tracker=getattr(self.ctx, "state_tracker", None),
                protagonist_name=protagonist_name,
            )
            relation_slice = broker.build_relation_slice(focus_text=focus_text, max_chars=420)
            if relation_slice:
                lines.append(relation_slice)
        except Exception as broker_err:
            logging.debug("[Stage2Preflight] semantic relation slice 생성 실패 (비치명): %s", broker_err)

        return smart_truncate("\n".join(lines), max_chars=max_chars, head_chars=max_chars // 2)

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
        genre: str = "",
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

        # [S2-P1-5] perf_timer 공유 상태 보호용 Lock
        _perf_lock = threading.Lock()

        def _compute_arc_drive() -> dict:
            return self._compute_arc_drive(
                arcs_source=arcs_source,
                arc_idx=arc_idx,
                lack_report=lack_report,
                grand_obj=grand_obj,
                global_arc_no=global_arc_no,
                perf_lock=_perf_lock,
            )

        def _compute_preflight() -> tuple:
            return self._compute_preflight(
                all_refined_arcs=all_refined_arcs,
                global_arc_no=global_arc_no,
                genre=genre,
                perf_lock=_perf_lock,
            )

        # [S2-I1] constraint_db 수집을 arc_drive/preflight와 병렬 실행
        def _compute_constraint_block() -> str:
            return self._compute_constraint_block(
                constraint_db=constraint_db,
                global_arc_no=global_arc_no,
            )

        _parallel_payload = self._run_preflight_parallel_tasks(
            global_arc_no=global_arc_no,
            compute_arc_drive_fn=_compute_arc_drive,
            compute_preflight_fn=_compute_preflight,
            compute_constraint_block_fn=_compute_constraint_block,
        )
        arc_drive = _parallel_payload.arc_drive
        _cached_preflight_injection = _parallel_payload.cached_preflight_injection
        _cached_preflight_result = _parallel_payload.cached_preflight_result
        constraint_block = _parallel_payload.constraint_block

        if _cached_preflight_result:
            logging.info("✅ [V66.1] arc_drive + preflight + constraint 병렬 완료")
            logging.info(f"- 아이템 타임라인: {len(_cached_preflight_result.get('item_timeline', []))}개")
            logging.info(f"- 금지 사항: {len(_cached_preflight_result.get('absolute_prohibitions', []))}개")
            logging.info(f"- 관계 맵: {len(_cached_preflight_result.get('relationship_map', {}))}명")

        passed = False
        current_feedback = ""

        # [S2-I1] constraint_block 로깅 (병렬 결과)
        if constraint_block:
            self.ctx.ui.log(f"      🔒 [V49.4] Arc {global_arc_no} 제약 조건 주입됨")

        constraint_block = self._apply_constraint_compiler_block(
            all_refined_arcs=all_refined_arcs,
            constraint_block=constraint_block,
        )

        # [V60.77] FourPhase-Director 대면 루프
        attempt = 0
        max_attempts = int(_threshold("retry.analyst_max_attempts", 5))
        director_feedback_for_fourphase = ""

        _st_snapshot = None  # [V70] StateTracker 롤백용 스냅샷

        return {
            "arc_drive": arc_drive,
            "cached_preflight_injection": _cached_preflight_injection,
            "cached_preflight_result": _cached_preflight_result,
            "passed": passed,
            "current_feedback": current_feedback,
            "constraint_block": constraint_block,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": _st_snapshot,
        }

    def _compute_arc_drive(
        self,
        *,
        arcs_source: list,
        arc_idx: int,
        lack_report: dict,
        grand_obj: str,
        global_arc_no: int,
        perf_lock: threading.Lock,
    ) -> dict:
        """Weaver 욕망 드라이브 생성 (LLM)."""
        try:
            with perf_lock:
                self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_arc_drive")
        except Exception as _e:
            logging.debug("[Stage2Preflight] perf_timer arc_drive start 실패 (무시): %s", _e)
        try:
            return self.ctx.agents["weaver"].generate_arc_drive(
                current_arc_dna=arcs_source[arc_idx],
                analyst_lack_report=lack_report,
                grand_objective=grand_obj,
            )
        except Exception as weaver_err:
            logging.warning("[Weaver] 욕망 드라이브 생성 실패: %s", weaver_err)
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "weaver_error",
                    "generate_arc_drive failed",
                    {"arc_no": global_arc_no, "error": str(weaver_err)},
                )
            return {"desire_vector": "생성 실패", "status": "error"}
        finally:
            try:
                with perf_lock:
                    self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_arc_drive")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer arc_drive stop 실패 (무시): %s", _e)

    def _compute_preflight(
        self,
        *,
        all_refined_arcs: list,
        global_arc_no: int,
        genre: str,
        perf_lock: threading.Lock,
    ) -> tuple[str, dict]:
        """Preflight 분석 (LLM) — 결과를 attempt 루프에서 재사용."""
        try:
            with perf_lock:
                self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_analysis")
        except Exception as _e:
            logging.debug("[Stage2Preflight] perf_timer preflight start 실패 (무시): %s", _e)
        _pf_injection = ""
        _pf_result = None
        try:
            if "preflight" in self.ctx.agents and all_refined_arcs:
                try:
                    _usable_preflight_arcs = []
                    _skipped_hollow_arc_nos = []
                    for _idx, _arc in enumerate(all_refined_arcs, start=1):
                        if not isinstance(_arc, dict):
                            _skipped_hollow_arc_nos.append(_idx)
                            continue
                        _tactical = _arc.get("tactical_doc")
                        if isinstance(_tactical, dict):
                            try:
                                _tactical = json.dumps(_tactical, ensure_ascii=False)
                            except Exception:
                                _tactical = str(_tactical)
                        if not str(_tactical or "").strip():
                            _skipped_hollow_arc_nos.append(_arc.get("arc_no", _idx))
                            continue
                        _usable_preflight_arcs.append(_arc)
                    if _skipped_hollow_arc_nos:
                        logging.warning(
                            "[Preflight] hollow previous arcs skipped before analyze: %s",
                            _skipped_hollow_arc_nos,
                        )
                        try:
                            self.ctx.ui.log(
                                f"      [Preflight] hollow previous arcs skipped: {_skipped_hollow_arc_nos}"
                            )
                        except Exception:
                            pass
                        if callable(getattr(self.ctx, "audit_event", None)):
                            self.ctx.audit_event(
                                "preflight_hollow_prev_arcs_skipped",
                                "Preflight skipped hollow previous arcs",
                                {
                                    "arc_no": global_arc_no,
                                    "skipped_arc_nos": list(_skipped_hollow_arc_nos),
                                    "usable_prev_arc_count": len(_usable_preflight_arcs),
                                    "total_prev_arc_count": len(all_refined_arcs),
                                },
                            )
                    _resolved_plots = ""
                    if self.ctx.state_tracker:
                        _resolved_plots = self.ctx.state_tracker.get_resolved_plots_summary()
                    _pf_result = self.ctx.agents["preflight"].analyze(
                        _usable_preflight_arcs, resolved_plots_summary=_resolved_plots
                    )
                    if _pf_result:
                        if _skipped_hollow_arc_nos and isinstance(_pf_result, dict):
                            _pf_result["_input_hygiene"] = {
                                "skipped_hollow_arc_nos": list(_skipped_hollow_arc_nos),
                                "usable_prev_arc_count": len(_usable_preflight_arcs),
                                "total_prev_arc_count": len(all_refined_arcs),
                            }
                        _last_arc = _usable_preflight_arcs[-1] if _usable_preflight_arcs else {}
                        _actual_injuries = (
                            _last_arc.get("state_constraints", {}).get("arc_end_state", {}).get("injuries") or "없음"
                        )
                        _ws = _pf_result.setdefault("world_state", {})
                        _ps = _ws.setdefault("protagonist_status", {})
                        _ps["injuries"] = _actual_injuries
                        _pf_injection = self.ctx.agents["preflight"].generate_analyst_injection(
                            _pf_result, genre=genre
                        )
                except Exception as pf_err:
                    logging.warning(f" [Preflight] 스킵: {str(pf_err)[:50]}")
            return _pf_injection, _pf_result
        finally:
            try:
                with perf_lock:
                    self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_analysis")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer preflight stop 실패 (무시): %s", _e)

    def _compute_constraint_block(self, *, constraint_db, global_arc_no: int) -> str:
        """ConstraintDB 제약 블록 생성 (독립, LLM 미사용)."""
        try:
            return constraint_db.generate_constraint_block(global_arc_no) or ""
        except Exception as _cb_err:
            logging.warning(f"[S2-I1] constraint_block 생성 실패 (비차단): {_cb_err}")
            return ""

    def _run_preflight_parallel_tasks(
        self,
        *,
        global_arc_no: int,
        compute_arc_drive_fn,
        compute_preflight_fn,
        compute_constraint_block_fn,
    ) -> Stage2PreflightParallelPayload:
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_parallel")
        except Exception as _e:
            logging.debug("[Stage2Preflight] perf_timer parallel start 실패 (무시): %s", _e)
        payload = Stage2PreflightParallelPayload()
        _parallel_exec = None
        self.ctx.ui.log("      ⏳ [Preflight] 병렬 분석 시작 (arc_drive + preflight + constraint)...")
        try:
            _parallel_exec = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            _fut_drive = _parallel_exec.submit(compute_arc_drive_fn)
            _fut_preflight = _parallel_exec.submit(compute_preflight_fn)
            _fut_constraint = _parallel_exec.submit(compute_constraint_block_fn)
            try:
                payload.arc_drive = _fut_drive.result(timeout=300)
                self.ctx.ui.log("      ✅ [Preflight] arc_drive 완료")
            except Exception as _drv_err:
                logging.warning("[Preflight] arc_drive 타임아웃/실패: %s", str(_drv_err)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] arc_drive 실패")
            try:
                (
                    payload.cached_preflight_injection,
                    payload.cached_preflight_result,
                ) = _fut_preflight.result(timeout=300)
                self.ctx.ui.log("      ✅ [Preflight] preflight 완료")
            except Exception as _pf_err2:
                logging.warning("[Preflight] preflight 타임아웃/실패: %s", str(_pf_err2)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] preflight 실패")
            try:
                payload.constraint_block = _fut_constraint.result(timeout=60)
                self.ctx.ui.log("      ✅ [Preflight] constraint 완료")
            except Exception as _con_err:
                logging.warning("[Preflight] constraint 타임아웃/실패: %s", str(_con_err)[:80])
                self.ctx.ui.log("      ⚠️ [Preflight] constraint 실패")
        except Exception as _pf_err:
            if _parallel_exec is not None:
                try:
                    _parallel_exec.shutdown(wait=False, cancel_futures=True)
                except Exception as _e:
                    logging.debug("[Stage2Preflight] executor shutdown(err path) 실패 (무시): %s", _e)
            logging.warning(f" [Preflight] 병렬 실행 타임아웃/오류 (비치명): {str(_pf_err)[:80]}")
        finally:
            if _parallel_exec is not None:
                try:
                    _parallel_exec.shutdown(wait=False, cancel_futures=True)
                except Exception as _e:
                    logging.debug("[Stage2Preflight] executor shutdown(finally) 실패 (무시): %s", _e)
            try:
                self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_parallel")
            except Exception as _e:
                logging.debug("[Stage2Preflight] perf_timer parallel stop 실패 (무시): %s", _e)
        return payload

    def _apply_constraint_compiler_block(self, *, all_refined_arcs: list, constraint_block: str) -> str:
        if not self.ctx.constraint_compiler or not all_refined_arcs:
            return constraint_block
        try:
            state_result = self._extract_constraint_compiler_state(all_refined_arcs=all_refined_arcs)
            resolved_plots = getattr(self.ctx.state_tracker, "resolved_plots", []) if self.ctx.state_tracker else []
            compiled_constraints = self.ctx.constraint_compiler.compile(
                all_refined_arcs,
                state_result,
                resolved_plots=resolved_plots,
            )
            constraint_block = compiled_constraints + "\n\n" + (constraint_block or "")
            self.ctx.ui.log("      📋 [V60.11] ConstraintCompiler 체크리스트 생성 완료")
            if resolved_plots and len(resolved_plots) >= 2 and self.ctx.semantic_plot_guard:
                try:
                    self.ctx.semantic_plot_guard.index_resolved_plots(resolved_plots)
                except Exception as e:  # [V64.P4] SPG init — OPTIONAL
                    if callable(getattr(self.ctx, "audit_event", None)):
                        self.ctx.audit_event("semantic_plot_guard_index_failed", str(e)[:100])
        except Exception as cc_err:
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("v60_11_constraint_compiler_error", str(cc_err)[:100])
        return constraint_block

    def _extract_constraint_compiler_state(self, *, all_refined_arcs: list):
        if "state_extractor" not in self.ctx.agents:
            return None
        try:
            arc_count = len(all_refined_arcs)
            if self.ctx.cumulative_state_cache is not None and self.ctx.cumulative_state_cache_key == arc_count:
                return self.ctx.cumulative_state_cache
            self.ctx.ui.log("      ⏳ [StateExtractor] 누적 상태 추출 중...")
            state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
            self.ctx.ui.log("      ✅ [StateExtractor] 누적 상태 추출 완료")
            self.ctx.cumulative_state_cache = state_result
            self.ctx.cumulative_state_cache_key = arc_count
            if self.ctx.sync_cache_key_to_app:
                self.ctx.sync_cache_key_to_app(arc_count, cache=state_result)
            return state_result
        except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
            logging.warning(
                f"[V64.P4] CRITICAL: extract_cumulative_state 실패 (NPC 검증 약화): {e}",
                exc_info=True,
            )
            self.ctx.ui.log(f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("critical_state_extraction_failed", str(e)[:200])
            return None

    def _apply_retry_focus_mode(
        self,
        *,
        attempt: int,
        current_feedback: str,
        constraint_block: str,
        cached_preflight_injection: str,
        all_refined_arcs: list,
        protagonist_name: str,
        enhanced_context: str,
    ) -> str:
        is_retry = attempt > 0 and current_feedback
        if not is_retry:
            return enhanced_context

        _preserved_constraints = ""
        if constraint_block:
            _preserved_constraints += constraint_block
        if cached_preflight_injection:
            _preserved_constraints += (
                ("\n\n" + cached_preflight_injection) if _preserved_constraints else cached_preflight_injection
            )

        if callable(getattr(self.ctx, "build_minimal_arc_context", None)):
            minimal_prev_context = self.ctx.build_minimal_arc_context(
                all_refined_arcs, protagonist_name or "주인공"
            )
        else:
            minimal_prev_context = smart_truncate(
                enhanced_context, max_chars=15000, head_chars=8250
            )  # [Phase3-B] retry fallback keeps recent tail

        if _preserved_constraints:
            enhanced_context = f"{current_feedback}\n\n{_preserved_constraints}\n\n{minimal_prev_context}"
        else:
            enhanced_context = f"{current_feedback}\n\n{minimal_prev_context}"
        context_size = len(enhanced_context)
        self.ctx.ui.log(f"      📢 [V60.21] Focus Mode 활성화 - 컨텍스트 {context_size:,}자 (제약 보존)")
        return enhanced_context

    @staticmethod
    def _build_patch_feedback(previous_attempt: dict) -> str:
        patch_feedback = previous_attempt.get("rejection_reason", "")
        selection_reason = previous_attempt.get("selection_reason", "")
        score_breakdown = previous_attempt.get("score_breakdown", {})
        validation_warnings = previous_attempt.get("validation_warnings", [])

        if selection_reason:
            patch_feedback += f"\n[선택/거절 사유]\n{selection_reason}"
        if isinstance(score_breakdown, dict) and score_breakdown:
            score_summary = ", ".join(
                f"{k}={v}" for k, v in score_breakdown.items() if isinstance(v, int | float)
            )
            if score_summary:
                patch_feedback += f"\n[점수 분해]\n{score_summary}"
        if isinstance(validation_warnings, list) and validation_warnings:
            patch_feedback += "\n[검증 경고]\n" + "\n".join(
                f"- {warning}" for warning in validation_warnings[:10] if isinstance(warning, str)
            )

        fix_scope_reasoning = previous_attempt.get("fix_scope_reasoning", "")
        if fix_scope_reasoning:
            patch_feedback += f"\n[수정 범위 근거]\n{fix_scope_reasoning}"
        return patch_feedback

    @staticmethod
    def _resolve_patch_mode(previous_attempt: dict | None) -> Stage2PatchModeDecision:
        fix_scope = previous_attempt.get("fix_scope", "") if previous_attempt else ""
        prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
        has_best_arc = bool(previous_attempt and previous_attempt.get("best_arc"))
        use_inplace = has_best_arc and (fix_scope == "inplace")
        use_patch = has_best_arc and (fix_scope in ("inplace", "partial"))
        return Stage2PatchModeDecision(
            fix_scope=fix_scope,
            prev_score=prev_score,
            has_best_arc=has_best_arc,
            use_inplace=use_inplace,
            use_patch=use_patch,
            was_patch=bool(use_patch),
        )

    def _build_stage2_vector_context(
        self,
        *,
        global_arc_no: int,
        current_ep_start: int,
        enriched_block: dict,
        current_vol_strategy: dict,
        protagonist_name: str,
    ) -> str:
        s2_vector_ctx = ""
        retrieval_plan = None
        use_advisor_path = False
        npc_roster: list[str] = []
        work_focus = self._resolve_work_retrieval_focus(
            enriched_block,
            current_vol_strategy=current_vol_strategy,
        )
        work_slot_summary = self._build_work_identity_slot_summary(
            work_focus,
            enriched_block,
            protagonist_name=protagonist_name,
        )

        try:
            if self.ctx.memory and current_ep_start > 1:
                advisor = getattr(self.ctx, "context_advisor", None)
                smart_enabled = bool(_threshold("smart_retrieval.enabled", False)) and bool(
                    _threshold("smart_retrieval.stage2_enabled", False)
                )
                if advisor and smart_enabled:
                    try:
                        npc_roster = self._collect_npc_roster(enriched_block)
                        retrieval_plan = advisor.plan_stage2_retrieval(
                            arc_data=enriched_block or {},
                            current_ep=current_ep_start,
                            npc_roster=npc_roster,
                            work_focus=work_focus,
                        )
                        perf_key = f"sc_stage2_arc{global_arc_no}_retrieval"
                        try:
                            self.ctx.perf_timer.start(perf_key)
                        except Exception as perf_err:
                            logging.debug("[Stage2Preflight] SC perf_timer start 실패 (무시): %s", perf_err)
                        try:
                            s2_vector_ctx = self._execute_stage2_retrieval_plan(
                                retrieval_plan,
                                current_ep=current_ep_start,
                                npc_roster=npc_roster,
                                current_arc_no=global_arc_no,
                                protagonist_name=protagonist_name,
                            )
                        finally:
                            try:
                                self.ctx.perf_timer.stop(perf_key)
                            except Exception as perf_err:
                                logging.debug("[Stage2Preflight] SC perf_timer stop 실패 (무시): %s", perf_err)
                        use_advisor_path = True
                    except Exception as exc:
                        logging.warning("[S2-SC] advisor 실패, legacy fallback: %s", exc)
                        audit_cb = getattr(self.ctx, "audit_event", None)
                        if callable(audit_cb):
                            audit_cb("s2_vector_search_failed", str(exc)[:100])

                if not use_advisor_path:
                    s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
                        enriched_block.get("block_theme", ""),
                        current_ep_start,
                        n_results=int(_threshold("context.vector_max_results_s2", 40)),
                    )
        except Exception as exc:
            audit_cb = getattr(self.ctx, "audit_event", None)
            if callable(audit_cb):
                audit_cb("s2_vector_search_failed", str(exc)[:100])

        fact_ledger_context = self._build_fact_ledger_context(max_items=10)
        if fact_ledger_context:
            s2_vector_ctx = fact_ledger_context + ("\n\n" + s2_vector_ctx if s2_vector_ctx else "")
        if work_slot_summary:
            s2_vector_ctx = work_slot_summary + ("\n\n" + s2_vector_ctx if s2_vector_ctx else "")

        source_counts = self._summarize_retrieval_sources(retrieval_plan)
        if not source_counts and s2_vector_ctx and not use_advisor_path:
            source_counts = {"legacy_high_res": 1}

        coverage_warnings: list[str] = []
        if work_focus and not work_slot_summary:
            coverage_warnings.append("missing_work_slot_summary")
        if (
            work_focus
            and retrieval_plan
            and not any(
                str(getattr(slot, "category", "")).startswith("work_")
                for slot in (getattr(retrieval_plan, "slots", []) or [])
            )
        ):
            coverage_warnings.append("work_focus_without_slots")
        if (
            source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0
            and "[관계 의미 질의]" not in s2_vector_ctx
        ):
            coverage_warnings.append("missing_relation_slice")

        stage2_budget_cap = int(getattr(retrieval_plan, "total_budget_chars", 0) or 0)
        stage2_budget_ledger = build_context_budget_ledger(
            stage="stage2",
            configured_cap=stage2_budget_cap,
            effective_cap=stage2_budget_cap,
            consumed_chars=len(s2_vector_ctx),
            overflow_chars=max(0, len(s2_vector_ctx) - stage2_budget_cap) if stage2_budget_cap > 0 else 0,
        )
        self._record_retrieval_observation(
            ep_num=current_ep_start,
            stage="stage2",
            observation=build_context_observation(
                stage="stage2",
                work_focus=work_focus,
                retrieval_plan=retrieval_plan,
                source_counts=source_counts,
                coverage_warnings=coverage_warnings,
                advisor_path_used=use_advisor_path,
                work_slot_summary_present=bool(work_slot_summary),
                work_slot_summary_included=bool(
                    work_slot_summary and "[작품 추적 슬롯 요약]" in s2_vector_ctx
                ),
                relation_slice_included="[관계 의미 질의]" in s2_vector_ctx,
                vector_context_chars=len(s2_vector_ctx),
                budget_ledger=stage2_budget_ledger,
            ),
        )
        if s2_vector_ctx:
            self.ctx.ui.log(f"      🔎 [TF-38] 벡터 검색 완료 ({len(s2_vector_ctx):,}자)")
        return s2_vector_ctx

    def _apply_postpass_state_change_fixes(self, *, refined_arc: dict, enriched_block: dict) -> dict:
        state_changes = refined_arc.get("state_changes", {})
        if not isinstance(state_changes, dict):
            state_changes = {}

        relationship_delta = enriched_block.get("relationship_delta", [])
        if relationship_delta:
            existing_rel = state_changes.get("relationship_changes")
            if not isinstance(existing_rel, list):
                existing_rel = []
                state_changes["relationship_changes"] = existing_rel

            for relation in relationship_delta:
                if not isinstance(relation, dict):
                    continue

                target = relation.get("target", "")
                before = relation.get("before", "")
                after = relation.get("after", "")
                matched = None

                for entry in existing_rel:
                    if not isinstance(entry, dict):
                        continue
                    entry_target = entry.get("npc") or entry.get("target", "")
                    entry_before = entry.get("from") or entry.get("from_state") or entry.get("before", "")
                    entry_after = entry.get("to") or entry.get("to_state") or entry.get("after", "")
                    if entry_target != target:
                        continue
                    if before and entry_before and entry_before != before:
                        continue
                    if after and entry_after and entry_after != after:
                        continue
                    matched = entry
                    break

                if matched is not None:
                    if relation.get("trigger") and not matched.get("trigger"):
                        matched["trigger"] = relation.get("trigger", "")
                    if relation.get("justification") and not matched.get("justification"):
                        matched["justification"] = relation.get("justification", "")
                    continue

                existing_rel.append(
                    {
                        "npc": target,
                        "from": before,
                        "to": after,
                        "trigger": relation.get("trigger", ""),
                        "justification": relation.get("justification", ""),
                        "episode": None,
                    }
                )

        time_span = enriched_block.get("time_span", {})
        if isinstance(time_span, dict) and time_span and not state_changes.get("timeline", {}).get("start"):
            time_value = time_span.get("in_story_time", "")
            if time_value:
                state_changes["timeline"] = {"start": time_value, "end": time_value}
        refined_arc["state_changes"] = state_changes

        state_constraints = refined_arc.get("state_constraints", {})
        if not (state_constraints.get("protagonist_items") or state_constraints.get("items_acquired")):
            end_eq = state_constraints.get("arc_end_state", {}).get("equipment", [])
            start_eq = state_constraints.get("arc_start_state", {}).get("equipment", [])
            if isinstance(end_eq, list) and isinstance(start_eq, list):
                diff_items = [item for item in end_eq if item not in start_eq]
                if diff_items:
                    logging.debug(
                        "[S2-Preflight] items_acquired LLM 미제공 — equipment diff advisory: %s",
                        diff_items,
                    )
        return refined_arc

    @staticmethod
    def _run_auxiliary_state_tracker_extractors(*, state_tracker, refined_arc: dict) -> None:
        extractor_specs = (
            ("extract_npc_dialogue_styles_from_arc", logging.debug, "[SilentPass:S2:NpcDialogue] %s"),
            ("extract_time_markers_from_arc", logging.warning, "[V66.1] 시간선 추출 실패 (무시): %s"),
            ("extract_permanent_injuries_from_arc", logging.warning, "[V66.1] 신체 변화 추출 실패 (무시): %s"),
            ("update_companions_from_arc", logging.warning, "[V66.1] 동행자 추출 실패 (무시): %s"),
            ("extract_commitments_from_arc", logging.warning, "[V66.1] 약속 추출 실패 (무시): %s"),
            ("extract_protagonist_emotion_from_arc", logging.warning, "[V66.1] 감정 추출 실패 (무시): %s"),
            ("extract_relationship_changes_from_arc", logging.warning, "[V66.2] 관계 변화 추출 실패 (무시): %s"),
            ("extract_npc_injuries_from_arc", logging.warning, "[V66.2] NPC 부상 추출 실패 (무시): %s"),
            ("extract_npc_movements_from_arc", logging.warning, "[V66.2] NPC 이동 추출 실패 (무시): %s"),
        )

        for method_name, log_fn, log_template in extractor_specs:
            try:
                getattr(state_tracker, method_name)(refined_arc)
            except Exception as e:
                log_fn(log_template, e)

    def _run_state_tracker_tail_tasks(
        self,
        *,
        refined_arc: dict,
        global_arc_no: int,
        genre_for_tracker: str,
    ) -> None:
        state_tracker = self.ctx.state_tracker
        try:
            state_tracker._populate_genre_registries_from_arc(refined_arc)
        except Exception as e:
            logging.warning("[Sweep5-D] genre registry update failed: %s", e)

        if genre_for_tracker == "investment":
            try:
                state_tracker.extract_financial_events_from_arc(refined_arc)
                self.ctx.current_project.save_v20_anchor(
                    "financial_registry",
                    state_tracker.export_financial_registry(),
                )
            except Exception as fin_err:
                logging.warning("[SilentPass:Preflight] financial registry save failed: %s", fin_err)

        if self.ctx.semantic_plot_guard and state_tracker.resolved_plots:
            try:
                indexed = self.ctx.semantic_plot_guard.index_resolved_plots(state_tracker.resolved_plots)
                if indexed > 0:
                    logging.warning(f" [V66] SemanticPlotGuard: {indexed}개 플롯 인덱싱")
            except Exception as e:
                logging.warning("[Sweep5-D] semantic plot indexing failed: %s", e)

        try:
            arc_summary = state_tracker.generate_arc_summary(global_arc_no, refined_arc)
            self.ctx.current_project.save_v20_anchor(f"arc_summary_{global_arc_no}", arc_summary)
            logging.info(f"📊 [V66] Arc {global_arc_no} 요약 저장 완료")
        except Exception as e:
            logging.warning(f"⚠️ [V66] Arc 요약 저장 실패 (비차단): {e}")

        if global_arc_no > 0 and global_arc_no % 5 == 0:
            try:
                removed = state_tracker.cleanup_npc_registry_with_llm(global_arc_no)
                if removed:
                    logging.info(f"🧹 [V69] NPC 레지스트리 정리: {len(removed)}개 오탐 제거 ({', '.join(removed[:5])})")
            except Exception as e:
                logging.warning(f"⚠️ [V69] NPC 레지스트리 정리 실패 (비차단): {e}")

        tactical_doc = refined_arc.get("tactical_doc", "")
        if tactical_doc and hasattr(state_tracker, "check_and_expand_genre"):
            new_genre = state_tracker.check_and_expand_genre(tactical_doc)
            if new_genre:
                logging.info(f"- 새 장르 감지: {new_genre}")

    @staticmethod
    def _log_four_phase_pass_summary(
        *,
        dead_npcs: list,
        learned_skills: list,
        npc_info: list,
        pipeline_result: dict,
    ) -> None:
        if dead_npcs:
            logging.info(f"- 사망 NPC 기록: {', '.join(dead_npcs)}")
        if learned_skills:
            logging.info(f"- 무공 습득 기록: {', '.join(learned_skills)}")
        if npc_info:
            logging.info(f"- NPC 정보 기록: {len(npc_info)}건")

        phases = pipeline_result.get("phases", {}) if isinstance(pipeline_result, dict) else {}
        generate_phase = phases.get("generate", {}) if isinstance(phases, dict) else {}
        if isinstance(generate_phase, dict) and generate_phase:
            logging.info(f"- 후보 수: {generate_phase.get('candidates_count', 0)}개")
            logging.info(f"- 선택 전략: {generate_phase.get('selected_strategy', 'unknown')}")


    def _apply_four_phase_pass_state_tracker_updates(
        self,
        *,
        refined_arc: dict,
        global_arc_no: int,
        genre_for_tracker: str,
        pipeline_result: dict,
    ) -> Stage2FourPhaseTrackerPayload:
        import copy as _copy

        state_tracker = self.ctx.state_tracker
        if state_tracker is None:
            st_snapshot = {}
        else:
            st_snapshot = {
                "npc_registry": _copy.deepcopy(state_tracker.npc_registry),
                "resolved_plots": _copy.deepcopy(state_tracker.resolved_plots),
                "entity_destructions": _copy.deepcopy(state_tracker.entity_destructions),
                "protagonist_skills": _copy.deepcopy(state_tracker.protagonist_skills),
                "skill_acquisitions": _copy.deepcopy(state_tracker.skill_acquisitions),
                "npc_npc_relationships": _copy.deepcopy(state_tracker.npc_npc_relationships),
                "item_state_registry": _copy.deepcopy(state_tracker.item_state_registry),
                "active_plots": _copy.deepcopy(state_tracker.active_plots),
                "npc_dialogue_profiles": _copy.deepcopy(state_tracker.npc_dialogue_profiles),
                "in_world_timeline": _copy.deepcopy(state_tracker.in_world_timeline),
                "current_companions": _copy.deepcopy(state_tracker.current_companions),
                "pending_commitments": _copy.deepcopy(state_tracker.pending_commitments),
                "protagonist_emotion": _copy.deepcopy(state_tracker.protagonist_emotion),
                "dungeon_clear_registry": _copy.deepcopy(state_tracker.dungeon_clear_registry),
                "skill_cooldown_registry": _copy.deepcopy(state_tracker.skill_cooldown_registry),
                "spell_repertoire": _copy.deepcopy(state_tracker.spell_repertoire),
                "financial_number_registry": _copy.deepcopy(state_tracker.financial_number_registry),
            }

        dead_npcs = []
        learned_skills = []
        npc_info = []
        try:
            state_tracker.extract_resolved_plots_from_arc(refined_arc)
            dead_npcs = state_tracker.extract_npc_deaths_from_arc(refined_arc)
            learned_skills = state_tracker.extract_skill_acquisitions_from_arc(refined_arc)
            npc_info = state_tracker.extract_npc_info_from_arc(refined_arc, genre=genre_for_tracker)
            state_tracker.extract_entity_destructions_from_arc(refined_arc)
            state_tracker.extract_npc_personality_from_arc(refined_arc)
            state_tracker.extract_npc_npc_relationships_from_arc(refined_arc)
            state_tracker.extract_item_states_from_arc(refined_arc)
            state_tracker.update_plot_mentions_from_arc(refined_arc)
        except Exception as st_err:
            logging.error("[Preflight] StateTracker partial update failed: %s", st_err)

        suspended = state_tracker.check_suspended_plots(global_arc_no)
        if suspended:
            for suspended_warning in suspended:
                logging.warning(f" [V66] {suspended_warning['message']}")

        self._run_auxiliary_state_tracker_extractors(
            state_tracker=state_tracker,
            refined_arc=refined_arc,
        )
        self._run_state_tracker_tail_tasks(
            refined_arc=refined_arc,
            global_arc_no=global_arc_no,
            genre_for_tracker=genre_for_tracker,
        )
        self._log_four_phase_pass_summary(
            dead_npcs=dead_npcs,
            learned_skills=learned_skills,
            npc_info=npc_info,
            pipeline_result=pipeline_result,
        )
        return Stage2FourPhaseTrackerPayload(
            st_snapshot=st_snapshot,
            dead_npcs=dead_npcs,
            learned_skills=learned_skills,
            npc_info=npc_info,
        )


    def _emit_patch_mode_audit_event(
        self,
        *,
        was_patch: bool,
        global_arc_no: int,
        attempt: int,
        prev_score: int | float,
        patch_fallback: bool,
    ) -> None:
        if not was_patch:
            return
        audit_event = getattr(self.ctx, "audit_event", None)
        if not callable(audit_event):
            return
        try:
            audit_event(
                "stage2_patch_mode",
                "stage2 four_phase patch mode attempted",
                self._build_patch_mode_audit_payload(
                    global_arc_no=global_arc_no,
                    attempt=attempt,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                ),
            )
        except Exception as e:
            logging.debug("[Stage2Preflight] audit_event(patch_mode) 실패 (무시): %s", e)

    @staticmethod
    def _build_patch_mode_audit_payload(
        *,
        global_arc_no: int,
        attempt: int,
        prev_score: int | float,
        patch_fallback: bool,
    ) -> dict:
        return {
            "arc_no": global_arc_no,
            "attempt": attempt + 1,
            "prev_score": prev_score,
            "fallback": patch_fallback,
        }

    @staticmethod
    def _build_four_phase_result_payload(
        *,
        four_phase_passed: bool,
        refined_arc,
        generation_method: str,
        draft_validator_passed: bool,
        consensus_passed: bool,
        st_snapshot: dict,
        director_feedback_for_fourphase: str,
        was_patch: bool,
        patch_fallback: bool,
        prev_score: int | float,
    ) -> dict:
        return {
            "four_phase_passed": four_phase_passed,
            "refined_arc": refined_arc,
            "generation_method": generation_method,
            "draft_validator_passed": draft_validator_passed,
            "consensus_passed": consensus_passed,
            "st_snapshot": st_snapshot,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "was_patch": was_patch,
            "patch_fallback": patch_fallback,
            "prev_score": prev_score,
        }

    @staticmethod
    def _build_four_phase_prerun_state() -> dict:
        return {
            "four_phase_passed": False,
            "refined_arc": None,
            "generation_method": "analyst",
            "draft_validator_passed": False,
            "consensus_passed": False,
            "st_snapshot": None,
            "was_patch": False,
            "patch_fallback": False,
            "prev_score": 0,
        }

    @staticmethod
    def _build_four_phase_spinner_labels(*, attempt: int, global_arc_no: int) -> dict:
        return {
            "attempt_log": f"      🎯 [V60.77] FourPhase-Director 대면 {attempt + 1}/5",
            "spinner_title": f"Arc {global_arc_no}",
            "vector_detail": f"Arc {global_arc_no} · 벡터 검색",
        }

    @staticmethod
    def _build_patch_mode_labels(*, prev_score: int | float, attempt: int) -> Stage2PatchModeLabels:
        return Stage2PatchModeLabels(
            enter_log=f"[Patch Mode] Arc 패치 모드 진입 (score={prev_score}, attempt={attempt})",
            enter_ui=f"   🔧 [Patch Mode] Arc 패치: score={prev_score}, 원본 보존 수정",
            fallback_log="[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백",
            fallback_ui="   ⚠️ [Patch Mode] Arc 패치 실패 → 전면 재생성 폴백",
        )

    def _build_four_phase_failure_feedback(
        self,
        *,
        pipeline_result: dict,
        global_arc_no: int,
    ) -> str:
        final_verdict = str(pipeline_result.get("final_verdict", "") or "").upper()
        validate_phase = pipeline_result.get("phases", {}).get("validate", {})
        issues = validate_phase.get("issues_count", 0) if isinstance(validate_phase, dict) else 0

        if final_verdict == "FAILED":
            logging.warning(" [V60.77] FourPhase 재시도 소진 실패")
            if issues:
                logging.info(f"- 최종 검증 이슈: {issues}개")
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "four_phase_failed",
                    "retry budget exhausted",
                    {
                        "arc_no": global_arc_no,
                        "retries": pipeline_result.get("retries", 0),
                        "issues_count": issues,
                    },
                )
            return "FourPhase 재시도 소진 실패 (final_verdict=FAILED). 구조적 문제 해결 후 재시도 필요."

        logging.warning(" [V60.77] FourPhase 내부 검증 실패")
        if issues:
            logging.info(f"- 검증 이슈: {issues}개")
        return "FourPhase 내부 검증 실패. 구조적 문제 해결 필요."

    def _build_four_phase_exception_feedback(
        self,
        *,
        fp_err: Exception,
        global_arc_no: int,
    ) -> str:
        error_text = str(fp_err)[:100]
        logging.warning(f"❌ [V60.77] FourPhase 오류: {error_text[:80]}")
        if callable(getattr(self.ctx, "audit_event", None)):
            self.ctx.audit_event("four_phase_error", error_text, {"arc_no": global_arc_no})
        return f"FourPhase 오류 발생: {error_text}"

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
        return self.runtime.preflight_arc_analysis(
            attempt=attempt,
            current_feedback=current_feedback,
            constraint_block=constraint_block,
            last_refined_context=last_refined_context,
            all_refined_arcs=all_refined_arcs,
            protagonist_name=protagonist_name,
            global_arc_no=global_arc_no,
            cached_preflight_injection=cached_preflight_injection,
            cached_preflight_result=cached_preflight_result,
        )

    @staticmethod
    def _build_four_phase_generation_attempt_result(
        *,
        four_phase_arc: dict | None,
        pipeline_result: dict,
        prev_score: int | float,
        was_patch: bool,
        patch_fallback: bool,
    ) -> Stage2FourPhaseAttemptResult:
        return Stage2FourPhaseAttemptResult(
            four_phase_arc=four_phase_arc,
            pipeline_result=pipeline_result,
            prev_score=prev_score,
            was_patch=was_patch,
            patch_fallback=patch_fallback,
        )

    def _resolve_four_phase_generation_seed(
        self,
        *,
        request: Stage2FourPhaseGenerationRequest,
    ) -> tuple[dict | None, dict]:
        generation_plan = request.generation_plan
        if not generation_plan.use_inplace:
            return generation_plan.four_phase_arc, generation_plan.pipeline_result
        return self._run_inplace_four_phase_attempt(
            global_arc_no=request.global_arc_no,
            fix_scope=generation_plan.fix_scope,
            prev_score=generation_plan.prev_score,
            previous_attempt=request.previous_attempt,
        )

    @staticmethod
    def _build_patch_or_generate_attempt_kwargs(
        *,
        request: Stage2FourPhaseGenerationRequest,
        four_phase_arc: dict | None,
        pipeline_result: dict,
    ) -> dict:
        return {
            **Stage2PreflightAnalysis._build_patch_or_generate_request_fields(request),
            **Stage2PreflightAnalysis._build_patch_or_generate_plan_fields(
                request=request,
                four_phase_arc=four_phase_arc,
                pipeline_result=pipeline_result,
            ),
        }

    @staticmethod
    def _build_patch_or_generate_request_fields(request: Stage2FourPhaseGenerationRequest) -> dict:
        return {
            **Stage2PreflightAnalysis._build_patch_or_generate_episode_fields(request),
            **Stage2PreflightAnalysis._build_patch_or_generate_content_fields(request),
        }

    @staticmethod
    def _build_patch_or_generate_episode_fields(request: Stage2FourPhaseGenerationRequest) -> dict:
        return {
            "attempt": request.attempt,
            "global_arc_no": request.global_arc_no,
            "current_ep_start": request.current_ep_start,
            "s2_spinner": request.s2_spinner,
            "s2_vector_ctx": request.s2_vector_ctx,
        }

    @staticmethod
    def _build_patch_or_generate_content_fields(request: Stage2FourPhaseGenerationRequest) -> dict:
        return {
            **Stage2PreflightAnalysis._build_patch_or_generate_story_fields(request),
            **Stage2PreflightAnalysis._build_patch_or_generate_director_fields(request),
        }

    @staticmethod
    def _build_patch_or_generate_story_fields(request: Stage2FourPhaseGenerationRequest) -> dict:
        return {
            "current_vol_strategy": request.current_vol_strategy,
            "enriched_block": request.enriched_block,
            "all_refined_arcs": request.all_refined_arcs,
            "bible_root": request.bible_root,
            "protagonist_name": request.protagonist_name,
        }

    @staticmethod
    def _build_patch_or_generate_director_fields(request: Stage2FourPhaseGenerationRequest) -> dict:
        return {
            "director_feedback_for_fourphase": request.director_feedback_for_fourphase,
            "entity_registry_for_director": request.entity_registry_for_director,
            "previous_attempt": request.previous_attempt,
        }

    @staticmethod
    def _build_patch_or_generate_plan_fields(
        *,
        request: Stage2FourPhaseGenerationRequest,
        four_phase_arc: dict | None,
        pipeline_result: dict,
    ) -> dict:
        return {
            "prev_score": request.generation_plan.prev_score,
            "use_patch": request.generation_plan.use_patch,
            "four_phase_arc": four_phase_arc,
            "pipeline_result": pipeline_result,
        }

    def _log_four_phase_generation_attempt_outcome(self, four_phase_arc: dict | None) -> None:
        if four_phase_arc:
            self.ctx.ui.log("      ✅ [TF-38] Arc 생성 완료")
        else:
            self.ctx.ui.log("      ⚠️ [TF-38] Arc 생성 실패")

    def _run_inplace_four_phase_attempt(
        self,
        *,
        global_arc_no: int,
        fix_scope: str,
        prev_score: int | float,
        previous_attempt: dict | None,
    ) -> tuple[dict | None, dict]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        logging.info(f"[TF-23] Arc InPlace 진입 (fix_scope={fix_scope!r}, score={prev_score})")
        self.ctx.ui.log(f"   🔧 [TF-23] Arc InPlace: fix_scope={fix_scope!r}, score={prev_score}")
        four_phase_arc = self.ctx.agents["four_phase"]._inplace_patch_arc(
            original_arc=previous_attempt["best_arc"],
            director_feedback=previous_attempt.get("rejection_reason", ""),
            arc_no=global_arc_no,
        )
        pipeline_result = {"final_verdict": None}
        if not four_phase_arc:
            logging.warning("[TF-23] Arc InPlace 실패 -> Patch 대체")
            self.ctx.ui.log("   ⚠️ [TF-23] Arc InPlace 실패 -> Patch 대체")
            return None, pipeline_result

        try:
            import json as _json_mod

            from modules.core.constants import calc_patch_change_ratio, log_patch_diff

            pf_orig_json = _json_mod.dumps(previous_attempt.get("best_arc", {}), ensure_ascii=False, indent=2)
            pf_patch_json = _json_mod.dumps(four_phase_arc, ensure_ascii=False, indent=2)
            log_patch_diff("S2-Preflight-Arc", pf_orig_json, pf_patch_json)
            pf_change_ratio = calc_patch_change_ratio(
                _json_mod.dumps(previous_attempt.get("best_arc", {}), ensure_ascii=False),
                _json_mod.dumps(four_phase_arc, ensure_ascii=False),
            )
            if pf_change_ratio > 0.30:
                logging.warning("[TF-IPG] Preflight Arc 변경 비율 %.1f%% > 30%%", pf_change_ratio * 100)
        except Exception as diff_err:
            logging.debug("[TF-IPG] preflight diff 계산 실패: %s", diff_err)
        pipeline_result["final_verdict"] = "PASS"
        return four_phase_arc, pipeline_result

    def _run_patch_or_generate_four_phase_attempt(
        self,
        *,
        attempt: int,
        global_arc_no: int,
        current_ep_start: int,
        current_vol_strategy: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        bible_root: dict,
        protagonist_name: str,
        director_feedback_for_fourphase: str,
        entity_registry_for_director,
        previous_attempt: dict | None,
        s2_spinner,
        s2_vector_ctx: str,
        prev_score: int | float,
        use_patch: bool,
        four_phase_arc: dict | None,
        pipeline_result: dict,
    ) -> tuple[dict | None, dict, bool]:
        previous_attempt = previous_attempt if isinstance(previous_attempt, dict) else {}
        patch_fallback = False
        if not four_phase_arc and use_patch:
            patch_labels = self._build_patch_mode_labels(
                prev_score=prev_score,
                attempt=attempt,
            )
            logging.info(patch_labels.enter_log)
            self.ctx.ui.log(patch_labels.enter_ui)
            patch_feedback = self._build_patch_feedback(previous_attempt)
            four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].patch_arc_with_feedback(
                original_arc=previous_attempt["best_arc"],
                director_feedback=patch_feedback,
                attempt_number=attempt + 1,
                arc_no=global_arc_no,
                ep_start=current_ep_start,
                vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                curr_block=enriched_block,
                prev_arcs=all_refined_arcs,
                assets=bible_root.get("AssetLibrary", {}),
                protagonist_name=protagonist_name or "주인공",
                entity_registry=entity_registry_for_director,
                state_tracker=self.ctx.state_tracker,
                vector_context=s2_vector_ctx,
                adversarial_self_play=self.ctx.adversarial_self_play,
                rejected_strategy=previous_attempt.get("selected_strategy", ""),
            )
            if not four_phase_arc:
                patch_fallback = True
                logging.warning(patch_labels.fallback_log)
                self.ctx.ui.log(patch_labels.fallback_ui)

        s2_spinner.update_detail(f"Arc {global_arc_no} · Arc 생성")
        if not four_phase_arc:
            four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].generate(
                arc_no=global_arc_no,
                ep_start=current_ep_start,
                vol_strategy=current_vol_strategy.get("strategy_doc", ""),
                curr_block=enriched_block,
                prev_arcs=all_refined_arcs,
                assets=bible_root.get("AssetLibrary", {}),
                max_internal_retries=9,
                protagonist_name=protagonist_name or "주인공",
                director_feedback=director_feedback_for_fourphase,
                entity_registry=entity_registry_for_director,
                state_tracker=self.ctx.state_tracker,
                vector_context=s2_vector_ctx,
                adversarial_self_play=self.ctx.adversarial_self_play,
                director=self.ctx.agents.get("director"),
            )
        return four_phase_arc, pipeline_result, patch_fallback


    def _preflight_enrichment(
        self,
        *,
        attempt: int,
        global_arc_no: int,
        current_ep_start: int,
        current_vol_strategy: dict,
        enriched_block: dict,
        all_refined_arcs: list,
        bible_root: dict,
        protagonist_name: str,
        director_feedback_for_fourphase: str,
        entity_registry_for_director,
        genre_for_tracker: str,
        previous_attempt: dict | None = None,
    ) -> dict:
        """[4-R3-c] FourPhase generation and state tracker enrichment.

        Runs FourPhaseArcGenerator if available, and on PASS enriches
        StateTracker with NPC deaths, skills, relationships, etc.

        Returns dict of generation results for the attempt loop.
        """
        return self.runtime.preflight_enrichment(
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
            genre_for_tracker=genre_for_tracker,
            previous_attempt=previous_attempt,
        )
