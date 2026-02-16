# Codex Order B-1-6: Stage2 Validation Pipeline 추출

> **목표**: `stage2_orchestrator.py`에서 검증 체인(validation pipeline)을 독립 서브모듈로 분리
> **패턴**: V64 delegation — `self.host` 참조, lazy init property
> **프로덕션 코드 무결성**: 기존 테스트 전체 통과 필수

---

## 1. 추출 대상 메서드 (6개, ~667줄)

| # | 현재 메서드 | 라인 범위 | 줄 수 | 서브모듈 메서드명 |
|---|-----------|----------|-------|----------------|
| 1 | `_preflight_validation(self, *, ...)` | L1454-1975 | 522 | `run_validation(self, *, ...)` (public) |
| 2 | `_stage2_flow_guard(self, refined_arc)` | L2541-2616 | 76 | `_stage2_flow_guard(self, refined_arc)` |
| 3 | `_stage2_flow_guard_legacy(self, normalized)` | L2617-2639 | 22 | `_stage2_flow_guard_legacy(self, normalized)` |
| 4 | `_normalize_flow_text(self, text)` | L2533-2540 | 8 | `_normalize_flow_text(self, text)` |
| 5 | `_is_tactical_doc_duplicate(self, candidate, refs, threshold)` | L2505-2532 | 28 | `_is_tactical_doc_duplicate(self, candidate, refs, threshold)` |
| 6 | `_normalize_tactical_text(self, text)` | L2494-2504 | 11 | `_normalize_tactical_text(self, text)` |

---

## 2. 신규 파일: `modules/core/stage2_validation_pipeline.py`

### 2-A. 클래스 구조

```python
"""[B-1-6] Stage2 Validation Pipeline — 검증 체인 서브모듈."""

import hashlib
import json
import logging
import re
from difflib import SequenceMatcher

from modules.core.constants import AIModels


class Stage2ValidationPipeline:
    """Stage2Orchestrator의 Pre-Director 검증 체인.

    Host dependencies:
        - self.host.ctx: Stage2Context (agents, validators, monitors, callbacks)
    """

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        """Host의 DI 컨텍스트 프록시."""
        return self.host.ctx
```

### 2-B. 메서드 이동 규칙

1. **`run_validation`** (was `_preflight_validation`):
   - 시그니처의 `self` → `self` (host 대신 pipeline의 self)
   - `self.ctx.*` 접근은 `self.ctx.*`로 유지 (property proxy)
   - **`self.app` 참조 3건 제거** (아래 2-C 참조)
   - `self._stage2_flow_guard(...)` → `self._stage2_flow_guard(...)` (동일 — 이제 파이프라인 내부 호출)
   - `self._is_tactical_doc_duplicate(...)` → `self._is_tactical_doc_duplicate(...)` (동일)
   - 내부 lazy import 유지: `from modules.core.spinners import V50_MODULES_AVAILABLE, rich_console`
   - 내부 lazy import 유지: `from modules.core.self_reflection import ReflectionTarget`

2. **`_stage2_flow_guard`**:
   - `self.ctx.sys.api_client` → `self.ctx.sys.api_client` (동일)
   - `self._normalize_flow_text(...)` → `self._normalize_flow_text(...)` (동일)
   - `self._stage2_flow_guard_legacy(...)` → `self._stage2_flow_guard_legacy(...)` (동일)
   - top-level import `from modules.core.constants import AIModels` 가능 (lazy import 해제)

3. **나머지 4개**: `self` 참조만 변경, 로직 동일

### 2-C. `self.app` 참조 제거 (3건 → 0건)

| 위치 | 현재 코드 | 변환 후 |
|------|----------|--------|
| L1503 | `state_tracker=getattr(self.app, "state_tracker", None)` | `state_tracker=self.ctx.state_tracker` |
| L1685 | `state_tracker=getattr(self.app, "state_tracker", None)` | `state_tracker=self.ctx.state_tracker` |
| L1753 | `state_tracker=getattr(self.app, "state_tracker", None)` | `state_tracker=self.ctx.state_tracker` |

> `state_tracker`는 Stage2Context 필수 슬롯(5종 중 1개)이므로 안전

---

## 3. 오케스트레이터 변경: `stage2_orchestrator.py`

### 3-A. `__init__` 확장

```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._validation_pipeline = None  # [B-1-6] 신규
```

### 3-B. Lazy init property 추가

```python
@property
def validation_pipeline(self):
    """[B-1-6] Validation chain sub-module (lazy init)."""
    if self._validation_pipeline is None:
        from modules.core.stage2_validation_pipeline import Stage2ValidationPipeline
        self._validation_pipeline = Stage2ValidationPipeline(self)
    return self._validation_pipeline
```

### 3-C. 메인 루프 호출 변경 (1곳)

```python
# L598: 변경 전
_val = self._preflight_validation(
    refined_arc=refined_arc,
    ...
)

# L598: 변경 후
_val = self.validation_pipeline.run_validation(
    refined_arc=refined_arc,
    ...
)
```

### 3-D. Thin wrappers (6개 — 기존 테스트 호환)

```python
# ── [B-1-6] Thin wrappers (backward compat) ──────────────

def _preflight_validation(self, **kwargs):
    return self.validation_pipeline.run_validation(**kwargs)

def _stage2_flow_guard(self, refined_arc: dict) -> dict:
    return self.validation_pipeline._stage2_flow_guard(refined_arc)

def _stage2_flow_guard_legacy(self, normalized) -> dict:
    return self.validation_pipeline._stage2_flow_guard_legacy(normalized)

def _normalize_flow_text(self, text: str) -> str:
    return self.validation_pipeline._normalize_flow_text(text)

def _is_tactical_doc_duplicate(self, candidate_text: str, reference_texts: list, threshold: float = 0.98) -> bool:
    return self.validation_pipeline._is_tactical_doc_duplicate(candidate_text, reference_texts, threshold)

def _normalize_tactical_text(self, text: str) -> str:
    return self.validation_pipeline._normalize_tactical_text(text)
```

### 3-E. 삭제 대상

| 삭제할 메서드 | 라인 범위 |
|-------------|----------|
| `_preflight_validation(self, *, ...)` | L1454-1975 (522줄) |
| `_normalize_tactical_text(self, text)` | L2494-2504 (11줄) |
| `_is_tactical_doc_duplicate(self, ...)` | L2505-2532 (28줄) |
| `_normalize_flow_text(self, text)` | L2533-2540 (8줄) |
| `_stage2_flow_guard(self, refined_arc)` | L2541-2616 (76줄) |
| `_stage2_flow_guard_legacy(self, normalized)` | L2617-2639 (22줄) |

> 삭제 총량: ~667줄, thin wrappers 추가: ~20줄

---

## 4. 기존 테스트 수정: `test_stage2_preflight_helpers.py`

### 4-A. Mock 대상 변경 (필수)

기존 테스트는 오케스트레이터의 `_stage2_flow_guard`를 mock한 뒤 `_preflight_validation`을 호출합니다.
분리 후 `_preflight_validation` thin wrapper → `validation_pipeline.run_validation` → 파이프라인 내부 `_stage2_flow_guard`로 라우팅되므로, mock 대상을 변경해야 합니다.

**변경 패턴** (~15건):

```python
# 변경 전
s2_orch._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
result = s2_orch._preflight_validation(**kwargs)

# 변경 후
s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
result = s2_orch._preflight_validation(**kwargs)
```

**`_is_tactical_doc_duplicate` mock도 동일** (~1건):

```python
# 변경 전
s2_orch._is_tactical_doc_duplicate = MagicMock(return_value=True)

# 변경 후
s2_orch.validation_pipeline._is_tactical_doc_duplicate = MagicMock(return_value=True)
```

### 4-B. `test_stage2_pipeline.py` — 변경 불필요

이 파일의 테스트들은 오케스트레이터의 메서드를 직접 호출합니다:
```python
orchestrator._normalize_tactical_text("text")
orchestrator._stage2_flow_guard(arc)
```
thin wrapper가 파이프라인으로 위임하므로 **변경 없이 통과**.

`hasattr` 체크도 thin wrapper 존재로 **통과**:
```python
assert hasattr(orchestrator, '_normalize_tactical_text')  # ✅ thin wrapper 존재
```

---

## 5. 신규 테스트: `tests/test_stage2_validation_pipeline.py`

**최소 15개 테스트** — 파이프라인을 직접 인스턴스화하여 검증:

### 5-A. 구조 테스트 (3개)

```python
class TestValidationPipelineStructure:
    def test_init_requires_host(self):
        """host 없이 생성 불가"""

    def test_ctx_proxy(self):
        """self.ctx가 host.ctx를 반환"""

    def test_all_methods_exist(self):
        """6개 메서드 존재 확인"""
```

### 5-B. 텍스트 유틸 테스트 (4개)

```python
class TestTextUtils:
    def test_normalize_tactical_basic(self):
    def test_normalize_tactical_none(self):
    def test_normalize_flow_basic(self):
    def test_is_duplicate_exact_match(self):
```

### 5-C. Flow Guard 테스트 (3개)

```python
class TestFlowGuard:
    def test_reject_insufficient_beats(self):
    def test_reject_short_beats(self):
    def test_legacy_fallback_stagnation(self):
```

### 5-D. run_validation 통합 테스트 (5+개)

```python
class TestRunValidation:
    def test_invalid_arc_returns_retry(self):
        """refined_arc=None → action='retry'"""

    def test_flow_guard_reject(self):
        """Flow Guard REJECT → action='retry'"""

    def test_duplicate_guard_reject(self):
        """tactical_doc 중복 → action='retry'"""

    def test_happy_path_no_four_phase(self):
        """모든 검증 통과 → action='proceed'"""

    def test_consensus_reject(self):
        """Consensus REJECT → action='retry' + 피드백"""
```

---

## 6. Import 정리

### `stage2_validation_pipeline.py` (신규)

```python
# top-level
import hashlib
import json
import logging
import re
from difflib import SequenceMatcher
from modules.core.constants import AIModels

# lazy (run_validation 내부)
from modules.core.spinners import V50_MODULES_AVAILABLE, rich_console
from modules.core.self_reflection import ReflectionTarget  # conditional
from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer  # conditional
```

### `stage2_orchestrator.py` (변경)

**삭제 가능한 import**: 없음 (다른 메서드에서도 사용)
**추가 import**: 없음 (lazy import in property)

---

## 7. 예상 결과

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| `stage2_orchestrator.py` | 2,639줄 | ~1,992줄 (**-24.5%**) |
| `stage2_validation_pipeline.py` | 없음 | ~680줄 |
| `self.app` in 추출 메서드 | 3건 | 0건 (→ `self.ctx.state_tracker`) |
| 기존 테스트 | 전체 통과 | 전체 통과 (mock 대상 변경 후) |
| 신규 테스트 | 없음 | 15+개 |

---

## 8. 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/stage2_validation_pipeline.py
python -m py_compile modules/core/stage2_orchestrator.py

# Gate 2: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_validation_pipeline.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_pipeline.py tests/test_stage2_preflight_helpers.py tests/test_stage2_context.py -v

# Gate 5: 전체 회귀 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -x --timeout=60

# Gate 6: pre-commit
pre-commit run --files modules/core/stage2_validation_pipeline.py modules/core/stage2_orchestrator.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight_helpers.py
```

---

## 9. 체크리스트

- [ ] `stage2_validation_pipeline.py` 생성 (6개 메서드 이동)
- [ ] `self.app` 3건 → `self.ctx.state_tracker` 전환
- [ ] `stage2_orchestrator.py`: `__init__` + lazy property + 메인 루프 호출 변경
- [ ] `stage2_orchestrator.py`: 원본 6개 메서드 삭제
- [ ] `stage2_orchestrator.py`: thin wrappers 6개 추가
- [ ] `test_stage2_preflight_helpers.py`: mock 대상 ~16건 변경
- [ ] `test_stage2_validation_pipeline.py` 신규 작성 (15+개)
- [ ] Gate 1-6 전체 통과
- [ ] 커밋 메시지: `refactor(B-1-6): extract stage2 validation pipeline to sub-module`
