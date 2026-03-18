# 비용 테이블 + ROL 복합 지표 정의서

**문서 유형**: 빌드업 (S7-G3/G4 선행 정의)
**작성일**: 2026-03-18
**상태**: DEFINITION — 코드 미착수
**감리**: 3회 전면 재조사 + 적대적 3-pass 완료 (6 TF 병렬 투입)
**교정 이력**: 초판 3건 허위 → 2차 교정 → **3차 thinking 비용 합산 확정, ScoringValidator 가중 채점 발견**

---

## 1. 현행 비용 테이블

### 1.1 `metrics_collector.py` MODEL_COSTS (현행, 2026-03-12 교정 완료)

```python
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50, "cache_read": 0.03},
    "gemini-2.5-pro":   {"input": 1.25, "output": 10.00, "cache_read": 0.125},
    "default":          {"input": 1.25, "output": 10.00, "cache_read": 0.125},
}
```

교정 이력: 커밋 `19505108` (2026-03-12) — Flash input 0.15→0.30, Flash output 0.60→2.50, Pro output 5.00→10.00

### 1.2 미반영 사항 (S7-G3 업데이트 대상)

| 항목 | 현행 | 실제 | 영향 |
|------|------|------|------|
| **Claude Opus 4.6** | 미등록 | input $5.00 / output $25.00 / cache $0.50 | 멀티프로바이더 전환 시 필수 |
| **Claude Sonnet 4.6** | 미등록 | input $3.00 / output $15.00 / cache $0.30 | 멀티프로바이더 전환 시 필수 |
| **Gemini >200K 구간** | 미구분 | input $2.50 / output $15.00 (2x) | 장문 에피소드에서 과소 추정 |

### 1.3 Thinking 토큰 추적 현황 (초판 오류 교정)

> **초판 주장**: "Thinking 토큰 완전 미추적" → **거짓. 이미 추적 중.**

| 위치 | 추적 방식 |
|------|----------|
| `metrics_collector.py:39` | `AgentMetric.thinking_tokens: int = 0` |
| `metrics_collector.py:215,240` | `end_call(thinking_tokens=...)` 파라미터 |
| `base_agent.py:432` | `usage.get("thoughts_token_count")` 실측 추출 |
| `base_agent.py:583` | `thinking_tokens=_usage_payload["thinking_tokens"]` 전달 |
| `db_manager.py:604` | `thinking_tokens INTEGER` DB 컬럼 |

**3차 재조사 확정**: `metrics_collector.py:300` 주석에 **"출력 토큰 수 (Developer API: thinking 토큰 포함)"** 명시. Gemini Developer API에서 `candidates_token_count`는 thinking 토큰을 이미 합산한 값. 따라서:
- `calculate_cost()`의 `output_cost = (output_tokens / 1M) × output_price`에 thinking 비용이 **이미 포함**됨
- `thinking_tokens` 필드는 **분석/디버깅용 별도 추적**이지, 추가 과금 대상 아님
- **초판 "완전 미추적" 주장 거짓, 2차 "비용 계산 미반영" 주장도 부정확 → thinking 비용은 output에 이미 합산**

### 1.4 업데이트 목표 테이블

```python
MODEL_COSTS = {
    # Gemini (현행)
    "gemini-2.5-flash": {
        "input": 0.30, "output": 2.50, "cache_read": 0.03,
        "input_200k_plus": 0.60, "output_200k_plus": 5.00,
    },
    "gemini-2.5-pro": {
        "input": 1.25, "output": 10.00, "cache_read": 0.125,
        "input_200k_plus": 2.50, "output_200k_plus": 15.00,
    },
    # Claude (신규)
    "claude-opus-4-6": {
        "input": 5.00, "output": 25.00, "cache_read": 0.50,
        "batch_discount": 0.50,
    },
    "claude-sonnet-4-6": {
        "input": 3.00, "output": 15.00, "cache_read": 0.30,
        "batch_discount": 0.50,
    },
    "default": {"input": 1.25, "output": 10.00, "cache_read": 0.125},
}
```

---

## 2. 토큰 추정 정확도

### 2.1 현행 (휴리스틱)

```python
# metrics_collector.py:287-290
korean_chars / 1.5 + other_chars / 4
# 오차: ±15-20%
```

### 2.2 실측 우선 전략

`_last_llm_usage`에 실측값 저장 중 (`base_agent.py:386`) → `metrics_collector.end_call()`에 전달 (`base_agent.py:583`).

**현재 상태**: 실측 토큰이 있으면 사용, 없으면 휴리스틱 폴백. 이미 구현됨.

### 2.3 한국어 토크나이저 효율 (외부 참조 — 미검증)

> **초판 오류 교정**: 이 수치는 외부 웹 자료에서 인용한 것이며, 코드베이스 내 실측 데이터 아님. 참고용으로만 사용.

| 모델 | chars/token (외부 자료) | 비고 |
|------|----------------------|------|
| DeepSeek | ~2.02 | CJK 최적화 |
| Qwen | ~1.5-1.8 | 중국어 최적화 |
| Claude | ~1.25 | 코드베이스 휴리스틱: 1.5 |
| GPT | ~1.0-1.2 | - |
| Gemini | ~0.82 | SentencePiece |

**코드베이스 내 유일한 측정값**: `korean_chars / 1.5` (모델 무관 단일 휴리스틱)
**실측 검증 방법**: 동일 텍스트를 각 프로바이더에 보내고 `usage.input_tokens` 비교 → 이후 과제.

---

## 3. ROL 복합 지표 정의 (S7-G4)

### 3.1 ROL (Return on LLM) 정의

> **초판 오류 교정**: 아래 공식은 **제안**임. 현재 코드에 복합 품질 점수 계산 로직이 없으므로 즉시 구현 불가. 구현 전제조건을 명시.

**에피소드 단위 ROL**:
```
ROL(ep) = Quality(ep) / Cost(ep)
```

### 3.2 Quality(ep) — 현재 사용 가능한 데이터

| 지표 | 데이터 소스 | 현재 수집 상태 |
|------|-----------|--------------|
| director_score | `quality_metrics.jsonl` validation 이벤트 | O — `score` 필드 |
| validation_score | `validation_orchestrator.py` 반환값 | O — `score` 필드 |
| rejection_rate | `pass_rate_monitor.json` | O — `success` 필드로 계산 |
| advisory_pass_rate | `advisory_validator.py` 결과 | **부분** — 개별 advisory 결과 있으나 집계 없음 |

**현재 존재하는 가중 채점 시스템**:
- `DirectorGradingSystem` (`director_grading.py:65-72`): structure 0.15, prose 0.15, consistency 0.25, engagement 0.15, commercial 0.20, satisfaction 0.10
- `ScoringValidator` (`scoring_validator.py:50-57`): character_consistency 15, emotion_arc 15, dialogue_quality 15, commercial_appeal 15, pattern_diversity 10, reader_satisfaction 10

**이들은 에피소드 내 세부 항목 채점이며, 에피소드 간 복합 점수가 아님.**

**3차 재조사 추가 발견** — `ScoringValidator`에 장르별 가중 채점 시스템 존재 (`scoring_validator.py:751-937`):
- 장르별 항목 가중치 (예: wuxia → prose_rhythm 1.2x, sensory_balance 1.3x)
- `weighted_percentage = weighted_total / weighted_max_total × 100`
- `genre_delta` cap ±1점 적용
- **즉, 에피소드 내 품질 점수는 이미 가중 계산됨**. ROL의 `validation_score` 축으로 직접 사용 가능.
- 다만 `director_score` + `validation_score` + `rejection_rate` + `advisory_pass_rate`를 하나로 묶는 **에피소드 간 복합 공식은 여전히 미존재**.

### 3.3 제안 ROL 복합 공식

```
Quality(ep) = 0.4 × director_score
            + 0.3 × validation_score
            + 0.2 × (1 - rejection_rate) × 100
            + 0.1 × advisory_pass_rate × 100
```

**구현 전제조건**:
1. `pass_rate_monitor.json`에서 에피소드별 rejection_rate 집계 함수 필요
2. advisory 통과율 집계 함수 필요
3. 복합 점수 계산 + 저장 모듈 필요 (현재 미존재)

### 3.4 Cost(ep) — 현재 사용 가능한 데이터

```
Cost(ep) = Σ (input_tokens × input_price + output_tokens × output_price
             + cached_tokens × cache_price)
         across all LLM calls for this episode
```

| 데이터 | 소스 | 수집 상태 |
|--------|------|----------|
| 에이전트별 토큰 사용량 | `metrics_collector.py` | O — 실측 |
| 모델별 단가 | `MODEL_COSTS` | O — Gemini만 |
| 에피소드 단위 집계 | `snapshot_and_reset_scope()` | O |

**Stage 2/3 token_cost 누락**: `pass_rate_monitor.record_attempt()` 호출 시 `token_cost` 파라미터 미전달 (기본값 0.0). 단, `metrics_collector`에는 별도 경로로 토큰 비용이 추적됨. `pass_rate_monitor`의 token_cost 필드만 0.0.

### 3.5 ROL 등급표 (제안)

| 등급 | ROL 범위 | 의미 |
|------|---------|------|
| **S** | > 200 | 극효율 (품질 80+ / 비용 < $0.40) |
| **A** | 150-200 | 고효율 |
| **B** | 100-150 | 정상 |
| **C** | 50-100 | 개선 필요 |
| **D** | < 50 | 비용 대비 품질 심각 |

---

## 4. 시뮬레이션 도구 가격 갱신 (S7-G3)

### `tools2/` 현행 vs 교정 필요값

| 변수 | `tools2/` 현행 | `metrics_collector.py` 교정값 | 차이 |
|------|--------------|---------------------------|------|
| Flash input | $0.075/MTok | $0.30/MTok | **4x 과소** |
| Flash output | $0.30/MTok | $2.50/MTok | **8.3x 과소** |
| Pro output | $5.00/MTok | $10.00/MTok | **2x 과소** |
| 환율 | 1300 | 1300 | 동일 |

**tools2/ 스크립트 교정은 데이터 파일 업데이트이므로 코드 수정에 해당하지 않음** → 즉시 실행 가능.
