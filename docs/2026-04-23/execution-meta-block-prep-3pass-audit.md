# Execution Meta Block Prep 3-Pass Audit

Date: 2026-04-23
Status: final
Scope: pre-implementation preparation for machine-readable execution metadata blocks in execution SSOT docs
Mode: survey-and-contract-prep only; no queue automation code mutation
Canonical Path: `docs/2026-04-23/execution-meta-block-prep-3pass-audit.md`
Commit State:
- Baseline Commit: `a0e728dc493af5b902fe1648432e6cd142542e7b`
- Baseline Dirty Summary: `dirty: unrelated projects/test_project/logs/episode_production.jsonl only`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `new prep branch only; no queue or production-code mutation in this turn`
Queue Note:
- this prep order does not create a new active queue item; it exists to make later queue automation safer and less prose-dependent
Confidence: `97%`

## 1. Intent

Prepare the next automation step before touching parser code:

- make execution SSOT metadata machine-readable
- stop relying on free-form prose for fields like `depends_on`
- define the minimum contract so future implementation can be narrow and testable

## 2. Current Gap

Current queue automation is honest but limited:

- `scripts/sync_temp_queue_state.py` can infer `roadmap_rank` and `queue_role` from roadmap prose
- it does **not** parse `depends_on`
- it hardcodes `depends_on: []` into every queue-state item
- `scripts/ops_validator.py` validates `depends_on` shape if present, but today it mostly checks an empty array

That means the current system is:

- good enough for visible ordering
- weak on dependency graph fidelity
- prone to prose drift if we try to parse more structure from natural language

## 3. Options Considered

### Option A. Parse more prose from existing sections

Pros:

- no visible doc format change

Cons:

- brittle
- easy to break when wording changes
- hard to validate confidently

Verdict:

- rejected as the default path

### Option B. Separate sidecar JSON files per execution doc

Pros:

- very machine-friendly

Cons:

- splits authority between prose doc and sidecar file
- easier for one to drift from the other
- adds more files to queue maintenance

Verdict:

- not preferred for this workspace

### Option C. Small machine-readable block embedded inside the execution SSOT

Pros:

- keeps human and machine surfaces in one canonical file
- avoids prose scraping for key queue fields
- easy to test
- still keeps the rest of the doc human-readable

Cons:

- requires one small format convention

Verdict:

- chosen

## 4. Format Choice

Chosen direction:

- one fenced `yaml` block under an explicit `## 0. Execution Metadata Block` heading
- parser reads only that section, not the whole document body

Why `yaml` is acceptable here:

- the workspace already imports `yaml` in multiple modules and tests
- no brand-new serialization style needs to be introduced
- it remains easier for humans to edit than raw JSON

Guardrail:

- keep the schema narrow so the parser does not become a general markdown interpreter

## 5. Minimal Contract

The block should carry only the fields that queue automation actually needs first.

Required:

- `schema_version`
- `topic`
- `status`
- `queue_role`
- `roadmap_rank`
- `depends_on`
- `tranches`

Recommended optional fields:

- `github_issue`
- `verification_commands`

The human prose sections remain authoritative for explanation, scope, and nuance.

The block exists only to carry stable machine-readable facts.

## 6. Tranche Shape

The parser target should not infer tranche meaning from markdown bullets.

Instead, the block should provide a small ordered list like:

- `id`
- `title`

That lets later tooling:

- render queue-aware tranche lists
- expose the next tranche cleanly
- keep tranche identity stable even if prose wording changes slightly

## 7. Recommended Rollout Order

1. add the contract document
2. add an optional example to the execution SSOT template
3. pilot the block in the three live parked items:
   - `authority-alignment-benchmark-operating-model-hardening`
   - `stage234-session-memory-max-utilization`
   - `stage0-bi-tr-production-harness-normalization-remediation`
4. only then update `sync_temp_queue_state.py`
5. then extend `ops_validator.py`
6. then add tests for block presence, bad schema, and dependency cycles or unknown topics

## 8. Ready-To-Implement Criteria

Implementation can begin safely once all of the following are true:

- the metadata block contract is saved canonically
- the template shows the exact placement and example shape
- rollout order is written down
- we explicitly choose that parser code reads the block only, not free-form prose

Those conditions are satisfied by the prep work in this branch.

## 9. Conclusion

The next step should **not** be a general-purpose markdown parser.

The implementation-ready path is:

- keep execution SSOT prose for humans
- add one small embedded metadata block for machines
- teach queue tooling to read that block and prefer it over prose inference for dependency and tranche structure
