# Stage Pipeline Process Integrity Global Survey Order Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/stage-pipeline-process-integrity-global-survey-order-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- preserve a reusable bounded global-survey order for Stage pipeline process integrity work
- frame a high-ROI repo-wide survey without opening immediate realization work
- connect previously saved planning notes into one survey thesis
Non-Goals:
- no code changes in this note
- no claim that the note is 3-pass finalized
- no execution SSOT or execution queue opened by this note alone

## 0. Why A Bounded Global Survey
- the current high-ROI problems are no longer isolated single-file bugs
- they are cross-cutting process-architecture questions spanning:
  - Stage 4 pre-write context
  - context composition and retrieval ranking
  - Director prompt austerity
  - quality-gate semantics
  - PASS_WITH_FIX local repair semantics
  - retry budget policy
- running separate brainstorm threads forever risks duplication and local optimization
- a bounded repo-wide survey can unify these into one process map without prematurely entering implementation

## 1. Recommended Survey Thesis
- investigate whether the current Stage pipeline produces good manuscripts through a good process
- focus on process integrity, not isolated feature count
- primary lens:
  - context flow
  - authority boundaries
  - gate semantics
  - repair semantics
  - retry/escalation control
  - persistence and observability linkage

## 2. Recommended Scope Boundary

### Include
- Stage 2, Stage 3, Stage 4 process surfaces
- Chief Writer, Director, pre-director validation, retry and escalation modules
- persistence and carry-over surfaces when they affect process quality
- dashboard/observability surfaces only insofar as they explain or distort process integrity
- process-related docs already created on 2026-03-17

### Exclude
- broad desktop/UI/product review
- unrelated scripts or infrastructure unless they directly shape Stage pipeline process semantics
- narrative-production content quality review by `work_id`
- immediate patch realization

## 3. Governing Harness Path
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- optional:
  - `docs/implementation/single-ssot-roadmap-contract.md`
  - `docs/implementation/evidence-triangulation-contract.md`
  - `docs/implementation/integrity-confidence-scoring-contract.md`

## 4. Recommended Survey Question Set

### 4.1 Context
- does CW receive the right context at the right time and in the right density
- are retrieval and mandatory-context composition ranked by process importance or just accumulated

### 4.2 Authority
- are Python, Director, advisory modules, and supporting agents staying within clean authority boundaries
- where do "reference only" surfaces become de facto decision surfaces

### 4.3 Gate Semantics
- are verdict, score, advisory, fix scope, and retry routing semantically separated well enough
- where does one field currently carry too many meanings

### 4.4 Repair And Retry
- when is local repair truly justified
- how are round budget, repair budget, escalation budget, and guidance budget currently shaped

### 4.5 Observability
- can operators reconstruct why a manuscript passed, failed, patched, retried, or escalated
- are process traces aligned with real decision boundaries

## 5. Proposed Survey Outputs
- one bounded master survey doc in `docs/YYYY-MM-DD/`
- one aggregate roadmap only if the survey identifies multiple realization lanes worth queueing
- optional supporting evidence manifests or tranche docs if the surface is too large for one coherent writeup
- no temp execution mirror unless the survey genuinely crosses into execution planning

## 6. Recommended Working Model

### Phase A. Map
- produce a cross-cutting map of Stage pipeline process surfaces
- identify shared hotspots and repeated semantic overloads

### Phase B. Cluster
- cluster findings into a small number of action lanes
- preferred shape:
  - context architecture
  - gate semantics
  - repair/retry architecture

### Phase C. Rank
- rank action lanes by process ROI and implementation risk
- prefer fewer high-leverage lanes over many narrow fixes

### Phase D. Stop
- stop at survey and survey-derived prioritization unless explicitly told to open execution

## 7. Reusable Order Wording

### Compact Version
```text
시스템 오더다. AGENTS.md와 system-order init harness를 따른 뒤, ROL 전역 전체 전수조사만 수행하라.

이번 조사는 repo-wide이되 무제한 full survey가 아니다. 주제는 Stage pipeline process integrity로 제한한다.

조사 초점:
- Stage 2~4 context flow
- CW/Director/validator/advisory authority boundary
- verdict/score/fix_scope/advisory/retry semantics
- PASS_WITH_FIX local repair contract
- retry/escalation budget policy
- persistence/observability linkage

구현은 하지 말고 survey-only로 멈춰라.
산출물은 docs/YYYY-MM-DD/ 아래 canonical survey 문서 기준으로 정리하라.
가능하면 기존 2026-03-17 planning note 묶음을 survey hypothesis seed로 사용하되, live code authority를 우선하라.

최종 보고는:
1. survey scope
2. global process map
3. high-severity semantic overlaps
4. high-ROI action lanes
5. execution queue 필요 여부
형식으로 정리하라.
```

### Higher-Rigor Version
```text
시스템 오더다. AGENTS.md -> system-order init harness -> system-full-survey-execution-harness -> codebase-global-survey-coverage-contract -> deep-global-integrity-survey-harness 순서로 따르라.

모드는 ROL 전역 전체 전수조사만이다. 구현/패치/실행문서 실현으로 넘어가지 말고 survey-only에서 멈춰라.

이번 조사 주제는 Stage pipeline process integrity다. 범위는 Stage 2/3/4 process architecture, Chief Writer, Director, pre-director validation, retry/escalation, persistence, process observability까지 포함한다. UI/desktop/product 전역 감사로 확장하지 마라.

핵심 질문:
- CW pre-write context가 timing, density, ranking 면에서 적절한가
- retrieval/context composition이 좋은 원고보다 문맥 누적에 치우쳐 있지 않은가
- Director prompt가 decision core와 reference appendix를 구분하고 있는가
- verdict/score/advisory/fix_scope/retry routing이 semantic overload 없이 분리되어 있는가
- PASS_WITH_FIX가 truly local repair contract로 쓰이고 있는가
- retry budget이 round, repair, strategy, escalation, guidance 축으로 읽히는가
- persistence와 observability가 실제 process state를 복원 가능하게 남기고 있는가

산출물:
- docs/YYYY-MM-DD/ canonical master survey 1건
- 필요 시 supporting tranche survey docs
- execution SSOT/roadmap은 survey 결과상 action lane이 실제로 여러 개 남고 realization 필요성이 확인될 때만 작성

조사 중에는 live code authority > stale survey text 원칙을 지켜라.
최종 결론은 Fact / Inference / Decision을 분리해 적어라.
```

## 8. Why This Order Has Better ROI Than Another Narrow Brainstorm
- it uses the six existing 2026-03-17 planning notes as hypothesis seeds rather than final truth
- it can reveal whether several "separate" improvements are really one or two deeper architecture problems
- it prevents premature patching before the shared process map is understood
- it creates a stronger base for any future execution SSOT

## 9. Interaction With Existing Draft Notes
- `cw-context-delivery-optimization-outline.md`
- `stage4-context-composition-ranking-outline.md`
- `quality-gate-semantics-outline.md`
- `pass-with-fix-local-repair-contract-outline.md`
- `director-prompt-austerity-outline.md`
- `retry-budget-policy-outline.md`

These should be treated as brainstorming seeds, not authoritative findings.

## 10. Recommended Stop Line
- if the survey starts drifting into file-by-file micro-remediation, stop and re-center on process architecture
- if the survey starts expanding into unrelated desktop/UI/runtime territory, stop and re-bound scope
- if realization lanes become obvious, record them, but do not implement them during the same order unless explicitly instructed

## 11. Open Questions To Resume Later
- whether the bounded global survey should produce one master survey only or one master survey plus a small number of tranche docs
- whether Director-side and CW-side context architecture should remain one shared lane or split into two lanes
- whether retry budget and PASS_WITH_FIX should stay in one repair-policy lane or split into semantics vs execution-control lanes
