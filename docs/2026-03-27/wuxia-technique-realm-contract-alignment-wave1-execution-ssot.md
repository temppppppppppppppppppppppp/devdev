# Wuxia Technique-Realm Contract Alignment Wave 1 Execution SSOT

Date: 2026-03-27
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-27/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: multi-provider runtime/provider edits, stage3/stage4 contract-alignment edits, local logs/jsonl churn, wuxia narrative artifact churn, untracked 2026-03-27 docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-27/wuxia-technique-realm-tracking-design-memo.md`
- `docs/2026-03-26/wuxia-combat-scene-readiness-compact-survey.md`
- `docs/2026-03-26/wuxia-combat-quality-probe-report.md`
Evidence Artifacts:
- `modules/core/stage4_context_builder.py`
- `modules/core/world_state.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `config/genres/wuxia.yaml`
- `tests/test_stage4_context_builder.py`
- `tests/test_blocking_validator_submodules.py`
- `tests/test_validation.py`
Side-Effect Coverage: covered

## 1. Intent

- Realize the smallest bounded follow-up to `per-work-fact-contract-alignment-wave1` for the one residual seam that still matters in production: wuxia protagonist technique / realm contradictions.
- Make protagonist-side wuxia technique / realm authority more explicit to the LLM without introducing a new registry or persistence layer.
- Add one narrow consistency lane only for unambiguous protagonist technique-vs-realm mismatch, using current owners and current wuxia rule surfaces.

## 2. Baseline Facts

- `StateTracker` already owns protagonist technique accumulation through:
  - `protagonist_skills`
  - `skill_acquisitions`
- `WorldState` already surfaces protagonist skills inside the canonical body summary, but not in the tighter canonical precedence block.
- `config/genres/wuxia.yaml` already defines:
  - `realm_hierarchy`
  - `realm_technique_limits`
- The residual survey found:
  - protagonist technique / realm facts exist, but remain mostly advisory
  - NPC technique / realm facts have no persistent owner
  - the dominant remaining seam is not general authority anymore, but wuxia-specific technique / realm reconciliation
- Current evidence does **not** justify:
  - a per-work registry
  - NPC technique persistence
  - technique usage ledgering across episodes

## 3. Scope

Included:
- `modules/core/stage4_context_builder.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/validation/blocking_validator.py` only if a tiny facade hook is required
- bounded regression tests only

Excluded:
- `modules/domain/agents/state_tracker.py` storage contract changes
- `modules/domain/agents/state_tracker_npc.py` persistence expansion
- `modules/core/world_state.py` persistence redesign
- new registry or registry-like persistence layer
- NPC technique mastery tracking
- NPC realm progression tracking
- technique usage history / reveal ledger
- fight geography or combat choreography persistence
- destroyed-item Stage 3 pre-check
- broader Stage 3 truth-gate expansion

## 4. Pass 1. Inventory Summary

- Current owner split is already enough for a protagonist-only contract wave:
  - protagonist learned techniques: `StateTracker`
  - protagonist current realized state when present: `WorldState` / existing realized surfaces
  - allowed technique families per realm: `wuxia.yaml`
- The main missing contract is prompt-facing precedence:
  - realized protagonist technique / realm facts are not clearly ranked above stale seed or advisory phrasing
- The main missing enforcement is narrow:
  - a protagonist should not cleanly pass when a confirmed low realm is paired with a clearly disallowed technique family
- NPC technique / realm facts are a different class of problem:
  - not just precedence ambiguity
  - but missing persistent ownership

## 5. Pass 2. Semantic Classification

- Class A. Wuxia-specific prompt authority clarification
  - make protagonist technique / realm precedence explicit in the Stage 4 prompt path
- Class B. Narrow protagonist consistency enforcement
  - reject only clear protagonist technique-vs-realm mismatches when the current realm is explicitly confirmed
- Class C. Deferred modeling
  - NPC technique / realm persistence and technique usage history remain deferred

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 4 prompt text gains a short wuxia-only authority clause
  - blocking validator may emit one new protagonist technique / realm failure type
  - bounded tests only
- DB / schema / transaction boundaries:
  - not applicable; no storage mutation or schema work
- JSONL / log / audit sinks:
  - existing validation/advisory output may include one new technique / realm contradiction label
- console / UI / operator output:
  - Stage 4 / validation reporting may surface the new mismatch category through existing channels
  - no new UI surface
- rollback / recovery / retry:
  - no new retry system
  - existing validation pass/fail boundary remains the control surface
- cache / global state:
  - no new cache or singleton state
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- Preserve the current ownership spine:
  - `StateTracker` continues to own protagonist learned-technique accumulation
  - `WorldState` remains the realized-state surface when those facts are already available
  - `wuxia.yaml` remains the static capability rule source
- Add one short wuxia-only authority note to the Stage 4 canonical prompt path, but only when relevant protagonist technique / realm signals exist.
- Add one bounded validator check for protagonist technique-vs-realm mismatch:
  - only when current protagonist realm is explicit in the validation context or realized state
  - only when the manuscript clearly uses a technique family outside the allowed list for that realm
  - never synthesize a realm that is not already confirmed
- Keep NPC technique / realm completely out of this wave.

## 8. Execution Tranches

1. Tranche A. Stage 4 wuxia technique / realm authority statement
   - insert a short wuxia-only precedence statement adjacent to canonical Stage 4 context injection
   - clarify that confirmed realized protagonist technique / realm state outranks stale BI seed or advisory wording

2. Tranche B. Narrow protagonist technique-vs-realm consistency lane
   - add one bounded consistency check in `blocking_validator_consistency_checks.py`
   - consult `wuxia.yaml` realm limits only when a confirmed current realm exists
   - keep the mismatch definition narrow and unambiguous

3. Tranche C. Bounded regression coverage
   - extend existing Stage 4 context tests
   - extend existing `BlockingValidator` / consistency tests
   - add one tiny new test file only if existing test files cannot host the coverage cleanly

## 9. Acceptance Criteria

- Stage 4 explicitly communicates protagonist-side wuxia technique / realm precedence when relevant facts are present.
- The new authority statement stays short, local, and wuxia-only; it must not become a registry-like dump.
- The wave does **not** invent or persist new NPC technique / realm facts.
- If current protagonist realm is not explicitly confirmed, no new hard mismatch reject fires.
- If current protagonist realm is explicitly confirmed and manuscript technique use is clearly outside the allowed realm limit, the system surfaces a bounded contradiction through the validator path.
- No registry, DB table, schema, or persistence owner is introduced.

## 10. Verification Plan

- `python -m py_compile modules/core/stage4_context_builder.py modules/validation/blocking_validator_consistency_checks.py modules/validation/blocking_validator.py`
- `pytest tests/test_stage4_context_builder.py -q`
- `pytest tests/test_blocking_validator_submodules.py -q`
- `pytest tests/test_validation.py -q`
- if a new tiny test file is introduced, run it separately and keep it bounded to this wave
- `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py modules/validation/blocking_validator_consistency_checks.py modules/validation/blocking_validator.py tests/test_stage4_context_builder.py tests/test_blocking_validator_submodules.py tests/test_validation.py docs/2026-03-27/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md docs/temp/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Do not widen this into NPC technique persistence or NPC realm tracking.
- Do not add a new technique registry or event-history ledger.
- Do not touch `StateTracker` storage contracts unless implementation proves a tiny read-only helper is strictly necessary.
- Do not synthesize protagonist realm facts from loose manuscript hints when realized state is absent.
- Do not bundle fight geography, choreography repetition, or combat escalation work into this wave.
- If a clean protagonist-only mismatch rule cannot be defined from existing owners, stop and reopen scope rather than silently expanding modeling.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove temp mirror only after implementation + closure audit passes
- roadmap dependency: none; this is a single active bounded wave

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Structure and Scope
- the execution target matches the design memo:
  - protagonist-first contract clarification
  - one narrow protagonist technique-vs-realm consistency lane
- NPC modeling, registry work, and Stage 3 pre-check expansion remain excluded
- PASS

Pass 2. Evidence and Consistency
- residual survey and design memo both converge on the same seam: `technique-realm-tracking`
- live owner surfaces confirm protagonist technique accumulation exists today, while NPC technique ownership does not
- `wuxia.yaml` already provides the static rule surface required for a bounded protagonist mismatch check
- PASS

Pass 3. Execution Readiness
- touched production surface is bounded
- acceptance criteria are concrete
- verification plan is reproducible and narrow
- guardrails prevent this from turning into a registry or persistence project
- PASS

Estimated confidence: 96%

---

- Recommended direction: protagonist-contract-now / NPC-modeling-later
- Dominant unresolved seam: protagonist technique / realm precedence is still too implicit for prompt + validator consumption
- Should Codex open an execution SSOT now: yes

## 15. Closure Note

Closure Date: 2026-03-27
Closure Status: closed (closure-audited)

Realization Summary:
- Stage 4 now injects a short wuxia-only protagonist technique / realm authority clause when wuxia genre context and protagonist skill signals are present.
- `BlockingValidator` now owns one bounded wuxia-only protagonist technique-vs-realm consistency lane.
- The wave remained protagonist-first and did not introduce NPC technique persistence, registry work, or broader persistence redesign.

Verification Evidence:
- `python -m py_compile modules/core/stage4_context_builder.py modules/validation/blocking_validator_consistency_checks.py modules/validation/blocking_validator.py` -> PASS
- `pytest tests/test_stage4_context_builder.py -q` -> `101 passed`
- `pytest tests/test_blocking_validator_submodules.py -q` -> `29 passed`
- `pytest tests/test_validation.py -q` -> `33 passed`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py modules/validation/blocking_validator_consistency_checks.py modules/validation/blocking_validator.py tests/test_stage4_context_builder.py tests/test_blocking_validator_submodules.py tests/test_validation.py docs/2026-03-27/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md docs/temp/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md` -> PASS

Residual Risk:
- No blocking residual risk remains inside this wave scope.
- Stage 3 pre-checks are still unchanged in this wave; technique / realm mismatch remains a Stage 4 validation concern.
- NPC technique mastery, NPC realm persistence, technique usage history, and fight geography remain explicitly deferred.
- Missing or ambiguous protagonist realm still resolves to no-op by design.

Excluded Surface Check:
- `modules/domain/agents/state_tracker.py` not touched
- `modules/domain/agents/state_tracker_npc.py` not touched
- `modules/core/world_state.py` not touched
- Stage 3 pre-check surfaces not touched
- non-wuxia family logic was not broadened; hunter/fantasy/business flows remain gated out
