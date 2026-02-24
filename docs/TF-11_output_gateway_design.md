# TF-11: LLM Output Normalization Gateway -- 설계 문서

> 작성일: 2026-02-24
> 근거: 코드 실독 기반 (추정 없음)
> 전제 문서: TF-10 (episode_detail_map 분석)

---

## 0. 배경: 암묵적 계약(Implicit Contract) 문제

현재 글도비 시스템에서 LLM 출력은 다음 경로를 따른다:

```
LLM raw text → BaseAgent.ask() [str 반환]
            → _extract_json_robust() [dict 반환]
            → 호출자가 .get()으로 소비
```

이 경로에서 **타입 검증이 없다**. `_extract_json_robust()`는 JSON 파싱과 자가 치유만 담당하고, 반환된 dict의 필드 타입/존재 여부를 보장하지 않는다. 22개 에이전트 파일의 55개 `.ask()` 호출, 27개 파일의 65개 `_extract_json_robust()` 호출이 모두 bare dict를 맹목적으로 `.get()`한다.

**결과**: Arc에 `episode_details`가 `None`이면 downstream에서 `for item in None` TypeError 발생. Blueprint에 `scene_breakdown`이 str이면 dict 기대 코드가 깨짐. 이런 버그가 반복 발생한다.

---

## 1. LLM 출력 경계 전수 조사

### 1-A. 중앙 파서: BaseAgent._extract_json_robust()

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/base_agent.py` L1000-1123 |
| **입력** | `str` (LLM raw text) |
| **출력** | `dict` (항상) -- 파싱 실패 시 `{"parsing_error": True, ...}` |
| **자가 치유** | 괄호 폐쇄, 마크다운 펜스 제거, json.loads -> ast.literal_eval -> _parse_and_repair_hard -> regex 필드 추출 |
| **한계** | 반환 dict의 필드 타입/존재 여부 무보장. 평탄화 엔진이 중첩 구조를 파괴할 수 있음 |

### 1-B. 중앙 검증: BaseAgent._validate_response()

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/base_agent.py` L896-938 |
| **검증 내용** | 빈 응답, 최소 길이(10자), JSON 시작 문자, 괄호 균형, 핵심 필드 13개 중 1개 이상 존재 |
| **한계** | 필드 **존재**만 검사. 타입/값 범위 미검증. `"content"` 키가 있으면 OK인데 값이 `None`이어도 통과 |

### 1-C. 전체 LLM 출력 경계 맵 (22개 에이전트, 55개 .ask() 호출)

#### Tier 1 -- 핵심 생성 경로 (파이프라인 SSOT 데이터 생성)

| # | 에이전트 | 파일:라인 | .ask() 호출 | _extract_json_robust 호출 | 기대 출력 타입 | 실패 처리 |
|---|----------|-----------|-------------|---------------------------|---------------|-----------|
| B1 | ArcEnsemble | `arc_ensemble.py:474` | `_ask_with_cached_context()` | L483 | `dict{arc_no, tactical_doc, beat_sequence, state_constraints, ...}` | isinstance(dict) 체크 + parsing_error 체크. 실패 시 후보 탈락 |
| B2 | BlueprintEnsemble | `blueprint_ensemble.py:428` | `_ask_with_cached_context()` | L435 | `dict{scene_breakdown, integrated_scenario, ...}` | isinstance(dict) 체크 + 핵심 키 존재 확인. 실패 시 후보 탈락 |
| B3 | ChiefWriter | `chief_writer.py:445` | `ask() / _ask_with_cached_context()` | L454 | `dict{content: str, title: str, state_updates: dict}` | content 타입 강제 변환(str/list/dict). validate_manuscript_candidate() Pydantic 검증 |
| B4 | StateLocked ArcGen | `state_locked_arc_generator.py:392,408,426,455` | `ask()` x4 | L460 | `dict{arc_no, tactical_doc, ...}` (Arc 스키마) | json.loads 폴백 |

#### Tier 2 -- 검증/심사 경로 (PASS/REJECT 판정)

| # | 에이전트 | 파일:라인 | .ask() 호출 | _extract_json_robust 호출 | 기대 출력 타입 | 실패 처리 |
|---|----------|-----------|-------------|---------------------------|---------------|-----------|
| B5 | UnifiedArcValidator | `unified_arc_validator.py:550` | `ask()` | L551 | `dict{verdict, issues, summary, confidence}` | fail-closed: 파싱 실패 시 REJECT + CRITICAL |
| B6 | DirectorAuditor | `director_auditor.py:174,705,822,846,895` | `_d.ask()` x5 | L175,706,823,847,896 | `dict{decision, score, reason, ...}` | 각 호출마다 개별 try/except |
| B7 | DirectorContinuity | `director_continuity.py:120,410,745` | `_d.ask()` x3 | L121,411,525,747 | `dict{conflicts, score, ...}` | 개별 try/except |
| B8 | DirectorEnsemble | `director_ensemble.py:145,393,513` | `_d.ask()` x3 | L146,397,514 | `dict{decision, reasons, ...}` | 개별 try/except |
| B9 | ArcCritic | `arc_critic.py:161` | `ask()` | L164 | `dict{issues, severity, ...}` | result가 str이면 _extract_json_robust 호출 |
| B10 | Critic | `critic.py:436,547` | `ask()` x2 | L437,548 | `dict{feedback, score, ...}` | 직접 반환 |
| B11 | ConsensusValidator | `consensus_validator.py:311` | `ask()` | L314 | `dict{verdict, ...}` | isinstance 체크 |

#### Tier 3 -- 보조 분석/추출 경로

| # | 에이전트 | 파일:라인 | .ask() 호출 | _extract_json_robust 호출 | 기대 출력 타입 | 실패 처리 |
|---|----------|-----------|-------------|---------------------------|---------------|-----------|
| B12 | Analyst | `analyst.py:142,771,841,1091,1108,1161,1217,1298,1309` | `ask()` x9 | L148,742,771,841,1092,1109,1162,1220,1299,1310 | 다양 (Arc/Bible/Treatment/Calibration) | 호출마다 다름. response_schema 사용(L737,771) |
| B13 | ArcCorrector | `arc_corrector.py:263,314,398` | `ask()` x3 | L265,316,400 | `dict{corrected_tactical_doc, ...}` | isinstance 체크 |
| B14 | StateExtractor | `state_extractor.py:243,798` | `ask()` x2 | L246,800 | `dict{state_changes, ...}` | isinstance 체크 |
| B15 | BlockEnricher | `block_enricher.py:343,374,421,477,521,831,908` | `ask()` x7 | L346,376,423,482,526,836,911 | `dict` (다양한 블록 타입) | 각 호출마다 isinstance + retry |
| B16 | Manager | `manager.py:150,176` | `ask()` x2 | L156 | `dict` (관리 커맨드) | 직접 반환 |
| B17 | PreflightChecker | `preflight_checker.py:156` | `ask()` | L159 | `dict{risks, ...}` | isinstance 체크 |
| B18 | Weaver | `weaver.py:67,115` | `ask()` + `response.text` | L67,116 | `dict{drive_data, ...}` | 직접 반환 |
| B19 | Writer | `writer.py:251,253` | `ask()` x2 | 없음 (raw str 반환) | `str` (원고 텍스트) | _sanitize_leakage만 적용 |

#### Tier 4 -- 연속성 검사 경로 (ContinuityInspector 위임)

| # | 에이전트 | 파일:라인 | .ask() 호출 | _extract_json_robust 호출 | 기대 출력 타입 | 실패 처리 |
|---|----------|-----------|-------------|---------------------------|---------------|-----------|
| B20 | ContinuityArc | `continuity_arc.py:380,541` | `_ci.ask()` x2 | L381,542 | `dict{conflicts, score}` | isinstance 체크 |
| B21 | ContinuityBlueprint | `continuity_blueprint.py:234` | `_ci.ask()` | L235 | `dict{conflicts, score}` | isinstance 체크 |
| B22 | ContinuityManuscript | `continuity_manuscript.py:290` | `_ci.ask()` | L291 | `dict{conflicts, score}` | isinstance 체크 |

#### Tier 5 -- 비에이전트 경로 (core 모듈에서 직접 호출)

| # | 모듈 | 파일:라인 | _extract_json_robust 호출 | 비고 |
|---|------|-----------|---------------------------|------|
| B23 | ReferenceAnchor | `reference_anchor.py:113` | `agent._extract_json_robust(response)` | 외부 agent 인스턴스 경유 |
| B24 | Stage2Preflight | `stage2_preflight.py:855-856` | `_fp_agent._extract_json_robust()` | ASP 경로 |
| B25 | Stage4Orchestrator | `stage4_orchestrator.py:272` | `director._extract_json_robust(result)` | 체인 링크 파싱 |

### 1-D. 요약 통계

| 메트릭 | 값 |
|--------|-----|
| 총 `.ask()` 호출 | **55회** (22개 에이전트 파일) |
| 총 `_extract_json_robust()` 호출 | **65회** (27개 파일) |
| Pydantic 검증 적용 경계 | **3곳** (chief_writer L382, stage2_finalizer L358, three_phase_bp_gen L388/L446) |
| Gemini response_schema 적용 | **1곳** (analyst.py L737, L771) |
| **타입 미검증 경계** | **62회** (65 - 3 Pydantic) |

---

## 2. 기존 정규화 유틸리티 평가

### 2-A. _extract_json_robust() (base_agent.py L1000-1123)

| 평가 항목 | 상태 |
|-----------|------|
| JSON 파싱 | 우수 -- 4단계 폴백 (json.loads -> ast.literal_eval -> hard_repair -> regex) |
| 자가 치유 | 우수 -- 괄호 폐쇄, 마크다운 펜스 제거, 페이로드 크기 가드 |
| 평탄화 | 위험 -- 재귀적 process_node()가 중첩 dict를 단일 레벨로 평탄화. `state_constraints.arc_start_state.location`이 `location` 키로 승격되어 최상위 `location`과 충돌 가능 |
| 타입 보장 | **없음** -- dict 반환만 보장. 내부 필드 타입 무검증 |
| 에러 표현 | 일관적 -- `{"parsing_error": True}` 패턴. 다만 호출자마다 이 키 체크 방식이 다름 |

**결론**: 파싱 계층으로는 충분. 그러나 **타입 검증 계층이 부재**하여 Gateway의 핵심 보완 대상.

### 2-B. response_schemas.py (594줄)

| 평가 항목 | 상태 |
|-----------|------|
| 스키마 정의 | 우수 -- 9개 Gemini API types.Schema 정의 (BLOCKING, SCORING, ADVISORY, DIRECTOR_AUDIT, STRATEGIC_AUDIT, CHARACTER_LOGIC, ARC_DESIGN, BLUEPRINT, MANUSCRIPT) |
| 실제 사용 | **analyst.py 1곳만** -- L737(`ARC_DESIGN_SCHEMA`), L771(`get_schema_for_task`) |
| 범용성 | 낮음 -- Gemini API `response_schema` 파라미터 전용. LLM 출력 후 Python 측 검증에는 사용 불가 |
| 검증 함수 | `validate_response_against_schema()` 존재 (L382+) -- 그러나 필수 필드 존재만 검사, 타입 미검증 |

**결론**: Gemini API 쪽 출력 강제 도구로는 유효하지만, Python 측 타입 보장 역할은 불가. Gateway와 직교(orthogonal)한 레이어.

### 2-C. modules/models/ Pydantic v2 모델 (4개)

| 모델 | 파일 | 필드 수 | 사용처 | graceful degradation |
|------|------|---------|--------|---------------------|
| `ArcData` | `arc.py` L163-203 | 13 (+ sub-models 6개) | `stage2_finalizer.py` L358 (`validate_arc()`) | O -- 실패 시 원본 반환 |
| `Blueprint` | `blueprint.py` L30-63 | 7 | `three_phase_bp_gen.py` L388, L446 (`validate_blueprint()`) | O |
| `ManuscriptCandidate` | `manuscript.py` L14-40 | 7 | `chief_writer.py` L382 (`validate_manuscript_candidate()`) | O |
| `NPCEntry` | `npc.py` L20-33 | 6 | `state_tracker.py` (간접) | O |

**핵심 문제점**:
1. **3곳에서만 사용** -- 65개 _extract_json_robust 호출 중 3곳만 Pydantic 검증을 거침
2. **graceful degradation** -- 검증 실패 시 원본 dict를 그대로 반환하므로 "통과" 착각 발생
3. **egress 후 bare dict** -- `model_dump()` 결과가 다시 bare dict이므로 downstream에서는 Pydantic 보호 없음
4. **extra="allow"** -- 미지 키를 모두 수용하므로 오타 키(`tacticl_doc`)도 조용히 통과

**결론**: 모델 자체는 건전하나, **적용 범위가 3/65 (4.6%)로 극히 제한적**. Gateway는 이 모델들을 65개 경계 전체로 확산시키는 것이 핵심.

### 2-D. 검증 파이프라인 (pre_llm_validator 등)

`modules/validation/` 하위 validator들은 **LLM 호출 전** 입력 검증에 집중. LLM **출력** 검증은 담당하지 않음. Gateway와 보완 관계.

---

## 3. Gateway 설계 제안

### 3-1. 우선순위 TOP 5 경계 (리스크 x 빈도)

| 순위 | 경계 ID | 에이전트 | 이유 |
|------|---------|----------|------|
| **P0** | B1 | ArcEnsemble | Arc는 전체 파이프라인의 SSOT. 여기서 타입 오류 발생 시 Stage 3/4 전체 연쇄 실패. `tactical_doc`이 dict일 수 있고 `beat_sequence`가 str일 수 있음 |
| **P0** | B3 | ChiefWriter | 원고 생성 경로. `content`가 str/list/dict 어느 것이든 올 수 있어 이미 L460-472에 수동 타입 강제 존재. 정규화 게이트웨이의 가장 직접적인 수혜자 |
| **P1** | B2 | BlueprintEnsemble | Blueprint는 Stage 4의 직접 입력. `scene_breakdown`이 dict/list/str 중 어느 것인지 미보장 |
| **P1** | B5 | UnifiedArcValidator | PASS/REJECT 판정. `verdict` 필드가 없으면 fail-closed로 무조건 REJECT. 정상 출력도 REJECT될 수 있음 |
| **P2** | B6 | DirectorAuditor | 5개 .ask() 호출, 5개 _extract_json_robust. 각각 기대 스키마가 다름. 스키마 혼동 시 PASS/REJECT 오판 |

### 3-2. Gateway 구조: 함수형 + 모델 기반 하이브리드

#### 3-2-A. 설계 원칙

1. **기존 경로 무파괴** -- `_extract_json_robust()` 반환 이후에 삽입. 기존 코드의 `.get()` 패턴 유지
2. **graceful degradation 유지** -- 검증 실패 시 원본 dict 반환 (현재 Pydantic 모델과 동일 패턴)
3. **점진적 확산** -- TOP 5부터 적용, 안정화 후 나머지 확산
4. **BaseAgent에 메서드 추가** -- 각 에이전트가 개별 구현하지 않도록 중앙 집중

#### 3-2-B. 구조 제안

```
                      ask()
                        │
                        ▼
              _extract_json_robust()     ← 기존 (파싱 계층)
                        │
                        ▼
             _normalize_output()         ← 신규 (Gateway)
              ┌─────────┼─────────┐
              ▼         ▼         ▼
          ArcData   Blueprint   ManuscriptCandidate   ← Pydantic 모델
              │         │         │
              ▼         ▼         ▼
          model_dump()  ...       ...     ← dict 반환 (하위호환)
                        │
                        ▼
                  호출자 .get()          ← 기존 코드 무수정
```

#### 3-2-C. 핵심 API

```python
# base_agent.py에 추가할 메서드

def _normalize_output(self, raw: dict, schema_hint: str = None) -> dict:
    """LLM 출력 정규화 Gateway

    Args:
        raw: _extract_json_robust() 반환값
        schema_hint: 기대 스키마 힌트 ("arc", "blueprint", "manuscript",
                     "validation_result", "director_decision")

    Returns:
        정규화된 dict (검증 실패 시 원본 반환 -- graceful degradation)
    """
    if not isinstance(raw, dict) or raw.get("parsing_error"):
        return raw

    normalizer = self._SCHEMA_REGISTRY.get(schema_hint)
    if normalizer is None:
        return raw  # 힌트 없으면 패스스루

    return normalizer(raw)


# 레지스트리 (클래스 변수)
_SCHEMA_REGISTRY = {
    "arc": lambda raw: _safe_validate(ArcData, raw),
    "blueprint": lambda raw: _safe_validate(Blueprint, raw),
    "manuscript": lambda raw: _safe_validate(ManuscriptCandidate, raw),
    "validation_result": lambda raw: _normalize_validation_result(raw),
    "director_decision": lambda raw: _normalize_director_decision(raw),
}


def _safe_validate(model_cls, raw: dict) -> dict:
    """Pydantic 검증 + graceful degradation"""
    try:
        return model_cls.model_validate(raw).model_dump()
    except Exception:
        logger.warning("[Gateway] %s 검증 실패 -- 원본 유지", model_cls.__name__)
        return raw
```

#### 3-2-D. 추가 정규화 함수 (Pydantic 모델 미존재 스키마용)

```python
def _normalize_validation_result(raw: dict) -> dict:
    """검증 결과 정규화 (UnifiedArcValidator, DirectorAuditor 등)"""
    # verdict 필드 보장
    if "verdict" not in raw and "decision" in raw:
        raw["verdict"] = raw["decision"]
    # issues 필드 타입 보장 (list)
    issues = raw.get("issues")
    if issues is None:
        raw["issues"] = []
    elif isinstance(issues, str):
        raw["issues"] = [issues]
    # confidence 필드 보장 (float)
    conf = raw.get("confidence")
    if conf is not None:
        try:
            raw["confidence"] = float(conf)
        except (ValueError, TypeError):
            raw["confidence"] = 0.5
    return raw


def _normalize_director_decision(raw: dict) -> dict:
    """Director 심사 결과 정규화"""
    # decision 필드 보장
    if "decision" not in raw:
        raw["decision"] = "REJECT"  # fail-closed 원칙
    else:
        raw["decision"] = str(raw["decision"]).upper().strip()
    # score 필드 보장 (int)
    score = raw.get("score")
    if score is not None:
        try:
            raw["score"] = int(score)
        except (ValueError, TypeError):
            raw["score"] = 0
    # reason 필드 보장 (str)
    if "reason" not in raw:
        raw["reason"] = ""
    return raw
```

### 3-3. 점진적 도입 전략

#### Phase 0: 인프라 (base_agent.py 수정)

```
base_agent.py에 _normalize_output() + _SCHEMA_REGISTRY 추가
테스트: 기존 2,537개 전량 그린 확인
수정량: ~60줄
```

#### Phase 1: P0 경계 (ArcEnsemble + ChiefWriter)

적용 방식: 각 에이전트의 `_extract_json_robust()` 호출 직후에 `_normalize_output()` 1줄 추가

```python
# arc_ensemble.py L483 (현재)
result = self._extract_json_robust(result)

# arc_ensemble.py L483 (변경 후)
result = self._extract_json_robust(result)
result = self._normalize_output(result, schema_hint="arc")
```

```python
# chief_writer.py L454 (현재)
data = self._extract_json_robust(response)

# chief_writer.py L454 (변경 후)
data = self._extract_json_robust(response)
data = self._normalize_output(data, schema_hint="manuscript")
```

**수정량**: 각 파일 1줄 추가 (2개 파일, 2줄)
**효과**:
- ArcEnsemble: `tactical_doc`이 dict이면 str 변환, `beat_sequence`가 str이면 list 변환
- ChiefWriter: L460-472의 수동 타입 강제를 Pydantic이 대체

#### Phase 2: P1 경계 (BlueprintEnsemble + UnifiedArcValidator)

```python
# blueprint_ensemble.py L435
result = self._extract_json_robust(response)
result = self._normalize_output(result, schema_hint="blueprint")

# unified_arc_validator.py L551
result = self._extract_json_robust(response)
result = self._normalize_output(result, schema_hint="validation_result")
```

**수정량**: 2개 파일, 2줄

#### Phase 3: P2 경계 (DirectorAuditor) + 나머지 Tier 2

```python
# director_auditor.py L175, L706, L823, L847, L896 (5곳)
result = self._d._extract_json_robust(response)
result = self._d._normalize_output(result, schema_hint="director_decision")
```

**수정량**: 1개 파일, 5줄

#### Phase 4: Tier 3~5 확산 (잔여 52개 경계)

나머지 경계는 다음 두 전략 중 선택:

**전략 A (opt-in)**: 각 에이전트가 필요한 곳에 `_normalize_output()` 추가
- 장점: 최소 침습
- 단점: 적용 누락 위험

**전략 B (opt-out)**: `_extract_json_robust()` 내부 마지막에 `_normalize_output()` 자동 호출. `schema_hint`는 호출 컨텍스트에서 추론
- 장점: 전체 자동 적용
- 단점: schema_hint 추론 로직 필요. 무관한 경계에도 적용

**권장**: Phase 0-3에서 **전략 A**로 안정화 후, Phase 4에서 **전략 B**로 전환 검토.

### 3-4. Phase 계획 (파일/라인 추정)

| Phase | 작업 | 파일 수 | 추가 줄 | 선후관계 |
|-------|------|---------|---------|----------|
| **Phase 0** | `_normalize_output()` + Registry + 유틸 함수 | 1 (`base_agent.py`) | ~60줄 | 선행 필수 |
| **Phase 0-T** | 단위 테스트 (Gateway 함수 자체) | 1 (신규 테스트) | ~80줄 | Phase 0 후 |
| **Phase 1** | ArcEnsemble + ChiefWriter 적용 | 2 | 2줄 | Phase 0 후 |
| **Phase 1-T** | P0 경계 회귀 테스트 | 1 | ~40줄 | Phase 1 후 |
| **Phase 2** | BlueprintEnsemble + UnifiedArcValidator | 2 | 2줄 | Phase 1 후 |
| **Phase 3** | DirectorAuditor + Tier 2 잔여 | 5 | ~12줄 | Phase 2 후 |
| **Phase 4** | Tier 3~5 확산 (전략 결정 포함) | 15~20 | ~30줄 | Phase 3 안정화 후 |
| **Phase 5** | 추가 Pydantic 모델 정의 (ValidationResult, DirectorDecision) | 2 (models/) | ~60줄 | Phase 3 후 |

**전체 예상**: 25~30 파일, ~290줄 추가/수정. Phase 0-3까지 ~120줄.

---

## 4. TF-10 episode_details 통합

### 4-1. 문제 정의

TF-10 설계(Section 11)에서 확정된 `episode_details: list[dict]` 필드가 Arc에 추가될 예정. 이 필드는:

- LLM이 생성하므로 **없을 수 있음** (LLM이 무시)
- LLM이 잘못된 타입을 반환할 수 있음 (`str`, `dict`, `None`)
- 소비처(BlueprintConstraintCompiler)는 `list[dict]`를 기대

### 4-2. Gateway 통합 방안

`ArcData` Pydantic 모델에 필드 추가:

```python
# modules/models/arc.py ArcData 클래스에 추가
episode_details: list[dict] = Field(default_factory=list)
```

이 한 줄로 Gateway가 자동 보장하는 것:
1. **필드 없음** -> `[]` (빈 리스트)
2. **`None`** -> `[]` (Pydantic default)
3. **`str`** -> 검증 실패 -> graceful degradation으로 원본 유지 -> 소비처에서 `.get("episode_details", [])` 폴백
4. **`dict`** -> 검증 실패 -> graceful degradation -> 소비처 폴백
5. **`list[str]`** -> `extra="allow"` + list[dict] 검증 -> 아이템이 dict 아니면 실패 -> graceful degradation

### 4-3. 소비처 안전 패턴

```python
# blueprint_constraint_compiler.py _extract_episode_focus() 내부
details = arc_data.get("episode_details", [])
if not isinstance(details, list):
    details = []
# list[dict] 보장
details = [d for d in details if isinstance(d, dict)]
```

Gateway가 ArcData 검증을 통과하면 `episode_details`는 항상 `list`이지만, graceful degradation 경로에서는 원본이 그대로 내려올 수 있으므로 **이중 방어** 패턴 권장.

### 4-4. TF-10 Section 11과의 정합성

| TF-10 결정 | Gateway 반영 |
|------------|-------------|
| `dict[str, list[str]]` -> `list[dict]` 타입 변경 | `episode_details: list[dict] = Field(default_factory=list)` |
| ArcCorrector 수정 후 map 불일치 (EC-1) | Gateway는 파싱 후 타입만 보장. 의미적 불일치는 검증 체인(Phase 3-1~3-3) 담당 |
| ASP 경로 map 소실 (EC-2) | Gateway는 `default_factory=list`로 빈 리스트 보장. 소실 자체는 ASP 코드에서 방어 |
| Gemini response_schema 동적 키 미지원 | `list[dict]` 형태는 Gemini Schema에 표현 가능 (TF-10 대안 B) |

---

## 5. 리스크 목록

| # | 리스크 | 등급 | 설명 | 완화 방안 |
|---|--------|------|------|-----------|
| R1 | 평탄화 엔진과 Pydantic 충돌 | **HIGH** | `_extract_json_robust()`의 `process_node()` 평탄화가 중첩 dict를 파괴한 뒤 Pydantic에 전달하면, `state_constraints` 같은 중첩 필드가 소실됨 | Gateway를 `_extract_json_robust()` **이후** 삽입하되, 평탄화가 발동하지 않는 정상 경로(L1033 json.loads 성공)에서만 Pydantic 적용. 평탄화 경로(`process_node` 진입)에서는 schema_hint 무시 |
| R2 | graceful degradation 남용 | **MED** | 검증 실패 시 원본 반환이면 Gateway 효과가 "로깅만"으로 전락 | Phase 5에서 `strict=True` 옵션 추가. 핵심 경계(B1, B3)에서는 검증 실패 시 후보 탈락(기존 패턴과 동일) |
| R3 | schema_hint 오지정 | **MED** | 개발자가 잘못된 hint를 지정하면 엉뚱한 모델로 검증 | hint 없으면 패스스루. 테스트에서 hint-schema 매핑 검증 |
| R4 | `model_dump()` 후 extra 키 소실 | **LOW** | `extra="allow"`이지만 `model_dump()`가 extra 키를 포함하는지 확인 필요 | Pydantic v2 `model_dump()`는 `extra="allow"` 시 extra 키를 포함함 (검증 완료). 단, `by_alias=True` 등 옵션에 따라 달라질 수 있으므로 테스트 필수 |
| R5 | 성능 영향 | **LOW** | 65개 경계마다 Pydantic `model_validate()` 호출 시 지연 | Pydantic v2는 Rust 기반으로 매우 빠름 (<1ms/call). LLM API 호출(2-10초)에 비해 무시 가능 |
| R6 | BaseAgent 비대화 | **MED** | base_agent.py가 이미 1,403줄. Gateway 추가로 ~60줄 증가 | `_normalize_output()`은 얇은 디스패처. 실제 로직은 models/ 모듈에 위임. 향후 B-1 패턴으로 별도 모듈 추출 가능 |
| R7 | Director 주권 침해 가능성 | **LOW** | Gateway가 Director 출력을 수정하면 대원칙 #3 위반 | Gateway는 **타입 정규화만** 수행 (str->int 등). 판단(PASS/REJECT) 변경 불가. `decision` 값 자체는 건드리지 않음 |
| R8 | _extract_json_robust 내부 수정과 충돌 | **MED** | 향후 파서 개선 시 Gateway 가정이 깨질 수 있음 | Gateway는 파서 **이후**에 삽입되므로 파서 내부 변경에 독립적. 인터페이스(dict 반환)만 유지되면 됨 |

---

## 6. 컴팩트 이력서 (Compact Resume)

> 이 섹션은 컨텍스트 리셋 후에도 독립적으로 읽을 수 있도록 설계됨.

### TF-11: LLM Output Normalization Gateway

**문제**: 글도비 시스템의 22개 에이전트가 55회 LLM 호출 후 `_extract_json_robust()`로 JSON 파싱하지만, 반환된 dict의 **필드 타입/존재 여부를 검증하지 않는다** (65개 파싱 경계 중 Pydantic 적용은 3곳뿐 = 4.6%). `tactical_doc`이 dict로 오거나 `content`가 None이면 downstream에서 TypeError 발생.

**기존 자산**:
- `_extract_json_robust()` (base_agent.py L1000-1123): 4단계 JSON 파싱 + 자가 치유. **파싱은 충분, 타입 검증 부재**
- `response_schemas.py`: Gemini API 출력 강제 스키마 9개 정의. **analyst.py 1곳에서만 사용**
- `modules/models/`: Pydantic v2 모델 4개 (ArcData, Blueprint, ManuscriptCandidate, NPCEntry). **3곳에서만 사용**

**Gateway 설계**:
- `BaseAgent._normalize_output(raw, schema_hint)` 메서드 추가
- `_extract_json_robust()` 반환 이후에 삽입 (기존 코드 무파괴)
- `_SCHEMA_REGISTRY`로 schema_hint -> Pydantic 모델 매핑
- graceful degradation 유지 (검증 실패 시 원본 반환)

**TOP 5 우선 경계**:
1. **P0**: ArcEnsemble (`arc_ensemble.py:483`) -- Arc는 전체 파이프라인 SSOT
2. **P0**: ChiefWriter (`chief_writer.py:454`) -- 원고 생성, 이미 수동 타입 강제 존재
3. **P1**: BlueprintEnsemble (`blueprint_ensemble.py:435`) -- Stage 4 직접 입력
4. **P1**: UnifiedArcValidator (`unified_arc_validator.py:551`) -- PASS/REJECT 판정
5. **P2**: DirectorAuditor (`director_auditor.py:175,706,823,847,896`) -- 5개 경계

**Phase 계획**:
- Phase 0: base_agent.py에 Gateway 인프라 (~60줄)
- Phase 1: P0 경계 적용 (2파일, 2줄)
- Phase 2: P1 경계 적용 (2파일, 2줄)
- Phase 3: P2 경계 + Tier 2 잔여 (5파일, ~12줄)
- Phase 4: Tier 3~5 확산 결정
- Phase 5: 추가 Pydantic 모델 (ValidationResult, DirectorDecision)

**TF-10 통합**: `episode_details: list[dict] = Field(default_factory=list)`를 ArcData에 추가. Gateway가 타입 보장 + 빈 리스트 주입을 자동 처리.

**핵심 리스크**: R1(평탄화 엔진 충돌, HIGH), R2(graceful degradation 남용, MED), R6(BaseAgent 비대화, MED).

**수정 규모**: Phase 0-3까지 ~120줄, 전체 ~290줄. 기존 테스트 2,537개 무영향 (타입 검증 추가만, 기존 로직 변경 없음).

---

## 11. 3-시각 검토 결과 및 최종 결정

> 검토일: 2026-02-24
> 검토 방법: OPUS 독립 에이전트 3명 (코드 실독 기반)

### 11-1. 검토 A — 회의론 (Devil's Advocate)

**핵심 결론**: 수정 후 진행 (Gateway 방향은 유효하나 구현 방식 변경 필요)

**주요 반론**:
1. **ROI 과대 추정**: P0로 지정한 ArcEnsemble(B1)과 ChiefWriter(B3)는 이미 가장 두꺼운 방어 코드를 보유 (3-4중 방어). Gateway 추가 시 5번째 레이어가 될 뿐.
2. **BaseAgent 비대화**: 현재 1,402줄인 base_agent.py에 Gateway 책임 추가 시 6번째 책임이 됨. SRP 위반 심화.
3. **Graceful Degradation은 위험한 자기기만**: 검증 실패 시 원본 반환 패턴이 결국 버그를 무음 통과시킴.
4. **~120줄 추정 비현실적**: 실제 ~420줄 (코드 ~120 + 테스트 ~250 + 기존 조정 ~50).

**권장 대안** (3가지 경량 조치, ~100줄 총계):
- 대안 B: `_ensure_required_fields()` 패턴을 ChiefWriter/UnifiedArcValidator/DirectorAuditor에 복제 (~80줄)
- 대안 C: `response_schema` 확대 적용 (~5줄)
- TF-10 통합: `episode_details` 필드 추가 (1줄 + 테스트 ~10줄)

### 11-2. 검토 B — 아키텍처 관점

**핵심 결론**: 조건부 승인 (BLOCKER 해소 필수, 독립 모듈화 권장)

**BLOCKER 발견**:
- `_extract_json_robust()`는 `json.loads()` 성공 이후에도 `process_node(data)`를 **항상** L1117에서 호출. TF-11의 "정상 경로에서 평탄화 미발동" 가정이 틀렸음.
- 결과: Gateway에 전달되는 dict는 항상 이미 평탄화된 상태. 중첩 필드(`state_constraints` 내부 구조) 검증 불가.

**아키텍처 제안**:
- Gateway를 base_agent.py가 아닌 독립 `output_gateway.py` 모듈로 구현
- TF-10(episode_details)과 충돌 없음 (orthogonal)

### 11-3. 검토 C — 구현 리스크

**핵심 결론**: 선결 조건 해소 후 진행

**새로 발견된 위험**:

| # | 위험 | 심각도 | 설명 |
|---|------|--------|------|
| EC-2 | ASP 경로 Gateway 완전 우회 | HIGH | `four_phase_arc_generator.py` L370, L644 — 경계 맵에서 빠짐. Patch Mode ASP는 Phase 3 PASS 이후 실행 |
| EC-4 | 평탄화 항상 실행 (BLOCKER) | HIGH | json.loads 성공 후에도 process_node() 발동. Gateway가 이미 파괴된 구조를 검증 |
| EC-6 | content vs manuscript 필드명 불일치 | MED | LLM은 `content` 반환, ManuscriptCandidate는 `manuscript` 기대 |

**선결 조건 (구현 전 필수)**:
- P-1: `_extract_json_robust()` 평탄화 삽입 지점 재설계 (json.loads 성공 직후 Gateway 적용)
- P-2: ManuscriptCandidate 모델에 `content` 필드 추가 또는 alias 매핑
- P-3: ASP 경로 2곳을 경계 맵에 추가 (B26, B27)

**수정 범위 재추정**: Phase 0-3 ~190줄, 전체 ~360줄.

---

### 11-4. 3-시각 종합 판정

| 시각 | 판정 | 핵심 이유 |
|------|------|-----------|
| A (회의론) | 경량 대안 3가지로 대체 권장 | ROI 낮음, BaseAgent 비대화, 기존 방어 코드로 충분 |
| B (아키텍처) | 조건부 승인 — BLOCKER 해소 필수 | process_node 항상 실행 → 설계 전제 오류 |
| C (구현 리스크) | 선결 조건 3건 해소 후 진행 | ASP 누락, content/manuscript 불일치 |

### 11-5. 최종 결정: 경량 대안 채택 (POC 기간 기준)

**배경**: POC 기한 내 25화 원고 생산이 우선. Gateway 전면 도입은 BLOCKER 해소 + 설계 재작성 + 테스트 ~250줄이 필요하여 이번 사이클에서 부적합.

**채택된 조치** (TF-11 원안 대신):

1. **`response_schema` 확대 적용** (대안 C)
   - arc_ensemble.py / four_phase_arc_generator.py에 `ARC_DESIGN_SCHEMA` 적용
   - 추정: ~5줄

2. **ArcData에 `episode_details` 필드 추가** (TF-10 Phase 1과 병합)
   - `episode_details: list[dict] = Field(default_factory=list)`
   - 추정: 1줄

3. **ASP 경로 episode_details 복원** (TF-10 P2, 구현 완료)
   - `four_phase_arc_generator.py` L376, L651 — 원본 map 백업 후 복원 (~4줄)

4. **ArcCorrector 동기화** (TF-10 P3, 구현 완료)
   - `arc_corrector.py` 3곳 — tactical_doc 수정 성공 시 해당 화 episode_details 항목 삭제 (~6줄)

**Gateway 재도입 조건** (후순위):
- `process_node()` 평탄화를 opt-in으로 전환한 후
- BaseAgent에서 캐싱/키순환 로직을 분리한 후
- 위 조치 적용 후에도 타입 관련 프로덕션 버그가 반복될 경우

---

**문서 끝**
