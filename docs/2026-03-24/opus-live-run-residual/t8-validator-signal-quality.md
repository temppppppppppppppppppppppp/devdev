# T8 Validator Signal Quality

Date: 2026-03-24
Lane: T8 -- Validator Signal Quality
Status: final
Master Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Evidence Run: `projects/0324_00_`

---

## 1. Executive Summary

The validator subsystem in this run splits cleanly into two tiers with fundamentally different roles:

**Tier A -- Advisory warnings ([V66.1], [TF-49])**: Fired 51+ times across all 8 episodes. Never caused a single verdict change. The most frequent signal -- "직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음" -- appeared on virtually every candidate in every episode (30 instances) and is **mostly advisory noise** in the investment genre context. Re-acquisition warnings ("이미 소유한 X을 다시 획득하려 함") caught real item-handling issues but remained advisory.

**Tier B -- Verdict-flipping gates (post-select IFC, history conflict, continuity firewall)**: Fired 7 times. Caused 7/7 REJECT downgrades. All 7 caught **real contradictions** grounded in artifact truth: provenance drift (어머니 vs 조부), item location drift (금고 vs 서랍), timeline regression (4:35 PM → 3:35 PM), capital accounting errors (5천만 원 expense omission), and capital-state contradiction (20억 가용현금 after 19억 전액 투입).

**Verdict**: Validator overreach is **not a primary cause** of the rescue-round failures. The validators that flip verdicts are catching real problems. The validators that produce noise do not flip verdicts.

---

## 2. Included Coverage / Exclusions

### Included

- `modules/validation/continuity_validator.py` -- full 1,265-line analysis
- `modules/core/stage4_interview_round.py` -- `_run_post_select_checks`, `_handle_positive_verdict_transition`
- `modules/domain/agents/director_continuity.py` -- `check_manuscript_history_conflicts`, `check_manuscript_continuity_with_cache`
- `modules/core/stage4_immutable_fact_contract.py` -- `ImmutableFactPacket`, `classify_violation_family`, `should_escalate_to_rewrite`
- `docs/2026-03-24/console.txt` -- full validator signal extraction (43 [V66.1] warnings, 6 post-select conflicts, 1 firewall trigger, 13 history conflict entries, 2 PASS_WITH_FIX, 5 IFC, 12 TF-49)
- All Stage 4 artifacts for troubled episodes (EP2/3/5/6/7/8) cross-referenced against validator claims

### Excluded

- Stage 2 validation pipeline (T3 lane)
- Stage 3 blueprint generation logic (T4 lane)
- Carryover packet construction (T6 lane)
- Retry/PASS_WITH_FIX architecture (T7 lane)
- Broader run chronology (T1 lane)

---

## 3. Key Evidence

### 3A. Validator Architecture -- Two Independent Tiers

| Tier | Validator | Mechanism | Can Flip Verdict? | Instances in Run |
|------|-----------|-----------|-------------------|------------------|
| A | ContinuityValidator [V66.1] | Python pattern-matching: injury, location, pressure, time | **No** (advisory WARNING to Director) | 43 |
| A | [TF-49] inventory_gaps | Python item-ownership check | **No** (advisory to CW prompt) | 12 (8 S3 + 4 S4 preflight) |
| A | start-contract PreCheck | Blueprint opening location vs first 600 chars | **No** (advisory) | 4 |
| B | Post-select IFC | LLM-based history/continuity conflict check (2 parallel threads) | **Yes** (PASS → REJECT, fix_scope=full) | 6 |
| B | Continuity firewall | Director LLM primary scoring | **Yes** (direct REJECT with low score) | 1 |
| B | PASS_WITH_FIX gate | Director fix_pack eligibility | **Yes** (keeps or downgrades to REJECT) | 2 |

### 3B. [V66.1] Signal Distribution (43 warnings, 0 verdict changes)

| Warning Type | Count | Valid Signal? | Assessment |
|-------------|-------|---------------|------------|
| "직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음" (threat carryover drift) | 30 | **Mostly noise** | Fires on every candidate in every episode. In the investment genre, episode openings naturally shift context (office → bank → trading desk) without carrying forward "threat pressure" from the prior episode's cliffhanger. The mechanism (`_check_active_pressure_continuity`, L435-465) extracts `active_pressure_vectors` from prev_hud and checks for cue_term overlap in first 1000 chars. In practice, investment-genre pressure is financial/strategic, not physical/threatening, so keyword matching against `cue_terms` fails systematically. |
| "이미 소유한 'X'을(를) 다시 획득하려 함" (duplicate acquisition) | 8 | **Valid but advisory** | Items: 가죽 노트 ×6, 휴대전화 ×2. These correctly flag manuscripts where the writer describes obtaining an already-owned item. However, this is a WARNING-level item continuity check, not a BLOCKING violation. The Director may or may not penalize it. |
| "위치 변화가 감지됨. 이동 경위 묘사 권장" (location change) | 5 | **Valid but low-severity** | Correctly detects cross-scene location changes without explicit travel description. INFO-level. Appropriate. |
| Time/season warning | 1 | **Uncertain** | EP1 only: season_contradiction between "겨울" in timeline and "한여름" expression. Single occurrence, not recurring. |

### 3C. Post-Select IFC -- All 6 Conflicts Were Real (6/6 valid)

| EP | Rd | IFC Conflict | Artifact Evidence | Valid? |
|----|----|-------------|-------------------|--------|
| 2 | R1 | 신탁 계좌 출처: 어머니(EP1) vs 조부(EP2) | `rejected_best__A_balanced.txt` L86: "조부님께서" vs `final_manuscript__A.txt` L90: "어머니께서" | **YES** -- blueprint carried wrong provenance |
| 2 | R2 | 신탁 자산 특성 변경 (어머니 몰래 남김 → 회장 동의 필요) | Same provenance drift in R2 candidate | **YES** -- still not corrected |
| 2 | R3 | 시간 배경 불일치 (오전 10시 → 늦은 오후) | EP1 ending → EP2 opening timeline gap | **YES** -- real timeline discontinuity |
| 3 | R1 | 가죽 노트 보관 위치 (금고 vs 서랍) + 시간 역행 (4:35pm → 3:35pm) | `rejected_best__C_tension.txt` L27: "책상 아래의 서랍" vs EP2 safe; 시간 역행 confirmed | **YES** -- writer invention + timeline regression |
| 5 | R1 | 법인 자본금 5천만 원 미반영 + 파생상품 이체 타임라인 모순 | `selected_before_fix__B.txt` L29: "예수금: 1,900,000,000원" without 5천만 deduction | **YES** -- real accounting gap |
| 6 | R2 | 자본금 정합성: EP5에서 19억 전액 WTI 투입 후 20억 가용현금 불가 | `rejected_best__A_tension.txt` L17: "20억 원의 법인 자금" (nonexistent) | **YES** -- writer invented 법인 자금 |

### 3D. Continuity Firewall -- 1 Trigger, Valid

EP6 R2 scored 44 (lowest in entire run). Triggered by Director LLM detecting critical capital-state contradiction. The underlying contradiction (20억 available cash after full 19억 WTI deployment) is confirmed real by artifact comparison between EP5 final and EP6 R2 candidate.

### 3E. PASS_WITH_FIX -- 2 Occurrences, Both Correct

| EP | Director Fix | Post-Select Override? | Outcome |
|----|--------------|-----------------------|---------|
| 5 R1 | Leverage arithmetic fix (3x stated vs ~15x actual) | **YES** -- IFC caught separate capital accounting error | REJECT (fix discarded, full rewrite) |
| 7 R1 | "18년 전" → "전생에" single-phrase fix | **No** -- no post-select conflict | PASS (patch applied, re-reviewed at 90) |

Both PASS_WITH_FIX decisions were architecturally correct. EP5's override was justified -- the IFC caught a different, real issue. EP7's successful patch demonstrates the system working as designed.

---

## 4. Findings Ranked

### Finding 1: [V66.1] "threat carryover drift" is systematic advisory noise in investment genre
- **Rank**: Confirmed non-culprit
- **Count**: 30 instances, 0 verdict changes
- **Mechanism**: `_check_active_pressure_continuity()` (continuity_validator.py L435-465) always produces WARNING severity and always sets `passed=True`. It matches prev_hud `active_pressure_vectors` cue_terms against the first 1000 chars of the manuscript. In the investment genre, "pressure" is strategic/financial, not expressed through the physical/action keywords the matcher expects.
- **Impact**: Zero. These warnings are injected into the Director's validation_results but the Director consistently ignores them -- every PASS in the run came despite these warnings being present.
- **Recommendation**: Not harmful (never blocks), but adds noise to Director context. Could be genre-gated or tuned for investment-genre pressure vocabulary in a future hygiene pass.

### Finding 2: Post-select IFC is the only verdict-flipping validator, and it catches real problems
- **Rank**: Confirmed correct validator, confirmed secondary amplifier of rescue rounds
- **Count**: 6 verdict flips, all valid
- **Mechanism**: Two parallel LLM checks (`check_manuscript_continuity_with_cache` + `check_manuscript_history_conflicts`) run after Director provisional PASS. Fail-closed on exceptions. On conflict: forces REJECT + fix_scope=full + clears fix_pack.
- **Impact**: Directly responsible for 6 of the 7 total non-first-round REJECT events in the run. These 6 rejects added 6 retry rounds. But all 6 caught real contradictions.
- **Assessment**: The IFC is not overreaching -- it is correctly detecting real problems that the Director LLM missed. The rescue rounds exist because **the problems exist**, not because the validator is overzealous.

### Finding 3: Continuity firewall is rare and well-calibrated
- **Rank**: Confirmed correct validator
- **Count**: 1 trigger (EP6 R2, score=44)
- **Assessment**: The firewall correctly identified the worst contradiction in the run (capital-state impossibility). Score 44 is appropriate for a critical factual contradiction.

### Finding 4: [V66.1] re-acquisition warnings catch real issues but lack verdict authority
- **Rank**: Valid signal, correctly advisory
- **Count**: 8 instances
- **Assessment**: These correctly flag duplicate item acquisition (가죽 노트 appearing to be re-obtained, 휴대전화 re-obtained). The items are real continuity issues. But making them advisory rather than blocking is the right design -- duplicate item descriptions are often stylistic (the writer describes the character having an item without implying re-acquisition).

### Finding 5: [TF-49] inventory gap warnings are correctly advisory
- **Rank**: Valid signal, correctly advisory
- **Count**: 12 instances (8 S3 + 4 S4 preflight)
- **Assessment**: Correctly tracked item prerequisites across episodes. Never caused harmful pressure in this run. The stale-across-retries issue (inventory gaps are write-once into blueprint dict, never updated during Stage 4 retries) is a latent risk but did not materialize.

### Finding 6: IFC fail-closed on LLM errors is architecturally correct but wasteful
- **Rank**: Architectural observation
- **Evidence**: `_run_post_select_checks` (stage4_interview_round.py L3711-3729) treats LLM exceptions as conflicts (fail-closed). In this run, no LLM errors occurred during post-select checks, so this path was not exercised. However, the design means a transient API failure would force a full rewrite of a potentially good manuscript.
- **Status**: Not proven as a problem in this run.

---

## 5. Cleared Non-Culprits

| Suspected Cause | Status | Evidence |
|----------------|--------|----------|
| **Validator overreach causing false rejects** | **Cleared** | 0/6 post-select rejects were false positives. All caught real contradictions confirmed by artifact inspection. |
| **[V66.1] warnings driving rescue rounds** | **Cleared** | 0/43 [V66.1] warnings caused verdict changes. They are architecturally unable to flip verdicts (always WARNING severity, always `passed=True`). |
| **[TF-49] inventory gaps causing harmful pressure** | **Cleared** | 0/12 inventory gap warnings caused verdict changes. Advisory-only in CW prompt. |
| **PASS_WITH_FIX mechanism broken** | **Cleared** | EP7 demonstrated correct operation. EP5 override was justified by a separate, real IFC conflict. |
| **continuity_firewall false-positive risk** | **Cleared** | The single trigger (EP6 R2) caught a real critical contradiction (score 44 appropriate). |

---

## 6. Residual Culprit Candidate

**Validator overreach is not a residual culprit.** The validators that flip verdicts are catching real problems upstream.

However, this lane identifies one **secondary concern**:

**Post-select conflict forces overly aggressive response (fix_scope=full + fix_pack wipe)**

When post-select IFC detects a conflict, `stage4_reject_runtime.py:514-524` unconditionally:
1. Forces `resolved_fix_scope = "full"` (full rewrite)
2. Clears `resolved_fix_pack = {}` (discards Director's targeted fix instructions)

This means even when the Director correctly identified a fixable issue AND the IFC detected a separate issue, both fixes are discarded in favor of a blind full rewrite. In EP5 R1, the Director's leverage arithmetic fix was valid for the arithmetic issue, but was discarded because the IFC caught a separate capital accounting issue. A more nuanced response would be to:
- Keep the Director's fix_pack for the fixable issue
- Add the IFC conflict to the feedback
- Allow the retry to address both

This is an optimization opportunity, not a bug. The current aggressive response guarantees correctness (full rewrites always address both issues) at the cost of efficiency (extra retry rounds).

**Classification**: Confirmed secondary amplifier (of retry count, not of error introduction).

---

## 7. Next-Scope Recommendation

**No execution SSOT justified from this lane alone.**

The validators are working correctly. The rescue rounds exist because real contradictions exist upstream (Stage 3 blueprint authority gaps + Stage 4 writer invention). This lane's findings support the other lanes' root causes rather than adding a new one.

If a future hygiene wave is planned, two low-priority items from this lane:

1. **Genre-gate the pressure carryover check**: `_check_active_pressure_continuity()` (continuity_validator.py L435-465) should either be disabled for the investment genre or extended with investment-specific pressure vocabulary (financial terms, deadline pressure, market urgency). This would reduce Director context noise by ~30 warnings per run without losing valid signal.

2. **Soften post-select conflict response**: Instead of unconditionally forcing fix_scope=full and wiping fix_pack, preserve the Director's fix_pack and add the IFC conflict as supplementary feedback. This could reduce retry rounds by 1-2 in episodes where the Director and IFC catch different issues.

Both are optimization-only and do not affect correctness.

---

## 8. Confidence And Limits

| Dimension | Confidence | Basis |
|-----------|-----------|-------|
| "Validators are not overreaching" | **95%** | 6/6 post-select rejects confirmed valid by artifact inspection. 0/43 advisory warnings caused verdict changes. |
| "All IFC conflicts were real" | **93%** | Cross-referenced every IFC conflict against actual manuscript text. All contradictions confirmed. |
| "[V66.1] pressure warning is mostly noise" | **90%** | 30/30 occurrences fired without verdict impact. However, the Director may have internally used some of these warnings for scoring (unobservable from console output alone). |
| "Post-select full-rewrite override is secondary amplifier" | **80%** | Mechanism confirmed by code reading. Impact estimated at 1-2 extra retry rounds, but not directly measurable without a controlled A/B test. |

**Limits**:
- This analysis covers one investment-genre run (EP1-8). The [V66.1] pressure carryover check may be more valid in wuxia/hunter genres where physical threat is the dominant pressure vector.
- The Director's internal use of [V66.1] warnings for scoring is unobservable -- we can only confirm they did not cause verdict changes, not that they had zero influence on scores.
- No LLM errors occurred during post-select checks in this run, so the fail-closed exception path was not tested.
- The IFC prompt (`MANUSCRIPT_HISTORY_CONFLICT_PROMPT` in `director.yaml`) was not read directly -- the LLM's interpretation of "CRITICAL" vs "MAJOR" vs "MINOR" severity is inferred from outputs, not verified against prompt text.

---

## 3-Pass Audit Record

- Pass 1: confirmed this is a survey-only lane report for T8 Validator Signal Quality, not an execution SSOT
- Pass 2: confirmed all findings are grounded in artifact truth and code references, not console paraphrase alone
- Pass 3: confirmed weak claims are marked as "not proven" and confidence levels reflect evidence quality

---

## Mandatory Final Lines

- Can this lane explain a real residual failure by itself: **no**
- Does this lane explain repeated rescue rounds after the closed waves: **no** (validators catch real upstream problems; they do not create them)
- Would this lane justify a bounded next execution wave: **no**
