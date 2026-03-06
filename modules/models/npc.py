"""
[Step 2] NPC 엔트리 Pydantic v2 모델

참조:
- state_tracker.py create_npc_entry()
- OPUS_TF_BLUEPRINT_step2_pydantic.md §2-D

NOTE: EpisodeState(@dataclass)는 전환 대상 아님. NPC 엔트리(bare dict)만 모델화.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class NPCEntry(BaseModel):
    """NPC 레지스트리 엔트리

    extra="allow" — PresetRegistry 기반 동적 필드 수용
    """

    model_config = ConfigDict(extra="allow")

    name: str
    status: str = "alive"
    deceased: bool = False  # [대원칙4] status=="dead" 체크와 병행 (truth_gate 기준)
    weapon: str = ""
    level: str = ""
    death_arc: int | None = None
    last_arc: int = 0


def validate_npc_entry(raw: dict) -> dict:
    """NPC 엔트리 dict 검증 → dict 반환 (graceful degradation)"""
    try:
        npc = NPCEntry.model_validate(raw)
        return npc.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] NPCEntry 검증 실패 — 원본 유지: %s", e)
        return raw
