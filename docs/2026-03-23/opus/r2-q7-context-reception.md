Date: 2026-03-23
Status: final
Document Type: R2 Q7 context reception delta survey report
Terminal: T7
Axis: Q7 "잘 받냐" — context reception, prompt injection completeness, truncation/order problems
Canonical Path: `docs/2026-03-23/opus/r2-q7-context-reception.md`
Evidence Path: `docs/2026-03-23/opus/r2-q7-context-reception-evidence.md`
Source Order: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; Q7 scope files (stage4_context_builder.py, stage4_context_packets.py, chief_writer_context.py, chief_writer_context_packets.py, prompt_builder.py, base_agent.py) are clean — no dirty changes in primary scope`

---

## 1. Executive Summary

Q7 R2 delta survey 결과, R1의 5개 P1 finding 중 **1건 stale**, **3건 persists**, **1건 absorbed**로 분류된다. 커밋 79f570f2는 Q7 컨텍스트 수신 경로를 직접 수정하지 않았으므로, R1 finding 중 코드 수정으로 해소된 것은 없다.

R1에서 `fresh-run-before-fix allowed: no`로 판정했으나, R2에서는 **yes로 상향 조정**한다. 근거:
- Fresh run(`projects/0_0323/`) 실증: context budget 사용률 0.60-0.72% (2K-6K / 300K)
- 모든 P1 finding은 50+ 에피소드 장기연재에서만 발현하는 구조적 위험
- T9 root-cause 보고서: "No context/retrieval finding blocks the next rerun"
- Merge audit: Q7은 "long-run structural", rerun 후 후속

핵심 발견: R1 P1-4의 "Director 200K 하드코딩" 주장은 **stale (오보)**임을 git 고증으로 확인. Director prev_manuscripts도 CW와 동일하게 default(1M/80K)를 사용하며, P1-1/P1-5의 budget mismatch 범위에 흡수된다.

---

## 2. R1→R2 Delta Summary

| R1 Finding | R1 심각도 | R2 상태 | 근거 |
|------------|----------|---------|------|
| P1-1: CW prev_manuscripts 기본 1M 잘림 — 중간 화 소실 | P1 | **persists** | live code `chief_writer_context_packets.py:158` 확인, 변경 없음 |
| P1-2: head/tail 고정 비율 0.55 — 의미 단위 무시 | P1 | **persists** | live code `stage4_context_builder.py:125` 확인, 변경 없음 |
| P1-3: CP/World State budget 비보호 | P1 | **persists** | live code `stage4_context_builder.py:1144-1170` 확인, 보호 대상 2개뿐 |
| P1-4: Director ensemble prev_manuscripts 200K 하드코딩 | P1 | **stale** | git 고증 결과 200K 파라미터 부재 — R1 오보 |
| P1-5: CW context와 Stage4 budget 간 mismatch | P1 | **persists** (범위 확대) | CW + Director 양쪽 모두 동일 budget mismatch |

| 분류 | 건수 |
|------|------|
| resolved (코드 수정 검증) | 0 |
| stale (R1 오보) | 1 (P1-4) |
| persists (여전히 존재) | 3 (P1-1, P1-2, P1-3) |
| absorbed (다른 finding에 병합) | 1 (P1-5 → P1-1에 흡수, Director 경로 포함) |
| worsened | 0 |
| new | 0 |

---

## 3. Current Ownership / Flow Map

R1의 소유권 맵은 여전히 유효하다. 변경 없음.

```
Stage 4 Episode Production:
  stage4_orchestrator.py                  # DI context 주입, mandatory_context budget 적용
    └─ stage4_context_builder.py          # 3-tier context 수집 + retrieval plan 실행
        ├─ stage4_context_packets.py      # CP(Continuity Packet), World State condensed, FactLedger
        └─ context_advisor.py             # Retrieval plan 생성 + budget 할당
    └─ stage4_interview_round.py          # round-level context 조립 → CW/Director에 전달
        ├─ chief_writer_context.py        # CW 프롬프트 조립 (build_common_context)
        │   └─ chief_writer_context_packets.py  # digest, guard, HUD, prev_manuscripts 패킷
        └─ stage4_director_runtime.py     # Director context 조립 (run_pre_director_validation)
            └─ director_ensemble.py       # ensemble selection + audit context 조립
```

Budget Authority Chain (변경 없음):
```
MAX_CONTEXT_CHARS = 1,000,000 (validation.yaml SSOT)
  └─ BaseAgent._apply_prompt_size_gate()   # 최종 안전 게이트 (ask() 전)

Per-Stage Budget (validation.yaml):
  stage4_total_budget = 300,000
  director_total_budget = 300,000
  mandatory_context_max = 400,000
```

---

## 4. Focus-Scope Findings

### Persisting P1 — 3건

#### P1-1. CW + Director prev_manuscripts 기본 smart_truncate (중간 화 소실 위험)
- **file:line**: `chief_writer_context_packets.py:158`, `director_ensemble.py:748`
- **evidence type**: source
- **fix type**: `contract-cleanup`
- **현상**: 양쪽 모두 `smart_truncate(prev_manuscripts_text)` — 기본값 `max_chars=1,000,000`, `head_chars=80,000`. 200화 프로젝트(1M자)에서 head 80K + tail 920K 구간만 보존, 중간 에피소드 통째 소실.
- **R2 추가 발견**: R1은 CW만 지적했으나, Director ensemble도 동일 패턴. Director의 200K 한도 주장(R1 P1-4)은 stale이었으므로, Director도 동일한 1M default budget mismatch에 노출.
- **root-causal**: yes (장기연재 한정)
- **blocks rerun**: no — 4-10화 범위에서 발현 불가

#### P1-2. head/tail 고정 비율 0.55 — 에피소드 경계 무시
- **file:line**: `stage4_context_builder.py:125`
- **evidence type**: source
- **fix type**: `contract-cleanup`
- **현상**: `_fit_context_text`의 head_ratio=0.55 고정. 에피소드 경계(`=== EP N ===`) 인식 없이 char 수 기준 절삭.
- **R2 변화**: 없음
- **root-causal**: yes (장기연재 한정)
- **blocks rerun**: no

#### P1-3. Budget 초과 시 Continuity Packet / World State 비보호
- **file:line**: `stage4_context_builder.py:1144,1164-1170`
- **evidence type**: source
- **fix type**: `contract-cleanup`
- **현상**: `_apply_context_budget` 보호 대상은 `[작품 추적 슬롯 요약]`과 `[SC:arc_semantic_carryover]`뿐. Continuity Packet과 World State condensed header는 일반 섹션과 동일하게 압축됨.
- **R2 변화**: 없음. Emergency trim ratio 0.68 경로(`stage4_context_builder.py:1214`)도 여전히 존재.
- **root-causal**: yes (budget 초과 시 한정)
- **blocks rerun**: no — fresh run에서 budget 사용률 < 1%

### Stale — 1건

#### P1-4. Director ensemble prev_manuscripts "200K 하드코딩" (R1 오보)
- **R1 주장**: `director_ensemble.py:729` — `smart_truncate(prev_manuscripts_text, max_chars=200000, head_chars=110000)`
- **R2 검증**: live code(`director_ensemble.py:748`)와 git 고증(`a3b9a286`, `ea8a597b` 커밋) 모두 `smart_truncate(prev_manuscripts_text)` — explicit params 부재. **200K/110K 파라미터는 코드에 존재한 적 없음.**
- **판정**: stale — R1 오보. 실제 Director는 CW와 동일하게 default(1M/80K)를 사용. 이 발견은 P1-1에 흡수됨(양쪽 동일 패턴).

### Absorbed — 1건

#### P1-5. CW context와 Stage4 budget 간 mismatch
- **R1 주장**: CW의 prev_manuscripts가 1M default인데 stage4_total_budget은 300K — 두 게이트 사이 조율 부재
- **R2 판정**: P1-1에 흡수. P1-4가 stale로 판명되면서, CW와 Director 양쪽 모두 동일한 budget mismatch 패턴임이 확인됨. P1-1의 범위를 "CW + Director 양쪽"으로 확장하여 P1-5를 별도 항목으로 유지할 필요 없음.

---

## 5. Code-Fix Verification

커밋 79f570f2는 Q7 컨텍스트 수신 경로를 **직접 수정하지 않았다.**

79f570f2가 수정한 `director_ensemble.py` 변경사항:
- `_normalize_quality_gate_reasons`: `[:160]` 절삭 제거 → Q8 (logging max-display)
- `_build_contradiction_summary_lines`: `[:160]`, `[:120]` 절삭 제거 → Q8
- `_log_director_frame`: `_short_text()` 한도 제거 → Q8
- `_apply_final_decision`: `ep_type` forwarding 추가 → Q3 (verdict accuracy)
- score provenance `_operator_log` 추가 → Q8
- `apply_adaptive_decision` fail-closed guard → Q3
- `review_reason` `[:100]` 제거 → Q8

이 변경들은 전부 Q3/Q8 범위이며, Director에 주입되는 **context 내용물**은 변경하지 않았다.

Q7 primary scope 6개 파일 중 dirty 상태인 파일: **0개**. 전부 커밋 상태.

---

## 6. Pre-Rerun T-Report Cross-Reference

### T9: Context and Retrieval Support Factors

| T9 Finding | Q7 관련성 | R2 흡수 |
|------------|----------|---------|
| T9 P1-1: Thin vector memory at early episodes | Q6 scope (retrieval), not Q7 | 비흡수 |
| T9 P1-2: Continuity pressure vectors not reaching writer output | LLM behavioral, not context assembly | 비흡수 |
| T9 P1-3: WorldState/FactLedger not cross-checked by continuity validators | Q5 scope | 비흡수 |
| T9 P2-1: NPC 10-name cap | **Q7 scope** — `stage4_context_packets.py:39,91` | persists, absorbed as supplementary |
| T9 P2-2: Slot cap 8 | **Q7 adjacent** — `context_advisor.py:365-370` | persists, Q6 primary |
| T9 P2-3: No coverage warning for slot overflow | **Q7 adjacent** — observability gap | persists, Q6 primary |
| T9 P2-4: Embedding cache LRU no model-change signal | Q6 scope | 비흡수 |
| T9 verdict: fresh-run-before-fix: yes | Q7 판정과 일치 | 흡수 |

### Generation-Coherence Deep-Dive (Q7 section: RX-1 ~ RX-9)

| Finding | Live Code 검증 | R2 상태 |
|---------|---------------|---------|
| RX-1: Tier2 T0+T1>limit 시 미로드 | `stage4_context_builder.py:1251-1253` 확인 | persists |
| RX-2: Work focus emergency trim ratio=0.68 | `stage4_context_builder.py:1214` 확인 | persists |
| RX-3: Tier1 manuscripts_range 실패 → 빈 배열 | 구조 확인 | persists |
| RX-4: Tier2 ep당 5000자 하드캡 | 구조 확인 | persists |
| RX-5: Arc semantic carryover 미복구 | `stage4_context_builder.py:1168` carryover는 보호되지만 trim 후 미복구 | persists |
| RX-6: Tier0 insert(0) 역순 삽입 | 구조 확인 | persists |
| RX-7: NPC 10명 캡 | `stage4_context_packets.py:39,91` 확인 | persists |
| RX-8: 슬롯 간 중복 제거 없음 | 구조 확인 | persists |
| RX-9: NPC history limit=3 | 구조 확인 | persists |

**요약**: RX-1~RX-9 전부 persists. 이들은 R1 P1 finding과 중복(RX-1~RX-5)되거나 P2 수준 보완 항목(RX-6~RX-9)이다. 새로운 root-cause는 아님.

---

## 7. Fresh-Run Evidence

### projects/0_0323/ 실증 데이터

**Session log**: `projects/0_0323/logs/session_20260323_134127.log`

| 측정 항목 | 값 | 한도 | 사용률 |
|----------|-----|------|--------|
| Stage4 context budget (ep1) | 2,159자 | 300,000 | 0.72% |
| Stage4 context budget (ep2) | 2,027자 | 300,000 | 0.68% |
| Stage4 context budget (ep3) | 1,807자 | 300,000 | 0.60% |
| mandatory_context compose (ep1) | t0=220, t1=579, t2=2167, total=2,970 | 400,000 | 0.74% |
| mandatory_context compose (ep2) | t0=1258, t1=2291, t2=2037, total=5,590 | 400,000 | 1.40% |
| mandatory_context compose (ep3) | t0=1413, t1=2512, t2=1817, total=5,746 | 400,000 | 1.44% |

**절삭/압축 이벤트**: 0건
- `[SC:TRIM]`: 미발생
- `[SC:TRIM:EMERGENCY]`: 미발생
- `[TF3-H7] Prompt length gate`: 미발생
- `smart_truncate` 활성 절삭: 미발생

**슬롯 사용**:
- Stage4: 7-8 slots (cap=8에 근접하나 budget은 여유)
- Director: 1 slot
- Stage3: 3-4 slots (budget=80K)

**결론**: 4화 범위에서 context budget은 1-2% 사용. 모든 tier가 무절삭으로 주입됨. R1의 모든 P1 finding은 50+ 에피소드에서만 발현하는 구조적 위험으로 확인.

---

## 8. Root-Cause vs Symptom Classification

| Finding | Root cause or Symptom? | 발현 조건 |
|---------|----------------------|-----------|
| P1-1: prev_manuscripts 기본 1M/80K | **Root cause** (장기연재 한정) | 200+ 에피소드, 합산 1M자 초과 시 |
| P1-2: head/tail 고정 비율 0.55 | **Root cause** (long-run) | budget 초과 시 에피소드 경계 깨짐 |
| P1-3: CP/WS 비보호 | **Root cause** (long-run) | stage4 budget 초과 시 |
| RX-1~RX-5: Tier 절삭/비복구 | **Symptom** of budget pressure | budget 초과 시 |
| RX-6~RX-9: 캡/중복/순서 | **Structural limitation** | 복잡 에피소드(15+ NPC, 8+ 슬롯) |

**Q7 범위의 root cause는 모두 "budget pressure → 구조적 정보 손실" 패턴이다.** 현재 운영 범위(4-10화)에서는 budget pressure가 존재하지 않으므로 발현하지 않는다. 이는 Q7이 "long-run structural" 분류를 받은 직접적 근거이다.

---

## 9. Quick Wins

### QW-1. CW + Director prev_manuscripts에 budget-aware 상한 부여 (R1 QW-1 갱신)
- **file:line**: `chief_writer_context_packets.py:158`, `director_ensemble.py:748`
- **fix type**: `contract-cleanup`
- **현황**: 양쪽 모두 `smart_truncate(prev_manuscripts_text)` → 기본 1M
- **권고**: `smart_truncate(prev_manuscripts_text, max_chars=stage4_budget의 40% 또는 120K, head_chars=50%)`로 변경. 또는 `stage4_context_builder`의 budget meta에서 CW/Director 할당량을 계산해 전달.
- **ROI**: 중간 — 장기연재(200+ 화) 전용이나, 핵심 방어선.

### QW-2. Continuity Packet을 budget 보호 대상에 추가 (R1 QW-2 유지)
- **file:line**: `stage4_context_builder.py:1164`
- **fix type**: `contract-cleanup`
- **현황**: `protected_prefix = "[작품 추적 슬롯 요약]"` 만 보호
- **권고**: `"=== [Continuity Packet]"` prefix도 보호 목록에 추가
- **ROI**: 낮음~중간 — 현재 budget 초과 드묾. 그러나 보호 누락은 설계 결함.

### QW-3. Context budget meta에 Director 할당량 명시 (신규)
- **file:line**: `stage4_context_builder.py:1315-1326`
- **fix type**: `observability-only`
- **현황**: `_stage4_context_budget_meta`에 tier0/1/2 분리가 있으나, CW/Director 개별 할당량은 기록되지 않음
- **권고**: budget meta에 `cw_prev_manuscripts_chars`, `director_prev_manuscripts_chars` 필드 추가
- **ROI**: 낮음 — 진단 개선.

---

## 10. False Leads / Non-Causes

### 10.1 "Director 200K 하드코딩이 budget mismatch를 일으킨다" — R1 오보
R1 P1-4가 `director_ensemble.py:729`에 `max_chars=200000` 하드코딩이 있다고 주장했으나, live code와 git 고증(`a3b9a286`, `ea8a597b` 커밋)에서 해당 파라미터는 존재하지 않음. Director는 CW와 동일하게 default(1M/80K)를 사용.

### 10.2 "79f570f2의 Director 수정이 Q7에 영향을 준다" — 비적용
79f570f2의 director_ensemble.py 변경은 전부 Q3(verdict)/Q8(logging) 범위. Context injection 경로는 변경되지 않음.

### 10.3 "Fresh run에서 context truncation이 발생했다" — 미발생
Session log에서 `[SC:TRIM]`, `[TF3-H7]`, emergency trim 이벤트는 0건. Budget 사용률 1-2%.

### 10.4 "NPC 10-name cap이 fresh run에서 문제를 일으켰다" — 미발현
Fresh run의 NPC 수는 에피소드당 5-8명으로 cap(10) 미만.

---

## 11. Fresh-Run Readiness

**Fresh-run-before-fix allowed: yes**

R1에서 "no"로 판정했던 근거를 재평가한다:

| R1 근거 | R2 재평가 |
|---------|----------|
| P1-1/P1-5의 prev_manuscripts 잘림이 장기연재(30화+)에서 중간 화 소실로 이어져 모순 감지 실패를 유발 | 다음 rerun은 test scope(4-10화). 30화 이상 도달 불가. Budget 사용률 < 2% |
| fresh run에서도 재현될 수 있다 | Fresh run 0_0323에서 미재현 확인. Budget pressure 0% |

**판정 변경 근거**:
1. **T9 보고서 합치**: "No context/retrieval finding blocks the next rerun" (confidence 96%)
2. **Merge audit 합치**: Q7은 "long-run structural", rerun 후 후속으로 분류
3. **실증**: fresh run 0_0323에서 context budget 0.6-1.4% 사용, 절삭 0건
4. **범위**: 모든 P1 finding은 50+ 에피소드에서만 발현. 다음 rerun은 test scope.

**Top 3 highest-ROI remaining fixes** (Q7 범위):

1. **QW-1**: CW + Director prev_manuscripts budget-aware 상한 — 장기연재 핵심 방어선 (200+ 화 한정)
2. **QW-2**: Continuity Packet budget 보호 추가 — 설계 결함 교정 (budget 초과 시 한정)
3. **QW-3**: Context budget meta에 CW/Director 할당량 기록 — 진단 개선

**이 3건 모두 rerun을 block하지 않는다.**

---

## 12. Confidence And Limits

**Estimated confidence: 96%**

**Basis**:
- Primary scope 6개 파일 live code 검증 완료 (chief_writer_context_packets.py, stage4_context_builder.py, stage4_context_packets.py, director_ensemble.py, base_agent.py, constants.py)
- R1 P1-4 stale 판정: git 고증(`a3b9a286`, `ea8a597b` 커밋)으로 200K 부재 확인
- 79f570f2 diff 전수 확인: Q7 scope 변경 0건
- Fresh run session log(`projects/0_0323/logs/session_20260323_134127.log`) 실증: budget/tier/trim 이벤트 전수 대조
- T9 보고서(confidence 96%) 교차 검증
- Generation-coherence deep-dive RX-1~RX-9 live code 대조

**Residual limits (4%)**:
- `context_advisor.py` 전수 재독 미실시 — T9에서 확인했으므로 delta만 검증 (1%)
- 장기연재(50+) 실측 데이터 없음 — budget 초과 시 실제 동작 미검증 (2%)
- prompt_builder.py 가이드 텍스트 길이가 장기연재에서 증가할 가능성 미측정 (1%)

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope Coverage
- R2 오더가 요구하는 12개 필수 섹션 전체 작성 확인
- Primary scope 6개 파일 + fresh run logs + git diff + T9/generation-coherence 교차 참조 확인
- R1 P1-1~P1-5 전수 재검증 기록 확인
- PASS

### Pass 2. Evidence and Consistency
- P1-4 stale 판정: git 고증으로 확인, R1 evidence manifest의 `director_ensemble.py:729 | smart_truncate(max_chars=200000)` 주장과 모순 → live code가 우선
- Fresh run 실증: session log line anchor 확인 (budget 0.72%, 0.68%, 0.60%)
- 79f570f2 diff: director_ensemble.py 변경이 Q3/Q8 범위임을 diff 전수로 확인
- P1-1 범위 확대(Director 포함)와 P1-5 흡수의 논리적 일관성 확인
- PASS

### Pass 3. Recommendation and Readiness
- Fresh-run readiness 판정: R1(no) → R2(yes) 변경의 4가지 근거 명시
- QW-1~QW-3 모두 survey-only 범위 (코드 수정 제안만)
- 모든 recommendation의 fix type 명시 확인
- root-cause vs symptom 분류가 finding별로 명시됨
- PASS
