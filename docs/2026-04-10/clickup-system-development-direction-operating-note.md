# ClickUp System Development Direction Operating Note

Date: 2026-04-10
Status: final
Canonical Path: `docs/2026-04-10/clickup-system-development-direction-operating-note.md`
Baseline Commit: `e597a7bf4836dab71547e350b015f6658a1cfb03`
Baseline Dirty Summary: `dirty worktree already contained active stage0/material edits plus unrelated tests/scripts/doc changes; this note adds one dated operating document only`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `same-turn planning note; no code changes; conclusions are grounded in current HEAD docs, queue artifacts, and control-plane contracts`

## 1. Question

Now that ClickUp has been introduced, how should the Geuldobi system evolve in a structured way without creating a second SSOT or adding more operator confusion?

## 2. Scope

Included surfaces:
- system-track operating model only
- ClickUp role definition for queue, proof, and product work
- mapping between current repo-side execution artifacts and ClickUp tasks
- recommended Space / List / Status / Custom Field design
- near-term and mid-term development direction for the current system state

Excluded surfaces:
- narrative/material-side pipeline planning
- direct ClickUp API automation implementation
- code changes to the runner, bridge, desktop app, or DB
- replacement of the current canonical repo-side execution docs

## 3. Current State

### 3.1 The repo already has a real operating spine

Current HEAD is not a loose script pile anymore. The system already has a coherent operating path:

- CLI runtime owner in `main_a.py`
- bridge/control-plane layer in `modules/api/`
- Electron desktop shell in `geuldobi-desktop/`
- authoritative vs companion sink split in `modules/api/control_plane_contract.py`
- operator-facing readback via `/status`, `/quality/dashboard`, `proof_status`, `runtime_audit_summary`

This means the next step should not be "add more tools everywhere." The next step should be "make work selection, proof, and closure easier to operate."

Key evidence:
- `README.md`
- `modules/api/control_plane_contract.py`
- `modules/api/bridge_server.py`
- `docs/implementation/api-contract-v1.yaml`

### 3.2 Queue pressure is now a bigger problem than missing features

The current machine-readable queue state already shows a substantial active bundle:

- `docs/temp/queue-state.json` reports `queue_mode = "aggregate"`
- active item count is `21`
- the queue already distinguishes `front_active`, `blocked_holding`, `parked_future_wave`, and `historical_backing`
- the queue already has canonical doc paths, temp mirror paths, status, and roadmap rank

This is strong evidence that the next maturity step is queue control and closure discipline, not an immediate broad feature wave.

Key evidence:
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/implementation/temp-queue-state-contract-v1.json`
- `docs/implementation/queue-priority-rubric.md`

### 3.3 Operator readback is already rich enough to support productization

The bridge/dashboard layer already exposes the right direction of travel:

- `proof_status`
- `runtime_health`
- `gate_repair_summary`
- `artifact_ladder`
- `safe_ops`
- `budget_status`
- `control_plane_provenance`

That means ClickUp should sit above this stack as an execution-management layer, not compete with it as a fact store.

Key evidence:
- `modules/api/bridge_server.py`
- `tests/test_bridge_quality_summary.py`
- `docs/2026-04-09/stage234-proof-wave-logging-readiness-survey.md`

### 3.4 Human navigation drift still exists

The repo has strong runtime and queue structures, but some human-facing navigation still drifts. For example, current root docs still reference an orientation-pack path that is not present on disk. This is a reminder that growth should prioritize reducing operator ambiguity.

Operational consequence:
- ClickUp should not become another place where ambiguous truth accumulates
- repo-side canonical docs still need to remain the authority for conclusions and queue meaning

Key evidence:
- `README.md`
- `docs/implementation/system-order-init-harness.md`

## 4. Direction Judgment

Primary judgment:

ClickUp should be adopted as the system's execution-management layer, not as the system's semantic or technical SSOT.

What stays authoritative in the repo:
- `AGENTS.md` for workspace governance
- canonical docs in `docs/YYYY-MM-DD/`
- execution SSOT docs and the single active roadmap
- runtime evidence in DB / JSONL / artifacts / authoritative sinks

What ClickUp should own:
- intake
- prioritization
- assignment
- due dates and review cadence
- queue visibility for humans
- epics/waves across multiple repo-side execution lanes

What ClickUp should not own:
- final technical verdicts
- runtime truth
- source-of-truth queue semantics
- detailed remediation logic that belongs in canonical docs
- evidence interpretation that should live in dated surveys or execution SSOTs

## 5. Recommended ClickUp Model

### 5.1 Space

Recommended immediate setup:

- one Space: `Geuldobi System`

Recommended later split only if volume justifies it:

- `Geuldobi System`
- `Geuldobi Material`

Do not mix system-track and narrative/material-side active work in one queue by default. The repo governance is already split that way, and ClickUp should respect that split rather than blur it.

### 5.2 Lists

Inside `Geuldobi System`, use these lists:

1. `01 Intake & Survey`
2. `02 Canonical Queue`
3. `03 Proof & Validation`
4. `04 Product Surface`
5. `05 Architecture & Debt`
6. `06 Closed Archive`

Intent of each list:

- `01 Intake & Survey`
  - new issues
  - bounded surveys
  - triage notes
  - "do we need an execution SSOT?" questions
- `02 Canonical Queue`
  - tasks directly backed by active execution SSOT docs and the active roadmap
  - this list is the human mirror of the current repo queue, not a replacement for it
- `03 Proof & Validation`
  - merged proof waves
  - canaries
  - live-run verification
  - proof-closure follow-up after code lands
- `04 Product Surface`
  - desktop UX
  - bridge UX/readback
  - control-plane operator flow
  - dashboard ergonomics
- `05 Architecture & Debt`
  - owner-surface reduction
  - module boundary cleanup
  - Stage0/2/3/4 contract normalization not actively sitting at the front proof edge
- `06 Closed Archive`
  - closed items
  - historical backing tasks
  - parked work that should stop polluting the active view

### 5.3 Statuses

Recommended statuses:

- `Intake`
- `Surveying`
- `Ready`
- `Realizing`
- `Proof Pending`
- `Blocked`
- `Parked`
- `Closed`

Recommended mapping from repo-side queue state:

| Repo-side signal | ClickUp status |
| --- | --- |
| new idea or unframed issue | `Intake` |
| survey in progress | `Surveying` |
| canonical doc exists, work not started | `Ready` |
| execution or doc-backed work in progress | `Realizing` |
| code/doc landed, proof or rerun still needed | `Proof Pending` |
| `status = blocked` or dependency stops progress | `Blocked` |
| `queue_role = parked_future_wave` | `Parked` |
| `historical_backing` or fully closed execution lane | `Closed` |

Important rule:

If ClickUp status and canonical repo status disagree, the repo wins. ClickUp should be updated to match the repo, not the other way around.

### 5.4 Custom Fields

Required custom fields:

1. `Canonical Path`
   - text
   - canonical doc in `docs/YYYY-MM-DD/`
2. `Temp Mirror Path`
   - text
   - empty when not applicable
3. `Work Type`
   - dropdown
   - `survey`, `execution`, `proof`, `product`, `debt`, `ops`
4. `Subsystem`
   - dropdown
   - `stage0`, `stage2`, `stage3`, `stage4`, `desktop`, `bridge`, `control-plane`, `ops`, `tests`
5. `Roadmap Rank`
   - number
   - sourced from `docs/temp/queue-state.json` when applicable
6. `Queue Role`
   - dropdown
   - `front_active`, `blocked_holding`, `parked_future_wave`, `historical_backing`, `standalone`
7. `Risk Band`
   - dropdown
   - `P0`, `P1`, `P2`, `P3`, `none`
8. `Verification Mode`
   - multi-select
   - `static`, `pytest`, `live_run`, `canary`, `readback`, `doc_3pass`
9. `Authority Impact`
   - multi-select
   - `db`, `jsonl`, `artifact`, `control_plane_provenance`, `runtime_audit_summary`, `dashboard_snapshot`, `none`

Nice-to-have fields later:

- `Baseline Commit`
- `Target Wave`
- `Proof Run ID`
- `Blocking Topic`

Do not add large narrative free-text fields for technical truth. If the conclusion matters, it belongs in the canonical doc and ClickUp should link to it.

### 5.5 Task Templates

Recommended minimum templates:

- `Survey Task`
  - question
  - scope
  - canonical doc path
  - excluded surfaces
  - expected decision
- `Execution Lane Task`
  - linked execution SSOT
  - roadmap rank
  - affected subsystem
  - authoritative sink impact
  - verification path
- `Proof Wave Task`
  - target lane(s)
  - run shape
  - pass/fail closure rule
  - readback surfaces to inspect

## 6. Repo-to-ClickUp Mapping Rule

### 6.1 One-way truth flow first

Recommended maturity ladder:

1. manual link-only mode
2. one-way sync from repo queue artifacts to ClickUp fields
3. automated comment/status refresh after validation

Do not start with bi-directional sync.

Reason:
- current repo already has canonical queue semantics
- `docs/temp/queue-state.json` already exposes the machine-readable fields ClickUp needs
- bi-directional writeback would create conflict risk before the operating model stabilizes

### 6.2 What should sync first

If automation is added later, sync only these first:

- `topic`
- `canonical_path`
- `temp_path`
- `status`
- `queue_role`
- `roadmap_rank`
- `depends_on`

Source of truth:
- `docs/temp/queue-state.json`
- `docs/temp/execution-roadmap.md`
- canonical execution SSOT docs

### 6.3 What should never sync as field truth

Avoid treating these as ClickUp field truth:

- runtime verdict reason bodies
- final remediation judgment
- proof interpretation details
- wide evidence excerpts
- long operator notes that duplicate canonical docs

Those should stay in repo-side docs, DB, JSONL, or artifacts.

## 7. Recommended Development Direction By Horizon

### 7.1 Horizon A: next 2 weeks

Priority: queue visibility and proof closure

Recommended actions:

1. adopt the ClickUp structure above without changing repo authority
2. seed ClickUp from the current top queue items in `docs/temp/queue-state.json`
3. create one parent epic for the current front proof/closure wave
4. stop opening broad new feature waves until the current front-active closure stack shrinks
5. refresh human navigation docs where repo entrypoints drift from current reality

What this should look like in practice:

- `Stage4 consumer`
- `Stage4 repair`
- `nonwuxia state-lock`
- `Stage3 contract tightening`
- `Stage4 partial fix`

These should appear as clearly ranked active tasks, not as scattered notes.

### 7.2 Horizon B: next 1 to 2 months

Priority: contract normalization and boundary cleanup

Main theme:

Move from "prove the system can be operated" to "reduce how much special handling the operator needs."

Recommended epic groups:

1. `Proof Closure Wave`
   - front queue closure
   - rerun/proof bookkeeping
   - invalid-run handling discipline
2. `Contract Normalization Wave`
   - Stage2/3/4 contract alignment
   - Stage0 handoff normalization
   - shared vocabulary cleanup
3. `Architecture Reduction Wave`
   - owner-surface reduction
   - module boundary cleanup
   - dashboard/readback simplification

### 7.3 Horizon C: next quarter

Priority: productization and operator leverage

Recommended focus:

- one-way repo-to-ClickUp sync
- stronger operator cockpit around `proof_status`, `gate_repair_summary`, `runtime_health`, and `control_plane_provenance`
- release rhythm that reviews queue aging, proof debt, and blocked lanes weekly
- better distinction between `active queue`, `parked future wave`, and `historical backing`

The right product move is not "more screens first." It is "less ambiguity per run."

## 8. Weekly Operating Rhythm

Recommended weekly rhythm:

1. review the canonical roadmap first
2. refresh ClickUp ranks and statuses from repo-side queue artifacts
3. pick one proof/closure target and one architecture target
4. avoid mixing more than one broad feature wave into the same week
5. archive or park stale tasks aggressively

Recommended weekly review questions:

- which active tasks are truly front-active versus only historically important?
- which tasks are waiting on proof rather than code?
- which docs still carry meaning that ClickUp does not need to duplicate?
- did any human-facing entry doc drift from the actual codebase path?

## 9. Immediate Setup Checklist

Recommended first setup steps:

1. create the `Geuldobi System` Space
2. create the six lists from this note
3. add the required custom fields
4. seed the top `10` roadmap-ranked tasks from `docs/temp/queue-state.json`
5. mark `parked_future_wave` items as `Parked`
6. move `historical_backing` items out of the main active view
7. add the canonical doc path to every seeded task
8. create three epics:
   - `Proof Closure Wave`
   - `Contract Normalization Wave`
   - `Architecture Reduction Wave`
9. run with manual updates first for one to two weeks before discussing sync automation

## 10. Bottom Line

The next structured evolution for Geuldobi is:

- keep repo docs and runtime sinks as SSOT
- use ClickUp as the operator-visible planning and execution layer
- prioritize queue reduction and proof closure before broad new feature expansion
- then use the cleared queue to drive contract cleanup, owner-surface reduction, and productization

The system is mature enough that ClickUp can help a lot.

The system is not yet in a state where ClickUp should be allowed to define technical truth.

## 11. 3-Pass Audit Record

Pass 1. Structure and scope:
- document type matches the request as an operating note
- scope is explicit
- included and excluded surfaces are clear
- canonical save path is explicit

Pass 2. Evidence and consistency:
- conclusions are bounded to current repo docs, queue artifacts, and control-plane contracts
- queue claims are aligned with `docs/temp/queue-state.json`
- authority/companion split claims are aligned with `modules/api/control_plane_contract.py`
- product/readback claims are aligned with `modules/api/bridge_server.py`

Pass 3. Execution and readability:
- the note gives a concrete ClickUp operating model
- the note includes a near-term, mid-term, and quarterly direction
- the note ends in an immediate setup checklist instead of abstract advice only

Confidence:
- estimated confidence `96%`
