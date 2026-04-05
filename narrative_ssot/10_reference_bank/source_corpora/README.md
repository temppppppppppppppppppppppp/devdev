# Source Corpora Transition Note

Status: transition residue
Date: 2026-04-05

이 폴더는 `narrative_ssot` 내부에 남아 있는 old corpus subtree다.
현재는 historical residue와 pointer 역할만 수행하며, 새 canonical root로 쓰지 않는다.

Current canonical roots:

- `material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms`
- `material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld`
- `material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus`

Operational rule:

- corpus refresh, builder rerun, downstream read path update는 `material_ssot` root 기준으로 진행한다
- 이 `narrative_ssot` subtree는 bounded cutover 이후 pointer/archive pass 전까지 transition residue로만 유지한다
- 각 하위 corpus README의 transition note가 세부 경로 안내를 담당한다
