Date: 2026-03-23
Status: final (3-pass audited)
Document Type: parallel deep global survey order
Canonical Path: `docs/2026-03-23/rol-global-survey-3terminal-order.md`
Temp Mirror Path: none

## 1. Purpose

이 문서는 `ROL 전역 전체 전수조사`를 `Opus 3터미널 병렬 조사`로 수행하기 위한 공통 오더다.

목적은 아래 3가지다.
- live workspace 기준으로 현재 코드베이스 전역 상태를 다시 측정한다.
- 오래된 survey wording과 현재 live code를 분리한다.
- Opus는 조사만 수행하고, Codex가 merge-audit 후 필요 시 execution SSOT를 합성한다.

이 문서는 survey-only 오더다. 구현 오더가 아니다.

## 2. Hard Constraints

- survey-only. 코드 수정 금지.
- execution SSOT 생성 금지.
- `docs/temp/` queue artifact 생성 금지.
- temp queue, roadmap, queue-state 수정 금지.
- fresh run 실행/재실행 금지.
- 기존 문서 status 임의 변경 금지.
- live source가 오래된 보고서보다 우선한다.
- 모든 P0/P1 finding은 `file:line` anchor가 있어야 한다.
- 모든 actionable finding은 `fix type`을 가져야 한다.

## 3. Coverage Model

이번 전수조사는 `codebase-global-survey-coverage-contract`의 8개 tranche를 3개 lane으로 묶는다.

- `T1 Runtime / Domain`
  - macro topology
  - runtime core
  - domain / agent layer
- `T2 Persistence / Operator`
  - persistence / logging / audit
  - operator surface / UI / desktop linkage
- `T3 Contracts / Regression`
  - tests / canary / regression
  - scripts / utilities
  - cross-cut contracts / config / bootstrap

## 4. Output Contract

각 터미널은 자기 final report 1개와 optional evidence manifest 1개만 저장한다.

### 4.1 Terminal Reports

| Terminal | Lane | Final Report Path | Optional Evidence Path |
|---|---|---|---|
| T1 | Runtime / Domain | `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain.md` | `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain-evidence.md` |
| T2 | Persistence / Operator | `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator.md` | `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator-evidence.md` |
| T3 | Contracts / Regression | `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression.md` | `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression-evidence.md` |

### 4.2 Codex Merge Layer

Opus 3개 보고서가 완료되면 Codex가 아래 문서를 만든다.
- `docs/2026-03-23/rol-global-survey-3terminal-merge-audit.md`

Opus는 merge 문서를 만들지 않는다.

## 5. Required Report Structure

각 terminal report는 아래 구조를 따른다.

1. Executive Summary
2. Included Coverage
3. Current Ownership / Flow Map
4. Top Hotspots
5. Stale-vs-Live Corrections
6. Quick Wins
7. Boundary Refactor Candidates
8. Confidence And Limits

각 finding 규칙:
- severity: `P0 / P1 / P2`
- fix type: `comment-only / doc-only / observability-only / contract-cleanup / boundary-refactor / ignore`
- fresh-run relevance를 한 줄로 명시

## 6. Read Order

모든 터미널은 아래 문서를 먼저 읽는다.

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/deep-global-integrity-survey-harness.md`
5. `docs/implementation/codebase-global-survey-coverage-contract.md`
6. `docs/2026-03-23/rol-global-survey-3terminal-order.md`
7. `docs/2026-03-23/daily-roadmap-2026-03-23.md`
8. `docs/2026-03-23/llm-codebase-orientation-pack.md`
9. `docs/2026-03-23/q1-q8-r2-merge-audit.md`
10. `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`

## 7. Terminal Plan

### T1. Runtime / Domain

Primary scope:
- `main_a.py`
- `modules/core/` stage orchestrators and runtimes
- `modules/domain/agents/`
- generation / selection / director ownership seams

Core questions:
- 현재 entrypoint와 stage spine은 어디가 authoritative owner인가
- generation / selection / director / retry chain이 live code 기준으로 어떻게 연결되는가
- 남은 hotspot이 true blocker인지, stale report residue인지

### T2. Persistence / Operator

Primary scope:
- `db_manager.py`
- session logger / audit / JSONL / metrics
- console / UI / desktop visible surfaces
- operator-visible provenance and retention paths

Core questions:
- DB / console / audit가 같은 truth를 보고 있는가
- operator-visible surface에서 decision-bearing 정보가 빠지지 않는가
- persistence / logging 쪽 silent sink loss가 남아 있는가

### T3. Contracts / Regression

Primary scope:
- `tests/`
- canary / smoke / verification scripts
- `scripts/`
- config / prompt / bootstrap / shared contracts

Core questions:
- 현재 regression surface는 어디가 얇은가
- config / prompt / bootstrap drift가 다음 run을 흔들 가능성이 있는가
- 오래된 survey claim을 현재 테스트/스크립트/계약이 반박하는가

## 8. Opus Launch Prompt

아래 프롬프트를 공통으로 쓰고, `LANE_NAME`, `PRIMARY_SCOPE`, `FINAL_REPORT_PATH`, `EVIDENCE_PATH`만 terminal별로 바꾼다.

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/deep-global-integrity-survey-harness.md
5. docs/implementation/codebase-global-survey-coverage-contract.md
6. docs/2026-03-23/rol-global-survey-3terminal-order.md
7. docs/2026-03-23/daily-roadmap-2026-03-23.md
8. docs/2026-03-23/llm-codebase-orientation-pack.md
9. docs/2026-03-23/q1-q8-r2-merge-audit.md
10. docs/2026-03-23/pre-rerun-root-cause-merge-audit.md

Task:
Run a bounded deep global survey for LANE_NAME over the current live workspace state.

Hard constraints:
- Survey-only. No code changes.
- Do not create execution SSOTs.
- Do not create docs/temp queue artifacts.
- Do not rerun fresh live paths.
- Prefer live source over stale survey wording.
- If a prior claim is already fixed in live code, mark it stale instead of repeating it.

Primary scope:
PRIMARY_SCOPE

Required output:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Included Coverage
3. Current Ownership / Flow Map
4. Top Hotspots
5. Stale-vs-Live Corrections
6. Quick Wins
7. Boundary Refactor Candidates
8. Confidence And Limits

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
  - whether this lane contains a pre-rerun blocker
  - top 3 highest-ROI fixes in this lane

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH
- python scripts/ops_validator.py

In your final response:
- summarize top findings first
- then confidence
- then the top 3 fixes
- keep it concise
```

## 9. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Runtime / Domain` | `main_a.py, modules/core stage orchestrators/runtimes, modules/domain/agents` | `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain.md` | `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain-evidence.md` |
| T2 | `Persistence / Operator` | `db_manager.py, session logger, audit/jsonl/metrics, console/UI/desktop surfaces` | `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator.md` | `docs/2026-03-23/opus/rol-global-survey-t2-persistence-operator-evidence.md` |
| T3 | `Contracts / Regression` | `tests, canary/smoke, scripts, config/prompt/bootstrap/shared contracts` | `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression.md` | `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression-evidence.md` |

## 10. Terminal Dispatch One-Liners

아래 문구를 그대로 복붙하면 된다.

- `넌 1번 터미널. docs/2026-03-23/rol-global-survey-3terminal-order.md를 읽고 T1 규칙대로 진행해.`
- `넌 2번 터미널. docs/2026-03-23/rol-global-survey-3terminal-order.md를 읽고 T2 규칙대로 진행해.`
- `넌 3번 터미널. docs/2026-03-23/rol-global-survey-3terminal-order.md를 읽고 T3 규칙대로 진행해.`

## 11. Codex Merge Rule

Opus는 `조사와 저장`까지만 한다.

Codex가 그 다음을 맡는다.
- stale finding 제거
- 중복 finding 병합
- cross-lane contradiction 정리
- pre-rerun blocker vs deferable item 분리
- 필요 시 execution SSOT 합성

## 12. 3-Pass Audit Record

- Pass 1
  - system-track global survey 조건과 3터미널 병렬 분할 범위를 확정했다.
- Pass 2
  - 8개 coverage tranche를 3개 lane으로 누락 없이 재배치했다.
- Pass 3
  - report path, evidence path, 공통 프롬프트, dispatch one-liner까지 Opus 배포 가능 형태로 닫았다.

## 13. Confidence

- Confidence: 97%
- Basis:
  - 기존 병렬 조사 문서 패턴과 deep global survey harness를 같이 반영했다.
  - survey-only, no-temp-queue, Codex merge rule이 명확히 분리되어 있다.
  - 3터미널 분할이 coverage contract의 8개 tranche를 빠뜨리지 않는다.
