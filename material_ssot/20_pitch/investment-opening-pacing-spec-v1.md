# Investment Opening Pacing Spec v1

Date: 2026-04-10
Status: active
Scope: upstream opening-pace law for investment-family / business-power candidates before `Phase0`, `work_guard`, and live `TR`

## 1. Role

This spec exists because the current pair-side benchmark and opening-pacing triage are necessary but late.

Those surfaces tell us whether a live `TR + BI` pair already opened too slowly.

This document moves the same question upstream:

`투자물 opening은 설계 단계에서 어느 정도 속도로 독자에게 첫 proof / reevaluation / ticket를 줘야 하는가?`

Use this spec when:

- shaping a fresh investment-family pitch
- auditing `selection-ready` or `Phase0-ready` claims
- translating pitch truth into `work_guard.yaml`
- freezing `opening_bundle_contract`
- rejecting an overlong `ARC-01` before it becomes downstream drag

This spec does not replace:

- `material-benchmark-readiness-harness-v1.md`
- `work-guard-translation-map.md`
- `production-pair-benchmark-spec-v1.md`

It is an upstream family-side pace ruler that should feed those surfaces.

## 2. Core Thesis

투자물 opening의 독자 보상은 단순 `회귀했다`가 아니다.

The opening must quickly prove:

1. the protagonist reads the market or structure earlier than others
2. that read becomes a countable receipt, not just inner conviction
3. outside observers begin to change tone
4. the first receipt opens the next battlefield

One-line law:

`투자물 opening은 초반 3화 안에 실행 감각이 보여야 하고, 늦어도 4화 안에는 첫 signboard 또는 next-ticket가 보여야 한다.`

## 3. Translation Rule

### 3.1 Bundle-Side vs Episode-Side

The generic material benchmark still uses:

- `TR blocks 2~6` as the first reader-earning bundle

But investment-family operators must add one more translation layer:

- the same opening bundle should usually serialize into roughly `episodes 1~3`
- `episode 4` is a soft cap, not the default
- `episode 5+` requires explicit operator justification

This means:

- do not read a slow six-episode opening as acceptable merely because the generic bundle benchmark still talks in `TR 2~6`
- the investment-family opener should compress the bundle into a faster episode-side sell-in rhythm

### 3.2 Default Episode Cadence

Default target:

- `Episode 1`
  - opening wound, regression, or disadvantage may appear
  - but the protagonist must also choose or prepare a concrete market move
  - `memory sorting only`, `독립 선언 only`, or `설명-only setup` is insufficient
- `Episode 2`
  - the first protagonist-only proof or executable pre-positioning must be visible
  - readers should feel `저건 쟤라서 가능한 판단` instead of mere promise
- `Episode 3`
  - weighted reevaluation, signboard, or visible reward token must begin to cash
  - at minimum, the next battlefield ticket should already be earned or opened
- `Episode 4`
  - allowed as confirmation, enlargement, or cash-out
  - not allowed as the first real rescue for a weak opening

Default operator read:

- `3 episodes` = healthy target
- `4 episodes` = soft ceiling
- `5+ episodes` = slow-by-design suspicion

## 4. Hard Family Contract

An investment-family opener is not selection-ready when any of the following holds:

- `Episode 1~3` contains no concrete execution move
- first proof lands only as explanation or internal conviction
- reevaluation appears without shelf movement, tone shift, or access change
- the opening spends three episodes on grief, memory ordering, family talk, or independence rhetoric without a market-facing action
- the authority ladder is dripped too slowly to feel like an opening conversion

Default timing contract:

- first proof: `episode 2` target, `episode 3` hard latest
- first public or weighted signboard: `episode 2~3` target, `episode 4` soft latest
- representative reevaluation: `episode 2~3` target, `episode 4` soft latest
- first next-battlefield ticket: `episode 3` target, `episode 4` soft latest

If a work wants a slower lane, the pitch must explicitly explain why the extra delay produces a stronger sell-in than the faster investment norm.

No such note means the delay is treated as debt, not style.

## 5. Failure Shapes

The following are upstream slow-design smells for investment-family openings:

### 5.1 Setup-Only Trilogy

- `episode 1`: 죽음/회귀
- `episode 2`: 기억 정리
- `episode 3`: 결심/독립 선언
- but no countable execution receipt yet

This shape may still look narratively coherent, but it is slow for the family.

### 5.2 Proof Without Conversion

- the protagonist predicts or prepares something correctly
- but no observer tone shift, access change, seat change, or authority receipt follows soon after

In investment-family work, proof must convert.

### 5.3 Late Authority Ladder Drip

Bad shape:

- `B04`: first reevaluation
- `B06`: direct-report line
- `B09`: public hit
- `B11+`: seat / read / sign authority

This is not a narrow `TR` wobble.
It usually means the opening was designed too wide upstream.

### 5.4 Macro-Battlefield Overstay

- same office/family/grief/staging arena dominates the opening too long
- micro-scene churn exists, but the reader still feels the same battlefield
- signboard and next-ticket land late because the opening never truly exits the first arena

## 6. Positive Shape

Healthy investment-family opening rhythm usually looks like:

1. opening pain or regression
2. immediate thesis or pre-positioning choice
3. first proof that only the protagonist could have made
4. observer tone shift or reevaluation
5. visible reward token, seat, access, or exception line
6. the next cycle or battlefield opens quickly

Example receipts that count:

- PB or risk team tone shift
- VIP line, exception account, special seat
- fast access to thesis, broker, room, or data
- authority to enter the next trade, deal, or governance table

## 7. Upstream Translation Targets

### 7.1 `first_block_cider_ledger`

For investment-family pitches, the ledger must not merely show `has_cider: true`.

It should also make the early conversion chain legible:

- which row carries the first proof
- which row carries reevaluation
- which row carries the first visible token
- which row opens the next gate

If those functions are vague, the pitch may still be draftable, but it is not `selection-ready`.

### 7.2 `work_guard.yaml`

When translating to `work_guard`, preserve:

- a mandatory scene engine for pre-price or pre-event positioning
- a mandatory scene engine for post-event proof collection and tone shift
- an evaluation threshold that requires early tone change or authority movement
- a custom rule that blocks slow `proof only -> late conversion` drift

For investment-family guards, `first proof exists somewhere` is too weak.
The guard should expect:

- early proof
- early reevaluation
- early ticket conversion

### 7.3 `opening_bundle_contract`

For investment-family opening bundles, the default declared target should be read aggressively:

- `first_signboard_block`: aim `3`, treat `4` as soft latest
- `representative_reevaluation_block`: aim `3`, treat `4` as soft latest
- `next_battlefield_ticket_block`: aim `3~4`, treat `5+` as suspect

The generic scaffold default is not enough by itself.
Investment-family operators should freeze a faster declared contract when the work promises market-speed catharsis.

### 7.4 `Phase0 / ARC-01`

Do not normalize a six-episode `ARC-01` for investment-family work unless:

- the opening still cashes proof and reevaluation early inside that span, or
- the operator writes an explicit exception note explaining why the slower runway is commercially stronger

Without that note, a long `ARC-01` is read as structural pacing debt.

## 8. Evidence Anchors

Current workspace evidence that supports this spec:

- pair-side generic benchmark:
  - `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
- current opening triage wave:
  - `docs/2026-04-10/production-pair-opening-pacing-triage-wave.md`
- healthy investment-family mechanical exemplar:
  - `docs/2026-04-10/terminal_01_golden_canary_deployable_greenplus_audit.md`
- slow-by-design negative shape:
  - `docs/2026-04-10/jaebeol3se_loss_line_forensic_spot_audit.md`
- repairable but still slow queue reading:
  - `docs/2026-04-10/current-yellow-salvageability-split.md`
- NAS-backed investment corpus builder:
  - `scripts/build_investment_epub_corpus.py`

## 9. Operator Rule

Use this spec in the following order:

1. pitch or synthesis draft
2. `first_block_cider_ledger`
3. this investment-family opening pacing spec
4. `work-guard-translation-map.md`
5. `opening_bundle_contract` freeze
6. `Phase0-ready` call

If a work fails here, repair it upstream.
Do not push the debt into Stage2 and ask `TR` or `S3` to rescue a slow opening spine.

## 10. One-Line Rule

`투자물 opening은 실행 전 독백으로 버티지 말고, 빠른 proof -> reevaluation -> ticket chain으로 독자를 잡아야 한다.`
