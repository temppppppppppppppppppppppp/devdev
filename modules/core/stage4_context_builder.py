"""
[B-1-2] Stage4 Context Builder — 에피소드 컨텍스트 수집 및 프롬프트 조립.

Navigation ToC (major sections):
  TypedDict payload definitions  — typed envelopes for inter-method data
  Stage4ContextBuilder class     — owner shell
    build_episode_context()      — top-level orchestrator entry point
    _build_retrieval_*           — retrieval plan and coverage assembly
    _build_prompt_*              — prompt injection assembly
    _build_auxiliary_*           — HUD, anti-trope, justification helpers
    _build_mandatory_context     — mandatory context seed assembly
    context_packets              — delegation to Stage4ContextPackets

Delegation chain:
  Stage4Orchestrator → Stage4InterviewRound → Stage4ContextBuilder
    → Stage4ContextPackets (modules/core/stage4_context_packets.py)
    → ChiefWriterContextPackets (modules/domain/agents/chief_writer_context_packets.py)
    → writer_prompt_builders (modules/core/writer_prompt_builders.py)
"""

import inspect
import json
import logging
import re
from typing import TYPE_CHECKING, Any, TypedDict

from modules.core.constants import Stage2Limits, smart_truncate
from modules.core.context_advisor import (
    RetrievalSources,
    build_context_budget_ledger,
    build_context_observation,
)
from modules.core.context_compression import ContextCompressor
from modules.core.genre_schema_builder import is_wuxia
from modules.core.non_wuxia_recovery_policy import normalize_chain_link_for_genre, normalize_genre_type
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.core.stage4_context_packets import Stage4ContextPackets
from modules.core.stage_cross_stage_contract import (
    resolve_cross_stage_constraint_summary,
    resolve_cross_stage_episode_mission_lines,
)
from modules.core.tactical_utils import extract_episode_tactical
from modules.core.writer_prompt_builders import (
    _check_hud_anomalies as _detect_hud_anomalies,
)
from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
)
from modules.validation.threshold_helper import _threshold

_STAGE4_NUMERIC_CARRYOVER_AUTHORITY_HEADER = "[Stage4 Numeric Carryover Authority]"
_CARRYOVER_BASELINE_SCOPE = "carryover_baseline"
_NUMERIC_CARRYOVER_KEY_MARKERS = (
    "capital",
    "totalassets",
    "wealth",
    "asset",
    "assets",
    "cash",
    "balance",
    "networth",
)


class WorkRetrievalFocusPayload(TypedDict, total=False):
    tracking_slots: list[str]
    mandatory_scene_engines: list[str]
    registry_profiles: list[dict[str, Any]]


class Stage4RetrievalContextPayload(TypedDict):
    retrieval_plan: Any
    sc_parts: list[str]
    tier1_parts: list[str]


class Stage4RetrievalCoveragePayload(TypedDict):
    mandatory_context: str
    coverage_warnings: list[str]
    source_counts: dict[str, int]
    tier2_parts: list[str]


class Stage4AuxiliarySectionsPayload(TypedDict):
    tier1_parts: list[str]
    tier2_parts: list[str]


class Stage4MandatoryContextSeedPayload(TypedDict):
    cp_entities: dict[str, Any]
    work_focus: WorkRetrievalFocusPayload
    tier0_parts: list[str]
    slot_summary: str


class Stage4PromptInjectionsPayload(TypedDict):
    anti_trope_prompt: str
    justification_prompt: str
    reflexion_prompt: str


class Stage4PromptBasesPayload(TypedDict):
    anti_trope_prompt: str
    justification_prompt: str


class Stage4MandatoryContextPayload(TypedDict):
    reference_anchor_prompt: str
    mandatory_context: str
    anti_trope_prompt: str
    justification_prompt: str
    reflexion_prompt: str


class Stage4EpisodeBasePayload(TypedDict):
    arc_pos: int
    total_ep_in_arc: int
    arc_tactical: str
    prev_text: str
    prev_ending: str
    prev_manuscripts_text: str
    episode_digest: str


class Stage4EpisodeStatePayload(TypedDict):
    hud_report: str
    current_inventory: list[Any]
    current_martial_arts: list[Any]
    cumulative_bible: dict[str, Any]
    dead_npcs: list[Any]
    item_acquisition_timeline: str
    chain_link_section: str
    world_state_summary: str
    recent_scene_keywords: list[dict[str, Any]]


if TYPE_CHECKING:
    from modules.core.context_advisor import RetrievalPlan


def _fit_context_text(text: str, *, max_chars: int) -> str:
    raw = str(text or "")
    if len(raw) <= max_chars:
        return raw
    if max_chars <= 1:
        return raw[:max_chars]
    if max_chars < 80:
        tail_chars = max(8, min(max_chars // 3, max_chars - 2))
        head_chars = max_chars - tail_chars - 1
        if head_chars <= 0:
            return raw[:max_chars]
        return raw[:head_chars] + "…" + raw[-tail_chars:]
    head_chars = max(0, min(int(max_chars * 0.55), max_chars - 80))
    return smart_truncate(raw, max_chars=max_chars, head_chars=head_chars)


def _build_canonical_facts_section(db, full_text: str) -> str:
    """Blueprint 본문과 겹치는 canonical_facts를 CP 섹션 문자열로 조립한다."""
    getter = getattr(db, "get_canonical_facts", None)
    if not callable(getter):
        return ""

    try:
        canonical_facts = getter(fact_type="numerical")
        if not isinstance(canonical_facts, list) or not canonical_facts:
            return ""

        cf_lines: list[str] = []
        for fact in canonical_facts[:10]:
            if not isinstance(fact, dict):
                continue
            fact_key = str(fact.get("fact_key", "") or "").strip()
            if not fact_key:
                continue
            if full_text and fact_key not in full_text:
                continue

            fact_value = fact.get("value", {})
            fact_conf = str(fact.get("confidence", "confirmed") or "confirmed")
            first_ep = fact.get("first_ep", "?")
            last_ep = fact.get("last_ep", "?")
            if isinstance(fact_value, dict):
                value = fact_value.get("value", "?")
                unit = str(fact_value.get("unit", "") or "").strip()
                unit_str = f" {unit}" if unit else ""
                cf_lines.append(f"  {fact_key}: {value}{unit_str} (ep{first_ep}~{last_ep}, {fact_conf})")
            else:
                cf_lines.append(f"  {fact_key}: {fact_value} (ep{first_ep}~{last_ep}, {fact_conf})")

        if not cf_lines:
            return ""
        return "• 정규 팩트 참조\n" + "\n".join(cf_lines[:8])
    except Exception as cf_err:
        logging.debug("[CP-7] canonical_facts 조회 실패 (비치명): %s", cf_err)
        return ""


class Stage4ContextBuilder:
    """[B-1-2] Stage4 컨텍스트 빌더 전담 모듈."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.context_packets = Stage4ContextPackets(
            self,
            fit_context_text=_fit_context_text,
            build_canonical_facts_section=_build_canonical_facts_section,
        )

    def _resolve_protagonist_name(self) -> str:
        try:
            if getattr(self.ctx, "get_protagonist_name", None):
                name = self.ctx.get_protagonist_name()
                if name:
                    return str(name).strip()
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] protagonist callback 실패 (비치명): %s", exc)

        try:
            ws = getattr(self.ctx, "world_state", None)
            if ws and hasattr(ws, "get_state_dict"):
                state = ws.get_state_dict()
                if isinstance(state, dict):
                    protagonist = state.get("protagonist", {})
                    name = str((protagonist or {}).get("name", "") or "").strip()
                    if name:
                        return name
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] world_state protagonist 조회 실패 (비치명): %s", exc)

        try:
            master_bible = getattr(self.ctx.current_project, "master_bible", None) or {}
            bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
            protagonist = bible_root.get("protagonist_config", {}) if isinstance(bible_root, dict) else {}
            return str((protagonist or {}).get("name", "") or "").strip()
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] bible protagonist 조회 실패 (비치명): %s", exc)
            return ""

    def _resolve_stage4_genre_type(self, explicit_genre_type: str = "") -> str:
        candidates: list[object] = [explicit_genre_type]
        selected_genre = getattr(self.ctx, "selected_genre", None)
        if isinstance(selected_genre, dict):
            candidates.extend([selected_genre.get("type"), selected_genre.get("name")])
        project_genre = getattr(getattr(self.ctx, "current_project", None), "genre", None)
        if isinstance(project_genre, dict):
            candidates.extend([project_genre.get("type"), project_genre.get("name")])
        for candidate in candidates:
            normalized = normalize_genre_type(candidate)
            if normalized:
                return normalized
        return "wuxia"

    @staticmethod
    def _render_chain_link_items(value: object) -> str:
        if isinstance(value, list):
            items = [str(item or "").strip() for item in value if str(item or "").strip()]
            return ", ".join(items)
        return str(value or "").strip()

    @staticmethod
    def _extract_npc_tokens(query: str) -> list[str]:
        """Extract candidate NPC tokens from retrieval query text."""
        if not query:
            return []

        stopwords = {
            "npc",
            "history",
            "context",
            "consistency",
            "query",
            "past",
            "state",
            "change",
            "relation",
            "event",
            "continuity",
            "appear",
            "verify",
            # [TF7-P1-02] 한국어 일반어 — NPC 코어 슬롯 오점유 방지
            "등장",
            "과거",
            "행적",
            "관계",
            "상태",
            "내용",
            "정보",
            "히스토리",
            "배경",
            "이야기",
            "설명",
            "기록",
            "요약",
            "분석",
            "추적",
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
    def _collect_npc_roster(arc_data: dict, blueprint: dict | None = None) -> list[str]:
        """Collect NPC candidates from arc state_changes and blueprint hints."""
        names: list[str] = []
        state_changes = (arc_data or {}).get("state_changes", {}) if isinstance(arc_data, dict) else {}

        for field in (
            "npc_deaths",
            "relationship_changes",
            "npc_injuries",
            "npc_movements",
            "npc_attribute_changes",
            "npc_personality_changes",
            "companion_changes",
            "npc_introductions",
        ):
            for entry in state_changes.get(field) or []:
                if isinstance(entry, dict):
                    candidates = [
                        entry.get("name"),
                        entry.get("npc"),
                        entry.get("source"),
                        entry.get("target"),
                        entry.get("npc_name"),
                    ]
                    for cand in candidates:
                        text = str(cand or "").strip()
                        if text and text not in names:
                            names.append(text)
                elif isinstance(entry, str):
                    text = entry.strip()
                    if text and text not in names:
                        names.append(text)

        bp = blueprint or {}
        scene_blocks = bp.get("scene_breakdown") or bp.get("scenes") or []
        if isinstance(scene_blocks, dict):
            scene_blocks = list(scene_blocks.values())
        if isinstance(scene_blocks, list):
            for scene in scene_blocks:
                if not isinstance(scene, dict):
                    continue
                for key in ("npcs", "characters", "participants"):
                    raw = scene.get(key)
                    if isinstance(raw, list):
                        for item in raw:
                            text = str(item or "").strip()
                            if text and text not in names:
                                names.append(text)
                    elif isinstance(raw, str):
                        for item in re.split(r"[,\n/|]+", raw):
                            text = item.strip()
                            if text and text not in names:
                                names.append(text)

        for key in ("npc_roster", "key_npcs", "characters"):
            raw = bp.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        text = str(item.get("name") or item.get("npc") or "").strip()
                    else:
                        text = str(item or "").strip()
                    if text and text not in names:
                        names.append(text)

        return names[:50]

    @staticmethod
    def _collect_arc_state_entities(arc_data: dict) -> dict[str, list[str]]:
        """Collect explicit entities from arc.state_changes for CP fallback coverage."""
        state_changes = (arc_data or {}).get("state_changes", {}) if isinstance(arc_data, dict) else {}
        npcs = Stage4ContextBuilder._collect_npc_roster(arc_data=arc_data)
        items: list[str] = []
        plots: list[str] = []
        locations: list[str] = []

        for entry in state_changes.get("major_items") or []:
            if isinstance(entry, dict):
                for key in ("name", "item", "target"):
                    text = str(entry.get(key) or "").strip()
                    if text and text not in items:
                        items.append(text)
            elif isinstance(entry, str):
                text = entry.strip()
                if text and text not in items:
                    items.append(text)
        for entry in state_changes.get("items_acquired") or []:
            if isinstance(entry, dict):
                for key in ("name", "item", "target"):
                    text = str(entry.get(key) or "").strip()
                    if text and text not in items:
                        items.append(text)
            elif isinstance(entry, str):
                text = entry.strip()
                if text and text not in items:
                    items.append(text)

        for entry in state_changes.get("resolved_plots") or []:
            if isinstance(entry, dict):
                text = str(entry.get("plot", "") or entry.get("description", "") or "").strip()
            else:
                text = str(entry or "").strip()
            if text and text not in plots:
                plots.append(text)
        for entry in state_changes.get("active_plots") or []:
            if isinstance(entry, dict):
                text = str(entry.get("plot", "") or entry.get("description", "") or "").strip()
            else:
                text = str(entry or "").strip()
            if text and text not in plots:
                plots.append(text)

        for entry in state_changes.get("npc_movements") or []:
            if not isinstance(entry, dict):
                continue
            for key in ("from", "to"):
                text = str(entry.get(key) or "").strip()
                if text and text not in locations:
                    locations.append(text)

        return {"npcs": npcs[:50], "items": items[:20], "plots": plots[:10], "locations": locations[:10]}

    @staticmethod
    def _format_npc_meta_value(value) -> str:
        if isinstance(value, dict):
            if "value" in value:
                value = value.get("value")
            elif "public_role" in value or "secret_role" in value:
                public_role = str(value.get("public_role", "") or "").strip()
                secret_role = str(value.get("secret_role", "") or "").strip()
                known_by = Stage4ContextBuilder._format_npc_meta_value(
                    value.get("known_by") or value.get("known_by_characters") or []
                )
                parts = []
                if public_role:
                    parts.append(f"공개={public_role}")
                if secret_role:
                    parts.append(f"비밀={secret_role}")
                if known_by:
                    parts.append(f"인지={known_by}")
                return " / ".join(parts)
            else:
                return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, list):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        return str(value or "").strip()

    @staticmethod
    def _suggest_ambient_npcs(blueprint: dict) -> str:
        """[TF-J] Blueprint 씬 장소 기반 배경 인물 힌트 생성."""
        if not isinstance(blueprint, dict):
            return ""

        _location_hints = {
            "사무실": "직원, 비서, 인턴, 배달 기사",
            "오피스": "직원, 비서, 인턴, 배달 기사",
            "카페": "바리스타, 다른 손님, 종업원",
            "레스토랑": "웨이터, 소믈리에, 다른 손님",
            "호텔": "프론트 직원, 벨보이, 컨시어지",
            "병원": "간호사, 접수 직원, 다른 환자",
            "거래소": "트레이더, 브로커, 경비원",
            "증권": "영업 직원, 애널리스트, 다른 투자자",
            "은행": "은행원, 지점장, 대기 고객",
            "법원": "서기, 변호사, 방청객",
            "공항": "승무원, 세관 직원, 다른 승객",
            "택시": "택시 기사",
            "거리": "행인, 노점상, 경찰",
            "학교": "교사, 학생, 교직원",
            "본가": "집사, 가사 도우미, 경호원",
            "저택": "집사, 가사 도우미, 경호원",
        }

        hints: list[str] = []
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict):
            return ""

        for scene_key in sorted(scene_breakdown.keys()):
            scene = scene_breakdown.get(scene_key)
            if not isinstance(scene, dict):
                continue
            location = str(scene.get("location", "") or "")
            matched_roles: list[str] = []
            for keyword, npc_roles in _location_hints.items():
                if keyword in location:
                    matched_roles.extend(role.strip() for role in str(npc_roles).split(",") if role.strip())
            if matched_roles:
                dedup_roles = ", ".join(dict.fromkeys(matched_roles))
                hints.append(f"  {scene_key} ({location[:30]}): {dedup_roles}")

        if not hints:
            return ""

        return (
            "[TF-J 배경 인물 힌트]\n"
            "아래는 각 씬 장소에 자연스러운 배경 인물 후보입니다. "
            "이름 없이 역할만으로 활용하세요. 반드시 사용할 필요는 없습니다.\n" + "\n".join(hints)
        )

    def _extract_blueprint_entities(self, blueprint: dict, arc_data: dict | None = None) -> dict[str, list[str] | str]:
        """Blueprint 텍스트에서 이번 화 관련 엔티티를 추출한다."""
        if not blueprint or not isinstance(blueprint, dict):
            return {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": ""}

        text_parts: list[str] = []
        for key in (
            "integrated_scenario",
            "scene_breakdown",
            "core_tension",
            "expected_ending",
            "pacing_notes",
            "target_beat",
            "relationship_changes",
            "time_flow",
            "protagonist_state",
            "synopsis",
            "scenes",
            "ending_hook",
            "key_events",
            "npc_appearances",
            "emotional_arc",
            "required_items",
        ):
            value = blueprint.get(key)
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    text_parts.append(item if isinstance(item, str) else str(item))
            elif isinstance(value, dict):
                text_parts.append(json.dumps(value, ensure_ascii=False, default=str))

        full_text = "\n".join(text_parts)
        world_state = getattr(self.ctx, "world_state", None)
        ws_state = getattr(world_state, "_state", {}) if world_state else {}
        arc_entities = self._collect_arc_state_entities(arc_data or {})

        npcs: list[str] = []
        seen_npcs: set[str] = set()
        for pool in ("alive_npcs", "dead_npcs"):
            for name in ws_state.get(pool) or {}:
                npc_name = str(name).strip()
                if npc_name and npc_name not in seen_npcs and npc_name in full_text:
                    npcs.append(npc_name)
                    seen_npcs.add(npc_name)
        for npc_name in arc_entities.get("npcs", []):
            text = str(npc_name or "").strip()
            if text and text not in seen_npcs:
                npcs.append(text)
                seen_npcs.add(text)

        items: list[str] = []
        for name in ws_state.get("active_items") or {}:
            item_name = str(name).strip()
            if item_name and item_name in full_text:
                items.append(item_name)
        for item_name in arc_entities.get("items", []):
            text = str(item_name or "").strip()
            if text and text not in items:
                items.append(text)

        plots: list[str] = []
        for plot in ws_state.get("active_plots") or []:
            plot_name = plot.get("plot", "") if isinstance(plot, dict) else str(plot)
            plot_name = str(plot_name).strip()
            if plot_name and plot_name in full_text:
                plots.append(plot_name)
        for plot_name in arc_entities.get("plots", []):
            text = str(plot_name or "").strip()
            if text and text not in plots:
                plots.append(text)

        locations: list[str] = []
        protagonist = ws_state.get("protagonist", {}) if isinstance(ws_state, dict) else {}
        location = protagonist.get("location", "") if isinstance(protagonist, dict) else ""
        if location:
            locations.append(str(location))
        for location_name in arc_entities.get("locations", []):
            text = str(location_name or "").strip()
            if text and text not in locations:
                locations.append(text)

        return {"npcs": npcs, "items": items, "plots": plots, "locations": locations, "_full_text": full_text}

    def _build_npc_boundary_block(self, npc_names: list[str]) -> str:
        """Build explicit NPC knowledge/identity guidance for CW/Director."""
        if not npc_names:
            return ""

        project = getattr(self.ctx, "current_project", None)
        bible = getattr(project, "master_bible", None) or {}
        bible_root = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
        assets = bible_root.get("AssetLibrary", {}) if isinstance(bible_root, dict) else {}
        key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
        key_npc_map = {
            str(npc.get("name", "") or "").strip(): npc
            for npc in key_npcs
            if isinstance(npc, dict) and str(npc.get("name", "") or "").strip()
        }
        ws_state = getattr(getattr(self.ctx, "world_state", None), "_state", {}) or {}
        alive = ws_state.get("alive_npcs", {}) if isinstance(ws_state, dict) else {}
        dead = ws_state.get("dead_npcs", {}) if isinstance(ws_state, dict) else {}

        lines = ["[NPC 지식 범위/비밀 인지 참고]"]
        count = 0
        for npc_name in npc_names[:10]:
            text = str(npc_name or "").strip()
            if not text:
                continue
            info = {}
            if text in alive and isinstance(alive.get(text), dict):
                info = alive.get(text) or {}
            elif text in dead and isinstance(dead.get(text), dict):
                info = dead.get(text) or {}
            key_info = key_npc_map.get(text, {})
            known_attrs = info.get("known_attrs", {}) if isinstance(info, dict) else {}
            if not isinstance(known_attrs, dict):
                known_attrs = {}

            def _pick(*values):
                for value in values:
                    rendered = self._format_npc_meta_value(value)
                    if rendered:
                        return rendered
                return ""

            knowledge_era = _pick(
                info.get("knowledge_era"),
                key_info.get("knowledge_era"),
                known_attrs.get("knowledge_era"),
            )
            knowledge_tags = _pick(
                info.get("knowledge_tags"),
                key_info.get("knowledge_tags"),
                known_attrs.get("knowledge_tags"),
            )
            expertise_domain = _pick(
                info.get("expertise_domain"),
                key_info.get("expertise_domain"),
                known_attrs.get("expertise_domain"),
            )
            secrets_known = _pick(
                info.get("secrets_known"),
                key_info.get("secrets_known"),
                known_attrs.get("secrets_known"),
            )
            dual_identity = _pick(
                info.get("dual_identity"),
                key_info.get("dual_identity"),
                known_attrs.get("dual_identity"),
                {
                    "public_role": key_info.get("public_facade") or info.get("public_facade"),
                    "secret_role": key_info.get("secret_role") or info.get("secret_role"),
                    "known_by": key_info.get("known_by") or key_info.get("known_by_characters") or [],
                },
            )

            parts = []
            if knowledge_era:
                parts.append(f"지식시대={knowledge_era}")
            if knowledge_tags:
                parts.append(f"지식태그={knowledge_tags}")
            if expertise_domain:
                parts.append(f"전문영역={expertise_domain}")
            if secrets_known:
                parts.append(f"비밀인지={secrets_known}")
            if dual_identity:
                parts.append(f"이중정체={dual_identity}")
            if not parts:
                continue
            lines.append(f"- {text}: {' / '.join(parts)}")
            count += 1
            if count >= 6:
                break

        if count == 0:
            return ""
        lines.append("위 제약은 참고용 advisory다. 해당 NPC가 모를 정보·말투·정체 노출 여부를 점검하라.")
        return "\n".join(lines)

    @staticmethod
    def _trim_summary_value(value, max_chars: int = 60) -> str:
        text = str(value or "").strip()
        if len(text) <= max_chars:
            return text
        return _fit_context_text(text, max_chars=max_chars)

    @staticmethod
    def _tokenize_focus_terms(value: str) -> set[str]:
        text = str(value or "").strip().lower()
        if not text:
            return set()
        tokens: set[str] = set()
        for token in re.split(r"[\s,|/:;()\[\]{}<>\"'`~!@#$%^&*+=?!.\u2026-]+", text):
            token = token.strip()
            if len(token) < 2:
                continue
            tokens.add(token)
        return tokens

    def _compose_work_focus_text(
        self,
        *,
        arc_data: dict | None,
        arc_tactical: str,
        prev_ending: str,
        blueprint: dict | None,
        cp_entities: dict[str, list[str] | str] | None,
        next_ep: int | None = None,
        max_chars: int = 4000,
    ) -> str:
        parts: list[str] = []
        if arc_tactical:
            parts.append(str(arc_tactical))
        if prev_ending:
            parts.append(str(prev_ending))
        if isinstance(arc_data, dict):
            constraint_summary = resolve_cross_stage_constraint_summary(arc_data)
            if constraint_summary:
                parts.append(constraint_summary)
            for key in ("goal", "core_conflict", "hook"):
                value = str(arc_data.get(key, "") or "").strip()
                if value:
                    parts.append(value)
            mission_lines = resolve_cross_stage_episode_mission_lines(arc_data, ep_num=next_ep)
            if mission_lines:
                parts.extend(mission_lines)
        if isinstance(blueprint, dict):
            for key in ("title", "summary", "hook", "core_conflict", "goal", "twist"):
                value = str(blueprint.get(key, "") or "").strip()
                if value:
                    parts.append(value)
            scene_blocks = blueprint.get("scene_breakdown") or blueprint.get("scenes") or []
            if isinstance(scene_blocks, dict):
                scene_blocks = list(scene_blocks.values())
            if isinstance(scene_blocks, list):
                for scene in scene_blocks[:4]:
                    if not isinstance(scene, dict):
                        continue
                    for key in ("summary", "purpose", "conflict", "location"):
                        value = str(scene.get(key, "") or "").strip()
                        if value:
                            parts.append(value)
        if isinstance(cp_entities, dict):
            for key in ("npcs", "items", "plots", "locations"):
                values = cp_entities.get(key) or []
                if isinstance(values, list) and values:
                    parts.append(" ".join(str(v).strip() for v in values[:8] if str(v).strip()))
        combined = "\n".join(part for part in parts if part)
        if len(combined) > max_chars:
            return _fit_context_text(combined, max_chars=max_chars)
        return combined

    def _resolve_work_retrieval_focus(
        self,
        *,
        stage: str,
        arc_data: dict | None,
        arc_tactical: str,
        prev_ending: str,
        blueprint: dict | None,
        cp_entities: dict[str, list[str] | str] | None,
        next_ep: int | None = None,
    ) -> WorkRetrievalFocusPayload:
        guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if not guard or not hasattr(guard, "select_retrieval_focus"):
            return {}

        focus_text = self._compose_work_focus_text(
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            blueprint=blueprint,
            cp_entities=cp_entities,
            next_ep=next_ep,
        )
        try:
            focus = guard.select_retrieval_focus(stage=stage, focus_text=focus_text)
        except Exception as focus_err:
            logging.debug("[WorkGuard] retrieval focus 선택 실패 (비치명): %s", focus_err)
            return {}

        return focus if isinstance(focus, dict) else {}

    def _build_work_identity_slot_summary(
        self,
        *,
        focus: WorkRetrievalFocusPayload,
        arc_data: dict | None,
        cp_entities: dict[str, list[str] | str] | None,
        next_ep: int | None = None,
        max_chars: int = 1800,
    ) -> str:
        if not isinstance(focus, dict) or not focus:
            return ""

        tracking_slots = [str(x).strip() for x in (focus.get("tracking_slots") or []) if str(x).strip()]
        scene_engines = [str(x).strip() for x in (focus.get("mandatory_scene_engines") or []) if str(x).strip()]
        registry_profiles = [x for x in (focus.get("registry_profiles") or []) if isinstance(x, dict)]

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
                fields = [str(x).strip() for x in (profile.get("required_fields") or []) if str(x).strip()]
                if not name:
                    continue
                rendered_profiles.append(f"{name}" + (f"(fields={', '.join(fields[:4])})" if fields else ""))
            if rendered_profiles:
                lines.append(f"- registry focus: {', '.join(rendered_profiles)}")

        if isinstance(cp_entities, dict):
            linked_parts = []
            for label, key, limit in (
                ("NPC", "npcs", 4),
                ("플롯", "plots", 3),
                ("아이템", "items", 3),
                ("위치", "locations", 2),
            ):
                values = [str(v).strip() for v in (cp_entities.get(key) or []) if str(v).strip()]
                if values:
                    linked_parts.append(f"{label}={', '.join(values[:limit])}")
            if linked_parts:
                lines.append(f"- 이번 화 연동 엔티티: {' | '.join(linked_parts)}")

        if isinstance(arc_data, dict):
            constraint_summary = self._trim_summary_value(
                resolve_cross_stage_constraint_summary(arc_data),
                160,
            )
            if constraint_summary:
                lines.append(f"- 현재 갈등축: {constraint_summary}")
            mission_lines = resolve_cross_stage_episode_mission_lines(arc_data, ep_num=next_ep, limit=2)
            if mission_lines:
                lines.append(f"- 현재 화 mission packet: {' | '.join(mission_lines)}")

        try:
            protagonist_name = self._resolve_protagonist_name()
            focus_text = " ".join(
                [
                    ", ".join(tracking_slots),
                    ", ".join(scene_engines),
                    " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                    resolve_cross_stage_constraint_summary(arc_data),
                    " ".join(resolve_cross_stage_episode_mission_lines(arc_data, ep_num=next_ep, limit=2)),
                ]
            ).strip()
            broker = SemanticQueryBroker(
                db=getattr(self.ctx.current_project, "db", None),
                world_state=getattr(self.ctx, "world_state", None),
                fact_ledger=getattr(self.ctx, "fact_ledger", None),
                state_tracker=getattr(self.ctx, "state_tracker", None),
                protagonist_name=protagonist_name,
            )
            relation_slice = broker.build_stage4_relation_slice(focus_text=focus_text, max_chars=560)
            if relation_slice:
                lines.append(relation_slice)
        except Exception as broker_err:
            logging.debug("[Stage4ContextBuilder] semantic relation slice 생성 실패 (비치명): %s", broker_err)

        result = "\n".join(lines)
        if len(result) > max_chars:
            result = _fit_context_text(result, max_chars=max_chars)
        return result

    def _build_work_identity_authority_packet(
        self,
        *,
        focus: WorkRetrievalFocusPayload,
        arc_data: dict | None,
        blueprint: dict | None,
        cp_entities: dict[str, list[str] | str] | None,
        s4_genre_type: str = "",
        prev_ending: str = "",
        chain_link_section: str = "",
        max_chars: int = 2000,
    ) -> str:
        focus = focus if isinstance(focus, dict) else {}
        tracking_slots = [str(x).strip() for x in (focus.get("tracking_slots") or []) if str(x).strip()]
        scene_engines = [str(x).strip() for x in (focus.get("mandatory_scene_engines") or []) if str(x).strip()]
        registry_profiles = [x for x in (focus.get("registry_profiles") or []) if isinstance(x, dict)]

        blueprint = blueprint if isinstance(blueprint, dict) else {}
        opening_start_location = str(blueprint.get("start_location", "") or blueprint.get("location", "") or "").strip()
        opening_time_flow = str(blueprint.get("time_flow", "") or "").strip()
        opening_scene_location = ""
        opening_scene_title = ""
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, dict) and scenes:
            scene_1 = scenes.get("scene_1") or next(iter(scenes.values()), {})
            if isinstance(scene_1, dict):
                opening_scene_location = str(scene_1.get("location", "") or "").strip()
                opening_scene_title = str(scene_1.get("title", "") or "").strip()
        prev_ending_excerpt = re.sub(r"\s+", " ", str(prev_ending or "").strip())
        if len(prev_ending_excerpt) > 240:
            prev_ending_excerpt = prev_ending_excerpt[:237] + "..."
        carryover_fields = self._extract_chain_link_carryover_fields(chain_link_section)
        carryover_cliffhanger = carryover_fields.get("cliffhanger", "")
        carryover_pending_actions = carryover_fields.get("pending_actions", "")
        carryover_location = carryover_fields.get("location", "")
        carryover_time_marker = carryover_fields.get("time_marker", "")
        soft_carryover_fields = self._extract_chain_link_soft_fields(chain_link_section)
        soft_pending_actions = soft_carryover_fields.get("pending_actions", "")
        soft_physical_state = soft_carryover_fields.get("physical_state", "")
        genre_type = self._resolve_stage4_genre_type(s4_genre_type)
        non_wuxia_genre = not is_wuxia(genre_type)

        if not any(
            [
                tracking_slots,
                scene_engines,
                registry_profiles,
                opening_start_location,
                opening_time_flow,
                opening_scene_location,
                opening_scene_title,
                prev_ending_excerpt,
                carryover_cliffhanger,
                carryover_pending_actions,
                carryover_location,
                carryover_time_marker,
                soft_pending_actions,
                soft_physical_state,
            ]
        ):
            return ""

        lines = ["[Stage4 Opening Scene Authority]"]
        if opening_start_location:
            lines.append(f"- default opening start_location anchor: {opening_start_location}")
        if opening_scene_location and opening_scene_location != opening_start_location:
            lines.append(f"- default opening scene_1.location anchor: {opening_scene_location}")
        if opening_time_flow:
            lines.append(f"- default opening time_flow anchor: {opening_time_flow}")
        if opening_scene_title:
            lines.append(f"- opening scene_1.title anchor: {opening_scene_title}")
        lines.extend(
            [
                "- alternate openings are allowed only with an explicit transition/cut and immediate state declaration.",
                "- do not replay a completed prior-episode event in the opening. Continue its aftermath or explicitly transition away from it.",
                "- if the opening changes location, dominant action, or time band, use an explicit transition sentence or `* * *` first.",
                "- after `* * *`, state the changed location, time, or action within the next 1-2 sentences.",
                "- without a transition signal, do not jump to a new room, vehicle, exterior route, or later time band.",
            ]
        )
        if non_wuxia_genre:
            lines.insert(
                len(lines) - 4,
                "- opening continuity below is baseline authority. Keep true cliffhanger/location/time continuity strong, but allow natural healing or ordinary completion for non-wuxia soft-state carryover when the opening states the shift explicitly.",
            )
        else:
            lines.insert(
                len(lines) - 4,
                "- opening scene continuity below is hard canon. Do not improvise a different movement path or camera reset.",
            )
        if prev_ending_excerpt:
            lines.append(f"- previous ending bridge to honor before new motion: {prev_ending_excerpt}")
        if carryover_cliffhanger:
            lines.append(f"- opening carryover cliffhanger to resolve or explicitly transition from: {carryover_cliffhanger}")
        if carryover_location:
            lines.append(f"- opening carryover location to honor or explicitly transition from: {carryover_location}")
        if carryover_time_marker:
            lines.append(f"- opening carryover time_marker to honor or explicitly advance from: {carryover_time_marker}")
        if carryover_pending_actions:
            lines.append(
                "- opening carryover pending_actions to resolve before new thread or explicitly transition away: "
                f"{carryover_pending_actions}"
            )
        if soft_pending_actions or soft_physical_state:
            lines.append(
                "- non-wuxia soft carryover below is reference guidance. Natural healing or ordinary off-page completion is allowed when the opening states the changed condition clearly."
            )
            if soft_pending_actions:
                lines.append(f"- soft carryover pending_actions reference: {soft_pending_actions}")
            if soft_physical_state:
                lines.append(f"- soft physical_state reference: {soft_physical_state}")

        lines.extend(
            [
                "",
            "[Stage4 Work Identity Authority]",
            "- below fields are hard intake authority, not soft advisory prose.",
            ]
        )
        if tracking_slots:
            lines.append(f"- tracking_slots MUST survive into scene execution: {', '.join(tracking_slots[:3])}")
        if scene_engines:
            lines.append(f"- mandatory_scene_engines MUST appear on-page: {', '.join(scene_engines[:3])}")
        if registry_profiles:
            rendered_profiles = []
            for profile in registry_profiles[:2]:
                name = str(profile.get("name", "") or "").strip()
                fields = [str(x).strip() for x in (profile.get("required_fields") or []) if str(x).strip()]
                purpose = str(profile.get("purpose", "") or "").strip()
                if not name:
                    continue
                extras = []
                if fields:
                    extras.append(f"fields={', '.join(fields[:4])}")
                if purpose:
                    extras.append(f"purpose={purpose[:60]}")
                rendered_profiles.append(name + (f" ({'; '.join(extras)})" if extras else ""))
            if rendered_profiles:
                lines.append(f"- registry_profiles to consult before invention: {', '.join(rendered_profiles)}")

        if isinstance(cp_entities, dict):
            linked_parts = []
            for label, key, limit in (
                ("NPC", "npcs", 4),
                ("plot", "plots", 3),
                ("item", "items", 3),
                ("location", "locations", 2),
            ):
                values = [str(v).strip() for v in (cp_entities.get(key) or []) if str(v).strip()]
                if values:
                    linked_parts.append(f"{label}={', '.join(values[:limit])}")
            if linked_parts:
                lines.append(f"- linked authority entities: {' | '.join(linked_parts)}")

        if isinstance(arc_data, dict):
            constraint_summary = self._trim_summary_value(arc_data.get("constraint_summary", ""), 140)
            if constraint_summary:
                lines.append(f"- active constraint spine: {constraint_summary}")

        numeric_authority_block = self._build_numeric_carryover_authority_block(blueprint=blueprint)
        if numeric_authority_block:
            lines.extend(["", numeric_authority_block])

        result = "\n".join(lines)
        if len(result) > max_chars:
            result = _fit_context_text(result, max_chars=max_chars)
        return result

    @staticmethod
    def _normalize_numeric_authority_key(value: object) -> str:
        return re.sub(r"[\s_]+", "", str(value or "")).lower()

    @classmethod
    def _is_numeric_carryover_key(cls, key: object) -> bool:
        token = cls._normalize_numeric_authority_key(key)
        if not token:
            return False
        return any(marker in token for marker in _NUMERIC_CARRYOVER_KEY_MARKERS)

    @staticmethod
    def _format_numeric_authority_basis(info: dict[str, Any]) -> str:
        last_ep = info.get("last_ep", "?")
        scope = str(info.get("authority_scope") or "").strip().lower()
        if scope == _CARRYOVER_BASELINE_SCOPE:
            return f"EP{last_ep} carryover baseline"
        return f"EP{last_ep} basis"

    def _build_numeric_carryover_authority_block(
        self,
        *,
        blueprint: dict | None,
        max_chars: int = 700,
    ) -> str:
        fact_ledger = getattr(self.ctx, "fact_ledger", None)
        if fact_ledger is None or not hasattr(fact_ledger, "get_numbers"):
            return ""

        try:
            numbers = fact_ledger.get_numbers() or {}
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] numeric carryover authority probe failed", exc_info=exc)
            return ""
        if not isinstance(numbers, dict) or not numbers:
            return ""

        authority_lines: list[str] = []
        for key, info in numbers.items():
            if not isinstance(info, dict):
                continue
            if str(info.get("authority_scope") or "").strip().lower() != _CARRYOVER_BASELINE_SCOPE:
                continue
            if not self._is_numeric_carryover_key(key):
                continue
            value = info.get("value", "?")
            unit = str(info.get("unit", "") or "").strip()
            unit_suffix = f" {unit}" if unit else ""
            basis = self._format_numeric_authority_basis(info)
            authority_lines.append(f"- {key}: {value}{unit_suffix} ({basis})")
            if len(authority_lines) >= 3:
                break

        if not authority_lines:
            return ""

        blueprint_text = ""
        if isinstance(blueprint, dict):
            try:
                blueprint_text = json.dumps(blueprint, ensure_ascii=False)
            except TypeError:
                blueprint_text = str(blueprint)
        blueprint_mentions_assets = any(
            token in blueprint_text.lower()
            for token in ("capital", "asset", "assets", "wealth", "cash", "balance", "funding", "liquidat")
        )

        lines = [
            _STAGE4_NUMERIC_CARRYOVER_AUTHORITY_HEADER,
            "- asset-family FactLedger rows below are prior-episode carryover baselines, not automatic proof that later blueprint target numbers are already realized on-page.",
            *authority_lines,
            "- do not overwrite these baselines with arc or blueprint target numbers unless the manuscript explicitly shows the bridge transaction, liquidation, transfer, or funding event.",
        ]
        if blueprint_mentions_assets:
            lines.append(
                "- if blueprint asset numbers exceed the carryover baseline, treat them as pending claims or targets until the conversion path is written on-page."
            )
        lines.append(
            "- when current-episode capital or total-assets rise above the carryover baseline, narrate how the number became current truth before reusing it as settled fact."
        )

        result = "\n".join(lines)
        if len(result) > max_chars:
            result = _fit_context_text(result, max_chars=max_chars)
        return result

    @staticmethod
    def _extract_chain_link_carryover_fields(chain_link_section: str) -> dict[str, str]:
        if not chain_link_section:
            return {}
        fields: dict[str, str] = {}
        for raw_line in str(chain_link_section).splitlines():
            line = raw_line.strip()
            if not line.startswith("- carryover_"):
                continue
            key, _, value = line[2:].partition(":")
            normalized_key = key.replace("carryover_", "", 1).strip()
            normalized_value = re.sub(r"\s+", " ", value).strip()
            if normalized_key and normalized_value:
                fields[normalized_key] = normalized_value
        return fields

    @staticmethod
    def _extract_chain_link_soft_fields(chain_link_section: str) -> dict[str, str]:
        if not chain_link_section:
            return {}
        fields: dict[str, str] = {}
        for raw_line in str(chain_link_section).splitlines():
            line = raw_line.strip()
            if line.startswith("- soft_carryover_"):
                key, _, value = line[2:].partition(":")
                normalized_key = key.replace("soft_carryover_", "", 1).strip()
            elif line.startswith("- soft_physical_state:"):
                normalized_key = "physical_state"
                _, _, value = line[2:].partition(":")
            else:
                continue
            normalized_value = re.sub(r"\s+", " ", value).strip()
            if normalized_key and normalized_value:
                fields[normalized_key] = normalized_value
        return fields

    @staticmethod
    def _describe_retrieval_coverage_warning(code: str) -> str:
        mapping = {
            "missing_work_slot_summary": "작품 추적 슬롯 요약이 mandatory_context에 없다. work focus continuity를 직접 회수할 것.",
            "work_focus_without_slots": "work_focus가 감지됐지만 retrieval plan에 work_* slot이 없다. 작품 추적 포인트를 직접 반영할 것.",
            "trimmed_work_slot_summary": "작품 추적 슬롯 요약이 context budget에서 잘렸다. 핵심 tracking slot을 직접 회수할 것.",
            "missing_relation_slice": "관계 의미 질의가 빠졌다. 인물 관계 변화와 호칭 근거를 직접 회수할 것.",
        }
        mapping["missing_semantic_carryover"] = (
            "Stage 2 semantic carryover was planned but did not survive into Stage 4 mandatory_context. "
            "Directly restate the relation rationale and continuity anchors."
        )
        return mapping.get(str(code or "").strip(), str(code or "").strip())

    def _build_retrieval_coverage_warning_section(self, coverage_warnings: list[str]) -> str:
        lines: list[str] = []
        seen: set[str] = set()
        for code in coverage_warnings or []:
            text = self._describe_retrieval_coverage_warning(str(code or ""))
            if text and text not in seen:
                seen.add(text)
                lines.append(f"- {text}")
        if not lines:
            return ""
        lines.append(
            "- 이번 화 원고에서는 위 retrieval 근거를 직접 회수하고 관련 인물/작품 축을 명시적으로 재노출할 것."
        )
        return "[검색 커버리지 경고]\n" + "\n".join(lines)

    @staticmethod
    def _summarize_retrieval_sources(plan: "RetrievalPlan | None") -> dict[str, int]:
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
            logging.debug("[Stage4ContextBuilder] retrieval observation record failed: %s", exc)

    def _record_hud_anomaly_observation(self, *, ep_num: int, db) -> None:
        dashboard = getattr(self.ctx, "quality_dashboard", None)
        if dashboard is None or not hasattr(dashboard, "record_hud_anomaly"):
            return
        try:
            result = _detect_hud_anomalies(db, ep_num)
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] HUD anomaly detection failed: %s", exc)
            return

        anomalies = result.get("anomalies") if isinstance(result, dict) else None
        if not isinstance(anomalies, list) or not anomalies:
            return
        try:
            dashboard.record_hud_anomaly(ep_num=ep_num, anomalies=anomalies)
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] HUD anomaly record failed: %s", exc)

    def _prioritize_summaries_by_work_focus(
        self,
        summaries: list[str],
        focus: dict[str, object],
    ) -> list[str]:
        if not summaries or not isinstance(focus, dict) or not focus:
            return summaries

        phrases: list[str] = []
        phrases.extend(str(x).strip() for x in (focus.get("tracking_slots") or []) if str(x).strip())
        phrases.extend(str(x).strip() for x in (focus.get("mandatory_scene_engines") or []) if str(x).strip())
        for profile in focus.get("registry_profiles") or []:
            if not isinstance(profile, dict):
                continue
            for key in ("name", "purpose"):
                value = str(profile.get(key, "") or "").strip()
                if value:
                    phrases.append(value)

        if not phrases:
            return summaries

        phrase_tokens = set()
        for phrase in phrases:
            phrase_tokens |= self._tokenize_focus_terms(phrase)

        scored: list[tuple[int, int, str]] = []
        for idx, summary in enumerate(summaries):
            text = str(summary or "")
            lowered = text.lower()
            score = 0
            for phrase in phrases:
                if phrase.lower() in lowered:
                    score += 4
            score += len(self._tokenize_focus_terms(lowered) & phrase_tokens)
            scored.append((score, idx, text))

        if not any(score > 0 for score, _, _ in scored):
            return summaries
        return [text for _, _, text in sorted(scored, key=lambda row: (-row[0], row[1]))]

    def _filter_state_tracker_summaries_for_authority(
        self,
        summaries: dict[str, str],
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Drop arc-derived summaries that overlap with persisted canonical layers."""
        if not isinstance(summaries, dict) or not summaries:
            return {}, {}

        overlap_sources: dict[str, str] = {}
        if getattr(self.ctx, "world_state", None):
            overlap_sources.update(
                {
                    "dead_npc": "world_state",
                    "item_state": "world_state",
                    "relationship_changes": "world_state",
                    "npc_injury": "world_state",
                    "npc_movement": "world_state",
                    "time_timeline": "world_state",
                }
            )
        if getattr(self.ctx, "fact_ledger", None):
            overlap_sources["financial_state"] = "fact_ledger"

        kept: dict[str, str] = {}
        suppressed: dict[str, str] = {}
        for key, value in summaries.items():
            if value is None:
                continue
            if overlap_sources.get(key) and str(value).strip():
                suppressed[key] = overlap_sources[key]
            else:
                kept[key] = value
        return kept, suppressed

    @staticmethod
    def _build_state_tracker_authority_note(suppressed: dict[str, str]) -> str:
        if not isinstance(suppressed, dict) or not suppressed:
            return ""

        labels = {
            "dead_npc": "사망/NPC 생존 상태",
            "item_state": "아이템 보유 상태",
            "relationship_changes": "관계 변화",
            "npc_injury": "NPC 부상 상태",
            "npc_movement": "NPC 이동 상태",
            "time_timeline": "작중 시간선",
            "financial_state": "금융 상태",
        }
        rendered = []
        for key, source in suppressed.items():
            rendered.append(f"- {labels.get(key, key)}: {source} canonical block 우선")
        return (
            "[Authority precedence]\n아래 persisted canonical 레이어가 같은 영역의 arc-derived state_tracker 요약보다 우선한다.\n"
            + "\n".join(rendered[:8])
        )

    # [Wave-1 authority contract] This statement is the prompt-facing declaration
    # that canonical layers (WorldState, FactLedger) override advisory summaries.
    # The code-facing counterpart is _filter_state_tracker_summaries_for_authority()
    # at L939, which suppresses 7 overlapping StateTracker domains when canonical
    # layers are present. Together they form the Wave 1 authority contract.
    @staticmethod
    def _build_persisted_authority_statement(
        *,
        include_world_state: bool,
        include_fact_ledger: bool,
    ) -> str:
        lines: list[str] = []
        if include_world_state:
            lines.append("- WorldState current-state facts override extracted or advisory summaries on conflict.")
        if include_fact_ledger:
            lines.append("- FactLedger numeric facts override BI seed numbers and arc-derived summaries on conflict.")
        if not lines:
            return ""
        return "[Authority precedence]\n" + "\n".join(lines)

    def _execute_retrieval_plan(self, plan: "RetrievalPlan", arc_no: int | None = None) -> list[str]:
        """Execute retrieval plan slots and return context sections."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return []

        sections: list[str] = []
        compressor = ContextCompressor()
        max_results = int(_threshold("context.vector_max_results_s4", 50))
        current_arc_no = arc_no
        ordered_slots = sorted(plan.slots, key=lambda slot: getattr(slot, "priority", 2))

        for slot in ordered_slots:
            _VM = RetrievalSources.VEC_MEMORY
            source = str(getattr(slot, "source", _VM) or _VM)
            query_text = str(getattr(slot, "query", "") or "").strip()
            if not query_text:
                continue

            try:
                if source == RetrievalSources.STATIC:
                    # [TF-55b] query 문자열 자체가 이미 필요한 내용 → 벡터 검색 불필요
                    result = query_text
                elif source == RetrievalSources.DB_NPC_RELATIONSHIP:
                    # [TF-55b] npc_relationship_history 테이블 직접 조회
                    db = getattr(self.ctx, "db", None)
                    result = ""
                    if db:
                        _body = query_text.replace("관계 변화 이력:", "").strip()
                        _raw_names = [part.split(":")[0].strip() for part in _body.split(",") if part.strip()]
                        _names = [name for name in _raw_names if name]
                        _lines: list[str] = []
                        for _i in range(len(_names)):
                            for _j in range(_i + 1, len(_names)):
                                _rows = db.get_relationship_history(_names[_i], _names[_j], limit=5)
                                for _row in _rows:
                                    _lines.append(
                                        f"EP{_row.get('change_ep', '?')} {_row.get('npc1', '')}-"
                                        f"{_row.get('npc2', '')}: {_row.get('old_relation', '')}->"
                                        f"{_row.get('new_relation', '')}"
                                    )
                        result = "\n".join(_lines) if _lines else ""
                elif source == RetrievalSources.DB_NPC_HISTORY:
                    npc_tokens = self._extract_npc_tokens(query_text)
                    result = memory.retrieve_npc_context(
                        npc_names=npc_tokens,
                        current_ep=plan.episode_num,
                        max_results=max_results,
                    )
                elif source == "manuscript_db":
                    ep_range = self._parse_ep_range_from_query(query_text)
                    if ep_range:
                        result = self._fetch_manuscript_excerpt(ep_range[0], ep_range[1])
                    else:
                        result = ""
                else:
                    # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
                    _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "hybrid")
                    if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                        result = memory.retrieve_hybrid_context(
                            query=query_text,
                            current_ep=plan.episode_num,
                            dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                            sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                            rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                        )
                    elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                        _fts = memory._fts_search(query_text, plan.episode_num, n_results=max_results)
                        result = (
                            "\n\n".join(f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}" for r in _fts)
                            if _fts
                            else ""
                        )
                    else:
                        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
                            logging.warning(
                                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                                _retrieval_mode,
                            )
                        result = memory.retrieve_multi_query_context(
                            queries=[query_text],
                            current_ep=plan.episode_num,
                            n_per_query=3,
                            max_results=max_results,
                            current_arc_no=current_arc_no,
                        )
            except Exception as e:
                logging.warning(f"[SC:SLOT-FAIL] {source}/{slot.category}: {str(e)[:80]}")
                continue

            if not result:
                continue

            slot_max = int(getattr(slot, "max_chars", 0) or 0)
            if slot_max > 0 and len(result) > slot_max:
                result = compressor._smart_trim(result, slot_max)

            sections.append(f"[SC:{slot.category}]\n{result}")

        logging.info(f"[SC] stage4 retrieval: {len(sections)} sections from {len(plan.slots)} slots")
        return sections

    def _fetch_manuscript_excerpt(self, start_ep: int, end_ep: int, max_chars: int = 3000) -> str:
        """DB manuscripts 테이블에서 실제 원고 발췌 반환 (연속성 참조용)."""
        db = getattr(self.ctx, "db", None)
        if not db:
            logging.debug("[Stage4ContextBuilder] _fetch_manuscript_excerpt 스킵: db 없음")
            return ""
        try:
            manuscripts = db.get_manuscripts_range(start_ep, end_ep + 1)
        except Exception as e:
            logging.debug("[Stage4ContextBuilder] 원고 발췌 실패 (비치명): %s", e)
            return ""
        if not manuscripts:
            return ""
        excerpts = []
        for row in manuscripts:
            ep_no = row.get("ep_num", "?")
            content = str(row.get("content", "") or "")
            if content:
                excerpts.append(f"[EP {ep_no} 원고 발췌]\n{_fit_context_text(content, max_chars=800)}")
        combined = "\n\n".join(excerpts)
        return _fit_context_text(combined, max_chars=max_chars)

    def _parse_ep_range_from_query(self, query_text: str) -> tuple[int, int] | None:
        """query_text에서 'ep:N~M' 형식 파싱."""
        import re as _re

        m = _re.search(r"ep:(\d+)~(\d+)", query_text)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None

    def _apply_context_budget(self, sections: list[str], total_budget_chars: int) -> list[str]:
        """Track section-level budget usage and trim large sections when over budget."""
        if not sections:
            return sections

        if total_budget_chars <= 0:
            total_budget_chars = int(_threshold("smart_retrieval.stage4_total_budget", 300000))
        if total_budget_chars <= 0:
            return sections

        from modules.core.context_advisor import ContextBudgetTracker

        def _build_tracker(values: list[str]) -> ContextBudgetTracker:
            tracker = ContextBudgetTracker(total_budget_chars=total_budget_chars)
            for idx, content in enumerate(values, start=1):
                tracker.register_section(f"section_{idx}", content)
            return tracker

        tracker = _build_tracker(sections)
        report = tracker.get_usage_report()
        logging.info(
            f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )

        if report["used_chars"] <= report["total_budget_chars"]:
            return sections

        # [S4-P1-6] 압축 대상 목록을 루프 전 1회 캐시하여 O(n^2) → O(n) 개선
        compression_targets = tracker.get_compression_targets()
        compressor = ContextCompressor()
        protected_prefixes = (
            "[작품 추적 슬롯 요약]",
            "[Stage4 Opening Scene Authority]",
            "[Stage4 Work Identity Authority]",
            _STAGE4_NUMERIC_CARRYOVER_AUTHORITY_HEADER,
        )

        def _used_chars() -> int:
            return sum(len(s) for s in sections)

        target_indices: list[int] = []
        seen: set[int] = set()
        for target in compression_targets:
            try:
                idx = int(target.split("_")[-1]) - 1
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(sections) or idx in seen:
                continue
            seen.add(idx)
            target_indices.append(idx)
        for idx in range(len(sections)):
            if idx not in seen:
                target_indices.append(idx)

        protected_indices = [
            idx for idx in target_indices if any(sections[idx].startswith(prefix) for prefix in protected_prefixes)
        ]
        for idx in target_indices:
            if idx in protected_indices:
                continue
            if sections[idx].startswith("[SC:arc_semantic_carryover]"):
                protected_indices.append(idx)
        regular_indices = [idx for idx in target_indices if idx not in protected_indices]

        def _trim_indices(
            indices: list[int],
            *,
            label: str,
            min_chars: int,
            ratio: float,
            max_rounds: int = 1,
        ) -> None:
            for _ in range(max_rounds):
                if _used_chars() <= total_budget_chars:
                    return
                changed = False
                for idx in indices:
                    section = sections[idx]
                    if len(section) <= min_chars:
                        continue
                    trim_target = max(min_chars, int(len(section) * ratio))
                    if trim_target >= len(section):
                        continue
                    trimmed = compressor._smart_trim(section, trim_target)
                    if len(trimmed) >= len(section):
                        continue
                    orig_len = len(section)
                    sections[idx] = trimmed
                    changed = True
                    logging.info(f"{label} section_{idx + 1}: {orig_len:,}→{len(trimmed):,}자")
                    if _used_chars() <= total_budget_chars:
                        return
                if not changed:
                    return

        # 1) 일반 섹션을 먼저 줄여 opening/work-identity/작품 슬롯 authority가 가능한 한 오래 살아남게 한다.
        _trim_indices(regular_indices, label="[SC:TRIM]", min_chars=300, ratio=0.7, max_rounds=2)
        # 2) 그래도 넘치면 protected authority section만 완만하게 줄인다.
        _trim_indices(protected_indices, label="[SC:TRIM:PROTECTED]", min_chars=500, ratio=0.88, max_rounds=2)
        # 3) 여전히 넘치는 예외 상황에서만 비상 trim을 한 번 더 돈다.
        if _used_chars() > total_budget_chars:
            _trim_indices(regular_indices, label="[SC:TRIM:EMERGENCY]", min_chars=240, ratio=0.5, max_rounds=2)
            _trim_indices(
                protected_indices,
                label="[SC:TRIM:EMERGENCY:PROTECTED]",
                min_chars=420,
                ratio=0.68,
                max_rounds=2,
            )

        # 최종 보고용 tracker 1회 재생성
        tracker = _build_tracker(sections)
        report = tracker.get_usage_report()
        logging.info(
            f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )
        return sections

    @staticmethod
    def _join_context_sections(parts: list[str]) -> str:
        return "\n\n".join(part for part in parts if part)

    def _compose_tiered_mandatory_context_with_headroom(
        self,
        tier0_parts: list[str],
        tier1_parts: list[str],
        tier2_parts: list[str],
    ) -> str:
        """Compose Tier 0/1/2 context while trimming advisory bulk before retrieval."""

        def _combined_text(*bodies: str) -> str:
            return self._join_context_sections([body for body in bodies if body])

        tier0_body = self._join_context_sections(tier0_parts)
        tier1_body = self._join_context_sections(tier1_parts)
        tier2_body = self._join_context_sections(tier2_parts)
        limit = int(_threshold("context.mandatory_context_max", 400000))
        headroom = 0

        if tier1_body and limit > 0:
            headroom = min(20000, max(500, limit // 20))
            headroom = min(headroom, max(0, limit // 5))

        if limit > 0 and tier2_body:
            available_for_tier2 = max(0, limit - len(_combined_text(tier0_body, tier1_body)) - headroom)
            if available_for_tier2 > 0 and len(tier2_body) > available_for_tier2 and tier2_parts:
                trimmed_tier2 = self._apply_context_budget(list(tier2_parts), available_for_tier2)
                tier2_body = self._join_context_sections(trimmed_tier2)
                logging.info(
                    "[S4:CTX] trimmed tier2 against Tier0/Tier1 headroom (t0=%d, t1=%d, t2=%d, limit=%d, headroom=%d)",
                    len(tier0_body),
                    len(tier1_body),
                    len(tier2_body),
                    limit,
                    headroom,
                )

        total_len = len(_combined_text(tier0_body, tier1_body, tier2_body))
        if limit > 0 and total_len > limit and tier1_body and tier1_parts:
            available_for_tier1 = max(300, limit - len(_combined_text(tier0_body, tier2_body)))
            if len(tier1_body) > available_for_tier1:
                trimmed_tier1 = self._apply_context_budget(list(tier1_parts), available_for_tier1)
                tier1_body = self._join_context_sections(trimmed_tier1)
                logging.info(
                    "[S4:CTX] trimmed tier1 after tier2 rebalance (t0=%d, t1=%d, t2=%d, limit=%d)",
                    len(tier0_body),
                    len(tier1_body),
                    len(tier2_body),
                    limit,
                )

        compressor = ContextCompressor()
        total_len = len(_combined_text(tier0_body, tier1_body, tier2_body))
        if limit > 0 and total_len > limit and tier2_body:
            tier2_budget = max(0, limit - len(_combined_text(tier0_body, tier1_body)))
            original_len = len(tier2_body)
            tier2_body = compressor._smart_trim(tier2_body, tier2_budget) if tier2_budget > 0 else ""
            if len(tier2_body) != original_len:
                logging.info("[S4:CTX] final tier2 trim %d→%d (limit=%d)", original_len, len(tier2_body), limit)

        total_len = len(_combined_text(tier0_body, tier1_body, tier2_body))
        if limit > 0 and total_len > limit and tier1_body:
            tier1_budget = max(300, limit - len(_combined_text(tier0_body, tier2_body)))
            if len(tier1_body) > tier1_budget:
                original_len = len(tier1_body)
                tier1_body = compressor._smart_trim(tier1_body, tier1_budget)
                logging.info("[S4:CTX] final tier1 trim %d→%d (limit=%d)", original_len, len(tier1_body), limit)

        mandatory_context = _combined_text(tier0_body, tier1_body, tier2_body)
        total_len = len(mandatory_context)
        logging.info(
            "[S4:CTX] compose pre-final tier0=%d tier1=%d tier2=%d total=%d limit=%d headroom=%d",
            len(tier0_body),
            len(tier1_body),
            len(tier2_body),
            total_len,
            limit,
            headroom,
        )

        prev_budget_meta = getattr(self.ctx, "_stage4_context_budget_meta", {}) or {}
        preserved_callbacks = None
        if isinstance(prev_budget_meta, dict):
            callbacks = prev_budget_meta.get("_callbacks")
            if isinstance(callbacks, dict) and callbacks:
                preserved_callbacks = dict(callbacks)

        self.ctx._stage4_context_budget_meta = {
            "tier0_chars": len(tier0_body),
            "tier1_chars": len(tier1_body),
            "tier2_chars": len(tier2_body),
            "sc_chars": len(tier1_body),
            "mc_chars": len(_combined_text(tier0_body, tier2_body)),
            "total_chars": total_len,
            "limit_chars": limit,
            "headroom_chars": headroom,
        }
        if preserved_callbacks:
            self.ctx._stage4_context_budget_meta["_callbacks"] = preserved_callbacks
        _final_total = total_len
        _dropped_chars = 0
        _overflow_chars = max(0, total_len - limit) if limit > 0 else 0
        if limit > 0 and total_len > limit:
            original_len = len(mandatory_context)
            mandatory_context = compressor._smart_trim(mandatory_context, limit)
            _final_total = len(mandatory_context)
            _dropped_chars = max(0, original_len - _final_total)
            self.ctx._stage4_context_budget_meta["total_chars"] = _final_total
            logging.info("[S4:CTX] final combined trim %d→%d (limit=%d)", original_len, len(mandatory_context), limit)
        self.ctx._stage4_context_budget_meta["budget_ledger"] = build_context_budget_ledger(
            stage="stage4",
            configured_cap=limit,
            fallback_cap=400000,
            effective_cap=limit,
            consumed_chars=_final_total,
            dropped_chars=_dropped_chars,
            overflow_chars=_overflow_chars,
            headroom_chars=headroom,
        )
        return mandatory_context

    def _compose_mandatory_context_with_headroom(self, sc_parts: list[str], mc_parts: list[str]) -> str:
        """Backward-compatible wrapper for SC-first composition callers."""
        return self._compose_tiered_mandatory_context_with_headroom([], sc_parts, mc_parts)

    def load_chain_link_section(self, next_ep: int) -> str:
        """
        [V68] 직전 화의 chain_link를 DB에서 로드하여 프롬프트 주입용 텍스트로 변환.

        1화이거나 직전 chain_link가 없으면 빈 문자열 반환.
        """
        if next_ep <= 1:
            return ""
        try:
            _cl_raw = self.ctx.current_project.db.load_anchor(f"chain_link_{next_ep - 1}")
            if not _cl_raw or not isinstance(_cl_raw, dict):
                return ""
            _cl_data = normalize_chain_link_for_genre(_cl_raw, self._resolve_stage4_genre_type())
            _cl_parts = ["### [V68] 직전 화 연결고리 - 반드시 이어받을 것"]
            if _cl_data.get("cliffhanger"):
                _cl_parts.append(f"- 진행 중 상황: {_cl_data['cliffhanger']}")
            if _cl_data.get("pending_actions"):
                actions = self._render_chain_link_items(_cl_data["pending_actions"])
                if actions:
                    _cl_parts.append(f"- 해야 할 행동: {actions}")
            if _cl_data.get("emotional_state"):
                _cl_parts.append(f"- 감정 상태: {_cl_data['emotional_state']}")
            if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
                _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
            if _cl_data.get("location"):
                _cl_parts.append(f"- 현재 위치: {_cl_data['location']}")
            if _cl_data.get("time_marker"):
                _cl_parts.append(f"- 작중 시간: {_cl_data['time_marker']}")
            _carryover_parts = []
            if _cl_data.get("cliffhanger"):
                _carryover_parts.append(f"- carryover_cliffhanger: {_cl_data['cliffhanger']}")
            if _cl_data.get("pending_actions"):
                actions = self._render_chain_link_items(_cl_data["pending_actions"])
                if actions:
                    _carryover_parts.append(f"- carryover_pending_actions: {actions}")
            if _cl_data.get("location"):
                _carryover_parts.append(f"- carryover_location: {_cl_data['location']}")
            if _cl_data.get("time_marker"):
                _carryover_parts.append(f"- carryover_time_marker: {_cl_data['time_marker']}")
            if _carryover_parts:
                _cl_parts.append("")
                _cl_parts.append("### [ChainLink Carryover Contract]")
                _cl_parts.extend(_carryover_parts)
            _soft_parts = []
            if _cl_data.get("soft_physical_state"):
                _soft_parts.append(f"- soft_physical_state: {_cl_data['soft_physical_state']}")
            if _cl_data.get("soft_pending_actions"):
                soft_actions = self._render_chain_link_items(_cl_data["soft_pending_actions"])
                if soft_actions:
                    _soft_parts.append(f"- soft_carryover_pending_actions: {soft_actions}")
            if _soft_parts:
                _cl_parts.append("")
                _cl_parts.append("### [V68-Soft] 직전 화 soft carryover 참고 - 자연 회복/명시적 전환 허용")
                _cl_parts.extend(_soft_parts)
                _cl_parts.append(
                    "- 비무협 soft state와 routine pending_actions는 opening에서 자연 회복되거나 off-page로 정리될 수 있다. 다만 바뀐 상태는 첫 1-2문장에서 분명히 보여줄 것."
                )
            if len(_cl_parts) > 1:
                return "\n".join(_cl_parts)
            return ""
        except Exception as e:
            logging.warning(f"[SilentPass:ContextBuilder] ChainLink 다이제스트 로드 실패: {e!s:.100}")
            return ""

    def build_extended_lookback_digest(self, next_ep: int) -> str:
        """
        [V66] 직전 10화 원고에서 1-2줄 요약 추출 → mandatory_context 주입.
        기존 3화 lookback을 보완하여 중장기 맥락 제공.
        총 1,500자 이내 truncate.

        [V66.1] B-4: 전문 로드 → SQL SUBSTR 발췌 조회로 최적화 (~100KB I/O 제거/ep).
        첫 200자만 사용하므로 DB에서 200자만 가져옴.
        """
        if next_ep <= 3:
            return ""
        try:
            # 직전 10화 (기존 3화 제외 → ep-10 ~ ep-4 범위)
            start_ep = max(1, next_ep - 10)
            end_ep = max(1, next_ep - 3)  # 최근 3화는 기존 lookback이 커버
            # [V66.1] B-4: 발췌 전용 쿼리 (첫 200자만 DB에서 조회)
            _excerpt_max = _threshold("context.lookback_excerpt_chars", 5000)
            manuscripts = self.ctx.current_project.db.get_recent_manuscript_excerpts(
                before_ep=next_ep, limit=10, max_chars=_excerpt_max
            )
            if not manuscripts or not isinstance(manuscripts, list):
                return ""

            lines = []
            for ms in manuscripts:
                ep_num = ms.get("ep_num", 0)
                if ep_num < start_ep or ep_num >= end_ep:  # end_ep exclusive: 최근 3화는 기존 lookback이 커버
                    continue
                content = ms.get("content", "")
                if not content:
                    continue
                # 첫 문단 또는 첫 150자에서 핵심 요약 추출
                paragraphs = content.split("\n\n")
                first_para = "\n\n".join(paragraphs[:2]) if len(paragraphs) > 1 else content[:_excerpt_max]
                # 줄바꿈 정리
                first_para = re.sub(r"\s+", " ", first_para).strip()
                if len(first_para) > _excerpt_max:
                    first_para = first_para[: _excerpt_max - 3] + "..."
                lines.append(f"[제{ep_num}화] {first_para}")

            if not lines:
                return ""

            digest = "\n".join(lines)
            _total_max = _threshold("context.lookback_total_chars", 40000)
            if len(digest) > _total_max:
                digest = digest[: _total_max - 3] + "..."
            return f"[확장 Lookback: 직전 4~10화 요약]\n{digest}"
        except Exception as e:
            logging.warning(f"[SilentPass:ContextBuilder] 확장 lookback 다이제스트 실패: {e!s:.100}")
            return ""

    def _build_future_arc_context(self, current_ep: int, arc_data: dict) -> str:
        """
        [미래 서사 방향 힌트] 현재 Arc 남은 Blueprint + 다음 Arc 요약 → 포맷된 텍스트 반환.
        mandatory_context에 append되어 CW·Director 양쪽에 주입됨.
        """
        try:
            lines = [
                "[미래 Arc/Blueprint 참고]\n"
                "▸ CW: 아래 향후 계획에 없는 새 갈등·사건·인물관계를 임의로 추가하지 마세요.\n"
                "▸ Director: Blueprint에 없는 서사 요소가 아래 미래 계획과 무관하면 점수 차감 사유입니다."
            ]

            # 1. 현재 Arc 내 남은 Blueprint (ep+1 ~ arc_end)
            arc_end = arc_data.get("ep_end", current_ep) if arc_data else current_ep
            remaining = []
            for ep in range(current_ep + 1, arc_end + 1):
                try:
                    bp = self.ctx.current_project.get_blueprint(ep)
                except Exception:
                    bp = None
                if bp:
                    scenario = str(bp.get("integrated_scenario", ""))[:200]
                    core = str(bp.get("core_tension", ""))[:80]
                    remaining.append(f"  제{ep}화: {scenario}" + (f" / 긴장: {core}" if core else ""))

            if remaining:
                lines.append("[현재 Arc 남은 화 Blueprint]")
                lines.extend(remaining)

            # 2. 다음 Arc 1개 — beat_sequence + tactical_doc 앞 500자
            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            _db = getattr(self.ctx.current_project, "db", None)
            all_arcs: list[dict] = []
            try:
                all_arcs = (_db.load_anchor("arcs") if _db else []) or []
            except Exception:
                all_arcs = []
            future_arcs = sorted(
                [a for a in all_arcs if isinstance(a, dict) and a.get("arc_no", 0) > current_arc_no],
                key=lambda a: a.get("arc_no", 0),
            )
            if future_arcs:
                arc = future_arcs[0]
                beats = " → ".join(str(b) for b in arc.get("beat_sequence", [])[:6])
                snippet = str(arc.get("tactical_doc", ""))[:500]
                lines.append(
                    f"[다음 Arc {arc.get('arc_no')} '{arc.get('title', '')}' "
                    f"({arc.get('ep_start')}~{arc.get('ep_end')}화)]"
                )
                if beats:
                    lines.append(f"  비트: {beats}")
                if snippet:
                    lines.append(f"  방향: {snippet}")

            if len(lines) == 1:
                return ""

            return "\n".join(lines)
        except Exception as _fut_err:
            logging.warning("[SilentPass:FutureArcCtx] 미래 Arc 컨텍스트 생성 실패: %s", str(_fut_err)[:80])
            return ""

    def _build_stage2_failure_context(self, arc_data: dict) -> str:
        """Stage 2의 최근 실패/보정 이력을 Stage 4 mandatory_context에 요약 주입."""
        if not isinstance(arc_data, dict):
            return ""

        _arc_no = arc_data.get("arc_no")
        try:
            _arc_no = int(_arc_no)
        except (TypeError, ValueError):
            return ""

        _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        if not _db or not hasattr(_db, "get_stage_attempts_for_arc"):
            return ""

        try:
            _rows = _db.get_stage_attempts_for_arc(_arc_no, stages=(2,), limit=12) or []
        except Exception as exc:
            logging.debug("[Stage4ContextBuilder] stage2 failure context 로드 실패 (비치명): %s", exc)
            return ""

        if not isinstance(_rows, list) or not _rows:
            return ""

        def _compact(_value: object, limit: int = 120) -> str:
            _text = " ".join(str(_value or "").split())
            if len(_text) <= limit:
                return _text
            return _text[: limit - 3].rstrip() + "..."

        _noteworthy: list[dict] = []
        for _row in _rows:
            if not isinstance(_row, dict):
                continue
            _verdict = str(_row.get("verdict", "") or "").strip()
            if _verdict in {"REJECT", "PASS_WITH_FIX", "PASS_WITH_WARNING"} or any(
                _row.get(_field)
                for _field in (
                    "reject_reason",
                    "selection_reason",
                    "verdict_reason",
                    "open_review",
                    "fix_scope_reasoning",
                    "runtime_advisory",
                    "retry_directives",
                )
            ):
                _noteworthy.append(_row)

        if not _noteworthy:
            return ""

        _category_counts: dict[str, int] = {}
        _reason_samples: list[str] = []
        _retry_samples: list[str] = []
        for _row in _noteworthy:
            _category = str(_row.get("failure_category", "") or "").strip()
            if _category:
                _category_counts[_category] = _category_counts.get(_category, 0) + 1
            for _field in ("reject_reason", "verdict_reason", "selection_reason", "open_review"):
                _reason = _compact(_row.get(_field, ""))
                if _reason and _reason not in _reason_samples:
                    _reason_samples.append(_reason)
            for _field in ("fix_scope_reasoning", "runtime_advisory", "retry_directives"):
                _retry = _compact(_row.get(_field, ""))
                if _retry and _retry not in _retry_samples:
                    _retry_samples.append(_retry)

        _top_categories = sorted(_category_counts.items(), key=lambda item: item[1], reverse=True)[:3]
        _lines = [
            "[Stage 2 실패/보정 이력]",
            "아래 Arc 설계 실패/보정 맥락을 우선 반영하고 같은 유형의 문제를 반복하지 말 것.",
        ]
        if _top_categories:
            _lines.append("주요 카테고리: " + ", ".join(f"{name}({count})" for name, count in _top_categories))
        if _reason_samples:
            _lines.append("대표 사유:")
            for _reason in _reason_samples[:3]:
                _lines.append(f"- {_reason}")
        if _retry_samples:
            _lines.append("대표 보정/재시도 지시:")
            for _retry in _retry_samples[:3]:
                _lines.append(f"- {_retry}")

        return "\n".join(_lines)

    def _build_tier0_mandatory_sections(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        blueprint: dict | None,
        s4_genre_type: str,
        prev_ending: str,
        chain_link_section: str,
        cp_entities: dict[str, list[str] | str],
        work_focus: WorkRetrievalFocusPayload,
        mandatory_context: str,
    ) -> list[str]:
        """Assemble tier-0 mandatory sections in stable insertion order."""
        # [Tier-0 injection stack] Final ordering after all insert(0, ...) calls:
        #   NPC boundary block
        #   > Stage4 work identity authority packet
        #   > continuity packet
        #   > canonical constraints (authority statement + NPC L0 + numeric L0)
        #   > fact ledger summary
        #   > timeline summary
        #   > world state summary
        #   > mandatory_context (arc constraints, etc.)
        #   > wuxia technique/realm authority clause (append, not insert)
        # Sections inserted via insert(0, ...) end up in reverse order of insertion.
        tier0_parts = [mandatory_context] if mandatory_context else []

        arc_constraint_summary = resolve_cross_stage_constraint_summary(arc_data)
        if arc_constraint_summary:
            tier0_parts.append(f"[Arc 제약 - MUST NOT DO]\n{arc_constraint_summary}")
        mission_lines = resolve_cross_stage_episode_mission_lines(arc_data, ep_num=next_ep)
        if mission_lines:
            tier0_parts.append("[Current Episode Mission Packet]\n" + "\n".join(f"- {line}" for line in mission_lines))

        if self.ctx.world_state:
            try:
                if cp_entities.get("npcs") or cp_entities.get("items") or cp_entities.get("plots"):
                    world_state_summary = self.context_packets.build_condensed_world_state_summary(
                        cp_entities,
                        max_chars=50000,
                    )
                    if not world_state_summary:
                        world_state_summary = self.ctx.world_state.get_summary(max_chars=50000)
                else:
                    world_state_summary = self.ctx.world_state.get_summary(max_chars=50000)
                if world_state_summary:
                    tier0_parts.insert(0, world_state_summary)
                    logging.info(" [V68] 세계 상태 문서 주입 (%d자)", len(world_state_summary))
            except Exception as world_state_err:
                logging.warning(" [V68] 세계 상태 문서 주입 실패 (비치명): %s", str(world_state_err)[:50])

        try:
            timeline_budget = int(_threshold("context.timeline_budget", 3000))
            timeline_text = ""
            if getattr(self.ctx, "world_state", None):
                timeline_text = self.ctx.world_state.get_timeline_summary(max_chars=timeline_budget)
            if timeline_text:
                tier0_parts.insert(0, timeline_text)
                logging.info("[Phase3] 타임라인 주입 (%d자)", len(timeline_text))
        except Exception as timeline_err:
            logging.warning("[Phase3] 타임라인 주입 실패 (비치명): %s", str(timeline_err)[:50])

        if self.ctx.fact_ledger:
            try:
                if cp_entities.get("npcs") or cp_entities.get("items") or cp_entities.get("_full_text"):
                    fact_ledger_summary = self.context_packets.build_condensed_fact_ledger_summary(
                        cp_entities,
                        max_chars=25000,
                    )
                    if not fact_ledger_summary:
                        fact_ledger_summary = self.ctx.fact_ledger.to_summary(max_chars=25000)
                else:
                    fact_ledger_summary = self.ctx.fact_ledger.to_summary(max_chars=25000)
                if fact_ledger_summary:
                    tier0_parts.insert(0, fact_ledger_summary)
                    logging.info(" [V68] 팩트 원장 주입 (%d자)", len(fact_ledger_summary))
            except Exception as fact_ledger_err:
                logging.warning(" [V68] 팩트 원장 주입 실패 (비치명): %s", str(fact_ledger_err)[:50])

        try:
            canonical_budget = int(_threshold("context.canonical_facts_budget", 13000))
            canonical_npc = ""
            canonical_numeric = ""
            if getattr(self.ctx, "world_state", None):
                canonical_npc = self.ctx.world_state.get_canonical_constraints(max_chars=int(canonical_budget * 0.62))
            if getattr(self.ctx, "fact_ledger", None):
                canonical_numeric = self.ctx.fact_ledger.get_canonical_summary(max_chars=int(canonical_budget * 0.38))
            if canonical_npc or canonical_numeric:
                authority_statement = self._build_persisted_authority_statement(
                    include_world_state=bool(canonical_npc),
                    include_fact_ledger=bool(canonical_numeric),
                )
                canonical_parts = [authority_statement] if authority_statement else []
                canonical_parts.extend(x for x in [canonical_npc, canonical_numeric] if x)
                canonical_block = "\n\n".join(canonical_parts)
                tier0_parts.insert(0, canonical_block)
                logging.info("[Phase1-L0] Canonical 고정 주입 (%d자)", len(canonical_block))
        except Exception as canonical_err:
            logging.warning("[Phase1-L0] Canonical 주입 실패 (비치명): %s", str(canonical_err)[:50])

        # [Wave-TR1] Wuxia-only protagonist technique/realm authority clause
        try:
            _genre_name = ""
            if getattr(self.ctx, "current_project", None):
                _genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "")
            if _genre_name in ("무협", "wuxia"):
                _ws = getattr(self.ctx, "world_state", None)
                _protag_skills = (_ws._state.get("protagonist", {}).get("skills") or []) if _ws else []
                if _protag_skills:
                    tier0_parts.append(
                        "[무협 기술/경지 권위]\n"
                        "- 확정된 주인공 경지 및 습득 기술 목록이 BI 초기 설정이나 advisory 요약보다 우선한다.\n"
                        "- 주인공의 현재 경지에서 허용되지 않는 기술을 사용하면 안 된다."
                    )
                    logging.info("[Wave-TR1] Wuxia technique/realm authority clause injected (%d skills)", len(_protag_skills))
        except Exception as _wuxia_auth_err:
            logging.debug("[Wave-TR1] Wuxia authority clause skipped (non-blocking): %s", _wuxia_auth_err)

        if blueprint:
            try:
                continuity_packet = self.context_packets.build_continuity_packet(cp_entities)
                if continuity_packet:
                    tier0_parts.insert(0, continuity_packet)
                    logging.info(
                        "[CP] Continuity Packet 주입 (%d자, NPC %d, 플롯 %d, 아이템 %d)",
                        len(continuity_packet),
                        len(cp_entities["npcs"]),
                        len(cp_entities["plots"]),
                        len(cp_entities["items"]),
                    )
            except Exception as continuity_err:
                logging.warning("[CP] Continuity Packet 생성 실패 (비치명): %s", str(continuity_err)[:80])

        try:
            work_identity_authority = self._build_work_identity_authority_packet(
                focus=work_focus,
                arc_data=arc_data,
                blueprint=blueprint,
                cp_entities=cp_entities,
                s4_genre_type=s4_genre_type,
                prev_ending=prev_ending,
                chain_link_section=chain_link_section,
            )
            if work_identity_authority:
                tier0_parts.insert(0, work_identity_authority)
                logging.info("[WorkGuard] Stage4 work identity authority packet injected (%d chars)", len(work_identity_authority))
        except Exception as work_identity_err:
            logging.debug("[WorkGuard] Stage4 authority packet build failed (non-blocking): %s", work_identity_err)

        try:
            boundary_npcs = list(cp_entities.get("npcs") or [])
            if not boundary_npcs:
                boundary_npcs = self._collect_npc_roster(arc_data=arc_data or {}, blueprint=blueprint or {})
            npc_boundary_block = self._build_npc_boundary_block(boundary_npcs)
            if npc_boundary_block:
                tier0_parts.insert(0, npc_boundary_block)
        except Exception as npc_boundary_err:
            logging.debug("[QI-NPC] NPC boundary block 생성 실패 (비치명): %s", npc_boundary_err)

        return tier0_parts

    def _collect_stage4_retrieval_context(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        prev_ending: str,
        arc_tactical: str,
        blueprint: dict | None,
        s4_genre_type: str,
        work_focus: str,
        tier1_parts: list[str],
    ) -> Stage4RetrievalContextPayload:
        """Collect Stage 4 retrieval context and append legacy vector memory blocks."""
        retrieval_plan = None
        sc_parts: list[str] = []

        try:
            if self.ctx.memory and prev_ending:
                use_advisor_path = False
                advisor = getattr(self.ctx, "context_advisor", None)
                smart_enabled = bool(_threshold("smart_retrieval.enabled", True)) and bool(
                    _threshold("smart_retrieval.stage4_enabled", True)
                )
                current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1

                if advisor and smart_enabled:
                    arc_ep_start = arc_data.get("ep_start", next_ep) if arc_data else next_ep
                    arc_ep_count = arc_data.get("ep_count", 0) if arc_data else 0
                    arc_pos = next_ep - arc_ep_start + 1
                    is_arc_boundary = arc_pos <= 1 or (arc_ep_count > 0 and arc_pos >= arc_ep_count)
                    npc_roster = self._collect_npc_roster(arc_data=arc_data, blueprint=blueprint)
                    retrieval_plan = advisor.plan_stage4_retrieval(
                        arc_data=arc_data or {},
                        blueprint=blueprint or {},
                        prev_ending=prev_ending,
                        current_ep=next_ep,
                        npc_roster=npc_roster,
                        genre=s4_genre_type,
                        work_focus=work_focus,
                        is_arc_boundary=is_arc_boundary,
                        is_reject_retry=False,
                    )
                    perf_key = f"sc_stage4_ep{next_ep}_retrieval"
                    try:
                        self.ctx.perf_timer.start(perf_key)
                    except Exception as perf_err:
                        logging.debug("[Stage4ContextBuilder] perf_timer SC start 실패 (무시): %s", perf_err)
                    try:
                        arc_no_s4 = arc_data.get("arc_no", None) if arc_data else None
                        for retrieved in self._execute_retrieval_plan(retrieval_plan, arc_no=arc_no_s4):
                            sc_parts.append(retrieved)
                    finally:
                        try:
                            self.ctx.perf_timer.stop(perf_key)
                        except Exception as perf_err:
                            logging.debug("[Stage4ContextBuilder] perf_timer SC stop 실패 (무시): %s", perf_err)
                    use_advisor_path = True

                mq_queries = [] if use_advisor_path else [prev_ending]
                if not use_advisor_path:
                    logging.warning("[Q6-T3] advisor plan 미사용 → 레거시 벡터 검색 폴백 (ep=%d)", next_ep)
                if (not use_advisor_path) and arc_data and arc_data.get("state_changes"):
                    state_changes = arc_data["state_changes"]
                    npc_names = []
                    if not isinstance(state_changes, dict):
                        state_changes = {}
                    for field in ["npc_deaths", "relationship_changes", "npc_injuries"]:
                        for entry in state_changes.get(field) or []:
                            if isinstance(entry, dict):
                                npc_name = entry.get("name") or entry.get("npc", "")
                            elif isinstance(entry, str):
                                npc_name = entry
                            else:
                                continue
                            if npc_name:
                                npc_names.append(npc_name)
                    if npc_names:
                        mq_queries.append(" ".join(npc_names[:5]))

                if (not use_advisor_path) and arc_tactical and len(arc_tactical) > 50:
                    episode_tactical = extract_episode_tactical(
                        arc_tactical,
                        next_ep,
                        episode_details=(arc_data or {}).get("episode_details"),
                        fallback_full=False,
                    )
                    if episode_tactical:
                        mq_queries.append(_fit_context_text(episode_tactical, max_chars=1800))
                    else:
                        mq_queries.append(_fit_context_text(arc_tactical, max_chars=1800))

                genre_queries = {
                    "hunter": ["던전 클리어 각성 스킬 랭크"],
                    "investment": ["포트폴리오 거래 수익률 투자"],
                    "fantasy": ["마법 축복 주문 마나 정령"],
                }
                if (not use_advisor_path) and s4_genre_type in genre_queries:
                    mq_queries.extend(genre_queries[s4_genre_type])

                if mq_queries:
                    vector_memory = self.ctx.memory.retrieve_multi_query_context(
                        queries=mq_queries,
                        current_ep=next_ep,
                        n_per_query=3,
                        max_results=_threshold("context.vector_max_results_s4", 50),
                        current_arc_no=current_arc_no,
                    )
                    if vector_memory:
                        tier1_parts.append(f"[과거 유사 맥락 (벡터 검색)]\n{vector_memory}")
        except Exception as exc:
            self.ctx.ui.log(f"   ⚠️ 벡터 검색 실패 (비치명): {exc}")

        return {
            "retrieval_plan": retrieval_plan,
            "sc_parts": sc_parts,
            "tier1_parts": tier1_parts,
        }

    def _compose_context_with_retrieval_coverage(
        self,
        *,
        next_ep: int,
        work_focus: str,
        retrieval_plan,
        tier0_parts: list[str],
        tier1_parts: list[str],
        sc_parts: list[str],
        tier2_parts: list[str],
        slot_summary: str,
    ) -> Stage4RetrievalCoveragePayload:
        """Compose mandatory context with SC retrieval coverage bookkeeping."""
        sc_budget = int(getattr(retrieval_plan, "total_budget_chars", 0) or 0)
        if _threshold("smart_retrieval.enabled", True) and _threshold("smart_retrieval.stage4_enabled", True):
            tier2_parts = self._apply_context_budget(tier2_parts, sc_budget)

        source_counts = self._summarize_retrieval_sources(retrieval_plan)
        if not source_counts and any("[과거 유사 맥락" in str(part) for part in tier1_parts):
            source_counts = {"legacy_multi_query": 1}

        def _compute_coverage_warnings(context_text: str) -> list[str]:
            warnings: list[str] = []
            if work_focus and not slot_summary:
                warnings.append("missing_work_slot_summary")
            if (
                work_focus
                and retrieval_plan
                and not any(
                    str(getattr(slot, "category", "")).startswith("work_")
                    for slot in (getattr(retrieval_plan, "slots", []) or [])
                )
            ):
                warnings.append("work_focus_without_slots")
            if slot_summary and "[작품 추적 슬롯 요약]" not in context_text:
                warnings.append("trimmed_work_slot_summary")
            if source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0 and "[관계 의미 질의]" not in context_text:
                warnings.append("missing_relation_slice")
            if (
                retrieval_plan
                and any(
                    str(getattr(slot, "category", "") or "") == "arc_semantic_carryover"
                    for slot in (getattr(retrieval_plan, "slots", []) or [])
                )
                and "[SC:arc_semantic_carryover]" not in context_text
            ):
                warnings.append("missing_semantic_carryover")
            return warnings

        mandatory_context = ""
        coverage_warnings: list[str] = []
        coverage_note = ""
        coverage_note_idx: int | None = None
        for _ in range(3):
            tier1_body = tier1_parts + sc_parts
            mandatory_context = self._compose_tiered_mandatory_context_with_headroom(
                tier0_parts,
                tier1_body,
                tier2_parts,
            )
            coverage_warnings = _compute_coverage_warnings(mandatory_context)
            next_coverage_note = self._build_retrieval_coverage_warning_section(coverage_warnings)
            if not next_coverage_note or coverage_note == next_coverage_note:
                break
            if coverage_note_idx is None:
                tier2_parts.insert(0, next_coverage_note)
                coverage_note_idx = 0
            else:
                tier2_parts[coverage_note_idx] = next_coverage_note
            coverage_note = next_coverage_note

        slot_summary_survived = "[작품 추적 슬롯 요약]" in mandatory_context
        vector_context_chars = sum(len(str(part or "")) for part in sc_parts)
        stage4_budget_ledger = dict(
            (getattr(self.ctx, "_stage4_context_budget_meta", {}) or {}).get("budget_ledger") or {}
        )
        self._record_retrieval_observation(
            ep_num=next_ep,
            stage="stage4",
            observation=build_context_observation(
                stage="stage4",
                work_focus=work_focus,
                retrieval_plan=retrieval_plan,
                source_counts=source_counts,
                coverage_warnings=coverage_warnings,
                advisor_path_used=bool(retrieval_plan),
                work_slot_summary_present=bool(slot_summary),
                work_slot_summary_included=slot_summary_survived,
                relation_slice_included="[관계 의미 질의]" in mandatory_context,
                vector_context_chars=vector_context_chars,
                mandatory_context_chars=len(mandatory_context),
                protected_summary_survived=slot_summary_survived,
                trimmed_work_slot_summary=bool(slot_summary and not slot_summary_survived),
                budget_ledger=stage4_budget_ledger,
            ),
        )

        return {
            "mandatory_context": mandatory_context,
            "coverage_warnings": coverage_warnings,
            "source_counts": source_counts,
            "tier2_parts": tier2_parts,
        }

    def _build_prev_manuscripts_text(self, next_ep: int) -> str:
        _db = self.ctx.current_project.db
        _prev_manuscripts_parts: list[str] = []

        # [Tier4-12] Tier 1: recent 30 episodes full text  [1M-CTX: 20→30]
        _tier1_start = max(1, next_ep - 30)
        _tier1_rows: list[dict] = []
        try:
            if hasattr(_db, "get_manuscripts_range"):
                _tier1_rows = _db.get_manuscripts_range(_tier1_start, next_ep) or []
            else:
                for _prev_ep in range(_tier1_start, next_ep):
                    _row = _db.get_manuscript(_prev_ep)
                    if _row:
                        _tier1_rows.append(
                            {
                                "ep_num": _prev_ep,
                                "content": _row.get("content", "") if isinstance(_row, dict) else str(_row),
                            }
                        )
        except Exception as e:
            logging.warning(f"[SilentPass:Tier4-12] tier1 full-text load failed: {e!s:.100}")
            _tier1_rows = []

        for _row in _tier1_rows:
            _ep_no = int(_row.get("ep_num", 0) or 0)
            _content = str(_row.get("content", "") or "")
            if _content and len(_content) > 100:
                _prev_manuscripts_parts.append(f"[EP {_ep_no}]\n{_content}")

        # [Tier4-12] Tier 2: summaries for episodes 21~60 before current  [Phase3-A: 30→60]
        _tier2_start = max(1, next_ep - 60)
        _tier2_end = _tier1_start
        if _tier2_end > _tier2_start:
            _tier2_parts: list[str] = []
            try:
                if hasattr(_db, "get_episode_meta_summaries"):
                    _rows = _db.get_episode_meta_summaries(_tier2_start, _tier2_end) or []
                else:
                    _rows = []

                for _row in _rows:
                    if isinstance(_row, dict):
                        _ep_no = int(_row.get("ep_num", 0) or 0)
                        _summary = str(_row.get("summary", "") or "")
                    else:
                        _ep_no = int(_row["ep_num"] or 0)
                        _summary = str(_row["summary"] or "")
                    if _summary:
                        _tier2_parts.append(f"[EP {_ep_no} summary] {_summary[:5000]}")
            except Exception as e:
                logging.warning(f"[SilentPass:Tier4-12] tier2 summary load failed: {e!s:.100}")

            if _tier2_parts:
                _prev_manuscripts_parts.insert(
                    0, "-- Tier2 summaries (21-60 episodes back) --\n" + "\n".join(_tier2_parts)
                )

        # [Tier4-12] Tier 3: older arc summaries
        if _tier2_start > 1:
            _tier3_parts: list[str] = []
            try:
                _arcs = _db.load_anchor("arcs") or []
            except Exception:
                _arcs = []

            for _idx, _arc in enumerate(_arcs):
                if not isinstance(_arc, dict):
                    continue
                _arc_no = int(_arc.get("arc_no", _idx + 1) or (_idx + 1))
                _arc_eps = _arc.get("episodes", [])
                if not isinstance(_arc_eps, list) or not _arc_eps:
                    continue

                _arc_max_ep = 0
                for _ep in _arc_eps:
                    if isinstance(_ep, int):
                        _arc_max_ep = max(_arc_max_ep, _ep)
                    elif isinstance(_ep, dict):
                        _cand = _ep.get("ep_num") or _ep.get("episode") or _ep.get("ep") or 0
                        try:
                            _arc_max_ep = max(_arc_max_ep, int(_cand))
                        except (TypeError, ValueError):
                            continue
                if _arc_max_ep >= _tier2_start:
                    continue

                try:
                    _arc_sum = self.ctx.current_project.load_v20_anchor(f"arc_summary_{_arc_no}")
                    if not _arc_sum:
                        continue
                    if isinstance(_arc_sum, dict):
                        _sum_text = str(_arc_sum.get("summary", _arc_sum) or "")
                    else:
                        _sum_text = str(_arc_sum)
                    if _sum_text:
                        _tier3_parts.append(f"[Arc {_arc_no} summary] {_sum_text[:8000]}")
                except Exception:
                    continue

            if _tier3_parts:
                _prev_manuscripts_parts.insert(
                    0,
                    "-- Tier3 arc summaries (older than 60 episodes) --\n" + "\n".join(_tier3_parts),
                )

        _prev_manuscripts_text = "\n\n---\n\n".join(_prev_manuscripts_parts) if _prev_manuscripts_parts else ""
        if _prev_manuscripts_parts:
            logging.info(
                "[Tier4-12] hybrid lookback ready: parts=%d chars=%d",
                len(_prev_manuscripts_parts),
                len(_prev_manuscripts_text),
            )
        return _prev_manuscripts_text

    def prepare_episode_context(self, next_ep: int, arc_data: dict, chief_writer) -> dict:
        """에피소드별 컨텍스트 데이터 수집 (Arc 메타 + 이전 원고 + HUD + 연결고리)."""
        base_payload = self._build_episode_base_payload(
            next_ep=next_ep,
            arc_data=arc_data,
            chief_writer=chief_writer,
            db=self.ctx.current_project.db,
        )

        state_payload = self._build_episode_state_payload(next_ep=next_ep, db=self.ctx.current_project.db)

        return {
            **base_payload,
            **state_payload,
        }

    def _build_episode_base_payload(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        chief_writer,
        db,
    ) -> Stage4EpisodeBasePayload:
        arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1
        total_ep_in_arc = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):  # [V70] dict 타입 방어
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)
        arc_tactical = str(arc_tactical) if arc_tactical else ""

        prev_ms_data = db.get_manuscript(next_ep - 1)
        prev_text = (prev_ms_data.get("content") or "") if prev_ms_data else ""  # [V70] NULL content 방어
        prev_ending = prev_text[-2500:] if prev_text else ""  # [1M-CTX: 500→2500] CW와 동일 수준

        prev_manuscripts_text = self._build_prev_manuscripts_text(next_ep)
        if next_ep >= 60:
            try:
                world_state = getattr(self.ctx, "world_state", None)
                if world_state and hasattr(world_state, "get_long_term_anchor"):
                    long_term_anchor = world_state.get_long_term_anchor(current_ep=next_ep)
                    if long_term_anchor:
                        prev_manuscripts_text = (
                            long_term_anchor + "\n\n---\n\n" + prev_manuscripts_text
                            if prev_manuscripts_text
                            else long_term_anchor
                        )
                        logging.info("[LongTerm] 장기 설정 앵커 주입 (ep%d, %d자)", next_ep, len(long_term_anchor))
            except Exception as long_term_err:
                logging.debug("[LongTerm] 장기 설정 앵커 주입 실패 (비차단): %s", long_term_err)

        episode_digest = self._build_episode_digest(
            prev_text=prev_text,
            next_ep=next_ep,
            chief_writer=chief_writer,
        )
        return Stage4EpisodeBasePayload(
            arc_pos=arc_pos,
            total_ep_in_arc=total_ep_in_arc,
            arc_tactical=arc_tactical,
            prev_text=prev_text,
            prev_ending=prev_ending,
            prev_manuscripts_text=prev_manuscripts_text,
            episode_digest=episode_digest,
        )

    def _build_episode_state_payload(self, *, next_ep: int, db) -> Stage4EpisodeStatePayload:
        hud = self.ctx.sys.hud if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud else None
        hud_report = hud.get_v20_hud_report() if hud else ""

        current_inventory: list[Any] = []
        current_martial_arts: list[Any] = []
        if hud:
            current_inventory = list(hud.inventory) if hasattr(hud, "inventory") and hud.inventory else []
            current_martial_arts = list(hud.techniques) if hasattr(hud, "techniques") and hud.techniques else []

        # [S4-P2-6] dead_npcs만 필요하지만 개별 쿼리 없음 — DBManager 내부 캐시(_cumulative_bible_cache)로 반복 로드 무비용
        cumulative_bible = db.get_cumulative_bible(next_ep - 1)
        dead_npcs = cumulative_bible.get("dead_npcs", []) if cumulative_bible else []
        if isinstance(dead_npcs, str):
            dead_npcs = [dead_npcs]  # LLM이 단일 문자열 반환 시 리스트화

        item_acquisition_timeline = self.ctx.build_item_acquisition_timeline(next_ep - 1)

        chain_link_section = self.load_chain_link_section(next_ep)
        world_state_summary = ""
        if self.ctx.world_state:
            try:
                world_state_summary = self.ctx.world_state.get_summary(max_chars=50000)
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] WorldState 요약 로드 실패: {e!s:.100}")

        recent_scene_keywords: list[dict[str, Any]] = []
        try:
            recent_scene_keywords = self._collect_recent_scene_keywords(
                db,
                next_ep,
                lookback=3,
            )
        except Exception as scene_keywords_err:
            logging.debug("[NC-2] 씬 키워드 수집 실패 (비치명): %s", scene_keywords_err)

        return Stage4EpisodeStatePayload(
            hud_report=hud_report,
            current_inventory=current_inventory,
            current_martial_arts=current_martial_arts,
            cumulative_bible=cumulative_bible,
            dead_npcs=dead_npcs,
            item_acquisition_timeline=item_acquisition_timeline,
            chain_link_section=chain_link_section,
            world_state_summary=world_state_summary,
            recent_scene_keywords=recent_scene_keywords,
        )

    def _build_episode_digest(self, *, prev_text: str, next_ep: int, chief_writer) -> str:
        episode_digest = ""
        if prev_text and hasattr(chief_writer, "_generate_episode_digest"):
            episode_digest = chief_writer._generate_episode_digest(prev_text, next_ep - 1)

        try:
            if hasattr(self.ctx, "sys") and self.ctx.sys and hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                from modules.core.genre_hud_manager import FinanceHUDManager

                if isinstance(self.ctx.sys.hud, FinanceHUDManager):
                    if self._fact_ledger_has_numeric_authority():
                        return episode_digest
                    hud_cap = self.ctx.sys.hud.pro_data.get("capital", "")
                    hud_total = self.ctx.sys.hud.pro_data.get("total_assets", "")
                    hud_parts = []
                    if hud_cap:
                        hud_parts.append(f"HUD 확정 자본: {hud_cap}")
                    if hud_total:
                        hud_parts.append(f"HUD 총자산: {hud_total}")
                    if hud_parts:
                        snapshot = "\n".join(f"- {part}" for part in hud_parts)
                        episode_digest = (
                            (episode_digest + f"\n{snapshot}")
                            if episode_digest
                            else f"[HUD 금융 스냅샷]\n{snapshot}"
                        )
        except Exception as hud_err:
            logging.warning("[SilentPass:V74] HUD 스냅샷 주입 실패: %s", hud_err)
        return episode_digest

    def _fact_ledger_has_numeric_authority(self) -> bool:
        fact_ledger = getattr(self.ctx, "fact_ledger", None)
        if fact_ledger is None:
            return False

        try:
            canonical_getter = getattr(fact_ledger, "get_canonical_summary", None)
            if callable(canonical_getter) and str(canonical_getter(max_chars=1200) or "").strip():
                return True
        except Exception:
            logging.debug("[Stage4ContextBuilder] canonical numeric authority probe failed", exc_info=True)

        try:
            numbers_getter = getattr(fact_ledger, "get_numbers", None)
            if callable(numbers_getter):
                numbers = numbers_getter()
                if isinstance(numbers, dict) and numbers:
                    return True
        except Exception:
            logging.debug("[Stage4ContextBuilder] numeric authority probe via get_numbers failed", exc_info=True)

        ledger = getattr(fact_ledger, "_ledger", None)
        if isinstance(ledger, dict):
            numbers = ledger.get("numbers", {})
            if isinstance(numbers, dict) and numbers:
                return True
        return False

    # ── [NC-2 GAP-1] 씬 유사도 분석 유틸 ──────────────────────────

    _SCENE_SPLIT_RE = re.compile(r"\n(?:#{1,3}\s+\uC52C\s*\d+|---+|\*\*\*+|\n{3,})")

    @classmethod
    def _split_scenes(cls, text: str) -> list[str]:
        """원고를 씬 단위로 분리. 구분자: # 씬 N, ---, ***, 빈 줄 3개+."""
        if not text:
            return []
        parts = cls._SCENE_SPLIT_RE.split(text)
        return [p.strip() for p in parts if p and len(p.strip()) > 20]

    @staticmethod
    def _scene_keywords(scene_text: str, max_keywords: int = 30) -> set[str]:
        """씬에서 장소/인물/핵심 동사 키워드 추출 (300자 사용)."""
        snippet = scene_text[:300]
        # 한글 2~6자 단어 추출 (조사 제거)
        words = re.findall(r"[\uac00-\ud7a3]{2,6}", snippet)
        # 흔한 조사/어미 제거
        stopwords = {
            "그리고",
            "하지만",
            "그래서",
            "그런데",
            "때문에",
            "하면서",
            "라고",
            "이라고",
            "했다",
            "있다",
            "없다",
            "되었다",
            "이었다",
            "것이다",
            "같다",
            "있었다",
            "않았다",
        }
        return {w for w in words[:max_keywords] if w not in stopwords}

    @classmethod
    def _collect_recent_scene_keywords(
        cls,
        db,
        next_ep: int,
        lookback: int = 3,
    ) -> list[dict]:
        """직전 N화 원고에서 씬별 키워드 목록 수집.

        Returns:
            [{"ep": int, "scenes": [set[str], ...]}, ...]
        """
        result: list[dict] = []
        for prev_ep in range(max(1, next_ep - lookback), next_ep):
            try:
                ms_row = db.get_manuscript(prev_ep)
                if not ms_row:
                    continue
                content = ms_row.get("content", "") or ms_row.get("manuscript", "") or ""
                if not content or len(content) < 100:
                    continue
                scenes = cls._split_scenes(content)
                scene_kws = [cls._scene_keywords(s) for s in scenes]
                if scene_kws:
                    result.append({"ep": prev_ep, "scenes": scene_kws})
            except Exception:
                continue
        return result

    @classmethod
    def compute_scene_similarity_advisory(
        cls,
        candidate_text: str,
        recent_scene_keywords: list[dict],
        threshold: float = 0.50,
    ) -> str:
        """후보 원고와 직전 화 씬의 키워드 자카드 유사도 → advisory 문자열.

        유사도 > threshold 씬 쌍이 2개 이상이면 advisory 반환, 아니면 빈 문자열.
        """
        if not candidate_text or not recent_scene_keywords:
            return ""

        cand_scenes = cls._split_scenes(candidate_text)
        cand_kws = [cls._scene_keywords(s) for s in cand_scenes]
        if not cand_kws:
            return ""

        similar_pairs: list[str] = []
        for entry in recent_scene_keywords:
            ep = entry.get("ep", "?")
            for prev_idx, prev_kw in enumerate(entry.get("scenes", [])):
                if not prev_kw:
                    continue
                for cand_idx, cand_kw in enumerate(cand_kws):
                    if not cand_kw:
                        continue
                    inter = prev_kw & cand_kw
                    union = prev_kw | cand_kw
                    sim = len(inter) / len(union) if union else 0.0
                    if sim > threshold:
                        similar_pairs.append(f"EP{ep} 씬{prev_idx + 1} ↔ 후보 씬{cand_idx + 1} (유사도 {sim:.0%})")

        if len(similar_pairs) >= 2:
            lines = ["[SceneSimilarity] 에피소드 간 씬 구조 중복 감지:"]
            lines.extend(f"  - {p}" for p in similar_pairs[:5])
            lines.append("  → 같은 장소·상황·인물 조합 반복 주의. Director 판정 필요.")
            return "\n".join(lines)

        return ""

    def build_mandatory_context(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        arc_tactical: str,
        prev_text: str,
        prev_ending: str,
        hud_report: str,
        writer_agent,
        anchor_sys,
        s4_genre_type: str,
        v50_modules_available: bool,
        blueprint: dict | None = None,
        pacing_analyzer=None,
    ) -> Stage4MandatoryContextPayload:
        """[4-R1-b] mandatory_context + writer prompt 조립을 분리 (동작 변화 없음)."""
        genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "")
        if not genre_name:
            genre_name = s4_genre_type or "unknown"
            logging.warning("[genre-guardrail] _assemble_mandatory_context: genre display name unresolved, using %r", genre_name)

        if writer_agent is None:
            return self._build_empty_mandatory_context_payload()

        return self._build_mandatory_context_payload(
            next_ep=next_ep,
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            prev_text=prev_text,
            hud_report=hud_report,
            anchor_sys=anchor_sys,
            genre_name=genre_name,
            blueprint=blueprint,
            s4_genre_type=s4_genre_type,
            v50_modules_available=v50_modules_available,
            pacing_analyzer=pacing_analyzer,
        )

    @staticmethod
    def _build_empty_mandatory_context_payload() -> Stage4MandatoryContextPayload:
        return Stage4ContextBuilder._build_mandatory_context_result_payload(
            reference_anchor_prompt="",
            mandatory_context="",
            anti_trope_prompt="",
            justification_prompt="",
            reflexion_prompt="",
        )

    def _build_mandatory_context_payload(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        arc_tactical: str,
        prev_ending: str,
        prev_text: str,
        hud_report: str,
        anchor_sys,
        genre_name: str,
        blueprint: dict | None,
        s4_genre_type: str,
        v50_modules_available: bool,
        pacing_analyzer=None,
    ) -> Stage4MandatoryContextPayload:
        reference_anchor_prompt = self._load_reference_anchor_prompt(
            anchor_sys=anchor_sys,
            next_ep=next_ep,
            arc_tactical=arc_tactical,
        )

        mandatory_context = self._load_base_mandatory_context(next_ep=next_ep)
        seed = self._build_mandatory_context_seed(
            next_ep=next_ep,
            arc_data=arc_data,
            s4_genre_type=s4_genre_type,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            blueprint=blueprint,
            mandatory_context=mandatory_context,
        )
        context_result = self._build_mandatory_context_retrieval_coverage(
            next_ep=next_ep,
            arc_data=arc_data,
            blueprint=blueprint,
            s4_genre_type=s4_genre_type,
            v50_modules_available=v50_modules_available,
            pacing_analyzer=pacing_analyzer,
            prev_text=prev_text,
            prev_ending=prev_ending,
            arc_tactical=arc_tactical,
            work_focus=seed["work_focus"],
            tier0_parts=seed["tier0_parts"],
            slot_summary=seed["slot_summary"],
        )
        prompt_injections = self._build_mandatory_prompt_injections(
            next_ep=next_ep,
            hud_report=hud_report,
            genre_name=genre_name,
            blueprint=blueprint,
            prev_text=prev_text,
        )

        return self._build_mandatory_context_result_payload(
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=context_result["mandatory_context"],
            anti_trope_prompt=prompt_injections["anti_trope_prompt"],
            justification_prompt=prompt_injections["justification_prompt"],
            reflexion_prompt=prompt_injections["reflexion_prompt"],
        )

    @staticmethod
    def _build_mandatory_context_result_payload(
        *,
        reference_anchor_prompt: str,
        mandatory_context: str,
        anti_trope_prompt: str,
        justification_prompt: str,
        reflexion_prompt: str,
    ) -> Stage4MandatoryContextPayload:
        return {
            "reference_anchor_prompt": reference_anchor_prompt,
            "mandatory_context": mandatory_context,
            "anti_trope_prompt": anti_trope_prompt,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
        }

    def _load_reference_anchor_prompt(
        self,
        *,
        anchor_sys,
        next_ep: int,
        arc_tactical: str,
    ) -> str:
        try:
            relevant_anchors = anchor_sys.get_relevant_anchors(
                current_ep_num=next_ep,
                arc_context=arc_tactical or "",
                n_anchors=5,
            )
            critical_anchors = anchor_sys.get_critical_anchors(
                current_ep_num=next_ep,
                anchor_types=["item", "injury", "power", "location"],
            )
            if relevant_anchors or critical_anchors:
                return anchor_sys.generate_reference_prompt(
                    relevant_anchors=relevant_anchors,
                    critical_anchors=critical_anchors,
                )
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ ReferenceAnchor 로드 실패 (비치명): {e}")
        return ""

    def _load_base_mandatory_context(self, *, next_ep: int) -> str:
        try:
            db = getattr(self.ctx.current_project, "db", None)
            bible = getattr(self.ctx.current_project, "master_bible", {})
            mandatory_context = _build_writer_mandatory_context(db, bible, next_ep)
            self._record_hud_anomaly_observation(ep_num=next_ep, db=db)
            return mandatory_context
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
            return "[경고] 필수 컨텍스트 로딩 실패 - 이전 에피소드 상태를 우선 참조하여 연속성을 유지하세요."

    def _build_mandatory_context_seed(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        s4_genre_type: str,
        arc_tactical: str,
        prev_ending: str,
        blueprint: dict | None,
        mandatory_context: str,
    ) -> Stage4MandatoryContextSeedPayload:
        cp_entities = self._resolve_mandatory_context_cp_entities(
            blueprint=blueprint,
            arc_data=arc_data,
        )

        work_focus: WorkRetrievalFocusPayload = self._resolve_work_retrieval_focus(
            stage="manuscript",
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            blueprint=blueprint,
            cp_entities=cp_entities,
            next_ep=next_ep,
        )
        slot_summary = self._build_work_identity_slot_summary(
            focus=work_focus,
            arc_data=arc_data,
            cp_entities=cp_entities,
            next_ep=next_ep,
        )
        chain_link_section = self.load_chain_link_section(next_ep)
        if chain_link_section:
            logging.info(f"[V68] 직전 화 연결고리 로드 완료 ({len(chain_link_section)}자)")
        tier0_parts = self._build_tier0_mandatory_sections(
            next_ep=next_ep,
            arc_data=arc_data,
            blueprint=blueprint,
            s4_genre_type=s4_genre_type,
            prev_ending=prev_ending,
            chain_link_section=chain_link_section,
            cp_entities=cp_entities,
            work_focus=work_focus,
            mandatory_context=mandatory_context,
        )
        return {
            "cp_entities": cp_entities,
            "work_focus": work_focus,
            "tier0_parts": tier0_parts,
            "slot_summary": slot_summary,
        }

    def _resolve_mandatory_context_cp_entities(
        self,
        *,
        blueprint: dict | None,
        arc_data: dict,
    ) -> dict:
        cp_entities = {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": ""}
        if not blueprint:
            return cp_entities

        try:
            return self._extract_blueprint_entities(blueprint, arc_data=arc_data)
        except Exception as cp_entity_err:
            logging.debug("[CP] blueprint entity 추출 실패 (비치명): %s", cp_entity_err)
            return cp_entities

    def _build_mandatory_context_retrieval_coverage(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        blueprint: dict | None,
        s4_genre_type: str,
        v50_modules_available: bool,
        pacing_analyzer,
        prev_text: str,
        prev_ending: str,
        arc_tactical: str,
        work_focus: WorkRetrievalFocusPayload,
        tier0_parts: list[str],
        slot_summary: str,
    ) -> Stage4RetrievalCoveragePayload:
        tier_aux: Stage4AuxiliarySectionsPayload = self.context_packets.build_tier12_auxiliary_sections(
            next_ep=next_ep,
            arc_data=arc_data,
            blueprint=blueprint,
            s4_genre_type=s4_genre_type,
            v50_modules_available=v50_modules_available,
            pacing_analyzer=pacing_analyzer,
            prev_text=prev_text,
            work_focus=work_focus,
            slot_summary=slot_summary,
        )
        tier1_parts = tier_aux["tier1_parts"]
        tier2_parts = tier_aux["tier2_parts"]

        retrieval_result: Stage4RetrievalContextPayload = self._collect_stage4_retrieval_context(
            next_ep=next_ep,
            arc_data=arc_data,
            prev_ending=prev_ending,
            arc_tactical=arc_tactical,
            blueprint=blueprint,
            s4_genre_type=s4_genre_type,
            work_focus=work_focus,
            tier1_parts=tier1_parts,
        )
        return self._compose_context_with_retrieval_coverage(
            next_ep=next_ep,
            work_focus=work_focus,
            retrieval_plan=retrieval_result["retrieval_plan"],
            tier0_parts=tier0_parts,
            tier1_parts=retrieval_result["tier1_parts"],
            sc_parts=retrieval_result["sc_parts"],
            tier2_parts=tier2_parts,
            slot_summary=slot_summary,
        )

    def _build_mandatory_prompt_injections(
        self,
        *,
        next_ep: int,
        hud_report: str,
        genre_name: str,
        blueprint: dict | None,
        prev_text: str,
    ) -> Stage4PromptInjectionsPayload:
        base_prompts = self._build_mandatory_prompt_bases(
            hud_report=hud_report,
            genre_name=genre_name,
        )
        reflexion_prompt = ""

        justification_prompt = self._append_writer_guidance_prompt(
            justification_prompt=base_prompts["justification_prompt"],
            blueprint=blueprint,
            prev_text=prev_text,
        )
        reflexion_prompt = self._load_reflexion_prompt(next_ep=next_ep)

        return self._build_mandatory_prompt_payload(
            anti_trope_prompt=base_prompts["anti_trope_prompt"],
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
        )

    @staticmethod
    def _build_mandatory_prompt_payload(
        *,
        anti_trope_prompt: str,
        justification_prompt: str,
        reflexion_prompt: str,
    ) -> Stage4PromptInjectionsPayload:
        return {
            "anti_trope_prompt": anti_trope_prompt,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
        }

    def _build_mandatory_prompt_bases(
        self,
        *,
        hud_report: str,
        genre_name: str,
    ) -> Stage4PromptBasesPayload:
        anti_trope_prompt = ""
        justification_prompt = ""

        try:
            anti_trope_prompt = _build_anti_trope(genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Anti-Trope 실패 (비치명): {e}")

        try:
            justification_prompt = _build_justification(hud_report, genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Justification 실패 (비치명): {e}")

        return Stage4PromptBasesPayload(
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
        )

    def _append_writer_guidance_prompt(
        self,
        *,
        justification_prompt: str,
        blueprint: dict | None,
        prev_text: str,
    ) -> str:
        writer_guidance_callback = None
        try:
            inspect.getattr_static(self.ctx, "generate_writer_guidance_v60_8")
        except AttributeError:
            writer_guidance_callback = None
        else:
            writer_guidance_callback = getattr(self.ctx, "generate_writer_guidance_v60_8", None)

        if not callable(writer_guidance_callback):
            return justification_prompt

        try:
            writer_guidance = writer_guidance_callback(
                blueprint=blueprint or {},
                prev_manuscript=prev_text or "",
            )
            if not writer_guidance:
                return justification_prompt
            guidance_block = f"[Writer Guidance]\n{writer_guidance}"
            return (
                f"{justification_prompt}\n\n{guidance_block}".strip()
                if justification_prompt
                else guidance_block
            )
        except Exception as writer_guidance_err:
            self.ctx.ui.log(f"   ⚠️ Writer guidance 실패 (비치명): {writer_guidance_err}")
            return justification_prompt

    def _load_reflexion_prompt(self, *, next_ep: int) -> str:
        if next_ep < 20:
            return ""
        try:
            from modules.core.reflexion_manager import ReflexionManager

            reflexion = ReflexionManager(self.ctx.current_project)
            return reflexion.get_prompt_injection(min_frequency=2)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Reflexion 실패 (비치명): {e}")
            return ""

    def build_round_context(
        self,
        *,
        ep_ctx: dict,
        ctx_prompts: dict,
        chief_writer,
        manuscript_validator,
        consistency_validator,
        blocking_validator,
        continuity_validator,
        next_ep: int,
        blueprint: dict,
        arc_data: dict,
        purism_prompt: str,
        genre_name: str,
        npc_equipment_summary: str,
        effective_anti_trope: str,
        intro_dna: str,
        story_context: str,
        style_guide: str,
        mandatory_context: str,
        preflight_advisory: str = "",
        reference_excerpt: str = "",
    ):
        """[4-R1-e-2] Build round context dict from episode context and prompts."""
        from modules.core.stage4_types import _RoundContext

        return _RoundContext(
            chief_writer=chief_writer,
            manuscript_validator=manuscript_validator,
            consistency_validator=consistency_validator,
            blocking_validator=blocking_validator,
            continuity_validator=continuity_validator,
            next_ep=next_ep,
            blueprint=blueprint,
            arc_data=arc_data,
            arc_pos=ep_ctx["arc_pos"],
            total_ep_in_arc=ep_ctx["total_ep_in_arc"],
            arc_tactical=ep_ctx["arc_tactical"],
            prev_text=ep_ctx["prev_text"],
            prev_ending=ep_ctx["prev_ending"],
            prev_manuscripts_text=ep_ctx["prev_manuscripts_text"],
            episode_digest=ep_ctx["episode_digest"],
            hud_report=ep_ctx["hud_report"],
            current_inventory=ep_ctx["current_inventory"],
            current_martial_arts=ep_ctx["current_martial_arts"],
            dead_npcs=ep_ctx["dead_npcs"],
            item_acquisition_timeline=ep_ctx["item_acquisition_timeline"],
            chain_link_section=ep_ctx["chain_link_section"],
            world_state_summary=ep_ctx["world_state_summary"],
            purism_prompt=purism_prompt,
            genre_name=genre_name,
            npc_equipment_summary=npc_equipment_summary,
            effective_anti_trope=effective_anti_trope,
            intro_dna=intro_dna,
            story_context=story_context,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            reference_anchor_prompt=ctx_prompts["reference_anchor_prompt"],
            mandatory_context=mandatory_context,
            justification_prompt=ctx_prompts["justification_prompt"],
            reflexion_prompt=ctx_prompts["reflexion_prompt"],
            preflight_advisory=preflight_advisory,
            recent_scene_keywords=ep_ctx.get("recent_scene_keywords", []),  # [NC-2 GAP-1]
        )
