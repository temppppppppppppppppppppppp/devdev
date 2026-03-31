# EP8 Artifact Truth / Narrative Lane — Draft Report

Date: 2026-03-30
Status: draft-bounded-partial-evidence
Lane: 1 (Artifact Truth / Narrative)
Terminal: 1
Baseline Commit: `92ba1cf7`
Master Order: `docs/2026-03-30/0_1-ep8-artifact-vs-code-parallel-master-order.md`

## 1. Coverage

| Evidence Source | Status |
|---|---|
| `0_temp.txt` L200-814 (EP8 Stage 4 full run) | Read in full |
| `projects/0_1/plans/blueprints/blueprint_0008.txt` | Read in full |
| `projects/0_1/drafts/ep_0007.txt` (prior episode manuscript) | Read in full (focus L90-120) |
| `attempt_01/rejected_best__A.txt` | Read in full |
| `attempt_05/selected_before_fix__C_asp_correction.txt` | Read in full |
| `attempt_02-04/` file existence and sizes | Verified |
| `project_data.db` — `stage_attempts` WHERE ep_num=8 AND stage=4 | Queried (5 rows) |
| `project_data.db` — `anchors` WHERE key='bible' (NPC 박성호 data) | Queried |
| `project_data.db` — `npc_history` WHERE npc_name LIKE '%박성호%' | Queried |

## 2. Findings

### F-1. [CRITICAL] Blueprint embeds temporal contradiction — '18년 전 과거의 기억'

**Defect origin:** Blueprint (artifact stage)

**Evidence chain:**

1. `blueprint_0008.txt` L7 (integrated scenario) contains the literal phrase:
   > 현실의 지표가 18년 전 과거의 기억과 단 1초의 오차도 없이 맞물려 돌아가고 있었다.

2. The protagonist is a time-regression character who returned from 2024 to 2006. He is currently living in 2006.

3. From the 2006 perspective, memories of 2024 are **future memories** (미래의 기억), not **past memories** (과거의 기억). Calling them "18년 전 과거의 기억" inverts the temporal logic.

4. CW faithfully reproduces this blueprint phrase. Confirmed in `attempt_05/selected_before_fix__C_asp_correction.txt` L46:
   > 현실의 지표가 18년 전 과거의 기억과 단 1초의 오차도 없이 맞물려 돌아가고 있었다.

5. FlashbackVerifier advisory (attempt 5, `0_temp.txt` L711-714) correctly diagnoses the issue:
   > EP 1의 맥락에 따르면 주인공은 2024년에서 2006년으로 회귀하여 현재 2006년을 살고 있습니다. 따라서 작중 현재(2006년) 시점에서 벌어지는 경제 상황을 '18년 전 과거의 기억'과 비교하는 것은 시점상 모순입니다.

6. Director catches this in attempt 5 and issues explicit fix instruction (`0_temp.txt` L739):
   > 씬 2의 '18년 전 과거의 기억'을 '18년 치 미래의 데이터' 또는 '전생의 기억'으로 수정할 것

**Conclusion:** The contradiction is embedded in the blueprint's integrated scenario. No code change or CW behavioral adjustment can prevent it from appearing in manuscripts as long as the blueprint contains it.

### F-2. [IMPORTANT] Blueprint numeric inconsistency — 5억 원 vs 4억 7,100만 원

**Defect origin:** Blueprint (artifact stage, upstream sync failure with EP7)

**Evidence chain:**

1. `blueprint_0008.txt` L7, Scene 4 dialogue ending:
   > 계좌에 남은 5억 원...

2. `ep_0007.txt` L73 (Park Sungho dialogue, EP7 established fact):
   > 잔고에 4억 7,100만 원이 남아있다고는 하지만

3. Director explicitly acknowledged the correct figure in attempt 2 (`0_temp.txt` L420):
   > 직전 화에서 확립된 정확한 잔여 증거금 수치(4억 7,100만 원)를 사용하여 수치 연속성을 완벽하게 지켰습니다

4. Attempt 5 post-select continuity check caught this mismatch and downgraded PASS to REJECT (`0_temp.txt` L741-746):
   > 4억 7,100만 원으로 설정된 남은 증거금이 마지막 대사에서 5억 원으로 잘못 표기되었습니다

**Conclusion:** The blueprint's Scene 4 was not updated to match EP7's established exact figure. CW candidates that faithfully follow the blueprint's "5억 원" phrasing trigger continuity violations.

### F-3. [MODERATE] 박성호 NPC role drift

**Defect origin:** Mixed (Blueprint ambiguity + CW inference)

**Evidence chain:**

1. Bible anchor NPC registration: `"role": "SW인베스트먼트 전담 PB"`
2. Attempts 1-4: Some candidates describe him as "한미증권 본사 파생상품 데스크 소속"
3. NpcDriftAdvisor repeatedly flagged: `기대='SW인베스트먼트 전담 PB' → 원고='한미증권 본사 파생상품 데스크 소속으로 묘사됨'`
4. Attempt 5 selected candidate (C) correctly used: "SW인베스트먼트 전담 PB 박성호" (artifact file L21)
5. Blueprint does not explicitly state Park's title in the Scene 3 description, only contextually places him at "한미증권 본사 파생상품 데스크"

**Conclusion:** The drift self-corrected by attempt 5. Blueprint could mitigate recurrence by explicitly including Park's registered title in his Scene 3 introduction.

### F-4. [MODERATE] Persistent dialogue ratio deficit

**Defect origin:** Mixed (Blueprint scenario design + CW tendency)

**Evidence chain:**

1. All attempts: dialogue ratio 8-13% vs. style target 30%
2. Blueprint's 4 scenes are structurally description-heavy:
   - Scene 1: lobby chaos description
   - Scene 2: cafe + Bloomberg terminal + market data observation
   - Scene 3: Park's internal monologue at trading desk
   - Scene 4: only scene with meaningful dialogue (phone call)
3. Director consistently notes this but does not downgrade for it, recognizing the genre context

**Conclusion:** Blueprint scenario design inherently constrains dialogue ratio for this episode. This is a style concern, not a blocking defect.

## 3. Non-Issues

| Item | Reason for dismissal |
|---|---|
| Opening continuity (location change detection) | EP7 L116-120 ends with VIP room door opening into lobby chaos. EP8 Scene 1 picks up from the same moment. **Perfect continuity.** Python's `위치 변화 감지` warning is a false positive. |
| NumericConsistency "처음" warnings | `"처음이었다"`, `"첫 번째 톱니바퀴"` flagged as potential contradictions. These are contextually valid first-time references within their specific semantic scope. False positives. |
| 경비원 NPC drift | Appeared in only one unselected candidate (attempt 3, candidate B). Not a systemic issue. |
| Missing transition description (이동 경위) | EP7 → EP8 transition occurs at the same physical location (VIP room doorway). No transition description is needed. |

## 4. Verdict: artifact-first

### Primary Assessment

EP8's primary blockers are **blueprint-stage defects**:

1. **Temporal contradiction** (F-1): The phrase '18년 전 과거의 기억' is embedded in the blueprint's integrated scenario and is faithfully reproduced by CW. This is a factual error in the story's temporal logic that no code change can prevent.

2. **Numeric inconsistency** (F-2): The blueprint uses "5억 원" in Scene 4 while EP7 established the exact figure as 4억 7,100만 원. This causes guaranteed continuity violations.

### Critical Test: "Would EP8 be rejected even with perfect code?"

**Yes.** Attempt 5 directly proves this:
- Attempts 1-4 were blocked by a code-level mechanism (`pass_with_fix_contract_missing_patch_targets` gate, a Lane 2 concern)
- Attempt 5 bypassed the code gate (Director issued `PASS_WITH_FIX` directly)
- Despite bypassing the code issue, attempt 5 was REJECTED for:
  - Temporal contradiction (FlashbackVerifier + Director detection)
  - Numeric inconsistency (post-select continuity conflict)
- This proves the artifact defects are the ultimate blockers

### Secondary Assessment

- Attempts 1-4's `pass_with_fix_contract_missing_patch_targets` REJECT pattern is a **code-stage concern** (Terminal 2 scope). This mechanism delayed artifact-defect discovery by 4 rounds.
- The code's quality detection pipeline (FlashbackVerifier, post-select continuity check) ultimately works correctly — it caught the artifact defects when the routing gate stopped masking them.
- Director's quality judgment is high (scores 93-96) — the manuscripts are well-written. The defects are upstream.

### Immediate Next Action (for synthesis terminal)

- **Blueprint repair first**: Fix the '18년 전 과거의 기억' phrase and the '5억 원' figure in `blueprint_0008.txt` before re-running Stage 4.
- Code investigation (pass_with_fix gate behavior) is separately worthwhile but not the primary blocker.

## 5. Stop

read-only lane complete; no files mutated
