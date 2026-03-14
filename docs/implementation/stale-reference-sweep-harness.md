# Stale Reference Sweep Harness

Date: 2026-03-14
Status: active
Applies To: system-track governance changes and process-document maintenance
Automation:
- `python scripts/run_stale_reference_sweep.py`

## 1. Purpose
- Standardize sweeps for stale references after SSOT or process changes.
- Reduce drift caused by historical mentions of outdated authorities, paths, or counts.
- Keep compatibility shims intentional instead of accidental.

## 2. When To Use
Use this harness when one or more of the following is true:
- `AGENTS.md` or a major harness changed meaning
- a new SSOT or governance rule was introduced
- a compatibility shim such as `CLAUDE.md` was altered
- the user asks for a cleanup of stale references or old process guidance

## 3. Sweep Targets
Inspect for:
- references that still treat `CLAUDE.md` as authority rather than shim
- references to removed or renamed harness files
- outdated path policy statements about `docs/temp/`
- stale execution counts or snapshots presented as current facts
- old operational phrases that conflict with the current queue or closure model

## 4. Suggested Commands
Examples:

```powershell
rg -n "CLAUDE\.md|AGENTS\.md|execution-roadmap|docs/temp" AGENTS.md CLAUDE.md docs
```

```powershell
rg -n "ready for implementation|execution-ready|closed" docs/temp docs/20*
```

Tailor the pattern to the specific governance change being audited.

## 5. Triage Rules
- keep references that are explicitly historical or compatibility-only
- update active operational documents that still point to stale authorities
- do not blindly replace historical citations that are part of archival context
- if a dated survey contains an old count, label it as historical rather than silently rewriting history

## 6. Outputs
Recommended outputs:
- `docs/YYYY-MM-DD/<topic>-stale-reference-sweep.md`
- `docs/YYYY-MM-DD/<topic>-stale-reference-findings.txt`

## 7. Guardrails
- Do not mass-edit old docs without checking whether they are meant to remain historical records.
- Do not delete compatibility shims only because stale references exist.
- Do not claim a governance migration is complete without checking active implementation docs.
