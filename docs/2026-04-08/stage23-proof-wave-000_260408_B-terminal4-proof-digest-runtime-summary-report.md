# Terminal 4 — Proof Digest / Runtime Summary Readiness Report

- Target project: `projects/000_260408_B/`
- Target session: `20260408_161433`
- Shutdown tag: `shutdown_final` @ `2026-04-08 16:42:30`
- Mode: evidence harvest only (no code edits, no rerun)
- Role: Terminal 4 of the Stage2/Stage3 proof-wave

## 1. What was checked

Authoritative sink under inspection:

- `projects/000_260408_B/logs/runtime_audit_summary.json`

Cross-read for parity / causation:

- `projects/000_260408/logs/runtime_audit_summary.json` (prior fresh run, baseline for deltas)
- `projects/000_260408_B/logs/session/decisions.jsonl` (9 rows) — to explain `session_decision_rows_without_attempt_key = 6`
- Presence check: `projects/000_260408_B/logs/artifacts/stage2/{arc_001,arc_002,arc_003}` — artifact directories exist

Fields specifically read inside `runtime_audit_summary.json`:

- `proof_digest.available`
- `proof_digest.status`
- `proof_digest.stages.stage2` (counts, coverage, issue_counts)
- `proof_digest.operational_metadata.status`
- `proof_digest.operational_metadata.stage2_live_session` (all coverage blocks + carryover_authority)
- `proof_digest.operational_metadata.stage3_live_session`
- `proof_digest.operational_metadata.stage4_live_session`
- `proof_digest.session_lineage`
- `proof_digest.artifacts.pass_rate_monitor_exists`
- `proof_digest.artifacts.ui_event_coverage_status`
- `contract.*` (to confirm authoritative-truth hierarchy is still correctly scoped)

## 2. Concrete evidence

### 2.1 Top-level proof digest state (this run, `000_260408_B`)

| Field | Value |
| --- | --- |
| `proof_digest.available` | `true` |
| `proof_digest.status` | `warn` |
| `proof_digest.artifacts.db_available` | `true` |
| `proof_digest.artifacts.session_decisions_exists` | `true` |
| `proof_digest.artifacts.ui_events_jsonl_exists` | `true` |
| `proof_digest.artifacts.pass_rate_monitor_exists` | `true` |
| `proof_digest.artifacts.episode_production_exists` | `false` |
| `proof_digest.artifacts.runtime_audit_jsonl_exists` | `true` |
| `proof_digest.artifacts.ui_events_db_available` | `true` |
| `proof_digest.artifacts.ui_events_count` | `371` |
| `proof_digest.artifacts.ui_event_coverage_status` | `ok` |
| `session_lineage.plain_log_token` | `20260408_161430` |
| `session_lineage.structured_session_id` | `20260408_161433` |
| `session_lineage.status` | `split_mapped` |
| `operational_metadata.status` | `ok` |
| `operational_metadata.latest_session_id` | `20260408_161433` |

### 2.2 `stages.stage2` block (this run)

| Field | Value |
| --- | --- |
| `status` | `warn` |
| `attempts_considered` | `3` |
| `complete_final_attempts` | `3` |
| `complete_lifecycle_attempts` | `0` |
| `legacy_key_attempts` | `0` |
| `session_scoped_attempts` | `3` |
| `coverage.stage_attempts` | `3` |
| `coverage.pass_rate_monitor` | `3` |
| `coverage.director_selections` | `3` |
| `coverage.episode_production` | `0` |
| `coverage.session_decisions` | `3` |
| `issue_counts.rationale_metadata_missing` | `3` |
| `issue_counts.session_decision_rows_without_attempt_key` | `6` |

### 2.3 `stage2_live_session` coverage (this run)

All six coverage axes report `present = total = 3`, `status = ok`:

- `attempt_key_coverage` → 3/3 ok
- `artifact_path_coverage` → 3/3 ok
- `selection_reason_coverage` → 3/3 ok
- `verdict_reason_coverage` → 3/3 ok
- `decision_attempt_key_coverage` → 3/3 ok
- `decision_artifact_path_coverage` → 3/3 ok

Additional populated fields:

- `attempt_count = 3`, `episode_count = 3`, `episodes = [1,2,3]`, `latest_ep = 3`
- `latest_final_verdict = "PASS"`
- `session_decision_count = 3`
- `ui_event_count = 9`
- `carryover_authority_event_count = 3`
- `latest_carryover_authority` present with:
  - `start_location`, `end_location` (arc 3 span: 화물 게이트 임시 관제 → 일반 조문객 셔틀버스 승강장)
  - `start_inventory_count = 5`, `end_inventory_count = 8`, inventory previews present
  - `start_capital = "2억원"`, `end_capital = "1억원"`
  - `start_total_assets = "2억 500만원 + 장례식장 뒷문 운영권"`, `end_total_assets = "1억 500만원 + 장례식장 운영권 일체"`
  - `start_portfolio_position`, `end_portfolio_position` fully populated
  - `investment_calc_final_total_assets = 105_000_000`, `investment_calc_final_cash = 100_000_000`
  - `semantic_carryover_keys = [relationship_rationale, growth_justification, foreshadow_anchors, continuity_checkpoints]`
  - `continuity_checkpoint_count = 3`

### 2.4 `stage3_live_session` and `stage4_live_session` (this run)

- `stage3_live_session.status = "absent"` — every count is `0`, every coverage axis is `missing`. `source_anchor_summary_count = 0`, `source_anchor_ui_event_count = 0`, `latest_source_anchor_summary = {}`.
- `stage4_live_session.status = "absent"` — all counters `0/false`, `non_exercised_reasons = []`.

Stage3/Stage4 absence is **not scored against `proof_digest.status`** in the `stages` block — `stages.stage3` / `stages.stage4` are simply not instantiated. Only `stage2` is in `proof_digest.stages`.

### 2.5 Contract section (this run)

`contract.operational_metadata_scope` is `"latest_structured_session_plus_runtime_audit_events_and_session_sinks"` — the prior run said `"latest_structured_session_plus_runtime_audit_events"`. Session sinks are now part of the declared metadata scope.

`contract.attempt_truth_authoritative = false` and `contract.proof_digest_truth_scope = "committed_persistence_only"` are unchanged — the summary is still explicitly non-authoritative for attempt truth.

### 2.6 Why `session_decision_rows_without_attempt_key = 6`

`decisions.jsonl` has exactly 9 stage2 rows, all with `session_id = 20260408_161433`:

| row | decision_type | ep_num | round_num | attempt_key populated? |
| --- | --- | --- | --- | --- |
| 1 | `arc` | 1 | 0 | no |
| 2 | `arc_final` | 1 | 1 | yes (`s2:ep1:arc1:a1:20260408_161433`) |
| 3 | `arc_design` | 0 | 0 | no |
| 4 | `arc` | 2 | 0 | no |
| 5 | `arc_final` | 2 | 1 | yes (`s2:ep2:arc2:a1:20260408_161433`) |
| 6 | `arc_design` | 0 | 0 | no |
| 7 | `arc` | 3 | 0 | no |
| 8 | `arc_final` | 3 | 1 | yes (`s2:ep3:arc3:a1:20260408_161433`) |
| 9 | `arc_design` | 0 | 0 | no |

The `6` is exactly the 3 × `arc` draft rows + 3 × `arc_design` rows. Only the 3 × `arc_final` rows carry `attempt_key` / `candidate_key` / `artifact_path` / `carryover_authority`. So the `6` is **not a regression against the 3 canonical attempts** — it is sink shape for the intermediate decision rows that never received an attempt_key in their emitter path.

### 2.7 Why `rationale_metadata_missing = 3` despite selection/verdict/fix all "ok"

All 3 `arc_final` rows have populated `selection_reason`, `verdict_reason`, `fix_scope`, `fix_scope_reasoning` (that is why the four coverage axes above report 3/3 ok). However:

- `arc_final` row for arc 1: `reason` populated, `reject_reason` populated
- `arc_final` row for arc 2: `reason = ""`, `reject_reason = ""`
- `arc_final` row for arc 3: `reason = ""`, `reject_reason = ""`

Additionally the intermediate `arc` rows for ep 2 and ep 3 carry `reason = ""`. The `issue_counts.rationale_metadata_missing = 3` matches the attempt cardinality (3), and the only rationale-family fields not fully covered by the six coverage axes are `reason` / `reject_reason` — which are blank for arcs 2 and 3 at the `arc_final` layer and blank at the intermediate `arc` layer for the same arcs. The digest appears to be counting rationale-metadata blanks at **one slot per attempt** rather than per row, which is why the number is `3` instead of `2` or `6`.

Classification: **logging gap at the emitter side of `arc_final.meta.reason` / `reject_reason`** for arcs 2 and 3. It is not a sink drift (the digest reads what is persisted) and it is not an upstream semantic failure (selection, verdict, fix_scope and carryover are all present and coherent). Operator intent was not to suppress these fields.

### 2.8 Deltas versus `projects/000_260408` (prior fresh run, baseline)

| Field | `000_260408` | `000_260408_B` |
| --- | --- | --- |
| `proof_digest.available` | `false` | `true` |
| `proof_digest.status` | `unavailable` | `warn` |
| `proof_digest.stages` | `{}` | `{stage2: {...}}` |
| `operational_metadata.stage2_live_session` | **absent block** | fully populated with 6 coverage axes + carryover authority |
| `operational_metadata_scope` in `contract` | `latest_structured_session_plus_runtime_audit_events` | `latest_structured_session_plus_runtime_audit_events_and_session_sinks` |
| `proof_digest.artifacts.pass_rate_monitor_exists` | `true` | `true` (unchanged) |
| `ui_event_coverage_status` | `ok` | `ok` (unchanged) |
| `session_lineage.status` | `split_mapped` | `split_mapped` (unchanged) |

The prior run had no stage2 block in `proof_digest.stages` at all and no `stage2_live_session` block in `operational_metadata`. This run has both, and all six coverage axes flip from non-existent to `ok` with 3/3 coverage.

## 3. Mismatches or blanks

No sink-level mismatches between `runtime_audit_summary.json` and the backing session sinks for the 3 canonical stage2 attempts:

- `stage_attempts` / `pass_rate_monitor` / `director_selections` / `session_decisions` → all `3` in the digest coverage map
- The 3 `arc_final` rows in `decisions.jsonl` all have `session_id = 20260408_161433`, matching `latest_session_id`
- Artifact directories `logs/artifacts/stage2/arc_00{1,2,3}/` exist, consistent with the `artifact_path` values recorded per row

Actual blanks that the digest is calling out:

- **B1 — `complete_lifecycle_attempts = 0`** while `complete_final_attempts = 3`. This is the lifecycle-completeness flag — stage2 arc_final arrivals are seen, but whatever "full lifecycle" the digest demands (likely a matched `arc` → `arc_final` → downstream episode_production triple, or a lifecycle completion event) is not satisfied. It does not contradict `attempts_considered = 3`; it is a stricter shape check.
- **B2 — `coverage.episode_production = 0`** and `artifacts.episode_production_exists = false`. Stage2 emits arcs, not episode_production rows; this is expected-blank for a stage2-only run, not a regression. It contributes to `complete_lifecycle_attempts = 0` being stuck at zero.
- **B3 — `rationale_metadata_missing = 3`** — `arc_final.meta.reason` and `arc_final.meta.reject_reason` are blank for arcs 2 and 3, and the intermediate `arc` rows for arcs 2 and 3 also have `meta.reason = ""`. Only arc 1 populates these.
- **B4 — `session_decision_rows_without_attempt_key = 6`** — the 3 × `arc` and 3 × `arc_design` rows. These rows' emitter does not stamp `attempt_key`; only the `arc_final` emitter does.

## 4. Gap classification

| Blank | Classification | Rationale |
| --- | --- | --- |
| B1 `complete_lifecycle_attempts = 0` | **operator-choice / not exercised** (plus partial **logging gap**) | Stage3/Stage4 absent (see Terminal 5 scope), so no downstream lifecycle rows exist to close the loop; the shape check is designed for Stage2+downstream runs, not stage2-only runs. |
| B2 `episode_production = 0` | **operator-choice / not exercised** | Expected for a stage2-only run; episode_production belongs to later stages. |
| B3 `rationale_metadata_missing = 3` | **logging gap** | Emitter for `arc_final` does not populate `meta.reason` / `meta.reject_reason` for arcs 2 and 3 (arc 1 proves the field is reachable). All other rationale fields are populated and the digest sees them. Not a sink drift, not an upstream semantic failure. |
| B4 `session_decision_rows_without_attempt_key = 6` | **logging gap** (sink shape) | The `arc` and `arc_design` rows are shape-correct per current emitter, but carry no `attempt_key`. Not a coverage failure for the canonical attempts (those are tracked via `arc_final`), but it is what the digest is pattern-matching against. |

No **upstream semantic/runtime issue** detected in the stage2 side of the digest. No **sink drift** detected — the digest numbers reconcile row-for-row with `decisions.jsonl`, and the artifact directories for arcs 1–3 are all on disk.

## 5. Concise verdict

**What is now fixed vs `projects/000_260408`:**

- `proof_digest.available` flipped from `false` → `true`; `status` from `unavailable` → `warn`. Stage2 now has a populated `stages.stage2` block and a populated `operational_metadata.stage2_live_session` block, with all six coverage axes (attempt_key, artifact_path, selection_reason, verdict_reason, decision_attempt_key, decision_artifact_path) reporting 3/3 ok. Carryover authority is now surfaced in the summary at full fidelity — arc 3 start/end locations, inventory counts/previews, capital, total assets, portfolio position, numeric investment_calc fields, and the 4 semantic_carryover_keys are all present. `operational_metadata_scope` in the contract was widened to include session sinks, matching the populated content.
- Stage2 summary-only triage is now usable for an operator: the single file answers "how many attempts, which session, what verdicts, what carryover" without DB spelunking.

**Exact root cause of current `warn`:**

- `proof_digest.stages.stage2.status = "warn"` is driven by two issue_counts, in order of importance:
  1. `rationale_metadata_missing = 3` — `arc_final.meta.reason` and `arc_final.meta.reject_reason` are blank for arcs 2 and 3 (arc 1 populates both). This is a **logging gap** at the `arc_final` emitter, not a semantic failure.
  2. `session_decision_rows_without_attempt_key = 6` — the 3 × `arc` draft rows and 3 × `arc_design` rows never receive `attempt_key`. Only `arc_final` rows do. This is a **sink-shape logging gap**, not a coverage failure for the canonical 3 attempts.
- Secondary contributors (do not alone trip `warn`, but keep `complete_lifecycle_attempts = 0`): Stage3/Stage4/`episode_production` are absent in this run, which is operator-choice (Stage2-only run, operator exited at main menu per orientation hints) rather than a runtime failure.

**Is Stage2 summary-only triage usable now?** Yes, for stage2-only runs. An operator reading `runtime_audit_summary.json` alone can reconstruct attempt count (3), episodes (1–3), verdicts (PASS), per-axis coverage (3/3 ok across six axes), latest carryover authority payload for arc 3, and session lineage (`split_mapped`, structured session id `20260408_161433`) — without touching the DB. The `warn` itself is fully explained by two logging gaps that do not invalidate the underlying stage2 truth; downgrading to `ok` requires the two `arc_final.meta.reason`/`reject_reason` blanks and the intermediate-row `attempt_key` stamping to be filled at the emitter.
