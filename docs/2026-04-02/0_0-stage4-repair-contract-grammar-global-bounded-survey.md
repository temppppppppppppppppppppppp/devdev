# Stage4 Repair-Contract Grammar Global Bounded Survey

Date: 2026-04-02
Status: final (3-pass audit complete, confidence >= 95%)
Baseline Commit: `aaf495d6`
Scope: Stage4 repair-contract grammar — field lifecycle from detector emission to operator-visible sink
Evidence: `docs/2026-04-02/0_0-stage4-repair-contract-grammar-global-evidence.json`

---

## Answer-First Summary

**Stage4 repair-contract grammar는 canonical grammar가 아니라 family별 ad hoc 구조의 집합이다.**

각 detector/advisor가 자체 필드 이름으로 emission하고, interview_round가 중간에 새 필드를 backfill/synthesize하며, reject_runtime이 또 다른 이름으로 transform한다. Operator-visible sink(runtime evidence JSON)에 도달하는 시점에서는 구조화된 repair contract 필드가 **전량 탈락**하고, 문자열 설명(dominant_blocker, blockers)과 경고 코드(advisory_warnings)만 남는다.

**가장 큰 contract drift 3개:**
1. **Subtype 이름 파편화**: `contradiction_subtype` (flashback) / `drift_subtype` (NPC) / `subtype` (interview normalization) / `contradiction_types` (conflict_contract) — 4개 이름
2. **Operator sink 블랙아웃**: 52개 고유 필드 중 0개가 operator-visible JSON에 구조적으로 도달
3. **fix_scope 권한 침식**: Director의 `authoritative_fix_scope`가 runtime widening으로 routinely override되지만, 원본 scope가 operator output에 보존되지 않음

**공통 grammar 최소 field set (승격 후보 12개):**

| Field | Type | 역할 |
|-------|------|------|
| `check` | str | family identifier |
| `severity` | str | 강도 (현재 항상 MAJOR) |
| `text` | str | human-readable 설명 |
| `subtype` | str | 하위 분류 (통합 이름 필요) |
| `target_kind` | str enum | 수리 범위 종류 |
| `expected_truth` | str | 기대 사실 (통합 이름 필요) |
| `local_fixable` | bool | 로컬 수리 가능 여부 |
| `patch_targets` | list[str] | 수리 대상 위치 |
| `must_fix` | list[str] | 필수 수정 사항 |
| `fix_scope` | str enum | 수리 범위 (inplace/partial/full) |
| `provenance` | str enum | 출처 (director/runtime) |

**Execution SSOT 승격 가치: 있음** — 단, 현재 sink 블랙아웃 문제가 해소되어야 실질적 의미가 있다.

---

## 1. Emission Axis — Detector/Advisor 출력 Grammar

### 1.1 FlashbackVerifier (`modules/core/flashback_verifier.py`)

**항상 출력 (6 fields):**

| Field | Type | Source | Value |
|-------|------|--------|-------|
| `marker` | str | LLM | 플래시백 마커 텍스트 |
| `issue` | str | LLM | 문제 설명 |
| `referenced_context` | str | LLM | 참조된 컨텍스트 |
| `severity` | str | hardcoded | "MAJOR" |
| `check` | str | hardcoded | "flashback_contamination" |
| `text` | str | derived | marker + issue 결합 |

**조건부 출력 (6 fields):**

| Field | Type | Source | 조건 |
|-------|------|--------|------|
| `contradiction_subtype` | str | LLM | 존재 + 비공백 시 |
| `local_fixable` | bool | LLM | bool 정규화 성공 시 |
| `patch_anchor` | str | LLM | 존재 + 비공백 시 |
| `expected_truth` | str | LLM | 존재 + 비공백 시 |
| `local_fix_hint` | str | LLM | 존재 + 비공백 시 |
| `target_kind` | str | LLM | whitelist(`local_phrase`, `local_sentence`) 일치 시 |

### 1.2 NpcDriftAdvisor (`modules/core/npc_drift_advisor.py`)

**항상 출력 (7 fields):**

| Field | Type | Source | Value |
|-------|------|--------|-------|
| `npc` | str | LLM | NPC 이름 |
| `field` | str | LLM | 변경된 필드명 |
| `expected` | str | LLM | authoritative 기대값 |
| `found_in_ms` | str | LLM | 원고에서 발견된 값 |
| `severity` | str | hardcoded | "MAJOR" |
| `check` | str | hardcoded | "npc_drift" |
| `text` | str | derived | npc + field + found_in_ms 결합 |

**조건부 출력 (4 fields, relation_to_protag 케이스 전용):**

| Field | Type | Source | 조건 |
|-------|------|--------|------|
| `drift_subtype` | str | hardcoded | "relation_tag_semantic" |
| `target_kind` | str | hardcoded | "local_phrase" |
| `expected_relation_axes` | list[str] | derived | relation tag 토큰 파싱 |
| `semantic_local_fix_hint` | str | derived | 템플릿 생성 |

### 1.3 ImmutableFactContract (`modules/core/stage4_immutable_fact_contract.py`)

Repair contract 필드를 **출력하지 않음**. 인프라 전용 모듈:
- violation family 분류 (키워드 → family 문자열)
- escalation 결정 로직
- actor reference 정규화

### 1.4 Emission Grammar 진단

**핵심 문제: Detector 간 필드 이름 불일치**

| 의미 | Flashback 이름 | NPC Drift 이름 | 비고 |
|------|---------------|---------------|------|
| 하위 유형 | `contradiction_subtype` | `drift_subtype` | 통합 필요 |
| 기대값 | `expected_truth` | `expected` | 통합 필요 |
| 수리 힌트 | `local_fix_hint` | `semantic_local_fix_hint` | 통합 필요 |
| 수리 가능 여부 | `local_fixable` | (없음) | NPC는 target_kind로 대체 |
| 수리 앵커 | `patch_anchor` | (없음) | Flashback 전용 |

`severity`, `check`, `text`, `target_kind`만 양 detector에서 이름이 동일하다.

---

## 2. Routing Axis — Interview/Retry/Reject 변환 Grammar

### 2.1 Interview Round (`stage4_interview_round.py`)

**Detector 필드 소비 + 새 필드 생성:**

| 동작 | Field | Line 범위 | 비고 |
|------|-------|----------|------|
| CONSUME | `local_fixable` | ~2173 | `False` → fix_pack에서 제외 (gating) |
| CONSUME | `contradiction_subtype` | ~2137 | subtype 추론 입력 |
| CONSUME | `patch_anchor` | ~2229 | patch_targets 레이블링 |
| CONSUME | `expected_truth` | ~234 | fallback으로 `referenced_context` 사용 |
| INFER | subtype | ~2140-2154 | 텍스트 휴리스틱으로 6종 추론 |
| NORMALIZE | `target_kind` | ~1957-2004 | 단수/복수 통합, whitelist 검증 |
| CREATE | `conflict_contract` | ~127-187 | post-select conflict 감지 시 |
| CREATE | `patch_targets` | ~2055 | 필수, 없으면 backfill (~2382) |
| CREATE | `must_fix` | ~2056 | 필수, 없으면 backfill (~2391) |
| CREATE | `do_not_regress` | ~2057 | 필수 |
| CREATE | `success_condition` | ~2058 | 필수 |
| CREATE | `evidence_summary` | ~2062 | 선택 |
| STAMP | `provenance` | ~1931 | `director_authored` / `runtime_synthesized` / `runtime_backfilled` |
| STAMP | `provenance_sources` | ~1932 | advisory class 목록 |
| EXTRACT | `fix_scope` | ~2010 | `inplace`/`partial`/`full` |
| EXTRACT | `authoritative_fix_scope` | ~2496 | Director 원본, blank → violation |

**Critical Gates:**

| Gate | Field | 조건 | 결과 |
|------|-------|------|------|
| G1 | `local_fixable` | `False` | fix_pack 항목 제외 |
| G2 | `target_kind` | `scene_model` | contract 거부 |
| G3 | `fix_scope` | `!= inplace` | PASS_WITH_FIX 불가 |
| G4 | `authoritative_fix_scope` | blank/invalid | PASS_WITH_FIX → REJECT 강제 |

### 2.2 Retry Runtime (`stage4_retry_runtime.py`)

**소비 전용, 새 필드 생성 없음.** Validation gate로 동작:

| Gate | Field | 조건 | 효과 |
|------|-------|------|------|
| V1 | `fix_scope` | `== inplace` | patch 경로 허용 |
| V2 | `provenance` | `runtime_*` | patch 선호 (director는 bypass) |
| V3 | `target_kind` | local set 내 | patch 허용 |
| V4 | `contradiction_types` | continuity subset | bounded retry 허용 |

### 2.3 Reject Runtime (`stage4_reject_runtime.py`)

**새 필드 생성 + scope 변환:**

| 동작 | Field | 비고 |
|------|-------|------|
| CREATE | `resolved_fix_scope` | Director scope + runtime escalation 합산 |
| CREATE | `resolved_fix_scope_reasoning` | 누적 정당화 텍스트 |
| CREATE | `resolved_fix_pack` | 조건부 보존 또는 초기화 |
| CREATE | `fix_pack_origin` | `{provenance, provenance_sources, routing_contract}` |
| CREATE | `scope_origin` | 각 scope 필드의 설정 주체 추적 |
| CREATE | `retry_budget_axes` | `{repair, strategy, escalation, guidance}` |

**Scope Escalation 변환:**

| 원본 | 결과 | 조건 |
|------|------|------|
| `inplace` | `partial` | violation family + empty patch_targets |
| `any` | `full` | post_select_conflict |
| `inplace` | `partial` | ready contract 없음 |

---

## 3. Finalization Axis — Post-Select/Post-Pass Grammar

### 3.1 Post-Pass Runtime (`stage4_post_pass_runtime.py`)

**Repair contract 필드 전량 부재.**

Interview/reject 단계의 `patch_targets`, `must_fix`, `fix_scope`, `provenance`, `conflict_contract` 등이 post-pass 단계에 전혀 전파되지 않는다.

대신 별도 grammar인 `state_truth_owner_contract`가 존재:
- `contract_version`: "stage4_state_truth_owner_contract_v1"
- `actual_truth_primary_owner`: "none" | "manager_actual_truth" | "director_state_updates_fallback"
- `actual_truth_fallback_used`: bool
- `field_families`: dict (6종 family, 각각 owner/surfaces/fields 포함)

이 contract는 episode_bible DB + state_log DB에 직접 sink된다.

### 3.2 Post-Processor (`stage4_post_processor.py`)

Repair contract 필드 전량 부재. 최종 포매팅 및 artifact 저장 전용.

### 3.3 Finalization Grammar 진단

Post-pass/post-processor는 **repair grammar와 별도 도메인**에서 동작한다. Interview/reject 단계의 repair contract는 verdict 결정까지만 살아있고, PASS 확정 후에는 state ownership grammar로 전환된다. 이 전환 경계에서 repair 메타데이터가 전량 소실된다.

---

## 4. Sink Axis — Operator-Visible Output Grammar

### 4.1 Runtime Evidence JSON에 도달하는 필드

| Field | Type | 출처 |
|-------|------|------|
| `round` | int | round counter |
| `mode` | str | ensemble mode |
| `candidates` | int | ensemble size |
| `selected` | str | candidate id |
| `score` | int | quality score |
| `initial_verdict` | str | pre-advisory verdict |
| `gate` | str | gate type |
| `final_verdict` | str | post-fix verdict |
| `post_fix_verdict` | str | conditional |
| `dominant_blocker` | str | 문자열 설명 |
| `blockers` | list[str] | 경고 코드 목록 |
| `advisory_warnings` | list[str] | advisory 코드 목록 |

### 4.2 Runtime Evidence JSON에 도달하지 않는 필드 (52개 중 전량)

Repair contract의 모든 구조화된 필드:
`patch_targets`, `must_fix`, `fix_scope`, `provenance`, `conflict_contract`, `contradiction_types`, `contradiction_details`, `target_kind`, `expected_truth`, `local_fixable`, `authoritative_fix_scope`, `resolved_fix_scope`, `fix_pack_origin`, `scope_origin`, `retry_budget_axes`, `strong_advisory_escalation`, `do_not_regress`, `success_condition`, `evidence_summary` 등

### 4.3 Naming Inconsistency

| 의미 | focused-bounded canary | demo-run | 비고 |
|------|----------------------|----------|------|
| 최종 판정 | `final_verdict` | `verdict` | 동일 개념, 다른 이름 |
| 차단 요인 | `dominant_blocker` | `blockers` (list) | 동일 개념, 다른 구조 |

### 4.4 Sink Grammar 진단

**Operator sink는 repair contract grammar와 완전히 분리되어 있다.** Detector → interview → reject 경로에서 생산된 52개 이상의 구조화된 필드 중 0개가 operator JSON에 구조적으로 도달한다. Operator는 문자열 설명과 경고 코드만으로 repair 상태를 추론해야 한다.

---

## 5. Cross-Cut: 필드 이름 파편화 전수 목록

### 5.1 동일 개념 — 다수 이름

| 의미 | 이름 변종 | 모듈 |
|------|----------|------|
| 하위 유형 | `contradiction_subtype`, `drift_subtype`, `subtype` (inferred), `contradiction_types` (list) | flashback, npc_drift, interview, conflict_contract |
| 기대값 | `expected_truth`, `expected`, `referenced_context` (fallback) | flashback, npc_drift, interview |
| 수리 힌트 | `local_fix_hint`, `semantic_local_fix_hint`, `bounded_local_fix_hint` | flashback, npc_drift, conflict_contract |
| 수리 범위 | `fix_scope`, `authoritative_fix_scope`, `resolved_fix_scope`, `repair_scope` | interview, reject |
| 출처 | `provenance`, `fix_pack_provenance` (alias), `backfilled_from` (alias), `provenance_sources` | interview, reject |

### 5.2 통합 이름 후보

| 현재 변종 | 제안 통합 이름 | 비고 |
|----------|-------------|------|
| `contradiction_subtype` / `drift_subtype` | `subtype` | interview에서 이미 이 이름으로 추론 |
| `expected_truth` / `expected` | `expected_truth` | flashback이 더 명시적 |
| `local_fix_hint` / `semantic_local_fix_hint` / `bounded_local_fix_hint` | `local_fix_hint` | 가장 짧고 보편적 |
| `fix_scope` / `authoritative_fix_scope` / `resolved_fix_scope` | 유지 (의미 구분 필요) | 3단계 scope는 의도적 |
| `provenance` / `provenance_sources` / `backfilled_from` | `provenance` + `provenance_sources` | alias 제거만 |

---

## 6. 필수 질문 답변

### Q1. Stage4 repair contract의 canonical grammar는 존재하는가?

**존재하지 않는다.** Family별 ad hoc 구조의 집합이다.

증거:
- FlashbackVerifier: 12 fields, 자체 이름 체계
- NpcDriftAdvisor: 11 fields, 자체 이름 체계
- Interview: 20+ fields 새로 생성, detector 필드 이름 일부 그대로, 일부 변환
- Reject: 10+ fields 또 새로 생성
- 공통 이름은 `severity`, `check`, `text`, `target_kind` 정도

### Q2. 어떤 field가 detector에서 생기고, 어떤 field가 interview/retry/reject에서 backfill/synthesize 되는가?

**Detector 생성 (authoritative):**
- `marker`, `issue`, `referenced_context` (flashback)
- `npc`, `field`, `expected`, `found_in_ms` (NPC drift)
- `severity`, `check`, `text` (both)
- `contradiction_subtype` / `drift_subtype` (각자)
- `local_fixable`, `patch_anchor`, `expected_truth`, `local_fix_hint` (flashback)
- `target_kind` (both, 다른 값 집합)

**Interview backfill/synthesize:**
- `patch_targets`, `must_fix`, `do_not_regress`, `success_condition` — detector가 제공하지 않으면 runtime이 생성
- `provenance`, `provenance_sources` — runtime stamp
- `conflict_contract` — post-select conflict 시 새로 생성
- `fix_scope`, `authoritative_fix_scope` — Director verdict에서 추출
- `strong_advisory_escalation` — advisory gate 시 새로 생성

**Reject synthesize:**
- `resolved_fix_scope` — Director scope + runtime escalation 합산
- `fix_pack_origin` — provenance 재포장
- `scope_origin` — meta-tracking
- `retry_budget_axes` — routing 결정

### Q3. 어떤 field가 operator-visible sink까지 살아남는가?

**0개.** 구조화된 repair contract 필드는 전량 탈락.

Operator JSON에 도달하는 것:
- `gate` (str) — repair 경로의 간접적 흔적
- `advisory_warnings` (list) — 어떤 advisory가 발화했는지
- `dominant_blocker` / `blockers` — 문자열 설명
- `post_fix_verdict` — fix 시도 결과

이들은 repair contract의 **그림자**이지 contract 자체가 아니다.

### Q4. authoritative와 runtime_synthesized의 경계는 어디서 흐려지는가?

3곳에서 흐려진다:

1. **Interview backfill** (~2382-2403): Director가 fix_pack을 제공하지 않으면 runtime이 `patch_targets`, `must_fix`를 synthesize. `provenance` 필드로 구분하지만, 이 provenance가 operator sink에 도달하지 않음.

2. **Reject scope escalation** (~606-648): Director의 `authoritative_fix_scope: inplace`가 runtime에 의해 `partial` 또는 `full`로 widening. `scope_origin` 메타데이터로 추적하지만, 이것도 operator sink에 도달하지 않음.

3. **Retry provenance gate** (~135): runtime-synthesized fix_pack은 patch 경로를 선호하지만, director-authored와의 구분이 operator에게 보이지 않음.

결론: **코드 내부에서는 authoritative/runtime 경계가 유지되지만, operator-visible 표면에서는 완전히 소실된다.**

### Q5. 공통 grammar로 승격할 최소 field set은?

**Tier 1 — 양 detector 공통, 즉시 통합 가능 (4 fields):**
- `check` (family identifier)
- `severity` (강도)
- `text` (human-readable)
- `target_kind` (수리 범위 종류)

**Tier 2 — 이름 통합 후 공통화 가능 (4 fields):**
- `subtype` ← `contradiction_subtype` / `drift_subtype` 통합
- `expected_truth` ← `expected_truth` / `expected` 통합
- `local_fix_hint` ← 3종 변종 통합
- `local_fixable` ← flashback에만 있지만 NPC도 동일 개념 필요

**Tier 3 — Interview/reject 단계 공통 (3 fields):**
- `patch_targets`
- `must_fix`
- `fix_scope`

**Tier 4 — Provenance (통합 후 sink 전파 필요) (1 field):**
- `provenance`

최소 12 fields (Tier 1: 4 + Tier 2: 4 + Tier 3: 3 + Tier 4: 1).

### Q6. Execution SSOT로 올릴 가치가 있는가?

**있다.** 단, 조건부.

승격 가치가 있는 이유:
- 현재 4개 이름 변종이 유지보수 비용을 발생시킴
- Operator sink 블랙아웃으로 인해 runtime 행동의 진단 가능성이 낮음
- 5개 기존 execution SSOT가 각각 부분적으로 이 grammar를 참조하지만, 공통 정의를 공유하지 않음

승격 전 선행 조건:
1. Operator sink에 최소 `provenance` + `fix_scope` + `subtype`가 구조적으로 도달하도록 sink 경로를 확인해야 함
2. 이름 통합 (5.2절)이 합의되어야 함
3. 통합된 grammar가 기존 5개 execution SSOT와 충돌하지 않는지 확인 필요

---

## Hard Conclusions (Confidence >= 95%)

1. **Stage4 repair-contract canonical grammar는 존재하지 않는다.** Family별 ad hoc 구조의 집합이다.
2. **Operator-visible sink에 repair contract 필드가 0개 도달한다.** 이것은 설계적 gap이다.
3. **Subtype 이름이 4종으로 파편화**되어 있다: `contradiction_subtype`, `drift_subtype`, `subtype`, `contradiction_types`.
4. **fix_scope가 4종으로 파편화**되어 있다: `fix_scope`, `authoritative_fix_scope`, `resolved_fix_scope`, `repair_scope`. 이 중 3종(`fix_scope`, `authoritative_fix_scope`, `resolved_fix_scope`)은 의미적으로 구분되지만, `repair_scope`는 `fix_scope`의 단순 복사본이다.
5. **Expected-truth 필드 이름이 2종**(`expected_truth`, `expected`)으로 다르다.
6. **Fix-hint 필드 이름이 3종**으로 다르다.
7. **Provenance 추적은 코드 내부에서 정상 동작**한다 (`director_authored` / `runtime_backfilled` / `runtime_synthesized`).
8. **ImmutableFactContract는 repair emission과 무관**한 인프라 모듈이다.
9. **Post-pass/post-processor는 repair grammar와 별도 도메인**이다.

## Medium-Confidence Conclusions (Confidence 70-94%)

1. **Sink 블랙아웃은 의도적이 아닐 가능성이 높다** — 기존 5개 execution SSOT가 모두 sink 전파를 전제로 서술되어 있지만 실제 구현은 이를 반영하지 않은 것으로 보인다. (Confidence: ~85%)
2. **`repair_scope` 필드는 제거 후보**다 — `fix_scope`의 단순 복사본으로 보이며 독립적 의미가 없다. (Confidence: ~80%)
3. **NPC drift에도 `local_fixable` 명시 필드가 필요하다** — 현재는 `target_kind` 존재 여부로 간접 추론하지만, flashback과의 일관성이 떨어진다. (Confidence: ~75%)

## Open Questions

1. **Sink 블랙아웃이 의도적 설계인가?** — Interview/reject 내부 필드를 의도적으로 operator에게 숨기는 것인가, 아니면 sink 배선 누락인가? 이 결정이 execution SSOT 범위를 결정한다.
2. **기존 5개 execution SSOT와 통합 grammar SSOT의 관계는?** — 통합 grammar SSOT가 5개를 대체하는가, 상위 참조가 되는가, 병렬 보조가 되는가?
3. **advisory chain의 다른 detector들(TruthGate, NumericDrift, InfoParadox, RelDrift, LongTermRep, NumericConsistency)도 같은 grammar 파편화를 보이는가?** — 이번 조사는 Flashback과 NPC Drift만 직접 조사했다.
4. **Retry budget axes와 repair contract grammar의 관계는?** — `retry_budget_axes`가 repair grammar의 일부인가 별도 도메인인가?
5. **`conflict_contract` 내부 `conflicts` 배열의 개별 항목 grammar는 어디서 정의되는가?** — Interview에서 텍스트 파싱으로 생성하지만 정의가 암묵적이다.

---

## 최종 보고

| 항목 | 결론 |
|------|------|
| **Stage4 repair grammar 존재 여부** | 존재하지 않음. Family별 ad hoc 집합 |
| **가장 큰 contract drift** | (1) subtype 4종 파편화, (2) operator sink 전량 블랙아웃, (3) fix_scope 권한 침식의 비가시성 |
| **공통 grammar 최소 field set** | 12 fields (check, severity, text, target_kind, subtype, expected_truth, local_fix_hint, local_fixable, patch_targets, must_fix, fix_scope, provenance) |
| **Execution SSOT 승격 여부** | **승격 가치 있음** — sink 블랙아웃 해소 + 이름 통합 합의를 선행 조건으로 |
| **다음 액션** | Operator-visible sink 배선 조사: 현재 sink에 최소 3 fields (provenance, fix_scope, subtype) 구조적 전파가 가능한지 경로 확인 |
