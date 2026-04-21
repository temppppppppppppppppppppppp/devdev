# S2-S3-S4 Authority Alignment Parallel Deep-Dive 3-Pass Audit

Date: 2026-04-21
Status: final (adversarial 3-pass re-audited; parallel live-code and queue-surface deep dive completed against the current dirty head)
Canonical Path: `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md`
Commit State:
- Baseline Commit: `e9b45933c1e0ba1b61528f466e6b7415494a698b`
- Baseline Dirty Summary: `dirty: large existing workspace drift across canary/manual-backup/runtime/docs-temp trees; Stage3/Stage4 authority-lane files and tests already modified; no unrelated rollback performed`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD; this audit adds only the canonical survey doc and verification notes`
Source Survey Docs:
- `docs/2026-04-21/00_0420-s2-s3-s4-authority-alignment-3pass-audit.md`
- `docs/2026-04-21/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md`
- `docs/2026-04-21/stage3-authority-alignment-post-run-merge-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- `docs/2026-04-16/stage234-arc23-stage2-packet-fidelity-focused-3pass-audit.md`
Evidence Artifacts:
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/temp/clickup-sync-state.json`
- `docs/temp/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md`
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_interview_round.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_stage4_advisory_escalation_seam.py`
Side-Effect Coverage: covered (Stage2 packet emission, Stage3 packet consumption and repair-scope precedence, Stage4 intake/retry/post-select/post-pass seams, temp queue/controller metadata, targeted compile/pytest validation)
Confidence: `97%`

## 1. Intent

The user asked for a parallel deep-dive survey of the `S2 -> S3 -> S4` authority-alignment lane.

This audit answers five questions against the live workspace:

1. who currently owns cross-stage authority at each stage
2. whether the current 2026-04-21 authority-alignment SSOT still matches the live working tree
3. which unresolved seams are still structurally meaningful
4. whether the temp queue/controller surfaces still describe the live lane honestly
5. whether the newly added hardening tests are green on the dirty head

This audit is survey-only. No production code mutation was performed in this turn.

## 1A. Scope

Included:

- Stage2 cross-stage authority emission:
  - `modules/core/cross_stage_authority_packet.py`
  - `modules/core/stage2_finalizer.py`
- Stage3 packet consume and repair-scope precedence:
  - `modules/core/episode_state_arbiter.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - Stage3 repair-scope precedence surfaces
- Stage4 intake, post-select, retry, advisory, and post-pass surfaces:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_postselect_runtime.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_pass_runtime.py`
- temp queue / controller artifacts:
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`
  - `docs/temp/clickup-sync-state.json`
  - `docs/temp/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md`
- targeted compile / pytest verification for the touched authority lane

Excluded:

- fresh live rerun of `projects/00_0420`
- project artifact hand-editing
- broader Stage0 or narrative-pipeline remediation
- queue/controller mutation in this turn
- any production code patch beyond the already-existing live working-tree state being audited

## 2. Final Verdict

### Finding 1. The live authority-owner chain is coherent, but the current working tree has outgrown the active 2026-04-21 execution SSOT

Severity: high

The active execution SSOT for the `00_0420` lane still scopes the realized wave to:

- `UnifiedBlueprintValidator`
- `Stage4RetryRuntime`
- bounded supporting tests

That scope is no longer an honest description of the live authority lane.

The current dirty head also contains live Stage3 and Stage4 companion changes that materially affect authority routing:

- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_interview_round.py`
- supporting Stage3/Stage4 tests

Operational meaning:

- the authority-alignment lane is no longer just `validator + retry`
- the existing execution SSOT remains useful lineage, but it is now narrower than the live code reality
- any next implementation step should treat the current lane as a broader cross-stage working tree than the canonical SSOT text currently says

### Finding 2. The dominant problem is split-owner coordination, not missing ownership

Severity: high

The owner map is real and reasonably crisp:

- Stage2 emission owner:
  - `Stage2Finalizer`
- Stage3 consume/arbiter owners:
  - `BlueprintConstraintCompiler`
  - `EpisodeStateArbiter`
  - `_Stage3RepairRouter` for fix-scope precedence
- Stage4 owners by concern:
  - intake/prioritization: `Stage4ContextBuilder`
  - post-select contradiction shaping: `Stage4PostSelectRuntime`
  - retry suppression/routing: `Stage4RetryRuntime`
  - settlement/persistence: `Stage4PostPassRuntime`
  - advisory/local-fix synthesis: `Stage4InterviewRound`

So the lane is not suffering from “nobody owns authority.”

It is suffering from cross-owner seams where:

- one owner emits a narrow transport contract
- another owner silently falls back when that contract is absent or stale
- a third owner reinterprets the same authority family for retry or persistence

Operational meaning:

- the next risks are at the seams, not at the existence of owners
- surveys and SSOTs should describe the seam owners together, not only one module at a time

### Finding 3. The highest-value unresolved seams are silent fallback or split-contract surfaces, not the already-covered packet basics

Severity: high

Confirmed unresolved seams:

- Stage3 packet-version fallback is silent:
  - packet acceptance is version-gated, but mismatch falls back without an explicit contradiction record
- Stage4 numeric transport is asymmetric:
  - a mixed `fact_ledger + disjoint packet-only numeric fields` case can lose transport information without a dedicated contradiction surface
- Stage4 still carries an acknowledged `missing_semantic_carryover` seam:
  - the handoff is recognized, not guaranteed
- `previous_attempt` ownership is split:
  - `Stage4PostSelectRuntime` shapes it
  - `Stage4RetryRuntime` consumes it
  - `Stage4InterviewRound` also persists and logs it

Operational meaning:

- packet emission/consumption is not the weakest part anymore
- the weaker surfaces are silent downgrade rules and cross-owner contract handoffs

### Finding 4. The temp queue/controller surfaces are not fully aligned with the live temp surface

Severity: medium

`docs/temp/00_0420-s2-s3-s4-authority-alignment-remediation-execution-ssot.md` explicitly says:

- the temp mirror exists because this lane is active now
- it is a user-directed immediate lane
- it should not be blocked on the parked roadmap

But the controller surfaces still describe only the parked aggregate board:

- `docs/temp/execution-roadmap.md` says the board is in parked mode with no honest front-active implementation lane
- `docs/temp/queue-state.json` still reports `generated_at = 2026-04-20T10:26:38.559384+00:00`, `active_item_count = 7`, and does not include the `00_0420` lane
- `docs/temp/clickup-sync-state.json` still reports `updated_at = 2026-04-20T10:26:56.370162+00:00` and mirrors that parked-only queue state

This may be intentional as an operator override, but it is still a real controller drift:

- the live temp directory contains one more execution artifact than the machine-readable queue admits

### Finding 5. The newly added Stage3/Stage4 authority hardenings are locally coherent on the dirty head

Severity: medium

The new guardrail tests that correspond to the live dirty changes passed in sequence:

- `tests/test_unified_blueprint_validator_lane_c.py`
  - `4 passed, 42 deselected`
- `tests/test_stage4_interview_round.py`
  - `3 passed, 313 deselected`
- `tests/test_stage4_advisory_escalation_seam.py`
  - `1 passed, 32 deselected`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
  - `6 passed, 39 deselected`

`python -m py_compile` also passed for the touched Stage3/Stage4 production files inspected in this survey.

Operational meaning:

- the current live hardenings are not obviously broken at the targeted-test level
- this raises confidence in the local code shape
- it does not erase the scope-drift and queue-drift findings above

## 3. Pass 1. Live Inventory

### 3.1 Stage2 emission surface

Stage2 authority is emitted through `Stage2Finalizer`, not through `main_a.py` or the Stage2 orchestrator shell.

The canonical transport payload is `cross_stage_authority_packet` with:

- `opening_carryover`
- `protagonist_carryover`
- `numeric_carryover`
- `source_precedence`
- `provenance`

The packet is built from:

- `state_constraints.arc_end_state`
- `state_constraints.investment_calc`
- `joint_docs`

Stage2 also emits a separate carryover summary sidecar into observability/UI/DB paths.

Inventory judgment:

- Stage2 does have a real canonical packet contract
- but it also still emits auxiliary summary surfaces beside it

### 3.2 Stage3 consume surface

Stage3 consumes packet truth in two layers:

- `BlueprintConstraintCompiler` builds and hands off the Stage3-local packet context
- `EpisodeStateArbiter` resolves opening/protagonist/time/numeric truth into `episode_state_packet`

Live working-tree observations:

- arc-opening precedence now prefers Stage2 arc-start truth more aggressively
- mid-arc opening can also consume current-episode tactical start location
- opening-transition expectation now reacts to time-cut as well as location-shift
- tests were added to cover these newer precedence rules

Inventory judgment:

- Stage3 is no longer merely packet-first in the old 4/14 sense
- it now contains a stronger arc-start and tactical-start arbitration layer than the current 4/21 execution SSOT text mentions

### 3.3 Stage4 consume/reuse surface

Stage4 authority is split by concern:

- context intake:
  - `Stage4ContextBuilder`
- post-select contradiction classification:
  - `Stage4PostSelectRuntime`
- retry suppression/reuse:
  - `Stage4RetryRuntime`
- advisory local-fix synthesis:
  - `Stage4InterviewRound`
- settlement/persistence:
  - `Stage4PostPassRuntime`

Live working-tree observations:

- retry duplicate suppression now refuses automatic reuse bypass for rewrite-required continuity/history conflicts
- PASS_WITH_FIX re-audit now snapshots and clears stale advisory caches before re-normalizing director semantics
- interview-round logic now synthesizes a separate `npc_drift relation_to_protag` local-fix contract

Inventory judgment:

- Stage4 is materially broader than the active execution SSOT summary
- the current dirty head is already addressing multiple Stage4 authority seams at once

### 3.4 Queue/controller surface

Live queue inventory:

- parked aggregate roadmap still exists and is active as a controller artifact
- parked queue-state/clickup mirrors still exclude the `00_0420` lane
- live temp execution mirror for `00_0420` exists anyway and describes itself as active

Inventory judgment:

- canonical queue/controller state and live temp artifact state are not fully synchronized

## 4. Pass 2. Semantic Classification

### 4.1 Stable authority contracts

These surfaces look structurally stable on the current head:

- Stage2 packet emission owner is still `Stage2Finalizer`
- Stage3 packet consume owner is still `EpisodeStateArbiter`
- Stage4 post-pass numeric authority still resolves through `state_truth_owner_contract`
- targeted tests around the new hardenings are green

### 4.2 Drift between canonical execution contract and live code

This is the most important classification result.

The active 2026-04-21 execution SSOT currently describes a bounded wave centered on:

- `UnifiedBlueprintValidator`
- `Stage4RetryRuntime`

But the live dirty head now also includes:

- Stage3 arbiter precedence changes
- Stage3 time-cut/opening-transition changes
- Stage4 interview-round local-fix synthesis changes
- broader Stage3/Stage4 test updates than the SSOT names

This is not evidence that the code is wrong.

It is evidence that:

- the live remediation wave has widened past the current documented execution boundary

### 4.3 Residual silent-fallback seams

The strongest residual seams are:

- Stage3 silent version-fallback
- Stage4 disjoint numeric transport asymmetry
- Stage4 `missing_semantic_carryover`
- Stage4 `previous_attempt` split ownership

These are the next seams that still deserve structural attention after the already-landed hardenings.

### 4.4 Controller drift classification

The queue/controller mismatch is best classified as:

- operator-intent-visible but machine-state-underreported

That is less severe than a broken canonical source file, but still important because temp queue artifacts are meant to guide later work honestly.

## 5. Pass 3. Verification Audit

### 5.1 Commands run

- `python -m py_compile modules/domain/agents/unified_blueprint_validator.py modules/core/stage4_retry_runtime.py modules/core/episode_state_arbiter.py modules/core/stage4_interview_round.py modules/domain/agents/blueprint_constraint_compiler.py`
- `pytest tests/test_unified_blueprint_validator_lane_c.py -q -k "work_identity_opening_drift_for_multi_location_partial_progression or authorized_scene1_time_cut_without_replay_false_positive or lawful_repetition_when_execution_rotates_same_room or arc_timeline_preserves_same_month_day_window_for_non_terminal_episode"`
- `pytest tests/test_stage4_interview_round.py -q -k "duplicate_suppression_does_not_auto_bypass_for_rewrite_required_post_select_reuse_contract or duplicate_suppression_still_bypasses_for_bounded_local_fix_reuse_contract or run_pass_with_fix_reaudit_does_not_reuse_stale_strong_advisory_cache"`
- `pytest tests/test_stage4_advisory_escalation_seam.py -q -k "relation_to_protag_npc_drift"`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q -k "prefers_arc_start_truth_when_arc_opening_packet_conflicts or uses_arc_start_truth_on_arc_opening_when_packet_missing or reflects_arc_opening_stage2_priority_in_source_precedence or surfaces_arc_opening_transition_expectation_on_time_cut or episode_progression_lawful_repetition_window_detects_execution_rotation_tokens or prefers_current_episode_tactical_start_location_mid_arc"`

### 5.2 Results

- compile: pass
- validator shard: `4 passed, 42 deselected`
- Stage4 retry shard: `3 passed, 313 deselected`
- Stage4 advisory seam shard: `1 passed, 32 deselected`
- Stage3 packet shard: `6 passed, 39 deselected`

### 5.3 UTF-8 / hygiene note

Explicit UTF-8 byte reads succeeded for the files inspected in this survey.

`python scripts/check_utf8_hygiene.py` on the multi-file batch failed on `modules/core/episode_state_arbiter.py`, but the reported hits were regex lines containing literal `?` quantifiers rather than a proven decode failure.

Exact reported lines:

- `modules/core/episode_state_arbiter.py:396`
- `modules/core/episode_state_arbiter.py:418`

Current best read:

- treat that batch failure as a hygiene-checker false-positive candidate for this audit
- do not treat it as proof of source corruption without a narrower checker pass or rule update

This is an inference from byte-level decode plus the exact failure lines.

## 6. Next-Step Shape

If the user later wants implementation to continue, the honest next operating shape is:

1. refresh or supersede the current 2026-04-21 execution SSOT so it matches the widened live Stage3/Stage4 lane
2. decide whether the queue/controller surfaces should formally reflect the `00_0420` immediate lane or keep it as an explicit operator override
3. if the queue/controller decision is made and code work continues after that, prioritize the still-open seam class:
   - Stage4 split-owner `previous_attempt` contract
   - Stage4 disjoint numeric transport asymmetry
   - Stage3 packet-version fallback visibility
   - Stage4 `missing_semantic_carryover`

## 7. 3-Pass Notes

Pass 1:

- established the live owner map across Stage2, Stage3, Stage4, and temp queue surfaces

Pass 2:

- classified the main issue as execution-SSOT drift plus split-owner seam debt, not missing owner debt

Pass 3:

- confirmed the current dirty-head hardenings compile and their targeted tests pass in low-memory sequential shards

Adversarial re-audit delta:

- Pass 1 tightened the document by adding an explicit included/excluded scope block
- Pass 2 tightened evidence anchors for queue/controller drift and the hygiene-checker false-positive note
- Pass 3 narrowed the follow-up order so documentation/controller refresh stays ahead of further code expansion
