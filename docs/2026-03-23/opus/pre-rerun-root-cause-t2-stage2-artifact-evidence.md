Date: 2026-03-23
Document Type: evidence manifest
Terminal: T2
Focus: Stage 2 arc artifact and DB truth

---

# T2 Evidence Manifest

## 1. Artifact Files

| Path | Type | Size | Integrity |
|------|------|------|-----------|
| `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` | JSON | 364 lines, ~12K tokens | Complete, 24 keys, UTF-8 clean |
| `projects/0_0323/plans/arcs/arc_001.txt` | Text | 96 lines | Complete, tactical_doc matches artifact |

## 2. DB Tables Queried

### stage_attempts

| Query | Result |
|-------|--------|
| `SELECT * FROM stage_attempts WHERE stage=2` | 1 row: id=1, verdict=PASS, score=100, all textual fields EMPTY |
| `SELECT * FROM stage_attempts WHERE stage=3` | 4 rows: ids 2-5, all textual fields EMPTY |
| `SELECT * FROM stage_attempts WHERE stage=4` | 7 rows: ids 6-12, all textual fields POPULATED |

Stage 2 empty fields confirmed:
- `selection_reason = ""`
- `verdict_reason = ""`
- `open_review = ""`
- `runtime_advisory = ""`
- `retry_directives = ""`
- `score_breakdown = null`

### director_selections

| Query | Result |
|-------|--------|
| `SELECT * FROM director_selections WHERE stage=2` | 1 row: id=1, selection_reason POPULATED, verdict_reason EMPTY, director_thinking POPULATED |
| `SELECT * FROM director_selections WHERE stage=3` | 4 rows: ids 2-5, selection_reason POPULATED, verdict_reason POPULATED |
| `SELECT * FROM director_selections WHERE stage=4` | 6 rows: ids 6-11, both fields POPULATED |

### anchors

| Key | Size | Notes |
|-----|------|-------|
| `arcs` | 14,139 bytes | 1 arc, 24 keys, identical to artifact JSON |
| `arc_summary_1` | 451 bytes | Arc 1 summary |
| `world_state` | 2,933 bytes | Post ep 3 |
| `fact_ledger` | 1,988 bytes | Post ep 3 |

## 3. Log Files

### runtime_audit.jsonl (19 entries total)

| Entry | Type | Stage 2 Relevant? |
|-------|------|-------------------|
| [0] | v60_25_auto_correct | Yes — arc 1 auto-corrections |
| [1] | db_commit | Indirect — post-Stage 2 commit |
| [2] | v60_10_state_extracted | Yes — StateExtractor after arc 1 |
| [4]-[11] | blueprint_success, continuity_pin, db_commit | Stage 3 |
| [12]-[18] | stage4_retry_pathology, target_ep_reached, stage4_complete | Stage 4 |

No explicit Stage 2 Director verdict event in runtime_audit.

### episode_production.jsonl (11 entries)

All entries are Stage 4 (ep 1-3). No Stage 2 or Stage 3 entries.

### session/decisions.jsonl (13 entries)

| Index | Stage | Decision | Score |
|-------|-------|----------|-------|
| [0] | stage2 | PASS_WITH_FIX | 95 |
| [1] | stage2 | PASS (arc_design) | 0 |
| [2]-[5] | stage3 | PASS (blueprint) | 92-98 |
| [6]-[12] | stage4 | PASS/REJECT (manuscript) | 76-98 |

### session/state_changes.jsonl (6 entries)

All entries are Stage 4 post-pass state changes (world_state + fact_ledger for ep 1-3). No Stage 2 state change entries.

## 4. Source Code Anchors

| Finding | File | Lines | Notes |
|---------|------|-------|-------|
| Stage 2 PASS save_stage_attempt | `modules/core/stage2_finalizer.py` | L2691-2710 | Missing: selection_reason, verdict_reason, open_review, score_breakdown |
| Stage 2 REJECT save_stage_attempt | `modules/core/stage2_finalizer.py` | L2829-2849 | Same omissions |
| Stage 2 PASS save_director_selection | `modules/core/stage2_finalizer.py` | L2714-2729 | Missing: verdict_reason |
| Stage 2 REJECT save_director_selection | `modules/core/stage2_finalizer.py` | L2852-2867 | Missing: verdict_reason |
| Stage 4 save_stage_attempt | `modules/core/stage4_interview_round.py` | L5784-5813 | All fields passed via _build_stage4_db_attempt_payload |
| Stage 4 save_director_selection | `modules/core/stage4_interview_round.py` | L2304-2325 | verdict_reason explicitly passed at L2316 |
| DB save_stage_attempt signature | `modules/core/db_manager.py` | L2878-2910 | All fields supported |
| DB save_director_selection signature | `modules/core/db_manager.py` | L2152-2174 | All fields supported |

## 5. Console Transcript Anchors

| Line Range | Event |
|------------|-------|
| L319-320 | Stage 2 Arc 1 design start |
| L326-329 | Batch enrich |
| L330-334 | Preflight (arc_drive, preflight, constraint) |
| L335-339 | FourPhase-Director attempt 1/10 |
| L343-384 | Director PASS_WITH_FIX (score=95), 1 contradiction, full thinking |
| L386-389 | TF-32-V patch (financial amount fix) |
| L391 | Director re-audit #1: PASS (score=100) |
| L392 | PatchPressure advisory |
| L393-397 | ConstraintDB update, arc 1 success |

## 6. Cross-Source Reconciliation

| Data Point | Artifact | DB stage_attempts | DB director_selections | Console | Session decisions |
|------------|----------|-------------------|----------------------|---------|-------------------|
| Final verdict | (implicit PASS) | PASS | PASS | PASS | PASS |
| Final score | _ensemble_meta.best_score=95 | 100 | 100 | 100 (re-audit) | 95 (initial), 0 (final arc_design) |
| Strategy | conservative | conservative | conservative | conservative | N/A |
| Candidate count | _ensemble_meta.total_candidates=3 | N/A | candidate_count=3 | 3 | N/A |
| Director thinking | N/A | N/A | FULL (multi-paragraph) | FULL | N/A |
| selection_reason | N/A | EMPTY | "PatchPressure Advisory..." | N/A | N/A |
| verdict_reason | N/A | EMPTY | EMPTY | (in thinking) | meta.reason POPULATED |

Score discrepancy (95 vs 100) is explained by pre-patch (95) vs post-patch re-audit (100). Not a bug.
