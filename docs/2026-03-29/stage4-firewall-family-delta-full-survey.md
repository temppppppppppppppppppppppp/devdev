## Stage4 Firewall Family Delta Full Survey

Date: 2026-03-29
Status: draft-for-audit
Track: system
Type: bounded full-survey
Topic Slug: stage4-firewall-family-delta
Audit Order: `docs/2026-03-29/stage4-firewall-family-delta-full-survey-audit-order.md`
Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`

---

### 1. Scope and Intent

This survey freezes the **pre-patch EP3 firewall family baseline** so the patched EP3 canary can be judged by exact fingerprint delta instead of vague prose similarity.

The survey does not conclude whether the patch succeeded. It only builds the `before` baseline.

**Pre-patch canary sources** (ran with unpatched or earlier-patched blueprint):
- `canary_0329_feedback_windowing_check` — EP3: 8 rounds (R0-R7), PASS at R7
- `canary_0329_scope_sink_semantics_check` — EP3: 10+ rounds (R0-R9), did not reach clean PASS within observed data

**Post-patch canary** (for naming alignment only, not used as primary evidence):
- `canary_0329_retry_loop_compression_check` — EP3: 2 rounds (R0-R1), PASS at R1

---

### 2. Evidence Sources

| Source | Role | EP3 Rounds |
|--------|------|------------|
| `projects/canary_0329_feedback_windowing_check/logs/episode_production.jsonl` | Pre-patch primary — round verdicts and gate metadata | 8 (R0-R7) |
| `projects/canary_0329_feedback_windowing_check/logs/runtime_audit.jsonl` | Pre-patch primary — pathology fingerprints with exact fields | 7 pathology signals |
| `projects/canary_0329_scope_sink_semantics_check/logs/episode_production.jsonl` | Pre-patch secondary — extended oscillation pattern | 10+ (R0-R9) |
| `projects/canary_0329_scope_sink_semantics_check/logs/runtime_audit.jsonl` | Pre-patch secondary — pathology fingerprints | 13 pathology entries |
| `projects/canary_0329_feedback_windowing_check/logs/session/ui_events.jsonl` | V75-D/V75-B event timestamps | 4 escalation events |
| `modules/core/stage4_outcome_runtime.py` L596-627 | Code: logic_error_streak counting rules |
| `modules/core/stage4_reject_runtime.py` L500-568 | Code: A-4 continuity replay enforcement |

---

### 3. Pre-Patch EP3 Round Map

#### 3.1 Canary A: `feedback_windowing_check` (8 rounds)

| Round | Verdict | Score | Gate Basis | Firewall | Reject Bucket | Error Category | Contradiction Type | Pathology Fingerprint |
|-------|---------|-------|-----------|----------|---------------|----------------|--------------------|----------------------|
| R0 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | — | — | `structure_error\|contradiction:아이템\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R1 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | LOGIC_ERROR | 아이템 | `structure_error\|contradiction:아이템\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R2 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | LOGIC_ERROR | 아이템 | `structure_error\|contradiction:아이템\|continuity_firewall\|fix_pack:scene_model_target` |
| R3 | REJECT (PASS→downgrade) | 94 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R4 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | LOGIC_ERROR | 타임라인 | `structure_error\|contradiction:타임라인\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R5 | REJECT (PASS→downgrade) | 98 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R6 | REJECT | 44 | `continuity_firewall` | TRUE | `post_select_conflict` | LOGIC_ERROR | 타임라인 | `post_select_conflict\|contradiction:타임라인\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R7 | **PASS** | 100 | `director_primary_pass` | FALSE | — | — | — | — |

**V75 escalation events:**
- V75-D (inplace BP patch): after R0, success, change_ratio=0.2902
- V75-B (full BP regen): after R2, success

**Oscillation pattern**: `continuity_firewall` → `post_select_conflict` → `continuity_firewall` repeating (R0-R6)

#### 3.2 Canary B: `scope_sink_semantics_check` (10+ rounds)

| Round | Verdict | Score | Gate Basis | Firewall | Reject Bucket | Error Category | Contradiction Type | Pathology Fingerprint |
|-------|---------|-------|-----------|----------|---------------|----------------|--------------------|----------------------|
| R0 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | — | 타임라인 | — |
| R1 | REJECT (PASS→downgrade) | 96 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R2 | REJECT | 44 | `continuity_firewall` | TRUE | `structure_error` | LOGIC_ERROR | 타임라인 | `structure_error\|contradiction:타임라인\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R3 | REJECT (PASS→downgrade) | 91 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R4 | REJECT | 44 | `continuity_firewall` | TRUE | `post_select_conflict` | LOGIC_ERROR | 타임라인 | `post_select_conflict\|contradiction:타임라인\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R5 | REJECT | 84 | `director_primary_reject` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | 고유명사 | `constraint_violation\|contradiction:고유명사\|fix_pack_ready` |
| R6 | REJECT (PASS→downgrade) | 91 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R7 | REJECT | 44 | `continuity_firewall` | TRUE | `post_select_conflict` | LOGIC_ERROR | 타임라인 | `post_select_conflict\|contradiction:타임라인\|continuity_firewall\|fix_pack:missing_fix_pack` |
| R8 | REJECT (PASS→downgrade) | 95 | `post_select_conflict` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | — | `constraint_violation\|fix_pack:missing_fix_pack` |
| R9 | REJECT | 84 | `director_primary_reject` | FALSE | `constraint_violation` | CONSTRAINT_VIOLATION | 타임라인 | `constraint_violation\|contradiction:타임라인\|fix_pack:scene_model_target` |

**V75 escalation events:**
- V75-D (inplace BP patch): after R0, snapshot persisted (runtime_audit entry with candidate_key=V75-D|blueprint_inplace)
- V75-B: not observed in this canary's runtime_audit data

**Oscillation pattern**: Same `continuity_firewall` ↔ `post_select_conflict` oscillation, plus `director_primary_reject` (R5, R9)

#### 3.3 Cross-Canary Round Count Comparison

| Canary | EP3 Rounds | Final Outcome | V75-D | V75-B |
|--------|-----------|---------------|-------|-------|
| feedback_windowing (pre-patch A) | **8** | PASS (R7, score 100) | YES (R0→R1) | YES (R2→R3) |
| scope_sink_semantics (pre-patch B) | **10+** | Did not reach clean PASS within data | YES (R0→R1) | Not observed |
| retry_loop_compression (post-patch) | **2** | PASS (R1, score 98) | YES (R0→R1) | Not needed |

---

### 4. Old Firewall/Post-Select Family Matrix

Based on raw pathology fingerprints extracted from both pre-patch canaries, the old EP3 pattern contains exactly **5 distinct families**.

#### Family F-1: `continuity_firewall + structure_error + 아이템`

**Raw fingerprint**: `structure_error|contradiction:아이템|continuity_firewall|fix_pack:missing_fix_pack`

| Field | Value |
|-------|-------|
| gate_basis | `continuity_firewall` |
| reject_bucket | `structure_error` |
| error_category | `LOGIC_ERROR` |
| contradiction_type | `아이템` |
| firewall_triggered | TRUE |
| score | 44 (capped) |
| fix_scope | `full` |
| authoritative_fix_scope | `full` |
| repair_scope | `full` |
| fix_pack_ready | FALSE |
| fix_pack_reason | `missing_fix_pack` or `scene_model_target` |

**Occurrence**: Canary A R0-R2 (3 consecutive rounds, early phase)

**fix_scope_reasoning extracts**:
- R1: "에피소드 1에서 이미 20억 자본금 확보 및 OTP 수령이 완료된 것으로 서술되었으나, 이번 화의 전체 줄거리가 자본금을 '이제부터' 확보하는 과정으로 짜여 있어"
- R2: "에피소드 1에서 주인공이 이미 법인 인감도장을 확보했음에도, 이번 화의 핵심 목표를 '인감도장 확보'로 설정하여 치명적인 연속성 오류"
- R3: "Blueprint 자체가 이전 원고(EP 1)에서 확립된 사실과 정면으로 충돌하는 치명적인 연속성 오류를 포함"

**open_review extracts**:
- "모든 후보가 Blueprint의 지시에 따라 이전 화(EP 1)에서 확립된 사실과 정면으로 충돌하는 서사를 전개하고 있다. Blueprint 자체의 설계 오류"
- "모든 후보가 동일한 오류를 포함하고 있어 Blueprint 자체의 결함을 의심"

#### Family F-2: `continuity_firewall + structure_error + 타임라인`

**Raw fingerprint**: `structure_error|contradiction:타임라인|continuity_firewall|fix_pack:missing_fix_pack`

| Field | Value |
|-------|-------|
| gate_basis | `continuity_firewall` |
| reject_bucket | `structure_error` |
| error_category | `LOGIC_ERROR` |
| contradiction_type | `타임라인` |
| firewall_triggered | TRUE |
| score | 44 (capped) |
| fix_scope | `full` |
| authoritative_fix_scope | `full` |
| repair_scope | `full` |
| fix_pack_ready | FALSE |
| fix_pack_reason | `missing_fix_pack` |

**Occurrence**: Canary A R4 (post-V75-B), Canary B R0, R2, R3

**fix_scope_reasoning extracts**:
- "에피소드의 핵심 사건인 '20억 자본금 확보'가 1화에서 이미 완료된 사건과 중복되어, 이야기의 근간을 흔드는 치명적인 연속성 오류"
- "선택된 원고를 포함한 모든 후보가 이전 화(EP 1)에서 이미 확립된 '주인공이 20억 자본금 확보를 완료했다'는 사실과 정면으로 충돌하는, 근본적인 타임라인 모순"

**Distinction from F-1**: Same gate_basis and bucket, but contradiction_type shifts from `아이템` to `타임라인`. This indicates the Director re-classified the same underlying conflict (capital acquisition repeat) under a different contradiction taxonomy label after V75-D/V75-B modified the blueprint.

#### Family F-3: `continuity_firewall + post_select_conflict + 타임라인`

**Raw fingerprint**: `post_select_conflict|contradiction:타임라인|continuity_firewall|fix_pack:missing_fix_pack`

| Field | Value |
|-------|-------|
| gate_basis | `continuity_firewall` |
| reject_bucket | `post_select_conflict` |
| error_category | `LOGIC_ERROR` |
| contradiction_type | `타임라인` |
| firewall_triggered | TRUE |
| score | 44-98 (varies) |
| fix_scope | `full` |
| authoritative_fix_scope | `inplace` (Director said small fix) |
| repair_scope | `inplace` |
| fix_pack_ready | FALSE |
| fix_pack_reason | `missing_fix_pack` |

**Occurrence**: Canary A R6, R7(pre-final), Canary B R4, R7, R8

**Key distinction**: `reject_bucket=post_select_conflict` despite `gate_basis=continuity_firewall`. This hybrid fingerprint occurs when:
1. A previous round's A-3 post-select conflict set `reject_bucket=post_select_conflict`
2. The current round triggers continuity_firewall again
3. The A-4 enforcement overrides fix_scope to "full" but the reject_bucket inherits the post_select_conflict classification

**fix_scope_reasoning extracts**:
- Canary A R7: "원고의 완성도가 매우 높아 수정이 필요 없는 PASS 판정입니다. [A-4 continuity replay] 직전 화와 충돌하는 frontier/연속성 신호가 방화벽 REJECT로 재발"
- Shows plateau_detected=True (score 98 repeating)

#### Family F-4: `post_select_conflict + constraint_violation`

**Raw fingerprint**: `constraint_violation|fix_pack:missing_fix_pack`

| Field | Value |
|-------|-------|
| gate_basis | `post_select_conflict` |
| reject_bucket | `constraint_violation` |
| error_category | `CONSTRAINT_VIOLATION` |
| contradiction_type | (empty) |
| firewall_triggered | FALSE |
| score | 91-98 (high, near-pass) |
| fix_scope | `partial` |
| authoritative_fix_scope | `inplace` |
| repair_scope | `full` |
| fix_pack_ready | FALSE |
| fix_pack_reason | `missing_fix_pack` |

**Occurrence**: Canary A R3, R5; Canary B R1, R3, R6, R8, R9

**IFC overlays detected in fix_scope_reasoning**:
- R4 (Canary A): "[IFC] 불변사실 위반 감지 (확정상태회귀). 국소 패치 대신 재작성 우선 처리가 필요합니다"
- R6 (Canary A): "[IFC] 불변사실 위반 감지 (확정상태회귀 / 완료사건반복). 국소 패치 대신 재작성 우선 처리가 필요합니다"

**Key characteristic**: These are PASS manuscripts (score 91-98) that Director approved but A-3 post-select checks flagged contradiction. The manuscript is high quality but contains residual blueprint-inherited continuity conflict.

#### Family F-5: `director_primary_reject + constraint_violation`

**Raw fingerprint**: `constraint_violation|contradiction:고유명사|fix_pack_ready` or `constraint_violation|contradiction:타임라인|fix_pack:scene_model_target`

| Field | Value |
|-------|-------|
| gate_basis | `director_primary_reject` |
| reject_bucket | `constraint_violation` |
| error_category | `CONSTRAINT_VIOLATION` |
| contradiction_type | `고유명사` or `타임라인` |
| firewall_triggered | FALSE |
| score | 84 (mid-range) |
| fix_scope | `inplace` or `partial` |
| authoritative_fix_scope | `inplace` or `partial` |
| repair_scope | `inplace` or `partial` |
| fix_pack_ready | TRUE (R5 고유명사) or FALSE (R9 타임라인) |

**Occurrence**: Canary B R5, R9 only (not observed in Canary A)

**Reason text**:
- R5: "주요 투자 대상의 첫 이름 오류" / "서사 구조와 타임라인은 완벽하게 올바르나, 이전 화와 충돌하는 핵심 등장인물의 이름(고유명사) 오류"
- R9: "가장 핵심적인 문제는 제1화에서 이미 완료된 '20억 자금 확보' 사건을 제3화에서 반복하는 중대한 타임라인 모순"

**Key characteristic**: Director rejected directly (not firewall, not post-select). Lower severity — specific factual errors rather than structural blueprint conflict.

---

### 5. Narrative Conflict Theme Map

Each narrative conflict theme is mapped to the raw families that express it, with the inference path labeled.

#### Theme T-1: 자금 확보 재수행 (Capital Acquisition Repeated)

**Raw signal**: fix_scope_reasoning contains "20억 자본금 확보" + "이미 완료" or "이미 확립"

**Expressed by families**: F-1, F-2, F-3, F-4 (all with IFC overlay), F-5 (R9)

**Inference**: DIRECT — the phrase "20억 자본금 확보가 1화에서 이미 완료" appears verbatim in multiple pathology signals.

**Blueprint root**: EP3 blueprint directed the episode to execute capital acquisition as a primary story event, but EP1 already established this was completed. This is the **core structural conflict** that drives all other families.

#### Theme T-2: 확정상태회귀 / 완료사건반복 (Confirmed State Regression / Completed Event Replay)

**Raw signal**: IFC overlay in fix_scope_reasoning: "[IFC] 불변사실 위반 감지 (확정상태회귀)" or "(확정상태회귀 / 완료사건반복)"

**Expressed by families**: F-4 (IFC-tagged rounds only)

**Inference**: DIRECT — IFC violation classification uses these exact terms as formal violation family names (from `stage4_immutable_fact_contract.py`).

**Distinction from T-1**: T-1 is the narrative description; T-2 is the formal IFC classification of the same underlying problem. T-2 only appears on post_select_conflict rounds where IFC re-checks the near-pass manuscript.

#### Theme T-3: OTP / 법인 인감도장 / 계좌 개설 반복 (OTP / Corporate Seal / Account Setup Repeated)

**Raw signal**: fix_scope_reasoning contains "OTP 수령" or "법인 인감도장" or "인감도장 확보"

**Expressed by families**: F-1 (R1, R2)

**Inference**: DIRECT — exact phrases in pathology signals.

**Relation to T-1**: This is a sub-theme of T-1. The capital acquisition involved OTP receipt and corporate seal acquisition in EP1. When the blueprint repeats the capital acquisition, these subsidiary items are also repeated.

#### Theme T-4: 그룹명 / 고유명사 혼용 (Group Name / Proper Noun Confusion)

**Raw signal**: contradiction_type=`고유명사`, open_review contains "태성그룹 → 한양그룹" or "형의 이름이 잘못 표기"

**Expressed by families**: F-5 (R5 only in Canary B), F-4 (Canary A R3 open_review)

**Inference**: DIRECT for F-5 (contradiction_type=고유명사); INDIRECT for F-4 (mentioned in open_review of a post_select_conflict round, not the primary reject reason).

**Relation to T-1**: Partially independent. Group name confusion (태성그룹 vs 한양그룹) and character name errors (한태준 vs 한진우) may be blueprint-inherited or generation-side drift. Not purely a blueprint structural issue.

#### Theme T-5: Opening-Ending Mismatch / Blueprint-Previous Episode Disconnect

**Raw signal**: open_review contains "직전 화 엔딩의 긴장감이 오프닝에서 다소 약하게 이어지는 아쉬움" or "Blueprint의 구조적 결함을 그대로 따르고 있습니다"

**Expressed by families**: F-1 (R2), F-2 (Canary B R0)

**Inference**: INDIRECT — not a first-class field. Derived from open_review text describing how the blueprint's scene structure doesn't properly bridge from EP2's ending to EP3's opening.

**Relation to T-1**: This is a downstream symptom. Because the blueprint directs capital acquisition (already done), the episode's opening doesn't connect to EP2's ending tension.

---

### 6. Baseline Comparison Set

The following 4-family baseline is the minimal stable set for judging the patched EP3 canary.

#### Baseline Family B-1: `FIREWALL_CAPITAL_REPLAY`

**Fingerprint match**: F-1 + F-2 (collapsed)

| Check Field | Match Value |
|-------------|-------------|
| gate_basis | `continuity_firewall` |
| reject_bucket | `structure_error` |
| firewall_triggered | TRUE |
| score | 44 (capped) |
| contradiction_type | `아이템` OR `타임라인` |

**Narrative label**: Capital acquisition repeated — blueprint directs EP3 to execute events EP1 already completed.

**Expected delta in patched canary**:
- `old family removed` — if V75-D blueprint patch corrected the capital acquisition directive and no more firewall REJECT with this fingerprint appears
- `old family weakened` — if firewall still triggers but with fewer rounds or different contradiction_type
- `old family renamed but still present` — if same conflict appears under a different gate_basis or contradiction taxonomy

#### Baseline Family B-2: `POSTSELECT_NEAR_PASS_RESIDUAL`

**Fingerprint match**: F-4

| Check Field | Match Value |
|-------------|-------------|
| gate_basis | `post_select_conflict` |
| reject_bucket | `constraint_violation` |
| firewall_triggered | FALSE |
| score | 91-98 |
| error_category | `CONSTRAINT_VIOLATION` |

**Narrative label**: Near-pass manuscript catches residual blueprint contradiction in A-3 post-select checks.

**Expected delta in patched canary**:
- `old family removed` — if blueprint patch eliminated the structural contradiction so post-select checks pass
- `old family weakened` — if post-select still triggers but with fewer rounds or at higher scores
- `new family introduced` — if post-select catches a different contradiction from the patched blueprint

#### Baseline Family B-3: `FIREWALL_POSTSELECT_HYBRID`

**Fingerprint match**: F-3

| Check Field | Match Value |
|-------------|-------------|
| gate_basis | `continuity_firewall` |
| reject_bucket | `post_select_conflict` |
| firewall_triggered | TRUE |
| score | 44-98 (varies) |
| plateau_detected | TRUE (late rounds) |

**Narrative label**: Oscillation hybrid — firewall re-triggers after a post_select_conflict round, combining both families.

**Expected delta in patched canary**:
- `old family removed` — if no oscillation occurs because B-1 is eliminated
- This family is **derivative** of B-1 + B-2. If both are removed, B-3 should disappear automatically.

#### Baseline Family B-4: `DIRECTOR_FACTUAL_REJECT`

**Fingerprint match**: F-5

| Check Field | Match Value |
|-------------|-------------|
| gate_basis | `director_primary_reject` |
| reject_bucket | `constraint_violation` |
| firewall_triggered | FALSE |
| score | 84 |
| contradiction_type | `고유명사` OR `타임라인` |

**Narrative label**: Director rejects for specific factual errors (proper noun, timeline detail) without firewall trigger.

**Expected delta in patched canary**:
- `old family weakened or removed` — if blueprint patch fixes the factual errors
- `old family renamed but still present` — if director still finds factual issues but of a different type
- This family is **partially independent** of the blueprint structural conflict. Proper noun errors (T-4) may persist even with a patched blueprint.

---

### 7. Highest-Risk False Comparisons

#### False Comparison 1: Treating `아이템` and `타임라인` as different families

**Risk**: An operator comparing patched vs unpatched canary might report "아이템 family removed, 타임라인 family introduced" when in reality the same underlying conflict (capital acquisition repeat) was merely re-classified under a different contradiction taxonomy.

**Mitigation**: B-1 collapses both contradiction_types into a single family. Compare by `gate_basis + reject_bucket + firewall_triggered`, not by `contradiction_type` alone.

#### False Comparison 2: Counting post_select_conflict rounds as separate from firewall rounds

**Risk**: B-2 and B-3 rounds are causally downstream of B-1. If B-1 is removed by the blueprint patch, B-2 and B-3 should also vanish. An operator might incorrectly report "3 families removed" when only 1 root cause was fixed.

**Mitigation**: The comparison rule should distinguish **root families** (B-1, B-4) from **derivative families** (B-2, B-3). Count root removals, not derivative.

#### False Comparison 3: Treating 8R→2R as proof of general compression

**Risk**: The retry_loop_compression canary ran EP3 in 2 rounds. This could be interpreted as "blueprint patch compressed 8 rounds to 2 across all episodes." But the evidence only proves EP3-specific compression. Other episodes may behave differently.

**Mitigation**: The baseline is EP3-specific. Claims about general compression must cite per-episode deltas, not a single EP3 comparison.

#### False Comparison 4: Ignoring V75-D/V75-B contribution

**Risk**: Both pre-patch canaries ran V75-D (and Canary A ran V75-B) but still needed 8-10 rounds. The post-patch canary also ran V75-D and passed in 2 rounds. An operator might conclude "V75-D didn't help in the old runs" when in reality V75-D contributed to eventual resolution in both.

**Mitigation**: The comparison should note that V75-D fired in both old and new runs. The delta is not "V75-D was added" but "the blueprint V75-D patches was already improved, so V75-D's incremental patch was sufficient on the first try."

#### False Comparison 5: Using `director_primary_reject` (B-4) as evidence of blueprint fix success

**Risk**: B-4 only appeared in Canary B (scope_sink_semantics), not in Canary A (feedback_windowing). Its absence from the patched canary might reflect run-to-run variance, not a patch effect.

**Mitigation**: B-4 is marked as **partially independent** of the blueprint structural conflict. Its absence from the patched run is consistent with success but not conclusive evidence of it.

---

### 8. Recommended Comparison Rule For Patched Canary

When the patched EP3 canary completes, apply these comparison rules in order:

**Step 1 — Check B-1 (root family)**

| If patched canary shows... | Conclusion |
|---------------------------|------------|
| Zero `continuity_firewall` + `structure_error` REJECT on EP3 | B-1 **removed** — root conflict eliminated |
| Fewer `continuity_firewall` rounds, different contradiction_type | B-1 **weakened** — root partially resolved |
| Same fingerprint pattern on EP3 | B-1 **still present** — patch did not address root |

**Step 2 — Check B-2 (derivative family)**

| If B-1 was removed and... | Conclusion |
|--------------------------|------------|
| Zero `post_select_conflict` on EP3 | B-2 **removed** (expected if B-1 removed) |
| `post_select_conflict` appears with different contradiction | B-2 **renamed** — new conflict from patched blueprint |
| `post_select_conflict` appears with same IFC tags | B-2 **still present** — blueprint patch incomplete |

**Step 3 — Check B-3 (derivative hybrid)**

B-3 should disappear automatically if B-1 is removed. If B-3 appears without B-1, this indicates a new oscillation source.

**Step 4 — Check B-4 (independent family)**

B-4 (director_primary_reject for factual errors) should be checked separately. Its presence or absence is only weakly correlated with the blueprint patch.

**Step 5 — Check for new families**

Any reject fingerprint that does not match B-1 through B-4 is a **new family introduced** by the patched blueprint. Document its fingerprint for future baseline.

**Compact operator decision table**:

| Root Family | Status | Rounds Saved | Confidence |
|------------|--------|-------------|------------|
| B-1 removed | Old: 4-6 firewall rounds → New: 0 | 4-6 rounds | HIGH if zero continuity_firewall |
| B-2 removed | Old: 2-5 post-select rounds → New: 0 | 2-5 rounds | HIGH if B-1 also removed |
| B-3 removed | Derivative of B-1+B-2 | Included above | Automatic |
| B-4 removed | Old: 0-2 director reject rounds → New: 0 | 0-2 rounds | LOW — independent variance |

---

### 9. Confidence

| Section | Confidence | Basis |
|---------|------------|-------|
| Pre-patch round map (Canary A) | **HIGH** | Raw episode_production.jsonl + runtime_audit.jsonl with exact field values |
| Pre-patch round map (Canary B) | **HIGH** | Same raw sources, 10+ rounds with detailed pathology |
| Family F-1 through F-5 identification | **HIGH** | Raw pathology_fingerprint field from runtime_audit, no inference needed |
| Family collapse into B-1 through B-4 | **HIGH** | Based on gate_basis + reject_bucket + firewall_triggered grouping |
| T-1 (capital acquisition) as root cause | **HIGH** | Verbatim fix_scope_reasoning across both canaries |
| T-2 (IFC formal classification) | **HIGH** | "[IFC] 불변사실 위반 감지 (확정상태회귀)" exact text |
| T-3 (OTP/seal sub-theme) | **MODERATE** | Present in Canary A R1-R2 only; may not appear in all runs |
| T-4 (group name confusion) | **MODERATE** | Present in Canary B only; partially independent of blueprint |
| T-5 (opening-ending mismatch) | **LOW** | Derived from open_review prose, not a first-class field |
| B-3 as derivative of B-1+B-2 | **HIGH** | Fingerprint combines both families; logically dependent |
| B-4 as partially independent | **MODERATE** | Only appeared in one of two canaries |
| Comparison rule validity | **HIGH** | Based on root-cause analysis with raw evidence |

**Overall survey confidence: HIGH** — all family fingerprints are extracted from raw pathology_fingerprint fields in runtime_audit.jsonl. Narrative theme labels are explicitly separated from raw signals and labeled by inference path.
