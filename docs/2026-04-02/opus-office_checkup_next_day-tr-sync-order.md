# OPUS office_checkup_next_day TR Sync Spot-Audit Order

Date: 2026-04-02
Track: narrative pipeline
Status: pending
Scope: single-work OPUS spot audit for `office_checkup_next_day`

## 1. Order Intent

This order asks OPUS to review exactly one bounded question:

- `after-sync spot audit for remaining micro-inconsistencies`

This is **not** a rewrite order.
This is **not** a new concept review.

## 2. Current Lane Truth

- family: `blockguide`
- stage: existing `phase0 + TR + BI` pair
- recent local action:
  - `phase0` and `BI` were upgraded to `유통 코어 유지 + 그룹 외피 추가`
  - `TR` was then synchronized to that upgraded direction
- current question:
  - after the TR sync, are any **remaining** micro-patches still necessary?

## 3. Non-Negotiable Rules

- UTF-8 only
- one work only
- review only
- no full rewrite
- no engine replacement
- no sector swap
- no new ideation
- no romance pivot
- no `회귀 / 빙의 / 상태창 / 시스템` injection
- focus only on bounded post-sync consistency

## 4. Canonical Target Files

1. `treatments/office_checkup_next_day_phase0_design.json`
2. `treatments/office_checkup_next_day_tr_block_070_draft.json`
3. `bible/0_bi_office_checkup_next_day.json`

## 5. Current Ground Truth

The pair has already been upgraded to this baseline:

- `한일유통` is now a `한일그룹 유통 핵심 계열사`
- opening spike is now `그룹 핵심 계열사의 최대 투자안`
- end-state is now `한일유통 경영기획팀장 + 그룹 구조조정 TF 실무총괄`
- late-arc pressure includes `그룹 구조조정 상무`

Local judgment:

- the TR sync is broadly successful
- there may still be `2-3` micro-level alignment issues
- these do **not** currently look like full blockers

## 6. Specific Findings Under Review

### Finding A. NPC introduction timing drift

- `그룹 구조조정 상무` is currently declared in `phase0` / `BI` as introduced in `ARC-06`
- but the first clear TR body appearance is at `Block 62 / ARC-07`

Question for OPUS:

- Is this an actual repair-worthy chronology inconsistency?
- If yes, should the fix move the intro earlier, or move the metadata later?

### Finding B. Phase 0 final-status ceiling is slightly weaker

- `phase0` final-status wording still reads roughly as:
  - `라인 선택권 보유자, 유통사 핵심 의사결정 노드`
- but `BI` and `TR` now end on:
  - `한일유통 경영기획팀장 + 그룹 구조조정 TF 실무총괄`

Question for OPUS:

- Is this worth patching now?
- Or is the current `phase0` wording acceptable as an abstraction layer?

### Finding C. Late seed copy still uses older phrasing

- some late seed wording still says:
  - `경영기획팀장 + TF 겸임`
- while the latest end-state is:
  - `경영기획팀장 + 그룹 구조조정 TF 실무총괄`

Question for OPUS:

- Is this normal shorthand, or does it create meaningful end-state blur?

## 7. Evaluation Standard

OPUS should evaluate primarily by:

1. whether the inconsistency can cause future harness drift
2. whether it can trigger avoidable audit noise later
3. whether the repair is small enough to be worth doing now
4. whether leaving it alone is cleaner than patching it

## 8. Required Output

Return exactly these sections:

### 8.1 Verdict

- one of:
  - `Patch all`
  - `Patch only A/B/C`
  - `Leave as-is`

### 8.2 Finding-by-Finding Ruling

For each of `A / B / C`:

- `patch` or `leave`
- one short reason

### 8.3 Minimal Patch Set

Only if any item should be patched.

For each patch:

- target file
- target field / area
- replacement direction

### 8.4 Over-Repair Risk

- what would become worse if these micro-patches are overdone

## 9. Stop Conditions

Stop and flag if:

- the answer drifts into concept redesign
- the answer tries to reopen `Option A/B/C`
- the answer proposes broad TR surgery

## 10. Minimal Paste Prompt

```text
너는 이번 런의 review-OPUS다. `docs/2026-04-02/opus-office_checkup_next_day-tr-sync-order.md`, `docs/2026-04-02/office_checkup_next_day-tr-sync-opus-context-memo.md`, `docs/2026-04-02/office_checkup_next_day-tr-sync-order-opus-brief.md`를 UTF-8로 읽고, `office_checkup_next_day` pair의 TR sync 이후 남은 미세 정합성 이슈만 spot audit하라. 전면 재기획 금지, review only. A/B/C 각 finding에 대해 patch or leave를 판정하고, 필요하면 minimal patch set만 제시하라.
```
