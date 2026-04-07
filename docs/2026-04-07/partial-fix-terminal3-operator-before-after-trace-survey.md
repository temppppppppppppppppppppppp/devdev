# Partial-Fix Terminal 3 Operator Before/After Trace Survey

Date: 2026-04-07
Status: final
Document Type: read-only terminal survey
Canonical Path: `docs/2026-04-07/partial-fix-terminal3-operator-before-after-trace-survey.md`
Track: system
Lane: `operator-facing before/after trace / snapshot-dashboard surfaces`
Parent Order: `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 87 tracked, 71 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/; survey-only, no code or queue mutation`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

Read in this lane:

- `modules/core/stage4_interview_round.py` (focus: `_RoundOutcomeTracePayload`, `_summarize_patch_provenance`, `_append_episode_log` → `episode_production.jsonl`, `snapshot_logged_artifact` call sites for `patched_after_fix`/`final_manuscript`)
- `modules/domain/agents/chief_writer.py` (focus: `_set_last_inplace_patch_trace`, `_attempt_structural_inplace_patch`, structural patched_blocks merge)
- `modules/domain/agents/chief_writer_inplace_local_ops.py` (entire file, ~230 LOC)
- `modules/core/db_manager.py` (focus: `save_stage_attempt`, `get_latest_stage4_gate_repair_snapshot`, `stage_attempts` columns, advisory_flags packaging)
- `modules/api/bridge_server.py` (focus: `_build_gate_repair_summary`, gate_repair surface payload composition)
- `modules/core/stage4_canary_tools.py` (focus: `patch_trace_summary` consumer, `_build_stage4_gate_repair_surface_summary`)
- `modules/core/failure_analyzer.py` `patch_trace_summary` aggregator
- `modules/core/artifact_logging.py` (`snapshot_logged_artifact` and on-disk layout)
- Parent execution SSOT: `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- Stage container/PWF master survey: `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- Stage shape evidence: `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`

Intentionally excluded:

- Stage2/Stage3 partial-fix surfaces (out of lane scope; repair payloads there are instruction strings, no patch_trace dict)
- Director ensemble verdict gating internals (gate_basis is already surfaced; not a trace concern)
- Desktop UI rendering layer beyond bridge readback payload shape
- Live canary or fresh-run validation (read-only wave)

## 2. Findings

Ordered by severity for the operator-facing trace question.

1. **Operator readback exposes the contract but never the textual change.**
   `bridge_server.py:1591-1689` `_build_gate_repair_summary` returns `fix_pack`, `repair_contract`, `scope_authority`, `retry_budget_axes`, `final_verdict`, `gate_basis`, `repair_scope`, `fix_scope`, `authoritative_fix_scope`, `repair_contract_subtype`, `repair_contract_provenance`, plus authority linkage. It does **not** include any `old_text`/`new_text`/excerpt/diff/anchor/guard-result field. The operator can see "what was supposed to be fixed" but never "what actually changed in the manuscript and whether the rule held".

2. **Local-edit replace operations are produced and discarded.**
   `chief_writer_inplace_local_ops.py:74-79` returns `LocalEditAttempt(success, manuscript, state_updates, failure_reason, operation_count)`. The `operations` list (each containing `op`, `old_text`, `new_text`, `anchor_before`, `anchor_after`) is consumed by `_apply_replace_operation` and then dropped on the floor. No caller (`chief_writer.py` does not surface them either) re-attaches the operation list to the patch_trace, JSONL, DB, or any sink. This is the single biggest substrate gap for `target / old_excerpt / new_excerpt`.

3. **Structural patch loses per-block before/after pairs after merge.**
   `chief_writer.py:1495-1547` `_attempt_structural_inplace_patch` iterates `target_scene_ids`, replaces `merged_blocks[block_idx]` with `patch_text` from `patched_blocks[scene_id]`, and returns the merged manuscript plus a list of scene IDs. The pre-replace block contents are still in scope at line 1497-1505 (`merged_blocks[block_idx]` before assignment) but never captured into the trace. Boundary excerpts (`prev`, `next`) at lines 1372-1382 exist only inside the prompt builder.

4. **`_set_last_inplace_patch_trace` payload schema is intentionally narrow.**
   `chief_writer.py:1133-1150` defines exactly five fields: `patch_strategy`, `patch_targets` (list of stringified scene IDs or fix_pack targets), `fallback_reason`, `focus`, `structural_attempted`. There is no slot for an excerpt list, an operations list, a per-target outcome, or a guard_result. The same shape is then echoed verbatim into `episode_production.jsonl` at `stage4_interview_round.py:6991-6998`. So even if upstream wanted to push excerpts, the contract dict shape would silently truncate them.

5. **`do_not_regress` / `must_fix` / `success_condition` never become a runtime guard signal.**
   `stage4_interview_round.py:1979-2080` normalizes the contract and `_evaluate_fix_pack_contract` only checks **presence**, not satisfaction. The parent execution SSOT (Stage4 partial-fix hardening §2 Baseline Facts and §7 Tranche 3) explicitly notes these are "carried as contract text but not treated as first-class post-patch gates". Consequence for the operator-trace question: `guard_result` is not derivable from any current sink because no component has ever produced a per-target pass/fail decision.

6. **`why_changed` is reconstructable but not consolidated.**
   `_summarize_patch_provenance` (`stage4_interview_round.py:6694-6734`) already builds an operator-readable string from `fix_scope`, `target_kind`, `fix_scope_reasoning`, `open_review`, `compact_feedback`, `patch_targets`, `patch_strategy`, `change_ratio`. It is the closest existing substrate to a `why_changed` field. It is, however, a flat string assembled per attempt, not a per-target attribution, and it is not piped into `_append_episode_log` patch_trace dict, the DB advisory_flags, or the bridge gate_repair_summary. It currently feeds re-audit prompts and operator console lines only.

7. **Per-attempt manuscript snapshots already exist on disk and are addressable.**
   `artifact_logging.py:40-89` `snapshot_logged_artifact` writes `logs/artifacts/stage{N}/ep_{NNNN}/attempt_{NN}/{kind}__{candidate}.{txt|json}` with `content_hash` and `artifact_path`. `stage4_interview_round.py:4253-4260` and `:5564` distinguish `patched_after_fix` from `final_manuscript`, and the same `(candidate_key, content_hash, artifact_path)` triple is persisted into `stage_attempts` columns by `db_manager.save_stage_attempt` (`db_manager.py:3187-3213`). A bounded operator before/after view is therefore reachable today **as a paired-file lookup**, but no helper exposes it as paired excerpts to the bridge or canary surfaces.

8. **Aggregate surface already exists, per-episode trace surface does not.**
   `failure_analyzer.py:1858-1945` `patch_trace_summary` aggregates the last 100 episode_production rows into `strategy_counts`, `fallback_reasons`, `focus_counts`, `top_patch_targets`, `avg_unchanged_ratio`, `final_pass`, `final_reject`. `stage4_canary_tools.py:559-642` consumes that into `gate_repair_surface_summary`. So fleet-level "is patching working" is already visible. The missing thing is the **per-attempt before/after evidence surface** that an operator would open when one episode looks suspicious.

9. **Workspace TEXT-no-truncate policy already permits storing full excerpts.**
   AGENTS.md §정책 결정 사항 1 ("DB 최대 보존 정책") explicitly forbids Python-side truncation of diagnostic TEXT fields. So storing `old_excerpt` / `new_excerpt` as TEXT (with no `[:N]` slicing) is allowed and even preferred. The current inplace local-op layer does enforce span limits at `chief_writer_inplace_local_ops.py:223-230` (`entity_ref` ≤160/240, `local_phrase` ≤240/480, `local_sentence` ≤1200/1800), so the upstream excerpts are already pre-bounded and storage cost is naturally capped.

## 3. Existing Coverage Check

Already covered by ranks `9-11`:

- Stage4 partial-fix hardening SSOT §5 Class B explicitly lists "richer patch telemetry for operator comparison" as residual.
- Stage4 partial-fix hardening SSOT §7 Tranche 4 ("Patch Exhaustion and Telemetry Hardening") names "preserve target-level outcome summaries in patch traces" as a goal.
- Stage4 partial-fix hardening SSOT §7 Tranche 3 ("Post-Patch Targeted Verifier") plans to make `must_fix` / `do_not_regress` / `success_condition` executable, which is the only credible producer of `guard_result` for any future operator trace.
- Stage4 partial-fix hardening SSOT §6 Side-Effect Map line ("repair traces, fix-pack summaries, and post-check results may become richer") implicitly authorizes both the JSONL and the operator readback to gain new fields.

Only implied, not explicit:

- The text shape of any future "target-level outcome summary" — the SSOT does not say whether it would be a paired excerpt, a flat string, or a structured per-target list.
- The bridge readback path: nothing in queue ranks `9-11` says `gate_repair_summary` must be widened. Tranche 4 lives on the producer side; the readback widening is implicit at best.
- The local-op operations list capture: the SSOT names patch-address normalization and post-patch verification, not "stop dropping the operations list inside `LocalEditAttempt`".

Still missing:

- An explicit `repair_trace[]` schema spec (`target` / `old_excerpt` / `new_excerpt` / `why_changed` / `guard_result`).
- A binding clause that the same trace records are surfaced through `bridge_server._build_gate_repair_summary` so operators see them.
- A binding clause that local-edit operations are no longer dropped after `_apply_replace_operation`.
- Stage2/Stage3 are not in scope for this trace because their PWF payload is an instruction string and would not have `old_text`/`new_text` to capture.

## 4. Minimal Contract Proposal

Smallest bounded addition that still answers the operator's "before vs after, why, did the rule hold" question:

```json
{
  "repair_trace": [
    {
      "target": "string  (e.g. patch_targets[i] or scene_id)",
      "target_kind": "entity_ref|local_phrase|local_sentence|scene_block",
      "old_excerpt": "string  (no truncation; bounded by local-op span limits)",
      "new_excerpt": "string  (no truncation; bounded by local-op span limits)",
      "why_changed": "string  (compact reuse of fix_pack.must_fix[i] or _summarize_patch_provenance per-target slice)",
      "guard_result": {
        "must_fix": "satisfied|unsatisfied|unverified",
        "do_not_regress": "preserved|violated|unverified",
        "success_condition": "met|unmet|unverified"
      }
    }
  ]
}
```

Bounded placement rules:

1. **Producer side.** Extend `chief_writer._set_last_inplace_patch_trace` payload with one new key `repair_trace: list[dict]`. Local-edit path populates entries from the operations list before discarding it (`chief_writer_inplace_local_ops.py:74-79` returns the list explicitly). Structural-patch path populates entries from the pre-/post-`merged_blocks[block_idx]` pair captured at `chief_writer.py:1497-1505`.
2. **Persistence side.** `stage4_interview_round.py:6991-6998` `patch_trace` dict gains the new key as-is and is written verbatim into `episode_production.jsonl`. `stage_attempts.advisory_flags` JSON, packaged in `_append_episode_log`'s upstream `_extract_stage4_advisory_contract_payloads`, gains a parallel `repair_trace` slot under `advisory_flags`. No new DB column is required.
3. **Guard signal source.** `guard_result` defaults to `unverified` for every entry. It is upgraded to `satisfied` / `preserved` / `met` only when Tranche 3 (post-patch targeted verifier) actually runs. Until Tranche 3 lands, `repair_trace[].guard_result` always reports `unverified`. This keeps the new field honest without faking executable gating.
4. **Excerpt size policy.** Honor AGENTS.md §정책 결정 사항 1 (no Python truncation of TEXT). Rely on existing local-op span limits at `chief_writer_inplace_local_ops.py:223-230` to bound entity_ref/local_phrase/local_sentence excerpts. For structural patch entries, use the pre-existing `prev_excerpt[-220:]` / `next_excerpt[:220]` boundary slices already used at `chief_writer.py:1372-1382` for the merged-block before/after.
5. **Operator readback.** Extend `bridge_server._build_gate_repair_summary` once: pull `repair_trace` from `snapshot.get("advisory_flags", {})` (or directly from the surfaced gate snapshot if `db_manager.get_latest_stage4_gate_repair_snapshot` is widened) and add `repair_trace: []` to the returned payload. No other bridge endpoint changes.

This is intentionally one schema, two producer sites (local-op + structural), one persistence chain, one readback widening, no new DB column, and no new aggregator. It is a strict extension of Stage4 partial-fix hardening Tranche 4, sourced by Tranche 3 results when available.

## 5. Owner Verdict

Narrowest plausible owner set:

- `modules/domain/agents/chief_writer_inplace_local_ops.py` — return `operations` (or a per-op excerpt summary) on `LocalEditAttempt` instead of dropping them.
- `modules/domain/agents/chief_writer.py` — capture pre-/post-block excerpts in `_attempt_structural_inplace_patch`; widen `_set_last_inplace_patch_trace` schema with `repair_trace`.
- `modules/core/stage4_interview_round.py` — pass `repair_trace` through `_append_episode_log` patch_trace dict and through `_extract_stage4_advisory_contract_payloads` so it lands in `stage_attempts.advisory_flags`.
- `modules/core/db_manager.py` — `get_latest_stage4_gate_repair_snapshot` reads `repair_trace` out of the existing `advisory_flags` JSON; no schema change.
- `modules/api/bridge_server.py` — `_build_gate_repair_summary` adds `repair_trace` to its payload.

Out of owner scope for this lane:

- `failure_analyzer.patch_trace_summary` (aggregate; can stay unchanged)
- `stage4_canary_tools._build_stage4_gate_repair_surface_summary` (consumer of the bridge payload; cosmetic only)
- Stage2/Stage3 producers (no `old_text`/`new_text` substrate to capture)

## 6. Promotion Signal

`extend-rank9-11-stage-local-wave`

Rationale:

- Stage4 partial-fix hardening §7 Tranche 4 already owns "target-level outcome summaries in patch traces" as a goal and §7 Tranche 3 already owns the only credible producer for `guard_result`. The before/after operator trace is the missing concrete schema and the missing one-line bridge readback widening, both of which fit naturally inside the parked Stage4 lane without splitting off a new cross-stage execution lane.
- Stage2/Stage3 PWF is instruction-string only and has no analogous before/after substrate, so a "cross-stage operator trace" would be fictional outside Stage4. A separate cross-stage lane is not justified.
- The proposal does not require new DB columns, new aggregators, or new dashboards — only a schema extension on the existing producer/persistence/readback chain. That is precisely the kind of bounded extension §7 Tranche 4 contemplates.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output

## 8. 3-Pass Audit Record

Pass 1, structure and scope:

- Stayed inside the lane assigned by the parent order: operator-facing before/after trace surfaces only.
- Did not touch Stage2/Stage3 surfaces, the active queue, or any code path.
- Used the shared output contract sections (Coverage / Findings / Existing Coverage Check / Minimal Contract Proposal / Owner Verdict / Promotion Signal / Stop) and added a 3-pass audit record per AGENTS.md document save rule.

Pass 2, evidence and consistency:

- Every numbered finding cites a live file path plus a line range that was actually read in this turn.
- Cross-checked the parent Stage4 partial-fix hardening SSOT (§5 Class B and §7 Tranche 3/4) against the proposed extension before claiming `extend-rank9-11-stage-local-wave`.
- Honored AGENTS.md §정책 결정 사항 1 by explicitly forbidding Python-side truncation of the new excerpt fields and pointing at existing local-op span limits as the natural bound.
- Confirmed that the structural-patch path already has pre-/post-block content in scope at `chief_writer.py:1497-1505`, so the proposal does not assume substrate that does not exist.

Pass 3, execution and readability:

- Reduced the proposal to one schema (`repair_trace[]`), two producer sites, one persistence chain, one readback widening — small enough to slot under Stage4 partial-fix hardening Tranche 4 without reopening it.
- Made the `guard_result` upgrade path conditional on Tranche 3 so the new field is honest from day one and does not pretend to gate.
- Kept the document a survey output, not an execution doc, in line with the parent order's guardrails 4 / 5 / 6 / 7 / 11 / 12.
