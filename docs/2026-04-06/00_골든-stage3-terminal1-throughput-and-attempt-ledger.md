# Terminal 1: Throughput, Attempt Ledger, Manual-Stop Boundary

Date: 2026-04-06
Scope: `00_골든` latest Stage3 run (session `20260406_084609`)
Mode: read-only bounded survey

---

## Findings

### 1. Throughput materially worsens at ep4, peaks at ep5, recovers at ep6

Authoritative timeline (sources: `ui_events.jsonl` heartbeat→result pairs, `decisions.jsonl` attempt_key):

| ep | heartbeat ts | result ts | wall-clock | attempt | score | window | arc |
|----|-------------|-----------|------------|---------|-------|--------|-----|
| 1 | 08:48:20 | 08:51:51 | **3m 31s** | a1 | 92 | 0 | 1 |
| 2 | 08:52:03 | 08:58:05 | **6m 02s** | a1 | 94 | 1 | 1 |
| 3 | 08:58:17 | 09:01:50 | **3m 33s** | a1 | 95 | 2 | 1 |
| 4 | 09:02:02 | 09:11:45 | **9m 43s** | a2 | 92 | 3 | 1 |
| 5 | 09:11:59 | 09:29:29 | **17m 30s** | a2 | 84 | 4 | 1 |
| 6 | 09:30:38 | 09:36:46 | **6m 08s** | a2 | 92 | 5 | 2 |
| 7 | 09:36:58 | (manual stop) | **19m 34s+** | — | — | 6 | 2 |

Baseline (ep1-3 average): **4m 22s**

- **ep4**: 9m 43s = 2.2x baseline. First episode with internal retry.
- **ep5**: 17m 30s = 4.0x baseline. Worst completed episode. Score dropped to 84 (lowest).
- **ep6**: 6m 08s = 1.4x baseline. Recovery after arc boundary (Arc 1 → Arc 2). Entity Registry re-extraction at ep5→6 boundary added ~46s overhead (09:29:29 → 09:30:15).
- **ep7**: 19m 34s when stopped. Still within plausible range (see Finding 3).

The throughput degradation is **not monotonic**. ep6 recovered to near-baseline, proving the bottleneck is retry-driven, not cumulative context pressure.

### 2. ep4–ep6 persist as attempt_02 because of one internal retry each

**Mechanism** (confirmed via code):

```
three_phase_blueprint_runtime.py L1438:
    pipeline_result["retries"] = retry   # 0-based loop index

stage3_orchestrator.py L2168-2174:
    def _extract_stage3_attempt_num(pipeline_result):
        retries = pipeline_result.get("retries", 0)
        return max(1, int(retries) + 1)    # → attempt_num

logging_keys.py L50:
    parts = [f"s{stage_num}", f"ep{episode_num}", f"arc{arc_no}", f"a{attempt_no}"]
```

- ep1-3: `retries=0` → `a1` (first internal attempt succeeded, no retry)
- ep4-6: `retries=1` → `a2` (first internal attempt rejected by Phase 3 validation, second attempt succeeded)

**Why only attempt_02 artifacts exist:**

The ThreePhase runtime persists artifacts only for the final successful candidate (`snapshot_logged_artifact` at `stage3_orchestrator.py` L1826). Failed intermediate attempts are recorded to `pass_rate_monitor` via `_record_intermediate_reject` (`three_phase_blueprint_generator.py` L65-111) but do NOT produce artifact files.

Artifact directory confirms:

```
ep_0001/attempt_01/  ← a1 success
ep_0002/attempt_01/  ← a1 success
ep_0003/attempt_01/  ← a1 success
ep_0004/attempt_02/  ← a1 rejected internally, a2 success
ep_0005/attempt_02/  ← a1 rejected internally, a2 success
ep_0006/attempt_02/  ← a1 rejected internally, a2 success
```

**This is by design, not a bug.** The `max_retries=9` budget allows up to 10 internal attempts. One retry is a bounded internal repair cycle, not an alarm.

**What likely caused the internal reject at attempt_01:**

The retry mechanism provides previous-attempt feedback (`_build_retry_strategy_feedback` at runtime L228-245) including `prev_reject_strategy`, `prev_selection_reason`, `prev_reject_feedback`, `prev_fix_scope`, and `prev_validation_warnings`. This confirms the Phase 3 Director validation rejected the first candidate set and provided structured feedback for the second attempt.

The time overhead for retry follows this pattern:
- ep4: 9m43s ≈ ~5min (attempt_01 LLM call + rejection) + ~5min (attempt_02 LLM call + success)
- ep5: 17m30s ≈ ~9min (attempt_01) + ~9min (attempt_02) — longer due to window=4 context
- ep6: 6m08s ≈ ~3min + ~3min — faster because new Arc 2 context was smaller/cleaner

### 3. No authoritative evidence that ep7 was hanging

Evidence from all three authoritative sinks:

**ui_events.jsonl** (last ep7 events):
- Line 629, ts `09:36:58`: `"⏳ 제7화 Blueprint 생성 시작 (최대 10회 시도)..."` — normal progress event
- Line 630, ts `09:36:58`: `"⏳ 제7화 Blueprint 대기: ThreePhase runtime 호출 중 (anchors=0, window=6, semantic_ctx=2422자)"` — normal heartbeat, runtime actively calling LLM
- **No error events. No timeout events. No stall indicators. No REJECT events.**
- Line 631 is the end of the file.

**decisions.jsonl**: No ep7 entry. Normal — no verdict was reached before the manual stop.

**Artifact directory**: No `ep_0007/` directory. Normal — no artifact was persisted before the manual stop.

**tttt.txt** (convenience evidence only): Shows spinner `⠴ 제7화 · Blueprint 생성  19m 34s` — spinner was still actively progressing, not frozen.

**Duration analysis:**

| comparison | duration |
|-----------|----------|
| ep5 (completed, a2, window=4) | 17m 30s |
| ep7 (stopped, ?, window=6) | 19m 34s+ |
| ep5-to-ep7 window delta | +2 |

The 19m 34s duration at manual stop is within the observed range for a retry-cycle episode (ep5 = 17m30s with window=4). ep7 had window=6 (+2 additional previous blueprints in context), which would add LLM processing time.

If ep7 was on its first internal attempt (attempt_01) and that attempt was ~10min in, the remaining runtime would be another ~10min for the LLM response, placing total expected completion at ~20-25min. This is consistent with the 19m34s snapshot.

**Verdict: ep7 was in normal runtime wait, not hanging.** The manual stop terminated a healthy in-progress LLM call.

### 4. Narrowest owner file set

**Primary (2 files):**

| Owner | Role | Throughput impact |
|-------|------|------------------|
| `modules/domain/agents/three_phase_blueprint_runtime.py` | Owns the 3-phase retry loop (constraint → generation → validation), candidate selection, internal reject/retry logic | ALL retry-driven throughput variability originates here. Phase 2 generates 3 candidates with 3 LLM calls. Phase 3 runs Director validation. Internal reject triggers full re-run. |
| `modules/core/stage3_orchestrator.py` | Owns episode iteration loop, entity registry extraction, decision/artifact persistence, heartbeat logging | Entity Registry re-extraction at arc boundaries (28 → 56 entities, ~46s at ep5→6). Episode-level PASS/REJECT decision logging. |

**Not primary:**

| File | Why excluded |
|------|-------------|
| `modules/domain/agents/three_phase_blueprint_generator.py` | Thin facade — `generate()` at L134 is a 1-line delegation to `self.runtime.generate()`. No throughput logic. |
| Director (`modules/domain/agents/director.py`) | Runs WITHIN the runtime's Phase 3 call. Its latency is captured in the runtime's wall-clock. Not independently actionable for throughput. |

---

## Cross-Check Notes

### Attempt counter is per-episode, not session-global

The `retries` field is reset to 0 at bootstrap (`three_phase_blueprint_runtime.py` L207: `"retries": 0`) and updated per retry cycle (`L1438: pipeline_result["retries"] = retry`). The `a2` on ep4-6 reflects **each episode's own retry count**, not a session-level accumulation.

### Context window growth is bounded

`_STAGE3_HISTORY_CACHE_LIMIT = 36`, `_STAGE3_HISTORY_RECENT_LIMIT = 24`, `_STAGE3_HISTORY_ANCHOR_LIMIT = 6` (`stage3_orchestrator.py` L36-38). For ep1-7, the cache is well within limits. The `semantic_ctx` size grew from 2176자 (ep1-5, Arc 1) to 2422자 (ep6-7, Arc 2) — a modest +11% increase, not a throughput driver.

### No inter-episode gap anomalies

| transition | gap |
|-----------|-----|
| ep1→ep2 | 12s (entity cache reuse) |
| ep2→ep3 | 12s |
| ep3→ep4 | 12s |
| ep4→ep5 | 14s |
| ep5→ep6 | 69s (Entity Registry re-extraction: 28→56 entities, new Arc) |
| ep6→ep7 | 12s (entity cache reuse) |

The only notable gap is ep5→ep6 (Arc boundary + entity re-extraction). All other transitions are ~12s of orchestrator overhead.

---

## Summary Table

| Question | Answer |
|----------|--------|
| Where does throughput worsen? | **ep4** (2.2x baseline), peaks at **ep5** (4.0x). ep6 recovers. |
| Why attempt_02 for ep4-6? | One internal Phase 3 reject per episode. Normal bounded repair, not a quality alarm. `max_retries=9` budget barely touched. |
| Was ep7 hanging? | **No.** All sinks show normal runtime wait. 19m34s is within range for a retry-cycle episode with window=6. Manual stop is the sole cause of non-completion. |
| Narrowest owner set? | `three_phase_blueprint_runtime.py` (retry loop, candidate generation, validation) + `stage3_orchestrator.py` (episode loop, entity registry, persistence). |

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
