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

from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.core.constants import Stage2Limits

logger = logging.getLogger(__name__)


# ── ARC_STATE_SCHEMA 대응 ──────────────────────────────────────────


class ArcState(BaseModel):
    """Arc 시작/종료 상태 (response_schemas.py ARC_STATE_SCHEMA 대응)

    *** SSOT 계약 ***
    이 모델의 필드들이 주인공 물리적 상태의 Single Source of Truth.
    - injuries: 공식 부상 상태. StatusShadow.expected_injuries(예측값)와 혼용 금지.
    - location: 공식 위치. joint_docs.final_location과 동기화 후 여기가 SSOT.
    - internal_energy: 공식 내공 수치 (0-100).

    소비 코드: arc_end_state["injuries"] 사용. StatusShadow 폴백 금지.
    """

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
    """Arc 상태 그림자 — PREDICTION ONLY (LLM 서사 추론, SSOT 아님)

    *** 경고: 모든 필드는 예측값. ground truth 사용 금지. ***
    - expected_injuries: LLM이 서사 흐름에서 추론한 부상 예측.
      arc_end_state.injuries(SSOT) 대신 사용 절대 금지.
      허용: LLM 프롬프트에 '[참고]' 레이블로만 제공.
    - internal_energy_loss: 내공 소모 예측 (e.g. "30%").
      arc_end_state.internal_energy(SSOT) 대신 사용 절대 금지.

    SSOT는 반드시 StateConstraints.arc_end_state를 통해 읽을 것.
    """

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


class StateChangesDict(TypedDict, total=False):
    """state_changes 최상위 계약 TypedDict.

    persisted replay authority: Stage4PostPassRuntime -> episode_bibles.state_changes
    tracker normalization helper: StateTracker.extract_all_state_changes()
    primary consumers: WorldStateManager, FactLedger

    이 TypedDict는 최상위 키 계약만 정의합니다.
    각 키의 내부 엔트리 구조는 이 웨이브에서 정형화하지 않습니다.
    total=False — 모든 키 선택적 (런타임 .get() 폴백과 호환).
    """

    npc_deaths: list[dict[str, Any] | str]
    skill_acquisitions: list[dict[str, Any] | str]
    relationship_changes: list[dict[str, Any] | str]
    major_items: list[dict[str, Any]]
    resolved_plots: list[dict[str, Any] | str]
    npc_injuries: list[dict[str, Any] | str]
    npc_movements: list[dict[str, Any] | str]
    npc_martial_state_changes: list[dict[str, Any]]
    financial_events: dict[str, Any]
    entity_destructions: list[dict[str, Any] | str]
    npc_personality_changes: list[dict[str, Any] | str]
    npc_npc_relationships: list[dict[str, Any] | str]
    time_markers: list[dict[str, Any] | str]
    permanent_injuries: list[dict[str, Any] | str]
    companion_changes: list[dict[str, Any] | str]
    commitments: list[dict[str, Any] | str]
    protagonist_emotion: dict[str, Any]


class StateChanges(BaseModel):
    """V61 구조화된 상태 변화 추적 — limited legacy compat shell.

    NOTE: 이 Pydantic 모델은 4개 필드만 커버하는 제한적 호환 셸입니다.
    canonical SSOT는 위의 StateChangesDict TypedDict를 사용하세요."""

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
    ep_count: int = Stage2Limits.DEFAULT_EP_COUNT
    volume_no: int = 0
    global_arc_no: int = 0  # project_manager 별칭
    title: str = ""
    tactical_doc: str | dict = ""
    beat_sequence: list | str = Field(default_factory=list)
    state_constraints: dict = Field(default_factory=dict)
    joint_docs: dict = Field(default_factory=dict)
    status_shadow: dict = Field(default_factory=dict)
    constraint_summary: str = ""
    state_changes: StateChangesDict = Field(default_factory=dict)
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

    @model_validator(mode="after")
    def _enforce_arc_ssot_contracts(self) -> ArcData:
        """[TF-12 Layer1] arc_end_state SSOT 계약 강제 (ingress 정규화)

        규칙:
        1. arc_end_state.injuries: falsy → "없음"  (StatusShadow fallback 차단)
        2. arc_end_state.location: 빈값 + joint_docs.final_location 있음 → 동기화
           (fill-if-missing only. 기존값 override 금지)

        Note: _sync_final_location()과 이중 안전장치 구성.
        이 validator는 Pydantic ingress에서 fill-if-missing,
        _sync_final_location()은 생성 파이프라인에서 항상-override.
        """
        sc = self.state_constraints
        if not isinstance(sc, dict):
            return self

        arc_end = sc.get("arc_end_state")
        if not isinstance(arc_end, dict):
            return self

        # 규칙 1: injuries SSOT 강제
        if not arc_end.get("injuries"):
            arc_end["injuries"] = "없음"

        # 규칙 2: location fill-if-missing
        if not arc_end.get("location"):
            jd = self.joint_docs
            if isinstance(jd, dict):
                final_loc = jd.get("final_location", "")
                if final_loc:
                    arc_end["location"] = final_loc

        sc["arc_end_state"] = arc_end
        return self


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
