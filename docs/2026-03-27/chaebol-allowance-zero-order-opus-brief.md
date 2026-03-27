# Chaebol Allowance Zero Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `chaebol_allowance_zero`

## 1. What You Are

You are not the single editing worker for this run.
You are the coordinator OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to one unit
- prevent stale-root-path drift
- separate structural PASS from narrative readiness
- use parallelism only for read-only planning diagnosis
- return one coherent next-step judgment

## 2. Fixed Scope

This run is only:

- `density-recovery rewrite plan`

This run is not:

- active promotion
- revival-stage probe
- live TR rewrite
- BI redesign

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:

- parallel read-only investigation is allowed
- parallel private note-taking is allowed
- parallel edits to the same final report are not allowed
- only one worker may write the final rewrite-plan report

## 4. Recommended Sub-OPUS Layout

### OPUS-Order

Own:

- orchestration
- work partitioning
- final truth synthesis
- final next-unit judgment

Do not let multiple sub-OPUS workers edit the same final report.

### Sub-OPUS-A: Canonical Path / Duplicate Truth

Read-only task:

- verify which pair files actually exist now
- verify which root-path docs are stale
- verify duplicate BI variants
- verify whether `_quarantine` should remain the live authority for the next wave

Expected output:

- short path-truth ledger only

### Sub-OPUS-B: Audit Defect Extractor

Read-only task:

- read the 4-axis audit and retry-vs-failed evidence
- separate immediate blockers from later-wave rewrite targets
- preserve what the retry wave already fixed

Expected output:

- short defect / preserve split only

### Sub-OPUS-C: Rewrite-Band Sampler

Read-only task:

- use direct TR reads to compare the benchmark band with the weak bands
- identify the best first rewrite wave

Required windows:

- `Block 1-6`
- `Block 7-15`
- `Block 16-35`
- `Block 36-70`

Expected output:

- benchmark traits
- first rewrite band recommendation
- one-line wave judgment

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

If any of these appear, stop the optimism and do not force a salvage narrative:

- missing root canonical paths are repeated as if they still exist
- structural PASS is repeated as if it proves treatment-grade density
- the work is drifted into stock-market spectacle instead of support-system cashflow warfare
- retry gains are discarded and the plan restarts from zero
- all 64 weak blocks are treated as one undifferentiated blob with no first-wave priority
- failed numbered assets are mistakenly treated as live overwrite targets

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- the support-system cashflow ladder
- the “moneyline before inheritance” engine
- funeral / catering / hotel / factory / hospital / settlement / nationwide ops sequence
- no family bailout
- B2B daily-expense choke points

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-chaebol-allowance-zero-density-rewrite-plan-order.md`
- `docs/2026-03-27/chaebol-allowance-zero-opus-context-memo.md`
- `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
- `treatments/preprocess/chaebol_allowance_zero/source_manifest.json`
- `treatments/preprocess/chaebol_allowance_zero/phase0_ready_snapshot.json`
- `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md`
- `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_chaebol_allowance_zero.json`

## 9. Coordinator Output Requirement

The coordinator should produce exactly one final judgment:

- `pass`
- `mixed`
- `fail`

and exactly one next unit:

- `rewrite block wave 1`
- `canonical-path patch`
- `weakness report only`

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 read-only Sub-OPUS-A다. `chaebol_allowance_zero`의 canonical live pair truth만 확인하라. 실제 존재 pair, stale root paths, duplicate BI variants, `_quarantine` authority 여부만 짧은 ledger로 반환하라. 수정 금지.
```

### Prompt B

```text
너는 read-only Sub-OPUS-B다. `chaebol_allowance_zero`의 4축 감사와 retry-vs-failed evidence를 읽고, immediate blockers와 preserved strengths를 분리하라. immediate 3개, preserve 3개만 반환하라. 수정 금지.
```

### Prompt C

```text
너는 read-only Sub-OPUS-C다. `chaebol_allowance_zero` TR의 benchmark band(1-6)와 weak bands(7-15, 16-35, 36-70)를 비교하라. 질문은 하나다: 첫 rewrite wave는 어디부터 들어가야 하는가. benchmark trait 1개, weak trait 1개, first-wave recommendation 1개만 반환하라. 수정 금지.
```

## 11. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-chaebol-allowance-zero-density-rewrite-plan-order.md`와 `docs/2026-03-27/chaebol-allowance-zero-opus-context-memo.md`, `docs/2026-03-27/chaebol-allowance-zero-order-opus-brief.md`를 UTF-8로 읽고, `chaebol_allowance_zero`에 대해 `density-recovery rewrite plan` 1단위만 조율하라. 같은 work_id 안에서는 단 한 명만 최종 보고서를 쓰게 하고, 읽기만 `A(path truth) || B(defect extractor) || C(rewrite-band sample)`로 병렬화하라.
```

Confidence:
- 98% this is the lowest-risk delegation shape for `chaebol_allowance_zero`
