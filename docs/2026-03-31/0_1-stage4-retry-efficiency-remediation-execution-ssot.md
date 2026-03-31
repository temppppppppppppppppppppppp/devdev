# 0_1 Stage4 Retry Efficiency Remediation Execution SSOT

Date: 2026-03-31
Status: closed (3-pass audited, realized, runtime-bounded-validated)
Confidence: 96%
Document Type: execution SSOT
Canonical Path: `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-execution-ssot.md`
Temp Mirror Path: `(closed; mirror removed after canonical closure update)`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue/roadmap already dirty, multiple 2026-03-30 and 2026-03-31 docs plus artifact outputs untracked`
Resume Commit: `512b0d23498d386d5199db2c01304b0d53bfd5aa`
Resume Drift Summary: `0_1 stage34 canary plus targeted tests proved retry-lane attempt_key in runtime and left QR-7 escalation / TF-RH1 non-contradicted; mirror retired after closure`
Source Survey Docs:
- `docs/2026-03-31/0_1-stage4-ep1-15-db-log-bounded-audit.md`
- `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-survey.md`
- `docs/2026-03-31/0_1-stage4-ep8-15-retry-efficiency-bounded-survey.md`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-runtime-progress-audit.md`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-runtime-closure-proof-audit.md`
Evidence Artifacts:
- `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-evidence.json`
- `docs/2026-03-31/0_1-stage4-ep8-15-retry-efficiency-bounded-evidence.json`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-runtime-progress-evidence.json`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-runtime-closure-proof-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/canary_0_1_stage34_ep14_cw_hierarchy/logs/stage34_canary_summary.json`
- `projects/canary_0_1_stage34_ep14_cw_hierarchy/logs/session/ui_events.jsonl`
- `projects/canary_0_1_stage34_ep14_cw_hierarchy/logs/runtime_audit.jsonl`
- `projects/canary_0_1_stage34_ep14_cw_hierarchy/logs/episode_production.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe Stage 4 wave that improves retry efficiency without weakening correctness gates or defaulting to model-tier changes.

This execution wave is based on two now-stable survey conclusions:

1. late-stage retry inflation is primarily `downstream gate churn`, not `CW first-pass incompetence`
2. retry compression is currently weak because the system tolerates:
   - repeated `Director non-reject -> final reject` churn
   - duplicate candidate/hash reselection
   - `QR-7` plateau detection as advisory-only
   - retry-lane logs without `attempt_key`

This wave therefore does **not** try to redesign the whole Director policy stack, replace models, or reopen the EP9 truth-source substrate.

It does four bounded things:

1. make retry-lane policy/advisory events joinable to concrete attempts
2. promote `QR-7` from passive warning to bounded stop-or-escalate policy under explicit conditions
3. suppress wasteful duplicate artifact reselection when the retry context has not materially changed
4. require a fresh-session verification gate so efficiency work is not judged on stale in-memory code

## 2. Baseline Facts

- Stage 4 mean attempt rows rose from `1.29` on EP1-7 to `5.38` on EP8-15.
- EP8-15 reject rows are `35`; `31` of them (`88.6%`) are `Director PASS/PASS_WITH_FIX -> final REJECT`.
- Repeated artifact/candidate churn is material:
  - repeated-hash participation: `14 / 43`
  - repeated-candidate participation: `21 / 43`
- Some final PASS rows reused the exact prior rejected hash:
  - EP8
  - EP11
  - EP13
  - EP14
- `QR-7` currently logs a plateau warning but does not stop the loop.
  - EP13 `QR-7` was followed by 2 more Stage 4 rows
  - EP15 `QR-7` was followed by 2 more Stage 4 rows
- retry-lane JSONL events still omit `attempt_key` for the relevant Stage 4 policy/advisory rows.
- CW and Director already run on `gemini-3.1-pro-preview` across EP8-15, so the immediate ROI is not model uplift.

## 3. Scope

Included:

- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_interview_round.py`
- bounded Stage 4 tests covering retry routing, plateau handling, and attempt identity
- canonical execution SSOT, temp mirror, roadmap refresh, queue-state refresh

Excluded:

- broad model/provider/fallback redesign
- NpcDrift truth-source redesign already handled by prior Stage 4 work
- broad flashback taxonomy rewrite
- Stage 3 lanes
- DB schema changes
- relaxing Director sovereignty or broad safety-gate weakening

## 4. Pass 1. Inventory Summary

Primary owners:

- `stage4_outcome_runtime.py`
  - score-history tracking
  - `QR-7` plateau warning construction
- `stage4_retry_runtime.py`
  - retry-lane routing
  - `TF-PATCH-GATE` and `TF-4` policy emissions
- `stage4_interview_round.py`
  - attempt metadata propagation
  - prior-attempt history
  - candidate/hash metadata already available at round boundary

Primary operator sinks affected:

- `projects/0_1/logs/session/ui_events.jsonl`
- any DB/UI sink that consumes retry-lane events
- Stage 4 attempt lifecycle metrics and post-run audits

Primary behavioral surfaces affected:

- retry stop/escalation timing
- whether an already-rejected equivalent artifact is allowed to consume another full retry slot

## 5. Pass 2. Semantic Classification

### Class A. Retry-lane identity observability

Problem:

- retry-lane policy/advisory events are visible but not reliably joinable to a specific `attempt_key`
- operator diagnosis and efficiency analysis are therefore slower and fuzzier than they should be

Execution choice:

- propagate the current round `attempt_key` into retry-lane `policy` and `advisory` UI events
- keep field shape additive and avoid schema changes

### Class B. Advisory-only plateau handling

Problem:

- `QR-7` detects non-convergence accurately enough to be useful
- but today it only prepends feedback and logs a warning
- the loop can still spend more attempts in the same local regime

Execution choice:

- keep the first plateau/decline warning operator-visible
- add a bounded stop-or-escalate contract when plateau/non-convergence persists under the same retry family
- prefer explicit reroute or terminal stop over silent extra local retries

### Class C. Equivalent-artifact reselection waste

Problem:

- some retries are not new search; they are materially the same artifact being re-admitted
- a naive global ban would be unsafe because some final PASS rows reused a previously rejected hash

Execution choice:

- do **not** hard-ban all duplicate hashes
- instead, suppress exact duplicate artifact reuse only when the retry context is materially unchanged:
  - same `content_hash`
  - same or equivalent retry/gate family
  - no fresh fix-pack contract delta
  - no explicit structural reroute that justifies re-evaluation

### Class D. Fresh-session verification gate

Problem:

- the prior survey showed a plausible stale-session gap for `verdict_layers`
- efficiency patches should not be judged on stale in-memory runtime evidence

Execution choice:

- require a fresh-process verification tranche before or alongside the policy wave
- if current on-disk observability fields still do not land after restart, stop and reopen the observability seam first

## 6. Side-Effect Map

- file writes:
  - `modules/core/stage4_outcome_runtime.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_interview_round.py`
  - bounded tests
  - canonical SSOT + temp mirror + roadmap + queue-state

- DB / persistence:
  - no schema mutation intended
  - additive event payload/metadata changes only

- JSONL / log / audit sinks:
  - retry-lane UI events gain `attempt_key`
  - post-run audits gain clearer retry compression evidence

- console / UI / operator output:
  - `QR-7`, `TF-PATCH-GATE`, and any new stop/escalate reason remain operator-visible
  - messaging semantics may become more decisive, not more silent

- rollback / recovery / retry:
  - yes, directly affected
  - this is a retry-policy wave and must preserve safe fallback behavior

- cache / global state:
  - any duplicate-artifact suppression ledger must stay episode-scoped and bounded
  - do not introduce unbounded global retention

- bootstrap fallback / config-env mutation:
  - not applicable in this wave

## 7. Realization Architecture

### 7.1 Tranche 0 Verification Gate: Fresh-Session Observability Check

Before trusting new efficiency telemetry:

- run a fresh process restart
- rerun a bounded Stage 4 sample with known downstream override behavior
- confirm current on-disk verdict-layer fields actually land in the intended sinks

Guardrail:

- if the fields still do not land after restart, pause this wave and reopen the observability seam instead of stacking new retry policy on bad telemetry

### 7.2 Retry-Lane Attempt Identity

Additive contract:

- every Stage 4 retry-lane `policy` / `advisory` event should carry the round `attempt_key`

Targets:

- `TF-PATCH-GATE`
- `TF-4`
- `QR-7`
- any new stop-or-escalate event added in this wave

Guardrail:

- preserve current `stage`, `ep_num`, and `round_num` semantics
- do not introduce schema changes

### 7.3 QR-7 Bounded Stop-Or-Escalate Policy

Policy direction:

- the first plateau warning can remain advisory
- repeated plateau/decline inside the same retry regime should no longer be passive

Bounded trigger candidates:

- repeated `QR-7` on the same episode lane
- plateau plus `non-ready fix_pack`
- plateau plus repeated `Director non-reject -> final reject`
- plateau plus exact duplicate artifact reselection candidate

Allowed actions:

- skip another local retry and force broader reroute
- or stop the loop with an explicit operator-visible termination reason

Guardrail:

- do not silently discard candidates
- do not turn one plateau warning into an immediate global hard fail

### 7.4 Duplicate Artifact Suppression

Bounded rule:

- if the exact same `content_hash` is about to re-enter the same retry family without a meaningful contract delta, suppress that admission and log why

Allowed escape hatches:

- contract delta exists
- lane/routing changed materially
- prior decision context was not equivalent

Guardrail:

- candidate-key duplication alone is not enough; hash and context both matter
- avoid blanket bans that would block legitimate later PASS rows

## 8. Execution Tranches

1. Tranche 0: fresh-session observability verification gate
2. Tranche 1: retry-lane `attempt_key` propagation
3. Tranche 2: `QR-7` bounded stop-or-escalate policy
4. Tranche 3: duplicate artifact suppression with explicit escape hatches
5. Tranche 4: post-patch live efficiency audit and queue closure review

## 9. Acceptance Criteria

- retry-lane Stage 4 `policy` and `advisory` events carry `attempt_key`
- `QR-7` is no longer purely passive when non-convergence persists under a bounded trigger contract
- exact duplicate artifact reuse is suppressed only when retry context is materially unchanged
- the wave does not weaken Director sovereignty or broad safety gates
- no DB schema change is introduced
- a fresh-session rerun proves that the observability baseline is trustworthy before final closure claims

## 10. Verification Plan

- targeted pytest shards:
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_ep9_remediation.py`
  - `tests/test_stage4_advisory_escalation_seam.py`
- `python -m py_compile` on touched production/tests
- `ruff check` on touched production/tests
- `python scripts/check_utf8_hygiene.py` on touched docs/code/tests
- fresh Stage 4 live rerun after process restart on a bounded episode sample
- `python scripts/ops_validator.py --strict`
- `python scripts/sync_temp_queue_state.py`

## 11. Guardrails

- do not default to model-tier changes in this wave
- do not broadly relax strong-advisory gates
- do not hard-ban all duplicate hashes
- do not treat stale-session telemetry as closure evidence
- keep retry compression bounded and operator-visible

## 12. Temp Queue Notes

- this item enters the existing aggregate temp queue in the same turn
- it should sit directly after the currently in-progress CW false-miss lane
- it partially depends on the already-landed Stage 4 correctness substrates, but does not need to wait for broad provider/model work

## 13. 3-Pass Audit Record

Pass 1, structure and scope:

- the SSOT stays bounded to retry efficiency, not whole Stage 4 redesign
- included/excluded scope is explicit
- side-effect categories are named

Pass 2, evidence and consistency:

- tranches reflect the new retry-efficiency survey rather than ad hoc optimization guesses
- model-tier work is explicitly excluded because the evidence does not support it as first-order cause
- duplicate suppression is bounded with escape hatches to avoid conflicting with same-hash later PASS cases

Pass 3, execution and readability:

- acceptance criteria are concrete
- verification includes both targeted tests and fresh-session live evidence
- queue admission and roadmap dependency are explicit

Confidence: 96%

## 14. Closure Record

Fresh-session runtime proof supports these parts:

- retry-lane `policy` / `advisory` rows carry `attempt_key`
- `TF-PATCH-GATE` and `QR-7` are operator-visible with fresh-session attempt identity
- the fresh-session observability gate is satisfied

Residual runtime branches are bounded as follows:

- `[QR-7 escalation]`: runtime-not-exercised, non-contradicted
- `[TF-RH1]`: runtime-not-exercised, non-contradicted

Current interpretation:

- code landed
- targeted tests cover the residual branches and passed in the current workspace
- runtime evidence is sufficient for closure because the unobserved residual branches were not contradicted by the canary
