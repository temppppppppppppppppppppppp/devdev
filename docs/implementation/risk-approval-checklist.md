# Risk Approval Checklist

## Pre-check
- [ ] Ticket exists and is linked to request.
- [ ] Target key is one of `44/77/88/99`.
- [ ] Request reason is specific and testable.
- [ ] Rollback path is defined.
- [ ] Time window and `expires_at` are set.

## Dual-control
- [ ] Primary approver assigned.
- [ ] Secondary approver assigned.
- [ ] Primary and secondary approvers are different people.
- [ ] Operator is not both approvers.

## Runtime enforcement
- [ ] Request without `approval_id` returns `403 RISK_APPROVAL_REQUIRED`.
- [ ] Expired approval returns `403 RISK_APPROVAL_EXPIRED`.
- [ ] Same approver identity returns `403 RISK_APPROVAL_DUAL_CONTROL_REQUIRED`.
- [ ] UI requires two-step confirm before run.

## Audit
- [ ] `risk-approval-log.jsonl` record created.
- [ ] Log has `approval_id`, `ticket_id`, approvers, and timestamps.
- [ ] Execution log can be traced by `approval_id`.
- [ ] QA verified at least one valid and one invalid path.
