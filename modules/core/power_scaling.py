"""
[V49.7] Power Scaling Tracker
캐릭터 파워 레벨 추적 및 급격한 변화 감지

기능:
1. 캐릭터별 power_level 추적
2. Arc별 성장률 모니터링
3. 급격한 파워업 감지 및 경고
4. 성장 근거 검증

사용:
    tracker = PowerScalingTracker()
    tracker.set_power("팽무진", arc=1, power=30, reason="회귀 초기")
    tracker.set_power("팽무진", arc=2, power=45, reason="역근경 수련")
    result = tracker.validate_growth("팽무진", arc=3, new_power=90)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PowerTier(Enum):
    """파워 등급"""

    MORTAL = (0, 20, "범인")  # 일반인
    INITIATE = (21, 40, "입문")  # 입문자
    ADEPT = (41, 60, "숙련")  # 숙련자
    EXPERT = (61, 80, "고수")  # 고수
    MASTER = (81, 95, "절정")  # 절정고수
    LEGEND = (96, 100, "전설")  # 전설급

    @classmethod
    def from_power(cls, power: int) -> "PowerTier":
        for tier in cls:
            if tier.value[0] <= power <= tier.value[1]:
                return tier
        return cls.MORTAL

    @property
    def min_power(self) -> int:
        return self.value[0]

    @property
    def max_power(self) -> int:
        return self.value[1]

    @property
    def name_kr(self) -> str:
        return self.value[2]


@dataclass
class PowerRecord:
    """파워 기록"""

    arc: int
    episode: int
    power: int
    tier: str
    reason: str  # 성장/감소 사유
    delta: int = 0  # 이전 대비 변화량


class PowerScalingTracker:
    """
    [V49.7] 파워 스케일링 추적기

    캐릭터의 파워 레벨 변화를 추적하여
    급격한 파워업을 감지하고 경고합니다.
    """

    # 정상 성장률 (Arc당)
    NORMAL_GROWTH_RATE = 10  # Arc당 평균 10 포인트
    MAX_GROWTH_RATE = 20  # Arc당 최대 20 포인트 (정당화 없이)

    # ═══════════════════════════════════════════════════════════════
    # [V49.7 Enhanced] 정당화 품질 기반 성장 허용 시스템
    # ═══════════════════════════════════════════════════════════════

    # 정당화 품질 등급 (높을수록 강한 정당화)
    JUSTIFICATION_QUALITY = {
        # 매우 강함 (LEGENDARY) - +40까지 허용
        "legendary": {
            "max_growth": 40,
            "keywords": [
                "전설급 비급",
                "신물",
                "천재지변",
                "신수의 혈",
                "만년",
                "천년",
                "금단의",
                "봉인 해제",
                "혈맥 각성",
                "선천진기",
                "태을신공",
            ],
            "description": "전설급 기연으로 획기적 성장",
        },
        # 강함 (STRONG) - +30까지 허용
        "strong": {
            "max_growth": 30,
            "keywords": [
                "비급",
                "절기",
                "각성",
                "돌파",
                "기연",
                "영약",
                "단약",
                "천재",
                "오의",
                "비전",
                "진전",
                "대성",
                "통달",
            ],
            "description": "강력한 계기로 대폭 성장",
        },
        # 보통 (MODERATE) - +20까지 허용
        "moderate": {
            "max_growth": 20,
            "keywords": ["수련", "깨달음", "실전", "경험", "훈련", "연마", "숙달", "이해", "체득", "정진", "단련"],
            "description": "노력과 경험으로 성장",
        },
        # 약함 (WEAK) - +10까지 허용
        "weak": {
            "max_growth": 10,
            "keywords": ["위기", "고비", "역경", "시간", "자연"],
            "description": "시간 경과나 위기 극복으로 소폭 성장",
        },
        # 없음 (NONE) - +5까지만 허용
        "none": {"max_growth": 5, "keywords": [], "description": "정당화 없음 - 최소 성장만 허용"},
    }

    # 복합 정당화 보너스 (여러 키워드 조합 시)
    COMPOUND_BONUS = {
        2: 5,  # 2개 키워드 조합: +5 추가
        3: 10,  # 3개 키워드 조합: +10 추가
        4: 15,  # 4개 이상: +15 추가
    }

    # 레거시 호환용
    GROWTH_JUSTIFICATIONS = {"수련": 15, "비급": 25, "영약": 20, "각성": 30, "위기": 10, "기본": 5}

    def __init__(self) -> None:
        self.characters: dict[str, list[PowerRecord]] = {}

    def set_power(self, character: str, arc: int, power: int, reason: str = "", episode: int = 0) -> dict[str, Any]:
        """
        캐릭터 파워 설정

        Args:
            character: 캐릭터 이름
            arc: Arc 번호
            power: 파워 레벨 (0-100)
            reason: 성장/변화 사유
            episode: 에피소드 번호

        Returns:
            {"success": bool, "delta": int, "warning": str or None}
        """
        # [TypeSafety] LLM이 power_level을 문자열("85")로 반환할 수 있음
        try:
            power = int(power)
        except (TypeError, ValueError):
            power = 0
        power = max(0, min(100, power))
        tier = PowerTier.from_power(power)

        delta = 0
        warning = None

        if character not in self.characters:
            self.characters[character] = []
        else:
            # 이전 기록 확인
            prev_records = self.characters[character]
            if prev_records:
                prev_power = prev_records[-1].power
                delta = power - prev_power

                # 급격한 변화 감지
                if delta > self.MAX_GROWTH_RATE:
                    warning = f"급격한 파워업: {delta}pt (최대 {self.MAX_GROWTH_RATE}pt 권장)"
                elif delta < -self.MAX_GROWTH_RATE:
                    warning = f"급격한 파워 감소: {delta}pt"

        record = PowerRecord(arc=arc, episode=episode, power=power, tier=tier.name_kr, reason=reason, delta=delta)
        self.characters[character].append(record)

        return {"success": True, "power": power, "tier": tier.name_kr, "delta": delta, "warning": warning}

    def get_power(self, character: str) -> int | None:
        """캐릭터 현재 파워 조회"""
        if character not in self.characters or not self.characters[character]:
            return None
        return self.characters[character][-1].power

    def get_tier(self, character: str) -> str | None:
        """캐릭터 현재 등급 조회"""
        if character not in self.characters or not self.characters[character]:
            return None
        return self.characters[character][-1].tier

    def validate_growth(self, character: str, arc: int, new_power: int, justification: str = "") -> dict[str, Any]:
        """
        [V49.7 Enhanced] 성장 유효성 검증 - 정당화 품질 기반

        핵심 원칙: 급성장은 허용하되, 반드시 합리적인 정당화가 필요

        Args:
            character: 캐릭터 이름
            arc: 현재 Arc
            new_power: 새 파워 레벨
            justification: 성장 근거 (상세할수록 더 많은 성장 허용)

        Returns:
            {
                "valid": bool,
                "severity": "OK" | "WARNING" | "CRITICAL",
                "message": str,
                "suggestion": str,
                "quality": str,  # 정당화 품질 등급
                "max_allowed": int  # 허용된 최대 성장량
            }
        """
        # [CrosscutR59] non-int new_power 방어
        try:
            new_power = int(new_power)
        except (TypeError, ValueError):
            return {
                "valid": False,
                "severity": "WARNING",
                "message": f"new_power 타입 오류: {type(new_power).__name__}",
                "suggestion": "정수 파워 레벨을 입력하세요",
                "quality": "none",
                "max_allowed": 0,
            }

        current_power = self.get_power(character)
        if current_power is None:
            return {
                "valid": True,
                "severity": "OK",
                "message": "첫 파워 설정",
                "suggestion": "",
                "quality": "none",
                "max_allowed": 100,
            }

        delta = new_power - current_power

        # 감소는 대체로 OK (부상, 내력 손상 등)
        if delta <= 0:
            return {
                "valid": True,
                "severity": "OK",
                "message": f"파워 감소: {delta}pt",
                "suggestion": "",
                "quality": "none",
                "max_allowed": 0,
            }

        # 정당화 품질 평가
        quality, max_allowed, matched_keywords = self._evaluate_justification_quality(justification)

        # 정상 범위 (10 이하) - 정당화 불필요
        if delta <= self.NORMAL_GROWTH_RATE:
            return {
                "valid": True,
                "severity": "OK",
                "message": f"정상 성장: {delta}pt",
                "suggestion": "",
                "quality": quality,
                "max_allowed": max_allowed,
            }

        # 정당화 없이 큰 성장 시도
        if not justification.strip():
            if delta <= self.MAX_GROWTH_RATE:
                return {
                    "valid": True,
                    "severity": "WARNING",
                    "message": f"성장 {delta}pt - 정당화 권장",
                    "suggestion": "비급 습득, 각성, 영약 복용 등 '왜 강해졌는지' 명시 필요",
                    "quality": "none",
                    "max_allowed": self.MAX_GROWTH_RATE,
                }
            else:
                return {
                    "valid": False,
                    "severity": "CRITICAL",
                    "message": f"급격한 성장 {delta}pt - 정당화 필수",
                    "suggestion": "이 정도 성장에는 반드시 서사적 근거가 필요합니다. "
                    "예: '전설급 비급 습득', '혈맥 각성', '신물 획득' 등",
                    "quality": "none",
                    "max_allowed": self.MAX_GROWTH_RATE,
                }

        # 정당화가 있는 경우 - 품질에 따라 허용
        if delta <= max_allowed:
            severity = "OK" if delta <= max_allowed * 0.8 else "WARNING"
            return {
                "valid": True,
                "severity": severity,
                "message": f"정당한 성장: {delta}pt ({justification})",
                "suggestion": "" if severity == "OK" else "다음 Arc에서는 성장 속도 조절 권장",
                "quality": quality,
                "max_allowed": max_allowed,
                "matched_keywords": matched_keywords,
            }
        else:
            # 정당화가 있어도 부족한 경우
            return {
                "valid": False,
                "severity": "CRITICAL",
                "message": f"성장 {delta}pt가 정당화 수준 초과 (허용: {max_allowed}pt)",
                "suggestion": self._generate_stronger_justification_hint(delta, quality),
                "quality": quality,
                "max_allowed": max_allowed,
                "matched_keywords": matched_keywords,
            }

    def _evaluate_justification_quality(self, justification: str) -> tuple:
        """
        [V49.7] 정당화 품질 평가

        Returns:
            (quality_level, max_growth, matched_keywords)
        """
        if not justification:
            return ("none", 5, [])
        if not isinstance(justification, str):
            justification = str(justification)

        justification_lower = justification.lower()

        # 각 품질 등급에서 매칭되는 키워드 수집
        quality_matches = {}
        for quality, config in self.JUSTIFICATION_QUALITY.items():
            if quality == "none":
                continue
            matches = [kw for kw in config["keywords"] if kw in justification_lower]
            if matches:
                quality_matches[quality] = matches

        if not quality_matches:
            return ("none", 5, [])

        # 가장 높은 품질 등급 선택
        quality_order = ["legendary", "strong", "moderate", "weak"]
        best_quality = "weak"
        for q in quality_order:
            if q in quality_matches:
                best_quality = q
                quality_matches[q]
                break

        # 기본 최대치
        base_max = self.JUSTIFICATION_QUALITY[best_quality]["max_growth"]

        # 복합 정당화 보너스 (여러 키워드 조합)
        total_keywords = sum(len(matches) for matches in quality_matches.values())
        compound_bonus = 0
        for threshold, bonus in sorted(self.COMPOUND_BONUS.items(), reverse=True):
            if total_keywords >= threshold:
                compound_bonus = bonus
                break

        final_max = base_max + compound_bonus
        all_matched = [kw for matches in quality_matches.values() for kw in matches]

        return (best_quality, final_max, all_matched)

    def _generate_stronger_justification_hint(self, delta: int, current_quality: str) -> str:
        """더 강한 정당화가 필요할 때 힌트 생성"""
        if delta > 35:
            return (
                f"이 정도 성장(+{delta}pt)에는 '전설급' 정당화가 필요합니다. "
                "예: '만년 영지 복용', '전설급 비급 득음', '혈맥 각성', '신물 획득'"
            )
        elif delta > 25:
            return (
                f"이 정도 성장(+{delta}pt)에는 '강한' 정당화가 필요합니다. "
                "예: '비급 습득', '각성/돌파', '기연', '천재적 깨달음'"
            )
        elif delta > 15:
            return f"이 정도 성장(+{delta}pt)에는 '보통' 정당화가 필요합니다. 예: '집중 수련', '실전 경험', '깨달음'"
        else:
            return f"성장(+{delta}pt)에 대한 서사적 근거를 추가하세요."

    def _get_max_allowed_growth(self, justification: str) -> int:
        """[레거시 호환] 근거에 따른 최대 허용 성장량"""
        quality, max_allowed, _ = self._evaluate_justification_quality(justification)
        return max_allowed

    def get_power_history(self, character: str) -> list[dict]:
        """캐릭터 파워 히스토리"""
        if character not in self.characters:
            return []

        return [
            {"arc": r.arc, "episode": r.episode, "power": r.power, "tier": r.tier, "delta": r.delta, "reason": r.reason}
            for r in self.characters[character]
        ]

    def get_growth_rate(self, character: str) -> float:
        """캐릭터 평균 성장률 (Arc당)"""
        history = self.characters.get(character, [])
        if len(history) < 2:
            return 0.0

        total_growth = sum(r.delta for r in history if r.delta > 0)
        arc_count = history[-1].arc - history[0].arc

        if arc_count <= 0:
            return 0.0  # [V70] 같은 Arc 내 기록 → 의미있는 Arc당 비율 없음

        return total_growth / arc_count

    def compare_characters(self, *characters: str) -> dict[str, Any]:
        """
        캐릭터 간 파워 비교

        Returns:
            {
                "ranking": [(character, power), ...],
                "gaps": [(char1, char2, gap), ...]
            }
        """
        powers = []
        for char in characters:
            power = self.get_power(char)
            if power is not None:
                powers.append((char, power))

        # 파워 순 정렬
        powers.sort(key=lambda x: x[1], reverse=True)

        # 격차 계산
        gaps = []
        for i in range(len(powers) - 1):
            char1, p1 = powers[i]
            char2, p2 = powers[i + 1]
            gap = p1 - p2
            gaps.append((char1, char2, gap))

        return {"ranking": powers, "gaps": gaps}

    def detect_power_creep(self, current_arc: int) -> list[dict]:
        """
        파워 크립 감지 (전체적인 파워 인플레이션)

        Args:
            current_arc: 현재 Arc

        Returns:
            파워 크립 경고 목록
        """
        warnings = []

        for char, records in self.characters.items():
            if len(records) < 3:
                continue

            # 최근 3개 Arc 성장률
            recent_records = [r for r in records if r.arc >= current_arc - 3]
            if len(recent_records) < 2:
                continue

            recent_growth = sum(r.delta for r in recent_records if r.delta > 0)
            avg_growth = recent_growth / len(recent_records)

            if avg_growth > self.NORMAL_GROWTH_RATE * 1.5:
                warnings.append(
                    {
                        "character": char,
                        "avg_growth": round(avg_growth, 1),
                        "message": f"'{char}' 성장 속도 과다: Arc당 평균 {avg_growth:.1f}pt",
                    }
                )

        return warnings

    def generate_scaling_prompt(self, protagonist: str) -> str:
        """
        파워 스케일링 프롬프트 생성

        Args:
            protagonist: 주인공 이름

        Returns:
            프롬프트 텍스트
        """
        power = self.get_power(protagonist)
        tier = self.get_tier(protagonist)
        growth_rate = self.get_growth_rate(protagonist)

        if power is None:
            return ""

        lines = [
            "",
            "=" * 50,
            "[V49.7 파워 스케일링 가이드]",
            "=" * 50,
            f"주인공 현재 파워: {power} ({tier})",
            f"평균 성장률: Arc당 {growth_rate:.1f}pt",
            "",
            f"다음 Arc 권장 파워 범위: {power} ~ {power + self.MAX_GROWTH_RATE}",
            "",
            "성장 근거별 최대 허용치:",
        ]

        for reason, max_val in self.GROWTH_JUSTIFICATIONS.items():
            lines.append(f"  - {reason}: +{max_val}pt")

        lines.append("=" * 50)
        return "\n".join(lines)
