# Side-Effect Survey Checklist

Date: 2026-03-14
Status: active
Applies To: system-track surveys, audits, execution SSOTs, and risky direct patches

## 1. Purpose
- Provide a reusable checklist for side-effect coverage during surveys.
- Make `covered / partial / not-applicable` explicit for every major side-effect class.

## 2. Use Rule
For each applicable target surface, mark every category:
- covered
- partial
- not-applicable

Do not leave a category implicit.

## 3. Checklist

### A. File and Artifact Writes
- Which files are created, updated, renamed, or deleted?
- Are there derived artifacts, exports, caches, or reports?
- Are write paths stable or dynamic?

### B. DB and Transaction Boundaries
- Which tables, schemas, or migrations are touched?
- Are transactions explicit, implicit, or absent?
- What happens on partial failure?

### C. JSONL, Logs, and Audit Sinks
- Which JSONL or log files receive new records?
- Are there audit trails, proof digests, or event streams?
- Does the change alter retention or visibility?

### D. Console, UI, and Operator Surface
- What does the operator see before and after the change?
- Which messages are warnings, prompts, summaries, or errors?
- Does console-visible behavior diverge from durable logging?

### E. Recovery, Retry, and Compensation
- Are there retries, backoff loops, or compensating actions?
- What rollback or cleanup path exists?
- Is the failure mode silent, noisy, or recoverable?

### F. Cache, Singleton, and In-Memory State
- Are there global caches, singleton services, or process-local registries?
- Does order of execution affect correctness?
- Is state reset or invalidation required?

### G. Bootstrap, Config, and Environment
- Are env vars, config files, or bootstrap defaults involved?
- Is there a pre-runtime or no-context fallback path?
- Are secrets or machine-local assumptions present?

### H. External Interfaces
- Are subprocesses, network calls, desktop IPC, or external services involved?
- Does the surface expose a new contract or dependency?
- What evidence exists for success and failure paths?

## 4. Output Pattern
Recommended survey summary block:

```text
file writes: covered
DB / transaction: partial
JSONL / logs: covered
console / UI: covered
recovery / retry: not-applicable
cache / global state: covered
bootstrap / config-env: covered
external interfaces: partial
```

## 5. Guardrails
- Do not reduce side-effects to file writes only.
- Do not mark a category `not-applicable` without checking it first.
- Do not skip operator-visible output when the request touches logging, prompts, or runtime messages.
