# 현대판타지 재료 하네스 v1

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-12
> 적용 장르: 현대판타지 전반 (`investment`, `entertainment`, `medical`, `office_power`, `tech_startup`, `urban_power` 등)
> 목적: **Phase 0/TR/BI 전에 작품의 업계·직업·전문분야 재료를 먼저 수집하고, 수동 감리된 `source_manifest`로 고정**
> 선행 문서: `SSOT_blockguide-integrated-order.md`, `treatment-planning-harness.md`, `treatment-production-harness-v2.md`, `bi-production-harness-v1.md`

> 상태: **경로 호환용 미러 문서**
> 현재 진실: `전처리_ssot\docs\stage0_material_collection_harness.md`
> 역할: `docs/blockguide` 경로를 참조하는 오래된 오더와의 호환 유지

---

## 0. 이 문서를 언제 읽는가

아래 중 하나라도 해당하면 범용 Blockguide 4문서를 읽은 직후 이 문서를 추가로 읽는다.

1. 작품이 현대판타지이며 업계, 직업, 전문분야, 플랫폼, 조직 구조의 디테일이 필요하다.
2. 사용자가 "자료 먼저", "근거 붙여", "DB에서 뽑아", "레퍼런스 정리", "재료 모아"를 요구한다.
3. `Phase 0`, `TR`, `BI`를 만들기 전에 산업/직군/현장 재료를 먼저 묶어야 한다.
4. 투자물, 엔터물, 의학물, 신입사원물, 테크 창업물, 헌터/길드물처럼 **실무 디테일이 품질을 좌우하는 장르**다.

핵심 원칙:

- 현대판타지 재료는 기억보다 **명시된 source set**을 먼저 본다.
- 자동 조회와 자동 정리는 허용되지만, **`source_manifest` 확정은 반드시 수동 감리**를 거친다.
- `auto-run`은 재료 수집 순서를 이어 간다는 뜻이지, 재료를 검토 없이 생산 단계로 넘기라는 뜻이 아니다.
- 재료가 약하면 상상으로 때우지 말고 먼저 재료 패킷을 보강한다.

추가 원칙:

- 이제 Stage 0 전처리는 전 장르 필수 선행 단계다.
- 정식 전처리 산출물 경로는 `treatments/preprocess/{work_id}/...` 4종이다.
- 이 문서의 상세 진실은 `전처리_ssot/stage0_material_collection_harness.md`가 우선한다.

---

## 0A. 초저지능 LLM용 빠른 시작

현대판타지 재료가 필요하면 아래 9단계만 그대로 따른다.

1. `SSOT_blockguide-integrated-order.md`를 UTF-8로 읽는다.
2. `treatment-planning-harness.md`, `treatment-production-harness-v2.md`, `bi-production-harness-v1.md`를 UTF-8로 읽는다.
3. 이 문서를 UTF-8로 읽는다.
4. 작품의 주 프로파일과 보조 프로파일을 1개씩만 잠근다.
5. 현재 작품 기획 문서, `phase0_design`, `TR draft`, `BI`가 있으면 먼저 다시 읽는다.
6. 로컬 재료 소스를 우선순위대로 모은다.
7. `source_manifest` 초안을 만든다.
8. `source_manifest`를 사람이 읽고 수동 감리한다.
9. 감리된 `source_manifest` 없이 `Phase 0`, `TR`, `BI`를 바로 쓰지 않는다.

금지:

- "대충 이 업계는 이럴 것" 같은 일반론으로 기획 골격을 채우기
- raw DB 전체나 긴 JSON 전체를 그대로 프롬프트에 밀어 넣기
- 자동 조회 결과를 검토 없이 정본으로 승격하기
- 재료 패킷 없이 의학/엔터/회사/기술 업계 디테일을 즉흥 생성하기

---

## 1. 역할

이 문서의 역할은 "현대판타지 작품의 전문 재료를 모아 생산 준비 패킷으로 고정하는 것"이다.

역할 분리:

- `treatment-planning-harness.md`: 서사 설계 원칙
- `treatment-production-harness-v2.md`: TR 블록 생산 규칙
- `bi-production-harness-v1.md`: BI 동기화/감리 규칙
- 현재 문서: **현대판타지 재료 수집, 소스 선택, `source_manifest` 고정의 blockguide 경로 미러**
- `alt_history_db_harness.md`: **역사 재료 전용 특화판**

즉:

- blockguide 구경로를 참조하는 오래된 오더라면 현재 문서를 연다.
- 현행 전처리 SSOT 기준의 진실은 `전처리_ssot/stage0_material_collection_harness.md`를 쓴다.
- 대체역사 재료는 `alt_history_db_harness.md`를 쓴다.

---

## 2. 소스 우선순위

`source_manifest`는 아래 순서로 고른다.

1. 현재 작품의 기획 문서, 온보딩 문서, `phase0_design`, 기존 `TR`/`BI`
2. `test_material/material_bank.db`와 `test_material/query_material_bank.py`
3. `test_material/json_outputs/` 안의 장르별/섹터별 재료 팩
4. repo 안의 인접 장르 샘플 (`treatments/`, `bible/`, `docs/`)
5. 로컬 자료가 부족할 때만 외부 1차 자료 또는 공식 자료

규칙:

- 이미 작품에 박힌 고유 설정을 무시하고 일반 산업 자료만 우선하지 않는다.
- DB/JSON 출력은 재료 은행이지, 연속성 엔진이 아니다.
- 외부 자료를 쓰더라도 핵심 사실만 추려 `source_manifest`에 넣고 원문을 길게 복붙하지 않는다.

---

## 3. `source_manifest` 최소 계약

현대판타지 재료 패킷은 최소한 아래를 담는다.

- `primary_profile`
- `secondary_profile` 또는 `null`
- `time_anchor`
- `primary_arena`
- `core_materials` 6~15개
- `npc_pool` 4~12개
- `crisis_pool` 3~8개
- `hard_constraints`
- `do_not_fake`
- `manual_audit_note`

좋은 `source_manifest` 기준:

- 너무 넓지 않고 작품 전장에 직접 쓰일 재료만 남아 있다.
- 프로파일과 재료가 맞물린다.
- `TR` 블록에 바로 옮길 수 있는 사건, 관행, 장소, 역할 이름이 있다.
- "하지 말아야 할 가짜 디테일"이 분명하다.

정식 전처리 산출물 경로:

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

---

## 4. 프로파일별 재료 체크리스트

| 프로파일 | 먼저 모을 재료 | 절대 비우면 안 되는 축 |
| ---- | ---- | ---- |
| `business_growth_profile` | 운영 병목, 공급망, 정산 구조, 반복매출, 조직 관문 | 병목 위치, 운영권, 돈 흐름 |
| `investment_market_profile` | 자산 종류, 시장 타이밍, 규제, 지분 구조, 금융 이벤트 | 진입 타이밍, 가격 근거, 구조화 포인트 |
| `entertainment_media_profile` | IP, 팬덤, 편성, 유통, 계약 구조, 여론 채널 | 아티스트/IP 라인, 배급/편성, 화제성 |
| `medical_professional_profile` | 병원 위계, 진료과, 집도권, 레퍼럴, 프로토콜 | 전문성 단계, 집도권, 병원 정치 |
| `office_power_profile` | 조직도, KPI, 예산, 결재선, 인사권, 프로젝트 구조 | 실적 축, 승인 구조, 권한 이동 |
| `tech_startup_profile` | 제품, 기술 스택, 라이선스, 데이터, 고객, 규격 | 제품 우위, 진입장벽, 배포/고객 축 |
| `urban_power_profile` | 능력 체계, 길드 구조, 던전/게이트 권리, 팀 편성 | 힘의 계급, 권리 배분, 사회적 위상 |

---

## 5. 자동화와 수동 감리

자동화 허용:

- DB 조회
- 로컬 JSON/문서 검색
- 후보 재료 묶음 정리
- 중복 제거 초안

수동 감리 필수:

- 최종 `source_manifest` 확정
- 가짜 디테일 제거
- 작품 기획과 재료의 충돌 확인
- 너무 강한/너무 약한 재료 컷팅

수동 감리 메모는 최소 3줄로 남긴다.

1. 이번 재료 패킷에서 바로 쓸 수 있는 것
2. 아직 비어 있는 것
3. 상상으로 때우면 안 되는 것

---

## 6. Failure Triage 기준

아래면 재료 단계에서 멈춘다.

- 프로파일과 재료가 맞지 않음
- 사건/직군/업계 디테일이 작품 전장과 직접 연결되지 않음
- 동일한 일반론만 있고 현장 고유성이 없음
- `source_manifest` 수동 감리 메모가 없음
- 자료가 약한데도 곧바로 `Phase 0`나 `TR`로 넘어가려 함

이 경우에는 생산으로 가지 말고 재료 패킷부터 다시 만든다.

---

## 7. 미러 문서 규칙

이 문서는 독자적 진실이 아니다.

- `전처리_ssot/stage0_material_collection_harness.md`와 충돌하면 새 SSOT가 우선
- 본 문서는 blockguide 경로 호환을 위해 유지
- 새 계약 추가나 변경은 먼저 `전처리_ssot` 쪽에 반영한 뒤 여기로 가져온다
