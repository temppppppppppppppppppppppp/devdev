Date: 2026-03-24
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-24/genre-contamination-guardrail-execution-ssot.md`
Temp Mirror Path: `removed after closure (former path: docs/temp/genre-contamination-guardrail-execution-ssot.md)`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: active stage4/state/writer edits and deleted historical project artifacts; docs/temp queue currently empty except queue-state.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD; bounded realization landed in main_a.py, director.py, stage4_context_builder.py, validation/scoring/continuity/blocking fallbacks, and targeted regression tests`
Source Survey Docs:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-24/현상황요약.txt`
Evidence Artifacts:
- live source anchors in `main_a.py`, `director.py`, `stage4_context_builder.py`, and validator modules
Side-Effect Coverage: yes

---

# Bounded Genre Contamination Guardrail Execution SSOT

## 1. Intent

Realize one compact guardrail wave that stops `silent wuxia fallback` from contaminating Director/validator behavior in non-wuxia runs.

Primary symptom:
- on non-wuxia work, Director or downstream validators can still speak as if the work were wuxia and emit feedback like `무협, 내공 쓰지 마`

Primary goal:
- keep explicit genre specialization for `wuxia` and `investment`
- stop `genre missing -> wuxia by default` from leaking into judgment text or guard behavior

## 2. Baseline Facts

Positive baseline:
- `modules/domain/agents/chief_writer_context.py:34-45` already has explicit alias normalization for `wuxia` and `investment`
- this means the workspace already has one usable model for explicit genre resolution instead of silent defaulting

Contamination evidence:
- `main_a.py:1168-1170`, `main_a.py:1265`, `main_a.py:1622`, `main_a.py:3374`
  - critical app paths still fall back to `wuxia`
- `modules/domain/agents/director.py:40`
  - Director instance default genre is `wuxia`
- `modules/core/stage4_context_builder.py:2302`
  - Stage 4 writer-context build falls back to display name `무협`
- `modules/validation/validation_orchestrator.py:194`, `modules/validation/validation_orchestrator.py:279`, `modules/validation/validation_orchestrator.py:1297-1313`
  - validator constructor, threshold profile fallback, and fallback constitution all treat `wuxia` as the generic default
- `modules/validation/scoring_validator.py:916-917`
  - scoring weights fall back to `wuxia`
- `modules/validation/continuity_validator.py:243`
  - continuity branch condition treats missing genre as `wuxia`
- `modules/validation/blocking_validator_consistency_checks.py:42-43`
  - blocking consistency checks also default missing genre to `wuxia`

Working interpretation:
- the issue is not “genre-specific logic exists”
- the issue is “genre-agnostic or missing-genre paths are not neutral; they silently become wuxia-shaped”

## 3. Scope

Included:
- `main_a.py`
- `modules/domain/agents/director.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/validation_orchestrator.py`
- `modules/validation/scoring_validator.py`
- `modules/validation/continuity_validator.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- one bounded shared helper or reuse path for explicit active-genre normalization
- targeted tests for `investment` path and missing-genre handling

Excluded:
- global rename of `martial_hud`
- repo-wide genre architecture rewrite
- narrative-router family changes
- “support every genre equally” campaign
- removal of explicit `wuxia` or `investment` specialization where genre is known
- desktop/UI copy cleanup outside the touched runtime path

## 4. Pass 1. Inventory Summary

- current codebase supports genre-specific behavior by design
- the contamination risk is concentrated in a small number of default/fallback seams
- most dangerous seams are:
  - Director object default genre
  - Stage 4 context-builder display-name fallback
  - validator/scoring/continuity fallback profiles
- the likely user-facing symptom is genre-inappropriate rejection/advice text, not data corruption

## 5. Pass 2. Semantic Classification

- Class A. Active genre resolution
  - resolve current genre once, explicitly, at critical Stage 4 / Director entry surfaces
- Class B. Neutral fallback behavior
  - if genre is absent or unsupported, use a neutral/default profile instead of `wuxia`
- Class C. Observability
  - when a critical path cannot resolve genre, emit one bounded warning/debug note rather than silently acting wuxia
- Class D. Regression lock
  - investment path must not inherit wuxia-only wording or martial-specific checks purely through fallback

## 6. Side-Effect Map

- file writes / artifacts:
  - source code only
  - no new artifact family required
- DB / schema:
  - not applicable
- JSONL / audit / metrics:
  - optional bounded warning/debug only if genre resolution is missing
- console / operator output:
  - possible one-line genre-resolution warning in touched critical paths
- retry / verdict behavior:
  - affected indirectly because wrong genre policy should stop contaminating judgment text
- config / bootstrap:
  - touched only where default genre fallback currently hardcodes `wuxia`

## 7. Realization Architecture

Bounded design:
- do not chase every `wuxia` string in the repo
- touch only paths where missing genre can alter Director/validator behavior

Recommended approach:
1. introduce or reuse one small shared resolver that returns an explicit runtime genre code
2. use that resolver at app/stage4/director critical boundaries
3. replace `wuxia` fallback in touched validator paths with a neutral fallback profile
4. keep explicit `wuxia` and `investment` special behavior intact when genre is known

Neutral fallback rule:
- unknown or absent genre should not imply martial vocabulary, wuxia constitution, or wuxia score weights
- unknown genre may use:
  - neutral/default threshold profile
  - no genre-specific constitution amendment
  - no wuxia-only continuity branch

## 8. Execution Tranches

1. Critical genre-resolution seam
- remove silent `wuxia` fallback from touched `main_a.py`, `director.py`, and `stage4_context_builder.py`
- ensure touched Director/Stage 4 paths carry the explicit current genre through

2. Validator neutralization seam
- replace touched validator/scoring/continuity/consistency fallbacks that currently default to `wuxia`
- add one bounded neutral fallback profile / constitution path if needed

3. Operator guardrail seam
- add one bounded warning/debug signal when a critical Director/validator path reaches “genre unresolved”

4. Regression lock
- add tests that prove:
  - `investment` does not inherit wuxia-specific wording through fallback
  - explicit `wuxia` still gets wuxia-specific behavior
  - missing genre in touched paths does not silently act as `wuxia`

## 9. Acceptance Criteria

- touched non-wuxia critical paths no longer default to `wuxia`
- touched validators do not emit wuxia-only reasoning or weight profile solely because genre was missing
- explicit `investment` path is preserved
- explicit `wuxia` path is preserved
- one bounded operator/dev signal exists for unresolved genre in touched critical paths
- no global rename wave is opened
- no DB schema or persistence contract changes are introduced

## 10. Verification Plan

- `python -m py_compile main_a.py modules/domain/agents/director.py modules/core/stage4_context_builder.py modules/validation/validation_orchestrator.py modules/validation/scoring_validator.py modules/validation/continuity_validator.py modules/validation/blocking_validator_consistency_checks.py`
- targeted pytest shards for:
  - Director genre-resolution tests
  - Stage 4 context builder genre-resolution tests
  - validator/scoring/continuity fallback tests
  - one `investment` regression asserting no wuxia-specific fallback language in touched paths
  - one `wuxia` no-regression assertion for touched paths
- `python scripts/check_utf8_hygiene.py docs/2026-03-24/genre-contamination-guardrail-execution-ssot.md docs/temp/genre-contamination-guardrail-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

Optional fresh verification after realization:
- one bounded `investment` Stage 4 smoke path
- one bounded `wuxia` no-regression smoke path

## 11. Guardrails

- do not widen into a repo-wide terminology cleanup
- do not rename `martial_hud` in this wave
- do not remove legitimate wuxia specialization
- do not add “generic genre abstraction” layers beyond one bounded resolver/profile path
- do not treat unsupported genre expansion as part of this item
- optimize for `wuxia + investment + missing-genre safety`, not universal elegance

## 12. Temp Queue Notes

- temp status: closed; mirror removed after closure audit
- cleanup condition:
  - realization complete
  - canonical status updated after closure audit
  - temp mirror removed
- roadmap dependency:
  - none

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue-state tracking: `python scripts/sync_temp_queue_state.py`
- execution-start rule:
  - keep this bounded to touched Director / Stage 4 / validator fallback seams only

## 14. 3-Pass Audit Summary

Pass 1. Structure and Scope
- compact execution SSOT only
- widened neither into global survey nor full genre cleanup

Pass 2. Evidence and Consistency
- grounded in live source anchors where missing genre still falls back to `wuxia`
- explicit positive counterexample (`chief_writer_context.py`) shows a narrower normalization model already exists

Pass 3. Execution and Readability
- tranches, acceptance criteria, and verification plan are small enough for direct realization
- refactor ambition is explicitly capped

Confidence
- estimated confidence: 97%

## 15. Closure Note

- Realization state:
  - closed
- Closure audit result:
  - touched Director / Stage 4 / validator fallback seams no longer silently default to `wuxia`
  - explicit `wuxia` and `investment` behavior remain intact in the touched paths
  - one bounded warning path now exists when critical genre resolution is missing

### Implemented Scope Confirmed

- Critical genre-resolution seam:
  - `main_a.py`
  - `modules/domain/agents/director.py`
  - `modules/core/stage4_context_builder.py`
- Validator neutralization seam:
  - `modules/validation/validation_orchestrator.py`
  - `modules/validation/scoring_validator.py`
  - `modules/validation/continuity_validator.py`
  - `modules/validation/blocking_validator_consistency_checks.py`
- Regression lock:
  - `tests/test_genre_contamination_guardrail.py`
  - `tests/test_director_modules.py`

### Verification Evidence

- `python -m py_compile main_a.py modules/domain/agents/director.py modules/core/stage4_context_builder.py modules/validation/validation_orchestrator.py modules/validation/scoring_validator.py modules/validation/continuity_validator.py modules/validation/blocking_validator_consistency_checks.py`
- `pytest tests/test_genre_contamination_guardrail.py tests/test_validation_orchestrator.py tests/test_validation_orchestrator_soft_failure.py tests/test_director_modules.py tests/test_main_a_init_bootstrap.py tests/test_main_a_packaged_bootstrap_contract.py tests/test_quality_sidecar_bootstrap.py -q` -> `168 passed`
- implementation-run evidence reported at handoff:
  - new guardrail tests `28/28 PASS`
  - existing validation tests `49/49 PASS`
  - existing director tests `128/128 PASS`
  - existing bootstrap tests `10/10 PASS`
- `python scripts/check_utf8_hygiene.py main_a.py modules/domain/agents/director.py modules/core/stage4_context_builder.py modules/validation/validation_orchestrator.py modules/validation/scoring_validator.py modules/validation/continuity_validator.py modules/validation/blocking_validator_consistency_checks.py tests/test_genre_contamination_guardrail.py tests/test_director_modules.py docs/2026-03-24/genre-contamination-guardrail-execution-ssot.md docs/temp/genre-contamination-guardrail-execution-ssot.md`

### Residual Risk

- out-of-scope fallback residues still exist:
  - `director_grading.py` has two `... else "wuxia"` sites
  - `main_a.py` `_apply_genre_bindings` still uses `.get("type", "wuxia")`, but only after selected genre existence checks
  - `NarrativeDiversityEngine` constructor still defaults to `wuxia`
- downstream consumers receiving `""` genre may emit generic text; this is neutral behavior, but not exhaustively unit-tested beyond the touched paths
- those residuals do not block closure because they were excluded by this compact SSOT

### Temp Cleanup

- `docs/temp/genre-contamination-guardrail-execution-ssot.md` removed after canonical closure update
- `docs/temp/queue-state.json` must show the queue as empty after sync
