# i-ah-1900-1950-crisis_library-b01 3-Pass 감리

> 대상 파일: `test_material/json_outputs/i-ah-1900-1950-crisis_library-b01.json`
> 메타 파일: `test_material/json_outputs/i-ah-1900-1950-crisis_library-b01.meta.json`
> 감리 시점: 2026-03-10
> 터미널: 18 / wave: STD-C1 / campaign: AH-STD18-1900-1950-B01

---

## Pass 1. JSON 구조 / 스키마 무결성

### 점검 항목

- 최상위 5개 키 존재 및 배열 타입 여부
- 각 테이블 필수 필드 전량 존재 여부
- confidence(1~5) / severity(1~5) / synergy_score(1~5) 범위
- 코드펜스, 주석, trailing comma 혼입 여부

### 확인 결과

| 테이블 | 항목 수 | 필수 필드 | 범위 값 |
|--------|---------|-----------|---------|
| events | 12 | PASS | confidence 4~5 |
| npcs | 3 | PASS | — |
| crises | 10 | PASS | severity 3~5 |
| sector_chains | 3 | PASS | synergy_score 4~5 |
| market_data | 4 | PASS | — |

- 최상위 5개 키 모두 존재, 전부 배열 타입
- 필수 필드 누락 0건
- confidence/severity/synergy_score 전량 1~5 범위 내
- 코드펜스, 주석, trailing comma 없음

### 판정

**PASS**

---

## Pass 2. 내용 정합성 / 하네스 원칙 준수

### 점검 항목

- source 값 일관성 (전 항목 `AH-1900-1950-CRISIS_LIBRARY-B01`)
- ID prefix 일관성 및 중복 여부
- 날짜 형식 (`YYYY`, `YYYY-MM`, `YYYY-MM-DD` 중 하나)
- 금지어 (`???`, `TBD`, `미정`, `확인 필요`) 0건
- 빈 필수 문자열 필드 0건
- connected_events 참조 대상 존재 여부
- market_data value 숫자 타입
- 반사실 혼입 여부 (주인공 개입 결과, 가공 수치)
- 6대 위기 유형 커버리지

### 확인 결과

**자동 검사**

- source 불일치: 0건
- ID 중복: 0건
- 날짜 형식 위반: 0건
- 금지어: 0건
- 빈 필수 필드: 0건
- connected_events 깨진 참조: 0건 (참조 대상 전량 payload 내 존재)
- market_data value 비숫자: 0건

**수동 검사 — 반사실 혼입**

- events 12개 전량 역사적 사실 사건 기반. 주인공 개입 결과 미수록.
- `opportunity`, `strategy` 필드는 하네스 허용 범위(사업 기회 구조 기술)에 해당.
- crises 10개의 `resolution`은 실존 우회 방법 기술. 반사실 결과물 미수록.
- npcs 3개 모두 `복합:` 명시 전형 모델. 완전 허구 인물 없음.
- market_data 수치 4개 모두 `note`에 추정 범위·출처 성격 명시. 억지 정밀 수치 없음.

**6대 위기 유형 커버리지**

| 유형 | 커버 항목 |
|------|-----------|
| 검역 | C001, E003, E005 |
| 봉쇄 | C002, C009, E004, E011 |
| 환율 혼란 | C007, E007, E008 |
| 식민지 단속 | C003, C010, E002, E012 |
| 파업 | C004, E010 |
| 유동성 위기 | C005, C006, E006, E007 |

전 유형 커버.

### 판정

**PASS**

---

## Pass 3. UTF-8 / 문자 무결성 / meta 정합성

### 점검 항목

- BOM 없음
- UTF-8 디코딩 성공
- `\ufffd` (Unicode replacement character) 0건
- `???` 0건
- 제어문자 혼입 0건
- JSON 파싱 성공
- meta `row_counts` ↔ payload 실제 건수 일치
- meta `terminal_id` = 18
- meta `status` = READY_FOR_INGEST

### 확인 결과

| 항목 | payload | meta |
|------|---------|------|
| BOM | 없음 | 없음 |
| UTF-8 디코딩 | OK | OK |
| `\ufffd` | 0건 | 0건 |
| `???` | 0건 | 0건 |
| 제어문자 | 0건 | 0건 |
| JSON 파싱 | OK | OK |

| 테이블 | payload 실제 | meta 선언 | 일치 |
|--------|-------------|-----------|------|
| events | 12 | 12 | OK |
| npcs | 3 | 3 | OK |
| crises | 10 | 10 | OK |
| sector_chains | 3 | 3 | OK |
| market_data | 4 | 4 | OK |

- terminal_id: 18 ✓
- status: READY_FOR_INGEST ✓

### 판정

**PASS**

---

## 최종 판정

| Pass | 판정 |
|------|------|
| Pass 1: 구조/스키마 | **PASS** |
| Pass 2: 내용 정합성 | **PASS** |
| Pass 3: UTF-8/메타 | **PASS** |

**3-Pass 전량 PASS. DB 적재 가능.**

다음 행동: `test_material/ingest_i_materials.py`로 단일 작업자 적재.
