# Debug Sweep 6차 — 스레드 안전성 + 리소스 상한

> **목적**: ThreadPoolExecutor 병렬 실행 환경에서 공유 자원 경쟁 조건 해소 + 무한 성장 캐시 상한 설정
> **규칙**: 각 항목은 독립 실행 가능 (의존성 없음). 수정 후 반드시 `set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q` 통과 확인.
> **테스트 기준선**: 1,728 passed + 68 xfailed
> **Ruff**: 수정한 파일에 `ruff check <파일> && ruff format <파일>` 적용
> **커밋하지 말 것** — 수정만 하고 검증만 수행

### ⚠️ CRITICAL: Encoding Safety Rules

**All source files are UTF-8 encoded with Korean comments and string literals.**

1. **NEVER re-write entire files.** Only modify the specific lines described in each item.
2. When reading files, always use `encoding='utf-8'`.
3. When writing files, always use `encoding='utf-8'` and write back only the changed content.
4. **Do NOT use `open()` without explicit `encoding='utf-8'`** — the default system encoding may corrupt Korean characters.
5. Prefer targeted line-level edits over full-file rewrites. If your tool reads and writes the whole file, ensure the round-trip preserves all non-ASCII characters exactly.
6. After each file modification, verify Korean text is intact by checking the file does not contain garbled sequences (e.g., `?쒖뒪`, `紐⑤뱺`, `留ㅼ쭅`).

---

## A. 공유 캐시 Lock 보호 (CRITICAL 2건 + IMPORTANT 2건)

### A-1: `modules/validation/validation_orchestrator.py` — `_CONSTITUTION_CACHE` Lock

**심각도**: CRITICAL
**현상**: 모듈 레벨 dict `_CONSTITUTION_CACHE`가 `validate_parallel_v59()`의 ThreadPoolExecutor에서 lock 없이 동시 접근.
**위치**: L70 (정의), L794-801 (읽기/쓰기)

**수정 1 — L70 부근에 Lock 추가**:
```python
# 현재:
_CONSTITUTION_CACHE: dict[str, str] = {}

# 수정:
import threading
_CONSTITUTION_CACHE: dict[str, str] = {}
_CONSTITUTION_LOCK = threading.Lock()
```
- `import threading`은 파일 상단 import 영역에 추가.
- `_CONSTITUTION_LOCK` 선언은 `_CONSTITUTION_CACHE` 바로 아래에.

**수정 2 — L791-802 `_load_constitution_cached()` 내부**:
```python
# 현재:
global _CONSTITUTION_CACHE
if genre in _CONSTITUTION_CACHE:
    return _CONSTITUTION_CACHE[genre]
if CONSTITUTION_AVAILABLE:
    try:
        constitution = get_constitution_for_genre(genre)
        _CONSTITUTION_CACHE[genre] = constitution
        return constitution
    except Exception as e:
        logging.warning(f"[WARNING] Constitution 로드 실패 ({genre}): {e}")

# 수정:
global _CONSTITUTION_CACHE
with _CONSTITUTION_LOCK:
    if genre in _CONSTITUTION_CACHE:
        return _CONSTITUTION_CACHE[genre]
if CONSTITUTION_AVAILABLE:
    try:
        constitution = get_constitution_for_genre(genre)
        with _CONSTITUTION_LOCK:
            _CONSTITUTION_CACHE[genre] = constitution
        return constitution
    except Exception as e:
        logging.warning(f"[WARNING] Constitution 로드 실패 ({genre}): {e}")
```

---

### A-2: `modules/core/prompt_loader.py` — `_cache` dict Lock

**심각도**: CRITICAL
**현상**: 싱글톤 클래스 변수 `_cache` dict가 여러 스레드(앙상블 LLM 호출)에서 동시 접근 가능.
**위치**: L30 (정의), L59-60 (읽기), L128 (쓰기)

**수정 1 — L30 부근에 Lock 추가**:
```python
# 현재:
_instance: Optional["PromptLoader"] = None
_cache: dict[str, dict[str, str]] = {}

# 수정:
_instance: Optional["PromptLoader"] = None
_cache: dict[str, dict[str, str]] = {}
_cache_lock: threading.Lock = threading.Lock()
```
- `import threading`을 파일 상단에 추가.

**수정 2 — `_load_yaml_file()` L57-135 내부**:
```python
def _load_yaml_file(self, domain: str) -> dict[str, str]:
    """YAML 파일을 로드하여 딕셔너리로 반환."""
    with self._cache_lock:
        if domain in self._cache:
            return self._cache[domain]

    # ... (기존 YAML 로드 로직 그대로) ...

    # 캐시에 저장하는 모든 지점 (L128, L65, L134):
    with self._cache_lock:
        self._cache[domain] = prompts  # 또는 {}
    return prompts  # 또는 {}
```
- L59-60, L65, L128, L134의 `self._cache[domain] = ...` 접근을 모두 `with self._cache_lock:` 블록으로 감싸기.
- `invalidate_cache()` 메서드(L178-183)도 lock 보호 추가:
```python
def invalidate_cache(self, domain: str | None = None):
    with self._cache_lock:
        if domain:
            self._cache.pop(domain, None)
        else:
            self._cache.clear()
```

---

### A-3: `modules/core/semantic_cache.py` — OrderedDict Lock

**심각도**: IMPORTANT
**현상**: `_cache` (OrderedDict)와 `_signature_index` dict가 `get()`/`set()` 에서 동시 변경 가능.
**위치**: L94-97 (정의), L196-271 (get), L273-326 (set)

**수정 — `__init__`에 Lock 추가 + get/set 감싸기**:
```python
# __init__에 추가 (L93 부근):
import threading
# ...
self._lock = threading.Lock()

# get() 메서드 (L196):
def get(self, request_type, context):
    with self._lock:
        # 기존 get 로직 전체

# set() 메서드 (L273):
def set(self, request_type, context, value, metadata=None):
    with self._lock:
        # 기존 set 로직 전체

# _evict_lru() 메서드:
# 이미 set() 안에서만 호출되므로 별도 lock 불필요 (set의 lock 내부)
```
- `import threading`은 파일 상단에 추가.
- `get()`과 `set()` 메서드 본문 전체를 `with self._lock:` 으로 감싸기.

---

### A-4: `modules/validation/batch_validator.py:83-85` — 최종 stats Lock 범위 확장

**심각도**: IMPORTANT
**현상**: `validate_batch_async()` 마지막에 `total_time`, `average_time` 기록이 `_stats_lock` 없이 실행.
**위치**: L83-85

**현재 코드**:
```python
elapsed = time.time() - start_time
self.stats["total_time"] = elapsed
self.stats["average_time"] = elapsed / len(manuscripts) if manuscripts else 0
```

**수정**:
```python
elapsed = time.time() - start_time
with self._stats_lock:
    self.stats["total_time"] = elapsed
    self.stats["average_time"] = elapsed / len(manuscripts) if manuscripts else 0
```

---

## B. 싱글톤 경쟁 조건 — Double-Checked Locking (6건)

> **패턴**: 두 스레드가 동시에 `if _instance is None` 통과 → 인스턴스 2개 생성.
> **표준 수정**:
> ```python
> _lock = threading.Lock()
>
> def get_xxx():
>     global _instance
>     if _instance is None:          # 1차 체크 (lock 없이 — 빠른 경로)
>         with _lock:
>             if _instance is None:  # 2차 체크 (lock 안에서)
>                 _instance = XxxClass()
>     return _instance
> ```

### B-1: `modules/core/adaptive_retry.py` — 2건

**위치 1: L418-426** — `get_adaptive_retry()`
```python
# 파일 상단에 추가:
import threading

# L418 부근에 추가:
_adaptive_retry_lock = threading.Lock()

# L421-426 수정:
def get_adaptive_retry() -> AdaptiveRetryStrategy:
    global _adaptive_retry_instance
    if _adaptive_retry_instance is None:
        with _adaptive_retry_lock:
            if _adaptive_retry_instance is None:
                _adaptive_retry_instance = AdaptiveRetryStrategy()
    return _adaptive_retry_instance
```

**위치 2: L737-745** — `get_adaptive_manager()`
```python
# L737 부근에 추가:
_adaptive_manager_lock = threading.Lock()

# L740-745 수정:
def get_adaptive_manager() -> AdaptiveRetryManager:
    global _adaptive_manager_instance
    if _adaptive_manager_instance is None:
        with _adaptive_manager_lock:
            if _adaptive_manager_instance is None:
                _adaptive_manager_instance = AdaptiveRetryManager()
    return _adaptive_manager_instance
```

---

### B-2: `modules/core/semantic_item_registry.py` — 1건

**위치: L761-769** — `get_item_registry()`
```python
# L761 부근에 추가:
_registry_lock = threading.Lock()

# L764-769 수정:
def get_item_registry() -> SemanticItemRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = SemanticItemRegistry()
    return _registry_instance
```
- `import threading` 파일 상단에 추가.

---

### B-3: `modules/core/primitive_guard.py` — 2건 (싱글톤 + `__new__`)

**위치 1: L19-25** — `__new__` 경쟁
```python
# L19 위에 추가:
import threading
_primitive_guard_lock = threading.Lock()

# L22-25 수정:
def __new__(cls):
    if cls._instance is None:
        with _primitive_guard_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
    return cls._instance
```

**위치 2: L174-182** — `get_primitive_guard()`
```python
# L174 부근에 추가:
_guard_lock = threading.Lock()

# L177-182 수정:
def get_primitive_guard() -> PrimitiveGuard:
    global _guard_instance
    if _guard_instance is None:
        with _guard_lock:
            if _guard_instance is None:
                _guard_instance = PrimitiveGuard()
    return _guard_instance
```

---

### B-4: `modules/core/pass_rate_monitor.py` — 1건

**위치: L410-421** — `get_monitor()`
```python
# L410 부근에 추가:
_monitor_lock = threading.Lock()

# L415-421 수정:
def get_monitor(project_path: str = None) -> PassRateMonitor:
    global _monitor_instance, _monitor_project_path
    if _monitor_instance is None or (project_path and project_path != _monitor_project_path):
        with _monitor_lock:
            if _monitor_instance is None or (project_path and project_path != _monitor_project_path):
                _monitor_instance = PassRateMonitor(project_path)
                _monitor_project_path = project_path
    return _monitor_instance
```
- `import threading` 파일 상단에 추가.

---

### B-5: `modules/core/quality_dashboard.py` — 1건

**위치: L898-907** — `get_dashboard()`
```python
# L899 부근에 추가:
_dashboard_lock = threading.Lock()

# L902-907 수정:
def get_dashboard(project_path: Path | None = None) -> QualityDashboard:
    global _dashboard_instance
    if _dashboard_instance is None:
        with _dashboard_lock:
            if _dashboard_instance is None:
                _dashboard_instance = QualityDashboard(project_path)
    return _dashboard_instance
```
- `import threading` 파일 상단에 추가.

---

### B-6: `modules/core/prompt_loader.py` — `__new__` 경쟁 (A-2와 동일 파일)

**위치: L32-37** — 싱글톤 `__new__`

> A-2에서 이미 `import threading`과 `_cache_lock` 추가.
> `__new__`에도 lock 적용.

```python
# L29 부근에 추가 (A-2의 _cache_lock과 함께):
_instance_lock = threading.Lock()

# L32-37 수정:
def __new__(cls) -> "PromptLoader":
    if cls._instance is None:
        with _instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._cache = {}
    return cls._instance
```

---

## C. 리소스 상한 — 무한 성장 캐시 제한 (2건)

### C-1: `modules/domain/agents/base_agent.py` — `_context_caches` 상한

**심각도**: CRITICAL
**현상**: 클래스 변수 `_context_caches = {}` (L1002)가 상한 없이 성장. TTL 만료는 동일 키 재접근 시에만 발동 → 다양한 키 사용 시 메모리 누수.

**수정 — L1002 부근에 상수 + 정리 로직 추가**:
```python
# L1002 수정:
_context_caches = {}
_CONTEXT_CACHE_MAX = 50  # 최대 캐시 항목 수
```

**수정 — L1065 이후 (캐시 저장 직후)에 정리 로직 추가**:
```python
self._context_caches[cache_key] = {
    "name": cache.name,
    "created_at": current_time,
    "content_hash": content_hash,
}

# [Sweep6] 캐시 상한 초과 시 가장 오래된 항목 정리
if len(self._context_caches) > self._CONTEXT_CACHE_MAX:
    sorted_keys = sorted(
        self._context_caches,
        key=lambda k: self._context_caches[k].get("created_at", 0),
    )
    for old_key in sorted_keys[: len(sorted_keys) - self._CONTEXT_CACHE_MAX]:
        del self._context_caches[old_key]
```

**테스트**: 1건 추가 — `_context_caches` 50개 초과 시 정리 확인.

---

### C-2: `modules/core/adaptive_retry.py` — `_failures` dict 에피소드 키 상한

**심각도**: IMPORTANT
**현상**: `AdaptiveRetryManager._failures` (L494)가 에피소드별 키를 무한 축적. 200화+ 세션에서 200+ 키 × 100 레코드.

**수정 — L532-534 (기존 레코드 수 제한 바로 아래)에 키 제한 추가**:
```python
# 기존:
if len(self._failures[ep_num]) > self.max_history:
    self._failures[ep_num] = self._failures[ep_num][-self.max_history :]

# 추가:
# [Sweep6] 에피소드 키 수 제한 — 최근 50개만 유지
_MAX_EPISODE_KEYS = 50
if len(self._failures) > _MAX_EPISODE_KEYS:
    oldest_eps = sorted(self._failures.keys())[: len(self._failures) - _MAX_EPISODE_KEYS]
    for old_ep in oldest_eps:
        del self._failures[old_ep]
```

- `_MAX_EPISODE_KEYS = 50`은 클래스 상수로 추출해도 됨 (L489 부근에 `self._max_episode_keys = 50` 등).

**테스트**: 1건 추가 — 50개 초과 에피소드 키 정리 확인.

---

## 실행 가이드 (Codex용)

- **총 14개 항목** — 모두 독립 실행 가능, 병렬 OK
- A-1~A-4: 공유 캐시 Lock 추가 — 4건
- B-1~B-6: 싱글톤 double-checked locking — 6건 (8 파일 내 함수)
- C-1~C-2: 리소스 상한 추가 — 2건
- 신규 테스트: +2건 (C-1, C-2)
- 각 항목 수정 후: `ruff check <파일> && ruff format <파일> && set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q`
- 기대 결과: `1,724+ passed, 68 xfailed` (신규 테스트 포함)
- **커밋하지 말 것** — 수정만 하고 검증만 수행

### 주의사항

- `import threading`은 이미 있는 파일도 있음. 중복 import 확인 후 추가.
- B 카테고리의 `reset_xxx()` 함수들은 lock 불필요 (단일 스레드 호출 전제).
- A-2와 B-6은 동일 파일(`prompt_loader.py`). 두 수정을 함께 적용할 것.

---

## 카테고리별 커밋 메시지 (나중에 사람이 커밋할 때 사용)

```
fix(sweep6-a): add threading.Lock to shared caches — constitution, prompt_loader, semantic_cache, batch_validator
fix(sweep6-b): add double-checked locking to 6 singleton factories
fix(sweep6-c): add max-size limits to context_caches and failure records
```

---

## 산출물 요약

| 카테고리 | 항목 수 | 파일 수 | 신규 테스트 | 성격 |
|----------|---------|---------|------------|------|
| A. 공유 캐시 Lock | 4 | 4 | 0 | 스레드 안전성 |
| B. 싱글톤 DCL | 6 | 5 | 0 | 스레드 안전성 |
| C. 리소스 상한 | 2 | 2 | +2 | 메모리 관리 |
| **합계** | **12** | **9** | **+2** | |

---

## 파일별 변경 요약

| # | 파일 | 카테고리 | 변경 내용 |
|---|------|----------|----------|
| 1 | `modules/validation/validation_orchestrator.py` | A-1 | `_CONSTITUTION_LOCK` + Lock 보호 |
| 2 | `modules/core/prompt_loader.py` | A-2, B-6 | `_cache_lock` + `_instance_lock` + DCL |
| 3 | `modules/core/semantic_cache.py` | A-3 | `self._lock` + get/set 보호 |
| 4 | `modules/validation/batch_validator.py` | A-4 | stats final write Lock 확장 |
| 5 | `modules/core/adaptive_retry.py` | B-1, C-2 | 싱글톤 DCL 2건 + 에피소드 키 상한 |
| 6 | `modules/core/semantic_item_registry.py` | B-2 | 싱글톤 DCL |
| 7 | `modules/core/primitive_guard.py` | B-3 | `__new__` DCL + factory DCL |
| 8 | `modules/core/pass_rate_monitor.py` | B-4 | 싱글톤 DCL |
| 9 | `modules/core/quality_dashboard.py` | B-5 | 싱글톤 DCL |
| 10 | `modules/domain/agents/base_agent.py` | C-1 | `_CONTEXT_CACHE_MAX=50` + 정리 로직 |
