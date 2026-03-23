System-track survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/daily-roadmap-2026-03-23.md
4. docs/2026-03-23/opus-llm-friendliness-global-survey-order.md
5. docs/2026-03-23/llm-codebase-orientation-pack.md
6. docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md
7. docs/2026-03-23/fresh-run-3pass-audit-report.md

Task:
Run a codebase-wide LLM-friendliness survey for the current live workspace state.

Primary goal:
Assess whether the production codebase is navigation-ready, authority-readable, contract-readable, and observability-readable for an LLM after the long-function reduction campaign and fresh run.

Hard constraints:
- This is survey-only. Do not patch code.
- Do not drift into general style review.
- Do not reopen the long-function campaign just because a file is still 100+ LOC.
- Do not create an execution SSOT or implementation roadmap unless explicitly asked.
- Prefer live workspace evidence over stale document assumptions.
- Fresh run already exists. Use it as evidence input where relevant.

Evaluate the repo on exactly these 5 axes:
- Navigation
- Authority
- Contract
- Observability
- Local Readability

Required method:
1. Static topology map
- Re-walk the live codebase using the orientation pack as a starting map.
- Confirm or reject current reading order, authority boundaries, and sink ownership.
- Note where the orientation pack is stale or incomplete.

2. Hotspot grading
- Build a repo-wide hotspot list for LLM comprehension cost.
- Rank by breadth of impact, likelihood of wrong edits, authority ambiguity, contract ambiguity, and observability ambiguity.
- Produce:
  - Top 20 comprehension hotspots
  - Top 10 quick wins
  - Top 10 no-action / already-settled zones

3. Recommendation merge audit
- For each hotspot, decide whether the right next step is:
  - no action
  - comment/doc improvement
  - observability improvement
  - bounded refactor
- If a recommendation would change entry flow, owner authority, contract meaning, or sink topology, mark it as orientation-pack-impacting.

Output:
Write the final report to:
docs/2026-03-23/opus-llm-friendliness-global-survey-report.md

The report must contain these sections:
1. Executive Summary
2. Heatmap by Area
3. Top 20 Comprehension Hotspots
4. Quick Wins
5. Boundary Refactor Candidates
6. Orientation Pack Refresh Candidates
7. No-Action / Settled Areas
8. Confidence And Limits

For each hotspot include:
- file path
- line anchor
- affected axis
- severity: P0 / P1 / P2
- why it is costly for LLM reasoning
- recommended fix type:
  - comment-only
  - doc-only
  - observability-only
  - boundary-refactor
  - contract-cleanup
  - ignore

Acceptance criteria:
- every P0/P1 item has a concrete file and line anchor
- every recommendation has a fix type
- orientation-pack-impacting items are separated from local readability-only items
- the report explicitly states whether the codebase is now navigation-ready, authority-readable, contract-readable, and observability-readable for an LLM
- include a confidence score
- apply 3-pass audit before final save

After writing the report, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/opus-llm-friendliness-global-survey-report.md
- python scripts/ops_validator.py

In your final response to me:
- summarize the top findings first
- then give confidence
- then list the highest-ROI next actions
- do not include fluff
