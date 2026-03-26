# Blockguide Quarantine Static Quality Survey

Date: 2026-03-26
Type: narrative-truth static quality assessment
Scope: blockguide-family quarantine BI/TR pairs only
Method: consumability filter -> dedupe -> direct artifact read -> 7-axis scoring + skeleton detection

## 1. Consumability Filter Summary

Source: `python scripts/check_bi_tr_consumability.py --json`

| work_key | pair | tr | bi_standalone | blocks | notes |
| ---- | ---- | ---- | ---- | ---- | ---- |
| chaebol_allowance_zero | pass | pass | mixed | 70 | 3 duplicate BI files, dedupe to `02_bi_` |
| chaebol_ent_empire | pass | pass | mixed | 70 | |
| defense_defect_engineer | pass | pass | mixed | 70 | |
| fallen_prince_buys_joseon | pass | pass | mixed | 70 | 2 duplicate BI files |
| pantech_cyworld_reborn | pass | pass | pass | 70 | BI repaired 2026-03-26 |
| us_ai_exile_monopoly | pass | pass | mixed | 70 | 3 duplicate entries |
| empire_youngest_allsector | pass | pass | mixed | 70 | BI roadmap 70, TR actual 43 |

Excluded (pair=fail, blockguide family):

| work_key | reason |
| ---- | ---- |
| imf_kukje_heir | BI missing ProjectData, TR wrong format |
| chaebol_ent_empire_entertainment | orphan TR, no matching BI |
| defense_defect_engineer_defense_business | orphan TR, no matching BI |
| us_ai_exile_monopoly_ai_business | orphan TR, no matching BI |
| failed_future_ceo_intern | pair validation fail |
| wallstreet_great_depression | TR format error |

Excluded (wuxia family): wuxia_nakyang_merchant_daughter, wuxia_third_rate_sect_master

---

## 2. Static Quality Scorecard

7 salvage-ready pairs evaluated. Each scored 1-10 on 7 axes + skeleton detection.

### 2.1 chaebol_ent_empire

- **Files**: `03_chaebol_ent_empire_bi.json` / `03_chaebol_ent_empire_tr_block_070_draft.json`
- **Logline**: 쓰레기통 상속 — 몰락 재벌 3세가 엔터 자회사를 IP 라이프스타일 복합 기업으로 전환
- **Genre profile**: entertainment_media + investment_growth + chaebol_succession

| Axis | Score |
| ---- | ---- |
| Premise clarity | 9 |
| Protagonist distinctiveness | 8 |
| Growth resource clarity | 9 |
| Block progression density | 8 |
| Sceneability | 8 |
| Genre texture | 8 |
| BI amplification | 3 |

- **Skeleton signals**: BI auto-generated (`_schema_description` confirms), NPC descriptions identical boilerplate x12, all 70 blocks use `ability_name: '스타 감지'` without variation, Seeds all `echo_count: 0`, FinanceHUD `total_assets: '초기 설정 필요'`
- **Strongest**: Block narrative has real scene architecture (Block 7: spatial/talent blocking in hotel venue), capital tracking internally coherent (120억 -> 1280억 by Block 50), genuine tactical complexity in talent management decisions
- **Weakest**: BI is data scaffolding with zero creative expansion. "narrative is real, infrastructure is skeleton" split
- **Classification**: **usable-but-mixed** (confidence 78)

### 2.2 pantech_cyworld_reborn

- **Files**: `07_pantech_cyworld_reborn_bi.json` / `07_pantech_cyworld_reborn_tr_block_070_draft.json`
- **Logline**: 회귀 재벌 3세가 팬택 + 싸이월드를 한국판 애플+페이스북 결합체로 재건
- **Genre profile**: investment_market + tech_startup + chaebol_succession

| Axis | Score |
| ---- | ---- |
| Premise clarity | 9 |
| Protagonist distinctiveness | 8 |
| Growth resource clarity | 9 |
| Block progression density | 8 |
| Sceneability | 8 |
| Genre texture | 9 |

| BI amplification | 4 |

- **Skeleton signals**: BI explicitly auto-generated from TR (`_schema_description` states it), NPC descriptions identical boilerplate x12, FinanceHUD `total_assets/liquid_cash: '초기 설정 필요'`, Seeds all `echo_count: 0 / harvested_ep: null`
- **Strongest**: Highest genre texture in the batch. Specific investment mechanisms per block (전환사채, 부실자산인수, 조인트벤처, 우호적 M&A). Capital delta tracking with real business logic. Regression mechanic creates slip-up tension unique to this work
- **Weakest**: BI adds no narrative depth beyond reorganizing TR content. Relationship deltas transposed without synthesis
- **Classification**: **usable-but-mixed** (confidence 72)

### 2.3 empire_youngest_allsector

- **Files**: `0_bi_empire_youngest_allsector.json` / `empire_youngest_allsector_tr_block_070_draft.json`
- **Logline**: 2045->2025 회귀 재벌 막내, 신용카드 3천만에서 전섹터 동시 롤링으로 200조 제국
- **Genre profile**: business_growth + investment_market (전섹터 투자물)

| Axis | Score |
| ---- | ---- |
| Premise clarity | 8 |
| Protagonist distinctiveness | 9 |
| Growth resource clarity | 9 |
| Block progression density | 8 |
| Sceneability | 8 |
| Genre texture | 7 |
| BI amplification | 6 |

- **Skeleton signals**: TR only 43/70 blocks complete (61%), rear half thins toward summaries, "타자 POV" blocks patterned, stakeholder arcs mechanical (의심->감탄->충성)
- **Strongest**: Best character engine in batch — "4초간 눈을 감는다" moment (Block 5), "BTC 16만 1,200달러 터치 새벽 3시 47분" time-specificity, genuine decision moments with emotional weight
- **Weakest**: Only 43/70 blocks exist in TR. Blocks 35+ devolve into 1-2 line summaries. Sector depth relies on timing knowledge, not industry substance
- **Classification**: **usable-but-mixed** (confidence 72)
- **Special note**: Highest BI amplification (6) in batch. BI has real independent structure (OpponentTransitionPlan, NPC_Timeline). But TR incompleteness is a hard gap

### 2.4 us_ai_exile_monopoly

- **Files**: `0_bi_us_ai_exile_monopoly.json` / `us_ai_exile_monopoly_tr_block_070_draft.json`
- **Logline**: 미국 빅테크에서 추방된 한국인 AI 연구자가 추론 엔진 병목을 독점해 미국에 라이선스비를 내게 만든다
- **Genre profile**: tech_startup + investment_market (AI monopoly)

| Axis | Score |
| ---- | ---- |
| Premise clarity | 9 |
| Protagonist distinctiveness | 8 |
| Growth resource clarity | 9 |
| Block progression density | 7 |
| Sceneability | 6 |
| Genre texture | 8 |
| BI amplification | 6 |

- **Skeleton signals**: Every block follows identical template without variation, copy-paste antagonist weakness exploitation verbatim across 70 blocks, NPCs all "reconfigure around protagonist's advantage", placeholder capital gains (arithmetic only)
- **Strongest**: Exceptional commercial hook (AI bottleneck monopoly). 7-arc progression structurally coherent
- **Weakest**: Zero dialogue across sampled blocks. All TR content is business-outcome summary, not episodic drama. Mechanism replaces narrative
- **Classification**: **usable-but-mixed** (confidence 72)

### 2.5 chaebol_allowance_zero

- **Files**: `02_bi_chaebol_allowance_zero.json` / `chaebol_allowance_zero_tr_block_070_draft.json`
- **Logline**: 유언장으로 자금 차단된 회귀 재벌 3세가 생활 인프라 계약 독점으로 가문을 역전
- **Genre profile**: business_growth + investment_market (B2B 캐시플로우 장악물)

| Axis | Score |
| ---- | ---- |
| Premise clarity | 8 |
| Protagonist distinctiveness | 7 |
| Growth resource clarity | 9 |
| Block progression density | 6 |
| Sceneability | 6 |
| Genre texture | 7 |
| BI amplification | 5 |

- **Skeleton signals**: Solution phrasing template repeated 5-10 times ("X를 깨달아 Y를 다시 설계한다"), NPC arcs all follow identical 3-phase progression (의심->인정->의존), deal_type field averages ~10 chars (thin), regression_ext identical structure every block
- **Strongest**: Measurable capital tracking (0 -> 1320억), 42 business sectors planned, BI has complete opponent_transition_plan
- **Weakest**: ~245 char average context per block (situation summary, not scene). Zero specific dialogue or sensory detail
- **Classification**: **usable-but-mixed** (confidence 72)

### 2.6 defense_defect_engineer

- **Files**: `04_defense_defect_engineer_bi.json` / `04_defense_defect_engineer_tr_block_070_draft.json`
- **Logline**: 회귀 재벌 후계자가 항공기 구조결함을 협상 레버리지로 전환해 방산 제국 재건
- **Genre profile**: investment_market + tech_defense_procurement

| Axis | Score |
| ---- | ---- |
| Premise clarity | 9 |
| Protagonist distinctiveness | 8 |
| Growth resource clarity | 9 |
| Block progression density | 7 |
| Sceneability | 6 |
| Genre texture | 8 |
| BI amplification | 4 |

- **Skeleton signals**: Identical execution_doctrine repeated verbatim all 70 blocks, NPC descriptions identical boilerplate x13, FinanceHUD placeholder, every block follows identical JSON structure with zero variation, block titles algorithmically generated (병목/권한/카드 rotation)
- **Strongest**: Protagonist has genuine character engine (cold, structural thinker). Core mechanic (defect-as-leverage) is narratively distinctive
- **Weakest**: Zero dialogue, zero voice, zero human moments across all sampled blocks. Blocks are system diagrams, not drama. No real aeronautics/procurement detail beyond generic "structural defect" language
- **Classification**: **consumable-but-skeleton-likely** (confidence 78)

### 2.7 fallen_prince_buys_joseon

- **Files**: `05_bi_fallen_prince_buys_joseon.json` / `05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- **Logline**: 1936년 독살당한 조선 황족이 1907년으로 회귀해 유럽 금융으로 식민지 인프라를 사들인다
- **Genre profile**: alt_history_investment (국가규모 자산 인수)

| Axis | Score |
| ---- | ---- |
| Premise clarity | 9 |
| Protagonist distinctiveness | 8 |
| Growth resource clarity | 9 |
| Block progression density | 6 |
| Sceneability | 5 |
| Genre texture | 7 |
| BI amplification | 4 |

- **Skeleton signals**: `weakness_exploited` text identical verbatim across all 70 blocks ("실물과 권력을 보지만 장부 우선순위와 병목 결합이 만드는 지배력은 뒤늦게 이해한다"), identical execution_doctrine all 70 blocks, `source_binding` arrays empty in most blocks, placeholder `leverage_used` arrays
- **Strongest**: 70-block capital progression internally coherent (4억 -> 1조6400억). Real knowledge of 1907-1940 geopolitical finance
- **Weakest**: TR blocks have almost no narrative meat. Block 1 mentions "1936년 취리히에서 독살당한" but solution reduces to "금고부터 챙긴다". Arithmetic progression is real but narratively flat — Block 15 and Block 65 have same emotional intensity
- **Classification**: **consumable-but-skeleton-likely** (confidence 72)

---

## 3. Cross-Work Pattern Analysis

### 3.1 Dominant Weak Pattern: BI-as-thin-TR-echo

6 of 7 BIs are auto-generated from their TR (`_schema_description` confirms). Symptoms:
- NPC descriptions: identical boilerplate string copy-pasted 10-13 times
- Seeds: all `echo_count: 0`, `harvested_ep: null`
- FinanceHUD: `total_assets/liquid_cash: '초기 설정 필요'`
- `plot_roadmap`: direct TR block mirror, no structural synthesis

Only empire_youngest_allsector shows partial BI independence (OpponentTransitionPlan, NPC_Timeline with block-level turning points), but even there amplification is limited.

### 3.2 Secondary Pattern: Template Block Execution

Across all 7 works:
- Identical `weakness_exploited` or `execution_doctrine` copy-pasted across all 70 blocks
- solution/reward fields follow formulaic phrasing
- Zero or near-zero dialogue in TR blocks
- emotional_beat metadata exists but blocks lack actual emotional scene architecture

### 3.3 What Separates "usable" from "skeleton"

The divide is block-level narrative specificity:
- **Usable** works (ent_empire, pantech, empire_youngest) have blocks with spatial detail, named tactical decisions, measurable consequences
- **Skeleton** works (defense_defect, fallen_prince) reduce every block to mechanism summary: "protagonist applies leverage X, opponent loses position Y, capital changes Z"

---

## 4. Classification Summary

### Strong
(none)

### Usable But Mixed
| Rank | work_id | Conf | Best axis | Worst axis |
| ---- | ---- | ---- | ---- | ---- |
| 1 | chaebol_ent_empire | 78 | sceneability (8) | BI amplification (3) |
| 2 | pantech_cyworld_reborn | 72 | genre texture (9) | BI amplification (4) |
| 3 | empire_youngest_allsector | 72 | protagonist (9) | TR completeness (43/70) |
| 4 | us_ai_exile_monopoly | 72 | premise (9) | sceneability (6) |
| 5 | chaebol_allowance_zero | 72 | growth clarity (9) | block density (6) |

### Consumable But Skeleton-Likely
| work_id | Conf | Key skeleton signal |
| ---- | ---- | ---- |
| defense_defect_engineer | 78 | zero dialogue, system diagram blocks |
| fallen_prince_buys_joseon | 72 | identical weakness text all 70 blocks |

### Blocked / Not Worth Salvaging Now
| work_id | Reason |
| ---- | ---- |
| imf_kukje_heir | schema-fail (missing ProjectData, wrong TR format) |
| failed_future_ceo_intern | pair validation fail |
| wallstreet_great_depression | TR format error |
| chaebol_ent_empire_entertainment | orphan TR fragment |
| defense_defect_engineer_defense_business | orphan TR fragment |
| us_ai_exile_monopoly_ai_business | orphan TR fragment |

---

## 5. Ranked Shortlists

### Top 3 Works Worth Reviving First

1. **chaebol_ent_empire** — Highest evaluation confidence (78). Genuine scene architecture already present in blocks. Entertainment-IP premise has clear commercial differentiation. Repair scope is bounded: BI `block_no` + NPC enrichment + protagonist_config supplementation. TR needs no structural rework.

2. **pantech_cyworld_reborn** — BI already repaired (2026-03-26). Highest genre texture (9/10). Investment mechanisms per block are the most specific in the batch. Regression slip-up mechanic adds unique tension layer. Ready for production pipeline evaluation.

3. **empire_youngest_allsector** — Strongest character engine (protagonist distinctiveness 9/10, "4초간 눈을 감는다" moment). Highest BI amplification (6/10). But TR is only 43/70 blocks — requires 27 new blocks before pipeline entry. Prioritize if willing to invest in completion.

### Works to Ignore For Now

1. **defense_defect_engineer** — Skeleton despite a strong premise. Would require rewriting all 70 blocks from scratch to inject scene-level content. The mechanism (defect-as-leverage) is interesting but current blocks are system diagrams, not drama.

2. **fallen_prince_buys_joseon** — Same skeleton problem compounded by identical antagonist text across all 70 blocks. Historical finance architecture is impressive but non-functional as narrative source material.

3. **imf_kukje_heir** — Schema-level broken. No salvage path without fundamental reconstruction.

---

## 6. Evidence References

| work_id | BI file | TR file |
| ---- | ---- | ---- |
| chaebol_allowance_zero | `bible/_quarantine/02_bi_chaebol_allowance_zero.json` | `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` |
| chaebol_ent_empire | `bible/_quarantine/03_chaebol_ent_empire_bi.json` | `treatments/_quarantine/03_chaebol_ent_empire_tr_block_070_draft.json` |
| defense_defect_engineer | `bible/_quarantine/04_defense_defect_engineer_bi.json` | `treatments/_quarantine/04_defense_defect_engineer_tr_block_070_draft.json` |
| fallen_prince_buys_joseon | `bible/_quarantine/05_bi_fallen_prince_buys_joseon.json` | `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json` |
| pantech_cyworld_reborn | `bible/_quarantine/07_pantech_cyworld_reborn_bi.json` | `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json` |
| us_ai_exile_monopoly | `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` | `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` |
| empire_youngest_allsector | `bible/_quarantine/0_bi_empire_youngest_allsector.json` | `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` |

Consumability scan raw output: `docs/temp/consumability_scan_raw.json`

---

- Best salvage candidate: chaebol_ent_empire
- Dominant weak pattern: BI-auto-generated-thin-echo (6/7 BIs are TR mirrors with zero creative amplification)
- Should Codex open a repair/action SSOT now: no
