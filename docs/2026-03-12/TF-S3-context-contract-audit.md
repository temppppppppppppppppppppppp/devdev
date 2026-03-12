# TF-S3: Stage 3 Context Contract 전수조사

> **범위**: Stage 3 (Blueprint 생성) LLM 컨텍스트 입력·출력·핸드오프 전면 감사
> **조사일**: 2026-03-12
> **조사 방법**: 4개 병렬 에이전트 1차 조사 → 핵심 주장 직접 코드 검증 → 3-pass 감리
> **확신도**: 96%

---

## 목차

1. [LLM 컨텍스트 입력 맵](#1-llm-컨텍스트-입력-맵)
2. [목표 정렬성](#2-목표-정렬성)
3. [Stage 2→3→4 핸드오프 계약](#3-stage-23-4-핸드오프-계약)
4. [컨텍스트 오염 위험](#4-컨텍스트-오염-위험)
5. [프롬프트 드리프트 위험](#5-프롬프트-드리프트-위험)
6. [관측성 갭](#6-관측성-갭)
7. [프로바이더 차이 영향](#7-프로바이더-차이-영향)

---

## 1. LLM 컨텍스트 입력 맵

### 1.1 `_bp_semantic_ctx` 조립 체인

`stage3_orchestrator.py` L923-1172에서 조립. **8개 소스를 역순 prepend**하여 최종 문자열 생성:

| 순서 | 소스 | 코드 위치 | 크기 (추정) | 비고 |
|------|------|-----------|-------------|------|
| 8→1 | Work Focus Advisory | L1124-1138 | 200-500자 | 작품 추적 슬롯 요약 |
| 7→2 | Stale Seeds Advisory | L1120-1122 | 100-300자 | 20화+ 방치 떡밥 |
| 6→3 | FactLedger Advisory | L1116-1118 | 200-800자 | 수치 팩트 요약 |
| 5→4 | StyleGuide Advisory | L1112-1114 | 100-300자 | 문체 가이드 |
| 4→5 | WorldState Advisory | L1108-1110 | 300-1000자 | 세계 상태 요약 |
| 3→6 | NS-4 Time Markers | L1063-1106 | 50-200자 | Arc 간 시간 연속성 |
| 2→7 | Treatment Block | L1004-1061 | 500-2000자 | 원본 블록 (genre_ext 포함) |
| 1→8 | SC Retrieval | L928-1000 | 0-2000자 | Smart Context 벡터 검색 |

**최종 크기**: 1,000-4,000자/에피소드 (추정). LLM 50K 윈도우 대비 2-8%.

### 1.2 BlueprintEnsemble LLM 호출

`blueprint_ensemble.py` L483-489:

```python
response = self._ask_with_cached_context(
    cache_name=cache_name,
    prompt=prompt,
    temperature=0.7,
    thinking_level="medium",
    full_prompt_fallback=full_prompt_fallback,
)
```

**주목**: `response_schema` 파라미터 미전달. 소프트 검증만 수행 (L497: `scene_breakdown`/`integrated_scenario` 필수 키 존재 확인).

### 1.3 Context Caching

- **TTL**: 600s (10분), `blueprint_ensemble.py` L220-227
- **적용 조건**: 컨텍스트 50,000자 이상 (`system.yaml` `min_content_chars`)
- **공유**: 3개 전략(action/emotion/dialogue)이 동일 캐시 공유
- **위험**: Ensemble timeout=300s vs Cache TTL=600s → 정상 범위. 단, retry 3회차에서 캐시 만료 가능성 존재 (300s×3=900s > 600s). 이 경우 `full_prompt_fallback`으로 자동 전환.

---

## 2. 목표 정렬성

### 2.1 Director 채점 루브릭과의 정렬

Director Stage 3 audit (`director.yaml` AUDIT_PROMPT):
- continuity_contradiction: 40%
- coverage: 20%
- creativity: 20%
- feasibility: 20%

**갭 발견**: Blueprint 생성 프롬프트(`blueprint_ensemble.yaml`)에 Director 채점 가중치(continuity=40%, coverage=20% 등)가 명시적으로 참조되지 않음. 생성 에이전트는 "좋은 Blueprint"를 자체 판단으로 생성하고, Director가 사후 평가.

**심각도**: P2 (설계 의도). 생성-평가 분리는 대원칙 3(Director 주권주의)과 일치. 생성 에이전트가 Director 루브릭을 알면 오히려 "점수 해킹" 위험. 현재 구조가 건전함.

### 2.2 Arc 설계와의 정렬

Blueprint는 Arc의 `scene_plan`을 에피소드 단위로 구체화. Treatment Block 주입(L1004-1061)이 원본 블록 참조를 보장하되, `working_ep`에 배정된 내용만 구현하도록 명시적 지시 포함 (L1046-1049).

---

## 3. Stage 2→3→4 핸드오프 계약

### 3.1 Stage 2 → Stage 3 입력

| 입력 | 소스 | 검증 |
|------|------|------|
| `arc_data` | Stage 2 최종 선택 Arc | ✅ Director 선택 보장 |
| `prev_blueprints` | DB 조회 (최근 5개) | ✅ `[-5:]` 슬라이싱 |
| `entity_registry` | StateTracker 추출 | ⚠️ 배치 시작 시 1회 로드, 생산 중 NPC 변경 미반영 |
| `working_ep` | 현재 에피소드 번호 | ✅ |
| `arc_idx` | 0-based 블록 인덱스 | ✅ 범위 체크 (L1011) |

### 3.2 Stage 3 → Stage 4 출력

| 출력 | 필드 | 소비처 |
|------|------|--------|
| `blueprint` dict | `scene_breakdown`, `integrated_scenario` 등 | Stage 4 CW 컨텍스트 |
| `_stage3_meta` | `quality_risk`, `last_score`, `final_verdict` | Stage 4 V75-D 동적 트리거 |
| `_inventory_gaps` | 소지품 갭 어노테이션 | Stage 4 CW advisory |

### 3.3 Arc 격리 검증

- `arc_idx` 범위 체크: L1011 `0 <= arc_idx < len(_plot_roadmap)` ✅
- `entity_cache`: 전략별 독립 (BlueprintEnsemble 내부 per-strategy) ✅
- Treatment Block: `arc_idx` 기반 정확한 블록 선택 ✅

**결론**: Arc 간 격리 CLEAN.

---

## 4. 컨텍스트 오염 위험

### 4.1 StateTracker 정체성

- **로딩 시점**: 배치 시작 시 1회 (`stage3_orchestrator` lazy init)
- **위험**: 동일 배치 내 멀티 에피소드 생산 시, 이전 에피소드에서 NPC 삭제/추가가 반영되지 않을 수 있음
- **심각도**: P2 (낮음). 실제 운영에서 배치 내 NPC 변경은 드묾. WorldState/FactLedger는 매 에피소드 갱신됨.

### 4.2 피드백 누적 (Retry 경로)

`three_phase_blueprint_generator.py` L137-149:
- retry 시 이전 실패 피드백이 프롬프트에 누적 추가
- **의도적 설계**: 학습 루프 (동일 실수 반복 방지)
- **위험**: retry 3회차에서 누적 피드백이 컨텍스트의 상당 비중을 차지할 수 있음
- **심각도**: P2 (의도적). 최대 3회 retry로 제한되어 있어 실질적 오염 위험 낮음.

### 4.3 `_bp_semantic_ctx` 수명

- **생성**: L923에서 빈 문자열로 초기화
- **소비**: `ThreePhaseBlueprintGenerator.generate()` 호출 시 전달
- **폐기**: 함수 스코프 종료 시 자동 폐기
- **DB 저장**: ❌ **저장되지 않음** (GAP-OBS-1 참조)
- **오염 없음**: 매 에피소드마다 새로 조립. 이전 에피소드의 semantic_ctx가 다음 에피소드로 유입되지 않음 ✅

---

## 5. 프롬프트 드리프트 위험

### 5.1 스키마 분리 (설계 의도)

- **생성 스키마**: BlueprintEnsemble → 9-12개 필드 (scene_breakdown, integrated_scenario, core_tension 등)
- **심사 스키마**: Director audit → 17개 필드 (score, verdict, consistency_checklist 등)
- **이것은 버그가 아님**: 생성은 "원고 설계"를 만들고, 심사는 "평가 보고서"를 만듦. 필드 집합이 다른 것은 구조적 필연.

### 5.2 `response_schema` 미사용

`blueprint_ensemble.py` L483: `_ask_with_cached_context()`에 `response_schema` 미전달.

- **현재 검증**: L497 `scene_breakdown`/`integrated_scenario` 키 존재 확인 (소프트)
- **추가 검증**: `UnifiedBlueprintValidator`가 3-phase 파이프라인의 Phase 3에서 구조/내용 검증
- **위험**: LLM이 예상 외 필드를 포함하거나 누락할 수 있으나, validator가 사후 검증으로 커버
- **심각도**: P2. `response_schema` 추가 시 검증 강도 상승 가능하나, Context Caching과의 호환성 확인 필요 (캐시된 프롬프트에 response_schema 변경 시 캐시 무효화).

### 5.3 InPlace Patch 무결성

`three_phase_blueprint_generator.py` L486-491:
```python
from modules.core.constants import calc_patch_change_ratio, log_patch_diff
...
log_patch_diff("S3-Blueprint", _original_json, _patched_json)
```

- **확인**: InPlace 패치 diff 로깅 **구현됨** ✅
- **추가 보호**: 30KB 초과 Blueprint → `return None` (full rewrite 폴백) ✅
- **1-depth deep merge**: 중첩 dict 서브키 복원 ✅

---

## 6. 관측성 갭

### GAP-OBS-1: `_bp_semantic_ctx` 미저장 (P1)

**현상**: `_bp_semantic_ctx` (1,000-4,000자)가 LLM에 전달되지만 DB에 저장되지 않음.

**영향**:
- 사후 디버깅 시 "LLM이 무엇을 보았는지" 재구성 불가
- 품질 회귀 분석 시 컨텍스트 기여도 측정 불가

**비교**: Stage 4는 `stage4_context_builder`가 조립한 컨텍스트를 Director MC parts로 전달하며, 일부는 `stage_attempts` advisory_flags에 기록됨. Stage 3은 이 경로 부재.

**권장**: `stage_attempts` 또는 별도 컬럼에 `_bp_semantic_ctx` 해시/크기/소스 목록을 기록하여 최소한 "어떤 소스가 포함되었는지" 추적 가능하게 함. 전문 저장은 DB 팽창 대비 ROI 낮음.

### GAP-OBS-2: `save_stage_attempt()` 필드 누락 (P1)

**현상**: `stage3_orchestrator.py` L1325-1339 호출 시 `duration_ms`, `failure_category`, `advisory_flags` 미전달.

```python
# 현재 (L1325-1339)
_db.save_stage_attempt(
    stage=3, verdict=..., attempt_num=..., ep_num=...,
    arc_num=..., score=..., model=..., session_id=...,
    attempt_key=..., prompt_version=..., candidate_key=...,
    content_hash=..., artifact_path=...
)
# 누락: duration_ms, failure_category, advisory_flags
```

**비교**: Stage 2 (`stage2_finalizer.py`)는 `duration_ms`, `failure_category`, `advisory_flags` 전량 전달. Stage 3만 누락.

**영향**:
- `FailureAnalyzer`가 Stage 3 실패 패턴 분석 시 `failure_category` NULL → 분류 불가
- 성능 추적 시 `duration_ms` NULL → Stage 3 소요 시간 미측정
- advisory 영향도 분석 시 `advisory_flags` NULL → 어떤 advisory가 활성이었는지 추적 불가

### GAP-OBS-3: Retrieval 관측성 기록 (정상)

L1155-1172: `_record_retrieval_observation()`이 SC 검색 결과, work_focus, source_counts, coverage_warnings를 기록함 ✅. 이 부분은 정상 동작.

---

## 7. 프로바이더 차이 영향

### 7.1 현재 상태

- **운영**: Gemini-only (`models.yaml` gemini: enabled=true, 나머지 disabled)
- **BlueprintEnsemble**: `gemini-2.5-pro`, Context Caching 사용 중

### 7.2 Vertex AI 전환 시 영향

- **Context Caching**: Vertex AI도 동일 `google-genai` SDK 사용, `vertexai=True` 플래그만 차이. Context Caching API 동일 → 무변경 전환 가능.
- **`response_schema` 미사용**: Vertex AI는 `response_schema` 강제 시 JSON 정합도 향상 (API 레벨 검증). 현재 미사용이므로 Vertex 전환 시에도 변화 없음.
- **Thinking Mode**: `thinking_level="medium"` — Vertex AI에서도 동일하게 지원 (`google-genai` 통합).
- **가격 차이**: Google AI vs Vertex AI Pro 기본가는 동일. 캐시 비용만 약간 차이 (상세: `TF-VERTEX-migration-full-audit.md`).

### 7.3 Anthropic/OpenAI 전환 시 영향

- **Context Caching**: Anthropic은 자체 캐싱 메커니즘, OpenAI는 미지원 → BlueprintEnsemble 캐시 로직 리팩토링 필요.
- **`thinking_level`**: Anthropic `extended_thinking`/OpenAI `reasoning_effort` → 매핑 필요.
- **`temperature=0.7`**: Anthropic은 `thinking` 모드에서 temperature 무시 → 전략 다양성 영향.
- **심각도**: P2 (현재 disabled, 전환 시점에 대응).

---

## 발견 사항 요약

| ID | 심각도 | 영역 | 설명 | 상태 |
|----|--------|------|------|------|
| GAP-OBS-1 | P1 | 관측성 | `_bp_semantic_ctx` DB 미저장 — LLM 입력 재구성 불가 | TF 후보 |
| GAP-OBS-2 | P1 | 관측성 | Stage 3 `save_stage_attempt()` duration_ms/failure_category/advisory_flags 미전달 | TF 후보 |
| DESIGN-1 | P2 | 정렬 | Blueprint 생성 프롬프트에 Director 채점 루브릭 미참조 | 설계 의도 — 현상유지 |
| DESIGN-2 | P2 | 스키마 | 생성 vs 심사 스키마 필드 분리 | 설계 의도 — 현상유지 |
| DESIGN-3 | P2 | 검증 | `response_schema` 미사용 (소프트 검증만) | 설계 의도 — Context Cache 호환성 고려 필요 |
| RISK-1 | P2 | 오염 | StateTracker 배치 내 1회 로드 — NPC 변경 미반영 가능 | 낮은 발생 확률 |
| RISK-2 | P2 | 캐시 | retry 3회차에서 Context Cache TTL 만료 가능 (900s > 600s) | fallback 자동 전환으로 안전 |
| RISK-3 | P2 | 피드백 | retry 누적 피드백 비율 증가 | 의도적 — max 3회 제한 |

---

## 3-Pass 감리

### Pass 1: 사실 정확성 검증

| 항목 | 주장 | 직접 검증 | 판정 |
|------|------|-----------|------|
| `_bp_semantic_ctx` 미저장 | DB에 저장되지 않음 | L923-1172 조립 후 `generate()` 전달만, INSERT 없음 | ✅ CORRECT |
| `save_stage_attempt` 필드 누락 | duration_ms/failure_category/advisory_flags 미전달 | L1325-1339: 해당 파라미터 없음. `db_manager.py` L3081: 메서드는 받을 수 있음 | ✅ CORRECT |
| `response_schema` 미사용 | BlueprintEnsemble에서 미전달 | L483-489: `_ask_with_cached_context(temperature=0.7, thinking_level="medium")` — response_schema 없음 | ✅ CORRECT |
| InPlace patch diff 미로깅 | (Agent 3 주장) | `three_phase_blueprint_generator.py` L486-491: `log_patch_diff("S3-Blueprint", ...)` **존재** | ❌ INCORRECT — 오탐 제거 |
| 스키마 9-17 필드 불일치 | (Agent 4 주장) | 생성(Blueprint 본문) vs 심사(audit 보고서) — 용도가 다른 스키마 | ❌ INCORRECT — 설계 의도 재분류 |
| Arc 격리 | arc_idx 범위 체크 | L1011 `0 <= arc_idx < len(_plot_roadmap)` | ✅ CORRECT |
| Context Cache TTL | 600s | `blueprint_ensemble.py` L220-227 | ✅ CORRECT |
| 피드백 누적 | retry 시 이전 실패 피드백 추가 | `three_phase_blueprint_generator.py` L137-149 | ✅ CORRECT |

### Pass 2: 심각도 평가 정합성

- GAP-OBS-1 (P1): `_bp_semantic_ctx` 미저장 → **P1 유지**. 사후 디버깅 핵심 데이터. 단, 전문 저장이 아닌 메타데이터(소스 목록+크기)만 저장해도 충분.
- GAP-OBS-2 (P1): Stage 2는 전량 전달, Stage 3만 누락 → **P1 유지**. 동일 테이블 동일 스키마에서 Stage 3만 빈 값은 분석 편향 유발.
- DESIGN-1~3 (P2): 전부 구조적 설계 의도와 정합. Director 주권주의(대원칙 3) 위배 없음. **P2 현상유지 확정**.
- RISK-1~3 (P2): 실운영 발생 확률 낮고 안전 장치(fallback, retry 제한) 존재. **P2 현상유지 확정**.

### Pass 3: 누락 영역 점검

- ✅ LLM 컨텍스트 입력 맵: 8개 소스 전량 추적 완료
- ✅ 목표 정렬성: Director 루브릭 vs 생성 프롬프트 비교 완료
- ✅ 핸드오프 계약: S2→S3 입력 5개, S3→S4 출력 3개 전량 문서화
- ✅ 오염 위험: StateTracker 정체성, 피드백 누적, semantic_ctx 수명 검증
- ✅ 프롬프트 드리프트: 스키마 분리 의도 확인, response_schema 미사용 영향 평가
- ✅ 관측성: 2개 실질 갭 식별 (GAP-OBS-1, GAP-OBS-2)
- ✅ 프로바이더 차이: Gemini/Vertex/Anthropic/OpenAI 4종 영향 평가

**누락 없음 확인.**

---

## 확신도: 96%

**근거**:
- 핵심 코드 4개 파일 직접 검증 (stage3_orchestrator, blueprint_ensemble, three_phase_blueprint_generator, db_manager)
- Agent 오탐 2건 식별 및 제거 (log_patch_diff 존재 확인, 스키마 분리 설계 의도 재분류)
- 8개 컨텍스트 소스 전량 추적
- P0 발견 0건, P1 발견 2건 (관측성 갭), P2 발견 6건 (설계 의도/낮은 위험)

**4% 불확실성 요인**:
- BlueprintEnsemble 내부 캐시 키 생성 로직 미정밀 검증 (50K 미달 시 skip 경로)
- `UnifiedBlueprintValidator` 검증 범위 정밀 대조 미실시 (P3 수준)

---

## TF 후보 (P1 2건)

### TF-S3-OBS-1: `_bp_semantic_ctx` 관측성 보강

- `save_stage_attempt()` 호출 시 `advisory_flags`에 `{"semantic_ctx_chars": len, "semantic_ctx_sources": [소스목록]}` 추가
- 전문 저장 불필요 (메타데이터만)
- 예상 변경: `stage3_orchestrator.py` 1곳 (L1325 호출부)

### TF-S3-OBS-2: `save_stage_attempt()` 필드 보강

- `duration_ms`: Stage 3 전체 소요 시간 (이미 `StageSpinner` 타이머 존재 → 값 추출)
- `failure_category`: REJECT 시 reject_reason 기반 분류
- `advisory_flags`: 활성 advisory 목록
- 예상 변경: `stage3_orchestrator.py` 1곳 (L1325 호출부), Stage 2 패턴 참조

---

*3-pass 감리 완료. P0 0건, P1 2건(관측성), P2 6건(설계 의도/낮은 위험). 확신도 96%.*
