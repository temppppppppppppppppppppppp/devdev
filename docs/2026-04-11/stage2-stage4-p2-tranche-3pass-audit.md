# Stage2-Stage4 P2 Tranche 3-Pass Audit

Date: 2026-04-11
Status: final
Canonical Path: `docs/2026-04-11/stage2-stage4-p2-tranche-3pass-audit.md`
Doc Type: targeted system-track audit
Scope: Stage2 P2 normalization tranche plus Stage4 FailureAnalyzer parity widening landed on top of `main`
Baseline Commit: `2b7cb64f`
Baseline Dirty Summary: workspace dirty; bounded audit scope limited to 6 touched files in this tranche
Resume Commit: `2b7cb64f`
Resume Drift Summary: same baseline commit; touched-area diff present in `modules/core/` and `tests/`
Related Queue Docs:
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`

## 1. Scope

This audit covers the bounded P2 tranche that just landed in:

- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/failure_analyzer.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage2_orchestrator_lane_f.py`
- `tests/test_failure_analyzer.py`

Excluded on purpose:

- fresh runtime rerun
- queue-state / ClickUp mutation
- broader Stage3 / Stage4 runtime artifact truth
- structural `P3` owner-surface cleanup outside this tranche

## 2. Evidence Basis

Primary evidence:

- live code readback for touched functions
- touched-area diff review
- targeted low-memory validation

Verification commands:

- `python -m ruff check modules/core/failure_analyzer.py modules/core/stage2_finalizer.py modules/core/stage2_orchestrator.py tests/test_failure_analyzer.py tests/test_stage2_finalizer.py tests/test_stage2_orchestrator_lane_f.py`
- `python scripts/check_utf8_hygiene.py modules/core/failure_analyzer.py modules/core/stage2_finalizer.py modules/core/stage2_orchestrator.py tests/test_failure_analyzer.py tests/test_stage2_finalizer.py tests/test_stage2_orchestrator_lane_f.py`
- `pytest tests/test_failure_analyzer.py -q`
- `pytest tests/test_stage2_finalizer.py -q`
- `pytest tests/test_stage2_orchestrator_lane_f.py -q`
- `pytest tests/test_failure_analyzer.py tests/test_stage2_finalizer.py tests/test_stage2_orchestrator_lane_f.py -q`

Observed results:

- targeted shard total: `98 passed`
- UTF-8 hygiene: pass
- ruff: pass
- py_compile on touched files: pass

## 3. Pass 1 Audit

### Structure and scope

The tranche matches the requested `P2 first` shape:

- Stage2 `runtime_advisory` fallback widened
- Stage2 `single_arc_attempt` `ep_num` semantics normalized
- Stage2 opening-state carryover truth widened to `location / total_assets / capital / portfolio_position`
- Stage4 FailureAnalyzer sink/rationale parity widened to include Stage4 `runtime_advisory / retry_directives`

Side-effect scope checked:

- DB writes
- session decision sink
- pass-rate monitor sink
- director selection sink
- Stage2 UI/operator-visible event payloads
- tactical doc sync path

No path-policy issues found. This is an audit doc only, so no `docs/temp/` mirror was created.

## 4. Pass 2 Audit

### Evidence and consistency

What landed cleanly:

- `Stage4` final sink union now includes `pass_rate_monitor` and `director_selections` for stage 4 in `FailureAnalyzer`.
- `Stage4` rationale parity now inspects `runtime_advisory` and `retry_directives` for stage 4 across `stage_attempts`, `director_selections`, and `session_decisions`.
- `Stage2` authoritative sinks now share the same widened `runtime_advisory` fallback path instead of leaving the field blank when only verdict/open-review style rationale exists.
- `Stage2` operator-facing `single_arc_attempt` events now use `ep_num=global_arc_no` and preserve absolute episode start in `meta.current_ep_start`.
- `Stage2` opening-state carryover now syncs previous arc `arc_end_state` values into current `arc_start_state` for:
  - `location`
  - `total_assets`
  - `capital`
  - `portfolio_position`

Residual inconsistency still present:

### Finding 1. `P2` residual

`_sync_first_episode_start_state_line()` still rewrites only `location`, `equipment`, `injuries`, and `internal_energy`, while the newly widened carryover sync now updates `total_assets`, `capital`, and `portfolio_position` only in structured `arc_start_state`.

Evidence:

- financial start-state sync is introduced at `modules/core/stage2_finalizer.py:1784`
- tactical text sync still calls `_sync_first_episode_start_state_line()` at `modules/core/stage2_finalizer.py:1811`
- the helper itself still rewrites only four fields at `modules/core/stage2_finalizer.py:218` and `modules/core/stage2_finalizer.py:232`

Operational consequence:

- authoritative structured state can now be correct while a tactical-doc `[시작 상태]` line with financial fields remains stale
- this is not a crash risk, but it is still an operator-visible and artifact-visible carryover truth gap

Severity:

- `P2`

### Finding 2. `P3` test-coverage residual

The new Stage4 aligned-parity test validates final sink coverage and Stage4 rationale parity, but it does not include a matching `episode_production` aligned row in the green-path fixture.

Evidence:

- aligned Stage4 parity test lives at `tests/test_failure_analyzer.py:2530`
- the fixture writes `stage_attempts`, `director_selections`, `session_decisions`, and `pass_rate_monitor`
- no aligned `episode_production` fixture row is present in that test body

Operational consequence:

- lifecycle parity is still partially exercised by older tests and by the mismatch path, but the newly added aligned path is not full-lifecycle complete

Severity:

- `P3`

## 5. Pass 3 Audit

### Execution and readability

The tranche is actionable and bounded:

- no new queue artifact was required
- no runtime rerun was silently performed
- touched-area validation is sufficient for code-side closure of this tranche

Guardrails respected:

- manual edits used bounded file scope
- no unrelated dirty files were reverted
- no temp mirror / ClickUp update was done during audit-only work
- no fresh run was triggered even though the next proof step is obvious

## 6. Conclusion

Current audit verdict:

- no new `P0`
- no new `P1`
- `P2` one residual remains
- `P3` one test-coverage residual remains

Net judgment:

- the P2 tranche is materially improved and safe to keep
- before the next expensive fresh run, the highest ROI follow-up is a small Stage2 patch that extends tactical start-state text sync to financial carryover fields

Recommended next order:

1. patch Stage2 tactical `[시작 상태]` financial sync
2. optionally add one aligned Stage4 `episode_production` parity test
3. then run the deferred fresh proof wave

## 7. Confidence

Estimated confidence: `96%`

Why not higher:

- no fresh runtime proof was included in this audit
- one real Stage2 artifact-surface residual remains
- one Stage4 lifecycle green-path test gap remains
