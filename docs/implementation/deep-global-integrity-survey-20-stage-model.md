# Deep Global Integrity Survey 20-Stage Model

Date: 2026-03-14
Status: active
Applies To: deep, high-rigor, codebase-global system-track survey work
Related Harness:
- `docs/implementation/deep-global-integrity-survey-harness.md`
Related Contracts:
- `docs/implementation/single-ssot-roadmap-contract.md`
- `docs/implementation/evidence-triangulation-contract.md`
- `docs/implementation/integrity-confidence-scoring-contract.md`

## 1. Purpose
- Define the "endgame" version of a codebase-global survey for this workspace.
- Make deep survey work slow, explicit, and auditable rather than informal.
- Ensure the survey bundle can support a 95% or higher integrity-confidence claim.

## 2. Stage Groups

### Group A. Framing and Scope Lock
1. Scope lock
- Declare included and excluded paths before counting anything.

2. Change-lock check
- Record whether canary, code-freeze, or runtime sensitivity forces survey-only behavior.

3. Baseline lineage harvest
- Read the minimum prior canonical audits, execution docs, and contracts needed to avoid duplicate work.

4. Coverage plan freeze
- Map the survey to macro, micro, cross-cut, and operational lenses before evidence collection expands.

### Group B. Macro Authority and Control-Flow Mapping
5. Repo topology map
- Identify active roots, dominant entrypoints, and ownership boundaries.

6. Authority map
- Distinguish authoritative, compatibility, debug-shadow, and stale surfaces.

7. Runtime spine map
- Trace bootstrap, orchestration, steady-state runtime, and shutdown paths.

8. Dependency seam map
- Record where subsystems, services, agents, bridges, and contracts actually connect.

### Group C. Micro and Side-Effect Evidence
9. Hotspot census
- Count high-LOC, high-churn, or high-side-effect files and modules.

10. Side-effect provenance matrix
- Record file writes, DB writes, JSONL/audit sinks, console/UI output, network, subprocess, cache, and config mutation.

11. State and mutation map
- Identify mutable global state, singleton ownership, retry loops, rollback boundaries, and in-memory coordination points.

12. Persistence and durability map
- Trace which surfaces are durable, partially durable, or console-only.

### Group D. Cross-Cut and Operational Integrity
13. Operator surface audit
- Survey what humans see, what gets persisted, and where those two diverge.

14. Contract and config drift sweep
- Check prompts, IPC/API/event contracts, bootstrap assumptions, and config coupling.

15. Failure and recovery sweep
- Capture retries, fallbacks, compensation, integrity checks, and shutdown recovery behavior.

16. Regression and canary boundary audit
- Separate read-only verification from mutation-heavy helpers and live canary tools.

### Group E. Contradiction Closure and Action Synthesis
17. Evidence triangulation
- Require multi-source support for critical claims before elevating them.

18. Uncertainty and contradiction ledger
- Track unresolved gaps, conflicting evidence, and confidence caps explicitly.

19. Area execution SSOT synthesis
- Convert action-bearing areas into canonical execution SSOT documents.

20. Single master roadmap synthesis and confidence gate
- Create exactly one SSOT roadmap for the active bundle, validate the bundle, and close only when confidence reaches at least 95%.

## 3. What This Model Adds Beyond the Standard Global Survey
- more than tranche coverage: it requires lens coverage
- more than inventory: it requires authority, state, and side-effect provenance maps
- more than one report: it requires execution SSOT lineage plus a single roadmap
- more than "looks complete": it requires triangulation, contradiction handling, and confidence scoring

## 4. Minimum Deep Bundle
- one master survey doc using the deep global survey template or equivalent headings
- one evidence manifest
- one cross-cut integrity matrix section or companion doc
- one uncertainty and contradiction ledger section or companion doc
- one canonical execution SSOT per action-bearing area
- one single canonical SSOT roadmap for the bundle
- matching temp mirrors for execution SSOT docs and the single roadmap
- validator output for queue integrity plus deep bundle structure

## 5. Guardrails
- Do not call a survey "deep" if it only contains counts and a short risk list.
- Do not claim 95% confidence while critical claims remain single-sourced.
- Do not create multiple SSOT roadmaps for one active global survey bundle.
- Do not let execution docs outrun unresolved contradictions that cap confidence below threshold.
