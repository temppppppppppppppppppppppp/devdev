Date: 2026-03-24
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-24/stage4-immutable-fact-convergence-execution-ssot.md`
Temp Mirror Path: `removed after closure (former path: docs/temp/stage4-immutable-fact-convergence-execution-ssot.md)`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: docs/2026-03-23/console.txt retained as post-run evidence; docs/2026-03-24 tracked analysis docs`
- Resume Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Resume Drift Summary: `same HEAD; realization landed in stage4 immutable-fact substrate, Stage 3 handoff gate, CW context wiring, pre-director/state sink surfaces, and targeted tests; closure audit also fixed effective_score propagation for IFC penalty`
Source Survey Docs:
- `docs/2026-03-24/fresh-run-stage4-convergence-root-cause-report.md`
- `docs/2026-03-24/stage4-immutable-fact-convergence-design.md`
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/00_001/logs/soft_failures.jsonl`
- active live code seams in `modules/domain/agents/chief_writer_context.py`
- active live code seams in `modules/core/stage4_interview_round.py`
Side-Effect Coverage: yes

---

# Stage 4-Led Immutable Fact Convergence Execution SSOT

## 1. Intent

Realize one bounded Stage 4-led convergence wave that turns hard continuity/state facts into a shared immutable contract for:

- Stage 2 carryover-sensitive tactical planning
- Stage 3 scene-obligation handoff quality
- CW first-write
- pre-director hard gate
- post-select downgrade explanation
- retry/rewrite routing

Why now:

- current live evidence shows repeated late convergence on Stage 4
- current live evidence also shows the same hard-fact weakness one step upstream in Stage 2 and Stage 3
- final safety is working
- time-to-convergence is not

## 2. Baseline Facts

- Stage 4 often passes only after 2-3 rounds of write/fix churn
- failure family is usually hard continuity/history/state drift, not generic prose weakness
- `patch_targets is empty` still appears in precisely the cases where the manuscript is globally wrong
- Stage 2 Arc 3 also showed hard-fact weakness:
  - prior-arc recovery obligation was initially omitted
  - capital arithmetic had to be patched after Director REJECT/PASS_WITH_FIX
- Stage 3 Arc 3 blueprints continue to pass with scene metadata gaps:
  - repeated `goal/summary` omission warnings
  - unresolved continuity pin warnings
- Episode 7 exposed one additional bounded sink bug after PASS:
  - post-pass `relationship_changes[npc]` can still carry dict witnesses
  - `WorldState` / `FactLedger` expect scalar actor references there
  - the result was `TF-C10` atomic metadata rollback with `unhashable type: 'dict'`
- existing code already has:
  - opening-anchor injection
  - pre-director opening/scene checks
  - fix-pack contract evaluation
  - retry-directive surfaces
- what is missing is one shared immutable fact substrate applied early enough

## 3. Scope

Included:
- `modules/core/four_phase_arc_runtime.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- one new small substrate module for immutable fact packet assembly/classification
- targeted tests for packet assembly, checker parity, retry routing, and metadata normalization

Excluded:
- Stage 2 pacing changes
- broad Stage 3 strategy redesign
- repo-wide DB schema wave
- model-family swaps
- long-run Q5/Q7 architecture
- broad prompt redesign outside Chief Writer Stage 4 path

## 4. Pass 1. Inventory Summary

- writer input substrate already exists but is prose-heavy
- checker substrate already exists but does not consume a shared packet object
- retry substrate already exists but routes off weak textual signals and fix-pack readiness
- upstream spillover is now evidenced:
  - Stage 2 can still violate prior-arc carryover facts before Stage 4 ever runs
  - Stage 3 can still hand down under-specified scene obligations
- this wave remains bounded because it touches Stage 2/3 only at those carryover / metadata seams

## 5. Pass 2. Semantic Classification

- Class A. Immutable fact substrate
  - build one normalized packet with opening, committed-state, completed-event, and scene-obligation facts
- Class B. Writer contract reinforcement
  - inject packet ahead of softer context and forbid creative override
- Class C. Violation-driven repair routing
  - convert hard fact drift into explicit rewrite-biased routing rather than empty local patch loops
- Class D. Upstream spillover control
  - prevent Stage 2/3 from handing obviously broken or under-specified immutable facts into Stage 4
- Class E. Metadata sink normalization
  - prevent rich dict actor references from crossing into scalar persistence sinks after PASS

## 6. Side-Effect Map

- file writes / artifacts:
  - no new durable artifact type required
  - existing Stage 4 artifact outputs remain authoritative
- DB / schema / transaction boundaries:
  - no new schema required in this wave
  - existing reason / advisory persistence surfaces remain in use
  - existing metadata atomic save path must stop rolling back on dict-shaped relationship witnesses
- JSONL / log / audit sinks:
  - may enrich existing reason / retry fields with packet-based violation names
- console / UI / operator output:
  - should surface violation family and rewrite-vs-patch routing
- rollback / recovery / retry:
  - primary impact surface
  - retry policy becomes violation-family aware
- upstream tactical / blueprint handoff:
  - Stage 2 carryover constraints become immutable-fact aware
  - Stage 3 blueprint scene metadata completeness becomes part of handoff quality
- cache / global state:
  - packet may be per-attempt derived data only; avoid new global cache
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

Substrate:
- add one small owner module, recommended topic slug:
  - `modules/core/stage4_immutable_fact_contract.py`

Responsibilities:
- build immutable fact packet from already-available Stage 4 inputs
- build minimal upstream packet views for Stage 2/3 carryover/handoff seams
- expose compact helpers:
  - `build_packet(...)`
  - `classify_violation_family(...)`
  - `should_escalate_to_rewrite(...)`

Contract constraints:
- packet must remain derived-only
- packet must not become a new authority owner
- Director remains final judge

Implementation shape:
- Stage 2 path consumes packet-derived carryover facts as non-negotiable planning truths
- Stage 3 path uses packet-derived obligation completeness checks before handoff
- CW path consumes packet as non-negotiable context
- checkers consume packet as hard-gate reference
- retry path consumes packet-derived violation family for escalation
- post-pass metadata settlement normalizes actor references before `WorldState` / `FactLedger` persistence

## 8. Execution Tranches

1. Immutable Fact Packet substrate
- add new packet/classification helper module
- normalize:
  - opening anchor
  - committed state facts
  - completed-event facts
  - scene obligations

2. Stage 2 carryover seam
- feed prior-arc recovery/state facts through the shared contract path
- ensure tactical planning cannot silently soften mandatory carryover facts

3. Stage 3 obligation seam
- require minimally usable scene obligation metadata where Stage 4 depends on it
- convert repeated `goal/summary`-missing style warnings into contract-aware handoff quality checks

4. CW contract injection
- build packet section in `chief_writer_context_packets`
- inject it ahead of softer continuity prose in `chief_writer_prompts`
- state clearly that packet facts override local plausibility improvisation

5. Checker parity
- pre-director checklist/manuscript checker consume packet-derived anchors
- hard fact drift becomes packet-aware instead of only prose-symptom-aware

6. Retry / rewrite routing
- Stage 4 downgrade/reject path emits explicit violation families
- if violation family is hard fact drift and local patch contract is weak or empty, escalate earlier to rewrite-biased regeneration

7. Observability and regression lock
- surface packet/violation family in existing operator and reason fields
- add targeted tests for packet build, gate behavior, and rewrite escalation

8. Post-pass metadata normalization
- normalize `relationship_changes` actor references to stable scalar names before metadata persistence
- preserve rich observer detail only in explicitly nested metadata fields
- add bounded sink-side guards in `WorldState` / `FactLedger` so dict-shaped actor refs degrade safely instead of rolling back the whole atomic save

## 9. Acceptance Criteria

- CW receives a distinct immutable fact section before softer context
- Stage 2 cannot silently drop known carryover obligations in touched paths
- Stage 3 cannot hand off touched blueprints with unusable scene obligation metadata in touched paths
- opening/state/event fact drift can be named as explicit violation families
- hard fact drift no longer burns repeated empty local patch rounds by default
- local prose fixes remain available for genuinely local problems
- Director sovereignty remains unchanged
- no new schema is required for this wave
- Episode 7-style dict witness payloads no longer break post-pass atomic metadata save
- `WorldState` and `FactLedger` settle the same PASS result without `TF-C10` rollback on relationship-reference shape

## 10. Verification Plan

- `python -m py_compile modules/core/four_phase_arc_runtime.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/three_phase_blueprint_runtime.py modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer_context_packets.py modules/domain/agents/chief_writer_prompts.py modules/core/pre_director_checklist.py modules/core/pre_director_manuscript_checker.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/core/stage4_reject_runtime.py modules/core/stage4_post_pass_runtime.py modules/core/world_state.py modules/core/fact_ledger.py modules/core/stage4_immutable_fact_contract.py`
- targeted low-memory pytest shards for:
  - `tests/test_blueprint_patch_mode.py`
  - touched Stage 2/3 planning and blueprint shards
  - `tests/test_chief_writer_context.py`
  - `tests/test_pre_director_submodules.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_world_state_manager.py`
  - `tests/test_fact_ledger.py`
  - retry / rewrite routing tests in touched Stage 4 shards
- fresh-run validation after realization:
  - verify that hard continuity/state drift either fails earlier or escalates earlier
  - verify fewer repeated `patch_targets is empty` loops for the same failure family
- `python scripts/check_utf8_hygiene.py docs/2026-03-24/stage4-immutable-fact-convergence-design.md docs/2026-03-24/stage4-immutable-fact-convergence-execution-ssot.md docs/temp/stage4-immutable-fact-convergence-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- do not widen into Stage 2 or Stage 3 redesign
- do not create a second quality authority beside Director
- do not solve this by unconditional full rewrite
- do not add new DB schema unless later evidence proves it necessary
- do not introduce global caches for packet state
- Stage 2/3 touches in this wave are limited to immutable-fact carryover and handoff quality only
- metadata sink hardening must stay bounded to actor-reference normalization; do not open a broader state-manager redesign

## 12. Temp Queue Notes

- temp status: closed; mirror removed after closure audit
- cleanup condition:
  - execution realization complete
  - Codex closure audit complete
  - temp mirror removed
  - queue state resynced
- roadmap dependency:
  - none yet

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - post-run 3-pass audit already refreshed against live evidence
  - temp mirror creation is allowed immediately

## 14. Opus Order Prompt

Use this against the temp mirror after Codex finishes temp queue activation.

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/stage4-immutable-fact-convergence-execution-ssot.md
4. docs/2026-03-24/stage4-immutable-fact-convergence-design.md
5. docs/2026-03-24/fresh-run-stage4-convergence-root-cause-report.md
6. docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md
7. docs/2026-03-23/console.txt
8. projects/00_001/logs/soft_failures.jsonl

Task:
Implement the bounded Stage 4-led immutable-fact convergence wave defined in the execution SSOT.

Hard constraints:
- Follow the execution SSOT exactly.
- Do not widen into Stage 2/3 redesign.
- Do not replace Director authority.
- Do not solve this by unconditional full rewrite.
- Do not widen the metadata fix beyond actor-reference normalization and bounded sink hardening.
- No new DB schema unless the SSOT is first refreshed by Codex.

Output requirements:
- summarize changes by tranche
- list verification results
- do not close the execution SSOT; Codex will audit and close it
```

## 15. 3-Pass Audit Summary

Pass 1. Structure and Scope
- post-run execution SSOT, queue-activatable
- scope strengthened from Stage 4-only to Stage 4-led with minimal Stage 2/3 immutable-fact spillover plus bounded metadata normalization

Pass 2. Evidence and Consistency
- grounded in current root cause report, prior remediation plan, console tail, soft-failure evidence, and live code seam audit
- no claim that the fix is already realized

Pass 3. Execution and Readability
- tranches, acceptance criteria, guardrails, and immediate temp-queue activation rule are explicit

Confidence
- estimated confidence: 96%

## 16. Closure Note

- Realization state:
  - closed
- Closure audit result:
  - the two residual gaps reported at handoff are resolved in live code
  - Codex closure audit found one remaining Stage 3 observability/contract mismatch: IFC penalty affected PASS/REJECT but the returned/logged score still carried the raw pre-penalty value
  - that mismatch is now fixed so `effective_score`, `raw_score`, and `ifc_penalty` are recorded explicitly and the returned Phase 3 score matches the quality gate input

### Implemented Scope Confirmed

- Immutable fact substrate:
  - `modules/core/stage4_immutable_fact_contract.py`
- Stage 3 obligation seam:
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
  - scene obligation completeness now applies a bounded score penalty before the quality gate
- CW contract injection:
  - `modules/domain/agents/chief_writer_context.py`
  - immutable fact packet now receives `prev_digest`, `world_state_summary`, and `chain_link_section` in the live prompt build path
- Metadata sink normalization / parity surfaces:
  - `modules/core/world_state.py`
  - `modules/core/fact_ledger.py`
  - `modules/core/stage4_post_pass_runtime.py`
- Retry / reject / checker parity surfaces:
  - `modules/core/pre_director_checklist.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/chief_writer_prompts.py`

### Verification Evidence

- `python -m py_compile modules/domain/agents/three_phase_blueprint_runtime.py modules/domain/agents/chief_writer_context.py modules/core/stage4_immutable_fact_contract.py tests/test_blueprint_patch_mode.py tests/test_chief_writer_context.py tests/test_stage4_immutable_fact_contract.py`
- `pytest tests/test_blueprint_patch_mode.py tests/test_chief_writer_context.py tests/test_stage4_immutable_fact_contract.py -q` -> `132 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `78 passed`
- reported implementation verification from the realization handoff:
  - `tests/test_stage4_immutable_fact_contract.py` previously green on the worker run
  - UTF-8 hygiene clean
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py`

### Residual Risk

- No fresh live rerun was executed after the final residual-gap patches.
- Convergence improvement is therefore code-and-test verified, but not yet re-measured with a new runtime attempt family.
- That rerun is follow-up validation, not an active blocker for closing this bounded execution item.

### Temp Cleanup

- `docs/temp/stage4-immutable-fact-convergence-execution-ssot.md` removed after canonical closure update
- `docs/temp/queue-state.json` must reflect the empty execution queue after sync
