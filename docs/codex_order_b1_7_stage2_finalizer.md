# Codex Order B-1-7: Stage2 Finalizer 추출

> **목표**: `stage2_orchestrator.py`에서 Director 심사 + PASS/REJECT 후처리를 독립 서브모듈로 분리
> **패턴**: V64 delegation — `self.host` 참조, lazy init property
> **프로덕션 코드 무결성**: 기존 테스트 전체 통과 필수

---

## 1. 추출 대상 메서드 (3개, ~518줄)

| # | 현재 메서드 | 라인 범위 | 줄 수 | 서브모듈 메서드명 |
|---|-----------|----------|-------|----------------|
| 1 | `async _preflight_finalize(self, *, ...)` | L1463-1872 | 414 | `async run_finalize(self, *, ...)` (public) |
| 2 | `_record_s2_pass_metrics(self, *, ...)` | L1881-1925 | 45 | `_record_s2_pass_metrics(self, *, ...)` |
| 3 | `_record_s2_reject_metrics(self, *, ...)` | L1926-1984 | 59 | `_record_s2_reject_metrics(self, *, ...)` |

**호출 관계:**
```
main loop (L634)
  └── _preflight_finalize()
        ├── _record_s2_pass_metrics()   (L1728, PASS 경로)
        └── _record_s2_reject_metrics() (L1861, REJECT 경로)
```
metrics 2개는 `_preflight_finalize` 내부에서만 호출됨 → 완벽한 응집 그룹.

---

## 2. 신규 파일: `modules/core/stage2_finalizer.py`

### 2-A. 클래스 구조

```python
"""[B-1-7] Stage2 Finalizer — Director 심사 + PASS/REJECT 후처리 서브모듈."""

import json
import logging

from modules.models.arc import validate_arc


class Stage2Finalizer:
    """Stage2Orchestrator의 Director 심사 및 최종 처리.

    주요 책임:
    - SemanticPlotGuard 최종 체크
    - Director 컨텍스트 확장 (V67) + 심사 호출
    - API 할당량 폴백 (V60.43)
    - PASS: 데이터 주입, DB 저장, 볼륨/시리즈 요약
    - REJECT: StateTracker 롤백, 피드백 생성
    - 메트릭 기록 (PassRateMonitor, Dashboard, Optimizer)

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

1. **`run_finalize`** (was `_preflight_finalize`, async):
   - 시그니처 동일 (keyword-only 22개)
   - `self.ctx.*` 접근은 `self.ctx.*`로 유지 (property proxy)
   - `self._record_s2_pass_metrics(...)` → `self._record_s2_pass_metrics(...)` (동일 — 파이프라인 내부 호출)
   - `self._record_s2_reject_metrics(...)` → `self._record_s2_reject_metrics(...)` (동일)
   - `validate_arc(refined_arc)` → top-level import로 해결 (`from modules.models.arc import validate_arc`)
   - 내부 lazy import 유지: `from modules.core.constants import RecoveryLimits`
   - **`self.app` 참조: 0건** (이미 clean)

2. **`_record_s2_pass_metrics`**: 로직 동일, lazy import 유지 (`from modules.core.spinners import V50_MODULES_AVAILABLE`)

3. **`_record_s2_reject_metrics`**: 로직 동일, lazy import 유지

---

## 3. 오케스트레이터 변경: `stage2_orchestrator.py`

### 3-A. `__init__` 확장

```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._validation_pipeline = None  # [B-1-6]
    self._finalizer = None            # [B-1-7] 신규
```

### 3-B. Lazy init property 추가

```python
@property
def finalizer(self):
    """[B-1-7] Finalizer sub-module (lazy init)."""
    if self._finalizer is None:
        from modules.core.stage2_finalizer import Stage2Finalizer
        self._finalizer = Stage2Finalizer(self)
    return self._finalizer
```

### 3-C. 메인 루프 호출 변경 (1곳)

```python
# L634: 변경 전
_fin = await self._preflight_finalize(
    refined_arc=refined_arc,
    ...
)

# L634: 변경 후
_fin = await self.finalizer.run_finalize(
    refined_arc=refined_arc,
    ...
)
```

### 3-D. Thin wrappers (3개 — 기존 테스트 호환)

```python
# ── [B-1-7] Thin wrappers (backward compat) ──────────────

async def _preflight_finalize(self, **kwargs):
    return await self.finalizer.run_finalize(**kwargs)

def _record_s2_pass_metrics(self, **kwargs):
    return self.finalizer._record_s2_pass_metrics(**kwargs)

def _record_s2_reject_metrics(self, **kwargs):
    return self.finalizer._record_s2_reject_metrics(**kwargs)
```

> **주의**: `_preflight_finalize` thin wrapper는 **async** 함수여야 함 (`await` 필수)

### 3-E. 삭제 대상

| 삭제할 메서드 | 라인 범위 | 줄 수 |
|-------------|----------|-------|
| `async _preflight_finalize(self, *, ...)` | L1463-1872 | 414 |
| `_record_s2_pass_metrics(self, *, ...)` | L1881-1925 | 45 |
| `_record_s2_reject_metrics(self, *, ...)` | L1926-1984 | 59 |

> 삭제 총량: ~518줄, thin wrappers 추가: ~10줄

### 3-F. top-level import 정리

`from modules.models.arc import validate_arc` (L21)은 `_preflight_finalize` 내부에서만 사용됨.
다른 메서드에서 사용하지 않으면 삭제 가능. **사용 여부 확인 후 판단**.

---

## 4. 기존 테스트: 변경 불필요

### `test_stage2_preflight_helpers.py`

| 테스트 패턴 | 호환성 |
|-----------|--------|
| `s2_orch._preflight_finalize(**kwargs)` (L406, L433) | ✅ async thin wrapper로 통과 |
| `s2_orch._record_s2_pass_metrics(...)` (L142, L167, L181) | ✅ thin wrapper로 통과 |
| `s2_orch._record_s2_reject_metrics(...)` (L200, L222, L240) | ✅ thin wrapper로 통과 |
| `hasattr(orch, "_preflight_finalize")` (L122) | ✅ thin wrapper 존재 |
| `hasattr(orch, "_record_s2_pass_metrics")` (L123) | ✅ thin wrapper 존재 |
| `hasattr(orch, "_record_s2_reject_metrics")` (L124) | ✅ thin wrapper 존재 |

`_preflight_finalize` 테스트는 `ctx.pass_rate_monitor = None` 등으로 metrics를 비활성화하므로,
metrics 메서드의 내부 호출 경로가 파이프라인으로 변경되어도 영향 없음.

**B-1-6 때와 달리 mock 대상 변경이 필요하지 않음** — finalize 테스트는 내부 메서드를 mock하지 않고 ctx 속성을 None으로 설정하는 패턴.

### `test_stage2_pipeline.py`

`_preflight_finalize`, `_record_s2_*` 참조 없음 — 변경 불필요.

---

## 5. 신규 테스트: `tests/test_stage2_finalizer.py`

**최소 15개 테스트** — 파이프라인을 직접 인스턴스화하여 검증:

### 5-A. 구조 테스트 (3개)

```python
class TestFinalizerStructure:
    def test_init_requires_host(self):
        """host 없이 생성 불가"""

    def test_ctx_proxy(self):
        """self.ctx가 host.ctx를 반환"""

    def test_all_methods_exist(self):
        """3개 메서드 존재 확인: run_finalize, _record_s2_pass_metrics, _record_s2_reject_metrics"""
```

### 5-B. Metrics 테스트 (6개)

```python
class TestMetricsRecording:
    def test_pass_metrics_with_monitor(self):
        """pass_rate_monitor.record_attempt 호출 확인"""

    def test_pass_metrics_without_monitor(self):
        """monitor=None 시 안전 스킵"""

    def test_pass_metrics_clears_optimizer_failures(self):
        """PASS 시 failure_memory.clear_arc_failures 호출"""

    def test_reject_metrics_with_monitor(self):
        """reject 기록 + stage_rejection_history.append"""

    def test_reject_metrics_without_monitor(self):
        """monitor=None 시 안전 스킵"""

    def test_reject_metrics_records_optimizer_failure(self):
        """REJECT 시 failure_memory.record_failure 호출"""
```

### 5-C. run_finalize 통합 테스트 (6+개)

```python
class TestRunFinalize:
    def test_director_pass_returns_break(self):
        """Director PASS → action='break', DB 저장 확인"""

    def test_director_reject_returns_next(self):
        """Director REJECT → action='next', 피드백 포함"""

    def test_quota_fallback_override(self):
        """V60.43: API 할당량 오류 시 REJECT→PASS 오버라이드"""

    def test_missing_critical_data_returns_retry(self):
        """필수 키 과다 누락 시 action='retry'"""

    def test_state_tracker_rollback_on_reject(self):
        """V70: FourPhase PASS + Director REJECT 시 ST 롤백"""

    def test_volume_summary_generation(self):
        """V68: 10 Arc 마다 볼륨 요약 생성"""
```

---

## 6. Import 정리

### `stage2_finalizer.py` (신규)

```python
# top-level
import json
import logging
from modules.models.arc import validate_arc

# lazy (run_finalize 내부)
from modules.core.constants import RecoveryLimits

# lazy (metrics 내부)
from modules.core.spinners import V50_MODULES_AVAILABLE
```

### `stage2_orchestrator.py` (변경)

`from modules.models.arc import validate_arc` (L21) — 다른 메서드에서 사용하지 않으면 삭제 가능.
확인: `validate_arc`이 `_preflight_finalize` 외에 사용되는 곳 확인 후 판단.

---

## 7. 예상 결과

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| `stage2_orchestrator.py` | 2,008줄 | ~1,500줄 (**-25%**, 누적 -43%) |
| `stage2_finalizer.py` | 없음 | ~530줄 |
| `self.app` in 추출 메서드 | 0건 | 0건 (이미 clean) |
| 기존 테스트 수정 | 0건 | 0건 (thin wrapper 호환) |
| 신규 테스트 | 없음 | 15+개 |

**B-1 누적 성과 (B-1-7 완료 시):**

| 대상 | 원본 | 현재 | 감소율 |
|------|------|------|--------|
| stage4_orchestrator | 2,481 | 883 | -64% |
| chief_writer | 2,255 | 854 | -62% |
| stage2_orchestrator | 2,639 | ~1,500 | **-43%** |

---

## 8. 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/stage2_finalizer.py
python -m py_compile modules/core/stage2_orchestrator.py

# Gate 2: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_finalizer.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/test_stage2_pipeline.py tests/test_stage2_preflight_helpers.py tests/test_stage2_context.py tests/test_stage2_validation_pipeline.py -v

# Gate 5: 전체 회귀 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -x --timeout=60

# Gate 6: pre-commit
pre-commit run --files modules/core/stage2_finalizer.py modules/core/stage2_orchestrator.py tests/test_stage2_finalizer.py
```

---

## 9. 체크리스트

- [ ] `stage2_finalizer.py` 생성 (3개 메서드 이동)
- [ ] `stage2_orchestrator.py`: `__init__` + lazy property + 메인 루프 호출 변경
- [ ] `stage2_orchestrator.py`: 원본 3개 메서드 삭제
- [ ] `stage2_orchestrator.py`: thin wrappers 3개 추가 (async 주의)
- [ ] `stage2_orchestrator.py`: `validate_arc` import 정리 (필요시)
- [ ] `test_stage2_finalizer.py` 신규 작성 (15+개)
- [ ] Gate 1-6 전체 통과
- [ ] 커밋 메시지: `refactor(B-1-7): extract stage2 finalizer to sub-module`
