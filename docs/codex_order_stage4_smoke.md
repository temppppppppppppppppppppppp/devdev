# Codex Order: Stage 4 스모크 테스트 (Blueprint → 원고)

> **목표**: Stage 3에서 생성한 Blueprint를 Stage 4에 투입, mock LLM으로 원고 3편을 생산하여 DB + 파일에 저장
> **범위**: pytest 테스트 1개 + standalone 스크립트 1개 신규
> **전제**: Stage 2(arcs 3개) + Stage 3(blueprints 3개) 완료 상태 (`코덱스_테스트` 프로젝트)
> **위험도**: 낮음 (테스트 프로젝트만, 프로덕션 코드 무변경)
> **API 비용**: $0 (LLM mock)

---

## 배경

Stage 2 → Stage 3 스모크가 완료되어 `코덱스_테스트` 프로젝트 DB에 arcs 3개 + blueprints 3개가 존재.
이번에는 Stage 4 파이프라인(Blueprint → 원고 집필)을 mock LLM으로 실행한다.

```
현재 상태:
- bible: ✅ (골든루트, 투자물, plot_roadmap 60블록)
- arcs: ✅ (3개, ep 1-30)
- blueprints: ✅ (3개, ep 1-3)
- manuscripts: {} (비어있음) ← 이번에 채울 것
```

---

## 핵심 설계: "3-seam mock" 전략

Stage 4는 복잡도가 높다 (인터뷰 루프, 컨텍스트 빌더, 포스트 프로세서).
전체를 실행하면 수십 개의 ctx 속성에 접근하므로, **3개의 깔끔한 이음새(seam)에서 mock**한다:

| Seam | 메서드 | Mock 전략 |
|------|--------|-----------|
| S1 | `_prepare_stage4_session()` | `_SessionConfig` 반환 (mock 에이전트) |
| S2 | `_handle_round_outcome()` | `_RoundOutcome(PASS)` 즉시 반환 |
| S3 | `post_processor.process_pass_result()` | DB 저장 + 파일 저장만 (slim) |

추가 mock:
- `post_processor.run_post_episode_tasks()` → no-op (`input()` 호출 방지)
- `context_builder.prepare_episode_context()` → 최소 dict 반환
- `context_builder.build_mandatory_context()` → 최소 dict 반환
- `context_builder.build_round_context()` → MagicMock 반환
- `StageSpinner` → noop context manager
- `ReferenceAnchor` → noop (build_mandatory_context가 mock이라 사용 안 됨)

**이 전략의 장점**: 메인 루프의 핵심 제어 흐름(에피소드 카운터, Blueprint 로드, Arc 매칭, 루프 종료)을 실제로 검증하면서 LLM 의존성을 완전히 제거.

---

## Part 1: pytest 테스트

### 파일: `tests/e2e/test_l3_stage4_smoke.py`

---

### 1. Import + 상수

```python
"""[L3] Stage4 3-episode smoke test — Blueprint → Manuscript with mocked LLM."""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage4_context import Stage4Context
from modules.core.stage4_orchestrator import (
    Stage4Orchestrator,
    _RoundOutcome,
    _SessionConfig,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "코덱스_테스트"
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / PROJECT_NAME / "project_data.db"

MOCK_MANUSCRIPT = (
    "한시윤은 모니터 속 차트를 응시했다. "
    "검은 선이 가파르게 하락하고 있었다. "
    "이번 생에서는 이 순간을 기다려왔다. "
) * 60  # ~5,000자 이상
```

---

### 2. 유틸리티

```python
@contextmanager
def _noop_spinner(*_args, **_kwargs):
    """StageSpinner 대체 noop context manager."""
    yield MagicMock()  # update_detail() 등 호출 가능


def _normalize_arcs(raw_arcs: object) -> list[dict]:
    """DB anchor arcs → list[dict] 정규화."""
    if isinstance(raw_arcs, list):
        return [arc for arc in raw_arcs if isinstance(arc, dict)]
    if isinstance(raw_arcs, dict):
        values = [arc for arc in raw_arcs.values() if isinstance(arc, dict)]
        return sorted(values, key=lambda arc: arc.get("ep_start", 0) if isinstance(arc.get("ep_start"), int) else 0)
    return []
```

---

### 3. Fixture

```python
@pytest.fixture
def stage4_env(tmp_path):
    """Stage4 smoke 환경: 복사 DB + bible/arcs/blueprints 로드."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip(f"Real project DB not found: {REAL_PROJECT_DB}")

    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)

    db = DBManager(copied_db)
    bible = db.load_anchor("bible")
    arcs = _normalize_arcs(db.load_anchor("arcs"))

    assert bible, "Bible is empty"
    assert len(arcs) >= 1, f"arcs must be >= 1, got {len(arcs)}"

    # Blueprint 3개 이상 존재 확인
    bp_count = db.get_latest_blueprint_number()
    assert bp_count >= 3, f"blueprints must be >= 3, got {bp_count}"

    # Manuscripts 테이블 초기화 (깨끗한 시작)
    db.cursor.execute("DELETE FROM manuscripts")
    db.conn.commit()

    output_dir = tmp_path / "drafts"
    output_dir.mkdir()

    try:
        yield {
            "db": db,
            "bible": bible,
            "arcs": arcs,
            "output_dir": output_dir,
            "tmp_path": tmp_path,
        }
    finally:
        db.close()
```

---

### 4. Mock current_project 조립

```python
def _make_mock_project(db, bible, arcs, output_dir):
    """current_project mock 조립 — DB 메서드는 실제 위임."""
    project = MagicMock()
    project.db = db
    project.get_blueprint = db.get_blueprint
    project.get_latest_episode_number = db.get_latest_episode_number
    project.arcs = arcs
    project.master_bible = bible
    project.genre = {"type": "investment", "name": "투자물"}
    project.paths.drafts = output_dir
    project.name = "코덱스_테스트"
    # load_v20_anchor — 필요 시 DB에서 로드, 없으면 None
    project.load_v20_anchor = lambda key: db.load_anchor(key) if db else None
    return project
```

---

### 5. Stage4Context 조립

```python
def _make_stage4_ctx(mock_project):
    """Stage4Context 조립 — 필수 5종 + 나머지 None/mock."""
    mock_ui = MagicMock()
    mock_ui.log = print  # 디버그용 출력

    mock_sys = MagicMock()
    mock_sys.guard = None   # purism prompt 스킵
    mock_sys.hud = None     # HUD 스킵

    return Stage4Context(
        ui=mock_ui,
        current_project=mock_project,
        agents={},
        sys=mock_sys,
        state_tracker=None,
        selected_genre={"type": "investment", "name": "투자물"},
        perf_timer=MagicMock(),
        get_int_input=lambda *a, **kw: kw.get("default", 1),
        build_item_acquisition_timeline=lambda *a, **kw: "",
        load_narrative_summaries=lambda: "",
        get_protagonist_name=lambda: "한시윤",
        generate_narrative_summary=lambda *a, **kw: None,
        flush_audit_buffer=lambda: None,
        safe_commit=lambda: None,
    )
```

---

### 6. Seam mock 함수들

```python
def _mock_prepare_session(output_dir):
    """S1: _prepare_stage4_session mock — _SessionConfig 즉시 반환."""
    return _SessionConfig(
        chief_writer=MagicMock(),
        manuscript_validator=MagicMock(),
        consistency_validator=MagicMock(),
        blocking_validator=MagicMock(),
        continuity_validator=MagicMock(),
        s4_genre_type="investment",
        story_context="- 장르: investment\n- 주인공 이름: 한시윤",
        style_guide="카카오: 사이다 전개",
        target_ep=3,
        output_dir=output_dir,
        v50_modules_available=False,
        total_planned_ep=3,
    )


def _mock_handle_round_outcome(*, round_ctx):
    """S2: _handle_round_outcome mock — 항상 PASS."""
    next_ep = round_ctx.next_ep if hasattr(round_ctx, "next_ep") else 1
    return _RoundOutcome(
        final_manuscript=MOCK_MANUSCRIPT,
        final_title=f"제{next_ep}화 골든루트",
        final_state_updates={},
        should_return=False,
    )


def _make_slim_process_pass_result(db, output_dir):
    """S3: post_processor.process_pass_result slim 대체."""
    def slim(*, next_ep, final_manuscript, final_title, **kwargs):
        # DB 저장
        db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)
        db.conn.commit()
        # 파일 저장
        file_path = output_dir / f"ep_{next_ep:04d}.txt"
        file_path.write_text(
            f"# {final_title}\n\n{final_manuscript}", encoding="utf-8"
        )
        return True
    return slim
```

---

### 7. 테스트 함수 — 메인

```python
@patch("modules.core.stage4_orchestrator.StageSpinner", _noop_spinner)
@patch("modules.core.reference_anchor.ReferenceAnchor", MagicMock)
def test_stage4_smoke_3ep(stage4_env):
    """Stage 4 smoke: 3 episodes Blueprint → Manuscript (mock LLM)."""
    db = stage4_env["db"]
    bible = stage4_env["bible"]
    arcs = stage4_env["arcs"]
    output_dir = stage4_env["output_dir"]

    # 1. current_project + ctx 조립
    mock_project = _make_mock_project(db, bible, arcs, output_dir)
    ctx = _make_stage4_ctx(mock_project)

    # 2. Orchestrator 생성
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    # 3. Seam mocks 주입
    orch._prepare_stage4_session = lambda **kw: _mock_prepare_session(output_dir)
    orch._handle_round_outcome = _mock_handle_round_outcome
    orch._post_processor = MagicMock()
    orch._post_processor.process_pass_result = _make_slim_process_pass_result(db, output_dir)
    orch._post_processor.run_post_episode_tasks = MagicMock()

    # context_builder mocks
    orch._context_builder = MagicMock()
    orch._context_builder.prepare_episode_context.return_value = {
        "arc_pos": 1, "total_ep_in_arc": 10, "arc_tactical": "",
        "prev_text": "", "prev_ending": "", "prev_manuscripts_text": "",
        "episode_digest": "", "hud_report": "", "current_inventory": [],
        "current_martial_arts": [], "cumulative_bible": {}, "dead_npcs": [],
        "item_acquisition_timeline": "", "chain_link_section": "",
        "world_state_summary": "",
    }
    orch._context_builder.build_mandatory_context.return_value = {
        "reference_anchor_prompt": "", "mandatory_context": "",
        "anti_trope_prompt": "", "justification_prompt": "",
        "reflexion_prompt": "",
    }

    # 4. 실행
    orch.stage_4_v2_chief_writer(limit_mode=False)

    # 5. 검증
    # 5a. Manuscripts 3개 DB 저장 확인
    for ep in range(1, 4):
        ms = db.get_manuscript(ep)
        assert ms is not None, f"제{ep}화 원고 없음"
        assert len(ms["content"]) >= 4000, f"제{ep}화 원고 너무 짧음: {len(ms['content'])}자"
        assert "한시윤" in ms["content"], f"제{ep}화 원고에 주인공 이름 없음"

    # 5b. 파일 3개 생성 확인
    for ep in range(1, 4):
        fpath = output_dir / f"ep_{ep:04d}.txt"
        assert fpath.exists(), f"{fpath.name} 없음"
        text = fpath.read_text(encoding="utf-8")
        assert len(text) >= 4000, f"{fpath.name} 너무 짧음"

    # 5c. Episode counter 증가 확인
    next_ep = db.get_latest_episode_number()
    assert next_ep == 4, f"next_ep should be 4, got {next_ep}"

    # 5d. _handle_round_outcome이 3번 호출됐는지 확인
    # (직접 mock이라 호출 횟수 추적은 불가 → DB 결과로 간접 확인)


@patch("modules.core.stage4_orchestrator.StageSpinner", _noop_spinner)
@patch("modules.core.reference_anchor.ReferenceAnchor", MagicMock)
def test_stage4_loop_termination(stage4_env):
    """Stage 4 loop terminates when target_ep is reached."""
    db = stage4_env["db"]
    bible = stage4_env["bible"]
    arcs = stage4_env["arcs"]
    output_dir = stage4_env["output_dir"]

    mock_project = _make_mock_project(db, bible, arcs, output_dir)
    ctx = _make_stage4_ctx(mock_project)
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    # target_ep=2 → 2화까지만 집필
    orch._prepare_stage4_session = lambda **kw: _SessionConfig(
        chief_writer=MagicMock(),
        manuscript_validator=MagicMock(),
        consistency_validator=MagicMock(),
        blocking_validator=MagicMock(),
        continuity_validator=MagicMock(),
        s4_genre_type="investment",
        story_context="",
        style_guide="",
        target_ep=2,
        output_dir=output_dir,
        v50_modules_available=False,
        total_planned_ep=3,
    )
    orch._handle_round_outcome = _mock_handle_round_outcome
    orch._post_processor = MagicMock()
    orch._post_processor.process_pass_result = _make_slim_process_pass_result(db, output_dir)
    orch._post_processor.run_post_episode_tasks = MagicMock()
    orch._context_builder = MagicMock()
    orch._context_builder.prepare_episode_context.return_value = {
        "arc_pos": 1, "total_ep_in_arc": 10, "arc_tactical": "",
        "prev_text": "", "prev_ending": "", "prev_manuscripts_text": "",
        "episode_digest": "", "hud_report": "", "current_inventory": [],
        "current_martial_arts": [], "cumulative_bible": {}, "dead_npcs": [],
        "item_acquisition_timeline": "", "chain_link_section": "",
        "world_state_summary": "",
    }
    orch._context_builder.build_mandatory_context.return_value = {
        "reference_anchor_prompt": "", "mandatory_context": "",
        "anti_trope_prompt": "", "justification_prompt": "",
        "reflexion_prompt": "",
    }

    orch.stage_4_v2_chief_writer(limit_mode=False)

    # 2화까지만 저장되었는지 확인
    assert db.get_manuscript(1) is not None
    assert db.get_manuscript(2) is not None
    assert db.get_manuscript(3) is None, "3화가 저장됨 — target_ep=2인데 초과"
    assert db.get_latest_episode_number() == 3  # next_ep = 3 (2화 이후)


@patch("modules.core.stage4_orchestrator.StageSpinner", _noop_spinner)
@patch("modules.core.reference_anchor.ReferenceAnchor", MagicMock)
def test_stage4_no_blueprint_stops(stage4_env):
    """Stage 4 loop stops when blueprint is missing."""
    db = stage4_env["db"]
    bible = stage4_env["bible"]
    arcs = stage4_env["arcs"]
    output_dir = stage4_env["output_dir"]

    # Blueprint 전부 삭제 → 1화 시작 시 "Blueprint 없음" 으로 즉시 종료
    db.cursor.execute("DELETE FROM blueprints")
    db.conn.commit()

    mock_project = _make_mock_project(db, bible, arcs, output_dir)
    ctx = _make_stage4_ctx(mock_project)
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    orch._prepare_stage4_session = lambda **kw: _mock_prepare_session(output_dir)
    orch._handle_round_outcome = _mock_handle_round_outcome
    orch._post_processor = MagicMock()
    orch._post_processor.process_pass_result = _make_slim_process_pass_result(db, output_dir)
    orch._post_processor.run_post_episode_tasks = MagicMock()
    orch._context_builder = MagicMock()
    orch._context_builder.prepare_episode_context.return_value = {
        "arc_pos": 1, "total_ep_in_arc": 10, "arc_tactical": "",
        "prev_text": "", "prev_ending": "", "prev_manuscripts_text": "",
        "episode_digest": "", "hud_report": "", "current_inventory": [],
        "current_martial_arts": [], "cumulative_bible": {}, "dead_npcs": [],
        "item_acquisition_timeline": "", "chain_link_section": "",
        "world_state_summary": "",
    }
    orch._context_builder.build_mandatory_context.return_value = {
        "reference_anchor_prompt": "", "mandatory_context": "",
        "anti_trope_prompt": "", "justification_prompt": "",
        "reflexion_prompt": "",
    }

    orch.stage_4_v2_chief_writer(limit_mode=False)

    # 원고 0개 (blueprint 없어서 즉시 종료)
    assert db.get_manuscript(1) is None
    assert db.get_latest_episode_number() == 1


@patch("modules.core.stage4_orchestrator.StageSpinner", _noop_spinner)
@patch("modules.core.reference_anchor.ReferenceAnchor", MagicMock)
def test_stage4_session_none_returns(stage4_env):
    """stage_4_v2_chief_writer returns gracefully when session is None."""
    db = stage4_env["db"]
    bible = stage4_env["bible"]
    arcs = stage4_env["arcs"]
    output_dir = stage4_env["output_dir"]

    mock_project = _make_mock_project(db, bible, arcs, output_dir)
    ctx = _make_stage4_ctx(mock_project)
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    # _prepare_stage4_session → None (데이터 부족)
    orch._prepare_stage4_session = lambda **kw: None

    orch.stage_4_v2_chief_writer(limit_mode=False)

    # 크래시 없이 정상 종료
    assert db.get_manuscript(1) is None
```

**중요 — `_noop_spinner`**:
기존 Stage 3 테스트에서는 `yield`만 했지만, Stage 4에서는 `StageSpinner`가 `with` 블록 내에서 `.update_detail()`을 호출한다.
`_handle_round_outcome`을 mock하므로 실제로 호출되지 않지만, 만약 `_noop_spinner`가 `_run_interview_loop` 내부 다른 곳에서 사용되면 `yield MagicMock()`으로 `update_detail`을 흡수한다.

그런데 **`_handle_round_outcome`을 mock했으므로 `_run_interview_loop` 내부에서 StageSpinner를 직접 import하지 않는다**. StageSpinner는 `_handle_round_outcome` 내부에서만 사용. 따라서 `_noop_spinner`는 사실상 `_handle_round_outcome` 내부용이지만, 이미 mock했으므로 호출되지 않는다.

`@patch`는 혹시 모를 다른 import 경로를 대비한 안전망.

---

## Part 2: standalone 스크립트

### 파일: `scripts/run_stage4_smoke.py`

Part 1과 동일한 mock 전략이나, **실제 프로젝트 DB에 원고를 영구 저장**한다.

```python
"""Stage4 mock smoke runner — 코덱스_테스트 프로젝트.

실제 프로젝트 DB에 mock 원고 3편을 생산/저장하고 파일로 내보낸다.
LLM 호출 mock. API 비용 $0.

Usage:
    python scripts/run_stage4_smoke.py
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.stage4_context import Stage4Context  # noqa: E402
from modules.core.stage4_orchestrator import (  # noqa: E402
    Stage4Orchestrator,
    _RoundOutcome,
    _SessionConfig,
)

PROJECT_NAME = "코덱스_테스트"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME
DB_PATH = PROJECT_DIR / "project_data.db"
MS_OUTPUT_DIR = PROJECT_DIR / "plans" / "manuscripts"

# (이하 _noop_spinner, _normalize_arcs, MOCK_MANUSCRIPT,
#  _make_mock_project, _make_stage4_ctx,
#  _mock_prepare_session, _mock_handle_round_outcome,
#  _make_slim_process_pass_result
#  — Part 1과 동일한 함수를 인라인 정의)
```

**스크립트 본문 (`main` 함수)**:

```python
def main():
    assert DB_PATH.exists(), f"DB 없음: {DB_PATH}"
    MS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    db = DBManager(DB_PATH)

    # 사전 검증
    bible = db.load_anchor("bible")
    assert bible, "Bible이 비어있음"
    arcs = _normalize_arcs(db.load_anchor("arcs"))
    assert len(arcs) >= 1, f"arcs {len(arcs)}개 (최소 1 필요)"
    bp_count = db.get_latest_blueprint_number()
    assert bp_count >= 3, f"blueprints {bp_count}개 (최소 3 필요)"
    print(f"✅ 사전 검증 완료: arcs {len(arcs)}개, blueprints {bp_count}개")

    # 기존 manuscripts 확인 (덮어쓸 것이므로 경고)
    existing_ep = db.get_latest_episode_number()
    if existing_ep > 1:
        print(f"⚠️ 기존 manuscripts 발견 (next_ep={existing_ep}). 삭제 후 진행.")
        db.cursor.execute("DELETE FROM manuscripts")
        db.conn.commit()

    output_dir = MS_OUTPUT_DIR
    mock_project = _make_mock_project(db, bible, arcs, output_dir)
    ctx = _make_stage4_ctx(mock_project)

    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    # Seam mocks
    orch._prepare_stage4_session = lambda **kw: _mock_prepare_session(output_dir)
    orch._handle_round_outcome = _mock_handle_round_outcome
    orch._post_processor = MagicMock()
    orch._post_processor.process_pass_result = _make_slim_process_pass_result(db, output_dir)
    orch._post_processor.run_post_episode_tasks = MagicMock()
    orch._context_builder = MagicMock()
    orch._context_builder.prepare_episode_context.return_value = {
        "arc_pos": 1, "total_ep_in_arc": 10, "arc_tactical": "",
        "prev_text": "", "prev_ending": "", "prev_manuscripts_text": "",
        "episode_digest": "", "hud_report": "", "current_inventory": [],
        "current_martial_arts": [], "cumulative_bible": {}, "dead_npcs": [],
        "item_acquisition_timeline": "", "chain_link_section": "",
        "world_state_summary": "",
    }
    orch._context_builder.build_mandatory_context.return_value = {
        "reference_anchor_prompt": "", "mandatory_context": "",
        "anti_trope_prompt": "", "justification_prompt": "",
        "reflexion_prompt": "",
    }

    print("🚀 Stage 4 시작 (3화, mock LLM)...")
    with patch("modules.core.stage4_orchestrator.StageSpinner", _noop_spinner), \
         patch("modules.core.reference_anchor.ReferenceAnchor", MagicMock):
        orch.stage_4_v2_chief_writer(limit_mode=False)

    # 결과 확인 + JSON 내보내기
    saved_count = 0
    for ep in range(1, 4):
        ms = db.get_manuscript(ep)
        if ms:
            saved_count += 1
            out_path = MS_OUTPUT_DIR / f"manuscript_ep{ep}.json"
            out_path.write_text(
                json.dumps(
                    {"ep_num": ep, "title": ms["title"], "content_length": len(ms["content"]),
                     "content_preview": ms["content"][:500]},
                    ensure_ascii=False, indent=2,
                ),
                encoding="utf-8",
            )
            print(f"📄 제{ep}화 '{ms['title']}' — {len(ms['content'])}자 → {out_path.name}")

    next_ep = db.get_latest_episode_number()
    print(f"\n🎉 완료: {saved_count}편 원고 → DB + {MS_OUTPUT_DIR}")
    print(f"   next_ep = {next_ep}")
    db.close()


if __name__ == "__main__":
    main()
```

---

## 실행 방법

### Part 1: pytest

```bash
set PYTHONIOENCODING=utf-8
pytest tests/e2e/test_l3_stage4_smoke.py -v
```

### Part 2: 스크립트

```bash
cd "C:\Users\User\Desktop\글도비"
python scripts/run_stage4_smoke.py
```

---

## 검증 게이트

```bash
# Gate 1: pytest 통과
set PYTHONIOENCODING=utf-8
pytest tests/e2e/test_l3_stage4_smoke.py -v

# Gate 2: 스크립트 실행 (크래시 없이 완료)
python scripts/run_stage4_smoke.py

# Gate 3: DB에 manuscripts 3개 저장 확인
python -c "from modules.core.db_manager import DBManager; db=DBManager('projects/코덱스_테스트/project_data.db'); assert db.get_latest_episode_number()==4, f'next_ep={db.get_latest_episode_number()}'; print('✅ manuscripts 3개 확인'); db.close()"

# Gate 4: JSON 파일 3개 존재
python -c "from pathlib import Path; ms=list(Path('projects/코덱스_테스트/plans/manuscripts').glob('manuscript_ep*.json')); assert len(ms)>=3, f'{len(ms)}개'; print(f'✅ JSON {len(ms)}개 확인')"

# Gate 5: 전체 회귀 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 6: pre-commit
pre-commit run --files tests/e2e/test_l3_stage4_smoke.py scripts/run_stage4_smoke.py
```

---

## 커밋

```
feat(e2e): add stage4 smoke test — Blueprint-to-Manuscript pipeline with mock LLM
```

push 포함.

---

## 실패 시

- `_run_interview_loop` 내부에서 예상치 못한 ctx 접근 에러 → traceback 보고 후 중단, 어떤 ctx 속성이 필요한지 확인
- Blueprint/Arc 매칭 실패 → DB 내용 확인 (`arcs`의 `ep_start`/`ep_end` 범위가 blueprints의 `ep_num`을 커버하는지)
- `_SessionConfig` import 실패 → `_SessionConfig`는 private이므로 import 경로 확인: `from modules.core.stage4_orchestrator import _SessionConfig`
- 무한 루프 → `get_latest_episode_number()`가 증가하지 않음. `save_manuscript` + `conn.commit()` 확인

---

## 체크리스트

- [ ] `tests/e2e/test_l3_stage4_smoke.py` 생성
- [ ] `scripts/run_stage4_smoke.py` 생성
- [ ] pytest 4개 테스트 통과
- [ ] 스크립트 실행: 크래시 없이 완료
- [ ] DB에 manuscripts 3개 저장 확인
- [ ] `plans/manuscripts/` 에 JSON 3개 생성 확인
- [ ] 전체 회귀 테스트 통과
- [ ] pre-commit 통과
- [ ] 커밋 + push
