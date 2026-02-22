# 인프라/공통 모듈 전수 감사 리포트 (2026-02-22)

> 감사 범위: DB 매니저, 벡터 메모리, 프롬프트 로더, 설정 관리, 시스템 초기화, base_agent, 메트릭 수집, 컨텍스트 어드바이저, 상태 추적, 세계 상태, 팩트 원장, 프로젝트 매니저 등 인프라 전반
>
> 감사 기준: 버그(P0~P2), 연결성 이슈, 개선 아이디어

---

## 요약

| 등급 | 건수 | 설명 |
|------|------|------|
| P0 (차단급) | 2건 | 운영 중 데이터 손실 또는 크래시 가능성 |
| P1 (품질 이슈) | 9건 | 엣지케이스 장애, 자원 누수, 스레드 안전 |
| P2 (스타일/경미) | 7건 | 코드 위생, 방어 로직 부재, 로깅 |
| 개선 아이디어 | 8건 | 성능, 관측성, 유지보수성 향상 제안 |

---

## P0 -- 차단급 버그

### P0-1. DBManager `commit_episode_factory` 수동 Lock acquire/release -- 예외 시 교착 위험

**파일**: `modules/core/db_manager.py` L1118~1272

```python
self._lock.acquire()
try:
    ...
finally:
    self._lock.release()
```

`commit_episode_factory`는 RLock을 `self._lock.acquire()`로 직접 잡고, `finally`에서 `self._lock.release()`를 호출한다. 문제는 내부에서 호출하는 `self.save_manuscript()`, `self.update_martial_tracker()`, `self.save_state_log_with_summary()` 등이 **각각 `with self._lock:`를 재진입**한다는 점이다. RLock이므로 현재는 동작하지만, 만약 내부 메서드에서 예외가 발생하면서 RLock의 재진입 카운트가 꼬이면 데드락이 발생할 수 있다.

더 큰 문제는 `begin()`, `commit()`, `rollback()` 메서드는 Lock을 잡지 않는데, `commit_episode_factory` 내부에서 이들을 Lock 안에서 호출한다는 것이다. 다른 스레드가 `begin()` 또는 `commit()`을 동시에 호출하면 트랜잭션 상태가 충돌할 수 있다.

**영향**: 멀티스레드 환경에서 에피소드 저장 실패 시 DB Lock 교착 가능성.

**권고**: `with self._lock:` 컨텍스트 매니저로 교체하고, `begin()/commit()/rollback()`에도 Lock 보호를 추가할 것.

---

### P0-2. PromptLoader 싱글톤의 `_cache`가 클래스 변수로 선언되어 인스턴스 간 공유

**파일**: `modules/core/prompt_loader.py` L31~32

```python
class PromptLoader:
    _instance: Optional["PromptLoader"] = None
    _cache: dict[str, dict[str, str]] = {}
```

`_cache`가 클래스 변수(mutable dict)로 선언되어 있다. 싱글톤이므로 의도적일 수 있으나, `__new__`에서 `cls._cache = {}`로 초기화하면서 **`__init__`이 호출될 때마다 `_find_prompts_dir()`가 재실행**된다. 프로젝트 경로가 바뀌는 상황(프로젝트 변경)에서 캐시는 초기화되지 않고, 이전 프로젝트의 프롬프트가 새 프로젝트에서 그대로 사용될 수 있다.

또한 `_cache`가 클래스 변수이므로, 만약 싱글톤이 `reset`되지 않은 채 다른 경로에서 재사용되면 stale 캐시 문제가 발생한다.

**영향**: 프로젝트 변경 시 이전 프로젝트의 프롬프트 템플릿이 새 프로젝트에서 사용될 수 있음.

**권고**: `_cache`를 인스턴스 변수로 이동하거나, 프로젝트 변경 시 `invalidate_cache()`를 호출하는 훅을 추가할 것. `__init__`에서 `_prompts_dir` 변경 감지 후 캐시 무효화 로직 추가 권장.

---

## P1 -- 품질 이슈

### P1-1. DBManager의 `self.cursor`가 인스턴스 전체에서 공유됨 -- 스레드 안전하지 않음

**파일**: `modules/core/db_manager.py` L54, L74

```python
self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
self.cursor = self.conn.cursor()
```

`check_same_thread=False`로 멀티스레드 접근을 허용하고 RLock으로 보호하고 있으나, **단일 `self.cursor`를 모든 메서드에서 공유**한다. SQLite cursor는 상태를 가지고 있어서 (fetchall 전에 다른 execute가 끼어들면 결과가 오염됨), RLock으로 보호되더라도 `commit_episode_factory`처럼 Lock을 수동으로 관리하는 코드에서는 cursor 상태가 꼬일 수 있다.

**영향**: 장기적 안정성 위험. 현재는 RLock이 대부분의 경우를 보호하지만, Lock 누락 시 데이터 오염.

**권고**: 각 메서드에서 `self.conn.cursor()`로 로컬 커서를 생성하고, 메서드 종료 시 `cursor.close()`를 호출하는 패턴으로 전환할 것. VecMemory는 이미 이 패턴을 따르고 있어 좋은 참고 사례임.

---

### P1-2. DBManager `begin()/commit()/rollback()`에 Lock 보호 없음

**파일**: `modules/core/db_manager.py` L505~512

```python
def begin(self):
    self.cursor.execute("BEGIN TRANSACTION")

def commit(self):
    self.conn.commit()

def rollback(self):
    self.conn.rollback()
```

이 세 메서드는 `self._lock` 없이 직접 DB를 조작한다. 다른 스레드가 동시에 `execute_query()`나 `save_manuscript()` (Lock 보호됨)를 호출하면, 트랜잭션 상태가 불일치할 수 있다.

**영향**: 멀티스레드 환경에서 트랜잭션 상태 불일치 가능.

**권고**: `begin()/commit()/rollback()` 모두 `with self._lock:` 내에서 실행하도록 변경.

---

### P1-3. BaseAgent `_rotation_count` 리셋 조건이 Lock 밖에서 실행

**파일**: `modules/domain/agents/base_agent.py` L359~360

```python
if current_model == self.primary_model:
    BaseAgent._rotation_count = 0
```

이 코드는 `ask()` 메서드의 while 루프 안, API 호출 성공 직후에 있으며, **어떤 Lock도 보호하지 않는다**. `_rotation_count`는 클래스 변수로 모든 에이전트 인스턴스에서 공유되므로, 멀티스레드에서 race condition이 발생할 수 있다.

**영향**: 키 순환 카운터가 잘못 리셋되어 불필요한 키 순환 또는 순환 중단 발생 가능.

**권고**: `_rotation_count` 리셋을 `_rotation_lock` 내부에서 수행할 것.

---

### P1-4. MetricsCollector `_metrics` dict가 무한 성장 가능

**파일**: `modules/core/metrics_collector.py` L142

```python
self._metrics: dict[str, AgentMetric] = {}
```

`start_call()`이 호출될 때마다 `_metrics`에 항목이 추가되지만, `end_call()` 이후에도 삭제되지 않는다. 장기 세션(200화 이상)에서 수천 개의 `AgentMetric` 객체가 메모리에 남아있게 된다.

마찬가지로 `_agent_durations`도 `defaultdict(list)`로, 모든 응답 시간을 영구 보존한다.

**영향**: 장기 세션에서 메모리 사용량 점진적 증가 (GC 대상이지만, dict가 참조를 유지).

**권고**: `end_call()` 이후 `_metrics`에서 해당 항목을 삭제하거나, `_agent_durations`에 sliding window (최근 N개만 보존)를 적용할 것.

---

### P1-5. VecMemory `retrieve_multi_query_context`에서 `_load_episode_meta`가 Lock 중첩 호출

**파일**: `modules/core/vec_memory.py` L406~420

```python
with self._db_lock():
    rows = self._conn.execute(...).fetchall()
for rowid, dist in rows:
    ...
    meta = self._load_episode_meta(rowid)  # _load_episode_meta 내부에서도 _db_lock() 사용
```

`_load_episode_meta`(L708~726)는 내부에서 `with self._db_lock():`을 다시 호출한다. shared 모드에서 `self._lock`이 DBManager의 RLock이므로 재진입이 가능하지만, standalone 모드에서 `self._lock`이 None이면 `_db_lock()`이 no-op이어서 문제없다.

그러나 만약 누군가 Lock을 일반 `threading.Lock()`으로 변경하면 즉시 데드락이 발생한다. 이는 계약이 문서화되지 않은 암묵적 가정이다.

**영향**: 현재는 안전하지만, Lock 타입 변경 시 즉시 데드락.

**권고**: `_load_episode_meta`에 `_locked=False` 파라미터를 추가하여 이미 Lock을 잡고 있을 때 중복 Lock을 방지하거나, 코드 주석으로 RLock 필수 조건을 문서화할 것.

---

### P1-6. ConfigManager `load_settings()` 스레드 안전하지 않음

**파일**: `modules/core/config_manager.py` L80~106

```python
def load_settings(self, *, force_reload: bool = False) -> dict:
    if self._validation_settings is not None and not force_reload:
        return self._validation_settings
    ...
    self._validation_settings = data if isinstance(data, dict) else {}
```

`_validation_settings`의 읽기/쓰기가 Lock 없이 수행된다. 멀티스레드에서 동시에 `load_settings(force_reload=True)`를 호출하면, 한 스레드가 YAML을 읽는 도중 다른 스레드가 `_validation_settings`를 `None`으로 설정할 수 있다.

**영향**: 멀티스레드에서 validation 설정이 일시적으로 `None`이 되어 `_get_nested()`에서 AttributeError 발생 가능.

**권고**: `threading.Lock`을 추가하거나, lazy load 패턴을 atomic하게 변경할 것.

---

### P1-7. DBManager `close()` 후 `self.cursor = None`으로 설정하지만 다른 메서드가 이를 체크하지 않음

**파일**: `modules/core/db_manager.py` L514~523

```python
def close(self) -> None:
    if self.conn:
        try:
            if self.conn.in_transaction:
                self.conn.commit()
            self.conn.close()
        finally:
            self.conn = None
            self.cursor = None
```

`close()` 호출 후 `self.conn`과 `self.cursor`가 `None`이 되지만, `save_manuscript()`, `execute_query()` 등 모든 DB 메서드는 `self.cursor`가 유효하다고 가정한다. `close()` 후 이들을 호출하면 `AttributeError: 'NoneType' object has no attribute 'execute'` 크래시가 발생한다.

**영향**: 정상적인 종료 시퀀스에서는 문제없으나, 프로젝트 전환 시 이전 DB 핸들에 접근하면 크래시.

**권고**: 각 공개 메서드 시작 시 `if not self.conn:` 체크를 추가하거나, `close()` 후 접근 시 의미 있는 에러 메시지를 발생시킬 것.

---

### P1-8. BaseAgent 컨텍스트 캐시 `_context_caches`가 클래스 변수 dict -- 스레드 안전하지 않음

**파일**: `modules/domain/agents/base_agent.py` L1045

```python
_context_caches = {}  # {cache_key: {"name": str, "created_at": float, "content_hash": str}}
```

`_context_caches`는 클래스 변수(dict)로 모든 에이전트 인스턴스에서 공유된다. `_get_or_create_context_cache()`와 `_try_rotate_key()`에서 이 dict를 읽기/쓰기하지만, 전용 Lock이 없다. `_try_rotate_key()`의 `cls._context_caches.clear()`(L200)는 `_rotation_lock` 안에서 실행되지만, `_get_or_create_context_cache`는 어떤 Lock도 잡지 않는다.

**영향**: 멀티스레드에서 캐시 읽기/쓰기 경합 가능. Python GIL이 dict 단일 연산을 보호하지만, 복합 연산(읽기 후 쓰기)에서 race condition 가능.

**권고**: `_context_caches` 전용 Lock을 추가하거나, `_rotation_lock`의 보호 범위를 확장할 것.

---

### P1-9. WorldStateManager/FactLedger `rollback_to()` -- 200화 이상에서 성능 저하

**파일**: `modules/core/world_state.py` L433~451, `modules/core/fact_ledger.py` L558~577

```python
def rollback_to(self, target_ep: int) -> None:
    self._state = json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))
    for ep in range(1, target_ep):
        bible = self.db.get_episode_bible(ep)
        if bible:
            sc = bible.get("state_changes", {})
            if sc:
                self.update_from_state_changes(ep, sc)
```

롤백 시 1화부터 `target_ep-1`까지 모든 에피소드를 순회하며 state_changes를 리플레이한다. 200화 기준으로 `get_episode_bible()`을 200번 호출하면서 각각 JSON 파싱을 수행한다. FactLedger는 `update_from_state_changes` + `update_from_bible_delta`를 이중으로 호출하므로 더 느리다.

**영향**: 200화 이상에서 롤백 시 수십 초 소요 가능.

**권고**: 주기적(10화 또는 아크 단위) 스냅샷을 DB에 저장하여 롤백 시 가장 가까운 스냅샷에서 시작하도록 최적화할 것.

---

## P2 -- 스타일/경미

### P2-1. DBManager `execute_query()`/`execute_update()` -- SQL 인젝션 가능성 표면

**파일**: `modules/core/db_manager.py` L531~540

```python
def execute_query(self, sql: str, params: tuple = ()) -> list:
    with self._lock:
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
```

파라미터 바인딩(`params`)을 사용하므로 직접적인 SQL 인젝션은 방지되지만, `sql` 문자열 자체는 임의의 SQL을 받을 수 있어 공격 표면이 존재한다. 외부 입력이 `sql` 파라미터에 직접 전달되는 경로가 있으면 위험하다.

**영향**: 현재 호출자가 하드코딩된 SQL을 사용하므로 실제 위험은 낮음.

**권고**: 이 메서드를 `_execute_query`로 내부 전용으로 변경하거나, 허용된 SQL 패턴을 화이트리스트로 제한할 것.

---

### P2-2. `update_martial_tracker()`에서 동적 SQL 컬럼 이름 사용

**파일**: `modules/core/db_manager.py` L573~589

```python
columns = ", ".join(sanitized_data.keys())
placeholders = ", ".join(["?"] * len(sanitized_data))
query = f"INSERT OR REPLACE INTO martial_tracker (ep_num, {columns}) VALUES (?, {placeholders})"
```

`sanitized_data`의 키가 `MARTIAL_METRICS` 상수에서 필터링되므로 SQL 인젝션 위험은 낮지만, f-string으로 SQL을 구성하는 패턴은 코드 리뷰 시 주의가 필요하다. `_boot_db()`에서 이미 `safe_column_pattern`으로 검증하고 있으나, `update_martial_tracker()`에서는 재검증하지 않는다.

**영향**: 현재 안전하지만, `MARTIAL_METRICS` 상수에 잘못된 값이 추가되면 SQL 오류 또는 인젝션 가능.

**권고**: `update_martial_tracker()`에서도 컬럼명 정규식 검증을 추가하거나, 컬럼명을 parameterized query가 불가능하므로 화이트리스트 교차검증을 수행할 것.

---

### P2-3. PromptLoader YAML 파서 -- 표준 YAML 미지원

**파일**: `modules/core/prompt_loader.py` L76~144

PromptLoader는 PyYAML 의존성을 회피하기 위해 정규식 기반 커스텀 YAML 파서를 사용한다. 이 파서는 `KEY_NAME: |` 형식의 멀티라인 블록만 지원하며, YAML 앵커(`&`/`*`), flow 스타일(`{key: value}`), 인용 문자열 등을 처리하지 못한다.

**영향**: 프롬프트 YAML 파일이 표준 YAML 문법을 사용하면 파싱 실패. 현재는 커스텀 형식만 사용하므로 문제없음.

**권고**: PyYAML은 이미 프로젝트 의존성에 포함되어 있으므로 (`config_manager.py`와 `base_agent.py`에서 `import yaml` 사용), 커스텀 파서 대신 `yaml.safe_load()`를 사용하는 것을 고려할 것. 단, 현재 커스텀 형식이 43개 파일에서 일관되게 사용 중이므로 마이그레이션 비용을 평가해야 함.

---

### P2-4. MetricsCollector 싱글톤 `reset()` -- 전역 변수 `_collector`와 이중 관리

**파일**: `modules/core/metrics_collector.py` L110~117, L466~475

```python
@classmethod
def reset(cls, metrics_dir: Path | None = None):
    global _collector
    with cls._lock:
        cls._instance = None
        _collector = None

_collector: MetricsCollector | None = None

def get_metrics_collector(metrics_dir: Path | None = None) -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector(metrics_dir)
    return _collector
```

`MetricsCollector._instance`와 모듈 레벨 `_collector`가 동일 인스턴스를 이중으로 추적한다. `get_metrics_collector()`는 `_collector`만 체크하고, `MetricsCollector()`의 `__new__`는 `_instance`만 체크한다. `reset()` 이후 `get_metrics_collector()`가 먼저 호출되면 `MetricsCollector()`를 통해 `_instance`도 설정되므로 결과적으로 동기화되지만, 코드가 불필요하게 복잡하다.

**영향**: 현재 동작에는 문제없으나, 향후 유지보수 시 혼란 유발.

**권고**: `get_metrics_collector()`가 `MetricsCollector()`를 호출하므로 `_collector` 전역 변수를 제거하고 `MetricsCollector._instance`만 사용하도록 단순화할 것.

---

### P2-5. BaseAgent `_check_connectivity()` -- 연결 체크에 `models.list()` 사용

**파일**: `modules/domain/agents/base_agent.py` L742~762

```python
def _check_connectivity(self, timeout: int = 15) -> bool:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(self.client.models.list)
        future.result(timeout=timeout)
```

네트워크 연결 체크를 위해 `models.list()` API를 호출하는데, 이 호출 자체가 API 할당량을 소모하며, 응답이 클 수 있다. 특히 야간 무인 운영에서 22회까지 네트워크 재시도가 가능하므로(MAX_NETWORK_RETRIES=22), 최악의 경우 22번의 `models.list()` 호출이 발생한다.

**영향**: 네트워크 불안정 시 불필요한 API 할당량 소모.

**권고**: DNS 해석 또는 HTTPS HEAD 요청 등 더 가벼운 연결 체크 방법을 사용할 것.

---

### P2-6. StudioSystem `boot_v20_project()` -- 무협 전용 서비스 하드코딩

**파일**: `modules/core/system.py` L30~46

```python
def boot_v20_project(self, project_name: str) -> None:
    self.lore = LoreManager(self.project)
    self.martial = MartialManager(self.project)
    self.world = JianghuLogic(self.project)
    self.techniques = TechniqueWeaver()
    self.karma = KarmaService(self.project)
```

`MartialManager`, `JianghuLogic`, `TechniqueWeaver`는 무협 전용 서비스인데, 모든 장르(투자, 스포츠, 의학 등)에서 무조건 초기화된다. 이들이 비무협 장르에서 사용되지 않더라도 메모리를 점유하고, 불필요한 DB 테이블 마이그레이션을 유발할 수 있다.

**영향**: 비무협 장르에서 약간의 메모리 낭비와 초기화 시간 증가. 기능적 문제는 없음.

**권고**: 장르 선택 후 필요한 서비스만 lazy-initialize하도록 변경할 것.

---

### P2-7. `constants.py`에서 모듈 레벨 `_threshold()` 호출 -- import 시 YAML 로드

**파일**: `modules/core/constants.py` L8, L95~98

```python
from modules.validation.threshold_helper import _threshold

class ManuscriptLimits:
    MIN_LENGTH = _threshold("manuscript.min_length", 4000)
```

`_threshold()`는 내부적으로 `ConfigManager().load_settings()`를 호출하여 `validation.yaml`을 로드한다. 이 호출이 모듈 import 시점에 발생하므로, YAML 파일이 없거나 파싱 실패 시 import 자체는 성공하지만 (fallback default 반환), 예상치 못한 시점에 파일 I/O가 발생한다.

**영향**: import 시 부작용. 테스트 환경에서 YAML 파일 경로가 달라지면 기본값이 사용됨.

**권고**: 현재 fallback이 잘 작동하므로 당장의 수정은 불필요하나, 이 동작을 문서화할 것.

---

## 개선 아이디어

### I-1. DBManager 커서 관리 패턴 표준화

현재 DBManager는 `self.cursor`(인스턴스 공유 커서)를 사용하는 메서드와 `self.conn.cursor()`(로컬 커서)를 사용하는 메서드가 혼재되어 있다. `_migrate_vec_memory_db()`는 로컬 커서를 사용하고 `finally`에서 닫는 좋은 패턴을 따르지만, 대부분의 CRUD 메서드는 공유 커서를 사용한다.

**제안**: 모든 공개 메서드에서 로컬 커서를 사용하도록 통일하고, `@contextmanager`로 커서 생성/해제를 래핑하는 헬퍼를 만들 것.

```python
@contextmanager
def _cursor(self):
    cur = self.conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
```

---

### I-2. VecMemory 임베딩 결과 캐싱

`_embed_text()`는 동일한 텍스트에 대해 매번 Google API를 호출한다. 같은 에피소드의 텍스트가 여러 쿼리에서 반복적으로 임베딩될 때 불필요한 API 호출과 비용이 발생한다.

**제안**: LRU 캐시(최대 100개)를 `_embed_text()`에 적용하여 동일 텍스트의 재임베딩을 방지할 것. 캐시 키는 텍스트의 MD5 해시를 사용.

---

### I-3. DBManager 연결 풀링 또는 WAL 모드 활성화

현재 단일 연결(`sqlite3.connect()`)을 사용하고 RLock으로 보호한다. SQLite의 WAL(Write-Ahead Logging) 모드를 활성화하면 읽기와 쓰기가 동시에 가능해져 병목이 줄어든다.

**제안**: `_boot_db()` 시작 부분에 다음을 추가:
```python
self.conn.execute("PRAGMA journal_mode=WAL")
self.conn.execute("PRAGMA synchronous=NORMAL")
```

---

### I-4. FactLedger/WorldStateManager 변경 이벤트 알림 시스템

현재 FactLedger와 WorldStateManager는 `save()` 호출 시점을 호출자가 결정해야 한다. `update_from_state_changes()` 내부에서 자동 저장하지 않으므로, 호출자가 `save()`를 잊으면 데이터가 유실될 수 있다.

**제안**: `update_from_state_changes()` 호출 횟수를 추적하여, N회 이상 또는 마지막 저장 후 일정 시간 경과 시 자동 `save()`를 수행하는 dirty flag 패턴을 도입할 것.

---

### I-5. BaseAgent API 호출 로깅 구조화

현재 API 호출 로그가 이모지 기반 한글 메시지로 출력되어 파싱이 어렵다. 구조화된 로깅(JSON 형식)을 도입하면 로그 분석과 모니터링이 용이해진다.

**제안**: 주요 이벤트(API 호출/성공/실패/폴백/키순환)에 대해 `logging.info(json.dumps({...}))`로 구조화된 로그를 병행 출력할 것.

---

### I-6. StateTracker 메모리 사용 최적화

`StateTracker`는 17종 이상의 dict/list를 인스턴스 변수로 유지한다 (`npc_registry`, `entity_name_registry`, `skill_cooldown_registry`, `dungeon_clear_registry`, `spell_repertoire`, `blessing_curse_registry`, `filmography_registry` 등). 장르에 따라 대부분의 레지스트리가 사용되지 않지만 항상 초기화된다.

**제안**: 장르 감지 후 필요한 레지스트리만 초기화하거나, `__slots__`를 활용하여 메모리 사용을 줄일 것.

---

### I-7. ContextAdvisor 장르 힌트 외부화

`ContextAdvisor._GENRE_HINTS`가 Python 코드에 하드코딩되어 있다. 장르 추가 시 코드 수정이 필요하다.

**제안**: `config/smart_retrieval/genre_hints.yaml`로 외부화하여 코드 변경 없이 장르별 힌트를 추가/수정할 수 있게 할 것.

---

### I-8. main_a.py import 최적화

`main_a.py`의 상단에 30개 이상의 import가 있으며, 이 중 일부(`FourPhaseArcGenerator`, `StateLockedArcGenerator` 등)는 특정 Stage에서만 사용된다. 모듈 로드 시간이 길어질 수 있다.

**제안**: Stage별로 lazy import를 적용하여 초기 로드 시간을 줄일 것. 특히 Stage 2 전용 에이전트는 Stage 2 진입 시에만 import하도록 변경.

---

## 특이사항 (양호)

감사 과정에서 다음 항목들은 잘 구현되어 있음을 확인했다:

1. **VecMemory의 커서 관리**: `memorize_v20_episode()`, `delete_episodes_from()` 등에서 로컬 커서 생성 + `finally` 블록에서 `cursor.close()` 호출 패턴이 일관되게 적용됨. DBManager보다 우수한 패턴.

2. **VecMemory의 차원 마이그레이션**: 임베딩 모델 변경 시 자동으로 vec_episodes 테이블을 재생성하고 sync_status를 리셋하는 로직이 견고함.

3. **DBManager의 `_safe_json_loads()` 방어**: JSON 파싱 실패 시 기본값을 반환하여 단일 행 파손이 전체 조회를 크래시하지 않도록 방어함.

4. **BaseAgent의 429/Rate Limit/Quota 3단 구분**: Rate Limit(분당 제한), Quota Exhausted(일/월 제한), gemini-3-pro 특수 처리가 잘 구분되어 있음.

5. **BaseAgent의 네트워크 복원력**: 22회까지 재시도, 백오프, 하트비트 출력 등 야간 무인 운영에 적합한 복원력을 갖추고 있음.

6. **WorldStateManager/FactLedger의 state_changes 파싱**: dict/str 양방향 처리, None 방어, 중복 방지 등이 철저함.

7. **DBManager의 트랜잭션 컨텍스트 매니저**: `transaction()` 메서드가 중첩 트랜잭션을 올바르게 처리하고, 에러 타입별 롤백 전략을 적용함.

---

*감사 완료: 2026-02-22*
*감사자: Claude Opus 4.6*
*대상 파일: 14개 모듈, 약 6,500줄*
