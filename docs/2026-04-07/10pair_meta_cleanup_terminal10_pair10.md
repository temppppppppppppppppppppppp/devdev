# 10-Pair Legacy Meta Cleanup — Terminal 10 / Pair 10

- Date: 2026-04-07
- Status: final
- Document Type: read-only bounded survey, single-pair lane output
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal10_pair10.md`
- Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_10terminal_opus_order.md`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Lane Owner: Opus Terminal 10
- Mutation Scope: this output file only; no `treatments/`, `bible/`, `docs/temp/`, or unrelated dirty file was touched

## 1. Terminal Scope

This terminal answers exactly one bounded question for one pair:

- across pair `10` (`jaebeol3se_loss_line`), which human-readable / label fields still carry disallowed `Block / ARC / Phase / Stage` wording, which hits are allowed structural metadata, and whether wording cleanup can proceed independently of the prior `TR incomplete vs BI ahead` truth blocker.

This terminal does not:

- repair TR or BI
- modify `docs/temp/` or any pair file
- regrade pair quality
- run Stage 2/3/4 probes
- write the merged 10-pair survey (Codex owns that)
- regenerate or finish TR blocks

## 2. Assigned Pair And Family

- Pair: `10`
- Work id: `jaebeol3se_loss_line`
- Family overlay: `blockguide` (`docs/blockguide/SSOT_blockguide-integrated-order.md`)
- TR: `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`
- BI: `bible/10_bi_jaebeol3se_loss_line.json`

## 3. Artifact Truth

| Check | TR | BI |
| --- | --- | --- |
| File exists | yes (`368,193` bytes, mtime `2026-04-06 18:53`) | yes (`16,728` bytes, mtime `2026-04-06 18:53`) |
| UTF-8 decode | pass | pass |
| JSON parse | pass | pass |
| Top-level type | `list` | `dict` |
| Live block count (TR) | `70` (`Block 1` ... `Block 70`, every block has populated `content.*` strings) | n/a |
| `_sync_manifest.tr_block_count` (BI) | n/a | `70` |

Important file-state delta vs the prior `2026-04-06` consistency survey:

- the prior survey recorded `TR root list length = 57`, `BI _sync_manifest.tr_block_count = 5`, and a live `TR incomplete vs BI ahead` truth gap
- the current on-disk state shows `TR root list length = 70` with all 70 blocks populated (no empty `content.*`) and `BI _sync_manifest.tr_block_count = 70`
- this terminal is read-only and is not authorized to certify TR 58-70 truth correctness; it only reports that the file-shape symptom of the prior truth blocker is no longer visible at the file level
- final certification of TR 58-70 truth remains a Codex merge-step responsibility, not a meta-wording lane responsibility

## 4. Raw Token-Hit Snapshot

Read-only scan with strict regex (`Block N` / `B<digit>` / `블록 N` / `ARC-NN` / `Arc N` / `arc-N` / `아크 N` / `Phase N` / `페이즈 N` / `Stage N` / `스테이지 N`).

| Surface | Strings carrying ≥1 meta token | Token instances | Bucketed `allowed_structural_meta` strings | Bucketed disallowed strings |
| --- | ---: | ---: | ---: | ---: |
| TR | `257` | `283` | `70` (all are `block_id`) | `187` |
| BI | `30` | `30` | `5` | `25` |

Triage reading per the order's interpretation rule:

- raw token hits are not failure counts; the meaningful numbers are the bucketed disallowed-string counts
- the order's 04-07 raw snapshot of `TR 685 / BI 29` reflects a character-level scan; this terminal's strict regex with digit requirement is what feeds the field-classification verdict below
- the BI surface is narrow and almost entirely concentrated in two structural list paths; the TR surface is wide and saturated

## 5. Findings First

### 5.1 `allowed_structural_meta`

TR — all 70 hits are `block_id`:

- every TR block stores its identifier as `block_id: "Block N"` (e.g. `[0].block_id = "Block 1"`, `[69].block_id = "Block 70"`)
- this is exactly the form the policy contract permits in `block_id` and is not in cleanup scope

BI — small allowed surface:

- the `_sync_manifest` numeric counters (`tr_block_count`, `arc_count`, `defeat_block_count`, `capital_checkpoint_count`, etc.) are integers, not meta-wording strings
- no `evolution` field carrying block-trace strings was found in this BI; the BI does not currently lean on the `evolution` metadata standard

False positives that this lane explicitly excludes from cleanup scope:

- `_authority_chain[2]` value `"treatments/phase0/jaebeol3se_loss_line_phase0_design.json"` — the substring `phase0` is a filesystem directory name, not a leaked stage label, and must not be rewritten
- TR `block_id` values themselves — allowed by contract

### 5.2 `label_meta_ref` (label fields whose values still encode `Block / ARC / Phase / Stage` wording)

TR — heavy and structural:

- `genre_ext.section_rotation` is a label field with `70/70` blocks carrying values of the form `"ARC-01 - ..."`, `"ARC-02 - ..."`, etc.
- `genre_ext.deal_type` carries inline labels such as `"새 trigger set 감지 (ARC-02 입장권)"` and `"산업 차원 공급망 재편 신호 감지 (ARC-04 입장권)"`
- `genre_ext.leverage_used[*]` is a list of short label-style strings, with `34` items carrying explicit `"Block N"` or `"ARC-NN"` markers (e.g. `"Block 9-10 방어 실적"`, `"ARC-01 손실선 증명 실적"`)

BI — narrow but explicit:

- `opponent_transition_plan[*].phase` carries `4` values of the form `"Phase 1: 무시→침묵"`, `"Phase 2: 경계→합리적 견제"`, `"Phase 3: 본격 대응→내부 정보 의심"`, `"Phase 4: 전략적 공존"` — `phase` is in the explicit forbidden list and the value should be split into a numeric `phase_no` plus a natural-language `phase_label`
- `npc_timeline[*].arc_presence[*]` carries `18` values of the form `"ARC-01"`, `"ARC-02"`, etc. — this is a label-list of arc identifiers; per the spirit of the metadata contract these should be normalized to numeric `arc_no`/`arc_id` form rather than left as `"ARC-NN"` strings in a human-readable list slot

### 5.3 `diegetic_meta_ref` (natural-language / prose fields with leaked meta wording)

TR — wide and prose-level (this is the dominant violation surface):

- `foreshadow[*]` (`28` hits) — narrator-voiced foreshadow lines such as `"...ARC-03 Block 49의 저울 장면으로 이어진다"`, `"...ARC-02 Block 17에서 갱신안 오류를 찍히는 장면의 복선이다"`
- `callback[*]` (`13` hits) — narrator-voiced callback lines such as `"Block 11 배석 → Block 13 서명 → Block 30 의결. ARC-01~02를 관통하는 권한 축 상승 완성"`
- `content.context` (`10` hits) — scene-facing prose such as `"Block 4에서 도진우가 사촌 형의 보고를 뒤집은 직후"` and the most acute case at `[69].content.context`: `"Block 1과 같은 건물, 같은 층, 같은 시간대..."` — this is exactly the meta-into-prose erosion the `meta-language-leak-context-handoff` policy was written to forbid
- `content.reward` (`8` hits), `content.event_villain` (`4` hits), `content.solution` (`2` hits) — reward / villain / solution paragraphs carrying `Block N` or `ARC-NN` references
- `power_shift.protagonist` (`3` hits), `power_shift.antagonist` (`2` hits) — short prose deltas such as `"Block 1의 말석 메모와 대칭되는 구도"` and `"ARC-02 마무리 블록"`
- `genre_ext.method` (`2` hits), `genre_ext.success_pattern` (`1` hit), `genre_ext.profit_loss` (`3` hits), `genre_ext.risk_level` (`1` hit) — short prose lines carrying meta references such as `"Block 1의 패턴을 반복하되..."` and `"(ARC-04 마무리 — 자본 변동 없음)"`
- `relationship_delta[*].before` / `[*].after` (`2` hits) — prose such as `"...Block 32 경고가 맞았음"`

BI — narrow:

- `arcs[0].exit_function` carries the prose line `"배석자가 된 도진우가 새로운 trigger set를 감지하며 ARC-02 입장권을 얻는다."` — this is the only true `diegetic_meta_ref` in the BI body
- `_schema_description` carries a minor administrative reference `"...Phase0/TR draft 동기화 산출물..."` — cosmetic, doc-level descriptor only, not consumed by stage prose; lowest cleanup priority

### 5.4 `blocked_by_pair_truth`

The prior survey's `TR incomplete vs BI ahead` truth blocker is, at the file-state level, no longer present:

- TR root list now has 70 populated blocks (`Block 1` through `Block 70`), all with non-empty `content.*` strings
- BI `_sync_manifest.tr_block_count` is now `70`, matching the live TR length
- BI's `capital_curve`, `defeat_blocks`, and `arcs` for late blocks (e.g. capital checkpoints at `Block 59` / `Block 68`, defeat anchors at `Block 63` / `Block 67`, fifth arc covering `Block 61-70`) now have a live TR backing instead of pointing into vacuum

This terminal therefore does not classify pair `10` as `blocked_by_pair_truth` for the purpose of this meta-wording survey, with two explicit caveats:

- this lane is read-only; it certifies file shape, not narrative truth, and it does not audit whether TR 58-70 was finished correctly (only that it exists and is populated)
- final certification of the prior `TR incomplete vs BI ahead` resolution remains Codex's responsibility in the merge step, including the spot-check anchors already listed in `docs/2026-04-06/10pair_tr_bi_consistency_bounded_survey.md`

If Codex's merge-step audit reverses that judgment and finds TR 58-70 truth still unstable, the route in §7 below downgrades automatically from `cleanup_now` to `tr_completion_first`.

## 6. Concrete Anchors (max 5)

1. `TR: blocks[*].genre_ext.section_rotation` — `70/70` blocks carry `"ARC-NN - ..."` style label values; saturated `label_meta_ref`, the largest single cleanup unit in the pair
2. `TR: blocks[69].content.context` — `"Block 1과 같은 건물, 같은 층, 같은 시간대..."`; the worst single `diegetic_meta_ref` in the pair, narrator pointing at the opening scene by `Block 1` instead of by scene description
3. `TR: blocks[*].foreshadow[*]` and `blocks[*].callback[*]` — `28` foreshadow + `13` callback prose lines carrying `"ARC-NN Block N"` cross-references; these prose fields should hold meaning while structural numbering moves to the existing `foreshadow_targets` / `callback_sources` companion fields
4. `BI: opponent_transition_plan[*].phase` — `4` values of the form `"Phase 1: 무시→침묵"`; `phase` is in the explicit forbidden list and should be split into `phase_no` + natural-language `phase_label`
5. `BI: npc_timeline[*].arc_presence[*]` — `18` `"ARC-NN"` string entries in a list slot; should be normalized to numeric `arc_no` form per the spirit of the structural-metadata contract

## 7. Final Severity

- `P2`

Reasoning:

- not `P0`: file exists, UTF-8 decode pass, JSON parse pass
- not `P1`: at the file-state level the prior `TR incomplete vs BI ahead` truth blocker is no longer visible (TR has 70 populated blocks; BI sync manifest matches), and the meta-wording problem is bounded to known field paths, not fused with a production-state collapse
- `P2` rather than `P3`: the leakage is structural and saturated (every `section_rotation` value, dozens of `foreshadow` / `callback` prose lines, and a narrator-level `Block 1` reference at the closing block), so this is a real cleanup target that should be scheduled, not a cosmetic note

## 8. Final Execution Route

- `cleanup_now`

Hard preconditions attached to this route (these belong to Codex at merge time, not to this terminal):

- Codex's merge-step verifies that the prior `TR incomplete vs BI ahead` truth blocker is genuinely resolved in the live pair (not just that the file shape changed)
- if that verification fails, this terminal's route automatically downgrades to `tr_completion_first` and the wording cleanup waits behind it
- the cleanup wave must respect the policy's separation rule: structural numbering moves into the allowed metadata fields (`block_id`, `arc_id`, `arc_no`, `phase_no`, `foreshadow_targets`, `callback_sources`, `evolution`), and the human-readable / label fields are rewritten as natural-language prose without `Block / ARC / Phase / Stage` tokens
- no `TR` and `BI` simultaneous mass-rewrite: per the revival ladder, `TR` leakage cleanup and `BI` leakage cleanup should be planned as two adjacent units, not as a single sweep

## 9. One-Line Minimal Next Step

Recommend Codex first re-verify TR 58-70 truth in the merge step, and if confirmed clean, schedule a bounded `BI label_meta_ref` patch (`opponent_transition_plan[*].phase` split + `npc_timeline[*].arc_presence[*]` normalization + `arcs[0].exit_function` prose rewrite) as the smallest cleanup unit before opening the much larger TR `section_rotation` / `foreshadow` / `callback` rewrite wave.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
