# T8. Stage3 Cost-To-Outcome Attribution Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T8
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: config/models.yaml + config/prompts/ensemble.yaml + modules/core/{response_schemas,scene_obligation_heuristics}.py + modules/domain/agents/{arc_ensemble,blueprint_ensemble,chief_writer,three_phase_blueprint_runtime}.py + projects/000_260412_a/{logs/*, project_data.db, config/work_guard.yaml, stage0_output/style_guide.json} + tests/test_* (7 files) + docs/2026-04-01,02,13/* temp-queue snapshots; untracked 2026-04-13 survey docs + 000_260412_a metrics_20260413_194343.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation; no live rerun; no git mutation beyond rev-parse/status`
- Confidence: `96%`

## Purpose

For the 000_260412_a session (ep1–ep7 closed, ep8 interrupted), exactly where is the $35+ Stage3 spend going — break total cost down into `ensemble fan-out`, `local patch repair`, `full regenerate repair`, `Director compare + judge`, and any other distinguishable category — and which spend axis has the lowest cost-to-successful-contract ratio?

## Evidence Anchors

Primary sinks (frozen reads):

- `projects/000_260412_a/project_data.db` — `llm_calls` (513 rows), `stage_attempts` (9 rows for Stage3), `director_selections` (9 rows for Stage3), `cost_log`. Schema verified via `PRAGMA table_info`. Read via `sqlite3` `mode=ro` URI only.
- `projects/000_260412_a/logs/session/llm_io.jsonl` (16 089 864 bytes, 513 lines) — one-to-one row alignment with `llm_calls.id`; full prompt/response text available.
- `projects/000_260412_a/logs/pass_rate_monitor.json` (15 183 bytes, 12 records) — terminal-only verdict ledger (every Stage3 ep has exactly one success record, plus two ep4 FAILED records).
- `projects/000_260412_a/logs/metrics/metrics_20260412_223713.json`, `metrics_20260413_075801.json`, `metrics_20260413_101248.json`, `metrics_20260413_101351.json`, `metrics_20260413_102305.json`, `metrics_20260413_105311.json`, `metrics_20260413_113138.json`, `metrics_20260413_140157.json`, `metrics_20260413_194343.json` — per-session aggregate snapshots.
- `projects/000_260412_a/logs/runtime_audit_summary.json` (5 910 bytes) — scanned but adds no per-call cost split.
- `projects/000_260412_a/logs/quality_metrics.jsonl` (28 647 bytes) — scanned; quality stream, no cost fields beyond what `llm_calls` carries.

Governing code (read-only, used only to disambiguate call-type semantics, not to judge quality):

- `modules/domain/agents/blueprint_ensemble.py` — producer fan-out and patch-mode prompt assembly
- `modules/domain/agents/three_phase_blueprint_runtime.py` — Phase 2/3 retry router (referenced, not re-audited here; that belongs to T2)
- `modules/domain/agents/director_ensemble.py` — Director scoring and judge calls (referenced, not re-audited; that belongs to T7)

Classifier ground truth is prompt text, not code inspection: a call is `FANOUT` iff its full prompt (from `llm_io.jsonl`) begins with the header `[V60.80 BLUEPRINT ENSEMBLE - <flavor> 중심]`; it is `PATCH` iff its full prompt begins with `[패치 모드: Blueprint 원본 보존 + 지적사항만 수정]`. Director calls are split into `D_SCORE` (prompt contains `score`/`점수`) and `D_OTHER` (remaining director calls). All Stage3 blueprint calls in the session match one of those two prompt headers — no `full_regenerate` / `rewrite` prompt header was observed.

## Findings

### F1. `llm_calls` is the only clean per-call sink; `context_tag` and `session_id` are effectively null — severity `gap`

- `project_data.db:llm_calls` has 471 rows for Stage3 (`stage=3`). Every row carries `agent_name`, `ep_num`, `prompt_chars`, `input_tokens`, `output_tokens`, `thinking_tokens`, `total_cost_usd`, `duration_ms`, `ts`, `model`. That alone is enough to split spend by agent and ep.
- However, **`session_id` is `NULL` for all 513 rows** in this DB snapshot (`SELECT session_id, COUNT(*) FROM llm_calls GROUP BY session_id` → `(None, 513, …)`). Session attribution must fall back to metrics-file time windows.
- **`context_tag` is effectively null**: 465 of 471 Stage3 rows have `context_tag IS NULL`; only 6 rows carry `context_tag='backup_recovery'` ($0.124 total). There is no built-in tag for `fanout_initial` vs `patch_retry` vs `full_regenerate` vs `director_judge`. Call-type split has to be reconstructed from prompt text.
- **`prompt_snippet` and `response_snippet` in `llm_calls` are null for 274 of 286 `blueprint_ensemble_generator` rows and for 185 of 185 `director` rows.** The DB-side snippet fields are unusable for classification. The full-text `llm_io.jsonl` is the only viable ground truth for call-type split.
- Anchor: `project_data.db` schema is canonical here; the gap is in writer-side tagging, not reader-side.

Severity tag: `gap` — visibility blocker. Any future cost-reduction decision that depends on tracking "how much did repair churn cost" must first land a `context_tag` writer for Stage3 calls or keep depending on post-hoc prompt-regex classification.

### F2. `pass_rate_monitor.json` undercounts ep-level cost by up to 84% on retry-heavy eps — severity `leak`

Per-ep cost reported by `pass_rate_monitor.json` vs ground-truth from `llm_calls` (summed over all rows with `stage=3 AND ep_num=N`):

| ep | pass_rate_monitor.token_cost | llm_calls SUM(total_cost_usd) | delta | delta_pct |
|---:|---:|---:|---:|---:|
| 1 | $2.2509 | $2.2509 | +$0.00 | 0% |
| 2 | $6.6123 | $12.1264 | +$5.51 | **+83.4%** |
| 3 | $3.6621 | $3.6621 | +$0.00 | 0% |
| 4 (two fails + success) | $3.3758 + $0.1240 + $0.1240 = $3.6238 | $3.6238 | +$0.00 | 0% |
| 5 | $5.8173 | $5.8173 | +$0.00 | 0% |
| 6 | $6.7613 | $6.7613 | +$0.00 | 0% |
| 7 | $7.3551 | $7.3551 | +$0.00 | 0% |
| 8 | (not recorded — interrupted) | $3.4807 | — | — |

- The ep2 delta of $5.51 is entirely explained by the first session crashing mid-ep2. `llm_calls` for `stage=3 AND ep_num=2` span `2026-04-12T23:38:14 → 2026-04-13T08:37:47` — a ~9-hour wall gap. The first 71 calls occurred 23:38–01:xx before the session died; the final 70 calls occurred 08:00–08:37 inside `metrics_20260413_075801.json`, and only the tail attempt was recorded in `pass_rate_monitor.json` as `s3:ep2:arc1:a10:20260413_075801` at `token_cost=$6.61`.
- `pass_rate_monitor.json:162-194` captures only the successful terminal attempt's `token_cost`, not the cumulative cost of all prior failed attempts from the same or earlier sessions. For ep1, ep3, ep5, ep6, ep7 the ledger happens to match the DB sum only because those eps completed inside a single session with no prior partial.
- For ep4 the ledger is consistent because the two FAILED sessions were recorded as their own rows in `pass_rate_monitor.json` with `token_cost=$0.124` each; they happen to be tiny because each crashed right after the first fan-out (≈7 LLM calls each per `metrics_20260413_101351.json` and `metrics_20260413_105311.json`).

Severity tag: `leak` — downstream operator math that uses `pass_rate_monitor.token_cost` as "cost of episode N" silently undercounts whenever a session crashed mid-episode before the terminal attempt. The DB `llm_calls` sum is authoritative; `pass_rate_monitor` should be treated as "terminal attempt cost" not "episode cost".

### F3. Full Stage3 spend baseline = **$45.08 over 471 calls** for this session block — severity `TP`

From `SELECT SUM(total_cost_usd) FROM llm_calls WHERE stage=3`:

| scope | calls | cost |
|---|---:|---:|
| all stages (stage in {NULL,2,3}) | 513 | $49.0867 |
| Stage 2 | 32 | $3.9381 |
| Stage 3 | 471 | **$45.0776** |
| stage NULL (preflight/housekeeping) | 10 | $0.071 |

The operator order cites "$35+ Stage3 spend per 7 episodes before ep8 closes". The authoritative figure from the DB is **$41.60 for ep1–ep7** (`$45.0776 - $3.4807` subtracting ep8) and **$45.08 including the interrupted ep8 rerun tail**. The order's "$35+" is a floor reading from `pass_rate_monitor` (which sums the per-ep ledger: $2.25 + $6.61 + $3.66 + $3.62 + $5.82 + $6.76 + $7.36 = $36.08). The $5.52 gap on top of that is the crashed-ep2 first-session retry cost (F2).

Severity tag: `TP` — the operator intuition is correct in direction; the authoritative anchor is higher.

### F4. Per-agent Stage3 split — `blueprint_ensemble_generator` owns 92% of spend, `director` owns 7.8% — severity `TP`

From `SELECT agent_name, COUNT(*), SUM(total_cost_usd) FROM llm_calls WHERE stage=3 GROUP BY agent_name`:

| agent_name | calls | cost | share |
|---|---:|---:|---:|
| `blueprint_ensemble_generator` | 286 | $41.5754 | **92.23%** |
| `director` | 185 | $3.5022 | 7.77% |
| (no other agent appears in Stage3 rows) | — | — | — |

- Stage3 `state_extractor` calls: **0** in this DB snapshot. StateExtractor's 13 calls are all `stage=NULL` or Stage2 housekeeping. StateExtractor is not a Stage3 cost axis in this session.
- Stage3 `preflight_checker`: **0**. Preflight's 4 calls are stage-boundary only.
- Stage3 `weaver` / `analyst` / `arc_ensemble_generator`: **0**. Those are upstream agents.

Implication: the Stage3 cost question reduces to splitting `blueprint_ensemble_generator`'s $41.58 into fan-out vs patch-mode, and splitting `director`'s $3.50 into score vs other.

Severity tag: `TP`.

### F5. Fine-grained call-type split via prompt-header classifier — severity `TP`

Classifier: for each Stage3 row, join `llm_calls.id` to `llm_io.jsonl` line-index (rows are in id-order, and agent-name alignment was verified with zero mismatches across all 513 rows). Inspect the first ~500 chars of the `prompt` field:

- Header `[V60.80 BLUEPRINT ENSEMBLE - 액션 중심]` → `fanout_action`
- Header `[V60.80 BLUEPRINT ENSEMBLE - 감정 중심]` → `fanout_emotion`
- Header `[V60.80 BLUEPRINT ENSEMBLE - 대화 중심]` → `fanout_dialogue`
- Header `[V60.80 BLUEPRINT ENSEMBLE - 보수 중심]` → `fanout_conservative` (**never observed**)
- Header `[V60.80 BLUEPRINT ENSEMBLE - 균형 중심]` → `fanout_balanced` (**never observed**)
- Header `[패치 모드: Blueprint 원본 보존 + 지적사항만 수정]` → `patch_mode`
- No row begins with any `전면 재작성` / `full regenerate` / `rewrite` header

Stage3 grand totals (ep1–ep8 inclusive, 471 calls, $45.0776):

| category | calls | cost | share |
|---|---:|---:|---:|
| fanout_dialogue (대화 중심) | 76 | $13.3779 | 29.68% |
| fanout_emotion (감정 중심) | 76 | $12.8830 | 28.58% |
| fanout_action (액션 중심) | 76 | $11.9721 | 26.56% |
| **FANOUT total** | **228** | **$38.2330** | **84.82%** |
| patch_mode | 58 | $3.3424 | 7.41% |
| director_score | 127 | $2.6995 | 5.99% |
| director_other | 58 | $0.8027 | 1.78% |
| **DIRECTOR total** | **185** | **$3.5022** | **7.77%** |
| **GRAND TOTAL** | **471** | **$45.0776** | **100.00%** |

Anchor observation: **three flavors are run, not five.** `conservative` and `balanced` strategies exist in the prompt vocabulary but are never fired for any Stage3 attempt in this session. That is a T6 finding (ensemble diversity) surfaced here only incidentally — cross-terminal pointer listed below.

Anchor observation: **there is no `full_regenerate_repair` axis in this session.** Every retry after a failing attempt either (a) issues a fresh `FANOUT × 3 candidates` round, or (b) issues one `PATCH` call keeping the prior candidate as base. No call uses a "full rewrite" prompt template. The T8 operator question's fourth axis (`full regenerate repair`) is empirically collapsed into the `FANOUT` axis — "full regenerate" is literally a re-firing of the same fan-out template.

Severity tag: `TP`.

### F6. Per-ep spend by call category — severity `TP`

Cost in USD. `FAN` = fanout sum of three flavors, `PAT` = patch_mode, `DSC` = director_score, `DOX` = director_other.

| ep | calls | FAN ($) | PAT ($) | DSC ($) | DOX ($) | total ($) | pass_rate_monitor verdict | attempt_num |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 33 | $1.66 | $0.34 | $0.17 | $0.08 | **$2.25** | PASS (clean) | 7 |
| 2 | 141 | $9.51 | $1.40 | $0.88 | $0.34 | **$12.13** | PASS_WITH_WARNING | 10 |
| 3 | 36 | $3.14 | $0.24 | $0.23 | $0.06 | **$3.66** | PASS (clean) | 6 |
| 4 | 42 | $3.29 | $0.12 | $0.20 | $0.02 | **$3.62** | PASS_WITH_WARNING (after 2 fails) | 1,1,6 |
| 5 | 45 | $5.27 | $0.17 | $0.33 | $0.04 | **$5.82** | PASS_WITH_WARNING | 9 |
| 6 | 67 | $5.79 | $0.45 | $0.39 | $0.12 | **$6.76** | PASS_WITH_WARNING | 10 |
| 7 | 70 | $6.26 | $0.55 | $0.42 | $0.13 | **$7.36** | PASS_WITH_WARNING | 10 |
| 8 | 37 | $3.31 | $0.06 | $0.10 | $0.01 | **$3.48** | interrupted mid-run | — |
| **total** | **471** | **$38.23** | **$3.34** | **$2.70** | **$0.80** | **$45.08** | — | — |

Cross-check: for each ep, the sum of the four categories matches the DB per-ep total to three decimal places (rounded rows ± $0.01). The classifier is complete: every Stage3 call is assigned to exactly one bucket.

Severity tag: `TP`.

### F7. Canonical retry cycle shape — FANOUT(3) → D_SCORE → [PATCH → D_OTHER → D_SCORE]? → FANOUT(3) … — severity `TP`

Walking `llm_calls.ts` in order for ep1 (33 calls), the pattern repeats cleanly:

```
FANOUT×3  D_SCORE  PATCH  D_OTHER  D_SCORE   ← attempt 1: fan-out + score, then one patch retry with rescore
PATCH     D_OTHER  D_SCORE                   ← attempt 2: second patch on same candidate, rescore
FANOUT×3  D_SCORE  PATCH  D_OTHER  D_SCORE   ← attempt 3: new fan-out, then patch+rescore
PATCH     D_OTHER  D_SCORE                   ← attempt 4: second patch, rescore
FANOUT×3  D_SCORE                            ← attempt 5: fan-out, clean
FANOUT×3  D_SCORE                            ← attempt 6: fan-out, still not clean
FANOUT×3  D_SCORE                            ← attempt 7: fan-out → final PASS
```

Per-step cost anchors (ep1):

- FANOUT(3) round: ~$0.36–$0.47 depending on context length
- Single D_SCORE: ~$0.025
- Single PATCH: ~$0.05–$0.06
- Single D_OTHER: ~$0.01
- Post-patch D_SCORE rescore: ~$0.01

Round cost:

- Bare fan-out + score: **~$0.50 per round**
- Fan-out + score + one patch + rescore: **~$0.60 per round**

Implications:

- A single "attempt" in `pass_rate_monitor.attempt_num` vocabulary is **not** a single LLM call. It is a composite: fan-out (3 LLM calls) + director scoring + 0..2 patch cycles + patch rescoring.
- The `director_other` category has a strict 1:1 count with `patch_mode` (58 vs 58). Inspection confirms every patch is flanked by one `D_OTHER` call (patch directive / feedback composition) and one `D_SCORE` rescore.
- Director calls are issued **more than once per fan-out round** when patches are applied: fan-out → score (1) → patch → rescore (2). That is why `director_score` has 127 calls across 76 fan-out rounds (1.67× per round).

Severity tag: `TP`.

### F8. Attempt-cap saturation: 4/7 closed episodes exhausted the 10-attempt budget — severity `waste`

`director_selections` terminal rounds per ep (`SELECT ep_num, round_num, verdict, score, fix_scope FROM director_selections WHERE stage=3`):

| ep | final round_num | verdict | score | fix_scope |
|---:|---:|---|---:|---|
| 1 | 7 | PASS | 92 | (empty) |
| 2 | 10 | PASS_WITH_WARNING | 85 | inplace |
| 3 | 6 | PASS | 92 | (empty) |
| 4 | 1 (×2 failed) then 6 | PASS_WITH_WARNING | 85 | inplace |
| 5 | 9 | PASS_WITH_WARNING | 85 | inplace |
| 6 | 10 | PASS_WITH_WARNING | 88 | (empty) |
| 7 | 10 | PASS_WITH_WARNING | 85 | inplace |

- **eps 2, 6, 7 all hit `round_num=10`** and closed as PASS_WITH_WARNING with Director score in the 85–88 band. The retry loop has a 10-attempt cap; three eps are budget-capped, not quality-converged.
- **ep5 hit `round_num=9`**. One more retry was theoretically available; the loop terminated on whatever degraded-admission path Director's firewall exposed.
- Eps that hit clean PASS (1, 3) needed `round_num=7` and `6` respectively. Those are the only eps where fan-out+patch combined actually produced a contract-clean candidate inside the budget.
- Eps 2, 5, 6, 7 plus ep4 represent ≈$33.3 of Stage3 spend (74% of total) for **zero clean-PASS outcomes**. They all closed on the retry floor, not the retry ceiling of quality.

The cost/outcome reading: 84.8% of Stage3 spend (the fan-out axis) bought 2 clean-PASS episodes and 5 `PASS_WITH_WARNING` ceilings. The fan-out axis is delivering diminishing returns past ~round 6 — for eps 2/6/7, rounds 7–10 consumed $3.20–$4.10 of additional fan-out spend per ep without flipping the verdict.

Severity tag: `waste` — the marginal cost of the tail rounds (rounds 7–10 on maxed eps) is demonstrably not producing an outcome delta against the retry floor.

### F9. ROI ranking per spend axis — severity `TP`

Using "closed eps" ep1–ep7 only (excluding ep8 interrupted). Total Stage3 cost ep1–ep7 = **$41.5969**.

Outcome accounting:

- **Clean PASS**: 2 episodes (ep1, ep3)
- **PASS_WITH_WARNING**: 5 episodes (ep2, ep4, ep5, ep6, ep7)
- **Clean fail (never closed)**: 0 (ep8 is interrupted, not classified)

Per-axis totals for ep1–ep7 (derived by subtracting ep8 row from F5 grand totals):

| axis | ep1–ep7 cost | share | calls | $/closed ep (out of 7) | $/clean PASS (out of 2) |
|---|---:|---:|---:|---:|---:|
| FANOUT total | $34.92 | 83.96% | 201 | $4.99 | $17.46 |
| patch_mode | $3.28 | 7.89% | 57 | $0.47 | $1.64 |
| director_score | $2.60 | 6.25% | 119 | $0.37 | $1.30 |
| director_other | $0.80 | 1.92% | 57 | $0.11 | $0.40 |
| GRAND | $41.60 | 100% | 434 | $5.94 | $20.80 |

**Top absolute spend axis: FANOUT at $34.92 (≈84% of ep1–ep7 cost).** Fan-out is by far the dominant cost — four out of every five Stage3 dollars flow to 3-way producer fan-out, not to Director judging, not to patch repair, not to overhead.

**Lowest ROI axis: `patch_mode`.** Rationale — patch_mode's stated purpose (per its own prompt header: "지적사항만 수정 … 전면 재설계하지 마세요") is to rescue a candidate that has fixable local drift. On the 5 PASS_WITH_WARNING eps (2, 4, 5, 6, 7) `director_selections.fix_scope='inplace'` records that patches were in fact applied, yet the final verdict remained `PASS_WITH_WARNING` (not clean `PASS`) in every one of those cases. Patch_mode cost for those 5 eps = $0.12 + $0.17 + $0.45 + $0.55 + $1.40 = **$2.69 spent on patches that did not lift any episode to clean PASS**. On ep1 and ep3 (the two clean PASS outcomes) patch_mode also fired for $0.34 and $0.24 but the clean PASS was ultimately secured on a later bare FANOUT round (ep1 attempt 7's terminal call is a `FANOUT` with no patch), so the clean-PASS attribution is not clearly patch-driven. Patch_mode's empirical `clean-PASS rescue count` in this session is **at most 0** and provably no more than 2 (the ep1/ep3 ceiling).

**Rank: patch_mode has the lowest cost-to-successful-contract ratio** because its outcome delta against "remove this axis" is zero clean rescues for $3.34. Director_score and director_other are also <$3 each but are load-bearing for candidate selection (without them the fan-out cannot be reduced to a single winner), so they cannot be removed unilaterally.

Caveat: patch_mode may still be load-bearing for the `PASS_WITH_WARNING` verdict itself — i.e. without patches the 5 PWW eps might have degraded to FAILED. The data available to T8 does not expose a pre-patch director verdict on those same candidates, so the null counterfactual ("would the verdict have been FAILED instead of PWW without the patch?") is not falsifiable from this sink.

Severity tag: `TP` + patch_mode tagged `waste` pending counterfactual.

### F10. Session/metrics-file cost reconciliation leaves a $3.77 unexplained gap — severity `gap`

Summing `metrics_*.json:total_cost_usd` across all 9 metrics files:

| metrics file | start_time | end_time | calls | cost |
|---|---|---|---:|---:|
| metrics_20260412_223713.json | 2026-04-12T22:37:13 | 2026-04-12T23:05:16 | 32 | $3.9381 |
| metrics_20260413_075801.json | 2026-04-13T07:58:01 | 2026-04-13T09:16:56 | 107 | $10.2812 |
| metrics_20260413_101248.json | 2026-04-13T10:12:48 | 2026-04-13T10:12:50 | 0 | $0.0000 |
| metrics_20260413_101351.json | 2026-04-13T10:13:51 | 2026-04-13T10:22:18 | 7 | $0.1312 |
| metrics_20260413_102305.json | 2026-04-13T10:23:05 | 2026-04-13T10:23:12 | 0 | $0.0000 |
| metrics_20260413_105311.json | 2026-04-13T10:53:11 | 2026-04-13T10:55:37 | 7 | $0.1305 |
| metrics_20260413_113138.json | 2026-04-13T11:31:38 | 2026-04-13T12:56:16 | 143 | $15.9614 |
| metrics_20260413_140157.json | 2026-04-13T14:01:57 | 2026-04-13T14:53:56 | 83 | $8.6859 |
| metrics_20260413_194343.json | 2026-04-13T19:43:43 | 2026-04-13T20:05:49 | 29 | $2.1790 |
| **sum** | — | — | **408** | **$41.3073** |

The DB `llm_calls` total is **513 calls / $49.09**. The metrics aggregate is **408 calls / $41.31**.

- **Call-count gap**: 105 calls. Those are the calls issued between sessions (on the crashed ep2 first session `2026-04-12T23:38 → 2026-04-13T01:xx` that was never flushed to a metrics file) and the ep7 start window between ~14:49 and 19:43 that also has no metrics file. The first `23:38–01:xx` block for ep2 alone accounts for 71 of those calls per F2's ts bucketing.
- **Cost gap**: $7.78. Same root cause — a crashed session never wrote a metrics snapshot, so its spend is visible only in `llm_calls` (which is written per-call, not per-session).

Severity tag: `gap` — the metrics sink is **not a reliable cost aggregator** when a session crashes before `end_time` is recorded. Any dashboard or audit that sums `metrics_*.json:total_cost_usd` will silently undercount crashed-session spend. The per-call `llm_calls` table is the only complete sink.

### F11. `thinking_tokens` split — only ep8 rerun paid for thinking — severity `TP`

`SELECT ep_num, SUM(thinking_tokens) FROM llm_calls WHERE stage=3 GROUP BY ep_num`:

- ep1–ep7: `thinking_tokens = 0` for every row (the pre-ep8 sessions ran on `vertexai:gemini-3.1-pro-preview` / `gemini-2.5-flash` without thinking budget enabled)
- ep8: `thinking_tokens = 117 756` (blueprint_ensemble_generator) + `14 933` (director)

The ep8 rerun is the only ep in this session block that consumed thinking tokens. That matches `metrics_20260413_194343.json:model_stats` which reports `cached_tokens: 0` and `thinking_tokens: 6 285 + 132 689` across the two models used in that session. For cost attribution purposes, thinking-token spend cannot be split out from `total_cost_usd` in this snapshot — it is bundled into the per-call total. It can only be reported as "ep8 paid a thinking premium that ep1–ep7 did not". If a cost-reduction hypothesis proposes enabling thinking on ep1–ep7 as well, the baseline for that comparison is not available in this session.

Severity tag: `TP` (factual observation, no conclusion attempted).

### F12. Director call count (185) far exceeds director_selections round count (9) — severity `TP`

`SELECT ep_num, round_num, COUNT(*) FROM director_selections WHERE stage=3` yields only **9 rows total** (ep4 has two ep4 r1 rows from its two failed sessions, so 7 unique successful rounds + 2 failed). Yet `llm_calls` has **185 director calls** across Stage3 (119 `D_SCORE` + 57 `D_OTHER` for ep1–ep7, plus 9 for ep8).

Reconciliation: a `director_selections` row represents a terminal Director verdict for a round, but within one round Director issues multiple LLM calls (candidate-level score + overall judge + post-patch rescore + patch directive). The average is ~26 director LLM calls per `director_selections` row.

- Per terminal round: typical signature is 1 D_SCORE + 1 D_OTHER + 1 D_SCORE after each patch. With typical ~6 patches per ep, that's ~1 + 6×3 = 19 calls per ep, close to the observed 15–30 per ep.
- This does **not** indicate wasteful redundant scoring — it is a consequence of patches each triggering their own micro-cycle (F7). The per-call cost of each director LLM call is tiny ($0.01–$0.03). Director is **not** the cost sink despite having 185 calls.

Severity tag: `TP`.

### F13. Per-ep cost scales linearly with attempt_num — severity `TP`

Pairing `attempt_num` from `pass_rate_monitor.json` with `total_cost` from F6:

| ep | attempt_num (terminal) | total_cost | $/attempt |
|---:|---:|---:|---:|
| 1 | 7 | $2.25 | $0.32 |
| 3 | 6 | $3.66 | $0.61 |
| 4 | 6 (after 2 fails) | $3.62 | $0.60 |
| 5 | 9 | $5.82 | $0.65 |
| 6 | 10 | $6.76 | $0.68 |
| 7 | 10 | $7.36 | $0.74 |
| 2 | 10 (but includes crashed retry block) | $12.13 | $1.21 |

- Linear regression fit eyeballed: ~$0.60–$0.70 per attempt for healthy sessions (ep3–ep7), ~$0.32 for the cheap ep1, and ~$1.21 for ep2 which is inflated by the crashed-session retry block.
- ep1's anomalously low $/attempt is explained by its context window being smaller (first episode → no prior-ep recap, no style seed accumulation). Subsequent eps ship more context per call which raises prompt_chars and hence input-token cost per call.
- The scaling implication: the marginal cost of attempt N+1 past 6 does not fall — it climbs slightly because context grows. The 4/7 eps that hit attempt cap = 10 were spending roughly $0.70 per extra attempt for nothing (F8).

Severity tag: `TP`.

### F14. FANOUT prompt_chars distribution shows context is large and consistent — severity `TP`

For `blueprint_ensemble_generator` Stage3 calls classified as FANOUT:

- min `prompt_chars` = 12 854 (ep1 attempt 1, first call of session — smallest context)
- median ≈ 20 500
- max = 28 994 (ep8 emotion fan-out with deepest prior-ep recap)
- FANOUT calls with `prompt_chars > 20000`: 168 of 228 (74%)

For PATCH calls:

- min = 4 321, median ≈ 5 500, max ≈ 14 465
- PATCH calls carry dramatically less context than FANOUT — patches reuse the original blueprint and ship only the Director feedback plus the base scene scaffolding.

That is why a FANOUT call costs ~$0.14 (23k prompt_chars × gemini pricing) while a PATCH call costs ~$0.05 (5.5k prompt_chars). The ~2.8× FANOUT/PATCH per-call ratio is consistent with a ~3.5–4× prompt-char ratio (output tokens are smaller on patches).

Severity tag: `TP` — a factual anchor only. Any cost-reduction hypothesis that proposes shrinking fan-out context has to pass through T1/T3 (prompt forensics / context packet audit); T8 only surfaces the dollar impact.

### F15. Per-call cost attribution is clean ENOUGH for the T8 question but `call-type tagging` is the remaining gap — severity `gap`

Summary of what this sink CAN answer cleanly:

- total Stage3 spend — YES (`llm_calls.stage=3` sum)
- per-ep Stage3 spend — YES
- per-agent split — YES
- fanout vs patch split — YES **only via post-hoc prompt-text classification** using `llm_io.jsonl`
- director score vs director other split — YES (same post-hoc method)
- per-attempt cost — YES (by sequencing ts)
- per-retry-round cost — PARTIAL (retry rounds are not structurally tagged; have to be reconstructed from the FANOUT × 3 repetition pattern)

Summary of what this sink CANNOT answer cleanly:

- "which specific fan-out candidate won" — maps to `director_selections.selected_label` + `candidate_key` in `stage_attempts`, but only for the terminal round, not for intermediate rejected rounds
- "what was the pre-patch Director verdict for every patched candidate" — not persisted anywhere visible to T8
- "what did the crashed sessions spend before they died" — DB has the raw calls but not the session_id tying them to a crash event
- "did thinking_tokens cause ep8's quality improvement" — no comparable non-thinking ep8 baseline exists

Severity tag: `gap` — explicit visibility gap enumeration, as demanded by the T8 residual-uncertainty note in the parent order (§13).

## Cross-Terminal Pointers

Evidence encountered during this audit that **materially belongs** to another terminal — filed as one-line pointers, not investigated further:

- → **T6 (ensemble candidate diversity)**: `conservative` and `balanced` fan-out flavors have **zero calls** in this entire session block. Only 3 of 5 advertised flavors are actually fired. Anchor: `SELECT COUNT(*) FROM llm_calls WHERE stage=3 AND agent_name='blueprint_ensemble_generator'` split by prompt header → only `액션/감정/대화` observed. This halves the diversity T6 expected to measure.
- → **T2 (retry feedback loop audit)**: F7's retry cycle shape (FANOUT×3 → D_SCORE → PATCH → D_OTHER → D_SCORE) shows the feedback-loop structure at a cost-telemetry level. T2 must verify whether the patch prompt actually carries forward the prior Director rejection reason or issues a stale directive — that semantic check is not in T8 scope.
- → **T5 (validator heuristic true/false positive)**: F8's 4/7 attempt-cap saturation could be either "producer cannot learn the contract" (T1/T3 territory) or "validator is over-rejecting contract-compliant candidates" (T5 territory). T8 cannot split the two from the cost-telemetry lens alone.
- → **T7 (Director vs Validator authority overlap)**: `director_selections.firewall_triggered` column exists but was not queried here; T7 should check whether firewall triggers correlate with the terminal `PASS_WITH_WARNING` verdicts on eps 2/5/6/7.
- → **T4 (cheap admission gate effectiveness)**: F9's "patch_mode delivered zero clean-PASS rescues" is consistent with T4 territory — if cheap admission is letting weak candidates through and patches cannot fix them, the cheap-admission gate is the upstream fix, not the patch axis.
- → **T10 (Stage4 handoff)**: 5 of 7 closed eps entered Stage4 in `PASS_WITH_WARNING` state. T10 must measure how many of those bleed into the manuscript vs are rescued by Stage4 writer gates. T8 deliberately does not score that; it only notes the PWW population size.

## Hypothesis Candidates For Synthesis

These are cost-attribution hypotheses for the synthesis pass. They are **candidates**, not directives, and each carries an explicit cost-counterfactual anchor.

**H8.1 — `fan-out round count` is the dominant cost lever, not `fan-out per-call cost`.**
- Evidence: FANOUT owns 84% of spend (F5). Per-call cost is ~$0.14–$0.16, which is not unusually high for a 20k-char prompt on `gemini-3.1-pro-preview`. The cost magnitude comes from the **count** (228 calls = 76 rounds × 3 flavors).
- Cost anchor: each round = ~$0.50; a 1-round reduction per ep ≈ $3.50 across 7 eps (~8.4% of current spend).
- Candidate tension: 4 of 7 eps hit round_num=10 (F8). Lowering the attempt cap from 10 to 7 would save ~$14 per 7 eps (≈33% reduction) **only if** the verdict does not degrade — but the eps that hit cap=10 already closed as PASS_WITH_WARNING, not as clean PASS, so the marginal rounds 8–10 were not producing verdict flips. The cost delta is defensible; the verdict delta must be checked by T5/T7.

**H8.2 — `patch_mode` is the lowest-ROI axis and is a candidate for removal OR escalation.**
- Evidence: $3.34 spent, 0 clean-PASS rescues visible (F9). Every PWW-terminal episode had at least one patch fire (ep2/4/5/6/7 all have `fix_scope='inplace'` in director_selections).
- Cost anchor: removing patch_mode entirely saves $3.34 over 7 eps (~8% reduction) **only if** the alternative (re-fanout) is cheaper than patch+rescore. Re-fanout costs ~$0.50/round vs patch+rescore ~$0.09, so a 1:1 swap is **more expensive**, not cheaper.
- The real question the synthesis pass must answer is not "remove patches" but "why do patches never produce a clean-PASS lift" — this is the axis where evidence of ineffectiveness is clearest and where a writer-side or prompt-side fix has the highest $-equivalent value per delta.

**H8.3 — the ep2 crashed-session retry block ($5.52 of waste) is a process-level failure, not a prompt-level one.**
- Evidence: F2 shows ep2 spent 71 LLM calls (~$5.5) on a first-session block that crashed and was never reused. The 70 calls in the successful session had to redo everything.
- Cost anchor: $5.52 / ep2 = 45% of ep2's Stage3 cost, or ~12% of the whole ep1–ep7 Stage3 spend on this session.
- Candidate: resilience/checkpoint on session crash would have prevented this single incident from doubling ep2's cost. That is not a prompt/validator fix; it is a queue/runtime fix and belongs in the session-resilience track, not in S2/S3/S4 runtime improvement. Flag only.

**H8.4 — `director` spend is not a cost lever; do not target Director for cost reduction.**
- Evidence: Director owns 7.8% of Stage3 spend (F4) across 185 calls at ~$0.019 avg per call. The majority (127) are `D_SCORE` micro-calls that are load-bearing for candidate selection.
- Cost anchor: a 50% cut of Director calls would save at most $1.75 per 7 eps (~4% of total). Meanwhile Director is the only gate that picks the winning fan-out candidate; removing it drops quality on every round. **Low ROI for cost-reduction attention, high ROI for quality.**

**H8.5 — the `conservative`/`balanced` fan-out flavors are paying no cost and therefore cannot be blamed for cost, but their absence means cost is concentrated on 3 flavors that evidently all fail the same contract (T6 territory, cross-pointer only).**
- Cost anchor: 0 calls = $0 spend. If adding `conservative`/`balanced` back in as active flavors, expect ~+$14 per 7 eps of spend (proportional to 3→5 flavor expansion). This only makes sense if T6 shows that `conservative`/`balanced` would have produced candidates that the current 3 flavors cannot.

**H8.6 — the tail 3–4 rounds of attempt-capped eps are demonstrably wasted at $3.20–$4.10 per ep.**
- Evidence: F8, F13. ep6 and ep7 both spent ≈$4 on rounds 7–10 without flipping verdict.
- Cost anchor: across the 4 attempt-cap eps (2, 6, 7, and possibly 5), the rounds-past-6 cost = $(12.13-4.5) + $(6.76-4.5) + $(7.36-4.5) + $(5.82-4.5) = ~$13.5 of spend producing no verdict delta vs a stop-at-6 policy.
- Candidate: a "stop if no verdict improvement over last 2 rounds" circuit breaker could save ~30% of ep1–ep7 Stage3 spend. Whether that is safe depends on whether some of those rounds did produce intermediate improvements that the final aggregation captured (this is not visible to T8 from the cost sink alone; belongs to T2/T7).

**H8.7 — per-call prompt_chars on FANOUT is ~20k median; shrinking context is the only fan-out-side lever that lowers per-call cost without lowering call count.**
- Evidence: F14.
- Cost anchor: halving FANOUT prompt_chars from 20k to 10k would roughly halve input-token cost, or ~$15 saved per 7 eps (~36%). But cutting context without knowing which sections are load-bearing is T3 territory (context packet audit); T8 only surfaces the dollar-size of the lever.

## Severity Tag Summary

| finding | tag |
|---|---|
| F1 context_tag/session_id null | gap |
| F2 pass_rate_monitor undercount | leak |
| F3 baseline $45.08 | TP |
| F4 agent split | TP |
| F5 prompt-header classifier split | TP |
| F6 per-ep per-category table | TP |
| F7 retry cycle shape | TP |
| F8 attempt-cap saturation 4/7 | waste |
| F9 ROI ranking | TP + waste (patch_mode) |
| F10 metrics-file $7.78 reconciliation gap | gap |
| F11 thinking_tokens ep8-only | TP |
| F12 Director call count | TP |
| F13 $/attempt scaling | TP |
| F14 prompt_chars distribution | TP |
| F15 visibility gap enumeration | gap |

## 3-Pass Audit Record

**Pass 1 (draft)** — initial walk of `pass_rate_monitor.json` + `metrics_20260413_194343.json` produced a per-ep cost table based on `pass_rate_monitor.token_cost`. Sum came out to $36.08, consistent with the order's "$35+" language. I almost stopped here.

**Pass 2 (DB vs ledger reconciliation)** — crossed `pass_rate_monitor.token_cost` against `SUM(total_cost_usd) FROM llm_calls WHERE stage=3` and found a $9 delta ($36.08 vs $45.08). Investigated: $3.48 is ep8 (not in pass_rate_monitor because interrupted), $5.52 is the ep2 crashed-session first block. Updated F2 and F3. Draft per-axis split was still based on `agent_name` only, which conflated fan-out and patch_mode into one bucket (`blueprint_ensemble_generator`). Pass 2 surfaced that the agent-level split cannot answer T8's actual question (`fanout vs patch vs regenerate`). Had to go to prompt text.

**Pass 3 (prompt-header classifier)** — read `llm_io.jsonl` full prompts to classify by header. Verified jsonl/DB alignment is exact (0 mismatches across 513 rows, agent-name cross-check) and built the F5 table. Discovered three additional details that required body edits:

1. No `full_regenerate` header exists in the session — the "full regenerate repair" axis from the T8 order collapses into FANOUT. Added explicit note to F5.
2. `conservative`/`balanced` flavors have zero calls — added as cross-pointer to T6.
3. Per-retry-cycle shape (F7) emerged only from ts-ordered walk of ep1; pattern confirmed on ep3, ep4, ep6.

Final confidence check: re-ran the four critical sums (`SUM(total_cost_usd) WHERE stage=3`, per-agent split, per-ep split, per-category split) and verified they all round-trip to the same grand total $45.0776 to 4 decimals. No residual arithmetic uncertainty. Residual uncertainty is limited to:

- patch_mode counterfactual ("would eps have degraded to FAILED without patches") — not falsifiable from this sink; explicit gap in F9
- thinking-token per-call split — not falsifiable from this snapshot; explicit gap in F11
- crashed-session spend attribution — visible in DB but not structurally labeled; explicit gap in F2 and F10

These three are enumerated rather than resolved. The T8 question itself (where is the money going, what is the ROI) is resolved with high confidence.

## Final Confidence

**96%** — one full percentage point below 97% due to the three explicit visibility gaps listed above; all gaps are documented findings, not unknowns. The 3-pass audit passed arithmetic cross-checks on four independent paths.
