# 대체역사 DB 연동 하네스 v1

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-10
> 적용 장르: `alt_history`
> 목적: **대체역사 작품의 Phase 0/TR/BI 작업 전에 `material_bank`에서 관련 재료를 먼저 조회하고, 그 결과를 생산 준비 패킷으로 고정**
> 선행 문서: `SSOT_blockguide-integrated-order.md`, `treatment-planning-harness.md`, `treatment-production-harness-v2.md`, `bi-production-harness-v1.md`

---

## 0. 이 문서를 언제 읽는가

아래 중 하나라도 해당하면, 범용 Blockguide 문서 4개를 읽은 직후 이 문서를 추가로 읽는다.

1. 작품 장르가 `alt_history`다.
2. 조선, 대한제국, 식민지 조선, 만주, 제국 일본, 동아시아 근대사 기반 대체역사다.
3. 사용자가 "역사 재료", "사료", "DB에서 뽑아", "material_bank에서 찾아", "근거 붙여"를 요구한다.
4. `Phase 0`, `TR`, `BI`를 만들기 전에 역사 재료를 먼저 모아야 한다.

참고:

- 현대판타지 일반 장르의 재료 준비는 `modern_fantasy_material_harness.md`가 담당한다.
- 현재 문서는 그중 **역사 재료 전용 특화판**이다.

핵심 원칙:

- 대체역사물은 기억보다 `material_bank`를 먼저 본다.
- 이미 DB에 있는 역사 재료를 무시하고 임의 상상으로 골격을 채우지 않는다.
- `TR`과 `BI`는 DB 기반 재료 패킷 위에서 만든다.
- DB 조회 자동화는 허용되지만, `source_manifest` 확정은 반드시 수동 감리를 거친다.
- 여기서 `auto-run`은 조회 순서를 이어 간다는 뜻이지, DB 결과를 검토 없이 다음 단계로 넘기라는 뜻이 아니다.

---

## 0A. 초저지능 LLM용 빠른 시작

대체역사 작업이면 아래 8단계만 그대로 따른다.

1. `SSOT_blockguide-integrated-order.md`를 UTF-8로 읽는다.
2. `treatment-planning-harness.md`, `treatment-production-harness-v2.md`, `bi-production-harness-v1.md`를 UTF-8로 읽는다.
3. 이 문서를 UTF-8로 읽는다.
4. 작품 단계가 `Planning`, `Production`, `BI` 중 어디인지 파일 존재로 판정한다.
5. `test_material/material_bank.db`에서 `catalog`와 `bundle`을 먼저 조회한다.
6. 조회 결과로 `source_manifest` 초안을 만든다.
7. `source_manifest`를 사람이 읽고 수동 감리한다.
8. 감리된 `source_manifest` 없이 `Phase 0`, `TR`, `BI`를 바로 쓰지 않는다.
9. 재료가 약하면 상상으로 때우지 말고, 먼저 AH 범위를 넓혀 다시 조회하거나 필요 시 `alt_history_material_json_harness.md`로 새 재료 생산을 요청한다.

금지:

- DB를 보지 않고 역사 재료를 메모리로 재조립하기
- `AH-*` 자료가 충분한데도 일반론으로만 기획안을 채우기
- `TR` 초안 안에 사실 근거 없는 기관, 인물, 제도, 소유 구조를 끼워 넣기
- `BI`에 긴 역사 요약을 새로 창작하기

---

## 1. 역할 분리

이 문서의 역할은 "대체역사 재료를 DB에서 꺼내어 Phase 0/TR/BI 준비 상태로 만드는 것"이다.

역할 경계:

- `treatment-planning-harness.md`: 서사 설계 원칙
- `treatment-production-harness-v2.md`: TR 블록 생산 규칙
- `bi-production-harness-v1.md`: BI 동기화/감리 규칙
- 현재 문서: **대체역사 DB 조회, 소스 선택, 준비 패킷 구성**
- `alt_history_material_json_harness.md`: **DB에 없는 대체역사 재료를 새 JSON 팩으로 생산할 때만 사용**

즉:

- 이미 DB에 있으면 현재 문서를 쓴다.
- DB에 없으면 `alt_history_material_json_harness.md`로 보강한 뒤 다시 현재 문서로 돌아온다.

---

## 2. SSOT

대체역사 재료 준비 단계의 SSOT는 아래 순서다.

1. `test_material/material_bank.db`
2. `test_material/query_material_bank.py`
3. 현재 작품의 기획 문서, `phase0_design`, `TR draft`, `BI`

규칙:

- 역사 사실 밀도는 DB에서 뽑는다.
- 블록 연속성은 `Phase 0`와 `TR draft`가 담당한다.
- `BI.plot_roadmap`는 여전히 `TR draft`에서 복사한다.
- DB는 재료 은행이지, `TR` 연속성 엔진이 아니다.
- DB 조회 결과는 초안일 뿐이며, `source_manifest` 수동 감리 전에는 SSOT로 승격하지 않는다.

---

## 3. 기본 조회 프로토콜

### 3.1 카탈로그 조회

대체역사 작업 시작 시 최소 1회는 카탈로그를 본다.

```powershell
python -X utf8 test_material/query_material_bank.py catalog `
  --source "AH-" `
  --limit 100
```

목적:

- 현재 DB에 들어 있는 `AH-*` 소스 범위를 확인
- 이미 충분한 재료가 있는지 먼저 판정
- 누락 팩이 있으면 새 재료 생산 여부 판단

### 3.2 핵심 번들 조회

작품의 시대/지역/섹터에 맞는 핵심 소스부터 `bundle`로 뽑는다.

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --source "KR_ROYAL_ASSETS_EXILE" `
  --limit-events 8 `
  --limit-npcs 6 `
  --limit-crises 4 `
  --limit-sector-chains 4 `
  --limit-market-data 6 `
  --with-meta
```

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --source "EU_FINANCE_PORTS" `
  --limit-events 8 `
  --limit-npcs 6 `
  --limit-crises 4 `
  --limit-sector-chains 4 `
  --limit-market-data 6 `
  --with-meta
```

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --source "KR_COLONIAL_ASSET_TAKEOVER" `
  --limit-events 10 `
  --limit-npcs 6 `
  --limit-crises 4 `
  --limit-sector-chains 5 `
  --limit-market-data 6 `
  --with-meta
```

### 3.3 보조 번들 조회

핵심 3팩만으로 부족하면 섹터/연도/지역 축으로 보조 조회를 추가한다.

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --keyword "조선은행,식산은행,동양척식,철도,광산,보험,선적금융" `
  --year-start 1905 `
  --year-end 1938 `
  --limit-events 12 `
  --limit-npcs 8 `
  --limit-crises 6 `
  --limit-sector-chains 6 `
  --limit-market-data 10
```

보조 추천 source substring:

- `BANKING_FX`
- `MARINE_INSURANCE`
- `SH_KR_MANCHURIA-HUBS`
- `RAIL_INFRA`
- `RESOURCE_EXTRACTION`
- `BOOM_BLOCK`
- `WARTIME_POSTWAR`

---

## 4. source_manifest 필수 규격

대체역사 작품은 `Phase 0` 전에 아래 6개를 최소로 정리한다.

```json
{
  "work_id": "작품 식별자",
  "genre": "alt_history",
  "catalog_scope": "AH-*",
  "core_sources": [
    "AH-1905-1910-KR_ROYAL_ASSETS_EXILE-B01",
    "AH-1907-1936-EU_FINANCE_PORTS-B01",
    "AH-1910-1938-KR_COLONIAL_ASSET_TAKEOVER-B01"
  ],
  "support_sources": [
    "AH-1900-1950-BANKING_FX-B01",
    "AH-1900-1950-MARINE_INSURANCE-B01",
    "AH-1900-1950-RAIL_INFRA-B01"
  ],
  "why_selected": {
    "opening": "오프닝/망명/황실 자산 반출",
    "midgame": "유럽 성장/항만/금융/보험",
    "payoff": "식민지 자산 매집/등기/지분 인수"
  }
}
```

운영 규칙:

- `core_sources`는 2개 이상
- `support_sources`는 2개 이상 권장
- 왜 이 소스를 고른 건지 한 줄 근거를 남긴다
- source 이름을 추상적으로 줄이지 말고, 실제 DB source 문자열 기준으로 적는다

---

## 5. Phase 0 준비 패킷

`Phase 0`로 넘기기 전에 DB 번들에서 아래 5묶음을 추출한다.

### 5.1 역사 엔진

- 시작 시점의 국제 정세
- 분기점을 만들 수 있는 실제 역사 사건
- 조선/만주/일본/유럽 간 연결 경로
- 주인공이 비집고 들어갈 제도적 틈

### 5.2 사업 엔진

- 은행, 외환, 해운, 보험, 철도, 광산, 창고, 군수 중 주력 2~4개
- 담보, 채권, 지분, 인허가, 경매, 운송 병목 같은 실무 메커니즘
- 돈이 어디서 벌리고 어디서 새는지

### 5.3 NPC 엔진

- 실존 인물 또는 실존형 역할군 8~12명
- 협력자, 반대자, 중개자, 정보원, 법률/등기 실무자 분리
- 각 인물이 주인공에게 제공하는 실익과 리스크

### 5.4 위기 엔진

- 공황, 환율, 금본위, 운임, 보험, 전쟁, 총동원 같은 시스템 위기
- 블록경제, 규제, 수탈 구조, 금융 경색
- 70블록 기준 장기 위기 사다리

### 5.5 장소 엔진

- 경성, 인천, 부산, 신의주, 대련, 로테르담, 앤트워프, 취리히, 런던 같은 허브
- 장소별 기능을 분리: 금융, 선적, 등기, 외교, 밀수, 철도 환적, 광산 담보

`Phase 0` 입력으로 넘길 때는 "사건 목록"이 아니라 "블록 설계에 바로 쓰일 재료"로 정리한다.

---

## 6. TR 준비 규칙

`TR draft`는 DB 번들을 그대로 복사해 붙이는 문서가 아니다.
대신 각 대단원이 어떤 source 묶음을 소비하는지 먼저 고정한다.

권장 매핑 예시:

| 대단원 | 우선 source | 용도 |
| ---- | ---- | ---- |
| Arc 1 | `KR_ROYAL_ASSETS_EXILE` | 출발 자산, 망명/유학 명분, 황실 재정 흔적 |
| Arc 2~3 | `EU_FINANCE_PORTS`, `BANKING_FX`, `MARINE_INSURANCE` | 유럽 성장, 해운금융, 보험, 외환 |
| Arc 4~5 | `KR_COLONIAL_ASSET_TAKEOVER`, `RAIL_INFRA`, `RESOURCE_EXTRACTION` | 조선/만주 자산 인수, 담보/등기/철도 |
| Arc 6~7 | `BOOM_BLOCK`, `WARTIME_POSTWAR`, `SH_KR_MANCHURIA-HUBS` | 대공황, 총력전, 전후 재편 |

TR 준비 체크:

- 각 Arc에 최소 1개의 핵심 source를 배정
- `event`, `npc`, `crisis`, `sector_chain`, `market_data`가 한 Arc 안에서 최소 3종 이상 섞이게 배정
- 주인공의 사업 확장이 시대 질서와 충돌하는 지점을 위기로 배치
- DB에 있는 메커니즘 용어를 우선 사용하고, 없는 메커니즘은 gap으로 표시

금지:

- TR에서 실제 제도/기관/시장 메커니즘을 완전히 새로 발명하기
- 근거 없는 "비밀 금괴", "만능 황실 자산"을 사실처럼 취급하기
- 같은 source를 7개 Arc에 균등 복붙하기

---

## 7. BI 준비 규칙

BI 단계에서 DB는 직접 `plot_roadmap`를 만드는 데 쓰지 않는다.
대신 `TR draft`를 풍성하게 만들기 위한 역사 뼈대와 용어 정합성을 제공한다.

BI 준비 시 DB에서 가져올 것:

- 시대 배경 서술에 필요한 핵심 역사 사실
- `AltHistoryWorld` 또는 동등 섹션에 넣을 제도/당대 질서 요약
- 주인공이 실제로 활용하는 역사 메커니즘
- 자산 구조, 항만, 철도, 식민지 금융, 블록경제 관련 용어

BI 준비 시 여전히 `TR draft`에서 복사할 것:

- `plot_roadmap`
- 블록 제목
- 자본 또는 권력 이력
- 블록별 요약

원칙:

- BI는 역사 백과사전이 아니다.
- DB에서 긴 문단을 그대로 옮기지 말고, `TR`에서 실제로 쓰인 축만 짧게 동기화한다.
- BI가 DB보다 풍부해 보이려고 새 사실을 덧칠하지 않는다.

---

## 8. 재료 부족 시 대응

아래 중 하나면 현재 DB만으로는 부족한 것으로 본다.

1. 핵심 Arc 3개 이상에 대응하는 source가 비어 있다.
2. 사건은 많은데 장소/메커니즘/NPC가 지나치게 빈약하다.
3. 유럽 현장, 식민지 자산 인수 실무, 전시 통제 같은 핵심 축 중 하나가 없다.
4. 조회 결과가 일반론 위주라 블록 단위 장면이 안 나온다.

대응 순서:

1. `bundle` 조건을 넓혀 재조회
2. `catalog`에서 관련 `AH-*` source를 다시 탐색
3. 그래도 없으면 `alt_history_material_json_harness.md`로 새 재료 팩 생산
4. 새 팩 ingest 후 다시 현재 문서로 복귀

---

## 9. 작품별 권장 기본 묶음

### 9.1 `망국 황자는 조선을 산다` 류 작품

핵심 3팩:

- `KR_ROYAL_ASSETS_EXILE`
- `EU_FINANCE_PORTS`
- `KR_COLONIAL_ASSET_TAKEOVER`

보조 4팩:

- `BANKING_FX`
- `MARINE_INSURANCE`
- `RAIL_INFRA`
- `SH_KR_MANCHURIA-HUBS`

핵심 질문:

- 주인공은 어떤 명분으로 조선을 떠나는가
- 유럽에서 어떤 금융/해운/보험 네트워크를 먼저 장악하는가
- 식민지 자산을 어떤 법적/금융적 구조로 사들이는가

### 9.2 조선 정치 중심 대체역사

이 경우 현재 문서보다 `alt_history_material_json_harness.md`의 조선 관직/당파 스키마 비중이 더 크다.
다만 그래도 DB 조회는 먼저 한다.

---

## 10. 최소 실행 예시

### 10.1 카탈로그 확인

```powershell
python -X utf8 test_material/query_material_bank.py catalog `
  --source "AH-" `
  --limit 50
```

### 10.2 핵심 3팩 번들

```powershell
python -X utf8 test_material/query_material_bank.py bundle --source "KR_ROYAL_ASSETS_EXILE" --with-meta
python -X utf8 test_material/query_material_bank.py bundle --source "EU_FINANCE_PORTS" --with-meta
python -X utf8 test_material/query_material_bank.py bundle --source "KR_COLONIAL_ASSET_TAKEOVER" --with-meta
```

### 10.3 보조 조회

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --keyword "조선은행,동양척식,로테르담,재보험,철도,광산" `
  --year-start 1905 `
  --year-end 1938 `
  --limit-events 12 `
  --limit-npcs 8 `
  --limit-crises 6 `
  --limit-sector-chains 6 `
  --limit-market-data 10
```

---

## 11. 한 줄 요약

**대체역사 작품은 먼저 DB에서 `AH-*` 재료를 묶고, 그 source_manifest를 기준으로 `Phase 0 -> TR -> BI`를 준비한다.**
DB가 비어 있지 않은데 기억과 상상으로 역사 뼈대를 다시 만드는 것은 금지다.
