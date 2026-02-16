# Codex Order B-1-3: stage4 Interview Round 추출

> 카테고리: 구조 개선 (B-1 모놀리스 분할, 3/3) / 규모: 대 / 위험도: 낮음~중

---

## 목표

`stage4_orchestrator.py` (1,415줄)에서 **Interview Round 로직** (`_run_interview_round`, 540줄, 38%)을
`stage4_interview_round.py`로 추출.

V64 위임 패턴 적용:
```python
# stage4_orchestrator.py
from modules.core.stage4_interview_round import Stage4InterviewRound

class Stage4Orchestrator:
    def __init__(self, app, *, context=None):
        ...
        self._interview_round = None  # lazy init

    @property
    def interview_round(self):
        if self._interview_round is None:
            self._interview_round = Stage4InterviewRound(self.ctx)
        return self._interview_round
```

이 완료 시 stage4 모놀리스 분할 **3/3 완료**: orchestrator ~890줄.

---

## 추출 대상

| 메서드 | 라인 | 줄 수 | 역할 |
|--------|------|-------|------|
| `_run_interview_round()` | 670-1209 | 540 | 단일 면담 라운드: 앙상블 생성 → Python 검증 → Director 심사 |

**호출 지점** (`_handle_round_outcome` 내부):
- L563: `self._run_interview_round(...)` → `self.interview_round.run(...)`

**`_handle_round_outcome`은 이동하지 않음** — 3라운드 루프 + 냉동인간 폴백은 오케스트레이터의 조율 책임.

---

## `self.app` 잔여 참조 처리 (4건)

`_run_interview_round` 내부에 `self.app` 참조 4건이 있음. 모두 동일 패턴:
`state_tracker=getattr(self.app, "state_tracker", None)` → ChiefWriter 메서드에 전달

| 라인 | 호출 대상 | 변환 |
|------|----------|------|
| L746 | `chief_writer.generate_ensemble(state_tracker=...)` | `self.ctx.state_tracker` |
| L785 | `chief_writer.patch_with_feedback(state_tracker=...)` | `self.ctx.state_tracker` |
| L818 | `chief_writer.regenerate_with_feedback(state_tracker=...)` (패치 폴백) | `self.ctx.state_tracker` |
| L848 | `chief_writer.regenerate_with_feedback(state_tracker=...)` (일반) | `self.ctx.state_tracker` |

**근거**: `state_tracker`는 이미 Stage4Context에 존재 (`self.ctx.state_tracker`).

---

## 작업 상세

### Step 1: 신규 모듈 생성

**파일**: `modules/core/stage4_interview_round.py` (~550줄)

```python
"""
[B-1-3] Stage4 Interview Round — 단일 면담 라운드 실행

stage4_orchestrator.py에서 분리된 면담 로직.
V64 위임 패턴: Stage4Orchestrator → Stage4InterviewRound
"""
import logging


class Stage4InterviewRound:
    """[B-1-3] Stage4 단일 면담 라운드 실행 모듈"""

    def __init__(self, ctx) -> None:
        """
        Args:
            ctx: Stage4Context 인스턴스
        """
        self.ctx = ctx

    def run(
        self,
        *,
        round_num: int,
        stage4_spinner,
        director_feedback: str,
        previous_attempt: dict,
        round_ctx,  # _RoundContext (지역 import 또는 타입 생략)
    ):
        """[4-R1-e-1] Single interview round: generation, validation, judgment.

        Returns _InterviewRoundResult.
        """
        from modules.core.stage4_orchestrator import _InterviewRoundResult, _PATCH_REWRITE_THRESHOLD

        # === 기존 _run_interview_round 본문 그대로 이동 ===
        # 변경 1: self.app → self.ctx (state_tracker 4건)
        # 변경 2: self._time_consistency_warnings → self.ctx 경유 or 속성 유지
        ...
```

**변환 규칙**:
- `self.ctx` 접근 → **변경 없음** (동일 Stage4Context 참조)
- `self.app` 접근 → 4건 모두 `self.ctx.state_tracker`로 전환
- 메서드명: `_run_interview_round` → `run` (public API)
- `_InterviewRoundResult`, `_PATCH_REWRITE_THRESHOLD` → 지역 import로 해결
- `self._time_consistency_warnings` → 호출부(`_handle_round_outcome` → `_run_interview_loop`)에서 관리.
  sub-module에서는 `_InterviewRoundResult`로 반환하고, orchestrator가 `self._time_consistency_warnings`에 저장.

**`_time_consistency_warnings` 처리 방안**:
현재 L1177-1179에서 `self._time_consistency_warnings`에 append함.
이 속성은 `_run_interview_loop` L347에서 에피소드마다 리셋됨.
→ **방법**: sub-module의 `run()`이 반환하는 `_InterviewRoundResult`에 `time_warnings: list` 필드 추가하거나,
별도 속성 `self.time_warnings`로 sub-module에 저장 후 orchestrator가 읽음.

→ **권장**: 가장 단순한 방법 — `Stage4InterviewRound`에 `time_warnings` 속성 추가.
```python
class Stage4InterviewRound:
    def __init__(self, ctx):
        self.ctx = ctx
        self.time_warnings = []  # [V66.1] 에피소드별 시간선 경고

    def run(self, ...):
        ...
        # L1177-1179 대응:
        if _time_warnings:
            self.time_warnings.extend(_time_warnings)
        ...
```
orchestrator의 `_run_interview_loop`에서:
```python
self.interview_round.time_warnings = []  # 에피소드마다 리셋 (기존 L347)
```

---

### Step 2: stage4_orchestrator.py 수정

#### 2-a. import 추가

```python
from modules.core.stage4_interview_round import Stage4InterviewRound
```

#### 2-b. __init__ 수정

**After**:
```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._post_processor = None      # [B-1-1] lazy init
    self._context_builder = None     # [B-1-2] lazy init
    self._interview_round = None     # [B-1-3] lazy init
```

#### 2-c. interview_round 프로퍼티 추가

```python
@property
def interview_round(self):
    """[B-1-3] Interview Round 서브모듈 (lazy init)"""
    if self._interview_round is None:
        self._interview_round = Stage4InterviewRound(self.ctx)
    return self._interview_round
```

#### 2-d. 호출 지점 변경 — L563

**Before**:
```python
_round_result = self._run_interview_round(
    round_num=interview_round,
    stage4_spinner=stage4_spinner,
    director_feedback=director_feedback,
    previous_attempt=previous_attempt,
    round_ctx=round_ctx,
)
```

**After**:
```python
_round_result = self.interview_round.run(
    round_num=interview_round,
    stage4_spinner=stage4_spinner,
    director_feedback=director_feedback,
    previous_attempt=previous_attempt,
    round_ctx=round_ctx,
)
```

#### 2-e. `_time_consistency_warnings` 리셋 변경

현재 `_run_interview_loop` 내 (약 L347):
```python
self._time_consistency_warnings = []  # [V70] 에피소드마다 리셋
```
→ 변경:
```python
self.interview_round.time_warnings = []  # [V70] 에피소드마다 리셋
```

그리고 `_cv_context`에서 참조하는 부분 (이미 context_builder로 이동됨)이 있으면 동일 변경.
**확인**: `_cv_context["time_warnings"]`는 `_run_interview_round` 내부(L938)에서 설정되므로,
sub-module 내에서 `self.time_warnings`를 직접 참조하면 됨:
```python
_cv_context["time_warnings"] = self.time_warnings  # 기존: getattr(self, "_time_consistency_warnings", [])
```

#### 2-f. 기존 메서드 삭제

`_run_interview_round` (L670-1209) 삭제.
→ 약 540줄 감소 (1,415 → ~890줄)

---

### Step 3: 테스트

**파일**: `tests/test_stage4_interview_round.py` (신규, ~150줄)

```python
"""[B-1-3] Stage4InterviewRound 단위 테스트"""
import pytest
from unittest.mock import MagicMock, patch


class TestInterviewRoundInit:
    """초기화 테스트"""

    def test_init_with_ctx(self):
        from modules.core.stage4_interview_round import Stage4InterviewRound
        ctx = MagicMock()
        ir = Stage4InterviewRound(ctx)
        assert ir.ctx is ctx
        assert ir.time_warnings == []

    def test_lazy_init_via_orchestrator(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        ir = orch.interview_round
        assert ir is not None
        assert ir.ctx is orch.ctx

    def test_lazy_init_singleton(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        ir1 = orch.interview_round
        ir2 = orch.interview_round
        assert ir1 is ir2


class TestInterviewRoundRun:
    """run() 기본 동작 테스트"""

    def _make_ir(self):
        from modules.core.stage4_interview_round import Stage4InterviewRound
        ctx = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
        ctx.current_project.db.get_recent_manuscripts.return_value = []
        ctx.current_project.db.get_manuscript.return_value = None
        ctx.state_tracker = MagicMock()
        ctx.state_tracker.npc_registry = {}
        ctx.state_tracker.item_state_registry = {}
        ctx.perf_timer = MagicMock()
        ctx.agents = {"director": MagicMock()}
        return Stage4InterviewRound(ctx)

    def _make_round_ctx(self):
        from modules.core.stage4_orchestrator import _RoundContext
        return _RoundContext(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=5, blueprint={"integrated_scenario": "test"},
            arc_data={"arc_no": 1}, arc_pos=1, total_ep_in_arc=10,
            arc_tactical="전술", prev_text="이전", prev_ending="엔딩",
            prev_manuscripts_text="", episode_digest="", hud_report="HUD",
            current_inventory=[], current_martial_arts=[], dead_npcs=[],
            item_acquisition_timeline="", chain_link_section="",
            world_state_summary="", purism_prompt="", genre_name="무협",
            npc_equipment_summary="", effective_anti_trope="",
            intro_dna="CYNICAL", story_context="", style_guide="",
            reference_anchor_prompt="", mandatory_context="",
            justification_prompt="", reflexion_prompt="",
        )

    def test_pass_verdict_returns_pass(self):
        ir = self._make_ir()
        round_ctx = self._make_round_ctx()
        # Chief Writer generates candidates
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "테스트 원고 " * 500, "strategy_name": "balanced", "title": "테스트"},
        ]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 5000}},
        ]
        round_ctx.consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
        round_ctx.blocking_validator.validate.return_value = {"failures": []}
        round_ctx.continuity_validator.validate.return_value = {"violations": [], "warnings": []}
        round_ctx.continuity_validator.check_frustration_streak.return_value = []
        # Director passes
        ir.ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A", "verdict": "PASS", "score": 85,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "테스트 원고 " * 500, "title": "테스트"},
            "state_updates": {},
        }
        result = ir.run(
            round_num=0, stage4_spinner=MagicMock(),
            director_feedback="", previous_attempt={}, round_ctx=round_ctx,
        )
        assert result.verdict == "PASS"
        assert result.final_manuscript is not None

    def test_reject_verdict_returns_reject(self):
        ir = self._make_ir()
        round_ctx = self._make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "테스트 원고 " * 500, "strategy_name": "balanced", "title": "테스트"},
        ]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 5000}},
        ]
        round_ctx.consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
        round_ctx.blocking_validator.validate.return_value = {"failures": []}
        round_ctx.continuity_validator.validate.return_value = {"violations": [], "warnings": []}
        round_ctx.continuity_validator.check_frustration_streak.return_value = []
        ir.ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A", "verdict": "REJECT", "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제1"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "테스트 원고"},
        }
        result = ir.run(
            round_num=0, stage4_spinner=MagicMock(),
            director_feedback="", previous_attempt={}, round_ctx=round_ctx,
        )
        assert result.verdict == "REJECT"
        assert result.final_manuscript is None

    def test_empty_candidates_returns_empty(self):
        ir = self._make_ir()
        round_ctx = self._make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []
        result = ir.run(
            round_num=0, stage4_spinner=MagicMock(),
            director_feedback="", previous_attempt={}, round_ctx=round_ctx,
        )
        assert result.verdict == "EMPTY"

    def test_time_warnings_stored(self):
        ir = self._make_ir()
        round_ctx = self._make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            {"manuscript": "테스트 원고 " * 500, "strategy_name": "balanced", "title": "테스트"},
        ]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 5000}},
        ]
        round_ctx.consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
        round_ctx.blocking_validator.validate.return_value = {"failures": []}
        round_ctx.continuity_validator.validate.return_value = {"violations": [], "warnings": []}
        round_ctx.continuity_validator.check_frustration_streak.return_value = []
        ir.ctx.state_tracker.check_time_consistency.return_value = ["시간 역행 감지"]
        ir.ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A", "verdict": "PASS", "score": 85,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "테스트 원고 " * 500, "title": "테스트"},
            "state_updates": {},
        }
        ir.run(
            round_num=0, stage4_spinner=MagicMock(),
            director_feedback="", previous_attempt={}, round_ctx=round_ctx,
        )
        assert len(ir.time_warnings) >= 1

    def test_state_tracker_from_ctx_not_app(self):
        """self.app 대신 self.ctx.state_tracker 사용 확인"""
        from modules.core.stage4_interview_round import Stage4InterviewRound
        import inspect
        source = inspect.getsource(Stage4InterviewRound.run)
        assert "self.app" not in source
        assert "self.ctx.state_tracker" in source or "self.ctx" in source


class TestModuleStructure:
    """모듈 구조 검증"""

    def test_import(self):
        from modules.core.stage4_interview_round import Stage4InterviewRound
        assert Stage4InterviewRound is not None

    def test_orchestrator_has_interview_round_property(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert hasattr(Stage4Orchestrator, "interview_round")

    def test_orchestrator_no_legacy_interview_method(self):
        """기존 메서드가 orchestrator에서 제거되었는지 확인"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert not hasattr(Stage4Orchestrator, "_run_interview_round")

    def test_no_self_app_in_interview_round(self):
        """interview_round 모듈에 self.app 참조가 없는지 확인"""
        from modules.core.stage4_interview_round import Stage4InterviewRound
        import inspect
        source = inspect.getsource(Stage4InterviewRound)
        assert "self.app" not in source
```

---

## 검증 게이트

```bash
# Gate 1: 신규 모듈 import
python -c "from modules.core.stage4_interview_round import Stage4InterviewRound; print('OK')"

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 기존 orchestrator에서 메서드 제거 확인
python -c "from modules.core.stage4_orchestrator import Stage4Orchestrator; assert not hasattr(Stage4Orchestrator, '_run_interview_round'); print('REMOVED OK')"

# Gate 4: self.app 제거 확인
python -c "import inspect; from modules.core.stage4_interview_round import Stage4InterviewRound; assert 'self.app' not in inspect.getsource(Stage4InterviewRound); print('NO SELF.APP OK')"

# Gate 5: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage4_interview_round.py -v

# Gate 6: 기존 회귀
pytest tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_stage4_context_builder.py tests/test_npc_history.py tests/test_config_manager.py -v

# Gate 7: pre-commit
pre-commit run --files modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py tests/test_stage4_interview_round.py
```

---

## 커밋

```
refactor(B-1-3): extract stage4 interview round to sub-module (540 lines)

- Create modules/core/stage4_interview_round.py with Stage4InterviewRound class
- Move _run_interview_round() (540 lines): generation, validation, judgment
- V64 delegation pattern: lazy init via interview_round property
- Migrate 4 self.app refs to self.ctx.state_tracker
- Add time_warnings attribute for cross-round state
- Add unit tests for interview round
- Orchestrator: 1,415 → ~890 lines (-37%)
- Stage4 monolith split complete: 4 modules (orchestrator + 3 sub-modules)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- `_run_interview_round` 내부 로직 변경 금지 (그대로 이동, `self.app` 4건만 전환)
- `_handle_round_outcome` 이동 금지 (orchestrator에 유지 — 3라운드 루프 조율 담당)
- `_run_interview_loop` 이동 금지 (orchestrator에 유지 — 메인 루프 조율 담당)
- `_prepare_stage4_session` / `stage_4_v2_chief_writer` 이동 금지
- `_extract_chain_link` 이동 금지
- dataclass 정의 이동 금지 (orchestrator에 유지, 지역 import로 참조)
- module-level 헬퍼 (`_detect_npc_overexposure`, `_detect_cross_episode_repetition`) 이동 금지
- main_a.py 변경 금지
- Stage4Context 변경 금지

---

## 완료 시 stage4 분할 전체 현황

| 모듈 | 줄 수 | 역할 |
|------|-------|------|
| `stage4_orchestrator.py` | ~890 | 메인 루프 + 3라운드 조율 + 세션 준비 + 진입점 |
| `stage4_post_processor.py` | 543 | PASS 후처리 |
| `stage4_context_builder.py` | 570 | 컨텍스트 빌더 5개 |
| `stage4_interview_round.py` | ~550 | 단일 면담 라운드 (생성+검증+심사) |
| **합계** | ~2,553 | (원본 2,481 + 위임 코드 ~72줄) |

→ orchestrator 원본 2,481줄 → 890줄 (-64%), **stage4 모놀리스 분할 완료**.
