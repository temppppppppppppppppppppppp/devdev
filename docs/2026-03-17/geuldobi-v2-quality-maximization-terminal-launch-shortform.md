# Geuldobi V2 Quality Maximization Terminal Launch Shortform

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-launch-shortform.md`
Document Type: operator launch shortform
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: stage-pipeline lane1~3 code/tests/docs edits, temp execution mirror deletions, 1 runtime log, 1 untracked roadmap draft; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Authorities:
- `AGENTS.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md`

## 1. Purpose
- provide the shortest safe launch text for each terminal
- let the operator say essentially:
  - `문서경로, 넌 T0N 터미널이다. 읽고 실행해라`
- keep the shortform safe by delegating detailed rules to the canonical prompt pack

## 2. When This Shortform Is Valid
- valid only for the current `geuldobi-v2-quality-maximization` repo-wide survey cycle
- valid only because the prompt pack already contains terminal-specific scope, output path, and stop-line
- not valid as a generic shortcut for unrelated tasks

## 3. Common Header
Use this exact common header for every terminal.

```text
시스템 오더다.

최우선 SSOT:
- AGENTS.md

이번 조사 governing canonical 문서:
- docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md
- docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md
- docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md

reference only:
- docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md
- docs/2026-03-17/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md
- docs/2026-03-17/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md
- docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md

docs/roadmap-v2.md는 seed일 뿐 authority가 아니다.
survey-only로 유지한다.
코드 수정 금지.
execution SSOT/roadmap 생성 금지.
위 문서를 읽고 너에게 해당하는 T0N 섹션 기준으로 실행하라.
```

## 4. Terminal Suffixes
Append exactly one of the following suffixes after the common header.

### T01

```text
넌 T01 터미널이다.
T01 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt
```

### T02

```text
넌 T02 터미널이다.
T02 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt
```

### T03

```text
넌 T03 터미널이다.
T03 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt
```

### T04

```text
넌 T04 터미널이다.
T04 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt
```

### T05

```text
넌 T05 터미널이다.
T05 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt
```

### T06

```text
넌 T06 터미널이다.
T06 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt
```

### T07

```text
넌 T07 터미널이다.
T07 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt
```

### T08

```text
넌 T08 터미널이다.
T08 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt
```

### T09

```text
넌 T09 터미널이다.
T09 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt
```

### T10

```text
넌 T10 터미널이다.
T10 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t10-merge-watchlist.txt
```

## 5. Minimal Launch Example
Example for terminal 1:

```text
시스템 오더다.

최우선 SSOT:
- AGENTS.md

이번 조사 governing canonical 문서:
- docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md
- docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md
- docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md

reference only:
- docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md
- docs/2026-03-17/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md
- docs/2026-03-17/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md
- docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md

docs/roadmap-v2.md는 seed일 뿐 authority가 아니다.
survey-only로 유지한다.
코드 수정 금지.
execution SSOT/roadmap 생성 금지.
위 문서를 읽고 너에게 해당하는 T0N 섹션 기준으로 실행하라.

넌 T01 터미널이다.
T01 섹션을 기준으로 실행하라.
산출물: docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt
```

## 6. Guardrail
- this shortform works because the detailed authority already lives in the prompt pack
- if the prompt-pack sections change materially, refresh this shortform in the same turn
- do not omit the governing doc block and send only `넌 T01이다` by itself

## 7. Confidence Statement
- estimated confidence in this shortform as an operator document: `98%`
- rationale:
  - it preserves governing/reference separation
  - it is short enough for practical terminal launch use
  - terminal-specific variance is reduced to identity and output path only
