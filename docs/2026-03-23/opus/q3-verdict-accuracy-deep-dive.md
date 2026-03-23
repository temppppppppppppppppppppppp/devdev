Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q3 verdict accuracy deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md`
Source Order: `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md` (T3)
Axis: Q3 — "잘 판단하냐" (PASS/REJECT correctness, gate chain, director verdict accuracy)
Primary Scope:
- `modules/domain/agents/director_ensemble.py` (2,210 lines)
- `modules/domain/agents/director_auditor.py` (1,488 lines)
- `modules/core/stage4_director_runtime.py` (1,516 lines)
- `modules/core/stage4_interview_round.py` (5,897 lines)
- `modules/domain/agents/four_phase_arc_runtime.py` (1,704 lines)
Secondary References:
- `modules/domain/agents/director_grading.py` (adaptive threshold logic)
- `modules/domain/agents/director.py` (facade)
- `config/settings/validation.yaml` (quality_gate_score, thresholds)

---

## 1. Executive Summary

The Director verdict pipeline is a **14-gate chain** spanning 5 files and ~12,800 LOC. The chain transforms an LLM raw verdict through Python gates, firewalls, adaptive thresholds, and contract enforcement before producing the final PASS/REJECT outcome.

**Overall assessment:** The verdict chain is structurally sound — error defaults are consistently REJECT (fail-closed), and no code path silently converts REJECT to PASS without at least one logged marker. However, the chain has **3 P0 accuracy risks** and **5 P1 accuracy risks** where Python logic can override LLM judgment in ways that reduce verdict accuracy.

**Key tension:** The system uses two fundamentally different threshold regimes — `quality_gate_score=90` (hard Python gate) and `base_pass_threshold=60` (adaptive, position-adjusted) — creating a 30-point gray zone where adaptive logic says CONDITIONAL_PASS but the quality gate says REJECT. This is the single largest source of verdict accuracy ambiguity.

Fresh-run-before-fix allowed: **no**

Top 3 highest-ROI code fixes before next fresh run:
1. **P0-1:** `apply_adaptive_decision()` call has no try/except — any `director_grading.py` error crashes the entire verdict pipeline (one-line fix, zero risk)
2. **P0-2:** V60.97 score reset unconditionally to 50, later forced to REJECT by adaptive fallthrough — Director's chosen candidate is discarded without re-evaluation (contract-cleanup)
3. **P1-1:** `ep_type` parameter not forwarded to `apply_adaptive_decision()` — climax episode strictness silently dropped (one-line fix)

---

## 2. Current Ownership / Flow Map

### 2.1 Stage 4 Manuscript Verdict Chain (14 gates)

```
ChiefWriter generates 3 candidates
    │
    ▼
Stage4InterviewRound._run_validation_phase()
    │ Sets _god1_* attributes for Stage4DirectorRuntime
    ▼
Stage4DirectorRuntime.run_pre_director_validation()
    │ manuscript_validator, consistency/blocking/continuity validators
    │ Collects advisory chain (9 parallel advisories)
    ▼
DirectorEnsembleSelector.select_and_judge_ensemble()
    │
    ├─ GATE 1: Prompt error → REJECT, score=50
    ├─ GATE 2: Length guard (all <MIN) → REJECT, score=30
    ├─ GATE 3: LLM ask + JSON parse error → REJECT, score=0
    ├─ GATE 4: V60.97 length swap → CONDITIONAL_PASS, score=50
    ├─ GATE 5: Score breakdown reconciliation → authoritative sum
    ├─ GATE 6: SCM single-candidate cap → score ≤ 90
    ├─ GATE 7: Contradiction firewall → PASS_WITH_FIX (cap 97) or REJECT (cap 44)
    ├─ GATE 8: Numeric consistency advisory (info only, no verdict change)
    ├─ GATE 9: Consistency checklist penalty → python_warnings cap to 3
    └─ GATE 10: Adaptive decision (director_grading) → CONDITIONAL_PASS resolution
    │
    ▼
Stage4DirectorRuntime._invoke_director_review()
    ├─ GATE 11: _normalize_director_gate_semantics() → gate_basis derivation
    └─ GATE 12: _enforce_pass_with_fix_contract() → PASS_WITH_FIX → REJECT if invalid fix_pack
    │
    ▼
Stage4InterviewRound._process_verdict()
    ├─ GATE 13: Quality gate (PASS + score < 90) → REJECT
    └─ GATE 14: Post-select continuity/history checks → REJECT on conflict
    │
    ▼
Final: _finalize_round_pass_path() or _finalize_round_reject_path()
```

### 2.2 Stage 2 Arc Verdict Chain (3 gates)

```
FourPhaseArcRuntime: ensemble generates 1-3 candidates
    │
    ├─ Quality flags: NS-3-B (score_cap=89), Investment CRITICAL (force_reject, cap=69), Investment MAJOR (cap=89)
    ├─ GATE 1: Director.compare_and_select_arc() → PASS/PASS_WITH_FIX/REJECT
    └─ GATE 2: Validator.validate() → final PASS/REJECT
    │
    ▼
Final: return (arc, pipeline_result) or retry loop (max 9)
```

### 2.3 File Authority Map

| File | Authority | Verdict Role |
|---|---|---|
| `director_ensemble.py` | Ensemble selection + 10 gates | LLM verdict → post-gate verdict |
| `director_auditor.py` | Quality auditing + hard guards | Pre-LLM early REJECT, V0128 3-tier |
| `stage4_director_runtime.py` | Runtime coordination + 2 gates | Gate normalization, contract enforcement |
| `stage4_interview_round.py` | Round orchestration + 2 gates | Quality floor, post-select checks |
| `four_phase_arc_runtime.py` | Stage 2 arc orchestration | Candidate filtering, director delegation |
| `director_grading.py` | Adaptive threshold computation | Threshold = base ± position ± genre ± type ± retry |

---

## 3. Top Hotspots

### P0-1. `apply_adaptive_decision()` — no try/except wrapper
- **file:line**: `director_ensemble.py:1109-1115`
- **fix type**: contract-cleanup
- **Description**: The adaptive decision call at L1109 has no try/except. If `director_grading.py` raises any exception (division by zero in threshold calc, attribute error on disabled grading system), the entire verdict pipeline crashes. All other external calls in this file have error handling.
- **Impact**: Pipeline crash → episode failure → retry storm or manual intervention. Not exercised in fresh run, but structurally unguarded.
- **Fix**: Wrap in try/except, default to `{"decision": original_verdict, "adjusted": False}` on failure.

### P0-2. V60.97 score reset = unconditional REJECT path
- **file:line**: `director_ensemble.py:888-928` (swap) + `director_ensemble.py:1122-1124` (REJECT enforcement)
- **fix type**: boundary-refactor
- **Description**: When V60.97 triggers (LLM picks short candidate), score is reset to 50 and verdict to CONDITIONAL_PASS. Later, at L1122-1124, if `v60_97_swapped=True`, CONDITIONAL_PASS is forced to REJECT. This means: *any V60.97 swap is guaranteed REJECT regardless of the swapped candidate's quality*. The Director never re-evaluates the swapped candidate.
- **Impact**: Fresh run P1-1 (ep5 REJECT) was directly caused by this chain — Director chose Candidate C (best continuity), V60.97 swapped to A (longest but worse continuity), score reset to 50, forced REJECT. The swapped candidate was never judged on its own merit.
- **Evidence**: `fresh-run-3pass-audit-report.md` P1-1: "Director가 선택한 후보를 길이 이유로 폐기하고 열등한 후보로 교체하는 패턴은 재발 가능성 높음."
- **Fix direction**: After V60.97 swap, run a quick single-candidate re-evaluation (`quick_judge_single()` already exists at L2142-2209) instead of unconditionally resetting score to 50.

### P0-3. Dual threshold regime — 90 vs 60 gray zone
- **file:line**: `stage4_interview_round.py:3753-3765` (quality gate 90) + `director_grading.py:461-553` (adaptive base 60)
- **fix type**: contract-cleanup
- **Description**: Two independent threshold regimes coexist:
  - `quality_gate_score=90`: Hard Python gate in `_process_verdict()` — if Director says PASS but score < 90, verdict → REJECT
  - `base_pass_threshold=60`: Adaptive threshold in `director_grading.py` — used to decide CONDITIONAL_PASS elevation
  - With adaptive adjustments, the pass threshold can range from 55 (intro, -5) to 72 (climax investment, +12). A score of 75 passes adaptive but fails quality gate (90).
- **Impact**: The quality gate at 90 makes the adaptive threshold below 90 largely irrelevant for PASS decisions. The adaptive system can only elevate REJECT→CONDITIONAL_PASS, but the quality gate catches it again. The two systems produce contradictory signals.
- **Fix direction**: Unify: either quality_gate_score = adaptive_threshold, or remove quality_gate_score and let the adaptive system be the single authority.

### P1-1. `ep_type` parameter dropped from adaptive decision
- **file:line**: `director_ensemble.py:1109` (caller) vs `director_grading.py:461-462` (callee)
- **fix type**: contract-cleanup
- **Description**: `apply_adaptive_decision()` at L1109 passes `arc_pos`, `total_eps`, `retry_count` but omits `ep_type`. The underlying `get_adaptive_threshold()` accepts `ep_type` (L462) with modifiers: climax=+10, transition=+3, intro=-5. Since `ep_type` defaults to `"normal"`, climax episodes get no strictness boost.
- **Impact**: Medium-High. Climax episodes (arc_pos/total_eps ≥ 0.8) get the +10 boost from position ratio anyway, but mid-arc climax episodes get no type-based strictness. This was already identified in `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md` (TF-DG-03).
- **Fix**: Add `ep_type` parameter to `apply_adaptive_decision()` and forward from ensemble caller.

### P1-2. Firewall fixability detection — token-matching false negatives
- **file:line**: `director_ensemble.py:313-405`
- **fix type**: observability-only
- **Description**: The contradiction firewall classifies contradictions as "fixable" via `_is_fixable_firewall_contradiction()` (L394-405), which checks for 30+ token types (L313-343) and text marker patterns (L345-361). A contradiction that doesn't match any token or marker pattern is classified as unfixable → triggers REJECT instead of PASS_WITH_FIX.
- **Impact**: False negatives in fixability detection mean valid PASS_WITH_FIX candidates get rejected. The token list is comprehensive but not exhaustive — novel contradiction types from LLM advisory can bypass all 30 tokens.
- **Fix direction**: Add observability: log when a contradiction is classified as unfixable, showing which tokens/markers were checked. This allows monitoring false negatives without changing verdict logic.

### P1-3. Post-select continuity check — silent PASS→REJECT downgrade
- **file:line**: `stage4_interview_round.py:3553-3703`
- **fix type**: observability-only
- **Description**: After Director says PASS, `_run_post_select_checks()` runs continuity and history conflict checks in parallel. If either returns CONFLICT, verdict is downgraded to REJECT with `error_category="LOGIC_ERROR"` and `provisional_pass_downgrade=True`. The downgrade is logged, but the operator sees it only in the final verdict line — there's no explicit "Director PASS was overridden by post-select check" operator-surface message.
- **Impact**: Operator may not understand why a Director PASS became REJECT. The `gate_basis` is set to `"post_select_conflict"`, which is correct but requires DB query to discover.
- **Fix direction**: Add explicit operator-surface log line when post-select downgrade occurs: "Director PASS(score=X) overridden by {continuity|history} conflict."

### P1-4. CONDITIONAL_PASS resolution — incomplete branch logging
- **file:line**: `director_ensemble.py:1118-1137`
- **fix type**: observability-only
- **Description**: The CONDITIONAL_PASS resolution logic at L1118-1130 has 4 branches (REJECT passthrough, V60.97 REJECT, adjusted passthrough, default PASS). The `_adaptive_branch` variable is only set in 3 of 4 branches — the default PASS fallback at L1129-1130 sets `_adaptive_branch` to `"unknown_conditional_pass"` but doesn't always trigger `_operator_log`. If `_adaptive_branch` is set, the operator log at L1131-1135 fires; if somehow unset (impossible in current code but fragile), the decision is silent.
- **Impact**: Low in current code (all branches set `_adaptive_branch`), but the structure is fragile — adding a new branch without setting `_adaptive_branch` would create a silent verdict path.
- **Fix direction**: Move operator_log after the if-elif chain unconditionally, log the resolved branch regardless.

### P1-5. Score=0 on parsing error — no recovery path
- **file:line**: `director_ensemble.py:2099-2117`
- **fix type**: contract-cleanup
- **Description**: When JSON parsing fails, score is set to 0 with comment `[P0-3] score=0이면 adaptive에서도 올릴 수 없음`. This is an intentional safety mechanism — but it means a transient JSON formatting issue from the LLM (e.g., markdown wrapper around JSON) causes an unrecoverable REJECT for that attempt.
- **Impact**: The LLM may have produced a valid judgment that failed only in formatting. `_extract_json_robust()` already handles many edge cases, but if it fails, the entire LLM reasoning is discarded with no fallback.
- **Fix direction**: Consider a single retry with `json_mode=True` or explicit re-ask before defaulting to score=0. Current behavior is safe but wasteful.

---

## 4. Quick Wins

| # | Description | file:line | fix type | ROI |
|---|---|---|---|---|
| QW-1 | Wrap `apply_adaptive_decision()` in try/except | `director_ensemble.py:1109` | contract-cleanup | HIGH — prevents crash |
| QW-2 | Forward `ep_type` to `apply_adaptive_decision()` | `director_ensemble.py:1109` | contract-cleanup | MEDIUM — 1 parameter add |
| QW-3 | Log when firewall contradiction is "unfixable" | `director_ensemble.py:1000-1033` | observability-only | MEDIUM — diagnostic |
| QW-4 | Log post-select downgrade explicitly on operator surface | `stage4_interview_round.py:3654-3664` | observability-only | MEDIUM — clarity |
| QW-5 | Log V60.97 swap on operator surface with pre/post candidate details | `director_ensemble.py:894` | observability-only | LOW — already has WARNING |

---

## 5. Boundary Refactor Candidates

### BR-1. V60.97 swap + re-evaluation (P0-2)
- **Current**: V60.97 swap → score=50 → forced REJECT (no re-evaluation)
- **Target**: V60.97 swap → `quick_judge_single(swapped_candidate)` → use returned score/verdict
- **Complexity**: Medium — `quick_judge_single()` already exists (L2142-2209) but is designed for emergency fallback. Need to validate it produces comparable scores to ensemble selection.
- **Risk**: Low — the current behavior is strictly worse (unconditional REJECT).

### BR-2. Unify quality_gate_score and adaptive threshold (P0-3)
- **Current**: Two independent thresholds (90 vs 60-72 adaptive) create contradictory signals
- **Target**: Either:
  - (A) Remove quality_gate_score, let adaptive be sole authority, or
  - (B) Set quality_gate_score = max(adaptive_threshold, quality_gate_score), so quality gate is never stricter than adaptive, or
  - (C) Feed quality_gate_score into adaptive calculation as a floor
- **Complexity**: Medium — requires understanding which threshold the user considers authoritative
- **Risk**: Medium — changing quality_gate_score from 90 could let lower-quality manuscripts pass

### BR-3. CONDITIONAL_PASS semantic cleanup
- **Current**: CONDITIONAL_PASS is used as an intermediate state that is always resolved before return. It has no semantic meaning beyond "pending resolution."
- **Target**: Eliminate CONDITIONAL_PASS as a verdict value. Instead, use explicit state flags:
  - `v60_97_swapped` → triggers re-evaluation or REJECT
  - `adaptive_adjusted` → triggers passthrough or elevation
  - `firewall_downgraded` → already has `firewall_triggered`
- **Complexity**: High — touches 15+ code paths
- **Risk**: Low if done correctly — all existing behavior preserved, just cleaner representation

---

## 6. Fresh-Run Relevance

### Fresh-run-before-fix allowed: **no**

**Rationale**: The fresh run already demonstrated P0-2 (V60.97 → ep5 REJECT cascade → pipeline termination). Running another fresh run without fixing this would likely reproduce the same failure pattern, especially for manuscripts near MIN_LENGTH boundary.

### Top 3 highest-ROI fixes before next fresh run:

1. **P0-1 try/except for adaptive decision** — prevents crash on grading system error (1 line, zero risk)
2. **P0-2 V60.97 re-evaluation instead of unconditional REJECT** — directly addresses fresh run ep5 failure
3. **P1-1 ep_type forwarding** — ensures climax episodes get correct strictness

### Fresh-run relevance classification:

| Finding | Classification | Reason |
|---|---|---|
| P0-1 (adaptive no try/except) | **fix before rerun** | LLM-Director 정합성 불일치 |
| P0-2 (V60.97 forced REJECT) | **fix before rerun** | LLM-Director 정합성 불일치 — directly caused ep5 failure |
| P0-3 (dual threshold) | **fix before rerun** | LLM-Director 정합성 불일치 — signals contradict each other |
| P1-1 (ep_type dropped) | **fix before rerun** | LLM-Director 정합성 불일치 |
| P1-2 (firewall false neg) | 관측성 부족 | need observability first |
| P1-3 (post-select silent) | 관측성 부족 | need observability first |
| P1-4 (branch logging) | 관측성 부족 | low impact |
| P1-5 (score=0 no recovery) | LLM-Director 정합성 불일치 | moderate impact, but safe default |

---

## 7. Confidence And Limits

**Estimated confidence: 95%**

**Basis:**
- All 5 primary scope files read in full (12,800+ LOC)
- Adaptive decision logic verified in `director_grading.py` source
- Fresh run evidence (P1-1 ep5 failure) triangulated against V60.97 code path
- Gate chain mapped end-to-end: 14 gates for Stage 4, 3 gates for Stage 2
- All hardcoded thresholds cataloged with source lines
- Error handling defaults verified: consistently REJECT (no false PASS paths)

**The 5% gap is from:**
- V0128 3-tier validation internals not fully traced (delegated to `ValidationOrchestrator`, outside primary scope) — 2%
- Blocking validator post-select behavior partially delegated to `reject_runtime` (outside primary scope) — 1%
- Advisory chain has 9 parallel advisories; only TruthGate was traced to its text injection logic — 1%
- `_extract_json_robust()` robustness (in `base_agent.py`) not fully verified — 1%

**Stale claim check:**
- Fresh run report P1-1 (V60.97 swap → REJECT cascade): **confirmed in live code** — L888-928 + L1122-1124 exactly match the described behavior
- Director deep-dive "P0=0": **consistent** — no new P0 verdict accuracy issues found beyond what was already flagged as design tension
- TF-DG-03 (ep_type not forwarded): **confirmed still present** — `director_ensemble.py:1109` still omits `ep_type`

---

## Appendix A: Complete Threshold Reference

| Threshold | Value | Source | Purpose |
|---|---|---|---|
| quality_gate_score | 90 | `validation.yaml:34` | Hard PASS floor in _process_verdict() |
| base_pass_threshold | 60 | `validation.yaml:35` | Adaptive threshold base |
| genre_threshold (wuxia) | 70 | `validation.yaml:37` | Genre override (unused in adaptive?) |
| V60.97 reset score | 50 | `director_ensemble.py:922` | Unconditional on swap |
| Firewall REJECT cap | 44 | `director_ensemble.py:1024` | Contradiction severity |
| Firewall PASS_WITH_FIX cap | 97 | `director_ensemble.py:1006` | Fixable contradiction |
| SCM penalty cap | 90 | `director_ensemble.py:971` | Single-candidate ceiling |
| Parsing error score | 0 | `director_ensemble.py:2105` | Prevents adaptive elevation |
| Length guard score | 30 | `director_ensemble.py:674` | All candidates too short |
| Firewall fixable: score min | 80 | `director_ensemble.py:435` | Must score ≥80 for fix path |
| Firewall fixable: continuity min | 30 | `director_ensemble.py:440` | Continuity breakdown ≥30 |
| Firewall fixable: contradiction max | 3 | `director_ensemble.py:437` | ≤3 for fix, >3 for REJECT |
| Contradiction CRITICAL trigger | 1 | `director_ensemble.py:994` | 1+ CRITICAL = firewall |
| Contradiction MAJOR trigger | 2 | `director_ensemble.py:994` | 2+ MAJOR = firewall |
| Adaptive intro modifier | -5 | `director_grading.py:485` | arc_pos/total ≤ 0.2 |
| Adaptive climax modifier | +10 | `director_grading.py:489` | arc_pos/total ≥ 0.8 |
| Adaptive transition modifier | +3 | `director_grading.py:493` | 0.4 ≤ ratio ≤ 0.6 |
| Adaptive retry modifier | -3/retry | `director_grading.py:~520` | Per retry relaxation |

## Appendix B: Gate Basis Values

| gate_basis | Meaning | Set By |
|---|---|---|
| `director_primary_pass` | LLM said PASS, no gate overrode | `_derive_gate_basis()` |
| `director_primary_pass_with_fix` | LLM said PASS_WITH_FIX, fix_pack valid | `_derive_gate_basis()` |
| `director_primary_reject` | LLM said REJECT, no gate overrode | `_derive_gate_basis()` |
| `continuity_firewall` | Python firewall triggered on contradictions | `_derive_gate_basis()` |
| `quality_floor_fail` | PASS but score < quality_gate_score (90) | `_process_verdict()` or `_derive_gate_basis()` |
| `pass_with_fix_contract_{reason}` | PASS_WITH_FIX but fix_pack invalid | `_enforce_pass_with_fix_contract()` |
| `post_select_conflict` | Post-select continuity/history conflict | `_run_post_select_checks()` |

---

## 3-Pass Audit Record

### Pass 1. Evidence Collection
- Read all 5 primary scope files via subagent exploration (12,800+ LOC)
- Verified adaptive decision logic in `director_grading.py` (L461-580)
- Cross-referenced `validation.yaml` for quality_gate_score (L34: 90)
- Triangulated V60.97 behavior against fresh run P1-1 evidence

### Pass 2. Finding Classification
- Classified 3 P0 + 5 P1 findings with file:line anchors
- Verified no false PASS error paths exist (all errors default to REJECT)
- Confirmed stale claim status for TF-DG-03 (still present)
- Separated verdict-accuracy findings from observability findings

### Pass 3. Recommendation Validation
- Confirmed all fix types are within allowed set
- Verified fresh-run-before-fix = no is justified by P0-2 reproducing ep5 failure
- Checked that no recommendation changes verdict logic beyond the specific fix scope
- Confirmed no code changes made (survey-only)
