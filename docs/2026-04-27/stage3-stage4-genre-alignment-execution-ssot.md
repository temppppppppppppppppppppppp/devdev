# Stage3/Stage4 Genre Alignment Execution SSOT

Date: 2026-04-27
Track: system
Status: execution-ready (parked future wave)
Canonical Path: `docs/2026-04-27/stage3-stage4-genre-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were already present under `docs/2026-04-27/` and `docs/temp/`; `docs/temp/queue-state.json` was modified before this SSOT; no production code was edited while preparing this document.
- Resume Commit: same-as-baseline
- Resume Drift Summary: no tracked source edits made while creating this SSOT
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
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage3-stage4-genre-alignment
  github_issue: 56
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 6
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

- temp status: pending
- queue role: parked future wave
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
