# WG-V2 Verdict: chaebol_allowance_zero

- Date: 2026-04-06
- Terminal: 2
- Batch: work_guard_greenplus_batch01

## 1. Target Work

- work_id: `chaebol_allowance_zero`
- title: 재벌 3세인데 용돈이 0원
- family: blockguide
- profiles: `business_growth_profile` + `office_power_profile`

## 2. Authority Set Used

- canonical pitch: `material_ssot/20_pitch/canon/chaebol_allowance_zero.md`
- pitch philosophy: `material_ssot/20_pitch/pitch-philosophy.md`
- protagonist-first constitution: `material_ssot/20_pitch/protagonist-first-constitution.md`
- translation map: `material_ssot/20_pitch/work-guard-translation-map.md`
- profile lock: `treatments/preprocess/chaebol_allowance_zero/profile_lock.json`
- phase0 ready snapshot: `treatments/preprocess/chaebol_allowance_zero/phase0_ready_snapshot.json`
- live phase0: `treatments/chaebol_allowance_zero_phase0_design.json`
- live TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- live BI: `bible/02_bi_chaebol_allowance_zero.json`
- production grade: `GREENPLUS`

## 3. WG-V2 Checklist

### 1. One-Line Truth — YES

`카드 잘린 재벌 3세가 장례식장 뒷문에서 시작해 밥차·린넨·셔틀·영수증·정산 레인을 한 칸씩 손에 옮겨, 가문이 먼저 자기 현금흐름망에 의존하는 구조를 만든다`

주인공 장악 판타지가 바로 읽힌다. `왜 이 주인공이 멋있는가`가 한 문장에 들어 있다. generic `재벌 승계전`이 아니라 밑단 운영망 → 반복 현금흐름 → 가문 역의존의 인과가 압축됐다.

### 2. Protagonist-First Purity — YES

결핍(현금 0원, 망나니 평판, 가문 지원 전면 차단)은 명확하되 과실은 없다. 유언장 7항이라는 외부 강제이지 자업자득이 아님. 회귀 기억은 예언이 아니라 현장 지식(협력사 붕괴 순서·누수 지도·재배치 감각)으로 제약됨.

### 3. Tracking Slots — YES

4개 slot 모두 `서열 변화 / 통제권 회수 / 재평가` 축이다.

- 반복 현금흐름 규모 상승 (0원 → 연환산 12억 → 38억 → 76억 → 154억 → 전국망) — 사업 체급 추적
- 저평가 → 고평가 전환 — 망나니 → 하부 운영망을 읽는 사람
- 계약권·승인권·정산권·현장 대체 불가능성 회수 — 권한 축 누적
- 가문 역의존도 상승 — 장악도의 최종 형태

`성장`, `성공` 같은 generic 없음.

### 4. Signature Scene Engine — YES

3개 engine 모두 `저건 쟤라서 가능했다`를 증명하는 구조.

- 밑단 누수·유령업체·정산 병목 감지 → 소액/즉시 개입: 윤재이만의 누수 지도와 재배치 감각이 원인
- 정산 표준화 → 관문 전환 → 공개 성과 증명: 반복 현금흐름·납기·위생이 증거
- 성과 직후 체감형 보상 부착: 다음 운영 전장 입장권·형의 눈빛 변화 즉시 부착

첫 블록 간판(장례 특수 끝 후 첫 월 반복매출 증명 + 형의 눈빛 전환)이 engine에 정확히 잡혀 있다.

### 5. Protagonist Weapon — YES

3개 무기 모두 인과가 선명하다.

- 하부 운영망 누수 지도: 어느 현장에 언제 뭐가 터지는지 기억하는 것은 이 작품 고유
- 새벽 뒷문 현장 감각: 회의실이 아니라 밑단에서 먼저 읽는 것은 generic competence 아님
- 소액/즉시 재배치 속도: 현금 0원 상태에서 밥차 한 대·꽃값·영수증부터 잡는 실행력에 인과 제한(큰돈·시세판 시선 유혹)이 걸려 있음

### 6. Reward Vector — YES

- 초반 보상이 돈 자체가 아니라 `세탁·청소·셔틀 반복 계약 → 정산 레인 접근권 → 형의 눈빛 전환 → 호텔 BOH 입장권`으로 다음 운영 전장 입장권 형태의 서열 변화
- `admiration_axes`에 `결과로 인정 강제`, `밑바닥에서 시작하는 여유` 등 재평가 방식 명시
- `observer_tiers`가 현장 실무자 → 유수리 → 서도윤 → 윤석진 → 노현주 → 각 전장 실무 동맹으로 계층화
- `evaluation_thresholds`에 1화/3화/각 ARC 기준점 명시

### 7. Crisis Doctrine — YES

- `남들보다 먼저 읽음`이 admiration_axes 첫 항목
- `손실을 통제함`이 별도 축 (현장 사고·납기 위기에서 최소 피해 + 관문 전환)
- `위기 때 빈손/무대응/무보상`이 forbidden_flattenings에 포함
- custom_rules에 `위기는 피해 연출보다 우선순위 선택권 증명`, `반격 예약 없는 손해 금지` 명시
- 현장 사고가 신뢰 붕괴 구조로 작동해야 한다는 canon pitch 원칙이 guard의 `현장 대체 불가능성` control_axis로 번역됨

### 8. Forbidden Flattenings Coverage — YES

15개 항목으로 치명 drift를 충분히 막고 있다. 7대 기본 drift 전부 포함 + 작품 고유 금지(투자물 둔갑 금지, 가문 공짜 구제 금지, 운영축 뭉개기 금지, 현장 사고 추상화 금지, 유령업체 캐리커처화 금지, 적대자 캐리커처 금지, 운빨 포장 금지) 8개 추가.

### 9. Translation Discipline — YES

upstream 철학 문서 복붙 없음. 모든 항목이 support-system cashflow 고유 doctrine으로 압축됨. 교육용 설명문 없음.

### 10. Work Specificity — YES

이 guard를 다른 작품에 그대로 붙이면 어색하다. `반복매출`, `정산 레인`, `구매 코드`, `승인 도장`, `린넨`, `밥차`, `셔틀`, `백오브하우스`, `폐기물 코드`, `가동률`, `서도윤/윤석진/노현주` 등 이 작품 고유의 생활 인프라 산업 언어와 인물 역학이 전면에 있다.

## 4. WG-V2 Result

**PASS**

- NO: 0개
- WEAK: 0개
- 4번(Signature Scene Engine), 5번(Protagonist Weapon), 6번(Reward Vector) 모두 YES

## 5. Weak Points

전체적으로 깨끗하다. 한 가지 유의할 점:

- `mandatory_lexicon`이 15개로 다른 작품 대비 가장 많은 편이나, 이 작품은 7개 운영축(장례·급식·호텔·공장·병원·정산·전국망)을 순차 확장하는 구조라 각 전장의 핵심 어휘가 모두 독자 체감에 필수적이다. 축소보다 유지가 맞다고 판단한다.
- 회귀 기억의 `시장 시세 예언 금지` 제약이 custom_rules에 명시되어 있어, 투자물 오염 drift 방어가 이중으로 걸려 있다. 이 작품의 가장 큰 drift 위험이 `주식물/투자물 둔갑`이므로 적절한 이중 보호.

## 6. Next Action

- freeze candidate로 확정
- 다른 터미널의 draft 완료 후 batch close 시 일괄 freeze 검토
