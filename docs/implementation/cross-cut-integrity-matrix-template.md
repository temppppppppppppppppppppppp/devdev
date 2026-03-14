# Cross-Cut Integrity Matrix Template

Use this matrix inline in a deep survey doc or as a companion doc when cross-cut integrity needs explicit rollup.

| Cross-Cut Surface | Authority / Owner | Key Touchpoints | Major Side-Effects | Evidence Classes Used | Known Gap | Governing Execution Doc |
| --- | --- | --- | --- | --- | --- | --- |
| Observability | `<owner>` | `<files/services>` | console, log, JSONL, DB | A+B(+C) | `<gap>` | `<doc or none>` |
| Persistence | `<owner>` | `<files/services>` | DB writes, transactions, migrations | A+B(+D) | `<gap>` | `<doc or none>` |
| Operator Surface | `<owner>` | `<files/services>` | prompts, selections, UI output | A+B(+C) | `<gap>` | `<doc or none>` |
| Contracts / Config | `<owner>` | `<files/contracts>` | drift, bootstrap assumptions | A+D(+E) | `<gap>` | `<doc or none>` |
| Recovery / Retry | `<owner>` | `<files/services>` | retry, rollback, fallback | A+B(+C) | `<gap>` | `<doc or none>` |
| Subprocess / Network | `<owner>` | `<files/services>` | spawn, bridge, HTTP | A+B(+C) | `<gap>` | `<doc or none>` |
| Cache / Global State | `<owner>` | `<files/services>` | singleton or in-memory mutation | A+B | `<gap>` | `<doc or none>` |
| Regression / Canary | `<owner>` | `<files/scripts/tests>` | mutation vs read-only checks | A+B(+C) | `<gap>` | `<doc or none>` |
| Shadow / Stale Authority | `<owner>` | `<files>` | debug-shadow or drift risk | A+B(+E) | `<gap>` | `<doc or none>` |
