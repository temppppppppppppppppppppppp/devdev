# 10-Pair Meta Cleanup — Terminal 04 / Pair 04

Date: 2026-04-07
Status: final
Document Type: read-only bounded survey lane output
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal04_pair04.md`
Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Mode: read-only / no repair / no pair mutation / no `docs/temp/` mutation

## 1. Terminal Scope

- one terminal, one pair
- bounded `legacy meta wording cleanup` survey only
- no `TR` repair, no `BI` repair, no promotion, no Stage 2/3/4 probing, no pair regrading
- only writes to this single output file inside `docs/2026-04-07/`
- does not touch `treatments/`, `bible/`, or `docs/temp/`

## 2. Assigned Pair And Family

- pair: `04`
- work_id: `defense_defect_engineer`
- title: `밀린 막내아들은 방산을 독점한다`
- family overlay: `blockguide` (현대판타지 business-power, `business_growth_profile`)
- prior consistency verdict (carried from `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`): `clean / P3` — pair-consistent, no `blocked_by_pair_truth` carry-over
- pair files surveyed:
  - `treatments/04_defense_defect_engineer_tr_block_070_draft.json`
  - `bible/04_bi_defense_defect_engineer.json`

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| file exists | yes (`308,845` bytes) | yes (`112,213` bytes) |
| UTF-8 byte decode | yes | yes (but file begins with `EF BB BF` UTF-8 BOM) |
| `json.load` strict (no BOM tolerance) | yes | **no** — Python `json.load` raises `Unexpected UTF-8 BOM (decode using utf-8-sig)` |
| `json.load` with `utf-8-sig` | yes | yes |
| top-level shape | dict (`6` keys: `_schema`, `_work_id`, `_title`, `_total_blocks=70`, `_authority_sources`, `blocks[70]`) | dict (`16` keys: `MasterBible`, `arcs[7]`, `npc_timeline`, `opponent_transition_plan[5]`, `capital_curve`, `defeat_blocks`, `_sync_manifest`, …) |
| TR `blocks` length | `70` (matches `_total_blocks`) | n/a |
| BI `_sync_manifest.tr_block_count` | n/a | `70` (matches TR — no `pair 10` style mismatch) |

Hygiene caveat:

- the BI file is consumable but carries a leading UTF-8 BOM. By the order's `§7. Severity` definition this is a `P0` candidate (`JSON parse fails`) under strict `json.load`, while it parses cleanly under `utf-8-sig` and is functionally consumable. This terminal does not escalate the pair to `P0` because the artifact is recoverable with the standard `utf-8-sig` reader the rest of the harness already uses, but the BOM should be stripped during the same wording cleanup pass to avoid future strict-parser regressions.

## 4. Raw Meta-Token Snapshot

UTF-8 read-only token scan, regex `\b(?:Block\s*\d+|블록\s*\d+|ARC[- ]?\d+|Arc\s*\d+|아크\s*\d+|Phase\s*\d+|페이즈\s*\d+|Stage\s*\d+|스테이지\s*\d+|B\d+)\b`. Counts are triage evidence only, not failure counts.

| Asset | Total raw hits | `Block N` | `ARC-N` | `Phase N` |
| --- | ---: | ---: | ---: | ---: |
| TR | `312` | `259` | `40` | `13` |
| BI | `121` | `93` | `16` | `12` |

Per-asset string-leaf walk after `allowed_structural_meta` exclusion (`block_id`, `block_no`, `arc_id`, `arc_no`, `phase_no`, `stage_no`, `foreshadow_targets`, `callback_sources`, `evolution`, plus `_sync_manifest.*_count` numerics):

| Asset | string leaves with meta | `allowed_structural_meta` | `disallowed leakage` |
| --- | ---: | ---: | ---: |
| TR | `237` | `70` | `167` |
| BI | `99` | `77` | `22` |

Order-doc table reported `TR 299 / BI 114` raw English-form hits; my regex includes a slightly broader meta lexicon (Korean variants, `B\d+`) and matches the same general magnitude.

## 5. Findings

### 5.1 `allowed_structural_meta` (correctly placed)

- TR: `blocks[*].block_id = "Block 1"…"Block 70"` (`70` items) and `blocks[*].block_no` integers — these are the canonical structural anchors and are allowed.
- BI: `MasterBible.plot_roadmap[*].block_id`, `arcs[*].arc_id`, `_sync_manifest.tr_block_count = 70`, `_sync_manifest.arc_count = 7` — all allowed.
- BI: `evolution` key — **not present anywhere** in this BI. By `SSOT_bi-evolution-metadata-standard.md` §3 this is allowed (the standard is `P1 recommended`, not mandatory). No false-positive risk for evolution-style meta in this pair.

### 5.2 `label_meta_ref` (label/short-tag fields with disallowed wording)

Systematically dirty label-style fields:

- **TR `blocks[0..4].genre_ext.section_rotation`** — `5` distinct values, all `"ARC-01 — …"`. This is the canonical bad pattern documented in `meta-language-leak-context-handoff.md` §5.2. The remaining `65` blocks have empty `section_rotation`, so this is also a coverage gap (label is supposed to exist with natural-language content per handoff §6).
- **TR `blocks[*].regression_ext.future_prep.target_event`** — `60 / 70` blocks carry short labels of the form `"Block N <짧은 라벨>"` (e.g., `"Block 18 빈 칸 회수"`, `"Block 38 규격 문구 삽입"`, `"Block 30 그림자 법인 서명"`, `"Block 40 카르텔의 목청"`). Reads as label, not prose → `label_meta_ref`.
- **BI `MasterBible.plot_roadmap[0..4].arc_section`** — `5` mirror copies of the same `"ARC-01 — …"` labels. `arc_section` is explicitly listed as forbidden in `meta-language-leak-context-handoff.md` §3.2.
- **BI `opponent_transition_plan[0..4].phase`** — `5` values of the form `"Phase 1: 버림패 프레임"`, `"Phase 2: 규격·시험·폭로 카르텔"`, … `"Phase 5: 이사회 장악 시도"`. The key name is exactly `phase`, which is explicitly forbidden (`§3.2`).
- **BI `MasterBible.plot_roadmap[19,29,39,49,59,68].capital_delta`** — `6` short labels carrying the trailing tag `"… / Phase0 체크포인트"`. **Borderline**: `Phase0` here is the planning-artifact SSOT name (`treatments/phase0/{work_id}_phase0_design.json`), not a narrative `Phase 1/2/3` reference. By the strict regex it matches `Phase\s*\d+`, but semantically it is a process-tooling tag, not in-story meta. Cleanup pass must explicitly decide: rename (e.g., `"… / 기획 체크포인트"`) or carve out as an exception in the validator's allow-list. This terminal flags it as `label_meta_ref` for review, not auto-strip.
- **BI `MasterBible.plot_roadmap[69].capital_delta`** — `"0.0%p (구조 공식 가동 / ARC-07 완성)"`. `ARC-07` reference inside a label-style field → `label_meta_ref`.
- **BI `_schema_description`** — `"… Bible — Phase0/TR draft 동기화 산출물 (첫 live BI)"`. Same `Phase0` system-tag situation; one occurrence; treat as borderline `label_meta_ref` and group with the `capital_delta` decision.

### 5.3 `diegetic_meta_ref` (prose / human-readable fields with disallowed wording)

Natural-language prose fields with embedded `Block N` / `ARC-N` references — these are the higher-risk leaks because they will visibly bleed into manuscript-facing text downstream:

- **TR `blocks[*].regression_ext.butterfly_effect.ripple_effect`** — `32 / 70` blocks. Examples (key-paths only, no long quotes): `blocks[14]` references `Block 30` and `Block 41`; `blocks[16]` references `Block 55`; `blocks[18]` references `Block 20`; etc. These are scene-internal narrator-style sentences, not labels.
- **TR `blocks[*].content.context` / `content.event_villain` / `content.solution` / `content.reward`** — total `~34` leaks (`context 4`, `event_villain 9`, `solution 10`, `reward 11`). Example anchors: `blocks[15].content.solution` (mentions `Block 8`), `blocks[18].content.context` and `.event_villain` and `.reward` (mention `ARC-02`, `ARC-03`, `Block 16`). These are the most prose-grade leaks in the pair and are exactly what `meta-language-leak-context-handoff.md` §7 warns about (`"BLOCK 3에서 얻은 물건으로…"` style erosion).
- **TR `blocks[*].stakes`** — `7` leaks (e.g., `blocks[10].stakes` references `ARC-02`, `blocks[17].stakes` references `Block 31`, `blocks[18].stakes` references `Block 20`).
- **TR `blocks[*].power_shift.protagonist`**, **`genre_ext.method`**, **`genre_ext.opponent.weakness_exploited`**, **`butterfly_effect.changed_event`** — `4` more sparse leaks across the same pattern.
- **TR `blocks[*].genre_ext.capital_delta`** — `7` leaks of the form `"… / Phase0 체크포인트"`; same borderline `Phase0` system-tag situation as the BI side. Flagged for explicit cleanup-policy decision, not auto-strip.
- **BI `MasterBible.plot_roadmap[18,20,49,65].context`** — `4` prose-field leaks mirroring the TR side (references `ARC-02`, `ARC-03`, `Block 48`, `Block 49`, `Block 42`, `Block 59`).

### 5.4 `blocked_by_pair_truth`

- **none**. Pair `04` is `clean` in the prior consistency survey. There is no `is_regressor` mismatch, no end-state drift, and no `TR-incomplete-vs-BI-ahead` blocker. The `_sync_manifest.tr_block_count` matches the actual TR length (`70`), unlike pair `10`. No truth blocker carries forward into this wording cleanup wave.

## 6. Concrete Anchors (5 max)

Key-path first, short explanation second.

1. `TR: blocks[0..4].genre_ext.section_rotation` — `label_meta_ref`. `5` distinct `"ARC-01 — …"` values; remaining `65` blocks have empty `section_rotation`. Canonical handoff §5.2 bad pattern; both wording cleanup and coverage backfill needed.
2. `TR: blocks[*].regression_ext.future_prep.target_event` — `label_meta_ref`. `60 / 70` blocks carry `"Block N …"` short labels. Highest-volume single-field leak in the whole pair.
3. `TR: blocks[*].regression_ext.butterfly_effect.ripple_effect` and `TR: blocks[15,18].content.{solution,context,event_villain,reward}` — `diegetic_meta_ref`. `~32` ripple_effect prose leaks plus `~34` `content.*` prose leaks; the highest downstream-erosion risk in this pair.
4. `BI: opponent_transition_plan[0..4].phase` — `label_meta_ref`. `5` `"Phase N: …"` values directly in the explicitly-forbidden `phase` key.
5. `BI: MasterBible.plot_roadmap[19,29,39,49,59,68].capital_delta` and `BI: MasterBible.plot_roadmap[0..4].arc_section` — mixed bucket. `6` `"… / Phase0 체크포인트"` borderline label tags (process-artifact reference, not narrative `Phase N`) **plus** `5` mirrored `"ARC-01 — …"` `arc_section` values. The `capital_delta` Phase0 tag needs an explicit cleanup-policy decision (rename vs. validator allow-list); the `arc_section` is straight `label_meta_ref`.

## 7. Final Severity

- `P2`

Reasoning:

- not `P0` — files exist, JSON is recoverable (BI BOM is a tracked hygiene caveat, not a fatal block).
- not `P1` — pair is `clean` in the prior consistency survey; wording cleanup is cleanly separable from any truth blocker because no truth blocker exists for pair `04`.
- not `P3` — leakage is not sparse or cosmetic. `label_meta_ref` and `diegetic_meta_ref` are both systematically present across `~70` blocks on the TR side and across the entire `opponent_transition_plan` plus the first arc's `plot_roadmap` slice on the BI side.
- `P2` matches `§7. Severity`'s definition: "repeated disallowed meta leakage exists and bounded cleanup should be scheduled soon."

## 8. Final Execution Route

- `cleanup_now`

Justification: there is no upstream pair-truth blocker, no TR-completion blocker, and no schema-shape blocker. The smallest cleanup unit is **`TR + BI`** (both sides carry mirrored leakage in `arc_section` / `section_rotation` and parallel prose `context`/`stakes`/`ripple_effect` references), so the cleanup must be scheduled as a single coordinated `TR + BI` patch rather than `BI only` or `TR only`.

## 9. Minimal Next-Step Suggestion

Schedule one bounded `TR + BI` wording-cleanup patch for pair `04` that (a) backfills natural-language `section_rotation` / `arc_section` values across all `70` blocks and removes `"ARC-NN — "` prefixes, (b) rewrites `regression_ext.future_prep.target_event` and `butterfly_effect.ripple_effect` to drop `"Block N"` references in favor of structured `foreshadow_targets` / `callback_sources` numeric arrays plus a short natural-language label, (c) replaces `BI.opponent_transition_plan[*].phase` `"Phase N: …"` strings with prose stage names, (d) makes one explicit policy call on the borderline `Phase0` / `ARC-07` `capital_delta` and `_schema_description` system-artifact tags (rename to `"기획 체크포인트"` form **or** carve out in the validator allow-list), and (e) strips the BI file's leading UTF-8 BOM in the same commit so strict `json.load` consumers stop tripping.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
