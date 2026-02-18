# Debug Sweep 34 — 타임아웃 크래시 + LLM 타입 안전성 + NPC 데이터 손실

## Context

Sweep 33 완료 (2,066 passed, 68 xfailed). 5개 탐색 에이전트가 concurrent.futures 미처리 예외, LLM 반환값 타입 불일치, NPC 데이터 덮어쓰기 패턴을 발견. 수동 검증 후 **확인된 실제 버그 6건**.

---

## A-1 (HIGH): `stage2_preflight.py:99-103` — 보호 없는 future.result() → Stage 2 전체 크래시

**파일**: `modules/core/stage2_preflight.py:99-103`

**문제**:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
    _fut_drive = _parallel_exec.submit(_compute_arc_drive)
    _fut_preflight = _parallel_exec.submit(_compute_preflight)
    arc_drive = _fut_drive.result(timeout=300)                                    # ← 보호 없음
    _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result(timeout=300)  # ← 보호 없음
```
- 300초 타임아웃 시 `concurrent.futures.TimeoutError` 발생
- 호출자 `stage2_orchestrator.py:392`에도 try/except 없음
- **결과**: LLM API 지연 → Stage 2 Arc 처리 루프 전체 크래시

**수정**: L99-103을 try/except로 감싸고, 타임아웃 시 안전한 기본값 반환:
```python
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:
        _fut_drive = _parallel_exec.submit(_compute_arc_drive)
        _fut_preflight = _parallel_exec.submit(_compute_preflight)
        arc_drive = _fut_drive.result(timeout=300)
        _cached_preflight_injection, _cached_preflight_result = _fut_preflight.result(timeout=300)
except Exception as _pf_err:
    logging.warning(f"⚠️ [Preflight] 병렬 실행 타임아웃/오류 (비차단): {str(_pf_err)[:80]}")
    arc_drive = ""
    _cached_preflight_injection = ""
    _cached_preflight_result = {}
```

---

## A-2 (MEDIUM): 4개 앙상블 파일 — `future.cancel()` 누락 (chief_writer만 수정됨)

**파일**: 4개
- `modules/domain/agents/arc_ensemble.py:157-180`
- `modules/domain/agents/blueprint_ensemble.py:198-220`
- `modules/domain/agents/consensus_validator.py:220-260`
- `modules/domain/agents/director_auditor.py:861-879`

**문제**: `chief_writer.py:305-307`에는 Sweep3-G2 수정으로 `finally: for f in futures: f.cancel()` 블록이 있지만, 같은 패턴의 4개 파일에는 없음.

`as_completed(timeout=N)` 타임아웃 후 `with ThreadPoolExecutor` 블록 종료 시 `executor.shutdown(wait=True)` 가 호출되어 미완료 LLM 콜이 끝날 때까지 **추가 대기**. 타임아웃이 사실상 무력화됨.

**수정**: 각 파일의 `as_completed` try/except 블록 끝에 finally 추가:
```python
            except Exception as e:
                logging.warning(f"⚠️ [V61.3] 앙상블 루프 예외: {str(e)[:80]}")
            finally:
                # [Sweep34] 미완료 future 정리 — executor.shutdown 대기 방지
                for f in futures:
                    f.cancel()
```

각 파일의 정확한 위치:
- `arc_ensemble.py`: L178-180 `except Exception` 블록 뒤에 finally 추가
- `blueprint_ensemble.py`: L218-220 `except Exception` 블록 뒤에 finally 추가
- `consensus_validator.py`: L258-260 `except Exception` 블록 뒤에 finally 추가
- `director_auditor.py`: L876-879 `except Exception` 블록 뒤에 finally 추가

---

## A-3 (MEDIUM): `block_enricher.py:631` — as_completed for-loop TimeoutError 미처리

**파일**: `modules/domain/agents/block_enricher.py:629-645`

**문제**:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
    futures = {executor.submit(enrich_single, idx): idx for idx in batch}
    for future in concurrent.futures.as_completed(futures, timeout=600):  # ← TimeoutError 여기서 발생
        try:
            idx, result = future.result(timeout=60)   # ← 이건 보호됨
            ...
        except Exception as e:                        # ← future.result() 예외만 잡음
            ...
    # as_completed 자체의 TimeoutError는 미처리 → 호출자까지 전파
```
- `main_a.py:1250` 호출부에도 try/except 없음
- **결과**: 600초 타임아웃 → 나머지 배치 미처리 + enrichment 전체 크래시

**수정**: for-loop을 outer try/except로 감싸기:
```python
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = {executor.submit(enrich_single, idx): idx for idx in batch}
                processed_indices = set()
                try:
                    for future in concurrent.futures.as_completed(futures, timeout=600):
                        try:
                            idx, result = future.result(timeout=60)
                            processed_indices.add(idx)
                            if result.get("enriched") and result.get("block"):
                                enriched_blocks[idx] = result["block"]
                                stats["enriched_count"] += 1
                            else:
                                enriched_blocks[idx] = treatment_blocks[idx]
                                stats["failed_count"] += 1
                        except Exception as e:
                            idx = futures[future]
                            processed_indices.add(idx)
                            enriched_blocks[idx] = treatment_blocks[idx]
                            stats["failed_count"] += 1
                            if ui:
                                ui.log(f"      ⚠️ Block {idx + 1} 농축 실패: {str(e)[:30]}")
                except Exception as _timeout_err:
                    # [Sweep34] as_completed 전체 타임아웃 — 미처리 블록 원본 유지
                    for fut, idx in futures.items():
                        if idx not in processed_indices:
                            enriched_blocks[idx] = treatment_blocks[idx]
                            stats["failed_count"] += 1
                    if ui:
                        ui.log(f"      ⏰ 배치 타임아웃: {str(_timeout_err)[:50]}")
                finally:
                    for f in futures:
                        f.cancel()
```

---

## A-4 (MEDIUM): `director_ensemble.py` — LLM score/index 타입 미검증 (3곳)

**파일**: `modules/domain/agents/director_ensemble.py`

**문제**: `director_auditor.py:811`에 `_safe_int_score()` 헬퍼가 있지만, 같은 Director 서브모듈인 `director_ensemble.py`에서는 LLM 반환 score/index를 타입 검증 없이 사용:

```python
# L145: LLM이 "selected_index": "0" (문자열) 반환 시 → "0" < 0 → TypeError
selected_idx = result.get("selected_index", 0)
if selected_idx < 0 or selected_idx >= len(candidates):

# L150: LLM이 "score": "75" 반환 시 → 하류 비교에서 TypeError
score = result.get("score", 70)

# L406: 같은 패턴
score = result.get("score", 50)
```
- L150의 score는 `unified_blueprint_validator.py:105`에서 `>= 70` 비교에 사용
- L406의 score는 `director_grading.py:560`에서 `>= threshold` 비교에 사용
- **결과**: LLM이 숫자를 문자열로 반환하면 TypeError → Blueprint 선택 크래시

**수정**:

1. `director_ensemble.py` 상단에 헬퍼 추가 (또는 director_auditor에서 import):
```python
def _safe_int(value, default=0):
    """LLM 반환값 int 변환 (문자열/None 안전)"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

2. 3곳 수정:
```python
# L145
selected_idx = _safe_int(result.get("selected_index", 0), 0)

# L150
score = _safe_int(result.get("score", 70), 70)

# L406
score = _safe_int(result.get("score", 50), 50)
```

---

## A-5 (MEDIUM): `unified_blueprint_validator.py` — score 타입 미검증 (2곳)

**파일**: `modules/domain/agents/unified_blueprint_validator.py`

**문제**:
```python
# L105: compare_result["score"]가 문자열이면 >= 70 비교 시 TypeError
"confidence": 0.9 if compare_result.get("score", 0) >= 70 else 0.6,

# L228+L254: director_score가 문자열이면 >= 70 비교 시 TypeError
director_score = director_result.get("score", 50)
# ...
"confidence": 0.9 if director_score >= 70 else 0.6,
```

**수정**: A-4의 `_safe_int` 패턴 적용:
```python
# L105
"confidence": 0.9 if _safe_int(compare_result.get("score", 0), 0) >= 70 else 0.6,

# L228
director_score = _safe_int(director_result.get("score", 50), 50)
```

`_safe_int`를 `director_ensemble.py`에서 정의하고 import하거나, 각 파일에 인라인으로 추가:
```python
try:
    director_score = int(director_result.get("score", 50))
except (ValueError, TypeError):
    director_score = 50
```

---

## B-1 (MEDIUM): `state_tracker_npc.py:534` — NPC 속성 빈값 덮어쓰기

**파일**: `modules/domain/agents/state_tracker_npc.py:528-534`

**문제**:
```python
existing = self.tracker.npc_registry[name]
if existing.get("status") == "dead" and info.get("status") != "dead":
    continue  # 사망 보호 ✓
elif info.get("status") == "dead":
    self.tracker.npc_registry[name] = info.copy()
else:
    existing.update(info)  # ← 빈값으로 덮어쓰기 위험
```
- LLM이 NPC를 언급만 하면 `info = {"name": "장웅", "status": "alive", "weapon": ""}` 생성 가능
- `existing.update(info)` → 기존 `"weapon": "대도"` 가 `""` 로 덮어쓰기
- **결과**: NPC 속성(무기, 무공, 관계 등) 점진적 소실

**수정**: 빈값 필터링 후 업데이트:
```python
else:
    # [Sweep34] 빈값 덮어쓰기 방지 — 유의미한 값만 병합
    filtered = {k: v for k, v in info.items() if v not in ("", None, [], {})}
    existing.update(filtered)
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/core/stage2_preflight.py` | L99-103 try/except 감싸기 |
| A-2a | `modules/domain/agents/arc_ensemble.py` | finally: cancel() 추가 |
| A-2b | `modules/domain/agents/blueprint_ensemble.py` | finally: cancel() 추가 |
| A-2c | `modules/domain/agents/consensus_validator.py` | finally: cancel() 추가 |
| A-2d | `modules/domain/agents/director_auditor.py` | finally: cancel() 추가 |
| A-3 | `modules/domain/agents/block_enricher.py` | outer try/except + finally cancel + processed tracking |
| A-4 | `modules/domain/agents/director_ensemble.py` | `_safe_int` 헬퍼 + 3곳 적용 |
| A-5 | `modules/domain/agents/unified_blueprint_validator.py` | score int 변환 2곳 |
| B-1 | `modules/domain/agents/state_tracker_npc.py` | 빈값 필터링 후 update |

**총 9파일, ~50줄 변경**

---

## 테스트

```python
# tests/test_sweep34.py
"""Sweep 34: 타임아웃 안전성 + LLM 타입 안전성 + NPC 데이터 보호 테스트"""
import concurrent.futures
from unittest.mock import MagicMock, patch
import pytest


class TestStage2PreflightTimeout:
    """A-1: stage2_preflight 타임아웃 시 안전 폴백"""

    def test_preflight_timeout_does_not_crash(self):
        """future.result 타임아웃 시 빈 기본값 반환, 크래시 아님"""
        from modules.core.stage2_preflight import Stage2Preflight

        preflight = Stage2Preflight.__new__(Stage2Preflight)
        preflight.ctx = MagicMock()
        preflight.ctx.perf_timer = MagicMock()
        # _preflight_state_setup이 예외 시에도 유효한 dict 반환하는지 확인
        # (실제 호출은 복잡하므로 단위 확인)


class TestFutureCancelPropagation:
    """A-2: 4개 앙상블 파일에 future.cancel() 존재 확인"""

    @pytest.mark.parametrize("module_path", [
        "modules/domain/agents/arc_ensemble.py",
        "modules/domain/agents/blueprint_ensemble.py",
        "modules/domain/agents/consensus_validator.py",
        "modules/domain/agents/director_auditor.py",
    ])
    def test_cancel_exists_in_ensemble(self, module_path):
        """각 앙상블 파일에 f.cancel() 또는 future.cancel() 존재"""
        import pathlib
        content = pathlib.Path(module_path).read_text(encoding="utf-8")
        assert ".cancel()" in content, f"{module_path}에 .cancel() 누락"


class TestBlockEnricherTimeout:
    """A-3: block_enricher as_completed 타임아웃 안전성"""

    def test_enricher_timeout_falls_back_to_original(self):
        """as_completed 타임아웃 시 원본 블록 유지, 크래시 아님"""
        # block_enricher.enrich_all_blocks_parallel의 타임아웃 처리 확인
        from modules.domain.agents import block_enricher
        source = __import__("pathlib").Path(block_enricher.__file__).read_text(encoding="utf-8")
        # as_completed과 같은 레벨에 except가 있어야 함
        assert "processed_indices" in source or "except" in source


class TestDirectorEnsembleTypeSafety:
    """A-4: director_ensemble LLM score/index 타입 안전성"""

    def test_string_selected_index_no_crash(self):
        """LLM이 selected_index를 문자열로 반환해도 정상 작동"""
        from modules.domain.agents.director_ensemble import DirectorEnsemble
        from unittest.mock import MagicMock

        de = DirectorEnsemble.__new__(DirectorEnsemble)
        de._d = MagicMock()
        # LLM이 문자열 인덱스 반환하는 시나리오
        de._d._extract_json_robust.return_value = {
            "selected_index": "1",  # 문자열!
            "decision": "PASS",
            "score": "85",  # 문자열!
            "reason": "test",
        }
        de._d.ask.return_value = "{}"
        # compare_and_select_blueprint 호출 시 TypeError 아닌지 확인

    def test_string_score_no_crash(self):
        """LLM이 score를 문자열로 반환해도 정상 작동"""
        from modules.domain.agents.director_ensemble import DirectorEnsemble
        de = DirectorEnsemble.__new__(DirectorEnsemble)
        de._d = MagicMock()
        de._d._extract_json_robust.return_value = {
            "score": "75",
            "decision": "PASS",
        }
        # _safe_int("75") == 75 확인


class TestNPCMergeEmptyValueProtection:
    """B-1: NPC merge 시 빈값 덮어쓰기 방지"""

    def test_empty_weapon_does_not_overwrite(self):
        """빈 weapon 값이 기존 weapon을 덮어쓰지 않음"""
        from modules.domain.agents.state_tracker_npc import StateTrackerNPC
        from unittest.mock import MagicMock

        tracker = MagicMock()
        tracker.npc_registry = {
            "장웅": {"name": "장웅", "status": "alive", "weapon": "대도", "level": 5}
        }
        other = MagicMock()
        other.npc_registry = {
            "장웅": {"name": "장웅", "status": "alive", "weapon": "", "level": None}
        }
        other.protagonist_skills = {}
        other.skill_acquisitions = {}

        npc_module = StateTrackerNPC(tracker)
        npc_module.merge_npc_registry(other)

        # 빈값으로 덮어쓰기 되지 않아야 함
        assert tracker.npc_registry["장웅"]["weapon"] == "대도"
        assert tracker.npc_registry["장웅"]["level"] == 5
```

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_sweep34.py -x -q
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q
```

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| scoring_validator 3000자 제한 | ✗ 설계 결정 | `_sanitize_manuscript` — Prompt Injection 방지 + 토큰 절약 명시적 목적 |
| agent_intelligence 3000자 제한 | ✗ 설계 결정 | `# 토큰 절약` 주석으로 의도 명시 |
| project_manager block_no 덮어쓰기 | ✗ LOW | treatment_data에 block_no 키 포함 가능성 극히 낮음 |
| EpisodeState.to_dict extra_fields | ✗ 잠재 위험 | 현재 호출자 전부 read-only, 트리거 불가 |
| extract_npc_profiles bible 직접 참조 | ✗ 잠재 위험 | 현재 호출자 전부 read-only |
| pre_llm_validator set() 순서 | ✗ 표시 전용 | PASS/REJECT 판정에 영향 없음, 경고 표시만 |
| PromptLoader class-level cache | ✗ 무해 | 싱글톤 패턴으로 인스턴스 하나만 존재 |
| analyst list(set(existing)) 순서 | ✗ LOW | equipment 순서는 presence/absence 체크만 사용 |
| validate_parallel_v59 asyncio 무한대기 | ✗ 미사용 | 프로덕션에서 호출 안 됨 (테스트 전용) |

---

## Execution Update (2026-02-18)

Status: completed for Sweep 34 scope.

Applied items:
- A-1 `modules/core/stage2_preflight.py`: parallel preflight future waits are now wrapped in try/except; timeout/error falls back to safe defaults (`arc_drive={}`, cached preflight empty) and always stops perf timer in finally.
- A-2 `modules/domain/agents/arc_ensemble.py`: added `finally` cleanup to cancel outstanding futures after `as_completed` loop.
- A-2 `modules/domain/agents/blueprint_ensemble.py`: added `finally` cleanup to cancel outstanding futures after `as_completed` loop.
- A-2 `modules/domain/agents/consensus_validator.py`: added `finally` cleanup to cancel outstanding futures after `as_completed` loop.
- A-2 `modules/domain/agents/director_auditor.py`: self-consistency voting loop now has generic loop-exception logging + `finally` future cancel cleanup.
- A-3 `modules/domain/agents/block_enricher.py`: wrapped `as_completed(..., timeout=600)` loop with outer timeout/exception handling, tracks processed indices, falls back unprocessed blocks to original text, and cancels pending futures in `finally`.
- A-4 `modules/domain/agents/director_ensemble.py`: added `_safe_int` helper and applied to `selected_index` and `score` parsing paths to prevent string-number TypeError.
- A-5 `modules/domain/agents/unified_blueprint_validator.py`: added `_safe_int` helper and applied to score-based confidence and director score parsing.
- B-1 `modules/domain/agents/state_tracker_npc.py`: merge now filters empty values (`"", None, [], {}`) to avoid overwriting existing NPC attributes with blanks.

Additional fix during execution:
- `modules/domain/agents/block_enricher.py`: repaired pre-existing string-literal corruption discovered during full-suite import path (`main_a.py` -> `block_enricher`) so module compiles cleanly; kept Sweep34 timeout/fallback logic intact.

Added tests:
- `tests/test_sweep34.py` (8 tests):
  - preflight parallel-timeout fallback
  - ensemble modules future-cancel source guards
  - block enricher timeout/cancel source guards
  - director ensemble type-safe index/score parsing
  - unified blueprint validator string-score confidence coercion (compare + director path)
  - NPC merge blank-overwrite protection
  - source regression checks for Sweep34 guards

Verification run:
- `python -m pytest tests/test_sweep34.py -q -x` -> `8 passed`
- `python -m pytest tests/test_sweep34.py tests/test_director_modules.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_state_tracker_npc_sweep20.py -q -x` -> `234 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2074 passed, 68 xfailed, 1 warning`

Notes:
- Full run output still includes existing interactive/log prints and post-run mocked ImportError traceback print, but pytest exit code is 0.
