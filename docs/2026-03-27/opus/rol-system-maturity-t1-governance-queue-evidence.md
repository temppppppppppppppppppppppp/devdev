# T1 Governance / Queue / Confidence Hygiene - Evidence Manifest

Date: 2026-03-27
Type: evidence manifest (companion to T1 lane report)
Lane: T1 Governance / Queue / Confidence Hygiene

## 1. Live Evidence (current workspace state, 2026-03-27)

| # | Evidence | Source | Classification |
|---|----------|--------|----------------|
| E-01 | `ops_validator.py --strict` passes with 0 errors, 0 warnings | live run of `python scripts/ops_validator.py --strict` | **live** |
| E-02 | `docs/temp/queue-state.json` reports `queue_mode: empty`, `active_item_count: 0`, `items: []` | direct read of `docs/temp/queue-state.json` | **live** |
| E-03 | Zero execution SSOT mirrors in `docs/temp/` | `ls docs/temp/*-execution-ssot*` returns no results | **live** |
| E-04 | No execution roadmap mirror in `docs/temp/` | `ls docs/temp/*-execution-roadmap*` returns no results | **live** |
| E-05 | `docs/temp/README.md` exists and is consistent with current governance rules | direct read | **live** |
| E-06 | Both previously pending execution SSOTs are now `Status: closed` | `db-logging-integrity-post-audit-execution-ssot.md` header shows `closed`; `llm-friendliness-post-survey-execution-ssot.md` header shows `closed` | **live** |
| E-07 | Three 2026-03-27 execution SSOTs are `Status: closed` with temp mirrors removed | `llm-friendliness-gimmick-elegance-clarity-wave1`, `per-work-fact-contract-alignment-wave1`, `wuxia-technique-realm-contract-alignment-wave1` | **live** |
| E-08 | `AGENTS.md` precedence chain is consistent with `operations-governance-map.md` | direct cross-read | **live** |
| E-09 | 35 implementation harness/contract/template files exist in `docs/implementation/` | `Glob docs/implementation/*.md` | **live** |
| E-10 | HEAD commit is `eb7a41d8` with 30+ tracked modified and 19+ untracked files | `git rev-parse HEAD` and `git status --short` | **live** |
| E-11 | docs/temp contains 8 non-queue residual artifacts (narrative pipeline working files) | `ls docs/temp/` — wuxia_block1_check.md, wuxia_heavenly_physician_rebuild*, consumability_scan_raw.json, phase0/stage2/stage3 output files | **live** |

## 2. Recent Evidence (2026-03-27, same day)

| # | Evidence | Source | Classification |
|---|----------|--------|----------------|
| E-12 | chaebol_ent_empire canary report: pair consumability pass, revival canary pass | `docs/2026-03-27/chaebol-ent-empire-revival-canary-report.md` | **recent** |
| E-13 | chaebol_ent_empire stage probe: runtime admission pass, Stage 2/3 pass | `docs/2026-03-27/chaebol-ent-empire-revival-stage-probe-report.md` | **recent** |
| E-14 | 6-terminal LLM friendliness master survey completed and merge-audited | `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-merge-audit.md` | **recent** |
| E-15 | Master maturity-banding order written and 3-pass audited at 97% confidence | `docs/2026-03-27/rol-system-maturity-banding-5terminal-master-order.md` | **recent** |

## 3. Historical Evidence (2026-03-23 and earlier)

| # | Evidence | Source | Classification |
|---|----------|--------|----------------|
| E-16 | Current-state situation survey: `stabilization mode`, queue=1 active item | `docs/2026-03-23/current-state-situation-survey-report.md` | **historical** (queue state is now stale; mode claim still directionally valid) |
| E-17 | Fresh run 3-pass audit: 0 P0, 0 regressions, 4 manuscripts | `docs/2026-03-23/fresh-run-3pass-audit-report.md` | **historical** (valid for exercised-path baseline; 4 days old) |
| E-18 | LLM codebase orientation pack: 97% confidence | `docs/2026-03-23/llm-codebase-orientation-pack.md` | **historical** (structurally valid; detail-level accuracy eroding with dirty source drift) |
| E-19 | TF-static-complexity-audit-v2: 180+=0, 200+=0, 100+=171 | `docs/2026-03-20/TF-static-complexity-audit-v2.md` | **historical** (structural claim still directionally valid but LOC counts need refresh after dirty source changes) |

## 4. Stale or Superseded Evidence

| # | Evidence | Reason |
|---|----------|--------|
| E-20 | 2026-03-23 situation survey `active_item_count: 1` | Queue is now empty; the active item was closed since then |
| E-21 | 2026-03-23 situation survey `Mode: stabilization` | Directionally valid, but the workspace has moved into more advanced activities (multi-provider integration, genre expansion, per-work fact alignment, maturity banding) since this label was assigned |

## 5. Canonical-vs-Temp Integrity Check

| Check | Result |
|-------|--------|
| Execution SSOT mirrors in temp | 0 (clean) |
| Execution roadmap mirror in temp | absent (clean) |
| queue-state.json consistent with temp contents | yes (empty mode, 0 items, matches 0 mirrors) |
| README.md present and accurate | yes |
| Non-queue residual files in temp | 8 narrative pipeline working files (not execution queue artifacts, but semantic clutter) |
| Temp-only authority violations | none detected |
| Canonical-before-mirror rule violations | none detected (all closed SSOTs have canonical counterparts) |

## 6. Governance Chain Integrity Check

| Check | Result |
|-------|--------|
| AGENTS.md is SSOT | yes (CLAUDE.md is shim) |
| Init harness references correct | yes (all 13 companion harnesses listed) |
| Governance map precedence consistent | yes (7-level hierarchy consistent across AGENTS.md and operations-governance-map.md) |
| Document 3-pass gate stated | yes (in AGENTS.md, system-full-survey-execution-harness.md, document-3pass-audit-harness.md) |
| 95% confidence gate stated | yes (in all relevant harnesses) |
| Canonical-vs-temp policy stated | yes (in AGENTS.md, operations-governance-map.md, README.md) |
| Live-evidence-beats-stale-survey stated | yes (in AGENTS.md and operations-governance-map.md) |
| Commit-state minimal contract referenced | yes (in init harness, survey harness) |
| Queue priority rubric available | yes |
| Closure harness available | yes |
| Exception registry available | yes |
| Stale reference sweep available | yes |
| Process health scorecard available | yes |

## 7. Contradiction Notes

| # | Contradiction | Severity |
|---|--------------|----------|
| C-01 | 2026-03-23 situation survey says queue has 1 active item; live queue is empty | **resolved** (item was closed since survey) |
| C-02 | 2026-03-23 situation survey says `stabilization mode`; live workspace activity suggests early optimization | **open** (mode label not formally updated) |
| C-03 | per-work-fact and wuxia-technique execution SSOTs declare `Temp Mirror Path: docs/temp/...` but those mirrors were removed; the metadata field still references the temp path | **cosmetic** (correct behavior per closure protocol — mirror removed, canonical updated) |
| C-04 | docs/temp contains 8 non-queue narrative pipeline working artifacts that are not covered by the README's "recommended contents" list | **low** (not governance violations, but semantic clutter) |
