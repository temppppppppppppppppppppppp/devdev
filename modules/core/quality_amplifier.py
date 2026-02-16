"""
[V51.2] Quality Amplifier (품질 증폭기)
검증 실패 패턴 학습 → 생성 전 제약 주입 → 성공률 향상

핵심: LLM 비용 0원으로 성공률 10-20% 향상

원리:
1. 과거 REJECT 사유 수집
2. 패턴별 제약 조건 생성
3. Writer/Architect 프롬프트에 주입
4. 자가 검증 체크리스트 제공

사용:
    amplifier = QualityAmplifier()
    constraints = amplifier.get_writer_constraints(ep_num, blueprint, prev_manuscripts)
    # Writer 호출 시 constraints 주입
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureType(Enum):
    """실패 유형"""

    # Stage 2 (Arc)
    ITEM_DUPLICATE = "item_duplicate"  # 아이템 중복 획득
    GRANT_TIMELINE = "grant_timeline"  # 수여물 타임라인 오류
    STATE_DISCONTINUITY = "state_discontinuity"  # 상태 불연속

    # Stage 3 (Blueprint)
    SCOPE_OVERFLOW = "scope_overflow"  # 범위 초과
    CONTINUITY_BREAK = "continuity_break"  # 연속성 단절
    MISSING_CLIFFHANGER = "missing_cliffhanger"  # 클리프행어 누락

    # Stage 4 (Manuscript)
    RELATIONSHIP_JUMP = "relationship_jump"  # 관계 급변
    BLUEPRINT_MISMATCH = "blueprint_mismatch"  # 블루프린트 미반영
    PACING_ISSUE = "pacing_issue"  # 호흡 문제
    ITEM_CONTINUITY = "item_continuity"  # 아이템 연속성
    POWER_UNJUSTIFIED = "power_unjustified"  # 파워업 정당화 부족


@dataclass
class FailureRecord:
    """실패 기록"""

    failure_type: FailureType
    stage: int  # 2, 3, or 4
    episode: int
    description: str
    timestamp: str = ""


@dataclass
class Constraint:
    """제약 조건"""

    rule: str  # 규칙 설명
    check_pattern: str  # 검증 패턴 (정규식)
    priority: int = 5  # 1-10 (높을수록 중요)
    failure_type: FailureType = None


class QualityAmplifier:
    """품질 증폭기"""

    # 스테이지별 기본 제약 조건
    DEFAULT_CONSTRAINTS = {
        2: [  # Stage 2 (Arc Design)
            Constraint(
                rule="이미 획득한 아이템을 다시 획득하는 설계 금지",
                check_pattern=r"(획득|입수|얻).*(이미|전에|앞서)",
                priority=10,
                failure_type=FailureType.ITEM_DUPLICATE,
            ),
            Constraint(
                rule="수여물(패, 직위)은 수여 시점 이후에만 효력 발생",
                check_pattern=r"(철혈사자패|직위|봉호)",
                priority=9,
                failure_type=FailureType.GRANT_TIMELINE,
            ),
            Constraint(
                rule="부상 상태는 Arc 간 누적 - 갑자기 완치 금지",
                check_pattern=r"(부상|상처|골절)",
                priority=8,
                failure_type=FailureType.STATE_DISCONTINUITY,
            ),
        ],
        3: [  # Stage 3 (Blueprint)
            Constraint(
                rule="씬 개수는 4-6개로 제한 (범위 초과 방지)",
                check_pattern=r"scene_\d+",
                priority=10,
                failure_type=FailureType.SCOPE_OVERFLOW,
            ),
            Constraint(
                rule="직전 화 엔딩과 연결되는 오프닝 필수",
                check_pattern=r"(이어서|계속|직전)",
                priority=9,
                failure_type=FailureType.CONTINUITY_BREAK,
            ),
            Constraint(
                rule="마지막 씬은 반드시 클리프행어로 종료",
                check_pattern=r"(클리프|절벽|긴장)",
                priority=8,
                failure_type=FailureType.MISSING_CLIFFHANGER,
            ),
        ],
        4: [  # Stage 4 (Manuscript)
            Constraint(
                rule="관계 변화는 1단계씩만 (무시→경계→중립, 2단계 점프 금지)",
                check_pattern=r"(갑자기|돌연|순식간에).*(충성|굴복|존경)",
                priority=10,
                failure_type=FailureType.RELATIONSHIP_JUMP,
            ),
            Constraint(
                rule="Blueprint의 모든 핵심 씬을 반영해야 함",
                check_pattern=r"core_scene",
                priority=10,
                failure_type=FailureType.BLUEPRINT_MISMATCH,
            ),
            Constraint(
                rule="대화:서술 비율 25-45% 유지",
                check_pattern=r"\".*\"",
                priority=7,
                failure_type=FailureType.PACING_ISSUE,
            ),
            Constraint(
                rule="직전 화에서 소지한 아이템은 이번 화 시작에도 소지",
                check_pattern=r"(들고|쥐고|차고)",
                priority=9,
                failure_type=FailureType.ITEM_CONTINUITY,
            ),
            Constraint(
                rule="급성장 시 반드시 정당화 서술 필요 (비급, 깨달음, 극한 수련)",
                check_pattern=r"(경지|돌파|각성)",
                priority=8,
                failure_type=FailureType.POWER_UNJUSTIFIED,
            ),
        ],
    }

    # 관계 상태 전이 규칙 (1단계 전이만 허용)
    RELATIONSHIP_TRANSITIONS = {
        "적대": ["무시", "경계"],
        "무시": ["적대", "경계", "의심"],
        "경계": ["무시", "의심", "중립"],
        "의심": ["경계", "중립"],
        "중립": ["의심", "경외", "호감"],
        "호감": ["중립", "경외", "친밀"],
        "경외": ["중립", "호감", "충성"],
        "친밀": ["호감", "충성"],
        "충성": ["경외", "친밀", "배신"],
        "굴복": ["충성", "배신"],
        "배신": ["적대"],
    }

    def __init__(self) -> None:
        self.failure_history: list[FailureRecord] = []
        self.custom_constraints: dict[int, list[Constraint]] = {2: [], 3: [], 4: []}

    def record_failure(self, failure_type: FailureType, stage: int, episode: int, description: str) -> None:
        """실패 기록 추가"""
        from datetime import datetime

        self.failure_history.append(
            FailureRecord(
                failure_type=failure_type,
                stage=stage,
                episode=episode,
                description=description,
                timestamp=datetime.now().isoformat(),
            )
        )

    def get_frequent_failures(self, stage: int, limit: int = 3) -> list[FailureType]:
        """자주 발생하는 실패 유형 반환"""
        stage_failures = [f for f in self.failure_history if f.stage == stage]
        if not stage_failures:
            return []

        from collections import Counter

        type_counts = Counter(f.failure_type for f in stage_failures)
        return [ft for ft, _ in type_counts.most_common(limit)]

    def get_constraints(self, stage: int) -> list[Constraint]:
        """스테이지별 제약 조건 반환 (기본 + 커스텀)"""
        import copy as _copy

        base = self.DEFAULT_CONSTRAINTS.get(stage, [])
        custom = self.custom_constraints.get(stage, [])

        # [V70] 클래스 공유 Constraint 객체를 복사 후 변형 (priority 누적 방지)
        all_constraints = [_copy.copy(c) for c in base + custom]

        # 빈도 높은 실패 유형의 제약 우선순위 상향
        frequent = self.get_frequent_failures(stage)
        for c in all_constraints:
            if c.failure_type in frequent:
                c.priority = min(10, c.priority + 2)

        # 우선순위 순 정렬
        return sorted(all_constraints, key=lambda x: -x.priority)

    def generate_writer_constraints(
        self,
        ep_num: int,
        blueprint: dict[str, Any],
        prev_manuscript: str = "",
        prev_items: list[str] = None,
        prev_relationships: dict[str, str] = None,
    ) -> str:
        """
        Writer용 제약 조건 프롬프트 생성

        Args:
            ep_num: 현재 에피소드 번호
            blueprint: 현재 블루프린트
            prev_manuscript: 직전 화 원고
            prev_items: 직전 화 소지 아이템
            prev_relationships: 직전 화 관계 상태

        Returns:
            str: Writer에 주입할 제약 조건 프롬프트
        """
        lines = ["[V51.2 품질 제약 조건]"]
        lines.append("다음 규칙을 반드시 준수하세요:\n")

        # 1. 기본 제약
        constraints = self.get_constraints(4)
        for i, c in enumerate(constraints[:5], 1):
            lines.append(f"{i}. {c.rule}")

        # 2. 아이템 연속성
        if prev_items:
            lines.append("\n[소지 아이템 연속성]")
            lines.append(f"직전 화 종료 시 소지: {', '.join(prev_items)}")
            lines.append("→ 이번 화 시작에서 동일하게 소지해야 함")

        # 3. 관계 변화 제한
        if prev_relationships:
            lines.append("\n[관계 변화 제한]")
            for npc, state in list(prev_relationships.items())[:3]:
                allowed = self.RELATIONSHIP_TRANSITIONS.get(state, [])
                if allowed:
                    lines.append(f"- {npc}: 현재 '{state}' → 가능: {allowed}")

        # 4. Blueprint 핵심 씬 체크리스트
        scenes = blueprint.get("scene_breakdown", blueprint.get("scenes", {}))
        if scenes:
            lines.append("\n[필수 반영 씬]")
            if isinstance(scenes, dict):
                for scene_id, scene_data in list(scenes.items())[:4]:
                    desc = scene_data.get("summary", scene_data.get("description", str(scene_data)[:50]))
                    lines.append(f"- {scene_id}: {desc[:60]}")
            elif isinstance(scenes, list):
                for i, scene in enumerate(scenes[:4], 1):
                    if isinstance(scene, dict):
                        desc = scene.get("summary", scene.get("description", ""))[:60]
                    else:
                        desc = str(scene)[:60]
                    lines.append(f"- Scene {i}: {desc}")

        # 5. 자가 검증 체크리스트
        lines.append("\n[제출 전 자가 검증]")
        lines.append("□ 직전 화 엔딩과 자연스럽게 연결되는가?")
        lines.append("□ 소지 아이템이 유지되는가?")
        lines.append("□ 관계 변화가 1단계 이내인가?")
        lines.append("□ Blueprint의 모든 핵심 씬이 반영되었는가?")
        lines.append("□ 클리프행어로 종료되는가?")

        return "\n".join(lines)

    def generate_architect_constraints(
        self, ep_num: int, arc_data: dict[str, Any], prev_blueprint: dict[str, Any] = None
    ) -> str:
        """
        Architect용 제약 조건 프롬프트 생성
        """
        lines = ["[V51.2 Blueprint 제약 조건]"]
        lines.append("다음 규칙을 반드시 준수하세요:\n")

        # 1. 기본 제약
        constraints = self.get_constraints(3)
        for i, c in enumerate(constraints[:4], 1):
            lines.append(f"{i}. {c.rule}")

        # 2. 씬 개수 제한
        lines.append("\n[씬 구성 규칙]")
        lines.append("- 씬 개수: 4-6개 (초과 시 REJECT)")
        lines.append("- 각 씬 예상 분량: 800-1500자")
        lines.append("- 총 분량 목표: 4000-6000자")

        # 3. 연속성 체크
        if prev_blueprint:
            prev_ending = prev_blueprint.get("cliffhanger", prev_blueprint.get("ending", ""))
            if prev_ending:
                lines.append("\n[직전 화 엔딩]")
                lines.append(f"'{prev_ending[:100]}'")
                lines.append("→ 이 상황에서 자연스럽게 이어지는 오프닝 설계")

        # 4. 자가 검증
        lines.append("\n[설계 전 체크]")
        lines.append("□ 직전 화 클리프행어 해소 장면 포함?")
        lines.append("□ 이번 화만의 클리프행어 존재?")
        lines.append("□ 씬 개수 4-6개 이내?")

        return "\n".join(lines)

    def generate_analyst_constraints(self, arc_num: int, prev_arcs: list[dict[str, Any]] = None) -> str:
        """
        Analyst용 제약 조건 프롬프트 생성
        """
        lines = ["[V51.2 Arc 설계 제약 조건]"]
        lines.append("다음 규칙을 반드시 준수하세요:\n")

        # 1. 기본 제약
        constraints = self.get_constraints(2)
        for i, c in enumerate(constraints[:4], 1):
            lines.append(f"{i}. {c.rule}")

        # 2. 이미 획득한 아이템 목록
        if prev_arcs:
            acquired_items = set()
            for arc in prev_arcs:
                items = arc.get("acquired_items", arc.get("new_items", []))
                if isinstance(items, list):
                    acquired_items.update(items)

            if acquired_items:
                lines.append("\n[이미 획득한 아이템]")
                for item in list(acquired_items)[:10]:
                    lines.append(f"- {item}")
                lines.append("→ 위 아이템을 다시 획득하는 설계 금지")

        # 3. 자가 검증
        lines.append("\n[설계 전 체크]")
        lines.append("□ 기존 아이템 중복 획득 없는가?")
        lines.append("□ 수여물 타임라인이 논리적인가?")
        lines.append("□ 부상/상태가 이전 Arc와 연속적인가?")

        return "\n".join(lines)

    def extract_items_from_manuscript(self, manuscript: str) -> list[str]:
        """원고에서 소지 아이템 추출"""
        # 무기/아이템 패턴
        patterns = [
            r"(대도|장검|단검|비수|창|봉|도|검|검집)을?\s*(들|쥐|차|뽑)",
            r"(주머니|보따리|배낭|품).*?(넣|꺼내|간직)",
            r"허리.*?(차고|매고|걸고)",
        ]

        items = set()
        for pattern in patterns:
            for match in re.finditer(pattern, manuscript):
                item = match.group(1) if match.groups() else match.group()
                items.add(item)

        return list(items)

    def extract_relationships_from_manuscript(self, manuscript: str) -> dict[str, str]:
        """원고에서 관계 상태 추출"""
        relationship_markers = {
            "적대": ["적", "원수", "증오", "죽이"],
            "무시": ["무시", "거들떠", "안중에"],
            "경계": ["경계", "의심", "수상"],
            "중립": ["중립", "담담", "무관심"],
            "호감": ["호감", "호의", "관심"],
            "경외": ["경외", "존경", "두려움"],
            "충성": ["충성", "따르", "모시"],
            "굴복": ["굴복", "항복", "무릎"],
        }

        # 간단한 휴리스틱 추출
        relationships = {}
        # 실제 구현은 NPC 이름과 매칭 필요
        return relationships

    def get_self_check_prompt(self, stage: int) -> str:
        """자가 검증 프롬프트 생성"""
        if stage == 2:
            return """
[Arc 설계 자가 검증]
생성한 Arc를 제출하기 전에 다음을 확인하세요:
1. 이전 Arc에서 이미 획득한 아이템을 다시 획득하게 설계하지 않았는가?
2. 수여물(패, 직위)의 시점이 논리적인가?
3. 캐릭터 부상/상태가 이전 Arc와 연속적인가?
4. 각 화의 분량이 균등한가?

위 항목 중 하나라도 위반되면 수정 후 제출하세요.
"""
        elif stage == 3:
            return """
[Blueprint 자가 검증]
생성한 Blueprint를 제출하기 전에 다음을 확인하세요:
1. 씬 개수가 4-6개 이내인가?
2. 직전 화 엔딩과 자연스럽게 연결되는가?
3. 클리프행어로 종료되는가?
4. 총 예상 분량이 4000-6000자인가?

위 항목 중 하나라도 위반되면 수정 후 제출하세요.
"""
        elif stage == 4:
            return """
[원고 자가 검증]
생성한 원고를 제출하기 전에 다음을 확인하세요:
1. 직전 화 엔딩에서 자연스럽게 이어지는가?
2. 소지 아이템이 유지되는가?
3. NPC 관계가 1단계 이상 급변하지 않았는가?
4. Blueprint의 모든 핵심 씬이 반영되었는가?
5. 클리프행어로 종료되는가?
6. 대화:서술 비율이 적절한가? (25-45%)

위 항목 중 하나라도 위반되면 수정 후 제출하세요.
"""
        return ""
