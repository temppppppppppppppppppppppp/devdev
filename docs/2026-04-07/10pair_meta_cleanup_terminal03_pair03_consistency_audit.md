# 10-Pair Meta Cleanup Terminal 03 — Pair 03 Consistency Audit

- Date: 2026-04-07
- Status: final
- Document Type: bounded post-cleanup consistency audit (one terminal, one pair)
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03_consistency_audit.md`
- Owning Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_execution_order.md`
- Source Survey: `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03.md`
- Prior Execution Audit: `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03_execution_audit.md`
- Terminal: `03`
- Patched Pair: `03_chaebol_ent_empire`
- Family: `blockguide`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Scope

After the prior legacy meta cleanup pass on pair `03`, the user requested a
cross-cut + individual consistency check (citing NPC name spelling mismatches
across surfaces as an example of the kind of issue to find and fix).

This audit covers a single pair only. No system-track files, no `docs/temp/`,
no other pairs, no schema redesign.

Touched files:

- `bible/03_bi_chaebol_ent_empire.json` (BI only — TR mirror was already clean)

Read-only verified:

- `treatments/03_chaebol_ent_empire_tr_block_070_draft.json`

## 2. Survey Dimensions Checked

| # | Dimension | Result |
|---|---|---|
| 1 | NPC roster cross-cut name parity (KeyNPCs vs npc_timeline vs prose) | **Issue found** (F1) |
| 2 | TR↔BI plot_roadmap mirror parity (block_id, block_no, title, pov_character, location, time_span, emotional_beat, tension_level on all 70 blocks) | Clean |
| 3 | Capital / money figure cross-block coherence | Clean |
| 4 | HistoricalEvents.events ↔ plot_roadmap index alignment | Clean |
| 5 | opponent_transition_plan internal integrity (entry_block in block_range, method_blocks parallel-array shape) | **Issue found** (F2) |
| 6 | foreshadow_map planted/payoff range integrity | Clean (1-based, 1..70 in range) |
| 7 | callback_sources sanity (no self / future / OOR) | Clean |
| 8 | method_blocks sanity vs methods | Partial — see F2 |
| 9 | Schema variance across blocks | Acceptable variance, intentional |
| 10 | Year / date references | Clean |
| 11 | Protagonist name / config | Clean |

## 3. Findings

### F1 — KeyNPCs name parenthetical breaks cross-surface parity (P1, REAL)

**Observation.** All 13 entries in `BI.MasterBible.AssetLibrary.KeyNPCs` embedded
an occupational/career parenthetical inside the `name` field, while every other
surface used the bare name:

| Surface | Form |
|---|---|
| `KeyNPCs[*].name` | `"강이현(연습생→ORBIT 센터)"` |
| `npc_timeline[*].name` | `"강이현"` |
| `opponent_transition_plan[*].main_actors` | `"강이현"` |
| `plot_roadmap[*].pov_character` | bare name |
| BI prose mentions of `강이현` (bare) | 149 occurrences |
| BI prose mentions of `강이현(연습생→ORBIT 센터)` | 1 occurrence |

A literal join of `KeyNPCs[*].name ∩ npc_timeline[*].name` returned **0/13**
even though both arrays describe the same 13 people. This is exactly the
"NPC가 이름이 다르다" category the user wanted to eliminate.

**Why the parenthetical wasn't redundant.** The existing `role` field carries
the **narrative function** ("구조적 적대자 / 심판자", "핵심 자산 / 내부 갈등 축",
etc.). The parenthetical inside `name` carried the **occupational position /
career arc** ("아버지", "연습생→ORBIT 센터", etc.). Different semantics — the
parenthetical info had to be preserved, not just discarded.

### F2 — opponent_transition_plan parallel-array gap on entries 0 and 4 (P3, regression I introduced)

**Observation.**

```
opponent_transition_plan[0]: methods length 4, method_blocks ABSENT
opponent_transition_plan[4]: methods length 3, method_blocks ABSENT
opponent_transition_plan[1,2,3,5,6]: method_blocks present (parallel arrays)
```

The prior cleanup pass added `method_blocks` only to entries whose `methods`
items had inline `(Block N)` parentheticals to extract. Entries `0` and `4` had
clean methods strings (no inline tethers), so the field was never created.
This left the OTP array's per-entry shape uneven across the 7 entries, breaking
the implied parallel-array contract for individual integrity.

## 4. Findings Deferred (and Why)

### F3 — Explore agent's claim of `foreshadow_map[3].payoff_blocks=[30,70]` being out-of-range — **FALSE ALARM**

A read-only Explore agent flagged `foreshadow_map[3].payoff_blocks[1]=70` as
P1 truth-breaking (claiming `70` exceeds the valid index range `0-69`).

This is **wrong**. Independent verification:

```
TR.blocks[*].block_id: "Block 1"..."Block 70"   (1-based labels)
TR.blocks[*].block_no: 1..70                     (1-based ints)
foreshadow_map ints across all 7 entries: min=1, max=70
```

The file uses **1-based** block numbering. `Block 70` exists. All 7
foreshadow_map entries are valid. **No fix needed.** Agent finding was based on
an unverified 0-based assumption.

### F4 — `opponent_transition_plan[*].main_actors` mixes character names with abstract forces — out of scope

7 of 7 OTP entries mix concrete KeyNPC names (`권도현`, `한도윤`, `백승문`,
`마커스 리`) with abstract faction labels (`'감사실'`, `'내부 냉소'`,
`'플랫폼 정책'`, `'외부 자본'`, `'공신 라인'`, etc.) inside the same
`main_actors` array.

This is a **pre-existing schema design choice**, not a regression introduced by
the cleanup pass, and it is not a name spelling mismatch. The user explicitly
asked for consistency fixes, not a schema redesign. Per execution order §3.3
("do not normalize unrelated schema naming"), this is left untouched and
documented as observation.

If a future wave decides to split this into `main_actors` (NPCs only) +
`antagonistic_forces` (factions), that is a separate schema-design decision and
should be applied uniformly across all `01-10` pairs in one wave, not just
pair `03`.

## 5. Fixes Applied

### Fix 1 (F1): KeyNPCs name normalization

For all 13 entries in `BI.MasterBible.AssetLibrary.KeyNPCs`:

- Pre-flight: regex `^([^()]+?)\(([^()]*)\)\s*$` validated against all 13
  entries — all matched.
- `name` field replaced with the bare name (group 1, trimmed).
- New sibling field `profile` added carrying the parenthetical content
  (group 2, trimmed).
- Insertion order: `name` → `profile` → existing `role` → existing `desc`.

Resulting 13 entries:

| name | profile |
|---|---|
| 권도현 | 아버지 |
| 강이현 | 연습생→ORBIT 센터 |
| 한도윤 | 경영관리실장→공신 라인 실무자 |
| 서민재 | A&R 총괄→전략 참모 |
| 윤서아 | 배우 |
| 오지혁 | 현장 매니저→현장 브레인 |
| 문선우 | 호텔 서브 셰프→F&B 브랜드 얼굴 |
| 최라희 | 콘텐츠 기획자→브랜딩 설계자 |
| 백승문 | 제국엔터 전략본부장 |
| 박재인 | 스트리머→팬덤 엔진 |
| 하은솔 | 유통 계열 MD |
| 마커스 리 | 글로벌 플랫폼 아시아 총괄 |
| 이세린 | 법무 |

After fix: `set(KeyNPCs[*].name) ∩ set(npc_timeline[*].name)` = **13/13**.

### Fix 2 (F2): OTP method_blocks parallel-array completion

- `opponent_transition_plan[0]` (`ARC-01`): added
  `method_blocks: [[], [], [], []]` matching the 4 methods.
- `opponent_transition_plan[4]` (`ARC-05`): added
  `method_blocks: [[], [], []]` matching the 3 methods.
- Insertion position: immediately after `methods` (matches the layout used by
  entries `1`, `2`, `3`, `5`, `6`).

After fix: all 7 OTP entries have `len(methods) == len(method_blocks)`.

## 6. Validation Results

| # | Check | Result |
|---|---|---|
| 1 | Byte-level UTF-8 read-back, no BOM, CRLF preserved, no trailing newline | Pass |
| 2 | `json.loads` parse | Pass |
| 3 | KeyNPCs ↔ npc_timeline name parity | **13/13** (was `0/13`) |
| 4 | Profile coverage (every KeyNPCs entry has non-empty `profile`) | 13/13 |
| 5 | OTP method_blocks parity (`len(methods) == len(method_blocks)` on all 7 entries) | 7/7 |
| 6 | Meta-leak walker regression (prior `0` hits still holds) | **0** disallowed hits in BI |
| 7 | Allowed structural meta untouched (`block_id`, `evolution`, `arc_id`, `block_range`, `entry_block`) | Pass |
| 8 | TR file untouched (size 360,666 bytes — same as after prior cleanup) | Pass |

## 7. File Size Delta

- BI: `453,836` → `454,331` bytes (+`495` bytes)
  - Source of growth: 13 new `profile` keys + values, plus 2 empty
    `method_blocks` arrays (4 and 3 inner empty lists).
- TR: `360,666` → `360,666` bytes (no change).

## 8. Files Touched

- `bible/03_bi_chaebol_ent_empire.json` (Fix 1 + Fix 2)
- `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03_consistency_audit.md`
  (this audit note)

No other files mutated.

## 9. Stop Gates Held

- Pair truth not touched (no plot_roadmap edits, no callback/foreshadow edits,
  no character role swaps) — applies to F1 / F2.
- Allowed structural metadata not touched (`evolution`, `block_id`, `arc_id`,
  `block_range`, `entry_block`).
- Schema naming not normalized beyond the F1 / F2 scope (OTP `main_actors`
  mixing left as-is, schema-key uniformity in plot_roadmap left as-is).
- No fix made on the basis of the unverified Explore agent claim that turned
  out to be a 1-vs-0 indexing misread (F3).

## 10. Follow-up Backfill: callback_sources Coverage Parity

After F1 / F2 a deeper readiness probe found that pair `03` had only `48/69`
(`70 %`) `callback_sources` coverage on callback-bearing blocks, while sibling
pairs `01`, `02`, `05` were at `100 %` and pair `07` at `91 %`. Because
`callback_sources` is consumed by `scripts/audit_bi_5pass.py`,
`scripts/tr_batch_harness.py`, and the wuxia-side equivalents, this gap was a
real outlier — not dead metadata. The user authorized a follow-up backfill
pass.

### 10.1 Scope

Add `callback_sources` to the 21 plot blocks that had callback prose but no
structural sibling. Source block numbers were inferred per block by reading
the prose and locating the cited past event in the actual block roster +
neighborhood titles. No callback prose was rewritten — only the structural
sibling list was added.

### 10.2 Per-block backfill table

| Block | Sources | Rationale (excerpt) |
|---|---|---|
| 23 | `[21, 22]` | "초반에 깐 시스템" → b21 연습실 규칙, "윤서아 배후" → b22 윤서아의 그림자 |
| 26 | `[12, 15]` | "연습생 시절부터 강이현 문제" → b12 팀 적응 문제, b15 데뷔조를 고르다 |
| 29 | `[]` | Phase 0 pre-block reference; no integer anchor (explicit empty, replaces prior absence so coverage is uniform) |
| 30 | `[24, 27, 29]` | "비방송 팬 유입" → b24, "배우 간판 효과" → b27, "인재 확보 문제의식" → b29 |
| 35 | `[24, 34]` | "방송 밖 팬 유입" → b24, "플랫폼 실패" → b34 플랫폼이 문을 닫다 |
| 38 | `[32, 35]` | "포맷 설계" → b32 포맷을 먼저 만든다, "분산 접점 구조" → b35 |
| 44 | `[22, 37]` | "윤서아 배후 추적 첫 부분 회수" — planted at b22, deepened at b37 |
| 45 | `[41, 42, 43]` | "문선우에게 쌓인 반응" — b41 / b42 / b43 (주방 → 메뉴 테스트 → 셰프 팀) |
| 46 | `[31, 36]` | "박재인에게 쌓인 데이터" → b31 카메라 한 대로도 스타는 뜬다, b36 박재인 이름이 아니라 습관 |
| 47 | `[45]` | "빠르게 키운 팝업·상품 구조" → b45 문선우, 얼굴이 되다 |
| 49 | `[47, 48]` | "위기" → b47 위생 논란, "장부 추적" → b48 장부 속 이상한 흐름 |
| 50 | `[40, 45, 46, 49]` | "시장형 회사 체질" → b40 / b45 / b46 / b49 |
| 51 | `[15, 25, 26]` | "강이현 중심 팀 구성" → b15 데뷔조 / b25 팀을 만드는 일 / b26 천재는 팀을 찢는다 |
| 52 | `[51]` | "직전 블록에서 점화한 무드 전략" → b51 데뷔가 아니라 점화 |
| 53 | `[1, 12, 26]` | "연습생 시절부터 강이현 양면성" — earliest signs at b1 / b12 / b26 |
| 60 | `[38, 57, 59]` | "팬 접점 구조" → b38 / b57, "운영 기준 변화" → b59 잠깐 멈춘 방 |
| 61 | `[54, 55, 56]` | "해외 성공 뒤 짙어진 통제권 냄새" — 마커스 라인 b54 / b55 / b56 |
| 62 | `[5, 16, 18]` | "초반부터 예고된 한도윤" — first move b5 / 감사실 b16 / 아버지의 진짜 조건 b18 |
| 63 | `[1, 18]` | "숨은 조건 조항" — planted at b1 위임 계약, surfaced at b18 (also matches `foreshadow_map[0]` F-001 planted=`[1]`, payoff=`[63, 68]`) |
| 67 | `[28, 59]` | "오랜 자기 성찰" → b28 새벽의 숨고르기, b59 잠깐 멈춘 방 |
| 70 | `[1, 69]` | "쓰레기통처럼 던져진" → b1 origin, "팬 플랫폼" → b69 우리 플랫폼 |

Block `29` is the only entry with explicit `callback_sources: []`. The
prose references a `Phase 0` pre-block design event with no integer block
anchor (this is the same policy decision documented in the prior execution
audit `§5`, now expressed as an explicit empty list rather than an absent
field so the schema is uniform across all 69 callback-bearing blocks).

### 10.3 Validation after backfill

| # | Check | Result |
|---|---|---|
| 1 | UTF-8 + JSON parse (TR + BI) | Pass |
| 2 | TR LF + trailing newline preserved; BI CRLF + no trailing newline preserved | Pass |
| 3 | TR ↔ BI mirror parity on `callback_sources` (all 70 blocks) | **0 mismatches** |
| 4 | `callback_sources` sanity (no future / self / OOR; all integers in `1..70`) | **0 issues** |
| 5 | Meta-leak walker regression | **0** disallowed hits, TR + BI |
| 6 | KeyNPCs ↔ npc_timeline name parity (F1 hold) | **13/13** |
| 7 | OTP `methods`/`method_blocks` length parity (F2 hold) | 7/7 |
| 8 | `block_id` sequence | `Block 1..Block 70` intact |
| 9 | Cross-pair coverage check | pair 03 = `100 %` (69/69), now in tier with `01`, `02`, `05` |

### 10.4 File Size Delta (cumulative across all three passes)

- TR: `357,719` → `360,666` (cleanup) → `361,976` (backfill) — total `+4,257` bytes
- BI: `450,005` → `453,836` (cleanup) → `454,331` (consistency) → `455,905` (backfill) — total `+5,900` bytes

Source of backfill growth: 21 new `callback_sources` integer-list keys on each
side (TR + BI), most under 5 ints each.

### 10.5 Stop Gates Held in §10

- Callback **prose** not rewritten — only the structural sibling added.
- Pair truth not touched.
- Source block numbers selected only where the prose unambiguously cited a
  prior event resolvable to a single block neighborhood; ambiguous prose was
  not fabricated. Block `29` is the explicit `[]` case for that reason.

## 11. Finalize Pass: Hard Gate Closure (Block 63 + Block 10)

After the §10 backfill, a final readiness audit using the real downstream
validators (`validate_bible_canonical_structure`,
`validate_treatment_canonical_structure`,
`scripts/tr_batch_harness.compute_treatment_metrics`) showed that pair `03`
was the best-conformance pair of all 10 by `hard_gate_failures` count
(`1` vs `2-8` for siblings) but still had two pre-existing baseline issues:

1. `late_thin_blocks_zero: False` — Block 63 [`빼앗기는 날`] had a `bundle_size`
   of `347` chars, two below the `350` threshold for the "thin" tag, and
   it sits in the late `>60` zone so the `late_thin_blocks_zero` gate failed.
2. `npc_continuity_mismatch_count: 1` — Block 10 한도윤(경영관리실장)
   `relationship_delta.before` did not match Block 5 한도윤
   `relationship_delta.after` (no intermediate block carries 한도윤).

Both were verified as **pre-existing** by re-running
`compute_treatment_metrics` against `git HEAD` baseline (string-identical
mismatch examples, identical thin-block list). Neither was a regression
introduced by the cleanup or backfill passes. The user authorized closing
both as a finalize step.

### 11.1 Fix 11A — Block 63 densification

Block 63 had `context: 83`, `event_villain: 65`, `solution: 65`, `reward: 84`,
`stakes: 50` for a total `bundle_size = 347` (thin threshold = `350`,
critical threshold = `300`).

Densified to bring Block 63 in line with the pair `03` average (`avg_bundle_chars
≈ 463`), expanding `content.context`, `content.event_villain`,
`content.solution`, `content.reward` while preserving:

- the original narrative beats (조건부 위임 계약서 조항 발동, `666억` 자본
  급감, 사업이 아닌 권력에서의 첫 패배)
- the existing characters (권태하, 권도현, 한도윤, 이세린, 외부 자본)
- mirror parity to `BI.MasterBible.plot_roadmap[62]` (TR + BI patched
  string-identical)
- zero meta-language leaks (Block N / ARC / Phase / Stage absent — verified
  post-write)
- the existing `relationship_delta`, `power_shift`, `genre_ext`, `stakes`,
  `tension_level`, and other structural fields (untouched)

New `bundle_size`: `762` chars (well above `350` threshold).
`one_sentence_like_solution_blocks`: 63 → 62 (Block 63 solution now has
`3+` sentences).

### 11.2 Fix 11B — Block 10 한도윤 continuity sync

Block 5 한도윤 `relationship_delta.after`:

```
태하가 실패 구조까지 추적하자 단순한 도련님이 아님을 불편하게 인식
```

Block 10 한도윤 `relationship_delta.before` (before fix):

```
태하가 실패 구조까지 추적하자 불편해하면서도 구조조정 카드를 계속 쥐고 있는 적대자
```

Patched Block 10 한도윤 `relationship_delta.before` to be **string-identical**
to Block 5 한도윤 `relationship_delta.after`. Applied to both
`TR.blocks[9]` and `BI.MasterBible.plot_roadmap[9]`. No other field on Block
10 modified — `after` and the other 3 character entries (`권도현`, `윤서아`,
`강이현`) stay as-is, so the chain Block 10.한도윤.after → Block 14.한도윤.before
("당장 청산은 못 하지만 계속 흔들 감시자") still string-matches.

### 11.3 Validation after finalize

| # | Check | Result |
|---|---|---|
| 1 | UTF-8 + JSON parse (TR + BI) | Pass |
| 2 | TR LF + trailing newline; BI CRLF + no trailing newline preserved | Pass |
| 3 | `validate_bible_structure` | `(True, [], [])` |
| 4 | `validate_treatment_structure` | `(True, [], [])` |
| 5 | `validate_bible_canonical_structure` | `(True, [], [])` |
| 6 | `validate_treatment_canonical_structure` | `(True, [], [])` |
| 7 | `compute_treatment_metrics.hard_gate_failures` | **`[]`** (was `['late_thin_blocks_zero']`) |
| 8 | `production_density_gate` | **`True`** (was `False`) |
| 9 | `npc_continuity_mismatch_count` | **`0`** (was `1`) |
| 10 | `late_thin_blocks_zero` gate | **`True`** (was `False`) |
| 11 | `thin_blocks` list | **`[]`** (was `[63]`) |
| 12 | `diegetic_meta_ref_count` | `0` (held) |
| 13 | `label_meta_ref_count` | `0` (held) |
| 14 | `unresolved_foreshadow_count` | `0` (held) |
| 15 | `callback_sources` coverage (BI plot_roadmap) | `69/69` (held) |
| 16 | `KeyNPCs` ↔ `npc_timeline` name parity | `13/13` (held) |
| 17 | TR ↔ BI Block 63 content parity | OK |
| 18 | Block 5 한도윤.after `===` Block 10 한도윤.before (TR + BI) | True |
| 19 | Meta-leak walker (`Block N` / `ARC` / `Phase` / `Stage`) — TR / BI | `0` / `0` |

Per-gate breakdown:

```
✅ critical_thin_blocks_zero
✅ thin_blocks_ratio_ok
✅ late_thin_blocks_zero
✅ short_stakes_blocks_total_ok
✅ endgame_low_stakes_zero
✅ callback_ratio_ok
✅ unresolved_foreshadow_count_ok
✅ section_rotation_present
✅ late_blank_opponent_ok
✅ normalized_solution_stakes_repeat_ok
✅ diegetic_meta_ref_zero
✅ label_meta_ref_zero
✅ diegetic_block_ref_zero
```

All `13/13` hard gates pass.

### 11.4 Cross-pair ranking after finalize

| Rank | Pair | hard_gate_failures count |
|---|---|---|
| **1** | **03** | **0** ← `production_density_gate: True` (only pair in repo) |
| 2 | 05 | 1 |
| 3 | 06 | 2 |
| 3 | 09 | 2 |
| 5 | 01 | 3 |
| 6 | 02 | 5 |
| 6 | 07 | 5 |
| 8 | 04 | 6 |
| 8 | 10 | 6 |
| 10 | 08 | 8 |

Pair `03` is the **only pair in the entire `01-10` set that passes
`production_density_gate`** as of this finalize pass.

### 11.5 File size delta (cumulative across 4 passes)

| File | Original | + Cleanup | + Consistency | + Backfill | + Finalize | Total |
|---|---|---|---|---|---|---|
| TR | `357,719` | `360,666` | `360,666` | `361,976` | `362,958` | `+5,239` |
| BI | `450,005` | `453,836` | `454,331` | `455,905` | `456,887` | `+6,882` |

Source of finalize growth: Block 63 content prose expansion (`+~415` chars on
each side) plus the Block 10 한도윤 `before` string swap (small delta).

### 11.6 Stop Gates Held in §11

- Pair truth preserved: Block 63 narrative beats unchanged, characters
  unchanged, `666억` capital figure unchanged, opponent unchanged,
  emotional_beat / tension_level / location / time_span unchanged.
- Mirror parity: TR `blocks[62]` and BI `plot_roadmap[62]` patched
  string-identical for all 4 content sub-fields.
- No new fields introduced. No schema-shape change. No meta leaks.
- Block 10 fix is a single-string sync — `after` and 3 other character entries
  on Block 10 untouched.
- Pre-flight guards in the patch script confirmed the baseline state matched
  expected before-values (so a re-run cannot silently double-apply or apply to
  drifted state).

### 11.7 Final readiness verdict

Pair `03` now passes:

- All 4 canonical/raw validators (`validate_*_structure`,
  `validate_*_canonical_structure`)
- All 13 hard gates in `tr_batch_harness.compute_treatment_metrics`
- `production_density_gate` (uniquely among the `01-10` set)
- Cross-cut consistency: `KeyNPCs` ↔ `npc_timeline` 13/13, TR ↔ BI mirror
  parity, `callback_sources` 69/69, NPC continuity 0 mismatches
- Zero meta-leak walker hits (TR + BI)
- Format integrity (UTF-8, line endings, no BOM, JSON parse)

**Pair 03 is production-ready.** No remaining hard-gate failures, no
remaining cross-cut consistency issues, no remaining narrative continuity
mismatches that the harness checks. It is the highest-conformance pair in
the current `01-10` repository.
