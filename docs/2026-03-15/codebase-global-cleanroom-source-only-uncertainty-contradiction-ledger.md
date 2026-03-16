<!-- [참고자료] -->
# codebase-global-cleanroom-source-only Uncertainty And Contradiction Ledger

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/codebase-global-cleanroom-source-only-uncertainty-contradiction-ledger.md`

## Contradictions

| ID | Claim Area | Conflicting Evidence | Current Interpretation | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `C-01` | Source-text hygiene | direct reads show mojibake in active files, while `scripts/check_utf8_hygiene.py` also flags legitimate Korean question prompts | active source contains real corruption in some files, and the hygiene gate still has residual false positives | bounded; no hard cap because the claim is triangulated by direct reads plus gate output | repair corrupted strings/comments file-by-file and narrow the detector grammar again | open |
| `C-02` | Operator prompt authority | `main_a.py` still contains many raw `input(...)` sites, while `UIService` and `StudioVisualizer` provide wrapper prompt surfaces and bridge mode adds `PromptBroker` | prompt handling is split across at least four authorities and is not centralized today | bounded; action-bearing | stabilize backend-front transport first, then unify console and wrapper prompt contracts behind one prompt authority | open |
| `C-03` | UI runtime footprint | top-level `UI/` is the largest tree by bytes, but most visible runtime logic sits in `geuldobi-desktop/src` and Python services | `UI/` is primarily asset weight, not the main active operator-control logic | closed | none beyond explicit exclusion from action priority | closed |
| `C-04` | Hotspot ranking | `geuldobi-desktop/src/splash/lucide.js` is the largest file, but it is vendor-like splash support rather than the desktop control plane | do not let raw line count alone drive roadmap priority | closed | keep file visible in inventory but exclude it from top-priority remediation lanes | closed |
| `C-05` | Backend-front readiness | renderer run actions require `_backendConnected`, while `runKey()` actually uses preload -> Electron main -> HTTP bridge rather than websocket transport | desktop command readiness is currently conflated with event-stream readiness | bounded; action-bearing | split command-path health from websocket-path health and define an explicit resync rule | open |
| `C-06` | Prompt lifecycle concurrency | `PromptBroker` tracks multiple pending prompt IDs per run, while renderer ignores `prompt_request` when a dialog is already open | prompt concurrency is supported upstream but not honored in the renderer transport contract | bounded; action-bearing | choose and implement one policy: queue, upstream reject, or explicit replace; silent drop is not acceptable | open |

## Uncertainty

| ID | Topic | Missing Proof | Why It Matters | Temporary Bound | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `U-01` | Runtime reproduction | no logs, DB artifacts, or completed fresh run evidence were used | source-only findings should not be overstated as runtime-confirmed failures | limit claims to static architecture, text hygiene, and authority fragmentation | bounded only; does not block final source-only survey | follow with live-merge or bounded smoke after execution docs are realized | open |
| `U-02` | Test coverage depth | heuristic category tags do not prove assertion quality or scenario completeness | hotspot modules may still outgrow regression protection | use tests only as operational coverage indicators, not as proof of correctness | bounded only | do focused coverage audit per execution lane | open |
| `U-03` | Asset liveness | source-only sweep cannot prove which `UI/` assets are dead, bundled, or user-facing today | prevents overclaiming asset cleanup ROI | keep `UI/` out of the first remediation wave | none beyond scope bound | separate asset-liveness survey if requested | open |
| `U-04` | Config route liveness | static references do not prove every prompt/config asset is loaded in current runtime | affects blast-radius estimates for contract/config changes | treat config and prompt maps as supporting surfaces, not the first change substrate | bounded only | verify active loads during later runtime-focused audit | open |
| `U-05` | Reconnect state resync | static sweep found websocket reconnect plus quality-summary refresh, but no active renderer consumer of `getStatus()` and no prompt replay or active-run snapshot restore | fresh runs can lose visibility or input state after transient disconnects even if the subprocess survives | keep the claim at "missing explicit contract" rather than runtime-confirmed data loss | bounded only | define one reconnect policy in the backend-front connectivity lane and add regression coverage | open |
| `U-06` | Desktop timeout coherence | splash polling uses `AbortSignal.timeout(5000)`, while `bridgeFetch()` has no timeout and API key validation uses a separate direct renderer fetch | user-visible hang behavior and diagnostics may differ across seemingly similar readiness paths | keep the claim at transport-policy inconsistency, not measured UX duration | bounded only | unify or explicitly separate timeout/error-envelope policy across splash, bridgeFetch, and approved direct fetches | open |
