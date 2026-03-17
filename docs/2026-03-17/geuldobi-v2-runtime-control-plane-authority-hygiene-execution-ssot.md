# Geuldobi V2 Runtime Control Plane Authority Hygiene Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-runtime-control-plane-authority-hygiene-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-runtime-control-plane-authority-hygiene-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp mirror deletions, runtime log, survey bundle docs/evidence, and unrelated local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-cross-cut-integrity-matrix.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-cluster-compression.md`
Evidence Artifacts:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- make the public runtime/control-plane authority story explicit instead of split across Mode-B reality, compatibility lanes, and maintenance-path residue
- normalize startup, process-runner, bridge, and operator log surfaces so public truth is easier to read
- quarantine or clearly label Lite/Test/runtime-control-plane exceptions rather than letting them masquerade as equal authority paths

## 2. Baseline Facts
- `T01` and `T02` found that live runtime authority is effectively `desktop/app shell -> bridge -> process runner -> main_a.py -> stage pipeline`
- the repo still contains root utilities, root `main.js`, `lite_mode/`, and `test_mode/` surfaces that can blur authority boundaries
- `T07` found operator truth split between early workspace-level logs and later project-local logs
- `T08` found proof and smoke paths for these runtime surfaces are less standardized than the core stage logic

## 3. Scope
Included:
- `main_a.py`
- root `main.js`
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/`
- `lite_mode/`
- `test_mode/`
- startup and runtime log root decisions that affect operator truth

Excluded:
- Stage 4 semantic redesign already handled in other lanes
- deep prompt/config precedence work except where runtime routing consumes the resolved values
- large desktop UI redesign unrelated to authority or operator truth
- narrative pipeline output review

## 4. Pass 1. Inventory Summary
- main hotspots:
  - bridge and process-runner path
  - public versus compatibility runtime entrypoints
  - boot log root versus project-local runtime sinks
  - Lite/Test surfaces and maintenance utilities
- main mutable state:
  - runner mode flags
  - startup failure paths
  - bridge session state
  - per-project versus workspace-level log routing
- primary risk:
  - operators and future code changes can misread which path is actually authoritative for live runtime behavior

## 5. Pass 2. Semantic Classification
- Class A: public supported path
  - the runtime path that operators and future docs should treat as authoritative
- Class B: compatibility or maintenance path
  - modes or entrypoints that may remain, but should not blur public authority
- Class C: operator-truth surfaces
  - startup logs, bridge payloads, desktop surfaces, and runtime status files
- Class D: proof and smoke paths
  - the cheapest repeatable checks that prove the authority map still holds

## 6. Side-Effect Map
- file writes / artifacts:
  - startup and runtime logs across workspace-level and project-level roots
- DB / schema / transaction boundaries:
  - not a primary direct surface, except where runtime metadata or session truth is persisted
- JSONL / log / audit sinks:
  - bridge or runner logs and session truth surfaces
- console / UI / operator output:
  - desktop, bridge, and CLI/operator status output are primary surfaces
- rollback / recovery / retry:
  - startup fallback, mode fallback, and process restart behavior
- cache / global state:
  - runner or bridge session memory and mode state
- bootstrap fallback / config-env mutation:
  - startup mode selection and missing-config behavior are primary surfaces

## 7. Realization Architecture
- define one supported authority map for runtime/control-plane execution
- label compatibility or maintenance paths explicitly instead of leaving them implicit
- normalize log-root and operator-truth routing so early boot and later runtime truth are easier to connect
- create a bounded smoke/proof path that confirms the supported authority map without forcing expensive end-to-end runs every time

## 8. Execution Tranches
1. codify the supported authority map and compatibility-path labels
2. normalize boot/runtime operator-truth routing and log-root semantics
3. quarantine or simplify stale maintenance-path exceptions where they confuse public authority
4. add a bounded smoke/proof path for the supported runtime/control-plane contract

## 9. Acceptance Criteria
- one supported runtime/control-plane path is explicitly documented in code/docs and is easy to identify
- compatibility lanes are labeled or quarantined rather than silently competing with the supported path
- startup and runtime truth surfaces no longer require cross-reading multiple root styles without explanation
- a repeatable bounded smoke/proof path exists for the supported authority map

## 10. Verification Plan
- targeted tests or smoke scripts for process-runner and bridge startup paths
- low-memory pytest shards for touched runtime/control-plane modules
- manual operator-surface readback of startup and runtime log destinations after implementation
- bounded smoke run that confirms the supported path and compatibility labels

## 11. Guardrails
- do not break supported desktop or bridge flows in order to delete compatibility residue too aggressively
- do not create a second public authority path
- do not let log normalization hide the distinction between boot failure and project-local runtime evidence
- do not let proof-path work balloon into a full live-run campaign inside this lane

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition:
  - remove the temp mirror after implementation closure and roadmap status update
- roadmap dependency:
  - phase 4 of `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Addendum
- post-review follow-up landed after closure to tighten the authority contract against live runtime surfaces
- `RUNTIME_AUTHORITY_CONTRACT` now distinguishes desktop pre-bridge boot logging from engine bootstrap fallback instead of collapsing both into one boot sink
- `CONTROL_PLANE_AUTHORITY_CONTRACT` now exposes helper-based authority lookup and summary builders that live server payloads consume directly
- `/status`, `/quality/summary`, and `/quality/dashboard` now surface the authority map coherently instead of leaving `/quality/summary` unlabeled
- supplemental verification:
  - `python -m py_compile modules/api/control_plane_contract.py modules/core/runtime_paths.py modules/api/process_runner.py modules/api/bridge_server.py tests/test_runtime_authority_contract.py tests/test_bridge_server_http_contract.py tests/test_bridge_quality_summary.py`
  - `python -m pytest tests/test_runtime_authority_contract.py -q`
  - `python -m pytest tests/test_bridge_server_http_contract.py -q`
  - `python -m pytest tests/test_bridge_quality_summary.py -k "quality_summary_endpoint or authority_maps" -q`
  - `python -m pytest tests/test_process_runner.py -q`
  - `python scripts/check_utf8_hygiene.py modules/api/control_plane_contract.py modules/core/runtime_paths.py modules/api/process_runner.py modules/api/bridge_server.py tests/test_runtime_authority_contract.py tests/test_bridge_server_http_contract.py tests/test_bridge_quality_summary.py`
- residual risk:
  - desktop `src/main.js` still mirrors the authority story via JS-local comments and route wiring rather than consuming a generated cross-language contract artifact
