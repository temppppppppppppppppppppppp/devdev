Date: 2026-03-24
Status: final (3-pass audited)
Document Type: design note
Canonical Path: `docs/2026-03-24/stage4-immutable-fact-convergence-design.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-24/fresh-run-stage4-convergence-root-cause-report.md`
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
- `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
- `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
- `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/00_001/logs/soft_failures.jsonl`
- live code seams in `modules/domain/agents/chief_writer_context.py`
- live code seams in `modules/domain/agents/chief_writer_context_packets.py`
- live code seams in `modules/domain/agents/chief_writer_prompts.py`
- live code seams in `modules/core/pre_director_checklist.py`
- live code seams in `modules/core/pre_director_manuscript_checker.py`
- live code seams in `modules/core/stage4_interview_round.py`
- live code seams in `modules/core/stage4_retry_runtime.py`
- live code seams in `modules/core/stage4_reject_runtime.py`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: docs/2026-03-23/console.txt retained as post-run evidence; docs/2026-03-24 tracked design/report updates`
- Resume Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Resume Drift Summary: `same HEAD; design refreshed after Ep 7 terminal evidence and soft-failure seam audit`
Side-Effect Coverage:
- artifact truth: yes
- DB truth: indirect via source reports
- console/operator truth: yes
- JSONL/metrics truth: indirect via source reports
- config/bootstrap: not primary

---

# Stage 4 Immutable Fact Convergence Design

## 1. Intent

This design answers one specific question:

`Can the current write/fix loop be made both simpler and more correct without defaulting to brute-force full regeneration?`

The answer is yes.

The elegant path is not "retry more" and not "always rewrite."
The elegant path is:

`compile one immutable fact contract once, feed it to every boundary that mutates or materializes narrative state, and let repair policy key off explicit fact violations instead of prose-level intuition.`

## 2. Problem Statement

The current fresh run shows a stable pattern:

- Director and post-select eventually protect final safety.
- CW initial drafting and early repair still rewrite committed facts too easily.
- early patch rounds often operate on weak or empty patch targets
- convergence happens late, after 2-3 expensive retries
- the same weakness is now visible one step upstream in Stage 2 and Stage 3:
  - Stage 2 Arc 3 needed REJECT -> PASS_WITH_FIX because recovery-scene carryover and capital arithmetic were treated as soft planning details
  - Stage 3 Arc 3 blueprints continue to pass with `goal/summary` metadata gaps and unresolved continuity pins
- post-pass metadata settlement can still break after a successful PASS:
  - Ep 7 emitted `relationship_changes[npc]` as rich dict witnesses
  - `WorldState` and `FactLedger` still expect scalar NPC references there
  - the result was a non-blocking atomic-save rollback instead of stable metadata settlement

This is not primarily a "smartness" issue.
It is a contract-shape issue.

The same truth currently exists in multiple weak forms:

- blueprint `start_location`, `time_flow`, `scene_breakdown`
- previous manuscript ending
- digest / state packet prose
- post-select continuity and history conflict messages
- fix pack summaries

Those surfaces are informative, but they do not behave like one authoritative object.

Result:

- CW treats some hard facts as revisable prose
- Director and post-select treat them as veto conditions
- retry logic receives late, compressed, or under-structured repair signals

## 3. Design Goal

The target is not broad architecture churn.
The target is one clean policy shift:

`hard continuity/state facts become first-class immutable inputs, not soft prose guidance.`

Success means:

- first draft drifts less
- repair packets become more actionable
- rewrite escalation becomes selective and explainable
- Director remains sovereign
- no new competing authority is introduced

## 4. Existing Substrate We Can Reuse

This is not a greenfield redesign.
The codebase already has the right partial pieces:

- CW already receives `scene_breakdown`, `prev_digest`, `prev_ending`, and `opening_anchor_section`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/domain/agents/chief_writer_context_packets.py`
- prompt ordering already has an early opening-anchor slot
  - `modules/domain/agents/chief_writer_prompts.py`
- pre-director already runs opening and scene checks
  - `modules/core/pre_director_checklist.py`
  - `modules/core/pre_director_manuscript_checker.py`
- Stage 4 already carries `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `fix_pack`, `retry_directives`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_reject_runtime.py`
- Stage 2 and Stage 3 already expose the upstream seams where the same immutable facts should be enforced earlier
  - Stage 2 tactical planning / validation
  - Stage 3 blueprint metadata and continuity pin warnings

So the missing piece is not more data.
The missing piece is one shared contract object.

## 5. Proposed Core Abstraction

Introduce one bounded substrate:

`Immutable Fact Packet`

It should be built once per attempt family and reused across:

- Stage 2 tactical planning where prior-arc carryover facts matter
- Stage 3 blueprint completion where scene obligations are first shaped
- CW first-write context
- pre-director hard gate
- Director/post-select downgrade explanation
- retry / rewrite routing

The packet is not freeform prose.
It is a normalized structure with stable keys.

Recommended shape:

1. `opening_anchor`
- start location
- start time flow
- scene 1 title / summary / location
- prior manuscript ending bridge

2. `committed_state_facts`
- current numeric truths that must not regress
- ownership / possession / established state values
- actor-role facts that were already fixed in prior episodes

3. `completed_event_facts`
- already finished beats that must not be replayed as unresolved
- already crossed thresholds that must not be downgraded again

4. `scene_obligations`
- one row per scene
- must-materialize beat
- must-not-erase beat
- optional local engine labels if already available

5. `repair_policy_hints`
- which violation families are patch-friendly
- which are rewrite-biased

6. `upstream_contract_flags`
- whether prior-arc recovery or carryover obligations are still open
- whether blueprint scene metadata is complete enough for downstream materialization

7. `sink_normalization_rules`
- which packet-backed references must degrade to stable scalar IDs before persistence
- which rich witness or observer detail may remain attached as nested metadata
- which sinks may never receive dict-shaped actor keys

## 6. Authority Model

The packet does not replace Director.
It changes only input discipline.

Authority remains:

- CW: draft only
- Director: quality judgment
- post-select: defensive validation

The packet simply makes all three read the same hard facts.

That is the clean part of the design:

`one truth object, many readers, one sovereign judge`

## 7. Writer-Side Change

CW should stop receiving hard facts only as mixed prose context.

Instead, CW should receive:

1. `immutable fact packet`
2. `scene breakdown`
3. `style / density / HUD / arc context`

in that priority order.

Prompt rule should become explicit:

- immutable facts are non-negotiable
- if local plausibility conflicts with packet facts, packet wins
- if packet facts appear self-contradictory, do not self-correct creatively; surface the conflict

This avoids the current pattern:

- BP says Gangnam
- CW thinks Yeouido is more plausible
- Director later rejects the rewrite

The same discipline should apply one step earlier:

- Stage 2 should not improvise away mandatory recovery/carryover obligations
- Stage 3 should not hand down scene structures with missing `goal/summary` metadata and expect Stage 4 to infer them cleanly

## 8. Gate-Side Change

Pre-director and post-select should stop speaking only in prose symptoms.

They should emit explicit violation classes tied to the same packet.

Recommended families:

- `opening_anchor_drift`
- `committed_state_regression`
- `completed_event_replay`
- `scene_obligation_missing`
- `scene_order_drift`
- `metadata_reference_shape_violation`

This matters because repair policy should branch by violation family, not by vague "quality issue."

## 9. Metadata Sink Normalization

The same contract discipline must continue one step after PASS.

Ep 7 showed that a manuscript can pass, and then post-pass settlement can still degrade because a rich witness payload crosses the persistence boundary in the wrong shape:

- `relationship_changes[npc]` arrived as a dict
- `WorldState` treated it like a scalar relationship key
- the atomic metadata transaction rolled back with `unhashable type: 'dict'`

That is not a separate architecture problem.
It is the same contract problem at a later boundary.

The rule should be:

- actor references that reach `WorldState` or `FactLedger` must be scalarized first
- rich observer detail should be preserved as nested metadata only in fields that are explicitly allowed to hold dict payloads
- producer-side normalization should be primary
- sink-side defensive coercion should exist only as a bounded guardrail

That keeps the design elegant:

- one packet
- one reference vocabulary
- one scalar persistence rule
## 10. Repair Policy Change

This is the most important runtime simplification.

Current failure mode:

- hard fact drift is treated like local prose repair
- fix pack goes weak or empty
- retry still continues

Proposed rule:

1. if violation family is local and patch targets are concrete
- keep patch path

2. if violation family is hard fact drift and patch targets are weak or empty
- escalate early to rewrite-biased regeneration

3. if scene-model obligation is broken broadly
- skip local patching
- regenerate against the packet and scene obligations

This is not blind rewrite.
It is classified rewrite.

It also implies one upstream rule:

- if Stage 2 or Stage 3 hands off obviously incomplete immutable facts, do not pretend Stage 4 patching will rescue them cheaply

## 11. What Makes This Design Elegant

It is elegant because it removes ambiguity rather than adding more heuristics.

It does not require:

- a larger model
- more advisory chains
- more retries
- broader DB schema first
- a new authority role

It only requires:

- one normalized fact packet
- one shared violation vocabulary
- one rewrite-escalation rule keyed to that vocabulary
- one scalar persistence rule for metadata sinks

That is both simpler and stronger than the current mixed-prose guidance pattern.

## 12. Minimal Code Landing Shape

Recommended bounded landing shape:

1. new small substrate module
- suggested topic: `stage4_immutable_fact_contract`
- responsibility: packet build + violation classification helpers

2. Stage 2 / Stage 3 upstream spillover
- minimal carryover-fact enforcement in Stage 2 tactical planning
- minimal blueprint metadata completeness enforcement in Stage 3 where `scene_obligations` are formed

3. CW injection
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`

4. checker parity
- `modules/core/pre_director_checklist.py`
- `modules/core/pre_director_manuscript_checker.py`

5. retry / downgrade parity
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`

6. metadata sink normalization
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`

This keeps change centered on Stage 4 while admitting the two upstream spillover seams now visible in live evidence.

## 13. Out of Scope

Not part of this design wave:

- Stage 2 pacing redesign
- long-run Q5/Q7 architecture
- broad DB schema expansion
- model family swaps
- retry count inflation
- global prompt rewrite across unrelated agents

The wave may touch Stage 2/3 only where they shape or violate immutable facts.
It does not reopen their broader strategy logic.

## 14. Operating Consequence

If implemented well, the expected change is:

- fewer "eventually passes after 3 rounds" cases
- more correct first drafts
- fewer empty `patch_targets`
- earlier rewrite only when a hard fact family is broken
- fewer Stage 2 carryover misses and fewer Stage 3 metadata gaps entering Stage 4
- no Ep 7-style metadata rollback from dict-shaped relationship witnesses

That is the right notion of improvement here.

The system already has a good firewall.
It now needs a better steering wheel.

## 15. 3-Pass Audit Summary

Pass 1. Structure and Scope
- design doc, not survey and not execution SSOT
- scope updated from Stage 4-only to Stage 4-led immutable-fact convergence with minimal Stage 2/3 spillover

Pass 2. Evidence and Consistency
- aligned to live console evidence, prior ROL reports, and current code seams
- no claim that the active fresh run has already fully confirmed the redesign

Pass 3. Execution and Readability
- substrate, authority, runtime use points, and out-of-scope surfaces are explicit

Confidence
- estimated confidence: 96%
