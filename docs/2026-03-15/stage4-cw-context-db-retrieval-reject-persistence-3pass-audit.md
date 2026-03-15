# Stage4 CW Context / DB Retrieval / Reject Persistence 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
Evidence Path: `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-evidence.txt`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- Save one focused investigation doc that answers three questions without inflating into a new execution lane:
  - does CW actually receive past context
  - does DB retrieval actually find enough truth for post-run investigation
  - does DB already store enough reject/rationale detail
- Keep the classification precise: `not miswiring by default`.

## 2. Pass 1 - Scope And Structure
- Document type is correct:
  - investigation report plus raw evidence plus 3-pass audit
  - no execution SSOT, no temp mirror, no roadmap mutation
- Scope is correctly bounded:
  - included: CW context intake, Director critique surfaces, DB retrieval surfaces, reject-rationale persistence
  - excluded: fresh runtime log merge, backend-front control plane, menu `7`, prose-quality literary audit
- Output set is sufficient:
  - raw evidence file
  - final investigation report
  - this audit

## 3. Pass 2 - Evidence And Internal Consistency
- CW intake claim is supported:
  - `stage4_context_builder.py:1749-1973`
  - `stage4_context_builder.py:2088-2620`
  - `stage4_interview_round.py:1261-1358`
  - `chief_writer_context.py:388-467`
- `not miswiring` classification is supported because the same evidence shows multiple active carryover paths.
- `lossy after trim` claim is supported:
  - `stage4_context_builder.py:1444-1516`
  - `stage4_orchestrator.py:812-856`
  - `chief_writer_context.py:458-467`
- DB retrieval claim is internally consistent:
  - recent full retrieval exists via `get_manuscripts_range()`
  - helper thinness exists via `get_stage_attempts_for_arc()`
  - richer direct SQL retrieval exists in `failure_analyzer.py`
- DB persistence sufficiency claim is supported:
  - schema fields in `db_manager.py:645-661`
  - save path in `db_manager.py:3265-3329`
  - Stage 4 forwarding path in `stage4_interview_round.py:4906-5028`
  - tests in `tests/test_db_manager.py:448-478` and `tests/test_stage4_interview_round.py:1816-1842`

## 4. Pass 3 - Judgment Quality
- The report avoids overclaiming:
  - it does not say CW continuity is broken in all runs
  - it does not say DB retrieval is absent
  - it does not say reject reasons are understored
- The report answers the user-facing questions directly:
  - CW issue: yes, but likely as budgeted loss
  - DB search: yes for some paths, uneven for others
  - reject DB storage: mostly yes
- The follow-on section is proportionate:
  - fresh run comparison across Director/CW/final manuscript truth
  - trim-survival measurement
  - richer post-run retrieval view

## 5. Confidence And Save Gate
- Pass 1 structure and scope: pass
- Pass 2 evidence and consistency: pass
- Pass 3 judgment quality: pass
- Estimated confidence: `97%`
- Save decision: final save allowed

## 6. Audit Conclusion
- The investigation should be saved as a final reference for future post-run audits.
- The strongest claim is not `miswiring`.
- The most accurate diagnosis bundle is:
  - `CW historical-context quality risk`
  - `DB retrieval surface thinness`
  - `mostly sufficient reject-rationale persistence with bounded caps`
