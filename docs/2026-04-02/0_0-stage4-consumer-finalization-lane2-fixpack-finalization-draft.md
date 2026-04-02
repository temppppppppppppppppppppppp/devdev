# 0_0 Stage4 Consumer-Finalization Lane 2: Fix-Pack and Finalization Contract

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: lane survey draft
Track: system
Mode: bounded static parallel survey, read-only
Terminal: Opus Terminal 2
Master Order: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas`

## 1. Coverage

### Required Surfaces Inspected

| File | Lines | Read Coverage |
|------|-------|---------------|
| `modules/core/stage4_interview_round.py` | 6820 | ~5400 lines (L1-5900): fix-pack helpers, gate normalization, post-select, advisory chain, verdict processing |
| `modules/core/stage4_retry_runtime.py` | 1250 | Full: pass-with-fix loop, retry lane routing, patch guards |
| `modules/core/stage4_reject_runtime.py` | 1040 | Full: reject guidance, retry snapshot, followup side effects |

### Questions Answered

1. **Where does Stage4 lose or flatten fix-pack truth?** — Answered (F-1, F-3, F-4, F-8)
2. **Which strong advisories can localize, and which fail closed because contract fields are missing?** — Answered (F-2, F-6)
3. **How does post_select_conflict reclassify bounded repair vs full rewrite?** — Answered (F-3, F-5)

## 2. Findings

### F-1: Fix-pack has two origin layers — Director-authored vs runtime-backfilled

**Location:** `stage4_interview_round.py` L2014-2084 (`_backfill_strong_advisory_fix_pack`)

When a strong advisory (TruthGate, NpcDrift, RelDrift, Flashback, InfoParadox) escalates a Director PASS to PASS_WITH_FIX, and the Director did not produce a fix_pack, the runtime synthesizes one:
- `patch_targets` are generated from advisory-type templates (e.g. "정합성 충돌 문장")
- `must_fix` instructions are generated from advisory-type templates
- `evidence_summary` is stamped with `"runtime strong advisory backfill: {triggered_classes}"`

**Split-truth implication:** Downstream consumers (retry lane, inplace patch, session log) see a fix_pack that looks Director-authored but is actually runtime-synthesized. The only distinguishing marker is the `evidence_summary` text, which is not a structured field. The `strong_advisory_escalation.local_fix_contract_backfilled` flag exists but is on the escalation dict, not on the fix_pack itself.

**Severity:** MEDIUM — the backfill is conservative and template-bound, but it creates a second truth origin for the same contract field.

### F-2: Strong advisory escalation creates a 4-step verdict cascade that can flip PASS → REJECT

**Location:** `stage4_interview_round.py` L2206-2374 (`_normalize_director_gate_semantics`)

The gate normalization applies these cascading rules in sequence:

1. **Lane2-G1** (L2212): PASS + any tier-2/3 advisory triggered → PASS_WITH_FIX
2. **Lane2-G2** (L2262): PASS_WITH_FIX + blank/invalid authoritative_fix_scope → REJECT
3. **Lane2-G2a** (L2276): If the REJECT came from advisory escalation, fix_scope is widened to "partial"
4. **Lane2-G2b** (L2316): Advisory escalation PASS_WITH_FIX where fix_scope != inplace OR fix_pack not ready → REJECT

**Net effect:** A Director PASS can traverse all four gates and emerge as REJECT with fix_scope="partial". The Director never saw a REJECT verdict — this is entirely runtime reclassification based on advisory presence + fix_scope contract validity.

**Split-truth implication:** The `gate_basis` field faithfully records which gate triggered the downgrade (e.g. `"strong_advisory_escalation_non_local_fix"`), and `scope_origin` metadata distinguishes Director-authoritative vs runtime layers. However, the operator console and session decision log show the same `final_verdict="REJECT"` regardless of whether it was Director-originated or cascade-originated, making post-hoc debugging of "why did this round fail?" harder.

**Severity:** MEDIUM — the cascading logic is correct but the number of possible paths (4 gates, 3+ possible gate_basis values) creates a combinatorial explosion that makes contract reasoning brittle for future changes.

### F-3: Post-select conflict unconditionally overwrites fix_scope to "full"

**Location:** `stage4_interview_round.py` L4376 + `stage4_reject_runtime.py` L607

When post-select checks (continuity or history conflict) fire:
- L4376: `director_result["fix_scope"] = "full"` — unconditional overwrite
- L4442: `previous_attempt["fix_scope"] = "full"` — retry snapshot also gets "full"
- L4398: `_post_select_fix_scope = "full"` — local variable is hardcoded
- `_build_reject_guidance_payload` L607: `resolved_fix_scope = "full"` — reject guidance also forces full

Additionally, `authoritative_fix_scope` is preserved separately (L4444), so the Director's original scope opinion survives in metadata. But the operational routing path reads `fix_scope`, not `authoritative_fix_scope`.

**Split-truth implication:** This is the single largest truth-flattening point in Stage4 finalization. A Director that returned `fix_scope="inplace"` with a complete fix_pack will have all of that overridden by one post-select conflict. The `scope_origin` metadata (L4489) marks this as `"post_select_conflict_override"`, which is correct, but retry routing ignores it.

**Severity:** HIGH — this is the dominant source of "Director said fix locally, runtime said rewrite everything" confusion observed in production.

### F-4: authoritative_fix_scope is tracked but not consumed by retry routing

**Location:**
- `stage4_interview_round.py` L2170 (capture)
- `stage4_reject_runtime.py` L442-444 (preserve in snapshot)
- `stage4_retry_runtime.py` L965 (routing reads `fix_scope` not `authoritative_fix_scope`)

The system correctly captures the Director's original fix_scope as `authoritative_fix_scope` and tracks scope widening in `scope_origin`. But the actual retry lane routing at `_resolve_retry_lane_routing` L965 reads:

```python
fix_scope = previous_attempt.get("fix_scope", "")
```

Not `authoritative_fix_scope`. This means all the careful semantic layering is observability-only — it does not influence the actual repair path.

**Split-truth implication:** The authoritative-vs-derived scope split is a telemetry/audit mechanism, not a contract enforcement mechanism. This is not necessarily wrong (the runtime may legitimately need to widen scope), but it creates a seam where operators see `authoritative_fix_scope="inplace"` in logs but the retry actually runs as "full".

**Severity:** MEDIUM — technically correct as observability but creates operator confusion.

### F-5: PASS_WITH_FIX → REJECT fallback can adopt patched manuscript while reporting REJECT

**Location:** `stage4_retry_runtime.py` L856-940 (`_finalize_pass_with_fix_loop_outcome`)

When the pass-with-fix loop exhausts its 3 iterations without achieving `fix_ok=True`:
- If the last re-audit returned PASS_WITH_FIX and the last patched ms differs from the original, the patched ms is adopted (L884-886)
- But the verdict is still set to REJECT (L882)
- The Director result is updated with the re-audit's fields (L894-916)

**Split-truth implication:** The accepted manuscript (carried forward as `best_manuscript` in the retry snapshot) is actually a patched version that passed a PASS_WITH_FIX re-audit, but the official verdict is REJECT. If the next retry succeeds and builds on this manuscript, the provenance chain shows REJECT → PASS but the actual content was partially fixed.

**Severity:** LOW — this is a design choice (prefer best available manuscript even on failure), but the provenance trail is slightly misleading.

### F-6: Advisory suppression can silently remove lower-tier warnings

**Location:** `stage4_interview_round.py` L1759-1802 (`_suppress_conflicting_advisories`)

When a tier-3 advisory (TruthGate) overlaps in subject with a tier-1 advisory (NumericDrift, LongTermRepetition), the lower-tier advisory is removed from the Director's mandatory_context pack. This is logged at INFO level but not surfaced as an explicit "suppressed" marker in the advisory summary.

**Split-truth implication:** The Director never sees the suppressed advisory. If the tier-3 advisory has a false positive or addresses a different aspect of the same entity, the suppressed tier-1 signal is permanently lost for that round.

**Severity:** LOW — the suppression logic has reasonable overlap detection, and the logging exists for audit.

### F-7: IFC classification can widen scope without Director re-evaluation

**Location:** `stage4_reject_runtime.py` L568-603 (`_build_reject_guidance_payload`)

The IFC (Immutable Fact Contract) classifier runs on rejection feedback text and fix_pack to detect violation families. When `should_escalate_to_rewrite()` returns True, it can widen `resolved_fix_scope` from "" or "inplace" to "partial" — without the Director being consulted on the scope change.

**Split-truth implication:** This is consistent with the "Python detects, LLM judges" principle for the *detection* step, but the scope *widening* is a routing decision that bypasses Director authority. The escalation is logged and added to `resolved_fix_scope_reasoning`, but the Director's next evaluation starts with an already-widened scope.

**Severity:** LOW-MEDIUM — aligns with the advisory-only principle in intent, but the scope widening is a side effect rather than a recommendation.

### F-8: Retry budget axes are advisory-only, not hard constraints

**Location:** `stage4_interview_round.py` L2138-2165 (`_set_retry_budget_axes`)

The retry budget system sets `repair`, `strategy`, `escalation`, and `guidance` axes that describe the intended retry approach. These are saved in the retry snapshot and logged in session decisions. However, `generate_candidates` in `stage4_retry_runtime.py` does not enforce them as hard constraints — the actual retry lane is determined by `fix_scope` + `fix_pack` contract readiness, not by budget axes.

**Split-truth implication:** Budget axes are pure observability metadata. They describe intent but do not constrain behavior. This is consistent but could confuse consumers who expect them to be binding.

**Severity:** LOW — observability is valuable, and the actual constraints are enforced elsewhere.

## 3. Non-Issues

- **Fix-pack normalization** (`_normalize_fix_pack`, `_normalize_fix_pack_list`, `_normalize_fix_target_kind`): Thorough and consistent. All paths go through the same normalization.
- **Advisory chain parallelism**: 9 advisories with proper ThreadPoolExecutor, 60s per-advisory timeout, 300s overall timeout, future cancellation on timeout. No resource leak.
- **Retry hash dedup** (`suppress_equivalent_retry_candidates`): Correctly uses SHA-256 content hash to prevent identical retries. Properly skips when reuse_contract exists.
- **Artifact provenance tracking**: `candidate_key`, `content_hash`, `artifact_path` triple is consistently produced and logged across PASS and REJECT paths.
- **scope_origin metadata**: Correctly distinguishes `director_authoritative`, `runtime_widened`, `post_select_conflict_override`, and `runtime_lane` origins.
- **Conflict contract construction**: `_build_post_select_conflict_contract` correctly preserves contradiction types, contradiction details, and bounded_local_fix_hint.
- **Reuse contract**: `reuse_contract` correctly marks post-select conflict retries as baseline reuse rather than fresh generation.

## 4. Verdict

**finalization-mixed**

The fix-pack contract is well-structured and the advisory chain is architecturally sound. However, the finalization path contains three truth-splitting seams:

1. **Post-select conflict unconditionally flattens fix_scope to "full"** (F-3) — this is the dominant consumer-side contract drift
2. **Strong advisory escalation cascade** (F-2) — creates 4 possible verdict paths from a single Director PASS, with the Director never seeing the final REJECT
3. **Fix-pack backfill** (F-1) — runtime-synthesized fix_packs look identical to Director-authored ones in downstream consumers

The `authoritative_fix_scope` + `scope_origin` metadata system is a correct observability layer, but it does not influence the actual routing decisions (F-4).

**Summary classification:** finalization-lossy for post-select conflict paths; finalization-clean for direct PASS/REJECT paths without advisory escalation.

## 5. Stop

read-only lane complete; no files mutated
