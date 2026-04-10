# Live Run Merge Survey Harness

Date: 2026-03-15
Status: active
Applies To: system-track orders that intentionally combine fresh live runs with survey or audit work
Companion First-Read: `docs/implementation/system-order-init-harness.md`
Required Companion:
- `docs/implementation/system-full-survey-execution-harness.md`
Related Companions:
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/evidence-manifest-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/ops-validator-harness.md`
- `docs/implementation/execution-closure-harness.md`

## 1. Purpose
- Define the operating mode for `static survey + fresh live run + post-run merge audit`.
- Let operators investigate broadly while a real run is generating evidence, without prematurely freezing stale conclusions.
- Separate mid-run evidence capture from post-run SSOT conclusions.
- Keep final authority aligned with completed live evidence rather than partial runtime state.

## 2. When To Use
Use this harness when the user explicitly wants one or more of the following:
- `ROL 전수조사-실전테스트 병행`
- `ROL live-merge`
- fresh live run plus survey
- 실전테스트 중 전수조사
- global/static investigation while a bounded real run is executing

Do not use this harness when:
- the user wants only a static survey with no live run
- the user wants only a live run with no parallel survey/audit output
- the run has already completed and the task is now a normal post-run audit

## 3. Mode Definition
Live-merge mode is a bounded ROL variant with three lanes:
1. pre-run static watchlist and survey scaffolding
2. live-run raw evidence capture
3. post-run merge audit that upgrades the work into canonical conclusions

This mode is not:
- a license to final-save survey conclusions before the run completes
- a license to treat mid-run DB/log state as final truth
- a shortcut around the 3-pass document audit and 95% confidence gate

Accepted aliases:
- `ROL 전수조사-실전테스트 병행`
- `ROL live-merge`
- `live-merge survey`

## 4. Authority Rules
- completed live-run evidence beats static inference
- static inference beats stale survey text
- stale survey text beats memory or assumption
- mid-run evidence is provisional until the run reaches a terminal state or is explicitly abandoned

Terminal-state rule:
- `completed`
- `failed`
- `stopped`
- `aborted by operator`

If the run is still in progress, no final resolution claim may be saved.

## 5. Allowed Outputs By Phase

### 5.1 Before Or During The Run
Allowed:
- raw evidence files
- inventories
- sink maps
- prompt-site manifests
- draft watchlists
- explicit draft notes marked as pending live evidence
- evidence manifests

Not allowed as final:
- canonical closure claims
- final SSOT conclusions
- execution SSOT mirrors in `docs/temp/`
- roadmap completion or queue cleanup decisions driven by incomplete run data

Draft marker rule:
- if a human-facing document must exist before the run completes, mark it explicitly as `draft-live-run-pending`
- do not present it as a final survey or closure document

### 5.2 After The Run Completes
Allowed:
- merged 3-pass audit
- canonical final survey doc
- execution SSOT docs for action-bearing findings
- roadmap creation or refresh if multiple execution items emerge
- queue or closure actions after the merged audit passes confidence gates
- ClickUp reflection only after canonical docs, temp mirrors, and queue-state refresh are complete

## 6. Standard Workflow

### Step 0. Confirm Mode
- Confirm the task is system-track.
- Confirm that a fresh live run is intentionally paired with survey work.
- If the task is global or repo-wide, also load the global coverage contract and deep-global harness as needed.

### Step 1. Pre-Run Static Watchlist
- Inventory likely risk surfaces before the run starts.
- Capture:
  - prompt sites
  - DB write points
  - JSONL/log/audit sinks
  - stderr/stdout capture boundaries
  - rollback/retry paths
  - known residual risks from prior audits
- Save this as a watchlist or evidence manifest, not as a resolved conclusion.

### Step 2. Live-Run Evidence Capture
- During the run, collect raw evidence only.
- Prefer immutable or append-only capture surfaces:
  - session logs
  - JSONL sinks
  - summary snapshots
  - DB row counts or bounded snapshots
  - operator transcript captures
- If the run fails, record the terminal state and preserve the failure evidence as-is.

### Step 3. Parallel Static Deepening
- While the run is active, continue static code reading, sink tracing, and side-effect mapping.
- New hypotheses may be added to the watchlist.
- Do not upgrade hypotheses to final findings until post-run merge.

### Step 4. Run Completion Gate
- Wait for a terminal run state before final interpretation.
- If the run never reaches a usable terminal state, produce an incomplete-run note rather than a closure claim.
- If the user stops the run intentionally, classify the evidence as bounded and partial.

### Step 5. Post-Run Merge Audit
- Merge:
  - pre-run static watchlist
  - live-run raw evidence
  - post-run static re-checks
- Then run the normal 3-pass audit.
- Confidence must reach at least 95% before final save.

### Step 6. Execution Output Decision
- If the merged audit finds only bounded observations, stop at survey output.
- If it finds action-bearing items, create canonical execution SSOT docs after the merged audit.
- Create `docs/temp/` mirrors only after the governing canonical execution docs pass the save gate.
- If the merged audit materially changes queue status or roadmap ordering, refresh `docs/temp/queue-state.json`, validate the queue, and only then mirror the change into ClickUp.

## 7. Output Set
Recommended output shapes for this mode:
- `docs/YYYY-MM-DD/*-preflight-watchlist.md`
- `docs/YYYY-MM-DD/*-live-run-evidence-manifest.md`
- `docs/YYYY-MM-DD/*-live-run-evidence.txt`
- `docs/YYYY-MM-DD/*-post-run-merge-audit.md`
- `docs/YYYY-MM-DD/*-execution-ssot.md` when warranted
- `docs/YYYY-MM-DD/*-execution-roadmap.md` when two or more execution items emerge

Naming guidance:
- keep one stable topic slug across the watchlist, evidence manifest, merge audit, and any execution docs
- use `post-run-merge` in the final survey filename when the distinction matters

## 8. Temp Queue Rule
- Do not create or refresh `docs/temp/` execution mirrors while the live run is still active.
- Temp queue artifacts are allowed only after the post-run merge audit has produced canonical execution docs that pass the save gate.
- If earlier temp queue items already exist for unrelated work, leave them governed by the normal queue rules; do not let the live-run mode silently rewrite them.

## 9. Guardrails
- Do not mistake mid-run mismatch or missing data for final failure without checking whether the run was still active.
- Do not freeze a canonical SSOT while the evidence-generating run is still moving.
- Do not let shell-host capture quirks outrank the completed run's authoritative sinks.
- Do not treat provisional watchlists as closure notes.
- Do not mirror draft execution documents into `docs/temp/`.
- Do not mirror provisional live-run findings into ClickUp before the post-run merge audit is finalized.

## 10. Completion Markers
Before declaring the live-merge cycle complete, confirm:
- the live run reached a documented terminal state
- raw evidence artifacts are saved or intentionally discarded with reason
- static survey findings were re-checked against completed live evidence
- the final human-facing document passed 3-pass audit
- confidence is at least 95%
- any execution SSOT mirrors were created only after the merged canonical doc was finalized
