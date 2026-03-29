## Stage4 Blueprint Frontier Patch Trigger Semantics Full Survey

Date: 2026-03-29
Status: draft-for-audit
Track: system
Type: bounded full-survey
Topic Slug: stage4-blueprint-frontier-patch-trigger-semantics
Audit Order: `docs/2026-03-29/stage4-blueprint-frontier-patch-trigger-semantics-full-survey-audit-order.md`
Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`

---

### 1. Scope and Intent

This survey answers one concrete question:

> When Stage 4 encounters continuity-firewall or related structural reject families, what exact runtime conditions trigger blueprint/frontier patch behavior versus another manuscript retry, and where is that trigger contract authoritative today?

The survey does not propose lane redesign, blunt round compression, or broad blueprint authoring changes.

---

### 2. Evidence Sources

| Source | Role |
|--------|------|
| `modules/domain/agents/director_ensemble.py` L1149-1213 | Firewall gate: V75-C contradiction firewall origin |
| `modules/domain/agents/director_auditor.py` L1109-1119 | Firewall gate: auditor-side parallel trigger |
| `modules/core/stage4_interview_round.py` L819-859 | Continuity replay classifier: `_is_continuity_replay_reject()` |
| `modules/core/stage4_reject_runtime.py` L500-568 | Runtime enforcement: A-4 continuity replay + IFC escalation + post_select_conflict |
| `modules/core/stage4_outcome_runtime.py` L596-627, L792-873 | Logic error streak + V75-D/V75-B escalation trigger |
| `modules/core/stage4_orchestrator.py` L1804-1864, L2028-2094 | V75-D inplace patch + V75-B full regen execution |
| `modules/core/stage4_policy_digest.py` L40-42 | Policy thresholds |
| `modules/core/stage4_retry_runtime.py` L831-925 | Manuscript retry lane routing |
| `tests/test_v75c_contradiction_firewall.py` L32-218 | Firewall trigger unit tests |
| `tests/test_stage4_orchestrator.py` L344-2283 | V75-D/V75-B escalation tests |
| `tests/test_blueprint_patch_mode.py` L59-140 | Blueprint inplace patch mechanics |
| `projects/canary_0329_feedback_windowing_check/logs/` | Live canary: V75-D + V75-B full escalation chain observed |
| `projects/canary_0329_retry_loop_compression_check/logs/` | Live canary: V75-D patch + continuity_firewall evidence |

---

### 3. Trigger Ownership Map

The blueprint/frontier patch trigger system has three distinct owners that act in sequence. Conflation of these three is the primary source of operator misreads.

#### Layer 1: Director Ensemble — Contradiction Firewall (V75-C)

**Owner**: `director_ensemble.py` `_apply_contradiction_firewall_gate()` L1149-1213

**Trigger condition** (L1167):
```
CRITICAL contradiction count >= 1  OR  MAJOR contradiction count >= 2
```

**Two modes** (L1168-1198):
- **Fixable mode** (`firewall_mode == "pass_with_fix"`): `state.firewall_fixable = True`, score capped to 97, verdict → `PASS_WITH_FIX`
- **Hard firewall** (else): `state.firewall_triggered = True`, verdict forced → `REJECT`, score capped to `min(score, 44)` (L1203)

**Output fields**: `firewall_triggered`, `firewall_fixable`, `firewall_reason`, `contradiction_details`

**Ownership**: **Director-authored** — the Director ensemble evaluates contradictions from its consistency checklist. Python hardcodes severity thresholds (CRITICAL >= 1, MAJOR >= 2) and score caps, but the contradiction assessment itself comes from the LLM.

#### Layer 2: Interview Round — Continuity Replay Classifier

**Owner**: `stage4_interview_round.py` `_is_continuity_replay_reject()` L819-859

**Trigger condition**: `firewall_triggered == True` AND at least one of:
1. `contradiction_types` contains any of: `scene_overlap`, `event_ordering`, `space_continuity`, `timeline_arc_consistency`, `opening_diversity` (L828-836)
2. Combined text from `director_feedback` + `verdict_reason` + `open_review` + `firewall_reason` contains Korean or English continuity markers (L838-859)

**Ownership**: **Runtime-derived** — Python classifies the firewall reject into a specific continuity replay family using keyword matching over Director-provided text. The Director does not signal "continuity replay" explicitly.

#### Layer 3: Reject Runtime — Enforcement Actions

**Owner**: `stage4_reject_runtime.py` `_handle_reject_verdict()` L500-568

**When continuity replay fires** (L500-518):
- `error_category` forced to `"LOGIC_ERROR"` (L504)
- `reject_bucket` set to `"post_select_conflict"` if fix_scope was not already "full", else `"structure_error"` (L505)
- `fix_scope` forced to `"full"` (L507)
- Injects `[A-4 continuity replay]` notice into director_feedback (L508-513)

**When IFC violation detected** (L520-556):
- `fix_scope` widened from `""` or `"inplace"` to `"partial"` (L542-543)
- Injects `[IFC]` escalation notice

**When `reject_bucket == "post_select_conflict"`** (L558-568):
- `fix_scope` forced to `"full"` unconditionally
- `fix_pack` cleared to `{}`
- Injects `[Conflict-first retry]` notice

**Ownership**: **Runtime-derived** — all enforcement is Python policy, not Director signaled.

#### Layer 4: Outcome Runtime — Logic Error Streak + Escalation

**Owner**: `stage4_outcome_runtime.py` L596-873

**Streak accumulation** (L545-552): `logic_error_streak` incremented when `_should_count_reject_as_logic_like()` returns True.

**`_should_count_reject_as_logic_like()`** (L596-627) returns True when:
1. `error_category == "LOGIC_ERROR"` (L606) — **this is always true for continuity firewall rejects** due to Layer 3 forcing it
2. IFC quality issue with plateau detected (L609-613, L630-646)
3. `reject_bucket == "post_select_conflict"` with `provisional_pass_downgrade` (L622-627), controlled by policy `treat_post_select_conflict_as_logic_like` (default=True)

**Escalation trigger** `apply_retry_repair_escalation()` (L792-873):

| Escalation | Condition | Action | Line |
|------------|-----------|--------|------|
| **V75-D** (inplace blueprint patch) | `logic_error_streak >= v75d_threshold` AND `not inplace_attempted` | `_apply_v75d_inplace_repair()` | L843 |
| **V75-B** (full blueprint regen) | `logic_error_streak >= blueprint_regeneration_threshold` AND `inplace_attempted` AND `not blueprint_regenerated` | `_apply_v75b_blueprint_regeneration()` | L854 |
| No escalation | Default fallthrough | Return unchanged state | L866 |

**Policy thresholds** (stage4_policy_digest.py L40-42):
- `quality_risk_inplace_threshold`: **1** (if blueprint has quality_risk flag)
- `default_inplace_threshold`: **2** (standard)
- `blueprint_regeneration_after_inplace_streak`: **2** (logic errors after V75-D before V75-B)

**Ownership**: **Runtime policy** — Python controls thresholds, streak counting, and escalation gating. Director has no direct influence on when V75-D/V75-B fires.

#### Layer 5: Orchestrator — Blueprint Patch/Regen Execution

**V75-D execution**: `stage4_orchestrator.py` `_apply_v75d_inplace_repair()` L1759-1802 → `_attempt_v75d_inplace_blueprint_patch()` L1840-1864
- Calls `bp_agent._inplace_patch_blueprint(original_blueprint, director_feedback, ...)` (L1853)
- Max change ratio: ~30% (observed canary: 29.02%)
- On success: `round_ctx.blueprint` updated, `logic_error_streak` reset to 0
- On failure: `inplace_attempted = True` set (blocks re-attempt, enables V75-B)
- Always sets `blueprint_regenerated = False`

**V75-B execution**: `stage4_orchestrator.py` `_apply_v75b_blueprint_regeneration()` L2028-2094
- Builds Stage 4→3 reverse feedback (L2046-2048)
- Calls `_regenerate_blueprint()` with merged feedback (L2050-2054)
- On success: new blueprint installed, `logic_error_streak` reset to 0, `previous_attempt` cleared to `{}`, `director_feedback` replaced with regen notice (L2056-2069)
- On failure/exception: `blueprint_regenerated = True` set to block further attempts (L2071-2075)

**Ownership**: **Orchestrator execution** — the blueprint agent performs the actual patch/regen, but the orchestrator owns the decision to invoke it.

---

### 4. Gate-to-Blueprint/Frontier Transition Matrix

#### 4.1 Complete Decision Chain

```
Director Ensemble
  └─ V75-C contradiction firewall
     ├─ firewall_triggered=True → REJECT, score≤44
     └─ firewall_fixable=True → PASS_WITH_FIX, score≤97

Interview Round
  └─ _is_continuity_replay_reject()
     └─ True → continuity replay classification

Reject Runtime
  └─ A-4 continuity replay enforcement
     ├─ error_category = "LOGIC_ERROR"
     ├─ reject_bucket = "post_select_conflict" (if fix_scope was not "full")
     ├─ fix_scope = "full"
     └─ [A-4 continuity replay] notice injected

Outcome Runtime
  └─ _should_count_reject_as_logic_like() → True (error_category == "LOGIC_ERROR")
     └─ logic_error_streak += 1

  └─ apply_retry_repair_escalation()
     ├─ streak >= v75d_threshold AND !inplace_attempted
     │    → V75-D: inplace blueprint patch (30% max change)
     ├─ streak >= blueprint_regen_threshold AND inplace_attempted AND !blueprint_regenerated
     │    → V75-B: full blueprint regeneration (new blueprint from Stage 3)
     └─ else → ordinary manuscript retry with full rewrite
```

#### 4.2 Gate Family to Blueprint Trigger Mapping

| Gate Family | Triggers Continuity Replay? | Counts as Logic-Like? | Can Trigger V75-D? | Can Trigger V75-B? |
|-------------|----------------------------|-----------------------|--------------------|---------------------|
| `continuity_firewall` (with continuity types) | **YES** | **YES** (error_category forced to LOGIC_ERROR) | **YES** (at streak threshold) | **YES** (after V75-D) |
| `continuity_firewall` (without continuity types) | **NO** | Depends on error_category | Depends on streak | Depends on V75-D |
| `post_select_conflict` (A-3 downgrade) | **NO** (different path) | **YES** (if provisional_pass_downgrade, policy-gated) | **YES** (at streak threshold) | **YES** (after V75-D) |
| `quality_floor_fail` | **NO** | **NO** (unless IFC-tagged plateau) | Only via IFC escalation path | Only after V75-D via IFC |
| `director_primary_reject` | **NO** | Depends on error_category | Only if LOGIC_ERROR | Only after V75-D |
| `pass_with_fix_contract_*` | **NO** | **NO** | **NO** (streak resets) | **NO** |

#### 4.3 Manuscript Retry Lane vs Blueprint Patch

These are **independent** decisions at different levels:

**Manuscript lane routing** (`stage4_retry_runtime.py` `_resolve_retry_lane_routing()` L831-925):
- Decides: inplace patch / manuscript patch / full rewrite for the **manuscript**
- Inputs: `fix_scope`, `reject_bucket`, `fix_pack`, `round_num`, `prev_score`
- This always fires regardless of V75-D/V75-B

**Blueprint escalation** (`stage4_outcome_runtime.py` `apply_retry_repair_escalation()` L792-873):
- Decides: V75-D inplace blueprint patch / V75-B full blueprint regen / no blueprint change
- Inputs: `logic_error_streak`, `inplace_attempted`, `blueprint_regenerated`
- When V75-D/V75-B fires, it modifies the blueprint **before** the next manuscript retry round
- After V75-B success, `previous_attempt` is cleared and `director_feedback` is replaced, so the manuscript retry starts fresh

**Critical distinction**: Blueprint patch and manuscript retry are **not mutually exclusive**. V75-D patches the blueprint, then the next round still generates a new manuscript (typically full rewrite because continuity_replay forces `fix_scope=full`). They operate at different substrate levels.

---

### 5. Live Canary Evidence

#### 5.1 `canary_0329_feedback_windowing_check` — Full V75-D → V75-B Escalation Chain (EP3)

This canary shows the complete escalation sequence on a single episode:

| Round | Gate Basis | Firewall | Fix Scope | Error Category | Blueprint Action |
|-------|-----------|----------|-----------|----------------|-----------------|
| R0 | `patch_reaudit_fail` | TRUE | inplace | QUALITY_ISSUE | — |
| R1 | `continuity_firewall` | TRUE | full | LOGIC_ERROR | **V75-D inplace patch** (change_ratio=0.2902) |
| R2 | `continuity_firewall` | TRUE | full | LOGIC_ERROR | — (V75-D already attempted) |
| R3 | `post_select_conflict` | FALSE | partial | CONSTRAINT_VIOLATION | — |
| R4 | `continuity_firewall` | TRUE | full | LOGIC_ERROR | **V75-B full regen** (streak=2) |
| R5 | `post_select_conflict` | FALSE | partial | CONSTRAINT_VIOLATION | — |

**UI event timeline** (from `session/ui_events.jsonl`):
- seq=294: `"🔧 [V75-D] LOGIC_ERROR 1연속 → 블루프린트 inplace 패치 시도..."` (07:28:41)
- seq=295: `"✅ [V75-D] inplace 패치 성공"` (07:29:19)
- seq=399: `"🔄 [V75-B] LOGIC_ERROR 2연속 → 블루프린트 재생성 시도..."` (07:45:38)
- seq=400: `"✅ [V75-B] 블루프린트 재생성 성공"` (07:49:12)

**V75-D artifact snapshot** (from `runtime_audit.jsonl` entry 3):
```json
{
  "type": "stage4_v75d_blueprint_patch_snapshot",
  "data": {
    "ep_num": 3,
    "round_num": 1,
    "candidate_key": "V75-D|blueprint_inplace",
    "change_ratio": 0.2902,
    "artifact_path": "logs/artifacts/stage4/ep_0003/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json"
  }
}
```

**Interpretation**: V75-D fired at R1 (streak=1, quality_risk threshold met), patched 29% of blueprint, but firewall continued at R2. After R2+R4 accumulated streak=2, V75-B fired for full blueprint regeneration. Episode eventually PASS at R5 after post_select_conflict resolution.

This is **not** 8R→2R compression — EP3 ran 6 rounds. The 8R→2R claim likely refers to a different episode or a comparison across canary runs, not a single-episode observation.

#### 5.2 `canary_0329_retry_loop_compression_check` — V75-D Only (No V75-B)

| Entry | Gate Basis | Firewall | Fix Scope | Error Category | Blueprint Action |
|-------|-----------|----------|-----------|----------------|-----------------|
| 1 | `post_select_conflict` | FALSE | partial | CONSTRAINT_VIOLATION | — |
| 2 | `continuity_firewall` | TRUE | full | LOGIC_ERROR | — |
| 3 | — | — | — | — | **V75-D inplace patch** (candidate_key=V75-D\|blueprint_inplace) |

**Interpretation**: V75-D fired after continuity_firewall LOGIC_ERROR, but V75-B was not needed — episode resolved before streak reached blueprint_regeneration_threshold.

#### 5.3 Evidence Limitation

Neither canary persists `blueprint_regenerated` or `logic_error_streak` as top-level fields in the JSONL sinks. These are in-memory state variables tracked within `_InterviewRoundLoopState`. Their values must be inferred from the sequence of UI events and V75 artifact snapshots. This is an operator visibility gap for the escalation state machine.

---

### 6. Root-Cause Assessment

**Finding**: The blueprint/frontier patch trigger is a **three-layer escalation chain** with distinct ownership at each layer, not a single decision point.

#### 6.1 The Trigger Contract Is Stable and Deterministic

The V75-D/V75-B escalation is **deterministic** given the same `logic_error_streak`:

1. Streak counting is deterministic: `_should_count_reject_as_logic_like()` uses clear field checks (L606: `error_category == "LOGIC_ERROR"`, L622-626: `reject_bucket == "post_select_conflict"`)
2. Threshold comparison is simple integer: `logic_error_streak >= v75d_threshold` (L843)
3. State flags (`inplace_attempted`, `blueprint_regenerated`) are monotonic booleans — once set True, never reset

The **non-deterministic** element is **which rounds count as logic-like**. A continuity_firewall reject always counts (Layer 3 forces LOGIC_ERROR). But a `post_select_conflict` from A-3 downgrade only counts if `treat_post_select_conflict_as_logic_like` policy is True (default) AND `provisional_pass_downgrade` is True (L622-626).

#### 6.2 The 8R→2R Improvement Is Not Proven General

The canary evidence shows:
- EP3 in `canary_0329_feedback_windowing_check` ran **6 rounds** with both V75-D and V75-B
- V75-D at R1 patched 29% of blueprint but did not resolve the firewall
- V75-B at R4 regenerated the full blueprint, and the episode passed 2 rounds later

This is consistent with "blueprint patch helps but doesn't guarantee compression." The evidence **supports** that the trigger contract is mechanically sound but **does not prove** that V75-D alone produces 8R→2R compression. The specific 8R→2R claim would require:
- A before/after comparison on the same episode content with different policy
- Or evidence that V75-D alone resolved a previously 8-round episode in 2 rounds

Neither is present in current canary evidence.

#### 6.3 The Layered Ownership Creates an Operator Interpretation Gap

The trigger chain crosses 5 files and 4 ownership layers:

| Layer | File | Decides | Operator Visible? |
|-------|------|---------|-------------------|
| V75-C firewall | director_ensemble.py | Whether contradiction triggers firewall | YES — `firewall_triggered`, `firewall_reason` in sinks |
| Continuity replay | stage4_interview_round.py | Whether firewall is continuity-specific | **NO** — `_is_continuity_replay_reject()` result is not persisted |
| A-4 enforcement | stage4_reject_runtime.py | `error_category=LOGIC_ERROR`, `fix_scope=full` | YES — `error_category`, `fix_scope` in sinks |
| Streak counting | stage4_outcome_runtime.py | `logic_error_streak` increment | **NO** — streak is in-memory only |
| V75-D/V75-B decision | stage4_outcome_runtime.py | Whether to patch/regen blueprint | **PARTIAL** — V75-D artifact snapshot persisted; V75-B success logged to UI events; but the streak value and threshold comparison are not persisted |

**Root cause**: An operator can see that V75-D or V75-B fired (via artifact snapshot or UI event), but cannot see **why** it fired (the streak value, the threshold used, which rounds counted as logic-like). The trigger contract is internally deterministic but externally opaque.

---

### 7. Highest-Risk Operator Misreads

#### Misread 1: "Continuity firewall always triggers blueprint patch"

**Truth**: Continuity firewall triggers `error_category=LOGIC_ERROR` (Layer 3), which increments `logic_error_streak` (Layer 4). V75-D only fires when streak reaches the threshold (default 2, quality_risk 1). A single firewall reject does NOT trigger V75-D unless `quality_risk=True`.

**Risk**: HIGH — an operator seeing `continuity_firewall` + `firewall_triggered=True` may expect V75-D to follow immediately. It may not until the streak accumulates.

#### Misread 2: "V75-D resolves the structural problem"

**Truth**: V75-D patches up to ~30% of the blueprint. In the canary, V75-D fired at R1 but `continuity_firewall` persisted at R2. V75-D is a **partial repair**, not a guaranteed resolution. V75-B (full regen) is the fallback.

**Risk**: MODERATE — operators may conclude V75-D failed if the next round is still a firewall reject, when in reality the patch was applied but insufficient.

#### Misread 3: "V75-D and V75-B are Director-signaled lanes"

**Truth**: V75-D/V75-B are **purely runtime escalation**. The Director signals firewall severity and fix_scope but has no knowledge of or control over V75-D/V75-B. The streak threshold, escalation sequence, and execution are all Python runtime decisions.

**Risk**: MODERATE — documentation or operator training that describes V75-D as "Director requests blueprint patch" would be factually wrong.

#### Misread 4: "logic_error_streak counts all REJECT rounds"

**Truth**: `_should_count_reject_as_logic_like()` only counts rounds where:
- `error_category == "LOGIC_ERROR"` (continuity_firewall via A-4 enforcement), OR
- IFC quality issue with plateau, OR
- `post_select_conflict` with `provisional_pass_downgrade` (policy-gated)

Ordinary `quality_issue` or `constraint_violation` rejects **reset the streak to 0** (L545-551). An intervening non-logic reject between two firewall rejects resets the streak and delays V75-D/V75-B.

**Risk**: HIGH — this means the escalation sequence is fragile to oscillation between firewall and non-firewall gate families. The canary shows exactly this pattern: `continuity_firewall` → `post_select_conflict` → `continuity_firewall` oscillation. If `post_select_conflict` is not counted as logic-like (policy disabled), the streak resets and V75-B may never fire.

#### Misread 5: "blueprint_regenerated prevents all further blueprint changes"

**Truth**: `blueprint_regenerated = True` is set **even on V75-B failure** (L2071-2074). This blocks further V75-B attempts in the same episode but also means a failed regen is treated as "done" — the system falls back to manuscript retry with the original (or V75-D-patched) blueprint.

**Risk**: LOW — correct fail-closed behavior, but operators cannot distinguish "V75-B succeeded and blueprint is new" from "V75-B failed and original blueprint is still active" unless they check the UI event log for `✅ [V75-B] 블루프린트 재생성 성공` vs `⚠️ [V75-B] 블루프린트 재생성 실패`.

---

### 8. Bounded Remediation Options Ranked

| Rank | Option | Scope | Risk | ROI |
|------|--------|-------|------|-----|
| 1 | **Document the trigger matrix** — freeze the 5-layer escalation chain as an explicit operator-facing contract doc; include streak-counting rules and threshold values | Zero code change | Zero risk | HIGH — eliminates misreads 1, 3, 4 immediately |
| 2 | **Persist `logic_error_streak` to pathology payload** — add the streak value to `build_retry_pathology_payload()` so operators can see why V75-D/V75-B did or did not fire | Additive metadata in outcome_runtime, one field | Very low | HIGH — eliminates the primary operator-invisible state variable |
| 3 | **Persist `continuity_replay_classified` boolean to reject snapshot** — surface whether `_is_continuity_replay_reject()` fired, so operators can distinguish "firewall + continuity" from "firewall + other contradiction type" | Additive metadata in reject_runtime | Very low | MODERATE — closes the Layer 2 visibility gap |
| 4 | **Persist V75-D/V75-B outcome (success/fail/skipped) to pathology payload** — currently only visible in UI events and artifact snapshots; adding to JSONL sink would make escalation outcome queryable | Additive metadata | Very low | MODERATE — closes the escalation outcome visibility gap |
| 5 | **Lower `default_inplace_threshold` from 2 to 1** to match quality_risk behavior — would make V75-D fire sooner on all episodes, not just quality_risk ones | Policy change, behavior change | LOW-MODERATE — changes escalation timing for all episodes; needs canary validation | LOW — unclear if earlier V75-D improves outcomes generally |
| 6 | **No code change** — current trigger is deterministic and mechanically sound; document only | Zero change | Zero risk | LOW-MODERATE — defers visibility gaps to manual log reading |

---

### 9. Recommended Bounded Next Step

**Option 1: Document the trigger matrix.**

Rationale:

- The blueprint/frontier patch trigger contract is **mechanically sound and deterministic**. No field is misbehaving, no threshold is incorrectly calibrated for the observed canaries.
- The gap is **operator visibility and interpretation**, not trigger logic. The five-layer chain is internally consistent but externally opaque.
- A frozen trigger matrix that includes streak-counting rules, threshold values, and the exact conditions under which V75-D/V75-B fire would immediately eliminate the 4 highest-risk misreads.
- The 8R→2R claim is **not disproven** but also **not yet generalized** from canary evidence. Documentation should record what is proved (the trigger contract) without overstating compression guarantees.

The safest first move is:

> Freeze one explicit trigger matrix for when continuity-firewall or adjacent structural families move from manuscript retry into blueprint/frontier patch behavior, so future canaries and operators can distinguish a true upstream substrate correction from another ordinary retry.

This survey's findings directly support that conclusion.

**If ROI justifies a second tranche**: Option 2 (persist `logic_error_streak` to pathology payload) is the single highest-impact additive metadata change. It would make the escalation state machine observable without any behavior change.

---

### 10. Confidence

| Section | Confidence | Basis |
|---------|------------|-------|
| V75-C firewall trigger (Director ensemble) | **HIGH** | Direct code inspection: director_ensemble.py L1149-1213 |
| Continuity replay classifier | **HIGH** | Direct code inspection: stage4_interview_round.py L819-859 |
| A-4 enforcement actions | **HIGH** | Direct code inspection: stage4_reject_runtime.py L500-568 |
| Logic error streak counting | **HIGH** | Direct code inspection: stage4_outcome_runtime.py L596-627 |
| V75-D threshold and trigger | **HIGH** | Direct code: outcome_runtime L843 + policy_digest L40-42 |
| V75-B threshold and trigger | **HIGH** | Direct code: outcome_runtime L854 + policy_digest L42 |
| V75-D execution mechanics | **HIGH** | Direct code: stage4_orchestrator.py L1840-1864 |
| V75-B execution mechanics | **HIGH** | Direct code: stage4_orchestrator.py L2028-2094 |
| Canary V75-D+V75-B escalation chain | **HIGH** | Raw UI events + artifact snapshot from canary_0329_feedback_windowing_check |
| 8R→2R generality | **LOW** | No before/after comparison on same episode content; canary EP3 ran 6 rounds, not 2 |
| Streak reset on non-logic reject | **HIGH** | Direct code: outcome_runtime L545-551 (ternary resets to 0) |
| Operator visibility gaps | **HIGH** | Confirmed by searching JSONL sinks: `logic_error_streak` and `continuity_replay_classified` absent from all persistent sinks |

**Overall survey confidence: HIGH** — all trigger mechanics are traced with exact line references. The one LOW-confidence item (8R→2R generality) is explicitly marked as unproven from current evidence.
