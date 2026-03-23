Date: 2026-03-23
Document Type: evidence manifest
Terminal: T1
Parent Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md`

---

## Source Files Inspected

| File | LOC | Lines Read | Coverage |
|---|---|---|---|
| `modules/core/stage2_orchestrator.py` | 1,731 | 1-1731 (full) | 100% |
| `modules/core/stage2_finalizer.py` | 3,234 | 1-3000+ (full) | ~95% |

## Artifact Paths Verified

| Path | Exists | Type |
|---|---|---|
| `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` | yes | Stage 2 final arc artifact |
| `projects/0_0323/plans/arcs/arc_001.txt` | yes | Stage 2 arc plan |

## Console Evidence Anchors

| Line Range | Content Summary |
|---|---|
| console.txt L319-398 | Stage 2 Arc 1 design: PASS_WITH_FIX (95) -> patch -> PASS (100), ~5min |
| console.txt L326-329 | Batch 1~1 enrichment: 35.6s |
| console.txt L330-341 | Preflight + four-phase generation |
| console.txt L344-384 | Director PASS_WITH_FIX verdict with financial arithmetic issue |
| console.txt L386-394 | TF-32-V patch + Director re-audit PASS (100) |
| console.txt L397 | Stage 2 Arc 1 complete (ep 1~5) |

## DB/Audit Evidence Notes

- Stage 2 attempt records should be in `stage_attempts` table with `stage=2, arc_num=1`
- Director selection records in `director_selections` with `stage=2, ep_num=1`
- Cost record in `cost_records` with `scope_type='arc', scope_id=1`
- Not directly queried (T2 scope covers DB truth)

## Key Code Anchors

| Finding | File | Line(s) | Evidence Type |
|---|---|---|---|
| reject_reason 500-char truncation | stage2_finalizer.py | L2837 | source |
| session log reason 500-char truncation | stage2_finalizer.py | L1878 | source |
| Mojibake in legacy PASS_WITH_FIX path | stage2_finalizer.py | L1899-1903 | source |
| Legacy dead code _legacy_stage2_pass_persistence | stage2_finalizer.py | L1409-1466 | source |
| Legacy dead code _prepare_stage2_pass_fix_iteration | stage2_finalizer.py | L1883-1999 | source |
| Legacy dead code _legacy_stage2_pass_with_fix_loop_outcome | stage2_finalizer.py | L2554-2612 | source |
| Quality gate score >= 90 check | stage2_finalizer.py | L1487 | source |
| PASS_WITH_FIX max 3 iterations | stage2_finalizer.py | L2136 | source |
| Director story context 30-arc lookback | stage2_finalizer.py | L1652 | source |
| score_breakdown empty on REJECT | stage2_finalizer.py | L1533 | source |
| Mojibake in story context builder | stage2_finalizer.py | L2030-2041 | source |

## Cross-Reference to Prior Reports

| Prior Finding | This Survey Finding | Status |
|---|---|---|
| Q4 feedback-fidelity verdict_reason 500-char truncation | F-2/F-3 confirm same pattern in Stage 2 | confirmed, same class |
| Q8 Stage 2 DB rationale gap | F-2 confirms Python-side truncation exists | confirmed |
| Fresh run "0 regressions" | Confirmed: Stage 2 code operated correctly | confirmed |
| Q3 verdict accuracy chain | Stage 2's Director audit code is structurally clean; issue is in director_ensemble.py (Stage 4 path) | not T1 scope |
