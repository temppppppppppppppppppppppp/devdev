# Stage3 First-Ensemble Visibility Live-Run Compact Survey

Date: 2026-04-12
Status: active
Confidence: `97%`
Canonical Path: `docs/2026-04-12/stage3-first-ensemble-visibility-live-run-compact-survey.md`
Scope: `Stage3 ep1 first-ensemble quiet window -> main console/operator visibility`
Track: system-track

## 1. Answer First

Yes, this is a real bounded operator-visibility seam, but it is not a hard runtime hang.

The current live workspace already proves that `Stage3` is progressing through `ThreePhase runtime -> BP ensemble -> Director`, yet the main console capture in `0_temp.txt` can stay visually frozen after the first `제1화 Blueprint 생성 중...` line.

Recommended owner:

- keep this under `0_0-stage3-contract-tightening-remediation`
- treat it as a bounded Stage3 operator-observability follow-up, not a new top-level queue family

## 2. Evidence

### 2.1 The main console capture looks frozen

- `0_temp.txt`
  - the visible Stage3 surface stops at:
    - `Three Phase Blueprint Generator 시작`
    - `제1화 Blueprint 생성 중... (Arc 1, 주인공: 한시우)`
  - the captured console then stays blank long enough to look like a stall

### 2.2 The runtime is still alive and progressing

- `projects/000_260412_a/logs/session_20260412_231516.log`
  - `23:17:53`
    - `제1화 Blueprint 생성 시작 (최대 10회 시도)...`
    - `제1화 Blueprint 대기: ThreePhase runtime 호출 중 (anchors=0, window=0, semantic_ctx=2659자)`
    - `[BPEnsemble] 3개 후보 병렬 생성 중...`
    - three `call_start agent=BlueprintEnsembleGenerator model=claude-sonnet-4-6`
  - `23:18:39` to `23:18:46`
    - three `call_success agent=BlueprintEnsembleGenerator`
    - `3개 후보 -> Director 선택 대기`
    - `call_start agent=Director`

This is enough to show the process is working, not wedged.

### 2.3 A heartbeat substrate already exists, but it does not fully solve the main-console gap

- `modules/core/stage3_orchestrator.py`
  - emits:
    - `Blueprint 생성 시작`
    - `Blueprint 대기: ThreePhase runtime 호출 중 (...)`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
  - `_call_with_operator_heartbeat(...)` already exists
  - default cadence is `30.0` seconds
  - later progress stays in runtime/root log space

### 2.4 UI evidence also shows the split

- `projects/000_260412_a/logs/session/ui_events.jsonl`
  - records the initial `progress` and first `heartbeat` for blueprint generation
  - does not continue to reflect the richer later ensemble / candidate / Director progress now visible in the session log

### 2.5 Semantic conclusion

- this is not primarily a model-quality problem
- this is not primarily a process crash
- this is an operator-surface mismatch:
  - the live session log proves progress
  - the main console capture remains too quiet during the first expensive ensemble wait

## 3. Semantic Classification

### Class A. Proven seam

- Stage3 first-ensemble progress is real
- the operator-facing main console can still feel frozen

### Class B. Likely root cause

- initial Stage3 progress is surfaced once at the orchestrator boundary
- deeper runtime heartbeat and candidate progress remain split across:
  - root/session log
  - limited UI-event surfacing
- the first meaningful reassurance arrives too late for human perception

### Class C. Bounded execution shape

1. surface the first-ensemble wait state more aggressively on the main console capture
2. surface candidate-launch / candidate-return milestones, not only the initial `ThreePhase runtime 호출 중`
3. tighten elapsed-time reassurance for the first quiet window so the operator can tell `working` from `stalled`

## 4. Side-Effect Notes

- file writes / artifacts:
  - no artifact-shape change required
- DB / schema:
  - not applicable
- console / UI:
  - primary owner surface for this slice
- JSONL / logs:
  - may add clearer heartbeat / progress event emission
- retry / recovery:
  - not directly affected
- config / env:
  - not applicable

## 5. Recommendation

Promote this as a bounded same-lane follow-up under `0_0-stage3-contract-tightening-remediation`.

Do not open a new queue family.

Do not treat it as a functional blocker ahead of the current proof stack.

## 6. 3-Pass Audit Record

Pass 1:

- bounded the question to Stage3 operator visibility, not generation correctness
- verified this is system-track and execution-doc eligible

Pass 2:

- confirmed `0_temp.txt`, `ui_events.jsonl`, and the session log disagree in visibility richness
- confirmed live progress exists across ensemble and Director phases

Pass 3:

- confirmed the correct owner is the existing Stage3 parent lane
- confirmed this is a small observability slice, not a new remediation family
