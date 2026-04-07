# Stage234 Handoff Harness 4-Terminal Parallel Survey Order

Date: 2026-04-07
Status: final
Document Type: operator parallel order
Canonical Path: `docs/2026-04-07/stage234-handoff-harness-4terminal-parallel-survey-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Track: system
Mode: read-only parallel survey; no code patching; docs-only outputs
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas; hotspots include docs/temp/execution-roadmap.md, docs/temp/queue-state.json, docs/2026-04-01/active-temp-execution-roadmap.md, narrative-router files, multiple BI/TR artifacts, and untracked docs/2026-04-07 notes`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Purpose

This order splits one bounded system-track survey into four non-overlapping
terminal lanes:

- `Stage2 producer / handoff`
- `Stage3 binding / blueprint handoff`
- `Stage4 consumer / manuscript handoff`
- `cross-cut authority / compression / promotion matrix`

This wave is not asking whether the pipeline works in the large.
This wave is asking a narrower question:

- where the execution harness is still weak across `Stage2 -> Stage3 -> Stage4`
- which weakness is still stage-local versus boundary-crossing
- which owner files actually own the debt
- whether the merged evidence justifies promotion into a new execution SSOT

## 2. Queue Context

Active temp queue context exists already.
This order does not replace the current queue controller and must not mutate it.

Context only:

- canonical roadmap:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
- temp mirror queue controller:
  - `docs/temp/execution-roadmap.md`
- queue snapshot:
  - `docs/temp/queue-state.json`

Current queue reading relevant to this survey:

- `Stage2` active residual debt is now mainly `producer-side contract packaging /
  persistence authority`, not broad content generation failure.
- `Stage3` future-wave debt is mainly `binding weakness + semantically lossy
  handoff`.
- `Stage4` active debt is mainly `consumer-side contract normalization`, not a
  full prompt redesign.
- a parked `cross-stage` lane already exists, but it must not be promoted or
  reprioritized casually without fresh merged evidence.

This survey therefore stays read-only and produces evidence only.
Queue promotion, if any, happens after the four lane docs are merged and
audited centrally.

## 3. Fixed Read Before Starting

Every terminal reads these first:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/stage_map/interfaces.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

## 4. Global Guardrails

1. Stay read-only.
2. Do not patch code in this wave.
3. Do not mutate `docs/temp/`.
4. Do not rewrite or reprioritize the active queue in this wave.
5. Do not reopen a broad `readiness` or `global architecture rewrite` claim.
6. Use live code and canonical docs first; temp mirrors are queue context only.
7. Findings are the primary content.
   A short `Coverage` header may precede them, but no overview or summary may
   outrank the findings.
8. Cite exact file paths for owner claims.
9. Each terminal writes exactly one output document under `docs/2026-04-07/`.
10. Each lane must classify findings into:
   - `stage-local`
   - `boundary-local`
   - `cross-stage`
11. Each lane must end with a promotion signal, not a promotion action.
12. The four lane docs are survey outputs only.
    No terminal may create or refresh an execution SSOT in this wave.

## 5. Global Questions

Across all four lanes, answer these without duplicating each other:

1. What is the strongest canonical packet or contract that the stage believes it
   owns?
2. What does the actual downstream consumer really read?
3. Where does meaning get compressed, flattened, rewritten, or dropped?
4. Which owner files own the gap?
5. Is the gap already covered by an existing queue item, or is there still a
   missing execution lane after merge?

## 6. Terminal Ownership

### Terminal 1

- owner: `Stage2 producer / handoff harness`
- mission:
  - inspect what `Stage2` believes it is authoritatively handing off
  - distinguish strong packet surfaces from prose-only fallback surfaces
  - isolate remaining producer-side harness weakness without reopening broad
    Stage3/4 blame
- output:
  - `docs/2026-04-07/stage234-terminal1-stage2-producer-handoff-survey.md`

### Terminal 2

- owner: `Stage3 binding / blueprint handoff harness`
- mission:
  - inspect how `Stage3` ingests `Stage2` truth
  - map which parts become advisory-only, prose-only, or semantically weakened
  - isolate Stage3-owned contract debt without collapsing into Stage4-only blame
- output:
  - `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`

### Terminal 3

- owner: `Stage4 consumer / manuscript handoff harness`
- mission:
  - inspect how `Stage4` consumes blueprint truth
  - map where intake hierarchy survives versus where it is flattened into writer
    context, repair loops, or post-pass sinks
  - isolate true Stage4 consumer-harness weakness
- output:
  - `docs/2026-04-07/stage234-terminal3-stage4-consumer-handoff-survey.md`

### Terminal 4

- owner: `cross-cut authority / compression / promotion matrix`
- mission:
  - build the `Stage2 -> Stage3 -> Stage4` contract matrix
  - identify exact drop, compression, alias, and owner-boundary seams
  - decide whether the merged survey should later promote a new execution SSOT
    or simply attach to existing queue lanes
- output:
  - `docs/2026-04-07/stage234-terminal4-crosscut-authority-matrix-survey.md`

## 7. Shared Output Contract

Each terminal uses the same section shape:

1. `Coverage`
2. `Findings`
3. `Authority / Loss Map`
4. `Non-Issues`
5. `Owner Verdict`
6. `Promotion Signal`
7. `Stop`

Section rules:

- `Coverage`:
  - what was read
  - what was intentionally excluded
- `Findings`:
  - ordered by severity
  - file paths required
- `Authority / Loss Map`:
  - `authoritative surface`
  - `actual consumer surface`
  - `loss/compression point`
- `Non-Issues`:
  - things that looked suspicious but are not front debt in this wave
- `Owner Verdict`:
  - narrowest plausible owner set
- `Promotion Signal`:
  - one of:
    - `covered-by-existing-queue`
    - `merge-first-no-promotion`
    - `candidate-for-new-execution-ssot`
- `Stop`:
  - no extra planning prose after the required stop line

Required stop line:

- `read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output`

## 8. Lane-Specific Questions

### Terminal 1 Questions

1. Which `Stage2` surfaces are truly canonical for downstream use:
   `episode_details`, `tactical_doc`, `state_constraints`, `joint_docs`,
   `status_shadow`, `state_changes`, `beat_sequence`, or a narrower subset?
2. Where does `Stage2` already provide strong execution-harness structure, and
   where is it still relying on prose expansion or fallback normalization?
3. Which remaining `Stage2` weakness is still genuinely producer-local versus
   already downstream-consumer debt?
4. What is the narrowest owner set if a future producer-side harness wave is
   promoted?

### Terminal 2 Questions

1. Where does `Stage3` first weaken or flatten `Stage2` intent:
   compiler, runtime orchestration, validator, or blueprint candidate flow?
2. Which `Stage2` packet truths survive as machine-meaningful constraints, and
   which survive only as prose or weak advisory context?
3. Is the main `Stage3` harness weakness binding scope, semantic transport, or
   both?
4. What is the narrowest owner set if a future `Stage3` harness wave is
   promoted?

### Terminal 3 Questions

1. Which `Stage3` truths survive as structured `Stage4` intake, and which are
   flattened into writer context, repair prompts, or post-pass normalization?
2. Does `Stage4` still rely on repair/review loops where a stronger intake
   contract should have blocked or preserved truth earlier?
3. Which `Stage4` weakness is truly consumer-local versus inherited upstream?
4. What is the narrowest owner set if a future `Stage4` harness wave is
   promoted?

### Terminal 4 Questions

1. Across `Stage2 -> Stage3 -> Stage4`, where are the exact authority seams:
   packet owner, compiler owner, consumer owner, persistence owner, and
   observability owner?
2. Which loss families are:
   - field death
   - prose flattening
   - advisory downgrade
   - repair-loop compensation
   - operator visibility gap
3. Which existing queue items already cover the proven debt, and which debt
   still has no clean execution home?
4. After merge, should the central audit:
   - attach findings to existing queue items only
   - stop at merged survey
   - promote a new bounded execution SSOT

## 9. Read Lists Per Terminal

### Terminal 1 Read List

- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`
- `config/prompts/ensemble.yaml`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_entity_contract.py`
- `modules/core/tactical_utils.py`

### Terminal 2 Read List

- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/chief_writer_context_packets.py`

### Terminal 3 Read List

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_context_packets.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_quality.py`
- `modules/domain/agents/manuscript_validator.py`

### Terminal 4 Read List

- `docs/stage_map/interfaces.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `modules/core/response_schemas.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`

## 10. Merge and Promotion Flow

After all four lane docs exist, the central auditor (`Codex`) will do this:

1. read all four outputs
2. merge duplicate findings
3. separate:
   - stage-local debt
   - cross-stage debt
   - queue-covered debt
   - uncovered debt
4. write one merged audit document:
   - `docs/2026-04-07/stage234-handoff-harness-merge-audit.md`
5. decide whether execution promotion is justified
6. only if justified, write canonical execution SSOT:
   - `docs/2026-04-07/stage234-handoff-harness-strengthening-execution-ssot.md`
7. only after 3-pass audit and 95% confidence, refresh temp mirror:
   - `docs/temp/stage234-handoff-harness-strengthening-execution-ssot.md`

Promotion gate:

- promote only if merged evidence identifies:
  - one bounded topic slug
  - one narrow owner set or tightly related owner family
  - one actionable acceptance boundary
- do not promote if the merged result is only:
  - overlapping observations already fully covered by active queue items
  - broad architecture commentary without a bounded execution seam

## 11. Paste-Ready Orders

### Terminal 1

```text
시스템 오더다. 이 lane은 `Stage2 producer / handoff harness`만 조사한다.

목적:
- Stage2가 downstream에 무엇을 canonical하게 넘긴다고 믿는지 확인
- strong packet surface와 prose/fallback surface를 구분
- producer-local debt만 좁혀라. Stage3/4 일반론으로 도망가지 마라

공통 선행 읽기:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/implementation/commit-state-minimal-contract.md
- docs/stage_map/interfaces.md
- docs/2026-04-01/active-temp-execution-roadmap.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md

추가 읽기:
- modules/domain/agents/arc_ensemble.py
- modules/core/response_schemas.py
- config/prompts/ensemble.yaml
- modules/core/stage2_preflight.py
- modules/core/stage2_validation_pipeline.py
- modules/core/stage2_finalizer.py
- modules/core/stage2_entity_contract.py
- modules/core/tactical_utils.py

질문:
1. Stage2 canonical surface는 정확히 무엇인가
2. episode_details / tactical_doc / state_constraints / joint_docs / status_shadow / state_changes / beat_sequence 중 무엇이 strong handoff이고 무엇이 fallback인가
3. Stage2가 아직 prose expansion이나 normalization에 기대는 지점은 어디인가
4. 남은 debt 중 producer-local인 것과 downstream debt를 어떻게 가를 수 있나
5. 실행 승격 시 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-07/stage234-terminal1-stage2-producer-handoff-survey.md

섹션:
1. Coverage
2. Findings
3. Authority / Loss Map
4. Non-Issues
5. Owner Verdict
6. Promotion Signal
7. Stop

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- 기존 queue 재정렬 금지
- findings first
- exact file path 인용 필수

필수 종료문:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
```

### Terminal 2

```text
시스템 오더다. 이 lane은 `Stage3 binding / blueprint handoff harness`만 조사한다.

목적:
- Stage3가 Stage2 truth를 어디서 ingest하고 어디서 약화시키는지 확인
- binding scope, semantic transport, advisory downgrade를 분리
- Stage4 일반론으로 넘기지 말고 Stage3 owner를 좁혀라

공통 선행 읽기:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/implementation/commit-state-minimal-contract.md
- docs/stage_map/interfaces.md
- docs/2026-04-01/active-temp-execution-roadmap.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md

추가 읽기:
- modules/core/stage3_orchestrator.py
- modules/domain/agents/three_phase_blueprint_runtime.py
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/unified_blueprint_validator.py
- modules/domain/agents/chief_writer_context_packets.py

질문:
1. Stage3가 Stage2 intent를 처음 약화시키는 지점은 compiler, runtime, validator, candidate flow 중 어디인가
2. 어떤 Stage2 truth가 machine-meaningful constraint로 남고 어떤 truth가 prose/advisory로만 남는가
3. main debt는 binding scope 부족인가 semantic transport loss인가 둘 다인가
4. Stage3 local debt와 inherited upstream debt를 어떻게 가를 수 있나
5. 실행 승격 시 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md

섹션:
1. Coverage
2. Findings
3. Authority / Loss Map
4. Non-Issues
5. Owner Verdict
6. Promotion Signal
7. Stop

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- queue 재정렬 금지
- findings first
- exact file path 인용 필수

필수 종료문:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
```

### Terminal 3

```text
시스템 오더다. 이 lane은 `Stage4 consumer / manuscript handoff harness`만 조사한다.

목적:
- Stage4가 blueprint truth를 어떻게 intake하는지 확인
- structured intake가 writer context, repair loop, post-pass sink로 어떻게 변하는지 분리
- 진짜 consumer-local debt를 좁혀라

공통 선행 읽기:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/implementation/commit-state-minimal-contract.md
- docs/stage_map/interfaces.md
- docs/2026-04-01/active-temp-execution-roadmap.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md

추가 읽기:
- modules/core/stage4_orchestrator.py
- modules/core/stage4_context_builder.py
- modules/core/stage4_context_packets.py
- modules/core/stage4_context.py
- modules/core/stage4_interview_round.py
- modules/core/pre_director_manuscript_checker.py
- modules/core/stage4_post_pass_runtime.py
- modules/domain/agents/chief_writer_context.py
- modules/domain/agents/chief_writer_prompts.py
- modules/domain/agents/chief_writer_quality.py
- modules/domain/agents/manuscript_validator.py

질문:
1. Stage3 truth 중 무엇이 Stage4 structured intake로 남고 무엇이 flattened prose나 advisory로 바뀌는가
2. Stage4가 repair/review loop로 메우는 seam 중 intake contract가 더 세야 하는 지점은 어디인가
3. 어떤 debt가 진짜 Stage4 consumer-local이고 어떤 debt가 upstream inherited인가
4. post-pass / finalization / review sink 중 어느 owner가 실제 truth boundary를 쥐고 있나
5. 실행 승격 시 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-07/stage234-terminal3-stage4-consumer-handoff-survey.md

섹션:
1. Coverage
2. Findings
3. Authority / Loss Map
4. Non-Issues
5. Owner Verdict
6. Promotion Signal
7. Stop

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- queue 재정렬 금지
- findings first
- exact file path 인용 필수

필수 종료문:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
```

### Terminal 4

```text
시스템 오더다. 이 lane은 `cross-cut authority / compression / promotion matrix`만 조사한다.

목적:
- Stage2 -> Stage3 -> Stage4 contract matrix를 만든다
- field death, prose flattening, advisory downgrade, repair-loop compensation, operator visibility gap를 분리한다
- existing queue cover 여부와 new execution SSOT 필요 여부를 판단할 promotion signal만 남긴다

공통 선행 읽기:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/implementation/commit-state-minimal-contract.md
- docs/stage_map/interfaces.md
- docs/2026-04-01/active-temp-execution-roadmap.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md
- docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md

추가 읽기:
- docs/stage_map/interfaces.md
- docs/2026-04-01/active-temp-execution-roadmap.md
- modules/core/response_schemas.py
- modules/domain/agents/arc_ensemble.py
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/core/stage4_context_builder.py
- modules/core/stage4_orchestrator.py

질문:
1. packet owner, compiler owner, consumer owner, persistence owner, observability owner는 stage chain 어디에 있나
2. exact loss family는 무엇인가: field death, prose flattening, advisory downgrade, repair compensation, operator gap
3. existing queue items가 이미 커버하는 debt와 아직 execution home이 없는 debt는 무엇인가
4. merge 후 central audit는 기존 queue attach로 끝나야 하나, merged survey만 저장해야 하나, 아니면 bounded execution SSOT 승격이 필요한가
5. 새 execution SSOT가 필요하다면 topic slug는 무엇이 가장 bounded한가

산출물:
- docs/2026-04-07/stage234-terminal4-crosscut-authority-matrix-survey.md

섹션:
1. Coverage
2. Findings
3. Authority / Loss Map
4. Non-Issues
5. Owner Verdict
6. Promotion Signal
7. Stop

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- queue 재정렬 금지
- findings first
- exact file path 인용 필수
- stage deep-dive를 다시 다 하지 말고 cross-cut seam만 보라

필수 종료문:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
```
