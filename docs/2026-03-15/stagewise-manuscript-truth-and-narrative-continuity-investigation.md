<!-- [참고자료] -->
# Stagewise Manuscript Truth / Narrative Continuity Investigation

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-investigation.md`
Evidence Path: `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-evidence.txt`
Audit Path: `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-3pass-audit.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, active roadmap/temp edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked post-remediation docs plus projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- included:
  - direct Stage 2 arc artifact truth for `projects/000`
  - direct Stage 3 blueprint truth for `projects/000`
  - direct Stage 4 terminal manuscript truth for `projects/000`
  - continuity handoff checks across `arc -> blueprint -> final or patched manuscript`
  - decision and episode-production metadata only where needed to explain the artifact truth
- excluded:
  - backend-front or menu `7` runtime control-plane work
  - global log-sink restructuring
  - full literary scoring or marketability review of the prose
  - broad code realization beyond bounded follow-up hooks

## 1. Executive Summary
- Artifact truth is strong across the selected run: the Stage 2, Stage 3, and Stage 4 output files exist and decode cleanly as UTF-8.
- Metadata truth is weaker in two places: Arc 1 enters the pipeline with a blank `constraint_summary`, and the Stage 3 blueprint pass surface can still allow a cross-episode continuity contradiction to reach Stage 4.
- Narrative truth is recoverable at the terminal Stage 4 surface, but only by manually reading the artifacts and replaying the retry reasoning; the final authority is not yet surfaced as a canonical post-run manuscript-truth lane.

## 2. Process A - Stage 2 Arc Truth Is Real, But Carryover Metadata Starts Uneven
Severity: `P2`

What was directly confirmed:
- `projects/000/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` exists and decodes.
- `projects/000/logs/artifacts/stage2/arc_002/attempt_01/final_arc__conservative.json` exists and decodes.
- Arc 2 carries a populated `constraint_summary` that explicitly names carryover prohibitions.

What is weak:
- Arc 1 carries `constraint_summary: ""`.
- The raw stagewise evidence already flagged this as a possible Stage 2 carryover gap.
- That means the first handoff into later stages begins with asymmetric metadata authority:
  - Arc 1 has real artifact truth.
  - Arc 1 does not preserve the same carryover-summary surface that Arc 2 later uses.

Why this matters:
- When later blueprint or manuscript continuity is reviewed, the system cannot rely on a stable Stage 2 constraint-summary surface across arcs.
- This is not a missing-artifact problem.
- It is a `carryover metadata completeness` problem.

Classification:
- `artifact truth: strong`
- `metadata truth: uneven at entry`

## 3. Process B - Stage 3 Blueprint Truth Is Rich, But Not Sufficient For Cross-Episode Continuity
Severity: `P1`

What is strong:
- `projects/000/plans/blueprints/` contains `7` saved blueprint files.
- `projects/000/logs/artifacts/stage3/` contains `7` selected final blueprint artifacts.
- `projects/000/logs/session/decisions.jsonl` preserves rich Stage 3 `selection_reason` and `verdict_reason` fields.
- The selected blueprint surfaces for Episode 4 and Episode 5 are explicit:
  - Episode 4 ends on legal pressure from the group legal team.
  - Episode 5 ends on a physical-threat hook after the PB confrontation.

What is weak:
- The Stage 3 pass surface still allowed a blueprint-level continuity problem to survive into Stage 4.
- Episode 5's later Stage 4 rejection reasoning explicitly says the blueprint conflicted with Episode 4's ending because Episode 4 had already committed the full `20억` all-in position.
- In other words:
  - Stage 3 produced a coherent local Episode 5 blueprint.
  - Stage 3 did not fully police the prior-episode state implied by the final Episode 4 manuscript truth.

Why this matters:
- Blueprint truth is currently stronger at `episode-local shape` than at `cross-episode continuity truth`.
- The pipeline therefore relies on Stage 4 retries and manual reasoning to repair a contradiction that should be surfaced earlier or at least reported canonically.

Classification:
- `artifact truth: strong`
- `metadata truth: strong inside the episode`
- `cross-episode continuity truth: under-surfaced before Stage 4`

## 4. Process C - Stage 4 Recovers Terminal Narrative Truth, But Terminal Artifact Authority Is Uneven
Severity: `P1`

What was directly confirmed:
- `projects/000/logs/artifacts/stage4/` contains `21` files across retries and selected outputs.
- Terminal output authority is split across two shapes:
  - Episode 4 terminal truth is represented by `patched_after_fix__A.txt`
  - Episode 5 terminal truth is represented by `final_manuscript__C.txt`
- `projects/000/logs/session/decisions.jsonl` and `projects/000/logs/episode_production.jsonl` preserve rich `selection_reason`, `verdict_reason`, `open_review`, and retry metadata for these attempts.

What the direct artifact reads show:
- The Episode 4 terminal artifact ends on the attorney/legal-pressure hook that the selected Episode 4 blueprint promised.
- The Episode 5 terminal artifact begins from the post-investment drawdown state and ends on the physical-threat hook promised by the selected Episode 5 blueprint.
- The Episode 5 retry path is narratively meaningful, not only formally valid:
  - the rejected attempt records why the continuity contradiction still existed
  - the passing attempt records why candidate `C` repaired that contradiction while preserving tension

What is still weak:
- Post-run audit authority is uneven because a successful terminal truth can live in either:
  - `final_manuscript__*.txt`
  - `patched_after_fix__*.txt`
- That means an auditor can recover the final narrative truth, but the authority is not normalized into one terminal artifact contract.

Classification:
- `narrative truth: recoverable and real at terminal Stage 4`
- `terminal artifact authority: uneven`

## 5. Direct Answers To The User-Facing Questions
### 5.1 `Did manuscript analysis happen across the process?`
- It now has for the selected stagewise run.
- The analysis covered:
  - Stage 2 arc artifacts
  - Stage 3 selected blueprints
  - Stage 4 terminal manuscript artifacts
  - decision and retry metadata where needed to explain continuity outcomes

### 5.2 `Is the pipeline missing manuscript outputs?`
- No.
- The primary issue is not missing output files.
- The sharper issue is that metadata and terminal authority are less uniform than the artifact existence itself.

### 5.3 `Where is the strongest process gap?`
- The strongest gap sits between `blueprint pass truth` and `final manuscript continuity truth`.
- Stage 4 can repair the contradiction, but the pipeline does not yet surface that repaired truth in one canonical manuscript-truth audit surface.

## 6. Action-Bearing Follow-On Hooks
- Save one canonical post-run manuscript-truth lane that compares:
  - Stage 2 carryover metadata
  - Stage 3 blueprint handoff truth
  - Stage 4 terminal narrative truth
- Add one bounded continuity report or regression surface for cases like Episode 4 -> Episode 5 where Stage 3 local success still conflicts with previous final manuscript state.
- Normalize terminal Stage 4 artifact authority for post-run audits so `patched_after_fix__*` outputs are not treated as second-class or ad hoc terminal truth.

## 7. Final Judgment
- The stagewise run does have real manuscript truth at the end of the process.
- The more accurate diagnosis is:
  - Stage 2 entry metadata is uneven
  - Stage 3 blueprint truth is rich but not sufficient for cross-episode continuity enforcement
  - Stage 4 terminal narrative truth is real, but its audit authority is still too manual and artifact-shape-dependent
