# Metrics Baseline

Purpose:
- Track the last verified full-suite baseline separately from live runtime thresholds.
- Prevent partial session checks from being mistaken for the global baseline.

## Last Verified Full-suite Baseline

| Metric | Value | Verified Date | Source | Notes |
|---|---|---|---|---|
| Full test suite | `3,831 passed / 16 skipped / 0 failed` | 2026-03-10 | `docs/2026-03-12/TF-HEALTH-codebase-full-audit.md` | Latest verified full-suite baseline recorded in dated audit evidence |
| Ruff | `0 violations` | 2026-03-10 | `docs/2026-03-12/TF-HEALTH-codebase-full-audit.md` | Keep as last verified full-repo lint baseline |

## Live Threshold Ledger

| Metric | Stage | Current Value | Source | Notes |
|---|---|---|---|---|
| QualityGate score | Stage 2 | `90` | `config/settings/validation.yaml` -> `scoring.quality_gate_score` | Arc validation gate |
| QualityGate score | Stage 3 | `90` | `config/settings/validation.yaml` -> `scoring.quality_gate_score` | Blueprint validation gate |
| QualityGate score | Stage 4 | `90` | `config/settings/validation.yaml` -> `scoring.quality_gate_score` | Manuscript validation gate |
| Patch threshold | Shared | `rewrite_below=50` | `config/settings/validation.yaml`, `modules/core/constants.py` | Below 50 -> full rewrite branch |
| Patch threshold | Shared | `inplace_below=60` | `config/settings/validation.yaml`, `modules/core/constants.py` | 60 or above -> in-place branch allowed |
| Patch routing | Stage 4 | `fix_scope + inplace_below/rewrite_below` | `modules/core/stage4_interview_round.py` | Legacy mid-tier patch threshold text is no longer the live branch key |
| Manuscript length | Stage 4 | `min=4000, target=5000, max=15000` | `config/settings/validation.yaml` -> `manuscript.*` | Blocking + scoring guard |
| Retry budget | Stage 2 | `analyst_max_attempts=10` | `config/settings/validation.yaml` -> `retry.analyst_max_attempts` | UI strings may still show older fallback text in some surfaces |
| Retry budget | Stage 3/4 | `director_max_attempts=10` | `config/settings/validation.yaml` -> `retry.director_max_attempts` | Some Python fallback defaults still use `5` if YAML is missing |
| Mandatory context max | Stage 4 | `400000` | `config/settings/validation.yaml` -> `context.mandatory_context_max` | 1M-context era live limit |
| Lookback excerpt chars | Stage 4 | `5000` | `config/settings/validation.yaml` -> `context.lookback_excerpt_chars` | Python fallback defaults may still say `500` |
| Lookback total chars | Stage 4 | `40000` | `config/settings/validation.yaml` -> `context.lookback_total_chars` | Python fallback defaults may still say `4000` |
| Vector recall | Stage 4 | `vector_max_results_s4=50` | `config/settings/validation.yaml` -> `context.vector_max_results_s4` | Shared retrieval input size |
| Smart retrieval budget | Stage 4 | `300000` | `config/settings/validation.yaml` -> `smart_retrieval.stage4_total_budget` | Writer-side retrieval budget |
| Smart retrieval budget | Director | `300000` | `config/settings/validation.yaml` -> `smart_retrieval.director_total_budget` | Director-side retrieval budget |

## Measurement Rules
- Only a full-suite run updates the global baseline.
- Partial pytest runs belong in dated audit or remediation docs, not in this ledger.
- When YAML and Python fallback defaults diverge, record YAML as truth and fallback drift as a note or risk.

## Session Note
- This stage_map refresh did not rerun the full test suite.
- Current-session targeted pytest evidence remains in the dated `docs/2026-03-13/*` audit documents.

## Last Verified
- Date: 2026-03-27
- Commit: `eb7a41d8`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
