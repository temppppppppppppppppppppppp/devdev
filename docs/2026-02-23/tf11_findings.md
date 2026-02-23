# TF-11 Findings - DI Wiring Verification Audit

> Baseline: `2,549 passed, 0 violations` (commit `91a87ab`)

---

## Current Position

```
Last Completed Round: Round D
Next Round: (done)
Status: completed
```

---

## Progress Table

| Round | Scope | Status | HIGH | MED | LOW | INFO |
|---|---|---|---:|---:|---:|---:|
| A | Stage2Context + Stage2 usage | done | 0 | 0 | 1 | 1 |
| B | Stage3Context + Stage3 usage | done | 0 | 0 | 1 | 1 |
| C | Stage4Context + Stage4 usage | done | 0 | 1 | 0 | 1 |
| D | main_a.py vs Context.from_app cross-check | done | 0 | 0 | 0 | 1 |

---

## Findings

### Round A

- `modules/core/stage2_context.py:46` + `modules/core/stage2_context.py:73` + `modules/core/stage2_context.py:97`  
  Snippet: `__slots__ = (... 'adversarial_self_play', ... 'sync_cache_key_to_app')`  
  Severity: INFO  
  Note: Current slot count is 47 (not 45 in order text), with additional DI surface now present.

- `modules/core/stage2_context.py:239` + `modules/core/stage2_orchestrator.py:182` + `modules/core/stage2_finalizer.py:314`  
  Snippet: `get_max_episode_from_manuscripts=getattr(app, ... None)` / `self.ctx.get_max_episode_from_manuscripts()` / `await self.ctx.safe_commit_async()`  
  Severity: LOW  
  Note: Several callbacks are DI-injected as nullable but called without `callable` guard; custom/partial app wiring can raise `NoneType` call errors.

### Round B

- `modules/core/stage3_context.py:16` + `modules/core/stage3_context.py:26`  
  Snippet: `__slots__ = (... 'adversarial_self_play', ...)`  
  Severity: INFO  
  Note: Current slot count is 20 (not 19 in order text).

- `modules/core/stage3_context.py:108` + `modules/core/stage3_orchestrator.py:304` + `modules/core/stage3_orchestrator.py:370`  
  Snippet: `validate_arc_data_fields=getattr(app, ... None)` / `ctx.validate_arc_data_fields(...)` / `ctx.fix_entity_registry_protagonist(...)`  
  Severity: LOW  
  Note: Nullable callbacks are invoked without `callable` checks on some paths (some calls are protected, but not uniformly).

### Round C

- `modules/core/stage4_context.py:52` + `modules/core/stage4_context.py:88` + `modules/core/stage4_context.py:143` + `modules/core/stage4_post_processor.py:291`  
  Snippet: slot/ctor include `emotion_tracker`, but `from_app()` return args omit it, while post-processor reads `self.ctx.emotion_tracker`.  
  Severity: MEDIUM  
  Note: DI mismatch: default `Stage4Context.from_app()` drops `emotion_tracker`; features depending on it are disabled on that path.

- `modules/core/stage4_context.py:30` + `modules/core/stage4_context.py:54` + `modules/core/stage4_context.py:62`  
  Snippet: `__slots__ = (... 'conditional_modules', ... callbacks ...)`  
  Severity: INFO  
  Note: Effective slot surface is 28, not the older 24(+conditional-keys) description.

### Round D

- `main_a.py:3256` + `main_a.py:3276` + `modules/core/stage4_context.py:143`  
  Snippet: `main_a` manually injects `emotion_tracker=...` when building Stage4Context, while `Stage4Context.from_app()` still omits it.  
  Severity: INFO  
  Note: Runtime path in `main_a` masks the `from_app()` mismatch; direct/lazy Stage4Orchestrator usage still has drift.

---

## Round Checklist Notes

### Round A (Stage2)
- Slot definition/from_app/usage mapping: completed.
- Dead middle-slot check: none found among current slots.
- `getattr(..., None)` nullable callback risk paths: present (documented above).

### Round B (Stage3)
- Slot mapping: completed.
- `world_state`/`fact_ledger` lazy init flow: present and synced back to ctx.
- 10 callback invocation audit: mixed guard strategy (documented above).

### Round C (Stage4)
- 24-slot(+conditional) mapping against actual code: completed (actual surface larger).
- `get_module()` unknown-module request path: no invalid key usage observed in audited files.
- `emotion_tracker` usage check: used in post-processing; `from_app()` omission confirmed.

### Round D (Cross-stage DI)
- `main_a.py` app attributes vs Context `from_app()` keys: compared.
- Typo/rename mismatch: none found for Stage2/Stage3 callback names.
- Cross-slot dependency mismatch: Stage4 `emotion_tracker` mismatch remains (masked by manual injection path).

---

## Totals

| Severity | Count |
|---|---:|
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 2 |
| INFO | 4 |
| **TOTAL** | **7** |