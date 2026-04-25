# Repo Spikes Preservation And Removal Preflight Reaudit

Date: 2026-04-25
Status: final - preservation plus removal gate PASS
Canonical Path: `docs/2026-04-25/repo-spikes-preservation-removal-preflight-reaudit.md`
Governing SSOT: `docs/2026-04-25/repo-generated-project-residue-execution-ssot.md`
Current Commit: `f03cadf3042f946ac6487fd8523a7dcecd37932a`
Current Dirty Summary: `clean branch feat/spikes-preservation-cleanup opened from main after PR #24 merge`

## 1. Question

Can the remaining tracked `spikes/` prototype tree be removed without losing useful operator or implementation knowledge?

## 2. Verdict

Pass with preservation. The useful conclusions from the four spike result notes are preserved in this document, and the tracked `spikes/` tree may be removed from the normal source view.

Authorized removal:

```text
spikes/bridge/result.md
spikes/electron/result.md
spikes/pyinstaller/result.md
spikes/pyinstaller/spike_pyinstaller.py
spikes/pyinstaller/spike_pyinstaller.spec
spikes/subprocess/result.md
spikes/subprocess/spike_subprocess.py
```

Future prototype re-entry should be blocked with root-level `spikes/` ignore coverage.

## 3. Current-State Evidence

- Branch: `feat/spikes-preservation-cleanup`
- Head before removal: `f03cadf3042f946ac6487fd8523a7dcecd37932a`
- `git ls-files -- spikes` returns 7 tracked paths, 26468 bytes total.
- Reference scan found no supported runtime dependency on `spikes/`; references are packaging/Ruff exclusions, tests asserting those exclusions, and prior repo-trashbox governance docs.
- `geuldobi-desktop/src/*` and `modules/api/*` are already tracked live implementation surfaces for the relevant bridge/Electron spike outcomes.

## 4. Preserved Spike Conclusions

### Spike 1 - PyInstaller plus sqlite-vec

- Verdict: PASS / GO.
- PyInstaller one-file bundling can include the `sqlite_vec` C extension when `vec0.dll` or `vec0.so` is explicitly added under the bundled `sqlite_vec` directory.
- Required packaging details: include `hiddenimports=["sqlite_vec"]`, keep `upx=False`, and preserve `enable_load_extension(True)` before `sqlite_vec.load(conn)`.
- Operational expectation: a sqlite-vec enabled one-file executable is feasible; expected full-app bundle size remains in the hundreds of MB once numpy and full dependencies are included.

### Spike 2 - subprocess stdin/stdout control

- Verdict: PASS / GO.
- `main_a.py` can be launched through `subprocess.Popen(stdin=PIPE, stdout=PIPE, stderr=STDOUT)` and controlled by writing menu keys through stdin.
- UTF-8 output stayed valid with `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1`, `TERM=dumb`, and `NO_COLOR=1`.
- Important caveat: interactive prompts may flush late through a PIPE, so production bridge logic should parse stable menu/status markers and tolerate delayed prompt text instead of depending only on immediate prompt visibility.
- Recommended production direction: use `asyncio.create_subprocess_exec`, parse `"Select Command"` / `"Choice"` / shutdown markers, and emit `waiting_input` or `prompt_request` events through the bridge.

### Spike 3 - FastAPI bridge skeleton

- Verdict: PASS.
- Uvicorn successfully served the bridge skeleton, and `/status` returned an idle state at startup.
- Request validation was wired to `RunValidator`, risk approval checks were wired to `RiskApprovalGate`, `PromptBroker` loaded through importlib, and `ProcessRunner` state transitions worked as a stub.
- Follow-up already identified by the spike: replace the `ProcessRunner` stub with real subprocess start/read behavior after the subprocess spike passes.

### Spike 4 - Electron splash skeleton

- Verdict: PASS.
- The Electron skeleton produced a splash window, loading animation, main-window transition, backend `/status` polling, fallback transition, and first-run wording branch.
- `ELECTRON_RUN_AS_NODE` must be explicitly cleared in the desktop start path when inherited from the environment.
- Chromium disk-cache permission warnings were observed during the spike but did not block splash display or transition behavior.

## 5. Pass 1 - Inventory

The tracked `spikes/` set is small but mixed: four result notes and three prototype/spec files. The result notes contain useful deployment and bridge decisions; the prototype scripts are one-off verification scaffolds.

Pass 1 result: pass after preserving conclusions above.

## 6. Pass 2 - Runtime Boundary

No supported runtime, formal test, or packaging flow depends on the tracked `spikes/` files. Current packaging and Ruff configuration already treat `spikes/` as excluded prototype surface. The live implementation surfaces are outside `spikes/`.

Pass 2 result: pass.

## 7. Pass 3 - Reviewability And Rollback

The cleanup is reviewable because it removes exactly 7 tracked paths, preserves the useful conclusions in this dated document, updates future ignore coverage, and closes the active temp queue only after validation. Rollback is a normal PR revert.

Pass 3 result: pass.

## 8. Required Post-Removal Validation

- `git ls-files -- spikes`
- `git check-ignore --no-index spikes/example.txt spikes/subprocess/example.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py docs/2026-04-25/repo-spikes-preservation-removal-preflight-reaudit.md docs/2026-04-25/repo-generated-project-residue-execution-ssot.md docs/implementation/surface-containment-contract-v1.json tests/test_surface_containment_contract.py .gitignore`
- `python -m pytest tests/test_surface_containment_contract.py tests/test_runtime_authority_contract.py -q`

Confidence: 96/100
