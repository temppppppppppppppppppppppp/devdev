# Stage 3 Blueprint additionalProperties 스키마 비호환 해소 Execution SSOT

Date: 2026-03-18
Status: investigation-only; superseded for implementation by `docs/2026-03-18/stage3-blueprint-schema-compatibility-execution-ssot.md`
Canonical Path: `docs/2026-03-18/stage3-blueprint-failure-deepdive-investigation.md`
Temp Mirror Path: `none`
Commit State:
- Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Baseline Dirty Summary: `dirty: 4 untracked (docs/2026-03-18 신규 3건, projects/0_260318)`
- Resume Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Resume Drift Summary: `re-audited on current workspace; implementation authority moved to stage3-blueprint-schema-compatibility-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-18/stage3-blueprint-failure-deepdive-investigation.md` (본 문서, 조사→실행 전환)
Evidence Artifacts:
- `projects/0_260318/logs/session/llm_io.jsonl` (BlueprintEnsembleGenerator 실패 30건 확인)
- `projects/0_260318/logs/session/ui_events.jsonl:268` (FAILED score=0 최종 기록)
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `82%` (`scene_breakdown` ARRAY 전환안이 live runtime contract 범위를 과대평가하여 구현 authority로는 부적합)

---

## 1. Intent

- **무엇을**: `response_schemas.py:556`의 `additionalProperties` 키워드가 Google Generative AI SDK에서 지원되지 않아 Stage 3 Blueprint 생성이 API 스키마 검증 단계에서 즉시 거부되는 P0 결함을 해소한다.
- **왜 지금**: 0_260318 프로젝트에서 Stage 2 Arc 설계까지 성공(3분 19초, score=100)했으나 Stage 3 진입 즉시 전량 실패(2초, score=0). 파이프라인 전체가 차단된 상태.
- **부차적**: 동일 스키마 에러가 10회 retry되는 비효율(P3) 함께 해소.

---

## 2. Baseline Facts

### 2.1 장애 타임라인 (로그 포렌식 확정)

```
10:22:17  Stage 3 진입, WorldState/Entity 초기화
10:22:20  제1화 Blueprint 생성 시작 (max_retries=9, 총 10회)
10:22:22  제1화 Blueprint 결과: FAILED (score=0)
```

- 2초 내 10회 retry 전량 실패 → LLM 품질 문제 아닌 **API 수준 즉시 거부**
- Phase 2 (Ensemble 생성) 단계에서 차단, Phase 3 (Director 검증)은 한 번도 실행되지 않음

### 2.2 에러 메시지 (llm_io.jsonl 원문)

```
[Warning] 모델 실패 (unknown), 백업 가동: additionalProperties is not supported in the Gemin
[Critical] 백업 실패 (unknown): additionalProperties is not supported in the Gemin
❌ [BPEnsemble] 모든 후보 생성 실패
```

- Primary (gemini-2.5-pro) → 실패 → Backup (gemini-2.5-flash) → 동일 실패
- 3개 전략 × 2개 모델 = 6회 API 호출 전량 동일 패턴 실패

### 2.3 score=0 산출 메커니즘

`pipeline_result["last_score"]`는 **PASS 경로에서만** 설정됨 (line 492). Phase 2 전량 실패 시:
1. `last_score` 미설정
2. `phases.generate.selected_score` 미설정
3. `stage3_orchestrator.py:1346` 폴백 체인 → 기본값 `0`

### 2.4 근본 원인 코드

**`modules/core/response_schemas.py:550-584`**:
```python
BLUEPRINT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "episode_number": types.Schema(type=types.Type.INTEGER),
        "scene_breakdown": types.Schema(
            type=types.Type.OBJECT,
            additionalProperties=BLUEPRINT_SCENE_ENTRY_SCHEMA,  # ← LINE 556: 원인
            description="Scene breakdown map with typed entries...",
        ),
        "integrated_scenario": types.Schema(type=types.Type.STRING),
        "pacing_notes": types.Schema(type=types.Type.STRING),
        "target_beat": types.Schema(type=types.Type.STRING),
        "relationship_changes": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.OBJECT, properties={
                "target": types.Schema(type=types.Type.STRING),
                "from_state": types.Schema(type=types.Type.STRING),
                "to_state": types.Schema(type=types.Type.STRING),
                "justification": types.Schema(type=types.Type.STRING),
            }),
        ),
        "time_flow": types.Schema(type=types.Type.STRING),
        "core_tension": types.Schema(type=types.Type.STRING),
        "expected_ending": types.Schema(type=types.Type.STRING),
    },
    required=["episode_number", "scene_breakdown", "integrated_scenario"],
)
```

**`BLUEPRINT_SCENE_ENTRY_SCHEMA` (lines 518-547)**:
```python
BLUEPRINT_SCENE_ENTRY_SCHEMA = types.Schema(
    anyOf=[
        types.Schema(
            type=types.Type.OBJECT,
            properties={
                "goal": types.Schema(type=types.Type.STRING),
                "summary": types.Schema(type=types.Type.STRING),
                "characters": types.Schema(
                    anyOf=[
                        types.Schema(type=types.Type.STRING),
                        types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                    ]
                ),
                "key_events": types.Schema(
                    anyOf=[
                        types.Schema(type=types.Type.STRING),
                        types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                    ]
                ),
                "location": types.Schema(type=types.Type.STRING),
                "content": types.Schema(type=types.Type.STRING),
            },
        ),
        types.Schema(type=types.Type.STRING),
    ],
    description="Scene entry value. Prefer an object with goal/summary, characters, key_events, and location; short string fallback remains allowed for compatibility.",
)
```

---

## 3. Scope

Included:
- `modules/core/response_schemas.py` — BLUEPRINT_SCHEMA, BLUEPRINT_SCENE_ENTRY_SCHEMA 재설계
- `modules/domain/agents/base_agent.py` — `_classify_error()` 스키마 에러 분류 추가
- `modules/domain/agents/three_phase_blueprint_generator.py` — Phase 2 실패 circuit breaker
- `modules/domain/agents/blueprint_ensemble.py` — scene_breakdown 파싱 호환성 확인
- `modules/models/blueprint.py` — Pydantic 모델 scene_breakdown 타입 정합성 확인
- `modules/validation/blocking_validator_scene_checks.py` — scene_breakdown 소비자 호환성 확인
- `config/prompts/ensemble.yaml` — 프롬프트 내 scene_breakdown 포맷 지시 확인
- 관련 테스트 파일

Excluded:
- Stage 0 주인공 설정 검증 (사용자 입력 오류이므로 코드 대상 아님)
- Stage 2 Arc 설계 로직
- Director/Auditor 검증 로직 (Phase 3 — 현재 미도달이므로 별도 검증 대상)
- broad LLM 프롬프트 리팩토링
- WorldState 초기화 갭 (별도 실행문서 대상)

---

## 4. Pass 1. Inventory Summary

### 4.1 핫스팟 (우선순위순)

| # | 파일 | 핫스팟 | 변경 성격 |
|---|------|--------|----------|
| 1 | `modules/core/response_schemas.py:550-584` | `BLUEPRINT_SCHEMA.scene_breakdown` | P0: 스키마 재설계 |
| 2 | `modules/core/response_schemas.py:518-547` | `BLUEPRINT_SCENE_ENTRY_SCHEMA` | P0: 연동 스키마 재설계 |
| 3 | `modules/domain/agents/base_agent.py:1498-1511` | `_classify_error()` | P3: 에러 분류 확장 |
| 4 | `modules/domain/agents/three_phase_blueprint_generator.py:346-351` | Phase 2 실패 경로 | P3: circuit breaker |
| 5 | `modules/domain/agents/blueprint_ensemble.py:589` | `response_schema=BLUEPRINT_SCHEMA` | P0: 소비자 확인 |

### 4.2 다운스트림 소비자 (scene_breakdown 사용처)

| 파일 | 사용 방식 | 호환성 영향 |
|------|----------|------------|
| `modules/models/blueprint.py:50` | `dict[str, BlueprintScene \| str]` Pydantic 모델 | ARRAY 전환 시 변경 필요 |
| `modules/validation/blocking_validator_scene_checks.py:72-155` | `scene_breakdown.items()` 순회 | ARRAY 전환 시 변경 필요 |
| `modules/domain/agents/unified_blueprint_validator.py` | dict 키 기반 씬 카운트 | ARRAY 전환 시 변경 필요 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | dict 접근, 씬 카운트 | ARRAY 전환 시 변경 필요 |
| `config/prompts/ensemble.yaml:318-330` | LLM 지시 포맷 | 프롬프트 수정 필요 |
| `tests/stage3_isolated_test/blueprints_*.json` | 테스트 데이터 (scene_1~scene_4 dict 키) | 테스트 데이터 갱신 필요 |

### 4.3 기존 성공 패턴 (동일 파일 내)

`response_schemas.py`의 다른 스키마들은 동적 구조를 다음과 같이 처리:
- `BLOCKING_RESULT_SCHEMA` (line 24): explicit ARRAY of OBJECTs
- `SCORING_RESULT_SCHEMA` (line 43): 중첩 OBJECT with explicit properties
- `ARC_DESIGN_SCHEMA` (line 179): ARRAY of OBJECTs for variable-length lists
- **공통 패턴**: 동적 키 맵 대신 ARRAY 타입 사용 또는 명시적 properties 정의

---

## 5. Pass 2. Semantic Classification

### Class A: 즉시 차단 해소 (P0)
- `response_schemas.py` BLUEPRINT_SCHEMA의 `scene_breakdown` 스키마를 Gemini 호환 구조로 재설계
- 다운스트림 소비자(Pydantic 모델, 검증기, 프롬프트) 정합성 동기화

### Class B: 방어적 에러 핸들링 (P3)
- `base_agent.py` `_classify_error()`에 스키마 비호환 에러 분류 추가
- `three_phase_blueprint_generator.py` Phase 2 연속 실패 시 circuit breaker (동일 에러 3회 반복 → 즉시 중단)

---

## 6. Side-Effect Map

- **file writes / artifacts**: `response_schemas.py` 스키마 변경 → 모든 Blueprint 생성 API 호출에 영향. 기존 저장된 Blueprint JSON 파일(`stage3_output/`)의 포맷이 dict→array 전환 시 변경됨.
- **DB / schema / transaction boundaries**: `project_data.db`의 `blueprints` 테이블에 저장되는 `scene_breakdown` 필드 포맷이 변경될 수 있음. 기존 데이터는 dict 포맷이므로 **마이그레이션 불필요** (Pydantic `extra="allow"` + JSON 문자열 저장).
- **JSONL / log / audit sinks**: `llm_io.jsonl`에 기록되는 response_schema가 변경됨. 로그 포맷 자체는 불변.
- **console / UI / operator output**: Phase 2 실패 시 circuit breaker 메시지 추가 (`[CircuitBreaker] 동일 스키마 에러 반복 — 즉시 중단`). 기존 `❌ [Phase 2] Ensemble 생성 실패` 메시지는 유지.
- **rollback / recovery / retry**: retry 횟수가 스키마 에러 시 10→최대 3으로 감소. 정상 에러(LLM 품질/네트워크)는 기존 10회 유지.
- **cache / global state**: `BLUEPRINT_SCHEMA`는 모듈 레벨 상수이므로 전역 영향. 변경 후 모든 Stage 3 실행에 즉시 적용.
- **bootstrap fallback / config-env mutation**: 해당 없음.

---

## 7. Realization Architecture

### 7.1 P0 스키마 재설계 전략 선택

**선택: ARRAY 전환 방식** (Option 1)

`scene_breakdown`을 `dict<string, SceneEntry>` → `array<SceneEntry>` (각 항목에 `scene_id` 필드 추가)로 전환.

**근거**:
- Gemini SDK가 ARRAY를 완전 지원 (기존 성공 패턴: `ARC_DESIGN_SCHEMA`, `BLOCKING_RESULT_SCHEMA`)
- `anyOf` (BLUEPRINT_SCENE_ENTRY_SCHEMA)도 ARRAY items에서 사용 가능
- 다운스트림 소비자 변경이 명확하고 기계적 (dict.items() → list enumerate)
- 기존 dict 데이터와의 하위 호환성은 Pydantic `extra="allow"` + 파싱 레이어에서 흡수

**기각된 대안**:
- Option 2 (명시적 properties scene_1~scene_N): 씬 수 상한 고정 → 유연성 상실
- Option 3 (STRING 타입): API 레벨 스키마 검증 상실
- Option 4 (response_schema=None): 전체 구조화 응답 포기 → 파싱 오류 급증 예상

### 7.2 하위 호환성 계약

- **신규 포맷**: `"scene_breakdown": [{"scene_id": "scene_1", "goal": "...", ...}, ...]`
- **레거시 포맷**: `"scene_breakdown": {"scene_1": {"goal": "...", ...}, ...}`
- **파싱 레이어**: `validate_blueprint()` (blueprint.py)에서 dict 수신 시 자동 변환 (레거시 호환)
- **저장 포맷**: 항상 array 포맷으로 정규화 후 저장

### 7.3 에러 분류 확장 계약

`base_agent.py:_classify_error()`에 새 분류 추가:
```
SCHEMA_INCOMPATIBLE = "schema_incompatible"
```
키워드: `"additionalproperties"`, `"not supported"`, `"schema"` 조합 감지.

### 7.4 Circuit Breaker 계약

`three_phase_blueprint_generator.py` Phase 2 실패 경로에:
- 동일 에러 메시지 연속 3회 → `final_verdict = "FAILED"` + 즉시 리턴
- 에러 메시지 비교는 정규화 후 동등성 판단

---

## 8. Execution Tranches

### Tranche 1: P0 스키마 재설계 (BLUEPRINT_SCHEMA)

**Step 1.1**: `modules/core/response_schemas.py` 수정

**Before** (lines 518-584):
```python
BLUEPRINT_SCENE_ENTRY_SCHEMA = types.Schema(
    anyOf=[
        types.Schema(type=types.Type.OBJECT, properties={
            "goal": types.Schema(type=types.Type.STRING),
            "summary": types.Schema(type=types.Type.STRING),
            "characters": types.Schema(anyOf=[
                types.Schema(type=types.Type.STRING),
                types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            ]),
            "key_events": types.Schema(anyOf=[
                types.Schema(type=types.Type.STRING),
                types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            ]),
            "location": types.Schema(type=types.Type.STRING),
            "content": types.Schema(type=types.Type.STRING),
        }),
        types.Schema(type=types.Type.STRING),
    ],
    description="Scene entry value...",
)

BLUEPRINT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "episode_number": types.Schema(type=types.Type.INTEGER),
        "scene_breakdown": types.Schema(
            type=types.Type.OBJECT,
            additionalProperties=BLUEPRINT_SCENE_ENTRY_SCHEMA,  # ← 제거 대상
            description="...",
        ),
        # ... (나머지 필드 동일)
    },
    required=["episode_number", "scene_breakdown", "integrated_scenario"],
)
```

**After**:
```python
BLUEPRINT_SCENE_ENTRY_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "scene_id": types.Schema(type=types.Type.STRING),
        "goal": types.Schema(type=types.Type.STRING),
        "summary": types.Schema(type=types.Type.STRING),
        "characters": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
        "key_events": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
        "location": types.Schema(type=types.Type.STRING),
        "content": types.Schema(type=types.Type.STRING),
    },
    description=(
        "Scene entry with scene_id, goal, summary, characters, key_events, location. "
        "scene_id는 'scene_1', 'scene_2' 등 순번 식별자."
    ),
)

BLUEPRINT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "episode_number": types.Schema(type=types.Type.INTEGER),
        "scene_breakdown": types.Schema(
            type=types.Type.ARRAY,
            items=BLUEPRINT_SCENE_ENTRY_SCHEMA,
            description="씬 목록. 각 항목은 scene_id로 식별되는 구조화된 씬 엔트리.",
        ),
        "integrated_scenario": types.Schema(type=types.Type.STRING),
        "pacing_notes": types.Schema(type=types.Type.STRING),
        "target_beat": types.Schema(type=types.Type.STRING),
        "relationship_changes": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.OBJECT, properties={
                "target": types.Schema(type=types.Type.STRING),
                "from_state": types.Schema(type=types.Type.STRING),
                "to_state": types.Schema(type=types.Type.STRING),
                "justification": types.Schema(type=types.Type.STRING),
            }),
        ),
        "time_flow": types.Schema(type=types.Type.STRING),
        "core_tension": types.Schema(type=types.Type.STRING),
        "expected_ending": types.Schema(type=types.Type.STRING),
    },
    required=["episode_number", "scene_breakdown", "integrated_scenario"],
)
```

**변경 요약**:
1. `BLUEPRINT_SCENE_ENTRY_SCHEMA`: `anyOf` 제거 → 단일 OBJECT 타입, `scene_id` 필드 추가, `characters`/`key_events`를 `anyOf` 대신 순수 ARRAY로 단순화
2. `BLUEPRINT_SCHEMA.scene_breakdown`: `type=OBJECT + additionalProperties` → `type=ARRAY + items`

**Step 1.2**: `modules/models/blueprint.py` Pydantic 모델 동기화

**Before** (line 50):
```python
scene_breakdown: dict[str, BlueprintScene | str] = Field(default_factory=dict)
```

**After**:
```python
scene_breakdown: list[dict] | dict[str, BlueprintScene | str] = Field(default_factory=list)
```

하위 호환 유지: dict(레거시)도 수용하되 기본값은 list.

**Step 1.3**: `modules/models/blueprint.py`에 정규화 유틸리티 추가

`validate_blueprint()` 함수 내부 또는 별도 헬퍼:

```python
def _normalize_scene_breakdown(raw: dict | list) -> list[dict]:
    """dict 포맷(레거시)을 array 포맷(신규)으로 정규화."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        result = []
        for scene_id, entry in raw.items():
            if isinstance(entry, str):
                result.append({"scene_id": scene_id, "content": entry})
            elif isinstance(entry, dict):
                entry_copy = dict(entry)
                entry_copy.setdefault("scene_id", scene_id)
                result.append(entry_copy)
        return result
    return []
```

**Step 1.4**: 다운스트림 소비자 동기화

**`modules/validation/blocking_validator_scene_checks.py`**:

Before (line 72-74):
```python
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown and isinstance(scene_breakdown, dict):
    scene_count = len(scene_breakdown)
```

After:
```python
scene_breakdown = blueprint.get("scene_breakdown", [])
if isinstance(scene_breakdown, dict):
    scene_breakdown = _normalize_scene_breakdown(scene_breakdown)
scene_count = len(scene_breakdown) if isinstance(scene_breakdown, list) else 0
```

Before (line 155):
```python
for scene_name, scene_desc in scene_breakdown.items():
```

After:
```python
for scene_entry in scene_breakdown:
    scene_name = scene_entry.get("scene_id", "unknown") if isinstance(scene_entry, dict) else "unknown"
    scene_desc = scene_entry if isinstance(scene_entry, dict) else {"content": str(scene_entry)}
```

**동일 패턴의 소비자 전량** (`three_phase_blueprint_generator.py`, `unified_blueprint_validator.py` 등)에서 `scene_breakdown.items()` → list 순회로 변경. 각 위치는 `scene_breakdown` grep 결과 기반으로 전수 확인 필요.

**Step 1.5**: 프롬프트 동기화

**`config/prompts/ensemble.yaml:318-330`**:

Before:
```yaml
"scene_breakdown": {
    "scene_1": {
        "type": "opening_hook",
        "title": "씬 제목",
        ...
    },
    "scene_2": {...},
}
```

After:
```yaml
"scene_breakdown": [
    {
        "scene_id": "scene_1",
        "type": "opening_hook",
        "title": "씬 제목",
        ...
    },
    {
        "scene_id": "scene_2",
        ...
    }
]
```

---

### Tranche 2: P3 에러 분류 및 Circuit Breaker

**Step 2.1**: `modules/domain/agents/base_agent.py` `_classify_error()` 확장

Before (lines 1498-1511):
```python
def _classify_error(self, error: Exception) -> str:
    error_str = str(error).lower()
    if "timeout" in error_str or "timed out" in error_str or "deadline" in error_str:
        return AgentErrorType.TIMEOUT
    elif "quota" in error_str or "rate" in error_str or "429" in error_str:
        return AgentErrorType.QUOTA_EXCEEDED
    elif "connection" in error_str or "network" in error_str or "ssl" in error_str:
        return AgentErrorType.NETWORK_ERROR
    elif "json" in error_str or "parse" in error_str or "decode" in error_str:
        return AgentErrorType.MALFORMED_RESPONSE
    else:
        return AgentErrorType.UNKNOWN
```

After:
```python
def _classify_error(self, error: Exception) -> str:
    error_str = str(error).lower()
    if "timeout" in error_str or "timed out" in error_str or "deadline" in error_str:
        return AgentErrorType.TIMEOUT
    elif "quota" in error_str or "rate" in error_str or "429" in error_str:
        return AgentErrorType.QUOTA_EXCEEDED
    elif "connection" in error_str or "network" in error_str or "ssl" in error_str:
        return AgentErrorType.NETWORK_ERROR
    elif "json" in error_str or "parse" in error_str or "decode" in error_str:
        return AgentErrorType.MALFORMED_RESPONSE
    elif "not supported" in error_str and ("schema" in error_str or "additionalproperties" in error_str):
        return AgentErrorType.SCHEMA_INCOMPATIBLE
    else:
        return AgentErrorType.UNKNOWN
```

`AgentErrorType` 클래스에 추가 (line 45):
```python
SCHEMA_INCOMPATIBLE = "schema_incompatible"
```

**Step 2.2**: `modules/domain/agents/three_phase_blueprint_generator.py` Circuit Breaker

Phase 2 실패 경로 (lines 346-351) 직전에 에러 축적 추적 삽입:

Before:
```python
if not best_blueprint:
    logging.warning("❌ [Phase 2] Ensemble 생성 실패")
    self._operator_log("❌ [Phase 2] Ensemble 생성 실패", level="warning", meta={"phase": "generate"})
    pipeline_result["phases"]["generate"] = {"status": "failed"}
    feedback = "Blueprint 생성 실패. 다시 시도하세요."
    continue
```

After:
```python
if not best_blueprint:
    _consecutive_phase2_failures += 1
    logging.warning("❌ [Phase 2] Ensemble 생성 실패")
    self._operator_log("❌ [Phase 2] Ensemble 생성 실패", level="warning", meta={"phase": "generate"})
    pipeline_result["phases"]["generate"] = {"status": "failed"}

    if _consecutive_phase2_failures >= 3:
        logging.error(
            f"[CircuitBreaker] Phase 2 연속 {_consecutive_phase2_failures}회 실패 — 동일 에러 반복 판단, 즉시 중단"
        )
        self._operator_log(
            f"🔌 [CircuitBreaker] Phase 2 연속 {_consecutive_phase2_failures}회 실패 — 즉시 중단",
            level="error",
            meta={"phase": "generate", "circuit_breaker": True},
        )
        break

    feedback = "Blueprint 생성 실패. 다시 시도하세요."
    continue
```

retry 루프 진입 전 (line 180 직전)에 카운터 초기화:
```python
_consecutive_phase2_failures = 0
```

Phase 2 성공 시 (line 353 부근) 카운터 리셋:
```python
_consecutive_phase2_failures = 0  # Phase 2 성공 → 카운터 리셋
```

---

## 9. Acceptance Criteria

- `BLUEPRINT_SCHEMA`가 Gemini API 스키마 검증을 통과하여 LLM 호출이 실행됨
- `additionalProperties` 키워드가 `response_schemas.py`에서 완전 제거됨
- 기존 dict 포맷 Blueprint 데이터가 `_normalize_scene_breakdown()`을 통해 정상 파싱됨
- 신규 array 포맷 Blueprint가 모든 다운스트림 소비자(검증기, Director, Writer)에서 정상 처리됨
- Phase 2 동일 에러 연속 3회 시 circuit breaker가 작동하여 불필요한 retry 7회를 절감함
- `_classify_error()`가 `"additionalProperties is not supported"` 에러를 `SCHEMA_INCOMPATIBLE`로 정확 분류함
- 모든 기존 테스트가 통과함

---

## 10. Verification Plan

### 10.1 단위 검증
- `python -m py_compile modules/core/response_schemas.py` — 구문 검증
- `python -m py_compile modules/domain/agents/base_agent.py`
- `python -m py_compile modules/domain/agents/three_phase_blueprint_generator.py`
- `python -m py_compile modules/models/blueprint.py`
- `ruff check` on touched files
- `ruff format --check` on touched files

### 10.2 스키마 호환성 검증
```python
# 인라인 검증 스크립트
from modules.core.response_schemas import BLUEPRINT_SCHEMA
from google.genai import types
# BLUEPRINT_SCHEMA가 types.Schema 인스턴스이고 additionalProperties가 없는지 확인
assert not hasattr(BLUEPRINT_SCHEMA.properties["scene_breakdown"], "additional_properties") or \
    BLUEPRINT_SCHEMA.properties["scene_breakdown"].additional_properties is None
print("✅ BLUEPRINT_SCHEMA Gemini 호환성 확인")
```

### 10.3 정규화 유틸리티 검증
```python
from modules.models.blueprint import _normalize_scene_breakdown
# dict → list 변환
assert _normalize_scene_breakdown({"scene_1": {"goal": "test"}}) == [{"scene_id": "scene_1", "goal": "test"}]
# list 패스스루
assert _normalize_scene_breakdown([{"scene_id": "s1"}]) == [{"scene_id": "s1"}]
# string value 변환
assert _normalize_scene_breakdown({"s1": "text"}) == [{"scene_id": "s1", "content": "text"}]
print("✅ _normalize_scene_breakdown 정상")
```

### 10.4 회귀 테스트
- `pytest tests/test_stage3_*.py -q` — Stage 3 관련 전체
- `pytest tests/test_run_stage34_canary.py -q` — Stage 3/4 카나리아
- `pytest tests/test_auto_frontier_lag_harness.py -q` — FrontierLag 파이프라인
- `pytest tests/ -q --timeout=120` — 전체 테스트 스위트

### 10.5 통합 검증 (수동)
- 0_260318 프로젝트에서 Stage 3 재실행: `python main_a.py` → 장르 선택 → 프로젝트 선택 → Command 7 (FrontierLag)
- 제1화 Blueprint 생성이 score>0으로 PASS/PASS_WITH_FIX/PASS_WITH_WARNING 중 하나를 반환하는지 확인
- `projects/0_260318/logs/session/llm_io.jsonl`에 `additionalProperties` 에러 부재 확인

### 10.6 인프라 검증
- `python scripts/check_utf8_hygiene.py modules/core/response_schemas.py modules/models/blueprint.py`
- `python scripts/ops_validator.py --strict`

---

## 11. Guardrails

- `response_schemas.py`에서 `additionalProperties` 키워드를 다른 스키마에도 사용하지 않음을 전수 확인할 것
- `anyOf`는 Gemini SDK에서 제한적 지원이므로 가능한 단일 타입으로 단순화할 것 (이번 변경에서 BLUEPRINT_SCENE_ENTRY_SCHEMA의 anyOf 제거)
- Circuit breaker는 Phase 2 전용. Phase 3 (Director REJECT)에는 적용하지 않음 (Director REJECT는 LLM 품질 이슈이므로 retry가 유효)
- 프롬프트 포맷 변경 시 `config/prompts/ensemble.yaml`만 수정. 다른 프롬프트 파일은 건드리지 않음
- `_normalize_scene_breakdown()`은 방어적 코딩: 입력이 dict/list 아닌 경우 빈 리스트 반환

---

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: 실행 완료 후 temp mirror 제거, queue-state 갱신
- roadmap dependency: Stage 3 파이프라인 정상화가 전제되어야 Stage 4 (원고 생산) 진행 가능

---

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

## 감리 상태

- [x] 1-pass: 초기 조사 — 3개 Explore 에이전트 병렬 투입, 근본 원인 식별 (`additionalProperties` 스키마 비호환)
- [x] 2-pass: 코드 직접 검증 — `response_schemas.py:518-584`, `three_phase_blueprint_generator.py:180-739`, `stage3_orchestrator.py:1325-1346`, `base_agent.py:1498-1511`, `blueprint_ensemble.py:589`, `blueprint.py:50`, `blocking_validator_scene_checks.py:72-155`, `ensemble.yaml:318-330`, `constants.py:633-645`, `validation.yaml:34,100-104` 원문 대조 완료
- [x] 3-pass: 로그 포렌식 + 실행문서 정합성 — `ui_events.jsonl:255-274` 타임라인 확인, `llm_io.jsonl` 에러 메시지 60건 확인, 다운스트림 소비자 전수 매핑 완료, Before/After 코드 블록 정합성 확인
