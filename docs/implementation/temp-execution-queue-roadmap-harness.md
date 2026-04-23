# Temp Execution Queue and Roadmap Harness

Date: 2026-03-14
Status: active
Applies To: system-track execution SSOT realization work
Template: `docs/implementation/execution-roadmap-template.md`
Automation:
- `python scripts/build_execution_roadmap.py`
Related Documents:
- `docs/implementation/queue-priority-rubric.md`
- `docs/implementation/execution-closure-harness.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/process-health-scorecard-harness.md`
- `docs/implementation/execution-meta-block-contract.md`
- `docs/implementation/temp-queue-state-contract-v1.json`
- `docs/implementation/temp-queue-state-template.json`

## 1. Purpose
- Standardize how `docs/temp/` execution SSOT mirror copies are treated as an active execution queue.
- Define when an aggregate roadmap is required and how it controls realization order.
- Prevent ad hoc execution ordering and stale temp residue.

## 2. When To Use
Use this harness when one or more of the following is true:
- `docs/temp/` contains `*-execution-ssot.md`
- `docs/temp/execution-roadmap.md` exists
- the user asks to continue or realize queued execution work
- multiple execution SSOT mirror copies exist at the same time

## 3. Queue Inventory

### Step 1. Enumerate Queue Artifacts
Inspect `docs/temp/` and classify:
- `*-execution-ssot.md`: execution queue items
- `execution-roadmap.md`: queue controller
- `queue-state.json`: optional machine-readable queue snapshot
- `README.md`: static operator note, not a queue item

### Step 2. Map Each Queue Item
For each execution SSOT mirror, capture:
- temp path
- canonical dated path
- title or topic slug
- source survey docs
- current status
- obvious dependencies or overlap with other queue items

### Step 3. Detect Queue Mode
- `0` execution docs: no active queue
- `1` execution doc: single-item queue
- `2+` execution docs: aggregate roadmap required

## 4. Aggregate Roadmap Rule

### When Required
Create or refresh an aggregate roadmap when:
- two or more execution SSOT mirrors exist in `docs/temp/`
- a new execution SSOT enters the queue while another is still pending
- dependency or substrate assumptions change enough to reorder work

### Canonical and Mirror Paths
- canonical roadmap: `docs/YYYY-MM-DD/*-execution-roadmap.md`
- temp roadmap mirror: `docs/temp/execution-roadmap.md`
- use `docs/implementation/execution-roadmap-template.md` as the default starting shape

### Minimum Roadmap Contents
- queue inventory
- canonical and temp paths for every queued execution SSOT
- execution order
- dependency notes
- shared substrate opportunities
- status ledger:
  - pending
  - in_progress
  - completed
  - blocked
- cleanup rule for each item
- priority basis or dependency rationale

### Polaris Alignment Rule
- If a canonical dated `Polaris` note exists for the same subsystem or for the cross-stage spine, use it as a future-state alignment aid when refreshing roadmap language.
- `Polaris` alignment may justify:
  - reducing overloaded `partially_realized` wording
  - separating active-realization language from proof-pending language
  - separating historical backing from active queue semantics
- `Polaris` alignment does not by itself authorize:
  - deleting temp mirrors mid-run
  - changing queue state before canonical docs and queue-state are aligned
  - rewriting roadmap order without evidence or dependency rationale

## 5. Realization Rules
- If a roadmap exists, realization follows roadmap order.
- Do not bypass the roadmap because a later item looks easier.
- If work reveals a stronger dependency ordering, update the roadmap first.
- If a new execution SSOT is created during ongoing realization, refresh the roadmap before continuing.
- A single-item queue may proceed without an aggregate roadmap, but it still remains a queue item until realized and cleaned up.
- Use `docs/implementation/queue-priority-rubric.md` when the ordering is not trivially obvious.
- During migration, if a canonical execution SSOT contains an `Execution Metadata Block`, future queue tooling should prefer that block over prose inference for `depends_on`, tranche identity, and queue metadata that the block explicitly carries.
- Before any code modification starts, re-audit the governing canonical execution SSOT or canonical roadmap with the document 3-pass harness and confirm at least 95% confidence against the current workspace state.

## 5A. Optional Queue State File
- `docs/temp/queue-state.json` may be used as a machine-readable queue snapshot.
- If present, it should follow `docs/implementation/temp-queue-state-contract-v1.json`.
- Refresh it whenever queue membership or status changes.
- Preferred command: `python scripts/sync_temp_queue_state.py`
- Remove it when the queue becomes empty.

## 5B. ClickUp Reflection Rule
- If the workspace is using the ClickUp mirror, treat ClickUp as an external visibility surface only.
- Repo authority order remains:
  - canonical execution docs in `docs/YYYY-MM-DD/`
  - temp mirrors in `docs/temp/`
  - `docs/temp/queue-state.json`
  - ClickUp mirror
- Default rule:
  - do not sync ClickUp during routine queue maintenance
  - sync ClickUp only when the user explicitly asks for a human-facing mirror refresh
  - the rationale is operational latency: ClickUp is slower than repo-side queue updates and should not tax normal execution flow
- When the user explicitly asks for ClickUp reflection after one of the following materially changes, refresh ClickUp only after the repo-side queue artifacts are aligned:
  - execution SSOT status
  - roadmap ordering or roadmap rank
  - queue membership
  - blocked / parked / completed state
- Preferred order:
  1. update canonical execution docs or canonical roadmap
  2. refresh the matching `docs/temp/` mirror
  3. refresh `docs/temp/queue-state.json`
  4. run `python scripts/ops_validator.py --strict`
  5. if the user explicitly asked for ClickUp sync and validation passes, run `python -X utf8 scripts/sync_clickup_queue.py`
- Do not update ClickUp from stale roadmap text, a stale temp mirror, or mid-edit queue assumptions.

## 6. Cleanup Rules

### Per-Item Cleanup
When one execution SSOT is realized and closed:
- keep the canonical execution SSOT in `docs/YYYY-MM-DD/`
- remove only that mirror copy from `docs/temp/`
- update the roadmap status to `completed`
- use `docs/implementation/execution-closure-harness.md` before deletion
- run `python scripts/ops_validator.py` before and after cleanup when practical

### Queue Exhaustion Cleanup
When all queued items are complete:
- remove remaining execution SSOT mirrors from `docs/temp/`
- remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if it exists
- leave `docs/temp/README.md`

### Queue Compaction Rule
- If the roadmap or queue-state already classifies an item as `historical_backing`, treat it as a compaction candidate rather than as normal active workload.
- If a canonical execution doc says the remaining work is only fresh proof, verifier follow-up, or deferred debt, prefer making that posture explicit instead of leaving the item to read like open realization work.
- Compaction should preserve canonical evidence while reducing active temp noise.
- During active live-run-merge mode, queue compaction decisions must still wait until the post-run merged audit passes the save gate.

### Optional Queue Health Reporting
- For operator-facing governance checks, create a scorecard with `docs/implementation/process-health-scorecard-harness.md`.

## 7. Guardrails
- Do not treat `docs/temp/` as archival storage.
- Do not keep realized items in the temp queue.
- Do not execute multiple items without a roadmap once the queue has more than one item.
- Do not let the temp roadmap become newer in meaning than the canonical roadmap.
- Do not edit only the temp roadmap mirror without syncing the canonical roadmap in the same turn.
- Do not start realization from a stale execution SSOT or roadmap that has not been re-audited at execution start.
