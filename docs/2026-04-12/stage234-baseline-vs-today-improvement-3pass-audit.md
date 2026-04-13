# Stage234 Baseline-Vs-Today Improvement 3-Pass Audit

Date: 2026-04-12
Status: final
Canonical Path: `docs/2026-04-12/stage234-baseline-vs-today-improvement-3pass-audit.md`
Doc Type: pre-run improvement audit
Scope: current uncommitted Stage2-Stage4 tranche versus baseline commit `2b7cb64f`, asking whether today's changes are a net improvement before snapshot and fresh run
Commit State:
- Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Baseline Dirty Summary: `dirty: 26 tracked, 2 untracked within audited S2-S4 tranche; broader workspace also has unrelated docs/material-side drift`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none; this audit evaluates the current dirty tranche directly against the baseline commit because HEAD itself remains unchanged`
Source Survey Docs:
- `docs/2026-04-11/stage234-pre-fresh-run-global-parallel-3pass-audit.md`
- `docs/2026-04-11/stage2-stage4-p2-tranche-3pass-audit.md`
- `docs/2026-04-11/stage23-live-workspace-static-parallel-survey.md`
- `docs/2026-04-11/stage34-live-workspace-static-parallel-roadmap-validity-survey.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_episode_logging.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_raw_evidence.py`
- `modules/core/failure_analyzer.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/director_continuity.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- directly aligned touched tests listed in Verification Basis
Side-Effect Coverage: static code, structured sink, raw evidence, audit summary, and targeted regression surfaces covered; fresh runtime/DB truth remains intentionally out of scope until the next run

## 1. Question

Compared with the current commit baseline `2b7cb64f`, is today's uncommitted Stage2-Stage4 tranche actually a net improvement, or did the workspace only accumulate more code and tests without increasing trust?

## 2. Verification Basis

Diff scope captured during this audit:

- audited dirty tranche: `26 tracked + 2 untracked`
- touched files inside audited tranche: `28`
- git diff footprint across audited tranche: `8518 insertions / 1245 deletions`

Commands run during this audit:

- `git diff --stat -- <audited S2-S4 tranche>`
- `python -m py_compile <audited S2-S4 tranche>`
- `python -m ruff check <audited S2-S4 tranche>`
- `python scripts/check_utf8_hygiene.py <audited S2-S4 tranche>`
- `pytest tests/test_stage2_finalizer.py tests/test_stage2_orchestrator_lane_f.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `pytest tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_handle_success_lane_c.py tests/test_stage3_blueprint_state_precision_guardrail.py tests/test_stage3_clarity_density_wave1.py tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_patch_mode.py tests/test_director_auditor_pre_llm_lane.py tests/test_arc_noise_fixes.py tests/test_stage3_director_compare_advisory_lane.py -q`
- `pytest tests/test_stage4_interview_round.py -k "contract_packet or session_decision or save_stage4_db_attempt or record_stage4_pass_rate or feedback_provenance or selection_advisory or director_selection or selection_rationale" -q`
- `pytest tests/test_stage4_interview_round.py -k "pass_episode_log or reject_episode_log or round_outcome_trace_payload or reject_retry_contract_projection or retry_pathology_projection or raw_rationale_record or selection_surface_raw or raw_advisory_payload_bundle" -q`
- `pytest tests/test_failure_analyzer.py -q`
- targeted AST recount for `Stage2Finalizer`, `Stage2Orchestrator`, `Stage3Orchestrator`, `Stage4InterviewRound`, `FailureAnalyzer`

Observed results:

- static checks: pass
- targeted pytest shards: `89 + 248 + 32 + 32 + 46 = 447 passed`
- no touched-area test failed under the current dirty tranche

## 3. Answer First

Yes: compared with baseline `2b7cb64f`, today's Stage2-Stage4 tranche is a real net improvement.

That answer is bounded, not euphoric:

- it is a **static and targeted-regression** improvement, not yet a runtime-proven improvement
- it materially improves contract normalization, observability, retry metadata continuity, and post-run auditability
- it does **not** reduce structural complexity everywhere; some owner-surface pressure is worse, especially in `FailureAnalyzer`

Working judgment:

- net improvement: `yes`
- ship-ready without fresh run: `no`
- right next step: `snapshot -> fresh run -> post-run merge audit`

## 4. Pass 1 Audit

### 4.1 Scope coherence

The diff is large, but it is not random. It clusters into four coherent families:

1. Stage2 carryover and advisory truth
2. Stage3 director-first + typed repair-contract flow
3. Stage4 contract/evidence/raw-rationale convergence
4. FailureAnalyzer auditability upgrades so the new Stage4 evidence can actually be verified

### 4.2 Improvement thesis

The tranche is trying to do one thing:

- make Stage3/Stage4 contract-bearing data less free-text and less sink-specific
- make post-run explanation and audit evidence more trustworthy

That thesis is internally coherent across the touched files and tests.

## 5. Pass 2 Audit

### 5.1 Stage2 is better than baseline

Stage2 did not just gain more output. It gained stronger truth propagation.

- tactical `[시작 상태]` sync now carries the same finance truth as structured `arc_start_state`
  - `modules/core/stage2_finalizer.py:210`
  - `modules/core/stage2_finalizer.py:241`
- runtime advisory fallback remains explicit and centralized
  - `modules/core/stage2_finalizer.py:1120`
- UI `ep_num` semantics stay normalized while preserving `current_ep_start`
  - `modules/core/stage2_orchestrator.py:1217`
  - `modules/core/stage2_orchestrator.py:1259`

Net effect versus baseline: less Stage2 truth drift between structured state, tactical text, and observability surfaces.

### 5.2 Stage3 is better than baseline

Stage3 improved in three concrete ways.

1. success/failure sink assembly is more unified
   - `modules/core/stage3_orchestrator.py:43`
   - `modules/core/stage3_orchestrator.py:2116`
2. repair semantics are now preserved as typed payloads rather than only incidental strings
   - `modules/core/stage3_orchestrator.py:2383`
   - `modules/core/stage3_orchestrator.py:2776`
   - `modules/domain/agents/unified_blueprint_validator.py:685`
   - `modules/domain/agents/three_phase_blueprint_runtime.py:1296`
3. `PASS_WITH_FIX` is treated more consistently as a success-path concept
   - `modules/core/stage3_orchestrator.py:2265`
   - `modules/domain/agents/three_phase_blueprint_runtime.py:1756`

Net effect versus baseline: less contract loss between validator, runtime, orchestrator, and sink writes.

### 5.3 Stage4 is much more auditable than baseline

This is the biggest improvement area.

Stage4 now has stronger shared contract surfaces:

- attempt contract packet and projections
  - `modules/core/stage4_interview_round.py:239`
  - `modules/core/stage4_interview_round.py:445`
  - `modules/core/stage4_interview_round.py:478`
- reject retry/pathology projections
  - `modules/core/stage4_reject_runtime.py:161`
  - `modules/core/stage4_outcome_runtime.py:26`
- centralized feedback provenance and episode-log carryover surfaces
  - `modules/core/stage4_episode_logging.py:153`

Stage4 also now leaves raw evidence that is substantially easier to reconstruct later:

- raw evidence decoder/projector substrate
  - `modules/core/stage4_raw_evidence.py:112`
  - `modules/core/stage4_raw_evidence.py:160`
  - `modules/core/stage4_raw_evidence.py:257`
- selection/raw/reject/pathology records now share a clearer storage vocabulary
  - `modules/core/stage4_interview_round.py:539`
  - `modules/core/stage4_reject_runtime.py:71`
  - `modules/core/stage4_outcome_runtime.py:59`

Net effect versus baseline: Stage4 is not just producing more metadata; it is producing metadata that has a better chance of being cross-checked and understood after the fact.

### 5.4 FailureAnalyzer is much stronger than baseline

This is where today's tranche most clearly improves trust.

Before, Stage4 raw evidence could exist without a strong summary layer proving whether it agreed with structured sinks.
Now:

- raw rationale rows are summarized into kinds, families, surfaces, and projections
  - `modules/core/failure_analyzer.py:32`
- raw rationale health and watchlists are computed
  - `modules/core/failure_analyzer.py:126`
  - `modules/core/failure_analyzer.py:186`
  - `modules/core/failure_analyzer.py:292`
- whole sink alignment now exposes top issue headlines and operator summaries
  - `modules/core/failure_analyzer.py:383`
  - `modules/core/failure_analyzer.py:426`
  - `modules/core/failure_analyzer.py:2840`

Net effect versus baseline: the workspace is materially better at explaining and auditing itself.

### 5.5 Targeted regression evidence supports the improvement claim

Current green anchors are not hand-wavy:

- Stage2 touched tests: `89 passed`
- Stage3 touched tests: `248 passed`
- Stage4 touched shards: `32 + 32 passed`
- FailureAnalyzer touched tests: `46 passed`

For this audit question, that is strong evidence that today’s tranche is not just conceptual cleanup.

## 6. Pass 3 Audit

### 6.1 What improved

The best concise description is:

- baseline commit had weaker sink continuity, weaker raw evidence structure, and weaker post-run explainability
- today’s tranche gives the system a better chance of surviving a real proof wave without “we have the evidence but can’t trust or read it” failure modes

### 6.2 What did not improve

This is not a pure win:

- `FailureAnalyzer` is structurally heavier than before
  - `77` direct methods / `4` `120+` / `2` `180+`
  - top hotspots:
    - `_build_sink_alignment_summary_payload` `286`
    - `_collect_sink_alignment_raw_rationale_results` `281`
- `Stage4InterviewRound` remains structurally heavy
  - `166` direct methods / `5` `120+` / `2` `180+`

So the tranche improves truth and auditability more than it improves shape.

### 6.3 Practical judgment

If the question is:

- "did today's work improve the system?" -> `yes`
- "is the improvement already proven in runtime?" -> `no`
- "should we keep coding before proof?" -> `probably no`

## 7. Residual Risks

1. diff size alone raises review risk
   - `8518 insertions / 1245 deletions` is large enough that runtime proof is mandatory
2. Stage4 full-file regression was not used as the primary anchor
   - targeted shards passed
   - a whole-file `tests/test_stage4_interview_round.py -q` run timed out earlier, so this audit relies on bounded shards rather than a single monolithic pass
3. governing docs and queue bookkeeping are still stale relative to live code
   - this audit is intentionally documentation-first and does not close that drift yet

## 8. Conclusion

Compared with baseline commit `2b7cb64f`, today's Stage2-Stage4 tranche is a real improvement.

The strongest gains are:

- better contract preservation
- better sink continuity
- better raw evidence structure
- better operator-facing audit summaries

The strongest caveats are:

- structural debt remains high
- diff volume is large
- runtime truth is still unproven

Recommended next step:

1. save this audit result
2. save the separate adversarial audit
3. snapshot commit
4. run the expensive fresh run once
5. decide closure only after merged post-run audit

Confidence: `96%`
