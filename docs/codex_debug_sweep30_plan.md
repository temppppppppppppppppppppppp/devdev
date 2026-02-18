# Debug Sweep 30 — 캐시 변이 + truthiness 트랩 + 로깅 크래시

## Context

Sweep 29(8건) 완료 후, 5-에이전트 병렬 탐색으로 새로운 패턴 집중 스윕:
shallow copy 변이, boolean truthiness 트랩, dict iteration 변이, 로깅 크래시, 캐시 일관성.
수동 코드 검증으로 **확인된 실제 버그 6건** 정리.

---

## A-1 (HIGH): `state_extractor.py:292,371-380` — `extract_cumulative_state`가 캐시된 dict 직접 변이

**파일**: `modules/domain/agents/state_extractor.py:292,371-380`

**문제**:
```python
# L292 — 캐시된 결과를 직접 참조 획득
current_state = self.extract_state(latest_arc)
# ↑ 캐시 히트 시 self._state_cache[key] 그대로 반환 (L216)

# L371-380 — 캐시된 dict를 직접 변이!
current_state["cumulative"] = {
    "all_acquired_items": list(set(all_acquired)),
    ...
}
current_state["entity_registry"] = {  # ← 원래 entity_registry 덮어씀!
    category: list(entities.values()) ...
}
```

**영향**:
1. `_state_cache`에 저장된 마지막 Arc의 `entity_registry`가 누적 버전으로 덮어써짐
2. 이후 `extract_state()` 단독 호출 시 누적 entity_registry가 반환됨 (개별 Arc 데이터 손실)
3. 재호출 시 `extract_cumulative_state` → L335-336에서 이미 변이된 캐시에서 entity 읽기 → 중복 entity 누적

**수정** — L292에서 shallow copy:
```python
current_state = dict(self.extract_state(latest_arc))
```

**테스트**: `extract_state` 캐시 결과가 `extract_cumulative_state` 호출 후에도 원본 유지 검증

---

## A-2 (MEDIUM): `ab_testing.py:168,207,213` — `if score:` truthiness 트랩 → score=0 통계 제외

**파일**: `modules/core/ab_testing.py:168,207,213`

**문제**:
```python
score = r["result"].get("score", 0)
if score:  # ← score=0이면 False → 통계에서 제외!
    scores.append(score)
```
- 3곳 동일 패턴: L168 (전체 집계), L207 (variant A), L213 (variant B)
- score=0인 결과가 A/B 테스트 통계에서 누락 → 평균 점수 왜곡

**수정** — 3곳:
```python
if score is not None:
    scores.append(score)
```

**참고**: `.get("score", 0)`의 기본값 0은 키 자체가 없을 때만 적용. 키가 있고 값이 None/0이면 그 값이 반환됨.

**테스트**: `r["result"] = {"score": 0}` 시 `scores`에 0이 포함되는지 검증

---

## A-3 (MEDIUM): `project_manager.py:509` — `new_hud.get(key) and ...` → achievement_rate=0 변경 추적 누락

**파일**: `modules/core/project_manager.py:509`

**문제**:
```python
for key in ["achievement_rate", "current_status", "realm"]:
    if new_hud.get(key) and new_hud.get(key) != old_hud.get(key):
        # ↑ achievement_rate=0이면 get() → 0 → falsy → and 단락 → 변경 미추적
        changes.append(f"{key}: {old_hud.get(key, 'N/A')} -> {new_hud[key]}")
```
- `achievement_rate`가 0으로 변경된 경우(예: 초기화, 리셋) UI에 표시되지 않음
- `current_status`나 `realm`이 빈 문자열로 변경된 경우도 동일

**수정**:
```python
if new_hud.get(key) is not None and new_hud.get(key) != old_hud.get(key):
```

**테스트**: `new_hud = {"achievement_rate": 0}`, `old_hud = {"achievement_rate": 50}` 시 changes에 포함 검증

---

## B-1 (LOW): `critic.py:604` — `if score:` → 점수 0 표시 누락

**파일**: `modules/domain/agents/critic.py:604`

**문제**:
```python
score = review_result.get("score")
if score:  # ← score=0이면 표시 안 됨
    lines.append(f"품질 점수: {score}/100")
```

**수정**:
```python
if score is not None:
```

---

## B-2 (LOW): `pre_llm_validator.py:304` — `.find() > 0` 센티넬 오류

**파일**: `modules/validation/pre_llm_validator.py:304`

**문제**:
```python
same_day_idx = manuscript.find("같은 날")
days_later_idx = manuscript.find("며칠 후")
if same_day_idx > 0 and days_later_idx > 0 and days_later_idx < same_day_idx:
    # ↑ > 0이면 위치 0에서 발견 시 미감지
    # .find() 미발견 시 -1 반환. 올바른 비교: != -1 또는 >= 0
```
- 원고 첫 문자가 "같은 날" 또는 "며칠 후"일 확률은 극히 낮지만, 의미상 오류

**수정**:
```python
if same_day_idx >= 0 and days_later_idx >= 0 and days_later_idx < same_day_idx:
```

---

## B-3 (LOW): `.get("key", "")[:N]` on None — LLM JSON null 값 시 TypeError

**파일 5곳**: `stage2_validation_pipeline.py`, `arc_corrector.py`, `unified_blueprint_validator.py`, `feedback_system.py`

**문제**:
```python
# LLM이 {"issue": null} 반환 시:
ci.get("issue", "?")  # → None (키가 존재하므로 기본값 미적용)
ci.get("issue", "?")[:80]  # → None[:80] → TypeError
```

**패턴**: `.get(key, default)` → 키가 **존재하고 값이 None**이면 default 무시하고 None 반환

**수정** — `or ""` 가드 추가 (가장 임팩트 큰 5곳만):
```python
# 패턴: (val.get("key", "") or "")[:N]
```

| 파일 | 라인 | 현재 | 수정 |
|------|------|------|------|
| `stage2_validation_pipeline.py` | 145 | `ci.get('issue', '?')[:80]` | `(ci.get('issue', '?') or '?')[:80]` |
| `stage2_validation_pipeline.py` | 342 | `i.get("message", "")[:30]` | `(i.get("message", "") or "")[:30]` |
| `arc_corrector.py` | 163 | `issue.get('message', '')[:50]` | `(issue.get('message', '') or '')[:50]` |
| `arc_corrector.py` | 178 | `correction_result.get('summary', '')[:50]` | `(correction_result.get('summary', '') or '')[:50]` |
| `arc_corrector.py` | 183 | `correction_result.get('reason', '')[:50]` | `(correction_result.get('reason', '') or '')[:50]` |
| `unified_blueprint_validator.py` | 258 | `director_reason[:50]` | `(director_reason or "")[:50]` |
| `feedback_system.py` | 204 | `v.get("description", "위반사항 수정")[:80]` | `(v.get("description", "위반사항 수정") or "위반사항 수정")[:80]` |
| `feedback_system.py` | 257 | `v.get("description", "")[:150]` | `(v.get("description", "") or "")[:150]` |

**테스트**: `{"issue": None}` → `.get("issue", "")[:80]` 대신 `or ""` 가드로 TypeError 방지 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/state_extractor.py` | 1줄 수정 (`dict()` 래핑) |
| A-2 | `modules/core/ab_testing.py` | 3줄 수정 (`is not None`) |
| A-3 | `modules/core/project_manager.py` | 1줄 수정 (`is not None`) |
| B-1 | `modules/domain/agents/critic.py` | 1줄 수정 (`is not None`) |
| B-2 | `modules/validation/pre_llm_validator.py` | 1줄 수정 (`>= 0`) |
| B-3 | `modules/core/stage2_validation_pipeline.py` | 2줄 수정 (`or ""`) |
| B-3 | `modules/domain/agents/arc_corrector.py` | 3줄 수정 (`or ""`) |
| B-3 | `modules/domain/agents/unified_blueprint_validator.py` | 1줄 수정 (`or ""`) |
| B-3 | `modules/core/feedback_system.py` | 2줄 수정 (`or ""`) |

**총 ~15줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| NPC merge shallow copy (`state_tracker_npc.py:525`) | ✗ 오탐 | `other`는 임시 StateTracker, merge 후 폐기. 공유 참조로 역방향 변이 경로 없음 |
| `director_auditor` validation_context 변이 | ✗ 설계 | 의도적 context 보강 — 호출자가 매번 새 dict 생성. 재사용 패턴 없음 |
| `world_state.get_state_dict()` shallow copy | ✗ LOW | `.copy()` 반환. "디버깅/대시보드용" 주석. 호출자가 nested 변이하는 코드 없음 |
| `lore_manager` 캐시 shallow 반환 | ✗ LOW | lore 데이터는 읽기 전용 소비. 호출자가 반환 리스트 변이하는 코드 없음 |
| `_item_timeline_cache` 프로젝트 전환 | ✗ 오탐 | `SovereignApp()`는 프로젝트당 단일 인스턴스. 세션 내 프로젝트 전환 없음 |
| `_cumulative_state_cache` 프로젝트 전환 | ✗ 오탐 | 동일 — 세션 내 전환 없음. arc_count 키 기반 무효화 정상 |
| `_narrative_summaries_cache` 프로젝트 전환 | ✗ 오탐 | 동일 — 세션 내 전환 없음 |
| `StateExtractor` 폴백 영구 캐시 | ✗ 설계 | 의도적 — LLM 실패 시 반복 재시도 방지. `invalidate_cache()` 존재 |
| dict mutation during iteration | ✗ 0건 | 전량 안전 (리스트 순회, copy 후 수정, 새 dict 생성) |
| `consensus_validator.py:397` `.get()[:N]` | ✗ 안전 | `if ci.get("evidence")` ternary 가드로 None 차단됨 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_sweep30.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Update (2026-02-18)

Status: completed for Sweep 30 scope.

Applied items:
- A-1 `modules/domain/agents/state_extractor.py`: cumulative state build now starts from a shallow copy (`dict(...)`) to avoid mutating cached arc state.
- A-2 `modules/core/ab_testing.py`: score collection now uses `if score is not None` in all three aggregation paths.
- A-3 `modules/core/project_manager.py`: HUD diff tracking now detects `0`/empty transitions by checking `is not None`.
- B-1 `modules/domain/agents/critic.py`: score output now includes zero scores.
- B-2 `modules/validation/pre_llm_validator.py`: `.find()` index checks updated from `> 0` to `>= 0`.
- B-3 None-safe slicing fixes:
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/domain/agents/arc_corrector.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/core/feedback_system.py`

Added tests:
- `tests/test_sweep30.py` (9 tests) covering zero-score handling, cache-mutation guard, and None-safe slicing guards.

Verification run:
- `python -m pytest tests/test_sweep30.py -q -x` -> `9 passed`
- `python -m pytest tests/test_feedback_system.py tests/test_stage2_validation_pipeline.py tests/test_pre_llm_validator.py -q -x` -> `80 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2037 passed, 68 xfailed, 1 warning`

Notes:
- Test output still includes existing interactive/log prints and a post-run traceback print from mocked ImportError path; pytest exit code is 0.
