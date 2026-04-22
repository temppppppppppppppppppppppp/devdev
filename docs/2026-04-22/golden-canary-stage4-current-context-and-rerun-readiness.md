# Golden Canary Stage4 Current Context and Rerun Readiness

Date: 2026-04-22
Scope: current workspace state before commit/push
Project: `projects/골든 카나리아`
Lane: `Stage4 direct supervised guarded run`

## 1. Current Frontier

- authoritative manuscript frontier is `ep10`
- `ep11` did **not** persist a final manuscript
- latest guarded run targeted `ep15`, but stopped on monitor policy before `ep11` cleared

Authoritative evidence:

- DB: `projects/골든 카나리아/project_data.db`
- guarded result: `projects/골든 카나리아/logs/stage4_direct_supervised_guarded_result.json`
- run log: `projects/골든 카나리아/logs/session_20260422_145530.log`

DB readback at documentation time:

- manuscripts: `max_ep=10`, `count=10`
- latest Stage4 attempts:
  - `ep11 attempt 5 -> REJECT score 97 primary_failure_layer=downstream_gate`
  - `ep11 attempt 4 -> REJECT score 98 primary_failure_layer=downstream_gate`
  - `ep11 attempt 3 -> REJECT score 100 primary_failure_layer=downstream_gate`
  - `ep11 attempt 2 -> REJECT score 100 primary_failure_layer=downstream_gate`
  - `ep11 attempt 1 -> REJECT score 100 primary_failure_layer=downstream_gate`
  - `ep10 attempt 4 -> PASS score 98 primary_failure_layer=none`

Guarded result summary:

- `success=false`
- `terminated_by_monitor=true`
- `termination_reason=stage4_round_limit_exceeded`
- `terminated_attempt_num=6`
- `latest_round_seen=6`
- `target_ep=15`

Note:

- `stage4_direct_supervised_guarded_result.json` reports `latest_written_ep_after=11`, but DB manuscripts remain `max_ep=10`
- manuscript SSOT remains the DB, so `ep11` is still unresolved

## 2. What Actually Broke

### 2.1 Earliest stable defect owner

The earliest stable owner was `Stage3 ep11 blueprint acceptance`, not Stage4 manuscript generation.

Canonical continuity chain:

- `ep9` already issues the gold-report order
  - see `projects/골든 카나리아/drafts/ep_0009.txt`
- `ep10` explicitly preserves that as already-issued carryover
  - see `projects/골든 카나리아/drafts/ep_0010.txt`
- accepted `ep11` blueprint re-framed the same order as if it were new work
  - see `projects/골든 카나리아/logs/artifacts/stage3/ep_0011/attempt_01/final_blueprint__emotion_focused.json`

In short:

- prior truth: `gold report already ordered`
- accepted ep11 blueprint: `gold report ordered again as fresh command`
- Stage4 then mostly realized that defective blueprint
- Stage4 post-select history gate was catching a real pre-existing contradiction

### 2.2 Stage4-side gap

There was also a Stage4 contract synthesis gap.

Observed path:

- raw Director result did not provide a ready local `fix_pack`
- contradiction firewall upgraded the outcome to `PASS_WITH_FIX`
- downstream contract enforcement then fail-closed on `missing_fix_pack`

This means the final REJECT was not random. It was a valid fail-close, but the `PASS_WITH_FIX` path had a synthesis gap that made recovery worse than it needed to be.

## 3. Patches Added in This Batch

### 3.1 Stage3 prompt carryover reinforcement

Added a compact carryover-order digest so the blueprint lane sees recent unresolved/pending orders earlier and more explicitly.

Files:

- `modules/domain/agents/stage3_prompt_envelope.py`
- `modules/domain/agents/blueprint_ensemble.py`

Behavior:

- scans recent prior manuscripts for order/pending-action style carryover
- promotes those rows into Stage3 prompt context as a dedicated high-visibility tier
- this is a retrieval/attention aid, not a Python-side verdict or fact rewrite

Intent:

- reduce `already-issued order gets restated as fresh order` failures in Stage3
- especially for direct-continuation / same-night lanes like the `ep9 -> ep10 -> ep11` chain

### 3.2 Stage4 firewall fix-pack backfill

Added a synthesized local fix-pack fallback when Stage4 contradiction firewall promotes a decision to `PASS_WITH_FIX` but the Director result leaves `fix_pack` blank.

File:

- `modules/domain/agents/director_ensemble.py`

Behavior:

- if firewall marks the contradiction as locally fixable and the final verdict is `PASS_WITH_FIX`
- and no usable `fix_pack` exists
- synthesize a minimal local sentence-level fix contract from contradiction details and feedback action items

Intent:

- prevent `PASS_WITH_FIX -> missing_fix_pack -> REJECT` collapse in obviously local contradiction cases

## 4. Validation Performed

Targeted regression/verification:

- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py tests/test_fix_scope_contract.py tests/test_director_modules.py tests/test_v75c_contradiction_firewall.py::test_fixable_firewall_promotes_local_name_drift_to_pass_with_fix -q`
- result: `199 passed`

UTF-8 hygiene:

- `python scripts/check_utf8_hygiene.py modules/domain/agents/stage3_prompt_envelope.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/director_ensemble.py tests/test_blueprint_ensemble_generate_ensemble.py tests/test_fix_scope_contract.py tests/test_v75c_contradiction_firewall.py`
- result: pass

Additional sanity check:

- `build_stage3_recent_carryover_digest(...)` was manually exercised against `ep9 + ep10` manuscripts to confirm that gold carryover is surfaced in the prompt lane

## 5. Rerun Readiness

Current call:

- `main geometry hole from ep10 is patched`
- `ep11 carryover-order visibility is reinforced`
- `Stage4 firewall fix-pack synthesis gap is patched`
- status is `rerun-ready`, but not yet re-run after these latest patches

Recommended next run:

- guarded rerun from current frontier
- project: `골든 카나리아`
- expected resume target: resolve `ep11`, then continue forward under the existing retry cap policy

## 6. Broader Batch Context in This Worktree

This commit batch is broader than the final `ep11` fix alone. The current worktree also contains:

- benchmark archive infrastructure
- direct supervised archive hooks
- canary archive hooks
- guarded Stage4 supervised runner
- Golden Canary static survey / merge-audit docs
- generated project artifacts and logs from the supervised runs

This document exists to preserve the latest `Golden Canary Stage4` runtime context before committing and pushing the full batch.
