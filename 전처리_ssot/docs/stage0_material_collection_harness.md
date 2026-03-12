# Stage 0 Material Collection 하네스 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 역할: material 수집 우선순위, 좋은/나쁜 수집 방식, stop/go 기준 고정
> 정식 출력 경로: `treatments/preprocess/{work_id}/material_bundle_summary.json`

---

## 0. 이 문서의 목적

이 문서는 `무엇을 먼저 모아야 하는지`를 느슨한 감이 아니라 계약으로 고정한다.

핵심:

- source는 많이 모으는 것이 목적이 아니다
- 작품 전장에 직접 쓸 수 있는 재료만 남기는 것이 목적이다
- 자동화는 허용하지만, 사람이 읽고 버릴 것과 남길 것을 정해야 한다

---

## 1. 소스 우선순위

반드시 아래 순서로 본다.

1. 현재 작품의 기획안, onboarding, 사용자 메모, 기존 `phase0/TR/BI`
2. `test_material/material_bank.db`와 관련 query 도구
3. `test_material/json_outputs/`의 재료 팩
4. repo 내부 유사 장르 샘플
5. 부족할 때만 외부 1차/공식 자료

원칙:

- 작품 고유 설정보다 일반 업계 자료를 앞세우지 않는다
- DB 출력은 재료 은행이지 정본이 아니다
- 외부 자료를 써도 긴 원문 복붙은 금지

---

## 2. 뽑아야 하는 재료

공통:

- 사건 후보
- NPC 후보
- 위기 후보
- 장소/기관 후보
- 용어 후보
- 현장 루틴 후보
- 금지 디테일 후보

프로파일별 핵심:

- `investment_market_profile`
  - 시장 이벤트, 규제, 자산 종류, 지배구조, 회수 구조
- `entertainment_media_profile`
  - 편성, 배급, 팬덤, 레이블 구조, 계약 충돌
- `medical_professional_profile`
  - 병원 위계, 집도권, 레퍼럴, 프로토콜, 증례/연구 라인
- `office_power_profile`
  - KPI, 예산, 결재선, 인사권, 프로젝트 오너십
- `tech_startup_profile`
  - 제품, 고객, 라이선스, 데이터, 배포, 기술 스택
- `urban_power_profile`
  - 능력 체계, 길드 규칙, 권리 구조, 공적 노출 리스크

---

## 3. 좋은 수집 예시

```text
작품: 의학물
나쁜 수집: 병원은 정치가 있다 / 의사는 바쁘다 / 수술은 긴장된다
좋은 수집: 응급수술 승인 루프 / 주임교수-전임의-레지던트 위계 / 집도권 박탈 사유 / 증례 발표가 인사에 미치는 영향
```

좋은 이유:

- 추상 감정이 아니라 현장 규칙을 뽑았다
- `TR`에 바로 옮길 수 있다

---

## 4. 나쁜 수집 예시

```text
작품: 엔터물
source set: 유튜브 영상 몇 개, 막연한 업계 감
material bundle: 화제성, 논란, 팬덤, 계약
manual audit: 없음
```

나쁜 이유:

- 현장 구조가 없다
- 정본/참고 소스 구분이 없다
- 수동 감리가 없다

---

## 5. Stop / Go 기준

### Stop

- 재료가 전부 추상 명사
- 작품 전장과 직접 연결되는 사건/용어/관행이 없음
- profile과 재료가 충돌
- `source_manifest`에 바로 옮길 수 없는 재료만 있음

### Go

- 사건/NPC/위기/용어/현장 디테일이 작품 전장과 직접 연결됨
- `material_bundle_summary`로 압축 가능함
- 수동 감리 메모에서 “바로 쓸 수 있는 재료”가 분명함

---

## 6. 수동 감리 메모 예시

```text
1. 바로 쓸 수 있는 것
- 레이블 계약 구조, 편성 슬롯 선점 규칙, 팬덤 역풍 트리거

2. 아직 비어 있는 것
- 플랫폼 수익 분배 세부치, 해외 판권 회수 루프

3. 상상으로 때우면 안 되는 것
- 방송 편성 승인 구조, 병원 집도권 위계, 본부 KPI 승인 루프
```

---

## 7. 호환 문서

현재 `docs/blockguide/modern_fantasy_material_harness.md`는 경로 호환용 미러 문서다.

현행 진실은 이 문서다.

---

## 8. 3-Pass Self Audit

### Pass 1. 계약 정합성

- material 수집 우선순위를 현재 material bank 운용 메모와 충돌 없이 정리했다.

### Pass 2. 실행 가능성

- 좋은/나쁜 예시와 stop/go 기준을 넣어 낮은 성능 모델도 따라갈 수 있게 했다.

### Pass 3. 무결성

- UTF-8 only
- 정식 출력 경로 명시
