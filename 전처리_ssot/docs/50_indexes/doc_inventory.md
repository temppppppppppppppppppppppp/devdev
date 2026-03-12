# doc_inventory

> snapshot: 2026-03-12
> 목적: `전처리_ssot/docs/` 아래 문서와 허브의 역할을 한 번에 파악하기 위한 색인

## 1. 사용 지침

- 이 문서는 `전처리_ssot/docs/` 전체 인벤토리다.
- 기존 루트 `docs/`는 건드리지 않고, 여기서는 `정본`, `미러`, `배경`, `허브`, `준비 문서`를 구분한다.
- 사용자가 먼저 읽을 문서는 `전처리_ssot/README.md`이고, 이 문서는 운영자용 상세 인벤토리다.

## 2. 상위 SSOT / 전달 규칙

| path | role | class | note |
| --- | --- | --- | --- |
| `docs/SSOT_stage0_preprocess_integrated_order.md` | 전처리 상위 오더 | `canonical` | Stage 0 진입 순서와 완료 판정 |
| `docs/stage0_source_manifest_harness.md` | source manifest 규칙 | `canonical` | Stage 0 계약 파일 1 |
| `docs/stage0_profile_lock_harness.md` | profile lock 규칙 | `canonical` | Stage 0 계약 파일 2 |
| `docs/stage0_material_collection_harness.md` | material collection 규칙 | `canonical` | Stage 0 자료 수집 규칙 |

## 2A. 실행 계약층

| path | role | class | note |
| --- | --- | --- | --- |
| `../contracts/README.md` | contracts 안내 | `execution-guide` | 설명층과 계약층 연결 |
| `../contracts/schema_version.json` | 계약 패키지 버전 | `execution-contract` | 패키지 메타와 포함 파일 |
| `../contracts/stage_machine.json` | 단계 판정 계약 | `execution-contract` | stage detection과 resume 규칙 |
| `../contracts/artifact_contracts.json` | 산출물 계약 | `execution-contract` | 필수 파일과 최소 키 |
| `../contracts/quality_gates.json` | 품질 게이트 | `execution-contract` | stop/go와 hard/soft fail |
| `../contracts/profile_catalog.json` | 프로파일 카탈로그 | `execution-contract` | all-genre profile 정의 |
| `../contracts/handoff_rules.json` | handoff 규칙 | `execution-contract` | 단계 전환 조건 |
| `../contracts/sequential_run_status.schema.json` | 순차 상태 표준 스키마 | `execution-contract` | 작품별 production resume 상태 표준 |
| `../contracts/audit_status.schema.json` | 감리 상태 표준 스키마 | `execution-contract` | 작품별 audit 상태 표준 |

## 3. 배경 문서 / TF 감리

| path | role | class | note |
| --- | --- | --- | --- |
| `docs/00_전처리_SSOT_1차_기획안.md` | 전처리 기지 초기 기획안 | `background` | 초안, 현행 진실 아님 |
| `docs/01_TF_전처리기획_재감리_3pass.md` | 초기 기획 TF 재감리 | `background` | 구조 개혁 근거 |
| `docs/02_TF_생산기지_감리_및_경로.md` | 생산기지/경로 감리 | `background` | 허브 구조 개혁 근거 |
| `docs/2026-03-12/codex_stage0_preprocess_tr_bi_foundation_plan.md` | Codex 설계 배경 문서 | `background` | 상설 SSOT 이전 설계안 |

## 4. blockguide 미러

| path | role | class | note |
| --- | --- | --- | --- |
| `docs/blockguide/SSOT_blockguide-integrated-order.md` | Planning/TR/BI 상위 오더 미러 | `mirror` | 루트 blockguide 정본 미러 |
| `docs/blockguide/treatment-planning-harness.md` | Planning 하네스 미러 | `mirror` | Phase 0 작성 규칙 |
| `docs/blockguide/treatment-production-harness-v2.md` | TR 하네스 미러 | `mirror` | block 1개씩 작성 규칙 |
| `docs/blockguide/bi-production-harness-v1.md` | BI 하네스 미러 | `mirror` | BI 최소 계약 / 5-pass |
| `docs/blockguide/modern_fantasy_material_harness.md` | 현대판타지 재료 하네스 미러 | `mirror` | Stage 0와 연결됨 |
| `docs/blockguide/alt_history_db_harness.md` | 대체역사 DB 하네스 미러 | `mirror` | alt_history 전용 |
| `docs/blockguide/TF-BH1_block_harness_reinforcement.md` | 실패작 기반 하네스 보강안 | `reference` | 루프/반복 보강 |
| `docs/blockguide/harness_3pass_audit_and_patch.md` | Opus 하네스 감리 패치안 | `reference` | planning/production 개선 근거 |
| `docs/blockguide/codex_comment_on_harness_3pass_audit_and_patch.md` | Codex 코멘트 | `reference` | patch 방향 보정 |
| `docs/blockguide/codex_r31_tail_repetition_recalibration.md` | R31 규칙 재조정 | `reference` | repetition 규칙 수정안 |

## 5. 허브 폴더

| path | role | class | note |
| --- | --- | --- | --- |
| `docs/10_pitches/` | 기획안 허브 | `hub` | incoming / fixed / rejected / canon |
| `docs/20_db_and_materials/` | DB/자료 허브 | `hub` | db / materials / refs / samples |
| `docs/30_ops/` | 운영 허브 | `hub` | intake / manifest / lock / review / migration |
| `docs/40_archive/` | 아카이브 허브 | `hub` | legacy / superseded 격리 |
| `docs/50_indexes/` | 색인 허브 | `hub` | inventory / registry / migration map |

## 6. 허브 하위 문서

| path | role | class | note |
| --- | --- | --- | --- |
| `docs/10_pitches/README.md` | 기획안 허브 설명 | `hub-guide` | 기획안 분류 기준 |
| `docs/20_db_and_materials/README.md` | DB/자료 허브 설명 | `hub-guide` | 자료 수집 분류 기준 |
| `docs/20_db_and_materials/db/README.md` | DB 영역 설명 | `hub-guide` | domain/entity/timeline |
| `docs/20_db_and_materials/materials/README.md` | 비정형 자료 설명 | `hub-guide` | genre_notes/scene_bank/terminology |
| `docs/20_db_and_materials/local_refs/README.md` | 로컬 참고 자료 설명 | `hub-guide` | 프로젝트 내부 자료 묶음 |
| `docs/20_db_and_materials/external_refs/README.md` | 외부 참고 자료 설명 | `hub-guide` | 조사 메모와 웹 출처 |
| `docs/20_db_and_materials/samples/README.md` | 샘플 설명 | `hub-guide` | 골든/비교 샘플 |
| `docs/30_ops/README.md` | 운영 허브 설명 | `hub-guide` | intake/handoff/review |
| `docs/30_ops/migration_notes/README.md` | 마이그레이션 노트 설명 | `hub-guide` | `md + json` 전환 준비 패키지 |
| `docs/30_ops/migration_notes/md_json_migration_charter.md` | MD/JSON 전환 헌장 | `canonical-prep` | 개편 목적, 범위, cutover/rollback |
| `docs/30_ops/migration_notes/md_json_contract_inventory.md` | MD/JSON ownership 표 | `canonical-prep` | 설명층/계약층 분리 |
| `docs/30_ops/migration_notes/json_contracts_roadmap.md` | JSON 계약층 로드맵 | `canonical-prep` | 상위 계약과 작품 상태 JSON 도입 순서 |
| `docs/30_ops/migration_notes/json_schema_package_plan.md` | JSON 스키마 패키지 계획 | `canonical-prep` | 패키지 구조, versioning, slot 설계 |
| `docs/30_ops/migration_notes/md_json_migration_95_confidence_audit.md` | 95% confidence 감리 | `canonical-prep` | 문서 패키지 자체의 3-pass audit |
| `docs/30_ops/migration_notes/json_contracts_seed_3pass_audit.md` | JSON 계약 시드 감리 | `canonical-prep` | 실제 JSON 파일 3-pass audit |
| `docs/30_ops/path_rules/README.md` | 경로 규칙 | `hub-guide` | 파일명/경로 운영 규칙 |
| `docs/30_ops/handoffs/README.md` | handoff 가이드 | `hub-guide` | 단계 전환 메모 |
| `docs/40_archive/README.md` | 아카이브 설명 | `hub-guide` | 오래된 문서 격리 |
| `docs/50_indexes/README.md` | 색인 허브 설명 | `hub-guide` | index 계층 안내 |
| `docs/50_indexes/doc_inventory.md` | 현재 문서 인벤토리 | `canonical-index` | 지금 이 파일 |
| `docs/50_indexes/work_registry.md` | 작품 레지스트리 | `canonical-index` | work_id별 정본/레거시 상태 |
| `docs/50_indexes/migration_map.md` | 경로 매핑 | `canonical-index` | 루트 -> 허브 매핑 |

## 7. 운영상 중요한 구분

### 7.1 `canonical`

지금 직접 따라야 하는 규칙 문서다.

### 7.2 `mirror`

루트 정본을 전처리 허브에서도 같이 읽게 복제한 문서다.
원본 경로를 없앴다는 뜻은 아니다.

### 7.3 `background`

왜 이런 구조가 맞는지 설명하는 근거 문서다.
현행 규칙보다 우선하지는 않는다.

### 7.4 `canonical-prep`

아직 구현 전이지만, 갈아엎기 전 기준을 잠그는 준비 문서다.
`md + json` 구조 전환은 이 문서들을 통과한 뒤에만 시작한다.

### 7.5 `hub`

문서를 분류하고 모아두는 장소다.

## 8. 다음 운영 우선순위

1. `migration_notes` 기준으로 JSON 계약층 준비 범위를 더 이상 흔들지 않는다.
2. `work_registry.md`를 실제 작품 기준으로 계속 갱신한다.
3. `migration_map.md`에 루트 경로와 허브 경로 관계를 계속 추가한다.
4. 실제 JSON 계약 구현은 95% confidence audit 이후에만 시작한다.
