# Empire Youngest Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `empire_youngest_allsector`

## 1. What You Are

You are not the single editing worker for this run.
You are the coordinator OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to one unit
- prevent stale-authority drift
- use parallelism only for read-only truth gathering
- return one coherent next-step judgment

## 2. Fixed Scope

This run is only:

- `truth-reconciliation re-audit`

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
- only one worker may write the final re-audit report

## 4. Recommended Sub-OPUS Layout

### OPUS-Order

Own:

- orchestration
- work partitioning
- final truth synthesis
- final next-unit judgment

Do not let multiple sub-OPUS workers edit the same final report.

### Sub-OPUS-A: Artifact Truth Ledger

Read-only task:

- verify live pair paths
- verify direct TR block count
- verify BI roadmap count
- verify preprocess gate truth
- verify sequential status truth

Expected output:

- short factual ledger only

### Sub-OPUS-B: Stale-Authority Reconciliation

Read-only task:

- read the old survey claim set
- compare it against live files
- mark each claim `confirmed`, `stale`, or `partially true`

Expected output:

- short authority table only

### Sub-OPUS-C: Bounded Quality Sampler

Read-only task:

- sample early / mid / late windows
- check whether `70 exists` also means `70 usable`
- identify compression bands and patterned execution

Recommended windows:

- `Block 1-5`
- `Block 32-43`
- `Block 65-70`

Expected output:

- strongest surviving engine
- weakest compression zone
- probe-readiness opinion

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

If any of these appear, stop the ladder-thinking and do not force a promotion narrative:

- an old survey claim is repeated as fact even though live files contradict it
- raw block count is treated as proof of runtime quality
- BI richness is mistaken for overall pair readiness
- mid-band compression is hand-waved away because the ending exists
- the work drifts into sector-timing summary instead of domain-specific scene pressure
- protagonist engine gets washed out behind only capital arithmetic

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- 2045 -> 2025 regression
- credit-card `3,000만 원` BTC seed
- `세 개씩. 쉬지 않고.` doctrine
- independent-capital rule
- family-collapse 3-axis memory
- low-affect protagonist who cracks late, not early
- 0원 -> 200조 all-sector build

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-empire-youngest-truth-reaudit-order.md`
- `docs/2026-03-27/empire-youngest-opus-context-memo.md`
- `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`
- `treatments/preprocess/empire_youngest_allsector/sequential_run_status.json`
- `treatments/preprocess/empire_youngest_allsector/phase0_ready_snapshot.json`
- `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 9. Coordinator Output Requirement

The coordinator should produce exactly one final judgment:

- `pass`
- `mixed`
- `fail`

and exactly one next unit:

- `revival-stage probe`
- `fresh TR static audit`
- `weakness report only`

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 read-only Sub-OPUS-A다. `empire_youngest_allsector`의 live artifact truth만 확인하라. `TR` block count, `BI.plot_roadmap` count, `sequential_run_status.json`, `phase0_ready_snapshot.json`만 읽고 짧은 사실 ledger만 반환하라. 해석 과장 금지, 수정 금지.
```

### Prompt B

```text
너는 read-only Sub-OPUS-B다. `docs/2026-03-26/blockguide-quarantine-static-quality-survey.md`의 `empire_youngest_allsector` 관련 주장만 뽑아서 현재 live pair와 대조하라. 각 주장마다 `confirmed / stale / partially true` 중 하나로만 표시하고 짧은 근거를 붙여라. 수정 금지.
```

### Prompt C

```text
너는 read-only Sub-OPUS-C다. `empire_youngest_allsector`의 `TR`과 `BI`를 early(1-5) / middle(32-43) / late(65-70)만 표본 읽기하라. 질문은 하나다: `70개가 실제로 probe-ready한가`. 강점 1개, 약점 1개, next-unit 의견 1개만 반환하라. 수정 금지.
```

## 11. Minimal Prompt You Can Give Order-OPUS

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-empire-youngest-truth-reaudit-order.md`와 `docs/2026-03-27/empire-youngest-opus-context-memo.md`, `docs/2026-03-27/empire-youngest-order-opus-brief.md`를 UTF-8로 읽고, `empire_youngest_allsector`에 대해 `truth-reconciliation re-audit` 1단위만 조율하라. 같은 work_id 안에서는 단 한 명만 최종 보고서를 쓰게 하고, 읽기만 `A(artifact truth) || B(stale-authority reconcile) || C(bounded quality sample)`로 병렬화하라.
```

Confidence:
- 98% this is the lowest-risk delegation shape for `empire_youngest_allsector`
