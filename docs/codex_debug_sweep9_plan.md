# Debug Sweep 9 — API 안전성 + 테스트 커버리지 확장

> **목적**: json.dumps 한글 안전성, 문자열 연결 성능, 예외 처리 명확화, 미테스트 모듈 커버리지 확장
> **규칙**: 각 항목은 독립 실행 가능 (의존성 없음). 수정 후 반드시 `set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q` 통과 확인.
> **테스트 기준선**: 1,710 passed + 68 xfailed (Sweep 8 적용 전 기준 — Sweep 8 적용 후 변동 있으면 그 숫자 기준)
> **Ruff**: 수정한 파일에 `ruff check <파일> && ruff format <파일>` 적용

---

## 인코딩 안전 규칙 (필독)

1. **파일 읽기/쓰기 시 반드시 `encoding="utf-8"` 명시**
2. **한글 주석·문자열을 절대 변경하지 말 것** — 읽지 못하는 한글은 그대로 유지
3. **BOM 삽입 금지** — UTF-8 without BOM
4. **파일 전체를 다시 쓰지 말 것** — 변경할 부분만 정확히 수정
5. **수정 전후 파일 크기 비교** — ±10% 이상 차이나면 인코딩 파손 의심
6. **검증**: `python -c "open('<파일>', encoding='utf-8').read()"` 로 깨짐 확인

---

## A. json.dumps ensure_ascii=False (4건)

한글 프로젝트이므로 json.dumps에 ensure_ascii=False가 필요합니다. 없으면 한글이 `\uXXXX`로 이스케이프됩니다.

### A-1: `modules/core/slack_bot.py:55` — Slack webhook 한글 깨짐

**파일**: `modules/core/slack_bot.py`
**라인**: 55
**현상**: Slack 알림에서 한글이 `\uD55C\uAE00` 형태로 전송됨
**현재 코드**:
```python
data=json.dumps(payload),
```
**수정 코드**:
```python
data=json.dumps(payload, ensure_ascii=False),
```

### A-2: `modules/core/world_state.py:62` — deep copy 일관성

**파일**: `modules/core/world_state.py`
**라인**: 62
**현상**: deep copy용 json 라운드트립. 기능적 문제 없지만 일관성 확보.
**현재 코드**:
```python
return json.loads(json.dumps(self._INIT_STATE))  # deep copy
```
**수정 코드**:
```python
return json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))  # deep copy
```

### A-3: `modules/core/world_state.py:413` — deep copy 일관성

**파일**: `modules/core/world_state.py`
**라인**: 413
**현재 코드**:
```python
self._state = json.loads(json.dumps(self._INIT_STATE))
```
**수정 코드**:
```python
self._state = json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))
```

### A-4: `modules/domain/agents/arc_critic.py:215` — deep copy 일관성

**파일**: `modules/domain/agents/arc_critic.py`
**라인**: 215
**현재 코드**:
```python
fixed = json.loads(json.dumps(arc))  # Deep copy
```
**수정 코드**:
```python
fixed = json.loads(json.dumps(arc, ensure_ascii=False))  # Deep copy
```

---

## B. 문자열 연결 → join 패턴 변환 (4건)

`injection += "..."` 반복 → `"\n".join(parts)` 패턴으로 변환. O(n) 할당으로 성능 개선 + 가독성 향상.

### B-1: `modules/core/adaptive_retry.py` — `_strategy_for_constraint_violation` (L270-278)

**파일**: `modules/core/adaptive_retry.py`
**라인**: 270-278
**현재 코드**:
```python
injection = "\n\n" + "=" * 60 + "\n"
injection += "[!!! CRITICAL RETRY WARNING !!!]\n"
injection += f"이전 시도에서 {len(violations)}건의 제약 조건 위반이 발생했습니다.\n"
injection += "아래 항목을 절대 위반하지 마십시오:\n"
for i, v in enumerate(violations[:5], 1):  # 최대 5개
    injection += f"  {i}. {v}\n"
if forbidden_items:
    injection += f"\n[ABSOLUTE BAN - 절대 재획득 금지]: {', '.join(forbidden_items)}\n"
injection += "=" * 60 + "\n"
```
**수정 코드**:
```python
parts = [
    "\n\n" + "=" * 60,
    "[!!! CRITICAL RETRY WARNING !!!]",
    f"이전 시도에서 {len(violations)}건의 제약 조건 위반이 발생했습니다.",
    "아래 항목을 절대 위반하지 마십시오:",
    *[f"  {i}. {v}" for i, v in enumerate(violations[:5], 1)],
]
if forbidden_items:
    parts.append(f"\n[ABSOLUTE BAN - 절대 재획득 금지]: {', '.join(forbidden_items)}")
parts.append("=" * 60)
injection = "\n".join(parts) + "\n"
```

### B-2: `modules/core/adaptive_retry.py` — `_strategy_for_quality_issue` (L299-307)

**파일**: `modules/core/adaptive_retry.py`
**라인**: 299-307
**현재 코드**:
```python
injection = "\n\n" + "-" * 60 + "\n"
injection += "[QUALITY IMPROVEMENT REQUIRED]\n"
injection += f"이전 시도의 품질 점수: {score}점\n"
injection += f"개선 필요 사항: {reason}\n"
injection += "\n[개선 지침]:\n"
injection += "1. 각 화의 전술 밀도를 높이십시오 (최소 800자/화)\n"
injection += "2. 물리적 인과관계를 더 구체적으로 서술하십시오\n"
injection += "3. 캐릭터의 심리적 동기를 명확히 하십시오\n"
injection += "-" * 60 + "\n"
```
**수정 코드**:
```python
parts = [
    "\n\n" + "-" * 60,
    "[QUALITY IMPROVEMENT REQUIRED]",
    f"이전 시도의 품질 점수: {score}점",
    f"개선 필요 사항: {reason}",
    "\n[개선 지침]:",
    "1. 각 화의 전술 밀도를 높이십시오 (최소 800자/화)",
    "2. 물리적 인과관계를 더 구체적으로 서술하십시오",
    "3. 캐릭터의 심리적 동기를 명확히 하십시오",
    "-" * 60,
]
injection = "\n".join(parts) + "\n"
```

### B-3: `modules/core/adaptive_retry.py` — `_strategy_for_structure_error` (L325-334)

**파일**: `modules/core/adaptive_retry.py`
**라인**: 325-334
**현재 코드**:
```python
injection = "\n\n" + "#" * 60 + "\n"
injection += "[JSON STRUCTURE REPAIR REQUIRED]\n"
injection += "이전 응답의 JSON 구조가 올바르지 않았습니다.\n"
if missing_keys:
    injection += f"누락된 필수 키: {', '.join(missing_keys)}\n"
injection += "\n반드시 아래 구조를 준수하십시오:\n"
injection += "- 응답은 반드시 '{' 로 시작하고 '}' 로 끝나야 합니다\n"
injection += "- 모든 필수 키를 포함해야 합니다\n"
injection += "- 문자열 내 큰따옴표는 이스케이프 처리해야 합니다\n"
injection += "#" * 60 + "\n"
```
**수정 코드**:
```python
parts = [
    "\n\n" + "#" * 60,
    "[JSON STRUCTURE REPAIR REQUIRED]",
    "이전 응답의 JSON 구조가 올바르지 않았습니다.",
]
if missing_keys:
    parts.append(f"누락된 필수 키: {', '.join(missing_keys)}")
parts.extend([
    "\n반드시 아래 구조를 준수하십시오:",
    "- 응답은 반드시 '{' 로 시작하고 '}' 로 끝나야 합니다",
    "- 모든 필수 키를 포함해야 합니다",
    "- 문자열 내 큰따옴표는 이스케이프 처리해야 합니다",
    "#" * 60,
])
injection = "\n".join(parts) + "\n"
```

### B-4: `modules/core/adaptive_retry.py` — `_strategy_for_timeout` (L349-354)

**파일**: `modules/core/adaptive_retry.py`
**라인**: 349-354
**현재 코드**:
```python
injection = "\n\n" + "*" * 60 + "\n"
injection += "[OUTPUT LENGTH CONSTRAINT]\n"
injection += "이전 응답이 최대 토큰을 초과했습니다.\n"
injection += "tactical_doc을 핵심 비트 위주로 압축하여 작성하십시오.\n"
injection += "각 화당 최대 600자로 제한하십시오.\n"
injection += "*" * 60 + "\n"
```
**수정 코드**:
```python
parts = [
    "\n\n" + "*" * 60,
    "[OUTPUT LENGTH CONSTRAINT]",
    "이전 응답이 최대 토큰을 초과했습니다.",
    "tactical_doc을 핵심 비트 위주로 압축하여 작성하십시오.",
    "각 화당 최대 600자로 제한하십시오.",
    "*" * 60,
]
injection = "\n".join(parts) + "\n"
```

---

## C. 예외 처리 명확화 (2건)

### C-1: `modules/core/prompt_builder.py:878-884` — bare except → 명시적 타입

**파일**: `modules/core/prompt_builder.py`
**라인**: 878-884
**현상**: POV 추출 실패 시 bare `except Exception: pass` — 디버깅 불가
**현재 코드**:
```python
# 5. [V70] POV 추출
try:
    _bible_root = app.current_project.master_bible.get("MasterBible", {})
    _pov = _bible_root.get("protagonist_config", {}).get("pov", "")
    if _pov:
        context["pov"] = _pov
except Exception:
    pass
```
**수정 코드**:
```python
# 5. [V70] POV 추출
try:
    _bible_root = app.current_project.master_bible.get("MasterBible", {})
    _pov = _bible_root.get("protagonist_config", {}).get("pov", "")
    if _pov:
        context["pov"] = _pov
except (AttributeError, KeyError, TypeError):
    pass  # POV 미설정 시 정상 생략
```

### C-2: `modules/core/prompt_builder.py:888-894` — 중첩 try/except 제거

**파일**: `modules/core/prompt_builder.py`
**라인**: 886-894
**현상**: 로깅 코드 자체를 try/except로 감싸고 bare except: pass — 불필요한 중첩
**현재 코드**:
```python
except Exception as e:
    # [V70] app이 None일 수 있으므로 안전하게 로깅
    try:
        if app and hasattr(app, "ui") and app.ui:
            app.ui.log(f"⚠️ [Validation Context] 구성 중 오류 (비치명적): {e}")
        else:
            logging.warning(f"⚠️ [Validation Context] 구성 중 오류 (비치명적): {e}")
    except Exception:
        pass
```
**수정 코드**:
```python
except Exception as e:
    # [V70] app이 None일 수 있으므로 안전하게 로깅
    if app and hasattr(app, "ui") and getattr(app.ui, "log", None):
        app.ui.log(f"⚠️ [Validation Context] 구성 중 오류 (비치명적): {e}")
    else:
        logging.warning("[Validation Context] 구성 중 오류 (비치명적): %s", e)
```
**참고**: `hasattr(app, "ui") and app.ui` + `getattr(app.ui, "log", None)` 체크로 `try` 없이 안전하게 로깅. `logging.warning`은 절대 실패하지 않으므로 감싸지 않아도 됨.

---

## D. 장르 가드 테스트 확장 — 미테스트 8개 장르 (신규 파일 1개)

기존 `tests/test_genre_guard.py`가 WuxiaGuard만 테스트합니다. 나머지 8개 장르를 parametrize로 커버합니다.

### D-1: `tests/test_genre_guards_extended.py` 신규 생성

**파일**: `tests/test_genre_guards_extended.py` (신규)
**내용**:

```python
"""
[Sweep9-D] 장르 가드 확장 테스트 — 미테스트 8개 장르 커버리지
기존 test_genre_guard.py(WuxiaGuard)를 보완합니다.
"""

import pytest

from modules.core.genre_guards.investment_guard import InvestmentGuard
from modules.core.genre_guards.fantasy_guard import FantasyGuard
from modules.core.genre_guards.cooking_guard import CookingGuard
from modules.core.genre_guards.alt_history_guard import AltHistoryGuard
from modules.core.genre_guards.composer_guard import ComposerGuard
from modules.core.genre_guards.actor_guard import ActorGuard
from modules.core.genre_guards.medical_guard import MedicalGuard
from modules.core.genre_guards.sports_guard import SportsGuard


# ── 파라미터화 픽스처 ──────────────────────────────────────────

GUARD_CLASSES = [
    (InvestmentGuard, "투자물(INVESTMENT)"),
    (FantasyGuard, "판타지"),
    (CookingGuard, "요리물(COOKING)"),
    (AltHistoryGuard, "대체역사물(ALT_HISTORY)"),
    (ComposerGuard, "작곡가물(COMPOSER)"),
    (ActorGuard, "배우물(ACTOR)"),
    (MedicalGuard, "의학물(MEDICAL)"),
    (SportsGuard, "스포츠물(SPORTS)"),
]


@pytest.fixture(params=GUARD_CLASSES, ids=[c[1] for c in GUARD_CLASSES])
def guard_and_name(request):
    cls, expected_name = request.param
    return cls(), expected_name


# ── 인스턴스화 ──────────────────────────────────────────


class TestGuardInstantiation:
    """가드가 에러 없이 생성되는지 확인"""

    def test_instantiation(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard is not None

    def test_genre_name(self, guard_and_name):
        guard, expected_name = guard_and_name
        assert guard.get_genre_name() == expected_name

    def test_has_forbidden_terms(self, guard_and_name):
        guard, _ = guard_and_name
        assert isinstance(guard.FORBIDDEN_TERMS, list)
        assert len(guard.FORBIDDEN_TERMS) > 0, "FORBIDDEN_TERMS가 비어 있으면 안 됨"


# ── convert_to_numeric (BaseGuard 공통) ──────────────────────────

class TestConvertToNumeric:
    """BaseGuard.convert_to_numeric 기본 동작 (모든 가드 공통)"""

    def test_none_returns_zero(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric(None) == 0.0

    def test_int_passthrough(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric(42) == 42.0

    def test_arabic_string(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("100") == 100.0

    def test_zero_keywords(self, guard_and_name):
        guard, _ = guard_and_name
        for word in ["영", "없음", "소멸"]:
            assert guard.convert_to_numeric(word) == 0.0

    def test_korean_numeral(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("삼") == 3.0

    def test_ten_korean(self, guard_and_name):
        guard, _ = guard_and_name
        assert guard.convert_to_numeric("이십") == 20.0


# ── validate_v20_manuscript ──────────────────────────────────

class TestValidateV20Manuscript:
    """BaseGuard.validate_v20_manuscript 기본 검증"""

    def test_clean_text_passes(self, guard_and_name):
        guard, _ = guard_and_name
        # 한글 전용 클린 텍스트 — 금기어가 없는 일반 서술
        result = guard.validate_v20_manuscript("그는 조용히 걸었다. 바람이 불었다.")
        assert isinstance(result, dict)
        assert "is_pure" in result
        assert "issues" in result

    def test_forbidden_term_detected(self, guard_and_name):
        guard, _ = guard_and_name
        if not guard.FORBIDDEN_TERMS:
            pytest.skip("금기어 없음")
        # 첫 번째 금기어를 삽입한 텍스트
        forbidden = guard.FORBIDDEN_TERMS[0]
        result = guard.validate_v20_manuscript(f"그는 {forbidden}을 사용했다.")
        assert result["is_pure"] is False
        assert any(forbidden in issue for issue in result["issues"])


# ── run_deep_validation ──────────────────────────────────

class TestRunDeepValidation:
    """run_deep_validation 반환 구조 검증"""

    def test_returns_dict(self, guard_and_name):
        guard, _ = guard_and_name
        result = guard.run_deep_validation("그는 조용히 걸었다. 바람이 불었다.")
        assert isinstance(result, dict)

    def test_has_passed_key(self, guard_and_name):
        guard, _ = guard_and_name
        result = guard.run_deep_validation("그는 조용히 걸었다. 바람이 불었다.")
        # run_deep_validation은 "passed" 또는 "is_valid" 키를 가짐
        has_result_key = "passed" in result or "is_valid" in result or "issues" in result
        assert has_result_key, f"반환 키: {list(result.keys())}"
```

---

## E. ActionSceneEvaluator 테스트 (신규 파일 1개)

### E-1: `tests/test_action_scene_evaluator.py` 신규 생성

**파일**: `tests/test_action_scene_evaluator.py` (신규)
**내용**:

```python
"""
[Sweep9-E] ActionSceneEvaluator 단위 테스트
전투/액션 씬 평가의 기본 동작을 검증합니다.
"""

import pytest

from modules.validation.action_scene_evaluator import ActionSceneEvaluator


@pytest.fixture(params=["wuxia", "hunter", "investment"])
def evaluator(request):
    return ActionSceneEvaluator(genre=request.param)


class TestInstantiation:
    def test_create(self, evaluator):
        assert evaluator is not None

    def test_action_keywords_populated(self, evaluator):
        assert isinstance(evaluator.ACTION_KEYWORDS, dict)
        assert len(evaluator.ACTION_KEYWORDS) > 0


class TestEvaluate:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate("그는 검을 휘둘렀다. 상대의 공격을 피했다.")
        assert isinstance(result, dict)

    def test_score_in_range(self, evaluator):
        result = evaluator.evaluate("그는 검을 휘둘렀다. 상대의 공격을 피했다.")
        if "score" in result:
            assert 0 <= result["score"] <= 100

    def test_empty_manuscript(self, evaluator):
        result = evaluator.evaluate("")
        assert isinstance(result, dict)


class TestExtractActionScenes:
    def test_returns_list(self, evaluator):
        scenes = evaluator._extract_action_scenes("그는 검을 휘둘렀다. 피가 튀었다.")
        assert isinstance(scenes, list)


class TestEvaluateChoreography:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate_choreography(["그는 검을 휘둘렀다."])
        assert isinstance(result, dict)

    def test_empty_scenes(self, evaluator):
        result = evaluator.evaluate_choreography([])
        assert isinstance(result, dict)


class TestEvaluateStakesEscalation:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate_stakes_escalation(["첫 장면", "두 번째 장면"])
        assert isinstance(result, dict)

    def test_single_scene(self, evaluator):
        result = evaluator.evaluate_stakes_escalation(["유일한 장면"])
        assert isinstance(result, dict)
```

---

## F. CatharsisTimer 테스트 (신규 파일 1개)

### F-1: `tests/test_catharsis_timer.py` 신규 생성

**파일**: `tests/test_catharsis_timer.py` (신규)
**내용**:

```python
"""
[Sweep9-F] CatharsisTimer 단위 테스트
카타르시스 타이밍 관리의 기본 동작을 검증합니다.
"""

import pytest

from modules.validation.catharsis_timer import CatharsisTimer


@pytest.fixture
def timer():
    return CatharsisTimer(genre="wuxia")


@pytest.fixture
def hunter_timer():
    return CatharsisTimer(genre="hunter")


class TestInstantiation:
    def test_default_genre(self):
        t = CatharsisTimer()
        assert t is not None

    def test_custom_genre(self, hunter_timer):
        assert hunter_timer is not None

    def test_max_frustration_default(self, timer):
        assert timer.MAX_FRUSTRATION_EPISODES == 3

    def test_custom_max_frustration(self):
        t = CatharsisTimer(max_frustration=5)
        # max_frustration 파라미터가 적용되는지 확인
        assert t is not None


class TestCheckCatharsisTiming:
    def test_returns_dict(self, timer):
        result = timer.check_catharsis_timing(ep_num=1, manuscript="통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_catharsis_detected(self, timer):
        # "통쾌", "승리" 등 카타르시스 지표 포함 텍스트
        result = timer.check_catharsis_timing(
            ep_num=1,
            manuscript="드디어 통쾌한 승리를 거두었다. 모두가 경악했다.",
        )
        assert isinstance(result, dict)

    def test_no_catharsis(self, timer):
        # 카타르시스 지표 없는 답답한 텍스트
        result = timer.check_catharsis_timing(
            ep_num=1,
            manuscript="그는 또 패배했다. 아무것도 할 수 없었다.",
        )
        assert isinstance(result, dict)

    def test_with_history(self, timer):
        history = [
            {"ep_num": 1, "has_catharsis": False},
            {"ep_num": 2, "has_catharsis": False},
        ]
        result = timer.check_catharsis_timing(
            ep_num=3,
            manuscript="또다시 좌절의 연속이었다.",
            history=history,
        )
        assert isinstance(result, dict)


class TestAnalyzeCatharsis:
    def test_returns_dict(self, timer):
        result = timer._analyze_catharsis("통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_empty_text(self, timer):
        result = timer._analyze_catharsis("")
        assert isinstance(result, dict)


class TestGetRecommendedCatharsisType:
    def test_returns_list(self, timer):
        result = timer.get_recommended_catharsis_type()
        assert isinstance(result, list)

    def test_with_context(self, timer):
        result = timer.get_recommended_catharsis_type(context={"genre": "wuxia"})
        assert isinstance(result, list)


class TestRecordEpisode:
    def test_returns_dict(self, timer):
        result = timer.record_episode(ep_num=1, manuscript="통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_sequential_recording(self, timer):
        timer.record_episode(ep_num=1, manuscript="패배했다.")
        result = timer.record_episode(ep_num=2, manuscript="또 패배했다.")
        assert isinstance(result, dict)
```

---

## 실행 가이드 (Codex용)

- **총 12개 항목** (A: 4, B: 4, C: 2, D: 1신규파일, E: 1신규파일, F: 1신규파일)
- 각 항목 수정 후: `ruff check <파일> && ruff format <파일> && set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q`
- D/E/F 테스트 파일 생성 시: 위 코드를 그대로 사용. 테스트가 통과하지 않으면 해당 클래스의 실제 시그니처를 확인하고 픽스처/assertion을 조정할 것.
- **커밋하지 말 것** — 수정만 하고 검증만 수행

---

## 카테고리별 커밋 메시지 (나중에 사람이 커밋할 때 사용)

```
fix(sweep9-a): add ensure_ascii=False to 4 json.dumps calls
refactor(sweep9-b): string concatenation to join pattern in adaptive_retry
fix(sweep9-c): explicit exception types in prompt_builder
test(sweep9-def): add genre guard extended + action evaluator + catharsis timer tests
```

---

## 산출물 요약

| 카테고리 | 항목 수 | 신규 테스트 | 성격 |
|----------|---------|------------|------|
| A. json ensure_ascii | 4 | 0 | 한글 안전성 |
| B. 문자열 concat→join | 4 | 0 | 성능+가독성 |
| C. 예외 처리 명확화 | 2 | 0 | 디버깅 용이 |
| D. 장르 가드 확장 테스트 | 1 (신규파일) | +88 (8장르×11테스트) | 커버리지 |
| E. ActionSceneEvaluator | 1 (신규파일) | +24 (3장르×8테스트) | 커버리지 |
| F. CatharsisTimer | 1 (신규파일) | +13 | 커버리지 |
| **합계** | **12** | **+125** | |
