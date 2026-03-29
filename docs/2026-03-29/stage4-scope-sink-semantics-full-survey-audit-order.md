## Stage4 Scope Sink Semantics Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-scope-sink-semantics

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/runtime/tests plus narrative assets, temp queue, and canary artifacts; retry-loop-compression is the active realization lane`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `scope sink semantics` problem before any new sink-normalization or observability work.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Across Stage 4 runtime sinks, what does each field actually mean today for authoritative fix scope, derived retry scope, repair scope, conflict carryover, and rationale preservation, and where do operators currently risk reading different truths as if they were the same field?`

This survey exists because current evidence suggests:

- the `fix_scope` seam is now improved enough that `authoritative_fix_scope` appears in main JSONL sinks
- recent waves added:
  - `authoritative_fix_scope`
  - `authoritative_fix_scope_violation`
  - `conflict_contract`
  - near-pass rationale preservation
  - best-manuscript reuse metadata
- but Stage 4 still emits semantically adjacent fields through multiple sinks:
  - `authoritative_fix_scope`
  - derived `fix_scope`
  - `repair_scope`
  - `selection_reason`
  - `open_review`
  - `conflict_contract`
  - `reuse_contract`
- the retry-loop-compression validation wave will be easier to interpret if sink meanings are explicitly mapped before any new semantic drift accumulates

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-scope-sink-semantics-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- sink or persistence paths directly linked from the inspected code:
  - `logs/session/decisions.jsonl`
  - `logs/episode_production.jsonl`
  - `logs/runtime_audit.jsonl`
  - `logs/session/ui_events.jsonl`
  - `logs/session/llm_io.jsonl` only if a sink meaning depends on it
  - DB-facing payload builders such as `stage_attempts`, `director_selections`, or adjacent session rows when reachable from code
- recent live evidence as support:
  - `projects/canary_0328_gemini_direct_fixscope_check/logs/`
  - `projects/canary_0328_sink_verify_micro/logs/`
  - `projects/canary_0329_feedback_windowing_check/logs/`
  - `projects/canary_0329_retry_loop_compression_check/logs/` if present
- prior bounded context only as support:
  - `docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`
  - `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`
  - `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`

Excluded surfaces:

- provider-default redesign
- provider fallback observability redesign except where sink meaning directly depends on served-vs-attempted truth
- narrative-pipeline artifacts
- broad UI redesign
- new execution SSOT authoring
- code changes

### 4. Survey Questions

The survey must answer all of these.

1. Authoritative scope truth
- Where is Director-authored scope authoritative today?
- Which sink or payload should an operator trust first for:
  - `authoritative_fix_scope`
  - `authoritative_fix_scope_violation`
  - Director-authored rationale
- Where is that authoritative value copied, normalized, renamed, or dropped?

2. Derived scope truth
- Where is runtime-derived retry scope decided?
- Which sinks expose derived `fix_scope` versus lane-oriented `repair_scope`?
- Which fields describe:
  - rewrite lane
  - patch lane
  - carryover/reuse decision
  - escalation state
- Where can one round show `authoritative_fix_scope`, derived `fix_scope`, and `repair_scope` simultaneously, and what does each one mean?

3. Rationale and carryover truth
- For `selection_reason`, `open_review`, `fix_pack`, `conflict_contract`, and `reuse_contract`:
  - where do they originate?
  - which sink is intended to preserve them?
  - where are they intentionally blanked or omitted?
- In `post_select_conflict` and similar downgraded PASS paths, which rationale fields are preserved, stripped, or rewritten?

4. Sink divergence risk
- Which operator-facing sinks currently compress different semantics into one visual slot?
- Rank the highest-risk misreads, such as:
  - reading derived `fix_scope` as if it were Director-authored
  - reading `repair_scope` as if it were synonymous with retry `fix_scope`
  - assuming rationale loss means manuscript loss
  - assuming absent DB fields mean absent JSONL fields

5. Smallest safe next move
- After the survey, what is the smallest safe next move?
- Rank only bounded options such as:
  - rename or relabel operator-facing sink fields
  - document sink authority explicitly
  - add missing additive metadata to one sink family
  - leave code alone and tighten post-mortem reading rules
  - no change because current semantics are already acceptably separated

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Field Origin and Ownership Map
4. Sink-by-Sink Semantics Matrix
5. Live Canary Divergence Evidence
6. Root-Cause Assessment
7. Highest-Risk Operator Misreads
8. Bounded Remediation Options Ranked
9. Recommended Bounded Next Step
10. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When comparing sinks:

- preserve the difference between:
  - Director-authored `authoritative_fix_scope`
  - runtime-derived `fix_scope`
  - lane or retry-facing `repair_scope`
  - rationale fields
  - carryover or conflict payloads
- do not collapse those into one generic `scope` statement

When using live canary evidence:

- prefer raw rows from `decisions.jsonl` and `episode_production.jsonl`
- use DB or side sinks only when the code proves those sinks are fed by the same round identity
- label inference explicitly if the sink relationship is not directly evidenced

When discussing missing fields:

- distinguish:
  - field absent by design
  - field dropped by one sink family only
  - field intentionally blanked for one reject family
  - field unexpectedly lost

Do not assume DB absence means runtime absence.
Do not assume JSONL presence means DB parity.

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a broad Stage 4 redesign survey.

Do not reopen:

- provider-default work
- fallback observability work
- feedback windowing work
- retry-loop-compression implementation scope

unless inspected code proves a direct semantic dependency.

Do not recommend Python-side story judgment changes.
Do not recommend removing sink detail just to simplify dashboards.
This survey is about clarifying field meaning and sink authority, not flattening evidence.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`freeze one explicit semantics matrix for authoritative_fix_scope, derived fix_scope, repair_scope, and carryover/rationale fields so operators and future canaries stop reading distinct sink meanings as one truth`

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
