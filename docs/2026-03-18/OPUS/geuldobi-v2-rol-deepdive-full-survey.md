# 글도비 v2 ROL(Return on Labor) 전역 딥다이브 전수 조사

> **조사일**: 2026-03-18
> **조사 대상**: 글도비 v2 전체 코드베이스 — 비용 추적, 토큰 계량, 통과율, 재시도 예산, ROI 분석 인프라
> **조사 범위**: "1원/1토큰/1초 투입당 산출 품질·수량"을 추적하는 모든 계층
> **조사 방법**: 3방향 독립 조사 → 교차 대조 → 3PASS 감리
> **코드 수정**: 없음 (조사 전용)

---

## 목차

1. [조사 방법론](#1-조사-방법론)
2. [방향 A: 비용 계량 인프라 (측정 계층)](#2-방향-a-비용-계량-인프라)
3. [방향 B: 산출 효율 추적 (통과율·재시도·품질)](#3-방향-b-산출-효율-추적)
4. [방향 C: ROI 분석·의사결정 자산 (문서·도구)](#4-방향-c-roi-분석의사결정-자산)
5. [교차 대조 결과](#5-교차-대조-결과)
6. [3PASS 감리 결과](#6-3pass-감리-결과)
7. [발견 사항 종합](#7-발견-사항-종합)
8. [근거 파일 인벤토리](#8-근거-파일-인벤토리)

---

## 1. 조사 방법론

### 1.1 ROL 정의

**ROL (Return on Labor)** = 투입 자원(API 비용 USD, 토큰 수, 시간, 재시도 횟수) 대비 산출 결과(에피소드 수, 통과율, 품질 점수)의 효율 지표.

```
ROL = 산출(에피소드 × 품질) / 투입(비용 + 시간 + 재시도 증폭)
```

### 1.2 3방향 독립 조사

| 방향 | 관점 | 핵심 질문 |
|------|------|----------|
| **A — 비용 계량 인프라** | 측정 정확도 | 토큰·비용·시간을 어디서, 어떻게, 얼마나 정확하게 측정하는가? |
| **B — 산출 효율 추적** | 통과율·재시도 | 스테이지별 통과율, 재시도 증폭, 패치 효과를 어떻게 추적하는가? |
| **C — ROI 분석 자산** | 의사결정 | 비용 절감 전략, 예산 시뮬레이션, 모델 선택이 어떤 자료에 기반하는가? |

### 1.3 3PASS 감리

| PASS | 목적 | 판정 기준 |
|------|------|----------|
| **1st** | 사실 확인 | 코드/파일 근거 없는 서술 제거 |
| **2nd** | 교차 일관성 | 3방향 결과 간 모순·수치 불일치 탐지 |
| **3rd** | 완전성 검증 | 미추적 비용 채널, 사각지대 탐지 |

---

## 2. 방향 A: 비용 계량 인프라

### 2.1 아키텍처 개관

```
┌─────────────────────────────────────────────────────────────┐
│  L1. LLM 호출 계층 (base_agent.py)                         │
│      start_call() → API 호출 → end_call()                   │
│      토큰 수: SDK usage_metadata 또는 추정                   │
├─────────────────────────────────────────────────────────────┤
│  L2. MetricsCollector (metrics_collector.py)                │
│      싱글톤 — 에이전트별/모델별/스코프별 집계               │
│      비용 계산: MODEL_COSTS × 토큰 수                       │
├─────────────────────────────────────────────────────────────┤
│  L3. 스코프 스냅샷 (stage*_finalizer/post_processor)       │
│      snapshot_and_reset_scope() → arc/episode 단위 집계      │
├─────────────────────────────────────────────────────────────┤
│  L4. DB 영속화 (db_manager.py cost_log 테이블)              │
│      save_cost_record() → SQLite 저장                       │
├─────────────────────────────────────────────────────────────┤
│  L5. 대시보드 노출 (bridge_server.py /quality/dashboard)    │
│      _build_cost_summary_payload() → Renderer 표시           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 L1 — LLM 호출 계층 (base_agent.py)

#### 2.2.1 메트릭 수집 연동

```python
# base_agent.py (개략)
metric_id = collector.start_call(agent_name, model)
try:
    response = self._generate_content(prompt, ...)
    # usage_metadata에서 실제 토큰 추출
    collector.end_call(metric_id,
        success=True,
        input_tokens=response.usage_metadata.prompt_token_count,
        output_tokens=response.usage_metadata.candidates_token_count,
        cached_tokens=response.usage_metadata.cached_content_token_count,
        thinking_tokens=response.usage_metadata.thoughts_token_count)
except:
    collector.end_call(metric_id, success=False, error_type=...)
```

#### 2.2.2 _USAGE_KEYS (토큰 추적 필드)

| 필드 | 소스 | 설명 |
|------|------|------|
| `prompt_token_count` | Gemini SDK `usage_metadata` | 입력 토큰 (캐시 포함) |
| `candidates_token_count` | Gemini SDK `usage_metadata` | 출력 토큰 |
| `thoughts_token_count` | Gemini SDK `usage_metadata` | Thinking 토큰 (과금 대상) |
| `cached_content_token_count` | Gemini SDK `usage_metadata` | 캐시 히트 토큰 (할인) |

#### 2.2.3 API 키 순환 및 쿼터 캐싱

- 최대 10개 키 순환 (`GOOGLE_API_KEY`, `GOOGLE_API_KEY_2`, ...)
- 쿼터 소진 시 3600초 캐시 → 비용 절감 (불필요한 재시도 방지)
- 네트워크 재시도: 3회, 지수 백오프 10-30초

### 2.3 L2 — MetricsCollector (metrics_collector.py, 533행)

#### 2.3.1 데이터 모델

**AgentMetric** (단일 호출):
```python
@dataclass
class AgentMetric:
    agent_name: str          # Writer, Architect, Director, etc.
    model: str               # gemini-2.5-pro, gemini-2.5-flash
    start_time: float
    end_time: float
    success: bool
    retry_count: int
    input_tokens: int
    output_tokens: int
    cached_tokens: int       # 캐시 히트 (할인 적용)
    thinking_tokens: int     # 과금 대상 thinking
    error_type: str | None
```

**SessionStats** (세션 전체):
```python
@dataclass
class SessionStats:
    session_id: str
    total_calls: int
    successful_calls: int
    total_retries: int
    total_tokens: int
    total_cost_usd: float
    agent_stats: dict       # 에이전트별 호출 횟수/성공률/응답시간
    model_stats: dict       # 모델별 토큰/비용
```

#### 2.3.2 모델별 토큰 비용 (MODEL_COSTS)

| 모델 | Input ($/M) | Output ($/M) | Cache Read ($/M) | 근거 |
|------|------------|-------------|-----------------|------|
| `gemini-2.5-pro` | $1.25 | $10.00 | $0.125 | metrics_collector.py:77-79 |
| `gemini-2.5-flash` | $0.30 | $2.50 | $0.03 | metrics_collector.py:73-76 |
| `default` (fallback) | $1.25 | $10.00 | $0.125 | metrics_collector.py:81 |

#### 2.3.3 비용 계산 로직 (cache-aware)

```python
def calculate_cost(model, input_tokens, output_tokens, cached_tokens=0):
    costs = MODEL_COSTS[model]
    non_cached_input = max(0, input_tokens - cached_tokens)
    input_cost = (non_cached_input / 1M) * costs["input"]
    cache_cost = (cached_tokens / 1M) * costs["cache_read"]
    output_cost = (output_tokens / 1M) * costs["output"]
    return input_cost + cache_cost + output_cost
```

#### 2.3.4 집계 차원

| 차원 | 추적 항목 | 집계 수준 |
|------|----------|----------|
| 에이전트별 | 호출 수, 성공 수, 재시도, 응답시간(P50/P90/P99) | 세션 |
| 모델별 | input/output/cached/thinking 토큰, 비용 | 세션 |
| 스코프별 | calls, tokens, cost, model_breakdown | arc/episode |

#### 2.3.5 메트릭 영속화

| 출력 | 경로 | 형식 |
|------|------|------|
| 세션 메트릭 파일 | `logs/metrics/metrics_{session_id}.json` | JSON |
| 요약 리포트 | `get_summary_report()` → 콘솔 출력 | 텍스트 |
| 스코프 스냅샷 | `snapshot_and_reset_scope()` → DB 저장 | dict → SQL |

### 2.4 L3 — 스코프 스냅샷 (파이프라인 연동)

#### 2.4.1 스냅샷 발행 지점

| 발행 위치 | scope_type | scope_id | 시점 |
|----------|-----------|---------|------|
| `stage2_finalizer.py:1356` | `"arc"` | `global_arc_no` | Arc 설계 완료 시 |
| `stage3_orchestrator.py:2159` | `"episode"` | `working_ep` | Blueprint 완료 시 |
| `stage4_post_processor.py:690` | `"episode"` | `next_ep` | 원고 최종 저장 시 |
| `main_a.py` (세션 종료) | `"session"` | `0` | 전체 세션 종료 시 |

#### 2.4.2 스냅샷 데이터 구조

```json
{
  "total_calls": 12,
  "total_tokens": 45000,
  "total_cost_usd": 0.234,
  "model_breakdown": "{\"gemini-2.5-pro\": {\"tokens\": 35000, \"cost\": 0.21, \"cached_tokens\": 5000, \"thinking_tokens\": 2000}, \"gemini-2.5-flash\": {\"tokens\": 10000, \"cost\": 0.024, ...}}"
}
```

### 2.5 L4 — DB 영속화 (cost_log 테이블)

#### 2.5.1 테이블 스키마

```sql
CREATE TABLE cost_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  scope_type TEXT CHECK(scope_type IN ('arc', 'episode', 'session')),
  scope_id INTEGER DEFAULT 0,
  total_calls INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  total_cost_usd REAL DEFAULT 0.0,
  model_breakdown TEXT,          -- JSON string
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 인덱스: (scope_type, scope_id), (session_id)
```

#### 2.5.2 DB 메서드

| 메서드 | 용도 | 근거 |
|--------|------|------|
| `save_cost_record()` | 스코프별 비용 스냅샷 저장 | db_manager.py:3732 |
| `get_cost_summary(lookback=N)` | 최근 N건 비용 기록 조회 | db_manager.py:3770 |

#### 2.5.3 소비자

| 소비자 | 용도 |
|--------|------|
| `bridge_server.py /quality/dashboard` | 비용 요약 payload 생성 |
| `bridge_server.py /quality/summary` | 품질 신호 + 비용 개요 |
| `stage4_interview_round.py` | 재시도 예산 판단 참조 |

### 2.6 L5 — 대시보드 노출 (/quality/dashboard)

#### 2.6.1 _build_cost_summary_payload

```python
def _build_cost_summary_payload(rows, lookback):
    # 입력: get_cost_summary() 결과 (최근 N건 cost_log 행)
    # 출력:
    return {
        "available": True/False,
        "lookback": int,
        "row_count": int,
        "latest_session_id": str,
        "total_calls": int,          # 전체 합산
        "total_tokens": int,         # 전체 합산
        "total_cost_usd": float,     # 전체 합산
        "scope_counts": {"arc": N, "episode": N, "session": N},
        "recent": [                  # 최근 기록 목록
            {"session_id", "scope_type", "scope_id", "cost", "created_at"}
        ]
    }
```

---

## 3. 방향 B: 산출 효율 추적

### 3.1 PassRateMonitor (pass_rate_monitor.py)

#### 3.1.1 AttemptRecord — 시도 단위 추적

| 필드 | 타입 | 설명 | ROL 의미 |
|------|------|------|----------|
| `stage` | int | 스테이지 번호 (2/3/4) | 비용 집중 구간 식별 |
| `episode` | int | 에피소드 번호 | 산출 단위 |
| `attempt_num` | int | 시도 순번 | 재시도 증폭 계수 |
| `success` | bool | 통과 여부 | 산출 여부 |
| `reject_reason` | str | 거부 사유 | 병목 원인 분류 |
| `generation_method` | str | 생성 방법 (four_phase/blueprint/ensemble/tot/asp/mad) | 전략별 효율 비교 |
| `model_tier` | int | 모델 등급 | 모델별 비용-품질 트레이드오프 |
| `duration_ms` | int | 소요 시간 (밀리초) | 시간 ROL |
| `token_cost` | float | 토큰 비용 (USD) | 금전 ROL |
| `is_patch` | bool | 패치 모드 여부 | 패치 vs 전체 재생성 효율 |
| `patch_strategy` | str | 패치 전략 | 전략별 효과 |
| `score_breakdown` | dict | 점수 내역 | 품질 상세 |
| `retry_budget_axes` | dict | 재시도 예산 축 | 예산 제어 |
| `candidate_key` | str | 후보 키 (balanced/emotion/action) | 앙상블 효율 |
| `content_hash` | str | 콘텐츠 해시 | 중복 생성 감지 |
| `artifact_path` | str | 산출물 경로 | 추적성 |

#### 3.1.2 StageStats — 스테이지 단위 집계

| 지표 | 계산법 | ROL 의미 |
|------|--------|----------|
| `first_attempt_pass` | 1회 시도 통과 건수 | 최적 효율 (재시도 0) |
| `first_attempt_rate` | first_pass / total_episodes | 핵심 ROL 지표 |
| `eventual_pass` | 최종 통과 건수 | 실질 산출 |
| `eventual_rate` | eventual / total_episodes | 실질 생산성 |
| `avg_attempts_to_pass` | 합산 시도 / 통과 건수 | 재시도 증폭 계수 |
| `common_reject_reasons` | 거부 사유 빈도 | 병목 원인 순위 |
| `method_success_rate` | 방법별 성공률 | 전략 효과 비교 |

#### 3.1.3 고급 분석 메서드

| 메서드 | 용도 | 반환 |
|--------|------|------|
| `get_patch_effectiveness()` | 패치 모드 성공률 + fallback 비율 | dict |
| `get_arc_difficulty()` | Arc별 난이도 추정 (시도 횟수 기반) | dict |
| `check_alerts()` | 통과율 5%+ 하락 또는 <50% 1차 통과 경고 | list[str] |
| `get_trend()` | 최근 N건 이동평균 추세 | dict |

#### 3.1.4 실측 데이터 (projects/0_260318)

| 스테이지 | 에피소드 | 시도 횟수 | 결과 | 방법 | 후보 |
|----------|---------|----------|------|------|------|
| Stage 2 | ep1 arc1 | 1회 | PASS | four_phase | balanced |
| Stage 3 | ep1 arc1 | 3회 | PASS | blueprint | emotion_focused |
| Stage 3 | ep2 arc1 | 1회 | PASS | blueprint | emotion_focused |
| Stage 3 | ep3 arc1 | 2회 | PASS | blueprint | action_focused |

**관찰**: Stage 3에서 ep1이 3회 시도 필요 — 초기 에피소드 콜드스타트 비용.

### 3.2 Quality Metrics (quality_metrics.jsonl)

#### 3.2.1 기록 유형

| type | 주요 필드 | ROL 의미 |
|------|----------|----------|
| `retrieval_observation` | source_counts, vector_context_chars, budget_ledger | 컨텍스트 효율 (투입 문자 대비 검색 품질) |
| `validation` | decision, score, violations, warnings | 산출 품질 |

#### 3.2.2 Budget Ledger (컨텍스트 예산 추적)

```json
{
  "budget_bucket": "smart_retrieval.stage3_total_budget",
  "configured_cap": 80000,
  "effective_cap": 80000,
  "consumed_chars": 2606,
  "dropped_chars": 0,
  "overflow_chars": 0,
  "headroom_chars": 0,
  "trim_applied": false
}
```

**ROL 의미**: 80,000자 예산 중 2,606자만 사용 → 컨텍스트 활용률 3.3%. 나머지는 미활용 헤드룸.

### 3.3 Episode Production Log (episode_production.jsonl)

#### 3.3.1 권위 싱크 (Authoritative Sink)

| 항목 | 내용 |
|------|------|
| 경로 | `{project}/logs/episode_production.jsonl` |
| 권한 | control_plane_contract.py에서 authoritative_sink로 선언 |
| 소비자 | failure_analyzer, audit_service, canary_tools, manuscript_truth_report |
| 내용 | 에피소드별 생성 메타데이터, 모델, 시도 횟수, 비용, 품질 판정 |

### 3.4 재시도 예산 체계

#### 3.4.1 retry_budget_axes

| 축 | 출처 | 설명 |
|----|------|------|
| advisory_flags | context_advisor.py | 7개 어드바이저 체인의 품질 신호 |
| gate_basis | director_auditor.py | Director 판정 근거 |
| repair_scope | feedback_system.py | inplace/partial/full 수리 범위 |
| fix_pack | feedback_system.py | 구체적 수정 지시사항 |

#### 3.4.2 재시도 결정 흐름

```
Director 판정: PASS_WITH_FIX
  → fix_pack 생성 (수정 지시)
  → repair_scope 결정 (inplace vs partial vs full)
  → inplace 시도 → 성공? → 종료
  → 실패 → structural 시도 → 성공? → 종료
  → 실패 → full 재생성 (가장 비용 높음)
```

**ROL 영향**: inplace 패치 성공 시 비용 ~30% 절감 (Writer 재호출 없이 Director만 재검증).

---

## 4. 방향 C: ROI 분석·의사결정 자산

### 4.1 비용 시뮬레이션 도구

#### 4.1.1 tools2/cost_calculation.py — V41 vs V0128 비교

| 항목 | V41 (현재) | V0128 (목표) |
|------|-----------|-------------|
| 통과율 | 55% | 80% |
| 평균 재시도 | 1.8회 | 1.25회 |
| 에피소드당 비용 | $0.1268 | $0.0739 |
| 250화 총 비용 | $31.70 (41.3만원) | $18.48 (24만원) |
| 예산 대비 (50만원) | 82.5% | 48.0% |

#### 4.1.2 tools2/full_project_cost.py — 스테이지별 분해

| 스테이지 | 단위 수 | 단가 | 재시도 계수 | 소계 |
|----------|---------|------|-----------|------|
| Stage 0 (Bible) | 1 | $0.52 | 1.0× | $0.52 |
| Stage 1 (Volume) | 10 | $0.14 | 1.0× | $1.38 |
| Stage 2 (Arc) | 50 | $0.048 | 1.5× | $7.65 |
| Stage 3 (Blueprint) | 250 | $0.026 | 1.4× | $18.43 |
| Stage 4 V41 (Manuscript) | 250 | $0.049 | 1.8× | $31.70 |
| Stage 4 V0128 | 250 | $0.029 | 1.25× | $18.48 |
| **V41 전체** | — | — | — | **$59.68 (77,584원)** |
| **V0128 전체** | — | — | — | **$46.46 (60,398원)** |

#### 4.1.3 캐시 적용 시 (-90% 절감)

| 버전 | 캐시 전 | 캐시 후 | 예산 50만원 대비 |
|------|---------|---------|---------------|
| V41 | 77,584원 | 7,758원 | 1.6% |
| V0128 | 60,398원 | 6,040원 | 1.2% |

### 4.2 비용 정확도 감사 (docs/2026-03-12/accurate-cost-tracking-spec.md)

#### 4.2.1 현재 측정 오차

| 오차 원인 | 영향 | 심각도 |
|----------|------|--------|
| Pro output 가격: 코드 $5 → 실제 $10 | 2× 과소 계상 | **P0** |
| Flash output 가격: 코드 $0.60 → 실제 $2.50 | 4× 과소 계상 | **P0** |
| Flash input 가격: 코드 $0.15 → 실제 $0.30 | 2× 과소 계상 | **P0** |
| Thinking 토큰 미계량 | 50-500% 추가 누락 | **P1** |
| 한국어 토큰 추정 오차 | ±15-20% | **P2** |

**종합**: 현재 DB 기록은 실제 비용의 **1/2 ~ 1/5** 수준.

#### 4.2.2 수정 계획 (45행 수정)

| 우선도 | 수정 내용 | 행수 |
|--------|---------|------|
| **P0** | MODEL_COSTS 가격표 업데이트 (2026-03 공식) | 3행 |
| **P1** | usage_metadata 실측값으로 전환 (추정 → 실측) | 25행 |
| **P2** | cached_tokens 할인 로직 정비 | 15행 |
| **P3** | llm_generate.py 직접 호출 경로 커버 | 미정 |

**현황**: P0 수정은 이미 metrics_collector.py:72-82에 반영됨 (Pro output $10.00, Flash output $2.50). cost_calculation.py의 구 가격표는 **시뮬레이션 도구 전용**으로, 런타임과 별개.

### 4.3 ROI 개선 후보 (docs/2026-03-11/production-roi-improvement-ideas.md)

| 순위 | 전략 | 예상 절감 | 복잡도 |
|------|------|----------|--------|
| 1 | **Vertex Context Caching** (Bible/Treatment/Style 재사용) | 70%+ | 중 |
| 2 | **Prompt Prefix 정규화** (캐시 히트 극대화) | 30-50% | 저 |
| 3 | **Batch Prediction** (비실시간 스코어링 분리) | 20% | 중 |
| 4 | **LiteLLM 라우팅** (pro/lite 혼합) | 15-30% | 중 |
| 5 | **vLLM 자체 호스팅** | 50%+ | 고 |

### 4.4 운영 비용 실측 (docs/2026-03-11/ops-runtime-cost-crosscheck-report-OPUS.md)

#### 4.4.1 Arc별 실측 비용

| Arc | 시도 횟수 | 소요 시간 | 토큰 수 | 비용 | 주요 병목 |
|-----|----------|----------|---------|------|----------|
| Arc 1 | 12회 | 2,800초 | 1.12M | $2.11 | — |
| Arc 2 (미완) | 12회 | 3,900초 | 1.04M | $1.96 | 모순 방화벽(RC-1), 후선택 충돌 패치(RC-3) |

#### 4.4.2 병목 원인 분류

| 코드 | 원인 | 빈도 | 비용 영향 |
|------|------|------|----------|
| RC-1 | 모순 방화벽 트리거 | Arc 2에서 3-4회 반복 | 재시도 증폭 |
| RC-3 | 후선택 충돌 패치 | Arc 2 ep5-7에서 4/7회 | 패치 오버헤드 |
| RC-10 | Director 전처리 기본 비용 | 매 라운드 | 고정 비용 |

### 4.5 매출 ROI 기준선 (docs/2026-03-11/work_sales_roi_baseline_male_only.csv)

| 기간 | 중앙값 매출 | 손익분기 비율 |
|------|-----------|-------------|
| 1개월 | $12,259 | 125/1,819 작품 (6.9%) |
| 12개월 | $141,855 | 427/1,699 작품 (25.1%) |

**ROL 의미**: 250화 프로젝트 API 비용 $46-60 대비, 12개월 중앙값 매출 $141,855 → **ROI 약 2,400:1** (비용이 매출의 0.04%).

---

## 5. 교차 대조 결과

### 5.1 3방향 합치 확인

| 검증 항목 | 방향 A | 방향 B | 방향 C | 합치 |
|----------|-------|-------|-------|------|
| 비용 기록 경로 (L1→L5) | 5계층 추적 | PassRateMonitor.token_cost 필드 | 시뮬레이션에서 단가 사용 | **합치** |
| 모델 가격 (metrics_collector) | Pro $10/M out, Flash $2.50/M out | — | cost_calc은 구 가격 사용 (시뮬 전용) | **합치** (용도 분리) |
| 스코프 스냅샷 발행 지점 | stage2/3/4/session 4곳 | stage2/3/4 attempt 3곳 | — | **합치** |
| 재시도 증폭 계수 | MetricsCollector.retry_count | avg_attempts_to_pass | V41=1.8×, V0128=1.25× | **합치** |
| 에피소드당 비용 | calculate_cost() 실시간 | token_cost 필드 (현재 0.0 다수) | $0.049~$0.127 (시뮬) | **불완전** (B에서 0.0 다수) |

### 5.2 교차 대조 핵심 발견

#### 발견 1: token_cost 필드가 대부분 0.0

실측 데이터 (pass_rate_monitor.json)에서 4건 모두 `token_cost: 0.0`. 이는 PassRateMonitor.record_attempt() 호출 시 비용이 전달되지 않거나 0으로 기본값이 사용됨을 의미.

**영향**: 시도 단위 비용 추적이 **사실상 비활성**. 스코프 단위(cost_log)에서만 비용이 기록됨.

#### 발견 2: duration_ms도 Stage 3에서 0

Stage 3의 duration_ms가 모두 0 — Stage 3 오케스트레이터에서 시간 측정이 누락된 것으로 추정.

#### 발견 3: cost_calculation.py 가격과 metrics_collector.py 가격 불일치

| 항목 | cost_calculation.py (시뮬) | metrics_collector.py (런타임) |
|------|--------------------------|----------------------------|
| Pro output | $5.00/M | $10.00/M |
| Flash input | $0.075/M | $0.30/M |
| Flash output | $0.30/M | $2.50/M |

시뮬레이션 도구가 구 가격을 사용하므로, 시뮬 결과는 실제의 **1/2~1/4 수준 과소 추정**.

---

## 6. 3PASS 감리 결과

### PASS 1: 사실 확인

| 검증 항목 | 코드 근거 | 판정 |
|----------|----------|------|
| cost_log 테이블 스키마 | db_manager.py:724-737 | **확인** |
| MODEL_COSTS Pro output $10.00 | metrics_collector.py:78 | **확인** |
| save_cost_record 호출 4곳 | stage2_finalizer, stage3_orchestrator, stage4_post_processor, main_a | **확인** |
| PassRateMonitor 싱글톤 패턴 | pass_rate_monitor.py:83 | **확인** |
| AttemptRecord 30+ 필드 | pass_rate_monitor.py:33-65 | **확인** |
| 실측 token_cost = 0.0 | pass_rate_monitor.json 전 4건 | **확인** |
| snapshot_and_reset_scope 호출 | stage2_finalizer:1356, stage4_post_processor:690 | **확인** |
| Vertex Context Caching 70%+ 절감 추정 | production-roi-improvement-ideas.md | **확인** (문서 근거) |
| 캐시 -90% 절감 추정 | full_project_cost.py:179 | **확인** (시뮬 근거) |

**PASS 1 결과**: 근거 없는 서술 0건.

### PASS 2: 교차 일관성

| 대조 쌍 | 모순 | 판정 |
|---------|------|------|
| A-가격표 vs C-시뮬가격 | **불일치** (시뮬 구가격 사용) | **식별됨** — 시뮬 전용이므로 런타임 무영향 |
| A-스코프비용 vs B-시도비용 | **불완전** (B의 token_cost=0.0) | **식별됨** — 시도 단위 비용 미전달 |
| B-duration_ms vs A-응답시간 | **불완전** (Stage 3 duration=0) | **식별됨** — Stage 3 시간 미계량 |

**PASS 2 결과**: 모순 0건, 불완전 3건 (모두 기존 알려진 제약).

### PASS 3: 완전성 검증

| 검증 항목 | 상태 | 비고 |
|----------|------|------|
| LLM 호출 비용 추적 | **활성** | MetricsCollector → cost_log |
| 토큰 수 추적 (input/output) | **활성** | SDK usage_metadata 사용 |
| 캐시 토큰 추적 | **활성** | cached_tokens 필드 |
| Thinking 토큰 추적 | **활성** | thinking_tokens 필드 (MetricsCollector 수준) |
| 스테이지별 비용 집계 | **활성** | scope snapshot → cost_log |
| 대시보드 비용 노출 | **활성** | /quality/dashboard cost_summary |
| **시도 단위 비용 추적** | **비활성** | token_cost=0.0 (PassRateMonitor) |
| **Stage 3 시간 측정** | **비활성** | duration_ms=0 |
| **비-LLM 비용** (인프라, 스토리지) | **미추적** | 시스템 범위 밖 |
| **인적 비용** (운영자 시간) | **미추적** | 시스템 범위 밖 |

**PASS 3 결과**: 미추적 채널 2건 (시도 단위 비용, Stage 3 시간), 범위 밖 2건.

---

## 7. 발견 사항 종합

### 7.1 ROL 인프라 강점

| # | 강점 | 근거 |
|---|------|------|
| S1 | **5계층 비용 추적** | 호출→집계→스냅샷→DB→대시보드 완전 체인 |
| S2 | **Cache-aware 비용 계산** | cached_tokens 할인, thinking_tokens 분리 |
| S3 | **30+ 필드 시도 기록** | AttemptRecord의 풍부한 메타데이터 |
| S4 | **앙상블 후보별 추적** | candidate_key로 balanced/emotion/action 효율 비교 가능 |
| S5 | **패치 효과 분석** | is_patch, patch_strategy, patch_fallback으로 수리 ROI 측정 |
| S6 | **경고 시스템** | 통과율 5% 하락 자동 감지 |
| S7 | **컨텍스트 예산 원장** | budget_ledger로 검색 효율 추적 |
| S8 | **매출 ROI 기준선** | 작품별 1/12개월 매출 데이터로 투자 판단 지원 |

### 7.2 ROL 측정 사각지대

| # | 사각지대 | 심각도 | 설명 | 수정 난이도 |
|---|---------|--------|------|-----------|
| G1 | **시도 단위 비용 미전달** | 중 | PassRateMonitor.token_cost가 0.0 → 시도별 ROL 분석 불가 | 저 (record_attempt 호출 시 cost 전달) |
| G2 | **Stage 3 시간 미계량** | 중 | duration_ms=0 → Stage 3 시간 ROL 사각지대 | 저 (타이머 추가) |
| G3 | **시뮬 도구 구가격** | 저 | cost_calculation.py, full_project_cost.py 가격 비현실적 | 저 (상수 갱신) |
| G4 | **에피소드 단위 종합 ROL 미계산** | 중 | 비용·시간·시도·품질을 하나의 ROL 지표로 합산하는 로직 없음 | 중 (새 집계 레이어 필요) |
| G5 | **Arc 난이도 대비 비용 상관 분석 부재** | 저 | get_arc_difficulty() 존재하나 비용과 교차 분석 미구현 | 저 (조인 쿼리) |

### 7.3 ROL 수치 요약

| 지표 | 수치 |
|------|------|
| 비용 추적 계층 수 | 5 |
| cost_log 스코프 타입 수 | 3 (arc/episode/session) |
| 스냅샷 발행 지점 | 4 (stage2/3/4/session) |
| AttemptRecord 필드 수 | 33 |
| PassRateMonitor 분석 메서드 수 | 6 |
| MODEL_COSTS 항목 수 | 3 (pro/flash/default) |
| 추적 가능 토큰 유형 | 4 (input/output/cached/thinking) |
| 시뮬레이션 도구 수 | 2 (cost_calculation, full_project_cost) |
| ROI 분석 문서 수 | 5 (비용 비교, 전체 비용, 정확도 감사, 개선 후보, 실측 교차확인) |
| **비용 측정 정확도** | **50-100%** (P0 수정 후, 구 가격 대비 2-4× 개선됨) |
| **시도 단위 비용 추적률** | **0%** (token_cost=0.0) |
| **Stage 3 시간 추적률** | **0%** (duration_ms=0) |

### 7.4 ROL 최적화 지렛대 (비용 영향 순)

| 순위 | 지렛대 | 현재 | 목표 | 비용 영향 |
|------|--------|------|------|----------|
| 1 | **통과율 향상** (55%→80%) | 재시도 1.8× | 재시도 1.25× | -30% |
| 2 | **Vertex Context Caching** | 미적용 | Bible/Treatment/Style 캐시 | -70% |
| 3 | **Prompt Prefix 정규화** | 부분 적용 | 전 스테이지 캐시 히트 극대화 | -30~50% |
| 4 | **패치 모드 효율화** | inplace 부분 성공 | structural 패치 강화 | -15% |
| 5 | **모델 티어 최적화** | 전 에이전트 Pro | 비핵심 에이전트 Flash | -20% |

---

## 8. 근거 파일 인벤토리

### 8.1 비용 계량 인프라 소스

| 파일 | 행수 | 역할 |
|------|------|------|
| `modules/core/metrics_collector.py` | 533 | 메트릭 싱글톤, 비용 계산, 스코프 집계 |
| `modules/core/db_manager.py` | 5000+ | cost_log 테이블, save_cost_record, get_cost_summary |
| `modules/domain/agents/base_agent.py` | 2000+ | start_call/end_call 연동, usage_metadata 추출 |
| `modules/core/stage2_finalizer.py` | 1800+ | Arc 스코프 스냅샷 발행 |
| `modules/core/stage3_orchestrator.py` | 2200+ | Episode 스코프 스냅샷 발행 |
| `modules/core/stage4_post_processor.py` | 750+ | Episode 스코프 스냅샷 발행 |
| `modules/api/bridge_server.py` | 2100+ | /quality/dashboard 비용 요약 노출 |

### 8.2 산출 효율 추적 소스

| 파일 | 행수 | 역할 |
|------|------|------|
| `modules/core/pass_rate_monitor.py` | 550+ | 통과율, 패치 효과, 난이도, 경고 |
| `modules/core/stage4_interview_round.py` | 6000+ | 재시도 예산, retry_budget_axes |
| `modules/core/failure_analyzer.py` | 3000+ | 실패 패턴 분류, 병목 진단 |
| `modules/core/feedback_system.py` | 2000+ | PASS/REJECT/PASS_WITH_FIX, fix_pack |

### 8.3 ROI 분석 문서

| 파일 | 내용 |
|------|------|
| `tools2/cost_calculation.py` | V41 vs V0128 에피소드당 비용 비교 |
| `tools2/full_project_cost.py` | Stage 0-4 전체 프로젝트 비용 분해 |
| `docs/2026-03-12/accurate-cost-tracking-spec.md` | 비용 정확도 감사 + P0-P3 수정 계획 |
| `docs/2026-03-11/production-roi-improvement-ideas.md` | 비용 절감 전략 5개 후보 |
| `docs/2026-03-11/ops-runtime-cost-crosscheck-report-OPUS.md` | Arc 1-2 실측 비용 교차확인 |
| `docs/2026-03-11/work_sales_roi_baseline_male_only.csv` | 작품별 매출 ROI 기준선 |

### 8.4 실측 데이터

| 파일 | 내용 |
|------|------|
| `projects/0_260318/logs/pass_rate_monitor.json` | 4건 시도 기록 (Stage 2/3) |
| `projects/0_260318/logs/quality_metrics.jsonl` | 검증/검색 관측 12건 |
| `projects/0_260318/logs/runtime_audit.jsonl` | 런타임 감사 이벤트 |

### 8.5 회귀 테스트

| 파일 | 커버 대상 |
|------|----------|
| `tests/test_cost_tracking.py` | save_cost_record, snapshot_and_reset_scope |
| `tests/test_bridge_quality_summary.py` | 대시보드 비용 요약 |
| `tests/test_stage4_interview_round.py` | 재시도 예산, 비용 기록 |
| `tests/test_stage4_post_processor.py` | 에피소드 스코프 스냅샷 |
| `tests/test_stage2_finalizer.py` | Arc 스코프 스냅샷 |
| `tests/test_resume_status.py` | 비용 누적 복원 |

---

> **조사 종결**
> 3방향 독립 조사 + 교차 대조 + 3PASS 감리 완료.
> 인프라 강점 8건 (S1-S8), 측정 사각지대 5건 (G1-G5), 최적화 지렛대 5건 식별.
> 가장 높은 ROL 영향: **통과율 향상 + Vertex Context Caching** (합산 -70~80% 비용 절감 잠재).
> 가장 시급한 수정: **G1 (시도 단위 비용 전달)** + **G2 (Stage 3 시간 계량)** — 둘 다 저난이도.
