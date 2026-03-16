# Stage4 Menu7 Arc Transition Enter Skip OPUS Revalidation

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/stage4-menu7-arc-transition-enter-skip-opus-revalidation.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop packaging files, project artifacts, OPUS docs, and 2026-03-16 manuscript docs already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `re-audit found one remaining final-close Stage 4 call path without skip_pause; this turn patched main_a.py and added final-close regression coverage`
Source Survey Docs:
- `docs/2026-03-16/opus/stage4-menu7-arc-transition-enter-skip-3pass-audit.md`
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
Evidence Artifact: `docs/2026-03-16/stage4-menu7-arc-transition-enter-skip-opus-revalidation-evidence.txt`
Confidence: `98%`

## 1. Intent

- Re-audit the OPUS menu 7 Enter-skip claim against the current live workspace.
- Decide whether the issue was fully landed or whether a remaining menu 7 branch still needed runtime remediation.

## 2. Source Under Review

The OPUS document claims that menu 7 frontier progression prompts for Enter after each Stage 4 arc boundary because `run_post_episode_tasks()` contains a raw `input(...)` call. It recommends a `skip_pause` propagation chain from menu 7 down to the Stage 4 post processor.

That claim was treated as low-trust input, not as authority, because:

- the OPUS file is a historical investigation artifact
- the file has noisy encoding in this workspace
- OPUS previously produced scope drift in adjacent manuscript documents

## 3. Pass 1. Live Inventory

Live code check found the exact chain the OPUS memo proposed, but the first pass also exposed one remaining branch that had been missed in the earlier closure read:

- `modules/core/stage4_post_processor.py`
  - `run_post_episode_tasks(self, *, skip_pause: bool = False)`
  - the raw Enter prompt is behind `if not skip_pause`
- `modules/core/stage4_orchestrator.py`
  - `_run_interview_loop(..., skip_pause: bool = False)`
  - both the early-return and normal-completion paths call `run_post_episode_tasks(skip_pause=skip_pause)`
  - `stage_4_v2_chief_writer(..., skip_pause: bool = False)` forwards the flag into `_run_interview_loop`
- `main_a.py`
  - `_stage_4_v2_chief_writer(..., skip_pause: bool = False)` forwards the flag to the orchestrator
  - menu 7 frontier progression calls Stage 4 with `skip_pause=True`
  - menu 7 final-close progression had one remaining Stage 4 call without `skip_pause=True` when `remaining_design <= 0`
  - the final return-to-menu pause still exists separately via `wait_for_menu_return`

The earlier revalidation was therefore too broad. The issue was mostly landed, not fully landed.

## 4. Pass 2. Validity Judgment

The OPUS issue class is valid.

- Historically, this was the right problem to investigate.
- The per-arc blocking prompt does belong to the Stage 4 post-episode cleanup path.
- The OPUS proposed fix shape is also valid: `skip_pause` must propagate through the menu 7 -> Stage 4 wrapper -> orchestrator -> post processor chain.

However, the current live workspace did not fully contain that fix shape at the start of this re-audit. The frontier and one-stop arc-range paths were already fixed, but the `remaining_design <= 0` final-close branch in `_one_stop_pipeline_frontier_lag()` still called Stage 4 without `skip_pause=True`.

So the OPUS memo was valid as a historical lead and still partially actionable, even though its line-by-line trust level remained low.

Important scope split:

- the intermediate per-arc Stage 4 Enter prompt is now skipped on menu 7 and the one-stop path
- the final `[Enter] return to menu` pause remains intentionally separate and still belongs to `wait_for_menu_return`
- the older menu 7 execution SSOT covered desired Arc-count input, not this Stage 4 per-arc Enter-skip contract

## 5. Pass 3. Operational Decision

Targeted runtime remediation was required.

What was missing was narrower than the OPUS memo implied:

- one remaining menu 7 final-close Stage 4 call needed `skip_pause=True`
- dedicated regression coverage for that final-close branch
- corrected canonical documentation that distinguishes partially-landed code from fully-closed authority

This turn closes that gap by patching the final-close branch, adding focused regression tests, and promoting the corrected result into a closure-grade execution SSOT.

## 6. Confidence Basis

- live code matches the OPUS proposed fix shape end-to-end
- the user-reported discrepancy forced a fresh reachability check, which uncovered a real missed branch rather than a logging illusion
- the remaining final menu return pause is explicitly separated from the issue under review
- focused regression coverage now exists on the post processor, wrapper, menu 7 frontier path, and orchestrator forwarding seam
- focused regression coverage now also exists on the menu 7 final-close branch
- the conclusion is bounded: this is not a broad menu 7 or prompt-authority claim

Final confidence: `98%`
