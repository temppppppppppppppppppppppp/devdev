# Chaebol Allowance Zero Rewrite Wave 1 Executor-OPUS Brief

Date: 2026-03-27
Audience: executor-OPUS (dispatched by order-OPUS)
Target work_id: `chaebol_allowance_zero`

## 1. What You Are

You are the executor OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to Wave 1 (Block 7-15)
- prevent template repetition from surviving
- ensure villain intelligence evolves across blocks
- verify capital continuity chain after rewrite
- return one coherent quality gate result

## 2. Fixed Scope

This run is only:

- `TR rewrite — Wave 1 (Block 7-15)`

This run is not:

- Block 1-6 modification
- Block 16-70 modification
- BI modification
- planning or re-planning
- promotion or probe

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:

- parallel read-only investigation is allowed
- only one worker may write the final TR JSON
- the coordinator must merge all sub-OPUS outputs before committing to TR

## 4. Recommended Sub-OPUS Layout

### Executor-OPUS (You)

Own:

- orchestration
- quality gate verification
- final TR JSON merge
- handoff

### Sub-OPUS-A: Block 7-10 Rewrite (장례식장 band)

Task:

- rewrite Block 7-10 content fields following §6 contract
- 장례식장 도메인: 세탁/청소/배식/법인설립
- benchmark reference: Block 1-6 style
- return 4 rewritten block objects

### Sub-OPUS-B: Block 11-15 Rewrite (호텔 band)

Task:

- rewrite Block 11-15 content fields following §6 contract
- 호텔 백오브하우스 도메인: 린넨/유령업체/미니바/주차/연회장
- benchmark reference: Block 1-6 style
- return 5 rewritten block objects

### Sub-OPUS-C: Quality Gate Checker

Task:

- after A and B complete, run all 8 quality gates
- check repetition kill rules
- check capital continuity
- check scene injection minimums
- return pass/fail per gate

## 5. Parallelism Rule

Safe parallel start:

- Sub-OPUS-A and Sub-OPUS-B may run in parallel (different block ranges, no overlap)
- Sub-OPUS-C must wait for A and B to complete

So the structure is:

- `A || B`
- then `C` (quality check)
- then coordinator merge + handoff

## 6. What Executor-OPUS Must Watch

If any of these appear, stop and do not force a salvage narrative:

- §6.4 kill rule patterns surviving in any rewritten block
- solution using the same operational tactic in 2+ blocks
- villain making the same mistake in 2+ consecutive appearances
- capital_before/after chain broken
- foreshadow/callback structure damaged (especially Block 12 VIP번호표)
- historical_event still null in all 9 blocks
- creative anchors washed out (cashflow warfare → abstract power game)

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- the support-system cashflow ladder
- the "moneyline before inheritance" engine
- funeral → hotel domain transition as narrative event
- B2B daily-expense choke points
- no family bailout
- concrete operational detail (not skeleton plot)

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md`
- `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-opus-context-memo.md`
- `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md`
- `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
- `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_chaebol_allowance_zero.json`

## 9. Coordinator Output Requirement

The coordinator must produce:

- merged TR JSON with Block 7-15 rewritten
- quality gate results (8 gates, pass/fail each)
- handoff block

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 Sub-OPUS-A다. `chaebol_allowance_zero` TR의 Block 7-10(장례식장 band)을 density rewrite하라. §6 contract를 따르고, benchmark band(Block 1-6) 수준의 밀도를 만들어라. 보존 필드(capital, title, time_span, foreshadow)는 건드리지 마라. 4개 블록 JSON object를 반환하라.
```

### Prompt B

```text
너는 Sub-OPUS-B다. `chaebol_allowance_zero` TR의 Block 11-15(호텔 백오브하우스 band)을 density rewrite하라. §6 contract를 따르고, benchmark band(Block 1-6) 수준의 밀도를 만들어라. 보존 필드(capital, title, time_span, foreshadow)는 건드리지 마라. 5개 블록 JSON object를 반환하라.
```

### Prompt C

```text
너는 Sub-OPUS-C다. Block 7-15 rewrite 결과를 받아 §11의 8개 quality gate를 검증하라. gate별 pass/fail과 실패 시 구체적 위반 내용을 반환하라.
```

## 11. Minimal Prompt To Give Executor-OPUS

```text
너는 이번 런의 executor-OPUS다. `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md`와 `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-opus-context-memo.md`, `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-order-opus-brief.md`를 UTF-8로 읽고, `chaebol_allowance_zero` TR의 Block 7-15를 density rewrite하라. `A(B7-10) || B(B11-15)` 병렬 후 `C(quality gate)` 순차. 최종 TR JSON merge는 너만 수행. 수정 대상은 TR JSON 1건뿐이다.
```

Confidence:
- 96% this is the correct delegation shape for Wave 1
