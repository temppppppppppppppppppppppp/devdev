# marine_insurance JSON pack 3-pass 감리

> 대상 파일:
> - `test_material/json_outputs/i-ah-1900-1950-marine_insurance-b01.json`
> - `test_material/json_outputs/i-ah-1900-1950-marine_insurance-b01.meta.json`
> 감리 시점: 2026-03-10
> 터미널: 11 / wave_id: STD-S3 / campaign: AH-STD18-1900-1950-B01
> 목적: 하네스 규칙 준수, 사실 재료 품질, UTF-8·meta 정합성 3단계 검증

---

## Pass 1. 규칙 구조 / ID·source·필드 감리

### 점검 포인트

- 최상위 5개 키(`events / npcs / crises / sector_chains / market_data`) 모두 존재하는가
- source가 팩 전체에서 단일값으로 일관되는가
- ID 중복이 없는가
- 각 테이블별 필수 필드가 빠짐없이 채워졌는가
- 배열형 필드(`category`, `sectors`, `tags`, `connected_events`)가 배열로 작성됐는가
- `connected_events` 참조가 실제 존재하는 event ID만 가리키는가
- `confidence`, `severity`, `synergy_score`가 정수인가
- `market_data.value`가 숫자인가

### 확인 결과

| 항목 | 결과 |
|------|------|
| 최상위 5개 키 | OK |
| source 일관성 (`AH-1900-1950-MARINE_INSURANCE-B01`) | OK |
| ID 중복 | 없음 |
| events 필수 필드 전량 | OK |
| npcs 필수 필드 전량 | OK |
| crises 필수 필드 전량 | OK |
| sector_chains 필수 필드 전량 | OK |
| market_data 필수 필드 전량 | OK |
| 배열형 필드 준수 | OK |
| connected_events 참조 유효성 (20개 이벤트 전수) | OK — 단절 참조 0건 |
| confidence 정수 여부 | OK |
| severity 정수 여부 | OK |
| synergy_score 범위 (3~5, all 1~5) | OK |
| market_data.value 숫자 여부 | OK — float 5건 / int 2건 |

### 목표 수량 대비

| 테이블 | 목표 | 실제 |
|--------|------|------|
| events | 18~28 | 20 |
| npcs | 4~8 | 6 |
| crises | 3~5 | 5 |
| sector_chains | 4~7 | 5 |
| market_data | 5~10 | 7 |

### 개선 반영 사항

- 없음

### 판정

- **PASS**

---

## Pass 2. 사실 재료 품질 / 섹터 정합성 감리

### 점검 포인트

- `detail` 필드에 반사실적 결과(주인공 개입 결과)가 혼입됐는가
- `opportunity`, `strategy`, `return_estimate` 필드가 현실성 있는 실무 서술인가
- `market_data` 수치에 근거 없는 가공 숫자가 있는가
- 기간 커버리지가 1900~1950 전체에 고르게 분포하는가
- NPC의 실존 여부 및 복합 모델 명시가 적절한가
- `sector_chains`의 연결이 그 시대에 실제로 붙어 다녔는가
- `connected_events` 연결의 논리적 정합성이 있는가

### 확인 결과

**반사실적 결과 침투 여부**

- `detail` 필드에 "주인공이" 문장 0건 확인.
- `narrative_use`, `tension` 필드에만 서사 활용 아이디어를 격리. 규칙 준수.

**기간 커버리지 (decade별 events 수)**

| 연대 | events 수 |
|------|---:|
| 1900년대 | 5 |
| 1910년대 | 5 |
| 1920년대 | 5 |
| 1930년대 | 3 |
| 1940년대 | 2 |

1930~1940년대는 중일전쟁·태평양전쟁 사건으로 밀도가 낮아 보이지만, 해당 연대 사건(E011 만주사변, E012 상하이봉쇄, E013 WWII 대서양, E014 태평양전쟁, E020 전후재편)이 모두 수록돼 시기 공백 없음.

**NPC 구성**

- 실존 인물 1명(Cuthbert Heath, 생몰연도·역할 명시).
- 복합 모델 5명 전원 `[복합 모델]` 명시 및 `real_model` 필드에 복합 기준 서술. 적절.

**market_data 수치 근거**

- 7개 항목 전원 `note` 필드에 "추정", "범위", "문헌 추정치" 등을 명기해 거짓 정밀도를 방지. 규칙 준수.
- confidence 3 항목(6건)은 모두 불확실성이 이미 필드 내 명시됨.

**sector_chains 정합성**

| 연쇄 | synergy | 실존 근거 |
|------|:---:|------|
| 해운 → 보험 | 5 | 선박운항·무역금융 보험 연동 — 역사적 사실 |
| 보험 → 재보험 | 5 | 극동 현지보험 60~80% 세션 구조 — 역사적 사실 |
| 무역/상사 → 보험 | 4 | CIF 조건·상사별 우선계약 — 역사적 사실 |
| 군수/방산 → 보험 | 3 | 전쟁보험 정부위탁 구조 — 역사적 사실 |
| 정보/통신 → 보험 | 3 | Lloyd's List 선박 동정 수집(1734년~) — 역사적 사실 |

억지 연결 없음. 모두 그 시대에 실제로 붙어 다닌 섹터.

**connected_events 논리 정합성 점검**

- E009(관동대지진) → E003(도쿄해상 조선 독점): 간접적이나 도쿄해상이 지진 후 포괄보험 패키지를 설계하며 시장 재편에 적극 참여했다는 맥락에서 수용 가능. 강한 연결은 아님. → **경미한 관찰사항, PASS 유지.**
- E017(상하이 사기 클레임) → E019(CIF 거래 확산): CIF 확산에 따른 상하이 거래 증가가 사기 클레임 증가와 간접 연관. E012(상하이봉쇄)와 연결했으면 더 직접적이나 논리 파탄은 아님. → **경미한 관찰사항, PASS 유지.**

나머지 18건의 connected_events 연결은 직접적 인과 또는 동시기 구조 연쇄로 적절.

**confidence 분포**

| confidence | 건수 |
|:---:|---:|
| 5 | 2 (MIA1906, 루시타니아) |
| 4 | 12 |
| 3 | 6 |

MIA 1906 제정(실정법)·루시타니아 침몰(고정 사실) → confidence 5 적절. confidence 3 항목은 점유율 추정·재보험 Treaty 구조 등 문헌 부재 항목에만 적용. 분포 합리적.

### 개선 반영 사항

- E009 / E017 connected_events 연결 강도 약함 — 수정 불필요(논리 파탄 아님), 차기 배치(B02) 재작업 시 개선 권장.

### 판정

- **PASS**
- 잔여 관찰사항: connected_events 2건 약한 연결 (비치명, 수정 불필요)

---

## Pass 3. UTF-8 / 문자 무결성 / meta 정합성 감리

### 점검 포인트

- payload와 meta 둘 다 UTF-8로 정상 읽히는가
- 물음표 3개 연속(`???`)이 없는가
- Unicode replacement character(U+FFFD)가 없는가
- `TBD`, `미정`, `확인 필요` 같은 placeholder가 없는가
- meta의 `source`가 payload의 source와 일치하는가
- meta의 `row_counts`가 payload 실제 행 수와 일치하는가
- meta의 `status`가 `READY_FOR_INGEST`인가

### 확인 결과

| 항목 | 결과 |
|------|------|
| payload UTF-8 파싱 | OK |
| meta UTF-8 파싱 | OK |
| 물음표 3개 연속 | 0건 |
| U+FFFD | 0건 |
| placeholder (`TBD` / `미정` / `확인 필요`) | 0건 |
| meta.source = payload source | OK |
| meta.row_counts.events = 20 | OK |
| meta.row_counts.npcs = 6 | OK |
| meta.row_counts.crises = 5 | OK |
| meta.row_counts.sector_chains = 5 | OK |
| meta.row_counts.market_data = 7 | OK |
| meta.row_counts.total = 43 | OK |
| meta.status | READY_FOR_INGEST |
| meta.terminal_id | 11 |
| meta.wave_id | STD-S3 |
| meta.campaign_id | AH-STD18-1900-1950-B01 |
| 파일명 패턴 (`i-ah-*.json`) | OK |
| meta 파일 동반 존재 (`*.meta.json`) | OK |

### 개선 반영 사항

- 없음

### 판정

- **PASS**

---

## 최종 결론

```
Pass 1 (규칙·구조): PASS
Pass 2 (사실 재료·품질): PASS
Pass 3 (UTF-8·meta): PASS

최종 판정: PASS
```

잔여 관찰사항 2건(E009·E017 connected_events 연결 강도 약함)은 비치명이며 수정 불필요. 차기 재작업(B02) 시 개선 권장.

**status: READY_FOR_INGEST**
**다음 액션**: `test_material/ingest_i_materials.py --pattern "i-ah-1900-1950-marine_insurance-b01.json"` 드라이런
