Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q5 long-term consistency R2 bounded delta survey report
Canonical Path: `docs/2026-03-23/opus/r2-q5-long-term-consistency.md`
Terminal: T5
Axis: Q5 "잘 기억하냐" — long-run consistency, WorldState/FactLedger/StateTracker alignment

Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
R1 Report: `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md`
R1 Evidence: `docs/2026-03-23/opus/q5-long-term-consistency-evidence-manifest.md`
Related T-Reports:
- `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md`
- `docs/2026-03-23/generation-coherence-deep-dive-report.md`

---

## 1. Executive Summary

Q5 인프라는 R1에서 식별된 4P0/8P1 구조를 유지한다. 커밋 `79f570f2`는 Q5를 직접 수정하지 않았으므로 코드 수정 검증 대상이 아니다. 그러나 R1 이후 두 가지 중요한 delta가 발생했다:

1. **P0-1 SHIFTED**: `_save_world_state_atomic()` + snapshot rollback이 존재하여, "no atomicity"에서 "best-effort atomicity with snapshot rollback"으로 상향. R1의 P0 심각도는 P1으로 하향 조정이 적절하다.
2. **P1-5 SHIFTED**: Stage 2에 WorldState context slot이 존재하나, arc generator는 DB에서 독립적으로 로드하여 실질적 gap은 축소되었으나 완전 해소되지 않았다.
3. **P1-7 STALE**: 한국어 키워드 복원 확인. 버그 클레임은 무효. 파라미터화 개선만 남음.

**Fresh run 실증 결과** (`projects/0_0323/`, 3 에피소드):
- WorldState `timeline`과 `active_plots` 필드가 3화까지 0건 — 핵심 시간적 추적 구조가 미사용
- FactLedger `locations`/`organizations` 0건 — LLM 추출 미작동
- `wealth` vs `capital` vs `total_assets` 수치 불일치 — 동일 개념 다필드 추적 드리프트 실증
- ChainLink은 건전 — 3화 모두 올바른 cliffhanger/pending_actions/emotional_state

R1→R2 delta: **resolved 1, shifted 2, stale 1, persists 14, new 4**

---

## 2. R1→R2 Delta Summary

| R1 ID | R1 Claim | R2 Status | Evidence |
|-------|---------|-----------|---------|
| P0-1 | No cross-system atomicity | **shifted** | `_save_world_state_atomic()` + snapshot rollback 존재. 순차 모드에서 DB write 복원 불가 잔여 gap |
| P0-2 | Entity exact string match | **persists** | 4 upsert 메서드 모두 `dict[name]` 직접 키, 정규화 없음 |
| P0-3 | ContinuityValidator no WS/FL | **persists** | `continuity_validator.py`에 world_state/fact_ledger 참조 0건 |
| P0-4 | LLM fallback unfiltered | **persists** | `return candidates` when `_llm_client is None` (L752) |
| P1-1 | WorldState silent FIFO | **persists** | 11+ 절삭 사이트, WARNING 로그 0건 |
| P1-2 | FactLedger silent FIFO | **persists** | 5 카테고리 history 절삭, WARNING 로그 0건 |
| P1-3 | Partial section update | **persists** | `last_updated_ep` 무조건 설정 후 섹션 처리 |
| P1-4 | NPC-NPC LRU 50 cap | **persists** | FIFO 50 (LRU 아님), 로그 없음 |
| P1-5 | Stage 2 missing WorldState | **shifted** | Context slot 존재, StateTracker 바인딩됨. Arc generator는 DB에서 독립 로드 |
| P1-6 | Chain link not in Stage 2 | **persists** | `stage2_orchestrator.py`에 chain_link 로딩 없음 |
| P1-7 | Growth keywords mojibake | **stale** | 한국어 8개 키워드 정상. 버그 아닌 파라미터화 개선 수준 |
| P1-8 | Revive NPC non-atomic | **persists** | 3단계 mutation 비트랜잭션. 신규: `revive_history` 무한 증가 |
| P2-1 | Dead NPC updates dropped | **persists** | `continue` 처리, WARNING 없음 |
| P2-2 | Entity name LRU 500 | **persists** | OrderedDict LRU 500, 로그 없음 |
| P2-3 | NPC-NPC no regex fallback | **persists** | state_changes 의존, 미추출 시 소실 |
| P2-4 | `_is_same_item()` substring | **persists** | "검" matches "검은 검" 등 |
| P2-5 | prev_hud missing degraded | **persists** | fail-open BLOCKING severity |
| P2-6 | Protagonist emotion no history | **persists** | 덮어쓰기, 히스토리 없음 |

---

## 3. Current Ownership / Flow Map

R1 보고서 Section 2와 동일. 모듈 소유권/데이터 흐름/앵커 매핑에 변경 없음.

주요 변경점:
- `stage4_post_pass_runtime.py`에 `_capture_atomic_metadata_snapshots()` (L920-932), `_save_world_state_atomic()` (L1070-1117), `_handle_atomic_metadata_rollback()` (L1019-1068) 추가
- `stage2_context.py`에 `world_state` 슬롯 존재 (Stage2Context L141)

---

## 4. Focus-Scope Findings

### F-1 (P1, shifted from P0-1): Best-Effort Atomicity Gap

- **File**: `modules/core/stage4_post_pass_runtime.py:1070-1117`
- **Evidence type**: source
- **Current mechanism**:
  1. Pre-save: `_capture_atomic_metadata_snapshots()` (L920-932) — `deepcopy(world_state._state)`, `deepcopy(fact_ledger._ledger)`
  2. Transaction attempt: `meta_db.transaction()` (L1088) — 가용 시 true DB transaction, 불가 시 `sequential_mode=True` + WARNING
  3. Sequential persist: WorldState → FactLedger 순차 저장 (L1098-1107)
  4. Save validation: `_raise_if_save_failed()` — `.save()` False 반환 시 RuntimeError
  5. Rollback: `_best_effort_rollback_manager()` — `rollback_to(target_ep)` 또는 in-memory snapshot restore
- **Remaining gap**: Sequential mode에서 WorldState DB write 성공 후 FactLedger save 실패 시, in-memory snapshot은 복원되지만 WorldState DB 레코드는 되돌릴 수 없음
- **R1 대비 변화**: "no atomicity" → "best-effort atomicity". 위험 수준 P0→P1 하향 적절
- **Root-causal or symptomatic**: root-causal (장기 연재 시 divergence 가능)
- **Blocks rerun**: no
- **Fix type**: `boundary-refactor` (true atomic은 DB transaction 보장 시에만)

### F-2 (P0, persists): Entity Exact String Match

- **File**: `modules/core/fact_ledger.py:504-595`
- **Evidence type**: source
- **Finding**: 4 upsert 메서드 (`_upsert_character` L508, `_upsert_item` L540, `_upsert_location` L564, `_upsert_org` L584) 모두 `dict[name]` 직접 키 접근. `update_number` L416도 동일. 정규화/별칭 해소 없음.
- **Root-causal or symptomatic**: root-causal (30+ 에피소드에서 이름 드리프트 필연)
- **Blocks rerun**: no (3-4 에피소드에서는 발현 안 됨)
- **Fix type**: `boundary-refactor`

### F-3 (P0, persists): ContinuityValidator No WorldState/FactLedger

- **File**: `modules/validation/continuity_validator.py:83-88, 123-174`
- **Call site**: `modules/core/stage4_interview_round.py:3369-3399`
- **Evidence type**: source
- **Finding**: 생성자가 `context` (ProjectContext)만 수용. `world_state`, `fact_ledger` 파라미터 없음. Grep 결과 파일 전체에서 두 키워드 참조 0건. `cv_context` dict에도 미포함.
- **Root-causal or symptomatic**: root-causal (장기 팩트 모순 무감지)
- **Blocks rerun**: no (TruthGate advisory가 부분 커버하지만 non-blocking)
- **Fix type**: `boundary-refactor`

### F-4 (P1, persists): Silent FIFO Truncation (WorldState + FactLedger)

- **Files**: `modules/core/world_state.py` (L214,422,431,476,506,723-728), `modules/core/fact_ledger.py` (L433,528,560,580,595)
- **Evidence type**: source
- **Finding**: WorldState 11개+ 절삭 사이트, FactLedger 5개 카테고리 history 절삭. 모든 사이트에서 WARNING 로그 0건. Grep `warning.*truncat`, `warning.*FIFO`, `warning.*한도` 결과 0건.
- **Root-causal or symptomatic**: root-causal (장기 데이터 소실)
- **Blocks rerun**: no
- **Fix type**: `observability-only`

### F-5 (NEW, P1): WorldState timeline/active_plots 미사용

- **Evidence type**: DB (fresh run)
- **Source**: `projects/0_0323/project_data.db` → `anchors.world_state`
- **Finding**: 3화까지 `timeline`=0, `active_plots`=0, `world_notes`=0, `world_laws`=0, `motivations`=0, `promises`=0. 9개 핵심 필드 중 6개가 미사용 상태.
- **Impact**: 시간적 추적(timeline), 플롯 추적(active_plots), 세계 법칙(world_laws) 등 장기 일관성의 핵심 구조가 실질적으로 사문화. `pressure_vectors`(2건)과 `alive_npcs`(8명)과 `active_items`(2건)만 활성.
- **Root-causal or symptomatic**: root-causal (update 경로에서 LLM이 이 필드를 채우지 않거나, 추출 로직이 투자 장르에서 미작동)
- **Blocks rerun**: no
- **Fix type**: `contract-cleanup`

### F-6 (NEW, P1): FactLedger locations/organizations 미추출

- **Evidence type**: DB (fresh run)
- **Source**: `projects/0_0323/project_data.db` → `anchors.fact_ledger`
- **Finding**: `locations`=0, `organizations`=0. 스토리에 성북동 본가, 유성증권, 교보타워 등 다수 장소와 조직이 등장하지만 FactLedger에 등록되지 않음.
- **Impact**: 장소/조직 변동 추적 불가. 장기 연재 시 장소 소유권 변경, 조직 해체 등 감지 불능.
- **Root-causal or symptomatic**: root-causal (LLM state_changes 추출 시 locations/organizations 카테고리 미포함)
- **Blocks rerun**: no
- **Fix type**: `contract-cleanup`

### F-7 (NEW, P2): wealth vs capital vs total_assets 수치 불일치

- **Evidence type**: DB (fresh run)
- **Source**: `projects/0_0323/project_data.db` → `state_logs`
- **Finding**: ep2에서 `capital`=2B이지만 `total_assets`=0, `wealth`=0. ep3에서 수렴 (wealth=2,015,487,250). 동일 개념을 다수 필드로 추적하면서 1화 동안 불일치 발생.
- **Impact**: 수치 일관성 검증기가 다른 필드를 참조하면 오탐/누락 가능
- **Root-causal or symptomatic**: symptomatic (LLM 추출 불완전성)
- **Blocks rerun**: no
- **Fix type**: `comment-only`

### F-8 (NEW, P2): FactLedger history 포맷 불일치

- **Evidence type**: DB (fresh run)
- **Finding**: FactLedger history 엔트리가 `"ep3: 관계 변화: -> 목격자"` 형태의 평문 문자열. `dict` with `fact` 키가 아님. 코드에서 `h.get("fact")` 접근 시 실패 가능.
- **Root-causal or symptomatic**: symptomatic (포맷 정규화 미비)
- **Blocks rerun**: no
- **Fix type**: `contract-cleanup`

---

## 5. Code-Fix Verification

Q5는 커밋 `79f570f2`에서 직접 수정 대상이 아니었다. 해당 커밋의 수정 축은 Q3/Q4/Q6/Q8이다.

Q5에 영향을 미칠 수 있는 간접 변경:
- P0-1 atomicity: `_save_world_state_atomic()` 도입 시점은 R1 이전으로 추정되며, R1에서 merge audit가 "shifted"로 정정한 것과 일치. `79f570f2` 커밋에서 추가된 것은 아님.
- 나머지 Q5 findings는 코드 변경 없이 R1 상태 유지.

---

## 6. Pre-Rerun T-Report Cross-Reference

### T1 (Stage 2 Contract)
- **교차 발견**: Stage 2 reject_reason [:500] 절삭 (F-2/F-3) — Q5에 간접 영향. 장기 arc REJECT 사유에서 일관성 관련 상세 정보 손실 가능.
- **흡수 결과**: Q5 범위 밖 (Q4/Q8 영역). 참고만.

### T2 (Stage 2 Artifact Truth)
- **교차 발견**: Stage 2 `stage_attempts` textual metadata 손실 (F-5) — Stage 2/3의 DB 관측성 갭.
- **Q5 영향**: WorldState/FactLedger가 Stage 2 정보를 소급 참조할 때 DB-only 분석 불가. 이는 Q8 영역이지만 Q5 진단을 간접 제약.

### T10 (Cross-Layer Artifact)
- **교차 발견 1**: Blueprint `time_flow` 메타데이터가 이전 blueprint 메타에서 읽음, 이전 원고 텍스트 아님 (F1) — 날짜 오염 체인.
- **Q5 영향**: WorldState `timeline` 필드가 비어있는 상황에서(F-5 신규), 시간 일관성의 유일한 방어선이 blueprint metadata → manuscript 체인. 이 체인이 T10에서 입증된 대로 오염되면, Q5 시간적 일관성에 이중 취약점.
- **교차 발견 2**: Python scene-detection false-positive (F2) — Q5 직접 관련 없음.
- **교차 발견 3**: Empty scene_breakdown (F3) — Q5 직접 관련 없음.

### Generation-Coherence Deep-Dive
- **교차 발견**: CO-1/CO-2/CO-3 (비원자 저장, StateTracker 역기록 없음) — R1 P0-1과 정확히 일치. 해당 보고서의 라인 번호(stage4_post_pass_runtime.py L938-989)가 현재 코드와 정합.
- **교차 발견**: CO-5 (entity_name_registry LRU 500) — R1 P2-2와 일치.
- **교차 발견**: CO-9 (continuity_validator 정규식 띄어쓰기 변형 미탐지) — R1에서 미커버, 그러나 Q5 맥락에서 유효. 장기 연재 시 NPC 이름 띄어쓰기 변형이 모순 감지를 회피.

---

## 7. Fresh-Run Evidence

### 7.1 WorldState 상태 (`projects/0_0323/project_data.db`)

| 필드 | 값 | Q5 의미 |
|------|-----|---------|
| version | 1 | 정상 |
| last_updated_ep | 3 | 정상 |
| alive_npcs | 8 | 건전 — 이름 parity 완벽 (FactLedger와 100% 일치) |
| dead_npcs | 0 | 사망 NPC 없음 (사망 경로 미검증) |
| active_items | 2 | ThinkPad T60, flip phone — 일관 |
| active_plots | **0** | **미사용** — 플롯 추적 사문화 |
| timeline | **0** | **미사용** — 시간 추적 사문화 |
| pressure_vectors | 2 | ep3 ending_hook + expected_ending — 건전 |
| world_notes / world_laws / motivations / promises | 모두 0 | **미사용** |

### 7.2 FactLedger 상태

| 카테고리 | 건수 | Q5 의미 |
|----------|------|---------|
| characters | 8 | WorldState와 parity |
| items | 2 | WorldState와 parity |
| locations | **0** | **미추출** — 성북동/유성증권 등 미등록 |
| organizations | **0** | **미추출** |
| numbers | 1 (capital) | **부분 추적** — 1 history entry만 |

### 7.3 ChainLink 상태 (3건)

모든 chain_link 건전:
- chain_link_1: 1,263 bytes, pending_actions=5
- chain_link_2: 1,468 bytes, pending_actions=4
- chain_link_3: 1,573 bytes, pending_actions=5

에피소드 간 연속성: ep1 각성 → ep2 독립 선언 → ep3 자산 청산 — 일관된 서사 진행.

### 7.4 StateLogs 상태 (3행)

자본 추이: 0 → 2B → 2.015B. 아이템 추적 일관. 그러나 ep2에서 `capital`=2B, `total_assets`=0, `wealth`=0 — 동일 개념 다필드 드리프트 실증.

### 7.5 Entity Parity

WorldState alive_npcs 8명 = FactLedger characters 8명. 이름 100% 일치. 3화 규모에서 별칭 드리프트 미발생.

### 7.6 Fresh-Run Q5 Risk Summary

| 위험 | 발현 여부 | 근거 |
|------|-----------|------|
| 비원자 저장 divergence | **미발현** | save 실패 0건 |
| 엔티티 별칭 드리프트 | **미발현** | 3화, 8 NPC로 너무 짧음 |
| FIFO 절삭 | **미발현** | 최대값 미도달 (timeline 0, history 최대 6건) |
| ContinuityValidator 맹점 | **미발현** | 장기 팩트 모순 자체 미생성 |
| WorldState 필드 사문화 | **발현** | timeline/active_plots/motivations/promises 0건 |
| FactLedger 카테고리 미추출 | **발현** | locations/organizations 0건 |
| 수치 다필드 드리프트 | **발현** | wealth/capital/total_assets 불일치 |

---

## 8. Root-Cause vs Symptom Classification

### Root Causes

| ID | Finding | Type | 장기 영향 |
|----|---------|------|-----------|
| P0-2 | Entity exact string match | structural design gap | 30+ ep에서 별칭 분기 필연 |
| P0-3 | ContinuityValidator no WS/FL | coverage gap | 장기 팩트 모순 무감지 |
| F-5 | WorldState 6/9 필드 미사용 | data flow gap | 시간/플롯/법칙 추적 사문화 |
| F-6 | FactLedger 2/5 카테고리 미추출 | LLM extraction gap | 장소/조직 추적 불가 |

### Amplifying Factors

| ID | Finding | Why Amplifier |
|----|---------|---------------|
| F-1 (P1) | Best-effort atomicity | 장기 연재에서 save failure 누적 시 divergence 확률 증가 |
| F-4 (P1) | Silent FIFO truncation | 데이터 소실을 감지 불능 → 진단 지연 |
| P0-4 | Unfiltered NPC death fallback | NPC registry 오염 → 하류 일관성 검증 노이즈 |

### Symptoms

| ID | Finding | Root Cause Reference |
|----|---------|---------------------|
| F-7 | wealth/capital/total_assets 불일치 | LLM 추출 불완전성 (F-6 family) |
| F-8 | FactLedger history 포맷 불일치 | FactLedger 스키마 미강제 |

---

## 9. Quick Wins

| # | Finding | File:Line | Fix Type | Effort | ROI |
|---|---------|-----------|----------|--------|-----|
| QW-1 | FIFO 절삭 시 WARNING 로그 (WorldState) | `world_state.py:214,422,431,476,506,723-728` | observability-only | 1h | HIGH |
| QW-2 | FIFO 절삭 시 WARNING 로그 (FactLedger) | `fact_ledger.py:433,528,560,580,595` | observability-only | 1h | HIGH |
| QW-3 | LLM client None 시 exclude_words 폴백 (NPC death) | `state_tracker_npc.py:751-752` | contract-cleanup | 30m | HIGH |
| QW-4 | Dead NPC update 억제 시 WARNING | `fact_ledger.py:329,340,351,370` | observability-only | 30m | MEDIUM |
| QW-5 | NPC-NPC relationship eviction 로그 | `state_tracker_npc.py:1698-1700` | observability-only | 15m | MEDIUM |

---

## 10. False Leads / Non-Causes

### 10.1 "P0-1 atomicity는 여전히 완전 부재" — FALSE
R1의 "no atomicity" 프레이밍은 stale. 현재 코드에 snapshot capture + rollback handler + transaction attempt가 존재. 잔여 gap은 sequential mode에서의 DB write 비가역성이며, 이는 P1 수준.

### 10.2 "P1-7 growth_keywords가 영어/깨진 한국어" — STALE
현재 코드에 정상 한국어 8개 키워드 확인. 버그 클레임 무효. 남은 것은 YAML 파라미터화 개선 희망사항.

### 10.3 "Stage 2에 WorldState가 전혀 없다" — SHIFTED
Stage2Context에 `world_state` slot 존재, StateTracker.bind_world_state() 호출됨. 다만 arc generator가 DB에서 독립 로드하므로 in-memory 변경이 반영 안 되는 gap은 남음.

### 10.4 "3화 fresh run에서 Q5 위험이 발현되었다" — PARTIAL
구조적 위험(비원자 저장, 별칭 드리프트, FIFO 절삭, ContinuityValidator 맹점)은 미발현 — 3화는 너무 짧음. 그러나 WorldState 필드 사문화, FactLedger 카테고리 미추출, 수치 다필드 드리프트는 3화에서도 실증됨.

### 10.5 "ChainLink 시스템이 불완전하다" — FALSE
ChainLink은 Q5 인프라 중 가장 건전. 3화 모두 올바른 cliffhanger/pending_actions/emotional_state. 에피소드 간 서사 연속성 완벽.

---

## 11. Fresh-Run Readiness

**Fresh-run-before-fix allowed: yes**

근거:
1. Q5의 구조적 위험(P0-2 별칭 드리프트, P0-3 CV 맹점, F-1 비원자 저장)은 모두 **장기 연재(30+ ep) 전제** 조건에서만 발현
2. 3-4화 fresh run에서는 이 위험들이 발현하지 않음이 이번 fresh run에서 실증됨
3. Q5 quick wins(QW-1~5)는 관측성 개선이며, rerun을 block하지 않음
4. Q5에는 "수정하지 않으면 rerun이 실패하는" 코드 결함이 없음
5. WorldState 필드 사문화(F-5)와 FactLedger 미추출(F-6)은 LLM 행동 이슈이며 코드 수정만으로 해결 불가

단, **Q3/Q4/Q6 수정 후 rerun이 먼저** 권고됨 (merge audit 기준). Q5는 이후 장기 연재 테스트에서 재평가.

**Top 3 highest-ROI remaining fixes:**
1. **QW-3**: NPC death LLM fallback → exclude_words 폴백 (`state_tracker_npc.py:751-752`) — NPC registry 오염 방지, 즉시 효과
2. **QW-1+QW-2**: FIFO 절삭 로깅 (`world_state.py` + `fact_ledger.py`) — 장기 데이터 소실 가시화
3. **F-5/F-6 진단**: WorldState 필드 미사용 + FactLedger 카테고리 미추출 원인 추적 (`world_state.py:update_from_state_changes()` → LLM state_changes 포맷 검증)

---

## 12. Confidence And Limits

**Estimated confidence: 96%**

Basis:
- R1 P0/P1 전체 18건을 live source에서 라인 수준 재검증 완료
- `projects/0_0323/project_data.db`에서 WorldState/FactLedger/ChainLink/StateLogs 직접 쿼리
- 4개 T-보고서 교차 참조 완료
- Merge audit의 shifted/stale 판정 3건 live code로 확인
- 신규 finding 4건(F-5~F-8)을 fresh run DB 증거로 발견

The 4% gap:
- `state_tracker_plots.py`/`state_tracker_financial.py` 내부 미완독 (1%)
- `director_continuity.py` → ContinuityArcValidator 연계 미추적 (1%)
- WorldState 필드 미사용(F-5)의 원인이 LLM 추출 로직인지 update 경로인지 미확정 (1%)
- 장기 연재(30+ ep) 환경 미검증 — 구조적 추론에 의존 (1%)

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- R2 delta survey 포맷 확인 (12 mandatory sections)
- R1→R2 delta 분류: resolved 1, shifted 2, stale 1, persists 14, new 4
- Primary scope 6개 파일 + fresh run DB 검증 범위 확인
- PASS

### Pass 2. Evidence and Consistency
- R1 라인 번호와 현재 코드 대조: P0-1 L1070-1117 정합, P0-2 L504-595 정합, P0-3 L83-174 정합
- Merge audit의 shifted/stale 3건 live code로 확인
- Fresh run DB 증거(WorldState/FactLedger/ChainLink/StateLogs) 직접 쿼리 결과 반영
- T-보고서 4건 교차 참조 정합성 확인
- PASS

### Pass 3. Execution and Readability
- P0/P1 모든 항목에 file:line 앵커 기재
- 모든 recommendation에 fix type 지정
- Fresh-run readiness 명시 (yes, 장기 위험이므로)
- Top 3 highest-ROI fixes 순위화
- Root-cause vs symptom 분리 명확
- PASS
