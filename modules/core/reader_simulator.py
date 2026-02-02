"""
[V50.4] Reader Simulator
독자 시뮬레이터 - 가상 독자 관점에서 원고 피드백

기능:
1. 가상 독자 유형별 반응 시뮬레이션
2. 지루함 감지 (템포, 반복, 정보 과잉)
3. 예측가능성 감지 (클리셰, 복선 노출)
4. 혼란 감지 (동기 불명확, 설정 모순)
5. 몰입도 평가 (후크, 긴장, 감정 페이오프)

사용:
    simulator = ReaderSimulator()
    feedback = simulator.simulate_reading(manuscript, context)
    engagement = simulator.calculate_engagement_score(manuscript)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re
from collections import Counter


class ReaderType(Enum):
    """독자 유형"""
    CASUAL = ("캐주얼", "가볍게 즐기는 독자")
    HARDCORE = ("하드코어", "설정과 세계관에 집착하는 독자")
    EMOTIONAL = ("감성파", "캐릭터 감정에 몰입하는 독자")
    CRITIC = ("비평가", "문학적 완성도를 따지는 독자")
    SPEED = ("속도파", "빠른 전개를 선호하는 독자")


class ReaderMood(Enum):
    """독자 감정 상태"""
    EXCITED = "흥분"
    ENGAGED = "몰입"
    CURIOUS = "호기심"
    NEUTRAL = "평온"
    BORED = "지루"
    CONFUSED = "혼란"
    FRUSTRATED = "짜증"
    SATISFIED = "만족"


@dataclass
class ReadingFeedback:
    """독자 피드백"""
    reader_type: ReaderType
    overall_mood: ReaderMood
    engagement_score: int  # 0-100

    # 상세 피드백
    positive_moments: List[Dict[str, Any]] = field(default_factory=list)
    negative_moments: List[Dict[str, Any]] = field(default_factory=list)

    # 문제점
    boredom_flags: List[str] = field(default_factory=list)
    confusion_flags: List[str] = field(default_factory=list)
    predictability_flags: List[str] = field(default_factory=list)

    # 종합 코멘트
    summary: str = ""


class ReaderSimulator:
    """
    [V50.4] 독자 시뮬레이터

    가상 독자의 관점에서 원고를 평가하여
    실제 독자가 느낄 반응을 예측합니다.
    """

    # ═══════════════════════════════════════════════════════════════
    # 감지 패턴
    # ═══════════════════════════════════════════════════════════════

    # 지루함 유발 패턴
    BOREDOM_PATTERNS = {
        "info_dump": {
            "patterns": [
                r"[가-힣]{20,}(?:이다|했다|였다|있다)[.]",  # 긴 설명문
                r"(?:역사|전설|유래|기원)[^.]{50,}[.]",  # 배경 설명
                r"(?:라고 하며|라고 불리며|라고 전해지며)[^.]{30,}",
            ],
            "message": "정보 과잉 - 설명이 너무 길어요"
        },
        "repetition": {
            "patterns": [
                r"([가-힣]{3,})[가-힣]*\1[가-힣]*\1",  # 같은 단어 3회 반복
            ],
            "message": "단어 반복이 눈에 띄어요"
        },
        "slow_pacing": {
            "patterns": [
                r"(?:천천히|느릿느릿|서서히|조용히)[^.]{5,}(?:천천히|느릿느릿|서서히|조용히)",
                r"(?:한참|오래|오랫동안|시간이 지나)[^.]{20,}(?:한참|오래|오랫동안)",
            ],
            "message": "전개가 느려지고 있어요"
        },
        "excessive_description": {
            "patterns": [
                r"(?:아름다운|화려한|장엄한|웅장한)[^.]{10,}(?:아름다운|화려한|장엄한|웅장한)",
            ],
            "message": "묘사가 과하게 느껴져요"
        }
    }

    # 예측가능성 패턴
    PREDICTABILITY_PATTERNS = {
        "obvious_foreshadowing": {
            "patterns": [
                r"(?:앞으로|나중에|언젠가)[^.]{5,}(?:알게 될|깨닫게 될|후회할)",
                r"(?:이것이|이 순간이)[^.]{5,}(?:운명|시작)",
            ],
            "message": "복선이 너무 노골적이에요"
        },
        "cliche_setup": {
            "patterns": [
                r"(?:평범한|평화로운)[^.]{10,}(?:갑자기|그때)",  # 평화 → 사건
                r"(?:이상하게|왠지)[^.]{5,}(?:느낌|예감)",  # 불길한 예감
            ],
            "message": "전형적인 클리셰 전개예요"
        },
        "telegraphed_twist": {
            "patterns": [
                r"아무도[^.]{5,}몰랐[^.]{5,}(?:사실|비밀)",
                r"(?:정체|비밀)[^.]{5,}(?:곧|이제|드디어)[^.]{5,}(?:밝혀|드러나)",
            ],
            "message": "반전이 예상됩니다"
        }
    }

    # 혼란 유발 패턴
    CONFUSION_PATTERNS = {
        "unmotivated_action": {
            "patterns": [
                r"(?:갑자기|별다른 이유 없이|문득)[^.]{10,}(?:결심|결정|마음먹)",
            ],
            "message": "캐릭터 행동의 이유가 불명확해요"
        },
        "unclear_reference": {
            "patterns": [
                r"그것[^.]{20,}그것",  # 불명확한 대명사
                r"그[^.]{30,}그[^.]{30,}그",
            ],
            "message": "지시 대상이 불분명해요"
        },
        "timeline_jump": {
            "patterns": [
                r"(?:그때|그 순간)[^.]{50,}(?:이전에|전에|과거)",
            ],
            "message": "시간 흐름이 헷갈려요"
        }
    }

    # 몰입 유발 패턴 (긍정)
    ENGAGEMENT_PATTERNS = {
        "hook": {
            "patterns": [
                r"(?:그러나|하지만|그런데)[^.]{5,}(?:!|\?)",  # 반전
                r"(?:순간|찰나)[^.]{10,}(?:!)",  # 긴박함
            ],
            "score_bonus": 10,
            "message": "좋은 훅이에요!"
        },
        "tension": {
            "patterns": [
                r"(?:심장|숨|호흡)[^.]{5,}(?:멈추|빨라지|거칠어)",
                r"(?:긴장|살기|위기)[^.]{10,}(?:!)",
            ],
            "score_bonus": 8,
            "message": "긴장감이 살아있어요"
        },
        "emotional_payoff": {
            "patterns": [
                r"(?:눈물|울음|감동)[^.]{5,}(?:흘렀다|터졌다|밀려왔다)",
                r"(?:드디어|마침내|결국)[^.]{10,}(?:!)",
            ],
            "score_bonus": 12,
            "message": "감정적 보상이 있어요"
        },
        "action_beat": {
            "patterns": [
                r"(?:검|도|창|권)[^.]{5,}(?:스쳤다|베었다|꿰뚫었다|날아갔다)",
                r"(?:강|기|력|공)[^.]{5,}(?:폭발|터졌다|쏟아졌다)",
            ],
            "score_bonus": 7,
            "message": "액션이 역동적이에요"
        }
    }

    # 독자 유형별 가중치
    READER_WEIGHTS = {
        ReaderType.CASUAL: {
            "boredom": 1.5,      # 지루함에 민감
            "predictability": 0.5,  # 예측가능성에 관대
            "confusion": 1.0,
            "engagement": 1.2
        },
        ReaderType.HARDCORE: {
            "boredom": 0.5,      # 상세 설명 좋아함
            "predictability": 1.2,  # 클리셰 싫어함
            "confusion": 1.5,    # 설정 오류에 민감
            "engagement": 0.8
        },
        ReaderType.EMOTIONAL: {
            "boredom": 1.0,
            "predictability": 0.7,
            "confusion": 0.8,
            "engagement": 1.5   # 감정적 순간에 강하게 반응
        },
        ReaderType.CRITIC: {
            "boredom": 1.2,
            "predictability": 1.3,
            "confusion": 1.3,
            "engagement": 1.0
        },
        ReaderType.SPEED: {
            "boredom": 2.0,      # 느린 전개 매우 싫어함
            "predictability": 0.5,
            "confusion": 0.7,
            "engagement": 1.0
        }
    }

    def __init__(self):
        self.reading_history: List[Dict] = []

    def simulate_reading(
        self,
        manuscript: str,
        reader_type: ReaderType = ReaderType.CASUAL,
        context: Dict[str, Any] = None
    ) -> ReadingFeedback:
        """
        독자 시뮬레이션 실행

        Args:
            manuscript: 원고 텍스트
            reader_type: 독자 유형
            context: 추가 맥락 (선택적)

        Returns:
            ReadingFeedback
        """
        if not manuscript:
            return ReadingFeedback(
                reader_type=reader_type,
                overall_mood=ReaderMood.NEUTRAL,
                engagement_score=50,
                summary="원고가 비어있습니다."
            )

        weights = self.READER_WEIGHTS[reader_type]

        # 각 요소 감지
        boredom = self._detect_boredom(manuscript)
        predictability = self._detect_predictability(manuscript)
        confusion = self._detect_confusion(manuscript)
        engagement = self._detect_engagement(manuscript)

        # 점수 계산
        base_score = 70

        # 부정적 요소 감점
        base_score -= len(boredom) * 5 * weights["boredom"]
        base_score -= len(predictability) * 4 * weights["predictability"]
        base_score -= len(confusion) * 6 * weights["confusion"]

        # 긍정적 요소 가점
        engagement_bonus = sum(e.get("bonus", 5) for e in engagement)
        base_score += engagement_bonus * weights["engagement"]

        final_score = max(0, min(100, int(base_score)))

        # 기분 결정
        mood = self._determine_mood(final_score, boredom, confusion)

        # 피드백 조합
        positive_moments = [{"type": e["type"], "message": e["message"]} for e in engagement]
        negative_moments = (
            [{"type": "boredom", "message": b} for b in boredom] +
            [{"type": "predictability", "message": p} for p in predictability] +
            [{"type": "confusion", "message": c} for c in confusion]
        )

        # 요약 생성
        summary = self._generate_summary(
            reader_type, mood, final_score,
            boredom, predictability, confusion, engagement
        )

        return ReadingFeedback(
            reader_type=reader_type,
            overall_mood=mood,
            engagement_score=final_score,
            positive_moments=positive_moments,
            negative_moments=negative_moments,
            boredom_flags=boredom,
            confusion_flags=confusion,
            predictability_flags=predictability,
            summary=summary
        )

    def _detect_boredom(self, text: str) -> List[str]:
        """지루함 유발 요소 감지"""
        flags = []
        for name, config in self.BOREDOM_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    flags.append(config["message"])
                    break
        return flags

    def _detect_predictability(self, text: str) -> List[str]:
        """예측가능성 감지"""
        flags = []
        for name, config in self.PREDICTABILITY_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    flags.append(config["message"])
                    break
        return flags

    def _detect_confusion(self, text: str) -> List[str]:
        """혼란 유발 요소 감지"""
        flags = []
        for name, config in self.CONFUSION_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    flags.append(config["message"])
                    break
        return flags

    def _detect_engagement(self, text: str) -> List[Dict]:
        """몰입 유발 요소 감지"""
        moments = []
        for name, config in self.ENGAGEMENT_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    moments.append({
                        "type": name,
                        "bonus": config["score_bonus"],
                        "message": config["message"]
                    })
                    break
        return moments

    def _determine_mood(
        self,
        score: int,
        boredom: List[str],
        confusion: List[str]
    ) -> ReaderMood:
        """독자 기분 결정"""
        if score >= 85:
            return ReaderMood.EXCITED
        elif score >= 75:
            return ReaderMood.ENGAGED
        elif score >= 65:
            return ReaderMood.CURIOUS
        elif score >= 55:
            return ReaderMood.NEUTRAL
        elif len(confusion) >= 2:
            return ReaderMood.CONFUSED
        elif len(boredom) >= 2:
            return ReaderMood.BORED
        elif score < 40:
            return ReaderMood.FRUSTRATED
        else:
            return ReaderMood.NEUTRAL

    def _generate_summary(
        self,
        reader_type: ReaderType,
        mood: ReaderMood,
        score: int,
        boredom: List[str],
        predictability: List[str],
        confusion: List[str],
        engagement: List[Dict]
    ) -> str:
        """독자 관점 요약 생성"""
        type_name = reader_type.value[0]
        mood_name = mood.value

        parts = [f"[{type_name} 독자의 반응: {mood_name}]"]

        if score >= 80:
            parts.append("이 에피소드 정말 재밌네요!")
        elif score >= 60:
            parts.append("괜찮은 에피소드예요.")
        elif score >= 40:
            parts.append("조금 아쉬운 부분이 있어요.")
        else:
            parts.append("읽기 힘드네요...")

        if engagement:
            parts.append(f"좋았던 점: {engagement[0]['message']}")

        if boredom:
            parts.append(f"아쉬운 점: {boredom[0]}")

        if confusion:
            parts.append(f"이해 안 되는 점: {confusion[0]}")

        if predictability:
            parts.append(f"뻔한 점: {predictability[0]}")

        return " ".join(parts)

    def simulate_all_readers(self, manuscript: str) -> Dict[str, ReadingFeedback]:
        """모든 독자 유형으로 시뮬레이션"""
        results = {}
        for reader_type in ReaderType:
            feedback = self.simulate_reading(manuscript, reader_type)
            results[reader_type.value[0]] = feedback
        return results

    def calculate_engagement_score(self, manuscript: str) -> Dict[str, Any]:
        """
        종합 몰입도 점수 계산

        Returns:
            {
                "overall_score": int,
                "by_reader_type": {type: score},
                "strengths": [],
                "weaknesses": []
            }
        """
        all_results = self.simulate_all_readers(manuscript)

        scores = {name: fb.engagement_score for name, fb in all_results.items()}
        overall = sum(scores.values()) // len(scores)

        # 강점/약점 집계
        all_positive = []
        all_negative = []
        for fb in all_results.values():
            all_positive.extend([m["message"] for m in fb.positive_moments])
            all_negative.extend(fb.boredom_flags + fb.confusion_flags + fb.predictability_flags)

        # 중복 제거 및 빈도순 정렬
        positive_counter = Counter(all_positive)
        negative_counter = Counter(all_negative)

        return {
            "overall_score": overall,
            "by_reader_type": scores,
            "strengths": [msg for msg, _ in positive_counter.most_common(3)],
            "weaknesses": [msg for msg, _ in negative_counter.most_common(3)]
        }

    def generate_reader_prompt(self, feedback: ReadingFeedback) -> str:
        """Writer용 독자 피드백 프롬프트 생성"""
        lines = [
            "",
            "=" * 50,
            f"[V50.4 독자 시뮬레이션 - {feedback.reader_type.value[0]}]",
            "=" * 50,
            f"몰입도: {feedback.engagement_score}/100 ({feedback.overall_mood.value})",
            "",
        ]

        if feedback.positive_moments:
            lines.append("👍 좋은 점:")
            for m in feedback.positive_moments[:3]:
                lines.append(f"   - {m['message']}")

        if feedback.negative_moments:
            lines.append("")
            lines.append("👎 개선 필요:")
            for m in feedback.negative_moments[:3]:
                lines.append(f"   - {m['message']}")

        lines.append("")
        lines.append(f"💬 {feedback.summary}")
        lines.append("=" * 50)

        return "\n".join(lines)

    def analyze_episode_series(
        self,
        manuscripts: List[str],
        reader_type: ReaderType = ReaderType.CASUAL
    ) -> Dict[str, Any]:
        """
        여러 에피소드 연속 분석

        독자가 시리즈를 읽으면서 어떻게 반응하는지 추적
        """
        feedbacks = []
        mood_history = []
        score_history = []

        for i, ms in enumerate(manuscripts, 1):
            fb = self.simulate_reading(ms, reader_type)
            feedbacks.append(fb)
            mood_history.append(fb.overall_mood.value)
            score_history.append(fb.engagement_score)

        # 트렌드 분석
        avg_score = sum(score_history) / len(score_history) if score_history else 50
        trend = "상승" if score_history and score_history[-1] > score_history[0] else "하락"

        # 드롭 지점 (몰입도가 급락한 에피소드)
        drop_points = []
        for i in range(1, len(score_history)):
            if score_history[i] < score_history[i-1] - 15:
                drop_points.append(i + 1)

        return {
            "episode_count": len(manuscripts),
            "average_score": int(avg_score),
            "trend": trend,
            "score_history": score_history,
            "mood_history": mood_history,
            "drop_points": drop_points,
            "recommendation": self._generate_series_recommendation(avg_score, trend, drop_points)
        }

    def _generate_series_recommendation(
        self,
        avg_score: float,
        trend: str,
        drop_points: List[int]
    ) -> str:
        """시리즈 분석 권장사항"""
        parts = []

        if avg_score >= 75:
            parts.append("전반적으로 독자 반응이 좋습니다.")
        elif avg_score >= 60:
            parts.append("평균적인 반응입니다.")
        else:
            parts.append("독자 이탈 위험이 있습니다.")

        if trend == "하락":
            parts.append("몰입도가 하락 추세입니다. 긴장감을 높여주세요.")

        if drop_points:
            parts.append(f"에피소드 {drop_points}에서 급락이 있었습니다. 해당 에피소드를 점검하세요.")

        return " ".join(parts)
