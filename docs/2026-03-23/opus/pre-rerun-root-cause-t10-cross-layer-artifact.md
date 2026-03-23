Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey (T10)
Terminal: T10
Focus: Cross-layer artifact continuity
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md`
Temp Mirror Path: none
Source Evidence:
- `projects/0_0323/plans/arcs/arc_001.txt`
- `projects/0_0323/plans/blueprints/blueprint_0003.txt`
- `projects/0_0323/drafts/ep_0001.txt`, `ep_0002.txt`, `ep_0003.txt`
- `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/0_0323/logs/artifacts/stage3/ep_0001/attempt_02/final_blueprint__emotion_focused.json`
- `projects/0_0323/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json`
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C.txt`
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_03/rejected_best__A.txt`
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_04/selected_candidate__A_asp_correction.txt`
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/selected_candidate__A.txt`
- `projects/0_0323/logs/runtime_audit.jsonl` (entries 9, 13-17)
- `docs/2026-03-23/console.txt` (L434-989)

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: dirty workspace allowed; survey-only, no code changes

---

# T10: Cross-Layer Artifact Continuity

## 1. Executive Summary

Arc 1 Episode 3 is the critical diagnostic episode for cross-layer artifact continuity. It required **5 Stage 4 rounds** (29 minutes, ~15+ LLM calls) while episodes 1 and 2 each passed on attempt 1. The root cause chain spans all three stages:

1. **Stage 2 (Arc)**: The arc uses only relative time references ("다음 날 아침", "저녁 식사 후") without absolute dates. This is structurally correct but leaves date resolution to downstream stages.
2. **Stage 3 (Blueprint)**: The blueprint generator produced a **wrong `time_flow` metadata field** for ep3 ("2006년 1월 17일 저녁 ~ 1월 18일 저녁"), off by one day. The error was inherited from ep2's blueprint, which also had wrong ending dates. Crucially, the blueprint's `integrated_scenario` narrative was correct — the metadata diverged from the text.
3. **Stage 4 (Manuscripts)**: Early candidates followed the blueprint's wrong metadata dates and were correctly rejected by post-select continuity checks. The system self-corrected on round 5.

**Primary blocker**: Blueprint `time_flow` metadata does not synchronize with actual manuscript dates, creating cross-layer date contamination that wastes 4 rounds per affected episode.

**Secondary amplifier**: Python scene-detection false-positives ("0/5 씬만 완성") flagged on every candidate in every round, adding noise that contributed to rounds 1-3 REJECT even when the narrative content was acceptable.

Fresh-run-before-fix allowed: **no** — the date contamination and scene-detection false-positive will recur and waste compute on every episode boundary where relative dates need resolution.

## 2. Current Ownership / Flow Map

### Cross-Layer Data Flow: Arc → Blueprint → Manuscript

```
Stage 2: Arc Plan (arc_001.txt)
  ├─ ep_num, beat_sequence, tactical_doc (narrative text with relative dates)
  ├─ start_state / end_state (location, equipment, assets — NO absolute dates)
  └─ Output: plans/arcs/arc_001.txt + artifacts/stage2/arc_001/.../final_arc__conservative.json

      ↓ (arc plan feeds into blueprint generation)

Stage 3: Blueprint (blueprint_0003.txt)
  ├─ integrated_scenario (narrative text — correct dates possible)
  ├─ time_flow (metadata field — LLM resolves relative→absolute dates HERE)
  ├─ ending_state.timeline (metadata — should match time_flow)
  ├─ scene_breakdown (5 scenes: title, type, tension — goal/summary/content EMPTY)
  └─ Output: plans/blueprints/blueprint_0003.txt + artifacts/stage3/ep_0003/.../final_blueprint__action_focused.json

      ↓ (blueprint + arc + prev manuscripts feed into writer)

Stage 4: Manuscript (drafts/ep_0003.txt)
  ├─ ChiefWriter generates 3 candidates per round
  ├─ Python pre-validation (scene detection, continuity, length)
  ├─ Director selects best candidate, applies gates
  ├─ Post-select checks (continuity/history conflict detection)
  └─ Output: drafts/ep_0003.txt + artifacts/stage4/ep_0003/attempt_NN/
```

### Date Resolution Ownership

| Layer | Date Source | Authority | Issue |
|-------|-----------|-----------|-------|
| Arc (S2) | Relative ("다음 날 아침") | Arc narrative only | No absolute dates — by design |
| Blueprint (S3) | `time_flow` metadata | Blueprint LLM | **Resolves relative→absolute dates, but reads prev blueprint metadata, not prev draft text** |
| Manuscript (S4) | Inline date markers | ChiefWriter LLM | May follow blueprint metadata (wrong) or prev manuscript text (right) |
| Post-select | Compares manuscript vs prev manuscript | Continuity checker | **Correctly catches date conflicts** |

## 3. Focus-Scope Findings

### F1 (P0): Blueprint `time_flow` Metadata Does Not Reflect Actual Manuscript Dates

**Evidence — Blueprint date chain:**

| Episode | Blueprint `time_flow` | Blueprint `ending_timeline` | Actual Draft Dates |
|---------|----------------------|----------------------------|-------------------|
| ep1 | "2006년 1월 17일, 아침부터 저녁까지" | 2006-01-17 Evening | 1월 17일 AM 09:14 → evening (correct) |
| ep2 | "2006년 1월 17일 아침부터 저녁까지" | 2006-01-17 Evening | **1월 17일 밤 → 1월 18일 저녁** (blueprint WRONG) |
| ep3 | "2006년 1월 17일 저녁 ~ 1월 18일 저녁" | 2006-01-18 Evening | **1월 18일 저녁 → 1월 19일 오후** (blueprint WRONG) |

**Root cause mechanism**: The ep2 blueprint claimed its ending date was "2006-01-17 Evening", but the ep2 draft actually ends on 1월 18일 저녁 (the father meeting at 저녁 8시). When the ep3 blueprint was generated, it used ep2's blueprint `ending_timeline` (1/17 Evening) as the starting point, producing a 1-day offset that propagated into ep3's `time_flow`.

**File anchors**:
- ep2 blueprint: `artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` → `ending_state.timeline.expression = "2006-01-17 Evening"`
- ep3 blueprint: `artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` → `time_flow = "2006년 1월 17일 저녁 ~ 1월 18일 저녁"`
- ep2 draft: `drafts/ep_0002.txt` L71 → "저녁 8시, 한정호의 서재" (this is 1월 18일, not 1월 17일)

**Impact**: Stage 4 manuscripts that followed the blueprint's `time_flow` metadata inherited the wrong date, causing rounds 1, 3, and 4 to produce date-inconsistent manuscripts. Only the post-select continuity check prevented a wrong-date draft from being saved.

**Why it is root-causal**: This is not a display error or observability gap. It is a **data-flow contamination** where incorrect metadata from one layer cascades to the next. Every episode that requires absolute date resolution from relative arc references is vulnerable.

**Fix type**: `contract-cleanup`

---

### F2 (P1): Python Scene-Detection Persistent False-Positive

**Evidence**: Console output for ep3 shows ALL candidates in ALL 5 rounds received:
```
[Python검증-HIGH] 씬 완성도 부족: 0/5 씬만 완성 (최소 50% 필요)
```

Yet the final accepted draft has clearly structured scenes:
```
### 씬 1: 보이지 않는 감시망
### 씬 2: 자산 청산 작전
### 씬 3: 금융가의 작은 파문
### 씬 4: 마지막 퍼즐 조각
### 씬 5: 예상 밖의 방문자
```

**Root cause**: The Python scene detector looks for specific format markers that don't match the LLM's actual output format. The detector likely expects something like `[씬 1]` or a JSON-like scene structure, while the LLM naturally produces `### 씬 N: Title` markdown headers.

**Impact**:
- Rounds 1-3 REJECT reasons cited "씬 구분 미반영" as the primary issue, partly influenced by this false HIGH warning
- Director received noise warnings that amplified rejection probability
- The `CrossVerify:VIOLATION 5개 씬 중 0개만 감지됨 (0%)` also came from the same detection logic
- Direct compute cost: 3 wasted rounds × 3+ LLM calls ≈ 9+ LLM calls (~$2+)

**File anchor**: Python scene detection logic likely in `modules/validation/` or `modules/core/stage4_interview_round.py` pre-validation section (not inspected per survey-only constraint).

**Why it is root-causal**: The false-positive is a **systematic sensor error** that affects every episode where the LLM produces markdown-formatted scenes. It is not downstream of the date issue — it is an independent root cause that amplified the retry cost.

**Fix type**: `contract-cleanup`

---

### F3 (P1): Blueprint `scene_breakdown` Has Empty Semantic Fields

**Evidence** (from `final_blueprint__action_focused.json`):
```json
"scene_1": {
    "characters": [],
    "content": "",
    "goal": "",
    "key_events": [],
    "location": "성북동 본가 서재와 한시우의 방",
    "summary": "",
    "tension_level": 7,
    "title": "보이지 않는 감시망",
    "type": "opening_hook"
}
```

All 5 scenes have empty `goal`, `summary`, `characters`, `key_events`, and `content` fields. The blueprint prevalidation correctly flagged this:
```json
"python_warnings": [
    {"message": "씬 구조 미비: 5/5개 씬에 goal/summary 없음", "severity": "MINOR"},
    {"message": "intent 불일치: Arc 관계 변화 NPC 3명 blueprint 미언급", "severity": "MINOR"}
]
```

**Impact**: ChiefWriter only has `title`, `type`, `tension_level`, and `location` as per-scene guidance. The `integrated_scenario` provides overall narrative, but scene-level character assignments, goals, and key events are absent. This means the Writer has to infer scene content, increasing variance and the probability of structural mismatches.

**Why it is root-causal for retry cost**: Director's rounds 1-3 REJECT cited "5개의 씬 구분이 원고에 전혀 반영되지 않았음" — but the blueprint itself provided only skeletal scene structure. The Writer and Director are locked in a loop where the Writer doesn't have enough scene-level guidance and the Director demands scene-level compliance.

**Fix type**: `contract-cleanup`

---

### F4 (positive finding): Post-Select Continuity Check Works Correctly

**Evidence**: Round 4 — Director gave PASS with score 98, but post-select checks detected:
```
[A-3] Post-select continuity conflict: 제3화의 시작 시점이 제2화에서 설정된 시간 흐름과 명백하게 충돌합니다.
아버지와의 독대는 1월 18일 저녁에 이루어졌어야 하나, 제3화에서는 1월 17일 저녁으로 잘못 기재
```
```
[A-3] 2 post-select conflicts detected -> downgrade to REJECT
```

The continuity checker correctly compared the manuscript against the previous episode's actual text (not the blueprint metadata) and caught the 1-day offset. This defense layer prevented a date-inconsistent episode from being saved.

**This is the system working as designed.** The post-select check is the critical cross-layer defense.

---

### F5 (P2): NPC `relation_to_protag` Drift Advisory Is Persistent Noise

**Evidence**: All 5 rounds flagged `한정호 relation_to_protag: 기대='목격자' → 원고='감시자/통제자'`. The NPC registry still lists 한정호 as "목격자" while the arc plan explicitly describes him as a "방관자/잠재적 적대자" who initiates surveillance.

**Impact**: Advisory-only, non-blocking. But it adds noise to Director's evaluation context.

**Fix type**: `ignore` (NPC registry update is a StateTracker/WorldState sync issue, covered by other lanes)

---

### F6 (observation): Cross-Layer Continuity Is Strong for ep1 and ep2

| Episode | S4 Attempts | Final Score | Post-Select Conflicts |
|---------|-------------|-------------|----------------------|
| ep1 | 1 | 100 | 0 |
| ep2 | 1 | 98 | 0 |
| ep3 | **5** | 98 | **2** (round 4, then 0 in round 5) |

Episodes 1 and 2 passed cleanly on first attempt. The cross-layer breakdown is localized to ep3, where the cumulative blueprint date drift became detectable.

## 4. Root-Cause Relevance

| Finding | Root Cause or Symptom? | Blocks Next Rerun? |
|---------|----------------------|-------------------|
| F1: Blueprint `time_flow` date contamination | **Root cause** — data-flow design gap between S3 metadata and S4 manuscript dates | Yes — will recur at every relative→absolute date boundary |
| F2: Python scene-detection false-positive | **Root cause** — sensor calibration error independent of content quality | Yes — wastes 3+ rounds per episode |
| F3: Empty scene_breakdown fields | **Root cause** — blueprint generator doesn't fill per-scene semantic fields | Partial — increases variance but doesn't guarantee failure |
| F4: Post-select check success | **Defense working** | No — this is protection, not a blocker |
| F5: NPC relation drift advisory | **Symptom** of stale NPC registry | No — advisory-only, non-blocking |
| F6: ep1/ep2 clean | **Observation** | No |

## 5. Quick Wins

### QW-1: Fix Python scene-detection regex/pattern to match `### 씬 N: Title` format
- Estimated effort: Small (regex/pattern update)
- Expected impact: Eliminates 100% of `씬 완성도 부족` false-positives, saves 3+ rounds per episode
- Fix type: `contract-cleanup`

### QW-2: Blueprint `time_flow` should reference previous manuscript's actual ending date, not previous blueprint's metadata
- Estimated effort: Medium (requires changing the context fed to the blueprint generator to include prev manuscript ending dates)
- Expected impact: Eliminates cross-layer date contamination
- Fix type: `boundary-refactor`

### QW-3: Fill `scene_breakdown` semantic fields (goal, summary, characters) in blueprint generator
- Estimated effort: Medium (prompt engineering + possibly schema enforcement)
- Expected impact: Reduces Writer/Director retry loop by giving scene-level guidance
- Fix type: `contract-cleanup`

## 6. False Leads / Non-Causes

### 6.1 "Director judgment inconsistency"
Director was consistent throughout:
- Rounds 1-3: Correctly rejected for scene structure problems
- Round 4: Correctly passed for content quality (98), then correctly overridden by post-select check for date conflict
- Round 5: Correctly passed after date was fixed

There is no split-brain or inconsistent judgment. The Director did its job. The problem was upstream (blueprint dates) and lateral (scene detection).

### 6.2 "ASP correction failure"
ASP correction worked on round 4 (delta: +24, fixing scene structure) but couldn't fix the date error because the date came from the blueprint, not from the candidate's quality. This is expected behavior — ASP corrects writing quality, not metadata contamination.

### 6.3 "Blueprint narrative quality"
The blueprint's `integrated_scenario` is narratively excellent — it correctly describes the scene sequence, character actions, and cliffhanger ending. The problem is entirely in the **metadata fields** (`time_flow`, `ending_state.timeline`), not the narrative content.

### 6.4 "V60.97 swap mechanism"
Not triggered for ep3. The V60.97 swap issue (identified in the fresh-run 3-pass audit for ep5) is unrelated to ep3's cross-layer continuity failure.

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed: no**

Reasons:
1. The blueprint `time_flow` metadata error will recur at every episode boundary where relative dates need resolution. A new run will hit the same problem.
2. The Python scene-detection false-positive will waste 3+ rounds on every episode, inflating cost and time.
3. The empty `scene_breakdown` fields will continue to cause Writer/Director retry loops.

**Top 3 highest-ROI fixes before the next rerun:**

1. **Fix Python scene-detection pattern** (QW-1) — eliminates false HIGH warnings, saves ~3 rounds per episode, highest ROI per effort
2. **Blueprint `time_flow` resolution from prev manuscript** (QW-2) — eliminates cross-layer date contamination root cause
3. **Fill blueprint scene_breakdown semantic fields** (QW-3) — reduces retry variance by giving Writer per-scene guidance

## 8. Confidence And Limits

**Estimated confidence: 96%**

**Basis:**
- All artifact files (arc, blueprint, 4 manuscript attempts, final draft) were directly inspected
- Console log was traced line-by-line for ep3 (L662-989)
- Runtime audit entries for ep3 rounds 1-4 were read
- Blueprint JSON metadata (time_flow, ending_state) was extracted and compared across ep1-ep3
- Draft content was cross-referenced for actual dates vs blueprint metadata dates
- The date contamination chain is triangulated across 3 independent evidence sources (blueprint JSON, console log, draft text)

**The 4% gap is from:**
- Scene detection source code was not inspected (survey-only constraint) — the exact regex/pattern is inferred from behavior (2%)
- Blueprint generator's context-feeding logic was not inspected — the claim that it reads prev blueprint metadata rather than prev manuscript text is inferred from the output pattern (2%)

---

## 3-Pass Audit Record

### Pass 1. Artifact Inventory
- Confirmed arc_001 (1 attempt), 4 blueprints (ep1-4), 3 drafts (ep1-3), 4 Stage 4 attempt directories for ep3
- Traced time_flow metadata across all 3 blueprint JSONs
- Confirmed ep1/ep2 passed in 1 attempt each, ep3 required 5 attempts

### Pass 2. Cross-Layer Date Tracing
- Confirmed ep2 blueprint ending date (2006-01-17 Evening) contradicts ep2 draft (meeting on 2006-01-18 저녁 8시)
- Confirmed ep3 blueprint time_flow (2006-01-17 저녁 ~ 1월 18일 저녁) inherited the wrong date
- Confirmed post-select check in round 4 correctly caught the date conflict
- Confirmed round 5 fixed the date to 2006-01-18 저녁

### Pass 3. Root-Cause vs Symptom Classification
- Separated 3 root causes (F1 date contamination, F2 scene detection, F3 empty scene fields) from 2 non-causes (Director judgment, ASP behavior)
- Confirmed each finding has file/line/artifact evidence
- Confirmed recommendations carry fix types and ROI ranking
