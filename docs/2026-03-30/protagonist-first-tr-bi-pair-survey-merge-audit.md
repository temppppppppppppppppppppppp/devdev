# Protagonist-First TR-BI Pair Survey Merge Audit

Date: 2026-03-30
Status: final (merge-audited)
Document Type: merge audit
Canonical Path: `docs/2026-03-30/protagonist-first-tr-bi-pair-survey-merge-audit.md`
Scope: merge + audit of the 4-terminal live pair survey only
Mode: documentation-only

## 0. Executive Verdict

Final merge verdict: **GREEN**

One-line conclusion:

- the current live `TR + BI` pairs overwhelmingly preserve `주인공 둥기둥기 first`; no surveyed pair showed a proven `success -> pure punishment spiral` or a `protagonist engine collapse`

Important audit note:

- `GREEN` does **not** mean all five pairs are equally strong or equally clean
- the merge result is:
  - `3 active green reference candidates`
  - `1 quarantine green reference candidate` (`wuxia_third_rate_sect_master`, because the pair now lives fully under `_quarantine/`)
  - `1 yellow repair candidate` (`wuxia_heavenly_physician`, because the opening reward vector is too punitive under the current philosophy)

## 1. Inputs

Merged lane reports:

- `docs/2026-03-30/opus-protagonist-first-pair-survey/t1-blockguide-calibration-lane.md`
- `docs/2026-03-30/opus-protagonist-first-pair-survey/t2-pantech-cyworld-heavy-lane.md`
- `docs/2026-03-30/opus-protagonist-first-pair-survey/t3-wuxia-heavenly-physician-live-lane.md`
- `docs/2026-03-30/opus-protagonist-first-pair-survey/t4-wuxia-third-rate-quarantine-lane.md`

Merge-audit spot checks performed before closure:

- `treatments/pantech_cyworld_reborn_tr_block_070_draft.json` blocks `1, 5, 30, 65, 70`
- `treatments/wuxia_heavenly_physician_tr_block_070_draft.json` blocks `1, 38, 39, 50, 69, 70`
- `treatments/_quarantine/wuxia_third_rate_sect_master_tr_block_070_draft.json` blocks `1, 34, 38, 66, 69, 70`
- `bible/0_bi_pantech_cyworld_reborn.json`
- `bible/0_bi_wuxia_heavenly_physician.json`
- `bible/_quarantine/0_bi_wuxia_third_rate_sect_master.json`

## 2. Pair Ledger

| work_id | family | TR | BI | pair | reference status | merge note |
| --- | --- | --- | --- | --- | --- | --- |
| `chaebol_ent_empire` | `blockguide` | green | green | green | active reference | hardship-containing protagonist-first reference |
| `투자물_골든_카나리아 테스트` | `blockguide` | green | green | green | active reference | low-drift / high-reward protagonist-first reference |
| `pantech_cyworld_reborn` | `blockguide` | green | green | green | active reference | setback-heavy but still reward-first reference |
| `wuxia_heavenly_physician` | `wuxguide` | yellow | yellow | yellow | repair candidate | mid/late arc is strong, but opening onboarding drifts against reward-first philosophy |
| `wuxia_third_rate_sect_master` | `wuxguide` | green | green | green | quarantine reference | TR + BI both parked in `_quarantine/`; philosophically green, but not an active baseline |

## 3. Findings

### F1. No pair showed proven protagonist-first collapse

This is the main merge conclusion.

Across all four lanes, the reports consistently found:

- visible reward after meaningful protagonist success
- almost no proven `win -> immediate pure punishment` collapse
- pain that remains growth-bearing or aspirational
- deeper vector reversal after stress windows
- a persistent protagonist-only engine

Spot-audit confirmation:

- `pantech_cyworld_reborn` Block 5 is humiliation on the surface, but the reward field immediately turns the failure into `312종 충돌 로그 + 인증 병목 데이터` acquisition
- `wuxia_heavenly_physician` Blocks 38-39 are not the real problem; the stricter problem is the opening reward vector in Blocks 1-2, where life-saving success is followed by `조사 대상 / 감시 / 축출 위기` framing before sufficient visible reward lands
- `wuxia_third_rate_sect_master` Blocks 34-38 form a real drop, but Block 38 rebounds through 심안결 각성 and confirms the valley is a designed growth hinge, not a drift into helplessness

### F2. Blockguide pairs are the cleanest BI-level philosophy carriers

The three active `blockguide` pairs are not just green in TR.
They also encode protagonist-first logic more explicitly in BI.

Consistent strengths:

- `ProjectData.CoreIdentity.edge/desire/crisis` are populated and legible
- `FinanceHUD` makes protagonist leverage readable
- `GenreRules` often encode reward logic directly
- protagonist-first value is easy to locate without cross-reading many sections

Practical merge judgment:

- if one needs a **cross-family-readable** protagonist-first reference set right now, the strongest immediate anchors are in `blockguide`

### F3. `wuxia_heavenly_physician` is not a clean reference pair under the current philosophy

This is the largest merge correction.

The lane report treated the pair as fully green, but a stricter reread against the current `what-how` rules changes that result.

Why the verdict changes:

- in `treatments/wuxia_heavenly_physician_tr_block_070_draft.json` Block 1, the protagonist saves his brother and awakens the core engine, yet the immediate aftermath is dominated by suspicion and `사술` framing rather than visible protagonist-centered reward
- in `treatments/wuxia_heavenly_physician_tr_block_070_draft.json` Block 2, the text explicitly says he merely avoids expulsion but gets tagged as `조사 대상`, watched by the elders, and held under suspicion
- under the current philosophy, this is too close to `사람을 살렸는데 감옥/축출/감시로 받는 보상` logic

Why this is a philosophy mismatch:

- `둥기둥기 first` expects success to produce visible recognition, reward, or a clearly protective vector
- hidden concern, delayed recognition, and "at least you were not expelled" is too weak as the first reward after a life-saving act
- this is especially damaging in the opening arc, where the reader is learning how the story rewards the protagonist

Why this does not make the pair red:

- the middle and late arcs recover strongly
- the protagonist engine remains unique and powerful
- later arcs do satisfy reward, vector, and pain-aesthetic conditions well

Revised merge judgment:

- `wuxia_heavenly_physician` = `yellow repair candidate`
- not an active reference pair until the opening reward vector is repaired

### F4. Wuxguide preserves the philosophy strongly overall, but BI field placement is less normalized

This is the most important audit correction added during merge.

`wuxguide` pairs still land **GREEN** at pair level.
However, their protagonist-first BI encoding is distributed differently:

- key protagonist engine details are often strongest in `protagonist_config`
- `MartialHUD.actual_truth`, `faction_status`, and `jianghu_reputation` carry much of the protagonist-first payload
- `ProjectData.CoreIdentity.edge/desire` is not normalized the same way as blockguide and may be null or thinner

This is **not** a philosophy failure.
It is a **normalization gap**.

Why this does not flip the verdict:

- `wuxia_heavenly_physician` still encodes protagonist-first clearly through `protagonist_config.true_strength`, `final_goal`, `MartialHUD`, and reputation/faction history
- `wuxia_third_rate_sect_master` still encodes the protagonist engine through `protagonist_config.goals`, `true_strength`, `true_weakness`, and the education-centered MartialHUD history

Why it still matters:

- future cross-family surveys become easier to overrate or underrate if `CoreIdentity` normalization is inconsistent
- this is an audit note, not a reopen-worthy drift claim

### F5. `wuxia_third_rate_sect_master` is green, but only as a quarantine reference

The lane report is convincing that the pair itself is aligned:

- reward visibility remains high
- long stress windows still resolve upward
- BI provenance appears low-risk

But the merge audit keeps one reserve:

- TR is still under `_quarantine/`
- BI is also under `_quarantine/`

The pair can be treated as:

- `quarantine green reference`

Its internal provenance is now aligned, but it should **not** be treated as the cleanest family baseline until it is promoted out of quarantine.

## 4. False Alarms

These looked like possible protagonist-first drift points, but the merged evidence says they are not.

### A. `chaebol_ent_empire` Block 4 first failure

Not drift.
The loss is paired with immediate structural insight and near-term rebound.
This is a hardship-to-upgrade pattern, not a reward-collapse pattern.

### B. `pantech_cyworld_reborn` repeated capital drawdowns

Not drift.
The capital decreases are usually strategic spend / defense cost / positioning cost, not humiliating confiscation or helpless erosion.

### C. `wuxia_third_rate_sect_master` Blocks 34-37 prolonged decline

Not drift.
The decline is long enough to require caution, but Block 38 confirms it is a designed awakening hinge, not a protagonist humiliation spiral.

## 5. Reference Tiering

### Tier A. Active Reference Pairs

- `투자물_골든_카나리아 테스트`
  - best when the question is: `how do we make protagonist-first drift almost impossible by structure?`
- `chaebol_ent_empire`
  - best when the question is: `how do we keep protagonist-first even with meaningful setbacks?`
- `pantech_cyworld_reborn`
  - best when the question is: `how do we preserve reward-first logic under repeated public/business stress?`

### Tier B. Quarantine Reference Pair

- `wuxia_third_rate_sect_master`
  - best when the question is: `how do we keep protagonist-first with a weak-combat / strong-education protagonist?`
  - quarantine-only because the pair is now parked fully under `_quarantine/`

### Tier C. Repair Candidate

- `wuxia_heavenly_physician`
  - strong mid/late arc protagonist-first pair
  - not a clean reference pair because Blocks 1-2 reward a life-saving act with too much suspicion / surveillance / expulsion-pressure framing

## 6. Merge Audit Corrections To Lane Conclusions

No lane needs a verdict reversal.

Two corrections are added at merge level:

- `wuxia_heavenly_physician = YELLOW`
  - the opening reward vector is misaligned with the current philosophy
  - early onboarding repair is justified
- `wuxguide BI amplification = GREEN, but with a normalization note`
  - the protagonist-first engine is present
  - it is just less uniformly surfaced in `ProjectData.CoreIdentity` than in blockguide

This means:

- one lane verdict is partially overridden at merge level
- merge wording must not overclaim that all families encode the philosophy in the same BI schema shape

## 7. Action Queue

This remains a survey merge, so the queue is bounded and non-execution by default.

### P1

- if you want one canonical family reference per family right now, use `골든 카나리아` for blockguide and treat `wuxia_third_rate_sect_master` as quarantine-only for wuxguide until `천의무쌍` opening arc is repaired or another clean active wuxguide pair exists

### P1

- reopen `wuxia_heavenly_physician` only for opening-arc repair: Blocks `1-3` and likely `10-12` should change from `사술 의심 / 조사 대상 / 축출 위기` framing to `비공개 보호 + 제한적 내부 인정 + 통제된 은닉` framing

### P1

- if future surveys must compare families mechanically, add a small normalization pass for `wuxguide BI` so protagonist engine fields are easier to read at `CoreIdentity` level without hunting through `protagonist_config`

### P2

- if `wuxia_third_rate_sect_master` is promoted out of quarantine later, re-run only a provenance micro-audit; no need for a full protagonist-first resurvey unless the contents change

## 8. Final Judgment

The merged answer to the user's question is:

- yes, the current live `TR + BI` set is philosophically much healthier than expected under the `주인공 둥기둥기 first` lens
- the more meaningful distinction is no longer `green vs red`
- it is now:
  - `which pairs are active references, which are provisional, and which need targeted repair before they can be used as references?`

## 9. 3-Pass Self Audit

### Pass 1. Merge Scope

- merged only the 4 lane reports requested
- did not drift into code/runtime/member audit
- kept the focus on live pair philosophy alignment

### Pass 2. Contradiction Audit

- all four lanes initially converged on `green`
- merge audit spot-checks tested the highest-risk stress windows before closure
- one lane conclusion (`wuxia_heavenly_physician`) was downgraded after a stricter opening-arc reread
- one family-level normalization note was added for `wuxguide BI`

### Pass 3. Integrity Audit

- saved under `docs/2026-03-30/`
- UTF-8 only
- no queue/temp mutation
- no execution SSOT or patch escalation
