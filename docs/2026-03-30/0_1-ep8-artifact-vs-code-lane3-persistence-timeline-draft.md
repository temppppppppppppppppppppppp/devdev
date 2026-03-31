# EP8 Artifact-vs-Code Lane 3: Persistence & Timeline Reconstruction

Date: 2026-03-30
Status: draft-bounded-partial-evidence
Lane: 3 — persistence, DB, JSONL, attempt timeline
Master Order: `docs/2026-03-30/0_1-ep8-artifact-vs-code-parallel-master-order.md`
Baseline Commit: `92ba1cf7`

## 1. Coverage

| Source | Path | Status |
|---|---|---|
| 0_temp.txt | `0_temp.txt` L300-814 | EP8 Stage4 round 1-6 (6차 미완) |
| project_data.db / stage_attempts | `ep_num=8, stage=4` | 5 rows 전량 |
| project_data.db / director_selections | `ep_num=8, stage=4` | 5 rows 전량 |
| project_data.db / attempt_raw_rationale | `ep_num=8` | 5 rows 전량 |
| episode_production.jsonl | Lines 14-25 | EP8 attempt + pathology 전량 |
| session log | `session_20260330_161043.log` (423KB) | 말미: 17:03:56 attempt 6 mid-flight |
| artifacts/stage4/ep_0008/ | attempt_01~05 dirs | 파일 리스트 + SHA-256 교차검증 |
| manuscripts / episode_meta / episode_bibles | DB | EP8 행 없음 (최대 EP7) |
| quality_metrics.jsonl | — | EP8 항목 없음 |

## 2. Findings

### 2A. Attempt-by-Attempt Matrix

| # | TS (KST) | Director Verdict | Final Verdict | Score | gate_basis | patch_targets | Selected | Primary Blocker |
|---|---|---|---|---|---|---|---|---|
| 1 | 16:31:53 | PASS | REJECT | 95 | pass_with_fix_contract_missing_patch_targets | [] | A\|narrative | advisory escalation empty patch loop |
| 2 | 16:37:24 | PASS | REJECT | 96 | pass_with_fix_contract_missing_patch_targets | [] | A\|narrative | advisory escalation empty patch loop |
| 3 | 16:47:10 | PASS | REJECT | 96 | pass_with_fix_contract_missing_patch_targets | [] | A\|balanced | advisory escalation empty patch loop |
| 4 | 16:54:09 | PASS | REJECT | 96 | pass_with_fix_contract_missing_patch_targets | [] | A\|balanced | advisory escalation empty patch loop |
| 5 | 17:01:28 | PASS_WITH_FIX | REJECT | 93 | post_select_conflict | ["18년 전 과거의 기억..."] | C\|asp_correction | post-select continuity (4.71억→5억) |
| 6 | ~17:03:56 | (in flight) | (not persisted) | - | - | - | - | operator stopped terminal |

### 2B. Empty Patch Targets Loop (attempts 1-4)

Mechanism (identical on all 4):

1. Director evaluates manuscript → verdict: PASS (score 95-96)
2. Advisory chain fires `npc_drift`: 박성호 역할='SW인베스트먼트 전담 PB' ≠ 원고='한미증권 본사 파생상품 데스크 소속'
3. Strong advisory escalation upgrades PASS → PASS_WITH_FIX
4. Escalation path does **not** populate `patch_targets`
5. Lane3 Gate contract: PASS_WITH_FIX + empty patch_targets → REJECT
6. Result: Director wanted PASS, code gate forced REJECT

DB evidence (`advisory_flags` JSON for all a1-a4):
```
gate_semantics.director_verdict = "PASS"
gate_semantics.final_verdict = "REJECT"
gate_semantics.gate_basis = "pass_with_fix_contract_missing_patch_targets"
fix_pack.patch_targets = []
strong_advisory_escalation.source_verdict = "PASS"
strong_advisory_escalation.escalated_to = "PASS_WITH_FIX"
strong_advisory_escalation.triggered_by = ["npc_drift"]  // a3: ["flashback"]
```

JSONL pathology fingerprint (persistent across a1-a4):
```
pathology_fingerprint: "quality_issue|fix_pack:missing_patch_targets" (a1-a2)
pathology_fingerprint: "constraint_violation|fix_pack:missing_patch_targets" (a3-a4)
fix_pack_ready: false
fix_pack_reason: "missing_patch_targets"
```

Plateau detected at round 3 (pathology JSONL `plateau_detected: true`).

### 2C. Attempt 5 — Different Mechanism

- Director returns PASS_WITH_FIX (not escalated from PASS)
- patch_target populated: `["18년 전 과거의 기억과 단 1초의 오차도 없이"]`
- gate_basis initially `director_primary_pass_with_fix`
- Post-select continuity check finds **numeric conflict**: 4억 7,100만 원 → 5억 원
- gate_basis overridden to `post_select_conflict` → REJECT with repair_scope=full

DB evidence:
```
gate_semantics.director_verdict = "PASS_WITH_FIX"
gate_semantics.final_verdict = "REJECT"
gate_semantics.gate_basis = "post_select_conflict"
```

JSONL pathology:
```
pathology_fingerprint: "constraint_violation|contradiction:타임라인|fix_pack_ready"
fix_pack_ready: true
contradiction_type: "타임라인"
```

### 2D. Content Hash Identity: Attempt 4 = Attempt 5

Byte-level file verification:

| File | Size (bytes) | SHA-256 prefix |
|---|---|---|
| attempt_04/rejected_best__A_balanced.txt | 10,930 | f1c85c1690d7b4dfde00 |
| attempt_05/selected_before_fix__C_asp_correction.txt | 10,930 | f1c85c1690d7b4dfde00 |
| attempt_05/rejected_best__C_asp_correction.txt | 10,930 | f1c85c1690d7b4dfde00 |

All three files are **byte-identical**. The asp_correction candidate in attempt 5 is the same text as attempt 4's balanced candidate. This indicates the rewrite/correction pathway did not produce genuinely new content between rounds 4 and 5 despite different candidate labels.

DB `content_hash` field confirms: `f1c85c1690d7b4dfde00c309d110dd4e987d8c93393d7c9351d24a313673cea4` for both attempt 4 (A|balanced) and attempt 5 (C|asp_correction).

### 2E. Attempt 6 — Incomplete (Operator Stop)

Evidence from `0_temp.txt` L807-814:
- Advisory chain: 1건 (StyleSignal only) — **no NpcDrift, no Flashback**
- 2 candidates: 4663자, 4675자 — both had only 3 warnings (Confidence:medium)
- This was the cleanest advisory profile across all 6 rounds
- Waiting for Director LLM response at 42m 22s elapsed

Evidence from session log (17:03:56):
- Director LLM call sent, HTTP 200 received, response_len=2 (likely parsing phase)
- No further stage_attempts DB row for attempt 6
- Terminal was stopped during or immediately after this call

### 2F. Terminal State of EP8

No success state persisted:
- `manuscripts` table: rows for ep 1-7 only
- `episode_meta` table: rows for ep 1-7 only
- `episode_bibles` table: rows for ep 1-7 only
- `episode_quality_labels`: ep 1-7 only (all PASS, scores 90-98)
- `quality_metrics.jsonl`: no EP8 entries

Last persisted attempt: attempt 5 at 17:01:28 (REJECT)
Last observed activity: attempt 6 mid-flight at ~17:03:56 (not persisted)

### 2G. Upstream Stage Verdicts

| Stage | TS | Verdict | Score | Note |
|---|---|---|---|---|
| Stage 2 (Arc) | 2026-03-29 20:56:11 | PASS | 95 | arc 8, balanced strategy |
| Stage 3 (Blueprint) | 2026-03-30 08:37:26 | PASS | 78 | arc 2, dialogue_focused |

Both upstream stages passed without issue.

## 3. Non-Issues

- **Stage 2/3 input quality**: Both PASS, no re-examination needed
- **EP7 production**: PASS score 97, Round 1 — no carry-over defect
- **Score magnitude**: EP8 manuscripts scored 93-96 by Director — quality itself was not the blocker
- **Firewall**: `firewall_triggered=0` on all attempts — no firewall override
- **Encoding**: All artifacts verified byte-level UTF-8 — no corruption
- **Patch mode**: `is_patch=0`, `is_patch_fallback=0` on all attempts — patch mode never engaged (correctly, given empty patch_targets)

## 4. Verdict

**Timeline says: code-first**

| Factor | Attempts | Direction | Weight |
|---|---|---|---|
| Empty patch_targets loop from advisory escalation | 1,2,3,4 | code-first | **dominant** (4/5) |
| Director PASS overridden by Lane3 Gate REJECT | 1,2,3,4 | code-first | strong |
| Content hash identity across a4/a5 (rewrite ineffective) | 4,5 | code (routing) | moderate |
| '18년 전 과거의 기억' 시점 모순 | 5 | artifact | real but secondary |
| 4.71억→5억 수치 충돌 | 5 | artifact | real but secondary |
| 박성호 role drift (advisory trigger) | 1-5 | artifact (recurring) | trigger for code defect |
| Attempt 6 had cleanest advisory, was not completed | 6 | inconclusive | suggestive |

**Summary judgment**: The primary blocker is a **code contract defect** in the advisory-escalation → patch_targets → Lane3 Gate pathway. Director consistently wanted to pass the manuscripts (4 out of 5 rounds returned PASS), but the strong advisory escalation mechanism created PASS_WITH_FIX without populating patch_targets, causing automatic Lane3 Gate downgrades to REJECT.

Artifact-level defects (박성호 role drift, 시점 표현, 수치 충돌) are **real and recurring**, but they are secondary: they triggered the advisory, but the advisory did not produce actionable fix instructions. If the code contract had worked correctly (either passing the Director's PASS through, or generating valid patch_targets), the manuscript would have been accepted or patched in-place.

The content hash identity between attempt 4 and 5 further suggests a routing/rewrite issue — the correction pathway did not produce differentiated content.

Attempt 6, which had the cleanest advisory profile (no NpcDrift, no Flashback), was interrupted before Director judgment, leaving the hypothesis that the loop might have self-resolved untested.
