"""
[V40 Multi-Genre] 장르별 Purism Guard 시스템
각 장르에 맞는 금기어 검증 및 순혈성 보존
"""

from .wuxia_guard import WuxiaGuard
from .hunter_guard import HunterGuard
from .investment_guard import InvestmentGuard
from .composer_guard import ComposerGuard
from .cooking_guard import CookingGuard
from .alt_history_guard import AltHistoryGuard
from .actor_guard import ActorGuard
from .sports_guard import SportsGuard
from .medical_guard import MedicalGuard

def create_genre_guard(genre_type):
    """
    [V40 Factory] 장르별 Guard 생성 팩토리 함수

    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment' | 'composer' | 'cooking' | 'alt_history' | 'actor' | 'sports' | 'medical'

    Returns:
        GenreGuard 구현체
    """
    if genre_type == 'wuxia':
        return WuxiaGuard()
    elif genre_type == 'hunter':
        return HunterGuard()
    elif genre_type == 'investment':
        return InvestmentGuard()
    elif genre_type == 'composer':
        return ComposerGuard()
    elif genre_type == 'cooking':
        return CookingGuard()
    elif genre_type == 'alt_history':
        return AltHistoryGuard()
    elif genre_type == 'actor':
        return ActorGuard()
    elif genre_type == 'sports':
        return SportsGuard()
    elif genre_type == 'medical':
        return MedicalGuard()
    else:
        # 기본값: 무협
        return WuxiaGuard()

__all__ = ['WuxiaGuard', 'HunterGuard', 'InvestmentGuard', 'ComposerGuard', 'CookingGuard', 'AltHistoryGuard', 'ActorGuard', 'SportsGuard', 'MedicalGuard', 'create_genre_guard']
