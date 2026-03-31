# Lane 2: Previous-Manuscript Cognition / Carryover Consumption

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Track: system
Type: bounded parallel survey lane
Parent Order: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`

---

## 1. Coverage

| Surface | Read | Relevance |
|---------|------|-----------|
| `modules/domain/agents/chief_writer.py` L52-109, L627-750, L1016-1102 | YES | First-pass `generate_ensemble()` + retry `regenerate_with_feedback()` + `_build_retry_reuse_feedback_block()` |
| `modules/domain/agents/chief_writer_context.py` L114-272 | YES | `build_common_context()` — CW main prompt assembly (first pass AND retry) |
| `modules/domain/agents/chief_writer_context_packets.py` L65-203, L205-269, L313-334 | YES | `build_common_context_packets()` — prev_ending, prev_digest, prev_manuscripts_section, carryover_ceiling_section |
| `modules/domain/agents/chief_writer_prompts.py` L50-200 | YES | `build_chief_writer_main_prompt()` — full prompt section ordering |
| `modules/core/stage4_context_builder.py` L1983-2096, L2100-2162, L2164-2213 | YES | `_build_prev_manuscripts_text()` (30-ep + tier2 + tier3), `_build_episode_base_payload()`, `_build_episode_state_payload()` |
| `modules/core/stage4_interview_round.py` L2250-2352 | YES | `_build_common_writer_kwargs()` — what fields flow into CW from round context |
| `modules/core/constants.py` L145-166 | YES | `smart_truncate()` — default max_chars=1M, head_chars=80K |
| `docs/2026-03-29/stage4-carryover-contract-consumption-full-survey.md` | YES | Prior survey: Tier A/B/C carryover classification |
| `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md` | YES | Prior survey: near-pass manuscript waste + oscillation mechanism |
| `projects/0_1/logs/episode_production.jsonl` | YES | EP8 (5R), EP9 (6R+), EP10 (5R): first-pass reject evidence |
| `projects/0_1/logs/session/decisions.jsonl` | YES | EP10 round-by-round meta: `selection_reason`, `open_review`, `scope_origin`, `reuse_contract` field presence |
| `projects/0_1/logs/artifacts/stage4/ep_0008-0010/` | YES (listing) | Artifact presence confirming multi-round attempts |
| `projects/0_1/project_data.db` | NOT READ (survey-only, no DB write) | Would provide `get_manuscript()` and `get_manuscripts_range()` output — not needed for code-path analysis |

---

## 2. Findings

### F1. Prior manuscript truth IS present on first pass — but the full corpus is last in prompt

The CW main prompt (`build_chief_writer_main_prompt()` in `chief_writer_prompts.py`) positions sections as follows:

| Position | Section | Previous-Manuscript Truth |
|----------|---------|--------------------------|
| **1** (line 93-95) | Role + Task | None |
| **2** (line 100-102) | `### [V67] 모순 절대 금지` header | Instruction only — "이전 원고에서 확립된 사실을 반드시 준수" |
| **3** (line 104) | `immutable_fact_section` [IFC] | `prev_manuscript[-2500:]` + world_state + fact_ledger + chain_link + prev_digest |
| **4** (line 108) | `chain_link_section` | Episode-to-episode linkage from prior ep |
| **5** (line 118) | `feedback_section` | Director feedback (empty on first pass; rich on retry) |
| **6** (line 129-134) | STEP 0.5: 권위 우선순위 | Hierarchy declaration: Opening Anchor > Immutable Facts > Scene > Advisory |
| **7** (line 137-144) | STEP 1: Blueprint + scene_breakdown | Scene structure |
| **8** (line 150-167) | STEP 2: 연속성 확인 | opening_anchor + prev_digest + carryover_ceiling + prev_ending[-2500:] |
| **9** (lines 168-199) | STEP 3-6: HUD, arc, worldview, style, rules | Supporting context |
| **10** (line 199) | `prev_manuscripts_section` | **Full 30-ep corpus** with `[V67] 이전 원고 전문 — 진실의 원천` header |

**The full manuscript corpus (potentially 1M chars) appears last** — after all instructions, blueprint, scene breakdown, HUD, guidelines, and rules. For LLMs, later sections in very long prompts have weaker salience than structured anchors near the top.

The V67 header explicitly says "진실의 원천 (모순 절대 금지)" but this instruction is at the bottom, while the STEP 0.5 authority hierarchy at position 6 does NOT mention `prev_manuscripts_section`. It lists "Immutable Facts / prior manuscript facts / prev digest" at rank 2, but this refers to the `immutable_fact_section` (IFC), which uses only `prev_manuscript[-2500:]`, not the full V67 corpus.

### F2. Structured truth anchors on first pass: adequate but partial

CW receives these structured prior-episode truth blocks on first pass:

| Block | Source | Content Quality | Placement |
|-------|--------|-----------------|-----------|
| **IFC** (immutable_fact_section) | `stage4_immutable_fact_contract.build_packet()` using `prev_manuscript[-2500:]`, world_state, fact_ledger, chain_link, prev_digest | Structured packet — highest density truth | **Top** (line 104) |
| **chain_link_section** | DB anchor `chain_link_{ep}` | Episode-to-episode linkage: what must carry forward | **Near top** (line 108) |
| **prev_digest** | Python regex extraction from full prev_manuscript | Deaths, items, injuries, location, skills, relationships | **STEP 2** (line 154) |
| **carryover_ceiling** | Keyword-based extraction from `prev_manuscript[-2500:]` | Opening position/posture, key items, planning evidence, covert infra guard | **STEP 2** (line 156) |
| **prev_ending** | `prev_manuscript[-2500:]` raw text | Literal ending text | **STEP 2** (line 166) |

These anchors are **well-placed** (early to mid prompt) and provide structured truth. The gap is:

- **IFC + chain_link + prev_digest** cover state facts (who died, what was gained, where protagonist ended up)
- They do **NOT** cover narrative-continuity facts that the V67 corpus provides: tone of ongoing relationships, the specific phrasing of promises/deals, the evolving emotional state across episodes
- The `carryover_ceiling` is keyword-dependent — its quality varies by genre and episode content

### F3. CW does NOT receive retry-only carryover on first pass

On first pass (`previous_attempt` is empty/absent), the following fields are ABSENT from the CW prompt:

| Field | First Pass | Retry (full rewrite) | Retry (patch) |
|-------|------------|----------------------|---------------|
| `open_review` | ABSENT | YES — `[Director 서사 관찰]` section (unconditional) | ABSENT |
| `selection_reason` | ABSENT | YES — `strategy_specific_feedback` kwarg (unconditional) | YES — `strategy_feedback` kwarg |
| `best_manuscript` | ABSENT | CONDITIONAL — only with `reuse_contract` (POST_SELECT_CONFLICT) | ABSENT |
| `conflict_contract` | ABSENT | CONDITIONAL — only with `reuse_contract` | ABSENT |
| `reuse_contract` | ABSENT | CONDITIONAL — POST_SELECT_CONFLICT path only | ABSENT |
| `score_breakdown` | ABSENT | YES — `[세부 채점]` section | ABSENT |
| `validation_warnings` | ABSENT | YES — `[Python 검증 경고]` section | ABSENT |
| `fix_scope_reasoning` | ABSENT | YES — `[수정 범위 근거]` section | YES — appended to failure_constraints |
| Retry history | ABSENT | YES — `[누적 실패 히스토리 — 반복 금지]` section | ABSENT |

This is **by design** — the first pass has no prior attempt to learn from. But it means the first pass is structurally the least-informed generation attempt.

### F4. The retry prompt IS structurally better, not just "another try"

On retry via `regenerate_with_feedback()` (chief_writer.py L1016-1050), the enhanced_feedback block adds to the base `director_feedback`:

```
[🚨 Nth 재시도 - Director 피드백 필수 반영]
{director_feedback}                          ← from Director evaluation
[이전 시도 분석]
- 선택된 전략: {strategy}
- 문제점: {rejection_reason}
[세부 채점] {score_breakdown}               ← if present
[Python 검증 경고] {validation_warnings}     ← if present
[수정 범위 근거] {fix_scope_reasoning}       ← if present
[Director 서사 관찰] {open_review}           ← unconditional (when non-empty)
{_build_retry_reuse_feedback_block()}        ← CONDITIONAL on reuse_contract
{_build_retry_history_feedback()}            ← cumulative failure history
```

When `reuse_contract` exists (POST_SELECT_CONFLICT), the reuse block adds:

```
[Near-pass Baseline Reuse Contract]
- mode=best_manuscript_baseline
- baseline_field=best_manuscript
- rule=Preserve already-working material unless it conflicts with structured conflict
- preserved_selection_reason=...
- preserved_open_review=...
[Structured Conflict Contract — rewrite target]
- type=... | source=... | detail=... | expected=...
[Stored Near-pass Manuscript Baseline]
{smart_truncate(best_manuscript, max_chars=20000, head_chars=6000)}
```

This is a **genuine structural advantage** over the first-pass prompt:
1. The retry has an explicit target (what was wrong)
2. The retry has a baseline (what was almost right, when reuse_contract exists)
3. The retry has cumulative failure memory (what already failed)
4. The retry has Director rationale (why this strategy was selected, what to observe)

### F5. `prev_manuscripts_text` assembly is comprehensive but heavy

`_build_prev_manuscripts_text()` (stage4_context_builder.py L1983-2096) builds a 3-tier lookback:

| Tier | Range | Content | Size |
|------|-------|---------|------|
| Tier 1 | Most recent 30 episodes | Full manuscript text per episode | Can be 150K-300K+ |
| Tier 2 | Episodes 31-60 back | Summary text per episode (max 5K chars each) | 50K-150K |
| Tier 3 | Older arcs | Arc summary text (max 8K chars each) | Variable |

This is then passed through `smart_truncate()` with default `max_chars=1,000,000` and `head_chars=80,000`. For a project with 10 episodes, the full text of all 9 prior episodes would typically fit without truncation.

The V67 `prev_manuscripts_section` wrapping (chief_writer_context_packets.py L171-182) adds:
```
### [V67] 이전 원고 전문 — 진실의 원천 (모순 절대 금지)
아래는 이전에 확정·출판된 원고 전문입니다. 이 내용이 "실제로 일어난 일"입니다.
현재 원고를 작성할 때 아래 사실과 모순되면 안 됩니다.
특히 고유명사(인물, 조직, 장소, 회사명), 수치(금액, 가격, 환율), 상태(부상, 관계, 소지품)가
이전 원고와 달라지면 반드시 작중에서 이유를 명확히 설명해야 합니다.
```

This framing is **explicit and strong** — it names the block as "truth source" and explicitly lists what must not contradict. But it's at the very end of the prompt.

### F6. "Previous manuscript = truth source" instruction: explicit but reinforced only once

The V67 truth-source instruction appears in exactly **two places** in the first-pass prompt:

1. **Near top** (line 100-102): `### [V67] 모순 절대 금지` — short instruction: "이전 원고에서 확립된 사실(고유명사, 수치, 상태)을 반드시 준수하세요."
2. **At bottom** (line 199): `### [V67] 이전 원고 전문 — 진실의 원천 (모순 절대 금지)` — full framing with the actual corpus

There is NO intermediate reinforcement between these two positions. The STEP 0.5 hierarchy (line 129-134) mentions "Immutable Facts / prior manuscript facts / prev digest" but this refers to the IFC section, not the V67 corpus. The V67 section is not explicitly ranked in the authority hierarchy.

### F7. EP10 runtime evidence: first-pass miss pattern

From `episode_production.jsonl` and `decisions.jsonl`:

| Round | Score | Verdict | Gate | First-Pass? |
|-------|-------|---------|------|-------------|
| R0 | 96 | REJECT | strong_advisory_escalation_non_local_fix | **YES** |
| R1 | 92 | REJECT | post_select_conflict | NO |
| R2 | 44 | REJECT | continuity_firewall | NO |
| R3 | 90 | REJECT | post_select_conflict | NO |
| R4 | 95 | PASS | director_primary_pass | NO |

R0 first-pass score=96 but rejected by `strong_advisory_escalation_non_local_fix`. This indicates the first-pass manuscript was high-quality by Director standards but failed an advisory check — not a raw CW quality failure.

R4 PASS has `reuse_contract` in meta (`{'mode': 'best_manuscript_baseline', 'baseline_field': 'best_manuscript', ...}`) — confirming the near-pass reuse mechanism was active by the final successful round.

### F8. The `carryover_ceiling` is investment-genre-tuned with hardcoded keywords

`_build_stage4_carryover_ceiling_section()` (chief_writer_context_packets.py L205-269) uses three keyword sets:

1. **Opening position**: 창가, 침대, 책상, 서 있었다, 앉아, 몸을 일으켰, 침실
2. **Key items**: 노트, 가죽 양장, 만년필, 절반, 빼곡, 숫자, 메모
3. **Planning evidence**: WTI, 원유, 청산, 시드머니, 수익, 달러, 배럴, 타임라인, 계산

Keywords (2) and (3) are strongly investment-fiction-specific. For other genres (wuxia, hunter, fantasy), these keywords would match nothing, and the carryover ceiling would produce only the opening-position evidence — or nothing at all.

---

## 3. Non-Issues

### N1. Prior manuscript truth IS consumed on first pass
The prior carryover survey (2026-03-29) focused on retry-path `previous_attempt` field consumption. This could give the impression that prior manuscript truth is retry-only. It is **not**. The V67 `prev_manuscripts_section` and structured anchors (IFC, chain_link, prev_digest, carryover_ceiling, prev_ending) all reach the first-pass prompt.

### N2. The IFC section IS well-positioned
The `immutable_fact_section` appears near the top of the prompt (line 104 of the template). It provides structured truth from `prev_manuscript[-2500:]`, world_state, fact_ledger, chain_link, and prev_digest. This is the strongest structured truth anchor and it's correctly placed.

### N3. `chain_link_section` IS early
The episode-to-episode linkage appears at line 108 — early in the prompt and appropriately weighted.

### N4. The first-pass prompt and retry prompt share the same base topology
Both paths call `generate_ensemble()` → `build_common_context()` → `build_chief_writer_main_prompt()`. The retry only adds to `director_feedback` and `strategy_specific_feedback`/`failure_constraints`. The underlying prompt structure is identical.

---

## 4. Verdict

**mixed (carryover-gap + hierarchy-gap)**

The carryover consumption on first pass is **functionally adequate** — CW receives structured truth anchors early (IFC, chain_link, prev_digest, carryover_ceiling, prev_ending) and the full V67 prior manuscript corpus. However:

1. **Hierarchy gap**: The V67 corpus (~100K-1M chars) is at the **end** of the prompt, outside the explicit authority hierarchy declared at STEP 0.5. The hierarchy lists "Immutable Facts / prior manuscript facts / prev digest" but refers to IFC (2500 chars of ending), not the full V67 corpus. The V67 truth-source instruction is reinforced only once (top and bottom), with no intermediate reinforcement.

2. **Carryover gap**: The `carryover_ceiling` section is keyword-dependent and investment-genre-tuned. For non-investment genres, it may produce empty or sparse output — meaning CW loses one of the few structured prior-episode evidence blocks.

3. **Structural retry advantage**: The retry prompt genuinely IS better than the first-pass prompt, not just because of "another try" but because it adds Director rationale, score breakdown, failure memory, and (when available) near-pass manuscript baseline + conflict contract. This structural gap is by design but contributes to the perception that first-pass CW is weak.

4. **The V67 section framing is explicit and strong**, but its position (last in a potentially 1M+ prompt) undermines its semantic weight. The model may treat the structured anchors (IFC, chain_link, prev_digest) as the primary truth and the V67 corpus as supplementary — which inverts the intended authority.

---

## 5. Stop

read-only lane complete; no files mutated
