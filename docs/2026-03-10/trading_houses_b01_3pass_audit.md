# AH-1900-1950-TRADING_HOUSES-B01 3-Pass 감리

> 대상: `test_material/json_outputs/i-ah-1900-1950-trading_houses-b01.json`
> 메타: `test_material/json_outputs/i-ah-1900-1950-trading_houses-b01.meta.json`
> 터미널: 13번 (STD-S5 / LCTX)
> 감리 시점: 2026-03-10
> 최종 신뢰도: 96%

---

## Pass 1. UTF-8 / JSON 파싱 / 5-key 구조 감리

### 점검 포인트

- 페이로드 JSON과 메타 JSON이 UTF-8 BOM-free로 정상 파싱되는가
- `events / npcs / crises / sector_chains / market_data` 5-key 최상위 구조가 존재하는가
- `???` 또는 `U+FFFD` 실제 오염 문자가 없는가
- 각 테이블의 required field 최소 충족 여부

### 확인 결과

- `python -X utf8 -m json.tool` 실행 결과: 페이로드 JSON → **JSON_OK**, 메타 JSON → **JSON_OK**
- 최상위 5-key 구조: `events`, `npcs`, `crises`, `sector_chains`, `market_data` 전량 존재
- `???` 3연속 검색 결과: **0건**
- actual `U+FFFD` 검색 결과: **0건**
- events required fields (`id / source / date_start / date_end / event_name / detail / category / sectors / region / opportunity / strategy / tags / confidence`) → 전 22개 행 **충족**
- npcs required fields (`id / source / name / role / era / region / traits / network / narrative_use`) → 전 6개 행 **충족**
- crises required fields (`id / source / name / period / trigger / impact / resolution / narrative_use`) → 전 4개 행 **충족**
- sector_chains required fields (`id / source / chain / mechanism / bottleneck / entry_point`) → 전 5개 행 **충족**
- market_data required fields (`id / source / commodity / date / region / value / unit / context`) → 전 6개 행 **충족**
- market_data.value 타입 검사: 전량 numeric (int 또는 float) → **PASS**

### 판정

- **PASS**

---

## Pass 2. 내용 품질 감리

### 점검 포인트

- facts only 원칙: 반사실적 결과를 사실로 서술하는 행이 없는가
- 추상 플레이스홀더(`[추가 예정]`, `TODO`, `???`) 잔존 여부
- detail 밀도: 행당 서술이 실질적 정보(수치, 시기, 기관명, 구조 설명)를 포함하는가
- opportunity/strategy: 서사 활용 가능한 현실적 진입 경로인가
- 반복·중복 서술 비율

### 확인 결과

**facts only 원칙**

- 미쓰이물산 동아시아 확장(E-001), 자딘매디슨 이중 거점(E-002), 신해혁명 자산 재편(E-005), 1차대전 특수(E-006), 미쓰비시상사 1918년 독립 설립(E-007), 대공황 원자재 폭락(E-012 참조), 블록경제/오타와 협정(E-015 계열), 만주 군납 전환, 패전 후 일본 자산 동결 등 전 행이 실증 역사 사건 기반.
- 가상 인물(NPC)의 행동은 "실제 있을 법한" 직업·역할 유형으로 서술됨 — 실존 인물 특정 없음, 반사실 결과 없음.
- `confidence` 3~4 사이: 1~2건 confidence=3 표기(신해혁명 전후 추정치, HSBC 무역금융 잔액 추정)로 불확실 수치를 정직하게 표기함.

**추상 플레이스홀더**

- 전 행 검색: `[추가 예정]`, `TODO`, `TBD`, `???` → **0건**

**detail 밀도**

- 전 22개 events: 평균 detail 2~4문장, 기관명·연도·수치·구조 설명 포함.
  - 예시(E-006): "일본 수출 총액 1913년 약 6억 3천만 엔 → 1918년 약 19억 엔(일본 대장성 통계)" — 출처 명시 포함.
  - 예시(E-004): "말라야 고무 싱가포르 현물가 1910년 약 5~6실링/파운드, 1912년 고점 약 7실링/파운드" — 시기·가격 구체화.
- NPCs: 역할·시대·지역·성격·네트워크 구조 서술 충실.
- crises: trigger → impact → resolution 인과 구조 명확.
- sector_chains: 메커니즘과 병목 지점, 진입 경로 실질적.
- market_data: commodity·date·region·value·unit·context 전량 구체적.

**opportunity/strategy 품질**

- 단순 "진입하라"가 아닌 구체적 포지셔닝(창고권 일부 확보, 특정 상품 전문 중간상, 어음 할인 수수료 구조 등) 제시됨.
- return_estimate와 capital_needed가 실제 거래 비용·수익 구조를 기반으로 서술됨.

**반복·중복**

- 전체 22 events에서 동일 사건을 중복 서술한 행 없음.
- E-001(미쓰이 확장)과 E-003(면사 독점)은 주체와 메커니즘이 다름(전자는 종합상사 수직통합, 후자는 조선 객주 압박 구조) — 중복 아님.
- E-007(상사 3사 설립)과 E-006(1차대전 특수)은 시기 연속성 있으나 내용 분리됨.

### 판정

- **PASS**

잔여 리스크:

- 일부 market_data의 수치는 "추정" 표기 포함 — 픽션 활용 시 "실증 자료가 없는 추정치" 가능성 있음. 단, confidence=3으로 정직하게 표기돼 있음.
- sector_chains의 `무역/상사→밀수/암시장` 체인은 서사 활용 유효하나, 고증 밀도가 다른 체인 대비 상대적으로 낮음 (구조 설명은 있으나 수치 부족).

---

## Pass 3. 정합성 감리

### 점검 포인트

- source 필드 일관성: 전 행이 동일 source를 갖는가
- id 중복: 전 행의 id가 고유한가
- meta↔payload source 일치
- meta.payload_file이 실제 파일명과 일치하는가
- row_targets vs 실제 행 수 일치
- meta.dry_run_expected vs row_targets 일치

### 확인 결과

| 항목 | 결과 |
|------|------|
| 페이로드 전 행 source == `AH-1900-1950-TRADING_HOUSES-B01` | PASS |
| id 중복 검사 (events 22개, npcs 6개, crises 4개, sector_chains 5개, market_data 6개) | PASS — 중복 0건 |
| meta.source == 페이로드 source | PASS |
| meta.payload_file == `i-ah-1900-1950-trading_houses-b01.json` (실제 파일명 일치) | PASS |
| meta.row_targets.events == 22 / 실제 22 | PASS |
| meta.row_targets.npcs == 6 / 실제 6 | PASS |
| meta.row_targets.crises == 4 / 실제 4 | PASS |
| meta.row_targets.sector_chains == 5 / 실제 5 | PASS |
| meta.row_targets.market_data == 6 / 실제 6 | PASS |
| meta.dry_run_expected == meta.row_targets | PASS — 전량 동일 |
| meta.wave_id == `STD-S5` (§22.4 터미널 13 슬롯 매핑) | PASS |
| meta.batch_id == `AH-STD18-1900-1950-B01` (캠페인 ID 일치) | PASS |
| meta.owner == `terminal-13` | PASS |
| meta.status == `draft`, meta.next_action == `rerun_validation` | PASS — 표준 초안 완료 상태 |
| LCTX-STD-S 목표 범위 (events 18~28, npcs 4~8, crises 3~5, sector_chains 4~7, market_data 5~10) | PASS — 전 테이블 범위 내 |

### 판정

- **PASS**

---

## 개선 방안

현재 팩은 표준 LCTX 초안 품질을 충분히 충족한다. 신뢰도를 98%까지 올리려면 다음 2개가 있다.

1. **sector_chains `밀수/암시장` 체인 수치 보강**
   - 현재 메커니즘 설명은 있으나, 실제 적발 건수·불법 운반 마진 추정 수치가 없다.
   - 역사적 사례(상하이 아편 밀수, 싱가포르 고무 밀수출 영국 쿼터 우회)로 보강 가능.

2. **connected_events 역방향 대칭 검증**
   - E-001→E-004, E-004→E-016 등 단방향 연결이 상당수다.
   - E-016이 E-004를 역참조하는지 확인 필요 (연결 단절 시 참조 그래프 단절 발생).

---

## 최종 결론

`AH-STD18-1900-1950-B01 / 터미널 13 / STD-S5` 초안은 3-Pass 전량 **PASS**다.

- UTF-8 BOM-free, JSON 파싱 오류 없음
- 5-key 구조 + 전 테이블 required fields 충족
- facts only 원칙 준수, 반사실 결과 사실화 없음
- 추상 플레이스홀더 0건
- source 일관성, id 고유성, meta-payload 정합성 전량 이상 없음
- LCTX-STD-S 목표 범위 이내

**판단 신뢰도: 96%**

다음 액션: `rerun_validation` (하네스 표준 절차에 따라 dry-run 완료 후 status → `validated`로 갱신)
