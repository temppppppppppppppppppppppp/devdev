"""
[Step 2] Blueprint 데이터 Pydantic v2 모델

참조:
- response_schemas.py BLUEPRINT_SCHEMA (L363-388)
- OPUS_TF_BLUEPRINT_step2_pydantic.md §2-B
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class BlueprintRelationshipChange(BaseModel):
    """Blueprint 내 관계 변화 항목"""

    model_config = ConfigDict(extra="allow")

    target: str = ""
    from_state: str = ""
    to_state: str = ""
    justification: str = ""


class Blueprint(BaseModel):
    """Blueprint 데이터 (response_schemas.py BLUEPRINT_SCHEMA 대응)

    extra="allow" — LLM이 생성하는 미정의 키 안전 수용
    """

    model_config = ConfigDict(extra="allow")

    # ── Schema 정의 필드 ──
    episode_number: int = 0
    scene_breakdown: dict = Field(default_factory=dict)
    integrated_scenario: str = ""
    pacing_notes: str = ""
    target_beat: str = ""
    relationship_changes: list[dict] = Field(default_factory=list)
    time_flow: str = ""

    # ── Blueprint doc §2-B 추가 필드 ──
    protagonist_state: dict = Field(default_factory=dict)
    start_location: str = ""
    location: str = ""  # start_location 별칭
    core_tension: str = ""
    expected_ending: str = ""


def validate_blueprint(raw: dict) -> dict:
    """Blueprint dict를 검증하고 다시 dict로 반환

    검증 실패 시 원본 dict 그대로 반환 (graceful degradation)
    """
    try:
        bp = Blueprint.model_validate(raw)
        return bp.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] Blueprint 검증 실패 — 원본 dict 유지: %s", e)
        return raw
