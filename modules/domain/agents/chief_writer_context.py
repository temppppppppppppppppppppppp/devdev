"""
[B-1-4] ChiefWriter Context Builder — context assembly and analysis helpers.
"""

import json
import logging
import re

from modules.core.constants import smart_truncate
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

        # Blueprint에서 씬 정보 추출
        scene_breakdown = ""
        ending_hook = ""
        if isinstance(blueprint, dict):
            scenes = blueprint.get("scene_breakdown", {})
            if isinstance(scenes, dict):
                scene_breakdown = json.dumps(scenes, ensure_ascii=False, indent=2)
            integrated = blueprint.get("integrated_scenario", "")
            if integrated:
                scene_breakdown += f"\n\n통합 시나리오:\n{integrated}"
            _eh = blueprint.get("ending_hook", "")
            if _eh:
                ending_hook = f"### 이 화의 마무리 훅\n{_eh}"

        # 마스터 바이블에서 핵심 정보 추출
        bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
        core_identity = bible_root.get("ProjectData", {}).get("CoreIdentity", {})
        # [V60.95] 주인공 설정 추출 (원시인/현대인 제약)
        protagonist_config = bible_root.get("protagonist_config", {})
        world_origin = protagonist_config.get("world_origin", "원시인")
        # [Sweep45] 기본값 "" — 미설정 프로젝트에 회귀자 가이드 주입 방지
        incarnation_type = protagonist_config.get("incarnation_type", "")

        # [V67.1] 환생 유형별 집필 맥락 주입
        incarnation_context_section = ""
        if incarnation_type == "회귀자":
            incarnation_context_section = """
### [V67.1] 회귀자 집필 가이드
주인공은 미래에서 되돌아온 회귀자입니다.
- 미래의 사건/인물/가격 등을 미리 아는 것이 당연합니다
- 내면 독백에서 "전생에서는...", "원래라면..." 같은 회고가 자연스럽습니다
- 주인공이 역사를 의도적으로 바꾸려는 행동은 핵심 서사입니다
- 단, NPC에게 미래 정보를 직접 말하면 어색합니다 (합리적 이유 필요)
"""
        elif incarnation_type == "빙의자":
            incarnation_context_section = """
### [V67.1] 빙의자 집필 가이드
주인공은 다른 인물의 몸에 빙의한 존재입니다.
- 원래 인물의 기억이 부분적으로 떠오를 수 있습니다
- 원래 인물과 다른 반응/성격을 보이면 주변이 의아해합니다
- "이 몸의 주인은..." 같은 내면 갈등이 자연스럽습니다
"""
        elif incarnation_type == "환생자":
            incarnation_context_section = """
### [V67.1] 환생자 집필 가이드
주인공은 전생의 기억을 가진 환생자입니다.
- 전생의 지식/기술이 단편적으로 떠오를 수 있습니다
- 현생의 몸이 전생의 능력을 완전히 재현하지 못할 수 있습니다
"""

        # [V60.96] 장르 코드 변환 (장르별 금지어 적용)
        genre_type = ""
        try:
            genre_type = str((self.host.context.selected_genre or {}).get("type", "") or "")
        except Exception:
            genre_type = ""
        genre_code = normalize_chief_writer_genre_code(
            genre_name,
            genre_type=genre_type,
            bible_root=bible_root,
            default="wuxia",
        )

        # [V60.96] 원시인 모드 제약 섹션 (장르별 JSON 기반 PrimitiveGuard)
        world_origin_constraint_section = ""
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                # 장르별 JSON 기반 동적 생성
                world_origin_constraint_section = get_primitive_constraint_section(
                    protagonist_config, genre=genre_code, length="build"
                )
            else:
                # [V65] 폴백: 최소한의 경고
                world_origin_constraint_section = get_primitive_constraint_fallback()
        elif world_origin == "현대인":
            world_origin_constraint_section = get_modern_origin_section()  # [V65]

        # [V62.6→V63.2] 직전 원고: 구조화 다이제스트 + 엔딩 2500자 (800→2500 확대)
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
        prev_ending = packet_sections["prev_ending"]
        prev_digest = packet_sections["prev_digest"]
        future_guard_section = packet_sections["future_guard_section"]
        past_guard_section = packet_sections["past_guard_section"]
        npc_equipment_section = packet_sections["npc_equipment_section"]
        npc_frequency_section = packet_sections["npc_frequency_section"]
        hud_trend_section = packet_sections["hud_trend_section"]
        hud_anomaly_section = packet_sections["hud_anomaly_section"]
        dna_instruction = packet_sections["dna_instruction"]
        high_density_hud_section = packet_sections["high_density_hud_section"]
        prev_manuscripts_section = packet_sections["prev_manuscripts_section"]

        # Director 피드백 섹션
        feedback_section = ""
        if director_feedback:
            feedback_section = f"""
### 🚨 [Director 피드백 - 반드시 반영]
{self.host._escape_braces(director_feedback)}
"""

        # 실패 학습 제약
        constraint_section = ""
        if failure_constraints:
            constraint_section = f"""
### ⚠️ [이전 REJECT 패턴 - 회피 필수]
{self.host._escape_braces(failure_constraints)}
"""
        # [V68] 세계 상태 요약 섹션 (최우선 주입)
        world_state_section = ""
        if world_state_summary:
            world_state_section = f"""
### [V68] 세계 상태 문서 (World State) — 반드시 참조
{self.host._escape_braces(world_state_summary)}
⚠️ 위 세계 상태와 모순되는 묘사/대화/사건은 절대 금지.
"""

        # [TF-54c] WritingDirective 섹션 주입
        if writing_directive is None:
            writing_directive = getattr(self.host, "_tf54_writing_directive", None)
        writing_directive_section = ""
        if writing_directive and hasattr(writing_directive, "is_empty") and not writing_directive.is_empty():
            _wd_lines = [
                "### 이번 화 집필 지시 (WritingDirective)",
                "**반드시 준수하세요. Director가 이 지시의 준수 여부를 평가합니다.**",
                "",
            ]
            if getattr(writing_directive, "ending_style", ""):
                _wd_lines.append(
                    f"- 마무리 방식: {self.host._escape_braces(str(getattr(writing_directive, 'ending_style', '')))}"
                )
            # [QI-1-A4] 엔딩 회피 문구 주입
            _ending_avoid = list(getattr(writing_directive, "ending_avoid_phrases", []) or [])
            if _ending_avoid:
                _wd_lines.append(
                    f"- 피할 엔딩 문구: {self.host._escape_braces(', '.join(str(x) for x in _ending_avoid[:5]))}"
                )
            _exp_ban = list(getattr(writing_directive, "expression_ban", []) or [])
            if _exp_ban:
                _wd_lines.append(f"- 금지 표현: {self.host._escape_braces(', '.join(str(x) for x in _exp_ban))}")
            _meta_avoid = list(getattr(writing_directive, "metaphor_avoid", []) or [])
            if _meta_avoid:
                _wd_lines.append(f"- 피할 은유: {self.host._escape_braces(', '.join(str(x) for x in _meta_avoid))}")
            _meta_suggest = list(getattr(writing_directive, "metaphor_suggest", []) or [])
            if _meta_suggest:
                _wd_lines.append(f"- 추천 은유: {self.host._escape_braces(', '.join(str(x) for x in _meta_suggest))}")
            if getattr(writing_directive, "emotion_required", ""):
                _wd_lines.append(
                    f"- 감정 요구: {self.host._escape_braces(str(getattr(writing_directive, 'emotion_required', '')))}"
                )
            _npc_directives = getattr(writing_directive, "npc_directives", {}) or {}
            if isinstance(_npc_directives, dict) and _npc_directives:
                _npc_pairs = ", ".join(f"{k}: {v}" for k, v in _npc_directives.items())
                _wd_lines.append(f"- NPC 지시: {self.host._escape_braces(_npc_pairs)}")
            if getattr(writing_directive, "intensity_note", ""):
                _wd_lines.append(
                    f"- 강도 가이드: {self.host._escape_braces(str(getattr(writing_directive, 'intensity_note', '')))}"
                )
            writing_directive_section = "\n".join(_wd_lines)

        # [I-25] 캐릭터 보이스 섹션 주입
        character_voice_section = ""
        _cv = getattr(self.host, "context", None)
        _cv_module = getattr(_cv, "character_voice", None) if _cv else None
        if _cv_module is None:
            # Stage4Context에서도 탐색
            _s4ctx = getattr(self.host, "_stage4_ctx", None)
            _cv_module = getattr(_s4ctx, "character_voice", None) if _s4ctx else None
        if _cv_module and hasattr(_cv_module, "get_writing_guide"):
            try:
                # blueprint에서 등장 NPC 이름 추출
                _npc_names = []
                if isinstance(blueprint, dict):
                    for _scene in (blueprint.get("scene_breakdown") or {}).values():
                        if isinstance(_scene, dict):
                            _npc_names.extend(_scene.get("npcs", []))
                _guide = _cv_module.get_writing_guide(_npc_names) if _npc_names else ""
                if _guide:
                    character_voice_section = f"\n### [I-25] 캐릭터 보이스 가이드\n{_guide}\n"
            except Exception as _cv_err:
                logging.debug(f"[I-25] character_voice guide failed (non-blocking): {_cv_err}")

        # [V60.80+] 기존 Writer 핵심 기능 섹션 조립
        writer_core_section = ""
        if character_voice_section:
            writer_core_section += character_voice_section
        if world_state_section:
            writer_core_section += f"\n{world_state_section}\n"
        if writing_directive_section:
            writer_core_section += f"\n{writing_directive_section}\n"
        if reference_anchor_prompt:
            writer_core_section += f"\n{reference_anchor_prompt}\n"
        if mandatory_context:
            writer_core_section += f"\n{mandatory_context}\n"
        if anti_trope_prompt:
            writer_core_section += f"\n{anti_trope_prompt}\n"
        if justification_prompt:
            writer_core_section += f"\n{justification_prompt}\n"
        if reflexion_prompt:
            writer_core_section += f"\n{reflexion_prompt}\n"

        # [V60.85] 장르 Guard Purism 섹션
        purism_section = ""
        if purism_prompt:
            purism_section = f"""
### 🛡️ [장르 순혈주의 절대 준수]
{self.host._escape_braces(purism_prompt)}
"""

        _investment_guidelines = get_writing_guidelines_investment_only() if genre_code == "investment" else ""
        reference_excerpt_section = (
            f"\n## 참조 원고 발췌 (이 문체를 따라 쓸 것)\n{self.host._escape_braces(reference_excerpt)}"
            if reference_excerpt
            else ""
        )

        # [V65] 메인 프롬프트 함수 래핑 호출
        return build_chief_writer_main_prompt(
            ep_num=ep_num,
            dna_instruction=dna_instruction,
            purism_section=purism_section,
            world_origin_constraint_section=world_origin_constraint_section,
            feedback_section=feedback_section,
            constraint_section=constraint_section,
            future_guard_section=future_guard_section,
            past_guard_section=past_guard_section,
            writer_core_section=writer_core_section,
            hud_anomaly_section=hud_anomaly_section,
            scene_breakdown=self.host._escape_braces(scene_breakdown),
            prev_digest=self.host._escape_braces(prev_digest),
            prev_ending=self.host._escape_braces(prev_ending),
            hud_report=self.host._escape_braces(hud_report),
            high_density_hud_section=high_density_hud_section,
            hud_trend_section=hud_trend_section,
            npc_equipment_section=npc_equipment_section,
            npc_frequency_section=npc_frequency_section,
            arc_doc=self.host._escape_braces(arc_doc) if arc_doc else "특이사항 없음",
            core_identity_desire=self.host._escape_braces(str(core_identity.get("desire", ""))),
            style_guide=self.host._escape_braces(style_guide) if style_guide else "기본 웹소설 문체",
            reference_excerpt_section=reference_excerpt_section,
            common_rules=get_common_rules_section(),
            writing_guidelines=get_writing_guidelines_section() + _investment_guidelines,
            prev_manuscripts_section=prev_manuscripts_section,  # [V67]
            incarnation_context_section=incarnation_context_section,  # [V67.1]
            chain_link_section=self.host._escape_braces(chain_link_section) if chain_link_section else "",  # [V68]
            ending_hook_section=self.host._escape_braces(ending_hook) if ending_hook else "",
            emotional_beat_section=self.host._escape_braces(emotional_beat_section) if emotional_beat_section else "",
            satisfaction_guide_section=get_satisfaction_guide_section(),  # [D-Step2]
        )

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


