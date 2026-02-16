# Codex Order: Stage 2→3 파이프라인 스모크 테스트

> **목표**: Stage 2에서 생성된 arc 데이터로 Stage 3 (Blueprint) 파이프라인을 mock LLM으로 실행
> **범위**: 테스트 1개 신규 + 실행 스크립트 1개 신규
> **위험도**: 낮음 (테스트 프로젝트만, 프로덕션 코드 무변경)
> **API 비용**: $0 (LLM 전부 mock)

---

## 배경

Stage 2 스모크 테스트(`af2eed2`)에서 `코덱스_테스트` 프로젝트 DB에 arc 3개가 저장됨.
이번에는 그 arc를 입력으로 **Stage 3 (Blueprint) 파이프라인**을 mock LLM으로 실행.

```
현재 상태:
- bible: ✅ (골든루트, 투자물, plot_roadmap 60블록)
- arcs: ✅ 3개 (arc_1~3, ep 1-30)
- blueprints: {} (비어있음 — Stage 3 미실행)
```

---

## Part 1: pytest 테스트 (`tests/e2e/test_l3_stage3_smoke.py`)

### 1. 핵심 원리

Stage 3 오케스트레이터는 `self.app`을 25개소 이상 직접 참조한다 (Stage 2와 달리 DI 미완).
따라서 **MagicMock으로 app 전체를 생성**하되, 아래 핵심 속성만 실제/커스텀으로 설정:

```python
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / "코덱스_테스트" / "project_data.db"
```

### 2. Fixture: DB 복사 + 데이터 로드

```python
@pytest.fixture
def stage3_env(tmp_path):
    """Stage 3 테스트 환경: DB 복사 + arcs/bible 로드."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip("코덱스_테스트 프로젝트가 없습니다")

    from modules.core.db_manager import DBManager

    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)
    db = DBManager(copied_db)

    bible = db.load_anchor("bible")
    arcs = db.load_anchor("arcs")
    assert bible, "Bible이 비어있음"
    assert arcs and len(arcs) >= 3, f"arcs {len(arcs) if arcs else 0}개 (최소 3 필요)"

    yield {"db": db, "bible": bible, "arcs": arcs, "tmp_path": tmp_path}
    db.close()
```

### 3. Mock Blueprint 생성 — Pydantic 활용

**가장 중요**: Pydantic `Blueprint` 모델을 사용하면 스키마가 자동으로 맞는다.
`_validate_blueprint_integrity`는 `integrated_scenario`(str) + `scene_breakdown`(dict)만 체크.

```python
from modules.models.blueprint import Blueprint

def make_mock_blueprint(ep_num: int) -> dict:
    """Pydantic Blueprint 모델로 유효한 mock 생성."""
    return Blueprint(
        episode_number=ep_num,
        integrated_scenario=f"제{ep_num}화: 한시우의 투자 전략이 전개된다.",
        scene_breakdown={
            "scene_1": {"summary": "도입 — 상황 파악", "location": "서울"},
            "scene_2": {"summary": "갈등 — 투자 결정", "location": "증권사"},
            "scene_3": {"summary": "해결 — 실행", "location": "시장"},
        },
        pacing_notes="빠른 전개",
        target_beat="투자 결정",
        core_tension="자본 리스크",
        expected_ending="수익 확보",
        start_location="서울",
        location="서울",
    ).model_dump()
```

### 4. Mock App 조립

```python
def build_mock_app(db, bible, arcs):
    """Stage 3에 필요한 mock SovereignApp 조립."""
    app = MagicMock()

    # ── 실제 데이터 연결 ──
    app.current_project.db = db
    app.current_project.arcs = arcs
    app.current_project.master_bible = bible
    app.current_project.name = "코덱스_테스트"

    # ── get_blueprint: DB에서 조회 ──
    app.current_project.get_blueprint = MagicMock(
        side_effect=lambda ep: db.get_blueprint(ep)  # 없으면 None
    )

    # ── save_episode_blueprint: DB에 저장 ──
    def _save_bp(ep, bp_data):
        db.save_blueprint(ep, bp_data)
    app.current_project.save_episode_blueprint = MagicMock(side_effect=_save_bp)

    # ── DB 조회 메서드 ──
    app.current_project.db.get_latest_blueprint_number = MagicMock(return_value=0)

    # ── 사용자 입력: 3화까지 생성 ──
    app._get_int_input = MagicMock(return_value=3)

    # ── 원고 없음 ──
    app._get_max_episode_from_manuscripts = MagicMock(return_value=0)

    # ── Arc 컨텍스트 매핑 (실제 로직 재현) ──
    def _get_arc_context(ep_num):
        for i, a in enumerate(arcs):
            if (isinstance(a.get("ep_start"), int)
                and isinstance(a.get("ep_end"), int)
                and a["ep_start"] <= ep_num <= a["ep_end"]):
                return (i, a)
        return (None, None)
    app._get_arc_context_for_episode = MagicMock(side_effect=_get_arc_context)

    # ── Arc 데이터 검증 (통과) ──
    app._validate_arc_data_fields = MagicMock(side_effect=lambda arc, idx: arc)

    # ── Blueprint 무결성 검증 (실제 로직) ──
    def _validate_integrity(bp):
        if not isinstance(bp, dict):
            return False
        if not isinstance(bp.get("integrated_scenario"), str):
            return False
        if not isinstance(bp.get("scene_breakdown"), dict):
            return False
        return True
    app._validate_blueprint_integrity = MagicMock(side_effect=_validate_integrity)

    # ── 주인공 이름 ──
    app._get_protagonist_name = MagicMock(return_value="한시우")

    # ── Entity Registry 수정 (통과) ──
    app._fix_entity_registry_protagonist = MagicMock(side_effect=lambda reg, name: reg)

    # ── 감사/커밋 (noop) ──
    app._audit_event = MagicMock()
    app._safe_commit = MagicMock()
    app._write_audit_summary = MagicMock()

    # ── 장르 ──
    app.selected_genre = {"type": "investment", "name": "투자물"}

    # ── UI (print로 출력) ──
    app.ui.log = MagicMock(side_effect=lambda msg: print(msg))

    # ── 에이전트: three_phase_bp (핵심 LLM mock) ──
    _bp_counter = {"n": 0}
    def _mock_generate(**kwargs):
        ep = kwargs.get("ep_num", _bp_counter["n"] + 1)
        _bp_counter["n"] = ep
        bp = make_mock_blueprint(ep)
        result = {
            "final_verdict": "PASS",
            "phases": {
                "generate": {
                    "selected_strategy": "momentum",
                    "selected_score": 85,
                }
            },
        }
        return (bp, result)
    app.agents = {
        "three_phase_bp": MagicMock(generate=MagicMock(side_effect=_mock_generate)),
        "director": MagicMock(),
        "state_extractor": MagicMock(
            extract_cumulative_state=MagicMock(return_value={"entity_registry": {}})
        ),
    }

    return app
```

### 5. StageSpinner 패치

Stage 3은 `StageSpinner` 컨텍스트 매니저를 사용. rich console 의존이라 mock 필요:

```python
@contextmanager
def _noop_spinner(*args, **kwargs):
    yield

# 테스트에서:
@patch("modules.core.stage3_orchestrator.StageSpinner", _noop_spinner)
```

**주의**: `StageSpinner`는 `_generate_blueprint` 내부에서 import됨:
```python
from modules.core.spinners import StageSpinner
```
따라서 패치 경로는 **`modules.core.spinners.StageSpinner`** 또는 오케스트레이터 내부 import 후 참조되는 경로.
실제 import가 `_generate_blueprint` 함수 안에서 일어나므로 `modules.core.spinners.StageSpinner`을 패치.

### 6. 테스트 클래스

```python
class TestL3Stage3Setup:
    """Stage 3 전제조건 검증."""

    def test_arcs_loaded(self, stage3_env):
        assert len(stage3_env["arcs"]) >= 3

    def test_arc_structure(self, stage3_env):
        arc = stage3_env["arcs"][0]
        assert arc["ep_start"] == 1
        assert arc["ep_end"] == 10

    def test_bible_has_data(self, stage3_env):
        bible = stage3_env["bible"]
        mb = bible.get("MasterBible", bible)
        assert "plot_roadmap" in mb


class TestL3Stage3Pipeline:
    """Stage 3 파이프라인 스모크 테스트."""

    @patch("modules.core.spinners.StageSpinner", _noop_spinner)
    def test_stage3_runs_3_episodes(self, stage3_env):
        """Stage 3이 3 에피소드를 mock LLM으로 크래시 없이 처리."""
        from modules.core.stage3_orchestrator import Stage3Orchestrator
        from modules.core.stage3_context import Stage3Context

        db = stage3_env["db"]
        bible = stage3_env["bible"]
        arcs = stage3_env["arcs"]

        app = build_mock_app(db, bible, arcs)

        ctx = Stage3Context(
            ui=app.ui,
            current_project=app.current_project,
            get_protagonist_name=lambda: "한시우",
        )

        orch = Stage3Orchestrator(app=app, context=ctx)
        orch.stage_3_batch_blueprinting()

        # 검증 1: 크래시 없이 완료
        # (여기까지 왔으면 성공)

        # 검증 2: Blueprint가 DB에 저장됨
        # save_episode_blueprint이 호출되었는지 확인
        assert app.current_project.save_episode_blueprint.call_count >= 1, \
            "save_episode_blueprint이 한 번도 호출되지 않음"

        # 검증 3: three_phase_bp.generate가 호출됨
        assert app.agents["three_phase_bp"].generate.call_count >= 1, \
            "three_phase_bp.generate가 호출되지 않음"

    @patch("modules.core.spinners.StageSpinner", _noop_spinner)
    def test_blueprint_content_valid(self, stage3_env):
        """저장된 Blueprint의 구조가 유효."""
        from modules.core.stage3_orchestrator import Stage3Orchestrator
        from modules.core.stage3_context import Stage3Context

        db = stage3_env["db"]
        bible = stage3_env["bible"]
        arcs = stage3_env["arcs"]

        app = build_mock_app(db, bible, arcs)

        ctx = Stage3Context(
            ui=app.ui,
            current_project=app.current_project,
            get_protagonist_name=lambda: "한시우",
        )

        orch = Stage3Orchestrator(app=app, context=ctx)
        orch.stage_3_batch_blueprinting()

        # save_episode_blueprint 호출 인자 검증
        for call in app.current_project.save_episode_blueprint.call_args_list:
            ep_num, bp_data = call[0]
            assert isinstance(bp_data, dict), f"ep {ep_num}: blueprint이 dict가 아님"
            assert "integrated_scenario" in bp_data, f"ep {ep_num}: integrated_scenario 누락"
            assert "scene_breakdown" in bp_data, f"ep {ep_num}: scene_breakdown 누락"
            assert isinstance(bp_data["scene_breakdown"], dict)
```

### 7. 주의: `save_blueprint` vs `save_episode_blueprint`

DB에 실제로 저장하려면 `db.save_blueprint(ep, data)` 메서드가 있는지 확인 필요.
`test_l3_golden_route.py`의 패턴을 참고하되, 없으면 `db.save_anchor(f"blueprint_{ep}", data)` 또는 mock의 side_effect에서 실제 저장 생략 가능.

**반드시 `tests/e2e/test_l3_golden_route.py`와 `tests/e2e/conftest.py`를 읽고** DB 저장 패턴을 확인할 것.

---

## Part 2: 실행 스크립트 (`scripts/run_stage3_smoke.py`)

### 목적

실제 `코덱스_테스트` DB에 Blueprint를 기록하고 JSON으로 내보내기.
(`scripts/run_stage2_smoke.py` 패턴 동일)

### 구현

```python
"""Stage 3 mock 스모크 실행 — 코덱스_테스트 프로젝트.

Stage 2에서 생성된 arc 3개로 Blueprint 3화를 생성하고 DB + JSON으로 저장.
LLM 호출은 mock. API 비용 $0.

Usage:
    python scripts/run_stage3_smoke.py
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.core.stage3_orchestrator import Stage3Orchestrator
from modules.core.stage3_context import Stage3Context
from modules.models.blueprint import Blueprint

# ── 설정 ──
PROJECT_DIR = PROJECT_ROOT / "projects" / "코덱스_테스트"
DB_PATH = PROJECT_DIR / "project_data.db"
BP_OUTPUT_DIR = PROJECT_DIR / "plans" / "blueprints"

assert DB_PATH.exists(), f"DB 없음: {DB_PATH}"
BP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

db = DBManager(DB_PATH)
bible = db.load_anchor("bible")
arcs = db.load_anchor("arcs")
assert bible, "Bible이 비어있음"
assert arcs and len(arcs) >= 3, f"arcs {len(arcs) if arcs else 0}개"
print(f"✅ 데이터 로드: bible ✓, arcs {len(arcs)}개")

# ── mock blueprint 생성 (Pydantic) ──
def make_mock_blueprint(ep_num, arc_data=None):
    content = arc_data.get("content", {}) if arc_data else {}
    return Blueprint(
        episode_number=ep_num,
        integrated_scenario=f"제{ep_num}화: {content.get('context', '투자 전개')[:100]}",
        scene_breakdown={
            "scene_1": {"summary": content.get("context", "도입")[:80], "location": "서울"},
            "scene_2": {"summary": content.get("event_villain", "갈등")[:80], "location": "증권사"},
            "scene_3": {"summary": content.get("solution", "해결")[:80], "location": "시장"},
            "scene_4": {"summary": content.get("reward", "보상")[:80], "location": "서울"},
        },
        pacing_notes="투자물 긴장감 유지",
        target_beat=f"Arc {arc_data.get('arc_no', '?')} 전개" if arc_data else "전개",
        core_tension=content.get("event_villain", "시장 리스크")[:50],
        expected_ending=content.get("reward", "수익 확보")[:50],
        start_location="서울",
        location="서울",
    ).model_dump()

# ── mock app 조립 (Part 1과 동일 패턴) ──
# ... build_mock_app 함수 (위 Part 1 섹션 4 참조, DB만 실제 프로젝트 DB 사용)

# ── 실행 ──
# Stage 3 오케스트레이터 실행 후 DB에서 결과 확인

# ── JSON 내보내기 ──
# 에피소드 1~3 Blueprint를 plans/blueprints/bp_ep_1.json ~ bp_ep_3.json으로 내보내기

# ── 결과 출력 ──
# print(f"🎉 완료: {count}개 Blueprint → DB + {BP_OUTPUT_DIR}")
# db.close()
```

**중요**: `make_mock_blueprint`에서 **arc의 실제 content (한글 treatment 내용)**을 scene_breakdown에 반영하라.
사용자가 `plans/blueprints/bp_ep_1.json`을 열어서 실제 스토리 맥락을 확인할 수 있어야 한다.

### JSON 내보내기 형식

```python
for ep in range(1, 4):  # 에피소드 1~3
    bp_data = db.get_blueprint(ep)  # 또는 저장된 데이터 직접 사용
    if bp_data:
        out_path = BP_OUTPUT_DIR / f"bp_ep_{ep}.json"
        out_path.write_text(
            json.dumps(bp_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"📄 {out_path.name} 저장")
```

---

## DB 메서드 확인 필수

Stage 3에서 사용하는 DB 메서드를 반드시 확인:

```python
# 이 메서드들이 DBManager에 실제로 존재하는지 확인할 것:
db.get_latest_blueprint_number()   # → int (없으면 0)
db.get_blueprint(ep)               # → dict or None  (= get_manuscript와 유사)
db.save_blueprint(ep, data)        # → None

# ProjectManager에서:
current_project.get_blueprint(ep)          # → dict or None
current_project.save_episode_blueprint(ep, data)  # → None
```

**없으면 대체 경로 사용** (예: `db.load_anchor(f"blueprint_{ep}")` 등).
반드시 `modules/core/db_manager.py`와 `modules/core/project_manager.py`를 읽고 실제 메서드명 확인.

---

## 검증 게이트

```bash
# Gate 1: 신규 테스트 실행
set PYTHONIOENCODING=utf-8
pytest tests/e2e/test_l3_stage3_smoke.py -v --tb=short

# Gate 2: 기존 E2E 회귀
set PYTHONIOENCODING=utf-8
pytest tests/e2e/ -v --tb=short

# Gate 3: 전체 회귀
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 4: 스크립트 실행
python scripts/run_stage3_smoke.py

# Gate 5: JSON 파일 확인
python -c "from pathlib import Path; bps=list(Path('projects/코덱스_테스트/plans/blueprints').glob('bp_ep_*.json')); assert len(bps) >= 1, f'{len(bps)}개'; print(f'✅ Blueprint JSON {len(bps)}개 확인')"

# Gate 6: pre-commit
pre-commit run --files tests/e2e/test_l3_stage3_smoke.py scripts/run_stage3_smoke.py
```

---

## 커밋

```
feat(e2e): add Stage 3 blueprint smoke test with mock LLM + real arc data

feat(scripts): add stage3 smoke runner that persists blueprints to real project DB + JSON export
```

단일 커밋 OK. push 포함.

---

## 실패 시

- **StageSpinner import 실패**: `modules.core.spinners` 경로 확인 후 패치 경로 수정
- **DB 메서드 미존재** (`get_blueprint`, `save_blueprint` 등): `db_manager.py` 읽고 실제 메서드명으로 교체
- **`_get_arc_context_for_episode` mock 불일치**: arcs 데이터의 `ep_start`/`ep_end` 타입 확인 (int여야 함)
- **MagicMock 자동 속성 문제**: `hasattr(app, "state_tracker")` 등이 MagicMock에서 항상 True → 의도대로 V68 lazy init 스킵됨 (정상)
- **3회 이상 새로운 크래시**: 크래시 지점 목록만 보고하고 중단

---

## 핵심 포인트 (코덱스 필독)

1. **Pydantic `Blueprint` 모델 사용** — `modules/models/blueprint.py`. 스키마 자동 충족.
2. **`test_l3_golden_route.py` 참조** — Stage 2 mock 패턴 참고하되, Stage 3은 `self.app` 직접 참조가 많으므로 app mock이 핵심.
3. **Stage 3은 동기 함수** — `stage_3_batch_blueprinting()`은 async가 아님. `@pytest.mark.asyncio` 불필요.
4. **`_get_int_input` 반환값 = 3** — 에피소드 1~3까지만 생성.
5. **StageSpinner 패치 필수** — rich console 의존. `@patch("modules.core.spinners.StageSpinner", _noop_spinner)` 또는 해당 import 경로.

---

## 체크리스트

- [ ] `tests/e2e/test_l3_golden_route.py` + `conftest.py` 읽고 mock 패턴 파악
- [ ] `modules/core/db_manager.py` 읽고 blueprint 관련 메서드 확인
- [ ] `modules/core/project_manager.py` 읽고 `get_blueprint`/`save_episode_blueprint` 확인
- [ ] `tests/e2e/test_l3_stage3_smoke.py` 생성
- [ ] Stage 3 mock LLM으로 3 에피소드 실행 — 크래시 없음
- [ ] Blueprint DB 저장 확인
- [ ] `scripts/run_stage3_smoke.py` 생성
- [ ] 스크립트 실행: 실제 DB 기록 + JSON 내보내기
- [ ] `plans/blueprints/bp_ep_1.json` ~ `bp_ep_3.json` 생성 확인
- [ ] 기존 E2E 회귀 없음
- [ ] Gate 1-6 통과
- [ ] 커밋 + push
