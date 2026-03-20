# Stage4 Retry Pathology Observability and Escalation Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-retry-pathology-observability-and-escalation-execution-ssot.md`
Temp Mirror Path: `removed at closure`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: fresh-run project 0_260320, docs/mmmm collector bundle, active smoke-fixture temp mirror, ongoing dated-doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
- `docs/2026-03-20/rol-live-run-0_260320-evidence-manifest.md`
- `docs/2026-03-20/rol-low-trust-mmmm-intake-triage-3pass-audit.md`
- `docs/2026-03-20/rol-post-run-action-bearing-split-3pass-audit.md`
Evidence Artifacts:
- `projects/0_260320/print.txt`
- `projects/0_260320/logs/session/decisions.jsonl`
- `projects/0_260320/logs/session/ui_events.jsonl`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
Side-Effect Coverage: covered

## 1. Intent

Make repeated Stage4 retry-pathology loops explicit before changing the repair policy.

The fresh run exposed a bounded pattern:
- Director provisional PASS
- post-select downgrade to `post_select_conflict`
- `Fix Pack is missing` widening to `partial`
- later `continuity_firewall`
- then a temporary PASS followed by CoVe fail-closed and another round

This execution item is observability-first. It should improve diagnosis and escalation hygiene before any larger semantic rewrite.

## 2. Baseline Facts

- `modules/core/stage4_interview_round.py` downgrades provisional PASS to `REJECT` on post-select continuity/history conflicts and stores `reject_bucket=post_select_conflict`.
- the same Stage4 retry lane widens `fix_scope=inplace` to `partial` when explicit `fix_pack` is missing.
- `projects/0_260320/logs/session/decisions.jsonl` shows repeated `director PASS -> post_select_conflict downgrade` for ep2.
- `projects/0_260320/logs/session/ui_events.jsonl` and `print.txt` show:
  - repeated `Fix Pack is missing`
  - later `Contradiction Firewall`
  - provisional PASS
  - CoVe runtime failure
  - another round start
- current logs are sufficient to see that something went wrong, but not yet sufficient to fingerprint and group one repeated pathology cleanly.

## 3. Scope

Included:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- bounded Stage4 retry/audit/logging surfaces
- focused tests for retry-pathology evidence capture

Excluded:
- changing Director sovereignty
- disabling post-select downgrade
- disabling CoVe fail-closed semantics
- large Stage3/Stage4 rewrite-lane redesign

## 4. Realization Architecture

### Tranche 1. Round-level pathology fingerprinting
- persist a bounded fingerprint when repeated Stage4 failure motifs recur
- minimum payload should include:
  - `reject_bucket`
  - continuity/history/firewall tag
  - fix-pack readiness
  - repair scope
  - whether the candidate was provisional PASS before downgrade
  - whether CoVe caused the subsequent fail-closed

Preferred sink:
- `audit_event(...)`
- and/or bounded Stage4 control-row logging

### Tranche 2. Repeated-pattern surfacing
- when the same Stage4 pathology repeats across rounds, surface one compact repeated-pattern signal
- goal:
  - make later merge audits and operators see “same conflict family repeated”
  - avoid reading six separate raw logs to infer that pattern

### Tranche 3. Escalation hygiene
- after observability is in place, tighten escalation guidance without rewriting policy:
  - make plateau / repeated-post-select pattern explicit
  - make “blueprint/frontier correction preferred over local prose repair” visible earlier
- defer any stronger semantics change until the new evidence is observed in another run

## 5. CoVe Boundary

- CoVe fail-closed after provisional PASS is kept inside this execution item's evidence surface only.
- It is not a standalone execution item yet.
- Reason:
  - fail-closed behavior itself is currently intentional and test-pinned
  - the fresh run gives one bounded runtime-failure sample, not enough for a standalone behavior rewrite

## 6. Side-Effect Map

- file writes / artifacts:
  - none required beyond bounded JSONL/log/audit additions
- DB / schema / transaction boundaries:
  - avoid schema expansion unless a truly authoritative sink is needed
- JSONL / log / audit sinks:
  - yes; this is the primary realization surface
- console / UI / operator output:
  - optional compact pathology line allowed
- rollback / recovery / retry:
  - should remain semantically unchanged in tranche 1
- cache / global state:
  - none targeted

## 7. Validation Plan

Minimum:
- focused tests for:
  - repeated `post_select_conflict` evidence capture
  - `fix_pack` widening visibility
  - CoVe post-pass fail-closed breadcrumb capture
- UTF-8 hygiene
- `git diff --check`

Preferred:
- a synthetic or bounded rerun reproducing the same pattern
- confirmation that one compact pathology signal now survives into post-run merge analysis

## 8. Pass/Fail Criteria

Pass:
- repeated Stage4 loops are observable as one coherent pathology family
- the run no longer requires manual cross-reading of `print.txt`, `ui_events`, and `decisions` to prove the repeated pattern

Fail:
- logs still show only disconnected per-round messages
- post-run merge still cannot tell whether the same conflict family repeated

## 9. Queue Priority

- priority:
  - `3`
- rationale:
  - broader than the blueprint observability gap
  - should follow the narrower artifact/snapshot fix

## 10. Confidence

- pass 1:
  - fresh-run evidence and code path aligned
- pass 2:
  - scope bounded to observability-first with escalation hygiene
- pass 3:
  - CoVe boundary and queue role checked
- estimated confidence:
  - `0.95`

## 11. Closure Note

Closed after Stage4 retry-pathology observability landed in the live retry loop without changing repair semantics.

Implemented:
- bounded retry-pathology fingerprinting and repeat grouping in `modules/core/stage4_orchestrator.py`
- post-select downgrade provenance in `modules/core/stage4_interview_round.py`
- CoVe fail-closed breadcrumbs for both LLM verify and quick-verify runtime failures
- soft-fail sink behavior so observability cannot break retry execution

Verification Evidence:
- `python -m pytest tests/test_stage4_orchestrator.py -k "retry_pathology or cove_verify_raises or log_escalation_event" -q`
- `python -m pytest tests/test_stage4_interview_round.py -k "post_select_conflict_preserves_patch_seed_metadata" -q`
- `python -m pytest tests/test_v75b_escalation.py -q`

Residual Notes:
- this item does not change escalation policy, CoVe fail-closed semantics, or retry stop conditions
- any future Stage4 retry redesign should use the new pathology signal family as input evidence, not as policy authority by itself
