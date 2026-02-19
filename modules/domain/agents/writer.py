"""
[V64] Writer - Thin Fallback Agent

독립 API로 유지 (오케스트레이터 호출 경로 제거됨).
원래 2,580줄 → 500줄 이하로 경량화.

삭제된 기능 (ChiefWriter에 이미 존재):
  - SCENE_PRESETS / get_scene_preset_guide
  - Emotion Skeleton 시스템 전체
  - self_review_and_refine / quick_self_check
  - write_manuscript_by_beats (Beat 분할 생성)
  - identify_problem_scenes / partial_rewrite
  - refine_with_editor
  - Multi-round Self-Critique (단순 Python 체크로 대체)
"""

import json
import re

from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared  # [V64.P4]
from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope_instructions_shared,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification_guidance_shared,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_mandatory_context_shared,
)

from .base_agent import BaseAgent


class Writer(BaseAgent):
    """[V64] Thin Fallback Writer — ChiefWriter 실패 시 최후 폴백 전용"""

    def __init__(self, context, client, model_tier="gemini-1.5-pro") -> None:
        super().__init__(context, client, model_tier)
        self.cache_name = None  # main_a.py에서 주입됨
        self.last_hud_anomalies = None
        self.guard = None
        self.genre = "wuxia"

    def set_guard(self, guard) -> None:
        """장르 Guard 설정"""
        self.guard = guard

    def set_genre(self, genre: str):
        """장르 설정"""
        self.genre = genre

    # ==================================================================
    # 핵심 생성 메서드 (main_a.py line ~6600 에서 호출)
    # ==================================================================

    def write_v20_manuscript(
        self,
        ep_num,
        breakdown_doc,
        master_bible,
        hud_report,
        purism_prompt,
        style_mode="",
        intro_dna="CYNICAL",
        feedback="",
        prev_full_manuscript="",
        arc_doc="",
        tactical_references="",
        protagonist_name="주인공",
        entity_registry=None,
    ):
        """[V64 Slim] 냉동인간 폴백 생성"""
        # 1. 데이터 추출
        focus_info = arc_doc if isinstance(arc_doc, dict) else {}
        focus_tag = focus_info.get("MUST_FOCUS_ON", "N/A")
        pattern_profile = focus_info.get("PATTERN_PROFILE", {})
        pattern_logic = focus_info.get("PATTERN_MIXING_LOGIC", "")
        pattern_primary = (
            pattern_profile.get("primary", "패턴 정보 없음") if isinstance(pattern_profile, dict) else "패턴 정보 없음"
        )
        pattern_secondary = pattern_profile.get("secondary", []) if isinstance(pattern_profile, dict) else []

        bible_root = master_bible.get("MasterBible", master_bible)
        core_identity = bible_root.get("ProjectData", {}).get("CoreIdentity", {})
        assets = bible_root.get("AssetLibrary", {})

        protagonist_config = bible_root.get("protagonist_config", {})
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")

        protagonist_instructions = []
        if world_origin == "원시인":
            protagonist_instructions.append("[원시인 모드] 현대 용어 절대 금지!")
        else:
            protagonist_instructions.append("[현대인 모드] 현대 지식 활용 가능")
        if incarnation_type == "회귀자":
            protagonist_instructions.append("[회귀자] 미래를 알고 있음")
        elif incarnation_type == "빙의자":
            protagonist_instructions.append("[빙의자] 원래 인물의 기억/관계를 의식")
        elif incarnation_type == "환생자":
            protagonist_instructions.append("[환생자] 전생의 기억이 있음")
        protagonist_instructions_text = "\n        ".join(protagonist_instructions)

        # NPC 장비
        npc_equipment_summary = []
        key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
        for npc in key_npcs:
            if isinstance(npc, dict):
                npc_name = npc.get("name") or npc.get("Name", "알 수 없음")
                npc_hud = npc.get("NPC_Martial_HUD", {})
                if isinstance(npc_hud, dict):
                    equip = npc_hud.get("equipment", [])
                    if equip:
                        npc_equipment_summary.append(f"- {npc_name}: {equip}")

        entity_registry_text = self._format_entity_registry_for_writer(entity_registry)
        safe_desire = self._escape_braces(core_identity.get("desire", "전설적 무인으로의 복귀"))
        safe_assets = self._escape_braces(json.dumps(assets, ensure_ascii=False))
        safe_npc_equipment = (
            self._escape_braces("\n".join(npc_equipment_summary)) if npc_equipment_summary else "NPC 장비 정보 없음"
        )
        safe_entity_registry = self._escape_braces(entity_registry_text)

        feedback_section = f"\n[REJECTION FEEDBACK]: {feedback}" if feedback else ""
        dna_instruction = (
            f"[제1화 특수 DNA 적용]: {intro_dna}"
            if int(ep_num) == 1
            else "[연속 집필 모드]: 이전 화에서 이어서 전진시켜라."
        )
        if not tactical_references:
            tactical_references = "특이 사항 없음."

        # ReferenceAnchor
        reference_anchor_prompt = ""
        try:
            from modules.core.reference_anchor import ReferenceAnchor

            anchor_sys = ReferenceAnchor(self.context)
            relevant = anchor_sys.get_relevant_anchors(current_ep_num=ep_num, arc_context=arc_doc or "", n_anchors=5)
            critical = anchor_sys.get_critical_anchors(
                current_ep_num=ep_num, anchor_types=["item", "injury", "power", "location"]
            )
            if relevant or critical:
                reference_anchor_prompt = anchor_sys.generate_reference_prompt(
                    relevant_anchors=relevant, critical_anchors=critical
                )
        except Exception:
            pass

        anti_trope = _build_anti_trope_instructions_shared(
            (getattr(self.context, "genre", None) or {}).get("name", "무협")
        )
        genre_rules_prompt = self.get_genre_rules_prompt()
        mandatory_context = _build_mandatory_context_shared(
            getattr(self.context, "db", None), getattr(self.context, "master_bible", {}), ep_num
        )
        justification_guidance = _build_justification_guidance_shared(
            hud_report, (getattr(self.context, "genre", None) or {}).get("name", "무협")
        )

        # 2. 프롬프트 조립
        dynamic_prompt = f"""
        [주인공 이름: {protagonist_name}]
        {mandatory_context}
        {feedback_section}
        {reference_anchor_prompt}
        {anti_trope}
        {genre_rules_prompt}
        {justification_guidance}

        [WRITER'S FOCUS MISSION]
        1. {focus_tag}의 내용을 바탕으로 소설 원고를 집필.
        2. 미래 사건을 미리 노출하지 마라.
        3. Blueprint에 명시된 장면을 하나하나 늘려 써라.
        4. 에피소드 마지막은 절벽걸기로 끝내라.

        [CURRENT MISSION: Ep {ep_num}]
        - 스타일: {style_mode}
        - 전개 모드: {dna_instruction}
        {purism_prompt}

        - 주인공 동력: {safe_desire}
        - 가용 자산: {safe_assets}
        - NPC 장비: {safe_npc_equipment}
        - Entity Registry: {safe_entity_registry}
        - 주인공 설정: {world_origin} / {incarnation_type}
        {protagonist_instructions_text}

        씬 설계도: {self._escape_braces(breakdown_doc)}
        실시간 상태: {self._escape_braces(hud_report)}
        HUD 추세: {_get_hud_trend_safe_shared(self.context, ep_num)}
        NPC 빈도: {self._get_npc_frequency_warning(ep_num)}
        직전 원고 엔딩: ...{self._escape_braces(prev_full_manuscript)[-1500:]}
        아크 전술: {self._escape_braces(arc_doc)}
        {self._escape_braces(tactical_references)}
        주 패턴: {self._escape_braces(str(pattern_primary))}
        부 패턴: {self._escape_braces(str(pattern_secondary))}
        조합 논리: {self._escape_braces(str(pattern_logic))}

        출력 형식 (Strict JSON):
        {{
            "title": "에피소드 제목",
            "content": "5,000자 이상의 소설 본문 (줄바꿈은 \\n)",
            "state_updates": {{
                "internal_energy": "70%",
                "realm": "경지명",
                "causal_injuries": "부상 상태",
                "wealth": "은자 500냥",
                "misunderstanding": 30,
                "obsession": 20,
                "equipment": ["소지 아이템"],
                "martial_arts": ["습득 무공"]
            }}
        }}
        """

        # 3. API 호출
        try:
            if self.cache_name:
                from google.genai import types

                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=dynamic_prompt,
                    config=types.GenerateContentConfig(
                        cached_content=self.cache_name,
                        temperature=0.8,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    ),
                )
                return self._sanitize_leakage(response.text)
            else:
                return self._fallback_full_request(dynamic_prompt)
        except Exception:
            return self._fallback_full_request(dynamic_prompt)

    def _fallback_full_request(self, dynamic_prompt):
        """캐시 없을 때 전체 프롬프트 구성"""
        try:
            rules_path = self.context.paths.config / "prompts" / "writer_rules.json"
            full_context = "[SYSTEM: WRITER MANIFESTO]\n"
            if rules_path.exists():
                data = json.loads(rules_path.read_text(encoding="utf-8"))
                manifesto = "\n".join(data.get("common_manifesto", []))
                ep1 = "\n".join(data.get("special_rule_ep1", []))
                full_context += f"{manifesto}\n\n{ep1}\n\n"
            seed_path = self.context.paths.config / "cash" / "style_seeds_final.txt"
            if seed_path.exists():
                full_context += f"### [STYLE GENETIC SEEDS]\n{seed_path.read_text(encoding='utf-8')}\n\n"
            return self._sanitize_leakage(self.ask(f"{full_context}\n{dynamic_prompt}", temperature=0.8))
        except Exception:
            return self._sanitize_leakage(self.ask(dynamic_prompt, temperature=0.8))

    def _sanitize_leakage(self, text):
        """출력 누수 방지 필터"""
        if not text:
            return text
        # [TypeSafety] ask()가 list/tuple을 반환할 수 있음 → 문자열로 결합
        if isinstance(text, list | tuple):
            text = "\n".join(str(item) for item in text)
        # [V70] ask()가 dict를 직접 반환할 수 있음 → re.sub TypeError 방어
        if isinstance(text, dict):
            banned_keys = ["Beat 3", "Beat 4", "continuation_text", "scene_summary"]
            for key in banned_keys:
                text.pop(key, None)
            return json.dumps(text, ensure_ascii=False, indent=4)
        try:
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            data = json.loads(clean_text)
            banned_keys = ["Beat 3", "Beat 4", "continuation_text", "scene_summary"]
            if isinstance(data, dict):
                for key in banned_keys:
                    data.pop(key, None)
                return json.dumps(data, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError, TypeError):  # [V70] TypeError 추가
            pass
        filtered = [line for line in text.splitlines() if not re.search(r'"(Beat \d+|continuation_text)":', line)]
        return "\n".join(filtered)

    # ==================================================================
    # 유틸리티 메서드 (main_a.py에서 writer_agent.xxx() 로 직접 호출됨)
    # ==================================================================

    def get_genre_rules_prompt(self) -> str:
        """장르별 특화 규칙 프롬프트"""
        if not self.guard:
            return ""
        try:
            if self.genre == "hunter":
                prompts = []
                if hasattr(self.guard, "get_dungeon_rules_prompt"):
                    prompts.append(self.guard.get_dungeon_rules_prompt())
                if hasattr(self.guard, "get_awakening_rules_prompt"):
                    prompts.append(self.guard.get_awakening_rules_prompt())
                return "\n\n".join(filter(None, prompts))
            elif self.genre == "investment":
                if hasattr(self.guard, "get_finance_rules_prompt"):
                    return self.guard.get_finance_rules_prompt()
            return ""
        except Exception:
            return ""

    def _get_npc_frequency_warning(self, ep_num: int) -> str:
        """NPC 등장 빈도 경고"""
        if ep_num < 2:
            return "초반부"
        try:
            freq = self._get_npc_frequency(ep_num)
            if not freq:
                return "주요 NPC 정보 없음"
            warnings = []
            for name, count in freq.items():
                if count == 0:
                    warnings.append(f"{name}: 최근 10화 미등장")
                elif count >= 7:
                    warnings.append(f"{name}: {count}회 등장 (주연급)")
            return "\n".join(warnings) if warnings else "NPC 적정 빈도"
        except Exception:
            return "빈도 추적 실패"

    def _get_npc_frequency(self, ep_num: int, window: int = 10) -> dict:
        """최근 N화 NPC 등장 빈도"""
        try:
            master_bible = getattr(self.context, "master_bible", None)
            if not master_bible:
                return {}
            bible_root = master_bible.get("MasterBible", master_bible)
            assets = bible_root.get("AssetLibrary", {})
            key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
            if not key_npcs:
                return {}
            npc_names = [npc.get("name", "") for npc in key_npcs if isinstance(npc, dict) and npc.get("name")]
            frequency = {name: 0 for name in npc_names}
            for i in range(max(1, ep_num - window), ep_num):
                try:
                    past_ms = self.context.db.get_manuscript(i)
                    if past_ms:
                        content = past_ms.get("content", "") if isinstance(past_ms, dict) else str(past_ms)
                        for name in npc_names:
                            if name in content:
                                frequency[name] += 1
                except Exception:
                    continue
            return frequency
        except Exception:
            return {}

    def _format_entity_registry_for_writer(self, entity_registry: dict) -> str:
        """Entity Registry 포맷팅"""
        if not entity_registry:
            return "(Entity Registry 없음)"
        categories = [
            ("characters", "캐릭터"),
            ("organizations", "조직"),
            ("locations", "장소"),
            ("objects", "무기/아이템"),
            ("concepts", "무공/기술"),
        ]
        lines = []
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                formatted = []
                for item in items[:10]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("canonical_name", str(item)))
                        aliases = item.get("aliases", [])
                        formatted.append(f"{name}({','.join(aliases[:3])})" if aliases else name)
                    else:
                        formatted.append(str(item))
                lines.append(f"{label}: {', '.join(formatted)}")
        return "\n        ".join(lines) if lines else "(등록된 Entity 없음)"
