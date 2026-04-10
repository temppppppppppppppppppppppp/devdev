# chaebol_allowance_zero Deep Repair Masterplan

Date: 2026-04-10
Status: active
Scope: full material-side repair for `chaebol_allowance_zero`

## 0. One-line recommendation

Do **not** patch the current 70 blocks in place first.

Start with:

1. pacing contract lock
2. `Phase 0` redesign
3. harness surface patch
4. wave rewrite with short audit checkpoints

This pair is a **macro pacing failure first** and a **density failure second**.

## 1. Why direct line-editing is the wrong first move

Current root problems:

1. `Phase 0` already locks `ARC-01` as `Block 1-10 = 장례식장 뒤문`.
2. live TR keeps the funeral macro-battlefield alive through `B09`, with the first clear signboard shift only at `B10`.
3. executable TR harness enforces continuity/cider/format well, but does **not** executable-enforce:
   - `1 block = 2~6 downstream episodes`
   - opening macro-battlefield residence cap
   - market-speed opening signboard timing
4. preprocess `seed_baseline_sync` is not real sequential production truth.

Implication:

- if we patch sentences only, we preserve the wrong macro map
- if we densify only, we create a prettier failure
- if we rewrite without harness patch, the same failure shape can recur

## 2. Repair doctrine

### 2.1 Order

1. **design first**
2. **opening first**
3. **short audited waves**
4. **BI sync only after TR repair stabilizes**

### 2.2 Practical reading

- yes, we should go from design first
- yes, we should move sequentially
- but not as `70 blocks of blind one-by-one patching`
- the right speed is:
  - strategic redesign once
  - production rewrite in small audited waves

## 3. Recommended execution path

### Phase A. Contract lock

Goal:

- make the repair standard explicit before touching content

Work:

1. reconcile `work_guard`, benchmark spec, and production harness
2. promote these rules to active repair gates:
   - `TR block` is a plan-level bundle, not a 1:1 published episode
   - one `TR block` should feel expandable into roughly `2~6` episodes
   - opening macro-battlefield cannot dominate too long
   - first strong reader payback must land in the opening benchmark window
   - signboard explosion / reevaluation / next-gate ticket must not drift late
3. define explicit fail conditions for:
   - micro-location churn without macro progression
   - same-battlefield overstay
   - late opening signboard event

Output:

- one repair gate doc
- one implementation checklist for runtime harness patch

### Phase B. `Phase 0` redesign

Goal:

- fix the upstream shape that currently forces `B1~B10` funeral overstay

Work:

1. rebuild arc skeleton, not just block prose
2. redesign `ARC-01` and likely `ARC-02` together
3. preserve the work's true engine:
   - support-system cashflow warfare
   - moneyline > inheritance
   - no family bailout
   - operational detail over abstract power talk

Opening target:

- funeral macro-battlefield should be compressed sharply
- first public reevaluation and signboard shift should land much earlier
- hotel ticket should be earned early and cashed soon after
- hotel field entry should not wait until the current `B11`

Recommended opening target band:

- `B1`: pain + first foothold
- `B2~B3`: proof + reevaluation + repeatability seed
- `B4~B5`: first next-battlefield ticket
- `B5~B6`: actual next-battlefield cash-in

Output:

- repaired `Phase 0`
- new opening pacing map
- revised arc entry/exit ladder

### Phase C. Harness surface patch

Goal:

- prevent the old failure from regenerating during rewrite

Patch targets:

1. live TR prompt surface
2. candidate validation
3. batch audit metrics

Must-add gates:

1. opening macro-battlefield residence check
2. signboard timing check
3. next-battlefield ticket timing check
4. block-as-bundle reminder in active prompt
5. phase0/material-side inputs consumption beyond just title/summary

Important rule:

- density remains mandatory
- but density cannot substitute for pacing progression

### Phase D. TR rewrite

Goal:

- rewrite the pair with the new structure, not cosmetically patch the old one

Recommended wave plan:

1. Wave 1: `B1~B15`
2. Wave 2: `B16~B35`
3. Wave 3: `B36~B70`

Internal operating rule:

- rewrite in `5-block` audited checkpoints
- no unaudited long run
- no densification-only rescue

Why this split:

- `B1~B15` determines whether the pair is alive or dead
- `B16~B35` absorbs the consequences of the opening redesign
- `B36~B70` is downstream scale-up and should inherit the corrected engine

### Phase E. BI and benchmark refresh

Goal:

- only after TR stabilizes, rebuild downstream truth

Work:

1. regenerate BI from repaired `Phase 0 + TR`
2. rerun BI 5-pass
3. rerun pair benchmark
4. verify opening pacing with absolute block anchors

## 4. What we should not do

Do not:

1. keep the current `ARC-01 block_range = 1-10` funeral map and only improve wording
2. treat preprocess `seed_baseline_sync` as proof that the harness is healthy
3. use densification as the primary fix
4. preserve current `B09/B10/B11` timing for repeat revenue, signboard shift, and hotel entry
5. let a block pass because it has same-block cider while the macro battlefield still does not move

## 5. Acceptance criteria

The repair is not complete unless all of the following are true:

1. opening no longer reads as one funeral battlefield stretched across `B1~B9`
2. signboard explosion lands inside the intended opening window
3. next battlefield ticket is earned early and cashed soon after
4. live harness can actively fail future drafts for macro pacing overstay
5. density, continuity, and cider rules still pass after the pacing fix
6. BI and benchmark agree with the repaired timing in absolute block numbers

## 6. Immediate next move

Start from **Phase B + Phase C in parallel**:

1. redesign `Phase 0` opening/early arc map
2. patch the harness so that the old opening-overstay pattern becomes a hard failure

Then:

3. rewrite `B1~B15`
4. audit
5. continue wave by wave

## 7. Recommendation summary

Recommended path:

- **설계부터 간다**
- **천천히 순차로 간다**
- but the unit is **wave + 5-block checkpoint**, not blind sentence patching

Shortest correct answer:

- `설계 먼저 -> 하네스 패치 -> opening rewrite -> 나머지 wave 순차 처리`
