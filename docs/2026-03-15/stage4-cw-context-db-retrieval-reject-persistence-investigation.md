# Stage4 CW Context / DB Retrieval / Reject Persistence Investigation

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
Evidence Path: `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-evidence.txt`
Audit Path: `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-3pass-audit.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- included:
  - CW historical-context intake
  - Director critique persistence/retry carryover
  - DB retrieval quality for post-run investigation and Stage 4 context assembly
  - whether reject reasons and rationale are stored richly enough in DB
- excluded:
  - fresh runtime log merge
  - backend-front miswiring/control-plane analysis
  - menu `7` operator contract
  - literary-quality verdict on manuscript prose itself

## 1. Executive Summary
- `CW context problem` exists as a likely quality risk, but the code does not support a `missing wire` diagnosis.
- `DB retrieval problem` exists, but it is more precisely a `thin helper / inconsistent retrieval authority` problem than a `DB cannot find it` problem.
- `reject reason persistence in DB` is mostly sufficient already for post-run investigation; the weak spots are field caps and thin convenience APIs, not absence of storage.

## 2. Finding A - CW history is wired, but likely lossy after assembly and trim
Severity: `P1`

What the code currently does:
- `prepare_episode_context()` in `stage4_context_builder.py:1749-1973` builds a multi-layer historical payload:
  - recent full manuscripts from DB
  - episode digests and summaries
  - long-range arc anchors
  - world-state summary
- `build_mandatory_context()` in `stage4_context_builder.py:2088-2620` adds continuity and state blocks beyond raw manuscript history.
- `_build_common_writer_kwargs()` in `stage4_interview_round.py:1261-1358` passes these surfaces to CW.
- `chief_writer_context.py:388-467` injects `mandatory_context` and `prev_manuscripts_text` into the actual CW prompt.

Why this still looks risky:
- The same context is budgeted multiple times:
  - `_compose_mandatory_context_with_headroom()` in `stage4_context_builder.py:1444-1516`
  - `mandatory_context` trim in `stage4_orchestrator.py:812-856`
  - `smart_truncate(prev_manuscripts_text)` in `chief_writer_context.py:458-467`
- That means past context is present, but not guaranteed to survive at equal fidelity.
- The likely failure mode is not `CW receives no past`, but `CW receives a large, priority-competing, partially trimmed past`.

Why this matters for post-run investigation:
- If Director correctly flags continuity drift and CW still repeats or forgets prior state, the gap can plausibly sit in context budget allocation rather than in Director vision or total absence of carryover.

Classification:
- `not miswiring`
- better label: `budgeted context loss / prioritization drift`

## 3. Finding B - DB can retrieve important history, but helper surfaces are uneven
Severity: `P1`

What is strong:
- Recent manuscript retrieval is explicit and direct:
  - `get_manuscripts_range()` in `db_manager.py:2636-2686`
- Canonical fact and relationship retrieval are present:
  - `load_anchor()` / `get_canonical_facts()` / relationship helpers in `db_manager.py:1681-1858`
- Stage 4 context assembly actively uses DB-backed history for recent carryover.

What is weak:
- Long-range recall is progressively downgraded:
  - recent full text -> episode summaries -> arc anchors
- `get_recent_manuscript_excerpts()` is excerpt-only by design.
- `get_stage_attempts_for_arc()` in `db_manager.py:3145-3173` is thin:
  - it returns `reject_reason`, but not richer rationale fields
  - it omits artifact lineage fields useful for post-run audit
- `stage4_context_builder.py:1681-1718` uses that thin helper for Stage 2 failure carryover, so the resulting Stage 4 prompt can only see a reduced failure summary.

Why the problem is not simply `DB can't find it`:
- The richer data is already in the database.
- `failure_analyzer.py:383-411` and `failure_analyzer.py:629-681` use direct SQL and richer sink comparison logic to recover `selection_reason`, `verdict_reason`, and `fix_scope` truth.
- So the gap is retrieval-surface inconsistency:
  - some code paths see rich truth
  - some convenience/helper paths only expose a thin slice

Classification:
- `not miswiring`
- better label: `retrieval surface thinness / inconsistent query authority`

## 4. Finding C - Reject and rationale persistence in DB is mostly sufficient
Severity: `P2`

What is already persisted:
- `stage_attempts` schema stores:
  - `reject_reason`
  - `selection_reason`
  - `verdict_reason`
  - `open_review`
  - `fix_scope_reasoning`
  - `runtime_advisory`
  - `retry_directives`
  via `db_manager.py:645-661`
- `save_stage_attempt()` writes those fields via `db_manager.py:3265-3329`
- `_record_s4_attempt()` forwards them from Stage 4 via `stage4_interview_round.py:4906-5028`
- `episode_production` also stores selection/verdict rationale and provenance via `stage4_interview_round.py:4802-4886`
- `director_selections` separately persists selection-level rationale in `db_manager.py:2767-2848`

What this means:
- If the post-run question is `what content was rejected and why`, the DB already stores much more than just a generic reject flag.
- The claim `DB is not storing enough reject reasons` is not supported by the source.

Bounded limitations:
- DB save path truncates these rationale fields to roughly 500 characters.
- Some session/log payloads cap `open_review` more aggressively.
- Thin retrieval helpers can hide stored richness unless the caller uses richer SQL paths.

Classification:
- `storage mostly sufficient`
- weak points: `field caps`, `helper omissions`, `query-path inconsistency`

## 5. Director vs CW interpretation
- Director appears to have a rich critique surface:
  - `selection_reason`
  - `verdict_reason`
  - `feedback.issues`
  - `action_items`
  - `open_review`
  - `fix_scope_reasoning`
  - `consistency_checklist`
  - `contradiction_types`
- Retry wiring also exists:
  - `open_review` and `action_items` propagate into CW retry prompts
  - tests explicitly cover this propagation
- So the current best explanation for `Director seems right, CW still misses the past` is:
  - Director can point out the issue
  - CW can receive the issue
  - but the historical substrate and retry context may be too compressed or priority-competing by the time generation happens

## 6. Direct Answers To The Requested Questions
### 6.1 `CW 컨텍스트 문제냐`
- likely yes
- but not as a missing-wire problem
- more likely as a context-budget and prioritization problem

### 6.2 `DB에서 잘 찾냐`
- recent/history retrieval: mostly yes
- deep and investigative retrieval: only partially
- the DB has the data, but not every helper exposes enough of it

### 6.3 `무슨 사유로 reject냐를 DB에 충분히 넣고 있냐`
- mostly yes
- Stage 4 already persists rich reject/rationale/advisory fields
- however, convenience retrieval and field caps reduce how usable that truth is during post-run investigation

## 7. Follow-On Investigation Hooks
- compare one fresh run across three truth layers:
  - Director critique truth
  - CW retry prompt truth
  - final manuscript narrative truth
- measure how much `mandatory_context` survives trimming in a real Stage 4 run
- add a post-run retrieval view that exposes the rich rationale fields without forcing every audit path to reimplement direct SQL

## 8. Final Judgment
- This area should not be filed primarily as `miswiring`.
- The sharper diagnosis is:
  - CW historical carryover risk = `budgeted context loss`
  - DB investigation friction = `thin retrieval surface`
  - reject-reason storage = `mostly sufficient but ergonomically underexposed`
