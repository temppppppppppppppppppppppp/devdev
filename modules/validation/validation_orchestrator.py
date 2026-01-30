"""
[V0128] ValidationOrchestrator
[V47] 5-Tier 검증 통합 실행 (CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY)
+ Self-Consistency + CatharsisTimer + ActionSceneEvaluator

[V47 업데이트]
- TIER 0.5: ContinuityValidator 추가 (에피소드 간 연속성 검증)
- 아이템 중복 획득, 무기 상태 리셋, 부상 연속성 검증
"""
from typing import Dict, List, Any, Optional
from .continuity_validator import ContinuityValidator
from .blocking_validator import BlockingValidator
from .consistency_validator import ConsistencyValidator
from .scoring_validator import ScoringValidator
from .advisory_validator import AdvisoryValidator
from .catharsis_timer import CatharsisTimer
from .action_scene_evaluator import ActionSceneEvaluator


# [V44] Constitution 캐시 (모듈 레벨에서 관리)
_CONSTITUTION_CACHE: Dict[str, str] = {}


class ValidationOrchestrator:
    """
    글도비 V47 통합 검증 오케스트레이터

    5-Tier 검증을 순차적으로 실행하고 최종 결과를 반환합니다.
    TIER 0.5: CONTINUITY → TIER 1: BLOCKING → TIER 1.5: CONSISTENCY → TIER 2: SCORING → TIER 3: ADVISORY
    Self-Consistency (다수결 투표) 적용 가능.
    """

    def __init__(self, config: dict, client=None, genre='wuxia', context=None):
        self.config = config
        self.client = client
        self.genre = genre
        self.context = context  # [Phase 5.2.2] Reflexion용 context

        # [V44] Constitution 로드 (캐싱 + 장르별 fallback 강화)
        self.constitution = self._load_constitution_cached(genre)

        # [V47] TIER 0.5: CONTINUITY (에피소드 간 연속성)
        self.continuity = ContinuityValidator(context=context)

        # TIER 1: BLOCKING
        self.blocking = BlockingValidator()

        # [V46] TIER 1.5: CONSISTENCY (새로 추가)
        self.consistency = ConsistencyValidator(genre=genre)

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

        # [Phase 3] 장기 일관성 검증 (선택적)
        self.use_retrospective = config.get('use_retrospective', False)
        self.retrospective = None  # Lazy initialization

        # [Phase 5.2.2] Reflexion 시스템 (선택적)
        self.use_reflexion = config.get('use_reflexion', True)  # 기본 활성화
        self.reflexion = None  # Lazy initialization

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
        # [V47] TIER 0.5: CONTINUITY (에피소드 간 연속성)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V47] TIER 0.5: CONTINUITY 검증 중...")
        continuity_result = self.continuity.validate(ep_num, manuscript, validation_context)
        results['continuity_result'] = continuity_result

        if not continuity_result['passed']:
            # 연속성 위반 시 즉시 REJECT
            print(f"      ❌ CONTINUITY 실패: {len(continuity_result['violations'])}개 위반")
            self._record_failure_to_reflexion(ep_num, 'continuity', continuity_result['violations'])

            return {
                "final_decision": "REJECT",
                "reason": "CONTINUITY 검증 실패 - 에피소드 간 연속성 위반",
                "violations": continuity_result['violations'],
                "continuity_result": continuity_result,
                "total_score": 0,
                "feedback": self._generate_continuity_feedback(continuity_result),
                "self_consistency_used": False
            }

        # 경고만 있는 경우 로그
        warning_count = continuity_result.get('warning_count', 0)
        if warning_count > 0:
            print(f"      ⚠️ CONTINUITY 경고: {warning_count}개 (계속 진행)")
        else:
            print(f"      ✅ CONTINUITY 통과")

        # ═══════════════════════════════════════════════════════════════
        # TIER 1: BLOCKING (필수 통과)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V0128] TIER 1: BLOCKING 검증 중...")
        blocking_result = self.blocking.validate(manuscript, validation_context)
        results['blocking_result'] = blocking_result

        if not blocking_result['passed']:
            # [Phase 5.2.2] Reflexion: 실패 패턴 기록
            self._record_failure_to_reflexion(ep_num, 'blocking', blocking_result['failures'])

            return {
                "final_decision": "REJECT",
                "reason": "BLOCKING 검증 실패",
                "failures": blocking_result['failures'],
                "blocking_result": blocking_result,
                "continuity_result": continuity_result,
                "total_score": 0,
                "feedback": self._generate_blocking_feedback(blocking_result),
                "self_consistency_used": False
            }

        print(f"      ✅ BLOCKING 통과 (0/{blocking_result.get('failure_count', 0)} 실패)")

        # ═══════════════════════════════════════════════════════════════
        # [V46] TIER 1.5: CONSISTENCY (일관성 검증)
        # ═══════════════════════════════════════════════════════════════
        print(f"      [V46] TIER 1.5: CONSISTENCY 검증 중...")
        consistency_result = self.consistency.validate(manuscript, validation_context)
        results['consistency_result'] = consistency_result

        # 정당화 불가 위반이 있으면 즉시 REJECT
        unjustifiable = consistency_result.get('unjustifiable_violations', [])
        if unjustifiable:
            print(f"      ❌ CONSISTENCY 실패: {len(unjustifiable)}개 정당화 불가 위반")
            return {
                "final_decision": "REJECT",
                "reason": "CONSISTENCY 검증 실패 - 정당화 불가 모순",
                "violations": unjustifiable,
                "consistency_result": consistency_result,
                "blocking_result": blocking_result,
                "total_score": 0,
                "feedback": consistency_result.get('feedback', ''),
                "detailed_feedback": consistency_result.get('feedback', ''),
                "self_consistency_used": False
            }

        # 정당화 가능 위반은 점수 감점으로 처리
        consistency_penalty = consistency_result.get('score_penalty', 0)
        justifiable_count = len(consistency_result.get('justifiable_violations', []))

        if justifiable_count > 0:
            print(f"      ⚠️ CONSISTENCY 경고: {justifiable_count}개 (감점: {consistency_penalty}점)")
        else:
            print(f"      ✅ CONSISTENCY 통과")

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
        # [Phase 5.2.3] TIER 2.5: CONDITIONAL SELF-REFINE (조건부 품질 정제)
        # ═══════════════════════════════════════════════════════════════
        # ⚠️ 설계 노트: ValidationOrchestrator는 검증만 담당.
        #    실제 Self-Refine 실행은 상위 레벨(main_a.py Stage 4)에서 처리.
        #    여기서는 조건만 판단하고 플래그 반환.
        refine_applied = False
        refine_reason = ""

        # 조건 1: 아쉬운 점수 (88-90점)
        if 88 <= total_score <= 90:
            refine_applied = True
            refine_reason = f"아쉬운 점수 ({total_score}점)"

        # 조건 2: 중요 화 (1, 25, 50, 75, 100, ...)
        important_episodes = [1] + [i for i in range(25, 251, 25)]  # 1, 25, 50, 75, ...
        if ep_num in important_episodes:
            refine_applied = True
            refine_reason = f"중요 화 (제{ep_num}화)" if not refine_reason else refine_reason + " + 중요 화"

        if refine_applied:
            print(f"      ✨ [Self-Refine] 품질 정제 권장 ({refine_reason})")
            results['refine_recommended'] = True
            results['refine_reason'] = refine_reason
            # TODO: 상위 레벨에서 Writer._self_refine() 호출 필요
        else:
            results['refine_recommended'] = False

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

        # [V46] CONSISTENCY 감점 적용
        consistency_adjustment = consistency_penalty  # 이미 음수

        # 조정된 총점
        adjusted_total = total_score + catharsis_adjustment + action_adjustment + consistency_adjustment
        adjusted_total = max(0, min(100, adjusted_total))  # 0~100 범위 제한

        adjustments_made = (catharsis_adjustment != 0 or action_adjustment != 0 or consistency_adjustment != 0)
        if adjustments_made:
            adjustment_parts = []
            if consistency_adjustment != 0:
                adjustment_parts.append(f"일관성: {consistency_adjustment:+d}")
            if catharsis_adjustment != 0:
                adjustment_parts.append(f"카타르시스: {catharsis_adjustment:+d}")
            if action_adjustment != 0:
                adjustment_parts.append(f"액션: {action_adjustment:+d}")
            print(f"      📊 점수 조정: {total_score} → {adjusted_total} ({', '.join(adjustment_parts)})")
            total_score = adjusted_total

        # ═══════════════════════════════════════════════════════════════
        # [Phase 3] Retrospective Validator (장기 일관성 검증)
        # ═══════════════════════════════════════════════════════════════
        if self.use_retrospective and ep_num > 3:  # 3화 이상부터 활성화
            print(f"      [Phase 3] RETROSPECTIVE: 장기 일관성 검증 중...")

            # Lazy initialization
            if self.retrospective is None:
                from .retrospective_validator import RetrospectiveValidator
                # context는 validation_context에서 추출
                context_obj = validation_context.get('_context')
                if context_obj:
                    self.retrospective = RetrospectiveValidator(context_obj, lookback_episodes=5)

            if self.retrospective:
                retrospective_result = self.retrospective.validate_long_term_consistency(
                    current_ep=ep_num,
                    manuscript=manuscript,
                    validation_context=validation_context
                )
                results['retrospective_result'] = retrospective_result

                if not retrospective_result['passed']:
                    severity = retrospective_result.get('severity_level', 'NONE')
                    violation_count = retrospective_result.get('total_violations', 0)

                    print(f"      ⚠️ RETROSPECTIVE: {violation_count}개 장기 일관성 위반 ({severity})")

                    # CRITICAL 위반이 있으면 즉시 REJECT
                    if severity == "CRITICAL":
                        return {
                            "final_decision": "REJECT",
                            "reason": "장기 일관성 CRITICAL 위반",
                            "retrospective_result": retrospective_result,
                            "blocking_result": blocking_result,
                            "total_score": 0,
                            "feedback": retrospective_result.get('message', ''),
                            "detailed_feedback": self._format_retrospective_feedback(retrospective_result),
                            "self_consistency_used": False
                        }

                    # HIGH 이상이면 점수 감점
                    if severity in ["HIGH", "MEDIUM"]:
                        penalty = 10 if severity == "HIGH" else 5
                        total_score = max(0, total_score - penalty)
                        print(f"      📊 장기 일관성 감점: -{penalty}점 (새 총점: {total_score})")
                else:
                    print(f"      ✅ RETROSPECTIVE: 장기 일관성 통과")

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
        [Phase 5.1.2] Conditional Self-Consistency: 조건부 다수결 투표

        - 1차 평가 먼저 실행
        - 70-85점 구간 (애매한 점수): 3-vote 실행
        - 그 외 (명확한 점수): 1-vote로 종료

        목적: 비용 60% 절감, 품질 유지
        """
        # 1차 평가
        print(f"      🔄 Self-Consistency (Conditional): 1차 평가 중...")
        first_eval = self.scoring.validate(manuscript, context)
        first_score = first_eval['total_score']

        print(f"         Vote 1: {first_score}점, {first_eval['message']}")

        # 조건부 판단: 애매한 점수인가?
        ambiguous_lower = 70
        ambiguous_upper = 85

        if ambiguous_lower <= first_score <= ambiguous_upper:
            # 애매한 구간 → 추가 2회 평가
            print(f"      ⚖️ 애매한 점수({first_score}) → 추가 평가 활성화")

            evaluations = [first_eval]
            for i in range(1, self.consistency_votes):
                result = self.scoring.validate(manuscript, context)
                evaluations.append(result)
                print(f"         Vote {i+1}: {result['total_score']}점, {result['message']}")

            # 점수 중앙값
            import statistics
            scores = [e['total_score'] for e in evaluations]
            median_score = statistics.median(scores)

            # PASS/REJECT 다수결
            pass_votes = sum(1 for e in evaluations if e['passed'])
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
                'median_score': median_score,
                'conditional': True,
                'reason': f'ambiguous_score ({first_score})'
            }

            print(f"      ✅ Self-Consistency 완료: {median_score}점 (PASS {pass_votes}/{self.consistency_votes})")

        else:
            # 명확한 구간 → 1-vote로 종료
            print(f"      ✓ 명확한 점수({first_score}) → 1-vote로 종료 (비용 절감)")

            result = first_eval.copy()
            result['self_consistency'] = {
                'votes': 1,
                'pass_votes': 1 if first_eval['passed'] else 0,
                'scores': [first_score],
                'median_score': first_score,
                'conditional': True,
                'reason': f'clear_score ({first_score})',
                'cost_saved': True
            }

        return result

    def _generate_continuity_feedback(self, continuity_result: dict) -> str:
        """[V47] CONTINUITY 실패 시 피드백 생성"""
        violations = continuity_result.get('violations', [])
        warnings = continuity_result.get('warnings', [])

        feedback_parts = ["## CONTINUITY 검증 실패 (에피소드 간 연속성 위반)\n"]

        for violation in violations:
            vtype = violation.get('type', 'unknown')
            reason = violation.get('reason', '')
            severity = violation.get('severity', 'CRITICAL')
            fix = violation.get('fix_suggestion', '')

            feedback_parts.append(f"- [{severity}] {reason}")
            if fix:
                feedback_parts.append(f"  → 수정 방법: {fix}")

        if warnings:
            feedback_parts.append("\n### 추가 경고:")
            for warning in warnings[:3]:
                feedback_parts.append(f"- {warning.get('reason', '')}")

        feedback_parts.append("\n위 문제를 수정 후 재제출하십시오.")
        feedback_parts.append("직전 에피소드의 상태를 확인하고 연속성을 유지해주세요.")

        return "\n".join(feedback_parts)

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

    def _format_retrospective_feedback(self, retrospective_result: dict) -> str:
        """[Phase 3] Retrospective 검증 결과를 피드백 형식으로 변환"""
        feedback_parts = ["## 장기 일관성 위반\n"]

        violations = retrospective_result.get('violations', [])
        severity = retrospective_result.get('severity_level', 'NONE')

        feedback_parts.append(f"심각도: {severity}")
        feedback_parts.append(f"총 {len(violations)}개 위반 감지\n")

        for violation in violations:
            vtype = violation.get('type', 'unknown')
            reason = violation.get('reason', '')
            severity = violation.get('severity', 'LOW')

            feedback_parts.append(f"- [{severity}] {reason}")

            if 'required_fix' in violation:
                feedback_parts.append(f"  수정 방법: {violation['required_fix']}")

        return "\n".join(feedback_parts)

    def _record_failure_to_reflexion(self, ep_num: int, failure_type: str, failures: list):
        """
        [Phase 5.2.2] 실패 패턴을 Reflexion에 기록

        Args:
            ep_num: 에피소드 번호
            failure_type: 실패 유형
            failures: 실패 목록
        """
        if not self.use_reflexion:
            return

        try:
            # Lazy initialization
            if self.reflexion is None:
                from modules.core.reflexion_manager import ReflexionManager
                # context가 필요한데, ValidationOrchestrator에는 없을 수 있음
                # 이 경우 기록 스킵
                if not hasattr(self, 'context') or self.context is None:
                    return

                self.reflexion = ReflexionManager(self.context)

            # 각 실패 항목 기록
            for failure in failures:
                description = failure.get('reason', '알 수 없는 실패')
                solution = failure.get('required_fix', '')

                self.reflexion.record_failure(
                    ep_num=ep_num,
                    failure_type=failure_type,
                    description=description,
                    solution=solution
                )

        except Exception as e:
            # Reflexion 실패해도 검증은 계속 진행
            print(f"      ⚠️ [Reflexion] 실패 기록 실패: {e}")
