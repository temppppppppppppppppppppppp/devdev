# Codex Order: D-3 문체 분석 → Guard 자동생성 연동

> **목표**: StyleGuide 데이터로부터 Guard 검증 규칙을 자동 생성하여 Director 심사에 반영
> **범위**: 신규 1파일 + 수정 2파일 + 테스트 1파일
> **위험도**: 낮음 (기존 Guard 체인에 선택적 래퍼 추가, 비활성 시 무영향)

---

## 배경

**현재 두 서브시스템이 단절되어 있음:**

| 서브시스템 | 역할 | 소비자 |
|-----------|------|--------|
| StyleGuide (`style_extractor.py`) | 문체 DNA 18개 필드 추출 | Chief Writer (to_prompt() 주입) |
| GenreGuard (`base_guard.py` + 10개 구현체) | 장르 금기어/일관성 검증 | Director (run_deep_validation()) |

**문제**: Chief Writer에 문체 규칙을 주입하지만, Director의 Guard는 그 규칙 위반을 감지 못함.
예: `anti_ai_patterns`에 "그의 눈동자가 흔들렸다"가 있어도, Guard는 이를 검증하지 않음.

**해결**: StyleGuard 래퍼 클래스가 기존 장르 Guard를 감싸고, StyleGuide에서 추출한 추가 규칙을 검증.

---

## 설계

```
기존 Guard 체인:
  create_genre_guard("wuxia") → WuxiaGuard
  Director → guard.run_deep_validation(manuscript, state)

D-3 이후:
  create_genre_guard("wuxia") → WuxiaGuard (base_guard)
  StyleGuide 존재 시:
    StyleGuard(base_guard, style_guide) → 래퍼
    Director → style_guard.run_deep_validation(manuscript, state)
      1. base_guard.run_deep_validation() 호출 (기존 장르 검증)
      2. + anti_ai_patterns 매칭 (MEDIUM)
      3. + forbidden_expressions 매칭 (MEDIUM)
      4. + 문장 길이 분포 편차 경고 (LOW, advisory)
```

**핵심 원칙:**
- 기존 장르 Guard를 **대체하지 않고 래핑** (기존 검증 100% 보존)
- 문체 기반 위반은 **MEDIUM/LOW** (HIGH가 아님) — advisory 성격
- StyleGuide 미존재 시 래핑 안 함 (기존 동작 100% 유지)

---

## 수정/생성 파일

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/core/genre_guards/style_guard.py` | **신규** — StyleGuard 래퍼 클래스 | ~130줄 |
| `modules/core/genre_guards/__init__.py` | 수정 — export 추가 | ~3줄 |
| `main_a.py` | 수정 — Guard 등록 시 StyleGuard 래핑 | ~12줄 |
| `tests/test_style_guard.py` | **신규** — 테스트 | ~120줄 |

---

## 상세 구현

### 1. `modules/core/genre_guards/style_guard.py` (신규)

```python
"""
[D-3] 문체 기반 Guard 래퍼 — StyleGuide에서 추출한 규칙으로 추가 검증.

기존 장르 Guard를 래핑하여:
1. 장르 검증 (기존 100% 유지)
2. + anti_ai_patterns 위반 감지 (MEDIUM)
3. + forbidden_expressions 위반 감지 (MEDIUM)
4. + 문장 길이 분포 편차 경고 (LOW)
"""

import logging
import re
from typing import Any

from .base_guard import BaseGuard

_logger = logging.getLogger(__name__)

# 문장 분리 정규식 (한국어)
_SENTENCE_SPLIT = re.compile(r"[.!?。]+\s*")

# 문장 길이 분류 기준 (글자 수)
_SHORT_THRESHOLD = 20
_LONG_THRESHOLD = 50


class StyleGuard(BaseGuard):
    """[D-3] StyleGuide 기반 추가 검증 래퍼.

    기존 장르 Guard를 내부에 보유하고, run_deep_validation() 시
    장르 검증 결과에 문체 검증 결과를 추가.
    """

    def __init__(self, base_guard: BaseGuard, style_guide) -> None:
        """
        Args:
            base_guard: 기존 장르 Guard 인스턴스 (WuxiaGuard 등)
            style_guide: StyleGuide 데이터클래스 인스턴스
        """
        super().__init__()
        self._base = base_guard
        self._sg = style_guide

        # base guard 속성 복사 (Director가 직접 접근하는 경우 대비)
        self.FORBIDDEN_TERMS = base_guard.FORBIDDEN_TERMS
        self.ALLOWED_TERMS = base_guard.ALLOWED_TERMS
        self.MANDATORY_CONCEPTS = base_guard.MANDATORY_CONCEPTS

        # StyleGuide에서 검증 규칙 추출
        self._anti_ai = [p for p in (style_guide.anti_ai_patterns or []) if len(p) >= 4]
        self._forbidden_expr = [e for e in (style_guide.forbidden_expressions or []) if len(e) >= 2]
        self._target_sentence_length = style_guide.sentence_length or "medium"

        _logger.info(
            "[D-3] StyleGuard 초기화: anti_ai=%d, forbidden=%d, target_len=%s",
            len(self._anti_ai),
            len(self._forbidden_expr),
            self._target_sentence_length,
        )

    # ── BaseGuard 인터페이스 위임 ──────────────────────────────

    def get_genre_name(self) -> str:
        base_name = self._base.get_genre_name()
        return f"{base_name}+Style"

    def get_v20_purism_prompt(self) -> str:
        return self._base.get_v20_purism_prompt()

    def get_impossible_actions(self, current_state: dict = None) -> list[dict]:
        return self._base.get_impossible_actions(current_state or {})

    def get_justification_patterns(self) -> list[str]:
        return self._base.get_justification_patterns()

    def get_hierarchy_rules(self) -> dict:
        return self._base.get_hierarchy_rules()

    def check_state_action_consistency(self, manuscript: str, current_state: dict) -> dict:
        return self._base.check_state_action_consistency(manuscript, current_state)

    # ── 핵심: 통합 검증 ───────────────────────────────────────

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """기존 장르 검증 + 문체 기반 추가 검증."""
        # 1. 기존 장르 Guard 검증 (100% 위임)
        result = self._base.run_deep_validation(manuscript, current_state)
        violations = result.get("violations", [])

        # 2. Anti-AI 패턴 검증
        for pattern in self._anti_ai:
            if pattern in manuscript:
                violations.append({
                    "type": "style_anti_ai",
                    "severity": "MEDIUM",
                    "message": f"[Style] AI 패턴 감지: '{pattern}'",
                })

        # 3. 금지 표현 검증
        for expr in self._forbidden_expr:
            if expr in manuscript:
                violations.append({
                    "type": "style_forbidden_expression",
                    "severity": "MEDIUM",
                    "message": f"[Style] 금지 표현 감지: '{expr}'",
                })

        # 4. 문장 길이 분포 편차 경고
        length_warning = self._check_sentence_length_distribution(manuscript)
        if length_warning:
            violations.append({
                "type": "style_length_deviation",
                "severity": "LOW",
                "message": length_warning,
            })

        # 결과 재구성
        has_critical = any(v.get("severity") == "HIGH" for v in violations)
        summary_parts = [v.get("message", "") for v in violations[:5]]
        summary = "; ".join(summary_parts) if summary_parts else "검증 통과"
        feedback = ""
        if violations:
            feedback = f"[{self.get_genre_name()} Guard] {len(violations)}건 위반 발견: {summary}"

        return {
            "has_critical": has_critical,
            "violations": violations,
            "summary": summary,
            "feedback": feedback,
        }

    # ── 문장 길이 분포 분석 ────────────────────────────────────

    def _check_sentence_length_distribution(self, manuscript: str) -> str:
        """문장 길이 분포가 StyleGuide 목표에서 크게 벗어나면 경고."""
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(manuscript) if len(s.strip()) >= 5]
        if len(sentences) < 10:
            return ""

        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths)

        # 목표 평균 범위 (sentence_length 필드 기준)
        targets = {
            "short": (10, 25),
            "medium": (20, 45),
            "long": (35, 70),
        }
        target_range = targets.get(self._target_sentence_length, (20, 45))

        if avg_len < target_range[0] * 0.6:
            return f"[Style] 문장 평균 길이({avg_len:.0f}자)가 목표({self._target_sentence_length})보다 지나치게 짧음"
        if avg_len > target_range[1] * 1.5:
            return f"[Style] 문장 평균 길이({avg_len:.0f}자)가 목표({self._target_sentence_length})보다 지나치게 긺"

        return ""
```

---

### 2. `modules/core/genre_guards/__init__.py` — export 추가

**현재 (L54-66):**
```python
__all__ = [
    "WuxiaGuard",
    "HunterGuard",
    "InvestmentGuard",
    "FantasyGuard",
    "ComposerGuard",
    "CookingGuard",
    "AltHistoryGuard",
    "ActorGuard",
    "SportsGuard",
    "MedicalGuard",
    "create_genre_guard",
]
```

**수정 후:**
```python
from .style_guard import StyleGuard

__all__ = [
    "WuxiaGuard",
    "HunterGuard",
    "InvestmentGuard",
    "FantasyGuard",
    "ComposerGuard",
    "CookingGuard",
    "AltHistoryGuard",
    "ActorGuard",
    "SportsGuard",
    "MedicalGuard",
    "StyleGuard",
    "create_genre_guard",
]
```

> `from .style_guard import StyleGuard`를 기존 import 블록 마지막에 추가.
> `__all__`에 `"StyleGuard"` 추가.

---

### 3. `main_a.py` — Guard 등록 시 StyleGuard 래핑

**현재 (L1403-1406):**
```python
            # [V60.90] Director에 Guard 연결 (장르별 특화 검증용)
                if hasattr(self.sys, "guard") and self.sys.guard:
                    self.agents["director"].set_guard(self.sys.guard)
                    self.ui.log("   🛡️ Director Guard 연결 완료")
```

**수정 후:**
```python
            # [V60.90] Director에 Guard 연결 (장르별 특화 검증용)
                if hasattr(self.sys, "guard") and self.sys.guard:
                    _guard = self.sys.guard
                    # [D-3] StyleGuide 존재 시 StyleGuard 래핑
                    try:
                        _sg_data = self.current_project.load_v20_anchor("style_guide")
                        if _sg_data and isinstance(_sg_data, dict):
                            from modules.core.genre_guards import StyleGuard
                            from modules.core.stage0 import StyleGuide
                            _sg = StyleGuide.from_dict(_sg_data)
                            _guard = StyleGuard(_guard, _sg)
                            self.ui.log("   🎨 StyleGuard 래핑 완료 (문체 기반 검증 활성)")
                    except Exception as e:
                        logging.warning(f"[D-3] StyleGuard 래핑 실패 (장르 Guard만 사용): {e}")
                    self.agents["director"].set_guard(_guard)
                    self.ui.log("   🛡️ Director Guard 연결 완료")
```

> **핵심**: style_guide anchor가 있으면 래핑, 없으면 기존 guard 그대로 전달.
> try/except로 감싸서 StyleGuard 생성 실패 시에도 기존 guard 사용 보장.

---

## 테스트

### `tests/test_style_guard.py` (신규, ~120줄)

```python
"""[D-3] StyleGuard 래퍼 테스트."""
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class MockStyleGuide:
    """StyleGuide 최소 mock."""
    anti_ai_patterns: list = None
    forbidden_expressions: list = None
    sentence_length: str = "medium"
    signature_expressions: list = None
    tone: str = "진지"
    pov: str = "3인칭"
    sentence_rhythm: str = ""
    emotion_rendering: str = ""
    dialogue_narration_pattern: str = ""

    def __post_init__(self):
        if self.anti_ai_patterns is None:
            self.anti_ai_patterns = []
        if self.forbidden_expressions is None:
            self.forbidden_expressions = []
        if self.signature_expressions is None:
            self.signature_expressions = []


class MockBaseGuard:
    """BaseGuard 최소 mock."""

    def __init__(self):
        self.FORBIDDEN_TERMS = ["시스템", "로그인"]
        self.ALLOWED_TERMS = []
        self.MANDATORY_CONCEPTS = []

    def get_genre_name(self):
        return "TEST"

    def get_v20_purism_prompt(self):
        return "test prompt"

    def get_impossible_actions(self, current_state=None):
        return []

    def get_justification_patterns(self):
        return []

    def get_hierarchy_rules(self):
        return {}

    def check_state_action_consistency(self, manuscript, current_state):
        return {"violations": []}

    def run_deep_validation(self, manuscript, current_state=None):
        violations = []
        for term in self.FORBIDDEN_TERMS:
            if term in manuscript:
                violations.append({
                    "type": "forbidden_term",
                    "severity": "HIGH",
                    "message": f"금기어 '{term}' 발견",
                })
        return {
            "has_critical": any(v["severity"] == "HIGH" for v in violations),
            "violations": violations,
            "summary": "",
            "feedback": "",
        }


class TestStyleGuardInit:
    """StyleGuard 초기화 테스트."""

    def test_wraps_base_guard(self):
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)
        assert "TEST" in guard.get_genre_name()
        assert "Style" in guard.get_genre_name()

    def test_copies_base_forbidden_terms(self):
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.FORBIDDEN_TERMS == ["시스템", "로그인"]

    def test_filters_short_patterns(self):
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["abc", "네 글자 이상 패턴"])
        guard = StyleGuard(base, sg)
        assert len(guard._anti_ai) == 1  # "abc" (3자)는 필터됨


class TestStyleGuardValidation:
    """StyleGuard 검증 로직 테스트."""

    def test_base_guard_violations_preserved(self):
        """기존 장르 검증 결과가 보존됨."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("이 원고에 시스템 오류가 있습니다.")
        assert result["has_critical"] is True
        assert any(v["type"] == "forbidden_term" for v in result["violations"])

    def test_anti_ai_pattern_detected(self):
        """anti_ai_patterns 위반 감지."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그의 눈동자가 흔들렸다. 무슨 일이 일어난 것일까.")
        style_violations = [v for v in result["violations"] if v["type"] == "style_anti_ai"]
        assert len(style_violations) == 1
        assert style_violations[0]["severity"] == "MEDIUM"

    def test_forbidden_expression_detected(self):
        """forbidden_expressions 위반 감지."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(forbidden_expressions=["마치 ~처럼", "한편으로는"])
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("그는 한편으로는 기뻤지만 슬프기도 했다.")
        style_violations = [v for v in result["violations"] if v["type"] == "style_forbidden_expression"]
        assert len(style_violations) == 1

    def test_no_false_positive_when_clean(self):
        """위반 없는 원고에서 style 위반 0건."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(
            anti_ai_patterns=["그의 눈동자가 흔들렸다"],
            forbidden_expressions=["한편으로는"],
        )
        guard = StyleGuard(base, sg)

        result = guard.run_deep_validation("검은 바람이 불었다. 이청풍은 검을 뽑았다.")
        style_violations = [v for v in result["violations"] if v["type"].startswith("style_")]
        assert len(style_violations) == 0

    def test_sentence_length_too_short_warning(self):
        """문장이 지나치게 짧으면 LOW 경고."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(sentence_length="long")
        guard = StyleGuard(base, sg)

        # 매우 짧은 문장 20개 (평균 ~8자)
        short_text = ". ".join(["짧은 문장이다"] * 20) + "."
        result = guard.run_deep_validation(short_text)
        length_violations = [v for v in result["violations"] if v["type"] == "style_length_deviation"]
        assert len(length_violations) == 1
        assert length_violations[0]["severity"] == "LOW"

    def test_sentence_length_ok_no_warning(self):
        """적절한 문장 길이면 경고 없음."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(sentence_length="medium")
        guard = StyleGuard(base, sg)

        # 중간 길이 문장 (평균 ~25자)
        medium_text = ". ".join(["이청풍은 새벽녘에 눈을 떴다, 검을 잡았다"] * 15) + "."
        result = guard.run_deep_validation(medium_text)
        length_violations = [v for v in result["violations"] if v["type"] == "style_length_deviation"]
        assert len(length_violations) == 0

    def test_style_violations_are_not_critical(self):
        """문체 위반은 has_critical=False (MEDIUM/LOW만)."""
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide(anti_ai_patterns=["그의 눈동자가 흔들렸다"])
        guard = StyleGuard(base, sg)

        # 장르 금기어 없고, 문체 위반만 있는 원고
        result = guard.run_deep_validation("그의 눈동자가 흔들렸다. 바람이 불었다.")
        assert result["has_critical"] is False  # MEDIUM은 critical 아님


class TestStyleGuardDelegation:
    """BaseGuard 인터페이스 위임 테스트."""

    def test_delegates_purism_prompt(self):
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.get_v20_purism_prompt() == "test prompt"

    def test_delegates_impossible_actions(self):
        from modules.core.genre_guards.style_guard import StyleGuard
        base = MockBaseGuard()
        sg = MockStyleGuide()
        guard = StyleGuard(base, sg)
        assert guard.get_impossible_actions() == []
```

---

## 동작 원리

```
프로젝트 시작 → main_a.py L897-901
  → create_genre_guard("wuxia") → WuxiaGuard 생성

에이전트 등록 → main_a.py L1403-1414
  → style_guide anchor 로드
  → StyleGuide.from_dict(data)
  → StyleGuard(WuxiaGuard, style_guide) 래핑
  → Director.set_guard(style_guard)

원고 심사 → Director → director_auditor.py L82
  → style_guard.run_deep_validation(manuscript, state)
    → WuxiaGuard.run_deep_validation()  (기존 장르 검증)
    → + anti_ai_patterns 매칭            (문체 검증 추가)
    → + forbidden_expressions 매칭       (문체 검증 추가)
    → + 문장 길이 분포 경고              (문체 검증 추가)
  → 통합 결과 반환
```

---

## 주의사항

1. **StyleGuard는 BaseGuard를 상속** — Director가 `isinstance(guard, BaseGuard)` 검사를 하는 경우 대비.
2. **anti_ai_patterns 최소 길이 4자** — 너무 짧은 패턴은 오탐 위험 (예: "은", "의").
3. **forbidden_expressions 최소 길이 2자** — 한국어 특성상 2자도 의미 있는 단어.
4. **문장 길이 검사 최소 10문장** — 너무 짧은 원고에서는 통계적 의미 없으므로 skip.
5. **MEDIUM/LOW 전용** — 문체 위반은 Director에 advisory로만 전달. REJECT 유발 안 함.
6. **main_a.py 래핑 try/except** — StyleGuard 생성 실패 시 기존 Guard만 사용 (비차단).

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/genre_guards/style_guard.py
python -m py_compile modules/core/genre_guards/__init__.py
python -m py_compile main_a.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_style_guard.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 5: pre-commit
pre-commit run --files modules/core/genre_guards/style_guard.py modules/core/genre_guards/__init__.py main_a.py tests/test_style_guard.py
```

---

## 체크리스트

- [ ] `style_guard.py` 신규 생성 (~130줄)
- [ ] `__init__.py` export 추가 (import + __all__)
- [ ] `main_a.py` L1403-1406 StyleGuard 래핑 로직 추가
- [ ] `test_style_guard.py` 신규 생성 (11건)
- [ ] 문체 위반 severity는 MEDIUM/LOW만 (HIGH 없음)
- [ ] StyleGuide 미존재 시 기존 동작 100% 유지
- [ ] Gate 1-5 전체 통과
- [ ] 커밋: `feat(guard): add StyleGuard wrapper for style-based validation (D-3)`
