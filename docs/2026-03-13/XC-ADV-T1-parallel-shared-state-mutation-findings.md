# XC-ADV-T1: 병렬 실행 중 공유 상태 변이 — Findings

> 감사 일자: 2026-03-13
> 초점: Advisory 스레드들이 공유 객체를 변이하는가? 참조 전달로 인한 교차 오염 가능성

---

## 분석 요약

Advisory 체인 8개는 `ThreadPoolExecutor(max_workers=8)`로 병렬 실행된다.
CPython GIL이 dict 연산의 원자성을 일부 보장하지만, **복합 read-modify-write 패턴**은 GIL로 보호되지 않는다.
아래에서 각 advisory가 접근하는 공유 객체와 변이 패턴을 전수 조사한다.

---

## PASS 1: 후보 수집

### [XC-ADV-001] P2 | validation_results 병렬 setdefault 변이

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-001 |
| Severity | P2 |
| 현상 요약 | TruthGate와 NpcDrift가 동일 `validation_results[_ci]` dict에 병렬로 `setdefault()` 호출 |
| 코드 근거 | `stage4_interview_round.py:3858-3859` (TruthGate), `stage4_interview_round.py:3899-3900` (NpcDrift) |
| 영향 경계 | Stage 4 — Director 심사 시 validation_results 참조 |
| 테스트 근거 | 기존 테스트는 `_run_advisory_chain`을 MagicMock 처리 (D-T3 확인). 병렬 setdefault 경쟁 미검증 |
| 기존 중복 여부 | T3-004 (advisory 병렬 테스트 부재)와 관련되나, 구체적 mutation 지점은 신규 |
| 권장 후속 조치 | 낮은 위험 — CPython GIL 하에서 `dict.setdefault()`는 atomic. 그러나 다른 Python 구현(PyPy 등)에서는 보장 안 됨. 방어적 조치로 결과를 thread-local 수집 후 메인 스레드에서 merge 권장. 공수 0.5h |

**코드 스니펫:**
```python
# TruthGate advisory — L3858-3859
if _ci < len(validation_results) and isinstance(validation_results[_ci], dict):
    validation_results[_ci].setdefault("truth_gate_warnings", _tg_result["structured_warnings"])

# NpcDrift advisory — L3899-3900
if _ci < len(validation_results) and isinstance(validation_results[_ci], dict):
    validation_results[_ci].setdefault("npc_drift_warnings", _drifts)
```

**분석:**
- `validation_results`는 호출자(run 메서드)에서 생성된 `list[dict]`이며, 2개의 advisory(TruthGate, NpcDrift)가 동시에 같은 dict 원소에 `setdefault()`를 호출한다.
- 두 advisory가 **서로 다른 key**("truth_gate_warnings" vs "npc_drift_warnings")를 사용하므로, CPython에서는 실질적 경쟁이 발생하지 않는다.
- 다만, 이 패턴은 **의도적 공유 상태 변이**이며, 나머지 6개 advisory는 validation_results를 변이하지 않아 비대칭적이다.

---

### [XC-ADV-002] P3 | candidates dict 내부 참조 공유

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-002 |
| Severity | P3 |
| 현상 요약 | `candidates` list[dict]가 8개 스레드에 참조로 전달되나, 모든 advisory는 읽기 전용 접근 |
| 코드 근거 | `stage4_interview_round.py:3808-3815` (submit 호출부) |
| 영향 경계 | Stage 4 전체 |
| 테스트 근거 | 읽기 전용이므로 직접 위험 없음 |
| 기존 중복 여부 | OPUS-TF-T1 L273 ("동일 값 중복 계산") 관련 |
| 권장 후속 조치 | 현재 안전. 향후 advisory가 candidates를 변이하는 코드 추가 시 위험 발생 가능. 주석 경고 추가 권장. 공수 0.1h |

**분석:**
- 모든 advisory 메서드는 `_cand.get("manuscript", "")`로 읽기만 수행한다.
- `_fw["_cand_idx"] = _ci` 같은 패턴은 advisory 결과 dict(새로 생성)에 대한 쓰기이지, candidates 원본 변이가 아니다.
- `candidates` 자체의 원소 dict를 직접 수정하는 코드는 없다.

---

### [XC-ADV-003] P3 | self.ctx 공유 참조 (world_state, fact_ledger 등)

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-003 |
| Severity | P3 |
| 현상 요약 | 8개 advisory가 `self.ctx.world_state`, `self.ctx.fact_ledger`, `self.ctx.memory` 등 공유 객체를 동시 읽기 |
| 코드 근거 | `stage4_interview_round.py:3842-3843` (world_state/fact_ledger), `stage4_interview_round.py:3968` (memory), `stage4_interview_round.py:3931` (fact_ledger), `stage4_interview_round.py:4083` (db), `stage4_interview_round.py:4175-4177` (fact_ledger/db/world_state) |
| 영향 경계 | Stage 4 — 모든 advisory |
| 테스트 근거 | 모두 읽기 전용 접근. world_state.get_npc_role_snapshot(), fact_ledger.get_numbers() 등 getter만 호출 |
| 기존 중복 여부 | 신규 (기존 감사에서 구체적 접근 패턴 미분석) |
| 권장 후속 조치 | 현재 안전. world_state/fact_ledger가 advisory 실행 중 다른 경로에서 변이되지 않는 한 문제 없음. Stage4 interview round 실행 중에는 단일 스레드 제어 흐름 내에서만 호출되므로 안전. 공수 0h (조치 불필요) |

**분석:**
- 각 advisory는 `self.ctx`에서 읽기 전용으로 데이터를 취득한다.
- TruthGate: `self.ctx.world_state`, `self.ctx.fact_ledger` → 새 TruthGate 인스턴스 생성 시 참조 전달
- NpcDrift: `self.ctx.world_state.get_npc_role_snapshot()` → 스냅샷 dict 반환 (원본 아님)
- NumericDrift: `self.ctx.fact_ledger.get_numbers()` → dict 반환
- Flashback: `self.ctx.memory.retrieve_high_res_context()` → str 반환
- NumericConsistency: fact_ledger, db, world_state → 모두 getter 호출

---

### [XC-ADV-004] P2 | TruthGate 내부 world_state 메서드 호출 시 부작용 가능성

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-004 |
| Severity | P2 |
| 현상 요약 | TruthGate가 `world_state.get_deceased_npcs()`, `get_owned_items()` 등을 호출할 때 내부 캐시 갱신 등 부작용이 존재할 수 있음 |
| 코드 근거 | `truth_gate.py:100-108` (get_deceased_npcs), `truth_gate.py:180-186` (get_owned_items), `truth_gate.py:211-218` (get_destroyed_locations), `truth_gate.py:265-271` (get_known_skills), `truth_gate.py:331-335` (get_npc_role_snapshot) |
| 영향 경계 | Stage 4 — TruthGate + 동일 world_state 접근하는 다른 advisory |
| 테스트 근거 | world_state 구현체의 getter 메서드가 순수 함수인지 별도 확인 필요 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | world_state getter 메서드의 순수성 확인. 만약 내부 캐시/lazy-load 패턴이 있다면 thread-safety 이슈 발생 가능. 공수 0.5h (조사) |

---

### [XC-ADV-005] P2 | _truth_gate_llm_ask 콜백 공유

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-005 |
| Severity | P2 |
| 현상 요약 | 8개 advisory 중 LLM 호출이 필요한 6개가 동일한 `self._truth_gate_llm_ask` 콜백을 동시 호출 |
| 코드 근거 | `stage4_interview_round.py:3844` (TruthGate), `3883` (NpcDrift), `3935` (NumericDrift), `3959` (Flashback), `4038` (InfoParadox), `4089` (RelDrift), `4137` (LongTermRep) |
| 영향 경계 | Stage 4 — LLM API 호출 경로 |
| 테스트 근거 | llm_ask 콜백이 thread-safe인지는 LLM provider 구현에 의존 |
| 기존 중복 여부 | 신규 (기존 T3-004는 테스트 갭만 언급, 콜백 thread-safety 미분석) |
| 권장 후속 조치 | `_truth_gate_llm_ask`가 내부적으로 상태를 변이하지 않는 순수 wrapper인지 확인 필요. Gemini Provider의 `generate_content` 호출은 일반적으로 stateless이므로 안전할 것으로 추정되나, Context Caching이 관여하면 경쟁 가능. 공수 1h (조사+방어 코드) |

---

## PASS 2: 교차 검증

| ID | PASS 1 신뢰도 | PASS 2 판정 | 근거 |
|----|-------------|------------|------|
| XC-ADV-001 | HIGH | **유효** | CPython GIL 하에서 setdefault() atomic이나, 비대칭 설계 + 비CPython 미지원 |
| XC-ADV-002 | HIGH | **유효 (낮은 위험)** | 현재 모든 advisory 읽기 전용 확인 완료 |
| XC-ADV-003 | HIGH | **유효 (낮은 위험)** | getter만 호출, 실행 중 외부 변이 경로 없음 |
| XC-ADV-004 | MED | **유효** | world_state 구현체 미확인이나 getter 패턴상 부작용 가능성 낮음 |
| XC-ADV-005 | MED | **유효** | LLM 콜백 자체는 stateless 추정, Context Caching 경로 확인 필요 |

---

## PASS 3: 최종 확정

| ID | 최종 Severity | 비고 |
|----|-------------|------|
| XC-ADV-001 | **P2** | 설계 결함 수준. 현재 CPython에서 안전하나 방어적 개선 권장 |
| XC-ADV-002 | **P3** | 정보성. 현재 안전 |
| XC-ADV-003 | **P3** | 정보성. 현재 안전 |
| XC-ADV-004 | **P2** | world_state 구현체 순수성 미확인. 잠재적 위험 |
| XC-ADV-005 | **P2** | LLM 콜백 thread-safety 미확인. 잠재적 위험 |

---

## 총평

Advisory 체인의 병렬 실행에서 **명시적 공유 상태 변이**는 2건(XC-ADV-001: validation_results setdefault)으로 제한적이다.
나머지 공유 참조(candidates, ctx.world_state, ctx.fact_ledger, llm_ask 콜백)는 모두 읽기 전용 또는 stateless 호출이다.

CPython GIL이 현재 런타임에서 dict.setdefault() 원자성을 보장하므로 **즉시 장애로 이어지지는 않으나**,
설계 원칙 측면에서 advisory 결과는 thread-local로 수집 후 메인 스레드에서 merge하는 패턴이 더 안전하다.
