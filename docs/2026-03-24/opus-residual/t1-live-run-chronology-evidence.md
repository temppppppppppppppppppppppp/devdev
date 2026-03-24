Date: 2026-03-24
Status: final
Document Type: evidence ledger (T1 Live Run Chronology)
Parent Report: `docs/2026-03-24/opus-residual/t1-live-run-chronology.md`

---

# T1 Evidence Ledger

## E1. Run A (00_001) — Old Family Rejection at ep3 R2

- Source: `projects/00_001/logs/runtime_audit.jsonl:25`
- Timestamp: `2026-03-24 06:55:35`
- Type: `stage4_retry_pathology_signal`
- ep_num: 3, round_num: 2
- pathology_fingerprint: `structure_error|contradiction:타임라인|continuity_firewall|fix_pack:missing_patch_targets`
- reject_bucket: `structure_error`
- gate_basis: `continuity_firewall`
- fix_scope: `full`
- error_category: `LOGIC_ERROR`
- contradiction_type: `타임라인`
- firewall_triggered: `true`
- score: 50
- fix_scope_reasoning: "이전 화(EP 1)에서 이미 완료된 20억 원 현금화 및 OTP 수령 사건이 현재 화에서 다시 반복되는 심각한 타임라인 및 설정 충돌(CRITICAL)이 발생하여 전면 재작성이 필요함."
- open_review: "Blueprint 자체가 이전 화의 진행 상황을 무시하고 작성되었습니다. 주인공은 이미 EP 1에서 20억 원을 법인 계좌로 이체받았고 OTP도 가지고 있는 상태로 아버지의 서재에 들어갔습니다. 따라서 은행에 가서 다시 자금을 현금화하는 씬은 명백한 설정 오류입니다."

## E2. Run A (00_001) — Old Family Rejection at ep4 R1

- Source: `projects/00_001/logs/runtime_audit.jsonl:27`
- Timestamp: `2026-03-24 07:12:38`
- Type: `stage4_retry_pathology_signal`
- ep_num: 4, round_num: 1
- pathology_fingerprint: `structure_error|contradiction:타임라인|continuity_firewall|fix_pack:missing_patch_targets`
- reject_bucket: `structure_error`
- gate_basis: `continuity_firewall`
- fix_scope: `full`
- error_category: `LOGIC_ERROR`
- contradiction_type: `타임라인`
- firewall_triggered: `true`
- score: 30
- fix_scope_reasoning: "직전 화에서 이미 완료된 오피스텔 계약, HTS 세팅, WTI 매수 진입을 모든 후보가 다시 반복 서술하는 치명적인 타임라인 모순이 발생하여 전면 재작성이 필요함."
- open_review: "Blueprint 자체가 3화의 내용을 반영하지 못하고 잘못 설계되었습니다. 작가(AI)들은 Blueprint를 따르다 보니 3화에서 이미 일어난 일들을 4화에서 다시 반복하는 치명적인 타임라인 오류를 범했습니다."

## E3. Run A (00_001) — V75-D Blueprint Patch at ep3

- Source: `projects/00_001/logs/runtime_audit.jsonl:26`
- Timestamp: `2026-03-24 06:56:39`
- Type: `stage4_v75d_blueprint_patch_snapshot`
- ep_num: 3, round_num: 2
- candidate_key: `V75-D|blueprint_inplace`
- change_ratio: **0.4011** (40% of blueprint rewritten)
- artifact_path: `logs/artifacts/stage4/ep_0003/attempt_02/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`

## E4. Run A (00_001) — V75-D Blueprint Patch at ep4

- Source: `projects/00_001/logs/runtime_audit.jsonl:28`
- Timestamp: `2026-03-24 07:13:31`
- Type: `stage4_v75d_blueprint_patch_snapshot`
- ep_num: 4, round_num: 1
- candidate_key: `V75-D|blueprint_inplace`
- change_ratio: **0.5492** (55% of blueprint rewritten)
- artifact_path: `logs/artifacts/stage4/ep_0004/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`

## E5. Run A (00_001) — Stage 3 ep1-3 Blueprint PASS (no failures)

- Source: `projects/00_001/logs/quality_metrics.jsonl:3,5,7`
- ep1: PASS 95 @ 05:50:22
- ep2: PASS 95 @ 05:51:53
- ep3: PASS 95 @ 05:53:22
- All first-attempt, no violations, quality_risk=true

## E6. Run A (00_001) — Stage 4 ep1-2 PASS (first round)

- Source: `projects/00_001/logs/quality_metrics.jsonl:11,15`
- ep1: PASS 96 @ 05:59:28, blueprint_coverage=40% (2/5)
- ep2: PASS 96 @ 06:07:18, blueprint_coverage=40% (2/5)

## E7. Run A (00_001) — New/Local Rejections (ep5-7)

- ep5 R1: `runtime_audit.jsonl:30` — quality_issue, score 80, 타임라인 (이란 선언 시점)
- ep6 R1: `runtime_audit.jsonl:32` — constraint_violation, score 96, missing_patch_targets
- ep6 R2: `runtime_audit.jsonl:33` — constraint_violation, score 93, 수치 (OTP 잔고)
- ep7 R1: `runtime_audit.jsonl:53` — constraint_violation, score 95, missing_patch_targets

## E8. Run A (00_001) — WorldState Save Failure

- Source: `projects/00_001/logs/runtime_audit.jsonl:54`
- Timestamp: `2026-03-24 08:40:48`
- Component: `stage4_post_processor`
- Operation: `save_world_state_atomic`
- Exception: `unhashable type: 'dict'`
- Rolled back: true, degraded: true

## E9. Run B (00_0324) — Clean Stage 4 Results

- Source: `projects/00_0324/logs/episode_production.jsonl:1,3,6`
- ep1: PASS R0, score 95, strategy balanced @ 13:17:53
- ep2: PASS_WITH_FIX->PASS R0, score 90, strategy tension @ 13:30:06
- ep3: PASS R0, score 95, strategy tension @ 13:36:13
- 0 rejections, 0 continuity_firewall triggers, 0 V75-D patches

## E10. Run B (00_0324) — Stage 3 Blueprint Quality

- Source: `projects/00_0324/logs/runtime_audit.jsonl:6,8,10,12`
- ep1: PASS 95, quality_risk=false, revision_required=false
- ep2: PASS 88, quality_risk=false, revision_required=true
- ep3: PASS 90, quality_risk=false, revision_required=true
- ep4: PASS 95, quality_risk=false, revision_required=true
- All `quality_risk=false` — contrast with 00_001 where 9/11 are `quality_risk=true`

## E11. Run A (00_001) — Arc 2 Difficulty Feedback

- Source: `projects/00_001/logs/runtime_audit.jsonl:37`
- Arc 2 difficulty: normal, avg_attempts: 2.5
- Hard episodes: [6]
- Semantic failures recorded for ep5 (QUALITY_ISSUE) and ep6 (CONSTRAINT_VIOLATION x2)
- ep5 failure: "EP 4에서 이미 이란이 우라늄 농축 재개를 '공식 선언'했으므로, 씬 2의 뉴스를 '선언 임박'이 아닌 '선언 이후 서방의 강력한 경제 제재 구체화'로 수정하십시오"
- ep6 failure: "OTP 기기 액정에 38억 원의 계좌 잔고가 표시된다는 설정 오류"

## E12. Console Verification — Stage 3 Clean Pass for 00_0324

- Source: `docs/2026-03-24/console.txt:424-489`
- ep1 PASS score=95 (emotion_focused) @ console L424
- ep2 PASS score=88 (action_focused) @ console L440
- ep3 PASS score=90 (action_focused) @ console L459
- ep4 PASS score=95 (dialogue_focused) @ console L477
- Stage 3 completion: 100% pass rate, 0 failures @ console L494
