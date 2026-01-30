"""
[V47] TIER 0.5: CONTINUITY Validator
에피소드 간 연속성 검증 (API 호출 불필요 - 순수 Python)

핵심 역할:
1. 아이템 소지 연속성 - 이미 가진 아이템을 다시 획득하러 가는 패턴 감지
2. 무기 소지 연속성 - 들고 있던 무기가 사라지는 문제 감지
3. 부상 상태 연속성 - 부상 상태에서 무리한 행동 감지
4. 위치 연속성 - 순간이동 방지

실행 시점:
- Blueprint 생성 시 (Architect) → 사전 검증
- Manuscript 생성 시 (Director) → 재확인

비용: $0 (LLM 호출 없음)
"""

import re
from typing import Dict, List, Any, Optional, Set


class ContinuityValidator:
    """
    TIER 0.5: 에피소드 간 연속성 검증
    
    BLOCKING보다 먼저 실행되어야 함.
    직전 에피소드 상태와 현재 원고/블루프린트 간 모순 감지.
    """
    
    def __init__(self, context=None):
        """
        Args:
            context: ProjectContext 객체 (직전 에피소드 데이터 조회용)
        """
        self.context = context
        
        # 아이템 획득 패턴 (한국어)
        self.acquire_patterns = [
            r"(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들|획득|챙기|얻|주워\s*들)",
            r"(.+?)(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
            r"(?:녹슨|묵직한|육중한)?\s*(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들)",
        ]
        
        # 아이템 분실 패턴
        self.lose_patterns = [
            r"(.+?)(?:을|를)\s*(?:잃어버리|놓치|떨어뜨리|버리|내려놓)",
            r"(.+?)(?:이|가)\s*(?:부러지|파손되|사라지)",
        ]
        
        # 부상 관련 패턴
        self.injury_patterns = [
            r"(?:부상|상처|골절|파열|출혈|중상|경상)",
            r"(?:어깨|팔|다리|등|가슴|복부).*?(?:다치|부상|파열)",
        ]
        
        # 무리한 행동 패턴 (부상 시 불가능한 행동)
        self.strenuous_patterns = [
            r"(?:휘두르|내리치|베어|찌르|막아내)",
            r"(?:달리|뛰어|도약|점프)",
            r"(?:들어올리|메|짊어지)",
        ]
        
        # 이동 패턴 (위치 변경 감지용)
        self.location_patterns = [
            r"(?:로|으로)\s*(?:향하|이동하|걸어가|달려가)",
            r"(?:에서|부터)\s*(?:나와|나서|떠나)",
            r"(?:에|로)\s*(?:도착|당도)",
        ]
    
    def validate(self, current_ep: int, manuscript: str, 
                 validation_context: dict, prev_hud: Optional[dict] = None) -> dict:
        """
        연속성 검증 실행
        
        Args:
            current_ep: 현재 에피소드 번호
            manuscript: 현재 원고/블루프린트
            validation_context: 검증 컨텍스트
            prev_hud: 직전 에피소드 HUD (없으면 context에서 조회)
        
        Returns:
            {
                "tier": "CONTINUITY",
                "passed": True/False,
                "violations": [...],
                "warnings": [...],
                "message": "..."
            }
        """
        violations = []
        warnings = []
        
        # 1화는 이전 에피소드가 없으므로 스킵
        if current_ep <= 1:
            return {
                "tier": "CONTINUITY",
                "passed": True,
                "violations": [],
                "warnings": [],
                "message": "첫 번째 에피소드 - 연속성 검증 스킵"
            }
        
        # 직전 에피소드 HUD 가져오기
        if prev_hud is None:
            prev_hud = self._get_prev_hud(current_ep, validation_context)
        
        if not prev_hud:
            return {
                "tier": "CONTINUITY",
                "passed": True,
                "violations": [],
                "warnings": [{"type": "no_prev_hud", "message": "직전 HUD 없음 - 연속성 검증 제한적"}],
                "message": "직전 HUD 없음 - 일부 검증 스킵"
            }
        
        # 직전 원고 가져오기 (선택적)
        prev_manuscript = self._get_prev_manuscript(current_ep, validation_context)
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 1: 아이템 소지 연속성
        # ═══════════════════════════════════════════════════════════════
        item_check = self._check_item_continuity(
            current_ep, manuscript, prev_hud, prev_manuscript
        )
        if not item_check['passed']:
            violations.extend(item_check['violations'])
        warnings.extend(item_check.get('warnings', []))
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 2: 무기 소지 연속성
        # ═══════════════════════════════════════════════════════════════
        weapon_check = self._check_weapon_continuity(
            current_ep, manuscript, prev_hud, prev_manuscript
        )
        if not weapon_check['passed']:
            violations.extend(weapon_check['violations'])
        warnings.extend(weapon_check.get('warnings', []))
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 3: 부상 상태 연속성
        # ═══════════════════════════════════════════════════════════════
        injury_check = self._check_injury_continuity(
            current_ep, manuscript, prev_hud, prev_manuscript
        )
        if not injury_check['passed']:
            violations.extend(injury_check['violations'])
        warnings.extend(injury_check.get('warnings', []))
        
        # ═══════════════════════════════════════════════════════════════
        # 검증 4: 위치 연속성 (선택적 - 경고만)
        # ═══════════════════════════════════════════════════════════════
        location_check = self._check_location_continuity(
            current_ep, manuscript, prev_hud, prev_manuscript
        )
        warnings.extend(location_check.get('warnings', []))
        
        # 결과 집계
        passed = len(violations) == 0
        
        if passed:
            message = "연속성 검증 통과"
        else:
            message = f"연속성 위반 {len(violations)}건 감지"
        
        return {
            "tier": "CONTINUITY",
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "message": message,
            "violation_count": len(violations),
            "warning_count": len(warnings)
        }
    
    def _get_prev_hud(self, current_ep: int, validation_context: dict) -> Optional[dict]:
        """직전 에피소드 HUD 가져오기"""
        # 1. validation_context에서 직접 제공된 경우
        prev_hud = validation_context.get('prev_hud')
        if prev_hud:
            return prev_hud
        
        # 2. context를 통해 DB에서 조회
        if self.context and hasattr(self.context, 'db'):
            try:
                prev_ep = current_ep - 1
                manuscript_data = self.context.db.get_manuscript(prev_ep)
                if manuscript_data:
                    hud_snapshot = manuscript_data.get('hud_snapshot')
                    if hud_snapshot:
                        if isinstance(hud_snapshot, str):
                            import json
                            return json.loads(hud_snapshot)
                        return hud_snapshot
            except Exception as e:
                print(f"      ⚠️ [CONTINUITY] 직전 HUD 조회 실패: {e}")
        
        # 3. martial_hud에서 이전 상태 추론 (fallback)
        martial_hud = validation_context.get('martial_hud', {})
        if martial_hud:
            return martial_hud  # 현재 HUD를 이전으로 가정 (제한적)
        
        return None
    
    def _get_prev_manuscript(self, current_ep: int, validation_context: dict) -> Optional[str]:
        """직전 에피소드 원고 가져오기"""
        # 1. validation_context에서 제공된 경우
        prev_text = validation_context.get('prev_full_text')
        if prev_text:
            return prev_text
        
        # 2. history에서 가져오기
        history = validation_context.get('history', [])
        if history and len(history) > 0:
            last_entry = history[-1]
            if isinstance(last_entry, dict):
                return last_entry.get('text', '')
            return str(last_entry)
        
        # 3. context를 통해 DB에서 조회
        if self.context and hasattr(self.context, 'db'):
            try:
                prev_ep = current_ep - 1
                manuscript_data = self.context.db.get_manuscript(prev_ep)
                if manuscript_data:
                    return manuscript_data.get('text', '')
            except Exception as e:
                print(f"      ⚠️ [CONTINUITY] 직전 원고 조회 실패: {e}")
        
        return None
    
    def _extract_equipment(self, hud: dict) -> Set[str]:
        """HUD에서 장비 목록 추출"""
        equipment = set()
        
        # actual_truth.equipment 경로
        actual_truth = hud.get('actual_truth', {})
        eq_data = actual_truth.get('equipment', hud.get('equipment', []))
        
        if isinstance(eq_data, list):
            for item in eq_data:
                if isinstance(item, str) and item.strip():
                    equipment.add(item.strip())
                elif isinstance(item, dict):
                    name = item.get('name', item.get('item', ''))
                    if name:
                        equipment.add(name.strip())
        elif isinstance(eq_data, str):
            equipment.add(eq_data.strip())
        elif isinstance(eq_data, dict):
            for key, value in eq_data.items():
                if isinstance(value, str) and value:
                    equipment.add(value.strip())
                elif key and isinstance(key, str):
                    equipment.add(key.strip())
        
        return equipment
    
    def _check_item_continuity(self, current_ep: int, manuscript: str,
                               prev_hud: dict, prev_manuscript: Optional[str]) -> dict:
        """
        아이템 소지 연속성 검증
        - 이미 소유한 아이템을 다시 획득하러 가는 패턴 감지
        """
        violations = []
        warnings = []
        
        # 직전 HUD에서 소유 아이템 추출
        prev_equipment = self._extract_equipment(prev_hud)
        
        if not prev_equipment:
            return {"passed": True, "violations": [], "warnings": []}
        
        # 현재 원고에서 획득 패턴 검색
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, manuscript)
            for item_name in matches:
                item_name = item_name.strip()
                if not item_name:
                    continue
                
                # 이미 소유한 아이템인지 확인 (부분 매칭)
                for owned_item in prev_equipment:
                    # 핵심 키워드 추출 (예: "녹슨 백근 대도" → "대도", "백근")
                    if self._is_same_item(item_name, owned_item):
                        violations.append({
                            "type": "duplicate_acquisition",
                            "severity": "CRITICAL",
                            "item": item_name,
                            "owned_item": owned_item,
                            "reason": f"이미 소유한 '{owned_item}'을(를) 다시 획득하려 함",
                            "prev_ep": current_ep - 1,
                            "fix_suggestion": f"'{owned_item}'는 이미 제{current_ep-1}화에서 획득함. "
                                            f"현재 에피소드에서는 소지 상태로 시작해야 함."
                        })
                        break
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def _check_weapon_continuity(self, current_ep: int, manuscript: str,
                                 prev_hud: dict, prev_manuscript: Optional[str]) -> dict:
        """
        무기 소지 연속성 검증
        - 직전 에피소드 끝에서 들고 있던 무기가 현재 에피소드에서 사라지는 문제
        """
        violations = []
        warnings = []
        
        # 직전 원고 끝부분에서 무기 소지 상태 확인
        if prev_manuscript:
            # 마지막 500자에서 무기 관련 언급 찾기
            last_part = prev_manuscript[-500:] if len(prev_manuscript) > 500 else prev_manuscript
            
            # 무기를 들고 있는 패턴
            holding_patterns = [
                r"(.+?)(?:을|를)\s*(?:어깨에\s*메|손에\s*들|쥐)",
                r"(.+?)(?:을|를)\s*(?:끌며|끌고)",
                r"(?:메고|들고|쥐고)\s*(?:있는|있던)\s*(.+?)",
            ]
            
            held_weapons = set()
            for pattern in holding_patterns:
                matches = re.findall(pattern, last_part)
                for match in matches:
                    if isinstance(match, tuple):
                        for m in match:
                            if m.strip():
                                held_weapons.add(m.strip())
                    elif match.strip():
                        held_weapons.add(match.strip())
            
            # 현재 원고 첫 500자에서 해당 무기 확인
            if held_weapons:
                first_part = manuscript[:500] if len(manuscript) > 500 else manuscript
                
                for weapon in held_weapons:
                    # 무기 언급이 있는지 확인
                    if weapon not in first_part:
                        # 핵심 키워드로 재확인
                        keywords = self._extract_keywords(weapon)
                        mentioned = any(kw in first_part for kw in keywords if len(kw) > 1)
                        
                        if not mentioned:
                            # 무기를 다시 획득하러 가는지 확인
                            acquiring = any(
                                re.search(pattern, first_part) 
                                for pattern in self.acquire_patterns
                            )
                            
                            if acquiring:
                                violations.append({
                                    "type": "weapon_reset",
                                    "severity": "CRITICAL",
                                    "weapon": weapon,
                                    "reason": f"직전 에피소드 끝에서 '{weapon}'을(를) 소지하고 있었으나, "
                                            f"현재 에피소드에서 다시 획득하러 감",
                                    "prev_ep": current_ep - 1,
                                    "fix_suggestion": f"'{weapon}'는 이미 소지 중. "
                                                    f"에피소드 시작 시 소지 상태로 묘사해야 함."
                                })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }
    
    def _check_injury_continuity(self, current_ep: int, manuscript: str,
                                 prev_hud: dict, prev_manuscript: Optional[str]) -> dict:
        """
        부상 상태 연속성 검증
        - 부상 상태에서 무리한 행동 감지
        """
        violations = []
        warnings = []
        
        # 직전 HUD에서 부상 상태 확인
        actual_truth = prev_hud.get('actual_truth', {})
        condition = actual_truth.get('condition', prev_hud.get('condition', ''))
        
        # 부상 상태인지 확인
        injury_keywords = ['부상', '상처', '파열', '골절', '중상', '경상', '출혈', '다친']
        has_injury = any(kw in str(condition) for kw in injury_keywords)
        
        # 직전 원고에서 부상 언급 확인
        if prev_manuscript and not has_injury:
            last_part = prev_manuscript[-1000:] if len(prev_manuscript) > 1000 else prev_manuscript
            for pattern in self.injury_patterns:
                if re.search(pattern, last_part):
                    has_injury = True
                    break
        
        if has_injury:
            # 현재 원고에서 부상 부위 특정
            injury_detail = self._extract_injury_detail(str(condition), prev_manuscript)
            
            # 부상 부위와 관련된 무리한 행동 검색
            strenuous_actions = []
            for pattern in self.strenuous_patterns:
                matches = re.findall(pattern, manuscript)
                strenuous_actions.extend(matches)
            
            if strenuous_actions:
                # 정당화 패턴 확인 (역근경, 진기, 내공 등)
                justification_patterns = [
                    r"역근경",
                    r"내공.*?운용",
                    r"진기.*?순환",
                    r"고통.*?억누르",
                    r"이를\s*악물",
                ]
                
                has_justification = any(
                    re.search(jp, manuscript) for jp in justification_patterns
                )
                
                if not has_justification:
                    warnings.append({
                        "type": "injury_action_mismatch",
                        "severity": "WARNING",
                        "injury": injury_detail,
                        "actions": strenuous_actions[:3],
                        "reason": f"부상 상태({injury_detail})에서 무리한 행동 감지. "
                                f"정당화 묘사 권장 (역근경, 내공 운용 등)",
                        "fix_suggestion": "부상에도 불구하고 행동하는 이유를 내공/정신력 등으로 정당화"
                    })
        
        return {
            "passed": True,  # 부상은 경고만, REJECT하지 않음
            "violations": violations,
            "warnings": warnings
        }
    
    def _check_location_continuity(self, current_ep: int, manuscript: str,
                                   prev_hud: dict, prev_manuscript: Optional[str]) -> dict:
        """
        위치 연속성 검증 (경고만)
        - 급격한 위치 변화 감지
        """
        warnings = []
        
        # 직전 원고 끝부분에서 위치 확인
        if prev_manuscript:
            last_part = prev_manuscript[-300:] if len(prev_manuscript) > 300 else prev_manuscript
            first_part = manuscript[:300] if len(manuscript) > 300 else manuscript
            
            # 직전 위치 키워드
            prev_locations = set()
            location_markers = [
                r"(?:에서|에)\s*(.{2,10}?)(?:에서|에|를|을)",
                r"(.{2,10}?)(?:로|으로)\s*(?:향하|이동|가|걸어)",
            ]
            
            for pattern in location_markers:
                matches = re.findall(pattern, last_part)
                prev_locations.update(m.strip() for m in matches if m.strip())
            
            # 현재 위치 키워드
            curr_locations = set()
            for pattern in location_markers:
                matches = re.findall(pattern, first_part)
                curr_locations.update(m.strip() for m in matches if m.strip())
            
            # 위치 연결 확인 (시간 경과 없이 급격한 위치 변화)
            time_markers = ['이튿날', '다음날', '며칠 후', '시간이 지나', '해가 지고', '날이 밝']
            has_time_skip = any(tm in first_part for tm in time_markers)
            
            if prev_locations and curr_locations and not has_time_skip:
                # 위치가 완전히 다르면 경고
                overlap = prev_locations & curr_locations
                if not overlap and len(prev_locations) > 0 and len(curr_locations) > 0:
                    warnings.append({
                        "type": "location_jump",
                        "severity": "INFO",
                        "prev_locations": list(prev_locations)[:3],
                        "curr_locations": list(curr_locations)[:3],
                        "reason": "위치 변화가 감지됨. 이동 경위 묘사 권장",
                        "fix_suggestion": "이전 위치에서 현재 위치로 이동하는 과정을 간략히 묘사"
                    })
        
        return {
            "passed": True,  # 위치는 경고만
            "violations": [],
            "warnings": warnings
        }
    
    def _is_same_item(self, item1: str, item2: str) -> bool:
        """두 아이템이 같은 것인지 판단 (부분 매칭)"""
        # 정규화
        item1 = item1.strip().lower()
        item2 = item2.strip().lower()
        
        # 완전 일치
        if item1 == item2:
            return True
        
        # 한쪽이 다른 쪽을 포함
        if item1 in item2 or item2 in item1:
            return True
        
        # 핵심 키워드 비교
        keywords1 = self._extract_keywords(item1)
        keywords2 = self._extract_keywords(item2)
        
        # 2개 이상의 키워드가 일치하면 같은 아이템으로 판단
        common = keywords1 & keywords2
        if len(common) >= 2:
            return True
        
        # 핵심 단어가 일치하면 같은 아이템
        important_words = ['대도', '검', '창', '도끼', '활', '패', '옥', '환', '단']
        for word in important_words:
            if word in item1 and word in item2:
                return True
        
        return False
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """텍스트에서 핵심 키워드 추출"""
        # 한글 단어만 추출
        words = re.findall(r'[가-힣]+', text)
        # 조사/접미사 제거
        stopwords = {'을', '를', '이', '가', '에', '에서', '으로', '로', '의', '한', '된', '인'}
        keywords = {w for w in words if w not in stopwords and len(w) > 1}
        return keywords
    
    def _extract_injury_detail(self, condition: str, prev_manuscript: Optional[str]) -> str:
        """부상 상세 정보 추출"""
        if '어깨' in condition or (prev_manuscript and '어깨' in prev_manuscript[-500:]):
            return "어깨 부상"
        if '팔' in condition or (prev_manuscript and '팔' in prev_manuscript[-500:]):
            return "팔 부상"
        if '다리' in condition or (prev_manuscript and '다리' in prev_manuscript[-500:]):
            return "다리 부상"
        if '파열' in condition:
            return "근육 파열"
        return "부상 상태"
