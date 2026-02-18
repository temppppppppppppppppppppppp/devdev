# Debug Sweep 31 — LLM 점수 타입 혼동 체계적 수정 + int() 무방비 변환

## Context

Sweep 30(6건, 2,037 passed) 완료 후, 5-에이전트 병렬 탐색:
unguarded int/float 변환, split 인덱스, 누락 return, 산술 타입 혼동, 변수 스코프.
수동 코드 검증으로 **확인된 실제 버그 9건** 정리.

**핵심 패턴**: LLM이 `{"score": "75"}` (string) 반환 시 `score >= 70` → `TypeError: '>=' not supported between instances of 'str' and 'int'`. `json.loads`는 타입을 보존하므로 JSON string `"75"`는 Python string `"75"`가 됨. 코드베이스 전역에서 점수 타입 강제 변환(coercion) 없이 산술/비교 수행.

**공통 수정 패턴**:
```python
# Before:
score = result.get("score", 50)

# After:
try:
    score = int(result.get("score", 50))
except (ValueError, TypeError):
    score = 50
```

---

## A-1 (CRITICAL): `arc_critic.py:187,192` — `sum(scores.values())` + `score >= 70` on LLM string scores

**파일**: `modules/domain/agents/arc_critic.py:180-197`

**문제**:
```python
def _ensure_critique_fields(self, result: dict) -> dict:
    if "total_score" not in result:
        scores = result["scores"]
        result["total_score"] = sum(scores.values()) if scores else 0  # ← TypeError
    if "verdict" not in result:
        score = result["total_score"]
        if score >= 70 and not has_critical:  # ← TypeError
```
- LLM이 `"scores": {"item_continuity": "8", "location_continuity": "10"}` 반환 시
- `sum(["8", "10", ...])` → `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
- `_ensure_critique_fields`는 try/except 없음

**수정**:
```python
if "total_score" not in result:
    scores = result["scores"]
    try:
        result["total_score"] = sum(int(v) for v in scores.values()) if scores else 0
    except (ValueError, TypeError):
        result["total_score"] = 0

if "verdict" not in result:
    try:
        score = int(result["total_score"])
    except (ValueError, TypeError):
        score = 0
```

---

## A-2 (CRITICAL): `director_auditor.py:811-888` — 점수 비교 + statistics.median on string scores

**파일**: `modules/domain/agents/director_auditor.py:811,814,822,880,888`

**문제**:
```python
first_score = first_eval.get("score", 50)  # string "75" 가능

if first_decision == "REJECT" and first_score < self._d.ambiguous_lower:  # ← TypeError
if first_decision == "PASS" and first_score > self._d.ambiguous_upper:    # ← TypeError

scores = [e.get("score", 50) for e in evaluations if isinstance(e, dict)]
median_score = statistics.median(scores)  # ← TypeError (정렬 시 str/int 혼합)

representative = min(evaluations, key=lambda e: abs(e.get("score", 50) - median_score))  # ← TypeError
```

**수정** — L811에서 int 강제:
```python
try:
    first_score = int(first_eval.get("score", 50))
except (ValueError, TypeError):
    first_score = 50
```
— L880에서 int 강제:
```python
scores = []
for e in evaluations:
    if isinstance(e, dict):
        try:
            scores.append(int(e.get("score", 50)))
        except (ValueError, TypeError):
            scores.append(50)
```
— L888에서 int 강제:
```python
representative = min(evaluations, key=lambda e: abs(int(e.get("score", 50)) if str(e.get("score", 50)).isdigit() else 50) - median_score)
```
→ 또는 더 간단하게 `_safe_int` 인라인 람다 사용.

---

## A-3 (HIGH): `multi_agent_deliberation.py:231,297,300` — score 산술 on string

**파일**: `modules/core/multi_agent_deliberation.py:231,297,300`

**문제**:
```python
# L231 — LLM score를 raw 저장
score=result.get("score", 70),  # AgentOpinion.score = "75" (string)

# L297 — 산술
scores = [o.score for o in opinions]
avg_score = sum(scores) / len(scores)  # ← TypeError

# L300 — 비교
all_pass = all(s >= 80 for s in scores)  # ← TypeError
```

**수정** — L231에서 int 강제:
```python
try:
    _score = int(result.get("score", 70))
except (ValueError, TypeError):
    _score = 70
return AgentOpinion(
    role=role,
    score=_score,
    ...
)
```

---

## A-4 (HIGH): `state_delta_tracker.py:408` — `int(energy)` 무방비

**파일**: `modules/core/state_delta_tracker.py:406-409`

**문제**:
```python
energy = arc_end.get("internal_energy", 100)
if isinstance(energy, str):
    energy = int(energy.replace("%", "").strip())  # ← ValueError: "N/A", "고갈", "불명"
self.current_energy = max(0, min(100, int(energy)))  # ← TypeError: None
```
- 전체 파일에 `try/except` 0건
- 같은 패턴의 `analyst.py:228`은 `try/except (ValueError, TypeError)` 가드 존재

**수정**:
```python
energy = arc_end.get("internal_energy", 100)
if isinstance(energy, str):
    try:
        energy = int(energy.replace("%", "").strip())
    except (ValueError, TypeError):
        energy = 50  # 안전 기본값
try:
    self.current_energy = max(0, min(100, int(energy)))
except (ValueError, TypeError):
    self.current_energy = 50
```

---

## A-5 (HIGH): `cross_agent_verifier.py:306,310` — score 산술 on string

**파일**: `modules/core/cross_agent_verifier.py:306,310` (+ L390 동일 패턴)

**문제**:
```python
score = result.get("compliance_score", 0.7)  # string "0.8" 가능
if py_violations:
    score = max(0.0, score - 0.2 * len(py_violations))  # ← TypeError
```

**수정** — L306에서 float 강제:
```python
try:
    score = float(result.get("compliance_score", 0.7))
except (ValueError, TypeError):
    score = 0.7
```
— L390 근처에서도 동일 패턴 적용.

---

## A-6 (HIGH): `block_enricher.py:473` — `total_score >= 70` on string

**파일**: `modules/domain/agents/block_enricher.py:473`

**문제**:
```python
total_score = result.get("total_score", 0)
if total_score >= 70:  # ← TypeError: "70" >= 70
```

**수정**:
```python
try:
    total_score = int(result.get("total_score", 0))
except (ValueError, TypeError):
    total_score = 0
```

---

## B-1 (MEDIUM): `constraint_db.py:153,163,169,172` — `int(arc_no)` 무방비

**파일**: `modules/core/constraint_db.py:93-172`

**문제**:
```python
arc_no = arc_data.get("arc_no")
if not arc_no:
    return
# ... 이후 L153,163,169,172에서:
int(arc_no)  # ← ValueError: "Arc1", "1-A" 등 비숫자
```
- L96 `if not arc_no: return` 가드로 None/0/"" 차단
- 하지만 비숫자 문자열("Arc1")은 통과 → `int("Arc1")` → ValueError
- 외부 `except Exception` (L90)이 잡지만 남은 Arc 전부 중단

**수정** — L96 다음에:
```python
try:
    arc_no = int(arc_no)
except (ValueError, TypeError):
    logging.warning(f"[ConstraintDB] arc_no 파싱 실패: {arc_no!r} — 스킵")
    return
```

---

## B-2 (MEDIUM): `stage2_orchestrator.py:545` + `stage4_interview_round.py:103` — score >= Threshold on string

**파일 2곳**:

**(1) `stage2_orchestrator.py:545,547`**:
```python
_rej_score = _fin.get("score", 0)
if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
    # ← TypeError: "50" >= 50
```

**(2) `stage4_interview_round.py:103,105`**:
```python
_prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
_use_patch = _prev_score >= _PATCH_REWRITE_THRESHOLD and _prev_manuscript
    # ← TypeError: "50" >= 50
```

**수정** — 각각 int 강제:
```python
# stage2_orchestrator.py:545
try:
    _rej_score = int(_fin.get("score", 0))
except (ValueError, TypeError):
    _rej_score = 0

# stage4_interview_round.py:103
try:
    _prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0
except (ValueError, TypeError):
    _prev_score = 0
```

---

## B-3 (MEDIUM): `quality_dashboard.py:804,887` — 지속 데이터 score 산술

**파일**: `modules/core/quality_dashboard.py:804-806,887-891`

**문제**:
```python
# L804-806
current_score = scored[-1].get("score", 0)
prev_score = scored[-2].get("score", 0)
delta = prev_score - current_score  # ← TypeError: "75" - "70"

# L887-891
scores = [r.get("score", 0) for r in recent]
avg = sum(scores) / len(scores)  # ← TypeError
delta = scores[-1] - scores[0]   # ← TypeError
```
- JSON 파일에 string score가 저장되면 이후 로드 시 전량 크래시
- L950의 `float()` 사용은 별도 경로

**수정** — 각각 int 강제:
```python
# L804-806
try:
    current_score = int(scored[-1].get("score", 0))
    prev_score = int(scored[-2].get("score", 0))
except (ValueError, TypeError):
    current_score, prev_score = 0, 0

# L887-889
scores = []
for r in recent:
    try:
        scores.append(int(r.get("score", 0)))
    except (ValueError, TypeError):
        scores.append(0)
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/arc_critic.py` | ~8줄 (sum+score int 강제) |
| A-2 | `modules/domain/agents/director_auditor.py` | ~12줄 (first_score+scores+representative int 강제) |
| A-3 | `modules/core/multi_agent_deliberation.py` | ~4줄 (score int 강제) |
| A-4 | `modules/core/state_delta_tracker.py` | ~6줄 (energy try/except) |
| A-5 | `modules/core/cross_agent_verifier.py` | ~6줄 (compliance_score float 강제 2곳) |
| A-6 | `modules/domain/agents/block_enricher.py` | ~4줄 (total_score int 강제) |
| B-1 | `modules/core/constraint_db.py` | ~4줄 (arc_no int 강제) |
| B-2 | `modules/core/stage2_orchestrator.py` | ~4줄 (_rej_score int 강제) |
| B-2 | `modules/core/stage4_interview_round.py` | ~4줄 (_prev_score int 강제) |
| B-3 | `modules/core/quality_dashboard.py` | ~10줄 (score int 강제 2곳) |

**총 ~62줄 변경, 10개 파일**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `str.split()[N]` 전체 (Agent 2) | ✗ 0건 | 전량 `if delim in str:` 가드 + try/except 확인 |
| `load_state_log -> dict` 어노테이션 (Agent 3) | ✗ LOW | 4개 호출자 전량 `if log_data and isinstance(log_data, dict):` 가드. 어노테이션만 부정확 |
| `create_manuscript_cache -> str` (Agent 3) | ✗ LOW | 프로덕션 호출자 없음 (dead code) |
| `_try_merge_responses` 외 3건 (Agent 3) | ✗ LOW | 전량 호출자가 `if result:` 가드 |
| `_cv_context` 미초기화 (`stage4_interview_round.py:268`) | ✗ 오탐 | L268은 dict literal — 예외 불가. 항상 정의된 후 L355에서 사용 |
| `manual_input` 미초기화 (`stage2_orchestrator.py:722`) | ✗ 오탐 | `user_choice == "4" and manual_input` — short-circuit으로 `user_choice != "4"`이면 `manual_input` 미평가 |
| `_rejected_arc` 스코프 (`stage2_finalizer.py:469`) | ✗ 오탐 | L469는 else 블록 내부 — PASS 경로는 early return |
| `scoring_validator.py:752` score*weight | ✗ 오탐 | upstream `_calculate_llm_scores`에서 `int()` clamp 후 전달 |
| `director_grading.py:159` score/max_score | ✗ 오탐 | upstream scoring_validator에서 clamp됨 |
| `prompt_optimizer.py:87` score/max_score | ✗ LOW | 동일 — upstream에서 보호되지만 별도 경로 가능 |
| `adversarial_self_play.py:291,308` | ✗ 후순위 | 별도 심화 수정 대상 (현재 sweep 스코프 외) |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_sweep31.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Update (2026-02-18)

Status: completed for Sweep 31 scope.

Applied items:
- A-1 `modules/domain/agents/arc_critic.py`: `scores` 합산 및 verdict 분기 전 `int` 강제 + 예외 fallback 추가.
- A-2 `modules/domain/agents/director_auditor.py`: Self-Consistency 경로에 `_safe_int_score` 추가, 첫 점수/투표 점수/중앙값/대표 선택 모두 정수 기반으로 정규화.
- A-3 `modules/core/multi_agent_deliberation.py`: `AgentOpinion.score` 생성 시 `int` coercion + fallback.
- A-4 `modules/core/state_delta_tracker.py`: `internal_energy` 문자열 파싱/최종 int 변환에 `try/except` 추가.
- A-5 `modules/core/cross_agent_verifier.py`: `compliance_score`를 두 경로에서 `float` coercion + fallback.
- A-6 `modules/domain/agents/block_enricher.py`: `total_score` int coercion 후 PASS/REJECT 판정.
- B-1 `modules/core/constraint_db.py`: `arc_no`를 초기에 int 파싱하고 실패 시 warning 후 skip.
- B-2 `modules/core/stage2_orchestrator.py`, `modules/core/stage4_interview_round.py`: 분기 점수 비교 전 int coercion.
- B-3 `modules/core/quality_dashboard.py`: 회귀 감지/추세 계산 점수를 int로 정규화해 산술/비교 안전성 확보.

Added tests:
- `tests/test_sweep31.py` (10 tests): string-score coercion, safe parsing guards, source regression checks.

Verification run:
- `python -m pytest tests/test_sweep31.py -q -x` -> `10 passed`
- `python -m pytest tests/test_director_modules.py tests/test_stage2_pipeline.py tests/test_stage4_interview_round.py tests/test_stage2_validation_pipeline.py -q -x` -> `184 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2047 passed, 68 xfailed, 1 warning`

Notes:
- 기존과 동일하게 테스트 출력에는 interactive/log print와 post-run mocked ImportError traceback print가 포함되지만, pytest exit code는 0입니다.
