# 전처리 SSOT 로드맵

> 사용자용 단일 안내 문서
> UTF-8 only
> 작성일: 2026-03-12

## 0. 이것만 읽으면 된다

사용자는 이 `README.md` 하나만 읽으면 된다.

내부 설명 문서는 모두 `전처리_ssot/docs/` 아래에 있고,
실행 계약 JSON은 `전처리_ssot/contracts/` 아래에 있다.

- 상위 오더: `docs/SSOT_stage0_preprocess_integrated_order.md`
- source manifest 규칙: `docs/stage0_source_manifest_harness.md`
- profile lock 규칙: `docs/stage0_profile_lock_harness.md`
- material collection 규칙: `docs/stage0_material_collection_harness.md`
- blockguide 미러: `docs/blockguide/`
- 구조 개혁 / `md + json` 전환 준비 문서: `docs/30_ops/migration_notes/`
- 실행 계약층: `contracts/`

핵심은 이거다.

- `전처리_ssot/` = 지휘소
- `전처리_ssot/docs/` = 전처리 문서 허브
- `전처리_ssot/contracts/` = 전처리 실행 계약층
- `treatments/preprocess/{work_id}/` = 작품별 생산기지
- `treatments/` = 최종 `Phase 0`, `TR`
- `bible/` = 최종 `BI`

## 1. 운영 철학

- `quality-first`가 최상위다.
- `auto-run`은 순서를 이어가라는 뜻이지, 스크립트 자동 실행 강제가 아니다.
- 기존 폴더는 건드리지 않는다. 당장은 `전처리_ssot/docs/`에 복사본, 미러, 정리본, 인덱스를 모은다.
- 전처리 허브는 "흩어진 자료를 한곳에 모아 보는 장소"다.
- 정본 경로는 계속 `treatments/`와 `bible/`이다.
- Production은 기본적으로 `블록 1개씩` 작성하고 감리한 뒤 다음 블록으로 간다.
- preprocess 작업공간에 block이 미리 차 있어도, 그게 곧바로 순차 production 완료를 뜻하지는 않는다.
- `Phase 0` 없이 TR 금지
- `TR draft` 없이 BI 금지
- 감리 PASS 전 완료 선언 금지
- UTF-8 only. `???`, `�`가 보이면 즉시 중단

## 2. 전처리 SSOT 표면 구조

`전처리_ssot/` 최상단은 단순하게 유지하되,
설명층과 계약층을 분리한다.

```text
전처리_ssot/
├── README.md
├── contracts/
│   ├── README.md
│   ├── schema_version.json
│   ├── stage_machine.json
│   ├── artifact_contracts.json
│   ├── quality_gates.json
│   ├── profile_catalog.json
│   ├── handoff_rules.json
│   ├── sequential_run_status.schema.json
│   └── audit_status.schema.json
└── docs/
    ├── SSOT_stage0_preprocess_integrated_order.md
    ├── stage0_source_manifest_harness.md
    ├── stage0_profile_lock_harness.md
    ├── stage0_material_collection_harness.md
    ├── 00_전처리_SSOT_1차_기획안.md
    ├── 01_TF_전처리기획_재감리_3pass.md
    ├── 02_TF_생산기지_감리_및_경로.md
    ├── 10_pitches/
    │   ├── incoming/
    │   ├── fixed/
    │   ├── rejected/
    │   └── canon/
    ├── 20_db_and_materials/
    │   ├── db/
    │   │   ├── domain_db/
    │   │   ├── entity_db/
    │   │   └── timeline_db/
    │   ├── materials/
    │   │   ├── genre_notes/
    │   │   ├── scene_bank/
    │   │   └── terminology/
    │   ├── local_refs/
    │   │   └── project_refs/
    │   ├── external_refs/
    │   │   └── web_refs/
    │   └── samples/
    │       └── golden/
    ├── 30_ops/
    │   ├── intake_queue/
    │   ├── source_manifests/
    │   ├── profile_locks/
    │   ├── phase0_ready_reviews/
    │   ├── migration_notes/
    │   ├── path_rules/
    │   └── handoffs/
    ├── 40_archive/
    │   ├── legacy_docs/
    │   └── superseded/
    ├── 50_indexes/
    ├── 2026-03-12/
    └── blockguide/
```

## 3. `docs/` 허브의 역할

### 3.1 `10_pitches/`

기획안과 원안 묶음이다.

- `incoming/`: 아직 정리되지 않은 투입 기획안
- `fixed/`: 정리 완료된 기획안
- `rejected/`: 폐기한 기획안
- `canon/`: 작품별 기준 기획안

즉, "기획안 폴더"는 여기다.

### 3.2 `20_db_and_materials/`

DB와 자료 허브다.

- `db/`: 구조화된 재료 DB
- `materials/`: 장르 노트, 장면 은행, 용어집
- `local_refs/`: 로컬 문서, 프로젝트 내부 참고 자료
- `external_refs/`: 외부 조사 메모, 웹 출처 정리
- `samples/`: 골든 샘플, 비교용 샘플

즉, "DB 및 자료 폴더"는 여기다.

### 3.3 `contracts/`

실행 계약층이다.

- 단계 판정
- 필수 산출물 계약
- quality gate
- 프로파일 카탈로그
- handoff 규칙

즉, "기계가 읽어야 하는 규칙"은 여기다.

추가:

- 작품별 상태 JSON 표준도 여기서 잠근다.
- 실제 인스턴스 경로는 `treatments/preprocess/{work_id}/sequential_run_status.json`, `audit_status.json`이다.

### 3.4 `30_ops/`

운영 문서와 handoff 허브다.

- intake queue
- source manifest 보관
- profile lock 보관
- phase0 ready review
- 경로 규칙
- handoff 메모
- migration note

즉, "지금 무엇이 들어왔고, 어디까지 확정됐는지"는 여기서 본다.

추가:

- `migration_notes/`는 갈아엎기 전 기준을 잠그는 문서 패키지다.
- 인간 설명은 `md`, 실행 계약은 `json`으로 가기 위한 cutover 기준은 여기서 먼저 읽는다.

### 3.5 `40_archive/`

옛 문서와 대체된 문서 격리 구역이다.

- `legacy_docs/`
- `superseded/`

정본 근처에 낡은 문서를 두지 않기 위한 곳이다.

### 3.6 `50_indexes/`

색인과 지도다.

- 문서 인벤토리
- 작품 레지스트리
- 경로 매핑

즉, "무엇이 어디 있는지"를 잃지 않기 위한 곳이다.

### 3.7 `blockguide/`

기존 blockguide 정본의 미러다.
전처리 관점에서 같이 읽어야 하는 문서를 모아 둔다.

### 3.8 `2026-03-12/`와 번호 문서

배경 문서, TF 감리, 개혁 메모를 보관한다.
정본 규칙보다 아래에 둔다.

## 4. 기존 폴더는 안 건드린다

이번 구조 개편의 원칙은 이렇다.

- 루트 `docs/`, `treatments/`, `bible/`는 그대로 둔다.
- `전처리_ssot/docs/`는 별도 허브로 키운다.
- 흩어진 문서를 여기로 "정리본/미러/색인" 형태로 모은다.
- 나중에 완전 이관이 필요하면 `30_ops/migration_notes/`에 계획을 남긴다.

즉, 지금은 이관보다 "허브화"가 먼저다.

## 5. 작품별 생산기지 트리

진짜 운영은 `treatments/preprocess/{work_id}/`에서 버틴다.
새 작품은 `treatments/preprocess/_template/`를 복제해서 시작한다.

```text
treatments/preprocess/{work_id}/
├── source_manifest.json
├── profile_lock.json
├── material_bundle_summary.json
├── phase0_ready_snapshot.json
├── 00_brief/
├── 01_source_pack/
├── 02_phase0_work/
├── 03_tr_blocks/
├── 04_tr_final/
├── 05_bi_work/
├── 06_release/
├── 07_archive/
└── docs/
    ├── progress_log.md
    ├── decisions.md
    ├── comparison_notes.md
    └── sequential_run_status.md
```

의미:

- `전처리_ssot/docs/` = 공용 허브
- `treatments/preprocess/{work_id}/` = 작품별 실작업 공간

둘은 역할이 다르다.

### 5.1 `sequential_run_status.md`는 왜 필요한가

작품별 생산기지에는 기존 canonical `TR`을 복제해 둔 seed baseline이 들어 있을 수 있다.
이건 참고용 작업 기반이지, SSOT가 요구하는 **실제 순차 production 기록**이 아니다.

그래서 진행률은 block 폴더 개수로 읽지 않고 아래 상태 파일로 읽는다.

- `treatments/preprocess/{work_id}/docs/sequential_run_status.md`
- 표준 target: `treatments/preprocess/{work_id}/sequential_run_status.json`

읽는 법:

- `run_class = seed_baseline_sync`
  - 지금 있는 block들은 참고용 seed다.
  - 실제 순차 production 진행률은 0 또는 명시된 값으로 본다.
- `run_class = sequential_production`
  - `last_sequential_block_pass = N`까지는 진짜 수동 감리 PASS로 쌓인 블록이다.
  - 다음 시작점은 `next_block`이다.

즉, **최고 번호 block 디렉터리나 `04_tr_final/` 존재만으로는 진행률을 판정하지 않는다.**

## 6. 단계와 게이트

작업 순서는 항상 아래 순서다.

1. `Stage 0 preprocess`
2. `Planning`
3. `Production`
4. `BI`
5. `Audit / Release`

Stage 0에서 Planning으로 넘어가려면 아래 4개가 있어야 한다.

- `source_manifest.json`
- `profile_lock.json`
- `material_bundle_summary.json`
- `phase0_ready_snapshot.json`

그리고 반드시:

- `phase0_ready_snapshot.manual_audit_pass == true`

하나라도 아니면 Planning 금지다.

Production 진입 해석:

- Production 재개 전에는 항상 `docs/sequential_run_status.md`를 읽는다.
- 상태 파일이 없거나 모호하면 `Block 001`부터 다시 간다.
- seed baseline만 있는 기지는 진짜 완주본으로 취급하지 않는다.

## 7. 무엇을 어디에 모을지

실무 기준은 이렇게 보면 된다.

- 작품 기획안: `전처리_ssot/docs/10_pitches/`
- 장르/소재 DB: `전처리_ssot/docs/20_db_and_materials/db/`
- 장르 노트/자료: `전처리_ssot/docs/20_db_and_materials/materials/`
- 프로젝트 내부 참고 자료: `전처리_ssot/docs/20_db_and_materials/local_refs/`
- 외부 참고 자료: `전처리_ssot/docs/20_db_and_materials/external_refs/`
- 골든 샘플/비교 샘플: `전처리_ssot/docs/20_db_and_materials/samples/`
- intake / handoff / review / migration: `전처리_ssot/docs/30_ops/`
- 오래된 문서: `전처리_ssot/docs/40_archive/`
- 색인: `전처리_ssot/docs/50_indexes/`

## 8. 3-Pass 고정 감리

### Pass 1. 구조 / 경로 감리

확인:

- `전처리_ssot/` 최상단에는 `README.md`와 `docs/`만 있는가
- 새로운 허브 폴더가 `docs/` 아래에 정리돼 있는가
- 기존 루트 폴더를 건드리지 않았는가

### Pass 2. 운영 / 역할 감리

확인:

- 기획안, DB, 자료, 운영, 아카이브, 색인의 역할이 분리돼 있는가
- `전처리_ssot/docs/`와 `treatments/preprocess/{work_id}/`의 역할이 섞이지 않는가
- Stage 0 계약 파일 4개와 Planning 진입 게이트가 유지되는가

### Pass 3. 실행자 친화성 / 무결성 감리

확인:

- 낮은 성능 모델도 이 README 하나만 보고 구조를 이해할 수 있는가
- "기획안 폴더", "DB 및 자료 폴더", "작품별 생산기지", "출고", "아카이브"가 모두 보이는가
- UTF-8 오염이 없는가

세 pass 중 하나라도 FAIL이면 구조는 미완성이다.

## 9. 결론

이제 사용자 기준은 이렇게 보면 된다.

- 읽을 문서: `전처리_ssot/README.md`
- 공용 전처리 허브: `전처리_ssot/docs/`
- 작품별 생산기지: `treatments/preprocess/{work_id}/`
- 최종 정본: `treatments/`, `bible/`

즉, 표면은 단순하게 유지하되,
실제 운영은 `전처리_ssot/docs/` 허브와 작품별 생산기지 트리로 버티는 구조다.
