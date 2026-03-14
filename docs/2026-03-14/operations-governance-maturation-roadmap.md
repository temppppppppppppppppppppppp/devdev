# Operations Governance Maturation Roadmap

Date: 2026-03-14
Status: active
Scope: system-track operational governance, survey/execution workflow, temp queue control, and analysis readiness
Recommended Target Maturity: Level 4
Current Estimated Maturity: Level 5.0

## 1. Why This Exists
- The workspace now has the foundation of a serious operating system for system-track work.
- The next question is no longer "can we add another harness" but "what is the right end-state and where should we stop."
- This roadmap defines a bounded maturation path so hardening stays coherent instead of endlessly ornamental.

## 2. North Star
The target state is:

- system-track work starts with a predictable preflight
- surveys, evidence, execution docs, and closure artifacts are traceable end to end
- temp queue state is visible to both humans and tools
- exceptions are explicit and time-bounded
- queue realization can be validated mechanically
- later LLM analysis can reconstruct what happened, why, and with what evidence

This does not require infinite process growth. It requires reaching a stable operational plateau.

Working alias:
- this operating pattern may be referred to as `Recursive Ops Loop`
- accepted aliases: `Recursive Ops Loop`, `ROL`, `rol`
- that label means a bounded governance loop for system-track work, not an unbounded self-modifying loop

## 3. Recommended Stop Line
Recommended stop line for this repo:
- stop at `Level 4` unless queue volume, team size, or failure rate materially increases

Why stop there:
- Level 4 gives policy-as-code, automation hooks, and high-confidence closure without turning the repo into a bureaucracy engine
- Level 5 is useful only if execution volume becomes high enough that human orchestration is no longer sufficient

Move past Level 4 only if one or more of the following becomes true:
- `docs/temp/` regularly has `3+` concurrent execution items
- multiple agents or operators are running overlapping system-track work
- closure quality is drifting despite the current validator and closure harness
- the repo needs automatic portfolio-level planning rather than per-topic planning

## 4. The 20-Step Roadmap

### Level 1. Structural SSOT
Goal:
- establish a clear operating constitution

#### 1. SSOT consolidation
Status: completed
- `AGENTS.md` is the workspace SSOT
- `CLAUDE.md` is a compatibility shim only

#### 2. init-first routing
Status: completed
- system-track work enters through the init harness

#### 3. specialized harness split
Status: completed
- survey, queue, 3-pass audit, closure, validator, and stale sweep are split into focused docs

#### 4. canonical vs temp split
Status: completed
- canonical history stays in `docs/YYYY-MM-DD/`
- temp is an execution mirror queue, not archival storage

### Level 2. Queue Integrity
Goal:
- make active execution work observable and mechanically checkable

#### 5. temp queue semantics
Status: completed
- active execution mirrors in `docs/temp/` have explicit meaning

#### 6. roadmap requirement for multi-item queues
Status: completed
- aggregate roadmap is mandatory once multiple execution items exist

#### 7. validator
Status: completed
- canonical/mirror integrity is checked by script

#### 8. queue-state snapshot
Status: completed
- `docs/temp/queue-state.json` can be generated for operators and tooling

### Level 3. Evidence Discipline
Goal:
- make execution docs defensible, reusable, and analyzable

#### 9. side-effect sweep default
Status: completed
- side-effects are part of baseline survey scope, not optional appendix

#### 10. execution synthesis
Status: completed
- multi-source evidence can be collapsed into one traceable execution doc

#### 11. evidence manifest
Status: completed
- high-evidence topics can use an index instead of repeating artifact lists

#### 12. canonical naming contract
Status: completed
- filenames and topic slugs are stable enough for both humans and scripts

### Level 4. Operational Control Plane
Goal:
- move from doc rigor to controlled operations

#### 13. exception registry
Status: completed
- bounded exceptions become explicit artifacts rather than silent drift

#### 14. process health scorecard
Status: completed
- governance health can be summarized across docs and queue state

#### 15. preflight gate
Status: completed
- substantial system-track work can begin with a readiness gate

#### 16. closure discipline
Status: completed
- closure, cleanup, and residual risk are handled by a dedicated harness

Level 4 result:
- at this point the system is already strong enough for serious ongoing use
- this is the recommended plateau for this repo right now

### Level 5. Automation Expansion
Goal:
- reduce manual process assembly for repeated high-volume use

#### 17. roadmap auto-builder
Status: completed
- script that inventories temp execution docs and produces a canonical + temp roadmap skeleton

#### 18. evidence-manifest generator
Status: completed
- helper that turns a known artifact set into a manifest draft

#### 19. stale-reference sweep automation
Status: completed
- script support for SSOT drift scans after governance changes

#### 20. scorecard auto-population
Status: completed
- partial automation that fills scorecard dimensions from validator, queue-state, and known evidence docs

### Level 6. Analysis-Native Operations
Goal:
- make the process itself first-class analysis material for later LLM reasoning

This level is optional and should be entered only after Level 5 is clearly needed.

Candidate items:
- execution docs linked to commit/test/proof artifacts automatically
- closure packs generated from execution SSOT + validation + evidence manifest
- runtime `ui_events` and operator-visible traces joined with execution docs
- LLM-generated queue triage or anomaly summaries

## 5. Recommended Order From Here
Immediate next tranche:
1. optional Level 6 `closure pack generator`
2. optional Level 6 `runtime ui_events + execution-doc join layer`
3. optional Level 6 `LLM queue triage summaries`
4. optional Level 6 `proof/test artifact auto-linking`

Reason:
- Level 5 automation is now in place
- the next ROI boundary is analysis-native operations, not more of the same document plumbing
- further growth should happen only if the repo actually needs deeper automation

## 6. What Not To Do
- do not keep adding harnesses that duplicate existing ones
- do not jump into fully autonomous planning before automation of the current queue is stable
- do not turn every tiny patch into full process overhead
- do not introduce machine-readable state that humans cannot still audit quickly

## 7. Operating Recommendation
Use two modes going forward.

Mode A. full-governance mode
- for wide surveys, migrations, runtime control-plane changes, persistence changes, and multi-step remediation

Mode B. compact mode
- for narrow bug fixes and small focused patches
- still respect SSOT, canonical/temp rules, and closure honesty, but do not force every advanced artifact unless needed

Safety rule:
- `Recursive Ops Loop` is intent-bounded
- the same rule applies when the user says `ROL` or `rol`
- if the request is "survey only", stop after survey/evidence outputs
- if the request is "execution doc only", stop after canonical + temp execution artifacts and validation
- if the request is "implement/continue", proceed into queue realization and closure flow
- if the request is a narrow patch, prefer compact mode rather than the full-governance path

## 8. Final Recommendation
My recommendation is:

- treat the current state as "foundation plus automation complete"
- keep `Level 4` as the minimum stable operating plateau and `Level 5` as the current implemented ceiling
- do not add more process layers unless they serve Level 6 analysis-native outcomes
- delay deeper Level 6 work until the actual runtime/operator trace substrate exists

If we keep going in this order, the result is not "more docs." The result is a reusable operating system for system-track work.
