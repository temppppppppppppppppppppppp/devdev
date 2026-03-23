Date: 2026-03-23
Status: final
Document Type: R2 Q3 verdict accuracy evidence manifest
Terminal: T3
Source Report: `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md`
R1 Evidence: `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md`

---

## 1. Code-Fix Verification Evidence

### P0-1 Resolved: Adaptive Decision Guard
- **Before**: `director_ensemble.py` R1 L1109 — bare call, no exception handler
- **After**: `director_ensemble.py:1168-1183` — try/except with `[Q3-T1]` marker
- **Fallback**: `{"decision": state.original_verdict, "adjusted": False, "reason": f"grading_error: {_adp_exc}"}`
- **Verification method**: direct source read

### P1-1 Resolved: ep_type Forwarding
- **Callee signature**: `director_grading.py:555-558` — `def apply_adaptive_decision(self, score, original_decision, arc_pos=1, total_eps=5, retry_count=0, ep_type="normal")`
- **Call site**: `director_ensemble.py:1169-1176` — `ep_type=ep_type` at L1175
- **Forwarding**: `director_grading.py:560` — `self.get_adaptive_threshold(ep_type=ep_type, ...)`
- **Modifiers confirmed**: `director_grading.py:518` climax=+10, L522 intro=-5, L526 transition=-3
- **Verification method**: direct source read

### P1-2 Resolved: Firewall Observability
- **Method**: `director_ensemble.py:1023-1089` — `_apply_contradiction_firewall_gate()`
- **Logging**: L1069 `logging.warning(f" [V75-C] {state.firewall_reason} → REJECT 강제")` (CRITICAL path)
- **Logging**: L1072 `logging.warning(f" [V75-C] {state.firewall_reason} → REJECT 강제")` (MAJOR path)
- **Operator log**: L1078-1082 `_operator_log` integration
- **Summary loop**: L1084-1089 contradiction detail lines
- **Verification method**: direct source read

### P1-3 Resolved: Post-Select Downgrade Logging
- **Individual continuity**: `stage4_interview_round.py:3648` — `"[A-3] Post-select continuity conflict: {_conflict_msg}"`
- **Individual history**: `stage4_interview_round.py:3662` — `"[A-3] Post-select history conflict: {_conflict_msg}"`
- **Aggregate**: `stage4_interview_round.py:3671-3673` — `"[A-3] {count} post-select conflicts detected -> downgrade to REJECT"`
- **Error escalation**: `stage4_interview_round.py:3681-3683` — `error_category = "LOGIC_ERROR"` for V75-D/V75-B
- **Previous attempt dict**: L3694-3721 — 12+ structured fields including `provisional_pass_downgrade: True`
- **Verification method**: direct source read

## 2. V60.97 CONDITIONAL_PASS Downstream Path Evidence (N-1)

### Step 1: Score Reset
- **File:line**: `director_ensemble.py:941-942`
- **Code**: `score = 50; original_verdict = "CONDITIONAL_PASS"`
- **Trigger**: `v60_97_swapped = True` (L912)

### Step 2: Adaptive Decision
- **File:line**: `director_ensemble.py:1169-1176`
- **Input**: `score=50, original_verdict="CONDITIONAL_PASS"`
- **Output**: `adaptive_result` with `threshold_used` from `director_grading.py`

### Step 3: CONDITIONAL_PASS Resolution
- **File:line**: `director_ensemble.py:1187-1198`
- **Branch**: `elif state.v60_97_swapped:` at L1191
- **If score >= threshold**: `final_verdict = "CONDITIONAL_PASS"` at L1194
- **If score < threshold**: `final_verdict = "REJECT"` at L1197

### Step 4: Normalization
- **File:line**: `stage4_interview_round.py:1824-1858` — `_normalize_director_gate_semantics()`
- **L1833-1838**: `final_verdict = str(director_result.get("final_verdict") or ...)` → extracts "CONDITIONAL_PASS"
- **L1843-1851**: gate_basis derivation — "CONDITIONAL_PASS" matches no positive case → `else: gate_basis = "director_primary_reject"` at L1851
- **L1857**: `director_result["verdict"] = final_verdict` → "CONDITIONAL_PASS"

### Step 5: Verdict Processing
- **File:line**: `stage4_interview_round.py:3773-3812` — `_process_verdict()`
- **L3774**: `if verdict == "PASS" and score < quality_gate_score` → False (not "PASS")
- **L3787**: `if verdict in ("PASS", "PASS_WITH_FIX")` → False ("CONDITIONAL_PASS" not in set)
- **L3812**: `return None, director_feedback, previous_attempt, trace_meta` → **REJECT path**

### Conclusion
CONDITIONAL_PASS at L1194 is **never recognized as a positive verdict** by downstream code. The V60.97 threshold comparison at L1191-1198 has no functional effect.

## 3. Adaptive Threshold Calculation Evidence

### Constants
- `_ADAPTIVE_BASE_MIN = 45` (`director_grading.py:14`, config: `adaptive_grading.base_score_min`)
- `_ADAPTIVE_BASE_MAX = 85` (`director_grading.py:15`, config: `adaptive_grading.base_score_max`)
- `base_pass_threshold = 60` (`validation.yaml:35`, via `director_grading.py:477`)

### Modifiers (director_grading.py)
- **Position**: L484-489 — intro(ratio≤0.2): -5, climax(ratio≥0.8): +10
- **Transition**: L493 — ratio 0.4-0.6: -3
- **Retry**: L530-535 — retry≥3: -10, retry≥2: -5 (NOT linear)
- **Floor/Ceiling**: L537-538 — `base = max(45, min(85, base))`

### Score=50 vs Threshold Matrix

| ep_type | retry | base | modifiers | raw | floor | threshold | score=50 | result |
|---------|-------|------|-----------|-----|-------|-----------|----------|--------|
| normal | 0 | 60 | 0 | 60 | max(60,45) | 60 | 50<60 | REJECT |
| normal | 2 | 60 | -5 | 55 | max(55,45) | 55 | 50<55 | REJECT |
| normal | 3 | 60 | -10 | 50 | max(50,45) | 50 | 50>=50 | CONDITIONAL_PASS* |
| intro | 0 | 60 | -5 | 55 | max(55,45) | 55 | 50<55 | REJECT |
| intro | 2 | 60 | -5-5 | 50 | max(50,45) | 50 | 50>=50 | CONDITIONAL_PASS* |
| intro | 3 | 60 | -5-10 | 45 | max(45,45) | 45 | 50>=45 | CONDITIONAL_PASS* |
| climax | 0 | 60 | +10 | 70 | max(70,45) | 70 | 50<70 | REJECT |
| climax | 3 | 60 | +10-10 | 60 | max(60,45) | 60 | 50<60 | REJECT |

*CONDITIONAL_PASS → effectively REJECT per N-1

## 4. Fresh-Run Evidence Anchors

### runtime_audit.jsonl (Q3 relevant entries)

| ep | round | score | gate_basis | key observations |
|----|-------|-------|------------|-----------------|
| 3 | 1 | 80 | director_primary_reject | "씬 구분 미반영", fix_scope=partial |
| 3 | 2 | 0 | (empty) | Parsing failure, missing_fix_pack |
| 3 | 3 | 76 | director_primary_reject | "씬 구조 미구현", fix_scope=full, pathology_repeat |
| 3 | 4 | 98 | post_select_conflict | PASS(98) → timeline conflict → REJECT |
| 3 | 5 | (not in pathology) | — | PASS accepted (no pathology signal) |

### V60.97 Occurrence
- `console.txt`: 0 matches for "V60.97", "v60_97", "후보 교체"
- `runtime_audit.jsonl`: 0 matches for "v60_97"
- **V60.97 was NOT triggered in 0_0323 run**

### Console.txt Key Anchors (from T7 cross-reference)
- L662-989: ep3 all 5 rounds
- L672-677, L762-767, L844-848: Scene detection FP "0/5 씬만 완성"
- L902-913: Round 4 post-select downgrade

## 5. Source Files Examined

| File | Lines | R2 Read Depth |
|------|-------|--------------|
| `modules/domain/agents/director_ensemble.py` | ~2,210 | Full (via subagent) |
| `modules/domain/agents/director_grading.py` | ~600 | Key methods (L461-581) |
| `modules/core/stage4_interview_round.py` | ~5,900 | Key methods (L1824-1858, L3670-3812) |
| `modules/core/stage4_director_runtime.py` | ~1,500 | Reference only |
| `config/settings/validation.yaml` | ~200 | L34-35 (thresholds) |
| `projects/0_0323/logs/runtime_audit.jsonl` | 20 entries | grep for Q3 events |
| `docs/2026-03-23/console.txt` | 1,011 lines | Cross-reference via T7/T10 |
