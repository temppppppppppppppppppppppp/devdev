Date: 2026-03-23
Status: final (3-pass audited)
Document Type: ROL global survey T3 lane report
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression.md`
Evidence Path: `docs/2026-03-23/opus/rol-global-survey-t3-contracts-regression-evidence.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `T3 survey performed against dirty workspace with docs/runtime/test edits; see parent order for full dirty manifest`

---

# T3 Contracts / Regression — ROL Global Survey

## 1. Executive Summary

The T3 lane covers tests, scripts, config, prompt maps, and shared contracts.

Key findings:

- **Test harness is large and well-structured** (383 files, 5,423 collected items, 5,175 test functions). E2E, integration, chaos, property, canary, and smoke tiers all exist. No xfail markers remain. Contract-test pattern is actively used.
- **Regression surface has one thin zone**: genre guards (10 implementations, only 2 have dedicated tests) and LLM provider implementations (4 providers, 0 dedicated tests). These are low-frequency change surfaces, so risk is bounded, but they are the thinnest regression coverage.
- **Config is schema-less**: all 44 config files (24 YAML + 20 JSON) load via `yaml.safe_load()` / `json.load()` without schema validation. Silent fallback to hardcoded defaults on any parse or type error. ConfigManager provenance contract (`get_guard_threshold_contract`) mitigates but does not prevent drift.
- **Scripts are well-classified**: 47 scripts, 3-tier regression validation contract (CONTRACT_SAFE / FOCUSED_MUTATION / FULL_CANARY_PROOF) is active and correct.
- **No pre-rerun blocker exists in T3 scope**. The top 3 fixes are all quick wins.

**Pre-rerun blocker in this lane**: none.

**Top 3 highest-ROI fixes in this lane**:
1. Add `if __name__ == "__main__"` guard to `scripts/tf_c1_patch.py` (P1, safety)
2. Add genre-guard smoke tests for untested guards (P2, regression gap)
3. Remove `config/prompts/deprecated/` dead files (P2, hygiene)

## 2. Included Coverage

### Included (primary sweep)
- `tests/` — 383 Python files, 5,175 test functions, 5,423 collected items
- `tests/e2e/` — 8 files, 2,074 lines
- `tests/integration/` — 2 files, 1,505 lines
- `tests/chaos/` — 7 files, 1,108 lines
- `scripts/` — 47 Python + 1 PowerShell, ~17,000 lines total
- `config/` — 24 YAML + 20 JSON = 44 config files
- `.editorconfig`, `.pre-commit-config.yaml`, `pyproject.toml`
- `modules/core/config_manager.py`, `constants.py`, `models_config.py`, `prompt_loader.py`
- `scripts/regression_validation_tiers.py`, `smoke_fixture_contract.py`

### Included as reference
- `AGENTS.md` — script references, pytest memory rules
- `docs/implementation/` harnesses — script and validation contract references
- Prior survey docs — stale claim cross-checks

### Excluded
- Runtime core, domain agents, persistence, UI (T1/T2 scope)
- `.git/`, `__pycache__/`, `.venv/`, build outputs

## 3. Current Ownership / Flow Map

### 3.1 Test Harness Ownership

```
tests/
├── conftest.py                 — 11 fixtures (function scope), Windows-safe temp_dir
├── e2e/conftest.py             — 5 fixtures, real DBManager with tmp_path SQLite
├── e2e/                        — 8 end-to-end smoke/golden-route tests
├── integration/                — 2 integration tests (patch wiring, pipeline smoke)
├── chaos/                      — 7 fault-injection tests (dead NPC, rollback, degrade)
├── test_*.py (root)            — ~360 unit/contract/sweep test files
└── (no property_based/ dir)    — parametrize-based property tests inline in root
```

**Regression tier contract**: `scripts/regression_validation_tiers.py`
- CONTRACT_SAFE: 10 non-mutating desktop/runtime contract tests
- FOCUSED_MUTATION: 2 canary tests + 4 smoke scripts (stage-level fixture mutation)
- FULL_CANARY_PROOF: 2 canary scripts (live project mutation)

**Fixture contract**: `scripts/smoke_fixture_contract.py`
- `CANONICAL_SMOKE_SOURCE_PROJECT = "smoke_fixture_demo"`
- `BOUND_SMOKE_TARGET_PROJECT = "코덱스_테스트"`
- `PACKAGED_SMOKE_PROJECT = "investment_canary_demo"`

### 3.2 Script Ownership

| Category | Count | Runtime Risk | Authority |
|---|---|---|---|
| A. Runtime-affecting (smoke/canary/harness) | 9 | state mutation (fixture-bounded) | AGENTS.md + regression_validation_tiers.py |
| B. Governance/ops tools | 9 | read-only | AGENTS.md L99-106 explicit |
| C. Document/artifact builders | 15 | file output only | narrative harness docs |
| D. Corpus/dataset builders | 3 | external only | docs |
| E. Migration/repair (one-time) | 2 | high if re-run | completed, should archive |
| F. Support libraries (import-only) | 4 | N/A | imported by A/B |
| G. Shell integration | 1 | PowerShell | regression tiers |

### 3.3 Config Ownership

| Config Layer | Files | Authority | Load Path |
|---|---|---|---|
| `config/models.yaml` | 1 | SSOT for model assignment | `models_config.py` → `config_manager.py` → `constants.py` |
| `config/settings/validation.yaml` | 1 | SSOT for thresholds + feature flags | `config_manager.py` → `threshold_helper.py` → lazy `_LazyThreshold` |
| `config/genres/*.yaml` | 10 | Genre-specific guard rules | `*_guard.py` constructors |
| `config/prompts/*.yaml` | 9 | LLM prompt templates | `prompt_loader.py` singleton cache |
| `config/prompts/*.json` | 12 | Prompt libraries + rules | direct `json.load()` in agents |
| `config/settings.json` | 1 | **Legacy compat shim** (deprecated) | `config_manager.py` compat path |
| `config/style_references/` | 2 | Style guide cache | `style_guard.py` |
| `config/terms/*.json` | 2 | Genre terminology mapping | LLM term normalization |

**Authority chain**: `validation.yaml` > `settings.json` (compat) > hardcoded fallback.

### 3.4 Pre-Commit / Bootstrap

- **Pre-commit hook**: `scripts/check_utf8_hygiene.py` only (UTF-8 enforcement)
- **Ruff**: configured in `pyproject.toml`, target py312, select E/W/F/I/UP, 31 per-file ignores
- **Pytest config**: `pyproject.toml` testpaths=["tests"], `-p no:xdist --tb=short`
- **Encoding**: `.editorconfig` mandates UTF-8 + LF globally

## 4. Top Hotspots

### H-1. Schema-less Config Loading (P1, contract-cleanup)

**file:line anchors**:
- `modules/core/config_manager.py:66-75` — `_load_agents_from_yaml()`: bare `except Exception` swallows parse errors
- `modules/core/config_manager.py:110-131` — `load_settings()`: returns `{}` on missing/malformed YAML
- `modules/core/config_manager.py:97-108` — `_coerce_to_default_type()`: type mismatch returns fallback silently

**Mechanism**: All 44 config files load without schema validation. If a YAML key has the wrong type (e.g., string `"90"` instead of int `90`), `_coerce_to_default_type()` silently returns the hardcoded default with `valid=False`. The provenance contract logs this, but nothing enforces it.

**Fresh-run relevance**: unlikely to cause immediate failure (defaults are safe), but makes config drift invisible until operator manually checks provenance contract output.

**Fix type**: `contract-cleanup`

### H-2. Genre Guard Test Gap (P2, contract-cleanup)

**file:line anchors**: N/A (absence finding)

**Mechanism**: 10 genre guard YAML files exist (`actor`, `alt_history`, `composer`, `cooking`, `fantasy`, `hunter`, `investment`, `medical`, `sports`, `wuxia`) with complex regex patterns (`forbidden_modern_patterns`, `realm_technique_limits`). Only `wuxia` and `investment` have dedicated test files. If a regex pattern in `cooking.yaml` or `sports.yaml` becomes invalid, no test catches it.

**Fresh-run relevance**: low for current wuxia/investment projects; higher if extended genres are activated.

**Fix type**: `contract-cleanup`

### H-3. `tf_c1_patch.py` Missing `__main__` Guard (P1, comment-only)

**file:line anchor**: `scripts/tf_c1_patch.py:1-99`

**Mechanism**: This one-time repair script has no `if __name__ == "__main__"` guard. It reads a hardcoded path (`C:\Users\wjjo\Desktop\글도비\modules\core\db_manager.py`) and writes modifications. If imported by any test or script, it executes unconditionally. The hardcoded path also points to a different user directory, so it would fail on this machine, but the import-side-effect risk is real.

**Fresh-run relevance**: none (one-time patch already applied).

**Fix type**: `comment-only` (add guard or archive)

### H-4. Deprecated Prompt Configs Still Present (P2, doc-only)

**file:line anchors**:
- `config/prompts/deprecated/architect_rules.json`
- `config/prompts/deprecated/writer.json`

**Mechanism**: Two deprecated JSON files remain in `config/prompts/deprecated/`. No production code imports them (verified via grep). They are dead files that could confuse future LLM-assisted code exploration.

**Fresh-run relevance**: none.

**Fix type**: `doc-only` (delete or move to archive)

### H-5. `settings.json` Legacy Compat Shim (P2, contract-cleanup)

**file:line anchor**: `config/settings.json:1-12`

**Mechanism**: `config_manager.py` still checks `settings.json` as a compatibility fallback when a key is missing from `validation.yaml`. The file has not been the primary authority since the validation.yaml SSOT was established. It could shadow a YAML value if someone edits settings.json but not validation.yaml.

**Fresh-run relevance**: low (validation.yaml always wins when present).

**Fix type**: `contract-cleanup`

### H-6. Style Guide mtime-Based Cache Invalidation (P2, contract-cleanup)

**file:line anchor**: `config/style_references/investment/style_guide.json` — `reference_manifest.mtime_ns` field

**Mechanism**: The style guide cache embeds file mtime_ns as cache invalidation key. If a reference manuscript file is updated but style_guide.json is not regenerated, stale style data persists. Hash-based invalidation would be more robust.

**Fresh-run relevance**: could cause stale style data in investment genre runs.

**Fix type**: `contract-cleanup`

## 5. Stale-vs-Live Corrections

### 5.1 "264 test files with 0 test functions" — STALE

The initial broad scan found many files with 0 `def test_*` matches. This is **misleading**. The actual pytest collection finds 5,423 items. Many test files use class-based test methods (`def test_*` inside `class Test*`) or parametrize decorators that expand test counts at collection time. The 383 test files are overwhelmingly functional.

### 5.2 "87% of production modules have zero direct test imports" — STALE framing

Name-matching analysis (`find tests/test_{module}*.py`) shows every production module directory has test file coverage. The earlier "87% uncovered" claim used import-tracing, which undercounts because:
- Sweep tests (`test_sweep3.py` through `test_sweep39.py`) test cross-module behaviors
- Many tests import a module indirectly through an orchestrator or context

The actual regression surface is narrower than 87% suggests, but the genre-guard and provider gaps (H-2) are real.

### 5.3 xfail count — STALE

MEMORY.md records "68 xfailed". Current live workspace has **0 xfail markers** in tests/. This was already addressed in a prior sweep.

### 5.4 "2,114 passed" — STALE

Current collection shows **5,423 collected items** (up from 2,114 at the TF audit checkpoint). Significant test growth has occurred.

### 5.5 Old "config drift" survey claims — PARTLY LIVE

The `ConfigManager` provenance contract (`get_guard_threshold_contract`) was added to address config drift. It is tested (29 tests in `test_config_manager.py`). The provenance contract is a strong defense. The remaining gap is the absence of schema validation on load (H-1), which the provenance contract records but does not block.

## 6. Quick Wins

### QW-1. Add `__main__` guard to `tf_c1_patch.py`

**Effort**: 2 lines
**Impact**: eliminates import-side-effect safety risk
**Severity**: P1
**Fix type**: `comment-only`

### QW-2. Delete `config/prompts/deprecated/`

**Effort**: delete 2 files
**Impact**: removes dead config that could confuse exploration
**Severity**: P2
**Fix type**: `doc-only`

### QW-3. Add parametrized genre guard load test

**Effort**: ~30 lines (one test function that loops over all 10 genre YAML files, validates they parse and contain expected top-level keys)
**Impact**: catches regex syntax errors or structural drift in any genre guard
**Severity**: P2
**Fix type**: `contract-cleanup`

### QW-4. Archive `repair_tr_korean_utf8.py`

**Effort**: move 1 file
**Impact**: removes completed one-time repair script from active scripts directory
**Severity**: P2
**Fix type**: `doc-only`

### QW-5. Add `validation.yaml` presence check on bootstrap

**Effort**: ~5 lines in `config_manager.py.__init__`
**Impact**: fast-fails if the threshold SSOT file is missing, instead of silently falling back to defaults
**Severity**: P2
**Fix type**: `contract-cleanup`

## 7. Boundary Refactor Candidates

### BR-1. Config Schema Validation Layer (boundary-refactor)

**Current state**: Config loading uses `yaml.safe_load()` + type coercion + provenance contract. No schema.

**Candidate**: Add a lightweight schema definition (dict of key → expected type/range) for `validation.yaml` and `models.yaml`. Validate once on load. This would turn silent fallbacks into loud failures during bootstrap.

**ROI**: medium. The provenance contract already catches most drift. Schema validation would catch structural errors (missing sections, wrong nesting) that provenance does not.

**Fresh-run relevance**: prevents config-related silent degradation on next run.

### BR-2. Regression Tier Expansion for Genre Guards (boundary-refactor)

**Current state**: `regression_validation_tiers.py` covers desktop, runtime, and canary tiers but has no tier for genre-guard contract tests.

**Candidate**: Add a `GENRE_GUARD_CONTRACT` tier that validates all genre YAML files parse correctly, all mandatory keys exist, and all regex patterns compile.

**ROI**: low immediate, high if genre palette expands.

**Fresh-run relevance**: low for current wuxia/investment focus.

## 8. Confidence And Limits

**Estimated confidence**: 96%

### Why this is above 95%

- All 383 test files were accounted for; pytest collection was verified live (5,423 items)
- All 47 scripts were classified and cross-checked against AGENTS.md and governance docs
- All 44 config files were inventoried with load paths and authority chains
- Key claims were verified against live source: `tf_c1_patch.py` missing guard, deprecated configs unreferenced, provenance contract tested, xfail count = 0
- Regression tier contract (`regression_validation_tiers.py`) was read in full
- Config manager authority chain was traced from YAML through lazy threshold to production

### Remaining uncertainty

- Not every test file was opened and read line-by-line; coverage claims rely on `grep -c "def test_"` and pytest collection
- Script error handling quality was sampled, not exhaustively verified for all 47 scripts
- Genre guard YAML regex patterns were counted but not individually compiled or validated
- The `settings.json` compat path was confirmed present but not load-tested against a deliberately conflicting `validation.yaml` value

## 9. 3-Pass Audit Record

### Pass 1. Structure and Coverage

- Confirmed all 383 test files, 47 scripts, 44 config files inventoried
- Confirmed regression tier contract maps to correct files
- Confirmed pre-commit hook is only `check_utf8_hygiene.py`
- Confirmed config authority chain: validation.yaml > settings.json > hardcoded
- PASS

### Pass 2. Evidence and Consistency

- Verified xfail claim stale (0 in live source vs 68 in MEMORY.md)
- Verified test count growth (5,423 collected vs 2,114 at checkpoint)
- Verified `tf_c1_patch.py` missing `__main__` guard (confirmed no match)
- Verified deprecated configs unreferenced in production (confirmed grep empty)
- Verified ConfigManager provenance tested (29 tests in test_config_manager.py)
- PASS

### Pass 3. Execution and Readability

- Separated stale from live findings
- Ranked quick wins by effort/impact
- Stated pre-rerun blocker status clearly (none in T3)
- Top 3 fixes are bounded and verifiable
- PASS
