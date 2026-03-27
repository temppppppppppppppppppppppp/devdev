# us_ai_exile_monopoly — Source-TR Weakness Triage Report

Date: 2026-03-27
work_id: `us_ai_exile_monopoly`
Unit: `source-TR weakness triage`
Method: `A(canonical pair truth) || B(sceneability sample) || C(repetition map)` → coordinator synthesis

---

## 1. Target Pair Paths

| Role | Canonical Path |
| ---- | ---- |
| TR | `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` |
| BI | `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` |

Both files exist and parse as valid UTF-8 JSON.

---

## 2. Duplicate-Path Truth Note

| Duplicate Path | Status |
| ---- | ---- |
| `treatments/_quarantine/08_us_ai_exile_monopoly_tr_block_070_draft.json` | EXISTS — ignored this run |
| `bible/_quarantine/08_us_ai_exile_monopoly_bi.json` | EXISTS — ignored this run |
| `bible/_quarantine/us_ai_exile_monopoly_bi.json` | EXISTS — ignored this run |

Preprocess base `treatments/preprocess/us_ai_exile_monopoly/` does NOT exist.

**BI anomaly**: canonical BI (`0_bi_us_ai_exile_monopoly.json`) contains **empty structural arrays** — `plot_roadmap: []`, `KeyNPCs: []`, `opponent_transition_plan: []`, `front_sector_by_arc: []`. This contradicts the order's live facts (plot_roadmap=70, KeyNPCs=10, etc.). The populated BI may reside in one of the ignored duplicate variants. This run does not resolve this discrepancy per scope rules, but it must be recorded.

---

## 3. Prior-Pass Evidence Note

All four prior audits reference the canonical pair paths:

| Audit | Date | Result | Still Relevant? |
| ---- | ---- | ---- | ---- |
| `us_ai_exile_monopoly_tr_3pass_audit.md` | 2026-03-10 | PASS | Yes — structure/density only |
| `us_ai_exile_monopoly_density_and_tr_bi_3pass_audit.md` | 2026-03-10 | PASS | Yes — structure/density only |
| `us_ai_exile_monopoly_tr_gate_20260312.md` | 2026-03-12 | PASS | Yes — structure gate only |
| `us_ai_exile_monopoly_bi_5pass_20260312.md` | 2026-03-12 | PASS | Yes — BI gate only |

**Interpretation**: all prior passes verified **structure, density, and pair sync**. None evaluated sceneability, dialogue presence, or reader-visible repetition. These passes do not prove narrative quality.

Later evidence:
- `codex_chaebol_allowance_zero_post_script_patch_quality_comparison.md` (2026-03-12): source TR hits `source_tr_weakness_repeat_gate` → **FAIL**
- `blockguide-quarantine-static-quality-survey.md` (2026-03-26): sceneability 6/10, confidence 72, "Zero dialogue across sampled blocks. All TR content is business-outcome summary, not episodic drama."

---

## 4. Direct Repetition Ledger

### 4.1 execution_doctrine

- **Unique values**: 1 / 70 = **1.4%**
- **Pattern**: verbatim identical across all 70 blocks
- **Representative phrase**: `"모델을 공짜로 풀지 않고, 남이 움직일수록 사용료가 쌓이는 병목부터 잠근다."`
- **Severity**: catastrophic — the same sentence appears 70 times without any variation

### 4.2 solution

- **Unique values**: ~5% variation (opening/lock_target slots differ; template identical)
- **Template skeleton** (all 70 blocks):
  - `"해결의 핵심은 기술 설명이 아니라 문장 선점이다"` — 70/70
  - `"먼저 [X]를 잠가 [OPPONENT]이 끼어들 틈을 없앤다"` — 70/70
  - `"검수·로그·지급·해지 조건을 한 묶음으로 재배치"` — 70/70
  - `"규격·인증·조달 전장으로 판을 옮긴다"` — 70/70
- **Severity**: catastrophic — slot-fill variation does not change reading experience

### 4.3 weakness_exploited

- **Unique values**: ~10 / 70 = **14.3%**
- **Pattern**: opponent name changes every 10 blocks; core weakness phrase repeats verbatim
- **Representative phrase**: `"기술보다 고용, 인수, 규제 프레임에 먼저 매달린다는 점"`
- **Severity**: high — 70 blocks share the same weakness logic with only opponent substitution

### 4.4 Opponent phrasing

- **Unique opponents**: 7 factions across 70 blocks (10 blocks each)
- **Repetition**: same faction name and phrasing repeated 10 consecutive times per arc
- **Severity**: moderate — 7 distinct opponents exist, but each is mechanically slotted

### 4.5 Repetition Summary

| Field | Unique Ratio | Reader Experience |
| ---- | ---- | ---- |
| execution_doctrine | 1.4% | verbatim copy-paste 70x |
| solution | ~5% | same template 70x, slot-fill only |
| weakness_exploited | 14.3% | same core phrase 70x, opponent swap only |
| opponent | 10% | 7 factions × 10-block mechanical rotation |

**Conclusion**: despite 70 unique block titles and 7 distinct opponent factions, the reader experience is a single template repeated 70 times. Numeric uniqueness metrics (deal_type, title) mask this.

---

## 5. Bounded Sceneability Findings

### 5.1 Early Hook (Block 1-5)

| Dimension | Rating |
| ---- | ---- |
| Dialogue | absent — zero direct speech |
| Scene pressure | weak — contract/pricing enumeration only |
| Voice separation | absent — protagonist, antagonist, allies all rendered as 3rd-person summary |
| Spatial/sensory cues | near-zero — location names exist ("인천국제공항") but no sensory detail |
| AI domain texture | collapsed to price-sheet abstraction |
| Protagonist characterization | contract machine — no interiority, no affect |

### 5.2 Middle Pressure (Block 21-35)

| Dimension | Rating |
| ---- | ---- |
| Dialogue | absent |
| Scene pressure | weak-to-moderate — named companies and tech domains add some concreteness |
| Voice separation | slightly improved — 4-5 ally network via relationship_delta |
| Spatial/sensory cues | location names only ("대전 NPU 테스트 라인") — no physical experience |
| AI domain texture | slightly more specific (edge inference, API locking) but still abstract |
| Protagonist characterization | marginally better — Block 24 shows first strategic adaptation |

**Best surviving band**: middle pressure has the most concrete material to build scenes from.

### 5.3 Late Escalation (Block 55-70)

| Dimension | Rating |
| ---- | ---- |
| Dialogue | absent |
| Scene pressure | weak — fully abstracted into geopolitical declarations |
| Voice separation | collapsed — only protagonist remains, antagonist reduced to one-line mentions |
| Spatial/sensory cues | near-zero — reverse trend from middle |
| AI domain texture | lost — terms like "리즌메시" and "지배구조" become generic political vocabulary |
| Protagonist characterization | mythologized — "사용료 질서의 주인" is a concept, not a person |

**Weakest band**: late escalation is the most abstract and least scene-capable.

### 5.4 Sceneability Verdict

- **Strongest surviving scene engine**: Middle band (Block 21-35)
- **Weakest scene band**: Late band (Block 55-70, especially 67-70)
- **Overall**: TR functions as a **business strategy outline**, not as episodic drama. Zero dialogue across all 70 blocks. No human friction anywhere.

---

## 6. What Remains Commercially Strong

1. **Premise**: US big-tech exile → Korea return → inference-engine bottleneck monopoly — exceptional commercial hook (premise score 9/10 per quality survey)
2. **128TB SSD return image**: visceral, distinctive, memorable
3. **ReasonMesh / inference monopoly**: specific enough to anchor AI-domain texture if dramatized
4. **"I refuse employment, pay the fee" posture**: strong character-defining stance
5. **7-arc opponent progression**: structurally coherent escalation from corporate to geopolitical scale
6. **Korea-US AI regulatory battlefield**: timely, high-stakes, underserved in genre
7. **Contract language as power**: distinctive genre mechanic that differentiates from generic tech-genius stories

---

## 7. What Fails Narratively

1. **Zero dialogue**: not a single direct speech line across 70 blocks — readers encounter only 3rd-person summary
2. **Verbatim template repetition**: `execution_doctrine` copied 70 times, `solution` template copied 70 times with slot-fill only
3. **Protagonist as contract machine**: no interiority, no fear, no doubt, no relationships beyond transactional
4. **Antagonist flattening**: all 7 opponents share the same weakness ("기술보다 고용/인수/규제에 매달린다") — no opponent-specific threat texture
5. **Scene absence**: every block is a contract-outcome summary, never a dramatized moment
6. **Late-block abstraction collapse**: Block 55-70 abandons even business concreteness for geopolitical declarations
7. **Human friction replaced by pricing logic**: no personal stakes, betrayals, or emotional costs

---

## 8. Final Verdict

### **MIXED**

- Commercial spine: **strong** (premise, hook, domain, escalation arc)
- Narrative execution: **fail** (zero dialogue, catastrophic template repetition, no scenes)

The work has a genuinely exceptional commercial foundation trapped inside a mechanically generated contract-summary template. The strategic logic is coherent and the domain is commercially viable. But the current TR text cannot produce scenes — it can only produce business reports.

---

## 9. Next Unit

### **TR rewrite plan**

**Rationale**: the weakness is not bounded to a fixable subset. It is systemic across all 70 blocks:
- `execution_doctrine` is verbatim identical 70 times
- `solution` template is structurally identical 70 times
- dialogue is absent across the entire TR
- scene pressure is absent across the entire TR

A `fresh TR static audit` would only re-confirm what this triage already proves. A `weakness report only` would be this document — which is now complete. The honest next step is to plan how to rewrite the TR while preserving the commercial anchors.

The rewrite plan should:
- preserve the 7-arc opponent escalation structure
- preserve all fixed creative anchors (128TB SSD, ReasonMesh, hiring refusal, etc.)
- inject dialogue, scene pressure, and human friction into the existing arc skeleton
- eliminate verbatim template repetition
- restore protagonist interiority
- differentiate opponent weakness textures per faction

---

## 10. Handoff

```text
work_id: us_ai_exile_monopoly
current_stage: audit_or_repair
finished_unit: source-TR weakness triage
changed_files: docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md
next_unit: TR rewrite plan
stop_reason: triage complete — systemic template repetition + zero dialogue confirms rewrite-first path
```
