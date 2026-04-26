# Frontier Lag Clean 5-Arc — Lane D Continuity Bridge Design

Date: 2026-04-26
Track: system order / read-only design
Lane: D — Continuity Bridge Design
Status: design draft, embedded 3-pass mini audit
Confidence: 95%
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-lane-d-continuity-bridge-design.md`
Order Pack: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md` §9
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
- `?? projects/0_골든카나리아/`

## Scope

Design a stage-agnostic **continuity bridge packet** that runs between upstream
and downstream pipeline stages (S2→S3, S3→S4) so that downstream candidate
contradictions like `Blueprint=2006-01-01` vs `Arc=2006-01-03` are surfaced as
adjudicable proposals **before** ten retries are wasted.

In-scope:
- Packet field contract (16 minimum fields per order pack §9).
- Where the packet lives (DB table vs JSON envelope vs both).
- Director adjudication insertion point.
- How the packet integrates with `session_memory_envelope` without replacing it.
- Worked example for the Stage3 ep4 Jan1 vs Jan3 case.

Out-of-scope:
- Code patches, migrations, or schema deployment. This document is read-only
  design surface only.
- Auto-skip / auto-quarantine HIL policy (Lane E owns harness policy).
- Failure forensics for the existing run (Lane A owns the trace).
- Whether session memory and context cache are actually applied today
  (Lane B owns that audit).

## Evidence

Authoritative source surfaces consulted (file:line anchors verified against
the current workspace, not subagent paraphrase):

DB schema surfaces — `modules/core/db_bootstrap_runtime.py`:

- `stage_attempts` CREATE — `db_bootstrap_runtime.py:514`
  - `advisory_flags TEXT` column at `db_bootstrap_runtime.py:529`
- `director_selections` CREATE — `db_bootstrap_runtime.py:328`
  - `advisory_warnings TEXT` ALTER added later (subagent-A reported line 351)
  - `downstream_override_applied INTEGER` migration (subagent-A reported line 374)
- `context_cache_attempts` CREATE — `db_bootstrap_runtime.py:482`
- `canonical_facts` CREATE — `db_bootstrap_runtime.py:773`
- `timeline_entries` CREATE — `db_bootstrap_runtime.py:785`

Existing envelope contract — `modules/core/session_memory_envelope.py`:

- `SESSION_MEMORY_ENVELOPE_VERSION = "session-memory-envelope-v1"` at line 6.
- Envelope already carries `truth_pins`, `truth_pin_items`, `carryover_refs`,
  `conflict_contract`, `scope_authority`, `repair_contract`, `fix_pack` — see
  `session_memory_envelope.py:120-193`.
- These fields are populated **post-verdict** as advisory telemetry; they do
  not currently gate Director judgment.

HIL stop boundary — `main_a.py`:

- Stage3 failure → operator skip/stop prompt at `main_a.py:4184-4208`
  (verified by direct read; matches post-run audit).
- `prompt_id="frontier_lag_stage3_skip_choice"`; default = `2` (stop).
- `stop_reason: "stage3_user_abort"` when operator picks default.

Run evidence (from `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`):

- Terminal failed Stage3 attempt key: `s3:ep4:arc1:a10:20260426_171126`.
- Director-selected candidate scored 95 with `PASS_WITH_FIX`, but downstream
  binding/prevalidation surface ended `FAILED`.
- Persisted contradiction: Blueprint timeline surface `2006년 1월 1일` while
  Arc state required `2006년 1월 3일`.
- Terminal failed attempt has blank `artifact_path` and blank `content_hash`
  (no diagnostic snapshot).

Subagent reports (cross-verified for the anchors above):

- Lane-D Subagent A — DB schema/telemetry surfaces.
- Lane-D Subagent B — Director-authority workflow surfaces.

Where the two subagent reports describe code regions I did not personally
re-read, I label the claim as **subagent-evidence** rather than verified
evidence and treat the surrounding inference as design inference.

## Findings

### F1. Bridge surface does not exist today

There is no surface that compares an upstream candidate field (e.g. Blueprint
`time_flow.start_date`) against a downstream authority field (e.g. Arc state
`expected_start_date`) **before** the downstream stage runs Director
ensemble. Subagent B reports that
`DirectorContinuityValidator.check_blueprint_continuity_with_cache` is
Python-deterministic but only flags location discontinuity, not timeline
authority drift.

### F2. The current authority chain is correct but late

- Director (LLM) owns narrative verdict.
- Python routes after the verdict.
- HIL only fires after Stage3 attempt budget is exhausted.

The result is that ten attempts are spent before the operator sees the
contradiction. The bridge does not need to take authority from Director or
HIL; it needs to surface the contradiction earlier so Director adjudicates
once instead of ten times.

### F3. session_memory_envelope is the right downstream sink, not the right upstream proposer

`session_memory_envelope` already carries `truth_pins`, `conflict_contract`,
`carryover_refs` — but these are **populated after** a Stage4 attempt closes
and are read by the next attempt as advisory hints. The bridge packet is
**produced earlier** (between stages, before the downstream stage opens its
first attempt) and Director-adjudicated **before** the candidate enters the
ensemble.

The bridge packet should therefore feed **into** the envelope's
`conflict_contract` / `truth_pin_items` channels, not duplicate them.

### F4. Existing "proposed vs applied" patterns already exist

Subagent A surfaced these anchors:

- `FactCommitProposals` with explicit `"authority_status":
  "proposed_only_requires_director_fact_commit"` —
  `stage4_post_pass_runtime.py:1032` (subagent-evidence).
- `cross_stage_authority_packet.py` extracts numeric carryover entries
  (subagent-evidence).
- `_build_capital_continuity_packet` in `blueprint_constraint_compiler.py`
  (subagent-evidence).

The bridge packet should follow the same `proposed_only_requires_director`
pattern these surfaces already establish.

### F5. Arc text files are an authority surface that has no pre-write gate

Subagent A reports that `projects/<project>/plans/arcs/arc_NNN.txt` are
treated as canonical source of truth, written via
`_save_arc_payload_collection` in `db_manager.py` without a Director-gated
pre-write step (subagent-evidence). The bridge does **not** propose to gate
Arc writes themselves; it proposes to detect when a downstream Blueprint
disagrees with an existing Arc authority value, and to route that
disagreement to Director before the downstream attempt is committed.

This finding matters because it bounds the bridge's scope: the bridge
adjudicates **candidate-vs-authority contradictions**, not **authority
mutation requests**. Authority mutation remains owned by Director (LLM)
through existing canon-edit flows.

## Risks

| ID | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| R1 | Python decides which side of the contradiction is right | High | `director_verdict` is the only authoritative field. Python only computes `observed_conflict` and proposes `allowed_fix_scope` options. |
| R2 | Bridge silently rewrites Arc / Bible / factsheet | High | `applied_status` requires a Director verdict row before any downstream applier mutates anything. Python writes only the proposal, never the canon. |
| R3 | Bridge becomes a back door around Director | High | Bridge inserts an additional adjudication request; it never replaces or short-circuits Director ensemble. If Director rejects the bridge, downstream still runs the ordinary verdict path. |
| R4 | Bridge proposals accumulate as advisory noise | Medium | Bridge rows are scoped to `(work_id, arc_num, ep_num, source_stage, target_stage)` and de-duplicated by `source_hashes`. Stale advisory entries are read-only history, not pending work. |
| R5 | Bridge widens fix scope beyond candidate intent | Medium | `allowed_fix_scope` is restricted to `candidate_only` and `escalate_to_human`. Both `authority_only` and `both_with_director_approval` are explicitly rejected because they let Python or the bridge widen scope without Director language-level authority. |
| R6 | Bridge masks real quality failures by adjudicating around them | Medium | Bridge only fires when `observed_conflict` matches a structured contract type (e.g. `timeline_date_authority_drift`). Quality, scoring, and contradiction-firewall logic in Director ensemble are unchanged. |
| R7 | Bridge interacts badly with provider context cache | Low | Bridge writes are DB-only; cache lineage stays advisory. Bridge does not assume cached prompts are authoritative truth. |
| R8 | Bridge proposals leak across runs / projects | Low | Every row carries `work_id` / `project_id`; queries scope by project; archived runs do not leak into new runs. |

## Recommendation

### R-1. Storage: hybrid (dedicated DB table + envelope reference)

The bridge packet lives in a new dedicated DB table
`continuity_bridge_proposals`. The packet is **referenced by id** from inside
`stage_attempts.advisory_flags` and from inside the existing
`session_memory_envelope` so that downstream consumers can resolve the bridge
verdict without duplicating the packet body.

Reasons:

- A dedicated table is append-only, indexable, and decouples bridge audit from
  per-attempt churn (subagent-A recommended this shape).
- A pure JSON-in-`advisory_flags` design buries the packet inside per-attempt
  rows and makes cross-attempt queries (`how often did the same contradiction
  fire?`) hard.
- A pure table design without an envelope reference loses the link between a
  given attempt and the bridge it consulted.
- Pin both: table for canonical row + envelope reference for in-flight
  resume / cache linkage. This matches the existing
  `proposed_only_requires_director_fact_commit` pattern surfaced by
  subagent A.

### R-2. Packet field contract (minimum)

The packet stores **observation + proposal + verdict + application** in one
row. Order pack §9 listed sixteen minimum fields; the contract below covers
all sixteen with explicit types and authority semantics.

| Field | Type | Authority owner | Notes |
| --- | --- | --- | --- |
| `bridge_id` | TEXT (uuid) | Python (allocator) | Stable id; safe to reference from envelopes and logs. |
| `source_stage` | INTEGER | Python | 2 or 3. Upstream stage producing the candidate. |
| `target_stage` | INTEGER | Python | 3 or 4. Downstream stage that would consume it. |
| `work_id` | TEXT | Python | Project / work scoping. |
| `project_id` | TEXT | Python | Same as `work_id` in current single-project layout, kept separate for future multi-project tenancy. |
| `arc_num` | INTEGER | Python | Arc index from the upstream stage. |
| `ep_num` | INTEGER | Python | Episode index from the upstream stage. |
| `authority_source` | TEXT (enum) | Python (proposes), Director (confirms) | One of `arc_state`, `episode_bible`, `factsheet`, `timeline_entries`. The bridge does not declare which side is canonically authoritative; Python tags **what surface the authority value was read from**. |
| `observed_downstream_candidate` | JSON | Python | Structured snapshot of the candidate field (e.g. `{"field": "time_flow.start_date", "value": "2006-01-01", "candidate_artifact_path": "...", "candidate_hash": "..."}`). |
| `observed_conflict` | JSON | Python | Structured contradiction (e.g. `{"contract": "timeline_date_authority_drift", "magnitude_days": 2, "authority_value": "2006-01-03"}`). |
| `proposed_bridge` | JSON | Python | Mechanical translation of the contradiction into a fix proposal. Python may **propose** (`"rewrite_candidate_to": "2006-01-03"`) but must not **apply**. |
| `allowed_fix_scope` | JSON list | Python (proposes), Director (selects) | Restricted enum: `candidate_only`, `escalate_to_human`. Other values explicitly disallowed. |
| `director_verdict` | TEXT (enum) | **Director (LLM)** | One of `APPROVE`, `REJECT`, `MODIFY`, `ESCALATE`, NULL while pending. Bridge only becomes actionable when this is set. |
| `director_reason` | TEXT | Director (LLM) | Free-form rationale; preserved without truncation per workspace DB policy. |
| `applied_status` | TEXT (enum) | Python (writes), Director (gates) | One of `pending`, `applied`, `rejected`, `escalated`, `superseded`. Python flips `pending → applied` only after `director_verdict == APPROVE`. |
| `applied_artifact_key` | TEXT | Python | When Director approves, this is the resulting candidate artifact key (path + hash) so downstream can resolve to the post-bridge candidate. NULL when not applied. |
| `created_at` | TEXT (ISO timestamp) | Python | Set on insert. |
| `source_hashes` | JSON | Python | `{"candidate_hash": "...", "authority_hash": "...", "upstream_attempt_key": "..."}`. Used for de-duplication and replay safety. |

Beyond the sixteen required fields, two operational fields should be present:

- `verdict_at` (TEXT timestamp, set when Director writes verdict).
- `applied_at` (TEXT timestamp, set when applier transitions `pending → applied`).

Indexes:

- `(work_id, arc_num, ep_num, source_stage, target_stage)` — locate active
  bridges for a given handoff.
- `(applied_status)` — find pending proposals for adjudication queue.
- `(director_verdict)` — find approved/rejected bridges for post-mortem.

### R-3. Where the packet lives in the codebase

- Schema: new CREATE TABLE in `modules/core/db_bootstrap_runtime.py` next to
  the existing CREATE blocks.
- Manager: new accessor methods in `modules/core/db_manager.py` exposing
  `propose_continuity_bridge`, `record_continuity_bridge_verdict`,
  `apply_continuity_bridge`, `query_pending_bridges`. Each method is single
  responsibility, append-only-where-possible.
- JSON payload reference: extend `stage_attempts.advisory_flags` with a new
  key `continuity_bridge_refs: [bridge_id, ...]`. The full packet body lives
  in the DB table; only the id list goes in the JSON payload to avoid
  duplicating the body across attempts.
- Envelope linkage: `session_memory_envelope` consumes `bridge_id` references
  through its existing `conflict_contract` / `truth_pin_items` channels (see
  R-5 below) — no new envelope key is required.

### R-4. Director adjudication insertion point

Per Subagent B, the right Director surface is an extended
`DirectorContinuityValidator` path. The design separates two responsibilities:

1. **Detection** (Python only). Inserted as a new prevalidation step **after**
   upstream stage finalization and **before** the downstream stage opens an
   attempt. For S2→S3 detection runs after `Stage 2` arc finalization;
   for S3→S4 detection runs after `Stage 3` blueprint finalization. Python
   reads candidate fields and authority fields, computes structured
   `observed_conflict`, and inserts a bridge row with `director_verdict =
   NULL` and `applied_status = pending`.

2. **Adjudication** (Director / LLM). The downstream stage's existing
   ensemble entry (e.g. Director ensemble for Stage 4, Director continuity
   for Stage 3 blueprints) checks for pending bridges scoped to its
   `(work_id, arc_num, ep_num, source_stage, target_stage)` slot **before**
   running the candidate through quality gates. Director receives the bridge
   packet as an LLM-facing prompt fragment, decides `APPROVE` /
   `REJECT` / `MODIFY` / `ESCALATE`, and writes `director_verdict` +
   `director_reason` back into the row.

This deliberately **does not** introduce a new Python decision authority. The
bridge only becomes actionable when an LLM-judged surface stamps a verdict.

### R-5. How the bridge interacts with `session_memory_envelope`

The bridge does **not** replace `session_memory_envelope`. They are layered:

- `session_memory_envelope` continues to be written **after** each Stage4
  attempt closes (see `build_stage4_session_memory_envelope` in
  `session_memory_envelope.py:92`). It is the per-attempt telemetry record.
- The bridge packet is written **between stages**, before the downstream
  stage's first attempt. It is the cross-stage proposal record.
- When the downstream stage opens a new attempt, it reads pending bridge rows
  for its slot. Approved bridges are surfaced into the prompt's
  `truth_pin_items` channel (existing field, no schema change) by reusing the
  `_merge_truth_pin_items` helper in
  `session_memory_envelope.py:56-79`. The bridge contributes a new
  truth-pin entry with `pin_key = "continuity_bridge:" + bridge_id` so the
  envelope can de-duplicate against other pin sources.
- The envelope's `conflict_contract` channel records the **applied** bridge
  decision so the next attempt's envelope contains a back-reference to the
  bridge id, the Director verdict, and the `applied_artifact_key` — letting
  retries resume cleanly without re-detecting the same contradiction.

In short: the bridge is the **upstream proposer**, the envelope is the
**downstream telemetry surface**. Neither replaces the other.

### R-6. Worked example — Stage3 ep4 Jan1 vs Jan3

Setup (from the post-run audit):

- Upstream artifact: `projects/0_골든카나리아/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`.
- Authority surface: `projects/0_골든카나리아/plans/arcs/arc_002.txt`, which
  records the canonical timeline including the Arc requirement that ep4
  begins on `2006년 1월 3일`.
- Downstream candidate: Stage3 Blueprint produced for ep4 surfaces
  `time_flow.start_date = "2006년 1월 1일"`.

Bridge lifecycle in the proposed design:

1. **Detect.** After Stage3 finalizes the ep4 Blueprint candidate (and
   before Stage4 opens), Python prevalidator reads:
   - candidate field: `time_flow.start_date = "2006년 1월 1일"` from the
     Blueprint payload.
   - authority field: `arc_state.expected_start_date["ep4"] = "2006년 1월 3일"`
     from `plans/arcs/arc_002.txt` parsed via `db_manager.load_arc_payloads`.
   - magnitude: 2 days drift. Contract: `timeline_date_authority_drift`.

2. **Propose.** Python inserts:

   ```text
   bridge_id = "cbp-2026-04-26T17:11:26-arc1-ep4-s3s4-001"
   source_stage = 3
   target_stage = 4
   work_id = "0_골든카나리아"
   project_id = "0_골든카나리아"
   arc_num = 1
   ep_num = 4
   authority_source = "arc_state"
   observed_downstream_candidate = {
     "field": "time_flow.start_date",
     "value": "2006년 1월 1일",
     "candidate_artifact_path": "logs/artifacts/stage3/arc_001/ep_004/attempt_10/final_blueprint__primary.json",
     "candidate_hash": "<sha256 placeholder>"
   }
   observed_conflict = {
     "contract": "timeline_date_authority_drift",
     "authority_value": "2006년 1월 3일",
     "candidate_value": "2006년 1월 1일",
     "magnitude_days": 2
   }
   proposed_bridge = {
     "rewrite_candidate_to": "2006년 1월 3일",
     "rewrite_field": "time_flow.start_date"
   }
   allowed_fix_scope = ["candidate_only", "escalate_to_human"]
   director_verdict = NULL
   director_reason = NULL
   applied_status = "pending"
   applied_artifact_key = NULL
   created_at = "2026-04-26T17:11:26Z"
   source_hashes = {
     "candidate_hash": "<sha256>",
     "authority_hash": "<sha256 of arc_002.txt>",
     "upstream_attempt_key": "s3:ep4:arc1:a10:20260426_171126"
   }
   ```

3. **Adjudicate.** Stage4's Director-continuity surface (extended per
   Subagent-B recommendation in `director_continuity.py`) detects the
   pending bridge for slot `(work_id="0_골든카나리아", arc_num=1, ep_num=4,
   source_stage=3, target_stage=4)`. The bridge body is rendered into the
   Director prompt. Director adjudicates and writes back, e.g.

   ```text
   director_verdict = "APPROVE"
   director_reason = "Arc 캐논 일정과의 정합 우선. Candidate timeline은 1/3로 정렬."
   verdict_at = "2026-04-26T17:11:40Z"
   ```

   If Director picked `REJECT`, the bridge is closed and the downstream
   stage runs ordinary retry / HIL paths. If Director picked `ESCALATE`,
   Lane E HIL policy decides the next operator action — the bridge does not
   silently auto-skip.

4. **Apply.** Python applier reads the approved bridge and constructs a
   bridge-derived candidate that respects `allowed_fix_scope = candidate_only`
   — i.e. Python rewrites only the candidate Blueprint field, never the Arc
   authority surface, never the factsheet, never the Bible. The applier
   writes:

   ```text
   applied_status = "applied"
   applied_artifact_key = "logs/artifacts/stage3/arc_001/ep_004/attempt_11_bridge/final_blueprint__primary.json"
   applied_at = "2026-04-26T17:11:42Z"
   ```

   The downstream Stage4 attempt then proceeds against the bridge-applied
   candidate. The next attempt's `session_memory_envelope` contains
   `conflict_contract.continuity_bridge_refs = ["cbp-2026-04-26T17:11:26-arc1-ep4-s3s4-001"]`
   and a matching `truth_pin_items` entry, so retries do not re-detect the
   same contradiction.

5. **Post-mortem.** If a future Stage3 attempt for the same ep regenerates
   `2006년 1월 1일`, the bridge row's `source_hashes` collide on
   `(work_id, arc_num, ep_num, contract, authority_value)` and the new
   proposal is marked `superseded` rather than duplicated; a fresh row may
   still be inserted if `magnitude` / `authority_hash` changes, so audit
   replay stays accurate.

This worked example shows the bridge intercepting the Jan1 vs Jan3 conflict
**once** under Director authority, instead of letting Stage3 churn through
retry attempts 1..10 and then handing operator a stop choice with no
diagnostic trail.

### R-7. What the bridge explicitly does NOT do

To keep the design within governance §3 of the order pack:

- It does not auto-edit Arc text files, Bible, or factsheet.
- It does not let Python decide which side of a contradiction is canonical.
- It does not bypass Director ensemble or HIL stop policy.
- It does not weaken Stage3 / Stage4 quality gates so a 5-arc run passes.
- It does not assume provider context cache or session memory carries
  authoritative narrative truth.
- It does not run for arbitrary "looks suspicious" signals — only structured
  `observed_conflict` contracts matching a registered detector.

## Subagent Cross-Check

Two subagents were spawned per order pack §4 with the read-only design
mandate.

**Subagent A — DB schema / telemetry surfaces** (`Explore`, read-only):

- Confirmed schema anchors at `db_bootstrap_runtime.py:328 / 482 / 514 / 773 / 785`.
- Confirmed `stage_attempts.advisory_flags TEXT` at line 529.
- Recommended the **hybrid** storage shape (dedicated table +
  `advisory_flags` JSON reference). Lane D adopts that recommendation as R-1.
- Surfaced the existing `FactCommitProposals` "proposed_only_requires_director"
  pattern at `stage4_post_pass_runtime.py:1032` (subagent-evidence).
  Lane D adopts this pattern as R-2 / R-7.
- Surfaced `cross_stage_authority_packet` and
  `_build_capital_continuity_packet` as existing carryover packet shapes
  (subagent-evidence). Lane D treats these as siblings of the bridge, not
  duplicates.
- Subagent-A also proposed a slightly different SQL table name and column
  set (`field_name`, `blueprint_value`, `arc_value`, `canonical_value`,
  `confidence`). Lane D **diverges** here: the order pack §9 explicitly
  requires the sixteen named fields including `proposed_bridge`,
  `allowed_fix_scope`, `applied_artifact_key`, `source_hashes`. The Lane D
  contract preserves the sixteen required fields and embeds the
  Subagent-A column intent inside the JSON `observed_conflict` /
  `observed_downstream_candidate` payloads.

**Subagent B — Director adjudication / workflow surfaces** (`Explore`, read-only):

- Confirmed Director ensemble verdict entry at
  `director_ensemble.py:2825-2939` (subagent-evidence).
- Confirmed
  `DirectorContinuityValidator.check_blueprint_continuity_with_cache`
  is Python-deterministic and **does not** validate timeline /
  arc-state authority drift today (subagent-evidence). Lane D treats this
  as the natural extension point for bridge adjudication (R-4).
- Confirmed HIL stop path at `main_a.py:4174-4219` (independently verified
  by parent terminal at `main_a.py:4170-4219`).
- Confirmed `session_memory_envelope` already carries
  `truth_pins`, `conflict_contract`, `carryover_refs` (independently
  verified by parent terminal at `session_memory_envelope.py:120-193`).
- Subagent B also proposed a new fix_scope value
  `both_with_director_approval`. Lane D **rejects** this value (R-5
  risk row, R-2 enum) because it lets the bridge widen scope to
  authority-side mutation without a Director-language-level verdict on
  the authority itself; it is incompatible with §3 governance. Subagent
  B's safer recommendation (`escalate_to_human`) is adopted.

Where the parent terminal independently re-read code, anchors are labeled
as verified evidence; where claims rest on subagent reading only, the text
is labeled "subagent-evidence" so a follow-up reader can re-verify.

## 3-Pass Mini Audit

**Pass 1 — Scope and structure.** PASS.

The document covers the order pack §9 contract: storage location, integration
with `session_memory_envelope`, sixteen-field minimum packet, worked Jan1 vs
Jan3 example. The document is read-only design and does not patch code. The
required sections (`Scope`, `Evidence`, `Findings`, `Risks`, `Recommendation`,
`Subagent Cross-Check`, `3-Pass Mini Audit`) are present.

**Pass 2 — Governance and authority.** PASS.

Cross-checked against AGENTS.md §대원칙:

- Python collects/proposes; Director (LLM) decides. Bridge `director_verdict`
  is owned by an LLM-judged surface; Python only writes proposal +
  `applied_status` transitions gated on the verdict.
- Factsheet / canon edit authority remains LLM-only. Bridge does not mutate
  Arc, Bible, or factsheet — it only mutates the **candidate** under
  `candidate_only` scope, never the authority.
- Director sovereignty preserved. Bridge inserts an additional adjudication
  before downstream ensemble, never replaces or overrides the ensemble.
- Deceased-character rule unaffected (out of bridge scope; bridge does not
  touch character lifecycle).
- DB max-preservation policy honored: bridge stores full `director_reason`
  in TEXT without truncation, preserves `source_hashes` for replay.

**Pass 3 — Evidence and consistency.** PASS.

- Anchors that the parent terminal re-read directly are verified
  (`db_bootstrap_runtime.py:514 / 528 / 482 / 328 / 773 / 785 / 529`,
  `main_a.py:4170-4219`, `session_memory_envelope.py:6 / 56-79 / 92-193`).
- Anchors that rest on subagent reading are explicitly labeled
  "subagent-evidence" so a future reader can re-verify
  (`director_ensemble.py:2825`, `director_continuity.py:860-964`,
  `stage4_post_pass_runtime.py:1032`, `cross_stage_authority_packet.py`,
  `blueprint_constraint_compiler.py`).
- Worked example values match the post-run merge audit (attempt key
  `s3:ep4:arc1:a10:20260426_171126`, score 95, persisted contradiction
  `2006년 1월 1일` vs `2006년 1월 3일`).
- Bridge field contract matches order pack §9 minimum sixteen fields;
  divergences from subagent recommendations are documented in §Subagent
  Cross-Check with rationale.

Estimated confidence: **95%**.

The score is not higher because:

1. Three subagent-evidence anchors (`director_ensemble.py:2825`,
   `director_continuity.py:860`, `stage4_post_pass_runtime.py:1032`) were
   not personally re-read by the parent terminal and could shift line
   numbers in future commits.
2. The exact prompt-rendering shape Director should see for a bridge packet
   is left to implementation review — this design does not freeze the LLM
   prompt format.
3. Headquarters synthesis of all six lane reports has not yet happened, so
   cross-lane coherence with Lane B (memory/cache audit) and Lane F
   (governance audit) is not yet verified.

Per order pack §12, this design **does not** create a `docs/temp/` execution
mirror. Headquarters will synthesize the execution SSOT separately if and
only if the combined six-lane evidence reaches the 95% confidence threshold
and the user opts to implement.
