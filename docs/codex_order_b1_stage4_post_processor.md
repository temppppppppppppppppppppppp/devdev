# Codex Order B-1-1: stage4 Post-Processor 추출

> 카테고리: 구조 개선 (B-1 모놀리스 분할, 1/3) / 규모: 중 / 위험도: 낮음

---

## 목표

`stage4_orchestrator.py` (2,481줄)에서 **Post-Processing 로직** (519줄, 21%)을
`stage4_post_processor.py`로 추출.

V64 위임 패턴 적용:
```python
# stage4_orchestrator.py
from modules.core.stage4_post_processor import Stage4PostProcessor

class Stage4Orchestrator:
    def __init__(self, app, *, context=None):
        ...
        self._post_processor = None  # lazy init

    @property
    def post_processor(self):
        if self._post_processor is None:
            self._post_processor = Stage4PostProcessor(self.ctx)
        return self._post_processor
```

---

## 추출 대상

| 메서드 | 라인 | 줄 수 | 역할 |
|--------|------|-------|------|
| `_process_pass_result()` | 803-1301 | 499 | PASS 후 후처리: HUD, DB, 벡터메모리, 내러티브, EpisodeBible, ChainLink, StateLog, ContinuityInspector |
| `_run_post_episode_tasks()` | 1303-1321 | 19 | 세션 종료: 사용자 프롬프트 + 벡터메모리 동기화 |

**호출 지점** (stage4_orchestrator.py 내):
- L1587: `self._process_pass_result(...)` → `self.post_processor.process_pass_result(...)`
- L1600: `self._run_post_episode_tasks()` → `self.post_processor.run_post_episode_tasks()`

---

## 작업 상세

### Step 1: 신규 모듈 생성

**파일**: `modules/core/stage4_post_processor.py` (~530줄)

```python
"""
[B-1-1] Stage4 Post-Processor — PASS 후 데이터 정산 및 세션 종료

stage4_orchestrator.py에서 분리된 후처리 로직.
V64 위임 패턴: Stage4Orchestrator → Stage4PostProcessor
"""
import json
import logging
import os


class Stage4PostProcessor:
    """[B-1-1] Stage4 PASS 후처리 전담 모듈"""

    def __init__(self, ctx) -> None:
        """
        Args:
            ctx: Stage4Context 인스턴스
        """
        self.ctx = ctx

    def process_pass_result(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        output_dir,
        v50_modules_available: bool,
    ) -> bool:
        """[4-R1-c] Pass result post-processing. Returns False on DB save failure."""
        # === 기존 _process_pass_result 본문 그대로 이동 ===
        # self.ctx 접근은 동일하게 유지
        ...

    def run_post_episode_tasks(self) -> None:
        """[4-R1-d] Session wrap-up: logs, vector sync."""
        # === 기존 _run_post_episode_tasks 본문 그대로 이동 ===
        ...
```

**변환 규칙**:
- `self.ctx` 접근 → **변경 없음** (동일 Stage4Context 참조)
- `self.app` 접근 → 없음 (이 메서드들은 self.app 미사용, 이미 DI 전환 완료)
- import 필요: `json`, `logging`, `os` (기존 orchestrator에서 사용)
- `_extract_chain_link()` 호출 (L1104 부근) → orchestrator에 남아있으므로 `self.ctx`를 통해 orchestrator 참조가 필요하거나, 별도 파라미터로 전달

**_extract_chain_link 의존성 해결**:
`_process_pass_result` 내부(L1104-1133)에서 `self._extract_chain_link()`를 호출함.
이 메서드는 Context Builder 그룹(L254-303)에 속하므로 post_processor로 이동하지 않음.

**해결 방법**: `_extract_chain_link` 함수를 파라미터로 주입하거나, orchestrator에서 호출 후 결과를 전달.

→ **권장**: `extract_chain_link_fn` 콜백 파라미터 추가.

```python
def process_pass_result(
    self,
    *,
    next_ep: int,
    final_manuscript: str,
    final_title: str,
    final_state_updates: dict,
    blueprint: dict,
    arc_data: dict,
    output_dir,
    v50_modules_available: bool,
    extract_chain_link_fn=None,  # [B-1-1] 콜백: orchestrator._extract_chain_link
) -> bool:
```

호출부에서:
```python
self.post_processor.process_pass_result(
    ...,
    extract_chain_link_fn=self._extract_chain_link,
)
```

---

### Step 2: stage4_orchestrator.py 수정

#### 2-a. import 추가

```python
from modules.core.stage4_post_processor import Stage4PostProcessor
```

#### 2-b. __init__ 수정 (L228-235)

**After**:
```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._post_processor = None  # [B-1-1] lazy init
```

#### 2-c. post_processor 프로퍼티 추가 (ctx 프로퍼티 아래)

```python
@property
def post_processor(self):
    """[B-1-1] Post-Processor 서브모듈 (lazy init)"""
    if self._post_processor is None:
        self._post_processor = Stage4PostProcessor(self.ctx)
    return self._post_processor
```

#### 2-d. 호출 지점 변경 — L1587

**Before**:
```python
if not self._process_pass_result(
    next_ep=next_ep,
    final_manuscript=final_manuscript,
    final_title=final_title,
    final_state_updates=final_state_updates,
    blueprint=blueprint,
    arc_data=arc_data,
    output_dir=output_dir,
    v50_modules_available=v50_modules_available,
):
```

**After**:
```python
if not self.post_processor.process_pass_result(
    next_ep=next_ep,
    final_manuscript=final_manuscript,
    final_title=final_title,
    final_state_updates=final_state_updates,
    blueprint=blueprint,
    arc_data=arc_data,
    output_dir=output_dir,
    v50_modules_available=v50_modules_available,
    extract_chain_link_fn=self._extract_chain_link,
):
```

#### 2-e. 호출 지점 변경 — L1600

**Before**:
```python
self._run_post_episode_tasks()
```

**After**:
```python
self.post_processor.run_post_episode_tasks()
```

#### 2-f. 기존 메서드 삭제

`_process_pass_result` (L803-1301)과 `_run_post_episode_tasks` (L1303-1321)을 **삭제**.
→ 약 519줄 감소.

---

### Step 3: 테스트

**파일**: `tests/test_stage4_post_processor.py` (신규, ~100줄)

```python
"""[B-1-1] Stage4PostProcessor 단위 테스트"""
import pytest
from unittest.mock import MagicMock, patch


class TestPostProcessorInit:
    """초기화 테스트"""

    def test_init_with_ctx(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        ctx = MagicMock()
        pp = Stage4PostProcessor(ctx)
        assert pp.ctx is ctx

    def test_lazy_init_via_orchestrator(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        pp = orch.post_processor
        assert pp is not None
        assert pp.ctx is orch.ctx

    def test_lazy_init_singleton(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        pp1 = orch.post_processor
        pp2 = orch.post_processor
        assert pp1 is pp2


class TestProcessPassResult:
    """process_pass_result 테스트"""

    def _make_pp(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.agents = {
            "director": MagicMock(),
            "manager": MagicMock(),
        }
        ctx.current_project = MagicMock()
        ctx.current_project.db = MagicMock()
        ctx.current_project.name = "test_project"
        ctx.memory = None
        ctx.state_tracker = MagicMock()
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        return Stage4PostProcessor(ctx)

    def test_returns_true_on_success(self):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir="/tmp/test",
            v50_modules_available=False,
            extract_chain_link_fn=lambda **kw: {},
        )
        assert result is True

    def test_returns_false_on_db_failure(self):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.side_effect = Exception("DB error")
        result = pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir="/tmp/test",
            v50_modules_available=False,
            extract_chain_link_fn=lambda **kw: {},
        )
        assert result is False

    def test_hud_update_called(self):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        pp.ctx.agents["director"].on_approve_workflow.return_value = {"applied_updates": {"hp": 100}}
        pp.ctx.sys.hud.snapshot.return_value = {}
        pp.ctx.sys.hud.bulk_update = MagicMock()
        pp.process_pass_result(
            next_ep=1,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={"hp": 100},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir="/tmp/test",
            v50_modules_available=False,
            extract_chain_link_fn=lambda **kw: {},
        )
        pp.ctx.agents["director"].on_approve_workflow.assert_called_once()

    def test_chain_link_fn_called(self):
        pp = self._make_pp()
        pp.ctx.current_project.db.save_manuscript.return_value = True
        mock_fn = MagicMock(return_value={"cliffhanger": "test"})
        pp.process_pass_result(
            next_ep=5,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir="/tmp/test",
            v50_modules_available=False,
            extract_chain_link_fn=mock_fn,
        )
        mock_fn.assert_called_once()


class TestRunPostEpisodeTasks:
    """run_post_episode_tasks 테스트"""

    def test_vector_sync_called_when_operational(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        ctx = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = True
        pp = Stage4PostProcessor(ctx)
        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()
        ctx.memory.sync_v20_drafts.assert_called_once()

    def test_vector_sync_skipped_when_not_operational(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        ctx = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.is_operational.return_value = False
        pp = Stage4PostProcessor(ctx)
        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()
        ctx.memory.sync_v20_drafts.assert_not_called()

    def test_no_memory_safe(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        ctx = MagicMock()
        ctx.memory = None
        pp = Stage4PostProcessor(ctx)
        with patch("builtins.input", return_value=""):
            pp.run_post_episode_tasks()  # should not raise


class TestModuleStructure:
    """모듈 구조 검증"""

    def test_import(self):
        from modules.core.stage4_post_processor import Stage4PostProcessor
        assert Stage4PostProcessor is not None

    def test_orchestrator_has_post_processor_property(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert hasattr(Stage4Orchestrator, "post_processor")

    def test_orchestrator_no_process_pass_result(self):
        """기존 메서드가 orchestrator에서 제거되었는지 확인"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert not hasattr(Stage4Orchestrator, "_process_pass_result")
        assert not hasattr(Stage4Orchestrator, "_run_post_episode_tasks")
```

---

## 검증 게이트

```bash
# Gate 1: 신규 모듈 import
python -c "from modules.core.stage4_post_processor import Stage4PostProcessor; print('OK')"

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 기존 orchestrator에서 메서드 제거 확인
python -c "from modules.core.stage4_orchestrator import Stage4Orchestrator; assert not hasattr(Stage4Orchestrator, '_process_pass_result'); print('REMOVED OK')"

# Gate 4: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage4_post_processor.py -v

# Gate 5: 기존 회귀
pytest tests/test_stage4_orchestrator.py tests/test_npc_history.py tests/test_config_manager.py -v

# Gate 6: pre-commit
pre-commit run --files modules/core/stage4_post_processor.py modules/core/stage4_orchestrator.py tests/test_stage4_post_processor.py
```

---

## 커밋

```
refactor(B-1-1): extract stage4 post-processor to sub-module (519 lines)

- Create modules/core/stage4_post_processor.py with Stage4PostProcessor class
- Move _process_pass_result() + _run_post_episode_tasks() (519 lines)
- V64 delegation pattern: lazy init via post_processor property
- Inject _extract_chain_link as callback to avoid circular dependency
- Add 12 unit tests for post-processor
- Orchestrator: 2,481 → ~1,962 lines (-21%)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- `_process_pass_result` 내부 로직 변경 금지 (그대로 이동만)
- `_extract_chain_link` 메서드 이동 금지 (orchestrator에 유지)
- 다른 메서드 이동 금지 (이번 오더는 post-processor만)
- dataclass 정의 변경 금지
- main_a.py 변경 금지

---

## 향후 계획 (참고용, 이번 오더 범위 아님)

| 순서 | 추출 대상 | 예상 줄 수 | 위험도 |
|------|----------|-----------|--------|
| **B-1-1** (이번) | Post-Processor | 519 | 낮음 |
| B-1-2 | Context Builders | ~590 | 낮음 |
| B-1-3 | Interview Loop | ~862 | 중 |
| B-1-4 | chief_writer ManuscriptAnalyzer | ~277 | 낮음 |
| B-1-5 | chief_writer QualityGate | ~411 | 중 |
