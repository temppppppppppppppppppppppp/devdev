"""Smart retrieval planner used by Stage2/4 and Director paths.

SC-1 focuses on planning (what to retrieve), not execution (how to retrieve).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from modules.validation.threshold_helper import _threshold


def _load_genre_hints() -> dict[str, list[str]]:
    """[INF-I7] config/smart_retrieval/genre_hints.yaml에서 장르 힌트 로드.

    YAML 로드 실패 시 하드코딩된 기본값을 반환한다.
    """
    yaml_path = Path(__file__).resolve().parent.parent.parent / "config" / "smart_retrieval" / "genre_hints.yaml"
    try:
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            # 값이 list[str]인지 간단 검증
            return {k: v for k, v in data.items() if isinstance(v, list)}
    except Exception as exc:
        logging.debug("[INF-I7] genre_hints.yaml 로드 실패, 하드코딩 폴백 사용: %s", exc)
    return _DEFAULT_GENRE_HINTS


_DEFAULT_GENRE_HINTS: dict[str, list[str]] = {
    "hunter": [
        "던전 클리어 각성 스킬 랭크",
        "보스 공략 파티 구성 전투 손실 회복",
        "게이트 붕괴 레이드 보상 길드 경쟁",
        "검술 체술 사격 마법 복합 전투",
        "장비 강화 제작 재료 경매 자원 채굴",
    ],
    "investment": [
        "포트폴리오 자산배분 주식 채권 부동산",
        "레버리지 손절 리스크 관리 금리 유동성",
        "매크로 이벤트 금리 환율 유동성",
        "원자재 선물 옵션 환헤지 변동성 관리",
        "M&A 지분 인수 규제 세무 회계",
    ],
    "fantasy": [
        "마법 검술 창술 궁술 체술 전투",
        "유물 계약 혈통 각성 의식",
        "왕국 음모 길드 전쟁 봉인 해제",
        "정령 소환 연금술 룬 각인 제작",
        "신성력 저주 해제 성물 축복 의식",
    ],
    "wuxia": [
        "검술 내공 경공 권법 장법",
        "문파 비급 심법 기연 수련",
        "강호 세력 암투 복수 의리",
        "영약 단약 독공 해독 경맥",
    ],
    "composer": [
        "작곡 편곡 사운드 디자인 멜로디",
        "음원 발매 차트 반응 저작권 수익",
        "공연 리허설 밴드 합주 프로듀싱",
    ],
    "cooking": [
        "식재료 손질 조리법 불 조절 플레이팅",
        "주방 동선 원가 관리 재고 회전 위생",
        "메뉴 개발 단골 확보 리뷰 대응 운영",
    ],
    "alt_history": [
        "역사 분기 정치 외교 군사 전략",
        "산업 기술 도입 개혁 세력 균형",
        "전쟁 억제 동맹 협상 정보전 심리전",
    ],
    "actor": [
        "대본 분석 캐릭터 구축 감정선 연기",
        "오디션 캐스팅 촬영 스케줄 현장 대응",
        "흥행 성적 평단 반응 이미지 관리",
    ],
    "sports": [
        "기술 훈련 체력 강화 경기 운영 전술",
        "부상 관리 재활 루틴 컨디션 조절",
        "리그 일정 상대 분석 기록 갱신",
    ],
    "medical": [
        "증상 감별 진단 검사 수술 처치",
        "응급 대응 중증도 분류 협진 프로토콜",
        "의료 윤리 병원 운영 연구 임상",
    ],
}


class RetrievalSources:
    """Canonical source identifiers for retrieval slots."""

    VEC_MEMORY = "vec_memory"
    DB_NPC_HISTORY = "db_npc_history"
    MANUSCRIPT_DB = "manuscript_db"  # [Phase2-L2]
    STATIC = "static"  # [TF-55b] query 문자열 자체를 결과로 반환
    DB_NPC_RELATIONSHIP = "db_npc_relationship"  # [TF-55b] npc_relationship_history 테이블 직접 조회


@dataclass(slots=True)
class RetrievalSlot:
    """Single retrieval instruction."""

    category: str
    query: str
    source: str = RetrievalSources.VEC_MEMORY
    priority: int = 2
    max_chars: int = 0


@dataclass(slots=True)
class RetrievalPlan:
    """Stage-level retrieval plan."""

    stage: str
    episode_num: int
    slots: list[RetrievalSlot] = field(default_factory=list)
    total_budget_chars: int = 0
    used_llm: bool = False


_STAGE_BUDGET_BUCKETS = {
    "stage2": "smart_retrieval.stage2_total_budget",
    "stage3": "smart_retrieval.stage3_total_budget",
    "stage4": "context.mandatory_context_max",
    "director": "smart_retrieval.director_total_budget",
}


def _clean_str_list(values: Any) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def normalize_context_source_counts(source_counts: dict | None) -> dict[str, int]:
    if not isinstance(source_counts, dict):
        return {}

    normalized: dict[str, int] = {}
    for key, value in source_counts.items():
        name = str(key or "").strip()
        if not name:
            continue
        try:
            count = int(value or 0)
        except (TypeError, ValueError):
            continue
        if count > 0:
            normalized[name] = count
    return normalized


def build_context_budget_ledger(
    *,
    stage: str,
    configured_cap: int = 0,
    effective_cap: int = 0,
    consumed_chars: int = 0,
    dropped_chars: int = 0,
    overflow_chars: int = 0,
    fallback_cap: int = 0,
    budget_bucket: str | None = None,
    headroom_chars: int = 0,
) -> dict[str, Any]:
    configured_cap = max(0, int(configured_cap or 0))
    fallback_cap = max(0, int(fallback_cap or 0))
    effective_cap = max(0, int(effective_cap or configured_cap or fallback_cap or 0))
    consumed_chars = max(0, int(consumed_chars or 0))
    dropped_chars = max(0, int(dropped_chars or 0))
    overflow_chars = max(0, int(overflow_chars or 0))
    headroom_chars = max(0, int(headroom_chars or 0))
    return {
        "budget_bucket": str(budget_bucket or _STAGE_BUDGET_BUCKETS.get(stage, stage) or stage),
        "configured_cap": configured_cap,
        "fallback_cap": fallback_cap,
        "effective_cap": effective_cap,
        "consumed_chars": consumed_chars,
        "dropped_chars": dropped_chars,
        "overflow_chars": overflow_chars,
        "headroom_chars": headroom_chars,
        "trim_applied": bool(dropped_chars or overflow_chars),
    }


def build_context_provenance_ledger(
    *,
    stage: str,
    retrieval_plan=None,
    work_focus: dict[str, Any] | None = None,
    source_counts: dict | None = None,
    coverage_warnings: list[str] | None = None,
    work_slot_summary_present: bool = False,
    work_slot_summary_included: bool = False,
    relation_slice_included: bool = False,
    stage_context_chars: int = 0,
    budget_bucket: str | None = None,
) -> dict[str, Any]:
    normalized_source_counts = normalize_context_source_counts(source_counts)
    coverage_warnings = _clean_str_list(coverage_warnings)

    slot_categories: list[str] = []
    for slot in getattr(retrieval_plan, "slots", []) or []:
        category = str(getattr(slot, "category", "") or "").strip()
        if category and category not in slot_categories:
            slot_categories.append(category)

    source_item = [f"slot:{category}" for category in slot_categories]
    if not source_item and normalized_source_counts:
        source_item = [f"source:{key}" for key in sorted(normalized_source_counts.keys())]
    if not source_item:
        source_item = ["legacy_context"]

    stage_present = list(source_item)
    if isinstance(work_focus, dict) and work_focus:
        stage_present.append("work_focus")
    if work_slot_summary_present:
        stage_present.append("work_slot_summary")
    if normalized_source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0:
        stage_present.append("relation_slice")
    stage_present = _clean_str_list(stage_present)

    stage_survived = []
    if work_slot_summary_included:
        stage_survived.append("work_slot_summary")
    if relation_slice_included:
        stage_survived.append("relation_slice")
    if stage_context_chars > 0:
        stage_survived.extend(source_item)
    stage_survived = _clean_str_list(stage_survived)

    return {
        "source_pack": str(stage or "unknown"),
        "source_item": source_item,
        "stage_present": stage_present,
        "stage_survived": stage_survived,
        "dropped_at": str(stage or "unknown") if coverage_warnings else "",
        "drop_reason": coverage_warnings,
        "budget_bucket": str(budget_bucket or _STAGE_BUDGET_BUCKETS.get(stage, stage) or stage),
        "context_chars": max(0, int(stage_context_chars or 0)),
        "source_counts": normalized_source_counts,
    }


def build_context_observation(
    *,
    stage: str,
    work_focus: dict[str, Any] | None = None,
    retrieval_plan=None,
    source_counts: dict | None = None,
    coverage_warnings: list[str] | None = None,
    advisor_path_used: bool = False,
    work_slot_summary_present: bool = False,
    work_slot_summary_included: bool = False,
    relation_slice_included: bool = False,
    vector_context_chars: int = 0,
    mandatory_context_chars: int = 0,
    protected_summary_survived: bool = False,
    trimmed_work_slot_summary: bool = False,
    budget_ledger: dict | None = None,
) -> dict[str, Any]:
    work_focus = work_focus if isinstance(work_focus, dict) else {}
    normalized_source_counts = normalize_context_source_counts(source_counts)
    coverage_warnings = _clean_str_list(coverage_warnings)
    provenance_ledger = build_context_provenance_ledger(
        stage=stage,
        retrieval_plan=retrieval_plan,
        work_focus=work_focus,
        source_counts=normalized_source_counts,
        coverage_warnings=coverage_warnings,
        work_slot_summary_present=work_slot_summary_present,
        work_slot_summary_included=work_slot_summary_included,
        relation_slice_included=relation_slice_included,
        stage_context_chars=max(int(vector_context_chars or 0), int(mandatory_context_chars or 0)),
        budget_bucket=(budget_ledger or {}).get("budget_bucket"),
    )
    budget_ledger = budget_ledger if isinstance(budget_ledger, dict) else {}

    return {
        "work_focus_present": bool(work_focus),
        "tracking_slots_count": len(work_focus.get("tracking_slots") or []),
        "scene_engines_count": len(work_focus.get("mandatory_scene_engines") or []),
        "registry_profiles_count": len(work_focus.get("registry_profiles") or []),
        "planned_slots_count": len(getattr(retrieval_plan, "slots", []) or []) if retrieval_plan else 0,
        "advisor_path_used": bool(advisor_path_used),
        "work_slot_summary_included": bool(work_slot_summary_included),
        "relation_slice_included": bool(relation_slice_included),
        "source_counts": normalized_source_counts,
        "coverage_warnings": coverage_warnings,
        "vector_context_chars": max(0, int(vector_context_chars or 0)),
        "mandatory_context_chars": max(0, int(mandatory_context_chars or 0)),
        "protected_summary_survived": bool(protected_summary_survived),
        "trimmed_work_slot_summary": bool(trimmed_work_slot_summary),
        "provenance_ledger": provenance_ledger,
        "budget_ledger": budget_ledger,
    }


class ContextBudgetTracker:
    """Tracks section-level usage and suggests trim targets when over budget."""

    def __init__(self, total_budget_chars: int):
        self.total_budget_chars = max(0, int(total_budget_chars))
        self._sections: dict[str, int] = {}

    def register_section(self, name: str, content: str) -> None:
        self._sections[name] = len(content or "")

    def get_usage_report(self) -> dict[str, Any]:
        used = sum(self._sections.values())
        remaining = max(0, self.total_budget_chars - used)
        pct = round((used / self.total_budget_chars) * 100, 2) if self.total_budget_chars else 0.0
        return {
            "total_budget_chars": self.total_budget_chars,
            "used_chars": used,
            "remaining_chars": remaining,
            "usage_pct": pct,
            "sections": dict(self._sections),
        }

    def get_compression_targets(self) -> list[str]:
        report = self.get_usage_report()
        overflow = max(0, report["used_chars"] - self.total_budget_chars)
        if overflow <= 0:
            return []

        recovered = 0
        targets: list[str] = []
        for name, size in sorted(self._sections.items(), key=lambda item: item[1], reverse=True):
            targets.append(name)
            recovered += size
            if recovered >= overflow:
                break
        return targets


class ContextAdvisor:
    """Builds heuristic retrieval plans and conditionally enriches with LLM hints."""

    _STAGE_BUDGET_KEYS = {
        "stage2": "smart_retrieval.stage2_total_budget",
        "stage3": "smart_retrieval.stage3_total_budget",
        "stage4": "smart_retrieval.stage4_total_budget",
        "director": "smart_retrieval.director_total_budget",
    }

    _STAGE_ENABLED_KEYS = {
        "stage2": "smart_retrieval.stage2_enabled",
        "stage3": "smart_retrieval.stage3_enabled",
        "stage4": "smart_retrieval.stage4_enabled",
        "director": "smart_retrieval.director_enabled",
    }

    _STAGE_QUERY_CAPS = {
        "stage2": 5,
        "stage3": 6,
        "stage4": 8,
        "director": 5,
    }

    # [INF-I7] 장르 힌트 YAML 외부화 — 모듈 로드 시 1회 로딩
    _GENRE_HINTS = _load_genre_hints()
    _WORK_FOCUS_RELATION_TOKENS = {
        "ally",
        "bond",
        "family",
        "friend",
        "mentor",
        "rival",
        "relationship",
        "relation",
        "trust",
        "소꿉친구",
        "관계",
        "관계선",
        "동맹",
        "동료",
        "라이벌",
        "멘토",
        "믿음",
        "사부",
        "사제",
        "숙적",
        "우군",
        "은인",
        "인맥",
        "죽마고우",
        "조력자",
        "친구",
        "파트너",
        "후배 라인",
    }
    _WORK_FOCUS_NPC_TOKENS = {
        "actor",
        "ally",
        "apprentice",
        "artist",
        "associate",
        "cast",
        "casting",
        "character",
        "crew",
        "disciple",
        "family",
        "fandom",
        "friend",
        "junior",
        "line",
        "manager",
        "member",
        "mentor",
        "npc",
        "partner",
        "people",
        "person",
        "rival",
        "student",
        "talent",
        "team",
        "trainee",
        "후배",
        "동료",
        "라이벌",
        "매니저",
        "멘토",
        "문파",
        "배우",
        "사람",
        "소꿉친구",
        "승무원",
        "연습생",
        "인맥",
        "인물",
        "인재",
        "제자",
        "조력자",
        "팀",
        "팬덤",
        "핵심 배우",
    }

    def __init__(
        self,
        *,
        llm_enricher: Callable[..., Any] | None = None,
    ) -> None:
        self.llm_enricher = llm_enricher
        self.enabled = bool(_threshold("smart_retrieval.enabled", False))
        self.max_queries_per_plan = int(_threshold("smart_retrieval.max_queries_per_plan", 8))

    @staticmethod
    def _fit_slot_text(value: object, max_chars: int, head_ratio: float = 0.55) -> str:
        text = str(value or "").strip()
        if len(text) <= max_chars:
            return text
        marker = "...(중간 생략)..."
        remaining = max_chars - len(marker)
        if remaining <= 0:
            return text[:max_chars]
        min_tail_chars = min(16, max(1, remaining - 1))
        head_chars = max(1, min(int(max_chars * head_ratio), remaining - min_tail_chars))
        tail_chars = max(1, remaining - head_chars)
        if head_chars + tail_chars > len(text):
            return text
        return f"{text[:head_chars]}{marker}{text[-tail_chars:]}"

    def plan_stage2_retrieval(
        self,
        arc_data: dict,
        current_ep: int,
        npc_roster: list[Any] | None = None,
        work_focus: dict[str, Any] | None = None,
    ) -> RetrievalPlan:
        context_data = {
            "arc_data": arc_data or {},
            "npc_roster": npc_roster or [],
            "current_ep": current_ep,
            "work_focus": work_focus or {},
        }
        return self._build_plan("stage2", current_ep, context_data)

    def plan_stage3_retrieval(
        self,
        arc_data: dict,
        prev_blueprints: list[dict] | None = None,
        current_ep: int = 1,
        npc_roster: list[Any] | None = None,
        genre: str = "",
        work_focus: dict[str, Any] | None = None,
    ) -> RetrievalPlan:
        """[S3-I1] Stage 3 Blueprint 생성 시 과거 유사 Blueprint를 SC로 검색."""
        context_data = {
            "arc_data": arc_data or {},
            "prev_blueprints": prev_blueprints or [],
            "npc_roster": npc_roster or [],
            "genre": genre or "",
            "current_ep": current_ep,
            "work_focus": work_focus or {},
        }
        return self._build_plan("stage3", current_ep, context_data)

    def plan_stage4_retrieval(
        self,
        arc_data: dict,
        blueprint: dict,
        prev_ending: str,
        current_ep: int,
        npc_roster: list[Any] | None = None,
        genre: str = "",
        work_focus: dict[str, Any] | None = None,
        *,
        is_arc_boundary: bool = False,
        is_reject_retry: bool = False,
    ) -> RetrievalPlan:
        context_data = {
            "arc_data": arc_data or {},
            "blueprint": blueprint or {},
            "prev_ending": prev_ending or "",
            "npc_roster": npc_roster or [],
            "genre": genre or "",
            "current_ep": current_ep,
            "work_focus": work_focus or {},
            "is_arc_boundary": bool(is_arc_boundary),
            "is_reject_retry": bool(is_reject_retry),
        }
        return self._build_plan("stage4", current_ep, context_data)

    def plan_director_retrieval(
        self,
        manuscript: str,
        blueprint: dict,
        current_ep: int,
        npc_roster: list[Any] | None = None,
        *,
        is_arc_boundary: bool = False,
        is_reject_retry: bool = False,
        low_confidence: bool = False,
        work_focus: dict[str, Any] | None = None,
    ) -> RetrievalPlan:
        context_data = {
            "manuscript": manuscript or "",
            "blueprint": blueprint or {},
            "npc_roster": npc_roster or [],
            "current_ep": current_ep,
            "is_arc_boundary": bool(is_arc_boundary),
            "is_reject_retry": bool(is_reject_retry),
            "low_confidence": bool(low_confidence),
            "work_focus": work_focus or {},
        }
        return self._build_plan("director", current_ep, context_data)

    def _build_plan(self, stage: str, episode_num: int, context_data: dict[str, Any]) -> RetrievalPlan:
        total_budget = self._get_stage_budget(stage)
        if not self.enabled or not self._is_stage_enabled(stage):
            return RetrievalPlan(stage=stage, episode_num=episode_num, total_budget_chars=total_budget)

        plan = self._heuristic_plan(stage, context_data)
        plan.episode_num = episode_num
        plan.total_budget_chars = total_budget

        if self._should_use_llm(stage, context_data):
            plan = self._llm_enrich_plan(plan, context_data)
        logging.info(
            f"[SC] {stage} plan: {len(plan.slots)} slots, budget={plan.total_budget_chars}, llm={plan.used_llm}"
        )
        return plan

    def _heuristic_plan(self, stage: str, context_data: dict[str, Any]) -> RetrievalPlan:
        if stage == "stage2":
            slots = self._build_stage2_slots(context_data)
        elif stage == "stage3":
            slots = self._build_stage3_slots(context_data)
        elif stage == "stage4":
            slots = self._build_stage4_slots(context_data)
        elif stage == "director":
            slots = self._build_director_slots(context_data)
        else:
            slots = []

        slots = self._dedupe_slots(slots)
        slots = slots[: self._stage_query_cap(stage)]
        self._assign_slot_budgets(stage, slots)
        return RetrievalPlan(stage=stage, episode_num=int(context_data.get("current_ep", 0)), slots=slots)

    def _llm_enrich_plan(self, base_plan: RetrievalPlan, context_data: dict[str, Any]) -> RetrievalPlan:
        if not self.llm_enricher:
            return base_plan

        try:
            raw = self.llm_enricher(stage=base_plan.stage, context=context_data, plan=base_plan)
            payload = self._safe_json_loads(raw) if isinstance(raw, str) else raw
            if not isinstance(payload, list):
                return base_plan

            extra_slots: list[RetrievalSlot] = []
            for item in payload[:5]:
                if not isinstance(item, dict):
                    continue
                query = str(item.get("query", "")).strip()
                if not query:
                    continue
                priority = self._safe_priority(item.get("priority", 2))
                extra_slots.append(
                    RetrievalSlot(
                        category=str(item.get("category", "llm_suggestion")),
                        query=query,
                        source=RetrievalSources.VEC_MEMORY,
                        priority=priority,
                    )
                )

            if not extra_slots:
                return base_plan

            merged_slots = self._dedupe_slots(base_plan.slots + extra_slots)
            merged_slots = merged_slots[: self._stage_query_cap(base_plan.stage)]
            self._assign_slot_budgets(base_plan.stage, merged_slots)
            return RetrievalPlan(
                stage=base_plan.stage,
                episode_num=base_plan.episode_num,
                slots=merged_slots,
                total_budget_chars=base_plan.total_budget_chars,
                used_llm=True,
            )
        except Exception as exc:
            logging.warning("[SilentPass:SC:LLMEnrich] LLM enrichment 실패, 휴리스틱 폴백: %s", exc)
            return base_plan

    def _should_use_llm(self, stage: str, context_data: dict[str, Any]) -> bool:
        npc_count = len(self._normalize_npc_names(context_data.get("npc_roster", [])))
        if context_data.get("is_arc_boundary"):
            logging.debug(f"[SC] LLM enrichment trigger: arc_boundary ({stage})")
            return True
        if context_data.get("is_reject_retry"):
            logging.debug(f"[SC] LLM enrichment trigger: reject_retry ({stage})")
            return True
        if npc_count >= 5:
            logging.debug(f"[SC] LLM enrichment trigger: npc_count={npc_count} ({stage})")
            return True
        if stage == "director" and context_data.get("low_confidence"):
            logging.debug(f"[SC] LLM enrichment trigger: low_confidence ({stage})")
            return True
        return False

    def _build_stage2_slots(self, context_data: dict[str, Any]) -> list[RetrievalSlot]:
        arc_data = context_data.get("arc_data", {})
        npc_names = self._normalize_npc_names(context_data.get("npc_roster", []))
        slots: list[RetrievalSlot] = self._build_work_focus_slots(
            context_data.get("work_focus", {}),
            stage="stage2",
        )

        block_theme = str(arc_data.get("block_theme", "")).strip()
        tactical = str(arc_data.get("tactical_doc", "") or arc_data.get("arc_tactical", "")).strip()
        plot_suspension = arc_data.get("plot_suspension", []) or []

        if block_theme:
            slots.append(RetrievalSlot("block_theme", f"블록 테마 핵심: {block_theme}", priority=1))
            slots.append(
                RetrievalSlot(
                    "similar_theme",
                    f"유사 아크 테마/갈등/해결: {block_theme}",
                    priority=2,
                )
            )
        if npc_names:
            slots.append(
                RetrievalSlot(
                    "npc_recent",
                    f"등장 NPC 최근 행적/상태 변화: {' '.join(npc_names[:5])}",
                    source=RetrievalSources.DB_NPC_HISTORY,
                    priority=2,
                )
            )
        if plot_suspension:
            joined = ", ".join(str(item)[:30] for item in plot_suspension[:3])
            slots.append(RetrievalSlot("unresolved_plot", f"미해결 복선/보류 플롯: {joined}", priority=1))
        if tactical:
            slots.append(
                RetrievalSlot(
                    "arc_tactical",
                    f"아크 전술 키워드: {self._fit_slot_text(tactical, 260)}",
                    priority=2,
                )
            )

        return slots

    def _build_stage3_slots(self, context_data: dict[str, Any]) -> list[RetrievalSlot]:
        """[S3-I1] Stage 3 Blueprint SC 슬롯: 과거 유사 Blueprint + NPC + 전술 연속성."""
        arc_data = context_data.get("arc_data", {})
        npc_names = self._normalize_npc_names(context_data.get("npc_roster", []))
        prev_blueprints = context_data.get("prev_blueprints", [])
        genre = str(context_data.get("genre", "")).strip().lower()

        slots: list[RetrievalSlot] = self._build_work_focus_slots(
            context_data.get("work_focus", {}),
            stage="stage3",
        )

        # 1. Arc 전술 키워드 → 과거 유사 블루프린트 검색
        tactical = str(arc_data.get("tactical_doc", "") or arc_data.get("arc_tactical", "")).strip()
        if tactical:
            slots.append(
                RetrievalSlot(
                    "similar_blueprint",
                    f"유사 블루프린트/아크 전술 키워드: {self._fit_slot_text(tactical, 300)}",
                    priority=1,
                )
            )

        # 2. NPC 최근 행적 (Blueprint 단계에서도 NPC 연속성 필요)
        if npc_names:
            slots.append(
                RetrievalSlot(
                    "npc_history",
                    f"등장 NPC 과거 행적/관계/상태: {' '.join(npc_names[:6])}",
                    source=RetrievalSources.DB_NPC_HISTORY,
                    priority=1,
                )
            )

        # 3. 직전 Blueprint의 ending_hook → 연결 포인트 검색
        if prev_blueprints:
            last_bp = prev_blueprints[-1] if prev_blueprints else {}
            ending_hook = str(last_bp.get("ending_hook", "") or last_bp.get("cliffhanger", "")).strip()
            if ending_hook:
                slots.append(
                    RetrievalSlot(
                        "continuity_hook",
                        f"직전 화 연결 포인트: {self._fit_slot_text(ending_hook, 200)}",
                        priority=1,
                    )
                )

        # 4. 미해결 플롯 검색
        plot_suspension = arc_data.get("plot_suspension", []) or []
        if plot_suspension:
            joined = ", ".join(str(item)[:30] for item in plot_suspension[:3])
            slots.append(RetrievalSlot("unresolved_plot", f"미해결 복선/보류 플롯: {joined}", priority=2))

        # 5. 장르별 컨텍스트
        if genre in self._GENRE_HINTS:
            for idx, phrase in enumerate(self._GENRE_HINTS[genre][:1], start=1):
                slots.append(RetrievalSlot(f"genre_context_{idx}", f"장르 맥락 키워드: {phrase}", priority=3))

        return slots

    @classmethod
    def _infer_work_focus_source(cls, *values: Any) -> str:
        haystack = " ".join(str(value or "").lower() for value in values if value)
        if not haystack:
            return RetrievalSources.VEC_MEMORY
        if any(token in haystack for token in cls._WORK_FOCUS_RELATION_TOKENS):
            return RetrievalSources.DB_NPC_RELATIONSHIP
        if any(token in haystack for token in cls._WORK_FOCUS_NPC_TOKENS):
            return RetrievalSources.DB_NPC_HISTORY
        return RetrievalSources.VEC_MEMORY

    def _build_work_focus_slots(self, work_focus: dict[str, Any], *, stage: str) -> list[RetrievalSlot]:
        if not isinstance(work_focus, dict) or not work_focus:
            return []

        slots: list[RetrievalSlot] = []
        tracking_slots = [str(item).strip() for item in (work_focus.get("tracking_slots") or []) if str(item).strip()]
        scene_engines = [
            str(item).strip() for item in (work_focus.get("mandatory_scene_engines") or []) if str(item).strip()
        ]
        registry_profiles = [item for item in (work_focus.get("registry_profiles") or []) if isinstance(item, dict)]

        for idx, item in enumerate(tracking_slots[:3], start=1):
            source = self._infer_work_focus_source(item)
            slots.append(
                RetrievalSlot(
                    category=f"work_tracking_slot_{idx}",
                    query=f"{stage} 작품 tracking slot 핵심 상태/최근 변화: {item}",
                    source=source,
                    priority=1,
                )
            )

        for idx, item in enumerate(scene_engines[:2], start=1):
            source = self._infer_work_focus_source(item)
            slots.append(
                RetrievalSlot(
                    category=f"work_scene_engine_{idx}",
                    query=f"{stage} mandatory scene engine 관련 근거/최근 장면: {item}",
                    source=source,
                    priority=1,
                )
            )

        for idx, profile in enumerate(registry_profiles[:2], start=1):
            name = str(profile.get("name", "") or "").strip()
            purpose = str(profile.get("purpose", "") or "").strip()
            required_fields = [
                str(item).strip() for item in (profile.get("required_fields") or []) if str(item).strip()
            ]
            if not name:
                continue
            source = self._infer_work_focus_source(name, purpose, " ".join(required_fields))
            query_parts = [name]
            if purpose:
                query_parts.append(purpose)
            if required_fields:
                query_parts.append(f"required_fields={', '.join(required_fields[:5])}")
            slots.append(
                RetrievalSlot(
                    category=f"work_registry_{idx}",
                    query=f"{stage} registry profile 상태/근거: {' | '.join(query_parts)}",
                    source=source,
                    priority=2,
                )
            )

        return slots

    def _build_stage4_slots(self, context_data: dict[str, Any]) -> list[RetrievalSlot]:
        arc_data = context_data.get("arc_data", {})
        blueprint = context_data.get("blueprint", {})
        prev_ending = str(context_data.get("prev_ending", "")).strip()
        genre = str(context_data.get("genre", "")).strip().lower()

        state_changes = arc_data.get("state_changes", {}) if isinstance(arc_data, dict) else {}
        npc_names = self._normalize_npc_names(context_data.get("npc_roster", []))
        npc_names.extend(self._extract_npc_names_from_state_changes(state_changes))

        slots: list[RetrievalSlot] = self._build_work_focus_slots(
            context_data.get("work_focus", {}),
            stage="stage4",
        )
        if prev_ending:
            slots.append(
                RetrievalSlot(
                    "prev_ending",
                    f"직전 결말 연결 포인트: {self._fit_slot_text(prev_ending, 260)}",
                    priority=1,
                )
            )
        if npc_names:
            slots.append(
                RetrievalSlot(
                    "npc_history",
                    f"등장 NPC 과거 행적/관계/상태: {' '.join(sorted(set(npc_names))[:6])}",
                    source=RetrievalSources.DB_NPC_HISTORY,
                    priority=1,
                )
            )

        tactical = str(arc_data.get("tactical_doc", "") or arc_data.get("arc_tactical", "")).strip()
        if tactical:
            slots.append(
                RetrievalSlot(
                    "arc_tactical",
                    f"아크 전술 연속성: {self._fit_slot_text(tactical, 320)}",
                    source=RetrievalSources.STATIC,
                    priority=2,
                )
            )

        scene_query = self._build_scene_query(blueprint)
        if scene_query:
            slots.append(RetrievalSlot("scene_context", scene_query, source=RetrievalSources.STATIC, priority=2))

        plot_suspension = arc_data.get("plot_suspension", []) or []
        if plot_suspension:
            slots.append(
                RetrievalSlot(
                    "unresolved_plot",
                    f"미해결 복선/회수 필요 요소: {', '.join(str(item)[:30] for item in plot_suspension[:3])}",
                    priority=1,
                )
            )

        rel_query = self._build_relationship_query(state_changes)
        if rel_query:
            slots.append(
                RetrievalSlot(
                    "relationship_history",
                    rel_query,
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=2,
                )
            )

        semantic_query = self._build_semantic_carryover_query(arc_data)
        if semantic_query:
            slots.append(
                RetrievalSlot(
                    "arc_semantic_carryover",
                    semantic_query,
                    source=RetrievalSources.STATIC,
                    priority=2,
                )
            )

        if genre in self._GENRE_HINTS:
            for idx, phrase in enumerate(self._GENRE_HINTS[genre][:2], start=1):
                slots.append(
                    RetrievalSlot(
                        f"genre_context_{idx}",
                        f"장르 맥락 키워드: {phrase}",
                        source=RetrievalSources.STATIC,
                        priority=3,
                    )
                )

        # Slot: Manuscript excerpt (실제 원고 발췌, 연속성 참조용)
        # [Phase2-L2] 버그수정: "ep_num" 키 없음 → "current_ep" 키 사용
        ep_num = context_data.get("current_ep", 0)
        if ep_num and ep_num > 3:
            slots.append(
                RetrievalSlot(
                    "manuscript_excerpt",
                    f"ep:{ep_num - 3}~{ep_num - 1} 원고 발췌 (연속성 참조용)",
                    source="manuscript_db",
                    priority=1,
                )
            )

        return slots

    def _build_director_slots(self, context_data: dict[str, Any]) -> list[RetrievalSlot]:
        manuscript = str(context_data.get("manuscript", ""))
        blueprint = context_data.get("blueprint", {})
        npc_names = self._normalize_npc_names(context_data.get("npc_roster", []))
        mentioned_npcs = [name for name in npc_names if name and name in manuscript]

        slots: list[RetrievalSlot] = self._build_work_focus_slots(
            context_data.get("work_focus", {}),
            stage="director",
        )
        if mentioned_npcs:
            slots.append(
                RetrievalSlot(
                    "npc_consistency",
                    f"원고 등장 NPC 연속성 검증: {' '.join(mentioned_npcs[:6])}",
                    source=RetrievalSources.DB_NPC_HISTORY,
                    priority=1,
                )
            )

        event_anchor = str(blueprint.get("core_event", "") or blueprint.get("story_goal", "")).strip()
        if event_anchor:
            slots.append(
                RetrievalSlot(
                    "event_claim",
                    f"원고 사건 주장 검증: {self._fit_slot_text(event_anchor, 240)}",
                    priority=1,
                )
            )

        rel_query = self._build_relationship_query(blueprint.get("state_changes", {}))
        if rel_query:
            slots.append(
                RetrievalSlot(
                    "relationship_consistency",
                    rel_query,
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=2,
                )
            )

        place = str(blueprint.get("end_location", "") or blueprint.get("start_location", "")).strip()
        if place:
            slots.append(
                RetrievalSlot(
                    "location_item_consistency",
                    f"위치/소지품 연속성 검증: {self._fit_slot_text(place, 120)}",
                    priority=2,
                )
            )

        if manuscript:
            slots.append(
                RetrievalSlot(
                    "blueprint_alignment",
                    f"원고-블루프린트 정합 검토: {self._fit_slot_text(manuscript, 120)}",
                    priority=3,
                )
            )

        return slots

    @staticmethod
    def _normalize_npc_names(npc_roster: list[Any]) -> list[str]:
        names: list[str] = []
        for item in npc_roster or []:
            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict):
                name = str(item.get("name", "") or item.get("npc", "") or item.get("target", "")).strip()
            else:
                name = str(item).strip()
            if name:
                names.append(name)
        return names

    @staticmethod
    def _extract_npc_names_from_state_changes(state_changes: Any) -> list[str]:
        if not isinstance(state_changes, dict):
            return []
        names: list[str] = []
        for key in ("npc_deaths", "relationship_changes", "npc_injuries"):
            for item in state_changes.get(key, []) or []:
                if isinstance(item, dict):
                    name = str(item.get("name", "") or item.get("npc", "") or item.get("target", "")).strip()
                else:
                    name = str(item).strip()
                if name:
                    names.append(name)
        return names

    @staticmethod
    def _build_scene_query(blueprint: Any) -> str:
        if not isinstance(blueprint, dict):
            return ""
        scene_breakdown = blueprint.get("scene_breakdown", [])
        if isinstance(scene_breakdown, dict):
            scene_breakdown = list(scene_breakdown.values())
        if not isinstance(scene_breakdown, list) or not scene_breakdown:
            return ""
        parts: list[str] = []
        for idx, scene in enumerate(scene_breakdown[:3], start=1):
            if isinstance(scene, dict):
                for key in ("goal", "objective", "summary", "scene_goal"):
                    value = str(scene.get(key, "")).strip()
                    if value:
                        parts.append(f"장면{idx}: {ContextAdvisor._fit_slot_text(value, 52)}")
                        break
            elif isinstance(scene, str):
                parts.append(f"장면{idx}: {ContextAdvisor._fit_slot_text(scene, 52)}")
        return ContextAdvisor._fit_slot_text(" | ".join(parts), 260)

    @staticmethod
    def _build_relationship_query(state_changes: Any) -> str:
        rel_changes = []
        if isinstance(state_changes, dict):
            rel_changes = state_changes.get("relationship_changes", []) or []
        if not isinstance(rel_changes, list):
            return ""
        pairs: list[str] = []
        for item in rel_changes[:4]:
            if isinstance(item, dict):
                who = str(item.get("npc", "") or item.get("target", "")).strip()
                delta = str(item.get("change", "")).strip()
                if who:
                    pair = f"{who}:{delta}" if delta else who
                    pairs.append(ContextAdvisor._fit_slot_text(pair, 42))
            elif isinstance(item, str):
                pairs.append(ContextAdvisor._fit_slot_text(item.strip(), 42))
        return f"관계 변화 이력: {', '.join(pairs)}" if pairs else ""

    @staticmethod
    def _build_semantic_carryover_query(arc_data: Any) -> str:
        if not isinstance(arc_data, dict):
            return ""
        payload = arc_data.get("semantic_carryover", {})
        if not isinstance(payload, dict) or not payload:
            return ""

        lines: list[str] = []
        for entry in payload.get("relationship_rationale", []) or []:
            if not isinstance(entry, dict):
                continue
            npc = str(entry.get("npc", "") or entry.get("target", "") or "").strip()[:40]
            cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()[:120]
            if cue:
                prefix = f"relationship {npc}: " if npc else "relationship: "
                lines.append(prefix + cue)

        growth = str(payload.get("growth_justification", "") or "").strip()[:140]
        if growth:
            lines.append(f"growth_justification: {growth}")

        for anchor in (payload.get("foreshadow_anchors", []) or [])[:3]:
            text = str(anchor or "").strip()[:120]
            if text:
                lines.append(f"foreshadow: {text}")

        checkpoints = [str(item or "").strip()[:80] for item in (payload.get("continuity_checkpoints", []) or [])[:3]]
        checkpoints = [item for item in checkpoints if item]
        if checkpoints:
            lines.append(f"continuity: {'; '.join(checkpoints)}")

        if not lines:
            return ""
        return "[Arc Semantic Carryover]\n" + "\n".join(lines[:8])

    def _assign_slot_budgets(self, stage: str, slots: list[RetrievalSlot]) -> None:
        total_budget = self._get_stage_budget(stage)
        if not slots or total_budget <= 0:
            return
        weight_map = {1: 3, 2: 2, 3: 1}
        weights = [weight_map.get(slot.priority, 1) for slot in slots]
        weight_sum = sum(weights) or 1
        _min_chars = int(_threshold("smart_retrieval.slot_max_chars_default", 1500))  # [P3-04]
        for slot, weight in zip(slots, weights, strict=False):
            slot.max_chars = max(_min_chars, int(total_budget * (weight / weight_sum)))

    @staticmethod
    def _safe_priority(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 2
        return 1 if parsed <= 1 else (3 if parsed >= 3 else 2)

    @staticmethod
    def _safe_json_loads(raw: str) -> Any:
        try:
            return json.loads(raw)
        except Exception:
            return []

    @staticmethod
    def _dedupe_slots(slots: list[RetrievalSlot]) -> list[RetrievalSlot]:
        seen: set[tuple[str, str]] = set()
        deduped: list[RetrievalSlot] = []
        for slot in slots:
            query = slot.query.strip()
            if not query:
                continue
            key = (slot.category.strip().lower(), query.lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(slot)
        deduped.sort(key=lambda slot: slot.priority)
        return deduped

    def _is_stage_enabled(self, stage: str) -> bool:
        key = self._STAGE_ENABLED_KEYS.get(stage)
        return bool(_threshold(key, False)) if key else True

    def _get_stage_budget(self, stage: str) -> int:
        defaults = {"stage2": 20000, "stage3": 30000, "stage4": 50000, "director": 20000}
        key = self._STAGE_BUDGET_KEYS.get(stage)
        if not key:
            return defaults["stage2"]
        return int(_threshold(key, defaults[stage]))

    def _stage_query_cap(self, stage: str) -> int:
        stage_cap = self._STAGE_QUERY_CAPS.get(stage, self.max_queries_per_plan)
        return max(1, min(self.max_queries_per_plan, stage_cap))
