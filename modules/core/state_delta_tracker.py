"""
[V49.7] State Delta Tracker
내공/부상/상태 변화를 공식화하여 추적

기능:
1. 에피소드별 내공 변화 추적 (delta 기반)
2. 부상 상태 연속성 검증
3. 변화량 자동 계산 및 검증
4. "갑작스러운 회복" 오류 방지

사용:
    tracker = StateDeltaTracker(initial_energy=100)
    tracker.apply_delta(arc=1, episode=2, delta=-20, reason="격전")
    tracker.apply_delta(arc=1, episode=3, delta=+10, reason="휴식")
    current = tracker.get_current_energy()  # 90
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class InjuryLevel(Enum):
    """부상 수준"""

    NORMAL = "정상"
    MINOR = "경상"
    MAJOR = "중상"
    CRITICAL = "위독"

    @classmethod
    def from_string(cls, s: str) -> "InjuryLevel":
        for level in cls:
            if level.value == s:
                return level
        return cls.NORMAL

    def severity_index(self) -> int:
        """심각도 인덱스 (0=정상, 3=위독)"""
        return list(InjuryLevel).index(self)


@dataclass
class EnergyDelta:
    """내공 변화 기록"""

    arc: int
    episode: int
    delta: int  # 양수=회복, 음수=소모
    reason: str
    before: int
    after: int


@dataclass
class InjuryEvent:
    """부상 이벤트 기록"""

    arc: int
    episode: int
    from_level: str
    to_level: str
    body_part: str  # 부상 부위
    cause: str  # 원인
    recovery_required: str  # 회복 필요 조건 (휴식/치료/약물)


class StateDeltaTracker:
    """
    [V49.7] 상태 변화 추적기

    내공, 부상 등의 변화를 delta 기반으로 추적하여
    갑작스러운 변화를 감지하고 방지합니다.
    """

    # 내공 회복 최대치 (조건별)
    RECOVERY_LIMITS = {
        "휴식_반나절": 15,
        "휴식_하루": 25,
        "휴식_삼일": 50,
        "운기조식": 20,
        "영약": 40,
        "비급_수련": 30,
        "기본_회복": 5,  # 시간 경과만으로
    }

    # 부상 자연 회복 시간 (에피소드 단위)
    INJURY_RECOVERY_TIME = {
        "경상": 1,  # 1 에피소드
        "중상": 3,  # 3 에피소드
        "위독": 5,  # 5 에피소드
    }

    def __init__(self, initial_energy: int = 100, protagonist_name: str = "주인공"):
        self.protagonist_name = protagonist_name
        self.initial_energy = initial_energy
        self.current_energy = initial_energy

        self.energy_history: list[EnergyDelta] = []
        self.injury_history: list[InjuryEvent] = []

        self.current_injuries: dict[str, InjuryEvent] = {}  # {부위: 이벤트}
        self.current_injury_level = InjuryLevel.NORMAL

    def apply_energy_delta(self, arc: int, episode: int, delta: int, reason: str) -> dict[str, Any]:
        """
        내공 변화 적용

        Args:
            arc: Arc 번호
            episode: 에피소드 번호
            delta: 변화량 (양수=회복, 음수=소모)
            reason: 변화 사유

        Returns:
            {
                "valid": bool,
                "before": int,
                "after": int,
                "warning": str or None
            }
        """
        before = self.current_energy
        after = max(0, min(100, before + delta))

        warning = None

        # 회복량 검증
        if delta > 0:
            # 회복 사유에 따른 최대치 확인
            max_recovery = self._get_max_recovery(reason)
            if delta > max_recovery:
                warning = f"과도한 회복: {delta}% (최대 {max_recovery}%)"

        # 이벤트 기록
        event = EnergyDelta(arc=arc, episode=episode, delta=delta, reason=reason, before=before, after=after)
        self.energy_history.append(event)
        self.current_energy = after

        return {"valid": True, "before": before, "after": after, "delta": delta, "warning": warning}

    def _get_max_recovery(self, reason: str) -> int:
        """사유에 따른 최대 회복량 반환"""
        reason_lower = reason.lower()

        if "영약" in reason_lower or "단약" in reason_lower or "환" in reason_lower:  # [V70] reason_lower 사용
            return self.RECOVERY_LIMITS["영약"]
        if "운기조식" in reason_lower or "운기" in reason_lower:
            return self.RECOVERY_LIMITS["운기조식"]
        if "삼일" in reason_lower or "3일" in reason_lower or "사흘" in reason_lower:
            return self.RECOVERY_LIMITS["휴식_삼일"]
        if "하루" in reason_lower or "1일" in reason_lower or "밤새" in reason_lower:
            return self.RECOVERY_LIMITS["휴식_하루"]
        if "반나절" in reason_lower or "반일" in reason_lower:  # [V70] 단독 "반" 제거 (반격/반란 오탐 방지)
            return self.RECOVERY_LIMITS["휴식_반나절"]
        if "비급" in reason_lower or "수련" in reason_lower:
            return self.RECOVERY_LIMITS["비급_수련"]

        return self.RECOVERY_LIMITS["기본_회복"]

    def apply_injury(
        self, arc: int, episode: int, level: str, body_part: str, cause: str, recovery_required: str = ""
    ) -> dict[str, Any]:
        """
        부상 적용

        Args:
            arc: Arc 번호
            episode: 에피소드 번호
            level: 부상 수준 (경상/중상/위독)
            body_part: 부상 부위
            cause: 부상 원인
            recovery_required: 회복에 필요한 것

        Returns:
            {
                "valid": bool,
                "from_level": str,
                "to_level": str,
                "warning": str or None
            }
        """
        from_level = self.current_injury_level.value
        to_level = level

        # 부상 수준 업데이트
        new_level = InjuryLevel.from_string(level)

        warning = None

        # 갑작스러운 호전 감지
        if new_level.severity_index() < self.current_injury_level.severity_index():
            # 회복인데 recovery_required가 없으면 경고
            if not recovery_required:
                warning = f"부상 회복({from_level}→{to_level})에 치료/휴식 근거 필요"

        # 이벤트 기록
        event = InjuryEvent(
            arc=arc,
            episode=episode,
            from_level=from_level,
            to_level=to_level,
            body_part=body_part,
            cause=cause,
            recovery_required=recovery_required,
        )
        self.injury_history.append(event)

        self.current_injuries[body_part] = event
        self.current_injury_level = new_level

        return {
            "valid": True,
            "from_level": from_level,
            "to_level": to_level,
            "body_part": body_part,
            "warning": warning,
        }

    def recover_injury(self, arc: int, episode: int, body_part: str, recovery_method: str) -> dict[str, Any]:
        """
        부상 회복 처리

        Args:
            arc: Arc 번호
            episode: 에피소드 번호
            body_part: 회복할 부위
            recovery_method: 회복 방법 (휴식/치료/약물)

        Returns:
            {
                "valid": bool,
                "recovered": bool,
                "warning": str or None
            }
        """
        if body_part not in self.current_injuries:
            return {"valid": True, "recovered": False, "warning": f"'{body_part}' 부위에 기록된 부상 없음"}

        injury = self.current_injuries[body_part]
        injury_ep = injury.episode
        current_ep = episode

        # 회복 시간 검증
        level = injury.to_level
        required_eps = self.INJURY_RECOVERY_TIME.get(level, 1)
        elapsed = current_ep - injury_ep

        warning = None
        if elapsed < required_eps:
            warning = f"'{level}' 부상이 {elapsed}화 만에 회복됨 (권장: {required_eps}화 이상)"

        # 회복 이벤트 기록
        recovery_event = InjuryEvent(
            arc=arc,
            episode=episode,
            from_level=level,
            to_level="정상",
            body_part=body_part,
            cause="회복",
            recovery_required=recovery_method,
        )
        self.injury_history.append(recovery_event)

        del self.current_injuries[body_part]

        # 다른 부상이 없으면 정상으로
        if not self.current_injuries:
            self.current_injury_level = InjuryLevel.NORMAL

        return {"valid": True, "recovered": True, "elapsed_episodes": elapsed, "warning": warning}

    def validate_state_continuity(
        self, arc: int, episode: int, expected_energy: int, expected_injury: str
    ) -> dict[str, Any]:
        """
        상태 연속성 검증

        Args:
            arc: Arc 번호
            episode: 에피소드 번호
            expected_energy: 예상 내공
            expected_injury: 예상 부상 수준

        Returns:
            {
                "valid": bool,
                "violations": [],
                "warnings": []
            }
        """
        violations = []
        warnings = []

        # 내공 검증
        energy_diff = abs(expected_energy - self.current_energy)
        if energy_diff > 20:
            violations.append(
                {
                    "type": "energy_discontinuity",
                    "expected": expected_energy,
                    "actual": self.current_energy,
                    "diff": energy_diff,
                    "message": f"내공 불연속: 예상 {expected_energy}% vs 실제 {self.current_energy}%",
                }
            )
        elif energy_diff > 10:
            warnings.append(f"내공 차이 {energy_diff}%: 예상 {expected_energy}% vs 실제 {self.current_energy}%")

        # 부상 검증
        expected_level = InjuryLevel.from_string(expected_injury)
        if expected_level != self.current_injury_level:
            level_diff = abs(expected_level.severity_index() - self.current_injury_level.severity_index())
            if level_diff >= 2:
                violations.append(
                    {
                        "type": "injury_discontinuity",
                        "expected": expected_injury,
                        "actual": self.current_injury_level.value,
                        "message": f"부상 불연속: 예상 '{expected_injury}' vs 실제 '{self.current_injury_level.value}'",
                    }
                )
            else:
                warnings.append(f"부상 차이: 예상 '{expected_injury}' vs 실제 '{self.current_injury_level.value}'")

        return {"valid": len(violations) == 0, "violations": violations, "warnings": warnings}

    def get_current_energy(self) -> int:
        """현재 내공 반환"""
        return self.current_energy

    def get_current_injury_level(self) -> str:
        """현재 부상 수준 반환"""
        return self.current_injury_level.value

    def get_active_injuries(self) -> list[dict]:
        """현재 활성 부상 목록"""
        return [
            {"body_part": part, "level": event.to_level, "cause": event.cause, "since_episode": event.episode}
            for part, event in self.current_injuries.items()
        ]

    def get_energy_timeline(self) -> list[dict]:
        """내공 변화 타임라인"""
        return [
            {
                "arc": e.arc,
                "episode": e.episode,
                "delta": e.delta,
                "reason": e.reason,
                "before": e.before,
                "after": e.after,
            }
            for e in self.energy_history
        ]

    def calculate_expected_energy(self) -> int:
        """
        델타 기반으로 예상 내공 계산
        (검증용 - 기록된 모든 델타를 합산)
        """
        calculated = self.initial_energy
        for delta in self.energy_history:
            calculated = max(0, min(100, calculated + delta.delta))
        return calculated

    def generate_state_prompt(self) -> str:
        """
        현재 상태를 LLM 프롬프트용 텍스트로 생성
        """
        lines = [
            "",
            "=" * 50,
            "[V49.7 상태 추적기 - 현재 상태]",
            "=" * 50,
            f"내공: {self.current_energy}%",
            f"부상: {self.current_injury_level.value}",
        ]

        if self.current_injuries:
            lines.append("활성 부상:")
            for part, event in self.current_injuries.items():
                lines.append(f"  - {part}: {event.to_level} (원인: {event.cause})")

        if self.energy_history:
            recent = self.energy_history[-3:]
            lines.append("\n최근 내공 변화:")
            for e in recent:
                sign = "+" if e.delta > 0 else ""
                lines.append(f"  Ep{e.episode}: {sign}{e.delta}% ({e.reason})")

        lines.append("=" * 50)
        return "\n".join(lines)

    def load_from_arc_state(self, state_constraints: dict) -> None:
        """
        Arc state_constraints에서 상태 로드

        Args:
            state_constraints: Arc의 state_constraints 딕셔너리
        """
        arc_end = state_constraints.get("arc_end_state", {})

        # 내공 로드
        energy = arc_end.get("internal_energy", 100)
        if isinstance(energy, str):
            # "50%" 같은 문자열 처리
            try:
                energy = int(energy.replace("%", "").strip())
            except (ValueError, TypeError):
                energy = 50
        try:
            self.current_energy = max(0, min(100, int(energy)))
        except (ValueError, TypeError):
            self.current_energy = 50

        # 부상 로드
        injuries = arc_end.get("injuries", "정상")
        self.current_injury_level = InjuryLevel.from_string(injuries)
