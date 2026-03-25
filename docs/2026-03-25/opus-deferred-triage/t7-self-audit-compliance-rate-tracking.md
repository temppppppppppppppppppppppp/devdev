# T7. Self-Audit Compliance Rate Tracking — Triage Report

Date: 2026-03-25
Status: final
Document Type: lane triage report
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t7-self-audit-compliance-rate-tracking.md`
Lane: T7 of deferred-followups-yesno-triage-7terminal-master-order
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 artifacts, Wave 1 + self-audit wave closed edits, 2026-03-25 docs`

## 1. Lane Question

Is self-audit compliance rate tracking worth opening before another canary, or is it observability-only and later/no?

## 2. Findings

### Finding 1. Zero compliance tracking exists today across all three stages

Every self-audit system in the pipeline is fire-and-forget: the prompt injects a checklist or instruction, but the LLM response is parsed exclusively for JSON content. No extraction, logging, or persistence of whether the LLM actually followed the self-check.

Evidence:

- **Stage 2 — ConstraintCompiler SELF-CHECK** (`modules/domain/agents/constraint_compiler.py:378-389`): renders a 5-item checklist into the prompt. Response parsed via `_extract_json_robust()` for arc JSON only. Checkbox compliance: not captured.
- **Stage 2 — NegativeExampleInjector self-check** (`modules/domain/agents/negative_example_injector.py:353-370`): 8-item `□` checklist injected. Response parsed for JSON only. Compliance: not captured.
- **Stage 2 — ConstitutionalChecker arc constitution** (`modules/core/constitutional_checker.py:220-275`): question-per-article format injected via `stage2_preflight_runtime.py:272-277`. Compliance: not captured.
- **Stage 3 — 자가 검증 체크리스트** (`config/prompts/ensemble.yaml`): 7-item `□` checklist added 2026-03-25. Response parsed via `_extract_json_robust()` (`blueprint_ensemble.py:735`). Compliance: not captured.
- **Stage 4 — Self-Critique loop** (`chief_writer_quality.py:102-247`): multi-round LLM critique runs internally. Round count, skip decisions, and compliance outcomes: not logged to any metrics sink.

### Finding 2. Metrics infrastructure exists but has zero compliance fields

- `modules/core/pass_rate_monitor.py`: `AttemptRecord` has 24 slots tracking stage/episode/attempt/success/reject_reason/score_breakdown. No `self_audit_compliance`, `self_check_passed`, or `self_critique_rounds` fields exist.
- `projects/*/logs/runtime_audit.jsonl`: logs `blueprint_success`, `stage4_retry_pathology_signal`, and similar events. No self-audit compliance fields in any event type.
- `projects/*/logs/quality_metrics.jsonl`: episode-level quality scores. No compliance rate data.
- `projects/*/logs/metrics/`: agent-level call statistics (total_calls, duration, cost). No compliance fields.
- DB (`project_data.db`): stage_attempts and director_selections tables. No compliance columns.

### Finding 3. The Stage 3 self-audit checklist was added today — no data exists to track

The `자가 검증 체크리스트` insertion was closed as part of the self-audit wave on 2026-03-25. Zero live runs have been executed with this checklist active. There is no historical compliance data and no observable signal to analyze.

The Stage 2 self-check systems have been active for longer, but their compliance was never tracked either, so there is no retroactive baseline.

### Finding 4. Compliance tracking is observability-only with no current actionable hook

Building compliance rate tracking would answer "does the LLM follow the checklist?" but would not change pipeline behavior. The pipeline today:

1. Injects self-check prompt text
2. Parses JSON output
3. Runs Python prevalidation
4. Sends to Director

Adding compliance extraction would insert a step between (2) and (3) — parse the LLM's free-text or JSON for evidence of checklist completion. This is:

- **Technically feasible**: extend `AttemptRecord`, add a post-extraction regex/heuristic, log to JSONL
- **Not behaviorally impactful**: the pipeline would still do the same thing regardless of compliance result
- **Only actionable after accumulating data**: e.g., "if compliance < 70%, reinforce prompt" — but that requires multiple runs of data first

### Finding 5. Blast radius assessment

If compliance tracking were opened now:

- **Code surface**: `pass_rate_monitor.py` (add fields), blueprint_ensemble.py / four_phase_arc_generator.py / four_phase_arc_runtime.py / chief_writer_quality.py (add extraction), runtime_audit sink (new event type)
- **Files touched**: 5-6 production files across Stages 2/3/4
- **Risk**: moderate — response parsing changes touch the hot path of all three generation stages
- **Attribution**: compliance tracking changes mixed with the just-closed self-audit wave would make canary signal harder to interpret, not easier

## 3. Triage Assessment

### Arguments for "yes now"

- None strong. The infrastructure could be built. But there is no data to consume, no baseline to compare against, and no behavioral change that would result.

### Arguments for "later after canary"

- The Stage 3 self-audit checklist was added today. A fresh canary is needed first to see whether blueprints improve. Only after observing the canary can we meaningfully ask "did the LLM actually follow the checklist?"
- Compliance tracking across all three stages touches 5-6 production files in hot paths. Building this before seeing any live signal is speculative engineering.
- The pre-director self-audit survey report (`docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`) rated Stage 2 self-check compliance logging as `LOW` ROI — observability, not quality.
- The bp-clarity-density merge audit (`docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`) explicitly deferred compliance tracking behind primary Stage 3 quality-up fixes.

### Arguments for "no"

- Not quite "no" — compliance tracking is a reasonable future observability step once there is live data to track. But it is strictly post-canary work.

## 4. Confidence

Estimated confidence: 97%

Why this clears the 95% gate:

- All claims are grounded in file:line evidence from live code inspection
- The zero-data-exists finding is structural (the checklist was added today)
- The observability-only classification matches both source survey reports
- No conflicting evidence was found suggesting compliance tracking would be immediately actionable

## 5. Verdict

Lane verdict: later after canary
Best bounded next wave from this lane: compliance-rate extraction after post-self-audit canary run (if canary shows quality stagnation despite checklist presence)
Should Codex open an execution SSOT from this lane now: no
