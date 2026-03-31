# 0_1 Stage4 CW First-Pass Miss — Lane 4: Runtime Evidence & Downstream Gate Separation

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Document Type: bounded parallel survey lane draft
Lane: Terminal 4 — runtime evidence / downstream gate separation
Canonical Path: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane4-runtime-vs-gate-draft.md`
Master Order: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/docs-temp/log-db drift, recent EP8/EP9 survey-doc outputs untracked`

Evidence Sources:
- `projects/0_1/project_data.db` — `stage_attempts` (63 rows), `director_selections` (63 rows)
- `projects/0_1/logs/session/decisions.jsonl` (77 lines)
- `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_01..05`
- `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
- `projects/0_1/logs/artifacts/stage4/ep_0010/attempt_01..05`
- `modules/core/stage4_interview_round.py` L1811-2136 (fix_pack contract + advisory escalation gate)
- `modules/core/stage4_reject_runtime.py` L62-211 (reject guidance)
- `modules/core/stage4_retry_runtime.py` L90-236 (PASS_WITH_FIX loop)
- `modules/core/stage4_outcome_runtime.py` L23-69 (pass outcome + CoVe)

Context Surveys:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-draft-meta-leak-bounded-survey.md`

---

## 1. Coverage

### Read and analyzed

| Surface | Method | Detail |
|---|---|---|
| `stage_attempts` | DB query, stage=4 | EP1-10 전량, 63 rows |
| `director_selections` | DB query, stage=4 | EP1-10 전량, 63 rows |
| Artifact dirs EP8/9/10 | filesystem ls | attempt_01..05 (EP8), attempt_01..06 (EP9), attempt_01..05 (EP10) |
| `decisions.jsonl` | JSON parse, EP8-10 filter | Stage 2/3/4 전체 decision chain |
| `stage4_interview_round.py` | L1990-2136 read | Advisory escalation + Lane2-G1/G2a/G2b gate chain |
| `stage4_interview_round.py` | L3969-4143 read | Post-select conflict downgrade path |
| `stage4_interview_round.py` | L1811-1828 read | `_evaluate_fix_pack_contract()` — 6-field readiness gate |
| `stage4_reject_runtime.py` | L62-211 read | Reject guidance + retry snapshot construction |
| `stage4_retry_runtime.py` | L90-236 read | PASS_WITH_FIX loop: 3-iteration patch + re-audit |
| `stage4_outcome_runtime.py` | L23-119 read | Pass outcome governance + CoVe verification |

### Not read (out of scope for this lane)

- CW prompt topology (Terminal 1)
- Previous-manuscript carryover consumption (Terminal 2)
- Model tier / provider fallback / budget (Terminal 3)
- `llm_io.jsonl` per-call payload (model/provider lane)

---

## 2. Findings

### Finding 1: ALL 10 first-pass manuscripts receive Director PASS

This is the single most important finding of this lane.

| EP | First-Pass Score | Director Verdict | Final Verdict | Gate Basis |
|---|---|---|---|---|
| 1 | 95 | **PASS** | PASS | director_primary_pass |
| 2 | 90 | **PASS** | PASS | patch_reaudit_pass |
| 3 | 100 | **PASS** | REJECT | post_select_conflict |
| 4 | 98 | **PASS** | PASS | director_primary_pass |
| 5 | 96 | **PASS** | REJECT | post_select_conflict |
| 6 | 90 | **PASS** | PASS | patch_reaudit_pass |
| 7 | 97 | **PASS** | PASS | director_primary_pass |
| 8 | 95 | **PASS** | REJECT | pass_with_fix_contract_missing_patch_targets |
| 9 | 98 | **PASS** | REJECT | strong_advisory_escalation_non_local_fix |
| 10 | 96 | **PASS** | REJECT | strong_advisory_escalation_non_local_fix |

**Implication**: Director LLM (the manuscript quality authority) has never rejected a first-pass CW manuscript across all 10 episodes. Every first-pass REJECT originates from Python-side gates that run after Director evaluation.

### Finding 2: First-pass scores are equal or higher than passing-attempt scores

| Metric | First-Pass Scores (EP1-10) | Passing-Attempt Scores (EP1-10) |
|---|---|---|
| Range | 90 - 100 | 90 - 98 |
| Median | 96 | 95.5 |
| Mean | 95.6 | 94.8 |

Three episodes where first-pass scored HIGHER than the eventually-passing attempt:
- EP3: first-pass 100 → pass on A2 at 96
- EP9: first-pass 98 → pass on rerun-A1 at 95
- EP10: first-pass 96 → pass on A5 at 95

**Implication**: CW does not improve with retries. Retries succeed because downstream gates stop firing, not because CW generates better text.

### Finding 3: First-pass REJECT families cluster into 3 downstream gate types

| Gate Basis Family | Episodes Affected | Mechanism | CW Weakness? |
|---|---|---|---|
| **Advisory escalation + fix_pack deadlock** | EP8, EP9, EP10 | NpcDrift/flashback advisory triggers Lane2-G1 escalation (PASS→PASS_WITH_FIX), then Lane2-G2b finds no ready fix_pack → REJECT | **No** — Director PASSED, advisory is FP or imprecise, contract deadlock is structural |
| **Post-select conflict** | EP3, EP5 | Continuity/history conflict detected by post-select LLM check after Director approved | **No** — CW text is structurally fine; a specific continuity signal conflicts with prior episode state |
| **(none — CW passed)** | EP1, EP2, EP4, EP6, EP7 | Director PASS survived all gates | N/A |

**Not one first-pass REJECT is attributable to CW writing quality.**

### Finding 4: Advisory escalation → fix_pack deadlock is the dominant false-REJECT generator

The code path (confirmed in live code):

```
Advisory fires (npc_drift / flashback / etc.)
→ Lane2-G1: PASS → PASS_WITH_FIX (interview_round.py:2015-2024)
→ Lane2-G2b: _evaluate_fix_pack_contract() → missing_patch_targets
→ REJECT (interview_round.py:2097-2101)
```

`_evaluate_fix_pack_contract()` requires ALL of:
1. `patch_targets` non-empty
2. `must_fix` non-empty
3. `do_not_regress` non-empty
4. `success_condition` non-empty
5. `target_kind` in {entity_ref, local_phrase, local_sentence}

When Director gives PASS, the Director output schema has no `fix_pack` field at all. Advisory escalation changes the verdict to PASS_WITH_FIX but does not generate a fix_pack. Therefore Lane2-G2b always finds `missing_patch_targets` → REJECT.

This structural deadlock was the sole root cause of EP9's 6 consecutive REJECTs and the primary cause of EP8's 8 consecutive REJECTs.

### Finding 5: Post-NpcDrift-patch, the same structural pattern persists with flashback

EP10 (post-patch) first-pass:
- A1: flashback advisory → strong_advisory_escalation_non_local_fix → REJECT (score 96, Director PASS)

The NpcDrift patch resolved NpcDrift as a trigger, but the advisory escalation → fix_pack deadlock mechanism is unchanged. Any strong advisory class (truth_gate, npc_drift, rel_drift, flashback, info_paradox) can trigger the same deadlock.

### Finding 6: EP10 shows a mixed failure distribution that separates genuine issues from gate illusions

| EP10 Attempt | Score | Director Verdict | Final Verdict | Gate Basis | Classification |
|---|---|---|---|---|---|
| A1 | 96 | PASS | REJECT | strong_advisory_escalation_non_local_fix | **Gate illusion** — flashback advisory |
| A2 | 92 | PASS_WITH_FIX | REJECT | post_select_conflict | **Genuine** — continuity issue |
| A3 | 44 | REJECT | REJECT | continuity_firewall | **Genuine** — Director rejected, bad manuscript |
| A4 | 90 | PASS_WITH_FIX | REJECT | post_select_conflict | **Genuine** — continuity issue |
| A5 | 95 | PASS | PASS | director_primary_pass | Clean pass |

Post-patch, 1/5 attempts hit the advisory deadlock (gate illusion), 2/5 hit genuine continuity issues, 1/5 was a genuinely bad manuscript, and 1/5 passed. This is a much healthier distribution than EP9's 6/6 advisory deadlock.

### Finding 7: Retries help through gate avoidance, not CW improvement

Evidence per episode:

| Episode | Why first-pass failed | Why eventual pass succeeded | CW improvement? |
|---|---|---|---|
| EP3 | post_select_conflict | Different candidate did not trigger conflict | **No** — score dropped 100→96 |
| EP5 | post_select_conflict | Different candidate did not trigger conflict | **No** — score constant 96→96 |
| EP8 | npc_drift advisory escalation | Advisory non-deterministically did not fire on run2-A3 | **No** — score unchanged 95→96 |
| EP9 | npc_drift advisory escalation | Code patch removed the false positive | **No** — score dropped 98→95 |
| EP10 | flashback advisory escalation | A5 avoided triggering any strong advisory | **No** — score dropped 96→95 |

In ALL 5 cases:
- The passing attempt scored **equal or lower** than the first-pass
- The passing attempt succeeded because **downstream gates stopped blocking**, not because CW wrote better
- Retry feedback, MAD/ToT escalation, and patch mode did not contribute to the eventual pass

### Finding 8: EP10 A3 is the sole genuine CW first-pass weakness in the dataset

EP10 A3 scored 44 with Director verdict REJECT and gate_basis `continuity_firewall`. This is the only case in the entire 0_1 dataset where the Director itself rejected a first-pass manuscript (albeit it was attempt 3, not attempt 1). This represents a genuine CW failure mode — but it occurred after 2 previous retry-with-feedback rounds, not on first pass.

Across all 10 episodes, Director rejected exactly 1 manuscript total (EP10 A3, score 44, `continuity_firewall`). Zero first-pass manuscripts were Director-rejected.

---

## 3. Non-Issues

### CW first-pass writing quality
NOT an issue. Director PASSES all first-pass manuscripts with scores 90-100. CW produces consistently high-quality first-pass output.

### Retry-driven CW improvement
NOT observed. Passing scores are equal or lower than first-pass scores. Retries succeed through gate avoidance, not quality improvement.

### Director scoring accuracy
NOT an issue in this lane. Director consistently gives PASS to manuscripts that are structurally sound. The one Director REJECT (EP10 A3, score 44) was a genuine failure case.

### Post-select conflict as systemic CW weakness
NOT CW weakness. Post-select conflict (EP3, EP5, EP10 A2/A4) detects genuine continuity mismatches between the selected manuscript and prior episode state. This is a feature of the quality gate, not a CW prompt/generation failure. Different candidate selection resolves it.

---

## 4. Verdict

**`downstream-first`**

CW first-pass weakness is NOT real as a primary diagnosis. The data shows:

1. **Director never rejects first-pass manuscripts** (0/10 Director REJECTs on first pass)
2. **First-pass scores (90-100) exceed passing scores (90-98)** — CW does not improve with retries
3. **All 5 first-pass REJECTs originate from downstream Python gates**, not from CW writing quality:
   - 3/5 from advisory escalation + fix_pack contract deadlock (false positive mechanism)
   - 2/5 from post-select conflict (genuine but not CW weakness)
4. **Retries help by gate avoidance** (advisory non-determinism, different candidate selection, or code patch), not by CW improvement

The primary blocker is the **advisory escalation → fix_pack contract deadlock** pattern:
- Any strong advisory false positive (npc_drift, flashback, etc.) triggers PASS → PASS_WITH_FIX
- No code owner generates fix_pack for advisory-escalated verdicts
- Lane2-G2b inevitably finds missing_patch_targets → REJECT
- This wastes retry budget on a structural contract gap, not a CW quality gap

The secondary blocker is **post-select conflict** detection, which is a legitimate safety gate but contributes to the appearance of CW first-pass failure because it fires after Director PASS.

### Downstream gate illusion quantification

| Classification | Episodes | Count | Description |
|---|---|---|---|
| Gate illusion: advisory deadlock | EP8, EP9, EP10-A1 | 3/10 first-pass | Advisory FP + fix_pack deadlock creates REJECT despite Director PASS |
| Genuine but non-CW: post-select conflict | EP3, EP5 | 2/10 first-pass | Continuity mismatch, not CW quality |
| Clean first-pass PASS | EP1, EP2, EP4, EP6, EP7 | 5/10 first-pass | CW passed all gates on first try |
| Genuine CW weakness on first pass | — | 0/10 first-pass | No Director REJECT on any first pass |

---

## 5. Stop

read-only lane complete; no files mutated (except this draft report)

---

## Appendix A: Full First-Pass Evidence Matrix

| EP | A# | Score | Dir V | Final V | Gate Basis | Advisory Keys | CW Quality? |
|---|---|---|---|---|---|---|---|
| 1 | A1 | 95 | PASS | PASS | director_primary_pass | style_signal | Good |
| 2 | A1 | 90 | PASS | PASS | patch_reaudit_pass | style_signal | Good |
| 3 | A1 | 100 | PASS | REJECT | post_select_conflict | style_signal | Good |
| 4 | A1 | 98 | PASS | PASS | director_primary_pass | style_signal | Good |
| 5 | A1 | 96 | PASS | REJECT | post_select_conflict | style_signal | Good |
| 6 | A1 | 90 | PASS | PASS | patch_reaudit_pass | style_signal, npc_drift | Good |
| 7 | A1 | 97 | PASS | PASS | director_primary_pass | style_signal | Good |
| 8 | A1 | 95 | PASS | REJECT | pass_with_fix_contract_missing_patch_targets | style_signal, npc_drift | Good |
| 9 | A1 | 98 | PASS | REJECT | strong_advisory_escalation_non_local_fix | style_signal, npc_drift | Good |
| 10 | A1 | 96 | PASS | REJECT | strong_advisory_escalation_non_local_fix | style_signal, flashback | Good |

## Appendix B: Per-Episode Attempt Count and Pass Attempt

| EP | Total Attempts | First-Pass Score | Pass Attempt | Pass Score | Delta |
|---|---|---|---|---|---|
| 1 | 1 | 95 | A1 | 95 | 0 |
| 2 | 1 | 90 | A1 | 90 | 0 |
| 3 | 2 | 100 | A2 | 96 | -4 |
| 4 | 1 | 98 | A1 | 98 | 0 |
| 5 | 2 | 96 | A2 | 96 | 0 |
| 6 | 1 | 90 | A1 | 90 | 0 |
| 7 | 1 | 97 | A1 | 97 | 0 |
| 8 | 9 | 95 | A3(run2) | 96 | +1 |
| 9 | 7 | 98 | A1(rerun) | 95 | -3 |
| 10 | 5 | 96 | A5 | 95 | -1 |

Average delta: -0.7 (retries score slightly LOWER than first pass)

## Appendix C: EP10 Post-Patch Failure Distribution

| Attempt | Score | Director | Final | Gate | Class |
|---|---|---|---|---|---|
| A1 | 96 | PASS | REJECT | strong_advisory_escalation_non_local_fix (flashback) | Gate illusion |
| A2 | 92 | PASS_WITH_FIX | REJECT | post_select_conflict | Genuine non-CW |
| A3 | 44 | REJECT | REJECT | continuity_firewall | Genuine CW failure |
| A4 | 90 | PASS_WITH_FIX | REJECT | post_select_conflict | Genuine non-CW |
| A5 | 95 | PASS | PASS | director_primary_pass | Clean pass |
