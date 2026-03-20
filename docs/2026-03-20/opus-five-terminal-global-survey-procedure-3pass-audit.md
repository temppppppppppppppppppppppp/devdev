# Opus Five Terminal Global Survey Procedure 3pass Audit

Date: 2026-03-20
Status: final
Document Type: procedure / operator order
Topic: Opus 5터미널을 기초 자료 수집자로만 쓰는 `ROL 전역 전체 전수조사` 절차
Scope:
- system-track global survey collection workflow
- Opus multi-terminal role split
- draft collector artifact naming
- Codex handoff and re-audit rule
Non-Goals:
- code patch
- execution SSOT realization
- aggregate roadmap realization
- temp queue closure

Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: large active workspace; hotspots include docs, geuldobi-desktop, modules, tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-manifest-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/canonical-naming-contract.md`
- `docs/implementation/single-ssot-roadmap-contract.md`

Confidence:
- Estimated confidence after 3-pass audit: 97%

## 1. Purpose

이 절차는 `Opus 5개 터미널`을 실행 권위자가 아니라 `기초 자료 수집자`로만 쓰기 위한 것이다.

핵심 원칙:

- Opus는 `1차 자료 수집`, `draft watchlist`, `evidence organization`까지만 한다.
- Opus는 `execution SSOT`, `aggregate roadmap`, `final severity`, `resolved/regressed` 판정을 하지 않는다.
- 그 이후 모든 권위 판단, 적대적 감리, canonical survey/SSOT/roadmap 작성은 Codex가 맡는다.

## 2. Governing Interpretation

이 오더는 하네스 기준으로 아래에 해당한다.

- `system-track`
- `Mode B. Survey / Audit / Execution-Doc Production`
- 범위가 `전역 전체`이면 `deep integrity mode`
- 구현/패치가 아니라 `survey-only mode`

따라서 이번 bundle에서는:

- code patch 금지
- runtime mutation 금지
- `docs/temp/` 새 mirror 생성 금지
- temp queue cleanup 금지
- active temp execution item은 건드리지 않음

현재 참고해야 할 temp queue 상태:

- active temp execution mirror exists:
  - `docs/temp/stage2-llm-owned-ep-count-density-pacing-execution-ssot.md`
- 이번 Opus survey는 이 queue를 실현하지 않고 별도 조사 bundle로만 취급한다

## 3. Role Split

### 3.1 Opus

Opus는 아래만 한다.

- wide scan
- draft tranche survey
- evidence list
- hotspot/watchlist 수집
- uncertainty/stale suspicion 기록
- side-effect sweep notes

Opus는 아래를 하지 않는다.

- execution SSOT
- canonical master survey
- single roadmap
- closure doc
- resolved/regressed/final severity 확정
- code patch

### 3.2 Codex

Codex는 Opus 결과를 받은 뒤 아래를 한다.

- live code 재조사
- Opus draft의 noise/stale/overclaim 제거
- evidence triangulation
- 3pass 적대적 감리
- canonical master survey 작성
- action-bearing area execution SSOT 필요 여부 판단
- 2개 이상 execution SSOT가 필요할 때만 single roadmap 작성

## 4. Output Policy

### 4.1 Opus output location

모든 Opus collector output은 아래에 저장한다.

- `docs/2026-03-20/`

### 4.2 Opus output naming

collector output은 아래 접두를 사용한다.

- `opus-collector-`

권장 파일 세트:

- `docs/2026-03-20/opus-collector-global-tranche-a-b-macro-runtime-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-c-domain-agents-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-d-g-persistence-scripts-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-e-operator-desktop-ui-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-f-h-tests-config-crosscut-draft.md`
- `docs/2026-03-20/opus-collector-global-uncertainty-ledger-draft.md`
- `docs/2026-03-20/opus-collector-global-evidence-index-draft.md`

필요하면 각 tranche별 raw artifact를 아래처럼 추가한다.

- `docs/2026-03-20/opus-collector-<topic>-raw-paths.txt`
- `docs/2026-03-20/opus-collector-<topic>-raw-hotspots.txt`
- `docs/2026-03-20/opus-collector-<topic>-raw-notes.json`

### 4.3 Mandatory Opus header marker

Opus가 저장하는 모든 markdown draft 상단에는 아래를 반드시 넣는다.

- `DRAFT`
- `NOT AUTHORITY`
- `COLLECTOR ONLY`
- `NO EXECUTION AUTHORITY`

## 5. Five-Terminal Split

5개 터미널은 아래처럼 자른다.

### Terminal 1

Coverage:

- Tranche A. macro topology
- Tranche B. runtime core

Focus:

- repo topology
- entrypoints
- runtime orchestration
- stage pipeline spine
- main bootstrap
- process runner / fallback

Output:

- `opus-collector-global-tranche-a-b-macro-runtime-draft.md`

### Terminal 2

Coverage:

- Tranche C. domain and agent layer

Focus:

- domain/agent modules
- ensembles
- validators
- retry / fallback / decision seams
- side-effect-bearing agent paths

Output:

- `opus-collector-global-tranche-c-domain-agents-draft.md`

### Terminal 3

Coverage:

- Tranche D. persistence and observability
- Tranche G. scripts and utility surface

Focus:

- DB manager
- session logger
- audit service
- JSONL / proof sinks
- migrations / repair scripts
- runtime-affecting scripts vs standalone utilities

Output:

- `opus-collector-global-tranche-d-g-persistence-scripts-draft.md`

### Terminal 4

Coverage:

- Tranche E. operator surface and app shell

Focus:

- UI
- geuldobi-desktop
- operator-visible control plane
- app shell / preload / bridge / desktop linkage
- prompt/output path notes

Output:

- `opus-collector-global-tranche-e-operator-desktop-ui-draft.md`

### Terminal 5

Coverage:

- Tranche F. quality and regression surface
- Tranche H. cross-cutting contracts and config

Focus:

- tests / smoke / canary / regression harnesses
- prompt maps
- contracts
- config / bootstrap rules
- shared constants
- contract drift risks

Output:

- `opus-collector-global-tranche-f-h-tests-config-crosscut-draft.md`

## 6. Mandatory Structure For Each Opus Draft

각 terminal draft는 최소 아래 구조를 가진다.

1. Scope
2. Included Paths
3. Excluded Paths
4. Entry Points / Hotspots
5. Side-Effect Sweep
6. Facts
7. Inferences
8. Uncertainty / Contradictions
9. Candidate Watchlist
10. Raw Evidence References

각 section 규칙:

- `Facts`: live code or direct artifact evidence only
- `Inferences`: 반드시 inference라고 표시
- `Uncertainty / Contradictions`: stale 가능성, 불확실성, 상충 문구 기록
- `Candidate Watchlist`: patch 가치가 있을 수 있는 항목만 나열

## 7. Absolute Opus Guardrails

Opus collector는 아래를 절대 하지 않는다.

- `execution SSOT` 작성
- `execution roadmap` 작성
- `docs/temp/` mirror 생성
- `resolved`, `fixed`, `regressed`, `authoritative` 선언
- final severity 확정
- policy verdict 확정
- code patch
- runtime/config mutation

추가 금지:

- 기존 docs를 authority처럼 인용하지 말 것
- live code 재확인 없이 conclusion을 쓰지 말 것
- survey-only order를 realization order로 승격하지 말 것

## 8. Operator Run Sequence

### Step 1. Launch

Opus 터미널 5개를 동시에 띄운다.

### Step 2. Feed the common base prompt

모든 터미널에 공통 base prompt를 먼저 준다.

### Step 3. Feed the terminal-specific prompt

각 터미널에 자기 tranche prompt를 추가로 준다.

### Step 4. Wait for collector outputs only

Opus가 draft collector docs를 다 저장할 때까지 기다린다.

### Step 5. Stop Opus

Opus는 collector 단계에서 종료한다.

### Step 6. Hand off to Codex

이후부터는 Codex가:

- live code 재조사
- draft 정리
- 3pass 적대적 감리
- canonical docs 생산

을 수행한다.

## 9. Common Base Prompt For All Five Opus Terminals

```text
시스템 트랙 오더다. narrative pipeline으로 해석하지 마라.

너는 execution SSOT 작성자가 아니다.
너의 역할은 기초 자료 수집자, evidence organizer, draft survey collector다.

반드시 먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/deep-global-integrity-survey-harness.md
- docs/implementation/document-3pass-audit-harness.md

이번 오더:
- ROL 전역 전체 전수조사만 수행한다.
- survey-only mode를 유지한다.
- 구현, 패치, execution SSOT, roadmap, closure는 하지 않는다.
- side-effects를 기본 포함한다.
- 기존 docs는 참고용일 뿐 authority가 아니다.
- live workspace evidence를 우선한다.

절대 금지:
- docs/temp/ mirror 생성
- execution SSOT 작성
- execution roadmap 작성
- resolved/regressed/final severity 선언
- policy verdict 확정
- 코드 수정

문서 저장 규칙:
- docs/2026-03-20/ 아래에만 저장
- 파일명은 opus-collector- 접두 사용
- 각 문서 상단에 DRAFT / NOT AUTHORITY / COLLECTOR ONLY / NO EXECUTION AUTHORITY 를 명시
- facts, inferences, uncertainty를 분리해 쓸 것
- stale 가능성은 stale/uncertain/watchlist로 남길 것
```

## 10. Terminal-Specific Prompt Add-ons

### Terminal 1 Prompt

```text
너는 Terminal 1이다.
Coverage:
- Tranche A. macro topology
- Tranche B. runtime core

반드시 조사할 것:
- repo topology
- entrypoints
- main bootstrap
- stage pipeline spine
- process runner / fallback
- runtime authority seams

산출물:
- docs/2026-03-20/opus-collector-global-tranche-a-b-macro-runtime-draft.md
```

### Terminal 2 Prompt

```text
너는 Terminal 2다.
Coverage:
- Tranche C. domain and agent layer

반드시 조사할 것:
- modules/domain/
- ensembles
- validators
- retry / fallback / director seams
- agent-level side effects

산출물:
- docs/2026-03-20/opus-collector-global-tranche-c-domain-agents-draft.md
```

### Terminal 3 Prompt

```text
너는 Terminal 3이다.
Coverage:
- Tranche D. persistence and observability
- Tranche G. scripts and utility surface

반드시 조사할 것:
- DB writes / schema touchpoints
- session logger / audit / JSONL sinks
- proof artifacts
- scripts/
- runtime-affecting utility split

산출물:
- docs/2026-03-20/opus-collector-global-tranche-d-g-persistence-scripts-draft.md
```

### Terminal 4 Prompt

```text
너는 Terminal 4다.
Coverage:
- Tranche E. operator surface and app shell

반드시 조사할 것:
- UI/
- geuldobi-desktop/
- operator-visible surfaces
- preload / bridge / desktop linkage
- prompt/output/operator path notes

산출물:
- docs/2026-03-20/opus-collector-global-tranche-e-operator-desktop-ui-draft.md
```

### Terminal 5 Prompt

```text
너는 Terminal 5다.
Coverage:
- Tranche F. quality and regression surface
- Tranche H. cross-cut contracts and config

반드시 조사할 것:
- tests/
- smoke/canary/regression harnesses
- prompt maps
- contracts
- bootstrap/config/constants
- contract drift risks

산출물:
- docs/2026-03-20/opus-collector-global-tranche-f-h-tests-config-crosscut-draft.md
```

## 11. Codex Handoff Prompt

Opus collector outputs가 다 생긴 뒤 Codex에 넘길 prompt는 아래를 권장한다.

```text
이제 docs/2026-03-20/opus-collector-* draft들을 기초 자료로만 사용해라.
live workspace code를 다시 우선 조사하고, Opus draft의 stale/noise/overclaim을 적대적으로 제거하라.

해야 할 일:
- evidence triangulation
- contradiction 정리
- stale/no-trust 재분류
- canonical master survey 작성
- action-bearing area execution SSOT 필요 여부 판단
- 필요 시 single roadmap 작성
- 3pass audit + 95% confidence gate 적용

하지 말 것:
- Opus draft를 authority로 채택하지 말 것
- live code 재조사 없이 결론을 쓰지 말 것
- parallel roadmap을 만들지 말 것
```

## 12. Final Recommendation

추천 운영은 아래 한 줄로 요약된다.

- `Opus 5터미널은 tranche별 collector draft만 만들고 멈추게 하고, 이후 Codex가 live re-check + 3pass 적대적 감리로 canonical survey와 execution 판단을 이어받아라`
