"""
[V64 P2-2] PromptBuilder — SovereignApp 프롬프트 생성 로직 캡슐화

SovereignApp에서 분리된 15개 프롬프트 생성/컨텍스트 조립 메서드.
Pure 메서드(Writer 가이드 등)는 app 참조 없이 동작,
App-dependent 메서드(벡터 검색, DB 조회 등)는 self._app으로 접근.
"""

import json
import logging
import re

from modules.core.arc_state_utils import compute_terminal_arc_state
from modules.core.constants import ManuscriptLimits
from modules.core.genre_schema_builder import get_item_suffixes
from modules.core.tactical_utils import extract_episode_tactical

# [V60.10] 수여물 패턴 (main_a.py에서 이관)
_GRANT_SUFFIXES_ALL = sorted(set(["패", "권", "직", "장", "인장", "자격", "계약서", "명함"] + get_item_suffixes("")), key=len, reverse=True)
_GRANT_SUFFIX_GROUP = "|".join(re.escape(s) for s in _GRANT_SUFFIXES_ALL) or r"패|권|인장"

GRANT_PATTERNS_COMPILED = [
    (re.compile(r"([가-힣]+패)[를을]?\s*(?:하사|수여|받|얻)"), "패"),
    (re.compile(r"([가-힣]+권)[를을]?\s*(?:위임|부여|받|얻|하사)"), "권"),
    (re.compile(r"([가-힣]+직|[가-힣]+장)[에으로]?\s*(?:임명|취임|올|받)"), "직위"),
    (re.compile(r"((?:[가-힣]+\s*)?인장)[를을]?\s*(?:받|하사|수여)"), "인장"),
    (re.compile(r"([가-힣A-Za-z0-9\s]+자격)[를을]?\s*(?:부여|수여|받|획득)"), "자격"),
    (re.compile(r"([가-힣A-Za-z0-9\s]+계약서)[를을]?\s*(?:수여|교부|받|전달)"), "계약서"),
    (re.compile(r"([가-힣A-Za-z0-9\s]+명함)[를을]?\s*(?:수여|받|전달)"), "명함"),
    (
        re.compile(
            rf"([가-힣A-Za-z0-9][가-힣A-Za-z0-9\s]{{0,30}}(?:{_GRANT_SUFFIX_GROUP}))[를을]?\s*"
            r"(?:하사|수여|받|얻|획득|교부|전달|위임|부여|임명|취임)"
        ),
        "SSOT",
    ),
    (
        re.compile(
            rf"(?:하사|수여|받|얻|획득|교부|전달|위임|부여|임명|취임)[가-힣A-Za-z0-9\s]{{0,20}}"
            rf"([가-힣A-Za-z0-9][가-힣A-Za-z0-9\s]{{0,30}}(?:{_GRANT_SUFFIX_GROUP}))"
        ),
        "SSOT",
    ),
]


class PromptBuilder:
    """
    [V64 P2-2] SovereignApp의 프롬프트 생성 로직 캡슐화

    카테고리:
    - Writer 가이드 (8개): generate_arc_position_guide, generate_high_impact_zone_guide, ...
    - Arc 컨텍스트 (2개): generate_arc_context_v60, generate_arc_context_fallback
    - V50 플러그인 (2개): generate_v50_writer_prompt, generate_self_diagnosis_checklist
    - 검증/헬퍼 (3개): build_validation_context, extract_npc_profiles, get_character_traits
    - 아이템 타임라인 (1개): build_item_acquisition_timeline
    """

    def __init__(self, app=None) -> None:
        """
        Args:
            app: SovereignApp 인스턴스 (DB/모듈 접근용).
                 Pure 메서드들은 app 없이도 동작.
        """
        self._app = app
        # [V64 P2-7] 아이템 타임라인 증분 캐시 {up_to_ep: (timeline_lines_list, max_ep_loaded)}
        self._item_timeline_cache: dict = {}

    def invalidate_timeline_cache(self, from_ep: int | None = None) -> None:
        """[I-15] 타임라인 캐시 순방향 무효화.

        Args:
            from_ep: 이 에피소드 이상 키 전부 제거. None이면 전체 클리어.
        """
        if from_ep is None:
            self._item_timeline_cache.clear()
        else:
            keys_to_remove = [k for k in self._item_timeline_cache if k >= from_ep]
            for k in keys_to_remove:
                del self._item_timeline_cache[k]

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.5] Writer 가이드 — Pure (app 의존 없음)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_arc_position_guide(self, arc_pos: int, total_eps: int) -> str:
        """
        [V60.5] 아크 위치 기반 기대치 가이드 생성

        아크 내 위치에 따라 서사 밀도 기대치를 차등 적용:
        - 초반 (1화, 20%): 도입부, 설정 전개, 긴장감 시작
        - 중반 (40-60%): 갈등 고조, 사건 전개
        - 후반 (80-100%): 클라이맥스, 해결의 실마리, 강력한 엔딩
        """
        if total_eps <= 0:
            return ""

        position_ratio = arc_pos / total_eps

        lines = ["[V60.5 아크 위치 기반 가이드]"]

        if arc_pos == 1:
            lines.append("📍 현재 위치: 아크 제1화 (도입부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 새로운 사건/갈등의 시작점 설정")
            lines.append("  - 주인공의 목표와 장애물 명확히 제시")
            lines.append("  - 독자의 기대감 구축 (급한 해결 금지)")
            lines.append("")
            lines.append("⚠️ 주의: 도입부에서 사건을 해결하면 서사 폭주. 설정과 긴장감 구축에 집중.")

        elif position_ratio <= 0.4:
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (전개부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 갈등의 심화와 장애물 추가")
            lines.append("  - 캐릭터 관계 발전")
            lines.append("  - 복선 심기")
            lines.append("")
            lines.append("⚠️ 주의: 아직 클라이맥스 아님. 긴장감을 쌓아가는 단계.")

        elif position_ratio <= 0.7:
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (상승부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 갈등 최고조로 끌어올리기")
            lines.append("  - 주인공의 시련과 성장 묘사")
            lines.append("  - 반전 또는 새로운 정보 공개")
            lines.append("")
            lines.append("💡 서사 밀도가 가장 높아야 하는 구간. 사건을 풍부하게 전개하라.")

        elif arc_pos == total_eps:
            lines.append("📍 현재 위치: 아크 마지막 화 (절정/결말)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 이 아크의 핵심 갈등 해결")
            lines.append("  - 카타르시스 제공")
            lines.append("  - 다음 아크로 이어지는 강력한 클리프행어")
            lines.append("")
            lines.append("🔥 High Impact Zone: 클라이맥스 밀도를 최대로. 감정적 절정 필수.")

        else:
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (절정부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 클라이맥스 직전 긴장감 극대화")
            lines.append("  - 주인공의 결정적 행동 또는 선택")
            lines.append("  - 절벽걸기로 다음 화 기대감 극대화")
            lines.append("")
            lines.append("🔥 High Impact Zone 진입. 감정선과 액션 밀도를 높여라.")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.8] Writer 사전 가이드 시스템 — Pure
    # ═══════════════════════════════════════════════════════════════════════

    def generate_high_impact_zone_guide(self, blueprint: dict, target_len: int = ManuscriptLimits.TARGET_LENGTH) -> str:
        """[V60.8-1] High Impact Zone 분량 가이드 생성"""
        if not blueprint or not isinstance(blueprint, dict):
            return ""

        scene_breakdown = blueprint.get("scene_breakdown", {})
        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return ""

        total_scenes = len(scene_breakdown)
        if total_scenes < 4:
            return ""

        front_ratio = 0.4
        back_ratio = 0.6

        mid_point = total_scenes // 2
        front_scenes = list(scene_breakdown.keys())[:mid_point]
        back_scenes = list(scene_breakdown.keys())[mid_point:]

        front_total = int(target_len * front_ratio)
        back_total = int(target_len * back_ratio)

        front_per_scene = front_total // len(front_scenes) if front_scenes else 0
        back_per_scene = back_total // len(back_scenes) if back_scenes else 0

        lines = [
            "",
            "=" * 50,
            "[V60.8 High Impact Zone 분량 가이드]",
            "=" * 50,
            f"총 목표 분량: {target_len}자",
            "",
            "📍 전반부 (도입/전개):",
        ]

        for scene_key in front_scenes:
            scene_data = scene_breakdown.get(scene_key, {})
            scene_title = scene_data.get("title", scene_key) if isinstance(scene_data, dict) else scene_key
            lines.append(f"  - {scene_key}: 약 {front_per_scene}자 ('{scene_title[:20]}...')")

        lines.append("")
        lines.append("🔥 후반부 (클라이맥스/결말) - 반드시 상세하게!")

        for scene_key in back_scenes:
            scene_data = scene_breakdown.get(scene_key, {})
            scene_title = scene_data.get("title", scene_key) if isinstance(scene_data, dict) else scene_key
            lines.append(f"  - {scene_key}: 최소 {back_per_scene}자 이상 ('{scene_title[:20]}...')")

        lines.extend(["", "⚠️ 경고: 후반부가 전반부보다 요약되면 REJECT됩니다!", "=" * 50, ""])

        return "\n".join(lines)

    def generate_npc_relationship_justification(self, blueprint: dict) -> str:
        """[V60.8-2] NPC 관계 단계별 정당화 가이드 생성"""
        if not blueprint or not isinstance(blueprint, dict):
            return ""

        relationship_changes = blueprint.get("relationship_changes", [])
        if not relationship_changes:
            return ""

        STATE_PRIORITY = {
            "멸시": 0,
            "적대": 1,
            "무시": 2,
            "의심": 3,
            "경계": 4,
            "중립": 5,
            "호기심": 6,
            "경외": 7,
            "호감": 8,
            "충성": 9,
            "추종": 10,
        }

        JUSTIFICATION_PATTERNS = {
            (0, 7): ["압도적 무력 시연", "목숨 구해줌", "적을 처단"],
            (0, 9): ["목숨을 걸고 지켜줌 + 압도적 실력 증명"],
            (2, 7): ["예상 밖의 실력 증명", "지혜로운 문제 해결"],
            (2, 9): ["여러 차례 실력 증명 + 품성 확인"],
            (3, 7): ["의심이 경외로 바뀌는 결정적 사건 필요"],
            (4, 9): ["신뢰 회복 사건 + 능력 증명"],
        }

        jump_guides = []

        for change in relationship_changes:
            if not isinstance(change, dict):
                continue

            target = change.get("target", "알수없음")
            from_state = change.get("from", "")
            to_state = change.get("to", "")

            from_priority = STATE_PRIORITY.get(from_state, 5)
            to_priority = STATE_PRIORITY.get(to_state, 5)
            jump_size = to_priority - from_priority

            if jump_size >= 2:
                intermediate_states = []
                for state, priority in sorted(STATE_PRIORITY.items(), key=lambda x: x[1]):
                    if from_priority < priority < to_priority:
                        intermediate_states.append(state)

                key = (from_priority, to_priority)
                justifications = JUSTIFICATION_PATTERNS.get(key, ["강력한 서사적 근거 필요"])

                guide = [
                    "",
                    f"📌 '{target}' 관계 전환: {from_state} → {to_state} ({jump_size}단계 점프)",
                    "   ⚠️ 급격한 전환은 REJECT 사유입니다!",
                    "",
                    "   권장 단계적 전환:",
                ]

                if intermediate_states:
                    for i, state in enumerate(intermediate_states[:2]):
                        guide.append(f"     {i + 1}. {from_state} → {state}: [정당화 이유 작성]")
                    guide.append(
                        f"     {len(intermediate_states[:2]) + 1}. {intermediate_states[-1] if intermediate_states else from_state} → {to_state}: [정당화 이유 작성]"
                    )
                else:
                    guide.append(f"     1. {from_state} → {to_state}: [강력한 정당화 필요]")

                guide.append("")
                guide.append(f"   정당화 예시: {', '.join(justifications)}")

                jump_guides.append("\n".join(guide))

        if not jump_guides:
            return ""

        header = [
            "",
            "=" * 50,
            "[V60.8 NPC 관계 전환 정당화 가이드]",
            "=" * 50,
        ]

        footer = ["", "=" * 50, ""]

        return "\n".join(header + jump_guides + footer)

    def generate_item_acquisition_timeline(self, blueprint: dict, episode_bibles: list = None) -> str:
        """[V60.8-3] 아이템/무공 획득 시점 명시화"""
        lines = []

        current_inventory = []
        current_skills = []

        if blueprint and isinstance(blueprint, dict):
            protagonist_state = blueprint.get("protagonist_state", {})
            if isinstance(protagonist_state, dict):
                current_inventory = protagonist_state.get("inventory", [])
                current_skills = protagonist_state.get("skills", []) or protagonist_state.get("martial_arts", [])

        item_timeline = {}
        skill_timeline = {}

        if episode_bibles:
            for eb in episode_bibles:
                if not isinstance(eb, dict):
                    continue
                ep_num = eb.get("ep_num", 0)
                new_items = eb.get("new_items", [])
                if isinstance(new_items, list):
                    for item in new_items:
                        item_name = item.get("name", item) if isinstance(item, dict) else str(item)
                        if item_name and item_name not in item_timeline:
                            item_timeline[item_name] = ep_num
                # [Sweep43] skill_timeline 누락 수정
                new_skills = eb.get("new_skills", []) or eb.get("acquired_skills", [])
                if isinstance(new_skills, list):
                    for skill in new_skills:
                        skill_name = skill.get("name", skill) if isinstance(skill, dict) else str(skill)
                        if skill_name and skill_name not in skill_timeline:
                            skill_timeline[skill_name] = ep_num

        if not current_inventory and not current_skills:
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.8 아이템/무공 획득 타임라인]",
            "=" * 50,
        ]

        if current_inventory:
            lines.append("")
            lines.append("📦 현재 소지 아이템:")
            for item in current_inventory[:10]:
                item_name = item.get("name", item) if isinstance(item, dict) else str(item)
                acquired_ep = item_timeline.get(item_name, "?")
                lines.append(f"  - {item_name} (제{acquired_ep}화 획득)")
            lines.append("")
            lines.append("⚠️ 위 아이템 외의 것을 사용하면 REJECT됩니다!")

        if current_skills:
            lines.append("")
            lines.append("⚔️ 습득 무공:")
            for skill in current_skills[:10]:
                skill_name = skill.get("name", skill) if isinstance(skill, dict) else str(skill)
                acquired_ep = skill_timeline.get(skill_name, "기본")
                lines.append(f"  - {skill_name} (제{acquired_ep}화 습득)")
            lines.append("")
            lines.append("⚠️ 미습득 무공/비급 사용은 REJECT됩니다!")

        lines.extend(["", "=" * 50, ""])

        return "\n".join(lines)

    def generate_temporal_spatial_guide(self, blueprint: dict, prev_manuscript: str = "") -> str:
        """[V60.8-4] 시간/공간 연속성 가이드"""
        lines = []

        time_flow = ""
        start_location = ""

        if blueprint and isinstance(blueprint, dict):
            time_flow = blueprint.get("time_flow", "")
            start_location = blueprint.get("start_location", "") or blueprint.get("location", "")

        prev_time = ""
        prev_location = ""

        if prev_manuscript:
            time_patterns = [
                r"(다음\s*날|그날\s*밤|새벽|아침|정오|저녁|밤|자정|해질\s*무렵)",
                r"(\d+일\s*후|\d+일\s*뒤|며칠\s*후|한\s*달\s*후)",
            ]
            for pattern in time_patterns:
                matches = re.findall(pattern, prev_manuscript[-2000:])
                if matches:
                    prev_time = matches[-1] if isinstance(matches[-1], str) else matches[-1][0]
                    break

            location_patterns = [
                r"(객잔|주막|산장|동굴|광장|저택|성문|시장|숲|산|강가|절벽|무림맹|사파)",
            ]
            for pattern in location_patterns:
                matches = re.findall(pattern, prev_manuscript[-2000:])
                if matches:
                    prev_location = matches[-1]
                    break

        if not (time_flow or prev_time or prev_location or start_location):
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.8 시간/공간 연속성 가이드]",
            "=" * 50,
        ]

        if prev_time or prev_location:
            lines.append("")
            lines.append("📍 이전 화 마지막 상황:")
            if prev_time:
                lines.append(f"  - 시간: {prev_time}")
            if prev_location:
                lines.append(f"  - 장소: {prev_location}")

        if time_flow or start_location:
            lines.append("")
            lines.append("📍 현재 화 시작 상황:")
            if time_flow:
                lines.append(f"  - 시간 흐름: {time_flow}")
            if start_location:
                lines.append(f"  - 시작 장소: {start_location}")

        lines.extend(
            [
                "",
                "⚠️ 시간/공간 연속성 주의사항:",
                "  - 순간이동 금지 (장소 이동 시 이동 과정 묘사)",
                "  - 시간 역행 금지 (이전 화보다 과거 시점 불가)",
                "  - 같은 날 과다 이벤트 주의 (하루에 대형 사건 2개 이상 지양)",
                "",
                "=" * 50,
                "",
            ]
        )

        return "\n".join(lines)

    def generate_cliche_avoidance_guide(self, cliche_check_result: dict = None) -> str:
        """[V60.8-5] 클리셰 회피 가이드"""
        CLICHE_ALTERNATIVES = {
            "눈이 번쩍": ["시야가 환해지며", "정신이 맑아지며", "깨달음이 스쳤다"],
            "몸이 굳어": ["움직임이 멈추며", "발이 땅에 박힌 듯", "숨이 멎는 듯"],
            "심장이 멎": ["가슴이 조여들며", "피가 얼어붙는 듯한", "등줄기에 한기가"],
            "피가 끓어": ["분노가 차올랐다", "억누른 감정이 폭발", "참았던 것이 터졌다"],
            "입꼬리가 올라": ["미소를 머금었다", "만족한 표정", "흐뭇함이 번졌다"],
            "전율이": ["몸이 떨렸다", "긴장이 흘렀다", "압도당하는 느낌"],
            "살기가": ["위협적인 기운", "날카로운 눈빛", "공격 의지가"],
            "기세가": ["분위기가 압도", "존재감이 팽창", "무게감이 실렸다"],
        }

        lines = [
            "",
            "=" * 50,
            "[V60.8 클리셰 회피 가이드]",
            "=" * 50,
            "",
            "🚫 과다 사용 금지 표현 (1000자당 3회 미만 유지):",
            "",
        ]

        for cliche, alternatives in list(CLICHE_ALTERNATIVES.items())[:8]:
            lines.append(f"  '{cliche}' → {', '.join(alternatives[:2])}")

        lines.extend(
            [
                "",
                "💡 클리셰 회피 원칙:",
                "  1. 감정을 직접 서술하지 말고 행동/반응으로 보여주기",
                "  2. 동일 표현 연속 사용 금지 (최소 500자 간격)",
                "  3. 신체 반응 묘사 다양화 (심장/눈/피 외에 다른 부위)",
                "",
                "=" * 50,
                "",
            ]
        )

        return "\n".join(lines)

    def generate_writer_guidance_v60_8(
        self,
        blueprint: dict,
        prev_manuscript: str = "",
        episode_bibles: list = None,
        cliche_check_result: dict = None,
        target_len: int = ManuscriptLimits.TARGET_LENGTH,
    ) -> str:
        """
        [V60.8] Writer 사전 가이드 통합 생성

        5개 가이드를 통합하여 Writer에게 전달.
        """
        guides = []

        hiz_guide = self.generate_high_impact_zone_guide(blueprint, target_len)
        if hiz_guide:
            guides.append(hiz_guide)

        relationship_guide = self.generate_npc_relationship_justification(blueprint)
        if relationship_guide:
            guides.append(relationship_guide)

        item_guide = self.generate_item_acquisition_timeline(blueprint, episode_bibles)
        if item_guide:
            guides.append(item_guide)

        temporal_guide = self.generate_temporal_spatial_guide(blueprint, prev_manuscript)
        if temporal_guide:
            guides.append(temporal_guide)

        cliche_guide = self.generate_cliche_avoidance_guide(cliche_check_result)
        if cliche_guide:
            guides.append(cliche_guide)

        if not guides:
            return ""

        return "\n".join(guides)

    def generate_self_diagnosis_checklist(self, blueprint: dict) -> str:
        """[V60.5] Writer 자가 진단 체크리스트 생성"""
        lines = ["[V60.5 자가 진단 체크리스트 - 제출 전 필수 확인]", "원고 제출 전 아래 항목을 스스로 점검하라:", ""]

        scene_count = 6
        if blueprint and isinstance(blueprint, dict):
            scene_breakdown = blueprint.get("scene_breakdown", {})
            scene_count = len(scene_breakdown) if scene_breakdown else 6

        lines.append("📏 분량: 4,500자 이상 목표 (4,000자 미만 = 즉시 REJECT)")
        lines.append(f"🎬 장면: {scene_count}개 씬 모두 균등 반영 (앞만 상세하고 뒤 요약 금지)")
        lines.append("🔄 흐름: 서사 폭주(1~2장면에 해결) 또는 정체(3장면+ 반복) 금지")
        lines.append("⚙️ 설정: 미습득 무공 사용 금지, 핵심 인물 이름 유지")
        lines.append("✍️ 문체: 대화 4개+, 감각 묘사 포함, 시점 전환 활용")
        lines.append("")
        lines.append("⚠️ 3개 이상 미충족 시 REJECT 확률 80%")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.10] Arc 컨텍스트 — App-dependent (StateExtractor, 캐시)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_arc_context_v60(self, all_refined_arcs: list, current_arc_no: int = None) -> str:
        """
        [V60.10] StateExtractor를 활용한 Arc 컨텍스트 생성

        이전 Arc들의 상태를 구조화하여 추출하고,
        다음 Arc 설계 시 명확한 제약으로 주입
        """
        if not all_refined_arcs:
            return self._decorate_arc_context_for_target("서사 시작점", current_arc_no)
        if not self._app or not getattr(self._app, "agents", None):
            return self._decorate_arc_context_for_target(
                self.generate_arc_context_fallback(all_refined_arcs),
                current_arc_no,
            )

        try:
            state_extractor = self._app.agents.get("state_extractor")
            if state_extractor:
                arc_count = len(all_refined_arcs)
                if self._app._cumulative_state_cache is not None and self._app._cumulative_state_cache_key == arc_count:
                    cumulative_state = self._app._cumulative_state_cache
                else:
                    cumulative_state = state_extractor.extract_cumulative_state(all_refined_arcs)
                    self._app._cumulative_state_cache = cumulative_state
                    self._app._cumulative_state_cache_key = arc_count

                constraint_prompt = state_extractor.generate_constraint_prompt(cumulative_state)

                self._app._audit_event(
                    "v60_10_state_extracted",
                    "StateExtractor generated context",
                    {
                        "arc_count": arc_count,
                        "target_arc_no": current_arc_no,
                        "items_tracked": len(cumulative_state.get("inventory", {}).get("current_items", [])),
                    },
                )

                return self._decorate_arc_context_for_target(constraint_prompt, current_arc_no)

        except Exception as se_err:
            if hasattr(self._app, "_audit_event"):
                self._app._audit_event(
                    "v60_10_state_extractor_error",
                    "StateExtractor failed, using fallback",
                    {"error": str(se_err)[:100], "target_arc_no": current_arc_no},
                )
            if getattr(getattr(self._app, "ui", None), "log", None):
                self._app.ui.log(f"      ⚠️ [V60.10] StateExtractor 실패, Python 폴백 사용: {str(se_err)[:50]}")

        return self._decorate_arc_context_for_target(self.generate_arc_context_fallback(all_refined_arcs), current_arc_no)

    @staticmethod
    def _decorate_arc_context_for_target(context_text: str, current_arc_no: int | None) -> str:
        if not current_arc_no:
            return context_text
        return f"[다음 Arc #{current_arc_no} 설계 기준]\n{context_text}"

    def generate_arc_context_fallback(self, all_refined_arcs: list) -> str:
        """[V60.10] StateExtractor 실패 시 Python 기반 폴백"""
        last_arc = all_refined_arcs[-1]
        joint_docs = last_arc.get("joint_docs", {})
        status_shadow = last_arc.get("status_shadow", {})
        state_constraints = last_arc.get("state_constraints", {})
        arc_end_state = state_constraints.get("arc_end_state", {})

        all_acquired_items = []
        _seen_item_names = set()
        all_grants_received = []
        _seen_grant_names = set()

        for prev_arc in all_refined_arcs:
            arc_label = prev_arc.get("arc_no", "?")

            state_constraints = prev_arc.get("state_constraints", {})
            # [BUG-F] protagonist_items 우선 폴백
            items_acquired = state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", [])
            if items_acquired:
                for item in items_acquired:
                    item = str(item) if isinstance(item, dict) else item
                    if item and item not in _seen_item_names:
                        _seen_item_names.add(item)
                        all_acquired_items.append(f"Arc{arc_label}: {item}")

            prev_joint = prev_arc.get("joint_docs", {})
            prev_inventory = prev_joint.get("physical_inventory", [])
            if isinstance(prev_inventory, list):
                for item in prev_inventory:
                    item = str(item) if isinstance(item, dict) else item
                    if item and item not in _seen_item_names:
                        _seen_item_names.add(item)
                        all_acquired_items.append(f"Arc{arc_label}: {item}")
            elif isinstance(prev_inventory, str) and prev_inventory:
                if prev_inventory not in _seen_item_names:
                    _seen_item_names.add(prev_inventory)
                    all_acquired_items.append(f"Arc{arc_label}: {prev_inventory}")

            tactical = prev_arc.get("tactical_doc", "")
            # [Sweep46] tactical_doc가 dict일 수 있음 (arc.py: str | dict) — regex TypeError 방지
            if not isinstance(tactical, str):
                tactical = ""
            for pattern_compiled, suffix in GRANT_PATTERNS_COMPILED:
                matches = pattern_compiled.findall(tactical)
                for match in matches:
                    grant_item = match if isinstance(match, str) else match[0] if match else None
                    if grant_item and grant_item not in _seen_grant_names:
                        _seen_grant_names.add(grant_item)
                        all_grants_received.append(f"Arc{arc_label}: {grant_item}")

        terminal_state = compute_terminal_arc_state(all_refined_arcs)
        final_energy = terminal_state["final_energy"]
        final_injuries = terminal_state["injuries"]
        final_location = terminal_state["location"]
        final_equipment = terminal_state["equipment_text"]

        acquired_items_str = "\n   ".join(all_acquired_items) if all_acquired_items else "없음"
        grants_str = "\n   ".join(all_grants_received) if all_grants_received else "없음"
        energy_history = terminal_state["energy_history"]
        energy_history_str = " → ".join(energy_history) if energy_history else "소모 없음"

        return (
            f"[직전 아크 {last_arc.get('arc_no')} 결말 상태]:\n"
            f"══════════════════════════════════════\n"
            f"🔴🔴🔴 [필수 계승 - 다음 Arc 시작 조건] 🔴🔴🔴\n"
            f"[⚡ 최종 내공]: {final_energy}% ← 다음 Arc는 이 값으로 시작해야 함\n"
            f"[💔 최종 부상]: {final_injuries} ← 이 상태로 시작해야 함\n"
            f"[🗺️ 최종 위치]: {final_location}\n"
            f"[📦 최종 소지품]: {final_equipment}\n"
            f"══════════════════════════════════════\n"
            f"[🌍 세계 변화]: {joint_docs.get('world_joint', '알 수 없음')}\n"
            f"[🧪 소모 아이템]: {status_shadow.get('item_consumption', '없음')}\n"
            f"[📊 내공 소모 이력]: {energy_history_str}\n"
            f"══════════════════════════════════════\n"
            f"🚨🚨🚨 [중복 획득 절대 금지 목록] 🚨🚨🚨\n"
            f"아래 아이템들은 이미 이전 Arc에서 획득 완료되었습니다.\n"
            f"다시 획득하러 가거나, 다시 수여받는 설정은 CRITICAL 위반입니다:\n"
            f"   {acquired_items_str}\n"
            f"══════════════════════════════════════\n"
            f"🏅 [이미 수여받은 권한/패]:\n"
            f"   {grants_str}\n"
            f"══════════════════════════════════════\n"
            f"[📜 핵심 전술 요약]: {extract_episode_tactical(last_arc.get('tactical_doc'), last_arc.get('ep_end') or last_arc.get('ep_start', 1), episode_details=last_arc.get('episode_details'))[:1800]}\n"
            f"══════════════════════════════════════\n"
            f"🚨 [CONTINUITY LOCK] 위 상태는 절대 무시하거나 리셋할 수 없습니다. "
            f"현재 아크는 위 종료 시점에서 단 1초의 공백 없이 이어져야 합니다."
        )

    # ═══════════════════════════════════════════════════════════════════════
    # [V50] Writer 프롬프트 — App-dependent (V50 모듈들)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_v50_writer_prompt(self, ep_num: int, blueprint: dict) -> str:
        """
        [V50] Writer를 위한 서사 품질 프롬프트 생성

        - V50.1: 긴장도 가이드
        - V50.2: 대사 DNA 가이드
        - V50.3: 서브플롯 리마인더 (V65 삭제)
        """
        app = self._app

        prompts = []

        # [V65] V50.1 tension_manager, V50.2 dialogue_engine, V50.3 subplot_weaver 삭제 (Dead Code)

        # V51.1: 호흡 가이드
        pacing_analyzer = getattr(app, "pacing_analyzer", None)
        if pacing_analyzer and getattr(pacing_analyzer, "history", None):
            try:
                pacing_prompt = pacing_analyzer.generate_pacing_prompt()
                if pacing_prompt:
                    prompts.append(pacing_prompt)
            except Exception as e:
                logging.warning(f" [V64.P4-fix] pacing_analyzer 프롬프트 생성 실패: {e}")

        # V51.5: 캐릭터 음성 가이드
        character_voice = getattr(app, "character_voice", None)
        if character_voice and getattr(character_voice, "profiles", None):
            try:
                voice_prompt = character_voice.get_writer_injection()
                if voice_prompt:
                    prompts.append(voice_prompt)
            except Exception as e:
                logging.warning(f" [V64.P4-fix] character_voice 프롬프트 생성 실패: {e}")

        # V51.6: 복선 관리 가이드
        foreshadow_tracker = getattr(app, "foreshadow_tracker", None)
        if foreshadow_tracker:
            try:
                foreshadow_prompt = foreshadow_tracker.generate_writer_prompt(ep_num)
                if foreshadow_prompt:
                    prompts.append(foreshadow_prompt)
            except Exception as e:
                logging.warning(f" [V64.P4-fix] foreshadow_tracker 프롬프트 생성 실패: {e}")

        # V52.3: 씬별 전문가 가이드
        expert_mixture = getattr(app, "expert_mixture", None)
        if expert_mixture and blueprint:
            try:
                expert_prompt = expert_mixture.generate_writer_injection(blueprint)
                if expert_prompt:
                    prompts.append(expert_prompt)
            except Exception as e:
                logging.warning(f" [V64.P4-fix] expert_mixture 프롬프트 생성 실패: {e}")

        # [V60.5] 자가 진단 체크리스트
        try:
            self_diagnosis = self.generate_self_diagnosis_checklist(blueprint)
            if self_diagnosis:
                prompts.append(self_diagnosis)
        except Exception as e:
            logging.warning(f" [V64.P4-fix] self_diagnosis 프롬프트 생성 실패: {e}")

        if prompts:
            return "\n\n".join(prompts)
        return ""

    # ═══════════════════════════════════════════════════════════════════════
    # [V60.80] 아이템 타임라인 — App-dependent (DB)
    # ═══════════════════════════════════════════════════════════════════════

    def build_item_acquisition_timeline(self, up_to_ep: int) -> str:
        """
        [V60.80] 아이템 획득 타임라인 생성 (미래 침범 방지용)
        [V64 P2-7] 증분 캐시: 이전 호출 결과를 재활용하여 새 에피소드만 DB 조회

        에피소드 바이블에서 아이템 획득 기록을 추출하여
        "몇 화에서 무엇을 얻었는지" 타임라인 문자열 생성.
        """
        if up_to_ep <= 0:
            return ""
        if not self._app or not getattr(self._app, "current_project", None):
            return ""

        try:
            # [V64 P2-7] 증분 캐시 활용: 가장 가까운 이전 캐시 찾기
            cached_lines = []
            start_ep = 1

            # 정확히 같은 ep까지 캐시가 있으면 즉시 반환
            if up_to_ep in self._item_timeline_cache:
                cached = self._item_timeline_cache[up_to_ep]
                return "\n".join(cached) if cached else ""

            # 이전 캐시 중 가장 큰 ep 찾아서 재활용
            best_cached_ep = 0
            for cached_ep in self._item_timeline_cache:
                if cached_ep < up_to_ep and cached_ep > best_cached_ep:
                    best_cached_ep = cached_ep

            if best_cached_ep > 0:
                cached_lines = list(self._item_timeline_cache[best_cached_ep])
                start_ep = best_cached_ep + 1

            timeline_lines = cached_lines

            for ep in range(start_ep, up_to_ep + 1):
                ep_bible = self._app.current_project.db.get_episode_bible(ep)
                if not ep_bible:
                    continue

                new_items = ep_bible.get("new_items", [])
                if new_items:
                    # [V66] dict/str 양쪽 호환 처리
                    if isinstance(new_items, list):
                        item_parts = []
                        for item in new_items:
                            if isinstance(item, dict):
                                name = item.get("name", str(item))
                                desc = item.get("description", "")
                                item_parts.append(f"{name}({desc})" if desc else name)
                            else:
                                item_parts.append(str(item))
                        items_str = ", ".join(item_parts)
                    else:
                        items_str = str(new_items)
                    timeline_lines.append(f"제{ep}화: {items_str} 획득")

                lost_items = ep_bible.get("lost_items", [])
                if lost_items:
                    # [V70] dict 타입 방어 (new_items 처리와 동일 패턴)
                    if isinstance(lost_items, list):
                        lost_str = ", ".join(
                            item.get("name", str(item)) if isinstance(item, dict) else str(item) for item in lost_items
                        )
                    else:
                        lost_str = str(lost_items)
                    timeline_lines.append(f"제{ep}화: {lost_str} 분실/파괴")

            # [V66.1] C-3: LRU 캐시 크기 제한 (최대 3개 — 장기 세션 메모리 안정화)
            # [Sweep53] 방금 쓴 키가 즉시 퇴출되지 않도록 쓰기 전 evict
            _MAX_TIMELINE_CACHE = 3
            while len(self._item_timeline_cache) >= _MAX_TIMELINE_CACHE:
                oldest_ep = min(self._item_timeline_cache.keys())
                del self._item_timeline_cache[oldest_ep]
            self._item_timeline_cache[up_to_ep] = list(timeline_lines)

            if timeline_lines:
                return "\n".join(timeline_lines)
            else:
                return ""

        except Exception as e:
            if getattr(getattr(self._app, "ui", None), "log", None):
                self._app.ui.log(f"⚠️ 아이템 타임라인 생성 실패 (비차단): {e}")
            else:
                logging.warning(f"[PromptBuilder] item timeline build failed: {e}")
            return ""

    # ═══════════════════════════════════════════════════════════════════════
    # [V45] 검증 컨텍스트 / NPC 헬퍼 — App-dependent (DB/Bible)
    # ═══════════════════════════════════════════════════════════════════════

    def build_validation_context(
        self, ep_num: int, blueprint: dict = None, mode: str = "MANUSCRIPT", blueprint_text: str = ""
    ) -> dict:
        """
        [V45] BlockingValidator용 validation_context 구성
        """
        context = {
            "mode": mode,
            "encyclopedia": {},
            "martial_hud": {},
            "blueprint": blueprint or {},
            "blueprint_text": blueprint_text,
            "history": [],
            "npc_profiles": {},
            "external_pov_insert_policy": "",
            "pov": "",  # [V70] 시점 정보
        }

        try:
            app = self._app

            # 1. Encyclopedia 구성
            if hasattr(app.sys, "lore") and app.sys.lore:
                context["encyclopedia"] = app.sys.lore.build_validation_encyclopedia()

            # 2. Martial HUD 구성
            if hasattr(app.sys, "hud") and app.sys.hud:
                # [Sweep48] pro_root 전체 사용 (actual_truth + public_reputation)
                context["martial_hud"] = app.sys.hud.pro_root or {}

            # 3. 최근 히스토리 추출
            if app.current_project:
                causal_summary = app.current_project.get_causal_history_summary()
                if causal_summary:
                    context["history"] = [{"summary": causal_summary}]

            # 4. NPC 프로필 추출
            if app.current_project:
                bible = app.current_project.master_bible.get("MasterBible", {})
                asset_lib = bible.get("AssetLibrary", {})
                npc_lib = asset_lib.get("KeyNPCs", []) or asset_lib.get("Key_NPCs", [])
                for npc in npc_lib:
                    npc_name = npc.get("name", "") or npc.get("Name", "")
                    if npc_name:
                        context["npc_profiles"][npc_name] = npc

            # 5. [V70] POV 추출
            try:
                _bible_root = app.current_project.master_bible.get("MasterBible", {})
                _pov = _bible_root.get("protagonist_config", {}).get("pov", "")
                _external_policy = _bible_root.get("protagonist_config", {}).get("external_pov_insert_policy", "")
                if _pov:
                    context["pov"] = _pov
                if _external_policy:
                    context["external_pov_insert_policy"] = _external_policy
            except (AttributeError, KeyError, TypeError):
                pass  # POV 미설정 시 정상 생략

        except Exception as e:
            # [V70] app이 None일 수 있으므로 안전하게 로깅
            if app and hasattr(app, "ui") and getattr(app.ui, "log", None):
                app.ui.log(f"⚠️ [Validation Context] 구성 중 오류 (비치명적): {e}")
            else:
                logging.warning("[Validation Context] 구성 중 오류 (비치명적): %s", e)

        return context

    def extract_npc_profiles(self, arc_data: dict) -> dict:
        """[V41] 아크 데이터에서 등장 NPC 프로필 추출"""
        npcs = {}
        if not self._app or not getattr(self._app, "current_project", None):
            return npcs

        bible = self._app.current_project.master_bible.get("MasterBible", {})
        npc_lib = bible.get("AssetLibrary", {}).get("KeyNPCs", []) or bible.get("AssetLibrary", {}).get("Key_NPCs", [])

        arc_text = json.dumps(arc_data, ensure_ascii=False) if arc_data else ""
        for npc in npc_lib:
            npc_name = npc.get("name", "") or npc.get("Name", "")
            if npc_name and npc_name in arc_text:
                npcs[npc_name] = npc

        return npcs

    def get_character_traits(self) -> dict:
        """[V41] 캐릭터 특성 DB 로드 (성격, 지능, 무공수준)"""
        traits = {}
        if not self._app or not getattr(self._app, "current_project", None):
            return traits

        bible = self._app.current_project.master_bible.get("MasterBible", {})

        for npc in bible.get("AssetLibrary", {}).get("KeyNPCs", []) or bible.get("AssetLibrary", {}).get(
            "Key_NPCs", []
        ):
            npc_name = npc.get("name", "") or npc.get("Name", "")
            if npc_name:
                traits[npc_name] = {
                    "personality": npc.get("personality", npc.get("Personality", "")),
                    "intelligence": npc.get("intelligence", "normal"),
                    "martial_level": npc.get("NPC_Martial_HUD", {}).get("realm", "알 수 없음"),
                    "faction": npc.get("faction", npc.get("Faction", "")),
                    "role": npc.get("role", npc.get("Role", "")),
                }

        return traits
