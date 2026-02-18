# Debug Sweep 26 — 크로스모듈 패턴 스윕: re.escape + off-by-one + json TypeError + 로거

## Context

Sweep 25(10건) 완료 후, **크로스모듈 패턴 스윕** — 개별 모듈이 아닌 코드베이스 전체에서 반복되는 5대 버그 패턴 탐색:
`json.loads` TypeError, error handler self-crash, `get_latest_episode_number` off-by-one, MasterBible unwrap, `re.escape` 누락 + 로거 불일치.
수동 코드 검증으로 **확인된 실제 버그: re.escape 11건 + off-by-one 2건 + json TypeError 1건 + 로거 9건** 정리.
error handler self-crash (0건, Sweep 21 완전 해결), MasterBible unwrap (0건, writer.py 유일)은 패턴 소진 확인.

---

## A-1 (HIGH): 7개 파일 — LLM/DB 출처 이름이 regex 패턴으로 직접 사용 → `re.error` 크래시

**문제**: NPC명, 아이템명, 빌런명, 스킬명 등 LLM/DB 출처 문자열이 `re.findall()` / `re.search()`에 직접 패턴으로 전달됨.
한국 웹소설 이름에 regex 메타문자 포함 가능: `파이어볼(화)`, `천극(天極)의 검`, `장무혁(독존)`, `A+급`

**영향 파일 및 수정**:

### A-1a: `modules/core/genre_guards/base_guard.py`
- **L506-512**: `superior_name` → `re.escape(superior_name)`
- **L628-649**: `npc_name` → `re.escape(npc_name)` (companion_patterns, fear_patterns)
- **L769-778**: `villain_name` → `re.escape(villain_name)` (villain_specific_response)

```python
# 수정 전 (L506 예시)
superior_delegation = [
    f"{superior_name}.*명",
    ...
]

# 수정 후
_esc = re.escape(superior_name)
superior_delegation = [
    f"{_esc}.*명",
    ...
]
```

### A-1b: `modules/validation/consistency_validator.py`
- **L364**: `item_name`, `forbidden_use` → `re.escape(item_name)`, `re.escape(forbidden_use)`
- **L469-488**: `npc_name` → `re.escape(npc_name)` (loyalty/betrayal/forgiveness patterns)
- **L497-507**: `npc_name` → `re.escape(npc_name)` (trigger_patterns)

### A-1c: `modules/domain/agents/manuscript_validator.py`
- **L352-358**: `npc` → `re.escape(npc)` (alive_patterns for dead NPC check)

### A-1d: `modules/core/character_voice_profiler.py`
- **L228-234**: `character_name` → `re.escape(character_name)` (dialogue extraction patterns)

### A-1e: `modules/validation/blocking_validator_consistency_checks.py`
- **L332-342**: `name` → `re.escape(name)` (ignorance_patterns)

### A-1f: `modules/validation/pre_llm_validator.py`
- **L368-369**: `correct_name` 슬라이스를 regex에 직접 삽입 — `re.escape()` 적용
```python
# 수정 전
pattern = correct_name[:i] + r"[가-힣]" + correct_name[i + 1 :]
# 수정 후
pattern = re.escape(correct_name[:i]) + r"[가-힣]" + re.escape(correct_name[i + 1 :])
```

**테스트**: `npc_name="장무혁(독존)"`, `item_name="천극(天極)의 검"` 등 메타문자 포함 이름에서 `re.error` 없이 정상 매칭 검증

---

## A-2 (HIGH): `project_manager.py:874` — `current_ep` off-by-one → 롤백 범위 1화 부족

**파일**: `modules/core/project_manager.py:874`

**문제**:
```python
current_ep = self.get_latest_episode_number()  # MAX+1 (e.g., 11 when episodes 1-10)
target_ep = max(origin_ep, current_ep - 3)     # max(origin_ep, 8) — 의도는 max(origin_ep, 7)
```
- `get_latest_episode_number()` = NEXT ep (MAX+1)
- `current_ep - 3` = MAX-2, 의도는 MAX-3 (3화 이전까지 롤백 허용)
- 결과: 롤백 범위가 의도보다 1화 부족
- Sweep 25 B-4에서 L872만 수정 — L874는 companion bug

**수정** — L874:
```python
current_ep = self.get_latest_episode_number() - 1  # 실제 최신 에피소드
```

**테스트**: 에피소드 1-10 존재 시 `auto_backtrack_v35("제 5화 오류", ...)` → `target_ep = max(5, 7) = 7` (3화 롤백 허용) 검증

---

## A-3 (MEDIUM): `narrative_diversity.py:359-362` — `latest_ep` off-by-one → 분석 윈도우 1화 부족

**파일**: `modules/core/narrative_diversity.py:359-362`

**문제**:
```python
latest_ep = self.context.db.get_latest_episode_number()  # MAX+1
start_ep = max(1, latest_ep - n + 1)  # 1화 늦은 시작
for ep_num in range(start_ep, latest_ep + 1):  # MAX+2까지 → 없는 에피소드 쿼리
```
- `n=5`, MAX=10: `start_ep = max(1, 11-5+1) = 7`, `range(7, 12)` = [7,8,9,10,11]
- 에피소드 11 미존재 → None 반환 → 실질 분석 4화 (의도는 5화)
- 의도된 범위: [6,7,8,9,10] = 5화

**수정** — L359:
```python
latest_ep = self.context.db.get_latest_episode_number() - 1  # 실제 최신 에피소드
```

**테스트**: 에피소드 1-10 + window=5 → 분석 대상이 정확히 5화(6-10)인지 검증

---

## B-1 (MEDIUM): `project_service.py:125,132` — `json.loads(NULL)` TypeError 미처리

**파일**: `modules/core/services/project_service.py:122-132`

**문제**:
```python
row = project.db.cursor.fetchone()
if row:
    past_data = json.loads(row["data"])          # L125 — NULL → TypeError!
    ...
    bible_data = json.loads(bible_row["data"])    # L132 — NULL → TypeError!
```
- `state_logs.data` / `anchors.data` 컬럼은 NULL 가능
- `json.loads(None)` → `TypeError`
- 외부 `try...except Exception` (L119)이 catch하지만 에러 메시지 오도 + 롤백 실패

**수정** — L125, L132에 가드 추가:
```python
past_data = json.loads(row["data"]) if row["data"] else {}
...
bible_data = json.loads(bible_row["data"]) if bible_row["data"] else {}
```

**테스트**: `state_logs.data=NULL` 상태에서 롤백 시 TypeError 없이 빈 dict 처리 검증

---

## C-1 (LOW): `stage4_orchestrator.py` — root logger 5건 → `_perf_logger` 전환

**파일**: `modules/core/stage4_orchestrator.py`

**문제**: L19에 `_perf_logger = logging.getLogger(__name__)` 정의했으나, 5곳에서 `logging.info/warning` 직접 호출

**수정 대상**:
- L495: `logging.info(...)` → `_perf_logger.info(...)`
- L670: `logging.info(...)` → `_perf_logger.info(...)`
- L672: `logging.warning(...)` → `_perf_logger.warning(...)`
- L714: `logging.warning(...)` → `_perf_logger.warning(...)`
- L736: `logging.warning(...)` → `_perf_logger.warning(...)`

**테스트**: 소스 코드에서 `logging.info` / `logging.warning` 직접 호출이 없는지 grep 검증

---

## C-2 (LOW): `retrospective_validator.py` — root logger 4건 → `_logger` 전환

**파일**: `modules/validation/retrospective_validator.py`

**문제**: L9에 `_logger = logging.getLogger(__name__)` 정의했으나, 4곳에서 `logging.warning` 직접 호출

**수정 대상**:
- L115: `logging.warning(...)` → `_logger.warning(...)`
- L170: `logging.warning(...)` → `_logger.warning(...)`
- L204: `logging.warning(...)` → `_logger.warning(...)`
- L239: `logging.warning(...)` → `_logger.warning(...)`

**테스트**: C-1과 동일 grep 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1a | `modules/core/genre_guards/base_guard.py` | ~12줄 수정 (re.escape 3개 메서드) |
| A-1b | `modules/validation/consistency_validator.py` | ~6줄 수정 (re.escape 3곳) |
| A-1c | `modules/domain/agents/manuscript_validator.py` | ~2줄 수정 (re.escape 1곳) |
| A-1d | `modules/core/character_voice_profiler.py` | ~2줄 수정 (re.escape 1곳) |
| A-1e | `modules/validation/blocking_validator_consistency_checks.py` | ~2줄 수정 (re.escape 1곳) |
| A-1f | `modules/validation/pre_llm_validator.py` | ~1줄 수정 (re.escape 슬라이스) |
| A-2 | `modules/core/project_manager.py` | 1줄 수정 (current_ep -1) |
| A-3 | `modules/core/narrative_diversity.py` | 1줄 수정 (latest_ep -1) |
| B-1 | `modules/core/services/project_service.py` | 2줄 수정 (truthiness 가드) |
| C-1 | `modules/core/stage4_orchestrator.py` | 5줄 수정 (logging→_perf_logger) |
| C-2 | `modules/validation/retrospective_validator.py` | 4줄 수정 (logging→_logger) |

**총 ~38줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| error handler self-crash 패턴 (전체) | ✗ 소진 | PromptBuilder(app=None)이 유일한 Optional app — Sweep 21에서 3건 전부 수정 완료 |
| MasterBible unwrap 패턴 (전체) | ✗ 소진 | writer.py:325가 유일 — 나머지 35곳 모두 정상 unwrap |
| `db_manager.py:870,1241,1305` json.loads | ✗ 오탐 | `if row["data"]` truthiness 가드가 None 방어 → json.loads 미도달 |
| `base_guard.py:386-389,491-499` title 패턴 | ✗ LOW | 개발자 제어 상수 — 메타문자 포함 없음 |
| `semantic_item_registry.py:143` modifier | ✗ 오탐 | 하드코딩 한글 상수 — 메타문자 없음 |
| `RESET.py:82,87` json.loads | ✗ 스크립트 | 유틸리티 스크립트, 프로덕션 외 |
| `tools/fix_future_items.py:45` json.loads | ✗ 스크립트 | 유틸리티 스크립트, 프로덕션 외 |
| `tools2/studio_dashboard.py` json.loads 3건 | ✗ 도구 | 대시보드 도구, bare except 미티게이션 |
| `tools/make_BP.py:44` json.loads | ✗ 도구 | 유틸리티 도구, 프로덕션 외 |
| `tools/db_porter.py:39,53` json.loads | ✗ 도구 | outer Exception 미티게이션 |
| `stage2_validation_pipeline.py:112` json.loads | ✗ 미티게이션 | outer `except Exception` catch (L116) |

---

## 패턴 소진 현황

| 패턴 | 상태 |
|------|------|
| error handler self-crash | ✅ **소진** — Sweep 21에서 완전 해결 |
| MasterBible unwrap 누락 | ✅ **소진** — writer.py 유일 (Sweep 25 B-3) |
| `json.loads` TypeError | ⚠️ 프로덕션 3건 수정 (Sweep 25 A-3/A-4 + 본건 B-1), tools 미수정 |
| `get_latest_episode_number` off-by-one | ⚠️ 3건 수정 (Sweep 25 B-4 + 본건 A-2/A-3) |
| `re.escape` 누락 | ⚠️ 12건 수정 (Sweep 25 B-2 + 본건 A-1), base_guard title은 LOW로 보류 |
| root logger 불일치 | ⚠️ 13건 수정 (Sweep 22 B-1/B-2 + 본건 C-1/C-2) |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_genre_guards.py tests/test_consistency_validator.py tests/test_pre_llm_validator.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- [x] A-1a `modules/core/genre_guards/base_guard.py` re.escape 적용
  - superior_name (authority delegation)
  - npc_name (unresolved conflict companion/fear patterns)
  - villain_name (villain response patterns)
- [x] A-1b `modules/validation/consistency_validator.py` re.escape 적용
  - item_name/forbidden_use (effect consistency)
  - npc_name (relation contradiction + trigger patterns)
- [x] A-1c `modules/domain/agents/manuscript_validator.py` dead NPC alive pattern에 re.escape 적용
- [x] A-1d `modules/core/character_voice_profiler.py` dialogue extraction pattern에 re.escape 적용
- [x] A-1e `modules/validation/blocking_validator_consistency_checks.py` ignorance pattern에 re.escape 적용
- [x] A-1f `modules/validation/pre_llm_validator.py` NPC 유사명 패턴 생성 시 `re.escape` 적용
- [x] A-2 `modules/core/project_manager.py` `auto_backtrack_v35` current_ep off-by-one 수정
  - `current_ep = self.get_latest_episode_number() - 1`
- [x] A-3 `modules/core/narrative_diversity.py` latest_ep off-by-one 수정
  - `latest_ep = self.context.db.get_latest_episode_number() - 1`
- [x] B-1 `modules/core/services/project_service.py` NULL JSON 방어
  - `json.loads(row["data"]) if row["data"] else {}`
  - `json.loads(bible_row["data"]) if bible_row["data"] else {}`
- [x] C-1 `modules/core/stage4_orchestrator.py` root logger -> `_perf_logger` 치환 (5건)
- [x] C-2 `modules/validation/retrospective_validator.py` root logger -> `_logger` 치환 (4건)

## Added Regression Tests

- `tests/test_sweep26.py` 추가 (12 tests)
  - regex metachar escape 회귀: base_guard, consistency_validator, manuscript_validator, character_voice_profiler, pre_llm_validator
  - off-by-one 회귀: project_manager, narrative_diversity
  - NULL JSON 회귀: project_service rollback path
  - logger usage 회귀: stage4_orchestrator, retrospective_validator

## Validation Results

- `python -m py_compile modules/core/genre_guards/base_guard.py modules/validation/consistency_validator.py modules/domain/agents/manuscript_validator.py modules/core/character_voice_profiler.py modules/validation/blocking_validator_consistency_checks.py modules/validation/pre_llm_validator.py modules/core/project_manager.py modules/core/narrative_diversity.py modules/core/services/project_service.py modules/core/stage4_orchestrator.py modules/validation/retrospective_validator.py tests/test_sweep26.py`
  - OK

- `python -m pytest tests/test_sweep26.py tests/test_genre_guard.py tests/test_consistency_validator.py tests/test_pre_llm_validator.py tests/test_project_service.py tests/test_rollback_npc.py -q -x`
  - 72 passed

- `python -m pytest tests/ -q -p no:capture`
  - 2007 passed, 68 xfailed, 1 warning

## Notes

- 테스트 종료 후 출력되는 faulthandler traceback은 기존 테스트 mock 시나리오의 출력이며, pytest 종료코드(0)에는 영향이 없습니다.
