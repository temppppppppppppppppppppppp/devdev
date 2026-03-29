## Stage4 Carryover Contract Consumption Full Survey

Date: 2026-03-29
Status: draft-for-audit
Track: system
Type: bounded full-survey
Topic Slug: stage4-carryover-contract-consumption
Audit Order: `docs/2026-03-29/stage4-carryover-contract-consumption-full-survey-audit-order.md`
Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`

---

### 1. Scope and Intent

This survey answers one concrete question:

> Which carryover fields written during downgraded PASS or retry handoff are actually consumed by the next round generation path, which are operator-only persistence, and where does stored carryover truth stop affecting Chief Writer behavior?

The survey does not propose lane redesign, scope-sink policy changes, or broad Stage 4 routing changes.

Carryover fields surveyed:

| Field | Category |
|-------|----------|
| `best_manuscript` | Manuscript baseline |
| `selection_reason` | Director rationale |
| `open_review` | Director editorial observation |
| `conflict_contract` | Structured conflict specification |
| `reuse_contract` | Reuse routing contract |
| `scope_origin` | Scope-layer metadata |

---

### 2. Evidence Sources

| Source | Role |
|--------|------|
| `modules/domain/agents/chief_writer.py` L52-109, L1052-1102, L1952-1968 | Read-side: prompt assembly and strategy hints |
| `modules/core/stage4_reject_runtime.py` L351-448 | Write-side: REJECT snapshot assembly |
| `modules/core/stage4_interview_round.py` L3964-4016 | Write-side: POST_SELECT_CONFLICT carryover |
| `modules/core/stage4_outcome_runtime.py` L363-372, L935-984 | Write-side: CoVe downgrade + pathology payload |
| `modules/core/stage4_retry_runtime.py` L354, L783-785 | Pass-through: PASS_WITH_FIX audit result relay |
| `tests/test_chief_writer_candidate_lane_f.py` L166-247 | Test: read-side consumption assertions |
| `tests/test_stage4_handoff_carryover_guardrail.py` L76-167 | Test: write-side blanking and escalation |
| `tests/test_stage4_interview_round.py` L2918-2925, L8301-8595 | Test: scope-sink semantics + carryover structure |
| `projects/canary_0329_retry_loop_compression_check/logs/` | Live canary: persistence proof |
| `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md` | Prior survey: near-pass waste identification |
| `docs/2026-03-29/stage4-scope-sink-semantics-full-survey.md` | Prior survey: field ownership mapping |

---

### 3. Carryover Field Origin Map

#### 3.1 `best_manuscript`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_reject_runtime.py` | 389 | Standard REJECT | `selected_candidate.get("manuscript", "")` |
| `stage4_interview_round.py` | 3969 | POST_SELECT_CONFLICT downgrade | `final_manuscript` (the PASS manuscript being downgraded) |
| `stage4_outcome_runtime.py` | 365 | CoVe fail-closed downgrade | `final_manuscript` |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | Written fresh from Director's selected_candidate each round |
| POST_SELECT_CONFLICT | Explicitly written from the near-pass manuscript |
| CoVe fail-closed | Written from the provisional PASS manuscript |
| PASS_WITH_FIX | Not applicable — separate patch lane |

#### 3.2 `selection_reason`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_reject_runtime.py` | 351, 391 | Standard REJECT | `director_result.get("selection_reason", "")` |
| `stage4_interview_round.py` | 3964, 3979 | POST_SELECT_CONFLICT | `director_result.get("selection_reason", "")` |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | Preserved from director_result |
| POST_SELECT_CONFLICT (resolve_downgraded_pass_rationale=True) | Preserved |
| POST_SELECT_CONFLICT (resolve_downgraded_pass_rationale=False) | **BLANKED** to `""`, marker: `rationale_blanked_by: "runtime_post_select_conflict_elision"` (L371-373) |
| PASS_WITH_FIX | Relayed from audit_result via retry_runtime L783 |

#### 3.3 `open_review`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_reject_runtime.py` | 353, 411 | Standard REJECT | `director_result.get("open_review", "")` |
| `stage4_interview_round.py` | 3993 | POST_SELECT_CONFLICT | `director_result.get("open_review", "")` |
| `stage4_retry_runtime.py` | 354 | PASS_WITH_FIX empty feedback abort | Synthetic notice string |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | Preserved from director_result |
| POST_SELECT_CONFLICT (rationale preserved) | Preserved |
| POST_SELECT_CONFLICT (rationale blanked) | **BLANKED** to `""` (L372) |
| PASS_WITH_FIX | Overwritten with synthetic empty_feedback_notice (L354) |

#### 3.4 `conflict_contract`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_interview_round.py` | 3967, 4004 | POST_SELECT_CONFLICT | `_build_post_select_conflict_contract(_post_select_conflicts)` — structured dict with `contract_type`, `conflicts[]` |
| `stage4_reject_runtime.py` | 428-430 | Standard REJECT (carry-forward) | `copy.deepcopy(previous_attempt.get("conflict_contract"))` |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | Carried forward via deepcopy if present in previous_attempt |
| POST_SELECT_CONFLICT | **CREATED NEW** from current post-select conflicts (L78-111 builder) |
| CoVe fail-closed | Not created (absent from outcome_runtime L363-372) |

Note: `conflict_contract` is only originated on POST_SELECT_CONFLICT paths. On standard REJECT it carries forward from a prior POST_SELECT_CONFLICT round if one occurred.

#### 3.5 `reuse_contract`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_interview_round.py` | 4005-4010 | POST_SELECT_CONFLICT | Hardcoded structure: `mode=best_manuscript_baseline`, `baseline_field=best_manuscript`, `conflict_field=conflict_contract`, `preserve_rationale=True` |
| `stage4_reject_runtime.py` | 431-433 | Standard REJECT (carry-forward) | `dict(previous_attempt.get("reuse_contract"))` |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | Carried forward via shallow dict copy if present |
| POST_SELECT_CONFLICT | **CREATED NEW** with standardized best_manuscript_baseline mode |
| CoVe fail-closed | Not created |

#### 3.6 `scope_origin`

**Creation points:**

| Location | Line | Trigger | Source Value |
|----------|------|---------|--------------|
| `stage4_reject_runtime.py` | 438-448 | Standard REJECT | Computed: `fix_scope` = "runtime_widened" or "director_authoritative", `authoritative_fix_scope` = "director_authoritative", `repair_scope` = "runtime_lane" |
| `stage4_interview_round.py` | 4012-4016 | POST_SELECT_CONFLICT | Fixed: `fix_scope` = "post_select_conflict_override" |
| `stage4_outcome_runtime.py` | 956-980 | Pathology payload (all families) | Enriched or created fresh with same structure |

**Family preservation:**

| Family | Behavior |
|--------|----------|
| Standard REJECT | **ALWAYS CREATED** (not optional) |
| POST_SELECT_CONFLICT | **CREATED NEW** with conflict-specific origin marker |
| Pathology payload | Enriched from previous_attempt or created fresh |

---

### 4. Carryover Field Consumption Matrix

| Field | Stored in `previous_attempt` | Read by Chief Writer | Prompt-consumed | Lane-consumed | Operator-sink only |
|-------|------------------------------|----------------------|-----------------|---------------|-------------------|
| `best_manuscript` | YES | YES — `_build_retry_reuse_feedback_block()` L86 | **YES** — full text excerpt, smart-truncated to 20K chars (head 6K preserved) | NO | NO |
| `selection_reason` | YES | YES — two paths | **YES** — (1) metadata line in reuse block L97, (2) `strategy_specific_feedback` kwarg L1097/L1963 | NO | Also written to decisions.jsonl L488 |
| `open_review` | YES | YES — two paths | **YES, with lane caveat** — (1) metadata line in reuse block L99 when `reuse_contract` exists, (2) standalone `[Director 서사 관찰]` section L1081-1083 on full rewrite; patch lane direct consumption 없음 | NO | Also written to decisions.jsonl L491 |
| `conflict_contract` | YES | YES — `_format_retry_conflict_contract_block()` L103 | **YES** — structured `[Structured Conflict Contract]` block L59-73 | NO | Also written to pathology payload L948-950 |
| `reuse_contract` | YES | YES — `_build_retry_reuse_feedback_block()` L81-94 | **PARTIAL** — contract metadata (mode, baseline_field, rule) is prompt-visible; the contract itself controls which field to read for baseline manuscript | Also controls field routing (L85) | Also written to pathology payload L952-954 |
| `scope_origin` | YES | **NO** — zero reads in chief_writer.py or prompt_builder.py | **NO** | **NO** | **YES** — operator-facing only (pathology payload L956-980, decisions.jsonl) |

---

### 5. Prompt-Surface Injection Map

#### 5.1 Full Prompt Assembly Path

```
regenerate_with_feedback(previous_attempt)
  └─ _build_regeneration_feedback(previous_attempt, director_feedback, attempt_number)
       ├─ _build_retry_history_feedback(previous_attempt)
       │     └─ prior_attempts / history → [누적 실패 히스토리 — 반복 금지]
       ├─ _build_retry_reuse_feedback_block(previous_attempt)        ← CARRYOVER GATE
       │     ├─ Guard: requires reuse_contract dict + non-empty baseline_manuscript
       │     ├─ [Near-pass Baseline Reuse Contract — rewrite, do not discard gains]
       │     │     ├─ mode={reuse_contract.mode}
       │     │     ├─ baseline_field={reuse_contract.baseline_field}
       │     │     ├─ rule=Preserve already-working material...
       │     │     ├─ preserved_selection_reason={selection_reason}  (conditional)
       │     │     └─ preserved_open_review={open_review}  (conditional, filtered)
       │     ├─ [Structured Conflict Contract — rewrite target]       (conditional)
       │     │     └─ type=... | source=... | detail=... | expected=...
       │     └─ [Stored Near-pass Manuscript Baseline]
       │           └─ smart_truncate(best_manuscript, max_chars=20000, head_chars=6000)
       ├─ [Director 서사 관찰 — 반드시 개선할 것]                       ← open_review (separate)
       │     └─ open_review full text (filtered: 특이사항 없음/없음 excluded)
       └─ enhanced_feedback → generate_ensemble(director_feedback=enhanced_feedback)
  └─ _build_regeneration_strategy_hints(previous_attempt)
       └─ selection_reason → strategy_specific_feedback kwarg
```

#### 5.2 Patch Lane Assembly Path

```
patch_with_feedback(previous_attempt)
  └─ _build_patch_with_feedback_retry_args(previous_attempt)
       └─ selection_reason → strategy_feedback kwarg  (L1963)
  NOTE: patch lane does NOT call _build_retry_reuse_feedback_block()
        → best_manuscript, reuse_contract, conflict_contract are NOT consumed on patch lane
```

#### 5.3 `best_manuscript` Injection Detail

**Injection type**: Full text excerpt (not rationale-only, not excerpted context)

**Mechanism**: `smart_truncate(baseline_manuscript, max_chars=20000, head_chars=6000)` at chief_writer.py L108

**Labeled section**: `[Stored Near-pass Manuscript Baseline]`

**Activation gate**: `reuse_contract` must exist AND baseline field must be non-empty (L82-88). Without `reuse_contract`, the entire reuse block including `best_manuscript` is skipped.

**Implication**: `best_manuscript` is only prompt-consumed when `reuse_contract` exists. On standard REJECT paths where no prior POST_SELECT_CONFLICT occurred, `reuse_contract` will be absent, and `best_manuscript` will be stored but **never reach the prompt**.

#### 5.4 `open_review` Dual Injection

`open_review` has two independent consumption paths:

1. **Reuse block metadata** (L99-101): conditional on `reuse_contract` existing — appears as `preserved_open_review=...` metadata line
2. **Standalone Director observation section** (L1081-1083): unconditional (subject only to content filter) — appears as `[Director 서사 관찰 — 반드시 개선할 것]` section

Path 2 fires even when `reuse_contract` is absent, meaning `open_review` reaches the full-rewrite prompt surface without requiring `reuse_contract`, but it does not have patch-lane parity.

#### 5.5 `selection_reason` Dual Injection

`selection_reason` also has two independent consumption paths:

1. **Reuse block metadata** (L96-98): conditional on `reuse_contract` existing — appears as `preserved_selection_reason=...`
2. **Strategy feedback kwarg** (L1097 full rewrite, L1963 patch): unconditional — passed to `generate_ensemble()` as `strategy_specific_feedback`

Path 2 fires on all retry lanes (full rewrite and patch), meaning `selection_reason` always affects Chief Writer behavior regardless of `reuse_contract`.

---

### 6. Live Canary Evidence

#### 6.1 `canary_0329_retry_loop_compression_check`

**decisions.jsonl** — 5 rounds recorded:

| Field | Present | Location | Value Pattern |
|-------|---------|----------|---------------|
| `selection_reason` | YES — all 5 rounds | `meta.selection_reason` | Korean rationale strings (20-80 chars) |
| `open_review` | YES — all 5 rounds | `meta.open_review` | Korean editorial strings; one round shows `특이사항 없음` |

**Interpretation**: Both fields are **persisted** to decisions.jsonl on every PASS round. This confirms operator-sink visibility. However, sink presence alone does not prove prompt consumption. Prompt consumption is proven by code path analysis in Section 5.

**runtime_audit.jsonl** — 2 entries with carryover fields:

| Field | Present | Location |
|-------|---------|----------|
| `conflict_contract` | YES (1 entry) | `data.conflict_contract` |
| `open_review` | YES (2 entries) | `data.open_review` |

**Interpretation**: `conflict_contract` presence in runtime_audit confirms it was carried through a pathology payload (outcome_runtime L948-950). This is operator persistence, not generation consumption proof.

**episode_production.jsonl** — 7 entries with carryover fields:

| Field | Present | Count |
|-------|---------|-------|
| `selection_reason` | YES | 5 entries |
| `open_review` | YES | 7 entries |
| `conflict_contract` | YES | 1 entry |

**Interpretation**: `selection_reason` and `open_review` are the most widely persisted fields. `conflict_contract` appears only once, consistent with its POST_SELECT_CONFLICT-only origin.

#### 6.2 `canary_0329_scope_sink_semantics_check`

No JSONL decision or episode logs present — only canary_prep.json and session log. This canary did not produce retry evidence relevant to carryover consumption.

#### 6.3 Canary Limitation

No canary log can prove `best_manuscript` prompt injection because the injection happens inside `_build_retry_reuse_feedback_block()` which constructs an in-memory string passed to LLM — it is not separately logged. Code path analysis (Section 5.3) is the authoritative evidence.

---

### 7. Root-Cause Assessment

**Finding**: Carryover fields fall into three distinct behavioral tiers, not a single "carryover" abstraction.

#### Tier A: Lane-Complete Prompt-Consumed

| Field | Consumption Path | Always Fires |
|-------|-----------------|--------------|
| `selection_reason` | `strategy_specific_feedback` kwarg (L1097/L1963) | YES — all retry lanes |

This field reaches the Chief Writer prompt on **every** retry regardless of whether `reuse_contract` exists.

#### Tier B: Prompt-Consumed, But Not Lane-Complete

| Field | Consumption Path | Gate / Caveat |
|-------|-----------------|---------------|
| `open_review` | `[Director 서사 관찰]` section (L1081-1083) plus `preserved_open_review=` metadata (L99) | Standalone section fires on full rewrite only; metadata line requires `reuse_contract`; patch lane direct consumption 없음 |
| `best_manuscript` | `[Stored Near-pass Manuscript Baseline]` full text (L108) | `reuse_contract` must be dict and non-empty AND baseline must be non-empty |
| `conflict_contract` | `[Structured Conflict Contract]` block (L103) | Same gate — inside `_build_retry_reuse_feedback_block()` |
| `reuse_contract` | Contract metadata lines (L92-94) | Self-gating |
| `selection_reason` (secondary) | `preserved_selection_reason=` line (L97) | Same gate |
| `open_review` (secondary) | `preserved_open_review=` line (L99) | Same gate |

**Critical implication**: On standard REJECT paths where no POST_SELECT_CONFLICT has occurred, `reuse_contract` is absent. Therefore `best_manuscript` and `conflict_contract` are stored in `previous_attempt` but **never reach the prompt**. `open_review` is broader than those fields because it still reaches the full-rewrite prompt, but it remains patch-incomplete. The families that trigger reuse-gated Tier B consumption are:

- POST_SELECT_CONFLICT (creates `reuse_contract` at interview_round L4005)
- Any subsequent REJECT round that inherits `reuse_contract` via reject_runtime L431-433

#### Tier C: Operator-Only (never prompt-consumed)

| Field | Persistence Sinks |
|-------|------------------|
| `scope_origin` | pathology payload (outcome_runtime L956-980), decisions.jsonl |

`scope_origin` has zero reads in `chief_writer.py` or `prompt_builder.py`. It exists exclusively for operator interpretation.

#### Root Cause Summary

The root cause of confusion is that **the same `previous_attempt` dict serves both prompt-consumption and operator-persistence**, with no explicit marker distinguishing the two roles. A field's presence in `previous_attempt` looks equally important whether it is prompt-consumed or operator-only.

---

### 8. Highest-Risk Misreads

#### Misread 1: "best_manuscript is always reused on retry"

**Truth**: `best_manuscript` is only reused when `reuse_contract` exists in `previous_attempt`. This only happens on POST_SELECT_CONFLICT paths and their carry-forward. On standard Director REJECT paths, `best_manuscript` is stored but never reaches the prompt.

**Risk**: An operator seeing `best_manuscript` in a REJECT snapshot may assume Chief Writer uses it as a baseline. It does not unless `reuse_contract` is present.

#### Misread 2: "conflict_contract reaches Chief Writer on all REJECT families"

**Truth**: `conflict_contract` is only originated on POST_SELECT_CONFLICT paths. On standard REJECT, it can be carried forward from a prior POST_SELECT_CONFLICT round, but it is only prompt-consumed if `reuse_contract` is also present. A standalone `conflict_contract` without `reuse_contract` is impossible in current code (they are created together at L4004-4010).

**Risk**: Low — the two are co-created. But if future work adds `conflict_contract` to other families without adding `reuse_contract`, it would silently become dead carryover.

#### Misread 3: "scope_origin affects generation behavior"

**Truth**: `scope_origin` has zero reads in the generation path. It is purely operator metadata.

**Risk**: Moderate — an operator reading `scope_origin.fix_scope = "runtime_widened"` might assume the runtime widening was communicated to Chief Writer. It was not via `scope_origin`; the actual widened scope reaches Chief Writer through `fix_scope` and `fix_scope_reasoning` fields, not through `scope_origin`.

#### Misread 4: "open_review is blanked on POST_SELECT_CONFLICT so it never reaches the prompt"

**Truth**: `open_review` is blanked only when `resolve_downgraded_pass_rationale=False`. When preserved, it has two prompt paths — the reuse block metadata line and the standalone `[Director 서사 관찰]` section on full rewrite. It does not have patch-lane direct consumption. Even when blanked, the next round's fresh `open_review` from a new Director evaluation will populate the field again.

**Risk**: Low-MODERATE — the dual-path injection means `open_review` appears twice in the full-rewrite prompt when `reuse_contract` exists, but operators could still over-assume patch-lane parity if the caveat is undocumented.

#### Misread 5: "selection_reason is only metadata in the reuse block"

**Truth**: `selection_reason` has a second path as `strategy_specific_feedback` kwarg (L1097), which is consumed on all retry lanes. This path is unconditional and does not depend on `reuse_contract`.

**Risk**: Low — but operator-facing docs that describe `selection_reason` as "operator-visible only" would be incorrect.

---

### 9. Bounded Remediation Options Ranked

| Rank | Option | Scope | Risk | ROI |
|------|--------|-------|------|-----|
| 1 | **Document consumption matrix as operator reference** — freeze the Tier A/B/C classification plus the `open_review` lane caveat as an explicit contract doc, no code changes | Zero code change | Zero risk | HIGH — eliminates misreads 1-5 immediately |
| 2 | **Add `_consumption_tier` marker to carryover fields** — annotate each field in `previous_attempt` with its tier (prompt-consumed, conditional, operator-only) so downstream code and operators can distinguish | Additive metadata, no behavior change | Very low | MODERATE — makes the tiering machine-readable |
| 3 | **Remove `best_manuscript` from standard REJECT snapshots** where `reuse_contract` will not be created — prevents storing dead carryover that cannot reach the prompt | Subtractive, reject_runtime only | Low — could break if future code adds reuse_contract to standard REJECT | MODERATE — reduces misleading storage |
| 4 | **Wire `best_manuscript` into standard REJECT prompt** by creating a minimal `reuse_contract` on all REJECT paths | Additive, behavior change | Moderate — changes Chief Writer prompt on all retries, needs validation | LOW-MODERATE — might improve retry quality but needs canary |
| 5 | **Leave current behavior as-is** — persistence is intentionally operator-only where not prompt-consumed; document for clarity | Zero change | Zero risk | LOW — defers all clarity to ad-hoc reading |

---

### 10. Recommended Bounded Next Step

**Option 1: Document consumption matrix as operator reference.**

Rationale:

- The carryover system is currently **correct** — `selection_reason` reaches all retry lanes, `open_review` reaches the full-rewrite prompt and reuse metadata surface, and reuse-gated fields reach the prompt only when `reuse_contract` exists.
- The gap is **not behavioral** but **interpretive** — operators and future developers cannot distinguish prompt-consumed from operator-only fields without reading code.
- A frozen consumption matrix (this survey's Section 4 and Section 7) is the smallest safe artifact that eliminates all 5 misreads identified in Section 8.
- No code changes are needed because no field is incorrectly consumed or incorrectly ignored — the tiering is intentional, but the `open_review` patch-lane caveat must be documented explicitly.

The safest first move is:

> Freeze one explicit matrix for carryover fields that says which fields are only persisted, which fields are actually consumed by next-round generation, and which ones merely look important in operator sinks while having no behavioral effect.

This survey's findings directly support that conclusion.

---

### 11. Confidence

| Section | Confidence | Basis |
|---------|------------|-------|
| Carryover Field Origin Map | **HIGH** | Direct code inspection with line references |
| Carryover Field Consumption Matrix | **HIGH** | Direct code inspection of chief_writer.py prompt assembly path |
| Prompt-Surface Injection Map | **HIGH** | Full call chain traced from `regenerate_with_feedback` through `generate_ensemble` |
| `scope_origin` is operator-only | **HIGH** | Zero grep hits in chief_writer.py confirmed |
| `best_manuscript` gated by `reuse_contract` | **HIGH** | Guard at L82-88 confirmed — returns empty string without reuse_contract |
| Patch lane does not consume reuse block | **HIGH** | `patch_with_feedback()` at L1970+ does not call `_build_retry_reuse_feedback_block()` |
| Live canary evidence | **MODERATE** | Canary logs confirm persistence but cannot prove prompt-time injection (expected limitation) |
| `open_review` dual injection | **HIGH** | Two independent code paths at L99-101 and L1081-1083 confirmed |
| `selection_reason` dual injection | **HIGH** | Two independent code paths at L96-98 and L1097 confirmed |

**Overall survey confidence: HIGH** — all major findings are based on direct code inspection with exact line references. Canary evidence is used only as persistence confirmation, not as generation proof.
