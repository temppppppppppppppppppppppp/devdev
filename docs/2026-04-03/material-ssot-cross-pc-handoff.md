# material_ssot cross-PC handoff v0.1

Date: 2026-04-03
Status: handoff baseline
Scope: 다른 PC에서 `material_ssot` / `research` / `narrative_ssot` 정리 작업을 안전하게 이어받기 위한 현재 컨텍스트를 한 장으로 고정한다

## 1. Read This First

새 PC에서 이 작업을 이어받을 때는 아래 순서로 열면 된다.

1. `AGENTS.md`
2. `material_ssot/00_governance/authority-map.md`
3. `material_ssot/10_research/source-map.md`
4. `docs/2026-04-03/material-ssot-full-absorption-checklist.md`
5. `docs/2026-04-03/narrative-ssot-triage-inventory.md`
6. `docs/2026-04-03/narrative-reference-bank-mirror-necessity-audit.md`
7. `docs/2026-04-03/narrative-source-corpora-bounded-cutover-design.md`

이 handoff 문서는 위 문서들을 빠르게 요약한 운영용 맵이다.

## 2. One-Line State

`material_ssot`는 현재 `재료 사이드 오더`의 stage SSOT로는 이미 유효하다.

남은 큰 잡음은 이제 거의 `narrative_ssot` 쪽이며, `docs/실물기반 사각지대 테스트`는 대부분 provenance/pointer shell 수준까지 내려왔다.

## 3. Canonical Interpretation Now

현재 authoritative 해석은 아래가 맞다.

- stage SSOT root:
  - `material_ssot`
- family axis:
  - `docs/narrative-router`
- live narrative artifacts:
  - `treatments/`
  - `bible/`
- legacy research shell:
  - `docs/실물기반 사각지대 테스트`
- legacy runtime note root:
  - `로직_리서치`
- scaffold residue:
  - `narrative_ssot`

## 4. What Is Already Done

### A. stage-axis SSOT bootstrap

아래 축은 이미 `material_ssot`로 세워졌다.

- `10_research`
- `20_pitch`
- `30_stage0_preprocess`
- `40_phase0_design`
- `50_tr`
- `60_bi`

핵심 governance:

- `material_ssot/README.md`
- `material_ssot/00_governance/authority-map.md`
- `material_ssot/00_governance/legacy-map.md`
- `material_ssot/00_governance/stage-read-order.md`

### B. research absorption

이미 canonical로 넘어간 research lanes:

- reference profiles
  - `material_ssot/10_research/10_reference_profiles`
- few-shot bank
  - `material_ssot/10_research/20_fewshot_bank`
- work-level normalized packs
  - `material_ssot/10_research/30_work_materials`
- long-form analysis
  - `material_ssot/10_research/40_analysis/pattern_reports`
- collector-promoted snapshots
  - `material_ssot/10_research/40_analysis/market_snapshots`
- curated corpus bundles
  - `material_ssot/10_research/50_corpus_curated`
- longtail title corpus
  - `material_ssot/10_research/60_corpus_longtail`
- promoted raw ingest
  - `material_ssot/10_research/80_ingest_raw`

### C. old research root status

`docs/실물기반 사각지대 테스트`는 이제 canonical research root가 아니다.

현재 남은 것은 거의 아래뿐이다.

- `원고/manifest.json`
- `원고/errors.log`
- pointer README들
- old analysis pointer surface

즉, 이 경로는 authority split이라기보다 `provenance shell`에 가깝다.

### D. logic_research status

`로직_리서치`는 authority 기준으로는 거의 정리됐다.

현재 해석:

- collector code root는 `scripts/research_collectors`
- output authority는 `material_ssot/10_research/40_analysis/market_snapshots`와 `80_ingest_raw`
- old `로직_리서치`는 runtime note shell

### E. narrative_ssot status

`narrative_ssot`는 현재 active SSOT가 아니다.

다만 즉시 삭제 대상도 아니다.
이유는 아래가 아직 남아 있기 때문이다.

- `10_reference_bank`
  - cards/manifest mirror
  - source_corpora active sink
- `50_projects/_template`
  - pilot scaffold utility dependency

## 5. The Most Important New Finding

`narrative_ssot/10_reference_bank`는 한 덩어리 mirror가 아니다.

하위 성격이 갈린다.

- low-priority mirror residue
  - `cards/`
  - `reference_card_manifest.json`
  - `mirror_status.json`
- active sink
  - `source_corpora/`
- archive candidates
  - `idea_engine_db/`
  - `selection/`

즉, `10_reference_bank`를 바로 retire 못 하는 이유는 `cards mirror`가 아니라 `source_corpora` 때문이다.

## 6. Active Script Dependencies

현재 `source_corpora`를 직접 쓰는 bounded script set:

- `scripts/build_platform_trend_corpus.py`
- `scripts/build_business_trend_slice.py`
- `scripts/build_youtube_channel_corpus.py`
- `scripts/export_youtube_idea_packets.py`

이 스크립트들이 아직 `narrative_ssot/10_reference_bank/source_corpora/...`를 default root로 쓴다.

그래서 다음 execution은 `source_corpora` subtree cutover여야 한다.

## 7. Exact Next Step

다음 실작업 1순위는 아래다.

`platform_trends source_corpora cutover execution SSOT`

왜 이게 1순위인가:

- active script가 2개뿐이라 가장 bounded하다
- modern business 관련 현재 문서 참조가 여기에 가장 많다
- 성공하면 `youtube/syukaworld`도 같은 패턴으로 따라가기 쉽다

실행 순서 초안:

1. `material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms`를 canonical lane으로 선언
2. `scripts/build_platform_trend_corpus.py` default output root 전환
3. `scripts/build_business_trend_slice.py` default input/output root 전환
4. `narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms` subtree move
5. old path pointer화
6. stale reference sweep
7. UTF-8 hygiene + targeted smoke validation

그다음 순서:

1. `youtube/syukaworld` cutover
2. `nas_serials/medical/magical_surgeon_sample_corpus` cutover
3. `idea_engine_db` / `selection` triage
4. `10_reference_bank` re-judge

## 8. Files That Matter Most

현재 handoff 기준 핵심 파일:

- `docs/2026-04-03/material-ssot-full-absorption-checklist.md`
- `docs/2026-04-03/narrative-ssot-triage-inventory.md`
- `docs/2026-04-03/narrative-reference-bank-mirror-necessity-audit.md`
- `docs/2026-04-03/narrative-source-corpora-bounded-cutover-design.md`
- `material_ssot/00_governance/authority-map.md`
- `material_ssot/10_research/source-map.md`
- `scripts/build_platform_trend_corpus.py`
- `scripts/build_business_trend_slice.py`
- `scripts/build_youtube_channel_corpus.py`
- `scripts/export_youtube_idea_packets.py`

## 9. Worktree Caution

현재 worktree는 깨끗하지 않다.

중요 포인트:

- 이번 웨이브에서 `docs/실물기반 사각지대 테스트/원고/...` 아래 대량 `D`는 longtail move 결과라 정상이다
- `docs/temp/` 쪽에는 별도 시스템-track temp 변경도 남아 있다
- 다른 PC에서 이어받을 때는 `git status`를 먼저 확인하되, unrelated temp 변경을 함부로 되돌리지 않는다

즉, 이 handoff 범위에서 집중할 변경은 아래다.

- `material_ssot`
- `docs/2026-04-03/` 관련 정리 문서
- `docs/실물기반 사각지대 테스트/` pointer/provenance shell
- `narrative_ssot/10_reference_bank/source_corpora`
- related builder scripts

## 10. Do Not Do First

새 PC에서 바로 하면 안 되는 것:

- `narrative_ssot` 전체 삭제
- `10_reference_bank` 전체 삭제
- `source_corpora`를 raw/normalized로 성급히 재분해
- `docs/실물기반 사각지대 테스트` provenance shell를 지금 당장 지우기
- `treatments/`, `bible/` live artifact root 건드리기

## 11. Practical Resume Prompt

다른 PC에서 이어받을 때는 아래 한 줄로 시작하면 된다.

`material_ssot cross-PC handoff 기준으로, platform_trends source_corpora cutover execution SSOT부터 이어서 진행`

## 12. 3-Pass Audit Note

Pass 1. Scope
- handoff 문서를 `material_ssot + research absorption + narrative_ssot blocker` 3축으로 제한

Pass 2. Evidence
- authority map, source map, absorption checklist, triage inventory, mirror audit, source_corpora design을 교차 확인

Pass 3. Closure
- 다음 행동을 `platform_trends source_corpora cutover` 하나로 수렴

Estimated Confidence: 96%
