# Pair 01 Legacy Meta Cleanup Survey - Terminal 01

Date: 2026-04-07
Status: final
Document Type: read-only bounded survey output
Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal01_pair01.md`
Owner Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Terminal Scope

- terminal: `01`
- mode: read-only
- pair scope: pair `01` only
- no `treatments/`, `bible/`, or `docs/temp/` mutation
- no patch order generation
- this terminal answers only the bounded meta cleanup question for pair `01`

## 2. Assigned Pair

- pair id: `01`
- family overlay: `blockguide`
- TR: `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`
- BI: `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json`
- prior `10pair` consistency verdict: `clean / P3` — no upstream truth blocker carried in

## 3. Artifact Truth

| File | Exists | UTF-8 Decode | JSON Parse | Root | Notes |
| --- | --- | --- | --- | --- | --- |
| TR | yes | ok | ok | `dict` | `_schema = "tr.v1"`, `_total_blocks = 60`, `len(blocks) = 60` consistent |
| BI | yes | ok | ok | `dict` | top: `_schema_version`, `_genre`, `MasterBible` |

No `P0` (file/decode/parse) issues.

## 4. Raw Meta-Token Snapshot

Local read-only scan with token family `Block / 블록 / B<digits> / ARC[-/space]<digits> / Arc / 아크 / Phase / 페이즈 / Stage / 스테이지`.

| Asset | Total raw token hits | Allowed structural | Allowed metadata zone | `diegetic_meta_ref` | `label_meta_ref` | `other_natural_field` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TR | `325` | `60` | `0` | `205` | `60` | `0` |
| BI | `335` | `60` | `10` | `172` | `78` | `15` |

Order Section 5 interpretation rule applied: raw counts are triage evidence only, not failure counts. Classification follows.

## 5. Findings

### 5.1 `allowed_structural_meta`

- TR: every `blocks[i].block_id = "Block <i+1>"` for `i in 0..59`. Allowed by Section 6.1 — `block_id` is the canonical structural id slot.
- BI: every `MasterBible.plot_roadmap[i].block_id = "Block <i+1>"` for `i in 0..59`. Same rule. Clean.
- BI metadata zone (`SectorSceneKit.sectors[*].arcs[*]`, `ControlThemeMap._rule`): pure arc-id slot lists like `["ARC-01"]` and a single underscore-prefixed metadata rule line. Treated as structural meta zone, not leakage.

### 5.2 `label_meta_ref`

- TR: `60 / 60` blocks carry `genre_ext.section_rotation` populated with the **exact bad-example shape** from `meta-language-leak-context-handoff.md` Section 5.2:
  - `"ARC-01 - 원자재로 첫 증명을 만들고 금융위기 숏을 준비하다"`
  - the prose tail is fine; the leading `ARC-01 -` prefix is the disallowed leak
- BI: `section_rotation` × `72` hits, mirroring the same `ARC-NN - <prose>` shape across all 6 arcs. Duplicated under both `MasterBible.WorldState.opponent_transition_plan[*]` and `MasterBible.opponent_transition_plan[*]` (the same template appears in two parallel containers, doubling the surface).
- BI: `phase` leaf × `6` carries human-readable phase labels with `Phase`-style wording leakage (subset of the same template family).

This is the primary `label_meta_ref` cluster for pair `01` and it is mechanically isolatable: strip the leading `ARC-NN - ` prefix and keep the natural-language tail.

### 5.3 `diegetic_meta_ref`

- TR: `205` hits, dominated by:
  - `blocks[*].callback[*]`: `105` hits (e.g., `"Block 1에서 '원자재 트레이딩으로 시작'이라고 선언한 것의 실행"`)
  - `blocks[*].foreshadow[*]`: `83` hits (e.g., `"... - Block 2 원유 투자 복선"`)
  - long tail: `stakes` × 4, `relationship_delta.before` × 6, `content.context` × 1, `content.event_villain` × 2, `content.solution` × 1, `content.reward` × 1
- BI: `172` hits, mostly mirroring TR through `MasterBible.plot_roadmap[*].foreshadow` (`71`) and `MasterBible.plot_roadmap[*].callback` (`98`), plus `context` × 1 and `relationship_delta.before` × 2.
- The TR and BI diegetic leaks are not independent — the BI `plot_roadmap` `foreshadow / callback` strings are textually parallel to the TR ones. Cleaning one without the other would re-create drift.

### 5.4 `blocked_by_pair_truth`

- none.
- prior `10pair` consistency survey rated pair `01` as `clean / P3`.
- this terminal found no `tr-truth ↔ bi-truth` divergence that would block wording cleanup. The leakage is wording-only and lives in fields explicitly named in Section 6.2.

### 5.5 Classification Edge Note (for Codex merge)

- BI `opponent_transition_plan[*].arc = "ARC-NN"` (`12` hits) is a pure arc-id slot, not a prose field. Section 6.1 lists `arc_id` and `arc_no` but not the bare key `arc`. This is most likely an undeclared structural id slot rather than diegetic leakage; classified here as `other_natural_field` and flagged for Codex to either:
  - normalize the key name to a Section 6.1 canonical (`arc_id`/`arc_no`), or
  - whitelist `arc` as a structural id slot in the policy.
- This is a classification housekeeping item, not a wording-cleanup item.

## 6. Concrete Anchors

Five anchors total, key-path first.

1. `TR: blocks[0].genre_ext.section_rotation` — value is the verbatim bad example from the policy doc Section 5.2 (`"ARC-01 - 원자재로 ..."`); same template repeats on all 60 blocks.
2. `TR: blocks[1].callback[0]` — `"Block 1에서 '원자재 트레이딩으로 시작'이라고 선언한 것의 실행"`. Representative `callback` diegetic leak; `callback` × 105 follow this shape.
3. `BI: MasterBible.plot_roadmap[1].foreshadow[1]` — `"한시우 독백: '금도 간다' - Block 4 금 투자 복선"`. Representative BI `foreshadow` diegetic leak that mirrors the TR text.
4. `BI: MasterBible.WorldState.opponent_transition_plan[0].section_rotation` — `"ARC-01 - 원자재로 첫 증명을 만들고 금융위기 숏을 준비하다"`. The TR `section_rotation` template propagated into BI.
5. `BI: MasterBible.opponent_transition_plan[0].section_rotation` — same template under a parallel sibling container; cleanup must touch both BI containers, not only the `WorldState` one.

## 7. Severity

`P2`

Reason: repeated disallowed meta leakage exists across both TR and BI in fields explicitly named by Section 6.2 (`section_rotation`, `foreshadow`, `callback`, `stakes`, `phase`, plus `content.*` long tail). It is widespread (`>400` total disallowed-zone hits across the pair) and matches the canonical bad-example shape verbatim. Bounded cleanup should be scheduled soon, but no `P0/P1` blocker prevents it.

## 8. Execution Route

`cleanup_now`

- pair `01` was already `clean` in the prior consistency survey, so wording cleanup does not need to wait on truth repair
- the leakage is mechanically isolatable: strip leading `ARC-NN - ` / `Block N` prefix tags and keep the natural-language tail
- TR and BI must be cleaned together (`TR + BI`) because the BI `plot_roadmap` foreshadow/callback strings are textually parallel to the TR ones and would re-drift if cleaned in isolation
- the `arc: "ARC-NN"` BI key-naming question (Section 5.5) should be settled by Codex before patch authoring, but does not block wording cleanup itself

Smallest cleanup unit: `TR + BI` (paired wording sweep, single repair unit)

## 9. Next-Step Suggestion

Author a single bounded wording-only patch order that strips `Block N / ARC-NN / Phase N` prefixes from TR `genre_ext.section_rotation`, `foreshadow`, `callback`, `stakes`, `relationship_delta.before`, and `content.*` long-tail leaves, and applies the same strip to BI `plot_roadmap[*].foreshadow / callback` and both `opponent_transition_plan[*].section_rotation` containers — no structural id slot, `block_id`, `evolution`, or arc-list metadata is touched.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
