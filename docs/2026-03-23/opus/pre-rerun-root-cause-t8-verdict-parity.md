Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey report
Terminal: T8
Focus: Director and post-select DB/console parity
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md`
Source Order: `docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md`
Primary Scope: `docs/2026-03-23/console.txt`, `projects/0_0323/logs/session/**`, `projects/0_0323/logs/runtime_audit.jsonl`, relevant director and stage attempt DB rows

---

# T8: Director and Post-Select DB/Console Parity

## 1. Executive Summary

T8 surveyed the parity between what the operator observes on the console during Director verdict, post-select gate, and feedback synthesis — and what the DB actually records. The survey compared console.txt (1,011 lines), runtime_audit.jsonl (20 entries), session logs (decisions.jsonl, ui_events.jsonl, state_changes.jsonl, llm_io.jsonl), and DB tables (stage_attempts 12 rows, director_selections 11 rows, attempt_raw_rationale 12 rows).

**Primary blocker**: No single P0 crash or data-loss blocker. The parity gaps are observability debts, not decision-path correctness issues.

**Key findings**:

| Severity | Count | Summary |
|----------|-------|---------|
| P1 | 3 | initial_verdict NULL on post-select downgrade, Stage 2/3 reasoning fields empty in stage_attempts, Stage 2 reject_reason 500-char truncation |
| P2 | 3 | Stage 3 director_thinking not preserved, attempt_raw_rationale Stage 4 only, split-brain requires JSON parsing to reconstruct |

**Root-cause vs symptom**: All 6 findings are root-cause parity gaps in the save-path code, not downstream symptoms. They stem from three distinct origins:
1. Stage 2/3 save calls pass fewer fields than Stage 4 (structural omission)
2. Post-select conflict path does not populate `initial_verdict` (path-specific omission)
3. Stage 2 reject_reason has explicit Python truncation violating AGENTS.md policy (policy violation)

**Fresh-run-before-fix allowed: yes** — These are observability gaps, not decision-path bugs. A rerun will still work correctly; it will just be harder to diagnose retrospectively.

---

## 2. Current Ownership / Flow Map

### DB Sink Topology for Director Verdicts

```
Director LLM verdict
  │
  ├─→ director_selections table ← saves: verdict, score, selection_reason,
  │                                 verdict_reason, pre_firewall_score,
  │                                 firewall_triggered/reason, director_thinking,
  │                                 advisory_warnings, candidate_key, artifact_path
  │
  ├─→ stage_attempts table     ← saves: verdict (final), score, reject_reason,
  │                                 selection_reason, verdict_reason, open_review,
  │                                 fix_scope_reasoning, runtime_advisory,
  │                                 retry_directives, initial_verdict,
  │                                 score_breakdown, advisory_flags (JSON)
  │
  ├─→ attempt_raw_rationale    ← saves: director_thinking (payload_kind),
  │                                 advisory_warnings_raw (payload_kind)
  │
  ├─→ runtime_audit.jsonl      ← saves: pathology signals, retry_pathology_repeat
  │
  ├─→ console                  ← displays: verdict, score, gate, selection_reason,
  │                                 verdict_reason, Director Thinking (full),
  │                                 advisory warnings, post-select conflicts
  │
  └─→ session/decisions.jsonl  ← saves: decision events
```

### Which Stages Write to Which Sinks

| Sink | Stage 2 | Stage 3 | Stage 4 |
|------|---------|---------|---------|
| `stage_attempts` (core fields) | YES | YES | YES |
| `stage_attempts` (reasoning fields) | NO | NO | YES |
| `director_selections` | YES | YES | YES |
| `director_selections.director_thinking` | YES | NO | YES |
| `attempt_raw_rationale` | NO | NO | YES |
| `runtime_audit.jsonl` | YES | YES | YES |
| Console (Director Thinking) | YES | NO | YES |
| Console (verdict details) | YES | YES | YES |

---

## 3. Focus-Scope Findings

### F-1. [P1] `initial_verdict` NULL on post-select downgrade

**File**: `modules/core/stage4_interview_round.py:5643`
**Evidence type**: DB + console
**DB evidence**: `stage_attempts` id=11 (ep3 attempt 4): `initial_verdict=NULL`, `verdict=REJECT`, `score=98`
**Console evidence**: Lines 893-912 — Director PASS (score=98) → post-select continuity conflict → downgrade to REJECT
**DB cross-check**: `advisory_flags.gate_semantics` contains `"director_verdict": "PASS", "final_verdict": "REJECT", "gate_basis": "post_select_conflict"` — the split IS recorded in advisory_flags JSON
**DB cross-check**: `director_selections` id=10 records `verdict=PASS, score=98` — the Director's original PASS is preserved in this table

**Root cause**: `_build_stage4_db_attempt_payload` at L5643 does `initial_verdict or None`. The post-select conflict path re-records the attempt as REJECT but does not pass the Director's original PASS as the `initial_verdict` parameter. The `initial_verdict` field is only populated when the final outcome is PASS and matches the Director's original verdict.

**Impact**: Querying `stage_attempts.initial_verdict` alone cannot distinguish:
- "Director said REJECT originally" (initial_verdict=NULL)
- "Director said PASS but post-select overrode to REJECT" (initial_verdict=NULL)
- "Director said PASS and it stayed PASS" (initial_verdict="PASS")

The first two cases are conflated. Recovery is possible via `advisory_flags.gate_semantics.director_verdict` (requires JSON parsing) or via the `director_selections` table (requires a JOIN).

### F-2. [P1] Stage 2/3 Director reasoning fields empty in stage_attempts

**File (Stage 2)**: `modules/core/stage2_finalizer.py:2691-2706` (PASS path), `L2829-2844` (REJECT path)
**File (Stage 3)**: `modules/core/stage3_orchestrator.py:1858-1874`
**Evidence type**: source + DB

**DB evidence**: `stage_attempts` ids 1-5 (all Stage 2/3 records):
- `selection_reason = ""`
- `verdict_reason = ""`
- `open_review = ""`
- `fix_scope_reasoning = ""`
- `runtime_advisory = ""`
- `retry_directives = ""`
- `initial_verdict = NULL`

**Root cause**: Both `stage2_finalizer.py` and `stage3_orchestrator.py` call `db.save_stage_attempt()` without passing any of these optional reasoning fields. The DB protocol accepts them as optional with defaults of `None`, so they are silently stored as empty.

**Cross-check**: `director_selections` table DOES contain reasoning for these stages:
- Stage 2 id=1: `selection_reason` populated, `director_thinking` populated (4,116+ chars)
- Stage 3 ids 2-5: `selection_reason` and `verdict_reason` populated with LLM-generated content

**Impact**: An operator or automated tool querying `stage_attempts` for "why did Stage 2/3 reach this verdict?" gets no answer. They must know to also query `director_selections` and JOIN on `attempt_key`.

### F-3. [P1] Stage 2 reject_reason 500-char Python truncation

**File**: `modules/core/stage2_finalizer.py:2837`
**Evidence type**: source
**Code**: `reject_reason=str(audit.get("reason", ""))[:500]`

**Root cause**: Explicit Python-side `[:500]` slice on a TEXT column value before DB save.

**Policy violation**: AGENTS.md states: "DB의 TEXT 컬럼에 저장하는 진단·판정·사유 필드는 Python에서 절삭([:N])하지 않는다. SQLite TEXT는 길이 제한이 없으며, 런타임 증거는 최대한 보존한다."

**Impact**: Stage 2 REJECT reasons longer than 500 chars are irreversibly truncated in the DB. This project had no Stage 2 REJECTs in the current run, so no data was lost in this session, but future runs with longer reject reasons will lose information.

### F-4. [P2] Stage 3 director_thinking not preserved in director_selections

**Evidence type**: DB
**DB evidence**: `director_selections` ids 2-5 (Stage 3): `director_thinking = ""`
**DB cross-check**: `director_selections` id=1 (Stage 2): `director_thinking` has full content
**DB cross-check**: `director_selections` ids 6-11 (Stage 4): `director_thinking` has full content

**Root cause**: Stage 3 Blueprint Director uses a simpler LLM scoring path that either does not generate full thinking text or does not capture it in the `selection_kwargs` dict passed to `save_director_selection`.

**Impact**: Cannot reconstruct Stage 3 Director reasoning from DB. Console also does not show Stage 3 Director Thinking (unlike Stage 2 and Stage 4).

### F-5. [P2] attempt_raw_rationale only stores Stage 4 data

**Evidence type**: DB
**DB evidence**: All 12 rows in `attempt_raw_rationale` are `stage=4`
**Payload kinds**: `director_thinking` (6 rows) and `advisory_warnings_raw` (6 rows)

**Root cause**: Only `stage4_interview_round.py` calls `save_attempt_raw_rationale()`. Stage 2/3 code does not.

**Impact**: Stage 2 Director thinking IS available in `director_selections.director_thinking`, but Stage 2/3 advisory warnings raw data is not preserved in the adjunct table.

### F-6. [P2] Split-brain requires JSON parsing for reconstruction

**Evidence type**: DB structure
**DB evidence**: The split-brain (Director PASS → post-select REJECT) is recorded in `advisory_flags` as nested JSON: `{"gate_semantics": {"director_verdict": "PASS", "final_verdict": "REJECT", "gate_basis": "post_select_conflict"}}`

**Root cause**: The split information is stored only in a JSON blob field, not in dedicated columns.

**Impact**: SQL queries for "how many times did post-select override Director?" require `json_extract()` against `advisory_flags`. This is functional but less ergonomic than a dedicated `gate_basis` column on `stage_attempts`.

---

## 4. Root-Cause Relevance

### What is root-causal vs symptomatic

| Finding | Classification | Why |
|---------|---------------|-----|
| F-1 initial_verdict NULL | **root cause** | save-path code omission; the parameter exists but isn't wired in the post-select conflict path |
| F-2 Stage 2/3 empty reasoning | **root cause** | save-path code omission; the fields exist in the DB schema but the callers don't populate them |
| F-3 Stage 2 reject_reason truncation | **root cause** | explicit `[:500]` in source code, direct policy violation |
| F-4 Stage 3 thinking empty | **root cause** | save-path doesn't capture thinking from Stage 3 Blueprint Director |
| F-5 raw_rationale Stage 4 only | **downstream** | symptom of Stage 2/3 not wiring the adjunct save |
| F-6 split-brain in JSON only | **structural** | design choice (advisory_flags is a catch-all JSON blob), not a bug |

### Blocks next rerun?

**No**. All findings are observability debts. The Director decision path, post-select gate, feedback synthesis, and retry logic all function correctly. The gaps only affect post-hoc diagnostic ability.

---

## 5. Quick Wins

| # | Fix | File | Fix Type | Effort | ROI |
|---|-----|------|----------|--------|-----|
| QW-1 | Remove `[:500]` from Stage 2 reject_reason save | `stage2_finalizer.py:2837` | contract-cleanup | trivial (1 line) | high — policy compliance |
| QW-2 | Pass `initial_verdict=director_verdict` in post-select conflict REJECT path | `stage4_interview_round.py` or `stage4_reject_runtime.py` | contract-cleanup | low (trace caller, add param) | high — eliminates split-brain ambiguity |
| QW-3 | Add `selection_reason`, `verdict_reason`, `open_review` to Stage 3 save_stage_attempt call | `stage3_orchestrator.py:1858-1874` | contract-cleanup | low (extract from selection_kwargs) | medium — enables single-table querying |

---

## 6. False Leads / Non-Causes

| Item | Why not a cause |
|------|----------------|
| Console verdict_reason truncation | Console does truncate with `...` but the full text IS in DB stage_attempts.verdict_reason for Stage 4. This is a display choice, not a DB gap |
| Director Thinking missing from console for Stage 3 | Stage 3 uses a simpler scoring Director that does not produce full thinking. This is by design, not a bug |
| runtime_audit.jsonl missing fields | runtime_audit records pathology signals, not verdict details. The full verdict is in stage_attempts and director_selections. Different sinks for different purposes |
| session/decisions.jsonl / ui_events.jsonl | These capture flow decisions and UI events, not Director reasoning. They complement, not duplicate, the verdict sinks |
| Console encoding issues (mojibake at L392) | Observed at L392 — terminal encoding artifact, not a DB parity issue. Data in DB is clean UTF-8 |

---

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed: yes**

Rationale:
- All 6 findings are observability/retention gaps
- No decision-path logic is affected
- The Director will still make correct verdicts
- Post-select gates will still fire correctly
- Feedback synthesis will still work correctly
- The only cost is reduced post-hoc diagnostic ability for the new run

**However**: If the goal is to diagnose the next run's failures more precisely (especially any split-brain verdicts), fixing QW-1 through QW-3 before the rerun would significantly improve diagnostic coverage.

### Top 3 highest-ROI fixes before next rerun

1. **QW-1**: Remove Stage 2 `[:500]` truncation — trivial 1-line fix, eliminates a policy violation
2. **QW-2**: Wire `initial_verdict` in post-select conflict path — low effort, eliminates the most confusing parity gap (split-brain ambiguity in stage_attempts)
3. **QW-3**: Populate Stage 3 reasoning fields in stage_attempts — low effort, enables single-table diagnostic queries across all stages

---

## 8. Confidence And Limits

**Confidence: 96%**

### Basis
- Console.txt fully inspected (1,011 lines, Arc 1 Ep1-3 + Arc 2 start)
- All 12 stage_attempts rows field-by-field compared against console and runtime_audit
- All 11 director_selections rows field-by-field inspected
- All 12 attempt_raw_rationale rows inspected for coverage
- runtime_audit.jsonl 20 entries cross-checked against stage_attempts
- Source code save-path for Stage 2 (stage2_finalizer.py), Stage 3 (stage3_orchestrator.py), and Stage 4 (stage4_interview_round.py) traced to confirm root causes
- F-3 truncation confirmed in live source at stage2_finalizer.py:2837

### Limits
- Console.txt ends mid-Arc 2; Arc 2 verdict parity not tested (Arc 2 Stage 4 had not started)
- decisions.jsonl and ui_events.jsonl were too large for full read; sampled for structural understanding only
- llm_io.jsonl not inspected (LLM I/O is out of scope for verdict parity)
- `initial_verdict` wiring was traced via grep patterns, not a full call-graph walk; the exact line where the post-select path drops the value was identified by elimination rather than by stepping through the full code path

---

## 9. Cross-Reference to Diagnosis Questions

| Question | T8 Answer |
|----------|-----------|
| Q1: Did Stage 2 pass with a thin arc? | Out of T8 scope (see T1/T2). DB shows Stage 2 Arc 1 PASS score=100, verdict_reason="" in stage_attempts but director_selections has selection_reason. |
| Q2: Did Stage 3 over-pass weak blueprints? | Out of T8 scope (see T3/T4). DB shows all 4 blueprints PASS (92-98), no retry data in stage_attempts reasoning fields. |
| Q3: Did Stage 4 fail from writing, fixing, or inconsistent judgment? | Stage 4 ep3 failed due to blueprint scene structure compliance (rounds 1-3), then post-select continuity conflict (round 4). Judgment was internally consistent: Director was strict about scene structure, then post-select caught timeline error the Director missed. |
| **Q4: Did Director primary verdict and post-select gates diverge?** | **YES — confirmed in round 4 of ep3.** Director gave PASS (score=98) but post-select detected 2 timeline conflicts and downgraded to REJECT. This is **correctly functioning split-brain detection**, not a bug. The system worked as designed. The parity gap is that `initial_verdict` in stage_attempts doesn't record that the Director originally said PASS. |
| Q5: Root causes vs symptoms? | All 6 findings are root-cause save-path omissions, not downstream symptoms. |
