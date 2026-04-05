# Stage 0 전처리: TR/BI 생산 기반 1차 기획안

> UTF-8 only
> 작성일: 2026-03-12
> 성격: 구조 개혁용 1차 기획 문서
> 범위: `Phase 0 -> TR -> BI` 앞단에 놓이는 공통 전처리층 정의
> Historical Note: 이 문서는 capture-time 배경 문서이며, 아래 경로 표기는 현재 절대경로 요구가 아니라 당시 진입점 기록이다.

> 상태: **초기 설계 근거 / 개혁 배경 문서**
> 현재 진실: `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
> 하위 진실:
> - `전처리_ssot/docs/stage0_source_manifest_harness.md`
> - `전처리_ssot/docs/stage0_profile_lock_harness.md`
> - `전처리_ssot/docs/stage0_material_collection_harness.md`
> 이 문서는 더 이상 정식 SSOT가 아니라, 왜 이런 구조 개혁이 필요했는지 설명하는 배경 문서다.

## 1. 목적

이 문서의 목적은 `Stage 0 전처리`를 별도 층으로 정의해, 현대판타지 전 장르의 `Phase 0`, `TR`, `BI`가 더 안정적으로 만들어지도록 기반을 고정하는 것이다.

핵심은 다음 4가지다.

- `무엇을 모아야 하는지`를 장르별 감으로 처리하지 않고 계약으로 고정한다.
- `자동화는 허용`하되 `수동 감리`를 필수로 둔다.
- 최종 JSON은 계속 `treatments/`, `bible/`에 두되, 그 앞단 준비물과 근거 묶음을 표준화한다.
- 지금 흩어진 문서, DB, 스크립트, 개별 생성기를 하나의 전처리 관점에서 재배치한다.

---

## 2. 왜 구조 개혁이 필요한가

현재 구조는 `SSOT -> Phase 0 -> TR -> BI` 계약 자체는 정리되어 있지만, 그 앞단의 재료 수집과 기준 고정이 분산되어 있다.

문제는 크게 6개다.

- 작품마다 무엇을 먼저 모아야 하는지가 사람 감각에 많이 의존한다.
- `material bank`, 기존 기획안, 기존 TR/BI, 온보딩 문서, 수동 메모가 한 묶음으로 잠기지 않는다.
- 일부 스크립트는 옛 템플릿 기반이며, 현재 SSOT와 의미 계층이 다르다.
- `auto-run`이 작업 순서 자동 진행인지, 스크립트 자동 실행인지 혼동되기 쉽다.
- `DB 조회 자동화`는 있어도, 그 결과를 정식 근거로 확정하는 수동 감리 절차가 일관되지 않다.
- `Phase 0` 품질 문제가 종종 실제 설계 부족이 아니라 앞단 재료 부실에서 시작된다.

즉 지금 필요한 것은 새 생성기 하나가 아니라, `생성 전에 근거를 잠그는 전처리 공정`이다.

---

## 3. 북극성 원칙

Stage 0 전처리는 아래 원칙을 따른다.

- `quality-first`: 속도보다 근거, 밀도, 정합성을 우선한다.
- `automation-allowed`: DB 조회, 검색, 정리, 후보 압축은 자동화할 수 있다.
- `manual-audit-required`: 자동 수집 결과는 수동 감리 없이 정본이 될 수 없다.
- `auto-run != script-run`: auto-run은 작업 순서를 이어가라는 뜻이지, 파이썬 코드를 강제 실행하라는 뜻이 아니다.
- `one-unit progression`: 전처리 이후 생산도 한 번에 70블록 일괄 생성이 아니라, 가장 작은 단위로 차근차근 쌓는다.
- `evidence-first`: 모자란 정보는 창작으로 메우기 전에 먼저 재료 수집을 보강한다.
- `all-genre core, profile-aware execution`: 현대판타지 공통 코어를 쓰되, 장르 프로파일별로 필요한 재료는 다르게 모은다.

---

## 4. Stage 0 전처리가 맡는 역할

Stage 0 전처리는 아래까지만 책임진다.

- 작품의 `정체성 계약`을 잠근다.
- 장르 `profile lock`을 잠근다.
- 재료와 근거를 `source_manifest`로 잠근다.
- `Phase 0`에 들어갈 최소 재료가 충분한지 판정한다.
- `TR`, `BI`로 이어질 수 있는 handoff snapshot을 만든다.

Stage 0 전처리가 하지 않는 일도 분명히 둔다.

- 완성 TR을 대신 쓰지 않는다.
- BI를 직접 확정하지 않는다.
- 부족한 재료를 무리하게 상상으로 메꾸지 않는다.
- 장르 프로파일이 안 맞는데 억지로 `business_growth` 의미를 씌우지 않는다.

---

## 5. 무엇을 모을 것인가

Stage 0 전처리에서 모을 것은 6개 묶음으로 나눈다.

### 5.1 작품 정체성 묶음

- `work_id`
- 작품명
- 로그라인
- 한 줄 장르 정의
- 시간 앵커
- 주요 무대
- 주인공 이름
- 주인공 출발 상태
- 핵심 우위 또는 능력
- 핵심 결핍
- 70블록 성장축 한 줄 요약

### 5.2 프로파일 묶음

- `primary_profile`
- `secondary_profile` 또는 `null`
- 프로파일 선택 이유 3줄
- 이 작품에서 `resource`, `power`, `control`, `payoff`, `failure`가 무엇인지 정의
- 기존 호환 필드 해석표

예시:

- 투자물의 `resource` = 현금, 지분, 시장 정보, 회수 구조
- 엔터물의 `resource` = IP, 편성권, 팬덤, 제작 라인, 유통 채널
- 의학물의 `resource` = 수술 기회, 케이스 축적, 병원 내 신뢰, 연구 라인
- 회사원물의 `resource` = 예산, KPI, 결재선, 인사권, 팀 통제

### 5.3 근거 문서 묶음

- 현재 기획안
- 온보딩 문서
- 기존 `phase0_design`
- 기존 `TR draft`
- 기존 `BI`
- 사용자 메모
- 비교 대상으로 삼을 실패작 또는 골든 샘플

이 묶음은 `무엇이 정본이고 무엇이 참고용인지`를 함께 적어야 한다.

### 5.4 재료 묶음

공통 재료:

- 사건 후보
- NPC 후보
- 위기 후보
- 제도/규칙 후보
- 장소 후보
- 용어 후보
- 시간축 후보
- 금지해야 할 가짜 디테일 목록

프로파일별 추가 재료:

- 투자물: 시장 이벤트, 규제, 지배구조, 자산 종류, 회수 구조
- 엔터물: 편성, 캐스팅, 팬덤, 유통, 레이블 구조, 계약 분쟁
- 의학물: 병원 구조, 진료 프로세스, 전공 라인, 수련/평판 구조
- 회사원물: 조직도, KPI, 예산, 결재선, 평가/인사 구조
- 기술 창업물: 제품, 고객, 라이선스, 데이터, 배포, 기술 스택
- urban power 계열: 능력 체계, 권리 구조, 조직 질서, 공적 노출 리스크

### 5.5 서사 골격 묶음

- 5~8개 아크 초안
- 적대 축 3단계
- 주인공 자원 성장 곡선 초안
- 패배 포인트 후보
- 복선/회수 후보
- 직업/업계/현장 루틴 후보

### 5.6 수동 감리 묶음

- 이번 수집에서 바로 쓸 수 있는 것
- 아직 비어 있는 것
- 상상으로 채우면 위험한 것
- 장르 프로파일과 충돌하는 것
- 다음 단계로 넘겨도 되는지에 대한 한 줄 판정

---

## 6. Stage 0 전처리의 핵심 산출물

최종적으로 잠가야 하는 산출물은 5개다.

### 6.1 `source_manifest`

가장 중요한 전처리 산출물이다. 최소 필수 슬롯은 아래와 같다.

- `work_identity`
- `profile_lock`
- `canonical_sources`
- `reference_only_sources`
- `core_materials`
- `npc_pool`
- `crisis_pool`
- `terminology_pool`
- `hard_constraints`
- `do_not_fake`
- `manual_audit_note`

### 6.2 `profile_lock`

`primary_profile`과 `secondary_profile`만 적는 것이 아니라, 이 작품에서 호환 필드를 어떻게 읽을지까지 잠근다.

잠가야 할 필드:

- `resource_axis`
- `power_axis`
- `control_axis`
- `payoff_axis`
- `failure_axis`
- `hud_interpretation`
- `domain_lines_interpretation`
- `arena_state_interpretation`

### 6.3 `material_bundle_summary`

DB, 문서, 로컬 샘플에서 모은 재료의 요약본이다.

포함 항목:

- 사건 후보 상위 8~15개
- NPC 후보 상위 6~12개
- 위기 후보 상위 4~8개
- 용어 후보 10~30개
- 장소/기관 후보 5~12개
- 프로파일상 반드시 써야 하는 현장 디테일 5~10개

### 6.4 `phase0_ready_snapshot`

`이 상태로 Phase 0를 써도 되는가`를 판정하는 전처리 체크포인트다.

최소 포함:

- `identity_locked = true/false`
- `profile_locked = true/false`
- `material_sufficient = true/false`
- `manual_audit_pass = true/false`
- `remaining_risks`

### 6.5 최종 `phase0_design`

전처리의 최종 출력은 결국 `treatments/{work_id}_phase0_design.json`이다.

즉 전처리층은 별도 JSON 묶음을 잠근 뒤, 그 결과를 이용해 정식 `phase0_design`을 쓰는 구조다.

---

## 7. 최종 파일 경로 원칙

최종 산출물은 기존 경로를 유지한다.

- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

중간 문서와 전처리 보고서는 문서 경로에 둔다.

- `docs/{date}/codex_{work_id}_stage0_preprocess_report.md`
- `docs/{date}/codex_{work_id}_stage0_preprocess_audit.md`

전처리 중간 JSON을 파일로 남기고 싶다면 별도 작업 폴더를 두되, 정본 경로와 헷갈리지 않게 해야 한다.

권장 예시:

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

이 경로는 초안 단계에서 제안이었지만, 현재는 `전처리_ssot` 문서군에서 정식 계약으로 승격됐다. 현재 문서에서는 배경 설명으로만 남긴다.

---

## 8. Stage 0 전처리 공정

전처리 공정은 아래 7단계로 고정한다.

### 8.1 Intake Normalize

- 사용자 요청과 현재 파일 상태를 읽는다.
- `work_id`를 정한다.
- 기존 기획안/Phase 0/TR/BI 존재 여부를 판정한다.
- 무엇이 정본이고 무엇이 참고본인지 분리한다.

### 8.2 Profile Lock

- 작품의 `primary_profile`을 하나 고른다.
- 필요하면 `secondary_profile`을 하나만 추가한다.
- 호환 필드의 의미를 작품 단위로 재정의한다.
- 장르 프로파일이 흔들리면 여기서 멈춘다.

### 8.3 Source Collection

- 현재 기획안과 온보딩 문서를 읽는다.
- 기존 `phase0`, `TR`, `BI`가 있으면 참조한다.
- `material bank`와 로컬 샘플을 조회한다.
- 필요한 사건/NPC/위기/용어/현장 디테일을 추린다.

### 8.4 Source Manifest Draft

- 모은 재료를 `source_manifest` 초안으로 압축한다.
- `core_materials`, `npc_pool`, `crisis_pool`, `hard_constraints`, `do_not_fake`를 채운다.
- 이 단계에서는 많게 모으기보다, 실제로 쓸 것을 압축하는 것이 중요하다.

### 8.5 Manual Audit

- 자동 수집 결과를 사람이 읽고 정리한다.
- 가짜 디테일을 제거한다.
- 장르 프로파일과 충돌하는 재료를 제거한다.
- 비어 있는 핵심 재료가 있으면 추가 수집한다.

### 8.6 Phase 0 Synthesis

- 확정된 `source_manifest`를 기반으로 `phase0_design`을 쓴다.
- `arcs`, `npc_timeline`, `foreshadow_map`, `opponent_transition_plan` 최소 계약을 채운다.
- 필요하면 `capital_curve`나 프로파일별 확장 시트를 추가한다.

### 8.7 Handoff Snapshot

- 이 `phase0_design`으로 TR을 써도 되는지 최종 확인한다.
- `phase0_ready_snapshot`을 남긴다.
- 그 다음에만 Production 단계로 넘긴다.

---

## 9. 자동화와 수동 감리의 경계

자동화 허용 범위는 아래다.

- 문서 검색
- DB 조회
- 후보 목록 압축
- 중복 제거 초안
- 용어 정리 초안
- 산출물 형식화 초안

수동 감리 필수 범위는 아래다.

- `profile_lock` 확정
- `source_manifest` 확정
- `do_not_fake` 작성
- 프로파일과 재료 충돌 판정
- `phase0_ready_snapshot` 통과 판정
- 다음 단계 진행 승인

즉 자동화는 `모으는 일`을 도와줄 수 있지만, `정본으로 확정하는 일`은 반드시 수동 감리를 거쳐야 한다.

---

## 10. 무엇을 모자라다고 판정할 것인가

아래 중 하나라도 해당하면 전처리 미완료로 본다.

- 주인공의 욕망, 결핍, 우위가 모호하다.
- `primary_profile`이 안 잠겼다.
- 핵심 자원축이 무엇인지 정의되지 않았다.
- 적대 구조가 사람 이름만 있고 구조가 없다.
- 현장 디테일이 장르 수준에서 너무 빈약하다.
- `core_materials`가 추상 명사 위주다.
- `do_not_fake`가 비어 있다.
- 기획안과 기존 산출물 중 어느 쪽이 정본인지 불명확하다.
- 수동 감리 메모가 없다.

이 상태에서는 `Phase 0`를 쓰지 않는다.

---

## 11. 기존 문서와 스크립트의 재배치 제안

### 11.1 문서

- `SSOT_blockguide-integrated-order.md`
  - 상위 오더 문서
  - Stage 0 전처리를 정식 단계로 추가하는 대상

- `treatment-planning-harness.md`
  - `source_manifest -> phase0_design` 연결부를 가장 많이 받는 문서

- `treatment-production-harness-v2.md`
  - 전처리 결과를 실제 블록 생산 규칙으로 넘겨받는 문서

- `bi-production-harness-v1.md`
  - `TR -> BI` handoff 전, source manifest/profile lock의 흔적을 재확인하는 문서

- `modern_fantasy_material_harness.md`
  - 일반 현대판타지 재료 수집용 하위 하네스
  - Stage 0 전처리의 보조 문서로 재위치

### 11.2 스크립트

- `scripts/build_bi_from_phase0_and_tr.py`
  - 유지
  - 역할: `Phase 0 + verified TR -> BI`의 결정적 빌더

- `scripts/generate_tr_bibles.py`
  - 격하
  - 역할: 레거시 템플릿 기반 참고 스크립트
  - 기본 경로에서 제외 권장

- `scripts/process_and_audit_tr_bi_loop.py`
  - 격하
  - 역할: 옛 배치 루프 실험용
  - quality-first canonical path에서 제외 권장

- 개별 work 전용 생성기들
  - 유지 가능
  - 단, Stage 0 전처리 계약을 먹는 adapter 계층이 먼저 필요하다

---

## 12. 1차 구현 로드맵

### 12.1 문서 단계

- Stage 0 전처리를 SSOT에 단계로 추가한다.
- `treatment-planning-harness.md`에 `source_manifest` 계약을 명시한다.
- `modern_fantasy_material_harness.md`를 Stage 0 하위 문서로 재정렬한다.

### 12.2 데이터 단계

- `material bank`에서 프로파일별 추천 질의 템플릿을 만든다.
- `source_manifest` 표준 슬롯을 고정한다.
- `profile_lock` JSON 구조를 고정한다.

### 12.3 실행 단계

- 전처리 보고서 생성기 초안을 만든다.
- `source_manifest -> phase0_design` 보조 생성기를 만든다.
- 기존 개별 work 생성기를 새 입력 계약으로 천천히 감싼다.

### 12.4 검증 단계

- 엔터물 1개, 의학물 1개, 투자물 1개를 골라 Stage 0 전처리부터 다시 밟는다.
- `뭘 모을지 모르겠다`가 줄어드는지 본다.
- `Phase 0` 품질과 `TR` 반복률이 실제로 개선되는지 본다.

---

## 13. 권장 도입 순서

한 번에 전부 바꾸지 말고 아래 순서로 가는 것을 권장한다.

1. 문서 계약 확정
2. `source_manifest` 표준화
3. `profile_lock` 표준화
4. 수동 감리 메모 형식 표준화
5. `source_manifest -> phase0_design` 보조 도구 제작
6. 프로파일별 material query 템플릿 추가
7. 기존 생성기 adapter화

---

## 14. 1차 결론

구조 개혁의 핵심은 `TR/BI를 잘 만드는 생성기`보다 먼저 `무엇을 모아야 하는지와 무엇이 정본인지 잠그는 Stage 0 전처리층`을 세우는 것이다.

이번 1차 기획안의 결론은 다음과 같다.

- 최종 산출물 경로는 그대로 `treatments/`, `bible/`를 유지한다.
- 그 앞단에 `source_manifest`, `profile_lock`, `material_bundle_summary`, `phase0_ready_snapshot` 개념을 도입한다.
- 자동화는 자료 수집과 압축에만 쓰고, 정본 확정은 반드시 수동 감리를 거친다.
- 기존 스크립트는 새 canonical path 아래에서 역할을 재정의해야 한다.
- 위 방향은 이후 `전처리_ssot` 경로의 정식 SSOT와 `docs/blockguide` 상위 오더 패치로 이어졌다. 이 문서는 그 배경 근거로 본다.

---

## 15. 3-Pass Self Audit

### Pass 1. SSOT 정합성

- 현재 blockguide의 `quality-first`, `manual audit`, `auto-run은 스크립트 강제가 아님`, `Phase 0 -> TR -> BI` 규칙과 충돌하지 않도록 작성했다.
- `기업 성장물 전용`이 아니라 `현대판타지 all-genre general mode` 위에서 동작하도록 프로파일 방식으로 설계했다.

### Pass 2. 실행 가능성

- 현재 레포 구조를 전면 폐기하지 않고, `treatments/`, `bible/` 정본 경로 유지 전제로 설계했다.
- `build_bi_from_phase0_and_tr.py` 같은 기존 결정적 빌더는 살리고, 옛 템플릿 스크립트는 격하하는 방향이라 점진 도입이 가능하다.

### Pass 3. 문서 무결성

- 파일명은 ASCII 중심 `codex_` 접두사로 작성했다.
- 본문은 UTF-8 기준으로 저장한다.
- 구조 개혁 문서이며, 코드 변경 제안은 포함하되 실제 코드 수정은 수행하지 않았다.
