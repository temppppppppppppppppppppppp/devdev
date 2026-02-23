# Runbook

Purpose:
- Define standard operation and incident response steps.

## Normal Run
1. Pre-check configuration and dependencies.
2. Run target stage(s).
3. Validate outputs.
4. Record metrics and update stage docs.

## Retry Procedure
1. Capture failure context (stage, input, error, logs).
2. Apply retry policy (count, backoff, guardrails).
3. Re-run with minimal scope.
4. Compare outputs and side effects.

## Rollback Procedure
1. Identify rollback point (checkpoint/snapshot/commit).
2. Revert data and runtime state as defined.
3. Verify consistency checks.
4. Resume from validated boundary.

## Resume Procedure
1. Validate last committed checkpoint.
2. Restore required runtime state.
3. Re-run idempotency check.
4. Continue pipeline.

## Incident Template
- Timestamp:
- Stage:
- Trigger:
- Impact:
- Immediate mitigation:
- Root cause:
- Preventive action:

## Last Verified
- Date:
- Commit:
- Code Sync (Yes/No):
- Verified By:

