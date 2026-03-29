## Stage4 Carryover Contract Consumption Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-carryover-contract-consumption

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/provider/runtime/tests plus temp queue, canary artifacts, and narrative assets; scope-sink-semantics micro validation is the current adjacent live check`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `carryover contract consumption` problem before any new prompt-surface or retry-lane changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Which carryover fields written during downgraded PASS or retry handoff are actually consumed by the next round generation path, which are operator-only persistence, and where does stored carryover truth stop affecting Chief Writer behavior?`

This survey exists because current evidence suggests:

- recent waves improved persistence and operator visibility for:
  - `best_manuscript`
  - `selection_reason`
  - `open_review`
  - `conflict_contract`
  - `reuse_contract`
  - `scope_origin`
- retry-loop-compression live validation suggests reuse and rationale preservation now matter operationally
- but it is still not explicit which carryover fields:
  - are merely written to sinks
  - are actually consumed by `Chief Writer` prompt assembly
  - are consumed only on some lanes or families
  - are lost before prompt-time even though they were persisted earlier

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-carryover-contract-consumption-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- prompt or payload builders directly linked from those files
- targeted tests as support:
  - `tests/test_chief_writer_candidate_lane_f.py`
  - `tests/test_stage4_handoff_carryover_guardrail.py`
  - `tests/test_stage4_interview_round.py`
- operator sinks only as evidence of persistence versus consumption:
  - `logs/session/decisions.jsonl`
  - `logs/episode_production.jsonl`
  - `logs/runtime_audit.jsonl`
- live evidence as support where present:
  - `projects/canary_0329_retry_loop_compression_check/logs/`
  - `projects/canary_0329_scope_sink_semantics_check/logs/`
- prior bounded context only as support:
  - `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
  - `docs/2026-03-29/stage4-scope-sink-semantics-full-survey.md`
  - `docs/2026-03-29/stage4-scope-sink-semantics-execution-ssot.md`

Excluded surfaces:

- provider-default or fallback observability work
- broad scope-sink rename or DB schema work
- broad Stage 4 routing redesign
- narrative-pipeline artifacts
- new execution SSOT authoring
- code changes

### 4. Survey Questions

The survey must answer all of these.

1. Carryover write truth
- Where are these fields first created or enriched?
  - `best_manuscript`
  - `selection_reason`
  - `open_review`
  - `conflict_contract`
  - `reuse_contract`
- On which reject or downgraded PASS families are they preserved, blanked, or omitted?

2. Carryover read truth
- Which of those fields are actually read by the next-round generation path?
- Which function or prompt builder consumes each field?
- Which fields affect prompt text, structured prompt blocks, lane metadata, or retry strategy?

3. Prompt-surface truth
- For each carryover field, classify whether it is:
  - persisted-only
  - prompt-consumed
  - lane-consumed but not prompt-visible
  - dead or effectively ignored
- If `best_manuscript` is reused, how is it injected:
  - full baseline manuscript
  - excerpted context
  - rationale-only mention
  - structured contract block

4. Family-specific consumption truth
- In `post_select_conflict` and other downgraded PASS paths, which carryover fields survive all the way into the next Chief Writer prompt?
- In continuity-firewall or broader rewrite families, which carryover fields are intentionally ignored even if present?
- Where does runtime preserve a field for operator evidence only, without generation reuse?

5. Smallest safe next move
- After the survey, what is the smallest safe next move?
- Rank only bounded options such as:
  - documenting true consumption semantics only
  - wiring one already-persisted field into one prompt block
  - removing misleading dead carryover fields
  - leaving current behavior as-is because persistence is intentionally operator-only

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Carryover Field Origin Map
4. Carryover Field Consumption Matrix
5. Prompt-Surface Injection Map
6. Live Canary Evidence
7. Root-Cause Assessment
8. Highest-Risk Misreads
9. Bounded Remediation Options Ranked
10. Recommended Bounded Next Step
11. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When discussing consumption:

- distinguish `stored` from `consumed`
- distinguish `prompt-consumed` from `operator-visible only`
- distinguish `same-round runtime metadata` from `next-round generation input`
- do not infer prompt consumption merely because a field appears in JSONL or DB sinks

When discussing carryover fields:

- explicitly separate:
  - `best_manuscript`
  - rationale fields such as `selection_reason` and `open_review`
  - structured contracts such as `conflict_contract` and `reuse_contract`
- do not collapse them into one generic `carryover` statement

When using live canary evidence:

- treat canary logs as persistence proof only unless code and raw prompt assembly show actual downstream consumption
- label inference explicitly if live evidence cannot prove the exact prompt block

When discussing missing impact:

- distinguish:
  - field persisted but never read
  - field read but not rendered into prompt text
  - field read only on one retry family
  - field consumed indirectly through a summarized helper

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a broad Stage 4 redesign survey.

Do not reopen:

- provider-default work
- fallback observability work
- feedback-windowing work
- retry-loop-compression routing policy
- broad scope-sink semantics work

unless inspected code proves a direct dependency on carryover consumption.

Do not recommend Python-side story judgment changes.
Do not recommend forcing patch lane just because carryover exists.
This survey is about `consumption truth`, not lane redesign.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`freeze one explicit matrix for carryover fields that says which fields are only persisted, which fields are actually consumed by next-round generation, and which ones merely look important in operator sinks while having no behavioral effect`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and raw canary artifacts.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation if ROI is still high
3. only then code changes
