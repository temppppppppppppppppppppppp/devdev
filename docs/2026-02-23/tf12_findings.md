# TF-12 Findings - Failure Path Audit

> Baseline: 2,549 passed, 0 violations (commit `91a87ab`)

---

## Current Position

```text
Last Completed Round: Round F
Next Round: None
Status: Completed
```

---

## Progress Table

| Round | Scope | Status | HIGH | MED | LOW | INFO |
|---|---|---|---:|---:|---:|---:|
| A | DB transaction failure paths | Completed | 1 | 2 | 2 | 0 |
| B | Memory retrieval failure paths | Completed | 1 | 5 | 0 | 0 |
| C | Agent failure paths | Completed | 1 | 4 | 1 | 0 |
| D | Stage orchestrator failure paths | Completed | 2 | 4 | 1 | 0 |
| E | Validator failure paths | Completed | 2 | 3 | 1 | 0 |
| F | Resource cleanup + pass-only blocks | Completed | 0 | 2 | 2 | 0 |

---

## Findings

### Round A

1. `modules/core/project_manager.py:260`
```python
result = self.db.save_anchor(stage, data)
if self.db.conn.in_transaction:
    self.db.conn.commit()
```
Severity: HIGH
Explanation: `save_anchor()` failure (`False`) is ignored and an open transaction is force-committed, which can persist partial writes.

2. `modules/core/db_manager.py:1139`
```python
except sqlite3.IntegrityError as e:
    if not nested:
        self.rollback()
```
Severity: MEDIUM
Explanation: `update_lore_items_batch()` logs and returns on DB failure in non-nested mode, so callers can proceed as if lore sync succeeded.

3. `modules/core/db_manager.py:1202`
```python
except Exception as e:
    logging.warning(f"... Anchor ...: {e}")
    return False
```
Severity: MEDIUM
Explanation: `save_anchor()` swallows all exceptions and returns `False` without rollback, leaving transaction/error handling to callers inconsistently.

4. `modules/core/db_manager.py:238`
```python
try:
    self.conn.rollback()
except Exception as e:
```
Severity: LOW
Explanation: rollback failure during migration is silently suppressed (`pass`), so transaction state uncertainty is hidden.

5. `modules/core/db_manager.py:1214`
```python
try:
    return json.loads(row["data"])
except (json.JSONDecodeError, TypeError):
```
Severity: LOW
Explanation: corrupted anchor JSON is downgraded to default empty data, which masks data corruption as valid state.

### Round B

1. `modules/core/vec_memory.py:682`
```python
if not top:
    logging.debug("[VecMemory] hybrid search: no results for ep<%d", current_ep)
    return ""
```
Severity: HIGH
Explanation: hybrid retrieval returns empty context when dense+sparse both fail, with no keyword fallback, so writer context can collapse to blank.

2. `modules/core/vec_memory.py:1052`
```python
except Exception as _e:
    logging.debug("[VecMemory] FTS search failed: %s", _e)
    return []
```
Severity: MEDIUM
Explanation: FTS table/query failures are downgraded to empty results, hiding datastore breakage from callers.

3. `modules/core/stage4_context_builder.py:180`
```python
elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
    _fts = memory._fts_search(query_text, plan.episode_num, n_results=max_results)
    result = ("\n\n".join(...) if _fts else "")
```
Severity: MEDIUM
Explanation: sparse-mode retrieval has no dense fallback path, so FTS failures directly become empty Stage4 memory context.

4. `modules/core/stage2_preflight.py:146`
```python
elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
    _fts = memory._fts_search(query_text, current_ep, n_results=max_results)
    result = ("\n\n".join(...) if _fts else "")
```
Severity: MEDIUM
Explanation: Stage2 sparse-mode retrieval also lacks dense fallback, so preflight can run with missing memory evidence.

5. `modules/core/stage4_context_builder.py:200`
```python
except Exception as e:
    self.ctx.ui.log(f"... retrieval slot failed ...")
    continue
```
Severity: MEDIUM
Explanation: slot-level retrieval exceptions are skipped and execution continues, allowing all-slot failure to silently remove retrieval context.

6. `modules/core/stage2_preflight.py:172`
```python
except Exception as exc:  # OPTIONAL: retrieval failure should not block generation
    audit_cb("s2_vector_search_failed", str(exc)[:100])
    continue
```
Severity: MEDIUM
Explanation: preflight retrieval failures are treated as optional and skipped, so generation can proceed without any retrieval context.

### Round C

1. `modules/domain/agents/base_agent.py:208`
```python
new_client = genai.Client(api_key=cls._api_keys[cls._current_key_idx])
...
return new_client
```
Severity: HIGH
Explanation: API key rotation client creation is not guarded; if it raises, `ask()` fails before entering its retry/fallback block.

2. `modules/domain/agents/base_agent.py:757`
```python
if self.last_partial_response:
    self.requires_human_intervention = True
    return self.last_partial_response
```
Severity: MEDIUM
Explanation: malformed partial output is returned as payload fallback, which can propagate invalid JSON to downstream agents.

3. `modules/domain/agents/chief_writer.py:365`
```python
if not candidates:
    ...
    candidates = [{"strategy": "error_fallback", "manuscript": "", ...}]
```
Severity: MEDIUM
Explanation: total writer failure is converted into an error candidate with empty manuscript, letting pipeline continue in degraded mode.

4. `modules/domain/agents/analyst.py:1170`
```python
except Exception as e:
    logging.warning(f"... {e}")
    return raw_block
```
Severity: MEDIUM
Explanation: enrichment failures are silently downgraded to raw block return, so missing enrichment may pass undetected.

5. `modules/domain/agents/analyst.py:1439`
```python
def _validate_arc_with_state_tracker(self, arc_data: dict) -> list:
    ...
    return []
```
Severity: MEDIUM
Explanation: state-tracker validation is effectively disabled, so arc consistency issues are not surfaced at this stage.

6. `modules/core/adaptive_retry.py:851`
```python
if on_failure:
    try:
        feedback = on_failure(result, attempt)
    except Exception:
        feedback = ""
```
Severity: LOW
Explanation: failure-feedback callback errors are suppressed, so retries can proceed without corrective guidance context.

### Round D

1. `modules/core/stage2_orchestrator.py:308`
```python
for idx in range(batch_start, batch_end):
    if idx in original_batch_data:
        enriched_batch.append(original_batch_data[idx])
...
global_arc_no = batch_start + idx + 1
```
Severity: HIGH
Explanation: failed arcs are dropped from `enriched_batch`, then arc numbering is recalculated from compacted list index, which can shift downstream arc identity (validation/constraints/save) to the wrong arc number.

2. `modules/core/stage4_orchestrator.py:607`
```python
except Exception as e:
    logging.warning(f"[SilentPass:CoVe:LLM] {e!s:.100}")
...
except Exception as e:
    logging.warning(f"[SilentPass:CoVe:Quick] {e!s:.100}")
```
Severity: HIGH
Explanation: CoVe post-verification exceptions are downgraded to warnings, so manuscripts can remain accepted on PASS path even when verification runtime fails.

3. `modules/core/stage3_orchestrator.py:541`
```python
if callable(ctx.audit_event):
    ctx.audit_event("blueprint_gen_error", str(gen_err)[:200], {"ep_num": working_ep})
```
Severity: MEDIUM
Explanation: `audit_event()` is invoked inside blueprint generation exception handling without its own guard; audit failure can escape and break the intended ERROR fallback return path.

4. `modules/core/stage2_orchestrator.py:259`
```python
self.ctx.audit_event(
    "enrich_error", "batch enrich failed", {"error": str(item), "arc_idx": batch_start + idx}
)
```
Severity: MEDIUM
Explanation: Stage2 uses unguarded `audit_event()` calls in failure paths; if audit sink fails, telemetry failure can escalate into orchestration abort.

5. `modules/core/stage3_orchestrator.py:490`
```python
except Exception as _s3_slot_err:
    _logging.warning("[SilentPass:SC:Stage3] ...")
```
Severity: MEDIUM
Explanation: Stage3 smart-context slot failures are silently skipped, allowing blueprint generation to continue with partially missing retrieval evidence.

6. `modules/core/stage2_orchestrator.py:331`
```python
except Exception as stitch_err:
    self.ctx.audit_event("analyst_error", "stitch_joints failed", {...})
    continue
```
Severity: MEDIUM
Explanation: cross-arc stitch failures are logged and skipped, so joint continuity repair may be lost while pipeline continues.

7. `modules/core/stage4_orchestrator.py:278`
```python
except Exception as e:
    _perf_logger.warning(f"[V68] chain_link extraction failed ...")
    return {}
```
Severity: LOW
Explanation: chain-link extraction failure is downgraded to empty linkage data, which can silently reduce next-episode continuity context.

### Round E

1. `modules/validation/continuity_validator.py:113`
```python
if not prev_hud:
    return {"tier": "CONTINUITY", "passed": True, "degraded": True, ...}
```
Severity: HIGH
Explanation: when previous HUD is missing (including failed fetch path), continuity validation degrades to PASS and Stage4 can proceed without effective continuity enforcement.

2. `modules/validation/validation_orchestrator.py:1161`
```python
if isinstance(r, Exception):
    ...
    parallel_results[idx] = None
...
if not isinstance(consistency_result, dict):
    consistency_result = {"unjustifiable_violations": [], "score_penalty": 0, "feedback": ""}
```
Severity: HIGH
Explanation: parallel consistency-validator exceptions are converted to empty violations, so manuscripts may pass despite consistency validator runtime failure.

3. `modules/validation/blocking_validator.py:183`
```python
except (ValueError, KeyError, RuntimeError) as e:
    return {"check": "relationship_consistency", "passed": True, "degraded": True, "error": str(e)}
```
Severity: MEDIUM
Explanation: relationship/information consistency runtime errors are downgraded to degraded PASS in blocking tier, which weakens hard-stop behavior on validator failures.

4. `modules/validation/blocking_validator_scene_checks.py:52`
```python
if not scene_breakdown or not isinstance(scene_breakdown, dict):
    return {"check": "required_scenes", "passed": True}
```
Severity: MEDIUM
Explanation: missing/corrupt blueprint scene structure turns required scene checks into pass/skip, allowing blocking gate dilution when upstream blueprint payload is incomplete.

5. `modules/validation/validation_orchestrator.py:911`
```python
except Exception as e:
    logging.warning(f"[WARNING] Constitution load failed ...")
...
fallback = self._get_fallback_constitution(genre)
```
Severity: MEDIUM
Explanation: constitution load failures silently fall back to generic rules, which can materially alter scoring criteria without halting validation.

6. `modules/validation/validation_orchestrator.py:1028`
```python
except Exception as e:
    logging.warning(f"... Reflexion ... failed: {e}")
```
Severity: LOW
Explanation: Reflexion failure-recording errors are suppressed, so repeated failure patterns can be lost from learning/audit signals.

### Round F

1. `modules/core/diversity_sampler.py:82`
```python
if not samples:
    return "", {"error": "no_samples_generated"}
```
Severity: MEDIUM
Explanation: all-sample failure is converted to empty payload return instead of hard failure, so callers that ignore metadata can continue with blank candidate content.

2. `modules/core/stage01_helpers.py:164`
```python
except Exception as sync_err:
    ...
    app.ui.log("[Fallback] ... continue")
```
Severity: MEDIUM
Explanation: manuscript-history sync failures during Phase 0 recovery are downgraded to fallback-continue, which can leave memory/history unsynced while workflow proceeds.

3. `modules/core/stage01_helpers.py:180`
```python
try:
    input("\n[Enter] ...")
except (EOFError, KeyboardInterrupt):
    pass
```
Severity: LOW
Explanation: multiple pass-only blocks (`:180`, `:430`, `:447`, `:493`, `:515`, `:527`, `:553`, `:691`) swallow interrupt/EOF during pause points, hiding control-flow interruptions from logs.

4. `modules/core/stage0/__init__.py:377`
```python
except (ValueError, IndexError, EOFError):
    pass
```
Severity: LOW
Explanation: preset-management input errors are silently ignored; repeated invalid states can loop without explicit feedback or telemetry.

---

## Totals

| Severity | Count |
|---|---:|
| HIGH | 7 |
| MEDIUM | 20 |
| LOW | 7 |
| INFO | 0 |
| **Total** | **34** |
