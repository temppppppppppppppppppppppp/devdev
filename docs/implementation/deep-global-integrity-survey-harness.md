# Deep Global Integrity Survey Harness

Date: 2026-03-14
Status: active
Applies To: system-track repo-wide surveys that must maximize depth, rigor, and integrity confidence
Companion First-Read:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
Related Model:
- `docs/implementation/deep-global-integrity-survey-20-stage-model.md`
Related Contracts:
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/single-ssot-roadmap-contract.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`
Related Templates:
- `docs/implementation/deep-global-survey-template.md`
- `docs/implementation/cross-cut-integrity-matrix-template.md`
- `docs/implementation/uncertainty-contradiction-ledger-template.md`

## 1. Purpose
- Provide the high-rigor operating layer for codebase-global survey work.
- Turn `ROL 전역 전체 전수조사` into a deep integrity audit rather than a light repo inventory.
- Produce a single survey bundle that can support one SSOT roadmap and a defensible 95% confidence claim.

## 2. Trigger Conditions
Use this harness when one or more of the following are true:
- the order is `ROL 전역 전체 전수조사` or equivalent repo-wide wording
- the user explicitly asks for deep, high-rigor, exhaustive, integrity-focused, or endgame survey behavior
- the survey is intended to feed multiple execution SSOTs and one master roadmap
- the user wants time-expensive but higher-confidence documentation over speed

Compact or delta-only surveys do not need this harness unless the user elevates the rigor requirement.

## 3. Core Operating Rules
- Default global full survey mode is now deep integrity mode unless the user narrows scope or asks for a lighter pass.
- Use macro, micro, cross-cut, and operational views together; none are optional.
- Every action-bearing area may produce its own execution SSOT, but the bundle must converge into exactly one SSOT roadmap.
- Confidence claims must follow `docs/implementation/integrity-confidence-scoring-contract.md`.
- Critical claims should follow `docs/implementation/evidence-triangulation-contract.md`.
- Human-facing docs still require the 3-pass audit and 95% confidence gate before final save.

## 4. Required Output Bundle
Deep global survey output should normally include all of the following:
- one master survey doc in `docs/YYYY-MM-DD/`
- one evidence manifest
- one cross-cut integrity matrix section or companion doc
- one uncertainty and contradiction ledger section or companion doc
- one canonical execution SSOT per action-bearing area
- exactly one canonical master roadmap for the active bundle
- matching temp mirrors for execution SSOT docs and the single roadmap
- queue-state refresh if temp queue state is material to operators or tooling

## 5. Execution Shape

### Step A. Frame the Survey
- lock included and excluded scope
- record runtime/code-change locks
- read the latest canonical baseline only as needed
- choose the survey topic slug and dated output paths early

### Step B. Build Multi-Axis Evidence
- cover the required tranches from the global survey coverage contract
- collect macro topology, authority maps, and dependency seams
- collect micro hotspot and side-effect evidence
- collect cross-cut integrity views using the matrix template
- collect operational verification and regression surface notes
- when generated artifacts are part of the surveyed runtime, add an artifact-truth tranche that inspects actual blueprint/manuscript/episode files, not only surrounding telemetry
- artifact-heavy surveys should explicitly separate:
  - artifact truth
  - metadata truth
  - narrative truth

### Step C. Close Contradictions Before Synthesis
- apply the triangulation contract to critical claims
- record unresolved uncertainty explicitly instead of hiding it inside prose
- assign severity and blast-radius notes before drafting execution docs

### Step D. Synthesize Action Docs
- create or refresh area execution SSOTs for action-bearing areas
- mark `no-execution-doc-required` when justified
- create or refresh exactly one master roadmap for the active bundle
- do not split roadmap authority across multiple roadmap files

### Step E. Validate Confidence
- score the bundle with the integrity confidence contract
- if confidence remains below 95%, re-audit the weak sections and update the ledger
- run queue integrity validation and deep bundle validation before declaring the bundle complete

## 6. Single-Roadmap Rule
- The master roadmap is the only roadmap with SSOT authority for the bundle.
- Sub-lanes, themes, or thematic groupings may exist as sections inside the master roadmap.
- If extra planning slices are helpful, keep them as notes or subsections, not as parallel SSOT roadmaps.

## 7. Validation Hooks
After a deep survey bundle is materially updated:
- run `python scripts/ops_validator.py --strict` if temp execution mirrors or the temp roadmap changed
- run `python scripts/validate_deep_global_survey_bundle.py --survey-doc <canonical-master-survey-doc>` for structure and deep-bundle checks

## 8. Guardrails
- Do not downgrade to a quick inventory while still claiming deep survey coverage.
- Do not rely on one grep result for a critical architecture claim.
- Do not create more than one SSOT roadmap for the same active bundle.
- Do not claim 95% integrity confidence while unresolved contradictions still cap the score.
