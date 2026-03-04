# Codex Order: God Object 해체 1차 — `stage4_interview_round.run()` 3차 분할

> **목적**: `Stage4InterviewRound.run()` 782줄 → ~370줄 (-53%), 3개 private 메서드 추출.
>   `run()`이 Orchestrator 역할만 하도록 책임 분리.
> **금지**: 로직 변경. 변수명/파라미터 시그니처 변경(외부 호출부 불변). 모델 값 변경.
> **출력 보고서**: `docs/2026-03-04/god-object-1-result.md`

---

## 0) 강제 제약

- 수정 파일: **1개** (`modules/core/stage4_interview_round.py`).
- 완료 후 즉시 `python -m py_compile modules/core/stage4_interview_round.py` 통과 필수.
- `pytest tests/ -q` 기준선: **3227 passed, 0 failed** (현재 기준선).
- `ruff check modules/core/stage4_interview_round.py` 위반 0건.

---

## 1) 현재 상태 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: modules/core/stage4_interview_round.py
읽을 범위:
  - run() L27~L186  (PatternTracker + WritingDirective + kwargs 조립 구간)
  - run() L283~L582 (Python 사전 검증 6종 루프 구간)
```

확인 사항:
- `_writing_directive`, `_wd_expression_freq`가 L77~L115에서 초기화 후, L607~L615에서 Director 컨텍스트 주입에 재사용되는지 확인 — 추출 후 `run()`에 반환값 주입 필요
- `mandatory_context`가 L117~L124에서 문자열 정규화 + preflight prepend 후, kwargs dict(L156~L185)와 Director 준비 구간(L605~)에서 재사용되는지 확인 — 추출 후 반환된 값으로 `run()` 로컬 변수 교체
- `validation_results`가 L283~L582에서 in-place 수정된 후 L584~에서 Director에 전달되는지 확인 — 추출 후 반환값으로 교체

---

## 2) 추출 대상 3개 메서드

### A) `_setup_writing_directive()` — L77~L115 추출

**시그니처**:

```python
def _setup_writing_directive(
    self,
    chief_writer,
    blueprint: dict,
    genre_name: str,
    next_ep: int,
) -> tuple:
    """[God-1] PatternTracker + WritingDirective 초기화.

    Returns:
        (WritingDirective, dict): (_writing_directive, _wd_expression_freq)
    """
```

**추출 내용** (현재 L77~L115):
- `_threshold("pattern_tracker.enable", True)` 읽기 + PatternTracker 빌드
- `WritingDirectiveGenerator().generate(...)` 호출
- 결과를 `chief_writer`에 setattr로 주입 (L110~L115 부분 포함)
- 실패 시 비치명 `WritingDirective()`, `{}` 반환

**`run()` 호출부**:

```python
# Before (L77~L115 구간):
_writing_directive: WritingDirective = WritingDirective()
_wd_expression_freq: dict[str, int] = {}
try:
    ...PatternTracker + WritingDirectiveGenerator 로직 전체...
except Exception as _wd_e:
    ...
try:
    setattr(chief_writer, "_current_blueprint", ...)
    setattr(chief_writer, "_tf54_writing_directive", _writing_directive)
    setattr(chief_writer, "_tf54_expression_freq", _wd_expression_freq)
except Exception as _tf54_ctx_e:
    ...

# After:
_writing_directive, _wd_expression_freq = self._setup_writing_directive(
    chief_writer=chief_writer,
    blueprint=blueprint,
    genre_name=genre_name,
    next_ep=next_ep,
)
```

---

### B) `_build_common_writer_kwargs()` — L117~L186 추출

**시그니처**:

```python
def _build_common_writer_kwargs(
    self,
    round_ctx,
    next_ep: int,
    mandatory_context: str,
) -> tuple:
    """[God-1] mandatory_context 정규화 + common_writer_kwargs dict 조립.

    Returns:
        (str, dict): (mandatory_context_str, common_writer_kwargs)
    """
```

**추출 내용** (현재 L117~L186):
- `mandatory_context` / `director_feedback` 타입 정규화 (L117~L120)
- `_preflight_advisory` → mandatory_context prepend (L122~L124)
- `emotional_beat_section` 추출 (L126~L138)
- `_motivations`, `_promises` 추출 (L140~L143)
- `_upcoming_arc_items` 추출 (L145~L153)
- `_common_writer_kwargs` dict 25개 필드 조립 (L155~L186)

**반환**: `(mandatory_context, _common_writer_kwargs)` 두 값

**`run()` 호출부**:

```python
# Before (L117~L186 구간):
if type(director_feedback) is not str:
    ...
mandatory_context, _common_writer_kwargs = self._build_common_writer_kwargs(
    round_ctx=round_ctx,
    next_ep=next_ep,
    mandatory_context=mandatory_context,
)
```

**주의**: `director_feedback` 정규화(L117~L118)는 `run()` 로컬에서 처리하거나 이 메서드에 `director_feedback` 파라미터로 전달 — 어느 쪽이든 `run()` 안에서 교체 완료 필수.

---

### C) `_run_pre_director_validation()` — L283~L582 추출

**시그니처**:

```python
def _run_pre_director_validation(
    self,
    candidates: list,
    next_ep: int,
    blueprint: dict,
    prev_text: str,
    hud_report,
    genre_name: str,
    manuscript_validator,
    consistency_validator,
    blocking_validator,
    continuity_validator,
) -> list[dict]:
    """[God-1] Python 사전 검증 6종 실행 (manuscript/consistency/blocking/continuity/V66.2/Pre-check/CC/CV).

    Returns:
        list[dict]: validation_results (각 후보별 경고 목록 포함)
    """
```

**추출 내용** (현재 L283~L582):
- `validate_all_candidates()` 호출 (L294~L306)
- ConsistencyValidator 루프 (L309~L332)
- BlockingValidator 루프 (L337~L356)
- ContinuityValidator 루프 (L358~L393)
- V66.2 파괴 엔티티 검사 (L395~L407)
- Pre-Director Checklist 루프 (L408~L542)
- ConfidenceCalibrator 루프 (L544~L558)
- CrossAgentVerifier 루프 (L561~L582)

**`run()` 호출부**:

```python
# Before (L283~L582 구간, ~300줄):
# Phase 3: Python 사전 검증
...6종 검증 루프 전체...

# After:
validation_results = self._run_pre_director_validation(
    candidates=candidates,
    next_ep=next_ep,
    blueprint=blueprint,
    prev_text=prev_text,
    hud_report=hud_report,
    genre_name=genre_name,
    manuscript_validator=manuscript_validator,
    consistency_validator=consistency_validator,
    blocking_validator=blocking_validator,
    continuity_validator=continuity_validator,
)
```

---

## 3) 실행 순서

```bash
# 패치 후
python -m py_compile modules/core/stage4_interview_round.py

# ruff
ruff check modules/core/stage4_interview_round.py

# 전체 회귀
pytest tests/ -q
```

---

## 4) 검증 포인트

패치 후 수동 확인:

```python
# run() 줄 수 확인
import ast
src = open('modules/core/stage4_interview_round.py', encoding='utf-8').read()
tree = ast.parse(src)
for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == 'Stage4InterviewRound':
        for m in cls.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                size = m.end_lineno - m.lineno
                if size >= 50:
                    print(f'  {size:4d}줄  L{m.lineno}~{m.end_lineno}  {m.name}')
```

기대 결과:
- `run()`: **~370줄** (기존 782줄 대비 -53%)
- `_setup_writing_directive()`: **~45줄** (신규)
- `_build_common_writer_kwargs()`: **~75줄** (신규)
- `_run_pre_director_validation()`: **~310줄** (신규)
- 기존 `_process_verdict()`, `_handle_reject()`, `_build_cv_context()`, `_generate_candidates()` 시그니처 **불변**

---

## 5) 보고서 형식

출력: `docs/2026-03-04/god-object-1-result.md`

```markdown
# God Object 해체 1차 결과

> 감사일: 2026-03-04

## 추출 내역

| 메서드 | 추출 구간 | 추출 후 run() 줄 수 감소 |
|--------|----------|----------------------|
| `_setup_writing_directive()` | L77~L115 | -N줄 |
| `_build_common_writer_kwargs()` | L117~L186 | -N줄 |
| `_run_pre_director_validation()` | L283~L582 | -N줄 |

## run() 크기 변화

- Before: 782줄 (L27~L809)
- After: N줄 (-N%)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (N skipped)
```

---

## 6) 합격 기준

- `run()` 줄 수 **≤ 420줄** (기존 782 대비 -46% 이상)
- 3개 신규 메서드 **전부 존재** (`_setup_writing_directive`, `_build_common_writer_kwargs`, `_run_pre_director_validation`)
- `_process_verdict()`, `_handle_reject()`, `_build_cv_context()`, `_generate_candidates()` **시그니처 불변**
- 전체 테스트 **3227+ passed, 0 failed**
- ruff 위반 **0건**
