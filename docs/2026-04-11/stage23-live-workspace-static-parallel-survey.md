# Stage23 Live-Workspace Static Parallel Survey

Date: 2026-04-11
Status: final
Canonical Path: `docs/2026-04-11/stage23-live-workspace-static-parallel-survey.md`
Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
Baseline Dirty Summary: `dirty: Stage3 truth-first / opening-authority / analyzer-parity code and tests are modified in-worktree; queue docs and unrelated material-side files are also dirty, so this survey treats the live workspace rather than clean HEAD as the evidence source`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `current request is a fresh static parallel survey on the live workspace after additional Stage2/Stage3 bounded patches; stale backup-branch work remains excluded from authority`
Source Survey Docs:
- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/failure_analyzer.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_clarity_density_wave1.py`
- `tests/test_failure_analyzer.py`
Side-Effect Coverage: covered (static sink/contract/observability surfaces only; no rerun or DB mutation)

## 1. Question

After the latest bounded Stage2/Stage3 patches on the live workspace, what static risks still remain, what earlier risks now look closed, and which existing lanes should own the residual work?

## 2. Scope

Included:

- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/failure_analyzer.py`
- directly relevant Stage2 / Stage3 guardrail tests

Excluded:

- stale backup-branch work
- fresh runtime reruns, DB truth, or post-run merge audit
- broad Stage4 / Stage0 reprioritization
- material-side narrative artifacts except as dirty-worktree context

## 3. Answer First

- no new `P0`
- no remaining static `P1` in Stage2 or Stage3 after the latest bounded patches
- the previous Stage3 truth-first blockers now look statically closed
- the live residuals are `P2 observability / contract drift` plus `P3 structural pressure`
- the highest-value next move is no longer another broad static patch wave; it is a fresh proof wave, with one optional small Stage3 analyzer follow-up still worth noting

## 4. Static Closures Since The Earlier Current-Main Survey

### 4.1 Stage3 truth-first closures

1. Success sink ordering now sits behind the persistence barrier.
   - `modules/core/stage3_orchestrator.py:1977`
   - `modules/core/stage3_orchestrator.py:1995`
   - current code persists the blueprint first and only then builds/records success runtime payloads
2. `PASS_WITH_FIX` now follows the Stage3 success path and pass-rate success accounting.
   - `modules/core/stage3_orchestrator.py:1084`
   - `modules/core/stage3_orchestrator.py:2165`
   - `tests/test_stage3_orchestrator.py:1292`
   - `tests/test_stage3_orchestrator.py:1347`
3. Stage2 -> Stage3 opening-state authority is now current-arc first.
   - `modules/domain/agents/blueprint_constraint_compiler.py:82`
   - `modules/domain/agents/blueprint_constraint_compiler.py:445`
   - `modules/domain/agents/blueprint_constraint_compiler.py:547`
   - `tests/test_stage3_blueprint_state_precision_guardrail.py:199`
   - `tests/test_stage3_clarity_density_wave1.py:127`
4. Investment capital continuity now filters future-episode events.
   - `modules/domain/agents/blueprint_constraint_compiler.py:716`
   - `modules/domain/agents/blueprint_constraint_compiler.py:737`
   - `modules/domain/agents/blueprint_constraint_compiler.py:840`
   - `tests/test_stage3_blueprint_state_precision_guardrail.py:329`
   - `tests/test_stage3_clarity_density_wave1.py:160`
5. Stage3 rationale parity now covers `runtime_advisory` and `retry_directives`.
   - `modules/core/failure_analyzer.py:1607`
   - `modules/core/failure_analyzer.py:1624`
   - `modules/core/failure_analyzer.py:1641`
   - `modules/core/failure_analyzer.py:1672`
   - `tests/test_failure_analyzer.py:2171`
   - `tests/test_failure_analyzer.py:2286`

### 4.2 Stage2 / Stage3 severity consequence

- the old survey's Stage3 `P1` set is no longer the current static truth
- Stage2 still has residual debt, but it is no longer outranked by an open Stage3 sink-ordering bug

## 5. Remaining Findings

### 5.1 `P2` Stage3 sink-alignment coverage contract is still Stage2/Stage4-centric

`FailureAnalyzer` now compares Stage3 rationale fields correctly when rows are present, but the broader sink-alignment coverage logic still does not treat Stage3 `pass_rate_monitor` and `director_selections` as part of the final-attempt union the way Stage2 does, and it still reserves lifecycle-union logic for Stage4 only.

Evidence:

- `modules/core/failure_analyzer.py:1133`
- `modules/core/failure_analyzer.py:1147`
- `modules/core/failure_analyzer.py:1157`
- `modules/core/failure_analyzer.py:1176`

Operational meaning:

- Stage3 sink-alignment summary can now catch rationale mismatches
- but it can still under-report Stage3 coverage/missing-row problems in the same summary family
- this is an observability debt, not a content-generation bug

### 5.2 `P2` Stage2 `runtime_advisory` fallback remains too narrow

`_resolve_stage2_runtime_advisory()` still returns only the explicit field and does not promote advisory-like pressure from reason-bearing surfaces the way Stage2 does for other rationale fields.

Evidence:

- `modules/core/stage2_finalizer.py:1114`
- `modules/core/stage2_finalizer.py:2573`
- `modules/core/stage2_finalizer.py:3525`
- `modules/core/stage2_finalizer.py:3683`

Operational meaning:

- advisory-heavy `PASS_WITH_FIX` / reject paths can still persist blank `runtime_advisory`
- the sink contract is cleaner than before, but not yet robust

### 5.3 `P2` Stage2 `ep_num` semantics are still split across operator and authoritative sinks

The `single_arc_attempt` operator heartbeat/progress still logs `ep_num=current_ep_start`, while the authoritative session/DB sinks use `ep_num=global_arc_no`.

Evidence:

- `modules/core/stage2_orchestrator.py:1211`
- `modules/core/stage2_orchestrator.py:1253`
- `modules/core/stage2_finalizer.py:2535`
- `modules/core/stage2_finalizer.py:2577`
- `modules/core/stage2_finalizer.py:3506`
- `modules/core/stage2_finalizer.py:3673`

Operational meaning:

- Stage2 joins that rely on `ep_num` still need contextual interpretation
- the drift is operator-facing and analytics-facing, not a tactical-arc content defect

### 5.4 `P2` Stage2 carryover authority still stops at equipment-first truth

The current carryover sync recalculates equipment from the previous arc and updates the first-episode `[시작 상태]` line for location/equipment/injuries/internal_energy, but it still does not authoritatively recompute or overwrite start-side capital / total-assets / portfolio truth.

Evidence:

- `modules/core/stage2_finalizer.py:218`
- `modules/core/stage2_finalizer.py:1737`
- `modules/core/stage2_finalizer.py:1740`
- `modules/core/stage2_finalizer.py:1758`

Operational meaning:

- Stage2 start-state text is less stale than before
- but investment-style carryover authority is still only partial on the Stage2 side

### 5.5 `P3` Structural pressure remains on both Stage2 and Stage3 owners

Static AST recount on the live workspace still shows significant owner-surface pressure:

- `Stage2Finalizer`: `51 methods`, `120+ = 6`, `180+ = 1`, max `180 LOC`
  - hotspot: `modules/core/stage2_finalizer.py:3403`
- `Stage2Orchestrator`: `51 methods`, `120+ = 3`, `180+ = 0`, max `153 LOC`
  - hotspots: `modules/core/stage2_orchestrator.py:279`, `modules/core/stage2_orchestrator.py:433`, `modules/core/stage2_orchestrator.py:1182`
- `Stage3Orchestrator`: `46 methods`, `120+ = 4`, `180+ = 1`, max `204 LOC`
  - hotspot: `modules/core/stage3_orchestrator.py:2949`
- `BlueprintConstraintCompiler`: `17 methods`, `120+ = 3`, max `170 LOC`
  - hotspot: `modules/domain/agents/blueprint_constraint_compiler.py:716`
- `FailureAnalyzer`: `75 methods`, `120+ = 3`, max `176 LOC`
  - hotspots: `modules/core/failure_analyzer.py:1309`, `modules/core/failure_analyzer.py:1785`

Operational meaning:

- this is real debt
- but after the recent truth-first closures, it is lower priority than proof validation and the bounded P2 residuals above

## 6. Queue / Ownership Mapping

No new queue lane is needed.

- `0_0-stage3-contract-tightening-remediation`
  - still owns the remaining Stage3 sink-alignment coverage / observability contract gap
- `0_0-stage2-contract-normalization-remediation`
  - still owns Stage2 `runtime_advisory` fallback
  - still owns Stage2 `ep_num` semantics cleanup
  - still owns broader carryover-authority normalization
- structural pressure stays subordinate to proof and contract follow-up
  - it does not justify opening a new front-of-queue lane by itself

## 7. Recommended Next Order

1. `fresh proof wave`
   - current static picture says the high-severity Stage3 blockers are now code-closed
   - the highest-value next truth source is runtime, not another same-day static refactor
2. optional bounded follow-up before or after the rerun:
   - extend Stage3 `FailureAnalyzer` sink-alignment attempt-set / missing-bucket coverage so Stage3 pass-rate / director rows participate like Stage2
3. after proof:
   - resume Stage2 residual contract cleanup
   - only then reopen long-method / owner-surface reduction if it still matters

## 8. 3-Pass Audit

Pass 1. Structure / Scope
- kept this as a survey doc, not a new execution SSOT
- bounded scope to live Stage2 / Stage3 code and directly relevant tests
- separated static closures from remaining findings so earlier current-main survey claims do not silently survive

Pass 2. Evidence / Consistency
- re-read the earlier current-main survey and current execution SSOTs before classifying anything as still-open
- re-audited live code anchors instead of inheriting old findings by default
- used targeted tests only as static corroboration, not as runtime proof

Pass 3. Execution / Readability
- reduced the survey to ownership-bearing residuals plus one structural bucket
- kept queue consequence bounded: no new lane, no roadmap rewrite
- made the next operational consequence explicit: proof wave first

Confidence: `97%`
