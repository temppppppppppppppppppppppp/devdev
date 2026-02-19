# Codex Bug Bounty Sweep 10 + FP Recheck (No Code Changes)

- Date: 2026-02-18
- Scope: `modules/core/**`, `modules/domain/**`, `main_a.py`
- Method: 5 additional static rounds, contract tracing, FP re-triage
- Constraint: source code untouched (report-only)

## Round Coverage

1. Arc mapping and field-normalization contracts (`state_service`)
2. Stage4 PASS persistence atomicity and durability truthfulness
3. Anchor persistence contract (`save_anchor -> bool`) call-chain audit
4. Stage0 reverse-expander durability/return-value audit
5. Timeout and boundary candidates (FP/conditional recheck)

## Confirmed Findings

### N1) Arc mapping can miscompute `ep_end` when `ep_count` is missing
- Severity: HIGH
- Evidence:
  - `modules/core/services/state_service.py:69`
  - `modules/core/services/state_service.py:83`
- Why:
  - Fallback uses absolute `ep_end` as if it were `ep_count`, then recomputes `ep_end` as `expected_ep_start + ep_count - 1`.
  - If only `ep_end` is present, computed range can inflate and drift from intended arc boundaries.

### N2) `validate_arc_data_fields` can crash before repair loop on non-int `ep_count`
- Severity: HIGH
- Evidence:
  - `modules/core/services/state_service.py:242`
  - `modules/core/services/state_service.py:250`
  - Call path: `modules/core/stage3_orchestrator.py:284`
- Why:
  - `required_defaults` eagerly computes `ep_end` with arithmetic on `arc_data.get("ep_count", ...)`.
  - If `ep_count` is a string/non-int, a `TypeError` can occur before type repair logic executes.

### N3) Stage4 PASS DB write block is non-atomic despite DB-failure return
- Severity: CRITICAL
- Evidence:
  - `modules/core/stage4_post_processor.py:40`
  - `modules/core/stage4_post_processor.py:43`
  - `modules/core/stage4_post_processor.py:46`
  - Auto-commit behavior:
    - `modules/core/db_manager.py:401`
    - `modules/core/db_manager.py:405`
    - `modules/core/db_manager.py:427`
    - `modules/core/db_manager.py:441`
- Why:
  - Helper writes may commit independently when no transaction is open.
  - A later failure can return `False` while earlier writes are already durable (partial commit state).

### N4) Stage4 state-doc saves can silently fail while success logs continue
- Severity: HIGH
- Evidence:
  - `modules/core/stage4_post_processor.py:340`
  - `modules/core/stage4_post_processor.py:342`
  - `modules/core/world_state.py:67`
  - `modules/core/fact_ledger.py:65`
  - Bool contract source: `modules/core/db_manager.py:778`
- Why:
  - `save_anchor` returns `False` on failure (does not raise).
  - Callers rely on exceptions only and do not consume bool, so operators can get false-success signals.

### N5) Reverse expander reports success even if arc-anchor persistence fails
- Severity: HIGH
- Evidence:
  - `modules/core/stage0/reverse_expander.py:886`
  - `modules/core/stage0/reverse_expander.py:889`
  - `modules/core/stage0/reverse_expander.py:1029`
  - `modules/core/stage0/reverse_expander.py:1032`
  - Bool contract source: `modules/core/db_manager.py:778`
- Why:
  - `save_anchor` return value is ignored in both arc-stub save paths.
  - Functions return positive counts even when DB anchor save returns `False`.

### N6) ReferenceAnchor cache invalidation proceeds even when anchor save fails
- Severity: MEDIUM
- Evidence:
  - `modules/core/reference_anchor.py:280`
  - `modules/core/reference_anchor.py:282`
  - Bool contract source: `modules/core/db_manager.py:778`
- Why:
  - Save result is ignored; cache is invalidated regardless.
  - Can produce memory/DB mismatch under persistence failures.

## Conditional / Design-Risk (Not counted as confirmed defects)

### C1) ThreadPool timeouts are not hard wall-clock caps
- Verdict: Conditional risk
- Evidence:
  - `modules/core/stage2_preflight.py:100`
  - `modules/domain/agents/arc_ensemble.py:134`
  - `modules/domain/agents/chief_writer.py:244`
  - `modules/domain/agents/blueprint_ensemble.py:180`
  - `modules/domain/agents/consensus_validator.py:207`
  - `modules/domain/agents/base_agent.py:747`
- Note:
  - `future.result(timeout=...)` exists, but `with ThreadPoolExecutor(...)` shutdown wait semantics can still extend wall-clock. Risk depends on callable behavior.

## False-Positive Recheck

### FP1) `get_latest_episode_number` off-by-one suspicion
- Verdict: Likely false positive
- Evidence:
  - `modules/core/db_manager.py:1129`
  - `modules/core/project_manager.py:631`
  - `modules/core/information_diffusion.py:52`
- Reason:
  - Contract is intentionally "next episode number" in this codebase; several consumers already compensate with `-1` where needed.

### FP2) Stage4 `max_loops` formula looks odd (`+5`) but appears intentional safety margin
- Verdict: Likely false positive
- Evidence:
  - `modules/core/stage4_orchestrator.py:350`
  - `modules/core/stage4_orchestrator.py:351`
- Reason:
  - Guard is explicitly bounded by `max(1, min(..., 100))` and accompanied by safety comments.

## Priority Recommendation

1. P0: N3
2. P1: N1, N2, N4, N5
3. P2: N6
4. P2 (design-hardening): C1

## Notes

- No source code was modified in this sweep.
- This file is an addendum to prior bounty docs and focuses only on newly re-validated/extended items.
