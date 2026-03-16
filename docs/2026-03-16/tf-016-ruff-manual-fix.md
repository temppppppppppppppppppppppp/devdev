<!-- [완료] -->
<\!-- [완료] -->
# TF-016 Ruff Manual Fix

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/tf-016-ruff-manual-fix.md`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active post-remediation docs/temp edits, desktop/runtime/stage4 patches, tests, projects/000 artifacts, and untracked post-remediation reports`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-016 is being realized after TF-015 closure; TF-019 remains behind it`
Source Evidence:
- `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
- `docs/2026-03-16/tf-015-ruff-auto-fix.md`
- live `ruff check modules scripts main_a.py`

## 1. Intent
- Resolve the remaining non-auto-fixable Ruff findings left after `TF-015`.
- Keep the manual pass narrow and explicit instead of rewriting working script entrypoints.

## 2. Live Findings
- After `TF-015`, the lint backlog was reduced to only `9` `E402` violations.
- All `9` violations came from standalone script entrypoints that intentionally modify `sys.path` before importing workspace modules.
- These are not accidental import-order bugs; they are bootstrap ordering requirements for script execution.

## 3. Realization
- Added explicit `# noqa: E402 - entrypoint path bootstrap must precede imports` suppressions to the affected imports in:
  - `scripts/audit_bi_5pass.py`
  - `scripts/backfill_quality_sidecars.py`
  - `scripts/build_bi_from_phase0_and_tr.py`
  - `scripts/build_chaebol_allowance_zero_assets.py`
  - `scripts/build_fallen_prince_buys_joseon_assets.py`
  - `scripts/build_investment_epub_corpus.py`
  - `scripts/process_and_audit_tr_bi_loop.py`
- No runtime logic changed; only the lint disposition became explicit at the import sites.

## 4. Result
- `ruff check modules scripts main_a.py` now passes cleanly.
- The manual lint backlog is `0`.

## 5. Verification
- `python -m py_compile scripts/audit_bi_5pass.py scripts/backfill_quality_sidecars.py scripts/build_bi_from_phase0_and_tr.py scripts/build_chaebol_allowance_zero_assets.py scripts/build_fallen_prince_buys_joseon_assets.py scripts/build_investment_epub_corpus.py scripts/process_and_audit_tr_bi_loop.py`
- `ruff check modules scripts main_a.py` -> `All checks passed!`
- `ruff check modules scripts main_a.py --statistics` -> `0 findings`

## 6. Follow-On
- Close `TF-016` inside the residual lane.
- Continue with `TF-019`, the final remaining hardening item.
