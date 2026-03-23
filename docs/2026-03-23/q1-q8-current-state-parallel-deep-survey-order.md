Date: 2026-03-23
Status: final (3-pass audited)
Document Type: parallel deep global survey order
Canonical Path: `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md`
Temp Mirror Path: none

## 1. Purpose

이 오더는 `Q1~Q8` 축 기준 현황 파악 전수조사를 위한 `8터미널 병렬 Opus TF 조사` 오더다.

목적은 세 가지다.
- 현재 live workspace 기준으로 `Q1~Q8` 품질/위험/관측성 상태를 축별로 다시 파악한다.
- 이미 수행한 fresh run 실패 원인 중 `LLM-Director 정합성 불일치`를 코드 수정 ROI 기준으로 재정렬한다.
- 조사 결과를 바탕으로 Codex가 merge-audit 후 bounded execution SSOT로 승격할 action-bearing finding만 추린다.

이 문서는 조사 오더다. 구현 오더가 아니다.

## 2. Start Gate

이 병렬 조사는 아래 조건을 전제로 한다.
- `console-log-max-display-post-audit-execution-ssot` realization과 Codex closure audit이 완료된 뒤 시작한다.
- fresh run은 이미 1회 수행되었고, `LLM-Director 정합성 불일치` 때문에 재실행 ROI보다 `정확한 전수조사 + 수정` ROI가 더 높다고 본다.
- 따라서 이번 wave에서는 fresh run을 다시 돌리지 않는다. live rerun은 `조사 -> merge-audit -> code fix` 이후 단계다.

## 3. Hard Constraints

- 조사 전용. 코드 수정 금지.
- execution SSOT 생성 금지. Opus는 execution backlog를 제안만 하고 만들지 않는다.
- `docs/temp/` queue artifact 생성 금지.
- 기존 문서 status 임의 변경 금지.
- `console-log` / `db-logging` active item을 닫지 않는다.
- fresh run 재실행 금지.
- verdict policy, threshold, retry, swap semantics에 대한 구현 제안은 가능하되, 적용은 금지.
- 각 finding은 반드시 `file:line` anchor와 `fix type`을 가져야 한다.

## 4. Survey Axes

| Axis | 질문 | 핵심 초점 |
|---|---|---|
| Q1 | 잘 쓰냐 | first-pass generation quality, ensemble collapse, selection bias |
| Q2 | 잘 고치냐 | fix/retry loop quality, patch convergence, retry cost |
| Q3 | 잘 판단하냐 | PASS/REJECT correctness, gate chain, director verdict accuracy |
| Q4 | 잘 설명하냐 | reject/fix feedback quality, instruction handoff, explanation fidelity |
| Q5 | 잘 기억하냐 | long-run consistency, WorldState/FactLedger/StateTracker alignment |
| Q6 | 잘 찾냐 | selective retrieval, routing quality, vector/db/slot coverage |
| Q7 | 잘 받냐 | context reception, prompt injection completeness, truncation/order problems |
| Q8 | 잘 로깅하냐 | console/DB/audit observability, max display, max retention, sink parity |

## 5. Terminal Plan

모든 터미널은 `Opus TF` 1개씩 사용한다. 총 8개 터미널을 전제로 한다.

| Terminal | Axis | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | Q1 | `chief_writer.py`, `arc_ensemble.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py` | `docs/2026-03-23/opus/q1-generation-quality-deep-dive.md` | `docs/2026-03-23/opus/q1-generation-quality-evidence-manifest.md` |
| T2 | Q2 | `stage4_retry_runtime.py`, `stage2_finalizer.py`, `chief_writer.py`, `three_phase_blueprint_runtime.py` | `docs/2026-03-23/opus/q2-fix-retry-deep-dive.md` | `docs/2026-03-23/opus/q2-fix-retry-evidence-manifest.md` |
| T3 | Q3 | `director_ensemble.py`, `director_auditor.py`, `stage4_director_runtime.py`, `stage4_interview_round.py`, `four_phase_arc_runtime.py` | `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md` | `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md` |
| T4 | Q4 | `stage4_reject_runtime.py`, `stage2_finalizer.py`, `director_auditor.py`, `stage3_orchestrator.py` | `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md` | `docs/2026-03-23/opus/q4-feedback-loop-evidence-manifest.md` |
| T5 | Q5 | `world_state.py`, `fact_ledger.py`, `modules/domain/agents/state_tracker.py`, `state_tracker_npc.py`, `continuity_validator.py`, `continuity_arc.py` | `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md` | `docs/2026-03-23/opus/q5-long-term-consistency-evidence-manifest.md` |
| T6 | Q6 | `vec_memory.py`, `context_advisor.py`, `stage4_context_builder.py`, `stage4_context_packets.py` | `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md` | `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md` |
| T7 | Q7 | `chief_writer_context.py`, `chief_writer_context_packets.py`, `stage4_context_builder.py`, `stage4_context_packets.py`, `prompt_builder.py`, `base_agent.py` | `docs/2026-03-23/opus/q7-context-reception-deep-dive.md` | `docs/2026-03-23/opus/q7-context-reception-evidence-manifest.md` |
| T8 | Q8 | `director_ensemble.py`, `stage4_interview_round.py`, `stage4_director_runtime.py`, `stage2_finalizer.py`, `stage3_orchestrator.py`, `db_manager.py`, `logger.py`, `pass_rate_monitor.py`, `metrics_collector.py` | `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md` | `docs/2026-03-23/opus/q8-logging-retention-evidence-manifest.md` |

## 6. Output Contract

각 터미널은 아래 원칙으로 저장한다.

### 6.1 Final Report
- 경로: 각 터미널별 `Final Report Path`
- 형식: human-readable markdown
- 상태: `final` 또는 `provisional`
- confidence 95% 미만이면 반드시 `provisional`

### 6.2 Optional Evidence Manifest
- 경로: 각 터미널별 `Optional Evidence Path`
- 목적: rg output, path inventory, source anchor list, live trace note 같은 raw/near-raw evidence 저장
- interpretation 문서는 아님

### 6.3 No Temp Queue Artifacts
- 이번 wave는 survey-only다.
- `docs/temp/`에 execution SSOT, roadmap, queue item을 생성하지 않는다.
- Opus는 조사 결과만 저장한다.

### 6.4 Codex Merge Layer
- Opus 8개 보고서가 완료되면, Codex가 다음 산출물을 만든다:
  - `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
  - 필요한 경우 bounded execution SSOT들
- 이 merge 문서는 Opus가 만들지 않는다.

## 7. Mandatory Report Structure

각 터미널 보고서는 아래 구조를 따른다.

1. Executive Summary
2. Current Ownership / Flow Map
3. Top Hotspots
4. Quick Wins
5. Boundary Refactor Candidates
6. Fresh-Run Relevance
7. Confidence And Limits

핵심 규칙:
- 모든 P0/P1 finding은 `file:line` anchor 필수
- 모든 권고는 `fix type` 필수
- `fix type` allowed set:
  - `comment-only`
  - `doc-only`
  - `observability-only`
  - `contract-cleanup`
  - `boundary-refactor`
  - `ignore`

## 8. Fresh-Run Relevance Rule

이번 조사 wave는 이미 한 번 실패한 fresh run을 전제로 한다.

따라서 각 터미널은 반드시 아래를 판정해야 한다.
- 이번 축의 finding 중 `fresh run 재시도 전에 먼저 고쳐야 하는 것`은 무엇인가
- 그 이유가 `LLM-Director 정합성 불일치`, `관측성 부족`, `컨텍스트 손실`, `retrieval fault`, `consistency drift` 중 어디에 가까운가

각 보고서에는 반드시 이 한 줄이 들어가야 한다.
- `Fresh-run-before-fix allowed: yes/no`

## 9. Opus Launch Prompt

아래 프롬프트를 각 터미널에서 사용한다. `AXIS_NAME`, `PRIMARY_SCOPE`, `FINAL_REPORT_PATH`, `EVIDENCE_PATH`만 터미널별로 바꾼다.

```text
System-track survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md
4. docs/2026-03-23/daily-roadmap-2026-03-23.md
5. docs/2026-03-23/current-state-situation-survey-report.md
6. docs/2026-03-23/fresh-run-3pass-audit-report.md
7. docs/2026-03-23/llm-codebase-orientation-pack.md
8. docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md
9. docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md

Task:
Run a bounded deep-dive survey for AXIS_NAME over the current live workspace state.

Hard constraints:
- Survey-only. No code changes.
- Do not create execution SSOTs.
- Do not create docs/temp queue artifacts.
- Do not rerun fresh live paths.
- Prefer live source over stale report wording.
- If an older report claim is already fixed in live code, mark it stale instead of repeating it.

Primary scope:
PRIMARY_SCOPE

Required output:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Current Ownership / Flow Map
3. Top Hotspots
4. Quick Wins
5. Boundary Refactor Candidates
6. Fresh-Run Relevance
7. Confidence And Limits

Rules:
- Every P0/P1 finding must have file:line anchors.
- Every recommendation must have one fix type:
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - ignore
- Explicitly state:
  - Fresh-run-before-fix allowed: yes/no
  - Top 3 highest-ROI code fixes before next fresh run

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH
- python scripts/ops_validator.py

In your final response:
- summarize top findings first
- then confidence
- then the 3 highest-ROI fixes
- keep it concise
```

## 10. Terminal Overrides

| Terminal | AXIS_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Q1 generation quality` | `chief_writer.py, arc_ensemble.py, blueprint_ensemble.py, three_phase_blueprint_generator.py` | `docs/2026-03-23/opus/q1-generation-quality-deep-dive.md` | `docs/2026-03-23/opus/q1-generation-quality-evidence-manifest.md` |
| T2 | `Q2 fix/retry quality` | `stage4_retry_runtime.py, stage2_finalizer.py, chief_writer.py, three_phase_blueprint_runtime.py` | `docs/2026-03-23/opus/q2-fix-retry-deep-dive.md` | `docs/2026-03-23/opus/q2-fix-retry-evidence-manifest.md` |
| T3 | `Q3 verdict accuracy` | `director_ensemble.py, director_auditor.py, stage4_director_runtime.py, stage4_interview_round.py, four_phase_arc_runtime.py` | `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md` | `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md` |
| T4 | `Q4 feedback loop quality` | `stage4_reject_runtime.py, stage2_finalizer.py, director_auditor.py, stage3_orchestrator.py` | `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md` | `docs/2026-03-23/opus/q4-feedback-loop-evidence-manifest.md` |
| T5 | `Q5 long-term consistency` | `world_state.py, fact_ledger.py, modules/domain/agents/state_tracker.py, state_tracker_npc.py, continuity_validator.py, continuity_arc.py` | `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md` | `docs/2026-03-23/opus/q5-long-term-consistency-evidence-manifest.md` |
| T6 | `Q6 selective retrieval` | `vec_memory.py, context_advisor.py, stage4_context_builder.py, stage4_context_packets.py` | `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md` | `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md` |
| T7 | `Q7 context reception` | `chief_writer_context.py, chief_writer_context_packets.py, stage4_context_builder.py, stage4_context_packets.py, prompt_builder.py, base_agent.py` | `docs/2026-03-23/opus/q7-context-reception-deep-dive.md` | `docs/2026-03-23/opus/q7-context-reception-evidence-manifest.md` |
| T8 | `Q8 logging / retention observability` | `director_ensemble.py, stage4_interview_round.py, stage4_director_runtime.py, stage2_finalizer.py, stage3_orchestrator.py, db_manager.py, logger.py, pass_rate_monitor.py, metrics_collector.py` | `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md` | `docs/2026-03-23/opus/q8-logging-retention-evidence-manifest.md` |

## 10A. Terminal Dispatch One-Liners

아래 문구를 그대로 복붙해서 각 Opus TF에 배포하면 된다.

- `넌 1번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T1 규칙대로 진행해.`
- `넌 2번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T2 규칙대로 진행해.`
- `넌 3번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T3 규칙대로 진행해.`
- `넌 4번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T4 규칙대로 진행해.`
- `넌 5번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T5 규칙대로 진행해.`
- `넌 6번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T6 규칙대로 진행해.`
- `넌 7번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T7 규칙대로 진행해.`
- `넌 8번 터미널. docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md를 읽고 T8 규칙대로 진행해.`

## 11. Codex Merge Rule

Opus가 조사 결과를 저장한 후, Codex가 아래 순서로 감리한다.
- stale finding 제거
- cross-axis 중복 병합
- fresh-run relevance 재정렬
- action-bearing finding만 execution SSOT 승격

즉, Opus는 `수집 + 축별 deep-dive`, Codex는 `감리 + merge + 실행문서화`를 맡는다.

## 12. 3-Pass Audit Record

- Pass 1
  - current roadmap, fresh-run note, current-state situation report, active observability items를 반영해 조사 범위를 `Q1~Q8`으로 재정의했다
- Pass 2
  - 8터미널 병렬 구조, 저장 경로, evidence manifest 경로, Codex merge layer를 고정했다
- Pass 3
  - fresh run 재실행 금지, temp queue artifact 금지, survey-only 저장 규칙을 다시 검증했다

## 13. Confidence

- Confidence: 97%
- Basis:
  - 현재 workspace 운영 모드와 충돌하지 않는 survey-only 오더
  - 8개 터미널의 역할, 저장 경로, Codex 후속 merge responsibility가 분리되어 있음
  - fresh run 재시도보다 survey -> fix -> rerun의 ROI 우선순위를 명시함
