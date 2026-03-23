Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey lane report
Terminal: T2
Focus: Stage 2 arc artifact and DB truth
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md`
Temp Mirror Path: none
Source Evidence:
- `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/0_0323/plans/arcs/arc_001.txt`
- `projects/0_0323/project_data.db` (tables: stage_attempts, director_selections, anchors)
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/episode_production.jsonl`
- `projects/0_0323/logs/session/decisions.jsonl`
- `projects/0_0323/logs/session/state_changes.jsonl`
- `docs/2026-03-23/console.txt`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: dirty workspace; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py, tests/, docs/, projects/0_0323/

---

# T2: Stage 2 Arc Artifact and DB Truth

## 1. Executive Summary

Stage 2 arc artifact content is **complete and structurally sound**. The artifact JSON, the `arcs` DB anchor, and the `plans/arcs/arc_001.txt` are all consistent with each other and with the console-observed Director flow.

The root cause in this lane is **not artifact corruption or thin arc content**. It is a **DB metadata parity gap**: Stage 2 (and Stage 3) write `stage_attempts` and `director_selections` records with systematically empty textual fields that Stage 4 populates. This makes post-run root-cause analysis from DB alone impossible for Stage 2/3, forcing reliance on artifact files, console transcripts, and session logs.

Primary blocker: **observability gap, not decision-path failure**.

## 2. Current Ownership / Flow Map

### Artifact Write Chain

| Step | Owner | Output |
|------|-------|--------|
| Arc ensemble generation | `stage2_finalizer.py` L2391+ | 3 candidates (creative/balanced/conservative) |
| Director audit | `stage2_finalizer.py` → `director_ensemble.py` | verdict + score + thinking |
| Artifact save | `stage2_finalizer.py` L2680+ | `logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` |
| Plan text save | `stage2_finalizer.py` | `plans/arcs/arc_001.txt` |
| DB anchor save | `stage2_finalizer.py` → `db_manager.py` | `anchors` table key `arcs` |
| DB stage_attempts | `stage2_finalizer.py` L2691 (PASS) / L2829 (REJECT) | `stage_attempts` row |
| DB director_selections | `stage2_finalizer.py` L2714 (PASS) / L2852 (REJECT) | `director_selections` row |
| Session decisions log | `stage2_finalizer.py` | `session/decisions.jsonl` |

### DB Sink Parity

| Sink | Stage 2 | Stage 3 | Stage 4 |
|------|---------|---------|---------|
| `stage_attempts` textual fields | EMPTY | EMPTY | POPULATED |
| `director_selections` verdict_reason | EMPTY | POPULATED | POPULATED |
| `director_selections` selection_reason | POPULATED | POPULATED | POPULATED |
| `director_selections` director_thinking | POPULATED | EMPTY | POPULATED |
| `episode_production.jsonl` | ABSENT | ABSENT | POPULATED |
| `runtime_audit.jsonl` stage event | ABSENT | POPULATED (blueprint_success) | POPULATED (pathology, complete) |
| `session/decisions.jsonl` | POPULATED | POPULATED | POPULATED |

## 3. Focus-Scope Findings

### F-1. Arc Artifact JSON — Complete and Sound (NOT a root cause)

**Evidence**: `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`

24 top-level keys present:
- `_ensemble_meta`: 3 candidates (creative=100, balanced=95, conservative=95), max_similarity=0.29, no high-similarity warning
- `arc_drive`: full narrative_drive with protagonist_core_desire, active_villainy (3 antagonists), arc_reward, core_scene_ratio
- `tactical_doc`: 3,461 chars, 5 episodes with [start state] → narrative → [end state] per episode
- `state_changes`: 3 major items, 3 NPC introductions, 1 relationship change, 1 skill acquisition, timeline (Jan 2-25, 2006)
- `state_constraints`: arc_start_state, arc_end_state (capital=18.65B won), 3 continuity_checkpoints, 3 foreshadowings, investment_calc
- `semantic_carryover`: 3 continuity_checkpoints, 3 foreshadow_anchors, 3 relationship_rationale, growth_justification
- `joint_docs`: final_location, physical_inventory, world_joint
- `status_shadow`: expected_injuries, item_consumption, key_stat_change
- `pacing_decision`: standard pace_mode, density_focus, ep_count_reasoning
- `hybrid_composition`: primary=Setup, secondary=[Character Introduction, Inciting Incident]

**Verdict**: The arc is narratively rich, not "tactically thin." Episode tactical documents have clear state transitions, asset tracking, and character motivation. This arc did NOT destabilize Stage 3 or Stage 4 through content insufficiency.

### F-2. Arc Plan Text — Consistent with Artifact

**Evidence**: `projects/0_0323/plans/arcs/arc_001.txt` (96 lines)

Contains:
- Basic info (volume 0, ep 1-5, 5 episodes)
- Full tactical doc (identical to artifact JSON `tactical_doc` field)
- Beat sequence (5 beats)

**Verdict**: Plan text is a faithful extract of the artifact. No truncation or content loss.

### F-3. DB Anchor — Perfect Copy of Artifact

**Evidence**: DB `anchors` table, key `arcs` (14,139 bytes)

- Same 24 keys as artifact JSON
- `tactical_doc` matches byte-for-byte (3,461 chars)
- No field stripping between artifact file and DB runtime copy

**Verdict**: No data loss between artifact save and DB anchor. Stage 3 and Stage 4 receive the same arc data that was generated.

### F-4. Director Verdict Flow — Correct (NOT a root cause)

**Evidence**: Console L338-396, `director_selections` id=1, `decisions.jsonl` entries [0]-[1]

Flow:
1. FourPhase generation produced 3 ensemble candidates
2. Director initial verdict: `PASS_WITH_FIX` (score=95)
3. 1 contradiction flagged: financial discrepancy (18.65B vs computed 18.95B won)
4. TF-32-V patch applied (added 3,000만원 equipment purchase explanation)
5. Re-audit #1: `PASS` (score=100)
6. PatchPressure advisory: exceeded threshold → advisory-only PASS
7. ConstraintDB updated
8. Final result: PASS, score=100, strategy=conservative

The Director correctly identified a minor numerical inconsistency, the system patched it, and re-audit confirmed the fix. Decision path is sound.

### F-5. [P1] `stage_attempts` Textual Metadata Loss — Stage 2 AND Stage 3

**Evidence**: DB query `stage_attempts WHERE stage IN (2,3)`

All 5 Stage 2/3 rows have these fields systematically EMPTY:
- `selection_reason = ""`
- `verdict_reason = ""`
- `open_review = ""`
- `runtime_advisory = ""`
- `retry_directives = ""`
- `score_breakdown = null`

Compare Stage 4: all 7 rows have these fields POPULATED with rich Korean text.

**Source code root cause**:
- Stage 2 PASS path: `stage2_finalizer.py:2691-2710` — calls `save_stage_attempt()` without `selection_reason`, `verdict_reason`, `open_review`, `score_breakdown`
- Stage 2 REJECT path: `stage2_finalizer.py:2829-2849` — same omission
- Stage 4 path: `stage4_interview_round.py:5784-5813` — uses `_build_stage4_db_attempt_payload()` which explicitly passes all 4 fields
- DB method `db_manager.py:2878-2910` — signature supports all fields; default is empty string/None

**Impact**: Post-run DB-only analysis of Stage 2/3 cannot recover:
- Why a specific strategy was selected
- What the Director's verdict reasoning was
- What the open review notes were
- What the score breakdown was

This forces forensic investigation to artifact files + console + session logs, which is exactly the situation this survey encountered.

### F-6. [P1] `director_selections` Missing `verdict_reason` for Stage 2

**Evidence**: DB `director_selections` id=1 (Stage 2): `verdict_reason = ""`

**Source code root cause**:
- Stage 2: `stage2_finalizer.py:2714-2729` — calls `save_director_selection()` without `verdict_reason` parameter
- Stage 4: `stage4_interview_round.py:2304-2325` — explicitly passes `verdict_reason` at L2316
- The `audit` object available at L2714 contains `audit.get("reason")` which is passed as `selection_reason` but NOT as `verdict_reason`

**Impact**: `director_selections` for Stage 2 has `selection_reason` populated but `verdict_reason` empty. For Stage 4, both are populated (often with the same text).

### F-7. [P2] No `episode_production.jsonl` Entry for Stage 2

**Evidence**: `episode_production.jsonl` has 11 entries, all for Stage 4 (ep 1-3). Zero Stage 2 or Stage 3 entries.

**Impact**: Arc-level production lineage is incomplete. The production journal only tracks manuscript (Stage 4) completions, not arc design (Stage 2) or blueprint (Stage 3) completions.

### F-8. [P2] No Stage 2 Director Verdict in `runtime_audit.jsonl`

**Evidence**: 19 audit entries total. Stage 2 has only `v60_25_auto_correct` (arc auto-correction). No explicit Director verdict event for Stage 2. Stage 3 has `blueprint_success` events. Stage 4 has `stage4_retry_pathology_signal` and completion events.

**Impact**: Runtime audit cannot reconstruct Stage 2 Director verdicts without reading `decisions.jsonl` or `director_selections`.

### F-9. [P2] Ensemble Meta Shows `best_score=95` but Final Score is 100

**Evidence**: Artifact `_ensemble_meta.best_score = 95`, DB `stage_attempts.score = 100`, DB `director_selections.score = 100`

**Explanation**: This is NOT a bug. The ensemble meta snapshot captures the pre-patch selection score (conservative=95). The DB records the post-patch re-audit score (100). The arc's stored `_ensemble_meta` correctly reflects the initial selection moment, while the DB correctly reflects the final verdict.

**Impact**: None. But worth noting for cross-source reconciliation: artifact scores and DB scores may differ when PASS_WITH_FIX → re-audit occurs. This is by design.

## 4. Root-Cause Relevance

### Root Causes (This Lane)

| ID | Finding | Type | Root Cause? | Blocks Rerun? |
|----|---------|------|-------------|---------------|
| F-5 | `stage_attempts` textual metadata loss (Stage 2/3) | contract-cleanup | **Root cause of post-run diagnostic difficulty** | No (observability) |
| F-6 | `director_selections` missing `verdict_reason` (Stage 2) | contract-cleanup | **Root cause of verdict reason gap** | No (observability) |

### Downstream Symptoms

| ID | Finding | Symptomatic Of |
|----|---------|----------------|
| F-7 | No production journal for Stage 2 | F-5 family — Stage 2 observability is systematically lower than Stage 4 |
| F-8 | No runtime audit for Stage 2 Director | F-5 family — same root |

### Not Root Causes

| ID | Finding | Why Not |
|----|---------|---------|
| F-1 | Arc artifact content | Complete and rich — not the cause of downstream Stage 3/4 issues |
| F-2 | Arc plan text | Consistent with artifact |
| F-3 | DB anchor | Perfect copy of artifact |
| F-4 | Director verdict flow | Functioned correctly (PASS_WITH_FIX → patch → PASS) |
| F-9 | Score discrepancy (95 vs 100) | By design (pre-patch vs post-patch) |

## 5. Quick Wins

### QW-1. Pass textual fields in Stage 2 `save_stage_attempt()` calls
- **Fix type**: contract-cleanup
- **Files**: `modules/core/stage2_finalizer.py` L2691-2710, L2829-2849
- **Action**: Add `selection_reason=str(audit.get("reason", ""))`, `verdict_reason=str(audit.get("reason", ""))`, `open_review=str(audit.get("open_review", ""))`, `score_breakdown=audit.get("score_breakdown")` to both PASS and REJECT path calls
- **ROI**: High — enables DB-only post-run analysis for Stage 2

### QW-2. Pass `verdict_reason` in Stage 2 `save_director_selection()` calls
- **Fix type**: contract-cleanup
- **Files**: `modules/core/stage2_finalizer.py` L2714-2729, L2852-2867
- **Action**: Add `verdict_reason=str(audit.get("reason", ""))` to both calls
- **ROI**: High — closes the Stage 2 verdict_reason gap

### QW-3. Add Stage 2 Director verdict to `runtime_audit.jsonl`
- **Fix type**: observability-only
- **Files**: `modules/core/stage2_finalizer.py` (near L2710 / L2849)
- **Action**: Emit an `arc_director_verdict` or `stage2_verdict` event to the audit log
- **ROI**: Medium — enables audit log reconstruction without needing decisions.jsonl

## 6. False Leads / Non-Causes

1. **"Stage 2 passed a tactically thin arc"** — FALSE. The arc is 24-field, 364-line JSON with rich narrative structure, 5 detailed episode tactical documents, complete state tracking, and 3 continuity checkpoints. The arc is one of the strongest outputs in the pipeline.

2. **"Ensemble collapsed to single candidate"** — FALSE. 3 candidates were generated (creative/balanced/conservative), diversity scores were healthy (max_similarity=0.29), and Director selected conservative with a detailed audit rationale.

3. **"Director thinking was lost"** — PARTIALLY FALSE. `director_thinking` IS populated in `director_selections` (full multi-paragraph English analysis). It is only the `verdict_reason` field that is empty in both DB tables.

4. **"Arc artifact and DB anchor diverged"** — FALSE. They are identical (same 24 keys, same content).

5. **"Financial discrepancy was unresolved"** — FALSE. Director flagged it, system patched it (added equipment purchase line item), re-audit confirmed the fix.

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed: yes**

This lane's findings are exclusively observability/metadata gaps. They do not affect:
- Arc content quality (confirmed sound)
- Director decision accuracy (confirmed correct)
- Artifact file integrity (confirmed complete)
- DB anchor integrity (confirmed consistent)

A fresh run will produce the same arc quality. The metadata gaps will persist, making post-run analysis harder but not causing runtime failures.

**Top 3 highest-ROI fixes before the next rerun:**
1. **QW-1**: Stage 2 `stage_attempts` textual fields — enables DB-only post-mortem
2. **QW-2**: Stage 2 `director_selections` verdict_reason — closes verdict reasoning gap
3. **QW-3**: Stage 2 runtime audit event — enables audit log reconstruction

All three are `contract-cleanup` or `observability-only` fixes with zero risk of runtime regression.

## 8. Confidence And Limits

**Estimated confidence: 97%**

Basis:
- All artifact files read in full (JSON parsed, fields compared)
- DB tables queried directly (stage_attempts, director_selections, anchors)
- Source code call sites confirmed by subagent exploration of `stage2_finalizer.py`, `stage4_interview_round.py`, `db_manager.py`
- Console transcript cross-referenced with DB and artifact data
- Session logs (decisions.jsonl, state_changes.jsonl) verified

The 3% gap:
- Stage 2 was exercised only once (1 arc, 1 attempt). The textual field loss pattern is systematic and consistent, but a multi-arc run would provide stronger confirmation (1%)
- The audit log encoding issues (cp949 mojibake in some entries) were observed but not deeply root-caused — they may mask additional information (1%)
- Stage 3 metadata gap was confirmed but not deeply sourced in this lane (T3/T4 scope) (1%)

---

## 3-Pass Audit Record

### Pass 1
- Read all required context documents (AGENTS.md, harnesses, console.txt, prior reports)
- Inventoried all Stage 2 artifacts, DB tables, and log files
- Confirmed artifact existence and basic integrity

### Pass 2
- Deep-read arc artifact JSON (364 lines, 24 keys)
- Queried all relevant DB tables with field-level comparison
- Cross-referenced console, decisions.jsonl, and runtime_audit.jsonl
- Confirmed Stage 2/3 vs Stage 4 metadata parity gap via source code

### Pass 3
- Verified report structure against required sections (8 sections)
- Verified all P0/P1 items have file:line anchors
- Verified all recommendations have fix type
- Confirmed fresh-run-before-fix assessment
- Trimmed false leads section to prevent overclaiming
