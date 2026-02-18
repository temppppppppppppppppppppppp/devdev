# Debug Sweep 13 — 교차 커밋 + 심층 분석 버그 수정

## Execution Status (2026-02-17)

- A-1 completed: Stage 4 patch fallback now records `generation_method="ensemble"`.
- A-2 completed: `get_stage_stats()` now uses consistent `(episode, arc)` grouping key.
- A-3 completed: `detect_director_bias()` now uses numeric-score denominator for both `avg_score` and `pass_rate`.
- B-1 completed: energy derived from `internal_energy_loss` is now clamped to `[0, 100]`.
- Tests added:
  - `tests/test_stage4_interview_round.py`: patch fallback records `ensemble`.
  - `tests/test_director_bias.py`: non-numeric score records are excluded from denominator.
  - `tests/test_feedback_system.py`: negative loss does not exceed `100%` energy.
- Verification:
  - `pytest -q tests/test_stage4_interview_round.py tests/test_arc_difficulty.py tests/test_director_bias.py tests/test_quality_trend.py tests/test_feedback_system.py` -> `90 passed`
  - Expanded regression suite (Phase 1-6 set) -> `263 passed`

## Context

Sweep 11(4건) + Sweep 12(4건) 완료 후, 5-에이전트 병렬 심층 탐색 실시.
범위: ops-quality(`af32192`) + patch-mode(`396280b`) + legacy-removal(`dd825a8`) 교차 영향 분석.
수동 코드 검증으로 **확인된 실제 버그 4건** 정리.

---

## A-1 (HIGH): Stage 4 `generation_method="patch"` — 패치 폴백 시 실제 생성 방법 오기록

**파일**: `modules/core/stage4_interview_round.py:641`

**문제**:
```python
# L641 (_record_s4_attempt 내부)
generation_method="patch" if is_patch else "ensemble",
```
- 패치 시도 → 실패 → `regenerate_with_feedback()` 폴백 시:
  - `is_patch=True` (패치 *시도*함), `patch_fallback=True` (패치 *실패*함)
  - `generation_method="patch"` ← **오류**: 실제 원고는 ensemble(regenerate)이 생성
- 영향 1: `get_stage_stats()` L200 method_attempts에서 "patch" 메서드 시도 횟수 부풀림
- 영향 2: `get_patch_effectiveness()` L282 `patch_success`에서 full-rewrite 성공을 패치 성공으로 오집계

**수정**:
```python
generation_method="patch" if is_patch and not patch_fallback else "ensemble",
```

**테스트 수정** (`tests/test_stage4_interview_round.py`):
- `TestRecordS4Attempt` 에 패치 폴백 시 `generation_method == "ensemble"` 검증 테스트 추가

---

## A-2 (MEDIUM): `get_stage_stats()` 에피소드 그룹핑 — `arc=0` falsy 처리 오류

**파일**: `modules/core/pass_rate_monitor.py:188`

**문제**:
```python
key = (r.episode, r.arc) if r.arc else (r.episode,)
```
- `arc=0` 은 Python에서 falsy → key가 `(episode,)` (1-tuple)
- `arc=3` 은 truthy → key가 `(episode, 3)` (2-tuple)
- Sweep 11 이전 기록(arc=0)과 이후 기록(arc>0)이 같은 에피소드에 혼재 시, 서로 다른 그룹으로 분리 → 중복 카운팅
- `first_attempt_pass`, `eventual_pass` 등 에피소드 단위 통계 왜곡 가능

**수정**:
```python
key = (r.episode, r.arc)
```
- `arc=0`도 정상적인 2-tuple `(episode, 0)` 으로 처리
- 기존 기록(arc=0)과 신규 기록(arc=3)이 자연스럽게 분리됨 (의도된 동작)

---

## A-3 (LOW): `detect_director_bias()` 모집단 불일치 — avg_score vs pass_rate 분모 상이

**파일**: `modules/core/quality_dashboard.py:1025-1032`

**문제**:
```python
scores = [float(r.get("score")) for r in recs if isinstance(r.get("score"), int | float)]  # filtered
count = len(recs)  # ALL
avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0     # ← 분모: len(scores)
"pass_rate": round(passes / count, 2) if count > 0 else 0.0,           # ← 분모: count (= len(recs))
```
- `avg_score`는 유효 점수가 있는 레코드만, `pass_rate`는 전체 레코드 사용
- 점수 없는 레코드가 있으면 두 지표의 모집단이 달라 편향 감지가 왜곡됨
- 현재는 모든 director_selections에 score가 있어 실효적 차이 없으나, 방어 코드 필요

**수정**:
```python
scores = [float(r.get("score")) for r in recs if isinstance(r.get("score"), int | float)]
passes = sum(1 for r in recs if isinstance(r.get("score"), int | float) and str(r.get("verdict", "")).upper() == "PASS")
count = len(scores)
avg_score = round(sum(scores) / count, 1) if count > 0 else 0.0

strategy_stats[strategy] = {
    "avg_score": avg_score,
    "pass_rate": round(passes / count, 2) if count > 0 else 0.0,
    "count": count,
}
```

---

## B-1 (LOW): `energy` 상한 미보호 — LLM이 음수 loss 반환 시 100% 초과

**파일**: `modules/core/feedback_system.py:329`

**문제**:
```python
energy = max(0, 100 - loss_val)
```
- `loss_val`이 음수(예: LLM이 `"energy_loss": "-10%"` 반환)이면 `100 - (-10) = 110`
- `max(0, 110) = 110` → 내공 110% 표시
- 하한(0)은 보호되지만 상한(100)은 미보호

**수정**:
```python
energy = max(0, min(100, 100 - loss_val))
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/core/stage4_interview_round.py` | 1줄 수정 |
| A-1 | `tests/test_stage4_interview_round.py` | 테스트 1건 추가 (~15줄) |
| A-2 | `modules/core/pass_rate_monitor.py` | 1줄 수정 |
| A-3 | `modules/core/quality_dashboard.py` | 4줄 수정 |
| B-1 | `modules/core/feedback_system.py` | 1줄 수정 |

**총 ~22줄 변경**

---

## 오탐 제거 기록

5-에이전트 병렬 탐색에서 보고되었으나 수동 검증 후 오탐 확인된 항목:

| 보고 | 실제 | 이유 |
|------|------|------|
| `_was_patch` 시맨틱 오류 (Stage 2) | ✗ 오탐 | Stage 2의 `generation_method`는 `_was_patch`가 아닌 `pipeline_result`에서 결정 ("four_phase"). 패치 폴백 시에도 정확함 |
| `records.append()` 스레드 미보호 | ✗ 오탐 | CPython GIL이 `list.append()` 원자성 보장 + Stage 간 순차 실행 구조 |
| AttemptRecord 이전 포맷 역호환 실패 | ✗ 오탐 | dataclass 기본값 (`is_patch=False` 등)이 `**r` 언팩 시 누락 필드 자동 보충 |
| `detect_quality_drift` slope 정규화 누락 | ✗ 오탐 | `±5` 임계값이 현재 비정규 delta용으로 교정됨. 정규화 시 임계값도 변경 필요 → 설계 선택 |
| "건조" 키워드 이중 매칭 | ✗ 오탐 | "건조함"은 대화 부족 + 감각 묘사 부족을 동시 의미 → 양쪽 피드백 생성이 의도된 설계 |
| V50 모듈 초기화 실패 시 크래시 | ✗ 오탐 | 종료 블록 전부 `getattr(self, ..., None)` 가드로 None 체크 완비 |
| Stage2Context 바인딩 타이밍 | ✗ 오탐 | `_feedback_system` L185 초기화 → `Stage2Context.from_app()` L219 바인딩 시점에 이미 존재 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage4_interview_round.py tests/test_arc_difficulty.py tests/test_director_bias.py tests/test_quality_trend.py tests/test_feedback_system.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
