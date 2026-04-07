# Lane 5: Runtime Evidence / Operator Symptom / Test Codification

Date: 2026-04-06
Lane: 5 of 5
Status: survey complete
Mode: read-only survey, no code changes
Audit Authority: 3-pass audited before save

## Scope

Primary question: does live evidence support the claim that this is a real cross-stage operator-facing problem rather than a source-only hypothesis?

## Files Inspected

- `0_temp.txt` (runtime log, investment fiction project `01_투자물_골든_`)
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_continuity_pin_guard.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_continuity_modules.py` (L519-658)
- `tests/test_sweep32.py` (L25-36)
- `modules/domain/agents/state_extractor.py` (L100-175, L410-656 — LLM prompt, STATE LOCK formatter, Python fallback)
- `modules/domain/agents/arc_ensemble.py` (L380-491 — `_collect_non_wuxia_recovery_issues`)
- `modules/domain/agents/four_phase_arc_generator.py` (L1645-1699 — `_sanitize_injuries`, `_check_arc_end_state`)
- `modules/core/stage4_orchestrator.py` (L1050-1077 — chain_link extraction prompt)
- `modules/core/stage4_context_builder.py` (L1670-1689 — chain_link re-injection)
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

## Evidence

### E-1. Live Director REJECT — Investment Fiction Arc 4 (Anchor: `0_temp.txt` L505-517)

**This is the primary operator-facing symptom.**

Runtime session: genre = Investment Fiction, project = `01_투자물_골든_`, Arc 4 attempt 1.

Director REJECT (score=61) with two cited defects:
1. Mathematical contradiction in asset numbers (legitimate concern)
2. **V60.10 STATE LOCK violation** — the Director specifically states:

> `'V60.10 STATE LOCK'에서 명시한 주인공의 피로 상태 및 필수 회복 장면 지침을 완전히 무시하고, 주인공이 최상의 컨디션이라는 잘못된 전제로 시작하여 아크 간 연속성을 위반했습니다.`

Director correction demand:

> `[V60.10 STATE LOCK 준수] Arc 4 시작 시, 주인공의 상태를 '신경계 피로 Moderate'로 설정하고, 지침에 따라 휴식이나 회복을 묘사하는 장면을 초반에 포함하십시오. '신체적, 정신적으로 최상'이라는 서술은 삭제해야 합니다.`

**Key observation**: The fatigue label is "신경계 피로 Moderate" (nervous system fatigue, moderate severity). This is mental/psychological fatigue from weeks of high-stakes trading — genre-ordinary for investment fiction. An investment protagonist being tired after market activity does not warrant the same hard continuity obligation as a wuxia protagonist with broken bones.

After the retry where the fatigue constraint was honored, Arc 4 passed with score=95, then 100 on re-review. This means the system forced the LLM to write a recovery scene that wasn't narratively necessary for the genre, consuming an extra generation attempt (~10 minutes of compute).

### E-2. V60.10 STATE LOCK Prompt Wording — No Genre Distinction (Anchor: `state_extractor.py` L417-479)

The STATE LOCK prompt section uses REJECT-threat language:
```
🚨🚨🚨 [V60.10 STATE LOCK - 위반 시 즉시 REJECT] 🚨🚨🚨
```

Section "### 1. 부상/내공 상태 (RECOVERY REQUIRED)" lists injuries and internal energy without any genre-based softening. Section "### 4. 다음 Arc 필수 사항" renders `recovery_scene_required` as a hard gate:
```python
if constraints.get("recovery_scene_required"):
    lines.append(f"   ✅ 회복 장면 필수 (최소 {constraints.get('min_time_skip_days', 1)}일)")
```

The word "필수" (mandatory) combined with "위반 시 즉시 REJECT" creates an effectively hard-fail gate for all genres identically.

### E-3. Python Fallback Sets recovery_scene_required Without Genre Awareness (Anchor: `state_extractor.py` L529-534)

```python
recovery_needed = bool(injuries) or energy.get("current_percent", 100) < 50
result["next_arc_constraints"] = {
    "recovery_scene_required": recovery_needed,
    ...
}
```

This Python fallback triggers `recovery_scene_required = True` when:
- Any injury exists (regardless of genre-appropriateness)
- Internal energy < 50% (a wuxia-native concept applied universally)

For investment fiction, "internal_energy" is semantically nonsensical, yet the fallback still evaluates it.

The secondary Python fallback at L625 has the same pattern:
```python
"recovery_scene_required": bool(injuries) or loss_percent > 30,
```

### E-4. LLM Prompt Asks for recovery_scene_required Without Genre Guidance (Anchor: `state_extractor.py` L155-159)

The LLM extraction prompt includes:
```json
"next_arc_constraints": {
    "must_start_with": "다음 Arc 도입부 필수 요소",
    "recovery_scene_required": true/false,
    "min_time_skip_days": 숫자,
    ...
}
```

The prompt gives no guidance on when `recovery_scene_required` should be `true` vs `false`. The LLM is free to set it `true` for any perceived fatigue, including genre-ordinary stress in investment fiction.

### E-5. FourPhaseArcGenerator DOES Distinguish Mental Fatigue — But Only at Advisory Level (Anchor: `four_phase_arc_generator.py` L1688-1694)

```python
_mental_keywords = ("정신", "마모", "스트레스", "피로", "mental", "fatigue", "burnout")
_is_mental = any(k in ei.lower() for k in _mental_keywords)
if _is_mental:
    warnings.append(f"status_shadow 정신적 피로 잔류: '{ei}' (일상 휴식으로 자연 회복 가능)")
```

**This is the only existing genre-aware fatigue distinction in the codebase**, and it is:
- Advisory only (warning log, not a constraint modification)
- Located in FourPhaseArcGenerator, not in StateExtractor
- Not wired to `recovery_scene_required` — the constraint remains `True` regardless

The natural healing mechanism at L1655-1662 (`_sanitize_injuries`) blanket-clears all injuries across arc boundaries, which is good. But it operates on the `injuries` field, not on `recovery_scene_required` or the STATE LOCK prompt.

### E-6. Chain-Link Persistence Creates Sticky Fatigue Loop (Anchor: `stage4_orchestrator.py` L1058, `stage4_context_builder.py` L1677-1678)

Stage 4 extracts `physical_state` as free-text from manuscript:
```python
"physical_state": "부상/피로/상태 (정상이면 '정상')",
```

And re-injects it into next-episode context when non-normal:
```python
if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
    _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
```

If the V60.10 STATE LOCK forces the LLM to write "신경계 피로" into a manuscript, the chain_link persists it, and the next episode's context includes "신체 상태: 신경계 피로", creating a sticky loop where the fatigue is re-injected episode after episode until the LLM explicitly writes a recovery.

### E-7. ArcEnsemble Recovery Guard — Dual Binding with STATE LOCK (Anchor: `arc_ensemble.py` L386-491)

`_collect_non_wuxia_recovery_issues()` creates a secondary penalty layer:
- If fatigue tokens are detected in opening text AND no explicit recovery actions (eat/sleep/shower), penalty is issued
- If explicit recovery actions ARE present, the check passes

**The dual-binding problem**: STATE LOCK forces the LLM to mention fatigue → ArcEnsemble then penalizes if recovery is too vague → the candidate must include BOTH fatigue mention AND explicit recovery actions. For investment fiction, this creates a mandatory recovery beat that doesn't serve the genre.

### E-8. Prior Queue Docs Do Not Address This Symptom

- `0_0-stage2-contract-normalization-remediation-execution-ssot.md`: Addresses non-wuxia `internal_energy` field leakage and non-wuxia state noise (wuxia-only keys appearing in investment arcs). Does NOT address semantic overreach of recovery_scene_required or STATE LOCK prompt wording.
- `0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`: No mention of fatigue, recovery, STATE LOCK, or non-wuxia overreach.
- `0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`: No mention of fatigue, recovery, STATE LOCK, or non-wuxia overreach.

**This is a previously unaddressed gap in the normalization work.**

## Findings

### F-1. The Issue Is Genuinely Cross-Stage (Confidence: 97%)

The evidence chain spans:

| Stage | Role | Mechanism | Evidence |
|-------|------|-----------|----------|
| Stage 2 (StateExtractor) | Producer | `recovery_scene_required: True` set without genre awareness | E-3, E-4 |
| Stage 2 (STATE LOCK prompt) | Hardener | REJECT-threat language wraps soft fatigue as hard obligation | E-2 |
| Stage 2 (Director LLM) | Enforcer | REJECTs investment arc for not staging recovery scene | E-1 |
| Stage 2 (ArcEnsemble) | Double-binder | Penalizes vague recovery after STATE LOCK already demands it | E-7 |
| Stage 4 (chain_link) | Persister | `physical_state` free-text captures fatigue, re-injects into next episode | E-6 |

Stage 3 is NOT a direct amplifier for this specific symptom. It carries through `constraint_summary` and `tactical_doc` but does not independently harden fatigue constraints.

### F-2. The Complaint Is Best Described as "False Hardening + Genre Misclassification" (Confidence: 95%)

Two interlocking failures:

1. **False hardening**: Mental/psychological fatigue in non-wuxia genres is semantically equivalent to "the character had a busy week" — it does not require the same continuity obligation as physical injury. The V60.10 STATE LOCK prompt does not distinguish severity or genre-appropriateness.

2. **Genre misclassification**: The STATE LOCK mechanism was designed for wuxia-native concepts (injuries, internal energy, recovery days) and applied universally. For investment fiction, "신경계 피로 Moderate" is a normal character state, not a continuity defect.

### F-3. Natural Healing Is Recognized But Not Connected to the Constraint Flow (Confidence: 98%)

Two existing natural-healing mechanisms:
- `FourPhaseArcGenerator._sanitize_injuries()`: blanket-clears injuries across arc boundaries (good, but operates on `injuries` field only)
- `FourPhaseArcGenerator._check_arc_end_state()`: distinguishes mental fatigue from physical injury at advisory level (L1688-1694)

Neither flows into:
- `StateExtractor.recovery_scene_required`
- `StateExtractor._format_constraint_text()` (the STATE LOCK prompt)
- `ArcEnsemble._collect_non_wuxia_recovery_issues()`

### F-4. Tests Intentionally Lock In the Current Behavior (Confidence: 97%)

| Test | File | What It Locks |
|------|------|---------------|
| `test_evaluate_candidate_penalizes_implicit_non_wuxia_recovery_opening` | test_arc_ensemble_lane_a.py:509 | Vague recovery in investment fiction IS penalized |
| `test_evaluate_candidate_accepts_explicit_non_wuxia_recovery_opening` | test_arc_ensemble_lane_a.py:548 | Explicit recovery actions PASS the guard (escape hatch exists) |
| `test_evaluate_candidate_penalizes_non_wuxia_state_noise` | test_arc_ensemble_lane_a.py:478 | Wuxia-only fields in investment arcs are penalized |
| `test_state_extractor_validate_and_fix_result_handles_invalid_shapes` | test_sweep32.py:25 | Python fallback: malformed injuries → recovery_scene_required=False |
| `test_injury_warnings_only_fire_without_recovery_terms` | test_continuity_modules.py:519 | Injury warnings suppressed when recovery text present |
| `test_python_precheck_warns_on_rapid_recovery_in_opening` | test_continuity_modules.py:638 | Rapid recovery after physical injury generates warning |

The ArcEnsemble tests (509, 548) show the guard already has a well-formed escape hatch for explicit recovery actions. The issue is upstream: STATE LOCK forces the LLM to include fatigue mention, which then triggers the guard's fatigue detection path.

### F-5. Estimated Operator Cost per False Hardening Event

From the runtime log:
- Arc 4 attempt 1: REJECT (score=61), ~7-8 minutes generation + ~3 minutes Director review
- Arc 4 attempt 2: PASS_WITH_FIX (score=95), ~5 minutes generation + ~3 minutes Director review + ~2 minutes re-review
- Total wasted compute: ~10-13 minutes per false REJECT

For a batch of 5 arcs taking ~69 minutes total, one false REJECT represents ~15% overhead. Over a 60-arc investment-fiction project, if even 20% of arcs trigger the same pattern, the cumulative cost is significant.

## Open Questions

1. **How often does the LLM set `recovery_scene_required: True` for non-wuxia works?** The runtime evidence shows one clear case, but a broader audit of saved state-extraction results across multiple projects would quantify frequency. (Not inspectable from code alone — requires DB or artifact audit.)

2. **Does the Director's REJECT always cite STATE LOCK for mental fatigue, or only when the gap between fatigue-state and opening narrative is large?** The single runtime sample shows the Director citing STATE LOCK when the tactical doc describes the protagonist as "최상의 컨디션" (peak condition) while STATE LOCK says "신경계 피로 Moderate". If the opening merely omits an explicit recovery scene but doesn't contradict the fatigue, the Director might only issue PASS_WITH_FIX instead of REJECT. (Requires more runtime samples to confirm.)

3. **How many chain-link entries in the DB currently carry non-"정상" physical_state for non-wuxia projects?** This would indicate whether the sticky persistence loop (E-6) is an active problem or a theoretical one. (Requires DB audit.)

## Provisional Severity

**P1** — Real operator-facing false hard-fail

Justification:
- Live Director REJECT observed in actual production run
- The REJECT is driven by genre-inappropriate fatigue classification
- The system forces recovery scenes that don't serve the genre
- Measurable compute and operator-time cost
- The chain-link persistence loop creates a sticky multi-episode obligation

Confidence: 95%

Upgrading to P0 is not justified because:
- The system does eventually pass after retry (self-correcting, albeit wastefully)
- No data corruption occurs
- Natural healing mechanisms exist but are disconnected from the constraint flow

## Recommended Merge Notes

### For Lane 1 (Stage2 Origin)
- Confirm whether `StateExtractor._format_constraint_text()` always uses REJECT-threat wording regardless of genre
- Confirm whether the LLM extraction prompt for `next_arc_constraints` has any genre-awareness guidance
- Confirm whether `recovery_scene_required` is set by LLM response vs Python fallback in the observed runtime case

### For Lane 2 (Stage3 Carryover)
- Stage 3 is likely a passive carrier for this specific symptom — runtime evidence does not show Stage 3 independently hardening fatigue constraints

### For Lane 3 (Stage4 Opening Authority)
- Confirm whether Stage 4 preflight adds any independent fatigue-hardening pressure beyond what Stage 2 STATE LOCK already provides

### For Lane 4 (Stage4 Chain-Link Post-Pass)
- Confirm whether `physical_state` chain-link entries for non-wuxia projects carry fatigue labels that re-enter the next episode's context as mandatory state

### For Merged Survey
- The most likely future repair shape is a **policy split between hard injury and soft fatigue** combined with a **Stage2 + Stage4 dual-owner patch**:
  1. Stage 2: Genre-aware `recovery_scene_required` logic — physical injury remains hard, mental fatigue becomes advisory
  2. Stage 2: STATE LOCK prompt severity split — REJECT-threat for physical injury, advisory for soft fatigue
  3. Stage 4: chain_link `physical_state` normalization — mental fatigue not persisted as non-"정상"
- The FourPhaseArcGenerator's existing mental-fatigue distinction (L1688-1694) can serve as the model for the upstream fix
- Tests in test_arc_ensemble_lane_a.py will need updating if the upstream constraint flow changes

## 3-Pass Audit Record

Pass 1:
- All 7 survey questions from the order are addressed
- Evidence is anchored to specific file:line references
- Findings stay within inspected evidence

Pass 2:
- Runtime evidence from 0_temp.txt matches the operator concern described in the audit order
- Test references verified against actual test file contents
- Production code references verified against live source

Pass 3:
- Provisional severity is bounded and justified
- Open questions are explicit about what would change the assessment
- Merge notes are concrete and actionable for other lanes

Estimated confidence: 96%
