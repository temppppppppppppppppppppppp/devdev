# Terminal 2 — Stage2 Session Decision Coverage

Target: `projects/000_260408_B/`
Session: `20260408_161433`
Scope: evidence harvest only, no code edits, no rerun.

## 1. What was checked

- every Stage2 row in `projects/000_260408_B/logs/session/decisions.jsonl`
  (9 rows total, all `stage="stage2"`)
- row-kind inventory and per-field coverage on `decision_type="arc_final"` rows
- cross-check against `stage_attempts` (stage=2) and `director_selections` (stage=2) in `projects/000_260408_B/project_data.db`
- cross-check against `proof_digest.stages.stage2.issue_counts` in `runtime_audit_summary.json`

Authoritative inputs:
- persisted sink — `decisions.jsonl` (9 rows)
- persisted sink — DB `stage_attempts` (3 rows, stage=2)
- persisted sink — DB `director_selections` (3 rows, stage=2)
- persisted sink — `logs/runtime_audit_summary.json` → `proof_digest.stages.stage2`

## 2. Concrete evidence

### 2.1 Row-kind inventory for stage2 in `decisions.jsonl`

| decision_type | rows | ep_num values            | result | score |
| ------------- | ---: | ------------------------ | ------ | ----- |
| `arc`         |    3 | 1, 2, 3                  | PASS   | 100   |
| `arc_final`   |    3 | 1, 2, 3                  | PASS   | 100   |
| `arc_design`  |    3 | 0, 0, 0 (arc_no=1/2/3)   | PASS   | 0     |

Total = 9 rows. This matches the orientation hint `decisions.jsonl contains 9 rows, including 3 x arc_final`.

### 2.2 `arc_final` field coverage (the proof-relevant row kind)

Checked at `meta.*` level on rows 2, 5, 8 of `decisions.jsonl`.

| field                    | arc1 (ep1) | arc2 (ep2) | arc3 (ep3) |
| ------------------------ | ---------- | ---------- | ---------- |
| `session_id`             | ✅ `20260408_161433` | ✅ `20260408_161433` | ✅ `20260408_161433` |
| `attempt_key`            | ✅ `s2:ep1:arc1:a1:20260408_161433` | ✅ `s2:ep2:arc2:a1:20260408_161433` | ✅ `s2:ep3:arc3:a1:20260408_161433` |
| `candidate_key`          | ✅ `creative`     | ✅ `creative`     | ✅ `conservative` |
| `artifact_path`          | ✅ `logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` | ✅ `.../arc_002/attempt_01/final_arc__creative.json` | ✅ `.../arc_003/attempt_01/final_arc__conservative.json` |
| `selection_reason`       | ✅ populated | ✅ populated | ✅ populated |
| `verdict_reason`         | ✅ populated | ✅ populated | ✅ populated (advisory F-1/F-2 text) |
| `fix_scope`              | ✅ `inplace` | ✅ `inplace` | ✅ `inplace` |
| `fix_scope_reasoning`    | ✅ populated | ✅ populated | ✅ populated |
| `carryover_authority`    | ✅ full packet | ✅ full packet | ✅ full packet |
| `reason`                 | ✅ populated | ⚠️ empty string | ⚠️ empty string |
| `reject_reason`          | ✅ populated | ⚠️ empty string | ⚠️ empty string |
| `failure_category`       | `""` (PASS) | `""` (PASS) | `""` (PASS) |
| `content_hash`           | ✅ present | ✅ present | ✅ present |
| `generation_method`      | ✅ `four_phase` | ✅ `four_phase` | ✅ `four_phase` |
| `selected_strategy`      | ✅ `creative` | ✅ `creative` | ✅ `conservative` |

The `carryover_authority` packet on every `arc_final` row carries start/end `location`, `inventory_count`, `inventory_preview`, `total_assets`, `capital`, `portfolio_position`, `investment_calc_final_total_assets`, `investment_calc_final_cash`, `semantic_carryover_keys`, and `continuity_checkpoint_count`. Proof can be reconstructed from `decisions.jsonl` alone for the `arc_final` kind — no DB spelunking required for those three rows.

### 2.3 `arc` and `arc_design` row coverage (the "missing attempt_key" rows)

| field                    | `arc` ×3 | `arc_design` ×3 |
| ------------------------ | -------- | --------------- |
| `session_id` (in meta)   | ❌ absent | ❌ absent |
| `attempt_key`            | ❌ absent | ❌ absent |
| `candidate_key`          | ❌ absent | ❌ absent |
| `artifact_path`          | ❌ absent | ❌ absent |
| `selection_reason`       | ❌ absent | ❌ absent |
| `verdict_reason`         | ❌ absent | ❌ absent |
| `fix_scope`              | ❌ absent | `""` empty |
| `fix_scope_reasoning`    | ❌ absent | ❌ absent |
| `carryover_authority`    | ❌ absent | ❌ absent |
| `generation_method`      | ✅ `four_phase` | ❌ absent |
| `reason`                 | ep1 ✅ populated; ep2/ep3 `""` empty | ❌ absent |
| `arc_no`                 | ❌ absent | ✅ 1/2/3 |

These 6 rows (3 `arc` + 3 `arc_design`) are the direct source of `proof_digest.stages.stage2.issue_counts.session_decision_rows_without_attempt_key = 6`.

### 2.4 Cross-check against DB `stage_attempts` (stage=2)

All three rows are present with matching keys:

| field                 | status |
| --------------------- | ------ |
| `attempt_key`         | ✅ parity with `arc_final.meta.attempt_key` (3/3) |
| `candidate_key`       | ✅ parity (3/3) |
| `artifact_path`       | ✅ parity (3/3) |
| `selection_reason`    | ✅ populated and matches `arc_final` (3/3) |
| `verdict_reason`      | ✅ populated and matches `arc_final` (3/3) |
| `fix_scope`           | ✅ `inplace` (3/3) |
| `fix_scope_reasoning` | ✅ populated and matches `arc_final` (3/3) |
| `advisory_flags.carryover_authority` | ✅ carryover packet embedded (3/3) |
| `verdict`             | PASS (3/3) |

`decisions.jsonl arc_final` and `stage_attempts` are in full parity on the fields listed in the order deliverable.

### 2.5 Cross-check against DB `director_selections` (stage=2)

Queried all 3 rows (schema columns include `selection_reason`, `verdict_reason`, `fix_scope`, `attempt_key`, `candidate_key`, `artifact_path`, `content_hash`, `advisory_warnings`, `director_thinking`, `firewall_reason`; note: there is **no** `fix_scope_reasoning` column on `director_selections`).

| field                 | arc1 | arc2 | arc3 | vs `arc_final` / `stage_attempts` |
| --------------------- | ---- | ---- | ---- | --------------------------------- |
| `attempt_key`         | ✅   | ✅   | ✅   | parity |
| `candidate_key`       | ✅   | ✅   | ✅   | parity |
| `artifact_path`       | ✅   | ✅   | ✅   | parity |
| `selection_reason`    | ✅ (46 chars) | ✅ (42) | ✅ (46) | parity |
| `verdict_reason`      | ❌ **length=0** | ❌ **length=0** | ❌ **length=0** | **drift** — populated in `arc_final` + `stage_attempts`, empty here |
| `fix_scope`           | ✅ `inplace` | ✅ `inplace` | ✅ `inplace` | parity |
| `fix_scope_reasoning` | n/a (column absent) | n/a | n/a | schema gap |
| `director_thinking`   | ❌ length=0 | ❌ length=0 | ❌ length=0 | blank |
| `firewall_reason`     | ❌ length=0 | ❌ length=0 | ❌ length=0 | blank (no firewall trip) |
| `advisory_warnings`   | ✅ `carryover_authority` packet | ✅ same | ✅ same | parity |

### 2.6 `runtime_audit_summary.json` → `proof_digest.stages.stage2` (authoritative sink)

```
status: warn
attempts_considered:        3
complete_final_attempts:    3
complete_lifecycle_attempts: 0
legacy_key_attempts:        0
session_scoped_attempts:    3
coverage:
  stage_attempts:       3
  pass_rate_monitor:    3
  director_selections:  3
  episode_production:   0
  session_decisions:    3
issue_counts:
  rationale_metadata_missing:             3
  session_decision_rows_without_attempt_key: 6
```

## 3. Mismatches or blanks

1. **`director_selections.verdict_reason` is empty on all 3 rows** while the identical fact is populated in `decisions.jsonl arc_final.meta.verdict_reason` and in `stage_attempts.verdict_reason`. The count of 3 blanks matches `issue_counts.rationale_metadata_missing = 3` exactly — this is the precise generator of the "rationale metadata missing" count and therefore a primary driver of `proof_digest.status = "warn"`.
2. **6 stage2 rows in `decisions.jsonl` lack `attempt_key`** (the 3 `arc` rows + 3 `arc_design` rows). That count matches `issue_counts.session_decision_rows_without_attempt_key = 6` exactly. These rows also lack `session_id`, `candidate_key`, `artifact_path`, `carryover_authority`. They are bare pre-final / design-layer rows and cannot be joined back to any `stage_attempts` key from `decisions.jsonl` alone.
3. `arc` rows for ep2/ep3 carry `meta.reason = ""`; only ep1 has a non-empty narrative `reason`. `arc_final` rows for arc2/arc3 also carry `meta.reason = ""` and `meta.reject_reason = ""`, while arc1 has both populated. The proof-critical fields (`verdict_reason`, `selection_reason`, `fix_scope_reasoning`) are populated for all 3 arc_final rows, so this blank is cosmetic redundancy rather than missing rationale.
4. `complete_lifecycle_attempts = 0` vs `complete_final_attempts = 3`. Every attempt has a final row but none qualifies as a "complete lifecycle" in the digest's view. This is another component of `warn` and is orthogonal to session-decision coverage per se, but is relevant because it means `decisions.jsonl` by itself is not closing whatever lifecycle shape the digest is looking for.
5. Arc3 `verdict_reason` text contains `"Major investment advisory requires at least PASS_WITH_FIX. [F-1] Arc 3: 총자산 합산 불일치. 계산 2.00억 vs 서술 1.05억 (괴리 48%)"` yet `result=PASS` / `verdict=PASS`. This is an internal narrative contradiction visible in both `decisions.jsonl` and `stage_attempts`, not a coverage gap — flagged for Terminal 1 / Terminal 4 awareness but **it is not driving** the three `rationale_metadata_missing` counts (those are the empty `director_selections.verdict_reason` blanks, as shown in 2.5).
6. `director_selections` schema has no `fix_scope_reasoning` column at all, so any triage that walks the `director_selections` side cannot recover the scope rationale without falling back to `stage_attempts` or `decisions.jsonl`.

## 4. Gap classification

| finding | classification |
| ------- | -------------- |
| `arc_final` field coverage in `decisions.jsonl` for session_id, attempt_key, candidate_key, artifact_path, selection_reason, verdict_reason, fix_scope, fix_scope_reasoning, carryover_authority | **no gap** |
| `arc_final` ↔ `stage_attempts` parity | **no gap** |
| `director_selections.verdict_reason` empty × 3 (while `stage_attempts.verdict_reason` and `decisions.jsonl arc_final.verdict_reason` are populated) | **sink drift** (persisted sinks disagree; drives `rationale_metadata_missing = 3`) |
| `director_selections` lacking `fix_scope_reasoning` column | **sink drift** (schema-level coverage gap vs `stage_attempts`) |
| 6 `decisions.jsonl` rows (`arc` + `arc_design`) with no `attempt_key` / `session_id` / `candidate_key` / `artifact_path` | **logging gap** (upstream emits these row kinds without proof-linking metadata; drives `session_decision_rows_without_attempt_key = 6`) |
| `arc_final` rows 2 and 3 with `reason=""` / `reject_reason=""` | **logging gap** (minor, redundant field; proof-critical rationale is populated in `verdict_reason` / `selection_reason` / `fix_scope_reasoning`) |
| arc3 verdict_reason narrative says "requires at least PASS_WITH_FIX" while verdict is PASS | **upstream semantic / runtime issue** (out of scope for this terminal; not a decisions.jsonl coverage problem) |

## 5. Verdict

Stage2 proof reconstruction from `decisions.jsonl` **alone is now possible** for the three `arc_final` rows: `session_id`, `attempt_key`, `candidate_key`, `artifact_path`, `selection_reason`, `verdict_reason`, `fix_scope`, `fix_scope_reasoning`, and the full `carryover_authority` packet are all present and in parity with DB `stage_attempts`. The old "DB-only spelunking" story for final decisions is closed on the `arc_final` row kind.

However, `proof_digest.status = "warn"` is being driven by two residual coverage gaps that are directly attributable to session-decision/director-selection sinks:

1. **`director_selections.verdict_reason` is empty on all three rows** → this is the exact source of `issue_counts.rationale_metadata_missing = 3`. `decisions.jsonl` and `stage_attempts` carry the verdict rationale; the director-selection sink does not. **Classification: sink drift.**
2. **`decisions.jsonl` emits 6 stage2 rows (`arc` + `arc_design`) with no `attempt_key`** → this is the exact source of `issue_counts.session_decision_rows_without_attempt_key = 6`. These rows are genuinely proof-orphan at the logging layer. **Classification: logging gap.**

So — is `proof_digest.status = "warn"` partly driven by rationale metadata still missing? **Yes, exactly half of it.** The `rationale_metadata_missing = 3` half is fully explained by empty `director_selections.verdict_reason`, not by any blank in `decisions.jsonl arc_final` or `stage_attempts`. The other half (`session_decision_rows_without_attempt_key = 6`) is explained by the `arc` and `arc_design` row kinds in `decisions.jsonl` carrying no proof-linking metadata, which is a separate logging-layer shortfall in those pre-final row kinds. No evidence of upstream semantic drift on the final-decision coverage itself.
