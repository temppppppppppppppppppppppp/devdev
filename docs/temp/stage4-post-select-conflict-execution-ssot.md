# Stage4 POST_SELECT_CONFLICT Carryover Execution SSOT

Date: 2026-04-27
Track: system
Status: execution-ready (parked future wave)
Canonical Path: `docs/2026-04-27/stage4-post-select-conflict-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-post-select-conflict-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: same-as-baseline
- Resume Drift Summary: no tracked source edits made while creating this SSOT
GitHub Issue:
- #58 `[Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs`
Source Survey Docs:
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-01-current-run-forensics.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-02-postselect-conflict-route.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-03-stage3-stage4-handoff.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-04-continuity-authority-carriers.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-05-memory-cache-side-effects.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-06-retry-hydration-replay.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-07-context-cache-lineage.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-08-regression-gap-design.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-09-artifact-truth-samples.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-10-synthesis-map.md`
Evidence Artifacts:
- Current-run DB/artifact summaries from T01 and T09
- Source-route and authority-carrier audits from T02-T07
- Regression design from T08
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage4-post-select-conflict
  github_issue: 58
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 5
  depends_on: []
  tranches:
    - id: postselect-specificity-and-evidence-lock
      title: Post-select specificity and evidence lock
    - id: stage3-stage4-lineage-gates
      title: Stage3/Stage4 lineage gates
    - id: continuity-authority-runtime-wiring
      title: Continuity authority runtime wiring
    - id: retry-hydration-and-patch-containment
      title: Retry hydration and patch containment
    - id: cache-lineage-and-memory-suppression
      title: Cache lineage and memory suppression
    - id: artifact-backed-regression-suite
      title: Artifact-backed regression suite
  verification_commands:
    - python -m pytest tests/test_stage4_interview_round.py -k "hydrate or retry or previous_attempt" -q
    - python -m pytest tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q
    - python -m pytest tests/test_continuity_canary.py tests/test_continuity_pin_guard.py -q
    - python scripts/check_utf8_hygiene.py <touched docs/code/tests>
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Reduce the concrete #58 failure loop where Stage4 repeatedly reaches `POST_SELECT_CONFLICT` because stale or duplicated continuity/history information survives into later attempts.

The goal is not to weaken the post-select firewall. The goal is to make the writer, retry, cache, memory, and continuity authority surfaces converge before Stage4 has to reject the same drift family repeatedly.

## 2. Baseline Facts

- T01 and T09 confirm the handoff's ep4-ep9 Stage4 ladder from DB evidence: ep4-ep8 recover after POST_SELECT rejects, while ep9 stops after two `POST_SELECT_CONFLICT` rejects and no PASS.
- T02 confirms `POST_SELECT_CONFLICT` is a runtime continuity-firewall downgrade after Director-side post-select checks. It should be preserved as fail-closed transport.
- T03 finds Stage3-to-Stage4 lineage risks: persisted blueprint skip/reuse, stale `current_project.arcs`, and Stage4 entering with `_stage3_meta.revision_required` or binding prevalidation categories.
- T04 finds authority-carrier gaps: continuity canaries and `ContinuityInspector.inspect_manuscript` are not wired into live Stage4, and ACP/IFC truth does not symmetrically reach the verdict-side post-select prompt.
- T05 finds session/vector memory can amplify stale evidence but should not be treated as the primary authority carrier.
- T06 finds retry/hydration risks: rejected manuscript bodies can be reloaded, patch mode can replay failed bodies, `scope_authority.fix_scope` can shadow runtime widening, and cross-session fallback remains a risk if session id is unavailable.
- T07 finds context-cache lineage gaps, especially Director reuse paths that can be count-only or bypass richer lineage gates.
- T08 maps regression gaps for institution naming drift, duplicated continuation beats, date drift, and prior-failure replay.
- T09 confirms artifact truth is UTF-8 clean and shows artifact-level bug shapes: institution token drift, capital value drift, completed-event replay, and Stage3 blueprint pre-contamination.
- T10 was written before T01-T09 existed, so it is retained only as a candidate-family map, not as final synthesis authority.

## 3. Scope

Included:
- Stage3-to-Stage4 lineage and stale blueprint/context gates.
- Stage4 post-select conflict specificity and operator evidence.
- Continuity authority carriers consumed by Stage4 candidate and verdict paths.
- Retry/hydration/patch containment for rejected manuscripts.
- Context-cache and helper-memory suppression where stale rejected content could re-enter.
- Artifact-backed regression tests for the four #58 bug shapes.

Excluded:
- Relaxing Director or post-select quality gates.
- Claiming #57 terminal 5-arc proof readiness.
- Broad memory/cache redesign beyond #58 carryover suppression.
- Narrative judgment by Python. Python can tripwire, route, and preserve evidence; Director authority remains final.

## 4. Pass 1. Inventory Summary

| Surface | Evidence | Risk |
| --- | --- | --- |
| Stage4 ep4-ep9 attempt rows | T01/T09 | repeated `POST_SELECT_CONFLICT`, ep9 terminal stop |
| Post-select conflict route | T02 | bucket collapses useful subfamilies if not surfaced |
| Stage3 persisted blueprint / Stage4 context | T03/T09 | stale institution/capital can pre-contaminate Stage4 |
| Continuity authority carriers | T04 | ACP/IFC/canary/pin truth not fully wired into verdict path |
| Memory/cache helper surfaces | T05/T07 | stale helper context can amplify, not decide, drift |
| Retry hydration / patch lanes | T06 | rejected body and stale fix scope can replay into next attempt |
| Regression gaps | T08 | named bug shapes lack focused integrated coverage |

## 5. Pass 2. Semantic Classification

Class A - preserve fail-closed detection:
- Keep `POST_SELECT_CONFLICT` as a hard post-select route.
- Surface more specific subfamilies for operator visibility and retry guidance.

Class B - source-of-truth convergence:
- Ensure Stage3 blueprint lineage, accepted fact state, ACP/IFC truth, and Stage4 context agree before candidate generation.
- Gate stale or revision-required Stage3 outputs before Stage4 writer calls.

Class C - retry convergence:
- Prevent rejected content from being replayed as candidate source material.
- Ensure patch scope widening cannot be shadowed by stale `scope_authority` fields.

Class D - helper containment:
- Treat context cache, session memory, and vector memory as helper evidence.
- Add lineage gates and suppression where helper content can reintroduce stale names, dates, numbers, or completed beats.

## 6. Side-Effect Map

- file writes / artifacts: Stage3/Stage4 context packets, rejected/selected candidate artifacts, final manuscripts, blueprint artifacts, regression fixtures.
- DB / schema / transaction boundaries: `stage_attempts`, `director_selections`, `manuscripts`, `blueprints`, `episode_meta`, `context_cache_attempts`, and possible memory metadata tables.
- JSONL / log / audit sinks: `runtime_audit.jsonl`, `episode_production.jsonl`, session logs, UI events, pass-rate monitor, and cache-attempt logs must keep subfamily evidence visible.
- console / UI / operator output: show conflict subfamily and retry reason without collapsing everything into an opaque bucket.
- rollback / recovery / retry: failed/rejected attempt content must not become a future authority carrier; loop exhaustion must not adopt failed best manuscript text.
- cache / global state: cache reuse must prove lineage, not only count/episode match.
- bootstrap fallback / config-env mutation: not applicable to #58 except where run/session ids are missing; missing session id must fail safe for hydration.

## 7. Realization Architecture

Implement in narrow, test-first tranches:

1. Lock evidence and subfamily labels so future fixes can prove which drift class changed.
2. Gate stale Stage3 outputs before Stage4 candidate generation.
3. Wire continuity authority into both candidate context and verdict-side post-select prompts.
4. Contain retry/hydration so failed bodies are feedback, not source material.
5. Tighten cache/memory lineage for Stage4 retry and post-select flows.
6. Add artifact-backed regressions using T09 examples as small redacted fixtures.

## 8. Execution Tranches

1. Post-select specificity and evidence lock
   - Preserve `POST_SELECT_CONFLICT` fail-closed behavior.
   - Expose continuity/history/both/check-error subfamilies in operator and retry evidence.
2. Stage3/Stage4 lineage gates
   - Stamp or verify source lineage on blueprint payloads.
   - Gate Stage3 exists-skip and Stage4 input preparation on lineage equality.
   - Refuse Stage4 entry when `_stage3_meta.revision_required` or binding prevalidation categories require upstream repair.
3. Continuity authority runtime wiring
   - Ensure ACP/IFC/non-regression anchors reach post-select verdict prompts as well as writer prompts.
   - Decide whether to wire continuity canaries and/or retire unwired inspector paths.
   - Add Stage4 candidate-level pin guard or equivalent for institution/date/asset/completed-beat truth.
4. Retry hydration and patch containment
   - Prevent rejected manuscripts from rehydrating as candidate source bodies.
   - Fix stale `scope_authority.fix_scope` shadowing runtime widening.
   - Fail safe when session id is missing for previous-attempt hydration.
   - Prevent loop exhaustion from adopting failed `best_manuscript`.
5. Cache lineage and memory suppression
   - Lift Director cache reuse predicates to match richer lineage gates.
   - Ensure rejected/partially settled content cannot be written or retrieved as future authority.
6. Artifact-backed regression suite
   - Add focused tests for institution token drift, duplicated completed-event replay, date drift, capital/fact alignment, and prior-failure replay.

## 9. Acceptance Criteria

- Repeated `POST_SELECT_CONFLICT` retries surface specific subfamilies rather than only the opaque bucket.
- Stage4 cannot consume stale Stage3 blueprint/context lineage without an explicit audited fallback.
- Continuity truth used by the writer and the post-select verdict path is symmetric or the asymmetry is explicitly documented and tested.
- Rejected manuscripts are not replayed as source material for the next attempt.
- Cache and memory helpers cannot reintroduce stale rejected content without lineage proof.
- Focused regressions cover institution naming drift, duplicated continuation/completed-event beats, date drift, capital value drift, and prior-failure replay.
- No claim of clean 5-arc readiness is made until targeted proof and fresh live/validation evidence exist.

## 10. Verification Plan

- `python -m pytest tests/test_stage4_interview_round.py -k "hydrate or retry or previous_attempt" -q`
- `python -m pytest tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `python -m pytest tests/test_continuity_canary.py tests/test_continuity_pin_guard.py -q`
- Add and run new focused tests from T08/T09 once implemented.
- `python -m py_compile <touched Stage3/Stage4/cache/memory modules>`
- `python scripts/check_utf8_hygiene.py <touched docs/code/tests>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`
- Fresh live or targeted multi-arc proof before closing #58 or using it to unblock #57.

## 11. Guardrails

- Do not relax post-select Director conflict checks to make the run pass.
- Do not promote memory/cache helper evidence into final narrative authority.
- Do not let Python become the final narrative quality judge.
- Do not claim clean 5-arc readiness from green unit tests alone.
- Do not overwrite or delete generated run evidence while it is still an active proof source.

## 12. Temp Queue Notes

- temp status: pending
- queue role: parked future wave
- cleanup condition: remove `docs/temp/stage4-post-select-conflict-execution-ssot.md` after realization, verification, canonical closure update, and any #58 GitHub status update.
- roadmap dependency: no formal dependency edge is declared to avoid silently reordering the existing Frontier Lag queue item; however, this SSOT should be considered before any fresh claim of terminal clean 5-arc proof.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state: `python scripts/sync_temp_queue_state.py`
- execution-start rule: re-run document 3-pass audit and confirm at least 95% confidence against live workspace before code edits.

## 14. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. This is an execution SSOT for #58 only.
- PASS. Included/excluded scope preserves Director authority and forbids post-select relaxation.

Pass 2 - evidence and consistency:
- PASS. All ten terminal reports exist and decode as UTF-8.
- PASS. T10 is explicitly treated as stale initial synthesis, not final authority.
- PASS. T01/T09 DB/artifact evidence, T02 route audit, T03/T04 authority audits, T05/T07 helper audits, T06 retry audit, and T08 test design are all represented.

Pass 3 - execution readiness:
- PASS. Tranches are ordered from evidence specificity through lineage/authority/retry/cache containment into tests.
- PASS. Side effects and proof boundaries are explicit.

Estimated operational confidence: 96%.

