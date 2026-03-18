# S7: ROL + 정적 개선 SSOT

> 최종 갱신: 2026-03-18
> 소스: rol-deepdive, static-improvement-3pass, evidence-manifest, real-manuscript-corpus
> 감리: 3PASS + 적대적 보정 (11회 감리, 확신도 98%)

---

## 1. 개관

**ROL (Return on Labor)** = 투입 자원(API 비용 USD, 토큰 수, 시간, 재시도 횟수) 대비 산출 결과(에피소드 수, 통과율, 품질 점수)의 효율 지표.

```
ROL = 산출(에피소드 x 품질) / 투입(비용 + 시간 + 재시도 증폭)
```

이 SSOT는 두 축을 통합한다:
1. **ROL 측정 인프라**: 비용/시간/재시도를 어디서 어떻게 추적하는가
2. **정적 개선 발견**: 코드 수정 없는 조사로 발굴한 구조적 개선 기회 20건

---

## 2. 비용 추적 인프라 (5계층)

```
┌─────────────────────────────────────────────────────────┐
│  L1. LLM 호출 계층 (base_agent.py)                       │
│      start_call() → API 호출 → end_call()                 │
├─────────────────────────────────────────────────────────┤
│  L2. MetricsCollector (metrics_collector.py, 533행)      │
│      싱글톤 — 에이전트별/모델별/스코프별 집계             │
├─────────────────────────────────────────────────────────┤
│  L3. 스코프 스냅샷 (stage*_finalizer/post_processor)     │
│      snapshot_and_reset_scope() → arc/episode 단위        │
├─────────────────────────────────────────────────────────┤
│  L4. DB 영속화 (db_manager.py cost_log 테이블)            │
│      save_cost_record() → SQLite                          │
├─────────────────────────────────────────────────────────┤
│  L5. 대시보드 노출 (bridge_server.py /quality/dashboard)  │
│      _build_cost_summary_payload() → Renderer             │
└─────────────────────────────────────────────────────────┘
```

### 2.1 L1 LLM Call (base_agent start/end_call) → S4 참조

```python
# base_agent.py (개략)
metric_id = collector.start_call(agent_name, model)
try:
    response = self._generate_content(prompt, ...)
    collector.end_call(metric_id,
        success=True,
        input_tokens=response.usage_metadata.prompt_token_count,
        output_tokens=response.usage_metadata.candidates_token_count,
        cached_tokens=response.usage_metadata.cached_content_token_count,
        thinking_tokens=response.usage_metadata.thoughts_token_count)
except:
    collector.end_call(metric_id, success=False, error_type=...)
```

**추적 토큰 필드 (4종)**:

| 필드 | 소스 | 설명 |
|------|------|------|
| `prompt_token_count` | Gemini SDK `usage_metadata` | 입력 토큰 (캐시 포함) |
| `candidates_token_count` | Gemini SDK `usage_metadata` | 출력 토큰 |
| `thoughts_token_count` | Gemini SDK `usage_metadata` | Thinking 토큰 (과금 대상) |
| `cached_content_token_count` | Gemini SDK `usage_metadata` | 캐시 히트 토큰 (할인) |

API 키 순환: 최대 10개 키, 쿼터 소진 시 3600초 캐시, 네트워크 재시도 3회 지수 백오프 10-30초.

### 2.2 L2 MetricsCollector (싱글톤, 533행)

**MODEL_COSTS (2026-03 공식 가격, P0 수정 완료)**:

| 모델 | Input ($/M) | Output ($/M) | Cache Read ($/M) |
|------|------------|-------------|-----------------|
| `gemini-2.5-pro` | $1.25 | $10.00 | $0.125 |
| `gemini-2.5-flash` | $0.30 | $2.50 | $0.03 |
| `default` (fallback) | $1.25 | $10.00 | $0.125 |

**비용 계산 (cache-aware)**:

```python
def calculate_cost(model, input_tokens, output_tokens, cached_tokens=0):
    costs = MODEL_COSTS[model]
    non_cached_input = max(0, input_tokens - cached_tokens)
    input_cost = (non_cached_input / 1_000_000) * costs["input"]
    cache_cost = (cached_tokens / 1_000_000) * costs["cache_read"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + cache_cost + output_cost
```

**집계 차원**:

| 차원 | 추적 항목 | 집계 수준 |
|------|----------|----------|
| 에이전트별 | 호출 수, 성공 수, 재시도, 응답시간(P50/P90/P99) | 세션 |
| 모델별 | input/output/cached/thinking 토큰, 비용 | 세션 |
| 스코프별 | calls, tokens, cost, model_breakdown | arc/episode |

### 2.3 L3 Scope Snapshots (4개 발행 지점)

| 발행 위치 | scope_type | scope_id | 시점 |
|----------|-----------|---------|------|
| `stage2_finalizer.py:1356` | `"arc"` | `global_arc_no` | Arc 설계 완료 |
| `stage3_orchestrator.py:2159` | `"episode"` | `working_ep` | Blueprint 완료 (주의: `snapshot_and_reset_scope()` 아닌 `save_cost_record()`에 하드코딩 0값 직접 전달 — 실질 메트릭 스냅샷 아님) |
| `stage4_post_processor.py:690` | `"episode"` | `next_ep` | 원고 최종 저장 |
| `main_a.py` (세션 종료) | `"session"` | `0` | 전체 세션 종료 |

스냅샷 데이터:
```json
{
  "total_calls": 12,
  "total_tokens": 45000,
  "total_cost_usd": 0.234,
  "model_breakdown": "{\"gemini-2.5-pro\": {\"tokens\": 35000, \"cost\": 0.21, ...}}"
}
```

### 2.4 L4 DB cost_log 테이블

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

DB 메서드:
- `save_cost_record()` (db_manager.py:3732): 스코프별 비용 스냅샷 저장
- `get_cost_summary(lookback=N)` (db_manager.py:3770): 최근 N건 비용 기록 조회

### 2.5 L5 Dashboard (/quality/dashboard `_build_cost_summary_payload`)

> bridge_server.py 엔드포인트 전체 스펙 (REST 9개, WS 이벤트 8개, 검증 게이트 체인) → **S2 (BE-FE 연결 SSOT)** 참조. 본 섹션은 비용 대시보드 payload 구조만 기술.

```python
def _build_cost_summary_payload(rows, lookback):
    return {
        "available": True/False,
        "lookback": int,
        "row_count": int,
        "latest_session_id": str,
        "total_calls": int,
        "total_tokens": int,
        "total_cost_usd": float,
        "scope_counts": {"arc": N, "episode": N, "session": N},
        "recent": [{"session_id", "scope_type", "scope_id", "cost", "created_at"}]
    }
```

---

## 3. PassRateMonitor

### 3.1 AttemptRecord 33필드

핵심 ROL 필드:

| 필드 | 타입 | ROL 의미 |
|------|------|----------|
| `stage` | int | 비용 집중 구간 식별 (2/3/4) |
| `episode` | int | 산출 단위 |
| `attempt_num` | int | 재시도 증폭 계수 |
| `success` | bool | 산출 여부 |
| `reject_reason` | str | 병목 원인 분류 |
| `generation_method` | str | 전략별 효율 비교 |
| `model_tier` | int | 모델별 비용-품질 트레이드오프 |
| `duration_ms` | int | 시간 ROL |
| `token_cost` | float | 금전 ROL |
| `is_patch` | bool | 패치 vs 전체 재생성 효율 |
| `patch_strategy` | str | 전략별 효과 |
| `score_breakdown` | dict | 품질 상세 |
| `retry_budget_axes` | dict | 예산 제어 (아래 상세) |
| `candidate_key` | str | 앙상블 효율 (balanced/emotion/action) |
| `content_hash` | str | 중복 생성 감지 |

### 3.1.1 재시도 예산 4축 (retry_budget_axes)

재시도 예산 4축:
1. advisory_flags (context_advisor.py): 7개 어드바이저 체인 품질 신호
2. gate_basis (director_auditor.py): Director 판정 근거
3. repair_scope (feedback_system.py): inplace/partial/full 수리 범위
4. fix_pack (feedback_system.py): 구체적 수정 지시사항

흐름: Director PWF → fix_pack → repair_scope → inplace 시도 → 실패 시 structural → 실패 시 full 재생성 (최고 비용). inplace 성공 시 ~30% 비용 절감.

### 3.2 StageStats metrics

| 지표 | 계산법 | ROL 의미 |
|------|--------|----------|
| `first_attempt_pass` | 1회 시도 통과 건수 | 최적 효율 (재시도 0) |
| `first_attempt_rate` | first_pass / total_episodes | **핵심 ROL 지표** |
| `eventual_pass` | 최종 통과 건수 | 실질 산출 |
| `eventual_rate` | eventual / total_episodes | 실질 생산성 |
| `avg_attempts_to_pass` | 합산 시도 / 통과 건수 | 재시도 증폭 계수 |
| `common_reject_reasons` | 거부 사유 빈도 | 병목 원인 순위 |
| `method_success_rate` | 방법별 성공률 | 전략 효과 비교 |

### 3.3 Advanced analysis: patch_effectiveness, arc_difficulty, alerts, trend

| 메서드 | 용도 | 반환 |
|--------|------|------|
| `get_patch_effectiveness()` | 패치 모드 성공률 + fallback 비율 | dict |
| `get_arc_difficulty()` | Arc별 난이도 추정 (시도 횟수 기반) | dict |
| `check_alerts()` | 통과율 5%+ 하락 또는 <50% 1차 통과 경고 | list[str] |
| `get_trend()` | 최근 N건 이동평균 추세 | dict |

### 3.4 Production data: token_cost 불완전, Stage 3 duration_ms=0

실측 데이터 (`projects/0_260316/logs/pass_rate_monitor.json`, 25건):

| 스테이지 | 특이사항 |
|---------|---------|
| Stage 2 | duration 33-72초 정상, token_cost=0.0 |
| Stage 3 | duration_ms=0 (11건 전부), token_cost=0.0 |
| Stage 4 | duration 195-490초 정상, token_cost **100% 비영** (0.09-0.65 USD, 실측값 존재) |

**token_cost 현황**: Stage 2/3 레코드는 **전부 0.0** (비용 미전달). Stage 4는 **100% 실측값 존재** (11/11건, 0_260316 기준). record_attempt() 호출 시 Stage 4만 비용이 정상 전달되며, Stage 2/3은 전달 경로가 **누락**.

**Stage 3 duration=0**: Timing 코드(`stage3_orchestrator.py:1009,1370`)는 존재하나 결과가 0. 코드상 로직은 정상이나 런타임 디버깅 없이 원인 미확정.

---

## 4. ROI 분석 자산

### 4.1 Simulation tools (cost_calculation.py, full_project_cost.py) -- 구 가격 사용

**cost_calculation.py -- V41 vs V0128 비교**:

| 항목 | V41 (현재) | V0128 (목표) |
|------|-----------|-------------|
| 통과율 | 55% | 80% |
| 평균 재시도 | 1.8회 | 1.25회 |
| 에피소드당 비용 | $0.1268 | $0.0739 |
| 250화 총 비용 | $31.70 (41.3만원) | $18.48 (24만원) |

**full_project_cost.py -- 스테이지별 분해**:

| 스테이지 | 단위 수 | 단가 | 재시도 계수 | 소계 |
|----------|---------|------|-----------|------|
| Stage 0 (Bible) | 1 | $0.52 | 1.0x | $0.52 |
| Stage 1 (Volume) | 10 | $0.14 | 1.0x | $1.38 |
| Stage 2 (Arc) | 50 | $0.048 | 1.5x | $7.65 |
| Stage 3 (Blueprint) | 250 | $0.026 | 1.4x | $18.43 |
| Stage 4 V41 (Manuscript) | 250 | $0.049 | 1.8x | $31.70 |
| **V41 전체** | -- | -- | -- | **$59.68 (77,584원)** |
| **V0128 전체** | -- | -- | -- | **$46.46 (60,398원)** |

**주의**: 시뮬레이션 도구는 구 가격 사용 (Pro output $5 vs 실제 $10, Flash output $0.60 vs 실제 $2.50). 시뮬 결과는 실제의 **1/2~1/4 수준 과소 추정**. 런타임(`metrics_collector.py`)은 P0 수정 완료.

비용 정확도 상세 (2026-03-12 감사):
- P0 (수정 완료): Pro output $5→$10 (2× 과소), Flash output $0.60→$2.50 (4×), Flash input $0.15→$0.30 (2×)
- P1 (미수정): Thinking 토큰 미계량 (50-500% 추가 누락), 수정 25행
- P2 (미수정): 한국어 토큰 추정 오차 ±15-20%, 수정 15행
- 종합: P0 수정 전 DB 기록은 실제 비용의 1/2~1/5 수준이었음

### 4.2 Production measurements (Arc 1: $2.11, Arc 2: $1.96)

| Arc | 시도 횟수 | 소요 시간 | 토큰 수 | 비용 | 주요 병목 |
|-----|----------|----------|---------|------|----------|
| Arc 1 | 12회 | 2,800초 | 1.12M | $2.11 | -- |
| Arc 2 (미완) | 12회 | 3,900초 | 1.04M | $1.96 | 모순 방화벽(RC-1), 후선택 충돌 패치(RC-3) |

병목 원인:
- RC-1: 모순 방화벽 트리거 (Arc 2에서 3-4회 반복) → 재시도 증폭
- RC-3: 후선택 충돌 패치 (Arc 2 ep5-7에서 4/7회) → 패치 오버헤드
- RC-10: Director 전처리 기본 비용 (매 라운드 고정)

### 4.3 Sales ROI baseline ($141,855 중앙값 12개월 매출, ROI ~2,400:1)

| 기간 | 중앙값 매출 | 손익분기 비율 |
|------|-----------|-------------|
| 1개월 | $12,259 | 125/1,819 작품 (6.9%) |
| 12개월 | $141,855 | 427/1,699 작품 (25.1%) |

250화 프로젝트 API 비용 $46-60 대비, 12개월 중앙값 매출 $141,855 → **ROI 약 2,400:1** (비용이 매출의 0.04%).

### 4.4 ROI improvement candidates

| 순위 | 전략 | 예상 절감 | 복잡도 |
|------|------|----------|--------|
| 1 | **Vertex Context Caching** (Bible/Treatment/Style 재사용) | -70%+ | 중 |
| 2 | **Prompt Prefix 정규화** (캐시 히트 극대화) | -30~50% | 저 |
| 3 | **Batch Prediction** (비실시간 스코어링 분리) | -20% | 중 |
| 4 | **LiteLLM 라우팅** (pro/lite 혼합) | -15~30% | 중 |
| 5 | **vLLM 자체 호스팅** | -50%+ | 고 |

---

## 5. 정적 개선 발견

### 5.1 Phantom Verdict (OPP-01/02): CONDITIONAL_PASS no-op, PASS_WITH_WARNING in SQL

**OPP-01: Verdict Enum 6-Way Fragmentation**

시스템의 verdict는 **6개 상태**로 운영되지만 schema는 **3개만** 정의:

| Verdict | Schema 정의 | 최종 도달 | 비고 |
|---------|------------|----------|------|
| PASS | O | 모든 sink | 정상 |
| PASS_WITH_FIX | O | 모든 sink | 정상 |
| REJECT | O | 모든 sink | 정상 |
| CONDITIONAL_PASS | **X** | **0번** (no-op) | ensemble이 체계적으로 덮어씀 |
| PASS_WITH_WARNING | **X** | DB/코드 | SQL WHERE절 하드코딩 |
| FAILED | **X** | pipeline 내부 | DB/JSONL 미도달 |

PASS_WITH_WARNING은 `db_manager.py:3150`에서 `WHERE verdict IN ('PASS', 'PASS_WITH_WARNING')`으로 SQL에 상수로 존재. Schema 변경만으로 제거 불가.

**OPP-02: CONDITIONAL_PASS No-Op Layer**

- `director_grading.py:567,571`에서 생산
- `director_ensemble.py:1573,1732`에서 **체계적으로 원래 verdict로 되돌림**
- 코드 29건(modules/ 14 + tests/ 15) 존재하나 **최종 verdict에 0번 도달**
- TF-DG-11(2026-03-15)에서 이미 발견되었으나 "design coherence" 수준으로 분류
- 실질적 유지보수 비용이 정량화되지 않았음
- **권고**: 순수 logging으로 축소하거나 제거

### 5.2 Post-Hoc Observability (OPP-04): 4개 sink, 사후 정합성만

동일 사실(verdict/score/artifact_path)이 **최대 4개 sink**에 독립 기록:

| Sink | 대상 | 비차단? |
|------|------|--------|
| DB `director_selections` | SQLite | try-except |
| DB `stage_attempts` | SQLite | try-except |
| `decisions.jsonl` | JSONL | try-except |
| `pass_rate_monitor.json` | JSON | **조건부** (`if getattr(ctx, "pass_rate_monitor", None)`) |

- 모든 write가 try-except 비차단 -- 1개 sink만 성공해도 에러 없음
- `sink_alignment_summary()` 존재하나 **사후(post-hoc) 비교** -- divergence 발생 시점 미감지
- 정상 에피소드 생산 경로에서 자동 정합성 체크 없음 (캐너리 하니스에서만 호출)

### 5.3 Governance Overhead (OPP-08): ~3,450행, 14 harness, 순환 참조

- `docs/implementation/` (2,957행, 45 files) + `AGENTS.md` (188행) + blockguide (~300+행)
- 14 harness, 10 template, 6 contract가 순환 참조
- init harness <-> operations-governance-map 간 순환 참조
- 단순 버그 수정에도 3-4개 문서 읽기 → 라우팅 확정 → 작업 시작
- 실행문서 수정 시 canonical 수정 → 3-pass → temp mirror 갱신의 6-step 프로세스
- 5+ outline 문서가 draft/outline 상태에서 정체

### 5.4 Firewall info DB-only (OPP-03)

- `director_ensemble.py`에서 `firewall_triggered=True`와 `firewall_reason` 생성
- `db_manager.py:2809-2827`을 통해 DB에 기록
- `session_logger.log_decision()`에는 이 필드 **미포함**
- decisions.jsonl만 보면 firewall 발동 여부를 알 수 없음
- **Firewall은 시스템 최강 품질 방어선**(contradiction CRITICAL → score <=44 + REJECT 강제)인데, 가장 접근하기 쉬운 진단 소스(JSONL)에서 빠져 있음
- **즉시 개선**: `session_logger.log_decision()`에 firewall_triggered, firewall_reason 2개 필드 추가 (변경량 최소)

### 5.5 Other OPPs

| ID | 항목 | 카테고리 | 핵심 |
|----|------|---------|------|
| OPP-05 | quality_risk 3곳 불일치 | Contract Hardening | director_ensemble.py:771이 PASS_WITH_WARNING 누락 (실제 결함) |
| OPP-06 | Stage 4 rejection 45.5% | Retry Economics | Blueprint→Writing 핸드오프 컨텍스트 손실 시사, 샘플 제한 |
| OPP-07 | UNCONDITIONAL_PASS >=85 미문서화 | Contract Hardening | 런타임 상수, schema/constants에 미정의 |
| OPP-09 | Blockguide 외부 SSOT 의존 | Authority Compression | 전처리_ssot/ 외부 디렉토리 의존 |
| OPP-10 | UI "대기" 3-way 혼재 | Operator Cognition | 실행 중/데이터 없음/오류를 모두 "대기"로 표시 |
| OPP-11 | Test mock 과잉 | Quality Semantics | ask() mock → real failure 경로 미검증 |
| OPP-12 | Advisory 에스컬레이션 부재 | Quality Semantics | 반복 advisory가 blocking으로 미에스컬레이션 |
| OPP-13 | Artifact post-write 미검증 | Log Truth | partial write 감지 불가 |
| OPP-14 | Dead surface 누적 | Surface Retirement | RESERVED_SHIMS, dead IPC, outline docs |
| OPP-15 | Stage 3 duration=0ms | Observability | 확신도 85%, 런타임 디버깅 필요 |
| OPP-16 | WS reconnect 부재 | Operator Cognition | 단절 시 경고 없음, reconnect 없음 |
| OPP-17 | patch_strategy 비정규화 | Log Truth | is_patch=true 5건 중 4건(80%) 빈 문자열 |
| OPP-18 | Quality Radar 범례 부재 | Operator Cognition | CED/AI Slop/gzip/Rhythm/Density 단위/범위 미표시 |
| OPP-19 | Stage 3 에스컬레이션 비대칭 | Operator Cognition | 알림은 있으나 선택지 부재 (Stage 4와 비대칭) |
| OPP-20 | _LazyThreshold 스레드 비안전 | Contract Hardening | concurrent first-access 시 race condition, 현재 단일 스레드라 미발현 |

---

## 6. 실물 원고 코퍼스

### 6.1 현황: 22 works, 890 episodes, 11 YAML banks -- ZERO runtime usage

`docs/실물기반 사각지대 테스트/` 인벤토리:

| 자료군 | 규모 | 현재 런타임 사용 | 자연스러운 역할 |
|--------|------|----------------|--------------|
| 실물 원고 txt | 22작품 / 890화 | 없음 | 오프라인 기준 코퍼스, 벤치마크 |
| few-shot YAML | 11개 | 없음 | 프롬프트 exemplar bank |
| 문체 프로파일 | 5개 | 없음 | 장르별 정량 기준, anti-slop 기준 |
| 클리프행어 문서 | 4개 | 없음 | Director 상업성/엔딩 훅 rubric |
| 화간 연결 문서 | 4개 | 없음 | Stage 3/4 연결성 rubric |
| 모순 GT / 분석 | 2개 | 없음 | validator recall benchmark |

현재 시스템은 이미 유사 신호를 hardcoded heuristic으로 다루고 있음:
- `quality_constitution.py:140`: 화 시작 후킹력 / 클리프행어 효과
- `scoring_validator.py:1087`: 장르별 품질 피드백
- `writer_template.py:64`: 직전 화 연결 앵커, closing hook
- `constitutional_checker.py:110`: cliffhanger 무시 금지
- `confidence_calibration.py:199,374`: 연결 점수, ending hook 점수

**빠진 것**: raw corpus가 아니라 runtime-consumable distilled contract.

### 6.2 활용 방향: 평가 우선, 증류 기준, 벤치마크, few-shot은 최후

권장 순서:

1. **평가에 먼저 쓴다** (Judge-First Calibration)
   - 클리프행어 taxonomy → Director commercial appeal rubric
   - 화간 연결 분석 → Stage 3/4 continuity rubric
   - 문체 프로파일 → anti-slop drift 기준
   - contradiction GT → validator recall benchmark

2. **증류된 기준만 런타임에 넣는다**
   - taxonomy, profile, GT를 작은 규칙/예시/threshold 자산으로 변환

3. **raw 원고는 오프라인 벤치마크로 유지**
   - blind 비교 (실물 vs 생성), calibration, fine-tuning 입력

4. **생성 직접 주입은 맨 마지막 옵션**
   - 비용, 잡음, 과적합, 문체 모사 부작용

### 6.3 핵심 판단: "dead asset 아님, runtime-consumable distilled contract 부재"

`실물기반 사각지대 테스트/`는:
- **현재 상태**: 오프라인 품질 기준 코퍼스
- **빠진 것**: runtime-consumable distilled contract
- **필요한 것**: raw direct wiring이 아니라 증류 계층

비권장:
- raw 원고 890화를 runtime prompt에 직접 붙이는 방식
- "실물 원고 = 무조건 정답" 취급 (모순 포함 -- contradiction GT가 이를 증명)
- few-shot YAML을 검증 없이 대량 주입
- corpus를 하나의 거대한 SSOT 취급

---

## 7. 측정 사각지대 (G1-G5)

| ID | 사각지대 | 심각도 | 설명 | 수정 난이도 |
|----|---------|--------|------|-----------|
| **G1** | 시도 단위 비용 미전달 | 중 | PassRateMonitor.token_cost가 전 record 0.0 → 시도별 ROL 분석 불가 | 저 (record_attempt 호출 시 cost 전달) |
| **G2** | Stage 3 시간 미계량 | 중 | duration_ms=0 (11건 전부) → Stage 3 시간 ROL 사각지대 | 저 (타이머 추가 또는 버그 수정) |
| **G3** | 시뮬 도구 구 가격 | 저 | cost_calculation.py 가격이 실제의 1/2~1/4 → 시뮬 과소 추정 | 저 (상수 갱신) |
| **G4** | 에피소드 단위 종합 ROL 미계산 | 중 | 비용/시간/시도/품질을 하나의 ROL 지표로 합산하는 로직 없음 | 중 (새 집계 레이어) |
| **G5** | Arc 난이도-비용 상관 분석 부재 | 저 | get_arc_difficulty() 존재하나 비용과 교차 분석 미구현 | 저 (조인 쿼리) |

---

## 8. 수치 요약표

| 지표 | 수치 |
|------|------|
| 비용 추적 계층 수 | 5 |
| cost_log 스코프 타입 수 | 3 (arc/episode/session) |
| 스냅샷 발행 지점 | 4 (stage2/3/4/session) |
| AttemptRecord 필드 수 | 33 |
| PassRateMonitor 분석 메서드 수 | 6 |
| MODEL_COSTS 항목 수 | 3 (pro/flash/default) |
| 추적 가능 토큰 유형 | 4 (input/output/cached/thinking) |
| 시뮬레이션 도구 수 | 2 |
| ROI 분석 문서 수 | 5 |
| 비용 측정 정확도 | 50-100% (P0 수정 후) |
| 시도 단위 비용 추적률 | Stage 2/3: **0%** (전부 0.0), Stage 4: **100%** (실측값 존재) |
| Stage 3 시간 추적률 | **0%** (duration_ms=0) |
| 정적 개선 기회 | 20건 (OPP-01 ~ OPP-20) |
| Dead code/surface | 3 + 다수 dead surface |
| 실물 원고 코퍼스 | 22작품 / 890화 / ZERO runtime usage |
| 프로덕션 Arc 비용 | $2.11 (Arc 1), $1.96 (Arc 2) |
| 250화 프로젝트 비용 (시뮬) | $59.68 V41 / $46.46 V0128 |
| 매출 ROI | ~2,400:1 (12개월 중앙값) |
| Governance 문서량 | ~3,450행, 14 harness |
| Verdict 상태 수 | 코드 6 / 스키마 3 |
| CONDITIONAL_PASS 최종 도달 | 0회 |

---

## 9. ROL 최적화 지렛대

| 순위 | 지렛대 | 현재 | 목표 | 비용 영향 |
|------|--------|------|------|----------|
| **#1** | 통과율 향상 (55%→80%) | 재시도 1.8x | 재시도 1.25x | **-30%** |
| **#2** | Vertex Context Caching | 미적용 | Bible/Treatment/Style 캐시 | **-70%** |
| **#3** | Prompt Prefix 정규화 | 부분 적용 | 전 스테이지 캐시 히트 극대화 | **-30~50%** |
| **#4** | 패치 모드 효율화 | inplace 부분 성공 | structural 패치 강화 | **-15%** |
| **#5** | 모델 티어 최적화 | 전 에이전트 Pro | 비핵심 에이전트 Flash | **-20%** |

**가장 높은 ROL 영향**: 통과율 향상 + Vertex Context Caching (합산 -70~80% 비용 절감 잠재).
**가장 시급한 수정**: G1 (시도 단위 비용 전달) + G2 (Stage 3 시간 계량) -- 둘 다 저난이도.

---

## [부록 A] 감리 이력

### ROL 딥다이브 감리

| PASS | 목적 | 판정 |
|------|------|------|
| 1st | 사실 확인 | 근거 없는 서술 0건 |
| 2nd | 교차 일관성 | 모순 0건, 불완전 3건 (token_cost=0.0, Stage 3 duration=0, 시뮬 구가격) |
| 3rd | 완전성 검증 | 미추적 채널 2건 (시도 단위 비용, Stage 3 시간), 범위 밖 2건 |

### 정적 개선 감리

| Pass | 핵심 결과 |
|------|----------|
| 1-3 | 6 TF 결과 종합, 18개 opportunity 초안, cross-cut pattern 3개 추출 |
| 4 (재감리) | OPP-06 수치 정정 (63%→45.5%), S3 timing 코드 추적 보강 |
| 5 (재감리) | 10개 렌즈 독립 적용 섹션 추가, OPP-19/20 신규 추가 |
| 6 (비판적) | 샘플 제한 명시, 가설 재평가, 번호 동기화 |
| **7 (적대적)** | **5건 수치 과장 정정**: 코드 74건→29건, 4,000+행→3,450행, 50%→80% empty, FAILED 관통→내부 국한, 미문서화→schema 미정의 |
| 8 | 잔여 불일치 전수 제거, 문서 간 정합성 최종 확인 |
| 9-10 (적대적 코드 검증) | OPP-19/04/13 정정, OPP-05 실제 결함 확인, OPP-02 코드 경로 재확인 |
| 11 (종합) | Confidence 재조정 (OPP-15: 90%→85%, OPP-19: 97%→93%), 과장 표현 최종 제거 |

**최종 확신도**: 98%

### 실물 원고 코퍼스 감리

| Pass | 핵심 |
|------|------|
| 1 (구조/범위) | direct use vs potential use 분리 |
| 2 (근거/일관성) | 런타임 미사용 grep 재확인, producer/tooling 경로 분리 |
| 3 (실행/가독성) | 우선순위 있는 운영 방향 제시, raw wiring 비권장 명시 |

---

## [부록 B] 근거 파일

### ROL 인프라 소스

| 파일 | 행수 | 역할 |
|------|------|------|
| `modules/core/metrics_collector.py` | 533 | 메트릭 싱글톤, 비용 계산, 스코프 집계 |
| `modules/core/db_manager.py` | 5000+ | cost_log 테이블, save_cost_record, get_cost_summary |
| `modules/domain/agents/base_agent.py` | 2000+ | start_call/end_call, usage_metadata 추출 |
| `modules/core/pass_rate_monitor.py` | 550+ | 통과율, 패치 효과, 난이도, 경고 |
| `modules/core/stage4_interview_round.py` | 6000+ | 재시도 예산, retry_budget_axes |
| `modules/core/failure_analyzer.py` | 3000+ | 실패 패턴 분류, sink_alignment_summary |

### ROI 분석 문서

| 파일 | 내용 |
|------|------|
| `tools2/cost_calculation.py` | V41 vs V0128 비교 (구 가격) |
| `tools2/full_project_cost.py` | Stage 0-4 전체 비용 분해 (구 가격) |
| `docs/2026-03-12/accurate-cost-tracking-spec.md` | 비용 정확도 감사 + P0-P3 수정 계획 |
| `docs/2026-03-11/production-roi-improvement-ideas.md` | 비용 절감 전략 5개 후보 |
| `docs/2026-03-11/ops-runtime-cost-crosscheck-report-OPUS.md` | Arc 1-2 실측 교차확인 |
| `docs/2026-03-11/work_sales_roi_baseline_male_only.csv` | 작품별 매출 ROI 기준선 |

### 정적 개선 조사 소스

| 파일 | 역할 |
|------|------|
| `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-3pass-audit.md` | OPP-01~20, 20개 기회 |
| `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md` | 근거 매핑 |
| `docs/2026-03-18/OPUS/geuldobi-v2-rol-deepdive-full-survey.md` | 5계층 비용 추적, PassRateMonitor |
| `docs/2026-03-18/OPUS/real-manuscript-quality-corpus-usage-direction-3pass-audit.md` | 실물 원고 활용 방향 |

### 실측 데이터

| 파일 | 내용 |
|------|------|
| `projects/0_260316/logs/pass_rate_monitor.json` | 25건 시도 기록 |
| `projects/0_260316/logs/quality_metrics.jsonl` | 검증/검색 관측 |
| `projects/0_260318/logs/pass_rate_monitor.json` | 4건 시도 기록 |

---

*S7 SSOT -- ROL + 정적 개선 통합. 3PASS + 11회 적대적 보정.*
*최종 확신도: 98%*
