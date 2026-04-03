"""
[B-1-4] ChiefWriter Context Builder — context assembly and analysis helpers.
"""

import json
import logging
import re

from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False

from .chief_writer_context_packets import ChiefWriterContextPackets
from .chief_writer_prompts import (
    build_chief_writer_main_prompt,
    get_anti_trope_instructions,
    get_common_rules_section,
    get_modern_origin_section,
    get_primitive_constraint_fallback,
    get_satisfaction_guide_section,
    get_writing_guidelines_investment_only,
    get_writing_guidelines_section,
)

_GENRE_CODE_ALIASES = {
    "무협": "wuxia",
    "wuxia": "wuxia",
    "판타지": "fantasy",
    "fantasy": "fantasy",
    "헌터물": "hunter",
    "hunter": "hunter",
    "투자물": "investment",
    "투자": "investment",
    "investment": "investment",
    "investment fiction": "investment",
    "투자 (investment fiction)": "investment",
    "배우물": "actor",
    "actor": "actor",
    "스포츠": "sports",
    "sports": "sports",
    "의학": "medical",
    "medical": "medical",
    "요리": "cooking",
    "cooking": "cooking",
    "작곡가": "composer",
    "composer": "composer",
    "대체역사": "alt_history",
    "alt_history": "alt_history",
    "alt history": "alt_history",
}

_STAGE4_WORK_IDENTITY_AUTHORITY_HEADER = "[Stage4 Work Identity Authority]"
_STAGE4_OPENING_SCENE_AUTHORITY_HEADER = "[Stage4 Opening Scene Authority]"


def _normalize_genre_alias_key(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def normalize_chief_writer_genre_code(
    genre_name: str = "",
    *,
    genre_type: str = "",
    bible_root: dict | None = None,
    default: str = "wuxia",
) -> str:
    for candidate in (genre_name, genre_type):
        key = _normalize_genre_alias_key(candidate)
        if key and key in _GENRE_CODE_ALIASES:
            return _GENRE_CODE_ALIASES[key]

    if isinstance(bible_root, dict):
        raw_genre = str(bible_root.get("_genre", "") or "").strip()
        key = _normalize_genre_alias_key(raw_genre)
        if key and key in _GENRE_CODE_ALIASES:
            return _GENRE_CODE_ALIASES[key]
        if raw_genre:
            return raw_genre

    return default


class ChiefWriterContextBuilder:
    """ChiefWriter의 컨텍스트 빌딩 + 분석 담당 서브모듈."""

    def __init__(self, host) -> None:
        self.host = host
        self.context_packets = ChiefWriterContextPackets(self)

    @property
    def context(self):
        return self.host.context

    def _fit_compact_text(self, value: object, max_chars: int, head_ratio: float = 0.55) -> str:
        text = "" if value is None else str(value)
        if len(text) <= max_chars:
            return text
        if max_chars <= 6:
            return text[:max_chars]
        sep = "..."
        budget = max_chars - len(sep)
        head_chars = max(8, min(budget - 8, int(budget * head_ratio)))
        tail_chars = budget - head_chars
        if tail_chars <= 0:
            return text[:max_chars]
        return text[:head_chars] + sep + text[-tail_chars:]

    def build_common_context(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str,
        director_feedback: str,
        failure_constraints: str,
        reference_excerpt: str = "",
        # 미래 침범 방지
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # 기존 Writer 핵심 기능
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "",  # [QI-1-C3] CYNICAL 하드코딩 제거
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
        # [ending_hook] 현재 화 마무리 훅
        ending_hook_section: str = "",
        # [emotional_beat] 감정 정점
        emotional_beat_section: str = "",
        # [TF-49b] Arc 계획 아이템 사전 정당화
        upcoming_arc_items: list[str] = None,
        # [TF-54c] 동적 집필 지시
        writing_directive=None,
    ) -> str:
        """
        [V60.81] 공통 컨텍스트 구성 (CoT 기반 + Writer 핵심 기능 완전 통합)

        추가된 기능:
        - NPC 장비 현황
        - NPC 등장 빈도 경고
        - HUD 변화 추세
        - DNA 모드 (1화 특수)
        - HUD 급변 감지
        - [V60.85] 장르 Guard Purism Prompt 주입
        - [V67] 이전 원고 전문 (모순 방지용 컨텍스트)
        - [V68] 세계 상태 요약 (장기연재 모순 방지)
        """
        current_inventory = current_inventory or []
        current_martial_arts = current_martial_arts or []
        dead_npcs = dead_npcs or []

        scene_breakdown, integrated_scenario_advisory, ending_hook, opening_anchor_section = (
            self._extract_blueprint_sections(blueprint)
        )
        (
            bible_root,
            core_identity,
            protagonist_config,
            world_origin,
            incarnation_type,
        ) = self._extract_bible_context(master_bible)
        genre_code = self._resolve_genre_code(genre_name, bible_root)

        packet_sections = self.context_packets.build_common_context_packets(
            ep_num=ep_num,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            current_inventory=current_inventory,
            current_martial_arts=current_martial_arts,
            dead_npcs=dead_npcs,
            item_acquisition_timeline=item_acquisition_timeline,
            master_bible=master_bible,
            hud_report=hud_report,
            intro_dna=intro_dna,
            state_tracker=state_tracker,
            prev_manuscripts_text=prev_manuscripts_text,
            upcoming_arc_items=upcoming_arc_items,
        )

        # [IFC] Build immutable fact packet — after packet_sections so prev_digest is available
        immutable_fact_section = self._build_immutable_fact_section(
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            world_state_summary=world_state_summary,
            chain_link_section=chain_link_section,
            prev_digest=packet_sections.get("prev_digest", ""),
        )

        writing_directive = self._resolve_writing_directive(writing_directive)
        writer_hard_canon_section, writer_soft_guidance_section = self._build_writer_core_sections(
            blueprint=blueprint,
            world_state_section=self._build_world_state_section(world_state_summary),
            writing_directive=writing_directive,
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=mandatory_context,
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
        )
        writer_core_section = self._join_writer_sections(
            writer_hard_canon_section,
            writer_soft_guidance_section,
        )
        writing_guidelines = get_writing_guidelines_section()
        if genre_code == "investment":
            writing_guidelines += get_writing_guidelines_investment_only()

        return build_chief_writer_main_prompt(
            ep_num=ep_num,
            dna_instruction=packet_sections["dna_instruction"],
            purism_section=self._build_purism_section(purism_prompt),
            world_origin_constraint_section=self._build_world_origin_constraint_section(
                world_origin,
                protagonist_config,
                genre_code,
            ),
            feedback_section=self._build_feedback_section(director_feedback),
            constraint_section=self._build_constraint_section(failure_constraints),
            future_guard_section=packet_sections["future_guard_section"],
            past_guard_section=packet_sections["past_guard_section"],
            writer_core_section=writer_core_section,
            writer_hard_canon_section=self.host._escape_braces(writer_hard_canon_section)
            if writer_hard_canon_section
            else "",
            writer_soft_guidance_section=self.host._escape_braces(writer_soft_guidance_section)
            if writer_soft_guidance_section
            else "",
            hud_anomaly_section=packet_sections["hud_anomaly_section"],
            scene_breakdown=self.host._escape_braces(scene_breakdown),
            prev_digest=self.host._escape_braces(packet_sections["prev_digest"]),
            prev_ending=self.host._escape_braces(packet_sections["prev_ending"]),
            hud_report=self.host._escape_braces(hud_report),
            high_density_hud_section=packet_sections["high_density_hud_section"],
            hud_trend_section=packet_sections["hud_trend_section"],
            npc_equipment_section=packet_sections["npc_equipment_section"],
            npc_frequency_section=packet_sections["npc_frequency_section"],
            arc_doc=self.host._escape_braces(arc_doc) if arc_doc else "특이사항 없음",
            core_identity_desire=self.host._escape_braces(str(core_identity.get("desire", ""))),
            style_guide=self.host._escape_braces(style_guide) if style_guide else "기본 웹소설 문체",
            reference_excerpt_section=self._build_reference_excerpt_section(reference_excerpt),
            common_rules=get_common_rules_section(),
            writing_guidelines=writing_guidelines,
            prev_manuscripts_section=packet_sections["prev_manuscripts_section"],  # [V67]
            incarnation_context_section=self._build_incarnation_context_section(incarnation_type),  # [V67.1]
            chain_link_section=self.host._escape_braces(chain_link_section) if chain_link_section else "",  # [V68]
            ending_hook_section=self.host._escape_braces(ending_hook) if ending_hook else "",
            emotional_beat_section=self.host._escape_braces(emotional_beat_section) if emotional_beat_section else "",
            satisfaction_guide_section=get_satisfaction_guide_section(),  # [D-Step2]
            opening_anchor_section=self.host._escape_braces(opening_anchor_section) if opening_anchor_section else "",  # [TF-2]
            immutable_fact_section=self.host._escape_braces(immutable_fact_section) if immutable_fact_section else "",  # [IFC]
            integrated_scenario_advisory_section=self.host._escape_braces(integrated_scenario_advisory)
            if integrated_scenario_advisory
            else "",
            carryover_ceiling_section=self.host._escape_braces(packet_sections.get("carryover_ceiling_section", ""))
            if packet_sections.get("carryover_ceiling_section", "")
            else "",
        )

    def _extract_blueprint_sections(self, blueprint: dict) -> tuple[str, str, str, str]:
        scene_breakdown = ""
        integrated_scenario_advisory = ""
        ending_hook = ""
        opening_anchor_section = ""
        if not isinstance(blueprint, dict):
            return scene_breakdown, integrated_scenario_advisory, ending_hook, opening_anchor_section

        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, dict):
            scene_breakdown = json.dumps(scenes, ensure_ascii=False, indent=2)
        integrated = blueprint.get("integrated_scenario_advisory", "") or blueprint.get("integrated_scenario", "")
        if integrated:
            integrated_scenario_advisory = (
                "### [Advisory] 통합 시나리오 초안 (낮은 우선순위)\n"
                "이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / writer hard canon / prev digest / "
                "structured scene contract와 충돌하면 아래 prose는 버려라.\n"
                "이 prose의 요약/브리핑/HUD/상태창/시스템 문구를 그대로 답습하지 말고, 정본에 없는 메타 표현은 재사용하지 마라.\n"
                f"{integrated}"
            )
        hook = blueprint.get("ending_hook", "")
        if hook:
            ending_hook = f"### 이 화의 마무리 훅\n{hook}"

        # [TF-2] Opening-Anchor Packet — blueprint에서 첫 씬 불변 계약 추출
        _start_loc = blueprint.get("start_location", "")
        _time_flow = blueprint.get("time_flow", "")
        _scene_1 = {}
        if isinstance(scenes, dict):
            _scene_1 = scenes.get("scene_1") or next(iter(scenes.values()), {})
            if not isinstance(_scene_1, dict):
                _scene_1 = {}
        _s1_title = _scene_1.get("title", "")
        _s1_summary = _scene_1.get("summary", "") or _scene_1.get("goal", "")
        _s1_location = _scene_1.get("location", "")

        if _start_loc or _time_flow or _s1_title:
            anchor_parts = ["### ⚓ [TF-2] 이 화의 시작 계약 (불변)"]
            anchor_parts.append("이 화의 첫 씬은 아래 조건을 반드시 지켜야 한다. 임의로 바꾸면 불합격이다.")
            if _start_loc:
                anchor_parts.append(f"- 시작 장소: {_start_loc}")
            if _s1_location and _s1_location != _start_loc:
                anchor_parts.append(f"- 첫 씬 세부 장소: {_s1_location}")
            if _time_flow:
                anchor_parts.append(f"- 시간대: {_time_flow}")
            if _s1_title:
                anchor_parts.append(f"- 첫 씬 제목/목표: {_s1_title}")
            if _s1_summary:
                anchor_parts.append(f"- 첫 씬 요약: {_s1_summary[:200]}")
            anchor_parts.append(
                "다른 장소/시간 또는 다른 시점 opening이 필요하면 전환 문장이나 `* * *` 후 1~2문장 안에 "
                "바뀐 장소/시간/행동 상태를 명시하고, 다른 시점이면 작품 POV 정책을 어기지 마라."
            )
            anchor_parts.append(
                "⛔ 위 anchor를 무전환으로 덮어쓰거나 직전 화에서 이미 끝난 행동을 opening에서 다시 재연하면 즉시 불합격 처리된다."
            )
            opening_anchor_section = "\n".join(anchor_parts)

        return scene_breakdown, integrated_scenario_advisory, ending_hook, opening_anchor_section

    def _extract_bible_context(self, master_bible: dict) -> tuple[dict, dict, dict, str, str]:
        bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
        core_identity = bible_root.get("ProjectData", {}).get("CoreIdentity", {})
        protagonist_config = bible_root.get("protagonist_config", {})
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "")
        return bible_root, core_identity, protagonist_config, world_origin, incarnation_type

    def _build_incarnation_context_section(self, incarnation_type: str) -> str:
        if incarnation_type == "회귀자":
            return """
### [V67.1] 회귀자 집필 가이드
주인공은 미래에서 되돌아온 회귀자입니다.
- 미래의 사건/인물/가격 등을 미리 아는 것이 당연합니다
- 내면 독백에서 "전생에서는...", "원래라면..." 같은 회고가 자연스럽습니다
- 주인공이 역사를 의도적으로 바꾸려는 행동은 핵심 서사입니다
- 단, NPC에게 미래 정보를 직접 말하면 어색합니다 (합리적 이유 필요)
"""
        if incarnation_type == "빙의자":
            return """
### [V67.1] 빙의자 집필 가이드
주인공은 다른 인물의 몸에 빙의한 존재입니다.
- 원래 인물의 기억이 부분적으로 떠오를 수 있습니다
- 원래 인물과 다른 반응/성격을 보이면 주변이 의아해합니다
- "이 몸의 주인은..." 같은 내면 갈등이 자연스럽습니다
"""
        if incarnation_type == "환생자":
            return """
### [V67.1] 환생자 집필 가이드
주인공은 전생의 기억을 가진 환생자입니다.
- 전생의 지식/기술이 단편적으로 떠오를 수 있습니다
- 현생의 몸이 전생의 능력을 완전히 재현하지 못할 수 있습니다
"""
        return ""

    def _resolve_selected_genre_type(self) -> str:
        try:
            return str((self.host.context.selected_genre or {}).get("type", "") or "")
        except Exception:
            return ""

    def _resolve_genre_code(self, genre_name: str, bible_root: dict) -> str:
        return normalize_chief_writer_genre_code(
            genre_name,
            genre_type=self._resolve_selected_genre_type(),
            bible_root=bible_root,
            default="wuxia",
        )

    def _build_world_origin_constraint_section(
        self,
        world_origin: str,
        protagonist_config: dict,
        genre_code: str,
    ) -> str:
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                return get_primitive_constraint_section(protagonist_config, genre=genre_code, length="build")
            return get_primitive_constraint_fallback()
        if world_origin == "현대인":
            return get_modern_origin_section()
        return ""

    def _build_feedback_section(self, director_feedback: str) -> str:
        if not director_feedback:
            return ""
        return f"""
### 🚨 [Director 피드백 - 반드시 반영]
{self.host._escape_braces(director_feedback)}
"""

    def _build_constraint_section(self, failure_constraints: str) -> str:
        if not failure_constraints:
            return ""
        return f"""
### 주의 [이전 REJECT 패턴 - 회피 필수]
{self.host._escape_braces(failure_constraints)}
"""

    def _build_world_state_section(self, world_state_summary: str) -> str:
        if not world_state_summary:
            return ""
        return f"""
### [V68] 세계 상태 문서 (World State) — 반드시 참조
{self.host._escape_braces(world_state_summary)}
⚠️ 위 세계 상태와 모순되는 묘사/대사/사건은 절대 금지.
"""

    def _resolve_writing_directive(self, writing_directive):
        if writing_directive is not None:
            return writing_directive
        return getattr(self.host, "_tf54_writing_directive", None)

    def _build_writing_directive_section(self, writing_directive) -> str:
        if not writing_directive or not hasattr(writing_directive, "is_empty") or writing_directive.is_empty():
            return ""

        directive_lines = [
            "### 이번 화 집필 지시 (WritingDirective)",
            "**반드시 준수하세요. Director가 이 지시의 준수 여부를 평가합니다.**",
            "",
        ]
        if getattr(writing_directive, "ending_style", ""):
            directive_lines.append(
                f"- 마무리 방식: {self.host._escape_braces(str(getattr(writing_directive, 'ending_style', '')))}"
            )
        ending_avoid_phrases = list(getattr(writing_directive, "ending_avoid_phrases", []) or [])
        if ending_avoid_phrases:
            directive_lines.append(
                f"- 피할 엔딩 문구: {self.host._escape_braces(', '.join(str(item) for item in ending_avoid_phrases[:5]))}"
            )
        expression_ban = list(getattr(writing_directive, "expression_ban", []) or [])
        if expression_ban:
            directive_lines.append(
                f"- 금지 표현: {self.host._escape_braces(', '.join(str(item) for item in expression_ban))}"
            )
        metaphor_avoid = list(getattr(writing_directive, "metaphor_avoid", []) or [])
        if metaphor_avoid:
            directive_lines.append(
                f"- 피할 은유: {self.host._escape_braces(', '.join(str(item) for item in metaphor_avoid))}"
            )
        metaphor_suggest = list(getattr(writing_directive, "metaphor_suggest", []) or [])
        if metaphor_suggest:
            directive_lines.append(
                f"- 추천 은유: {self.host._escape_braces(', '.join(str(item) for item in metaphor_suggest))}"
            )
        if getattr(writing_directive, "emotion_required", ""):
            directive_lines.append(
                f"- 감정 요구: {self.host._escape_braces(str(getattr(writing_directive, 'emotion_required', '')))}"
            )
        npc_directives = getattr(writing_directive, "npc_directives", {}) or {}
        if isinstance(npc_directives, dict) and npc_directives:
            npc_pairs = ", ".join(f"{key}: {value}" for key, value in npc_directives.items())
            directive_lines.append(f"- NPC 지시: {self.host._escape_braces(npc_pairs)}")
        if getattr(writing_directive, "intensity_note", ""):
            directive_lines.append(
                f"- 강도 가이드: {self.host._escape_braces(str(getattr(writing_directive, 'intensity_note', '')))}"
            )
        return "\n".join(directive_lines)

    def _collect_blueprint_npc_names(self, blueprint: dict) -> list[str]:
        npc_names = []
        if not isinstance(blueprint, dict):
            return npc_names

        for scene in (blueprint.get("scene_breakdown") or {}).values():
            if isinstance(scene, dict):
                npc_names.extend(scene.get("npcs", []))
        return npc_names

    def _build_character_voice_section(self, blueprint: dict) -> str:
        context_obj = getattr(self.host, "context", None)
        character_voice = getattr(context_obj, "character_voice", None) if context_obj else None
        if character_voice is None:
            stage4_context = getattr(self.host, "_stage4_ctx", None)
            character_voice = getattr(stage4_context, "character_voice", None) if stage4_context else None
        if not character_voice or not hasattr(character_voice, "get_writing_guide"):
            return ""

        try:
            npc_names = self._collect_blueprint_npc_names(blueprint)
            guide = character_voice.get_writing_guide(npc_names) if npc_names else ""
            if guide:
                return f"\n### [I-25] 캐릭터 보이스 가이드\n{guide}\n"
        except Exception as error:
            logging.debug(f"[I-25] character_voice guide failed (non-blocking): {error}")
        return ""

    @staticmethod
    def _join_writer_sections(*sections: str) -> str:
        parts = [section.strip() for section in sections if section and section.strip()]
        return "\n\n".join(parts)

    @staticmethod
    def _extract_named_context_block(text: str, header: str) -> str:
        if not text or not header:
            return ""
        try:
            match = re.search(rf"({re.escape(header)}.*?)(?:\n\n(?=\[)|\Z)", str(text), flags=re.DOTALL)
        except re.error:
            return ""
        return match.group(1).strip() if match else ""

    def _build_writer_core_sections(
        self,
        *,
        blueprint: dict,
        world_state_section: str,
        writing_directive,
        reference_anchor_prompt: str,
        mandatory_context: str,
        anti_trope_prompt: str,
        justification_prompt: str,
        reflexion_prompt: str,
    ) -> tuple[str, str]:
        character_voice_section = self._build_character_voice_section(blueprint)
        opening_scene_authority = self._extract_named_context_block(
            mandatory_context,
            _STAGE4_OPENING_SCENE_AUTHORITY_HEADER,
        )
        work_identity_authority = self._extract_named_context_block(
            mandatory_context,
            _STAGE4_WORK_IDENTITY_AUTHORITY_HEADER,
        )
        hard_canon_section = self._join_writer_sections(
            opening_scene_authority,
            work_identity_authority,
            world_state_section,
            reference_anchor_prompt,
            mandatory_context,
        )
        soft_guidance_section = self._join_writer_sections(
            character_voice_section,
            self._build_writing_directive_section(writing_directive),
            anti_trope_prompt,
            justification_prompt,
            reflexion_prompt,
        )
        return hard_canon_section, soft_guidance_section

    def _build_immutable_fact_section(
        self,
        *,
        blueprint: dict,
        prev_manuscript: str,
        world_state_summary: str,
        chain_link_section: str,
        prev_digest: str = "",
    ) -> str:
        """[IFC] Build immutable fact contract section for CW prompt."""
        try:
            from modules.core.stage4_immutable_fact_contract import build_packet, render_packet_for_cw

            # [Wave1-A] Derive actual fact-ledger summary from context
            fact_ledger_text = ""
            try:
                fl = getattr(self.context, "fact_ledger", None)
                if fl is None:
                    _s4ctx = getattr(self.host, "_stage4_ctx", None)
                    fl = getattr(_s4ctx, "fact_ledger", None) if _s4ctx else None
                if fl is not None and hasattr(fl, "to_summary"):
                    fact_ledger_text = fl.to_summary(max_chars=25000) or ""
            except Exception:
                pass

            packet = build_packet(
                blueprint=blueprint,
                prev_manuscript_ending=prev_manuscript[-2500:] if prev_manuscript else "",
                world_state_summary=world_state_summary,
                fact_ledger_summary=fact_ledger_text,
                chain_link_section=chain_link_section,
                prev_digest=prev_digest,
            )
            return render_packet_for_cw(packet)
        except Exception as e:
            logging.debug("[IFC] immutable fact section build failed (non-blocking): %s", e)
            return ""

    def _build_purism_section(self, purism_prompt: str) -> str:
        if not purism_prompt:
            return ""
        return f"""
### 엄금[장르 순혈주의 위반 시 즉시 수정]
{self.host._escape_braces(purism_prompt)}
"""

    def _build_reference_excerpt_section(self, reference_excerpt: str) -> str:
        if not reference_excerpt:
            return ""
        return f"\n## 참고 원고 발췌 (※문체를 따라 쓰지 말 것)\n{self.host._escape_braces(reference_excerpt)}"

    def _get_hud_trend_safe(self, ep_num: int) -> str:
        """[V64.P4] 위임 → modules.core.hud_utils.get_hud_trend_safe"""
        return _get_hud_trend_safe_shared(self.context, ep_num)

    def _extract_numeric_value(self, value) -> int:
        """HUD 값에서 숫자 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            match = re.search(r"[+-]?\d+", value)
            if match:
                return int(match.group())
        return 0

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (writer variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="writer")

    def _build_anti_trope_instructions(self, genre_name: str) -> str:
        """
        [V60.81] 반클리셰 명령 생성

        ChiefWriter가 독립적으로 동작할 수 있도록 내장
        [V65] 프롬프트 본문 함수 래핑 호출
        """
        return get_anti_trope_instructions(genre_name=genre_name)
