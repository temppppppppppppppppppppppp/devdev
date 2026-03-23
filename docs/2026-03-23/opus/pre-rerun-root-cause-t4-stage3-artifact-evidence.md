Date: 2026-03-23
Status: final
Document Type: evidence manifest
Terminal: T4
Focus: Stage 3 blueprint artifact and DB truth
Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md`

---

## 1. Artifact Inventory

### On-Disk Blueprint Artifacts

| Episode | Artifact Path | Size | Strategy | Content Hash |
|---------|--------------|------|----------|-------------|
| ep1 | `logs/artifacts/stage3/ep_0001/attempt_02/final_blueprint__emotion_focused.json` | 8,284 bytes | emotion_focused | `c1b67a6c...` |
| ep2 | `logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | 9,892 bytes | emotion_focused | `d7c5ee53...` |
| ep3 | `logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` | 8,192 bytes | action_focused | `ca333c4c...` |
| ep4 | `logs/artifacts/stage3/ep_0004/attempt_01/final_blueprint__dialogue_focused.json` | 9,196 bytes | dialogue_focused | `39f06f1f...` |

### Blueprint Text Files

| Episode | Path | Size |
|---------|------|------|
| ep1 | `plans/blueprints/blueprint_0001.txt` | 6,137 bytes |
| ep2 | `plans/blueprints/blueprint_0002.txt` | 7,516 bytes |
| ep3 | `plans/blueprints/blueprint_0003.txt` | 5,158 bytes |
| ep4 | `plans/blueprints/blueprint_0004.txt` | 6,226 bytes |

### Missing Artifacts

| Item | Expected | Status |
|------|----------|--------|
| ep1 attempt_01 artifacts | `logs/artifacts/stage3/ep_0001/attempt_01/` | NOT PRESENT — only attempt_02 directory exists |

---

## 2. DB Evidence

### stage_attempts (Stage 3)

| id | ep | attempt | verdict | score | sr_len | vr_len | or_len | sb |
|----|-----|---------|---------|-------|--------|--------|--------|----|
| 2 | 1 | 2 | PASS | 92 | 0 | 0 | 0 | None |
| 3 | 2 | 1 | PASS | 95 | 0 | 0 | 0 | None |
| 4 | 3 | 1 | PASS | 95 | 0 | 0 | 0 | None |
| 5 | 4 | 1 | PASS | 98 | 0 | 0 | 0 | None |

### stage_attempts (Stage 4, for comparison)

| id | ep | attempt | verdict | score | sr_len | vr_len | or_len | sb_len |
|----|-----|---------|---------|-------|--------|--------|--------|--------|
| 6 | 1 | 1 | PASS | 98 | 219 | 219 | 80 | 120 |
| 7 | 2 | 1 | PASS | 98 | 183 | 183 | 141 | 120 |
| 8 | 3 | 1 | REJECT | 80 | 147 | 76 | 237 | 120 |
| 12 | 3 | 4 | PASS | 98 | 202 | 202 | 144 | 120 |

### director_selections (Stage 3)

| id | ep | round | label | strategy | verdict | score | candidate_count | fix_scope |
|----|-----|-------|-------|----------|---------|-------|----------------|-----------|
| 2 | 1 | 2 | A | emotion_focused | PASS | 92 | 1 | (empty) |
| 3 | 2 | 1 | B | emotion_focused | PASS | 95 | 3 | inplace |
| 4 | 3 | 1 | B | action_focused | PASS | 95 | 3 | inplace |
| 5 | 4 | 1 | C | dialogue_focused | PASS | 98 | 3 | inplace |

### attempt_raw_rationale

| Stage | Count |
|-------|-------|
| 3 | **0** |
| 4 | 12 |

### blueprints table

| ep_num | data_len |
|--------|----------|
| 1 | 4,310 |
| 2 | 5,186 |
| 3 | 4,715 |
| 4 | 5,466 |

---

## 3. LLM Call Evidence (Stage 3)

Total: 28 LLM calls, 100% success

| Episode | Generator Calls | Director Calls | Total | Initial Verdict | Final |
|---------|----------------|----------------|-------|-----------------|-------|
| ep1 | 4 | 6 | 10 | PASS_WITH_FIX | PASS (attempt 2) |
| ep2 | 4 | 3 | 7 | PASS_WITH_FIX | PASS |
| ep3 | 4 | 3 | 7 | PASS_WITH_FIX | PASS |
| ep4 | 3 | 1 | 4 | PASS | PASS |

### Context Caching

| Episode | Cached Tokens | Status |
|---------|--------------|--------|
| ep1 | 0 | cache not yet warmed |
| ep2 | 0 | cache not yet warmed |
| ep3 | 2,534 | cache active |
| ep4 | 0 | clean pass, no caching needed |

---

## 4. Runtime Log Evidence

### runtime_audit.jsonl (Stage 3 entries: 1)

```
timestamp: 2026-03-23 14:03:38
type: continuity_pin_unresolved
message: stage3 continuity pin unresolved
data: ep_num=4, proper_noun_pin "SW인베스트먼트" expected but not matched
```

### decisions.jsonl (Stage 3 entries: 4)

All 4 episodes recorded as `decision_type=blueprint`, `result=PASS`, with `quality_risk=True` for all.

### ui_events (Stage 3 entries: 16)

4 episodes x 4 events each (progress, heartbeat, result, summary).

---

## 5. Console Evidence Anchors

| Line | Content | Relevance |
|------|---------|-----------|
| 401 | `📐 [Stage 3] Blueprint frontier 동기화 (target <= ep 4)...` | Stage 3 start |
| 418 | `📊 제1화 Blueprint 결과: PASS (score=92)` | ep1 result |
| 427 | `📊 제2화 Blueprint 결과: PASS (score=95)` | ep2 result |
| 437 | `📊 제3화 Blueprint 결과: PASS (score=95)` | ep3 result |
| 447 | `📊 제4화 Blueprint 결과: PASS (score=98)` | ep4 result |
| 451 | `[PinGuard][WARN] ep 4 unresolved continuity pins` | F-6 evidence |
| 458 | `통과율: 83.3%` | F-5 pass rate display bug |

---

## 6. Source Code Anchors

| Finding | File | Lines | What |
|---------|------|-------|------|
| F-1 | `modules/core/stage3_orchestrator.py` | 1858-1874 | PASS path `save_stage_attempt()` — 14 kwargs, missing 6 metadata fields |
| F-1 | `modules/core/stage3_orchestrator.py` | 2624-2642 | REJECT path `save_stage_attempt()` — adds failure_category and reject_reason but still missing 4 metadata fields |
| F-1 | `modules/core/stage3_orchestrator.py` | 1875-1879 | `save_director_selection()` call with `selection_kwargs` — this path DOES save selection_reason and verdict_reason |

---

## 7. Cross-Layer Content Comparison

### Arc Plan ep3 vs Blueprint ep3

| Dimension | Arc Plan (`arc_001.txt` ep3) | Blueprint ep3 | Match |
|-----------|---------------------------|---------------|-------|
| Narrative core | 자산 정리, 20억 현금 확보 | 가족 감시망 속 20억 종잣돈 확보 | YES (elaboration) |
| Start location | 성북동 본가 한시우의 방 | 성북동 본가 서재와 한시우의 방 | YES (refined) |
| End location | 성북동 본가 한시우의 방 | 성북동 본가 한시우의 방 | YES |
| Start assets | 변동 없음 (from ep2) | (from ep2 ending state) | YES |
| End assets | 약 20억원의 현금 확보 | 개인 명의 계좌 잔고 약 20억 원 | YES |
| Timeline | ep2 다음날 | 2006-01-18 | YES (consistent) |
| Key tension | 자산 정리 = 과거 청산 의식 | 시간 싸움 + 가족 감시 | YES (elaboration with conflict) |
| Cliffhanger | (none in arc plan) | 둘째 형 한태민 등장, 직접 견제 | ADDED (blueprint enrichment) |
