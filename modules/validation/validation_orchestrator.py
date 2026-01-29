"""
[V0128] ValidationOrchestrator
3-Tier 검증 통합 실행 + Self-Consistency + CatharsisTimer + ActionSceneEvaluator
"""
from typing import Dict, List, Any, Optional
from .blocking_validator import BlockingValidator
from .scoring_validator import ScoringValidator
from .advisory_validator import AdvisoryValidator
from .catharsis_timer import CatharsisTimer
from .action_scene_evaluator import ActionSceneEvaluator


# [V44] Constitution 캐시 (모듈 레벨에서 관리)
_CONSTITUTION_CACHE: Dict[str, str] = {}


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

        # [V44] Constitution 로드 (캐싱 + 장르별 fallback 강화)
        self.constitution = self._load_constitution_cached(genre)

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

        # [V43] 추가 품질 평가 모듈
        catharsis_max_gap = config.get('catharsis_max_gap', 3)
        self.catharsis_timer = CatharsisTimer(max_frustration=catharsis_max_gap, genre=genre)
        self.action_evaluator = ActionSceneEvaluator(genre=genre)

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
        # [V43] 추가 품질 평가: CatharsisTimer + ActionSceneEvaluator
        # ═══════════════════════════════════════════════════════════════

        # CatharsisTimer - 카타르시스 타이밍 체크
        catharsis_history = validation_context.get('catharsis_history', [])
        catharsis_result = self.catharsis_timer.check_catharsis_timing(
            ep_num, manuscript, catharsis_history
        )
        results['catharsis_result'] = catharsis_result

        if catharsis_result.get('status') == 'warning':
            print(f"      ⚠️ CATHARSIS: {catharsis_result.get('message')}")
        elif catharsis_result.get('status') == 'critical':
            print(f"      🚨 CATHARSIS: {catharsis_result.get('message')}")
        else:
            print(f"      ✅ CATHARSIS: 적절한 타이밍")

        # ActionSceneEvaluator - 전투/액션 씬 평가
        action_context = {
            'technique_effects': validation_context.get('technique_effects', {}),
            'martial_hud': validation_context.get('martial_hud', {})
        }
        action_result = self.action_evaluator.evaluate(manuscript, action_context)
        results['action_result'] = action_result

        if action_result.get('action_scene_count', 0) > 0:
            print(f"      ⚔️ ACTION: {action_result['total_score']}/10점 ({action_result['action_scene_count']}개 씬)")

        # 추가 평가 결과를 총점에 반영 (보너스/감점)
        catharsis_adjustment = 0
        if catharsis_result.get('status') == 'critical':
            catharsis_adjustment = -5  # 심각한 카타르시스 부족 시 감점
        elif catharsis_result.get('status') == 'warning':
            catharsis_adjustment = -2

        action_adjustment = 0
        if action_result.get('action_scene_count', 0) > 0:
            action_score = action_result.get('total_score', 10)
            if action_score < 5:
                action_adjustment = -3  # 액션 씬 품질 낮음
            elif action_score >= 8:
                action_adjustment = 2  # 액션 씬 품질 우수

        # 조정된 총점
        adjusted_total = total_score + catharsis_adjustment + action_adjustment
        adjusted_total = max(0, min(100, adjusted_total))  # 0~100 범위 제한

        if catharsis_adjustment != 0 or action_adjustment != 0:
            print(f"      📊 점수 조정: {total_score} → {adjusted_total} (카타르시스: {catharsis_adjustment:+d}, 액션: {action_adjustment:+d})")
            total_score = adjusted_total

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

        # 점수 중앙값 - [V44 Fix] statistics.median 사용으로 정확한 계산
        import statistics
        scores = [e['total_score'] for e in evaluations]
        median_score = statistics.median(scores)

        # PASS/REJECT 다수결 - [V44 Fix] 과반수 계산 명확화
        pass_votes = sum(1 for e in evaluations if e['passed'])
        # 과반수: 3표 중 2표 이상, 5표 중 3표 이상 필요
        final_passed = pass_votes > (self.consistency_votes // 2)

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

    def _load_constitution_cached(self, genre: str) -> str:
        """
        [V44] Constitution 로드 (캐싱 + 장르별 fallback 강화)

        Args:
            genre: 장르 (wuxia, hunter, investment)

        Returns:
            str: Constitution 텍스트
        """
        global _CONSTITUTION_CACHE

        # 캐시 확인
        if genre in _CONSTITUTION_CACHE:
            return _CONSTITUTION_CACHE[genre]

        # Constitution 로드 시도
        try:
            from modules.core.quality_constitution import get_constitution_for_genre
            constitution = get_constitution_for_genre(genre)
            _CONSTITUTION_CACHE[genre] = constitution
            return constitution
        except Exception as e:
            print(f"[ERROR] Constitution 로드 실패 ({genre}): {e}")
            print(f"[WARNING] 기본 Constitution 사용 - 검증 품질 저하 가능")

            # [V44] 장르별 fallback Constitution
            fallback = self._get_fallback_constitution(genre)
            _CONSTITUTION_CACHE[genre] = fallback
            return fallback

    def _get_fallback_constitution(self, genre: str) -> str:
        """[V44] 장르별 Fallback Constitution 생성"""
        base = """
# 글도비 품질 헌법 (Fallback Mode)

## TIER 1: BLOCKING
### Article 1: 설정 일관성
1.1 사망한 NPC는 등장할 수 없다.
1.2 소유하지 않은 아이템은 사용할 수 없다.
1.3 파괴된 장소는 방문할 수 없다.
1.4 능력치 초과 기술 사용 불가.
1.5 최소 분량: MANUSCRIPT 4000자, BLUEPRINT 500자.

## TIER 2: SCORING (70점 이상 통과)
### Article 2: 캐릭터 일관성 [15점]
### Article 3: 문장 품질 [20점]
### Article 4: 감정선 [20점]
### Article 5: 대화 품질 [15점]
### Article 6: 상업성 [20점]
### Article 7: 패턴 다양성 [10점]

## TIER 3: ADVISORY
### Article 8: 클리셰 감지, 표현 개선, 복선 기회
"""

        # 장르별 Amendment 추가
        genre_amendments = {
            'wuxia': """
### Wuxia-Specific (Fallback)
- 무공 위계 준수 (후천 → 선천 → 절정 → 화경)
- 강호 예법 존중
- 내공 운용 묘사 권장
""",
            'hunter': """
### Hunter-Specific (Fallback)
- 게이트 등급 준수 (E-D-C-B-A-S)
- 미획득 스킬 사용 불가
- 각성 전 능력 사용 불가
""",
            'investment': """
### Investment-Specific (Fallback)
- 투자 수익률 현실성 (연 100% 이상은 근거 필요)
- 자금 출처 명확
- 정보 획득 경로 명시
"""
        }

        amendment = genre_amendments.get(genre, "")
        return base + amendment
