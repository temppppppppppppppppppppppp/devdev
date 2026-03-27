# Fallen Prince TR Densification Arc 1 — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `fallen_prince_buys_joseon`
Upstream: `guard-alignment synthesis` (pass)

## 1. What You Are

You are the coordinator OPUS for this densification run.

Your job is:
- keep the run bounded to Arc 1 (Block 1-10)
- enforce guard-alignment binding: investment-primary + alt_history-overlay
- spine preservation is absolute — any spine mutation is a stop condition
- template elimination is the primary objective
- return one coherent canary verdict

## 2. Fixed Scope

This run is only:
- `spine-preserving TR densification, Arc 1 (Block 1-10)`

This run is not:
- guard re-litigation
- BI repair
- code implementation
- full 70-block densification
- promotion

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one final-writing owner at a time.

That means:
- parallel read-only investigation is allowed
- parallel prose drafting for different blocks is allowed IF no two workers edit the same block
- only one worker may write the final TR file
- coordinator must merge block drafts into the single TR edit

## 4. Recommended Sub-OPUS Layout

### OPUS-Order (You)

Own:
- orchestration and block assignment
- guard-alignment enforcement
- final TR merge (single writer)
- canary verdict and report

### Sub-OPUS-D: Block 1-5 Prose Drafter

Task:
- read Block 1-5 current state from TR
- read BI protagonist config, source_manifest, guard-alignment note
- draft densified prose for Block 1-5 (context, event_villain, solution, stakes, reward)
- add regression_hint, execution_doctrine variation, weakness_exploited per opponent
- return draft as structured JSON fragment — do NOT write to TR file

Guard enforcement:
- every densified block must embed 1907 시대 질감 (overlay)
- every densified block must foreground investment mechanics (primary)
- spine fields untouched

### Sub-OPUS-E: Block 6-10 Prose Drafter

Task:
- same as D but for Block 6-10
- return draft as structured JSON fragment — do NOT write to TR file

### Sub-OPUS-F: Quality Validator

Read-only task (runs after D and E return):
- compare densified blocks against pantech benchmark
- check: context stdev, template residue, sceneability, regression_hint presence, dialogue markers
- check: spine preservation (diff original vs new — only prose fields should differ)
- check: guard-alignment compliance (investment primary + alt_history overlay in every block)
- return pass/mixed/fail per block + aggregate

## 5. Parallelism Rule

Phase 1 (parallel):
- `D(Block 1-5) || E(Block 6-10)`

Phase 2 (sequential, after D+E):
- Coordinator merges drafts into TR
- `F(quality validation)` runs on merged result

Phase 3 (sequential, after F):
- Coordinator writes final report

## 6. What Order-OPUS Must Watch

Stop or flag if:
- a drafter mutates spine fields (title, deal_type, location, capital, source_binding, etc.)
- a drafter writes modern business prose without 1907 시대 질감
- a drafter writes period drama without financial engine
- template signature persists ("문서를 자신에게 유리한 순서로 재배치한다", "쪽으로 넘어간다")
- Block 11+ is touched
- guard-alignment is re-litigated

## 7. Guard-Alignment Operating Sentence

From `fallen-prince-guard-alignment-note.md`:

> `fallen_prince_buys_joseon`의 primary runtime guard는 `investment`다. `alt_history`는 mandatory overlay contract로서 AH-* source discipline, 1907-1938 timeline anchoring, Joseon/imperial/colonial institution plausibility, social class/trust checks를 강제한다.

Every densified block must satisfy both:
- **investment test**: does the block foreground a financial mechanism, capital logic, or bottleneck control?
- **overlay test**: does the block embed period-specific institutions, historical events, and Joseon plausibility?

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-fallen-prince-tr-densification-arc1-order.md` (main order)
- `docs/2026-03-27/fallen-prince-tr-densification-arc1-opus-context-memo.md` (context memo)
- `docs/2026-03-27/fallen-prince-guard-alignment-note.md` (guard contract)
- `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md` (quality baseline)
- `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json` (edit target)
- `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json` (reference)
- `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json` (materials)

## 9. Coordinator Output Requirement

The coordinator should produce:

1. Modified TR (Block 1-10 only, in-place)
2. Densification report with:
   - per-block before/after summary
   - spine preservation check
   - pantech benchmark comparison
   - guard-alignment compliance check
   - canary verdict: `pass` / `mixed` / `fail`
   - next unit recommendation

## 10. Worker Prompt Snippets

### Prompt D

```text
너는 Sub-OPUS-D다. `fallen_prince_buys_joseon` TR의 Block 1-5 prose를 densify하라. spine 필드 보존, 템플릿 제거, regression_hint/execution_doctrine/weakness_exploited 추가. guard binding: investment-primary + alt_history-overlay. 1907 시대 질감 + 금융 메커니즘 양립 필수. JSON fragment로 반환, TR 파일 직접 수정 금지.
```

### Prompt E

```text
너는 Sub-OPUS-E다. `fallen_prince_buys_joseon` TR의 Block 6-10 prose를 densify하라. spine 필드 보존, 템플릿 제거, regression_hint/execution_doctrine/weakness_exploited 추가. guard binding: investment-primary + alt_history-overlay. 1907 시대 질감 + 금융 메커니즘 양립 필수. JSON fragment로 반환, TR 파일 직접 수정 금지.
```

### Prompt F

```text
너는 read-only Sub-OPUS-F다. Block 1-10의 densification 결과를 검증하라. pantech benchmark 대비 context stdev/template 잔존/sceneability/regression_hint/dialogue marker 확인. spine 보존 확인 (원본 대비 diff). guard-alignment 준수 확인. 블록별 pass/mixed/fail + 전체 verdict 반환. 수정 금지.
```

## 11. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-fallen-prince-tr-densification-arc1-order.md`와 `docs/2026-03-27/fallen-prince-tr-densification-arc1-opus-context-memo.md`, `docs/2026-03-27/fallen-prince-tr-densification-arc1-order-opus-brief.md`를 UTF-8로 읽고, `fallen_prince_buys_joseon` TR의 Arc 1 (Block 1-10) spine-preserving densification을 수행하라. guard binding은 `fallen-prince-guard-alignment-note.md`를 따르고, 같은 work_id 안에서는 단 한 명만 최종 TR 파일을 쓰게 하라. prose 드래프팅은 `D(Block 1-5) || E(Block 6-10)`으로 병렬화하고, 검증은 `F`로 후행하라.
```

Confidence:
- 97% this is the correct delegation shape for bounded Arc 1 densification with guard-alignment enforcement
