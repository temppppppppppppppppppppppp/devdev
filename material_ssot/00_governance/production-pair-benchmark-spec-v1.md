# Production Pair Benchmark Spec v1

Date: 2026-04-07
Status: active
Scope: canonical grading benchmark for existing live `TR + BI` pairs
Update Note:
- 2026-04-09 opening pacing reconciliation patch added
- 2026-04-09 TR block episode-bundle clarification added

## 1. Role

- define one shared benchmark before auditing, repairing, re-grading, or promoting existing `BI/TR` pairs
- replace taste-only pair judgment with explicit gates, caps, and score axes
- let `production_pair_grade_aliases/` and later pair audits use the same ruler
- keep the benchmark pair-level: `TR` and `BI` are judged as one unit
- external-model execution discipline is governed by `external-model-benchmark-operation-harness-v1.md`

Schema precondition:

- use `production-pair-schema-standard-v1.md` first when the pair still has contract-shape drift
- benchmark judgment starts after the pair is normalized enough to count as one canonical `TR + BI` unit
- this benchmark must not invent new pair-core requiredness outside that schema standard

## 2. Core Thesis

The first question is not `is this pair interesting?`

The first question is:

`Does block 1 pay the reader back clearly enough to earn block 2?`

Terminology note:

- benchmark shorthand `block 1`, `block 2` is not a literal published episode counter
- on this material side, `TR block` is a plan-level episode bundle, not `episode 1 = TR block 1`
- default operator reading: one meaningful `TR block` should be dense enough to unfold into roughly `2~6` downstream serialized episodes
- for opening benchmark work, the first reader-earning bundle is operationalized through `TR blocks 2~6`

Working rule:

- `block 1` means roughly episodes `2~6`
- do not read that line as `TR block 1 = episodes 2~6`; it means the first benchmarked reader-earning bundle is evidenced through `TR 2~6`
- if a pair has no visible `cider` inside block 1, it cannot grade above `YELLOW`
- proof alone is not enough
- block 1 must end with:
  - protagonist-only proof
  - reevaluation
  - visible reward token
  - next gate opening

### 2.1 Strict Window Contract

- for benchmark audits, `block 1` is a strict evidence window: `TR` blocks `2, 3, 4, 5, 6` only
- `TR block 1` may be used for opening pain, innocence, or setup context, but it cannot satisfy `P0` gates `1~5`
- `TR block 7+` may be used for later cadence or loop analysis, but it cannot rescue a missing `P0` gate `1~4`
- if the first visible `cider` or first concrete reward token lands at `TR block 7` or later, gate `1` fails and the pair has a `YELLOW ceiling`
- if proof exists in `TR blocks 2~6` but reevaluation or token first lands at `TR block 7+`, gates `3` and `4` fail
- gate `5` may cite `TR block 7+` only as downstream confirmation that a token already earned by `TR block 6` opened the next gate; `TR block 7+` cannot backfill a missing reward
- use absolute block numbers in every benchmark report; do not write vague phrases like `early blocks`, `opening arc`, or `초반부` without numbered anchors

### 2.1A WG Or Canon Timing Reconciliation

- `work_guard` or canon timing language may be cited as supporting authority, but never as free-floating rhetoric
- if a report cites timing phrases such as:
  - `1화 내`
  - `3화 내`
  - `opening arc`
  - `ARC 종료 시`
- the report must translate them into absolute `TR` block numbers for that pair
- if the translation is ambiguous, the report must say so explicitly and may not use that phrase as positive proof
- if the live `TR` misses the cited timing threshold, the report may not score as though the threshold passed
- gate `6` still belongs to `BI + TR 1~3`; `work_guard` timing language may sharpen the reading, but may not replace the anchor

### 2.1B Opening Macro-Battlefield Residence Check

- benchmark audits must distinguish `micro-location` from `macro-battlefield`
- different rooms, desks, lines, bays, or support spaces inside the same operating arena may still count as one opening macro-battlefield
- example:
  - `장례식장 배식 라인`
  - `장례식장 주차관제실`
  - `장례식장 지하 세탁실`
  - `장례식장 청소팀 대기실`
  - may all belong to one macro-battlefield: `장례식장 운영축`
- for any pair under benchmark review, map `TR blocks 1~12` to macro-battlefields before final grade closure
- micro-location churn alone does not prove pacing progression
- if the opening main battlefield still dominates through `TR block 8`, the report must explicitly check:
  - first public signboard event
  - first representative reevaluation with real shelf movement
  - first next-battlefield ticket that is actually cashed soon after
- if those beats arrive late, the pair may still retain same-block cider quality while failing opening pacing cleanliness

### 2.2 Fast Invalidity Checks

The following readings are invalid and should be rejected during audit:

- `Block 1 had a strong opener, so first-block cider passes`
- `Block 7 reward rescues a weak 2~6 opening`
- `Block 10 authority grant proves first-block visible reward`
- `later payoff` or `next arc reward` counts as first-block conversion
- `TR block = published episode`, so thin one-episode beats are an acceptable default planning unit
- `work_guard says 3화 내 간판 폭발`, but the live `TR` lands it at `B9/B10` and the report still treats the threshold as passed
- `micro-location changed, so the opening battlefield changed`

Valid shape:

- `TR blocks 2~6 already contain proof + reevaluation + token`
- `TR block 7` is cited only to confirm that the token earned by `TR block 6` opened the next battlefield

### 2.3 Full-Block Cider Scan Contract

After the opening gates, run one more benchmark pass across the full `TR`.

- scan every `TR` block individually
- mark each block as `has_cider: true/false`
- `has_cider: true` requires at least one reader-countable payback inside that same block:
  - visible reward token
  - weighted reevaluation receipt
  - protection receipt
  - authority or access shift
  - recovery asset that materially offsets same-block pain
  - explicit next-card or next-gate receipt the reader can feel now
- `has_cider: false` includes:
  - setup-only block
  - explanation-only block
  - wait-only block
  - pain-only block
  - humiliation-only block
  - failure-only block
  - `later payoff` promise with no same-block receipt
- if any block is `has_cider: false`, the pair has a `YELLOW ceiling`
- reports must name the exact no-cider block numbers; vague phrases like `middle feels slow` are not enough
- this is a strong house rule by design: a production pair does not earn `GREEN` or `GREENPLUS` by asking the reader to coast through rewardless blocks

### 2.4 Schema Interlock And Evidence Mode

Benchmark judgment does not erase schema status.

- every benchmark report must also name:
  - `schema status`
  - `benchmark freshness`
  - `evidence mode`
  - `open migration debt: yes/no`
- use `legacy_read` only under the conditions defined in `production-pair-operating-policy-addendum-v1.md`
- use `serialized_canonical` for new, newly touched, regenerated, or promotion-target pairs
- an untouched historical live pair may keep a historical alias snapshot while carrying open migration debt
- no pair may newly earn or refresh `GREEN` or `GREENPLUS` operationally while open migration debt remains

### 2.5 Benchmark Freshness Rule

Use the operating addendum to classify benchmark freshness.

Working rule:

- if a pair was materially touched or regenerated after the last benchmark artifact, benchmark freshness becomes `pending_refresh`
- `pending_refresh` does not delete the historical benchmark reading, but it does block active baseline claims and fresh alias refresh
- freshness becomes `current` only after:
  - a new benchmark run, or
  - a bounded benchmark-preservation audit that explicitly confirms the relevant benchmark anchors and cap rules remained intact after the latest rewrite

## 3. Grade Bands

- `GREENPLUS`
  - top-tier benchmark preservation
  - first-block conversion is exemplary
  - full-block cider scan finds zero no-cider blocks
  - no major cap rule is triggered
  - late blocks keep reward cadence
  - operator intent: this shelf should be strict enough to stand in for real webnovel sell-in quality, not just internal benchmark prestige
- `GREEN`
  - production-ready pair
  - core promise survives
  - full-block cider scan finds zero no-cider blocks
  - some residual weakness exists, but not enough to break the engine
- `YELLOW`
  - strong premise or some strong arcs exist
  - current pair breaks one or more benchmark ceilings
  - one no-cider block is enough to place the pair here
  - repair should focus on bounded top `3` units, not full-wave surgery by default
- `RED`
  - pair-level benchmark failure
  - current pair should not be promoted or grade-aliased upward before major repair

## 4. P0 Hard Gates

Run these first.

### 4.1 Gate Set

1. `first-block visible cider`
   - `TR blocks 2~6` contain at least one visible reward readers can count or feel
2. `protagonist-only proof`
   - `TR blocks 2~6` make `저건 쟤라서 가능했다` undeniable
3. `evaluation revision`
   - someone with weight reevaluates the protagonist inside `TR blocks 2~6`
4. `visible reward token`
   - `TR blocks 2~6` land at least one concrete token:
     - `blockguide`: name call, seat, `CC`, report line, `TF`, approval, ownership, entry ticket
     - `wuxguide`: rank, elder protection, manual access, treasure, realm step, reputation, inheritance clue
     - `medical` and adjacent lanes: case access, authority, conference slot, direct line, protocol ownership, public reevaluation
5. `block 1 -> block 2 gate linkage`
   - the reward earned by `TR block 6` or earlier opens the next gate
   - `TR block 7+` may confirm this linkage, but cannot supply the first reward token retroactively
6. `BI/TR early conversion alignment`
   - `BI` early promise, `cider_point`, and `success_device` are visibly alive in `TR` block `1~3`

### 4.2 Ceiling Rules

- if gate `1` fails: `YELLOW ceiling`
- if gate `2` fails: `YELLOW ceiling`
- if gate `3` or `4` fails: `YELLOW ceiling`
- if gate `5` fails: `YELLOW ceiling`
- if gate `6` fails: `YELLOW ceiling`
- if two or more gates fail: default `RED review lane`
- if a report cites `TR block 1` or `TR block 7+` as the primary proof for gates `1~4`, that gate reading is invalid and must be re-judged
- if a report cites `work_guard` or canon timing language without absolute block reconciliation, that gate reading is invalid and must be re-judged
- if a report mistakes micro-location churn for macro-battlefield progression, that opening reading is invalid and must be re-judged

### 4.3 Opening Innocence Rule

- if current-protagonist fault is the main cause of the opening fall, the pair cannot grade above `YELLOW`
- acceptable opening disadvantage:
  - wrong seat
  - wrong structure
  - political sacrifice
  - inherited bad frame
  - previous-era criteria
- unacceptable opening disadvantage:
  - laziness
  - irresponsibility
  - self-inflicted collapse by the current protagonist

## 5. P1 Score Axes

Score each axis `0 / 1 / 2`.

| Axis | `0` | `1` | `2` |
| --- | --- | --- | --- |
| protagonist innocence | opening fault mostly belongs to protagonist | mixed | protagonist is clearly defendable |
| protagonist-only proof clarity | generic success | partly specific | unmistakably protagonist-only |
| evaluation revision visibility | barely visible | partial | explicit and weighted |
| visible reward token strength | emotional only | weak token | concrete token with force |
| block1 -> block2 linkage | unclear | partial | clean next-gate opening |
| rational opposition | cartoon resistance | mixed | incentive-driven, era-valid opposition |
| domain truth density | generic lane | partly textured | concrete domain truth carries the engine |
| repeatable loop clarity | one-off win | partial loop | loop is visible and reusable |
| BI amplification power | BI echoes TR only | some amplification | BI materially sharpens TR promise |
| blockwise cider continuity | one or more no-cider blocks | all blocks pay but several are weak bridge-only beats | every block lands a felt receipt |

Total: `20`

## 6. Cap Rules Beyond P0

Even with a strong score, the pair cannot exceed the cap below if the pattern appears.

- no visible cider inside block 1: `YELLOW ceiling`
- first concrete token lands at `TR block 7+`: `YELLOW ceiling`
- any no-cider block in the full-block cider scan: `YELLOW ceiling`
- `work_guard` or canon declares an earlier opening timing threshold and the live `TR` misses it: `YELLOW ceiling`
- rewardless pain blocks `2` in a row: `GREEN ceiling`
- no-cider drought `6+` blocks: `YELLOW ceiling`
- major defeat without next card in the same or next block: `YELLOW ceiling`
- `BI` acts as summary echo only and does not amplify the pair: `GREEN ceiling`
- early reward is asset-only and lacks status or authority shift: `GREEN ceiling`
- opening main battlefield still dominates through `TR block 8` and the first public signboard event or representative-scale reevaluation lands at `TR block 9+`: `GREEN ceiling`
- micro-location churn exists, but real macro-battlefield progression is absent: `GREEN ceiling`
- wins rely on stupid opposition: `GREEN ceiling`
- domain texture is generic enough to swap with another lane: `GREEN ceiling`
- protagonist stays mostly passive across a key arc while reward remains weak: `YELLOW ceiling`

## 7. RED Triggers

Any of the following should start from `RED` unless later evidence clearly rescues the pair:

- two or more `P0` hard gates fail
- block 1 closes on pain-only exit and `BI/TR` early conversion mismatch is also present
- the repeatable loop is still unclear by block `10`
- protagonist passivity, weak reward, and low reevaluation stack together across early arc

## 8. Grade Decision Table

### 8.1 `GREENPLUS`

Requirements:

- all `P0` hard gates pass
- no `YELLOW` ceiling rule triggered
- total score `17~20`
- block 1 is an exemplar of `proof -> reevaluation -> reward -> next gate`
- full-block cider scan shows zero no-cider blocks
- later reward cadence still feels intentional

### 8.1A Operational Deployable `GREENPLUS`

`GREENPLUS` is not just a historical compliment band.

For current operator use, a pair should be treated as deployable `GREENPLUS` only when all of the following are true:

- benchmark grade is `GREENPLUS`
- benchmark freshness is `current`
- no open migration debt remains
- opening pacing triage is currently `GREEN`
- no whole-run pacing re-audit currently places the pair in `YELLOW` or `UNTRIAGED`
- no active operator note places the pair in:
  - `repair-first`
  - `manual re-audit pending`
  - `forensic re-audit`
  - `hold`
- opening cleanliness is supported by one of:
  - declared-contract evidence, or
  - bounded same-day manual closeout that explicitly confirms the opening timing gates with absolute block numbers
- the pair may be cited without qualifier as:
  - current family exemplar
  - market-facing quality reference
  - live sell-in baseline candidate

If any item above is missing, the pair may still keep a historical `GREENPLUS` benchmark alias snapshot, but it is not an operator-deployable `GREENPLUS` shelf item.

Quality-first reading:

- do not award operational `GREENPLUS` out of thrift, nostalgia, or repair sunk-cost protection
- if there is any serious doubt about live market deployability, keep the pair below deployable `GREENPLUS`
- the burden of proof is positive closure, not absence of obvious disaster

### 8.1B Immediate Material Deployment Overlay

Immediate material deployment is stricter than operational `GREENPLUS`.

For the current material-side order, a pair may be treated as immediately deployable material only when:

- it already clears the relevant benchmark/reference quality law
- donor structure is applied or adopted in visible material-side authority
- contamination guardrails are visible
- pair-level closeout ties the current usability claim to the donorized structure

Current overlay ruling as of 2026-04-29:

- `golden_canary_deepclone_probe_a_fullblock_v1` is the only immediately deployable material
- other `GREENPLUS` / `GREEN` rows stay benchmark/reference inventory until donor structure is applied and recorded
- see `docs/2026-04-29/material-side-immediate-deployment-overlay.md`

### 8.2 `GREEN`

Requirements:

- all `P0` hard gates pass
- no `YELLOW` ceiling rule triggered
- total score `13~16`
- full-block cider scan shows zero no-cider blocks
- one or more `GREEN` cap rules may exist, but the pair remains clearly production-ready

### 8.3 `YELLOW`

Requirements:

- any `YELLOW` ceiling rule triggered, or
- any no-cider block exists, or
- total score `9~12`

Interpretation:

- engine survives
- bounded repair is justified
- default repair scope is `top 3` weak units

### 8.4 `RED`

Requirements:

- any `RED` trigger, or
- total score `0~8`

Interpretation:

- do not promote or snapshot-grade upward
- repair should start from contract truth, early conversion, or regenerate-first judgment

## 9. Current Benchmark Exemplars

These are historical benchmark exemplars for reading the ruler, not automatic proof of current active-baseline freshness.

For operator use:

- read benchmark freshness from `production-pair-operational-registry-v1.md`
- do not treat this section alone as proof that a pair is a current active baseline candidate

- `office_checkup_next_day`
  - first-block conversion benchmark
  - cleanest `proof -> reevaluation -> token` chain
- `pantech_cyworld_reborn`
  - authority-ticket benchmark
  - block `1~3` converts proof into access rights and power gates
- `defense_defect_engineer`
  - proof-scene precision benchmark
  - hidden defect + hidden cost -> reevaluation and entry-ticket payoff
- `wuxia_heavenly_physician`
  - high-pain recovery-control benchmark
  - useful for testing whether a painful lane still keeps reward cadence
- `투자물_골든_카나리아 테스트_canonical_v1`
  - `GREENPLUS` live pair
  - market-power proof that now converts early into authority/status token as well as capital gain

## 10. Standard Audit Output Shape

Every pair benchmark audit should produce:

1. pair identity
2. operational state
3. schema status
4. benchmark freshness
5. evidence mode
6. compliance self-check
7. `P0` gate pass/fail table
8. full-block cider scan summary
9. active cap rules
10. `P1` score table and total
11. provisional grade
12. open migration debt: `yes/no`
13. alias update note if grade is `GREENPLUS` or `GREEN`
14. top `3` repair units if grade is `YELLOW` or `RED`

Audit discipline:

- the `P0` section must name at least one concrete `TR block` anchor for each gate
- if the anchor for gates `1~4` sits outside `TR blocks 2~6`, the report is non-compliant
- if a pair passes on the strength of `TR block 7+`, re-run the benchmark before using the grade operationally
- every report must include an `opening macro-battlefield map` for `TR blocks 1~12`
- if `work_guard` or canon timing language is cited, include a reconciliation note that maps each cited phrase to absolute live `TR` blocks
- the report must name the absolute block number for:
  - first public signboard event
  - first representative reevaluation with shelf movement
  - first next-battlefield ticket
- the compliance self-check must confirm:
  - `P0 = 6 gates`
  - `P1 = 10 axes x 0/1/2 = 20`
  - `gate 6 = BI + TR 1~3`
  - `full-block cider scan covered every TR block`
- the full-block cider scan must name:
  - total `TR` block count
  - no-cider block count
  - exact no-cider block numbers, or `none`

## 11. Operating Rule

- do not start from full-wave surgery
- after schema normalization, benchmark first
- classify second
- repair the smallest profitable scope third
- re-grade after repair

Shorthand:

- `block 1 must pay`
- `proof alone is not cider`
- `no first-block cider, no grade above YELLOW`
- `one no-cider block, no grade above YELLOW`
