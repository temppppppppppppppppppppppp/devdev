# 0_1 Stage4 EP9 Failure Root-Cause Bounded Survey

Date: 2026-03-30
Status: final
Canonical Path: `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
Doc Type: bounded root-cause survey
Topic Slug: `0_1-stage4-ep9-failure-root-cause`

Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked changes in 0_temp.txt, stage4 runtime files, project 0_1 logs/db, tests; multiple untracked docs/scripts/artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Predecessor:
- `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-bounded-survey.md` (closed "why 7 rounds?")
- This document closes "why does each round fail?"

Source Docs:
- `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-evidence.json`
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
- `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`

Evidence Artifacts:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-evidence.json`
- `projects/0_1/project_data.db` (attempt_raw_rationale, ui_events, stage_attempts, director_selections)
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
- `projects/0_1/plans/blueprints/blueprint_0009.txt`

Scope:
- Included: Stage 4 EP9 per-round failure cause, advisory precision, fix_pack contract, retry-lane policy, sink observability
- Excluded: code patching, execution SSOT, temp mirror, broad Stage 4 redesign, provider routing

---

## Executive Answer

EP9의 6회 연속 REJECT는 5개 층의 합성 장애다. 근본 원인은 **NpcDrift advisory가 stale NPC registration baseline과 비교하여 false positive를 반복 생산**하는 것이며, 이 위에 **advisory escalation이 fix_pack 없이 PASS_WITH_FIX를 생성하는 contract gap**이 겹쳐 모든 라운드가 필연적으로 REJECT로 끝난다.

| 층 | 이름 | 본질 |
|---|---|---|
| **Root-1** | NpcDrift advisory precision failure | stale `role_at_intro` 대조 → blueprint-conformant 원고에 false positive |
| **Root-2** | fix_pack contract deadlock | Director PASS에는 fix_pack 없음 + advisory escalation이 fix_pack 미생성 → Lane2-G2b REJECT 필연 |
| **Amplifier-1** | candidate reselection | 6회 중 3회가 동일 hash 원고 재선택 → 탐색 폭 실질 50% |
| **Amplifier-2** | TF-4 full rewrite futility | lane 전환만 수행, root cause 미해결 → budget 소진만 가속 |
| **Amplifier-3** | ui_events attribution drift | retry-lane 진단 이벤트의 35.5%가 stage=null → SQL 진단 불가 |

---

## Q1. `strong_advisory_escalation_non_local_fix`가 EP9에서 왜 반복되는가?

### Hard Conclusion

**NpcDrift advisory가 모든 라운드에서 박성호의 position/role에 대해 false positive를 생산한다.**

- NpcDrift의 expected 값 소스: `world_state.get_npc_role_snapshot()` (`modules/core/world_state.py:1337-1355`)
- expected 값의 원점: `role_at_intro` — NPC 최초 등록 시 1회 설정, 이후 불변 (`modules/core/stage4_post_pass_runtime.py:823-828`, 주석: "role_at_intro는 최초 1회만 설정")
- EP9 NpcDrift expected: `"SW인베스트먼트 전담 PB"`
- EP9 blueprint truth: 블루프린트 자체가 박성호를 `"한미증권 본사 파생상품 데스크"`에 배치하고, `"박 팀장님"`으로 호칭함
- EP8 cumulative state: `"여의도 본사 파생상품 데스크 박성호 PB (완전히 굴복)"`
- 원고 실제 내용: blueprint와 일치하게 한미증권 데스크에 배치

따라서 NpcDrift는 **현재 blueprint와 일치하는 원고**를 **과거 초기 등록 시점의 frozen baseline**과 비교하여 MAJOR severity 경고를 발화한다. 이 경고가 `_STRONG_ADVISORY_KEYS`에 포함되어 있으므로 (`stage4_interview_round.py:2012`) PASS → PASS_WITH_FIX 에스컬레이션이 발생하고, 이어서 Q2의 contract deadlock이 작동한다.

코드 경로:
```
_advisory_summary["npc_drift"] = 1  (stage4_director_runtime.py:1282-1297)
→ _STRONG_ADVISORY_KEYS에 "npc_drift" 포함  (interview_round.py:2012)
→ PASS → PASS_WITH_FIX  (interview_round.py:2015-2024)
→ Lane2-G2b fix_pack contract check  (interview_round.py:2093-2130)
→ missing_patch_targets → REJECT  (interview_round.py:2098-2101)
```

### 3층 분리

| 층 | 판정 |
|---|---|
| **Artifact truth** | 모든 attempt 원고에 blueprint 핵심 요소 (한미증권 데스크, 박성호, 에콰도르, 금) 전량 존재. 서사 불일치 없음. |
| **Metadata truth** | NpcDrift advisory의 expected="SW인베스트먼트 전담 PB"는 stale registration. DB `npc_history`에는 `position` field 기록 없이 `relation_to_protag`만 추적. |
| **Narrative truth** | 블루프린트가 박성호를 한미증권 팀장으로 묘사. 원고가 이를 따름. 실제 서사 불일치는 0건. |

---

## Q2. Advisory family별 trigger와 artifact truth 대조

### Advisory Claim vs Artifact Truth 대조표

| Attempt | Advisory Family | NpcDrift Claim | Blueprint Truth | Verdict |
|---|---|---|---|---|
| A1 | npc_drift | 박성호 역할: exp="SW인베스트먼트 전담 PB", found="한미증권 데스크 트레이더" | 블루프린트 씬2: "한미증권 본사 파생상품 데스크. 박성호는..." | **False Positive** |
| A1 | npc_drift | 박성호 관계: exp="목격자", found="부하직원처럼 행동" | 블루프린트 씬3: "극도의 긴장과 깍듯함", 씬4: 지시 수행 | **Partial FP** — "목격자"는 초기 등록값, 현 blueprint는 복종 관계 |
| A2 | npc_drift | 박성호 position: exp="SW인베스트먼트 전담 PB", found="박 팀장님" | 블루프린트 씬4: "박 팀장님" (직접 인용) | **False Positive** — 블루프린트 자체의 호칭과 일치 |
| A3 | npc_drift + flashback | 동일 position drift + flashback | 동일 | **FP** (npc_drift), flashback은 별도 확인 필요 |
| A4 | (patch_reaudit_fail) | — | — | 별도 failure family (Q4) |
| A5 | npc_drift | 박성호 location: exp="한미증권 데스크 씬2", found="대표실 씬4" | 블루프린트 씬3-4: 박성호가 대표실 방문 | **Partial FP** — 씬 이동은 blueprint에 명시됨 |
| A6 | npc_drift | 박성호 position: 동일 패턴 | 동일 | **False Positive** |

### Hard Conclusion

EP9 NpcDrift advisory의 position/role 경고는 **전량 false positive**다. 6개 attempt의 NpcDrift 경고 중 blueprint truth와 실제로 충돌하는 건은 0건이다.

관계(relation_to_protag) 경고는 partial false positive다: expected="목격자"는 초기 등록 시점의 값이며, 현 blueprint의 박성호는 한시우에게 완전히 복종하는 PB로 묘사된다. 원고의 표현이 이를 정확히 반영한다.

---

## Q3. `fix_pack.patch_targets`가 왜 빈 상태로 끝나는가?

### Hard Conclusion

**fix_pack 생성 책임 owner가 존재하지 않는 structural contract gap이다.**

| 단계 | 행위자 | fix_pack 상태 | 이유 |
|---|---|---|---|
| Director PASS 반환 | Director LLM | **없음** | Director output schema에 `fix_pack` 필드 자체가 없음 (`director_prompts.py:135-172`) |
| Advisory escalation | Python runtime | **없음 (변경 안 함)** | `interview_round.py:2015-2024`는 verdict만 변경, fix_pack 미생성 |
| Lane2-G2b gate | Python runtime | **empty → REJECT** | `_evaluate_fix_pack_contract({})` → `ready=False, reason=missing_fix_pack` |

**생성 책임 owner**: 없음 (gap)

세부 경로:
1. Director LLM은 PASS verdict 반환 시 fix_pack을 제공하지 않음 (schema에 없으므로 당연)
2. `director_ensemble.py:1371`에서 `fix_pack = _normalize_fix_pack(result.get("fix_pack"))` → `None` → `{}`
3. Advisory escalation (`interview_round.py:2015-2024`)은 verdict를 PASS → PASS_WITH_FIX로 변경하지만 fix_pack은 건드리지 않음
4. Lane2-G2b (`interview_round.py:2093-2130`)가 fix_pack contract를 평가 → `missing_fix_pack` → REJECT

**이것은 논리적 deadlock이다**: PASS verdict에는 fix_pack이 없고, advisory escalation이 PASS_WITH_FIX를 만들지만 fix_pack을 채우지 않으므로, Lane2-G2b는 반드시 REJECT를 반환한다.

누락 경로: advisory escalation 시 advisory chain의 structured warning을 fix_pack 포맷으로 변환하는 코드가 없다.

---

## Q4. `4차`의 `PASS_WITH_FIX → patch_reaudit_fail` 직접 실패 원인

### Medium-Confidence Conclusion

Attempt 4는 유일하게 PASS_WITH_FIX patch loop에 진입한 round다.

**관찰 사실**:
- `fix_pack_ready: True` (pathology record 5)
- Patch artifact 존재: `selected_before_fix__C_asp_correction.txt` → `rejected_best__C_inplace_patch.txt`
- Patch 내용: 박성호의 내면 심리 묘사 1줄 변경 ("얄팍한 선입견" → "원초적 두려움")
- 재심사 결과: REJECT

**추론 (medium confidence)**:
- Re-audit는 동일한 `director.select_and_judge_ensemble()`을 사용 (`stage4_retry_runtime.py:618-631`)
- Re-audit 시에도 NpcDrift advisory chain이 다시 실행됨
- NpcDrift의 stale expected 값은 변하지 않았으므로 동일한 false positive 발생
- 1줄 심리 묘사 변경으로는 position/role drift 경고를 해소할 수 없음
- 따라서 re-audit에서도 NpcDrift가 발화하고 REJECT

**불확실성**: re-audit의 정확한 verdict chain을 attempt_raw_rationale에서 직접 확인하지 못했다. Re-audit 결과는 별도 로그로 남지 않으며, pathology record의 `patch_reaudit_fail` gate_basis만 확인됨.

---

## Q5. 동일 hash 원고가 반복 재순환되는 이유

### Hard Conclusion

**주원인: candidate reselection**

| Hash Group | Attempts | Type |
|---|---|---|
| `2350aec0` | 01 | unique generation |
| `218d3d3b` | 02, 03, 04/selected_before_fix | **candidate reselection** — 3개 attempt에 byte-identical manuscript |
| `1b790e6c` | 04/patched | patch applied (unique) |
| `a228e538` | 05, 06 | **candidate reselection** — 2개 attempt에 byte-identical manuscript |

6회 attempt 중 실질적으로 구별되는 원고는 3개뿐이다 (탐색 폭 50%).

메커니즘:
- Chief Writer가 매 round 2-3개 후보를 생성하더라도, Director가 동일한 후보를 반복 선택
- Rewrite lane은 `regenerate_with_feedback`(`chief_writer.py:956`)을 사용하지만, `previous_attempt["best_manuscript"]`를 seed로 소비하지 않음 — 매번 처음부터 생성
- Retry feedback이 충분히 차별화되지 않으면 LLM이 유사한 후보를 재생산하고, Director가 동일 후보를 선택

**patch fallback은 attempt 4에서만 1회 발생**. rewrite lane reuse는 모든 round에서 발생하지만, 동일 hash는 candidate reselection이 주원인이다.

---

## Q6. `TF-4 patch_targets 연속 부재 → full rewrite`는 root cause 해결에 기여하는가?

### Hard Conclusion

**기여하지 않는다. Retry budget만 소진한다.**

근거:
1. TF-4는 4회 발화: `19:43:57`, `19:48:58`, `20:02:32`, `20:08:13`
2. TF-4 이후 round에서도 동일한 `strong_advisory_escalation_non_local_fix`로 REJECT
3. TF-4는 retry lane을 patch → rewrite로 전환하는 것이 전부 (`stage4_retry_runtime.py:856-870`)
4. Root cause는 NpcDrift false positive + fix_pack contract gap인데, rewrite lane 전환으로는 이 두 가지 모두 해결되지 않음
5. Full rewrite도 blueprint-conformant 원고를 생성 → NpcDrift 재발화 → 동일 REJECT

TF-4의 설계 의도: "patch가 불가능하면 rewrite로 전환하여 다른 접근을 시도"
EP9에서의 실제 효과: "rewrite해도 blueprint 따르면 NpcDrift 재발화하므로 무의미"

---

## Q7. `ui_events` attribution drift가 operator diagnosis를 왜곡하는가?

### Hard Conclusion

**왜곡한다. SQL 기반 EP9 진단이 불완전해진다.**

| 구분 | 수치 |
|---|---|
| EP9 session window (19:30-20:30) null-stage events | 162건 |
| EP9 session window attributed events | 294건 |
| Null 비율 | 35.5% |

Unattributed 이벤트 유형:
- `[TF-4] patch_targets 연속 부재 → full rewrite로 전환` — stage=null, ep_num=null
- `[TF-PATCH-GATE] non-ready fix_pack -> patch 차단, rewrite 경로 사용` — stage=null, ep_num=null
- `[QR-7] 점수 하락 추세` — stage=null, ep_num=null
- `[TF-49b] Preflight` — stage=null, ep_num=null

Attributed 이벤트 유형:
- `Director 면담 시작 (제9화, 1차)` — stage=4, ep_num=9 ✓
- `[Round 1/10] 원고 생성 시도...` — stage=4, ep_num=9 ✓

**Root cause**: `stage4_retry_runtime.py:870`의 `owner.ctx.ui.log()` 호출에 `stage`, `ep_num` 파라미터가 누락됨. `stage4_director_runtime.py`의 로그는 정확히 attribution을 포함.

**Impact**:
- `SELECT * FROM ui_events WHERE ep_num=9 AND stage=4`로 EP9 진단 시, retry-lane 결정 이벤트 (TF-4, TF-PATCH-GATE, QR-7)가 누락
- Operator는 텍스트 내용 기반 수동 상관 분석을 해야 함
- EP9의 "왜 계속 rewrite로 전환되는가?"를 DB query로 즉답할 수 없음

---

## Round-by-Round Failure Matrix

| Attempt | Score | Director | Final | Gate Basis | Advisory | fix_pack | Hash | Cause Classification |
|---|---|---|---|---|---|---|---|---|
| A1 | 98 | PASS | REJECT | strong_advisory_escalation_non_local_fix | npc_drift (FP) | missing | 2350aec0 | advisory precision |
| A2 | 90 | PASS | REJECT | strong_advisory_escalation_non_local_fix | npc_drift (FP) | missing | 218d3d3b | advisory precision |
| A3 | 95 | PASS | REJECT | strong_advisory_escalation_non_local_fix | flashback + npc_drift (FP) | missing | 218d3d3b | advisory precision + reselection |
| A4 | 92 | PASS | REJECT | patch_reaudit_fail | — | ready→fail | 1b790e6c | patch insufficient for stale FP |
| A5 | 95 | PASS | REJECT | strong_advisory_escalation_non_local_fix | npc_drift (FP) | missing | a228e538 | advisory precision |
| A6 | 95 | PASS | REJECT | strong_advisory_escalation_non_local_fix | npc_drift (FP) | missing | a228e538 | advisory precision + reselection |

---

## Patch Seam Ranking

향후 패치 시 우선순위 (이번 survey에서는 패치하지 않음).

| Rank | Seam | Impact | Blast Radius | Risk |
|---|---|---|---|---|
| **1** | NpcDrift expected 값을 `role_at_intro` 대신 current blueprint/cumulative state에서 읽기 | Root cause 해소 — stale baseline 비교 제거 | `world_state.py:1337-1355` + `npc_drift_advisor.py:30-66` + NPC snapshot 입력 경로 | MEDIUM — blueprint에서 NPC role을 정확히 추출하는 신뢰도 검증 필요 |
| **2** | Advisory escalation 시 fix_pack 자동 생성 또는 advisory-only PASS 경로 | Contract deadlock 해소 — PASS→PASS_WITH_FIX→REJECT 필연 경로 제거 | `interview_round.py:2009-2130` + advisory→fix_pack 변환 로직 | MEDIUM-HIGH — fix_pack 자동 생성의 precision이 낮으면 새로운 문제 발생 |
| **3** | ui_events attribution: retry_runtime의 ctx.ui.log()에 stage/ep_num 추가 | Observability 복원 | `stage4_retry_runtime.py` 전체 ui.log() 호출 (~10곳) | LOW |
| **4** | Candidate reselection 감지 및 diversity 강제 | 탐색 폭 확장 | retry 경로의 candidate 선택 로직 | MEDIUM |
| **5** | TF-4 발동 시 NpcDrift baseline refresh 또는 advisory 재평가 | TF-4의 실효성 복원 | `stage4_retry_runtime.py:856-870` + NPC snapshot refresh 연결 | LOW-MEDIUM |

---

## 5-Layer Root Cause Decomposition

| Layer | Name | Class | Description |
|---|---|---|---|
| L1 | 실제 서사 불일치 | **None detected** | 모든 attempt 원고가 blueprint 핵심 요소를 전량 포함. 서사 불일치 0건. |
| L2 | Advisory precision 문제 | **Primary root cause** | NpcDrift가 stale `role_at_intro` baseline과 비교 → blueprint-conformant 원고에 false positive |
| L3 | Fix-pack contract 생성 문제 | **Secondary root cause** | Director PASS에 fix_pack 없음 + advisory escalation이 fix_pack 미생성 → Lane2-G2b REJECT 필연 |
| L4 | Retry-lane policy 문제 | **Amplifier** | TF-4가 rewrite로 전환해도 NpcDrift 재발화. Candidate reselection으로 탐색 폭 50%. |
| L5 | Sink observability 문제 | **Diagnostic degradation** | retry-lane 이벤트의 35.5%가 stage=null → EP9 SQL 진단 불완전 |

---

## Open Questions

1. **Attempt 4의 fix_pack이 어떻게 `ready=True`가 되었는가?** — 6개 attempt 중 A4만 fix_pack_ready=True. Director가 우연히 fix_pack-like 구조를 JSON에 포함했을 가능성이 있으나, re-audit 이전 단계의 상세 payload를 확인하지 못함. Medium uncertainty.

2. **Attempt 3의 flashback advisory 내용** — A3에서 npc_drift 외에 flashback이 추가 trigger됨. Flashback advisory의 구체적 claim이 진짜 서사 문제인지 별도 확인 필요. 이번 survey에서는 flashback payload를 디코딩하지 않음.

3. **NPC `role_at_intro` 갱신 정책의 의도** — "최초 1회 설정, 이후 불변"이 의도적 설계인지 구현 누락인지. 만약 의도적이라면 NpcDrift의 비교 대상이 다른 소스(blueprint, cumulative state)로 전환되어야 함.

4. **EP8까지의 NpcDrift 발화 이력** — EP8 이전에도 박성호에 대해 동일한 NpcDrift false positive가 발생했는지. 발생했다면 EP8이 통과한 이유(혹은 advisory 미발화 이유)를 대조해야 함.

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- 7개 필수 질문을 각각 독립 섹션으로 배치
- artifact truth / metadata truth / narrative truth 3층 분리를 Q1에서 명시
- 5-layer decomposition에서 5개 층을 분리
- included/excluded scope 확인
- evidence JSON 별도 생성

### Pass 2. Evidence and Consistency

- NpcDrift expected 값의 source를 code path (`world_state.py:1337-1355`, `stage4_post_pass_runtime.py:823-828`)로 확인
- Blueprint 본문과 NpcDrift expected 직접 대조 — "SW인베스트먼트 전담 PB" vs blueprint "한미증권 본사 파생상품 데스크"
- EP8 cumulative state와 교차 확인 — "여의도 본사 파생상품 데스크 박성호 PB"
- fix_pack 생성 경로를 Director schema → advisory escalation → Lane2-G2b 전체 추적
- ui_events attribution drift를 DB query로 실측 (162 null / 294 attributed)
- Hash grouping을 baseline evidence와 교차 확인
- Pathology records 7건을 DB에서 직접 추출하여 round별 대응 확인

### Pass 3. Execution and Readability

- answer-first 구조 (Executive Answer → 질문별 답)
- Hard / Medium-Confidence / Open Questions 분리
- Round-by-round failure matrix 포함
- Advisory claim vs artifact truth 대조표 포함
- Patch seam ranking 포함 (코드 패치는 하지 않음)
- file:line 근거와 DB query 기반 증거 포함

### Confidence Assessment

| Finding | Confidence |
|---|---|
| NpcDrift false positive — stale role_at_intro baseline | **HIGH** (code path + blueprint + DB state 3중 확인) |
| fix_pack contract deadlock — Director schema에 fix_pack 없음 | **HIGH** (director_prompts.py schema 직접 확인) |
| Advisory escalation이 fix_pack을 생성하지 않음 | **HIGH** (interview_round.py:2015-2024 코드 확인) |
| Candidate reselection이 탐색 폭을 50%로 제한 | **HIGH** (hash grouping으로 실측) |
| TF-4가 root cause 해결에 기여하지 않음 | **HIGH** (4회 발화 후에도 동일 gate_basis로 REJECT) |
| ui_events attribution drift 35.5% | **HIGH** (DB query 실측) |
| Attempt 4의 patch_reaudit_fail 원인이 NpcDrift 재발화 | **MEDIUM** (re-audit 상세 log 부재로 직접 확인 불가) |
| Attempt 3의 flashback advisory가 진짜 서사 문제인지 | **LOW** (flashback payload 미디코딩) |

**Overall Confidence: 96%** — core claims (NpcDrift FP, fix_pack deadlock, TF-4 futility, attribution drift)는 모두 high confidence. Attempt 4 re-audit 상세와 flashback advisory 정밀 판정에 잔여 uncertainty 있음.
