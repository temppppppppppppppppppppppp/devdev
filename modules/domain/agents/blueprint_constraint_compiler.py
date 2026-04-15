"""
utf8-hygiene: allow-file -- legacy Korean prompt text and mojibake-adjacent literals predate this patch; item 1 additions are bounded.
[V60.80] Blueprint Constraint Compiler
Arc에서 해당 화의 제약 조건을 구조화된 블록으로 컴파일

목적:
- tactical_doc에서 해당 화 섹션 추출
- 이전 Blueprint와의 연속성 정보 수집
- 정지선(현재 화 이후 모든 미래 화 내용) 설정

출력 형식:
- MUST_FOCUS (이번 화 핵심 내용)
- STOP_LINE (현재 화 이후 모든 미래 화 내용 - 절대 침범 금지)
- CONTINUITY (이전 화 연속성)
- INHERITED_STATE (계승해야 할 상태)
"""

import json
import logging
import re

from modules.core.constants import Stage2Limits, smart_truncate
from modules.core.cross_stage_authority_packet import CROSS_STAGE_AUTHORITY_PACKET_VERSION
from modules.core.episode_state_arbiter import EpisodeStateArbiter
from modules.core.tactical_utils import _EPISODE_HEADER_PATTERNS, extract_episode_tactical
from modules.models.arc import StateChangesDict


def _coerce_mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _resolve_cross_stage_packet(arc_data: dict | None) -> dict:
    payload = arc_data if isinstance(arc_data, dict) else {}
    packet = payload.get("cross_stage_authority_packet")
    if isinstance(packet, dict) and packet.get("contract_version") == CROSS_STAGE_AUTHORITY_PACKET_VERSION:
        return packet
    return {}


def _resolve_cross_stage_opening_location(arc_data: dict | None) -> tuple[str, str]:
    opening = _coerce_mapping(_resolve_cross_stage_packet(arc_data).get("opening_carryover"))
    return str(opening.get("location", "") or "").strip(), str(opening.get("location_source", "") or "").strip()


def _resolve_cross_stage_protagonist_carryover(arc_data: dict | None) -> dict:
    return _coerce_mapping(_resolve_cross_stage_packet(arc_data).get("protagonist_carryover"))


def _append_cross_stage_numeric_fields(fields: list[dict], arc_data: dict | None) -> None:
    numeric = _coerce_mapping(_resolve_cross_stage_packet(arc_data).get("numeric_carryover"))
    for key, label in (
        ("capital", "잔고/자본"),
        ("total_assets", "총자산"),
        ("portfolio_position", "포지션"),
        ("investment_calc_final_cash", "최종 현금"),
        ("investment_calc_final_total_assets", "최종 총자산"),
    ):
        value = numeric.get(key)
        if value in (None, "", [], {}):
            continue
        fields.append({"label": label, "value": str(value)[:150]})


def _resolve_cross_stage_numeric_semantic_families(arc_data: dict | None) -> set[str]:
    numeric = _coerce_mapping(_resolve_cross_stage_packet(arc_data).get("numeric_carryover"))
    families: set[str] = set()
    for raw_key in numeric:
        field_name = str(raw_key or "").strip()
        if not field_name or field_name.endswith("_source"):
            continue
        if field_name in {"capital", "investment_calc_final_cash"}:
            families.add("capital")
        elif field_name in {"total_assets", "investment_calc_final_total_assets"}:
            families.add("total_assets")
        elif field_name == "portfolio_position":
            families.add("portfolio_position")
    return families


def _resolve_institution_family(name: str, suffixes: tuple[str, ...]) -> str:
    matching = [suffix for suffix in suffixes if name.endswith(suffix)]
    return min(matching, key=len) if matching else ""


def _filter_competing_institution_names(
    *,
    preferred_names: set[str],
    candidate_names: set[str],
    suffixes: tuple[str, ...],
) -> set[str]:
    preferred_families = {
        family
        for family in (_resolve_institution_family(name, suffixes) for name in preferred_names)
        if family
    }
    filtered: set[str] = set()
    for name in candidate_names:
        family = _resolve_institution_family(name, suffixes)
        if family and family in preferred_families and name not in preferred_names:
            continue
        filtered.add(name)
    return filtered


def _merge_authority_ordered_names(*name_groups: set[str], limit: int) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in name_groups:
        for name in sorted(group):
            if not name or name in seen:
                continue
            seen.add(name)
            ordered.append(name)
            if len(ordered) >= limit:
                return ordered
    return ordered


def _collect_fact_lock_institution_anchors(
    *,
    bp: dict,
    ms_text: str,
    arc_data: dict,
    ep_num: int,
) -> list[dict]:
    _inst_suffixes_ordered = (
        "투자증권",
        "자산운용",
        "인베스트먼트",
        "PB센터",
        "증권",
        "은행",
        "캐피탈",
        "보험",
        "병원",
        "센터",
        "그룹",
        "재단",
        "협회",
        "연구소",
        "본사",
        "지점",
        "사무실",
    )
    _inst_re = re.compile(
        r"([\w가-힣A-Za-z]{2,15}(?:" + "|".join(re.escape(s) for s in _inst_suffixes_ordered) + r"))"
    )

    def _collect_names(raw_texts: list[str]) -> set[str]:
        names: set[str] = set()
        for raw_text in raw_texts:
            for match in _inst_re.finditer(str(raw_text or "")):
                name = match.group(1).strip()
                if len(name) >= 4:
                    names.add(name)
        return names

    manuscript_institution_names = _collect_names([ms_text]) if ms_text else set()

    blueprint_texts: list[str] = []
    if bp:
        bp_scenes = bp.get("scene_breakdown", {})
        if isinstance(bp_scenes, dict):
            for scene in bp_scenes.values():
                if isinstance(scene, dict):
                    blueprint_texts.append(str(scene.get("location", "") or ""))
        blueprint_texts.append(str(bp.get("end_location", "") or ""))
        for key in ("integrated_scenario", "core_tension", "expected_ending", "ending_hook", "time_flow"):
            blueprint_texts.append(str(bp.get(key, "") or ""))
        bp_ending_state = bp.get("ending_state", {})
        if isinstance(bp_ending_state, dict):
            for value in bp_ending_state.values():
                blueprint_texts.append(str(value or ""))
    blueprint_institution_names = _collect_names(blueprint_texts)

    arc_texts: list[str] = []
    if isinstance(arc_data, dict):
        state = arc_data.get("state_constraints", {})
        if isinstance(state, dict):
            arc_start = state.get("arc_start_state", {})
            if isinstance(arc_start, dict):
                arc_texts.append(str(arc_start.get("relationship", "") or ""))
        arc_texts.append(
            str(
                extract_episode_tactical(
                    arc_data.get("tactical_doc", ""),
                    ep_num,
                    episode_details=arc_data.get("episode_details"),
                    fallback_full=False,
                )
                or ""
            )
        )
    arc_institution_names = _collect_names(arc_texts)

    institution_names = set(manuscript_institution_names)
    filtered_blueprint_names = _filter_competing_institution_names(
        preferred_names=institution_names,
        candidate_names=blueprint_institution_names,
        suffixes=_inst_suffixes_ordered,
    )
    institution_names.update(filtered_blueprint_names)
    filtered_arc_names = _filter_competing_institution_names(
        preferred_names=institution_names,
        candidate_names=arc_institution_names,
        suffixes=_inst_suffixes_ordered,
    )
    ordered_names = _merge_authority_ordered_names(
        manuscript_institution_names,
        filtered_blueprint_names,
        filtered_arc_names,
        limit=4,
    )
    return [{"category": "기관", "fact": f"확정 기관/장소: {inst_name}"} for inst_name in ordered_names]


class BlueprintConstraintCompiler:
    """
    [V60.80] Blueprint 제약 조건 컴파일러

    Arc tactical_doc에서 에피소드별 제약을 추출하고 구조화
    """

    def __init__(self) -> None:
        self.state_arbiter = EpisodeStateArbiter()

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
        is_arc_opening_episode = arc_position <= 1

        # 1. 이번 화 핵심 내용 추출
        must_focus = self._extract_episode_focus(arc_data, ep_num, arc_position)

        # 2. 정지선 설정 (다음 화 내용)
        stop_line = self._extract_stop_line(arc_data, ep_num, arc_position, ep_count)

        # 3. [V63] Arc에서 전달된 constraint_summary (Stage 2 → Stage 3)
        arc_constraint_summary = arc_data.get("constraint_summary", "")
        if not arc_constraint_summary:
            logging.info(f" [V63.4 P1] Arc {arc_no}에 constraint_summary 필드 없음 → Stage 2 제약 전달 누락 가능")

        # 4. [V63.2] Arc state_changes 요약 (Stage 2 → Stage 3 직접 전달)
        state_changes_summary = self._summarize_state_changes(arc_data.get("state_changes", {}), ep_num)
        semantic_carryover = self._normalize_semantic_carryover(arc_data.get("semantic_carryover"), ep_num=ep_num)

        # 5. [IFC] Immutable fact carryover from prior arc — [W2] ep_num 전달
        immutable_fact_carryover = self._extract_immutable_fact_carryover(arc_data, arc_position, ep_num=ep_num)

        # 6. [S3-FL] Fact-Lock Packet — settled prior canon outranks arc pressure
        fact_lock_packet = self._build_fact_lock_packet(
            prev_blueprint=prev_blueprint,
            prev_manuscript_ending=prev_manuscript_ending,
            arc_data=arc_data,
            ep_num=ep_num,
        )

        # 7. [S3-CC] Capital-State Continuity Packet — investment-genre only
        capital_continuity_packet = self._build_capital_continuity_packet(
            prev_blueprint=prev_blueprint,
            prev_manuscript_ending=prev_manuscript_ending,
            arc_data=arc_data,
            genre=genre,
            ep_num=ep_num,
        )

        # 8. [S3-EP] Episode-Progression Packet — prevent prior-episode replay/drift
        episode_progression_packet = self._build_episode_progression_packet(
            prev_blueprint=prev_blueprint,
            arc_data=arc_data,
            ep_num=ep_num,
        )

        episode_state_packet = self.state_arbiter.arbitrate(
            arc_data=arc_data,
            ep_num=ep_num,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            prev_manuscript_ending=prev_manuscript_ending,
            genre=genre,
            fact_lock_packet=fact_lock_packet,
            capital_continuity_packet=capital_continuity_packet,
            episode_progression_packet=episode_progression_packet,
        )
        continuity = self._continuity_from_episode_state_packet(episode_state_packet)
        inherited_state = self._inherited_state_from_episode_state_packet(episode_state_packet, genre=genre)

        # 9. 제약 블록 생성
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
            "immutable_fact_carryover": immutable_fact_carryover,  # [IFC]
            "fact_lock_packet": fact_lock_packet,  # [S3-FL]
            "capital_continuity_packet": capital_continuity_packet,  # [S3-CC]
            "episode_progression_packet": episode_progression_packet,  # [S3-EP]
            "episode_state_packet": episode_state_packet,
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
        lines.append("=" * 60)
        lines.append(f"[V60.80 BLUEPRINT CONSTRAINTS] 제{constraint_block['ep_num']}화")
        lines.append(f"Arc {constraint_block['arc_no']} - 위치: {constraint_block['arc_position']}")
        lines.append("=" * 60)
        lines.append("")

        # [S3-FL] FACT-LOCK PACKET — highest priority, before all other constraints
        fact_lock = constraint_block.get("fact_lock_packet", {})
        if isinstance(fact_lock, dict) and fact_lock.get("anchors"):
            lines.append("### 🔐 [FACT-LOCK] 확정 사실 (이전 원고에서 확정 — 변경 금지)")
            lines.append("아래 사항은 이미 독자에게 공개된 확정 사실입니다.")
            lines.append("Blueprint에서 이 사실을 번복·연화·생략하면 즉시 모순이 됩니다.")
            for anchor in fact_lock["anchors"]:
                if isinstance(anchor, dict):
                    category = anchor.get("category", "")
                    fact = anchor.get("fact", "")
                    if fact:
                        prefix = f"[{category}] " if category else ""
                        lines.append(f"  - {prefix}{fact}")
            lines.append("")

        # [S3-CC] CAPITAL CONTINUITY PACKET — investment-genre contract
        capital_pkt = constraint_block.get("capital_continuity_packet", {})
        if isinstance(capital_pkt, dict) and capital_pkt.get("fields"):
            lines.append("### 💰 [CAPITAL-LOCK] 자본/투자 상태 연속성 (변경 금지)")
            lines.append("아래 자본 상태는 이전 에피소드에서 확정된 수치입니다.")
            lines.append("'아직 여유 자금', '새로 투입' 등 모순 표현을 사용하면 즉시 REJECT.")
            for field in capital_pkt["fields"]:
                if isinstance(field, dict):
                    label = field.get("label", "")
                    value = field.get("value", "")
                    if label and value:
                        lines.append(f"  - {label}: {value}")
            lines.append("")

        progression_pkt = constraint_block.get("episode_progression_packet", {})
        if isinstance(progression_pkt, dict) and (
            progression_pkt.get("time_truths")
            or progression_pkt.get("institution_truths")
            or progression_pkt.get("blocked_scene_families")
        ):
            lines.append("### ⏭️ [EPISODE PROGRESSION] 직전 화 재연 금지 / 이번 화는 앞으로 전진")
            lines.append("이번 화는 직전 화 장면을 다시 재연하는 화가 아닙니다. 직전 화의 결과 이후로 전진하세요.")
            for truth in progression_pkt.get("time_truths", [])[:4]:
                lines.append(f"  - [시간 truth] {truth}")
            for truth in progression_pkt.get("institution_truths", [])[:4]:
                lines.append(f"  - [고유명사 truth] {truth}")
            blocked_families = progression_pkt.get("blocked_scene_families", [])
            if isinstance(blocked_families, list) and blocked_families:
                lines.append("  - [직전 화에서 이미 소비한 scene family — 주 장면으로 재연 금지]")
                for family in blocked_families[:4]:
                    if not isinstance(family, dict):
                        continue
                    label = str(family.get("label", "") or "").strip()
                    location = str(family.get("location", "") or "").strip()
                    scene_type = str(family.get("type", "") or "").strip()
                    characters = family.get("characters", [])
                    char_text = ", ".join(str(item or "").strip() for item in characters if str(item or "").strip())
                    parts = []
                    if label:
                        parts.append(label)
                    if location:
                        parts.append(f"장소:{location}")
                    if char_text:
                        parts.append(f"등장:{char_text}")
                    if scene_type:
                        parts.append(f"type:{scene_type}")
                    if parts:
                        lines.append("    - " + " | ".join(parts))
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

        # STOP LINE — [W1] 모든 미래 에피소드 포괄
        lines.append("### 🚨 STOP_LINE (현재 화 이후 모든 사건 — 절대 침범 금지)")
        stop_line = constraint_block.get("stop_line", {})
        if stop_line.get("is_arc_finale"):
            lines.append("(Arc 마지막 화 - 정지선 없음)")
        else:
            if stop_line.get("content"):
                _sl_raw = stop_line["content"]
                _sl_display = self._fit_prompt_text(_sl_raw, 500)
                lines.append(f"[제{stop_line.get('next_ep', '?')}화]: {_sl_display}")
                if len(_sl_raw) > 500:
                    lines.append(f"  (원본 {len(_sl_raw)}자 중 500자 표시 — 잔여분 생략)")
            for _fe in stop_line.get("future_eps", []):
                lines.append(f"[제{_fe['ep']}화]: {self._fit_prompt_text(_fe['content'], 300)}")
            _cur_ep = constraint_block.get("ep_num", "?")
            lines.append(
                f"⚠️ 현재 화(제{_cur_ep}화) 이후의 모든 에피소드 사건·NPC·전개를 "
                f"이번 화에서 소비하거나 언급하면 즉시 REJECT"
            )
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
            lines.append("### 📊 상태 변화 (현재 화까지 확정된 이벤트)")
            lines.append(sc_summary)
            lines.append("")

        if semantic_lines:
            lines.append("### 🧭 FUTURE SEMANTIC ADVISORY (이번 화 obligation 아님)")
            lines.append("아래 항목은 미래 화/관계 맥락 참고용입니다. 이번 화에서 반드시 모두 소비할 의무는 없습니다.")
            lines.extend(semantic_lines)
            lines.append("")

        # [IFC] Immutable fact carryover — prior-arc recovery obligations
        ifc_carryover = constraint_block.get("immutable_fact_carryover", "")
        if ifc_carryover:
            lines.append("### 🔒 [IFC] 불변 사실 계승 (Prior-Arc Carryover)")
            lines.append("아래 사실은 이전 Arc에서 확정된 불변 조건입니다.")
            lines.append("전술 설계에서 이 사실을 연화하거나 생략하면 안 됩니다.")
            lines.append(ifc_carryover)
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
        """정지선 추출 (현재 화 이후 모든 미래 화 내용)."""
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

        # [W1] 모든 미래 에피소드 정지선 수집 (ep+2 이후)
        future_eps: list[dict] = []
        if isinstance(_ep_details, list):
            for _item in _ep_details:
                if isinstance(_item, dict):
                    _fep = _item.get("ep_num")
                    if isinstance(_fep, int) and _fep > next_ep:
                        _fdetails = _item.get("details") or []
                        if isinstance(_fdetails, list) and _fdetails:
                            _brief = self._fit_prompt_text("; ".join(d for d in _fdetails if isinstance(d, str)), 300)
                            if _brief:
                                future_eps.append({"ep": _fep, "content": _brief})

        return {
            "content": content if content else None,
            "is_arc_finale": False,
            "next_ep": next_ep,
            "future_eps": future_eps,
        }

    def _extract_continuity(
        self,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None = None,
        *,
        prev_manuscript_ending: str = "",
        arc_data: dict | None = None,
        is_arc_opening_episode: bool = False,
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

        arc_start_location = ""
        packet_location, _ = _resolve_cross_stage_opening_location(arc_data)
        if isinstance(arc_data, dict):
            state = arc_data.get("state_constraints", {})
            if isinstance(state, dict):
                arc_start = state.get("arc_start_state", {})
                if isinstance(arc_start, dict):
                    arc_start_location = str(arc_start.get("location", "") or "").strip()
        if packet_location:
            arc_start_location = packet_location

        if not prev_blueprint:
            if arc_start_location:
                continuity["location"] = arc_start_location
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

        if arc_start_location and (is_arc_opening_episode or not continuity.get("location")):
            continuity["location"] = arc_start_location

        return continuity

    @staticmethod
    def _continuity_from_episode_state_packet(packet: dict | None) -> dict:
        payload = packet if isinstance(packet, dict) else {}
        opening = payload.get("opening_truth") if isinstance(payload.get("opening_truth"), dict) else {}
        return {
            "prev_ending": None,
            "location": opening.get("location"),
            "time_context": opening.get("time_context"),
            "ongoing_conflicts": list(opening.get("ongoing_conflicts") or []),
            "active_characters": list(opening.get("active_characters") or []),
        }

    def _extract_inherited_state(
        self,
        arc_data: dict,
        prev_blueprint: dict | None,
        *,
        genre: str = "wuxia",
        is_arc_opening_episode: bool = False,
    ) -> dict:
        """계승 상태 추출"""
        # [TF-41] P1-1: 비무협 장르는 internal_energy 기본값 제외
        inherited: dict = {"equipment": [], "injuries": "없음", "companions": [], "mood": "평온"}
        if genre == "wuxia":
            inherited["internal_energy"] = "100%"

        arc_start_has_equipment = False
        arc_start_has_injuries = False
        packet_has_equipment = False
        packet_has_injuries = False
        packet_has_internal_energy = False

        protagonist_carryover = _resolve_cross_stage_protagonist_carryover(arc_data)
        if protagonist_carryover:
            equipment = protagonist_carryover.get("equipment", [])
            if isinstance(equipment, list):
                inherited["equipment"] = equipment[:10]
                packet_has_equipment = True
            elif isinstance(equipment, str):
                inherited["equipment"] = [i.strip() for i in equipment.split(",")][:10]
                packet_has_equipment = True

            if protagonist_carryover.get("injuries") not in (None, ""):
                inherited["injuries"] = protagonist_carryover.get("injuries", inherited["injuries"])
                packet_has_injuries = True

            if genre == "wuxia" and protagonist_carryover.get("internal_energy") not in (None, ""):
                energy = str(protagonist_carryover.get("internal_energy", "") or "").strip()
                if energy:
                    inherited["internal_energy"] = energy if energy.endswith("%") else f"{energy}%"
                    packet_has_internal_energy = True

        # Arc의 joint_docs에서 추출
        joint_docs = arc_data.get("joint_docs", {})
        if joint_docs and not packet_has_equipment:
            inventory = joint_docs.get("physical_inventory", [])
            if isinstance(inventory, list):
                inherited["equipment"] = inventory[:10]
            elif isinstance(inventory, str):
                inherited["equipment"] = [i.strip() for i in inventory.split(",")][:10]

        # Arc의 status_shadow에서 추출
        shadow = arc_data.get("status_shadow", {})
        if shadow:
            injuries = shadow.get("expected_injuries", "")
            if injuries and not packet_has_injuries:
                inherited["injuries"] = injuries

            # [TF-41] P1-1: 무협 전용 — 비무협 장르는 내공 상속 스킵
            if genre == "wuxia" and not packet_has_internal_energy:
                energy = shadow.get("internal_energy_loss", "0%")
                if energy:
                    try:
                        loss = int(re.search(r"(\d+)", str(energy)).group(1))
                        inherited["internal_energy"] = f"{100 - loss}%"
                    except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                        pass

        # Arc의 state_constraints에서 추출
        state = arc_data.get("state_constraints", {})
        if state and (is_arc_opening_episode or not prev_blueprint):
            arc_start = state.get("arc_start_state", {})
            if arc_start:
                if arc_start.get("injuries") not in (None, "") and not packet_has_injuries:
                    inherited["injuries"] = arc_start.get("injuries", inherited["injuries"])
                    arc_start_has_injuries = True
                # [TF-41] P1-1: 무협 전용 — 비무협 장르는 내공 상속 스킵
                if genre == "wuxia" and arc_start.get("internal_energy") and not packet_has_internal_energy:
                    inherited["internal_energy"] = f"{arc_start['internal_energy']}%"
                if "equipment" in arc_start and arc_start.get("equipment") is not None and not packet_has_equipment:
                    inherited["equipment"] = arc_start.get("equipment", inherited["equipment"])
                    arc_start_has_equipment = True

        # 이전 Blueprint에서 보강
        if prev_blueprint:
            # protagonist_state 확인
            protag = prev_blueprint.get("protagonist_state", {})
            if protag:
                if protag.get("equipment") and not arc_start_has_equipment:
                    inherited["equipment"] = protag["equipment"]
                if protag.get("injuries") and not arc_start_has_injuries:
                    inherited["injuries"] = protag["injuries"]
                if protag.get("companions"):
                    inherited["companions"] = protag["companions"]
                if protag.get("mood"):
                    inherited["mood"] = protag["mood"]

        return inherited

    @staticmethod
    def _inherited_state_from_episode_state_packet(packet: dict | None, *, genre: str = "wuxia") -> dict:
        payload = packet if isinstance(packet, dict) else {}
        protagonist = payload.get("protagonist_truth") if isinstance(payload.get("protagonist_truth"), dict) else {}
        inherited: dict = {
            "equipment": list(protagonist.get("equipment") or []),
            "injuries": protagonist.get("injuries") or "없음",
            "companions": list(protagonist.get("companions") or []),
            "mood": protagonist.get("mood") or "평온",
        }
        if genre == "wuxia":
            inherited["internal_energy"] = protagonist.get("internal_energy") or "100%"
        return inherited

    @staticmethod
    def _build_fact_lock_packet(
        *,
        prev_blueprint: dict | None,
        prev_manuscript_ending: str,
        arc_data: dict,
        ep_num: int,
    ) -> dict:
        """[S3-FL] Build compact fact-lock packet from already-accepted prior canon.

        Extracts settled facts that must not be rewritten by the next blueprint:
        - provenance/source-of-funds anchors
        - key item location/state anchors
        - immediate time/day carryover anchors
        - already-completed action/planning anchors
        """
        anchors: list[dict] = []
        ms_text = str(prev_manuscript_ending or "").strip()
        bp = prev_blueprint if isinstance(prev_blueprint, dict) else {}

        if not ms_text and not bp:
            return {}

        # ── 1. Location anchor ──
        end_loc = bp.get("end_location", "")
        if not end_loc:
            scenes = bp.get("scene_breakdown", {})
            if isinstance(scenes, dict) and scenes:
                scene_keys = sorted(
                    scenes.keys(),
                    key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0,
                )
                if scene_keys:
                    last = scenes.get(scene_keys[-1], {})
                    if isinstance(last, dict):
                        end_loc = last.get("location", "")
        if end_loc:
            anchors.append({"category": "위치", "fact": f"직전 종료 위치: {str(end_loc)[:120]}"})

        # ── 2. Time/day anchor ──
        time_flow = bp.get("time_flow", "")
        ending_state = bp.get("ending_state", {})
        if isinstance(ending_state, dict) and ending_state.get("timeline"):
            tl = ending_state["timeline"]
            tl_str = ", ".join(f"{k}:{v}" for k, v in tl.items()) if isinstance(tl, dict) else str(tl)
            anchors.append({"category": "시간", "fact": f"직전 종료 시점: {str(tl_str)[:120]}"})
        elif time_flow:
            anchors.append({"category": "시간", "fact": f"직전 시간 흐름: {str(time_flow)[:120]}"})

        # ── 3. Ending hook anchor (prevents rewrite of how the previous ep ended) ──
        ending_hook = bp.get("ending_hook", "")
        if ending_hook:
            anchors.append({"category": "엔딩훅", "fact": f"직전 화 엔딩: {str(ending_hook)[:200]}"})

        # ── 4. Protagonist state anchor ──
        protag = bp.get("protagonist_state", {})
        if isinstance(protag, dict):
            equip = protag.get("equipment", [])
            if isinstance(equip, list) and equip:
                equip_str = ", ".join(str(x.get("name", x) if isinstance(x, dict) else x) for x in equip[:5])
                anchors.append({"category": "소지품", "fact": f"확정 소지품: {equip_str[:150]}"})
            injuries = protag.get("injuries", "")
            if injuries and str(injuries).strip() not in ("없음", "", "None"):
                anchors.append({"category": "부상", "fact": f"확정 부상: {str(injuries)[:120]}"})

        # ── 5. Manuscript-derived provenance anchors ──
        # Extract compact facts from the manuscript tail that indicate settled actions
        if ms_text:
            # Item storage/placement patterns (e.g., "금고에 넣었다", "품에 간직했다")
            _item_storage_re = re.compile(
                r"([\w가-힣]{2,10})(?:을|를|이|가)\s+"
                r"([\w가-힣]{2,10})(?:에|속에|안에|위에)\s*"
                r"(?:넣|보관|숨기|간직|감추|두|놓)"
            )
            for m in _item_storage_re.finditer(ms_text):
                item_name, location = m.group(1), m.group(2)
                anchors.append(
                    {
                        "category": "아이템위치",
                        "fact": f"원고 확정: '{item_name}' → '{location}'에 보관/배치",
                    }
                )
                if len(anchors) >= 12:
                    break

        # ── 6. NPC/Institution authority anchor [NPC-CF] ──
        # Prevent downstream blueprints from rewriting canonical institution/venue names
        anchors.extend(
            _collect_fact_lock_institution_anchors(
                bp=bp,
                ms_text=ms_text,
                arc_data=arc_data,
                ep_num=ep_num,
            )
        )

        if not anchors:
            return {}

        return {"anchors": anchors[:16], "source": "prev_manuscript+blueprint"}

    @staticmethod
    def _build_episode_progression_packet(
        *,
        prev_blueprint: dict | None,
        arc_data: dict,
        ep_num: int,
    ) -> dict:
        """Build compact progression guardrails for immediate next-episode generation.

        Purpose:
        - surface authoritative time/season truth from current arc authority
        - reinforce canonical institution/group names
        - discourage replaying prior episode scene families as the next episode's main beats
        """
        bp = prev_blueprint if isinstance(prev_blueprint, dict) else {}
        if not bp and not isinstance(arc_data, dict):
            return {}

        def _dedup(values: list[str], *, limit: int) -> list[str]:
            seen: set[str] = set()
            ordered: list[str] = []
            for raw in values:
                value = str(raw or "").strip()
                if not value or value in seen:
                    continue
                seen.add(value)
                ordered.append(value)
                if len(ordered) >= limit:
                    break
            return ordered

        def _parse_timeline_point(raw: object, *, pick: str) -> tuple[int, int] | None:
            if isinstance(raw, dict):
                year = raw.get("year")
                month = raw.get("month")
                if year is not None and month is not None:
                    try:
                        return int(year), int(month)
                    except (TypeError, ValueError):
                        return None
                raw = raw.get("표현") or raw.get("expression") or raw.get("text") or raw.get("raw") or ""
            text = str(raw or "").strip()
            if not text:
                return None
            year_match = re.search(r"(\d{4})년", text)
            month_match = re.findall(r"(\d{1,2})월", text)
            if not month_match:
                return None
            month = int(month_match[0] if pick == "start" else month_match[-1])
            year = int(year_match.group(1)) if year_match else 0
            return year, month

        def _season_from_month(month: int) -> str:
            if month in (12, 1, 2):
                return "겨울"
            if month in (3, 4, 5):
                return "봄"
            if month in (6, 7, 8):
                return "여름"
            return "가을"

        def _location_variants(raw: object) -> list[str]:
            location = str(raw or "").strip()
            if not location:
                return []
            parts = [part.strip() for part in re.split(r"[,/|>→]+", location) if part.strip()]
            return _dedup([location, *parts[-2:], *parts[:1]], limit=4)

        def _scene_rows(scene_breakdown: object) -> list[dict]:
            if isinstance(scene_breakdown, list):
                scene_breakdown = {
                    f"scene_{idx + 1}": scene for idx, scene in enumerate(scene_breakdown) if isinstance(scene, dict)
                }
            if not isinstance(scene_breakdown, dict):
                return []
            scene_rows: list[dict] = []
            scene_keys = sorted(
                scene_breakdown.keys(),
                key=lambda key: int(re.search(r"\d+", key).group()) if re.search(r"\d+", key) else 0,
            )
            for scene_key in scene_keys:
                scene = scene_breakdown.get(scene_key, {})
                if not isinstance(scene, dict):
                    continue
                location = str(scene.get("location", "") or "").strip()
                raw_characters = scene.get("characters", [])
                if isinstance(raw_characters, str):
                    characters = _dedup([raw_characters], limit=4)
                elif isinstance(raw_characters, list):
                    characters = _dedup([str(item or "").strip() for item in raw_characters], limit=4)
                else:
                    characters = []
                label = str(
                    scene.get("title", "") or scene.get("summary", "") or scene.get("goal", "") or scene_key
                ).strip()
                scene_type = str(scene.get("type", "") or "").strip()
                if not location and not characters:
                    continue
                scene_rows.append(
                    {
                        "scene_key": scene_key,
                        "label": label[:120],
                        "location": location[:120],
                        "location_variants": _location_variants(location),
                        "characters": characters,
                        "type": scene_type[:40],
                    }
                )
            return scene_rows[-3:]

        time_truths: list[str] = []
        institution_truths: list[str] = []
        blocked_scene_families = _scene_rows(bp.get("scene_breakdown", {}))

        if isinstance(arc_data, dict):
            current_episode_excerpt = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
                fallback_full=False,
            )
            excerpt_text = str(current_episode_excerpt or "").strip()
            if any(marker in excerpt_text for marker in ("다음 날", "다음날", "이튿날", "익일")):
                time_truths.append("이번 화는 직전 화 직후/다음 날 축에서 시작한다.")

            timeline = arc_data.get("state_changes", {}).get("timeline", {})
            if isinstance(timeline, dict):
                start_point = _parse_timeline_point(timeline.get("start"), pick="start")
                end_point = _parse_timeline_point(timeline.get("end"), pick="end")
                ref_point = start_point or end_point
                if ref_point is not None:
                    year, month = ref_point
                    prefix = f"{year}년 {month}월" if year > 0 else f"{month}월"
                    time_truths.append(f"현재 Arc 시간축은 {prefix}({_season_from_month(month)} 축)이다.")

            _inst_suffixes_ordered = (
                "투자증권",
                "자산운용",
                "인베스트먼트",
                "PB센터",
                "증권",
                "은행",
                "캐피탈",
                "보험",
                "병원",
                "센터",
                "그룹",
                "재단",
                "협회",
                "연구소",
                "본사",
                "지점",
                "사무실",
            )
            _inst_re = re.compile(
                r"([\w가-힣A-Za-z]{2,15}(?:" + "|".join(re.escape(s) for s in _inst_suffixes_ordered) + r"))"
            )
            inst_sources: list[str] = [excerpt_text]
            state = arc_data.get("state_constraints", {})
            if isinstance(state, dict):
                arc_start = state.get("arc_start_state", {})
                if isinstance(arc_start, dict):
                    inst_sources.append(str(arc_start.get("relationship", "") or ""))
                    inst_sources.append(str(arc_start.get("location", "") or ""))
            for raw_source in inst_sources:
                for match in _inst_re.finditer(str(raw_source or "")):
                    name = match.group(1).strip()
                    if len(name) >= 4:
                        institution_truths.append(name)

        prev_time_flow = str(bp.get("time_flow", "") or "").strip()
        if prev_time_flow:
            if any(marker in prev_time_flow for marker in ("다음 날", "다음날", "이튿날", "익일")):
                time_truths.append("직전 화 시간 진실에 이미 '다음 날' 축이 열려 있다.")
            if any(marker in prev_time_flow for marker in ("겨울", "한겨울", "1월", "12월", "2월")):
                time_truths.append(f"직전 화 시간 진실: {prev_time_flow[:120]}")

        if not time_truths and not institution_truths and not blocked_scene_families:
            return {}

        return {
            "time_truths": _dedup(time_truths, limit=4),
            "institution_truths": _dedup(institution_truths, limit=4),
            "blocked_scene_families": blocked_scene_families,
            "source": "prev_blueprint+arc_authority",
        }

    @staticmethod
    def _build_capital_continuity_packet(
        *,
        prev_blueprint: dict | None,
        prev_manuscript_ending: str,
        arc_data: dict,
        genre: str,
        ep_num: int = 0,
    ) -> dict:
        """[S3-CC] Build capital-state continuity packet for investment-genre runs."""
        if genre != "investment":
            return {}

        fields: list[dict] = []
        bp = prev_blueprint if isinstance(prev_blueprint, dict) else {}
        ms_text = str(prev_manuscript_ending or "").strip()
        _append_cross_stage_numeric_fields(fields, arc_data)
        packet_field_count = len(fields)
        packet_numeric_families = _resolve_cross_stage_numeric_semantic_families(arc_data)

        def _capital_within_ep(entry: object) -> bool:
            if ep_num <= 0:
                return True
            if not isinstance(entry, dict):
                return True
            for key in ("episode", "ep_num", "ep"):
                ep_val = entry.get(key)
                if ep_val is None:
                    continue
                try:
                    return int(ep_val) <= ep_num
                except (TypeError, ValueError):
                    return True
            return True

        # ── From blueprint ending state ──
        ending_state = bp.get("ending_state", {})
        if isinstance(ending_state, dict):
            for key, label in [
                ("balance", "잔고/자본"),
                ("capital", "자본 상태"),
                ("deployed", "투입 상태"),
                ("position", "포지션"),
                ("investment_status", "투자 현황"),
            ]:
                if key in {"balance", "capital"} and "capital" in packet_numeric_families:
                    continue
                if key == "position" and "portfolio_position" in packet_numeric_families:
                    continue
                val = ending_state.get(key)
                if val:
                    fields.append({"label": label, "value": str(val)[:150]})

        # ── From protagonist_state ──
        protag = bp.get("protagonist_state", {})
        if isinstance(protag, dict):
            for key, label in [
                ("balance", "잔고"),
                ("capital", "자본"),
                ("portfolio", "포트폴리오"),
            ]:
                if key in {"balance", "capital"} and "capital" in packet_numeric_families:
                    continue
                if key == "portfolio" and "portfolio_position" in packet_numeric_families:
                    continue
                val = protag.get(key)
                if val:
                    fields.append({"label": label, "value": str(val)[:150]})

        # ── Fallback: From equipment free-text [NPC-CF-B] ──
        if isinstance(protag, dict):
            equip_list = protag.get("equipment", [])
            if isinstance(equip_list, list):
                _money_in_equip_re = re.compile(
                    r"(\d[\d,.]*\s*억(?:\s*\d[\d,.]*\s*(?:천만|백만|만))?\s*(?:원|달러)"
                    r"|\d[\d,.]*\s*(?:천만|백만|만)?\s*(?:원|달러|만원|만\s*원))"
                )
                for item in equip_list[:10]:
                    item_str = str(item.get("name", item) if isinstance(item, dict) else item or "")
                    money_m = _money_in_equip_re.search(item_str)
                    if money_m:
                        amount = money_m.group(1).strip()
                        if any(kw in item_str for kw in ("예치", "잔고", "잔액", "보유", "가용")):
                            fields.append({"label": "보유 자본", "value": f"{amount} (예치/보유 상태)"})
                        elif any(kw in item_str for kw in ("투입", "매수", "투자", "배치", "체결")):
                            fields.append({"label": "투입 확정", "value": f"{amount} (투입/체결 완료 — 가용 아님)"})
                        else:
                            fields.append({"label": "자본 관련", "value": f"{amount}: {item_str[:80]}"})
                        if len(fields) >= 8:
                            break

        # ── Fallback: Protagonist status free-text [NPC-CF-B] ──
        protag_status = ""
        if isinstance(protag, dict):
            protag_status = str(protag.get("status", "") or "").strip()
        if not protag_status and isinstance(ending_state, dict):
            protag_status = str(ending_state.get("protagonist_status", "") or "").strip()
        if protag_status and len(fields) < 8:
            _money_in_status_re = re.compile(r"(\d[\d,.]*\s*(?:억|만|천만|백만)?\s*(?:원|달러|만원|만\s*원))")
            for m in _money_in_status_re.finditer(protag_status):
                amount = m.group(1).strip()
                if any(kw in protag_status for kw in ("투입", "매수", "배치", "체결")):
                    fields.append({"label": "투입 확정", "value": f"{amount} (상태 기록 — 투입 완료)"})
                else:
                    fields.append({"label": "상태 기록 자본", "value": f"{amount} (상태 기록)"})
                if len(fields) >= 8:
                    break

        # ── Fallback: Deployment-state markers from manuscript tail [NPC-CF-B] ──
        if ms_text and len(fields) < 8:
            _deploy_complete_re = re.compile(
                r"(\d[\d,.]*\s*(?:억|만|천만|백만)?\s*(?:원|달러|만원))"
                r".{0,40}?"
                r"(?:을|를)?\s*(?:전액\s*)?(?:투입|투자|매수|배치|사용)"
            )
            for m in _deploy_complete_re.finditer(ms_text[-2000:]):
                amount = m.group(1).strip()
                if amount and not any(amount in str(f.get("value", "")) for f in fields):
                    fields.append(
                        {
                            "label": "투입 확정",
                            "value": f"{amount} 투입/매수 — 가용 자본 아님",
                        }
                    )
                    if len(fields) >= 8:
                        break

        # ── From state_changes ──
        state_changes = arc_data.get("state_changes", {}) if isinstance(arc_data, dict) else {}
        if isinstance(state_changes, dict):
            capital_events = state_changes.get("capital_changes") or state_changes.get("financial_events") or []
            if isinstance(capital_events, list):
                for event in [entry for entry in capital_events if _capital_within_ep(entry)][:3]:
                    if isinstance(event, dict):
                        desc = event.get("description") or event.get("event") or ""
                        amount = event.get("amount") or ""
                        if desc:
                            val = f"{desc}"
                            if amount:
                                val += f" ({amount})"
                            fields.append({"label": "자본 이벤트", "value": str(val)[:150]})

        # ── From manuscript tail — explicit money/capital mentions ──
        if ms_text:
            _capital_re = re.compile(
                r"([\d,]+\s*(?:원|만원|억|만|달러|골드|냥|전|관))"
                r"(?:을|를|이|가|의|은|는)?\s*"
                r"(투자|투입|매수|매도|배치|사용|지출|입금|출금|결제|지불|소비)"
            )
            for m in _capital_re.finditer(ms_text):
                amount_str, action = m.group(1), m.group(2)
                fields.append(
                    {
                        "label": f"원고 확정 {action}",
                        "value": f"{amount_str} {action} 완료",
                    }
                )
                if len(fields) >= 8:
                    break

        if not fields:
            return {}

        # Deduplicate by label
        seen_labels: set[str] = set()
        source_origins: set[str] = set()
        unique_fields: list[dict] = []
        for index, f in enumerate(fields):
            label = f.get("label", "")
            if label not in seen_labels:
                seen_labels.add(label)
                unique_fields.append(f)
                source_origins.add("cross_stage_packet" if index < packet_field_count else "prev_authority")

        if source_origins == {"cross_stage_packet"}:
            return {"fields": unique_fields[:8], "source": "cross_stage_packet"}
        source = "prev_authority+cross_stage_packet" if "cross_stage_packet" in source_origins else "prev_authority"
        return {"fields": unique_fields[:8], "source": source}

    @staticmethod
    def _extract_immutable_fact_carryover(arc_data: dict, arc_position: int, ep_num: int = 0) -> str:
        """[IFC] Extract immutable fact carryover from prior-arc state.

        For arc_position > 1, prior episode state_changes contain facts that
        must not be silently softened in tactical planning.

        [W2] ep_num > 0 이면 해당 화 이하 에피소드 이벤트만 포함.
        """
        if arc_position <= 1:
            return ""

        state_changes = arc_data.get("state_changes", {})
        if not isinstance(state_changes, dict):
            return ""

        # [W2] episode boundary filter — reuse _within_ep() logic
        def _ifc_within_ep(entry: object) -> bool:
            if ep_num <= 0:
                return True
            if not isinstance(entry, dict):
                return True
            ep_val = entry.get("episode")
            if ep_val is None:
                return True
            try:
                return int(ep_val) <= ep_num
            except (TypeError, ValueError):
                return True

        carryover_lines: list[str] = []

        # NPC deaths are absolute — cannot be undone
        deaths = [d for d in (state_changes.get("npc_deaths") or []) if _ifc_within_ep(d)]
        for d in deaths[:5]:
            name = d.get("name", d) if isinstance(d, dict) else str(d)
            if name:
                carryover_lines.append(f"- 사망 확정: {name} (회상/언급만 가능)")

        # Relationship changes are committed
        for rel in [r for r in (state_changes.get("relationship_changes") or []) if _ifc_within_ep(r)][:5]:
            if isinstance(rel, dict):
                npc = rel.get("npc") or rel.get("target") or ""
                to_rel = rel.get("to", "")
                if npc and to_rel:
                    carryover_lines.append(f"- 관계 확정: {npc} → {to_rel}")

        # Major items acquired/lost are committed
        for item in [it for it in (state_changes.get("major_items") or []) if _ifc_within_ep(it)][:5]:
            if isinstance(item, dict):
                name = item.get("name", "")
                action = item.get("action", "획득")
                if name:
                    carryover_lines.append(f"- 아이템 확정: {name} ({action})")

        # Skill acquisitions are committed
        for skill in [s for s in (state_changes.get("skill_acquisitions") or []) if _ifc_within_ep(s)][:3]:
            name = skill.get("name", skill) if isinstance(skill, dict) else str(skill)
            if name:
                carryover_lines.append(f"- 무공 확정: {name}")

        return "\n".join(carryover_lines)

    def _summarize_state_changes(self, state_changes: StateChangesDict, ep_num: int = 0) -> str:
        """
        [V63.2] Arc state_changes를 Blueprint 제약용 요약 문자열로 변환.
        [W1] ep_num > 0이면 해당 화 이하 에피소드 이벤트만 포함, 미래 화 이벤트 제외.

        Stage 2에서 생성된 state_changes의 핵심 이벤트를 추출하여
        Blueprint 생성 시 참조할 수 있도록 한다.
        """
        if not state_changes or not isinstance(state_changes, dict):
            return ""

        # [W1] 현재 화 이하 에피소드만 허용하는 필터
        def _within_ep(entry: object) -> bool:
            if ep_num <= 0:
                return True
            if not isinstance(entry, dict):
                return True
            ep_val = entry.get("episode")
            if ep_val is None:
                return True
            try:
                return int(ep_val) <= ep_num
            except (TypeError, ValueError):
                return True

        lines = []

        # NPC 사망
        deaths = [d for d in (state_changes.get("npc_deaths") or []) if _within_ep(d)]
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
        skills = [s for s in (state_changes.get("skill_acquisitions") or []) if _within_ep(s)]
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
        relations = [r for r in (state_changes.get("relationship_changes") or []) if _within_ep(r)]
        if relations:
            for r in relations[:3]:
                if isinstance(r, dict):
                    lines.append(f"🤝 관계변화: {r.get('npc', '?')} {r.get('from', '?')}→{r.get('to', '?')}")

        # 주요 아이템
        items = [it for it in (state_changes.get("major_items") or []) if _within_ep(it)]
        if items:
            for it in items[:3]:
                if isinstance(it, dict):
                    lines.append(f"📦 아이템: {it.get('name', '?')} ({it.get('action', '?')})")

        # NPC 부상
        injuries = [inj for inj in (state_changes.get("npc_injuries") or []) if _within_ep(inj)]
        if injuries:
            for inj in injuries[:3]:
                if isinstance(inj, dict):
                    lines.append(
                        f"🩹 부상: {inj.get('name', inj.get('npc', '?'))} - {inj.get('injury', '?')}"  # [V70] 스키마 키 'name' 우선 ('npc' 폴백)
                    )

        # NPC 이동
        movements = [mv for mv in (state_changes.get("npc_movements") or []) if _within_ep(mv)]
        if movements:
            for mv in movements[:3]:
                if isinstance(mv, dict):
                    lines.append(
                        f"📍 이동: {mv.get('name', mv.get('npc', '?'))} → {mv.get('to', '?')}"  # [V70] 스키마 키 'name' 우선 ('npc' 폴백)
                    )

        # [V66] 완결된 플롯
        resolved = [rp for rp in (state_changes.get("resolved_plots") or []) if _within_ep(rp)]
        if resolved:
            for rp in resolved[:5]:
                if isinstance(rp, dict):
                    lines.append(f"✅ 완결 플롯: {rp.get('plot', '?')} (Arc {rp.get('arc_no', '?')}) → 재발생 금지")
                elif isinstance(rp, str):
                    lines.append(f"✅ 완결 플롯: {rp} → 재발생 금지")

        return "\n".join(lines) if lines else ""

    @staticmethod
    def _coerce_episode_marker(value: object) -> int | None:
        try:
            marker = int(value)
        except (TypeError, ValueError):
            return None
        return marker if marker > 0 else None

    @classmethod
    def _entry_visible_in_episode(cls, entry: object, ep_num: int) -> bool:
        if ep_num <= 0 or not isinstance(entry, dict):
            return True

        exact_keys = ("episode", "ep_num", "ep", "target_episode", "target_ep")
        for key in exact_keys:
            marker = cls._coerce_episode_marker(entry.get(key))
            if marker is not None:
                return marker <= ep_num

        start_keys = ("visible_from_episode", "start_episode", "from_episode")
        for key in start_keys:
            marker = cls._coerce_episode_marker(entry.get(key))
            if marker is not None:
                return marker <= ep_num

        return True

    @classmethod
    def _normalize_semantic_carryover(cls, payload: object, *, ep_num: int = 0) -> dict:
        if not isinstance(payload, dict):
            return {}

        normalized: dict[str, object] = {}

        rels = payload.get("relationship_rationale") or []
        if isinstance(rels, list):
            rel_rows: list[dict[str, str]] = []
            for entry in rels[:4]:
                if not isinstance(entry, dict):
                    continue
                if not cls._entry_visible_in_episode(entry, ep_num):
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

        # [W2] growth_justification: suppressed — encodes future achievement
        # that reads as current-episode progress fuel.

        foreshadow = payload.get("foreshadow_anchors") or []
        if isinstance(foreshadow, list):
            anchors: list[str] = []
            for item in foreshadow[:6]:
                if isinstance(item, dict):
                    if not cls._entry_visible_in_episode(item, ep_num):
                        continue
                    text = str(
                        item.get("anchor", "")
                        or item.get("text", "")
                        or item.get("summary", "")
                        or item.get("description", "")
                    ).strip()[:120]
                else:
                    text = str(item).strip()[:120]
                if not text:
                    continue
                anchors.append(text)
                if len(anchors) >= 3:
                    break
            if anchors:
                normalized["foreshadow_anchors"] = anchors

        # [W2] continuity_checkpoints: suppressed — describes arc-end
        # completion state that reads as current-episode obligation.

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

        # [W2] growth_justification: suppressed (arc-end achievement fuel)
        # [W2] continuity_checkpoints: suppressed (arc-end completion state)

        for anchor in (payload.get("foreshadow_anchors", []) or [])[:3]:
            text = str(anchor or "").strip()
            if text:
                lines.append(f"- [미래 복선 참고용] foreshadow: {text[:120]}")

        return lines


def create_blueprint_constraint_compiler():
    """BlueprintConstraintCompiler 생성 헬퍼"""
    return BlueprintConstraintCompiler()
