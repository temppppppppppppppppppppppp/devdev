# Codex Order: B-2 Protocol 미적합 5개 클래스 어댑터

> **목표**: 미적합 5개 클래스에 대한 Protocol 정의 + `isinstance()` 적합화
> **범위**: 1개 파일 수정(agents.py Protocol 추가) + 5개 파일 최소 수정 + 테스트 1개 신규
> **위험도**: 극저 (기존 동작 변경 0, Protocol 추가 + 리턴타입 명시만)

---

## 배경

`modules/protocols/agents.py`에 5개 Protocol이 정의되어 있고, 적합 에이전트 6개가 이미 존재.
하지만 **미적합 5개 클래스**는 메서드명 불일치 또는 Protocol 미정의로 `isinstance()` 검증 불가:

| 클래스 | 현재 메서드 | 문제 | 해결 방법 |
|--------|-----------|------|----------|
| ArcDraftValidator | `validate()` | Protocol 미정의 (ArtifactValidator와 시그니처 다름) | 전용 Protocol 정의 |
| ManuscriptValidator | `validate_candidate()` | 메서드명 불일치 (`validate` 아님) | 전용 Protocol 정의 |
| ConstraintCompiler | `compile()` | Protocol 미정의 | 전용 Protocol 정의 |
| BlueprintConstraintCompiler | `compile()` | Protocol 미정의 | 동일 Protocol 공유 |
| StateTracker | 50+ 메서드 Facade | Protocol 미정의 | 핵심 메서드만 Protocol 추출 |

**설계 원칙** (기존 `agents.py` 패턴 준수):
- `@runtime_checkable` Protocol — `isinstance()` 런타임 검증
- `**kwargs`로 파라미터 다양성 흡수
- 기존 클래스 코드 수정 최소화 (메서드명 변경 없음)
- 반환 타입은 실제 관찰된 패턴 기반

---

## 수정/생성 파일

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/protocols/agents.py` | Protocol 3종 추가 | ~45줄 |
| `modules/protocols/__init__.py` | export 추가 | ~6줄 |
| `tests/test_protocol_conformance.py` | **신규** — isinstance 적합 테스트 | ~80줄 |

**프로덕션 코드(5개 대상 클래스) 변경**: 없음. 구조적 서브타이핑이므로 코드 수정 불필요.

---

## 상세 구현

### 1. `modules/protocols/agents.py` — Protocol 3종 추가

기존 `Corrector` Protocol 뒤에 추가:

```python
@runtime_checkable
class DraftValidator(Protocol):
    """Arc/원고 사전 검증자 (Python 감지, LLM 판단)

    validate() → result_dict (warnings/score/suggestions 키 포함)
    validate_candidate() → result_dict (warnings/warning_count/metrics 키 포함)

    적합:
    - ArcDraftValidator.validate()
    - ManuscriptValidator.validate_candidate()

    NOTE: ArtifactValidator는 PASS/REJECT verdict 반환용.
    DraftValidator는 advisory warnings/score 반환용. 용도가 다름.
    """

    def validate(self, **kwargs: object) -> dict: ...


@runtime_checkable
class ConstraintCompilerProtocol(Protocol):
    """제약 조건 컴파일러

    compile() → str | dict (제약 조건 블록)

    적합:
    - ConstraintCompiler.compile() → str
    - BlueprintConstraintCompiler.compile() → dict
    """

    def compile(self, **kwargs: object) -> str | dict: ...


@runtime_checkable
class StateAggregator(Protocol):
    """다중 소스 상태 추적/검증 (Facade)

    핵심 생명주기 메서드만 Protocol 화.
    StateTracker의 50+ 메서드 중 4개 핵심만 선정.

    적합:
    - StateTracker.load_arc_design() + validate_timeline()
      + extract_all_state_changes() + generate_arc_summary()
    """

    def load_arc_design(self, tactical_doc: dict, **kwargs: object) -> bool: ...

    def validate_timeline(self, **kwargs: object) -> list[dict]: ...

    def extract_all_state_changes(self, arc: dict, **kwargs: object) -> dict: ...

    def generate_arc_summary(self, arc_no: int, **kwargs: object) -> dict: ...
```

또한 파일 상단 docstring의 미적합 목록을 갱신:

**현재 (L29-34):**
```python
미적합 에이전트 (메서드명 불일치 — 향후 어댑터 필요):
- ChiefWriter: generate_ensemble() 반환 list[dict] (tuple 아님)
- ConsensusValidator: validate_with_consensus() (validate 아님)
- Critic: critique_manuscript() (critique 아님)
- Director: audit_manuscript/audit_strategic_plan (validate 아님)
- StateExtractor: extract_state/extract_cumulative_state (analyze 아님)
```

**수정 후:**
```python
미적합 에이전트 (메서드명 불일치 — 향후 어댑터 필요):
- ChiefWriter: generate_ensemble() 반환 list[dict] (tuple 아님)
- ConsensusValidator: validate_with_consensus() (validate 아님)
- Critic: critique_manuscript() (critique 아님)
- Director: audit_manuscript/audit_strategic_plan (validate 아님)
- StateExtractor: extract_state/extract_cumulative_state (analyze 아님)

B-2 해소된 미적합 (Protocol 추가로 적합화):
- ArcDraftValidator: DraftValidator.validate() ✅
- ManuscriptValidator: DraftValidator.validate() (validate_candidate → validate 위임)
- ConstraintCompiler: ConstraintCompilerProtocol.compile() ✅
- BlueprintConstraintCompiler: ConstraintCompilerProtocol.compile() ✅
- StateTracker: StateAggregator (4개 핵심 메서드) ✅
```

적합 에이전트 표에도 추가:

**기존 표 뒤에 추가:**
```python
│ DraftValidator      │ ArcDraftValidator                         │
│                     │ ManuscriptValidator (via validate alias)   │
├─────────────────────┼───────────────────────────────────────────┤
│ ConstraintCompiler  │ ConstraintCompiler                        │
│   Protocol          │ BlueprintConstraintCompiler               │
├─────────────────────┼───────────────────────────────────────────┤
│ StateAggregator     │ StateTracker                              │
└─────────────────────┴───────────────────────────────────────────┘
```

---

### 2. `modules/protocols/__init__.py` — export 추가

**현재 (L11-42):**
```python
from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    Corrector,
    EnsembleGenerator,
    PipelineGenerator,
)
```

**수정 후:**
```python
from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    ConstraintCompilerProtocol,
    Corrector,
    DraftValidator,
    EnsembleGenerator,
    PipelineGenerator,
    StateAggregator,
)
```

**`__all__`에도 추가:**
```python
__all__ = [
    # Step 3 — Agent Protocol
    "PipelineGenerator",
    "EnsembleGenerator",
    "ArtifactValidator",
    "ArtifactCritic",
    "Corrector",
    # B-2 — 미적합 해소 Protocol
    "DraftValidator",
    "ConstraintCompilerProtocol",
    "StateAggregator",
    # Phase 4A — Service Protocol
    ...
]
```

---

### 3. ManuscriptValidator — `validate()` 알리아스 추가 (1줄)

ManuscriptValidator는 `validate_candidate()`를 사용하므로 DraftValidator Protocol의 `validate()` 시그니처와 불일치.
**가장 가벼운 해결**: `validate` 알리아스 1줄 추가.

**`modules/domain/agents/manuscript_validator.py`** — 클래스 내부 `validate_candidate()` 정의 뒤에:

```python
    # [B-2] DraftValidator Protocol 적합화
    validate = validate_candidate
```

> 이 1줄로 `isinstance(mv, DraftValidator)` 통과. 기존 호출 코드 변경 없음.

---

## 테스트

### `tests/test_protocol_conformance.py` (신규, ~80줄)

```python
"""[B-2] Protocol 적합성 테스트 — 구조적 서브타이핑 검증."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.protocols.agents import (
    ConstraintCompilerProtocol,
    DraftValidator,
    StateAggregator,
)


class TestDraftValidatorConformance:
    """DraftValidator Protocol 적합성."""

    def test_arc_draft_validator_conforms(self):
        """ArcDraftValidator가 DraftValidator Protocol에 적합."""
        from modules.domain.agents.arc_draft_validator import ArcDraftValidator
        adv = ArcDraftValidator()
        assert isinstance(adv, DraftValidator)

    def test_manuscript_validator_conforms(self):
        """ManuscriptValidator가 DraftValidator Protocol에 적합."""
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        mv = ManuscriptValidator()
        assert isinstance(mv, DraftValidator)

    def test_manuscript_validator_validate_alias(self):
        """ManuscriptValidator.validate가 validate_candidate와 동일."""
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        mv = ManuscriptValidator()
        assert mv.validate is mv.validate_candidate


class TestConstraintCompilerConformance:
    """ConstraintCompilerProtocol 적합성."""

    def test_constraint_compiler_conforms(self):
        """ConstraintCompiler가 Protocol에 적합."""
        from modules.domain.agents.constraint_compiler import ConstraintCompiler
        cc = ConstraintCompiler()
        assert isinstance(cc, ConstraintCompilerProtocol)

    def test_blueprint_constraint_compiler_conforms(self):
        """BlueprintConstraintCompiler가 Protocol에 적합."""
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler
        bcc = BlueprintConstraintCompiler()
        assert isinstance(bcc, ConstraintCompilerProtocol)


class TestStateAggregatorConformance:
    """StateAggregator Protocol 적합성."""

    def test_state_tracker_conforms(self):
        """StateTracker가 StateAggregator Protocol에 적합."""
        from modules.domain.agents.state_tracker import StateTracker
        st = StateTracker()
        assert isinstance(st, StateAggregator)

    def test_state_tracker_has_required_methods(self):
        """StateTracker가 4개 핵심 메서드를 보유."""
        from modules.domain.agents.state_tracker import StateTracker
        st = StateTracker()
        assert hasattr(st, "load_arc_design")
        assert hasattr(st, "validate_timeline")
        assert hasattr(st, "extract_all_state_changes")
        assert hasattr(st, "generate_arc_summary")
        assert callable(st.load_arc_design)
        assert callable(st.validate_timeline)


class TestExistingProtocolsStillWork:
    """기존 Protocol 적합성 회귀 테스트."""

    def test_pipeline_generator_still_conforms(self):
        """FourPhaseArcGenerator가 PipelineGenerator에 여전히 적합."""
        from modules.protocols.agents import PipelineGenerator
        from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
        gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
        assert isinstance(gen, PipelineGenerator)

    def test_corrector_still_conforms(self):
        """ArcCorrector가 Corrector에 여전히 적합."""
        from modules.protocols.agents import Corrector
        from modules.domain.agents.arc_corrector import ArcCorrector
        ac = ArcCorrector.__new__(ArcCorrector)
        assert isinstance(ac, Corrector)
```

---

## 파일별 변경 요약

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/protocols/agents.py` | Protocol 3종 + docstring 갱신 | ~45줄 |
| `modules/protocols/__init__.py` | import + __all__ 3개 추가 | ~6줄 |
| `modules/domain/agents/manuscript_validator.py` | `validate = validate_candidate` 1줄 | 1줄 |
| `tests/test_protocol_conformance.py` | 신규 테스트 9건 | ~80줄 |

**총 프로덕션 코드**: ~52줄 추가
**총 테스트**: 9건

---

## 주의사항

1. **구조적 서브타이핑** — Protocol은 `@runtime_checkable` + structural subtyping. 대상 클래스가 Protocol의 메서드를 보유하면 자동 적합. 상속 불필요.
2. **ManuscriptValidator만 1줄 수정** — `validate = validate_candidate` 알리아스. 나머지 4개는 코드 수정 없이 적합.
3. **`**kwargs`** — 기존 패턴 준수. 각 메서드의 파라미터가 10~25개로 다양하므로 `**kwargs`로 흡수.
4. **StateAggregator 4개 메서드만** — StateTracker 50+ 메서드 중 핵심 생명주기 4개만 선정. 나머지는 서브모듈 전용.
5. **ConstraintCompilerProtocol 이름** — `ConstraintCompiler`는 이미 클래스명으로 사용 중이므로 `ConstraintCompilerProtocol`로 명명.
6. **기존 Protocol 5종 무변경** — 기존 적합 에이전트 회귀 없음.

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/protocols/agents.py
python -m py_compile modules/protocols/__init__.py
python -m py_compile modules/domain/agents/manuscript_validator.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: Protocol import
python -c "from modules.protocols import DraftValidator, ConstraintCompilerProtocol, StateAggregator; print('OK')"

# Gate 4: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_protocol_conformance.py -v

# Gate 5: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 6: pre-commit
pre-commit run --files modules/protocols/agents.py modules/protocols/__init__.py modules/domain/agents/manuscript_validator.py tests/test_protocol_conformance.py
```

---

## 체크리스트

- [ ] `DraftValidator` Protocol 추가
- [ ] `ConstraintCompilerProtocol` Protocol 추가
- [ ] `StateAggregator` Protocol 추가
- [ ] `agents.py` docstring 적합 테이블 + 미적합 목록 갱신
- [ ] `__init__.py` import + __all__ 추가
- [ ] `manuscript_validator.py` `validate = validate_candidate` 1줄
- [ ] 테스트 9건 전체 통과
- [ ] Gate 1-6 전체 통과
- [ ] 커밋: `feat(protocols): add DraftValidator, ConstraintCompiler, StateAggregator protocols (B-2)`
