# Execution Closure Harness

Date: 2026-03-14
Status: active
Applies To: system-track realization items that are ready to close
Related Documents:
- `docs/implementation/execution-closure-template.md`
- `docs/implementation/temp-execution-queue-roadmap-harness.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/process-health-scorecard-harness.md`
- `docs/implementation/exception-registry-harness.md`

## 1. Purpose
- Standardize how a realized execution SSOT is closed.
- Prevent temp queue residue from lingering after work is already implemented.
- Capture verification evidence, residual risks, and follow-up items before cleanup.

## 2. When To Use
Use this harness when one or more of the following is true:
- an execution SSOT has been implemented and the user is asking to finish or close it
- a roadmap item has moved from `in_progress` to `completed`
- `docs/temp/` cleanup is about to happen
- the user asks whether a realization item is truly done

## 3. Required Inputs
- canonical execution SSOT path
- temp execution SSOT mirror path, if one exists
- canonical roadmap path and temp roadmap mirror path, if a roadmap exists
- verification evidence or test notes
- residual risk and follow-up list

## 4. Closure Workflow

### Step 1. Confirm Realization State
- Check whether acceptance criteria are actually satisfied.
- If implementation is partial, do not mark the item closed.
- If testing could not be run, record that explicitly and keep the closure honest.

### Step 2. Capture Verification Evidence
- Record the tests, inspections, or runtime checks used to support closure.
- Link to canonical evidence artifacts when they exist.
- Distinguish verified behavior from inferred behavior.

### Step 3. Record Residual Risk
- List remaining risks, follow-up work, or deferred scope.
- If there are no residual risks, say so explicitly.
- If a later tranche is required, point to the next queue item or next survey.
- If a residual issue is intentionally tolerated, record it as an explicit exception.

### Step 4. Update Canonical Execution SSOT
- Change status to `closed`, `partially_realized`, or `blocked` as appropriate.
- Add a closure section or append a closure note using the closure template.
- Keep the canonical file authoritative.

### Step 5. Update Roadmap State
- If the item belongs to an aggregate roadmap, update the canonical roadmap first.
- Refresh the temp roadmap mirror only after the canonical roadmap is updated.
- Mark the item `completed` or `blocked` in the roadmap ledger.

### Step 6. Run Queue Validation
- Run `python scripts/ops_validator.py`.
- If queue-state tracking is enabled, run `python scripts/sync_temp_queue_state.py`.
- Resolve queue or mirror drift before deleting temp artifacts.

### Step 7. Clean Temp Queue
- Remove the execution SSOT mirror only after the canonical doc and roadmap are updated.
- If the queue is exhausted, remove `docs/temp/execution-roadmap.md`.
- If `docs/temp/queue-state.json` exists, refresh it or remove it when the queue becomes empty.
- Leave `docs/temp/README.md`.

## 5. Closure Outputs
- updated canonical execution SSOT
- updated canonical roadmap, if applicable
- refreshed temp roadmap mirror, if applicable
- optional closure note in `docs/YYYY-MM-DD/`
- optional process health scorecard
- cleaned temp mirror queue

## 6. Closure Decision Rules
- `closed`: acceptance criteria satisfied and no active temp work remains for this item
- `partially_realized`: some work landed, but the execution SSOT still governs follow-up work
- `blocked`: closure attempted, but a blocker or failed verification prevented clean completion

## 7. Guardrails
- Do not close an item only because code changed.
- Do not delete temp mirrors before updating canonical status.
- Do not claim closure without verification notes.
- Do not silently drop residual risks or follow-up obligations.
