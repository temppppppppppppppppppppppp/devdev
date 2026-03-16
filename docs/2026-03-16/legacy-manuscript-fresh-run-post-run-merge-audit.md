# Legacy Manuscript Fresh Run Post-Run Merge Audit

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-audit.md`
Source Docs:
- `docs/2026-03-16/legacy-real-manuscript-contradiction-survey.md`
- `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey.md`
Evidence Artifacts:
- `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-evidence.txt`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop package/icon/version files, project 0/000 artifacts and db, OPUS manuscript docs, and untracked 2026-03-16 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `98%`

## 1. Intent

Merge the fresh bounded live evidence with the earlier legacy-manuscript surveys before the authority-sink lane proceeds.

This audit answers three questions:

- did the fresh run reproduce the earlier stale metadata drift
- which parts of the older synthesis remain valid
- what execution scope still survives after completed live evidence outranks static inference

## 2. Scope

Included:

- `projects/0` completed bounded run on `2026-03-16`
- `projects/000` startup-only fresh control session on `2026-03-16`
- persisted `projects/000` Stage 4 authority rows for session `20260315_190609`
- historical contrast project `projects/00_260315`
- Stage 4 final/patched artifact text files, DB `manuscripts`, DB `stage_attempts`, DB `director_selections`, and live runtime summaries

Excluded:

- new broad contradiction hunting across all historical projects
- continuity-class reclassification beyond the authority-sink question
- code patching

## 3. Pass 1. Inventory

### 3.1 Project `0` bounded fresh run

The fresh run reached a true terminal state.

- `runtime_audit_summary.json` closed as `shutdown_final`
- Stage 4 proof digest was `ok`
- Stage 4 coverage was `9/9` on considered attempts with empty `issue_counts`
- session lineage mapped plain log `20260316_071001` to structured session `20260316_071008`
- the session log closed with `213` successful calls, `2,658,618` tokens, and `1:32:20` duration

The authority join for the six published Stage 4 episodes aligned fully. The only patched case, `ep5`, stored:

- patched artifact path in `stage_attempts`
- `selected_candidate__A.txt` path in `director_selections`
- equal content hashes across `stage_attempts`, `director_selections`, DB manuscript content, and the on-disk text payloads

### 3.2 Project `000` fresh control run

The fresh `2026-03-16` control session was not a production run.

- terminal state was still `shutdown_final`
- the log closed after startup/shutdown with `0` calls and `0` tokens
- proof digest warned on `patch_strategy_mismatches = 1`

That warning does not by itself prove stale metadata drift. The persisted Stage 4 rows for the real production session `20260315_190609` were rechecked and remained aligned across:

- `stage_attempts`
- `director_selections`
- DB `manuscripts`
- on-disk final or patched artifact text

### 3.3 Historical contrast: `00_260315`

The earlier stale metadata authority pattern still exists historically.

- `ep4`: `patched_after_fix__A_InPlace.txt` vs `selected_before_fix__C.txt`
- `ep5`: `patched_after_fix__A_InPlace.txt` vs `selected_before_fix__A.txt`

For both episodes:

- `stage_attempts` matched DB manuscript content
- `director_selections` pointed to different pre-fix content
- the on-disk patched and selected files each matched their own hashes

## 4. Pass 2. Merged Findings

### 4.1 Fresh live surfaces did not reproduce stale hash drift

The strongest live result is negative reproduction:

- `projects/0` completed a real bounded run and did not produce the stale split
- `projects/000` fresh control run did not produce new manuscript data, and its persisted real run rows also remained aligned

This beats the earlier static-only inference that the stale split was still effectively live on active surfaces.

### 4.2 The historical issue class remains real

The historical stale-authority class is still confirmed, not hypothetical.

- `00_260315 ep4-5` remain valid examples
- the old issue should not be deleted from institutional memory
- but it is now a historical row / consumer-interpretation problem, not a currently reproduced fresh-run defect

### 4.3 The surviving live risk is narrower

What survives into execution scope is no longer "fix the currently reproduced drift bug."

What survives is:

- final-authority contract clarification after patch/finalization
- consumer hardening so `director_selections` is not over-read as standalone final truth
- bounded handling for legacy stale rows already present in older project DBs

## 5. Pass 3. Execution Consequence

The authority-sink lane remains justified, but its shape narrows.

Keep:

- one execution lane
- narrow scope
- direct emphasis on authority resolution and operator/analyzer semantics

Drop:

- any claim that the latest bounded fresh run actively reproduced stale content-hash drift
- any framing that this is a broad contradiction-remediation program

## 6. Final Conclusion

The post-run merge outcome is stable:

- active bounded fresh/live evidence did not reproduce stale authority drift
- historical stale rows still exist and are real
- the correct next execution lane is hardening the final-authority contract and consumer behavior, plus optionally surfacing or backfilling legacy mismatches

That is narrower than the earlier static-only synthesis, and therefore stronger.
