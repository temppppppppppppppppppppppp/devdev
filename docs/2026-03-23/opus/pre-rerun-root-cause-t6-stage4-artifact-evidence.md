Date: 2026-03-23
Document Type: evidence manifest
Terminal: T6
Focus: Stage 4 attempt artifact truth
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-evidence.md`

---

## Artifact File Inventory

### Stage 4 Artifacts

| Path | Bytes | Chars | SHA-256 (first 16) |
|------|-------|-------|--------------------|
| `ep_0001/attempt_01/selected_candidate__C.txt` | 12,411 | 5,221 | `6d302a22929a3fec` |
| `ep_0001/attempt_01/final_manuscript__C.txt` | 12,411 | 5,221 | `6d302a22929a3fec` |
| `ep_0002/attempt_01/selected_candidate__C.txt` | 12,971 | 5,401 | `b0f62e1ce8e3e11a` |
| `ep_0002/attempt_01/final_manuscript__C.txt` | 12,971 | 5,401 | `b0f62e1ce8e3e11a` |
| `ep_0003/attempt_01/rejected_best__C.txt` | 13,486 | 5,630 | verified via DB |
| `ep_0003/attempt_01/rejected_best__C_balanced.txt` | 13,486 | 5,630 | `446f46e86253` (DB match) |
| `ep_0003/attempt_03/rejected_best__A.txt` | 12,326 | 5,244 | verified via DB |
| `ep_0003/attempt_03/rejected_best__A_balanced.txt` | 12,326 | 5,244 | `05111a98b4f2` (DB match) |
| `ep_0003/attempt_04/selected_candidate__A_asp_correction.txt` | 12,560 | 5,340 | `45a3d6ff63bf` (DB match) |
| `ep_0003/attempt_04/rejected_best__A_asp_correction.txt` | 12,560 | 5,340 | verified via DB |
| `ep_0003/attempt_05/selected_candidate__A.txt` | 12,568 | 5,344 | `29637065aa01` (DB match) |
| `ep_0003/attempt_05/patched_after_fix__A.txt` | 12,568 | 5,344 | `29637065aa01` (DB match) |

### Draft Files

| Path | Bytes | Chars | Contains Artifact? |
|------|-------|-------|--------------------|
| `drafts/ep_0001.txt` | 12,520 | 5,312 | YES (selected_candidate__C, +91 chars title) |
| `drafts/ep_0002.txt` | 13,128 | 5,546 | YES (selected_candidate__C, +145 chars title) |
| `drafts/ep_0003.txt` | 12,831 | 5,593 | YES (patched_after_fix__A, +249 chars title) |

## DB Evidence

### stage_attempts (stage=4)

| ep | att | verdict | score | fail_cat | fix_scope | rr_len | vr_len | sr_len | rd_len | initial_verdict | is_patch | content_hash |
|----|-----|---------|-------|----------|-----------|--------|--------|--------|--------|-----------------|----------|--------------|
| 1 | 1 | PASS | 98 | NULL | inplace | 0 | 219 | 219 | 0 | PASS | 0 | 6d302a22929a |
| 2 | 1 | PASS | 98 | NULL | inplace | 0 | 183 | 183 | 0 | PASS | 0 | b0f62e1ce8e3 |
| 3 | 1 | REJECT | 80 | NULL | partial | 2576 | 76 | 147 | 0 | NULL | 0 | 446f46e86253 |
| 3 | 2 | EMPTY | 0 | NULL | NULL | 16 | 0 | 0 | 0 | NULL | 1 | NULL |
| 3 | 3 | REJECT | 76 | NULL | full | 4338 | 123 | 192 | 2941 | NULL | 0 | 05111a98b4f2 |
| 3 | 4 | REJECT | 98 | NULL | partial | 3394 | 239 | 239 | 1532 | NULL | 0 | 45a3d6ff63bf |
| 3 | 5 | PASS | 98 | NULL | inplace | 0 | 202 | 202 | 0 | PASS | 1 | 29637065aa01 |

### director_selections (stage=4)

| ep | round | verdict | score | label | hash (12) | thinking_len | fw | pre_fw_score |
|----|-------|---------|-------|-------|-----------|-------------|----|----|
| 1 | 0 | PASS | 98 | C | 6d302a22929a | 4116 | 0 | 98 |
| 2 | 0 | PASS | 98 | C | b0f62e1ce8e3 | 3261 | 0 | 98 |
| 3 | 0 | REJECT | 80 | C | 446f46e86253 | 4333 | 0 | 80 |
| 3 | 2 | REJECT | 76 | A | 05111a98b4f2 | 2602 | 0 | 76 |
| 3 | 3 | PASS | 98 | A | 45a3d6ff63bf | 2709 | 0 | 98 |
| 3 | 4 | PASS | 98 | A | 29637065aa01 | 2784 | 0 | 98 |

### manuscripts

| ep | content_len |
|----|-------------|
| 1 | 5,221 |
| 2 | 5,401 |
| 3 | 5,344 |

### attempt_raw_rationale (stage=4)

| attempt_key | kind | payload_len |
|-------------|------|-------------|
| s4:ep1:arc1:a1 | director_thinking | 4,116 |
| s4:ep1:arc1:a1 | advisory_warnings_raw | 1,964 |
| s4:ep2:arc1:a1 | director_thinking | 3,261 |
| s4:ep2:arc1:a1 | advisory_warnings_raw | 2,651 |
| s4:ep3:arc1:a1 | director_thinking | 4,333 |
| s4:ep3:arc1:a1 | advisory_warnings_raw | 3,704 |
| s4:ep3:arc1:a3 | director_thinking | 2,602 |
| s4:ep3:arc1:a3 | advisory_warnings_raw | 3,133 |
| s4:ep3:arc1:a4 | director_thinking | 2,709 |
| s4:ep3:arc1:a4 | advisory_warnings_raw | 3,371 |
| s4:ep3:arc1:a5 | director_thinking | 2,784 |
| s4:ep3:arc1:a5 | advisory_warnings_raw | 2,012 |

## Timeline Evidence: Blueprint vs Manuscript

### Blueprint (`blueprint_0003.txt`) Key Passage

> "다음 날, 2006년 1월 18일의 해가 밝자마자 한시우의 방은 전쟁터로 변했다."

This places January 18th as "the next day" after scene 1's evening, implying scene 1 is on January 17th evening.

### Ep2 Established Timeline

- Ep2 covers the night of January 17 → morning/day of January 18
- Father-son meeting ("아버지와의 독대") happens during January 18
- Post-select continuity system correctly identifies the meeting date as January 18th

### Attempt 04 Artifact (`selected_candidate__A_asp_correction.txt` line 3)

> `[2006년 1월 17일, 저녁 / 유성그룹 회장 자택]`

LLM followed the blueprint's implicit January 17th dating. Post-select correctly rejected this.

### Attempt 05 Artifact (`selected_candidate__A.txt` line 3)

> `[2006년 1월 18일, 저녁 / 유성그룹 회장 자택]`

LLM corrected the date to match ep2's established timeline. Post-select passed.

### Final Draft (`drafts/ep_0003.txt` line 5)

> `[2006년 1월 18일, 저녁 / 유성그룹 회장 자택]`

Correct date preserved in final output.

## Console Anchors

| Line | Event |
|------|-------|
| 537 | Ep1 PASS score=98 candidate C |
| 629 | Ep2 PASS score=98 candidate C |
| 727 | Ep3 att01 REJECT score=80 candidate C |
| 752 | Ep3 att02 all candidates failed in patch mode |
| 810 | Ep3 att03 REJECT score=76 candidate A |
| 893 | Ep3 att04 PASS score=98 candidate A (ASP correction) |
| 902-909 | Post-select continuity conflicts: timeline error Jan 17 vs Jan 18 |
| 961 | Ep3 att05 PASS score=98 candidate A |
| 989 | Ep3 production complete: 5,344 chars |
