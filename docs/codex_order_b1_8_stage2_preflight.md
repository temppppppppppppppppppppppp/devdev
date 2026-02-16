# Codex Order B-1-8: Stage2 Preflight Analysis 추출

> **목표**: `stage2_orchestrator.py`에서 preflight 3개 메서드(state_setup + arc_analysis + enrichment)를 독립 서브모듈로 분리
> **패턴**: V64 delegation — `self.host` 참조, lazy init property
> **프로덕션 코드 무결성**: 기존 테스트 전체 통과 필수

---

## 1. 추출 대상 메서드 (3개, ~622줄)

| # | 현재 메서드 | 라인 범위 | 줄 수 | 서브모듈 메서드명 |
|---|-----------|----------|-------|-------------------|
| 1 | `_preflight_state_setup(self, *, ...)` | L849-1016 | 168 | `_preflight_state_setup(self, *, ...)` |
| 2 | `_preflight_arc_analysis(self, *, ...)` | L1017-1212 | 196 | `_preflight_arc_analysis(self, *, ...)` |
| 3 | `_preflight_enrichment(self, *, ...)` | L1213-1470 | 258 | `_preflight_enrichment(self, *, ...)` |

**호출 관계:**
```
stage_2_arcs_async_logic (main loop)
  ├── L454: _preflight_state_setup()    ← per-arc, while 루프 밖
  │         └── ThreadPoolExecutor 병렬: _compute_arc_drive() + _compute_preflight()
  ├── L507: _preflight_arc_analysis()   ← per-attempt, while 루프 안
  └── L527: _preflight_enrichment()     ← per-attempt, while 루프 안
```

3개 메서드 간 직접 호출 없음 (각각 독립) → 완벽한 응집 그룹.

---

## 2. 신규 파일: `modules/core/stage2_preflight.py`

### 2-A. 클래스 구조

```python
"""[B-1-8] Stage2 Preflight Analysis — 상태 초기화 + Arc 분석 + FourPhase 보강 서브모듈."""

import concurrent.futures
import logging

_perf_logger = logging.getLogger(__name__)


class Stage2PreflightAnalysis:
    """Stage2Orchestrator의 preflight 분석 3단계.

    주요 책임:
    - _preflight_state_setup: arc_drive + preflight 병렬 실행, 제약 초기화
    - _preflight_arc_analysis: per-attempt 컨텍스트 빌딩, Analyst 무기 준비
    - _preflight_enrichment: FourPhase 생성 + StateTracker 보강

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

1. **`_preflight_state_setup`** (168줄):
   - 시그니처 동일 (keyword-only 7개)
   - nested functions `_compute_arc_drive()`, `_compute_preflight()` 그대로 이동
   - `concurrent.futures.ThreadPoolExecutor` 사용 → top-level import로 해결
   - `self.ctx.*` 접근은 `self.ctx.*`로 유지 (property proxy)
   - **`self.app` 참조: 0건** (이미 clean)

2. **`_preflight_arc_analysis`** (196줄):
   - 시그니처 동일 (keyword-only 9개)
   - lazy import 유지: `from modules.core.constants import Emojis, RetryLimits`
   - lazy import 유지: `from modules.core.spinners import V50_MODULES_AVAILABLE`
   - **`self.app` 참조: 0건**

3. **`_preflight_enrichment`** (258줄):
   - 시그니처 동일 (keyword-only 12개)
   - lazy import 유지: `from modules.core.spinners import StageSpinner`
   - `import copy as _copy` (L1298, 인라인) → 유지
   - **`self.app` 참조: 0건**

---

## 3. 오케스트레이터 변경: `stage2_orchestrator.py`

### 3-A. `__init__` 확장

```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._validation_pipeline = None  # [B-1-6]
    self._finalizer = None            # [B-1-7]
    self._preflight = None            # [B-1-8] 신규
```

### 3-B. Lazy init property 추가

```python
@property
def preflight(self):
    """[B-1-8] Preflight analysis sub-module (lazy init)."""
    if self._preflight is None:
        from modules.core.stage2_preflight import Stage2PreflightAnalysis
        self._preflight = Stage2PreflightAnalysis(self)
    return self._preflight
```

### 3-C. 메인 루프 호출 변경 (3곳)

```python
# L454: 변경 전
_setup = self._preflight_state_setup(...)
# L454: 변경 후
_setup = self.preflight._preflight_state_setup(...)

# L507: 변경 전
_analysis = self._preflight_arc_analysis(...)
# L507: 변경 후
_analysis = self.preflight._preflight_arc_analysis(...)

# L527: 변경 전
_enrichment = self._preflight_enrichment(...)
# L527: 변경 후
_enrichment = self.preflight._preflight_enrichment(...)
```

### 3-D. Thin wrappers (3개 — 기존 테스트 호환)

```python
# ── [B-1-8] Thin wrappers (backward compat) ──────────────

def _preflight_state_setup(self, **kwargs):
    return self.preflight._preflight_state_setup(**kwargs)

def _preflight_arc_analysis(self, **kwargs):
    return self.preflight._preflight_arc_analysis(**kwargs)

def _preflight_enrichment(self, **kwargs):
    return self.preflight._preflight_enrichment(**kwargs)
```

### 3-E. 삭제 대상

| 삭제할 메서드 | 라인 범위 | 줄 수 |
|-------------|----------|-------|
| `_preflight_state_setup(self, *, ...)` | L849-1016 | 168 |
| `_preflight_arc_analysis(self, *, ...)` | L1017-1212 | 196 |
| `_preflight_enrichment(self, *, ...)` | L1213-1470 | 258 |

> 삭제 총량: ~622줄, thin wrappers 추가: ~10줄

### 3-F. top-level import 정리

`import concurrent.futures` (L16)은 `_preflight_state_setup` 내부에서만 사용됨.
추출 후 오케스트레이터에서 삭제, 신규 서브모듈에 추가.

---

## 4. 기존 테스트 변경

### 4-A. `test_stage2_preflight_helpers.py` — 변경 불필요

| 테스트 클래스 | 패턴 | 호환성 |
|------------|------|--------|
| `TestPreflightMethodsExist` (L114-129) | `hasattr(s2_orch, method_name)` | ✅ thin wrapper 존재 |
| `TestPreflightEnrichmentDefaults` (L447-531, 4개) | `s2_orch._preflight_enrichment(**kwargs)` 직접 호출 | ✅ thin wrapper 위임 |
| `TestQualityTrendInjection` (L921-996, 4개) | `s2_orch._preflight_arc_analysis(**kwargs)` 직접 호출 | ✅ thin wrapper 위임 |
| `TestPreflightParallelTimer` (L1004-1090, 5개) | `s2_orch._preflight_state_setup(**kwargs)` 직접 호출 | ✅ thin wrapper 위임 |

이 테스트들은 **메서드 내부를 mock하지 않고** ctx 속성만 조작하는 패턴 → thin wrapper로 충분.

### 4-B. `test_npc_info_chain.py` — ⚠️ 수정 필요 (2곳)

이 파일은 `inspect.getsource(Stage2Orchestrator._preflight_arc_analysis)`를 사용하여 소스 코드를 직접 검사.
추출 후 thin wrapper의 소스만 보이므로 **반드시 수정 필요**.

```python
# 변경 전 (L13, L21)
from modules.core.stage2_orchestrator import Stage2Orchestrator
source = inspect.getsource(Stage2Orchestrator._preflight_arc_analysis)

# 변경 후
from modules.core.stage2_preflight import Stage2PreflightAnalysis
source = inspect.getsource(Stage2PreflightAnalysis._preflight_arc_analysis)
```

총 변경: 2곳 (L11-13, L19-21). import 1개 + getsource 대상 2개.

---

## 5. 신규 테스트: `tests/test_stage2_preflight.py`

**최소 15개 테스트** — 서브모듈을 직접 인스턴스화하여 검증:

### 5-A. 구조 테스트 (3개)

```python
class TestPreflightStructure:
    def test_init_requires_host(self):
        """host 없이 생성 불가"""

    def test_ctx_proxy(self):
        """self.ctx가 host.ctx를 반환"""

    def test_all_methods_exist(self):
        """3개 메서드 존재 확인: _preflight_state_setup, _preflight_arc_analysis, _preflight_enrichment"""
```

### 5-B. _preflight_state_setup 테스트 (4개)

```python
class TestPreflightStateSetup:
    def test_returns_all_required_keys(self):
        """반환 dict에 arc_drive, cached_preflight_*, passed, constraint_block 등 12개 키"""

    def test_parallel_execution_runs_both_tasks(self):
        """weaver.generate_arc_drive + preflight.analyze 두 task 실행 확인"""

    def test_weaver_error_returns_error_drive(self):
        """weaver 예외 시 안전 기본값 반환 (desire_vector='생성 실패')"""

    def test_constraint_compiler_integration(self):
        """constraint_compiler 존재 시 constraint_block에 컴파일 결과 포함"""
```

### 5-C. _preflight_arc_analysis 테스트 (4개)

```python
class TestPreflightArcAnalysis:
    def test_returns_all_required_keys(self):
        """반환 dict에 enhanced_context, recent_patterns, refined_arc 등 7개 키"""

    def test_enhanced_context_includes_constraint_block(self):
        """constraint_block이 enhanced_context에 주입됨"""

    def test_focus_mode_on_retry(self):
        """attempt>0 + current_feedback 존재 시 Focus Mode 활성화"""

    def test_entity_registry_default_is_dict(self):
        """entity_registry_for_director 초기값이 빈 dict (C-2 호환)"""
```

### 5-D. _preflight_enrichment 테스트 (4개)

```python
class TestPreflightEnrichment:
    def test_returns_all_required_keys(self):
        """반환 dict에 four_phase_passed, refined_arc 등 7개 키"""

    def test_no_fourphase_returns_defaults(self):
        """FourPhase 에이전트 없으면 안전 기본값"""

    def test_fourphase_exception_non_propagating(self):
        """FourPhase 예외 시 안전 기본값 + 에러 피드백"""

    def test_fourphase_pass_triggers_state_tracker_enrichment(self):
        """FourPhase PASS 시 StateTracker 14종 추출 메서드 호출"""
```

---

## 6. Import 정리

### `stage2_preflight.py` (신규)

```python
# top-level
import concurrent.futures
import logging

_perf_logger = logging.getLogger(__name__)

# lazy (_preflight_state_setup 내부 — 없음, 전부 self.ctx.* 접근)
# lazy (_preflight_arc_analysis 내부)
from modules.core.constants import Emojis, RetryLimits
from modules.core.spinners import V50_MODULES_AVAILABLE

# lazy (_preflight_enrichment 내부)
from modules.core.spinners import StageSpinner
import copy as _copy  # L1298 인라인
```

### `stage2_orchestrator.py` (변경)

- `import concurrent.futures` (L16) — 추출 후 다른 메서드에서 미사용 → **삭제**
- `_perf_logger` (L21) — `_preflight_state_setup` 외 다른 곳에서도 사용 가능. **사용 여부 확인 후 판단**.

---

## 7. 예상 결과

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| `stage2_orchestrator.py` | 1,510줄 | ~900줄 (**-40%**, 누적 -66%) |
| `stage2_preflight.py` | 없음 | ~640줄 |
| `self.app` in 추출 메서드 | 0건 | 0건 (이미 clean) |
| 기존 테스트 수정 | **2곳** (`test_npc_info_chain.py`) | inspect.getsource 대상 변경 |
| 신규 테스트 | 없음 | 15+개 |

**B-1 최종 성과 (B-1-8 완료 시):**

| 대상 | 원본 | 현재 | 감소율 |
|------|------|------|--------|
| stage4_orchestrator | 2,481 | 883 | -64% |
| chief_writer | 2,255 | 854 | -62% |
| stage2_orchestrator | 2,639 | **~900** | **-66%** |

---

## 8. 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/stage2_preflight.py
python -m py_compile modules/core/stage2_orchestrator.py

# Gate 2: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_preflight.py -v

# Gate 4: 기존 테스트 회귀 없음 (npc_info_chain 수정 포함)
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_pipeline.py tests/test_stage2_preflight_helpers.py tests/test_stage2_context.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/test_npc_info_chain.py -v

# Gate 5: 전체 회귀 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -x --timeout=60

# Gate 6: pre-commit
pre-commit run --files modules/core/stage2_preflight.py modules/core/stage2_orchestrator.py tests/test_stage2_preflight.py tests/test_npc_info_chain.py
```

---

## 9. 체크리스트

- [ ] `stage2_preflight.py` 생성 (3개 메서드 이동)
- [ ] `stage2_orchestrator.py`: `__init__` + lazy property + 메인 루프 호출 변경 (3곳)
- [ ] `stage2_orchestrator.py`: 원본 3개 메서드 삭제
- [ ] `stage2_orchestrator.py`: thin wrappers 3개 추가
- [ ] `stage2_orchestrator.py`: `import concurrent.futures` 삭제 (미사용 확인 후)
- [ ] `test_npc_info_chain.py`: `inspect.getsource` 대상 변경 (2곳)
- [ ] `test_stage2_preflight.py` 신규 작성 (15+개)
- [ ] Gate 1-6 전체 통과
- [ ] 커밋 메시지: `refactor(B-1-8): extract stage2 preflight analysis to sub-module`
