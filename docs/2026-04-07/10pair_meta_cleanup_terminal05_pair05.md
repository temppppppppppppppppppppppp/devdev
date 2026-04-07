# 10-Pair Meta Cleanup — Terminal 05 / Pair 05

Date: 2026-04-07
Status: final
Document Type: read-only bounded terminal survey
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal05_pair05.md`
Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- terminal: `05`
- mode: read-only meta-wording survey only
- forbidden: TR/BI mutation, `docs/temp/` mutation, code edits, pair regrading, runtime probing, `TR 58-70` work, promotion claims, patch order writing
- constraint reminder: pair `05` is not on the §10 escalation block list (only `07` and `10` are restricted)

## 2. Assigned Pair and Family

- pair: `05` (`failed_future_ceo_intern`)
- family: `blockguide` (current general-mode `office_power_profile` with regression_ext overlay)
- TR: `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json`
- BI: `bible/05_bi_failed_future_ceo_intern.json`
- prior verdict (`docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`): `clean`, highest severity `P3`, only flagged for `incarnation_type` label drift and a single `Block 1` reference in `CoreIdentity.desire`

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| file exists | yes | yes |
| size | `296,845` bytes | `414,694` bytes |
| UTF-8 decode | ok | ok |
| JSON parse | ok (root `dict`) | ok (root `dict`) |
| top-level shape | `_schema`/`_total_blocks=70`/`_work_id`/`_authority_chain`/`blocks[70]` | `MasterBible.plot_roadmap[70]` mirrors TR `blocks`; `ArcSheets[7]` |

Notes:
- BI `MasterBible.plot_roadmap` is a strict 70-element mirror of TR `blocks` — every meta-wording fix in TR will need a coordinated BI fix in `plot_roadmap`. This is the most important structural fact for routing the cleanup unit.

## 4. Raw Count Snapshot

Each count is one-hit-per-string from a UTF-8 walk over every leaf string, against the §4 meta lexicon (`Block N`, `B\d+`, `블록 N`, `ARC-N`, `Arc N`, `아크 N`, `Phase N`, `페이즈 N`, `Stage N`, `스테이지 N`).

| File | total raw hits | allowed_structural_meta | label_meta_ref | diegetic_meta_ref |
| --- | ---: | ---: | ---: | ---: |
| TR | `572` | `70` (`block_id`) | `70` (`section_rotation`) | `432` |
| BI | `618` | `91` (`block_id`×70 + `arc_id`×21) | `73` (`section_rotation`×70 + `phase`×3) | `454` |

Order order §6 reminder respected: raw token totals are triage evidence only. The classification columns are the actual signal.

## 5. Findings

### 5.1 allowed_structural_meta (no action)

- TR `blocks[*].block_id` × 70 → numeric `block_id`, allowed by §6.1
- BI `MasterBible.plot_roadmap[*].block_id` × 70 → mirrored, allowed
- BI `MasterBible.AssetLibrary.ArcSheets[*].arc_id` × 7 + further `arc_id` references × 14 → allowed by §6.1
- prior survey wording about `BI: protagonist_config.special_ability.evolution`-style anchors does not apply: this pair carries `regression_ext.*`, not `evolution`. No `evolution` field hits found, so the §6.1 evolution carve-out is not load-bearing here.

### 5.2 label_meta_ref (P2 leakage)

- TR `blocks[*].genre_ext.section_rotation` × 70 — every block carries an `ARC-NN ...` prefix as a label value. Per §6.2 + meta-language-leak handoff §5.2/§6, this is the canonical "label present but not label clean" failure. Mirrored 1:1 in BI `MasterBible.plot_roadmap[*].genre_ext.section_rotation`.
- BI `MasterBible.WorldState.opponent_transition_plan[*].phase` × 3 — `Phase 1: 내부 정치 (한가 보수파)` style label values. `phase` is a label field; the `Phase 1` prefix must be stripped to natural language. (Same string is also reused inside `MasterBible.AssetLibrary.Partners[*].cadence`, see §5.3.)

### 5.3 diegetic_meta_ref (P2 leakage, broad)

These are the human-readable / prose / reward-line / payoff-line / scene-facing-summary fields that the meta-language-leak handoff §3.2 + §5 explicitly forbids `Block / ARC / Phase / Stage` wording inside.

TR — top-leaking keys (one-hit-per-string counts):

| key | TR hits | BI hits | nature |
| --- | ---: | ---: | --- |
| `callback` | 134 | 134 | mirrored prose `Block N ...` references; should move semantic meaning into prose, push numeric to `callback_sources` |
| `foreshadow` | 115 | 115 | mirrored prose `→ Block N 회수` references; should split into prose + `foreshadow_targets` |
| `target_event` (under `regression_ext.future_prep`) | 69 | 69 | almost every block has `Block N 회의 배석` style values — these read as scene-facing event labels, not structural ids |
| `reward` (under `content`) | 30 | 30 | reward lines reference `Block 48 회수 준비` etc.; these are payoff-meaning prose |
| `context` (under `content`) | 19 | 19 | scene-facing context summaries reference `Block 4 증설 프로젝트`-style anchors |
| `stakes` | 15 | 15 | stake prose references `블록 14 좌천 공작` |
| `leverage_used` (under `genre_ext`) | 13 | 13 | leverage list items literally read `Block 4 예측` |
| `solution` (under `content`) | 11 | 11 | solution prose references `Block 11 옆자리 상사` |
| `action` (under `regression_ext.future_prep`) | 10 | 10 | action prose references `Block 43 폭로 타이밍` |
| `event_villain` | 6 | 6 | mirrored |
| `exit_function` (BI ArcSheets) | — | 7 | reward-style ArcSheet exit lines reference `Block 1 보상` |
| `entry_function` (BI ArcSheets) | — | 2 | references `블록 8→51` style |
| `payoff_meaning` (BI Seeds) | — | 3 | references `ARC-07 최종 방어의 핵심 블록` |
| `summary` (BI HistoricalEvents) | — | 2 | scene-facing summaries reference `Block 8` |
| `desire` (BI CoreIdentity) | — | 1 | confirms prior survey: still contains `Block 1 안에 ... 회수한다` |
| `cadence` (BI Partners) | — | 3 | reuses `Phase 1: ...` string from §5.2 |

Inference rule applied (§6.2 + meta-language-leak handoff §3.2 inference clause):

- `target_event`, `leverage_used`, `reward`, `solution`, `action`, `context`, `stakes`, `exit_function`, `entry_function`, `payoff_meaning`, `summary`, `desire`, `event_villain`, `ripple_effect`, `place`, `cadence` are not named by exact key in §3.2 of the handoff, but they are clearly "prose, label, short description, reward line, solution line, payoff line, or scene-facing summary" fields, so the handoff inference rule classifies them as `human-readable` and the leakage is `diegetic_meta_ref`.

### 5.4 blocked_by_pair_truth (out of scope, kept separate)

The prior survey already routed the following as **pair-truth drift**, not meta wording. Per §7 prior-survey constraint and §10 merge rule, I keep these explicitly separated and do **not** fold them into the cleanup-now route:

- `BI: MasterBible.protagonist_config.incarnation_type = "회귀자"` while every `MasterBible.plot_roadmap[*].regression_ext.incarnation_type` × 70 says `"빙의자"`. This is structural label drift inside `regression_ext`, not `Block / ARC / Phase / Stage` wording. It does not block meta cleanup, and meta cleanup must not silently fix it.
- `BI: MasterBible.ProjectData.CoreIdentity.desire` `Block 1` reference is **both** a meta-wording leak (counted in §5.3 above) **and** the prior `P3` cosmetic note. Meta cleanup can address the wording side; the desire-statement truth is unchanged.

These two items are noted only so the cleanup terminal does not double-count or accidentally widen scope into pair truth repair.

## 6. Concrete Anchors (max 5)

1. `TR: blocks[0].genre_ext.section_rotation` — value `"ARC-01 오프닝"`. Canonical §5.2-bad example for a label field. Mirrored at `BI: MasterBible.plot_roadmap[0].genre_ext.section_rotation`.
2. `TR: blocks[0].foreshadow[0]` — value `"정태준 스침 → Block 58 회수"`. Canonical §5-good rewrite target: split `→ Block 58 회수` into prose meaning + numeric `foreshadow_targets: [58]`. Mirrored at `BI: MasterBible.plot_roadmap[0].foreshadow[0]`.
3. `TR: blocks[0].regression_ext.future_prep.target_event` — value `"Block 9 회의 배석"`. Per §5.3 inference rule this is a scene-facing event label, not a structural id; needs prose form. 70 mirrored hits in BI.
4. `TR: blocks[12].stakes` — value contains `"블록 14 좌천 공작이 조기 발동"`. `stakes` is named in §6.2 directly. Mirrored at `BI: MasterBible.plot_roadmap[12].stakes`.
5. `BI: MasterBible.ProjectData.CoreIdentity.desire` — value contains `"Block 1 안에 권한 입장권 보상 4종으로 회수한다"`. This is the prior-survey `P3` cosmetic anchor and is also the highest-visibility character-engine prose leak.

## 7. Final Severity

`P2`

Reasoning:

- not `P0`: every artifact-truth check passes
- not `P1`: pair truth is recognizably stable; the only known truth drift (`incarnation_type`) is bounded inside `regression_ext` and is independently tracked by the prior consistency survey, so meta wording cleanup is cleanly separable
- not `P3`: leakage is not sparse or cosmetic — it touches every one of 70 blocks via `section_rotation`, `target_event`, `foreshadow`, `callback`, plus dozens of `reward` / `context` / `stakes` / `solution` / `action` / `leverage_used` instances, plus BI-only ArcSheet/Seed/HistoricalEvent leakage
- `P2`: meets the §7 P2 definition exactly — "repeated disallowed meta leakage exists and bounded cleanup should be scheduled soon"

## 8. Final Execution Route

`cleanup_now`

Smallest cleanup unit: **`TR + BI`** (mandatory coupling).

Rationale:

- BI `MasterBible.plot_roadmap[*]` is a 70-element mirror of TR `blocks[*]`, including the same `section_rotation`, `foreshadow`, `callback`, `target_event`, `reward`, `context`, `stakes`, `leverage_used`, `solution`, `action` strings. A TR-only cleanup pass would immediately go out of sync with BI's mirror.
- BI also carries independent leakage outside the mirror (`ArcSheets.exit_function/entry_function`, `Seeds.payoff_meaning`, `HistoricalEvents.summary`, `CoreIdentity.desire`, `WorldState.opponent_transition_plan.phase`, `Partners.cadence`) which a TR-only pass would miss.
- The pair is not on the §10 escalation block list, so `cleanup_now` is permitted.

## 9. One-Line Minimal Next-Step Suggestion

Codex should schedule a single coordinated `TR + BI` wording-cleanup pass for pair `05` that strips `Block / ARC / Phase / Stage` tokens from the §5.2/§5.3 keys (preserving meaning in prose, pushing numeric anchors into `block_id` / `arc_id` / `foreshadow_targets` / `callback_sources`), and explicitly excludes the `regression_ext.incarnation_type` truth drift from the same patch.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
