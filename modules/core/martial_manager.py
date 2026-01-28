import re
from .constants import MARTIAL_METRICS # 👈 상수 임포트

class MartialManager:
    """[V25 Sovereign Synchronized Core] DB 스키마와 성경 데이터 간의 1:1 무결성을 보장하는 최종 엔진"""

    def __init__(self, context):
        self.context = context
        # DB(martial_tracker) 컬럼명과 100% 일치하는 15대 표준 캐노니컬 키
        self.canonical_map = {
            'internal_energy': ['energy', 'PhysicalStatus', 'internal_energy', '내공', '공력', '내공수치'],
            'mental_method': ['current_technique', 'MentalMethod', 'mental_method', '심법', '수련법'],
            'realm': ['level', 'rank', 'realm', '경지', '무력단계'],
            'wealth': ['funds', 'Wealth', 'wealth', '자금', '재산', '은자'],
            'causal_injuries': ['injuries', 'physical_status', 'Status', 'causal_injuries', '상태', '부상', '내상'],
            'current_objective': ['CurrentObjective', 'objective', 'current_objective', '목표', '현재목표'],
            'reputation': ['reputation', 'fame', '명성', '평판'],
            'public_image': ['public_image', 'appearance', '이미지', '인상'],
            'equipment': ['equipment', 'items', '장비', '착용아이템'],
            'token': ['token', 'relic', '신물', '증표'],
            'qi_nature': ['qi_nature', 'attribute', '진기성질', '기운'],
            'rank': ['rank', 'position', '직위', '신분'],
            'alias': ['alias', 'title', '별호', '칭호'],
            'misunderstanding': ['misunderstanding', '착각', '오해지수'],
            'obsession': ['obsession', '집착', '집착지수']
        }

    @property
    def pro_root(self):
        """Protagonist 데이터의 루트 레이어 확보"""
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        hud_data = bible.get('MartialHUD', bible.get('martial_hud', {}))
        
        # [V40 Safety] HUD 데이터가 없으면 기본 구조 생성
        if not hud_data or not isinstance(hud_data, dict):
            hud_data = {
                'Protagonist': {
                    'actual_truth': {
                        'name': '주인공',
                        'realm': '초출',
                        'internal_energy': 0,
                        'mental_method': '기본 심법',
                        'wealth': '은자 100냥',
                        'causal_injuries': '정상',
                        'current_objective': '강해지기',
                        'reputation': '무명'
                    }
                }
            }
            bible['MartialHUD'] = hud_data
        
        return hud_data.get('Protagonist', hud_data)

    @property
    def pro_data(self):
        """[Actual Truth] 실제 물리적 수치 주머니 인출"""
        return self.pro_root.get('actual_truth', self.pro_root)

    # --- [데이터 통합 수혈 및 정규화 엔진] ---
    def _get_normalized_val(self, canonical_key, default="기록 없음"):
        """변칙 키들을 뒤져서 표준 키의 값을 찾아 반환함"""
        fallbacks = self.canonical_map.get(canonical_key, [canonical_key])
        for key in fallbacks:
            val = self.pro_data.get(key)
            if val is not None: return val
        return default

    # --- [통합 속성 관리] ---
    @property
    def name(self): return self.pro_data.get('name', self.pro_data.get('Name', self.pro_data.get('alias', '주인공')))
    @property
    def alias(self): return self.pro_data.get('alias', '무명인')
    @property
    def rank(self): return self.pro_data.get('rank', '평민')
    @property
    def realm(self): return self.pro_data.get('realm', '초출')
    @property
    def internal_energy(self) -> float:
        val = self.pro_data.get('internal_energy', 0)
        try:
            # [V40.1 Critical Fix] guard가 None일 경우 대비
            if self.context.guard is None:
                # guard 없이 직접 변환 시도
                return float(val) if isinstance(val, (int, float)) else 0.0
            return float(self.context.guard.convert_to_numeric(str(val)))
        except (ValueError, TypeError, AttributeError):
            return 0.0 # 에러 시 기본값 반환으로 시스템 멈춤 방지

    def get_internal_energy_description(self) -> str:
        """
        [V40.1] 내공 수치를 AI 판단 기반 서술형으로 변환
        서술형 + 정확한 수치를 함께 표시하여 에이전트가 올바른 판단 가능
        """
        try:
            energy = self.internal_energy

            # [V40.1 Safety] 특수값 처리 (음수, inf, nan)
            if energy < 0:
                return "내공 수치 오류 (음수)"
            if not isinstance(energy, (int, float)) or energy != energy:  # NaN 체크
                return "내공 수치 오류 (비정상)"
            if energy == float('inf'):
                return "내공 수치 오류 (무한대)"

            if energy < 0.1:
                desc = "내공이 거의 없음"
            elif energy < 1:
                desc = "기초 수준의 내공"
            elif energy < 5:
                desc = "내공이 많지 않음"
            elif energy < 10:
                desc = "약간의 내공을 보유"
            elif energy < 30:
                desc = "상당한 내공을 축적"
            elif energy < 50:
                desc = "풍부한 내공을 갖춤"
            elif energy < 100:
                desc = "강력한 내공을 지님"
            elif energy < 200:
                desc = "깊은 내공을 보유"
            else:
                # 200년 이상은 이미 수치 포함
                return f"심오한 경지의 내공 ({int(energy)}년)"

            # 200년 미만은 서술형 + 수치 병기
            # [V40.1 포맷팅] 소수점 처리 (0.0년 같은 경우 깔끔하게)
            if energy == int(energy):
                return f"{desc} ({int(energy)}년)"
            else:
                return f"{desc} ({energy:.1f}년)"
        except Exception as e:
            # 예상치 못한 에러 발생 시 안전한 기본값 반환
            return f"내공 정보 없음 (오류: {str(e)[:20]})"
    @property
    def mental_method(self): return self._get_normalized_val('mental_method')
    @property
    def wealth(self): return self._get_normalized_val('wealth')
    @property
    def causal_injuries(self): return self._get_normalized_val('causal_injuries')
    @property
    def qi_nature(self): return self.pro_data.get('qi_nature', '무색무취')
    @property
    def equipment(self): return self.pro_data.get('equipment', '평범한 무복')
    @property
    def token(self): return self.pro_data.get('token', '없음')
    @property
    def objective(self): return self._get_normalized_val('current_objective')
    @property
    def misunderstanding(self) -> int:
        """항상 정수(int) 타입을 보장함"""
        val = self.pro_data.get('misunderstanding', 0)
        try:
            # [V40.1 Critical Fix] guard가 None일 경우 대비
            if self.context.guard is None:
                return int(val) if isinstance(val, (int, float)) else 0
            return int(self.context.guard.convert_to_numeric(str(val)))
        except (ValueError, TypeError, AttributeError):
            return 0
    @property
    def obsession(self) -> int:
        """항상 정수(int) 타입을 보장함"""
        val = self.pro_data.get('obsession', 0)
        try:
            # [V40.1 Critical Fix] guard가 None일 경우 대비
            if self.context.guard is None:
                return int(val) if isinstance(val, (int, float)) else 0
            return int(self.context.guard.convert_to_numeric(str(val)))
        except (ValueError, TypeError, AttributeError):
            return 0
    @property
    def inventory(self): return self.pro_data.get('inventory', [])
    @property
    def techniques(self):
        techs = self.pro_data.get('martial_arts', self.pro_data.get('SignatureMove', []))
        return [t.strip() for t in techs.split(',')] if isinstance(techs, str) else techs

    # --- [핵심 업데이트부: 데이터 정규화 가드] ---
    def update_physical_status(self, full_state_data):
        """[🛡️ Guard Logic] 에이전트의 변칙 키를 표준 키로 강제 치환하여 성경에 박제"""
        if not full_state_data: return [] # 변경 사항 리스트 반환으로 변경

        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        pro = bible.setdefault('MartialHUD', {}).setdefault('Protagonist', {})
        actual = pro.setdefault('actual_truth', {})
        actual_in = full_state_data.get('actual_truth', full_state_data)

        update_logs = []
        for canonical_key in MARTIAL_METRICS: # 👈 상수를 직접 순회
            # 1단계: canonical_map에 정의된 변칙 키들을 모두 뒤져서 값 찾기
            val = None
            for alt_key in self.canonical_map.get(canonical_key, [canonical_key]):
                if alt_key in actual_in:
                    val = actual_in[alt_key]
                    break  # 값을 찾았으니 더 이상 검색하지 않음

            # 2단계: 값을 찾았다면 변환 및 업데이트 (for alt_key 루프 밖에서!)
            if val is not None:
                # [V35.6 Fix] 수치형 데이터 변환 시 텍스트 정보 유실 방지 가드 가동
                if canonical_key in ['misunderstanding', 'obsession', 'internal_energy']:
                    raw_str_val = str(val).strip()

                    # [V40.1 Critical Fix] guard가 None일 경우 대비
                    if self.context.guard is None:
                        # guard 없이 직접 변환 시도
                        try:
                            numeric_res = float(raw_str_val)
                        except (ValueError, TypeError):
                            numeric_res = 0
                    else:
                        numeric_res = self.context.guard.convert_to_numeric(raw_str_val)

                    # 변환 결과가 0이지만, 원본이 실제 숫자 '0' 계열이 아닌 경우 텍스트 보존
                    if numeric_res == 0 and raw_str_val not in ["0", "0.0", "영", "없음"]:
                        # 수치화할 수 없는 고유 묘사(예: "매우 높음")는 문자열 그대로 유지
                        pass
                    else:
                        val = numeric_res

                # 3단계: 실제 업데이트 수행
                old_val = actual.get(canonical_key)
                # 값의 물리적 내용이 변했을 때만 업데이트 수행
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    update_logs.append(f"{canonical_key}: {old_val} -> {val}")

        # 2. 리스트 데이터 및 상태 맵 유지
        for key in ['inventory', 'martial_arts', 'public_reputation', 'knowledge_map']:
            if key in full_state_data: pro[key] = full_state_data[key]
            elif key in actual_in: actual[key] = actual_in[key]

        if update_logs:
                self.context.save_v20_anchor("bible", self.context.master_bible)
            
        return update_logs # 👈 변경된 리스트를 메인으로 던져줌

    def get_critical_keys(self):
        """[V40] 무협 장르 필수 추적 키"""
        return ['realm', 'internal_energy', 'mental_method', 'wealth', 'current_objective', 'causal_injuries', 'reputation']
    
    def get_v20_hud_report(self):
        """[V25 High-Res] 정규화된 데이터 기반의 무결성 리포트 출력 (None 값 방어 처리 추가)"""
        rep = self.pro_root.get('public_reputation', {})

        # None 값 방어: 각 속성이 None이면 기본 설명으로 대체
        def safe_str(value, default="기록 없음"):
            return str(value) if value is not None else default

        name = safe_str(self.name, "주인공")
        alias = safe_str(self.alias, "무명인")
        rank = safe_str(self.rank, "평민")
        realm = safe_str(self.realm, "초출")
        mental_method = safe_str(self.mental_method, "수련 중인 심법 없음")
        causal_injuries = safe_str(self.causal_injuries, "특이사항 없음")
        wealth = safe_str(self.wealth, "자금 정보 없음")
        objective = safe_str(self.objective, "목표 미설정")

        techniques_list = self.techniques if self.techniques else ['기초 무공']
        techniques_str = ', '.join(str(t) for t in techniques_list)

        return f"""
[🛡️ V25 SOVEREIGN HUD - 실시간 다층 통합 상태]
─────────── [실제 진실 (Actual Truth)] ───────────
- 성명: {name} ({alias}) | 직위: {rank}
- 경지: {realm} | 내공: {self.get_internal_energy_description()} | 심법: {mental_method}
- 상태: {causal_injuries} | 자금: {wealth}
- 무공: {techniques_str}

─────────── [세간의 인식 (Reputation)] ───────────
- 대외 호칭: {rep.get('identity', '기록 없음')}
- 인식상 경지: {rep.get('realm', '알 수 없음')}
- 소문난 위력: {rep.get('perceived_power', '평범함')}
- 서사 지표: 착각({self.misunderstanding}) | 집착({self.obsession})
- 목표: {objective}
"""