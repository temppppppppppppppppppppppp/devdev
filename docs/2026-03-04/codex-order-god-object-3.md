# Codex Order: God Object 해체 3차 — `_process_verdict()` 분할

> **목적**: `Stage4InterviewRound._process_verdict()` 320줄 → ~104줄 (-67%).
>   PASS/REJECT/PASS_WITH_FIX 세 책임 경로를 분리해 단일 책임 원칙 적용.
> **금지**: 로직 변경. 반환 구조 변경. 기존 메서드 시그니처 변경. 모델 값 변경.
> **출력 보고서**: `docs/2026-03-04/god-object-3-result.md`

---

## 0) 강제 제약

- 수정 파일: **1개** (`modules/core/stage4_interview_round.py`).
- 완료 후 즉시 `python -m py_compile modules/core/stage4_interview_round.py` 통과 필수.
- `pytest tests/ -q` 기준선: **3227 passed, 0 failed**.
- `ruff check modules/core/stage4_interview_round.py` 위반 0건.

---

## 1) 현재 상태 파악 (수동 검사 필수)

구현 전 `_process_verdict()` 전체(L917~L1237 근방)를 직접 읽어라.

확인 사항:
- **QualityGate 블록** (L950~L959): `verdict = "REJECT"` 재설정 + `director_feedback` 수정 — `_process_verdict()` 본체에 유지
- **Post-select 블록** (L978~L1065): `if verdict in ("PASS", "PASS_WITH_FIX"):` 안의 병렬 continuity/history 체크 + 다운그레이드 로직 — 추출 대상 A
- **PWF 루프 블록** (L1067~L1194): `if verdict == "PASS_WITH_FIX":` InPlace 패치 최대 3회 + Director 재심사 — 추출 대상 B
- **Post-select 블록이 변경할 수 있는 변수**: `verdict`, `director_feedback`, `previous_attempt`, `error_category`
- **PWF 루프가 변경할 수 있는 변수**: `verdict`, `final_manuscript`, `final_state_updates`, `director_result["fix_scope"]`, `director_feedback`

---

## 2) 추출 대상 2개 메서드

### A) `_run_post_select_checks()` — Post-select 병렬 검사 (~88줄)

**추출 대상** (현재 L978~L1065 근방):
- `ThreadPoolExecutor` 병렬 continuity/history conflict 검사
- 충돌 발견 시 `verdict = "REJECT"` 다운그레이드 + `previous_attempt` 갱신

**시그니처**:

```python
def _run_post_select_checks(
    self,
    *,
    verdict: str,
    final_manuscript: str,
    final_state_updates: dict,
    next_ep: int,
    round_num: int,
    round_ctx,
    director_result: dict,
    director_feedback: str,
    score: int,
    error_category: str,
    previous_attempt: dict | None,
    stage4_spinner,
    director_memory_context: str,
) -> tuple:
    """[God-3] Post-select 병렬 검사 (continuity + history conflict).

    Returns:
        tuple: (verdict, director_feedback, previous_attempt, error_category)
               verdict 이 REJECT로 바뀔 수 있음.
    """
```

**`_process_verdict()` 호출부** (post-select 블록 대체):

```python
if verdict in ("PASS", "PASS_WITH_FIX"):
    selected_candidate = director_result.get("selected_candidate") or {}
    final_manuscript = selected_candidate.get("manuscript", "")
    final_title = selected_candidate.get("title", f"제{next_ep}화")
    final_state_updates = director_result.get("state_updates", {})

    verdict, director_feedback, previous_attempt, error_category = self._run_post_select_checks(
        verdict=verdict,
        final_manuscript=final_manuscript,
        final_state_updates=final_state_updates,
        next_ep=next_ep,
        round_num=round_num,
        round_ctx=round_ctx,
        director_result=director_result,
        director_feedback=director_feedback,
        score=score,
        error_category=error_category,
        previous_attempt=previous_attempt,
        stage4_spinner=stage4_spinner,
        director_memory_context=_director_memory_context,
    )
```

**주의**:
- `_run_post_select_checks()` 내부에서 충돌 없으면 `previous_attempt`를 변경하지 않고 입력 그대로 반환
- `final_title`, `final_manuscript`, `final_state_updates`는 호출 전 `_process_verdict()` 에서 꺼내 두므로 이 메서드에 전달 필요 없음
- `_run_continuity`, `_run_history` 조건 분기 로직도 메서드 내부로 이동

---

### B) `_execute_pass_with_fix_loop()` — PASS_WITH_FIX InPlace 패치 루프 (~128줄)

**추출 대상** (현재 L1067~L1194 근방):
- `if verdict == "PASS_WITH_FIX" and final_manuscript:` 블록 전체
- InPlace 패치 최대 3회 반복 + Director 재심사
- 최종 `verdict`, `final_manuscript`, `final_state_updates` 결정

**시그니처**:

```python
def _execute_pass_with_fix_loop(
    self,
    *,
    verdict: str,
    final_manuscript: str,
    final_state_updates: dict,
    director_result: dict,
    director_feedback: str,
    round_ctx,
    round_num: int,
    score: int,
    quality_gate_score: int,
    director_mandatory_context: str,
) -> tuple:
    """[God-3] PASS_WITH_FIX → InPlace 패치 + Director 재심사 루프 (최대 3회).

    Returns:
        tuple: (verdict, final_manuscript, final_state_updates, director_result, director_feedback)
               verdict 가 PASS 또는 REJECT로 확정됨.
    """
```

**`_process_verdict()` 호출부** (PWF 블록 대체):

```python
if verdict == "PASS_WITH_FIX" and final_manuscript:
    verdict, final_manuscript, final_state_updates, director_result, director_feedback = \
        self._execute_pass_with_fix_loop(
            verdict=verdict,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            director_result=director_result,
            director_feedback=director_feedback,
            round_ctx=round_ctx,
            round_num=round_num,
            score=score,
            quality_gate_score=int(_quality_gate_score),
            director_mandatory_context=_director_mandatory_context,
        )
```

**주의**:
- `_quality_gate_score`는 메서드 호출 전 `_process_verdict()` 에서 읽어 `int`로 변환 후 전달
- `_extract_fix_feedback()`, `chief_writer`, `style_guide`는 `self.ctx`, `round_ctx`를 통해 메서드 내부에서 접근:
  - `chief_writer = round_ctx.chief_writer`
  - `style_guide = round_ctx.style_guide`
  - `_director = self.ctx.agents.get("director")`
- `director_result["fix_scope"]` 변이가 발생하므로 `director_result` 도 반환

---

## 3) `_process_verdict()` 추출 후 골격

```python
def _process_verdict(self, *, director_result, director_feedback, verdict, score,
                     round_ctx, round_num, previous_attempt, is_patch,
                     is_patch_fallback, prev_score, stage4_spinner,
                     director_mandatory_context, director_memory_context, error_category):
    """[B-1-3b] PASS/PASS_WITH_FIX 처리."""
    from modules.core.stage4_types import _InterviewRoundResult
    from modules.validation.threshold_helper import _threshold

    next_ep = round_ctx.next_ep
    chief_writer = round_ctx.chief_writer   # 유지 (final block에서 사용)
    style_guide = round_ctx.style_guide     # 유지
    story_context = round_ctx.story_context # 유지
    _prev_manuscripts_text = round_ctx.prev_manuscripts_text
    _director_memory_context = director_memory_context
    _director_mandatory_context = director_mandatory_context
    _is_patch = is_patch
    _is_patch_fallback = is_patch_fallback
    _prev_score = prev_score

    _quality_gate_score = _threshold("scoring.quality_gate_score", 90)

    # QualityGate: PASS → REJECT 다운그레이드 (기존 코드 그대로 유지)
    if verdict == "PASS" and score < _quality_gate_score:
        ...

    if verdict in ("PASS", "PASS_WITH_FIX"):
        selected_candidate = director_result.get("selected_candidate") or {}
        final_manuscript = selected_candidate.get("manuscript", "")
        final_title = selected_candidate.get("title", f"제{next_ep}화")
        final_state_updates = director_result.get("state_updates", {})

        # A: Post-select 병렬 검사
        verdict, director_feedback, previous_attempt, error_category = self._run_post_select_checks(
            ...
        )

    # B: PASS_WITH_FIX 루프
    if verdict == "PASS_WITH_FIX" and final_manuscript:
        verdict, final_manuscript, final_state_updates, director_result, director_feedback = \
            self._execute_pass_with_fix_loop(...)

    if verdict in ("PASS", "PASS_WITH_FIX"):
        # 시간 일관성 체크 + _record_s4_attempt + return (기존 그대로)
        ...

    # REJECT fallthrough → _handle_reject() (기존 그대로)
    ...
```

---

## 4) 실행 순서

```bash
python -m py_compile modules/core/stage4_interview_round.py
ruff check modules/core/stage4_interview_round.py
pytest tests/ -q
```

---

## 5) 검증 포인트

```python
import ast
src = open('modules/core/stage4_interview_round.py', encoding='utf-8').read()
tree = ast.parse(src)
for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == 'Stage4InterviewRound':
        for m in cls.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name in (
                '_process_verdict', '_run_post_select_checks', '_execute_pass_with_fix_loop'
            ):
                print(f'  {m.end_lineno - m.lineno:4d}줄  L{m.lineno}~{m.end_lineno}  {m.name}')
```

기대 결과:
- `_process_verdict()`: **≤ 130줄** (기존 320줄 대비 -59% 이상)
- `_run_post_select_checks()`: **신규 존재**
- `_execute_pass_with_fix_loop()`: **신규 존재**

---

## 6) 보고서 형식

출력: `docs/2026-03-04/god-object-3-result.md`

```markdown
# God Object 해체 3차 결과

> 감사일: 2026-03-04

## 추출 내역

| 메서드 | 추출 구간 | 크기 |
|--------|----------|------|
| `_run_post_select_checks()` | L978~L1065 근방 | N줄 |
| `_execute_pass_with_fix_loop()` | L1067~L1194 근방 | N줄 |

## _process_verdict() 크기 변화

- Before: 320줄
- After: N줄 (-N%)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (N skipped)
```

---

## 7) 합격 기준

- `_process_verdict()` **≤ 130줄** (기존 320 대비 -59% 이상)
- `_run_post_select_checks()`, `_execute_pass_with_fix_loop()` **전부 존재**
- `_handle_reject()` 시그니처 **불변**
- 전체 테스트 **3227+ passed, 0 failed**
- ruff 위반 **0건**
