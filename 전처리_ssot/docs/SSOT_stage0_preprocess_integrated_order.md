# Stage 0 전처리 SSOT 통합 오더 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 역할: 현대판타지 전 장르의 `Phase 0 -> TR -> BI` 앞단에 놓이는 **전처리 SSOT 엔트리**
> 현재 진실: `C:\Users\wjjo\Desktop\글도비\전처리_ssot`
> 사용자용 단일 로드맵: `C:\Users\wjjo\Desktop\글도비\전처리_ssot\README.md`

---

## 0. 이 문서를 언제 읽는가

아래 중 하나라도 해당하면 이 문서를 **반드시** 읽는다.

1. 어떤 `work_id`든 처음 파이프라인에 진입한다.
2. 사용자가 `자료 먼저`, `근거 붙여`, `DB`, `레퍼런스`, `전처리`, `source_manifest`를 말한다.
3. `phase0_design`이 아직 없고, 작품의 업계/직업/현장 재료가 필요하다.
4. 사용자가 장르만 던지고 “방향 잡아 달라”고 한다.
5. 투자물, 엔터물, 의학물, 회사원/조직 권력물, 테크 창업물, urban power 계열처럼 실무 디테일이 품질을 좌우한다.
6. 사용자가 구조 개혁, 기반 시설, 계약층, `md + json` 전환을 말한다.

원칙:

- `Stage 0 preprocess`는 선택 기능이 아니다. **현대판타지 전 장르의 필수 선행 단계**다.
- `auto-run`은 단계 순서를 이어 간다는 뜻이지, 스크립트를 자동 실행하라는 뜻이 아니다.
- 자동화는 허용되지만, **정본 확정은 수동 감리 없이는 불가**다.

---

## 1. 읽기 순서

Stage 0 작업은 아래 순서로 읽는다.

1. 현재 문서 `SSOT_stage0_preprocess_integrated_order.md`
2. `stage0_source_manifest_harness.md`
3. `stage0_profile_lock_harness.md`
4. `stage0_material_collection_harness.md`
5. 구조 개혁이나 계약층 전환 논의면 `30_ops/migration_notes/README.md`
6. 실행 계약이 필요하면 `../contracts/README.md`
7. 그다음 `docs/blockguide/SSOT_blockguide-integrated-order.md`
8. 이후 현재 단계에 맞는 `treatment-planning-harness.md`, `treatment-production-harness-v2.md`, `bi-production-harness-v1.md`

해석:

- 이 문서 묶음은 `전처리 SSOT`
- `docs/blockguide` 문서 묶음은 `Planning / Production / BI SSOT`

즉, **Stage 0를 끝내고 나서야** blockguide의 일반 단계 문서로 넘어간다.

---

## 2. Stage 0 정식 산출물 경로

Stage 0 완료를 판정하는 중간 산출물 경로는 아래 4개로 고정한다.

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

최종 정본 경로는 기존과 같다.

- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

중간 산출물은 정본이 아니지만, **Stage 0 계약을 잠그는 정식 체크포인트**다.

## 2A. Production handoff 상태 파일

Stage 0가 끝난 뒤 preprocess 작업공간이 이미 채워져 있더라도, 그것이 곧바로
진짜 순차 production 진행률을 뜻하지는 않는다.

그래서 Production handoff에는 아래 상태 파일을 같이 둔다.

- `treatments/preprocess/{work_id}/docs/sequential_run_status.md`
- 표준 target: `treatments/preprocess/{work_id}/sequential_run_status.json`
- 표준 schema: `../contracts/sequential_run_status.schema.json`

이 파일의 목적:

- preprocess 작업공간이 단순 seed인지
- 실제 순차 production이 어디까지 진행됐는지
- compaction 뒤 어디서 다시 시작해야 하는지

최소 필수 슬롯:

```text
run_class: seed_baseline_sync | sequential_production
last_sequential_block_pass: 0..70
next_block: Block 001..070 | merge | BI_handoff
manual_audit_ready: true | false
notes: free text
```

핵심 규칙:

- `seed_baseline_sync`는 canonical 출력물 복제/정리 상태이며 참고용 seed일 뿐이다.
- `sequential_production`만 실제 production 진행률로 인정한다.
- 상태 파일이 없고 workspace가 미리 채워져 있으면, 기본값은 `seed_baseline_sync`로 본다.
- 이 상태 파일은 **Stage 0 완료 필수 산출물 4개에는 포함되지 않지만**, Production handoff의 기준 상태 파일이다.
- 현재는 `md` fallback을 허용하지만, JSON 표준 스키마와 target path는 이미 고정됐다.

---

## 3. 현재 단계 판정

| 조건 | 현재 단계 | 기본 행동 |
| ---- | --------- | --------- |
| 전처리 산출물 4개 중 하나라도 없음 | `Stage 0 preprocess` | Stage 0 문서 3종을 따라 산출물부터 만든다 |
| 전처리 산출물은 있으나 `phase0_ready_snapshot.manual_audit_pass != true` | `Stage 0 preprocess` | 수동 감리 메모를 보강하고 snapshot을 다시 잠근다 |
| 전처리 산출물 4개 모두 있고 `phase0_design` 없음 | `Planning` | `treatment-planning-harness.md`로 간다 |
| `phase0_design` 있음, `tr_block_070_draft` 없음 | `Production` | `treatment-production-harness-v2.md`로 간다 |
| `tr_block_070_draft` 있음, `0_bi_{work_id}.json` 없음 | `BI` | `bi-production-harness-v1.md`로 간다 |
| `BI` 있음, 감리 FAIL | `Audit / Repair` | 실패 원인 분석 후 필요한 단계만 재진입 |

핵심 해석:

- `Stage 0 preprocess`가 끝나지 않으면 `phase0_design` 작성 금지
- `manual_audit_pass`가 `true`가 아니면 Planning 진입 금지
- 전처리 산출물이 있어도 UTF-8 파싱이 깨지면 없는 것으로 본다

---

## 4. 초저지능 LLM용 빠른 시작

낮은 성능 모델도 아래 12단계만 따라가면 된다.

1. `work_id`를 잡는다.
2. `treatments/preprocess/{work_id}/...` 4개 파일이 있는지 확인한다.
3. 없으면 Stage 0부터 시작한다.
4. `stage0_profile_lock_harness.md`를 보고 주 프로파일 1개와 보조 프로파일 0~1개를 정한다.
5. `stage0_material_collection_harness.md`를 보고 자료를 우선순위대로 모은다.
6. `stage0_source_manifest_harness.md`를 보고 `source_manifest` 초안을 만든다.
7. `profile_lock.json`을 만든다.
8. `material_bundle_summary.json`을 만든다.
9. 사람이 읽고 `manual_audit_note`를 쓴다.
10. `phase0_ready_snapshot.json`을 만든다.
11. `manual_audit_pass = true`가 아니면 Stage 0에서 멈춘다.
12. 그 다음에만 `docs/blockguide/SSOT_blockguide-integrated-order.md`로 넘어간다.

Production handoff 추가 규칙:

- preprocess 작업공간에 block 디렉터리나 final draft가 이미 있더라도 그것만으로는 sequential progress를 인정하지 않는다.
- Stage 0를 끝낸 뒤 production으로 넘길 때는 `docs/sequential_run_status.md`에 현재 상태를 먼저 적는다.
- seed만 있는 기지는 `run_class = seed_baseline_sync`, `last_sequential_block_pass = 0`, `next_block = Block 001`로 시작한다.

금지:

- 전처리 파일 없이 바로 `phase0_design`을 쓰기
- DB 결과를 검토 없이 그대로 정본으로 승격하기
- 프로파일을 3개 이상 혼합하기
- `do_not_fake` 없이 장르 현장 디테일을 상상으로 메우기

---

## 5. Stop / Go 기준

### 5.1 Stop

아래면 Stage 0에서 멈춘다.

- `primary_profile`이 안 잠겼다
- `source_manifest`에 `canonical_sources`가 없다
- `core_materials`가 추상 일반론뿐이다
- `npc_pool`과 `crisis_pool`이 작품 전장과 직접 연결되지 않는다
- `do_not_fake`가 비어 있다
- `manual_audit_note`가 비어 있다
- `phase0_ready_snapshot.manual_audit_pass != true`

### 5.2 Go

아래면 Planning으로 넘긴다.

- 전처리 산출물 4개가 UTF-8로 파싱된다
- `profile_lock`의 주/보조 프로파일이 명확하다
- `source_manifest`에 정본/참고본 구분이 있다
- `material_bundle_summary`가 작품 전장에 바로 옮길 수 있는 재료를 담고 있다
- `phase0_ready_snapshot.manual_audit_pass == true`

---

## 6. 좋은 예시 / 나쁜 예시

### 6.1 좋은 예시

```text
work_id = chaebol_ent_empire
primary_profile = entertainment_media_profile
secondary_profile = business_growth_profile
canonical_sources = 기획안, onboarding, 기존 TR
core_materials = 편성 슬롯, 레이블 계약, 팬덤 여론, 배급 라인, 내부 정산 관행
do_not_fake = 방송 편성 구조를 추상 권력전으로만 쓰지 말 것
manual_audit_note = 편성/배급/정산 3축은 바로 Phase 0에 옮길 수 있음
```

좋은 이유:

- 장르 프로파일이 명확하다
- 현장 디테일이 추상어가 아니라 직접 쓸 수 있는 재료다
- 무엇을 상상으로 메우면 안 되는지 적혀 있다

### 6.2 나쁜 예시

```text
primary_profile = investment_market_profile
secondary_profile = medical_professional_profile
secondary_profile_2 = urban_power_profile
core_materials = 업계 느낌, 성공 욕망, 사람들 관계
manual_audit_note = 없음
```

나쁜 이유:

- 프로파일이 과다 혼합이다
- 재료가 전부 추상 명사다
- 수동 감리 메모가 없다
- 이 상태에선 `Phase 0`로 가면 안 된다

---

## 7. 레거시 스크립트 해석

- `scripts/build_bi_from_phase0_and_tr.py`
  - 유지
  - 역할: `phase0 + verified TR -> BI`의 canonical deterministic builder

- `scripts/generate_tr_bibles.py`
  - 기본 경로에서 제외
  - 역할: 레거시 템플릿 참고 스크립트

- `scripts/process_and_audit_tr_bi_loop.py`
  - 기본 경로에서 제외
  - 역할: 옛 배치 루프 실험용

근거:

- 현재 BI 빌더는 `phase0 + verified TR` 계약을 실제로 소비한다.
- 레거시 스크립트는 새 Stage 0 전처리 산출물 계약을 소비하지 않는다.

---

## 8. Stage 0의 목적

Stage 0는 자료를 많이 모으는 단계가 아니다.

Stage 0의 목적은 아래 3개다.

1. 무엇이 정본인지 잠근다
2. 어떤 프로파일로 읽을지 잠근다
3. 이 상태로 `phase0_design`을 써도 되는지 수동 감리로 승인한다

Stage 0를 건너뛰면 이후의 Planning, Production, BI는 빨라질 수는 있어도 흔들린다.

---

## 9. 3-Pass Self Audit

### Pass 1. 계약 정합성

- Stage 0 산출물 4개와 blockguide 정본 경로를 분리했다.
- `manual_audit_pass`가 Planning 진입 게이트로 명시됐다.

### Pass 2. 실행 가능성

- 낮은 성능 모델도 따라갈 수 있게 stop/go와 좋은/나쁜 예시를 넣었다.
- 레거시 스크립트와 canonical path를 분리했다.

### Pass 3. 무결성

- UTF-8 only
- 파일 경로를 명시했다
- `전처리_ssot`가 상설 진실이라는 역할을 문서 상단에 박았다
