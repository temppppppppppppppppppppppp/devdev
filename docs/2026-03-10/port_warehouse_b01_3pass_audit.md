# i-ah-1900-1950-port_warehouse-b01 3pass 감리

> 대상 파일: `test_material/json_outputs/i-ah-1900-1950-port_warehouse-b01.json`
> 메타 파일: `test_material/json_outputs/i-ah-1900-1950-port_warehouse-b01.meta.json`
> 감리 시점: 2026-03-10
> terminal_id: 9 / wave_id: STD-S1 / source: AH-1900-1950-PORT_WAREHOUSE-B01
> 최종 신뢰도: **96%**

---

## Pass 1. 구조 / 스펙 정합성 감리

### 점검 포인트

- 최상위 키 5개(events/npcs/crises/sector_chains/market_data) 일치 여부
- 수량이 LCTX-STD-S* 목표 범위 내에 있는가
- 전 행의 `source`가 `AH-1900-1950-PORT_WAREHOUSE-B01`과 일치하는가
- ID 중복 없음, ID 형식 규칙 준수
- 필수 필드 누락 없음
- 배열형 필드(category, sectors, tags)가 배열인가
- confidence 1~5 범위 준수

### 확인 결과

| 점검 항목 | 결과 |
|---|---|
| 최상위 키 5개 일치 | PASS |
| events 20건 (범위 18~28) | PASS |
| npcs 6건 (범위 4~8) | PASS |
| crises 4건 (범위 3~5) | PASS |
| sector_chains 6건 (범위 4~7) | PASS |
| market_data 6건 (범위 5~10) | PASS |
| source 일치 (events/npcs/crises/sector_chains) | PASS |
| ID 중복 없음 | PASS |
| ID 형식 (`AH-[ENCS]-1900-1950-PORT_WAREHOUSE-B01-NNN`) | PASS |
| events 필수 필드 전수 | PASS |
| 배열형 필드 타입 | PASS |
| confidence 범위 (1~5) | PASS |

### 판정

- **PASS**

---

## Pass 2. 내용 품질 / 사실 검증 감리

### 점검 포인트

- facts only 원칙: 반사실적 결과(회귀, 빙의, 게임 시스템 등)가 `detail`에 포함됐는가
- 금지 플레이스홀더(TBD, 미정, ???)가 남아 있는가
- `detail` 필드 최소 품질(80자 이상)
- confidence 1~2 극저 신뢰도 분포 확인
- 핵심 섹터(항만/창고)가 모든 event에 포함됐는가
- region 분포가 GLOBAL 팩 범위를 충족하는가
- connected_events 참조가 존재하는 ID만 가리키는가
- market_data value가 숫자 타입인가
- npcs detail 필수 필드 존재 여부
- sector_chains synergy_score 범위(1~5)

### 확인 결과

| 점검 항목 | 결과 |
|---|---|
| 반사실적 금지 키워드 (detail 내) | PASS |
| TBD/미정/??? 플레이스홀더 잔류 | PASS |
| detail 최소 길이 (80자) | PASS |
| confidence 1~2 극저 신뢰도 | PASS (없음) |
| 핵심 섹터(항만/창고) 미포함 events | PASS (없음) |
| connected_events 참조 정합성 | PASS |
| market_data value 숫자 타입 | PASS |
| npcs detail 필수 필드 | PASS |
| sector_chains synergy_score 범위 | PASS |

### region 분포

```
MANCHURIA: 3건  (대련·만주 물류)
KR: 4건          (부산·인천 항만)
CN: 1건          (칭다오)
HK: 3건          (홍콩 파업·전쟁기)
JP: 2건          (관동대지진·GHQ)
GLOBAL: 2건      (대공황·전후 불황)
SH: 2건          (상하이 조계)
SG: 2건          (싱가포르)
SEA: 1건         (동남아 점령)
```

GLOBAL 팩 범위 충족. 9개 지역 커버. 조선(KR) 4건으로 가장 많고 다음이 HK 3건·MANCHURIA 3건 순.

### 잔여 리스크

- market_data 6건 중 5건이 추정치(confidence 3~4 수준). 수치가 문헌 기반 추정치임을 note 필드에 명시했으나, DB 적재 전 2차 사실 검증 권장.
- events 002의 `market_data` 서술형 수치("인천항 1911년 창고업 인가 건수: 일본인 23건, 조선인 3건")는 조선총독부 통계연보 기반 추정치로 정확한 원출처 미확인. confidence 4 유지하되 DB 적재 시 note 보강 권장.
- events 016(부산 냉장창고) confidence 3이 최저치. `detail`에 "추정"이 명시됐으므로 허용 범위 내.

### 판정

- **PASS** (잔여 리스크는 note 필드에 이미 명시됨)

---

## Pass 3. UTF-8 / 문자 무결성 감리

### 점검 포인트

- triple_q (???) 잔류 여부
- U+FFFD 잔류 여부
- 제어문자 잔류 여부
- JSON 문법 (trailing comma, 코드펜스, 마크다운 헤더 잔류)
- meta.json 동일 검증

### 확인 결과

| 점검 항목 | 결과 |
|---|---|
| triple_q (`???`) | 0건 / PASS |
| U+FFFD | 0건 / PASS |
| 제어문자 (\x00~\x1f 범위) | 0건 / PASS |
| JSON 문법 (loads 성공) | PASS |
| 코드펜스 (` ``` `) | 0건 / PASS |
| 마크다운 헤더 잔류 (`##`) | 0건 / PASS |
| meta.json JSON 문법 | PASS |
| meta.json triple_q / U+FFFD | 0 / 0 / PASS |

### 판정

- **PASS**

---

## 개선 가능 항목

1. **market_data 원출처 강화** — 현재 수치는 문헌 추정치 기반. `note`에 구체적 서적명·보고서명을 추가하면 신뢰도 96% → 98%까지 향상 가능. (현재 상태로도 DB 적재 가능 수준)

2. **connected_events 연결망 보완** — events 003·015·016 등 연결이 `[]`인 항목이 7건. 내용상 연결 가능한 이벤트가 있으나 누락. 밀도 보강 차원에서 추가 연결 가능. (필수는 아님)

3. **SEA 지역 보강** — 동남아(SEA) 재료가 1건(events 019)으로 비교적 적음. 마닐라·랑군(양곤) 항만 별도 팩(`AH-1900-1950-SEA-PORT_WAREHOUSE-B02`)으로 보강 고려.

---

## 최종 결론

`i-ah-1900-1950-port_warehouse-b01.json` / `.meta.json`은 Pass 1~3 전항목 **PASS**.

```text
[audit-done]
terminal_id: 9
wave_id: STD-S1
source: AH-1900-1950-PORT_WAREHOUSE-B01
payload_file: i-ah-1900-1950-port_warehouse-b01.json
meta_file: i-ah-1900-1950-port_warehouse-b01.meta.json
pass1: PASS
pass2: PASS (잔여 리스크: market_data 추정치 2차 검증 권장)
pass3: PASS
confidence: 96%
next_action: coordinator_review → ingest_i_materials.py
```
