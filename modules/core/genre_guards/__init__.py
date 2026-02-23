"""
[V40 Multi-Genre] 장르별 Purism Guard 시스템
각 장르에 맞는 금기어 검증 및 순혈성 보존
"""

import logging

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


def create_genre_guard(genre_type, work_guard_path=None, style_guide=None):
    """
    [V40 Factory] 장르별 Guard 생성 팩토리 함수

    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment' | 'fantasy' | 'composer' | 'cooking' | 'alt_history' | 'actor' | 'sports' | 'medical'
        work_guard_path: (optional) work_guard.yaml 경로 → WorkGuard로 래핑
        style_guide: (optional) StyleGuide 인스턴스 → StyleGuard로 래핑

    Returns:
        GenreGuard 구현체 (체인: GenreGuard → WorkGuard → StyleGuard)
    """
    # [TF7-P2-03] 1단계: base guard 생성
    if genre_type == "wuxia":
        guard = WuxiaGuard()
    elif genre_type == "hunter":
        guard = HunterGuard()
    elif genre_type == "investment":
        guard = InvestmentGuard()
    elif genre_type == "fantasy":
        # [V66] 판타지 독립 Guard (WuxiaGuard 공유 → 분리)
        guard = FantasyGuard()
    elif genre_type == "composer":
        guard = ComposerGuard()
    elif genre_type == "cooking":
        guard = CookingGuard()
    elif genre_type == "alt_history":
        guard = AltHistoryGuard()
    elif genre_type == "actor":
        guard = ActorGuard()
    elif genre_type == "sports":
        guard = SportsGuard()
    elif genre_type == "medical":
        guard = MedicalGuard()
    else:
        # [ContractR84] 미지원 장르 경고 후 무협 폴백
        logging.warning(f"[GenreGuard] 미지원 장르 '{genre_type}' → WuxiaGuard 폴백")
        guard = WuxiaGuard()

    # [TF7-P2-03] 2단계: WorkGuard 래핑 (work_guard_path 있을 때만)
    if work_guard_path is not None:
        guard = WorkGuard(guard, work_guard_path)

    # [TF7-P2-03] 3단계: StyleGuard 래핑 (style_guide 있을 때만)
    if style_guide is not None:
        guard = StyleGuard(guard, style_guide)

    return guard


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
