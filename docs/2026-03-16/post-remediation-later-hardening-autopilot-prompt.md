<!-- [참고자료] -->
<\!-- [참고자료] -->
# Post-Remediation Later Hardening Autopilot Prompt

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt.md`
Automation Helper: `scripts/render_later_hardening_autopilot.py`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active post-remediation docs/temp edits, desktop/runtime/stage4 patches, tests, projects/000 artifacts, and untracked post-remediation reports`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Governing Queue Docs:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-3pass-audit.md`
- `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`
- `docs/temp/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/temp/execution-roadmap.md`

## 1. Intent
- Give one stable prompt that another Codex-style agent can use to continue the residual later-hardening tranche unattended.
- Keep the execution order fixed to the only remaining residual items: `TF-014`, `TF-015`, `TF-016`, `TF-019`.
- Pair the prompt with one live automation helper so the next operator can regenerate the prompt against the current queue state instead of reusing stale March 15 counts.

## 2. Live Drift Snapshot
- The residual lane is still the active queue authority; completed lanes must not be reopened.
- Live Ruff drift is already beyond the March 15 survey snapshot:
  - `ruff check modules scripts main_a.py --statistics` currently reports `66` errors, with `53` fixable via `--fix`.
- Live production/runtime-script `print()` inventory is also larger than the old survey headline:
  - `180` raw `print()` calls across `main_a.py`, `modules/`, `scripts/`, and `geuldobi-desktop/src/`
  - the largest cluster is `modules/core/stage0/spinner.py` with `48` hits, so `TF-014` must distinguish spinner output from diagnostic output.
- Guard-config loading remains distributed rather than centralized:
  - runtime anchors include `main_a.py`, `modules/core/genre_guards/work_guard.py`, `modules/core/config_manager.py`, `modules/validation/scoring_validator.py`, `modules/validation/consistency_validator.py`, and `modules/core/project_support.py`.

## 3. Ordered Loop
1. `TF-014` console print audit
2. `TF-015` Ruff auto-fix
3. `TF-016` Ruff manual-fix
4. `TF-019` guard chain config validation

Per item, run the same bounded loop:
1. Re-read the governing canonical docs and re-run a current-workspace 3-pass audit.
2. If confidence is below `95%`, or the item has become stale/no-op, save the decision as documentation and do not patch code.
3. If confidence is at least `95%`, implement only the minimal change justified by the live workspace.
4. Run targeted validation for the touched surface.
5. Update canonical docs first, then temp mirrors, roadmap state, and queue-state.
6. Run `python scripts/sync_temp_queue_state.py` and `python scripts/ops_validator.py --strict`.
7. Move to the next TF only after the current TF is closed or explicitly split into a successor queue item.

## 4. Copy-Paste Prompt
```text
You are Codex operating in c:\Users\User\Desktop\글도비.

Treat this as system-track queue realization. Do not reopen completed lanes. The active residual lane is:
- docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md
- docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md

Read, in order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/implementation/temp-execution-queue-roadmap-harness.md
5. docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md
6. docs/2026-03-15/post-remediation-unqueued-survey-followups-3pass-audit.md
7. docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md
8. docs/temp/queue-state.json

Current live drift to respect before patching:
- HEAD is still bbb00a77c7356a32fe6358642cff0d3d445b7e8e.
- Ruff is no longer at the old March 15 snapshot; live `ruff check modules scripts main_a.py --statistics` reports 66 errors with 53 fixable.
- Raw print inventory across `main_a.py`, `modules/`, `scripts/`, and `geuldobi-desktop/src/` is 180 hits, with spinner-heavy concentration in `modules/core/stage0/spinner.py`.
- Guard-config loading is still distributed across `main_a.py`, `modules/core/genre_guards/work_guard.py`, `modules/core/config_manager.py`, `modules/validation/scoring_validator.py`, `modules/validation/consistency_validator.py`, and `modules/core/project_support.py`.

Execute only this ordered loop:
1. TF-014 console print audit
2. TF-015 Ruff auto-fix
3. TF-016 Ruff manual-fix
4. TF-019 guard chain config validation

For each TF:
1. Re-audit the current workspace with a fresh 3-pass review of the governing canonical doc and confirm confidence >= 95%.
2. If the item is now a no-op or only warrants a decision doc, save the decision and close the item without broad code churn.
3. If code change is justified, patch only the smallest live surface needed.
4. Run targeted validation, plus UTF-8 hygiene on touched files.
5. Update canonical docs first, then temp mirrors, roadmap status, and queue-state.
6. Run `python scripts/sync_temp_queue_state.py` and `python scripts/ops_validator.py --strict`.
7. Only then continue to the next TF.

Mandatory validation baseline by TF:
- TF-014:
  - `rg -n "\bprint\s*\(" main_a.py modules scripts geuldobi-desktop/src`
  - `python -m pytest tests/test_runtime_print_allowlist.py`
  - targeted pytest shards for any touched logging/runtime files
- TF-015:
  - `ruff check modules scripts main_a.py --statistics`
  - `ruff check modules scripts main_a.py --fix`
  - `ruff check modules scripts main_a.py`
- TF-016:
  - `ruff check modules scripts main_a.py`
  - `python -m py_compile <touched python files>`
  - targeted pytest shards for touched modules
- TF-019:
  - re-audit guard loader/runtime surfaces first
  - add or update targeted tests around invalid YAML/schema failure at startup
  - run only the relevant config/guard tests after patching

Hard stop conditions:
- confidence below 95%
- evidence mismatch between canonical docs and live code
- scope expansion that needs a successor execution SSOT
- UTF-8 hygiene violation
- direct collision with unrelated dirty user work that cannot be safely composed

Do not:
- reopen TF-007 through TF-013, TF-017, TF-018, or TF-020
- convert spinner UX output into hidden logging if the print is operator-facing by contract
- use stale March 15 counts as live truth
- edit only docs/temp without updating the canonical dated doc
```

## 5. Automation Usage
- Live prompt render:
  - `python scripts/render_later_hardening_autopilot.py`
- JSON snapshot for tooling:
- `python scripts/render_later_hardening_autopilot.py --json`
- Save a fresh prompt artifact:
  - `python scripts/render_later_hardening_autopilot.py --write docs/2026-03-16/post-remediation-later-hardening-autopilot-live.md`

## 6. Guardrails
- The automation helper is allowed to regenerate prompt text and live drift summaries, but it must not auto-patch code or mutate queue files on its own.
- Queue authority stays in the canonical residual SSOT and canonical roadmap, not in this prompt note.
- If live drift changes the ordered work or introduces a new successor lane, the prompt note itself must be re-audited before reuse.
