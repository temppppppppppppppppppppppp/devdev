"""
[V40 Multi-Genre] 장르별 Purism Guard 시스템
각 장르에 맞는 금기어 검증 및 순혈성 보존
"""

from .actor_guard import ActorGuard
from .alt_history_guard import AltHistoryGuard
from .composer_guard import ComposerGuard
from .cooking_guard import CookingGuard
from .fantasy_guard import FantasyGuard  # [V66] 독립 분리
from .hunter_guard import HunterGuard
from .investment_guard import InvestmentGuard
from .medical_guard import MedicalGuard
from .sports_guard import SportsGuard
from .style_guard import StyleGuard
from .work_guard import WorkGuard
from .wuxia_guard import WuxiaGuard


def create_genre_guard(genre_type):
    """
    [V40 Factory] 장르별 Guard 생성 팩토리 함수

    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment' | 'fantasy' | 'composer' | 'cooking' | 'alt_history' | 'actor' | 'sports' | 'medical'

    Returns:
        GenreGuard 구현체
    """
    if genre_type == "wuxia":
        return WuxiaGuard()
    elif genre_type == "hunter":
        return HunterGuard()
    elif genre_type == "investment":
        return InvestmentGuard()
    elif genre_type == "fantasy":
        # [V66] 판타지 독립 Guard (WuxiaGuard 공유 → 분리)
        return FantasyGuard()
    elif genre_type == "composer":
        return ComposerGuard()
    elif genre_type == "cooking":
        return CookingGuard()
    elif genre_type == "alt_history":
        return AltHistoryGuard()
    elif genre_type == "actor":
        return ActorGuard()
    elif genre_type == "sports":
        return SportsGuard()
    elif genre_type == "medical":
        return MedicalGuard()
    else:
        # 기본값: 무협
        return WuxiaGuard()


__all__ = [
    "WuxiaGuard",
    "HunterGuard",
    "InvestmentGuard",
    "FantasyGuard",
    "ComposerGuard",
    "CookingGuard",
    "AltHistoryGuard",
    "ActorGuard",
    "SportsGuard",
    "MedicalGuard",
    "StyleGuard",
    "WorkGuard",
    "create_genre_guard",
]
