# Partial-Fix Terminal 1 — Eval Harness / Measurement Surfaces Survey

Date: 2026-04-07
Status: final
Document Type: parallel terminal lane survey (read-only)
Canonical Path: `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
Temp Mirror Path: `(none - read-only lane survey; no docs/temp mirror per order §4.10/§4.12)`
Track: system
Mode: read-only parallel survey; no code patching; docs-only output
Lane: `partial-fix eval harness / measurement surfaces`
Operator Order: `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread docs, narrative artifacts, runtime/output deltas; lane is survey-only and does not mutate queue or code`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

What was read:

- order: `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
- governance: `AGENTS.md`, `docs/implementation/system-order-init-harness.md`,
  `docs/implementation/system-full-survey-execution-harness.md`,
  `docs/implementation/document-3pass-audit-harness.md`,
  `docs/implementation/commit-state-minimal-contract.md`
- parent context: `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`,
  `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`
- queue context: `docs/2026-04-01/active-temp-execution-roadmap.md`,
  `docs/temp/execution-roadmap.md`, `docs/temp/queue-state.json`
- queued partial-fix hardening SSOTs (ranks 9–11):
  - `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
  - `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
  - `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
- live code (canonical paths; the order's `modules/db/db_manager.py` resolves to
  the canonical `modules/core/db_manager.py` and `bridge_server.py` to
  `modules/api/bridge_server.py`):
  - `modules/core/stage2_finalizer.py`
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/db_manager.py`
  - `modules/core/failure_analyzer.py`
  - `modules/api/bridge_server.py`
  - `modules/core/stage4_canary_tools.py`

What was intentionally excluded:

- Stage4 fix-pack grammar / repair-contract redesign (parent lane scope)
- Stage2/3 broader contract normalization (parent lanes)
- live canary execution and post-run merge audit
- terminal 2 (shared patch address schema) and terminal 3 (operator before/after
  trace) lane content; cross-lane synthesis is the merge survey's job
- DB migrations or new tables; this survey only measures what existing sinks
  already carry

## 2. Findings

Ordered by severity. Each finding cites the smallest concrete owner surface.

### F1. Stage4 already records the substrate for three of the four target metrics; Stage2/3 do not.

- Stage4 `_record_s4_attempt` / `_save_stage4_db_attempt`
  (`modules/core/stage4_interview_round.py:7440-7475`, `:7486-7549`) writes
  `stage_attempts` rows with `attempt_key`, `attempt_num`, `is_patch`,
  `is_patch_fallback`, `patch_strategy`, `fix_scope`, plus `advisory_flags` JSON
  that carries the live `fix_pack` (`patch_targets`, `must_fix`,
  `do_not_regress`, `success_condition`, `target_kind`).
- `db_manager.save_stage_attempt` (`modules/core/db_manager.py:3129-3240`)
  persists all of those columns and serializes `advisory_flags` losslessly.
- Stage2 finalizer `_record_stage2_pass_attempt`
  (`modules/core/stage2_finalizer.py:3055-3166`) calls the same DB sink, but
  does **not** pass `is_patch`, `is_patch_fallback`, or `patch_strategy`. Only
  `fix_scope`, `attempt_key`, and `attempt_num` are recorded. There is no
  Stage2 `fix_pack` payload in `advisory_flags` because Stage2 has no
  fix-pack-lite contract yet.
- Stage3 `_run_pass_with_fix_iteration`
  (`modules/domain/agents/three_phase_blueprint_runtime.py:998-1163`) drives
  `_inplace_patch_blueprint` with one `re_slice_instruction` / `feedback`
  string and never calls a per-iteration DB sink with patch-mode flags. The
  outer Stage3 attempt write only carries `fix_scope`.

Consequence: today, Stage4 alone can compute `local hit rate`, `fallback to
partial/full`, and `same-(round) retry count`; Stage2/3 can only compute
`fallback to partial/full` from `fix_scope`. None of the three stages can
compute `do_not_regress violation rate` because no code path verifies the
`do_not_regress` clauses against the post-patch artifact.

### F2. `do_not_regress` exists only as contract text, not as a measurable event.

- `Stage4Round._normalize_fix_pack` /
  `_evaluate_fix_pack_contract` / `_build_fix_pack_payload`
  (`modules/core/stage4_interview_round.py:1999-2156`) require
  `do_not_regress` to be present and non-empty for fix-pack readiness, and
  preserve the list inside `advisory_flags.fix_pack`.
- The latest snapshot helper
  `db_manager.get_latest_stage4_gate_repair_snapshot`
  (`modules/core/db_manager.py:2851-3020`) and the bridge serializer
  `_build_gate_repair_summary` (`modules/api/bridge_server.py:1591-1689`) both
  expose `fix_pack.do_not_regress` to operator surfaces.
- No live code path executes a post-patch check that the `do_not_regress`
  guards still hold. The Stage4 hardening SSOT Tranche 3
  ("Post-Patch Targeted Verifier", lines 171–183) is the queued realization;
  Stage3 and Stage2 SSOT Tranche 3 mirror that.
- A `do_not_regress violation rate` therefore cannot be computed today even
  retrospectively from logs, because no boolean per-clause outcome is ever
  emitted to any sink.

### F3. `failure_analyzer.patch_trace_summary` is the closest existing aggregator and the cleanest extension point.

- `FailureAnalyzer.patch_trace_summary`
  (`modules/core/failure_analyzer.py:1858-1945`) already aggregates
  `episode_production` patch entries into:
  `count`, `structural_attempted_count`, `final_pass`, `final_reject`,
  `avg_unchanged_ratio`, `strategy_counts`, `fallback_reasons`,
  `focus_counts`, `top_patch_targets`.
- It is consumed by `stage4_canary_tools.run_stage4_canary` via
  `analyzer.patch_trace_summary()` (`modules/core/stage4_canary_tools.py:559`,
  `:601-642`) and its output is exposed in the canary summary JSON the
  operator already reads.
- Two of the four target metrics are already substantially derivable from
  this surface: `local hit rate` (`final_pass` over patch rows) and
  `fallback to partial/full` (`fallback_reasons`). It does not yet read the
  `stage_attempts.advisory_flags.fix_pack` payload, so it cannot count
  `same-target` retries or `do_not_regress` evidence.

### F4. `same-target retry count` needs a stable target identifier; only Stage4 carries one.

- `attempt_key` (`modules/core/logging_keys.build_attempt_key` used in
  `stage4_interview_round.py:507-509`, `:7336-7458`) is per-round, not
  per-target — multiple targets in one round share one attempt_key.
- Stage4 `fix_pack.patch_targets` and `target_kind` provide the only
  per-target labeling currently in production, and they are persisted only
  inside `advisory_flags` JSON on `stage_attempts`.
- Stage2/3 do not yet emit `patch_targets`; their `_inplace_patch_arc` /
  `_inplace_patch_blueprint` calls
  (`modules/core/stage2_finalizer.py:2300`, `:2607`;
  `modules/domain/agents/three_phase_blueprint_runtime.py:1040-1045`)
  receive a single feedback string. So `same-target retry count` is not even
  definable for Stage2/3 until queue ranks 9–10 deliver fix-pack-lite.

### F5. `director_selections` already gives the cheapest cross-stage `fix_scope` aggregator and is unused for Stage2/3 PWF intelligence.

- `db_manager.get_fix_scope_stats`
  (`modules/core/db_manager.py:3369-3379`) cross-tabs `fix_scope × verdict`
  over the most recent N `director_selections` rows.
- Stage2 finalizer (`stage2_finalizer.py:3144-3164`) and Stage4 record
  per-attempt `director_selections` rows with `fix_scope` populated; Stage3
  also populates the row through validator/runtime handoff.
- The Stage4 PWF eligibility helper at `stage4_interview_round.py:447-464`
  already calls `get_fix_scope_stats(lookback=200)` and consumes
  `inplace`-PASS rate as a runtime signal. No equivalent consumption exists
  for Stage2 or Stage3.
- Net: a Stage2/3 `fallback to partial/full` rate is already computable from
  the existing sink without any new instrumentation.

### F6. The "Python collects facts, LLM judges" rule narrows where new evaluation can live.

- Per `AGENTS.md` §대원칙 1: Python may aggregate facts, but the
  pass/fail/regress judgment must come from an LLM Director / Validator.
- This means the eval harness must stay on the **fact-aggregation side**:
  count rows, group by axis, compute ratios, expose the deltas. The actual
  per-clause `do_not_regress` violation decision must be produced by the
  Director/Validator inside the post-patch verifier (Tranche 3 of all three
  queued SSOTs) and only **persisted** by the harness.

## 3. Existing Coverage Check

### What is already covered by ranks 9–11

- Stage2 fix-pack-lite contract (`patch_targets`, `must_fix`, `do_not_regress`,
  `success_condition`, `target_kind`):
  Stage2 SSOT Tranche 1 (lines 124–138).
- Stage3 fix-pack-lite contract: Stage3 SSOT Tranche 1 (lines 128–142).
- Stage4 patch-address normalization (the same key set, already partially
  realized): Stage4 SSOT Tranche 1 (lines 145–158).
- Post-patch targeted verifier that produces an executable `must_fix` /
  `do_not_regress` / `success_condition` outcome: Tranche 3 of every queued
  SSOT (Stage4 lines 171–183, Stage3 lines 154–166, Stage2 lines 153–165).
- Patch exhaustion / repeated-attempt heuristics that depend on per-target
  identity: Tranche 4 of every queued SSOT.
- Richer patch traces and operator-visible patch decisions (the persistence
  side, not the aggregation side): Class B "Residual but related" of every
  queued SSOT.

### What is only implied, not explicit

- None of the three queued SSOTs explicitly own the **aggregation surface**
  for the four target metrics. Each SSOT names "richer patch telemetry" as a
  Class B residual, but the only existing computed surface is
  `failure_analyzer.patch_trace_summary` and no SSOT explicitly schedules
  extending it.
- None of the three SSOTs explicitly own the **persistence boolean** that the
  post-patch verifier must emit per `do_not_regress` clause. Tranche 3 names
  the verifier but does not specify the sink shape that the harness needs to
  count violations.
- `same-target retry count` is implied by Tranche 4 ("repeated failures on
  the same scene/path target") but no SSOT names the storage location for
  the per-target counter.

### What is still missing

- A small, single aggregation function that joins
  `stage_attempts` (per-attempt fix-pack and patch flags),
  `director_selections` (per-attempt `fix_scope`), and
  `episode_production.patch_trace` (per-attempt unchanged ratio /
  fallback reason) into the four target metrics keyed by `(stage, target)`.
- A bounded persistence shape that the Tranche-3 post-patch verifier can
  write to so the harness can count violations rather than re-derive them
  from text.
- A bounded same-target identifier that survives a single PWF round so the
  harness can compute retry counts without inventing a new identity scheme.

## 4. Minimal Contract Proposal

The proposal stays inside fact aggregation. Judgment stays with the
Director/Validator inside Tranche 3 of the queued SSOTs.

### 4.1 Sink shape (extension to existing `advisory_flags` only)

Inside the existing `advisory_flags` JSON column on `stage_attempts`, the
post-patch verifier (Tranche 3 of each queued SSOT) writes one bounded
sub-object — no new column, no new table:

```
advisory_flags.partial_fix_eval = {
  "patch_round":          int,           # 1-based PWF round number
  "is_patch_attempt":     bool,          # this attempt was an inplace patch
  "patch_target_id":      str,           # stable identifier within attempt_key
  "target_kind":          str,           # local | scene | section | field
  "must_fix_resolved":    bool | null,   # null until verifier ran
  "do_not_regress_held":  bool | null,
  "success_condition_met":bool | null,
  "fallback_reason":      str            # "" | "non_local_scope" | "no_fix_pack" | "patch_failed" | "verifier_reject"
}
```

Rules:

- Python writes the booleans only after the LLM verifier returns them. No
  Python heuristic ever sets `must_fix_resolved`, `do_not_regress_held`, or
  `success_condition_met`.
- `patch_target_id` must be deterministic from the upstream `fix_pack`
  (Stage4 already has `patch_targets`; Stage2/3 will once ranks 9–10 land).
- `fallback_reason` reuses the existing `failure_analyzer.patch_trace_summary`
  vocabulary so the aggregator does not invent new buckets.

### 4.2 Aggregator shape (extension to `failure_analyzer.patch_trace_summary`)

Add to the existing return dict — same function, same call site, same
canary summary consumer:

```
"partial_fix_eval": {
  "stage": int,
  "lookback": int,
  "local_hit_rate":               float,  # PWF rounds with must_fix_resolved=True / total PWF rounds
  "fallback_to_partial_or_full":  float,  # rounds with fix_scope in (partial,full) / total fix_scope rows
  "same_target_retry_avg":        float,  # mean rounds per (attempt_key, patch_target_id)
  "same_target_retry_p95":        int,
  "do_not_regress_violation_rate":float,  # rounds with do_not_regress_held=False / rounds with verifier ran
  "verifier_coverage":            float   # rounds with verifier ran / total PWF rounds
}
```

Rules:

- `verifier_coverage` exists explicitly so the operator can see how much of
  the headline rate is real vs unmeasured.
- All numerators and denominators come from a single SQL pass over
  `stage_attempts` filtered by `stage` and `is_patch=1`, plus a `LEFT JOIN`
  on `director_selections.fix_scope`. No new query family is introduced.
- Stage2/3 rows produce empty buckets until ranks 9–10 land; the function
  must degrade by returning `null` per metric rather than zero.

### 4.3 Operator surface

`stage4_canary_tools` already routes `patch_trace_summary` into the canary
summary JSON. The new `partial_fix_eval` block surfaces the same way with
zero new operator-facing plumbing. Bridge `_build_gate_repair_summary` may
later mirror it; out of scope for this lane.

## 5. Owner Verdict

Narrowest plausible owner set:

- **Persistence side (judgment-bearing booleans)**: the Stage4 post-patch
  verifier owner, then the Stage3 and Stage2 verifier owners. These are the
  Tranche-3 owners of the three queued SSOTs:
  - `modules/core/stage4_interview_round.py` (Stage4 verifier landing site)
  - `modules/domain/agents/three_phase_blueprint_runtime.py` (Stage3)
  - `modules/core/stage2_finalizer.py` (Stage2)
- **Same-target identifier emission**: the same fix-pack-lite owners, i.e.
  Tranche-1 of the Stage2 / Stage3 SSOTs and Tranche-1 of the Stage4 SSOT
  (already partly in place).
- **Aggregation surface**: a single owner — `modules/core/failure_analyzer.py`
  `FailureAnalyzer.patch_trace_summary`. No new file, no new module.
- **Operator readback**: no owner change. The existing
  `stage4_canary_tools.run_stage4_canary` consumer already publishes the
  field.

This means the eval harness has **zero net new owners** beyond owners already
holding queued ranks 9–11 work, plus one bounded extension to
`failure_analyzer`. The cleanest landing is to fold the analyzer extension
into the **Stage4** rank-9 SSOT (Stage4 Tranche 4 already covers "Patch
Exhaustion and Telemetry Hardening" — lines 185–195), because Stage4 already
owns the strongest substrate and the existing aggregator path.

## 6. Promotion Signal

`extend-rank9-11-stage-local-wave`

Reasoning, kept short:

- Three of the four metrics become computable as a downstream consequence of
  the substrate that ranks 9–11 already plan to ship (fix-pack-lite for
  Stage2/3, address normalization for Stage4, post-patch verifier for all
  three).
- The fourth metric (`do_not_regress violation rate`) is **only** meaningful
  after Tranche 3 of those queued lanes runs, because no current sink emits
  the per-clause boolean.
- The aggregator extension is small enough (one function in
  `failure_analyzer`) that creating a separate cross-stage execution lane
  for it would be heavier than the work itself.
- The natural home for the aggregator extension is **Stage4 SSOT Tranche 4**
  (telemetry hardening), with Stage2 and Stage3 SSOT Tranche 4 each emitting
  the `partial_fix_eval` sink object so the same aggregator works across
  stages. No new cross-stage lane is required.

This is **not** `covered-by-existing-queue` because the queued SSOTs do not
explicitly own the aggregator extension or the sink shape. It is **not**
`candidate-new-cross-stage-lane` because the gap is one bounded extension
inside an owner that already exists.

Recommended merge-survey action: ask the merge doc to record one
"`partial_fix_eval` sink and aggregator extension" line item against the
existing Stage4 Tranche 4, and one mirroring line item against Stage2 and
Stage3 Tranche 4. No new queue rank is needed.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
