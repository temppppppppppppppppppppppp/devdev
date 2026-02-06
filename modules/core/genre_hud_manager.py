"""
[V40 Multi-Genre Factory] 장르별 HUD 시스템 통합 관리자
무협/헌터/투자 3가지 장르의 HUD를 추상화하여 통일된 인터페이스 제공
"""

from abc import ABC, abstractmethod

class GenreHUDManager(ABC):
    """장르 독립적 HUD 추상 인터페이스"""
    
    def __init__(self, context):
        self.context = context
        self.canonical_map = {}  # 각 장르별로 오버라이드
    
    @property
    @abstractmethod
    def pro_root(self):
        """주인공 데이터 루트"""
        pass
    
    @property
    @abstractmethod
    def pro_data(self):
        """실제 물리적 수치 데이터"""
        pass
    
    @abstractmethod
    def get_v20_hud_report(self):
        """HUD 보고서 생성 (장르별 구현)"""
        pass
    
    @abstractmethod
    def update_physical_status(self, full_state_data):
        """상태 업데이트 (장르별 구현)"""
        pass
    
    @abstractmethod
    def get_critical_keys(self):
        """장르별 필수 추적 키 반환"""
        pass
    
    def _get_normalized_val(self, canonical_key, default="기록 없음"):
        """변칙 키 정규화 (공통 로직)"""
        fallbacks = self.canonical_map.get(canonical_key, [canonical_key])
        for key in fallbacks:
            val = self.pro_data.get(key)
            if val is not None:
                return val
        return default


class HunterHUDManager(GenreHUDManager):
    """[헌터물] 각성자/헌터 전용 HUD 시스템"""
    
    def __init__(self, context):
        super().__init__(context)
        self.canonical_map = {
            'awakening_rank': ['rank', 'hunter_rank', 'awakening_rank', '랭크', '등급', '각성등급'],
            'mana': ['mana', 'magic_power', 'mp', '마나', '마력'],
            'skills': ['skills', 'abilities', 'skill_list', '스킬', '능력'],
            'wealth': ['wealth', 'money', 'funds', '자금', '재산', '골드'],
            'injuries': ['injuries', 'status', 'hp', '부상', '상태', '체력'],
            'current_objective': ['objective', 'quest', 'current_objective', '목표', '퀘스트'],
            'reputation': ['reputation', 'fame', '명성', '평판'],
            'guild': ['guild', 'party', 'affiliation', '길드', '소속'],
            'equipment': ['equipment', 'items', '장비', '아이템'],
            'title': ['title', 'alias', '칭호', '별명'],
            'stat_points': ['stat_points', 'points', '스탯포인트', '포인트'],
            'level': ['level', 'lv', '레벨'],
            'dungeon_clear': ['dungeon_clear', 'achievements', '던전클리어', '업적']
        }
    
    @property
    def pro_root(self):
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        hud_data = bible.get('HunterHUD', bible.get('hunter_hud', {}))
        
        # [V40 Safety] HUD 데이터가 없으면 기본 구조 생성
        if not hud_data or not isinstance(hud_data, dict):
            hud_data = {
                'Protagonist': {
                    'actual_truth': {
                        'name': '각성자',
                        'awakening_rank': 'F급',
                        'mana': 0,
                        'level': 1,
                        'skills': '없음',
                        'guild': '무소속',
                        'wealth': '0원',
                        'injuries': '정상',
                        'reputation': '무명',
                        'current_objective': '생존'
                    }
                }
            }
            bible['HunterHUD'] = hud_data
        
        return hud_data.get('Protagonist', hud_data)
    
    @property
    def pro_data(self):
        return self.pro_root.get('actual_truth', self.pro_root)
    
    def get_critical_keys(self):
        """헌터물 필수 추적 키"""
        return ['awakening_rank', 'mana', 'skills', 'wealth', 'reputation', 'injuries', 'guild', 'level']
    
    def get_v20_hud_report(self):
        """헌터 HUD 보고서"""
        return f"""
[🎮 HUNTER STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get('name', '각성자')}
⭐ Rank: {self._get_normalized_val('awakening_rank', 'F급')}
🔮 Mana: {self._get_normalized_val('mana', '0')}
📊 Level: {self._get_normalized_val('level', 'Lv.1')}

💪 Skills: {self._get_normalized_val('skills', '없음')}
🏢 Guild: {self._get_normalized_val('guild', '무소속')}
💰 Wealth: {self._get_normalized_val('wealth', '0원')}
❤️ Status: {self._get_normalized_val('injuries', '정상')}

🎯 Current Quest: {self._get_normalized_val('current_objective', '생존')}
🏆 Title: {self._get_normalized_val('title', '무명 헌터')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def update_physical_status(self, full_state_data):
        """[V40.1 Fix] 헌터 상태 업데이트 - MartialManager 패턴 적용"""
        if not full_state_data:
            return []

        # [V40.1] setdefault로 안전한 경로 보장
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        pro = bible.setdefault('HunterHUD', {}).setdefault('Protagonist', {})
        actual = pro.setdefault('actual_truth', {})
        actual_in = full_state_data.get('actual_truth', full_state_data)

        changes = []
        for canonical_key, fallback_keys in self.canonical_map.items():
            val = None
            for incoming_key in fallback_keys:
                if incoming_key in actual_in:
                    val = actual_in[incoming_key]
                    break

            if val is not None:
                old_val = actual.get(canonical_key, "기록 없음")
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    changes.append(f"{canonical_key}: {old_val} → {val}")

        # [V40.1] 변경사항 있을 때 Bible 저장
        if changes:
            self.context.save_v20_anchor("bible", self.context.master_bible)

        return changes


class FinanceHUDManager(GenreHUDManager):
    """[투자물] 금융/투자 전용 HUD 시스템"""
    
    def __init__(self, context):
        super().__init__(context)
        self.canonical_map = {
            'capital': ['capital', 'cash', 'liquid_assets', '자본', '현금', '유동자산'],
            'total_assets': ['total_assets', 'net_worth', 'wealth', '총자산', '순자산'],
            'stocks': ['stocks', 'portfolio', 'holdings', '주식', '포트폴리오', '보유주식'],
            'real_estate': ['real_estate', 'properties', '부동산', '건물'],
            'companies': ['companies', 'businesses', 'owned_companies', '기업', '회사', '보유기업'],
            'reputation': ['reputation', 'credibility', 'fame', '평판', '신용도', '명성'],
            'connections': ['connections', 'network', 'relationships', '인맥', '네트워크', '관계'],
            'current_objective': ['objective', 'goal', 'current_objective', '목표', '투자목표'],
            'market_insight': ['market_insight', 'info_level', 'intelligence', '시장통찰력', '정보력'],
            'risk_level': ['risk_level', 'risk', '리스크레벨', '위험도'],
            'status': ['status', 'condition', '상태', '컨디션'],
            'position': ['position', 'title', '직위', '직책'],
            'public_image': ['public_image', 'media_presence', '대중이미지', '언론인식']
        }
    
    @property
    def pro_root(self):
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        hud_data = bible.get('FinanceHUD', bible.get('finance_hud', {}))
        
        # [V40 Safety] HUD 데이터가 없으면 기본 구조 생성
        if not hud_data or not isinstance(hud_data, dict):
            hud_data = {
                'Protagonist': {
                    'actual_truth': {
                        'name': '투자자',
                        'capital': '0원',
                        'total_assets': '0원',
                        'stocks': '없음',
                        'companies': '없음',
                        'real_estate': '없음',
                        'reputation': '무명',
                        'connections': '평범',
                        'market_insight': '초보',
                        'status': '정상',
                        'current_objective': '재산 증식'
                    }
                }
            }
            bible['FinanceHUD'] = hud_data
        
        return hud_data.get('Protagonist', hud_data)
    
    @property
    def pro_data(self):
        return self.pro_root.get('actual_truth', self.pro_root)
    
    def get_critical_keys(self):
        """투자물 필수 추적 키"""
        return ['capital', 'total_assets', 'stocks', 'reputation', 'connections', 'market_insight', 'status']
    
    def get_v20_hud_report(self):
        """투자 HUD 보고서"""
        return f"""
[💼 FINANCE STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get('name', '투자자')}
💰 Capital: {self._get_normalized_val('capital', '0원')}
📊 Total Assets: {self._get_normalized_val('total_assets', '0원')}
📈 Stocks: {self._get_normalized_val('stocks', '없음')}

🏢 Companies: {self._get_normalized_val('companies', '없음')}
🏠 Real Estate: {self._get_normalized_val('real_estate', '없음')}
🤝 Connections: {self._get_normalized_val('connections', '평범')}
🧠 Market Insight: {self._get_normalized_val('market_insight', '초보')}

🎯 Investment Goal: {self._get_normalized_val('current_objective', '재산 증식')}
⚡ Status: {self._get_normalized_val('status', '정상')}
🏆 Position: {self._get_normalized_val('position', '개인투자자')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def update_physical_status(self, full_state_data):
        """[V40.1 Fix] 투자 상태 업데이트 - MartialManager 패턴 적용"""
        if not full_state_data:
            return []

        # [V40.1] setdefault로 안전한 경로 보장
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        pro = bible.setdefault('FinanceHUD', {}).setdefault('Protagonist', {})
        actual = pro.setdefault('actual_truth', {})
        actual_in = full_state_data.get('actual_truth', full_state_data)

        changes = []
        for canonical_key, fallback_keys in self.canonical_map.items():
            val = None
            for incoming_key in fallback_keys:
                if incoming_key in actual_in:
                    val = actual_in[incoming_key]
                    break

            if val is not None:
                old_val = actual.get(canonical_key, "기록 없음")
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    changes.append(f"{canonical_key}: {old_val} → {val}")

        # [V40.1] 변경사항 있을 때 Bible 저장
        if changes:
            self.context.save_v20_anchor("bible", self.context.master_bible)

        return changes


def create_hud_manager(genre_type, context):
    """
    [V40 Factory] 장르별 HUD 매니저 생성 팩토리 함수
    
    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment'
        context: ProjectManager 인스턴스
    
    Returns:
        GenreHUDManager 구현체
    """
    from .martial_manager import MartialManager
    
    if genre_type == 'wuxia':
        return MartialManager(context)
    elif genre_type == 'hunter':
        return HunterHUDManager(context)
    elif genre_type == 'investment':
        return FinanceHUDManager(context)
    else:
        raise ValueError(f"Unknown genre type: {genre_type}")


def validate_hud_compatibility(hud_manager, required_attrs: list = None) -> dict:
    """
    [V61.3] HUD 호환성 검증 - 필수 속성 존재 여부 체크

    Args:
        hud_manager: GenreHUDManager 인스턴스
        required_attrs: 체크할 속성 목록 (기본: Stage 4에서 사용하는 속성들)

    Returns:
        {
            "valid": bool,
            "genre": str,
            "missing": [str],  # 누락된 속성
            "warnings": [str]
        }
    """
    if required_attrs is None:
        # Stage 4에서 사용하는 주요 속성들
        required_attrs = [
            ("pro_root", "property"),
            ("pro_data", "property"),
            ("get_v20_hud_report", "method"),
            ("get_critical_keys", "method"),
            ("update_physical_status", "method"),
        ]

    # 선택적 속성 (무협에만 있음)
    optional_attrs = [
        ("inventory", "property"),
        ("techniques", "property"),
        ("snapshot", "method"),
        ("bulk_update", "method"),
    ]

    result = {
        "valid": True,
        "genre": type(hud_manager).__name__,
        "missing": [],
        "optional_missing": [],
        "warnings": []
    }

    # 필수 속성 체크
    for attr_name, attr_type in required_attrs:
        if not hasattr(hud_manager, attr_name):
            result["missing"].append(f"{attr_name} ({attr_type})")
            result["valid"] = False

    # 선택적 속성 체크 (경고만)
    for attr_name, attr_type in optional_attrs:
        if not hasattr(hud_manager, attr_name):
            result["optional_missing"].append(f"{attr_name} ({attr_type})")
            result["warnings"].append(
                f"'{attr_name}' 속성 없음 - 무협 전용 기능, 다른 장르에서는 hasattr 체크 필요"
            )

    return result


def log_hud_compatibility_report(hud_manager, logger=None):
    """
    [V61.3] HUD 호환성 보고서 출력

    Args:
        hud_manager: GenreHUDManager 인스턴스
        logger: 로거 함수 (기본: print)
    """
    if logger is None:
        logger = print

    report = validate_hud_compatibility(hud_manager)

    logger(f"   🔍 [V61.3] HUD 호환성 체크: {report['genre']}")

    if report["valid"]:
        logger(f"      ✅ 필수 속성 모두 존재")
    else:
        logger(f"      ❌ 누락된 필수 속성: {', '.join(report['missing'])}")

    if report["optional_missing"]:
        logger(f"      ⚠️ 선택적 속성 누락 (정상): {', '.join(report['optional_missing'])}")
