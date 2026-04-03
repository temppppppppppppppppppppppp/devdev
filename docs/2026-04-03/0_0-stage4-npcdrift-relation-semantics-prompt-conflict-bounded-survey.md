# 0_0 Stage4 NPC Relation-Semantics And Prompt-Conflict Bounded Survey

Date: 2026-04-03
Status: draft-bounded-post-run-evidence
Confidence: 96%
Canonical Path: `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-bounded-survey.md`
Evidence File: `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-evidence.json`
Order File: `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-bounded-survey-order.md`
Baseline Commit: `ecd58d57943a91ad5b946077eeacba224f49641a`
Mode: bounded post-run read-only survey
Prior Survey: `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`

---

## Coverage

### Runtime Evidence Read

| Source | Path | Read |
|--------|------|------|
| canary prep | `canary_…/logs/canary_prep.json` | full |
| canary episode_production | `canary_…/logs/episode_production.jsonl` | all 12 lines parsed |
| canary quality_metrics | `canary_…/logs/quality_metrics.jsonl` | full (5 REJECT entries) |
| canary ui_events | `canary_…/logs/session/ui_events.jsonl` | keyword-targeted (~320 lines) |
| canary decisions | `canary_…/logs/session/decisions.jsonl` | structure + key fields |
| canary llm_io | `canary_…/logs/session/llm_io.jsonl` | keyword-targeted |
| canary artifacts | `canary_…/logs/artifacts/stage4/ep_0002/` | 4 attempts, 7 txt files cataloged |
| source style_guide | `00_20260403/stage0_output/style_guide.json` | first 100 lines |
| source ep_0002 | `00_20260403/drafts/ep_0002.txt` | full (129 lines) |
| canary blueprint | `canary_…/plans/blueprints/blueprint_0002.txt` | first 60 lines |

### Code Surfaces Read

| Module | Key Finding |
|--------|-------------|
| `npc_drift_advisor.py` | full read (253 lines); `_extract_relation_tag_tokens` only handles `/`-separated compressed tags; plain `오해 대상` gets no semantic expansion |
| `stage4_interview_round.py` | keyword search: `_backfill_strong_advisory_fix_pack`, `_STRONG_ADVISORY_KEYS`, `resolve_style_dialogue_ratio_target`, dialogue PreCheck logic |
| `stage4_director_runtime.py` | strong_advisory_escalation gate chain (lines 2584–2642) |
| `project_support.py` | `resolve_style_dialogue_ratio_target` (lines 109–138): returns `None` for 0.0 |
| `pre_director_manuscript_checker.py` | `_resolve_dialogue_ratio_target` (lines 34–43): fallback to 0.30 when target is None |

### Document Context Read

| Document | Status |
|----------|--------|
| `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md` | full read |

---

## Findings

### Finding 1 (PRIMARY): `relation_to_protag: 오해 대상` is directionally ambiguous and systematically misread

**Severity: PRIMARY BLOCKER — 3 of 5 rounds rejected by this mechanism**

The canary world state assigns `relation_to_protag: 오해 대상` to all 4 NPCs (김 집사, 한정호, 한태민, 한태준).

`오해 대상` literally means "target of misunderstanding" but does not encode **who misunderstands whom**:

- **Interpretation A (NpcDrift LLM's reading):** protagonist misunderstands this NPC
- **Interpretation B (narratively correct):** this NPC misunderstands the protagonist

In a regressor/investment setup where the protagonist has 18 years of future knowledge, the protagonist correctly understands everyone while all NPCs misunderstand his transformation. Every manuscript correctly renders Interpretation B. The NpcDrift LLM consistently fires drift warnings claiming Interpretation A is violated.

Evidence from episode_production.jsonl round 0 warnings:

> `한태민 relation_to_protag: 기대='오해 대상' → 원고='주인공이 한태민을 오해하는 것이 아니라, 한태민이 주인공을 오해하며 무시함. 주인공은 오히려 그의 오해를 인지하고 역이용함.'`

This pattern repeats identically across all 5 rounds for all appearing NPCs.

**This is a different manifestation than the 04-02 survey finding.** The 04-02 survey identified compressed numeric tags (`집착100/오해-80`) as the problem. This canary has plain text `오해 대상` which bypasses the `_extract_relation_tag_tokens` semantic expansion path entirely (no `/` separator). Both manifestations share the same root: `relation_to_protag` lacks directionality metadata.

### Finding 2 (PRIMARY): Gate escalation path unchanged — PASS → PASS_WITH_FIX → REJECT via missing_fix_pack

The strong_advisory_escalation chain operates identically to the 04-02 survey finding:

1. Director gives PASS (scores 97–98)
2. `npc_drift` in `_STRONG_ADVISORY_KEYS` escalates to PASS_WITH_FIX
3. `_backfill_strong_advisory_fix_pack` cannot synthesize a fix_pack from zero
4. Gate downgrades to REJECT with basis `strong_advisory_escalation_non_local_fix`

This was the blocking gate in rounds 0, 3, and 4.

### Finding 3 (SECONDARY): `dialogue_ratio: 0.0` → fallback 30% → persistent false penalty

The style guide correctly extracts `dialogue_ratio: 0.0` from the source material (a pure narration investment novel with zero dialogue in ep2).

**The authority chain breaks at `resolve_style_dialogue_ratio_target`** (project_support.py:136): the guard `if 0.0 < value < 1.0` excludes exactly 0.0 and returns `None`.

**The fallback amplifies the break at `_resolve_dialogue_ratio_target`** (pre_director_manuscript_checker.py:36,43): when the target is `None`, it defaults to 0.30 (30%).

Result: every candidate in every round receives `[PreCheck] 대화 비율 심각 부족: 10-13% (스타일 목표 30%)` warnings.

This is NOT the primary rejection trigger — no round has `gate_basis: dialogue_ratio`. But it contributes:
- persistent warning noise in every candidate
- lowered confidence scores (values 0.0–0.8 across rounds)
- amplified Director rejection tendency in rounds where Director does reject

### Finding 4 (SECONDARY): FactLedger 1천만원 vs Blueprint/Source 200억

The source manuscript explicitly states the protagonist's assets total ~200억 (inherited land + trust + stocks + real estate). The blueprint correctly mirrors this.

But the FactLedger tracks `1천만원` as the protagonist's total assets — likely a Stage0/1 initialization issue where the starting cash was set to a small amount before the protagonist liquidates assets.

This caused:
- Round 1: `continuity_firewall` rejection (score 44)
- Preflight warning: `수치 정합성: 주인공의 총 자산이 1천만원(FactLedger)인데, Blueprint에서는 200억`

In later rounds, Director correctly selected candidates that adapted to 1천만원 (candidates C in rounds 3–4), and those rounds scored 97–98 PASS. But they were still overridden by the npc_drift gate.

The numeric issue is a **real contract violation** but it is secondary contamination that compounds the primary relation-semantics blocker, not an independent primary cause.

---

## Non-Issues

### Genre misbinding: RULED OUT

Investment genre binding is correct at source, prompt, and runtime. The blueprint, style guide, and manuscripts all correctly reflect the regressor/investment genre. No evidence of genre confusion.

### Opening replay / FlashbackVerifier: NOT DOMINANT

No FlashbackVerifier-triggered rejections in this 5-round canary. The dominant failure family has shifted entirely to relation-semantics and gate escalation.

### Stage2 or Stage3 structural failure: NOT INDICATED

The blueprint itself is well-formed. The 200억 value in the blueprint is faithful to the source material. The FactLedger discrepancy is a data-layer issue, not a Stage3 blueprint generation failure.

---

## Primary Owner Verdict

| Seam | Owner | Status |
|------|-------|--------|
| `relation_to_protag` directional ambiguity | Stage4 NpcDrift contract | **Primary** |
| fix_pack zero-to-local-fix synthesis gap | Stage4 gate chain | **Primary (same lane)** |
| `dialogue_ratio 0.0` fallback to 30% | Stage4 pre_director_manuscript_checker + project_support | **Secondary (new child lane)** |
| FactLedger 1천만원 vs source 200억 | Stage0/1 anchor initialization | **Secondary (investigation, not Stage4)** |

Owner: **Stage4 bounded child seam**, not Stage2/3 reactivation.

The evidence confirms the survey order's working hypothesis with one important revision: the primary seam is NOT compressed numeric tags (04-02 finding) but **plain text directional ambiguity** in `relation_to_protag`. The two manifestations share a common root and should be addressed in the same lane.

---

## Minimal Next Wave

### Lane 1 (expand existing): `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

The existing remediation lane from 04-02 should be expanded to cover:

1. **Directionality metadata for `relation_to_protag`**: encode who misunderstands whom (protag→NPC vs NPC→protag vs bidirectional) either as a stored field or as a semantic expansion hint in the NpcDrift prompt
2. **NpcDrift prompt guidance for non-compressed tags**: when `_extract_relation_tag_tokens` returns empty (plain text tag), provide explicit directionality guidance to the LLM instead of passing the raw ambiguous label
3. **fix_pack zero-to-local-fix synthesis**: unchanged from 04-02 — allow NpcDrift relation-tag advisories to synthesize a bounded local fix_pack when Director provides none
4. **Advisory threshold for directionally ambiguous tags**: consider downgrading plain-text `relation_to_protag` drift from strong advisory to advisory-only unless semantic contradiction is confirmed by additional evidence

### Lane 2 (new child): `0_0-stage4-dialogue-ratio-zero-fallback`

Bounded fix for the `dialogue_ratio: 0.0` → `None` → `0.30` fallback chain:

1. `resolve_style_dialogue_ratio_target` (project_support.py:136): change guard to `if 0.0 <= value < 1.0` to accept 0.0 as a valid author-intended target
2. `_resolve_dialogue_ratio_target` (pre_director_manuscript_checker.py): when target is explicitly 0.0, suppress `대화 비율 심각 부족` PreCheck warnings

### Lane 3 (investigation only): FactLedger anchor for 200억

The FactLedger tracking 1천만원 while the source/blueprint say 200억 needs investigation at the Stage0/1 level. This is NOT a Stage4 fix but may require a separate bounded survey.

---

## Open Questions

1. Should `relation_to_protag` store a structured directionality tuple (e.g., `{"label": "오해 대상", "direction": "NPC→protag", "description": "NPC가 주인공의 진정한 의도를 오해함"}`) instead of a flat string?

2. Is the `오해 대상` label itself semantically correct for this setup, or should it be replaced with a more precise label like `주인공을 오해하는 대상` or `일방적 오해 관계 (NPC→주인공)`?

3. Should the FactLedger 1천만원 issue be tracked as a separate Stage0/1 bounded lane, or is it a data artifact that will resolve when the NPC drift blocker is fixed (since later rounds already showed Director adapting to the FactLedger value)?

4. The 04-02 remediation SSOT may have been partially implemented. Before expanding that lane, verify which fixes from `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md` were actually applied to code vs. documented only.

---

## Stop

read-only bounded survey complete; no files mutated outside docs/2026-04-03 survey outputs

---

## 3-Pass Audit Record

**Pass 1. Structure and scope**
- Stayed bounded to the 8 required questions from the survey order
- Did not reopen Stage2/Stage3 realization
- Did not propose a new canary or code modification
- All findings separated into primary/secondary/ruled-out

**Pass 2. Evidence and consistency**
- All runtime claims verified against artifact payloads, not console rendering
- NpcDrift direction ambiguity confirmed across 3 rounds × 3 NPCs = 9 independent LLM judgments (consistent result)
- `dialogue_ratio` chain traced through 3 code files with line numbers
- FactLedger vs Blueprint discrepancy verified against both source manuscript and canary preflight
- No claim depends on a single log sentence without cross-verification

**Pass 3. Execution and readability**
- Survey answers all 8 required questions explicitly
- Expected finding shape from survey order confirmed with one revision (plain text vs compressed tag)
- Owner verdict is bounded Stage4, not Stage2/3 reopening
- Minimal next wave is explicit and scoped to 2 bounded lanes + 1 investigation
- Stop line present and compliant
