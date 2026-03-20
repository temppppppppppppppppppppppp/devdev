# ROL Global Integrity Survey

Date: 2026-03-20
Status: draft
Canonical Path: `docs/2026-03-20/rol-global-integrity-survey-3pass-audit.md`
Related Evidence Manifest: `docs/2026-03-20/rol-global-integrity-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 17 untracked; hotspots: geuldobi-desktop/, modules/core/, modules/domain/agents/, docs/2026-03-20/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent

이 survey는 `Opus 5-terminal collector bundle`을 기초 자료로만 사용하고, Codex가 live workspace 기준으로 authority를 다시 세우기 위해 존재한다.

이번 단계의 목표:
- collector draft를 그대로 합치지 않는다
- tranche inventory와 live re-check를 묶어 canonical skeleton을 세운다
- action-bearing area를 좁힌다
- execution SSOT / roadmap이 정말 필요한지 다음 단계에서 결정할 수 있게 만든다

lighter survey가 불충분한 이유:
- collector bundle 사이의 신뢰도 편차가 크다
- 최소 3개 stale 사례가 이미 live code로 확인됐다
- repo 전역에 active modifications가 많아 stale summary가 쉽게 발생한다

## 2. Scope Lock

- included paths:
  - `main_a.py`
  - `modules/`
  - `scripts/`, `tools/`, `tools2/`, `main_tools/`
  - `tests/`
  - `geuldobi-desktop/`
  - `config/`
  - `docs/implementation/`
  - `docs/2026-03-20/opus-collector-*.md`
- excluded paths:
  - `.git/`, `.venv/`, build outputs, `__pycache__/`
  - narrative pipeline outputs themselves as content truth target
- change-lock or canary constraints:
  - 이번 단계는 survey-only
  - execution SSOT, roadmap, code patch는 아직 확정하지 않음
- baseline docs read:
  - system init/full survey/deep integrity harness
  - naming + commit-state contracts
  - collector triage doc

## 3. Coverage Matrix

- macro views covered:
  repo topology, entrypoints, runtime/control-flow spine, desktop/app shell
- micro views covered:
  stage orchestrators, director/validator seams, sink inventories, test/config surface
- cross-cut views covered:
  observability, persistence, operator surface, contracts/config, retry/recovery, subprocess/network, cache/global state, regression/canary, stale authority
- operational views covered:
  desktop contract tests, sink contract tests, prompt/schema tests, smoke/canary inventory
- deferred surfaces:
  fresh live run merge
  generated artifact truth across representative runs
  execution-queue synthesis and roadmap

## 4. Macro View

- topology:
  current system still centers on `main_a.py` + stage orchestrators + desktop bridge/app shell
- authority map:
  desktop renderer/main/preload -> bridge server -> process runner -> `main_a.py` -> stage pipeline
- runtime/control-flow spine:
  synchronous stage/menu core with subprocess boundary for desktop-driven runs
- subsystem boundaries:
  - runtime core and stage orchestration
  - domain/agent judgment layer
  - persistence/observability and sink layer
  - operator surface / desktop app shell
  - tests/config/contracts surface

## 5. Micro View

- hotspot ranking:
  1. `main_a.py`
  2. `modules/core/stage4_interview_round.py`
  3. `modules/core/stage2_finalizer.py`
  4. `modules/domain/agents/director_ensemble.py`
  5. `modules/api/bridge_server.py`
  6. `geuldobi-desktop/src/index.html`
- dominant mutable state surfaces:
  - stage context snapshots and write-back seams
  - JSONL/DB sink fan-out
  - desktop renderer shell state
  - agent-local cache / class-level shared cache
- dense side-effect clusters:
  - runtime bootstrap and dotenv/import side effects
  - Stage 4 advisory/retry/repair chain
  - desktop preload/bridge/runtime contract
  - persistence/audit/proof sinks

## 6. Cross-Cut Integrity Matrix

| Cross-Cut Surface | Authority / Owner | Key Touchpoints | Major Side-Effects | Evidence Classes Used | Known Gap | Governing Execution Doc |
| --- | --- | --- | --- | --- | --- | --- |
| Observability | runtime core + session/audit services | `session_logger.py`, `audit_service.py`, `quality_dashboard.py`, `failure_analyzer.py` | JSONL, dashboard, runtime audits | live code + collector D/G + tests | Stage 2 proof coverage and some operator visibility questions remain | pending decision |
| Persistence | DBManager + sink writers | `db_manager.py`, fact/proof/status sinks | DB writes, JSONL append, artifact metadata | live code + collector D/G | sink authority and coverage questions remain | pending decision |
| Operator Surface | desktop/app shell + CLI output | `geuldobi-desktop/`, `studio_visualizer.py`, `ui_service.py` | prompt/output/UI state | live code + collector E + desktop tests | prompt ownership and runtime authority remain high-risk | existing React program for desktop lane |
| Contracts / Config | config manager + contract files | `config/*.yaml`, `response_schemas.py`, desktop contract JSON | drift, threshold semantics, bootstrap assumptions | live code + collector F/H + tests | some collector sync claims were overstated | no new doc yet |
| Recovery / Retry | stage orchestrators + director loops | Stage2/3/4 orchestrators, interview round, finalizers | retry, patch, fail-open/fail-soft | live code + collector A/B/C | policy boundaries remain and should not be flattened | pending focused policy audits |
| Subprocess / Network | desktop/bridge/process runner | `process_runner.py`, `bridge_server.py`, desktop main/preload | subprocess spawn, HTTP, WS, IPC | live code + collector A/B/E | live-run merge not yet done | pending |
| Cache / Global State | runtime core + agents | `main_a.py`, `base_agent.py`, cache holders | singleton/class cache, in-memory mutation | live code + collector A/B/C | thread-safety and degradation behavior need bounded review | pending |
| Regression / Canary | tests + scripts | `tests/`, smoke/canary suites, scripts | real API calls, persistent artifacts, Node subprocess | live code + collector F/H | no fresh whole-bundle run yet | no new doc yet |
| Shadow / Stale Authority | docs/tests/drafts | collector drafts, dated docs, sweep notes | stale counts, stale sync claims | collector triage + live checks | broad stale-reference sweep still deferred | pending |

## 7. Operational and Regression View

- tests:
  suite breadth is high, but collector inventory and live contract counts already diverged on desktop surface numbers
- smoke/canary:
  real API and project-dependent tests still exist and should not be treated as cheap default verification
- repair tooling:
  scripts/tools surface is broad; some mutation scripts bypass DBManager safety abstractions
- read-only vs mutation-heavy boundaries:
  desktop contract tests are relatively clean
  sink/persistence/scripts areas are more mutation-heavy

## 8. Contradiction and Uncertainty Ledger

### Contradictions

| ID | Claim Area | Conflicting Evidence | Current Interpretation | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `C-01` | desktop preload count | collector F/H says `26`; live contract is `25` | collector drift confirmed; use live code only | medium | carry live count forward only | closed |
| `C-02` | Stage 4 advisory worker count | collector A/B says `8`; live code is `9` | collector count stale | medium | use live code only | closed |
| `C-03` | `tools2/` reference coverage | collector D/G undercounts tests referencing `tools2/` | draft inventory incomplete | low | recalc in canonical tests/config pass | closed |

### Uncertainty

| ID | Topic | Missing Proof | Why It Matters | Temporary Bound | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `U-01` | `risk-approval-log.jsonl` authority role | fresh contract decision not yet made | affects persistence/control-plane authority mapping | treat as open contract question, not bug | medium | focused control-plane audit | open |
| `U-02` | xfail/xskip historical count drift | no fresh whole-suite audit count | affects trust in old TF baseline counts | do not reuse old aggregate test counts as authority | low | fresh test meta audit later | open |
| `U-03` | Stage 2 proof/sink alignment depth | no merged live run proof review yet | persistence confidence still partial | bound claims to Stage 3/4 confirmed zones only | medium | live-run merge tranche later | open |
| `U-04` | prompt ownership / runtime authority in desktop | no high-risk runtime isolation tranche yet | blocks deeper React migration authority changes | keep current non-React ownership model | medium | high-risk desktop audit when needed | open |

## 9. Severity and Action Map

- `P0` items:
  none newly established by this triage pass
- `P1` items:
  none newly established as bounded bugfix from collector bundle alone
- action-bearing areas:
  - runtime core / control authority seams
  - persistence / sink governance
  - domain-agent policy boundary verification
  - desktop/operator runtime authority
- areas with `no-execution-doc-required` right now:
  - pure collector draft cleanup itself
  - tests/config inventory only, until a focused drift decision is actually needed

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| runtime core / control authority | action-bearing | pending | needs narrower Codex-owned focused audit before realization |
| persistence / sink governance | action-bearing | pending | depends on `risk-approval-log` and proof coverage decisions |
| domain / agent policy boundaries | action-bearing | pending | mostly policy-bound, not bounded bugfix right now |
| desktop/operator surface | already governed elsewhere | existing React migration doc set | current program docs remain the authority for desktop realization |
| tests/config cross-cut drift | no-execution-doc-required | none | use as verification surface, not an execution lane yet |

## 11. Single SSOT Roadmap Lineage

- canonical roadmap:
  none yet
- temp roadmap mirror:
  none yet
- execution order basis:
  action-bearing areas are identified but not yet reduced into execution SSOT docs
- lane or phase structure:
  defer until at least 2 canonical execution SSOTs are justified

## 12. Confidence Summary

- estimated score: `0.92`
- score rationale:
  - all 5 collector drafts were triaged
  - multiple stale claims were directly re-checked against live code
  - harness and baseline commit state were refreshed
  - but no fresh live run merge exists and no focused execution docs are synthesized yet
- closed gaps:
  - collector trust tiering
  - representative stale claim verification
  - tranche backbone selection
- remaining gaps:
  - fresh live run evidence
  - area execution SSOT synthesis
  - single-roadmap decision
- final statement:
  this document is a draft canonical survey backbone, not yet the final 95% integrity bundle
