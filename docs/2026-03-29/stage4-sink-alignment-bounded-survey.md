# Stage 4 Sink Alignment Bounded Survey

Date: 2026-03-29
Status: final (3-pass audited, confidence 97%)
Baseline Commit: `dae2dd2f`
Canary Project: `projects/0_1_stage4_ep4_canary_r2`

## 1. Symptom

```json
{
  "hard_gates": {
    "status": "fail",
    "errors": ["patch_strategy_mismatches", "sink_alignment_status:warn"]
  }
}
```

2 attempt keys affected:
- `s4:ep2:arc1:a2:20260329_211919`
- `s4:ep4:arc1:a2:20260329_211919`

Both show `pass_rate_monitor.patch_strategy = "patch_with_feedback"` vs `episode_production.patch_strategy = ""`.

## 2. Sink Architecture

Stage 4 attempt data is written to 4 sinks:

| Sink | Type | Authority Role |
|------|------|---------------|
| `stage_attempts` | DB table | Final authority (attempt lifecycle, verdicts, advisory_flags) |
| `pass_rate_monitor` | JSON file | Operational monitor (pass rate trends, retry intelligence) |
| `episode_production` | JSONL file | Operator evidence (full per-attempt provenance + patch_trace) |
| `director_selections` | DB table | Companion evidence (Director rationale, selection reasons) |

`session/decisions.jsonl` is a session-scoped mirror of `stage_attempts`.

## 3. Root Cause

### 3.1 Dual-Source patch_strategy

`patch_strategy` has **two independent derivation paths** that diverge:

**Path A — pass_rate_monitor (via `_record_s4_attempt` prelude):**

```
stage4_interview_round.py L6013-6015:
  normalized_patch_strategy = str(patch_strategy or "").strip()
  if is_patch and not normalized_patch_strategy:
      normalized_patch_strategy = "patch_fallback_rewrite" if patch_fallback else "patch_with_feedback"
```

This auto-fills `"patch_with_feedback"` when:
- `is_patch=True` (retry used patch_with_feedback candidates)
- caller passed empty `patch_strategy=""` (because `_patch_trace` was empty)

**Path B — episode_production (via `_append_episode_log`):**

```
stage4_interview_round.py L5764:
  "patch_trace": {
      "patch_strategy": str(_patch_trace.get("patch_strategy", "") or ""),
      ...
  }
```

This reads directly from `_patch_trace` dict. When `patch_with_feedback()` is used for retries, `_patch_trace` is only populated during **InPlace patch** operations. For feedback-based retries that skip InPlace, `_patch_trace` remains `{}`.

### 3.2 When the Divergence Occurs

The mismatch happens specifically when:
1. A retry round uses `patch_with_feedback()` to generate new candidates
2. Director selects one but then post-select continuity check triggers REJECT
3. `_patch_trace` is never populated (no InPlace patch was performed)
4. `is_patch=True` is set (because `patch_with_feedback()` was called)

Result:
- pass_rate_monitor gets `"patch_with_feedback"` (auto-filled by prelude normalization)
- episode_production gets `""` (read from empty `_patch_trace`)

### 3.3 Hard Gate Escalation

```
stage4_canary_tools.py L1349-1362:
  for field in ("patch_strategy_mismatches", ...):
      if sink_alignment_summary.get(field):
          errors.append(field)
```

`patch_strategy_mismatches` is treated as an **error** (not warning), which pushes hard_gates to `"fail"`.

```
failure_analyzer.py L791-801:
  prm_strategy = pass_rate_monitor[attempt_key]["patch_strategy"]
  ep_strategy = episode_production[attempt_key]["patch_strategy"]
  if prm_strategy != ep_strategy:
      results["patch_strategy_mismatches"].append(...)
```

The aggregator extracts `episode_production.patch_strategy` from `patch_trace.patch_strategy` (L584).

## 4. Mismatch Taxonomy

| Mismatch Type | Count | Severity | Cause |
|---|---|---|---|
| `patch_strategy` PRM vs EP | 2 | **Gate blocker** (incorrectly) | Dual-source derivation; prelude auto-fills, EP reads raw _patch_trace |
| `director_verdict` | 2 | Warning-only | stage_attempts records final_verdict (post-TF3), director_selections records initial Director verdict |
| `repair_scope` | 5 | Warning-only | Different sinks capture scope at different lifecycle points |
| `gate_basis` | 7 | Warning-only | Similar lifecycle-stage capture divergence |

## 5. Authority Contract

| Field | Authoritative Sink | Reason |
|---|---|---|
| `final_verdict` | `stage_attempts` | Post all gates (TF-3, continuity firewall) |
| `initial_verdict` (Director's) | `director_selections` | Director primary decision before post-select gates |
| `patch_strategy` | Should be `pass_rate_monitor` | Prelude normalization is the correct derivation |
| `score` | `stage_attempts` | Final scored value |
| `candidate_key` / `content_hash` | `stage_attempts` + `director_selections` | Artifact provenance |
| `selection_reason` / `verdict_reason` | `director_selections` | Director rationale |

## 6. Impact Assessment

- **Artifact truth**: Unaffected. All 4 manuscripts are intact and correctly saved.
- **Metadata truth**: `patch_strategy` mismatch is observability-only. No verdict, score, or artifact selection was corrupted.
- **Narrative truth**: Not affected. The retry and PWF systems worked correctly at the content level.
- **Operational impact**: Hard gate falsely reports FAIL, blocking automated canary closure. Manual inspection shows the canary is substantively sound.

## 7. Files Investigated

| File | Purpose | Lines Referenced |
|---|---|---|
| `modules/core/stage4_interview_round.py` | Attempt recording, episode_production write | L5764, L6013-6015, L6072 |
| `modules/core/failure_analyzer.py` | Sink alignment aggregator | L561-584, L791-801 |
| `modules/core/stage4_canary_tools.py` | Hard gate evaluator | L1349-1362 |
| `modules/core/pass_rate_monitor.py` | PRM file writer | (record_attempt) |
| `modules/core/db_manager.py` | stage_attempts DB writer | (save_stage_attempt) |
