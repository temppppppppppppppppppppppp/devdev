# Protagonist Overvaluation Mini Bible + Blueprint Wave 1 Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/protagonist-overvaluation-mini-bible-blueprint-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: active Stage 3 wave edits, canary helper changes, dated survey/docs, project/log churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-25/protagonist-overvaluation-staging-4terminal-merge-audit.md`
- `docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-design.md`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-25/opus-protagonist-overvaluation/t1-bible-owner-mapping.md`
- `docs/2026-03-25/opus-protagonist-overvaluation/t3-blueprint-staging.md`
- `docs/2026-03-25/stage3-partial-canary-3terminal-merge-audit.md`
Side-Effect Coverage: covered

## 1. Intent
- Realize the first bounded `주인공 고평가` quality-up wave as `mini bible note + blueprint-first staging`.
- Keep the blast radius small enough that the wave stays narrative-design oriented, not a new system refactor.
- Use the now-stable Stage 3 baseline to add admiration-mode guidance without reopening deferred system lanes.

## 2. Baseline Facts
- The owner split is stable:
  - Bible defines admiration principles.
  - Blueprint executes admiration through scenes, observers, reveal order, and information gaps.
  - Arc distributes later.
  - Manuscript renders later.
- The design note converged on four admiration axes:
  - method quality
  - conditional reversal
  - information asymmetry
  - hierarchy shock
- The design note also converged on four forbidden praise patterns:
  - `big_number_wow`
  - `uniform_reaction`
  - `narrator_hype`
  - `instant_recognition`
- The current Stage 3 system-track culprit family is suppressed, so this wave is justified as a quality-up wave rather than a bug-fix wave.
- No deferred system lane was promoted to `yes-now` after canary, so this wave should stay bounded to narrative-design surfaces only.

## 3. Scope
Included:
- `modules/core/genre_guards/work_guard.py`
- `config/prompts/ensemble.yaml`
- `tests/test_work_guard.py`
- `tests/test_prompt_loader.py`
- `tests/test_tier4_ensemble_caching.py`
- `tests/test_protagonist_overvaluation_wave1.py`

Excluded:
- `modules/domain/agents/blueprint_ensemble.py`
- `config/prompts/director.yaml`
- Stage 2 / Arc schema changes
- Stage 4 writer prompt changes
- manuscript POV trigger expansion
- `side_glimpse` preset redefinition
- Python hard gates for admiration quality
- DB schema, JSONL schema, artifact naming, queue/roadmap design
- work-specific content authoring for any individual project `work_guard.yaml`

## 4. Pass 1. Inventory Summary
- Live owner surfaces already exist:
  - Work identity parsing and prompt surfacing live in `modules/core/genre_guards/work_guard.py`.
  - Blueprint generation prompt lives in `config/prompts/ensemble.yaml`.
- Blueprint already consumes WorkGuard retrieval-contract text through `get_retrieval_contract_prompt("blueprint")`, so this wave can avoid `blueprint_ensemble.py` changes.
- Existing WorkGuard tests already cover:
  - work identity prompt surfacing
  - retrieval contract text
  - director advisory
- Existing prompt tests already cover loader and ensemble prompt stability.

## 5. Pass 2. Semantic Classification
- Class A. `mini bible note substrate`
  - Add bounded optional `work_identity.protagonist_evaluation` support in WorkGuard.
  - Treat it as advisory identity context, not as a validator or hard gate.
- Class B. `blueprint execution guidance`
  - Add prompt-level admiration staging guidance to `BLUEPRINT_GENERATION_PROMPT`.
  - Keep it static text only in this wave.
- Class C. `deferred layers`
  - Director review usage
  - Arc mode distribution
  - manuscript rendering refinements
  - hard validation or observability

## 6. Side-Effect Map
- file writes / artifacts:
  - touched files limited to WorkGuard code, blueprint prompt YAML, and tests
  - no runtime artifact path or naming changes
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - no new persistent sink required in this wave
  - optional existing WorkGuard/operator text may become richer
- console / UI / operator output:
  - no new dashboard lane required
  - prompt/advisory text may include `protagonist_evaluation` guidance
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - PromptLoader cache sees updated `ensemble.yaml`
  - WorkGuard in-memory identity summary gains one optional bounded section
- bootstrap fallback / config-env mutation:
  - optional WorkGuard config shape expands
  - no env mutation

## 7. Realization Architecture
- Use the existing WorkGuard `work_identity` owner rather than inventing a new schema family.
- Keep `protagonist_evaluation` bounded as an optional nested mapping under `work_identity`.
- In this wave, only four compact subfields are allowed:
  - `admiration_axes`
  - `forbidden_praise_patterns`
  - `observer_tiers`
  - `evaluation_thresholds`
- All four subfields remain string-list style only in Wave 1.
- WorkGuard responsibilities in this wave:
  - validate the optional nested mapping shape
  - surface the section in `get_v20_purism_prompt()`
  - surface a compact stage-specific form in `get_retrieval_contract_prompt("blueprint")`
- Blueprint responsibilities in this wave:
  - consume the above retrieval contract if present
  - also receive static staging guidance in `BLUEPRINT_GENERATION_PROMPT`
- Practical limit:
  - Tranche A only affects live works that actually populate `work_identity.protagonist_evaluation`
  - Tranche C still provides bounded generic improvement even when that work-specific section is absent
- Do not add dynamic variable slots or schema-bound scene fields in this wave.

## 8. Execution Tranches
1. `Tranche A — WorkGuard mini bible note substrate`
   - extend WorkGuard config validation to allow optional `work_identity.protagonist_evaluation`
   - support only the four bounded list fields named in this SSOT
   - surface them in `[작품 정체성 SSOT]` with concise labels
2. `Tranche B — Blueprint retrieval-contract surfacing`
   - enrich `get_retrieval_contract_prompt("blueprint")` so Stage 3 sees a compact admiration contract when the new section exists
   - focus on:
     - admiration axes
     - forbidden praise patterns
     - observer tier awareness
     - threshold reminder
   - keep the contract advisory and short
3. `Tranche C — Static blueprint staging guidance`
   - add a bounded block to `BLUEPRINT_GENERATION_PROMPT`
   - require blueprint-level attention to:
     - observer allocation
     - information asymmetry
     - reveal ordering
     - show-not-tell admiration
     - avoidance of raw-number hype and uniform reactions
   - do not add new template variables
4. `Tranche D — Regression and wave tests`
   - extend WorkGuard tests for new config shape and retrieval-contract surfacing
   - add `tests/test_protagonist_overvaluation_wave1.py` for the blueprint prompt block and WorkGuard blueprint-contract surfacing
   - preserve existing prompt-loader and cache regressions

## 9. Acceptance Criteria
- `work_identity.protagonist_evaluation` is optional and backward-compatible.
- Existing WorkGuard configs without the new section still validate unchanged.
- When the new section is present, WorkGuard surfaces it in:
  - `get_v20_purism_prompt()`
  - `get_retrieval_contract_prompt("blueprint")`
- `BLUEPRINT_GENERATION_PROMPT` gains protagonist-overvaluation staging guidance without new template variables.
- The wave does not touch:
  - Director prompts
  - Stage 4 writer prompts
  - Arc schema
  - manuscript runtime
  - DB/log schemas

## 10. Verification Plan
- `python -m py_compile modules/core/genre_guards/work_guard.py`
- `python -c "import yaml; yaml.safe_load(open('config/prompts/ensemble.yaml', encoding='utf-8'))"`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_work_guard.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_prompt_loader.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_tier4_ensemble_caching.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_protagonist_overvaluation_wave1.py -q`
- `python scripts/check_utf8_hygiene.py modules/core/genre_guards/work_guard.py config/prompts/ensemble.yaml tests/test_work_guard.py tests/test_protagonist_overvaluation_wave1.py docs/2026-03-25/protagonist-overvaluation-mini-bible-blueprint-wave1-execution-ssot.md docs/temp/protagonist-overvaluation-mini-bible-blueprint-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not open Director prompt changes in this wave.
- Do not open Stage 4 writer or POV-trigger changes in this wave.
- Do not add Python hard-gate validation for admiration quality in this wave.
- Do not add new blueprint schema fields in this wave.
- Do not redefine `side_glimpse`; only add bounded guidance around observer/reaction usage.
- Do not author or mass-edit project-specific `work_guard.yaml` files in this wave.
- Keep all new `protagonist_evaluation` fields compact string lists; no deep nested taxonomy objects yet.
- If WorkGuard retrieval-contract growth becomes too long, trim the contract rather than moving logic into `blueprint_ensemble.py`.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - implementation complete
  - targeted verification complete
  - Codex closure audit complete
- roadmap dependency:
  - none while this is the only active execution item

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Notes
- Pass 1 scope result:
  - bounded to Wave 1A + Wave 1B only
  - no downstream narrative-system redesign opened
- Pass 2 evidence result:
  - owner mapping and design shape are consistent with the saved merge audit and design note
  - live code confirms WorkGuard and blueprint prompt are the relevant execution owners
- Pass 3 actionability result:
  - implementation surfaces are explicit
  - verification is targeted
  - exclusions and blast radius are explicit
- Estimated confidence: 96%

## 15. Closure Audit Note
- Implemented surfaces:
  - `modules/core/genre_guards/work_guard.py`
  - `config/prompts/ensemble.yaml`
  - `tests/test_work_guard.py`
  - `tests/test_protagonist_overvaluation_wave1.py`
- Closure verification rerun by Codex:
  - `py_compile` passed
  - `pytest tests/test_work_guard.py -q` passed
  - `pytest tests/test_protagonist_overvaluation_wave1.py -q` passed
  - `pytest tests/test_prompt_loader.py -q` passed
  - `pytest tests/test_tier4_ensemble_caching.py -q` passed
  - UTF-8 hygiene passed after bounded allow-line markers on legitimate regex lines in `work_guard.py`
  - `ops_validator.py` passed
- Residual risk:
  - live effect of `protagonist_evaluation` still depends on a work actually populating that optional WorkGuard section
  - blueprint prompt staging should still be checked in a future bounded canary for pass-rate drift / overcorrection risk
