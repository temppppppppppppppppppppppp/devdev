# Stage23 Current-Main Static Parallel Survey

Date: 2026-04-11
Status: final
Canonical Path: `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
Baseline Dirty Summary: `clean`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `same-turn read-only survey on reset main; stale 2026-04-11 backup branch work is intentionally excluded from authority and execution planning`

## 1. Question

After resetting to `main@2b7cb64f`, what Stage2 and Stage3 static risks remain on the live workspace, and which existing execution lanes should own them?

## 2. Scope

Included:

- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/failure_analyzer.py`
- directly relevant Stage2 / Stage3 guardrail and observability tests

Excluded:

- stale 2026-04-11 backup-branch code and docs
- fresh reruns, DB writes, or runtime validation
- broad Stage4 and Stage0 queue reprioritization

## 3. Findings

### 3.1 Stage3 truth-first risks

1. `P1`: success proof sinks still precede committed blueprint persistence.
   - `Stage3Orchestrator._handle_success(...)` records success observability before blueprint persistence and commit confirmation.
   - If `save_episode_blueprint(...)` or `safe_commit()` fails, success-like sink rows can exist for a logically failed path.
2. `P1`: opening and capital authority at the Stage2 -> Stage3 seam are still under-enforced.
   - `arc_start_state` can be applied and then weakened again by stale `prev_blueprint.protagonist_state`.
   - `capital_continuity_packet` still reads finance event families without episode-boundary filtering.
3. `P2`: Stage3 `runtime_advisory` / `retry_directives` remain blank by default.
   - success and reject persistence hardcode empty strings
   - `FailureAnalyzer` sink-alignment parity still only treats those fields as Stage2-owned
4. `P3`: `PASS_WITH_FIX` is success in Stage3 control flow but not in Stage3 pass-rate accounting.

### 3.2 Stage2 residual risks

1. `P2`: `runtime_advisory` can still go blank on PASS_WITH_FIX advisory-heavy paths because the explicit field is preferred over reason-derived pressure.
2. `P2`: Stage2 `ep_num` semantics still split between:
   - absolute episode start in `single_arc_attempt` heartbeat/progress
   - arc ordinal in authoritative DB/session sinks
3. `P2`: carryover authority remains only partially authoritative on arc start.
   - start-side equipment is synchronized
   - start location / capital / total-assets / portfolio-position can still remain stale while downstream summaries trust them
4. `P3`: Stage2 long-method / owner-surface pressure remains high, but this is lower urgency than the Stage3 truth-first seams above.

## 4. Execution Promotion Mapping

- `0_0-stage3-contract-tightening-remediation`
  - success proof sink ordering after committed persistence
  - Stage3 `runtime_advisory` / `retry_directives` normalization
  - `PASS_WITH_FIX` success accounting parity
- `0_0-stage3-opening-transition-contract-normalization-remediation`
  - authoritative `arc_start_state` intake for opening-state packeting
  - capital continuity episode-boundary filtering
- `0_0-stage2-contract-normalization-remediation`
  - Stage2 `runtime_advisory` fallback tightening
  - `ep_num` / `current_ep_start` observability semantics cleanup
  - broader carryover-authority start-state truth beyond equipment-only sync

No new queue lane is needed.

## 5. Queue Consequence

- keep the current Stage4 front stack unchanged
- inside the S2 / S3 family, `0_0-stage3-contract-tightening-remediation` now outranks `0_0-stage2-contract-normalization-remediation` on current-main severity
- `0_0-stage3-opening-transition-contract-normalization-remediation` remains a sibling follow-up inside the Stage3 family, not a new front-of-queue proof lane
- Stage2 remains open, but it should no longer rely on the older `no live Stage2 P0-P2` phrasing

## 6. 3-Pass Audit

Pass 1. Structure / Scope
- kept this as a compact current-main survey rather than a new execution SSOT
- bounded scope to live Stage2 / Stage3 code plus direct tests
- excluded stale backup-branch work and runtime reruns

Pass 2. Evidence / Consistency
- confirmed current authority against `main@2b7cb64f`
- re-read the active roadmap and target execution SSOTs before promotion mapping
- grounded each promoted item in live code anchors rather than stale 2026-04-11 backup diffs

Pass 3. Execution / Readability
- mapped findings into existing queue lanes instead of opening a new lane
- separated Stage3 truth-first work from Stage2 lower-severity proof/observability residue
- kept queue consequence explicit and bounded

Confidence: `96%`
