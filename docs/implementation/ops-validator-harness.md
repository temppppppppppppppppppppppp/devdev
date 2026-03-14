# Ops Validator Harness

Date: 2026-03-14
Status: active
Applies To: system-track document and temp-queue integrity checks
Script: `scripts/ops_validator.py`

## 1. Purpose
- Provide a repeatable validation step for canonical/mirror execution documents.
- Detect temp-queue drift before cleanup or further realization.
- Keep process failures observable without manual spot checks only.

## 2. When To Use
Run the validator when one or more of the following is true:
- a new execution SSOT mirror was added to `docs/temp/`
- a canonical execution SSOT was edited and its mirror was refreshed
- an aggregate roadmap was created or updated
- temp cleanup is about to happen
- the user asks whether the execution queue is in a valid state

## 3. What It Checks
- every `docs/temp/*-execution-ssot.md` has a canonical dated counterpart
- temp mirror content matches the canonical source when a counterpart is resolved
- `Canonical Path` and `Temp Mirror Path` metadata are consistent when present
- multiple temp execution SSOT mirrors require `docs/temp/execution-roadmap.md`
- temp roadmap mirrors resolve to canonical roadmap documents
- optional `docs/temp/queue-state.json` matches the active temp queue when present

## 4. Command
Default run:

```powershell
python scripts/ops_validator.py
```

Strict run:

```powershell
python scripts/ops_validator.py --strict
```

## 5. Output Semantics
- `PASS`: validation rule satisfied
- `WARN`: recoverable drift or missing metadata; fix when practical
- `FAIL`: canonical or queue integrity problem; do not close the queue yet

Default exit codes:
- `0`: no failures
- `1`: one or more failures

Strict mode:
- warnings are treated as failures

## 6. Recommended Workflow
1. update canonical docs
2. refresh temp mirrors
3. optionally refresh `docs/temp/queue-state.json` with `python scripts/sync_temp_queue_state.py`
4. run the validator
5. if validation passes, continue realization or closure
6. if validation fails, repair the doc or queue state first

## 7. Guardrails
- Do not treat the validator as a substitute for the document 3-pass audit.
- Do not clear temp artifacts after a failing validation run.
- Do not ignore repeated warnings; they signal drift that will become failure later.
