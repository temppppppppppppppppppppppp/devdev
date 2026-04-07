# Partial-Fix Hardening Parallel Merge Survey

Date: 2026-04-07
Status: final
Document Type: merged survey audit
Canonical Path: `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`
Temp Mirror Path: `(none - merge-only survey; no docs/temp mirror)`
Track: system
Mode: read-only merge survey; no code patching; no queue mutation
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread docs, narrative artifacts, runtime/output deltas; three partial-fix terminal survey docs landed under docs/2026-04-07`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
- `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
- `docs/2026-04-07/partial-fix-terminal3-operator-before-after-trace-survey.md`
Side-Effect Coverage: inherited from the three source survey docs; this merge turn added no live-run evidence and performed no side-effect sweep beyond source-doc consolidation
Confidence: `97%`

## 1. Coverage

This merge survey consolidates the three bounded lane docs created by:

- `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`

Included:

- `partial-fix eval harness` findings
- `shared patch address schema` findings
- `operator-facing before/after trace` findings
- queue coverage checks against:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
  - `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
  - `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
  - `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`

Excluded:

- code patching
- `docs/temp/` mutation
- queue reordering
- new execution SSOT creation
- fresh canary or live-run evidence

Convergence result:

- no material contradiction was found across the three lane docs
- all three lanes converge on `extend-rank9-11-stage-local-wave`
- no lane justifies `candidate-new-cross-stage-lane`
- queue ranks `9-11` already provide the right execution homes, but they are not explicit enough as written

## 2. Findings

### F-1. No new queue rank is justified; the real gap is missing explicit contract text inside existing ranks `9-11` (severity: high, class: queue-coverage verdict)

All three lanes converge on the same queue conclusion:

- Terminal 1 concludes the eval harness gap is a bounded sink and aggregator extension that belongs under the existing partial-fix hardening waves, not a new lane.
- Terminal 2 concludes the schema gap is a thin shared dependency consumed by the existing Stage2/3/4 partial-fix waves, not a separate cross-stage execution rank.
- Terminal 3 concludes the before/after trace is a Stage4-local extension under the existing Stage4 partial-fix wave, not a cross-stage observability lane.

Converging source findings:

- Terminal 1 `## 6. Promotion Signal`
- Terminal 2 `## 6. Promotion Signal`
- Terminal 3 `## 6. Promotion Signal`

Queue mapping:

- `0_0-stage4-partial-fix-hardening-remediation`
- `0_0-stage3-partial-fix-hardening-remediation`
- `0_0-stage2-partial-fix-hardening-remediation`

Verdict:

- the queue is sufficient in **topic coverage**
- the queue is insufficient in **explicit contract detail**
- the right action after this merge is later execution-doc expansion inside ranks `9-11`, not new queue creation

### F-2. Shared patch-address normalization is the only thin cross-stage dependency, but it is still better handled as a dependency of ranks `9-11` than as its own lane (severity: high, class: cross-stage dependency)

Terminal 2 isolates the cleanest cross-stage substrate:

- Stage4 already has the strongest patch-target envelope via `fix_pack` in `modules/core/stage4_interview_round.py`.
- Stage3 already has a natural scene-keyed container and can share `scene_id` semantics with Stage4.
- Stage2 is dict-first and needs `field_path` style addressing rather than Stage4 text anchors.

The missing piece is therefore not a new runtime family.
It is one thin shared schema authority that pins:

- `patch_targets` as structured records rather than `list[str]`
- a stage-aware `target_kind` enumeration
- universal vs stage-conditional address fields
- the shared meanings of `scene_id`, `field_path`, and `text_anchor`

Converging source findings:

- Terminal 2 `F1-F6`
- Terminal 1 `### What is already covered by ranks 9-11` and `### What is still missing`
- Terminal 3 `Already covered by ranks 9-11` and `Still missing`

Primary owner files:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/four_phase_arc_generator.py`

Queue mapping:

- Stage4 rank `9` Tranche 1 as schema authority anchor
- Stage3 rank `10` Tranche 1-2 as consumer of the shared record
- Stage2 rank `11` Tranche 1-2 as consumer of the shared record

Merged verdict:

- this theme is **not already covered as written**
- this theme does **not** need a new rank
- this theme needs one explicit shared-schema dependency added to the existing ranks

### F-3. The eval harness is missing one explicit sink shape and one explicit aggregator extension, not a new measurement lane (severity: high, class: stage-local extension with cross-stage consumers)

Terminal 1 shows that the Stage4 substrate already carries most of the needed measurement facts:

- `stage_attempts` already stores `fix_scope`, `is_patch`, `is_patch_fallback`, `patch_strategy`, and `advisory_flags.fix_pack`
- `director_selections` already supports `fix_scope` aggregation
- `failure_analyzer.patch_trace_summary` already computes patch-level aggregate metrics and already feeds `stage4_canary_tools`

What is still missing is narrow:

- one bounded `advisory_flags.partial_fix_eval` sink shape
- one bounded `failure_analyzer.patch_trace_summary.partial_fix_eval` extension
- one stable `patch_target_id`
- one boolean persistence contract for `must_fix_resolved`, `do_not_regress_held`, and `success_condition_met`

Converging source findings:

- Terminal 1 `F1-F6`
- Terminal 2 `### 3.3 Still missing`
- Terminal 3 `findings 5-8`

Primary owner files:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `modules/core/stage4_canary_tools.py`

Queue mapping:

- Stage4 rank `9` Tranche 4 for the aggregator anchor
- Stage4/3/2 Tranche 3 for verifier-produced booleans
- Stage4/3/2 Tranche 4 for mirrored sink emission and retry telemetry

Merged verdict:

- Stage4 remains the anchor owner because it already has the strongest substrate and the existing aggregator path
- Stage2/3 should emit the same bounded sink object once their queued fix-pack-lite and verifier tranches land
- no new eval-harness rank is needed

### F-4. Operator before/after trace is real but Stage4-local; it should not be mislabeled as a cross-stage observability wave (severity: medium-high, class: Stage4-local extension)

Terminal 3 is the clearest lane on scope:

- Stage4 already has local-edit operations containing `old_text`, `new_text`, `anchor_before`, `anchor_after`, but drops them before persistence.
- Stage4 structural patch already has pre-/post-block text in scope, but does not capture it into the trace.
- the bridge readback already exposes `fix_pack`, `repair_contract`, `scope_authority`, and related metadata, but never the actual textual change or `guard_result`.
- Stage2/3 currently do not have analogous `old_text` / `new_text` substrates because their PWF loop is still instruction-string driven.

That means the missing operator trace is:

- a Stage4 `repair_trace[]` schema
- one producer extension
- one persistence pass-through
- one bridge widening

Converging source findings:

- Terminal 3 findings `1-9`
- Terminal 1 `### What is only implied, not explicit`
- Terminal 2 `### 3.2 Implied but not explicit`

Primary owner files:

- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/db_manager.py`
- `modules/api/bridge_server.py`

Queue mapping:

- Stage4 rank `9` Tranche 3 for truthful `guard_result`
- Stage4 rank `9` Tranche 4 for `repair_trace[]` schema, persistence, and readback widening

Merged verdict:

- this theme is not cross-stage in execution ownership
- it belongs under Stage4 rank `9`
- Stage2/3 should not be forced into a fake shared trace contract until they have real before/after substrates

## 3. Theme Classification

Per the operator order, each theme is classified as follows:

- `partial-fix eval harness`
  - classification: `stage-local-extension-needed`
  - merge verdict: extend Stage4 rank `9` Tranche 4 with the aggregator anchor, and mirror the sink contract under Stage3 rank `10` and Stage2 rank `11`
- `shared patch address schema`
  - classification: `stage-local-extension-needed`
  - merge verdict: add one shared schema dependency / Tranche 0 style reference consumed by ranks `9-11`; do not open a new queue rank
- `operator-facing before/after trace`
  - classification: `stage-local-extension-needed`
  - merge verdict: extend Stage4 rank `9` only; do not pretend this is cross-stage before Stage2/3 have a real before/after substrate

None of the three themes is `already-covered` as written.
None of the three themes is `new-cross-stage-lane-needed`.

## 4. Queue Sufficiency Verdict

Queue ranks `9-11` are sufficient as execution homes, but they need later execution-doc expansion before implementation starts.

Minimum later expansions implied by this merge:

1. Add one shared `PatchTargetRecord` reference and stage-aware `target_kind` enumeration as a dependency consumed by ranks `9-11`.
2. Add one bounded `advisory_flags.partial_fix_eval` sink shape to the later Tranche-3/4 realization of ranks `9-11`.
3. Add one bounded `failure_analyzer.patch_trace_summary.partial_fix_eval` extension under Stage4 rank `9`.
4. Add one Stage4 `repair_trace[]` schema plus bridge readback widening under Stage4 rank `9`.

What this merge does **not** justify:

- a new queue topic slug
- a new temp execution item
- a new standalone cross-stage execution SSOT
- queue reprioritization ahead of the current active front

## 5. Owner Verdict

Narrowest plausible owner set by theme:

- `partial-fix eval harness`
  - anchor owner: `modules/core/failure_analyzer.py`
  - sink/verifier owners: `modules/core/stage4_interview_round.py`, `modules/domain/agents/three_phase_blueprint_runtime.py`, `modules/core/stage2_finalizer.py`
- `shared patch address schema`
  - schema authority anchor: `modules/core/stage4_interview_round.py`
  - direct Stage4 consumers: `modules/domain/agents/chief_writer_inplace_local_ops.py`, `modules/domain/agents/chief_writer.py`
  - later Stage3/2 consumers: `modules/domain/agents/three_phase_blueprint_runtime.py`, `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/core/stage2_finalizer.py`, `modules/domain/agents/four_phase_arc_generator.py`
- `operator-facing before/after trace`
  - producer owners: `modules/domain/agents/chief_writer_inplace_local_ops.py`, `modules/domain/agents/chief_writer.py`
  - persistence/readback owners: `modules/core/stage4_interview_round.py`, `modules/core/db_manager.py`, `modules/api/bridge_server.py`

Merged owner principle:

- Stage4 remains the anchor substrate for all three themes
- Stage3 and Stage2 are downstream consumers for schema and eval-sink alignment
- only the operator trace theme remains truly Stage4-local

## 6. Promotion Signal

Overall merge verdict:

- `stage-local-extension-needed`

Meaning:

- expand the existing queued ranks `9-11`
- do not create a new queue rank
- do not treat this merge survey as an execution SSOT

## 7. 3-Pass Audit Record

### Pass 1. Structure and Scope

- merged only the three lane survey docs named in the operator order
- stayed read-only and did not touch code, temp mirrors, or queue files
- answered the order's required merge questions:
  - theme classification
  - queue sufficiency
  - narrowest owner set
  - whether a new lane is needed

### Pass 2. Evidence and Consistency

- verified that all three source docs exist under `docs/2026-04-07/`
- cross-checked all three promotion signals; they converge on extending existing ranks `9-11`
- cross-checked queue context against `docs/2026-04-01/active-temp-execution-roadmap.md`
- retained only claims that were supported by at least one lane doc and contradicted by none

### Pass 3. Execution and Readability

- reduced the merge verdict to one actionable queue statement: `ranks 9-11 are sufficient, but need explicit later expansion`
- separated the three themes cleanly so future execution-doc updates can be applied without inventing a new topic slug
- kept the document survey-only and stopped before execution planning or queue mutation

## 8. Stop

read-only merge survey complete; no files mutated outside docs/2026-04-07 canonical survey outputs
