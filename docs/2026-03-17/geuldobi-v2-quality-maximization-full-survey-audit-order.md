# Geuldobi V2 Quality Maximization Full Survey Audit Order

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
Document Type: audit order
Mode: `ROL 전역 전체 전수조사만`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: stage-pipeline lane1~3 code/tests/docs edits, temp execution mirror deletions, 1 runtime log, 1 untracked roadmap draft; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Strategy Notes:
- `docs/roadmap-v2.md` is a draft thesis seed, not governing authority
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md` is the normalized seed filter and logging-attachment rule
- `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md` is the launch companion for T01~T10
- `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-launch-shortform.md` is the minimal terminal-launch companion
- `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md` is a bounded Stage-pipeline survey seed, not a repo-wide closure artifact
- live code authority beats historical notes and brainstorming docs

## 1. Intent
- open a repo-wide deep global survey aimed at maximizing manuscript-process quality before further realization work
- turn the high-level themes in `docs/roadmap-v2.md` into a bounded but broad system-track survey plan
- make the survey parallelizable across `10 terminals` without creating conflicting roadmap authority
- keep this cycle in `survey-only` mode until the merged survey bundle and confidence gate are complete

## 2. Why A New Global Survey Order Exists
- the 2026-03-17 Stage-pipeline bounded survey already mapped the highest-ROI process lanes inside Stage 2/3/4
- `docs/roadmap-v2.md` widens the concern from Stage-pipeline semantics into:
  - repo-wide information loss and hard truncation
  - taxonomy and intermediate-step loss
  - cost and latency duplication
  - long-run quality degradation
  - upper-stage design quality
  - prompt-structure quality
- those themes now touch more than the Stage pipeline alone, so the next survey must be `repo-wide` rather than one more Stage-4-only note

## 3. Scope Lock

### Included By Default
- `main_a.py`
- `main.js`
- `modules/`
- `scripts/`
- `tests/`
- `UI/`
- `geuldobi-desktop/`
- runtime-affecting root files and helpers
- `config/` and prompt/config maps that materially affect runtime behavior
- runtime-generated artifact and log surfaces under `projects/` when needed for artifact-truth or metadata-truth checks
- canonical governance docs and recent dated survey docs only as baseline/reference material

### Excluded By Default
- `.git/`
- virtualenv, build, cache, temp, and archival folders
- narrative-production content review by `work_id`
- broad treatment/bible authoring review
- direct code patching or runtime mutation
- execution realization in the same order

### Change Lock
- survey-only
- no code edits
- no config mutation
- no DB mutation
- no temp execution queue opening during the evidence-harvest phase

## 4. Governing Harness Stack
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`
- `docs/implementation/single-ssot-roadmap-contract.md`

## 5. Deliverable Policy

### During Parallel Harvest
- terminal workers may save only raw or reusable evidence artifacts
- preferred worker outputs:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t0N-*-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t0N-*-paths.json`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t0N-*-watchlist.txt`
- worker terminals must not save final human-facing survey conclusions or execution SSOTs

### After Synthesis
- one master survey doc:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
- one evidence manifest:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-evidence-manifest.md`
- one cross-cut integrity matrix section or companion doc:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-cross-cut-integrity-matrix.md`
- one uncertainty and contradiction ledger section or companion doc:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-uncertainty-contradiction-ledger.md`
- area execution SSOTs only for action-bearing areas
- exactly one canonical roadmap only if two or more execution SSOTs are produced
- temp mirrors only after the canonical execution docs pass the 3-pass save gate

### Logging Policy
- logging is not a standalone survey lane
- attach logging review only where lack of observability would make a claim invalid or non-actionable
- use the logging packs defined by:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
- prefer existing sinks and operator surfaces over ad hoc new log files

## 6. Parallel Operating Model

### Phase 0. Scope Freeze
- terminal 10 confirms baseline commit and dirty summary
- terminal 10 confirms no active temp execution queue beyond `docs/temp/README.md`
- terminal 10 freezes the survey slug: `geuldobi-v2-quality-maximization`
- terminal 10 loads the roadmap triage doc and uses it to filter `keep` vs `merge/defer/out-of-scope` seeds before worker launch

### Phase 1. Terminal 1-9 Evidence Harvest
- each worker owns a non-overlapping primary scope
- each worker must collect:
  - path inventory
  - hotspot list
  - side-effect notes
  - open contradictions
  - candidate action-bearing areas
- each worker must also note logging adequacy only when the triage doc says observability is required for validity
- critical claims should aim for `A + B + C/D/E` triangulation where feasible

### Phase 2. Terminal 10 First Merge
- collect all worker artifacts
- build the contradiction ledger
- request targeted delta reads only where critical claims remain single-sourced

### Phase 3. Terminal 10 Synthesis
- produce the master survey bundle
- run the 3-pass document audit
- score confidence under the integrity confidence contract
- stop if confidence is below 95

### Phase 4. Execution-Doc Opening, If Warranted
- only after the merged survey is final
- only for action-bearing areas
- canonical execution SSOTs first
- temp mirrors second
- exactly one SSOT roadmap if multiple execution SSOTs exist

## 7. Terminal Split

| Terminal | Primary Mission | Primary Paths | Roadmap-v2 Theme Anchor | Required Output |
| --- | --- | --- | --- | --- |
| `T01` | repo topology, entrypoints, authority map | root, `main_a.py`, `main.js`, top-level subsystem roots | global topology | `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt` |
| `T02` | bootstrap, runtime spine, process runner, fallback seams | `main_a.py`, `modules/core/`, `modules/api/`, `lite_mode/`, `test_mode/` entrypoints | runtime control-flow | `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt` |
| `T03` | Stage 2/3 upstream design quality and information handoff | `modules/core/stage2_*`, `modules/core/stage3_*`, related tests | upper-stage design quality | `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt` |
| `T04` | CW input quality, context layering, prompt structure, truncation | `modules/core/stage4_context_builder.py`, `modules/core/context_advisor.py`, CW prompt surfaces | input quality + prompt structure + truncation | `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt` |
| `T05` | Director, validators, gate semantics, PASS_WITH_FIX, retry policy | `modules/core/stage4_interview_round.py`, `modules/domain/agents/`, `modules/validation/`, `modules/core/adaptive_retry.py` | feedback quality + taxonomy/semantic loss | `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt` |
| `T06` | persistence, durability, artifact truth, metadata truth | `modules/core/stage4_post_processor.py`, `modules/core/world_state.py`, persistence/logging surfaces, `projects/` runtime artifacts | durability + long-run integrity | `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt` |
| `T07` | operator-visible surface and app shell linkage | `UI/`, `geuldobi-desktop/`, `modules/core/quality_dashboard.py`, `modules/core/pass_rate_monitor.py`, `modules/api/bridge_server.py` | operator surface | `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt` |
| `T08` | tests, smoke/canary, scripts, repair tooling, verification economics | `tests/`, `scripts/`, root helpers, smoke runners | regression surface + utility tooling | `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt` |
| `T09` | cross-cut contracts/config, model routing, thresholds, cost/latency duplication, long-context policy | `config/`, prompt maps, shared constants, routing/config surfaces across repo | cost/latency + long-context + contract drift | `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt` |
| `T10` | merge, contradiction closure, confidence scoring, execution-doc mapping | all worker artifacts plus targeted live reads as needed | synthesis | `docs/2026-03-17/geuldobi-v2-quality-maximization-t10-merge-watchlist.txt` |

## 7A. Overlap Guard
- `T01` may map ownership boundaries and entrypoints, but it should not deep-audit Stage 2/3/4 semantics already owned by `T03` to `T05`
- `T02` may inspect bootstrap and orchestration seams, but detailed CW/Director quality semantics belong to `T04` and `T05`
- `T06` owns durable state, metadata truth, and artifact truth; `T07` owns what the operator sees
- `T08` owns test and script surfaces; `T09` owns cross-cut config and contract meaning
- if a terminal finds a critical issue outside its lane, it should record a handoff note rather than expand scope

## 8. Terminal Rules

### Shared Rules For T01-T09
- do not patch code
- do not create execution SSOTs
- do not create roadmap docs
- do not overwrite another terminal's evidence file
- use the roadmap triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them
- use live code as authority and treat `docs/roadmap-v2.md` as a hypothesis seed only
- separate `Fact`, `Inference`, and `Open Question`
- explicitly mark not-applicable side-effect categories instead of silently omitting them

### Shared Rules For T10
- do not create a second roadmap authority
- do not call the survey final until the 3-pass audit and 95% confidence gate are complete
- do not synthesize critical `P1` claims from one evidence class only
- if worker outputs conflict, record the contradiction instead of silently choosing one side

## 9. Worker Evidence Format
Each worker evidence file should follow this compact structure:

1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Use short bullets. Prefer paths and concrete function/class names over prose.

## 10. Shared Prompt Skeleton
Use this base prompt for terminals `T01` to `T09`, then replace the terminal block with the lane-specific scope from Section 7.

```text
시스템 오더다. AGENTS.md -> system-order init harness -> system-full-survey-execution-harness -> codebase-global-survey-coverage-contract -> deep-global-integrity-survey-harness 순서로 따르라.

모드는 `ROL 전역 전체 전수조사만`이다. 구현, 패치, temp execution queue opening으로 넘어가지 말고 survey-only에서 멈춰라.

현재 active canonical audit order는:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`

seed triage authority는:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

상위 전략 seed는:
- `docs/roadmap-v2.md`
하지만 draft thesis일 뿐 authority는 live code에 있다.

너의 터미널 배정:
- terminal: `T0X`
- primary mission: `<Section 7 value>`
- primary paths: `<Section 7 value>`
- theme anchor: `<Section 7 value>`
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t0X-...-evidence.txt`

필수 규칙:
- 코드 수정 금지
- 다른 터미널 산출물 덮어쓰기 금지
- Fact / Inference / Open Question 분리
- side-effect category 비적용이면 명시
- critical claim은 가능하면 evidence triangulation을 맞춰라
- triage doc상 logging pack이 필요한 주제만 logging adequacy를 기록하라
- execution SSOT/roadmap은 만들지 마라

산출물은 raw evidence 수준으로만 저장하라.
최종 human-facing survey 결론은 terminal 10 synthesis 이후 3pass audit로만 확정된다.
```

## 10A. T10 Merge Prompt Skeleton
Use this prompt for terminal `T10`.

```text
시스템 오더다. AGENTS.md -> system-order init harness -> system-full-survey-execution-harness -> codebase-global-survey-coverage-contract -> deep-global-integrity-survey-harness -> document-3pass-audit-harness 순서로 따르라.

모드는 `ROL 전역 전체 전수조사만`이다. 구현, 패치, execution realization으로 넘어가지 말고 survey synthesis에서 멈춰라.

현재 active canonical audit order는:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`

seed triage authority는:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

상위 전략 seed는:
- `docs/roadmap-v2.md`
하지만 draft thesis일 뿐 authority는 live code와 worker evidence다.

너의 역할:
- terminal: `T10`
- primary mission: merge, contradiction closure, confidence scoring, execution-doc mapping
- worker inputs:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`
- watchlist output:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t10-merge-watchlist.txt`

필수 규칙:
- second SSOT roadmap 생성 금지
- single-sourced critical claim 금지
- worker evidence 간 충돌은 ledger에 기록
- human-facing final docs는 3pass audit + confidence >=95 이후에만 저장
- action-bearing area가 2개 이상이면 roadmap authority는 정확히 1개만 허용
- worker evidence가 부족하면 targeted delta request만 발행하고 scope를 새로 키우지 마라
```

## 11. Merge and 3-Pass Rule
- worker evidence files may be saved during investigation
- any human-facing interpretation doc must wait for:
  - draft
  - pass 1
  - pass 2
  - pass 3
  - targeted re-audit until confidence >= 95
- if the merged bundle produces two or more action-bearing execution docs:
  - create exactly one canonical roadmap
  - then mirror it to `docs/temp/execution-roadmap.md`
- if the merged bundle produces no action-bearing execution docs:
  - stop at the survey bundle

## 12. Why `10 Terminals` Is The Right Split
- `8` required global coverage tranches already exist in the coverage contract
- `T09` is needed because `roadmap-v2` raises cross-cut issues that do not fit one code folder:
  - truncation
  - contract drift
  - cost duplication
  - long-context policy
  - threshold sprawl
- `T10` is needed to preserve one synthesis authority and avoid parallel-roadmap drift

## 13. Immediate Next Step
- launch terminals `T01` to `T09` for evidence harvest
- keep `T10` as the merge coordinator
- do not open execution docs until the merged global survey clears the 3-pass audit and 95% confidence gate

## 14. Confidence Statement
- estimated confidence in this audit order as an operator document: `97%`
- rationale:
  - scope, mode, and stop-line are explicit
  - the split covers the required global survey tranches and the roadmap-v2 cross-cut themes
  - single-roadmap authority is preserved
  - raw-evidence vs final-doc boundary is explicit
- remaining risk:
  - worker terminals may still produce overlapping evidence if they ignore the path ownership table
  - terminal 10 must enforce contradiction logging rather than premature synthesis
