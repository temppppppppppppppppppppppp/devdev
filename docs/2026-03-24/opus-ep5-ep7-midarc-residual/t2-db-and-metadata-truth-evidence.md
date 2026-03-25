# T2 Evidence: DB / Metadata Truth — EP5-EP7

Date: 2026-03-24
Lane: T2
Evidence Type: raw data extracts with file/line anchors

---

## E-1. stage_attempts EP5-7 (DB)

Source: `projects/0324_00_/project_data.db` table `stage_attempts`

### EP5
| id | stage | attempt_num | verdict | score | failure_category | gate_basis | candidate_key | artifact_path | is_patch |
|---|---|---|---|---|---|---|---|---|---|
| 14 | 3 | 1 | PASS | 95 | — | — | emotion_focused | stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json | 0 |
| 20 | 4 | 1 | REJECT | 93 | CONSTRAINT_VIOLATION | post_select_conflict | B\|balanced | stage4/ep_0005/attempt_01/rejected_best__B_balanced.txt | 0 |
| 21 | 4 | 2 | REJECT | 93 | CONSTRAINT_VIOLATION | post_select_conflict | A\|inplace_patch | stage4/ep_0005/attempt_02/rejected_best__A_inplace_patch.txt | 1 |
| 22 | 4 | 3 | PASS | 95 | — | director_primary_pass | A\|inplace_patch | stage4/ep_0005/attempt_03/patched_after_fix__A_inplace_patch.txt | 1 |

### EP6
| id | stage | attempt_num | verdict | score | failure_category | gate_basis | candidate_key | artifact_path | is_patch |
|---|---|---|---|---|---|---|---|---|---|
| 15 | 3 | 3 | PASS | 95 | — | — | dialogue_focused | stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json | 0 |
| 23 | 4 | 1 | REJECT | 78 | CONSTRAINT_VIOLATION | director_primary_reject | A\|tension | stage4/ep_0006/attempt_01/rejected_best__A_tension.txt | 0 |
| 24 | 4 | 2 | REJECT | 44 | LOGIC_ERROR | continuity_firewall | A\|tension | stage4/ep_0006/attempt_02/rejected_best__A_tension.txt | 1 |
| 25 | 4 | 3 | PASS | 98 | — | director_primary_pass | A\|균형 전략 | stage4/ep_0006/attempt_03/final_manuscript__A.txt | 0 |

### EP7
| id | stage | attempt_num | verdict | score | failure_category | gate_basis | candidate_key | artifact_path | is_patch |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 3 | 1 | PASS | 95 | — | — | emotion_focused | stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json | 0 |
| 26 | 4 | 1 | PASS | 90 | — | patch_reaudit_pass | A\|InPlace 수정 | stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt | 1 |

---

## E-2. director_selections EP5-7 (DB)

Source: `projects/0324_00_/project_data.db` table `director_selections`

### EP5
| id | stage | round_num | verdict | score | pre_firewall_score | firewall_triggered | artifact_path |
|---|---|---|---|---|---|---|---|
| 14 | 3 | 1 | PASS | 95 | 0 | 0 | stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json |
| 20 | 4 | 0 | PASS_WITH_FIX | 93 | 93 | 0 | stage4/ep_0005/attempt_01/selected_before_fix__B.txt |
| 21 | 4 | 1 | PASS_WITH_FIX | 93 | 93 | 0 | stage4/ep_0005/attempt_02/selected_before_fix__A_inplace_patch.txt |
| 22 | 4 | 2 | PASS | 95 | 95 | 0 | stage4/ep_0005/attempt_03/selected_candidate__A_inplace_patch.txt |

### EP6
| id | stage | round_num | verdict | score | pre_firewall_score | firewall_triggered | artifact_path |
|---|---|---|---|---|---|---|---|
| 15 | 3 | 3 | PASS | 95 | 0 | 0 | stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json |
| 23 | 4 | 0 | REJECT | 78 | 83 | 0 | stage4/ep_0006/attempt_01/rejected_best__A.txt |
| 24 | 4 | 1 | REJECT | 44 | 69 | 1 | stage4/ep_0006/attempt_02/rejected_best__A.txt |
| 25 | 4 | 2 | PASS | 98 | 98 | 0 | stage4/ep_0006/attempt_03/selected_candidate__A.txt |

### EP7
| id | stage | round_num | verdict | score | pre_firewall_score | firewall_triggered | artifact_path |
|---|---|---|---|---|---|---|---|
| 16 | 3 | 1 | PASS | 95 | 0 | 0 | stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json |
| 26 | 4 | 0 | PASS_WITH_FIX | 94 | 94 | 0 | stage4/ep_0007/attempt_01/selected_before_fix__B.txt |

---

## E-3. Content Hash Cross-Check

| EP | Stage | stage_attempts hash | director_selections hash | Match? | Explanation |
|---|---|---|---|---|---|
| 5 | 3 | `b1838d9a4eb80eae` | `b1838d9a4eb80eae` | YES | Same blueprint |
| 5 | 4 (PASS) | `e00050bda8b59aaa` | `e00050bda8b59aaa` | YES | Same final content |
| 6 | 3 | `8fbbe6ef0d250ccf` | `8fbbe6ef0d250ccf` | YES | Same blueprint |
| 6 | 4 (PASS) | `c7a34baa90a606e5` | `c7a34baa90a606e5` | YES | Same final content |
| 7 | 3 | `8c9dc95ed5c10124` | `8c9dc95ed5c10124` | YES | Same blueprint |
| 7 | 4 (PASS) | `706888828a28c582` | `cbf852bd797cda72` | NO | Expected: patch changed content |

---

## E-4. Artifact Path Dual-Write Verification

Physical files confirmed on filesystem:

### EP5 Stage 4
```
attempt_01/selected_before_fix__B.txt         (13,051 bytes, 18:34)
attempt_01/rejected_best__B_balanced.txt      (13,051 bytes, 18:37)
attempt_02/selected_before_fix__A_inplace_patch.txt  (13,264 bytes, 18:40)
attempt_02/rejected_best__A_inplace_patch.txt        (13,264 bytes, 18:41)
attempt_03/selected_candidate__A_inplace_patch.txt   (13,051 bytes, 18:46)
attempt_03/patched_after_fix__A_inplace_patch.txt    (13,051 bytes, 18:46)
```

### EP6 Stage 4
```
attempt_01/rejected_best__A.txt         (11,704 bytes, 18:53)
attempt_01/rejected_best__A_tension.txt (11,704 bytes, 18:54)
attempt_02/rejected_best__A.txt         (11,765 bytes, 18:58)
attempt_02/rejected_best__A_tension.txt (11,765 bytes, 18:58)
attempt_03/selected_candidate__A.txt    (11,500 bytes, 19:03)
attempt_03/final_manuscript__A.txt      (11,500 bytes, 19:03)
```

### EP7 Stage 4
```
attempt_01/selected_before_fix__B.txt        (13,455 bytes, 19:12)
attempt_01/patched_after_fix__A_InPlace.txt  (13,455 bytes, 19:15)
```

All pairs have identical byte sizes. No orphaned or missing files.

---

## E-5. Episode Production Pathology Entries

Source: `projects/0324_00_/logs/episode_production.jsonl`

| EP | Round | Gate Basis | Contradiction Type | Score | Plateau? | Firewall? |
|---|---|---|---|---|---|---|
| 5 | 1 | post_select_conflict | 레버리지계산 | 93 | no | no |
| 5 | 2 | post_select_conflict | 수치 | 93 | yes | no |
| 6 | 1 | director_primary_reject | 타임라인 | 83* | no | no |
| 6 | 2 | continuity_firewall | 자본금정합 | 69* | no | yes |

*Episode production records pre-firewall scores; stage_attempts records post-adjustment scores (78, 44).

EP6 round 2 also has `fix_pack_ready: false` with `fix_pack_reason: missing_fix_pack`.

---

## E-6. Quality Metrics Validation Chain

Source: `projects/0324_00_/logs/quality_metrics.jsonl`

| Line | EP | Stage | Type | Decision | Score | Key Detail |
|---|---|---|---|---|---|---|
| L32 | 5 | 3 | validation | PASS | 95 | warnings=1, revision_required=true |
| L34 | 6 | 3 | validation | PASS | 95 | warnings=1, revision_required=true |
| L36 | 7 | 3 | validation | PASS | 95 | warnings=0, revision_required=false |
| L47 | 5 | 4 | validation | REJECT | 93 | violations=["director_reject"] |
| L49 | 5 | 4 | validation | REJECT | 93 | violations=["director_reject"] |
| L52 | 5 | 4 | validation | PASS | 95 | — |
| L55 | 6 | 4 | validation | REJECT | 78 | violations=["director_reject"] |
| L57 | 6 | 4 | validation | REJECT | 44 | violations=["director_reject"] |
| L60 | 6 | 4 | validation | PASS | 98 | — |
| L64 | 7 | 4 | validation | PASS | 90 | — |

Blueprint coverage:
| Line | EP | Coverage | Expected | Reflected | Valid |
|---|---|---|---|---|---|
| L51 | 5 | 100% | 5 | 5 | true |
| L59 | 6 | 60% | 5 | 3 | false |
| L63 | 7 | 60% | 5 | 3 | false |

---

## E-7. Runtime Audit EP5-7

Source: `projects/0324_00_/logs/runtime_audit.jsonl` (ep_num inside `data` field)

| Line | EP | Type | Message |
|---|---|---|---|
| L26 | 5 | blueprint_success | ep_5_blueprint_generated |
| L28 | 6 | blueprint_success | ep_6_blueprint_generated |
| L30 | 7 | blueprint_success | ep_7_blueprint_generated |
| L35 | 5 | stage4_retry_pathology_signal | stage4 retry pathology observed |
| L36 | 5 | stage4_retry_pathology_signal | stage4 retry pathology observed |
| L37 | 6 | stage4_retry_pathology_signal | stage4 retry pathology observed |
| L38 | 6 | stage4_retry_pathology_signal | stage4 retry pathology observed |
| L39 | 6 | stage4_cove_runtime_advisory | stage4 CoVe runtime advisory observed |

**EP7 has ZERO stage4 entries** despite PASS_WITH_FIX → patch → pass cycle.

Runtime audit self-declares non-authoritative:
> `contract.attempt_truth_authoritative: False`
> `contract.authoritative_attempt_sinks: ['stage_attempts', 'pass_rate_monitor', 'session_decisions', 'episode_production', 'director_selections']`

---

## E-8. State Changes and State Logs Comparison

Source: `projects/0324_00_/logs/session/state_changes.jsonl` (lines 9-14), `project_data.db` table `state_logs`

### Capital Trail
| EP | state_changes.capital | state_logs.capital | state_logs.total_assets |
|---|---|---|---|
| 4 | "19억 원" | (not checked) | — |
| 5 | "19억 원 (약 195만 달러)" | 1,958,762.88 | 1,958,762.88 |
| 6 | "19억 원 (전액 WTI 증거금)" | 1,950,000.0 | 1,950,000.0 |
| 7 | "19억 + 15억 (positions)" | 0 | 3,400,000,000 |

### Inventory Count Consistency
| EP | state_changes item count | state_changes deltas |
|---|---|---|
| 5 | 6 items | +24인치 모니터, +데스크톱 본체 |
| 6 | 7 items | +로로피아나 캐시미어 코트 |
| 7 | 8 items | +WTI 3배 레버리지 매수 체결 확인서 |

Inventory counts are monotonically increasing across EP5-7, consistent with the story progression.

---

## E-9. Cost Log EP5-7

Source: `projects/0324_00_/project_data.db` table `cost_log`

| id | EP | Round | Event | Bucket | Tokens | Cost USD |
|---|---|---|---|---|---|---|
| 11 | 5 | 0 | stage4_reject | constraint_violation | 0 | 0.00 |
| 12 | 5 | 1 | stage4_reject | constraint_violation | 0 | 0.00 |
| 13 | 5 | final | episode_complete | — | 549,029 | 0.99 |
| 14 | 6 | 0 | stage4_reject | constraint_violation | 0 | 0.00 |
| 15 | 6 | 1 | stage4_reject | post_select_conflict | 0 | 0.00 |
| 16 | 6 | final | episode_complete | — | 668,092 | 1.08 |
| 17 | 7 | final | episode_complete | — | 397,388 | 0.71 |

Reject events record `total_tokens: 0, total_cost_usd: 0.0` — cost is only recorded at episode completion. EP7 has no reject events, consistent with no hard rejection.

---

## E-10. Manuscripts and Blueprints (DB Summary)

| EP | Manuscript Title | Content Length | Blueprint Length | Created At |
|---|---|---|---|---|
| 5 | 제5화 | 5,585 chars | 6,392 chars | 09:46:50 |
| 6 | 제6화: 타이밍의 재구성 | 4,876 chars | 7,957 chars | 10:03:47 |
| 7 | 제7화: 허울뿐인 브리핑의 종말 | 5,641 chars | 4,991 chars | 10:15:11 |

All three manuscripts exist in DB with non-zero content. Timestamps are consistent with the production timeline (EP5 before EP6 before EP7).

---

## E-11. EP5-7 Rejection Reason Categorization

| EP | Round | Director Reason | System Override Reason | Contradiction Category |
|---|---|---|---|---|
| 5 | a1 | "3배 레버리지를 의도한다는 독백과 실제 480계약(15배 풀레버리지) 산술 불일치" | post_select_conflict | 레버리지 계산 |
| 5 | a2 | "잔고 19억 원에 대한 설명 문구에서 산술적 오류" | post_select_conflict | 수치 |
| 6 | a1 | "타임라인 오류 (2006년 2월 하순 → 4월 18일)" | director_primary_reject | 타임라인 |
| 6 | a2 | "Contradiction Firewall: CRITICAL 1건" (20억 현금 등장) | continuity_firewall | 자본금 정합 |
| 7 | — | PASS_WITH_FIX: "'18년 전' → '전생에' 수정" | (patched, not rejected) | 타임라인 |

All rejection reasons are **Stage 4 content-level contradictions**: capital math, leverage arithmetic, timeline anchors. None trace to DB corruption, metadata loss, or sink desync.
