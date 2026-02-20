# Debug Sweep 5 Plan (Codex Parallel)

> Updated: 2026-02-17
> Baseline: `1722 passed, 68 xfailed`
> Goal: observability/logging consistency + low-risk runtime hygiene
> Rule: no commits in this phase (edit + verify only)

---

## 1) Scope

Sweep 5 focuses on issues that are still noisy in production logs or technically deprecated, while avoiding behavior-changing refactors.

- A. `logging.info("⚠️ ...")` -> `logging.warning(...)` normalization
- B. `print(..., file=stderr)` -> `logging.error(...)` normalization
- C. deprecated asyncio API cleanup
- D. high-impact `except Exception: pass` -> warning log (selective)
- E. test/report sync

---

## 2) Item List

### A. Warning-level consistency (info -> warning)

Pattern:
```python
# before
logging.info("⚠️ ...")

# after
logging.warning("⚠️ ...")
```

Target groups (batch edit + file review):

1. `modules/domain/agents/director_auditor.py`
2. `modules/core/project_manager.py`
3. `modules/domain/agents/analyst.py`
4. `modules/domain/agents/arc_ensemble.py`
5. `modules/domain/agents/blueprint_ensemble.py`
6. `modules/domain/agents/chief_writer.py`
7. `modules/domain/agents/consensus_validator.py`
8. `modules/domain/agents/base_agent.py`
9. `modules/domain/agents/director_caching.py`
10. `modules/domain/agents/director_ensemble.py`
11. `modules/domain/agents/unified_arc_validator.py`
12. `modules/domain/agents/unified_blueprint_validator.py`
13. `modules/core/constants.py`
14. `modules/core/genre_hud_manager.py`
15. `modules/core/martial_manager.py`
16. `modules/core/reference_anchor.py`
17. `modules/core/stage2_preflight.py`
18. `modules/core/stage2_finalizer.py`
19. `modules/core/stage2_validation_pipeline.py`
20. `modules/domain/genre_manager.py`
21. `modules/validation/validation_orchestrator.py`

Notes:
- Keep `[INFO]` messages unchanged if they are not warning semantics.
- Only convert cases that already imply warning (`⚠️`, "warning", "경고", fallback/error path).

---

### B. stderr print normalization

Pattern:
```python
# before
print(msg, file=sys.stderr)
traceback.print_exc(file=sys.stderr)

# after
logging.error(msg)
logging.error(traceback.format_exc())
```

Targets:

1. `modules/domain/agents/arc_ensemble.py`
2. `modules/domain/agents/blueprint_ensemble.py`
3. `modules/domain/agents/consensus_validator.py`
4. `modules/domain/agents/chief_writer.py`
5. `modules/core/stage3_orchestrator.py`

Optional stdout normalization (informational):

6. `modules/core/stage3_orchestrator.py` (`print(...)` -> `logging.info(...)` for stage progress logs)
7. `modules/domain/agents/state_tracker_npc.py` (`print(...)` -> `logging.info(...)`)

---

### C. Deprecated asyncio API

1. `modules/validation/batch_validator.py`

Change:
```python
# before
loop = asyncio.get_event_loop()

# after
loop = asyncio.get_running_loop()
```

Reason:
- This call is inside async flow; `get_running_loop()` is the correct modern API.

---

### D. Selective silent-swallow hardening

Only high-impact mutation paths (do not blanket-replace all soft-fail blocks).

1. `modules/core/project_manager.py`
- DB sync status update swallow -> warning log with episode number.

2. `modules/core/stage2_preflight.py`
- genre registry update swallow -> warning log.
- semantic plot guard indexing swallow -> warning log.

3. `modules/core/writer_prompt_builders.py`
- critical extraction fallback swallows -> warning log (include short context key).

4. `modules/core/stage2_orchestrator.py`
- state_extractor cache invalidation swallow -> warning log.

5. `main_a.py`
- rollback-time writer cache invalidation swallow -> warning log.

Rule:
- Keep soft-fail behavior (non-blocking).
- Add observability only.

---

### E. Test and docs sync

1. Add `tests/test_sweep5.py` with focused cases:
- warning-level conversion sanity (sample files)
- `batch_validator` running-loop path
- selected soft-fail logging paths do not propagate exceptions

2. Update roadmap/worklog docs after verification:
- `docs/프로젝트_현황_로드맵_2026-02-16.md`
- `작업_2026-02-16.md` (or latest worklog file)

---

## 3) Validation Gates

1. Compile changed files
```bash
python -m py_compile <changed_files>
```

2. Ruff
```bash
python -m ruff check <changed_files>
python -m ruff format <changed_files>
```

3. Sweep 5 tests
```bash
set PYTHONIOENCODING=utf-8
python -m pytest tests/test_sweep5.py -q
```

4. Full regression
```bash
set PYTHONIOENCODING=utf-8
python -m pytest tests/ -q
```
Expected: `1722+ passed, 68 xfailed`

---

## 4) Execution Notes (Codex)

- Parallelize by category (A/B/C/D), then run E.
- Do not commit in this phase.
- If any category causes regression, stop at that category and report file+line only.

---

## 5) Suggested Commit Messages (for later manual use)

```text
fix(sweep5-a): normalize warning-level logging for warning-semantic info logs
fix(sweep5-b): replace stderr prints with structured logging
fix(sweep5-c): migrate batch_validator to asyncio.get_running_loop
fix(sweep5-d): add observability to selected silent-swallow mutation paths
test(sweep5): add focused regression tests for logging and async loop hygiene
```
