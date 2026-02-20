# Codex Sweep 100 Manual-Only Plan

## 1) Goal
- Run a new 100-round sweep that is valid only when code is manually inspected.
- Reject any round that relies on `rg/grep/freg` outputs without direct code reading.
- Require precise manual evidence for every reported issue.
- Minimize false positives by respecting existing code philosophy, contracts, and intended behavior.
- Execute in uninterrupted mode (no mid-run user query unless hard blocker).

## 1A) Uninterrupted Operation Policy
- During active rounds, do not stop for clarification questions.
- Continue until checkpoint/phase boundary unless one of the following occurs:
- Required file is missing/unreadable.
- Non-recoverable runtime/permission blocker.
- Unexpected workspace mutation that invalidates sweep continuity.
- On unavoidable interruption, record:
- `Blocker`
- `Last completed round`
- `Resume condition`

## 2) Non-Negotiable Rules
- No round is valid unless target code files were opened and read directly.
- `rg/grep/freg` can be used only for navigation, never as primary evidence.
- Any finding based only on pattern search output is auto-rejected.
- Every confirmed bug must include manual evidence from function body, branch path, and exception path.
- If behavior can reasonably be intentional policy/design, classify it as `Risk`, not `Confirmed Bug`.
- Existing architecture intent, fallback design, optional paths, and version notes must be checked before bug labeling.

## 3) Hard Rejection Criteria
- Reject a round if it does not include exact file/line references from manually read code.
- Reject a round if it reports a bug without caller-callee path verification.
- Reject a round if it reports a bug without checking documented intent/comments/contract.
- Reject a round if it only cites logs, stack traces, or test outcomes without code-path evidence.
- Reject a round if it duplicates an already confirmed issue without new evidence.

## 4) Manual Evidence Standard (Required Per Round)
- `Read Files`: 1-3 files that were manually opened.
- `Evidence A`: exact function and branch condition manually verified.
- `Evidence B`: exception/fallback path manually verified.
- `Evidence C`: caller-callee contract trace (or why none exists).
- `Intent Check`: why this is bug vs intended behavior.

Minimum for `Confirmed Bug`:
- At least 2 of:
- Runtime reproduction with deterministic failure.
- Contract mismatch across caller/callee.
- Deterministic wrong result path from code logic.
- Plus mandatory `Intent Check` pass (not documented/intentional behavior).

## 5) False Positive Prevention Protocol (Intent-First)
- Step 1: Read module/class docstring and local comments first.
- Step 2: Check whether behavior is tagged optional/fallback/compatibility.
- Step 3: Check whether caller preconditions intentionally guarantee the input type/state.
- Step 4: Check whether this is CLI-only or debug-only branch by design.
- Step 5: If uncertainty remains, mark as `Risk` with explicit open question.

Do not label as bug when:
- Behavior is explicitly documented fallback policy.
- Behavior is intentionally fail-open/fail-soft for service continuity.
- Behavior is in clearly isolated non-production/manual-only flow.
- Behavior depends on invalid inputs that are contractually impossible in normal path.

## 6) Round Workflow (Manual-Only)
- Open target files directly and read relevant function blocks.
- Trace execution flow manually: entry, branch, fallback, exception.
- Verify upstream and downstream contracts.
- Record findings with evidence template.
- If no issues, explicitly write `none` with evidence of what was checked.

## 7) Severity Policy
- `P0-CRITICAL`: data corruption, infinite loop, unrecoverable crash in normal path.
- `P1-HIGH`: deterministic wrong behavior in core flow.
- `P2-MEDIUM`: crash or wrong result in realistic boundary path.
- `P3-LOW`: non-fatal policy/quality defects (including hardening violations).

## 8) 100-Round Allocation

### Phase A (Rounds 1-25): Core stage pipeline and contracts
- 1-5: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_context.py`
- 6-10: `modules/core/stage2_preflight.py`
- 11-15: `modules/core/stage2_validation_pipeline.py`, `modules/core/stage2_finalizer.py`
- 16-20: `modules/core/stage3_orchestrator.py`, `modules/core/stage4_orchestrator.py`
- 21-25: `modules/core/stage4_context_builder.py`, `modules/core/stage4_post_processor.py`, `modules/core/prompt_builder.py`

### Phase B (Rounds 26-50): Agent and state tracking consistency
- 26-30: `modules/domain/agents/chief_writer.py`, `modules/domain/agents/director.py`, `modules/domain/agents/manager.py`
- 31-35: `modules/domain/agents/state_tracker.py`, `modules/domain/agents/state_tracker_npc.py`
- 36-40: `modules/domain/agents/state_tracker_plots.py`, `modules/core/world_state.py`, `modules/core/fact_ledger.py`
- 41-45: `modules/core/constraint_db.py`, `modules/core/agent_intelligence.py`
- 46-50: `modules/domain/agents/continuity_inspector.py`, `modules/domain/agents/continuity_arc.py`

### Phase C (Rounds 51-75): Retry/quality/support systems
- 51-55: `modules/core/adaptive_retry.py`, `modules/core/tree_of_thoughts.py`
- 56-60: `modules/core/manuscript_enhancer.py`, `modules/core/diversity_sampler.py`
- 61-65: `modules/core/foreshadow_tracker.py`, `modules/core/reference_anchor.py`
- 66-70: `modules/core/relationship_tracker_npc.py`, `modules/core/self_reflection.py`
- 71-75: `modules/core/genre_guards/base_guard.py` + one guard file per round

### Phase D (Rounds 76-100): Integration, startup, IO hardening
- 76-82: `modules/domain/agents/base_agent.py`, `modules/domain/agents/state_extractor.py`, `modules/domain/agents/consensus_validator.py`
- 83-90: `main_a.py` (startup flow, initialization order, stage wiring)
- 91-95: `modules/core/db_manager.py`, `modules/core/vec_memory.py`, `modules/core/prompt_loader.py`
- 96-100: manual encoding/line-ending hardening checks across docs/config/project text assets

## 9) Output Template (Mandatory)
```markdown
### Round N

**Read Files**: `file1`, `file2`

**Manual Inspection Evidence**:
- `file:line` function/branch manually verified.
- `file:line` fallback/exception path manually verified.
- Caller-callee contract trace and intent check.

**Confirmed Bugs**:
- `[Px-LEVEL] file:line` issue summary.
- Repro input and deterministic result.
- Why this violates code intent/contract.

**Risks**:
- `file:line` possible issue needing design confirmation.
- What contract/intent detail is still uncertain.

**False Positives Excluded**:
- `file:line` why this is intentional/contractual behavior.

**Test Gaps**:
- Missing test path and exact uncovered branch.
```

## 10) Checkpoints
- Every 10 rounds: one checkpoint section.
- Track:
- Cumulative confirmed bugs by severity.
- Cumulative risks.
- Cumulative false positives excluded.
- Cumulative test gaps.
- Consecutive empty rounds.
- Manual-evidence compliance rate.

## 11) Compliance Gate
- If any round fails manual-evidence standard, mark round `INVALID` and redo.
- If a confirmed bug misses intent-check justification, downgrade to `Risk`.
- If 3 invalid rounds occur in a phase, stop phase and run quality audit before continuing.

## 12) Tooling Guard (Must Run)
- Validator script: `scripts/validate_manual_sweep.py`
- Command:
```bash
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --allow-empty
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2
```
- Run timing:
- Before writing first round.
- Every 10 rounds.
- Before phase close.
- Before final report.
- Policy:
- Any non-zero result means stop-and-fix.
- Do not append new rounds until validation passes.
- Validation must pass in first pass (target process quality), not after bulk cleanup.

### FP Interim Settlement Logic
- Checkpoint interval: `--checkpoint-interval` (default: 10 rounds)
- Metrics: cumulative bugs/risks/fp/test-gaps, FP ratio, FP-only streak
- Ratio formula: `fp / (bugs + risks + fp)` (cumulative)
- Gate examples:
- Warn/report only: default run
- Hard gate: `--max-fp-ratio 0.35 --max-fp-streak 2`

## 13) Compaction Recovery Protocol
- If context compaction occurs:
- Re-open this plan and root `AGENTS.md`.
- Re-state manual-only constraints in current task notes.
- Run validator against current findings file.
- Resume from the last completed round only after validator passes.

## 14) Deliverables
- Plan file: `docs/codex_sweep100_manual_plan.md`
- Findings file (new run): `docs/codex_findings_sweep100_manual.md`
