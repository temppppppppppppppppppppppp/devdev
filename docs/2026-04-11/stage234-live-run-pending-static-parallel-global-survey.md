# Stage234 Live-Run-Pending Static Parallel Global Survey

Date: 2026-04-11
Status: draft-live-run-pending
Canonical Path: `docs/2026-04-11/stage234-live-run-pending-static-parallel-global-survey.md`
Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
Baseline Dirty Summary: `dirty: active Stage3 contract/opening/advisory code+tests, queue docs, 0_temp runtime log, and unrelated material-side files are present; this survey treats the live workspace as authority and does not assume a clean tree`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `a costly fresh run is still active and currently exercising Stage3, so this document records static findings plus run-pending watchlist items only; no closure or queue-demotion claim is final until post-run merge audit`
Source Survey Docs:
- `docs/2026-04-11/stage23-live-workspace-static-parallel-survey.md`
- `docs/2026-04-11/stage34-live-workspace-static-parallel-roadmap-validity-survey.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Evidence Artifacts:
- `0_temp.txt`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
Side-Effect Coverage: covered for static sink/contract/roadmap surfaces only; active live-run output is treated as provisional evidence and not as closure truth

## 1. Question

With a costly fresh run still in progress, what are the current static S2-S4 risks, which roadmap/SSOT statements remain valid, and what should the post-run merge audit watch most closely?

## 2. Scope

Included:

- Stage2 contract / persistence / observability residue
- Stage3 contract / advisory / opening-authority / compare-input residue
- Stage4 consumer / repair / analyzer / owner-surface residue
- aggregate roadmap and directly governing S2-S4 SSOT docs
- active Stage3 runtime transcript tail in `0_temp.txt` as provisional watchlist input

Excluded:

- final runtime verdicts from the still-running proof wave
- queue mutation, temp-mirror mutation, or ClickUp mutation
- new execution SSOT creation or lane reprioritization
- unrelated Stage0 / material-side work

## 3. Answer First

- static `P0`: none
- static `P1`: none newly reopened across Stage2-Stage4
- live `run-pending watchlist`: yes, centered on Stage3 semantic/advisory rejection behavior seen in the in-flight run
- static `P2`: still present
  - Stage2 observability / contract residue
  - Stage4 analyzer parity blind spot
  - roadmap / SSOT wording drift in a few places
- static `P3`: still present
  - Stage2, Stage3, and Stage4 structural pressure
- immediate next action stays the same:
  - let the expensive run finish
  - then do one post-run merge audit
  - only patch survivors, not the whole backlog

## 4. Active Findings

### 4.1 `P2` Stage2 still has bounded observability / authority residue

Static evidence still supports the earlier Stage2 residual story:

1. `runtime_advisory` fallback remains narrow.
   - `modules/core/stage2_finalizer.py:1113`
2. `ep_num` semantics still split between operator-facing attempt flow and authoritative sinks.
   - `modules/core/stage2_orchestrator.py:1211`
   - `modules/core/stage2_orchestrator.py:1253`
3. carryover truth is still equipment-first; broader start-state financial truth is not fully normalized on the Stage2 side.
   - `modules/core/stage2_finalizer.py:1737`
   - `modules/core/stage2_finalizer.py:1757`

Meaning:

- Stage2 is no longer a front-severity blocker.
- But its parent contract lane is still not truly closed.

### 4.2 `P2` Stage4 analyzer parity still lags the current sink reality

`FailureAnalyzer` still treats Stage4 differently from Stage2/3 in two places:

1. attempt-set / final-union coverage logic still gives Stage4 a separate lifecycle path instead of the broader Stage2/3-style sink union.
   - `modules/core/failure_analyzer.py:1133`
   - `modules/core/failure_analyzer.py:1147`
2. rationale parity for `runtime_advisory` / `retry_directives` is still gated to `stage in (2, 3)`.
   - `modules/core/failure_analyzer.py:1607`
   - `modules/core/failure_analyzer.py:1624`
   - `modules/core/failure_analyzer.py:1672`

Meaning:

- Stage4 consumer/repair docs remain directionally valid.
- But post-run merge should still inspect Stage4 sinks directly instead of trusting analyzer parity alone.

### 4.3 `P2` roadmap / SSOT wording drift exists even though queue order is still usable

Current roadmap control is mostly valid, but a few explanatory lines are stale:

1. the active roadmap order is current, but parts of the rationale still speak in older Stage2-vs-Stage3 terms.
   - `docs/2026-04-01/active-temp-execution-roadmap.md`
2. the Stage3 opening SSOT slightly overstates direct capital authority; live code clearly lands boundary filtering, but not a broad direct `arc_start_state.capital` authority claim.
   - `modules/domain/agents/blueprint_constraint_compiler.py:716`
3. the Stage4 owner-surface SSOT recount line is slightly stale relative to current live recount.
   - `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`

Meaning:

- no queue reorder is justified by static evidence alone
- but those wording/recount sections should be refreshed before they govern the next code-first turn

### 4.4 `P3` structural pressure still exists across all three stages

The current static picture still includes meaningful owner-surface / long-method debt:

- Stage2
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_orchestrator.py`
- Stage3
  - `modules/core/stage3_orchestrator.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/core/failure_analyzer.py`
- Stage4
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_reject_runtime.py`

Meaning:

- the debt is real
- but while the run is still active, this remains behind proof truth and survivor-only bugfixing

## 5. Live Run-Pending Watchlist

This section is provisional and does not outrank completed post-run evidence.

From the current `0_temp.txt` tail:

1. Stage3 is still showing advisory-heavy reject churn inside the active run.
   - repeated `scenario_density` / fidelity residuals appear in the transcript
2. lexical entity mismatch paths still appear in the current in-flight run.
   - V61-style complaints around surface forms continue to show up in the log
3. score-gate pressure is still visible in the current in-flight run.
   - `re-audit PASS but score=89 < 90`
   - later `effective_score=86 < threshold -> REJECT`

Interpretation rule:

- this is a watchlist, not a final reopened `P1`
- the current run started before the latest Stage3 advisory/compare improvements fully benefit a new rerun
- only the post-run merge audit may decide whether any of this survives as a new queue-level severity claim

## 6. Roadmap / SSOT Validity Snapshot

### 6.1 Still materially valid

- `docs/2026-04-01/active-temp-execution-roadmap.md`
  - queue order remains usable
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
  - still correctly describes Stage3 as landed-but-proof-pending
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
  - still correctly describes the lane as partially landed and proof-pending
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
  - still correctly frames the lane as runtime-demotion-pending
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
  - still correctly frames the lane as proof-pending rather than reopened P1

### 6.2 Valid but textually stale in places

- `docs/2026-04-01/active-temp-execution-roadmap.md`
  - rationale subsection
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
  - older appendices still read more "Stage2-safe" than current residual reality warrants
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
  - capital-authority phrasing is slightly too strong
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
  - recount metadata should be refreshed before reuse as controller text

## 7. Ownership Mapping

No new queue lane is justified from this static pass.

- Stage2 residual contract debt
  - owner: `0_0-stage2-contract-normalization-remediation`
- Stage3 runtime/advisory truth
  - owner remains the existing Stage3 parent + child stack
  - but current run evidence must finish before reopening severity
- Stage4 analyzer parity blind spot
  - owner remains the existing Stage4 consumer/repair/proof family
- structural debt
  - stays subordinate to proof completion

## 8. Next Step

1. let the current expensive run finish
2. perform one `post-run merge audit`
3. classify survivors only:
   - real reopened `P1/P2`
   - stale static worries that the run disproves
4. refresh roadmap/SSOT wording only after the post-run truth is in

## 9. Audit Note

This document is intentionally not a final 3-pass closure doc.

It is a `draft-live-run-pending` watchlist artifact allowed by live-merge governance so the current run can finish without losing the static context gathered in parallel.
