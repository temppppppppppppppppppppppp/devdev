"""
[Phase 2] JSON Response Schemas

Gemini API의 response_schema를 사용한 구조화된 출력 강제
JSON 파싱 실패율 90% 감소
"""

import logging
from copy import deepcopy

from google.genai import types

from modules.core.llm_schema import schema_to_dict, to_gemini_schema

# =================================================================
# V0128 Validation Schemas
# =================================================================

BLOCKING_RESULT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "tier": types.Schema(type=types.Type.STRING),
        "passed": types.Schema(type=types.Type.BOOLEAN),
        "failures": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "check": types.Schema(type=types.Type.STRING),
                    "passed": types.Schema(type=types.Type.BOOLEAN),
                    "reason": types.Schema(type=types.Type.STRING),
                    "severity": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "message": types.Schema(type=types.Type.STRING),
        "failure_count": types.Schema(type=types.Type.INTEGER),
    },
    required=["tier", "passed", "failures", "message"],
)


SCORING_RESULT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "tier": types.Schema(type=types.Type.STRING),
        "passed": types.Schema(type=types.Type.BOOLEAN),
        "total_score": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        "max_score": types.Schema(type=types.Type.INTEGER),
        "percentage": types.Schema(type=types.Type.NUMBER),
        "threshold": types.Schema(type=types.Type.INTEGER),
        "breakdown": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "character_consistency": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                    },
                ),
                "emotion_arc": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                    },
                ),
                "dialogue_quality": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                    },
                ),
                "commercial_appeal": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                    },
                ),
                "pattern_diversity": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                    },
                ),
            },
        ),
        "message": types.Schema(type=types.Type.STRING),
    },
    required=["tier", "passed", "total_score", "breakdown"],
)


ADVISORY_RESULT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "tier": types.Schema(type=types.Type.STRING),
        "passed": types.Schema(type=types.Type.BOOLEAN),
        "suggestions": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "type": types.Schema(type=types.Type.STRING),
                    "suggestion": types.Schema(type=types.Type.STRING),
                    "severity": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "message": types.Schema(type=types.Type.STRING),
    },
    required=["tier", "passed", "suggestions"],
)


# =================================================================
# Director Schemas
# =================================================================

DIRECTOR_AUDIT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(type=types.Type.STRING, enum=["PASS", "PASS_WITH_FIX", "REJECT"]),  # [TF-32]
        "score": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        "fix_scope": types.Schema(
            type=types.Type.STRING,
            enum=["inplace", "partial", "full"],
            description="REJECT/PASS_WITH_FIX 시 수정 범위: inplace(국소)/partial(부분)/full(전면)",
        ),  # [TF-23]
        "fix_scope_reasoning": types.Schema(
            type=types.Type.STRING,
            description="fix_scope 판단 근거: 어떤 문제의 조합이 이 수정 범위를 요구하는지 한 문장 (미작성 시 빈 문자열 허용)",
        ),  # [V73][TF-C]
        "error_category": types.Schema(type=types.Type.STRING, enum=["QUALITY_ISSUE", "LOGIC_ERROR"]),
        "diagnostic_report": types.Schema(type=types.Type.STRING),
        "current_beat_achieved": types.Schema(type=types.Type.BOOLEAN),
        "reason": types.Schema(type=types.Type.STRING),
        "feedback": types.Schema(type=types.Type.STRING),
        "consistency_checklist": types.Schema(  # [NC-3] 일관성 체크리스트
            type=types.Type.OBJECT,
            properties={
                "numeric_accuracy": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "arithmetic": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "title_consistency": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "scene_overlap": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "percent_calculation": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "event_ordering": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "space_continuity": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "npc_identity": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "time_progression": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "opening_diversity": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "timeline_arc_consistency": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),  # [NS-4]
                "fiction_term_leak": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),  # [TF-57-A]
                "scene_variety": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),  # [TF-J]
                "pacing_quality": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "dialogue_naturalness": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "pov_discipline": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "emotional_authenticity": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "npc_knowledge_boundary": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "secret_consistency": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
                "identity_consistency": types.Schema(type=types.Type.STRING, enum=["OK", "ISSUE"]),
            },
        ),
    },
    required=["decision", "score", "reason", "fix_scope"],  # [F-3] fix_scope 필수화
)


STRATEGIC_AUDIT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(type=types.Type.STRING, enum=["PASS", "PASS_WITH_FIX", "REJECT"]),  # [TF-32]
        "score": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        "fix_scope": types.Schema(
            type=types.Type.STRING,
            enum=["inplace", "partial", "full"],
            description="REJECT/PASS_WITH_FIX 시 수정 범위: inplace(국소)/partial(부분)/full(전면)",
        ),  # [TF-23]
        "fix_scope_reasoning": types.Schema(
            type=types.Type.STRING,
            description="fix_scope 판단 근거: 어떤 문제의 조합이 이 수정 범위를 요구하는지 한 문장 (미작성 시 빈 문자열 허용)",
        ),  # [V73][TF-C]
        "loop_detected": types.Schema(type=types.Type.BOOLEAN),
        "reason": types.Schema(type=types.Type.STRING),
        "re_slice_instruction": types.Schema(type=types.Type.STRING),
    },
    required=["decision", "score", "loop_detected", "reason", "fix_scope"],  # [F-3] fix_scope 필수화
)


CHARACTER_LOGIC_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(type=types.Type.STRING, enum=["PASS", "REJECT"]),
        "score": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        "violations": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "character": types.Schema(type=types.Type.STRING),
                    "trait": types.Schema(type=types.Type.STRING),
                    "action": types.Schema(type=types.Type.STRING),
                    "reason": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "severity": types.Schema(type=types.Type.STRING, enum=["NONE", "MINOR", "MAJOR", "CRITICAL"]),
        "feedback": types.Schema(type=types.Type.STRING),
    },
    required=["decision", "score", "violations", "severity"],
)


# =================================================================
# [V49.4] Analyst Arc Design Schema
# =================================================================

ARC_STATE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "location": types.Schema(type=types.Type.STRING),
        "equipment": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "injuries": types.Schema(type=types.Type.STRING, enum=["없음", "정상", "경상", "중상", "위독"]),
        "internal_energy": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        # [TF-59] 재무 상태 연속성 (투자물 등 비무협 장르용, optional)
        "capital": types.Schema(type=types.Type.STRING, description="보유 자본금 (예: '5억원', '$1M')"),
        "total_assets": types.Schema(type=types.Type.STRING, description="총 자산 (자본금+투자자산)"),
        "portfolio_position": types.Schema(type=types.Type.STRING, description="현재 포지션 요약 (예: '삼성전자 1000주 보유')"),
    },
    required=["location", "equipment", "injuries", "internal_energy"],
    # capital/total_assets/portfolio_position은 optional — 무협 등은 생략
)

ARC_STATE_CONSTRAINTS_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "arc_start_state": ARC_STATE_SCHEMA,
        "arc_end_state": ARC_STATE_SCHEMA,
        # [V49.6] 아이템 소유권 명확화
        "protagonist_items": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="주인공이 직접 소지하게 되는 아이템만 기록. 타인에게 지급한 것은 제외.",
        ),
        "distributed_items": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="주인공이 구매/획득 후 타인(병사, NPC 등)에게 지급한 아이템",
        ),
        "items_consumed": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="이 Arc에서 소모/사용되어 사라진 아이템 (금전, 소모품 등)",
        ),
        # [F-A] 투자물 수치 검산용 구조화 필드 (optional)
        "investment_calc": types.Schema(
            type=types.Type.OBJECT,
            description="투자물 장르: 에피소드별 투자 거래 명세. Python 검산에 사용.",
            properties={
                "transactions": types.Schema(
                    type=types.Type.ARRAY,
                    description="해당 Arc 내 투자 거래 목록",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "ep_no": types.Schema(type=types.Type.INTEGER, description="에피소드 번호"),
                            "asset": types.Schema(type=types.Type.STRING, description="자산명 (예: 'WTI 원유')"),
                            "action": types.Schema(type=types.Type.STRING, description="매수/매도/청산"),
                            "entry_price": types.Schema(type=types.Type.NUMBER, description="진입가"),
                            "exit_price": types.Schema(type=types.Type.NUMBER, description="청산가 (미청산 시 0)"),
                            "leverage": types.Schema(type=types.Type.NUMBER, description="레버리지 배수 (없으면 1)"),
                            "principal": types.Schema(type=types.Type.NUMBER, description="투자 원금 (원 단위)"),
                            "stated_profit": types.Schema(
                                type=types.Type.NUMBER,
                                description="서술된 수익/손실 (원 단위, 손실은 음수)",
                            ),
                        },
                        required=["ep_no", "asset", "action", "entry_price", "leverage", "principal"],
                    ),
                ),
                "final_cash": types.Schema(type=types.Type.NUMBER, description="Arc 종료 시 현금 (원 단위)"),
                "final_total_assets": types.Schema(type=types.Type.NUMBER, description="Arc 종료 시 총자산 (원 단위)"),
            },
        ),
        # [V49.7] 품질 추적 필드
        "relationship_changes": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "target": types.Schema(type=types.Type.STRING, description="변화 대상 NPC/집단명"),
                    "from": types.Schema(type=types.Type.STRING, description="이전 관계 상태"),
                    "to": types.Schema(type=types.Type.STRING, description="변경 후 상태"),
                    "trigger": types.Schema(type=types.Type.STRING, description="변화 계기"),
                    "justification": types.Schema(type=types.Type.STRING, description="서사적 근거"),
                },
                required=["target", "from", "to", "trigger"],
            ),
            description="이 Arc에서 발생하는 관계 변화 목록",
        ),
        "power_changes": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "start_power": types.Schema(type=types.Type.INTEGER, description="Arc 시작 시 파워 (0-100)"),
                "end_power": types.Schema(type=types.Type.INTEGER, description="Arc 종료 시 파워 (0-100)"),
                "growth_justification": types.Schema(type=types.Type.STRING, description="성장 근거"),
            },
            description="주인공 파워 스케일링 정보",
        ),
        "foreshadowings": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.STRING, description="복선 식별자"),
                    "type": types.Schema(
                        type=types.Type.STRING, description="복선 유형 (아이템/인물/사건/능력/비밀/예언)"
                    ),
                    "description": types.Schema(type=types.Type.STRING, description="복선 내용"),
                    "expected_payoff": types.Schema(type=types.Type.STRING, description="예상 회수 시점/방법"),
                },
                required=["id", "description"],
            ),
            description="이 Arc에서 설치하는 복선 목록",
        ),
        "continuity_checkpoints": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
    },
    required=["arc_start_state", "arc_end_state", "protagonist_items", "items_consumed"],
)

ARC_DESIGN_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "arc_no": types.Schema(type=types.Type.INTEGER),
        "hybrid_composition": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "primary": types.Schema(type=types.Type.STRING),
                "secondary": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                "mixing_logic": types.Schema(type=types.Type.STRING),
            },
            required=["primary", "mixing_logic"],
        ),
        "ep_count": types.Schema(type=types.Type.INTEGER, minimum=2, maximum=6),
        "ep_start": types.Schema(type=types.Type.INTEGER),
        "ep_end": types.Schema(type=types.Type.INTEGER),
        "title": types.Schema(type=types.Type.STRING),
        "beat_sequence": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "state_constraints": ARC_STATE_CONSTRAINTS_SCHEMA,
        "tactical_doc": types.Schema(type=types.Type.STRING),
        "joint_docs": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "final_location": types.Schema(type=types.Type.STRING),
                "physical_inventory": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                "world_joint": types.Schema(type=types.Type.STRING),
            },
            required=["final_location", "physical_inventory", "world_joint"],
        ),
        "status_shadow": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "key_stat_change": types.Schema(type=types.Type.STRING, description="핵심 수치 변동"),
                "expected_injuries": types.Schema(type=types.Type.STRING),
                "item_consumption": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            },
        ),
        # state_changes — 선택 필드 (LLM이 반환 안 하면 Python fallback)
        "state_changes": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "timeline": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "start": types.Schema(
                            type=types.Type.OBJECT,
                            description="Arc 시작 시점",
                            properties={
                                "year": types.Schema(type=types.Type.INTEGER),
                                "month": types.Schema(type=types.Type.INTEGER),
                                "day": types.Schema(type=types.Type.INTEGER),
                                "description": types.Schema(type=types.Type.STRING),
                            },
                        ),
                        "end": types.Schema(
                            type=types.Type.OBJECT,
                            description="Arc 종료 시점",
                            properties={
                                "year": types.Schema(type=types.Type.INTEGER),
                                "month": types.Schema(type=types.Type.INTEGER),
                                "day": types.Schema(type=types.Type.INTEGER),
                                "description": types.Schema(type=types.Type.STRING),
                            },
                        ),
                    },
                ),
                "relationship_changes": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "npc": types.Schema(type=types.Type.STRING),
                            "from": types.Schema(type=types.Type.STRING),
                            "to": types.Schema(type=types.Type.STRING),
                            "episode": types.Schema(type=types.Type.INTEGER),
                        },
                        required=["npc", "from", "to"],
                    ),
                ),
                "major_items": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "episode": types.Schema(type=types.Type.INTEGER),
                            "action": types.Schema(type=types.Type.STRING),
                        },
                        required=["name", "action"],
                    ),
                ),
                "npc_deaths": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "episode": types.Schema(type=types.Type.INTEGER),
                            "cause": types.Schema(type=types.Type.STRING),
                        },
                        required=["name"],
                    ),
                ),
                "skill_acquisitions": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "episode": types.Schema(type=types.Type.INTEGER),
                            "source": types.Schema(type=types.Type.STRING),
                        },
                        required=["name"],
                    ),
                ),
                "npc_introductions": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "episode": types.Schema(type=types.Type.INTEGER),
                        },
                        required=["name"],
                    ),
                ),
            },
        ),
        # [TF10-1-2] 화별 사건 인덱스 (선택 필드 — required에 추가하지 않음)
        "episode_details": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ep_num": types.Schema(type=types.Type.INTEGER),
                    "details": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                },
                required=["ep_num", "details"],
            ),
        ),
    },
    required=["arc_no", "ep_count", "ep_start", "ep_end", "title", "beat_sequence", "tactical_doc"],
)


# =================================================================
# Writer & Architect Schemas
# =================================================================

# =================================================================
# [TF-49b] Blueprint Preflight Validation Schema
# =================================================================

BLUEPRINT_PREFLIGHT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "passed": types.Schema(type=types.Type.BOOLEAN),
        "issues": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(type=types.Type.STRING),
                    "description": types.Schema(type=types.Type.STRING),
                    "severity": types.Schema(type=types.Type.STRING),
                },
                required=["category", "description", "severity"],
            ),
        ),
        "summary": types.Schema(type=types.Type.STRING),
    },
    required=["passed", "issues", "summary"],
)


BLUEPRINT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "episode_number": types.Schema(type=types.Type.INTEGER),
        "scene_breakdown": types.Schema(type=types.Type.OBJECT),
        "integrated_scenario": types.Schema(type=types.Type.STRING),
        "pacing_notes": types.Schema(type=types.Type.STRING),
        "target_beat": types.Schema(type=types.Type.STRING),
        # [V49.5] 관계 변화 추적
        "relationship_changes": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "target": types.Schema(type=types.Type.STRING),  # 대상 (NPC/집단)
                    "from_state": types.Schema(type=types.Type.STRING),  # 이전 관계
                    "to_state": types.Schema(type=types.Type.STRING),  # 변화 후 관계
                    "justification": types.Schema(type=types.Type.STRING),  # 변화 근거
                },
            ),
        ),
        # [V49.5] 시간 흐름
        "time_flow": types.Schema(type=types.Type.STRING),  # 예: "같은 날 밤", "3일 후"
        "core_tension": types.Schema(type=types.Type.STRING),
        "expected_ending": types.Schema(type=types.Type.STRING),
    },
    required=["episode_number", "scene_breakdown", "integrated_scenario"],
)


MANUSCRIPT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "content": types.Schema(type=types.Type.STRING),
        "word_count": types.Schema(type=types.Type.INTEGER),
        "state_updates": types.Schema(type=types.Type.OBJECT),
        "character_status": types.Schema(type=types.Type.STRING),
    },
    required=["content"],
)


_TASK_SCHEMA_CONSTANTS = {
    "BLOCKING": BLOCKING_RESULT_SCHEMA,
    "SCORING": SCORING_RESULT_SCHEMA,
    "ADVISORY": ADVISORY_RESULT_SCHEMA,
    "DIRECTOR_AUDIT": DIRECTOR_AUDIT_SCHEMA,
    "STRATEGIC_AUDIT": STRATEGIC_AUDIT_SCHEMA,
    "CHARACTER_LOGIC": CHARACTER_LOGIC_SCHEMA,
    "BLUEPRINT": BLUEPRINT_SCHEMA,
    "MANUSCRIPT": MANUSCRIPT_SCHEMA,
    "ARC_DESIGN": ARC_DESIGN_SCHEMA,
    "BLUEPRINT_PREFLIGHT": BLUEPRINT_PREFLIGHT_SCHEMA,
}
_TASK_SCHEMA_SPECS = {name: schema_to_dict(schema) for name, schema in _TASK_SCHEMA_CONSTANTS.items()}


# =================================================================
# Utility Functions
# =================================================================


def get_schema_for_task(task_type: str) -> types.Schema:
    """
    작업 유형에 맞는 스키마 반환

    Args:
        task_type: "BLOCKING" | "SCORING" | "ADVISORY" | "DIRECTOR_AUDIT" |
                   "STRATEGIC_AUDIT" | "CHARACTER_LOGIC" | "BLUEPRINT" | "MANUSCRIPT"

    Returns:
        types.Schema instance or None
    """
    spec = get_schema_spec_for_task(task_type)
    return to_gemini_schema(spec) if spec else None


def get_schema_spec_for_task(task_type: str) -> dict | None:
    """작업 유형에 맞는 provider-neutral dict schema 반환."""

    spec = _TASK_SCHEMA_SPECS.get(task_type)
    return deepcopy(spec) if spec else None


def validate_response_against_schema(response: dict, schema: types.Schema | dict) -> bool:
    """
    응답이 스키마를 만족하는지 기본 검증

    ⚠️ 주의: 이 함수는 간단한 구조 검증만 수행합니다.
    실제 타입 검증과 값 제약은 Gemini API의 response_schema 파라미터가 보장합니다.

    이 함수의 용도:
    - Gemini API 응답이 예상 구조인지 빠르게 확인
    - 디버깅 및 로깅 목적

    Args:
        response: API 응답 dict
        schema: Schema 객체

    Returns:
        True if basic structure is valid, False otherwise
    """
    if not isinstance(response, dict):
        logging.warning(f"[WARNING] Response is not a dict: {type(response)}")
        return False

    # [V70] required 필드만 체크 (optional 필드는 누락 허용)
    if isinstance(schema, dict):
        required_props = schema.get("required")
    else:
        required_props = getattr(schema, "required", None)
    if required_props:
        missing = [p for p in required_props if p not in response]
        if missing:
            logging.warning(f"[WARNING] Missing required fields: {missing}")
            return False

    return True


# =================================================================
# Schema Usage Examples
# =================================================================

# =================================================================
# [V49.3] Stage 0 (Phase 0) Input Validation Schemas
# =================================================================

# Bible 파일 필수 구조 정의 (Python dict 형태로 validation)
BIBLE_REQUIRED_STRUCTURE = {
    "MasterBible": {
        "required_fields": ["ProjectData"],
        "optional_fields": ["plot_roadmap", "world_setting", "character_profiles"],
    },
    "ProjectData": {"required_fields": ["MetaInfo"], "optional_fields": ["WorldRules", "CharacterArcs"]},
    "MetaInfo": {"required_fields": ["title"], "optional_fields": ["author", "genre", "synopsis", "total_episodes"]},
}

# Treatment 파일 필수 구조 정의 (배열 항목별)
TREATMENT_BLOCK_REQUIRED_FIELDS = ["title"]
TREATMENT_BLOCK_OPTIONAL_FIELDS = ["content", "summary", "beats", "arc_number"]
TREATMENT_CONTENT_FIELDS = ["context", "event_villain", "solution", "reward"]  # content 내부 필드 (V62.2)


def validate_bible_structure(bible_data: dict) -> tuple:
    """
    [V49.3] Bible 파일 구조 검증

    Args:
        bible_data: 로드된 Bible JSON 데이터

    Returns:
        tuple: (is_valid: bool, errors: list, warnings: list)
    """
    errors = []
    warnings = []

    if not isinstance(bible_data, dict):
        return False, ["Bible 데이터가 dict 형식이 아닙니다"], []

    # MasterBible 래퍼 확인
    master_bible = bible_data.get("MasterBible", bible_data)
    if "MasterBible" not in bible_data:
        warnings.append("MasterBible 래퍼가 없습니다. 루트를 MasterBible로 간주합니다.")

    # ProjectData 확인
    project_data = master_bible.get("ProjectData")
    if not project_data:
        errors.append("ProjectData 필드가 누락되었습니다")
    elif not isinstance(project_data, dict):
        errors.append("ProjectData가 dict 형식이 아닙니다")
    else:
        # MetaInfo 확인
        meta_info = project_data.get("MetaInfo")
        if not meta_info:
            errors.append("ProjectData.MetaInfo 필드가 누락되었습니다")
        elif not isinstance(meta_info, dict):
            errors.append("MetaInfo가 dict 형식이 아닙니다")
        else:
            if "title" not in meta_info:
                errors.append("MetaInfo.title 필드가 누락되었습니다")

    # plot_roadmap 확인 (선택적이지만 있으면 검증)
    if "plot_roadmap" in master_bible:
        roadmap = master_bible["plot_roadmap"]
        if not isinstance(roadmap, list):
            errors.append("plot_roadmap이 list 형식이 아닙니다")
        elif len(roadmap) == 0:
            warnings.append("plot_roadmap이 비어있습니다")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_treatment_structure(treatment_data: list) -> tuple:
    """
    [V49.3] Treatment 파일 구조 검증

    Args:
        treatment_data: 로드된 Treatment JSON 데이터 (배열)

    Returns:
        tuple: (is_valid: bool, errors: list, warnings: list)
    """
    errors = []
    warnings = []

    if not isinstance(treatment_data, list):
        return False, ["Treatment 데이터가 list 형식이 아닙니다"], []

    if len(treatment_data) == 0:
        return False, ["Treatment 데이터가 비어있습니다"], []

    # 각 블록 검증
    for i, block in enumerate(treatment_data):
        block_idx = i + 1

        if not isinstance(block, dict):
            errors.append(f"블록 {block_idx}: dict 형식이 아닙니다")
            continue

        # 필수 필드 확인
        if "title" not in block:
            errors.append(f"블록 {block_idx}: title 필드 누락")

        # content 구조 확인 (선택적)
        if "content" in block:
            content = block["content"]
            if isinstance(content, dict):
                for field in TREATMENT_CONTENT_FIELDS:
                    if field not in content:
                        warnings.append(f"블록 {block_idx}: content.{field} 필드 누락")
            elif not isinstance(content, str):
                warnings.append(f"블록 {block_idx}: content가 dict/str 형식이 아닙니다")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_phase0_files(bible_data: dict, treatment_data: list) -> tuple:
    """
    [V49.3] Phase 0 파일들 통합 검증

    Args:
        bible_data: Bible JSON 데이터
        treatment_data: Treatment JSON 데이터

    Returns:
        tuple: (is_valid: bool, report: dict)
    """
    bible_valid, bible_errors, bible_warnings = validate_bible_structure(bible_data)
    treatment_valid, treatment_errors, treatment_warnings = validate_treatment_structure(treatment_data)

    report = {
        "bible": {"valid": bible_valid, "errors": bible_errors, "warnings": bible_warnings},
        "treatment": {
            "valid": treatment_valid,
            "errors": treatment_errors,
            "warnings": treatment_warnings,
            "block_count": len(treatment_data) if isinstance(treatment_data, list) else 0,
        },
        "overall_valid": bible_valid and treatment_valid,
    }

    return report["overall_valid"], report


"""
사용 예제:

# BaseAgent에서 사용
from modules.core.response_schemas import get_schema_for_task

class Director(BaseAgent):
    def audit_manuscript(self, ...):
        schema = get_schema_for_task("DIRECTOR_AUDIT")

        response = self.ask(
            prompt=audit_prompt,
            temperature=0.1,
            response_schema=schema  # 스키마 강제
        )

        # response는 항상 올바른 구조 보장
        return response

# ScoringValidator에서 사용
class ScoringValidator:
    def _calculate_llm_scores(self, ...):
        schema = get_schema_for_task("SCORING")

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=schema  # 구조화된 출력 강제
            )
        )

        # JSON 파싱 실패 없음
        return json.loads(response.text)
"""
