# System Full Survey -> Execution SSOT Harness

Date: 2026-03-14
Status: active
Applies To: system-track orders only
Companion First-Read: `docs/implementation/system-order-init-harness.md`
Related Companions:
- `docs/implementation/system-order-preflight-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/temp-execution-queue-roadmap-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-manifest-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/execution-closure-harness.md`
- `docs/implementation/exception-registry-harness.md`
Templates:
- `docs/implementation/execution-ssot-template.md`
- `docs/implementation/execution-roadmap-template.md`
Reference Aids:
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/canonical-naming-contract.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/implementation/side-effect-survey-checklist.md`
- `docs/implementation/queue-priority-rubric.md`
- `docs/implementation/temp-queue-state-contract-v1.json`
- `docs/implementation/single-ssot-roadmap-contract.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`

## 1. Purpose
- Standardize how system-track full surveys, 3-pass audits, and execution SSOT documents are produced.
- Keep survey, audit, evidence, and canonical execution outputs in dated `docs/` locations, while also mirroring execution SSOT documents into `docs/temp/` for downstream collation.
- Separate stable process instructions from temporary investigation outputs.
- Treat side-effects as default survey scope, not an optional appendix.
- Require a 3-pass document audit before human-facing documents are finalized or mirrored.
- Require estimated confidence of at least 95% before final save or mirror refresh.
- Leave queue orchestration and detailed document-audit mechanics to their dedicated companion harnesses.

## 2. Trigger Conditions
Use this harness when the request is a system-track order and includes one or more of the following intents:
- full survey
- master audit
- audit order
- 3-pass audit
- execution SSOT
- remediation execution plan
- global or subsystem-wide codebase inspection
- residual inventory before patching
- fresh live run paired with survey or audit

Do not use this harness for narrative pipeline work. Narrative pipeline continues to use the blockguide harness set.

## 3. Path Policy

### 3.1 Stable Harness Path
- Process document: `docs/implementation/system-full-survey-execution-harness.md`

### 3.2 Default Working Output Path
- Survey docs: `docs/YYYY-MM-DD/`
- Audit docs: `docs/YYYY-MM-DD/`
- Evidence inventories: `docs/YYYY-MM-DD/`
- Canonical execution SSOT docs: `docs/YYYY-MM-DD/`
- Execution SSOT mirror copies: `docs/temp/`

### 3.3 Promotion Path
Execution SSOT handling rule:
- write the canonical execution SSOT to `docs/YYYY-MM-DD/`
- copy the same file to `docs/temp/`
- never use `docs/temp/` as the only copy

`docs/temp/` may be cleared after downstream collation or post-processing because the canonical copy already lives in `docs/YYYY-MM-DD/`.

### 3.4 Mirror Integrity Rule
- Edit the canonical `docs/YYYY-MM-DD/` execution SSOT first.
- After each material edit, overwrite the `docs/temp/` mirror copy from the canonical file.
- Do not manually hotfix the `docs/temp/` copy without syncing the canonical file in the same turn.
- Treat the `docs/temp/` copy as a disposable working mirror, not as an authority.

### 3.5 Execution SSOT Metadata Contract
Each execution SSOT should carry enough metadata to reconstruct lineage.

Default template:
- `docs/implementation/execution-ssot-template.md`

Recommended header fields:
- `Date`
- `Status`
- `Canonical Path`
- `Temp Mirror Path`
- `Baseline Commit`
- `Baseline Dirty Summary`
- `Resume Commit`
- `Resume Drift Summary`
- `Source Survey Docs`
- `Evidence Artifacts`
- `Side-Effect Coverage`

If a short format is used, at minimum include:
- canonical path
- temp mirror path
- source survey docs
- baseline commit
- baseline dirty summary

### 3.6 Temp Execution Queue Rule
`docs/temp/` is the active execution queue for execution SSOT mirror copies.

Queue semantics:
- an execution SSOT mirror in `docs/temp/` means the item is pending or active for realization
- once the execution SSOT is realized and closed, remove its mirror copy from `docs/temp/`
- the dated canonical execution SSOT remains in `docs/YYYY-MM-DD/`
- `docs/temp/` is for execution handling, not long-term storage

Operationally, "empty temp" means clearing active execution artifacts from `docs/temp/`.
Static operator notes such as `docs/temp/README.md` may remain.

### 3.7 Multi-Document Roadmap Rule
If `docs/temp/` contains two or more execution SSOT mirror copies, do not execute them independently in arbitrary order.

Detailed queue mechanics live in `docs/implementation/temp-execution-queue-roadmap-harness.md`.
Default roadmap template:
- `docs/implementation/execution-roadmap-template.md`

Required action:
- first create an aggregate roadmap covering all execution SSOTs currently in `docs/temp/`
- then execute according to that roadmap
- update roadmap status as items are completed

Recommended roadmap paths:
- canonical: `docs/YYYY-MM-DD/*-execution-roadmap.md`
- temp mirror: `docs/temp/execution-roadmap.md`

Minimum roadmap contents:
- inventory of all execution SSOT mirrors currently in `docs/temp/`
- canonical path and temp path for each item
- dependency graph or execution order
- shared substrate or merge opportunities
- per-item status: pending / in_progress / completed / blocked
- temp cleanup condition

When the roadmap is exhausted:
- remove completed execution SSOT mirrors from `docs/temp/`
- remove the temp roadmap mirror
- leave `docs/temp/` clear of active execution artifacts

### 3.8 Document Save Gate
Human-facing documents produced under this harness must follow:

1. draft
2. pass 1 audit
3. pass 2 audit
4. pass 3 audit
5. targeted re-audit until estimated confidence is at least 95%
6. final save

This applies to:
- survey docs
- audit docs
- execution SSOT docs
- execution roadmap docs
- readme or operating-note docs created for the process

Mirror rule:
- create or refresh the `docs/temp/` execution SSOT mirror only after the 3-pass document audit is complete and the confidence gate is met
- if the canonical execution SSOT changes later, re-run the 3-pass document audit and confidence gate before refreshing the mirror

Raw evidence artifacts may be generated during investigation, but any human-facing document that interprets them must pass the 3-pass save gate and confidence threshold.

Detailed document audit mechanics live in `docs/implementation/document-3pass-audit-harness.md`.

## 4. Standard Workflow

### Step 0. Order Classification
- Confirm the order is system-track.
- Confirm whether the user wants survey only, survey plus execution doc, or immediate implementation.
- If the user says not to patch yet, do not patch code. Produce survey and execution docs only.
- Inspect `docs/temp/` execution mirrors before starting implementation work.
- If multiple execution SSOT mirrors are already queued, create or refresh the aggregate roadmap first.
- If the user asks for `global`, `repo-wide`, or `전역 전체` survey coverage, use `docs/implementation/codebase-global-survey-coverage-contract.md`.
- For codebase-global survey requests, treat the default deliverable as a bundled documentation set: tranche survey coverage, area execution SSOT docs for action-bearing areas, and one SSOT roadmap if two or more execution docs are produced.
- For deep codebase-global survey requests, also use `docs/implementation/deep-global-integrity-survey-harness.md`.
- If the user explicitly pairs the survey with a fresh live run, also load `docs/implementation/live-run-merge-survey-harness.md` and keep outputs provisional until post-run merge.
- If implementation is about to begin from an execution SSOT or roadmap, re-run the document 3-pass audit and confidence gate on the governing canonical doc against the live workspace before patching code.
- During that revalidation, refresh `Resume Commit` and `Resume Drift Summary` instead of relying only on generic `current workspace state` wording.

### Step 1. Baseline Harvest
- Read only the minimum prior docs needed to avoid duplicate work.
- Prefer the most recent final audit or execution SSOT for the same topic.
- Capture the minimal commit-state baseline using `docs/implementation/commit-state-minimal-contract.md`.
- Record why the baseline may no longer be sufficient:
  - live-code-changed
  - artifact-contradiction
  - new-scope
  - operator-surface-mismatch

### Step 2. Evidence Inventory
- Build direct evidence from the live workspace first.
- Prefer AST or structured inventory over naive grep when precision matters.
- Save reusable survey artifacts in `docs/YYYY-MM-DD/` unless the user explicitly wants another path.
- If evidence volume is large or likely to be reused, create an evidence manifest.
- If the survey is deep or global, use the triangulation contract for claims that drive severity or execution planning.
- If generated runtime artifacts are in scope, inspect the actual artifact files directly rather than relying only on logs, DB rows, hashes, or summaries.
- For blueprint/manuscript/episode-style artifacts, build evidence across three layers:
  - artifact truth: file existence, byte stability, decode/parse integrity, and on-disk hash truth
  - metadata truth: DB/JSONL/summary/rationale linkage to those files
  - narrative truth: content-level contradictions, and mismatches against blueprint/selection/verdict claims

### Step 2A. Side-Effect Sweep
Before closing the inventory, explicitly inspect side-effects tied to the target surface.

Default checklist:
- use `docs/implementation/side-effect-survey-checklist.md`

Minimum side-effect categories:
- file writes and artifact generation
- actual artifact content integrity and content-level truth when runtime-generated artifacts are part of scope
- DB writes, schema touchpoints, and transaction boundaries
- JSONL/log/audit sink writes
- console, UI, and operator-visible output surfaces
- rollback, recovery, retry, and compensation paths
- cache, singleton, global-state, and in-memory mutation paths
- config mutation, env loading, and bootstrap fallback behavior

If a category is truly not applicable, state that explicitly in the survey instead of skipping it silently.

### Step 3. Pass 1 - Full Inventory
- Establish the baseline counts, paths, and hotspots.
- Separate runtime scope from scripts, tests, demos, or archived surfaces.
- Produce a concrete inventory table, not a general statement.
- Produce a side-effect map for the target runtime surface.
- For codebase-global survey requests, cover the required tranches from the global survey coverage contract rather than improvising scope.

### Step 4. Pass 2 - Semantic Classification
- Group findings by runtime meaning, not only by file count.
- Distinguish:
  - direct conversion targets
  - callback injection targets
  - bootstrap exceptions
  - interactive surfaces
  - standalone utilities
  - side-effect-bearing paths that require extra regression caution

### Step 5. Pass 3 - Execution Shape
- Turn the survey into an execution-ready document.
- Define the substrate first if the migration needs new persistence, schema, or bridge layers.
- Split execution into tranches so later code changes can follow the document without re-surveying the whole topic.
- Call out side-effect containment, rollback expectations, and post-change verification paths.
- When the execution SSOT passes the document 3-pass audit, create a mirror copy in `docs/temp/` in the same turn.
- Record which survey, audit, and evidence documents the execution SSOT was derived from.
- If multiple execution SSOT mirrors are active, order them with the roadmap plus `docs/implementation/queue-priority-rubric.md`.
- If there are multiple source docs, use `docs/implementation/execution-synthesis-harness.md`.
- If temporary exceptions remain, record them with `docs/implementation/exception-registry-harness.md`.

### Step 5A. Codebase-Global Bundle Rule
When the order is using the codebase-global survey coverage contract:
- produce tranche-level survey coverage for every required area, either as dedicated survey docs or as clearly separated sections in a master survey
- produce macro, micro, cross-cut, and operational views explicitly
- synthesize an area execution SSOT for each action-bearing tranche or area after the survey passes the document audit
- explicitly mark `no-execution-doc-required` for areas that do not need follow-on realization
- if two or more area execution SSOTs are produced, create or refresh exactly one master roadmap in the same documentation cycle
- apply the single SSOT roadmap contract rather than creating parallel roadmap authorities
- score the bundle with the integrity confidence contract before final save
- treat this bundle as documentation output only; do not begin realization unless the user explicitly asks for implementation

### Step 6. Output Set
Create one or more of the following, depending on scope:
- `docs/YYYY-MM-DD/*-audit-order.md`
- `docs/YYYY-MM-DD/*-3pass-audit.md`
- `docs/YYYY-MM-DD/*-execution-ssot.md`
- `docs/temp/*-execution-ssot.md` mirror copy
- `docs/YYYY-MM-DD/*-execution-roadmap.md`
- `docs/temp/execution-roadmap.md` mirror copy
- `docs/YYYY-MM-DD/*-evidence.txt`
- `docs/YYYY-MM-DD/*-evidence-manifest.md`
- `docs/YYYY-MM-DD/*-evidence.json`
- `docs/YYYY-MM-DD/*-preflight-watchlist.md`
- `docs/YYYY-MM-DD/*-live-run-evidence-manifest.md`
- `docs/YYYY-MM-DD/*-post-run-merge-audit.md`
- `docs/YYYY-MM-DD/*-side-effects.txt`
- `docs/YYYY-MM-DD/*-side-effects.json`
- `docs/YYYY-MM-DD/*-cross-cut-integrity-matrix.md`
- `docs/YYYY-MM-DD/*-uncertainty-ledger.md`
- `docs/temp/README.md`
- optional `docs/temp/queue-state.json`

Single-document mode is acceptable when one document can carry:
- baseline facts
- 3-pass classification
- side-effect map
- execution design
- acceptance criteria

Codebase-global bundle mode will usually require multiple docs rather than a single-document output.

### Step 7. Validation and Closure Hooks
- After creating or refreshing execution SSOT or roadmap mirrors, run `python scripts/ops_validator.py`.
- After creating or refreshing a deep global survey bundle, run `python scripts/validate_deep_global_survey_bundle.py --survey-doc <canonical-master-survey-doc>`.
- If queue-state tracking is desired, run `python scripts/sync_temp_queue_state.py`.
- Before realization starts from an execution SSOT or roadmap, complete a current-state re-audit of that governing doc.
- When realization later finishes, close the queue item with `docs/implementation/execution-closure-harness.md`.

## 5. Naming Convention
- Use lowercase kebab-case.
- Keep the topic slug stable across related outputs.
- Recommended pattern:
  - `<topic>-full-survey-audit-order.md`
  - `<topic>-3pass-audit.md`
  - `<topic>-execution-ssot.md`
  - `<topic>-evidence.txt`

If the document is a survey, audit, evidence, or side-effect artifact, prefer `docs/YYYY-MM-DD/` first.
For execution SSOT documents, write the dated `docs/` file first as canonical and then create the `docs/temp/` mirror copy.

## 6. Required Sections For Execution SSOT
An execution SSOT produced by this harness should usually contain:
- intent
- baseline facts
- pass 1 inventory
- pass 2 semantic classification
- side-effect map or side-effect section
- pass 3 realization architecture or execution shape
- execution tranches
- acceptance criteria
- verification plan
- non-goals or guardrails

## 7. Guardrails
- Do not start with blind search-and-replace.
- Do not treat old docs as truth if live code contradicts them.
- Do not mix narrative-pipeline harness rules into system-track orders.
- Do not put survey or audit artifacts in `docs/temp/` by default.
- Do not leave an execution SSOT only in `docs/temp/`.
- Do not treat the `docs/temp/` copy as canonical.
- Do not edit only the `docs/temp/` mirror.
- Do not finalize or mirror a human-facing document before the document 3-pass audit is complete.
- Do not finalize or mirror a human-facing document while estimated confidence remains below 95%.
- Do not begin code modification from an execution SSOT or roadmap without a fresh current-state re-audit.
- Do not start realizing multiple temp execution SSOTs without an aggregate roadmap.
- Do not keep realized execution SSOT mirrors in `docs/temp/`.
- Do not clear `docs/temp/` until the canonical file exists and the mirror has been refreshed from it.
- Do not let scripts or archived surfaces distort runtime priorities.
- Do not declare a full survey complete without checking applicable side-effect categories.
- Do not claim completion until the execution document has explicit acceptance criteria.

## 8. Recommended Promotion Rule
Default behavior:
- survey and audit outputs go straight to `docs/YYYY-MM-DD/`
- all human-facing docs are saved after document 3-pass audit and confidence gate
- execution SSOT is saved to `docs/YYYY-MM-DD/` after document 3-pass audit and confidence gate
- the same execution SSOT is copied to `docs/temp/` after document 3-pass audit and confidence gate
- if multiple execution SSOT mirrors exist in `docs/temp/`, create an aggregate execution roadmap before realization
- realize items according to the roadmap
- remove each temp execution mirror after its realization is closed
- review, collate, or post-process from `docs/temp/`
- once the roadmap is exhausted, clear remaining temp execution artifacts while keeping canonical docs intact

This keeps canonical history in dated archives while letting `docs/temp/` act as a disposable execution inbox.
