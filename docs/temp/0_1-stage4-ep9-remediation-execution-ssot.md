# 0_1 Stage4 EP9 Remediation Execution SSOT

Date: 2026-03-30
Status: execution-ready
Canonical Path: `docs/2026-03-30/0_1-stage4-ep9-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked changes in 0_temp.txt, Stage 4 runtime files/tests, project 0_1 logs/db, blueprint_0008; multiple untracked 2026-03-30 docs/artifacts/scripts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-bounded-survey.md`
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
- `projects/0_1/plans/blueprints/blueprint_0009.txt`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe Stage 4 correction that closes the EP9 retry pathology proven by the root-cause survey.

This wave exists because EP9 is currently blocked by runtime contract faults, not by a bad manuscript:

- `NpcDrift` compares against stale `role_at_intro`
- strong advisory escalation can create an impossible `PASS_WITH_FIX + empty patch_targets` state
- retry-lane diagnostics lose `stage` / `ep_num` attribution in `ui_events`

This wave is queue-worthy now because it is the current operator-requested blocker and has higher shared Stage 4 leverage than the older deferred observability lane.

## 2. Baseline Facts

- EP9 Stage 4 reached 6 persisted attempts and entered round 7 because live outer round cap is 10.
- Attempts 1, 2, 3, 5, 6 ended as `strong_advisory_escalation_non_local_fix` with `fix_pack_reason=missing_patch_targets`.
- Attempt 4 alone entered patch re-audit and then failed as `patch_reaudit_fail`.
- EP9 manuscript hashes collapse to 3 distinct texts across 6 attempts, but the dominant blocker is still upstream of diversity: false-positive `NpcDrift` plus impossible escalation contract.
- `NpcDrift` expected values currently come from `world_state.get_npc_role_snapshot()`, which surfaces frozen `role_at_intro`; EP9 blueprint truth and cumulative state both place 박성호 at the 한미증권 desk rather than the stale `SW인베스트먼트 전담 PB` baseline.
- `ui_events` attribution drift is material: EP9 session window retry-lane events show 162 `stage=null` rows versus 294 attributed rows.
- Related canonical-only doc `docs/2026-03-30/0_1-ep8-artifact-vs-code-execution-ssot.md` already identified the impossible `PASS_WITH_FIX` seam; this EP9 SSOT is the current queue authority because it adds the missing `NpcDrift` authority correction and retry attribution repair.

## 3. Scope

Included:
- `modules/core/world_state.py`
- `modules/core/npc_drift_advisor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- bounded Stage 4 tests for advisory escalation, retry attribution, and NPC role snapshot authority
- canonical execution SSOT, temp mirror, and active roadmap refresh

Excluded:
- EP8 blueprint manual repair lane
- broad Stage 3 validator or blueprint hardening lanes
- candidate diversity / same-hash reselection policy
- TF-4 rewrite-policy redesign beyond what is required to keep escalation coherent
- provider fallback observability work
- Director prompt schema expansion that turns Python into a fact owner
- DB schema change or automatic NPC fact-sheet rewrites

## 4. Pass 1. Inventory Summary

- root-cause runtime owners:
  - `world_state.py` for role snapshot authority
  - `npc_drift_advisor.py` for drift comparison semantics
  - `stage4_interview_round.py` for strong-advisory escalation and fix-pack gate
  - `stage4_retry_runtime.py` for retry-lane logging and re-audit path
  - `director_ensemble.py` for normalized `fix_pack` handoff shape
- evidence anchors:
  - EP9 round matrix in DB and JSONL
  - blueprint_0009 artifact truth
  - stage4 attempt artifacts 01..06
  - retry-lane `ui_events` attribution sample
- queue context:
  - active temp queue already contains 6 execution mirrors
  - no queued item currently targets EP9 root cause directly
  - this item is independent of the Stage 3 lanes and should not wait on them

## 5. Pass 2. Semantic Classification

- Class A. `NpcDrift` authority correction
  - replace stale intro-role comparison with a bounded current-truth authority ladder
- Class B. strong-advisory escalation coherence
  - remove the impossible `PASS_WITH_FIX + empty patch_targets` state
  - this wave chooses explicit non-local retry semantics when no patch-ready local fix exists; it does not invent speculative `patch_targets`
- Class C. retry observability repair
  - restore `stage` / `ep_num` attribution on retry-runtime `ui_events`
- Class D. explicitly deferred amplifiers
  - candidate diversity
  - TF-4 optimization beyond coherence preservation
  - broader advisory-to-fix-pack synthesis research

## 6. Side-Effect Map

- file writes / artifacts:
  - `modules/core/world_state.py`
  - `modules/core/npc_drift_advisor.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/domain/agents/director_ensemble.py`
  - targeted tests
  - canonical execution SSOT, temp mirror, roadmap refresh

- DB / schema / transaction boundaries:
  - no DB schema change intended
  - no write-authority change for NPC facts
  - runtime verdict persistence will change only through coherent retry-path outcomes

- JSONL / log / audit sinks:
  - `ui_events` should regain `stage` / `ep_num` on retry-lane messages
  - `episode_production.jsonl` / decision sinks may reflect different gate_basis or retry_scope outcomes after the impossible PASS_WITH_FIX seam is removed
  - no sink removal allowed

- console / UI / operator output:
  - retry-lane console/UI messages may become more explicit about why the path is non-local
  - observability should improve, not widen into new UX surfaces

- rollback / recovery / retry:
  - retry routing behavior is intentionally affected
  - residual strong advisories without a patch-ready local fix must no longer masquerade as local patch work
  - valid existing local `PASS_WITH_FIX` paths must remain intact

- cache / global state:
  - `WorldState` read semantics for NPC role snapshots will change
  - no new global registry or cache is allowed

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 NpcDrift Comparison Authority Ladder

The execution choice is to make `NpcDrift` read fresher current truth without granting Python fact-edit authority.

Required contract:

- prefer current episodic / cumulative truth when a fresher authoritative role-position signal exists
- keep `role_at_intro` only as fallback, not as universal truth
- the comparison ladder must be read-only
- no automatic mutation of canonical NPC facts, fact sheets, or intro-role storage

Acceptable implementation shape:

- add or refine a bounded helper near `world_state.get_npc_role_snapshot()` and the `npc_drift_advisor` consumer seam
- prefer current role/position semantics derived from already-authoritative runtime state
- if no fresher truth exists, fall back to the current conservative intro snapshot

Guardrail:

- do not solve this by mutating `role_at_intro` in Python
- do not let Python overwrite narrative facts outside the existing LLM-owned truth path

### 7.2 Strong-Advisory Escalation Coherence

This wave should not auto-generate speculative local patch packs from advisory prose.

Execution decision:

- if a plain Director `PASS` is escalated by a strong advisory and no patch-ready local fix exists, route into an explicit non-local retry / reject contract rather than emitting `PASS_WITH_FIX`
- preserve the advisory reason and retry guidance
- keep true local `PASS_WITH_FIX` behavior unchanged when a real `fix_pack` is already present and ready

Why this choice:

- survey evidence is sufficient to prove the current state is impossible
- survey evidence is not sufficient to prove robust free-text advisory -> `patch_targets` synthesis
- a coherent non-local path is lower risk than fabricating patch instructions

### 7.3 Retry Attribution Contract

`stage4_retry_runtime.py` must stop emitting unattributed retry-lane UI events.

Required contract:

- retry-runtime `ctx.ui.log()` calls carry `stage=4` and the current `ep_num`
- where round or attempt context is already known, preserve it in the same bounded path
- this is an observability repair only; it must not widen into a new sink family

### 7.4 Relationship To Existing Docs

- this item does not replace the EP8 artifact repair lane
- this item reuses and operationalizes the EP8 code-contract seam evidence where it overlaps
- if later evidence proves advisory-to-fix-pack synthesis is safe, that should be a follow-up wave, not an unbounded expansion of this one

## 8. Execution Tranches

1. Tranche 1: `NpcDrift` authority correction
   - implement the bounded current-truth ladder
   - add regression coverage for EP9-style blueprint-conformant 박성호 portrayal

2. Tranche 2: strong-advisory escalation coherence
   - remove impossible `PASS_WITH_FIX + empty patch_targets`
   - keep ready local fix-pack happy path unchanged
   - add targeted regression coverage for the previously hopeless advisory loop

3. Tranche 3: retry observability repair
   - add `stage` / `ep_num` to retry-runtime `ui_events`
   - add targeted verification for TF-4 / TF-PATCH-GATE / QR-7 style messages

4. Tranche 4: bounded post-fix validation
   - targeted low-memory pytest shards on touched areas
   - optional bounded EP9 fresh rerun or reproduction after code lands and the workspace is safe for runtime validation

## 9. Acceptance Criteria

- EP9-style blueprint-conformant 박성호 desk/team-lead portrayal no longer triggers `NpcDrift` solely because of stale `role_at_intro`
- strong-advisory escalation cannot end in `PASS_WITH_FIX` when `patch_targets` are absent
- residual non-local strong advisories route coherently and visibly without pretending local patch repair is ready
- valid existing local `PASS_WITH_FIX` flows still pass the fix-pack gate
- retry-runtime `ui_events` for TF-4 / TF-PATCH-GATE / QR-7 carry `stage` and `ep_num`
- no DB schema change, no automatic NPC fact rewrite, and no provider-policy drift occurs in this wave
- candidate diversity and TF-4 optimization remain explicitly deferred

## 10. Verification Plan

- targeted low-memory pytest shards for:
  - `tests/test_stage4_advisory_escalation_seam.py`
  - `tests/test_stage4_lane2_binding_contract.py`
  - `tests/test_world_state_manager.py`
  - one bounded retry-runtime attribution test surface in the touched Stage 4 runtime area
- `python -m py_compile` on touched production and test files
- `ruff check` on touched production and test files
- `python scripts/check_utf8_hygiene.py` on touched docs/code/tests
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- if code realization starts from this SSOT:
  - re-run this document's 3-pass audit against the live workspace
  - refresh `Resume Commit` and `Resume Drift Summary`
  - only then run the bounded EP9 validation path

## 11. Guardrails

- do not let Python become a fact-writing authority for NPC roles or relationships
- do not solve the advisory seam by silently fabricating speculative `patch_targets`
- do not reopen provider fallback, Stage 3 validator, or EP8 artifact-repair scope from this wave
- do not widen into candidate diversity or TF-4 redesign in the same patch unless fresh evidence proves the root-cause lane is already closed
- do not remove or rename existing audit sinks without replacement
- preserve Director sovereignty over quality verdicts

## 12. Temp Queue Notes

- temp status: ready-for-execution
- cleanup condition:
  - remove `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md` after realization, closure audit, roadmap refresh, and queue-state sync
- roadmap dependency:
  - must be admitted into the active aggregate roadmap in the same turn
  - should be ordered ahead of the older deferred Stage 4 provider item because it is the direct current blocker and has stronger substrate leverage on live Stage 4 correctness

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- execution SSOT type matches the user request
- canonical path and temp mirror path are explicit
- included, excluded, side-effect, verification, guardrails, and queue sections are present
- path policy follows canonical-first, temp-mirror-second

### Pass 2. Evidence and Consistency

- root-cause claims map to the EP9 bounded survey and evidence JSON
- the chosen escalation direction matches live evidence: remove impossible local-patch state rather than invent unsupported fix-pack synthesis
- current queue state and roadmap requirement were re-checked before admitting this item
- no contradiction with AGENTS fact-ownership rules: this wave is read-side authority correction, not Python fact mutation

### Pass 3. Execution and Readability

- the document is execution-shaped, not another survey restatement
- tranche order matches substrate-first correction:
  - truth source
  - escalation coherence
  - observability
  - bounded validation
- deferred amplifiers are explicitly cut to keep the wave bounded

Estimated confidence: `96%`
