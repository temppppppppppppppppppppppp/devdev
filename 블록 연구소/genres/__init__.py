"""
장르 모듈 패키지
================
각 장르별 설정, 어드바이저, 스키마 제공

사용법:
    from genres import get_genre, list_genres

    genre = get_genre("investment")
    advisor = genre.get_advisor(start_era="1996-01")
"""

from pathlib import Path

# 사용 가능한 장르 목록
AVAILABLE_GENRES = {
    "investment": {
        "name": "투자물",
        "desc": "회귀 투자, 재벌물, 금융 스릴러",
        "module": "investment"
    },
    "wuxia": {
        "name": "무협",
        "desc": "정통 무협, 회귀 무협, 현대 무협",
        "module": "wuxia"
    },
    "hunter": {
        "name": "헌터물",
        "desc": "던전물, 헌터 각성, 타워 클라이밍",
        "module": "hunter"
    }
}


def list_genres() -> dict:
    """사용 가능한 장르 목록"""
    return AVAILABLE_GENRES


def get_genre(genre_id: str):
    """장르 모듈 로드"""
    if genre_id not in AVAILABLE_GENRES:
        raise ValueError(f"Unknown genre: {genre_id}. Available: {list(AVAILABLE_GENRES.keys())}")

    if genre_id == "investment":
        from genres.investment import InvestmentGenre
        return InvestmentGenre()
    elif genre_id == "wuxia":
        from genres.wuxia import WuxiaGenre
        return WuxiaGenre()
    elif genre_id == "hunter":
        from genres.hunter import HunterGenre
        return HunterGenre()
    else:
        raise ValueError(f"Genre module not implemented: {genre_id}")
