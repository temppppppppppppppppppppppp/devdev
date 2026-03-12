"""
[Phase 4C-1a] Stage3Orchestrator — SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

원본: main_a.py:2855-3254 (_stage_3_batch_blueprinting, 400줄)

패턴: self.app = SovereignApp 인스턴스 (Stage2/4 Orchestrator와 동일)
V68 lazy init: state_tracker, world_state, fact_ledger를 self.app에 할당
"""

import json as _json
import logging as _logging
import time as _time
import traceback as _traceback

from modules.core.artifact_logging import build_candidate_key, snapshot_logged_artifact
from modules.core.constants import ContextLimits, Emojis, ErrorMessages
from modules.core.continuity_pin_guard import apply_continuity_pins
from modules.core.context_advisor import RetrievalSources
from modules.core.fact_ledger import summarize_fact_ledger_numbers_block
from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.core.tactical_utils import extract_episode_tactical

try:
    from modules.utils.notifier import notifier
except Exception:  # notifier 미설치 시 비차단
    notifier = None

_DB_ADVISORY_NOTICE = "(Python 자동 감지 — 오탐 가능, 참고용)"


def _normalize_semantic_source_counts(source_counts: dict | None) -> dict[str, int]:
    if not isinstance(source_counts, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, value in source_counts.items():
        name = str(key or "").strip()
        if not name:
            continue
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > 0:
            normalized[name] = count
    return normalized


def _build_stage3_observability_flags(meta: dict | None) -> dict:
    if not isinstance(meta, dict):
        return {}
    source_counts = _normalize_semantic_source_counts(meta.get("source_counts"))
    coverage_warnings = [
        str(item).strip()
        for item in (meta.get("coverage_warnings") or [])
        if str(item or "").strip()
    ]
    flags = {
        "semantic_ctx_chars": int(meta.get("semantic_ctx_chars") or 0),
        "semantic_ctx_sources": sorted(source_counts.keys()),
        "semantic_ctx_source_counts": source_counts,
        "coverage_warnings": coverage_warnings,
        "advisor_path_used": bool(meta.get("advisor_path_used", False)),
        "planned_slots_count": int(meta.get("planned_slots_count") or 0),
        "work_focus_present": bool(meta.get("work_focus_present", False)),
    }
    return {key: value for key, value in flags.items() if value not in ("", [], {}, None, 0, False)}


def _classify_stage3_failure_category(pipeline_result: dict) -> str | None:
    if not isinstance(pipeline_result, dict):
        return None

    verdict = str(pipeline_result.get("final_verdict", "") or "").upper()
    error_text = str(pipeline_result.get("error", "") or "").strip()
    if verdict == "ERROR" or error_text:
        return "generation_error"
    if pipeline_result.get("quality_gate_failed"):
        return "quality_gate"

    phases = pipeline_result.get("phases", {})
    validate = phases.get("validate", {}) if isinstance(phases, dict) else {}
    if isinstance(validate, dict):
        contradictions = validate.get("contradictions")
        if isinstance(contradictions, list) and contradictions:
            return "validation_contradiction"
        if validate.get("issues_count"):
            return "validation_issue"

    reject_reason = str(pipeline_result.get("reject_reason", "") or "")
    if "continuity" in reject_reason.lower():
        return "continuity"
    return "reject"


def _build_stage3_prompt_version() -> str | None:
    try:
        from modules.core.prompt_loader import PromptLoader

        return PromptLoader().compose_version_tag("ensemble", "blueprint_generator", "director")
    except Exception as _e:
        _logging.debug("[Stage3] prompt_version 계산 실패 (비차단): %s", _e)
        return None


def _build_stale_seed_advisory(db, next_ep: int) -> str:
    """장기 미회수 복선 경고를 Blueprint semantic_context용 문자열로 반환한다."""
    getter = getattr(db, "get_active_seeds", None)
    if not callable(getter):
        return ""

    try:
        seeds = getter()
        if not isinstance(seeds, list) or not seeds:
            return ""

        stale_seeds: list[str] = []
        for seed in seeds:
            if not isinstance(seed, dict):
                continue
            planted_ep = seed.get("planted_ep") or 0
            try:
                planted_ep = int(planted_ep)
            except (TypeError, ValueError):
                planted_ep = 0
            if planted_ep and (next_ep - planted_ep) >= 20:
                content = str(seed.get("content", "?") or "?")[:60]
                stale_seeds.append(f"  - {content} (ep{planted_ep}~ 미회수, {next_ep - planted_ep}화 경과)")

        if not stale_seeds:
            return ""
        return f"[DB-4 장기 미회수 복선] {_DB_ADVISORY_NOTICE}\n" + "\n".join(stale_seeds[:5])
    except Exception as seed_err:
        _logging.debug("[DB-4] foreshadow advisory 실패 (비치명): %s", seed_err)
        return ""


def _build_fact_ledger_advisory(db, *, max_items: int = 10) -> str:
    """Blueprint semantic_context용 핵심 수치 팩트 요약."""
    if db is None:
        return ""

    try:
        ledger = db.load_anchor("fact_ledger")
        return summarize_fact_ledger_numbers_block(
            ledger,
            header="[팩트 원장 핵심 수치]",
            max_items=max_items,
        )
    except Exception as fact_err:
        _logging.debug("[TF-DB-B1] Stage3 FactLedger advisory 실패 (비치명): %s", fact_err)
        return ""


def _build_world_state_advisory(world_state, *, max_chars: int = 1800) -> str:
    """Blueprint semantic_context용 compact WorldState 요약."""
    if world_state is None or not hasattr(world_state, "get_summary"):
        return ""

    try:
        summary = world_state.get_summary(max_chars=max_chars)
    except Exception as ws_err:
        _logging.debug("[CTX-P1-2] Stage3 WorldState advisory 실패 (비치명): %s", ws_err)
        return ""

    summary = str(summary or "").strip()
    if not summary:
        return ""
    return "[WorldState 핵심 요약]\n" + summary


def _build_style_guide_advisory(project, *, max_chars: int = 600) -> str:
    """Blueprint semantic_context용 compact StyleGuide 요약."""
    if project is None:
        return ""

    style_data = {}
    try:
        loader = getattr(project, "load_v20_anchor", None)
        raw_style = loader("style_guide") if callable(loader) else None
        if isinstance(raw_style, dict):
            style_data = raw_style
    except Exception as style_err:
        _logging.debug("[QR-1] Stage3 StyleGuide 로드 실패 (비치명): %s", style_err)

    bible_root = {}
    try:
        master_bible = getattr(project, "master_bible", None)
        if isinstance(master_bible, dict):
            bible_root = master_bible.get("MasterBible", master_bible)
    except Exception:
        bible_root = {}
    protagonist_config = bible_root.get("protagonist_config", {}) if isinstance(bible_root, dict) else {}
    bible_pov = str(protagonist_config.get("pov", "") or "").strip()

    tone = str(style_data.get("tone", "") or "").strip()
    pov = bible_pov or str(style_data.get("pov", "") or "").strip()
    sentence_length = str(style_data.get("sentence_length", "") or "").strip()
    paragraph_style = str(style_data.get("paragraph_style", "") or "").strip()
    anti_ai_patterns = [str(item).strip() for item in (style_data.get("anti_ai_patterns") or []) if str(item).strip()]
    forbidden_expr = [
        str(item).strip() for item in (style_data.get("forbidden_expressions") or []) if str(item).strip()
    ]

    if not any([tone, pov, sentence_length, paragraph_style, anti_ai_patterns, forbidden_expr]):
        return ""

    lines = ["[StyleGuide 문체/anti-AI 참고]"]
    core_bits: list[str] = []
    if tone:
        core_bits.append(f"톤={tone}")
    if pov:
        core_bits.append(f"시점={pov}")
    if sentence_length:
        core_bits.append(f"문장 길이={sentence_length}")
    if paragraph_style:
        core_bits.append(f"문단 스타일={paragraph_style}")
    if core_bits:
        lines.append("- " + ", ".join(core_bits))
    if anti_ai_patterns:
        lines.append("- anti-AI 금지: " + ", ".join(anti_ai_patterns[:6]))
    if forbidden_expr:
        lines.append("- 금지 표현: " + ", ".join(forbidden_expr[:5]))

    return "\n".join(lines)[:max_chars]


def _compose_stage3_work_focus_text(
    *,
    arc_data: dict | None,
    prev_blueprints: list[dict] | None,
    entity_registry: dict | None,
) -> str:
    parts: list[str] = []
    if isinstance(arc_data, dict):
        for key in ("title", "summary", "block_theme", "tactical_doc", "arc_tactical", "constraint_summary"):
            value = str(arc_data.get(key, "") or "").strip()
            if value:
                parts.append(value)
        plot_suspension = arc_data.get("plot_suspension", []) or []
        if isinstance(plot_suspension, list) and plot_suspension:
            parts.append(" ".join(str(item).strip() for item in plot_suspension[:4] if str(item).strip()))

    if isinstance(prev_blueprints, list) and prev_blueprints:
        last_bp = prev_blueprints[-1] if isinstance(prev_blueprints[-1], dict) else {}
        if isinstance(last_bp, dict):
            for key in ("title", "ending_hook", "cliffhanger", "core_event"):
                value = str(last_bp.get(key, "") or "").strip()
                if value:
                    parts.append(value)

    if isinstance(entity_registry, dict):
        for values in entity_registry.values():
            if not isinstance(values, list):
                continue
            names: list[str] = []
            for item in values[:8]:
                if isinstance(item, dict):
                    name = str(item.get("name", "") or item.get("npc", "") or item.get("title", "")).strip()
                else:
                    name = str(item).strip()
                if name:
                    names.append(name)
            if names:
                parts.append(" ".join(names[:6]))

    combined = "\n".join(part for part in parts if part)
    return combined[:1800]


def _resolve_stage3_work_focus(
    ctx,
    *,
    arc_data: dict | None,
    prev_blueprints: list[dict] | None,
    entity_registry: dict | None,
) -> dict[str, object]:
    guard = getattr(getattr(ctx, "sys", None), "guard", None)
    if not guard or not hasattr(guard, "select_retrieval_focus"):
        return {}

    focus_text = _compose_stage3_work_focus_text(
        arc_data=arc_data,
        prev_blueprints=prev_blueprints,
        entity_registry=entity_registry,
    )
    if not focus_text:
        return {}

    try:
        focus = guard.select_retrieval_focus(stage="blueprint", focus_text=focus_text)
    except Exception as focus_err:
        _logging.debug("[Stage3] work_focus 선택 실패 (비치명): %s", focus_err)
        return {}

    return focus if isinstance(focus, dict) else {}


def _build_stage3_work_focus_advisory(
    work_focus: dict[str, object],
    *,
    arc_data: dict | None,
    entity_registry: dict | None,
    ctx,
    protagonist_name: str = "",
    max_chars: int = 1200,
) -> str:
    if not isinstance(work_focus, dict) or not work_focus:
        return ""

    tracking_slots = [str(item).strip() for item in (work_focus.get("tracking_slots") or []) if str(item).strip()]
    scene_engines = [
        str(item).strip() for item in (work_focus.get("mandatory_scene_engines") or []) if str(item).strip()
    ]
    registry_profiles = [
        item for item in (work_focus.get("registry_profiles") or []) if isinstance(item, dict)
    ]
    if not any([tracking_slots, scene_engines, registry_profiles]):
        return ""

    lines = ["[작품 추적 슬롯 요약]"]
    if tracking_slots:
        lines.append(f"- 이번 화 우선 tracking_slots: {', '.join(tracking_slots[:3])}")
    if scene_engines:
        lines.append(f"- 이번 화 scene engines: {', '.join(scene_engines[:2])}")
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

    if isinstance(entity_registry, dict):
        linked_parts: list[str] = []
        for label, key in (("인물", "characters"), ("아이템", "items"), ("플롯", "plots"), ("위치", "locations")):
            values = entity_registry.get(key) or []
            rendered: list[str] = []
            if isinstance(values, list):
                for item in values[:4]:
                    if isinstance(item, dict):
                        name = str(item.get("name", "") or item.get("npc", "") or item.get("title", "")).strip()
                    else:
                        name = str(item).strip()
                    if name:
                        rendered.append(name)
            if rendered:
                linked_parts.append(f"{label}={', '.join(rendered[:4])}")
        if linked_parts:
            lines.append(f"- 연동 엔티티: {' | '.join(linked_parts)}")

    if isinstance(arc_data, dict):
        conflict = str(arc_data.get("constraint_summary", "") or arc_data.get("block_theme", "") or "").strip()
        if conflict:
            lines.append(f"- 현재 갈등축: {conflict[:160]}")

    try:
        focus_text = " ".join(
            [
                ", ".join(tracking_slots),
                ", ".join(scene_engines),
                " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                str((arc_data or {}).get("constraint_summary", "") or ""),
                str((arc_data or {}).get("block_theme", "") or ""),
            ]
        ).strip()
        broker = SemanticQueryBroker(
            db=getattr(getattr(ctx, "current_project", None), "db", None),
            world_state=getattr(ctx, "world_state", None),
            fact_ledger=getattr(ctx, "fact_ledger", None),
            state_tracker=getattr(ctx, "state_tracker", None),
            protagonist_name=protagonist_name,
        )
        relation_slice = broker.build_relation_slice(focus_text=focus_text, max_chars=420)
        if relation_slice:
            lines.append(relation_slice)
    except Exception as broker_err:
        _logging.debug("[Stage3] semantic relation slice 생성 실패 (비치명): %s", broker_err)

    text = "\n".join(lines)
    return text if len(text) <= max_chars else text[: max_chars - 18] + "\n... (슬롯 요약 절삭)"


def _build_stage3_relationship_context(db, *, npc_names: list[str], protagonist_name: str = "", limit: int = 6) -> str:
    if not db or not hasattr(db, "get_relationship_history"):
        return ""

    clean_names = [str(name).strip() for name in (npc_names or []) if str(name).strip()]
    protagonist_name = str(protagonist_name or "").strip()
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
            _logging.debug("[Stage3] relationship history 조회 실패 (비치명): %s", rel_err)
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


def _summarize_retrieval_sources(plan) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not plan or not getattr(plan, "slots", None):
        return counts
    for slot in getattr(plan, "slots", []) or []:
        source = str(getattr(slot, "source", RetrievalSources.VEC_MEMORY) or RetrievalSources.VEC_MEMORY)
        counts[source] = counts.get(source, 0) + 1
    return counts


def _record_retrieval_observation(app, *, ep_num: int, stage: str, observation: dict) -> None:
    dashboard = getattr(app, "quality_dashboard", None)
    if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
        return
    try:
        dashboard.record_retrieval_observation(ep_num=ep_num, stage=stage, observation=observation)
    except Exception as exc:
        _logging.debug("[Stage3] retrieval observation record failed: %s", exc)


class Stage3Orchestrator:
    """
    [Phase 4C-1a] SovereignApp의 Stage 3 Blueprint 배치 생성 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app, *, context=None) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (레거시 호환)
            context: Stage3Context DI 컨텍스트 (미주입 시 자동 빌드)
        """
        self.app = app
        self._ctx = context  # [Phase 4C-4] DI 컨텍스트
        # [V61.6] Entity Registry 캐시 (Arc 단위)
        self._entity_cache_arc_idx = -1
        self._cached_entity_registry = None

    @property
    def ctx(self):
        """[Phase 4C-4] DI 컨텍스트 (미주입 시 app에서 자동 빌드)"""
        if self._ctx is None:
            from modules.core.stage3_context import Stage3Context

            self._ctx = Stage3Context.from_app(self.app)
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value

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

        # 서브 에이전트 포함 전체 순회
        _all_agents = list(agents.values())
        _three_phase_bp = agents.get("three_phase_bp")
        if _three_phase_bp is not None:
            _sub = getattr(_three_phase_bp, "ensemble", None)
            if _sub is not None:
                _all_agents.append(_sub)

        for agent in _all_agents:
            if agent is None:
                continue
            try:
                setattr(agent, "_current_stage", 3)
            except Exception:
                pass
            if _ep_value is not None:
                try:
                    setattr(agent, "_current_ep_num", _ep_value)
                except Exception:
                    pass

    # ─────────────────────────────────────────────────────────────
    # Stage 3 메인 진입점
    # ─────────────────────────────────────────────────────────────
    def stage_3_batch_blueprinting(self, *, target_ep: int | None = None) -> dict:
        """
        [V60.80] Stage 3 - Three Phase Blueprint Generator

        3단계 파이프라인: 제약수집 → 앙상블생성 → 통합검증
        - Phase 1: Constraint compilation (Arc 섹션 추출, 연속성, 정지선)
        - Phase 2: Ensemble generation (3개 후보 → 최적 선택)
        - Phase 3: Unified validation (Python + LLM)

        철학: "Arc를 충실히 따르는, 연속성 있는 Blueprint"
        """
        ctx = self.ctx

        if not ctx.current_project.arcs:
            ctx.ui.log(f"{Emojis.ERROR} {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return {"success_count": 0, "fail_count": 0}

        # ═══════════════════════════════════════════════════════════════
        # [V60.96] StateTracker 초기화 (Stage 2에서 생성되지 않은 경우)
        # ═══════════════════════════════════════════════════════════════
        self._init_state_tracker_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] WorldStateManager 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_world_state_if_needed()

        # ═══════════════════════════════════════════════════════════════
        # [V68] FactLedger 초기화
        # ═══════════════════════════════════════════════════════════════
        self._init_fact_ledger_if_needed()

        # [E-1b] Sync lazy-inited objects to ctx (getattr for safety if lazy init failed)
        ctx.state_tracker = getattr(self.app, "state_tracker", None)
        ctx.world_state = getattr(self.app, "world_state", None)
        ctx.fact_ledger = getattr(self.app, "fact_ledger", None)
        # [TF-35b] StateTracker → WorldState re-bind (init 순서 보정)
        if ctx.state_tracker and ctx.world_state:
            ctx.state_tracker.bind_world_state(ctx.world_state)

        # ═══════════════════════════════════════════════════════════════
        # 1. 목표 범위 설정
        # ═══════════════════════════════════════════════════════════════
        _last_arc = ctx.current_project.arcs[-1] if ctx.current_project.arcs else None
        total_planned_ep = _last_arc.get("ep_end", 50) if isinstance(_last_arc, dict) else 50

        # [V60.80 FIX] Blueprint 테이블 기준으로 시작점 결정
        existing_bp_max = ctx.current_project.db.get_latest_blueprint_number()  # 0 if empty

        # [Smart Skip] 기존 원고가 있다면 원고 기준으로도 체크
        existing_ms_max_ep = (
            ctx.get_max_episode_from_manuscripts() if callable(ctx.get_max_episode_from_manuscripts) else 0
        )

        # 둘 중 큰 값을 기준으로 (Blueprint나 원고가 있는 화 다음부터)
        production_head = max(existing_bp_max, existing_ms_max_ep)

        if production_head > 0:
            ctx.ui.log(f"📂 [Detected] Blueprint {existing_bp_max}화, 원고 {existing_ms_max_ep}화까지 발견")
        else:
            ctx.ui.log("📂 [Fresh Start] 기존 데이터 없음 - 1화부터 시작")

        ctx.ui.log(f"📊 [V60.80] 현재 총 {total_planned_ep}화까지 설계가 가능합니다.")

        # [TF-CX-BUG-01] 입력 범위 역전 방어: 모든 블루프린트 이미 완료된 경우
        if production_head >= total_planned_ep:
            ctx.ui.log(f"✅ 이미 {production_head}화까지 완료되어 추가 생성할 범위가 없습니다.")
            ctx.ui.log("   💡 Stage 2에서 Arc를 추가하면 설계 범위가 늘어납니다.")
            return {"success_count": 0, "fail_count": 0}

        if target_ep is None:
            target_ep = (
                ctx.get_int_input(
                    f"👉 몇 화까지 설계도를 생성하시겠습니까? (현재 {production_head}화 / 최대 {total_planned_ep}화): ",
                    default=total_planned_ep,
                    min_val=production_head + 1,
                    max_val=total_planned_ep,
                )
                if callable(ctx.get_int_input)
                else total_planned_ep
            )
        # else: [OneStop] caller가 직접 target_ep 지정

        # ═══════════════════════════════════════════════════════════════
        # 2. 메인 에피소드 루프
        # ═══════════════════════════════════════════════════════════════
        working_ep = production_head + 1
        success_count = 0
        fail_count = 0
        prev_blueprints = []  # 연속성 검증용

        # [V67] 이전 Blueprint들 로드 (최근 30개 — Gemini 대용량 컨텍스트 활용)
        for prev_ep in range(max(1, working_ep - 30), working_ep):
            prev_bp = ctx.current_project.get_blueprint(prev_ep)
            if prev_bp:
                prev_blueprints.append(prev_bp)

        # [감리] target_ep < working_ep 방어 (이미 완료된 범위)
        if target_ep < working_ep:
            ctx.ui.log(f"✅ 이미 {target_ep}화까지 완료되어 추가 생성할 범위가 없습니다.")
            return {"success_count": 0, "fail_count": 0}

        ctx.ui.log(f"\n{'═' * 60}")
        ctx.ui.log("🎯 [V60.80] Three Phase Blueprint Generator 시작")
        ctx.ui.log(f"   범위: 제{working_ep}화 ~ 제{target_ep}화 ({target_ep - working_ep + 1}개)")
        ctx.ui.log(f"{'═' * 60}\n")

        while working_ep <= target_ep:
            result = self._process_single_episode(working_ep, target_ep, prev_blueprints, success_count, fail_count)
            working_ep = result["next_ep"]
            success_count = result["success_count"]
            fail_count = result["fail_count"]
            if result.get("break"):
                break

        # ═══════════════════════════════════════════════════════════════
        # 3. 완료 처리
        # ═══════════════════════════════════════════════════════════════
        if callable(ctx.write_audit_summary):
            ctx.write_audit_summary("stage3_complete")

        # 통계 출력
        ctx.ui.log(f"\n{'═' * 60}")
        ctx.ui.log("📊 [V60.80] Stage 3 완료 통계")
        ctx.ui.log(f"   성공: {success_count}개 | 실패: {fail_count}개")
        if ctx.agents and hasattr(ctx.agents.get("three_phase_bp"), "get_stats"):
            stats = ctx.agents["three_phase_bp"].get_stats()
            ctx.ui.log(f"   통과율: {stats.get('pass_rate', 'N/A')}")
        ctx.ui.log(f"{'═' * 60}\n")

        # Slack 알림
        if success_count > 0 and notifier:
            try:
                notifier.send_notification(
                    title="✅ [V60.80 Blueprint] 설계도 생성 완료",
                    message=f"프로젝트: {ctx.current_project.name}\n성공: {success_count}개 | 실패: {fail_count}개",
                    key_metrics={"성공": f"{success_count}개", "실패": f"{fail_count}개"},
                )
            except Exception as slack_err:
                ctx.ui.log(f"⚠️ [Slack] 알림 전송 실패: {str(slack_err)[:50]}")

        return {"success_count": success_count, "fail_count": fail_count}

    # ─────────────────────────────────────────────────────────────
    # V68 Lazy Init 헬퍼
    # ─────────────────────────────────────────────────────────────
    def _init_state_tracker_if_needed(self) -> None:
        """[V60.96] StateTracker lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "state_tracker") or app.state_tracker is None:
            try:
                from modules.domain.agents.state_tracker import StateTracker

                app.state_tracker = StateTracker(preset_registry=app.preset_registry, llm_client=app.sys.api_client)
                app.state_tracker.bind_db(app.current_project.db)  # [NPC-L1] NPC 이력 DB 배선
                app.state_tracker.bind_world_state(getattr(app, "world_state", None))  # [TF-36] WorldState 배선
                all_arcs = app.current_project.db.load_anchor("arcs") or []
                _g = app.selected_genre.get("type", "") if app.selected_genre else ""
                app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
                if app.state_tracker.npc_registry:
                    dead_count = sum(
                        1 for info in app.state_tracker.npc_registry.values() if info.get("status") == "dead"
                    )
                    app.ui.log(
                        f"      👤 [V60.96] StateTracker 초기화: NPC {len(app.state_tracker.npc_registry)}명 (사망: {dead_count}명)"
                    )
            except Exception as _st_err:
                # [Sweep54] sister 메서드(WorldState, FactLedger)와 동일한 비차단 패턴
                app.ui.log(f"      ⚠️ [V60.96] StateTracker 초기화 실패 (비차단): {str(_st_err)[:60]}")
                app.state_tracker = None

    def _init_world_state_if_needed(self) -> None:
        """[V68] WorldStateManager lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "world_state") or app.world_state is None:
            try:
                from modules.core.world_state import WorldStateManager

                app.world_state = WorldStateManager(app.current_project.db)
                _ws_ep = app.world_state.last_updated_ep
                if _ws_ep > 0:
                    app.ui.log(f"      🌍 [V68] WorldStateManager 로드 완료 (제{_ws_ep}화 기준)")
                else:
                    app.ui.log("      🌍 [V68] WorldStateManager 초기화 (신규)")
            except Exception as _ws_err:
                app.ui.log(f"      ⚠️ [V68] WorldStateManager 초기화 실패 (비차단): {str(_ws_err)[:60]}")
                app.world_state = None

    def _init_fact_ledger_if_needed(self) -> None:
        """[V68] FactLedger lazy init — app 인스턴스에 할당"""
        app = self.app
        if not hasattr(app, "fact_ledger") or app.fact_ledger is None:
            try:
                from modules.core.fact_ledger import FactLedger

                app.fact_ledger = FactLedger(app.current_project.db)
                _fl_ep = app.fact_ledger.last_updated_ep
                if _fl_ep > 0:
                    _fl_stats = app.fact_ledger.get_stats()
                    app.ui.log(
                        f"      📋 [V68] 팩트 원장 로드 완료 (제{_fl_ep}화 기준, 인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                    )
                else:
                    app.ui.log("      📋 [V68] 팩트 원장 초기화 (신규)")
            except Exception as _fl_err:
                app.ui.log(f"      ⚠️ [V68] 팩트 원장 초기화 실패 (비차단): {str(_fl_err)[:60]}")
                app.fact_ledger = None

    # ─────────────────────────────────────────────────────────────
    # 에피소드 단위 처리
    # ─────────────────────────────────────────────────────────────
    def _process_single_episode(
        self,
        working_ep: int,
        target_ep: int,
        prev_blueprints: list,
        success_count: int,
        fail_count: int,
    ) -> dict:
        """단일 에피소드 Blueprint 생성 처리. 루프 상태를 dict로 반환."""
        ctx = self.ctx

        # 이미 설계도가 존재하면 스킵 — [Sweep54] prev_blueprints에도 추가 (연속성 gap 방지)
        _existing_bp = ctx.current_project.get_blueprint(working_ep)
        if _existing_bp:
            prev_blueprints.append(_existing_bp)
            if len(prev_blueprints) > 30:
                prev_blueprints[:] = prev_blueprints[-30:]
            ctx.ui.log(f"   ⏭️  제{working_ep}화 - 기존 설계도 존재, 스킵")
            return {"next_ep": working_ep + 1, "success_count": success_count, "fail_count": fail_count}

        # [V60.83] 직전 화 Blueprint 필수 체크 (연속성 보장)
        if working_ep > 1:
            prev_bp_check = ctx.current_project.get_blueprint(working_ep - 1)
            if not prev_bp_check:
                ctx.ui.log(f"🚨 [V60.83] 제{working_ep - 1}화 Blueprint 없음! 연속성 보장 불가.")
                ctx.ui.log(f"   → 제{working_ep - 1}화를 먼저 생성하세요.")
                if callable(ctx.audit_event):
                    ctx.audit_event(
                        "continuity_block",
                        f"ep_{working_ep}_blocked_no_prev",
                        {"blocked_ep": working_ep, "missing_ep": working_ep - 1},
                    )
                return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 컨텍스트 확보
        if callable(ctx.get_arc_context_for_episode):
            arc_idx, arc_data = ctx.get_arc_context_for_episode(working_ep)
        else:
            arc_idx, arc_data = 0, {}
        if arc_idx is None or arc_data is None:
            ctx.ui.log(f"❌ [V60.80] 제{working_ep}화의 Arc 컨텍스트를 찾을 수 없습니다.")
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        ep_start_val = arc_data.get("ep_start")
        if ep_start_val is None or not isinstance(ep_start_val, int):
            ctx.ui.log(f"⚠️ [Stop] Arc ep_start 누락: arc_idx={arc_idx}")
            if callable(ctx.audit_event):
                ctx.audit_event("data_missing", "arc ep_start missing", {"arc_idx": arc_idx})
            return {"next_ep": working_ep, "success_count": success_count, "fail_count": fail_count, "break": True}

        # Arc 데이터 검증
        arc_data_validated = (
            ctx.validate_arc_data_fields(arc_data, arc_idx)
            if callable(getattr(ctx, "validate_arc_data_fields", None))
            else None
        )
        if arc_data_validated:
            arc_data = arc_data_validated

        arc_no = arc_data.get("arc_no", arc_idx + 1)

        # Entity Registry 추출/캐시
        entity_registry_for_stage3 = self._get_entity_registry(arc_idx)

        # 직전 Blueprint 로드
        prev_blueprint = self._load_prev_blueprint(working_ep)

        # 주인공 이름 추출
        protagonist_name_for_stage3 = self._get_protagonist_name_safe()

        # Three Phase Blueprint Generation
        ctx.ui.log(
            f"\n   📐 제{working_ep}화 Blueprint 생성 중... (Arc {arc_no}, 주인공: {protagonist_name_for_stage3})"
        )
        self._set_agent_telemetry_context(ep_num=working_ep)

        # [V67.1] protagonist_config 추출
        _bp_protagonist_config = {}
        try:
            _bp_bible_root = ctx.current_project.master_bible.get("MasterBible", ctx.current_project.master_bible)
            _bp_protagonist_config = _bp_bible_root.get("protagonist_config", {})
        except Exception as _e:
            _logging.warning("[Stage3] protagonist_config 추출 실패 (기본값 사용): %s", _e)

        blueprint, pipeline_result = self._generate_blueprint(
            working_ep,
            arc_data,
            arc_idx,
            prev_blueprint,
            prev_blueprints,
            entity_registry_for_stage3,
            protagonist_name_for_stage3,
            _bp_protagonist_config,
        )

        # 결과 처리
        if blueprint and pipeline_result.get("final_verdict") in (
            "PASS",
            "PASS_WITH_WARNING",
        ):  # [TF-32-S3]
            return self._handle_success(
                working_ep, arc_no, arc_data, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
            )
        else:
            return self._handle_failure(working_ep, pipeline_result, success_count, fail_count, arc_no=arc_no)

    # ─────────────────────────────────────────────────────────────
    # Entity Registry 캐시
    # ─────────────────────────────────────────────────────────────
    def _get_entity_registry(self, arc_idx: int):
        """[V61.6] Arc 단위 Entity Registry 캐시 관리"""
        ctx = self.ctx

        if self._entity_cache_arc_idx != arc_idx:
            ctx.ui.log(f"      ⏳ Entity Registry 추출 중... (Arc {arc_idx}, 첫 호출)")
            try:
                if ctx.agents and "state_extractor" in ctx.agents and ctx.current_project.arcs:
                    all_arcs_for_entity = list(ctx.current_project.arcs)[: arc_idx + 1]
                    if all_arcs_for_entity:
                        state_for_entity = ctx.agents["state_extractor"].extract_cumulative_state(all_arcs_for_entity)
                        self._cached_entity_registry = (
                            state_for_entity.get("entity_registry") if state_for_entity else None
                        )
                        if self._cached_entity_registry:
                            stage3_protag = ctx.get_protagonist_name() if callable(ctx.get_protagonist_name) else ""
                            if callable(getattr(ctx, "fix_entity_registry_protagonist", None)):
                                self._cached_entity_registry = ctx.fix_entity_registry_protagonist(
                                    self._cached_entity_registry, stage3_protag
                                )
                            total_entities = sum(
                                len(v) for v in self._cached_entity_registry.values() if isinstance(v, list)
                            )
                            ctx.ui.log(f"      📋 [V61] Entity Registry 추출: {total_entities}개 엔티티")
                    else:
                        self._cached_entity_registry = None
                else:
                    self._cached_entity_registry = None
                self._entity_cache_arc_idx = arc_idx
            except Exception as entity_err:
                ctx.ui.log(f"      ⚠️ [V61] Entity Registry 추출 실패: {str(entity_err)[:50]}")
                self._cached_entity_registry = None
                # [P0] 실패한 arc_idx 캐싱 — 동일 arc 무한 재시도 방지
                self._entity_cache_arc_idx = arc_idx
        else:
            ctx.ui.log(f"      ♻️ [V61.6] Entity Registry 캐시 재사용 (Arc {arc_idx})")

        return self._cached_entity_registry

    def _load_prev_blueprint(self, working_ep: int):
        """직전 Blueprint 로드 [V61.3 보호]"""
        prev_blueprint = None
        try:
            prev_blueprint = self.ctx.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None
        except Exception as prev_bp_err:
            _logging.error(f" [V61.3] prev_blueprint 로드 크래시: {str(prev_bp_err)[:100]}")
            _logging.error(_traceback.format_exc())
            self.ctx.ui.log("      ⚠️ 직전 Blueprint 로드 실패, None으로 진행")
        # [C3-P1-5] prev_blueprint 미존재 시 경고 강화
        if prev_blueprint is None and working_ep > 1:
            _logging.warning("[Stage3] prev_blueprint is None for ep %d (ep>1) — 연속성 참조 없이 진행", working_ep)
            self.ctx.ui.log(f"      ⚠️ 제{working_ep - 1}화 Blueprint 없음 — 연속성 참조 없이 진행")
        return prev_blueprint

    def _get_protagonist_name_safe(self) -> str:
        """주인공 이름 추출 [V61.3 보호] [C4-P1-3] callable 사전 검사"""
        protagonist_name = "주인공"
        if callable(getattr(self.ctx, "get_protagonist_name", None)):
            try:
                protagonist_name = self.ctx.get_protagonist_name()
            except Exception as protag_err:
                _logging.error(f" [V61.3] protagonist_name 추출 크래시: {str(protag_err)[:100]}")
                _logging.error(_traceback.format_exc())
                self.ctx.ui.log("      ⚠️ 주인공 이름 추출 실패, 기본값 사용")
        else:
            _logging.debug("[C4-P1-3] ctx.get_protagonist_name이 callable이 아님 — 기본값 사용")
        return protagonist_name

    def _extract_arc_time_markers(self, arc_data: dict) -> list:
        """[NS-4] Arc tactical_doc에서 시간 마커 추출 (regex, LLM 0회)"""
        import re as _re

        _tactical = arc_data.get("tactical_doc") or ""
        _beats = arc_data.get("beat_sequence") or ""
        if isinstance(_beats, list):
            _beats = " ".join(str(b) for b in _beats)
        _text = str(_tactical) + "\n" + str(_beats)
        _patterns = [
            r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",  # 2006년 7월 12일
            r"\d{1,2}월\s*\d{1,2}일",  # 7월 12일
            r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",  # 5월 말
            r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",  # 2달 후
        ]
        _found = []
        for _p in _patterns:
            _found.extend(_re.findall(_p, _text))
        return list(dict.fromkeys(_found))[:5]

    def _extract_timeline_start_end(self, arc_data: dict) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        """[NS-4] state_changes.timeline의 시작/종료 시점(연,월) 추출."""
        import re as _re

        def _parse_point(raw, *, pick: str) -> tuple[int, int] | None:
            if isinstance(raw, dict):
                year = raw.get("year")
                month = raw.get("month")
                if year is not None and month is not None:
                    try:
                        return (int(year), int(month))
                    except (TypeError, ValueError):
                        return None
                return None

            text = str(raw or "").strip()
            if not text:
                return None
            _year_m = _re.search(r"(\d{4})년", text)
            _year = int(_year_m.group(1)) if _year_m else 0
            _months = [int(m) for m in _re.findall(r"(\d{1,2})월", text)]
            if not _months:
                return None
            _month = _months[0] if pick == "start" else _months[-1]
            return (_year, _month)

        timeline = arc_data.get("state_changes", {}).get("timeline", {})
        if not isinstance(timeline, dict):
            return None, None
        return _parse_point(timeline.get("start"), pick="start"), _parse_point(timeline.get("end"), pick="end")

    def _timeline_start_end_raw_equal(self, arc_data: dict) -> bool:
        """[NS-4] timeline.start/end가 사실상 동일 표현인지 확인."""
        timeline = arc_data.get("state_changes", {}).get("timeline", {})
        if not isinstance(timeline, dict):
            return False
        start_raw = timeline.get("start")
        end_raw = timeline.get("end")
        if not start_raw or not end_raw:
            return False
        return str(start_raw).strip() == str(end_raw).strip()

    # ─────────────────────────────────────────────────────────────
    # Blueprint 생성 (LLM 호출)
    # ─────────────────────────────────────────────────────────────
    def _generate_blueprint(
        self,
        working_ep,
        arc_data,
        arc_idx,
        prev_blueprint,
        prev_blueprints,
        entity_registry,
        protagonist_name,
        protagonist_config,
    ):
        """[V60.80] Three Phase Blueprint Generation — LLM 호출 + 스피너"""
        ctx = self.ctx
        from modules.core.spinners import StageSpinner

        _started_at = _time.perf_counter()
        try:
            _bp_semantic_ctx = ""
            _s3_work_focus: dict[str, object] = {}
            _s3_plan = None
            _source_counts: dict[str, int] = {}
            _coverage_warnings: list[str] = []

            # [S3-I1] Smart Context Retrieval — 과거 유사 Blueprint 참조
            try:
                _s3_memory = getattr(self.app, "vec_memory", None) or getattr(self.app, "memory", None)
                _s3_advisor = getattr(self.app, "context_advisor", None)
                _s3_genre = ""
                if hasattr(self.app, "selected_genre") and self.app.selected_genre:
                    _s3_genre = self.app.selected_genre.get("type", "")

                from modules.validation.threshold_helper import _threshold as _s3_th

                _s3_sc_enabled = bool(_s3_th("smart_retrieval.enabled", False)) and bool(
                    _s3_th("smart_retrieval.stage3_enabled", False)
                )
                if _s3_sc_enabled and _s3_advisor and _s3_memory:
                    _s3_npc_roster = []
                    if entity_registry and isinstance(entity_registry, dict):
                        for _cat_items in entity_registry.values():
                            if isinstance(_cat_items, list):
                                for _item in _cat_items[:10]:
                                    _name = _item.get("name", "") if isinstance(_item, dict) else str(_item)
                                    if _name and _name not in _s3_npc_roster:
                                        _s3_npc_roster.append(_name)

                    _s3_work_focus = _resolve_stage3_work_focus(
                        ctx,
                        arc_data=arc_data,
                        prev_blueprints=prev_blueprints[-5:] if prev_blueprints else [],
                        entity_registry=entity_registry,
                    )
                    _s3_plan = _s3_advisor.plan_stage3_retrieval(
                        arc_data=arc_data,
                        prev_blueprints=prev_blueprints[-5:] if prev_blueprints else [],
                        current_ep=working_ep,
                        npc_roster=_s3_npc_roster[:10],
                        genre=_s3_genre,
                        work_focus=_s3_work_focus,
                    )
                    _s3_parts = []
                    # NOTE: S3 전용 키 없음 — S4의 vector_max_results_s4를 의도적으로 공유
                    _s3_max_results = int(_s3_th("context.vector_max_results_s4", 16))
                    for _slot in getattr(_s3_plan, "slots", []) or []:
                        _slot_query = str(getattr(_slot, "query", "") or "").strip()
                        if not _slot_query:
                            continue
                        _slot_source = str(getattr(_slot, "source", "vec_memory") or "vec_memory")
                        _slot_category = str(getattr(_slot, "category", "stage3") or "stage3")
                        _slot_max = int(getattr(_slot, "max_chars", 0) or 0) or 2000
                        try:
                            if _slot_source == "db_npc_history" and hasattr(_s3_memory, "retrieve_npc_context"):
                                _s3_text = _s3_memory.retrieve_npc_context(
                                    npc_names=_s3_npc_roster[:5],
                                    current_ep=working_ep,
                                    max_results=_s3_max_results,
                                )
                            elif _slot_source == "db_npc_relationship":
                                _s3_text = _build_stage3_relationship_context(
                                    getattr(ctx.current_project, "db", None),
                                    npc_names=_s3_npc_roster[:6],
                                    protagonist_name=protagonist_name,
                                )
                            else:
                                _s3_text = _s3_memory.retrieve_multi_query_context(
                                    queries=[_slot_query],
                                    current_ep=working_ep,
                                    n_per_query=3,
                                    max_results=_s3_max_results,
                                )
                            if _s3_text:
                                _s3_parts.append(f"[SC:{_slot_category}]\n{str(_s3_text)[:_slot_max]}")
                        except Exception as _s3_slot_err:
                            _logging.warning("[SilentPass:SC:Stage3] 슬롯 %s 실패: %s", _slot_category, _s3_slot_err)
                    if _s3_parts:
                        _bp_semantic_ctx = "\n\n".join(_s3_parts)
                        _logging.info("[S3-I1] Stage3 SC 검색 완료: %d건, %d자", len(_s3_parts), len(_bp_semantic_ctx))
            except Exception as _s3_sc_err:
                _logging.warning("[SilentPass:SC:Stage3] SC 검색 실패 (비차단): %s", _s3_sc_err)

            # [TF9] Treatment Block 직접 주입 — arc 압축으로 인한 정보 손실 보완
            # arc_idx = plot_roadmap의 블록 인덱스 (Arc 1→0, Arc 2→1, ...)
            # plot_roadmap[arc_idx]가 현재 아크 전체(ep_start~ep_end)의 원본 블록
            try:
                _master_bible = getattr(ctx.current_project, "master_bible", None) or {}
                _bible_root = _master_bible.get("MasterBible", _master_bible)
                _plot_roadmap = _bible_root.get("plot_roadmap", [])
                if isinstance(_plot_roadmap, list) and 0 <= arc_idx < len(_plot_roadmap):
                    _block = _plot_roadmap[arc_idx]
                    if isinstance(_block, dict):
                        _ep_start = arc_data.get("ep_start", working_ep)
                        _ep_end = arc_data.get("ep_end", working_ep)
                        _block_fields = []
                        for _f in (
                            "title",
                            "emotional_beat",
                            "foreshadow",
                            "power_shift",
                            "event_villain",
                            "solution",
                            "reward",
                        ):
                            if _block.get(_f):
                                _block_fields.append(f"  {_f}: {_block[_f]}")
                        _content = _block.get("content", {})
                        if isinstance(_content, dict):
                            for _cf in ("context", "event_villain", "solution"):
                                if _content.get(_cf):
                                    _block_fields.append(f"  content.{_cf}: {_content[_cf]}")
                        # [V74] genre_ext 주입 — 장르 특화 정보 (투자물: capital 등)
                        _genre_ext = _block.get("genre_ext", {})
                        if isinstance(_genre_ext, dict) and _genre_ext:
                            _ge_lines = []
                            for _gk, _gv in _genre_ext.items():
                                if isinstance(_gv, dict | list):
                                    _ge_lines.append(f"    {_gk}: {_json.dumps(_gv, ensure_ascii=False)}")
                                else:
                                    _ge_lines.append(f"    {_gk}: {_gv}")
                            _block_fields.append("  genre_ext:\n" + "\n".join(_ge_lines))
                        if _block_fields:
                            _tb_header = (
                                f"[원본 Treatment Block — 아크 {_ep_start}~{_ep_end}화 전체 참조용]\n"
                                f"⚠️ 현재 화는 {working_ep}화입니다. 위의 아크 설계(arc_focus)에서 "
                                f"{working_ep}화에 배정된 내용만 구현하세요. "
                                f"블록의 세부 정보(특정 NPC 만남·스킬·장소 등)는 아크 설계의 현재 화 베아트에 "
                                f"맞을 때만 사용하고, 이후 화의 내용은 보류하세요."
                            )
                            _tb_text = _tb_header + "\n" + "\n".join(_block_fields)
                            _bp_semantic_ctx = _tb_text + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
                            _logging.info(
                                "[TF9] Treatment Block 주입 완료 (arc_idx=%d, ep=%d~%d, %d자)",
                                arc_idx,
                                _ep_start,
                                _ep_end,
                                len(_tb_text),
                            )
            except Exception as _tb_err:
                _logging.warning("[SilentPass:TreatmentBlock] 추출 실패 (비차단): %s", _tb_err)

            # [NS-4] 이전 Arc 시간 마커 → Blueprint 컨텍스트 주입 (LLM 0회)
            try:
                if arc_idx > 0:
                    _all_arcs = getattr(ctx.current_project, "arcs", []) or []
                    if len(_all_arcs) >= arc_idx:
                        _prev_arc_data = _all_arcs[arc_idx - 1]
                        _prev_markers = self._extract_arc_time_markers(_prev_arc_data)
                        _cur_markers = self._extract_arc_time_markers(arc_data)
                        if _prev_markers or _cur_markers:
                            _ta_lines = ["[Arc 시간 연속성 참고]"]
                            if _prev_markers:
                                _ta_lines.append(f"이전 Arc 종료 시점 마커: {', '.join(_prev_markers)}")
                            if _cur_markers:
                                _ta_lines.append(f"현재 Arc 시간 마커: {', '.join(_cur_markers)}")

                            # [NS-4] timeline start/end 동일값 경고
                            if self._timeline_start_end_raw_equal(arc_data):
                                _ta_lines.append(
                                    "⚠️ [NS-4] 현재 Arc timeline.start와 end가 동일하게 기입됨 — "
                                    "시작/종료 시점을 분리해 서술하세요."
                                )

                            # [NS-4] Arc 시작 시점 역전 경고 (현재 시작 < 이전 시작)
                            _prev_start, _ = self._extract_timeline_start_end(_prev_arc_data)
                            _cur_start, _ = self._extract_timeline_start_end(arc_data)
                            if _prev_start and _cur_start and _prev_start[0] > 0 and _cur_start[0] > 0:
                                if _cur_start < _prev_start:
                                    _ta_lines.append(
                                        "⚠️ [NS-4] Arc timeline 역전 감지 — 현재 Arc 시작 시점이 "
                                        "이전 Arc 시작 시점보다 과거입니다. 시간 순서를 재점검하세요."
                                    )
                            _ta_lines.append(
                                "※ 현재 화에서 과거 사건 언급 시 '며칠 전'/'얼마 전' 같은 표현이 "
                                "위 시간 간격과 일치하는지 확인하세요."
                            )
                            _ta_text = "\n".join(_ta_lines)
                            _bp_semantic_ctx = _ta_text + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
                            _logging.info(
                                "[NS-4] Arc 시간 마커 주입: prev=%s, cur=%s",
                                _prev_markers,
                                _cur_markers,
                            )
            except Exception as _ns4_err:
                _logging.debug("[NS-4] 시간 마커 주입 실패 (비차단): %s", _ns4_err)

            _world_state_advisory = _build_world_state_advisory(getattr(ctx, "world_state", None))
            if _world_state_advisory:
                _bp_semantic_ctx = _world_state_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

            _style_guide_advisory = _build_style_guide_advisory(getattr(ctx, "current_project", None))
            if _style_guide_advisory:
                _bp_semantic_ctx = _style_guide_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

            _fact_ledger_advisory = _build_fact_ledger_advisory(getattr(self.ctx.current_project, "db", None))
            if _fact_ledger_advisory:
                _bp_semantic_ctx = _fact_ledger_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

            _seed_advisory = _build_stale_seed_advisory(getattr(self.ctx.current_project, "db", None), working_ep)
            if _seed_advisory:
                _bp_semantic_ctx = _seed_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")

            _work_focus_advisory = _build_stage3_work_focus_advisory(
                _s3_work_focus
                or _resolve_stage3_work_focus(
                    ctx,
                    arc_data=arc_data,
                    prev_blueprints=prev_blueprints[-5:] if prev_blueprints else [],
                    entity_registry=entity_registry,
                ),
                arc_data=arc_data,
                entity_registry=entity_registry,
                ctx=ctx,
                protagonist_name=protagonist_name,
            )
            if _work_focus_advisory:
                _bp_semantic_ctx = _work_focus_advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
            _source_counts = _summarize_retrieval_sources(_s3_plan)
            if not _source_counts and _bp_semantic_ctx:
                _source_counts = {"legacy_semantic_context": 1}
            if _s3_work_focus and not _work_focus_advisory:
                _coverage_warnings.append("missing_work_slot_summary")
            if _s3_work_focus and _s3_plan and not any(
                str(getattr(_slot, "category", "")).startswith("work_")
                for _slot in (getattr(_s3_plan, "slots", []) or [])
            ):
                _coverage_warnings.append("work_focus_without_slots")
            if (
                _source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0
                and "[관계 의미 질의]" not in _bp_semantic_ctx
            ):
                _coverage_warnings.append("missing_relation_slice")
            _record_retrieval_observation(
                self.app,
                ep_num=working_ep,
                stage="stage3",
                observation={
                    "work_focus_present": bool(_s3_work_focus),
                    "tracking_slots_count": len(_s3_work_focus.get("tracking_slots") or []) if isinstance(_s3_work_focus, dict) else 0,
                    "scene_engines_count": len(_s3_work_focus.get("mandatory_scene_engines") or []) if isinstance(_s3_work_focus, dict) else 0,
                    "registry_profiles_count": len(_s3_work_focus.get("registry_profiles") or []) if isinstance(_s3_work_focus, dict) else 0,
                    "planned_slots_count": len(getattr(_s3_plan, "slots", []) or []) if _s3_plan else 0,
                    "advisor_path_used": bool(_s3_plan),
                    "work_slot_summary_included": "[작품 추적 슬롯 요약]" in _bp_semantic_ctx,
                    "relation_slice_included": "[관계 의미 질의]" in _bp_semantic_ctx,
                    "source_counts": _source_counts,
                    "coverage_warnings": _coverage_warnings,
                    "vector_context_chars": len(_bp_semantic_ctx),
                },
            )

            with StageSpinner(3, f"제{working_ep}화") as _s3_spinner:
                # [V67][S3-I5] 이전 원고 로드 — 단일 쿼리로 최적화 (N+1 → 1)
                _prev_ms_for_bp = []
                _recent_manuscripts = ctx.current_project.db.get_recent_manuscripts(before_ep=working_ep, limit=30)
                for _ms_row in _recent_manuscripts:
                    _ms_text = _ms_row.get("content", "")
                    _ms_ep_num = _ms_row.get("ep_num", 0)
                    if _ms_text:
                        _prev_ms_for_bp.append(f"━━━ 제{_ms_ep_num}화 원고 ━━━\n{_ms_text}")
                _prev_ms_text_for_bp = "\n\n".join(_prev_ms_for_bp) if _prev_ms_for_bp else ""
                if len(_prev_ms_text_for_bp) > ContextLimits.MAX_CONTEXT_CHARS:
                    _prev_ms_text_for_bp = (
                        _prev_ms_text_for_bp[: ContextLimits.MAX_CONTEXT_CHARS]
                        + f"\n... ({ContextLimits.MAX_CONTEXT_CHARS // 1000}K자 절삭)"
                    )
                if _prev_ms_for_bp:
                    _logging.info(
                        f" [V67] Blueprint용 이전 원고 {len(_prev_ms_for_bp)}개 로드 ({len(_prev_ms_text_for_bp):,}자)"
                    )

                # [TF-4] prev_hud 추출 — BlockingValidator consistency checks용
                _bp_prev_hud = None
                if hasattr(ctx, "sys") and ctx.sys and hasattr(ctx.sys, "hud") and ctx.sys.hud:
                    try:
                        _bp_prev_hud = ctx.sys.hud.pro_root
                        if not isinstance(_bp_prev_hud, dict):
                            _bp_prev_hud = None
                    except Exception:
                        _bp_prev_hud = None

                _s3_spinner.update_detail(f"제{working_ep}화 · Blueprint 생성")
                print(f"      ⏳ 제{working_ep}화 Blueprint 생성 시작 (최대 10회 시도)...")
                blueprint, pipeline_result = ctx.agents["three_phase_bp"].generate(
                    ep_num=working_ep,
                    arc_data=arc_data,
                    prev_blueprint=prev_blueprint,
                    prev_blueprints=prev_blueprints[-30:] if prev_blueprints else [],
                    max_retries=9,
                    director=ctx.agents["director"],
                    arc_idx=arc_idx,
                    entity_registry=entity_registry,
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    state_tracker=ctx.state_tracker,
                    db=ctx.current_project.db,
                    semantic_context=_bp_semantic_ctx,
                    prev_manuscripts_text=_prev_ms_text_for_bp,
                    adversarial_self_play=ctx.adversarial_self_play,
                    prev_hud=_bp_prev_hud,
                )
                # [TF-48] Blueprint 생성 결과 요약
                _verdict = pipeline_result.get("final_verdict", "UNKNOWN")
                _bp_score = pipeline_result.get(
                    "last_score", pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
                )
                print(f"      📊 제{working_ep}화 Blueprint 결과: {_verdict} (score={_bp_score})")

        except Exception as gen_err:
            _logging.error(f" [V61.3] 제{working_ep}화 Blueprint 생성 크래시: {str(gen_err)[:100]}")
            _logging.error(_traceback.format_exc())

            ctx.ui.log(f"❌ [V60.80] 제{working_ep}화 생성 실패: {str(gen_err)[:100]}")
            if callable(ctx.audit_event):
                ctx.audit_event("blueprint_gen_error", str(gen_err)[:200], {"ep_num": working_ep})
            blueprint = None
            pipeline_result = {"final_verdict": "ERROR", "error": str(gen_err)[:200]}

        if not isinstance(pipeline_result, dict):
            pipeline_result = {"final_verdict": "ERROR", "error": "invalid_pipeline_result"}
        pipeline_result["_stage3_duration_ms"] = max(0, int((_time.perf_counter() - _started_at) * 1000))
        pipeline_result["_stage3_observability"] = {
            "semantic_ctx_chars": len(_bp_semantic_ctx),
            "source_counts": _normalize_semantic_source_counts(_source_counts),
            "coverage_warnings": list(_coverage_warnings),
            "advisor_path_used": bool(_s3_plan),
            "planned_slots_count": len(getattr(_s3_plan, "slots", []) or []) if _s3_plan else 0,
            "work_focus_present": bool(_s3_work_focus),
        }
        return blueprint, pipeline_result

    # ─────────────────────────────────────────────────────────────
    # 결과 처리
    # ─────────────────────────────────────────────────────────────
    def _handle_success(
        self, working_ep, arc_no, arc_data, blueprint, pipeline_result, prev_blueprints, success_count, fail_count
    ) -> dict:
        """Blueprint 생성 성공 시 저장 + 메트릭 기록"""
        ctx = self.ctx
        _final_verdict = pipeline_result.get("final_verdict", "PASS")
        _quality_gate_failed = bool(pipeline_result.get("quality_gate_failed", False))
        _quality_risk = bool(pipeline_result.get("quality_risk", False) or _quality_gate_failed)
        _observability_flags = _build_stage3_observability_flags(pipeline_result.get("_stage3_observability"))
        _duration_ms = int(pipeline_result.get("_stage3_duration_ms") or 0) or None

        # [LOG-1] 판정 경로 세션 로깅
        _sl = getattr(ctx, "session_logger", None)
        if _sl:
            try:
                _sl.log_decision(
                    stage="stage3",
                    ep_num=working_ep,
                    decision_type="blueprint",
                    result=_final_verdict,
                    score=pipeline_result.get("last_score", 0),
                    arc_no=arc_no,
                    quality_risk=_quality_risk,
                )
            except Exception:
                pass

        try:
            _db = getattr(getattr(ctx, "current_project", None), "db", None)
            _attempt_num = self._extract_stage3_attempt_num(pipeline_result)
            _session_id = resolve_logging_session_id(getattr(ctx, "current_project", None))
            _attempt_key = build_attempt_key(
                stage=3,
                ep_num=working_ep,
                arc_num=arc_no,
                attempt_num=_attempt_num,
                session_id=_session_id,
            )
            _score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get(
                "selected_score", 0
            )
            _selected_strategy = str(
                pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy", "unknown") or "unknown"
            )
            _candidate_key = build_candidate_key(strategy=_selected_strategy, fallback="stage3")
            _artifact_meta = snapshot_logged_artifact(
                getattr(ctx, "current_project", None),
                stage=3,
                ep_num=working_ep,
                arc_num=arc_no,
                attempt_num=_attempt_num,
                candidate_key=_candidate_key,
                artifact_kind="final_blueprint",
                payload=blueprint if isinstance(blueprint, dict) else None,
            )
            if not isinstance(_score, int):
                try:
                    _score = int(_score)
                except (ValueError, TypeError):
                    _score = 0
            if getattr(ctx, "pass_rate_monitor", None):
                try:
                    ctx.pass_rate_monitor.record_attempt(
                        stage=3,
                        episode=working_ep,
                        arc=arc_no,
                        attempt_num=_attempt_num,
                        success=_final_verdict in ("PASS", "PASS_WITH_WARNING"),
                        generation_method="blueprint",
                        attempt_key=_attempt_key,
                        final_verdict=str(_final_verdict),
                        candidate_key=_candidate_key,
                        content_hash=_artifact_meta["content_hash"],
                        artifact_path=_artifact_meta["artifact_path"],
                    )
                except Exception as _prm_err:
                    _logging.debug("[stage3_prm] Stage3 PASS 기록 실패 (비차단): %s", _prm_err)
            if _db and hasattr(_db, "save_stage_attempt"):
                _director = getattr(getattr(ctx, "agents", {}), "get", lambda *_: None)("director")
                _model = getattr(_director, "primary_model", None) if _director else None
                _prompt_version = _build_stage3_prompt_version()
                _db.save_stage_attempt(
                    stage=3,
                    verdict=str(_final_verdict),
                    attempt_num=_attempt_num,
                    ep_num=working_ep,
                    arc_num=arc_no,
                    score=_score,
                    model=str(_model) if _model else None,
                    session_id=_session_id,
                    attempt_key=_attempt_key,
                    prompt_version=_prompt_version,
                    duration_ms=_duration_ms,
                    advisory_flags=_observability_flags or None,
                    candidate_key=_candidate_key,
                    content_hash=_artifact_meta["content_hash"],
                    artifact_path=_artifact_meta["artifact_path"],
                )
        except Exception as _sa_err:
            _logging.debug("[stage_attempts] Stage3 PASS 기록 실패 (비차단): %s", _sa_err)

        if isinstance(blueprint, dict):
            blueprint["_stage3_meta"] = {
                "final_verdict": _final_verdict,
                "quality_gate_failed": _quality_gate_failed,
                "quality_risk": _quality_risk,
                "last_score": pipeline_result.get("last_score", 0),
            }
            # [P0] _stage3_meta에 통합 — 최상위 중복 키 제거

        # [TF-49] Blueprint 소지품 갭 어노테이션
        if isinstance(blueprint, dict) and working_ep > 1:  # Ep 1 스킵 (초기 소지품 미확정)
            _inv_gaps = self._detect_inventory_gaps(blueprint, arc_data)
            if _inv_gaps:
                blueprint["_inventory_gaps"] = _inv_gaps
                ctx.ui.log(f"   ⚠️ [TF-49] 소지품 갭 {len(_inv_gaps)}건: {', '.join(g['item'] for g in _inv_gaps)}")

        # 무결성 검증 후 저장
        # [S3-N-P1-3] DI 콜백 None 방어
        if isinstance(blueprint, dict):
            _prev_published_text = ""
            try:
                _db = getattr(getattr(ctx, "current_project", None), "db", None)
                _prev_row = _db.get_manuscript(working_ep - 1) if _db and working_ep > 1 else None
                if isinstance(_prev_row, dict):
                    _prev_published_text = str(
                        _prev_row.get("content")
                        or _prev_row.get("corrected_manuscript")
                        or _prev_row.get("manuscript")
                        or ""
                    )
                elif _prev_row:
                    _prev_published_text = str(_prev_row)
            except Exception as _pin_prev_err:
                _logging.debug("[Stage3] previous manuscript lookup failed (non-blocking): %s", _pin_prev_err)

            _arc_tactical_text = ""
            try:
                _arc_tactical_text = extract_episode_tactical(
                    arc_data.get("tactical_doc", ""),
                    working_ep,
                    episode_details=arc_data.get("episode_details"),
                )
            except Exception as _pin_tactical_err:
                _logging.debug("[Stage3] arc tactical extract failed (non-blocking): %s", _pin_tactical_err)

            _pin_result = apply_continuity_pins(
                blueprint,
                previous_published_text=_prev_published_text,
                arc_tactical_text=_arc_tactical_text,
            )
            blueprint = _pin_result.get("blueprint", blueprint)
            if _pin_result.get("changes"):
                blueprint["_continuity_pins"] = _pin_result["changes"]
                ctx.ui.log(f"   [PinGuard] ep {working_ep} continuity pins applied: {len(_pin_result['changes'])}")
            if _pin_result.get("unresolved"):
                ctx.ui.log(f"   ?슚 [PinGuard] ep {working_ep} unresolved continuity pins")
                if callable(ctx.audit_event):
                    ctx.audit_event(
                        "continuity_pin_unresolved",
                        "stage3 continuity pin unresolved",
                        {"ep_num": working_ep, "items": _pin_result["unresolved"][:3]},
                    )
                return {
                    "next_ep": working_ep + 1,
                    "success_count": success_count,
                    "fail_count": fail_count + 1,
                    "break": True,
                }

        if callable(ctx.validate_blueprint_integrity) and not ctx.validate_blueprint_integrity(blueprint):
            ctx.ui.log(f"   🚨 [Integrity] 제{working_ep}화 Blueprint 무결성 실패")
            if callable(ctx.audit_event):
                ctx.audit_event("integrity_fail", "blueprint integrity check failed", {"ep_num": working_ep})
            return {
                "next_ep": working_ep + 1,
                "success_count": success_count,
                "fail_count": fail_count + 1,
                "break": True,
            }  # [TF-R2-S3-08]

        # DB에 저장
        ctx.current_project.save_episode_blueprint(working_ep, blueprint)
        # [S3-N-P1-3] DI 콜백 None 방어
        if callable(ctx.safe_commit) and not ctx.safe_commit():
            ctx.ui.log(f"   🚨 [DB] 제{working_ep}화 Blueprint 커밋 실패")
            if callable(ctx.audit_event):
                ctx.audit_event("db_commit_error", "blueprint commit failed", {"ep_num": working_ep})
            return {
                "next_ep": working_ep + 1,
                "success_count": success_count,
                "fail_count": fail_count + 1,
                "break": True,
            }  # [TF-R2-S3-08]

        # prev_blueprints 업데이트
        prev_blueprints.append(blueprint)
        if len(prev_blueprints) > 30:
            prev_blueprints[:] = prev_blueprints[-30:]

        # 메트릭 기록
        # [S3-N-P1-3] DI 콜백 None 방어
        if callable(ctx.audit_event):
            ctx.audit_event(
                "blueprint_success",
                f"ep_{working_ep}_blueprint_generated",
                {
                    "ep_num": working_ep,
                    "arc_no": arc_no,
                    "strategy": pipeline_result.get("phases", {})
                    .get("generate", {})
                    .get("selected_strategy", "unknown"),
                    "score": pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0),
                    "final_verdict": _final_verdict,
                    "quality_risk": _quality_risk,
                },
            )

        ctx.ui.log(f"   ✅ 제{working_ep}화 Blueprint 저장 완료")
        # [P6-02] QualityDashboard Stage3 PASS 기록
        _qd = getattr(self.app, "quality_dashboard", None)
        if _qd is not None and hasattr(_qd, "record_validation"):
            try:
                _bp_score = pipeline_result.get("last_score")
                if _bp_score is None:
                    _bp_score = pipeline_result.get("phases", {}).get("generate", {}).get("selected_score")
                if _bp_score is None:
                    _bp_score = 1.0
                _qd.record_validation(
                    ep_num=working_ep,
                    result={
                        "decision": "PASS",
                        "score": _bp_score,
                        "violations": [],
                        "warnings": [],
                    },
                    stage=3,
                )
            except Exception as _e:
                _logging.debug("[Stage3] QualityDashboard PASS 기록 실패 (무시): %s", _e)
        return {"next_ep": working_ep + 1, "success_count": success_count + 1, "fail_count": 0}

    @staticmethod
    def _extract_stage3_attempt_num(pipeline_result: dict) -> int:
        """Convert pipeline retries(0-based) to attempt number(1-based)."""
        if not isinstance(pipeline_result, dict):
            return 1
        retries = pipeline_result.get("retries", 0)
        try:
            return max(1, int(retries) + 1)
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _resolve_stage3_arc_num(arc_no: int | None, pipeline_result: dict) -> int | None:
        """Recover arc number for REJECT path when available."""
        if isinstance(arc_no, int) and arc_no > 0:
            return arc_no
        if isinstance(pipeline_result, dict):
            candidate = pipeline_result.get("arc_no")
            try:
                candidate_int = int(candidate)
                if candidate_int > 0:
                    return candidate_int
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _build_stage3_reject_reason(pipeline_result: dict) -> str:
        """Assemble a compact, informative reject reason for stage_attempts logging."""
        if not isinstance(pipeline_result, dict):
            return ""

        parts: list[str] = []
        error_text = str(pipeline_result.get("error", "") or "").strip()
        if error_text:
            parts.append(error_text[:240])

        score = pipeline_result.get("last_score")
        if isinstance(score, int | float):
            parts.append(f"score={int(score)}")

        if pipeline_result.get("quality_gate_failed"):
            parts.append("quality_gate_failed=1")

        phases = pipeline_result.get("phases", {})
        if isinstance(phases, dict):
            generate = phases.get("generate", {})
            if isinstance(generate, dict):
                strategy = str(generate.get("selected_strategy", "") or "").strip()
                if strategy:
                    parts.append(f"strategy={strategy[:40]}")

            validate = phases.get("validate", {})
            if isinstance(validate, dict):
                verdict = str(validate.get("verdict", "") or "").strip()
                if verdict:
                    parts.append(f"validate_verdict={verdict[:20]}")
                issues_count = validate.get("issues_count")
                if isinstance(issues_count, int):
                    parts.append(f"issues={issues_count}")
                notes = str(validate.get("comparison_notes", "") or "").strip()
                if notes:
                    parts.append(f"notes={notes[:160]}")
                contradictions = validate.get("contradictions")
                if isinstance(contradictions, list) and contradictions:
                    _contr = "; ".join(str(c)[:60] for c in contradictions[:2])
                    if _contr:
                        parts.append(f"contradictions={_contr}")

        if not parts:
            verdict = str(pipeline_result.get("final_verdict", "REJECT") or "REJECT")
            parts.append(f"final_verdict={verdict[:20]}")

        return " | ".join(parts)[:500]

    def _detect_inventory_gaps(self, blueprint: dict, arc_data: dict) -> list[dict]:
        """[TF-49] Blueprint 참조 아이템 중 현재 미보유 항목 탐지."""
        ctx = self.ctx

        # 1. 현재 소지품
        owned = set()
        if ctx.world_state:
            try:
                owned = set(ctx.world_state.get_owned_items())
            except Exception as e:
                _logging.debug("[SilentPass:S3] get_owned_items failed: %s", e)
        if not owned:
            _cdb = getattr(self.app, "constraint_db", None)
            if _cdb:
                try:
                    owned = set(_cdb.get_current_inventory(arc_data.get("arc_no", 1) - 1))
                except Exception as e:
                    _logging.debug("[SilentPass:S3] get_current_inventory fallback failed: %s", e)

        # 2. Arc 계획된 신규 아이템 (미보유 중 이번 Arc에서 획득 예정)
        _sc = arc_data.get("state_constraints", {}) if isinstance(arc_data, dict) else {}
        planned = set()
        # [BUG-F] protagonist_items 우선 폴백
        for item in (_sc.get("protagonist_items") or _sc.get("items_acquired") or []):
            if item:
                planned.add(str(item))
        _end_eq = set(_sc.get("arc_end_state", {}).get("equipment", []))
        _start_eq = set(_sc.get("arc_start_state", {}).get("equipment", []))
        planned |= _end_eq - _start_eq

        # 3. Blueprint 참조 아이템 (구조화 필드 우선)
        referenced = {}  # item → source
        _ps = blueprint.get("protagonist_state", {})
        if isinstance(_ps, dict):
            for item in _ps.get("equipment") or []:
                if item:
                    referenced[str(item)] = "protagonist_state"

        # planned 아이템이 씬 텍스트에 언급되는지 확인
        scenes = blueprint.get("scene_breakdown") or blueprint.get("scenes") or {}
        if isinstance(scenes, dict):
            scenes = list(scenes.values())
        if isinstance(scenes, list):
            for i, scene in enumerate(scenes):
                scene_text = ""
                if isinstance(scene, dict):
                    scene_text = " ".join(str(v) for v in scene.values() if isinstance(v, str))
                elif isinstance(scene, str):
                    scene_text = scene
                for item in planned:
                    if item and item in scene_text and item not in referenced:
                        referenced[item] = f"scene_{i + 1}"

        integrated = blueprint.get("integrated_scenario", "")
        if isinstance(integrated, str):
            for item in planned:
                if item and item in integrated and item not in referenced:
                    referenced[item] = "integrated_scenario"

        # 4. 갭 = 참조됨 + 미보유
        return [
            {"item": item, "source": src, "note": "현재 미보유 — 획득 장면 필요"}
            for item, src in referenced.items()
            if item not in owned
        ]

    def _handle_failure(
        self, working_ep, pipeline_result, success_count, fail_count, arc_no: int | None = None
    ) -> dict:
        """Blueprint 생성 실패 시 처리. 항상 break=True를 반환하여 루프를 종료한다
        (순차 의존성: 후속 에피소드는 현재 에피소드 Blueprint에 의존)."""
        ctx = self.ctx

        ctx.ui.log(f"   ❌ 제{working_ep}화 Blueprint 생성 실패")

        # [LOG-1] 판정 경로 세션 로깅 (REJECT)
        _sl = getattr(ctx, "session_logger", None)
        if _sl:
            try:
                _sl.log_decision(
                    stage="stage3",
                    ep_num=working_ep,
                    decision_type="blueprint",
                    result=pipeline_result.get("final_verdict", "REJECT"),
                    score=pipeline_result.get("last_score", 0),
                )
            except Exception as e:
                _logging.debug("[TF-26] session_logger.log_decision failed: %s", str(e)[:100])

        try:
            _db = getattr(getattr(ctx, "current_project", None), "db", None)
            _final_verdict = str(pipeline_result.get("final_verdict", "REJECT"))
            _attempt_num = self._extract_stage3_attempt_num(pipeline_result)
            _arc_num = self._resolve_stage3_arc_num(arc_no=arc_no, pipeline_result=pipeline_result)
            _session_id = resolve_logging_session_id(getattr(ctx, "current_project", None))
            _attempt_key = build_attempt_key(
                stage=3,
                ep_num=working_ep,
                arc_num=_arc_num,
                attempt_num=_attempt_num,
                session_id=_session_id,
            )
            _reject_reason = self._build_stage3_reject_reason(pipeline_result)
            _score = pipeline_result.get("last_score") or pipeline_result.get("phases", {}).get("generate", {}).get(
                "selected_score", 0
            )
            _selected_strategy = str(
                pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy", "unknown") or "unknown"
            )
            _candidate_key = build_candidate_key(strategy=_selected_strategy, fallback="stage3")
            _observability_flags = _build_stage3_observability_flags(pipeline_result.get("_stage3_observability"))
            _duration_ms = int(pipeline_result.get("_stage3_duration_ms") or 0) or None
            _failure_category = _classify_stage3_failure_category(pipeline_result)
            if not isinstance(_score, int):
                try:
                    _score = int(_score)
                except (ValueError, TypeError):
                    _score = 0
            if getattr(ctx, "pass_rate_monitor", None):
                try:
                    ctx.pass_rate_monitor.record_attempt(
                        stage=3,
                        episode=working_ep,
                        arc=_arc_num,
                        attempt_num=_attempt_num,
                        success=False,
                        reject_reason=_reject_reason,
                        generation_method="blueprint",
                        attempt_key=_attempt_key,
                        final_verdict=_final_verdict,
                        candidate_key=_candidate_key,
                    )
                except Exception as _prm_err:
                    _logging.debug("[stage3_prm] Stage3 REJECT 기록 실패 (비차단): %s", _prm_err)
            if _db and hasattr(_db, "save_stage_attempt"):
                _director = getattr(getattr(ctx, "agents", {}), "get", lambda *_: None)("director")
                _model = getattr(_director, "primary_model", None) if _director else None
                _prompt_version = _build_stage3_prompt_version()
                _db.save_stage_attempt(
                    stage=3,
                    verdict=_final_verdict,
                    attempt_num=_attempt_num,
                    ep_num=working_ep,
                    arc_num=_arc_num,
                    score=_score,
                    failure_category=_failure_category,
                    reject_reason=_reject_reason,
                    model=str(_model) if _model else None,
                    duration_ms=_duration_ms,
                    advisory_flags=_observability_flags or None,
                    session_id=_session_id,
                    attempt_key=_attempt_key,
                    prompt_version=_prompt_version,
                    candidate_key=_candidate_key,
                )
        except Exception as _sa_err:
            _logging.debug("[stage_attempts] Stage3 REJECT 기록 실패 (비차단): %s", _sa_err)

        # [S3-N-P1-3] DI 콜백 None 방어
        if callable(ctx.audit_event):
            ctx.audit_event(
                "blueprint_fail",
                f"ep_{working_ep}_all_retries_exhausted",
                {"ep_num": working_ep, "final_verdict": pipeline_result.get("final_verdict", "UNKNOWN")},
            )
        try:
            _final_verdict = pipeline_result.get("final_verdict", "UNKNOWN")
            _score = pipeline_result.get("last_score", 0)
            if not isinstance(_score, int | float):
                try:
                    _score = float(_score)
                except (ValueError, TypeError):
                    _score = 0
            ctx.current_project.db.save_cost_record(
                session_id=resolve_logging_session_id(
                    getattr(ctx, "current_project", None),
                    fallback=f"ep_{working_ep}",
                ),
                scope_type="episode",
                scope_id=int(working_ep),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage3_reject",
                    "verdict": _final_verdict,
                    "score": _score,
                    "quality_gate_failed": bool(pipeline_result.get("quality_gate_failed", False)),
                },
            )
        except Exception as e:
            _logging.warning(f"[SilentPass:Stage3RejectMetric] {e!s:.120}")
        new_fail_count = fail_count + 1

        # [P6-02] QualityDashboard Stage3 REJECT 기록
        _qd = getattr(self.app, "quality_dashboard", None)
        if _qd is not None and hasattr(_qd, "record_validation"):
            try:
                _qd.record_validation(
                    ep_num=working_ep,
                    result={
                        "decision": "REJECT",
                        "score": 0,
                        "violations": [{"type": "blueprint_max_retries", "description": "Blueprint 최대 재시도 초과"}],
                        "warnings": [],
                    },
                    stage=3,
                )
            except Exception as _e:
                _logging.debug("[Stage3] QualityDashboard REJECT 기록 실패 (무시): %s", _e)
        # [TF-S3-02] 실패 에피소드에서 중단 (순차 의존성 보존)
        # 후속 에피소드는 현재 에피소드 Blueprint에 의존하므로 건너뛰기 금지
        return {
            "next_ep": working_ep,  # [TF-S3-02] 현재 에피소드에 머무름
            "success_count": success_count,
            "fail_count": new_fail_count,
            "break": True,  # 오케스트레이터 루프 종료
        }
