# 재료 사이드 오더 SSOT 설계안 v0.1

Date: 2026-04-03
Status: bootstrap design baseline
Scope: material-side stage SSOT only
Execution Rule: 본 문서는 구조 설계 정본이며 즉시 폴더 이동을 뜻하지 않는다. raw research bucket은 이번 웨이브에서 이동하지 않으며, 현재 확인된 deferred bucket은 `로직_리서치`다.
Implementation Note: 2026-04-03 same-day bounded cutover로 legacy pitch payload bundle은 `material_ssot/20_pitch/intake/legacy_import/` 아래로 옮겼고, pitch-adjacent QA summaries는 `material_ssot/20_pitch/quarantine/`으로 분리했다. 같은 날 research Wave 1로 reference profiles와 few-shot bank를 `material_ssot/10_research/` 아래로 옮겼다. 이어서 work-level normalized research handoff를 위해 `material_ssot/10_research/30_work_materials/`를 열고 bootstrap material packs를 만들었다. Research Wave 2로 long-form analysis reports를 `material_ssot/10_research/40_analysis/pattern_reports/`로 옮겼고, Research Wave 3로 bounded top-level corpus bundles를 `material_ssot/10_research/50_corpus_curated/`로 옮겼다. 현재 잔여 raw corpus는 주로 `docs/실물기반 사각지대 테스트/원고/titles/`에 남아 있다.

## 1. Purpose

글도비의 서사 생산 준비 축을 `재료 사이드 오더` 기준으로 다시 묶기 위한 stage SSOT 설계 문서다.

이번 설계의 목표는 아래 세 가지다.

- `리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성` 을 공식 stage chain으로 고정
- 각 단계의 현재 authoritative path와 legacy / mirror / non-move 경계를 먼저 문서로 확정
- 실제 폴더 이동 전에 단계별 read order와 migration 순서를 안전하게 제한

이 문서는 `재료 사이드 오더`만 다룬다. `글도비 파이프라인`과 시스템 트랙은 별도 축으로 유지한다.

## 2. Official Stage Chain

이 설계에서 공식으로 고정하는 재료 사이드 오더 상위 체인은 아래다.

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성`

이 stage chain은 작품 생산 준비와 서사 산출물 생성의 기준 순서를 뜻한다.

다만 이 문서는 family 축을 대체하지 않는다. family 라우팅은 계속 `docs/narrative-router`가 맡는다.

## 3. Governance Boundary

이 설계의 경계는 아래처럼 둔다.

- 이 문서는 `stage axis` SSOT다.
- `family axis`는 계속 `docs/narrative-router`가 담당한다.
- `system axis`는 계속 `글도비 파이프라인` 쪽 문서와 시스템 트랙이 담당한다.
- `treatments/`, `bible/`는 당분간 live artifact path로 유지한다.
- raw research는 당분간 stage SSOT 안으로 물리 이동하지 않는다.

즉, 이번 설계는 폴더 통합보다도 `단계 기준과 권위 경계`를 먼저 세우는 작업이다.

## 4. Current Snapshot

2026-04-03 현재 확인 기준으로 가장 안전한 해석은 아래다.

### A. 리서치

- stage root: `material_ssot/10_research`
- canonical reference profiles: `material_ssot/10_research/10_reference_profiles`
- canonical few-shot bank: `material_ssot/10_research/20_fewshot_bank`
- normalized work material packs: `material_ssot/10_research/30_work_materials`
- canonical analysis reports: `material_ssot/10_research/40_analysis/pattern_reports`
- canonical curated corpus bundles: `material_ssot/10_research/50_corpus_curated`
- residual raw corpus root: `docs/실물기반 사각지대 테스트/원고/titles`
- mirror / scaffold candidate: `narrative_ssot/10_reference_bank`
- deferred raw logic research bucket: `로직_리서치`
- any additional raw research bucket:
  - 이번 웨이브에서는 비이동 원칙으로만 다룬다.
  - 필요 시 이후 source-map에 reserved slot으로만 연결한다.

### B. 기획안

- current best canonical hub: `전처리_ssot/docs/10_pitches`
- legacy pitch bundle: `전처리_ssot/기획안`
- problem: pitch authority가 이미 `docs/10_pitches`와 `기획안`으로 이중화되어 있다.

### C. Stage 0 preprocess

- governance hub: `전처리_ssot`
- live preprocess artifacts: `treatments/preprocess/{work_id}`
- scaffold candidate: `narrative_ssot`

현재는 governance와 live artifacts가 분리되어 있고, stage naming도 `전처리_ssot`에 과도하게 묶여 있다.

### D. Phase 0 design

- live phase0 artifacts: `treatments/phase0/{work_id}_phase0_design.json`
- preprocess-side snapshots: `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`
- note: 현재 phase0 축은 live root file과 preprocess snapshot이 함께 존재한다.

### E. TR 생성

- live TR artifacts: `treatments/*_tr_block_070_draft.json`
- note: 2026-04-03 기준 routed / harness 경로에서 생성되는 TR은 canonical contract를 보장한다.

### F. BI 생성

- live BI artifacts: `bible/0_bi_{work_id}.json`
- note: 2026-04-03 기준 routed / harness 경로에서 생성되는 BI는 canonical contract를 보장한다.

## 5. Main Problem

현재 구조의 문제는 폴더 수가 아니라, `stage authority`, `family router`, `scaffold`, `legacy`, `live artifact path`가 서로 다른 축인데 루트에서 섞여 보인다는 점이다.

대표 증상은 아래와 같다.

- 리서치 authoritative source와 mirror가 분리되어 있다.
- 기획안 canonical hub와 legacy bundle이 동시에 살아 있다.
- Stage 0 governance path와 live preprocess artifact path가 분리되어 있다.
- Phase 0 / TR / BI는 live path가 분명하지만 상위 stage SSOT가 없다.
- `전처리_ssot`라는 이름은 실제로는 `기획안~Stage 0`을 넘어서 전체 material-side 흐름 설명에 쓰이기에는 범위가 좁다.

즉, 지금 필요한 것은 폴더 이동이 아니라 `재료 사이드 오더용 stage SSOT`를 별도로 세우는 것이다.

## 6. Target Decision

이번 설계는 `전처리_ssot`를 계속 확장하는 대신, 새 root stage SSOT를 세우는 방향을 권장한다.

권장 root 이름:

`material_ssot`

권장 이유는 아래와 같다.

- `전처리_ssot`는 이름상 `기획안`, `TR`, `BI`까지 포괄하기 어렵다.
- `material_ssot`는 `리서치 -> 기획안 -> preprocess -> phase0 -> tr -> bi` 전체 stage chain을 자연스럽게 담는다.
- family router와 구분되는 `stage-only SSOT`라는 의미가 명확하다.

## 7. Target Structure

권장 목표 구조는 아래다.

```text
material_ssot/
  00_governance/
    README.md
    authority-map.md
    stage-read-order.md
    legacy-map.md

  10_research/
    README.md
    source-map.md
    manifests/
    30_work_materials/
      {work_id}/
        00_sources/
        10_user_agreements.md
        20_fact_lock.json
        30_domain_map.md
        40_narrative_seed_bank.json
        50_pattern_refs.md
        60_gap_log.md
        90_material_pack.json
    40_analysis/
      market_snapshots/
      pattern_reports/
    50_corpus_curated/

  20_pitch/
    README.md
    canon/
    intake/
      legacy_import/
        supporting/
    quarantine/
    archive/

  30_stage0_preprocess/
    README.md
    contracts/
    work-index/

  40_phase0_design/
    README.md
    contracts/
    work-index/

  50_tr/
    README.md
    contracts/
    work-index/

  60_bi/
    README.md
    contracts/
    work-index/

  90_migration/
    pending-cuts.md
```

중요한 원칙은 `material_ssot`가 산출물 저장소가 아니라 `authority map + read order + manifest hub`라는 점이다.

즉, 실제 live artifacts는 당분간 아래 경로에 그대로 둔다.

- preprocess live: `treatments/preprocess/{work_id}`
- phase0 / tr live: `treatments/`
- bi live: `bible/`

## 8. Stage Roles

### A. `10_research`

- raw corpus를 바로 옮기지 않는다.
- `로직_리서치`와 `docs/실물기반 사각지대 테스트`를 source map으로 관리한다.
- canonical reference pack과 few-shot bank를 이 stage 아래 둔다.
- work-level normalized research handoff는 `30_work_materials/{work_id}` 아래에서 관리한다.
- 각 work pack은 `user agreements -> fact lock -> domain map -> narrative seed bank -> pattern refs -> gap log -> material pack` 순서로 정규화한다.
- 추가 raw research bucket이 생기더라도 이 웨이브에서는 reserved source slot으로만 연결한다.
- 즉, raw storage가 아니라 `research authority + normalized handoff hub` 역할을 맡는다.

### B. `20_pitch`

- 기획안의 canonical hub를 맡는다.
- `전처리_ssot/docs/10_pitches`는 legacy transition hub로 유지한다.
- legacy pitch payload bundle은 `material_ssot/20_pitch/intake/legacy_import/` 아래로 bounded cutover한다.
- `전처리_ssot/기획안`은 frozen pointer path로 내린다.

### C. `30_stage0_preprocess`

- Stage 0 preprocess의 contract, gate, work index를 맡는다.
- live preprocess 파일은 계속 `treatments/preprocess/{work_id}`에 남긴다.

### D. `40_phase0_design`

- Phase 0 design의 기준 contract와 work index를 맡는다.
- live phase0 JSON은 계속 `treatments/`에 남긴다.

### E. `50_tr`

- TR contract와 work index를 맡는다.
- live TR draft는 계속 `treatments/`에 남긴다.

### F. `60_bi`

- BI contract와 work index를 맡는다.
- live BI는 계속 `bible/`에 남긴다.

## 9. Non-Move Rules

이번 재료 사이드 오더 SSOT 웨이브는 아래 비이동 원칙을 가진다.

- raw research bucket은 이동하지 않는다.
- 현재 식별된 deferred raw research bucket인 `로직_리서치`도 이동하지 않는다.
- `docs/narrative-router`는 그대로 family SSOT로 둔다.
- `treatments/`, `bible/`는 live output path로 그대로 둔다.
- `narrative_ssot`는 scaffold로 유지한다.
- `전처리_ssot`는 즉시 삭제하지 않고 legacy / transition hub로 유지한다.
- `전처리_ssot/기획안`은 payload write path로 더 이상 쓰지 않는다.

## 10. Migration Sequence

실제 구현은 아래 순서로만 진행한다.

1. 설계 문서 고정
2. `material_ssot` 폴더 스켈레톤 생성
3. `00_governance` 문서 3종 생성
4. 각 stage의 `README + work-index` 생성
5. 각 `work_id`별 manifest 연결
6. 기존 경로에 `canonical / legacy / scaffold / mirror` 라벨 부여
7. 마지막에만 필요 시 실제 폴더 이동 또는 cutover 판단

즉, 초기 웨이브는 `문서와 index의 정리`이지 `대규모 파일 이동`이 아니다.

## 11. Immediate Implementation Recommendation

다음 액션은 아래처럼 제한하는 것이 가장 안전하다.

- 1단계: 이 설계 문서를 기준선으로 채택
- 2단계: `material_ssot/00_governance`와 stage 디렉터리 스켈레톤만 생성
- 3단계: `authority-map.md`, `stage-read-order.md`, `legacy-map.md` 작성
- 4단계: raw research bucket은 source map에만 연결하고, 현재는 `로직_리서치`만 명시 연결
- 5단계: `전처리_ssot`와 `narrative_ssot`는 당분간 라벨링만 하고 비이동 유지

## 12. Conclusion

재료 사이드 오더 SSOT는 아래 chain만 전담한다.

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성`

이 stage chain은 새 `material_ssot` root 아래에서 관리하고, family router와 시스템 오더는 별도 축으로 유지한다.

핵심 방침은 아래다.

- `재료 사이드 오더`만 stage SSOT로 분리
- raw research bucket은 이번 웨이브 비이동
- 현재 명시 연결 대상은 `로직_리서치`
- live artifacts는 기존 경로 유지
- 먼저 문서 / authority map / work manifest부터 정리
- cutover는 마지막 단계에서만 판단

## 13. 3-Pass Audit Note

Pass 1. Structure and scope
- `재료 사이드 오더`만 다루는 stage SSOT 설계 문서로 범위 고정
- family axis와 system axis를 명시적으로 제외

Pass 2. Evidence and consistency
- 2026-04-03 현재 root와 `전처리_ssot`, `narrative_ssot`, `docs`, `treatments`, `bible`, `로직_리서치`를 다시 확인
- raw research는 비이동 원칙으로만 다루고, 현재 명시 연결 대상은 `로직_리서치`로 정리

Pass 3. Execution and readability
- 폴더 이동보다 문서 고정과 스켈레톤 생성이 먼저라는 구현 순서를 명시
- 바로 실행 가능한 migration sequence와 non-move rules를 분리해서 기록

Estimated Confidence: 96%
