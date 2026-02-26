"""
[V53.3] Confidence Calibration (신뢰도 보정)
에이전트 출력에 신뢰도 점수를 부여하여 추가 검증 트리거

핵심: 낮은 신뢰도 출력은 추가 검증, 높은 신뢰도는 빠른 통과

원리:
1. 에이전트 출력 분석 (Python 휴리스틱 + LLM)
2. 신뢰도 점수 계산 (0-100)
3. 임계값 미만이면 추가 검증 권장
4. 신뢰도 메타데이터 반환

비용: +$0.01/검증 (LLM 사용 시)

사용:
    calibrator = ConfidenceCalibrator(api_client)
    result = calibrator.assess(
        content=manuscript,
        content_type="manuscript",
        context={"blueprint": bp}
    )
    if result.needs_extra_verification:
        # 추가 검증 수행
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from modules.core.constants import ManuscriptLimits


class ContentType(Enum):
    """콘텐츠 유형"""

    MANUSCRIPT = "manuscript"
    BLUEPRINT = "blueprint"
    ARC_DESIGN = "arc_design"


class ConfidenceLevel(Enum):
    """신뢰도 수준"""

    VERY_HIGH = "very_high"  # 90-100: 빠른 통과
    HIGH = "high"  # 75-89: 일반 검증
    MEDIUM = "medium"  # 50-74: 주의 필요
    LOW = "low"  # 25-49: 추가 검증 권장
    VERY_LOW = "very_low"  # 0-24: 재생성 권장


@dataclass
class ConfidenceResult:
    """신뢰도 평가 결과"""

    score: int  # 0-100
    level: ConfidenceLevel
    factors: dict[str, int]  # 각 요소별 점수
    concerns: list[str]  # 우려 사항
    needs_extra_verification: bool
    recommendation: str  # "pass", "verify", "regenerate"


class ConfidenceCalibrator:
    """신뢰도 보정 시스템"""

    # 신뢰도 요소별 가중치
    FACTOR_WEIGHTS = {
        "length_adequacy": 15,  # 적절한 길이
        "structure_quality": 20,  # 구조적 완성도
        "continuity_signals": 20,  # 연속성 신호
        "dialogue_ratio": 10,  # 대화 비율
        "sensory_detail": 10,  # 감각 묘사
        "scene_coverage": 15,  # 씬 반영도
        "ending_hook": 10,  # 클리프행어
    }

    # 임계값
    THRESHOLDS = {
        "extra_verification": 50,  # 이 미만이면 추가 검증
        "regenerate": 30,  # 이 미만이면 재생성 권장
        "fast_pass": 85,  # 이 이상이면 빠른 통과
    }

    def __init__(self, api_client=None, use_llm: bool = False):
        """
        Args:
            api_client: Google GenAI 클라이언트 (LLM 사용 시)
            use_llm: LLM 기반 평가 사용 여부 (기본 Python만)
        """
        self.client = api_client
        self.use_llm = use_llm and api_client is not None
        self.model = "gemini-2.5-flash"
        self.enabled = True

    def _score_to_level(self, score: int) -> ConfidenceLevel:
        """점수 → 신뢰도 수준"""
        if score >= 90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 75:
            return ConfidenceLevel.HIGH
        elif score >= 50:
            return ConfidenceLevel.MEDIUM
        elif score >= 25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def assess(
        self, content: str, content_type: str = "manuscript", context: dict[str, Any] = None
    ) -> ConfidenceResult:
        """
        신뢰도 평가

        Args:
            content: 평가할 콘텐츠
            content_type: "manuscript", "blueprint", "arc_design"
            context: 참조 컨텍스트 (blueprint, prev_manuscript 등)

        Returns:
            ConfidenceResult
        """
        if not self.enabled:
            return ConfidenceResult(
                score=75,
                level=ConfidenceLevel.HIGH,
                factors={},
                concerns=[],
                needs_extra_verification=False,
                recommendation="pass",
            )

        context = context or {}

        if content_type == "manuscript":
            return self._assess_manuscript(content, context)
        elif content_type == "blueprint":
            return self._assess_blueprint(content, context)
        else:
            return self._assess_generic(content, context)

    def _assess_manuscript(self, manuscript: str, context: dict[str, Any]) -> ConfidenceResult:
        """원고 신뢰도 평가"""
        factors = {}
        concerns = []

        # 1. 길이 적절성 (15점)
        length = len(manuscript)
        if ManuscriptLimits.TARGET_LENGTH <= length <= 12000:
            factors["length_adequacy"] = 15
        elif (
            ManuscriptLimits.MIN_LENGTH <= length < ManuscriptLimits.TARGET_LENGTH
            or 12000 < length <= ManuscriptLimits.MAX_LENGTH
        ):
            factors["length_adequacy"] = 10
            concerns.append(f"길이가 다소 {'짧음' if length < 5000 else '김'} ({length}자)")
        elif 3000 <= length < ManuscriptLimits.MIN_LENGTH:
            factors["length_adequacy"] = 5
            concerns.append(f"길이 부족 ({length}자)")
        else:
            factors["length_adequacy"] = 0
            concerns.append(f"길이 심각하게 {'부족' if length < 3000 else '초과'} ({length}자)")

        # 2. 구조적 완성도 (20점)
        structure_score = 0

        # 시작부 존재
        if len(manuscript) > 100:
            structure_score += 5

        # 문단 분리
        paragraphs = manuscript.split("\n\n")
        if 5 <= len(paragraphs) <= 50:
            structure_score += 5
        elif len(paragraphs) < 5:
            concerns.append("문단 분리 부족")

        # 대화와 묘사 혼합
        dialogue_count = manuscript.count('"') + manuscript.count("「")
        narration_ratio = (len(manuscript) - dialogue_count * 10) / max(len(manuscript), 1)
        if 0.3 <= narration_ratio <= 0.8:
            structure_score += 5
        else:
            concerns.append("대화/묘사 비율 불균형")

        # 끝부분 존재
        if manuscript.strip() and manuscript.strip()[-1] in '.!?"」':  # [V70] 빈 문자열 방어
            structure_score += 5

        factors["structure_quality"] = structure_score

        # 3. 연속성 신호 (20점)
        continuity_score = 0
        prev_ms = context.get("prev_manuscript", "")

        if prev_ms:
            # 직전 화 키워드가 현재 화에 있는지
            prev_keywords = set(re.findall(r"[\w가-힣]{3,}", prev_ms[-1000:]))
            curr_keywords = set(re.findall(r"[\w가-힣]{3,}", manuscript[:2000]))
            overlap = len(prev_keywords & curr_keywords)

            if overlap >= 10:
                continuity_score = 20
            elif overlap >= 5:
                continuity_score = 15
            elif overlap >= 2:
                continuity_score = 10
                concerns.append("직전 화와의 연결 신호 약함")
            else:
                continuity_score = 5
                concerns.append("직전 화와의 연결이 거의 없음")
        else:
            continuity_score = 15  # 이전 화 없으면 기본값

        factors["continuity_signals"] = continuity_score

        # 4. 대화 비율 (10점)
        total_dialogue = manuscript.count('"') + manuscript.count("「")
        dialogue_ratio = total_dialogue / max(len(manuscript) / 100, 1)

        if 3 <= dialogue_ratio <= 15:
            factors["dialogue_ratio"] = 10
        elif 1 <= dialogue_ratio < 3 or 15 < dialogue_ratio <= 20:
            factors["dialogue_ratio"] = 7
            concerns.append(f"대화 {'부족' if dialogue_ratio < 3 else '과다'}")
        else:
            factors["dialogue_ratio"] = 3
            concerns.append(f"대화 비율 문제 ({dialogue_ratio:.1f})")

        # 5. 감각 묘사 (10점)
        sensory_words = ["보이", "들리", "느껴", "냄새", "맛", "차가", "따뜻", "뜨거", "부드", "거칠"]
        sensory_count = sum(1 for w in sensory_words if w in manuscript)

        if sensory_count >= 10:
            factors["sensory_detail"] = 10
        elif sensory_count >= 5:
            factors["sensory_detail"] = 7
        elif sensory_count >= 2:
            factors["sensory_detail"] = 4
            concerns.append("감각 묘사 부족")
        else:
            factors["sensory_detail"] = 1
            concerns.append("감각 묘사 거의 없음")

        # 6. 씬 반영도 (15점)
        blueprint = context.get("blueprint", {})
        if blueprint and isinstance(blueprint, dict):
            scene_breakdown = blueprint.get("scene_breakdown", {})
            if scene_breakdown and isinstance(scene_breakdown, dict):  # [V70] list 타입 방어
                scene_keywords = []
                for scene_data in scene_breakdown.values():
                    if isinstance(scene_data, dict):
                        desc = scene_data.get("summary", scene_data.get("description", ""))
                        for ev in scene_data.get("key_events") or []:
                            desc += " " + str(ev)
                        scene_keywords.extend(re.findall(r"[\w가-힣]{2,}", desc)[:3])

                matched = sum(1 for kw in scene_keywords if kw in manuscript)
                ratio = matched / max(len(scene_keywords), 1)

                if ratio >= 0.7:
                    factors["scene_coverage"] = 15
                elif ratio >= 0.5:
                    factors["scene_coverage"] = 10
                elif ratio >= 0.3:
                    factors["scene_coverage"] = 5
                    concerns.append("Blueprint 씬 반영 부족")
                else:
                    factors["scene_coverage"] = 0
                    concerns.append("Blueprint 씬 대부분 미반영")
            else:
                factors["scene_coverage"] = 10  # Blueprint 없으면 기본값
        else:
            factors["scene_coverage"] = 10

        # 7. 클리프행어 (10점)
        ending = manuscript[-500:] if len(manuscript) > 500 else manuscript
        hook_signals = ["...", "!", "?", "그때", "순간", "갑자기", "하지만", "그러나"]
        hook_count = sum(1 for h in hook_signals if h in ending)

        if hook_count >= 3:
            factors["ending_hook"] = 10
        elif hook_count >= 1:
            factors["ending_hook"] = 6
        else:
            factors["ending_hook"] = 2
            concerns.append("클리프행어 신호 약함")

        # 총점 계산
        total_score = sum(factors.values())

        # 결과 생성
        level = self._score_to_level(total_score)
        needs_extra = total_score < self.THRESHOLDS["extra_verification"]

        if total_score >= self.THRESHOLDS["fast_pass"]:
            recommendation = "pass"
        elif total_score >= self.THRESHOLDS["extra_verification"]:
            recommendation = "verify"
        elif total_score >= self.THRESHOLDS["regenerate"]:
            recommendation = "verify"
        else:
            recommendation = "regenerate"

        return ConfidenceResult(
            score=total_score,
            level=level,
            factors=factors,
            concerns=concerns,
            needs_extra_verification=needs_extra,
            recommendation=recommendation,
        )

    def _assess_blueprint(self, content: str, context: dict[str, Any]) -> ConfidenceResult:
        """블루프린트 신뢰도 평가"""
        factors = {}
        concerns = []

        # Blueprint는 보통 dict이므로 문자열 변환
        if isinstance(content, dict):
            bp = content
            content = json.dumps(content, ensure_ascii=False)
        else:
            try:
                bp = json.loads(content)
            except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse failure
                bp = {}

        # 1. 필수 필드 존재 (30점)
        required_fields = ["integrated_scenario", "scene_breakdown"]
        field_score = 0
        for field in required_fields:
            if field in bp and bp[field]:
                field_score += 15
            else:
                concerns.append(f"필수 필드 누락: {field}")
        factors["required_fields"] = field_score

        # 2. 씬 개수 (20점)
        scene_breakdown = bp.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict):
            scene_breakdown = {}
        scene_count = len(scene_breakdown)

        if 4 <= scene_count <= 7:
            factors["scene_count"] = 20
        elif 3 <= scene_count <= 8:
            factors["scene_count"] = 15
        elif scene_count > 0:
            factors["scene_count"] = 10
            concerns.append(f"씬 개수 {'부족' if scene_count < 4 else '과다'} ({scene_count})")
        else:
            factors["scene_count"] = 0
            concerns.append("씬이 없음")

        # 3. 시나리오 길이 (20점)
        scenario = bp.get("integrated_scenario", "")
        scenario_len = len(scenario) if isinstance(scenario, str) else 0

        if scenario_len >= 1000:
            factors["scenario_length"] = 20
        elif scenario_len >= 500:
            factors["scenario_length"] = 15
        elif scenario_len >= 200:
            factors["scenario_length"] = 10
            concerns.append("시나리오 설명 부족")
        else:
            factors["scenario_length"] = 0
            concerns.append("시나리오가 거의 없음")

        # 4. 엔딩 훅 존재 (15점)
        ending_hook = bp.get("ending_hook") or bp.get("cliffhanger", "")
        if ending_hook and len(str(ending_hook)) > 10:
            factors["ending_hook"] = 15
        elif ending_hook:
            factors["ending_hook"] = 10
        else:
            factors["ending_hook"] = 0
            concerns.append("ending_hook 없음")

        # 5. 씬 상세도 (15점)
        detail_score = 0
        if scene_breakdown and isinstance(scene_breakdown, dict):  # [V70] list 타입 방어
            detailed_count = 0
            for scene_data in scene_breakdown.values():
                if isinstance(scene_data, dict):
                    desc = scene_data.get("description", "")
                    if len(str(desc)) >= 50:
                        detailed_count += 1

            ratio = detailed_count / len(scene_breakdown)
            if ratio >= 0.8:
                detail_score = 15
            elif ratio >= 0.5:
                detail_score = 10
            else:
                detail_score = 5
                concerns.append("씬 설명이 상세하지 않음")

        factors["scene_detail"] = detail_score

        # 총점
        total_score = sum(factors.values())
        level = self._score_to_level(total_score)
        needs_extra = total_score < self.THRESHOLDS["extra_verification"]

        if total_score >= self.THRESHOLDS["fast_pass"]:
            recommendation = "pass"
        elif total_score >= self.THRESHOLDS["regenerate"]:
            recommendation = "verify"
        else:
            recommendation = "regenerate"

        return ConfidenceResult(
            score=total_score,
            level=level,
            factors=factors,
            concerns=concerns,
            needs_extra_verification=needs_extra,
            recommendation=recommendation,
        )

    def _assess_generic(self, content: str, context: dict[str, Any]) -> ConfidenceResult:
        """일반 콘텐츠 신뢰도 평가"""
        # 길이 기반 기본 평가
        length = len(content)

        if length >= 1000:
            score = 70
        elif length >= 500:
            score = 50
        elif length >= 200:
            score = 30
        else:
            score = 10

        return ConfidenceResult(
            score=score,
            level=self._score_to_level(score),
            factors={"length": score},
            concerns=[] if score >= 50 else ["내용이 짧음"],
            needs_extra_verification=score < 50,
            recommendation="pass" if score >= 70 else "verify",
        )

    def get_summary(self, result: ConfidenceResult) -> str:
        """결과 요약 문자열 생성"""
        lines = [f"[V53.3 Confidence: {result.score}/100 ({result.level.value})]"]

        if result.concerns:
            lines.append("우려 사항:")
            for c in result.concerns[:3]:
                lines.append(f"  - {c}")

        lines.append(f"권장: {result.recommendation}")
        return "\n".join(lines)
