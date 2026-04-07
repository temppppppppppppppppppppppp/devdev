# Pair 08 Production-Readiness Audit

Date: 2026-04-07
Pair: `08` (`pantech_cyworld_reborn`)
Verdict: **NOT production-ready.** Schema-clean and meta-clean, but fails 8 of 16 hard production gates plus 2 hard infrastructure blockers.
Owner: Claude (Terminal 8)

## 0. Method

This audit goes one layer below the structural / consistency checks done earlier today. Earlier audits proved the file *parses*, *mirrors*, and *contains no number-meta tokens in human-readable surfaces*. This one asks whether the pair can actually feed Stage 2/3/4 production runtime — i.e. whether the live audit pipeline (`scripts/audit_bi_5pass.py`, `tr_batch_harness.compute_treatment_metrics`, `modules/core/response_schemas.validate_*`) accepts the pair as a production input.

I ran the actual scripts. Findings below are not opinions — they are exit codes and metric values from the live audit code.

## 1. Hard Infrastructure Blockers

These crash the audit pipeline before it can even score the pair.

### B1. BI BOM crashes the audit loader (HARD)

**Symptom:** `scripts/audit_bi_5pass.py` calls `load_json()` which uses `path.read_text(encoding="utf-8")` (strict). Pair 08 BI was preserved with `utf-8-sig` BOM during the cleanup wave (per the survey's "soft hygiene flag" classification).

**Crash:**
```
json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)
  at scripts/audit_bi_5pass.py:95
```

**Impact:** Pair 08 BI cannot be passed through the official audit script at all. The execution-order survey treated BOM as "soft hygiene" and explicitly excluded pair 08 from the BOM-strip group (only pair 02 / 04 were scheduled). That call was wrong against the live audit script.

**Fix:** Strip the BI BOM. Pair 08 must be added to the BOM-strip set.

### B2. Phase0 schema mismatch with audit script (HARD)

**Symptom:** `audit_bi_5pass.py` expects phase0 in v1 schema:
```python
phase0["setting"]["starter_company"]["name"]
phase0["project"]["title_ko"]
phase0["protagonist"]["name"]
phase0["phase0_design"]["npc_timeline"]
```

Pair 08's `treatments/phase0/pantech_cyworld_reborn_phase0_design.json` is in a **different (v2-style) schema** with flat top-level keys: `arcs`, `company_state`, `protagonist` (only), `opponent_transition_plan`, `capital_curve`, `regression_ext`. There is **no `setting`, no `project`, no `phase0_design.npc_timeline`**.

**Crash on first phase0 field access:**
```
KeyError: 'setting'  at audit_bi_5pass.py:246
```

**Impact:** The audit can't cross-validate pair 08 against its phase0 at all. The `protagonist_match`, `title_match_phase0`, `starter_company_match`, and `npc_name_match == expected_npcs` checks are all gated on phase0 v1 fields that don't exist.

Cross-checked against the other 9 live phase0 files (`treatments/phase0/*.json`): every other pair has v1 `phase0_design.npc_timeline`. Pair 08 is **the only pair on the v2 phase0 schema**.

**Fix options (not for me to choose unilaterally):**
- Regenerate pair 08 phase0 in v1 schema, OR
- Migrate pair 08 phase0 to v1 manually, OR
- Update `audit_bi_5pass.py` to accept v2 phase0 (cross-cuts all pairs and is out of pair-08 scope).

This is a **structural mismatch** that no amount of pair-08-internal cleanup can fix.

## 2. Schema Validation Layer — PASS

Just so this isn't missed: at the JSON schema level, pair 08 is valid in both raw and canonical-normalized form.

| Check | TR | BI |
|---|---|---|
| `validate_treatment_structure` | ✅ | – |
| `validate_treatment_canonical_structure` | ✅ | – |
| `validate_bible_structure` | – | ✅ |
| `validate_bible_canonical_structure` | – | ✅ |
| Normalized canonical view | ✅ | ✅ |

The cleanup did not break the schemas. The problems are at the production-quality gate level, not the schema level.

## 3. Hard Production Gates — 8/16 FAIL

Ran via `scripts/tr_batch_harness.compute_treatment_metrics(tr)` directly (no phase0 needed for this layer).

| Gate | Result | Detail |
|---|---|---|
| `production_density_gate` | ❌ FAIL | top-level density gate fails |
| `critical_thin_blocks_zero` | ❌ FAIL | critical_thin_blocks = `[48]` |
| `thin_blocks_ratio_ok` | ❌ FAIL | 15 thin blocks total |
| `late_thin_blocks_zero` | ❌ FAIL | thin blocks in late half: `[54, 57, 65]` |
| `short_stakes_blocks_total_ok` | ❌ FAIL | short stakes blocks = `[23, 29, 44, 48, 50, 57, 68, 69]` (8 blocks) |
| `endgame_low_stakes_zero` | ❌ FAIL | endgame low-stakes blocks: `[68, 69]` (Block 68 + Block 69 are the public-card reveal and the final-vote pass — too short) |
| `unresolved_foreshadow_count_ok` | ❌ FAIL | 28 unresolved foreshadow lines |
| `section_rotation_present` | ❌ FAIL | **all 70 blocks** missing `section_rotation` field |
| `regressor_recognition_gap_ok` | ❌ FAIL | `max_recognition_gap_streak = 30` (way over the threshold) |
| `regressor_recognition_count_ok` | ✅ PASS | (recognition signals exist, just clustered) |
| `callback_ratio_ok` | ✅ PASS | |
| `late_blank_opponent_ok` | ✅ PASS | |
| `normalized_solution_stakes_repeat_ok` | ✅ PASS | |
| `diegetic_meta_ref_zero` | ✅ PASS | (cleanup wave succeeded) |
| `label_meta_ref_zero` | ✅ PASS | (cleanup wave succeeded) |
| `diegetic_block_ref_zero` | ✅ PASS | (cleanup wave succeeded) |

The 4 cleanup-related meta gates all PASS — the meta-language work was successful as a discrete unit. **The other 8 failures are pre-existing structural deficiencies in the TR draft that the cleanup wave was never meant to fix.**

## 4. NPC Continuity Drift — 46 mismatches

`compute_treatment_metrics` reports `npc_continuity_mismatch_count = 46`. Examples:

| Block | NPC | prev `after` | current `before` | Issue |
|---|---|---|---|---|
| 4 | 정민석 | `보조금 회의록 경유 채널` | `회의록 경유 채널` | "보조금" word dropped |
| 5 | 차우진 CFO | `실무 자료는 열어주되 숫자로 감시할 타깃` | `실무 자료 개방+감시자` | full paraphrase rewrite |
| 6 | 오세라 | `단말+계정 결합 각도의 첫 파트너` | `단말+계정 결합 첫 파트너` | "각도의" dropped |
| 7 | 싸이월드 경영진 | `단기 라이선싱 조건으로 테이블 개방` | `단기 라이선싱 테이블 개방` | "조건으로" dropped |
| 9 | 정민석 | `냉대 장면 실시간 보조자 — 신용 +1` | `회의록 경유 채널` | regressed to older state |
| 10 | 윤재문 회장 | `일정표와 손익을 들고 온 후계 후보, 시험해볼 카드` | `시험해볼 카드` | tail fragment only |
| 10 | 차우진 CFO | `특별감사 카드 꺼냄 — 본격 적대자` | `감사 카드 꺼냄` | shortened |
| 11 | 정민석 | `포렌식 경고 라인 — 신용 +1` | `포렌식 경고 라인` | "— 신용 +1" dropped |
| 13 | 박기태 | `공동 운영 구조 합의 — 신용 +2` | `공동 운영 파트너` | full rewrite |
| 15 | 박기태 | `현장 공동 대응자 — 신용 +1` | `현장 공동 대응자` | "— 신용 +1" dropped |

These are pre-existing in the original draft. The cleanup wave did NOT touch `relationship_delta` text (it only added two new entries — 윤재문 to Block 30 and 한유리 to Block 70 in the consistency-fix wave). The 46 mismatches are inherited drift between adjacent blocks where the writer chose a slightly different paraphrase for the same NPC's continuity state.

Audit gate threshold for this is `npc_continuity_mismatch_count == 0`. **At 46, the gate fails.**

## 5. Solution-Length Cluster Risk — 60/70 too compact

| Metric | Value | Threshold | Status |
|---|---|---|---|
| `avg_solution_chars` | 124.29 | ≥ 120 | barely passing |
| `one_sentence_like_solution_blocks` | **60** | ≤ 20 | **3× over limit** |

60 of 70 blocks have solutions that the audit classifies as single-sentence-like. This is a measurable narrative-density problem. The cleanup wave **probably contributed** by rewriting multi-block citation phrases (e.g. `Block 2의 보조금 회의록 + Block 4 이사진의 '현금흐름 증거' 요구...`) into more compact paraphrases (`김포 브리지 자금 협상 때 확보한 통신사 보조금 회의록과 ...`). The new versions are still substantive but the audit's sentence-counter is conservative.

This wasn't reported because `compute_treatment_metrics`'s gate `one_sentence_like_solution_blocks <= 20` is enforced inside `audit_bi_5pass.py`'s `build_source_tr_handoff_checks`, which never ran (B1/B2 crashed first).

## 6. Missing structural field for ALL 70 blocks

Every TR block is missing the `section_rotation` field. Other pairs have it (Investment fiction blockguide harness expects per-block natural-language section titles). Pair 08 has zero.

```
section_rotation_missing: 70 / 70
section_rotation_present (gate): False
```

This is an upstream omission from however pair 08 was generated, not something the cleanup wave introduced. But it means **even after BOM/phase0 fixes, pair 08 will still fail this gate** until 70 `section_rotation` strings are written.

## 7. Foreshadow / callback resolution

| Metric | Value | Status |
|---|---|---|
| `unresolved_foreshadow_count` | 28 | ❌ FAIL |
| `callback_ratio_ok` | True | ✅ PASS |

28 foreshadow lines have no callback that resolves them. The cleanup wave introduced `foreshadow_targets[]` arrays, but those are *intent* metadata — the actual resolution happens when a later block's `callback`/`callback_sources` references back. So this gap is pre-existing.

The cleanup did make this measurable for the first time (the new `foreshadow_targets`/`callback_sources` arrays make it possible to mechanically check whether every target has a corresponding source). Now that the linkage is structural, the audit can see what was always true: 28 dangling threads.

## 8. Endgame thin scenes — Blocks 68 & 69

The most reputationally costly thin blocks are at the very end:
- **Block 68** (`공개 카드 — 매집 경로와 배후 차명의 이사회 노출`) — climactic public reveal — short stakes
- **Block 69** (`최종 표결 통과 — 디지털 계열의 공식 분리`) — climactic vote — short stakes
- Block 48 also flagged as critical thin

These are the moments the audit gate `endgame_low_stakes_zero` is specifically designed to catch — endgame blocks with stakes lines that don't carry the dramatic weight expected for a 70-block payoff. Pair 08 has both of its biggest payoff blocks below threshold.

## 9. Recognition signal gap — 30-block streak

`max_recognition_gap_streak = 30`. The protagonist 윤도현 is a 회귀자 (regressor) and the audit watches for "recognition signals" — moments where surrounding characters notice his too-precise predictions. The gate fails when there's a long stretch with no recognition signal at all.

Pair 08's recognition signals are clustered around blocks 5, 29, 56 (the three slip-up blocks), leaving long stretches in between with no recognition pressure. The audit threshold is around 15-20 blocks; pair 08 has a 30-block streak.

**Implication:** Even though `regressor_recognition_count_ok = True` (3 signals total is enough), the *distribution* fails the gap gate. Either more recognition beats need to be added, or the slip-ups need to be repositioned.

## 10. What the cleanup wave actually accomplished

Just so this isn't lost: the cleanup wave was successful at what it was scoped to do.

- ✅ All 4 meta-language gates pass (`diegetic_meta_ref_zero`, `label_meta_ref_zero`, `diegetic_block_ref_zero`, plus the structural `*_targets`/`*_sources` carriers exist on every block where prose references a future/past block).
- ✅ Schema validation passes (raw + canonical, TR + BI).
- ✅ Cross-cut consistency fixes (Group A/B/C from earlier today) all landed and stay landed.
- ✅ TR ↔ BI plot_roadmap mirror is byte-equal.

The cleanup wave was **never scoped to fix narrative density, NPC continuity drift, section_rotation, recognition cadence, or solution length**. Those are pre-existing draft deficiencies.

## 11. Verdict

**Pair 08 cannot enter Stage 2/3/4 production runtime in its current state.**

There are two tiers of blockers:

**Tier 1 — Infrastructure (cannot even score):**
1. **B1 BOM**: BI must be written without BOM. Until then, `audit_bi_5pass.py` crashes on `load_json`.
2. **B2 Phase0 schema**: Pair 08 phase0 is the only one in v2 schema. Either regenerate in v1, migrate to v1, or upgrade the audit script. Without this, the audit cannot cross-validate phase0 → BI → TR at all, and the protagonist/title/starter_company/NPC-name handoff checks all fail by KeyError.

**Tier 2 — Production-quality (can score, but fail):**
3. `production_density_gate` fail
4. `critical_thin_blocks_zero` fail (Block 48)
5. `thin_blocks_ratio_ok` fail (15 thin blocks)
6. `late_thin_blocks_zero` fail (Blocks 54, 57, 65)
7. `short_stakes_blocks_total_ok` fail (8 blocks with short stakes)
8. `endgame_low_stakes_zero` fail (Blocks 68, 69 — the climax)
9. `unresolved_foreshadow_count_ok` fail (28 dangling foreshadows)
10. `section_rotation_present` fail (0/70 — entire field missing)
11. `regressor_recognition_gap_ok` fail (30-block silence streak)
12. `npc_continuity_mismatch_count == 0` fail (46 mismatches)
13. `one_sentence_like_solution_blocks ≤ 20` fail (60 blocks over limit)

Tier 2 problems are **pre-existing draft deficiencies** that pre-date the meta-cleanup wave. The cleanup wave did not introduce them; in one case (`one_sentence_like_solution_blocks`) the cleanup may have made it slightly worse by tightening prose, but the underlying problem already existed.

## 12. Recommended remediation order

If the goal is to make pair 08 actually production-ready, the work needs to happen in this order:

1. **B1 — Strip BI BOM.** One-line script. Add pair 08 to the BOM-strip set retroactively. Unblocks the audit loader.
2. **B2 — Resolve phase0 schema mismatch.** This is a project-wide decision (regenerate pair 08 phase0 in v1 schema vs. update the audit script to handle v2). Out of pair-08-local scope.
3. **Run the live audit script** end-to-end against the BOM-stripped BI + a v1-schema phase0, capture the full report.
4. **Fix `section_rotation` for all 70 blocks** — the structural omission. Each block needs a natural-language section title (e.g. block 1: "그룹 본체 봉쇄선을 뚫고 디지털 SPC를 세우는 출범기"). The 7 arc-name paraphrases I introduced during cleanup are reusable as the seed.
5. **NPC continuity normalization** — sweep the 46 `npc_continuity_mismatch_examples` and standardize each NPC's `before/after` paraphrase across blocks. This is mostly mechanical (pick one canonical "after" string and propagate).
6. **Recognition cadence rework** — add 2-4 recognition signals between blocks 30 and 56 to break the 30-block streak. This is creative work, not mechanical.
7. **Endgame stakes expansion** — Block 68 and Block 69 stakes need to be expanded from short to full-weight payoff stakes. Block 48 needs density restoration.
8. **Solution-length expansion** — 60 of 70 solutions need at least one more clause to escape the single-sentence classifier. This will fight against the meta-cleanup contract (which prefers terse, number-meta-free prose), so the rewrite has to add narrative content, not just fluff.
9. **Foreshadow resolution audit** — for each of the 28 unresolved foreshadows, either add a callback in a later block (preferred), or remove the foreshadow line.

**Estimated workload**: B1 is minutes. B2 is hours-to-days depending on the project-level decision. Steps 4-9 are a multi-day production-quality remediation pass.

## 13. Summary line

Pair 08 is **schema-clean, meta-clean, structurally consistent, and BOM-blocked, phase0-incompatible, density-failing, thin-blocked at climax, NPC-drifted, foreshadow-dangling, recognition-clustered, and section-rotation-missing**. The cleanup wave succeeded at its narrow scope. Production readiness requires a separate, larger remediation pass that this audit has now scoped.

---

audit performed by direct invocation of `scripts/audit_bi_5pass.py`, `scripts/tr_batch_harness.compute_treatment_metrics`, `modules/core/response_schemas.validate_*`, and `modules/core/stage0_handoff.normalize_*` against the live pair 08 files. No edits were made to the TR or BI files during this audit.
