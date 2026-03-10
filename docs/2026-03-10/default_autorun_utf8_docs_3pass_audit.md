# Default Auto-Run + UTF-8 Docs 3PASS Audit (2026-03-10)

## Targets
- planning: `docs/blockguide/treatment-planning-harness.md`
- treatment: `docs/blockguide/treatment-production-harness-v2.md`
- bi: `docs/blockguide/bi-production-harness-v1.md`

## PASS 1 UTF-8 baseline
- result: OK
- planning_utf8_only: OK
- treatment_utf8_only: OK
- bi_utf8_only: OK
- all_docs_utf8_readable: OK

## PASS 2 auto-run default
- result: OK
- planning_autorun_default: OK
- treatment_autorun_default: OK
- bi_autorun_default: OK
- all_docs_have_stop_gate: OK

## PASS 3 compaction and corruption gates
- result: OK
- planning_compaction_resume: OK
- treatment_compaction_resume: OK
- bi_compaction_resume: OK
- utf8_corruption_is_stop_gate: OK
- utf8_only_emphasized_in_body: OK

## Notes
- verification method: PowerShell `Get-Content -Encoding UTF8 -Raw` + substring checks
- auto-run is now the default path across planning, treatment, and BI docs
- compaction no longer implies waiting for user; SSOT reopen -> automatic resume
- UTF-8 only is explicitly declared at the top and repeated in-body for all three docs
- overall: PASS
