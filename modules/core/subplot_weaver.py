"""
[V50.3] Subplot Weaver
서브플롯 직조기 - 다중 서브플롯 추적 및 균형 관리

기능:
1. 서브플롯 등록 및 상태 추적
2. 에피소드별 서브플롯 언급/진행 기록
3. 방치된 서브플롯 감지 및 경고
4. 다음 에피소드 서브플롯 비트 제안
5. Arc 내 서브플롯 분포 검증

사용:
    weaver = SubplotWeaver()
    weaver.register_subplot("복수", "revenge", "아버지의 원수를 갚는다")
    weaver.update_subplot("복수", arc=1, episode=3, event="원수의 단서 발견")
    neglected = weaver.get_neglected_subplots(current_ep=10)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime


class SubplotType(Enum):
    """서브플롯 유형"""
    ROMANCE = ("로맨스", "romance")
    REVENGE = ("복수", "revenge")
    GROWTH = ("성장", "growth")
    MYSTERY = ("미스터리", "mystery")
    RIVALRY = ("라이벌", "rivalry")
    FAMILY = ("가족", "family")
    FRIENDSHIP = ("우정", "friendship")
    POWER = ("권력", "power")
    TREASURE = ("보물", "treasure")
    REDEMPTION = ("속죄", "redemption")
    SURVIVAL = ("생존", "survival")
    MENTOR = ("사제", "mentor")

    @property
    def name_kr(self) -> str:
        return self.value[0]

    @classmethod
    def from_string(cls, s: str) -> Optional["SubplotType"]:
        s_lower = s.lower()
        for t in cls:
            if t.value[1] == s_lower or t.value[0] == s:
                return t
        return None


class SubplotStatus(Enum):
    """서브플롯 상태"""
    SETUP = "설정"           # 초기 설정 단계
    DEVELOPING = "전개"      # 전개 중
    ESCALATING = "고조"      # 갈등 고조
    CLIMAX = "절정"          # 서브플롯 절정
    RESOLVED = "해결"        # 해결됨
    DORMANT = "휴면"         # 일시 중단
    ABANDONED = "포기"       # 포기됨 (경고)


@dataclass
class SubplotEvent:
    """서브플롯 이벤트"""
    arc: int
    episode: int
    event_type: str  # mention, progress, setback, climax, resolution
    description: str
    impact: int = 1  # 1-5 (1=언급, 5=결정적 전환)


@dataclass
class Subplot:
    """서브플롯"""
    name: str
    subplot_type: SubplotType
    description: str
    status: SubplotStatus = SubplotStatus.SETUP

    # 관련 캐릭터
    characters: List[str] = field(default_factory=list)

    # 진행 기록
    events: List[SubplotEvent] = field(default_factory=list)

    # 메타 정보
    created_arc: int = 1
    created_episode: int = 1
    last_mention_arc: int = 1
    last_mention_episode: int = 1

    # 우선순위 (높을수록 중요)
    priority: int = 5  # 1-10

    # 예상 해결 시점
    expected_resolution_arc: int = 0  # 0=미정


@dataclass
class WeavingValidation:
    """직조 검증 결과"""
    is_balanced: bool
    score: int  # 0-100
    neglected: List[str]
    overused: List[str]
    suggestions: List[str]


class SubplotWeaver:
    """
    [V50.3] 서브플롯 직조기

    메인 플롯과 서브플롯들이 조화롭게
    엮여나가도록 관리합니다.
    """

    # ═══════════════════════════════════════════════════════════════
    # 설정
    # ═══════════════════════════════════════════════════════════════

    # 방치 경고 임계값 (에피소드 단위)
    WARNING_THRESHOLD = 5      # 5화 이상 언급 없으면 WARNING
    CRITICAL_THRESHOLD = 10    # 10화 이상 언급 없으면 CRITICAL

    # Arc당 권장 서브플롯 비트 수
    MIN_SUBPLOT_BEATS_PER_ARC = 2
    MAX_SUBPLOT_BEATS_PER_ARC = 5

    # 서브플롯 최대 개수 (관리 가능 범위)
    MAX_ACTIVE_SUBPLOTS = 5

    def __init__(self):
        self.subplots: Dict[str, Subplot] = {}
        self.current_arc: int = 1
        self.current_episode: int = 1

    def register_subplot(
        self,
        name: str,
        subplot_type: str,
        description: str,
        characters: List[str] = None,
        priority: int = 5,
        arc: int = 1,
        episode: int = 1,
        expected_resolution_arc: int = 0
    ) -> Subplot:
        """
        서브플롯 등록

        Args:
            name: 서브플롯 이름 (예: "복수", "로맨스")
            subplot_type: 유형 (revenge, romance, growth, etc.)
            description: 상세 설명
            characters: 관련 캐릭터 목록
            priority: 우선순위 (1-10)
            arc: 등록 Arc
            episode: 등록 에피소드
            expected_resolution_arc: 예상 해결 Arc (0=미정)

        Returns:
            등록된 Subplot
        """
        sp_type = SubplotType.from_string(subplot_type)
        if sp_type is None:
            sp_type = SubplotType.MYSTERY  # 기본값

        subplot = Subplot(
            name=name,
            subplot_type=sp_type,
            description=description,
            characters=characters or [],
            priority=min(10, max(1, priority)),
            created_arc=arc,
            created_episode=episode,
            last_mention_arc=arc,
            last_mention_episode=episode,
            expected_resolution_arc=expected_resolution_arc
        )

        self.subplots[name] = subplot

        # 초기 이벤트 기록
        self._add_event(
            name, arc, episode,
            event_type="setup",
            description=f"서브플롯 '{name}' 설정",
            impact=2
        )

        return subplot

    def update_subplot(
        self,
        name: str,
        arc: int,
        episode: int,
        event_type: str = "progress",
        description: str = "",
        impact: int = 2,
        new_status: str = None
    ) -> Dict[str, Any]:
        """
        서브플롯 진행 업데이트

        Args:
            name: 서브플롯 이름
            arc: Arc 번호
            episode: 에피소드 번호
            event_type: 이벤트 유형 (mention, progress, setback, climax, resolution)
            description: 이벤트 설명
            impact: 영향도 (1-5)
            new_status: 새 상태 (선택적)

        Returns:
            업데이트 결과
        """
        if name not in self.subplots:
            return {"success": False, "error": f"'{name}' 서브플롯 없음"}

        subplot = self.subplots[name]

        # 이벤트 추가
        self._add_event(name, arc, episode, event_type, description, impact)

        # 마지막 언급 업데이트
        subplot.last_mention_arc = arc
        subplot.last_mention_episode = episode

        # 상태 업데이트
        if new_status:
            try:
                subplot.status = SubplotStatus(new_status)
            except ValueError:
                pass
        elif event_type == "resolution":
            subplot.status = SubplotStatus.RESOLVED
        elif event_type == "climax":
            subplot.status = SubplotStatus.CLIMAX
        elif event_type == "progress" and subplot.status == SubplotStatus.SETUP:
            subplot.status = SubplotStatus.DEVELOPING

        return {
            "success": True,
            "subplot": name,
            "status": subplot.status.value,
            "event_count": len(subplot.events)
        }

    def _add_event(
        self,
        name: str,
        arc: int,
        episode: int,
        event_type: str,
        description: str,
        impact: int
    ):
        """이벤트 추가 헬퍼"""
        if name in self.subplots:
            event = SubplotEvent(
                arc=arc,
                episode=episode,
                event_type=event_type,
                description=description,
                impact=min(5, max(1, impact))
            )
            self.subplots[name].events.append(event)

    def get_neglected_subplots(
        self,
        current_arc: int,
        current_episode: int
    ) -> List[Dict[str, Any]]:
        """
        방치된 서브플롯 조회

        Args:
            current_arc: 현재 Arc
            current_episode: 현재 에피소드

        Returns:
            방치된 서브플롯 목록 (심각도 순 정렬)
        """
        neglected = []

        for name, subplot in self.subplots.items():
            # 이미 해결된 건 제외
            if subplot.status in [SubplotStatus.RESOLVED, SubplotStatus.ABANDONED]:
                continue

            # 방치 기간 계산 (대략적)
            episodes_since = self._calculate_episode_gap(
                subplot.last_mention_arc,
                subplot.last_mention_episode,
                current_arc,
                current_episode
            )

            if episodes_since >= self.WARNING_THRESHOLD:
                severity = "CRITICAL" if episodes_since >= self.CRITICAL_THRESHOLD else "WARNING"

                neglected.append({
                    "name": name,
                    "type": subplot.subplot_type.name_kr,
                    "status": subplot.status.value,
                    "episodes_since": episodes_since,
                    "severity": severity,
                    "priority": subplot.priority,
                    "last_mention": f"Arc {subplot.last_mention_arc}, Ep {subplot.last_mention_episode}",
                    "message": f"'{name}' 서브플롯이 {episodes_since}화 동안 언급되지 않았습니다."
                })

        # 심각도 + 우선순위 순 정렬
        neglected.sort(key=lambda x: (
            0 if x["severity"] == "CRITICAL" else 1,
            -x["priority"]
        ))

        return neglected

    def _calculate_episode_gap(
        self,
        arc1: int, ep1: int,
        arc2: int, ep2: int,
        eps_per_arc: int = 5
    ) -> int:
        """에피소드 간격 계산 (대략적)"""
        total1 = (arc1 - 1) * eps_per_arc + ep1
        total2 = (arc2 - 1) * eps_per_arc + ep2
        return max(0, total2 - total1)

    def suggest_subplot_beat(
        self,
        current_arc: int,
        current_episode: int,
        main_tension: str = "rising"
    ) -> Dict[str, Any]:
        """
        다음 에피소드에 적합한 서브플롯 비트 제안

        Args:
            current_arc: 현재 Arc
            current_episode: 현재 에피소드
            main_tension: 메인 플롯 긴장도 (rest, rising, high, climax)

        Returns:
            제안 정보
        """
        # 방치된 서브플롯 우선
        neglected = self.get_neglected_subplots(current_arc, current_episode)
        if neglected:
            top = neglected[0]
            return {
                "recommended_subplot": top["name"],
                "reason": f"'{top['name']}'이(가) {top['episodes_since']}화 동안 방치됨",
                "suggested_event_type": self._suggest_event_type(top["status"], main_tension),
                "priority": "HIGH",
                "message": f"우선적으로 '{top['name']}' 서브플롯을 진행하세요."
            }

        # 메인 긴장도에 따른 서브플롯 선택
        active_subplots = [
            (name, sp) for name, sp in self.subplots.items()
            if sp.status not in [SubplotStatus.RESOLVED, SubplotStatus.ABANDONED]
        ]

        if not active_subplots:
            return {
                "recommended_subplot": None,
                "reason": "활성 서브플롯 없음",
                "suggested_event_type": None,
                "priority": "LOW",
                "message": "새로운 서브플롯을 설정하는 것을 고려하세요."
            }

        # 긴장도에 따른 선택
        if main_tension in ["rest", "low"]:
            # 휴식 구간: 로맨스, 성장, 우정 서브플롯
            preferred_types = [SubplotType.ROMANCE, SubplotType.GROWTH,
                              SubplotType.FRIENDSHIP, SubplotType.MENTOR]
        elif main_tension == "climax":
            # 절정 구간: 복수, 라이벌 서브플롯
            preferred_types = [SubplotType.REVENGE, SubplotType.RIVALRY,
                              SubplotType.POWER, SubplotType.SURVIVAL]
        else:
            # 상승/고조 구간: 미스터리, 보물, 가족
            preferred_types = [SubplotType.MYSTERY, SubplotType.TREASURE,
                              SubplotType.FAMILY, SubplotType.POWER]

        # 선호 타입 중에서 선택
        for sp_type in preferred_types:
            for name, sp in active_subplots:
                if sp.subplot_type == sp_type:
                    return {
                        "recommended_subplot": name,
                        "reason": f"메인 긴장도 '{main_tension}'에 '{sp_type.name_kr}' 서브플롯이 적합",
                        "suggested_event_type": self._suggest_event_type(sp.status.value, main_tension),
                        "priority": "MEDIUM",
                        "message": f"'{name}' 서브플롯을 진행하기 좋은 타이밍입니다."
                    }

        # 기본: 우선순위 높은 것
        active_subplots.sort(key=lambda x: -x[1].priority)
        name, sp = active_subplots[0]
        return {
            "recommended_subplot": name,
            "reason": f"우선순위가 가장 높은 서브플롯",
            "suggested_event_type": self._suggest_event_type(sp.status.value, main_tension),
            "priority": "MEDIUM",
            "message": f"'{name}' 서브플롯을 조금씩 진행하세요."
        }

    def _suggest_event_type(self, status: str, main_tension: str) -> str:
        """상태와 긴장도에 따른 이벤트 타입 제안"""
        if main_tension == "climax":
            if status in ["고조", "전개"]:
                return "climax"  # 서브플롯도 절정으로
            else:
                return "progress"
        elif main_tension in ["rest", "low"]:
            if status == "설정":
                return "progress"  # 천천히 전개
            else:
                return "mention"  # 가벼운 언급
        else:  # rising, high
            if status == "설정":
                return "progress"
            elif status == "전개":
                return "progress"  # 갈등 심화
            else:
                return "progress"

    def validate_arc_weaving(
        self,
        arc: int,
        arc_ep_count: int = 5
    ) -> WeavingValidation:
        """
        Arc 내 서브플롯 직조 검증

        Args:
            arc: Arc 번호
            arc_ep_count: Arc 에피소드 수

        Returns:
            WeavingValidation
        """
        # Arc 내 서브플롯 이벤트 수집
        subplot_counts = {}
        for name, subplot in self.subplots.items():
            count = sum(1 for e in subplot.events if e.arc == arc)
            if count > 0:
                subplot_counts[name] = count

        # 분석
        total_beats = sum(subplot_counts.values())
        neglected = []
        overused = []
        suggestions = []

        # 활성 서브플롯 중 이 Arc에서 언급 안 된 것
        for name, subplot in self.subplots.items():
            if subplot.status in [SubplotStatus.RESOLVED, SubplotStatus.ABANDONED]:
                continue
            if name not in subplot_counts:
                neglected.append(name)

        # 과다 사용
        for name, count in subplot_counts.items():
            if count > self.MAX_SUBPLOT_BEATS_PER_ARC:
                overused.append(name)

        # 점수 계산
        score = 100
        score -= len(neglected) * 15
        score -= len(overused) * 10

        if total_beats < self.MIN_SUBPLOT_BEATS_PER_ARC:
            score -= 20
            suggestions.append(f"Arc {arc}에 서브플롯 비트가 부족합니다. (현재: {total_beats}, 권장: {self.MIN_SUBPLOT_BEATS_PER_ARC}+)")

        if neglected:
            suggestions.append(f"방치된 서브플롯: {', '.join(neglected)}")

        if overused:
            suggestions.append(f"과다 사용된 서브플롯: {', '.join(overused)} - 다른 서브플롯과 균형을 맞추세요.")

        is_balanced = score >= 70 and not neglected

        return WeavingValidation(
            is_balanced=is_balanced,
            score=max(0, score),
            neglected=neglected,
            overused=overused,
            suggestions=suggestions if suggestions else ["서브플롯 직조가 적절합니다."]
        )

    def get_subplot_status(self, name: str) -> Dict[str, Any]:
        """서브플롯 상태 조회"""
        if name not in self.subplots:
            return {"error": f"'{name}' 서브플롯 없음"}

        sp = self.subplots[name]
        return {
            "name": name,
            "type": sp.subplot_type.name_kr,
            "status": sp.status.value,
            "description": sp.description,
            "characters": sp.characters,
            "priority": sp.priority,
            "event_count": len(sp.events),
            "last_mention": f"Arc {sp.last_mention_arc}, Ep {sp.last_mention_episode}",
            "created": f"Arc {sp.created_arc}, Ep {sp.created_episode}",
            "expected_resolution": f"Arc {sp.expected_resolution_arc}" if sp.expected_resolution_arc else "미정"
        }

    def get_all_subplots_summary(self) -> List[Dict[str, Any]]:
        """모든 서브플롯 요약"""
        return [
            {
                "name": name,
                "type": sp.subplot_type.name_kr,
                "status": sp.status.value,
                "priority": sp.priority,
                "events": len(sp.events)
            }
            for name, sp in self.subplots.items()
        ]

    def generate_weaving_prompt(
        self,
        current_arc: int,
        current_episode: int,
        main_tension: str = "rising"
    ) -> str:
        """
        Writer/Architect용 서브플롯 가이드 프롬프트 생성
        """
        suggestion = self.suggest_subplot_beat(current_arc, current_episode, main_tension)
        neglected = self.get_neglected_subplots(current_arc, current_episode)

        lines = [
            "",
            "=" * 50,
            "[V50.3 서브플롯 직조 가이드]",
            "=" * 50,
            f"현재 위치: Arc {current_arc}, 제 {current_episode}화",
            "",
        ]

        # 활성 서브플롯 현황
        active = [
            (name, sp) for name, sp in self.subplots.items()
            if sp.status not in [SubplotStatus.RESOLVED, SubplotStatus.ABANDONED]
        ]
        if active:
            lines.append("활성 서브플롯:")
            for name, sp in active:
                lines.append(f"  - {name} ({sp.subplot_type.name_kr}): {sp.status.value}")

        # 방치 경고
        if neglected:
            lines.append("")
            lines.append("⚠️ 방치 경고:")
            for n in neglected[:3]:
                lines.append(f"  - {n['name']}: {n['episodes_since']}화 동안 언급 없음 [{n['severity']}]")

        # 권장 사항
        lines.append("")
        if suggestion["recommended_subplot"]:
            lines.append(f"권장: '{suggestion['recommended_subplot']}' 서브플롯 진행")
            lines.append(f"  이벤트 타입: {suggestion['suggested_event_type']}")
            lines.append(f"  이유: {suggestion['reason']}")
        else:
            lines.append("권장: 새로운 서브플롯 설정 고려")

        lines.append("=" * 50)
        return "\n".join(lines)

    def load_from_arc_data(self, arcs_data: List[Dict]) -> int:
        """
        Arc 데이터에서 서브플롯 정보 로드

        Returns:
            로드된 서브플롯 수
        """
        count = 0

        for arc in arcs_data:
            if not isinstance(arc, dict):
                continue

            arc_no = arc.get("arc_no", 1)
            ep_start = arc.get("ep_start", 1)

            # subplots 필드에서 로드
            subplots = arc.get("subplots", [])
            for sp in subplots:
                if isinstance(sp, dict):
                    name = sp.get("name", "")
                    if name and name not in self.subplots:
                        self.register_subplot(
                            name=name,
                            subplot_type=sp.get("type", "mystery"),
                            description=sp.get("description", ""),
                            characters=sp.get("characters", []),
                            priority=sp.get("priority", 5),
                            arc=arc_no,
                            episode=ep_start
                        )
                        count += 1

            # subplot_beats 필드에서 이벤트 로드
            beats = arc.get("subplot_beats", [])
            for beat in beats:
                if isinstance(beat, dict):
                    name = beat.get("subplot", "")
                    if name in self.subplots:
                        self.update_subplot(
                            name=name,
                            arc=arc_no,
                            episode=beat.get("episode", ep_start),
                            event_type=beat.get("type", "progress"),
                            description=beat.get("description", ""),
                            impact=beat.get("impact", 2)
                        )

        return count
