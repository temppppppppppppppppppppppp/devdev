"""
[V0128] ValidationOrchestrator
3-Tier 검증 통합 실행 + Self-Consistency
"""
from typing import Dict, List, Any
from .blocking_validator import BlockingValidator
from .scoring_validator import ScoringValidator
from .advisory_validator import AdvisoryValidator


class ValidationOrchestrator:
    """
    글도비 V0128 통합 검증 오케스트레이터

    3-Tier 검증을 순차적으로 실행하고 최종 결과를 반환합니다.
    Self-Consistency (다수결 투표) 적용 가능.
    """

    def __init__(self, config: dict, client=None, genre='wuxia'):
        self.config = config
        self.client = client
        self.genre = genre

        # Constitution 로드 (에러 처리 강화)
        try:
            from modules.core.quality_constitution import get_constitution_for_genre
            self.constitution = get_constitution_for_genre(genre)
        except Exception as e:
            print(f"[ERROR] Constitution 로드 실패 ({genre}): {e}")
            print(f"[WARNING] 기본 Constitution 사용 - 검증 품질 저하 가능")
            # 기본 Constitution (최소한의 규칙)
            self.constitution = """
# 글도비 품질 헌법 (Fallback)

## Article 1: 최소 분량
- 원고는 최소 4000자 이상이어야 합니다.

## Article 2: 설정 일관성
- 등장인물의 행동은 설정과 일치해야 합니다.

## Article 3-8: (Constitution 파일 로드 실패 - 간소화 규칙 사용)
"""

        # TIER 1: BLOCKING
        self.blocking = BlockingValidator()

        # TIER 2: SCORING
        scoring_model = config.get('scoring_model', 'gemini-2.5-pro')
        self.scoring = ScoringValidator(
            client=client,
            model=scoring_model,
            constitution=self.constitution
        )
        self.scoring.PASS_THRESHOLD = config.get('scoring_threshold', 70)

        # TIER 3: ADVISORY
        advisory_model = config.get('advisory_model', 'gemini-2.5-flash')
        self.advisory = AdvisoryValidator(
            client=client,
            model=advisory_model
        )

        # Self-Consistency 설정
        self.use_self_consistency = config.get('use_self_consistency', True)
        self.consistency_votes = config.get('consistency_votes', 3)

    def validate(self, ep_num: int, manuscript: str, validation_context: dict) -> dict:
        """
        전체 검증 실행

        Args:
            ep_num: 에피소드 번호
            manuscript: 검증 대상 원고
            validation_context: {
                'encyclopedia': {...},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'BLUEPRINT' | 'MANUSCRIPT',
                'history': [...],
                'npc_profiles': {...}
            }

        Returns:
            {
                "final_decision": "PASS" | "CONDITIONAL_PASS" | "REJECT",
                "blocking_result": {...},
                "scoring_result": {...},
                "advisory_result": {...},
                "total_score": float,
                "feedback": str,
                "self_consistency_used": bool
            }
        """
        results = {}

        # ═══════════════════════════════════════════════════════════════
        # TIER 1: BLOCKING (필수 통과)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V0128] TIER 1: BLOCKING 검증 중...")
        blocking_result = self.blocking.validate(manuscript, validation_context)
        results['blocking_result'] = blocking_result

        if not blocking_result['passed']:
            return {
                "final_decision": "REJECT",
                "reason": "BLOCKING 검증 실패",
                "failures": blocking_result['failures'],
                "blocking_result": blocking_result,
                "total_score": 0,
                "feedback": self._generate_blocking_feedback(blocking_result),
                "self_consistency_used": False
            }

        print(f"      ✅ BLOCKING 통과 (0/{blocking_result.get('failure_count', 0)} 실패)")

        # ═══════════════════════════════════════════════════════════════
        # TIER 2: SCORING (점수 기반)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V0128] TIER 2: SCORING 평가 중...")

        if self.use_self_consistency and self.client:
            # Self-Consistency: 다수결 투표
            scoring_result = self._evaluate_with_self_consistency(
                manuscript, validation_context
            )
            results['self_consistency_used'] = True
        else:
            # 단일 평가
            scoring_result = self.scoring.validate(manuscript, validation_context)
            results['self_consistency_used'] = False

        results['scoring_result'] = scoring_result

        total_score = scoring_result['total_score']
        print(f"      📊 SCORING: {total_score}/100점 (임계값: {self.scoring.PASS_THRESHOLD})")

        # ═══════════════════════════════════════════════════════════════
        # TIER 3: ADVISORY (권고)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V0128] TIER 3: ADVISORY 생성 중...")
        advisory_result = self.advisory.validate(manuscript, validation_context)
        results['advisory_result'] = advisory_result

        print(f"      💡 ADVISORY: {len(advisory_result.get('suggestions', []))}개 제안")

        # ═══════════════════════════════════════════════════════════════
        # 최종 판정
        # ═══════════════════════════════════════════════════════════════
        results['total_score'] = total_score

        if total_score >= 85:
            final_decision = "PASS"
            feedback = f"우수한 품질 ({total_score}점)"
        elif total_score >= self.scoring.PASS_THRESHOLD:
            final_decision = "CONDITIONAL_PASS"
            feedback = f"통과 ({total_score}점) - 개선 권장사항 확인"
        else:
            final_decision = "REJECT"
            feedback = f"품질 미달 ({total_score}점) - 재작성 필요"

        results['final_decision'] = final_decision
        results['feedback'] = feedback

        # 상세 피드백 생성
        results['detailed_feedback'] = self._generate_detailed_feedback(results)

        return results

    def _evaluate_with_self_consistency(self, manuscript: str, context: dict) -> dict:
        """
        Self-Consistency: 다수결 투표로 평가 안정성 향상

        3회 평가 후 점수 중앙값 사용, PASS/REJECT 다수결
        """
        print(f"      🔄 Self-Consistency: {self.consistency_votes}회 평가 중...")

        evaluations = []
        for i in range(self.consistency_votes):
            result = self.scoring.validate(manuscript, context)
            evaluations.append(result)
            print(f"         Vote {i+1}: {result['total_score']}점, {result['message']}")

        # 점수 중앙값
        scores = [e['total_score'] for e in evaluations]
        median_score = sorted(scores)[len(scores) // 2]

        # PASS/REJECT 다수결
        pass_votes = sum(1 for e in evaluations if e['passed'])
        final_passed = pass_votes >= (self.consistency_votes / 2)

        # 대표 결과 (중앙값에 가장 가까운 것)
        representative = min(evaluations, key=lambda e: abs(e['total_score'] - median_score))

        # 결과 병합
        result = representative.copy()
        result['total_score'] = median_score
        result['passed'] = final_passed
        result['self_consistency'] = {
            'votes': self.consistency_votes,
            'pass_votes': pass_votes,
            'scores': scores,
            'median_score': median_score
        }

        print(f"      ✅ Self-Consistency 완료: {median_score}점 (PASS {pass_votes}/{self.consistency_votes})")

        return result

    def _generate_blocking_feedback(self, blocking_result: dict) -> str:
        """BLOCKING 실패 시 피드백 생성"""
        failures = blocking_result.get('failures', [])

        feedback_parts = ["## BLOCKING 검증 실패\n"]

        for failure in failures:
            check = failure.get('check', 'unknown')
            reason = failure.get('reason', '')
            severity = failure.get('severity', 'UNKNOWN')

            feedback_parts.append(f"- [{severity}] {reason}")

        feedback_parts.append("\n위 문제를 수정 후 재제출하십시오.")

        return "\n".join(feedback_parts)

    def _generate_detailed_feedback(self, results: dict) -> str:
        """상세 피드백 생성"""
        feedback_parts = []

        # 점수 요약
        total_score = results.get('total_score', 0)
        feedback_parts.append(f"## 총점: {total_score}/100")

        # SCORING 세부 점수
        scoring_result = results.get('scoring_result', {})
        breakdown = scoring_result.get('breakdown', {})

        if breakdown:
            feedback_parts.append("\n### 세부 점수")
            for category, data in breakdown.items():
                if isinstance(data, dict):
                    score = data.get('score', 0)
                    max_score = data.get('max', 0)
                    reason = data.get('reason', '')
                    feedback_parts.append(f"- {category}: {score}/{max_score}점 - {reason}")

        # 강점
        strengths = self._identify_strengths(breakdown)
        if strengths:
            feedback_parts.append("\n### 강점")
            for s in strengths:
                feedback_parts.append(f"- {s}")

        # 개선 필요
        weaknesses = self._identify_weaknesses(breakdown)
        if weaknesses:
            feedback_parts.append("\n### 개선 필요")
            for w in weaknesses:
                feedback_parts.append(f"- {w}")

        # ADVISORY 제안
        advisory_result = results.get('advisory_result', {})
        suggestions = advisory_result.get('suggestions', [])
        if suggestions:
            feedback_parts.append("\n### 추가 제안 (ADVISORY)")
            for s in suggestions[:3]:
                suggestion_text = s.get('suggestion', '')
                feedback_parts.append(f"- {suggestion_text}")

        return "\n".join(feedback_parts)

    def _identify_strengths(self, breakdown: dict) -> List[str]:
        """강점 식별 (높은 점수 항목)"""
        strengths = []

        for category, data in breakdown.items():
            if isinstance(data, dict):
                score = data.get('score', 0)
                max_score = data.get('max', 1)
                percentage = (score / max_score) * 100 if max_score > 0 else 0

                if percentage >= 80:
                    reason = data.get('reason', category)
                    strengths.append(f"{category}: {reason}")

        return strengths

    def _identify_weaknesses(self, breakdown: dict) -> List[str]:
        """약점 식별 (낮은 점수 항목)"""
        weaknesses = []

        for category, data in breakdown.items():
            if isinstance(data, dict):
                score = data.get('score', 0)
                max_score = data.get('max', 1)
                percentage = (score / max_score) * 100 if max_score > 0 else 0

                if percentage < 60:
                    reason = data.get('reason', category)
                    weaknesses.append(f"{category}: {reason}")

        return weaknesses
