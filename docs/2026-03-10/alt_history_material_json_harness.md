# 식민지 시대 / 대체역사 재료 수집 하네스

> 목적: 현대판타지 계열의 식민지 시대 / 대체역사 작품에 필요한 역사 재료를 먼저 JSON으로 안정적으로 수집하고, 검증이 끝난 뒤 SQLite DB에 한 번에 적재하기 위한 작업 기준서.
>
> 적용 범위:
> - 1880~1945 전후의 조선, 대한제국, 일본 제국, 청말/민국, 동남아, 영국령 해협식민지, 유럽 열강, 미국
> - 해운, 항만, 무역, 보험, 금융, 광산, 철도, 군수, 정보, 밀수, 암시장, 식민지 행정, 외교, 전쟁 특수
> - 실존 역사 재료를 바탕으로 한 현대판타지 / 대체역사 기획, Phase 0, TR 밀도 보강
>
> 기본 원칙:
> - 지금은 DB에 바로 넣지 않는다.
> - 먼저 JSON 팩을 만든다.
> - JSON 검증이 끝난 뒤, 단일 작업자가 DB에 일괄 적재한다.
> - DB에는 "사실 재료"만 넣는다. 반사실적 전개, 대체역사 결과, 주인공의 개입 결과는 넣지 않는다.
> - UTF-8 only. 물음표 3개 연속 또는 Unicode replacement character(U+FFFD) 발견 시 즉시 중단한다.

---

## 1. 이 하네스가 필요한 이유

- 현재 재료 은행은 현대 경제물 중심으로 구축되어 있고, 식민지 시대 / 대체역사 전용 재료군은 비어 있거나 매우 약할 수 있다.
- 이 상태로 바로 TR 70블록까지 밀면 사건명, 항만명, 금융 구조, 군수 흐름, 식민지 권력 구조가 추상화되기 쉽다.
- 따라서 먼저 역사 재료를 구조화된 JSON으로 모아두고, 나중에 검증된 팩만 DB에 넣어 `material_bank_*` 뷰로 재사용하는 방식이 안전하다.

이 문서는 "지금 당장 작품 하나를 쓰기 위한 메모"가 아니라, 이후 LLM이 반복 작업을 수행해도 망가지지 않게 만드는 운영 하네스다.

---

## 2. 최상위 운영 원칙

### 2.1 JSON first, DB later

- 모든 재료는 먼저 JSON 파일로만 만든다.
- LLM은 DB insert, update, delete, schema 변경을 시도하지 않는다.
- DB 적재는 `test_material/ingest_i_materials.py`로만 수행한다.
- DB 후처리는 `test_material/material_bank_postprocess.py`로만 수행한다.

### 2.2 한 번에 1팩만 처리

- 한 세션에서 처리하는 기본 단위는 `JSON 팩 1개`다.
- 팩 하나를 만들고, 그 팩을 검증하고, 필요하면 수정하고, 그 다음 팩으로 넘어간다.
- 여러 지역, 여러 시기, 여러 섹터를 한 번에 섞지 않는다.

### 2.3 DB에는 사실만 넣는다

- 사건, 인물, 위기, 섹터 연쇄, 시장 수치 중 "실존 역사 재료"만 넣는다.
- 반사실적 결과물은 넣지 않는다.
- 예시:
  - 허용: "1905년 러일전쟁 이후 일본의 영향력 확대"
  - 금지: "주인공이 러일전쟁 정보를 이용해 조선을 되산다"

### 2.4 작은 팩으로 쪼갠다

- 이 하네스는 "크게 모아서 나중에 정리"가 아니라 "작게 쪼개서 검증 가능한 상태로 쌓기"를 우선한다.
- 팩이 커질수록 날짜 오류, 인물 혼입, 지역 혼선, JSON 파손 가능성이 급증한다.

### 2.5 UTF-8만 허용

- 모든 문서, JSON, 메모는 UTF-8로 저장한다.
- 물음표 3개 연속, Unicode replacement character(U+FFFD), 깨진 한글, 잘린 JSON이 보이면 그 팩은 폐기 또는 수정 후 재검증한다.

### 2.6 단계적 처리 최우선

- 저컨텍스트 작업자는 한 번에 여러 판단을 동시에 하지 않는다.
- `자기 팩 1개 해석 -> payload 작성 -> meta 작성 -> 검증 -> dry-run -> 상태 갱신 -> 중단` 순서를 지킨다.
- 자기 팩이 끝났다고 해서 다음 터미널 번호나 다음 팩으로 넘어가지 않는다.
- validation을 건너뛰고 "나중에 한 번에 보자"로 넘기지 않는다.
- 확신이 낮은 사실은 행 단위 `confidence`를 낮추고, 예외 질문 조건이 아니면 범위를 임의 확장하지 않는다.

---

## 3. 작업 단위 규칙

LLM이 한 번에 처리할 수 있는 안전한 범위는 아래를 넘지 않는 것을 기본으로 한다. 다만 `22.4 표준 터미널 맵`의 `AH-STD18-1900-1950-B01`은 coordinator가 owner와 범위를 미리 고정한 압축 배치이므로, 이 절의 상한을 예외적으로 넘을 수 있다. 이 예외는 "더 넓게 해도 된다"는 뜻이 아니라, 표준 맵의 자기 row 범위만 허용된다는 뜻이다.

### 3.1 권장 팩 범위(개별 팩 / 비압축 배치 기준)

- 기간: 최대 5년
- 핵심 지역: 최대 2개
- 핵심 섹터: 최대 3개
- 핵심 주제: 1개
- 총 행 수: 120행 이하 권장

### 3.2 권장 팩 예시

- `1902~1905 싱가포르 항만 / 해운 / 보험`
- `1910~1914 대한제국 잔존 인맥 / 상하이 / 밀무역`
- `1931~1933 만주사변 이후 군수 / 철도 / 광산`
- `1918~1922 영국령 해협식민지 무역 / 고무 / 주석 / 환율`

### 3.3 즉시 분할해야 하는 경우

아래 중 하나라도 해당되면 작업을 멈추고 팩을 둘 이상으로 쪼갠다.

- 기간이 6년 이상이다.
- 지역이 3개 이상이다.
- 섹터가 4개 이상이다.
- 전쟁, 외교, 금융, 밀수, 철도, 광산을 한 팩에 모두 넣으려 한다.
- 예상 JSON 행 수가 120행을 넘는다.
- 팩 설명이 한 줄로 명확하게 요약되지 않는다.
- "일단 다 넣고 나중에 고르자"라는 발상이 들어온다.

병렬 실행용 전체 판은 `18. 병렬 Wave 설계`, 태그 체계는 `19. 태그 taxonomy`, 팩 메타는 `20. 팩 메타 스펙`을 기준으로 한다.

### 3.4 표준 압축 배치 예외 해석

- `AH-STD18-1900-1950-B01`에서 작업자는 `3.1`의 기간/지역/섹터 상한을 다시 계산하지 않는다.
- 대신 `22.4 표준 터미널 맵`의 자기 row를 절대 범위로 사용한다.
- `CTX` 팩은 시기 베이스라인 통합 팩이라 기간이 길 수 있다.
- `LCTX` 팩은 섹터 라이브러리 팩이라 1900~1950 전체를 덮을 수 있다.
- 그렇더라도 호출 1회당 basename 1개 원칙은 그대로 유지한다.

---

## 4. 저장 위치와 파일명 규칙

### 4.1 JSON 팩 저장 위치

- 기본 저장 위치: `test_material/json_outputs/`
- 적재 대상 파일명 패턴: `i-ah-*.json`
- 권장 메타 파일 패턴: `i-ah-*.meta.json`

### 4.2 권장 파일명 형식

```text
i-ah-<period>-<region>-<topic>-bNN.json
```

예시:

```text
i-ah-1902-1905-sg-port_insurance-b01.json
i-ah-1902-1905-sg-port_insurance-b01.meta.json
i-ah-1910-1914-kr_sh-smuggling_finance-b02.json
i-ah-1931-1933-manchuria-rail_munitions-b01.json
```

규칙:

- `i-` 접두사는 적재 대상 파일이라는 뜻이다.
- `ah`는 alt-history / historical material 계열 팩임을 뜻한다.
- 기간, 지역, 주제를 파일명에 넣어야 나중에 패턴 적재와 추적이 가능하다.
- 같은 범위를 재작성하면 `b02`, `b03`처럼 배치를 올린다.
- `.meta.json`은 팩의 선언 메타다. 후속 배치에서 `material_bank_source_declared_meta`에 넣을 수 있게 별도 유지한다.

### 4.3 문서 저장 위치

- 하네스 문서, 상태 문서, 감리 메모는 `docs/YYYY-MM-DD/`에 둔다.
- JSON 적재 메모와 감리 결과는 문서로 남기되, DB 적재 대상 데이터는 반드시 `test_material/json_outputs/`에 둔다.

---

## 5. 소스 코드와 테이블 기준

이 하네스는 아래 실제 구현을 기준으로 한다.

- 적재 스크립트: `test_material/ingest_i_materials.py`
- 후처리 스크립트: `test_material/material_bank_postprocess.py`
- 운영 메모: `docs/2026-03-09/material-bank-ops.md`

후처리 이후 운영 계층:

- `material_bank_source_meta`
  - source 단위 자동 메타 카탈로그
  - `domain / source_group / scope_type / fit / use_modes / meta_tags / row_counts`를 담는다
- `material_bank_source_declared_meta`
  - 사람이 작성한 선언 메타 저장소
  - 후처리 시 derived meta와 합쳐져 최종 `material_bank_source_meta`가 된다

현재 적재 가능한 테이블은 5개다.

- `events`
- `npcs`
- `crises`
- `sector_chains`
- `market_data`

JSON 팩은 이 5개 키만 최상위에 가져야 한다.

---

## 6. 최상위 JSON 포맷

적재 대상 JSON 파일은 아래 구조를 따른다.

```json
{
  "events": [],
  "npcs": [],
  "crises": [],
  "sector_chains": [],
  "market_data": []
}
```

규칙:

- 최상위는 반드시 JSON 객체 1개여야 한다.
- 각 키의 값은 반드시 배열이어야 한다.
- 없는 항목도 키를 생략하지 말고 빈 배열 `[]`로 둔다.
- 적재 대상 JSON에는 설명문, 주석, 마크다운, 코드펜스, trailing comma를 넣지 않는다.

---

## 7. 공통 작성 규칙

### 7.1 언어

- 모든 자유서술 필드는 한국어로 작성한다.
- 고유명사, 기관명, 항만명, 회사명은 원문 표기를 병기해도 된다.

### 7.2 날짜

- 가능한 한 `YYYY-MM-DD`를 쓴다.
- 일 단위가 불명확하면 `YYYY-MM`를 쓴다.
- 월도 불명확하면 `YYYY`를 쓴다.
- 거짓 정밀도를 만들지 않는다.

### 7.3 배열형 필드

다음 필드는 JSON 배열로 작성하는 것을 기본으로 한다.

- `category`
- `sectors`
- `connected_events`
- `tags`

적재 스크립트가 내부적으로 문자열로 직렬화하므로, 작성 단계에서는 배열로 유지하는 편이 안전하다.

### 7.4 자신 없는 정보 처리

- 확정적 사실이 아니면 단정하지 않는다.
- 불확실한 경우 `confidence`를 낮춘다.
- 날짜나 수치가 불명확하면 `detail` 또는 `note`에 "대략", "추정", "연도 기준", "전후"를 명시한다.

### 7.5 금지사항

- 출처 없는 가공 숫자 삽입
- 존재하지 않는 회사, 기관, 인물, 항로를 사실처럼 적기
- 주인공 개입 결과를 역사 사실처럼 적기
- "어쩌면", "아마도"만 가득한 추상 문장
- 비어 있는 placeholder
- 물음표 3개 연속, `TBD`, `미정`, `확인 필요`를 그대로 남기기

---

## 8. source 와 id 규칙

### 8.1 source 규칙

`source`는 "이 행이 어느 팩에서 왔는지"를 식별하는 값이다. 한 JSON 팩 안에서는 모든 행의 `source`를 동일하게 맞춘다.

권장 형식:

```text
AH-<period>-<region>-<topic>-BNN
```

예시:

```text
AH-1902-1905-SG-PORT_INSURANCE-B01
AH-1910-1914-KR_SH-SMUGGLING_FINANCE-B02
AH-1931-1933-MANCHURIA-RAIL_MUNITIONS-B01
```

### 8.2 id 규칙

각 행의 `id`는 테이블별 접두사와 일련번호를 포함한다.

권장 형식:

```text
AH-E-<pack>-001
AH-N-<pack>-001
AH-C-<pack>-001
AH-S-<pack>-001
AH-M-<pack>-001
```

예시:

```text
AH-E-1902-1905-SG-PORT_INSURANCE-B01-001
AH-N-1902-1905-SG-PORT_INSURANCE-B01-003
AH-C-1910-1914-KR_SH-SMUGGLING_FINANCE-B02-002
AH-S-1931-1933-MANCHURIA-RAIL_MUNITIONS-B01-004
```

규칙:

- 같은 `id`를 재사용하지 않는다.
- 동일 팩 안에서는 번호를 001부터 연속으로 준다.
- 나중에 수정 재적재를 고려하면 사람도 읽을 수 있는 ID가 좋다.
- `source`는 팩 메타 파일의 `source`와 완전히 같아야 한다.
- 나중에 `material_bank_source_declared_meta`에 넣을 때 `source`가 기본 키가 된다.

---

## 9. 권장 분류 체계

### 9.1 category 권장값

`events.category`에는 아래 중 필요한 것만 쓴다.

- `ECON`
- `FIN`
- `TRADE`
- `PORT`
- `LOGI`
- `WAR`
- `POL`
- `DIPLO`
- `COLONIAL`
- `TECH`
- `SOCIAL`
- `CRIME`
- `RESOURCE`

### 9.2 sector 권장값

`events.sectors`, `npcs.sector`, `sector_chains.from_sector`, `sector_chains.to_sector`에는 아래 범주를 우선 사용한다.

- `해운`
- `항만`
- `무역/상사`
- `보험`
- `은행/금융`
- `광산/자원`
- `철도/인프라`
- `군수/방산`
- `정보/통신`
- `밀수/암시장`
- `농장/원자재`
- `식민지 행정`
- `언론/선전`

### 9.3 region 권장값

`events.region`에는 아래 같은 축약 또는 병기형을 사용한다.

- `KR`
- `JP`
- `QING`
- `CN`
- `SG`
- `SEA`
- `HK`
- `SH`
- `UK`
- `FR`
- `DE`
- `US`
- `RUS`
- `GLOBAL`

필요하면 `SG / SEA`, `KR / JP`, `SH / CN`처럼 병기해도 된다.

---

## 10. 테이블별 JSON 스키마

아래 필드명은 실제 적재 스크립트 기준이다. 철자를 바꾸지 않는다.

### 10.1 events

식민지 시대 / 대체역사 재료의 핵심이다. 사건, 제도 변화, 외교 합의, 조약, 전쟁 특수, 항만 개장, 회사 합병, 식민지 수탈 구조, 해상 봉쇄, 운임 폭등 같은 것을 넣는다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | 필수 | 이벤트 고유 ID |
| `source` | string | 필수 | 팩 식별자 |
| `date_start` | string | 필수 | 시작 시점 |
| `date_end` | string | 필수 | 종료 시점. 단일 사건이면 시작과 동일하게 둬도 됨 |
| `event_name` | string | 필수 | 한 줄 제목 |
| `detail` | string | 필수 | 사건 설명, 구조, 맥락, 누가 왜 이익을 봤는지 |
| `category` | array[string] | 필수 | 권장 분류 코드 배열 |
| `sectors` | array[string] | 필수 | 관련 섹터 배열 |
| `region` | string | 필수 | 지역 축약 |
| `market_data` | string | 권장 | 운임, 관세, 환율, 생산량, 수출액 등 |
| `opportunity` | string | 권장 | 이 사건에서 사업적 기회가 어디에 생기는지 |
| `strategy` | string | 권장 | 어떤 방식으로 돈과 권력을 먹을 수 있는지 |
| `return_estimate` | string | 권장 | 기대 이익. 수치가 아니어도 됨 |
| `capital_needed` | string | 권장 | 필요 자본 수준 |
| `risk` | string | 권장 | 규제, 전쟁, 환율, 민족 갈등, 운송 차질 등 |
| `connected_events` | array[string] | 권장 | 연결되는 다른 event ID |
| `narrative_use` | string | 권장 | 소설 장면 활용 포인트 |
| `tension` | string | 권장 | 이 재료가 만드는 긴장 |
| `tags` | array[string] | 권장 | 자유 태그 |
| `confidence` | int | 필수 | 1~5 |

`events` 작성 기준:

- 단순 연표가 아니라 "누가 어떤 구조에서 돈과 권력을 먹는가"가 보여야 한다.
- 식민지 시대 재료는 사건과 제도의 연결이 중요하다.
- 전쟁 사건이면 군수, 보험, 해운, 철도, 정보 흐름까지 같이 적는다.
- 항만 사건이면 통관, 보세창고, 선박, 보험, 브로커, 현지 행정까지 같이 적는다.
- 수치가 있으면 좋지만, 가짜 수치는 금지다.

### 10.2 npcs

실존 인물, 실존 기관의 대표자, 특정 집단을 대표하는 전형 인물을 넣는다. 완전한 허구 인물은 넣지 않는다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | 필수 | NPC 고유 ID |
| `source` | string | 필수 | 팩 식별자 |
| `name` | string | 필수 | 인물명 |
| `role` | string | 필수 | 역할. 상인, 총독부 관료, 은행가, 해운업자, 정보 브로커 등 |
| `sector` | string | 필수 | 주 활동 섹터 |
| `real_model` | string | 권장 | 실존 인물명, 복합 모델 표기 가능 |
| `personality` | string | 권장 | 냉정, 거래형, 기회주의, 군인형, 브로커형 등 |
| `relation_to_protag` | string | 권장 | 향후 서사에서의 기능적 관계 |
| `first_appearance` | string | 권장 | 등장 가능한 시점 또는 사건 |
| `arc` | string | 권장 | 장기 활용 방식 |
| `detail` | string | 필수 | 이 인물이 쥔 자원, 권력, 약점, 연결망 |
| `tags` | array[string] | 권장 | 자유 태그 |

`npcs` 작성 기준:

- "좋은 사람/나쁜 사람"보다 "무슨 병목을 쥐고 있는가"가 중요하다.
- 복합 모델을 쓸 때는 `real_model`에 `복합: A + B`처럼 명시한다.
- 식민지 경찰, 항만 서기, 보험 심사역, 군납 브로커처럼 중간 권력자도 가치가 높다.
- 실존 인물의 생몰연도, 직책 시기를 심하게 어기지 않는다.

### 10.3 crises

장편에서 반복적으로 써먹을 수 있는 위기 패턴, 제도 충격, 시장 붕괴, 검거, 봉쇄, 징발, 쿠데타 여파를 구조화한다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | 필수 | 위기 고유 ID |
| `source` | string | 필수 | 팩 식별자 |
| `crisis_type` | string | 필수 | 위기 유형 |
| `period` | string | 필수 | 발생 시기 |
| `trigger_event` | string | 권장 | 촉발 사건 ID 또는 사건명 |
| `severity` | int | 필수 | 1~5 |
| `detail` | string | 필수 | 위기의 구조와 확산 방식 |
| `resolution` | string | 권장 | 실존 사례 기준 해결 방식 |
| `real_case` | string | 권장 | 참고할 실제 사례 |
| `narrative_function` | string | 권장 | 어떤 장면용 위기인지 |
| `placement_after` | string | 권장 | 어느 사건 뒤에 배치하면 좋은지 |
| `tags` | array[string] | 권장 | 자유 태그 |

`crises` 작성 기준:

- 단순히 "전쟁이라 위험함" 수준으로 쓰지 않는다.
- 검문 강화, 선적 지연, 보험금 지급 거절, 환전 제한, 밀수선 적발, 어음 부도, 항만 파업처럼 구체화한다.
- 해결책도 추상적 결단이 아니라 실무적 우회 경로가 보여야 한다.

### 10.4 sector_chains

주인공이 양지와 음지를 동시에 먹는 구조를 설계할 때 핵심이 되는 섹터 연쇄다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | string | 필수 | 연쇄 고유 ID |
| `source` | string | 필수 | 팩 식별자 |
| `from_sector` | string | 필수 | 시작 섹터 |
| `to_sector` | string | 필수 | 도착 섹터 |
| `synergy_score` | int | 필수 | 1~5 |
| `reason` | string | 필수 | 왜 연결되는지 |
| `capital_needed` | string | 권장 | 필요한 자본 규모 |
| `real_example` | string | 권장 | 실존 사례 |

`sector_chains` 작성 기준:

- 식민지 시대에는 `항만 -> 보세창고 -> 보험 -> 은행`, `철도 -> 광산 -> 군수`, `무역 -> 정보 -> 밀수` 같은 구조가 중요하다.
- 억지 연결은 금지한다.
- "이론상 가능"보다 "그 시대에 실제로 자주 붙어 다녔는가"를 본다.

### 10.5 market_data

실제 수치 자료. 가능한 경우만 넣는다. 억지 수치 생성은 금지한다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `source` | string | 필수 | 팩 식별자 |
| `date` | string | 필수 | 시점 |
| `indicator` | string | 필수 | 지표명 |
| `value` | number | 필수 | 수치 |
| `unit` | string | 필수 | 단위 |
| `note` | string | 권장 | 범위, 출처 성격, 해석 메모 |

`market_data` 작성 기준:

- 환율, 은 가격, 고무 가격, 주석 가격, 운임지수, 수출액, 관세율, 철도 수송량, 광산 생산량 같은 것만 넣는다.
- 서술형 값은 넣지 않는다.
- 숫자가 불확실하면 `market_data`에 넣지 말고 `events.market_data`의 서술 필드로 돌린다.
- `market_data.source`에는 통계 출처명이 아니라 팩의 `source`를 넣는다.
- 실제 통계의 출처 성격, 서적명, 보고서명, 보정 메모는 `note`에 적는다.

주의:

- `market_data`는 다른 테이블과 달리 자동 증가 키를 사용하므로 append 성격이 강하다.
- 같은 값을 반복 삽입하면 누적되므로, 적용 전에 중복 여부를 더 엄격히 본다.

---

## 11. 필드별 작성 디테일

### 11.1 detail은 건조한 백과사전 문장이 아니어야 한다

좋은 `detail`은 아래를 포함한다.

- 무엇이 일어났는가
- 누가 병목을 잡았는가
- 돈이 어디서 어디로 이동했는가
- 권력이 누구에게 집중되었는가
- 주인공이 이용한다면 어느 틈을 파고들 수 있는가

### 11.2 opportunity와 strategy는 현실성을 가져야 한다

좋은 예:

- `opportunity`: 일본 대형 상사와 총독부 조달 사이의 중간 운송을 잡으면 물류 마진과 정보가 동시에 쌓인다.
- `strategy`: 선박 소유 대신 창고권과 보험 심사권부터 확보해 현금흐름과 통관 정보를 먼저 장악한다.

나쁜 예:

- `opportunity`: 아무튼 큰돈을 벌 수 있다.
- `strategy`: 주인공 버프로 다 해결한다.

### 11.3 narrative_use는 서사 전환점이어야 한다

좋은 예:

- 총독부가 밀수 단속을 강화하자, 주인공이 합법 운송회사로 위장한 뒤 야간 하역 라인을 따로 굴리는 장면
- 전쟁 특수로 보험료가 폭등하자, 전면에선 보험사 이사로 웃고 후면에선 무기 운송을 독점하는 장면

---

## 12. 단계별 작업 프로토콜

아래 순서를 반드시 지킨다. 한 번에 점프하지 않는다.

### Step 0. 팩 범위 고정

먼저 아래 5가지를 1줄씩 정한다.

1. 기간
2. 지역
3. 핵심 섹터
4. 핵심 주제
5. 이 팩이 보강하려는 작품상 목표

예시:

```text
기간: 1902~1905
지역: 싱가포르, 영국령 해협식민지
핵심 섹터: 항만, 해운, 보험
핵심 주제: 식민지 허브 항만에서 양지 자본과 음지 운송이 만나는 구조
작품상 목표: 주인공의 초반 거점 형성과 자본 증식 루트 설계
```

이 5줄이 흔들리면 JSON 작성에 들어가지 않는다.

### Step 1. 팩 설계표 작성

JSON을 쓰기 전에 아래 분량 계획을 먼저 고정한다.

- `events`: 20~40개
- `npcs`: 6~12개
- `crises`: 4~8개
- `sector_chains`: 4~8개
- `market_data`: 10~30개

시장 수치가 부족한 시기라면 `market_data`를 억지로 채우지 않는다.

### Step 2. facts only 초안 작성

이 단계에서는 facts only 원칙을 지킨다.

- 실제 사건만 쓴다.
- 실제 인물 또는 복합 실존 모델만 쓴다.
- 실제 위기 구조만 쓴다.
- 실제 산업 연결만 쓴다.
- 실제 수치만 쓴다.

아직 "작품에서 주인공이 뭘 할지"까지 쓰지 않아도 된다. 다만 `narrative_use`, `opportunity`, `strategy`에는 재료로서의 잠재력을 적어둘 수 있다.

### Step 3. JSON 자체 검수

적재 전에 아래를 직접 본다.

- 최상위 객체인가
- 5개 키가 모두 있는가
- 각 키의 값이 배열인가
- 필수 필드가 빠지지 않았는가
- `confidence`와 `severity`가 정수인가
- `market_data.value`가 숫자인가
- ID가 중복되지 않는가
- 물음표 3개 연속, Unicode replacement character(U+FFFD), 빈 문자열 남발이 없는가
- 반사실적 결과가 섞이지 않았는가

### Step 4. UTF-8 및 JSON 문법 검증

아래 검증을 통과해야 다음 단계로 간다.

```powershell
python -X utf8 -m json.tool test_material/json_outputs/i-ah-1902-1905-sg-port_insurance-b01.json > $null
python -X utf8 -c "from pathlib import Path; import sys; t=Path(r'test_material/json_outputs/i-ah-1902-1905-sg-port_insurance-b01.json').read_text(encoding='utf-8'); bad=('?'*3 in t) or ('\\\\ufffd' in t.encode('unicode_escape').decode()); sys.exit(1 if bad else 0)"
```

판정:

- `json.tool` 에러가 나면 수정 후 재검증
- Python 검증이 비정상 종료하면 수정 후 재검증

### Step 5. 드라이런 적재

실제 DB에 쓰기 전, 행 수와 테이블 분포를 본다.

```powershell
python -X utf8 test_material/ingest_i_materials.py --pattern "i-ah-1902-1905-sg-port_insurance-b01.json"
```

드라이런에서 확인할 것:

- 파일 1개만 잡혔는가
- `events`, `npcs`, `crises`, `sector_chains`, `market_data` 건수가 설계표와 크게 다르지 않은가
- 빈 배열만 가득한 껍데기 파일이 아닌가
- 이 단계는 파일 단위로 병렬 실행 가능하다

### Step 6. 일괄 적재

드라이런이 통과한 팩들만 모아서 일괄 적재한다.

```powershell
python -X utf8 test_material/ingest_i_materials.py --pattern "i-ah-*.json" --apply
```

원칙:

- 적재는 단일 작업자 1명만 수행
- 기본은 `INSERT OR IGNORE`
- 기존 keyed row를 덮어써야 할 명확한 사유가 있을 때만 `--replace` 사용
- `--apply`와 `material_bank_postprocess.py`는 병렬 금지

### Step 7. 후처리

raw table 적재가 끝나면 usable view를 재생성한다.

```powershell
python -X utf8 test_material/material_bank_postprocess.py
python -X utf8 test_material/query_material_bank.py audit
```

이 단계가 끝나야 비로소 집필 투입 가능 상태로 본다.

### Step 8. 집필 투입 전 최종 점검

작품에 넣기 전에 아래를 확인한다.

- usable view에 원하는 범위가 잡히는가
- 식민지 시대 핵심 사건이 빠지지 않았는가
- 항만, 금융, 밀수, 군수, 철도 같은 병목 섹터가 균형 있게 들어갔는가
- 사실 재료와 서사 아이디어가 뒤섞이지 않았는가

---

## 13. 중단 조건

아래 중 하나라도 발생하면 즉시 중단하고, 원인을 적은 뒤 더 작은 단위로 되돌린다.

- UTF-8 깨짐
- JSON 파손
- 같은 팩에서 기간이 계속 흔들림
- 사건과 인물의 국적, 직책, 시기가 충돌함
- `market_data`에 근거 없는 숫자를 넣으려 함
- 실존 재료와 가상 전개가 섞임
- 한 파일에서 3개 대륙 이상을 다룸
- LLM이 요약이 아니라 창작을 시작함
- "일단 DB에 넣고 나중에 고치자"라는 판단이 나옴

---

## 14. 품질 기준

### PASS 기준

- 팩 범위가 명확하다
- 필수 필드가 모두 찼다
- 사건과 인물과 위기가 서로 연결된다
- 항만/해운/보험/금융/밀수 같은 병목 구조가 보인다
- 수치가 있는 곳에는 실제 숫자 또는 명확한 범위가 있다
- 과장된 영웅 서사가 없다
- 역사 재료로 재사용 가능하다

### FAIL 기준

- 시대 분위기만 있고 사실 재료가 없다
- 사건명이 너무 추상적이다
- 인물이 "라이벌", "멘토" 수준으로만 적혀 있다
- sector chain이 억지다
- market_data가 비어 있는데 가짜 숫자를 채웠다
- 나중에 LLM이 그대로 쓰면 오류가 날 가능성이 높다

---

## 15. LLM 실행 템플릿

아래 템플릿을 복붙해서 "재료 JSON 생성 전용" 작업자에게 넘긴다.

```text
[역할]
너는 식민지 시대 / 대체역사 재료 JSON 생성 전용 작업자다.
너의 임무는 사실 재료를 구조화된 JSON 팩으로 만드는 것이다.

[절대 금지]
1. DB 접속, SQL 실행, DB 파일 수정
2. 마크다운 설명문 출력
3. 반사실적 결과를 사실처럼 작성
4. 근거 없는 숫자 생성
5. 물음표 3개 연속, TBD, 미정 남기기

[팩 범위]
- 기간: <입력>
- 지역: <입력>
- 핵심 섹터: <입력>
- 핵심 주제: <입력>
- source: <입력>

[출력 형식]
- 최상위 JSON 객체 1개
- 키는 반드시 events, npcs, crises, sector_chains, market_data
- 없는 항목도 빈 배열 [] 유지
- 코드펜스 금지

[작성 규칙]
1. 모든 자유서술은 한국어
2. 날짜는 가능한 범위 내에서 정확하게
3. category, sectors, connected_events, tags는 JSON 배열
4. confidence와 severity는 정수
5. market_data.value는 숫자
6. facts only
7. 한 팩의 범위를 넘기면 멈추고 분할안을 먼저 제시

[목표 수량]
- events: 20~40
- npcs: 6~12
- crises: 4~8
- sector_chains: 4~8
- market_data: 10~30

[최종 출력]
순수 JSON만 출력
```

---

## 16. 최소 예시 JSON

아래는 형식 예시다. 실제 작업에서는 범위에 맞게 늘린다.

```json
{
  "events": [
    {
      "id": "AH-E-1902-1905-SG-PORT_INSURANCE-B01-001",
      "source": "AH-1902-1905-SG-PORT_INSURANCE-B01",
      "date_start": "1903-01",
      "date_end": "1903-12",
      "event_name": "싱가포르 항만 중계무역 확대와 보험 수요 증가",
      "detail": "싱가포르 항은 영국령 해협식민지의 핵심 허브로 기능하며 동아시아와 인도양을 잇는 중계무역의 비중이 높아졌다. 운송량 증가와 함께 선박 보험, 화물 보험, 창고 보증, 통관 브로커 수요가 함께 늘어났다. 항만 운영권과 정보 접근권을 쥔 사업자에게는 합법 무역과 비공식 화물 운송을 동시에 붙일 여지가 생겼다.",
      "category": ["TRADE", "PORT", "FIN", "COLONIAL"],
      "sectors": ["항만", "해운", "보험", "무역/상사"],
      "region": "SG / SEA",
      "market_data": "중계무역 확대와 보험 수요 증가가 동반되며 운송 관련 서비스 마진이 상승하는 구조가 형성됨",
      "opportunity": "선박 소유보다 창고권, 보험 심사, 하역 계약부터 잡으면 현금흐름과 정보가 동시에 쌓인다.",
      "strategy": "항만 하역 계약과 보험 심사 라인을 묶어 거래 데이터를 선점한다.",
      "return_estimate": "고정자산 부담 대비 현금 회수 속도가 빠른 편",
      "capital_needed": "중간 규모 운전자금과 현지 행정 인맥 필요",
      "risk": "식민지 행정 규제, 전염병 검역, 전시 수송 재편 시 충격 가능",
      "connected_events": [],
      "narrative_use": "주인공이 양지에서는 보험사와 창고업자로 보이고, 음지에서는 야간 선적 정보를 먼저 받는 출발점으로 활용 가능",
      "tension": "합법 물류 계약과 비공식 운송 라인이 같은 항만에서 충돌한다.",
      "tags": ["싱가포르", "항만", "중계무역", "보험", "식민지 허브"],
      "confidence": 3
    }
  ],
  "npcs": [
    {
      "id": "AH-N-1902-1905-SG-PORT_INSURANCE-B01-001",
      "source": "AH-1902-1905-SG-PORT_INSURANCE-B01",
      "name": "해협식민지 항만 브로커형 상인",
      "role": "항만 브로커",
      "sector": "항만",
      "real_model": "복합: 영국계 항만 상인 + 화교 중개상",
      "personality": "거래형, 기회주의, 리스크 분산형",
      "relation_to_protag": "초기 현지 진입 창구이자 나중에는 수수료를 둘러싼 마찰 대상",
      "first_appearance": "1903년 항만 하역 계약 분쟁",
      "arc": "초반 조력자, 중반엔 이해관계 충돌, 후반엔 재편 대상",
      "detail": "통관, 창고, 선적 순번, 하역 인부 배치에 영향력을 행사하는 중간 권력자. 공식 문서보다 현장 질서를 더 잘 안다.",
      "tags": ["항만 브로커", "화교 네트워크", "중간 권력자"]
    }
  ],
  "crises": [
    {
      "id": "AH-C-1902-1905-SG-PORT_INSURANCE-B01-001",
      "source": "AH-1902-1905-SG-PORT_INSURANCE-B01",
      "crisis_type": "항만 검역 강화로 인한 선적 지연",
      "period": "1903-1904",
      "trigger_event": "항만 검역 강화",
      "severity": 3,
      "detail": "전염병 우려나 식민지 행정 지침 강화로 검역 절차가 늘어나면 선적 대기 시간이 길어지고, 보험료와 창고비가 동반 상승한다.",
      "resolution": "검역 일정이 느슨한 보조 항만과 창고를 병행 사용하고, 보험 계약 조건을 선제 조정한다.",
      "real_case": "식민지 항만 검역 강화와 물류 지연 사례 전반",
      "narrative_function": "합법 물류와 비공식 운송을 동시에 운영해야 하는 압박 장면",
      "placement_after": "항만 중계무역 확대 사건 뒤",
      "tags": ["검역", "선적 지연", "항만 위기"]
    }
  ],
  "sector_chains": [
    {
      "id": "AH-S-1902-1905-SG-PORT_INSURANCE-B01-001",
      "source": "AH-1902-1905-SG-PORT_INSURANCE-B01",
      "from_sector": "항만",
      "to_sector": "보험",
      "synergy_score": 5,
      "reason": "하역, 선적, 보관 정보가 보험 심사와 직결되므로 정보 우위를 가진 쪽이 보험료와 보상 판단을 좌우할 수 있다.",
      "capital_needed": "중간 규모 자본과 현지 인허가 인맥",
      "real_example": "항만 운영자와 해상보험 네트워크의 결합"
    }
  ],
  "market_data": []
}
```

위 예시는 형식 확인용이다. 실제 적재 전에는 근거 없는 숫자 placeholder를 절대 넣지 않는다.

---

## 17. 최종 체크리스트

적재 전 마지막으로 아래를 확인한다.

- 파일명 패턴이 `i-ah-*.json`인가
- 같은 basename의 `.meta.json`이 있는가
- 최상위 5개 키가 모두 있는가
- 필수 필드가 다 찼는가
- `source`가 한 팩 안에서 일관적인가
- payload의 `source`와 meta의 `source`가 일치하는가
- `id`가 중복되지 않는가
- 반사실적 결과가 섞이지 않았는가
- `market_data.value`에 가짜 숫자가 없는가
- UTF-8 깨짐이 없는가
- 드라이런 건수가 예상과 맞는가

이 체크리스트를 통과하지 못하면 DB 적재 금지.

---

## 18. 병렬 Wave 설계

병렬 수집은 가능하다. 다만 `시기 x 산업 x 지역 x 정치`를 완전한 곱집합으로 터미널 수만 늘리면 중복과 충돌이 폭증한다. 따라서 Wave는 "주축 1개 + 보조 축 1개"까지만 허용하는 구조로 쪼갠다.

### 18.1 핵심 원칙

- 같은 사실은 1개의 primary owner wave만 가진다.
- 다른 wave에서는 같은 사실을 복제하지 않고 `connected_events` 또는 `detail`에서 참조만 한다.
- timeline wave는 사건의 뼈대를 갖고, sector wave는 사업 구조를, political wave는 제도와 허가권을, hub wave는 도시/항로 병목을, crisis wave는 반복 가능한 충격 패턴을 담당한다.
- 병렬 허용 범위는 `JSON 작성`과 `드라이런`까지다.
- `DB apply`와 `postprocess`는 단일 작업자만 수행한다.

### 18.2 권장 Wave 묶음

#### Wave T: 시기 베이스라인

- `T1`: 1900~1904
- `T2`: 1905~1910
- `T3`: 1911~1918
- `T4`: 1919~1924
- `T5`: 1925~1929
- `T6`: 1930~1936
- `T7`: 1937~1945
- `T8`: 1946~1950

역할:

- 거시 사건 골격
- 조약, 전쟁, 항만 개장, 체제 전환, 금융 쇼크
- 각 시기별 핵심 병목 1차 식별

#### Wave S: 산업 / 병목 딥다이브

- `S1`: 항만 / 하역 / 보세창고
- `S2`: 해운 / 선박 / 항로 / 운임
- `S3`: 보험 / 해상보험 / 재보험
- `S4`: 은행 / 환 / 어음 / 결제
- `S5`: 무역 / 상사 / 중계무역
- `S6`: 광산 / 자원 / 농장
- `S7`: 철도 / 인프라 / 창고
- `S8`: 군수 / 조달 / 전쟁 특수
- `S9`: 정보 / 통신 / 전신 / 검열
- `S10`: 밀수 / 암시장 / 검문 우회

역할:

- 돈이 어디서 벌리고 어떻게 회수되는가
- 어떤 허가권과 정보권이 이익을 좌우하는가
- 양지와 음지가 어디서 붙는가

#### Wave P: 정치 / 국제역학 / 제도

- `P1`: 식민지 행정 / 총독부 / 조계
- `P2`: 관세 / 통상조약 / 치외법권
- `P3`: 경찰 / 헌병 / 검열 / 허가 / 면허
- `P4`: 열강 외교 / 조약 / 전쟁 외교
- `P5`: 통화체제 / 금본위 / 은본위 / 환전 제한
- `P6`: 노동 / 파업 / 민족운동 / 치안

역할:

- 허가와 단속이 어디서 발생하는가
- 국가권력과 회사권력이 어떻게 붙어 있는가
- 제도 변화가 사업기회와 검거 리스크를 어떻게 바꾸는가

#### Wave H: 허브 도시 / 항로 / 지역권력

- `H1`: 싱가포르 / 해협식민지
- `H2`: 상하이 / 조계 / 화계 네트워크
- `H3`: 홍콩 / 남중국 무역
- `H4`: 경성 / 인천 / 부산
- `H5`: 대련 / 하얼빈 / 만주
- `H6`: 바타비아 / 수라바야 / 네덜란드령 동인도
- `H7`: 사이공 / 하이퐁 / 프랑스령 인도차이나
- `H8`: 런던 / 암스테르담 / 마르세유

역할:

- 도시별 브로커 구조
- 항로별 병목과 통관 경로
- 각 허브에 붙는 금융, 보험, 정보, 밀수 네트워크

#### Wave C: 위기 엔진

- `C1`: 검역 / 전염병 / 격리
- `C2`: 전쟁 / 봉쇄 / 항로 차단
- `C3`: 환율 / 금은 가격 / 통화 쇼크
- `C4`: 단속 / 압수 / 검거 / 허가 취소
- `C5`: 파업 / 폭동 / 보험 분쟁
- `C6`: 어음 부도 / 은행 유동성 / 결제 경색

역할:

- 장편에서 반복 투입 가능한 위기 패턴
- 리스크와 우회 경로 데이터화

#### Wave X: 통합 / 감리 / 인수인계

- `X1`: 중복 / ID 충돌 / owner wave 점검
- `X2`: tag namespace / meta 파일 감리
- `X3`: 연표 모순 / 시기 오염 / 지역 혼선 검토
- `X4`: 드라이런 집계 / apply 대상 확정 / 일괄 적재 인계

### 18.3 권장 압축 병렬 규모

실전 기본값은 `42터미널 풀배치`가 아니라 `18터미널 압축 혼합 배치`다.

- 고컨텍스트 작업자용 `CTX` 터미널: 8개
- 저컨텍스트 작업자용 `LCTX` 터미널: 10개
- 총계: 18개

이유:

- timeline, 정치, 허브 도시처럼 다축 판단이 필요한 팩은 고컨텍스트 작업자에게 몰아주는 편이 낫다.
- 병목 섹터, 위기 라이브러리처럼 구조가 비교적 단순한 팩은 저컨텍스트 작업자에게 맡길 수 있다.
- 42개 풀배치는 감리 비용과 owner 충돌이 너무 커서 1차 배치 기본값으로는 과하다.

권장 분배:

- `CTX` 8개: Codex, GPT-5급, Opus급, 장문 컨텍스트 안정적인 모델
- `LCTX` 10개: Sonnet 계열, 저컨텍스트 작업자

42터미널 풀배치는 coverage를 극한으로 늘리고 싶을 때만 예외적으로 사용한다. 기본 운영은 `18터미널 압축 혼합 배치`를 따른다.

### 18.4 canonical wave와 표준 dispatch id 구분

- `18.2`의 `T1~T8`, `S1~S10`, `P1~P6`, `H1~H8`, `C1~C6`은 정규 wave taxonomy다.
- `22.4`의 `STD-*` 값은 `AH-STD18-1900-1950-B01` 전용 dispatch id다.
- dispatch id는 low-context 작업자가 자기 row를 빠르게 복원하기 위한 호출용 식별자다.
- 따라서 `STD-T1`은 `18.2`의 canonical `T1`과 같은 뜻이 아니다.
- 축약 호출 모드에서는 `18.2`보다 `22.4 표준 터미널 맵`의 `STD-*` row를 우선 해석한다.

---

## 19. 태그 taxonomy

앞에 문자열 몇 글자 붙이는 수준으로는 부족하다. 태깅은 아래 3층으로 분리한다.

### 19.1 3층 구조

1. `source`
   - 팩 출처와 계보
   - 예: `AH-1902-1905-SG-PORT_INSURANCE-B01`
2. row `tags`
   - 사건, 인물, 위기의 검색용 의미 태그
   - 향후 `keyword`와 `tag` 검색에서 같이 걸린다
3. pack meta
   - source 단위 메타
   - `material_bank_source_declared_meta`로 들어가고, 후처리 후 `material_bank_source_meta`로 합쳐진다

### 19.2 태그 원칙

- 역사 레이블보다 구조 레이블이 더 중요하다.
- 나중에 현대판타지에서 재활용하려면 `pattern:*`, `theme:*`, `use:*`, `fit:*`가 살아 있어야 한다.
- row마다 최소 4개의 구조화 태그를 넣는 것을 권장한다.
- freeform 태그를 아예 금지하진 않지만, namespace 태그를 먼저 넣는다.

### 19.3 namespace 권장 목록

| namespace | 의미 | 예시 |
|---|---|---|
| `domain:` | 재료의 대분류 | `domain:historical_material` |
| `group:` | source group | `group:historical_pack` |
| `scope:` | 팩의 범위 타입 | `scope:historical_fact_pack` |
| `era:` | 10년대 축 | `era:1930s` |
| `period:` | 구간 | `period:1930-1936` |
| `region:` | 지역 축약 | `region:sg`, `region:kr` |
| `sector:` | 섹터 | `sector:항만`, `sector:보험` |
| `theme:` | 주제 | `theme:colonial_admin`, `theme:smuggling` |
| `pattern:` | 구조 패턴 | `pattern:bottleneck_control`, `pattern:regulatory_arbitrage` |
| `fit:` | 장르 적합도 | `fit:alt_history`, `fit:modern_fantasy` |
| `use:` | 사용 모드 | `use:phase0`, `use:density`, `use:modern_analogy` |
| `power:` | 권력 성격 | `power:formal`, `power:informal` |
| `channel:` | 유통/통제 채널 | `channel:port`, `channel:rail`, `channel:customs` |
| `risk:` | 위기 축 | `risk:inspection`, `risk:currency`, `risk:blockade` |

### 19.4 fit와 use의 의미

`fit`는 "어느 장르에서 직접 재료로 쓰기 좋은가"를 뜻한다.

- `fit:alt_history`
- `fit:historical_fantasy`
- `fit:modern_fantasy`
- `fit:economic_story`

`use`는 "어떤 단계에서 주로 쓰는가"를 뜻한다.

- `use:phase0`
- `use:density`
- `use:tr`
- `use:bi`
- `use:reference`
- `use:modern_analogy`
- `use:npc_cast`
- `use:risk_design`

### 19.5 row tags 작성 예시

좋은 예:

```json
[
  "era:1900s",
  "region:sg",
  "sector:항만",
  "theme:colonial_trade",
  "pattern:bottleneck_control",
  "fit:alt_history",
  "use:phase0",
  "싱가포르",
  "중계무역"
]
```

나쁜 예:

```json
[
  "좋음",
  "대박",
  "재밌음",
  "역사"
]
```

### 19.6 source meta와의 관계

- row `tags`는 행 단위 세밀 검색용이다.
- pack meta의 `meta_tags`는 source 단위 축약 검색용이다.
- 같은 내용을 row와 pack meta에 모두 중복해서 꽉 채울 필요는 없다.
- 다만 `era`, `region`, `sector`, `pattern`, `fit`, `use` 중 핵심축은 pack meta에도 있어야 한다.

---

## 20. 팩 메타 스펙

팩 메타는 payload JSON 옆에 두는 companion 파일이다.

```text
i-ah-1902-1905-sg-port_insurance-b01.meta.json
```

현재 목적:

- 병렬 작업 중 누가 어떤 팩을 만들었는지 추적
- 드라이런 예상치와 실제 건수 대조
- 나중에 `material_bank_source_declared_meta`에 일괄 반영
- 현대판타지 / 대체역사 공용 재료은행에서 `fit`, `use`, `pattern` 축을 유지

### 20.1 DB 반영 대상 core fields

아래 필드는 나중에 `material_bank_source_declared_meta`에 넣을 수 있게 유지한다.

- `source`
- `domain`
- `source_group`
- `scope_type`
- `period_start`
- `period_end`
- `regions`
- `sectors`
- `themes`
- `structural_tags`
- `fit`
- `use_modes`
- `meta_tags`
- `notes`

### 20.2 파일 전용 ops fields

아래 필드는 메타 파일에만 두고, DB에는 꼭 넣지 않아도 된다.

- `payload_file`
- `wave_id`
- `batch_id`
- `owner`
- `status`
- `next_action`
- `completion_note`
- `row_targets`
- `dry_run_expected`
- `priority`

### 20.3 권장 메타 JSON 형식

```json
{
  "source": "AH-1902-1905-SG-PORT_INSURANCE-B01",
  "domain": "historical_material",
  "source_group": "historical_pack",
  "scope_type": "historical_fact_pack",
  "period_start": 1902,
  "period_end": 1905,
  "regions": ["SG", "SEA"],
  "sectors": ["항만", "해운", "보험", "무역/상사"],
  "themes": ["colonial_trade", "port_brokerage"],
  "structural_tags": [
    "pattern:bottleneck_control",
    "pattern:regulatory_arbitrage",
    "pattern:information_asymmetry"
  ],
  "fit": ["alt_history", "historical_fantasy", "modern_fantasy"],
  "use_modes": ["phase0", "density", "tr", "bi", "modern_analogy"],
  "meta_tags": [
    "domain:historical_material",
    "group:historical_pack",
    "scope:historical_fact_pack",
    "era:1900s",
    "period:1902-1905",
    "region:sg",
    "sector:항만",
    "sector:보험",
    "theme:colonial_trade"
  ],
  "notes": "싱가포르 항만을 식민지 허브 자본과 음지 운송의 결절점으로 잡는 팩",
  "payload_file": "i-ah-1902-1905-sg-port_insurance-b01.json",
  "wave_id": "H1",
  "batch_id": "AH-WAVE-H-B01",
  "owner": "terminal-h1",
  "status": "draft",
  "row_targets": {
    "events": 28,
    "npcs": 8,
    "crises": 5,
    "sector_chains": 5,
    "market_data": 12
  },
  "dry_run_expected": {
    "events": 28,
    "npcs": 8,
    "crises": 5,
    "sector_chains": 5,
    "market_data": 12
  },
  "priority": 4
}
```

### 20.4 메타 작성 규칙

- `source`는 payload 내부의 모든 row와 완전히 같아야 한다.
- `domain`은 대체역사 / 식민지 시대 팩이면 기본적으로 `historical_material`을 쓴다.
- `source_group`은 보통 `historical_pack`을 기본값으로 둔다.
- `scope_type`은 기본적으로 `historical_fact_pack`을 쓴다.
- `fit`에는 직접 재사용 가능한 장르만 넣는다.
- `fit:modern_fantasy`를 넣으려면 단순 역사 분위기가 아니라 구조적 재활용 가치가 있어야 한다.
- `meta_tags`는 사람이 직접 다 채우지 않아도 되지만, 최소 `domain / era / period / region / sector / fit / use` 축은 넣는 편이 좋다.
- `row_targets`와 `dry_run_expected`는 같아도 된다. 작업이 커지면 분리한다.
- `status`와 `next_action`은 완료 후 프로토콜에 따라 갱신한다.

### 20.5 권장 상태값

- `draft`
- `validated`
- `dry_run_pass`
- `ready_for_apply`
- `applied`
- `archived`

권장 `next_action` 값:

- `fix_payload`
- `fix_meta`
- `rerun_validation`
- `rerun_dry_run`
- `coordinator_review`
- `ready_for_apply`
- `archived`

---

## 21. 병렬 운영 프로토콜

### 21.1 역할 분리

- coordinator
  - Wave와 pack owner를 배정
  - 축약 호출 모드면 공통 하네스와 terminal id만 전달
  - 전체 오더 시트 모드면 공통 하네스와 개별 오더 시트를 같이 전달
  - basename 충돌, owner wave 충돌, apply 대상 확정을 관리
- 재료 생성 작업자
  - payload JSON 생성
  - `Mode B`에서는 `.meta.json`도 함께 생성 가능
  - facts only
  - DB 접근 금지
- 메타/감리 작업자
  - `.meta.json` 작성 또는 보정
  - 태그 namespace 감리
  - dry-run 결과 대조
- 적재 작업자
  - `--apply`
  - `material_bank_postprocess.py`
  - `query_material_bank.py audit`

### 21.2 파일 소유권 규칙

- 터미널 1개는 basename 1개만 소유한다.
- 예: `i-ah-1902-1905-sg-port_insurance-b01.*`
- 다른 터미널의 basename을 수정하지 않는다.
- 파일 충돌이 나면 새 배치 번호를 올린다.

### 21.3 병렬 허용 단계

- 팩 범위 고정
- payload JSON 작성
- `.meta.json` 작성
- UTF-8 검증
- JSON 문법 검증
- dry-run

### 21.4 직렬 강제 단계

- apply 대상 확정
- `python -X utf8 test_material/ingest_i_materials.py --apply`
- `python -X utf8 test_material/material_bank_postprocess.py`
- `python -X utf8 test_material/query_material_bank.py audit`

### 21.5 권장 실행 순서

1. coordinator가 Wave와 pack owner를 배정한다.
2. coordinator가 축약 호출 모드 또는 전체 오더 시트 모드 중 하나를 선택해 전달한다.
3. 각 작업자는 payload JSON을 만든다.
4. `Mode B`면 같은 작업자가 `.meta.json`까지 만들고, 아니면 메타/감리 작업자가 `.meta.json`을 작성하며 namespace를 점검한다.
5. 각 작업자가 자기 파일만 dry-run 한다.
6. coordinator가 dry-run 건수를 `.meta.json`의 `dry_run_expected`와 대조한다.
7. 통과한 파일만 apply 대상 목록에 넣는다.
8. 단일 작업자가 apply와 postprocess를 수행한다.
9. 마지막으로 `catalog`, `search`, `bundle --with-meta`로 메타 반영을 검수한다.

### 21.6 중복 통제 규칙

- 사건의 primary owner wave를 먼저 정한다.
- sector wave가 timeline wave의 사건을 복제하지 않는다.
- 같은 사건을 다른 wave에서 다시 써야 하면 새 row를 만들지 말고 `connected_events` 또는 `detail` 참조로 처리한다.
- primary owner가 불명확하면 JSON 작성 전에 coordinator가 owner를 확정한다.

---

## 22. 터미널 호출 규격

이 문서는 이제 `축약 호출 모드`를 지원한다. 즉, coordinator가 이 하네스 문서만 주고 `너는 1번 터미널이다`라고 말해도, 표준 배치 범위 안에서는 작업자가 자동으로 자기 역할을 해석할 수 있어야 한다.

다만 이 기능은 아무 경우에나 쓰는 것이 아니라, 아래 조건을 만족하는 `표준 1차 수집 배치`에서만 사용한다.

### 22.1 축약 호출 모드

아래 두 조건을 동시에 만족하면 작업자는 `축약 호출 모드`로 진입한다.

1. 공통 하네스로 `docs/2026-03-10/alt_history_material_json_harness.md`만 전달받았다.
2. 추가 지시가 사실상 `너는 N번 터미널이다` 수준이다.

축약 호출 모드에서 작업자는:

- 파일을 쓰기 전에 자기 로컬 오더 시트를 내부적으로 1회 복원한다.
- 이 문서의 `22.4 표준 터미널 맵`을 기준으로 자기 wave와 팩을 자동 해석한다.
- 이 문서의 `22.5 기본 산출 규격`을 기준으로 `source`, `payload_file`, `meta_file`, 목표 수량, 출력 모드를 자동 확정한다.
- 별도 오더 시트가 없더라도 기본적으로 작업을 진행한다.

내부 로컬 오더 시트에 최소 포함해야 하는 값:

- `terminal_id`
- `wave_id`
- `source`
- `payload_file`
- `meta_file`
- `기간`
- `지역`
- `핵심 섹터`
- `핵심 주제`
- `목표 수량`
- `출력 모드`

축약 호출 모드에서 `wave_id`는 `18.2` canonical wave id가 아니라 `22.4`의 `STD-*` dispatch id를 뜻한다.

이 복원이 끝나기 전에는 파일 작성 금지.

즉, 아래처럼 받아도 된다.

```text
공통 규칙은 alt_history_material_json_harness.md를 따른다.
너는 1번 터미널이다.
```

이 경우 1번 터미널은 문서 내부의 표준 맵을 보고 자기 작업을 스스로 확정한다.

### 22.2 축약 호출 모드의 범위

축약 호출 모드는 `표준 1차 압축 혼합 배치 B01`에만 적용한다.

- 기본 campaign id: `AH-STD18-1900-1950-B01`
- 지원 terminal id: `1~18`
- 기본 출력 모드: `Mode B`
  - 즉, payload JSON과 `.meta.json`을 둘 다 만든다.

지원하지 않는 경우:

- `19` 이상 비표준 터미널
- `B02` 이상 재작성 배치
- 특정 작품 맞춤형 커스텀 범위
- 표준 맵을 벗어난 기간/지역/섹터

이 경우에는 `22.7 전체 오더 시트 모드`를 쓴다.

### 22.3 축약 호출 모드에서 질문해도 되는 예외

축약 호출 모드라도 아래 경우에는 멈추고 질문해도 된다.

- terminal id가 `1~18` 밖이다
- 자기 basename 파일이 이미 존재하고, 덮어쓰면 기존 결과와 충돌할 수 있다
- 문서 내부 표준 맵과 실제 지시가 명백히 충돌한다
- UTF-8 파손이나 JSON 파손이 이미 존재한다

그 외에는 묻지 않고 표준 맵대로 진행한다.

### 22.4 표준 터미널 맵

아래 맵은 `표준 1차 압축 혼합 배치 B01`의 고정 배치다.

주의:

- 아래 `wave_id`는 모두 `STD-*` dispatch id다.
- `18.2`의 canonical wave taxonomy와 혼동하지 않는다.

- `CTX`: 고컨텍스트 작업자용
  - 권장: Codex, GPT-5급, Opus급
- `LCTX`: 저컨텍스트 작업자용
  - 권장: Sonnet 계열

#### A. CTX 터미널 1~8

| terminal_id | ctx_class | wave_id | 기간 | 지역 | 핵심 섹터 | 핵심 주제 | source | payload_file | meta_file |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CTX | STD-T1 | 1900~1910 | KR, JP, QING, SEA | 항만, 무역/상사, 은행/금융, 식민지 행정 | 러일전쟁 전야와 식민지 전환기의 동아시아 재편 | `AH-1900-1910-EASTASIA-BASELINE-B01` | `i-ah-1900-1910-eastasia-baseline-b01.json` | `i-ah-1900-1910-eastasia-baseline-b01.meta.json` |
| 2 | CTX | STD-T2 | 1911~1924 | CN, JP, KR, SEA | 해운, 보험, 무역/상사, 정보/통신 | 신해혁명, 1차대전, 전후 재편과 조계 경제 | `AH-1911-1924-WAR_POSTWAR-BASELINE-B01` | `i-ah-1911-1924-war_postwar-baseline-b01.json` | `i-ah-1911-1924-war_postwar-baseline-b01.meta.json` |
| 3 | CTX | STD-T3 | 1925~1936 | SEA, CN, JP, MANCHURIA | 무역/상사, 자원, 은행/금융, 철도/인프라 | 전간기 호황, 대공황, 블록경제, 만주 진출 | `AH-1925-1936-BOOM_BLOCK-BASELINE-B01` | `i-ah-1925-1936-boom_block-baseline-b01.json` | `i-ah-1925-1936-boom_block-baseline-b01.meta.json` |
| 4 | CTX | STD-T4 | 1937~1950 | CN, JP, KR, SEA, GLOBAL | 군수/방산, 해운, 밀수/암시장, 은행/금융 | 전시경제, 전후 암시장, 냉전 초입 재편 | `AH-1937-1950-WARTIME_POSTWAR-BASELINE-B01` | `i-ah-1937-1950-wartime_postwar-baseline-b01.json` | `i-ah-1937-1950-wartime_postwar-baseline-b01.meta.json` |
| 5 | CTX | STD-P1 | 1900~1950 | KR, CN, SEA | 식민지 행정, 정보/통신, 노동, 치안 | 총독부, 조계, 경찰, 헌병, 파업, 치안 병목 | `AH-1900-1950-COLONIAL_CONTROL-B01` | `i-ah-1900-1950-colonial_control-b01.json` | `i-ah-1900-1950-colonial_control-b01.meta.json` |
| 6 | CTX | STD-P2 | 1900~1950 | GLOBAL | 외교, 관세, 은행/금융, 통화체제 | 통상조약, 열강 외교, 금본위/은본위, 환전 제한 | `AH-1900-1950-TREATY_DIPLO_CURRENCY-B01` | `i-ah-1900-1950-treaty_diplo_currency-b01.json` | `i-ah-1900-1950-treaty_diplo_currency-b01.meta.json` |
| 7 | CTX | STD-H1 | 1900~1950 | SG, HK, SEA | 항만, 해운, 보험, 무역/상사 | 싱가포르-홍콩-해협식민지 해상 허브 네트워크 | `AH-1900-1950-SEA_MARITIME_HUBS-B01` | `i-ah-1900-1950-sea_maritime_hubs-b01.json` | `i-ah-1900-1950-sea_maritime_hubs-b01.meta.json` |
| 8 | CTX | STD-H2 | 1900~1950 | SH, KR, MANCHURIA, CN | 무역/상사, 금융, 철도/인프라, 식민지 행정 | 상하이-조계-경성-만주 육해 복합 병목 네트워크 | `AH-1900-1950-SH_KR_MANCHURIA-HUBS-B01` | `i-ah-1900-1950-sh_kr_manchuria-hubs-b01.json` | `i-ah-1900-1950-sh_kr_manchuria-hubs-b01.meta.json` |

#### B. LCTX 터미널 9~18

| terminal_id | ctx_class | wave_id | 기간 | 지역 | 핵심 섹터 | 핵심 주제 | source | payload_file | meta_file |
|---|---|---|---|---|---|---|---|---|---|
| 9 | LCTX | STD-S1 | 1900~1950 | GLOBAL | 항만, 창고 | 항만 하역, 창고권, 보세구역 병목 | `AH-1900-1950-PORT_WAREHOUSE-B01` | `i-ah-1900-1950-port_warehouse-b01.json` | `i-ah-1900-1950-port_warehouse-b01.meta.json` |
| 10 | LCTX | STD-S2 | 1900~1950 | GLOBAL | 해운, 항로 | 선박, 항로, 운임, 중계항 병목 | `AH-1900-1950-SHIPPING_ROUTES-B01` | `i-ah-1900-1950-shipping_routes-b01.json` | `i-ah-1900-1950-shipping_routes-b01.meta.json` |
| 11 | LCTX | STD-S3 | 1900~1950 | GLOBAL | 보험, 재보험 | 해상보험, 화물보험, 재보험 네트워크 | `AH-1900-1950-MARINE_INSURANCE-B01` | `i-ah-1900-1950-marine_insurance-b01.json` | `i-ah-1900-1950-marine_insurance-b01.meta.json` |
| 12 | LCTX | STD-S4 | 1900~1950 | GLOBAL | 은행/금융, 환 | 환전, 어음, 결제, 외환 통제 | `AH-1900-1950-BANKING_FX-B01` | `i-ah-1900-1950-banking_fx-b01.json` | `i-ah-1900-1950-banking_fx-b01.meta.json` |
| 13 | LCTX | STD-S5 | 1900~1950 | GLOBAL | 무역/상사 | 중계무역, 상사회사, 브로커 구조 | `AH-1900-1950-TRADING_HOUSES-B01` | `i-ah-1900-1950-trading_houses-b01.json` | `i-ah-1900-1950-trading_houses-b01.meta.json` |
| 14 | LCTX | STD-S6 | 1900~1950 | SEA, CN, KR | 광산/자원, 농장/원자재 | 광산, 고무, 주석, 농장 자산화 | `AH-1900-1950-RESOURCE_EXTRACTION-B01` | `i-ah-1900-1950-resource_extraction-b01.json` | `i-ah-1900-1950-resource_extraction-b01.meta.json` |
| 15 | LCTX | STD-S7 | 1900~1950 | KR, CN, MANCHURIA | 철도/인프라, 창고 | 철도, 물류망, 창고, 수송 병목 | `AH-1900-1950-RAIL_INFRA-B01` | `i-ah-1900-1950-rail_infra-b01.json` | `i-ah-1900-1950-rail_infra-b01.meta.json` |
| 16 | LCTX | STD-S8 | 1900~1950 | GLOBAL | 군수/방산, 조달 | 군수 조달, 전쟁 특수, 군납 브로커 | `AH-1900-1950-MUNITIONS_PROCUREMENT-B01` | `i-ah-1900-1950-munitions_procurement-b01.json` | `i-ah-1900-1950-munitions_procurement-b01.meta.json` |
| 17 | LCTX | STD-S9 | 1900~1950 | GLOBAL | 정보/통신, 밀수/암시장 | 전신, 검열, 정보 흐름, 밀수 우회 | `AH-1900-1950-INFORMATION_SMUGGLING-B01` | `i-ah-1900-1950-information_smuggling-b01.json` | `i-ah-1900-1950-information_smuggling-b01.meta.json` |
| 18 | LCTX | STD-C1 | 1900~1950 | GLOBAL | 위기/리스크 | 검역, 봉쇄, 환율, 단속, 파업, 유동성 위기 라이브러리 | `AH-1900-1950-CRISIS_LIBRARY-B01` | `i-ah-1900-1950-crisis_library-b01.json` | `i-ah-1900-1950-crisis_library-b01.meta.json` |

### 22.5 기본 산출 규격

축약 호출 모드에서 작업자는 아래 기본 규격을 자동 적용한다.

#### 공통

- 출력 모드: `Mode B`
- 최종 산출물: `payload JSON + meta JSON`
- 저장 경로: `test_material/json_outputs/`
- batch: `B01`
- facts only
- 코드펜스 금지
- 호출 1회당 basename 1개만 처리
- 완료 후 자동으로 `24. 완료 후 프로토콜`을 수행하고 중단

#### 기본 목표 수량

| wave family | events | npcs | crises | sector_chains | market_data |
|---|---:|---:|---:|---:|---:|
| `CTX-STD-T*` | 30~40 | 6~10 | 5~8 | 4~6 | 8~15 |
| `CTX-STD-P*` | 22~32 | 5~8 | 4~6 | 3~5 | 4~10 |
| `CTX-STD-H*` | 24~34 | 6~10 | 4~6 | 4~6 | 6~12 |
| `LCTX-STD-S*` | 18~28 | 4~8 | 3~5 | 4~7 | 5~10 |
| `LCTX-STD-C*` | 10~16 | 2~4 | 8~12 | 2~4 | 2~6 |

#### meta 기본값

- `domain`: `historical_material`
- `source_group`: `historical_pack`
- `scope_type`: `historical_fact_pack`
- `fit`: 최소 `["alt_history", "historical_fantasy"]`
- `use_modes`: 최소 `["phase0", "density", "tr", "bi"]`

### 22.6 축약 호출 모드 좋은 예시

아래처럼만 주어도 된다.

```text
공통 규칙은 alt_history_material_json_harness.md를 따른다.
너는 1번 터미널이다.
```

이 경우 1번 터미널은 자동으로 아래처럼 해석한다.

- `ctx_class`: `CTX`
- `wave_id`: `STD-T1`
- `source`: `AH-1900-1910-EASTASIA-BASELINE-B01`
- `payload_file`: `i-ah-1900-1910-eastasia-baseline-b01.json`
- `meta_file`: `i-ah-1900-1910-eastasia-baseline-b01.meta.json`
- 출력 모드: `Mode B`

### 22.7 전체 오더 시트 모드

축약 호출 모드보다 더 안전한 방식은 여전히 `전체 오더 시트 모드`다. 아래 경우에는 반드시 이 모드를 쓴다.

- 커스텀 작품 맞춤형 범위
- 기존 표준 맵을 수정해야 하는 경우
- `B02` 이상 재작업
- `19` 이상 비표준 터미널

#### 전체 오더 시트 필수 항목

- `terminal_id`
- `wave_id`
- `기간`
- `지역`
- `핵심 섹터`
- `핵심 주제`
- `작품상 목표`
- `source`
- `payload_file`
- `meta_file`
- `목표 수량`
- `출력 모드`
- `절대 금지 사항`

#### 전체 오더 시트 템플릿

```text
너는 <terminal_id>번 터미널이다.
공통 규칙은 docs/2026-03-10/alt_history_material_json_harness.md를 따른다.

[이번 작업]
- wave_id: <wave_id>
- 기간: <기간>
- 지역: <지역>
- 핵심 섹터: <핵심 섹터>
- 핵심 주제: <핵심 주제>
- 작품상 목표: <작품상 목표>
- source: <source>
- payload_file: <payload_file>
- meta_file: <meta_file>

[목표 수량]
- events: <수량>
- npcs: <수량>
- crises: <수량>
- sector_chains: <수량>
- market_data: <수량>

[출력 모드]
- <Mode A 또는 Mode B>

[절대 금지]
1. DB 접근
2. 다른 터미널 basename 수정
3. facts only 위반
4. 물음표 3개 연속, TBD, 미정 남기기
5. 범위를 넘긴 뒤 임의로 확장하기

[최종 출력]
- <payload JSON만 / payload JSON + meta JSON>
- 코드펜스 금지
```

### 22.8 나쁜 전달 예시

아래는 여전히 나쁘다.

```text
너는 19번 터미널이다.
하네스 보고 알아서 해라.
```

`19` 이상 비표준 터미널은 축약 호출 모드를 지원하지 않는다. 이 범위는 반드시 전체 오더 시트가 필요하다.

---

## 23. 저컨텍스트 Sonnet 안전장치

이 절은 "컨텍스트가 적은 Sonnet 계열이 멍청하게 굴 가능성"을 줄이기 위한 강제 규칙이다.

### 23.1 Sonnet용 강제 실행 순서

저컨텍스트 작업자는 반드시 아래 순서대로만 움직인다.

1. 자기 terminal id 확인
2. `22.4 표준 터미널 맵`에서 자기 row 찾기
3. 로컬 오더 시트 복원
4. payload JSON 작성
5. `.meta.json` 작성
6. UTF-8 점검
7. JSON 문법 점검
8. dry-run
9. `.meta.json`의 `status`, `next_action`, `completion_note` 갱신
10. 결과 보고 후 중단

위 순서를 건너뛰는 축약은 금지한다.

### 23.2 Sonnet 금지 행동

- 자기 terminal id 외의 다른 팩을 같이 처리
- 파일 2개 이상을 같은 호출에서 새로 시작
- `dry-run` 전에 완료 선언
- `status` 갱신 없이 종료
- 기존 다른 basename 수정
- 자기 판단으로 `B02`를 시작
- `apply`나 `postprocess`까지 직접 진행
- validation 실패 상태에서 "일단 됨"으로 넘기기

### 23.3 Sonnet 질문 규칙

- 질문은 예외 조건에서만 한다.
- 예외 조건이 아니면 추측하지 말고 표준 맵을 따른다.
- broad question 금지.
- 질문이 필요할 때도 1문장으로 짧게 묻는다.

좋은 질문 예:

```text
`i-ah-1900-1910-eastasia-baseline-b01.json`이 이미 존재합니다. 덮어쓸지 `B02`로 올릴지 확인 필요합니다.
```

나쁜 질문 예:

```text
제가 뭘 해야 하나요?
```

### 23.4 Sonnet 보고 규격

완료 보고는 짧고 기계적으로 한다.

권장 형식:

```text
[done]
terminal_id: 1
wave_id: STD-T1
source: AH-1900-1910-EASTASIA-BASELINE-B01
payload_file: i-ah-1900-1910-eastasia-baseline-b01.json
meta_file: i-ah-1900-1910-eastasia-baseline-b01.meta.json
status: dry_run_pass
next_action: coordinator_review
```

---

## 24. 완료 후 프로토콜

작업자가 자기 팩을 끝낸 뒤 자동으로 수행해야 하는 후속 절차다. 별도 지시가 없어도 이 절은 실행한다.

### 24.1 완료 조건

아래를 모두 만족해야 `완료`로 본다.

- payload JSON 저장 완료
- `.meta.json` 저장 완료
- UTF-8 검증 통과
- JSON 문법 검증 통과
- dry-run 완료

### 24.2 완료 후 자동 처리

완료 조건을 만족하면 아래를 자동 수행한다.

1. `.meta.json`의 `status`를 `dry_run_pass` 또는 그 직전 단계로 갱신
2. `.meta.json`의 `next_action`을 설정
3. `.meta.json`의 `completion_note`에 짧은 결과 메모를 남김
4. coordinator에게 `23.4 Sonnet 보고 규격` 형식으로 결과 전달
5. 중단

### 24.3 실패 시 자동 처리

검증 또는 dry-run에서 실패하면 아래를 자동 수행한다.

1. `.meta.json`의 `status`를 실패 직전 단계로 둔다
2. `.meta.json`의 `next_action`을 `fix_payload`, `fix_meta`, `rerun_validation`, `rerun_dry_run` 중 하나로 둔다
3. `completion_note`에 실패 원인을 한 줄로 기록한다
4. 자기 팩 안에서 고칠 수 있으면 한 번만 수정 후 재검증한다
5. 그래도 실패하면 보고 후 중단한다

### 24.4 완료 후 금지 행동

- 다음 terminal id 작업을 임의로 시작
- 다른 wave로 넘어감
- `apply` 실행
- `postprocess` 실행
- 다른 파일 감리 시작
- "시간 남으니 다른 팩도 하자" 식의 임의 확장

### 24.5 coordinator를 위한 해석 규칙

coordinator는 작업자 보고를 받으면 아래처럼 해석한다.

- `status: dry_run_pass` + `next_action: coordinator_review`
  - apply 후보군에 넣을 수 있다
- `status: validated` + `next_action: rerun_dry_run`
  - dry-run만 다시 시키면 된다
- `status: draft` + `next_action: fix_payload`
  - payload 수정이 먼저다
- `status: draft` + `next_action: fix_meta`
  - meta 보정이 먼저다
