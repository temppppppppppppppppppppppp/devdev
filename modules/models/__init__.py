"""
[Step 2] Pydantic v2 데이터 모델

점진적 도입: ingress model_validate() / egress model_dump()
기존 dict 소비 경로 100% 하위호환 유지
"""

from modules.models.arc import ArcData, ArcState, StateConstraints
from modules.models.blueprint import Blueprint
from modules.models.manuscript import ManuscriptCandidate, SelfCritiqueResult
from modules.models.npc import NPCEntry

__all__ = [
    "ArcData",
    "ArcState",
    "StateConstraints",
    "Blueprint",
    "ManuscriptCandidate",
    "SelfCritiqueResult",
    "NPCEntry",
]
