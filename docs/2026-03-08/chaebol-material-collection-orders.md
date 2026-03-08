# 재벌물 재료 수집 — 터미널 오더 전량

> **목적**: Block 설계 이전 단계. 선택지를 최대한 모은다.
> **저장**: SQLite DB (`material_bank.db`)
> **원칙**: 많이 모아서 나중에 고른다. 지금은 수집만.

---

## 0. DB 스키마

```sql
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,           -- 'T1-001', 'S2-E-003' 등
    source TEXT NOT NULL,          -- 터미널 ID (T1, S2, N2 등)
    date_start TEXT,               -- 'YYYY-MM' 또는 'YYYY-MM-DD'
    date_end TEXT,                 -- 종료일 (장기 사건)
    event_name TEXT NOT NULL,      -- 한 줄 제목
    detail TEXT,                   -- 상세 설명 (3~10줄)
    category TEXT,                 -- JSON 배열: ["ECON","INTL"]
    sectors TEXT,                  -- JSON 배열: ["에너지/원유","조선/해운"]
    region TEXT,                   -- KR / US / EU / CN / JP / GLOBAL
    market_data TEXT,              -- 구체적 수치 (유가, 환율, 주가 등)
    opportunity TEXT,              -- 투자/사업 기회 설명
    strategy TEXT,                 -- 매수/공매도/인수/창업 등
    return_estimate TEXT,          -- 예상 수익률
    capital_needed TEXT,           -- 필요 자본
    risk TEXT,                     -- 리스크/흔들리는 구간
    connected_events TEXT,         -- JSON 배열: 연관 사건 ID
    narrative_use TEXT,            -- 소설에서 어떤 장면으로 쓸 수 있는지
    tension TEXT,                  -- 긴장/갈등 요소
    tags TEXT,                     -- JSON 배열: 자유 태그
    confidence INTEGER DEFAULT 3, -- 팩트 신뢰도 1~5 (LLM 자체 평가)
    used INTEGER DEFAULT 0        -- Block에 사용됨 여부
);

CREATE TABLE IF NOT EXISTS npcs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT,                     -- 조력자/적대자/중립/가문
    sector TEXT,                   -- 주 활동 섹터
    real_model TEXT,               -- 실존 인물 모델 (참고용)
    personality TEXT,              -- 성격 요약
    relation_to_protag TEXT,       -- 주인공과의 관계
    first_appearance TEXT,         -- 추천 첫 등장 시기
    arc TEXT,                      -- 인물 변화 곡선
    detail TEXT,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS crises (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    crisis_type TEXT,              -- market_fail/legal/family/betrayal/political/health/butterfly
    period TEXT,                   -- 추천 배치 시기
    trigger_event TEXT,            -- 트리거 사건 ID (events 테이블 참조)
    severity INTEGER,              -- 1~10
    detail TEXT,
    resolution TEXT,               -- 해결 방식
    real_case TEXT,                -- 실제 사례
    narrative_function TEXT,       -- 성장/각성/겸손/결속
    placement_after TEXT,          -- 어떤 섹터 성공 직후에 넣을지
    tags TEXT
);

CREATE TABLE IF NOT EXISTS sector_chains (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    from_sector TEXT,
    to_sector TEXT,
    synergy_score INTEGER,         -- 1~5
    reason TEXT,                   -- 시너지 이유
    capital_needed TEXT,           -- 진출 시 필요 자본
    real_example TEXT              -- 실제 재벌 사례
);

CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    date TEXT NOT NULL,             -- YYYY-MM
    indicator TEXT NOT NULL,        -- WTI, KOSPI, USD_KRW, BTC, S&P500 등
    value REAL,
    unit TEXT,                      -- USD, KRW, point, %
    note TEXT
);

CREATE INDEX idx_events_date ON events(date_start);
CREATE INDEX idx_events_sector ON events(sectors);
CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_market_date ON market_data(date, indicator);
```

---

## 1. 터미널 오더 — Wave 1 (전부 동시 투입)

---

### T1: 시간축 2006~2008

```
## 역할
너는 금융·경제·정치 전문 리서치 애널리스트다.

## 과제
2006년 1월부터 2008년 12월까지 한국 및 세계에서 벌어진 주요 사건을 빠짐없이 수집해줘.
이 재료는 회귀 재벌물 소설에 쓸 "역사적 사건 데이터베이스"를 구축하기 위한 것이다.
주인공은 2006년에 자본금 20억으로 시작하는 투자자/사업가다.

## 범위 (이 기간에 해당하는 것 전부)
- 유가 변동 (이란, 나이지리아, OPEC, 투기)
- 미국 부동산/서브프라임 위기의 전개 과정 (월별로 상세히)
- 리먼 브라더스 파산과 글로벌 금융위기
- 한국 경제 (환율, 주가, 부동산, 정권 교체)
- 중국 경제 성장 (올림픽, WTO 이후)
- 원자재 슈퍼사이클 (구리, 철강, 금)
- IT/기술 (아이폰 출시 2007, 안드로이드)
- 한국 정치 (대선 2007, 정권교체)
- 기업 M&A (한국 및 글로벌)
- 암호화폐 태동기 (비트코인 백서 2008.10)

## 출력 형식 — JSON 배열

각 사건을 아래 형식으로 출력해줘. 반드시 JSON으로.

{
  "id": "T1-001",
  "date_start": "2006-01",
  "date_end": "2006-03",
  "event_name": "이란 핵위기 고조, UN 제재안 논의",
  "detail": "이란이 우라늄 농축을 재개하면서 국제 원유 시장에 공급 불안...(3~10줄로 상세하게)",
  "category": ["INTL", "ECON"],
  "sectors": ["에너지/원유"],
  "region": "GLOBAL",
  "market_data": "WTI 2006.01 $63.12 → 2006.04 $69.50 → 2006.07 $77.03",
  "opportunity": "WTI 선물 롱. 이란 제재가 현실화되면 유가 $70+ 확정적",
  "strategy": "선물 롱 + 에너지 ETF",
  "return_estimate": "+40% (3개월)",
  "capital_needed": "5억 (레버리지 3배 시 15억 효과)",
  "risk": "2006.10 일시 하락 -15%, 레버리지 마진콜 위험",
  "connected_events": ["T1-005"],
  "narrative_use": "모두가 이란을 모를 때 홀로 원유에 베팅하는 장면",
  "tension": "가족이 비웃는 상황에서 확신을 지키는 갈등",
  "tags": ["원유", "중동", "첫투자"],
  "confidence": 4
}

## 요구사항
- **최소 50개, 80개 권장** — 많을수록 좋다
- 큰 사건뿐 아니라 **소소하지만 투자 기회가 있는 사건**도 포함
- market_data에 가능한 **실제 수치** 포함
- 날짜순 정렬
- 한국 사건 최소 15개 포함
- 사건 간 connected_events로 인과관계 연결
```

---

### T2: 시간축 2008~2012

```
(T1과 동일 형식, 아래만 변경)

## 과제
2008년 1월부터 2012년 12월까지

## 범위
- 금융위기 절정과 회복 과정 (2008~2009)
- 각국 양적완화 (QE1, QE2)
- 유럽 재정위기 (그리스, PIIGS)
- 중국 4조 위안 부양책
- 한국 부동산 정책 변화
- 스마트폰 혁명 (아이폰3G→4S, 갤럭시S)
- 소셜미디어 부상 (페이스북, 트위터)
- 한국 IT (카카오톡 2010, 네이버)
- 아랍의 봄 (2011)
- 일본 대지진 + 후쿠시마 (2011.03)
- 비트코인 초기 거래 (2010 피자, 2011 $1→$30)
- 원자재 변동 (유가, 금값 $1900 피크 2011)
- 한국 정치 (이명박 정부, 4대강)
- K-pop 글로벌 진출 시작 (소녀시대, 빅뱅)

id 접두사: "T2-"
최소 50개
```

---

### T3: 시간축 2013~2018

```
(T1과 동일 형식, 아래만 변경)

## 과제
2013년 1월부터 2018년 12월까지

## 범위
- 아베노믹스 (2013)
- 중국 시진핑 집권 + 일대일로
- 한국 바이오 붐 (셀트리온, 삼성바이오)
- 세월호 (2014.04) 정치/사회적 영향
- 유가 폭락 (2014 하반기, $100→$30)
- 미국 금리 인상 시작 (2015.12)
- 브렉시트 국민투표 (2016.06)
- 트럼프 당선 (2016.11)
- 박근혜 탄핵 (2016.12) + 문재인 정부
- 암호화폐 광풍 (2017, BTC $1000→$20000)
- 반도체 슈퍼사이클 (2016~2018, 삼성 영업이익 50조)
- 미중 무역전쟁 시작 (2018)
- 한국 부동산 (규제 시작, 서울 집값)
- 넷플릭스/OTT 한국 진출
- 테슬라 Model 3 (2017)
- 4차 산업혁명 담론
- 한국 최저임금 급등 (2018)
- 남북 정상회담 (2018.04)

id 접두사: "T3-"
최소 50개
```

---

### T4: 시간축 2019~2025

```
(T1과 동일 형식, 아래만 변경)

## 과제
2019년 1월부터 2025년 5월까지

## 범위
- 미중 무역전쟁 격화 + 화웨이 제재
- 코로나19 팬데믹 (2020.01~)
- 각국 초대형 양적완화 + 제로금리
- 주식 광풍 (동학개미, 로빈후드, GME)
- 암호화폐 기관 투자 시대 (BTC $60000+)
- 부동산 폭등 + 전세 대란
- 백신 개발 경쟁 (모더나, 화이자)
- 전기차 전쟁 (테슬라, 현대, BYD)
- 배터리 3사 (LG, 삼성SDI, SK온)
- 러시아-우크라이나 전쟁 (2022.02)
- 인플레이션 + 금리 급등 (2022~2023)
- 실리콘밸리은행 파산 (2023.03)
- ChatGPT/AI 혁명 (2022.11~)
- 엔비디아 폭등
- 한국 반도체 수출 규제 이슈
- 일본 엔저 (2022~2024)
- 한국 정치 (윤석열 정부, 비상계엄)
- 방산 수출 호황 (K-방산)
- 쿠팡/네이버/카카오 플랫폼 전쟁
- NFT 붐과 붕괴
- 메타버스 붐과 붕괴
- 2차전지 소재 전쟁 (리튬, 니켈)

id 접두사: "T4-"
최소 60개 (기간이 길고 사건이 밀집)
```

---

### S1: 원자재 클러스터 (에너지 + 철강/소재 + 조선/해운)

```
## 역할
너는 원자재·에너지·중공업 전문 애널리스트다.

## 과제
2006~2025년 [에너지/원유], [철강/소재], [조선/해운] 3개 섹터의
투자/사업 기회를 빠짐없이 수집해줘.

## 각 섹터별로 아래 내용을 조사:

### A. 대형 투자 기회 (섹터당 최소 8개)

{
  "id": "S1-에너지-001",
  "sector": "에너지/원유",
  "period": "2006.01~2008.07",
  "event_name": "유가 슈퍼사이클",
  "detail": "(5~10줄 상세)",
  "market_data": "WTI 월별 가격 나열",
  "strategy": "선물 롱, 3배 레버리지, $120 부근 익절",
  "return_estimate": "+130%",
  "capital_needed": "10억",
  "risk": "2006.10 -15% 일시하락, 마진콜 위험",
  "connected_sectors": ["조선/해운 — LNG선 수주", "철강 — 해양플랜트 강재"],
  "tags": ["유가", "슈퍼사이클", "OPEC"],
  "confidence": 4
}

### B. 기업 인수 기회 (섹터당 최소 3개)

{
  "id": "S1-에너지-MA-001",
  "sector": "에너지/원유",
  "target_type": "중소 정유사 또는 에너지 트레이딩 회사",
  "real_model": "SK이노베이션 초기, 쿤룬에너지",
  "timing": "2009 금융위기 저점",
  "rationale": "유가 폭락으로 기업가치 1/3, 회복 시 3배",
  "capital_needed": "500억",
  "growth_scenario": "트레이딩 → 정유 → 신재생 (2015~)",
  "confidence": 3
}

### C. 섹터별 핵심 수치 타임라인 (market_data 테이블용)

{
  "indicator": "WTI",
  "data": [
    {"date": "2006-01", "value": 63.12, "unit": "USD"},
    {"date": "2006-06", "value": 73.93, "unit": "USD"},
    ...
  ]
}

### D. 섹터 간 연결고리 (sector_chains 테이블용)

{
  "from_sector": "에너지/원유",
  "to_sector": "조선/해운",
  "synergy_score": 5,
  "reason": "유가 상승 → LNG 수요 → LNG선 발주 폭증",
  "real_example": "현대중공업 2006~2007 수주 잔량 사상 최대"
}

## 요구사항
- 사건 최소 24개 (섹터당 8개 × 3섹터)
- 인수 기회 최소 9개 (섹터당 3개)
- market_data 주요 지표 월별 (가능한 범위에서)
- 섹터 간 연결고리 최소 6개
- 전부 JSON 형식
```

---

### S2: 금융 클러스터 (금융/은행 + 부동산/건설 + 암호화폐)

```
(S1과 동일 구조, 아래만 변경)

## 섹터
[금융/은행], [부동산/건설], [암호화폐/블록체인]

## 특별 주의
- 금융: 서브프라임 CDS/MBS 공매도 전략을 월별로 상세히
- 부동산: 한국 아파트값 변곡점 (강남, 전국), 정책 변화
- 암호화폐: BTC 가격 + 주요 이벤트 (해킹, 규제, ETF) 월별

id 접두사: "S2-금융-", "S2-부동산-", "S2-암호화폐-"
```

---

### S3: 테크 클러스터 (IT/소프트웨어 + 반도체 + 통신/플랫폼)

```
(S1과 동일 구조)

## 섹터
[IT/소프트웨어], [반도체], [통신/플랫폼]

## 특별 주의
- IT: 모바일 혁명(2007~2012), 클라우드(2015~), AI(2022~) 3대 웨이브
- 반도체: 메모리 사이클(호황/불황 반복), 파운드리 전쟁, AI칩
- 통신: 3G→4G→5G 전환점, 카카오/네이버 성장 궤적
- 창업/투자 기회 (초기 투자 → 대형 수익)

id 접두사: "S3-IT-", "S3-반도체-", "S3-통신-"
```

---

### S4: 산업 클러스터 (바이오/제약 + 자동차/모빌리티 + 항공/방산)

```
(S1과 동일 구조)

## 섹터
[바이오/제약], [자동차/모빌리티], [항공/방산]

## 특별 주의
- 바이오: 셀트리온/삼성바이오 성장, 코로나 백신, 바이오시밀러
- 자동차: 현대차 성장, 테슬라 충격, 전기차 전환, 배터리 3사
- 방산: K-방산 수출 2022~ (폴란드, UAE 등)

id 접두사: "S4-바이오-", "S4-자동차-", "S4-방산-"
```

---

### S5: 소비 클러스터 (엔터/미디어 + 유통/이커머스 + 식품/소비재)

```
(S1과 동일 구조)

## 섹터
[엔터/미디어], [유통/이커머스], [식품/소비재]

## 특별 주의
- 엔터: K-pop 글로벌화 (SM/YG/JYP/HYBE), OTT(넷플릭스→티빙), 게임(넥슨/크래프톤)
- 유통: 백화점 → 이커머스 전환 (쿠팡, SSG, 마켓컬리)
- 식품: 프랜차이즈(치킨/카페), 글로벌 진출(CJ, 삼양), K-푸드

id 접두사: "S5-엔터-", "S5-유통-", "S5-식품-"
```

---

### N1: 인물 재료

```
## 과제
재벌물에 쓸 인물 재료를 수집해줘. Block 설계가 아니라 재료 수집이다.

## 세계관
- 주인공: 한시우 (26세, 2024년 사망 후 2006년으로 회귀, 재벌가 막내)
- 가문: 한정호 그룹 (가공) — 회장 한정호, 큰형 한태준, 둘째형 한태민

## 수집 대상

### A. 실존 재벌 가문 구조 분석 (참고용)
- 삼성 이씨, 현대 정씨, SK 최씨, LG 구씨, 롯데 신씨
- 각 가문의 형제 간 경쟁, 경영권 분쟁, 2~3세 승계 패턴
- JSON 형식:

{
  "id": "N1-가문-001",
  "family": "삼성 이씨",
  "structure": "이건희(2세) → 이재용(3세), 형제: 이맹희/이건희 갈등",
  "succession_conflict": "이맹희 vs 이건희 경영권 분쟁 1990년대",
  "key_pattern": "장남이 아닌 차남이 승계, 능력주의",
  "usable_elements": ["형제 간 암투", "장남 vs 막내 구도", "아버지의 시험"]
}

### B. 섹터별 실존 인물 모델 (15개 섹터 × 3~5명)
- 각 섹터의 전설적 인물 (투자자, 기업인, 정치인)
- JSON 형식:

{
  "id": "N1-인물-001",
  "sector": "금융",
  "real_person": "존 폴슨",
  "achievement": "2007 서브프라임 공매도 → $15B 수익",
  "personality": "과묵, 데이터 집착, 역발상",
  "usable_as": "주인공의 롤모델 또는 라이벌",
  "narrative_role": "적대자 — 같은 기회를 노리는 해외 헤지펀드 매니저"
}

### C. 한국 금융/재계 주요 인물 유형
- PB (프라이빗 뱅커), 증권사 애널리스트, 기업 사냥꾼, 로비스트
- 검찰/국세청 인물, 정치인, 기자
- 각 유형의 행동 패턴, 말투, 동기

## 요구사항
- 가문 분석 최소 5개
- 섹터별 인물 최소 45명 (15×3)
- 한국 재계 인물 유형 최소 10개
- 전부 JSON
```

---

### N2: 위기/실패 재료

```
## 과제
재벌물 주인공이 겪을 수 있는 위기/실패 사례를 수집해줘.
실제 한국 재벌이 겪은 위기를 기반으로 소설 재료를 만든다.

## 위기 유형 7가지

1. **시장 예측 실패** — 미래 지식이 있어도 디테일이 다른 경우
2. **법적 위기** — 세무조사, 내부자거래 혐의, 공정위
3. **가문 충돌** — 형들의 방해, 경영권 분쟁, 상속
4. **배신** — 측근, 파트너, 내부 스파이
5. **정치적 압박** — 정권 교체, 국회 청문회, 여론
6. **건강/개인** — 과로, 고독, 인간관계
7. **나비효과** — 주인공의 행동이 역사를 바꿔서 미래 지식이 무효화

## 출력 형식

{
  "id": "N2-001",
  "crisis_type": "legal",
  "title": "국세청 특별세무조사",
  "real_case": "SK 최태원 세무조사 2003, 삼성 이건희 차명계좌 2008",
  "trigger": "급격한 자산 증가로 국세청 관심",
  "severity": 8,
  "detail": "20대 청년이 2년 만에 수백억 자산 형성 → 불법자금 의심...",
  "resolution_options": [
    "정면 대응: 모든 거래 기록 공개 (투명성으로 승부)",
    "정치적 해결: 로비스트를 통한 뒷거래",
    "역이용: 세무조사 결과를 오히려 신뢰도 강화에 활용"
  ],
  "narrative_function": "성장 — 첫 번째 사회적 시련, 투자자에서 기업인으로 전환",
  "placement_after": "금융 섹터 대성공 직후 (자본 500억+ 시점)",
  "duration_blocks": 1,
  "tags": ["법적위기", "세무조사", "국세청"]
}

## 요구사항
- 위기 유형별 최소 3개 = 최소 21개
- 실제 사례(real_case) 반드시 포함
- resolution_options 최소 2개 (선택지)
- severity 1~10 다양하게
- 전부 JSON
```

---

### N3: 섹터 체인 재료

```
## 과제
15개 섹터 간 시너지 관계를 분석해줘.
실제 한국 재벌이 어떻게 사업을 확장했는지 참고.

## 15개 섹터
에너지/원유, 금융/은행, 부동산/건설, IT/소프트웨어, 반도체,
바이오/제약, 엔터/미디어, 유통/이커머스, 자동차/모빌리티,
조선/해운, 철강/소재, 통신/플랫폼, 식품/소비재, 암호화폐/블록체인, 항공/방산

## 출력 1: 시너지 매트릭스 (JSON 배열)

{
  "id": "N3-001",
  "from_sector": "에너지/원유",
  "to_sector": "조선/해운",
  "synergy_score": 5,
  "reason": "유가 상승 → LNG 수요 → LNG선 발주 폭증. 에너지 트레이딩 이익으로 조선소 인수 자금 확보",
  "real_example": "현대중공업그룹: 정유(현대오일뱅크) + 조선 시너지",
  "capital_needed": "3000억+",
  "timing": "유가 저점에서 조선소 인수 (2016)"
}

모든 의미 있는 쌍을 다 뽑아줘. 최소 40개.

## 출력 2: 실제 재벌 확장 경로 분석

{
  "group": "삼성",
  "expansion_path": ["식품(제일제당) → 전자 → 반도체 → 금융 → 바이오 → 방산"],
  "key_decisions": [
    {"year": 1983, "decision": "반도체 진출 선언", "sector": "반도체", "result": "세계 1위"},
    ...
  ],
  "lessons": "초기 자본은 식품/유통에서, 핵심 도약은 기술 투자에서"
}

최소 5개 그룹 (삼성, 현대, SK, LG, 롯데)
```

---

### F1: 팩트체크 — 유가/원자재 (코덱스)

```
2006년 1월부터 2025년 5월까지 아래 지표의 월별 데이터를 조사해줘:

1. WTI 원유 (USD/배럴) — 월말 종가
2. 브렌트 원유 (USD/배럴) — 월말 종가
3. 금 (USD/트로이온스) — 월말 종가
4. 구리 (USD/파운드) — 월말 종가

JSON 형식:
[
  {"date": "2006-01", "WTI": 65.49, "Brent": 63.02, "Gold": 568.75, "Copper": 2.15},
  ...
]

가능한 범위에서 정확한 수치를 제공해줘.
정확하지 않은 경우 approximate라고 표시해줘.
```

---

### F2: 팩트체크 — 환율/주가/금리 (코덱스)

```
2006년 1월부터 2025년 5월까지 아래 지표의 월별 데이터:

1. USD/KRW 환율 — 월말
2. KOSPI 지수 — 월말 종가
3. S&P 500 — 월말 종가
4. 미국 기준금리 (Fed Funds Rate) — 월말
5. 한국 기준금리 — 월말

JSON 형식:
[
  {"date": "2006-01", "USD_KRW": 978, "KOSPI": 1389, "SP500": 1280, "Fed_rate": 4.50, "BOK_rate": 3.75},
  ...
]
```

---

### F3: 팩트체크 — 비트코인/암호화폐 (코덱스)

```
비트코인 가격 히스토리 + 주요 이벤트:

1. BTC/USD 월별 가격 (2010.07~2025.05)
2. 주요 이벤트 (해킹, 규제, 반감기, ETF 승인 등)

JSON 형식:
[
  {"date": "2010-07", "BTC_USD": 0.08, "event": "비트코인 첫 거래소 등장"},
  {"date": "2010-05", "BTC_USD": 0.003, "event": "피자 1만 BTC 거래"},
  ...
]
```

---

## 2. Wave 2 오더 (Wave 1 완료 후)

### X1: 교차 대조 + 통합

```
## 입력
T1~T4 결과 (시간축 JSON 4개)
S1~S5 결과 (섹터 JSON 5개)

## 과제
1. 같은 사건이 T와 S에 중복 등장 → 병합 (더 상세한 쪽 채택, 양쪽 ID 보존)
2. T에만 있는 사건 → 그대로 유지
3. S에만 있는 사건 → events 테이블 형식으로 변환
4. 날짜 불일치 → F1~F3 수치로 교정
5. 통합 events JSON 배열 출력 (고유 ID 재부여: "E-001"~)

출력: 하나의 통합 JSON 파일
```

---

### X2: 자본 시뮬레이션

```
## 입력
X1 통합 사건 DB (또는 T1~T4+S1~S5 원본)

## 과제
20억에서 시작해서 각 투자 기회를 순차 적용했을 때
자본 성장 곡선이 현실적인지 시뮬레이션해줘.

## 규칙
- 한 번에 전 자본을 투입하지 않음 (최대 50%)
- 레버리지는 3배 이하
- 세금/수수료 15% 차감
- 실패 확률 반영 (미래 지식이 있어도 타이밍 오차 ±20%)

## 출력
- 연도별 자본 추정치
- "자본 부족으로 이 기회를 잡을 수 없는 시점" 식별
- 대출/투자유치가 필요한 변곡점
```

---

### X3~X5: (이전 문서의 NPC배치/위기배치/팩트교정과 동일)

---

## 3. 수집 후 DB 적재 스크립트

```python
# load_materials.py — 터미널 결과물을 DB에 적재
import json
import sqlite3

def load_events(db_path, json_path, source_id):
    conn = sqlite3.connect(db_path)
    with open(json_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    for e in events:
        conn.execute('''
            INSERT OR REPLACE INTO events
            (id, source, date_start, date_end, event_name, detail,
             category, sectors, region, market_data,
             opportunity, strategy, return_estimate, capital_needed,
             risk, connected_events, narrative_use, tension,
             tags, confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            e['id'], source_id,
            e.get('date_start'), e.get('date_end'),
            e['event_name'], e.get('detail'),
            json.dumps(e.get('category', []), ensure_ascii=False),
            json.dumps(e.get('sectors', []), ensure_ascii=False),
            e.get('region'),
            e.get('market_data'),
            e.get('opportunity'), e.get('strategy'),
            e.get('return_estimate'), e.get('capital_needed'),
            e.get('risk'),
            json.dumps(e.get('connected_events', []), ensure_ascii=False),
            e.get('narrative_use'), e.get('tension'),
            json.dumps(e.get('tags', []), ensure_ascii=False),
            e.get('confidence', 3)
        ))
    conn.commit()
    print(f"[{source_id}] {len(events)}건 적재 완료")
    conn.close()

# 사용: load_events('material_bank.db', 'T1_result.json', 'T1')
```

---

## 4. 수집 규모 예상

| 터미널 | 대상 | 예상 건수 |
|--------|------|----------|
| T1~T4 | 시간축 사건 | 200~300건 |
| S1~S5 | 섹터 투자기회 | 120~150건 + MA 45건 |
| N1 | 인물 재료 | 50~70명 + 가문 5개 |
| N2 | 위기/실패 | 21~30건 |
| N3 | 섹터 체인 | 40~60쌍 + 재벌 5개 |
| F1~F3 | 시장 데이터 | 월별 230행 × 지표수 |
| **합계** | | **events 400건+, NPCs 60명+, 위기 25건+** |

이 정도 재료가 모이면 Block 50개 만들 때 **선택지가 넘침**.
