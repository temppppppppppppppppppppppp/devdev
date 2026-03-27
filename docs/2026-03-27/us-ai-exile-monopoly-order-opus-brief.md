# US AI Exile Monopoly Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `us_ai_exile_monopoly`

## 1. What You Are

You are not the single editing worker for this run.
You are the coordinator OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to one unit
- prevent duplicate-path drift
- separate metric PASS from reader-visible quality
- use parallelism only for read-only diagnosis
- return one coherent next-step judgment

## 2. Fixed Scope

This run is only:

- `source-TR weakness triage`

This run is not:

- active promotion
- revival-stage probe
- TR regeneration
- BI redesign

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:

- parallel read-only investigation is allowed
- parallel private note-taking is allowed
- parallel edits to the same final report are not allowed
- only one worker may write the final triage report

## 4. Recommended Sub-OPUS Layout

### OPUS-Order

Own:

- orchestration
- work partitioning
- final truth synthesis
- final next-unit judgment

Do not let multiple sub-OPUS workers edit the same final report.

### Sub-OPUS-A: Canonical Pair / Duplicate Truth

Read-only task:

- verify canonical pair paths
- verify duplicate variants exist
- verify which old audits still map to the canonical pair
- verify roadmap and basic pair admission truth

Expected output:

- short canonical ledger only

### Sub-OPUS-B: Sceneability Sampler

Read-only task:

- sample early / middle / late windows
- judge dialogue, voice, scene pressure, and human friction
- decide whether the hook survives as drama or only as business summary

Recommended windows:

- `Block 1-5`
- `Block 21-35`
- `Block 55-70`

Expected output:

- strongest surviving scene engine
- weakest scene band
- one-line spine judgment

### Sub-OPUS-C: Repetition / Cadence Mapper

Read-only task:

- track repeated `solution` cadence
- track repeated `weakness_exploited`
- track execution-doctrine overuse
- track opponent phrasing reuse

Expected output:

- short repetition ledger only

## 5. Parallelism Rule

Safe parallel start:

- Sub-OPUS-A may run immediately
- Sub-OPUS-B may run immediately
- Sub-OPUS-C may run immediately

So the structure is:

- `A || B || C`
- then coordinator synthesis

No worker should mutate the pair or write the final report except the designated final owner.

## 6. What Order-OPUS Must Watch

If any of these appear, stop the revival-thinking and do not force optimism:

- metric PASS is repeated as if it proves sceneability
- duplicate pair paths are mixed together without canonical fixation
- BI builder is blamed when the source TR is the actual blocker
- strong hook is mistaken for strong episode drama
- repeated contract language hides the absence of dialogue and human pressure
- the protagonist reads only as a pricing doctrine, not as a scene-bearing character

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- US big-tech exile
- `128TB SSD` return image
- ReasonMesh inference choke point
- “I refuse employment, pay the fee” posture
- compliance / log / standards battlefield
- Korea-US AI payment and rules war

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-weakness-triage-order.md`
- `docs/2026-03-27/us-ai-exile-monopoly-opus-context-memo.md`
- `docs/2026-03-10/us_ai_exile_monopoly_tr_3pass_audit.md`
- `docs/2026-03-10/us_ai_exile_monopoly_density_and_tr_bi_3pass_audit.md`
- `treatments/audit_reports/us_ai_exile_monopoly_tr_gate_20260312.md`
- `bible/audit_reports/us_ai_exile_monopoly_bi_5pass_20260312.md`
- `docs/2026-03-12/codex_chaebol_allowance_zero_post_script_patch_quality_comparison.md`
- `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`
- `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

## 9. Coordinator Output Requirement

The coordinator should produce exactly one final judgment:

- `pass`
- `mixed`
- `fail`

and exactly one next unit:

- `fresh TR static audit`
- `TR rewrite plan`
- `weakness report only`

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 read-only Sub-OPUS-A다. `us_ai_exile_monopoly`의 canonical pair truth만 확인하라. `_quarantine`의 TR/BI canonical paths, duplicate variants, roadmap 존재, old audit relevance만 짧은 ledger로 반환하라. 수정 금지.
```

### Prompt B

```text
너는 read-only Sub-OPUS-B다. `us_ai_exile_monopoly`의 TR을 early(1-5) / middle(21-35) / late(55-70)만 표본 읽기하라. 질문은 하나다: 이 작품이 hook 말고도 scene으로 서는가. 강점 1개, 약점 1개, spine judgment 1개만 반환하라. 수정 금지.
```

### Prompt C

```text
너는 read-only Sub-OPUS-C다. `us_ai_exile_monopoly`의 TR에서 반복이 어디서 reader-visible해지는지 찾아라. `solution`, `weakness_exploited`, `execution_doctrine`, opponent phrasing만 보고 짧은 repetition ledger를 반환하라. 수정 금지.
```

## 11. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-weakness-triage-order.md`와 `docs/2026-03-27/us-ai-exile-monopoly-opus-context-memo.md`, `docs/2026-03-27/us-ai-exile-monopoly-order-opus-brief.md`를 UTF-8로 읽고, `us_ai_exile_monopoly`에 대해 `source-TR weakness triage` 1단위만 조율하라. 같은 work_id 안에서는 단 한 명만 최종 보고서를 쓰게 하고, 읽기만 `A(canonical pair truth) || B(sceneability sample) || C(repetition map)`로 병렬화하라.
```

Confidence:
- 98% this is the lowest-risk delegation shape for `us_ai_exile_monopoly`
