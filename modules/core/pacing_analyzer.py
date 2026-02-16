"""
[V51.1] Pacing Analyzer (호흡 분석기)
문장/문단 단위 호흡 분석 - LLM 비용 0원

기능:
1. 문장 길이 분포 분석
2. 긴박감/이완 구간 탐지
3. 대화:서술 비율
4. 장면 전환 빈도
5. 문단 밀도 분석

사용:
    analyzer = PacingAnalyzer()
    result = analyzer.analyze(manuscript)
    prompt = analyzer.generate_pacing_prompt(result)
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PacingZone(Enum):
    """호흡 구간 타입"""

    RAPID = "rapid"  # 짧은 문장 연속 (긴박)
    FLOWING = "flowing"  # 중간 길이 (자연스러운 흐름)
    DENSE = "dense"  # 긴 문장 연속 (설명/묘사)
    DIALOGUE = "dialogue"  # 대화 중심
    MIXED = "mixed"  # 혼합


@dataclass
class PacingSegment:
    """호흡 구간"""

    zone_type: PacingZone
    start_char: int
    end_char: int
    avg_sentence_length: float
    sentence_count: int
    dialogue_ratio: float  # 0-1


@dataclass
class PacingAnalysis:
    """호흡 분석 결과"""

    # 기본 통계
    total_chars: int
    total_sentences: int
    total_paragraphs: int
    avg_sentence_length: float
    sentence_length_std: float  # 표준편차 (다양성)

    # 비율
    dialogue_ratio: float  # 대화 비율 (0-1)
    short_sentence_ratio: float  # 짧은 문장 비율 (<20자)
    long_sentence_ratio: float  # 긴 문장 비율 (>80자)

    # 구간 분석
    segments: list[PacingSegment] = field(default_factory=list)

    # 장면 전환
    scene_break_count: int = 0
    avg_scene_length: float = 0

    # 점수 (0-100)
    pacing_score: int = 70

    # 문제점
    issues: list[str] = field(default_factory=list)

    # 권장사항
    suggestions: list[str] = field(default_factory=list)


class PacingAnalyzer:
    """호흡 분석기"""

    # 문장 분리 패턴
    SENTENCE_PATTERN = re.compile(r"[^.!?。？！]+[.!?。？！]+")

    # 대화 패턴
    DIALOGUE_PATTERN = re.compile(r'["\'"「『].*?["\'"」』]|"[^"]*"')

    # 장면 전환 패턴
    SCENE_BREAK_PATTERNS = [
        re.compile(r"\n\s*\*\s*\*\s*\*\s*\n"),  # * * *
        re.compile(r"\n\s*[#]+\s*\n"),  # ###
        re.compile(r"\n\s*[-]{3,}\s*\n"),  # ---
        re.compile(r"\n\n\n+"),  # 빈 줄 3개 이상
    ]

    # 시간 경과 표현
    TIME_SKIP_PATTERNS = [
        re.compile(r"(다음\s*날|이튿날|며칠\s*(후|뒤)|일주일\s*(후|뒤)|한\s*달\s*(후|뒤))"),
        re.compile(r"(그로부터|그\s*후|시간이\s*흘러|세월이)"),
        re.compile(r"(아침이\s*밝|해가\s*(지|뜨)|밤이\s*깊)"),
    ]

    # 이상적인 범위
    IDEAL_DIALOGUE_RATIO = (0.25, 0.45)  # 25-45%
    IDEAL_AVG_SENTENCE = (25, 50)  # 25-50자
    IDEAL_SHORT_RATIO = (0.15, 0.35)  # 15-35%
    IDEAL_LONG_RATIO = (0.05, 0.20)  # 5-20%

    def __init__(self) -> None:
        self.history: list[PacingAnalysis] = []

    def analyze(self, manuscript: str) -> PacingAnalysis:
        """
        원고 호흡 분석

        Args:
            manuscript: 원고 텍스트

        Returns:
            PacingAnalysis: 분석 결과
        """
        if not manuscript or len(manuscript) < 100:
            return PacingAnalysis(
                total_chars=len(manuscript) if manuscript else 0,
                total_sentences=0,
                total_paragraphs=0,
                avg_sentence_length=0,
                sentence_length_std=0,
                dialogue_ratio=0,
                short_sentence_ratio=0,
                long_sentence_ratio=0,
                pacing_score=50,
                issues=["원고가 너무 짧습니다"],
            )

        # 1. 기본 분석
        sentences = self._extract_sentences(manuscript)
        paragraphs = [p for p in manuscript.split("\n\n") if p.strip()]

        # 문장 길이 통계
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        if not sentence_lengths:
            sentence_lengths = [0]

        avg_len = sum(sentence_lengths) / len(sentence_lengths)
        std_len = self._calculate_std(sentence_lengths, avg_len)

        # 2. 비율 계산
        dialogue_chars = sum(len(m.group()) for m in self.DIALOGUE_PATTERN.finditer(manuscript))
        dialogue_ratio = dialogue_chars / len(manuscript) if manuscript else 0

        short_count = sum(1 for l in sentence_lengths if l < 20)
        long_count = sum(1 for l in sentence_lengths if l > 80)
        total_sentences = len(sentence_lengths)

        short_ratio = short_count / total_sentences if total_sentences else 0
        long_ratio = long_count / total_sentences if total_sentences else 0

        # 3. 장면 전환 분석
        scene_breaks = self._count_scene_breaks(manuscript)
        time_skips = self._count_time_skips(manuscript)
        total_breaks = scene_breaks + time_skips

        avg_scene_len = len(manuscript) / (total_breaks + 1) if total_breaks >= 0 else len(manuscript)

        # 4. 구간 분석
        segments = self._analyze_segments(manuscript, sentences)

        # 5. 문제점 탐지
        issues = []
        suggestions = []

        # 대화 비율 체크
        if dialogue_ratio < self.IDEAL_DIALOGUE_RATIO[0]:
            issues.append(f"대화 비율 낮음 ({dialogue_ratio:.0%}) - 캐릭터 상호작용 부족")
            suggestions.append("대화 장면을 추가하여 캐릭터 간 상호작용을 늘리세요")
        elif dialogue_ratio > self.IDEAL_DIALOGUE_RATIO[1]:
            issues.append(f"대화 비율 높음 ({dialogue_ratio:.0%}) - 서술/묘사 부족")
            suggestions.append("서술과 묘사를 추가하여 장면을 풍부하게 만드세요")

        # 문장 길이 체크
        if avg_len < self.IDEAL_AVG_SENTENCE[0]:
            issues.append(f"평균 문장 짧음 ({avg_len:.0f}자) - 호흡이 급함")
            suggestions.append("일부 장면에서 문장을 연결하여 호흡을 늘리세요")
        elif avg_len > self.IDEAL_AVG_SENTENCE[1]:
            issues.append(f"평균 문장 길음 ({avg_len:.0f}자) - 호흡이 무거움")
            suggestions.append("긴 문장을 분리하여 가독성을 높이세요")

        # 단조로움 체크
        if std_len < 10:
            issues.append("문장 길이가 단조로움 - 리듬감 부족")
            suggestions.append("짧은 문장과 긴 문장을 섞어 리듬감을 만드세요")

        # 긴 문장 과다
        if long_ratio > self.IDEAL_LONG_RATIO[1]:
            issues.append(f"긴 문장 과다 ({long_ratio:.0%}) - 가독성 저하")
            suggestions.append("80자 이상 문장을 분리하세요")

        # 장면 전환 체크
        if total_breaks == 0 and len(manuscript) > 3000:
            issues.append("장면 전환 없음 - 단조로운 전개")
            suggestions.append("시간 경과나 장소 변화로 리듬을 만드세요")

        # 연속 구간 체크
        rapid_segments = [s for s in segments if s.zone_type == PacingZone.RAPID]
        dense_segments = [s for s in segments if s.zone_type == PacingZone.DENSE]

        if len(rapid_segments) > 3:
            issues.append("급박한 구간 연속 - 독자 피로도 상승")
            suggestions.append("긴박한 장면 사이에 휴식 구간을 넣으세요")

        if len(dense_segments) > 2:
            issues.append("설명 구간 과다 - 전개 지연")
            suggestions.append("설명보다 장면으로 보여주세요 (Show, don't tell)")

        # 6. 점수 계산
        pacing_score = self._calculate_score(dialogue_ratio, avg_len, std_len, short_ratio, long_ratio, len(issues))

        result = PacingAnalysis(
            total_chars=len(manuscript),
            total_sentences=total_sentences,
            total_paragraphs=len(paragraphs),
            avg_sentence_length=avg_len,
            sentence_length_std=std_len,
            dialogue_ratio=dialogue_ratio,
            short_sentence_ratio=short_ratio,
            long_sentence_ratio=long_ratio,
            segments=segments,
            scene_break_count=total_breaks,
            avg_scene_length=avg_scene_len,
            pacing_score=pacing_score,
            issues=issues,
            suggestions=suggestions,
        )

        self.history.append(result)
        return result

    def _extract_sentences(self, text: str) -> list[str]:
        """문장 추출"""
        # 대화 내부의 문장 부호 보호
        protected = text
        for m in self.DIALOGUE_PATTERN.finditer(text):
            original = m.group()
            replaced = original.replace(".", "\x00").replace("!", "\x01").replace("?", "\x02")
            protected = protected.replace(original, replaced, 1)

        sentences = self.SENTENCE_PATTERN.findall(protected)

        # 복원
        return [s.replace("\x00", ".").replace("\x01", "!").replace("\x02", "?") for s in sentences]

    def _calculate_std(self, values: list[float], mean: float) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    def _count_scene_breaks(self, text: str) -> int:
        """장면 전환 횟수"""
        count = 0
        for pattern in self.SCENE_BREAK_PATTERNS:
            count += len(pattern.findall(text))
        return count

    def _count_time_skips(self, text: str) -> int:
        """시간 경과 표현 횟수"""
        count = 0
        for pattern in self.TIME_SKIP_PATTERNS:
            count += len(pattern.findall(text))
        return count

    def _analyze_segments(self, text: str, sentences: list[str]) -> list[PacingSegment]:
        """구간별 호흡 분석"""
        segments = []
        if not sentences:
            return segments

        # 10문장 단위로 분석
        window_size = 10
        for i in range(0, len(sentences), window_size):
            window = sentences[i : i + window_size]
            if not window:
                continue

            lengths = [len(s.strip()) for s in window]
            avg_len = sum(lengths) / len(lengths)

            # 대화 비율 계산
            window_text = " ".join(window)
            dialogue_chars = sum(len(m.group()) for m in self.DIALOGUE_PATTERN.finditer(window_text))
            dialogue_ratio = dialogue_chars / len(window_text) if window_text else 0

            # 구간 타입 결정
            if dialogue_ratio > 0.5:
                zone_type = PacingZone.DIALOGUE
            elif avg_len < 25:
                zone_type = PacingZone.RAPID
            elif avg_len > 60:
                zone_type = PacingZone.DENSE
            elif avg_len < 45:
                zone_type = PacingZone.FLOWING
            else:
                zone_type = PacingZone.MIXED

            # 대략적인 문자 위치 계산
            start_char = sum(len(s) for s in sentences[:i])
            end_char = start_char + sum(len(s) for s in window)

            segments.append(
                PacingSegment(
                    zone_type=zone_type,
                    start_char=start_char,
                    end_char=end_char,
                    avg_sentence_length=avg_len,
                    sentence_count=len(window),
                    dialogue_ratio=dialogue_ratio,
                )
            )

        return segments

    def _calculate_score(
        self,
        dialogue_ratio: float,
        avg_len: float,
        std_len: float,
        short_ratio: float,
        long_ratio: float,
        issue_count: int,
    ) -> int:
        """호흡 점수 계산 (0-100)"""
        score = 100

        # 대화 비율 감점
        if dialogue_ratio < self.IDEAL_DIALOGUE_RATIO[0]:
            score -= 10
        elif dialogue_ratio > self.IDEAL_DIALOGUE_RATIO[1]:
            score -= 10

        # 문장 길이 감점
        if avg_len < self.IDEAL_AVG_SENTENCE[0]:
            score -= 10
        elif avg_len > self.IDEAL_AVG_SENTENCE[1]:
            score -= 10

        # 다양성 감점
        if std_len < 10:
            score -= 15
        elif std_len > 40:
            score -= 5  # 너무 들쭉날쭉도 문제

        # 긴 문장 과다 감점
        if long_ratio > self.IDEAL_LONG_RATIO[1]:
            score -= 10

        # 이슈 개수 감점
        score -= issue_count * 5

        return max(0, min(100, score))

    def generate_pacing_prompt(self, analysis: PacingAnalysis = None) -> str:
        """
        Writer용 호흡 가이드 프롬프트 생성

        Args:
            analysis: 분석 결과 (없으면 최근 분석 사용)
        """
        if analysis is None:
            if not self.history:
                return ""
            analysis = self.history[-1]

        if not analysis.issues and not analysis.suggestions:
            return ""

        lines = ["[V51 호흡 가이드]"]

        # 현재 상태 요약
        lines.append(f"현재 호흡 점수: {analysis.pacing_score}/100")
        lines.append(f"대화:서술 = {analysis.dialogue_ratio:.0%}:{1 - analysis.dialogue_ratio:.0%}")
        lines.append(f"평균 문장: {analysis.avg_sentence_length:.0f}자")

        # 주요 제안
        if analysis.suggestions:
            lines.append("\n개선 포인트:")
            for s in analysis.suggestions[:3]:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def compare_episodes(self, analyses: list[PacingAnalysis]) -> dict[str, Any]:
        """
        여러 에피소드 호흡 비교

        Args:
            analyses: 분석 결과 리스트

        Returns:
            Dict: 비교 결과
        """
        if not analyses:
            return {}

        scores = [a.pacing_score for a in analyses]
        dialogue_ratios = [a.dialogue_ratio for a in analyses]
        avg_lengths = [a.avg_sentence_length for a in analyses]

        # [V70] 단일 요소면 비교 불가 → 'stable'
        if len(analyses) < 2:
            trend = "stable"
        else:
            trend = "improving" if scores[-1] > scores[0] else ("stable" if scores[-1] == scores[0] else "declining")

        return {
            "score_trend": trend,
            "avg_score": sum(scores) / len(scores),
            "score_range": (min(scores), max(scores)),
            "dialogue_consistency": max(dialogue_ratios) - min(dialogue_ratios) < 0.15,
            "length_consistency": max(avg_lengths) - min(avg_lengths) < 15,
            "total_issues": sum(len(a.issues) for a in analyses),
        }

    def get_zone_distribution(self, analysis: PacingAnalysis) -> dict[PacingZone, float]:
        """구간 타입 분포 계산"""
        if not analysis.segments:
            return {}

        total_chars = sum(s.end_char - s.start_char for s in analysis.segments)
        if total_chars == 0:
            return {}

        distribution = {}
        for zone in PacingZone:
            zone_chars = sum(s.end_char - s.start_char for s in analysis.segments if s.zone_type == zone)
            distribution[zone] = zone_chars / total_chars

        return distribution
