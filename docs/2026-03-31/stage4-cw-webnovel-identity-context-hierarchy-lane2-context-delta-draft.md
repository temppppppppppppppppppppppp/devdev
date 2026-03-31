# Lane 2: Context Hierarchy / Hard-vs-Soft Separation / First-Pass vs Retry Delta

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: Opus Terminal 2
Role: context hierarchy / hard-vs-soft separation / first-pass vs retry delta

## 1. Coverage

Surfaces read:

- `modules/core/stage4_context_builder.py` — full (2800+ lines)
- `modules/core/stage4_interview_round.py` — key sections: `_build_common_writer_kwargs` (L2282-2384), `_run_generation_phase` (L2451-2559), `run()` (L2720-2804), `_prepare_round_execution` (L2806-2867), `_normalize_director_gate_semantics` (L1978-2146)
- `modules/core/stage4_retry_runtime.py` — full (1250+ lines): `generate_candidates` (L333-445), `_resolve_retry_lane_routing` (L948-1061), `_run_inplace_retry_lane` (L1063-1124), `_run_patch_or_rewrite_retry_lane` (L1126-1191)
- `modules/core/stage4_reject_runtime.py` — full (200+ lines): `handle_reject`, `_build_reject_guidance_payload`
- `modules/domain/agents/chief_writer.py` — key sections: `generate_ensemble` (L627-769), `regenerate_with_feedback` (L1016-1102), `patch_with_feedback` (L1970-2032), `_build_regeneration_feedback` (L1052-1088)
- `modules/domain/agents/chief_writer_context.py` — full (600+ lines): `build_common_context` (L114-272), `_build_writer_core_section` (L494-523), `_build_immutable_fact_section` (L525-561)
- `modules/domain/agents/chief_writer_context_packets.py` — full (200+ lines): `build_common_context_packets`
- `modules/domain/agents/chief_writer_prompts.py` — full: `build_chief_writer_main_prompt` (L50-206)
- `config/prompts/chief_writer.yaml` — full (100 lines)
- `projects/0_2/logs/session/decisions.jsonl` — full (14 records): EP1 R0-R1, EP2 R0-R2

## 2. Findings

### F-1: The first-pass prompt is physically unordered relative to its declared authority hierarchy

The prompt declares an explicit authority hierarchy at `[STEP 0.5]`:

```
1. Opening Anchor
2. Immutable Facts / chain_link / prior manuscript full-text / prev digest / carryover ceiling
3. Structured scene breakdown
4. Advisory integrated scenario prose
```

However the physical prompt layout does NOT follow this order. The actual block sequence (from `build_chief_writer_main_prompt`, L93-206):

| Block Order | Content | Authority Class |
|---|---|---|
| 1 | `[Role] 웹소설 1타 작가` | Writer Identity |
| 2 | `[Task] 제N화 원고를 Blueprint 기반으로 집필하라` | Episode Mission |
| 3 | `핵심 철학` | Writer Identity |
| 4 | `[V67] 모순 절대 금지` (2 lines) | Anti-Pattern |
| 5 | `{immutable_fact_section}` (IFC) | **Hard Canon** |
| 6 | `[STEP 0: Read This Authority First]` (reading order declaration) | Meta |
| 7 | `{incarnation_context_section}` | Soft Guidance |
| 8 | `{chain_link_section}` | **Hard Canon** |
| 9 | `{ending_hook_section}` | Episode Mission |
| 10 | `{dna_instruction}` | Soft Guidance |
| 11 | `{purism_section}` | Anti-Pattern |
| 12 | `{world_origin_constraint_section}` | Soft Guidance |
| 13 | `{feedback_section}` (Director feedback) | **Retry-Only** |
| 14 | `{constraint_section}` (failure patterns) | **Retry-Only** |
| 15 | `{future_guard_section}` | Carryover |
| 16 | `{past_guard_section}` | Carryover |
| 17 | `{writer_core_section}` | **MIXED** (see F-2) |
| 18 | `{hud_anomaly_section}` | Advisory |
| 19 | `[STEP 0.5: 권위 우선순위]` | Meta (authority declaration) |
| 20 | `[STEP 1: Blueprint 분석]` + `{scene_breakdown}` | **Hard Canon** |
| 21 | `{integrated_scenario_advisory_section}` | Soft Guidance |
| 22 | `{emotional_beat_section}` | Soft Guidance |
| 23 | `[STEP 2: 연속성 확인]` + `{opening_anchor_section}` | **Hard Canon** |
| 24 | `{prev_digest}` | **Hard Canon** |
| 25 | `{carryover_ceiling_section}` | Carryover |
| 26 | `{prev_ending}` (직전 화 마지막 2500자) | **Hard Canon** |
| 27 | `[STEP 3]` + `{hud_report}` + `{high_density_hud_section}` | **Hard Canon** |
| 28 | `{hud_trend_section}` | Advisory |
| 29 | `{npc_equipment_section}` | Carryover |
| 30 | `{npc_frequency_section}` | Advisory |
| 31 | `[STEP 4]` Arc tactical | Soft Guidance |
| 32 | `[STEP 5]` World setting | Soft Guidance |
| 33 | `[STEP 6]` Style guide | Style Guidance |
| 34 | `{reference_excerpt_section}` | Reference |
| 35 | `{satisfaction_guide_section}` | Writing Instruction |
| 36 | `{common_rules}` (16 rules) | Writing Instruction |
| 37 | `{writing_guidelines}` | Writing Instruction |
| 38 | `{prev_manuscripts_section}` (30화 원고 전문) | **Hard Canon** |

Critical observation: The `prev_manuscripts_section` — potentially the single largest and most important hard canon block (up to 200K chars of prior episode full text) — is placed at the absolute bottom of the prompt, AFTER all writing guidelines and formatting rules. This is the worst possible position for hard canon that must override everything.

### F-2: `writer_core_section` is a mixed-authority blob

`_build_writer_core_section` (chief_writer_context.py L494-523) concatenates these into a single undifferentiated block:

1. character_voice guide — Carryover
2. world_state_section — **Hard Canon** (세계 상태 문서)
3. writing_directive — Episode Mission
4. reference_anchor_prompt — **Hard Canon** (retrieval anchors)
5. mandatory_context — **MIXED** (retrieval results + semantic query results + CP coverage)
6. anti_trope_prompt — Anti-Pattern
7. justification_prompt — Writing Instruction
8. reflexion_prompt — Writing Instruction

No separators, no authority tags, no hierarchy markers. A ~40K char block mixing hard canon with writing advice.

### F-3: First-pass vs retry delta matrix

| Dimension | First-Pass (R0) | Retry: Regenerate | Retry: Patch | Retry: InPlace |
|---|---|---|---|---|
| **Base context** (`common_writer_kwargs`) | Full | Full (identical dict) | Full (identical dict) | Minimal (ms + feedback + fix_pack) |
| `director_feedback` | Empty or weighted_injection only | Enhanced: rejection_reason + action_items + score_breakdown + validation_warnings + fix_scope_reasoning + open_review + reuse_contract + retry_history | Patch section + enhanced feedback | Director feedback (raw) |
| `failure_constraints` | Empty | Prior REJECT action_items | Prior REJECT action_items | N/A |
| **Strategy budget** | full (3 strategies) | reduced (2) or single (1) | single (previous strategy) | N/A (1 inplace) |
| `strategy_specific_feedback` | Empty | Prior selection_reason | Prior selection_reason | N/A |
| `rejected_strategy` | Empty | Strategy name to avoid | Strategy name to single | N/A |
| **Reuse contract** | N/A | Near-pass ms baseline + conflict_contract | N/A | Original ms preserved |
| **Conflict contract** | N/A | Structured conflict targets when post_select_conflict | N/A | fix_pack targets |
| **Advisory digest** | N/A | Accumulated advisory findings | Accumulated | N/A |
| **Total prompt size** | ~50-200K chars | ~50-200K + 5-20K enhanced | ~50-200K + patch | Minimal (5-10K) |

### F-4: Retry is NOT less contaminated — it is MORE contaminated but more narrowly directed

The retry path does NOT reduce context volume. It ADD on top of the identical base context:
- 5-20K of enhanced director feedback
- Failure constraints
- Reuse contract (may embed 20K+ near-pass manuscript baseline)
- Advisory digest

Retry succeeds despite heavier context because:
1. The additional context is narrowly structured (specific fix targets, explicit conflict contracts)
2. Explicit framing: `[🚨 N차 재시도 - Director 피드백 필수 반영]` + `⚠️ 위 피드백을 100% 반영하지 않으면 다시 REJECT됩니다`
3. Reuse contract preserves near-pass quality baseline
4. InPlace path is genuinely minimal (only ms + feedback + fix_pack)

### F-5: EP2 runtime evidence confirms hierarchy gap, not retry superiority

EP2 0_2 run timeline:
- R0: score 95, PASS_WITH_FIX → post_select_conflict escalated to REJECT (opening anchor '2006년 본가 저택 한시우의 방' missing from first paragraph)
- R1: score 95, PASS_WITH_FIX → post_select_conflict escalated to REJECT (same anchor still missing). FlashbackVerifier caught `직전 화에서 확인했던 수치 그대로였다` as continuity advisory.
- R2: score 94, PASS. The winning candidate correctly maintained prior-episode facts AND added the opening anchor.

Key observations:
1. R0 and R1 both produced near-perfect manuscripts (95 score) but failed the same hard-canon constraint (opening anchor). The first-pass prompt DID contain `opening_anchor_section` at position 23 (deep in the prompt, after STEP 0.5 declaration and Blueprint). CW likely deprioritized it.
2. R2 succeeded after accumulating: (a) explicit conflict_contract targeting the anchor, (b) reuse_contract preserving near-pass baseline, (c) 2 rounds of advisory digest.
3. The FlashbackVerifier advisory on R1 (`직전 화에서 확인했던 수치 그대로였다`) was correctly classified as a continuity issue — NOT a meta/briefing prose issue. This sentence violates truth (the numbers weren't confirmed in ep1), but is shaped like normal narrative recall, not like briefing prose.

### F-6: Hard canon vs soft guidance separation table

| Layer | Status | Blocks | Notes |
|---|---|---|---|
| **Writer Identity** | Weak (2 lines) | `[Role]` + `핵심 철학` | Only the role title. No explicit "you are a webnovel writer, NOT an analyst/summarizer" conditioning |
| **Hard Canon** | Scattered | IFC (pos 5), chain_link (pos 8), scene_breakdown (pos 20), opening_anchor (pos 23), prev_digest (pos 24), prev_ending (pos 26), hud_report (pos 27), prev_manuscripts (pos 38) | Not consolidated. Spans positions 5-38. Most critical block (prev_manuscripts) at bottom. |
| **Episode Mission** | Interleaved | Task (pos 2), ending_hook (pos 9), emotional_beat (pos 22) | Adequate but spread across prompt |
| **Carryover** | Adequate | future_guard (pos 15), past_guard (pos 16), npc_equipment (pos 29), carryover_ceiling (pos 25) | Reasonable placement |
| **Soft Guidance** | Scattered | incarnation (pos 7), dna (pos 10), world_origin (pos 12), advisory_scenario (pos 21), arc_tactical (pos 31), world_setting (pos 32) | Not clearly marked as lower-authority |
| **Anti-Pattern** | Present | V67 mokeep (pos 4), purism (pos 11), anti_trope (inside writer_core) | No explicit anti-meta or anti-briefing section |
| **Advisory** | Scattered | hud_anomaly (pos 18), hud_trend (pos 28), npc_frequency (pos 30) | Mixed with hard canon at similar positions |
| **Writing Instruction** | Bottom cluster | satisfaction (pos 35), common_rules (pos 36), guidelines (pos 37) | Good: at bottom. But prev_manuscripts (hard canon) follows after. |

## 3. Non-Issues

### N-1: The retry prompt template IS the same prompt template

Both first-pass and retry call `generate_ensemble()` which calls `build_common_context()` which calls `build_chief_writer_main_prompt()`. There is NO separate retry prompt template. The prompt structure is identical. Only the `director_feedback` and `failure_constraints` parameters differ.

### N-2: Hard canon content IS present in the first-pass prompt

The first-pass prompt does include:
- Immutable fact contract (IFC)
- Chain link section
- Opening anchor section
- Previous episode digest
- Previous episode ending (2500 chars)
- Previous manuscripts full text (up to 200K)
- HUD report
- World state summary

There is no missing hard canon content problem. The issue is positioning and hierarchy enforcement, not content absence.

### N-3: STEP 0 + STEP 0.5 authority declarations DO exist

The prompt includes both:
- `[STEP 0: Read This Authority First]` — declares reading order
- `[STEP 0.5: 권위 우선순위]` — declares authority ranking

These are well-intentioned hierarchy enforcement mechanisms. The gap is between the declaration and the physical layout.

## 4. Verdict

**hierarchy-gap**

The context hierarchy gap is real and measurable:

1. **Physical layout violates declared authority**: The prompt declares a 4-level authority hierarchy (Opening Anchor > Immutable Facts > Scene Breakdown > Advisory) but the physical block order scatters hard canon across 34 positions.

2. **`writer_core_section` is undifferentiated**: Hard canon (world_state, reference_anchor, mandatory_context) and soft guidance (anti_trope, justification, reflexion) are concatenated without authority markers.

3. **`prev_manuscripts_section` is at the wrong end**: The largest hard canon block (potentially 200K chars of prior episode text) is placed at position 38 of 38 — after all writing guidelines. For LLM attention, bottom position deprioritizes this block.

4. **Retry confirms the gap**: Retry succeeds not because it removes contamination but because it adds narrowly-structured, explicitly-framed repair instructions that function as a local hierarchy override. The first-pass prompt lacks this targeted authority framing.

5. **delta-confirms-gap**: The first-pass vs retry delta matrix shows that retry's advantage is entirely in explicit, actionable framing — exactly what the first-pass prompt lacks for its scattered hard canon blocks.

### Bounded remediation seam ranking (from this lane's perspective)

1. **Context hierarchy consolidation** (HIGH ROI) — Consolidate hard canon blocks early in the prompt, with explicit authority markers separating them from soft guidance and advisory.
2. **`prev_manuscripts_section` repositioning** (HIGH ROI) — Move from position 38 to immediately after the IFC block (position 6-7 area).
3. **`writer_core_section` decomposition** (MEDIUM ROI) — Split into hard-canon subsection (world_state, reference_anchor, mandatory_context) and soft-guidance subsection (anti_trope, justification, reflexion), with explicit authority labels.
4. **Advisory isolation** (LOW-MEDIUM ROI) — Group all advisory blocks (hud_anomaly, hud_trend, npc_frequency) into a single marked advisory section.

## 5. Stop

read-only lane complete; no files mutated
