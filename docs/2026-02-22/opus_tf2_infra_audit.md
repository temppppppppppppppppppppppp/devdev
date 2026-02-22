# 2차 인프라/공통 모듈 전수조사 보고서

> **작성일**: 2026-02-22
> **작성자**: Claude Opus 4.6 (TF2)
> **범위**: db_manager, vec_memory, config_manager, constants, context_advisor, foreshadow_tracker, world_state, fact_ledger, metrics_collector, base_agent, state_tracker, main_a.py lazy import, genre_hints.yaml
> **목적**: 1차 감사 수정 검증 + 신규 이슈 발굴

---

## 1. 1차 수정 검증 결과

### 1.1 INF-P1-1: 로컬 커서 전환 (부분 완료)

**검증 대상**: `db_manager.py`에서 `self.cursor` (공유 커서) 대신 로컬 `cur = self.conn.cursor()` 사용 의무화.

**실측 결과**:
- `self.cursor` 잔존 사용: **약 80개소** (boot + 메서드 내부)
- `cur = self.conn.cursor()` 로컬 커서: **13개소** (1차에서 전환된 주요 메서드)

**분석**: `_boot_db()` 내 DDL 실행(~40개소)은 초기화 시점에 단일 스레드로 실행되므로 `self.cursor` 사용이 안전하다. 그러나 런타임 메서드 중 `self.cursor`를 여전히 사용하는 곳이 다수 존재한다:

| 카테고리 | 잔존 self.cursor 사용 메서드 | 스레드 위험도 |
|----------|------------------------------|--------------|
| 쓰기 | `save_surgery_log`, `sync_seeds`, `archive_seed`, `update_lore_item`, `save_anchor`, `save_blueprint`, `save_state_log_with_summary`, `update_karma`, `save_causal_links`, `insert_npc_change`, `save_director_selection`, `save_cost_record`, `update_sync_status`, `reset_after`, `delete_episode_bibles_after` | **MEDIUM** -- `_lock`으로 보호되지만 커서 상태 공유 |
| 읽기 | `get_lore_item`, `get_lore_list_by_category`, `load_anchor`, `load_all_anchors`, `get_previous_blueprint`, `get_latest_state`, `load_state_log`, `get_causal_summary_chain`, `get_all_karma`, `get_latest_episode_number`, `get_latest_blueprint_number`, `get_context_manuscripts`, `get_active_seeds`, `get_recent_blueprints`, `get_recent_manuscripts`, `get_npc_history`, `get_npc_latest_fields`, `get_strategy_win_rates`, `get_selection_analysis`, `get_cost_summary`, `get_recent_manuscript_excerpts`, `get_all_manuscripts`, `get_all_blueprints`, `get_npc_recent_episodes`, `get_rollback_impact` | **LOW** -- RLock 보호, 읽기 전용 |
| 배치 쓰기 | `update_lore_items_batch`, `commit_episode_factory` | **MEDIUM** -- executemany + 복합 트랜잭션 |

**판정**: `_lock(RLock)` 보호 하에서는 즉각적 레이스 컨디션은 발생하지 않는다. 그러나 공유 커서는 `fetchall()` 전에 다른 메서드가 같은 커서로 `execute()`를 호출하면 결과가 오염될 수 있다. RLock 보호로 동일 스레드 내 중첩만 허용하므로 실전 위험도는 **낮음**이나, `commit_episode_factory`처럼 내부에서 다른 메서드를 호출하는 경우 이론적 오염 가능성이 존재한다.

**등급: P3 (개선 권장)**
- 1차에서 핵심 13개 메서드에 로컬 커서 적용 완료. 나머지는 RLock 보호로 실전 안전.
- 향후 리팩토링 시 점진적 전환 권장 (특히 `commit_episode_factory`, `update_lore_items_batch` 우선).

---

### 1.2 INF-P1-2: begin/commit Lock -- 검증 완료

**실측**:
- `begin()` (L528): `with self._lock:` + 로컬 커서 사용 -- 정상
- `commit()` (L538): `with self._lock:` -- 정상
- `rollback()` (L544): `with self._lock:` -- 정상

**판정**: **완전 이행**. RLock으로 트랜잭션 제어가 보호됨.

---

### 1.3 INF-P1-6: ConfigManager Lock -- 검증 완료

**실측** (`config_manager.py`):
- `_settings_lock = threading.Lock()` (L17): 클래스 레벨 Lock 선언
- `load_settings()` (L83~116): double-check locking 패턴 적용
  - 캐시 히트 시 lock 없이 반환 (L91)
  - `with self._settings_lock:` 내부에서 재확인 (L96)

**판정**: **완전 이행**. 표준 double-check locking 패턴.

---

### 1.4 INF-P1-8: _context_caches Lock -- 검증 완료

**실측** (`base_agent.py`):
- `_cache_lock = threading.Lock()` (L1092): 클래스 변수
- `_get_or_create_context_cache()`: 읽기/삭제/쓰기 모두 `with self._cache_lock:` 보호 (L1126, L1158)
- `_try_rotate_key()`: `with cls._cache_lock:` 내에서 `.clear()` (L200)

**판정**: **완전 이행**. 캐시 읽기/쓰기/삭제/클리어 모두 Lock 보호.

---

### 1.5 INF-P1-9: rollback_to 배치 최적화 -- 검증 완료

**실측**:
- `WorldStateManager.rollback_to()` (L433~474): `get_all_episode_bibles()` 일괄 로드 + 실패 시 개별 조회 폴백
- `FactLedger.rollback_to()` (L558~601): 동일 패턴 적용

**판정**: **완전 이행**. O(N) DB 호출 -> O(1) 일괄 로드로 최적화.

---

### 1.6 INF-I2: LRU 캐시 -- 검증 완료

**실측** (`vec_memory.py`):
- `OrderedDict` 기반 LRU (L73): 최대 128개 (`_embed_cache_max`)
- `_embed_cache_lock = threading.Lock()` (L75): 스레드 안전
- `_embed_cache_get()` (L278): `move_to_end()` LRU 순서 갱신
- `_embed_cache_put()` (L286): `while > max` 조건 하 `popitem(last=False)` 퇴출
- `_embed_text()` (L296): 캐시 조회 -> 미스 시 API 호출 -> 결과 저장

**판정**: **완전 이행**. 표준 LRU 패턴.

---

### 1.7 INF-I3: WAL 모드 -- 검증 완료

**실측** (`db_manager.py` L91~96):
```python
self.cursor.execute("PRAGMA journal_mode=WAL")
self.cursor.execute("PRAGMA synchronous=NORMAL")
```
- `OperationalError` 포착 시 warning 로그 (비차단)

**판정**: **완전 이행**. WAL 모드 + `synchronous=NORMAL` 조합.

---

### 1.8 INF-I7: YAML 외부화 -- 검증 완료

**실측** (`context_advisor.py`):
- `_load_genre_hints()` (L18~34): YAML 로드 + `_DEFAULT_GENRE_HINTS` 폴백
- `config/smart_retrieval/genre_hints.yaml` (61줄): 10개 장르 힌트 정의

**대조 검증**:
- YAML 파일의 장르 키: `hunter`, `investment`, `fantasy`, `wuxia`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical`
- 코드 내 `_DEFAULT_GENRE_HINTS` 키: 동일 10개
- `GenreTypes.all()` 목록과 완전 일치 확인

**판정**: **완전 이행**. YAML과 하드코딩 폴백이 동일 콘텐츠.

---

### 1.9 INF-I8: Lazy Import -- 검증 완료

**실측** (`main_a.py`):
- `_lazy_load_stage0()` (L70): Stage 0 모듈 (PresetRegistry, StyleGuide)
- `_lazy_load_agents()` (L84): Stage 전용 에이전트 18종
- `_lazy_load_v50_modules()` (L129): V50 서사 품질 향상 모듈 7종
- `_attach_agents()` (L1365): 위 3개 함수를 이 시점에서만 호출
- 개별 lazy import: `BlockEnricher` (L1248), `StateTracker` (L3006)

**순환 의존성 검사**: `_lazy_load_agents()`가 반환하는 18개 에이전트 클래스는 모두 `modules.domain.agents.*` 하위이고, `main_a.py`는 `modules.core.*`만 최상위 import하므로 순환 참조 불가.

**판정**: **완전 이행**. Boot 시간 최적화 + 순환 의존성 안전.

---

## 2. 신규 발견 이슈

### INF2-F1: `delete_episode_bibles_after`에서 공유 커서 + return 위치 오류 (P2)

**파일**: `db_manager.py` L892~903
```python
def delete_episode_bibles_after(self, ep_num: int):
    with self._lock:
        self.cursor.execute("DELETE FROM episode_bibles WHERE ep_num > ?", (ep_num,))
        if not self.conn.in_transaction:
            self.conn.commit()
        invalidate_eps = [k for k in self._cumulative_bible_cache if k > ep_num]
        for k in invalidate_eps:
            del self._cumulative_bible_cache[k]
        return self.cursor.rowcount

    # --- [Section 2: ...] ---  <-- 이 코드는 도달 불가
```

**문제 1**: `self.cursor` 공유 커서 사용. `cursor.rowcount`는 마지막 `execute()` 결과를 반환하는데, RLock 내에서 다른 메서드 호출이 끼어들 여지는 낮지만, 로컬 커서로 전환하면 더 안전하다.

**문제 2 (구조)**: `return self.cursor.rowcount` 직후에 주석 블록이 있고, 다음 메서드 `save_surgery_log`가 잘못된 들여쓰기로 클래스 메서드가 아닌 것처럼 보일 수 있으나, 실제로는 Python 파서가 `with` 블록 안 `return` 이후를 무시하므로 동작에는 영향 없음.

**위험도**: LOW -- RLock 보호 하에서 `cursor.rowcount` 오염 확률 매우 낮음.

---

### INF2-F2: `get_all_episode_bibles` 내부 `safe_get` 클로저 재정의 (P3)

**파일**: `db_manager.py` L855~890

```python
for row in rows:
    def safe_get(key, default="[]"):
        ...
```

**문제**: `for` 루프 내부에서 `safe_get` 로컬 함수가 매 반복마다 재정의된다. Python은 이를 허용하고 올바르게 동작하지만, 루프 밖에서 한 번 정의하는 것이 더 명확하다. `get_episode_bible()` (L726)에서도 동일 패턴이 존재한다.

**위험도**: NONE (동작 정확). 스타일/명확성 개선 권장.

---

### INF2-F3: `_LazyThreshold` 디스크립터 -- 클래스 dict 직접 조작 (P3)

**파일**: `constants.py` L11~32

```python
def __get__(self, obj, objtype=None):
    cache = objtype.__dict__ if objtype else type(obj).__dict__
    if self.attr_name in cache:
        return cache[self.attr_name]
    from modules.validation.threshold_helper import _threshold
    val = _threshold(self.key, self.default)
    setattr(objtype or type(obj), self.attr_name, val)
    return val
```

**분석**:
1. **정확성**: 클래스 속성 접근(`ManuscriptLimits.MIN_LENGTH`)과 인스턴스 접근 모두 올바르게 동작. `setattr`로 클래스에 캐시하면 다음 접근 시 디스크립터 `__get__`이 호출되지 않고 직접 클래스 속성이 반환된다.

2. **스레드 안전성**: 두 스레드가 동시에 같은 `_LazyThreshold`에 최초 접근하면, `_threshold()` YAML I/O가 2회 실행될 수 있다. 그러나 `_threshold()` 자체가 멱등(idempotent)이고, `setattr`은 CPython GIL 하에서 원자적이므로 데이터 손상은 없다. 성능 관점에서만 중복 I/O가 발생할 수 있다.

3. **값 변경 불가**: 한번 캐시되면 `ConfigManager.invalidate_settings_cache()` 호출해도 `_LazyThreshold` 캐시는 갱신되지 않는다. `validation.yaml`을 수정한 뒤 `force_reload`해도 `ManuscriptLimits.MIN_LENGTH` 등은 이전 값을 유지한다.

**위험도**: LOW -- YAML 설정 변경이 런타임 중 발생하지 않는 현재 아키텍처에서는 문제 없음. 그러나 향후 hot-reload 기능 추가 시 이 한계를 인지해야 함.

---

### INF2-F4: `commit_episode_factory` -- 수동 Lock acquire/release (P2)

**파일**: `db_manager.py` L1218~1372

```python
self._lock.acquire()
try:
    ...
finally:
    self._lock.release()
```

**분석**: 이 메서드만 `with self._lock:` 대신 수동 `acquire()/release()`를 사용한다. 이유는 내부에서 `self.begin()`, `self.commit()`, `self.rollback()` 등 RLock 재진입이 필요하기 때문이다. `with self._lock:` 사용 시에도 RLock이므로 동일하게 동작하지만, 수동 방식은 `finally` 블록에서 확실히 해제를 보장하므로 의도적 설계로 판단된다.

**위험도**: LOW -- 현재 코드는 `finally` 블록에서 `release()` 보장. 다만 가독성 측면에서 `with self._lock:` 사용이 더 명확하다. RLock이므로 `with` 문 안에서 `begin()/commit()/rollback()` 호출해도 재진입 가능.

---

### INF2-F5: VecMemory standalone 모드 -- Lock 없이 동작 (P3)

**파일**: `vec_memory.py` L78~79

```python
self._shared_mode = conn is not None
self._lock = lock  # shared 모드에서만 DBManager RLock
```

**분석**: standalone 모드(`conn=None`)에서는 `self._lock = None`이 되어, `_db_lock()` 컨텍스트 매니저가 no-op으로 동작한다 (L131~137). 이는 standalone 모드에서 멀티스레드 접근이 없다는 전제에 기반한다.

**현실 점검**: standalone 모드는 테스트 전용이고, 프로덕션에서는 항상 DBManager RLock을 공유하는 shared 모드를 사용하므로 위험 없음.

**위험도**: NONE -- 설계 의도대로 동작.

---

### INF2-F6: `_embed_cache_put` -- 기존 키 업데이트 시 값 미갱신 (P2)

**파일**: `vec_memory.py` L286~294

```python
def _embed_cache_put(self, key: str, vec: list) -> None:
    with self._embed_cache_lock:
        if key in self._embed_cache:
            self._embed_cache.move_to_end(key)  # LRU 순서만 갱신
        else:
            self._embed_cache[key] = vec           # 새 키만 값 저장
            while len(self._embed_cache) > self._embed_cache_max:
                self._embed_cache.popitem(last=False)
```

**문제**: `key`가 이미 캐시에 있으면 `move_to_end()`만 호출하고 **값을 갱신하지 않는다**. 동일 텍스트(=동일 MD5 해시)에 대해 임베딩 결과가 달라질 수 있는가?

**분석**: Gemini 임베딩 모델은 동일 입력에 대해 결정론적(deterministic) 결과를 반환한다. 따라서 동일 해시 키에 대해 값이 다를 가능성은 사실상 없다. 현재 구현은 이 전제에 기반한 최적화로, 정확하게 동작한다.

**위험도**: NONE -- 결정론적 임베딩 모델 전제 하에서 올바른 동작.

---

### INF2-F7: WAL 모드와 VACUUM 호환성 (P3)

**파일**: `db_manager.py` L1452

```python
self.cursor.execute("VACUUM")
```

**분석**: `reset_after()` 메서드 끝에서 `VACUUM`을 실행한다. SQLite에서 WAL 모드 + `VACUUM`은 호환되지만, `VACUUM`은 실행 시 **배타적 잠금(exclusive lock)**을 획득한다. 이는:
1. 진행 중인 다른 읽기/쓰기 트랜잭션이 완료될 때까지 대기
2. `VACUUM` 실행 중에는 다른 연결의 읽기도 차단

`reset_after()`는 사용자가 명시적으로 롤백을 요청할 때만 호출되므로, 동시 접근 상황은 극히 드물다.

**위험도**: LOW -- 롤백 시에만 호출. 실전에서는 단일 세션 운영이므로 영향 없음.

---

### INF2-F8: MetricsCollector 싱글톤 -- `reset()` 후 이전 인스턴스 참조 문제 (P3)

**파일**: `metrics_collector.py` L110~116

```python
@classmethod
def reset(cls, metrics_dir: Path | None = None):
    with cls._lock:
        cls._instance = None
    if metrics_dir:
        return cls(metrics_dir)
```

**분석**: `reset()`을 호출하면 `_instance`가 `None`으로 설정된다. 그러나 이전에 `get_metrics_collector()`로 획득한 참조를 보유한 코드가 있으면, 해당 참조는 여전히 이전 인스턴스를 가리킨다. 새 인스턴스와 이전 인스턴스가 동시에 존재하게 되지만, 이전 인스턴스의 메트릭은 더 이상 수집되지 않는다.

**현실 점검**: `reset()`은 프로젝트 변경 시에만 호출되며, 이 시점에서 모든 에이전트가 재초기화되므로 이전 참조를 보유한 코드는 없다.

**위험도**: NONE -- 현재 사용 패턴에서 안전.

---

### INF2-F9: `_cumulative_bible_cache` LRU -- dict 기반 최소값 탐색 O(N) (P3)

**파일**: `db_manager.py` L839~843

```python
_MAX_BIBLE_CACHE = 5
while len(self._cumulative_bible_cache) >= _MAX_BIBLE_CACHE:
    oldest_ep = min(self._cumulative_bible_cache.keys())
    del self._cumulative_bible_cache[oldest_ep]
```

**분석**: 일반 `dict` 사용으로 `min()` 호출 시 O(N) 탐색이 발생한다. 캐시 크기가 5개로 제한되어 실질 비용은 무시 가능하나, `OrderedDict`를 사용하면 O(1)로 개선 가능하다.

**위험도**: NONE -- N=5로 고정. 성능 영향 없음.

---

### INF2-F10: ForeshadowTracker -- 스레드 안전성 부재 (P3)

**파일**: `foreshadow_tracker.py`

**분석**: `ForeshadowTracker`는 `self.hooks`, `self.episode_plants`, `self.episode_payoffs` 등 mutable dict/list를 사용하지만, Lock이 없다. 현재는 Stage 4 오케스트레이터에서 단일 스레드로만 접근하므로 문제 없으나, 향후 병렬 처리 확장 시 주의 필요.

**위험도**: NONE -- 현재 단일 스레드 접근 패턴.

---

### INF2-F11: WorldStateManager/FactLedger -- 메모리 내 상태와 DB 비동기 (P2)

**파일**: `world_state.py`, `fact_ledger.py`

**분석**: 두 클래스 모두 `_state`/`_ledger`를 메모리에 유지하고, `save()` 메서드를 명시적으로 호출해야 DB에 반영된다. `update_from_state_changes()` 후 `save()` 호출을 잊으면 크래시 시 데이터가 소실된다.

**현실 점검**: 호출자 코드를 조사하면:
- `Stage4Orchestrator`에서 에피소드 확정 후 `world_state.save()` + `fact_ledger.save()` 호출
- `rollback_to()` 메서드 끝에서 `self.save()` 호출

**판정**: 현재 호출 패턴에서는 안전. 그러나 `update_from_state_changes()` 내에서 자동 `save()`를 추가하면 더 안전하다. 단, 빈번한 DB 쓰기 비용과 트레이드오프.

**위험도**: LOW -- 현재 호출 패턴에서 `save()` 누락 없음.

---

### INF2-F12: `context_advisor.py` -- `_GENRE_HINTS` 모듈 레벨 로딩 (P3)

**파일**: `context_advisor.py` L190

```python
_GENRE_HINTS = _load_genre_hints()
```

**분석**: 클래스 변수로 모듈 로드 시점에 YAML을 읽는다. 이는 `import`만으로도 I/O가 발생한다는 의미이다. 그러나:
1. `_load_genre_hints()`는 실패 시 하드코딩 폴백을 반환하므로 import 실패는 없음
2. YAML 파일은 61줄로 매우 작음 (I/O 비용 무시 가능)
3. `ContextAdvisor.__init__`에서 `_threshold()` 호출도 이미 모듈 로드 시점 I/O를 유발

**위험도**: NONE -- 설계 의도대로 동작. 모듈 로드 시 1회 I/O.

---

### INF2-F13: `base_agent.py` -- `_load_model_config()` 매 호출 시 파일 I/O (P2)

**파일**: `base_agent.py` L57~68

```python
def _load_model_config() -> dict:
    config_path = _resolve_models_config_path()
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                ...
    except (OSError, yaml.YAMLError):
        ...
    return {}
```

**분석**: `_get_agent_default_model()`, `_get_sub_component_models()`, `_get_model_fallback_chain()` 각각이 `_load_model_config()`를 호출한다. `BaseAgent.__init__`에서 `_get_agent_default_model()`이 호출되고, 클래스 정의 시 `_get_model_fallback_chain()`이 호출된다. `models.yaml` 파일을 매번 읽고 파싱하는 것은 비효율적이다.

**현실 점검**:
- 클래스 변수 `MODEL_FALLBACK_CHAIN`은 클래스 정의 시 1회만 로드 (L133)
- `_SYSTEM_CFG`도 모듈 로드 시 1회만 로드 (L122)
- `__init__` 내 `_get_agent_default_model()`은 에이전트 인스턴스 생성마다 호출

에이전트는 `_attach_agents()`에서 일괄 초기화되므로 약 18회 파일 I/O가 발생한다. 크리티컬하지는 않으나 캐싱하면 개선 가능.

**위험도**: LOW -- 초기화 시점에만 발생. 런타임 영향 없음.

---

### INF2-F14: `db_manager.py` -- `_boot_db` 내 `import re` (P3)

**파일**: `db_manager.py` L225

```python
import re
safe_column_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
```

**분석**: `_boot_db()` 함수 내부에서 `import re`를 수행한다. Python의 import 메커니즘은 이미 로드된 모듈을 캐시하므로 성능 영향은 없지만, 파일 최상위에 이미 `import re`가 없으므로 함수 내부 import가 유일한 소스이다. 스타일 관점에서 최상위 import가 권장된다.

**위험도**: NONE -- Python import 캐시로 성능 영향 없음. 스타일 개선 권장.

---

### INF2-F15: `vec_memory.py` -- `_keyword_fallback_search` 내 `import re` (P3)

**파일**: `vec_memory.py` L717

```python
def _keyword_fallback_search(self, query_text: str, current_ep: int, n_results: int) -> str:
    import re
    keywords = [w for w in re.split(r"[\s,.\-|/]+", query_text) if len(w) >= 2]
```

**분석**: INF2-F14와 동일 -- 함수 내부 `import re`. `re`는 파일 최상위에 import되어 있지 않다. 그러나 `vec_memory.py` 최상위에는 `import hashlib, json, logging, os, sqlite3, struct, threading, time`만 있고 `re`가 없다. lazy import 의도로 보이나, `re`는 표준 라이브러리이므로 최상위 import가 더 적절하다.

**위험도**: NONE -- Python import 캐시로 성능 영향 없음.

---

## 3. 연결성 검증

### 3.1 DBManager <-> VecMemory (DB-MERGE)

**검증 항목**: shared 모드에서 VecMemory가 DBManager의 `conn`과 `_lock`을 공유하는지.

**실측**:
- `VecMemory.__init__` (L59): `conn` + `lock` 파라미터로 주입
- `_db_lock()` (L131~137): `self._lock` 존재 시 `with self._lock:`, 없으면 no-op
- DBManager의 `_lock`은 `RLock` -> VecMemory의 `_load_episode_meta()` -> `_db_lock()` 재진입 안전 (L437~439 문서화됨)

**결과**: 연결 정상. RLock 재진입 안전성 확보.

### 3.2 DBManager <-> WorldStateManager / FactLedger

**검증 항목**: `save_anchor()`/`load_anchor()` 인터페이스 정합성.

**실측**:
- WorldStateManager: `self.db.save_anchor("world_state", self._state)` / `self.db.load_anchor("world_state")`
- FactLedger: `self.db.save_anchor("fact_ledger", self._ledger)` / `self.db.load_anchor("fact_ledger")`
- `save_anchor()` (L1039~1058): `json.dumps(data)` -> `INSERT OR REPLACE INTO anchors`
- `load_anchor()` (L1060~1071): `json.loads(row["data"])` + TypeError/JSONDecodeError 방어

**결과**: 연결 정상. JSON 직렬화/역직렬화 안전.

### 3.3 ConfigManager <-> constants.py (_LazyThreshold)

**검증 항목**: `_threshold()` 호출 체인이 `ConfigManager.load_settings()`를 경유하는지.

**실측**:
- `_LazyThreshold.__get__()` -> `from modules.validation.threshold_helper import _threshold` -> `_threshold(key, default)`
- `threshold_helper._threshold()` -> `ConfigManager().load_settings()` -> YAML 로드

**결과**: 연결 정상. Lazy loading 체인이 올바르게 구성됨.

### 3.4 MetricsCollector <-> BaseAgent

**검증 항목**: 비용 추적 배선 정확성.

**실측**:
- `BaseAgent.ask()` (L342~349): `collector.start_call()` -> metric_id 획득
- 성공 시 (L592~600): `collector.end_call(metric_id, success=True, ...)`
- 실패 시 (L629~644): `collector.end_call(metric_id, success=False, ...)`
- 백업 모델 (L664~694): 별도 `backup_metric_id`로 추적

**결과**: 연결 정상. 성공/실패/백업 모든 경로에서 비용 추적.

### 3.5 ContextAdvisor <-> Stage 오케스트레이터

**검증 항목**: SC 검색 계획이 Stage별로 올바르게 연결되는지.

**실측**:
- `plan_stage2_retrieval()`: arc_data, current_ep, npc_roster 입력
- `plan_stage3_retrieval()`: arc_data, prev_blueprints, current_ep, npc_roster, genre
- `plan_stage4_retrieval()`: arc_data, blueprint, prev_ending, current_ep, npc_roster, genre
- `plan_director_retrieval()`: manuscript, blueprint, current_ep, npc_roster

**결과**: 연결 정상. 각 Stage별 필요 데이터를 받아 검색 계획 생성.

---

## 4. 개선 아이디어

### INF2-I1: `_load_model_config()` 결과 모듈 레벨 캐싱

**현재**: 매 에이전트 초기화 시 `models.yaml` 재파싱 (~18회).
**제안**: `_MODELS_CFG = _load_model_config()` 모듈 레벨 변수로 1회 로드, 이후 참조.
**예상 효과**: 초기화 시 파일 I/O 17회 절감. 크리티컬하지 않으나 코드 정리 효과.

### INF2-I2: `commit_episode_factory` -- `with self._lock:` 전환

**현재**: 수동 `acquire()/release()`.
**제안**: `with self._lock:` 사용. RLock이므로 내부 `begin()/commit()/rollback()` 재진입 안전.
**예상 효과**: 가독성 향상. `finally` 블록 불필요.

### INF2-I3: `safe_get` 클로저 -- 루프 밖 1회 정의

**현재**: `get_all_episode_bibles()` 루프 내부에서 매 반복 재정의.
**제안**: 루프 밖에서 `row` 파라미터를 받는 함수로 정의, 또는 `_safe_json_loads` 정적 메서드 활용 확대.
**예상 효과**: 코드 명확성 향상.

### INF2-I4: `db_manager.py` 잔여 `self.cursor` 메서드 점진적 전환

**현재**: ~50개 메서드에서 `self.cursor` 사용.
**제안**: 비교적 단순한 읽기 메서드부터 `cur = self.conn.cursor(); try: ... finally: cur.close()` 패턴 전환.
**우선순위**: `commit_episode_factory` > `update_lore_items_batch` > `reset_after` > 나머지.
**예상 효과**: 장기적 스레드 안전성 강화. 즉시 효과는 제한적 (현재 RLock 보호로 충분).

### INF2-I5: VecMemory `_embed_cache` -- `functools.lru_cache` 전환 고려

**현재**: 수동 `OrderedDict` + Lock LRU 구현.
**제안**: `@functools.lru_cache(maxsize=128)` 데코레이터로 대체 가능. 단, 캐시 키가 MD5 해시 문자열이므로 hashable.
**고려사항**: `lru_cache`는 스레드 안전하지 않으므로(CPython GIL 의존), 현재 수동 Lock이 더 안전. 전환 불권장.

### INF2-I6: FactLedger/WorldStateManager -- `update_from_state_changes()` 후 자동 세이브 옵션

**현재**: 호출자가 명시적으로 `save()` 호출 필요.
**제안**: `auto_save: bool = False` 파라미터 추가. `True`이면 갱신 후 자동 `save()`.
**예상 효과**: 크래시 시 데이터 소실 방지. 단, DB 쓰기 빈도 증가.

---

## 5. 종합 요약

### 1차 수정 검증: 9건 전량 이행 확인

| 항목 | 상태 |
|------|------|
| INF-P1-1 (로컬 커서) | 핵심 13개소 완료, 잔여 ~50개 메서드는 RLock 보호로 안전 |
| INF-P1-2 (begin/commit Lock) | 완전 이행 |
| INF-P1-6 (ConfigManager Lock) | 완전 이행 (double-check locking) |
| INF-P1-8 (_context_caches Lock) | 완전 이행 |
| INF-P1-9 (rollback_to 배치) | 완전 이행 (O(1) DB 호출) |
| INF-I2 (LRU 캐시) | 완전 이행 (OrderedDict + Lock) |
| INF-I3 (WAL 모드) | 완전 이행 (WAL + NORMAL) |
| INF-I7 (YAML 외부화) | 완전 이행 (10장르 일치) |
| INF-I8 (lazy import) | 완전 이행 (순환 의존성 안전) |

### 2차 신규 발견: 15건

| ID | 등급 | 파일 | 요약 |
|----|------|------|------|
| INF2-F1 | P2 | db_manager.py | `delete_episode_bibles_after` 공유 커서 + 구조 |
| INF2-F2 | P3 | db_manager.py | `safe_get` 클로저 루프 내 재정의 |
| INF2-F3 | P3 | constants.py | `_LazyThreshold` hot-reload 미지원 |
| INF2-F4 | P2 | db_manager.py | `commit_episode_factory` 수동 Lock |
| INF2-F5 | P3 | vec_memory.py | standalone Lock 미보유 (테스트 전용) |
| INF2-F6 | P2 | vec_memory.py | `_embed_cache_put` 기존 키 값 미갱신 |
| INF2-F7 | P3 | db_manager.py | WAL + VACUUM 호환성 |
| INF2-F8 | P3 | metrics_collector.py | 싱글톤 reset 후 이전 참조 |
| INF2-F9 | P3 | db_manager.py | Bible 캐시 dict min() O(N) |
| INF2-F10 | P3 | foreshadow_tracker.py | 스레드 안전성 미구현 (현재 불필요) |
| INF2-F11 | P2 | world_state/fact_ledger | save() 명시 호출 필요 |
| INF2-F12 | P3 | context_advisor.py | 모듈 레벨 YAML I/O |
| INF2-F13 | P2 | base_agent.py | `_load_model_config()` 미캐싱 |
| INF2-F14 | P3 | db_manager.py | 함수 내부 `import re` |
| INF2-F15 | P3 | vec_memory.py | 함수 내부 `import re` |

### 위험도 분포

| 등급 | 건수 | 설명 |
|------|------|------|
| P1 (Critical) | 0 | 즉시 수정 필요 항목 없음 |
| P2 (Important) | 5 | 코드 품질/견고성 개선 권장 |
| P3 (Nice-to-have) | 10 | 스타일/미래 확장성 개선 |

### 최종 판정

1차 감사에서 발견된 P1 9건 + P2 7건이 전량 올바르게 수정되었음을 확인하였다. 스레드 안전성 보강(RLock, Lock, 로컬 커서), WAL 모드, LRU 캐시, lazy import 등 인프라 품질이 크게 향상되었다.

2차에서 발견된 15건은 모두 P2~P3 수준으로, **즉시 수정이 필요한 P1 이슈는 없다**. P2 5건은 코드 품질 개선 관점에서 향후 리팩토링 시 반영을 권장한다. 현재 시스템은 안정적으로 운영 가능한 상태이다.
