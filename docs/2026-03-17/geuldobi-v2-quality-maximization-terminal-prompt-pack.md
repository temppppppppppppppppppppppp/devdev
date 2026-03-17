# Geuldobi V2 Quality Maximization Terminal Prompt Pack

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-prompt-pack.md`
Document Type: operator prompt pack
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: stage-pipeline lane1~3 code/tests/docs edits, temp execution mirror deletions, 1 runtime log, 1 untracked roadmap draft; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Authorities:
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-terminal-launch-shortform.md` is the minimal operator launcher companion

## 1. Purpose
- provide launch-ready copy-paste prompts for terminals `T01` to `T10`
- keep all workers aligned to the same survey-only order
- prevent workers from treating `docs/roadmap-v2.md` as direct authority

## 2. Launch Sequence
Recommended order:

1. launch `T10` first so the merge terminal loads the governing docs and waits for worker evidence
2. launch `T01` to `T03` for macro and upstream mapping
3. launch `T04` to `T06` for CW/Director/persistence deep dive
4. launch `T07` to `T09` for operator surface, regression/tooling, and cost/config cross-cut work
5. when worker artifacts exist, let `T10` start contradiction closure and synthesis watchlisting

## 3. Shared Launch Notes
- all terminals are system-track
- all terminals are `survey-only`
- no terminal may patch code or open execution SSOT/roadmap artifacts in this phase
- worker terminals may save only raw evidence artifacts
- `T10` is the only synthesis authority
- `docs/roadmap-v2.md` is a draft seed, not the governing source

## 4. Prompt: T01

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T01`
- primary mission: repo topology, entrypoints, authority map
- primary paths: root, `main_a.py`, `main.js`, top-level subsystem roots
- theme anchor: global topology
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- do not deep-audit Stage 2/3/4 semantics already owned by T03 to T05
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 5. Prompt: T02

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T02`
- primary mission: bootstrap, runtime spine, process runner, fallback seams
- primary paths: `main_a.py`, `modules/core/`, `modules/api/`, `lite_mode/`, `test_mode/` entrypoints
- theme anchor: runtime control-flow
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- keep detailed CW/Director quality semantics in T04/T05
- focus on bootstrap, steady-state flow, fallback seams, and process-runner boundaries
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 6. Prompt: T03

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T03`
- primary mission: Stage 2/3 upstream design quality and information handoff
- primary paths: `modules/core/stage2_*`, `modules/core/stage3_*`, related tests
- theme anchor: upstream Stage 2/3 design quality
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- prioritize triage `keep` themes `테마 D`, `테마 L`, and related upstream intent survival
- logging review is required only when triage logging packs make it necessary
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 7. Prompt: T04

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T04`
- primary mission: CW input quality, context layering, prompt structure, truncation
- primary paths: `modules/core/stage4_context_builder.py`, `modules/core/context_advisor.py`, CW prompt surfaces
- theme anchor: input quality + prompt structure + truncation
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- prioritize triage `keep` themes `절삭 하드코딩 전수조사`, `테마 N`, and CW-side portions of `테마 D`
- if logging review is needed, use the triage doc's `Pack A` and `Pack C`
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 8. Prompt: T05

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T05`
- primary mission: Director, validators, gate semantics, PASS_WITH_FIX, retry policy
- primary paths: `modules/core/stage4_interview_round.py`, `modules/domain/agents/`, `modules/validation/`, `modules/core/adaptive_retry.py`
- theme anchor: feedback quality + taxonomy/semantic loss
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- treat lane-1~3 core changes as already landed; validate them rather than re-inventing them
- prioritize triage `keep` themes `테마 G`, `테마 H`, `테마 I`, and repair/gate validation adequacy
- if logging review is needed, use the triage doc's `Pack B`
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 9. Prompt: T06

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T06`
- primary mission: persistence, durability, artifact truth, metadata truth
- primary paths: `modules/core/stage4_post_processor.py`, `modules/core/world_state.py`, persistence/logging surfaces, `projects/` runtime artifacts
- theme anchor: durability + long-run integrity
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- prioritize artifact truth, metadata truth, and durable sink linkage
- evaluate logging adequacy only where the triage doc requires it
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 10. Prompt: T07

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T07`
- primary mission: operator-visible surface and app shell linkage
- primary paths: `UI/`, `geuldobi-desktop/`, `modules/core/quality_dashboard.py`, `modules/core/pass_rate_monitor.py`, `modules/api/bridge_server.py`
- theme anchor: operator surface
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- focus on what operators can reconstruct from existing surfaces
- do not escalate into unrelated broad product review
- evaluate logging sufficiency only insofar as it becomes operator-visible state
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 11. Prompt: T08

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T08`
- primary mission: tests, smoke/canary, scripts, repair tooling, verification economics
- primary paths: `tests/`, `scripts/`, root helpers, smoke runners
- theme anchor: regression surface + utility tooling
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- map verification surfaces and economics, not just test counts
- note whether existing tests can validate triage `keep` themes or only landed lane regressions
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 12. Prompt: T09

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution SSOT creation
- no roadmap creation

Authority:
- live code > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- use the triage doc to ignore `merge`, `defer`, and `out-of-scope` seeds unless live evidence revives them

Your terminal assignment:
- terminal: `T09`
- primary mission: cross-cut contracts/config, model routing, thresholds, cost/latency duplication, long-context policy
- primary paths: `config/`, prompt maps, shared constants, routing/config surfaces across repo
- theme anchor: cost/latency + long-context + contract drift
- required output: `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`

Required output format:
1. scope
2. included paths
3. excluded paths
4. facts
5. hotspot files
6. side-effect notes
7. contradictions or uncertainty
8. candidate execution areas
9. follow-up requests for another terminal

Rules:
- prioritize triage `keep` themes `절삭 하드코딩`, `테마 J`, `테마 K`, and config/contract aspects of `테마 N`
- if logging review is needed, use the triage doc's `Pack D` and `Pack E`
- separate Fact / Inference / Open Question
- explicitly mark not-applicable side-effect categories
- do not overwrite another terminal's evidence file
```

## 13. Prompt: T10

```text
You are Codex operating in `c:\Users\wjjo\Desktop\글도비`.

This is a system-track survey-only synthesis order. Follow `AGENTS.md` exactly.

Read first:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-full-survey-audit-order.md`
- `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
- `docs/roadmap-v2.md`

Operating mode:
- `ROL 전역 전체 전수조사만`
- survey-only
- no code edits
- no execution realization

Authority:
- live code and worker evidence > prior notes
- `docs/roadmap-v2.md` is only a thesis seed
- the triage doc is the seed filter
- the audit-order doc is the operating authority

Your terminal assignment:
- terminal: `T10`
- primary mission: merge, contradiction closure, confidence scoring, execution-doc mapping
- worker inputs:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t01-topology-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t02-runtime-spine-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t03-upstream-design-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t04-cw-input-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t05-director-repair-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t06-persistence-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t07-operator-surface-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t08-regression-tooling-evidence.txt`
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t09-contracts-cost-evidence.txt`
- watchlist output:
  - `docs/2026-03-17/geuldobi-v2-quality-maximization-t10-merge-watchlist.txt`

Rules:
- do not create a second roadmap authority
- do not finalize the survey until 3-pass audit + confidence >=95
- do not synthesize critical P1 claims from one evidence class only
- record contradictions explicitly instead of silently choosing one side
- if worker evidence is insufficient, issue targeted delta-read requests instead of expanding scope
- create execution SSOTs only if the merged survey later proves action-bearing areas and only after the survey is finalized
```

## 14. Stop Line
- this prompt pack is for launching the survey
- it does not authorize execution realization
- temp mirrors and roadmap artifacts wait until the merged survey is final and action-bearing areas are confirmed

## 15. Confidence Statement
- estimated confidence in this prompt pack as an operator document: `97%`
- rationale:
  - every prompt is aligned to the same audit-order and triage authorities
  - worker overlap is bounded
  - synthesis authority is singular
  - stop-line is explicit
