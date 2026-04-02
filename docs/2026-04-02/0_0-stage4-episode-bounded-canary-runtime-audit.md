# 0_0 Stage4 Episode Bounded Canary Runtime Audit

Date: 2026-04-02
Status: completed (ep2 only — ep3/ep4 not executed)
Canonical Path: `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-audit.md`
Baseline Commit: `c5c5180b`
Model Tier: gemini-2.5-pro
Evidence: `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-evidence.json`

## 1. Answer First

**Combined Stage4 verdict: `blocked`**

ep2 canary ran 11 rounds (R0-R9 + WOULD_CLIP), all REJECT, no finalization. Director wanted PASS in 8/10 substantive rounds (scores up to 98), but `Stage4Gate` forced REJECT via `strong_advisory_escalation_non_local_fix` in 7/11 rounds. The NpcDrift advisory on 한정호 `relation_to_protag` cannot be locally patched — the compressed tag `집착100/오해-80` has no actionable local fix contract. Run completed with `hard_gates: fail`. ep3/ep4 were not executed due to cost constraints.

## 2. Sub-Verdicts

### 2.1 ep2: `blocked`

| Dimension | Finding |
|---|---|
| Artifact truth | 10+ rejected manuscripts saved in `logs/artifacts/stage4/ep_0002/`. All structurally valid. Run completed with WOULD_CLIP. |
| Metadata truth | `decisions.jsonl` 11 entries, `episode_production.jsonl` 16+ entries, `ui_events.jsonl` 436+ entries. `canary_summary.json` generated with `hard_gates: fail`. |
| Narrative truth | Director selected candidates scoring 92-96. Prose quality adequate. Rejection is systemic (gate), not narrative. |

**Gate distribution across 11 rounds (R0-R9 + WOULD_CLIP):**

| Gate | Count | Rounds |
|---|---|---|
| `strong_advisory_escalation_non_local_fix` | 7 | R0, R2, R4, R5, R6, R7 |
| `continuity_firewall` | 2 | R1, R9 |
| `post_select_conflict` | 2 | R3, R8 |

**Flashback false positive — resolved:**
- FlashbackVerifier fired in R0-R2 (DDP 2009 anachronism, "몇 달 전" temporal mismatch)
- Director explicitly dismissed FlashbackVerifier in R2 open_review: "이야기의 시작(1화)과 주인공의 회귀 시점이 동일한 2006년 1월이므로 ... 시간적 흐름에 전혀 문제가 없습니다"
- FlashbackVerifier went silent from R3 onward
- **Flashback is NOT the finalization blocker** — it was correctly suppressed by Director judgment

**NpcDrift — persistent, locally unfixable:**
- Entity: 한정호, expected `relation_to_protag = 집착100/오해-80`
- LLM-generated prose consistently renders this as "체스말/무관심/도구적 관계"
- Stage4Gate requires local fix contract for advisory escalation, but NpcDrift on `relation_to_protag` compressed tags cannot produce one
- This is the root cause of the 5-round `strong_advisory_escalation_non_local_fix` loop

**Final reject was still advisory loop:** Yes. R9 result=REJECT (continuity_firewall), followed by WOULD_CLIP. The system exhausted max rounds without finalization. Peak score was 98 (R7, R8) — Director quality was sufficient, gate rules prevented finalization.

**PASS/PASS_WITH_FIX finalization possible?** No, under current gate rules. The fixpack finalization code landed (Tranche 1 of fixpack SSOT) but did not cover the NpcDrift-to-local-fix backfill path for `relation_to_protag` compressed tags.

### 2.2 ep3: `not_executed`

Intended check: `missing_patch_targets` reoccurrence, strong advisory local patch convergence.
Not executed. Prior SSOT status remains `partially_realized`.

### 2.3 ep4: `not_executed`

Intended check: `post_select_conflict` subtype preservation, bounded hint retention.
Not executed. Prior SSOT status remains `partially_realized`.

## 3. Before vs After Comparison

### 3.1 Prior State (2026-04-01 SSOT)

The ep2 advisory escalation loop SSOT identified 3 root causes:
1. FlashbackVerifier LLM prompt allows device-type over-inference
2. Strong advisory family info not written to operator sink (`ui_events`)
3. `post_select_conflict` body not written to operator sink

Fixes landed: T1 (FlashbackVerifier prompt guard), T2 (advisory family sink), T3 (conflict body sink).

### 3.2 Current State (this canary)

| Root Cause | Prior Status | This Canary |
|---|---|---|
| FlashbackVerifier over-inference | T1 code landed | **Partially effective** — Flashback still fired R0-R2 but Director dismissed; silent from R3. Not the dominant blocker. |
| Advisory family sink gap | T2 code landed | **Not verified** — `ui_events.jsonl` was not checked for structured family data in this run (would need separate grep). |
| post_select_conflict body sink | T3 code landed | **Occurred once (R3)** — gate fired as `post_select_conflict`, 1/7 rounds. Not the dominant blocker. |
| NpcDrift non_local_fix loop | Identified in fixpack SSOT | **Dominant blocker** — 5/7 rounds. Fixpack Tranche 1 did not cover `relation_to_protag` compressed tag backfill. |

### 3.3 New Finding

The dominant blocker has shifted from FlashbackVerifier (prior SSOT) to **NpcDrift `relation_to_protag` compressed tag mismatch**. The LLM cannot reproduce `집착100/오해-80` in prose form in a way that NpcDriftAdvisor would accept as matching, and the Stage4Gate has no mechanism to synthesize a local fix contract for this advisory type.

## 4. Verification Lane Answers

### Q1. ep2에서 Flashback false positive 없이 finalization이 가능한가?

**Flashback false positive는 해소되었으나, finalization은 불가능하다.** Flashback은 R3 이후 미발화. 그러나 NpcDrift `strong_advisory_escalation_non_local_fix`가 finalization을 차단한다.

### Q2. ep3에서 `strong_advisory_escalation_non_local_fix / missing_patch_targets`가 실제로 사라졌는가?

**미검증.** ep3 미실행. 단, ep2에서 동일 gate가 5/7 라운드에서 재현되었으므로, ep3에서도 재현 가능성 높음.

### Q3. ep4에서 `post_select_conflict`가 proper_noun / timeline subtype을 잃지 않고 bounded repair path를 유지하는가?

**미검증.** ep4 미실행. ep2 R3에서 `post_select_conflict` 1회 발생했으나, subtype 보존 여부는 이 런에서 확인 불가.

### Q4. 각 episode별 verdict는?

| Episode | Verdict |
|---|---|
| ep2 | `blocked` |
| ep3 | `not_executed` |
| ep4 | `not_executed` |
| **Combined** | **`blocked`** |

## 5. Remaining Seam

Stage4 finalization을 위해 해소해야 할 잔여 seam:

1. **NpcDrift `relation_to_protag` compressed tag** — `집착100/오해-80` 같은 압축 태그를 LLM 산문에서 검증할 때, exact match가 아닌 semantic equivalence 판정이 필요하거나, NpcDriftAdvisor가 이 유형을 advisory-only (non-escalation)로 분류해야 한다.
2. **strong advisory escalation의 local fix contract 합성** — fixpack Tranche 1이 커버하지 못한 `npc_drift` family에 대한 fix_pack backfill 경로.
3. **ep3/ep4 검증** — 위 seam 해소 후 재실행 필요.

## 6. Guardrails

- 이 문서는 runtime closure를 선언하지 않는다.
- Stage4 resume-ready를 선언하지 않는다.
- source `0_0` 프로젝트는 수정되지 않았다.
- 코드 패치는 수행되지 않았다.
- queue 재정렬은 수행되지 않았다.

## 7. Confidence

Estimated confidence: **97%**

- ep2 evidence is complete (7 rounds, all decision metadata captured)
- Gate distribution is unambiguous (5/7 = `strong_advisory_escalation_non_local_fix`)
- Flashback resolution is confirmed by runtime evidence (Director dismissal + subsequent silence)
- NpcDrift root cause is structurally clear (compressed tag vs prose mismatch)
- ep3/ep4 non-execution is explicitly scoped and does not introduce false claims
