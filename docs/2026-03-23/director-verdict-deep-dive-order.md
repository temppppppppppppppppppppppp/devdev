Date: 2026-03-23
Status: final (3-pass audited, order scope)
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/director-verdict-deep-dive-order.md`
Temp Mirror Path: none
Source Planning Doc:
- `docs/2026-03-23/daily-roadmap-2026-03-23.md`

## 1. Purpose
- Define a bounded deep-dive order for the `Director-side` half of the 7-axis framework.
- Audit whether the Director pipeline:
  - judges correctly
  - explains verdicts cleanly
  - routes fix / retry feedback coherently
  - receives the right context at decision time

This is a survey order, not an implementation plan.

## 2. Covered Axes
- Q2. 잘 고치냐
- Q3. 잘 판단하냐
- Q4. 잘 설명하냐
- Q7. 잘 받냐
  - Director-side only

## 3. Scope
Included:
- `modules/core/stage4_director_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_auditor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/domain/agents/four_phase_arc_runtime.py`
- Director-facing prompt assembly and verdict payload surfaces directly touched by those files

Excluded:
- ChiefWriter generation quality as a primary topic
- WorldState / FactLedger internals unless directly needed for a Director verdict trace
- broad fresh-run execution planning
- implementation or refactor work

## 4. Primary Questions
1. What exact gates can move a Director path from PASS to REJECT or PASS_WITH_FIX?
2. Where are fix scope, retry instruction, and reject rationale shaped and forwarded?
3. Where can verdict explanation be lost, collapsed, or mistranslated before reaching the next generation step?
4. Which Director context fields are mandatory at each decision point, and where can they be dropped or truncated?

## 5. Required Investigation Method

### Pass 1. Verdict Topology
- Map authoritative owner for:
  - candidate selection
  - PASS / PASS_WITH_FIX / REJECT verdict
  - score and gate basis
  - fix scope and retry instructions
- Note where the owner shell ends and semantic-core logic begins.

### Pass 2. Feedback / Retry Trace
- Trace:
  - reject reason
  - verdict reason
  - fix scope
  - contradiction reasoning
  - retry feedback
from producer to consumer.
- Identify any lossy transformations, silent truncation, or field renaming.

### Pass 3. Director Context Reception
- Confirm that Director-side calls receive the required context bundle.
- Inspect:
  - director input pack assembly
  - advisory joins
  - previous-manuscript expansion
  - validation-result joins
- Flag missing, reordered, or low-priority-important fields.

## 6. Mandatory Output Structure
The final deep-dive report section for this lane must include:
1. Executive Summary
2. Verdict Ownership Map
3. Gate Basis / Override Map
4. Fix / Retry Feedback Flow
5. Director Context Reception Map
6. Top Hotspots
7. Quick Wins
8. Refactor Candidates
9. Confidence And Limits

## 7. Acceptance Criteria
- every P0 / P1 issue has a file and line anchor
- verdict ownership is explicitly mapped
- fix / retry chain is explicitly mapped
- Director-side Q7 findings are separated from generator-side context findings
- recommendations are labeled as:
  - comment-only
  - doc-only
  - observability-only
  - boundary-refactor
  - contract-cleanup
  - ignore

## 8. Stop Rules
- do not drift into ChiefWriter generation quality analysis unless directly required by a Director-side feedback loss claim
- do not patch code under this order
- do not reopen the long-function campaign based only on file size

## 9. Intended Report Integration
- primary integration target:
  - `docs/2026-03-23/director-pipeline-7axis-deep-dive.md`
- lane-local notes may be drafted during investigation, but final human-facing claims should land in the integrated 7-axis report

## 10. 3-Pass Audit Record
- Pass 1
  - scope bounded to Director-side axes and avoids generator / memory sprawl
- Pass 2
  - required maps and questions make the lane execution-grade rather than memo-grade
- Pass 3
  - output and stop rules align with current workspace survey governance

## 11. Confidence
- Confidence: 98%
- Basis:
  - directly derived from the 7-axis roadmap
  - bounded enough for Opus execution without execution-SSOT inflation
