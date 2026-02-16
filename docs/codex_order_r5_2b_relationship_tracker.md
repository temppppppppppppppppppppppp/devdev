# Codex Order: R5-2b — relationship_tracker.py 2-way 분할

> **목표**: `relationship_tracker.py` (1,275줄)에서 NPC/Faction 로직을 2개 서브모듈로 추출
> **범위**: 서브모듈 2개 신규 + 호스트 수정 + 테스트 신규
> **전제**: R5-2a 완료
> **패턴**: R5-1a/2a 동일 — `host` 위임, lazy `@property`

---

## 현재 구조 (1,275줄)

```
# 데이터클래스 (L15-56)
RelationshipEvent          L15  (dataclass)
FactionRelationshipEvent   L29  (dataclass)
FactionInfo                L45  (dataclass)

class RelationshipTracker:
  # NPC 상수 (L62-115)
  STATES                          L62   (dict, 13줄)
  RISKY_TRANSITIONS               L77   (set, 7줄)
  STATE_KEYWORDS                  L86   (dict, 12줄)
  TRANSITION_REQUIREMENTS         L101  (dict, 15줄)

  # Faction 상수 (L122-193)
  FACTION_STATES                  L122  (dict, 16줄)
  FACTION_TRANSITION_REQUIREMENTS L140  (dict, 15줄)
  FACTION_STATE_KEYWORDS          L157  (dict, 15줄)
  GENRE_FACTION_PATTERNS          L174  (dict, 20줄)

  # NPC 메서드 (L195-545)
  __init__()                              L195  (10줄)
  validate_transition()                   L206  (55줄)
  _suggest_transition_path()              L262  (36줄)
  infer_state_from_manuscript()           L300  (41줄)
  get_relationship_history()              L343  (28줄)
  record_transition()                     L377  (57줄)
  validate_transition_with_justification() L436  (54줄)
  get_npc_current_state()                 L492  (3줄)
  get_transition_history()                L496  (25줄)
  generate_transition_prompt()            L523  (22줄)

  # Faction 메서드 (L551-1275)
  register_faction_v59()                  L551  (30줄)
  set_faction_relation_v59()              L582  (48줄)
  validate_faction_transition_v59()       L632  (53줄)
  _suggest_faction_transition_path()      L687  (19줄)
  record_faction_transition_v59()         L708  (76줄)
  get_faction_relation_v59()              L786  (9줄)
  infer_faction_state_from_manuscript_v59() L797 (56줄)
  track_faction_dynamics_v59()            L855  (125줄) ⚠️ 대형
  get_faction_power_balance_v59()         L982  (55줄)
  generate_faction_dynamics_prompt_v59()  L1039 (51줄)
  get_faction_transition_history_v59()    L1092 (27줄)
  analyze_protagonist_faction_position_v59() L1121 (80줄)
  generate_faction_report_v59()           L1203 (72줄)
```

---

## 목표 구조 (2개 서브모듈)

### Module 1: `relationship_tracker_npc.py` (~350줄)

NPC 개인 간 관계 추적.

| 이동 대상 | 줄수 |
|----------|------|
| `STATES`, `RISKY_TRANSITIONS`, `STATE_KEYWORDS`, `TRANSITION_REQUIREMENTS` | 54 |
| `validate_transition()` | 55 |
| `_suggest_transition_path()` | 36 |
| `infer_state_from_manuscript()` | 41 |
| `get_relationship_history()` | 28 |
| `record_transition()` | 57 |
| `validate_transition_with_justification()` | 54 |
| `get_npc_current_state()` | 3 |
| `get_transition_history()` | 25 |
| `generate_transition_prompt()` | 22 |

### Module 2: `relationship_tracker_factions.py` (~770줄)

세력/팩션 간 관계 추적 (V59 전량).

| 이동 대상 | 줄수 |
|----------|------|
| `FACTION_STATES`, `FACTION_TRANSITION_REQUIREMENTS`, `FACTION_STATE_KEYWORDS`, `GENRE_FACTION_PATTERNS` | 72 |
| `FactionRelationshipEvent` dataclass | 14 |
| `FactionInfo` dataclass | 12 |
| `register_faction_v59()` | 30 |
| `set_faction_relation_v59()` | 48 |
| `validate_faction_transition_v59()` | 53 |
| `_suggest_faction_transition_path()` | 19 |
| `record_faction_transition_v59()` | 76 |
| `get_faction_relation_v59()` | 9 |
| `infer_faction_state_from_manuscript_v59()` | 56 |
| `track_faction_dynamics_v59()` | 125 |
| `get_faction_power_balance_v59()` | 55 |
| `generate_faction_dynamics_prompt_v59()` | 51 |
| `get_faction_transition_history_v59()` | 27 |
| `analyze_protagonist_faction_position_v59()` | 80 |
| `generate_faction_report_v59()` | 72 |

### 호스트 잔여 (~155줄)

```python
from dataclasses import dataclass

@dataclass
class RelationshipEvent:  # 그대로 유지 (NPC 서브모듈에서도 import)
    ...

class RelationshipTracker:
    def __init__(self):
        self.npc_states = {}
        self.faction_states = {}
        self.faction_relations = {}
        self.transition_history = []
        self.faction_transition_history = []
        self._npc = None
        self._factions = None

    @property
    def npc(self):
        if self._npc is None:
            from modules.core.relationship_tracker_npc import RelationshipTrackerNPC
            self._npc = RelationshipTrackerNPC(self)
        return self._npc

    @property
    def factions(self):
        if self._factions is None:
            from modules.core.relationship_tracker_factions import RelationshipTrackerFactions
            self._factions = RelationshipTrackerFactions(self)
        return self._factions

    # 위임 메서드 (기존 공개 API 유지)
    def validate_transition(self, *a, **kw):
        return self.npc.validate_transition(*a, **kw)
    def infer_state_from_manuscript(self, *a, **kw):
        return self.npc.infer_state_from_manuscript(*a, **kw)
    def record_transition(self, *a, **kw):
        return self.npc.record_transition(*a, **kw)
    # ... 나머지 공개 메서드도 동일 위임 ...
    def register_faction_v59(self, *a, **kw):
        return self.factions.register_faction_v59(*a, **kw)
    # ... faction 공개 메서드 위임 ...
```

**중요**: 외부 호출자(`blocking_validator_consistency_checks.py` 등)가 `RelationshipTracker().validate_transition()`을 직접 호출하므로, 호스트에 **위임 stub**를 유지해야 한다. 내부 로직만 서브모듈로 이동.

---

## 구현 상세

### 서브모듈 내 `self.host` 참조

NPC 서브모듈에서 호스트 상태에 접근하는 패턴:

```python
class RelationshipTrackerNPC:
    def __init__(self, host: RelationshipTracker):
        self.host = host

    def validate_transition(self, npc_name, from_state, to_state, ...):
        # self.npc_states → self.host.npc_states
        current = self.host.npc_states.get(npc_name, "neutral")
        ...

    def record_transition(self, ...):
        # self.transition_history → self.host.transition_history
        self.host.transition_history.append(event)
        # self.npc_states → self.host.npc_states
        self.host.npc_states[npc_name] = to_state
```

**치환 규칙**:
- `self.npc_states` → `self.host.npc_states`
- `self.transition_history` → `self.host.transition_history`
- `self.faction_states` → `self.host.faction_states`
- `self.faction_relations` → `self.host.faction_relations`
- `self.faction_transition_history` → `self.host.faction_transition_history`

상수(`STATES`, `FACTION_STATES` 등)는 서브모듈 클래스 상수로 이동하므로 `self.` 그대로 유지.

### dataclass 위치

- `RelationshipEvent` → **호스트에 유지** (NPC 서브모듈에서 `from modules.core.relationship_tracker import RelationshipEvent`로 import)
- `FactionRelationshipEvent`, `FactionInfo` → **faction 서브모듈로 이동** (호스트에서 필요 시 re-import)

---

## 테스트

### 파일: `tests/test_relationship_tracker_submodules.py`

```python
"""[R5-2b] RelationshipTracker 서브모듈 단위 테스트."""
import pytest
from modules.core.relationship_tracker import RelationshipTracker

@pytest.fixture
def rt():
    return RelationshipTracker()

# ── NPC ──
class TestNPCSubmodule:
    def test_validate_transition_normal(self, rt):
        result = rt.npc.validate_transition("장무기", "neutral", "friendly", arc=1, episode=1)
        assert result["allowed"]

    def test_validate_risky_transition(self, rt):
        result = rt.npc.validate_transition("장무기", "friendly", "hostile", arc=1, episode=1)
        assert result.get("warning") or result.get("risky")

    def test_record_and_retrieve(self, rt):
        rt.npc.record_transition(
            npc_name="장무기", from_state="neutral", to_state="friendly",
            arc=1, episode=1, trigger="도움", justification="생명 구조"
        )
        assert rt.npc_states["장무기"] == "friendly"
        assert len(rt.transition_history) == 1

    def test_infer_state(self, rt):
        state = rt.npc.infer_state_from_manuscript("그는 적의를 품고 공격했다.", "장무기")
        assert state  # 어떤 상태든 추론됨

    def test_get_current_state_default(self, rt):
        assert rt.npc.get_npc_current_state("미등록NPC") == "neutral"

# ── Faction ──
class TestFactionSubmodule:
    def test_register_faction(self, rt):
        rt.factions.register_faction_v59("무림맹", power_level=80)
        assert "무림맹" in rt.faction_states

    def test_set_faction_relation(self, rt):
        rt.factions.register_faction_v59("무림맹", power_level=80)
        rt.factions.register_faction_v59("마교", power_level=70)
        rt.factions.set_faction_relation_v59("무림맹", "마교", "hostile")
        rel = rt.factions.get_faction_relation_v59("무림맹", "마교")
        assert rel == "hostile"

    def test_validate_faction_transition(self, rt):
        rt.factions.register_faction_v59("무림맹", power_level=80)
        rt.factions.register_faction_v59("마교", power_level=70)
        rt.factions.set_faction_relation_v59("무림맹", "마교", "hostile")
        result = rt.factions.validate_faction_transition_v59("무림맹", "마교", "hostile", "allied")
        assert "allowed" in result

    def test_power_balance(self, rt):
        rt.factions.register_faction_v59("무림맹", power_level=80)
        rt.factions.register_faction_v59("마교", power_level=70)
        result = rt.factions.get_faction_power_balance_v59()
        assert "balance_type" in result

# ── Integration ──
class TestIntegration:
    def test_delegation_npc(self, rt):
        """호스트 위임 메서드가 서브모듈로 라우팅."""
        result = rt.validate_transition("장무기", "neutral", "friendly", arc=1, episode=1)
        assert result["allowed"]

    def test_delegation_faction(self, rt):
        """호스트 위임 메서드가 서브모듈로 라우팅."""
        rt.register_faction_v59("무림맹", power_level=80)
        assert "무림맹" in rt.faction_states

    def test_lazy_init(self, rt):
        assert rt._npc is None
        _ = rt.npc
        assert rt._npc is not None
```

**최소 12개 테스트** — NPC 5 + Faction 4 + Integration 3.

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -c "import py_compile; py_compile.compile('modules/core/relationship_tracker_npc.py', doraise=True)"
python -c "import py_compile; py_compile.compile('modules/core/relationship_tracker_factions.py', doraise=True)"

# Gate 2: import 정상
python -c "from modules.core.relationship_tracker import RelationshipTracker; rt=RelationshipTracker(); print(f'npc={type(rt.npc).__name__}, factions={type(rt.factions).__name__}')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_relationship_tracker_submodules.py -v

# Gate 4: 기존 테스트 회귀
pytest tests/ -k "relationship" -v

# Gate 5: 전체 회귀
pytest tests/ -q

# Gate 6: 줄 수 확인
python -c "print(sum(1 for _ in open('modules/core/relationship_tracker.py')))"
# 목표: ~155줄 이하 (위임 stub 포함)

# Gate 7: pre-commit
pre-commit run --files modules/core/relationship_tracker.py modules/core/relationship_tracker_npc.py modules/core/relationship_tracker_factions.py tests/test_relationship_tracker_submodules.py
```

---

## 커밋

```
refactor(r5-2b): extract NPC + faction sub-modules from relationship_tracker (1,275→~155 lines, -88%)
```

push 포함.

---

## 실패 시

- `self.host.npc_states` KeyError → 호스트 `__init__`에서 초기화 확인
- 위임 stub 누락 → 외부 호출자 grep: `relationship_tracker\.\w+` 패턴으로 공개 API 전수 확인
- faction 메서드 내 `self.npc_states` 잔류 → `self.host.` 치환 누락
- 크래시 시 traceback + 원인만 보고 후 중단
