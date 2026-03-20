# ROL Global Integrity Evidence Manifest

Date: 2026-03-20
Status: draft
Scope: repo-wide Codex re-audit after OPUS 5-terminal collector bundle
Role: evidence inventory only

## 1. Purpose

이 manifest는 OPUS collector draft를 authority로 승격하지 않고, Codex canonical survey가 실제로 어떤 근거를 사용했는지 고정하기 위한 것이다.

## 2. Primary Input Drafts

- `docs/2026-03-20/opus-collector-global-tranche-a-b-macro-runtime-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-c-domain-agents-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-d-g-persistence-scripts-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-e-operator-desktop-ui-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-f-h-tests-config-crosscut-draft.md`
- `docs/2026-03-20/opus-collector-global-survey-bundle-triage-3pass-audit.md`

## 3. Governance / Harness Inputs

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/deep-global-integrity-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/canonical-naming-contract.md`
- `docs/implementation/commit-state-minimal-contract.md`

## 4. Live Re-Checks Performed

### 4.1 Workspace Baseline

- `git rev-parse HEAD` → `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- `git status --porcelain=v1`
  - total entries: `145`
  - tracked/other: `128`
  - untracked: `17`

### 4.2 Desktop / Operator Surface

- `node -e "const c=require('./geuldobi-desktop/src/desktop_control_plane_contract.js'); console.log(c.LIVE_PRELOAD_METHOD_NAMES.length)"` → `25`
- live reference files:
  - `geuldobi-desktop/src/desktop_control_plane_contract.js`
  - `geuldobi-desktop/src/desktop_bridge_client.js`
  - `tests/test_desktop_contract_refresh.py`
  - `tests/test_desktop_preload_bridge_behavior.js`

### 4.3 Runtime / Stage Spine

- `modules/core/stage4_interview_round.py`
  - advisory chain executor currently `ThreadPoolExecutor(max_workers=9)`
- `main_a.py`
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `modules/core/runtime_paths.py`

### 4.4 Domain / Agent Layer

- `modules/domain/agents/analyst.py`
  - direct `self.ask(` live re-check
- `modules/domain/agents/base_agent.py`
  - residual silent-swallow telemetry paths
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`

### 4.5 Persistence / Scripts

- `modules/api/control_plane_contract.py`
- `modules/api/risk_approval.py`
- `tests/test_runtime_authority_contract.py`
- `tests/test_control_plane_approval_provenance_ssot.py`
- `tests/test_surface_containment_contract.py`

## 5. Evidence Classes Used

| Class | Description | Authority Level |
| --- | --- | --- |
| Live code | current workspace source files and contracts | highest |
| Live contract tests | tests that directly assert current runtime contracts | high |
| Collector drafts | OPUS tranche surveys and watchlists | secondary |
| Governance docs | harnesses and contracts for survey procedure | governing process only |

## 6. Known Evidence Corrections Applied

- desktop preload method count:
  collector draft 일부는 `26`으로 적었지만 live contract는 `25`
- Stage 4 advisory worker count:
  collector A/B draft는 `8`이라고 적었지만 live code는 `9`
- `tools2/` reference coverage:
  collector D/G draft의 언급보다 live tests가 더 넓다
- collector dirty-summary counts:
  일부 draft header의 dirty summary는 현재 live worktree와 어긋난다

## 7. Current Use Rule

- collector draft의 inventory/table/map은 참고 가능
- collector draft의 severity, sync/no-drift, contradiction 없음 같은 결론 문구는 직접 채택 금지
- canonical survey에는 반드시 live re-check 근거를 붙인다
