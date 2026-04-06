# 01 Golden Stage 2 — Lane 3: DB Residue

Date: 2026-04-06
Lane: 3 — DB truth / Arc 5 residue / recoverability
Status: final
Survey Order: `docs/2026-04-06/01_golden_stage2_p0_p3_full_survey_order.md`
Confidence: `97%`

---

## 1. Coverage

### Inspected Sinks

| Sink | Records Inspected | Notes |
|------|-------------------|-------|
| `stage_attempts` | 5 rows (all) | Arc 1–4 only; no Arc 5 entry |
| `director_selections` | 5 rows (all) | Arc 1–4 only; no Arc 5 entry |
| `llm_calls` | 69 rows (all) | ep_num distribution: 1→18, 6→10, 12→13, 17→25, 22→3 |
| `cost_log` | 5 rows (all) | scope_id 1–4 only; no Arc 5 entry |
| `blueprints` | 0 rows | Empty for this run |
| `state_logs` | 0 rows | Empty for this run |
| `attempt_raw_rationale` | 0 rows | Empty for this run |
| `logs/artifacts/stage2/**` | 4 directories (arc_001–arc_004), 5 artifact files | No arc_005 directory |
| `logs/session_20260406_151023.log` | 2,471 lines (all) | 4 lines mention Arc 5 by name |
| `logs/session/ui_events.jsonl` | 361 events (last 6 span Arc 5) | 1 event with ep_num=22 |
| `logs/session/decisions.jsonl` | All entries | 0 entries for Arc 5 |

### Ep-Num Mapping (confirmed from DB)

| Arc | ep_num | stage_attempts | llm_calls |
|-----|--------|---------------|-----------|
| 1 | 1 | 1 PASS | 18 |
| 2 | 6 | 1 PASS | 10 |
| 3 | 12 | 1 PASS | 13 |
| 4 | 17 | 1 REJECT + 1 PASS | 25 |
| 5 | 22 | **0** | **3** |

---

## 2. Findings

### F1. No hidden partial commit exists for Arc 5

Arc 5 (ep_num=22) has zero records in:
- `stage_attempts`
- `director_selections`
- `cost_log`
- `decisions.jsonl`
- `attempt_raw_rationale`
- `logs/artifacts/stage2/` (no `arc_005` directory)

The only DB-level trace of Arc 5 is 3 `llm_calls` rows (ids 67–69):

| id | ts | agent_name | success | cost_usd |
|----|-----|-----------|---------|----------|
| 67 | 16:17:53 | weaver | 1 | $0.0036 |
| 68 | 16:18:12 | preflight_checker | 1 | $0.0165 |
| 69 | 16:18:56 | preflight_checker | 1 | $0.0107 |

All three calls completed successfully. These are valid completed-work records, not orphans. They record preflight activity that ran to completion before the interruption.

The session log confirms the run progressed beyond these calls:
- `16:18:12` — preflight + constraint completion
- `16:18:13` — Arc 5 generation start announced; ConstraintCompiler + StateExtractor + Optimizer all completed
- `16:18:56` — Phase 2 Ensemble generation dispatched 3 `ArcEnsembleGenerator` calls to Vertex AI

The log ends at `16:18:56` with HTTP request headers being sent to `aiplatform.googleapis.com` for the 3 parallel ensemble calls. No response was received. No llm_calls record was created for these 3 dispatched-but-unfinished calls.

**Verdict: No partial artifact, no partial stage_attempt, no partial director_selection. Arc 5 left zero uncommitted data in any authoritative sink.**

### F2. Attempt/artifact identities are cleanly recoverable without collision

Cross-check between `stage_attempts` and `director_selections` on all 5 records:

| attempt_key | hash_match | path_match | verdict_match | candidate_match |
|------------|------------|------------|---------------|-----------------|
| s2:ep1:arc1:a1:20260406_151038 | ✓ | ✓ | PASS / PASS | creative / creative |
| s2:ep2:arc2:a1:20260406_151038 | ✓ | ✓ | PASS / PASS | creative / creative |
| s2:ep3:arc3:a1:20260406_151038 | ✓ | ✓ | PASS / PASS | balanced / balanced |
| s2:ep4:arc4:a1:20260406_151038 | ✓ | ✓ | REJECT / REJECT | conservative / conservative |
| s2:ep4:arc4:a2:20260406_151038 | ✓ | ✓ | PASS / PASS | creative / creative |

All 5 artifact files verified on disk via SHA-256:

| File | DB Hash Match |
|------|-------------|
| arc_001/attempt_01/final_arc__creative.json (33,141 bytes) | MATCH |
| arc_002/attempt_01/final_arc__creative.json (34,783 bytes) | MATCH |
| arc_003/attempt_01/final_arc__balanced.json (28,810 bytes) | MATCH |
| arc_004/attempt_01/rejected_arc__conservative.json (22,739 bytes) | MATCH |
| arc_004/attempt_02/final_arc__creative.json (31,587 bytes) | MATCH |

Rejected Arc 4 attempt_01 (conservative, score 88) is cleanly distinguishable from accepted Arc 4 attempt_02 (creative, score 100) by attempt_key, content_hash, artifact_path, and file naming convention.

**Verdict: No identity collision. Accepted and rejected artifacts are fully recoverable and distinguishable.**

### F3. DB sink authority classification after interruption

**Authoritative sinks (Arc 1–4 complete, Arc 5 absence is accurate):**

- `stage_attempts` — 5 records; complete for all attempted arcs that reached verdict. Arc 5 absence correctly reflects that no verdict was issued.
- `director_selections` — 5 records; perfect 1:1 correspondence with stage_attempts.
- `llm_calls` — 69 records; includes Arc 5 preflight calls. Every call that completed is recorded. The 3 dispatched-but-unfinished ArcEnsembleGenerator calls are correctly absent.

**Authoritative but incomplete for cost tracking:**

- `cost_log` — 5 records for Arc 1–4. No Arc 5 entry despite Arc 5 incurring ~$0.031 in LLM costs across 3 calls. `cost_log` commits only after a full arc attempt cycle completes. The missing Arc 5 cost is a design-level observation, not corruption.

**Structural note on cost_log:**

- cost_log id=4 (Arc 4 rejection) has `total_calls=0`, `total_tokens=0`, `total_cost_usd=0.0` with a special `model_breakdown` recording the rejection event metadata. Actual Arc 4 costs (both attempts) are aggregated in cost_log id=5 ($1.719). This is an accounting convention, not an error.

**Empty sinks (not used for this Stage 2 run):**

- `blueprints` — 0 rows
- `state_logs` — 0 rows
- `attempt_raw_rationale` — 0 rows

These empty tables are not evidence of data loss. They represent features that were either not active for this run or store data at different stages.

### F4. Arc 5 classification: interrupted mid-generation, after preflight, before verdict

The interruption timeline reconstructed from DB + log evidence:

| Time | Event | Sink |
|------|-------|------|
| 16:17:23 | Arc 4 accepted (state_extractor completes) | stage_attempts id=5, cost_log id=5 |
| 16:17:53 | Arc 5 weaver call starts and completes | llm_calls id=67 |
| 16:18:12 | Arc 5 preflight_checker #1 completes | llm_calls id=68 |
| 16:18:12 | Arc 5 preflight + constraint + state extraction all complete | session log L2396–L2406 |
| 16:18:13 | Arc 5 generation announced; ConstraintCompiler + Optimizer ready | session log L2409–L2422 |
| 16:18:13 | Phase 1 constraint collection + Phase 2 Ensemble dispatch starts | session log L2424–L2443 |
| 16:18:56 | Arc 5 preflight_checker #2 completes (parallel Phase 1 call) | llm_calls id=69 |
| 16:18:56 | 3 ArcEnsembleGenerator calls dispatched to Vertex AI | session log L2443–L2445 |
| 16:18:56 | HTTP requests sent; awaiting response | session log L2446–L2471 (end of log) |
| — | **Interruption point** | No further log entries |

**Classification: `interrupted mid-generation, after full preflight, during ensemble candidate generation`**

This is slightly more precise than the survey order's provisional "cleanly interrupted before verdict." The run progressed past preflight into active generation dispatch. However, no generation output was received, so no verdict-relevant data exists.

### F5. No explicit interrupted-run marker

There is no DB field, log entry, or file that explicitly records "Arc 5 was interrupted." The absence of a `stage_attempts` record for Arc 5 is the only signal. An operator must:

1. Read `llm_calls` to discover ep_num=22 activity
2. Read `stage_attempts` to confirm no verdict was recorded
3. Read the session log or `ui_events.jsonl` to confirm generation had started

This requires consulting 3 separate sinks to reconstruct Arc 5's interrupted state. Consistent with the survey order's P3 candidate assessment.

---

## 3. Non-Issues

### N1. DB corruption

No corruption signal found in any inspected table. All records decode cleanly, all foreign-key-equivalent relationships (attempt_key, content_hash, artifact_path) cross-validate perfectly.

### N2. Artifact integrity

All 5 artifact files exist, are UTF-8 decodable, and SHA-256 match their DB-recorded content_hash values.

### N3. Accepted/rejected identity collision

Arc 4's rejected attempt_01 and accepted attempt_02 are completely distinguishable by every available identifier (attempt_key suffix, content_hash, artifact_path, file name convention, verdict, candidate_key, score).

### N4. Orphaned data

The 3 Arc 5 `llm_calls` records are not orphans. They accurately record completed preflight work. They can be cleanly attributed to an interrupted arc attempt by their ep_num=22 + the absence of a corresponding stage_attempt record.

---

## 4. Severity Hint

### P0

No P0 found. No DB corruption, no missing accepted artifacts, no identity collision.

### P1

Not in this lane's scope. (P1 candidate `auto-correct false-closure on field removal` is artifact-truth and observability territory.)

### P2

Not directly in this lane's scope. However, `cost_log` missing Arc 5's ~$0.031 spend is a minor gap — cost accounting is incomplete for the interrupted arc. This does not rise to P2 on its own since cost_log's commit-on-completion design is intentional.

### P3 — confirmed: `Arc 5 implicit closure without explicit interrupted-run marker`

Strengthened from "candidate" to "confirmed P3."

Evidence:
- Arc 5 reached active generation dispatch (3 parallel ArcEnsembleGenerator calls sent to Vertex AI)
- Zero explicit signal in any sink that Arc 5 was interrupted
- Recovery requires consulting 3 sinks minimum (`llm_calls` → `stage_attempts` → session log)
- Contrast: Arc 4 rejection is explicitly marked with `verdict=REJECT` in both `stage_attempts` and `director_selections`

The operational risk is low (Arc 5 had no accepted/rejected artifact to confuse), but the observability gap is real.

---

## 5. Stop

read-only lane survey complete; no project artifacts mutated
