"""
[V40 Multi-Genre] 장르별 Purism Guard 시스템
각 장르에 맞는 금기어 검증 및 순혈성 보존
"""

from .wuxia_guard import WuxiaGuard
from .hunter_guard import HunterGuard
from .investment_guard import InvestmentGuard

def create_genre_guard(genre_type):
    """
    [V40 Factory] 장르별 Guard 생성 팩토리 함수
    
    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment'
    
    Returns:
        GenreGuard 구현체
    """
    if genre_type == 'wuxia':
        return WuxiaGuard()
    elif genre_type == 'hunter':
        return HunterGuard()
    elif genre_type == 'investment':
        return InvestmentGuard()
    else:
        # 기본값: 무협
        return WuxiaGuard()

__all__ = ['WuxiaGuard', 'HunterGuard', 'InvestmentGuard', 'create_genre_guard']
