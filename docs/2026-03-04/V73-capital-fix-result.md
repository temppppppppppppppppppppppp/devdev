# V73 자본금 역동기화 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1 | `modules/core/stage4_post_processor.py` | `_reconcile_capital`에 `final_state_updates` 파라미터 추가 + Director capital 키 우선 스킵 | 완료 |
| 2 | `modules/core/stage4_post_processor.py` | `_DIALOGUE_RE` 추가 + `_extract_capital_from_manuscript`에서 대사 제거 후 regex 매칭 | 완료 |
| 3 | `tests/test_v73_capital_fix.py` | V73 전용 테스트 7개 추가 | 완료 |

## 코드 반영 포인트

- Director 우선 스킵 로직
  - `_reconcile_capital(..., final_state_updates: dict | None = None)`
  - `{"capital", "자본", "자본금", "잔고"}` 키 포함 시 조기 return
- 대사 제거 후 자본금 추출
  - `_DIALOGUE_RE`로 따옴표 내부 텍스트 제거
  - 기존 `finditer(manuscript)` 2곳만 `finditer(narration_only)`로 교체
- 호출부 연동
  - `process_pass_result()`에서 `_reconcile_capital(final_manuscript, next_ep, final_state_updates=final_state_updates)`로 변경

## 검증 결과

- py_compile: 통과
  - `python -m py_compile modules/core/stage4_post_processor.py`
- 신규 테스트: 7 passed, 0 failed
  - `pytest tests/test_v73_capital_fix.py -v`
- ruff: 위반 0건
  - `ruff check modules/core/stage4_post_processor.py tests/test_v73_capital_fix.py`
- 전체 테스트: **3220 passed, 0 failed (16 skipped)**
  - `pytest tests/ -q`

## 산출물

- 수정 파일: `modules/core/stage4_post_processor.py`
- 신규 테스트: `tests/test_v73_capital_fix.py`
