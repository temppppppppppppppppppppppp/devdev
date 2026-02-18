# Debug Sweep 25 — Guard 시그니처 불일치 + DB TypeError + 폴백 구조 오류

## Context

Sweep 24(2건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색/경량 모듈 전면 스윕:
db_manager + prompt_loader + semantic_plot_guard, validation 모듈 17종, genre_guards 전체, writer + blueprint_ensemble + project_manager, quality_dashboard + pass_rate_monitor + vec_memory + feedback_system.
수동 코드 검증으로 **확인된 실제 버그 10건** 정리.

---

## A-1 (HIGH): `work_guard.py:105` + `style_guard.py:81` — `check_unresolved_conflict` 시그니처 불일치 → TypeError 크래시

**파일**: `modules/core/genre_guards/work_guard.py:105-106`, `modules/core/genre_guards/style_guard.py:81-82`

**문제**:
```python
# WorkGuard L105 / StyleGuard L81 — 2인자
def check_unresolved_conflict(self, manuscript: str, context: dict[str, Any]) -> dict[str, Any]:
    return self._base.check_unresolved_conflict(manuscript, context)

# base_guard.py L565 — 3인자
def check_unresolved_conflict(self, manuscript: str, karma_matrix: dict[str, Any], ep_num: int) -> dict[str, Any]:

# 호출자 consistency_validator.py L188 — 3인자 전달
conflict_check = self.guard.check_unresolved_conflict(manuscript, karma_matrix, ep_num)
```
- 호출자는 3인자, 래퍼는 2인자 → `TypeError: takes 3 positional arguments but 4 were given`
- 명시적 메서드 정의가 `__getattr__` 위임을 오버라이드하므로 폴백 불가
- WorkGuard/StyleGuard 활성 + karma_matrix 비어있지 않을 때 consistency validation 크래시

**수정** — work_guard.py L105-106:
```python
def check_unresolved_conflict(self, manuscript: str, karma_matrix: dict[str, Any], ep_num: int) -> dict[str, Any]:
    return self._base.check_unresolved_conflict(manuscript, karma_matrix, ep_num)
```

**수정** — style_guard.py L81-82:
```python
def check_unresolved_conflict(self, manuscript: str, karma_matrix: dict[str, Any], ep_num: int) -> dict[str, Any]:
    return self._base.check_unresolved_conflict(manuscript, karma_matrix, ep_num)
```

**테스트**: WorkGuard 래핑 상태에서 `check_unresolved_conflict(manuscript, karma_matrix, ep_num)` 3인자 호출 시 TypeError 없이 정상 위임 검증

---

## A-2 (HIGH): `work_guard.py:114` + `style_guard.py:90` — `check_villain_response` 시그니처 불일치 → TypeError 크래시

**파일**: `modules/core/genre_guards/work_guard.py:114-115`, `modules/core/genre_guards/style_guard.py:90-91`

**문제**:
```python
# WorkGuard L114 / StyleGuard L90 — 2인자
def check_villain_response(self, manuscript: str, context: dict[str, Any]) -> dict[str, Any]:
    return self._base.check_villain_response(manuscript, context)

# base_guard.py L715-716 — 3인자
def check_villain_response(self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]) -> dict[str, Any]:

# 호출자 consistency_validator.py L212 — 3인자 전달
villain_check = self.guard.check_villain_response(manuscript, villain_context, recent_events)
```
- A-1과 동일 패턴

**수정** — work_guard.py L114-115:
```python
def check_villain_response(self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]) -> dict[str, Any]:
    return self._base.check_villain_response(manuscript, villain_context, recent_events)
```

**수정** — style_guard.py L90-91:
```python
def check_villain_response(self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]) -> dict[str, Any]:
    return self._base.check_villain_response(manuscript, villain_context, recent_events)
```

**테스트**: WorkGuard 래핑 상태에서 `check_villain_response(manuscript, villain_context, recent_events)` 3인자 호출 정상 위임 검증

---

## A-3 (HIGH): `db_manager.py:812` `load_all_anchors` — json.loads(None) TypeError 미처리

**파일**: `modules/core/db_manager.py:810-814`

**문제**:
```python
# L810-812 — json.JSONDecodeError만 catch
try:
    result[row["key"]] = json.loads(row["data"])
except json.JSONDecodeError as e:  # ← TypeError 미처리!

# L800-802 — 동일 파일 load_anchor()는 올바른 패턴
except (json.JSONDecodeError, TypeError) as e:  # ✅
```
- `anchors` 테이블의 `data` 컬럼은 NULL 가능
- `json.loads(None)` → `TypeError` (not `JSONDecodeError`)
- 하나의 NULL row로 전체 `load_all_anchors()` 크래시 → 모든 앵커 데이터 소실

**수정** — L812:
```python
except (json.JSONDecodeError, TypeError) as e:
```

**테스트**: `data=NULL` 행이 포함된 anchors 테이블에서 `load_all_anchors()` 크래시 없이 빈 dict 대체 검증

---

## A-4 (HIGH): `db_manager.py:856` `get_latest_state` — 동일 TypeError 미처리

**파일**: `modules/core/db_manager.py:854-857`

**문제**:
```python
# L854-856 — json.JSONDecodeError만 catch
try:
    return json.loads(row["data"])
except json.JSONDecodeError as e:  # ← TypeError 미처리!

# L869 — 동일 파일 load_state_log()는 올바른 패턴
result["data"] = json.loads(row["data"]) if row["data"] else {}  # ✅
```

**수정** — L856:
```python
except (json.JSONDecodeError, TypeError) as e:
```

**테스트**: `data=NULL` state_logs 행에서 `get_latest_state()` 크래시 없이 `{}` 반환 검증

---

## B-1 (MEDIUM): `fantasy_guard.py:197` `mana=None` → TypeError 크래시

**파일**: `modules/core/genre_guards/fantasy_guard.py:184-197`

**문제**:
```python
mana = current_state.get("mana", current_state.get("magic_power", 100))  # L184
if isinstance(mana, str):  # L185 — str 처리
    ...
# L197 — None 미처리
if mana <= 0:  # ← mana=None → TypeError: '<=' not supported
```
- `current_state`에 `{"mana": None}` 존재 시, `.get()`은 `None` 반환 (기본값 미사용)
- `isinstance(None, str)` = False → 통과
- `None <= 0` → TypeError

**수정** — L185 뒤에 추가:
```python
if isinstance(mana, str):
    ...  # 기존 str 처리
if mana is None:
    mana = 100
```

**테스트**: `current_state={"mana": None}` 입력 시 크래시 없이 기본 마나(100) 적용 검증

---

## B-2 (MEDIUM): `hunter_guard.py:282` + `base_guard.py:325` — 스킬명 regex escape 누락 → re.error 크래시

**파일**: `modules/core/genre_guards/hunter_guard.py:278-285`, `modules/core/genre_guards/base_guard.py:325`

**문제**:
```python
# hunter_guard.py L282 — skill_name을 pattern으로 직접 사용
actions.append({
    "pattern": skill_name,  # ← 예: "파이어볼(화)", "물리+마법"
    ...
})

# base_guard.py L325 — regex로 사용
matches = re.findall(pattern, manuscript)  # ← re.error if metachar in skill_name
```
- LLM/사용자 생성 스킬명에 regex 메타문자 포함 가능: `()`, `+`, `[]`, `*` 등
- `re.findall("파이어볼(화)", text)` → `re.error: unbalanced parenthesis`
- try/except 없이 크래시

**수정** — hunter_guard.py L282:
```python
"pattern": re.escape(skill_name),
```

**테스트**: `skill_cooldowns={"파이어볼(화)": 5}` 입력 시 `re.error` 없이 정상 매칭 검증

---

## B-3 (MEDIUM): `writer.py:325` MasterBible unwrap 누락 → NPC 빈도 항상 빈 dict

**파일**: `modules/domain/agents/writer.py:322-326`

**문제**:
```python
master_bible = getattr(self.context, "master_bible", None)
if not master_bible:
    return {}
assets = master_bible.get("AssetLibrary", {})  # ← MasterBible unwrap 누락!

# L83 — 동일 파일의 올바른 패턴
bible_root = master_bible.get("MasterBible", master_bible)
```
- `master_bible` 구조: `{"MasterBible": {"AssetLibrary": {...}, ...}}`
- `master_bible.get("AssetLibrary")` → `{}` (최상위에 해당 키 없음)
- 결과: `key_npcs` 항상 `[]` → NPC 빈도 기능 전면 무력화

**수정** — L324-325:
```python
if not master_bible:
    return {}
bible_root = master_bible.get("MasterBible", master_bible)
assets = bible_root.get("AssetLibrary", {})
```

**테스트**: MasterBible 래퍼 포함 bible에서 `_get_npc_frequency()` 호출 시 빈 dict 아닌 NPC 빈도 반환 검증

---

## B-4 (MEDIUM): `project_manager.py:872` auto_backtrack 기본값 → 롤백 no-op

**파일**: `modules/core/project_manager.py:871-875`

**문제**:
```python
match = re.search(r"(\d+)\s*화", error_report)
origin_ep = int(match.group(1)) if match else self.get_latest_episode_number()
#                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# get_latest_episode_number() = MAX+1 (e.g., 11 when episodes 1-10 exist)

current_ep = self.get_latest_episode_number()  # 11
target_ep = max(origin_ep, current_ep - 3)     # max(11, 8) = 11
# reset_project(11) → 에피소드 >= 11 삭제 → 0건 삭제 (최고 ep는 10)
```
- regex 미매칭 시 `origin_ep` = NEXT ep number = 존재하지 않는 에피소드
- `target_ep` = max(NEXT, NEXT-3) = NEXT → 삭제 대상 0건
- 롤백이 성공한 것처럼 보이지만 실제 데이터 변경 없음

**수정** — L872:
```python
origin_ep = int(match.group(1)) if match else max(1, self.get_latest_episode_number() - 1)
```

**테스트**: 에피소드 번호 없는 error_report에서 `auto_backtrack_v35` 호출 시 실제 에피소드 1건 이상 삭제 검증

---

## B-5 (MEDIUM): `vec_memory.py:172` embedding truthiness 가드 누락 → retry 대신 abort

**파일**: `modules/core/vec_memory.py:170-176`

**문제**:
```python
if hasattr(res, "embeddings") and res.embeddings:      # L170 ✅ truthiness 가드
    val = res.embeddings[0].values
elif hasattr(res, "embedding"):                         # L172 ❌ truthiness 없음
    val = res.embedding.values                          # ← None.values → AttributeError
```
- `res.embedding=None` 시 `AttributeError` → except 블록 → break (retry 안 함)
- L170은 `and res.embeddings` 가드 있음 — 패턴 불일치
- 정상 동작: `val = None` → `time.sleep(0.5)` → retry. 현재: 즉시 abort

**수정** — L172:
```python
elif hasattr(res, "embedding") and res.embedding:
```

**테스트**: `embed_content` 반환값의 `embedding=None` 시 retry 동작 (abort 아님) 검증

---

## B-6 (MEDIUM): `pass_rate_monitor.py:88` AttemptRecord 스키마 불일치 시 전체 기록 소실

**파일**: `modules/core/pass_rate_monitor.py:82-91`

**문제**:
```python
self.records = [AttemptRecord(**r) for r in data.get("records", [])]
# ↑ JSON에 미지 필드 존재 시 TypeError → except → self.records = []
```
- `AttemptRecord`는 14개 필드의 dataclass
- 새 필드 추가 후 이전 JSON 로드, 또는 코드 롤백 후 새 JSON 로드 시
- `TypeError: __init__() got an unexpected keyword argument` → 전체 기록 소실
- 통계, 추세, 경고, arc difficulty 분석 모두 빈 데이터로 리셋

**수정** — L88:
```python
fields = {f.name for f in AttemptRecord.__dataclass_fields__.values()}
self.records = [
    AttemptRecord(**{k: v for k, v in r.items() if k in fields})
    for r in data.get("records", [])
]
```

**테스트**: 미지 필드 포함 JSON에서 `_load_records()` 호출 시 기존 레코드 정상 로드 + 미지 필드 무시 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/core/genre_guards/work_guard.py` | 1줄 수정 (시그니처 + 인자) |
| A-1 | `modules/core/genre_guards/style_guard.py` | 1줄 수정 (시그니처 + 인자) |
| A-2 | `modules/core/genre_guards/work_guard.py` | 1줄 수정 (시그니처 + 인자) |
| A-2 | `modules/core/genre_guards/style_guard.py` | 1줄 수정 (시그니처 + 인자) |
| A-3 | `modules/core/db_manager.py` | 1줄 수정 (TypeError 추가) |
| A-4 | `modules/core/db_manager.py` | 1줄 수정 (TypeError 추가) |
| B-1 | `modules/core/genre_guards/fantasy_guard.py` | 2줄 추가 (None 가드) |
| B-2 | `modules/core/genre_guards/hunter_guard.py` | 1줄 수정 (re.escape) |
| B-3 | `modules/domain/agents/writer.py` | 1줄 추가 + 1줄 수정 (MasterBible unwrap) |
| B-4 | `modules/core/project_manager.py` | 1줄 수정 (기본값 -1) |
| B-5 | `modules/core/vec_memory.py` | 1줄 수정 (truthiness 가드) |
| B-6 | `modules/core/pass_rate_monitor.py` | 3줄 수정 (필드 필터링) |

**총 ~16줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `continuity_validator.py:845` personality_changes 인덱싱 역전 | ✗ 오탐 | `get_npc_history` ORDER BY id DESC (최신순) → `reversed()` = 오래된순 → `[-2]`/`[-1]` = 최근 2건. 정확함 |
| `validation_orchestrator.py:244` PreLLMValidator REJECT dead code | ✗ 설계 | `[V60.56] REJECT 권한 제거` — 대원칙 "Python은 수집만, LLM이 최종 판단" 준수 |
| `scoring_validator.py:638` float score (sensory_penalty=0.5) | ✗ LOW | 3.5 vs 3 차이. 크래시 없음, 경계 편차 극소 |
| `project_manager.py:871` dict error_report → re.search TypeError | ✗ 오탐 | 호출자 전부 f-string 전달. dict 전달 경로 없음 |
| `project_manager.py:774` force_sync_v25_dna None 반환 | ✗ LOW | truthiness 체크에서 None=False 동일 동작 |
| `project_manager.py:448` raw cursor 접근 | ✗ LOW | 단일 스레드 정상 동작. 시스템적 이슈 |
| `db_manager.py` 레거시 메서드 락 미사용 (30건) | ✗ 시스템적 | 파이프라인 순차 실행 + CPython GIL. 대규모 리팩토링 필요 |
| `vec_memory.py:81` check_same_thread=False 스레드 안전성 | ✗ 시스템적 | 실제 동시 접근 극저확률 |
| `quality_dashboard.py:210` hud_anomaly_rate 분모 불일치 | ✗ LOW | advisory 메트릭. 동작 영향 없음 |
| `feedback_system.py:55` 비-dict violation entries | ✗ LOW | 주요 호출자는 dict 형식 전달 |
| `prompt_loader.py` TOCTOU race | ✗ LOW | 중복 I/O만 발생, 데이터 무결성 영향 없음 |
| `semantic_plot_guard.py` | ✗ 없음 | 전 경로 안전 (None 가드 + 코사인 zero-norm 가드 + 폴백 정상) |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_genre_guards.py tests/test_db_manager.py tests/test_chief_writer.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- [x] A-1 `work_guard.py` / `style_guard.py` `check_unresolved_conflict` 3-arg 위임으로 수정
- [x] A-2 `work_guard.py` / `style_guard.py` `check_villain_response` 3-arg 위임으로 수정
- [x] A-3 `db_manager.py` `load_all_anchors`에서 `(json.JSONDecodeError, TypeError)` 처리
- [x] A-4 `db_manager.py` `get_latest_state`에서 `(json.JSONDecodeError, TypeError)` 처리
- [x] B-1 `fantasy_guard.py` `mana is None` 가드 추가
- [x] B-2 `hunter_guard.py` 스킬명 패턴 `re.escape(skill_name)` 적용
- [x] B-3 `writer.py` `_get_npc_frequency`에서 `MasterBible` unwrap 후 `AssetLibrary` 접근
- [x] B-4 `project_manager.py` `auto_backtrack_v35` 기본 `origin_ep=max(1, latest-1)`로 수정
- [x] B-5 `vec_memory.py` `res.embedding` truthiness 가드 추가
- [x] B-6 `pass_rate_monitor.py` `_load_records` unknown key 필터링 로드로 수정

## Added Regression Tests

- `tests/test_sweep25.py` 추가 (10 tests)
  - Guard wrapper 3-arg delegation
  - DB NULL JSON path 방어 (`anchors`, `state_logs`)
  - Fantasy mana None
  - Hunter regex meta 스킬명
  - Writer MasterBible unwrap
  - ProjectManager backtrack default origin
  - VecMemory embedding None retry
  - PassRateMonitor unknown key 무시

## Validation Results

- `python -m pytest tests/test_sweep25.py -q -x`
  - **10 passed**
- `python -m pytest tests/test_genre_guard.py tests/test_db_manager.py tests/test_chief_writer.py tests/test_rollback_npc.py tests/test_vec_memory.py -q -x`
  - **154 passed, 9 xfailed**
- `python -m pytest tests/ -q -p no:capture`
  - **1995 passed, 68 xfailed, 1 warning**

## Notes

- 실행 중 `db_manager.py`의 일부 깨진 문자열/문법 라인을 복구했습니다.
- 전체 테스트는 성공(Exit code 0)이며, 테스트 종료 후 출력되는 faulthandler traceback은 기존 테스트 시나리오(mocked ImportError) 출력으로 종료코드에는 영향이 없었습니다.
