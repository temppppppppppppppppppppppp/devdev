# Lane 3: Pairs 05, 06 — TR/BI Consistency Bounded Survey

Date: 2026-04-06
Lane: 3
Assigned pairs: 05, 06
Family overlay: blockguide (both)
Audit scope: read-only pair consistency only
Harness read order: narrative-router SSOT -> material-revival-ladder -> blockguide SSOT -> parallel order

---

## Pair 05: `failed_future_ceo_intern`

### Pair Verdict: **clean**

### Severity Summary

| Severity | Count |
| --- | --- |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 3 |

### Findings

**1. P3 — incarnation_type 명칭 불일치**

- `TR: regression_ext.regression_type` = `"빙의"`, `incarnation_type` = `"빙의자"` (전 블록 일관)
- `BI: protagonist_config.incarnation_type` = `"회귀자"`
- `BI: _genre` = `"현대 한국 기업 빙의 조직장악물"` (장르 자체는 "빙의" 명시)
- TR과 BI 장르 라벨 모두 "빙의"를 쓰지만, BI protagonist_config만 "회귀자"로 표기. 쌍 정체성이나 서사 해석을 깨지는 않으나 메타데이터 정합성 노이즈.
- **next-step**: `BI: protagonist_config.incarnation_type` → `"빙의자"`로 패치

**2. P3 — FinanceHUD 최상위 financial_status가 엔드게임 값**

- `BI: FinanceHUD.Protagonist.actual_truth.financial_status.mobilizable_capital` = `"5200억+"`
- `BI: FinanceHUD.Protagonist.actual_truth.financial_status.total_assets` = `"5200억+"`
- 시작 상태(0원/인턴 직급 0)가 아니라 Block 70 최종값. `portfolio_history`는 Block 1(0원) → Block 70(5200억+)을 정확히 추적하므로 실질 정보 손실은 없으나, 최상위 snapshot이 출발이 아닌 도착을 보여줌.
- **next-step**: BI 관례 확인 후 시작/종료 구분 여부 결정 (pair-level 정합성 이슈 아님)

**3. P3 — CoreIdentity.desire에 블록 참조 잔류**

- `BI: CoreIdentity.desire` = `"...Block 1 안에 권한 입장권 보상 4종으로 회수한다."`
- BI 독립 문서로서 TR 블록 번호를 직접 참조하는 것은 약간 이례적. 서사 해석에는 영향 없음.
- **next-step**: BI standalone 정합성 강화 시 블록 참조 제거 고려

### Pair Identity Anchors

| Axis | TR | BI | Aligned |
| --- | --- | --- | --- |
| work_id / slug | `failed_future_ceo_intern` | `failed_future_ceo_intern` (파일명) | YES |
| title | (implicit) 망한 미래의 CEO가 인턴으로 빙의했다 | `망한 미래의 CEO가 인턴으로 빙의했다` | YES |
| protagonist | 이수혁 | 이수혁 | YES |
| start year | 2027 | 2027 | YES |
| company | 한라테크 | 한라테크 | YES |

### Core Narrative Alignment

| Axis | TR | BI | Status |
| --- | --- | --- | --- |
| protagonist desire | 결재선·KPI·이사회 표결 장악 → CEO 시총 85조 | 결재선·KPI·이사회 표결을 0권한에서 한 칸씩 재배치 | aligned |
| growth resource | 권한 입장권 (결재선·예산 코드·프로젝트 오너십·지분) | 권한 입장권 우선 회수, 통제권·지분>성과 | aligned |
| main antagonist | 정태준 → 삼면 연합(정태준+사라+CATT) | opponent_transition_plan 5단계 동일 | aligned |
| endgame pressure | Block 64-70: 삼면 연합 공개매수 → 분열 → 주총 분쇄 | Phase 3(block 61-70): 복합 연합 최종 → 공개매수 방어 | aligned |
| core premise/tone | 빙의 인턴 → 결재선 우회 → CEO 13년 역전물 | 빙의 조직장악물, 선점>회개/지배>충성 | aligned |

### Late-Pair Carry

- `TR Block 70`: 시총 85조, 개인 5200억+, 삼면 연합 와해, 전생 파산 역전 완성
- `BI: portfolio_history[block=70]`: `"5200억+"`, event `"다른 결말"`
- `BI: opponent_transition_plan` Phase 3 transition_block = 70
- Late-block escalation (공개매수 → 3중 방어 → 분열 → 주총 표결) 반영됨

### Family Overlay (blockguide)

- `BI: FinanceHUD` 존재, Resource-Power HUD 의미론 충족
- `BI: business_lines` 20개 라인 (경영지원본부~독일 동맹) 
- `BI: company_state` 출발점 정확 (인턴 직급 0, 보고서 상신 불가)
- `BI: investment_style` = TR의 execution_doctrine과 동일 문구
- `BI: front_sector_by_arc` 7개 아크 전선/지원 구조 완비

---

## Pair 06: `gatekeeper_heir`

### Pair Verdict: **clean**

### Severity Summary

| Severity | Count |
| --- | --- |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 3 |

### Findings

**1. P3 — FinanceHUD 최상위 financial_status가 엔드게임 값**

- `BI: FinanceHUD.Protagonist.actual_truth.financial_status.mobilizable_capital` = `"후계자 실권 확정 + 7관문 연결 가동 + 다음 관문 예고"`
- 시작 상태(Lv0 방치)가 아니라 Block 70 최종값. `portfolio_history`는 Block 1(Lv0 방치) → Block 70(후계자 실권 확정)을 정확히 추적.
- Pair 05와 동일 패턴. BI 관례 이슈이며 pair consistency에는 무관.
- **next-step**: BI 전체 관례 일괄 확인 시 처리

**2. P3 — CoreIdentity.crisis가 logline 중복**

- `BI: CoreIdentity.crisis` = logline과 동일 문구 (`"회장이 사랑한 유일한 손자는 회사가 아니라 관문을 먹는다..."`)
- crisis가 logline 복사본이 아니라 독립적 위기 서술이어야 더 유용하나, pair 정합성 자체는 깨지지 않음.
- **next-step**: BI 품질 강화 시 crisis를 독립 서술로 분리 고려

**3. P3 — start_point.context 조사 잔류 ("세원정밀를")**

- `BI: protagonist_config.start_point.context` = `"세원정밀를 매각 직전의 후공정 장비 계열사..."`
- "를"이 불필요하게 붙어 있음 (문법: "세원정밀은" 또는 쉼표 처리가 자연스러움). 타이포 수준.
- **next-step**: `"세원정밀를"` → `"세원정밀,"` 또는 `"세원정밀은"` 패치

### Pair Identity Anchors

| Axis | TR | BI | Aligned |
| --- | --- | --- | --- |
| work_id / slug | (implicit) gatekeeper_heir | `gatekeeper_heir` (파일명) | YES |
| title | (implicit) 사람값이 보이는 후계자 | `사람값이 보이는 후계자` | YES |
| protagonist | 강도윤 | 강도윤 | YES |
| start year | 2012 | 2012 | YES |
| company | 세원정밀 / 세원그룹 | 세원정밀 / 세원그룹 | YES |

### Core Narrative Alignment

| Axis | TR | BI | Status |
| --- | --- | --- | --- |
| protagonist desire | 총애받는 손자 → 권한을 줄 수밖에 없는 후계자 증명 | 동일 (`"할아버지가 바로 권한을 줄 수밖에 없는 후계자로 증명"`) | aligned |
| growth resource | 배치 조감 (사람×자리 최적 배치 읽기) | 동일 (`"배치 조감"`) | aligned |
| main antagonist | 원로 라인 → 공급망 → 현장 관성 → 외부 관문 → PEF 분리매각론 | opponent_transition_plan 5단계 동일 | aligned |
| endgame pressure | Block 62-70: PEF 분리안 vs holdco → 이사회 표결 → 후계자 실권 확정 | Phase 5(block 51-70): 쪼개기 제국 → holdco 방어 | aligned |
| core premise/tone | 재벌 손자 회귀 → 관문산업 장악 → 운영제국 재설계 | `"관문 제국으로 재설계"` | aligned |

### Late-Pair Carry

- `TR Block 70`: 관문 제국 — holdco 가동, 7관문 연결, 후계자 실권 확정, 다음 관문 예고
- `BI: portfolio_history[block=70]`: `"후계자 실권 확정 + 7관문 연결 가동 + 다음 관문 예고"`
- `BI: opponent_transition_plan` Phase 5 transition_block = 70
- `BI: final_goal` = `"장비·소재·서비스·금융·표준 관문 제국으로 재설계"` — TR exit과 완전 일치
- Late-block escalation (공신 서명 → holdco 설계 → 이사회 표결 → 대표이사 확정) 반영됨

### Family Overlay (blockguide)

- `BI: FinanceHUD` 존재, Resource-Power HUD 의미론 충족
- `BI: business_lines` 36개 라인 (후공정 장비~외부 자본 방어) — TR 아크 전선과 대응
- `BI: company_state` 출발점 정확 (매각 직전 후공정 장비 계열사, 비용센터 취급)
- `BI: investment_style` = TR의 execution_doctrine과 동일 의미 (`"관문을 먹는다"`)
- `BI: front_sector_by_arc` 7개 아크 전선/지원 구조 완비
- `BI: special_talent.name` = `"사업 감각"`, description = `"배치 조감"` — TR genre_ext.special_ability와 정합

---

## Lane 3 Summary Table

| Pair | Verdict | P0 | P1 | P2 | P3 | Key Note |
| --- | --- | --- | --- | --- | --- | --- |
| 05 | **clean** | 0 | 0 | 0 | 3 | incarnation_type 명칭 노이즈("회귀자"→"빙의자"), FinanceHUD 엔드게임 값, desire 블록참조 잔류 |
| 06 | **clean** | 0 | 0 | 0 | 3 | FinanceHUD 엔드게임 값, crisis=logline 중복, start_point 조사 타이포 |

Both pairs are **pair-consistent**. No P0/P1/P2 issues. All P3 findings are naming noise, metadata cosmetics, or minor typos that do not break pair identity or narrative alignment.
