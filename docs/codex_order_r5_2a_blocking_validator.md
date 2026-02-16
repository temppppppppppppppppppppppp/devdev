# Codex Order: R5-2a — blocking_validator.py 3-way 분할

> **목표**: `blocking_validator.py` (1,394줄)에서 12개 체크 메서드를 3개 서브모듈로 추출
> **범위**: 서브모듈 3개 신규 + 호스트 수정 + 테스트 신규
> **패턴**: R5-1a (`pre_director_manuscript_checker.py`) 동일 — `host` 위임
> **위험도**: 중 (검증 파이프라인 핵심, 회귀 주의)

---

## 현재 구조 (1,394줄)

```
BlockingValidator
├── __init__()                          L33   (18줄)
├── validate()                          L52   (100줄) — 12개 체크 오케스트레이션
├── _RECALL_PATTERNS                    L154  (상수)
├── _ACTION_PATTERNS                    L174  (상수)
├── _check_dead_npc_resurrection()      L194  (42줄)
├── _check_unowned_item_usage()         L237  (197줄) ⚠️ 대형
├── _check_damaged_item_usage()         L436  (143줄)
├── _check_destroyed_location_visit()   L581  (25줄)
├── _check_minimum_length()             L608  (21줄)
├── _check_required_scenes()            L631  (36줄)
├── _check_scope_overflow()             L669  (71줄)
├── _extract_keywords()                 L742  (11줄)
├── _check_physical_capability()        L755  (107줄)
├── _check_authority_exercise()         L864  (103줄)
├── _check_relationship_consistency()   L969  (53줄)
├── _check_information_consistency()    L1024 (68줄)
├── _check_scene_completeness()         L1094 (74줄)
├── _check_cliffhanger_ending()         L1170 (150줄)
├── _calculate_cliffhanger_strength()   L1322 (59줄)
└── _get_strength_grade()               L1383 (11줄)
```

---

## 목표 구조 (3개 서브모듈)

### Module 1: `blocking_validator_entity_checks.py` (~450줄)

엔티티(NPC, 아이템, 장소) 존재/상태 검증.

| 메서드 | 줄수 |
|--------|------|
| `_check_dead_npc_resurrection()` | 42 |
| `_check_unowned_item_usage()` | 197 |
| `_check_damaged_item_usage()` | 143 |
| `_check_destroyed_location_visit()` | 25 |
| 상수: `_RECALL_PATTERNS`, `_ACTION_PATTERNS` | 40 |
| nested helpers: `find_sentence_start/end` | 각 메서드 내부 |

### Module 2: `blocking_validator_scene_checks.py` (~420줄)

씬 구조 + 분량 + 클리프행어 검증.

| 메서드 | 줄수 |
|--------|------|
| `_check_minimum_length()` | 21 |
| `_check_required_scenes()` | 36 |
| `_check_scope_overflow()` | 71 |
| `_check_scene_completeness()` | 74 |
| `_check_cliffhanger_ending()` | 150 |
| `_calculate_cliffhanger_strength()` | 59 |
| `_get_strength_grade()` | 11 |

### Module 3: `blocking_validator_consistency_checks.py` (~340줄)

논리적 일관성 + 정당화 검증.

| 메서드 | 줄수 |
|--------|------|
| `_check_physical_capability()` | 107 |
| `_check_authority_exercise()` | 103 |
| `_check_relationship_consistency()` | 53 |
| `_check_information_consistency()` | 68 |
| `_extract_keywords()` | 11 |

### 호스트 잔여 (~180줄)

```python
class BlockingValidator:
    __init__()          # 18줄 (그대로)
    validate()          # 100줄 (위임 호출로 전환)
    # 3개 lazy @property
    entity_checks       # → BlockingValidatorEntityChecks
    scene_checks        # → BlockingValidatorSceneChecks
    consistency_checks  # → BlockingValidatorConsistencyChecks
```

---

## 구현 상세

### 서브모듈 공통 패턴 (R5-1a와 동일)

```python
"""[R5-2a] BlockingValidator 엔티티 체크 서브모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.validation.blocking_validator import BlockingValidator


class BlockingValidatorEntityChecks:
    """엔티티(NPC, 아이템, 장소) 존재/상태 검증."""

    def __init__(self, host: BlockingValidator) -> None:
        self.host = host

    # _RECALL_PATTERNS, _ACTION_PATTERNS → 클래스 상수로 이동

    def _check_dead_npc_resurrection(self, manuscript, context):
        # 원본 그대로 복사, self.host.xxx 접근 필요 시만 변경
        ...
```

**핵심 원칙**:
- `self` → `self` (서브모듈 자체)
- `self.context` → `self.host.context` (호스트의 context 참조)
- `self.enable_justification_checks` → `self.host.enable_justification_checks`
- 상수(`_RECALL_PATTERNS` 등)는 서브모듈 클래스 상수로 이동
- import는 서브모듈 파일 상단에서 직접

### 호스트 수정 (`blocking_validator.py`)

```python
class BlockingValidator:
    def __init__(self, context=None, enable_justification_checks=True):
        self.context = context
        self.enable_justification_checks = enable_justification_checks
        self._entity_checks = None
        self._scene_checks = None
        self._consistency_checks = None

    @property
    def entity_checks(self):
        if self._entity_checks is None:
            from modules.validation.blocking_validator_entity_checks import BlockingValidatorEntityChecks
            self._entity_checks = BlockingValidatorEntityChecks(self)
        return self._entity_checks

    @property
    def scene_checks(self):
        if self._scene_checks is None:
            from modules.validation.blocking_validator_scene_checks import BlockingValidatorSceneChecks
            self._scene_checks = BlockingValidatorSceneChecks(self)
        return self._scene_checks

    @property
    def consistency_checks(self):
        if self._consistency_checks is None:
            from modules.validation.blocking_validator_consistency_checks import BlockingValidatorConsistencyChecks
            self._consistency_checks = BlockingValidatorConsistencyChecks(self)
        return self._consistency_checks

    def validate(self, manuscript, validation_context):
        failures = []

        # Entity checks
        dead_npc_check = self.entity_checks._check_dead_npc_resurrection(manuscript, validation_context)
        if not dead_npc_check["passed"]:
            failures.append(dead_npc_check)

        unowned_item_check = self.entity_checks._check_unowned_item_usage(manuscript, validation_context)
        # ... (기존 패턴 유지, self.xxx → self.entity_checks.xxx 등)
```

**validate() 내부 위임 매핑**:

| 체크 | 위임 대상 |
|------|-----------|
| `_check_dead_npc_resurrection` | `self.entity_checks.` |
| `_check_unowned_item_usage` | `self.entity_checks.` |
| `_check_damaged_item_usage` | `self.entity_checks.` |
| `_check_destroyed_location_visit` | `self.entity_checks.` |
| `_check_minimum_length` | `self.scene_checks.` |
| `_check_required_scenes` | `self.scene_checks.` |
| `_check_scope_overflow` | `self.scene_checks.` |
| `_check_scene_completeness` | `self.scene_checks.` |
| `_check_cliffhanger_ending` | `self.scene_checks.` |
| `_check_physical_capability` | `self.consistency_checks.` |
| `_check_authority_exercise` | `self.consistency_checks.` |
| `_check_relationship_consistency` | `self.consistency_checks.` |
| `_check_information_consistency` | `self.consistency_checks.` |

### 주의 — 메서드 내부 참조

1. `_check_unowned_item_usage`와 `_check_damaged_item_usage`에는 **nested helper 함수** (`find_sentence_start`, `find_sentence_end`)가 있다. 이들은 메서드와 함께 서브모듈로 이동.

2. `_check_cliffhanger_ending`은 내부에서 `self._calculate_cliffhanger_strength()`와 `self._get_strength_grade()`를 호출 → 같은 서브모듈이므로 `self.` 유지.

3. `_check_physical_capability`와 `_check_authority_exercise`는 `JUSTIFICATION_AVAILABLE` 모듈 변수와 `get_justification_guide`, `get_pattern_description` import를 사용 → 서브모듈 파일 상단에서 동일 import.

4. `_check_relationship_consistency`는 `RelationshipTracker` import 사용:
   ```python
   from modules.core.relationship_tracker import RelationshipTracker
   ```
   → 서브모듈에서 동일 import.

5. `_check_information_consistency`는 `InformationDiffusion` import 사용:
   ```python
   from modules.validation.information_diffusion import InformationDiffusion
   ```
   → 서브모듈에서 동일 import.

6. `_check_scope_overflow`와 `_check_minimum_length`는 `ManuscriptLimits` + `_threshold()` import 사용 → 서브모듈에서 동일 import.

---

## 테스트

### 파일: `tests/test_blocking_validator_submodules.py`

기존 테스트(`tests/test_blocking_validator.py` 존재 여부 확인 필수)와 별도로 서브모듈 직접 테스트.

**테스트 구조**:

```python
"""[R5-2a] BlockingValidator 서브모듈 단위 테스트."""
import pytest
from modules.validation.blocking_validator import BlockingValidator

@pytest.fixture
def bv():
    return BlockingValidator(context=None, enable_justification_checks=True)

# ── Entity checks ──
class TestEntityChecks:
    def test_dead_npc_recall_allowed(self, bv):
        """회상 패턴은 통과."""
        result = bv.entity_checks._check_dead_npc_resurrection(
            "그는 회상에 잠겼다. 고인의 생전 모습이 떠올랐다.",
            {"encyclopedia": {"npcs": [{"name": "장무기", "status": "dead", "aliases": []}]}}
        )
        assert result["passed"]

    def test_dead_npc_action_blocked(self, bv):
        """사망 NPC 행동은 REJECT."""
        result = bv.entity_checks._check_dead_npc_resurrection(
            "장무기가 말했다. '나를 따라오라.'",
            {"encyclopedia": {"npcs": [{"name": "장무기", "status": "dead", "aliases": []}]}}
        )
        assert not result["passed"]

    def test_unowned_item_detected(self, bv):
        """미획득 아이템 사용 감지."""
        result = bv.entity_checks._check_unowned_item_usage(
            "그는 천잠사를 꺼내 들었다.",
            {"encyclopedia": {"items": [{"name": "천잠사", "aliases": []}]},
             "martial_hud": {"equipment": []}}
        )
        # 결과 확인 (소유 목록에 없으면 실패)
        assert not result["passed"]

    def test_damaged_item_usage(self, bv):
        """파손 아이템 사용 감지."""
        result = bv.entity_checks._check_damaged_item_usage(
            "그는 파괴된 검을 휘둘렀다.",
            {"item_states": {"검": "파괴"}}
        )
        assert not result["passed"]

    def test_destroyed_location(self, bv):
        """파괴된 장소 방문."""
        result = bv.entity_checks._check_destroyed_location_visit(
            "그는 무림맹으로 걸어갔다.",
            {"encyclopedia": {"destroyed_locations": [{"name": "무림맹"}]}}
        )
        assert not result["passed"]

# ── Scene checks ──
class TestSceneChecks:
    def test_minimum_length_pass(self, bv):
        ms = "가" * 5000
        result = bv.scene_checks._check_minimum_length(ms, {})
        assert result["passed"]

    def test_minimum_length_fail(self, bv):
        ms = "가" * 100
        result = bv.scene_checks._check_minimum_length(ms, {})
        assert not result["passed"]

    def test_cliffhanger_grade(self, bv):
        grade = bv.scene_checks._get_strength_grade(85)
        assert grade == "S"

# ── Consistency checks ──
class TestConsistencyChecks:
    def test_extract_keywords(self, bv):
        kw = bv.consistency_checks._extract_keywords("천잠사를 들고 무림맹으로")
        assert "천잠사" in kw or "무림맹" in kw

# ── Integration ──
class TestIntegration:
    def test_validate_delegates_correctly(self, bv):
        """validate()가 서브모듈을 통해 동작."""
        result = bv.validate("가" * 5000, {"encyclopedia": {}, "martial_hud": {}})
        assert "tier" in result
        assert result["tier"] == "BLOCKING"

    def test_lazy_init(self, bv):
        """서브모듈 lazy init 동작."""
        assert bv._entity_checks is None
        _ = bv.entity_checks
        assert bv._entity_checks is not None
```

**최소 15개 테스트** — 각 서브모듈 당 4-5개 + 통합 2-3개.

---

## 검증 게이트

```bash
# Gate 1: py_compile 3개 신규 파일
python -c "import py_compile; py_compile.compile('modules/validation/blocking_validator_entity_checks.py', doraise=True)"
python -c "import py_compile; py_compile.compile('modules/validation/blocking_validator_scene_checks.py', doraise=True)"
python -c "import py_compile; py_compile.compile('modules/validation/blocking_validator_consistency_checks.py', doraise=True)"

# Gate 2: BlockingValidator import 정상
python -c "from modules.validation.blocking_validator import BlockingValidator; bv=BlockingValidator(); print(f'entity={type(bv.entity_checks).__name__}, scene={type(bv.scene_checks).__name__}, consistency={type(bv.consistency_checks).__name__}')"

# Gate 3: 신규 테스트 통과
set PYTHONIOENCODING=utf-8
pytest tests/test_blocking_validator_submodules.py -v

# Gate 4: 기존 blocking_validator 테스트 회귀 없음
pytest tests/ -k "blocking" -v

# Gate 5: 전체 회귀
pytest tests/ -q

# Gate 6: 줄 수 확인
python -c "print(sum(1 for _ in open('modules/validation/blocking_validator.py')))"
# 목표: ~180줄 이하

# Gate 7: pre-commit
pre-commit run --files modules/validation/blocking_validator.py modules/validation/blocking_validator_entity_checks.py modules/validation/blocking_validator_scene_checks.py modules/validation/blocking_validator_consistency_checks.py tests/test_blocking_validator_submodules.py
```

---

## 커밋

```
refactor(r5-2a): extract 3 sub-modules from blocking_validator (1,394→~180 lines, -87%)
```

push 포함.

---

## 실패 시

- `self.host.context` 접근 에러 → 서브모듈에서 `self.host` 참조 확인
- import 순환 → `TYPE_CHECKING` 가드 + lazy import 패턴 확인
- 기존 테스트 실패 → `validate()` 위임 호출 매핑 재확인
- 크래시 시 traceback + 원인만 보고 후 중단
