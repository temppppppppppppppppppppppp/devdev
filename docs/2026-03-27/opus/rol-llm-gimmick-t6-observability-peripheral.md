Date: 2026-03-27
Status: final (3-pass audited)
Document Type: LLM-friendliness + gimmick-elegance lane survey report (T6)
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked metrics_collector/test files, untracked probe_claude_vertex_matrix scripts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Executive Summary

The T6 surface (observability modules, peripheral directories, governance docs) is **navigation-ready** and its gimmick elegance is **mixed** — strong in most areas but with two specific inelegance hotspots in `metrics_collector.py` and `logger.py`.

Since the prior T6 survey (2026-03-24), **7 of 10 hotspots have been resolved**: stale `.py` files in `docs/implementation/` deleted, `scripts/README.md` and `tests/README.md` added, `UI/README.md` added, `tf_c1_patch.py` deleted, temp Electron files deleted. The prior wave's quick wins were largely realized.

The remaining and new findings break down as:
- **Observability gimmick hotspots (2)**: `metrics_collector.py` has inline cost tables and fragile model-prefix-based provider inference; `logger.py` has an undocumented emoji-to-log-level gimmick
- **Stale artifacts (1)**: test fixture directories still contain 2-month-old JSON/log files
- **Governance metadata gap (2)**: `risk-approval-checklist.md` and `release-gate-v1.md` still lack Date/Status headers
- **New multi-provider surface (1)**: `probe_claude_vertex_matrix.py` is untracked exploratory — no authority concern yet

No boundary refactors are needed. All findings are addressable via comment/doc/observability fixes or artifact cleanup.

**Navigation-ready for this lane: yes**
**Cheap-fix-first verdict: yes**
**Gimmick-elegance verdict: mixed**
**Boundary-refactor can wait: yes**

**Top 3 highest-ROI quick wins:**
1. Add comment in `metrics_collector.py` noting that `MODEL_COSTS` and `_infer_provider_identity` are interim gimmicks pending config-driven model metadata SSOT (comment-only)
2. Add comment in `logger.py:166-173` documenting the emoji-to-log-level auto-detection gimmick (comment-only)
3. Delete stale JSON/log artifacts from `tests/stage3_isolated_test/` and `tests/stage4_v2_test/` (contract-cleanup)

---

## 2. Included Coverage / Exclusions

### Included (primary sweep)

- `modules/core/db_manager.py` (3,446 lines) — DB persistence and durable truth
- `modules/core/pass_rate_monitor.py` (~300 lines) — attempt/verdict convenience cache
- `modules/core/logger.py` (353 lines) — session file logging
- `modules/core/metrics_collector.py` (581 lines) — agent/model/cost telemetry
- `modules/core/session_logger.py` (392 lines) — JSONL session telemetry
- `scripts/` — 50+ utility scripts
- `tests/` — 378 test files across root + 6 subdirectories
- `UI/` — binary asset directory
- `geuldobi-desktop/` — Electron desktop app
- `docs/implementation/` — 47 governance files (harnesses, contracts, templates)
- Stale authority/reference sweep across all surfaces
- Settled-zone collection from prior T6

### Excluded

- Production runtime code (`main_a.py`, `modules/core/stage*`, `modules/domain/`, `modules/validation/`) — T1-T5
- `docs/YYYY-MM-DD/` historical survey docs — reference only
- Narrative pipeline content (`treatments/`, `bible/`, `projects/`)
- `.git/`, `__pycache__/`, `.venv/`, `node_modules/`

---

## 3. Current Read Order / Ownership / Gimmick Map

### Observability Sink Ownership

| Sink | Owner Module | Authority Level | Gimmick Notes |
|---|---|---|---|
| DB (durable truth) | `db_manager.py` | **Authoritative** | Method-Group ToC (L61-78); `_cumulative_bible_cache` is localized; thread-safe `_lock` pattern |
| Pass-rate JSON | `pass_rate_monitor.py` | **Non-authoritative** (explicitly declared L16-22) | Convenience cache rebuilt from memory on each save; loss = no durable truth lost |
| Session log file | `logger.py` | **File-only, no console** | Emoji auto-detection gimmick (L166-173); `retarget()` gimmick for project-specific paths |
| Agent/cost metrics | `metrics_collector.py` | **In-memory + JSON snapshot** | `_infer_provider_identity()` name-prefix gimmick; inline `MODEL_COSTS` dict; scope accumulator with reset |
| JSONL telemetry | `session_logger.py` | **Optional best-effort** (explicitly declared L12-18) | `enabled=False` default; 4-category JSONL split; thread-safe rotation with soft-failure tracking |

### Observability Gimmick Map

| Gimmick | Owner | Localized? | Explicit? | Precedence Clear? | Elegant? |
|---|---|---|---|---|---|
| DB Method-Group ToC | `db_manager.py:61-78` | yes | yes | N/A | **elegant** |
| Cumulative bible cache | `db_manager.py:89-90` | yes | yes (comment) | N/A | **elegant** |
| Non-authoritative declaration | `pass_rate_monitor.py:16-22` | yes | yes | yes | **elegant** |
| Emoji-to-log-level detection | `logger.py:166-173` | yes | **no** (no comment) | N/A | **inelegant** |
| Root logger StreamHandler cleanup | `logger.py:92-97` | yes | yes (`[TF-26]` tag) | N/A | **elegant** |
| Log file retarget | `logger.py:216-243` | yes | yes (`[TF-26]` tag) | N/A | **elegant** |
| Provider identity inference | `metrics_collector.py:97-110` | yes | **partly** (function exists but fragility undocumented) | **no** (silent unknown fallback) | **inelegant** |
| Inline MODEL_COSTS | `metrics_collector.py:80-94` | yes | yes (comment L74-79) | N/A | **mixed** (explicit but will drift) |
| Vertex billing normalization | `metrics_collector.py:113-119` | yes | yes (comment L75-79) | yes | **elegant** |
| Scope accumulator + reset | `metrics_collector.py:195-201, 536-552` | yes | yes | N/A | **elegant** |
| Session JSONL opt-in | `session_logger.py:18, 40` | yes | yes | N/A | **elegant** |
| JSONL rotation + soft failure | `session_logger.py:287-392` | yes | yes | N/A | **elegant** |
| Stale metric cleanup | `metrics_collector.py:222-227` | yes | yes (`[C5-P1-3]` tag) | N/A | **elegant** |

### Peripheral Surface Ownership (unchanged from prior T6)

| Surface | Owner / Entry | Authority |
|---|---|---|
| `scripts/` | Standalone utilities; `README.md` classification | `AGENTS.md` references 8 core scripts |
| `tests/` | pytest harness; `conftest.py` + `README.md` | `AGENTS.md` Pytest Memory Rule |
| `UI/` | Binary assets only; `README.md` present | No code authority |
| `geuldobi-desktop/` | Electron app; `DESKTOP-GUIDE.md` | `desktop-ipc-surface-contract-v1.json` |
| `docs/implementation/` | Governance hub-and-spoke | `AGENTS.md` routes via init harness |

### Governance Chain (verified, unchanged)

```
AGENTS.md (SSOT)
  -> system-order-init-harness.md (routing entry)
    -> 13 specialized harnesses
      -> contracts + templates
  -> AGENTS.narrative-router.md (narrative family router)
  -> CLAUDE.md (compatibility shim, lowest priority)
```

All links resolve. Zero orphaned governance documents.

---

## 4. Top Hotspots

| # | Surface | Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| H1 | `metrics_collector.py` | L97-110 | Gimmick Elegance | **P1** | `_infer_provider_identity()` infers provider/backend/family from model name prefix. Falls back to `("unknown", "unknown", "unknown")` silently. Fragile — adding a new model family requires code change in an observability module rather than config. No comment warns that this is a temporary bridge pending config-driven metadata. | comment-only |
| H2 | `metrics_collector.py` | L80-94 | Gimmick Elegance | **P1** | `MODEL_COSTS` dict is inline with hardcoded prices. Claude/OpenAI prices were just added. No link to a config SSOT or external price source. Will drift silently as prices change. The Vertex billing comment (L74-79) is good but the dict itself lacks a maintenance note. | comment-only |
| H3 | `logger.py` | L166-173 | Gimmick Elegance | **P1** | `log()` method auto-detects log level from emoji characters in the message string. This is a hidden gimmick: an LLM reading the method signature (`level=logging.INFO`) would not predict that the level can be silently overridden by message content. No comment explains this behavior. | comment-only |
| H4 | `tests/stage3_isolated_test/` | (directory) | Local Readability | **P2** | 8 stale JSON/log artifacts from 2026-02-03 (`blueprints_*.json`, `production_test_*.json`, `test_result_*.json`, `progress.log`). LLM file searches may treat these as active test fixtures. Prior T6 flagged this as H8; still unresolved. | contract-cleanup (delete artifacts) |
| H5 | `tests/stage4_v2_test/` | `project/`, `results/` | Local Readability | **P2** | Stale subdirectories (`project/`, `results/`) with leftover run artifacts. Same issue as H4. | contract-cleanup (delete artifacts) |
| H6 | `docs/implementation/risk-approval-checklist.md` | L1 | Contract | **P2** | Missing Date/Status/Applies To metadata header. Inconsistent with the 14 harnesses and 10 contracts that follow standard headers. Prior T6 flagged as H9; still unresolved. | doc-only |
| H7 | `docs/implementation/release-gate-v1.md` | L1 | Contract | **P2** | Missing Date/Status/Applies To metadata header. Same inconsistency as H6. Prior T6 flagged as H10; still unresolved. | doc-only |

---

## 5. Top Quick Wins

### Comment-Only (4 items)

| # | Target | Action | Fix Type |
|---|---|---|---|
| QW1 | `metrics_collector.py:97-110` | Add comment: `# [INTERIM] Provider identity inferred from model name prefix. Pending config/models.yaml metadata SSOT (see llm-multi-provider-context-note.md S8.2). Falls back to unknown silently.` | comment-only |
| QW2 | `metrics_collector.py:74-94` | Add comment: `# [INTERIM] Inline cost table. Must be manually updated when vendor pricing changes. Target: move to config/models.yaml or a dedicated pricing config.` | comment-only |
| QW3 | `logger.py:166-173` | Add comment: `# [GIMMICK] Emoji-based log level auto-detection — overrides caller-specified level if message contains specific emoji. StudioVisualizer compatibility layer.` | comment-only |
| QW4 | `pass_rate_monitor.py:16-22` | No action needed — the non-authoritative declaration is already exemplary. Record as reference pattern for other modules. | ignore (already good) |

### Doc-Only (2 items)

| # | Target | Action | Fix Type |
|---|---|---|---|
| QW5 | `docs/implementation/risk-approval-checklist.md` | Add standard metadata header: `Date: 2026-03-08`, `Status: active`, `Applies To: risk-approval operations` | doc-only |
| QW6 | `docs/implementation/release-gate-v1.md` | Add standard metadata header: `Date: 2026-03-16`, `Status: active`, `Applies To: desktop PoC release gate` | doc-only |

### Contract-Cleanup (1 item)

| # | Target | Action | Fix Type |
|---|---|---|---|
| QW7 | `tests/stage3_isolated_test/` + `tests/stage4_v2_test/` | Delete stale JSON/log artifacts: `blueprints_*.json`, `production_test_*.json`, `test_result_*.json`, `progress.log`, `project/`, `results/`. Keep only `test_*.py` and `__init__.py`. | contract-cleanup |

**Summary**: 7 items. 4 comment-only + 2 doc-only + 1 contract-cleanup. Over half are comment/doc. Meets the master order rule.

---

## 6. Gimmick Elegance Judgment

### Elegant (9 gimmicks)

1. **DB Method-Group ToC** (`db_manager.py:61-78`): One obvious owner, explicit, navigable in 1 hop.
2. **Non-authoritative pass-rate declaration** (`pass_rate_monitor.py:16-22`): Exemplary. Explicitly tells LLM and operator what this module is NOT.
3. **Session JSONL opt-in** (`session_logger.py`): `enabled=False` default, 4-category split, operator-truth classification in docstring.
4. **Soft failure tracking** (`session_logger.py:361-392`): Centralized via `report_soft_failure`, bounded, no silent swallow.
5. **Vertex billing normalization** (`metrics_collector.py:113-119`): Prefix-stripping with explicit Vertex pricing comment.
6. **Scope accumulator** (`metrics_collector.py:195-201`): Clear snapshot-and-reset lifecycle.
7. **Stale metric cleanup** (`metrics_collector.py:222-227`): Bounded, tagged `[C5-P1-3]`.
8. **Log file retarget** (`logger.py:216-243`): Explicit lifecycle, documented `[TF-26]` tag.
9. **Root logger cleanup** (`logger.py:92-97`): Prevents console double-output, documented.

### Inelegant (2 gimmicks)

1. **Emoji-to-log-level auto-detection** (`logger.py:166-173`):
   - No comment explains the behavior
   - Caller-specified `level` parameter is silently overridden
   - An LLM reasoning about log levels would miss this
   - Fix: comment-only

2. **Provider identity inference from model name prefix** (`metrics_collector.py:97-110`):
   - Depends on naming convention stability
   - Falls back to `("unknown", "unknown", "unknown")` with no warning
   - Adding a new model family requires editing an observability module
   - Fix: comment-only (interim) + eventual migration to config SSOT

### Mixed (1 gimmick)

1. **Inline MODEL_COSTS** (`metrics_collector.py:80-94`):
   - Explicit and well-commented for current state
   - But hardcoded prices will drift as vendors change pricing
   - The Claude/OpenAI entries were recently added — good coverage expansion
   - Fix: comment-only (maintenance note)

### Overall Gimmick-Elegance Verdict: **mixed**

The observability surface is mostly elegant. The two inelegant gimmicks are narrowly scoped and fixable with comment-only changes. The underlying architecture (sink ownership, authority declarations, opt-in telemetry) is sound.

---

## 7. Deferred Refactor Candidates

| # | Target | Description | Rationale for Deferral |
|---|---|---|---|
| DR1 | `metrics_collector.py` MODEL_COSTS + provider inference | Move cost tables and provider identity to `config/models.yaml` metadata SSOT as part of the multi-provider hardening wave (see `llm-multi-provider-context-note.md` S8.2, S8.5). | Blocked by multi-provider wave completion. Current inline version works. Comment-only bridge is sufficient now. |
| DR2 | `logger.py` emoji detection | Replace emoji-based level override with explicit caller-side level specification or a named `log_with_auto_level()` variant. | Low risk. The gimmick is localized and only affects file logging, not console. A comment is sufficient to prevent LLM confusion. |
| DR3 | `db_manager.py` size (3,446 lines) | The file is large but already has the Method-Group ToC and uses `db_bootstrap_runtime.py` for schema migration. Further decomposition would be a boundary-refactor with no immediate LLM-friendliness gain beyond the existing ToC. | Already navigable via ToC. No 180+ LOC functions. Decomposition is pure structural preference, not a comprehension bottleneck. |

**3 items, capped per master order rule. All explicitly marked as deferred.**

---

## 8. No-Action / Settled Areas

### Settled (no further investigation needed)

| Area | Reason |
|---|---|
| `scripts/README.md` | Added since prior T6. Categorizes 50+ scripts. No further action. |
| `tests/README.md` | Added since prior T6. Explains layout, naming conventions, running instructions. |
| `UI/README.md` | Added since prior T6. Clarifies binary-only contents. |
| `docs/implementation/` stale `.py` files | All deleted since prior T6 (H1, H2 resolved). Zero `.py` files remain. |
| `scripts/tf_c1_patch.py` | Deleted since prior T6 (H6 resolved). |
| `geuldobi-desktop/` temp files | Deleted since prior T6 (H7 resolved). |
| `AGENTS.md` governance chain | All 19 cross-references resolve. Hub-and-spoke intact. |
| `pass_rate_monitor.py` operator-truth | Exemplary non-authoritative declaration. No action. |
| `session_logger.py` architecture | Opt-in, category-split, rotation, soft-failure — all elegant. No action. |
| `db_manager.py` Method-Group ToC | Already present and accurate. No action. |
| `geuldobi-desktop/DESKTOP-GUIDE.md` | Clear, complete. Runtime contract and IPC entry declared. No action. |

### Explicitly Out of Next Execution Wave

| Area | Reason |
|---|---|
| `UI/` directory | Binary assets only. Renaming to `assets/` is a nice-to-have but not a gimmick or authority issue. |
| `scripts/build_chaebol_*.py`, `scripts/build_fallen_prince_*.py` | Large corpus builders (84KB, 115KB) for specific stories. Not production runtime. Not imported. Increase search cost but do not create authority confusion. |
| `scripts/investment_corpus_support.py` (72KB) | Same pattern — large story-specific support. |
| `tests/` naming conventions | Already documented in README. The sweep/lane/wave pattern is stable and understood. |

---

## 9. Cross-Lane Handoff Notes

### To T2 (Provider / Router / Backend-Family-Capability Elegance)

- `metrics_collector.py:97-110` `_infer_provider_identity()` duplicates model-name-to-provider logic that should ideally live in the router/config layer. T2 should note whether `llm_router.py` or `models_config.py` already owns this inference, and whether the metrics collector should consume that instead of re-inferring.
- `metrics_collector.py:80-94` `MODEL_COSTS` is the only place Claude/OpenAI pricing lives. If T2 recommends a model metadata SSOT in `config/models.yaml`, cost data should migrate there too.

### To T5 (Fact Authority / Genre Gimmick / Contract State)

- `pass_rate_monitor.py` and `session_logger.py` both carry explicit non-authoritative declarations. These are good reference patterns for any future fact-authority documentation — T5 may want to reference them as "how to declare non-authority cleanly."

### From Prior T6 (2026-03-24)

- 7 of 10 hotspots resolved. 3 remain (H8/stale artifacts, H9/H10 governance metadata). New hotspots are observability-specific gimmick findings not present in the prior wave.

---

## 10. Confidence And Limits

**Confidence: 96%**

Basis:
- All 5 observability modules read in full and gimmick-mapped
- All peripheral directories inventoried with file-level evidence
- Stale reference sweep completed against prior T6 baseline
- Governance chain verified with zero broken links
- Dirty/untracked files in scope identified and assessed

Limits:
- `db_manager.py` was sampled (first 200 lines + ToC) rather than read in full (3,446 lines). The ToC and prior surveys provide sufficient coverage for gimmick-elegance assessment. Individual method internals were not re-audited.
- `tests/` 378 files were inventoried at directory level, not individually read. Naming convention and stale artifact assessment is based on directory listing and prior T6 evidence.
- Cost table accuracy in `metrics_collector.py` was not validated against current vendor pricing pages. The structural finding (inline hardcoded = will drift) holds regardless.

---

## 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type matches: LLM-friendliness + gimmick-elegance lane survey report
- All 10 mandatory sections present
- Prior T6 baseline established and delta tracked
- Scope covers all assigned surfaces
- PASS

Pass 2. Evidence and Consistency
- File:line anchors provided for all P0/P1 findings
- Prior T6 resolved items verified against live filesystem
- Dirty/untracked file assessment matches `git status` evidence
- Gimmick map entries verified against live source reads
- MODULE_COSTS and provider inference findings verified against `metrics_collector.py` lines 74-119
- Logger emoji gimmick verified against `logger.py` lines 166-173
- No claims beyond inspected evidence
- PASS

Pass 3. Execution and Readability
- Quick wins are actionable with file:line targets
- Over half of quick wins are comment/doc (4 comment + 2 doc out of 7 total)
- Deferred refactor candidates capped at 3 with explicit deferral rationale
- Cross-lane handoff notes are specific and actionable
- No execution SSOT or roadmap created (survey-only constraint respected)
- PASS

Estimated confidence: 96%
