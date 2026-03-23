Date: 2026-03-23
Status: final
Document Type: T1 evidence manifest
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain-evidence.md`
Parent Report: `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain.md`

---

## Evidence Manifest

### E-1. CONDITIONAL_PASS Resolution Chain (STALE claim verification)

| Source | Evidence |
|---|---|
| `director_ensemble.py:942` | `original_verdict = "CONDITIONAL_PASS"` — V60.97 swap sets CONDITIONAL_PASS |
| `director_grading.py:568,572` | `new_decision = "CONDITIONAL_PASS"` — grading system can output CONDITIONAL_PASS |
| `director_ensemble.py:1185` | `final_verdict = adaptive_result["decision"]` — receives CONDITIONAL_PASS |
| `director_ensemble.py:1187-1204` | Full if-elif-else resolution: always converts CONDITIONAL_PASS to PASS or REJECT |
| `director_ensemble.py:1202-1204` | `else: final_verdict = "PASS"` — catch-all fallback ensures no leak |
| `director_ensemble.py:1212` | `return final_verdict, adaptive_result` — returns resolved verdict |
| `stage4_interview_round.py` | grep for `CONDITIONAL_PASS` returns 0 matches — never reaches downstream |
| `stage4_interview_round.py:3788` | `if verdict in ("PASS", "PASS_WITH_FIX")` — only checks resolved verdicts |

**Conclusion**: CONDITIONAL_PASS is fully resolved within `_apply_ensemble_quality_gates()`. The Q1-Q8 R2 merge audit claim is stale.

### E-2. Scene Validator Two-Phase Fix (STALE claim verification)

| Source | Evidence |
|---|---|
| `blocking_validator_scene_checks.py:135-141` | Docstring: "1차: 원고 내 마크다운 씬 헤더(### 씬 N:)로 실제 씬 영역 측정 / 2차(fallback): 씬 헤더 없을 때만 키워드-윈도우 휴리스틱 사용" |
| `blocking_validator_scene_checks.py:157-158` | `header_matches = list(self._SCENE_HEADER_RE.finditer(manuscript))` — primary markdown detection |
| `blocking_validator_scene_checks.py:159-165` | `if header_matches:` → `_analyze_scenes_by_headers()` — headers processed first |
| `blocking_validator_scene_checks.py:166-172` | `else:` → `_analyze_scenes_by_keywords()` — keyword heuristic is fallback only |

**Conclusion**: Pre-rerun B-1 finding is stale. Scene validator now prioritizes markdown headers.

### E-3. Stage 3 save_stage_attempt Field Coverage

| Field | PASS path (L1876-1882) | Status |
|---|---|---|
| `selection_reason` | `str(_sk.get("selection_reason", "") or "")` | forwarded |
| `verdict_reason` | `str(_sk.get("verdict_reason", "") or "")` | forwarded |
| `fix_scope_reasoning` | `str(_sk.get("fix_scope_reasoning", "") or "")` | forwarded |
| `open_review` | `str(_s3_validate.get("open_review", "") or "")` | forwarded |
| `runtime_advisory` | `""` | hardcoded empty |
| `retry_directives` | `""` | hardcoded empty |

**Conclusion**: 4/6 fields forwarded (partially stale claim). 2 fields remain empty.

### E-4. Stage 2 Reject Reason Truncation

| Source | Evidence |
|---|---|
| `stage2_finalizer.py` | grep `reject_reason[:500]` → no match (stale claim) |
| `stage2_finalizer.py:3018` | `reject_reason=str(audit.get("reason", ""))[:100]` — live truncation on audit path |

**Conclusion**: Original `[:500]` claim is stale (fixed). New `[:100]` truncation exists on different path.

### E-5. Truncation Inventory (modules/core/)

Total `[:N]` patterns found in `modules/core/`:

| File | Line | Pattern | Path Type |
|---|---|---|---|
| `arc_state_utils.py:92` | `[:100]` | display |
| `context_compression.py:284` | `[:100]` | compression |
| `context_compression.py:289` | `[:100]` | compression |
| `db_manager.py:980` | `[:300]` | logging |
| `db_manager.py:1750` | `[:300]` | logging |
| `db_manager.py:2076` | `[:80]` | logging |
| `db_manager.py:3091` | `[:200]` | DB persistence |
| `context_advisor.py:1094` | `[:80]` | display |
| `db_bootstrap_runtime.py:204` | `[:200]` | logging |
| `error_helper.py:245` | `[:100]` | display |
| `error_helper.py:333` | `[:150]` | display |
| `expert_mixture.py:317,338` | `[:100]` | display |
| `failure_learning.py:221` | `[:100]` | display |
| `stage2_finalizer.py:3018` | `[:100]` | **DB persistence** |
| `stage3_orchestrator.py:2260-2263` | `[:200]`,`[:300]` | console display |
| `stage4_reject_runtime.py:548` | `[:150]` | console |
| `stage4_reject_runtime.py:568` | `[:200]` | session logger |
| `stage4_reject_runtime.py:580` | `[:300]` | session logger |
| `stage4_reject_runtime.py:604` | `[:500]` | session logger |
| `stage4_interview_round.py:5369-5370` | `[:200]` | JSONL |
| `stage4_interview_round.py:5434-5436` | `[:100]` | session logger |

DB max-retention policy violations (DB persistence path with truncation): **1 confirmed** (`stage2_finalizer.py:3018`)

Console max-display policy potential issues: ~10 locations across stage3/stage4/context_advisor

### E-6. File Inventory Summary

| Category | Files | Total LOC |
|---|---|---|
| `main_a.py` | 1 | 4,781 |
| Stage orchestrators | 3 | 6,920 |
| Stage runtimes | 6 | 5,597 |
| Stage interview/finalizer | 2 | 9,167 |
| Stage contexts/types | 4 | 886 |
| Stage preflight/validation | 3 | 4,136 |
| Stage support (helpers, canary, logging) | 5 | 2,735 |
| Domain agents (total) | 49 | ~44,000 |
| Validation layer | 17 | ~9,000 |
| **Total T1 surveyed surface** | **~90** | **~87,000** |
