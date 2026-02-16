# Codex Order B-1-2: stage4 Context Builder 추출

> 카테고리: 구조 개선 (B-1 모놀리스 분할, 2/3) / 규모: 중 / 위험도: 낮음

---

## 목표

`stage4_orchestrator.py` (1,972줄)에서 **Context Builder 로직** (520줄, 26%)을
`stage4_context_builder.py`로 추출.

V64 위임 패턴 적용:
```python
# stage4_orchestrator.py
from modules.core.stage4_context_builder import Stage4ContextBuilder

class Stage4Orchestrator:
    def __init__(self, app, *, context=None):
        ...
        self._context_builder = None  # lazy init

    @property
    def context_builder(self):
        if self._context_builder is None:
            self._context_builder = Stage4ContextBuilder(self.ctx)
        return self._context_builder
```

---

## 추출 대상

| 메서드 | 라인 | 줄 수 | 역할 |
|--------|------|-------|------|
| `_load_chain_link_section()` | 313-347 | 35 | 직전 화 chain_link DB 로드 → 텍스트 변환 |
| `_build_extended_lookback_digest()` | 353-401 | 48 | 직전 4~10화 원고 발췌 요약 |
| `_prepare_episode_context()` | 407-497 | 91 | 에피소드별 컨텍스트 수집 (Arc 메타 + 이전 원고 + HUD) |
| `_build_mandatory_context()` | 502-809 | 308 | mandatory_context + writer 프롬프트 조립 |
| `_build_round_context()` | 811-868 | 38 | _RoundContext 데이터클래스 인스턴스 생성 |

**호출 지점** (모두 `_run_interview_loop` 내부, L870-1093):
- L930: `self._prepare_episode_context(...)` → `self.context_builder.prepare_episode_context(...)`
- L957: `self._build_mandatory_context(...)` → `self.context_builder.build_mandatory_context(...)`
- L1045: `self._build_round_context(...)` → `self.context_builder.build_round_context(...)`

**내부 호출 (추출 대상끼리)**:
- `_prepare_episode_context` L469 → `self._load_chain_link_section(next_ep)` (함께 이동하므로 문제 없음)
- `_build_mandatory_context` L738 → `self._build_extended_lookback_digest(next_ep)` (함께 이동하므로 문제 없음)

---

## `self.app` 잔여 참조 처리

`_build_mandatory_context` 내부에 `self.app` 참조 2건이 남아 있음. 추출 시 `self.ctx`로 전환:

| 라인 | Before | After | 비고 |
|------|--------|-------|------|
| L752 | `getattr(self.app, "semantic_plot_guard", None)` | `self.ctx.semantic_plot_guard` | 이미 Stage4Context에 존재 |
| L765 | `_pacing_analyzer = getattr(self.app, "pacing_analyzer", None)` | 콜백 파라미터 `pacing_analyzer=None` | Stage4Context에 미존재 → 파라미터로 주입 |

---

## 작업 상세

### Step 1: 신규 모듈 생성

**파일**: `modules/core/stage4_context_builder.py` (~530줄)

```python
"""
[B-1-2] Stage4 Context Builder — 에피소드 컨텍스트 수집 및 프롬프트 조립

stage4_orchestrator.py에서 분리된 컨텍스트 빌더 로직.
V64 위임 패턴: Stage4Orchestrator → Stage4ContextBuilder
"""
import json
import logging
import re

from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
)


class Stage4ContextBuilder:
    """[B-1-2] Stage4 컨텍스트 빌더 전담 모듈"""

    def __init__(self, ctx) -> None:
        """
        Args:
            ctx: Stage4Context 인스턴스
        """
        self.ctx = ctx

    def load_chain_link_section(self, next_ep: int) -> str:
        # === 기존 _load_chain_link_section 본문 그대로 이동 ===
        # self.ctx 접근 동일
        ...

    def build_extended_lookback_digest(self, next_ep: int) -> str:
        # === 기존 _build_extended_lookback_digest 본문 그대로 이동 ===
        ...

    def prepare_episode_context(self, next_ep: int, arc_data: dict, chief_writer) -> dict:
        # === 기존 _prepare_episode_context 본문 그대로 이동 ===
        # 내부 호출: self._load_chain_link_section → self.load_chain_link_section
        ...

    def build_mandatory_context(
        self,
        *,
        next_ep: int,
        arc_data: dict,
        arc_tactical: str,
        prev_text: str,
        prev_ending: str,
        hud_report: str,
        writer_agent,
        anchor_sys,
        s4_genre_type: str,
        v50_modules_available: bool,
        pacing_analyzer=None,  # [B-1-2] 콜백: app.pacing_analyzer (ctx 미존재)
    ) -> dict:
        # === 기존 _build_mandatory_context 본문 그대로 이동 ===
        # 변경 1: self._build_extended_lookback_digest → self.build_extended_lookback_digest
        # 변경 2: getattr(self.app, "semantic_plot_guard", None) → self.ctx.semantic_plot_guard
        # 변경 3: getattr(self.app, "pacing_analyzer", None) → pacing_analyzer 파라미터 사용
        ...

    def build_round_context(self, *, ep_ctx, ctx_prompts, **kwargs) -> "_RoundContext":
        # === 기존 _build_round_context 본문 그대로 이동 ===
        # _RoundContext는 orchestrator에서 import
        ...
```

**변환 규칙**:
- `self.ctx` 접근 → **변경 없음** (동일 Stage4Context 참조)
- `self.app` 접근 → 2건 처리 (위 표 참고)
- 메서드명: `_` prefix 제거 (public API)
- 내부 호출: `self._load_chain_link_section` → `self.load_chain_link_section` (동일 클래스)
- 내부 호출: `self._build_extended_lookback_digest` → `self.build_extended_lookback_digest` (동일 클래스)
- `_RoundContext` import: `from modules.core.stage4_orchestrator import _RoundContext`

**import 목록** (context_builder에 필요):
```python
import json
import logging
import re

from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
    build_justification_guidance as _build_justification,
    build_mandatory_context as _build_writer_mandatory_context,
)
```

**_RoundContext 순환 의존성 해결**:
`_RoundContext`는 orchestrator에 정의되어 있고, `build_round_context`가 이를 반환함.
→ **`_RoundContext`를 지역 import**로 처리:
```python
def build_round_context(self, ...) -> object:
    from modules.core.stage4_orchestrator import _RoundContext
    return _RoundContext(...)
```

---

### Step 2: stage4_orchestrator.py 수정

#### 2-a. import 추가

```python
from modules.core.stage4_context_builder import Stage4ContextBuilder
```

#### 2-b. import 제거

context_builder로 이동하는 import 3개는 orchestrator에서 **제거**:
```python
# 삭제 대상:
from modules.core.writer_prompt_builders import (
    build_anti_trope_instructions as _build_anti_trope,
)
from modules.core.writer_prompt_builders import (
    build_justification_guidance as _build_justification,
)
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
)
```

#### 2-c. __init__ 수정 (L234-236)

**After**:
```python
def __init__(self, app, *, context=None) -> None:
    self.app = app
    self._ctx = context
    self._post_processor = None  # [B-1-1] lazy init
    self._context_builder = None  # [B-1-2] lazy init
```

#### 2-d. context_builder 프로퍼티 추가 (post_processor 프로퍼티 아래)

```python
@property
def context_builder(self):
    """[B-1-2] Context Builder 서브모듈 (lazy init)"""
    if self._context_builder is None:
        self._context_builder = Stage4ContextBuilder(self.ctx)
    return self._context_builder
```

#### 2-e. 호출 지점 변경 — L930

**Before**:
```python
_ep_ctx = self._prepare_episode_context(next_ep, arc_data, chief_writer)
```

**After**:
```python
_ep_ctx = self.context_builder.prepare_episode_context(next_ep, arc_data, chief_writer)
```

#### 2-f. 호출 지점 변경 — L957-968

**Before**:
```python
_ctx_prompts = self._build_mandatory_context(
    next_ep=next_ep,
    arc_data=arc_data,
    arc_tactical=arc_tactical,
    prev_text=prev_text,
    prev_ending=prev_ending,
    hud_report=hud_report,
    writer_agent=writer_agent,
    anchor_sys=_anchor_sys,
    s4_genre_type=s4_genre_type,
    v50_modules_available=v50_modules_available,
)
```

**After**:
```python
_ctx_prompts = self.context_builder.build_mandatory_context(
    next_ep=next_ep,
    arc_data=arc_data,
    arc_tactical=arc_tactical,
    prev_text=prev_text,
    prev_ending=prev_ending,
    hud_report=hud_report,
    writer_agent=writer_agent,
    anchor_sys=_anchor_sys,
    s4_genre_type=s4_genre_type,
    v50_modules_available=v50_modules_available,
    pacing_analyzer=getattr(self.app, "pacing_analyzer", None),
)
```

#### 2-g. 호출 지점 변경 — L1045-1064

**Before**:
```python
_round_ctx = self._build_round_context(
    ep_ctx=_ep_ctx,
    ctx_prompts=_ctx_prompts,
    ...
)
```

**After**:
```python
_round_ctx = self.context_builder.build_round_context(
    ep_ctx=_ep_ctx,
    ctx_prompts=_ctx_prompts,
    ...
)
```

#### 2-h. 기존 메서드 삭제

5개 메서드 삭제 (L313-868):
- `_load_chain_link_section` (L313-347)
- `_build_extended_lookback_digest` (L353-401)
- `_prepare_episode_context` (L407-497)
- `_build_mandatory_context` (L502-809)
- `_build_round_context` (L811-868)

→ 약 520줄 감소 (1,972 → ~1,452줄)

---

### Step 3: 테스트

**파일**: `tests/test_stage4_context_builder.py` (신규, ~150줄)

```python
"""[B-1-2] Stage4ContextBuilder 단위 테스트"""
import pytest
from unittest.mock import MagicMock, patch


class TestContextBuilderInit:
    """초기화 테스트"""

    def test_init_with_ctx(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        cb = Stage4ContextBuilder(ctx)
        assert cb.ctx is ctx

    def test_lazy_init_via_orchestrator(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        cb = orch.context_builder
        assert cb is not None
        assert cb.ctx is orch.ctx

    def test_lazy_init_singleton(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        app = MagicMock()
        orch = Stage4Orchestrator(app)
        orch._ctx = MagicMock()
        cb1 = orch.context_builder
        cb2 = orch.context_builder
        assert cb1 is cb2


class TestLoadChainLinkSection:
    """chain_link 로드 테스트"""

    def _make_cb(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.load_anchor.return_value = {
            "cliffhanger": "적이 나타났다",
            "emotional_state": "긴장",
            "location": "청풍산장",
        }
        return Stage4ContextBuilder(ctx)

    def test_ep1_returns_empty(self):
        cb = self._make_cb()
        assert cb.load_chain_link_section(1) == ""

    def test_loads_chain_link_data(self):
        cb = self._make_cb()
        result = cb.load_chain_link_section(5)
        assert "적이 나타났다" in result
        assert "청풍산장" in result

    def test_no_data_returns_empty(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.load_anchor.return_value = None
        cb = Stage4ContextBuilder(ctx)
        assert cb.load_chain_link_section(5) == ""

    def test_db_exception_returns_empty(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.load_anchor.side_effect = RuntimeError("DB error")
        cb = Stage4ContextBuilder(ctx)
        assert cb.load_chain_link_section(5) == ""


class TestBuildExtendedLookback:
    """확장 Lookback 테스트"""

    def test_ep3_or_less_returns_empty(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        cb = Stage4ContextBuilder(ctx)
        assert cb.build_extended_lookback_digest(3) == ""
        assert cb.build_extended_lookback_digest(1) == ""

    def test_returns_digest_with_excerpts(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.get_recent_manuscript_excerpts.return_value = [
            {"ep_num": 5, "content": "이청풍은 검을 들었다."},
            {"ep_num": 6, "content": "노사부가 웃으며 말했다."},
        ]
        cb = Stage4ContextBuilder(ctx)
        result = cb.build_extended_lookback_digest(10)
        assert "확장 Lookback" in result

    def test_exception_returns_empty(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.get_recent_manuscript_excerpts.side_effect = RuntimeError()
        cb = Stage4ContextBuilder(ctx)
        assert cb.build_extended_lookback_digest(10) == ""


class TestPrepareEpisodeContext:
    """에피소드 컨텍스트 수집 테스트"""

    def _make_cb(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.db.get_manuscript.return_value = {"content": "이전 화 내용 " * 50}
        ctx.current_project.db.get_cumulative_bible.return_value = {"dead_npcs": ["흑풍"]}
        ctx.current_project.db.load_anchor.return_value = None
        ctx.current_project.db.get_recent_manuscript_excerpts.return_value = []
        ctx.build_item_acquisition_timeline.return_value = ""
        ctx.sys.hud.get_v20_hud_report.return_value = "HUD 리포트"
        ctx.world_state = None
        return Stage4ContextBuilder(ctx)

    def test_returns_all_keys(self):
        cb = self._make_cb()
        arc_data = {"ep_start": 1, "ep_count": 10, "tactical_doc": "전술"}
        chief_writer = MagicMock()
        chief_writer._generate_episode_digest.return_value = "다이제스트"
        result = cb.prepare_episode_context(5, arc_data, chief_writer)
        expected_keys = {
            "arc_pos", "total_ep_in_arc", "arc_tactical", "prev_text",
            "prev_ending", "prev_manuscripts_text", "episode_digest",
            "hud_report", "current_inventory", "current_martial_arts",
            "cumulative_bible", "dead_npcs", "item_acquisition_timeline",
            "chain_link_section", "world_state_summary",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_arc_pos_calculation(self):
        cb = self._make_cb()
        arc_data = {"ep_start": 11, "ep_count": 10, "tactical_doc": ""}
        result = cb.prepare_episode_context(15, arc_data, MagicMock())
        assert result["arc_pos"] == 5


class TestBuildMandatoryContext:
    """mandatory_context 조립 테스트"""

    def _make_cb(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        ctx = MagicMock()
        ctx.current_project.genre = {"name": "무협"}
        ctx.current_project.db = MagicMock()
        ctx.current_project.master_bible = {"MasterBible": {}}
        ctx.ui.log = MagicMock()
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.state_tracker = None
        ctx.memory = None
        ctx.foreshadow_tracker = None
        ctx.semantic_plot_guard = None
        ctx.load_narrative_summaries.return_value = ""
        ctx.current_project.load_v20_anchor.return_value = None
        return Stage4ContextBuilder(ctx)

    def test_returns_dict_with_5_keys(self):
        cb = self._make_cb()
        result = cb.build_mandatory_context(
            next_ep=5, arc_data={"arc_no": 1}, arc_tactical="전술",
            prev_text="이전", prev_ending="엔딩", hud_report="HUD",
            writer_agent=MagicMock(), anchor_sys=MagicMock(),
            s4_genre_type="wuxia", v50_modules_available=False,
        )
        assert set(result.keys()) == {
            "reference_anchor_prompt", "mandatory_context",
            "anti_trope_prompt", "justification_prompt", "reflexion_prompt",
        }

    def test_no_writer_agent_returns_empty(self):
        cb = self._make_cb()
        result = cb.build_mandatory_context(
            next_ep=5, arc_data={}, arc_tactical="", prev_text="",
            prev_ending="", hud_report="", writer_agent=None,
            anchor_sys=MagicMock(), s4_genre_type="wuxia",
            v50_modules_available=False,
        )
        assert result["mandatory_context"] == ""

    def test_pacing_analyzer_param_used(self):
        cb = self._make_cb()
        mock_pacing = MagicMock()
        mock_pacing.analyze.return_value = {"score": 0.5}
        mock_pacing.generate_pacing_prompt.return_value = "페이싱 프롬프트"
        result = cb.build_mandatory_context(
            next_ep=5, arc_data={"arc_no": 1}, arc_tactical="",
            prev_text="이전 원고 " * 100, prev_ending="엔딩",
            hud_report="HUD", writer_agent=MagicMock(),
            anchor_sys=MagicMock(), s4_genre_type="wuxia",
            v50_modules_available=False, pacing_analyzer=mock_pacing,
        )
        mock_pacing.analyze.assert_called_once()

    def test_semantic_plot_guard_uses_ctx(self):
        """self.app 대신 self.ctx.semantic_plot_guard 사용 확인"""
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        import inspect
        source = inspect.getsource(Stage4ContextBuilder.build_mandatory_context)
        assert "self.app" not in source
        assert "self.ctx.semantic_plot_guard" in source


class TestBuildRoundContext:
    """_RoundContext 생성 테스트"""

    def test_returns_round_context_instance(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        from modules.core.stage4_orchestrator import _RoundContext
        ctx = MagicMock()
        cb = Stage4ContextBuilder(ctx)
        ep_ctx = {
            "arc_pos": 1, "total_ep_in_arc": 10, "arc_tactical": "",
            "prev_text": "", "prev_ending": "", "prev_manuscripts_text": "",
            "episode_digest": "", "hud_report": "", "current_inventory": [],
            "current_martial_arts": [], "dead_npcs": [],
            "item_acquisition_timeline": "", "chain_link_section": "",
            "world_state_summary": "",
        }
        ctx_prompts = {
            "reference_anchor_prompt": "", "justification_prompt": "",
            "reflexion_prompt": "",
        }
        result = cb.build_round_context(
            ep_ctx=ep_ctx, ctx_prompts=ctx_prompts,
            chief_writer=MagicMock(), manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(), blocking_validator=MagicMock(),
            continuity_validator=MagicMock(), next_ep=1, blueprint={},
            arc_data={}, purism_prompt="", genre_name="무협",
            npc_equipment_summary="", effective_anti_trope="",
            intro_dna="CYNICAL", story_context="", style_guide="",
            mandatory_context="",
        )
        assert isinstance(result, _RoundContext)


class TestModuleStructure:
    """모듈 구조 검증"""

    def test_import(self):
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        assert Stage4ContextBuilder is not None

    def test_orchestrator_has_context_builder_property(self):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert hasattr(Stage4Orchestrator, "context_builder")

    def test_orchestrator_no_legacy_context_methods(self):
        """기존 메서드가 orchestrator에서 제거되었는지 확인"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        assert not hasattr(Stage4Orchestrator, "_load_chain_link_section")
        assert not hasattr(Stage4Orchestrator, "_build_extended_lookback_digest")
        assert not hasattr(Stage4Orchestrator, "_prepare_episode_context")
        assert not hasattr(Stage4Orchestrator, "_build_mandatory_context")
        assert not hasattr(Stage4Orchestrator, "_build_round_context")

    def test_no_self_app_in_context_builder(self):
        """context_builder 모듈에 self.app 참조가 없는지 확인"""
        from modules.core.stage4_context_builder import Stage4ContextBuilder
        import inspect
        source = inspect.getsource(Stage4ContextBuilder)
        assert "self.app" not in source
```

---

## 검증 게이트

```bash
# Gate 1: 신규 모듈 import
python -c "from modules.core.stage4_context_builder import Stage4ContextBuilder; print('OK')"

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 기존 orchestrator에서 메서드 제거 확인
python -c "from modules.core.stage4_orchestrator import Stage4Orchestrator; assert not hasattr(Stage4Orchestrator, '_build_mandatory_context'); print('REMOVED OK')"

# Gate 4: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage4_context_builder.py -v

# Gate 5: 기존 회귀
pytest tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_npc_history.py tests/test_config_manager.py -v

# Gate 6: pre-commit
pre-commit run --files modules/core/stage4_context_builder.py modules/core/stage4_orchestrator.py tests/test_stage4_context_builder.py
```

---

## 커밋

```
refactor(B-1-2): extract stage4 context builders to sub-module (520 lines)

- Create modules/core/stage4_context_builder.py with Stage4ContextBuilder class
- Move 5 context methods: load_chain_link, lookback_digest, episode_context,
  mandatory_context, round_context (520 lines)
- V64 delegation pattern: lazy init via context_builder property
- Migrate 2 self.app refs to self.ctx (semantic_plot_guard) + param (pacing_analyzer)
- Remove writer_prompt_builders imports from orchestrator (moved to context_builder)
- Add unit tests for context builder
- Orchestrator: 1,972 → ~1,452 lines (-26%)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- Context builder 내부 로직 변경 금지 (그대로 이동만, `self.app` 2건만 전환)
- `_RoundContext` / `_SessionConfig` 등 dataclass 이동 금지 (orchestrator에 유지)
- `_extract_chain_link` 메서드 이동 금지 (orchestrator에 유지)
- `_run_interview_loop` / `_handle_round_outcome` / `_run_interview_round` 이동 금지
- `_prepare_stage4_session` / `stage_4_v2_chief_writer` 이동 금지
- main_a.py 변경 금지
- Stage4Context 변경 금지 (`pacing_analyzer`는 파라미터로 주입, ctx에 추가하지 않음)

---

## 향후 계획 (참고용, 이번 오더 범위 아님)

| 순서 | 추출 대상 | 예상 줄 수 | 상태 |
|------|----------|-----------|------|
| ~~B-1-1~~ | ~~Post-Processor~~ | ~~519~~ | ✅ `ed48489` |
| **B-1-2** (이번) | Context Builders | 520 | 진행 중 |
| B-1-3 | Interview Loop | ~540 (나머지) | 미착수 |
| B-1-4 | chief_writer ManuscriptAnalyzer | ~277 | 미착수 |
| B-1-5 | chief_writer QualityGate | ~411 | 미착수 |
