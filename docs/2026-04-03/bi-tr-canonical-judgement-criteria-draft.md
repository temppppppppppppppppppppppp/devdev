# BI/TR Canonical Judgement Criteria Draft

Date: 2026-04-03
Status: draft
Owner Lane: `IDE-2`
Purpose: decide whether `Golden Canary`, current BI/TR builders, or a hybrid should become the next canonical BI/TR contract for Geuldobi

## 1. Decision Framing

This is not a simple choice between:

- `Golden Canary is always correct`
- `current builder output is always correct`

The correct question is:

- which structure is most compatible with real Geuldobi runtime consumption
- which structure minimizes silent rewrite during Stage0 -> Stage2 handoff
- whether canonical `v1` should be `Golden Canary`, `current builder`, or `hybrid`

## 2. Judgement Criteria

### Criterion 1. Stage2 Intake Readiness

Question:

- can the BI/TR pair enter Stage 2 without fallback regeneration or missing-payload warnings

Why it matters:

- Geuldobi treats `plot_roadmap` as the real Stage 0 -> Stage 2 intake surface
- if `plot_roadmap` is missing, empty, or lacks consumer-backed payload, runtime already considers the pair incomplete

Code anchors:

- `modules/core/stage0_handoff.py`
- `main_a.py`

Pass signal:

- effective BI root exposes `plot_roadmap`
- roadmap entries pass `validate_plot_roadmap_entries()`
- runtime does not need to rebuild roadmap from treatment or saved arcs

Fail signal:

- `plot_roadmap` missing
- `plot_roadmap` empty
- roadmap entries are only title/summary shells
- Stage 2 only works after compatibility backfill

### Criterion 2. Runtime Identity Contract Completeness

Question:

- does the BI provide the `protagonist_config` subset that Stage2/3/4 and writer-quality paths actually use

Why it matters:

- `world_origin`, `incarnation_type`, `pov`, and `external_pov_insert_policy` are referenced across Analyst, Blueprint, Chief Writer, Writer, and Director paths

Code anchors:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/director_caching.py`

Pass signal:

- effective BI root has stable `protagonist_config`
- runtime-critical keys are present and semantically valid
- no widespread fallback-to-default behavior is required

Fail signal:

- `protagonist_config` missing
- runtime subset only partially present
- downstream code frequently falls back to `"원시인"` or `"회귀자"` because source data is incomplete

### Criterion 3. Silent Overwrite Resistance

Question:

- can the BI/TR pair survive Stage0 handoff without being silently rewritten into a different truth shape

Why it matters:

- if runtime must immediately regenerate or overwrite key fields, the source artifact is not authoritative enough to be canonical

Code anchors:

- `modules/core/stage0_handoff.py`
- `modules/core/project_manager.py::force_sync_v25_dna`

Pass signal:

- Stage0 handoff mostly validates and forwards source truth
- compatibility bridge remains exceptional, not normal
- `plot_roadmap` does not need to be reconstructed on most healthy inputs

Fail signal:

- runtime regularly injects `plot_roadmap` from treatment
- DB anchor becomes the real owner because source BI is too weak
- canonical-looking BI files still require immediate rewrite

### Criterion 4. Source-of-Truth Convergence

Question:

- do raw BI, raw TR, and DB bible anchor converge on one meaning, or do they represent different effective truths

Why it matters:

- current debt is not only schema mismatch; it is authority split across:
  - raw BI file
  - treatment
  - DB bible anchor

Source doc anchor:

- `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`

Pass signal:

- owner priority is explicit
- same project yields the same effective roadmap and protagonist contract in file and DB
- Stage2 consume contract does not depend on hidden post-load sync

Fail signal:

- raw BI says one thing and DB anchor says another
- treatment is the real owner even when BI appears authoritative
- operator cannot tell which artifact is canonical

### Criterion 5. Family-Wide Reproducibility

Question:

- can the candidate structure be generated, validated, and reused across multiple families without one-off exceptions

Why it matters:

- canonical format must work for finance, modern business, wuxia, and future families
- one golden example is useful, but canonical `v1` must scale beyond a single work

Code anchors:

- `scripts/build_bi_from_phase0_and_tr.py`
- `scripts/build_wuxia_bi_from_phase0_and_tr.py`
- `scripts/check_bi_tr_consumability.py`
- `modules/core/response_schemas.py`

Pass signal:

- builder output is structurally consistent across projects
- validator can distinguish canonical pass from legacy compatibility pass
- template and produced artifacts align

Fail signal:

- each family produces a materially different effective root
- validator accepts too many incompatible shapes as equivalent
- template, builder output, and runtime expectation drift apart

## 3. Recommended Scoring Order

Use the criteria in this order:

1. `Stage2 Intake Readiness`
2. `Runtime Identity Contract Completeness`
3. `Silent Overwrite Resistance`
4. `Source-of-Truth Convergence`
5. `Family-Wide Reproducibility`

Rationale:

- if a candidate fails the first two, it is not a strong canonical candidate even if it looks cleaner on paper
- the middle two decide whether the format is truly authoritative or only cosmetically structured
- the last criterion decides whether the candidate can survive promotion to canonical `v1`

## 4. Practical Evaluation Sequence

Before any redesign work:

1. extract `Golden Canary BI/TR` effective structure
2. extract current builder-output effective structure
3. compare both against real runtime consume contract
4. score both against the five criteria above
5. decide:
   - `Golden Canary canonical`
   - `current builder canonical`
   - `hybrid canonical v1`

## 5. Current Working Hypothesis

Based on current repository evidence:

- `Golden Canary` looks stronger as a runtime-facing reference specimen
- current builder output is useful as a production mechanism
- but the likely result is neither pure `Golden Canary` nor pure current builder
- the likely outcome is `hybrid canonical v1`

Meaning:

- preserve the runtime-useful fields and richness proven by `Golden Canary`
- normalize container shape and builder reproducibility through the current harness lane
- explicitly demote silent rewrite paths into compatibility bridges

## 6. Immediate Next Step

Do not normalize yet.

First, run one bounded comparison:

- `Golden Canary BI/TR`
- one modern builder-output pair
- one wuxia builder-output pair

and judge them only by the five criteria above.
