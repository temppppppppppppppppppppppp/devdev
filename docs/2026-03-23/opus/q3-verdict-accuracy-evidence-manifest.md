Date: 2026-03-23
Status: final
Document Type: Q3 verdict accuracy evidence manifest
Canonical Path: `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md`
Source Report: `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md`

---

## 1. Primary Source Files Examined

| File | Lines | Method Count | Read Depth |
|---|---|---|---|
| `modules/domain/agents/director_ensemble.py` | 2,210 | ~25 methods + 60 helpers | Full |
| `modules/domain/agents/director_auditor.py` | 1,488 | ~30 methods | Full |
| `modules/core/stage4_director_runtime.py` | 1,516 | ~30 methods | Full |
| `modules/core/stage4_interview_round.py` | 5,897 | ~120 methods | Full |
| `modules/domain/agents/four_phase_arc_runtime.py` | 1,704 | ~30 methods | Full |

## 2. Secondary Source Files Examined

| File | Lines Read | Purpose |
|---|---|---|
| `modules/domain/agents/director_grading.py` | L461-580 | `get_adaptive_threshold()` + `apply_adaptive_decision()` |
| `modules/domain/agents/director.py` | L82-92 | Facade delegation to `_grading` |
| `config/settings/validation.yaml` | L33-39 | `quality_gate_score=90`, `default_pass_threshold=60` |

## 3. Evidence Anchors for P0/P1 Findings

### P0-1: Adaptive decision no try/except
- **Primary**: `director_ensemble.py:1109-1115` — bare call with no exception handler
- **Comparison**: L810-876 (`_request_ensemble_selection_response`) — has try/except
- **Comparison**: `stage4_director_runtime.py:L210-211` — ConsistencyValidator has logging.warning fallback

### P0-2: V60.97 unconditional REJECT
- **Swap trigger**: `director_ensemble.py:888` — `if selected_idx not in qualified_indices and qualified_indices`
- **Score reset**: `director_ensemble.py:922` — `score = 50`
- **Verdict reset**: `director_ensemble.py:923` — `original_verdict = "CONDITIONAL_PASS"`
- **REJECT enforcement**: `director_ensemble.py:1122-1124` — `elif state.v60_97_swapped: final_verdict = "REJECT"`
- **Fresh run evidence**: `fresh-run-3pass-audit-report.md` P1-1 — ep5 V60.97 → REJECT cascade
- **Existing fix**: `quick_judge_single()` at `director_ensemble.py:2142-2209` (potential re-evaluation target)

### P0-3: Dual threshold regime
- **Quality gate**: `stage4_interview_round.py:3753` — `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`
- **Quality gate check**: `stage4_interview_round.py:3755-3756` — `if verdict == "PASS" and score < _quality_gate_score: verdict = "REJECT"`
- **Adaptive base**: `director_grading.py:477` — `base = self._d.base_pass_threshold` (60)
- **Adaptive range**: `director_grading.py:484-494` — -5 to +10 position modifier
- **Config source**: `validation.yaml:34` — `quality_gate_score: 90`
- **Config source**: `validation.yaml:35` — `default_pass_threshold: 60`

### P1-1: ep_type dropped
- **Caller**: `director_ensemble.py:1109-1115` — `self._d.apply_adaptive_decision(score=..., original_decision=..., arc_pos=..., total_eps=..., retry_count=...)` — no `ep_type`
- **Callee signature**: `director_grading.py:555-556` — `def apply_adaptive_decision(self, score, original_decision, arc_pos=1, total_eps=5, retry_count=0)` — no `ep_type` param
- **Underlying**: `director_grading.py:461-462` — `def get_adaptive_threshold(self, arc_pos=1, total_eps=5, ep_type="normal", retry_count=0)` — accepts `ep_type`
- **Prior finding**: `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md` TF-DG-03

### P1-2: Firewall fixability false negatives
- **Token list**: `director_ensemble.py:313-343` — 30+ fixable token types
- **Text markers**: `director_ensemble.py:345-361` — 10+ marker patterns
- **Classification**: `director_ensemble.py:394-405` — `_is_fixable_firewall_contradiction()`
- **Usage**: `director_ensemble.py:442` — `all(_is_fixable_firewall_contradiction(c) for c in found_contradictions)`

### P1-3: Post-select silent downgrade
- **Entry**: `stage4_interview_round.py:3553` — `_run_post_select_checks()`
- **Continuity check**: `stage4_interview_round.py:3598-3606` — parallel future
- **History check**: `stage4_interview_round.py:3611-3619` — parallel future
- **Downgrade**: `stage4_interview_round.py:3654-3664` — `verdict → REJECT`, `error_category = "LOGIC_ERROR"`
- **Marker**: `stage4_interview_round.py:3676` — `provisional_pass_downgrade = True`

### P1-4: CONDITIONAL_PASS branch logging
- **Resolution logic**: `director_ensemble.py:1118-1130` — 4 branches
- **Branch tracking**: `director_ensemble.py:1131-1135` — `_adaptive_branch` variable
- **Operator log**: `director_ensemble.py:1131-1135` — fires only if `_adaptive_branch` set

### P1-5: Score=0 no recovery
- **Score set**: `director_ensemble.py:2105` — `score=0` with comment `[P0-3]`
- **Verdict**: `director_ensemble.py:2112-2113` — `verdict="REJECT"`, `parsing_error=True`
- **JSON parser**: `base_agent.py` — `_extract_json_robust()` (not fully traced)

## 4. Gate Chain Verification Trace

| Gate # | Location | Input Verdict | Output Verdict | Score Mutation | Logged |
|---|---|---|---|---|---|
| 1 | `director_ensemble.py:2081-2096` | — | REJECT | 50 | WARNING |
| 2 | `director_ensemble.py:662-697` | — | REJECT | 30 | WARNING |
| 3 | `director_ensemble.py:2099-2117` | — | REJECT | 0 | WARNING |
| 4 | `director_ensemble.py:888-928` | LLM verdict | CONDITIONAL_PASS | 50 | WARNING + operator_log |
| 5 | `director_ensemble.py:903-918` | unchanged | unchanged | sum of breakdown | WARNING + operator_log |
| 6 | `director_ensemble.py:969-977` | unchanged | unchanged | min(score, 90) | INFO + operator_log |
| 7 | `director_ensemble.py:979-1033` | PASS→PASS_WITH_FIX or REJECT | verdict changed | cap 97 or 44 | WARNING |
| 8 | `director_ensemble.py:1034-1057` | unchanged | unchanged | none | WARNING (info only) |
| 9 | `director_ensemble.py:1081-1107` | unchanged | unchanged | recalc from breakdown | INFO/WARNING |
| 10 | `director_ensemble.py:1109-1137` | verdict | resolved PASS/REJECT | none | operator_log |
| 11 | `stage4_director_runtime.py:618` → `stage4_interview_round.py:1804-1838` | verdict | normalized | none | implicit |
| 12 | `stage4_director_runtime.py:619` → `stage4_interview_round.py:1728-1773` | PASS_WITH_FIX | REJECT if invalid | none | WARNING |
| 13 | `stage4_interview_round.py:3753-3765` | PASS + score<90 | REJECT | none | feedback added |
| 14 | `stage4_interview_round.py:3553-3703` | PASS | REJECT on conflict | none | logged |

## 5. Hardcoded Threshold Inventory

See Appendix A in main report — 20 thresholds cataloged with exact file:line.

## 6. Error Handling Default Verification

| Error Path | Default | Verified Location |
|---|---|---|
| LLM ask failure | REJECT | `director_ensemble.py:822-824` |
| JSON parse failure | REJECT, score=0 | `director_ensemble.py:2099-2117` |
| Prompt load failure | REJECT, score=50 | `director_ensemble.py:2081-2096` |
| Missing verdict field | REJECT | `stage4_director_runtime.py:643` |
| Missing score field | 0 | `stage4_director_runtime.py:644-648` |
| Invalid fix_pack | REJECT | `stage4_interview_round.py:1769` |
| Post-select conflict | REJECT | `stage4_interview_round.py:3654-3664` |
| Director error (Stage 2) | retry loop | `four_phase_arc_runtime.py:1306-1315` |
| Validator error | REJECT (assumed) | `four_phase_arc_runtime.py:1522` |

All error paths verified: **no false PASS on error**.
