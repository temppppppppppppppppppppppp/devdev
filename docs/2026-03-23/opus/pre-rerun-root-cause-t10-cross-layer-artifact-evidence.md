Date: 2026-03-23
Document Type: evidence manifest (T10)
Terminal: T10
Focus: Cross-layer artifact continuity
Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md`

---

# T10 Evidence Manifest

## 1. Artifact Path Inventory

### Stage 2 (Arc)
| Path | Type | Size | Notes |
|------|------|------|-------|
| `projects/0_0323/plans/arcs/arc_001.txt` | Human-readable arc plan | — | 5 episodes, relative dates only |
| `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` | JSON arc artifact | 29,561 B | conservative strategy, score 95, ensemble_meta.all_scores: creative=100, balanced=95, conservative=95 |

### Stage 3 (Blueprints)
| Path | Strategy | Score | time_flow | ending_timeline |
|------|----------|-------|-----------|-----------------|
| `artifacts/stage3/ep_0001/attempt_02/final_blueprint__emotion_focused.json` | emotion_focused | — | "2006년 1월 17일, 아침부터 저녁까지" | 2006-01-17 Evening |
| `artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | emotion_focused | — | "2006년 1월 17일 아침부터 저녁까지" | **2006-01-17 Evening** (WRONG: actual draft ends 1/18 Evening) |
| `artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` | action_focused | 95 | **"2006년 1월 17일 저녁 ~ 1월 18일 저녁"** (WRONG: should be 1/18 저녁 ~ 1/19 저녁) | 2006-01-18 Evening |

### Stage 4 (Manuscripts — ep3 only)
| Attempt | Path | Candidate | Outcome | Score | Key Issue |
|---------|------|-----------|---------|-------|-----------|
| 01 | `attempt_01/rejected_best__C.txt` | C (balanced) | REJECT | 80 | Scene structure missing |
| 01 | `attempt_01/rejected_best__C_balanced.txt` | C copy | — | — | Same content as above |
| 02 | (no artifacts) | — | FAIL | 0 | All candidates failed to generate |
| 03 | `attempt_03/rejected_best__A.txt` | A (balanced) | REJECT | 76 | Scene structure missing |
| 03 | `attempt_03/rejected_best__A_balanced.txt` | A copy | — | — | Same content |
| 04 | `attempt_04/selected_candidate__A_asp_correction.txt` | A (ASP-corrected) | REJECT (post-select) | 98 | Date conflict: 1/17 vs 1/18 |
| 04 | `attempt_04/rejected_best__A_asp_correction.txt` | A copy | — | — | Rejected after post-select |
| 05 | `attempt_05/selected_candidate__A.txt` | A | PASS | 98 | Date corrected to 1/18 |
| 05 | `attempt_05/patched_after_fix__A.txt` | A (patched) | PASS | 98 | Final manuscript |

### Final Drafts
| Path | Bytes | Character Count | Status |
|------|-------|-----------------|--------|
| `projects/0_0323/drafts/ep_0001.txt` | 12,520 | ~4,200자 | PASS (1 attempt) |
| `projects/0_0323/drafts/ep_0002.txt` | 13,128 | ~5,837자 | PASS (1 attempt) |
| `projects/0_0323/drafts/ep_0003.txt` | 12,831 | 5,344자 | PASS (5 attempts) |

## 2. Date Contamination Evidence

### ep2 Draft vs ep2 Blueprint Date Mismatch

**ep2 draft** (`drafts/ep_0002.txt` L71):
```
저녁 8시, 한정호의 서재.
```
This is the evening of 1월 18일 (one night + one full day after ep1's 1월 17일 AM start).

**ep2 blueprint** (`final_blueprint__emotion_focused.json`):
```json
"ending_state": {
    "timeline": {
        "expression": "2006-01-17 Evening"
    }
}
```
This claims the episode ends on 1월 17일 Evening, which is **one day earlier** than the actual draft.

### ep3 Blueprint Inherits Wrong Date

**ep3 blueprint** (`final_blueprint__action_focused.json`):
```json
"time_flow": "2006년 1월 17일 저녁 ~ 1월 18일 저녁"
```
This starts from 1월 17일 저녁, matching ep2 blueprint's wrong ending date, not the actual ep2 draft ending date (1월 18일 저녁).

### Round 4 Post-Select Detection

**Console** L902-909:
```
[A-3] Post-select continuity conflict: 제3화의 시작 시점이 제2화에서 설정된 시간 흐름과 명백하게 충돌합니다.
아버지와의 독대는 1월 18일 저녁에 이루어졌어야 하나, 제3화에서는 1월 17일 저녁으로 잘못 기재
```
```
[A-3] 2 post-select conflicts detected -> downgrade to REJECT
```

### Round 5 Correction

**Final draft** (`ep_0003.txt` L3-5):
```
### 씬 1: 보이지 않는 감시망
[2006년 1월 18일, 저녁 / 유성그룹 회장 자택]
```

**씬 2** (`ep_0003.txt` L66-68):
```
### 씬 2: 자산 청산 작전
[2006년 1월 19일, 오전 / 한시우의 방]
```

Date is now correct (1/18 저녁 → 1/19 오전), matching ep2's actual ending.

## 3. Scene Detection False-Positive Evidence

### Console Pattern (all 5 rounds)

Round 1 (L673-677):
```
⚠️ 후보1 Python 검증 경고 1건 → Director에 전달
   - [HIGH] 씬 완성도 부족: 0/5 씬만 완성 (최소 50% 필요)
⚠️ 후보2 Python 검증 경고 1건 → Director에 전달
   - [HIGH] 씬 완성도 부족: 0/5 씬만 완성 (최소 50% 필요)
⚠️ 후보3 Python 검증 경고 1건 → Director에 전달
   - [HIGH] 씬 완성도 부족: 0/5 씬만 완성 (최소 50% 필요)
```

This pattern repeats identically in rounds 3, 4, and 5 (L762-767, L843-848, L924-927).

### CrossVerify Violation (same root cause)

Round 1 (L704):
```
[CrossVerify:VIOLATION] 5개 씬 중 0개만 감지됨 (0%)
```

### Accepted Draft Has Clear Scene Structure

```
### 씬 1: 보이지 않는 감시망       (matches blueprint scene_1.title)
### 씬 2: 자산 청산 작전           (matches blueprint scene_2.title)
### 씬 3: 금융가의 작은 파문       (matches blueprint scene_3.title)
### 씬 4: 마지막 퍼즐 조각        (matches blueprint scene_4.title)
### 씬 5: 예상 밖의 방문자         (matches blueprint scene_5.title)
```

## 4. Runtime Audit Anchors

| Entry | Timestamp | Round | Gate Basis | Score | Key Data |
|-------|-----------|-------|-----------|-------|----------|
| L13 | 14:25:37 | 1 | director_primary_reject | 80 | "씬 구분 미반영", fix_scope=partial |
| L14 | 14:31:35 | 2 | (empty) | 0 | All generation failed |
| L15 | 14:36:47 | 3 | director_primary_reject | 76 | "씬 구분 미반영" repeat |
| L17 | 14:44:37 | 4 | **post_select_conflict** | 98 | contradiction_type="아이템", fix_pack:missing |

## 5. Blueprint Prevalidation Warnings

From `final_blueprint__action_focused.json`:
```json
"python_warnings": [
    {
        "category": "structure",
        "message": "씬 구조 미비: 5/5개 씬에 goal/summary 없음",
        "severity": "MINOR"
    },
    {
        "category": "fidelity",
        "message": "intent 불일치: Arc 관계 변화 NPC 3명 blueprint 미언급",
        "severity": "MINOR"
    }
],
"quality_risk": true
```

The blueprint passed Stage 3 with `quality_risk: true` and 2 MINOR warnings. The empty scene fields were flagged but not treated as blocking.
