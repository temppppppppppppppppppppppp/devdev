Date: 2026-03-28
Status: final (3-pass audited)
Document Type: system-track defer ledger
Canonical Path: `docs/2026-03-28/system-remaining-defer-ledger.md`
Temp Mirror Path: none
Source Docs:
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md`
- `docs/2026-03-27/provider-request-shape-stability-wave1-execution-ssot.md`
- `docs/2026-03-27/stage4-god1-handoff-replacement-wave1-execution-ssot.md`
- `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-27/wuxia-technique-realm-tracking-design-memo.md`

Commit State:
- Baseline Commit: `8f6e16f9995aed633a6de64a045c2a0184831668`
- Baseline Dirty Summary: `dirty: tracked config/models, implementation docs, provider/runtime scripts/tests, benchmark and TR harness files; untracked docs/2026-03-28 outputs, system-supervisor harness, harness-digest artifacts, new router/test files`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent

- Separate active queue work from true deferred backlog.
- Subtract already-closed 2026-03-27 defer items from the still-open backlog.
- Leave one operator-readable answer to the question: "what is actually still deferred now?"

## 2. Executive Read

The remaining defer set is narrower than the older freeze stack suggests.

Closed and no longer part of the live defer backlog:
- `state_changes schema formalization`
- `provider request-shape stability`
- `stage4 _god1_* handoff replacement`

Still active right now, but not true defer:
- `npc-martial-state-substrate-wave1`
- `frontier-lag-soak-canary-wave1`
- one queue-sync discrepancy between `docs/temp/execution-roadmap.md` and `docs/temp/queue-state.json`

Highest remaining true defer seam:
- `realm owner + NPC technique-model gap`

## 3. Closed Items Removed From Live Defer

| Item | Current State | Evidence | Note |
| --- | --- | --- | --- |
| `state_changes schema formalization` | closed | `docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md` | no longer count this as an open defer |
| `provider request-shape stability` | closed | `docs/2026-03-27/provider-request-shape-stability-wave1-execution-ssot.md` | provider/request-shape cleanup already realized |
| `stage4 _god1_* handoff replacement` | closed | `docs/2026-03-27/stage4-god1-handoff-replacement-wave1-execution-ssot.md` | do not keep this in the active defer stack unless fresh regression appears |

Operator rule:
- The 2026-03-27 freeze order is still useful as lineage, but it must now be read after subtracting these closed items.

## 4. Active Queue, Not Defer

Current queue truth:
- roadmap says `npc-martial-state-substrate-wave1` is `in_progress`
- roadmap says `frontier-lag-soak-canary-wave1` is `pending`
- `queue-state.json` marks both items as `in_progress`

Interpretation:
- this is an active queue and queue-sync problem
- this is not evidence that the defer backlog expanded

Immediate consequence:
- repair roadmap versus queue-state alignment before using either file as the single next-step authority

## 5. Remaining True Defer

### 5.1 Next-Wave Candidate

`realm owner + NPC technique-model gap`

Why it remains:
- the narrowed freeze still keeps this seam in the fact-contract top tier
- current design memo still says `NPC technique mastery` and `NPC realm progression` are `deferred` and `not in next wave`
- current residual survey still says the dominant technique/realm issue is structural modeling, not another contract-alignment pass

What this means operationally:
- if a fresh defer-focused wave opens after current queue closure, this is the first real candidate
- scope should stay narrow:
  - canonical realm owner
  - NPC technique mastery owner
  - NPC realm progression owner
- do not inflate this into a full wuxia registry redesign

### 5.2 Later-Wave Consumers Explicitly Left Out Of `npc-martial` Wave 1

Still deferred:
- Stage 4 injection
- validator activation
- `FactLedger` martial modeling
- chronology/reveal ledger
- DB expansion

Interpretation:
- these are follow-on consumers or persistence expansions
- they should not be smuggled into the current active queue item

### 5.3 Structural Modeling Backlog, Clearly Later

Deferred modeling items from the residual survey:
- organization membership edges
- fight geography
- cross-episode escalation
- event causality chains

Interpretation:
- these are not "quick next wave" items
- they require new persistence design or broader cross-episode state, not a narrow patch

## 6. Priority Call

Use this order:

1. sync `docs/temp/execution-roadmap.md` and `docs/temp/queue-state.json`
2. close the current active queue items cleanly
3. only then consider opening a new defer-focused wave
4. when that wave opens, start with `realm owner + NPC technique-model gap`
5. keep the broader modeling backlog parked until a dedicated design memo or failure evidence justifies promotion

Do not reopen as "remaining defer":
- `state_changes schema formalization`
- provider/request-shape normalization
- `_god1_*` replacement

unless fresh live evidence shows regression.

## 7. Side-Effect Coverage

- file writes: this ledger only
- DB writes: not applicable
- JSONL/log/audit sinks: not applicable
- console/UI output: not applicable
- rollback/recovery/retry: not applicable
- cache/global state: not applicable
- bootstrap/config mutation: not applicable

## 8. 3-Pass Audit Record

### Pass 1. Structure and Scope

- document type is a defer ledger, not an execution SSOT
- active queue and true defer are explicitly separated
- save path is canonical dated docs only
- PASS

### Pass 2. Evidence and Consistency

- verified the three previously top defer items that are now closed
- verified the current temp roadmap versus queue-state mismatch
- verified that the remaining technique/realm seam is still open in the current design memo and residual survey
- PASS

### Pass 3. Execution and Readability

- next action is explicit
- "closed", "active queue", and "true defer" are not mixed
- later-wave backlog is kept bounded instead of turned into a wish list
- PASS

Estimated confidence: `96%`
