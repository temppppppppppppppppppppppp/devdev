# Codex Order: 코덱스_테스트 Stage 2 실제 DB 기록 + JSON 내보내기

> **목표**: `projects/코덱스_테스트/` 원본 DB에 Stage 2를 mock LLM으로 3블록 실행, 결과를 DB + JSON 파일로 영구 저장
> **범위**: 실행 스크립트 1개 신규 + 실행
> **위험도**: 낮음 (테스트 프로젝트만, 프로덕션 코드 무변경)
> **API 비용**: $0 (LLM mock)

---

## 배경

이전 테스트(`cf96ae4`)는 DB 복사본에서 실행 → 원본 프로젝트에 결과가 남지 않음.
이번에는 **원본 DB에 직접 기록**하여 사용자가 결과를 확인할 수 있게 한다.

```
현재 상태:
- bible: ✅ (골든루트, 투자물, plot_roadmap 60블록)
- arcs: {} (비어있음)
- volumes: {} (비어있음)
```

---

## 생성 파일

### `scripts/run_stage2_smoke.py` (standalone 스크립트)

pytest가 아닌 **직접 실행 스크립트**. `python scripts/run_stage2_smoke.py`로 실행.

---

## 구현 상세

### 1. 스크립트 골격

```python
"""Stage 2 mock 스모크 실행 — 코덱스_테스트 프로젝트.

실제 프로젝트 DB에 arc 3개를 생성하고 JSON으로 내보낸다.
LLM 호출은 mock. API 비용 $0.

Usage:
    python scripts/run_stage2_smoke.py
"""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager
from modules.core.stage2_context import Stage2Context
from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.domain.agents.state_tracker import StateTracker
```

### 2. 실제 프로젝트 DB 열기 (복사 안 함)

```python
PROJECT_DIR = PROJECT_ROOT / "projects" / "코덱스_테스트"
DB_PATH = PROJECT_DIR / "project_data.db"
ARCS_OUTPUT_DIR = PROJECT_DIR / "plans" / "arcs"

assert DB_PATH.exists(), f"DB 없음: {DB_PATH}"
ARCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

db = DBManager(DB_PATH)
```

### 3. Bible 로드 + 검증

```python
bible = db.load_anchor("bible")
assert bible, "Bible이 비어있음"
mb = bible.get("MasterBible", bible)
roadmap = mb.get("plot_roadmap", [])
assert len(roadmap) >= 3, f"plot_roadmap {len(roadmap)}블록 (최소 3 필요)"
print(f"✅ Bible 로드 완료: plot_roadmap {len(roadmap)}블록")
```

### 4. Mock 에이전트 — 기존 test_l3_golden_route.py 패턴 참조

**반드시 `tests/e2e/test_l3_golden_route.py`를 읽고** 동일한 mock 패턴을 사용할 것.

핵심: mock arc를 **투자물 장르에 맞는 내용**으로 생성.

```python
_arc_counter = 0

def make_mock_arc(enriched_block=None):
    global _arc_counter
    _arc_counter += 1

    # enriched_block에서 실제 treatment 내용 가져오기
    content = {}
    if enriched_block and isinstance(enriched_block, dict):
        content = enriched_block.get("content", {})

    return {
        "arc_no": _arc_counter,
        "ep_start": (_arc_counter - 1) * 10 + 1,
        "ep_end": _arc_counter * 10,
        "ep_count": 10,
        "tactical_doc": json.dumps({
            "arc_title": f"골든루트 Arc {_arc_counter}",
            "context": content.get("context", f"Arc {_arc_counter} 투자 전략"),
            "event_villain": content.get("event_villain", "시장 위기"),
            "solution": content.get("solution", "전략적 투자"),
            "reward": content.get("reward", "수익 실현"),
            "episodes": [
                {"ep_no": (_arc_counter - 1) * 10 + i + 1,
                 "title": f"에피소드 {(_arc_counter - 1) * 10 + i + 1}",
                 "summary": f"Arc {_arc_counter}의 {i+1}번째 전개"}
                for i in range(10)
            ]
        }, ensure_ascii=False, indent=2),
        "state_changes": {
            "npc_deaths": [],
            "relationship_changes": [],
            "npc_personality_changes": [],
        },
        "constraint_summary": "사망 NPC 없음",
        "content": content,
        "key_events": [f"Arc {_arc_counter} 핵심 이벤트"],
    }
```

**중요**: `tactical_doc`에 treatment의 **실제 context/event_villain/solution/reward**를 넣어라.
`roadmap[arc_no - 1]`에서 가져올 수 있다. mock이지만 실제 treatment 내용이 반영되어야 사용자가 읽을 수 있다.

### 5. Stage2Context 조립 + 실행

`test_l3_golden_route.py`의 mock context 조립 패턴을 그대로 사용.

핵심 변경:
- `get_int_input` → `3` 반환 (3블록)
- DB는 실제 프로젝트 DB (복사 아님)
- `current_project.master_bible = bible`

```python
async def run():
    # ... mock 조립 (test_l3_golden_route.py 참조) ...

    orch = Stage2Orchestrator(
        app=MagicMock(_state_tracker_loaded_arcs=0),
        context=ctx
    )

    print("🚀 Stage 2 시작 (3블록, mock LLM)...")
    await orch.stage_2_arcs_async_logic()
    print("✅ Stage 2 완료")

asyncio.run(run())
```

### 6. 결과 내보내기

Stage 2 실행 후 DB에서 arcs를 읽어 JSON 파일로 내보내기:

```python
# Stage 2 실행 후
saved_arcs = db.load_anchor("arcs")
if not saved_arcs:
    print("⚠️ arcs가 비어있음 — Stage 2 파이프라인에서 저장되지 않았을 수 있음")
    # 수동으로 mock arc를 DB에 저장하고 내보내기
    print("📝 mock arc 수동 저장 모드...")
    _arc_counter = 0
    manual_arcs = []
    for i in range(3):
        arc = make_mock_arc(enriched_block={"content": roadmap[i]})
        manual_arcs.append(arc)
    db.save_anchor("arcs", manual_arcs)
    saved_arcs = manual_arcs
    print(f"✅ mock arc {len(manual_arcs)}개 DB 저장 완료")

# JSON 내보내기
for arc in saved_arcs:
    arc_no = arc.get("arc_no", 0)
    out_path = ARCS_OUTPUT_DIR / f"arc_{arc_no}.json"
    out_path.write_text(
        json.dumps(arc, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"📄 {out_path.name} 저장 ({len(json.dumps(arc, ensure_ascii=False))}자)")

print(f"\n🎉 완료: {len(saved_arcs)}개 arc → DB + {ARCS_OUTPUT_DIR}")
db.close()
```

### 7. tactical_doc에 실제 treatment 내용 반영

**가장 중요한 부분**: mock이지만 사용자가 읽을 수 있는 내용이어야 한다.

`roadmap[0]`, `roadmap[1]`, `roadmap[2]`의 실제 한글 내용(context, event_villain, solution, reward)을 `tactical_doc`에 포함시켜라.

```python
# roadmap[i]는 이런 구조:
# {
#   "context": "2006년 겨울, 한시윤은...",
#   "event_villain": "아버지 한정호 회장의...",
#   "solution": "이번엔 다르다...",
#   "reward": "한시윤은 작은 자산을..."
# }
```

이 내용을 `tactical_doc` JSON 문자열에 그대로 넣으면 사용자가 `plans/arcs/arc_1.json`을 열어서 실제 스토리를 확인할 수 있다.

---

## 실행 방법

```bash
cd "C:\Users\User\Desktop\글도비"
python scripts/run_stage2_smoke.py
```

실행 후 확인:
```bash
# DB 확인
python -c "from modules.core.db_manager import DBManager; db=DBManager('projects/코덱스_테스트/project_data.db'); arcs=db.load_anchor('arcs'); print(f'arcs: {len(arcs)}개'); db.close()"

# JSON 파일 확인
ls projects/코덱스_테스트/plans/arcs/
```

---

## 검증 게이트

```bash
# Gate 1: 스크립트 실행
python scripts/run_stage2_smoke.py

# Gate 2: DB에 arcs 3개 저장 확인
python -c "from modules.core.db_manager import DBManager; db=DBManager('projects/코덱스_테스트/project_data.db'); arcs=db.load_anchor('arcs'); assert isinstance(arcs, list) and len(arcs) >= 3, f'arcs: {arcs}'; print(f'✅ arcs {len(arcs)}개 확인'); db.close()"

# Gate 3: JSON 파일 3개 존재
python -c "from pathlib import Path; arcs=list(Path('projects/코덱스_테스트/plans/arcs').glob('arc_*.json')); assert len(arcs) >= 3, f'{len(arcs)}개'; print(f'✅ JSON {len(arcs)}개 확인')"

# Gate 4: JSON 내용에 한글 treatment 포함 확인
python -c "import json; d=json.load(open('projects/코덱스_테스트/plans/arcs/arc_1.json','r',encoding='utf-8')); td=d.get('tactical_doc',''); print(td[:200]); assert '한시윤' in td or 'context' in td, 'treatment 내용 미반영'"

# Gate 5: 기존 테스트 회귀
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 6: pre-commit
pre-commit run --files scripts/run_stage2_smoke.py
```

---

## 커밋

```
feat(scripts): add stage2 smoke runner that persists arcs to real project DB + JSON export
```

push 포함.

---

## 실패 시

- Stage 2 파이프라인에서 arc가 DB에 저장 안 되는 경우: **수동 저장 모드**로 fallback (섹션 6 참고)
- 이 경우에도 JSON 내보내기는 수행
- 스크립트 크래시: traceback + 원인 보고 후 중단

---

## 체크리스트

- [ ] `tests/e2e/test_l3_golden_route.py` 읽고 mock 패턴 파악
- [ ] `scripts/run_stage2_smoke.py` 생성
- [ ] 스크립트 실행: 크래시 없이 완료
- [ ] DB에 arcs 3개 저장 확인
- [ ] `plans/arcs/arc_1.json` ~ `arc_3.json` 생성 확인
- [ ] JSON에 실제 treatment 한글 내용 포함 확인
- [ ] 기존 테스트 회귀 없음
- [ ] 커밋 + push
