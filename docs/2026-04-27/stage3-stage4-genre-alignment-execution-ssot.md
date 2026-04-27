# Stage3/Stage4 Genre Alignment Execution SSOT

Date: 2026-04-27
Track: system
Status: in_progress (operator-promoted compact survey -> tranche A/B execution)
Canonical Path: `docs/2026-04-27/stage3-stage4-genre-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were already present under `docs/2026-04-27/` and `docs/temp/`; `docs/temp/queue-state.json` was modified before this SSOT; no production code was edited while preparing this document.
- Resume Commit: `f484f59c33295add410f10401f8723da8c2fe03b`
- Resume Drift Summary: local `main` fast-forwarded from `a3d826978d530ab61d3765e5e095890fa6533ea7` to `f484f59c33295add410f10401f8723da8c2fe03b`; tracked source still retains the #56 risky Stage3 physical-action surfaces; only pre-existing local dirty file is `0_temp.txt`.
GitHub Issue:
- #56 `[Ensemble] Genre-align Stage3/Stage4 action and tension strategies`
Source Survey Docs:
- `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`
- GitHub issue #56 body
Evidence Artifacts:
- No separate local T01-T10 #56 terminal result files were found.
- GitHub issue #56 had no readable issue comments at audit time.
- Live source and config evidence are cited in this SSOT.
- Operator-promoted compact survey, 2026-04-27 current session:
  - T01 Stage3 surface survey: confirmed `action_focused`, `SCENE_PRESETS`, prompt preset table, and prompt insertion path still carry physical action defaults.
  - T03 genre semantics survey: defined investment/business-power action as business move, capital exposure, institutional pressure, proof, receipt, observer shift, and next gate.
  - T07 regression survey: recommended deterministic Stage3 prompt/metadata tests first, then Director-visible contract tests.
  - T09 authority survey: confirmed genre alignment must be a route/advisory contract carrier, not Python-owned narrative verdict authority.
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage3-stage4-genre-alignment
  github_issue: 56
  status: in_progress
  queue_role: front_active
  roadmap_rank: 2
  depends_on: []
  tranches:
    - id: genre-semantics-regression-net
      title: Test-first genre semantics regression net
    - id: stage3-strategy-semantic-map
      title: Stage3 strategy semantic map
    - id: prompt-material-ingress
      title: Prompt and material ingress
    - id: stage4-director-visibility
      title: Stage4 Director visibility
    - id: guard-preservation-and-operator-evidence
      title: Tactical guard preservation and operator evidence
    - id: benchmark-live-proof
      title: Benchmark and live proof packet
  verification_commands:
    - python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q
    - python -m pytest tests/test_stage4_orchestrator.py tests/test_tf29_open_review.py -q
    - python scripts/check_utf8_hygiene.py <touched docs/code/tests>
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Close the root cause behind #56: in an investment/business-power work, Stage3 and Stage4 must interpret "action", "tension", "peak", and "cliffhanger" as business conflict, institutional pressure, deal timing, capital risk, negotiation leverage, governance threat, public proof, private receipt, and next legal/structural gate.

This execution item must not merely add more physical-intrusion block words. The existing tactical guard is useful as a fail-closed safety net, but it is a symptom guard. The root fix is a genre-aware strategy contract that reaches both Stage3 blueprint generation and Stage4 Director selection.

## 2. Adversarial 3-Pass Audit

### Pass 1 - artifact intake attack

Attack: the operator reports that ten #56 terminal investigations returned, but no local `terminal-01` through `terminal-10` #56 report files are present under `docs/`, and GitHub issue #56 has no readable comments.

Result: PASS_WITH_LIMITATION. This SSOT does not claim to summarize unseen terminal reports. It synthesizes the #56 order, issue body, and live workspace evidence. Any later-discovered terminal reports must be merged before implementation starts.

### Pass 2 - root-cause attack

Attack: the issue could be fully solved by the existing unauthorized tactical intrusion guard.

Result: FAIL for that narrower interpretation. `modules/domain/agents/blueprint_ensemble.py` still defines `action_focused` with physical combat/chase/cliffhanger language, `SCENE_PRESETS.action_peak` is still combat/action-centered, and the prompt table still exposes `action_peak` as `전투/액션 클라이맥스`. The tactical guard catches some unauthorized physical intrusions after generation; it does not align the upstream strategy meaning.

### Pass 3 - authority attack

Attack: genre alignment could accidentally become Python judging story quality, violating Director sovereignty and the workspace rule that Python collects while LLM judges.

Result: PASS if execution stays contract-shaped. Python may route, format, attach advisory/contract payloads, and block explicit forbidden tactical intrusions. It must not replace Director judgment on whether a business-power scene is good. Stage4 must receive the genre strategy contract as visible authority/advisory context, and the Director remains the final quality judge.

### Current-state re-audit - 2026-04-27 operator promotion

Pass 1 - structure and scope:
- PASS. The existing SSOT is the correct governing document for #56; no new execution document is required.
- PASS. Operator promotion changes queue role from parked future wave to current implementation wave.

Pass 2 - evidence and consistency:
- PASS. Live HEAD `f484f59c33295add410f10401f8723da8c2fe03b` still contains the risky Stage3 physical-action language at `modules/domain/agents/blueprint_ensemble.py:61-69`, `:317-318`, and `config/prompts/ensemble.yaml:340-348`.
- PASS. Compact survey findings agree with this SSOT: root fix is upstream genre strategy semantics, not removal of the tactical guard.
- PASS. T09 authority guidance narrows Stage4 work to Director-visible advisory/route context; Python must not emit verdict authority for genre quality.

Pass 3 - execution readiness:
- PASS. First tranche is bounded to deterministic Stage3 prompt/metadata contract plus preservation of existing tactical guard tests.
- PASS. Stage4 work remains Director-visible contract plumbing only unless later proof justifies broader selection changes.

Estimated current-state confidence: 96%.

Estimated operational confidence after 3-pass audit: 95%.

## 3. Baseline Facts

- `modules/domain/agents/blueprint_ensemble.py:58-72` defines `action_focused` as high-tension physical action: combat, chase, confrontation, fast tempo, minimal emotion, and physical crisis/action cliffhanger.
- `modules/domain/agents/blueprint_ensemble.py:313-327` defines `action_peak` as combat/action climax, fast breathing, visual-centered, and minimal dialogue.
- `modules/domain/agents/blueprint_ensemble.py:551-560` resolves a genre value, but defaults through `GenreTypes.WUXIA` and does not by itself remap strategy semantics.
- `modules/domain/agents/blueprint_ensemble.py:955-1076` carries `genre` into the generation path, but the existing prompt bundle remains strategy-centered rather than a material-side genre semantics contract.
- `modules/domain/agents/blueprint_ensemble.py:1396-1412` and `:2287-2306` implement unauthorized tactical intrusion rejection. This is valuable and should remain.
- `tests/test_blueprint_ensemble_generate_ensemble.py:687-779` covers physical intruder and vehicle chase rejection/allowance behavior. It does not prove business-power `action_focused` semantics are aligned before generation.
- `config/prompts/ensemble.yaml:303-305` already forbids cross-genre contamination, but `:340-355` still labels `action_peak` as combat/action climax and `:390-431` keeps generic high-tension/cliffhanger slots.
- `config/prompts/director.yaml:348-380` receives story context, blueprint, previous ending, candidates, and Python warnings, while `:492-506` has broad genre reward examples. It does not yet expose a Stage3 strategy semantics contract as a first-class Director selection input.
- `projects/01_골든카나리아/config/work_guard.yaml:1-64` identifies the work as `investment_family_office_control` with economic calendar, exit design, governance firewall, capital operation, allocation priority, due diligence, operating authority, and legal next gate semantics.
- `config/style_references/investment/style_guide.json:1-64` and `:111-120` provide investment register and anti-AI rules: numerical specificity, plausible financial constraints, business-metric dialogue, and no unrealistic one-step success.

## 4. Scope

Included:
- Stage3 strategy semantics and prompt payloads in `modules/domain/agents/blueprint_ensemble.py`.
- Prompt/config text that names action/tension/peak/cliffhanger semantics, especially `config/prompts/ensemble.yaml`.
- Stage4 Director visibility path in `modules/domain/agents/director_ensemble.py` and the Stage4 orchestration handoff when needed.
- Regression tests that prove investment/business-power action strategy does not invent combat, chase, physical intrusion, or thriller pressure without tactical authority.
- Benchmark/proof packet design for April baseline versus current runtime/reject rates.

Excluded:
- Removing the unauthorized tactical intrusion guard.
- Replacing Director judgment with Python narrative quality scoring.
- Broad ensemble architecture redesign outside #56.
- Editing material facts in `work_guard`, factsheets, Bible, or treatment as an automated code operation.

## 5. Pass 1. Inventory Summary

Stage3 inventory:
- Strategy constants contain physical action language.
- Scene presets contain physical action language.
- Genre resolution exists, but genre-specific strategy semantics are not first-class.
- Candidate metadata stores strategy and prompt envelope, but not a stable genre strategy contract.
- Tactical intrusion detection exists and is tested.

Stage4 inventory:
- Stage4 bootstrap carries `s4_genre_type`, `story_context`, and `style_guide`, but the Director ensemble selection API does not have an explicit `genre_strategy_semantics` parameter.
- Director prompts have general genre reward examples and advisory warnings, but no visible contract that "action_focused" in this work means business pressure rather than physical action.
- Preflight advisory flows are advisory transfer, not blueprint patching. This is consistent with the desired authority model.

Material-side inventory:
- `work_guard` and investment style reference already contain enough semantic material to define a business-power action/tension register.
- The implementation should derive a compact runtime contract from existing material; it should not invent new facts.

## 6. Pass 2. Semantic Classification

Confirmed root issue:
- Physical-action defaults are embedded in Stage3 strategy names, directives, scene presets, and prompt descriptions.
- The current guard prevents some unauthorized physical intrusions after the model proposes them; it does not prevent the model from being invited toward the wrong action register.

Confirmed available substrate:
- `work_guard` and investment style guide provide genre-register material.
- Stage3 already has genre and prompt construction chokepoints.
- Stage4 already has advisory/context surfaces where a contract can be made visible without granting Python final quality authority.

Inferred, not proven from local terminal artifacts:
- The current vehicle/intrusion symptoms likely arise from the mismatch between investment-family material and physical-action strategy defaults.
- #56 should reduce downstream Stage4 rejects and post-select conflicts, but this needs fresh proof after implementation.

Blocked until implementation/proof:
- Exact reject-rate delta.
- Runtime delta.
- Whether #56 alone materially improves the clean 5-arc proof path or must be paired with #58 and Frontier Lag work.

## 7. Side-Effect Map

- file writes / artifacts: expected edits to Stage3/Stage4 code, prompt config, tests, and docs; this SSOT and temp mirror are queue artifacts.
- DB / schema / transaction boundaries: not expected for the initial implementation. Fresh proof may read `stage_attempts`, `director_selections`, `blueprints`, `manuscripts`, and episode metadata.
- JSONL / log / audit sinks: operator warnings and candidate rejection logs should preserve evidence if physical intrusion is rejected.
- console / UI / operator output: if a candidate is disqualified or a genre contract is applied, logs should show enough context without truncating Director/advisory reasons.
- rollback / recovery / retry: Stage4 retry should not reintroduce stale physical-action prompts from cached envelopes.
- cache / global state: prompt envelope/cache keys must account for the genre strategy contract so stale strategy text cannot silently survive.
- bootstrap fallback / config-env mutation: no environment or GCP change is expected for this item.

## 8. Realization Architecture

1. Introduce a compact genre strategy semantics contract.
   - Preserve public strategy names such as `action_focused` for compatibility.
   - For investment/business-power family, map `action_focused` to deal pressure, timing risk, institutional confrontation, capital exposure, governance/legal threat, and next-gate cliffhanger.
   - Do not mutate canonical material files automatically; read and condense their semantics.

2. Attach the contract at Stage3 generation time.
   - Stage3 prompts should receive the contract near strategy directive and scene preset guidance.
   - `action_peak` for investment should read as business/action climax, not combat/chase.
   - Candidate `_ensemble_meta` should retain enough metadata to prove which genre contract shaped the candidate.

3. Carry the contract into Stage4 selection.
   - The Director prompt should see the contract as a selection context or advisory route input.
   - The Director should reject/repair candidates that satisfy generic action but violate the current work's business-power register.
   - Python should not decide "good investment scene"; it should only make the contract visible and preserve hard tactical guards.

4. Keep the tactical guard.
   - Existing unauthorized intrusion/vehicle chase tests must stay green.
   - Add new tests that prove the root prompt/strategy mapping prevents those directions before the guard is needed.

## 9. Execution Tranches

### Tranche A - Test-first genre semantics regression net

- Add tests in `tests/test_blueprint_ensemble_generate_ensemble.py` that build an investment/business-power context and assert `action_focused` prompt/directive text does not contain combat, chase, intruder, vehicle attack, or physical-crisis defaults unless the tactical excerpt authorizes them.
- Add a deterministic prompt-envelope test proving the genre strategy contract is included and cache-visible.
- Add or extend Stage4 prompt tests proving the Director sees the same business-power strategy contract.

### Tranche B - Stage3 strategy semantic map

- Implement a small helper or module boundary for genre/family strategy semantics.
- Keep default behavior conservative for existing genres.
- Add an investment/business-power mapping for action/tension/peak/cliffhanger terms.
- Store the selected contract in candidate metadata.

### Tranche C - Prompt and material ingress

- Update `config/prompts/ensemble.yaml` or the prompt assembly layer so scene preset descriptions are contract-aware.
- Place the contract close to `{strategy_directive}` and before generic scene preset usage.
- Pull from `work_guard`/style guide through existing material-loading paths where practical.

### Tranche D - Stage4 Director visibility

- Add a Director-visible genre strategy block through an explicit parameter or an existing authority carrier.
- Prefer advisory/route labeling where persisted.
- Ensure Stage4 selection can criticize "wrong kind of action" without relying on Python to score narrative quality.

### Tranche E - Guard preservation and operator evidence

- Preserve `_detect_unauthorized_tactical_intrusion` and current rejection tests.
- Add operator evidence that distinguishes "contract applied" from "candidate disqualified by tactical guard."
- Do not lower existing block coverage for physical entry/vehicle-chase signatures.

### Tranche F - Benchmark and live proof packet

- Before fresh live proof, capture baseline comparison targets from early-April-or-earlier artifacts where available and current-run evidence:
  - runtime per episode/arc,
  - Stage3 candidate reject/disqualification count,
  - Stage4 reject rate,
  - `POST_SELECT_CONFLICT` count,
  - unauthorized physical-action misfire count,
  - clean 5-arc completion status.
- After implementation, run targeted tests first, then a bounded canary/live proof.
- Report deltas to the relevant benchmark GitHub issues and #56.

## 10. Acceptance Criteria

- Investment/business-power `action_focused` no longer prompts combat, chase, physical crisis, or thriller intrusion as the default action register.
- Stage3 prompt envelopes and candidate metadata expose the selected genre strategy contract.
- Stage4 Director selection sees the same contract and can reason about business-power action/tension mismatch.
- Existing tactical guard tests for unauthorized intruder and vehicle chase behavior still pass.
- No Python routine is introduced that makes final LLM narrative quality judgments.
- Fresh proof includes benchmarkable runtime/reject-rate evidence, not only static tests.

## 11. Verification Plan

- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q`
- `python -m pytest tests/test_stage4_orchestrator.py tests/test_tf29_open_review.py -q`
- `python scripts/check_utf8_hygiene.py <touched docs/code/tests>`
- `python scripts/ops_validator.py --strict`
- Fresh bounded live/canary run after implementation, with runtime and rejection metrics captured for benchmark comparison.

## 12. Guardrails

- Do not remove the tactical guard until a separate future issue proves it is redundant; this SSOT assumes it remains.
- Do not patch output artifacts or material facts to hide a prompt/strategy defect.
- Do not rely on console rendering for Korean/UTF-8 conclusions; byte-level UTF-8 read-back wins.
- Do not treat unseen T01-T10 investigation claims as evidence. Merge any later-discovered reports before code realization.
- Do not start implementation from this SSOT without a fresh 3-pass re-audit against the current workspace.

## 13. Temp Queue Notes

- temp status: in_progress
- queue role: front active, operator-promoted compact execution tranche
- roadmap dependency: no formal dependency edge, but #56 should be considered before a new clean 5-arc proof claim because it can reduce physical-action drift that otherwise surfaces downstream.
- cleanup condition: after implementation, targeted tests, fresh proof packet, and #56 status update are complete, remove only `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md` through the closure harness.

## 14. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state entry: `docs/temp/queue-state.json`
- canonical roadmap: `docs/2026-04-27/security-and-frontier-active-execution-roadmap.md`
- temp roadmap mirror: `docs/temp/execution-roadmap.md`

## 15. 3-Pass Document Audit

Pass 1 - structure and artifact truth:
- PASS. Canonical and temp paths are defined.
- PASS_WITH_LIMITATION. The claimed ten #56 terminal results are not present as local or GitHub-readable artifacts; this limitation is explicit.
- PASS. Source docs and live source evidence are listed.

Pass 2 - semantic truth:
- PASS. The root issue is separated from the existing tactical guard.
- PASS. Stage3, Stage4, material-side, prompt, cache, log, and benchmark side effects are covered.
- PASS. Inferred live-run impact is labeled as inferred, not proven.

Pass 3 - execution readiness:
- PASS. Tranches are implementation-ready but require fresh re-audit before code edits.
- PASS. Acceptance criteria preserve Director authority and the tactical guard.
- PASS. Benchmark/live proof requirements are explicit.

Estimated operational confidence: 95%.

## 16. Implementation Ledger - 2026-04-27 Tranche A/B Partial

Implemented:
- Added deterministic Stage3 genre strategy contract construction in `modules/domain/agents/blueprint_ensemble.py`.
- Investment/business-power `action_focused` now receives a route-level contract prompt instead of the raw physical-action directive.
- Stage3 candidate `_ensemble_meta` now preserves `genre_strategy_contract` with `authority_level: route`, `authority_source`, `contract_id`, and `contract_hash`.
- Stage4 Director ensemble prompt now extracts the selected blueprint's `genre_strategy_contract` into a Director-visible advisory block.
- `config/prompts/ensemble.yaml` no longer labels `action_peak` as physical combat/action by default.
- Added deterministic regressions in `tests/test_blueprint_ensemble_generate_ensemble.py` for investment prompt semantics, authority boundary, and metadata preservation.
- Added `tests/test_tf29_open_review.py` coverage proving the Director prompt receives the contract as advisory context, not Python verdict authority.
- Added Stage3 prompt envelope contract summary with `contract_id`, `contract_hash`, and `authority_level`.
- Added Stage3 blueprint comparison prompt visibility for candidate-level `genre_strategy_contract`.
- Added deterministic proof that cached prompt and full fallback prompt both carry the same contract id/hash.

Not yet implemented:
- GitHub #56 status update.
- Full live LLM proof packet with fresh archived benchmark sidecars.
- Queue closure; this item remains active until live proof and operator/GitHub status handling are complete or explicitly deferred.

Validation:
- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -q` -> PASS, 66 tests.
- `python -m pytest tests/test_director_modules.py::TestDirectorEnsemble::test_build_blueprint_compare_prompt_includes_prev_ending_and_advisory_block tests/test_tf29_open_review.py -q` -> PASS, 7 tests.
- `python -m pytest tests/test_stage3_director_compare_advisory_lane.py -q` -> PASS, 3 tests.
- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py tests/test_stage3_director_compare_advisory_lane.py tests/test_director_modules.py::TestDirectorEnsemble::test_build_blueprint_compare_prompt_includes_prev_ending_and_advisory_block tests/test_tf29_open_review.py -q` -> PASS, 76 tests.
- `python -m py_compile modules/domain/agents/blueprint_ensemble.py` -> PASS.
- `python -m py_compile modules/domain/agents/director_ensemble.py` -> PASS.
- `python -m py_compile modules/domain/agents/blueprint_ensemble.py modules/domain/agents/director_ensemble.py` -> PASS.
- `python scripts/check_utf8_hygiene.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/director_ensemble.py config/prompts/ensemble.yaml tests/test_blueprint_ensemble_generate_ensemble.py tests/test_tf29_open_review.py tests/test_director_modules.py tests/test_stage3_director_compare_advisory_lane.py docs/2026-04-27/stage3-stage4-genre-alignment-execution-ssot.md docs/temp/stage3-stage4-genre-alignment-execution-ssot.md docs/2026-04-27/security-and-frontier-active-execution-roadmap.md docs/temp/execution-roadmap.md` -> PASS.
- `python scripts/sync_temp_queue_state.py` -> PASS; wrote `docs/temp/queue-state.json` with `stage3-stage4-genre-alignment` status `in_progress`, queue_role `front_active`, roadmap_rank `2`.
- `python scripts/ops_validator.py --strict` -> PASS after canonical/temp mirror sync and queue-state regeneration.
- `python scripts/report_benchmark_operator_lines.py` -> PASS; report line: `status=clean; ci_gate=pass; live_records=0; stale_index_rows=9`.
- `git diff --check -- <touched #56 code/tests/docs plus queue-state>` -> PASS with only a line-ending warning on `tests/test_tf29_open_review.py`.
- Live canary not run: the bounded candidate is `scripts/run_stage34_canary.py full --source-project "projects/01_골든카나리아" --target-project "_canary/issue56_stage34_alignment_ep4_r1" --from-ep 1 --target-ep 4`, but current shell lacks checked Vertex/GCP auth environment variables, and the run would spend live LLM budget.

Complexity recount:
- `build_genre_strategy_contract`: 42 LOC.
- `format_genre_strategy_contract_prompt`: 11 LOC.
- `_generate_single`: 97 LOC.
- `_build_blueprint_prompt_bundle`: 76 LOC.
- `_request_blueprint_generation`: 61 LOC.
- `_format_genre_strategy_contract_block`: 24 LOC.
- `_build_ensemble_prompt_request`: 119 LOC.
- `_build_blueprint_compare_prompt`: 147 LOC. Classification: bounded prompt assembly shell; no new semantic scoring authority added, and further extraction is deferred to avoid widening this compact #56 tranche.
- No touched production function entered the 180+ LOC band.

3-pass implementation audit:
- Pass 1 - authority/sink: PASS. Python constructs a route-level prompt contract and metadata; it does not own Director verdict authority or mutate material facts.
- Pass 2 - diff audit: PASS. Existing tactical intrusion guard remains; prompt changes remove default physical action invitation for investment `action_focused`.
- Pass 3 - verification: PASS for Stage3 deterministic tranche, Stage3 blueprint selection visibility, and Stage4 Director-visible advisory carrier. Live proof remains open because `benchmarks/` has zero live records with backing sidecars in this checkout.

Estimated post-implementation confidence for deterministic #56 tranche: 96%.

## 17. Implementation Ledger - 2026-04-27 Combined Regression Isolation Hardening

Implemented:
- `modules/core/prompt_loader.py` now refreshes its singleton prompt directory when the active `PROMPT_DIR`/runtime context changes between calls. This prevents a prior temp prompt directory from leaking into later Stage3/Stage4 prompt tests or runtime flows.
- `modules/domain/agents/director_ensemble.py` now preserves the Director-visible genre strategy contract even when a compact/stub prompt template omits `{story_context}`. If the selected blueprint carries a contract and the rendered variable/fallback prompt does not include it, the contract block is appended as advisory context.
- This keeps the #56 rule intact: Python formats and carries route/advisory context, while Director remains the verdict authority.

Validation:
- `python -m pytest -q tests/test_director_modules.py tests/test_tf29_open_review.py::TestOpenReviewPropagation::test_director_prompt_receives_genre_strategy_contract_as_advisory` -> PASS, 135 tests.
- `python -m pytest -q tests/test_failure_analyzer.py tests/test_audit_service.py tests/test_bridge_quality_summary.py tests/test_desktop_direct_surface_contract.py tests/test_frontend_frontier_lag_wiring.py tests/test_ui_renderer_sanitization.py tests/test_blueprint_ensemble_generate_ensemble.py tests/test_director_modules.py tests/test_stage3_director_compare_advisory_lane.py tests/test_tf29_open_review.py` -> PASS, 321 tests.
- `python -m pytest -q tests/test_prompt_loader.py tests/test_bridge_quality_summary.py::test_quality_dashboard_endpoint_surfaces_config_authority_summary` -> PASS, 30 tests.
- `python -m py_compile modules/core/prompt_loader.py modules/domain/agents/director_ensemble.py modules/domain/agents/blueprint_ensemble.py modules/core/failure_analyzer.py modules/core/services/audit_service.py` -> PASS.
- `python scripts/check_utf8_hygiene.py modules/core/prompt_loader.py modules/domain/agents/director_ensemble.py` -> PASS.
- `git diff --check -- modules/core/prompt_loader.py modules/domain/agents/director_ensemble.py` -> PASS.

Complexity recount:
- `PromptLoader.__init__`: 6 LOC.
- `_build_ensemble_prompt_request`: remains under the 120 LOC guardrail threshold after the fail-safe addition.
- No touched production function entered the 180+ LOC band.

Residual open work:
- Full live LLM proof packet remains open.
- GitHub #56 final status/closure handling remains open.
- Queue closure remains blocked until live proof is completed or explicitly deferred.

3-pass implementation audit:
- Pass 1 - authority/sink: PASS. The change preserves prompt/context transport only and does not mutate material facts or verdict authority.
- Pass 2 - regression evidence: PASS. The prior combined shard failure is now covered by a 321-test shard, plus a focused prompt-loader isolation shard.
- Pass 3 - readiness: PASS for deterministic #56 hardening. Live proof remains the remaining acceptance blocker.

Estimated post-hardening confidence for deterministic #56 tranche: 97%.

## 18. Live Proof Attempt Ledger - 2026-04-27 r1/r2 Canary Attempts

Attempted commands:
- `python scripts/run_stage34_canary.py full --source-project "projects/01_골든카나리아" --target-project "projects/_canary/issue56_stage34_alignment_ep4_r1" --from-ep 1 --target-ep 4`
- `python scripts/run_stage34_canary.py full --source-project "projects/01_골든카나리아" --target-project "projects/_canary/issue56_stage34_alignment_ep4_r2" --from-ep 1 --target-ep 4`
- Command-local live env used for the r2 attempt: `VERTEX_PROJECT_ID=gen-lang-client-0159412471`, `GOOGLE_CLOUD_PROJECT=gen-lang-client-0159412471`, `VERTEX_LOCATION=us-central1`, `GOOGLE_CLOUD_LOCATION=us-central1`.

Preflight:
- `gcloud auth list` reported active account `barobook001@gmail.com`.
- `gcloud config get-value project` reported `gen-lang-client-0159412471`.
- Shell environment did not have persistent `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `VERTEX_PROJECT`, `VERTEX_LOCATION`, or `GOOGLE_CLOUD_LOCATION` set before the command-local injection.
- `gcloud ai models list --region=us-central1 --limit=1` reached the Vertex endpoint and returned successfully with zero listed model rows.

r1 result:
- Status: prepare failed before live proof.
- Cause: Windows file lock during target reset.
- Error: `PermissionError: [WinError 32] ... projects/_canary/issue56_stage34_alignment_ep4_r1/logs/artifacts/stage3/ep_0011/attempt_01/final_blueprint__action_focused.json`.
- Evidence path: partial target `projects/_canary/issue56_stage34_alignment_ep4_r1/`.

r2 result:
- Status: live run started and was stopped after the shell timeout.
- Timeout: 20 minutes.
- Runner cleanup: the lingering `python.exe scripts/run_stage34_canary.py full ... issue56_stage34_alignment_ep4_r2` process was terminated after timeout.
- Evidence path: `projects/_canary/issue56_stage34_alignment_ep4_r2/logs/stage34_canary_summary.json`.
- Session log: `projects/_canary/issue56_stage34_alignment_ep4_r2/logs/session_20260427_214842.log`.
- The log proves live Vertex calls reached `https://aiplatform.googleapis.com/.../locations/global/publishers/google/models/gemini-3.1-pro-preview:generateContent` with HTTP 200 responses.

r2 analyzed result:
- `stage3_latest_session_id`: `20260427_214844`.
- Stage3 current-session sink alignment: `status=ok`, `attempts_considered=2`, `complete_final_attempts=2`, `coverage_gap_count=0`, `structured_issue_count=0`.
- Stage4 latest session id: empty.
- Stage4 attempts: `0`.
- Draft count: `0`.
- `multi_stage_proof_scope_summary.status`: `fail`.
- Errors: `stage4_session_missing`, `stage4_current_session_summary_missing`.
- Stage4 hard gate errors: `draft_count_mismatch:0!=4`, `sink_alignment_summary_empty`.
- Interpretation: this is useful partial live evidence for Stage3 prompt/runtime path and Vertex connectivity, but it is not #56 acceptance proof because Stage4 live generation did not complete.

Benchmark/operator follow-up:
- `python scripts/report_benchmark_operator_lines.py --format json` still reports `live_records=0`.
- `python scripts/report_benchmark_operator_lines.py --format json --latest-live-pair` fails because fewer than two live benchmark records are available.
- No clean benchmark pair or fresh terminal #56 closure proof can be claimed from this attempt.

Residual open work:
- A bounded canary needs either a longer wall-clock window or a smaller target scope that reaches Stage4 and archives a benchmark sidecar.
- The r1/r2 partial canary directories are evidence artifacts and were left in place.
- GitHub #56 should remain open.

3-pass live-attempt audit:
- Pass 1 - artifact truth: PASS. r2 produced `stage34_canary_summary.json` and a session log; r1 produced a partial target and a prepare failure.
- Pass 2 - semantic truth: PASS. The attempt proves Stage3 live path and Vertex connectivity, but it explicitly fails Stage4 proof.
- Pass 3 - closure readiness: FAIL for #56 closure. Deterministic hardening is stronger, but live proof remains incomplete.

Estimated confidence in deterministic fix after live partial evidence: 97%.
Estimated confidence in #56 closure readiness: 70%, because Stage4 live proof is still missing.

## 19. Live Proof Ledger - 2026-04-27 r5 Stage34 Canary PASS

Implemented before r5:
- `modules/core/stage4_canary_tools.py` now retries transient `PermissionError` during canary target cleanup and makes target paths writable before retrying. This is scoped to canary cleanup and is intended to absorb short Windows file-lock windows during `shutil.rmtree`/`unlink`.
- `tests/test_stage4_canary_tools.py` adds a regression proving `_remove_path` retries a transient Windows-style permission error.

Invalid short-scope attempt:
- `target_ep=2` was attempted as `projects/_canary/issue56_stage34_alignment_ep2_r4` after cleanup retry hardening.
- Prepare succeeded, but run was rejected because the canary requires `target_ep` to match a designed arc frontier endpoint.
- Error: `target_ep must match a designed arc frontier ep_end for stage34 canary run (target_ep=2, designed_arc_ends=[4, 9, 13, 17, 20, 24, 28])`.

r5 command:
- `python scripts/run_stage34_canary.py full --source-project "projects/01_골든카나리아" --target-project "projects/_canary/issue56_stage34_alignment_ep4_r5" --from-ep 1 --target-ep 4`
- Command-local live env: `VERTEX_PROJECT_ID=gen-lang-client-0159412471`, `GOOGLE_CLOUD_PROJECT=gen-lang-client-0159412471`, `VERTEX_LOCATION=us-central1`, `GOOGLE_CLOUD_LOCATION=us-central1`.

r5 live proof result:
- Target: `projects/_canary/issue56_stage34_alignment_ep4_r5`.
- Summary: `projects/_canary/issue56_stage34_alignment_ep4_r5/logs/stage34_canary_summary.json`.
- `stage3_latest_session_id`: `20260427_221405`.
- `stage4_latest_session_id`: `20260427_221405`.
- `shared_session_id`: `20260427_221405`.
- `multi_stage_proof_scope_summary.status`: `pass`.
- Stage3 live generation path: `covered`.
- Stage4 live generation path: `covered`.
- Covered surfaces: `stage3_live_generation_path`, `stage4_live_generation_path`, `stage4_rationale_contract`, `stage4_companion_audit`.
- Uncovered surfaces: `stage2_live_generation_path`, `backend_wide_multi_stage_runtime`.
- Stage3 sink alignment: `ok`.
- Stage4 current-session sink alignment: `ok`.
- Stage4 attempts: `4`.
- Draft count: `4`.
- Stage4 hard gates: `status=warn`, `errors=[]`, `warnings=["stage4_retry_contract_not_exercised"]`.
- Interpretation: #56 has a valid bounded Stage3->Stage4 live proof for the first arc endpoint. It is not a backend-wide multi-stage runtime proof and does not exercise Stage4 retry-contract behavior.

Benchmark archive:
- Archive run id: `20260427_230217__stage34-canary__target-ep4__f484f59c`.
- Record root: `benchmarks/issue56_stage34_alignment_ep4_r5/20260427_230217__stage34-canary__target-ep4__f484f59c`.
- `benchmarks/benchmark_index.csv` now has `indexed_rows=10`, `live_records=1`.
- Native post-run evidence was backfilled:
  - `benchmarks/issue56_stage34_alignment_ep4_r5/20260427_230217__stage34-canary__target-ep4__f484f59c/native-post-run-evidence.json`.
  - `benchmarks/issue56_stage34_alignment_ep4_r5/20260427_230217__stage34-canary__target-ep4__f484f59c/benchmark_companion_links.json`.
- `python scripts/report_benchmark_operator_lines.py --format json` -> `records_with_sidecar=1`, companion `linked=post_run_evidence_json`.
- `python scripts/report_benchmark_operator_lines.py --format json --latest-live-pair` still fails because fewer than two live benchmark records are available. This is a compare-pair limitation, not a failure of the r5 single-run archive.

Validation:
- `python -m pytest -q tests/test_stage4_canary_tools.py::test_canary_remove_path_retries_transient_windows_permission_error tests/test_stage4_canary_tools.py::test_prepare_stage34_canary_project_resets_blueprints_and_stage3_stage4_outputs` -> PASS, 2 tests.
- `python -m pytest -q tests/test_backfill_benchmark_native_post_run_evidence.py tests/test_report_benchmark_operator_lines.py -q` -> PASS, 12 tests.
- `python -m py_compile modules/core/stage4_canary_tools.py` -> PASS.
- `python scripts/check_utf8_hygiene.py modules/core/stage4_canary_tools.py tests/test_stage4_canary_tools.py benchmarks/benchmark_index.csv .../manifest.json .../native-post-run-evidence.json .../benchmark_companion_links.json` -> PASS.
- `git diff --check -- modules/core/stage4_canary_tools.py tests/test_stage4_canary_tools.py benchmarks/benchmark_index.csv` -> PASS, with a line-ending warning for `benchmarks/benchmark_index.csv`.

Residual open work:
- GitHub #56 should remain open until the local #56 bundle is published/reviewed through PR/CI or the operator explicitly accepts local-only closure.
- `stage4_retry_contract_not_exercised` remains a hard-gate warning, not a #56 genre-alignment blocker by itself.
- Only one live benchmark record exists, so pair comparison remains unavailable.
- r1/r2/r3/r4/r5 canary directories remain local evidence artifacts.

3-pass live-proof audit:
- Pass 1 - artifact truth: PASS. r5 produced Stage3/Stage4 canary summary, drafts, artifacts, benchmark archive, native post-run evidence, and companion links.
- Pass 2 - semantic truth: PASS_WITH_LIMITATION. The first arc endpoint has a shared-session Stage3->Stage4 live proof, but retry-contract and backend-wide proof surfaces are not covered.
- Pass 3 - closure readiness: PASS_WITH_LIMITATION. #56 acceptance evidence is materially stronger and live proof exists, but repo closure should wait for PR/CI and final GitHub handling.

Estimated confidence in #56 deterministic plus bounded live proof: 97%.
Estimated confidence in immediate issue closure without PR/CI: 85%.
