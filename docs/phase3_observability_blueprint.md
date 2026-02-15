# Phase 3 관측성 개선 — ThreadPoolExecutor 병렬 구간 계측 청사진

> 작성: 2026-02-15, checkpoint `630dd98`
> 상태: **구현 전 청사진**

---

## 1) 범위

### 대상: `stage2_orchestrator.py` ThreadPoolExecutor 병렬 구간

현재 Stage 2에는 **1개의 ThreadPoolExecutor 사용 구간**이 존재:

| 위치 | 메서드 | 라인 | max_workers | 병렬 작업 |
|------|--------|------|-------------|----------|
| `stage2_orchestrator.py` | `_preflight_state_setup()` | L890-894 | 2 | arc_drive(Weaver LLM) + preflight(Preflight LLM) |

**이미 측정 중인 구간** (변경 없음):
- `s2_arc_{N}_generate` (L1216-1234): FourPhase Arc 생성
- `s2_arc_{N}_director` (L2002-2064): Director 심사

**미측정 구간** (이번 범위):
- `_preflight_state_setup()` 내 ThreadPoolExecutor 블록 전체
- 개별 병렬 태스크: arc_drive, preflight_analysis

### 측정 항목

| 항목 | 설명 | 예시 |
|------|------|------|
| 구간명 | PerfTimer step 이름 | `s2_arc_3_preflight_parallel` |
| 시작/종료 시각 | `time.monotonic()` (PerfTimer 내부) | — |
| elapsed_ms | `stop()` 반환값 × 1000 | `1234.56` |
| 예외 여부 | try/except 내 로그 | `WARNING` 레벨 |
| arc 식별자 | `global_arc_no` | `3` |

---

## 2) 비범위

- 판정 로직 변경 (Director audit, PASS/REJECT 분기) — **불변**
- 재시도 로직 변경 (attempt loop, max_retries) — **불변**
- async/sync 구조 변경 — **불변** (R4-a NO-GO 유지, 계측만)
- 성능 최적화 자체 — **불변** (측정 데이터 수집만, 최적화는 후속)
- Agent 내부 ThreadPoolExecutor 계측 (chief_writer, arc_ensemble 등 8곳) — **후속 확장**
- Stage4 ThreadPoolExecutor — **해당 없음** (Stage4는 미사용)

---

## 3) 설계안

### 3-1. PerfTimer 훅 삽입 지점

기존 PerfTimer 인스턴스(`self.ctx.perf_timer`)를 그대로 활용. 신규 인프라 불필요.

#### 삽입 지점 1: 병렬 블록 전체 (외곽 타이머)

```
L889 삽입 → perf_timer.start(f"s2_arc_{global_arc_no}_preflight_parallel")
L890     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
L891         _fut_drive = _parallel_exec.submit(_compute_arc_drive)
L892         _fut_preflight = _parallel_exec.submit(_compute_preflight)
L893         arc_drive = _fut_drive.result()
L894         _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result()
L895 삽입 → _elapsed = perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_parallel")
```

- **step 이름**: `s2_arc_{global_arc_no}_preflight_parallel`
- **측정 대상**: 2개 LLM 호출의 총 병렬 실행 시간
- **기대값**: 15~30초 (두 호출 중 느린 쪽이 결정)

#### 삽입 지점 2: 개별 태스크 (내부 타이머, 선택)

중첩 함수 `_compute_arc_drive()`, `_compute_preflight()` 내부에 start/stop 삽입:

```
# _compute_arc_drive() 내부
perf_timer.start(f"s2_arc_{global_arc_no}_arc_drive")
result = self.ctx.agents["weaver"].generate_arc_drive(...)
perf_timer.stop(f"s2_arc_{global_arc_no}_arc_drive")

# _compute_preflight() 내부
perf_timer.start(f"s2_arc_{global_arc_no}_preflight_analysis")
_pf_result = self.ctx.agents["preflight"].analyze(...)
perf_timer.stop(f"s2_arc_{global_arc_no}_preflight_analysis")
```

- **step 이름**: `s2_arc_{N}_arc_drive`, `s2_arc_{N}_preflight_analysis`
- **측정 대상**: 각 LLM 호출의 개별 소요 시간
- **기대 효과**: 병렬 효율성 = max(drive, preflight) vs (drive + preflight) 비교 가능
- **주의**: 중첩 함수에서 `self.ctx.perf_timer` 접근 가능 (closure 캡처)

### 3-2. 로그 포맷/레벨

| 이벤트 | 레벨 | 포맷 |
|--------|------|------|
| 정상 완료 | `INFO` | `[PerfTimer:Pipeline] s2_arc_3_preflight_parallel=18.45s` (기존 log_summary에 자동 포함) |
| 타이머 시작/종료 실패 | `—` | 무시 (기존 `try/except: pass` 패턴) |
| 개별 태스크 타임아웃 | `WARNING` | `[V65] preflight_parallel 30s 초과` (선택, threshold 기반) |

### 3-3. 실패 시 비전파 원칙 (soft-fail)

기존 Stage2 PerfTimer 패턴을 그대로 적용:

```python
try:
    self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_preflight_parallel")
except Exception:
    pass  # PerfTimer 실패 시 비전파 — 파이프라인 동작 불변
```

- PerfTimer가 None이거나 예외 발생해도 파이프라인 정상 진행
- 이 패턴은 이미 L1215-1218, L1233-1236, L2001-2004, L2063-2066에서 4회 사용 중

---

## 4) 수용 기준 (AC)

| # | 수용 기준 | 검증 방법 |
|---|----------|----------|
| AC-1 | `_preflight_state_setup()` 실행 시 `s2_arc_{N}_preflight_parallel` 타이머가 기록됨 | Unit: mock perf_timer → start/stop 호출 검증 |
| AC-2 | `perf_timer.summary()`에 `s2_arc_{N}_preflight_parallel` 키가 포함됨 | Unit: summary dict 키 검증 |
| AC-3 | 개별 태스크 타이머(`s2_arc_{N}_arc_drive`, `s2_arc_{N}_preflight_analysis`)가 기록됨 | Unit: mock perf_timer → 3개 step 호출 검증 |
| AC-4 | PerfTimer가 None이거나 예외 발생 시 `_preflight_state_setup()`가 정상 완료 | Unit: perf_timer=None + perf_timer.start side_effect=RuntimeError → 정상 반환 |
| AC-5 | 기존 테스트 258개 전량 통과 (회귀 없음) | Gate: pytest 5 스위트 |
| AC-6 | `log_summary()` 출력에 preflight_parallel 구간이 포함됨 | Unit: caplog에서 `preflight_parallel` 키워드 확인 |

---

## 5) 테스트 전략

### Unit 테스트 (4~5개)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | `test_preflight_parallel_timer_recorded` | mock perf_timer → start/stop 호출 3회(parallel + arc_drive + preflight) |
| 2 | `test_preflight_parallel_elapsed_positive` | 실제 PerfTimer → summary()에 elapsed > 0 |
| 3 | `test_perf_timer_none_no_crash` | perf_timer=None → `_preflight_state_setup()` 정상 반환 |
| 4 | `test_perf_timer_exception_non_propagating` | perf_timer.start side_effect=RuntimeError → 정상 반환 |
| 5 | `test_summary_includes_all_steps` | 실제 PerfTimer → summary() 키에 3개 step 존재 |

### 테스트 방식

- **LLM mock**: `agents["weaver"].generate_arc_drive = MagicMock(return_value={...})`
- **PerfTimer**: 실제 인스턴스(test 2, 5) 또는 MagicMock(test 1, 3, 4)
- **외부 API 호출**: 0건
- **기존 fixture**: `s2_ctx` / `s2_orch` (test_stage2_preflight_helpers.py 패턴)

### 회귀 스위트

| 스위트 | 통과 기대 |
|--------|----------|
| `test_stage2_preflight_helpers.py` | 38 |
| `test_quality_regression.py` | 15 |
| `test_stage2_pipeline.py` + `test_stage2_context.py` | 89 |
| `tests/e2e/` | 22 |
| `test_npc_history` + `test_config_manager` + `test_stage4_orchestrator` | 94 |
| **합계** | **258** (불변) |

---

## 6) 실행 단계 계획

### Step 1: 최소 삽입 — PerfTimer 훅 3개소

**수정 파일**:
- `modules/core/stage2_orchestrator.py` — `_preflight_state_setup()` 내 3개 timer 삽입 (~12줄)

**삽입 내용**:
1. 외곽 타이머: L889 start, L895 stop (`s2_arc_{N}_preflight_parallel`)
2. arc_drive 타이머: `_compute_arc_drive()` 내부 start/stop (`s2_arc_{N}_arc_drive`)
3. preflight 타이머: `_compute_preflight()` 내부 start/stop (`s2_arc_{N}_preflight_analysis`)

**종료 조건**:
- `python -m py_compile modules/core/stage2_orchestrator.py` 통과
- `python -c "from main_a import SovereignApp; print('OK')"` 통과

### Step 2: 테스트 + 게이트

**수정 파일**:
- `tests/test_stage2_preflight_helpers.py` — `TestPreflightParallelTimer` 클래스 추가 (~50줄, 4~5 테스트)

**게이트**:
1. `py_compile` 수정 파일
2. SovereignApp import
3. `pytest tests/test_stage2_preflight_helpers.py -q`
4. `pytest tests/test_stage2_pipeline.py tests/test_stage2_context.py -q`
5. `pytest tests/e2e/ -q`
6. `pytest tests/test_npc_history.py tests/test_config_manager.py tests/test_stage4_orchestrator.py -q`
7. `pre-commit run --files` 수정 파일

**종료 조건**:
- 신규 테스트 4~5건 + 기존 258건 전량 통과
- pre-commit 통과

### Step 3: 문서 동기화

**수정 파일**:
- `내일작업.md` — 완료 행 추가, 테스트 기준선 갱신, 우선순위 갱신
- `docs/프로젝트_현황_로드맵_2026-02-14.md` — checkpoint/테스트/완료 갱신
- `CLAUDE.md` — checkpoint/테스트/완료/RISKY 갱신
- 본 문서 상태 → "완료"

**종료 조건**:
- 4개 문서 checkpoint/테스트 수 일치
- 커밋 + push

---

## 7) 참고: 에이전트 레벨 확장 경로

이번 범위는 Stage2 오케스트레이터만. 향후 확장 시:

| 파일 | 메서드 | 병렬 작업 | 우선순위 |
|------|--------|----------|---------|
| `chief_writer.py` | `_generate_candidates()` | 3 원고 후보 앙상블 | 높음 (Stage4 핵심 병목) |
| `blueprint_ensemble.py` | `generate()` | 3 블루프린트 전략 | 중간 |
| `arc_ensemble.py` | `generate()` | 3 아크 전략 | 중간 |
| `consensus_validator.py` | `_validate_perspectives()` | N 검증 관점 | 낮음 |
| `director_auditor.py` | `_self_consistency_vote()` | 3 자기일관성 투표 | 낮음 |

---

## 8) 롤백 전략

| 방법 | 조치 |
|------|------|
| **코드 롤백** | `git revert <commit>` — 계측 코드만 제거, 파이프라인 동작 불변 |
| **런타임 비활성화** | `perf_timer = None` 설정 → try/except: pass로 전량 스킵 |
| **영향 범위** | 관측 전용이므로 비활성화 시 기존 동작과 100% 동일 |
