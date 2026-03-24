Date: 2026-03-24
Status: final (3-pass audited)
Document Type: parallel LLM-friendliness survey master order
Canonical Path: `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-24/현상황요약.txt`

Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer surfaces, docs/temp/queue-state.json, docs/2026-03-23/console.txt, many project artifacts deleted, new docs/2026-03-24/ and stage4 immutable-fact files`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

이 문서는 `ROL 전수조사`를 `LLM 친화도` 중심으로 다시 수행하기 위한 `Opus TF 6터미널 병렬 마스터 오더`다.

목적은 네 가지다.
- 현재 live workspace 기준으로 `LLM이 읽고, 찾고, 판단하고, 수정하기 쉬운가`를 다시 측정한다.
- 이미 닫힌 comment/doc/observability 후속 조치와 아직 남은 이해 비용을 분리한다.
- 리팩토링을 장기 과제로 뒤로 미루고, 이번 wave에서는 `comment/doc/observability/contract clarity`를 우선 논의한다.
- Opus는 lane별 수집과 저장까지만 맡고, Codex가 merge-audit와 후속 실행문서 판정을 맡는다.

이 문서는 조사 오더다. 구현 오더가 아니다.

## 2. Current Frame

이번 wave는 아래 현재 상태를 전제로 한다.

- `docs/2026-03-23/llm-codebase-orientation-pack.md`는 현재도 유효한 lightweight navigation map이다.
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`에서 low-blast comment/doc/observability follow-up은 이미 반영되고 닫혔다.
- 따라서 이번 조사는 `이미 해결된 quick win 재발굴`이 아니라 `현재도 남아 있는 이해 비용, stale claim 정리, lane별 residual hotspot 재등급`이 핵심이다.
- `docs/temp/`에는 active execution queue artifact가 남아 있다.
  - `docs/temp/stage4-immutable-fact-convergence-execution-ssot.md`
  - `docs/temp/queue-state.json`
- 이번 survey wave에서는 위 temp queue를 건드리지 않는다.

## 3. Hard Constraints

- survey-only. 코드 수정 금지.
- execution SSOT, roadmap, temp queue artifact 생성 금지.
- 기존 `docs/temp/` active item 수정 금지.
- `queue-state.json` status 변경 금지.
- live workspace evidence를 우선하고, stale survey wording은 낮은 authority로 본다.
- `100+ LOC`, `owner class pressure`, `long function residue` 자체를 이번 wave의 주된 논점으로 확대하지 않는다.
- `boundary-refactor`는 기록 가능하지만 장기 과제로 분리한다.
- 모든 P0/P1 finding은 반드시 `file:line` anchor를 가져야 한다.
- 모든 권고는 반드시 `fix type`을 가져야 한다.

## 4. LLM-Friendliness Survey Model

이번 조사에서 모든 finding은 아래 5축 중 하나 이상에 매핑한다.

| Axis | 질문 | 핵심 초점 |
|---|---|---|
| Navigation | cold LLM이 어디서 읽기 시작해야 하는가 | entrypoint, reading order, stale map |
| Authority | 최종 owner를 빨리 찾을 수 있는가 | owner shell, runtime authority, sink owner |
| Contract | payload와 field meaning이 빠르게 해석되는가 | dict/dataclass/result schema, envelope meaning |
| Observability | `무슨 일이 일어났는지`를 추적할 수 있는가 | console, audit, DB, metrics, JSONL parity |
| Local Readability | 로컬 코드 블록이 오해 없이 읽히는가 | comments, naming honesty, mutation visibility |

## 5. Refactor De-Prioritization Rule

이번 wave는 리팩토링 long-list를 만드는 자리가 아니다.

- lane report의 기본 우선순위는 아래 순서다.
  1. `comment-only`
  2. `doc-only`
  3. `observability-only`
  4. `contract-cleanup`
  5. `boundary-refactor`
  6. `ignore`
- `boundary-refactor`는 `cheap fix로는 이해 비용이 줄지 않는다`는 근거가 있을 때만 적는다.
- 각 터미널은 `Top Quick Wins`를 최소 5개 이상 적되, 그중 과반은 `comment/doc/observability`여야 한다.
- 각 터미널은 `Deferred Refactor Candidates`를 최대 3개까지만 적는다.
- `long-term` 또는 `defer` 표기가 없는 refactor 제안은 금지한다.

## 6. Terminal Plan

모든 터미널은 `Opus TF` 1개씩 사용한다. 총 6개 터미널을 전제로 한다.

| Terminal | Lane | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | Navigation / Entry / Reading Order | `main_a.py`, `stage01_helpers.py`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `stage4_orchestrator.py`, `modules/api/**/*.py`, orientation pack authority/read-order drift | `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry.md` | `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry-evidence.md` |
| T2 | Stage 4 Authority / Verdict Flow | `stage4_interview_round.py`, `stage4_director_runtime.py`, `stage4_post_processor.py`, `stage4_post_pass_runtime.py`, `stage4_reject_runtime.py`, `stage4_retry_runtime.py`, `director_ensemble.py` | `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md` | `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict-evidence.md` |
| T3 | Writer / Prompt / Context Reception | `chief_writer.py`, `chief_writer_context.py`, `chief_writer_context_packets.py`, `chief_writer_prompts.py`, `writer_template.py`, `prompt_builder.py`, `stage4_context_builder.py`, `stage4_context_packets.py` | `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt.md` | `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt-evidence.md` |
| T4 | Contract / Validation / Envelope Surface | `validation_orchestrator.py`, validator family, `four_phase_arc_runtime.py`, `three_phase_blueprint_runtime.py`, `pre_director_checklist.py`, `blueprint_constraint_compiler.py`, `base_agent.py` | `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope.md` | `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope-evidence.md` |
| T5 | Persistence / Observability / Operator Truth | `db_manager.py`, `pass_rate_monitor.py`, `logger.py`, `metrics_collector.py`, Stage 2/3 sink writers, audit/session/jsonl surfaces, operator-visible logs | `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability.md` | `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability-evidence.md` |
| T6 | Peripheral Surface / Regression / No-Action Sweep | `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, `docs/implementation/`, `AGENTS.md`, stale authority/reference sweep, already-settled zone collection | `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction.md` | `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction-evidence.md` |

## 7. Lane Questions

각 터미널은 자기 lane에서 아래 질문에 답해야 한다.

### T1. Navigation / Entry / Reading Order
- cold LLM이 어디서 시작해야 하는지가 현재도 명확한가
- orientation pack reading order가 live code 기준 stale인지 아닌지
- thin delegate, compat shell, entry-router noise가 잘못된 수정 경로를 만들 가능성이 있는가

### T2. Stage 4 Authority / Verdict Flow
- Stage 4에서 최종 owner와 mutation boundary를 빠르게 찾을 수 있는가
- verdict chain, retry chain, post-pass settlement가 LLM에게 과도한 search cost를 요구하는가
- implicit channel이나 hidden state transfer가 잘못된 reasoning을 유발하는가

### T3. Writer / Prompt / Context Reception
- Writer prompt와 context packet 구조가 LLM 관점에서 해석 가능한가
- truncation, packet assembly, prompt section order가 comprehension cost를 키우는가
- Writer-side quick win이 refactor 없이 comment/doc/contract note로 줄어드는가

### T4. Contract / Validation / Envelope Surface
- tier result schema, envelope, validator result contract가 빨리 해석되는가
- field meaning이나 payload shape가 file hop 과다를 유발하는가
- long-term refactor 없이 contract note나 schema map으로 해결 가능한가

### T5. Persistence / Observability / Operator Truth
- console / DB / audit / metrics / jsonl에서 `what happened`와 `why`를 쉽게 역추적할 수 있는가
- write owner와 sink owner가 분명한가
- operator-visible truth와 durable truth 사이의 해석 비용이 큰가

### T6. Peripheral Surface / Regression / No-Action Sweep
- scripts/tests/UI/desktop/governance surface가 LLM 진입 비용을 높이는가
- stale authority 문서나 misleading helper 이름이 남아 있는가
- 어떤 영역은 이미 settled/no-action으로 고정해야 과잉 논의를 막을 수 있는가

## 8. Output Contract

각 터미널은 자기 final report 1개와 optional evidence manifest 1개만 저장한다.

### 8.1 Final Report
- 경로: 각 터미널별 `Final Report Path`
- 형식: human-readable markdown
- 상태:
  - confidence `95%` 이상이면 `final`
  - confidence `95%` 미만이면 `provisional`
- 문서 저장 전 3-pass audit 수행

### 8.2 Optional Evidence Manifest
- 경로: 각 터미널별 `Optional Evidence Path`
- 목적: raw path inventory, rg anchor list, short evidence ledger
- interpretation 문서는 아님

### 8.3 No Temp Queue Artifacts
- 이번 wave는 survey-only다.
- `docs/temp/`에 execution SSOT, roadmap, queue item을 만들지 않는다.
- active temp queue item도 수정하지 않는다.

### 8.4 Codex Merge Layer
Opus 6개 보고서가 완료되면 Codex가 아래 문서를 만든다.

- `docs/2026-03-24/rol-llm-friendliness-6terminal-merge-audit.md`

Opus는 merge 문서를 만들지 않는다.

## 9. Mandatory Report Structure

각 터미널 보고서는 아래 구조를 따른다.

1. Executive Summary
2. Included Coverage / Exclusions
3. Current Read Order or Ownership Map
4. Top Hotspots
5. Top Quick Wins
6. Deferred Refactor Candidates
7. No-Action / Settled Areas
8. Cross-Lane Handoff Notes
9. Confidence And Limits

핵심 규칙:
- 모든 P0/P1 finding은 `file:line` anchor 필수
- 모든 권고는 `fix type` 필수
- allowed `fix type`
  - `comment-only`
  - `doc-only`
  - `observability-only`
  - `contract-cleanup`
  - `boundary-refactor`
  - `ignore`
- 각 report는 반드시 아래 3줄을 명시한다.
  - `Navigation-ready for this lane: yes/no`
  - `Cheap-fix-first verdict: yes/no`
  - `Boundary-refactor can wait: yes/no`

## 10. Read Order

모든 터미널은 아래 문서를 먼저 읽는다.

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/codebase-global-survey-coverage-contract.md`
5. `docs/implementation/deep-global-integrity-survey-harness.md`
6. `docs/implementation/document-3pass-audit-harness.md`
7. `docs/2026-03-23/llm-codebase-orientation-pack.md`
8. `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`
9. `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
10. `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
11. `docs/2026-03-24/현상황요약.txt`
12. `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`

## 11. Opus Launch Prompt

아래 프롬프트를 공통으로 쓰고, `LANE_NAME`, `PRIMARY_SCOPE`, `FINAL_REPORT_PATH`, `EVIDENCE_PATH`만 terminal별로 바꾼다.

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/codebase-global-survey-coverage-contract.md
5. docs/implementation/deep-global-integrity-survey-harness.md
6. docs/implementation/document-3pass-audit-harness.md
7. docs/2026-03-23/llm-codebase-orientation-pack.md
8. docs/2026-03-23/opus-llm-friendliness-global-survey-order.md
9. docs/2026-03-23/opus-llm-friendliness-global-survey-report.md
10. docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md
11. docs/2026-03-24/현상황요약.txt
12. docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md

Task:
Run a bounded LLM-friendliness survey for LANE_NAME over the current live workspace state.

Primary goal:
Assess whether this lane is easy for an LLM to navigate, reason about, and modify safely without reopening a broad refactor wave.

Hard constraints:
- Survey-only. No code changes.
- Do not create execution SSOTs or docs/temp queue artifacts.
- Do not modify docs/temp/stage4-immutable-fact-convergence-execution-ssot.md or docs/temp/queue-state.json.
- Prefer live workspace evidence over stale report wording.
- Do not reopen the long-function campaign as the main story.
- Treat refactor as long-term. Prefer comment/doc/observability quick wins first.

Primary scope:
PRIMARY_SCOPE

Required output:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Current Read Order or Ownership Map
4. Top Hotspots
5. Top Quick Wins
6. Deferred Refactor Candidates
7. No-Action / Settled Areas
8. Cross-Lane Handoff Notes
9. Confidence And Limits

Rules:
- Every P0/P1 finding must have file:line anchors.
- Every recommendation must have one fix type:
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - ignore
- Top Quick Wins must contain at least 5 items.
- More than half of Top Quick Wins must be comment/doc/observability items.
- Deferred Refactor Candidates must be capped at 3 and explicitly marked long-term or defer.
- Explicitly state:
  - Navigation-ready for this lane: yes/no
  - Cheap-fix-first verdict: yes/no
  - Boundary-refactor can wait: yes/no
  - Top 3 highest-ROI quick wins in this lane

Document save rule:
- Run a document 3-pass audit before saving.
- If confidence is 95% or higher, save status as final.
- If confidence is below 95%, save status as provisional.

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH

In your final response:
- summarize top findings first
- then confidence
- then the top 3 quick wins
- keep it concise
```

## 12. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Navigation / Entry / Reading Order` | `main_a.py, stage01_helpers.py, stage2_orchestrator.py, stage3_orchestrator.py, stage4_orchestrator.py, modules/api/**/*.py, orientation-pack drift` | `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry.md` | `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry-evidence.md` |
| T2 | `Stage 4 Authority / Verdict Flow` | `stage4_interview_round.py, stage4_director_runtime.py, stage4_post_processor.py, stage4_post_pass_runtime.py, stage4_reject_runtime.py, stage4_retry_runtime.py, director_ensemble.py` | `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md` | `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict-evidence.md` |
| T3 | `Writer / Prompt / Context Reception` | `chief_writer.py, chief_writer_context.py, chief_writer_context_packets.py, chief_writer_prompts.py, writer_template.py, prompt_builder.py, stage4_context_builder.py, stage4_context_packets.py` | `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt.md` | `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt-evidence.md` |
| T4 | `Contract / Validation / Envelope Surface` | `validation_orchestrator.py, validator family, four_phase_arc_runtime.py, three_phase_blueprint_runtime.py, pre_director_checklist.py, blueprint_constraint_compiler.py, base_agent.py` | `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope.md` | `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope-evidence.md` |
| T5 | `Persistence / Observability / Operator Truth` | `db_manager.py, pass_rate_monitor.py, logger.py, metrics_collector.py, stage2_finalizer.py, stage3_orchestrator.py, audit/session/jsonl/metrics sinks` | `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability.md` | `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability-evidence.md` |
| T6 | `Peripheral Surface / Regression / No-Action Sweep` | `scripts/, tests/, UI/, geuldobi-desktop/, docs/implementation/, AGENTS.md, stale authority/reference sweep, already-settled zone collection` | `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction.md` | `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction-evidence.md` |

## 13. Terminal Dispatch One-Liners

아래 문구를 그대로 복붙하면 된다. 사용 형식은 `경로 + 넌 n번 터미널`이다.

- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 1번 터미널. T1 규칙대로 진행해.`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 2번 터미널. T2 규칙대로 진행해.`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 3번 터미널. T3 규칙대로 진행해.`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 4번 터미널. T4 규칙대로 진행해.`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 5번 터미널. T5 규칙대로 진행해.`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md + 넌 6번 터미널. T6 규칙대로 진행해.`

## 14. Codex Merge Rule

Opus는 `lane 조사와 저장`까지만 한다.

Codex가 그 다음을 맡는다.
- stale finding 제거
- cross-lane 중복 병합
- comment/doc/observability vs contract-cleanup vs long-term refactor 재정렬
- 이미 닫힌 2026-03-23 follow-up과 새 finding 분리
- merge-audit 작성
- 필요 시에만 execution SSOT 승격

즉, Opus는 `수집 + lane 보고서`, Codex는 `감리 + merge + 실행문서 판정`을 맡는다.

## 15. 3-Pass Audit Record

- Pass 1
  - 문서 타입을 `parallel survey master order`로 고정했고, implementation authority를 배제했다.
- Pass 2
  - 6개 lane scope, 저장 경로, active temp queue 비간섭 규칙, embedded launch prompt 정합성을 점검했다.
- Pass 3
  - refactor 후순위 원칙, path-first dispatch 문구, Codex merge responsibility를 다시 확인했다.

## 16. Confidence

- Confidence: 98%
- Basis:
  - current orientation pack, prior LLM-friendliness survey, post-survey execution SSOT, current summary를 함께 반영했다.
  - 6개 lane이 entry/navigation, stage4 authority, writer/context, contract/validation, persistence/observability, peripheral/regression을 중복 과다 없이 덮는다.
  - 리팩토링 장기 과제화와 active temp queue 비간섭 원칙이 명시돼 있어 이번 wave 목적과 충돌하지 않는다.
