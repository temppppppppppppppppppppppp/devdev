## Stage4 Decision Contract Matrix Full Survey Audit Order

Date: 2026-03-28
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-decision-contract-matrix

### 1. Goal

Run a bounded system-track survey on the full Stage 4 decision contract before any further broad code changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`What are the actual Stage 4 decision contracts across prompt, Director output, runtime normalization, retry routing, and fail-closed behavior, and where are the current mismatches that can create hidden defect families?`

This survey exists because recent work and canary evidence suggest:

- hidden defects are surfacing as contract mismatches, not just as isolated bugs
- `fix_pack` was only one visible mismatch inside a larger decision matrix
- fake patch lanes, empty fix packs, IFC bridge behavior, and feedback snowball all sit on top of implicit contracts
- the current system lacks a single explicit matrix for:
  - verdict semantics
  - `fix_scope`
  - required fields
  - allowed retry lanes
  - fail-closed fallback behavior

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `config/prompts/director.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_orchestrator.py`
- relevant tests under:
  - `tests/test_director_modules.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_chief_writer.py`
  - `tests/test_chief_writer_patch_mode_wave9.py`
- recent bounded survey context only as support:
  - `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`
  - `docs/2026-03-28/stage4-ifc-bridge-full-survey.md`
  - `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
- recent canary evidence only as support, not sole truth:
  - `projects/canary_0328_golden_new2_s4/logs/`
  - `projects/canary_0328_stage4_ifc_bridge_check/logs/`
  - any fresh canary logs generated after the current prompt fix, if available during survey time

Excluded surfaces:

- Stage 2 and Stage 3 redesign
- blueprint generator redesign
- provider abstraction redesign
- canary runner redesign
- desktop/UI product work
- narrative-quality diagnosis outside Stage 4 contract semantics
- execution SSOT authoring

### 4. Survey Questions

The survey must answer all of these.

1. Prompt-to-runtime contract matrix
- For each relevant Stage 4 prompt family, what does the prompt require for:
  - `PASS`
  - `PASS_WITH_FIX`
  - `REJECT`
  - `fix_scope = inplace | partial | full`
- Which requirements are explicit?
- Which are only implied?
- Which runtime layers assume stronger rules than the prompt guarantees?

2. Director output contract truth
- What exact output fields does the runtime depend on from Director?
- Which fields are optional in practice?
- Which fields become mandatory only under certain verdicts or fix scopes?
- Where do `verdict`, `final_verdict`, `director_verdict`, `fix_scope`, `repair_scope`, `fix_pack`, `feedback`, and `action_items` first diverge?

3. Runtime normalization and enforcement truth
- Where are fields normalized, downgraded, widened, or reclassified?
- Which rules are true hard gates?
- Which rules are advisory only?
- Which fail-closed behaviors exist today?
- Which fail-closed gaps still remain?

4. Retry-lane contract truth
- For each retry lane, what are the real entry requirements?
- What combinations of:
  - verdict
  - fix_scope
  - fix_pack_contract
  - reject bucket
  - pathology streak
  lead to:
  - `inplace`
  - `patch_revision`
  - `rewrite_regenerate`
  - higher-repair candidates

5. Hidden mismatch inventory
- Beyond `empty fix_pack`, what other hidden contract mismatches are already visible?
- At minimum, inspect whether these are true mismatches, mere observations, or already-correct contracts:
  - `fix_scope` vs `repair_scope`
  - `QUALITY_ISSUE` vs logic-like streak counting
  - `director_feedback` accumulation vs advisory-only intent
  - `REJECT + local scope` vs required repair payload
  - `scene_model` vs local target kinds

6. Minimal harness opportunities
- Which contract rows should be made explicit in a harness or matrix first?
- Rank only bounded opportunities, not redesign.
- Example categories:
  - `verdict x fix_scope x required fields`
  - `allowed lane transition table`
  - `fail-closed table`
  - `prompt/runtime consistency assertions`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Stage4 Decision Surface Map
4. Prompt-to-Runtime Contract Matrix
5. Runtime Enforcement Matrix
6. Retry Lane Transition Matrix
7. Hidden Mismatch Inventory
8. Recent Canary Interpretation
9. Recommended Bounded Harness Priorities
10. Open Questions
11. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

The survey must distinguish:

- explicit contract
- implied contract
- runtime assumption
- enforced hard gate
- advisory-only behavior

When using canary evidence:

- treat it as support for observed failure families
- do not let one contaminated run override line-level code truth
- separate provider contamination from contract failure

When discussing today's harness-like changes:

- do not call them "the cause" unless a line-level causal path exists
- do not flatten everything into "prompt bug" if runtime assumptions materially differ

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full Stage 4 redesign survey.

Do not stop at `fix_pack`.
This survey must treat `fix_pack` as one row in a wider decision matrix.

Do not overclaim hidden diseases without showing the specific contract row that mismatches.

Do not turn this into a blame document about Python vs LLM.
This is a contract-map survey, not a component-shaming exercise.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest next operating move is:

`formalize Stage 4 as an explicit decision-contract matrix, then tighten the highest-risk rows via harness-like fail-closed rules`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and evidence.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation
3. only then code changes
