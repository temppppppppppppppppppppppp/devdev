"""
[Step 2] Arc 데이터 Pydantic v2 모델

참조:
- response_schemas.py ARC_DESIGN_SCHEMA (L301-356)
- response_schemas.py ARC_STATE_CONSTRAINTS_SCHEMA (L233-299)
- constraint_compiler.py (items_acquired/grants_received 런타임 키)
- OPUS_TF_BLUEPRINT_step2_pydantic.md §2-A
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


# ── ARC_STATE_SCHEMA 대응 ──────────────────────────────────────────


class ArcState(BaseModel):
    """Arc 시작/종료 상태 (response_schemas.py ARC_STATE_SCHEMA 대응)"""

    model_config = ConfigDict(extra="allow")

    location: str = ""
    equipment: list[str] = Field(default_factory=list)
    injuries: str = "정상"
    internal_energy: int = 100


# ── 관계 변화 ──────────────────────────────────────────────────────


class RelationshipChange(BaseModel):
    """Arc 내 관계 변화 항목"""

    model_config = ConfigDict(extra="allow")

    target: str = ""
    # Schema 키: from / to (Python 예약어 from은 alias 사용)
    from_state: str = Field(default="", alias="from")
    to_state: str = Field(default="", alias="to")
    trigger: str = ""
    justification: str = ""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ── 파워 변화 ──────────────────────────────────────────────────────


class PowerChanges(BaseModel):
    """주인공 파워 스케일링"""

    model_config = ConfigDict(extra="allow")

    start_power: int = 0
    end_power: int = 0
    growth_justification: str = ""


# ── 복선 ──────────────────────────────────────────────────────────


class Foreshadowing(BaseModel):
    """복선 항목"""

    model_config = ConfigDict(extra="allow")

    id: str = ""
    type: str = ""
    description: str = ""
    expected_payoff: str = ""


# ── ARC_STATE_CONSTRAINTS_SCHEMA 대응 ─────────────────────────────


class StateConstraints(BaseModel):
    """Arc 상태 제약 (response_schemas.py ARC_STATE_CONSTRAINTS_SCHEMA 대응)

    3계층 키 불일치 흡수:
    - Schema canonical: items_consumed, power_changes
    - 런타임 전용: items_acquired, grants_received (constraint_compiler 사용)
    """

    model_config = ConfigDict(extra="allow")

    arc_start_state: dict = Field(default_factory=dict)
    arc_end_state: dict = Field(default_factory=dict)
    protagonist_items: list[str] = Field(default_factory=list)
    distributed_items: list[str] = Field(default_factory=list)
    items_consumed: list[str] = Field(default_factory=list)
    relationship_changes: list[dict] = Field(default_factory=list)
    power_changes: dict = Field(default_factory=dict)
    foreshadowings: list[dict] = Field(default_factory=list)
    continuity_checkpoints: list[str] = Field(default_factory=list)
    # 런타임 전용 키 (Schema 미정의, constraint_compiler가 사용)
    items_acquired: list | None = None
    grants_received: list | None = None


# ── JointDocs ─────────────────────────────────────────────────────


class JointDocs(BaseModel):
    """Arc 접합 문서"""

    model_config = ConfigDict(extra="allow")

    final_location: str = ""
    physical_inventory: list[str] | str = Field(default_factory=list)
    world_joint: str = ""


# ── StatusShadow ──────────────────────────────────────────────────


class StatusShadow(BaseModel):
    """Arc 상태 그림자 (부상/내공 예측)"""

    model_config = ConfigDict(extra="allow")

    internal_energy_loss: str = ""
    expected_injuries: str = ""
    item_consumption: list[str] = Field(default_factory=list)


# ── HybridComposition ────────────────────────────────────────────


class HybridComposition(BaseModel):
    """Arc 패턴 혼합"""

    model_config = ConfigDict(extra="allow")

    primary: str = ""
    secondary: list[str] = Field(default_factory=list)
    mixing_logic: str = ""


# ── state_changes (V61 구조화) ────────────────────────────────────


class StateChanges(BaseModel):
    """V61 구조화된 상태 변화 추적"""

    model_config = ConfigDict(extra="allow")

    npc_deaths: list[dict] = Field(default_factory=list)
    skill_acquisitions: list[dict] = Field(default_factory=list)
    relationship_changes: list[dict] = Field(default_factory=list)
    major_items: list[dict] = Field(default_factory=list)


# ── ArcData (최상위) ─────────────────────────────────────────────


class ArcData(BaseModel):
    """Arc 데이터 (response_schemas.py ARC_DESIGN_SCHEMA 대응)

    extra="allow" — 예측 불가 키(LLM 생성) 안전 수용
    ingress: ArcData.model_validate(raw_dict)
    egress: arc.model_dump() → dict (기존 소비처 100% 호환)
    """

    model_config = ConfigDict(extra="allow")

    # ── 필수 ──
    arc_no: int
    ep_start: int
    ep_end: int

    # ── 기본값 있는 필드 ──
    ep_count: int = 5
    volume_no: int = 0
    global_arc_no: int = 0  # project_manager 별칭
    title: str = ""
    tactical_doc: str | dict = ""
    beat_sequence: list | str = Field(default_factory=list)
    state_constraints: dict = Field(default_factory=dict)
    joint_docs: dict = Field(default_factory=dict)
    status_shadow: dict = Field(default_factory=dict)
    constraint_summary: str = ""
    state_changes: dict = Field(default_factory=dict)
    hybrid_composition: dict = Field(default_factory=dict)
    seed_injection: list[dict] | None = None
    seeds: list[dict] | None = None
    # [TF10-1-1] 화별 사건 인덱스 — Arc 압축 손실 보완
    # 형식: [{"ep_num": 4, "details": ["사건1", "사건2"]}, ...]
    episode_details: list[dict] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sync_arc_no_alias(cls, data: Any) -> Any:
        """global_arc_no ↔ arc_no 동기화"""
        if isinstance(data, dict):
            if "global_arc_no" in data and "arc_no" not in data:
                data["arc_no"] = data["global_arc_no"]
            elif "arc_no" in data and "global_arc_no" not in data:
                data["global_arc_no"] = data["arc_no"]
        return data


def validate_arc(raw: dict) -> dict:
    """Arc dict를 검증하고 다시 dict로 반환 (ingress+egress 원샷)

    검증 실패 시 원본 dict 그대로 반환 (graceful degradation)
    """
    try:
        arc = ArcData.model_validate(raw)
        return arc.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] Arc 검증 실패 — 원본 dict 유지: %s", e)
        return raw


def validate_blueprint_arc(raw: dict) -> dict:
    """StateConstraints만 검증 (Blueprint 경로에서 Arc 참조 시)"""
    try:
        sc = raw.get("state_constraints")
        if sc and isinstance(sc, dict):
            validated = StateConstraints.model_validate(sc)
            raw["state_constraints"] = validated.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] StateConstraints 검증 실패: %s", e)
    return raw
