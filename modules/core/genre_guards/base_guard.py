"""
[V40 Multi-Genre] 장르별 Guard의 공통 기능을 제공하는 추상 클래스
[V46] 일관성 검증 인터페이스 추가 - 상태 vs 행동, 정당화 패턴, 위계 규칙
[V46.1] 권위 위임, 미해결 갈등, 빌런 반응 검증 인터페이스 추가
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseGuard(ABC):
    """장르 독립적 Guard 추상 인터페이스"""

    def __init__(self):
        self.FORBIDDEN_TERMS = []
        self.ALLOWED_TERMS = []
        self.MANDATORY_CONCEPTS = []

        # [V46] 일관성 검증용 기본 데이터
        self._impossible_action_rules = []
        self._justification_patterns = []
        self._hierarchy_rules = {}
    
    @abstractmethod
    def get_genre_name(self):
        """장르 이름 반환"""
        pass
    
    def convert_to_numeric(self, text, current_value: float = None):
        """
        [V60.22] 한글/한자 수사를 숫자로 변환 + 델타값 처리

        Args:
            text: 변환할 텍스트 (예: "80%", "+50", "현상 유지", "무공 100%")
            current_value: 현재 값 (델타 계산용, None이면 절대값으로 처리)

        Returns:
            float: 변환된 숫자값
        """
        if not text or not isinstance(text, (str, int, float)):
            # [V60.22] None이면 현재 값 유지
            return current_value if current_value is not None else 0.0
        if isinstance(text, (int, float)): return float(text)

        clean_text = str(text).replace(" ", "").strip()

        # [V60.22] "현상 유지" 처리 - 현재 값 반환
        if clean_text in ["현상유지", "유지", "변화없음", "동일"]:
            return current_value if current_value is not None else 0.0

        # [V60.22] 델타값 처리 ("+50", "-20" 등)
        delta_match = re.match(r'^([+-])(\d+(?:\.\d+)?)%?$', clean_text)
        if delta_match and current_value is not None:
            sign = 1 if delta_match.group(1) == '+' else -1
            delta = float(delta_match.group(2))
            return max(0, min(100, current_value + sign * delta))

        # 1. [V60.22 Fix] 제로 가드 - "무" 단독일 때만 0 처리
        # "무공", "무형", "무림" 등은 0이 아님!
        zero_exact = ["영", "없음", "소멸", "고갈", "전무"]
        if clean_text in zero_exact:
            return 0.0
        # "무"는 단독으로 쓰일 때만 0 (예: "내공: 무")
        if clean_text == "무":
            return 0.0
        # 정확히 "0" 또는 "0.0"인 경우만 체크 (아라비아 숫자 추출 전에)
        if clean_text in ["0", "0.0", "0.", ".0", "0%"]:
            return 0.0

        # 2. 단위 멀티플라이어 (갑자 대응)
        unit_multiplier = 1.0
        if "갑자" in clean_text:
            unit_multiplier = 60.0
        
        # 3. 아라비아 숫자 우선 처리
        digit_match = re.search(r'([0-9\.]+)', clean_text)
        if digit_match:
            try:
                val = float(digit_match.group(1)) * unit_multiplier
                if '반' in clean_text: val += (30.0 if "갑자" in clean_text else 0.5)
                return val
            except (ValueError, TypeError): pass

        # 4. 한글 수사 정밀 파싱
        num_map = {'일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}
        total = 0.0
        
        if '십' in clean_text:
            idx = clean_text.find('십')
            prefix = clean_text[idx-1] if idx > 0 else None
            total += (num_map.get(prefix, 1) * 10)
            if idx + 1 < len(clean_text):
                suffix = clean_text[idx+1]
                total += num_map.get(suffix, 0)
        else:
            for char, val in num_map.items():
                if char in clean_text:
                    total = float(val)
                    break

        # 5. '반' 처리
        if '반' in clean_text:
            total += 0.5

        # 6. 최종 산출
        final_val = (total if total > 0 else 1.0) * unit_multiplier
        return float(final_val)
    
    def validate_v20_manuscript(self, content):
        """원고 검증 (장르별 커스터마이징 가능)"""
        issues = []
        
        # 1. 괄호 검출 (한자 예외 처리)
        parentheses_matches = re.findall(r'\((.*?)\)', content)
        for inside in parentheses_matches:
            if re.search(r'[^\u4e00-\u9fff]', inside):
                issues.append(f"장르 부적격 괄호 설명 발견: ({inside})")

        # 2. 알파벳(영어) 노출 절대 금지 (장르에 따라 완화 가능)
        if self._should_check_english():
            if re.search(r'[a-zA-Z]', content):
                english_words = re.findall(r'[a-zA-Z]+', content)
                issues.append(f"외국어(영어) 노출: {', '.join(english_words[:3])}...")

        # 3. 금기어 검사
        for term in self.FORBIDDEN_TERMS:
            if term in content:
                issues.append(f"장르 파괴 금기어 발견: '{term}'")

        # 4. 숫자(아라비아 숫자) 미변환 검사 (장르에 따라 완화 가능)
        if self._should_check_numbers():
            if re.search(r'\d+', content):
                numbers = re.findall(r'\d+', content)
                issues.append(f"미변환 숫자 발견: {', '.join(numbers[:5])}...")

        return {
            "is_pure": len(issues) == 0,
            "issues": issues
        }
    
    @abstractmethod
    def get_v20_purism_prompt(self):
        """장르별 순혈주의 프롬프트 생성"""
        pass
    
    def _should_check_english(self):
        """영어 검증 여부 (장르별 오버라이드 가능)"""
        return True

    def _should_check_numbers(self):
        """숫자 검증 여부 (장르별 오버라이드 가능)"""
        return True

    # ========================================================================
    # [V46] 일관성 검증 인터페이스 (Consistency Validation Interface)
    # ========================================================================

    def get_impossible_actions(self, current_state: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        [V46] 현재 상태에서 불가능한 행동 패턴 반환

        Args:
            current_state: HUD actual_truth 데이터
                - causal_injuries: 부상 상태
                - realm: 경지/등급
                - equipment: 보유 장비
                - internal_energy: 내공/마나 등

        Returns:
            list: [{'pattern': r'정규식', 'reason': '불가능 사유', 'severity': 'HIGH'}]

        Note:
            - 하드코딩 금지: HUD 상태에서 동적으로 규칙 추론
            - 장르별 서브클래스에서 구체 구현
        """
        return []  # 기본값: 제한 없음

    def get_justification_patterns(self) -> List[str]:
        """
        [V46] 정당화로 인정되는 표현 패턴 반환

        불가능해 보이는 행동이라도 이 패턴과 함께 등장하면 허용

        Returns:
            list: [r'정규식1', r'정규식2', ...]

        Examples (무협):
            - r'내공.*이용' → "내공을 이용해 분산시켰다"
            - r'죽기.*살기' → "죽기 살기로 힘을 끌어올렸다"
        """
        return []  # 기본값: 정당화 패턴 없음

    def get_hierarchy_rules(self) -> Dict[str, Any]:
        """
        [V46] 직위/호칭 위계 규칙 반환

        Returns:
            dict: {
                'ranks': ['최하위', '하위', '중간', '상위', '최상위'],
                'titles': {'rank': ['허용된 호칭들']},
                'address_rules': {'상위→하위': '반말/하대', '하위→상위': '존칭'}
            }

        Note:
            - 직위/호칭 불일치는 정당화 불가 (명백한 오류)
        """
        return {}  # 기본값: 위계 규칙 없음

    def check_state_action_consistency(self, manuscript: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        [V46] 상태 vs 행동 일관성 검증 (범용 로직)

        Args:
            manuscript: 검증 대상 원고
            current_state: HUD actual_truth 데이터

        Returns:
            dict: {
                'passed': bool,
                'violations': [{'action': str, 'reason': str, 'has_justification': bool}],
                'score_penalty': int  # 0 ~ -15
            }
        """
        violations = []
        impossible_actions = self.get_impossible_actions(current_state)
        justifications = self.get_justification_patterns()

        for action in impossible_actions:
            pattern = action.get('pattern', '')
            reason = action.get('reason', '불명')

            if not pattern:
                continue

            # 정규식 매칭
            matches = re.findall(pattern, manuscript)
            if matches:
                # 정당화 패턴 존재 여부 확인
                has_justification = any(
                    re.search(jp, manuscript) for jp in justifications
                )

                if not has_justification:
                    violations.append({
                        'action': matches[0] if matches else pattern,
                        'reason': reason,
                        'has_justification': False,
                        'severity': action.get('severity', 'MEDIUM')
                    })
                # 정당화 있으면 violations에 추가하지 않음 (PASS)

        # 점수 감점 계산
        score_penalty = 0
        for v in violations:
            if v['severity'] == 'HIGH':
                score_penalty -= 5
            elif v['severity'] == 'MEDIUM':
                score_penalty -= 3
            else:
                score_penalty -= 1

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'score_penalty': max(-15, score_penalty)  # 최대 -15점
        }

    def check_hierarchy_consistency(self, manuscript: str, character_rank: str) -> Dict[str, Any]:
        """
        [V46] 직위/호칭 일관성 검증

        Args:
            manuscript: 검증 대상 원고
            character_rank: 캐릭터의 현재 직위/등급

        Returns:
            dict: {
                'passed': bool,
                'violations': [{'found': str, 'expected': str, 'reason': str}]
            }
        """
        hierarchy = self.get_hierarchy_rules()
        if not hierarchy:
            return {'passed': True, 'violations': []}

        violations = []
        titles = hierarchy.get('titles', {})
        allowed_titles = titles.get(character_rank, [])

        # 직위별 금지된 호칭 검사
        for rank, rank_titles in titles.items():
            if rank == character_rank:
                continue  # 자신의 호칭은 스킵

            for title in rank_titles:
                # 주인공이 자신을 부르는 패턴 검색
                self_address_patterns = [
                    f'나는.*{title}',
                    f'본좌.*{title}',
                    f'소생.*{title}'
                ]

                for pattern in self_address_patterns:
                    if re.search(pattern, manuscript):
                        if title not in allowed_titles:
                            violations.append({
                                'found': title,
                                'expected': ', '.join(allowed_titles) if allowed_titles else '해당 없음',
                                'reason': f"직위 '{character_rank}'에서 '{title}' 자칭 불가"
                            })

        return {
            'passed': len(violations) == 0,
            'violations': violations
        }

    # ========================================================================
    # [V46.1] 권위 위임 검증 인터페이스 (Authority Delegation)
    # ========================================================================

    def get_authority_hierarchy(self) -> Dict[str, Any]:
        """
        [V46.1] 권위/직위 위계 구조 반환

        Returns:
            dict: {
                'positions': ['최고위', '상위', '중위', '하위'],  # 높은 순
                'position_titles': {
                    '가주': ['가주', '문주', '방주'],
                    '가주대행': ['대행', '권한대행'],
                    '장로': ['장로', '원로'],
                    ...
                },
                'delegation_required': ['가주대행', '대리']  # 명분 필요한 직위들
            }
        """
        return {}  # 기본값: 권위 구조 없음

    def get_delegation_patterns(self) -> List[str]:
        """
        [V46.1] 권위 위임을 정당화하는 표현 패턴

        Returns:
            list: [r'~의 명으로', r'~께서 위임', ...]
        """
        return []  # 기본값: 위임 패턴 없음

    def check_authority_delegation(self, manuscript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        [V46.1] 권위 위임 일관성 검증

        상위자 생존 시 하위자가 상위 직위 자칭하면 경고
        명분 표현 있으면 정당화

        Args:
            manuscript: 검증 대상 원고
            context: {
                'protagonist_position': str,  # 주인공 현재 직위
                'superior_alive': bool,       # 상위자 생존 여부
                'superior_name': str,         # 상위자 이름
                'superior_position': str      # 상위자 직위
            }

        Returns:
            dict: {
                'passed': bool,
                'violations': [...],
                'has_justification': bool
            }
        """
        violations = []
        hierarchy = self.get_authority_hierarchy()
        delegation_patterns = self.get_delegation_patterns()

        if not hierarchy:
            return {'passed': True, 'violations': [], 'has_justification': False}

        protagonist_pos = context.get('protagonist_position', '')
        superior_alive = context.get('superior_alive', True)
        superior_name = context.get('superior_name', '')
        superior_position = context.get('superior_position', '')

        # 상위자가 생존해 있는 경우만 검증
        if not superior_alive:
            return {'passed': True, 'violations': [], 'has_justification': False}

        # 위임이 필요한 직위 목록
        delegation_required = hierarchy.get('delegation_required', [])
        position_titles = hierarchy.get('position_titles', {})

        # 주인공이 상위 직위를 자칭하는지 검사
        for pos, titles in position_titles.items():
            if pos == protagonist_pos:
                continue  # 자신의 직위는 스킵

            # 상위 직위인지 확인
            positions = hierarchy.get('positions', [])
            if pos in positions and protagonist_pos in positions:
                pos_idx = positions.index(pos)
                prot_idx = positions.index(protagonist_pos)
                if pos_idx >= prot_idx:
                    continue  # 상위 직위가 아니면 스킵

            for title in titles:
                # 자칭 패턴 검색
                self_claim_patterns = [
                    f'나는.*{title}',
                    f'본.*{title}',
                    f'{title}인 내가',
                    f'{title}로서',
                    f'{title} 대행',
                ]

                for pattern in self_claim_patterns:
                    if re.search(pattern, manuscript):
                        # 명분/위임 표현 확인
                        has_delegation = any(
                            re.search(dp, manuscript) for dp in delegation_patterns
                        )

                        # 상위자 이름으로 명분 빌리는지 확인
                        if superior_name:
                            superior_delegation = [
                                f'{superior_name}.*명',
                                f'{superior_name}.*위임',
                                f'{superior_name}.*허락',
                                f'{superior_name}.*뜻',
                            ]
                            has_delegation = has_delegation or any(
                                re.search(sp, manuscript) for sp in superior_delegation
                            )

                        if not has_delegation:
                            violations.append({
                                'claimed_position': title,
                                'actual_position': protagonist_pos,
                                'superior': f"{superior_name}({superior_position})" if superior_name else superior_position,
                                'reason': f"상위자 '{superior_position}' 생존 시 '{title}' 자칭은 명분 필요",
                                'severity': 'HIGH'
                            })

        has_justification = len(violations) == 0 or any(
            re.search(dp, manuscript) for dp in delegation_patterns
        )

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'has_justification': has_justification
        }

    # ========================================================================
    # [V46.1] 미해결 갈등 검증 인터페이스 (Unresolved Conflict / 고구마 감지)
    # ========================================================================

    def get_hostile_action_types(self) -> List[str]:
        """
        [V46.1] 적대적 행동 유형 반환 (고구마 요소 판단 기준)

        Returns:
            list: ['구타', '모욕', '배신', '암살시도', ...]
        """
        return ['구타', '모욕', '배신', '암살', '독살', '협박', '멸시', '학대']

    def get_resolution_patterns(self) -> List[str]:
        """
        [V46.1] 갈등 해소를 나타내는 패턴

        Returns:
            list: [r'용서', r'복수', r'응징', ...]
        """
        return [
            r'용서',
            r'복수',
            r'응징',
            r'처단',
            r'굴복',
            r'사과.*받',
            r'무릎.*꿇',
            r'공포.*질',
            r'벌.*받',
            r'대가.*치르',
        ]

    def check_unresolved_conflict(self, manuscript: str, karma_matrix: Dict[str, Any],
                                   ep_num: int) -> Dict[str, Any]:
        """
        [V46.1] 미해결 갈등 검증 (고구마 감지)

        적대 NPC가 관계변화/응징 없이 동행/협력하면 경고

        Args:
            manuscript: 검증 대상 원고
            karma_matrix: NPC 관계 데이터
            ep_num: 현재 에피소드 번호

        Returns:
            dict: {
                'passed': bool,
                'violations': [{'npc': str, 'hostile_action': str, 'current_status': str}],
                'goguma_score': int  # 0~10 (높을수록 고구마)
            }
        """
        violations = []
        goguma_score = 0

        if not karma_matrix or not isinstance(karma_matrix, dict):
            return {'passed': True, 'violations': [], 'goguma_score': 0}

        hostile_actions = self.get_hostile_action_types()
        resolution_patterns = self.get_resolution_patterns()

        for npc_name, npc_data in karma_matrix.items():
            if not isinstance(npc_data, dict):
                continue

            events = npc_data.get('events', [])
            current_relation = npc_data.get('relation_type', '')

            # 적대적 이벤트가 있었는지 확인
            hostile_event = None
            for event in events:
                if isinstance(event, dict):
                    event_type = event.get('type', '')
                    if any(ha in str(event_type) for ha in hostile_actions):
                        hostile_event = event
                        break

            if not hostile_event:
                continue

            # 해결 이벤트가 있었는지 확인
            resolved = False
            for event in events:
                if isinstance(event, dict):
                    event_type = event.get('type', '')
                    if any(rp in str(event_type) for rp in ['용서', '복수', '응징', '처단', '굴복']):
                        resolved = True
                        break

            # 현재 원고에서 해결 패턴이 있는지 확인
            has_resolution_in_manuscript = any(
                re.search(rp, manuscript) for rp in resolution_patterns
            )

            if resolved or has_resolution_in_manuscript:
                continue

            # 동행/협력 패턴 검색
            companion_patterns = [
                f'{npc_name}.*함께',
                f'{npc_name}.*동행',
                f'{npc_name}.*따라',
                f'{npc_name}.*수행',
                f'{npc_name}.*옆에',
                f'{npc_name}이 말했다',
                f'{npc_name}가 말했다',
            ]

            is_companion = any(re.search(cp, manuscript) for cp in companion_patterns)

            if is_companion:
                # 공포/굴복 묘사가 있는지 확인 (정당화)
                fear_patterns = [
                    f'{npc_name}.*공포',
                    f'{npc_name}.*두려',
                    f'{npc_name}.*벌벌',
                    f'{npc_name}.*고개.*숙',
                    f'{npc_name}.*감히',
                    f'{npc_name}.*말도.*못',
                ]
                has_fear = any(re.search(fp, manuscript) for fp in fear_patterns)

                if not has_fear:
                    hostile_type = hostile_event.get('type', '적대 행동')
                    violations.append({
                        'npc': npc_name,
                        'hostile_action': hostile_type,
                        'current_status': '동행/협력',
                        'reason': f"'{npc_name}'이(가) 과거 '{hostile_type}' 후 응징/변화 없이 동행 중 (고구마)",
                        'severity': 'MEDIUM'
                    })
                    goguma_score += 3

        # 고구마 점수 상한
        goguma_score = min(10, goguma_score)

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'goguma_score': goguma_score
        }

    # ========================================================================
    # [V46.1] 빌런 반응 검증 인터페이스 (Villain Response Check)
    # ========================================================================

    def get_protagonist_victory_patterns(self) -> List[str]:
        """
        [V46.1] 주인공 대역전/승리 패턴

        Returns:
            list: [r'역전', r'승리', r'각성', ...]
        """
        return [
            r'역전',
            r'승리.*거두',
            r'이겼다',
            r'쓰러뜨',
            r'제압',
            r'각성',
            r'돌파',
            r'비밀.*밝혀',
            r'음모.*파훼',
        ]

    def get_villain_response_patterns(self) -> List[str]:
        """
        [V46.1] 빌런의 적절한 대응 패턴

        Returns:
            list: [r'당황', r'분노', r'계획 변경', ...]
        """
        return [
            r'당황',
            r'경악',
            r'분노',
            r'이를.*갈',
            r'계획.*변경',
            r'후퇴',
            r'숨.*죽',
            r'다음.*기회',
            r'복수.*다짐',
            r'자리.*비워',  # 지능적 제약 (마교 밀약 등)
            r'급한.*일',
            r'소환',
            r'떠나',
        ]

    def check_villain_response(self, manuscript: str, villain_context: Dict[str, Any],
                                recent_events: List[Dict]) -> Dict[str, Any]:
        """
        [V46.1] 빌런 반응 검증

        주인공 대역전 후 빌런이 가만히 있으면 "무능한 빌런" 경고

        Args:
            manuscript: 검증 대상 원고
            villain_context: {
                'villain_name': str,
                'villain_role': str,  # '주적', '부적', '하수인'
                'is_aware': bool      # 빌런이 사건을 인지했는지
            }
            recent_events: 최근 에피소드 주요 이벤트

        Returns:
            dict: {
                'passed': bool,
                'violations': [...],
                'incompetent_villain_risk': bool
            }
        """
        violations = []

        villain_name = villain_context.get('villain_name', '')
        villain_role = villain_context.get('villain_role', '')
        is_aware = villain_context.get('is_aware', True)

        if not villain_name or not is_aware:
            return {'passed': True, 'violations': [], 'incompetent_villain_risk': False}

        victory_patterns = self.get_protagonist_victory_patterns()
        response_patterns = self.get_villain_response_patterns()

        # 주인공 대역전 이벤트 확인
        has_protagonist_victory = False
        for event in recent_events:
            if isinstance(event, dict):
                event_type = event.get('type', '')
                if any(vp in str(event_type) for vp in ['역전', '승리', '각성', '돌파']):
                    has_protagonist_victory = True
                    break

        # 현재 원고에서도 확인
        if not has_protagonist_victory:
            has_protagonist_victory = any(
                re.search(vp, manuscript) for vp in victory_patterns
            )

        if not has_protagonist_victory:
            return {'passed': True, 'violations': [], 'incompetent_villain_risk': False}

        # 빌런의 대응 확인
        villain_specific_response = [
            f'{villain_name}.*당황',
            f'{villain_name}.*경악',
            f'{villain_name}.*분노',
            f'{villain_name}.*이를',
            f'{villain_name}.*계획',
            f'{villain_name}.*떠나',
            f'{villain_name}.*자리.*비',
        ]

        has_response = any(re.search(rp, manuscript) for rp in villain_specific_response)

        # 일반 대응 패턴도 확인
        if not has_response:
            has_response = any(re.search(rp, manuscript) for rp in response_patterns)

        # 빌런이 원고에 언급되는지 확인
        villain_mentioned = villain_name in manuscript

        if villain_mentioned and not has_response:
            violations.append({
                'villain': villain_name,
                'role': villain_role,
                'reason': f"주인공 대역전 후 빌런 '{villain_name}'의 대응이 없음 (무능한 빌런 위험)",
                'severity': 'MEDIUM',
                'suggestion': f"'{villain_name}'이(가) 당황/분노하거나, 자리를 비워야 하는 이유(급한 일, 밀약 등)를 설정하세요."
            })

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'incompetent_villain_risk': len(violations) > 0
        }
