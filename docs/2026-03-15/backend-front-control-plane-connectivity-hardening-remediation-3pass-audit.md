# Backend-Front Control-Plane Connectivity Hardening Remediation 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
Temp Mirror Follow-On: `docs/temp/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active roadmap/temp docs, menu7/runtime/frontier edits, post-remediation bundle docs, unrelated pdf/style/log artifacts, and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `implementation landed for live getStatus promotion, queued prompt replay, status snapshot resync, explicit bridge timeout, targeted regression coverage, and minimal desktop runtime proof via start:spike`
Source Evidence:
- `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`
- `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
- `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `modules/api/bridge_server.py`
- `modules/api/prompt_broker.py`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_bridge_server_http_contract.py`
- `tests/test_desktop_transport_contract.py`

## 1. Intent
- Re-audit the `backend-front/control-plane` execution lane after implementation.
- Confirm that the realized patch set actually closed command-readiness drift, prompt concurrency loss, reconnect snapshot ambiguity, and bridge timeout ambiguity without widening into unrelated runtime or persistence work.
- Decide honestly whether the lane can be closed.

## 2. Pass 1. Structure And Scope
- Document type is correct:
  - this is a post-implementation 3-pass audit for an existing execution SSOT
- Scope remains explicit:
  - included: renderer run/stop gating, prompt replay/queue policy, bridge-managed `getStatus` authority, `/status` reconnect snapshot shape, bridge fetch timeout semantics, and minimal desktop smoke proof
  - excluded: `main_a.py` prompt contracts, persistence shutdown, broad websocket protocol redesign, and packaged build validation
- Output shape is proportionate:
  - one bounded patch set across desktop/control-plane files and targeted tests
  - one runtime smoke command for minimum handoff proof

Pass 1 judgment:
- pass

## 3. Pass 2. Evidence And Consistency
- Command-path readiness drift is closed in source:
  - `geuldobi-desktop/src/index.html` no longer blocks `runKey()` and `stopRun()` on websocket-open state alone
  - `window.geuldobiDesktop.getStatus()` now drives explicit command-path/resync checks
- Prompt concurrency drift is closed:
  - the renderer now keeps `_pendingPromptQueue`
  - concurrent prompt requests are queued instead of silently dropped
  - `PromptBroker.snapshot_run()` and `/status` expose unresolved prompt payloads for reconnect recovery
- Contract drift is closed:
  - `getStatus` moved from dead-candidate to live in `desktop_control_plane_contract.js`, `preload.js`, and `docs/implementation/desktop-ipc-surface-contract-v1.json`
  - `docs/implementation/api-contract-v1.yaml` now documents `request_timeout_ms` plus optional reconnect snapshot fields on `/status`
- Verification evidence exists:
  - `python -m pytest tests/test_bridge_server_http_contract.py`
  - `python -m pytest tests/test_desktop_shadow_hygiene.py tests/test_desktop_transport_contract.py tests/test_desktop_direct_surface_contract.py`
  - `npm run start:spike` completed with splash window show, backend startup, and timed auto-close

Pass 2 judgment:
- pass

## 4. Pass 3. Realization Shape
- The realized fix stayed bounded:
  1. `getStatus` is now a live renderer-consumed surface
  2. run/stop now use the bridge path even when websocket reconnect is pending
  3. reconnect can restore pending prompt state from `/status` without inventing a new websocket event type
  4. `bridgeFetch()` now aborts on an explicit timeout that matches the documented contract
- Residual risk is bounded and disclosed:
  - this turn added a minimum desktop runtime smoke, not a long-form interactive desktop canary
  - no packaged-build smoke was run
- Closure quality is sufficient:
  - source, contract, and HTTP regressions are covered
  - minimum handoff runtime proof exists

Pass 3 judgment:
- pass

## 5. Confidence And Save Gate
- Pass 1 structure and scope: pass
- Pass 2 evidence and consistency: pass
- Pass 3 realization shape: pass
- Estimated confidence: `96%`
- Save decision: final save allowed

## 6. Audit Conclusion
- The lane has been realized and verified.
- `getStatus` is now the authoritative bridge-managed resync surface instead of websocket open-state alone.
- The execution SSOT may be marked `closed`, its temp mirror may be removed, and the master roadmap may move the queue to the next lane.
