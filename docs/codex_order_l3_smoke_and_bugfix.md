# Codex Order: ✅ 상태 버그 수정 + L3 골든루트 파이프라인 스모크 테스트

> **목표**: (1) 빈 프로젝트에 ✅ 표시되는 버그 수정 + (2) 실물 골든루트 데이터로 Stage 2 파이프라인 스모크 테스트
> **위험도**: 낮음 (프로덕션 코드 1줄 수정 + 테스트 신규)
> **API 비용**: $0 (LLM 전부 mock)

---

## Part 1: ✅ 상태 버그 수정

### 원인
`modules/core/system.py` L61-83 `check_v20_readiness()`:
```python
bible_data = self.project.db.load_anchor("bible")
status["Stage 0 (Bible)"] = bible_data is not None  # ← 빈 dict {} 도 True
```

### 수정
`is not None` → truthiness 체크 (빈 dict/list는 False):

```python
bible_data = self.project.db.load_anchor("bible")
status["Stage 0 (Bible)"] = bool(bible_data)

vols_data = self.project.db.load_anchor("volumes")
status["Stage 1 (Volumes)"] = bool(vols_data)

arcs_data = self.project.db.load_anchor("arcs")
status["Stage 2 (Arcs)"] = bool(arcs_data)
```

### 테스트
`tests/test_stage_status.py` 신규:

```python
"""[L3] check_v20_readiness 상태 체크 정확성 테스트."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.system import SystemManager


@pytest.fixture
def sys_mgr(tmp_path):
    """SystemManager + mock project + real DB."""
    from modules.core.db_manager import DBManager
    db = DBManager(tmp_path / "test.db")
    project = MagicMock()
    project.db = db
    mgr = SystemManager.__new__(SystemManager)
    mgr.project = project
    yield mgr
    db.close()


class TestCheckV20Readiness:
    def test_empty_db_all_false(self, sys_mgr):
        """빈 DB → 전부 False."""
        status = sys_mgr.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is False
        assert status["Stage 1 (Volumes)"] is False
        assert status["Stage 2 (Arcs)"] is False

    def test_empty_dict_is_false(self, sys_mgr):
        """빈 dict 저장 → False."""
        sys_mgr.project.db.save_anchor("bible", {})
        status = sys_mgr.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is False

    def test_empty_list_is_false(self, sys_mgr):
        """빈 list 저장 → False."""
        sys_mgr.project.db.save_anchor("arcs", [])
        status = sys_mgr.check_v20_readiness()
        assert status["Stage 2 (Arcs)"] is False

    def test_real_data_is_true(self, sys_mgr):
        """실제 데이터 → True."""
        sys_mgr.project.db.save_anchor("bible", {"MasterBible": {"ProjectData": {}}})
        sys_mgr.project.db.save_anchor("volumes", [{"vol_no": 1}])
        sys_mgr.project.db.save_anchor("arcs", [{"arc_no": 1}])
        status = sys_mgr.check_v20_readiness()
        assert status["Stage 0 (Bible)"] is True
        assert status["Stage 1 (Volumes)"] is True
        assert status["Stage 2 (Arcs)"] is True
```

---

## Part 2: L3 골든루트 파이프라인 스모크 테스트

### 개요

실물 골든루트 데이터(bible + treatment)로 Stage 2 파이프라인이 **크래시 없이** 2블록을 처리하는지 검증.
LLM 호출은 전부 mock. API 비용 $0.

### 데이터 소스

| 파일 | 경로 | 내용 |
|------|------|------|
| Bible | `bible/골든루트_bi.json` | MasterBible (투자물, plot_roadmap 비어있음) |
| Treatment | `treatments/골든루트_tr_block_ALL.json` | 60블록 리스트 |

### 핵심: plot_roadmap 주입

Bible의 `plot_roadmap`이 비어있으므로, treatment 블록 2개의 `content`를 주입:

```python
import json

bible = json.load(open("bible/골든루트_bi.json", encoding="utf-8"))
treatments = json.load(open("treatments/골든루트_tr_block_ALL.json", encoding="utf-8"))

# treatment.content가 곧 plot_roadmap 엔트리 포맷 (context/event_villain/solution/reward)
bible["MasterBible"]["plot_roadmap"] = [
    treatments[0]["content"],  # Block 1
    treatments[1]["content"],  # Block 2
]
```

### 테스트 파일: `tests/e2e/test_l3_golden_route.py`

#### 구조

```
class TestL3Setup:         # 데이터 로딩 + DB 준비 검증
class TestL3PipelineSmoke: # Stage 2 파이프라인 실행 (mock LLM)
```

#### Mock 전략

Stage 2 파이프라인에서 LLM을 호출하는 에이전트 메서드를 **전부 mock**:

| 에이전트 | 메서드 | mock 반환값 |
|----------|--------|-------------|
| `agents["analyst"]` | `enrich_raw_block_async()` | 입력 block을 그대로 반환 + `joint_docs: {}` 추가 |
| `agents["analyst"]` | `stitch_joints()` | `{"status": "OK"}` |
| `agents["analyst"]` | `get_lack_report()` | `{"status": "ok", "martial_deficit": "없음"}` |
| `agents["analyst"]` | `plan_single_arc_v20()` | 유효한 arc dict (아래 참고) |
| `agents["four_phase_arc_generator"]` | `generate()` | 유효한 arc dict |
| `agents["director"]` | `audit_strategic_plan()` | `{"verdict": "PASS", "score": 80, "feedback": {}}` |
| `arc_draft_validator` | `validate()` | `{"passed": True, "warnings": [], "score": 85}` |
| `arc_corrector` | (사용 안 됨 — validator PASS이므로) | - |
| `constraint_compiler` | `compile()` | `""` (빈 문자열) |
| `constitutional_checker` | (있으면) | mock |
| `self_reflector` | (있으면) | mock |

**유효한 arc dict (mock 반환 템플릿)**:
```python
MOCK_ARC = {
    "arc_no": 1,       # 동적으로 설정
    "ep_start": 1,     # 동적으로 설정
    "ep_end": 10,
    "ep_count": 10,
    "tactical_doc": "한시윤이 SW인베스트먼트를 설립하고 첫 투자를 시작한다.",
    "state_changes": {
        "npc_deaths": [],
        "relationship_changes": [],
        "npc_personality_changes": [],
    },
    "constraint_summary": "사망 NPC 없음",
    "key_events": ["회사 설립", "첫 투자"],
    "content": {
        "context": "2006년 1월, 한시윤이 회귀한다.",
        "event_villain": "아버지 한정호의 반대",
        "solution": "독립 선언",
        "reward": "SW인베스트먼트 설립"
    },
}
```

#### Stage2Context 조립

기존 E2E conftest의 Stage4Context 조립 패턴을 Stage2Context에 적용:

```python
from modules.core.stage2_context import Stage2Context
from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.core.db_manager import DBManager
from modules.domain.agents.state_tracker import StateTracker

# 1. 실제 DB (tmp_path)
db = DBManager(tmp_path / "l3.db")

# 2. 실물 골든루트 데이터 로드 + plot_roadmap 주입
bible = _load_golden_route_bible()  # 위의 주입 로직
db.save_anchor("bible", bible)

# 3. mock UI
mock_ui = MagicMock()
mock_ui.log = MagicMock()
mock_ui.console = MagicMock()
mock_ui.menu = MagicMock(return_value="2")

# 4. mock project
mock_project = MagicMock()
mock_project.db = db
mock_project.name = "골든루트_L3_테스트"
mock_project.master_bible = bible
mock_project.volumes = []  # Stage 1 스킵

# 5. mock sys
mock_sys = MagicMock()
mock_sys.api_client = MagicMock()
mock_sys.hud = MagicMock()
mock_sys.hud.pro_root = bible["MasterBible"].get("protagonist_config", {})
mock_sys.lore = MagicMock()

# 6. mock agents (핵심!)
mock_analyst = MagicMock()
mock_analyst.enrich_raw_block_async = AsyncMock(side_effect=_enrich_passthrough)
mock_analyst.stitch_joints = MagicMock(return_value={"status": "OK"})
mock_analyst.get_lack_report = MagicMock(return_value={"status": "ok"})

mock_generator = MagicMock()
mock_generator.generate = MagicMock(return_value=_make_mock_arc(1, 1))

mock_director = MagicMock()
mock_director.audit_strategic_plan = MagicMock(
    return_value={"verdict": "PASS", "score": 80, "feedback": {}}
)

agents = {
    "analyst": mock_analyst,
    "four_phase_arc_generator": mock_generator,
    "director": mock_director,
}

# 7. StateTracker (실제 — NPC 추적 검증)
state_tracker = StateTracker()

# 8. Stage2Context 조립
ctx = Stage2Context(
    ui=mock_ui,
    current_project=mock_project,
    agents=agents,
    sys=mock_sys,
    state_tracker=state_tracker,
    selected_genre={"type": "investment", "name": "투자물"},
    stage_rejection_history=[],
    get_int_input=lambda prompt, **kw: kw.get("default", 2),  # 자동 응답: 2블록
    get_max_episode_from_manuscripts=lambda: 0,
    calculate_arc_from_episode=lambda ep: 0,
    audit_event=lambda *a, **kw: None,
    generate_arc_context_v60=lambda arcs, arc_no: "",
    cumulative_state_cache=None,
    cumulative_state_cache_key=0,
    # 나머지 콜백 — None or noop
)

# 9. Orchestrator 생성 + 실행
orch = Stage2Orchestrator(app=MagicMock(), context=ctx)
# app은 레거시 호환용 — self.app 접근 0이므로 MagicMock으로 충분

await orch.stage_2_arcs_async_logic()
```

#### 검증 항목 (assertions)

```python
# 1. 크래시 없이 완료
assert True  # 여기까지 왔으면 성공

# 2. arcs가 DB에 저장됨
saved_arcs = db.load_anchor("arcs")
assert saved_arcs is not None
assert len(saved_arcs) >= 1  # 최소 1개 arc 생성

# 3. arc 구조 유효
arc = saved_arcs[0]
assert "arc_no" in arc
assert "tactical_doc" in arc
assert "ep_start" in arc
assert "ep_end" in arc

# 4. 투자물 장르 데이터 처리 안 크래시
# (FinanceHUD, investment 관련 코드 경로 통과 확인)

# 5. analyst.enrich_raw_block_async 호출됨 (2번 — 2블록)
assert mock_analyst.enrich_raw_block_async.call_count >= 1
```

### 주의사항

1. **Stage 2 파이프라인은 async** — `pytest-asyncio` 사용 필수 (`@pytest.mark.asyncio`)
2. **`asyncio.gather`** — `enrich_raw_block_async`가 `AsyncMock`이어야 함 (`from unittest.mock import AsyncMock`)
3. **sub-module 접근** — `orch.preflight`, `orch.validation_pipeline`, `orch.finalizer`가 내부적으로 에이전트를 호출. 에이전트가 mock이면 sub-module도 자동으로 mock 응답 받음
4. **`self.app` 접근** — L154 `getattr(self.app, "_state_tracker_loaded_arcs", 0)` 있음. `MagicMock()`이면 `0` 반환 안 됨 → `MagicMock(_state_tracker_loaded_arcs=0)` 설정 필요
5. **SpinnerContext** — `rich_console.status()` mock 필요할 수 있음 → `monkeypatch` 또는 `MagicMock`
6. **input() 호출** — L279 `self.ctx.get_int_input()` → 콜백으로 자동 응답
7. **파이프라인이 중간에 실패해도 OK** — 스모크 테스트이므로 "크래시 없이 종료"가 목표. 부분 실행도 성공으로 간주
8. **골든루트 JSON 파일 경로** — 테스트에서 `PROJECT_ROOT / "bible" / "골든루트_bi.json"` 등으로 참조. 파일 없으면 `pytest.skip()`

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/system.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: Part 1 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage_status.py -v

# Gate 4: Part 2 테스트
set PYTHONIOENCODING=utf-8
pytest tests/e2e/test_l3_golden_route.py -v

# Gate 5: 기존 E2E 회귀
set PYTHONIOENCODING=utf-8
pytest tests/e2e/ -v

# Gate 6: 전체 회귀
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 7: pre-commit
pre-commit run --files modules/core/system.py tests/test_stage_status.py tests/e2e/test_l3_golden_route.py
```

---

## 커밋

```
fix(status): check stage readiness with truthiness instead of is-not-None

feat(e2e): add L3 golden route pipeline smoke test with real data + mocked LLM

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

단일 커밋 또는 2커밋 모두 OK. push 포함.

---

## 실패 시

- Part 1 (버그 수정)은 반드시 성공해야 함
- Part 2 (L3 스모크)는 mock 조립이 복잡함. **파이프라인 크래시 지점을 찾아 mock을 추가/수정하는 과정이 핵심**
- 크래시 발생 시: 에러 메시지 + traceback + 어떤 mock이 부족한지 분석 후 보고
- 3회 이상 mock 추가해도 새로운 크래시가 계속 나오면: 중단하고 "크래시 지점 목록"만 보고

---

## 체크리스트

- [ ] `system.py` `is not None` → `bool()` 수정 (3곳)
- [ ] `tests/test_stage_status.py` 4건 통과
- [ ] 골든루트 bible + treatment 로드 성공
- [ ] plot_roadmap 주입 (treatment[0:2].content)
- [ ] Stage2Context 조립 + Stage2Orchestrator 생성
- [ ] `stage_2_arcs_async_logic()` 크래시 없이 실행
- [ ] DB에 arc 1개 이상 저장 확인
- [ ] 기존 테스트 회귀 없음
- [ ] Gate 1-7 통과
- [ ] 커밋 + push
