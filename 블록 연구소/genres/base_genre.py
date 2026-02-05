"""
BaseGenre - 장르 베이스 클래스
==============================
모든 장르가 상속받아 구현해야 하는 인터페이스

새 장르 추가 방법:
1. genres/{genre_name}/ 폴더 생성
2. __init__.py에 {Genre}Genre 클래스 정의 (BaseGenre 상속)
3. 필수 메서드 구현
4. genres/__init__.py에 등록
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseGenre(ABC):
    """장르 베이스 클래스"""

    # 장르 기본 정보 (서브클래스에서 오버라이드)
    GENRE_ID: str = "base"
    GENRE_NAME: str = "베이스"
    GENRE_DESC: str = "장르 설명"

    # HUD 타입
    HUD_TYPE: str = "BaseHUD"

    # 아키타입 목록
    ARCHETYPES: List[str] = []

    # 일반적인 배경 설정
    TYPICAL_SETTINGS: List[str] = []

    def __init__(self):
        self.advisor = None

    # ===========================================
    # 필수 구현 메서드
    # ===========================================

    @abstractmethod
    def get_advisor(self, start_era: str):
        """장르별 전략 어드바이저 반환"""
        pass

    @abstractmethod
    def get_historical_events(self, start_era: str) -> List[Dict]:
        """시대별 활용 가능한 이벤트 반환"""
        pass

    @abstractmethod
    def get_real_figures(self) -> Dict[str, List[Dict]]:
        """실존 인물 데이터베이스 반환"""
        pass

    @abstractmethod
    def get_figure_appearance_guide(self) -> Dict[str, Dict]:
        """인물 등장 타이밍 가이드 반환"""
        pass

    @abstractmethod
    def get_romance_rules(self) -> Dict:
        """로맨스 규칙 반환"""
        pass

    @abstractmethod
    def get_genre_rules(self) -> Dict:
        """장르 규칙 (필수/금지/긴장장치) 반환"""
        pass

    @abstractmethod
    def build_initial_hud(self, protagonist_info: Dict) -> Dict:
        """초기 HUD 구조 생성"""
        pass

    @abstractmethod
    def get_npc_roles(self) -> List[Dict]:
        """필수 NPC 역할 목록"""
        pass

    @abstractmethod
    def get_power_progression_template(self) -> Dict:
        """성장 곡선 템플릿"""
        pass

    # ===========================================
    # 공통 메서드 (오버라이드 가능)
    # ===========================================

    def get_bible_schema(self) -> Dict:
        """Bible 스키마 템플릿"""
        return {
            "_schema_version": "2.0",
            "_genre": self.GENRE_ID,
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {},
                    "CoreIdentity": {},
                    "CommercialCode": {}
                },
                "protagonist_config": {},
                self.HUD_TYPE: {},
                "WorldState": {},
                "AssetLibrary": {
                    "KeyNPCs": [],
                    "KeyItems": [],
                    "KeyLocations": [],
                    "Persona": "",
                    "SpeechStyle": {}
                },
                "Seeds": [],
                "GenreRules": self.get_genre_rules()
            }
        }

    def get_treatment_schema(self) -> Dict:
        """Treatment 스키마 템플릿"""
        return {
            "_schema_version": "2.0",
            "_genre": self.GENRE_ID,
            "work_name": "",
            "total_blocks": 60,
            "treatments": []
        }

    def get_block_schema(self) -> Dict:
        """블록 스키마 템플릿"""
        return {
            "block_id": "",
            "title": "",
            "content": {
                "context": "",
                "event_villain": "",
                "solution": "",
                "reward": ""
            },
            "stakes": "",
            "power_shift": {
                "protagonist": "",
                "antagonist": ""
            },
            "relationship_delta": [],
            "tension_level": 5,
            "location": "",
            "time_span": {},
            "genre_ext": {}  # 장르별 확장 필드
        }

    def validate_bible(self, bible: Dict) -> List[str]:
        """Bible 유효성 검사 - 오류 메시지 리스트 반환"""
        errors = []

        if not bible.get("MasterBible"):
            errors.append("MasterBible 섹션 누락")

        mb = bible.get("MasterBible", {})

        if not mb.get("ProjectData", {}).get("MetaInfo", {}).get("title"):
            errors.append("작품 제목 누락")

        if not mb.get("AssetLibrary", {}).get("KeyNPCs"):
            errors.append("NPC 목록 누락")

        return errors

    def validate_treatment(self, treatment: Dict) -> List[str]:
        """Treatment 유효성 검사"""
        errors = []

        blocks = treatment.get("treatments", [])
        if len(blocks) < 10:
            errors.append(f"블록 수 부족: {len(blocks)}개 (최소 10개)")

        for i, block in enumerate(blocks):
            if not block.get("content"):
                errors.append(f"Block {i+1}: content 누락")

        return errors

    def get_genre_info(self) -> Dict:
        """장르 정보 반환"""
        return {
            "id": self.GENRE_ID,
            "name": self.GENRE_NAME,
            "desc": self.GENRE_DESC,
            "hud_type": self.HUD_TYPE,
            "archetypes": self.ARCHETYPES,
            "typical_settings": self.TYPICAL_SETTINGS
        }
