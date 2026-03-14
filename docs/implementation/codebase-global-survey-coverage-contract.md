# Codebase Global Survey Coverage Contract

Date: 2026-03-14
Status: active
Applies To: system-track `global`, `repo-wide`, `전역 전체`, or codebase-wide full survey requests
Deep Survey Harness:
- `docs/implementation/deep-global-integrity-survey-harness.md`
Roadmap Contract:
- `docs/implementation/single-ssot-roadmap-contract.md`

## 1. Purpose
- Define what `global full survey` means in this workspace.
- Prevent `global` from becoming a vague "look around the repo" request.
- Break a codebase-wide survey into bounded coverage tranches so the work is heavy but still auditable.

## 2. Default Interpretation
If the user says one of the following without narrowing scope:
- `ROL 전역 전체 전수조사`
- `ROL 전역 전체 전수조사만`
- `global full survey`
- `repo-wide survey`
- `codebase-wide survey`

Default meaning:
- codebase-wide system-track survey
- macro + micro coverage
- cross-cut + operational coverage
- side-effects included by default
- bundled documentation outputs rather than implementation
- tranche or area survey coverage across the full codebase
- area execution SSOT docs for action-bearing areas
- exactly one SSOT roadmap when two or more area execution SSOT docs are produced
- no code patching or realization unless the user explicitly asks for implementation
- deep integrity mode by default unless the user explicitly narrows or asks for a lighter pass

## 3. Scope Definition

### 3.1 Included By Default
- `main_a.py`
- `modules/`
- `scripts/`
- `tests/` and smoke or canary harness entrypoints
- `UI/`
- `geuldobi-desktop/`
- root-level system scripts and operational code files
- live contracts/config/prompt maps that materially affect runtime behavior

### 3.2 Included As Reference, Not Primary Sweep Target
- `docs/YYYY-MM-DD/` historical survey or execution docs
- `docs/implementation/` harnesses and contracts
- `CLAUDE.md`
- `AGENTS.md`

These may be read for baseline, governance, or contradiction checks, but they do not replace live code inspection.

### 3.3 Excluded By Default
- `.git/`
- virtual environments such as `.venv/`
- `__pycache__/`
- build outputs, cache directories, temporary artifacts, and generated logs
- archival blobs not tied to the active codebase

If an excluded area becomes materially relevant, declare that explicitly in the survey.

## 4. What `Global` Means
`Global` means codebase-wide coverage across the active system, not merely runtime core.

Default global sweep surfaces:
1. repo topology and entrypoints
2. runtime orchestration and stage pipeline
3. domain logic and agent surfaces
4. persistence, logging, audit, and state
5. operator-visible surfaces, UI, and desktop linkage
6. tests, smoke, canary, and regression harnesses
7. scripts, utilities, migrations, and repair tooling
8. cross-cutting config, contracts, prompts, and bootstrap rules

## 5. What `Full` Means
`Full` means all of the following:
- macro architecture map
- micro hotspot inventory
- cross-cut integrity view
- operational and regression view
- side-effect sweep
- path-based coverage accounting
- subsystem dependency view
- risk and regression surface notes
- uncertainty or contradiction rollup
- confidence summary

`Full` does not mean:
- reading every historical document in `docs/` line by line
- patching code
- skipping execution planning for action-bearing areas

## 6. Required Coverage Tranches

### Tranche A. Macro Topology
Target:
- top-level layout
- entrypoints
- subsystem boundaries
- control-flow spine

Minimum outputs:
- repo topology summary
- entrypoint list
- active subsystem map

### Tranche B. Runtime Core
Target:
- `main_a.py`
- runtime orchestrators
- stage pipeline spine
- process runner and bootstrap path

Minimum outputs:
- runtime hotspot inventory
- bootstrap and fallback notes
- operator-visible runtime surfaces

### Tranche C. Domain and Agent Layer
Target:
- `modules/domain/`
- major agent ensembles
- validation, decision, and generation logic

Minimum outputs:
- agent/module hotspot table
- callback and dependency map
- major side-effect or retry surfaces

### Tranche D. Persistence and Observability
Target:
- DB manager
- session logger
- audit service
- logging setup
- JSONL and proof artifacts

Minimum outputs:
- persistence sink map
- logging/audit flow map
- transaction and write-surface notes

### Tranche E. Operator Surface and App Shell
Target:
- `UI/`
- `geuldobi-desktop/`
- UI services
- prompts, menus, desktop/app linkage

Minimum outputs:
- operator-visible surface inventory
- UI/Desktop integration notes
- prompt and output path notes

### Tranche F. Quality and Regression Surface
Target:
- `tests/`
- smoke runners
- canary helpers
- verification scripts

Minimum outputs:
- test harness map
- regression coverage notes
- read-only validation constraints if live canary work is in progress

### Tranche G. Scripts and Utility Surface
Target:
- `scripts/`
- root utilities such as repair or one-off operational helpers

Minimum outputs:
- script classification table
- runtime-affecting vs standalone split
- migration/repair risk notes

### Tranche H. Cross-Cutting Contracts and Config
Target:
- prompt maps
- API or IPC contracts
- config or bootstrap rules
- shared constants that materially affect runtime behavior

Minimum outputs:
- config/contract dependency notes
- bootstrap and environment assumptions
- contract drift risks

## 7. Required Output Bundle
A codebase-global full survey should normally produce a documentation bundle, not a single loose report.

Minimum bundled outputs:
- one master survey doc or equivalent tranche index in `docs/YYYY-MM-DD/`
- tranche or area survey coverage for all eight required tranches
- one canonical area execution SSOT for every action-bearing area, or an explicit `no-execution-doc-required` note
- matching `docs/temp/` mirror copies for execution SSOT docs after the document 3-pass audit
- exactly one canonical SSOT roadmap when two or more area execution SSOT docs are produced
- one confidence summary that can justify a 95% or higher score

The execution docs created here are planning artifacts. They do not authorize realization by themselves.

## 8. Required Cross-Cutting Views
A codebase-global full survey is not complete without these rollups:
- included vs excluded path list
- subsystem dependency map
- side-effect matrix
- cross-cut integrity matrix
- hotspot ranking
- risk register or regression caution list
- open questions or uncertainty list
- contradiction ledger or contradiction section
- action-bearing area list
- area-to-execution-ssot mapping
- survey-to-execution lineage notes
- confidence summary tied to the integrity confidence contract

## 9. Completion Rule
Do not call a global full survey complete unless:
- all eight coverage tranches were addressed
- any deferred tranche is explicitly marked deferred with reason
- included/excluded scope is written down
- side-effect coverage is addressed for the relevant surfaces
- macro and micro views both exist
- cross-cut and operational views both exist
- every action-bearing area is mapped to a canonical execution SSOT or marked `no-execution-doc-required`
- if two or more execution SSOT docs were produced, exactly one master roadmap exists
- confidence reaches at least 95 under `docs/implementation/integrity-confidence-scoring-contract.md`

## 10. Safe Use With Canary or Code-Change Lock
If canary or other live testing is in progress:
- keep the order in survey-only mode
- do not patch code
- do not mutate config, DB, or runtime process state
- prefer read-only evidence collection and document production
- canonical execution SSOT docs and aggregate roadmaps may still be produced because they are documentation outputs, not runtime changes

## 11. Shorthand
Recommended short forms:
- `ROL 전역 전체 전수조사만`
- `ROL 전역 전체 조사만`
- `ROL global full survey only`

In this workspace, those should default to this contract and its bundled documentation outputs unless the user narrows scope further.

Deep default:
- `ROL 전역 전체 전수조사` should be interpreted as a deep integrity survey unless the user explicitly asks for a lighter pass.
