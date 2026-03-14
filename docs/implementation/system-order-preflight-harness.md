# System Order Preflight Harness

Date: 2026-03-14
Status: active
Applies To: risky or substantial system-track work before survey, patch, or realization
Related Documents:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/process-health-scorecard-harness.md`

## 1. Purpose
- Add a deliberate preflight layer before substantial system-track work.
- Catch queue drift, governance conflicts, evidence gaps, and risky exception assumptions early.
- Standardize what "ready to start" means for non-trivial system work.
- Apply the same way whether the user says `Recursive Ops Loop`, `ROL`, or `rol`.

## 2. When To Use
Use this harness when one or more of the following is true:
- the order is broad, risky, or cross-cutting
- temp execution artifacts already exist
- multiple docs, surveys, or subsystems are involved
- the user asks for a high-rigor audit or implementation pass
- the work will likely create or consume execution SSOT documents

## 3. Preflight Checks

### Step 1. Governance Readiness
- Confirm the task is system-track.
- Confirm `AGENTS.md` is the SSOT for workspace operations.
- Load `docs/implementation/operations-governance-map.md` if there is any routing ambiguity.

### Step 2. Temp Queue Readiness
- Inspect `docs/temp/` for execution mirrors, roadmap, and queue-state files.
- If queue artifacts exist, run `python scripts/ops_validator.py`.
- If queue-state automation is desired, run `python scripts/sync_temp_queue_state.py`.

### Step 3. Evidence Readiness
- Determine whether baseline evidence already exists.
- If evidence exists but is stale, mark it as historical and plan refresh.
- If fresh evidence is required, decide whether an evidence manifest should be created.
- If the request is codebase-global, decide how the survey will be split by tranche before starting the sweep.

### Step 4. Exception Readiness
- Determine whether the work requires temporary allowlists, bootstrap exceptions, or non-standard handling.
- If yes, record them with `docs/implementation/exception-registry-harness.md`.

### Step 5. Closure Readiness
- Decide what would count as closure before starting.
- Identify whether a closure note, scorecard, or queue cleanup will be required.

## 4. Preflight Outputs
Possible outputs:
- none, if the task is straightforward and preflight simply confirms readiness
- refreshed `docs/temp/queue-state.json`
- evidence manifest
- exception registry entry
- process health scorecard

## 5. Guardrails
- Do not start broad realization work with a dirty or unvalidated temp queue.
- Do not assume old evidence is fresh without checking it.
- Do not let exceptions stay implicit.
- Do not let preflight force realization when the order is survey-only or document-only.
