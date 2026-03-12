"""
[B-1-2] Stage4 Context Builder — 에피소드 컨텍스트 수집 및 프롬프트 조립.
"""

import json
import logging
import re
from typing import TYPE_CHECKING

from modules.core.constants import Stage2Limits, VolumeSettings
from modules.core.context_advisor import RetrievalSources
from modules.core.context_compression import ContextCompressor
from modules.core.semantic_query_broker import SemanticQueryBroker
from modules.core.tactical_utils import extract_episode_tactical
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

if TYPE_CHECKING:
    from modules.core.context_advisor import RetrievalPlan


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
            "이름 없이 역할만으로 활용하세요. 반드시 사용할 필요는 없습니다.\n"
            + "\n".join(hints)
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
            for name in (ws_state.get(pool) or {}):
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
        for name in (ws_state.get("active_items") or {}):
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

    def _build_continuity_packet(self, entities: dict[str, list[str] | str]) -> str:
        """이번 화 관련 엔티티의 상세 이력을 지목 조회하여 패킷으로 조립한다."""
        if not entities:
            return ""

        parts = ["=== [Continuity Packet] 이번 화 필수 기억 ==="]
        budget = 7000
        used = 0

        project = getattr(self.ctx, "current_project", None)
        db = getattr(project, "db", None)
        world_state = getattr(self.ctx, "world_state", None)
        ws_state = getattr(world_state, "_state", {}) if world_state else {}
        fact_ledger = getattr(self.ctx, "fact_ledger", None)
        ledger = getattr(fact_ledger, "_ledger", {}) if fact_ledger else {}

        for npc_name in (entities.get("npcs") or [])[:10]:
            npc_block: list[str] = []

            for pool in ("alive_npcs", "dead_npcs"):
                info = (ws_state.get(pool) or {}).get(npc_name)
                if info and isinstance(info, dict):
                    desc = ", ".join(
                        f"{key}={value}"
                        for key, value in info.items()
                        if value and key != "name"
                    )
                    if desc:
                        npc_block.append(f"  상태: {desc[:200]}")
                    if pool == "dead_npcs":
                        npc_block.append("  ⚠️ 사망 — 행동/대사 등장 금지 (회상/언급만 허용)")

            char_facts = (ledger.get("characters", {}) or {}).get(npc_name, {})
            if isinstance(char_facts, dict):
                history = char_facts.get("history", [])
                for entry in history[-5:]:
                    if isinstance(entry, str):
                        npc_block.append(f"  [이력] {entry[:100]}")

            if db and hasattr(db, "get_npc_history"):
                try:
                    history_rows = db.get_npc_history(npc_name, limit=3)
                    for row in history_rows or []:
                        if isinstance(row, dict):
                            reason = str(row.get("reason", "") or "")
                            reason_str = f" ({reason[:30]})" if reason else ""
                            npc_block.append(
                                f"  [변경 {row.get('episode_no', '?')}화] "
                                f"{row.get('field_name', '')}: {str(row.get('old_value', ''))[:30]} → "
                                f"{str(row.get('new_value', ''))[:30]}{reason_str}"
                            )
                except Exception as history_err:
                    logging.debug("[CP] npc_history 조회 실패: %s", history_err)

            if npc_block:
                section = f"• {npc_name}\n" + "\n".join(npc_block)
                if used + len(section) > budget:
                    break
                parts.append(section)
                used += len(section)

        for plot_name in (entities.get("plots") or [])[:5]:
            plot_line = f"• 진행 중 플롯: {plot_name}"
            if used + len(plot_line) > budget:
                break
            parts.append(plot_line)
            used += len(plot_line)

        item_names = entities.get("items") or []
        if item_names:
            item_line = "• 관련 아이템: " + ", ".join(item_names[:10])
            if used + len(item_line) <= budget:
                parts.append(item_line)
                used += len(item_line)

        location_names = entities.get("locations") or []
        if location_names:
            location_line = "• 현재 위치: " + ", ".join(location_names[:3])
            if used + len(location_line) <= budget:
                parts.append(location_line)
                used += len(location_line)

        if db and hasattr(db, "get_relationship_history") and hasattr(db, "get_npc_relationship_edges"):
            rel_lines: list[str] = []
            seen_pairs: set[tuple[str, str]] = set()
            blueprint_npcs = [str(name) for name in (entities.get("npcs") or [])[:10]]
            for npc_name in blueprint_npcs:
                try:
                    edges = db.get_npc_relationship_edges(npc_name)
                    if not isinstance(edges, list):
                        continue
                    for edge in edges[:5]:
                        if not isinstance(edge, dict):
                            continue
                        n1 = str(edge.get("npc1", "") or "").strip()
                        n2 = str(edge.get("npc2", "") or "").strip()
                        pair_key = tuple(sorted([n1, n2]))
                        if not n1 or not n2 or pair_key in seen_pairs:
                            continue
                        seen_pairs.add(pair_key)

                        other = n2 if n1 == npc_name else n1
                        if other not in blueprint_npcs:
                            continue

                        rel_hist = db.get_relationship_history(n1, n2, limit=5)
                        if not isinstance(rel_hist, list) or not rel_hist:
                            cur_rel = edge.get("relation", "?")
                            rel_lines.append(
                                f"  {n1} ↔ {n2}: {cur_rel} (ep{edge.get('since_ep', '?')}~)"
                            )
                            continue

                        stages: list[str] = []
                        eps: list[str] = []
                        for hist in rel_hist:
                            if not isinstance(hist, dict):
                                continue
                            new_rel = str(hist.get("new_relation", "") or "").strip()
                            change_ep = hist.get("change_ep", "?")
                            if new_rel:
                                stages.append(new_rel)
                                eps.append(str(change_ep))
                        if stages:
                            trajectory = "→".join(stages)
                            ep_flow = "→".join(f"ep{ep}" for ep in eps)
                            rel_lines.append(f"  {n1} ↔ {n2}: {trajectory} ({ep_flow})")
                except Exception as rel_err:
                    logging.debug("[CP] 관계 궤적 조회 실패: %s", rel_err)

            if rel_lines:
                rel_section = "• 관계 변천사\n" + "\n".join(rel_lines[:8])
                if used + len(rel_section) <= budget:
                    parts.append(rel_section)
                    used += len(rel_section)

        full_text = str(entities.get("_full_text", "") or "")
        if full_text and fact_ledger:
            nums = ledger.get("numbers", {})
            if isinstance(nums, dict) and nums:
                num_lines: list[str] = []
                for num_key, num_info in nums.items():
                    if not isinstance(num_info, dict):
                        continue
                    key_text = str(num_key)
                    if key_text not in full_text:
                        continue

                    cur_val = num_info.get("value", "?")
                    unit = num_info.get("unit", "")
                    est_val = num_info.get("established_value", "")
                    est_ep = num_info.get("established_ep", "?")
                    last_ep = num_info.get("last_ep", "?")
                    unit_str = f" {unit}" if unit else ""

                    if est_val != "" and str(est_val) != str(cur_val):
                        num_lines.append(
                            f"  {key_text}: {est_val}{unit_str}(ep{est_ep}) → {cur_val}{unit_str}(ep{last_ep})"
                        )
                    else:
                        num_lines.append(f"  {key_text}: {cur_val}{unit_str} (ep{last_ep} 기준)")

                    history = num_info.get("history", [])
                    if isinstance(history, list):
                        for history_entry in history[-3:]:
                            if isinstance(history_entry, str):
                                num_lines.append(f"    └ {history_entry[:80]}")

                if num_lines:
                    num_section = "• 수치 변화 이력\n" + "\n".join(num_lines[:15])
                    if used + len(num_section) <= budget:
                        parts.append(num_section)
                        used += len(num_section)

        canonical_facts_section = _build_canonical_facts_section(db, full_text)
        if canonical_facts_section and used + len(canonical_facts_section) <= budget:
            parts.append(canonical_facts_section)
            used += len(canonical_facts_section)

        if len(parts) == 1:
            return ""

        result = "\n".join(parts)
        return result[:budget]

    @staticmethod
    def _trim_summary_value(value, max_chars: int = 60) -> str:
        text = str(value or "").strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1] + "…"

    @staticmethod
    def _tokenize_focus_terms(value: str) -> set[str]:
        text = str(value or "").strip().lower()
        if not text:
            return set()
        tokens: set[str] = set()
        for token in re.split(r"[\s,|/:;()\[\]{}<>\"'`~!@#$%^&*+=?!.…-]+", text):
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
        max_chars: int = 4000,
    ) -> str:
        parts: list[str] = []
        if arc_tactical:
            parts.append(str(arc_tactical))
        if prev_ending:
            parts.append(str(prev_ending))
        if isinstance(arc_data, dict):
            for key in ("constraint_summary", "goal", "core_conflict", "hook"):
                value = str(arc_data.get(key, "") or "").strip()
                if value:
                    parts.append(value)
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
            return combined[:max_chars]
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
    ) -> dict[str, object]:
        guard = getattr(getattr(self.ctx, "sys", None), "guard", None)
        if not guard or not hasattr(guard, "select_retrieval_focus"):
            return {}

        focus_text = self._compose_work_focus_text(
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            blueprint=blueprint,
            cp_entities=cp_entities,
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
        focus: dict[str, object],
        arc_data: dict | None,
        cp_entities: dict[str, list[str] | str] | None,
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
                rendered_profiles.append(
                    f"{name}" + (f"(fields={', '.join(fields[:4])})" if fields else "")
                )
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
            constraint_summary = self._trim_summary_value(arc_data.get("constraint_summary", ""), 160)
            if constraint_summary:
                lines.append(f"- 현재 갈등축: {constraint_summary}")

        try:
            protagonist_name = self._resolve_protagonist_name()
            focus_text = " ".join(
                [
                    ", ".join(tracking_slots),
                    ", ".join(scene_engines),
                    " ".join(str(profile.get("purpose", "") or "") for profile in registry_profiles),
                    str((arc_data or {}).get("constraint_summary", "") or ""),
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
            result = result[: max_chars - 20] + "\n... (슬롯 요약 절삭)"
        return result

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

    def _build_condensed_world_state_summary(
        self,
        entities: dict[str, list[str] | str],
        *,
        max_chars: int = 50000,
    ) -> str:
        """CP가 이미 상세 주입한 엔티티는 간략 표기만 남긴 world_state 요약."""
        world_state = getattr(self.ctx, "world_state", None)
        if not world_state:
            return ""

        state = getattr(world_state, "_state", {}) if hasattr(world_state, "_state") else {}
        if not isinstance(state, dict) or not state:
            try:
                return world_state.get_summary(max_chars=max_chars)
            except Exception:
                return ""

        cp_npcs = {str(name).strip() for name in (entities.get("npcs") or []) if str(name).strip()}
        cp_items = {str(name).strip() for name in (entities.get("items") or []) if str(name).strip()}
        cp_plots = {str(name).strip() for name in (entities.get("plots") or []) if str(name).strip()}
        cp_locations = {str(name).strip() for name in (entities.get("locations") or []) if str(name).strip()}

        if not any([cp_npcs, cp_items, cp_plots, cp_locations]):
            try:
                return world_state.get_summary(max_chars=max_chars)
            except Exception:
                return ""

        parts: list[str] = []
        last_ep = state.get("last_updated_ep", 0)
        if last_ep:
            parts.append(f"=== 세계 상태 (제{last_ep}화 기준) ===")

        protagonist = state.get("protagonist", {})
        if isinstance(protagonist, dict):
            prot_lines = []
            if protagonist.get("name"):
                prot_lines.append(f"이름: {protagonist['name']}")
            if protagonist.get("location"):
                prot_lines.append(f"위치: {self._trim_summary_value(protagonist['location'])}")
            if protagonist.get("assets"):
                prot_lines.append(f"자산: {self._trim_summary_value(protagonist['assets'], 120)}")
            if protagonist.get("injuries") and protagonist.get("injuries") != "정상":
                prot_lines.append(f"부상: {self._trim_summary_value(protagonist['injuries'])}")
            if prot_lines:
                parts.append("[주인공]\n" + "\n".join(prot_lines))

        motivations = [
            mot
            for mot in (state.get("motivations") or [])
            if isinstance(mot, dict) and mot.get("status") == "active" and mot.get("text")
        ]
        if motivations:
            parts.append(
                "[주인공 핵심 동기]\n"
                + "\n".join(
                    f"- {self._trim_summary_value(mot.get('text'), 80)}"
                    + (f" (제{mot.get('since_ep')}화~)" if mot.get("since_ep") else "")
                    for mot in motivations[:6]
                )
            )

        promises = [
            promise
            for promise in (state.get("promises") or [])
            if isinstance(promise, dict)
            and promise.get("text")
            and promise.get("status") in ("pending", None, "")
        ]
        if promises:
            promise_lines = []
            for promise in promises[:6]:
                promiser = str(promise.get("promiser", "") or "").strip()
                promisee = str(promise.get("promisee", "") or "").strip()
                parties = "→".join(x for x in [promiser, promisee] if x)
                text = self._trim_summary_value(promise.get("text"), 80)
                label = f"{parties}: {text}" if parties else text
                if promise.get("since_ep"):
                    label += f" (제{promise.get('since_ep')}화~)"
                promise_lines.append(f"- {label}")
            if promise_lines:
                parts.append("[서약/약속]\n" + "\n".join(promise_lines))

        cumulative_elapsed = state.get("cumulative_elapsed", {})
        if isinstance(cumulative_elapsed, dict) and cumulative_elapsed.get("total_days"):
            parts.append(f"[누적 경과] 총 {cumulative_elapsed.get('total_days')}일")

        alive = state.get("alive_npcs", {})
        if isinstance(alive, dict) and alive:
            remaining_alive = [(name, info) for name, info in alive.items() if str(name).strip() not in cp_npcs]
            if remaining_alive:
                lines = []
                for name, info in remaining_alive[:12]:
                    desc_parts = []
                    if isinstance(info, dict):
                        if info.get("role"):
                            desc_parts.append(str(info["role"]))
                        if info.get("relation"):
                            desc_parts.append(f"관계={info['relation']}")
                        if info.get("location"):
                            desc_parts.append(f"위치={self._trim_summary_value(info['location'], 24)}")
                    desc = " / ".join(desc_parts)
                    lines.append(f"- {name}" + (f": {desc}" if desc else ""))
                parts.append(f"[생존 NPC - CP 비포함 {len(lines)}명]\n" + "\n".join(lines))
            if cp_npcs:
                parts.append("[CP 상세 참조]\n- 핵심 NPC 상세는 Continuity Packet 참조")

        dead = state.get("dead_npcs", {})
        if isinstance(dead, dict) and dead:
            remaining_dead = [(name, info) for name, info in dead.items() if str(name).strip() not in cp_npcs]
            if remaining_dead:
                lines = []
                for name, info in remaining_dead[:8]:
                    if isinstance(info, dict):
                        lines.append(f"- {name} (제{info.get('ep', '?')}화, {self._trim_summary_value(info.get('cause'), 24)})")
                    else:
                        lines.append(f"- {name}")
                parts.append(f"[사망 NPC - CP 비포함 {len(lines)}명]\n" + "\n".join(lines))

        relationships = state.get("relationships", {})
        if isinstance(relationships, dict) and relationships:
            rel_lines = []
            for npc, relation in list(relationships.items())[:12]:
                if str(npc).strip() in cp_npcs:
                    continue
                rel_lines.append(f"- {npc}: {self._trim_summary_value(relation, 40)}")
            if rel_lines:
                parts.append("[주요 관계 - CP 비포함]\n" + "\n".join(rel_lines))

        active_items = state.get("active_items", {})
        if isinstance(active_items, dict) and active_items:
            item_lines = [f"- {name}" for name, info in list(active_items.items())[:20] if str(name).strip() not in cp_items]
            if item_lines:
                parts.append("[보유 아이템 - CP 비포함]\n" + "\n".join(item_lines[:12]))
            if cp_items:
                parts.append("[CP 상세 참조]\n- 관련 아이템 상세는 Continuity Packet 참조")

        active_plots = state.get("active_plots", [])
        if isinstance(active_plots, list) and active_plots:
            plot_lines = []
            for plot in active_plots[-10:]:
                plot_name = plot.get("plot", "") if isinstance(plot, dict) else str(plot)
                if str(plot_name).strip() in cp_plots:
                    continue
                since_ep = plot.get("since_ep", "?") if isinstance(plot, dict) else "?"
                plot_lines.append(f"- {self._trim_summary_value(plot_name, 60)} (제{since_ep}화~)")
            if plot_lines:
                parts.append("[진행 중 플롯 - CP 비포함]\n" + "\n".join(plot_lines[:8]))
            if cp_plots:
                parts.append("[CP 상세 참조]\n- 이번 화 핵심 플롯 상세는 Continuity Packet 참조")

        if cp_locations:
            parts.append("[CP 상세 참조]\n- 이번 화 위치 맥락 상세는 Continuity Packet 참조")

        result = "\n\n".join(part for part in parts if part)
        if len(result) > max_chars:
            result = result[: max_chars - 20] + "\n... (세계 상태 절삭)"
        return result

    def _build_condensed_fact_ledger_summary(
        self,
        entities: dict[str, list[str] | str],
        *,
        max_chars: int = 25000,
    ) -> str:
        """CP가 이미 상세 주입한 인물/아이템/수치는 압축한 FactLedger 요약."""
        fact_ledger = getattr(self.ctx, "fact_ledger", None)
        if not fact_ledger:
            return ""

        ledger = getattr(fact_ledger, "_ledger", {}) if hasattr(fact_ledger, "_ledger") else {}
        if not isinstance(ledger, dict) or not ledger:
            try:
                return fact_ledger.to_summary(max_chars=max_chars)
            except Exception:
                return ""

        cp_npcs = {str(name).strip() for name in (entities.get("npcs") or []) if str(name).strip()}
        cp_items = {str(name).strip() for name in (entities.get("items") or []) if str(name).strip()}
        full_text = str(entities.get("_full_text", "") or "")
        if not any([cp_npcs, cp_items, full_text]):
            try:
                return fact_ledger.to_summary(max_chars=max_chars)
            except Exception:
                return ""

        parts = []
        last_ep = ledger.get("last_updated_ep", 0)
        if last_ep:
            parts.append(f"=== 팩트 원장 (제{last_ep}화 기준) ===")

        characters = ledger.get("characters", {})
        if isinstance(characters, dict) and characters:
            alive_lines = []
            for name, info in list(characters.items())[:40]:
                if str(name).strip() in cp_npcs or not isinstance(info, dict) or info.get("status") != "alive":
                    continue
                role = self._trim_summary_value(info.get("role", "?"), 24)
                relation = self._trim_summary_value(info.get("relationship", ""), 24)
                rel_str = f", 관계: {relation}" if relation else ""
                alive_lines.append(f"  - {name} ({role}{rel_str}, ep{info.get('established_ep', '?')}~)")
            if alive_lines:
                parts.append("[생존 인물 - CP 비포함]\n" + "\n".join(alive_lines[:12]))
            if cp_npcs:
                parts.append("[CP 상세 참조]\n- 핵심 인물 팩트 이력은 Continuity Packet 참조")

        items = ledger.get("items", {})
        if isinstance(items, dict) and items:
            item_lines = []
            for name, info in list(items.items())[:30]:
                if str(name).strip() in cp_items or not isinstance(info, dict):
                    continue
                if info.get("status") in ("분실", "파괴", "소모"):
                    continue
                owner = self._trim_summary_value(info.get("owner", ""), 20)
                owner_str = f", 소유: {owner}" if owner else ""
                item_lines.append(f"  - {name} ({info.get('status', '보유')}{owner_str})")
            if item_lines:
                parts.append("[보유 아이템/무공 - CP 비포함]\n" + "\n".join(item_lines[:10]))
            if cp_items:
                parts.append("[CP 상세 참조]\n- 관련 아이템 상세는 Continuity Packet 참조")

        numbers = ledger.get("numbers", {})
        if isinstance(numbers, dict) and numbers:
            num_lines = []
            for key, info in list(numbers.items())[:30]:
                if not isinstance(info, dict):
                    continue
                if full_text and str(key) in full_text:
                    continue
                unit = str(info.get("unit", "") or "").strip()
                unit_str = f" {unit}" if unit else ""
                num_lines.append(f"  - {key}: {info.get('value', '?')}{unit_str} (ep{info.get('last_ep', '?')} 기준)")
            if num_lines:
                parts.append("[주요 수치 - CP 비포함]\n" + "\n".join(num_lines[:10]))
            if full_text:
                parts.append("[CP 상세 참조]\n- 이번 화 관련 수치 변화 이력은 Continuity Packet 참조")

        result = "\n\n".join(part for part in parts if part)
        if len(result) > max_chars:
            result = result[: max_chars - 18] + "\n... (팩트 원장 절삭)"
        return result

    def _execute_retrieval_plan(self, plan: "RetrievalPlan", arc_no: int | None = None) -> list[str]:
        """Execute retrieval plan slots and return context sections."""
        memory = getattr(self.ctx, "memory", None)
        if not memory or not plan or not getattr(plan, "slots", None):
            return []

        sections: list[str] = []
        compressor = ContextCompressor()
        max_results = int(_threshold("context.vector_max_results_s4", 20))
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
                    _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
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
                            logging.warning("[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
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
                excerpts.append(f"[EP {ep_no} 원고 발췌]\n{content[:800]}")
        combined = "\n\n".join(excerpts)
        return combined[:max_chars]

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
            total_budget_chars = int(_threshold("smart_retrieval.stage4_total_budget", 50000))
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
        logging.info(f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )

        if report["used_chars"] <= report["total_budget_chars"]:
            return sections

        # [S4-P1-6] 압축 대상 목록을 루프 전 1회 캐시하여 O(n^2) → O(n) 개선
        compression_targets = tracker.get_compression_targets()
        compressor = ContextCompressor()
        protected_prefix = "[작품 추적 슬롯 요약]"

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

        protected_indices = [idx for idx in target_indices if sections[idx].startswith(protected_prefix)]
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

        # 1) 일반 섹션을 먼저 줄여 작품 슬롯 요약이 가능한 한 오래 살아남게 한다.
        _trim_indices(regular_indices, label="[SC:TRIM]", min_chars=300, ratio=0.7, max_rounds=2)
        # 2) 그래도 넘치면 작품 추적 슬롯만 완만하게 줄인다.
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
        logging.info(f"[SC] Context budget: {report['used_chars']}/{report['total_budget_chars']} ({report['usage_pct']}%)"
        )
        return sections

    def _compose_mandatory_context_with_headroom(self, sc_parts: list[str], mc_parts: list[str]) -> str:
        """Compose SC + mandatory context while preserving headroom against final tail-trim."""
        sc_header = "\n\n".join(sc_parts) if sc_parts else ""
        mc_body = "\n\n".join(mc_parts)
        limit = int(_threshold("context.mandatory_context_max", 80000))
        headroom = 0
        if sc_header and limit > 0:
            headroom = min(20000, max(500, limit // 20))
            headroom = min(headroom, max(0, limit // 5))
            available_for_mc = max(0, limit - len(sc_header) - headroom - 2)
            if available_for_mc > 0 and len(mc_body) > available_for_mc and mc_parts:
                trimmed_parts = self._apply_context_budget(list(mc_parts), available_for_mc)
                mc_body = "\n\n".join(trimmed_parts)
                logging.info(
                    "[S4:CTX] rebalanced mc_body against SC headroom (sc=%d, mc=%d, limit=%d, headroom=%d)",
                    len(sc_header),
                    len(mc_body),
                    limit,
                    headroom,
                )

        total_len = len(sc_header) + len(mc_body) + (2 if sc_header and mc_body else 0)
        if limit > 0 and total_len > limit and mc_body:
            compressor = ContextCompressor()
            mc_budget = max(300, limit - len(sc_header) - (2 if sc_header else 0))
            if len(mc_body) > mc_budget:
                original_len = len(mc_body)
                mc_body = compressor._smart_trim(mc_body, mc_budget)
                logging.info("[S4:CTX] final mc_body trim %d→%d (limit=%d)", original_len, len(mc_body), limit)

        total_len = len(sc_header) + len(mc_body) + (2 if sc_header and mc_body else 0)
        if limit > 0 and total_len > limit and sc_header:
            compressor = ContextCompressor()
            sc_budget = max(300, limit - len(mc_body) - (2 if mc_body else 0))
            if len(sc_header) > sc_budget:
                original_len = len(sc_header)
                sc_header = compressor._smart_trim(sc_header, sc_budget)
                logging.info("[S4:CTX] final sc_header trim %d→%d (limit=%d)", original_len, len(sc_header), limit)
                total_len = len(sc_header) + len(mc_body) + (2 if sc_header and mc_body else 0)

        logging.info(
            "[S4:CTX] compose pre-final sc=%d mc=%d total=%d limit=%d headroom=%d",
            len(sc_header),
            len(mc_body),
            total_len,
            limit,
            headroom,
        )

        self.ctx._stage4_context_budget_meta = {
            "sc_chars": len(sc_header),
            "mc_chars": len(mc_body),
            "total_chars": total_len,
            "limit_chars": limit,
            "headroom_chars": headroom,
        }
        mandatory_context = (sc_header + "\n\n" + mc_body).strip() if sc_header else mc_body
        if limit > 0 and len(mandatory_context) > limit:
            compressor = ContextCompressor()
            original_len = len(mandatory_context)
            mandatory_context = compressor._smart_trim(mandatory_context, limit)
            self.ctx._stage4_context_budget_meta["total_chars"] = len(mandatory_context)
            logging.info("[S4:CTX] final combined trim %d→%d (limit=%d)", original_len, len(mandatory_context), limit)
        return mandatory_context

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
            _cl_data = _cl_raw
            _cl_parts = ["### [V68] 직전 화 연결고리 - 반드시 이어받을 것"]
            if _cl_data.get("cliffhanger"):
                _cl_parts.append(f"- 진행 중 상황: {_cl_data['cliffhanger']}")
            if _cl_data.get("pending_actions"):
                actions = _cl_data["pending_actions"]
                if isinstance(actions, list):
                    _cl_parts.append(f"- 해야 할 행동: {', '.join(str(a) for a in actions)}")
                else:
                    _cl_parts.append(f"- 해야 할 행동: {actions}")
            if _cl_data.get("emotional_state"):
                _cl_parts.append(f"- 감정 상태: {_cl_data['emotional_state']}")
            if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
                _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
            if _cl_data.get("location"):
                _cl_parts.append(f"- 현재 위치: {_cl_data['location']}")
            if _cl_data.get("time_marker"):
                _cl_parts.append(f"- 작중 시간: {_cl_data['time_marker']}")
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
            _excerpt_max = _threshold("context.lookback_excerpt_chars", 500)
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
            _total_max = _threshold("context.lookback_total_chars", 4000)
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

    def prepare_episode_context(self, next_ep: int, arc_data: dict, chief_writer) -> dict:
        """에피소드별 컨텍스트 데이터 수집 (Arc 메타 + 이전 원고 + HUD + 연결고리)."""
        arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1
        total_ep_in_arc = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):  # [V70] dict 타입 방어
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)
        arc_tactical = str(arc_tactical) if arc_tactical else ""

        # 직전 화 원고
        prev_ms_data = self.ctx.current_project.db.get_manuscript(next_ep - 1)
        prev_text = (prev_ms_data.get("content") or "") if prev_ms_data else ""  # [V70] NULL content 방어
        prev_ending = prev_text[-2500:] if prev_text else ""  # [1M-CTX: 500→2500] CW와 동일 수준

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
                if hasattr(_db, "_lock"):
                    with _db._lock:
                        _cur = _db.conn.cursor()
                        try:
                            _cur.execute(
                                "SELECT ep_num, summary FROM episode_meta "
                                "WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num ASC",
                                (_tier2_start, _tier2_end),
                            )
                            _rows = _cur.fetchall()
                        finally:
                            _cur.close()
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
                        _tier2_parts.append(f"[EP {_ep_no} summary] {_summary[:5000]}")  # [Phase3-A: 800→5000]
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
                        _tier3_parts.append(f"[Arc {_arc_no} summary] {_sum_text[:8000]}")  # [Phase3-A: 1.5K→8K]
                except Exception:
                    continue

            if _tier3_parts:
                _prev_manuscripts_parts.insert(
                    0,
                    "-- Tier3 arc summaries (older than 60 episodes) --\n" + "\n".join(_tier3_parts),
                )

        _prev_manuscripts_text = "\n\n---\n\n".join(_prev_manuscripts_parts) if _prev_manuscripts_parts else ""
        if _prev_manuscripts_parts:
            logging.info("[Tier4-12] hybrid lookback ready: parts=%d chars=%d",
                len(_prev_manuscripts_parts),
                len(_prev_manuscripts_text),
            )

        # [LongTerm] 60화 이상 시 장기 설정 앵커 주입 (세계관 법칙 + NPC origin)
        if next_ep >= 60:
            try:
                _ws = getattr(self.ctx, "world_state", None)
                if _ws and hasattr(_ws, "get_long_term_anchor"):
                    _lt_anchor = _ws.get_long_term_anchor(current_ep=next_ep)
                    if _lt_anchor:
                        _prev_manuscripts_text = (
                            _lt_anchor + "\n\n---\n\n" + _prev_manuscripts_text
                            if _prev_manuscripts_text
                            else _lt_anchor
                        )
                        logging.info("[LongTerm] 장기 설정 앵커 주입 (ep%d, %d자)", next_ep, len(_lt_anchor))
            except Exception as _lt_err:
                logging.debug("[LongTerm] 장기 설정 앵커 주입 실패 (비차단): %s", _lt_err)

        # [V62.6] 에피소드 상태 다이제스트
        _episode_digest = ""
        if prev_text and hasattr(chief_writer, "_generate_episode_digest"):
            _episode_digest = chief_writer._generate_episode_digest(prev_text, next_ep - 1)

        # [V74] HUD 자본금 스냅샷 (투자물 전용)
        try:
            if hasattr(self.ctx, "sys") and self.ctx.sys and hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
                from modules.core.genre_hud_manager import FinanceHUDManager

                if isinstance(self.ctx.sys.hud, FinanceHUDManager):
                    _hud_cap = self.ctx.sys.hud.pro_data.get("capital", "")
                    _hud_total = self.ctx.sys.hud.pro_data.get("total_assets", "")
                    _hud_parts = []
                    if _hud_cap:
                        _hud_parts.append(f"HUD 확정 자본: {_hud_cap}")
                    if _hud_total:
                        _hud_parts.append(f"HUD 총자산: {_hud_total}")
                    if _hud_parts:
                        _snapshot = "\n".join(f"- {p}" for p in _hud_parts)
                        _episode_digest = (
                            (_episode_digest + f"\n{_snapshot}")
                            if _episode_digest
                            else f"[HUD 금융 스냅샷]\n{_snapshot}"
                        )
        except Exception as _hud_err:
            logging.warning("[SilentPass:V74] HUD 스냅샷 주입 실패: %s", _hud_err)

        # HUD 리포트
        hud_report = self.ctx.sys.hud.get_v20_hud_report() if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud else ""

        # ===== [V60.80 FIX] 미래 침범 방지 데이터 추출 =====
        current_inventory = []
        current_martial_arts = []
        if hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud:
            current_inventory = (
                list(self.ctx.sys.hud.inventory)
                if hasattr(self.ctx.sys.hud, "inventory") and self.ctx.sys.hud.inventory
                else []
            )
            current_martial_arts = (
                list(self.ctx.sys.hud.techniques)
                if hasattr(self.ctx.sys.hud, "techniques") and self.ctx.sys.hud.techniques
                else []
            )

        # [S4-P2-6] dead_npcs만 필요하지만 개별 쿼리 없음 — DBManager 내부 캐시(_cumulative_bible_cache)로 반복 로드 무비용
        cumulative_bible = self.ctx.current_project.db.get_cumulative_bible(next_ep - 1)
        dead_npcs = cumulative_bible.get("dead_npcs", []) if cumulative_bible else []
        if isinstance(dead_npcs, str):
            dead_npcs = [dead_npcs]  # LLM이 단일 문자열 반환 시 리스트화

        item_acquisition_timeline = self.ctx.build_item_acquisition_timeline(next_ep - 1)

        # [V68] 직전 화 연결고리 로드
        _chain_link_section = self.load_chain_link_section(next_ep)
        if _chain_link_section:
            logging.info(f"[V68] 직전 화 연결고리 로드 완료 ({len(_chain_link_section)}자)")

        # [V68] 세계 상태 요약 로드 (ChiefWriter 프롬프트 주입용)
        _world_state_summary = ""
        if self.ctx.world_state:
            try:
                _world_state_summary = self.ctx.world_state.get_summary(max_chars=50000)
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] WorldState 요약 로드 실패: {e!s:.100}")

        # [NC-2 GAP-1] 직전 3화 씬 키워드 수집 (씬 유사도 advisory용)
        _recent_scene_keywords: list[dict] = []
        try:
            _recent_scene_keywords = self._collect_recent_scene_keywords(
                _db,
                next_ep,
                lookback=3,
            )
        except Exception as _sk_err:
            logging.debug("[NC-2] 씬 키워드 수집 실패 (비치명): %s", _sk_err)

        return {
            "arc_pos": arc_pos,
            "total_ep_in_arc": total_ep_in_arc,
            "arc_tactical": arc_tactical,
            "prev_text": prev_text,
            "prev_ending": prev_ending,
            "prev_manuscripts_text": _prev_manuscripts_text,
            "episode_digest": _episode_digest,
            "hud_report": hud_report,
            "current_inventory": current_inventory,
            "current_martial_arts": current_martial_arts,
            "cumulative_bible": cumulative_bible,
            "dead_npcs": dead_npcs,
            "item_acquisition_timeline": item_acquisition_timeline,
            "chain_link_section": _chain_link_section,
            "world_state_summary": _world_state_summary,
            "recent_scene_keywords": _recent_scene_keywords,  # [NC-2 GAP-1]
        }

    # ── [NC-2 GAP-1] 씬 유사도 분석 유틸 ──────────────────────────

    _SCENE_SPLIT_RE = re.compile(r"\n(?:#{1,3}\s+씬\s*\d+|---+|\*\*\*+|\n{3,})")

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
    ) -> dict:
        """[4-R1-b] mandatory_context + writer prompt 조립을 분리 (동작 변화 없음)."""
        reference_anchor_prompt = ""
        mandatory_context = ""
        anti_trope_prompt = ""
        justification_prompt = ""
        reflexion_prompt = ""
        genre_name = (getattr(self.ctx.current_project, "genre", None) or {}).get("name", "무협")

        if writer_agent is None:
            return {
                "reference_anchor_prompt": reference_anchor_prompt,
                "mandatory_context": mandatory_context,
                "anti_trope_prompt": anti_trope_prompt,
                "justification_prompt": justification_prompt,
                "reflexion_prompt": reflexion_prompt,
            }

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
                reference_anchor_prompt = anchor_sys.generate_reference_prompt(
                    relevant_anchors=relevant_anchors,
                    critical_anchors=critical_anchors,
                )
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ ReferenceAnchor 로드 실패 (비치명): {e}")

        try:
            _db = getattr(self.ctx.current_project, "db", None)
            _bible = getattr(self.ctx.current_project, "master_bible", {})
            mandatory_context = _build_writer_mandatory_context(_db, _bible, next_ep)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
            mandatory_context = (
                "[경고] 필수 컨텍스트 로딩 실패 - 이전 에피소드 상태를 우선 참조하여 연속성을 유지하세요."
            )

        cp_entities = {"npcs": [], "items": [], "plots": [], "locations": [], "_full_text": ""}
        if blueprint:
            try:
                cp_entities = self._extract_blueprint_entities(blueprint, arc_data=arc_data)
            except Exception as cp_entity_err:
                logging.debug("[CP] blueprint entity 추출 실패 (비치명): %s", cp_entity_err)

        _work_focus = self._resolve_work_retrieval_focus(
            stage="manuscript",
            arc_data=arc_data,
            arc_tactical=arc_tactical,
            prev_ending=prev_ending,
            blueprint=blueprint,
            cp_entities=cp_entities,
        )

        _mc_parts = [mandatory_context] if mandatory_context else []

        _slot_summary = self._build_work_identity_slot_summary(
            focus=_work_focus,
            arc_data=arc_data,
            cp_entities=cp_entities,
        )
        if _slot_summary:
            _mc_parts.insert(0, _slot_summary)
            logging.info("[WorkGuard] tracking slot summary 주입 (%d자)", len(_slot_summary))

        _ambient_npc_hint = self._suggest_ambient_npcs(blueprint or {})
        if _ambient_npc_hint:
            _mc_parts.append(_ambient_npc_hint)

        _arc_cs = arc_data.get("constraint_summary", "") if arc_data else ""
        if _arc_cs:
            _mc_parts.append(f"[Arc 제약 - MUST NOT DO]\n{_arc_cs}")

        if self.ctx.world_state:
            try:
                if cp_entities.get("npcs") or cp_entities.get("items") or cp_entities.get("plots"):
                    _ws_summary = self._build_condensed_world_state_summary(cp_entities, max_chars=50000)
                    if not _ws_summary:
                        _ws_summary = self.ctx.world_state.get_summary(max_chars=50000)
                else:
                    _ws_summary = self.ctx.world_state.get_summary(max_chars=50000)
                if _ws_summary:
                    _mc_parts.insert(0, _ws_summary)
                    logging.info(f" [V68] 세계 상태 문서 주입 ({len(_ws_summary)}자)")
            except Exception as _ws_err:
                logging.warning(f" [V68] 세계 상태 문서 주입 실패 (비치명): {str(_ws_err)[:50]}")

        # [Phase3-L3] 타임라인 고정 주입 — world_state 요약 앞에 배치
        try:
            _timeline_budget = int(_threshold("context.timeline_budget", 3000))
            _timeline_text = ""
            if getattr(self.ctx, "world_state", None):
                _timeline_text = self.ctx.world_state.get_timeline_summary(max_chars=_timeline_budget)
            if _timeline_text:
                _mc_parts.insert(0, _timeline_text)
                logging.info("[Phase3] 타임라인 주입 (%d자)", len(_timeline_text))
        except Exception as _tl_err:
            logging.warning("[Phase3] 타임라인 주입 실패 (비치명): %s", str(_tl_err)[:50])

        try:
            _series_summary = self.ctx.current_project.load_v20_anchor("series_summary")
            if _series_summary:
                if isinstance(_series_summary, dict):
                    _series_summary = _series_summary.get("summary", "") or str(_series_summary)
                if _series_summary and len(str(_series_summary)) > 10:
                    _mc_parts.append(f"[V68 시리즈 전체 요약]\n{_series_summary}")

            _current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            _current_vol = max(1, (_current_arc_no - 1) // int(VolumeSettings.ARCS_PER_VOLUME) + 1)
            _volume_summaries = []
            for _vi in range(max(1, _current_vol - 2), _current_vol + 1):
                _vs = self.ctx.current_project.load_v20_anchor(f"volume_summary_{_vi}")
                if _vs:
                    if isinstance(_vs, dict):
                        _vs = _vs.get("summary", "") or str(_vs)
                    if _vs and len(str(_vs)) > 10:
                        _volume_summaries.append(f"[볼륨 {_vi}] {_vs}")
            if _volume_summaries:
                _mc_parts.append("[V68 볼륨 요약]\n" + "\n".join(_volume_summaries))
        except Exception as _hier_err:
            self.ctx.ui.log(f"   ⚠️ [V68] 계층형 요약 로드 실패 (비치명): {str(_hier_err)[:60]}")

        if self.ctx.fact_ledger:
            try:
                if cp_entities.get("npcs") or cp_entities.get("items") or cp_entities.get("_full_text"):
                    _fl_summary = self._build_condensed_fact_ledger_summary(cp_entities, max_chars=25000)
                    if not _fl_summary:
                        _fl_summary = self.ctx.fact_ledger.to_summary(max_chars=25000)
                else:
                    _fl_summary = self.ctx.fact_ledger.to_summary(max_chars=25000)
                if _fl_summary:
                    _mc_parts.insert(0, _fl_summary)
                    logging.info(f" [V68] 팩트 원장 주입 ({len(_fl_summary)}자)")
            except Exception as _fl_mc_err:
                logging.warning(f" [V68] 팩트 원장 주입 실패 (비치명): {str(_fl_mc_err)[:50]}")

        # [Phase1-L0] Canonical Constraints 최상단 고정 주입
        # 중복 방지: role_at_intro+known_attrs (NPC, get_summary에 없음) + 수치 참조 목록만 담당
        try:
            _canonical_budget = int(_threshold("context.canonical_facts_budget", 13000))
            _l0_npc = ""
            _l0_num = ""
            if getattr(self.ctx, "world_state", None):
                _l0_npc = self.ctx.world_state.get_canonical_constraints(max_chars=int(_canonical_budget * 0.62))
            if getattr(self.ctx, "fact_ledger", None):
                _l0_num = self.ctx.fact_ledger.get_canonical_summary(max_chars=int(_canonical_budget * 0.38))
            if _l0_npc or _l0_num:
                _l0_block = "\n\n".join(x for x in [_l0_npc, _l0_num] if x)
                _mc_parts.insert(0, _l0_block)
                logging.info("[Phase1-L0] Canonical 고정 주입 (%d자)", len(_l0_block))
        except Exception as _l0_err:
            logging.warning("[Phase1-L0] Canonical 주입 실패 (비치명): %s", str(_l0_err)[:50])

        # [V74] Treatment genre_ext — 아크 장르 특화 목표 주입
        try:
            _mb = getattr(self.ctx.current_project, "master_bible", None) or {}
            _bible_root = _mb.get("MasterBible", _mb)
            _plot_roadmap = _bible_root.get("plot_roadmap", [])
            _arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            _arc_idx = _arc_no - 1  # arc_no 1-based → plot_roadmap 0-based
            if isinstance(_plot_roadmap, list) and 0 <= _arc_idx < len(_plot_roadmap):
                _tr_block = _plot_roadmap[_arc_idx]
                if isinstance(_tr_block, dict):
                    _genre_ext = _tr_block.get("genre_ext", {})
                    if isinstance(_genre_ext, dict) and _genre_ext:
                        _ge_lines = ["### [V74 Treatment] 이번 아크 장르 특화 정보"]
                        for _gk, _gv in _genre_ext.items():
                            if isinstance(_gv, dict | list):
                                _ge_lines.append(f"  {_gk}: {json.dumps(_gv, ensure_ascii=False)}")
                            else:
                                _ge_lines.append(f"  {_gk}: {_gv}")
                        _ge_lines.append(
                            "⚠️ 원고의 장르 수치(금액, 수익, 레벨, 경지 등)가 "
                            "위 Treatment 목표와 합리적으로 연결되어야 합니다."
                        )
                        _mc_parts.insert(2, "\n".join(_ge_lines))
                        logging.info("[V74] Treatment genre_ext 주입 (arc_no=%d, %d필드)", _arc_no, len(_genre_ext))
        except Exception as _ge_err:
            logging.warning("[SilentPass:V74] Treatment genre_ext 주입 실패: %s", _ge_err)

        if blueprint:
            try:
                cp_text = self._build_continuity_packet(cp_entities)
                if cp_text:
                    _mc_parts.insert(0, cp_text)
                    logging.info(
                        "[CP] Continuity Packet 주입 (%d자, NPC %d, 플롯 %d, 아이템 %d)",
                        len(cp_text),
                        len(cp_entities["npcs"]),
                        len(cp_entities["plots"]),
                        len(cp_entities["items"]),
                    )
            except Exception as cp_err:
                logging.warning("[CP] Continuity Packet 생성 실패 (비치명): %s", str(cp_err)[:80])

        try:
            _boundary_npcs = list(cp_entities.get("npcs") or [])
            if not _boundary_npcs:
                _boundary_npcs = self._collect_npc_roster(arc_data=arc_data or {}, blueprint=blueprint or {})
            _npc_boundary_block = self._build_npc_boundary_block(_boundary_npcs)
            if _npc_boundary_block:
                _mc_parts.insert(0, _npc_boundary_block)
        except Exception as _npc_boundary_err:
            logging.debug("[QI-NPC] NPC boundary block 생성 실패 (비치명): %s", _npc_boundary_err)

        # [S4-I2] state_tracker 16종 요약을 get_all_summaries()로 일괄 수집
        _st = self.ctx.state_tracker
        if _st:
            _arc_no_for_st = arc_data.get("arc_no", 0) if arc_data else 0
            try:
                _all_summaries = _st.get_all_summaries(
                    arc_no=_arc_no_for_st,
                    genre=s4_genre_type,
                )
                _ordered_summaries = self._prioritize_summaries_by_work_focus(list(_all_summaries.values()), _work_focus)
                for _summary in _ordered_summaries:
                    if _summary:
                        _mc_parts.append(_summary)
            except Exception as _st_err:
                logging.warning("[S4-I2] get_all_summaries 실패, 개별 폴백: %s", _st_err)
                # 폴백: 개별 호출 (하위 호환성 보장)
                _fallback_summaries = [
                    _st.get_entity_destruction_summary(),
                    _st.get_resolved_plots_summary(),
                    _st.get_npc_personality_summary(),
                    _st.get_npc_npc_relationship_summary(),
                    _st.get_permanent_injury_summary(),
                    _st.get_time_timeline_summary(),
                    _st.get_companion_summary(),
                    _st.get_commitment_summary(),
                    _st.get_protagonist_emotion_summary(),
                    _st.get_item_state_summary(),
                    _st.get_plot_suspension_summary(_arc_no_for_st),
                    _st.get_npc_dialogue_style_summary(),
                    _st.get_relationship_changes_summary(),
                    _st.get_npc_injury_summary(),
                    _st.get_npc_movement_summary(),
                    _st.get_protagonist_skills_summary(),
                    _st.get_dead_npc_summary(),
                ]
                if s4_genre_type == "hunter":
                    _fallback_summaries.extend(
                        [
                            _st.get_dungeon_clear_summary(),
                            _st.get_skill_cooldown_summary(),
                        ]
                    )
                elif s4_genre_type == "fantasy":
                    _fallback_summaries.extend(
                        [
                            _st.get_spell_repertoire_summary(),
                            _st.get_blessing_curse_summary(),
                        ]
                    )
                elif s4_genre_type == "actor":
                    _fallback_summaries.append(_st.get_filmography_summary())
                _fallback_summaries = self._prioritize_summaries_by_work_focus(_fallback_summaries, _work_focus)
                for _summary in _fallback_summaries:
                    if _summary:
                        _mc_parts.append(_summary)

        try:
            arc_summaries = []
            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            for prev_arc in range(max(1, current_arc_no - 3), current_arc_no):
                arc_sum = self.ctx.current_project.load_v20_anchor(f"arc_summary_{prev_arc}")
                if arc_sum and isinstance(arc_sum, dict):
                    arc_summaries.append(arc_sum)
            if arc_summaries and _st:
                _arc_summary_text = _st.format_arc_summary_for_prompt(arc_summaries)
                if _arc_summary_text:
                    _mc_parts.append(_arc_summary_text)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ [V66] Arc 요약 주입 실패 (비치명): {e}")

        _retrieval_plan = None
        _sc_parts: list[str] = []  # [Wave-B] SC Retrieval 결과 별도 수집 (mandatory_context 앞에 배치)
        try:
            if self.ctx.memory and prev_ending:
                _use_advisor_path = False
                _advisor = getattr(self.ctx, "context_advisor", None)
                _smart_enabled = bool(_threshold("smart_retrieval.enabled", False)) and bool(
                    _threshold("smart_retrieval.stage4_enabled", False)
                )
                if _advisor and _smart_enabled:
                    _arc_ep_start = arc_data.get("ep_start", next_ep) if arc_data else next_ep
                    _arc_ep_count = arc_data.get("ep_count", 0) if arc_data else 0
                    _arc_pos = next_ep - _arc_ep_start + 1
                    _is_arc_boundary = _arc_pos <= 1 or (_arc_ep_count > 0 and _arc_pos >= _arc_ep_count)
                    _npc_roster = self._collect_npc_roster(arc_data=arc_data, blueprint=blueprint)
                    _retrieval_plan = _advisor.plan_stage4_retrieval(
                        arc_data=arc_data or {},
                        blueprint=blueprint or {},
                        prev_ending=prev_ending,
                        current_ep=next_ep,
                        npc_roster=_npc_roster,
                        genre=s4_genre_type,
                        is_arc_boundary=_is_arc_boundary,
                        is_reject_retry=False,
                    )
                    _perf_key = f"sc_stage4_ep{next_ep}_retrieval"
                    try:
                        self.ctx.perf_timer.start(_perf_key)
                    except Exception as _e:
                        logging.debug("[Stage4ContextBuilder] perf_timer SC start 실패 (무시): %s", _e)
                    try:
                        _arc_no_s4 = arc_data.get("arc_no", None) if arc_data else None
                        for _retrieved in self._execute_retrieval_plan(_retrieval_plan, arc_no=_arc_no_s4):
                            _sc_parts.append(_retrieved)  # [Wave-B] _mc_parts 대신 _sc_parts에 수집
                    finally:
                        try:
                            self.ctx.perf_timer.stop(_perf_key)
                        except Exception as _e:
                            logging.debug("[Stage4ContextBuilder] perf_timer SC stop 실패 (무시): %s", _e)
                    _use_advisor_path = True

                _mq_queries = [] if _use_advisor_path else [prev_ending]
                if (not _use_advisor_path) and arc_data and arc_data.get("state_changes"):
                    _sc = arc_data["state_changes"]
                    _npc_names = []
                    if not isinstance(_sc, dict):
                        _sc = {}
                    for _field in ["npc_deaths", "relationship_changes", "npc_injuries"]:
                        for _entry in _sc.get(_field) or []:
                            # [Sweep54] string 엔트리 대응 (stage4_post_processor가 npc_deaths를 str로 생성)
                            if isinstance(_entry, dict):
                                _n = _entry.get("name") or _entry.get("npc", "")
                            elif isinstance(_entry, str):
                                _n = _entry
                            else:
                                continue
                            if _n:
                                _npc_names.append(_n)
                    if _npc_names:
                        _mq_queries.append(" ".join(_npc_names[:5]))
                if (not _use_advisor_path) and arc_tactical and len(arc_tactical) > 50:
                    # [TTE] 에피소드별 지능 추출 (단순 절삭 제거)
                    _ep_tac = extract_episode_tactical(
                        arc_tactical,
                        next_ep,
                        episode_details=(arc_data or {}).get("episode_details"),
                        fallback_full=False,
                    )
                    if _ep_tac:
                        _mq_queries.append(_ep_tac[:1800])
                    else:
                        _mq_queries.append(arc_tactical[:1800])
                _genre_queries = {
                    "hunter": ["던전 클리어 각성 스킬 랭크"],
                    "investment": ["포트폴리오 거래 수익률 투자"],
                    "fantasy": ["마법 축복 주문 마나 정령"],
                }
                if (not _use_advisor_path) and s4_genre_type in _genre_queries:
                    _mq_queries.extend(_genre_queries[s4_genre_type])
                if _mq_queries:
                    _vector_memory = self.ctx.memory.retrieve_multi_query_context(
                        queries=_mq_queries,
                        current_ep=next_ep,
                        n_per_query=3,
                        max_results=_threshold("context.vector_max_results_s4", 20),
                        current_arc_no=current_arc_no,
                    )
                    if _vector_memory:
                        _mc_parts.append(f"[과거 유사 맥락 (벡터 검색)]\n{_vector_memory}")
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ 벡터 검색 실패 (비치명): {e}")

        try:
            _ext_lookback = self.build_extended_lookback_digest(next_ep)
            if _ext_lookback:
                _mc_parts.append(_ext_lookback)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ 확장 Lookback 실패 (비치명): {e}")

        try:
            if v50_modules_available and self.ctx.foreshadow_tracker:
                _foreshadow_prompt = self.ctx.foreshadow_tracker.generate_writer_prompt(next_ep)
                if _foreshadow_prompt:
                    _mc_parts.append(_foreshadow_prompt)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ ForeshadowTracker 프롬프트 실패 (비치명): {e}")

        if self.ctx.semantic_plot_guard:
            try:
                tactical_text = arc_data.get("tactical_doc", "") if arc_data else ""
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                _spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if _spg_warnings:
                    _spg_text = self.ctx.semantic_plot_guard.format_warnings(_spg_warnings)
                    if _spg_text:
                        _mc_parts.append(_spg_text)
            except Exception as e:
                logging.warning(f"[SilentPass:ContextBuilder] SemanticPlotGuard 경고 주입 실패: {e!s:.100}")

        if pacing_analyzer and prev_text and len(prev_text) >= 100:
            try:
                _pacing_result = pacing_analyzer.analyze(prev_text)
                _pacing_prompt = pacing_analyzer.generate_pacing_prompt(_pacing_result)
                if _pacing_prompt:
                    _mc_parts.append(_pacing_prompt)
            except Exception as _pace_err:
                self.ctx.ui.log(f"   ⚠️ [V65] 페이싱 분석 실패 (비치명): {str(_pace_err)[:60]}")

        try:
            _narrative_summaries = self.ctx.load_narrative_summaries()
            if _narrative_summaries:
                _mc_parts.append(_narrative_summaries)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ [V64.P4] 내러티브 요약 로드 실패 (비치명): {str(e)[:60]}")

        # [미래 Arc/Blueprint 주입] — CW·Director 공통 참조용
        _future_ctx = self._build_future_arc_context(next_ep, arc_data)
        if _future_ctx:
            _mc_parts.append(_future_ctx)

        _sc_budget = int(getattr(_retrieval_plan, "total_budget_chars", 0) or 0)
        # [TF7-P1-03] SC 비활성 시 비-SC 필수 문맥이 절삭되지 않도록 양쪽 플래그 모두 확인
        if _threshold("smart_retrieval.enabled", False) and _threshold("smart_retrieval.stage4_enabled", False):
            _mc_parts = self._apply_context_budget(_mc_parts, _sc_budget)

        # [LS-5] SC Retrieval 결과와 non-SC 본문을 합산 budget 기준으로 재조립
        mandatory_context = self._compose_mandatory_context_with_headroom(_sc_parts, _mc_parts)
        _source_counts = self._summarize_retrieval_sources(_retrieval_plan)
        if not _source_counts and any("[과거 유사 맥락" in str(_part) for _part in _mc_parts):
            _source_counts = {"legacy_multi_query": 1}
        _coverage_warnings: list[str] = []
        if _work_focus and not _slot_summary:
            _coverage_warnings.append("missing_work_slot_summary")
        if _work_focus and _retrieval_plan and not any(
            str(getattr(_slot, "category", "")).startswith("work_")
            for _slot in (getattr(_retrieval_plan, "slots", []) or [])
        ):
            _coverage_warnings.append("work_focus_without_slots")
        _slot_summary_survived = "[작품 추적 슬롯 요약]" in mandatory_context
        if _slot_summary and not _slot_summary_survived:
            _coverage_warnings.append("trimmed_work_slot_summary")
        if _source_counts.get(RetrievalSources.DB_NPC_RELATIONSHIP, 0) > 0 and "[관계 의미 질의]" not in mandatory_context:
            _coverage_warnings.append("missing_relation_slice")
        self._record_retrieval_observation(
            ep_num=next_ep,
            stage="stage4",
            observation={
                "work_focus_present": bool(_work_focus),
                "tracking_slots_count": len(_work_focus.get("tracking_slots") or []) if isinstance(_work_focus, dict) else 0,
                "scene_engines_count": len(_work_focus.get("mandatory_scene_engines") or []) if isinstance(_work_focus, dict) else 0,
                "registry_profiles_count": len(_work_focus.get("registry_profiles") or []) if isinstance(_work_focus, dict) else 0,
                "planned_slots_count": len(getattr(_retrieval_plan, "slots", []) or []) if _retrieval_plan else 0,
                "advisor_path_used": bool(_retrieval_plan),
                "work_slot_summary_included": _slot_summary_survived,
                "relation_slice_included": "[관계 의미 질의]" in mandatory_context,
                "source_counts": _source_counts,
                "coverage_warnings": _coverage_warnings,
                "mandatory_context_chars": len(mandatory_context),
                "protected_summary_survived": _slot_summary_survived,
                "trimmed_work_slot_summary": bool(_slot_summary and not _slot_summary_survived),
            },
        )

        try:
            anti_trope_prompt = _build_anti_trope(genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Anti-Trope 실패 (비치명): {e}")

        try:
            justification_prompt = _build_justification(hud_report, genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Justification 실패 (비치명): {e}")

        try:
            if next_ep >= 20:
                from modules.core.reflexion_manager import ReflexionManager

                reflexion = ReflexionManager(self.ctx.current_project)
                reflexion_prompt = reflexion.get_prompt_injection(min_frequency=2)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Reflexion 실패 (비치명): {e}")

        return {
            "reference_anchor_prompt": reference_anchor_prompt,
            "mandatory_context": mandatory_context,
            "anti_trope_prompt": anti_trope_prompt,
            "justification_prompt": justification_prompt,
            "reflexion_prompt": reflexion_prompt,
        }

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
