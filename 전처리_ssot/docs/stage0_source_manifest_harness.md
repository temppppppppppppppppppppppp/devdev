# Stage 0 Source Manifest 하네스 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 역할: `source_manifest.json`의 필수 슬롯, 좋은/나쁜 예시, stop/go 기준 고정
> 정식 출력 경로: `treatments/preprocess/{work_id}/source_manifest.json`

---

## 0. 이 문서의 목적

`source_manifest`는 Stage 0 전처리의 핵심 산출물이다.

이 파일은 “재료를 모아 둔 메모”가 아니라 아래를 잠그는 계약이다.

- 작품 정체성
- 정본 소스와 참고 소스
- 바로 쓸 재료
- 절대 상상으로 때우면 안 되는 영역
- 수동 감리 결과

이 파일이 약하면 이후 `phase0_design`, `TR`, `BI`가 흔들린다.

---

## 1. 필수 슬롯

`source_manifest.json`은 최소한 아래 키를 담는다.

- `work_identity`
- `canonical_sources`
- `reference_only_sources`
- `core_materials`
- `npc_pool`
- `crisis_pool`
- `hard_constraints`
- `do_not_fake`
- `manual_audit_note`

권장 추가 슬롯:

- `terminology_pool`
- `time_anchor`
- `primary_arena`
- `profile_ref`

---

## 2. 슬롯별 의미

### 2.1 `work_identity`

최소 포함:

- `work_id`
- `title`
- `logline`
- `time_anchor`
- `primary_arena`
- `protagonist`

### 2.2 `canonical_sources`

현재 진실로 삼는 소스만 넣는다.

예:

- 현재 기획안
- onboarding prompt
- 사용자가 직접 확정한 메모
- 최신 `phase0_design` 또는 정정된 설계 문서

### 2.3 `reference_only_sources`

아이디어 참고만 하는 소스다.

예:

- 실패작
- 예전 TR/BI
- 다른 작품 샘플
- material bank 조회 결과
- `material_ssot/10_research/20_fewshot_bank/cards/dokshik_jaebeol3se_A.md`
- `material_ssot/10_research/20_fewshot_bank/cards/gim_daerineun_byeorakbuja_B.md`
- `material_ssot/10_research/20_fewshot_bank/reference_card_manifest.json`에 등록된 카드 라벨
- `Slim Reference Card v1 :: dokshik_jaebeol3se_A`

주의:

- raw epub/txt/html 원문 경로만 적어 두는 것은 부족하다
- 실물 원고를 썼다면 `reference_only_sources`에는 카드/요약 라벨이 들어가야 한다
- 저장되지 않은 채팅 응답은 `reference_only_sources`로 인정하지 않는다
- `Master Reference Card v1` 전체를 그대로 옮기지 말고 `Slim Reference Card v1` 라벨/경로를 우선 넣는다

### 2.4 `core_materials`

이 작품의 전장에 **바로 옮겨 넣을 수 있는 재료**만 넣는다.

실물 원고/NAS 레퍼런스에서 가져온 재료라면, 기본 입력은 `Master Reference Card v1`이 아니라 `Slim Reference Card v1`이다.

좋은 예:

- “편성 슬롯 협상 때 쓰이는 우선 배정 논리”
- “응급 수술 집도권 승인 경로”
- “본부 KPI 산정식이 바뀌는 회의 루프”
- “Slim Reference Card에서 추출한 opening representative spike / first reward retention / authority gain route”

나쁜 예:

- “업계는 냉정하다”
- “정치가 있다”
- “성공하려면 인맥이 필요하다”
- 저장된 master card 전체를 통째로 복붙한 덩어리

### 2.4A 추출 스케일 계약

`source_manifest`는 source를 보관하는 파일이 아니라, Stage 0가 설계 연료를 확정하는 계약 파일이다.

따라서 opening 관련 재료는 아래처럼 적는다.

- `opening representative spike`
  - opening macro arc 안에서 작품 간판 맛을 대표하는 폭발
- `first reward retention`
  - 첫 보상이 얼마나 오래 체류하는지
- `authority gain route`
  - 주인공이 어떤 권한/입지 상승 경로를 밟는지

핵심 규칙:

- source evidence가 `ep1`, `ep5` 같은 episode checkpoint에서 왔더라도, `core_materials`에는 block-scale 언어로 번역해서 적는다.
- `TR Block 1 spike`라는 phrasing은 downstream planning / production에서 exact placement가 잠길 때만 쓴다.
- Stage 0의 `source_manifest`는 `opening block 전체를 어떻게 쓸지`를 위한 연료를 적는 곳이지, scene-by-scene beat를 적는 곳이 아니다.

### 2.5 `npc_pool`

역할과 연결점이 있는 후보군이다.

각 항목은 최소한 아래 3개를 담는다.

- `name_or_role`
- `narrative_use`
- `why_this_work`

### 2.6 `crisis_pool`

위기는 장르 일반론이 아니라 작품 전장과 직결되어야 한다.

예:

- 배급 계약 파기
- 집도권 박탈
- 인사평가 조작
- 라이선스 분쟁

### 2.7 `hard_constraints`

반드시 지켜야 하는 사실/규칙이다.

예:

- 시간 앵커
- 주인공 직위
- 세계관 규칙
- 절대 바꾸지 말아야 하는 이름/관계/조직 구조

### 2.8 `do_not_fake`

가짜 디테일 금지 목록이다.

예:

- “병원 권력 구조를 추상 승부처럼만 쓰지 말 것”
- “방송 편성을 막연한 정치 싸움으로 때우지 말 것”
- “투자 구조를 단순 돈 놀음으로 뭉개지 말 것”

### 2.9 `manual_audit_note`

최소 3줄.

1. 바로 써도 되는 재료
2. 비어 있는 재료
3. 상상으로 때우면 안 되는 재료

---

## 3. 좋은 예시

```json
{
  "work_identity": {
    "work_id": "office_heir_zero",
    "title": "신입사원인데 본부를 먹는다",
    "logline": "예산과 KPI를 읽는 신입이 본부 권력전을 뒤집는다.",
    "time_anchor": "2019-03",
    "primary_arena": "대기업 전략본부",
    "protagonist": "강민우"
  },
  "canonical_sources": [
    "현재 기획안",
    "사용자 메모"
  ],
  "reference_only_sources": [
    "material bank bundle",
    "기존 실패 TR"
  ],
  "core_materials": [
    "분기 KPI 산정식 변경 시 본부장 승인 루프",
    "예산 전용 코드가 부서 권력에 미치는 영향",
    "실적 회의에서 재무/영업 수치가 충돌하는 지점"
  ],
  "npc_pool": [
    {
      "name_or_role": "재무팀 차장",
      "narrative_use": "숫자 검증 게이트",
      "why_this_work": "주인공의 KPI 재설계가 현실성을 얻는 접점"
    }
  ],
  "crisis_pool": [
    "예산 전용 코드 회수",
    "인사평가 반영 전 실적 부정 이슈"
  ],
  "hard_constraints": [
    "순수 일상물처럼 흐르지 말 것",
    "결재선과 KPI는 실체가 있어야 함"
  ],
  "do_not_fake": [
    "조직 권력전을 추상 감정 싸움으로만 쓰지 말 것"
  ],
  "manual_audit_note": [
    "KPI/예산/결재선 축은 바로 Phase 0에 투입 가능",
    "인사평가 제도 세부치는 추가 확인 필요",
    "부서장 권한을 막연한 카리스마로 때우면 안 됨"
  ]
}
```

좋은 이유:

- 작품 정체성이 잠겨 있다
- 정본/참고본이 구분된다
- 재료가 구체적이다
- `do_not_fake`와 수동 감리 메모가 있다

---

## 4. 나쁜 예시

```json
{
  "work_identity": {
    "work_id": "unknown_work"
  },
  "core_materials": [
    "업계 감",
    "정치",
    "인맥"
  ],
  "manual_audit_note": []
}
```

나쁜 이유:

- 작품 정체성이 잠기지 않았다
- 정본 소스 구분이 없다
- 재료가 전부 추상 명사다
- 수동 감리 메모가 비어 있다

---

## 5. Stop / Go 기준

### Stop

- `canonical_sources`가 없음
- `core_materials`가 추상어뿐임
- `do_not_fake` 비어 있음
- `manual_audit_note` 비어 있음
- `npc_pool`과 `crisis_pool`이 작품 전장과 직접 연결되지 않음

### Go

- 정본 소스와 참고 소스가 분리돼 있음
- 바로 `phase0_design`에 옮길 재료가 있음
- `do_not_fake`가 분명함
- 수동 감리 메모가 있음

---

## 6. 금지사항

- raw DB 전체를 그대로 넣기
- raw NAS 원고 경로만 던져 넣기
- 긴 원문을 통째로 복붙하기
- 프로파일과 맞지 않는 재료를 억지로 섞기
- 기획이 비어 있는데 일반론으로 채우기

---

## 7. 3-Pass Self Audit

### Pass 1. 계약 정합성

- `source_manifest` 최소 슬롯을 Stage 0 산출물 계약과 맞췄다.

### Pass 2. 실행 가능성

- 낮은 성능 모델도 좋은/나쁜 예시와 stop/go로 판정 가능하게 적었다.

### Pass 3. 무결성

- UTF-8 only
- 파일 경로 명시
