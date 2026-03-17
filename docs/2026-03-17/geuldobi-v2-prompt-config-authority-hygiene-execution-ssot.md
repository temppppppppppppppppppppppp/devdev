# Geuldobi V2 Prompt Config Authority Hygiene Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-prompt-config-authority-hygiene-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-prompt-config-authority-hygiene-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp mirror deletions, runtime log, survey bundle docs/evidence, and unrelated local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; prompt/config authority precedence now resolves through explicit contracts and operator-visible config authority summaries without reopening model-policy scope`
Source Survey Docs:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-deep-global-survey.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-evidence-manifest.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-cluster-compression.md`
Evidence Artifacts:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `95%`

## 1. Intent
- reduce repo-wide drift between YAML, JSON, prompt-loader output, and inline fallback literals
- make budget, threshold, and prompt authority traceable enough that later runtime and observability work have one clean contract
- absorb the survey's cost and long-run telemetry concerns into the same authority-cleanup lane instead of opening a low-ROI extra SSOT

## 2. Baseline Facts
- `T09` found live disagreement between YAML values and code/test fallbacks for key caps and thresholds
- `T05` and `T04` both found prompt authority split across prompt files and legacy inline constants
- the current repo uses multiple config sources:
  - `config/prompts/director.yaml`
  - `config/settings/validation.yaml`
  - `config/settings.json`
  - `config/models.yaml`
  - prompt-loader and inline constant fallbacks in domain/core code
- authority drift currently affects context budgets, Director semantics, and cost/telemetry interpretation

## 3. Scope
Included:
- `config/prompts/director.yaml`
- `config/settings/validation.yaml`
- `config/settings.json`
- `config/models.yaml`
- `modules/domain/agents/director_prompts.py`
- prompt loader or config resolver code that decides the effective live values
- telemetry fields that need config provenance to explain cost or long-run behavior

Excluded:
- full runtime/control-plane cleanup outside config provenance
- Stage 2/3 provenance implementation itself
- broad UI changes beyond showing config provenance where needed
- model-selection strategy invention unrelated to existing drift

## 4. Pass 1. Inventory Summary
- main hotspots:
  - validation caps and thresholds
  - Director prompt loading and fallback literals
  - long-context or token budget settings
  - model and telemetry-related defaults
- main mutable state:
  - resolved prompt text
  - effective caps
  - fallback values
  - telemetry summaries derived from those values
- primary risk:
  - operators and later code changes cannot tell which authority source is actually live

## 5. Pass 2. Semantic Classification
- Class A: primary authority candidates
  - canonical YAML or JSON files meant to define behavior
- Class B: fallback and compatibility authorities
  - inline constants and local defaults used when primary sources are absent
- Class C: resolver layers
  - prompt loader and config-merging code that selects the effective runtime value
- Class D: telemetry consumers
  - sinks or summaries that should report which authority source produced the live value

## 6. Side-Effect Map
- file writes / artifacts:
  - prompt or settings changes can alter saved metadata and artifact behavior indirectly
- DB / schema / transaction boundaries:
  - any durable telemetry or metadata that records effective config source may touch schema or JSON payloads
- JSONL / log / audit sinks:
  - config provenance and cost/telemetry output should be auditable in logs
- console / UI / operator output:
  - operators may need to see effective source and resolved values, not only raw config files
- rollback / recovery / retry:
  - fallback behavior on missing config must be explicit and reversible
- cache / global state:
  - prompt/config caches must invalidate correctly when the authority source changes
- bootstrap fallback / config-env mutation:
  - this is a primary surface of the lane and must be fully mapped

## 7. Realization Architecture
- define one authority precedence map per config family
  - prompt
  - validation threshold
  - context budget
  - model or telemetry settings
- distinguish `authoritative source`, `fallback source`, and `effective source`
- propagate effective-source provenance to bounded durable sinks or operator surfaces
- merge long-run cost/telemetry contract work into this lane where the missing visibility is caused by source ambiguity

## 8. Execution Tranches
1. inventory and codify authority precedence for prompts, thresholds, and caps
2. remove or quarantine stale inline fallbacks that compete with declared canonical sources
3. emit effective-source provenance and key resolved values into durable telemetry paths
4. add low-cost regression checks for authority drift and fallback misuse

## 9. Acceptance Criteria
- every in-scope prompt/config family has one documented authority precedence map
- the live effective source for key budgets and thresholds is observable
- stale inline constants no longer silently override canonical sources
- cost or long-run telemetry no longer depends on hidden config provenance

## 10. Verification Plan
- targeted tests for config resolution and prompt loading
- targeted tests for fallback behavior on missing config
- low-memory pytest shards for prompt/config modules and any touched telemetry consumers
- post-implementation readback that compares canonical config, resolved runtime value, and emitted provenance

## 11. Guardrails
- do not expand this lane into model-policy invention
- do not rewrite all config formats if a precedence contract is enough
- do not hide fallback behavior; surface it as compatibility behavior if it must remain
- do not mutate unrelated narrative or project content

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - completed on 2026-03-17; remove the temp mirror after canonical closure, roadmap update, and queue validation
- roadmap dependency:
  - phase 3 of `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- realization outcome:
  - `modules/core/config_manager.py` now exposes explicit threshold/model authority contracts, including `authoritative_source`, `compatibility_source`, `fallback_source`, and `effective_source`
  - `modules/core/prompt_loader.py` and `modules/domain/agents/director_prompts.py` now resolve Director prompts YAML-first while quarantining inline prompt bodies as compatibility fallbacks with visible provenance
  - `modules/domain/agents/director_auditor.py` and `modules/api/bridge_server.py` now consume the new authority contracts so operator surfaces can see live threshold/model/prompt sources instead of hidden default chains
- verification evidence:
  - `python -m py_compile modules/core/config_manager.py modules/core/models_config.py modules/core/prompt_loader.py modules/domain/agents/director_prompts.py modules/domain/agents/director_auditor.py modules/api/bridge_server.py tests/test_config_manager.py tests/test_prompt_loader.py tests/test_director_modules.py tests/test_bridge_quality_summary.py`
  - `python -m pytest tests/test_config_manager.py -q`
  - `python -m pytest tests/test_prompt_loader.py -q`
  - `python -m pytest tests/test_director_modules.py -k "ensemble_prompt_constant_accessible or director_prompt_contract_prefers_yaml_source or strategic" -q`
  - `python -m pytest tests/test_phase5_hygiene.py -k "threshold" -q`
  - `python -m pytest tests/test_tf3_threshold_alignment.py -q`
  - `python -m pytest tests/test_bridge_quality_summary.py -q`
- residual risk:
  - some legacy call sites still pass inline defaults into `_threshold()` or model helpers, so the new contracts make those fallback chains visible but do not remove every compatibility default in one lane
