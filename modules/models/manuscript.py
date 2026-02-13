"""
[Step 2] 원고 후보 Pydantic v2 모델

참조:
- chief_writer.py generate_ensemble() 반환값
- OPUS_TF_BLUEPRINT_step2_pydantic.md §2-C
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ManuscriptCandidate(BaseModel):
    """원고 후보 (chief_writer.generate_ensemble() 반환 항목)"""

    model_config = ConfigDict(extra="allow")

    strategy: str = ""
    strategy_name: str = ""
    manuscript: str = ""
    title: str = ""
    state_updates: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    error: bool = False
    error_message: str = ""


class SelfCritiqueResult(BaseModel):
    """Self-Critique 결과"""

    model_config = ConfigDict(extra="allow")

    has_issues: bool = False
    issues: list[str] = Field(default_factory=list)
    severity: str = ""


def validate_manuscript_candidate(raw: dict) -> dict:
    """원고 후보 dict 검증 → dict 반환 (graceful degradation)"""
    try:
        mc = ManuscriptCandidate.model_validate(raw)
        return mc.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] ManuscriptCandidate 검증 실패 — 원본 유지: %s", e)
        return raw
