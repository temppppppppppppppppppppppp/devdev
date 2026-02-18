# Debug Sweep 4차 — 전면 디버깅 플랜 (Codex 병렬 실행용)

> **목적**: 코드 품질·안전성·관측성 향상을 위한 21개 독립 수정 항목
> **규칙**: 각 항목은 독립 실행 가능 (의존성 없음). 수정 후 반드시 `set PYTHONIOENCODING=utf-8 && pytest tests/ -q` 통과 확인.
> **테스트 기준선**: 1,716 passed + 68 xfailed
> **Ruff**: 수정한 파일에 `python -m ruff check <파일> && python -m ruff format <파일>` 적용

---

## A. 런타임 크래시 방지 (CRITICAL)

### A-1: `adaptive_retry.py` — `max()` 빈 dict 가드 (3곳)

**파일**: `modules/core/adaptive_retry.py:576, 629, 718`
**현상**: `max(type_counts, key=type_counts.get)` — `type_counts`가 빈 dict이면 `ValueError: max() arg is an empty sequence`
**코드 (L576)**:
```python
type_counts = defaultdict(int)
for f in failures:
    type_counts[f.error_type] += 1
primary_error = max(type_counts, key=type_counts.get)  # ← 빈 dict면 크래시
```
**수정**: 3곳 모두 `if not type_counts: return ...` 가드 추가.
- L576: `if not type_counts: return {"primary_error": "unknown", "failure_count": len(failures), "priority_fixes": [], "avoid_patterns": [], "temperature_adjustment": 0}`
- L629: `if not type_counts: return False, "adversarial_self_play"`
- L718: `if not stats: continue` (이미 `if stats:` 가드 있으므로 확인만)
**테스트**: `type_counts` 빈 dict 케이스 추가 (1개).

---

### A-2: `pattern_tracker.py:831-832` — `max()` 빈 `emotion_balance` dict 가드

**파일**: `modules/core/pattern_tracker.py:831-832`
**현상**: `max(first["emotion_balance"], key=first["emotion_balance"].get)` — `emotion_balance`가 `{}`이면 `ValueError`
**코드**:
```python
"emotion_shift": {
    "from": max(first["emotion_balance"], key=first["emotion_balance"].get),  # ← 빈 dict
    "to": max(last["emotion_balance"], key=last["emotion_balance"].get),      # ← 빈 dict
},
```
**수정**: 삼항 연산자로 방어:
```python
"from": max(first["emotion_balance"], key=first["emotion_balance"].get) if first.get("emotion_balance") else "neutral",
"to": max(last["emotion_balance"], key=last["emotion_balance"].get) if last.get("emotion_balance") else "neutral",
```
**테스트**: 빈 emotion_balance 케이스 추가 (1개).

---

### A-3: `stage2_preflight.py:102-103` — `future.result()` 타임아웃 누락

**파일**: `modules/core/stage2_preflight.py:102-103`
**현상**: `ThreadPoolExecutor` + `future.result()` 조합에서 타임아웃 없음 → LLM API 행 시 무한 블록
**코드**:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
    _fut_drive = _parallel_exec.submit(_compute_arc_drive)
    _fut_preflight = _parallel_exec.submit(_compute_preflight)
    arc_drive = _fut_drive.result()           # ← 타임아웃 없음
    _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result()  # ← 타임아웃 없음
```
**수정**: `_fut_drive.result(timeout=300)` + `_fut_preflight.result(timeout=300)` (5분).
**테스트 불필요**: 단순 파라미터 추가.

---

### A-4: `validation_orchestrator.py:243-244` — `pre_llm_result["critical_issues"]` KeyError 방어

**파일**: `modules/validation/validation_orchestrator.py:243-244`
**현상**: `pre_llm_result["critical_issues"]` — pre_llm_validator가 키를 누락하면 `KeyError`
**코드**:
```python
logging.warning(f"❌ PRE-LLM 실패: {len(pre_llm_result['critical_issues'])}개 이슈")
for issue in pre_llm_result["critical_issues"][:3]:
```
**수정**: `.get("critical_issues", [])` 패턴으로 2곳 변경 + L252도 동일 적용.
```python
_issues = pre_llm_result.get("critical_issues", [])
logging.warning(f"❌ PRE-LLM 실패: {len(_issues)}개 이슈")
for issue in _issues[:3]:
```
**테스트**: `critical_issues` 키 누락 케이스 추가 (1개).

---

## B. 로깅 태그/레벨 불일치 (`[ERROR]` 태그 → `[WARNING]`)

### B-1: `validation_orchestrator.py:802`

**파일**: `modules/validation/validation_orchestrator.py:802`
**현상**: `logging.warning(f"[ERROR] Constitution 로드 실패 ({genre}): {e}")` — `[ERROR]` 태그인데 `warning` 레벨
**수정**: `[ERROR]` → `[WARNING]` 으로 태그 변경 (레벨과 일치).

### B-2: `consistency_validator.py:72`

**파일**: `modules/validation/consistency_validator.py:72`
**현상**: `logging.warning(f"[ERROR] Guard 로드 실패 ({genre}): {e}")`
**수정**: `[ERROR]` → `[WARNING]` 으로 태그 변경.

### B-3: `blocking_validator_entity_checks.py:142`

**파일**: `modules/validation/blocking_validator_entity_checks.py:142`
**현상**: `logging.warning(f"[ERROR] owned_items is not a list after processing: ...")`
**수정**: `[ERROR]` → `[WARNING]` 으로 태그 변경.

### B-4: `batch_validator.py:271`

**파일**: `modules/validation/batch_validator.py:271`
**현상**: `logging.warning(f"[ERROR] Async 실행 실패: {e}")`
**수정**: `[ERROR]` → `[WARNING]` 으로 태그 변경.

### B-5: `data_collector.py:133, 173` — 2곳

**파일**: `modules/core/data_collector.py:133, 173`
**현상**: `logging.warning(f"[ERROR] 파일 저장 실패 ({filepath}): {e}")` — 2곳 동일
**수정**: 2곳 모두 `[ERROR]` → `[WARNING]` 으로 태그 변경.

---

## C. 스레드 안전성

### C-1: `batch_validator.py:53, 101` — stats 초기화 Lock 누락

**파일**: `modules/validation/batch_validator.py:53, 101`
**현상**: `self.stats["total_manuscripts"] = len(manuscripts)` — `_stats_lock` 없이 dict 수정. 이후 `self.stats["completed"] += 1`은 Lock 사용. 초기화와 증분이 서로 다른 Lock 정책.
**코드 (L53)**:
```python
self.stats["total_manuscripts"] = len(manuscripts)  # ← Lock 없음
```
**수정**: 2곳 모두 `with self._stats_lock:` 블록 안으로 이동.
```python
with self._stats_lock:
    self.stats["total_manuscripts"] = len(manuscripts)
```
**테스트 불필요**: Lock 사용 패턴 변경.

---

### C-2: `validation_orchestrator.py:998` — `asyncio.get_event_loop()` deprecated

**파일**: `modules/validation/validation_orchestrator.py:998`
**현상**: `asyncio.get_event_loop()` — Python 3.10+에서 deprecated. 실행 중인 루프가 없으면 `DeprecationWarning` + 잠재적 RuntimeError.
**코드**:
```python
loop = asyncio.get_event_loop()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_workers)
```
**수정**: 이 함수는 `async def validate_parallel_v59()` 내부이므로 `asyncio.get_running_loop()` 사용:
```python
loop = asyncio.get_running_loop()
```
**테스트 불필요**: API 변경.

---

### C-3: `validation_orchestrator.py:999-1022` — executor를 with 문으로 변경

**파일**: `modules/validation/validation_orchestrator.py:999, 1022`
**현상**: `ThreadPoolExecutor` 생성 후 `executor.shutdown(wait=False)` 수동 호출 — context manager 미사용
**코드**:
```python
executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_workers)
# ... submit tasks, await gather ...
executor.shutdown(wait=False)
```
**수정**: `with` 문으로 리팩토링. `await asyncio.gather()` 이후 executor 정리는 자동.
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
    consistency_task = loop.run_in_executor(executor, ...)
    # ...
    consistency_result, scoring_result, advisory_result = await asyncio.gather(...)
# executor.shutdown(wait=False) 제거 — with 문이 자동 처리
```
**테스트 불필요**: 구조 리팩토링.

---

## D. 캐시 무결성

### D-1: `state_extractor.py` — `_state_cache` 키가 arc_no만 사용 → 내용 변경 시 스탈

**파일**: `modules/domain/agents/state_extractor.py:199, 214-216`
**현상**: Arc가 REJECT→재생성되면 `arc_no`는 동일하지만 내용이 달라짐. 캐시가 `arc_no` 기반이므로 이전 REJECT된 Arc의 추출 결과를 반환.
**코드**:
```python
self._state_cache: dict[int, dict] = {}

cache_key = arc_no if isinstance(arc_no, int) else hash(str(arc_no))
if cache_key in self._state_cache:
    return self._state_cache[cache_key]  # ← 스탈 데이터 반환 가능
```
**수정**: `invalidate_cache(arc_no=None)` 메서드 추가. `arc_no` 지정 시 해당 키만, None이면 전체 초기화.
```python
def invalidate_cache(self, arc_no=None):
    """캐시 무효화. arc_no 지정 시 해당 키만, None이면 전체."""
    if arc_no is not None:
        cache_key = arc_no if isinstance(arc_no, int) else hash(str(arc_no))
        self._state_cache.pop(cache_key, None)
    else:
        self._state_cache.clear()
```
Stage2 Arc REJECT 시 호출하는 코드 추가 필요. `modules/core/stage2_orchestrator.py`에서 Arc REJECT 후 `self.ctx.agents["state_extractor"].invalidate_cache(arc_no)` 호출.
**테스트**: 캐시 무효화 메서드 테스트 (1개).

---

### D-2: `chief_writer.py` — `_manuscript_cache` 롤백 시 무효화 누락

**파일**: `modules/domain/agents/chief_writer.py:784-788`
**현상**: `_manuscript_cache`와 `_cache_ep_num`이 에피소드 롤백 시 무효화되지 않음. 롤백된 에피소드의 원고가 캐시에 남아 클리셰/NPC 빈도 분석에 스탈 데이터 사용.
**코드**:
```python
if self._cache_ep_num == ep_num and self._manuscript_cache:
    return  # ← 롤백 후에도 이전 캐시 그대로 사용
```
**수정**: `invalidate_manuscript_cache()` 메서드 추가 + `main_a.py` 롤백 로직에서 호출.
```python
def invalidate_manuscript_cache(self):
    """원고 캐시 무효화 (에피소드 롤백 시 호출)."""
    self._manuscript_cache = {}
    self._cache_ep_num = -1
```
**테스트**: 캐시 무효화 메서드 테스트 (1개).

---

## E. 하드코딩 임계값 → 설정 참조

### E-1: `director_auditor.py:575, 596` — RepetitionGuard 파라미터 하드코딩

**파일**: `modules/domain/agents/director_auditor.py:575, 596`
**현상**: `RepetitionGuard(window_size=5, threshold=3)` + `clean_score < 0.85` — `validation.yaml`의 `premium.repetition.*`과 중복
**코드**:
```python
guard = RepetitionGuard(window_size=5, threshold=3)          # L575
if clean_score < 0.85:                                        # L596
```
**수정**: `from modules.validation.threshold_helper import _threshold` 사용.
```python
guard = RepetitionGuard(
    window_size=_threshold("premium.repetition.window_size", 5),
    threshold=_threshold("premium.repetition.threshold", 3),
)
if clean_score < _threshold("premium.repetition.clean_score_min", 0.85):
```
**테스트 불필요**: 기존 테스트가 기본값으로 커버.

---

### E-2: `pre_llm_validator.py:112` — `repetition_score` 임계값 하드코딩

**파일**: `modules/validation/pre_llm_validator.py:112`
**현상**: `repetitive.get("repetition_score", 0) > 0.6` — 매직넘버
**수정**: `validation.yaml`에 `pre_llm.repetition_score_threshold: 0.6` 추가 + `_threshold()` 사용.
```python
if repetitive.get("repetition_score", 0) > _threshold("pre_llm.repetition_score_threshold", 0.6):
```
**테스트 불필요**: 기존 테스트가 기본값으로 커버.

---

### E-3: `validation_orchestrator.py:1281` — 히스토리 크기 하드코딩

**파일**: `modules/validation/validation_orchestrator.py:1281`
**현상**: `if len(self.validation_history) > 50:` — 매직넘버 50
**수정**: 모듈 상수 추출: `_VALIDATION_HISTORY_MAX = 50` (파일 상단) + 참조.
**테스트 불필요**: 상수 추출.

---

## F. 타입 안전성 / 방어적 프로그래밍

### F-1: `analyst.py:234-235` — `injuries`/`status` 기본값 타입 혼합

**파일**: `modules/domain/agents/analyst.py:234-235`
**현상**: `.get("injuries", []) or .get("status", "")` — 리스트/문자열 혼합. 이후 `str()` 래핑으로 동작하지만 타입 불일치.
**코드**:
```python
prev_injuries = prev_end.get("injuries", []) or prev_end.get("status", "")
curr_injuries = curr_start.get("injuries", []) or curr_start.get("status", "")
```
**수정**: 일관된 문자열 타입으로 통일:
```python
prev_injuries = str(prev_end.get("injuries", "") or prev_end.get("status", ""))
curr_injuries = str(curr_start.get("injuries", "") or curr_start.get("status", ""))
```
**테스트 불필요**: 기존 로직 동작 보존.

---

### F-2: `analyst.py:277` — `tactical_doc` dict→str 폴백 시 Python repr 오염

**파일**: `modules/domain/agents/analyst.py:277`
**현상**: `tactical_doc.get("tactical_doc", "") or str(tactical_doc)` — key 누락 시 `str(dict)` → `"{'key': 'value'}"` 형태로 Python repr이 텍스트로 사용됨
**코드**:
```python
if isinstance(tactical_doc, dict):
    tactical_doc = tactical_doc.get("tactical_doc", "") or str(tactical_doc)
```
**수정**: `json.dumps(tactical_doc, ensure_ascii=False)` 폴백으로 변경 (사람이 읽을 수 있는 형태).
```python
if isinstance(tactical_doc, dict):
    tactical_doc = tactical_doc.get("tactical_doc", "") or json.dumps(tactical_doc, ensure_ascii=False)
```
`import json`이 파일 상단에 있는지 확인. 없으면 추가.
**테스트 불필요**: 폴백 경로 개선.

---

### F-3: `state_tracker_plots.py:922` — `aliases`가 None일 때 `in` 연산 TypeError

**파일**: `modules/domain/agents/state_tracker_plots.py:922`
**현상**: `info.get("aliases", set())` — 키가 존재하지만 값이 `None`이면 `.get()`이 None 반환 → `match in None` → `TypeError`
**코드**:
```python
if match in info.get("aliases", set()):
```
**수정**: `or set()` 추가로 None 방어:
```python
if match in (info.get("aliases") or set()):
```
**테스트**: aliases=None 케이스 추가 (1개).

---

## 실행 가이드 (Codex용)

- **총 21개 항목** — 모두 독립 실행 가능, 병렬 OK
- 각 항목 수정 후: `python -m ruff check <파일> && python -m ruff format <파일> && set PYTHONIOENCODING=utf-8 && pytest tests/ -q`
- 기대 결과: `1,716+ passed, 68 xfailed` (신규 테스트 포함 시 증가)
- **커밋하지 말 것** — 수정만 하고 검증만 수행

## 카테고리별 커밋 메시지 (나중에 사람이 커밋할 때 사용)

```
fix(sweep4-a): critical crash prevention — max() empty guard, future timeout, KeyError defense
fix(sweep4-b): logging tag corrections — 6x [ERROR] tag→[WARNING] to match warning level
fix(sweep4-c): thread safety — stats lock, deprecated get_event_loop, executor context manager
fix(sweep4-d): cache integrity — state_extractor invalidation, manuscript_cache rollback reset
refactor(sweep4-e): extract hardcoded thresholds — RepetitionGuard params, repetition_score, history size
fix(sweep4-f): type safety — injuries type unification, tactical_doc json fallback, aliases None guard
```

## 산출물 요약

| 카테고리 | 항목 수 | 신규 테스트 | 성격 |
|----------|---------|------------|------|
| A. 크래시 방지 | 4 | +3 | CRITICAL |
| B. 로깅 태그/레벨 | 5 | 0 | 관측성 |
| C. 스레드 안전성 | 3 | 0 | 안정성 |
| D. 캐시 무결성 | 2 | +2 | 상태 무결성 |
| E. 하드코딩 임계값 | 3 | 0 | 유지보수성 |
| F. 타입 안전성 | 3 | +1 | 방어적 |
| **합계** | **21** | **+6** | |

---

## 수정 대상 파일 목록

| 파일 | 항목 |
|------|------|
| `modules/core/adaptive_retry.py` | A-1 |
| `modules/core/pattern_tracker.py` | A-2 |
| `modules/core/stage2_preflight.py` | A-3 |
| `modules/validation/validation_orchestrator.py` | A-4, B-1, C-2, C-3, E-3 |
| `modules/validation/consistency_validator.py` | B-2 |
| `modules/validation/blocking_validator_entity_checks.py` | B-3 |
| `modules/validation/batch_validator.py` | B-4, C-1 |
| `modules/core/data_collector.py` | B-5 |
| `modules/domain/agents/state_extractor.py` | D-1 |
| `modules/core/stage2_orchestrator.py` | D-1 (호출부) |
| `modules/domain/agents/chief_writer.py` | D-2 |
| `main_a.py` | D-2 (호출부) |
| `modules/domain/agents/director_auditor.py` | E-1 |
| `modules/validation/pre_llm_validator.py` | E-2 |
| `config/settings/validation.yaml` | E-2 |
| `modules/domain/agents/analyst.py` | F-1, F-2 |
| `modules/domain/agents/state_tracker_plots.py` | F-3 |
