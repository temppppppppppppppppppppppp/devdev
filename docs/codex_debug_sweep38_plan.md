# Debug Sweep 38 — 스레드 안전성 + 리소스 누수

## Context

Sweep 37 완료 (2,087 passed, 68 xfailed). 5개 에이전트로 리소스 누수, SQL 안전성, 레이스 컨디션, None 전파, 문자열 안전성 전면 탐색. 코드 수동 검증 후 **확인된 실제 버그 6건**으로 정리.

---

## A-1 (HIGH): `SemanticCache.invalidate()` — Lock 미적용 레이스 컨디션

**파일**: `modules/core/semantic_cache.py:349-363`

**문제**: `get()`(L210)과 `set()`(L289)은 `with self._lock:`으로 보호되지만, `invalidate()`는 Lock 없이 `self._cache`를 순회+삭제:

```python
def invalidate(self, pattern: str = None):
    if pattern is None:
        self._cache.clear()          # ← Lock 없이 dict.clear()
        self._signature_index.clear()
    else:
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]  # ← Lock 없이 순회
        for key in keys_to_remove:
            self._evict(key)          # ← Lock 없이 pop()
```

- 다른 스레드가 `get()`으로 `self._cache` 접근 중 `invalidate()` 호출 시 RuntimeError 또는 KeyError 크래시
- `get_stats()` (L365)도 Lock 없음

**수정**:
```python
def invalidate(self, pattern: str = None):
    """캐시 무효화"""
    with self._lock:
        if pattern is None:
            self._cache.clear()
            self._signature_index.clear()
        else:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._evict(key)

def get_stats(self) -> dict[str, Any]:
    """통계 반환"""
    with self._lock:
        return {
            "total_requests": self.stats.total_requests,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "fuzzy_hits": self.stats.fuzzy_hits,
            "evictions": self.stats.evictions,
            "current_size": len(self._cache),
            "max_size": self.max_size,
        }
```

---

## A-2 (MEDIUM): `VecMemory` — 커서 리소스 누수 (3개 메서드)

**파일**: `modules/core/vec_memory.py`

**문제**: `_ensure_tables()` (L108), `memorize_v20_episode()` (L210), `delete_episodes_from()` (L454)에서 `cur = self._conn.cursor()` 생성 후 `cur.close()` 호출 없음:

```python
# L108 (_ensure_tables)
cur = self._conn.cursor()
cur.execute(...)  # 4개 CREATE TABLE
self._conn.commit()
# cur.close() 없음 — 커서 리소스 누수

# L210 (memorize_v20_episode)
cur = self._conn.cursor()
cur.execute(...)  # DELETE + INSERT + INSERT OR REPLACE × 2
self._conn.commit()
return True
# cur.close() 없음 — 에피소드마다 커서 누적

# L454 (delete_episodes_from)
cur = self._conn.cursor()
# ... DELETE 3건
self._conn.commit()
return count
# cur.close() 없음
```

- 에피소드 100+화 생성 시 커서 핸들이 누적되어 메모리 증가
- 예외 발생 시 커서가 절대 닫히지 않음

**수정**: 3개 메서드 모두 try/finally 패턴 적용:

### `_ensure_tables()` (L106-147):
```python
def _ensure_tables(self) -> None:
    """벡터 테이블 + 메타데이터 테이블 + 앵커 테이블 생성"""
    cur = self._conn.cursor()
    try:
        cur.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodes
            USING vec0(embedding float[{EMBED_DIM}])
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS episode_meta (
                ep_num      INTEGER PRIMARY KEY,
                summary     TEXT,
                causal_data TEXT,
                arc_no      INTEGER,
                event_types TEXT,
                entity_names TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                ep_num    INTEGER PRIMARY KEY,
                synced    INTEGER DEFAULT 0,
                synced_at TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                key        TEXT PRIMARY KEY,
                value      TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()
    finally:
        cur.close()
```

### `memorize_v20_episode()` (L209-241):
기존 try/except 구조를 try/except/finally로 변경:
```python
try:
    cur = self._conn.cursor()
    try:
        cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep_num,))
        cur.execute(
            "INSERT INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
            (ep_num, _serialize_f32(emb)),
        )
        causal_str = json.dumps(causal_links, ensure_ascii=False)[:500] if causal_links else ""
        evt_str = ",".join(str(e) for e in event_types)[:200] if event_types else ""
        ent_str = ",".join(str(n) for n in entity_names)[:300] if entity_names else ""
        cur.execute(
            """INSERT OR REPLACE INTO episode_meta
               (ep_num, summary, causal_data, arc_no, event_types, entity_names)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ep_num, summary[:500], causal_str, arc_no, evt_str, ent_str),
        )
        cur.execute(
            "INSERT OR REPLACE INTO sync_status (ep_num, synced, synced_at) VALUES (?, 1, CURRENT_TIMESTAMP)",
            (ep_num,),
        )
        self._conn.commit()
        return True
    finally:
        cur.close()
except Exception as e:
    self._ui_log(f"[VecMemory] 제 {ep_num}화 저장 실패: {e}")
    return False
```

### `delete_episodes_from()` (L453-466):
```python
try:
    cur = self._conn.cursor()
    try:
        rows = cur.execute("SELECT ep_num FROM episode_meta WHERE ep_num >= ?", (target_ep,)).fetchall()
        count = len(rows)
        for (ep,) in rows:
            cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
        cur.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
        cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
        self._conn.commit()
        return count
    finally:
        cur.close()
except Exception as e:
    self._ui_log(f"[VecMemory] 에피소드 삭제 실패 (>={target_ep}): {e}")
    return 0
```

---

## A-3 (MEDIUM): `AdaptiveRetryStrategy` — TOCTOU 레이스 컨디션

**파일**: `modules/core/adaptive_retry.py:98-110`

**문제**: 싱글턴 인스턴스의 `self.contexts` dict에 Lock 없는 check-then-act:

```python
def __init__(self) -> None:
    self.contexts: dict[str, RetryContext] = {}  # Lock 없음

def get_context(self, task_id: str) -> RetryContext:
    if task_id not in self.contexts:    # CHECK
        self.contexts[task_id] = RetryContext()  # ACT — 두 스레드 동시 진입 시 덮어쓰기
    return self.contexts[task_id]

def reset_context(self, task_id: str):
    if task_id in self.contexts:    # CHECK
        del self.contexts[task_id]  # ACT — 두 스레드 동시 진입 시 KeyError
```

- 싱글턴(`get_adaptive_retry()`)이므로 모든 Stage에서 공유
- 동시 접근 시 RetryContext 상태 소실 또는 KeyError 크래시

**수정**:
```python
def __init__(self) -> None:
    self.contexts: dict[str, RetryContext] = {}
    self._lock = threading.Lock()

def get_context(self, task_id: str) -> RetryContext:
    """태스크별 컨텍스트 가져오기"""
    with self._lock:
        if task_id not in self.contexts:
            self.contexts[task_id] = RetryContext()
        return self.contexts[task_id]

def reset_context(self, task_id: str):
    """컨텍스트 초기화"""
    with self._lock:
        self.contexts.pop(task_id, None)
```

`import threading`이 파일 상단에 이미 있는지 확인 후 없으면 추가.

---

## A-4 (MEDIUM): `AdaptiveRetryManager` — 공유 dict/list Lock 누락

**파일**: `modules/core/adaptive_retry.py:502-560`

**문제**: 싱글턴(`get_adaptive_manager()`)의 `_failures`와 `_agent_stats`에 Lock 없음:

```python
def __init__(self, max_history: int = 100, failure_learner=None):
    self._failures: dict[int, list[FailureRecord]] = defaultdict(list)
    self._agent_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    # Lock 없음

def record_failure(self, ep_num, agent, error_info, attempt=1) -> ErrorType:
    self._failures[ep_num].append(record)           # L549 — Lock 없이 list.append
    self._agent_stats[agent][error_type.value] += 1  # L550 — Lock 없이 read-modify-write

    if len(self._failures[ep_num]) > self.max_history:
        self._failures[ep_num] = self._failures[ep_num][-self.max_history:]  # L554

    if len(self._failures) > self._max_episode_keys:
        oldest_eps = sorted(self._failures.keys())[...]
        for old_ep in oldest_eps:
            del self._failures[old_ep]  # L560 — Lock 없이 dict 삭제
```

- `get_retry_guidance()` (L573)와 기타 읽기 메서드도 Lock 없이 `_failures` 순회

**수정**: `__init__`에 Lock 추가, `record_failure`와 읽기 메서드에 적용:

```python
def __init__(self, max_history: int = 100, failure_learner=None):
    self.max_history = max_history
    self._max_episode_keys = 50
    self.strategy = get_adaptive_retry()
    self.failure_learner = failure_learner
    self._failures: dict[int, list[FailureRecord]] = defaultdict(list)
    self._agent_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    self._lock = threading.Lock()
```

`record_failure()` 전체를 `with self._lock:` 래핑:
```python
def record_failure(self, ep_num: int, agent: str, error_info: dict, attempt: int = 1) -> ErrorType:
    # ... error_type 분류 로직 (Lock 불필요) ...
    record = FailureRecord(...)

    with self._lock:
        self._failures[ep_num].append(record)
        self._agent_stats[agent][error_type.value] += 1

        if len(self._failures[ep_num]) > self.max_history:
            self._failures[ep_num] = self._failures[ep_num][-self.max_history:]

        if len(self._failures) > self._max_episode_keys:
            oldest_eps = sorted(self._failures.keys())[: len(self._failures) - self._max_episode_keys]
            for old_ep in oldest_eps:
                del self._failures[old_ep]

    # FailureLearner 연동은 Lock 밖에서 (별도 모듈이므로)
    if self.failure_learner:
        try:
            stage = self.AGENT_STAGE_MAP.get(agent.lower(), 4)
            reason = error_info.get("reason", error_info.get("message", "unknown"))
            self.failure_learner.record_failure(stage=stage, episode=ep_num, reason=str(reason), details=error_info)
        except Exception:
            pass
    return error_type
```

`get_retry_guidance()` (L573)와 기타 읽기 메서드에서 `_failures` 접근 시에도 `with self._lock:` 래핑.

---

## B-1 (LOW): `PassRateMonitor` — records Lock 누락

**파일**: `modules/core/pass_rate_monitor.py:76, 163, 181`

**문제**: 싱글턴 인스턴스의 `self.records` 리스트에 Lock 없음:

```python
def __init__(self, project_path=None):
    self.records: list[AttemptRecord] = []  # Lock 없음

def record_attempt(self, ...):
    self.records.append(record)  # L163 — 병렬 호출 시 list 오염 가능

def get_stage_stats(self, stage, recent_n=None):
    stage_records = [r for r in self.records if r.stage == stage]  # L181 — 순회 중 수정 시 크래시
```

**수정**: `__init__`에 `self._lock = threading.Lock()` 추가, `record_attempt`과 `get_stage_stats`에 `with self._lock:` 래핑:

```python
def __init__(self, project_path=None):
    self.project_path = Path(project_path) if project_path else Path(".")
    self.log_path = self.project_path / "logs" / "pass_rate_monitor.json"
    self.records: list[AttemptRecord] = []
    self.session_start = datetime.now().isoformat()
    self._lock = threading.Lock()
    self._load_records()

def record_attempt(self, ...):
    record = AttemptRecord(...)
    with self._lock:
        self.records.append(record)
        if len(self.records) % 100 == 0:
            self._save_records()

def get_stage_stats(self, stage: int, recent_n: int = None) -> StageStats:
    with self._lock:
        stage_records = [r for r in self.records if r.stage == stage]
    # 이후 계산은 Lock 밖에서 (stage_records는 로컬 복사본)
    if recent_n:
        stage_records = stage_records[-recent_n:]
    # ... 나머지 동일
```

`_save_records()`와 `get_arc_difficulty()` (L440+) 등 `self.records` 읽는 다른 메서드에도 동일하게 적용.

---

## B-2 (LOW): `pre_llm_validator` — re.DOTALL 누락

**파일**: `modules/validation/pre_llm_validator.py:277`

**문제**: 부상→무리한 행동 패턴이 줄바꿈을 넘지 못함:

```python
injury_action = re.findall(
    r"(중상|부상|피를 흘리).{0,50}(뛰어올|전력으로 달|힘껏 휘둘)", manuscript
)
```

- `.{0,50}`이 `\n`을 매칭하지 않으므로, 부상 서술과 행동 서술 사이에 줄바꿈이 있으면 미탐지
- 예: `"피를 흘리며 쓰러졌다.\n그러나 힘껏 휘둘렀다."` → 미탐지

**수정**:
```python
injury_action = re.findall(
    r"(중상|부상|피를 흘리).{0,50}(뛰어올|전력으로 달|힘껏 휘둘)", manuscript, re.DOTALL
)
```

동일 파일 L272도 확인:
```python
triple_action = re.findall(
    r"(왼손|오른손|양손).{0,20}(왼손|오른손|양손).{0,20}(왼손|오른손|양손)", manuscript, re.DOTALL
)
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/core/semantic_cache.py` | `invalidate()` + `get_stats()` Lock 래핑 |
| A-2 | `modules/core/vec_memory.py` | 3개 메서드 try/finally + cur.close() |
| A-3 | `modules/core/adaptive_retry.py` | `AdaptiveRetryStrategy.__init__` Lock 추가, `get_context`/`reset_context` Lock 래핑 |
| A-4 | `modules/core/adaptive_retry.py` | `AdaptiveRetryManager.__init__` Lock 추가, `record_failure` + 읽기 메서드 Lock 래핑 |
| B-1 | `modules/core/pass_rate_monitor.py` | `__init__` Lock 추가, `record_attempt`/`get_stage_stats`/`_save_records`/`get_arc_difficulty` Lock 래핑 |
| B-2 | `modules/validation/pre_llm_validator.py` | L272, L277에 `re.DOTALL` 추가 |

**총 5파일**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| main_a.py:1953 ThreadPoolExecutor 미종료 | ✗ 오탐 | L1961에 `executor.shutdown(wait=False)` 있음. 세션 종료 시점이라 `wait=False` 정당 |
| master_bible chained .get() 7+곳 | ✗ 오탐 | 모든 곳이 try/except로 보호됨 — graceful degradation 설계 |
| Python string slicing 한글 깨짐 | ✗ 오탐 | Python 3 str은 Unicode code point 시퀀스. `"한글"[:1]` = `"한"`. 바이트 분할 아님 |
| json.dumps()[:N] JSON 구조 깨짐 | ✗ 오탐 | 로깅/프롬프트용 스니펫. LLM이 파싱하지 않음 |
| SQL injection (table name f-string) | ✗ 오탐 | 모든 테이블명이 하드코딩된 상수. project_service.py는 frozenset 화이트리스트 검증 |
| VecMemory arc_no=None 전달 | ✗ 오탐 | `memorize_v20_episode(arc_no: int | None = None)` 타입 힌트 일치. SQLite NULL 저장 정상 |
| str(exception)[:N] 한글 깨짐 | ✗ 오탐 | Python 3 str slicing — 위와 동일한 이유 |

---

## 검증

```bash
# 전체 테스트
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -p no:capture

# 스레드 안전성 관련 기존 테스트
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -k "retry or monitor or cache" -p no:capture
```

---

## Execution Update (2026-02-18)

Status: completed for Sweep 38 scope.

Applied items:
- A-1 `modules/core/semantic_cache.py`: added lock guards to `invalidate()` and `get_stats()` to protect shared cache/index/state access.
- A-2 `modules/core/vec_memory.py`: cursor lifecycle hardened in `_ensure_tables()`, `memorize_v20_episode()`, and `delete_episodes_from()` using `finally` cleanup (`cur.close()`).
- A-3 `modules/core/adaptive_retry.py`: `AdaptiveRetryStrategy` now has per-instance lock and wraps `get_context()` / `reset_context()` map access.
- A-4 `modules/core/adaptive_retry.py`: `AdaptiveRetryManager` now has lock-protected shared state updates/reads (`record_failure`, `get_retry_guidance`, `should_trigger_ultimate`, `get_agent_weakness`, `get_summary`).
- B-1 `modules/core/pass_rate_monitor.py`: added monitor lock and guarded shared record access in `_save_records`, `record_attempt`, `get_stage_stats`, `get_patch_effectiveness`, `get_trend`, `get_arc_difficulty`, and `export_csv`.
- B-2 `modules/validation/pre_llm_validator.py`: added `re.DOTALL` to body-physics regex checks (`triple_action`, `injury_action`) to detect newline-spanning patterns.

Added tests:
- `tests/test_sweep38.py` (6 tests) covering lock guards/cursor cleanup and `re.DOTALL` source checks.

Verification run:
- `python -m py_compile modules/core/semantic_cache.py modules/core/vec_memory.py modules/core/adaptive_retry.py modules/core/pass_rate_monitor.py modules/validation/pre_llm_validator.py tests/test_sweep38.py` -> pass
- `python -m pytest tests/test_sweep38.py -q -x -p no:capture` -> `6 passed`
- `python -m pytest tests/ -q -k "retry or monitor or cache" -x -p no:capture` -> `81 passed, 2069 deselected, 1 warning`
- `python -m pytest tests/ -q -x -p no:capture` -> `2093 passed, 68 xfailed, 1 warning`

Notes:
- Full-suite output still includes the existing mocked ImportError traceback print from test flow, but pytest exit code is 0 and suite result is green.
