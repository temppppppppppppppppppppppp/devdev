# chaebol_ent_empire BI Repair Note

Date: 2026-03-27
Type: BI-only repair (TR untouched)
Source TR: `treatments/_quarantine/03_chaebol_ent_empire_tr_block_070_draft.json`
Output BI: `bible/_quarantine/03_chaebol_ent_empire_bi.json`
Prior TR audit: `docs/2026-03-27/chaebol-ent-empire-tr-static-quality-audit.md`

---

## 1. Critical Fix: 회귀자 → 비회귀

The old BI claimed `incarnation_type: "회귀자"` with `return_year: 2006`. The TR has `is_regressor: false` in all 70 blocks and starts in 2009. This was a copy-paste error from a template — the work is NOT a regression story. Fixed to `incarnation_type: "일반인"`, `is_regressor: false`, with explicit `regression_note`.

## 2. Repair Scope

| Section | Before | After |
|---------|--------|-------|
| `_genre` | `investment` | `entertainment_media` |
| `logline` | 회귀 재벌 3세 전섹터 공략 | 비회귀 몰락 재벌 3세 엔터 IP 기업 |
| `protagonist_faction` | 제국그룹 본사 | 세령컬처웍스 |
| `edge` | 미래 지식+협상 설계 | 스타 감지 — 배치 감각 |
| `incarnation_type` | 회귀자 | 일반인 (비회귀) |
| NPC descriptions | 12 identical (28 chars each) | 13 individualized (87-115 chars each) |
| `FinanceHUD.total_assets` | "초기 설정 필요" | "6800억" |
| `portfolio_history` | 0 entries | 11 milestones |
| Seeds | 10, all echo_count=0 | 12, all with echo_count/harvested_ep |
| `npc_timeline` | absent | 13 entries (NEW) |
| `foreshadow_map` | absent | 7 threads (NEW) |
| `opponent_transition_plan` | absent | 7 arcs (NEW) |
| `engine_evolution` | absent | 7 phases (NEW) |
| `special_ability` | absent | with evolution_arc (NEW) |
| `GenreRules` | 4 generic investment rules | 7 entertainment-specific rules |
| `plot_roadmap` | 70 blocks | 70 blocks (UNCHANGED — TR sync) |

## 3. What the New BI Adds Beyond TR Mirroring

1. **Protagonist engine evolution map**: 7-phase progression from talent discovery to industry standard-setting. This is not in the TR — the TR has per-block execution_doctrine but no synthesized arc.

2. **npc_timeline**: 13 characters with entry/exit blocks, turning points, and final states. The TR tracks relationship_delta per block but does not provide cross-block character arcs.

3. **foreshadow_map**: 7 threads with planted/payoff block pairs and status. The TR has per-block foreshadow arrays but no cross-block thread synthesis.

4. **opponent_transition_plan**: 7 arcs with antagonist goals, methods, and exploitable weaknesses per phase. The TR has per-block opponents but no arc-level strategic overview.

5. **portfolio_history**: 11 capital milestones including the Block 55 pyrrhic loss and Block 63 takeover crisis. The TR has per-block capital_before/after but no milestone synthesis.

6. **Seeds lifecycle**: 12 seeds with echo_blocks and harvest tracking. The old BI dumped TR foreshadow text with no lifecycle data.

## 4. P0 Contract Verification

| Check | Result |
|-------|--------|
| `plot_roadmap` length = 70 | PASS |
| `plot_roadmap` title sequence matches TR | PASS |
| `CoreIdentity.protagonist == FinanceHUD.name` | PASS (권태하) |
| `MetaInfo.title` valid Korean | PASS (쓰레기통 상속) |
| `total_assets` consistent with TR Block 70 capital_after | PASS (6800억) |
| UTF-8 clean | PASS |
| JSON parseable | PASS |

## 5. What Was NOT Changed

- `plot_roadmap`: kept as TR sync (per harness §2.1)
- `HistoricalEvents`: kept from old BI (TR-sourced content)
- File location: stays in `bible/_quarantine/` (quarantine preserved)

## 6. Remaining Limitations

- `portfolio_history` milestone capital for Block 63 is estimated ("약 3200억") — TR does not provide exact capital for that block
- Seeds `planted_ep` and `harvested_ep` are block-to-episode estimates (block × 5), not exact episode numbers
- NPC active_blocks ranges are based on TR relationship_delta appearances, not exhaustive presence tracking
- The BI still does not contain dialogue seeds or scene-level detail (TR limitation, not BI limitation)

---

## 7. Evaluation

**Did the new BI materially amplify the TR: yes**
- 5 new structural sections (npc_timeline, foreshadow_map, opponent_transition_plan, engine_evolution, portfolio_history)
- All NPC descriptions individualized
- FinanceHUD filled with real numbers
- Seeds given lifecycle tracking
- Critical 회귀자 misidentification corrected

**Is the pair now stronger than "usable but mixed": yes**
- The previous TR audit scored the TR at "mixed (strong end, 93% confidence)"
- With the BI now providing structural amplification (not just TR echo), the pair collectively crosses into genuinely usable territory
- The BI adds the cross-block synthesis that the TR lacks (character arcs, foreshadow threads, opponent strategy, capital milestones)

**Is the pair a top-tier revival candidate now: yes**
- Strongest TR in the quarantine cohort (no back-half collapse, unique execution_doctrines, coherent capital logic)
- BI now provides real structural amplification with 5 new sections
- Genre texture is genuine entertainment/media industry
- Only remaining weakness is zero dialogue (downstream concern)

---

**BI repair status: pass**

**TR rewrite needed: no**

**Should Codex prioritize this pair for revival canary next: yes**
