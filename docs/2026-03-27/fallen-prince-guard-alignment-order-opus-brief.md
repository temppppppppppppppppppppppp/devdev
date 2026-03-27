# Fallen Prince Guard-Alignment Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `fallen_prince_buys_joseon`

## 1. What You Are

You are not the single editing worker for this run.
You are the coordinator OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to one unit
- keep survey authority above guesswork
- separate primary runtime guard from overlay contract
- use parallelism only for read-only synthesis
- return one coherent next-step judgment

## 2. Fixed Scope

This run is only:

- `guard-alignment synthesis`

This run is not:

- code implementation
- hybrid guard engineering
- TR densification itself
- BI redesign
- active promotion

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one final-writing owner at a time.

That means:

- parallel read-only investigation is allowed
- parallel note extraction is allowed
- parallel edits to the same final note are not allowed
- only one worker may write the final alignment note

## 4. Recommended Sub-OPUS Layout

### OPUS-Order

Own:

- orchestration
- work partitioning
- final truth synthesis
- final next-unit judgment

Do not let multiple sub-OPUS workers edit the same final note.

### Sub-OPUS-A: Runtime Truth

Read-only task:

- verify that the live surveyed stack really leans `investment`
- verify preprocess primary profile
- verify live BI root genre and HUD
- verify that no direct artifact contradicts the survey verdict

Expected output:

- short runtime-truth ledger only

### Sub-OPUS-B: Overlay Contract Extractor

Read-only task:

- extract the `alt_history` duties that remain mandatory
- compress AH-* source-manifest, timeline, Joseon hierarchy, and historical-event anchoring into a flat checklist
- keep it to what later workers actually need

Expected output:

- short overlay-checklist only

### Sub-OPUS-C: Next-Unit Binder

Read-only task:

- read the TR static audit and existing Arc 1 densification order
- answer one question: after guard alignment, what is the single next worker unit
- if narrative continuation is still valid, bind it explicitly to `investment primary + alt_history overlay`

Expected output:

- one next-unit recommendation only

## 5. Parallelism Rule

Safe parallel start:

- Sub-OPUS-A may run immediately
- Sub-OPUS-B may run immediately
- Sub-OPUS-C may run immediately

So the structure is:

- `A || B || C`
- then coordinator synthesis

No worker should mutate the pair or write the final note except the designated final owner.

## 6. What Order-OPUS Must Watch

If any of these appear, stop the optimism and do not force a muddy hybrid story:

- a worker treats `alt_history` term richness as enough reason to flip the primary guard
- a worker ignores the survey and argues from raw preference
- a worker drops AH-* source discipline and Joseon plausibility because the runtime lane is investment
- a worker recommends `JoseonHUD` switch as if it were free
- a worker drifts into code-edit scope
- a worker treats the duplicate BI path as better authority than the surveyed live file

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- `alt_history_investment` hybrid identity
- `investment_market_profile` primary direction
- 1907-1938 historical timeline
- 황실 / 통감부 / 총독부 / 식민지 자산 인수 골격
- 병목 장악, 담보, 채권, 운임, 보험, 결제선 통제 엔진

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-fallen-prince-guard-alignment-order.md`
- `docs/2026-03-27/fallen-prince-guard-alignment-opus-context-memo.md`
- `docs/2026-03-27/fallen-prince-genre-guard-fit-survey.md`
- `docs/blockguide/alt_history_db_harness.md`
- `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`
- `treatments/preprocess/fallen_prince_buys_joseon/profile_lock.json`
- `treatments/preprocess/fallen_prince_buys_joseon/phase0_ready_snapshot.json`
- `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md`
- `docs/2026-03-27/opus-fallen-prince-tr-densification-arc1-order.md`
- `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
- `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`

## 9. Coordinator Output Requirement

The coordinator should produce exactly one final judgment:

- `pass`
- `mixed`
- `fail`

and exactly one next unit:

- `investment-primary arc1 densification`
- `overlay-contract note only`
- `hybrid-guard patch proposal`

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 read-only Sub-OPUS-A다. `fallen_prince_buys_joseon`의 runtime truth만 확인하라. preprocess profile, live BI `_genre`, live HUD root, survey verdict과의 충돌 여부만 짧은 ledger로 반환하라. 수정 금지.
```

### Prompt B

```text
너는 read-only Sub-OPUS-B다. `fallen_prince_buys_joseon`의 `alt_history` overlay contract만 추출하라. AH-* source discipline, 1907-1938 timeline anchoring, Joseon hierarchy/plausibility, historical-event binding만 flat checklist로 반환하라. 수정 금지.
```

### Prompt C

```text
너는 read-only Sub-OPUS-C다. `fallen_prince_buys_joseon`의 TR static audit와 기존 Arc 1 densification order를 읽고, guard alignment 이후의 next unit을 하나만 고르라. 질문은 하나다: 지금 바로 이어질 단일 worker unit은 무엇인가. 추천 1개만 반환하라. 수정 금지.
```

## 11. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-fallen-prince-guard-alignment-order.md`와 `docs/2026-03-27/fallen-prince-guard-alignment-opus-context-memo.md`, `docs/2026-03-27/fallen-prince-guard-alignment-order-opus-brief.md`를 UTF-8로 읽고, `fallen_prince_buys_joseon`에 대해 `guard-alignment synthesis` 1단위만 조율하라. 같은 work_id 안에서는 단 한 명만 최종 노트를 쓰게 하고, 읽기만 `A(runtime truth) || B(overlay contract) || C(next-unit binder)`로 병렬화하라.
```

Confidence:
- 98% this is the lowest-risk delegation shape to operationalize the survey without re-opening the whole `fallen_prince_buys_joseon` debate
