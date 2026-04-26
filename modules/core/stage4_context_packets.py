"""Stage 4 context packet rendering helpers extracted from Stage4ContextBuilder."""

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from modules.core.constants import VolumeSettings
from modules.core.fact_ledger import _format_number_basis_label

if TYPE_CHECKING:
    from modules.core.stage4_context_builder import Stage4ContextBuilder


class Stage4ContextPackets:
    """Owns continuity/world-state/fact-ledger/tier12 packet rendering."""

    def __init__(
        self,
        owner: "Stage4ContextBuilder",
        *,
        fit_context_text: Callable[..., str],
        build_canonical_facts_section: Callable[[Any, str], str],
    ) -> None:
        self.owner = owner
        self._fit_context_text = fit_context_text
        self._build_canonical_facts_section = build_canonical_facts_section

    def _build_continuity_npc_sections(
        self,
        *,
        npc_names: list[str],
        ws_state: dict[str, Any],
        ledger: dict[str, Any],
        db: Any,
        budget: int,
    ) -> tuple[list[str], int]:
        sections: list[str] = []
        used = 0

        for npc_name in npc_names[:10]:
            npc_block: list[str] = []

            for pool in ("alive_npcs", "dead_npcs"):
                info = (ws_state.get(pool) or {}).get(npc_name)
                if info and isinstance(info, dict):
                    desc = ", ".join(f"{key}={value}" for key, value in info.items() if value and key != "name")
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
                        if not isinstance(row, dict):
                            continue
                        reason = str(row.get("reason", "") or "")
                        reason_str = f" ({reason[:30]})" if reason else ""
                        npc_block.append(
                            f"  [변경 {row.get('episode_no', 'unknown')}화] "
                            f"{row.get('field_name', '')}: {str(row.get('old_value', ''))[:30]} → "
                            f"{str(row.get('new_value', ''))[:30]}{reason_str}"
                        )
                except Exception as history_err:
                    logging.debug("[CP] npc_history 조회 실패: %s", history_err)

            if not npc_block:
                continue

            section = f"• {npc_name}\n" + "\n".join(npc_block)
            if used + len(section) > budget:
                break
            sections.append(section)
            used += len(section)

        return sections, used

    def _build_continuity_relationship_section(self, *, npc_names: list[str], db: Any) -> str:
        if not db or not hasattr(db, "get_relationship_history") or not hasattr(db, "get_npc_relationship_edges"):
            return ""

        rel_lines: list[str] = []
        seen_pairs: set[tuple[str, str]] = set()
        blueprint_npcs = [str(name) for name in npc_names[:10]]

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
                        rel_lines.append(f"  {n1} ↔ {n2}: {cur_rel} (ep{edge.get('since_ep', '?')}~)")
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

        if not rel_lines:
            return ""
        return "• 관계 변천사\n" + "\n".join(rel_lines[:8])

    def _build_continuity_fact_sections(
        self,
        *,
        full_text: str,
        ledger: dict[str, Any],
        fact_ledger: Any,
        db: Any,
    ) -> list[str]:
        sections: list[str] = []
        if not full_text:
            return sections

        if fact_ledger:
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
                    unit_str = f" {unit}" if unit else ""
                    latest_basis = _format_number_basis_label(key_text, num_info)

                    if est_val != "" and str(est_val) != str(cur_val):
                        num_lines.append(
                            f"  {key_text}: {est_val}{unit_str}(ep{est_ep}) → {cur_val}{unit_str} ({latest_basis})"
                        )
                    else:
                        num_lines.append(f"  {key_text}: {cur_val}{unit_str} ({latest_basis})")

                    history = num_info.get("history", [])
                    if isinstance(history, list):
                        for history_entry in history[-3:]:
                            if isinstance(history_entry, str):
                                num_lines.append(f"    └ {history_entry[:80]}")

                if num_lines:
                    sections.append("• 수치 변화 이력\n" + "\n".join(num_lines[:15]))

        canonical_facts_section = self._build_canonical_facts_section(db, full_text)
        if canonical_facts_section:
            sections.append(canonical_facts_section)
        return sections

    def build_continuity_packet(self, entities: dict[str, list[str] | str]) -> str:
        """Assemble the continuity packet for the current episode."""
        owner = self.owner
        if not entities:
            return ""

        parts = ["=== [Continuity Packet] 이번 화 필수 기억 ==="]
        budget = 7000
        used = 0

        project = getattr(owner.ctx, "current_project", None)
        db = getattr(project, "db", None)
        world_state = getattr(owner.ctx, "world_state", None)
        ws_state = getattr(world_state, "_state", {}) if world_state else {}
        fact_ledger = getattr(owner.ctx, "fact_ledger", None)
        ledger = getattr(fact_ledger, "_ledger", {}) if fact_ledger else {}
        npc_names = [str(name) for name in (entities.get("npcs") or [])[:10]]

        npc_sections, npc_used = self._build_continuity_npc_sections(
            npc_names=npc_names,
            ws_state=ws_state,
            ledger=ledger,
            db=db,
            budget=budget,
        )
        parts.extend(npc_sections)
        used += npc_used

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

        rel_section = self._build_continuity_relationship_section(npc_names=npc_names, db=db)
        if rel_section and used + len(rel_section) <= budget:
            parts.append(rel_section)
            used += len(rel_section)

        full_text = str(entities.get("_full_text", "") or "")
        for fact_section in self._build_continuity_fact_sections(
            full_text=full_text,
            ledger=ledger,
            fact_ledger=fact_ledger,
            db=db,
        ):
            if used + len(fact_section) > budget:
                continue
            parts.append(fact_section)
            used += len(fact_section)

        if len(parts) == 1:
            return ""

        result = "\n".join(parts)
        return self._fit_context_text(result, max_chars=budget)

    def _build_condensed_world_state_header_sections(self, *, state: dict[str, Any]) -> list[str]:
        owner = self.owner
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
                prot_lines.append(f"위치: {owner._trim_summary_value(protagonist['location'])}")
            if protagonist.get("assets"):
                prot_lines.append(f"자산: {owner._trim_summary_value(protagonist['assets'], 120)}")
            if protagonist.get("injuries") and protagonist.get("injuries") != "정상":
                prot_lines.append(f"부상: {owner._trim_summary_value(protagonist['injuries'])}")
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
                    f"- {owner._trim_summary_value(mot.get('text'), 80)}"
                    + (f" (제{mot.get('since_ep')}화~)" if mot.get("since_ep") else "")
                    for mot in motivations[:6]
                )
            )

        promises = [
            promise
            for promise in (state.get("promises") or [])
            if isinstance(promise, dict) and promise.get("text") and promise.get("status") in ("pending", None, "")
        ]
        if promises:
            promise_lines = []
            for promise in promises[:6]:
                promiser = str(promise.get("promiser", "") or "").strip()
                promisee = str(promise.get("promisee", "") or "").strip()
                parties = "→".join(x for x in [promiser, promisee] if x)
                text = owner._trim_summary_value(promise.get("text"), 80)
                label = f"{parties}: {text}" if parties else text
                if promise.get("since_ep"):
                    label += f" (제{promise.get('since_ep')}화~)"
                promise_lines.append(f"- {label}")
            if promise_lines:
                parts.append("[서약/약속]\n" + "\n".join(promise_lines))

        cumulative_elapsed = state.get("cumulative_elapsed", {})
        if isinstance(cumulative_elapsed, dict) and cumulative_elapsed.get("total_days"):
            parts.append(f"[누적 경과] 총 {cumulative_elapsed.get('total_days')}일")
        return parts

    def _build_condensed_world_state_registry_sections(
        self,
        *,
        state: dict[str, Any],
        cp_npcs: set[str],
        cp_items: set[str],
        cp_plots: set[str],
    ) -> list[str]:
        owner = self.owner
        parts: list[str] = []

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
                            desc_parts.append(f"위치={owner._trim_summary_value(info['location'], 24)}")
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
                        lines.append(
                            f"- {name} (제{info.get('ep', 'unknown')}화, {owner._trim_summary_value(info.get('cause'), 24)})"
                        )
                    else:
                        lines.append(f"- {name}")
                parts.append(f"[사망 NPC - CP 비포함 {len(lines)}명]\n" + "\n".join(lines))

        relationships = state.get("relationships", {})
        if isinstance(relationships, dict) and relationships:
            rel_lines = []
            for npc, relation in list(relationships.items())[:12]:
                if str(npc).strip() in cp_npcs:
                    continue
                rel_lines.append(f"- {npc}: {owner._trim_summary_value(relation, 40)}")
            if rel_lines:
                parts.append("[주요 관계 - CP 비포함]\n" + "\n".join(rel_lines))

        active_items = state.get("active_items", {})
        if isinstance(active_items, dict) and active_items:
            item_lines = [
                f"- {name}" for name, _info in list(active_items.items())[:20] if str(name).strip() not in cp_items
            ]
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
                plot_lines.append(f"- {owner._trim_summary_value(plot_name, 60)} (제{since_ep}화~)")
            if plot_lines:
                parts.append("[진행 중 플롯 - CP 비포함]\n" + "\n".join(plot_lines[:8]))
            if cp_plots:
                parts.append("[CP 상세 참조]\n- 이번 화 핵심 플롯 상세는 Continuity Packet 참조")
        return parts

    def _build_condensed_world_state_tail_sections(
        self,
        *,
        state: dict[str, Any],
        cp_locations: set[str],
    ) -> list[str]:
        owner = self.owner
        parts: list[str] = []
        pressure_vectors = state.get("active_pressure_vectors", [])
        if isinstance(pressure_vectors, list) and pressure_vectors:
            pressure_lines = []
            for vector in pressure_vectors[:5]:
                if isinstance(vector, dict):
                    text = owner._trim_summary_value(vector.get("text"), 80)
                else:
                    text = owner._trim_summary_value(vector, 80)
                if text:
                    pressure_lines.append(f"- {text}")
            if pressure_lines:
                parts.append("[지속 압박/위협]\n" + "\n".join(pressure_lines))

        if cp_locations:
            parts.append("[CP 상세 참조]\n- 이번 화 위치 맥락 상세는 Continuity Packet 참조")
        return parts

    def build_condensed_world_state_summary(
        self,
        entities: dict[str, list[str] | str],
        *,
        max_chars: int = 50000,
    ) -> str:
        """Build a condensed world-state summary with CP-aware suppression."""
        owner = self.owner
        world_state = getattr(owner.ctx, "world_state", None)
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
        parts.extend(self._build_condensed_world_state_header_sections(state=state))
        parts.extend(
            self._build_condensed_world_state_registry_sections(
                state=state,
                cp_npcs=cp_npcs,
                cp_items=cp_items,
                cp_plots=cp_plots,
            )
        )
        parts.extend(
            self._build_condensed_world_state_tail_sections(
                state=state,
                cp_locations=cp_locations,
            )
        )

        result = "\n\n".join(part for part in parts if part)
        if len(result) > max_chars:
            result = self._fit_context_text(result, max_chars=max_chars)
        return result

    def build_condensed_fact_ledger_summary(
        self,
        entities: dict[str, list[str] | str],
        *,
        max_chars: int = 25000,
    ) -> str:
        """Build a condensed fact-ledger summary with CP-aware suppression."""
        owner = self.owner
        fact_ledger = getattr(owner.ctx, "fact_ledger", None)
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
                role = owner._trim_summary_value(info.get("role", "?"), 24)
                relation = owner._trim_summary_value(info.get("relationship", ""), 24)
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
                owner_name = owner._trim_summary_value(info.get("owner", ""), 20)
                owner_str = f", 소유: {owner_name}" if owner_name else ""
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
                basis = _format_number_basis_label(key, info)
                num_lines.append(f"  - {key}: {info.get('value', '?')}{unit_str} ({basis})")
            if num_lines:
                parts.append("[주요 수치 - CP 비포함]\n" + "\n".join(num_lines[:10]))
            if full_text:
                parts.append("[CP 상세 참조]\n- 이번 화 관련 수치 변화 이력은 Continuity Packet 참조")

        result = "\n\n".join(part for part in parts if part)
        if len(result) > max_chars:
            result = self._fit_context_text(result, max_chars=max_chars)
        return result

    def build_tier12_auxiliary_sections(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        blueprint: dict | None,
        s4_genre_type: str,
        v50_modules_available: bool,
        pacing_analyzer,
        prev_text: str,
        work_focus: str,
        slot_summary: str,
    ) -> dict[str, list[str]]:
        """Build tier-1/tier-2 auxiliary context sections outside the main coordinator."""
        owner = self.owner
        tier1_parts: list[str] = []
        tier2_parts: list[str] = []

        if slot_summary:
            tier1_parts.append(slot_summary)
            logging.info("[WorkGuard] tracking slot summary 주입 (%d자)", len(slot_summary))

        stage2_failure_context = owner._build_stage2_failure_context(arc_data)
        if stage2_failure_context:
            tier2_parts.append(stage2_failure_context)
            logging.info("[Stage4ContextBuilder] stage2 failure context 주입 (%d자)", len(stage2_failure_context))

        ambient_npc_hint = owner._suggest_ambient_npcs(blueprint or {})
        if ambient_npc_hint:
            tier2_parts.append(ambient_npc_hint)

        arc_rationale_digest = arc_data.get("rationale_digest", "") if arc_data else ""
        if arc_rationale_digest:
            tier1_parts.append(f"[Arc 서사 근거]\n{arc_rationale_digest}")

        try:
            series_summary = owner.ctx.current_project.load_v20_anchor("series_summary")
            if series_summary:
                if isinstance(series_summary, dict):
                    series_summary = series_summary.get("summary", "") or str(series_summary)
                if series_summary and len(str(series_summary)) > 10:
                    tier2_parts.append(f"[V68 시리즈 전체 요약]\n{series_summary}")

            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            current_volume = max(1, (current_arc_no - 1) // int(VolumeSettings.ARCS_PER_VOLUME) + 1)
            volume_summaries = []
            for volume_index in range(max(1, current_volume - 2), current_volume + 1):
                volume_summary = owner.ctx.current_project.load_v20_anchor(f"volume_summary_{volume_index}")
                if volume_summary:
                    if isinstance(volume_summary, dict):
                        volume_summary = volume_summary.get("summary", "") or str(volume_summary)
                    if volume_summary and len(str(volume_summary)) > 10:
                        volume_summaries.append(f"[볼륨 {volume_index}] {volume_summary}")
            if volume_summaries:
                tier2_parts.append("[V68 볼륨 요약]\n" + "\n".join(volume_summaries))
        except Exception as hierarchy_err:
            owner.ctx.ui.log(f"   ⚠️ [V68] 계층형 요약 로드 실패 (비치명): {str(hierarchy_err)[:60]}")

        try:
            from modules.core.stage0_handoff import cached_arcs_source_lineage_matches

            project = owner.ctx.current_project
            master_bible = getattr(owner.ctx.current_project, "master_bible", None) or {}
            bible_root = master_bible.get("MasterBible", master_bible)
            plot_roadmap = bible_root.get("plot_roadmap", [])
            cached_arcs = getattr(project, "arcs", []) or []
            if not cached_arcs_source_lineage_matches(project, cached_arcs=cached_arcs, roadmap=plot_roadmap):
                logging.warning(
                    "[Stage4] cached arcs source lineage differs from current plot_roadmap; "
                    "skipping treatment genre_ext injection."
                )
                plot_roadmap = []
            arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            arc_idx = arc_no - 1
            if isinstance(plot_roadmap, list) and 0 <= arc_idx < len(plot_roadmap):
                tr_block = plot_roadmap[arc_idx]
                if isinstance(tr_block, dict):
                    genre_ext = tr_block.get("genre_ext", {})
                    if isinstance(genre_ext, dict) and genre_ext:
                        genre_ext_lines = ["### [V74 Treatment] 이번 아크 장르 특화 정보"]
                        for genre_key, genre_value in genre_ext.items():
                            if isinstance(genre_value, dict | list):
                                genre_ext_lines.append(f"  {genre_key}: {json.dumps(genre_value, ensure_ascii=False)}")
                            else:
                                genre_ext_lines.append(f"  {genre_key}: {genre_value}")
                        genre_ext_lines.append(
                            "⚠️ 원고의 장르 수치(금액, 수익, 레벨, 경지 등)가 위 Treatment 목표와 합리적으로 연결되어야 합니다."
                        )
                        tier2_parts.append("\n".join(genre_ext_lines))
                        logging.info("[V74] Treatment genre_ext 주입 (arc_no=%d, %d필드)", arc_no, len(genre_ext))
        except Exception as genre_ext_err:
            logging.warning("[SilentPass:V74] Treatment genre_ext 주입 실패: %s", genre_ext_err)

        state_tracker = owner.ctx.state_tracker
        if state_tracker:
            tier2_parts.extend(
                self._build_state_tracker_auxiliary_sections(
                    state_tracker=state_tracker,
                    arc_data=arc_data,
                    s4_genre_type=s4_genre_type,
                    work_focus=work_focus,
                )
            )

        try:
            ext_lookback = owner.build_extended_lookback_digest(next_ep)
            if ext_lookback:
                tier2_parts.append(ext_lookback)
        except Exception as ext_lookback_err:
            owner.ctx.ui.log(f"   ⚠️ 확장 Lookback 실패 (비치명): {ext_lookback_err}")

        try:
            if v50_modules_available and owner.ctx.foreshadow_tracker:
                foreshadow_prompt = owner.ctx.foreshadow_tracker.generate_writer_prompt(next_ep)
                if foreshadow_prompt:
                    tier2_parts.append(foreshadow_prompt)
        except Exception as foreshadow_err:
            owner.ctx.ui.log(f"   ⚠️ ForeshadowTracker 프롬프트 실패 (비치명): {foreshadow_err}")

        if owner.ctx.semantic_plot_guard:
            try:
                tactical_text = arc_data.get("tactical_doc", "") if arc_data else ""
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                semantic_plot_guard_warnings = owner.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if semantic_plot_guard_warnings:
                    semantic_plot_guard_text = owner.ctx.semantic_plot_guard.format_warnings(
                        semantic_plot_guard_warnings
                    )
                    if semantic_plot_guard_text:
                        tier2_parts.append(semantic_plot_guard_text)
            except Exception as semantic_guard_err:
                logging.warning(
                    f"[SilentPass:ContextBuilder] SemanticPlotGuard 경고 주입 실패: {semantic_guard_err!s:.100}"
                )

        if pacing_analyzer and prev_text and len(prev_text) >= 100:
            try:
                pacing_result = pacing_analyzer.analyze(prev_text)
                pacing_prompt = pacing_analyzer.generate_pacing_prompt(pacing_result)
                if pacing_prompt:
                    tier2_parts.append(pacing_prompt)
            except Exception as pace_err:
                owner.ctx.ui.log(f"   ⚠️ [V65] 페이싱 분석 실패 (비치명): {str(pace_err)[:60]}")

        try:
            narrative_summaries = owner.ctx.load_narrative_summaries()
            if narrative_summaries:
                tier2_parts.append(narrative_summaries)
        except Exception as narrative_summary_err:
            owner.ctx.ui.log(f"   ⚠️ [V64.P4] 내러티브 요약 로드 실패 (비치명): {str(narrative_summary_err)[:60]}")

        future_context = owner._build_future_arc_context(next_ep, arc_data)
        if future_context:
            tier2_parts.append(future_context)

        return {
            "tier1_parts": tier1_parts,
            "tier2_parts": tier2_parts,
        }

    def _build_state_tracker_auxiliary_sections(
        self,
        *,
        state_tracker,
        arc_data: dict,
        s4_genre_type: str,
        work_focus: str,
    ) -> list[str]:
        owner = self.owner
        tier2_parts: list[str] = []
        arc_no_for_tracker = arc_data.get("arc_no", 0) if arc_data else 0
        try:
            all_summaries = state_tracker.get_all_summaries(
                arc_no=arc_no_for_tracker,
                genre=s4_genre_type,
            )
            filtered_summaries, suppressed_summaries = owner._filter_state_tracker_summaries_for_authority(
                all_summaries
            )
            authority_note = owner._build_state_tracker_authority_note(suppressed_summaries)
            if authority_note:
                tier2_parts.append(authority_note)
            ordered_summaries = owner._prioritize_summaries_by_work_focus(
                list(filtered_summaries.values()),
                work_focus,
            )
            for summary in ordered_summaries:
                if summary:
                    tier2_parts.append(summary)
        except Exception as state_tracker_err:
            logging.warning("[S4-I2] get_all_summaries 실패, 개별 폴백: %s", state_tracker_err)
            fallback_summary_map = {
                "entity_destruction": state_tracker.get_entity_destruction_summary(),
                "resolved_plots": state_tracker.get_resolved_plots_summary(),
                "npc_personality": state_tracker.get_npc_personality_summary(),
                "npc_npc_relationship": state_tracker.get_npc_npc_relationship_summary(),
                "permanent_injury": state_tracker.get_permanent_injury_summary(),
                "time_timeline": state_tracker.get_time_timeline_summary(),
                "companion": state_tracker.get_companion_summary(),
                "commitment": state_tracker.get_commitment_summary(),
                "protagonist_emotion": state_tracker.get_protagonist_emotion_summary(),
                "item_state": state_tracker.get_item_state_summary(),
                "plot_suspension": state_tracker.get_plot_suspension_summary(arc_no_for_tracker),
                "npc_dialogue_style": state_tracker.get_npc_dialogue_style_summary(),
                "relationship_changes": state_tracker.get_relationship_changes_summary(),
                "npc_injury": state_tracker.get_npc_injury_summary(),
                "npc_movement": state_tracker.get_npc_movement_summary(),
                "protagonist_skills": state_tracker.get_protagonist_skills_summary(),
                "dead_npc": state_tracker.get_dead_npc_summary(),
            }
            if s4_genre_type == "hunter":
                fallback_summary_map.update(
                    {
                        "dungeon_clear": state_tracker.get_dungeon_clear_summary(),
                        "skill_cooldown": state_tracker.get_skill_cooldown_summary(),
                    }
                )
            elif s4_genre_type == "fantasy":
                fallback_summary_map.update(
                    {
                        "spell_repertoire": state_tracker.get_spell_repertoire_summary(),
                        "blessing_curse": state_tracker.get_blessing_curse_summary(),
                    }
                )
            elif s4_genre_type == "actor":
                fallback_summary_map["filmography"] = state_tracker.get_filmography_summary()

            filtered_summaries, suppressed_summaries = owner._filter_state_tracker_summaries_for_authority(
                fallback_summary_map
            )
            authority_note = owner._build_state_tracker_authority_note(suppressed_summaries)
            if authority_note:
                tier2_parts.append(authority_note)
            fallback_summaries = owner._prioritize_summaries_by_work_focus(
                list(filtered_summaries.values()),
                work_focus,
            )
            for summary in fallback_summaries:
                if summary:
                    tier2_parts.append(summary)

        try:
            arc_summaries = []
            current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            for prev_arc in range(max(1, current_arc_no - 3), current_arc_no):
                arc_summary = owner.ctx.current_project.load_v20_anchor(f"arc_summary_{prev_arc}")
                if arc_summary and isinstance(arc_summary, dict):
                    arc_summaries.append(arc_summary)
            if arc_summaries:
                arc_summary_text = state_tracker.format_arc_summary_for_prompt(arc_summaries)
                if arc_summary_text:
                    tier2_parts.append(arc_summary_text)
        except Exception as arc_summary_err:
            owner.ctx.ui.log(f"   ⚠️ [V66] Arc 요약 주입 실패 (비치명): {arc_summary_err}")

        return tier2_parts
