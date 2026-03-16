<!-- [참고자료] -->
# Runtime Operator Prompt Authority Chain

Date: 2026-03-15
Status: final
Scope: `TF-011` runtime/operator surface unification
Related Execution SSOT: `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`

## 1. Purpose
- Fix the remaining prompt-authority ambiguity after menu `7` and backend-front transport repairs were already closed.
- Define one operator-facing prompt contract for the live runtime path.

## 2. Live Authority
### CLI / Console Path
```text
main_a.py continuation / skip / pause prompts
ProjectService destructive prompts
    -> SovereignApp facades (_get_int_input / _get_choice_input / _confirm / _pause)
    -> UIService
    -> StudioVisualizer.prompt()
    -> operator console input
    -> hidden prompt_response / selection telemetry
    -> session logger + ui_events sink
```

Rules:
- `main_a.py` does not own raw `input(...)` anymore.
- `ProjectService` uses injected prompt callbacks in the live app path.
- `UIService` is the shared authority for int, choice, confirm, and pause semantics.
- `StudioVisualizer.prompt()` remains the canonical console renderer and hidden `prompt_response` emitter.

### Desktop Broker Path
```text
renderer prompt overlay
    -> preload resolvePrompt / getStatus
    -> Electron main bridge
    -> FastAPI bridge_server
    -> PromptBroker
    -> PromptState(asyncio.Event)
    -> waiting backend task resumes
```

Rules:
- Desktop prompt transport ownership stays in the backend-front/control-plane lane.
- Runtime/operator only documents how that brokered prompt loop fits the global authority chain.
- `getStatus` remains the bridge-managed resync surface for reconnect snapshots.

## 3. Telemetry Contract
- Visible prompt text is emitted once through the prompt authority surface.
- Hidden raw response telemetry uses `event_kind=prompt_response`.
- Hidden normalized int selections use `event_kind=selection` with label `[int_input_selected]`.
- Service-local destructive confirmations should not invent a second telemetry format.

## 4. Bounded Exceptions
- `UIService` keeps one local `input(...)` fallback for non-visualizer contexts and tests.
- `ProjectService` keeps fallback prompt behavior only when callback injection is absent.
- `StudioVisualizer.menu()` still owns its direct console menu input surface.

## 5. Acceptance Mapping
- `main_a.py` raw prompt bypasses: removed from the live runtime path.
- `ProjectService` destructive prompt bypasses: routed through injected shared callbacks in the live runtime path.
- Hidden telemetry drift: reduced by reusing the same prompt authority surface for choice/confirm/pause flows.
- Desktop broker context: documented, but not re-owned here.
