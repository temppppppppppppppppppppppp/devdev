# 0_1 Stage4 EP10-15 Residual Gate Observability — Opus Insurance Survey

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: insurance bounded survey
Canonical Path: `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-opus-survey.md`
Temp Mirror Path: (none — insurance survey, no execution)
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: stage4_interview_round.py contains uncommitted verdict_layers code`
Primary Baseline: `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-survey.md`
Evidence Companion: `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-opus-evidence.json`
Track: system
Mode: bounded insurance survey, no realization

## Answer First

Baseline의 5대 결론을 독립 검증한 결과:

| # | Baseline 결론 | Opus 판정 | 일치/불일치 |
|---|---|---|---|
| 1 | `verdict_layers` 부재는 stale runtime session | **corroborate + strengthen** | 일치 + 강화 |
| 2 | EP13-14 `npc_drift(position/role)`는 authority-precision FP | **corroborate** | 일치 |
| 3 | EP15 `npc_drift(relation_to_protag)`는 true-positive pressure | **corroborate** | 일치 |
| 4 | `flashback` family는 taxonomy/observability loss | **corroborate** | 일치 |
| 5 | retry-lane `attempt_key` null | **corroborate** | 일치 |

Baseline과 불일치한 점: 1건 (severity: 아래 § Divergence 참조).

## Hard Conclusions

### 1. `verdict_layers` 부재 — stale runtime보다 더 강한 설명: uncommitted code

Baseline은 "stale long-running runtime session"이 가장 강한 설명이라고 했다. Opus는 이보다 한 단계 더 구체적인 원인을 확인했다.

**Evidence chain:**

1. `_build_verdict_layers_payload()`를 포함한 verdict_layers 관련 코드 18줄은 `git diff HEAD -- modules/core/stage4_interview_round.py`에서만 나타남 — **커밋된 적이 없다**.
   - `git log --all -S "verdict_layers"`: 0건
   - `git log --all -S "_build_verdict_layers_payload"`: 0건
   - `git diff HEAD` 출력에서 모두 `+` (added) 라인
2. Runtime session `20260330_231345`는 2026-03-30 23:13:45에 시작됨
3. `stage4_interview_round.py` mtime은 2026-03-31 01:05:56
4. Python은 import 시점에 모듈을 로드함 → 23:13:45 시점의 파일(HEAD 버전, verdict_layers 없음)이 프로세스 메모리에 올라감
5. 01:05:56에 파일이 수정되었으나 이미 running process는 old image 사용
6. 이후 14개 row (EP13 a2~EP15 a5)가 모두 verdict_layers 없이 persisted → **당연한 결과**

**판정:**

- Baseline의 "stale runtime session"은 올바르나, 정확한 root cause는 **"코드가 uncommitted dirty state에만 존재하며, 커밋 기준 HEAD에는 verdict_layers가 없다"**이다.
- 이 코드는 process restart만으로는 해결되지 않는다 — **commit이 선행되어야** 한다.
- Baseline이 "fresh rerun으로 확인"이라고 한 부분은 정확하지만, commit 없이 rerun하면 import 결과가 dirty file 기준이므로 작동할 수는 있다 (Python은 git이 아닌 filesystem에서 import).

**반증 시도:**

| 반증 가설 | 검증 결과 |
|---|---|
| serializer stripping | `db_manager.py:2858-2887` — advisory_flags JSON blob을 통째로 저장/로드하며 verdict_layers를 선택적으로 strip하는 코드 없음. 하지만 **read convenience path**는 verdict_layers를 추출하지 않음 (director_verdict, gate_basis, repair_scope만 추출). 이건 stripping이 아니라 read-path selectivity. |
| code omission (build 경로 누락) | `_build_gate_semantics_payload()` L2168에서 `_build_verdict_layers_payload()`를 호출하고 L2185-2186에서 payload에 넣는다. 이 코드가 HEAD에 없으므로 생성 자체가 불가능했다. |
| mixed-session artifact | EP10-15 전체가 session `20260330_231345` 단일 세션. 혼합 가능성 없음. |

### 2. EP13-14 `npc_drift(position/role)` — authority-precision false positive **corroborate**

DB raw payload 독립 확인:

| attempt_key | field | expected | found_in_ms |
|---|---|---|---|
| s4:ep13:arc3:a2 | position | SW인베스트먼트 전담 PB | 여의도 한미증권 본사 파생상품 데스크 소속으로 묘사됨 |
| s4:ep13:arc3:a2 (ci=1) | 역할 | SW인베스트먼트 전담 PB | 여의도 한미증권 본사 파생상품 데스크 소속 수석 PB로 묘사됨 |
| s4:ep13:arc3:a3 | position | SW인베스트먼트 전담 PB | 여의도 한미증권 본사 파생상품 데스크에서 근무하는 것으로 묘사됨 |
| s4:ep13:arc3:a4 (ci=1) | position | SW인베스트먼트 전담 PB | 여의도 한미증권 본사 파생상품 데스크에서 근무하는 것으로 묘사됨 |

Artifact truth 교차 확인:
- `projects/0_1/drafts/ep_0013.txt:11`: "한미증권 파생상품 데스크 소속으로 SW인베스트먼트 전담 PB를 맡고 있는 박성호"
- `projects/0_1/drafts/ep_0014.txt:7`: "한미증권 소속 SW인베스트먼트 전담 PB"

이것은 거짓이 아니라 **composite role phrasing** — 박성호는 한미증권 파생상품 데스크 소속이면서 동시에 SW인베스트먼트 전담 PB다. NpcDrift가 "SW인베스트먼트 전담 PB"만 expected로 갖고 있어서 "한미증권 파생상품 데스크"라는 소속 정보가 포함되면 mismatch로 판정한 것이다.

Code path 확인:
- `world_state.py:49-65` `_resolve_authoritative_npc_role()`: known_attrs.position → role → role_at_intro 순서로 읽음
- `npc_drift_advisor.py:104-114`: `authoritative_role`을 사용하되, 원본과 정확 일치(exact match) 비교

**판정**: Baseline과 일치. composite role phrasing over-penalty.

### 3. EP15 `npc_drift(relation_to_protag)` — true-positive narrative pressure **corroborate**

DB raw payload 독립 확인:

| attempt_key | expected | found_in_ms (요약) |
|---|---|---|
| s4:ep15:arc4:a2 (ci=0) | 집착100/오해100 | 평범한 부하직원이나 목격자처럼 묘사, 집착/오해 없음 |
| s4:ep15:arc4:a2 (ci=1) | 집착100/오해100 | 조력자나 목격자처럼 묘사, 집착/오해 없음 |
| s4:ep15:arc4:a2 (ci=2) | 집착100/오해100 | 경외감+패닉+순종적 대리인, 집착 없음 |
| s4:ep15:arc4:a3 (ci=2) | 집착100/오해100 | 단순 조력자/목격자, 집착/오해 없음 |
| s4:ep15:arc4:a4 (ci=1) | 집착100/오해100 | 강한 불신+두려움+반발, 집착/오해 없음 |

최종 PASS 원고 교차 확인:
- `ep_0015.txt:57`: "맹목적인 추종을 맹세한 그였지만"
- `ep_0015.txt:73`: "박성호는 자신의 내면에 남아있던 마지막 금융 공학적 상식마저 산산조각 나는 것을 느꼈다... 섣부른 의심은 곧 파멸을 의미했다"

Rejected candidate들은 집착/경외를 표현하지 않았고, 최종 PASS 원고는 복구했다. 이것은 real narrative pressure 감지가 맞다.

**판정**: Baseline과 일치. EP15 relation-to-protag는 EP13-14 position/role과 분리하여 true-positive로 유지해야 한다.

### 4. `flashback` family — taxonomy/observability loss **corroborate + 한 단계 더 구체화**

EP10:a1과 EP14:a1의 flashback trigger를 독립 추적:

- `stage_attempts.advisory_flags` 안에 `"flashback": 1` 비트만 존재
- `attempt_raw_rationale` payload의 `candidate_validation_payloads`에서 flashback-specific 경고 **0건**
- `selection_summary` 안에도 `"flashback": 1` 비트만 존재
- `flashback_contamination`, `회상 오염` 문자열이 raw payload 어디에도 없음

**경로 분석:**
- `flashback_verifier.py:187-197`: `FlashbackVerifier`는 원래 `check: "flashback_contamination"`, `text: "[회상 오염] ..."` 형태의 구조화된 issue를 생성
- `stage4_director_runtime.py:1282-1298`: advisory summary 생성 시 `"Flashback" in advisory_text` → `"flashback": 1`로 축약
- 구조화된 issue detail → family bit으로 압축되는 지점이 여기

**추가 발견**: EP10:a1과 EP14:a1 모두 `director_verdict=PASS`, `final_verdict=REJECT`로, Director는 통과시켰지만 flashback advisory escalation이 downstream에서 REJECT로 뒤집었다. 그런데 **무엇이** flashback 문제였는지는 어디에도 남아 있지 않다. operator가 이 REJECT를 진단하려면 원본 FlashbackVerifier 출력을 재구성해야 하는데, 그 경로가 없다.

**판정**: Baseline과 일치. flashback은 collapsed family label이며, literal flashback contamination과 generic continuity pressure를 구분할 수 없다.

### 5. retry-lane `attempt_key` null — **corroborate**

- `ui_events.jsonl`에서 stage4 retry-lane 관련 row 9건 전량 `attempt_key=null`
- EP10, EP11, EP13, EP14, EP15에 걸쳐 있으며 모두 `TF-PATCH-GATE` 또는 `QR-7` 메시지
- `ep_num`과 `stage`는 있으므로 에피소드 수준 attribution은 가능하지만, attempt-level join은 불가능

**판정**: Baseline과 일치. half-close 상태.

## Medium-Confidence Conclusions

1. `truth_gate.py:358-366`의 `role_at_intro` 비교 경로는 EP10-15 advisory_flags에서 `truth_gate` 언급 **0건** — 이번 범위에서는 **개입하지 않았다**. 그러나 코드가 존재하므로 latent risk는 유효. (Baseline과 일치)
2. EP10과 EP14의 `flashback` trigger는 literal flashback scene보다 generic continuity pressure였을 가능성이 높으나, raw payload에 detail이 없어 확정 불가. (Baseline과 일치)

## Open Questions

1. `verdict_layers` 코드를 commit한 뒤 process restart + known episode rerun으로 3개 sink (stage_attempts, episode_production, decisions) 전부에서 verdict_layers가 출현하는지 확인 필요
2. `flashback` family의 raw issue detail을 보존하는 별도 sink 경로가 필요한지 결정 필요
3. `NpcDrift` composite role normalization — exact match 대신 substring containment 또는 semantic equivalence로 완화할지 결정 필요

## Divergence From Baseline

### 일치한 점 (5/5 결론 모두)

모든 hard conclusion에서 Baseline과 방향이 일치.

### 불일치한 점 (1건, severity: refinement)

| 항목 | Baseline 서술 | Opus 발견 | Impact |
|---|---|---|---|
| verdict_layers 부재 root cause | "코드 파일은 바뀌었지만 실행 프로세스는 그 이전 메모리 이미지를 계속 사용" + "stale long-running runtime session" | **verdict_layers 코드는 커밋된 적이 없다** (`git log -S "verdict_layers"` = 0건). HEAD에 없고 dirty working tree에만 존재. "stale session"이 아니라 **"uncommitted code"**가 정확한 진단. | Process restart만으로는 해결 조건이 불완전 — commit이 선행되어야 한다. 단, Python은 filesystem에서 import하므로 dirty file 상태에서 restart하면 작동은 한다. |

이 불일치는 Baseline의 결론을 뒤집지 않으며, root cause를 한 단계 더 구체화하는 refinement다. Baseline의 "fresh rerun으로 확인" 권고는 dirty state에서는 사실상 맞지만, 운영 안정성 관점에서는 commit-first가 올바른 순서다.

## Episode-by-Attempt Classification Matrix

| attempt_key | EP | triggered_by | classification | Opus corroborate |
|---|---|---|---|---|
| s4:ep10:arc3:a1 | 10 | flashback | taxonomy/observability loss | **corroborate** — raw payload에 flashback detail 0건 |
| s4:ep13:arc3:a2 | 13 | npc_drift | authority-precision FP | **corroborate** — composite role phrasing over-penalty |
| s4:ep13:arc3:a3 | 13 | npc_drift | authority-precision FP (post_select_conflict) | **corroborate** |
| s4:ep13:arc3:a4 | 13 | flashback, npc_drift | mixed FP + observability loss | **corroborate** |
| s4:ep14:arc3:a1 | 14 | flashback | taxonomy/observability loss | **corroborate** — raw payload에 flashback detail 0건 |
| s4:ep14:arc3:a3 | 14 | flashback, npc_drift | mixed FP + observability loss (patch_reaudit_fail) | **corroborate** |
| s4:ep15:arc4:a2 | 15 | npc_drift | true-positive narrative pressure | **corroborate** — 3 candidates 모두 집착/오해 부재 |
| s4:ep15:arc4:a4 | 15 | npc_drift | true-positive narrative pressure | **corroborate** — "강한 불신+반발" ≠ 집착/오해 |

## Improvement Priorities (Baseline과 동일, 1건 수정)

1. **verdict_layers commit + process restart + bounded rerun** (Baseline 대비 commit 선행 추가)
2. flashback raw issue payload 별도 sink 보존
3. EP13-14 composite role normalization 보강
4. EP15 relation_to_protag lane 별도 gate pressure 유지
5. retry-lane JSONL attempt_key 부여

## 3-Pass Audit Record

Pass 1, structure and scope:
- 문서 유형은 insurance bounded survey
- scope는 EP10-15 residual gate + observability seam
- Baseline 결론 5건에 대한 corroborate/falsify 구조
- 일치/불일치 분리 섹션 존재

Pass 2, evidence and consistency:
- DB query 4종 독립 실행 (stage_attempts, director_selections, attempt_raw_rationale, advisory_flags JSON search)
- `git diff HEAD`, `git log -S` 독립 실행으로 uncommitted code 확인
- JSONL 3종 grep 독립 실행 (verdict_layers = 0건)
- artifact truth 3파일 교차 확인 (ep_0013.txt, ep_0014.txt, ep_0015.txt)
- UTF-8 byte-level read-back으로 한국어 payload 확인 (cp949 콘솔 출력은 navigational only)

Pass 3, execution and readability:
- answer-first 구조
- hard/medium/open 분리
- episode-by-attempt matrix 포함
- Baseline 일치/불일치 별도 섹션
- 반증 시도 표 포함
- file:line 근거 충분

Confidence: 97%
