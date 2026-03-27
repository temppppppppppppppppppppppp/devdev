# Pantech Cyworld Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `pantech_cyworld_reborn`

## 1. What You Are

You are not the single editing worker for this run.
You are the coordinator OPUS that may dispatch sub-OPUS workers.

Your job is:
- keep the run bounded to one unit
- avoid same-work drift
- use sub-OPUS parallelism only where it is safe
- return one coherent next-step judgment

## 2. Fixed Scope

This run is only:
- `revival-stage probe`

This run is not:
- active promotion
- Stage 4 canary
- TR regeneration
- broad BI redesign

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:
- parallel read-only investigation is allowed
- parallel note-taking in private scratch is allowed
- parallel edits to the same pair/report are not allowed
- only one worker may write the final probe report

## 4. Recommended Sub-OPUS Layout

### OPUS-Order

Own:
- orchestration
- work partitioning
- final truth synthesis
- final go/no-go judgment

Do not let multiple sub-OPUS workers edit the same final report.

### Sub-OPUS-A: Artifact Truth / Contract Check

Read-only task:
- verify live pair paths
- verify preprocess gate truth
- verify prior reports still match live files
- verify no new contract blocker has appeared

Expected output:
- short factual ledger only

### Sub-OPUS-B: Stage 2 Probe Executor

Single execution owner for generation path:
- run bounded runtime admission
- run bounded Stage 2 probe on early high-signal window
- save raw result or short evidence note if needed

Expected output:
- runtime admission verdict
- Stage 2 output quality verdict

### Sub-OPUS-C: Stage 3 Probe Evaluator

This worker should not start until Stage 2 output exists.

Task:
- take the Stage 2 result
- run bounded Stage 3 probe
- evaluate whether blueprint is sceneable or flattened

Expected output:
- Stage 3 verdict
- flattening / survival notes

## 5. Parallelism Rule

Safe parallel start:
- Sub-OPUS-A may run immediately
- Sub-OPUS-B may run immediately

Dependent start:
- Sub-OPUS-C starts only after Sub-OPUS-B produces usable Stage 2 output

So the structure is:
- `A || B`
- then `C`
- then coordinator synthesis

## 6. What Order-OPUS Must Watch

If any of these appear, stop the ladder and do not force completion:

- live pair contradicts prior repair/canary docs
- runtime admission fails for a new contract reason
- output drifts too early into generic smart-city / public-infra abstraction
- Stage 2 or Stage 3 collapses into summary-only slabs
- the next honest step would actually be `promotion patch`, not probe closure

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:
- 2006~2007 Korean IT timing
- Pantech + Cyworld dual-revival engine
- telecom certification / QA / first-screen / payment chokepoints
- regression slip-up pressure
- chaebol succession / capital pressure

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-pantech-cyworld-revival-stage-probe-order.md`
- `docs/2026-03-27/pantech-cyworld-opus-context-memo.md`
- `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
- `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
- `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`

## 9. Coordinator Output Requirement

The coordinator should produce exactly one final judgment:
- `pass`
- `mixed`
- `fail`

and exactly one next unit:
- `active promotion`
- `promotion patch`
- `weakness report only`

## 10. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-pantech-cyworld-revival-stage-probe-order.md`와 `docs/2026-03-27/pantech-cyworld-opus-context-memo.md`, `docs/2026-03-27/pantech-cyworld-order-opus-brief.md`를 UTF-8로 읽고, `pantech_cyworld_reborn`에 대해 `revival-stage probe` 1단위만 조율하라. 같은 work_id 안에서는 단 한 명만 최종 보고서를 쓰게 하고, 읽기/검증만 병렬화하라. 권장 구조는 `A(artifact truth) || B(stage2 probe)` 후 `C(stage3 probe)` 후 coordinator synthesis다.
```

Confidence:
- 97% this is the lowest-overhead safe delegation shape for order-OPUS
