# Debug Sweep 7차 — 런타임 안전성 + 데드코드 정리

> **목적**: 런타임 크래시 경로 차단, 예외 타입 정밀화, 데드코드 제거
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

## A. asyncio.gather 안전성 (CRITICAL — 2건)

> 단일 태스크 실패 시 전체 배치가 취소되는 문제. `return_exceptions=True` 추가.

### A-1: `modules/validation/batch_validator.py:81`

**현상**: `await asyncio.gather(*tasks)` — 개별 에피소드 검증 실패가 전체 배치를 취소.

**현재 코드**:
```python
results = await asyncio.gather(*tasks)
```

**수정**:
```python
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**추가**: 결과 처리 루프에서 Exception 인스턴스 핸들링 필요. L82 이후에:
```python
# gather 결과 중 Exception 인스턴스 처리
processed = []
for i, r in enumerate(results):
    if isinstance(r, Exception):
        logging.warning(
            "[Sweep7-A] batch validation failed for item %d: %s", i, r,
        )
        processed.append({"success": False, "error": str(r)})
    else:
        processed.append(r)
results = processed
```

**테스트**: 1건 — gather에서 단일 실패 시 나머지 결과 정상 반환 확인.

---

### A-2: `modules/validation/validation_orchestrator.py:1026-1028`

**현상**: `await asyncio.gather(consistency_task, scoring_task, advisory_task)` — 하나의 validator 실패가 전체를 취소.

**현재 코드 (L1026-1028)**:
```python
consistency_result, scoring_result, advisory_result = await asyncio.gather(
    consistency_task, scoring_task, advisory_task
)
```

**수정**:
```python
consistency_result, scoring_result, advisory_result = await asyncio.gather(
    consistency_task, scoring_task, advisory_task,
    return_exceptions=True,
)
```

**추가**: L1029 이후 결과 처리에서 Exception 체크:
```python
for idx, r in enumerate(results):
    if isinstance(r, Exception):
        task_names = ["consistency", "scoring", "advisory"]
        logging.warning(
            "[Sweep7-A] parallel validation %s failed: %s",
            task_names[idx], r,
        )
        results[idx] = None  # 해당 검증 결과 무효화
```

**테스트**: 1건 — scoring 실패 시 consistency/advisory 결과 정상 반환 확인.

---

## B. ZeroDivisionError 방지 (CRITICAL — 3건)

### B-1: `modules/core/adaptive_retry.py:720`

**현상**: `_agent_stats` 키가 존재하지만 모든 값이 0이면 `total = 0` → `v / total` ZeroDivisionError.

**현재 코드 (L714-720)**:
```python
total = sum(stats.values())
...
"weakness_distribution": {k: f"{v / total:.1%}" for k, v in sorted_types[:3]},
```

**수정**:
```python
total = sum(stats.values()) or 1
```

---

### B-2: `modules/core/pattern_tracker.py:726`

**현상**: `window_splits=0` 전달 시 가드 조건(`len < 0`)이 항상 False → `// 0` 크래시.

**현재 코드 (L722-726)**:
```python
def analyze_trends_windowed(self, manuscripts: list[str], window_splits: int = 3) -> dict:
    if len(manuscripts) < window_splits * 2:
        return {"status": "insufficient_data"}

    split_size = len(manuscripts) // window_splits
```

**수정 — L723에 가드 추가**:
```python
def analyze_trends_windowed(self, manuscripts: list[str], window_splits: int = 3) -> dict:
    if window_splits <= 0:
        return {"status": "invalid_window_splits"}
    if len(manuscripts) < window_splits * 2:
        return {"status": "insufficient_data"}

    split_size = len(manuscripts) // window_splits
```

---

### B-3: `modules/core/vec_memory.py:298-300`

**현상**: `max_results=0` 전달 시 `len(sorted_eps) > 0`이 True → `/ 0` 크래시.

**현재 코드**:
```python
if len(sorted_eps) > max_results:
    step = len(sorted_eps) / max_results
```

**수정**:
```python
max_results = max(1, max_results)
if len(sorted_eps) > max_results:
    step = len(sorted_eps) / max_results
```

---

## C. Dict 키 접근 안전성 (IMPORTANT — 4건)

### C-1: `modules/domain/agents/block_enricher.py:347`

**현상**: LLM 응답에서 `validation['issues']` 직접 접근 — `issues` 키 없으면 KeyError.

**수정**: `validation.get('issues', [])` 로 변경.

---

### C-2: `modules/core/data_collector.py:239`

**현상**: JSON 파일에서 로드한 `data["manuscript"]` 직접 접근 — 키 없으면 KeyError.

**수정**: `data.get("manuscript", "")` 로 변경.

---

### C-3: `modules/domain/agents/state_locked_arc_generator.py:450`

**현상**: `int(response.get("end_energy", start_state["energy"]))` — LLM이 "거의 소진" 같은 문자열 반환 시 ValueError.

**수정**:
```python
try:
    end_energy = int(response.get("end_energy", start_state.get("energy", 50)))
except (ValueError, TypeError):
    end_energy = start_state.get("energy", 50)
```

---

### C-4: `modules/core/foreshadow_tracker.py:446-447`

**현상**: `{int(k): v for k, v in data.items()}` — 외부 파일에서 로드한 dict 키 중 하나라도 비정수면 전체 로드 실패.

**수정**:
```python
result = {}
for k, v in data.items():
    try:
        result[int(k)] = v
    except (ValueError, TypeError):
        logging.warning("[Sweep7-C] foreshadow_tracker: skipping non-integer key: %s", k)
```

---

## D. 예외 타입 정밀화 (IMPORTANT — 5건)

### D-1: `modules/core/project_manager.py:542`

**현재**: `raise Exception(f"Bible 저장 실패로 에피소드 커밋 중단: {bible_err}")`
**수정**: `raise RuntimeError(f"Bible 저장 실패로 에피소드 커밋 중단: {bible_err}") from bible_err`

### D-2: `modules/core/project_manager.py:550`

**현재**: `raise Exception("SQLite Episode Factory 저장 실패")`
**수정**: `raise RuntimeError("SQLite Episode Factory 저장 실패") from factory_err`
- `factory_err`는 해당 except 블록의 변수명 확인 후 적용.

### D-3: `modules/domain/agents/analyst.py:763`

**현재**: `raise Exception("No Cache Found")`
**수정**: `raise LookupError("No Cache Found")`

### D-4: `modules/domain/agents/base_agent.py:65`

**현재**: `except Exception:`  (models.yaml 로드)
**수정**: `except (OSError, yaml.YAMLError):`
- 파일 상단에 `import yaml`이 이미 있는지 확인. 없으면 추가하지 말고 `except (OSError, Exception):` 유지 — yaml import 실패 가능성.

### D-5: `modules/domain/agents/base_agent.py:116`

**현재**: `except Exception:`  (system.yaml 로드)
**수정**: D-4와 동일 패턴. `except (OSError, yaml.YAMLError):` 또는 yaml import 상태에 따라 결정.

---

## E. 무한 성장 리스트 제한 (LOW — 2건)

### E-1: `modules/core/world_state.py:119`

**현상**: 주인공 스킬 리스트가 Arc마다 append → 300화 시 수백 개 무한 성장.

**수정 — append 후에 제한 추가**:
```python
# 기존 append 코드 아래에:
_MAX_SKILLS = 50
if len(skills_list) > _MAX_SKILLS:
    skills_list[:] = skills_list[-_MAX_SKILLS:]
```

- `skills_list` 변수명은 실제 코드에서 확인 후 적용.

### E-2: `modules/core/world_state.py:386`

**현상**: `active_plots` 리스트가 resolved 후에도 제거되지 않아 무한 성장.

**수정 — append 후에 제한 추가**:
```python
_MAX_ACTIVE_PLOTS = 30
if len(active_plots) > _MAX_ACTIVE_PLOTS:
    active_plots[:] = active_plots[-_MAX_ACTIVE_PLOTS:]
```

---

## F. 데드코드 제거 (9 파일, 2,315줄)

> 프로덕션에서 import되지 않는 모듈 삭제. 삭제 전 `grep -r "import <module>" modules/ main_a.py` 로 참조 0건 확인 필수.

| # | 파일 | 줄 수 | 사유 |
|---|------|-------|------|
| F-1 | `modules/core/db_adapter.py` | 82 | `db_manager.py`로 대체됨 |
| F-2 | `modules/domain/agents/ensemble_prompts.py` | 347 | prompt 문자열 어디서도 import 안 됨 |
| F-3 | `modules/core/genre_stage_prompts.py` | 480 | 장르별 stage 프롬프트, import 0건 |
| F-4 | `modules/core/graceful_degradation.py` | 512 | 우아한 열화 시스템, 미사용 |
| F-5 | `modules/core/model_cascading.py` | 218 | Flash/Pro 캐스케이드, 미참조 |
| F-6 | `modules/core/trend_booster.py` | 39 | V24 레거시, import 0건 |
| F-7 | `modules/core/seed_tracker.py` | 521 | 테스트 1개만 참조, 프로덕션 0 |
| F-8 | `modules/ui/console_interface.py` | 68 | Rich 콘솔 스텁, 미호출 |
| F-9 | `modules/domain/genre_manager.py` | 48 | strategy import 직접 수행, 클래스 미사용 |

**검증 방법** (각 파일 삭제 전):
```bash
# 예시: db_adapter.py
python -c "import re; import os; [print(f) for f in os.popen('git ls-files -- \"*.py\"').read().splitlines() if 'db_adapter' in open(f, encoding='utf-8').read() and f != 'modules/core/db_adapter.py']"
```
- 결과가 0건이면 삭제 안전.
- **1건이라도 나오면 삭제하지 말 것**.

**주의**: F-7(`seed_tracker.py`) 삭제 시 `tests/test_stage4_post_processor.py`에서 import 제거도 함께 수행.
**주의**: F-9(`genre_manager.py`) — Sweep 5에서 logging 변경이 적용됐으나, 프로덕션 참조가 0이면 삭제 가능.

**테스트**: 삭제 후 전체 테스트 통과 확인 (import 에러 발생 시 즉시 중단).

---

## G. 상수 중복 정리 (3건)

### G-1: `modules/core/stage2_validation_pipeline.py:673`

**현상**: `if sim >= 0.85:` — `semantic_plot_guard.py`의 `SIMILARITY_THRESHOLD = 0.85`와 중복.

**수정**:
```python
from modules.core.semantic_plot_guard import SIMILARITY_THRESHOLD
...
if sim >= SIMILARITY_THRESHOLD:
```

### G-2: `modules/core/constants.py` — 200K 컨텍스트 절삭 임계값 추가

**현상**: `200000` (200K 문자 컨텍스트 절삭)이 11개 파일에 하드코딩.

**수정 — constants.py에 추가**:
```python
class ContextLimits:
    """컨텍스트 크기 제한 상수"""
    MAX_CONTEXT_CHARS = 200_000  # 200K 문자 절삭 임계값
```

**후속**: 하드코딩된 11개 파일에서 `ContextLimits.MAX_CONTEXT_CHARS` 참조로 교체:
- `modules/core/stage2_finalizer.py:97-98`
- `modules/core/stage3_orchestrator.py:413-414`
- `modules/domain/agents/blueprint_ensemble.py:672`
- (나머지 파일은 grep으로 `200000` 검색하여 확인)

### G-3: 중복 `STATE_EXTRACTION_PROMPT` 통합

**현상**: `state_extractor.py:57` (3,181자)과 `state_locked_arc_generator.py:62` (434자)에 같은 이름의 프롬프트가 별도 정의.

**수정**: 이 항목은 **코드 리뷰만 수행**하고 수정하지 말 것. 두 프롬프트의 용도가 다를 수 있음 (하나는 범용 추출, 하나는 state-locked 전용). 용도 차이를 확인한 후 수동 결정 필요.
- 확인 사항: 각각 어디서 import되는지, 프롬프트 내용이 의도적으로 다른지.

---

## 실행 가이드 (Codex용)

- **총 26개 항목** — 모두 독립 실행 가능, 병렬 OK (단, F 카테고리는 순차 실행 권장)
- A: asyncio.gather 안전성 — 2건 (+2 테스트)
- B: ZeroDivisionError 방지 — 3건
- C: Dict/타입 안전성 — 4건
- D: 예외 타입 정밀화 — 5건
- E: 무한 성장 제한 — 2건
- F: 데드코드 삭제 — 9건 (삭제 전 참조 검증 필수)
- G: 상수 중복 — 2건 수정 + 1건 리뷰만
- 기대 결과: `1,730+ passed, 68 xfailed` (신규 테스트 포함)
- **커밋하지 말 것** — 수정만 하고 검증만 수행

### F 카테고리 실행 순서

1. 각 파일에 대해 참조 검증 스크립트 실행
2. 참조 0건인 파일만 삭제
3. 삭제 후 즉시 `pytest tests/ -q` 실행
4. 실패 시 해당 파일 `git checkout`으로 복원 후 다음 파일로 진행

---

## 카테고리별 커밋 메시지 (나중에 사람이 커밋할 때 사용)

```
fix(sweep7-a): add return_exceptions=True to asyncio.gather in batch_validator and validation_orchestrator
fix(sweep7-b): guard zero-division in adaptive_retry, pattern_tracker, vec_memory
fix(sweep7-c): safe dict access and type coercion for LLM/external data
refactor(sweep7-d): narrow exception types — RuntimeError, LookupError, OSError+YAMLError
fix(sweep7-e): cap unbounded skills and active_plots lists in world_state
chore(sweep7-f): remove 9 dead modules (2,315 lines)
refactor(sweep7-g): consolidate duplicate constants — similarity threshold, context limit
```

---

## 산출물 요약

| 카테고리 | 항목 수 | 파일 수 | 신규 테스트 | 성격 |
|----------|---------|---------|------------|------|
| A. asyncio.gather | 2 | 2 | +2 | 런타임 크래시 방지 |
| B. ZeroDivisionError | 3 | 3 | 0 | 런타임 크래시 방지 |
| C. Dict/타입 안전성 | 4 | 4 | 0 | 데이터 무결성 |
| D. 예외 타입 정밀화 | 5 | 3 | 0 | 코드 품질 |
| E. 무한 성장 제한 | 2 | 1 | 0 | 메모리 관리 |
| F. 데드코드 삭제 | 9 | 9 | 0 | 코드 위생 |
| G. 상수 중복 | 3 | 4+ | 0 | 유지보수성 |
| **합계** | **28** | **26+** | **+2** | |
