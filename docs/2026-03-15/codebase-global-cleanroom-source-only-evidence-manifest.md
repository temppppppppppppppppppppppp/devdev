<!-- [참고자료] -->
# codebase-global-cleanroom-source-only Evidence Manifest

Date: 2026-03-15
Status: final
Topic: `codebase-global-cleanroom-source-only`
Related Survey Docs: `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md`; `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Related Execution Docs: `docs/2026-03-15/source-text-utf8-hygiene-remediation-execution-ssot.md`; `docs/2026-03-15/backend-front-control-plane-connectivity-remediation-execution-ssot.md`; `docs/2026-03-15/runtime-operator-surface-unification-remediation-execution-ssot.md`; `docs/2026-03-15/persistence-observability-boundary-remediation-execution-ssot.md`

## 1. Summary
- evidence scope: current source tree only across `main_a.py`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, and `config/`
- freshness note: all evidence was collected against the live workspace on 2026-03-15 at baseline commit `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- known gaps: no historical docs, no live logs, no DB artifacts, and no run-state evidence were used as claim authority

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-source-inventory.txt` | inventory | Python path sweep | fresh | survey + execution | top-level scope counts and subtree sizing |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-hotspot-ranking.txt` | inventory | line-count sweep | fresh | survey + execution | hotspot ranking; vendor-like splash file kept visible but not auto-prioritized |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-surface-anchor-inventory.txt` | inventory | `rg` + direct reads | fresh | survey + execution | entrypoints, prompts, persistence, bridge, regression anchors |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-side-effects.txt` | side-effect map | source-only manual synthesis | fresh | survey + execution | default side-effect categories closed for all major surfaces |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-backend-front-connectivity.txt` | focused evidence | control-plane source sweep | fresh | survey + execution | renderer/preload/main/bridge/prompt-broker connectivity and fresh-run risk anchors |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-cross-cut-integrity-matrix.md` | matrix | survey synthesis | fresh | survey + roadmap | cross-cut ownership, gaps, and execution-doc mapping |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-uncertainty-contradiction-ledger.md` | ledger | survey synthesis | fresh | survey + roadmap | bounded contradictions and uncertainty caps |
| `docs/2026-03-15/codebase-global-cleanroom-source-only-3pass-audit.md` | audit | document review | fresh | survey governance | explicit pass1/pass2/pass3 and confidence rationale |

## 3. Limitations
- This manifest intentionally excludes prior dated survey docs, run logs, DB files, and project artifacts from authority.
- Source-only severity claims are bounded to static evidence and do not assert runtime reproduction by themselves.
