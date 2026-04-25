# Stage4 HUD Snapshot Safe-Copy Residual Fix

Date: 2026-04-25
Status: final - residual bugfix PASS
Canonical Path: `docs/2026-04-25/stage4-hud-snapshot-safe-copy-residual-fix.md`
Related Resume Context: `docs/2026-04-25/stage234-session-memory-resume-context.md`
Related SSOT: `docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md`
Current Commit Before Patch: `7815c6a8ef6fa651640f77aaaa80b600b689b96d`
Current Dirty Summary: `clean branch feat/stage4-hud-snapshot-safe-copy opened from main after PR #25 merge`

## 1. Question

Can the known `TestCrossEpisodeRepetitionHook` failure be closed without changing Stage4 runtime authority or DB schema?

## 2. Verdict

Pass. The failure was caused by `Stage4PostProcessor._build_projected_hud_snapshot(...)` attempting to `copy.deepcopy(...)` a non-dict HUD snapshot returned by a broad test `MagicMock`. That object graph included a `sqlite3.Connection`, which cannot be pickled or deep-copied.

The safe fix is to treat HUD snapshots as persisted JSON payloads:

- accept dict snapshots only
- project only JSON-safe primitive/list/dict values
- ignore unsupported objects instead of deep-copying them
- keep approved HUD updates on the same JSON-safe path

## 3. Evidence

Reproduced before patch:

- `python -m pytest tests/test_stage4_orchestrator.py -k CrossEpisodeRepetitionHook -q`
- result: 2 failed, 1 passed
- failure root: `TypeError: cannot pickle 'sqlite3.Connection' object`
- failing call: `modules/core/stage4_post_processor.py` `_build_projected_hud_snapshot(...)`

Validated after patch:

- `python -m pytest tests/test_stage4_orchestrator.py -k CrossEpisodeRepetitionHook -q` -> 3 passed
- `python -m pytest tests/test_stage4_post_processor.py -k "hud_snapshot or primary_db" -q` -> 4 passed
- `python -m pytest tests/test_stage4_orchestrator.py -q` -> 164 passed
- `python scripts/check_utf8_hygiene.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py` -> passed
- `git diff --check` -> passed

## 4. Side-Effect Map

File writes / artifacts:

- no runtime artifact path changed
- this bugfix changes only Stage4 post-processor HUD snapshot projection and focused tests

DB / schema / transaction boundaries:

- no DB schema change
- `DBManager.save_manuscript(...)` already persists `hud_snapshot` only when it is a dict
- the patch narrows post-processor input to match that persistence contract

JSONL / log / audit sinks:

- no log or audit sink was added, removed, or renamed

Console / UI / operator output:

- no operator-facing output changed

Rollback / recovery / retry:

- rollback is a normal PR revert

Cache / global state:

- not applicable

Bootstrap fallback / config-env mutation:

- not applicable

## 5. Pass 1 - Scope

The patch is a direct focused system-track bugfix. It does not reopen the closed Stage234 session-memory lane and does not alter provider/session-memory authority.

Pass 1 result: pass.

## 6. Pass 2 - Evidence And Consistency

The fix matches the persistence contract: HUD snapshots are saved as JSON and therefore should not carry live Python objects such as sqlite connections, mocks, locks, or other process resources.

Pass 2 result: pass.

## 7. Pass 3 - Execution Shape

The implementation adds a small JSON-safe HUD projection helper, routes base snapshots and approved updates through it, and adds regression tests for non-dict snapshots plus unserializable dict values.

Pass 3 result: pass.

Confidence: 96/100
