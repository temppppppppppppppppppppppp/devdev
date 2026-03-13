# S3D-T1: Stage 3 Orchestration DI Wiring Audit (1-Pass)

**Date**: 2026-03-13
**Scope**: `modules/core/stage3_orchestrator.py`, `modules/core/stage3_context.py`, `main_a.py` (Stage 3 sections)
**Auditor**: Claude Opus 4.6 (read-only)

---

## Checklist Results

### 1. Stage3Context `__slots__` vs `from_app()` mapping — 1:1 correspondence check

**Status**: OK

`__slots__` declares 23 slots (2 required + 10 attributes + 10 callbacks + 1 session_logger).
`from_app()` (L101-128) maps exactly 23 keyword arguments, one per slot. `__init__` (L47-98) assigns all 23. No orphan slots, no unmapped arguments.

**Evidence**: `stage3_context.py` L16-45 (`__slots__`), L100-128 (`from_app`), L47-98 (`__init__`).

| Category | Count | Matched |
|----------|-------|---------|
| Required | 2 (ui, current_project) | 2/2 |
| Attributes | 10 (agents, sys, state_tracker, memory, context_advisor, world_state, fact_ledger, adversarial_self_play, preset_registry, selected_genre, pass_rate_monitor) | 11/11 |
| Callbacks | 10 | 10/10 |
| Logger | 1 (session_logger) | 1/1 |

Note: docstring says "속성 9종" but `__slots__` comment says "속성 7종" while actual count is 11. This is a **cosmetic doc drift** only (P3).

---

### 2. Orchestrator `ctx.XXX` references vs Stage3Context declaration gaps

**Status**: OK

All `ctx.XXX` references in the orchestrator resolve to declared `__slots__`:

- `ctx.current_project` (L491, L521, L525, etc.) -- declared
- `ctx.ui` (L492, L540, etc.) -- declared
- `ctx.agents` (L443, L609, L818, L1245, L1251) -- declared
- `ctx.state_tracker` (L511, L1256) -- declared
- `ctx.world_state` (L512, L515) -- declared
- `ctx.fact_ledger` (L513) -- declared
- `ctx.memory` (L969) -- declared
- `ctx.context_advisor` (L970) -- declared
- `ctx.selected_genre` (L972-973) -- declared
- `ctx.adversarial_self_play` (L1260) -- declared
- `ctx.pass_rate_monitor` (L1357, L1870) -- declared
- `ctx.session_logger` (L1309, L1815) -- declared
- `ctx.sys` (L237, L1235) -- declared
- All 10 callbacks referenced with `callable()` guards -- declared

No undeclared attribute access found.

---

### 3. Callback `callable()` guard exhaustive check (S3-N-P1-3 pattern)

**Status**: OK

All 10 DI callbacks are guarded with `callable()` before invocation:

| Callback | Guard locations |
|----------|----------------|
| `get_protagonist_name` | L826, L868 |
| `audit_event` | L721, L741, L1275, L1488, L1497, L1511, L1527, L1944 |
| `write_audit_summary` | L602 |
| `get_arc_context_for_episode` | L730 |
| `get_max_episode_from_manuscripts` | L533 |
| `get_int_input` | L560 |
| `safe_commit` | L1509 |
| `validate_arc_data_fields` | L748 |
| `validate_blueprint_integrity` | L1495 |
| `fix_entity_registry_protagonist` | L827 |

Every callback site uses `callable(ctx.XXX)` or `callable(getattr(ctx, "XXX", None))` before calling. No unguarded invocation found.

---

### 4. Lazy init (`_init_*_if_needed`) -> `self.app` assignment -> `ctx` sync order correctness

**Status**: OK

Execution order in `stage_3_batch_blueprinting()`:
1. L498: `self._init_state_tracker_if_needed()` -- assigns to `self.app.state_tracker`
2. L503: `self._init_world_state_if_needed()` -- assigns to `self.app.world_state`
3. L508: `self._init_fact_ledger_if_needed()` -- assigns to `self.app.fact_ledger`
4. L511-513: ctx sync -- reads back from `self.app` with `getattr` safety
5. L515-516: StateTracker-WorldState rebind -- correct post-sync

Order is correct: init -> app assignment -> ctx sync -> cross-bind. No race or out-of-order risk.

**Evidence**: `stage3_orchestrator.py` L498-516, L630-690.

---

### 5. ctx sync timing (L511-516) — None propagation on init failure

**Status**: OK (by design)

Each `_init_*_if_needed()` method sets the attribute to `None` on failure (L653, L670, L690). The ctx sync at L511-513 uses `getattr(self.app, "xxx", None)`, so `None` propagates cleanly to ctx. Downstream code universally uses `if ctx.state_tracker`, `if ctx.world_state`, etc. before access.

The L515 guard `if ctx.state_tracker and ctx.world_state:` prevents `bind_world_state(None)`.

No None-dereference risk.

---

### 6. `_process_single_episode()` return dict (`break`/`next_ep`) vs while loop correspondence

**Status**: OK

The while loop (L590-597) consumes:
- `result["next_ep"]` -- always present in all return paths
- `result["success_count"]` -- always present
- `result["fail_count"]` -- always present
- `result.get("break")` -- checked with `.get()`, safe if absent

All return paths in `_process_single_episode()`:
- L713 (skip existing): `next_ep=working_ep+1` -- no break, loop continues
- L727 (no prev bp): `break=True` -- loop exits
- L736 (no arc ctx): `break=True` -- loop exits
- L743 (no ep_start): `break=True` -- loop exits
- L795-797 (`_handle_success`): returns from sub-method
- L799-806 (`_handle_failure`): returns from sub-method

`_handle_success` returns:
- L1499-1504 (integrity fail): `break=True`, `next_ep=working_ep+1`
- L1513-1518 (commit fail): `break=True`, `next_ep=working_ep+1`
- L1565 (normal success): no break key, `next_ep=working_ep+1`

`_handle_failure` returns:
- L1997-2002: `break=True`, `next_ep=working_ep` (stays on current ep)

All paths provide the 3 required keys. Loop correspondence is correct.

---

### 7. production_head calculation (L525-537) — both-zero -> episode 1 start verification

**Status**: OK

- L525: `existing_bp_max = db.get_latest_blueprint_number()` -- returns 0 if empty
- L530: `existing_ms_max_ep = max(0, int(latest_ep_fn() or 1) - 1)` -- Note: `or 1` means if fn returns 0/None, result = `max(0, 1-1) = 0`
- L537: `production_head = max(existing_bp_max, existing_ms_max_ep)` -- `max(0, 0) = 0`
- L568: `working_ep = production_head + 1` -- `0 + 1 = 1`

Both-zero correctly results in episode 1 start. The `or 1` in L530 is slightly misleading but mathematically correct: `max(0, int(1) - 1) = 0`.

**Evidence**: `stage3_orchestrator.py` L525-537, L568.

---

### 8. target_ep reversal defense (L547, L580) gap check

**Status**: OK

Two defense layers:

1. **L547**: `if production_head >= total_planned_ep:` -- catches case where all planned episodes already done. Returns early with `{success_count: 0, fail_count: 0}`.

2. **L580**: `if target_ep < working_ep:` -- catches case where user-entered (or caller-provided) target is already behind `working_ep`. Returns early.

Between L547 and L580, `target_ep` is set (L552-562). If `target_ep is None` and `callable(ctx.get_int_input)`, the input is bounded by `min_val=production_head+1`, preventing reversal. If not callable, defaults to `total_planned_ep` which passed the L547 check.

No gap found. Both pre-input and post-input reversal are defended.

---

### 9. `_handle_success` fail_count=0 reset (L1565) — total failure count loss

**Status**: FINDING

**Severity**: P2

**Evidence**: `stage3_orchestrator.py` L1565:
```python
return {"next_ep": working_ep + 1, "success_count": success_count + 1, "fail_count": 0}
```

On success, `fail_count` is unconditionally reset to 0. The while loop at L594 replaces the running `fail_count` with this value:
```python
fail_count = result["fail_count"]
```

This means if episodes 1-3 each fail once then succeed on retry (hypothetical -- currently Stage 3 breaks on any failure), the final reported `fail_count` would be 0 instead of accumulating.

**Impact**: In the current code, this is **low severity** because `_handle_failure()` always returns `break=True` (L2001), so the loop always exits on failure. The fail_count reset only matters if the failure-break pattern is ever relaxed. However, the final statistics at L608 (`실패: {fail_count}개`) would report 0 failures even if earlier episodes had failures before a later success, which is a **misleading metric**.

**Contrast with Stage 4**: Stage 4 orchestrator likely accumulates fail_count across episodes. This inconsistency could cause confusion in cross-stage telemetry.

---

### 10. `self.app` direct access (L1545, L1751, L1980) — ctx bypass intentionality

**Status**: FINDING

**Severity**: P3 (intentional, documented)

**Evidence**:

Three `self.app` direct access sites bypass `ctx`:

1. **L1545**: `_qd = getattr(self.app, "quality_dashboard", None)` -- QualityDashboard PASS recording
2. **L1751**: `_cdb = getattr(self.app, "constraint_db", None)` -- inventory gap fallback
3. **L1980**: `_qd = getattr(self.app, "quality_dashboard", None)` -- QualityDashboard REJECT recording
4. **L1194-1210**: `_record_retrieval_observation(self.app, ...)` -- retrieval observation (module-level function)

**Description**: These 4 sites access `self.app` attributes (`quality_dashboard`, `constraint_db`) that are NOT declared in `Stage3Context.__slots__`. This is a deliberate DI scope boundary: these are observability/telemetry sinks, not core orchestration dependencies.

**Impact**: Low. All accesses use `getattr(..., None)` with null guards. If `self.app` is replaced with a mock for testing, these would silently no-op. However, it means `Stage3Context` is not a complete DI boundary -- 2 app attributes (`quality_dashboard`, `constraint_db`) leak through.

**Recommendation**: If full DI isolation is desired, add `quality_dashboard` and `constraint_db` to `Stage3Context.__slots__`. Otherwise, document the intentional bypass.

---

## Summary

| # | Item | Status | Severity |
|---|------|--------|----------|
| 1 | `__slots__` vs `from_app()` 1:1 | OK | -- |
| 2 | `ctx.XXX` declaration gaps | OK | -- |
| 3 | Callback `callable()` guards | OK | -- |
| 4 | Lazy init -> app -> ctx sync order | OK | -- |
| 5 | ctx sync None propagation | OK | -- |
| 6 | `_process_single_episode` return/loop | OK | -- |
| 7 | production_head both-zero | OK | -- |
| 8 | target_ep reversal defense | OK | -- |
| 9 | `_handle_success` fail_count reset | FINDING | P2 |
| 10 | `self.app` direct access bypass | FINDING | P3 |

**Total**: 8 OK, 2 FINDING (1x P2, 1x P3). No P0/P1 issues found.
