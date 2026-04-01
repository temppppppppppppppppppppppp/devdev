# OPUS office_checkup_next_day Concept Upgrade Order

Date: 2026-04-01
Track: narrative pipeline
Status: pending
Scope: single-work OPUS review order for `office_checkup_next_day`

## 1. Order Intent

This order fixes the target to `office_checkup_next_day` and asks OPUS to complete exactly one bounded unit:

- `existing pair concept-strength review`

This is **not** a rewrite order.

OPUS should decide how to make the work commercially stronger with the smallest profitable change set.

## 2. Current Lane Truth

- family: `blockguide`
- stage: existing `phase0 + TR + BI` pair
- target question: concept strengthening, not fresh production
- current local recommendation exists, but OPUS is allowed to disagree

Current local baseline:

- keep current office-power engine
- keep current logistics / SCM / MD texture
- strengthen with `group / chaebol exterior`

## 3. Non-Negotiable Rules

- UTF-8 only
- one work only
- review only
- no code edits
- no system edits
- no full rewrite of BI/TR
- no new engine injection (`회귀`, `빙의`, `시스템`, `상태창`, `재벌3세 회귀`)
- no romance pivot
- focus on minimal profitable change

## 4. Canonical Target

- work_id: `office_checkup_next_day`
- BI: `bible/0_bi_office_checkup_next_day.json`
- Phase 0: `treatments/office_checkup_next_day_phase0_design.json`
- Source manifest: `treatments/preprocess/office_checkup_next_day/source_manifest.json`

## 5. Core Problem Definition

The work is already functional.

What is under review is not:

- whether the engine works
- whether the opening spike exists

What is under review is:

- whether the work reads slightly too small on the outside
- whether a `chaebol / group exterior` should be added
- whether a sector shift would outperform a group-exterior patch

## 6. Current Strengths To Preserve

- 말단 사원 + 오피스 파워 손맛
- 조직 병목 / 숫자 은닉 / 결재선 읽기
- 건강검진 다음 날 발현 트리거
- Block 7 대표 spike
- Block 8 보상 4종
- no-romance 현실밀착형 능력물 톤

## 7. Option Set Under Review

### Option A. Keep current sector, add group exterior

Meaning:

- keep `한일유통` field texture
- reinterpret it as a `group core affiliate`
- raise project stakes from `company-level` to `group-signaling`

### Option B. Shift toward group strategy / chaebol strategy room

Meaning:

- move the opening battlefield upward
- turn the work into a semi-chaebol strategy-room narrative

### Option C. Keep engine, retarget sector

Meaning:

- keep office-power engine
- move to a flashier industrial arena such as:
  - semiconductor
  - pharma
  - OTT/media
  - datacenter/power

## 8. Evaluation Criteria

OPUS should rank options primarily by:

1. platform packaging strength (`Kakao / Naver / Munpia`)
2. preservation of current pair value
3. tactile reader satisfaction
4. increase in perceived stakes / scale
5. revision cost efficiency

## 9. Required Reads

Read these files first:

1. `docs/2026-04-01/modern-business-material-context-handoff.md`
2. `docs/2026-04-01/office_checkup_next_day-concept-upgrade-options.md`
3. `docs/2026-04-01/office_checkup_next_day-opus-context-memo.md`
4. `bible/0_bi_office_checkup_next_day.json`
5. `treatments/office_checkup_next_day_phase0_design.json`
6. `treatments/preprocess/office_checkup_next_day/source_manifest.json`
7. `narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_rollup.json`

## 10. Required Output

Return exactly these sections:

### 10.1 Verdict

- pick exactly one: `Option A`, `Option B`, or `Option C`

### 10.2 Why This Wins

- explain why the chosen option is strongest commercially
- explain briefly why the other two are weaker

### 10.3 Minimal Patch Set

- list `3-7` fields or narrative levers to patch
- each item should say:
  - target field / area
  - what changes
  - why it matters

### 10.4 Sharpened Copy

Give replacement-level copy for:

- `logline`
- `group_background`
- `grand_objective`
- `status_end` or end-state promise

### 10.5 Overcorrection Risk

- what would be ruined if the chosen path is pushed too far

## 11. Preferred Outcome Shape

If OPUS agrees with `Option A`, ideal answer shape is:

- confirm `유통사 코어 유지 + 그룹 외피 추가`
- identify exact BI fields to touch
- sharpen wording so the work reads more like:
  - `오피스 파워 + 그룹 계열사 + 승계전 그림자`

If OPUS chooses `Option B` or `Option C`, it must clearly justify why the extra rewrite cost is worth it.

## 12. Stop Conditions

Stop and flag if:

- the answer drifts into a full rewrite
- the answer proposes a new engine unrelated to the current work
- the answer ignores current pair value and treats this as blank-page ideation

## 13. Deliverable Type

- recommendation only
- no file rewrite required on OPUS side
- final goal is to inform the next internal patch pass

## 14. Minimal Paste Prompt

```text
너는 이번 런의 review-OPUS다. `docs/2026-04-01/opus-office_checkup_next_day-concept-upgrade-order.md`, `docs/2026-04-01/office_checkup_next_day-opus-context-memo.md`, `docs/2026-04-01/office_checkup_next_day-order-opus-brief.md`를 UTF-8로 읽고, `office_checkup_next_day` existing pair의 컨셉 강화 방향을 판정하라. 전면 재기획 금지, review only. A/B/C 중 하나를 고르고 minimal patch set과 sharpened copy를 제시하라.
```
