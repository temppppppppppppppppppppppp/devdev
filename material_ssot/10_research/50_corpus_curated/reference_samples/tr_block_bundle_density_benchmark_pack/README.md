# TR Block Bundle Density Benchmark Pack

Date: 2026-04-10
Status: active planned pack

Role:

- build an empirical baseline for the operator claim:
  - `one TR block should be dense enough to unfold into roughly 2~6 downstream episodes`
- decide when `2~6 episode bundle density` is weak enough to justify `YELLOW` vs `RED`
- keep `benchmark alias` and `opening pacing triage` separate while this baseline is still being built

Current law:

- before this pack closes, `2~6 bundle density` is an investigation trigger, not yet a standalone `RED` hard gate
- after this pack closes, weak-reference lower bounds may be promoted into a harder operator law

## Provisional Local Baseline

Use these immediately:

- `material_ssot/10_research/50_corpus_curated/투자물_금수저 투자백서`
- `material_ssot/10_research/50_corpus_curated/투자물_금수저생활백서`
- `material_ssot/10_research/50_corpus_curated/재벌물_독식하는 재벌 3세`
- `material_ssot/10_research/50_corpus_curated/재벌물_재벌 3세는 총수가 되고 싶다`
- `material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus`

Use these as a first pass:

- strong reference:
  - `금수저 투자백서`
  - `금수저생활백서`
- low-bound reference:
  - `독식하는 재벌 3세`
  - `재벌 3세는 총수가 되고 싶다`
- cross-lane reference:
  - `medical_magical_surgeon_sample_corpus`

## NAS Expansion Candidates

- `대한민국 절대 재벌`
- `신흥재벌`
- `재벌생활기록부`
- `김 대리는 인생이 너무 가볍다`
- `매지컬 써전(강산)`

These expand:

- 정통 재벌 스케일
- 성장형 재벌
- 운영/생활 밀착형 재벌
- 가벼운 진입 현대 현판
- cross-lane medical density

## Core Axes

- `window_char_count`
- `window_paragraph_count`
- `window_sentence_count`
- `domain_anchor_per_1000_chars`
- `quote_paragraph_ratio`

Interpretation rule:

- this pack is not trying to define beauty or prose quality
- it is measuring whether a downstream `2~6 episode` window carries enough concrete movement to justify a material-side `TR block`

## Current Tooling

- manifest: `manifest.json`
- snapshot builder: `scripts/bundle_density_snapshot.py`
- provisional snapshot artifact: `docs/2026-04-10/tr-block-bundle-density-provisional-baseline.json`

Example:

```powershell
python -X utf8 scripts/bundle_density_snapshot.py `
  --corpus-dir material_ssot/10_research/50_corpus_curated/투자물_금수저 투자백서 `
  --corpus-dir material_ssot/10_research/50_corpus_curated/재벌물_독식하는 재벌 3세 `
  --corpus-dir material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus `
  --output docs/2026-04-10/tr-block-bundle-density-provisional-baseline.json
```

## Next Admissible Step

1. refresh the provisional local snapshot
2. ingest the NAS expansion candidates on a machine that can reach the NAS
3. freeze weak-reference lower bounds
4. only then decide whether `bundle density failure` becomes a standalone `RED` operator law
