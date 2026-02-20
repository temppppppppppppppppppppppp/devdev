# Manual Sweep Guard (Always-On)

This repository enforces manual code-inspection sweeps. Fast search tools are allowed only for navigation.

## Core Principle
- Findings are valid only when code was directly read in target files.
- `rg/grep/freg` results are never primary evidence.

## Uninterrupted Execution Mode
- Objective: finish manual sweep without mid-mission interruption.
- Do not pause to ask user questions during active sweep rounds.
- Continue autonomously until planned checkpoint/phase boundary.
- Allowed interruption reasons (only):
- Missing/blocked files required for the current round.
- Permission/runtime hard blocker that cannot be resolved locally.
- Unexpected workspace mutation that invalidates evidence continuity.
- If interruption is unavoidable, emit one concise blocker report with:
- Exact blocker.
- Last completed round.
- Immediate next action once unblocked.

## Round Validity Rules
- A round is `INVALID` unless it includes:
- Target files that were manually opened.
- At least 2 manual evidence bullets tied to real code paths.
- Exact file/line evidence from manually read code.
- Bug-vs-intent justification.

## Auto-Reject Conditions
- Search-output-only findings.
- Missing function/branch/exception path evidence.
- Missing caller-callee contract trace for confirmed bugs.
- Treating intentional fallback/compat behavior as bugs without intent check.
- Re-reporting old issues without new manual evidence.

## Intent-First False-Positive Control
- Before bug labeling, check:
- Docstring/comments nearby.
- Optional/fallback/compat markers.
- Caller preconditions and interface contract.
- Runtime mode (CLI-only/debug-only/non-prod).
- If uncertain, classify as `Risk` with open question.

## Compaction Recovery Guard
- After context compaction or restart:
- Re-read this file first.
- Re-state these rules in the current plan before continuing.
- Run manual sweep validator on the findings file before adding new rounds.
- Resume from the last completed round automatically (no re-scoping questions).

## Required Validator
- Before round 1: `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --allow-empty`
- After round 1 starts: `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100`
- Recommended FP gate: `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- If validator fails, do not continue. Fix invalid rounds first.

## First-Pass Quality Target
- Goal: pass validation on first implementation pass.
- If 1 invalid round appears, fix immediately.
- If 3 invalid rounds appear in a phase, pause and audit process quality before continuing.
