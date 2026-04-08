# Stage2 Pass-Rate Durability Report — `000_260408_B`

- Terminal: 3 (Stage2 Pass-Rate Durability)
- Target project: `projects/000_260408_B/`
- Target session: `20260408_161433`
- Date: 2026-04-08
- Mode: evidence harvest only (no code edits, no rerun, no DB mutation)

## 1. What was checked

- DB table `stage_attempts` filtered to `stage=2`
- DB table `director_selections` filtered to `stage=2`
- `logs/pass_rate_monitor.json`
- On-disk artifacts under `logs/artifacts/stage2/`
- Byte hashes recomputed against recorded `content_hash`

Guiding question: is Stage2 attempt parity now durable across DB `stage_attempts`, `director_selections`, `pass_rate_monitor.json`, and artifact disk truth — i.e. is the old `DB 3 vs pass_rate 0` gap closed?

## 2. Concrete evidence

### 2.1 Count parity

| Sink | Stage2 row count |
| --- | --- |
| `stage_attempts` (stage=2) | 3 |
| `director_selections` (stage=2) | 3 |
| `pass_rate_monitor.json` `total_records` | 3 |
| `pass_rate_monitor.json` `records[]` length | 3 |
| Stage2 artifact files on disk | 3 |

All four sinks agree on **3**. No additional Stage2 rows exist anywhere in the DB (`stage_attempts` total = 3; `director_selections` total = 3; both are entirely stage=2).

### 2.2 Attempt-key parity

| ep | arc | `stage_attempts.attempt_key` | `director_selections.attempt_key` | `pass_rate_monitor.attempt_key` | match |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | `s2:ep1:arc1:a1:20260408_161433` | `s2:ep1:arc1:a1:20260408_161433` | `s2:ep1:arc1:a1:20260408_161433` | ✅ |
| 2 | 2 | `s2:ep2:arc2:a1:20260408_161433` | `s2:ep2:arc2:a1:20260408_161433` | `s2:ep2:arc2:a1:20260408_161433` | ✅ |
| 3 | 3 | `s2:ep3:arc3:a1:20260408_161433` | `s2:ep3:arc3:a1:20260408_161433` | `s2:ep3:arc3:a1:20260408_161433` | ✅ |

All three attempt keys embed the target session `20260408_161433`, and all three sinks agree row-for-row.

### 2.3 Candidate / artifact / content-hash linkage parity

| attempt_key | candidate_key (SA / DS / PRM) | content_hash (SA / DS / PRM) | artifact_path (SA / DS / PRM) | disk file | recomputed sha256 |
| --- | --- | --- | --- | --- | --- |
| `s2:ep1:arc1:a1:20260408_161433` | creative / creative / creative | `3b6c2ad2…7873e7fb5` ×3 | `logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` ×3 | exists, 35 410 bytes | `3b6c2ad2a8724cd0dd1d4c323e4f227785529a598a0840a5b907b1b7873e7fb5` ✅ |
| `s2:ep2:arc2:a1:20260408_161433` | creative / creative / creative | `895012be…524e20aa` ×3 | `logs/artifacts/stage2/arc_002/attempt_01/final_arc__creative.json` ×3 | exists, 43 602 bytes | `895012be4de352350c731ee976a1c9f822223f0ddd079f0a305bce61524e20aa` ✅ |
| `s2:ep3:arc3:a1:20260408_161433` | conservative / conservative / conservative | `0a28bffe…4b9c009f` ×3 | `logs/artifacts/stage2/arc_003/attempt_01/final_arc__conservative.json` ×3 | exists, 40 171 bytes | `0a28bffed9089e38d6b72352c1ea9cc9b85187e631e507f6609239af4b9c009f` ✅ |

- Every `content_hash` recorded in DB and in `pass_rate_monitor.json` matches the byte-level sha256 of the referenced artifact on disk.
- Every `artifact_path` resolves to exactly one file; no dangling paths, no orphan artifacts.
- No unselected candidate artifacts are left behind — `find logs/artifacts/stage2 -type f` returns exactly the three files above, all of which are the selected candidates. Candidate mix is 2× `creative` + 1× `conservative`.

### 2.4 Verdict parity

| ep/arc | `stage_attempts.verdict` | `pass_rate_monitor.success` | `pass_rate_monitor.final_verdict` |
| --- | --- | --- | --- |
| ep1/arc1 | `PASS` | `true` | `PASS` |
| ep2/arc2 | `PASS` | `true` | `PASS` |
| ep3/arc3 | `PASS` | `true` | `PASS` |

All three arcs are first-attempt PASS, `attempt_num = 1`, `is_patch = false`, `patch_fallback = false`. No retries, no patches, no failed precursors.

## 3. Mismatches or blanks

No **parity** mismatches across the four durability sinks for Stage2. Every (attempt_key, candidate_key, content_hash, artifact_path, verdict) tuple is identical across `stage_attempts`, `director_selections`, `pass_rate_monitor.json`, and the disk.

Blanks that do exist, but are out of Terminal 3 scope (flagged for completeness so they are not miscounted as pass-rate-durability drift):

- `director_selections.selected_label` is empty (`''`) for all 3 stage=2 rows.
- `stage_attempts.fix_scope`, `fix_scope_reasoning`, `selection_reason`, `verdict_reason`, `failure_category`, `reject_reason` are all empty strings.
- `pass_rate_monitor.records[*]` mirrors those blanks: `director_verdict`, `gate_basis`, `repair_scope`, `fix_scope`, `authoritative_fix_scope`, `patch_strategy`, `error_category`, `reject_bucket`, `primary_failure_layer` are all `""`; `fix_pack`, `repair_contract`, `scope_authority`, `retry_budget_axes`, `score_breakdown`, `strong_advisory_escalation` are all `{}`.

These rationale/metadata blanks are consistent across the sinks, so they are **not** a durability gap between sinks — they are an upstream blank that Terminal 2 (session decision coverage) and Terminal 4 (proof digest warn cause) should characterize. Critically, all of them look like expected empties for first-attempt PASS rows with no fix-scope required.

## 4. Gap classification

**No gap — on the Terminal 3 question.**

- Count parity: closed (3 = 3 = 3 = 3).
- Attempt-key parity: closed.
- Candidate / artifact / content-hash linkage: closed, including byte-level hash verification against the on-disk artifacts.
- Old `DB 3 vs pass_rate 0` drift that motivated this terminal: **closed**. `pass_rate_monitor.total_records = 3` now and every record is fully linked back to its `stage_attempts` / `director_selections` / disk artifact counterpart.

Residual rationale/metadata emptiness (section 3) is classified as **operator-choice / not exercised** from Terminal 3's perspective: three first-attempt PASS arcs with no patch cycle legitimately have no fix-scope or reject-reason content to record. It is not sink drift.

## 5. Verdict

Stage2 attempt parity is durable across DB `stage_attempts`, DB `director_selections`, `pass_rate_monitor.json`, and the Stage2 artifact files on disk for session `20260408_161433`. Counts, attempt keys, candidate keys, artifact paths, and sha256 content hashes all match row-for-row. The prior `DB 3 vs pass_rate 0` gap is fully closed in `000_260408_B`. Any remaining `proof_digest.status = "warn"` signal is **not** attributable to pass-rate durability in this run and should be explained by the other terminals (rationale metadata coverage, proof digest readiness, Stage3 absence).
