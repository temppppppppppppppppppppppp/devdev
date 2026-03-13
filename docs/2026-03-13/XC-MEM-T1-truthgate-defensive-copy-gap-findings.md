# XC-MEM-T1: TruthGate 방어적 복사 갭 — 상세 분석

> 날짜: 2026-03-13
> Track: XC-MEM / Target: T1
> 대상: `modules/core/truth_gate.py`, `modules/core/stage4_interview_round.py`

---

## 1. 분석 범위

TruthGate가 `validate()` 호출 시 수신하는 `state_updates` dict와 `world_state`/`fact_ledger` 객체가 caller의 상태를 변이시킬 수 있는지 검사한다.

---

## 2. 코드 증거

### 2.1 TruthGate.validate() 시그니처

```python
# truth_gate.py:24-48
def validate(
    self,
    manuscript: str,
    state_updates: dict,
    *,
    npc_registry: dict | None = None,
) -> dict:
    ...
    su = state_updates if isinstance(state_updates, dict) else {}
    ...
```

`su`는 `state_updates`의 직접 참조이다. `state_updates`가 dict가 아닌 경우에만 빈 dict로 대체된다. 정상 경로에서는 caller가 보낸 dict 참조를 그대로 사용한다.

### 2.2 TruthGate 내부의 state_updates 사용 패턴

7개 검사 메서드 전량 조사 결과:

| 메서드 | 읽기 전용 | 쓰기 위험 |
|--------|----------|----------|
| `_check_deceased_resurrection` (L79) | `.get("npc_updates", {})` → 읽기만 | 없음 |
| `_check_unowned_items` (L169) | `.get("item_updates", {})` → 읽기만 | 없음 |
| `_check_destroyed_locations` (L203) | `.get("location_update", "")` → 읽기만 | 없음 |
| `_check_skill_duplication` (L252) | `.get("skill_updates", [])` → 읽기만 | 없음 |
| `_check_karma_bounds` (L288) | `.get("karma")`, `.get("protagonist_updates", {})` → 읽기만 | 없음 |
| `_check_npc_role_consistency` (L321) | `.get("npc_attribute_changes")`, `.get("npc_updates", {})` → 읽기만 | 없음 |
| `_check_world_law_violation` (L386) | `manuscript`만 사용, `state_updates` 미참조 | 없음 |

**결론**: TruthGate 내부는 `state_updates`에 대해 **순수 읽기 전용**으로 동작한다. `.get()` 호출만 하며, 키 추가/삭제/값 변경이 없다.

### 2.3 world_state / fact_ledger 객체 참조

```python
# truth_gate.py:19-22
def __init__(self, world_state=None, fact_ledger=None, llm_ask=None):
    self._world_state = world_state
    self._fact_ledger = fact_ledger
```

TruthGate는 `world_state`와 `fact_ledger` 인스턴스 참조를 보유하지만, 코드 전량 검사 결과:

- `self._world_state`는 `get_deceased_npcs()`, `get_owned_items()`, `get_destroyed_locations()`, `get_known_skills()`, `get_npc_role_snapshot()`, `get_world_laws()` 등 **읽기 전용 접근자**만 호출
- `self._fact_ledger`는 TruthGate 내부에서 **참조되지 않음** (생성자에서 받기만 하고 실제 사용 없음)
- 어떤 검사에서도 `save()`, `update_from_state_changes()` 등 쓰기 메서드를 호출하지 않음

### 2.4 Caller 측 (stage4_interview_round.py) 방어 패턴

```python
# stage4_interview_round.py:3848-3856
for _ci, _cand in enumerate(candidates):
    _ms = _cand.get("manuscript", "")
    ...
    _tg_result = _tg.validate(
        manuscript=_ms,
        state_updates=_cand.get("state_updates") or {},
        npc_registry=_npc_reg,
    )
```

`_cand.get("state_updates") or {}`는 원본 candidate dict의 `state_updates` 값을 직접 전달한다. 그러나 위 2.2에서 확인한 바와 같이 TruthGate는 읽기만 수행하므로, 방어적 복사 없이도 안전하다.

### 2.5 Advisory 병렬 실행 시 공유 상태

```python
# stage4_interview_round.py:3806-3815
with ThreadPoolExecutor(max_workers=8, thread_name_prefix="advisory") as executor:
    futures[executor.submit(self._advisory_truth_gate, candidates, validation_results, next_ep)] = "TruthGate"
    futures[executor.submit(self._advisory_npc_drift, candidates, validation_results, next_ep)] = "NpcDrift"
    ...
```

8개 advisory가 동일한 `candidates` 리스트와 `validation_results` 리스트를 공유한다. 각 advisory는 `validation_results[_ci].setdefault(...)` 패턴으로 결과를 쓴다(L3858-3859). 이는 **서로 다른 키**에 대한 `.setdefault()`이므로 dict 레벨 data race는 CPython GIL 하에서 안전하다.

단, `_tg_result["structured_warnings"]`에 대한 `_sw["text"]` 수정(L3862)은 TruthGate가 반환한 dict의 내부 값을 in-place 변경하는데, 이 dict는 TruthGate 내부에서 새로 생성된 것이므로 caller 원본에 영향 없다.

---

## 3. Finding

### [XC-MEM-T1-001] P3 | TruthGate state_updates 방어적 복사 부재 (설계상 안전)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-001 |
| Severity | P3 |
| 현상 요약 | TruthGate.validate()가 state_updates를 참조로 수신하나, 내부 7개 검사 모두 읽기 전용이므로 실제 변이 위험 없음 |
| 코드 근거 | `truth_gate.py:48` `su = state_updates if isinstance(state_updates, dict) else {}` — 참조 직접 사용. 그러나 L50-57의 7개 검사 전부 `.get()` 읽기만 |
| 영향 경계 | Stage 4 advisory 체인 |
| 테스트 근거 | `tests/test_truth_gate.py` 존재 — validate() 호출 후 입력 dict 변이 여부 검증 테스트는 없으나 현재 코드에서 변이 경로 없음 |
| 기존 중복 여부 | 기존 262+ finding에 TruthGate 방어적 복사 관련 finding 없음. `checklist-3pass-audit.md:64`에서 "TruthGate 7개 검사 OK" 확인만 |
| 권장 후속 조치 | 향후 TruthGate에 쓰기 로직 추가 시 `copy.deepcopy(state_updates)` 적용 권장. 현재는 조치 불필요 (0.5h 방어적 개선) |

### [XC-MEM-T1-002] P3 | fact_ledger 인스턴스 미사용 (dead parameter)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-002 |
| Severity | P3 |
| 현상 요약 | TruthGate 생성자가 `fact_ledger` 파라미터를 받지만, 7개 검사 메서드 어디에서도 `self._fact_ledger`를 참조하지 않음 |
| 코드 근거 | `truth_gate.py:21` `self._fact_ledger = fact_ledger` — 할당 후 미사용. `stage4_interview_round.py:3843` `fact_ledger=getattr(self.ctx, "fact_ledger", None)` — 전달은 하지만 TruthGate 내부에서 사용되지 않음 |
| 영향 경계 | 메모리 안전 관점에서 영향 없음. 설계 의도 불일치 가능성 |
| 테스트 근거 | 기존 테스트에서 fact_ledger 전달 여부 무관하게 통과 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | fact_ledger 기반 검사(수치 교차 검증 등) 추가 예정이면 유지, 아니면 파라미터 제거 검토 (0.5h) |

### [XC-MEM-T1-003] P2 | validation_results 공유 list에 대한 병렬 쓰기

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-003 |
| Severity | P2 |
| 현상 요약 | 8개 advisory가 ThreadPoolExecutor로 병렬 실행되면서 동일한 `validation_results` 리스트의 같은 인덱스 dict에 서로 다른 키로 `.setdefault()` 호출. CPython GIL 하에서 dict 단위 thread-safe이나, 공식 보장이 아닌 구현 의존적 동작 |
| 코드 근거 | `stage4_interview_round.py:3808-3815` — 8개 future 모두 `validation_results` 공유. L3858-3859 `validation_results[_ci].setdefault("truth_gate_warnings", ...)`, L3899 NpcDrift도 동일 패턴 |
| 영향 경계 | Stage 4 advisory 체인. PyPy/free-threaded Python에서 data race 가능 |
| 테스트 근거 | 병렬 쓰기 safety 검증 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 advisory 병렬 쓰기 관련 지적 없음 |
| 권장 후속 조치 | `validation_results` 대신 각 advisory가 독립 결과를 반환하고 main thread에서 merge하는 패턴 권장 (2h) |

---

## 4. 종합 판정

T1 영역은 **현재 코드 기준으로 실질적 메모리 오염 위험이 없다**. TruthGate 내부는 순수 읽기 전용이며, world_state/fact_ledger에 대한 쓰기 접근도 없다. 유일한 관심사는 병렬 advisory의 `validation_results` 공유 쓰기이나, CPython GIL 하에서 현실적 위험은 낮다.
