# Codex Order: R5-2c — pre_director_checklist.py 잔여 추출

> **목표**: `pre_director_checklist.py` (1,109줄)에서 남은 6개 메서드를 2개 서브모듈로 추출
> **범위**: 서브모듈 2개 신규 + 호스트 수정 + 테스트 신규
> **전제**: R5-2a + R5-2b 완료
> **기존 추출**: R5-1a에서 5개 메서드 → `pre_director_manuscript_checker.py` (완료)

---

## 현재 구조 (1,109줄, R5-1a 이후)

```
# 데이터 정의 (L35-81)
CheckCategory          L35  (enum, 16줄)
CheckSeverity          L53  (enum, 6줄)
CheckItem              L61  (dataclass, 9줄)
ChecklistResult        L72  (dataclass, 10줄)

class PreDirectorChecklist:
  __init__()                    L119 (3줄)
  manuscript_checker (property) L123 (8줄) — R5-1a lazy
  check()                      L132 (46줄) — 메인 진입점
  _check_manuscript()           L180 (226줄) — 원고 체크 오케스트레이터

  # ── 남은 6개 메서드 (추출 대상) ──
  _check_narrative_flow()       L408 (123줄) — 서사 흐름 (폭주/정체)
  _check_npc_behavior_jump()    L533 (130줄) — NPC 행동 급변
  _check_blueprint()            L665 (124줄) — 블루프린트 구조 검증
  _check_sentence_variety()     L791 (81줄)  — 문두 반복
  _check_pacing_rhythm()        L874 (119줄) — 긴장-이완 리듬
  _check_setting_keywords()     L995 (93줄)  — 설정 키워드 검증

  get_feedback()                L1090 (20줄)
```

---

## 목표 구조 (2개 서브모듈 추가)

### Module 1: `pre_director_narrative_checker.py` (~350줄)

서사 품질 + NPC + 설정 키워드 검증.

| 이동 대상 | 줄수 | 설명 |
|----------|------|------|
| `_check_narrative_flow()` | 123 | 서사 폭주(조기 해결)/정체(반복 키워드) |
| `_check_npc_behavior_jump()` | 130 | NPC 관계 급변 (regex + blueprint 분석) |
| `_check_setting_keywords()` | 93 | 사망 NPC 행동, 미습득 기술, 아이템 |

### Module 2: `pre_director_style_checker.py` (~200줄)

문체 + 리듬 검증.

| 이동 대상 | 줄수 | 설명 |
|----------|------|------|
| `_check_sentence_variety()` | 81 | 연속 문두 반복 (3회 이상 WARNING) |
| `_check_pacing_rhythm()` | 119 | 3-섹션 긴장-이완 균형 분석 |

### `_check_blueprint()` — 호스트에 유지

`_check_blueprint()`(124줄)은 **블루프린트 전용** 코드 경로로, 원고 체크와 독립적. 현재 `check()` 메서드에서 `content_type == "blueprint"` 분기로 호출. 분리해도 좋지만 124줄이라 ROI가 낮으므로 **호스트에 유지**.

### 호스트 잔여 (~430줄)

```
PreDirectorChecklist:
  __init__()                     (3줄)
  manuscript_checker (property)  (8줄) — R5-1a
  narrative_checker (property)   (8줄) — R5-2c 신규
  style_checker (property)       (8줄) — R5-2c 신규
  check()                       (46줄)
  _check_manuscript()            (226줄) — 위임 호출 업데이트
  _check_blueprint()             (124줄) — 그대로 유지
  get_feedback()                 (20줄)
```

**총 감소**: 1,579줄(원본) → ~430줄 (3개 서브모듈 총 ~1,000줄 추출, **-73%**)

---

## 구현 상세

### 서브모듈 패턴 (R5-1a와 동일)

```python
"""[R5-2c] PreDirectorChecklist 서사 품질 체크 서브모듈."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity

if TYPE_CHECKING:
    from modules.core.pre_director_checklist import PreDirectorChecklist


class PreDirectorNarrativeChecker:
    """서사 품질 + NPC 행동 + 설정 키워드 체크."""

    def __init__(self, host: PreDirectorChecklist) -> None:
        self.host = host

    def _check_narrative_flow(self, content: str, context: dict) -> list[CheckItem]:
        # 원본 그대로, self.xxx → self.host.xxx (필요 시)
        ...
```

### 호스트 수정 — `_check_manuscript()` 내부 위임

`_check_manuscript()`에서 6개 메서드 호출을 서브모듈 위임으로 전환:

```python
# Before (현재)
items.extend(self._check_narrative_flow(content, context))
items.extend(self._check_npc_behavior_jump(content, context))
items.extend(self._check_setting_keywords(content, context))
items.extend(self._check_sentence_variety(content, context))
items.extend(self._check_pacing_rhythm(content, context))

# After
items.extend(self.narrative_checker._check_narrative_flow(content, context))
items.extend(self.narrative_checker._check_npc_behavior_jump(content, context))
items.extend(self.narrative_checker._check_setting_keywords(content, context))
items.extend(self.style_checker._check_sentence_variety(content, context))
items.extend(self.style_checker._check_pacing_rhythm(content, context))
```

### 주의사항

1. `_check_narrative_flow()` 내부에 `extract_keywords()`라는 **nested helper** 함수 정의가 있다. 서브모듈로 이동 시 함께 이동.

2. `_check_sentence_variety()` 내부에 `get_starter()`라는 **nested helper**가 있다. 함께 이동.

3. `_check_npc_behavior_jump()`은 `context.get("blueprint")` + `context.get("arc_data")`에 접근. 호스트 의존 없음 (context는 파라미터).

4. `_check_setting_keywords()`은 `context.get("blueprint")`, `context.get("arc_data")`, `context.get("dead_npcs")` 등에 접근. 역시 호스트 의존 없음.

5. 모든 메서드는 `list[CheckItem]`을 반환. `CheckItem`, `CheckCategory`, `CheckSeverity`를 서브모듈에서 import.

---

## 테스트

### 파일: `tests/test_pre_director_checklist_submodules.py`

```python
"""[R5-2c] PreDirectorChecklist 추가 서브모듈 단위 테스트."""
import pytest
from modules.core.pre_director_checklist import PreDirectorChecklist

@pytest.fixture
def checker():
    return PreDirectorChecklist()

# ── Narrative checker ──
class TestNarrativeChecker:
    def test_narrative_flow_normal(self, checker):
        """정상 서사는 경고 없음."""
        ms = "그는 천천히 걸었다. " * 100
        items = checker.narrative_checker._check_narrative_flow(ms, {})
        fails = [i for i in items if i.severity.value != "pass"]
        assert len(fails) == 0

    def test_npc_behavior_jump_no_blueprint(self, checker):
        """Blueprint 없으면 스킵."""
        items = checker.narrative_checker._check_npc_behavior_jump(
            "내용", {"blueprint": None}
        )
        assert len(items) == 0 or all(i.severity.value == "pass" for i in items)

    def test_setting_keywords_dead_npc(self, checker):
        """사망 NPC 행동 감지."""
        ms = "장무기가 검을 휘둘렀다."
        items = checker.narrative_checker._check_setting_keywords(
            ms, {"dead_npcs": ["장무기"]}
        )
        warns = [i for i in items if i.severity.value != "pass"]
        assert len(warns) >= 1

# ── Style checker ──
class TestStyleChecker:
    def test_sentence_variety_pass(self, checker):
        """다양한 문두는 통과."""
        ms = "그는 걸었다. 바람이 불었다. 검이 빛났다. 달이 떴다."
        items = checker.style_checker._check_sentence_variety(ms, {})
        fails = [i for i in items if i.severity.value == "fail"]
        assert len(fails) == 0

    def test_sentence_variety_repetition(self, checker):
        """반복 문두 감지."""
        ms = "그는 걸었다. 그는 뛰었다. 그는 멈췄다. 그는 돌았다. 그는 앉았다."
        items = checker.style_checker._check_sentence_variety(ms, {})
        warns = [i for i in items if i.severity.value != "pass"]
        assert len(warns) >= 1

    def test_pacing_rhythm_short_text(self, checker):
        """짧은 텍스트는 분석 스킵."""
        items = checker.style_checker._check_pacing_rhythm("짧다", {})
        assert len(items) == 0 or all(i.severity.value == "pass" for i in items)

# ── Integration ──
class TestIntegration:
    def test_check_manuscript_delegates(self, checker):
        """check()이 서브모듈을 통해 동작."""
        ms = "가" * 5000
        result = checker.check(
            content=ms,
            content_type="manuscript",
            context={"blueprint": {}, "arc_data": {}}
        )
        assert hasattr(result, "passed")

    def test_lazy_init_narrative(self, checker):
        assert checker._narrative_checker is None
        _ = checker.narrative_checker
        assert checker._narrative_checker is not None

    def test_lazy_init_style(self, checker):
        assert checker._style_checker is None
        _ = checker.style_checker
        assert checker._style_checker is not None

    def test_check_blueprint_still_works(self, checker):
        """_check_blueprint는 호스트에 유지 — 정상 동작."""
        result = checker.check(
            content='{"integrated_scenario": "test", "scene_breakdown": {"s1": {}}}',
            content_type="blueprint",
            context={}
        )
        assert hasattr(result, "passed")
```

**최소 10개 테스트** — Narrative 3 + Style 3 + Integration 4.

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -c "import py_compile; py_compile.compile('modules/core/pre_director_narrative_checker.py', doraise=True)"
python -c "import py_compile; py_compile.compile('modules/core/pre_director_style_checker.py', doraise=True)"

# Gate 2: import 정상
python -c "from modules.core.pre_director_checklist import PreDirectorChecklist; c=PreDirectorChecklist(); print(f'narrative={type(c.narrative_checker).__name__}, style={type(c.style_checker).__name__}')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_pre_director_checklist_submodules.py -v

# Gate 4: 기존 테스트 회귀
pytest tests/ -k "pre_director or continuity_modules" -v

# Gate 5: 전체 회귀
pytest tests/ -q

# Gate 6: 줄 수 확인
python -c "print(sum(1 for _ in open('modules/core/pre_director_checklist.py')))"
# 목표: ~430줄 이하

# Gate 7: pre-commit
pre-commit run --files modules/core/pre_director_checklist.py modules/core/pre_director_narrative_checker.py modules/core/pre_director_style_checker.py tests/test_pre_director_checklist_submodules.py
```

---

## 커밋

```
refactor(r5-2c): extract narrative + style checkers from pre_director_checklist (1,109→~430 lines, -61%)
```

push 포함.

---

## 실패 시

- `CheckItem` import 에러 → `from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity`
- nested helper 누락 → `extract_keywords()`, `get_starter()` 서브모듈 이동 확인
- `_check_manuscript()` 위임 경로 오류 → 호출 매핑 전수 확인
- 크래시 시 traceback + 원인만 보고 후 중단
