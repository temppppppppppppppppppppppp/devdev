"""
[V55.3] Writer Template System (원고 템플릿 시스템)
Stage 4 통과율 향상을 위한 구조화된 원고 생성 가이드

핵심: Blueprint의 씬 구조를 강제하여 누락 방지

원리:
1. Blueprint 씬을 템플릿 슬롯으로 변환
2. 각 슬롯별 최소/최대 분량 가이드
3. 필수 요소 체크리스트 주입
4. Scene-by-Scene 생성 모드 지원

비용: $0 (프롬프트 주입만)
효과: Stage 4 첫 시도 통과율 +10%p

사용:
    template = WriterTemplate(genre='wuxia')
    injection = template.generate_template(blueprint, prev_ending)
    # Writer 프롬프트에 injection 추가
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits


class SceneType(Enum):
    """씬 타입"""

    OPENING = "opening"  # 오프닝 (직전 화 연결)
    BUILDUP = "buildup"  # 빌드업 (긴장 상승)
    CONFRONTATION = "confrontation"  # 대결/충돌
    REVELATION = "revelation"  # 반전/발각
    RESOLUTION = "resolution"  # 해결/정리
    CLIFFHANGER = "cliffhanger"  # 클리프행어


@dataclass
class SceneSlot:
    """씬 슬롯"""

    index: int
    scene_id: str
    scene_type: SceneType
    description: str
    min_chars: int
    max_chars: int
    required_elements: list[str]
    characters: list[str]


@dataclass
class ManuscriptTemplate:
    """원고 템플릿"""

    ep_num: int
    total_scenes: int
    slots: list[SceneSlot]
    total_min_chars: int
    total_max_chars: int
    opening_anchor: str  # 직전 화 연결 앵커
    closing_hook: str  # 클리프행어 목표
    inventory_reminder: list[str]  # 소지품 리마인더


class WriterTemplate:
    """원고 템플릿 시스템"""

    # 씬 타입별 기본 분량 (자)
    SCENE_LENGTH = {
        SceneType.OPENING: (400, 800),
        SceneType.BUILDUP: (600, 1200),
        SceneType.CONFRONTATION: (800, 1500),
        SceneType.REVELATION: (500, 1000),
        SceneType.RESOLUTION: (400, 800),
        SceneType.CLIFFHANGER: (300, 600),
    }

    # 씬 타입별 필수 요소
    SCENE_REQUIREMENTS = {
        SceneType.OPENING: ["직전 화 상황 연결", "현재 위치/시간 명시"],
        SceneType.BUILDUP: ["긴장감 상승 요소", "캐릭터 내면 묘사"],
        SceneType.CONFRONTATION: ["대결 안무/전개", "승패 또는 중단 이유"],
        SceneType.REVELATION: ["반전 포인트", "캐릭터 반응"],
        SceneType.RESOLUTION: ["사건 정리", "다음 목표 암시"],
        SceneType.CLIFFHANGER: ["긴박한 상황", "미해결 질문"],
    }

    # 장르별 추가 요소
    GENRE_ELEMENTS = {
        "wuxia": {
            SceneType.CONFRONTATION: ["무공 묘사", "내공 소모/회복"],
            SceneType.BUILDUP: ["강호 분위기", "무림 정세"],
        },
        "hunter": {
            SceneType.CONFRONTATION: ["스킬 사용", "마나 관리"],
            SceneType.BUILDUP: ["던전/게이트 환경", "파티 역할"],
        },
        "investment": {
            SceneType.REVELATION: ["시장 정보", "투자 결정"],
            SceneType.BUILDUP: ["경제 지표", "인맥 활용"],
        },
    }

    def __init__(self, genre: str = "wuxia"):
        """
        Args:
            genre: 장르 (wuxia, hunter, investment)
        """
        self.genre = genre

    def generate_template(
        self, blueprint: dict[str, Any], prev_ending: str = "", inventory: list[str] = None
    ) -> ManuscriptTemplate:
        """
        Blueprint에서 원고 템플릿 생성

        Args:
            blueprint: Blueprint 데이터
            prev_ending: 직전 화 마지막 500자
            inventory: 현재 소지품

        Returns:
            ManuscriptTemplate
        """
        ep_num = blueprint.get("ep_num", 0)
        scene_breakdown = blueprint.get("scene_breakdown", {})
        ending_hook = blueprint.get("ending_hook") or blueprint.get("cliffhanger", "")

        slots = []
        total_min = 0
        total_max = 0

        # 씬 슬롯 생성
        for i, (scene_id, scene_data) in enumerate(scene_breakdown.items()):
            scene_type = self._infer_scene_type(i, len(scene_breakdown), scene_data)

            if isinstance(scene_data, dict):
                description = scene_data.get("description", str(scene_data))
                characters = scene_data.get("characters", [])
            else:
                description = str(scene_data)
                characters = []

            min_chars, max_chars = self.SCENE_LENGTH.get(scene_type, (500, 1000))

            # 필수 요소
            required = list(self.SCENE_REQUIREMENTS.get(scene_type, []))

            # 장르별 추가 요소
            genre_extra = self.GENRE_ELEMENTS.get(self.genre, {})
            if scene_type in genre_extra:
                required.extend(genre_extra[scene_type])

            slots.append(
                SceneSlot(
                    index=i + 1,
                    scene_id=scene_id,
                    scene_type=scene_type,
                    description=description[:200],
                    min_chars=min_chars,
                    max_chars=max_chars,
                    required_elements=required,
                    characters=characters if isinstance(characters, list) else [],
                )
            )

            total_min += min_chars
            total_max += max_chars

        return ManuscriptTemplate(
            ep_num=ep_num,
            total_scenes=len(slots),
            slots=slots,
            total_min_chars=max(ManuscriptLimits.MIN_LENGTH, total_min),
            total_max_chars=min(12000, total_max),
            opening_anchor=prev_ending[-300:] if prev_ending else "",
            closing_hook=ending_hook[:200] if ending_hook else "",
            inventory_reminder=inventory or [],
        )

    def _infer_scene_type(self, index: int, total: int, scene_data: Any) -> SceneType:
        """씬 타입 추론"""
        # 위치 기반 추론
        if index == 0:
            return SceneType.OPENING
        elif index == total - 1:
            return SceneType.CLIFFHANGER
        elif index == total - 2:
            return SceneType.RESOLUTION

        # 내용 기반 추론
        desc = str(scene_data).lower() if scene_data else ""

        if any(kw in desc for kw in ["대결", "전투", "싸움", "격돌", "교전", "습격"]):
            return SceneType.CONFRONTATION
        elif any(kw in desc for kw in ["발각", "반전", "드러나", "밝혀", "정체", "비밀"]):
            return SceneType.REVELATION
        else:
            return SceneType.BUILDUP

    def generate_prompt_injection(self, template: ManuscriptTemplate) -> str:
        """
        템플릿을 프롬프트 주입 문자열로 변환

        Args:
            template: ManuscriptTemplate

        Returns:
            주입할 프롬프트 문자열
        """
        lines = [
            "=" * 60,
            f"[V55.3 Writer Template] 제{template.ep_num}화 원고 구조",
            "=" * 60,
            "",
            f"📊 목표 분량: {template.total_min_chars}~{template.total_max_chars}자",
            f"📋 씬 개수: {template.total_scenes}개",
            "",
        ]

        # 직전 화 앵커
        if template.opening_anchor:
            lines.append("📌 [직전 화 마지막 - 여기서 이어서 시작]")
            lines.append(f'   "...{template.opening_anchor[-200:]}"')
            lines.append("")

        # 소지품 리마인더
        if template.inventory_reminder:
            lines.append("🎒 [현재 소지품 - 이것만 사용 가능]")
            for item in template.inventory_reminder[:8]:
                lines.append(f"   - {item}")
            lines.append("")

        # 씬별 슬롯
        lines.append("=" * 40)
        lines.append("📝 씬별 작성 가이드 (순서대로 작성)")
        lines.append("=" * 40)

        for slot in template.slots:
            type_emoji = {
                SceneType.OPENING: "🌅",
                SceneType.BUILDUP: "📈",
                SceneType.CONFRONTATION: "⚔️",
                SceneType.REVELATION: "💡",
                SceneType.RESOLUTION: "✅",
                SceneType.CLIFFHANGER: "🔥",
            }.get(slot.scene_type, "📍")

            lines.append(f"\n{type_emoji} [{slot.index}] {slot.scene_id} ({slot.scene_type.value})")
            lines.append(f"   목표: {slot.description[:100]}")
            lines.append(f"   분량: {slot.min_chars}~{slot.max_chars}자")

            if slot.required_elements:
                lines.append("   필수:")
                for elem in slot.required_elements[:3]:
                    lines.append(f"      □ {elem}")

            if slot.characters:
                lines.append(f"   등장: {', '.join(slot.characters[:4])}")

        # 클리프행어 목표
        if template.closing_hook:
            lines.append("\n" + "=" * 40)
            lines.append("🔥 [클리프행어 목표]")
            lines.append(f'   "{template.closing_hook}"')

        lines.append("\n" + "=" * 60)
        lines.append("⚠️ 각 씬을 순서대로 빠짐없이 작성하세요.")
        lines.append("⚠️ 씬 번호 표시 없이 자연스럽게 연결하세요.")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_scene_by_scene_prompts(
        self, template: ManuscriptTemplate, blueprint: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Scene-by-Scene 생성 모드용 개별 프롬프트 생성

        Args:
            template: ManuscriptTemplate
            blueprint: Blueprint 데이터

        Returns:
            씬별 프롬프트 리스트
        """
        prompts = []

        for i, slot in enumerate(template.slots):
            prev_scene_hint = ""
            if i > 0:
                prev_slot = template.slots[i - 1]
                prev_scene_hint = f"직전 씬 '{prev_slot.scene_id}'에서 이어집니다."

            next_scene_hint = ""
            if i < len(template.slots) - 1:
                next_slot = template.slots[i + 1]
                next_scene_hint = f"다음 씬 '{next_slot.scene_id}'로 자연스럽게 연결되어야 합니다."

            prompt = {
                "scene_index": slot.index,
                "scene_id": slot.scene_id,
                "scene_type": slot.scene_type.value,
                "description": slot.description,
                "min_chars": slot.min_chars,
                "max_chars": slot.max_chars,
                "required_elements": slot.required_elements,
                "characters": slot.characters,
                "prev_hint": prev_scene_hint,
                "next_hint": next_scene_hint,
                "is_first": i == 0,
                "is_last": i == len(template.slots) - 1,
                "opening_anchor": template.opening_anchor if i == 0 else "",
                "closing_hook": template.closing_hook if i == len(template.slots) - 1 else "",
            }

            prompts.append(prompt)

        return prompts

    def validate_against_template(self, manuscript: str, template: ManuscriptTemplate) -> dict[str, Any]:
        """
        원고가 템플릿을 준수하는지 검증

        Args:
            manuscript: 생성된 원고
            template: 템플릿

        Returns:
            검증 결과
        """
        issues = []
        warnings = []

        # 1. 총 분량 체크
        length = len(manuscript)
        if length < template.total_min_chars:
            issues.append(f"분량 부족: {length}자 (최소 {template.total_min_chars}자)")
        elif length > template.total_max_chars * 1.2:
            warnings.append(f"분량 초과: {length}자 (권장 최대 {template.total_max_chars}자)")

        # 2. 씬 키워드 반영 체크
        missing_scenes = []
        for slot in template.slots:
            # 씬 설명에서 핵심 키워드 추출
            keywords = re.findall(r"[\w가-힣]{2,}", slot.description)[:3]
            if keywords:
                matched = sum(1 for kw in keywords if kw in manuscript)
                if matched == 0:
                    missing_scenes.append(slot.scene_id)

        if missing_scenes:
            issues.append(f"씬 누락 의심: {', '.join(missing_scenes[:3])}")

        # 3. 클리프행어 체크
        if template.closing_hook:
            hook_keywords = re.findall(r"[\w가-힣]{2,}", template.closing_hook)[:3]
            ending_part = manuscript[-600:] if len(manuscript) > 600 else manuscript
            if hook_keywords and not any(kw in ending_part for kw in hook_keywords):
                warnings.append("클리프행어가 원고 끝에서 감지되지 않음")

        # 4. 직전 화 연결 체크
        if template.opening_anchor:
            anchor_keywords = re.findall(r"[\w가-힣]{3,}", template.opening_anchor)[:3]
            opening_part = manuscript[:600] if len(manuscript) > 600 else manuscript
            if anchor_keywords and not any(kw in opening_part for kw in anchor_keywords):
                warnings.append("직전 화와의 연결이 약함")

        passed = len(issues) == 0

        return {
            "passed": passed,
            "issues": issues,
            "warnings": warnings,
            "length": length,
            "expected_range": f"{template.total_min_chars}~{template.total_max_chars}",
            "scene_coverage": f"{template.total_scenes - len(missing_scenes)}/{template.total_scenes}",
        }

    def get_feedback_for_retry(self, validation_result: dict[str, Any], template: ManuscriptTemplate) -> str:
        """
        재시도를 위한 피드백 생성

        Args:
            validation_result: validate_against_template 결과
            template: 템플릿

        Returns:
            피드백 문자열
        """
        lines = ["[V55.3 Template Feedback]"]

        if validation_result["issues"]:
            lines.append("\n❌ 수정 필요:")
            for issue in validation_result["issues"]:
                lines.append(f"   - {issue}")

        if validation_result["warnings"]:
            lines.append("\n⚠️ 권장 개선:")
            for warning in validation_result["warnings"]:
                lines.append(f"   - {warning}")

        lines.append(f"\n📊 현재: {validation_result['length']}자")
        lines.append(f"📊 목표: {validation_result['expected_range']}자")
        lines.append(f"📊 씬 반영: {validation_result['scene_coverage']}")

        return "\n".join(lines)


def create_writer_template(genre: str = "wuxia") -> WriterTemplate:
    """WriterTemplate 인스턴스 생성 헬퍼"""
    return WriterTemplate(genre)
