# docs/temp Operating Note

Purpose:
- temporary collection inbox and active execution queue for execution SSOT mirror copies
- optional temporary working area for downstream collation or post-processing

Companion harness:
- `docs/implementation/temp-execution-queue-roadmap-harness.md`

Rules:
- canonical survey, audit, evidence, and side-effect documents live in `docs/YYYY-MM-DD/`
- canonical execution SSOT documents also live in `docs/YYYY-MM-DD/`
- files in `docs/temp/` are mirror copies, not canonical authorities
- edit the canonical execution SSOT first, complete the document 3-pass audit, meet the 95% confidence gate, then refresh the mirror copy
- do not keep an execution SSOT only in `docs/temp/`
- `docs/temp/` may be cleared after collation, but only after confirming the canonical dated copy exists
- human-facing docs should not land here before the 3-pass document audit is complete and estimated confidence is at least 95%
- a mirrored execution SSOT in `docs/temp/` means it is pending or active for realization
- `docs/temp/queue-state.json` is optional, but if used it must reflect the live queue and be deleted when the queue is empty
- preferred sync command: `python scripts/sync_temp_queue_state.py`
- once realization is complete, remove that execution SSOT mirror from `docs/temp/`
- if multiple execution SSOT mirrors exist, create an aggregate roadmap first and execute by roadmap order
- use `docs/implementation/queue-priority-rubric.md` when ordering is not obvious
- run `python scripts/ops_validator.py` before claiming the queue is clean
- once the roadmap is exhausted, clear active execution artifacts from `docs/temp/`

Recommended contents:
- `*-execution-ssot.md` mirror copies
- `execution-roadmap.md` mirror copy when multiple execution SSOTs are queued
- `queue-state.json` only when a machine-readable queue snapshot is useful
- this README
