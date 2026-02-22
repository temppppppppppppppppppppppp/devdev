# Opus TF-4: Concurrency Safety Audit

**Date**: 2026-02-22
**Auditor**: Claude Opus 4.6
**Scope**: modules/ 전체 동시성 패턴 전수 조사
**Method**: 소스 코드 직접 열람 기반

---

## 1. ThreadPoolExecutor 사용처 전수 목록

### 1-1. `modules/domain/agents/arc_ensemble.py` (L136)

| 항목 | 내용 |
|------|------|
| **max_workers** | 3 (고정, `self.max_workers`) |
| **용도** | Arc 후보 3개 전략 병렬 생성 (conservative / balanced / creative) |
| **타임아웃** | 전체 300초, 개별 240초 |
| **공유 상태** | `self.context`, `self.client` (BaseAgent 인스턴스) |
| **패턴** | `with ThreadPoolExecutor as executor` + `as_completed` + `future.cancel()` cleanup |
| **보호** | genre를 사전 로드하여 스레드 내 DB 접근 제거 (L121-129). 각 `_generate_single` 호출은 `self.ask()`를 호출하는데, `self.client`는 읽기 전용이므로 안전. |
| **위험도** | **LOW** |
| **비고** | L191-193에서 미완료 future를 `cancel()` 처리. `cancel()`은 PENDING 상태에만 유효하고 RUNNING 스레드를 중단하지 못하지만, `with` 블록 종료 시 `shutdown(wait=True)`가 암묵 호출되므로 대기 후 정리됨. |

### 1-2. `modules/domain/agents/chief_writer.py` (L252)

| 항목 | 내용 |
|------|------|
| **max_workers** | 3 (고정) |
| **용도** | 원고 후보 3개 전략 병렬 생성 (balanced / narrative / tension) |
| **타임아웃** | `self.ENSEMBLE_TIMEOUT` (전체), `self.SINGLE_CANDIDATE_TIMEOUT` (개별) |
| **공유 상태** | `self.context`, `self.client` (BaseAgent 인스턴스), Context Cache |
| **패턴** | arc_ensemble과 동일 패턴 (as_completed + cancel) |
| **보호** | `_cache_lock`으로 `_context_caches` 보호 (BaseAgent L1137). |
| **위험도** | **LOW** |
| **비고** | `_generate_single_candidate` 내부에서 `_ask_with_cached_context`를 호출할 수 있는데, 캐시 조회/생성은 `_cache_lock`으로 보호됨. |

### 1-3. `modules/core/stage2_preflight.py` (L273)

| 항목 | 내용 |
|------|------|
| **max_workers** | 3 |
| **용도** | arc_drive + preflight + constraint_block 3개 독립 작업 병렬 |
| **타임아웃** | arc_drive/preflight 300초, constraint 60초 |
| **공유 상태** | `self.ctx.perf_timer` (PerfTimer 인스턴스) |
| **패턴** | `with ThreadPoolExecutor` + 개별 `future.result(timeout=)` |
| **보호** | `_perf_lock = threading.Lock()` (L194, 함수 로컬) — perf_timer.start/stop 호출을 보호 |
| **위험도** | **LOW** |
| **비고** | perf_timer 보호를 위한 전용 Lock이 함수 로컬 스코프에서 생성되어 Arc 단위로 독립적. `_compute_constraint_block`은 perf_timer를 사용하지 않아 Lock 불필요. |

### 1-4. `modules/core/stage4_post_processor.py` (L197)

| 항목 | 내용 |
|------|------|
| **max_workers** | 1 (`thread_name_prefix="bible_settle"`) |
| **용도** | Manager Bible 정산 LLM 호출을 비동기로 제출, 독립 작업 수행 후 future 회수 |
| **타임아웃** | `_bible_future.result(timeout=120)` (L299) |
| **공유 상태** | `self.ctx.agents["manager"]` (Manager 에이전트 인스턴스) |
| **패턴** | submit + shutdown(wait=False) + 이후 result(timeout=) 회수 |
| **보호** | 단일 워커이므로 병렬 경합 없음 |
| **위험도** | **MEDIUM** |
| **시나리오** | `shutdown(wait=False)` 호출 후 executor 참조가 로컬 변수이므로 GC 대상이 될 수 있으나, `_bible_future`가 참조를 유지하므로 실제 GC는 발생하지 않음. 단, `result(timeout=120)` 타임아웃 후 future가 여전히 RUNNING이면 백그라운드 스레드가 계속 실행된다. Manager LLM 호출이 2분 이상 걸릴 경우, 해당 스레드는 제어 불능 상태로 남는다. |
| **권고** | 타임아웃 후 `_bible_future.cancel()`을 호출하고, 후속 DB 작업과의 충돌 가능성을 로그로 경고할 것. 현재도 except 블록에서 동기 폴백을 수행하지만, 타임아웃된 비동기 스레드가 나중에 완료되어 DB에 쓸 경우 이중 기록 가능성 있음. |

### 1-5. `modules/validation/validation_orchestrator.py` (L1104)

| 항목 | 내용 |
|------|------|
| **max_workers** | `self.max_parallel_workers` (설정 가능) |
| **용도** | consistency + scoring + advisory 3개 검증 병렬 실행 |
| **타임아웃** | 없음 (asyncio.gather에 타임아웃 미설정) |
| **공유 상태** | 각 validator 인스턴스, manuscript, validation_context |
| **패턴** | `asyncio.get_running_loop()` + `loop.run_in_executor()` + `asyncio.gather(return_exceptions=True)` |
| **보호** | `return_exceptions=True`로 개별 실패 격리. 각 validator가 독립적 상태를 가짐. |
| **위험도** | **LOW** |
| **비고** | asyncio 이벤트 루프 내부에서 ThreadPool을 사용하는 올바른 패턴. 타임아웃이 없지만, 실제 운영에서 LLM API 호출 자체에 BaseAgent.API_TIMEOUT이 적용되므로 무한 대기는 발생하지 않음. |

### 1-6. `modules/validation/batch_validator.py` (L62-64, L134)

| 항목 | 내용 |
|------|------|
| **max_workers** | `max_concurrent` (기본 10) |
| **용도** | 여러 원고 동시 검증 (async 모드: run_in_executor, sync 모드: executor.map) |
| **타임아웃** | 없음 |
| **공유 상태** | `self.stats` dict, `self._stats_lock` |
| **패턴** | 두 가지 경로: (1) asyncio + run_in_executor + gather (2) ThreadPoolExecutor.map |
| **보호** | `_stats_lock`으로 stats 접근 보호 |
| **위험도** | **LOW** |
| **비고** | asyncio.run 호출 시 중첩 이벤트 루프 감지 로직 포함 (L273-291). Nested loop 방지를 위해 ThreadPool 동기 모드로 자동 폴백. |

### 1-7. `modules/domain/agents/block_enricher.py` (L641)

| 항목 | 내용 |
|------|------|
| **max_workers** | `batch_size` (가변) |
| **용도** | 트리트먼트 블록 배치 농축 |
| **타임아웃** | 전체 600초, 개별 60초 |
| **공유 상태** | `enriched_blocks` dict, `stats` dict |
| **패턴** | `with ThreadPoolExecutor` + `as_completed(timeout=600)` + 개별 `future.result(timeout=60)` |
| **보호** | 각 future의 결과를 인덱스 기반으로 dict에 저장 (서로 다른 키). 미처리 블록 원본 유지 폴백 (L664-667). |
| **위험도** | **MEDIUM** |
| **시나리오** | `enriched_blocks[idx]` 와 `stats["enriched_count"] += 1` 접근이 Lock 없이 수행됨. 그러나 각 future가 서로 다른 `idx`를 담당하므로 dict 키 충돌은 없음. `stats` 카운터의 `+=` 연산은 CPython GIL 하에서 원자적이지 않지만, 실질적으로 count 오차 수준의 문제이므로 운영 영향은 낮음. |
| **권고** | `stats` 카운터를 `threading.Lock`이나 `collections.Counter`로 보호하면 정합성 향상. |

---

## 2. asyncio 사용처

### 2-1. `modules/core/stage2_orchestrator.py` (L250)

```python
enriched_batch = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
```

| 항목 | 내용 |
|------|------|
| **용도** | 블록 농축 병렬 실행 |
| **패턴** | `return_exceptions=True` |
| **위험도** | **LOW** |
| **비고** | 예외를 Exception 객체로 수집하여 부분 실패 허용. 호출측에서 isinstance 체크로 실패 분기 처리. |

### 2-2. `modules/validation/validation_orchestrator.py` (L1125)

```python
parallel_results = await asyncio.gather(
    consistency_task, scoring_task, advisory_task,
    return_exceptions=True,
)
```

| 항목 | 내용 |
|------|------|
| **용도** | 3개 검증기 병렬 실행 (ThreadPool + asyncio 하이브리드) |
| **패턴** | `asyncio.get_running_loop()` + `run_in_executor` + `gather(return_exceptions=True)` |
| **위험도** | **LOW** |
| **비고** | Sweep7-A에서 `return_exceptions=True` 추가 완료. 실패 시 None 폴백으로 안전 처리. |

### 2-3. `modules/validation/batch_validator.py` (L81)

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
```

| 항목 | 내용 |
|------|------|
| **용도** | 배치 검증 병렬 실행 |
| **패턴** | `asyncio.Semaphore` + `run_in_executor(None, ...)` + `gather(return_exceptions=True)` |
| **위험도** | **LOW** |
| **비고** | `run_in_executor(None, ...)`는 기본 ThreadPoolExecutor를 사용. Semaphore로 동시 실행 수 제한. Sweep7-A에서 Exception 타입 체크 후 안전 폴백 추가. |

### 2-4. asyncio + ThreadPool 혼합 패턴 평가

현재 코드베이스에서 asyncio와 ThreadPool을 혼합하는 곳은 `validation_orchestrator.py`와 `batch_validator.py`이다. 두 곳 모두 올바른 패턴을 따른다:

- `asyncio.get_running_loop()` (deprecated `get_event_loop()` 아님)
- `loop.run_in_executor()` — 동기 함수를 비동기로 변환하는 표준 방법
- `return_exceptions=True` — 부분 실패 격리

**중첩 이벤트 루프 방지**: `batch_validator.py` L273-291에서 `asyncio.get_running_loop()` 존재 시 ThreadPool 동기 모드로 자동 폴백하는 안전 장치가 구현되어 있다.

---

## 3. 공유 상태 접근 분석

### 3-1. `base_agent.py` 클래스 변수 (전 인스턴스 공유)

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `_quota_exhausted_models` (dict) | `_quota_lock` (Lock) | read: L329 snapshot / write: L519, L202 clear | **SAFE** |
| `_key_rotation_pending` (bool) | `_rotation_lock` (RLock) | read: L310 / write: L185,190,195,205,524 | **SAFE** |
| `_current_key_idx` (int) | `_rotation_lock` (RLock) | read/write: L198-199 | **SAFE** |
| `_keys_initialized` (bool) | `_rotation_lock` (RLock) | TOCTOU 해결: L162-166 전체 Lock 내부 | **SAFE** |
| `_context_caches` (dict) | `_cache_lock` (Lock) | read: L1172-1173 / write: L1203-1215 / clear: L204 | **SAFE** |
| `_api_keys` (list) | `_rotation_lock` (RLock) | 초기화 후 읽기 전용 | **SAFE** |
| `_rotation_count` (int) | `_rotation_lock` (RLock) | L189,201 / L418 성공 시 리셋 | **SAFE** |

**세부 분석**:

- `_quota_exhausted_models`: L329에서 `dict(...)` 스냅샷을 Lock 내에서 생성 후 Lock 밖에서 읽기 전용 사용. TOCTOU 패턴 제거 완료.
- `_key_rotation_pending`: L310에서 Lock 내 읽기 후 Lock 밖에서 `_try_rotate_key()` 호출. `_try_rotate_key` 내부에서 다시 Lock 획득하므로 안전. `_rotation_lock`이 RLock이라 재진입 가능.
- `_context_caches`: L204에서 `_cache_lock` 내에서 `.clear()` 수행. L1172-1179에서 `.get()` + `.pop()` 패턴으로 TOCTOU 제거 완료 (TF-R4 주석 확인).

### 3-2. `db_manager.py` (DBManager 인스턴스)

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `self.conn` (Connection) | `self._lock` (RLock) | 모든 메서드에서 `with self._lock:` 사용 | **SAFE** |
| `self.cursor` (Cursor, legacy) | `self._lock` (RLock) | 대부분 `with self._lock:` 내에서 사용 | **MEDIUM** |
| `self._cumulative_bible_cache` | 없음 | `_boot_db`에서만 초기화 | **LOW** |

**`self.cursor` 상세 분석**:

`self.cursor`는 레거시 공유 커서로, INF-P1-1 주석에서 "신규 코드에서는 local cursor 사용 권장"이라고 명시되어 있다. 실제로 대부분의 메서드에서 `with self._lock:` 블록 안에서 `self.cursor`를 사용하므로 동시 접근은 차단된다.

그러나 `commit_episode_factory` (L1262-1435)에서는 `self._lock.acquire()` / `self._lock.release()`를 수동으로 호출하면서 내부에서 `self.update_karma()`, `self.save_causal_links()` 등 다른 `with self._lock:` 메서드를 호출한다. RLock이므로 재진입이 허용되어 데드락은 발생하지 않지만, 수동 acquire/release 패턴은 예외 발생 시 Lock 누출 위험이 있다. 현재는 `finally` 블록 (L1433-1435)에서 `self._lock.release()`를 보장하므로 안전하다.

### 3-3. `vec_memory.py` (VecMemory 인스턴스)

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `_embed_cache` (OrderedDict) | `_embed_cache_lock` (Lock) | get: L280-283 / put: L288-294 | **SAFE** |
| `_conn` (Connection) | `_lock` (shared, DBManager RLock) or None | shared 모드: `_db_lock()` 컨텍스트매니저 | **SAFE** |

**세부 분석**:

- `_embed_cache`: `_embed_cache_lock`으로 일관되게 보호. LRU 퇴출 로직(L293)도 Lock 내에서 수행.
- shared 모드에서 `_lock`은 DBManager의 RLock을 공유받아 사용. standalone 모드에서는 Lock이 None이므로 `_db_lock()`이 no-op.

### 3-4. `metrics_collector.py` (MetricsCollector 싱글톤)

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `_metrics` (dict) | `self._lock` (RLock) | start_call: L170-178 / end_call: L200+ | **SAFE** |
| `_agent_calls`, `_agent_durations` 등 | `self._lock` (RLock) | 모두 Lock 내 접근 | **SAFE** |
| `_instance` (클래스 변수) | `_lock` (클래스 RLock) | DCL 싱글톤 (L101-107) | **SAFE** |

### 3-5. `config_manager.py`

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `_validation_settings` | `_settings_lock` (클래스 Lock) | lazy load 시 보호 | **SAFE** |

### 3-6. `prompt_loader.py` (PromptLoader 싱글톤)

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `_instance` | `_instance_lock` (Lock) | DCL 싱글톤 (L36-41) | **SAFE** |
| `_cache` (dict) | `_cache_lock` (Lock) | read: L64-66 / write: L71-72, L135-136 | **SAFE** |

**세부 분석**: `_load_yaml_file`에서 캐시 미스 시 Lock 밖에서 파일 I/O를 수행한 뒤 Lock 안에서 결과를 저장한다 (L64-67 read, L68-138 load, L135-136 write). 동일 domain에 대해 두 스레드가 동시에 캐시 미스를 경험하면 파일을 두 번 읽게 되지만, 결과는 동일하므로 정합성 문제 없음 (중복 작업만 발생, 멱등성 보장).

### 3-7. `data_collector.py` 통계 카운터

| 변수 | Lock | 접근 패턴 | 위험도 |
|------|------|----------|--------|
| `self.stats["approved_count"]` 등 | 없음 | `+=` 연산 (L95, 98, 100) | **MEDIUM** |
| `self._sequence_counter` | `self._lock` (Lock) | L108-113에서 Lock 내 접근 | **SAFE** |

**시나리오**: `collect_validation_result`에서 `stats` dict의 `+=` 연산이 Lock 없이 수행됨. `_save_approved`/`_save_rejected`는 `_lock`으로 보호되지만, `stats` 업데이트는 Lock 밖에서 수행. 병렬 검증 시나리오에서 카운터 오차 발생 가능.

### 3-8. 기타 싱글톤 팩토리 함수

| 함수 | 위치 | DCL 패턴 | 위험도 |
|------|------|----------|--------|
| `get_item_registry()` | `semantic_item_registry.py:769-776` | `_registry_lock` + DCL | **SAFE** |
| `get_dashboard()` | `quality_dashboard.py:1087-1094` | `_dashboard_lock` + DCL | **SAFE** |
| `get_adaptive_retry()` | `adaptive_retry.py:440-447` | `_adaptive_retry_lock` + DCL | **SAFE** |
| `get_primitive_guard()` | `primitive_guard.py:26-31` | `_primitive_guard_lock` + DCL | **SAFE** |
| `StudioLogger.__new__()` | `logger.py:46-52` | `_lock` + DCL | **SAFE** |
| `get_pass_rate_monitor()` | `pass_rate_monitor.py:532+` | `_monitor_lock` + DCL | **SAFE** |
| `MetricsCollector.__new__()` | `metrics_collector.py:101-107` | `_lock` (RLock) + DCL | **SAFE** |

모든 싱글톤이 Double-Checked Locking 패턴을 올바르게 구현하고 있다.

### 3-9. `reset_dashboard()` 비보호 리셋

| 항목 | 내용 |
|------|------|
| **위치** | `quality_dashboard.py:1097-1100` |
| **코드** | `global _dashboard_instance; _dashboard_instance = None` |
| **위험도** | **LOW** |
| **시나리오** | Lock 없이 전역 변수를 None으로 설정. 다른 스레드가 동시에 `get_dashboard()`를 호출하면 이미 생성된 인스턴스를 사용 중일 수 있음. 그러나 이 함수는 프로젝트 전환 시에만 호출되며, 그 시점에서 병렬 검증이 진행 중일 가능성은 극히 낮음. |
| **권고** | `with _dashboard_lock:` 래핑 권장 (방어적 프로그래밍). |

---

## 4. Race Condition 위험 분석

### 4-1. [RESOLVED] base_agent TOCTOU 패턴

**위치**: `base_agent.py` L162-166 (`_init_api_keys`)

이전 감사에서 발견된 check-then-act 패턴은 TF-XC-05에서 수정 완료. `_keys_initialized` 확인과 설정이 모두 `_rotation_lock` 내부로 이동되었다.

```python
with cls._rotation_lock:
    if cls._keys_initialized:
        return
    cls._keys_initialized = True
```

**판정**: SAFE.

### 4-2. [RESOLVED] base_agent `_context_caches` TOCTOU

**위치**: `base_agent.py` L1172-1173

TF-R4에서 `.get()`으로 변경하여 KeyError 방지 완료. `.clear()` (L204)와의 경합도 `_cache_lock`으로 보호.

**판정**: SAFE.

### 4-3. [ACTIVE] `data_collector.py` stats 비보호 증분

**위치**: `data_collector.py` L95, 98, 100

```python
self.stats["approved_count"] += 1  # Lock 없음
```

| 항목 | 내용 |
|------|------|
| **위험도** | **MEDIUM** |
| **시나리오** | `batch_validator`의 ThreadPoolExecutor 내에서 `validate_one` → `orchestrator.validate` → `data_collector.collect_validation_result`가 병렬 호출될 때, `stats` 카운터에 lost update 발생 가능. |
| **영향** | 통계 수치 오차. 운영 기능에는 영향 없음 (통계는 리포팅 전용). |
| **권고** | `with self._lock:` 블록으로 `stats` 업데이트를 감쌀 것. 또는 `threading.Lock`을 별도 추가. |

### 4-4. [ACTIVE] `block_enricher.py` stats 비보호 증분

**위치**: `block_enricher.py` L651, 654

```python
stats["enriched_count"] += 1  # Lock 없음
stats["failed_count"] += 1    # Lock 없음
```

| 항목 | 내용 |
|------|------|
| **위험도** | **LOW** |
| **시나리오** | ThreadPoolExecutor 콜백에서 stats 카운터 증분. CPython GIL이 dict 연산의 원자성을 부분 보장하지만, `+=`는 read-modify-write이므로 lost update 가능. |
| **영향** | 통계 오차 (진단용 카운터). |
| **권고** | `threading.Lock` 추가 또는 `threading.atomic` 패턴 적용. |

### 4-5. [INFORMATIONAL] `_key_rotation_pending` 읽기-후-행동

**위치**: `base_agent.py` L309-313

```python
with BaseAgent._rotation_lock:
    pending = BaseAgent._key_rotation_pending  # Lock 내 읽기
if pending:                                     # Lock 밖 판단
    new_client = self._try_rotate_key()         # 다시 Lock 획득
```

| 항목 | 내용 |
|------|------|
| **위험도** | **LOW** |
| **시나리오** | Lock 해제 후 `pending` 상태가 다른 스레드에 의해 변경될 수 있으나, `_try_rotate_key` 내부에서 다시 `_rotation_lock`을 획득하고 최신 상태를 재확인하므로 실질적 문제 없음. 최악의 경우 불필요한 `_try_rotate_key` 호출이 1회 발생하는 수준. |
| **판정** | 의도적 설계. |

### 4-6. [INFORMATIONAL] `MetricsCollector.reset()` 경합

**위치**: `metrics_collector.py` L110-115

```python
@classmethod
def reset(cls, metrics_dir=None):
    with cls._lock:
        cls._instance = None
    if metrics_dir:
        return cls(metrics_dir)  # Lock 밖에서 새 인스턴스 생성
```

| 항목 | 내용 |
|------|------|
| **위험도** | **LOW** |
| **시나리오** | Lock 해제 후 `cls(metrics_dir)` 호출 사이에 다른 스레드가 `get_metrics_collector()`를 호출하면, 두 개의 인스턴스가 순간적으로 존재할 수 있음. 그러나 `__new__`에서 DCL로 재확인하므로 최종적으로 하나만 유지됨. |
| **판정** | 무해한 일시적 중복. 프로젝트 변경 시에만 호출되므로 운영 영향 없음. |

---

## 5. 데드락 가능성 분석

### 5-1. `db_manager.py` RLock 재진입

**위치**: `db_manager.py` 전체

| 항목 | 내용 |
|------|------|
| **Lock 종류** | `threading.RLock()` (L63) |
| **재진입 패턴** | `commit_episode_factory` (L1281 acquire) → `save_manuscript`, `update_karma`, `save_causal_links` 등 → 각각 `with self._lock:` |
| **판정** | **SAFE** — RLock은 동일 스레드의 재진입을 허용하므로 데드락 없음. |

**경고**: 만약 누군가 `self._lock`을 `threading.Lock()`으로 변경하면 즉시 데드락이 발생한다. 이 계약은 `commit_episode_factory` 내부의 수동 acquire/release 패턴 + 내부 메서드의 `with self._lock:` 패턴에 의해 암묵적으로 의존된다.

### 5-2. `base_agent.py` 중첩 Lock 획득

**위치**: `base_agent.py` L200-204

```python
with cls._rotation_lock:          # RLock 획득 (1)
    cls._quota_exhausted_models.clear()
    with cls._cache_lock:          # Lock 획득 (2)
        cls._context_caches.clear()
```

| 항목 | 내용 |
|------|------|
| **순서** | `_rotation_lock` → `_cache_lock` (항상 이 순서) |
| **역순 존재 여부** | `_cache_lock` → `_rotation_lock` 순서는 코드베이스에 존재하지 않음 |
| **판정** | **SAFE** — 단방향 Lock 획득 순서가 일관되게 유지됨. |

### 5-3. `base_agent.py` `_rotation_lock` + `_quota_lock` 혼합

**확인**:

- `_try_rotate_key` 내부 (L182): `_rotation_lock` 획득 상태에서 `_quota_exhausted_models.clear()` 호출 — 여기서는 `_quota_lock`을 사용하지 않음 (L202).
- `ask` 내부 (L518): `_quota_lock` 획득 → `_rotation_lock` 획득 (L522-523).
- `ask` 내부 (L328): `_quota_lock` 획득 → 해제 → L309-310 `_rotation_lock` 획득.

L518-523 경로: `_quota_lock` → `_rotation_lock` 순서.
L202: `_rotation_lock` 내에서 `_quota_exhausted_models.clear()` 직접 접근 (Lock 없음).

| 항목 | 내용 |
|------|------|
| **위험도** | **MEDIUM** |
| **시나리오** | L202에서 `_rotation_lock` 내에서 `_quota_exhausted_models.clear()`를 `_quota_lock` 없이 수행. 동시에 다른 스레드가 L518에서 `_quota_lock`을 획득하고 `_quota_exhausted_models`에 쓰려 하면, clear와 write가 동시 발생할 수 있다. CPython dict.clear()는 GIL 하에서 원자적이므로 크래시는 발생하지 않지만, clear 직후 다시 데이터가 추가되는 "lost clear" 상황이 가능. |
| **영향** | 키 순환 시 방금 추가된 쿼터 소진 기록이 유지될 수 있음. 키가 바뀌었으므로 새 키에서 다시 시도하면 되기 때문에 실질적 영향 미미. |
| **권고** | L202를 `with cls._quota_lock:` 블록으로 감싸면 이론적 정합성 향상. 현재 운영에서는 문제 발생 가능성 극히 낮음. |

### 5-4. 잠재적 데드락 경로 전체 검토

코드베이스 전체에서 두 개 이상의 Lock을 동시에 획득하는 경로:

| Lock 1 | Lock 2 | 위치 | 역순 존재 | 판정 |
|--------|--------|------|----------|------|
| `_rotation_lock` | `_cache_lock` | base_agent L200-204 | 없음 | **SAFE** |
| `_quota_lock` | `_rotation_lock` | base_agent L518-523 | L202에서 역순 가능 (주의) | **CONDITIONAL** |
| `DBManager._lock` | (내부 재진입) | db_manager 전체 | RLock이므로 무관 | **SAFE** |

**결론**: 현재 코드에서 데드락이 발생할 수 있는 경로는 발견되지 않았다. `_quota_lock` + `_rotation_lock`의 역순 가능성이 유일한 우려사항이나, L202의 `_quota_exhausted_models.clear()`가 Lock 없이 직접 접근하므로 Lock 교차 자체가 발생하지 않는다 (데드락 아닌 데이터 경합 문제).

---

## 6. 타임아웃과 취소 분석

### 6-1. `arc_ensemble.py` 타임아웃 처리

```python
for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):  # 300초
    result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)     # 240초
```

| 항목 | 내용 |
|------|------|
| **패턴** | 이중 타임아웃 (전체 + 개별) |
| **미완료 처리** | `finally` 블록에서 `f.cancel()` (L192-193) |
| **한계** | `cancel()`은 PENDING 상태 future에만 유효. RUNNING 상태 스레드는 중단 불가 (Python 한계). `with` 블록 종료 시 `shutdown(wait=True)`가 암묵 호출되어 RUNNING 스레드 완료를 대기. |
| **위험도** | **LOW** |
| **비고** | 코드 주석 (L275-277)에 이 한계가 문서화되어 있음: "Python ThreadPoolExecutor는 실행 중인 스레드를 강제 중단할 수 없으므로, LLM API 호출이 T초를 초과하면 실제 대기 시간 > T가 될 수 있다." |

### 6-2. `chief_writer.py` 타임아웃 처리

arc_ensemble과 동일 패턴. 동일한 한계와 보호 조치 적용.

### 6-3. `stage4_post_processor.py` Bible Future 타임아웃

```python
_bible_executor = ThreadPoolExecutor(max_workers=1)
_bible_future = _bible_executor.submit(...)
_bible_executor.shutdown(wait=False)  # 비대기 종료
...
raw_audit = _bible_future.result(timeout=120)  # 나중에 회수
```

| 항목 | 내용 |
|------|------|
| **위험도** | **MEDIUM** |
| **시나리오** | `shutdown(wait=False)` 호출 후 executor는 새 작업을 거부하지만, 이미 제출된 작업은 계속 실행. `result(timeout=120)` 타임아웃 시: (1) except 블록에서 동기 폴백 수행 (L302-309), (2) 타임아웃된 백그라운드 스레드는 여전히 Manager LLM 호출 중. 이 스레드가 나중에 완료되어 Manager가 DB에 쓰려 할 때, 메인 스레드의 `commit_episode_factory`와 충돌 가능. |
| **실제 발생 확률** | 매우 낮음. Manager LLM 호출이 2분을 초과하는 경우는 극히 드물며, 실제로는 BaseAgent.API_TIMEOUT (90초)에 의해 API 호출 자체가 먼저 실패. |
| **권고** | 타임아웃 후 `_bible_future.cancel()` 호출 추가. Manager 에이전트의 `update_state_and_lore_v20`가 DB에 직접 쓰지 않고 결과만 반환하는 순수 함수이므로, 실질적 충돌 위험은 낮으나 방어적 cancel 추가 권장. |

### 6-4. `stage2_preflight.py` 타임아웃 처리

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as _parallel_exec:
    arc_drive = _fut_drive.result(timeout=300)
    _cached_preflight_injection, _ = _fut_preflight.result(timeout=300)
    constraint_block = _fut_constraint.result(timeout=60)
```

| 항목 | 내용 |
|------|------|
| **위험도** | **LOW** |
| **시나리오** | `result(timeout=)` 타임아웃 시 except 블록 (L280-281)에서 경고 후 기본값 사용. `with` 블록이 정리를 보장. 순차적 `result()` 호출이므로, 첫 번째가 300초 걸리면 나머지 타임아웃은 이미 소모된 시간만큼 줄어들 수 있으나, `with` 블록 종료 시 모든 미완료 future가 정리됨. |

### 6-5. `block_enricher.py` 타임아웃 처리

```python
for future in concurrent.futures.as_completed(futures, timeout=600):
    idx, result = future.result(timeout=60)
```

| 항목 | 내용 |
|------|------|
| **미완료 처리** | L671-672에서 `f.cancel()` 호출. except 블록 (L662-668)에서 미처리 블록 원본 유지. |
| **위험도** | **LOW** |
| **비고** | 가장 방어적인 패턴 중 하나. 타임아웃 시 원본 블록을 유지하는 graceful degradation. |

---

## 7. 발견 사항 요약

### CRITICAL: 없음

현재 코드베이스에서 즉각적인 데이터 손실이나 크래시를 유발하는 동시성 결함은 발견되지 않았다.

### HIGH: 없음

### MEDIUM: 3건

| # | 위치 | 설명 | 시나리오 | 권고 |
|---|------|------|----------|------|
| M-1 | `stage4_post_processor.py:207` | `shutdown(wait=False)` 후 타임아웃 시 orphan 스레드 | Manager LLM > 120초 시 백그라운드 실행 지속 | 타임아웃 후 `_bible_future.cancel()` 추가 + 로그 |
| M-2 | `data_collector.py:95,98,100` | `stats` dict `+=` 연산 Lock 미보호 | 병렬 검증 시 카운터 lost update | `with self._lock:` 래핑 |
| M-3 | `base_agent.py:202` | `_quota_exhausted_models.clear()` 가 `_quota_lock` 없이 수행 | 키 순환 직후 다른 스레드의 쿼터 기록 유실 | `with cls._quota_lock:` 래핑 |

### LOW: 5건

| # | 위치 | 설명 | 영향 |
|---|------|------|------|
| L-1 | `block_enricher.py:651,654` | stats 카운터 Lock 미보호 | 진단용 통계 오차 |
| L-2 | `quality_dashboard.py:1097-1100` | `reset_dashboard()` Lock 미보호 | 프로젝트 전환 시 일시적 이중 인스턴스 |
| L-3 | `metrics_collector.py:110-115` | `reset()` Lock 밖에서 재생성 | 일시적 이중 인스턴스 (DCL로 해소) |
| L-4 | `db_manager.py:1281,1435` | 수동 `acquire()/release()` 패턴 | RLock + finally로 안전하지만 코드 스타일 비일관 |
| L-5 | `stage4_post_processor.py:207` | executor 참조 GC 가능성 | future가 참조를 유지하므로 실질적 문제 없음 |

---

## 8. 전체 평가

### 양호한 패턴 (Best Practices 준수)

1. **일관된 DCL 싱글톤**: 10개 이상의 싱글톤 팩토리가 모두 올바른 Double-Checked Locking을 구현.
2. **DBManager RLock**: `check_same_thread=False` + `RLock` + 모든 메서드의 `with self._lock:` — 표준 패턴.
3. **스레드 사전 로드**: `arc_ensemble.py` L121-129에서 genre를 ThreadPool 진입 전에 로드하여 SQLite thread-safety 문제 방지.
4. **TOCTOU 해결**: base_agent의 `_init_api_keys`, `_context_caches` 접근이 모두 Lock 내 `.get()` 패턴으로 수정됨.
5. **return_exceptions=True**: `asyncio.gather` 호출 3곳 모두에서 적용 (Sweep7-A).
6. **미완료 future cleanup**: `arc_ensemble`, `chief_writer`, `block_enricher`에서 finally 블록의 `cancel()` 호출.
7. **perf_timer 보호**: stage2_preflight에서 함수 로컬 `_perf_lock`으로 병렬 구간 계측 보호.

### 주의 필요 패턴

1. **`shutdown(wait=False)` 사용**: `stage4_post_processor.py`에서 유일하게 사용. fire-and-forget 패턴이지만, 타임아웃 후 orphan 스레드 가능성 존재.
2. **수동 Lock acquire/release**: `commit_episode_factory`에서 `self._lock.acquire()` + `finally: self._lock.release()` 사용. `with self._lock:` 패턴으로 통일 권장 (그러나 내부 메서드의 RLock 재진입이 필요하므로 현재 구조에서는 의도적).
3. **self.cursor (legacy)**: `_boot_db`에서 생성된 공유 커서가 여전히 100회 이상 사용됨. 새 코드에서 로컬 커서로 전환이 INF-P1-1 주석으로 명시되어 있으나, 레거시 코드의 전환은 미완료.

### 결론

글도비 코드베이스의 동시성 안전성은 **양호** 수준이다. 대부분의 공유 상태가 적절한 Lock으로 보호되어 있으며, 과거 감사(sweep6, Opus TF 재감사)에서 발견된 TOCTOU, 무잠금 접근 등의 문제가 체계적으로 수정되었다. 남아있는 MEDIUM 3건은 모두 통계 정확도나 edge case에 해당하며, 데이터 손실이나 크래시를 유발하지 않는다.

---

*End of Concurrency Safety Audit*
