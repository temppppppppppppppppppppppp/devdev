# Pre-Rerun Root-Cause Fix Cluster Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md`
Temp Mirror Path: `docs/temp/pre-rerun-root-cause-fix-cluster-execution-ssot.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty: active 2026-03-23 survey docs and reports, stage3_orchestrator.py, director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json, docs/2026-03-23/console.txt, projects/0_0323/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md`
- `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/project_data.db`
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/artifacts/stage3/**`
- `projects/0_0323/logs/artifacts/stage4/**`
- `projects/0_0323/plans/blueprints/**`
- `projects/0_0323/drafts/**`
Side-Effect Coverage: covered

## 1. Intent
- Realize the bounded pre-rerun fix cluster identified by the merge audit.
- Remove the two proven retry-storm blockers and the highest-ROI Stage 4 retry-fidelity defect before the next fresh run.
- Keep Director sovereignty, post-select downgrade semantics, and current DB/console max-retention work intact.

## 2. Baseline Facts
- The merge audit ranked three pre-rerun fix clusters:
  - Python scene-completeness false positive
  - blueprint timeline handoff contamination
  - Stage 4 feedback-fidelity / retry-loop inefficiency
- Stage 2 is not the root cause.
- Director PASS to post-select REJECT is not a split-brain bug; it is the intended safety net.
- Context and retrieval are contributing factors only, not the primary blocker.
- DB max-retention and console max-display items remain active queue items, but they are not the main rerun blockers.
- The next rerun is technically possible, but ROI favors fixing this cluster first.

## 3. Scope
Included:
- `modules/validation/blocking_validator_scene_checks.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- targeted tests covering:
  - scene completeness validation
  - blueprint temporal carryover
  - Stage 4 retry feedback and previous-attempt reconstruction

Excluded:
- DB schema or persistence expansion
- console max-display backlog beyond what is required for retry-fidelity correctness
- Stage 2 or Stage 3 observability-only debts
- retrieval and context-system redesign
- broad Stage 3 scene-schema redesign beyond what is required to remove the rerun blocker
- fresh rerun execution itself

## 4. Pass 1. Inventory Summary
- Inventory Class A. Scene validator contract failure
  - `BlockingValidatorSceneChecks._check_scene_completeness()` uses keyword-window heuristics that misclassify scene-complete manuscripts as `0/5`.
- Inventory Class B. Temporal handoff contamination
  - blueprint continuity carries `prev_blueprint.time_flow` and related metadata forward even when previous manuscript truth has already advanced farther.
- Inventory Class C. Retry-fidelity loss
  - Stage 4 repair guidance is flattened, compacted, and sometimes reconstructs too-poor `previous_attempt` data after empty or downgraded rounds.

## 5. Pass 2. Semantic Classification
- Class A. Pre-rerun blocker
  - scene validator contract fix
- Class B. Pre-rerun blocker
  - blueprint temporal truth handoff fix
- Class C. High-ROI amplifier fix
  - Stage 4 feedback-fidelity and retry snapshot preservation
- Deferred:
  - Stage 3 broad scene semantic-field enrichment
  - Stage 2/3 DB reasoning parity
  - console-only display polish not required for correction behavior

## 6. Side-Effect Map
- file writes / artifacts:
  - no direct artifact migration
  - future rerun artifacts should reflect changed blueprint time metadata and validator behavior
- DB / schema / transaction boundaries:
  - not primary scope
  - do not widen into DB retention work
- JSONL / log / audit sinks:
  - existing sinks remain
  - minor feedback content changes may affect saved advisory text indirectly
- console / UI / operator output:
  - some retry-feedback and validator wording may become fuller or structurally clearer
- rollback / recovery / retry:
  - primary scope
  - must preserve retry routing semantics unless explicitly covered by this SSOT
- cache / global state:
  - not primary scope
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Patch the earliest authoritative seam that can remove the defect instead of adding downstream overrides.
- For scene completeness:
  - make the validator understand actual manuscript scene structure, not just keyword windows.
- For temporal continuity:
  - prefer verified previous manuscript truth or verified ending-state truth when carrying timeline context into the next blueprint.
- For feedback fidelity:
  - keep retry directives structured
  - preserve richer previous-attempt context after failed or downgraded rounds
  - avoid new compacting/truncation in retry-critical paths
- Keep the following invariant:
  - Director verdict policy stays the same
  - post-select conflict downgrade stays the same
  - this wave corrects upstream truth and repair fidelity, not authority ownership

## 8. Execution Tranches
1. Scene validator contract tranche
   - update `BlockingValidatorSceneChecks._check_scene_completeness()`
   - accept real scene markers such as markdown `### 씬 N:` style structure
   - stop using the current keyword-window rule as the sole completeness oracle
2. Blueprint temporal handoff tranche
   - update blueprint temporal carryover so next-episode timeline context no longer trusts stale previous blueprint metadata by default
   - keep `time_flow`, continuity carryover, and ending timeline aligned with verified prior truth
3. Stage 4 feedback-fidelity tranche
   - replace retry-directive flattening that destroys instruction boundaries
   - preserve richer empty-round and downgrade-round `previous_attempt` context
   - stop compacting retry-critical provenance in the correction path where full context is already available
4. Regression and guard tranche
   - add focused regression tests for:
     - scene completeness under real manuscript scene headers
     - temporal carryover from previous manuscript truth
     - retry-directive structure and empty-round snapshot preservation

## 9. Acceptance Criteria
- an ep3-like manuscript with explicit scene headers no longer yields a false `0/5` scene-completeness failure under covered formats
- blueprint temporal handoff no longer reproduces the ep2-to-ep3 one-day drift from stale prior metadata
- retry directives remain structurally separated, not flattened into one slash-delimited blob
- empty-round or downgrade-round `previous_attempt` reconstruction preserves enough context to guide the next round
- no change to Director sovereignty, score policy, adaptive policy, or post-select downgrade ownership
- no widening into DB-retention or console-only backlog outside this SSOT

## 10. Verification Plan
- `python -m py_compile modules/validation/blocking_validator_scene_checks.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py`
- low-memory pytest shards, sequentially:
  - `python -m pytest tests/test_blocking_validator_submodules.py -q`
  - `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q`
  - `python -m pytest tests/test_blueprint_patch_mode.py -q`
  - `python -m pytest tests/test_stage4_interview_round.py -q`
  - add or extend targeted regressions if the existing shards do not directly cover the new seams
- post-implementation manual sanity target:
  - fresh rerun remains deferred until Codex audit
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md docs/temp/pre-rerun-root-cause-fix-cluster-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not reopen the long-function campaign during this work.
- Do not widen into DB logging max-retention changes.
- Do not widen into console max-display backlog except where retry-fidelity requires it.
- Do not change verdict math, Director thresholds, or post-select downgrade policy.
- Do not add new truncation to retry-critical fields.
- If a broader Stage 3 schema redesign appears necessary, stop and report it instead of quietly widening this wave.

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition:
  - satisfied: remove the temp mirror after realization and Codex closure
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Opus Order Prompt

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/pre-rerun-root-cause-fix-cluster-execution-ssot.md
4. docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md
5. docs/2026-03-23/pre-rerun-root-cause-merge-audit.md
6. docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md
7. docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md
8. docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md
9. docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md
10. docs/2026-03-23/max-retention-observability-execution-roadmap.md

Task:
Implement the bounded pre-rerun fix cluster defined in docs/temp/pre-rerun-root-cause-fix-cluster-execution-ssot.md.

Primary goal:
Remove the proven rerun blockers and the highest-ROI retry-fidelity defect before the next fresh run.

Hard constraints:
- Follow the execution SSOT exactly.
- Do not widen scope.
- Do not reopen DB max-retention work.
- Do not reopen console max-display backlog except where retry-fidelity requires it.
- Do not change Director verdict policy, adaptive thresholds, score math, retry routing policy, or post-select downgrade ownership.
- Do not create or close execution SSOTs or mutate queue-state by hand.
- If one included item is already fixed in live code, shrink scope and continue.
- If a broader Stage 3 schema redesign appears necessary, stop and report it rather than improvising a wider patch.

Execution scope:
1. Scene validator contract fix
- Target:
  - modules/validation/blocking_validator_scene_checks.py
- Goal:
  - scene completeness must recognize real manuscript scene structure and stop producing the known false 0/5 failure on covered formats

2. Blueprint temporal handoff fix
- Targets:
  - modules/domain/agents/blueprint_constraint_compiler.py
  - modules/domain/agents/blueprint_ensemble.py
- Goal:
  - next-episode temporal carryover must no longer trust stale previous blueprint metadata as the sole truth source when previous manuscript truth is available

3. Stage 4 feedback-fidelity fix
- Targets:
  - modules/core/stage4_interview_round.py
  - modules/core/stage4_reject_runtime.py
- Goal:
  - retry directives remain structured
  - empty-round and downgrade-round previous_attempt state preserves enough repair context
  - retry-critical provenance is not unnecessarily compacted

4. Regression tranche
- Add or extend focused tests covering:
  - scene completeness under explicit scene headers
  - blueprint temporal carryover from prior manuscript truth
  - retry-directive structure and previous_attempt preservation

Out of scope:
- DB schema or retention expansion
- console-only display polish unrelated to retry fidelity
- Stage 2 or Stage 3 observability-only debt
- retrieval redesign
- fresh rerun execution

Implementation rules:
- Use apply_patch for edits.
- Keep comments short and boundary-oriented.
- Preserve authority ownership and post-select safety semantics.
- If a hidden design fork appears, stop and report it instead of widening the wave.

Required verification:
- python -m py_compile modules/validation/blocking_validator_scene_checks.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py
- python -m pytest tests/test_blocking_validator_submodules.py -q
- python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q
- python -m pytest tests/test_blueprint_patch_mode.py -q
- python -m pytest tests/test_stage4_interview_round.py -q
- python scripts/check_utf8_hygiene.py docs/2026-03-23/pre-rerun-root-cause-fix-cluster-execution-ssot.md docs/temp/pre-rerun-root-cause-fix-cluster-execution-ssot.md
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize exactly what changed by tranche
- list verification results
- list any deferred item and why
- state whether any included item was already resolved and skipped
- do not close or supersede the execution SSOT; Codex will audit that afterward
```

## 15. 3-Pass Audit Record
- Pass 1: converted the merge audit into one bounded implementation slice instead of a broad rerun-era backlog
- Pass 2: separated the true rerun blockers from observability-only debts and explicitly excluded DB/console queue items
- Pass 3: rechecked queue semantics so this SSOT can enter the existing aggregate roadmap without replacing the active DB/console items

## 16. Confidence
- Estimated confidence: 96%
- Residual uncertainty:
  - the exact best seam for manuscript-truth temporal carryover may still tighten during implementation Pass 1
  - Stage 3 scene semantic-field enrichment remains intentionally deferred unless a bounded seam appears during the blocker fix
