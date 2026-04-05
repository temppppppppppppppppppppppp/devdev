# 00_0405 Stage2 Three-Terminal Parallel Survey Order

Date: 2026-04-05
Status: final
Document Type: operator parallel order
Canonical Path: `docs/2026-04-05/00_0405-stage2-three-terminal-parallel-survey-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Track: system
Mode: read-only parallel survey; no code patching; docs-only outputs
Confidence: `96%`

## 1. Purpose

This order splits the `00_0405` Stage2 investigation into three non-overlapping terminal lanes.

The working premise is already fixed:

- `Stage1 bypass` is not treated as the defect in this wave
- the question is not `did Stage2 fail`
- the question is:
  - `does Stage2 artifact truth round-trip cleanly`
  - `does Stage2 observability expose the real reasons to the operator`
  - `which owner lane should absorb the debt later`

## 2. Fixed Read Before Starting

Every terminal reads these first:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`

Queue context only:

- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/execution-roadmap.md`

## 3. Global Guardrails

1. Do not treat `Stage1 bypass` as the primary defect.
2. Do not patch code in this wave.
3. Do not mutate `docs/temp/`.
4. Do not reopen Stage3 or Stage4 realization.
5. Prefer byte-level UTF-8 reads for artifact truth.
6. Findings first. Overviews only after evidence.
7. Each terminal writes only its own output file.

## 4. Terminal Ownership

### Terminal 1

- owner: `Codex`
- mission: `artifact truth / round-trip ledger`
- focus:
  - `arc txt` vs `selected Stage2 artifact JSON`
  - location carryover
  - item carryover
  - state summary carryover
  - numeric spine sanity
- output:
  - `docs/2026-04-05/00_0405-stage2-terminal1-artifact-roundtrip-ledger.md`

### Terminal 2

- owner: `Opus`
- mission: `observability / sink map`
- focus:
  - what reaches console/UI
  - what only lands in `runtime_audit.jsonl`
  - what only lands in `quality_metrics.jsonl`
  - where the operator loses the strongest Stage2 reasons
- output:
  - `docs/2026-04-05/00_0405-stage2-terminal2-observability-sink-map.md`

### Terminal 3

- owner: `Opus`
- mission: `owner lane / patch candidate / queue-safe reading`
- focus:
  - translate findings into owner files
  - decide whether this is future `Stage2 contract normalization`, `readiness`, or mixed lane debt
  - propose bounded next wave without promoting Stage2 above active Stage4 queue
- output:
  - `docs/2026-04-05/00_0405-stage2-terminal3-owner-lane-and-next-wave.md`

## 5. Required Questions Per Terminal

### Terminal 1 Questions

1. Where does txt truth diverge from selected Stage2 packet truth?
2. Which divergences are cosmetic wording only, and which are real carryover drift?
3. Is the numeric/business spine still coherent despite packet drift?

### Terminal 2 Questions

1. Which high-signal Stage2 reasons are visible in console/UI?
2. Which high-signal reasons are audit-only or quality-only?
3. Which code surfaces own the missing console visibility?

### Terminal 3 Questions

1. Which parked Stage2 lane best matches the observed debt?
2. Which owner files should absorb the next bounded realization wave?
3. What is the smallest queue-safe next wave after this survey stack completes?

## 6. Output Contract

Each terminal must keep the same section shape:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Owner Verdict`
5. `Minimal Next Wave`
6. `Stop`

Required stop line:

- `read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output`

## 7. Paste-Ready Orders

### Terminal 1

```text
System-track order. This lane owns `00_0405 Stage2 artifact truth / round-trip ledger`.

Fixed premises:
- Do not treat Stage1 bypass as the defect in this survey.
- No code patching.
- Do not modify docs/temp.
- Write exactly one output file under docs/2026-04-05.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json

Inspect:
- projects/00_0405/plans/arcs/arc_001.txt through arc_004.txt
- projects/00_0405/logs/artifacts/stage2/**/final_arc__*.json
- projects/00_0405/logs/runtime_audit.jsonl

Questions:
1. Where does txt truth diverge from selected Stage2 artifact truth?
2. Which differences are real carryover drift versus wording-only differences?
3. Does the numeric/business spine remain coherent?

Output:
- docs/2026-04-05/00_0405-stage2-terminal1-artifact-roundtrip-ledger.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Owner Verdict
5. Minimal Next Wave
6. Stop

Required stop line:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output
```

### Terminal 2

```text
System-track order. This lane owns `00_0405 Stage2 observability / sink map`.

Fixed premises:
- Do not treat Stage1 bypass as the defect in this survey.
- No code patching.
- Do not modify docs/temp.
- Write exactly one output file under docs/2026-04-05.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json

Inspect:
- projects/00_0405/logs/session/ui_events.jsonl
- projects/00_0405/logs/runtime_audit.jsonl
- projects/00_0405/logs/quality_metrics.jsonl
- projects/00_0405/logs/metrics/metrics_20260405_101441.json
- modules/core/stage2_validation_pipeline.py
- modules/core/stage2_preflight.py
- modules/core/quality_dashboard.py
- modules/core/services/audit_service.py
- modules/core/session_logger.py

Questions:
1. Which Stage2 reasons are visible in console/UI and which are not?
2. Which sink holds auto-correct, retrieval, and state-extraction truth?
3. Which owner files are responsible for the operator visibility gap?

Output:
- docs/2026-04-05/00_0405-stage2-terminal2-observability-sink-map.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Owner Verdict
5. Minimal Next Wave
6. Stop

Required stop line:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output
```

### Terminal 3

```text
System-track order. This lane owns `00_0405 Stage2 owner lane / next wave`.

Fixed premises:
- Do not treat Stage1 bypass as the defect in this survey.
- No code patching.
- Do not modify docs/temp.
- Do not promote Stage2 above the active Stage4 queue.
- Write exactly one output file under docs/2026-04-05.

Read first:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/system-full-survey-execution-harness.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md
- docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json
- docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md
- docs/temp/execution-roadmap.md

Questions:
1. Which parked Stage2 lane best matches this evidence?
2. Which owner file group should absorb the eventual bounded realization wave?
3. What is the smallest queue-safe next wave after this survey stack?
4. Why should this stop at survey/proposal rather than immediate realization?

Output:
- docs/2026-04-05/00_0405-stage2-terminal3-owner-lane-and-next-wave.md

Section shape:
1. Coverage
2. Findings
3. Non-Issues
4. Owner Verdict
5. Minimal Next Wave
6. Stop

Required stop line:
- read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output
```

## 8. 3-Pass Audit Note

Pass 1:

- compressed the current Stage2 survey into three non-overlapping lanes

Pass 2:

- checked that each lane maps to a distinct evidence family and output file

Pass 3:

- checked operator usability and paste-readiness for immediate terminal dispatch
