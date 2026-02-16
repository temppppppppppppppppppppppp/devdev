# Codex Order: 코덱스_테스트 프로젝트 Stage 2 — 3블록 스모크 실행

> **목표**: `projects/코덱스_테스트/` 실제 프로젝트 DB에서 Stage 2를 mock LLM으로 3블록 실행
> **범위**: 테스트 스크립트 1개 신규 + 실행
> **위험도**: 낮음 (테스트 프로젝트에만 영향, 프로덕션 코드 변경 없음)
> **API 비용**: $0 (LLM 전부 mock)

---

## 현재 상태

```
프로젝트 경로: projects/코덱스_테스트/
DB: projects/코덱스_테스트/project_data.db

bible: ✅ 존재 (골든루트, 투자물 장르)
plot_roadmap: 60블록 (treatment에서 주입됨)
arcs: {} (비어있음 — Stage 2 미실행)
volumes: {} (비어있음 — Stage 1 스킵)
```

**Stage 2에 필요한 데이터가 전부 DB에 있음. 추가 세팅 불필요.**

---

## 생성 파일

### `tests/e2e/test_l3_stage2_realproject.py`

이 테스트는 `tests/e2e/test_l3_golden_route.py`와 비슷하지만:
- `tmp_path` 대신 **실제 프로젝트 DB** 사용
- plot_roadmap 주입 불필요 (이미 60블록 있음)
- **3블록** 실행
- 실행 후 DB에 arc 3개 저장 검증

---

## 핵심 구현 지침

### 1. DB 접근

```python
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / "코덱스_테스트" / "project_data.db"

# 원본 보호: 복사본에서 테스트
@pytest.fixture
def test_db(tmp_path):
    """실제 프로젝트 DB를 복사해서 사용 (원본 보호)."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip("코덱스_테스트 프로젝트가 없습니다")
    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)
    db = DBManager(copied_db)
    yield db
    db.close()
```

**중요: 원본 DB를 직접 수정하지 않는다. 항상 복사본 사용.**

### 2. 데이터 검증 (TestSetup 클래스)

실행 전 DB 상태 확인:

```python
class TestSetup:
    def test_bible_exists(self, test_db):
        bible = test_db.load_anchor("bible")
        assert bible, "Bible이 비어있음"
        mb = bible.get("MasterBible", bible)
        assert "plot_roadmap" in mb
        assert len(mb["plot_roadmap"]) >= 3, f"plot_roadmap {len(mb['plot_roadmap'])}블록 (최소 3 필요)"

    def test_genre_is_investment(self, test_db):
        bible = test_db.load_anchor("bible")
        # 장르 확인 — bible 최상위 또는 MasterBible 내부
        genre = bible.get("_genre", "")
        assert genre == "investment" or "FinanceHUD" in bible.get("MasterBible", {})

    def test_arcs_initially_empty(self, test_db):
        arcs = test_db.load_anchor("arcs")
        assert not arcs, f"arcs가 이미 존재: {len(arcs) if isinstance(arcs, list) else arcs}"
```

### 3. Stage 2 파이프라인 실행 (TestPipelineSmoke 클래스)

기존 `test_l3_golden_route.py`의 mock 패턴을 그대로 사용하되:

```python
@pytest.mark.asyncio
class TestPipelineSmoke:
    async def test_stage2_runs_3_blocks(self, test_db):
        """Stage 2가 3블록을 mock LLM으로 크래시 없이 처리."""
        bible = test_db.load_anchor("bible")

        # ... (mock 조립 — test_l3_golden_route.py 참고) ...

        # 핵심 차이: get_int_input이 3을 반환 (3블록)
        ctx = Stage2Context(
            # ... 기존 패턴과 동일 ...
            get_int_input=lambda prompt, **kw: 3,  # ← 3블록
            # ...
        )

        orch = Stage2Orchestrator(app=MagicMock(_state_tracker_loaded_arcs=0), context=ctx)
        await orch.stage_2_arcs_async_logic()

        # 검증
        saved_arcs = test_db.load_anchor("arcs")
        assert saved_arcs is not None
        assert isinstance(saved_arcs, list)
        assert len(saved_arcs) >= 1  # 최소 1개 (mock 환경에서 3개 보장 안 될 수 있음)

    async def test_arc_structure_valid(self, test_db):
        """저장된 arc의 구조가 유효."""
        # test_stage2_runs_3_blocks 이후 실행되어야 하므로,
        # 이 테스트에서도 Stage 2를 실행하거나,
        # 별도 fixture로 arc가 이미 저장된 DB를 받음
        #
        # 간단한 접근: 이 테스트 내에서도 Stage 2 실행
        # (DB 복사본이므로 격리됨)
        pass  # test_stage2_runs_3_blocks에서 검증 통합 가능
```

### 4. Mock 전략 — test_l3_golden_route.py 참조

**이미 작동하는 L3 mock 패턴을 그대로 복사**하되, 아래만 변경:

| 항목 | L3 (기존) | 이번 테스트 |
|------|-----------|------------|
| DB 소스 | `tmp_path` + bible 주입 | 실제 프로젝트 DB 복사본 |
| plot_roadmap | 2블록 수동 주입 | 60블록 (이미 DB에 있음) |
| `get_int_input` 반환값 | 2 | **3** |
| mock arc의 `arc_no` | 1~2 | 1~3 (side_effect로 동적) |

**mock arc를 동적으로 생성하는 패턴**:
```python
_arc_counter = 0

def _make_mock_arc(**kwargs):
    nonlocal _arc_counter
    _arc_counter += 1
    return {
        "arc_no": _arc_counter,
        "ep_start": (_arc_counter - 1) * 10 + 1,
        "ep_end": _arc_counter * 10,
        "ep_count": 10,
        "tactical_doc": f"골든루트 Arc {_arc_counter} 투자 전략 전개",
        "state_changes": {
            "npc_deaths": [],
            "relationship_changes": [],
            "npc_personality_changes": [],
        },
        "constraint_summary": "사망 NPC 없음",
        "content": kwargs.get("content", {}),
    }
```

### 5. 참고: test_l3_golden_route.py 구조

이미 커밋 `1818357`에 존재하는 `tests/e2e/test_l3_golden_route.py`를 반드시 읽고 mock 패턴을 파악한 뒤 작성할 것.
해당 파일의 fixture, mock agent 조립, Stage2Context 조립, async 실행 패턴을 그대로 재사용.

---

## 검증 게이트

```bash
# Gate 1: 신규 테스트 실행
set PYTHONIOENCODING=utf-8
pytest tests/e2e/test_l3_stage2_realproject.py -v --tb=short

# Gate 2: 기존 E2E 회귀
set PYTHONIOENCODING=utf-8
pytest tests/e2e/ -v --tb=short

# Gate 3: 전체 회귀
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 4: pre-commit
pre-commit run --files tests/e2e/test_l3_stage2_realproject.py
```

---

## 커밋

```
test(l3): add 3-block stage2 smoke test using real project DB copy
```

push 포함.

---

## 실패 시

- DB 복사/로딩 실패: `pytest.skip()`으로 처리
- Stage 2 파이프라인 크래시: `test_l3_golden_route.py`의 mock과 비교하여 누락 mock 추가
- 3회 이상 크래시 반복: 크래시 지점 목록만 보고하고 중단
- **원본 DB 절대 수정 금지** — 반드시 `shutil.copy2` 복사본 사용

---

## 체크리스트

- [ ] `test_l3_golden_route.py` 읽고 mock 패턴 파악
- [ ] `tests/e2e/test_l3_stage2_realproject.py` 신규 생성
- [ ] 실제 프로젝트 DB 복사본에서 bible/plot_roadmap 60블록 확인
- [ ] Stage 2 mock LLM으로 3블록 실행 — 크래시 없음
- [ ] DB에 arc 저장 확인
- [ ] 기존 E2E 24 tests 회귀 없음
- [ ] Gate 1-4 통과
- [ ] 커밋 + push
