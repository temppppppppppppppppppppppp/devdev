# Console Log Max-Display / Max-Retention Parity Execution SSOT

Date: 2026-03-23
Status: execution-ready
Canonical Path: `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md`
Temp Mirror Path: `docs/temp/console-log-max-display-post-audit-execution-ssot.md`
Commit State:
- Baseline Commit: `a3b9a286`
- Baseline Dirty Summary: `dirty: active 2026-03-23 docs, runtime/db edits, and one pending DB logging execution item`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-23/opus/console-log-max-display-audit.md`
- `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
Evidence Artifacts:
- `live code inspection regrade by Codex; no separate evidence manifest`
Side-Effect Coverage: covered

## 1. Intent
- Convert the console-log survey into a bounded execution item with one explicit policy: operator-facing decision logs should not be silently shortened, count-capped, or reduced to a summary when the full reasoning is already available at runtime.
- Keep console output aligned with the current max-retention DB direction so the operator screen and durable evidence no longer diverge by default.
- Prefer multi-line full display over short snippets for verdict, rejection, firewall, advisory, and fix-direction surfaces.

## 2. Baseline Facts
- Director thinking is already displayed without truncation in the covered Stage 2, Stage 3, and Stage 4 paths. That is a protected invariant, not a target for change.
- The survey's strongest live finding is confirmed:
  - Stage 4 advisory detail is generated, but the detailed advisory payloads stay on `logging.info(...)` paths rather than the operator console sink, so the operator usually sees only a count summary.
- Post-Q3/Q4/Q6 realization update:
  - `director_ensemble.py` already exposes Stage 4 score provenance and adaptive-branch provenance
  - Stage 4 `selection_reason`, `verdict_reason`, `open_review`, and issue lines in `director_ensemble.py` are already de-truncated
  - treat those surfaces as realized baseline, not pending scope for this item
- The live truncation problem remains real across operator-visible fields:
  - Stage 3 `reject_reason`, `comparison_notes`, contradictions, feedback, and error-path messages
  - Stage 4 compact attempt snapshot fields, advisory detail caps, and validator error-path messages
  - Stage 4 outcome/runtime summary fields
  - Stage 2 `reject_reason`, relationship/growth rationales, and patch/fix directions
  - Director auditor pass/reject reasons still use compact log snippets
- The DB retention wave now stores or is moving toward storing fuller rationale than the console shows. That creates operator-vs-durable-evidence drift, which this item is intended to reduce.
- `logging.info(...)` is not a reliable operator surface in this workspace because the Rich UI path is the authoritative operator channel.

## 3. Operating Policy
- For operator-facing decision logs, default policy is `show the full text`.
- Do not use Python slicing such as `[:80]`, `[:100]`, `[:150]`, or `[:200]` on decision-bearing operator lines unless the field is explicitly bounded metadata.
- Do not replace detailed decision output with a count-only summary if the detailed payload already exists at runtime.
- If a list of issues, contradictions, or warnings exists, show the full list or explicitly log that additional items continue below; do not silently cap the visible list at `[:3]` or `[:5]`.
- Preserve file/log sinks and DB sinks in addition to the operator display. This item expands operator visibility; it does not replace durable storage.

## 4. Scope
Included:
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_auditor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- targeted tests for Stage 2/3/4 operator-visible console paths

Excluded:
- verdict policy changes
- retry policy changes
- score math changes
- candidate swap semantics
- prompt content changes
- unrelated debug-noise expansion outside decision-bearing operator surfaces
- redoing already-landed `director_ensemble.py` Stage 4 max-display / provenance lines

## 5. Pass 1. Inventory Summary
- Current operator-surface losses split into the remaining active classes.

Class A. Truncation against already-available decision text:
- Stage 4 compact snapshot / outcome summary fields shortened before display
- Stage 3 rationale and rejection-history fields shortened before display
- Stage 2 reject and fix-direction fields shortened before display
- Stage 3/4 error-path lines shortened before display
- Director auditor pass/reject reasons shortened before display

Class B. Count-only summaries where full detail exists:
- advisory warnings shown as counts without operator-visible detail
- contradictions or issues capped at a small visible subset where the full list is already available

Class C. DB vs operator parity drift:
- DB stores or is moving to store fuller rationales than the operator sees on the console
- score/adaptive provenance in `director_ensemble.py` is no longer an active gap; keep it intact as realized baseline

## 6. Pass 2. Semantic Classification
- Class A. Immediate max-display parity flips
  - remove Python slicing from operator-visible rationale and error lines
- Class B. Detail-surface expansion
  - route full advisory payloads and uncapped contradiction/issue lists to the operator console sink
- Class C. Parity verification
  - confirm the console and DB now expose the same high-value rationale fields without silent shortening

## 7. Side-Effect Map
- console / UI / operator output:
  - primary scope
- file / log sinks:
  - must remain intact
  - logging-only detail should be supplemented, not removed
- DB / persistence:
  - not primary write scope for this item, but console output should align with the fuller retained fields
- rollback / recovery / retry:
  - must remain behaviorally unchanged
- cache / global state:
  - not primary scope
- bootstrap / config / env mutation:
  - not expected

## 8. Realization Architecture
- Use a three-layer observability model.

Layer 1. Operator-console truth
- decision-bearing lines go through the operator-visible sink
- full rationale, uncapped issue lists, and branch provenance belong here

Layer 2. Log-file continuity
- existing `logging.info(...)` and `logging.warning(...)` paths stay
- where only the log sink exists today, mirror the detail to the operator sink rather than moving it away from logging

Layer 3. DB parity
- the console should display the same reasoning families that DB retention now preserves
- DB remains the durable source; the console becomes a less lossy live surface

Design rule:
- console answers `what is happening right now`
- DB answers `what happened and why after the fact`
- the two should not disagree by truncation policy alone

## 9. Execution Tranches
1. Operator truncation removal tranche
   - remove operator-side slicing for decision-bearing text in:
     - `director_ensemble.py`
     - `director_auditor.py`
     - `stage2_finalizer.py`
     - `stage3_orchestrator.py`
     - `stage4_interview_round.py`
     - `stage4_outcome_runtime.py`
   - remove small visible caps for issue/contradiction lists where the list is already in memory
2. Advisory full-surface tranche
   - Stage 4 advisory families must mirror detailed payloads to the operator sink
   - Python validation advisory details should surface beyond a count-only line when details are available
3. Error-path max-display tranche
   - Stage 3/4 operator-facing error lines should carry the full message unless the field is explicitly bounded metadata
4. Verification / live-lane tranche
   - one Stage 3 lane and one Stage 4 lane after implementation
   - verify long rationale, advisory detail, and error-path detail appear on the console without truncation
   - verify already-landed score/adaptive provenance in `director_ensemble.py` remains intact

## 10. Acceptance Criteria
- operator-facing decision lines no longer use silent Python slicing unless the field is documented as bounded metadata
- Stage 4 advisory detail is visible on the operator console, not only in logging sinks
- visible issue/contradiction lists are no longer silently reduced to a tiny subset when the full list is already available
- DB-retained rationale families no longer have a materially shorter console counterpart by default
- already-landed `director_ensemble.py` score/adaptive provenance remains intact
- no change to verdict logic, retry logic, thresholds, or routing

## 11. Verification Plan
- `python -m py_compile modules/domain/agents/director_ensemble.py modules/domain/agents/director_auditor.py modules/core/stage4_interview_round.py modules/core/stage4_outcome_runtime.py modules/core/stage2_finalizer.py modules/core/stage3_orchestrator.py`
- targeted low-memory pytest shards covering:
  - Stage 4 interview round operator surfaces
  - Stage 4 outcome runtime operator surfaces
  - director ensemble operator output
  - director auditor operator output
  - Stage 2 finalizer operator output
  - Stage 3 operator output where touched
- fresh live path after implementation:
  - one Stage 3 lane with long reject/pass rationale
  - one Stage 4 lane with advisory warnings, firewall path, validator error path, and outcome summary path
  - capture operator transcript and compare against DB-retained fields
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md docs/temp/console-log-max-display-post-audit-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 12. Guardrails
- Do not reintroduce truncation as a convenience fix for noisy output.
- Do not treat operator-visible decision detail as optional if the runtime already has the detail.
- Do not replace existing log sinks; supplement them with operator-visible lines where needed.
- Do not change score math, verdict rules, retry behavior, or adaptive policy while surfacing provenance.
- If a field remains intentionally bounded, document why it is metadata rather than decision evidence.

## 13. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove the temp mirror after realization and Codex closure
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 14. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 15. 3-Pass Audit Record
- Pass 1: reclassified the survey from raw `critical/high` labels into live-code-accurate operator-gap classes
- Pass 2: removed already-realized provenance tranches from active scope and kept only residual truncation/detail gaps
- Pass 3: rechecked queue semantics against the already-active DB logging SSOT and converted this item into a roadmap-governed second queue entry with residual-only scope

## 16. Confidence
- Estimated confidence: 96%
- Residual uncertainty:
  - exact operator formatting for uncapped advisory payloads should be chosen during implementation Pass 1
  - one fresh Stage 3/4 live lane is still required before closure
