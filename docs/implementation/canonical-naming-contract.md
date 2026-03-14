# Canonical Naming Contract

Date: 2026-03-14
Status: active
Applies To: system-track docs, manifests, roadmaps, scorecards, and closure artifacts

## 1. Purpose
- Keep filenames stable enough for humans and scripts to reason about them.
- Reduce drift caused by one-off naming styles.

## 2. Naming Rules
- use lowercase kebab-case
- keep the topic slug stable across related artifacts
- suffix the artifact role clearly

## 3. Recommended Patterns
- `<topic>-full-survey-audit-order.md`
- `<topic>-3pass-audit.md`
- `<topic>-evidence-manifest.md`
- `<topic>-execution-ssot.md`
- `<topic>-execution-roadmap.md`
- `<topic>-execution-closure.md`
- `<topic>-process-health-scorecard.md`
- `<topic>-stale-reference-sweep.md`

## 4. Temp Names
- `docs/temp/<topic>-execution-ssot.md`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`

## 5. Guardrails
- Do not change topic slugs casually once queue artifacts exist.
- Do not use temp-style names for canonical dated docs.
