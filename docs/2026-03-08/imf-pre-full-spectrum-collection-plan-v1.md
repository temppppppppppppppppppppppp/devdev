# IMF 직전~2025 전구간 재료 수집 마스터 플랜 (V1)

> 범위: **1995-01 ~ 2025-12**  
> 목적: IMF 직전부터 현재 조사 구간까지, 섹터/경제/외교/정치/한국 기업 재료를 대량 확보  
> 원칙: **UTF-8 기본 정책 + 순차 실행 + 감리 우선**

---

## 1) UTF-8 기본 정책 (강제)

### 1-1. 저장/읽기 규칙
- 모든 문서/JSON/스크립트는 `UTF-8`로 저장한다.
- PowerShell 읽기 시 항상 `-Encoding utf8` 사용.
- Python 읽기/쓰기 시 항상 `encoding="utf-8"` 명시.
- DB 적재 전 JSON은 UTF-8 디코딩 테스트를 통과해야 한다.

### 1-2. 금지 규칙
- `ENCODING_BROKEN_TOKEN` 치환 텍스트가 포함된 결과물 적재 금지.
- 인코딩 불명 파일(CP949, ANSI 추정) 혼용 금지.
- 생성과 적재를 병렬 실행 금지.

### 1-3. 사전 검증 명령 (필수)
```powershell
Get-Content -Path <file> -Encoding utf8 | Select-Object -First 20
```
```powershell
@'
from pathlib import Path
p = Path(r"<file>")
t = p.read_text(encoding="utf-8")
print("ok", p, "len", len(t), "broken_token_count", t.count("ENCODING_BROKEN_TOKEN"))
'@ | python -X utf8 -
```

### 1-4. 적재 전 최종 게이트
- `ENCODING_BROKEN_TOKEN` 개수 = `0`
- 필수 키 누락 = `0`
- 상태표 업데이트는 적재 검증 후에만 수행

---

## 2) 수집 범위 정의

## 2-1. 기간
- `1995~2005`: 신규 확장 수집 (IMF 전후 핵심)
- `2006~2025`: 기존 수집분 재검증/보강

## 2-2. 도메인
- 경제/금융/거시지표
- 외교/지정학
- 정치/규제/법률
- 15개 섹터
- 한국 주요 기업(대기업/금융/플랫폼/바이오/방산)

## 2-3. DB 매핑
- 사건형: `events`
- 인물형: `npcs`
- 위기형: `crises`
- 섹터 연결: `sector_chains`
- 수치형: `market_data`

---

## 3) 수집 터미널 설계 (대량)

## 3-1. 시간축 확장 (I-T1~I-T6)
- `I-T1`: 1995~1996 (IMF 직전 징후)
- `I-T2`: 1997~1998 (IMF 충격, 구조조정)
- `I-T3`: 1999~2000 (회복/재편)
- `I-T4`: 2001~2002 (IT 버블 후행, 카드사태 전후)
- `I-T5`: 2003~2004 (신용/가계/내수 구조 변화)
- `I-T6`: 2005~2006 (글로벌 호황/레버리지 전야)
- 최소 목표: 터미널당 `events 40+`

## 3-2. 거시/금융 팩트 (I-F1~I-F8)
- `I-F1`: 금리/환율 월별 (1995~2025)
- `I-F2`: 주가지수 월별 (KOSPI/KOSDAQ/S&P/Nikkei 등)
- `I-F3`: 실업률/성장률/물가 (분기/연)
- `I-F4`: 가계부채/기업부채/신용스프레드
- `I-F5`: 원자재(유가/금/구리/철광석)
- `I-F6`: 부동산(가격/전세가율/거래량/미분양)
- `I-F7`: 암호화폐(2010~2025)
- `I-F8`: 한국 주요기업 시총/재무핵심 (연도말)
- 최소 목표: `market_data 8,000+`

## 3-3. 외교/지정학 (I-G1~I-G8)
- `I-G1`: 한미/북핵/안보축 변화
- `I-G2`: 한중/중국 부상/공급망
- `I-G3`: 한일/통상/기술갈등
- `I-G4`: 러시아/유럽/에너지
- `I-G5`: 중동/원자재/해상물류
- `I-G6`: 글로벌 금융질서(IMF/WB/달러체계)
- `I-G7`: 무역전쟁/제재/수출통제
- `I-G8`: 팬데믹/전쟁/블랙스완
- 최소 목표: `events 280+`

## 3-4. 정치/규제/법률 (I-K1~I-K8)
- 정권별 경제정책, 세제, 노동, 공정거래, 금융소비자, 데이터, 플랫폼, 가상자산
- IMF 이후 규제 전환의 장단기 파급 포함
- 최소 목표: `events 240+`

## 3-5. 섹터 확장 (I-S1~I-S15)
- 기존 15섹터를 1995~2025 전체 구간으로 확장 재수집
- 섹터별 `사건 + 시장수치 + 인물 + 인수 타깃 + 리스크`
- 최소 목표(섹터당):
- `events 30+`, `npcs 8+`, `sector_chains 6+`, `market_data 30+`

## 3-6. 한국 기업 전수 재료 (I-C1~I-C12)
- 대기업집단/금융지주/플랫폼/바이오/방산/물류/유통
- 기업별: 지배구조, M&A, 위기, 재무변곡, 정책 민감도
- 최소 목표: `events 360+`, `npcs 120+`

---

## 4) 순차 실행 계획 (중요)

## 4-1. 단계
1. 문서/JSON 생성
2. UTF-8 검증
3. 스키마 검증
4. DB 적재
5. 건수/품질 감리
6. 상태 문서 반영

## 4-2. 실행 원칙
- 한 번에 한 소스만 처리 (`I-T1` 완료 후 `I-T2`)
- 생성/적재 병렬 금지
- 실패 시 다음 소스로 진행 금지

---

## 5) 산출물 규격

## 5-1. JSON 파일명
- `test_material/json_outputs/<source>-<slug>.json`
- 예: `i-t2-imf-crisis-1997-1998.json`

## 5-2. 필수 키
- events: `id,source,date_start,date_end,event_name,detail,category,sectors,region,market_data,opportunity,strategy,return_estimate,capital_needed,risk,connected_events,narrative_use,tension,tags,confidence`
- npcs: `id,source,name,role,sector,real_model,personality,relation_to_protag,first_appearance,arc,detail,tags`
- crises: `id,source,crisis_type,period,trigger_event,severity,detail,resolution,real_case,narrative_function,placement_after,tags`
- sector_chains: `id,source,from_sector,to_sector,synergy_score,reason,capital_needed,real_example`
- market_data: `source,date,indicator,value,unit,note`

---

## 6) 감리 체크리스트

## 6-1. 인코딩 감리
- 파일 UTF-8 읽기 성공
- `ENCODING_BROKEN_TOKEN` 포함 여부 = 0

## 6-2. 정합성 감리
- 상태표 `v` ↔ DB 건수 > 0
- 기간 포맷 통일 (`YYYY-MM` 우선)
- 중복 `id` 없음

## 6-3. 품질 감리
- 템플릿 반복률 과도 금지
- `detail` 최소 길이 기준:
- events `120+` / crises `140+` / npcs `100+`
- `connected_events` 공백률 40% 이하 목표

---

## 7) 우선 실행 순서 (추천)

1. `I-T1~I-T6` (시간축 뼈대 먼저)
2. `I-F1~I-F8` (팩트 바닥 깔기)
3. `I-G1~I-G8`, `I-K1~I-K8`
4. `I-S1~I-S15`
5. `I-C1~I-C12`
6. 통합 감리 + 재적재

---

## 8) 완료 기준
- 기간 커버리지: `1995~2025` 연속
- 핵심 도메인 5개(섹터/경제/외교/정치/기업) 모두 `v`
- UTF-8 위반 0건
- DB 적재 누락 0건
- 감리 리포트 1건 이상 생성

---

## 9) 운영 메모
- 이번 확장은 “재료 하나 추가”가 아니라 “시대 확장 팩”으로 취급한다.
- 기존 `2006~2025` 자산은 유지하되, `1995~2005`를 선행 축으로 붙여 인과관계를 강화한다.
- 후배 작업 시에는 본 문서를 오더 기준으로 사용하고, 상태표 반영은 검증 후 진행한다.

---

## 10) 2Pass 감리 프로토콜 (강제)

## 10-1. Pass-1 (구조/인코딩/스키마)
1. UTF-8 읽기 성공 여부
2. `ENCODING_BROKEN_TOKEN` = 0
3. 필수 키 누락 = 0
4. DB 적재 건수 > 0 (`v` 예정 소스)
5. 날짜 포맷 일관성(`YYYY-MM` 우선)

## 10-2. Pass-2 (품질/재사용성)
1. `detail` 최소 길이 기준 충족
2. 템플릿 반복률 점검(동일 detail 과다 금지)
3. `connected_events` 링크 품질 점검
4. 상태표 `v`와 DB 건수 교차검증
5. 감리 로그 문서 1건 생성

## 10-3. 실패 처리
- Pass-1 실패: 적재 금지, 문서/JSON 수정 후 재검사
- Pass-2 실패: 적재 유지 가능하나 `운영사용 금지` 플래그 부여 후 보강
- 두 패스 모두 통과 시에만 “완료” 판정

---

## 11) 순차 배치 실행표 (운영용)

| 배치 | 소스 범위 | 목표 테이블 | 완료 조건 |
|---|---|---|---|
| B1 | I-T1~I-T6 | events | 소스별 40건+, Pass-1 통과 |
| B2 | I-F1~I-F8 | market_data (+events 보조) | 총 8,000행+, Pass-1 통과 |
| B3 | I-G1~I-G8 | events | 총 280건+, Pass-1 통과 |
| B4 | I-K1~I-K8 | events | 총 240건+, Pass-1 통과 |
| B5 | I-S1~I-S15 | events/npcs/sector_chains/market_data | 섹터별 최소치 달성 |
| B6 | I-C1~I-C12 | events/npcs | 기업별 핵심 축 충족 |
| B7 | 통합 감리 | 전 테이블 | Pass-2 통과 + 상태표 반영 |

---

## 12) 감리 이력 (운영 로그)

| 일시 | 대상 문서 | Pass-1 | Pass-2 | 보정 사항 |
|---|---|---|---|---|
| 2026-03-08 17:23 | `imf-pre-full-spectrum-collection-plan-v1.md` | v | v | 1-3 검증 코드의 토큰 표기를 `ENCODING_BROKEN_TOKEN`으로 통일 |
| 2026-03-08 18:05 | `i-t1-imf-prelude-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 18:40 | `i-t2-imf-crisis-core-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, 한글/UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 19:10 | `i-t3-recovery-restructuring-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, 한글/UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 19:45 | `i-t4-it-bubble-aftershock-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, 한글/UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 19:45 | `i-t5-credit-domestic-rebalance-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, 한글/UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 19:45 | `i-t6-global-boom-prelude-*.json` 4종 | v | v | `events 40 / npcs 12 / crises 5 / market_data 64`, 한글/UTF-8·필수키·길이 기준 통과 |
| 2026-03-08 20:15 | `i-f1~i-f8` 시장데이터 8종 | v | v | `market_data 10,620행`, 한글/UTF-8·필수키·row_count 정합성 통과 |
| 2026-03-08 20:40 | `i-g1~i-g8` 외교/지정학 8종 | v | v | `events 280건`, 한글/UTF-8·필수키·길이·연결무결성 통과 |
| 2026-03-08 21:00 | `i-k1~i-k8` 정치/규제 8종 | v | v | `events 240건`, 한글/UTF-8·필수키·길이·연결무결성 통과 |
| 2026-03-08 21:20 | `i-s01~i-s15` 섹터 15종 | v | v | `events 450 / npcs 120 / sector_chains 90 / market_data 540`, 한글/UTF-8·필수키·길이·연결무결성 통과 |
| 2026-03-08 21:35 | `i-c1~i-c12` 기업 12종 | v | v | `events 360 / npcs 120`, 한글/UTF-8·필수키·길이·연결무결성 통과 |
| 2026-03-08 21:45 | `i-*` 통합 감리/적재 드라이런 | v | v | `events 1,570 / npcs 312 / crises 30 / sector_chains 90 / market_data 11,544`, PK 중복 0, `ingest_i_materials.py` 준비 |
| 2026-03-08 18:24 | `i-*` 통합 실적재(`--apply`) | v | v | DB 반영 확인: `events 1,570 / npcs 312 / crises 30 / sector_chains 90 / market_data 11,544`, `source LIKE 'I-%'` 기준 누락 0 |
| 2026-03-08 18:31 | `i-*` UTF-8 텍스트 복원 + 재적재 | v | v | `repair_i_materials_utf8.py`로 75개 재료 보정 후 재적재 완료, DB 품질검증(`?`/`\uFFFD`/`ENCODING_BROKEN_TOKEN`) 모두 0 |
| 2026-03-08 18:40 | `i-*` Pass2 정제 + 재적재 | v | v | `enhance_i_materials_pass2.py`로 전량 문장 정제(이벤트 반복률 0%, 위기 반복률 0%, 인물 반복률 0.96%), 날짜 역전 0, 연결 무결성 100%, DB 재적재 완료 |
| 2026-03-08 18:42 | `i-*` Pass2 미세보정 + 재적재 | v | v | 인물 detail 잔여 중복 3건 제거 후 재적재, `events/npcs/crises detail` 반복률 모두 0%, 인코딩 이상 0, 건수 유지(`1,570/312/30/90/11,544`) |
| 2026-03-08 19:05 | `I0` 브리지 팩 생성 + 적재 | v | v | `i-i0-master-bridge-pack-1995-2025.json` 생성·검증·적재 완료(`events 24 / npcs 12 / crises 6 / sector_chains 10 / market_data 120`), 인코딩 이상 0 |
| 2026-03-08 19:32 | `json_outputs` 전수 UTF-8 감리 + 재적재 | v | v | `repair_json_outputs_utf8.py`로 40개 깨짐 파일 보정, `reingest_json_outputs.py`로 전수 재적재 완료(`events 3,315 / npcs 662 / crises 212 / sector_chains 168 / market_data 18,322`) |
