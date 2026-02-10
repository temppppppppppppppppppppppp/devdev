"""
[V64 P2-1] Director QualityAuditor — 품질 검증 전담 모듈

Director God Object 분해의 다섯 번째 단계.
장르 검증, 캐릭터 논리 검증, V0128 3-Tier 검증 시스템 담당.
"""

import json
from modules.validation.validation_orchestrator import ValidationOrchestrator


class DirectorQualityAuditor:
    """
    [V64 P2-1] Director에서 분리된 품질 검증 모듈

    담당:
    - _run_genre_specific_validation(): 장르별 특화 검증 (Python)
    - assess_character_logic(): 캐릭터 논리성 적대적 검증 (LLM)
    - _audit_with_v0128(): V0128 검증 시스템 내부 헬퍼
    - audit_manuscript_v0128(): V0128 3-Tier 검증 시스템 원고 검수
    """

    def __init__(self, director):
        """
        Args:
            director: Director 인스턴스 (BaseAgent 메서드 + 설정 접근용)
        """
        self._d = director

        # [V0128] Lazy initialization
        self.v0128_orchestrator = None

    def _run_genre_specific_validation(self, manuscript: str, ep_num: int) -> dict:
        """
        [V60.90] 장르별 특화 검증 실행

        Hunter: 던전 진입, 각성 단계, 스킬 쿨타임 등
        Investment: 투자 규모, 수익률, 타임라인 이벤트 등
        Wuxia: (base guard에서 처리)

        Returns:
            {
                'has_critical': bool,
                'violations': list,
                'summary': str,
                'feedback': str
            }
        """
        if not self._d.guard:
            return {'has_critical': False, 'violations': [], 'summary': '', 'feedback': ''}

        violations = []
        critical_found = False

        try:
            # ─────────────────────────────────────────────────────────────
            # Hunter 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            if self._d.genre == 'hunter':
                # 던전 진입 규칙 검증
                if hasattr(self._d.guard, 'validate_dungeon_entry'):
                    import re
                    dungeon_patterns = re.findall(r'(\w+)\s*(?:등급|랭크|급)\s*던전', manuscript)
                    for dungeon_rank in dungeon_patterns:
                        result = self._d.guard.validate_dungeon_entry(dungeon_rank, 'E')
                        if not result[0]:
                            violations.append({
                                'type': 'dungeon_entry',
                                'message': result[1],
                                'severity': 'warning'
                            })

                # 각성 단계 스킵 검증
                if hasattr(self._d.guard, 'validate_awakening_progression'):
                    awakening_patterns = re.findall(r'(\w)급.*?각성|각성.*?(\w)급', manuscript)
                    for match in awakening_patterns:
                        rank = match[0] or match[1]

                # 스킬 사용 검증
                if hasattr(self._d.guard, 'validate_skill_usage'):
                    pass

                print(f"      🎮 [V60.90] Hunter 특화 검증: {len(violations)}개 이슈")

            # ─────────────────────────────────────────────────────────────
            # Investment 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            elif self._d.genre == 'investment':
                import re

                # 투자 규모 검증
                if hasattr(self._d.guard, 'validate_investment_scale'):
                    amount_patterns = re.findall(r'(\d+(?:,\d{3})*)\s*(?:억|만|원)', manuscript)
                    for amount_str in amount_patterns:
                        amount = int(amount_str.replace(',', ''))
                        result = self._d.guard.validate_investment_scale(amount, 'small')
                        if not result[0]:
                            violations.append({
                                'type': 'investment_scale',
                                'message': result[1],
                                'severity': 'warning'
                            })

                # 수익률 검증
                if hasattr(self._d.guard, 'validate_return_rate'):
                    roi_patterns = re.findall(r'(\d+(?:\.\d+)?)\s*%', manuscript)
                    for roi_str in roi_patterns:
                        roi = float(roi_str)
                        if roi > 100:
                            result = self._d.guard.validate_return_rate(roi, 'stock', '1month')
                            if not result[0]:
                                violations.append({
                                    'type': 'return_rate',
                                    'message': result[1],
                                    'severity': 'warning'
                                })

                # 타임라인 이벤트 검증
                if hasattr(self._d.guard, 'validate_timeline_event'):
                    year_patterns = re.findall(r'(19\d{2}|20\d{2})년', manuscript)

                print(f"      💰 [V60.90] Investment 특화 검증: {len(violations)}개 이슈")

            # ─────────────────────────────────────────────────────────────
            # Wuxia 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            elif self._d.genre == 'wuxia':
                if hasattr(self._d.guard, 'check_modern_notation'):
                    modern_violations = self._d.guard.check_modern_notation(manuscript)
                    if modern_violations and isinstance(modern_violations, list):
                        examples = [v.get('match', '')[:20] for v in modern_violations[:3]]
                        violations.append({
                            'type': 'modern_notation',
                            'message': f"현대 표기 발견: {examples}",
                            'severity': 'warning'
                        })

                print(f"      ⚔️ [V60.90] Wuxia 특화 검증: {len(violations)}개 이슈")

            # ─────────────────────────────────────────────────────────────
            # Actor 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            elif self._d.genre == 'actor':
                if hasattr(self._d.guard, 'FORBIDDEN_TERMS'):
                    found_terms = [t for t in self._d.guard.FORBIDDEN_TERMS if t in manuscript]
                    if found_terms:
                        violations.append({
                            'type': 'forbidden_terms',
                            'message': f"장르 부적합 용어 발견: {found_terms[:5]}",
                            'severity': 'warning'
                        })

                print(f"      🎬 [V62] Actor 특화 검증: {len(violations)}개 이슈")

            # ─────────────────────────────────────────────────────────────
            # Sports 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            elif self._d.genre == 'sports':
                if hasattr(self._d.guard, 'FORBIDDEN_TERMS'):
                    found_terms = [t for t in self._d.guard.FORBIDDEN_TERMS if t in manuscript]
                    if found_terms:
                        violations.append({
                            'type': 'forbidden_terms',
                            'message': f"장르 부적합 용어 발견: {found_terms[:5]}",
                            'severity': 'warning'
                        })

                print(f"      🏆 [V62.1] Sports 특화 검증: {len(violations)}개 이슈")

            # ─────────────────────────────────────────────────────────────
            # Medical 장르 특화 검증
            # ─────────────────────────────────────────────────────────────
            elif self._d.genre == 'medical':
                if hasattr(self._d.guard, 'FORBIDDEN_TERMS'):
                    found_terms = [t for t in self._d.guard.FORBIDDEN_TERMS if t in manuscript]
                    if found_terms:
                        violations.append({
                            'type': 'forbidden_terms',
                            'message': f"장르 부적합 용어 발견: {found_terms[:5]}",
                            'severity': 'warning'
                        })

                print(f"      🏥 [V62.1] Medical 특화 검증: {len(violations)}개 이슈")

            # Critical 여부 판단 (3개 이상이면 critical)
            if len(violations) >= 3:
                critical_found = True

            # 결과 반환
            summary = "; ".join([v['message'][:50] for v in violations[:3]])
            feedback = "\n".join([f"- [{v['type']}] {v['message']}" for v in violations])

            return {
                'has_critical': critical_found,
                'violations': violations,
                'summary': summary,
                'feedback': feedback
            }

        except Exception as e:
            print(f"      ⚠️ [V60.90] 장르 검증 오류: {str(e)[:50]}")
            return {'has_critical': False, 'violations': [], 'summary': '', 'feedback': ''}

    def assess_character_logic(self, ep_num, manuscript, npc_profiles, character_traits):
        """
        [V41 Red Team] 캐릭터 논리성 적대적 검증

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            npc_profiles: 등장 NPC 프로필 (Master Bible에서 추출)
            character_traits: 캐릭터 특성 DB (성격, 지능, 무공 수준 등)

        Returns:
            dict: {decision, score, violations, severity, feedback}
        """
        safe_manuscript = self._d._escape_braces(manuscript[:6000])
        safe_npc = self._d._escape_braces(json.dumps(npc_profiles, ensure_ascii=False))
        safe_traits = self._d._escape_braces(json.dumps(character_traits, ensure_ascii=False))

        prompt = f"""
[Role] 레드팀 캐릭터 논리성 감사관 (Character Logic Auditor)
[Task] 원고 내 등장인물의 행동이 설정된 특성과 일치하는지 적대적으로 검증하라.

### 📋 검수 대상 데이터
- 현재 회차: 제 {ep_num}화
- 📝 원고 내용: {safe_manuscript}
- 👤 등장 NPC 프로필: {safe_npc}
- 🎭 캐릭터 특성 DB: {safe_traits}

### 🎯 적대적 검증 항목 (Red Team Criteria)
1. **지능적 캐릭터의 어리석은 결정**:
   - '교활한', '노회한', '간사한' 특성의 인물이 비합리적/어리석은 결정을 내리는가?
   - 예: 교활한 악당이 주인공을 함정에 빠뜨릴 수 있는 상황에서 정면대결을 선택

2. **강자의 급격한 약화**:
   - 설정상 강자가 설명 없이 쉽게 제압당하는가?
   - 예: 일류 고수가 삼류의 기습에 무력하게 당함

3. **성격 일관성 위반**:
   - 냉혹한 인물이 갑자기 자비를 베풀거나, 소심한 인물이 돌연 대담해지는가?
   - 성격 변화가 있다면 충분한 서사적 근거가 있는가?

4. **동기 불명 행동**:
   - 인물의 행동에 명확한 동기가 보이지 않는가?
   - 특히 주인공에게 유리한 방향으로 '우연히' 행동하는 조연

### [🚨 판정 기준]
- NPC 프로필이나 특성 DB가 비어있으면 자동 PASS (검증 불가)
- 경미한 위반(MINOR)은 경고만 하고 PASS
- 중대한 위반(MAJOR) 2개 이상 또는 치명적 위반(CRITICAL) 1개 이상 시 REJECT

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "violations": [
        {{
            "character": "캐릭터명",
            "trait": "설정된 특성",
            "action": "문제 행동",
            "reason": "위반 사유"
        }}
    ],
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "feedback": "수정 지침 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""
        # NPC 정보가 비어있으면 자동 PASS
        if not npc_profiles and not character_traits:
            return {
                "decision": "PASS",
                "score": 100,
                "violations": [],
                "severity": "NONE",
                "feedback": "NPC 프로필 없음 - 캐릭터 논리 검증 생략"
            }

        response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
        return self._d._extract_json_robust(response)

    def _audit_with_v0128(self, ep_num, manuscript, validation_context, target_len=4500):
        """
        [V43 내부 헬퍼] V0128 검증 시스템 사용 (장르 자동 전달)

        audit_manuscript에서 use_v0128=True일 때 호출됨
        """
        mode = "BLUEPRINT" if target_len <= 4000 else "MANUSCRIPT"
        validation_context['mode'] = mode

        return self.audit_manuscript_v0128(
            ep_num=ep_num,
            manuscript=manuscript,
            validation_context=validation_context,
            genre=self._d.genre
        )

    def audit_manuscript_v0128(self, ep_num, manuscript, validation_context, config=None, genre='wuxia'):
        """
        [V0128] 3-Tier 검증 시스템을 사용한 원고 검수

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            validation_context: {
                'encyclopedia': {...},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'BLUEPRINT' | 'MANUSCRIPT',
                'history': [...],
                'npc_profiles': {...}
            }
            config: 검증 설정 dict (선택적)
            genre: 장르 ('wuxia', 'hunter', 'investment')

        Returns:
            dict: {
                "final_decision": "PASS" | "CONDITIONAL_PASS" | "REJECT",
                "total_score": float,
                "blocking_result": {...},
                "scoring_result": {...},
                "advisory_result": {...},
                "feedback": str,
                "detailed_feedback": str,
                "self_consistency_used": bool
            }
        """
        # Lazy initialization of ValidationOrchestrator
        if self.v0128_orchestrator is None:
            default_config = {
                'scoring_model': self._d.primary_model,
                'advisory_model': 'gemini-2.0-flash',
                'scoring_threshold': 65,
                'use_self_consistency': True,
                'consistency_votes': 3
            }
            if config:
                default_config.update(config)

            self.v0128_orchestrator = ValidationOrchestrator(
                config=default_config,
                client=self._d.client,
                genre=genre
            )

        try:
            result = self.v0128_orchestrator.validate(
                ep_num=ep_num,
                manuscript=manuscript,
                validation_context=validation_context
            )

            legacy_result = {
                "decision": result['final_decision'],
                "score": result['total_score'],
                "reason": result['feedback'],
                "feedback": result['detailed_feedback'],
                "v0128_full_result": result
            }

            final_decision = result.get('final_decision', 'REJECT') if isinstance(result, dict) else 'REJECT'
            if final_decision in ['PASS', 'CONDITIONAL_PASS']:
                legacy_result['decision'] = 'PASS'
            else:
                legacy_result['decision'] = 'REJECT'

            return legacy_result

        except Exception as e:
            print(f"      🚨 [V0128 Error] 검증 중 예외 발생: {e}")
            return {
                "decision": "REJECT",
                "score": 0,
                "reason": f"V0128 검증 시스템 오류: {str(e)}",
                "feedback": "검증 시스템 오류 - 수동 검토 필요",
                "error": str(e)
            }
