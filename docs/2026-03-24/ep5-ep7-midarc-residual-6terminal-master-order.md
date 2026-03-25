# EP5-EP7 Mid-Arc Residual 6-Terminal Master Order

Date: 2026-03-24
Status: final (3-pass audited)
Document Type: system-track parallel survey master order
Canonical Path: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
Temp Mirror Path: none
Primary Evidence Run: `projects/0324_00_`
Queue State: `empty at order creation; survey-only document must not create temp queue artifacts`
Reference Docs:
- `docs/2026-03-24/console.txt`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-merge-audit.md`
- `docs/2026-03-24/stage3-blueprint-state-precision-reconciliation-wave-execution-ssot.md`
Primary Evidence Anchors:
- `docs/2026-03-24/console.txt`
- `projects/0324_00_/logs/episode_production.jsonl`
- `projects/0324_00_/project_data.db`
- `projects/0324_00_/logs/quality_metrics.jsonl`
- `projects/0324_00_/logs/runtime_audit.jsonl`
- `projects/0324_00_/logs/session/llm_io.jsonl`
- `projects/0324_00_/logs/session/decisions.jsonl`
- `projects/0324_00_/logs/session/state_changes.jsonl`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/`
- `projects/0324_00_/logs/artifacts/stage4/ep_0005/`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/`
- `projects/0324_00_/logs/artifacts/stage4/ep_0007/`

## 1. Purpose

This is a bounded, survey-only, 6-terminal re-investigation of the remaining mid-arc failures after the closed Stage 3 state-precision wave.

Goal:

- inspect the actual episode 5 to 7 artifacts directly
- reconcile console, JSONL, DB, and artifact truth
- identify where the remaining rescue rounds truly originate
- decide whether the next wave should hit Stage 3 again, Stage 4 only, or a narrower sink/contract seam

This document does not authorize code changes.

## 2. Why Narrow To EP5-EP7

Current live evidence no longer looks like the old EP2/EP3 collapse family.

What remains:

- `ep5`: repeated `post_select_conflict` before PASS
- `ep6`: `director_primary_reject` plus `continuity_firewall` before PASS
- `ep7`: multi-round rescue before PASS in console, while JSONL attempt trace looks thinner than expected

That means the current problem is a narrower mid-arc residual family spanning:

- capital-state continuity
- timeline/location/item carryover
- Stage 3 blueprint truth vs Stage 4 expansion truth
- sink reconciliation:
  - console
  - JSONL
  - DB
  - real artifact bodies

## 3. Hard Constraints

- survey only; no code changes
- inspect real artifact bodies, not just summaries
- inspect DB and JSONL truth, not just console paraphrase
- do not create execution SSOTs
- do not create or modify anything in `docs/temp/`
- do not close anything
- do not overwrite shared/canonical reports from another lane
- weak or mixed claims must be marked `not proven`

## 4. Survey Model

Each lane must classify every meaningful claim as one of:

- `confirmed primary cause`
- `confirmed secondary amplifier`
- `artifact-truth mismatch`
- `sink mismatch`
- `validator-only signal`
- `cleared / not primary`
- `not proven`

Each lane must also answer:

- `Can this lane explain a real EP5-EP7 rescue round by itself: yes/no`
- `Does this lane justify a bounded next execution wave: yes/no`
- `Is the likely owner Stage 3 / Stage 4 / sink-reconciliation / validator / mixed`

## 5. Report Path Rule

All lane outputs must be saved under:

- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/`

Do not write into canonical merge docs from a lane terminal.

## 6. Terminal Plan

| Terminal | Lane | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | `Run Chronology + Sink Reconciliation` | `console.txt`, `episode_production.jsonl`, rescue-round ledger, console vs JSONL mismatch | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t1-run-chronology-and-sinks.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t1-run-chronology-and-sinks-evidence.md` |
| T2 | `DB / Metadata Truth` | `project_data.db`, runtime audit, quality metrics, state_changes, row-level linkage to artifact files | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t2-db-and-metadata-truth.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t2-db-and-metadata-truth-evidence.md` |
| T3 | `Stage3 Blueprint Truth` | EP5/6/7 Stage 3 blueprints, fact-lock/capital-lock effect, where conflict first appears in blueprint authority | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t3-stage3-blueprint-truth.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t3-stage3-blueprint-truth-evidence.md` |
| T4 | `Stage4 Manuscript Expansion` | EP5/6/7 rejected, selected, patched, final manuscripts; what Stage 4 invents or repairs | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t4-stage4-manuscript-expansion.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t4-stage4-manuscript-expansion-evidence.md` |
| T5 | `Validator / Retry / PASS_WITH_FIX Semantics` | `continuity_firewall`, `post_select_conflict`, `PASS_WITH_FIX`, rescue-round semantics and whether the gates are well-targeted | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t5-validator-retry-semantics.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t5-validator-retry-semantics-evidence.md` |
| T6 | `Capital-Time-Item Diff Ledger` | cross-episode ledger for capital, timeline, item/location, from EP4 final truth -> EP5/6/7 blueprint -> Stage4 output | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger.md` | `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger-evidence.md` |

## 7. Lane Questions

### T1. Run Chronology + Sink Reconciliation

- Which exact rounds happened for EP5, EP6, and EP7?
- Does `console.txt` agree with `episode_production.jsonl`?
- If not, which sink is missing attempts, and is that a recording gap or a logic gap?

### T2. DB / Metadata Truth

- Do DB and JSONL agree on selected candidate, verdict chain, and artifact path?
- Are any episode attempts missing from DB while present in console or artifacts?
- Is there any metadata-to-artifact linkage break?

### T3. Stage3 Blueprint Truth

- Do EP5/6/7 blueprints already contain the capital, time, or item-state drift?
- Did the new fact-lock/capital-lock actually narrow the blueprint, or are the conflicts still born in Stage 3?
- For each troubled episode, is the blueprint:
  - hard contradiction
  - loose/ambiguous pressure
  - clean

### T4. Stage4 Manuscript Expansion

- For each troubled episode, what does Stage 4 add beyond the blueprint?
- Which conflicts are pure manuscript invention?
- Which are faithful expansion of already-wrong blueprint authority?

### T5. Validator / Retry / PASS_WITH_FIX Semantics

- Are `post_select_conflict`, `continuity_firewall`, and `director_primary_reject` well-grounded?
- Is `PASS_WITH_FIX` coexisting with later conflict in a sane way or a residual architecture smell?
- Is patch-bias still present in the rescue path?

### T6. Capital-Time-Item Diff Ledger

- Build one compact ledger from EP4 accepted truth through EP7 final truth.
- Track:
  - capital available vs deployed
  - paid expenditure vs remaining capital
  - explicit time anchors
  - item/location anchors
- Which contradiction first becomes undeniable, and at which stage?

## 8. Common Opus Survey Prompt

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/live-run-merge-survey-harness.md
5. docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md
6. docs/2026-03-24/console.txt

Task:
Run your assigned lane only for the EP5-EP7 mid-arc residual survey.

Hard constraints:
- survey only
- no code changes
- no execution SSOT creation
- no docs/temp changes
- do not overwrite shared canonical reports
- findings first
- file/line anchor every meaningful claim
- use artifact truth over console paraphrase when they disagree
- mark weak claims as not proven

Mandatory final lines:
- Dominant seam in this lane: <stage3 / stage4 / sink / validator / mixed / not proven>
- Can this lane explain a real rescue round by itself: yes / no
- Would this lane justify a bounded next execution wave: yes / no
```

## 9. Terminal-Specific Overrides

### T1 Override

- Focus: rescue chronology and sink mismatch only
- required files:
  - `docs/2026-03-24/console.txt`
  - `projects/0324_00_/logs/episode_production.jsonl`
  - `projects/0324_00_/logs/runtime_audit.jsonl`

### T2 Override

- Focus: DB and metadata truth only
- required files:
  - `projects/0324_00_/project_data.db`
  - `projects/0324_00_/logs/quality_metrics.jsonl`
  - `projects/0324_00_/logs/session/state_changes.jsonl`
  - artifact path references emitted by DB/JSONL

### T3 Override

- Focus: EP5/6/7 Stage 3 blueprint truth only
- required files:
  - `projects/0324_00_/logs/artifacts/stage3/ep_0005/`
  - `projects/0324_00_/logs/artifacts/stage3/ep_0006/`
  - `projects/0324_00_/logs/artifacts/stage3/ep_0007/`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`

### T4 Override

- Focus: EP5/6/7 Stage 4 manuscript expansion only
- required files:
  - `projects/0324_00_/logs/artifacts/stage4/ep_0005/`
  - `projects/0324_00_/logs/artifacts/stage4/ep_0006/`
  - `projects/0324_00_/logs/artifacts/stage4/ep_0007/`

### T5 Override

- Focus: validator and retry semantics only
- required files:
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_pass_runtime.py`
  - `modules/validation/continuity_validator.py`
  - `modules/validation/validation_orchestrator.py`
  - relevant console/JSONL lines for EP5/6/7

### T6 Override

- Focus: cross-episode capital/time/item ledger only
- required files:
  - EP4 accepted manuscript
  - EP5/6/7 Stage 3 blueprints
  - EP5/6/7 Stage 4 selected/rejected/patched/final manuscripts
  - any DB/JSONL rows needed only to anchor the ledger

## 10. Dispatch Lines

- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 1번 터미널`
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 2번 터미널`
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 3번 터미널`
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 4번 터미널`
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 5번 터미널`
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md + 넌 6번 터미널`

## 11. Expected Merge Outcome

Codex should be able to merge these six lane reports into one of:

- `Stage 3 primary, Stage 4 secondary`
- `Stage 4 primary, Stage 3 secondary`
- `sink-reconciliation issue first`
- `mixed but separable two-wave outcome`

This master order is successful if the next bounded culprit family becomes narrower than the current generic label `mid-arc continuity residual`.
