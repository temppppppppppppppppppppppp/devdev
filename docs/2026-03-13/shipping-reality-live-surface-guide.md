# Shipping Reality + Live Surface Guide

Status: current shipping freeze for the 2026-03-14 workspace

This guide is the operator-facing freeze for the current desktop shipping model and live surface split.
It does not replace the lower-level contracts in `docs/implementation/*.json`; it binds them into one release-facing view.

## Shipping Reality

- Runtime model: `source_bundle_primary`
- Authoritative Electron entry: `geuldobi-desktop/src/main.js`
- Authoritative package loader: `geuldobi-desktop/package.json`
- Packaged backend binary: `resources/backend/backend.exe`
- Packaged engine entry: `resources/engine/main_a.py`
- Packaged Python runtime: `resources/python-embed/python.exe`
- `engine.exe` is not the shipped primary runtime artifact.

## Live / Shadow / Alternate Surface Map

| Path | Classification | Meaning |
| --- | --- | --- |
| `geuldobi-desktop/src/main.js` | live | Current Electron main entry |
| `geuldobi-desktop/package.json` | live loader | Current package entry and desktop gate script source |
| `geuldobi-desktop/main.js` | shadow | Compatibility shim only; forwards to `src/main.js` |
| `main.js` | shadow | Manual debug shadow entry only; not a shipping/runtime source of truth |
| `lite_mode/` | alternate manual-only | Manual UI discovery and alternate operator probes |
| `test_mode/` | alternate manual-only | Experimental/manual UI discovery and alternate probes |
| `UI/` | reference archive | Reference asset archive, not runtime code |

## Desktop Test Envelope

- `npm --prefix geuldobi-desktop test` is the official desktop subset gate.
- `npm --prefix geuldobi-desktop run test:desktop-contract` is the explicit alias for the same gate.
- It is a curated subset for desktop bridge, contract, risk, runtime-path, packaging, and shadow hygiene checks.
- It is not the full repo regression envelope.
- `npm run start:spike` is the minimum runtime handoff proof for splash -> backend -> main window.
- `npm run start:desktop-spike` is the explicit alias for that same runtime proof.

## Release Reading Rules

- Treat `geuldobi-desktop/src/main.js` as the only active Electron main entry.
- Treat `geuldobi-desktop/main.js` and root `main.js` as non-authoritative shadow surfaces.
- Treat `lite_mode/` and `test_mode/` as alternate/manual-only tracks unless a later SSOT promotes them.
- Treat `UI/` as a reference/archive surface, not a live renderer/backend entry.

## Bound Contracts

- `docs/implementation/desktop-runtime-contract-v1.json`
- `docs/implementation/surface-containment-contract-v1.json`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
