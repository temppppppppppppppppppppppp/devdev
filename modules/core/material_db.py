"""
[V43] 장르별 소재 데이터베이스
- 무협/헌터/투자 장르별 소재 풀 분리
- laws/{genre}.json의 seed pools와 연동 가능
"""

import json
import logging
import random
from pathlib import Path


class MaterialDB:
    """[Multi-Genre Material Database] 장르별 기연, 아이템, 기술, 장소 소재."""

    # 장르별 기본 소재 (laws 파일 로드 실패 시 fallback)
    GENRE_MATERIALS = {
        "wuxia": {
            "ITEMS": ["영약", "비급", "신병이기", "영단", "보물"],
            "TECHNIQUES": ["심법", "검법", "장법", "경공", "내공심법"],
            "LOCATIONS": ["동굴", "장경각", "비경", "문파", "객잔"],
            "OBJECTIVES": ["복수", "가문 재건", "무림 통일", "천하제일"],
        },
        "hunter": {
            "ITEMS": ["마정", "마석", "아티팩트", "장비", "스킬북"],
            "TECHNIQUES": ["스킬", "각성 능력", "고유 기술", "패시브"],
            "LOCATIONS": ["게이트", "던전", "길드", "레이드 존", "보스룸"],
            "OBJECTIVES": ["S급 각성", "레이드 클리어", "길드 성장", "세계 최강"],
        },
        "investment": {
            "ITEMS": ["주식", "부동산", "기업", "암호화폐", "예술품"],
            "TECHNIQUES": ["투자 기법", "분석력", "인맥", "정보력"],
            "LOCATIONS": ["증권사", "은행", "기업 본사", "경매장", "거래소"],
            "OBJECTIVES": ["재벌 등극", "기업 인수", "시장 지배", "복수"],
        },
    }

    # 장르별 상세 소재 풀 (확장용)
    DETAILED_POOLS = {
        "wuxia": {
            "HERBS": ["천년설삼", "만년화리", "빙백신주", "대환단", "구전환혼단"],
            "WEAPONS": ["현철검", "중검", "천잠사", "벽력탄", "무영독침"],
            "MANUALS": ["심법 원본", "패도 무공", "회피 보법", "방어 공법"],
            "LOCATIONS": ["절벽 동굴", "지하 장경각", "비경", "수정궁", "설산"],
        },
        "hunter": {
            "CORES": ["E급 마정", "D급 마정", "C급 마정", "B급 마정", "A급 마정", "S급 마정"],
            "EQUIPMENT": ["마법 갑옷", "강화 무기", "회복 포션", "버프 아이템"],
            "SKILLS": ["화염구", "빙결", "번개", "치유", "버서커"],
            "DUNGEONS": ["저급 게이트", "중급 게이트", "고급 게이트", "레이드 게이트"],
        },
        "investment": {
            "STOCKS": ["우량주", "성장주", "배당주", "테마주", "공매도"],
            "ASSETS": ["빌딩", "토지", "아파트", "상가", "공장"],
            "COMPANIES": ["스타트업", "중소기업", "대기업", "재벌그룹"],
            "MARKETS": ["국내 증시", "해외 증시", "선물 시장", "옵션 시장"],
        },
    }

    _loaded_laws = {}

    @classmethod
    def _load_genre_laws(cls, genre: str) -> dict:
        """장르 laws 파일에서 seed pools 로드"""
        if genre in cls._loaded_laws:
            return cls._loaded_laws[genre]

        try:
            laws_path = Path(__file__).parent / "laws" / f"{genre}.json"
            if laws_path.exists():
                with open(laws_path, encoding="utf-8") as f:
                    data = json.load(f)
                    cls._loaded_laws[genre] = data
                    return data
        except Exception as e:
            logging.warning(f"[MaterialDB] laws 로드 실패 ({genre}): {e}")

        return {}

    @classmethod
    def get_materials(cls, genre: str = "wuxia") -> dict:
        """장르별 기본 소재 반환"""
        return cls.GENRE_MATERIALS.get(genre, cls.GENRE_MATERIALS["wuxia"])

    @classmethod
    def get_detailed_pool(cls, genre: str, category: str) -> list:
        """장르별 상세 소재 풀 반환"""
        genre_pool = cls.DETAILED_POOLS.get(genre, {})
        return genre_pool.get(category, [])

    @classmethod
    def get_random_material(cls, genre: str = "wuxia", category: str = "ITEMS") -> str:
        """장르별 랜덤 소재 반환"""
        # 1차: 상세 풀에서 시도
        pool = cls.get_detailed_pool(genre, category)
        if pool:
            return random.choice(pool)

        # 2차: 기본 소재에서 시도
        materials = cls.get_materials(genre)
        if category in materials:
            return random.choice(materials[category])

        # 3차: laws 파일에서 시도
        laws = cls._load_genre_laws(genre)
        if category.lower() + "_pool" in laws:
            pool = laws[category.lower() + "_pool"]
            if pool:
                return random.choice(pool)

        return f"[{category} 소재]"

    @classmethod
    def get_objectives(cls, genre: str = "wuxia") -> list:
        """장르별 목표 리스트 반환"""
        materials = cls.get_materials(genre)
        return materials.get("OBJECTIVES", ["목표 달성"])

    @classmethod
    def get_random_objective(cls, genre: str = "wuxia") -> str:
        """장르별 랜덤 목표 반환"""
        objectives = cls.get_objectives(genre)
        return random.choice(objectives) if objectives else "목표 달성"
