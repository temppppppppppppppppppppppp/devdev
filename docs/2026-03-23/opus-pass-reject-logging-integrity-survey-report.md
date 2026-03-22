Date: 2026-03-23
Status: final (3-pass audited, bounded scope)
Document Type: system-track survey report
Canonical Path: `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-order.md`
Evidence Artifacts:
- operator-provided fresh-run terminal capture on 2026-03-23
- `tests/test_stage01_helpers.py`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_stage2_finalizer.py`
Side-Effect Coverage:
- console / UI logs
- audit facade
- pass-rate metrics sink
- Stage 4 DB / file sidecars

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Baseline Dirty Summary: `dirty: 6 tracked, 2 untracked; hotspots: modules/core/stage0/__init__.py, modules/core/stage2_finalizer.py, tests/test_stage0_work_guard_style_cache.py, tests/test_stage2_finalizer.py, .tmp_stage0_msg/, docs/2026-03-23/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Scope
This report answers a bounded question:
- Did the long-function decomposition campaign cause confirmed PASS/REJECT decision loss, persistence loss, or operator-surface loss in the inspected Stage 0 / 2 / 4 lanes?

This report does not claim full end-to-end parity for every Stage 2/3/4 branch. The current live evidence is strongest on:
- Stage 0 operator path
- Stage 2 reject metrics sink
- Stage 2 finalizer console sink
- Stage 4 static verdict / sink authority map

## 2. Executive Conclusion
Current evidence does **not** show confirmed loss of PASS/REJECT authority or DB persistence caused by the long-function decomposition campaign in the inspected lanes.

What is confirmed instead:
- operator-surface regressions did occur
- they were concentrated in stale gating and source-string corruption
- the proven regressions were console/menu visibility issues, not verdict-contract loss

Bounded verdict:
- `confirmed verdict loss`: none
- `confirmed persistence loss`: none
- `confirmed operator-surface loss`: yes
- `root cause class`: stale availability gate + mojibake source strings

## 3. Stage-by-Stage Authority / Sink Map
### 3.1 Stage 0
Authority:
- [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L130) `phase_0_recovery()` owns the operator submenu and routing into extended Stage 0 modes.
- [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L892) `run_reference_analysis()` owns the reference-analysis flow.

Primary sinks:
- console / UI via `app.ui.log(...)` and `self._ui_log(...)`
- style-guide file persistence via [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L835) `_persist_reference_style_guide()`

Observed issue:
- user fresh run showed option `6` path with mojibake and, earlier, missing Stage 0 extended options.

Confirmed cause:
- stale availability gating in [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L141)
- source-string corruption inside [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L736) through [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L890)

Impact classification:
- operator-surface-only
- no evidence of decision-authority loss

### 3.2 Stage 2 Reject Path
Authority:
- reject classification and reject metrics recording remain in [stage2_validation_pipeline.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py#L1023)

Primary sinks:
- `pass_rate_monitor.record_attempt(...)`
- final verdict field: `final_verdict="REJECT"`
- reject reason field: `reject_reason=...`

Static conclusion:
- the reject sink contract is still explicitly wired after decomposition
- no static sign that Stage 2 reject outcomes stopped persisting to pass-rate monitoring

Impact classification:
- no confirmed verdict loss
- live rejection parity still needs a dedicated fresh-run branch to fully close

### 3.3 Stage 2 Pass Finalizer
Authority:
- post-pass constraint DB handoff lives in [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L1243) `_update_stage2_pass_constraint_db()`

Primary sinks:
- `constraint_db.update_arc_state(refined_arc)`
- console / UI log confirming the update

Confirmed issue:
- the UI log string was mojibake in source

Confirmed cause:
- source-string corruption, not sink detachment

Impact classification:
- operator-surface-only
- underlying update call remained invoked

### 3.4 Stage 4 Director Verdict
Authority:
- director verdict payload and summary logging remain in [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py#L642) `_log_director_decision_summary()`

Primary sinks:
- console / UI summary
- attempt event log via `owner._log_attempt_event(...)`
- meta payload fields: verdict, director_verdict, gate_basis, score, selected_candidate

Static conclusion:
- verdict shaping and logging are still explicit and centralized
- no static sign of lost final verdict surfacing in the inspected Stage 4 director lane

### 3.5 Stage 4 Pass Settlement
Authority:
- owner pass sink boundary remains in [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L553) `_save_pass_result_primary_db()`

Primary sinks:
- `db.save_manuscript(...)`
- `db.update_martial_tracker(...)`
- emergency dump fallback
- quality sidecars via [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L604) `_save_pass_result_quality_sidecars()`

Static conclusion:
- DB / emergency dump / quality sidecar paths are still owner-visible and explicit
- no static sign that post-pass persistence was silently dropped by helper extraction

## 4. Confirmed Regressions
### Finding 1. Stage 0 extended submenu visibility regression
Severity: medium

Evidence:
- operator terminal capture showed only option `1` and `0`
- [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L141) previously depended on a stale availability flag

Conclusion:
- confirmed operator-surface regression
- not a verdict or persistence regression

### Finding 2. Stage 0 reference-analysis mojibake
Severity: medium

Evidence:
- operator terminal capture showed mojibake after selecting Stage 0 option `6`
- source corruption was present in [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L736) through [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L890)

Conclusion:
- confirmed source-string corruption
- not terminal-render-only

### Finding 3. Stage 2 ConstraintDB update log mojibake
Severity: low

Evidence:
- [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L1243) had corrupted logging strings while the update call itself remained intact

Conclusion:
- confirmed operator-surface regression
- no evidence that `constraint_db.update_arc_state(...)` stopped executing

## 5. Console Volume Change Assessment
User suspicion:
- console output appears to have decreased after the decomposition campaign

Current judgment:
- partially true
- current evidence suggests a mix of:
  - intended duplicate / dead-log collapse
  - unintended operator-surface loss from stale gating and mojibake strings

What is confirmed:
- Stage 0 reference-analysis family had duplicate/dead residue removed, which legitimately reduces noise
- some visible loss was not intended, because the strings were corrupted or hidden by stale gating

What is not yet confirmed:
- any broader Stage 2/4 operator-surface reduction beyond the specific confirmed findings above

## 6. Decomposition Impact Verdict
Based on the inspected lanes and available fresh-run evidence:
- long-function decomposition **did not** produce confirmed PASS/REJECT authority loss
- long-function decomposition **did not** produce confirmed DB persistence loss
- long-function decomposition **did** coincide with operator-surface regressions in a small number of paths

Best current classification:
- `no confirmed loss` for verdict and persistence
- `operator-surface-only loss` for the proven regressions

## 7. Unconfirmed Areas
These are still open and should not be overclaimed:
- full live Stage 2 reject path after the latest fixes
- full live Stage 4 pass / reject path after the latest fixes
- whether any non-inspected console families were thinned too aggressively

## 8. Recommended Next Step
Do one bounded fresh run before any new refactor wave:
1. Stage 0 option `6` reference-analysis smoke
2. smallest reproducible Stage 2 reject path
3. one Stage 4 pass or reject path

During that run, verify for each stage:
- console explanation line
- audit-event emission
- pass-rate / metrics emission
- DB or artifact side effect

Only if a mismatch is observed there should a new execution SSOT be opened.

## 9. 3-Pass Audit Record
Pass 1. Structure and Scope
- report type, scope, included lanes, and exclusions are explicit
- PASS

Pass 2. Evidence and Consistency
- source anchors match inspected code
- fresh-run claims are bounded to the operator-provided transcript
- no claim of full Stage 2/4 live parity is made without run evidence
- PASS

Pass 3. Execution and Readability
- findings are grouped by authority, sink, and regression type
- next step is explicit and bounded
- PASS

## 10. Confidence
Estimated confidence: `96%`

Reasoning:
- high confidence for Stage 0 and Stage 2 finalizer operator-surface findings
- high confidence for static authority/sink mapping in inspected Stage 2/4 lanes
- lower confidence only on unrun Stage 2/4 live parity, which is explicitly excluded from final claims
