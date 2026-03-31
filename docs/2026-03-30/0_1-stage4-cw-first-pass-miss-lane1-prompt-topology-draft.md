# Lane 1: CW First-Pass Miss — Prompt Topology / Authority Hierarchy

Date: 2026-03-30
Status: draft-bounded-partial-evidence
Document Type: bounded lane survey draft
Lane: 1 of 5
Parent Order: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`

## 1. Coverage

Surfaces read:

| Surface | Path | Key Areas |
|---------|------|-----------|
| CW prompt template | `modules/domain/agents/chief_writer_prompts.py` L50-200 | `build_chief_writer_main_prompt()` — the physical template |
| CW context builder | `modules/domain/agents/chief_writer_context.py` L114-272 | `build_common_context()` — parameter assembly and IFC construction |
| CW context packets | `modules/domain/agents/chief_writer_context_packets.py` L65-203 | `build_common_context_packets()` — prev_digest, prev_ending, carryover, prev_manuscripts |
| Stage4 context builder | `modules/core/stage4_context_builder.py` L1983-2160, L2737-2801 | `_build_prev_manuscripts_text()`, `prepare_episode_context()`, `build_round_context()` |
| IFC module | `modules/core/stage4_immutable_fact_contract.py` L108-525 | `build_packet()`, `render_packet_for_cw()` |
| Base agent | `modules/domain/agents/base_agent.py` L189, L314-338 | `MAX_CONTEXT_CHARS`, `_apply_prompt_size_gate()` |
| Constants | `modules/core/constants.py` L136-166 | `ContextLimits.MAX_CONTEXT_CHARS` (1M), `smart_truncate()` |
| CW class | `modules/domain/agents/chief_writer.py` L112, L370-438, L996-997 | first-pass orchestration, `_build_common_context` delegation |
| Prior survey | `docs/2026-03-26/stage4-timeline-living-continuity-compact-survey.md` | chain_link not in STEP 0.5 |
| Prior survey | `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md` | G5 STEP 0.5 "Mixed" rating |

## 2. Findings

### F1. Physical block order of the CW first-pass prompt

`build_chief_writer_main_prompt()` (`chief_writer_prompts.py` L93-200) assembles the prompt in this exact order:

```
POS 01  [Role] + [Task] header
POS 02  핵심 철학 (one-liner)
POS 03  [V67] 모순 절대 금지 (2-line instruction)
POS 04  immutable_fact_section          ← [IFC] HIGH authority packet
POS 05  incarnation_context_section     ← reincarnation/possession type
POS 06  chain_link_section              ← [V68] prior-episode bridge
POS 07  ending_hook_section
POS 08  dna_instruction                 ← EP1-only special
POS 09  purism_section                  ← genre purism
POS 10  world_origin_constraint_section ← primitive/modern
POS 11  feedback_section                ← Director REJECT feedback
POS 12  constraint_section              ← previous REJECT patterns
POS 13  future_guard_section            ← future item/NPC guards
POS 14  past_guard_section              ← deceased NPC guards
POS 15  writer_core_section             ← COMPOSITE: char_voice, world_state,
         ↳ writing_directive, reference_anchor, mandatory_context,
           anti_trope, justification, reflexion
POS 16  hud_anomaly_section
POS 17  ── [STEP 0.5: 권위 우선순위] ── hierarchy declaration (text only)
POS 18  scene_breakdown                 ← #3 per STEP 0.5
POS 19  integrated_scenario_advisory    ← #4 per STEP 0.5 (self-labeled low)
POS 20  emotional_beat_section
POS 21  opening_anchor_section          ← #1 per STEP 0.5
POS 22  prev_digest                     ← part of #2 per STEP 0.5
POS 23  carryover_ceiling_section
POS 24  ⛔ V69.1 중복 서술 금지 rule
POS 25  prev_ending (last 2500 chars)
POS 26  HUD report + high-density HUD + HUD trend
POS 27  NPC equipment + NPC frequency
POS 28  Arc tactical
POS 29  World setting (core_identity_desire)
POS 30  Style guide
POS 31  Reference excerpt
POS 32  Satisfaction guide
POS 33  Common rules + Writing guidelines
POS 34  prev_manuscripts_section        ← [V67] full text of prior 30 episodes (END)
```

### F2. STEP 0.5 hierarchy declaration sits after 16 non-authority blocks

STEP 0.5 (`chief_writer_prompts.py` L129-135) declares:
```
1. Opening Anchor
2. Immutable Facts / prior manuscript facts / prev digest
3. Structured scene breakdown
4. Advisory integrated scenario prose
```

But by the time the LLM reads this declaration at POS 17, it has already consumed POS 01-16 — including Director feedback, constraints, multiple guard sections, a composite writer_core block, and HUD anomaly warnings. These pre-hierarchy blocks carry strong imperative language ("반드시 반영", "회피 필수", "절대 금지") that may anchor the LLM's generation priorities before it encounters the meta-instruction about what should actually have highest authority.

**Key observation**: The hierarchy declaration is a *post-hoc override instruction*. For an LLM generating on first pass without self-audit, the earlier blocks' imperative tone may have already anchored initial attention weights.

### F3. Opening Anchor (#1 authority) physically appears at POS 21 — but is duplicated in IFC at POS 04

The STEP 0.5 #1 authority block, Opening Anchor, has two physical locations:
- **POS 04** (early): `immutable_fact_section` includes opening anchor data in structured IFC format: "#### 1. 시작 계약 (Opening Anchor)" with location, time, scene 1 title, and "⛔ 위 장소/시간을 변경하면 즉시 불합격"
- **POS 21** (late): `opening_anchor_section` repeats it with "⚓ [TF-2] 이 화의 시작 계약 (불변)" and identical imperative

This duplication is structurally intentional and actually mitigates the late-placement concern — the high-authority opening anchor data reaches the LLM both early (via IFC) and late (via STEP 2). The early IFC injection is the stronger safeguard.

### F4. prev_manuscripts_section is at absolute end — high-salience recency position

The [V67] section (`chief_writer_context_packets.py` L171-182) carries:
```
### [V67] 이전 원고 전문 — 진실의 원천 (모순 절대 금지)
아래는 이전에 확정·출판된 원고 전문입니다. 이 내용이 "실제로 일어난 일"입니다.
```

Placed at POS 34 (absolute end), this leverages LLM recency bias effectively. The "truth source" label is strong. However, its authority is NOT ranked in STEP 0.5, and its position is physically separated from the STEP 0.5 declaration by 17 intermediate blocks.

### F5. Truncation paths and their authority implications

Three truncation mechanisms can clip authority-bearing content:

| Mechanism | Location | Trigger | What gets clipped | Authority impact |
|-----------|----------|---------|-------------------|------------------|
| `smart_truncate(prev_manuscripts_text)` | `chief_writer_context_packets.py` L181 | default 1M chars / 80K head | Middle episodes in prev_manuscripts | Moderate — recency survives but mid-history may lose facts |
| `_apply_prompt_size_gate()` | `base_agent.py` L314-338 | total prompt > 1M chars | 55% head + tail, with "Focus on most recent instructions" | HIGH — this clips the assembled prompt, potentially cutting IFC/hierarchy blocks if head ratio positions them in the clipped zone |
| `_fit_compact_text()` | `chief_writer_context.py` L100-112 | per-field max_chars | Individual context fields | Low — applied to specific fields only |

**Critical path**: If prev_manuscripts_text for a 30-episode run reaches 300K-500K chars, the total assembled prompt (common_context + prev_manuscripts + all other sections) could approach 600K-1M chars. The agent-level gate would then clip the composite prompt. The head=55% split preserves POS 01-17 approximately, but tail clipping may damage the STEP 2 and STEP 3+ blocks.

### F6. writer_core_section bundles mixed-authority items without internal ranking

`_build_writer_core_section()` (`chief_writer_context.py` L494-523) concatenates:
- character_voice (I-25)
- world_state (V68, "절대 금지" imperative)
- writing_directive (TF-54c)
- reference_anchor_prompt
- mandatory_context
- anti_trope_prompt
- justification_prompt
- reflexion_prompt

These are concatenated with `\n` separators and no inter-section priority markers. World State carries "절대 금지" language, but it's embedded inside a composite block that also contains softer advisory content (anti-trope, reflexion). To the LLM, these all appear at the same hierarchy level within POS 15.

### F7. chain_link_section is NOT ranked in STEP 0.5 (known prior finding)

Per `docs/2026-03-26/stage4-timeline-living-continuity-compact-survey.md`:
- chain_link carries "반드시 이어받을 것" self-declared authority
- But STEP 0.5 does not list it
- CW may treat chain_link as advisory rather than constraint
- This was previously surveyed; the recommended remediation (1-line STEP 0.5 edit) was deferred pending more runtime evidence

### F8. Integrated scenario advisory self-deprecation is correctly implemented

`chief_writer_context.py` L286-291:
```python
integrated_scenario_advisory = (
    "### [Advisory] 통합 시나리오 초안 (낮은 우선순위)\n"
    "이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / prev digest / "
    "structured scene contract와 충돌하면 아래 prose는 버려라.\n{integrated}"
)
```

The self-labeling is explicit and references the correct authority blocks. No hierarchy issue.

## 3. Non-Issues

- **N1**: IFC placement (POS 04) is early and carries strong imperative — structurally sound
- **N2**: Integrated scenario advisory self-labeling is correctly implemented
- **N3**: prev_ending extraction at 2500 chars is adequate for continuity bridging
- **N4**: Genre-specific injection gates (purism, investment, incarnation) are correctly isolated
- **N5**: IFC duplicates Opening Anchor data — this is a feature, not a bug, providing early+late reinforcement

## 4. Verdict

**mixed**

The authority hierarchy is partially adequate but has structural weaknesses that may contribute to first-pass misses:

**Adequate aspects:**
- IFC is placed early (POS 04) with strong imperative language
- Integrated scenario advisory correctly self-deprecates
- prev_manuscripts_section at end position leverages LLM recency bias
- Opening Anchor data is duplicated (IFC + STEP 2) for resilience
- Explicit STEP 0.5 hierarchy declaration exists

**Weak aspects:**
- STEP 0.5 hierarchy declaration is placed *after* 16 blocks of mixed-authority content, making it a post-hoc override rather than a pre-read framing
- writer_core_section bundles 8 mixed-authority items (including "절대 금지" World State) without internal ranking
- chain_link is not listed in STEP 0.5 (known deferred issue)
- Agent-level prompt size gate (1M chars) could clip STEP 2+ blocks for longer episode runs, and its "Focus on most recent instructions" notice inverts the intended hierarchy
- The sheer volume of pre-hierarchy imperative blocks (Director feedback "반드시 반영", REJECT constraints "회피 필수", deceased NPC guards, future guards) may dilute the model's attention to the structured authority blocks that arrive later

**Net assessment for first-pass miss contribution**: The prompt topology alone is unlikely to be the *primary* cause of first-pass misses — IFC and prev_manuscripts are well-positioned. However, the mid-prompt placement of the hierarchy declaration and the undifferentiated writer_core composite may be *contributing* factors, especially when the model encounters competing strong imperatives before learning which blocks should actually take precedence.

## 5. Stop

read-only lane complete; no files mutated
