# 0_0 Stage4 Consumer-Finalization Lane 3: Post-Pass State / Active-Pressure / State-Write Truth

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: survey lane draft
Lane: 3 — post-pass state / active-pressure / state-write truth
Parent Order: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Track: system
Mode: bounded static parallel survey, read-only

---

## 1. Coverage

### Files read (full or substantial sections)

| File | Lines read | Role |
|---|---|---|
| `modules/core/stage4_post_processor.py` | 1–1098 (full) | PASS 후처리 총괄, state-write orchestration |
| `modules/core/stage4_post_pass_runtime.py` | 1–1049 (full) | Manager 정산, bible_delta 조립, WorldState/FactLedger 원자 저장, advisory |
| `modules/core/stage4_reject_runtime.py` | 1–750 | reject guidance, retry snapshot, state_updates 반영 경로 |
| `modules/core/stage4_interview_round.py` | 4232–4870 | post-select checks, final_state_updates 생성, `_annotate_positive_verdict_state` |
| `modules/core/stage4_context_packets.py` | 390–419 | active_pressure_vectors context-packet 소비 |
| `modules/core/world_state.py` | 140–905 | `update_from_state_changes`, pressure vector 적용/상한 |
| `modules/core/project_manager.py` | 660–672 | `latest_state` property — state_logs DB 읽기 |

### Surfaces not covered (out-of-lane)

- Stage4 context_builder intake truth (Lane 1)
- Stage4 fix-pack contract specifics (Lane 2)
- Artifact-level vertical slicing (Lane 4)

---

## 2. Findings

### F-1. Triple-Source State Truth Split (CRITICAL)

On the PASS path, Stage4 generates and persists **three independent state-truth surfaces** that describe the same episode's post-episode reality. Each surface has its own authority, write path, and downstream consumers.

| Surface | Producer | Authority | Persistence | Downstream consumer |
|---|---|---|---|---|
| **`final_state_updates`** | Director (`director_result.state_updates`) | Director LLM 판정 | DB `manuscripts` + `martial_tracker`, file `ep_NNNN.txt`, HUD bulk_update | DB primary save, HUD overlay, quality sidecars |
| **`actual_truth`** | Manager LLM (`update_state_and_lore_v20` → `state_updates.actual_truth`) | Manager LLM 판정 | `state_logs.data.actual_truth`, `bible_delta.state_changes` | `latest_state` property, next-ep context builder, next-ep Manager submission |
| **`WorldState._state`** | Python `update_from_state_changes()` | Python 자동 | `world_state` DB anchor | `_build_condensed_world_state` context packet |

**The split-truth problem:**

1. `final_state_updates` comes from Director at verdict time — it reflects what Director saw in the selected candidate's metadata.
2. `actual_truth` comes from Manager's `update_state_and_lore_v20` — a separate LLM call that independently reads the finalized manuscript and may produce a different understanding of what changed.
3. `WorldState._state` is mechanically populated from a merged payload (`_build_atomic_state_payloads`) that uses `final_state_updates` as the base, then overlays `bible_delta` fields (which come from `actual_truth`).

These three surfaces are written in the same PASS pipeline but they **never reconcile with each other**. If Manager and Director disagree on what changed (e.g., Manager sees a relationship shift that Director's `state_updates` didn't include, or vice versa), the disagreement is silently persisted into different downstream stores.

**Evidence:**
- `stage4_post_pass_runtime.py:918-919`: `state_log_data["actual_truth"] = actual_truth if actual_truth else final_state_updates` — fallback only when Manager audit fully fails.
- `stage4_post_pass_runtime.py:1012-1020`: `world_state_changes = dict(final_state_updates or {})` then overlays `inventory_payload`, `relationship_payload`, `martial_payload`, `pressure_payload` from `bible_delta` — mixing Director base with Manager overlays.
- `stage4_post_pass_runtime.py:1022`: `fact_ledger_changes = dict(final_state_updates or {})` — same base, different overlay set (no martial, no pressure).

### F-2. active_pressure_vectors: Build-Filter-Persist Lossy Chain (IMPORTANT)

Active pressure vectors describe ongoing narrative threats/hooks. Their lifecycle:

1. **Build**: `_build_active_pressure_vectors(blueprint)` → reads `ending_hook`, `cliffhanger`, `expected_ending` from blueprint.
2. **Filter**: `_filter_active_pressure_vectors_by_manuscript(vectors, final_manuscript)` → keeps only vectors whose cue terms appear in the manuscript's last 1,200 characters.
3. **Persist into actual_truth**: `actual_truth["active_pressure_vectors"] = list(active_pressure_vectors)` (L467).
4. **Persist into bible_delta**: `bible_delta["active_pressure_vectors"] = list(active_pressure_vectors)` (L767).
5. **Persist into WorldState**: via `_build_atomic_state_payloads` → `pressure_payload` → `world_state_changes.update(pressure_payload)` → `WorldState.update_from_state_changes()` (L489–491).
6. **Persist into state_logs**: via `_persist_manager_state_log` (L926).
7. **Read-back next episode**: `WorldState._state["active_pressure_vectors"]` → context_packets `_build_condensed_world_state_tail_sections`.

**Split-truth point**: Pressure vectors are **blueprint-sourced, not Manager-sourced**. They are injected into `actual_truth` at L467, overriding whatever Manager might have produced. The Manager has no authority over this field — it's purely a Python post-pass overlay. This is architecturally sound (blueprint is authoritative for structural hooks), but creates a subtle issue: the vectors in `actual_truth` never went through the Manager LLM, yet they sit alongside Manager-produced fields. Downstream consumers that treat `actual_truth` as Manager-authoritative may misattribute these vectors.

**Lossy filter**: The manuscript-tail filter (last 1,200 chars) drops vectors whose hooks were resolved mid-episode or never appeared in the finale. This is intentional (filter out already-resolved pressure) but the filter doesn't distinguish "resolved" from "not yet activated." An ending_hook that builds slowly through the episode but doesn't appear in the last 1,200 chars is silently dropped.

**WorldState cap**: `world_state.py:900-901` — `active_pressure_vectors` is capped at 5 entries. The post-processor's normalization caps at 3 (`_normalize_active_pressure_vectors` returns `[:3]`). These caps compound but don't conflict since post-processor's cap is tighter.

### F-3. State-Log Fallback Masks Manager Failure (IMPORTANT)

`stage4_post_pass_runtime.py:919`:
```python
"actual_truth": actual_truth if actual_truth else final_state_updates,
```

When Manager LLM completely fails (both async and sync retry), `actual_truth` is `{}`, so `state_log_data["actual_truth"]` silently falls back to `final_state_updates` — Director's state understanding. The next episode's `latest_state.get("actual_truth")` then returns Director-sourced data masquerading as Manager-produced truth. No audit trail or marker distinguishes this fallback.

**Impact**: Downstream consumers of `latest_state` (Manager's own next-ep submission at L147, prev_actual comparison at L569-570, pressure vector diff) operate under a false assumption about their authority source.

### F-4. WorldState + FactLedger Atomic Save Recovery Asymmetry (MODERATE)

`_save_world_state_atomic` attempts a transactional save of both WorldState and FactLedger. If the DB exposes `transaction()`, both are wrapped in one context. Otherwise, it falls into "sequential save recovery mode" (L1207-1212).

In sequential mode, if FactLedger save succeeds but WorldState rollback fails:
- `world_state_snapshot` is restored via in-memory deepcopy fallback (L1168-1169)
- But `fact_ledger_snapshot` rollback already happened (L1151-1158)
- The two stores now reflect different episodes

This is partially mitigated by the deepcopy snapshots, but the mitigation assumes in-memory restoration matches what would have been persisted.

### F-5. HUD Update Runs After DB Save But Before Manager Audit (MODERATE)

In `process_pass_result`, the execution order is:
1. `_save_pass_result_primary_db` — DB save (Director's final_state_updates)
2. `_run_pass_result_local_side_effects` — HUD update via `director.on_approve_workflow`, file write, capital reconcile
3. `_run_pass_result_post_pass_pipeline` — Manager async submit → VecMemory → Manager collect → bible_delta → WorldState/FactLedger

The HUD is updated based on Director's `final_state_updates` **before** the Manager audit completes. If Manager's `actual_truth` contradicts Director (e.g., different capital amount, different item inventory), the HUD reflects Director's view while state_logs and WorldState reflect Manager's view. The capital reconciliation (`_reconcile_capital`) only applies to investment-genre, and only warns — it doesn't correct the HUD (the comment says "Director state_updates 반영 대기").

### F-6. Reject Path Does Not Persist Any State (NON-ISSUE, but notable)

On the REJECT path, `stage4_reject_runtime.py` writes:
- Episode production logs
- Reject attempt artifacts
- Cost records
- Decision session logs

But it does **not** update WorldState, FactLedger, state_logs, HUD, or bible_delta. This is correct — rejected manuscripts should not alter world state. The reject path's `state_updates` field in `previous_attempt` (L440) is for retry guidance only, not for persistence.

### F-7. _merge_storage_only_state_change_families Merges from Three Sources (MODERATE)

`stage4_post_pass_runtime.py:70-88`:
```python
merged_state_changes = dict(base_state_changes) if isinstance(base_state_changes, dict) else {}
```
Where `base_state_changes` is `actual_truth if actual_truth else final_state_updates`.

Then it scans both `final_state_updates` and `arc_data.state_changes` for `npc_martial_state_changes` that "Stage 4 manager actual_truth does not model." This means bible_delta's `state_changes` can contain martial data from Director's `final_state_updates` or from the arc's upstream `state_changes`, mixed into Manager's `actual_truth` base — a third source of truth for one field.

---

## 3. Non-Issues

### NI-1. Emergency Manuscript Dump Path
`_write_emergency_manuscript_dump` only fires on DB save failure. Correctly bounded — doesn't create a parallel truth surface.

### NI-2. Karma Persistence Independence
`_persist_karma_status` writes to a dedicated `karma_status` table and in-memory cache. It doesn't interfere with the triple-source state split — it consumes `karma_matrix` from Manager audit, which is a well-scoped sidecar.

### NI-3. Sequential Save Recovery
The deepcopy-based rollback is a reasonable fallback when DB transactions are unavailable. The asymmetry (F-4) is an edge case, not a design flaw.

### NI-4. Reject Path Isolation
Reject path correctly does not persist state. `state_updates` in the retry snapshot is operator/retry guidance only.

### NI-5. Reader-Facing Manuscript Normalization
`_normalize_reader_facing_manuscript` strips scene headers before the final manuscript reaches DB. This is purely cosmetic and doesn't affect state truth.

### NI-6. Post-Pass Advisory Chain
`_run_post_pass_advisories` (satisfaction, pacing, NPC overexposure, cross-episode repetition, quality regression) are all read-then-write-to-sidecar operations. They don't modify the triple-source state surfaces.

---

## 4. Verdict

**mixed** — leaning toward **split-truth-heavy** for the specific surfaces examined.

Rationale:
- The PASS path's triple-source state truth (Director `final_state_updates` vs Manager `actual_truth` vs Python WorldState) is architecturally deliberate but never reconciled. Each surface serves a different downstream consumer without a single source of truth for "what happened in this episode."
- `active_pressure_vectors` are blueprint-sourced and manuscript-filtered, injected into `actual_truth` without Manager awareness — functionally clean but contributes to the split-truth surface count.
- The Manager-failure fallback silently promotes Director truth into the Manager slot with no marker.
- HUD updates precede Manager audit completion, creating a temporal window where Director and Manager truths can diverge in operator-visible state.

The single consumer-side contract that would reduce the most downstream confusion if normalized first: **the `actual_truth` / `final_state_updates` boundary.** Defining which fields belong to Director-authority vs Manager-authority, and adding a provenance marker when fallback occurs, would let downstream consumers make informed decisions about which truth surface to trust.

---

## 5. Stop

read-only lane complete; no files mutated

---

## 3-Pass Audit Record

Pass 1, structure and scope:
- Verified coverage against all three required surfaces (stage4_post_processor, stage4_post_pass_runtime, stage4_reject_runtime)
- Confirmed questions address accepted-vs-state truth divergence, active_pressure_vectors competition, and stale/over-persistent surfaces

Pass 2, evidence and consistency:
- All findings cite specific line numbers and code patterns
- F-1 triple-source split verified through three independent write paths
- F-2 pressure vector lifecycle traced end-to-end from blueprint through context_packets read-back
- F-3 fallback verified at L919 and cross-checked against `latest_state` property at project_manager.py:663

Pass 3, execution and readability:
- Findings ordered by severity
- Non-issues explicitly listed to show examined-but-clean surfaces
- Verdict includes actionable single-contract recommendation

Confidence: `93%`
Confidence gap: Missing live artifact verification (lane 4 scope) to confirm whether the triple-source split actually manifests as observable drift in real episodes. Static code analysis alone cannot determine how often Manager and Director disagree in practice.
