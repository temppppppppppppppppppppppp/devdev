# Codex Order: V73 자본금 역동기화 — 2중 방어 구현

> **목적**: `stage4_post_processor._reconcile_capital()`의 두 가지 오인 리스크 해소.
>   1. Director가 이미 capital을 설정한 경우에도 regex가 덮어씀 (Director 주권 침해)
>   2. 대사 속 타인 자산 언급이 주인공 HUD capital로 오인
> **금지**: 기존 로직 삭제. 모델 값 변경. 명세에 없는 기능 추가.
> **출력 보고서**: `docs/2026-03-04/V73-capital-fix-result.md`

---

## 0) 강제 제약

- 수정 파일: `modules/core/stage4_post_processor.py` **1개만**.
- 각 Phase 완료 후 `python -m py_compile modules/core/stage4_post_processor.py` 통과 필수.
- `pytest tests/ -q` 기준선: **3,213 passed, 16 skipped, 0 failed**.
- `ruff check modules/core/stage4_post_processor.py` 위반 0건.

---

## 1) 현재 코드 구조 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: modules/core/stage4_post_processor.py
읽을 범위:
  - _CAPITAL_PATTERNS (L114~119)
  - _COMPOUND_CAPITAL_RE (L121~124)
  - _extract_capital_from_manuscript() (L159~196)  ← static method
  - _reconcile_capital() (L198~235)                ← 수정 대상
  - process_pass_result() 내 _reconcile_capital 호출부 (L313~317)
```

확인 사항:
- `_reconcile_capital(self, final_manuscript, ep_num)` 시그니처 — `final_state_updates` 파라미터 **없음** 확인
- `process_pass_result()`가 `final_state_updates: dict`를 파라미터로 받는지 확인 (L243 근방)
- `_reconcile_capital` 호출 시 `final_manuscript, next_ep` 2개 인자만 전달 중인지 확인 (L315)

---

## 2) Phase 1 — 방어 1: Director state_updates 우선

### 변경 대상

`_reconcile_capital()` 시그니처에 `final_state_updates: dict | None = None` 파라미터 추가.
메서드 진입부에서 Director가 이미 capital 관련 키를 설정했으면 → 조기 리턴.

### 구체 코드

```python
# Before:
def _reconcile_capital(self, final_manuscript: str, ep_num: int) -> None:

# After:
def _reconcile_capital(
    self,
    final_manuscript: str,
    ep_num: int,
    final_state_updates: dict | None = None,
) -> None:
    """확정 원고의 자본금과 HUD를 비교하여 불일치 시 경고 + 보정. 투자물 전용."""
    # [V73-방어1] Director가 이미 capital을 state_updates에 포함한 경우 → 스킵 (Director 주권 존중)
    if final_state_updates:
        _capital_keys = {"capital", "자본", "자본금", "잔고"}
        if _capital_keys & {k.lower() for k in final_state_updates}:
            logging.debug(
                "[V73] Director state_updates에 capital 포함 → 자본금 역동기화 스킵 (ep%d)", ep_num
            )
            return
```

### 호출부 수정

`process_pass_result()` 내 `_reconcile_capital` 호출부 (L315 근방):

```python
# Before:
self._reconcile_capital(final_manuscript, next_ep)

# After:
self._reconcile_capital(final_manuscript, next_ep, final_state_updates=final_state_updates)
```

---

## 3) Phase 2 — 방어 2: 대사 제거 후 regex 매칭

### 변경 대상

`_extract_capital_from_manuscript()` 메서드 진입부에서 따옴표 내부 텍스트(대사)를 제거한 뒤 regex 실행.

### 구체 코드

클래스 레벨 상수 추가 (`_COMPOUND_CAPITAL_RE` 다음 줄):

```python
# [V73-방어2] 대사(따옴표 내부) 제거용 패턴
_DIALOGUE_RE = re.compile(r'[""\u201c\u201d][^""\u201c\u201d]*[""\u201c\u201d]')
```

`_extract_capital_from_manuscript()` 메서드 진입부 수정:

```python
@staticmethod
def _extract_capital_from_manuscript(manuscript: str) -> float | None:
    """확정 원고에서 마지막으로 언급된 자본금(억 단위)을 추출. 없으면 None."""
    # [V73-방어2] 대사(따옴표 내부) 제거 → 타인 자산 언급 오인 방지
    narration_only = Stage4PostProcessor._DIALOGUE_RE.sub("", manuscript)
    # 이후 manuscript 대신 narration_only 사용
    candidates: list[tuple[int, float]] = []
    for pat in Stage4PostProcessor._CAPITAL_PATTERNS:
        for m in pat.finditer(narration_only):   # ← manuscript → narration_only
            ...
    for m in Stage4PostProcessor._COMPOUND_CAPITAL_RE.finditer(narration_only):  # ← 동일
        ...
```

**주의**: `manuscript` → `narration_only` 교체는 `finditer()` 호출 2곳만. 나머지 로직(candidates 처리, pos_best) 변경 없음.

---

## 4) Phase 3 — 테스트 추가

파일: `tests/test_v73_capital_fix.py` (신규)

```python
"""[V73] 자본금 역동기화 2중 방어 테스트."""
from modules.core.stage4_post_processor import Stage4PostProcessor


# ── 방어1: Director state_updates 우선 ──────────────────────────────────

def test_v73_skip_when_director_set_capital():
    """Director가 'capital' 키를 state_updates에 포함하면 _reconcile_capital 조기 리턴."""
    from unittest.mock import MagicMock, patch

    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    # FinanceHUDManager 체크 통과용
    from modules.core.genre_hud_manager import FinanceHUDManager
    mock_hud = MagicMock(spec=FinanceHUDManager)
    proc.ctx.sys.hud = mock_hud

    with patch.object(proc, "_extract_capital_from_manuscript") as mock_extract:
        proc._reconcile_capital(
            final_manuscript="자본금 200억이다.",
            ep_num=5,
            final_state_updates={"capital": "200억"},
        )
        # Director가 capital 설정 → extract 호출 안 됨
        mock_extract.assert_not_called()


def test_v73_skip_when_director_set_jabon():
    """'자본금' 키도 대소문자 무관하게 감지."""
    from unittest.mock import MagicMock, patch
    from modules.core.genre_hud_manager import FinanceHUDManager

    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    proc.ctx.sys.hud = MagicMock(spec=FinanceHUDManager)

    with patch.object(proc, "_extract_capital_from_manuscript") as mock_extract:
        proc._reconcile_capital(
            final_manuscript="자본금 200억",
            ep_num=3,
            final_state_updates={"자본금": "200억"},
        )
        mock_extract.assert_not_called()


def test_v73_runs_when_director_no_capital():
    """Director state_updates에 capital 없으면 정상 실행."""
    from unittest.mock import MagicMock
    from modules.core.genre_hud_manager import FinanceHUDManager

    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    mock_hud = MagicMock(spec=FinanceHUDManager)
    mock_hud.pro_data = {"capital": "100억"}
    proc.ctx.sys.hud = mock_hud

    # capital 없는 state_updates → 실행 진행 (크래시 없음만 확인)
    try:
        proc._reconcile_capital(
            final_manuscript="잔고 200억이 남아있었다.",
            ep_num=7,
            final_state_updates={"exp": 500},
        )
    except Exception as e:
        assert False, f"예외 발생: {e}"


# ── 방어2: 대사 제거 후 regex ────────────────────────────────────────────

def test_v73_dialogue_capital_excluded():
    """대사 속 타인 자산은 추출되지 않아야 한다."""
    manuscript = (
        "나레이션: 잔고 50억이 남아있다.\n"
        '"김사장 자산이 300억이나 된다고?" 그가 말했다.'
    )
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    # 대사(300억) 제거 → 나레이션(50억)만 남아야 함
    assert result == 50.0, f"expected 50.0, got {result}"


def test_v73_narration_capital_extracted():
    """나레이션 자본금은 정상 추출."""
    manuscript = "그의 잔고는 150억이었다. 충분한 실탄이었다."
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    assert result == 150.0, f"expected 150.0, got {result}"


def test_v73_dialogue_only_returns_none():
    """자본금 언급이 대사 내부에만 있으면 None 반환."""
    manuscript = '"잔고가 80억이래." 비서가 보고했다.'
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    assert result is None, f"expected None, got {result}"


def test_v73_no_capital_mention_returns_none():
    """자본금 언급 없으면 None."""
    assert Stage4PostProcessor._extract_capital_from_manuscript("오늘도 하루가 지났다.") is None
```

---

## 5) 실행 순서

```bash
# Phase 1 완료 후
python -m py_compile modules/core/stage4_post_processor.py

# Phase 2 완료 후
python -m py_compile modules/core/stage4_post_processor.py

# Phase 3 완료 후
pytest tests/test_v73_capital_fix.py -v

# ruff
ruff check modules/core/stage4_post_processor.py tests/test_v73_capital_fix.py

# 전체 회귀
pytest tests/ -q
```

---

## 6) 보고서 형식

출력: `docs/2026-03-04/V73-capital-fix-result.md`

```markdown
# V73 자본금 역동기화 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1 | stage4_post_processor.py | _reconcile_capital final_state_updates 파라미터 + Director 우선 방어 | ✅/❌ |
| 2 | stage4_post_processor.py | _DIALOGUE_RE 추가 + _extract_capital_from_manuscript 대사 제거 | ✅/❌ |
| 3 | test_v73_capital_fix.py | 7개 테스트 추가 | ✅/❌ |

## 검증 결과

- py_compile: 통과/실패
- 신규 테스트: N passed, N failed
- ruff: 위반 N건
- 전체 테스트: N passed, N failed (N skipped)
```

---

## 7) 합격 기준

- 신규 테스트 **7개 전부 PASS**
- 전체 테스트 **3,213+ passed, 0 failed**
- ruff 위반 **0건**
