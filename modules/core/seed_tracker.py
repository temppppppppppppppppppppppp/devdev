"""
[V57] Weaver Seed Tracking System

복선(Seed) 관리 시스템:
- 복선 생성 시점 추적
- 복선 회수 시점 관리
- 미회수 복선 경고
- 복선 타임라인 시각화

복선 상태:
- PLANTED: 심어진 상태 (회수 대기)
- WATERED: 중간 언급 (복선 강화)
- HARVESTED: 회수 완료
- WITHERED: 회수 실패 (너무 오래됨)
- ABANDONED: 의도적 폐기

장르별 복선 유형:
- wuxia: 비급, 원수, 보물, 과거, 약속
- hunter: 던전, 각성, 복수, 비밀, 시스템
- investment: 정보, 인맥, 위기, 기회, 배신
"""

import json
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict, fields
from datetime import datetime


class SeedStatus(Enum):
    """복선 상태"""
    PLANTED = "planted"       # 심어진 상태
    WATERED = "watered"       # 중간 언급으로 강화
    HARVESTED = "harvested"   # 회수 완료
    WITHERED = "withered"     # 회수 실패 (너무 오래됨)
    ABANDONED = "abandoned"   # 의도적 폐기


class SeedType(Enum):
    """복선 유형 (장르 공통)"""
    # 공통
    SECRET = "secret"         # 비밀 (정체, 과거 등)
    PROMISE = "promise"       # 약속/맹세
    ENEMY = "enemy"           # 원수/복수 대상
    TREASURE = "treasure"     # 보물/아이템
    PROPHECY = "prophecy"     # 예언/암시

    # 무협
    TECHNIQUE = "technique"   # 비급/무공
    RELATIONSHIP = "relationship"  # 인연/관계

    # 헌터
    DUNGEON = "dungeon"       # 던전/게이트
    AWAKENING = "awakening"   # 각성/진화
    SYSTEM = "system"         # 시스템 비밀

    # 투자
    INFORMATION = "information"  # 미래 정보
    CRISIS = "crisis"         # 위기/사건
    OPPORTUNITY = "opportunity"  # 기회


@dataclass
class Seed:
    """복선 데이터 클래스"""
    seed_id: str                      # 고유 ID
    seed_type: str                    # 복선 유형
    content: str                      # 복선 내용
    planted_ep: int                   # 심어진 화수
    planted_arc: int                  # 심어진 Arc
    target_harvest_ep: int = 0        # 목표 회수 화수 (0 = 미정)
    target_harvest_arc: int = 0       # 목표 회수 Arc (0 = 미정)
    status: str = SeedStatus.PLANTED.value
    watered_eps: List[int] = field(default_factory=list)  # 중간 언급 화수
    harvested_ep: int = 0             # 실제 회수 화수
    harvested_arc: int = 0            # 실제 회수 Arc
    importance: str = "medium"        # low/medium/high/critical
    notes: str = ""                   # 추가 노트
    created_at: str = ""              # 생성 시각
    updated_at: str = ""              # 수정 시각

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Seed':
        """딕셔너리에서 생성 [V61.5] 미지 키 무시"""
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


class SeedTracker:
    """
    [V57] Weaver Seed Tracking System

    복선 추적 및 관리 핵심 클래스

    사용 예:
    ```python
    tracker = SeedTracker(genre="wuxia")

    # 복선 심기
    seed_id = tracker.plant_seed(
        seed_type="technique",
        content="구음진경의 존재 암시",
        planted_ep=5,
        planted_arc=2,
        target_harvest_arc=4,
        importance="high"
    )

    # 복선 강화 (중간 언급)
    tracker.water_seed(seed_id, ep_num=12)

    # 복선 회수
    tracker.harvest_seed(seed_id, ep_num=25, arc_num=4)

    # 미회수 복선 경고
    warnings = tracker.check_overdue_seeds(current_ep=30, current_arc=5)
    ```
    """

    # 장르별 권장 회수 기간 (Arc 단위)
    HARVEST_WINDOW = {
        "wuxia": {
            "low": 3,       # 경미한 복선: 3 Arc 내 회수
            "medium": 2,    # 중요 복선: 2 Arc 내 회수
            "high": 2,      # 핵심 복선: 2 Arc 내 회수
            "critical": 1   # 필수 복선: 1 Arc 내 회수
        },
        "hunter": {
            "low": 4,
            "medium": 3,
            "high": 2,
            "critical": 1
        },
        "investment": {
            "low": 2,       # 투자물은 빠른 회수
            "medium": 2,
            "high": 1,
            "critical": 1
        },
        "cooking": {
            "low": 3,
            "medium": 2,
            "high": 2,
            "critical": 1
        },
        "alt_history": {
            "low": 3,
            "medium": 2,
            "high": 2,
            "critical": 1
        }
    }

    # 장르별 권장 복선 유형
    GENRE_SEED_TYPES = {
        "wuxia": ["technique", "secret", "enemy", "treasure", "relationship", "promise"],
        "hunter": ["dungeon", "awakening", "system", "secret", "enemy", "treasure"],
        "investment": ["information", "crisis", "opportunity", "secret", "promise"],
        "cooking": ["recipe", "ingredient", "secret", "rival", "customer", "promise"],
        "alt_history": ["court_intrigue", "technology", "diplomacy", "secret", "rebellion", "promise"]
    }

    def __init__(self, genre: str = "wuxia", db_manager=None):
        """
        Args:
            genre: 장르 (wuxia/hunter/investment)
            db_manager: DBManager 인스턴스 (영속성)
        """
        self.genre = genre
        self.db = db_manager
        self.seeds: Dict[str, Seed] = {}
        self._seed_counter = 0

        # DB에서 기존 데이터 로드
        self._load_from_db()

    def _load_from_db(self):
        """DB에서 복선 데이터 로드"""
        if self.db is None:
            return

        try:
            data = self.db.load_anchor("seed_tracker")
            if data:
                self._seed_counter = data.get("counter", 0)
                for seed_data in data.get("seeds", []):
                    seed = Seed.from_dict(seed_data)
                    self.seeds[seed.seed_id] = seed
                print(f"      [SeedTracker] {len(self.seeds)}개 복선 로드 완료")
        except Exception as e:
            print(f"      [SeedTracker] 로드 실패: {e}")

    def _save_to_db(self):
        """DB에 복선 데이터 저장"""
        if self.db is None:
            return

        try:
            data = {
                "counter": self._seed_counter,
                "seeds": [s.to_dict() for s in self.seeds.values()],
                "updated_at": datetime.now().isoformat()
            }
            self.db.save_anchor("seed_tracker", data)
        except Exception as e:
            print(f"      [SeedTracker] 저장 실패: {e}")

    def _generate_seed_id(self) -> str:
        """고유 Seed ID 생성"""
        self._seed_counter += 1
        return f"SEED_{self.genre.upper()}_{self._seed_counter:04d}"

    def plant_seed(
        self,
        seed_type: str,
        content: str,
        planted_ep: int,
        planted_arc: int,
        target_harvest_ep: int = 0,
        target_harvest_arc: int = 0,
        importance: str = "medium",
        notes: str = ""
    ) -> str:
        """
        복선 심기

        Args:
            seed_type: 복선 유형
            content: 복선 내용
            planted_ep: 심어진 화수
            planted_arc: 심어진 Arc
            target_harvest_ep: 목표 회수 화수 (0 = 자동 계산)
            target_harvest_arc: 목표 회수 Arc (0 = 자동 계산)
            importance: 중요도 (low/medium/high/critical)
            notes: 추가 노트

        Returns:
            생성된 Seed ID
        """
        seed_id = self._generate_seed_id()

        # 목표 Arc 자동 계산
        if target_harvest_arc == 0:
            window = self.HARVEST_WINDOW.get(self.genre, {}).get(importance, 2)
            target_harvest_arc = planted_arc + window

        seed = Seed(
            seed_id=seed_id,
            seed_type=seed_type,
            content=content,
            planted_ep=planted_ep,
            planted_arc=planted_arc,
            target_harvest_ep=target_harvest_ep,
            target_harvest_arc=target_harvest_arc,
            importance=importance,
            notes=notes
        )

        self.seeds[seed_id] = seed
        self._save_to_db()

        print(f"      [SeedTracker] 복선 심기: {seed_id} ({seed_type}) @ EP{planted_ep}/Arc{planted_arc}")
        return seed_id

    def water_seed(self, seed_id: str, ep_num: int, note: str = "") -> bool:
        """
        복선 강화 (중간 언급)

        Args:
            seed_id: Seed ID
            ep_num: 언급 화수
            note: 언급 내용

        Returns:
            성공 여부
        """
        if seed_id not in self.seeds:
            print(f"      [SeedTracker] 복선 없음: {seed_id}")
            return False

        seed = self.seeds[seed_id]

        if seed.status not in [SeedStatus.PLANTED.value, SeedStatus.WATERED.value]:
            print(f"      [SeedTracker] 강화 불가 상태: {seed.status}")
            return False

        seed.watered_eps.append(ep_num)
        seed.status = SeedStatus.WATERED.value
        seed.updated_at = datetime.now().isoformat()

        if note:
            seed.notes += f"\n[EP{ep_num}] {note}"

        self._save_to_db()
        print(f"      [SeedTracker] 복선 강화: {seed_id} @ EP{ep_num}")
        return True

    def harvest_seed(self, seed_id: str, ep_num: int, arc_num: int, note: str = "") -> bool:
        """
        복선 회수

        Args:
            seed_id: Seed ID
            ep_num: 회수 화수
            arc_num: 회수 Arc
            note: 회수 방식

        Returns:
            성공 여부
        """
        if seed_id not in self.seeds:
            print(f"      [SeedTracker] 복선 없음: {seed_id}")
            return False

        seed = self.seeds[seed_id]

        if seed.status == SeedStatus.HARVESTED.value:
            print(f"      [SeedTracker] 이미 회수됨: {seed_id}")
            return False

        seed.status = SeedStatus.HARVESTED.value
        seed.harvested_ep = ep_num
        seed.harvested_arc = arc_num
        seed.updated_at = datetime.now().isoformat()

        if note:
            seed.notes += f"\n[HARVEST EP{ep_num}] {note}"

        self._save_to_db()
        print(f"      [SeedTracker] 복선 회수: {seed_id} @ EP{ep_num}/Arc{arc_num}")
        return True

    def abandon_seed(self, seed_id: str, reason: str = "") -> bool:
        """
        복선 폐기 (의도적)

        Args:
            seed_id: Seed ID
            reason: 폐기 사유

        Returns:
            성공 여부
        """
        if seed_id not in self.seeds:
            return False

        seed = self.seeds[seed_id]
        seed.status = SeedStatus.ABANDONED.value
        seed.updated_at = datetime.now().isoformat()
        seed.notes += f"\n[ABANDONED] {reason}"

        self._save_to_db()
        print(f"      [SeedTracker] 복선 폐기: {seed_id} - {reason}")
        return True

    def check_overdue_seeds(self, current_ep: int, current_arc: int) -> List[Dict]:
        """
        미회수 복선 경고

        Args:
            current_ep: 현재 화수
            current_arc: 현재 Arc

        Returns:
            경고 목록 [{"seed_id", "severity", "message", "seed"}]
        """
        warnings = []

        for seed_id, seed in self.seeds.items():
            if seed.status not in [SeedStatus.PLANTED.value, SeedStatus.WATERED.value]:
                continue

            # 목표 Arc 초과 체크
            target_arc = seed.target_harvest_arc
            if target_arc > 0 and current_arc > target_arc:
                overdue_arcs = current_arc - target_arc

                if overdue_arcs >= 2:
                    severity = "CRITICAL"
                    seed.status = SeedStatus.WITHERED.value
                    message = f"복선 시들음: {seed.content[:30]}... (목표 Arc{target_arc}, 현재 Arc{current_arc})"
                elif overdue_arcs == 1:
                    severity = "WARNING"
                    message = f"복선 회수 지연: {seed.content[:30]}... (목표 Arc{target_arc}, 현재 Arc{current_arc})"
                else:
                    continue

                warnings.append({
                    "seed_id": seed_id,
                    "severity": severity,
                    "message": message,
                    "seed": seed.to_dict()
                })

        # 중요도별 정렬 (critical > high > medium > low)
        importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        warnings.sort(key=lambda w: importance_order.get(w["seed"]["importance"], 2))

        self._save_to_db()
        return warnings

    def get_active_seeds(self) -> List[Seed]:
        """활성 복선 목록 (PLANTED, WATERED)"""
        return [
            s for s in self.seeds.values()
            if s.status in [SeedStatus.PLANTED.value, SeedStatus.WATERED.value]
        ]

    def get_seeds_for_arc(self, arc_num: int) -> Dict[str, List[Seed]]:
        """
        특정 Arc에서 처리해야 할 복선 분류

        Returns:
            {
                "should_harvest": [회수해야 할 복선],
                "should_water": [강화할 복선],
                "can_plant": [심을 수 있는 유형]
            }
        """
        result = {
            "should_harvest": [],
            "should_water": [],
            "can_plant": self.GENRE_SEED_TYPES.get(self.genre, [])
        }

        for seed in self.get_active_seeds():
            if seed.target_harvest_arc == arc_num:
                result["should_harvest"].append(seed)
            elif seed.target_harvest_arc > arc_num and seed.status == SeedStatus.PLANTED.value:
                # 아직 회수 전이고, 중간 언급 가능
                result["should_water"].append(seed)

        return result

    def generate_weaver_prompt(self, current_arc: int, current_ep: int) -> str:
        """
        Weaver 에이전트용 프롬프트 생성

        Args:
            current_arc: 현재 Arc
            current_ep: 현재 화수

        Returns:
            복선 관리 프롬프트
        """
        arc_seeds = self.get_seeds_for_arc(current_arc)

        prompt_parts = [
            f"[V57 복선 관리 시스템 - Arc {current_arc} / EP {current_ep}]",
            ""
        ]

        # 회수해야 할 복선
        if arc_seeds["should_harvest"]:
            prompt_parts.append("### [CRITICAL] 이번 Arc에서 회수해야 할 복선:")
            for seed in arc_seeds["should_harvest"]:
                prompt_parts.append(
                    f"  - [{seed.seed_id}] {seed.seed_type}: {seed.content}"
                    f"\n    (심음: EP{seed.planted_ep}/Arc{seed.planted_arc}, "
                    f"중요도: {seed.importance})"
                )
            prompt_parts.append("")

        # 강화할 복선
        if arc_seeds["should_water"]:
            prompt_parts.append("### [RECOMMEND] 중간 언급으로 강화할 복선:")
            for seed in arc_seeds["should_water"]:
                prompt_parts.append(
                    f"  - [{seed.seed_id}] {seed.seed_type}: {seed.content[:50]}..."
                    f"\n    (목표 회수: Arc{seed.target_harvest_arc})"
                )
            prompt_parts.append("")

        # 미회수 경고
        warnings = self.check_overdue_seeds(current_ep, current_arc)
        if warnings:
            prompt_parts.append("### [WARNING] 미회수 복선 경고:")
            for warn in warnings:
                prompt_parts.append(f"  - [{warn['severity']}] {warn['message']}")
            prompt_parts.append("")

        # 심을 수 있는 복선 유형
        prompt_parts.append(f"### 이 장르에서 심을 수 있는 복선 유형:")
        prompt_parts.append(f"  {', '.join(arc_seeds['can_plant'])}")

        return "\n".join(prompt_parts)

    def get_timeline_summary(self) -> str:
        """복선 타임라인 요약"""
        lines = ["[V57 복선 타임라인]", ""]

        # 상태별 분류
        by_status = {
            "PLANTED": [],
            "WATERED": [],
            "HARVESTED": [],
            "WITHERED": [],
            "ABANDONED": []
        }

        for seed in self.seeds.values():
            status_key = seed.status.upper()
            if status_key in by_status:
                by_status[status_key].append(seed)

        for status, seeds in by_status.items():
            if not seeds:
                continue
            lines.append(f"### {status} ({len(seeds)}개):")
            for seed in seeds:
                lines.append(
                    f"  - [{seed.seed_id}] {seed.seed_type}: {seed.content[:40]}..."
                    f" (Arc{seed.planted_arc}~)"
                )
            lines.append("")

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """복선 통계"""
        total = len(self.seeds)
        by_status = {}
        by_type = {}
        by_importance = {}

        for seed in self.seeds.values():
            by_status[seed.status] = by_status.get(seed.status, 0) + 1
            by_type[seed.seed_type] = by_type.get(seed.seed_type, 0) + 1
            by_importance[seed.importance] = by_importance.get(seed.importance, 0) + 1

        # 회수율 계산
        harvestable = by_status.get("planted", 0) + by_status.get("watered", 0) + by_status.get("harvested", 0)
        harvested = by_status.get("harvested", 0)
        harvest_rate = harvested / harvestable * 100 if harvestable > 0 else 0

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "by_importance": by_importance,
            "harvest_rate": round(harvest_rate, 1),
            "active_count": len(self.get_active_seeds())
        }


def create_seed_tracker(genre: str = "wuxia", db_manager=None) -> SeedTracker:
    """SeedTracker 인스턴스 생성 헬퍼"""
    return SeedTracker(genre=genre, db_manager=db_manager)
