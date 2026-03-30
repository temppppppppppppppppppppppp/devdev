# Stage 4 Sink Alignment Fix — Execution SSOT

Date: 2026-03-29
Status: ready-for-execution (3-pass audited, confidence 97%)
Canonical Path: `docs/2026-03-29/stage4-sink-alignment-fix-execution-ssot.md`
Temp Mirror Path: (not mirrored — existing temp queue has 3 items + roadmap; this fix is standalone)
Source Survey Doc: `docs/2026-03-29/stage4-sink-alignment-bounded-survey.md`
Baseline Commit: `dae2dd2f`

## 1. Bug Statement

`patch_strategy` field has two independent derivation paths:
- **pass_rate_monitor** gets auto-filled `"patch_with_feedback"` via prelude normalization (L6014-6015)
- **episode_production** reads from `_patch_trace` dict which is empty for feedback-retry attempts (L5764)

This creates a mismatch that the sink alignment aggregator (failure_analyzer.py L791-801) correctly detects, and the hard gate evaluator (stage4_canary_tools.py L1353) incorrectly escalates to `errors` (blocking FAIL) instead of treating as a warn-level observability gap.

## 2. Authoritative Contract

| Field | Authority | Writer | Reader (aggregator) |
|---|---|---|---|
| `patch_strategy` | `pass_rate_monitor` (prelude-normalized) | `_record_stage4_pass_rate_attempt` L6072 | `failure_analyzer._load_pass_rate_monitor_alignment_sink` |
| `patch_strategy` (companion) | `episode_production.patch_trace` | `_append_episode_log` L5764 | `failure_analyzer._load_episode_production_alignment_sink` L584 |

**Decision**: pass_rate_monitor's prelude normalization is authoritative because it applies the `is_patch` flag consistently. episode_production should align to the same value.

## 3. Mismatch Taxonomy

| ID | Field | PRM Value | EP Value | Root Cause |
|---|---|---|---|---|
| M-1 | `patch_strategy` | `"patch_with_feedback"` | `""` | EP reads raw `_patch_trace` which is empty for feedback retries |
| M-2 | `patch_strategy` | `"patch_fallback_rewrite"` | (not observed yet) | Same mechanism, different branch — would fire on fallback retries |

## 4. Likely Root Cause

Single point: `_patch_trace` dict is only populated during InPlace patch operations. When `patch_with_feedback()` generates fresh candidates (not InPlace), `_patch_trace` stays `{}`, but `is_patch=True` is correctly set.

The prelude normalizer (L6014-6015) compensates for this by auto-filling from `is_patch` + `patch_fallback` flags. The episode_production writer does not have this compensation.

## 5. Touched-File Candidate Set

| File | Change | Risk |
|---|---|---|
| `modules/core/stage4_interview_round.py` | **Primary fix**: Propagate `prelude.normalized_patch_strategy` into `_patch_trace` before `_append_episode_log` reads it | Low — adds 1 assignment line |
| `modules/core/stage4_canary_tools.py` | **Optional**: Downgrade `patch_strategy_mismatches` from error to warning | Low — single line change in gate evaluator |
| `modules/core/failure_analyzer.py` | No change needed — aggregator correctly detects mismatch | None |

## 6. Implementation Order

### Option A: Single-Seam Fix (Recommended)

**Seam**: `stage4_interview_round.py`, in the episode_production entry builder, immediately before L5763.

**Change**: After prelude is computed but before episode_production entry is built, ensure `_patch_trace["patch_strategy"]` is populated from `prelude.normalized_patch_strategy` when empty.

```python
# Before building episode_production entry:
if prelude.normalized_patch_strategy and not _patch_trace.get("patch_strategy"):
    _patch_trace["patch_strategy"] = prelude.normalized_patch_strategy
```

This ensures both sinks derive from the same normalized value.

**Risk**: Minimal. `_patch_trace` is a local dict; this fills an empty field, does not overwrite existing values.

### Option B: Gate Severity Downgrade (Complementary)

**Seam**: `stage4_canary_tools.py` L1349-1362.

**Change**: Move `patch_strategy_mismatches` from the error list to the warning list.

```python
# Current (L1349-1362): all mismatch fields go to errors
# Proposed: split into error-grade vs warning-grade
error_fields = (
    "final_verdict_mismatches",
    "final_score_mismatches",
    "candidate_key_mismatches",
    "content_hash_mismatches",
    "artifact_path_mismatches",
    "artifact_missing_files",
    "artifact_metadata_missing",
)
warning_fields = (
    "initial_verdict_mismatches",
    "patch_strategy_mismatches",
    "selection_candidate_key_mismatches",
)
```

**Risk**: Low. This correctly separates artifact-truth mismatches (errors) from observability-metadata mismatches (warnings).

### Recommended Execution

1. Apply Option A first (single line in stage4_interview_round.py)
2. Apply Option B as complementary (gate severity taxonomy fix)
3. Validate with canary re-run

## 7. Validation Matrix

| Check | Method | Expected |
|---|---|---|
| Unit: `_patch_trace` populated | Add test: call `_record_s4_attempt` with `is_patch=True`, empty `patch_strategy`, verify `_patch_trace` gets normalized value | `_patch_trace["patch_strategy"] == "patch_with_feedback"` |
| Sink alignment: no mismatches | Re-run canary analyze on fixed project | `patch_strategy_mismatches = []` |
| Hard gate: pass | Re-run canary analyze | `hard_gates.status != "fail"` (may be "pass" or "warn" for unrelated) |
| Regression: existing pass paths | Run existing stage4 tests | No regression |
| Ruff: clean | `ruff check modules/core/stage4_interview_round.py modules/core/stage4_canary_tools.py` | 0 violations |

## 8. Closure Criteria

- [ ] `patch_strategy_mismatches` count = 0 on fresh canary
- [ ] `hard_gates.status` no longer "fail" due to this issue
- [ ] No regression in existing tests
- [ ] Ruff clean on touched files
- [ ] 3-pass code audit on touched lines

## 9. Non-Goals

- Resolving `director_verdict_mismatches` (different lifecycle semantics, not a bug)
- Resolving `repair_scope_mismatches` (different sinks capture at different lifecycle points, by design)
- Resolving `gate_basis_mismatches` (same reason)
- Adding `patch_strategy` column to `stage_attempts` DB table (not needed — PRM is authoritative)
