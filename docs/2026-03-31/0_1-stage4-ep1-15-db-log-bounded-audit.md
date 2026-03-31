# 0_1 Stage4 EP1-15 DB Log Bounded Audit

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: bounded DB/log audit
Canonical Path: `docs/2026-03-31/0_1-stage4-ep1-15-db-log-bounded-audit.md`
Temp Mirror Path: `(none - audit only)`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue, multiple dated docs/log artifacts still dirty`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Related Prior Docs:
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
- `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-bounded-survey.md`
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
Evidence Artifact:
- `docs/2026-03-31/0_1-stage4-ep1-15-db-log-bounded-audit-evidence.json`

## Answer First

`0_1` is not currently failing to ship episodes. All episodes `1-15` have:

- blueprint rows
- manuscript rows
- draft files
- at least one `stage_attempts` `PASS` row

The real problem is operational quality, not final delivery:

1. instability starts at `EP8`
2. many Stage 4 rejects are high-score provisional passes that are later blocked by downstream gates
3. the DB/log sinks are still partially misleading for chronology and final-outcome reconstruction
4. residual `npc_drift` / `flashback` strong-advisory escalations still appear after the EP9 remediation work
5. `ui_events` attribution is materially better now, but retry-lane rows still omit `attempt_key`

Smallest correct diagnosis:

- `delivery status`: working
- `runtime efficiency`: degraded from EP8 onward
- `operator observability`: improved in some sinks, still non-canonical in others

## Hard Conclusions

### 1. The pipeline ships, but Stage 4 becomes expensive and unstable from EP8 onward

Live DB evidence:

- `stage_attempts` Stage 4 rows for EP1-15: `52`
- EP1-7: `9` rows / `2` rejects
- EP8-15: `43` rows / `35` rejects
- heaviest retry clusters:
  - EP8: `9` rows across `3` sessions
  - EP9: `7` rows across `2` sessions
  - EP13: `6` rows

Live cost evidence from `llm_calls`:

- EP8: `140` Stage 4 calls / `$3.183`
- EP9: `92` Stage 4 calls / `$2.397`
- EP13: `86` Stage 4 calls / `$2.836`
- EP15: `69` Stage 4 calls / `$2.199`

This is not a terminal-break audit. It is an efficiency and diagnosis audit.

### 2. Most rejects are downstream gate failures, not low-quality writing failures

The strongest evidence is in `director_selections` plus `stage_attempts`.

Director-to-final mapping across EP1-15:

- `PASS -> PASS`: `17`
- `PASS_WITH_FIX -> PASS_WITH_FIX`: `11`
- `PASS -> REJECT`: `18`
- `PASS -> PASS_WITH_FIX`: `2`
- `REJECT -> REJECT`: `3`
- `DISMISS -> DISMISS`: `1`

Reject quality is still high:

- `stage_attempts` reject average score: `92.62`
- reject median score: `95`
- `26 / 37` rejects scored `>=95`

Dominant gate families:

- `director_primary_pass`: `17`
- `director_primary_pass_with_fix`: `11`
- `strong_advisory_escalation_non_local_fix`: `11`
- `pass_with_fix_contract_missing_patch_targets`: `7`
- `strong_advisory_escalation`: `2`
- `continuity_firewall`: `1`

Structured `runtime_audit.jsonl` also points to the same center of gravity:

- dominant pathology family: `post_select_conflict|missing_fix_pack`
- representative symptoms: high-scoring manuscript, `fix_pack_ready=false`, `missing_patch_targets`, routed to `REJECT`

This means the dominant problem is still `high-scoring provisional pass blocked downstream`, not low-score manuscript collapse.

### 3. `stage_attempts` is not a canonical chronological attempt ledger by itself

Two specific reasons:

1. `attempt_num` is reused across sessions.
2. a naive `MAX(attempt_num)` or `latest attempt_num` read can produce the wrong story.

Concrete live examples:

- EP8 has `3` distinct `session_id` values and reuses `attempt_num` `1-3`
- EP9 has `2` distinct `session_id` values and reuses `attempt_num` `1`
- duplicate `(ep_num, attempt_num)` groups:
  - EP8 attempt 1 -> `3` rows
  - EP8 attempt 2 -> `2` rows
  - EP8 attempt 3 -> `2` rows
  - EP9 attempt 1 -> `2` rows

So:

- use `attempt_key` or `ts` for chronology
- do not use `(ep_num, attempt_num)` alone as a unique attempt identity

### 4. There is still residual strong-advisory instability after EP9

Strong-advisory trigger families in `director_selections.advisory_warnings`:

- `npc_drift`: `13`
- `flashback + npc_drift`: `5`
- `flashback`: `2`

These remain visible after EP9, especially in:

- EP10 round 0
- EP13 rounds 1-3
- EP14 rounds 0 and 2
- EP15 rounds 1 and 3

The repeat pattern is still familiar:

- `Director PASS`
- strong advisory escalates
- local fix contract is not ready
- path falls into `strong_advisory_escalation_non_local_fix`

### 5. Artifact truth is mostly sound, but draft-file hash is not the canonical content hash

Verified facts:

- final `PASS` artifact file hash matches `stage_attempts.content_hash` for all EP1-15
- `manuscripts.content` hash also matches that same `content_hash`
- `drafts/ep_xxxx.txt` hash does **not** match because the draft file wraps the manuscript with an episode-title header

This is not a corruption finding. It is a sink-contract difference.

### 6. `ui_events` attribution drift is currently improved, but retry-lane linkage is still incomplete

Current live status for `projects/0_1/logs/session/ui_events.jsonl` and DB `ui_events`:

- `NULL stage`: `0`
- `NULL ep_num`: `0`
- retry-lane rows present with `stage="stage4"` and concrete `ep_num`

But:

- retry-lane rows: `9`
- retry-lane rows with `attempt_key = null`: `9`

So episode attribution is fixed, but per-attempt linkage is still missing for the retry-lane surface.

### 7. Sink schemas still drift enough to mislead simple audits

Three concrete sink issues remain:

1. `episode_production.jsonl` mixes multiple row schemas in the same file.
2. `pass_rate_monitor.json` under-reports retry depth by collapsing episodes to a single surviving record.
3. `quality_metrics.jsonl` flattens some downstream override cases into generic `director_reject` style labels without preserving gate family.

Concrete live evidence:

- `episode_production.jsonl` EP1-15 rows scanned: `107`
- rows missing `attempt_key` and `final_verdict`: `55`
- `runtime_audit.jsonl` switches between `data.ep_num` and `data.ep`
- `quality_metrics.jsonl` often lacks `round_num`, `gate_basis`, and `error_category`

This is why one sink can say:

- `Director PASS`

while another sink summarizes the same event as:

- `director_reject`

without enough context to reconstruct the override path.

## Medium-Confidence Conclusions

### 1. Upstream plan / blueprint quality is still leaking into Stage 4 repair load

The audit repeatedly found accepted manuscripts or high-scoring candidates correcting plan truth in-flight rather than simply executing it.

The cleanest direct example is `blueprint_0009.txt`, where line `7` still says `남은 5억 원` while the accepted EP9 reasoning explicitly praises the manuscript for correcting the live fact to `4억 7,100만 원`.

This does not prove blueprint quality is the main bottleneck, but it is clearly contributing to repair load.

### 2. The current observability patch has not yet shown up in persisted EP1-15 sinks

Current code in `modules/core/stage4_interview_round.py:2168-2214`, `modules/core/stage4_interview_round.py:6002-6008`, `modules/core/stage4_interview_round.py:6111-6141`, and `modules/core/stage4_interview_round.py:6185-6222` intends to persist verdict-layer metadata.

But live EP1-15 evidence shows:

- `director_selections` rows with `gate_semantics`: `52`
- `director_selections` rows with `gate_semantics.verdict_layers`: `0`
- `stage_attempts` rows with `gate_semantics.verdict_layers`: `0`
- `episode_production.jsonl` rows containing `downstream_override_applied` or `primary_failure_layer`: `0`

This is either:

- pre-patch run history, or
- a still-open runtime persistence gap

The audit cannot close that distinction without a fresh run or a smaller root-cause survey.

### 3. Prompt/context growth is not failing yet, but it is trending upward

No Stage 4 `llm_calls` errors were recorded for EP1-15.

However the max Stage 4 prompt size rose from:

- EP1: `38,473` chars
- EP8: `48,581`
- EP13: `77,601`
- EP15: `89,528`

This is not an active fault, but it is a monitor-now, ignore-later-risk.

## Improvement Priorities

### Priority 1. Make chronology and final outcome query-safe

Minimum fixes:

- treat `attempt_key` as the canonical Stage 4 attempt identity in all audits
- stop using `(ep_num, attempt_num)` as a unique attempt key
- add an explicit `episode_terminal_outcome` view or summary sink so operators do not infer closure from raw `stage_attempts`
- normalize `episode_production` row schemas or split pathology/streak rows into a different sink
- stop collapsing retry history into a single surviving `pass_rate_monitor` record when audit depth matters

### Priority 2. Close the verdict-layer persistence gap

The current code intends to expose:

- `director_quality_passed`
- `downstream_override_applied`
- `primary_failure_layer`

But none of those fields are visible in the live EP1-15 persisted sinks.

This should be treated as a bounded observability root-cause audit, not as a speculative code tweak.

### Priority 3. Keep reducing `npc_drift` / `flashback` strong-advisory churn

Residual strong-advisory escalations still consume expensive retry budget in EP10 and EP13-15.

The remaining question is no longer "does this family exist?" but:

- true positive?
- false positive?
- valid non-local escalation?
- missing local fix contract?

That needs a narrower follow-up survey if closure matters.

### Priority 4. Add `attempt_key` to retry-lane UI events

`stage` and `ep_num` attribution are now present, which is good.

The next observability step is simple:

- add `attempt_key` to retry-lane policy/advisory rows
- keep CoVe parse failures and rationale-elision notices visible in operator-facing sinks, not only runtime audit

That will make per-attempt diagnosis materially easier.

### Priority 5. Reduce upstream plan-truth leakage

The system is still spending Stage 4 budget on self-correcting plan or carryover truth.

The next upstream ROI target is:

- blueprint carryover validation
- numeric carryover validation
- role/title carryover validation

before Stage 4 spends retry budget fixing them.

## Opus Trigger

A deeper `Opus` bounded survey is justified only if the user wants closure on one of these two residual questions:

1. why live persisted EP1-15 sinks still do not show `verdict_layers` even though current code says they should
2. why `npc_drift` / `flashback` strong-advisory escalations still recur in EP10 and EP13-15 after the EP9 remediation wave

If the goal is just operator diagnosis, this audit is enough. If the goal is another patch wave, an Opus survey is warranted first.

## Pass Ledger

### Pass 1

- inventoried live DB tables, JSONL logs, artifact folders, drafts, and manuscripts for EP1-15
- separated artifact truth from operator-sink truth

### Pass 2

- grouped findings into delivery, downstream gate behavior, chronology integrity, and observability integrity
- cross-checked DB evidence with artifact hashes and UI/log sinks

### Pass 3

- rechecked encoding-sensitive claims with explicit UTF-8 decode
- refused to treat console mojibake as file corruption
- kept unresolved items explicitly open instead of over-claiming closure

## Confidence

Confidence: `96%`

The remaining uncertainty is narrow:

- verdict-layer persistence gap root cause
- exact residual truth status of late `npc_drift` / `flashback` advisories
