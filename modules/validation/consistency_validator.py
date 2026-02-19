"""
[V46] TIER 1.5: CONSISTENCY Validator
[V46.1] 권위 위임, 미해결 갈등(고구마), 빌런 반응 검증 추가
상태 vs 행동, 관계 역학, 직위/호칭, 설정 효능, 태도 전환 일관성 검증

핵심 원칙:
1. 하드코딩 금지 - 패턴/규칙은 GenreGuard + Bible에서 동적 로드
2. 정당화 허용 - 모순 감지 시 정당화 패턴도 함께 검색
3. 장르 확장성 - BaseGuard 인터페이스 기반 범용 검증
"""

import logging
import re


class ConsistencyValidator:
    """
    TIER 1.5: 일관성 검증 (BLOCKING과 SCORING 사이)

    감지 대상:
    1. 상태 vs 행동 - 현재 상태로 불가능한 행동 + 정당화 없음
    2. 관계 역학 - 관계 변화 이후 언행 불일치
    3. 직위/호칭 - 설정된 직위와 자칭/타칭 불일치
    4. 설정 효능 - 아이템/기술의 정의된 효능과 사용 불일치
    5. 태도 전환 - 태도 급변에 트리거 이벤트 없음
    [V46.1 추가]
    6. 권위 위임 - 상위자 생존 시 하위자가 상위 직위 자칭 (명분 필요)
    7. 미해결 갈등 - 적대 NPC가 응징 없이 동행 (고구마)
    8. 빌런 반응 - 주인공 대역전 후 빌런 무반응 (무능한 빌런)

    정당화 가능 모순 → SCORING 감점 + 피드백
    정당화 불가 모순 → REJECT
    """

    def __init__(self, guard=None, genre: str = "wuxia"):
        """
        Args:
            guard: GenreGuard 인스턴스 (WuxiaGuard, HunterGuard 등)
            genre: 장르 문자열 (guard 없을 때 동적 로드용)
        """
        self.guard = guard
        self.genre = genre

        # guard가 없으면 동적 로드 시도
        if self.guard is None:
            self.guard = self._load_guard_for_genre(genre)

    def _load_guard_for_genre(self, genre: str):
        """장르에 맞는 Guard 동적 로드"""
        try:
            if genre == "wuxia":
                from modules.core.genre_guards.wuxia_guard import WuxiaGuard

                return WuxiaGuard()
            elif genre == "hunter":
                from modules.core.genre_guards.hunter_guard import HunterGuard

                return HunterGuard()
            elif genre == "investment":
                # InvestmentGuard가 있으면 로드, 없으면 BaseGuard 사용
                try:
                    from modules.core.genre_guards.investment_guard import InvestmentGuard

                    return InvestmentGuard()
                except ImportError:
                    logging.warning("[WARNING] InvestmentGuard 없음 - 기본 검증만 수행")
                    return None
            else:
                logging.warning(f"[WARNING] 미지원 장르 '{genre}' - 기본 검증만 수행")
                return None
        except Exception as e:
            logging.warning(f"[WARNING] Guard 로드 실패 ({genre}): {e}")
            return None

    def validate(self, manuscript: str, validation_context: dict) -> dict:
        """
        CONSISTENCY 검증 실행

        Args:
            manuscript: 검증 대상 원고
            validation_context: {
                'martial_hud': {...},     # 주인공 상태 (actual_truth 포함)
                'karma_matrix': {...},    # NPC 관계 데이터
                'asset_library': {...},   # 아이템/기술 효능 데이터
                'npc_profiles': {...},    # NPC 프로필
                'prev_episode_events': [...],  # 직전 에피소드 주요 이벤트
            }

        Returns:
            {
                "tier": "CONSISTENCY",
                "passed": True/False,
                "violations": [...],
                "justifiable_violations": [...],  # 정당화 가능한 위반 (감점만)
                "unjustifiable_violations": [...],  # 정당화 불가 위반 (REJECT)
                "score_penalty": int,  # 0 ~ -20
                "feedback": str,
                "message": "..."
            }
        """
        violations = []
        justifiable = []
        unjustifiable = []

        # HUD 데이터 추출
        martial_hud = validation_context.get("martial_hud", {})
        actual_truth = {}
        if isinstance(martial_hud, dict):
            actual_truth = martial_hud.get("actual_truth", martial_hud)

        # ═══════════════════════════════════════════════════════════════
        # 1. 상태 vs 행동 일관성 (정당화 가능)
        # ═══════════════════════════════════════════════════════════════
        state_check = self._check_state_action_consistency(manuscript, actual_truth)
        if not state_check["passed"]:
            for v in state_check["violations"]:
                if v.get("has_justification", False):
                    justifiable.append({**v, "category": "state_action"})
                else:
                    unjustifiable.append({**v, "category": "state_action"})  # [V70] FIX: 정당화 불가 → unjustifiable
                violations.append({**v, "category": "state_action"})

        # ═══════════════════════════════════════════════════════════════
        # 2. 관계 역학 일관성 (정당화 가능 - 트리거 이벤트)
        # ═══════════════════════════════════════════════════════════════
        karma_matrix = validation_context.get("karma_matrix", {})
        relation_check = self._check_relation_dynamics(manuscript, karma_matrix, validation_context)
        if not relation_check["passed"]:
            for v in relation_check["violations"]:
                justifiable.append({**v, "category": "relation_dynamics"})
                violations.append({**v, "category": "relation_dynamics"})

        # ═══════════════════════════════════════════════════════════════
        # 3. 직위/호칭 일관성 (정당화 불가 - 명확한 오류)
        # ═══════════════════════════════════════════════════════════════
        character_rank = actual_truth.get("realm", actual_truth.get("rank", ""))
        hierarchy_check = self._check_hierarchy_consistency(manuscript, character_rank)
        if not hierarchy_check["passed"]:
            for v in hierarchy_check["violations"]:
                unjustifiable.append({**v, "category": "hierarchy"})
                violations.append({**v, "category": "hierarchy"})

        # ═══════════════════════════════════════════════════════════════
        # 4. 설정 효능 일관성 (정당화 가능 - 변환 설명)
        # ═══════════════════════════════════════════════════════════════
        asset_library = validation_context.get("asset_library", {})
        effect_check = self._check_effect_consistency(manuscript, asset_library)
        if not effect_check["passed"]:
            for v in effect_check["violations"]:
                if v.get("transformation_allowed", True):
                    justifiable.append({**v, "category": "effect"})
                else:
                    unjustifiable.append({**v, "category": "effect"})
                violations.append({**v, "category": "effect"})

        # ═══════════════════════════════════════════════════════════════
        # 5. 태도 전환 일관성 (정당화 가능 - 트리거 이벤트)
        # ═══════════════════════════════════════════════════════════════
        npc_profiles = validation_context.get("npc_profiles", {})
        prev_events = validation_context.get("prev_episode_events", [])
        attitude_check = self._check_attitude_transition(manuscript, npc_profiles, karma_matrix, prev_events)
        if not attitude_check["passed"]:
            for v in attitude_check["violations"]:
                justifiable.append({**v, "category": "attitude"})
                violations.append({**v, "category": "attitude"})

        # ═══════════════════════════════════════════════════════════════
        # [V46.1] 6. 권위 위임 일관성 (정당화 가능 - 명분 표현)
        # ═══════════════════════════════════════════════════════════════
        authority_context = validation_context.get("authority_context", {})
        if authority_context and self.guard:
            authority_check = self.guard.check_authority_delegation(manuscript, authority_context)
            if not authority_check["passed"]:
                for v in authority_check["violations"]:
                    if v.get("has_justification", False):
                        justifiable.append({**v, "category": "authority_delegation"})
                    else:
                        unjustifiable.append(
                            {**v, "category": "authority_delegation"}
                        )  # [V70] FIX: 정당화 불가 → unjustifiable
                    violations.append({**v, "category": "authority_delegation"})

        # ═══════════════════════════════════════════════════════════════
        # [V46.1] 7. 미해결 갈등 (고구마 감지) - 정당화 가능
        # ═══════════════════════════════════════════════════════════════
        ep_num = validation_context.get("ep_num", 1)
        if karma_matrix and self.guard:
            conflict_check = self.guard.check_unresolved_conflict(manuscript, karma_matrix, ep_num)
            if not conflict_check["passed"]:
                for v in conflict_check["violations"]:
                    justifiable.append({**v, "category": "unresolved_conflict"})
                    violations.append({**v, "category": "unresolved_conflict"})

                # 고구마 점수 기록
                goguma_score = conflict_check.get("goguma_score", 0)
                if goguma_score >= 5:
                    # 고구마 점수가 높으면 추가 경고
                    justifiable.append(
                        {
                            "reason": f"고구마 점수 {goguma_score}/10 - 독자 카타르시스 부족 위험",
                            "severity": "MEDIUM",
                            "category": "goguma_warning",
                        }
                    )

        # ═══════════════════════════════════════════════════════════════
        # [V46.1] 8. 빌런 반응 검증 - 정당화 가능
        # ═══════════════════════════════════════════════════════════════
        villain_context = validation_context.get("villain_context", {})
        recent_events = validation_context.get("recent_events", prev_events)
        if villain_context and self.guard:
            villain_check = self.guard.check_villain_response(manuscript, villain_context, recent_events)
            if not villain_check["passed"]:
                for v in villain_check["violations"]:
                    justifiable.append({**v, "category": "villain_response"})
                    violations.append({**v, "category": "villain_response"})

        # ═══════════════════════════════════════════════════════════════
        # 결과 집계
        # ═══════════════════════════════════════════════════════════════
        # 정당화 불가 위반이 있으면 REJECT
        has_unjustifiable = len(unjustifiable) > 0

        # 점수 감점 계산
        score_penalty = 0
        for v in justifiable:
            severity = v.get("severity", "MEDIUM")
            if severity == "HIGH":
                score_penalty -= 5
            elif severity == "MEDIUM":
                score_penalty -= 3
            else:
                score_penalty -= 1
        score_penalty = max(-20, score_penalty)

        # 피드백 생성
        feedback = self._generate_feedback(violations, justifiable, unjustifiable)

        # [FIX] passed와 message 일치시키기
        # unjustifiable이 있으면 REJECT, 없으면 PASS (justifiable 개수는 경고만)
        is_passed = len(unjustifiable) == 0

        return {
            "tier": "CONSISTENCY",
            "passed": is_passed,
            "violations": violations,
            "justifiable_violations": justifiable,
            "unjustifiable_violations": unjustifiable,
            "score_penalty": score_penalty,
            "feedback": feedback,
            "message": "REJECT - 정당화 불가능한 일관성 위반"
            if not is_passed
            else f"PASS (경고 {len(justifiable)}건)"
            if justifiable
            else "PASS",
        }

    # ========================================================================
    # 개별 검증 메서드
    # ========================================================================

    def _check_state_action_consistency(self, manuscript: str, current_state: dict) -> dict:
        """
        상태 vs 행동 일관성 검증

        Guard의 get_impossible_actions() + get_justification_patterns() 활용
        """
        if not self.guard:
            return {"passed": True, "violations": []}

        # Guard의 범용 메서드 사용
        return self.guard.check_state_action_consistency(manuscript, current_state)

    def _check_relation_dynamics(self, manuscript: str, karma_matrix: dict, context: dict) -> dict:
        """
        관계 역학 일관성 검증

        KarmaMatrix의 관계 변화 이후 언행 불일치 감지
        트리거 이벤트가 있으면 정당화
        """
        violations = []

        if not karma_matrix or not isinstance(karma_matrix, dict):
            return {"passed": True, "violations": []}

        # 각 NPC별 관계 검증
        for npc_name, npc_data in karma_matrix.items():
            if not isinstance(npc_data, dict):
                continue

            relation_type = npc_data.get("relation_type", "")
            events = npc_data.get("events", [])

            # 최근 관계 변화 확인
            if events and len(events) > 0:
                recent_event = events[-1] if isinstance(events[-1], dict) else {}
                event_type = recent_event.get("type", "")

                # 배신 후 충성, 적대 후 우호 등 급격한 변화 감지
                contradiction_patterns = self._get_relation_contradiction_patterns(npc_name, relation_type, event_type)

                for pattern_info in contradiction_patterns:
                    pattern = pattern_info.get("pattern", "")
                    if pattern and re.search(pattern, manuscript):
                        # 트리거 이벤트 존재 여부 확인
                        has_trigger = self._has_trigger_event(manuscript, npc_name, event_type)

                        violations.append(
                            {
                                "npc": npc_name,
                                "relation": relation_type,
                                "pattern": pattern,
                                "reason": pattern_info.get("reason", "관계 모순"),
                                "has_justification": has_trigger,
                                "severity": "MEDIUM",
                            }
                        )

        return {"passed": len(violations) == 0, "violations": violations}

    def _check_hierarchy_consistency(self, manuscript: str, character_rank: str) -> dict:
        """
        직위/호칭 일관성 검증

        Guard의 get_hierarchy_rules() 활용
        정당화 불가 (명확한 오류)
        """
        if not self.guard:
            return {"passed": True, "violations": []}

        return self.guard.check_hierarchy_consistency(manuscript, character_rank)

    def _check_effect_consistency(self, manuscript: str, asset_library: dict) -> dict:
        """
        설정 효능 일관성 검증

        아이템/기술의 정의된 효능과 실제 사용 불일치 감지
        """
        violations = []

        if not asset_library or not isinstance(asset_library, dict):
            # Guard의 기본 효능 규칙 사용
            if self.guard and hasattr(self.guard, "get_technique_effect_rules"):
                asset_library = self.guard.get_technique_effect_rules()
                if not asset_library or not isinstance(asset_library, dict):
                    return {"passed": True, "violations": []}
            else:
                return {"passed": True, "violations": []}

        for item_name, item_data in asset_library.items():
            if not isinstance(item_data, dict):
                continue

            # 아이템/기술이 원고에 등장하는지 확인
            if item_name not in manuscript:
                continue

            cannot_be_used_for = item_data.get("cannot_be_used_for") or []
            transformation_allowed = item_data.get("transformation_allowed", True)

            # 금지된 용도로 사용되었는지 확인
            for forbidden_use in cannot_be_used_for:
                # 용도 패턴 생성 (예: "독약.*치료" → 독약으로 치료)
                item_name_esc = re.escape(item_name)
                forbidden_use_esc = re.escape(forbidden_use)
                use_pattern = f"{item_name_esc}.*{forbidden_use_esc}|{forbidden_use_esc}.*{item_name_esc}"

                if re.search(use_pattern, manuscript, re.IGNORECASE):
                    # 변환 설명이 있는지 확인
                    transformation_patterns = [
                        r"특수한 방법",
                        r"반대.*효과",
                        r"역이용",
                        r"변형.*사용",
                        r"응용.*방식",
                    ]

                    has_transformation = any(re.search(tp, manuscript) for tp in transformation_patterns)

                    if not has_transformation:
                        violations.append(
                            {
                                "item": item_name,
                                "forbidden_use": forbidden_use,
                                "reason": f"'{item_name}'은(는) '{forbidden_use}' 용도로 사용 불가",
                                "transformation_allowed": transformation_allowed,
                                "severity": "HIGH" if not transformation_allowed else "MEDIUM",
                            }
                        )

        return {"passed": len(violations) == 0, "violations": violations}

    def _check_attitude_transition(
        self, manuscript: str, npc_profiles: dict, karma_matrix: dict, prev_events: list
    ) -> dict:
        """
        태도 전환 일관성 검증

        NPC의 태도 급변에 트리거 이벤트가 있는지 확인
        """
        violations = []

        if not npc_profiles or not isinstance(npc_profiles, dict):
            return {"passed": True, "violations": []}

        # 태도 급변 패턴
        sudden_attitude_patterns = [
            # 적대 → 우호
            (r"적.*갑자기.*미소|원수.*친절|증오.*사랑", "enemy_to_friend"),
            # 충성 → 배신
            (r"충성.*배신|믿음.*배반|은혜.*원수", "loyal_to_betrayal"),
            # 소심 → 대담
            (r"소심.*용감|겁쟁이.*영웅|비겁.*당당", "coward_to_brave"),
            # 냉혹 → 자비
            (r"냉혹.*자비|잔인.*온정|무정.*따뜻", "cold_to_merciful"),
        ]

        # 트리거 이벤트 패턴
        trigger_patterns = [
            r"깨달",
            r"눈물",
            r"충격",
            r"회상",
            r"진심.*느끼",
            r"마음.*변화",
            r"결심",
            r"사건.*이후",
            r"그날.*이후",
        ]

        for pattern, attitude_type in sudden_attitude_patterns:
            if re.search(pattern, manuscript):
                # 트리거 이벤트 존재 여부 확인
                has_trigger = any(re.search(tp, manuscript) for tp in trigger_patterns)

                # 직전 에피소드에 관련 이벤트가 있는지 확인
                has_prev_event = False
                if prev_events and isinstance(prev_events, list):
                    for event in prev_events:
                        if isinstance(event, dict):
                            event_type = event.get("type", "")
                            if attitude_type in str(event_type):
                                has_prev_event = True
                                break

                if not has_trigger and not has_prev_event:
                    violations.append(
                        {
                            "attitude_type": attitude_type,
                            "pattern": pattern,
                            "reason": f"태도 급변({attitude_type})에 트리거 이벤트 없음",
                            "has_justification": False,
                            "severity": "MEDIUM",
                        }
                    )

        return {"passed": len(violations) == 0, "violations": violations}

    # ========================================================================
    # 헬퍼 메서드
    # ========================================================================

    def _get_relation_contradiction_patterns(self, npc_name: str, relation_type: str, event_type: str) -> list[dict]:
        """관계 유형별 모순 패턴 생성"""
        patterns = []
        npc_name_esc = re.escape(npc_name)

        # 배신 후 충성 표현
        if event_type in ["betrayal", "배신"]:
            patterns.append(
                {
                    "pattern": f"{npc_name_esc}.*충성|{npc_name_esc}.*믿음|{npc_name_esc}.*은혜",
                    "reason": f"'{npc_name}'이(가) 배신한 후 충성/신뢰 표현 모순",
                }
            )

        # 적대 관계에서 우호 표현
        if relation_type in ["enemy", "적대", "원수"]:
            patterns.append(
                {
                    "pattern": f"{npc_name_esc}.*친구|{npc_name_esc}.*동지|{npc_name_esc}.*믿",
                    "reason": f"적대 관계인 '{npc_name}'에게 우호적 표현 모순",
                }
            )

        # 복종 관계에서 명령 표현
        if relation_type in ["subordinate", "하수인", "부하"]:
            patterns.append(
                {
                    "pattern": f"{npc_name_esc}.*에게.*명령받|{npc_name_esc}.*지시.*따라",
                    "reason": f"하위자 '{npc_name}'이(가) 주인공에게 명령하는 모순",
                }
            )

        return patterns

    def _has_trigger_event(self, manuscript: str, npc_name: str, event_type: str) -> bool:
        """트리거 이벤트 존재 여부 확인"""
        npc_name_esc = re.escape(npc_name)
        trigger_patterns = [
            f"{npc_name_esc}.*용서",
            f"{npc_name_esc}.*화해",
            f"{npc_name_esc}.*진심",
            f"{npc_name_esc}.*사과",
            f"{npc_name_esc}.*변화",
            r"마음.*바뀌",
            r"생각.*달라",
            r"오해.*풀",
        ]

        return any(re.search(tp, manuscript) for tp in trigger_patterns)

    def _generate_feedback(self, violations: list, justifiable: list, unjustifiable: list) -> str:
        """피드백 메시지 생성"""
        feedback_parts = []

        # 카테고리별 한글 이름
        category_names = {
            "state_action": "상태-행동 모순",
            "relation_dynamics": "관계 역학",
            "hierarchy": "직위/호칭",
            "effect": "효능 불일치",
            "attitude": "태도 전환",
            "authority_delegation": "권위 위임",
            "unresolved_conflict": "미해결 갈등(고구마)",
            "villain_response": "빌런 반응",
            "goguma_warning": "카타르시스 경고",
        }

        if unjustifiable:
            feedback_parts.append("## [REJECT] 정당화 불가 위반 (수정 필수)")
            for v in unjustifiable:
                category = v.get("category", "unknown")
                category_kr = category_names.get(category, category)
                reason = v.get("reason", "")
                feedback_parts.append(f"- [{category_kr}] {reason}")

        if justifiable:
            feedback_parts.append("\n## [WARNING] 일관성 경고 (정당화 권장)")
            for v in justifiable:
                category = v.get("category", "unknown")
                category_kr = category_names.get(category, category)
                reason = v.get("reason", "")
                suggestion = v.get("suggestion", "")
                feedback_parts.append(f"- [{category_kr}] {reason}")
                if suggestion:
                    feedback_parts.append(f"  -> {suggestion}")

            # 카테고리별 정당화 방법 안내
            categories_found = set(v.get("category", "") for v in justifiable)

            if "authority_delegation" in categories_found and self.guard:
                delegation_patterns = self.guard.get_delegation_patterns()
                if delegation_patterns:
                    feedback_parts.append("\n**권위 위임 정당화 방법:**")
                    for p in delegation_patterns[:3]:
                        readable = p.replace(r".*", "...").replace(r"\s+", " ")
                        feedback_parts.append(f'  - "{readable}"')

            if "unresolved_conflict" in categories_found and self.guard:
                resolution_patterns = self.guard.get_resolution_patterns()
                if resolution_patterns:
                    feedback_parts.append("\n**갈등 해소 방법:**")
                    for p in resolution_patterns[:3]:
                        readable = p.replace(r".*", "...").replace(r"\s+", " ")
                        feedback_parts.append(f'  - "{readable}"')

            if "villain_response" in categories_found and self.guard:
                response_patterns = self.guard.get_villain_response_patterns()
                if response_patterns:
                    feedback_parts.append("\n**빌런 대응 예시:**")
                    for p in response_patterns[:3]:
                        readable = p.replace(r".*", "...").replace(r"\s+", " ")
                        feedback_parts.append(f'  - "{readable}"')

            if "state_action" in categories_found and self.guard:
                patterns = self.guard.get_justification_patterns()
                if patterns:
                    feedback_parts.append("\n**상태-행동 정당화 방법:**")
                    for p in patterns[:3]:
                        readable = p.replace(r".*", "...").replace(r"\s+", " ")
                        feedback_parts.append(f'  - "{readable}"')

        if not feedback_parts:
            feedback_parts.append("[PASS] 일관성 검증 통과")

        return "\n".join(feedback_parts)


# ============================================================================
# 외부 인터페이스 함수
# ============================================================================


def create_consistency_validator(guard=None, genre: str = "wuxia") -> ConsistencyValidator:
    """ConsistencyValidator 팩토리 함수"""
    return ConsistencyValidator(guard=guard, genre=genre)
