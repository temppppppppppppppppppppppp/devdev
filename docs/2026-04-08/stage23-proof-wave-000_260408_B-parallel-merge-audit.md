# Stage2 / Stage3 Proof-Wave Parallel Merge Audit (`000_260408_B`)

Date: 2026-04-08
Status: final (3-pass audited; confidence gate passed)
Canonical Path: `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
Commit State:
- Baseline Commit: `6dd7712ea9a58802221634081ba199bc872d2349`
- Baseline Dirty Summary: `dirty: broad workspace narrative/material drift plus fresh runtime artifacts under projects/000_260408_B; unrelated changes preserved`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-opus-survey-orders.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal1-stage2-carryover-authority-report.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal2-stage2-session-decision-coverage-report.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal3-stage2-pass-rate-durability-report.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal4-proof-digest-runtime-summary-report.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal5-stage3-absence-and-handoff-readiness-report.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/000_260408_B/project_data.db`
- `projects/000_260408_B/logs/runtime_audit.jsonl`
- `projects/000_260408_B/logs/runtime_audit_summary.json`
- `projects/000_260408_B/logs/pass_rate_monitor.json`
- `projects/000_260408_B/logs/session/decisions.jsonl`
- `projects/000_260408_B/logs/session/ui_events.jsonl`
- `projects/000_260408_B/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json`
- `projects/000_260408_B/logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json`
- `projects/000_260408_B/logs/artifacts/stage2/arc_003/attempt_01/final_arc__conservative.json`
Side-Effect Coverage: covered (`project_data.db`, session JSONL sinks, runtime summary, runtime audit JSONL, pass-rate monitor, Stage2 artifacts, Stage3 artifact absence, operator-exit transcript)

## 1. Intent

Merge the five-terminal proof-wave for `projects/000_260408_B`, resolve terminal-to-terminal contradictions against live workspace evidence, and promote the result into the existing Stage2 / Stage3 execution SSOTs without creating a new queue lane.

This audit is live-evidence-first. Terminal prose was treated as draft input until it matched current DB / JSONL / summary / artifact truth.

## 2. Live Evidence Snapshot

- `stage_attempts` has `3` rows, all `stage = 2`
- `director_selections` has `3` rows, all `stage = 2`
- DB `ui_events` has `3` `carryover_authority` rows and `0` `source_anchor_summary` rows
- `logs/pass_rate_monitor.json` has `total_records = 3`
- `logs/session/decisions.jsonl` has `9` Stage2 rows:
  - `3 x arc`
  - `3 x arc_final`
  - `3 x arc_design`
- all `3` `arc_final` rows carry:
  - `session_id`
  - `attempt_key`
  - `candidate_key`
  - `artifact_path`
  - `selection_reason`
  - `verdict_reason`
  - `fix_scope`
  - `fix_scope_reasoning`
  - `carryover_authority`
- `runtime_audit_summary.json` reports:
  - `proof_digest.available = true`
  - `proof_digest.status = "warn"`
  - `proof_digest.stages.stage2.status = "warn"`
  - `proof_digest.operational_metadata.stage2_live_session.status = "ok"`
  - `proof_digest.operational_metadata.stage3_live_session.status = "absent"`
  - `issue_counts.rationale_metadata_missing = 3`
  - `issue_counts.session_decision_rows_without_attempt_key = 6`
- `0_temp.txt` ends at the main menu with `Stage 2 [✅]`, `Stage 3` offered but not entered, and `Choice: 5`, followed by normal shutdown

## 3. Contradiction Resolution

### 3.1 `rationale_metadata_missing = 3`

Terminal 2 and Terminal 4 disagreed on cause. Live recheck against `modules/core/failure_analyzer.py` plus `project_data.db` resolves it:

- accepted canonical cause: `director_selections.verdict_reason = ""` on all `3` Stage2 rows while `stage_attempts.verdict_reason` and `decisions.jsonl arc_final.meta.verdict_reason` are populated
- rejected cause: blank `arc_final.meta.reason` / `meta.reject_reason` on arcs 2 and 3 is real, but it is **not** what `FailureAnalyzer._collect_sink_alignment_rationale_results()` counts for `rationale_metadata_missing`

### 3.2 Stage2 rationale blanks

Terminal 3 described several Stage2 rationale fields as source blanks. Live DB readback does not support promoting that claim:

- `stage_attempts.selection_reason` lengths: `46 / 42 / 46`
- `stage_attempts.verdict_reason` lengths: `150 / 132 / 350`
- `stage_attempts.fix_scope_reasoning` lengths: `42 / 75 / 92`

So the promoted blank is narrower:

- `director_selections.verdict_reason = ""` on `3/3`

### 3.3 Mojibake claim

Terminal 5 flagged `stage_attempts.advisory_flags` mojibake on arc 3. Live UTF-8 recheck against raw SQLite payloads found no replacement characters and no byte-level evidence of corruption. That claim is not promoted into canonical findings.

## 4. Merged Terminal Verdicts

| Terminal | Question | Canonical merged verdict |
| --- | --- | --- |
| 1 | Stage2 carryover authority parity | materially closed on the proof-critical path: `stage_attempts`, `director_selections`, DB `ui_events`, session `ui_events.jsonl`, and Stage2 artifacts now agree on the canonical carryover packet; only preview truncation remains |
| 2 | Stage2 session decision coverage | materially closed for `arc_final` proof rows; residual gap is limited to `director_selections.verdict_reason` drift and 6 intermediate decision rows without `attempt_key` |
| 3 | Stage2 pass-rate durability | closed; `stage_attempts`, `director_selections`, `pass_rate_monitor`, and disk artifacts all align at count/key/hash/verdict level |
| 4 | Proof digest / runtime summary readiness | Stage2 summary-only triage is now usable; current `warn` is real but narrowed to two residual issues rather than broad Stage2 absence |
| 5 | Stage3 absence / handoff readiness | Stage3 absence is operator-choice / not exercised; the Stage2 tail is structurally ready for Stage3 handoff, with one latent semantic asset-math tension in arc 3 |

## 5. Confirmed Runtime Upgrades

### 5.1 Stage2 proof-sink tranche is materially validated

The proof-blocking gaps from `projects/000_260408` are now closed in `projects/000_260408_B`:

- DB `ui_events` now persists `carryover_authority` (`3` rows, parity with session JSONL)
- `logs/pass_rate_monitor.json` now persists the Stage2 committed attempts (`3` rows)
- `proof_digest.available` now flips `false -> true`
- `proof_digest.stages.stage2` now exists
- `proof_digest.operational_metadata.stage2_live_session` now exists and reports `status = "ok"`
- Stage2 session proof can now be reconstructed directly from the `3` `arc_final` rows in `decisions.jsonl`

### 5.2 Stage2 summary-only triage is now practical

An operator can now answer all of the following without reopening the DB:

- latest structured session id
- Stage2 attempt count / episode coverage
- latest final verdict
- Stage2 decision / artifact coverage
- latest persisted `carryover_authority`
- whether Stage3 was exercised in the same run

### 5.3 Stage3 absence is runtime truth, not a new logging failure

All relevant layers agree:

- operator transcript ended with exit after Stage2
- `stage_attempts`, `director_selections`, `llm_calls`, and `blueprints` have `0` Stage3 rows
- `logs/artifacts/stage3/` is absent
- `proof_digest.operational_metadata.stage3_live_session.status = "absent"`

## 6. Residuals That Still Matter

### 6.1 Stage2 `warn` is now narrow

The live residuals behind `proof_digest.stages.stage2.status = "warn"` are:

1. `director_selections.verdict_reason` is blank on `3/3`
   - classification: sink drift
   - impact: drives `rationale_metadata_missing = 3`
2. `session_decision_rows_without_attempt_key = 6`
   - exact rows: `3 x arc` plus `3 x arc_design`
   - classification: logging gap on intermediate decision rows
   - impact: the canonical `arc_final` rows are still usable, but the digest keeps warning on the unlinked intermediate rows

### 6.2 Lower-tier residuals

These are real, but they are no longer proof-blocking:

- `director_selections.selected_label = ""` on `3/3`
  - classification: cosmetic sink drift
- `carryover_authority.start_inventory_preview` / `end_inventory_preview` only echo the first `3` items while counts are `5` or `8`
  - classification: bounded logging truncation, not count drift
- arc 3 `verdict_reason` still records a 48% asset-math disagreement (`2.00억` expected vs `1.05억` stated) even though verdict is `PASS`
  - classification: upstream semantic / runtime issue, not a sink problem

### 6.3 Stage3 remains verification-pending

This audit does **not** validate the landed Stage3 proof surfaces themselves, because the run never reached Stage3. It only shows:

- Stage3 absence was intentional at run time
- the upstream Stage2 handoff packet is structurally present

## 7. Execution Consequence

- promote this audit into the existing Stage2 / Stage3 execution SSOTs
- do **not** open a new queue lane
- do **not** reorder the queue from this proof wave alone
- treat the bounded Stage2 proof-sink tranche as materially validated at the proof-blocking level
- keep the residual Stage2 `warn` items as same-lane sink hygiene:
  - `director_selections.verdict_reason`
  - intermediate `arc` / `arc_design` `attempt_key` coverage
- shift the next useful proof artifact from "repair Stage2 proof sinks first" to "run a path that actually reaches Stage3"

## 8. 3-Pass Audit Record

### Pass 1. Structure and Scope

- fixed the document type as a merge audit rather than a new execution SSOT
- kept scope bounded to the fresh `000_260408_B` proof wave
- separated proof-blocking closures from residual sink hygiene and from Stage3 non-exercise

### Pass 2. Evidence and Consistency

- revalidated all five terminal outputs against live DB / JSONL / summary / artifact truth
- resolved the Terminal 2 vs Terminal 4 disagreement with direct code readback of `failure_analyzer.py`
- rejected unsupported mojibake and Stage2-source-blank claims after UTF-8 / DB rechecks

### Pass 3. Execution and Readability

- made the queue consequence explicit: existing SSOT promotion, no new lane, no reorder
- narrowed the residual Stage2 scope to two concrete `warn` drivers
- shifted the next proof recommendation to a Stage3-reaching rerun without hiding the remaining Stage2 hygiene debt

Confidence: `97%`
