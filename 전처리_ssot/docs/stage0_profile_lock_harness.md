# Stage 0 Profile Lock 하네스 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 역할: `profile_lock.json`의 필수 슬롯과 프로파일 해석 계약 고정
> 정식 출력 경로: `treatments/preprocess/{work_id}/profile_lock.json`

---

## 0. 이 문서의 목적

`profile_lock`은 이 작품을 **어떤 장르 프로파일로 읽을지**를 잠그는 파일이다.

이 파일이 없으면 같은 `capital`, `deal_type`, `FinanceHUD`도 작품마다 뜻이 흔들린다.

원칙:

- `primary_profile`은 반드시 1개
- `secondary_profile`은 선택적으로 0~1개
- 3개 이상 혼합 금지

---

## 1. 필수 슬롯

- `primary_profile`
- `secondary_profile`
- `resource_axis`
- `power_axis`
- `control_axis`
- `payoff_axis`
- `failure_axis`
- `hud_interpretation`

권장 추가 슬롯:

- `domain_lines_interpretation`
- `arena_state_interpretation`
- `selection_rationale`

---

## 2. 프로파일 목록

| 프로파일 | 이 작품에서 무엇이 핵심 자원인가 |
| ---- | ---- |
| `business_growth_profile` | 운영권, 현금흐름, 공급망, 반복매출 |
| `investment_market_profile` | 자산, 지분, 가격, 수익률, 레버리지 |
| `entertainment_media_profile` | IP, 팬덤, 편성, 유통, 화제성 |
| `medical_professional_profile` | 집도권, 케이스, 신뢰도, 병원 권한 |
| `office_power_profile` | KPI, 예산, 결재선, 인사권, 프로젝트 통제 |
| `tech_startup_profile` | 제품, 데이터, 특허, 라이선스, 사용자 기반 |
| `urban_power_profile` | 전투력, 길드 자산, 권리, 위상 |

---

## 3. 호환 필드 해석 규칙

`profile_lock.json`은 아래 필드 의미를 작품 단위로 잠가야 한다.

- `resource_axis`
  - 주인공이 실제로 굴릴 수 있는 성장 자원
- `power_axis`
  - 남을 움직이게 만드는 힘
- `control_axis`
  - 주인공을 거치지 않고는 판이 움직이기 어려운 상태
- `payoff_axis`
  - 블록/아크가 끝날 때 회수되는 만족의 형태
- `failure_axis`
  - 패배했을 때 실제로 잃는 것
- `hud_interpretation`
  - `FinanceHUD` 또는 `Resource-Power HUD`를 어떤 축으로 읽는지

---

## 4. 좋은 예시

```json
{
  "primary_profile": "entertainment_media_profile",
  "secondary_profile": "business_growth_profile",
  "resource_axis": "IP, 편성 슬롯, 팬덤 화제성, 제작 라인",
  "power_axis": "캐스팅 결정권, 편성 협상력, 레이블 통제력",
  "control_axis": "주인공 없이는 주요 IP와 편성 라인이 굴러가지 않는 상태",
  "payoff_axis": "흥행, 편성권 회수, 내부 권한 확대",
  "failure_axis": "배급 손실, 팬덤 역풍, 라인 이탈",
  "hud_interpretation": "돈뿐 아니라 IP/편성/팬덤 자원을 함께 보여주는 HUD",
  "selection_rationale": [
    "주 전장은 방송/플랫폼/IP 성장",
    "부 전장은 레이블/사업 운영권 확보"
  ]
}
```

좋은 이유:

- 주/보조 프로파일 구분이 뚜렷하다
- 자원과 권력이 무엇인지 문장으로 보인다
- HUD 해석이 작품에 맞게 잠겼다

---

## 5. 나쁜 예시

```json
{
  "primary_profile": "investment_market_profile",
  "secondary_profile": "medical_professional_profile",
  "resource_axis": "대충 힘",
  "power_axis": "잘나감",
  "hud_interpretation": "그때그때 다름"
}
```

나쁜 이유:

- 두 프로파일이 같은 작품 전장을 설명하지 못한다
- 축 해석이 추상적이다
- HUD 의미가 고정되지 않는다

---

## 6. Stop / Go 기준

### Stop

- `primary_profile`가 비어 있음
- `secondary_profile`까지 합쳐 3개 이상 혼합하려 함
- `resource_axis`와 `power_axis`를 문장으로 설명하지 못함
- 호환 필드 해석이 작품 전장과 안 맞음

### Go

- 주 프로파일이 명확함
- 보조 프로파일이 있더라도 주 전장을 흐리지 않음
- `resource/power/control/payoff/failure`가 구체적으로 설명됨

---

## 7. 프로파일 선택 실패 사례

- 투자물인데 실제 핵심 전장이 회사 KPI/결재선이면 `investment`로만 잠그면 안 된다
- 의학물인데 병원 권한이 핵심인데 `business_growth`로만 잠그면 의료 디테일이 빠진다
- 신입사원물인데 KPI/예산/결재선이 없으면 `office_power_profile`로 받지 않는다

---

## 8. 3-Pass Self Audit

### Pass 1. 계약 정합성

- 현재 blockguide general mode의 프로파일 표와 호환된다.

### Pass 2. 실행 가능성

- 낮은 성능 모델도 좋은/나쁜 예시로 판단할 수 있게 적었다.

### Pass 3. 무결성

- UTF-8 only
- 파일 경로 명시
