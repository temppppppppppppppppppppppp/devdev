"""
utf8-hygiene: allow-file -- legacy Korean prompt text and mojibake-adjacent literals predate this patch; item 1 additions are bounded.
[V60.80] Blueprint Constraint Compiler
Arc에서 해당 화의 제약 조건을 구조화된 블록으로 컴파일

목적:
- tactical_doc에서 해당 화 섹션 추출
- 이전 Blueprint와의 연속성 정보 수집
- 정지선(다음 화 내용) 설정

출력 형식:
- MUST_FOCUS (이번 화 핵심 내용)
- STOP_LINE (다음 화 내용 - 절대 침범 금지)
- CONTINUITY (이전 화 연속성)
- INHERITED_STATE (계승해야 할 상태)
"""

import json
import logging
import re

from modules.core.constants import Stage2Limits, smart_truncate
from modules.core.tactical_utils import _EPISODE_HEADER_PATTERNS, extract_episode_tactical


class BlueprintConstraintCompiler:
    """
    [V60.80] Blueprint 제약 조건 컴파일러

    Arc tactical_doc에서 에피소드별 제약을 추출하고 구조화
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def _fit_prompt_text(value: object, max_chars: int, head_ratio: float = 0.55) -> str:
        text = str(value or "")
        if len(text) <= max_chars:
            return text
        return smart_truncate(text, max_chars=max_chars, head_chars=max(1, int(max_chars * head_ratio)))

    def compile(
        self,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict | None = None,
        prev_blueprints: list[dict] | None = None,
        genre: str = "wuxia",
        *,
        prev_manuscript_ending: str = "",
    ) -> dict:
        """
        Blueprint 제약 조건 컴파일

        Args:
            arc_data: 현재 Arc 데이터
            ep_num: 현재 에피소드 번호
            prev_blueprint: 직전 Blueprint (있으면)
            prev_blueprints: 이전 Blueprint 리스트 (연속성 검증용)
            prev_manuscript_ending: [pre-rerun] 직전 원고 말미 텍스트 (시간 진실 소스)

        Returns:
            constraint_block: 구조화된 제약 블록
        """
        # Arc 기본 정보
        ep_start = arc_data.get("ep_start", 1)
        ep_count = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
        arc_no = arc_data.get("arc_no", 1)

        # 현재 화의 Arc 내 위치
        arc_position = ep_num - ep_start + 1

        # 1. 이번 화 핵심 내용 추출
        must_focus = self._extract_episode_focus(arc_data, ep_num, arc_position)

        # 2. 정지선 설정 (다음 화 내용)
        stop_line = self._extract_stop_line(arc_data, ep_num, arc_position, ep_count)

        # 3. 연속성 정보 수집
        continuity = self._extract_continuity(
            prev_blueprint,
            prev_blueprints,
            prev_manuscript_ending=prev_manuscript_ending,
        )

        # 4. 계승 상태 추출
        inherited_state = self._extract_inherited_state(arc_data, prev_blueprint, genre=genre)

        # 5. [V63] Arc에서 전달된 constraint_summary (Stage 2 → Stage 3)
        arc_constraint_summary = arc_data.get("constraint_summary", "")
        if not arc_constraint_summary:
            logging.info(f" [V63.4 P1] Arc {arc_no}에 constraint_summary 필드 없음 → Stage 2 제약 전달 누락 가능")

        # 6. [V63.2] Arc state_changes 요약 (Stage 2 → Stage 3 직접 전달)
        state_changes_summary = self._summarize_state_changes(arc_data.get("state_changes", {}))
        semantic_carryover = self._normalize_semantic_carryover(arc_data.get("semantic_carryover"))

        # 7. 제약 블록 생성
        constraint_block = {
            "ep_num": ep_num,
            "arc_no": arc_no,
            "arc_position": f"{arc_position}/{ep_count}",
            "must_focus": must_focus,
            "stop_line": stop_line,
            "continuity": continuity,
            "inherited_state": inherited_state,
            "arc_constraint_summary": arc_constraint_summary,  # [V63]
            "state_changes_summary": state_changes_summary,  # [V63.2]
            "semantic_carryover": semantic_carryover,
        }

        return constraint_block

    def compile_to_prompt(self, constraint_block: dict) -> str:
        """
        제약 블록을 프롬프트 문자열로 변환

        Args:
            constraint_block: compile() 결과

        Returns:
            프롬프트 주입용 문자열
        """
        lines = []

        # 헤더
        semantic_lines = self._format_semantic_carryover_lines(constraint_block.get("semantic_carryover"))
        if semantic_lines:
            lines.append("### ARC semantic carryover")
            lines.extend(semantic_lines)
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"[V60.80 BLUEPRINT CONSTRAINTS] 제{constraint_block['ep_num']}화")
        lines.append(f"Arc {constraint_block['arc_no']} - 위치: {constraint_block['arc_position']}")
        lines.append("=" * 60)
        lines.append("")

        # MUST FOCUS
        lines.append("### 🎯 MUST_FOCUS (이번 화 핵심 - 반드시 포함)")
        must_focus = constraint_block.get("must_focus", {})
        if must_focus.get("arc_title"):
            lines.append(f"제목: {self._fit_prompt_text(must_focus.get('arc_title', ''), 120)}")
        lines.append(f"내용: {self._fit_prompt_text(must_focus.get('content', '정보 없음'), 500)}")
        if must_focus.get("key_events"):
            lines.append("핵심 이벤트:")
            for event in must_focus["key_events"][:5]:
                lines.append(f"  - {event}")
        lines.append("")

        # STOP LINE
        lines.append("### 🚨 STOP_LINE (다음 화 내용 - 절대 침범 금지)")
        stop_line = constraint_block.get("stop_line", {})
        if stop_line.get("content"):
            _sl_raw = stop_line["content"]
            _sl_display = self._fit_prompt_text(_sl_raw, 500)
            lines.append(f"다음 화 예고: {_sl_display}")
            if len(_sl_raw) > 500:
                lines.append(f"  (원본 {len(_sl_raw)}자 중 500자 표시 — 잔여분 생략)")
            lines.append("⚠️ 위 내용을 이번 화에서 다루면 즉시 REJECT")
        else:
            lines.append("(Arc 마지막 화 - 정지선 없음)")
        lines.append("")

        # CONTINUITY
        lines.append("### 🔗 CONTINUITY (이전 화 연속성)")
        continuity = constraint_block.get("continuity", {})
        if continuity.get("prev_ending"):
            lines.append(f"직전 화 엔딩: {self._fit_prompt_text(continuity['prev_ending'], 150)}")
        if continuity.get("location"):
            lines.append(f"현재 위치: {continuity['location']}")
        if continuity.get("time_context"):
            lines.append(f"시간 맥락: {continuity['time_context']}")
        if continuity.get("ongoing_conflicts"):
            lines.append(f"진행 중 갈등: {', '.join(continuity['ongoing_conflicts'][:3])}")
        lines.append("")

        # INHERITED STATE
        lines.append("### 📦 INHERITED_STATE (계승 상태)")
        inherited = constraint_block.get("inherited_state", {})
        if inherited.get("equipment"):
            lines.append(f"소지품: {inherited['equipment']}")
        if inherited.get("injuries"):
            lines.append(f"부상: {inherited['injuries']}")
        if inherited.get("internal_energy"):
            lines.append(f"내공: {inherited['internal_energy']}")
        if inherited.get("companions"):
            lines.append(f"동행: {', '.join(inherited['companions'])}")
        lines.append("")

        # [V63] Arc-level constraint summary (Stage 2 → Stage 3 전달)
        arc_cs = constraint_block.get("arc_constraint_summary", "")
        if arc_cs:
            lines.append("### 🚫 ARC 제약 (MUST NOT DO)")
            lines.append(arc_cs)
            lines.append("")

        # [V63.2] Arc state_changes 요약 (Stage 2 → Stage 3 직접 전달)
        sc_summary = constraint_block.get("state_changes_summary", "")
        if sc_summary:
            lines.append("### 📊 ARC 상태 변화 (이 Arc에서 발생한/발생할 이벤트)")
            lines.append(sc_summary)
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _extract_episode_focus(self, arc_data: dict, ep_num: int, arc_position: int) -> dict:
        """이번 화 핵심 내용 추출 — [TTE] 공유 유틸 위임"""
        content = extract_episode_tactical(
            arc_data.get("tactical_doc", ""),
            ep_num,
            episode_details=arc_data.get("episode_details"),
            fallback_full=False,
        )

        # beat_sequence 폴백 (기존 로직 유지)
        if not content:
            beats = arc_data.get("beat_sequence", [])
            if arc_position - 1 < len(beats):
                content = beats[arc_position - 1]

        # [Sweep60] beat_sequence 항목이 dict일 수 있음 → str 보장
        if isinstance(content, dict):
            content = content.get("beat", content.get("description", str(content)))
        if not isinstance(content, str):
            content = str(content) if content else ""

        arc_title = self._extract_episode_title(arc_data, ep_num)

        # 핵심 이벤트 추출
        key_events = []
        if content:
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    key_events.append(line.lstrip("-•").strip())
                elif 10 < len(line) < 100:
                    key_events.append(line)

        return {
            "content": content if content else "이번 화 전술 정보 없음",
            "key_events": key_events[:5],
            "arc_position": arc_position,
            "arc_title": arc_title,
        }

    def _extract_episode_title(self, arc_data: dict, ep_num: int) -> str:
        """이번 화 제목 추출.

        우선순위:
        1. episode_details 내 제목성 필드
        2. tactical_doc 에피소드 헤더
        3. arc_data 최상위 title
        """
        episode_details = arc_data.get("episode_details") or []
        if isinstance(episode_details, list):
            for item in episode_details:
                if not isinstance(item, dict) or item.get("ep_num") != ep_num:
                    continue
                for key in ("title", "ep_title", "episode_title", "name", "label"):
                    value = str(item.get(key, "") or "").strip()
                    if value:
                        return value

        tactical_doc = arc_data.get("tactical_doc", "")
        if isinstance(tactical_doc, dict):
            tactical_doc = json.dumps(tactical_doc, ensure_ascii=False, indent=2)
        elif not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc or "")

        if tactical_doc:
            generic_markers = {"전술 설계", "전술", "tactical", "tactical doc", "arc tactical"}
            title_patterns = [
                r"\[\s*제\s*{ep}\s*화([^\]]*)\]",
                r"#{{2,3}}\s*제\s*{ep}\s*화([^\n]*)",
                r"\*\*제\s*{ep}\s*화([^*]*)\*\*",
                r"제\s*{ep}\s*화\s*[:\-\u2013\u2014]\s*([^\n]+)",
            ]
            for pattern_template in title_patterns:
                match = re.search(pattern_template.format(ep=ep_num), tactical_doc, re.MULTILINE)
                if not match:
                    continue
                title = re.sub(r"\s+", " ", match.group(1).strip(" :-–—[]()"))
                if title and title.lower() not in generic_markers:
                    return title

        return str(arc_data.get("title", "") or "").strip()

    def _extract_stop_line(self, arc_data: dict, ep_num: int, arc_position: int, ep_count: int) -> dict:
        """정지선 추출 (다음 화 내용)"""
        # Arc 마지막 화면 정지선 없음
        if arc_position >= ep_count:
            return {"content": None, "is_arc_finale": True}

        next_ep = ep_num + 1
        tactical_doc = arc_data.get("tactical_doc", "")

        if isinstance(tactical_doc, dict):
            tactical_doc = json.dumps(tactical_doc, ensure_ascii=False, indent=2)

        # [TF10-2-2] episode_details 우선 참조 — 다음 화 정지선
        content = ""
        _ep_details = arc_data.get("episode_details") or []
        if isinstance(_ep_details, list):
            for _item in _ep_details:
                if isinstance(_item, dict) and _item.get("ep_num") == next_ep:
                    _details = _item.get("details") or []
                    if isinstance(_details, list) and _details:
                        content = self._fit_prompt_text("; ".join(d for d in _details if isinstance(d, str)), 800)
                    break

        # [S3-I4] 다중 정규식 폴백 패턴으로 다음 화 정지선 추출
        if not content:
            for pattern_template in _EPISODE_HEADER_PATTERNS:
                pattern = pattern_template.format(ep=next_ep)
                match = re.search(pattern, tactical_doc, re.DOTALL)
                if match:
                    content = self._fit_prompt_text(match.group(1).strip(), 800)
                if content:
                    break

        if not content:
            # 폴백: beat_sequence 사용
            beats = arc_data.get("beat_sequence", [])
            if arc_position < len(beats):
                # [TypeSafety] beat가 dict일 수 있음 → str() 래핑
                beat = beats[arc_position]
                content = str(beat) if not isinstance(beat, str) else beat

        return {"content": content if content else None, "is_arc_finale": False, "next_ep": next_ep}

    def _extract_continuity(
        self,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None = None,
        *,
        prev_manuscript_ending: str = "",
    ) -> dict:
        """연속성 정보 추출

        Args:
            prev_manuscript_ending: [pre-rerun] 직전 원고 말미 텍스트 (있으면 blueprint metadata보다 우선)
        """
        continuity = {
            "prev_ending": None,
            "location": None,
            "time_context": None,
            "ongoing_conflicts": [],
            "active_characters": [],
        }

        if not prev_blueprint:
            return continuity

        # 직전 Blueprint에서 추출 (기본값)
        continuity["prev_ending"] = prev_blueprint.get("ending_hook", "")
        continuity["location"] = prev_blueprint.get("end_location", prev_blueprint.get("location", ""))
        bp_time_flow = prev_blueprint.get("time_flow", "")

        # [pre-rerun] 원고 말미가 있으면 시간 컨텍스트를 보강
        if prev_manuscript_ending:
            continuity["time_context"] = (
                f"[원고 기준 종료 상황]\n{prev_manuscript_ending}\n[Blueprint 기록] {bp_time_flow}"
                if bp_time_flow
                else f"[원고 기준 종료 상황]\n{prev_manuscript_ending}"
            )
        else:
            continuity["time_context"] = bp_time_flow

        # scene_breakdown에서 마지막 씬 정보
        scenes = prev_blueprint.get("scene_breakdown", {})
        if scenes and isinstance(scenes, dict):  # [V70] list 타입 방어
            # 마지막 씬 키 찾기
            scene_keys = sorted(
                scenes.keys(), key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0
            )
            if scene_keys:
                last_scene = scenes.get(scene_keys[-1], {})
                if isinstance(last_scene, dict):
                    continuity["location"] = last_scene.get("location", continuity["location"])

                    # 등장인물 추출
                    chars = last_scene.get("characters", [])
                    if isinstance(chars, list):
                        continuity["active_characters"] = chars[:5]

        # ongoing_conflicts 추출 (여러 Blueprint에서)
        if prev_blueprints:
            conflicts = set()
            for bp in prev_blueprints[-3:]:  # 최근 3개
                bp_conflicts = bp.get("ongoing_conflicts", [])
                if isinstance(bp_conflicts, list):
                    conflicts.update(bp_conflicts[:2])
                # cliffhanger도 갈등으로
                cliffhanger = bp.get("cliffhanger", "")
                if cliffhanger:
                    conflicts.add(cliffhanger[:50])
            continuity["ongoing_conflicts"] = list(conflicts)[:5]

        return continuity

    def _extract_inherited_state(self, arc_data: dict, prev_blueprint: dict | None, *, genre: str = "wuxia") -> dict:
        """계승 상태 추출"""
        # [TF-41] P1-1: 비무협 장르는 internal_energy 기본값 제외
        inherited: dict = {"equipment": [], "injuries": "없음", "companions": [], "mood": "평온"}
        if genre == "wuxia":
            inherited["internal_energy"] = "100%"

        # Arc의 joint_docs에서 추출
        joint_docs = arc_data.get("joint_docs", {})
        if joint_docs:
            inventory = joint_docs.get("physical_inventory", [])
            if isinstance(inventory, list):
                inherited["equipment"] = inventory[:10]
            elif isinstance(inventory, str):
                inherited["equipment"] = [i.strip() for i in inventory.split(",")][:10]

        # Arc의 status_shadow에서 추출
        shadow = arc_data.get("status_shadow", {})
        if shadow:
            injuries = shadow.get("expected_injuries", "")
            if injuries:
                inherited["injuries"] = injuries

            # [TF-41] P1-1: 무협 전용 — 비무협 장르는 내공 상속 스킵
            if genre == "wuxia":
                energy = shadow.get("internal_energy_loss", "0%")
                if energy:
                    try:
                        loss = int(re.search(r"(\d+)", str(energy)).group(1))
                        inherited["internal_energy"] = f"{100 - loss}%"
                    except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                        pass

        # Arc의 state_constraints에서 추출
        state = arc_data.get("state_constraints", {})
        if state:
            arc_start = state.get("arc_start_state", {})
            if arc_start:
                inherited["injuries"] = arc_start.get("injuries", inherited["injuries"])
                # [TF-41] P1-1: 무협 전용 — 비무협 장르는 내공 상속 스킵
                if genre == "wuxia" and arc_start.get("internal_energy"):
                    inherited["internal_energy"] = f"{arc_start['internal_energy']}%"
                inherited["equipment"] = arc_start.get("equipment", inherited["equipment"])

        # 이전 Blueprint에서 보강
        if prev_blueprint:
            # protagonist_state 확인
            protag = prev_blueprint.get("protagonist_state", {})
            if protag:
                if protag.get("equipment"):
                    inherited["equipment"] = protag["equipment"]
                if protag.get("injuries"):
                    inherited["injuries"] = protag["injuries"]
                if protag.get("companions"):
                    inherited["companions"] = protag["companions"]
                if protag.get("mood"):
                    inherited["mood"] = protag["mood"]

        return inherited

    def _summarize_state_changes(self, state_changes: dict) -> str:
        """
        [V63.2] Arc state_changes를 Blueprint 제약용 요약 문자열로 변환.

        Stage 2에서 생성된 state_changes의 핵심 이벤트를 추출하여
        Blueprint 생성 시 참조할 수 있도록 한다.
        """
        if not state_changes or not isinstance(state_changes, dict):
            return ""

        lines = []

        # NPC 사망
        deaths = state_changes.get("npc_deaths", [])
        if deaths:
            death_descs = []
            for d in deaths[:5]:
                if isinstance(d, dict):
                    _name = d.get("name", "?")
                    _ep = d.get("episode", "?")
                    _cause = d.get("cause", "")
                    _desc = f"{_name}(EP{_ep}"
                    if _cause:
                        _desc += f", 원인: {_cause}"
                    _desc += ")"
                    death_descs.append(_desc)
                elif isinstance(d, str):
                    death_descs.append(d)
            if death_descs:
                lines.append(f"⚠️ 사망 NPC: {', '.join(death_descs)} → 이후 등장 금지")

        # 무공/스킬 습득
        skills = state_changes.get("skill_acquisitions", [])
        if skills:
            names = []
            for s in skills[:5]:
                if isinstance(s, dict):
                    names.append(s.get("name", "?"))
                elif isinstance(s, str):
                    names.append(s)
            if names:
                lines.append(f"🗡️ 습득 무공: {', '.join(names)}")

        # 관계 변화
        relations = state_changes.get("relationship_changes", [])
        if relations:
            for r in relations[:3]:
                if isinstance(r, dict):
                    lines.append(f"🤝 관계변화: {r.get('npc', '?')} {r.get('from', '?')}→{r.get('to', '?')}")

        # 주요 아이템
        items = state_changes.get("major_items", [])
        if items:
            for it in items[:3]:
                if isinstance(it, dict):
                    lines.append(f"📦 아이템: {it.get('name', '?')} ({it.get('action', '?')})")

        # NPC 부상
        injuries = state_changes.get("npc_injuries", [])
        if injuries:
            for inj in injuries[:3]:
                if isinstance(inj, dict):
                    lines.append(
                        f"🩹 부상: {inj.get('name', inj.get('npc', '?'))} - {inj.get('injury', '?')}"  # [V70] 스키마 키 'name' 우선 ('npc' 폴백)
                    )

        # NPC 이동
        movements = state_changes.get("npc_movements", [])
        if movements:
            for mv in movements[:3]:
                if isinstance(mv, dict):
                    lines.append(
                        f"📍 이동: {mv.get('name', mv.get('npc', '?'))} → {mv.get('to', '?')}"  # [V70] 스키마 키 'name' 우선 ('npc' 폴백)
                    )

        # [V66] 완결된 플롯
        resolved = state_changes.get("resolved_plots", [])
        if resolved:
            for rp in resolved[:5]:
                if isinstance(rp, dict):
                    lines.append(f"✅ 완결 플롯: {rp.get('plot', '?')} (Arc {rp.get('arc_no', '?')}) → 재발생 금지")
                elif isinstance(rp, str):
                    lines.append(f"✅ 완결 플롯: {rp} → 재발생 금지")

        return "\n".join(lines) if lines else ""

    @staticmethod
    def _normalize_semantic_carryover(payload: object) -> dict:
        if not isinstance(payload, dict):
            return {}

        normalized: dict[str, object] = {}

        rels = payload.get("relationship_rationale") or []
        if isinstance(rels, list):
            rel_rows: list[dict[str, str]] = []
            for entry in rels[:4]:
                if not isinstance(entry, dict):
                    continue
                npc = str(entry.get("npc", "") or entry.get("target", "") or "").strip()[:40]
                trigger = str(entry.get("trigger", "") or "").strip()[:120]
                justification = str(entry.get("justification", "") or "").strip()[:120]
                if not (npc or trigger or justification):
                    continue
                row: dict[str, str] = {}
                if npc:
                    row["npc"] = npc
                if trigger:
                    row["trigger"] = trigger
                if justification:
                    row["justification"] = justification
                if row:
                    rel_rows.append(row)
            if rel_rows:
                normalized["relationship_rationale"] = rel_rows

        growth = str(payload.get("growth_justification", "") or "").strip()[:140]
        if growth:
            normalized["growth_justification"] = growth

        foreshadow = payload.get("foreshadow_anchors") or []
        if isinstance(foreshadow, list):
            anchors = [str(item).strip()[:120] for item in foreshadow[:3] if str(item).strip()]
            if anchors:
                normalized["foreshadow_anchors"] = anchors

        checkpoints = payload.get("continuity_checkpoints") or []
        if isinstance(checkpoints, list):
            normalized_points = [str(item).strip()[:80] for item in checkpoints[:4] if str(item).strip()]
            if normalized_points:
                normalized["continuity_checkpoints"] = normalized_points

        return normalized

    @staticmethod
    def _format_semantic_carryover_lines(payload: object) -> list[str]:
        if not isinstance(payload, dict):
            return []

        lines: list[str] = []
        for entry in payload.get("relationship_rationale", []) or []:
            if not isinstance(entry, dict):
                continue
            npc = str(entry.get("npc", "") or "").strip() or "?"
            cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()
            if cue:
                lines.append(f"- relationship {npc}: {cue[:120]}")

        growth = str(payload.get("growth_justification", "") or "").strip()
        if growth:
            lines.append(f"- growth_justification: {growth[:140]}")

        for anchor in (payload.get("foreshadow_anchors", []) or [])[:3]:
            text = str(anchor or "").strip()
            if text:
                lines.append(f"- foreshadow: {text[:120]}")

        checkpoints = [str(item or "").strip()[:80] for item in (payload.get("continuity_checkpoints", []) or [])[:3]]
        checkpoints = [item for item in checkpoints if item]
        if checkpoints:
            lines.append(f"- continuity: {'; '.join(checkpoints)}")

        return lines


def create_blueprint_constraint_compiler():
    """BlueprintConstraintCompiler 생성 헬퍼"""
    return BlueprintConstraintCompiler()
