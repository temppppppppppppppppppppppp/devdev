# Debug Sweep 32 — 스레드 안전성 + LLM 타입 불일치 + 경계 조건

## Context

Sweep 31(9건, 2,047 passed) 완료 후, 8-에이전트 병렬 탐색으로 새로운 패턴 집중 스윕:
스레드 안전성, LLM 필드 타입 불일치 (chained .get() on non-dict), json 직렬화, 경계 조건.
수동 코드 검증으로 **확인된 실제 버그 13건** 정리.

---

## A-1 (HIGH): `base_agent.py:1075-1081` — `_context_caches` 퇴거 로직 스레드 레이스

**파일**: `modules/domain/agents/base_agent.py:1075-1081`

**문제**:
```python
# L1070: 캐시 삽입
self._context_caches[cache_key] = {...}

# L1075-1081: 퇴거 (공유 class-level dict, 락 없음)
if len(self._context_caches) > self._CONTEXT_CACHE_MAX:
    sorted_keys = sorted(
        self._context_caches,  # ← dict 직접 이터레이션
        key=lambda k: self._context_caches[k].get("created_at", 0),
    )
    for old_key in sorted_keys[: len(sorted_keys) - self._CONTEXT_CACHE_MAX]:
        del self._context_caches[old_key]  # ← KeyError 가능 (다른 스레드가 먼저 삭제)
```

**영향**:
1. `chief_writer`의 `ThreadPoolExecutor(max_workers=3)` — 3개 워커가 동시에 `_get_or_create_context_cache` 호출
2. `sorted(self._context_caches)` 중 다른 스레드가 dict 수정 → `RuntimeError: dictionary changed size during iteration`
3. `del self._context_caches[old_key]` — 다른 스레드가 먼저 삭제 → `KeyError`
4. 예외가 ThreadPoolExecutor 워커에서 발생 → 해당 후보 원고 손실

**수정**:
```python
if len(self._context_caches) > self._CONTEXT_CACHE_MAX:
    try:
        sorted_keys = sorted(
            list(self._context_caches.keys()),  # 스냅샷
            key=lambda k: self._context_caches.get(k, {}).get("created_at", 0),
        )
        for old_key in sorted_keys[: len(sorted_keys) - self._CONTEXT_CACHE_MAX]:
            self._context_caches.pop(old_key, None)  # pop으로 KeyError 방지
    except RuntimeError:
        pass  # dict 변경 감지 시 퇴거 스킵 (다음 기회에 재시도)
```

**테스트**: 기존 테스트 통과 확인 (동작 동일, 방어 코드만 추가)

---

## A-2 (HIGH): `constraint_compiler.py:172,174` — chained `.get()` on non-dict LLM 값

**파일**: `modules/domain/agents/constraint_compiler.py:172,174`

**문제**:
```python
protagonist = state_extractor_result.get("protagonist_state", {})

return {
    "location": protagonist.get("location", {}).get("current", "알 수 없음"),
    # ↑ LLM이 "location": "서울" 반환 시 → str.get() → AttributeError
    "internal_energy": protagonist.get("internal_energy", {}).get("current_percent", 100),
    # ↑ LLM이 "internal_energy": 85 반환 시 → int.get() → AttributeError
}
```

**수정**:
```python
_loc = protagonist.get("location", {})
_energy = protagonist.get("internal_energy", {})

return {
    "location": _loc.get("current", "알 수 없음") if isinstance(_loc, dict) else str(_loc) if _loc else "알 수 없음",
    "injuries": protagonist.get("injuries", []),
    "internal_energy": _energy.get("current_percent", 100) if isinstance(_energy, dict) else (int(_energy) if isinstance(_energy, (int, float)) else 100),
    "equipment": inventory.get("current_items", []),
    "world_state": state_extractor_result.get("next_arc_constraints", {}).get("must_start_with", ""),
}
```

**테스트**: `protagonist = {"location": "서울", "internal_energy": 85}` → AttributeError 없이 정상 추출 검증

---

## A-3 (HIGH): `state_extractor.py:408-420,499-503` — LLM 필드 타입 불일치 3곳

**파일**: `modules/domain/agents/state_extractor.py`

**문제 1** (L408-413): `format_state_lock_prompt`
```python
injuries = protagonist.get("injuries", [])
if injuries:
    for inj in injuries:  # ← "골절" (str) → 문자 순회 → inj.get() → AttributeError
        lines.append(f"   - {inj.get('name', '?')}: ...")
```

**문제 2** (L418-420):
```python
energy = protagonist.get("internal_energy", {})
lines.append(f"   - 내공: {energy.get('current_percent', 100)}%")
# ← energy=85 (int) → int.get() → AttributeError
```

**문제 3** (L499-503): `_validate_and_fix_result`
```python
injuries = ps.get("injuries", [])
energy = ps.get("internal_energy", {})
recovery_needed = bool(injuries) or energy.get("current_percent", 100) < 50
min_days = max([inj.get("recovery_days", 0) for inj in injuries] + [0])
# ← 동일 패턴
```

**수정** — 3곳 모두 isinstance 가드:
```python
# L408
injuries = protagonist.get("injuries", [])
if not isinstance(injuries, list):
    injuries = []

# L418
energy = protagonist.get("internal_energy", {})
if not isinstance(energy, dict):
    energy = {"current_percent": int(energy) if isinstance(energy, (int, float)) else 100}

# L499-500 동일 패턴
```

**테스트**: `protagonist = {"injuries": "골절", "internal_energy": 85}` → 크래시 없이 처리 검증

---

## A-4 (MEDIUM): `block_enricher.py:631,633` — `future.result()` timeout 누락

**파일**: `modules/domain/agents/block_enricher.py:631,633`

**문제**:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
    futures = {executor.submit(enrich_single, idx): idx for idx in batch}
    for future in concurrent.futures.as_completed(futures):  # ← timeout 없음
        try:
            idx, result = future.result()  # ← timeout 없음
```

- 코드베이스의 다른 모든 ThreadPoolExecutor 사용처는 `as_completed(timeout=600)` + `future.result(timeout=60)` 사용
- 이 곳만 유일하게 timeout 없음 → LLM 호출 행 시 무한 대기

**수정**:
```python
for future in concurrent.futures.as_completed(futures, timeout=600):
    try:
        idx, result = future.result(timeout=60)
```

---

## A-5 (MEDIUM): `arc_draft_validator.py:231-240` — `.append()` on non-list (비일관 가드)

**파일**: `modules/domain/agents/arc_draft_validator.py:231,240`

**문제**:
```python
# L210-211 (prev_arcs): isinstance 가드 ✓
items = prev_arc.get("state_constraints", {}).get("items_acquired", [])
if isinstance(items, list):  # ← 가드 있음
    all_acquired.update(items)

# L231,240 (current arc): isinstance 가드 ✗
current_items = arc.get("state_constraints", {}).get("items_acquired", [])
# ...
current_items.append(item)  # ← str이면 AttributeError
```

- 동일 파일 L210에 `isinstance(items, list)` 가드가 있으나 L231에는 없음 (비일관)
- L331 `current_grants` 에도 isinstance 가드 있음

**수정**:
```python
# L231
current_items = arc.get("state_constraints", {}).get("items_acquired", [])
if not isinstance(current_items, list):
    current_items = [current_items] if isinstance(current_items, str) else []
```

---

## A-6 (MEDIUM): `director_auditor.py:493` — `assess_character_logic()` list 반환 시 `.get()` 크래시

**파일**: `modules/domain/agents/director_auditor.py:174-175,493`

**문제**:
```python
# L174-175: assess_character_logic() — bare _extract_json_robust 반환
response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
return self._d._extract_json_robust(response)
# ↑ LLM이 [{...}] 반환 시 list 반환

# L493: 호출자 — isinstance 가드 없음
char_logic_result = self.assess_character_logic(...)
if char_logic_result.get("decision") == "REJECT":  # ← list.get() → AttributeError
```

**영향**: `audit_manuscript` 내부에서 모든 원고에 대해 실행됨. 호출자(`unified_blueprint_validator.py:262`, `ab_testing.py:79`)에 `except Exception` 있어 크래시는 방지되나, 불필요한 REJECT + retry 발생.

**수정**:
```python
char_logic_result = self.assess_character_logic(...)
if not isinstance(char_logic_result, dict):
    char_logic_result = char_logic_result[0] if isinstance(char_logic_result, list) and char_logic_result else {}
```

---

## A-7 (MEDIUM): `continuity_manuscript.py:430,850` — `scene_breakdown.items()` without isinstance 가드

**파일**: `modules/domain/agents/continuity_manuscript.py:430,850`

**문제 1** (L428-430): `_manuscript_python_precheck`
```python
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown:
    core_scenes = [k for k, v in scene_breakdown.items() if "[Core]" in str(v)]
    # ↑ scene_breakdown이 list면 → AttributeError
```

**문제 2** (L832-850): `_check_blueprint_only`
```python
scene_breakdown = blueprint.get("scene_breakdown", {})
if not scene_breakdown:
    return {...}  # 빈 list는 falsy → 여기서 반환. 비어있지 않은 list는 통과
for scene_key, scene_desc in scene_breakdown.items():  # ← list.items() → AttributeError
```

**참고**: `director_continuity.py:241`에서 `scene_breakdown`이 list일 때 변환 로직 존재 → LLM이 list 반환하는 실제 케이스 확인됨.

**수정** — 2곳:
```python
# L428
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown and isinstance(scene_breakdown, dict):
    core_scenes = [k for k, v in scene_breakdown.items() if "[Core]" in str(v)]

# L832
scene_breakdown = blueprint.get("scene_breakdown", {})
if not scene_breakdown or not isinstance(scene_breakdown, dict):
    return {...}
```

---

## A-8 (MEDIUM): `stage2_finalizer.py:347` — `npc_status.items()` without isinstance 가드

**파일**: `modules/core/stage2_finalizer.py:343-349`

**문제**:
```python
if _as.get("npc_status"):
    _parts.append(
        "NPC: "
        + ", ".join(
            f"{n}({v.get('status', '')})" for n, v in _as["npc_status"].items()
            # ↑ npc_status가 list이면 → AttributeError
        )
    )
```

- `_as`는 `load_v20_anchor(f"arc_summary_{_ai}")` — DB 저장 LLM 데이터
- LLM이 npc_status를 list로 반환 가능: `[{"name": "NPC1", "status": "alive"}, ...]`
- 10 Arc마다 volume summary 트리거 시에만 실행 → 발생 빈도 LOW
- L331 `except Exception` 내부 → 크래시는 방지되나 volume summary 생성 실패

**수정**:
```python
if _as.get("npc_status") and isinstance(_as["npc_status"], dict):
```

---

## B-1 (MEDIUM): `blocking_validator_scene_checks.py:59` — `.items()` on non-dict (비일관 가드)

**파일**: `modules/validation/blocking_validator_scene_checks.py:59`

**문제**:
```python
# L47-59: isinstance 가드 없음
scene_breakdown = blueprint.get("scene_breakdown", {})
if not scene_breakdown:
    return {"check": "required_scenes", "passed": True}
for scene_name, scene_desc in scene_breakdown.items():  # ← list면 AttributeError

# L98-99: isinstance 가드 있음 ✓
if scene_breakdown and isinstance(scene_breakdown, dict):
    scene_count = len(scene_breakdown)
```

**수정**:
```python
if not scene_breakdown or not isinstance(scene_breakdown, dict):
    return {"check": "required_scenes", "passed": True}
```

---

## B-2 (MEDIUM): `preflight_checker.py:454-461` — non-dict `.get()` + non-string `join()`

**파일**: `modules/domain/agents/preflight_checker.py:454-461`

**문제 1** (L454-455):
```python
status = world.get("protagonist_status", {})
if status.get("injuries") and status["injuries"] != "없음":
# ← LLM이 "protagonist_status": "부상 상태" 반환 시 → str.get() → AttributeError
```

**문제 2** (L460-461):
```python
inventory = preflight_result.get("timeline_analysis", {}).get("current_inventory", [])
if inventory:
    lines.append(f"📦 소지품: {', '.join(inventory[:10])}")
    # ← inventory가 [{"item": "검"}] (dict 리스트) → TypeError
```

**수정**:
```python
# L454
status = world.get("protagonist_status", {})
if not isinstance(status, dict):
    status = {}

# L460-461
if inventory:
    lines.append(f"📦 소지품: {', '.join(str(i) for i in inventory[:10])}")
```

---

## B-3 (LOW): `data_collector.py:125,165` — `except OSError` → TypeError 미포착

**파일**: `modules/core/data_collector.py:125,165`

**문제**:
```python
try:
    with open(temp_filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
except OSError as e:  # ← TypeError 미포착
```

- `data`에 `validation_result`, `validation_context` (외부 dict) 포함
- 비직렬화 타입(Counter, set 등) 포함 시 TypeError → 미포착 → .tmp 파일 잔류

**수정** — 2곳:
```python
except (OSError, TypeError) as e:
```

---

## B-4 (LOW): `pacing_analyzer.py:164` — 죽은 else 분기

**파일**: `modules/core/pacing_analyzer.py:164`

**문제**:
```python
total_breaks = scene_breaks + time_skips  # 항상 >= 0 (regex match count)
avg_scene_len = len(manuscript) / (total_breaks + 1) if total_breaks >= 0 else len(manuscript)
# ↑ total_breaks >= 0 는 항상 True → else 분기 도달 불가
# 의도: total_breaks > 0 (장면 전환이 있을 때만 분할 계산)
```

- `total_breaks == 0` 일 때 `len(manuscript) / 1 == len(manuscript)` → 결과 동일 (우연)
- 하지만 의미상 `> 0` 이 정확

**수정**:
```python
avg_scene_len = len(manuscript) / (total_breaks + 1) if total_breaks > 0 else len(manuscript)
```

---

## B-5 (LOW): `arc_draft_validator.py:707-715` — non-list iteration

**파일**: `modules/domain/agents/arc_draft_validator.py:707-715`

**문제**:
```python
items_acquired = arc.get("state_constraints", {}).get("items_acquired", [])
for forbidden in forbidden_items:
    for item in items_acquired:  # ← str이면 문자 순회 → 의미 없는 비교
```

**수정**:
```python
items_acquired = arc.get("state_constraints", {}).get("items_acquired", [])
if not isinstance(items_acquired, list):
    items_acquired = []
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/base_agent.py` | ~5줄 수정 (list 스냅샷 + pop + RuntimeError 방어) |
| A-2 | `modules/domain/agents/constraint_compiler.py` | ~4줄 수정 (isinstance 가드 2곳) |
| A-3 | `modules/domain/agents/state_extractor.py` | ~6줄 수정 (isinstance 가드 3곳) |
| A-4 | `modules/domain/agents/block_enricher.py` | 2줄 수정 (timeout 추가) |
| A-5 | `modules/domain/agents/arc_draft_validator.py` | 2줄 수정 (isinstance 가드) |
| A-6 | `modules/domain/agents/director_auditor.py` | 2줄 수정 (isinstance + list unwrap) |
| A-7 | `modules/domain/agents/continuity_manuscript.py` | 2줄 수정 (isinstance 가드 2곳) |
| A-8 | `modules/core/stage2_finalizer.py` | 1줄 수정 (isinstance 가드) |
| B-1 | `modules/validation/blocking_validator_scene_checks.py` | 1줄 수정 (isinstance 가드) |
| B-2 | `modules/domain/agents/preflight_checker.py` | 3줄 수정 (isinstance + str() 래핑) |
| B-3 | `modules/core/data_collector.py` | 2줄 수정 (except 확장) |
| B-4 | `modules/core/pacing_analyzer.py` | 1줄 수정 (`>= 0` → `> 0`) |
| B-5 | `modules/domain/agents/arc_draft_validator.py` | 2줄 수정 (isinstance 가드) |

**총 ~33줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `.format()` + json.dumps → ValueError | ✗ 오탐 | `.format()` 값은 재파싱 안 됨. 템플릿 내 `{{` 이 `{` 변환은 Python 표준 동작으로 정상 |
| chief_writer/four_phase/three_phase `.format()` | ✗ 잠재 | Sweep 28에서 확인 — 현재 YAML에 `{{` 없음. 동작 정상 |
| consistency_validator.py re.error 미가드 | ✗ 오탐 | 패턴 모두 `re.escape()` 사용 + 하드코딩 — 안전 |
| stage4_post_processor.py `_sat_tag['primary_tag']` KeyError | ✗ 오탐 | L413 `except Exception` 블록 내 — KeyError 포착됨 |
| `agents["director"]` 직접 구독 | ✗ 오탐 | director는 필수 에이전트, 항상 존재 |
| `_quota_exhausted_models` 스레드 안전성 | ✗ 설계 | CPython GIL로 개별 dict 연산 atomic. read-check-write 비원자이나 최악 시 1회 추가 API 실패뿐 |
| `vec_memory.__del__` 셧다운 위험 | ✗ LOW | `except Exception: pass` 로 일반 케이스 억제. 셧다운 시에만 발생 가능 |
| `prompt_optimizer.py:346` sorted KeyError | ✗ 죽은 코드 | `MetaLearner` 클래스 어디에도 인스턴스화 안 됨 |
| `DataCollector` 메인 파이프라인 미사용 | ✗ LOW | `main_a.py`에서 미사용, tools2/ 전용. B-3으로 LOW 등급 포함 |
| fantasy_guard.py:192 잘못된 폴백 | ✗ LOW | "고갈","없음" 등 명시적 리스트로 주요 케이스 처리. "거의 없음" 등 극히 드문 엣지 케이스 |
| `state_tracker_npc.py:1826` 괄호 누락 | ✗ 스타일 | Python `and > or` 우선순위로 의미 정확. 가독성 이슈만 |
| 모든 retry 루프 | ✗ 0건 | 전량 break/return 정상 |
| 모든 next() 호출 | ✗ 0건 | 전량 default 파라미터 또는 try/except |
| 모든 os.path.join | ✗ 0건 | None 유입 경로 없음 |
| `not x == y` 연산자 우선순위 | ✗ 0건 | 전량 정상 |
| `== None` 비교 | ✗ 0건 | 전량 `is None` 사용 |
| `block_enricher.py:344,366` list 반환 | ✗ 오탐 | L332 `except Exception` 블록 내 — 폴백 처리 |
| `reference_anchor.py:114` list 반환 | ✗ 오탐 | L122 `except Exception` → `return []` 폴백 |
| `analyst.py:1173` list assignment | ✗ 오탐 | L1180 `except Exception` → raw_block 폴백 |
| `critic.py:554` list `.get()` | ✗ 오탐 | L565 `except Exception` → `_default_review_result()` 폴백 |
| `state_extractor.py:462` list assignment | ✗ 오탐 | L246 `except Exception` → `_fallback_extraction()` |
| `state_locked_arc_generator.py:449` list `.get()` | ✗ 오탐 | L462 `except Exception` → 안전 폴백 |
| `preflight_checker.py:194` join on dicts | ✗ LOW | 표시 전용, 호출자 except 있음 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_sweep32.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Update (2026-02-18)

Status: completed for Sweep 32 scope.

Applied items:
- A-1 `modules/domain/agents/base_agent.py`: context cache eviction now uses key snapshot + `pop(..., None)` and guards `RuntimeError` for concurrent mutation.
- A-2 `modules/domain/agents/constraint_compiler.py`: `_extract_current_state` now tolerates non-dict `protagonist_state` fields (`location`, `internal_energy`) and non-dict inventory.
- A-3 `modules/domain/agents/state_extractor.py`: type guards added for `injuries`/`internal_energy` in both state-lock prompt formatting and `next_arc_constraints` synthesis.
- A-4 `modules/domain/agents/block_enricher.py`: futures loop now has `as_completed(..., timeout=600)` and `future.result(timeout=60)`.
- A-5 `modules/domain/agents/arc_draft_validator.py`: `items_acquired`/`current_items` are normalized to list before append/iteration.
- A-6 `modules/domain/agents/director_auditor.py`: character-logic result now unwraps/normalizes non-dict returns before `.get()` access.
- A-7 `modules/domain/agents/continuity_manuscript.py`: `scene_breakdown` access guarded with `isinstance(..., dict)` in two paths.
- A-8 `modules/core/stage2_finalizer.py`: `npc_status.items()` path now guarded by dict type check.
- B-1 `modules/validation/blocking_validator_scene_checks.py`: required scene check now early-returns unless `scene_breakdown` is dict.
- B-2 `modules/domain/agents/preflight_checker.py`: protagonist status type-normalized to dict; inventory join now string-coerces elements.
- B-3 `modules/core/data_collector.py`: atomic write handlers now catch `(OSError, TypeError)`.
- B-4 `modules/core/pacing_analyzer.py`: branch condition fixed from `>= 0` to `> 0`.
- B-5 `modules/domain/agents/arc_draft_validator.py`: forbidden-item check path now guards non-list `items_acquired`.

Added tests:
- `tests/test_sweep32.py` (12 tests): shape mismatch guards, timeout/eviction protections, non-list/non-dict robustness, and source regression checks.

Verification run:
- `python -m pytest tests/test_sweep32.py -q -x` -> `12 passed`
- `python -m pytest tests/test_director_modules.py tests/test_continuity_modules.py tests/test_stage2_pipeline.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_validation_pipeline.py tests/test_stage4_interview_round.py -q -x` -> `303 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2059 passed, 68 xfailed, 1 warning`

Notes:
- 기존과 동일하게 테스트 출력에는 interactive/log print와 post-run mocked ImportError traceback print가 포함되지만, pytest exit code는 0입니다.
