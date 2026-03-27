# System Maturity Next-Band Wave1 Tranche2 Stale Reference Cleanup Closure

Date: 2026-03-27
Status: final
Scope: low-risk doc-only stale-authority cleanup performed during the Tranche 2 canary wait window
Parent Wave: `docs/2026-03-27/system-maturity-next-band-wave1-execution-ssot.md`
Related Sweep:
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-sweep.md`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-findings.txt`

## 1. Outcome

- The incoming cleanup note was mechanically correct about the two edited files, but it was not closure-ready as submitted.
- Live audit confirmed that `AGENTS.md` is the current workspace SSOT, yet it is not the provenance source for the specific full-suite baseline values recorded in `docs/stage_map/metrics_baseline.md`.
- Closure therefore required a small follow-up correction before sign-off:
  - replace the mistaken `AGENTS.md` source reference with the dated audit document that actually contains the cited baseline values
- No active authority docs, temp queue artifacts, code files, or canary artifacts were touched by this closure.

## 2. Corrected Files

- `docs/stage_map/metrics_baseline.md`
  - restored the baseline source from a stale-authority replacement to the dated evidence document that actually records:
    - `3,847 collected, 3,831 passed, 16 skipped`
    - `Ruff: 0 violations`
- `docs/stage_map/UPDATE_ORDER.md`
  - aligned the stage_map refresh source mapping with the same dated evidence source

## 3. Audit Basis

- Live diff audit confirmed that the incoming cleanup only changed two references:
  - `docs/stage_map/metrics_baseline.md`
  - `docs/stage_map/UPDATE_ORDER.md`
- Live source recheck confirmed the cited baseline values do not appear in:
  - `AGENTS.md`
  - `CLAUDE.md`
- Live source recheck confirmed the cited baseline values do appear in:
  - `docs/2026-03-12/TF-HEALTH-codebase-full-audit.md`

## 4. Pass Record

Pass 1. Structure and scope
- kept this closure bounded to the stale-reference cleanup subtask only
- did not widen into historical doc rewriting or active queue/SSOT edits

Pass 2. Evidence and consistency
- checked the incoming diff directly
- verified that the initial `AGENTS.md` replacement was semantically wrong for provenance
- verified the replacement evidence path against the live dated audit doc

Pass 3. Execution and readability
- corrected the two active stage_map docs
- recorded explicit residual boundaries so this closure cannot be misread as Tranche 2 closure

Estimated confidence after re-audit: 97%

## 5. Residuals

- Historical `CLAUDE.md` references in dated docs remain intentionally untouched.
- The broader Tranche 2 item remains `in_progress`; this closure does not satisfy:
  - fresh canary evidence
  - exception review outcome
  - final Tranche 2 SSOT status update

## 6. Closure Decision

- `stale-reference cleanup subtask`: closed
- `system-maturity-next-band-wave1 / Tranche 2`: still in progress
