# Stage2 Headless Prompt Remediation Bounded Survey

Date: 2026-04-20
Status: final
Canonical Path: `docs/2026-04-20/stage2-headless-prompt-remediation-bounded-survey.md`
Baseline Commit: `466bbe4c1bc400d4539fb8ad19fa001856b8acce`
Baseline Dirty Summary: `dirty: .gitignore modified; local sensitive recovery-code file now ignored`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Evidence Artifacts:
- `docs/2026-04-20/stage2-headless-prompt-remediation-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent

Bound the Stage2 `headless prompt removal` issue so it can be realized safely without reopening the parked UI / bridge hardening lanes or the broader Stage2 architecture queue.

This survey is system-track only.
It focuses on current runtime prompt surfaces, desktop prompt-bridge boundaries, and the smallest safe non-interactive policy seam.

## 2. Scope

Included:

- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_context.py`
- `main_a.py`
- `scripts/canary_stage2_headless.py`
- `scripts/run_stage2_smoke.py`
- `modules/api/process_runner.py`
- `modules/api/prompt_broker.py`
- targeted Stage2 tests

Excluded:

- Stage3 / Stage4 failure-path prompt redesign
- bridge auth or desktop UI hardening
- broad Stage2 refactor or queue reprioritization
- material-side / donor workflow

## 3. Pass 1. Inventory Summary

Direct prompt surfaces found in `Stage2Orchestrator`:

1. failure-path choice prompt after Arc retries are exhausted
2. manual intervention follow-up prompt inside the same failure loop
3. Stage2 completion pause when `target_arc_count is None`

Relevant surrounding contracts:

1. `target_arc_count` is used for both automated and interactive paths, so it cannot serve as the sole headless detector
2. desktop bridge runs are non-TTY process runs but still intentionally interactive through `ProcessRunner` + `PromptBroker`
3. Stage4 already solved a similar post-run pause problem with an explicit bounded seam instead of a broad interaction rewrite

## 4. Pass 2. Semantic Classification

Class A. Real unattended-stall risk

- Stage2 failure-path prompts can block a genuinely unattended runner at the exact point where retries are exhausted
- completion pause can also block fully headless Stage2-only runs

Class B. False-positive headless detectors to avoid

- `target_arc_count is not None`
- raw `stdin.isatty()` by itself

Why:

- one-stop and other bounded operator paths use `target_arc_count=1`
- desktop bridge runs may look non-TTY while still providing prompt resolution via the prompt broker

Class C. Safe bounded substrate

- explicit Stage2-only headless policy seam
- keep default behavior interactive
- let dedicated headless scripts opt into deterministic `abort`
- preserve desktop prompt bridge by not auto-inferring headless from transport shape alone

## 5. Side-Effect Map

- file writes / artifacts:
  - Stage2 failure reports remain written
  - Stage2 canary / smoke scripts may set a bounded runtime env contract
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - operator log messages for failure handling and completion pause will change
- console / UI / operator output:
  - primary surface
- rollback / recovery / retry:
  - retry exhaustion still occurs first; only the post-exhaustion prompt contract changes
- cache / global state:
  - not applicable
- config / env mutation:
  - bounded runtime env seam is acceptable for dedicated headless scripts

## 6. Execution Consequence

The honest execution shape is a compact runtime contract fix:

1. add a small Stage2-specific headless policy seam
2. preserve the existing interactive prompt loop by default
3. preserve desktop prompt-broker runs
4. let the dedicated headless Stage2 runner opt into deterministic `abort`
5. suppress the Stage2 completion pause in that same headless policy

This should not be merged into the parked Stage4 owner-surface lane or the parked audit-report candidate lane.
It is a current-ops stabilization fix with small blast radius and direct verification.

## 7. Pass 3. Actionability Audit

The bounded next step is clear:

- create one compact execution SSOT for Stage2 headless prompt remediation
- keep the change isolated to Stage2 prompt policy plus dedicated headless-script activation
- verify with targeted Stage2 tests and compile checks

Confidence: `97/100`
