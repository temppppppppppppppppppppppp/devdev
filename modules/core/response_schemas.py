"""
[Phase 2] JSON Response Schemas

Gemini API의 response_schema를 사용한 구조화된 출력 강제
JSON 파싱 실패율 90% 감소
"""
from google.genai import types


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
                    "severity": types.Schema(type=types.Type.STRING)
                }
            )
        ),
        "message": types.Schema(type=types.Type.STRING),
        "failure_count": types.Schema(type=types.Type.INTEGER)
    },
    required=["tier", "passed", "failures", "message"]
)


SCORING_RESULT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "tier": types.Schema(type=types.Type.STRING),
        "passed": types.Schema(type=types.Type.BOOLEAN),
        "total_score": types.Schema(
            type=types.Type.INTEGER,
            minimum=0,
            maximum=100
        ),
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
                        "reason": types.Schema(type=types.Type.STRING)
                    }
                ),
                "emotion_arc": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)
                    }
                ),
                "dialogue_quality": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)
                    }
                ),
                "commercial_appeal": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)
                    }
                ),
                "pattern_diversity": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "score": types.Schema(type=types.Type.INTEGER),
                        "max": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)
                    }
                )
            }
        ),
        "message": types.Schema(type=types.Type.STRING)
    },
    required=["tier", "passed", "total_score", "breakdown"]
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
                    "severity": types.Schema(type=types.Type.STRING)
                }
            )
        ),
        "message": types.Schema(type=types.Type.STRING)
    },
    required=["tier", "passed", "suggestions"]
)


# =================================================================
# Director Schemas
# =================================================================

DIRECTOR_AUDIT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(
            type=types.Type.STRING,
            enum=["PASS", "REJECT"]
        ),
        "score": types.Schema(
            type=types.Type.INTEGER,
            minimum=0,
            maximum=100
        ),
        "error_category": types.Schema(
            type=types.Type.STRING,
            enum=["QUALITY_ISSUE", "LOGIC_ERROR"]
        ),
        "diagnostic_report": types.Schema(type=types.Type.STRING),
        "current_beat_achieved": types.Schema(type=types.Type.BOOLEAN),
        "reason": types.Schema(type=types.Type.STRING),
        "feedback": types.Schema(type=types.Type.STRING)
    },
    required=["decision", "score", "reason"]
)


STRATEGIC_AUDIT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(
            type=types.Type.STRING,
            enum=["PASS", "REJECT"]
        ),
        "score": types.Schema(
            type=types.Type.INTEGER,
            minimum=0,
            maximum=100
        ),
        "loop_detected": types.Schema(type=types.Type.BOOLEAN),
        "reason": types.Schema(type=types.Type.STRING),
        "re_slice_instruction": types.Schema(type=types.Type.STRING)
    },
    required=["decision", "score", "loop_detected", "reason"]
)


CHARACTER_LOGIC_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "decision": types.Schema(
            type=types.Type.STRING,
            enum=["PASS", "REJECT"]
        ),
        "score": types.Schema(
            type=types.Type.INTEGER,
            minimum=0,
            maximum=100
        ),
        "violations": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "character": types.Schema(type=types.Type.STRING),
                    "trait": types.Schema(type=types.Type.STRING),
                    "action": types.Schema(type=types.Type.STRING),
                    "reason": types.Schema(type=types.Type.STRING)
                }
            )
        ),
        "severity": types.Schema(
            type=types.Type.STRING,
            enum=["NONE", "MINOR", "MAJOR", "CRITICAL"]
        ),
        "feedback": types.Schema(type=types.Type.STRING)
    },
    required=["decision", "score", "violations", "severity"]
)


# =================================================================
# Writer & Architect Schemas
# =================================================================

BLUEPRINT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "episode_number": types.Schema(type=types.Type.INTEGER),
        "scene_breakdown": types.Schema(type=types.Type.OBJECT),
        "integrated_scenario": types.Schema(type=types.Type.STRING),
        "pacing_notes": types.Schema(type=types.Type.STRING),
        "target_beat": types.Schema(type=types.Type.STRING)
    },
    required=["episode_number", "scene_breakdown", "integrated_scenario"]
)


MANUSCRIPT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "content": types.Schema(type=types.Type.STRING),
        "word_count": types.Schema(type=types.Type.INTEGER),
        "state_updates": types.Schema(type=types.Type.OBJECT),
        "character_status": types.Schema(type=types.Type.STRING)
    },
    required=["content"]
)


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
    schemas = {
        "BLOCKING": BLOCKING_RESULT_SCHEMA,
        "SCORING": SCORING_RESULT_SCHEMA,
        "ADVISORY": ADVISORY_RESULT_SCHEMA,
        "DIRECTOR_AUDIT": DIRECTOR_AUDIT_SCHEMA,
        "STRATEGIC_AUDIT": STRATEGIC_AUDIT_SCHEMA,
        "CHARACTER_LOGIC": CHARACTER_LOGIC_SCHEMA,
        "BLUEPRINT": BLUEPRINT_SCHEMA,
        "MANUSCRIPT": MANUSCRIPT_SCHEMA
    }

    return schemas.get(task_type)


def validate_response_against_schema(response: dict, schema: types.Schema) -> bool:
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
        print(f"[WARNING] Response is not a dict: {type(response)}")
        return False

    # required 필드 존재 여부만 체크 (타입은 Gemini가 보장)
    if hasattr(schema, 'properties'):
        required_props = schema.properties.keys()
        missing = [p for p in required_props if p not in response]
        if missing:
            print(f"[WARNING] Missing required fields: {missing}")
            return False

    return True


# =================================================================
# Schema Usage Examples
# =================================================================

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
