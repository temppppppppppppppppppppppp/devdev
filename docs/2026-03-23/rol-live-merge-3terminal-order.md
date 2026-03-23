Date: 2026-03-23
Status: final (3-pass audited)
Document Type: ROL live-merge parallel survey order
Canonical Path: `docs/2026-03-23/rol-live-merge-3terminal-order.md`
Temp Mirror Path: none
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Baseline Dirty Summary: `dirty workspace with Stage 4 bottleneck fixes, live fresh-run artifacts, and survey/doc backlog already present`
Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Resume Drift Summary: `same HEAD; fresh run is active, queue is empty, and this order is for survey-only live-merge parallel investigation`
Source Survey Docs:
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/q1-q8-r2-merge-audit.md`
- `docs/2026-03-23/rol-global-survey-3terminal-order.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- live fresh-run DB / JSONL / artifact outputs under `projects/00_00/`
Side-Effect Coverage:
- artifact truth: yes
- DB truth: yes
- console/operator truth: yes
- JSONL/metrics truth: yes
- temp queue impact: no

## 1. Purpose

이 문서는 `fresh run 진행 중 + ROL Opus 전수조사 병행`을 위한 `3터미널 live-merge survey-only` 공통 오더다.

목적은 아래 4가지다.
- live workspace와 현재 fresh-run evidence를 함께 보면서 정적 조사와 실전 evidence를 병행한다.
- stale survey wording과 현재 run evidence를 분리한다.
- Opus는 lane별 조사와 저장만 수행한다.
- run 종료 후 Codex가 merge-audit를 수행하고, 그 다음에만 실행문서나 수정 우선순위를 확정한다.

이 문서는 구현 오더가 아니다.

## 2. Live-Merge Rules

- fresh run이 아직 진행 중이면 lane 보고서는 `draft-live-run-pending`로 저장한다.
- fresh run이 terminal state(`completed / failed / stopped / aborted`)에 도달하기 전에는 final closure claim 금지.
- mid-run DB/log/artifact state는 provisional evidence로 취급한다.
- completed live-run evidence가 static inference보다 우선한다.
- stale survey text는 live code와 live evidence보다 낮은 authority를 가진다.

## 3. Hard Constraints

- survey-only. 코드 수정 금지.
- execution SSOT 생성 금지.
- `docs/temp/` queue artifact 생성 금지.
- temp queue / roadmap / queue-state 수정 금지.
- fresh run stop / restart / rerun 금지.
- 현재 run evidence를 final truth로 과장 금지.
- prior stale claim은 live code나 live evidence가 반박하면 stale로 표기.
- 모든 P0/P1 provisional finding은 `file:line` 또는 `artifact path + line/section` anchor 필요.
- 모든 actionable finding은 `fix type` 필요.

## 4. Coverage Model

이번 live-merge 조사는 3개 lane으로 분리한다.

- `T1 Runtime / Artifact Flow`
  - Stage 2/3/4 runtime spine
  - generation -> selection -> writer -> retry 흐름
  - blueprint/manuscript artifact truth
- `T2 Verdict / Persistence / Operator`
  - Director / post-select / retry verdict chain
  - DB / JSONL / session logger / console parity
  - failure classification and operator provenance
- `T3 Contracts / Context / Regression`
  - context reception / retrieval / contract seams
  - config / bootstrap / test / regression surfaces
  - long-run risk and rerun-relevance

## 5. Output Contract

각 터미널은 자기 final report 1개와 optional evidence manifest 1개만 저장한다.

주의:
- fresh run이 아직 active이면 report `Status`는 반드시 `draft-live-run-pending`
- run이 해당 lane 조사 중 이미 terminal state가 되더라도, Opus는 자기 lane report만 저장하고 merge 문서는 만들지 않는다.

### 5.1 Terminal Reports

| Terminal | Lane | Final Report Path | Optional Evidence Path |
|---|---|---|---|
| T1 | Runtime / Artifact Flow | `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md` | `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact-evidence.md` |
| T2 | Verdict / Persistence / Operator | `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md` | `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator-evidence.md` |
| T3 | Contracts / Context / Regression | `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md` | `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression-evidence.md` |

### 5.2 Codex Merge Layer

Opus 3개 보고서와 fresh-run terminal state가 확보되면 Codex가 아래 문서를 만든다.

- `docs/2026-03-23/rol-live-merge-3terminal-post-run-merge-audit.md`

Opus는 merge 문서를 만들지 않는다.

## 6. Required Report Structure

각 terminal report는 아래 구조를 따른다.

1. Executive Summary
2. Included Coverage
3. Static Watchlist
4. Live Evidence Snapshot
5. Top Provisional Findings
6. Stale-vs-Live Corrections
7. Highest-ROI Fixes After Run
8. Confidence And Limits

각 finding 규칙:
- severity: `P0 / P1 / P2`
- fix type: `comment-only / doc-only / observability-only / contract-cleanup / boundary-refactor / execution-fix / ignore`
- `run relevance`를 한 줄로 명시
- `evidence type`을 아래 중 하나로 표기
  - `static-only`
  - `live-only`
  - `static+live`

## 7. Read Order

모든 터미널은 아래 문서를 먼저 읽는다.

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/live-run-merge-survey-harness.md`
5. `docs/implementation/deep-global-integrity-survey-harness.md`
6. `docs/implementation/codebase-global-survey-coverage-contract.md`
7. `docs/2026-03-23/rol-live-merge-3terminal-order.md`
8. `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
9. `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
10. `docs/2026-03-23/q1-q8-r2-merge-audit.md`
11. `docs/2026-03-23/console.txt`

## 8. Terminal Plan

### T1. Runtime / Artifact Flow

Primary scope:
- `main_a.py`
- `modules/core/` Stage 2/3/4 orchestrators and runtimes
- `modules/domain/agents/` writer / blueprint / director runtime seam
- live blueprint/manuscript artifacts under `projects/00_00/logs/artifacts/`

Core questions:
- 현재 run family에서 artifact truth 기준 drift가 어디서 처음 생기는가
- Stage 2/3 contract가 Stage 4 write path로 어떻게 materialize되는가
- Stage 4 retry가 artifact를 실제로 개선하는가, 아니면 열화시키는가

### T2. Verdict / Persistence / Operator

Primary scope:
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/db_manager.py`
- session logger / JSONL / pass-rate / console transcript / DB truth

Core questions:
- Director PASS/PASS_WITH_FIX와 post-select REJECT가 지금 run에서 어떻게 충돌하는가
- DB / JSONL / console / session logger가 같은 attempt truth를 보고 있는가
- failure_category, retry_directives, advisory, rationale가 evidence로 충분히 남는가

### T3. Contracts / Context / Regression

Primary scope:
- `modules/core/pre_director_*`
- `modules/domain/agents/chief_writer_*`
- context/retrieval/config/validation/shared contract seams
- `tests/`, `scripts/`, bootstrap/config surfaces

Core questions:
- current run family를 흔드는 context/contract/rule seam이 어디인가
- long-run Q5/Q7류 위험과 current rerun blocker를 어떻게 구분해야 하는가
- 현재 regression surface가 다음 rerun을 얼마나 신뢰 가능하게 만드는가

## 9. Opus Launch Prompt

아래 프롬프트를 공통으로 쓰고, `LANE_NAME`, `PRIMARY_SCOPE`, `FINAL_REPORT_PATH`, `EVIDENCE_PATH`만 terminal별로 바꾼다.

```text
System-track live-merge survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/live-run-merge-survey-harness.md
5. docs/implementation/deep-global-integrity-survey-harness.md
6. docs/implementation/codebase-global-survey-coverage-contract.md
7. docs/2026-03-23/rol-live-merge-3terminal-order.md
8. docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md
9. docs/2026-03-23/pre-rerun-root-cause-merge-audit.md
10. docs/2026-03-23/q1-q8-r2-merge-audit.md
11. docs/2026-03-23/console.txt

Task:
Run a bounded live-merge deep survey for LANE_NAME over the current live workspace state while the fresh run is active.

Hard constraints:
- Survey-only. No code changes.
- Do not create execution SSOTs.
- Do not create docs/temp queue artifacts.
- Do not stop, restart, or rerun the fresh run.
- Treat mid-run evidence as provisional until the run reaches terminal state.
- Prefer live source and live evidence over stale survey wording.
- If a prior claim is already fixed in live code, mark it stale instead of repeating it.

Primary scope:
PRIMARY_SCOPE

Required output:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report status rule:
- If the fresh run is still active when you save, set Status to `draft-live-run-pending`.
- If the fresh run has already reached terminal state during your work, you may save as `final`, but only for your lane report.

Required report sections:
1. Executive Summary
2. Included Coverage
3. Static Watchlist
4. Live Evidence Snapshot
5. Top Provisional Findings
6. Stale-vs-Live Corrections
7. Highest-ROI Fixes After Run
8. Confidence And Limits

Rules:
- Every P0/P1 finding must have file:line or artifact path anchors.
- Every recommendation must have one fix type:
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - execution-fix
  - ignore
- Explicitly state:
  - whether this lane contains a probable rerun blocker
  - which findings are only provisional because the run is still active
  - top 3 highest-ROI fixes in this lane after run completion

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH
- python scripts/ops_validator.py

In your final response:
- summarize top findings first
- then confidence
- then the top 3 fixes
- keep it concise
```

## 10. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Runtime / Artifact Flow` | `main_a.py, Stage 2/3/4 orchestrators and runtimes, writer/blueprint/director seam, artifact truth under projects/00_00/logs/artifacts/` | `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md` | `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact-evidence.md` |
| T2 | `Verdict / Persistence / Operator` | `stage4_director_runtime.py, stage4_interview_round.py, stage4_reject_runtime.py, stage4_retry_runtime.py, db_manager.py, JSONL/session logger/console/DB truth` | `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md` | `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator-evidence.md` |
| T3 | `Contracts / Context / Regression` | `pre_director_*, chief_writer_*, context/retrieval/config/validation contracts, tests/scripts/bootstrap surfaces` | `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md` | `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression-evidence.md` |

## 11. Terminal Dispatch One-Liners

아래 문구를 그대로 복붙하면 된다.

- `넌 1번 터미널. docs/2026-03-23/rol-live-merge-3terminal-order.md를 읽고 T1 규칙대로 진행해.`
- `넌 2번 터미널. docs/2026-03-23/rol-live-merge-3terminal-order.md를 읽고 T2 규칙대로 진행해.`
- `넌 3번 터미널. docs/2026-03-23/rol-live-merge-3terminal-order.md를 읽고 T3 규칙대로 진행해.`

## 12. Codex Merge Rule

Opus는 `lane 조사와 저장`까지만 한다.

Codex가 그 다음을 맡는다.
- fresh-run terminal state 확인
- stale finding 제거
- live-only vs static-only vs static+live finding 분리
- cross-lane contradiction 정리
- rerun blocker vs long-run issue 분리
- post-run merge audit 작성
- 필요 시 execution SSOT 합성

## 13. 3-Pass Audit Record

- Pass 1
  - fresh run active 상태에서 사용할 live-merge 문서인지, 일반 survey order인지 구분했다.
- Pass 2
  - 3터미널 scope, provisional save rule, output path, Codex merge rule의 정합성을 점검했다.
- Pass 3
  - Opus 공통 프롬프트와 `넌 1번 터미널...` 배포 문구까지 바로 사용 가능한 형태로 닫았다.

## 14. Confidence

- Confidence: 97%
- Basis:
  - init harness, full survey harness, live-run-merge harness를 함께 반영했다.
  - fresh run active 상태에서의 provisional/final save 경계가 명확하다.
  - 3터미널 분할이 runtime, persistence/operator, contracts/regression을 누락 없이 덮는다.
