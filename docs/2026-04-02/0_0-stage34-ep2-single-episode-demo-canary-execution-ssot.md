# 0_0 Stage34 ep2 Single-Episode Demo Canary Execution SSOT

Date: 2026-04-02
Status: partially_realized (code landed, static validation closed, demo runtime pending)
Canonical Path: `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md`
Commit State:
- Baseline Commit: `c32717ffc511389636c65edf2845bef6113b97c3`
- Baseline Dirty Summary: `dirty: regression-tier contract artifacts changed; new single-episode demo canary script/test untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `single-episode Stage34 demo runner landed; docs/roadmap sync and runtime demo proof pending`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-only-canary-blueprint-baseline-integrity-audit.md`
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage4-consumer-contract-normalization-remediation`

## 1. Answer First

The current demo problem is not another Stage4 seam. It is a runner-shape mismatch:

- `run_stage34_canary.py` is authoritative but forces arc-frontier execution, so it cannot stop at `ep2`
- `Stage4-only canary` is fast enough for demo use, but the blueprint baseline is no longer authoritative after the contamination audit

This lane introduces the missing middle path:

`frozen ep1 authority + fresh ep2 blueprint + fresh ep2 draft`

That gives demo-safe speed without reusing contaminated Stage4-only evidence and without paying arc-frontier cost through `ep4`.

## 2. Scope

Included:

- `scripts/run_stage34_ep_demo_canary.py`
- focused runner/contract regression tests
- validation-tier contract refresh
- roadmap/temp queue refresh

Excluded:

- broad canary redesign
- Stage2/Stage3 realization
- Stage4 closure proof claims
- source `0_0` mutation
- Stage4 resume declaration

## 3. Why Existing Runners Are Insufficient

### `run_stage34_canary.py`

- strong evidence quality
- wrong granularity for demo
- rejects `target_ep=2` because `0_0` designed arc frontiers are `4` and `9`

### `run_stage4_canary.py`

- correct granularity for demo
- wrong evidence boundary
- cannot currently be treated as authoritative closure evidence because Stage4-only retry/escalation can contaminate the frozen blueprint baseline

### Required middle path

- keep `ep1` manuscript/world-state/fact authority frozen
- regenerate only `ep2` Stage3 blueprint
- regenerate only `ep2` Stage4 draft
- stop there

## 4. Execution Tranches

### Tranche 1. Single-Episode Prepare Contract

Goal:

- reuse existing Stage3/4 prepare logic, but materialize explicit demo metadata proving:
  - frozen authority episode
  - regenerated blueprint episode
  - regenerated draft episode

Bounded targets:

- `scripts/run_stage34_ep_demo_canary.py`

Acceptance shape:

- prep writes dedicated metadata under `logs/stage34_ep_demo_canary_prep.json`
- stale `blueprint_*.txt` files at or after `from_ep` are removed for this demo lane

### Tranche 2. Single-Episode Run Contract

Goal:

- run Stage3 and Stage4 directly at one episode, without frontier-lag or arc-end gating

Bounded targets:

- `scripts/run_stage34_ep_demo_canary.py`

Acceptance shape:

- Stage3 calls `stage_3_batch_blueprinting(target_ep=2)`
- Stage4 calls `_stage_4_v2_chief_writer(target_ep=2, skip_pause=True)`
- `ep3+` generation is never entered

### Tranche 3. Single-Episode Analyze Contract

Goal:

- produce a compact proof artifact that is enough for demo judgment

Bounded targets:

- `scripts/run_stage34_ep_demo_canary.py`

Acceptance shape:

- summary writes `logs/stage34_ep_demo_canary_summary.json`
- summary reports:
  - frozen authority episode
  - regenerated blueprint/draft episode
  - stage3/session status
  - stage4/session status
  - boundary integrity for `ep3+`

### Tranche 4. Focused Regression Closure

Goal:

- lock the new runner and validation-tier contract with the smallest possible regression footprint

## 5. Non-Goals

- no broad canary framework merge
- no `Stage4-only` evidence rehabilitation in this lane
- no claim that this runner closes Stage4 globally
- no rewrite of frontier-lag orchestration

## 6. Acceptance Criteria

- prepare preserves `ep1` authority and resets only `ep2+` Stage3/4 outputs
- `ep2` is the only regenerated blueprint
- `ep2` is the only regenerated draft
- `ep3+` outputs are absent from the demo proof boundary
- the new runner is labeled as `FULL_CANARY_PROOF`
- no new `180+ LOC` production function is introduced

## 7. Verification Plan

- `python -m py_compile scripts/run_stage34_ep_demo_canary.py`
- `pytest tests/test_run_stage34_ep_demo_canary.py -q`
- `pytest tests/test_regression_validation_tier_contract.py -q`
- `pytest tests/test_run_stage3_canary.py tests/test_run_stage34_canary.py -q`
- `ruff check scripts/run_stage34_ep_demo_canary.py tests/test_run_stage34_ep_demo_canary.py scripts/regression_validation_tiers.py tests/test_regression_validation_tier_contract.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md docs/temp/0_0-stage34-ep2-single-episode-demo-canary-execution-ssot.md docs/2026-04-01/active-temp-execution-roadmap.md docs/temp/execution-roadmap.md docs/implementation/regression-validation-tier-contract-v1.json`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 8. Guardrails

- do not present this runner as Stage4 closure evidence
- do not fall back to contaminated Stage4-only reasoning just because it is faster
- keep `ep1` frozen-authority semantics explicit
- keep demo scope bounded to one regenerated episode

## 9. Temp Queue Notes

- temp status: `partial`
- cleanup condition:
  - keep the mirror while demo runtime proof is pending
  - remove when either:
    - demo proof is captured and this utility is no longer active, or
    - it is superseded by a more general authoritative runner
- roadmap dependency:
  - this lane is an operator-directed demo utility
  - it temporarily outranks broader Stage4 closure work for demo preparation
  - it does not replace the aggregate Stage4 consumer-contract wave

## 10. 3-Pass Audit Record

Pass 1, structure and scope:

- bounded the lane to a missing runner shape, not another Stage4 logic family
- kept closure/resume claims out of scope

Pass 2, evidence and consistency:

- tied the need for this lane directly to the Stage4-only contamination audit
- tied the frontier limitation directly to the existing Stage34 runner behavior
- aligned paths, target episode, and queue role

Pass 3, execution and readability:

- acceptance criteria cleanly distinguish demo utility from closure proof
- verification stays focused on the new runner and regression-tier contract
- operator consequence is explicit: faster demo-safe ep2 proof path

Confidence: `96%`
