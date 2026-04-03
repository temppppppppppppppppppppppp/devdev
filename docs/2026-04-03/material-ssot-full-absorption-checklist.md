# material_ssot 완전 흡수 체크리스트 v0.1

Date: 2026-04-03
Status: bootstrap completion checklist
Scope: `material_ssot`를 재료 사이드 오더의 실질 단일 SSOT라고 부르기 위해 남은 흡수 조건을 정의한다

## 1. Purpose

현재 `material_ssot`는 재료 사이드 오더의 `stage authority`로는 이미 작동한다.

하지만 아래 old root가 여전히 남아 있어, 운영자가 체감하는 `단일 SSOT` 상태는 아직 아니다.

- `narrative_ssot`
- `docs/실물기반 사각지대 테스트`
- `로직_리서치`

이 문서의 목적은:

- 각 old root가 현재 어느 단계까지 흡수됐는지 판정
- 무엇이 끝나야 `material_ssot가 진짜 SSOT다`라고 말할 수 있는지 completion gate를 정의
- 이후 웨이브 순서를 저위험 기준으로 고정

## 2. Current Status Snapshot

| Path | Current status | Current interpretation |
| --- | --- | --- |
| `narrative_ssot` | not absorbed | scaffold / pilot structure candidate |
| `docs/실물기반 사각지대 테스트` | mostly absorbed in authority terms | residual provenance and pointer root |
| `로직_리서치` | mostly absorbed in authority terms | legacy runtime note root |

## 3. Completion Standard

`material_ssot`를 진짜 SSOT라고 부르려면 아래 다섯 조건이 동시에 맞아야 한다.

1. 사람이 읽는 재료 사이드 오더의 첫 진입점이 `material_ssot` 하나뿐이다.
2. old root는 `pointer`, `archive`, `scaffold-frozen` 중 하나로만 남고 새 payload를 받지 않는다.
3. collector / reference / analysis / material-pack이 모두 `material_ssot` 기준 경로로 연결된다.
4. governance 문서와 실제 폴더 상태가 일치한다.
5. stale path sweep에서 old root를 current authority처럼 가리키는 active 문서가 남지 않는다.

## 4. Path-by-Path Checklist

### A. `로직_리서치`

현재 달성:

- collector code moved to `scripts/research_collectors/`
- runtime outputs write into `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`
- raw ingest writes into `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`
- old root has only:
  - `README.md`
  - `ORDER_youtube_parallel.md`
  - `output/README.md`

완전 흡수 완료 조건:

- old root에 executable script가 0개다
- old root에 새 output 파일이 더 이상 생성되지 않는다
- operator note가 registry 정본으로만 유지된다
- 필요 시 old root를 `archive` 또는 `legacy_note_root`로 rename/freeze 한다

남은 일:

- low risk: current state 유지 후 later wave에서 old root archive 여부 결정

판정:

- authority 기준으로는 `거의 종료`
- physical cleanup 기준으로는 `archive decision` 1개 남음

### B. `docs/실물기반 사각지대 테스트`

현재 달성:

- reference profiles moved into `material_ssot/10_research/10_reference_profiles/`
- few-shot bank moved into `material_ssot/10_research/20_fewshot_bank/`
- analysis reports moved into `material_ssot/10_research/40_analysis/pattern_reports/`
- bounded top-level corpus bundles moved into `material_ssot/10_research/50_corpus_curated/`
- longtail title corpus moved into `material_ssot/10_research/60_corpus_longtail/`
- old `few-shot-bank` is pointer-only

아직 남은 실데이터:

- `원고/manifest.json`
- `원고/errors.log`
- `원고/titles/README.md`
- `분석/` pointer surface
- `분석결과_회차간_연결패턴_분석.md` pointer surface

완전 흡수 완료 조건:

- remaining provenance files get either:
  - explicitly retained as provenance-only legacy evidence, or
  - archived outside the active authority lane
- old root stays pointer-only and receives no new payloads

남은 일:

- Wave 2 complete: `분석/` 흡수
- Wave 3 complete: curated `원고/` 흡수
- Wave 4 complete: longtail raw corpus migration
- later wave: provenance-only shell retention or archive decision

판정:

- `권위 기준으로는 거의 종료`
- 남은 것은 authority split보다 provenance shell 정리 문제에 가깝다

### C. `narrative_ssot`

현재 상태:

- `00_governance`
- `10_reference_bank`
- `30_harness`
- `40_contracts`
- `50_projects`
- `90_migration`

현재 해석:

- stage SSOT 아님
- scaffold / pilot candidate
- 일부 내용은 이미 `material_ssot` 또는 `docs/narrative-router`와 역할이 겹친다

완전 흡수 완료 조건:

- folder-by-folder triage가 끝난다:
  - absorb to `material_ssot`
  - move to `docs/narrative-router`
  - archive
  - delete candidate
- 새 작업이 이 경로를 active entry로 사용하지 않는다
- root README가 `scaffold-frozen` 또는 `archived` 상태로 고정된다
- `50_projects` pilot residue 처리 방침이 결정된다

남은 일:

- triage inventory 문서 작성
  - saved as `docs/2026-04-03/narrative-ssot-triage-inventory.md`
- `10_reference_bank` mirror 필요성 재판정
  - saved as `docs/2026-04-03/narrative-reference-bank-mirror-necessity-audit.md`
- `10_reference_bank/source_corpora` bounded cutover 설계
  - saved as `docs/2026-04-03/narrative-source-corpora-bounded-cutover-design.md`
- `30_harness`와 `40_contracts`의 실제 유효 자산만 분리 흡수
- 이후 archive or freeze

판정:

- `미흡수`
- 현재 단일 SSOT 체감에 가장 큰 구조적 잡음

## 5. Recommended Order

가장 안전한 순서는 아래다.

1. `로직_리서치`는 현 상태를 유지한 채 archive/freeze naming만 later wave에서 결정
2. `narrative_ssot` triage inventory 작성
3. `narrative_ssot`를 freeze 또는 archive로 내림
4. stale path sweep으로 old authority reference 정리
5. `docs/실물기반 사각지대 테스트` provenance shell archive 여부 later wave에서 결정

이 순서가 좋은 이유:

- `로직_리서치`는 이미 권위 분리가 거의 끝나서 급하지 않다
- `docs/실물기반 사각지대 테스트`는 이제 provenance shell에 가깝다
- `narrative_ssot`는 성격상 구조 triage가 먼저지, 즉시 이동이 먼저가 아니다

## 6. Practical Gate

현 시점 운영 문장으로는 이렇게 쓰는 게 정확하다.

`material_ssot는 재료 사이드 오더의 stage SSOT로는 이미 유효하다. research root는 거의 provenance shell만 남았지만, scaffold root가 남아 있어 아직 repo-wide 단일 material root라고 부르기에는 이르다.`

아래가 끝나면 문장을 더 세게 바꿀 수 있다.

- `narrative_ssot` freeze or archive
- `로직_리서치` archive naming 확정
- `docs/실물기반 사각지대 테스트` provenance shell retention policy 확정

그 시점의 최종 문장:

`material_ssot is the single active SSOT root for the material-side order.`

## 7. 3-Pass Audit Note

Pass 1. Scope
- `완전 흡수`를 파일 이동 여부가 아니라 authority completion gate로 정의

Pass 2. Evidence
- three old roots의 현재 잔존 폴더와 governance 문서 상태를 대조

Pass 3. Closure
- each root별 완료 조건과 저위험 실행 순서를 고정

Estimated Confidence: 96%
