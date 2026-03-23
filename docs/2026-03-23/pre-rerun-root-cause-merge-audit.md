Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause merge audit
Canonical Path: `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md`
Primary Evidence:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/project_data.db`
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/session/ui_events.jsonl`
- `projects/0_0323/logs/artifacts/stage2/**`
- `projects/0_0323/logs/artifacts/stage3/**`
- `projects/0_0323/logs/artifacts/stage4/**`
- `projects/0_0323/plans/arcs/**`
- `projects/0_0323/plans/blueprints/**`
- `projects/0_0323/drafts/**`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `parallel Opus survey order and 10 lane reports were generated against a dirty workspace; live touched surfaces include stage3_orchestrator.py, director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json, docs/2026-03-23/console.txt, projects/0_0323/`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `no commit drift from baseline; merge audit performed against the same HEAD with the same dirty workspace allowance`
Excluded Inputs:
- one separately commissioned extra report was intentionally excluded from this merge scope per operator instruction

---

# Pre-Rerun Root-Cause Merge Audit

## 1. Executive Summary

Arc 1 Episode 3 is not failing because the whole pipeline is broken. The merge result is narrower and more actionable:

1. Stage 2 is not the root cause.
2. Stage 3 is not broadly failing, but one Stage 3 artifact contract is: blueprint timeline metadata can drift from actual manuscript truth.
3. Stage 4 verdict ownership is not split-brain. The Director PASS to post-select REJECT transition is a correct defense-in-depth downgrade, not a logic bug.
4. The highest-cost retry storm came from two real pre-rerun blockers:
   - Python scene-completeness false positive
   - blueprint timeline handoff contamination
5. A third cluster amplifies cost without being the first spark:
   - Stage 4 feedback-fidelity and retry-loop structure
   - empty scene-level semantic fields in blueprint artifacts

There is no confirmed P0 crash, authority loss, or data-loss bug in the Stage 2 to Stage 4 decision chain. The next rerun is technically possible, but from ROI and diagnostic quality, the recommended move is to fix the top blocker cluster first.

**Merge recommendation**: wait, fix the blocker cluster, then rerun.

## 2. Report Inventory

| Lane | Focus | Merge verdict |
|---|---|---|
| T1 | Stage 2 contract static | not root cause |
| T2 | Stage 2 artifact and DB truth | observability debt only |
| T3 | Stage 3 contract static | not root cause |
| T4 | Stage 3 artifact and DB truth | narratively sound, but metadata and scene-field debt remain |
| T5 | Stage 4 write/fix/retry chain | secondary amplifier, not sole root cause |
| T6 | Stage 4 artifact truth | confirms upstream timeline contamination |
| T7 | Director and post-select static chain | not root cause; downgrade is by design |
| T8 | Director and post-select DB parity | observability debt only |
| T9 | context and retrieval support | contributing factor only |
| T10 | cross-layer artifact continuity | strongest root-cause lane |

## 3. Consensus Findings

### 3.1 Not Root Causes

- Stage 2 contract and pacing code is not the root cause.
  - `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md`
- Stage 2 arc artifact is not tactically thin.
  - `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md`
- Director verdict chain is not malfunctioning.
  - `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md`
- Context and retrieval are not the primary failure source.
  - `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md`

### 3.2 Reconciled Stage 3 Position

The Stage 3 reports need a tighter reconciliation than "Stage 3 fine" or "Stage 3 broken."

- T3 is right that the Stage 3 pipeline and Director governance are structurally sound.
- T4 is right that the integrated scenario text is narratively usable.
- T10 and T6 are also right that a narrower Stage 3 artifact contract is broken:
  - `time_flow` and `ending_state.timeline` can diverge from actual manuscript truth
  - scene-level semantic fields can stay empty while still passing

So the correct merge judgment is:

**Stage 3 is not broadly failing, but it does contain a targeted upstream blocker in blueprint temporal handoff, plus a secondary scene-structure precision debt.**

## 4. Primary Pre-Rerun Blockers

### B-1. Python Scene-Completeness False Positive

**Severity**: P1  
**Why it matters**: It repeatedly injects false HIGH warnings and contaminates retry cost.

**Live source anchors**
- `modules/validation/blocking_validator_scene_checks.py:142`
- `modules/validation/blocking_validator_scene_checks.py:185`

**Mechanism**
- The validator extracts a handful of keywords from each `scene_breakdown` item.
- It then scans the manuscript for those keywords and treats a 500-character window as scene evidence.
- This mismatches the actual manuscript format, which can be structurally valid with markdown scene headers like `### 씬 N:`.

**Artifact and console evidence**
- `docs/2026-03-23/console.txt` repeatedly shows `씬 완성도 부족: 0/5`
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/selected_candidate__A.txt` still contains explicit scene headers and passed only after multiple rounds

**Merge judgment**
- This is a real blocker before rerun.
- It is not just an observability issue.
- It wastes rounds, pollutes Director input, and obscures whether the writer actually failed scene realization.

**Fix type**
- `contract-cleanup`

### B-2. Blueprint Timeline Handoff Contamination

**Severity**: P1  
**Why it matters**: It causes cross-episode date drift that only gets caught late by post-select checks.

**Live source anchors**
- `modules/domain/agents/blueprint_constraint_compiler.py:342`
- `modules/domain/agents/blueprint_constraint_compiler.py:344`
- `modules/domain/agents/blueprint_ensemble.py:1014`
- `modules/domain/agents/blueprint_ensemble.py:1023`
- `modules/domain/agents/blueprint_ensemble.py:1129`

**Artifact evidence**
- ep2 blueprint ending metadata says `2006-01-17 Evening`
- ep2 manuscript actually reaches `2006-01-18` evening
- ep3 blueprint then inherits the wrong baseline and emits `2006년 1월 17일 저녁 ~ 1월 18일 저녁`

Key paths:
- `projects/0_0323/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json`
- `projects/0_0323/drafts/ep_0002.txt`

**Merge judgment**
- This is the strongest upstream blocker.
- The post-select downgrade in Ep3 round 4 is evidence that the safety net worked, not that the blocker is harmless.
- If left unfixed, reruns will keep paying a retry tax around relative-to-absolute date boundaries.

**Fix type**
- `contract-cleanup`

### B-3. Stage 4 Feedback-Fidelity and Retry-Loop Inefficiency

**Severity**: P1  
**Why it matters**: It did not ignite the first Ep3 error, but it clearly prolonged recovery.

**Live source anchors**
- `modules/core/stage4_interview_round.py:649`
- `modules/core/stage4_interview_round.py:572`
- `modules/core/stage4_interview_round.py:2071`
- `modules/core/stage4_interview_round.py:5460`
- `modules/core/stage4_interview_round.py:5462`
- `modules/core/stage4_reject_runtime.py:366`

**Mechanism**
- `retry_directives` are flattened with `" / ".join(...)`
- compact feedback still compresses important provenance
- full generation failure snapshots preserve too little structured repair context
- contradiction details and retry history are still reduced before re-entry

**Cross-lane support**
- T5 identifies this as a real downstream root-cause cluster for retry inefficiency
- T7 treats it as outside the verdict chain and consistent with designed gate behavior
- T9 treats it as the actual failure layer rather than context retrieval

**Merge judgment**
- This is the third-ranked pre-rerun fix cluster.
- It is not as universally blocking as B-1 or B-2, but it is high ROI before rerun because it directly affects round count and correction efficiency.

**Fix type**
- `contract-cleanup`

## 5. Secondary Amplifiers

### A-1. Empty Blueprint Scene Semantic Fields

**Severity**: P1  
**Evidence**
- `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json`
- `projects/0_0323/logs/artifacts/stage3/ep_0001/attempt_02/final_blueprint__emotion_focused.json`

`goal`, `summary`, `characters`, `key_events`, and `content` can remain empty across all scenes while the integrated scenario stays strong enough to pass.

**Merge judgment**
- Not the primary cause of the Ep3 storm by itself.
- But it weakens the Writer's per-scene execution contract and combines badly with B-1 and B-3.

**Fix type**
- `contract-cleanup`

### A-2. Early-Episode Thin Retrieval

**Severity**: P2  
**Evidence**
- `docs/2026-03-23/console.txt` shows repeated low-result retrieval patterns
- T9 classifies this as cold-start behavior, not a bug

**Merge judgment**
- Contributing friction only.
- Not a blocker for the next rerun.

**Fix type**
- `observability-only`

### A-3. Pressure Vector Non-Reception

**Severity**: P2  
The system appears to inject pressure signals, but the manuscript openings still fail to reflect them consistently.

**Merge judgment**
- Symptom-level amplifier.
- Worth observing, but below the primary fix cluster.

**Fix type**
- `observability-only`

## 6. Observability-Only Debts

These findings matter for learning from failures, but they are not what caused Ep3 to spiral.

### O-1. Stage 2 and Stage 3 DB Reasoning Sparsity

**Sources**
- `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md`

**Examples**
- Stage 2 and Stage 3 `stage_attempts` omit reasoning fields
- Stage 3 does not persist raw rationale like Stage 4
- Stage 3 `director_thinking` remains empty

**Merge judgment**
- Real debt
- not pre-rerun blocking

### O-2. Stage 2 Reject Reason Truncation

**Live source anchor**
- `modules/core/stage2_finalizer.py:2837`

This is a direct policy violation and should be fixed, but it did not drive the current Ep3 failure.

### O-3. `initial_verdict` Null on Post-Select Downgrade

**Source survey**
- `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md`

The split between Director PASS and final REJECT is recoverable from JSON and joins, but not represented ergonomically in `stage_attempts`.

**Merge judgment**
- diagnostic debt only

## 7. False Leads and Non-Causes

### N-1. "Stage 2 was tactically thin"

Rejected by T1 and T2.

### N-2. "Director and post-select are inconsistent"

Rejected by T7 and supported by console evidence.  
The downgrade is designed defense-in-depth, not split-brain malfunction.

### N-3. "Stage 4 simply cannot write"

Too broad.  
Ep1 and Ep2 passed on attempt 1, and Ep3 eventually passed on round 5. The problem is narrower: structure detection, timeline contamination, and retry inefficiency.

### N-4. "Retrieval failure caused the whole issue"

Rejected by T9.  
Retrieval is thinner than ideal, but not the primary failure source.

### N-5. "Stage 3 artifact quality is generally bad"

Too broad.  
The integrated scenarios are good. The defects are specific to temporal handoff metadata and empty scene semantic fields.

## 8. Recommended Pre-Rerun Fix Cluster

### Cluster 1. Scene Validator Contract Fix

Target direction:
- align scene-completeness detection with actual manuscript scene format
- stop treating structurally valid markdown scene headers as missing scenes

Priority: first

### Cluster 2. Blueprint Temporal Handoff Fix

Target direction:
- derive temporal continuity from verified previous manuscript truth or verified ending state
- stop relying on stale previous blueprint metadata as the only temporal baseline

Priority: first

### Cluster 3. Feedback-Fidelity and Retry Repair

Target direction:
- preserve structured retry directives
- preserve richer empty-round failure snapshots
- reduce flattening and compacting in Stage 4 repair guidance
- fill scene-level semantic fields where feasible

Priority: second

### Cluster 4. Observability Cleanup

Target direction:
- Stage 2 and Stage 3 DB reasoning parity
- `initial_verdict` parity
- Stage 2 truncation removal

Priority: after blocker cluster or in parallel if change blast radius stays low

## 9. Fresh-Run Recommendation

### Per-Lane Raw Signal

- `yes`: T1, T2, T3, T4, T5, T6, T7, T8, T9
- `no`: T10

### Merge Verdict

The merged answer is not "hard no because the repo is unsafe."  
It is:

**Do not rerun yet, because the next rerun will likely waste time and compute on already-understood blockers.**

The repo is not crash-unsafe. The ROI case is what changes the verdict:

- B-1 and B-2 are strong enough to recur
- B-3 is strong enough to amplify cost again
- the current fresh-run evidence already isolated the pattern sufficiently

So the recommended sequence is:

1. fix B-1
2. fix B-2
3. fix the highest-ROI part of B-3
4. rerun

## 10. Confidence And Limits

**Estimated confidence: 96%**

### Why this is above 95%

- 10 bounded lane reports all arrived and were read
- cross-lane consensus is strong on the main "not causes"
- the top blockers are triangulated across source, console, DB, and artifact truth
- live source anchors were rechecked for the two main blocker clusters and the main retry-fidelity cluster

### Remaining uncertainty

- the exact best implementation seam for blueprint temporal truth may require one more code-path audit before patching
- the scene validator's runtime false-positive mechanism is strongly evidenced by source and artifacts, but not replayed under an isolated micro-test in this survey document
- one extra separately commissioned report was excluded by instruction, so this merge covers only the ordered 10-lane bundle

## 11. 3-Pass Audit Record

### Pass 1. Structure and Scope

- confirmed this document is a merge audit, not an execution SSOT
- bounded scope to the 10 ordered lane reports only
- separated blockers, amplifiers, and observability debts

### Pass 2. Evidence and Consistency

- checked T1/T2 against T10 to resolve the "Stage 2 thin arc" question
- checked T3/T4 against T6/T10 to resolve the "Stage 3 broadly fine vs Stage 3 metadata defect" question
- checked T7 against console evidence to resolve the "split-brain" framing
- rechecked live source anchors for scene detection, blueprint handoff, and retry feedback flattening

### Pass 3. Execution and Readability

- reduced the output to one pre-rerun fix cluster rather than 10 unrelated backlogs
- converted the raw lane `yes/no` rerun signals into one merge recommendation
- made the operating consequence explicit: fix first, rerun second

