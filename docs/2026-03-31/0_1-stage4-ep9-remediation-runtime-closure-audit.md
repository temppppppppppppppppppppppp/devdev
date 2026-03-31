# 0_1 Stage4 EP9 Remediation Runtime Closure Audit

Date: 2026-03-31
Status: final (3-pass audited)
Confidence: 96%
Document Type: post-run closure audit
Canonical Path: `docs/2026-03-31/0_1-stage4-ep9-remediation-runtime-closure-audit.md`
Temp Mirror Path: `(none - audit doc only)`
Baseline Commit: `512b0d23498d386d5199db2c01304b0d53bfd5aa`
Baseline Dirty Summary: `active roadmap/docs/temp queue plus canary_0_1_stage34_ep14_cw_hierarchy logs/db/artifacts mutated by completed canary`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: runtime closure audit
Source Docs:
- `docs/2026-03-30/0_1-stage4-ep9-remediation-execution-ssot.md`
- `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-03-31/0_1-stage4-ep9-remediation-runtime-closure-evidence.json`
- `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__C.txt`

## 1. Answer-First

This lane can be closed.

1. The main EP9 blocker was the false-positive `NpcDrift -> strong_advisory_escalation_non_local_fix` loop. The fresh live session `20260330_231345` no longer shows that pattern.
2. EP9 now passes on round 1 with `gate_basis="director_primary_pass"` across all authoritative sinks:
   - [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/episode_production.jsonl:51)
   - [decisions.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/decisions.jsonl:72)
   - `stage_attempts.id=58` in `project_data.db`
3. Artifact truth is aligned with the sink truth:
   - [final_manuscript__C.txt](C:/Users/User/Desktop/글도비/projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__C.txt)
   - [selected_candidate__C.txt](C:/Users/User/Desktop/글도비/projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/selected_candidate__C.txt)
   - both carry the same hash `6f923544c0e6033f`
4. The retry-marker attribution subpath was not re-exercised in this successful rerun because EP9 no longer retried, but that subpath is current-workspace test-covered in [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L108), [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L143), and [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L169).

## 2. Acceptance Criteria Check

### 2.1 EP9-Style NpcDrift False Positive No Longer Blocks Publication

The pre-patch EP9 session `20260330_193026` still shows the failure pattern:

- Stage 4 attempt rows `52..57` in `stage_attempts`
- repeated `strong_advisory_escalation_non_local_fix`
- six REJECT outcomes before the loop opened round 7

The fresh live session `20260330_231345` breaks that pattern.

Authoritative runtime evidence:

- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/ui_events.jsonl:3833) shows `Advisory 체인 완료 — 2건 경고`
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/ui_events.jsonl:3834) and [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/ui_events.jsonl:3836) show only `NumericConsistency` and `StyleSignal`
- there is no `NpcDrift` family in that live pass window
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/ui_events.jsonl:3842) records `PASS | gate: director_primary_pass`
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/ui_events.jsonl:3846) records `Round 1 PASS`

This is the runtime proof that the main EP9 remediation goal is realized.

### 2.2 Sink Alignment

The final PASS is not prompt-only or console-only. It is persisted consistently.

- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/episode_production.jsonl:51)
  - `attempt_key=s4:ep9:arc2:a1:20260330_231345`
  - `final_verdict=PASS`
  - `gate_basis=director_primary_pass`
  - `content_hash=6f923544c0e6033f...`
- [decisions.jsonl](C:/Users/User/Desktop/글도비/projects/0_1/logs/session/decisions.jsonl:72)
  - same `attempt_key`
  - same `content_hash`
  - `result=PASS`
  - `director_verdict=PASS`
- `project_data.db` `stage_attempts.id=58`
  - `stage=4`
  - `ep_num=9`
  - `attempt_num=1`
  - `verdict=PASS`
  - same `attempt_key`
  - same `artifact_path`

The artifact path in both JSONL sinks resolves to the actual saved manuscript:

- [final_manuscript__C.txt](C:/Users/User/Desktop/글도비/projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__C.txt)

### 2.3 Artifact Truth

Artifact truth is coherent, not just metadata-coherent.

- [final_manuscript__C.txt](C:/Users/User/Desktop/글도비/projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__C.txt)
  - bytes: `10663`
  - hash: `6f923544c0e6033f`
- [selected_candidate__C.txt](C:/Users/User/Desktop/글도비/projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01/selected_candidate__C.txt)
  - bytes: `10663`
  - hash: `6f923544c0e6033f`

That closes the `artifact truth` part of the lane.

### 2.4 Retry Attribution Repair

This acceptance criterion is not runtime-proven inside the successful EP9 rerun, because there were no retries after the fix landed.

What is still supported:

- the relevant tests pass in the current workspace:
  - `pytest tests/test_stage4_ep9_remediation.py -q`
  - result: `6 passed`
- the specific stage/ep attribution guards remain covered at:
  - [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L108)
  - [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L143)
  - [test_stage4_ep9_remediation.py](C:/Users/User/Desktop/글도비/tests/test_stage4_ep9_remediation.py#L169)
- the broader retry-lane observability substrate was already closed in the separate retry-efficiency lane

Closure interpretation:

- `EP9 main pathology`: runtime-validated
- `EP9 retry-marker subpath`: not re-exercised here, but test-covered and non-contradicted

## 3. Residual Risk

Still outside this lane:

- `TruthGate` still carries stale-role semantics in other surfaces
- broader retry efficiency and duplicate/plateau handling belong to the already closed retry-efficiency lane, not to this EP9 remediation lane
- later EP13-EP15 `NpcDrift relation_to_protag` or `Flashback` churn is separate substrate, not a reopen signal for EP9

Not supported by the current evidence:

- a claim that all Stage 4 truth-source issues are globally solved
- a claim that every retry marker path was live-exercised in the EP9 PASS session

## 4. Closure Decision

Closure is supported for `0_1-stage4-ep9-remediation`.

Reason:

- the governing lane existed to remove the EP9-specific false-positive retry pathology
- the fresh live session `20260330_231345` publishes EP9 on round 1 instead of looping through non-local-fix REJECTs
- `episode_production`, `decisions`, DB `stage_attempts`, and the final manuscript artifact all agree on the same PASS attempt
- the remaining retry attribution subpath is not contradicted and stays test-covered

Operational consequence:

- mark the canonical SSOT `closed`
- remove the temp mirror from `docs/temp/`
- refresh the aggregate roadmap so `0_1-stage3-blueprint-fix` becomes the next active queue item
