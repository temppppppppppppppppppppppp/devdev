<!-- [참고자료] -->
<\!-- [참고자료] -->
# TF-C Manuscript Contradiction Audit Report

**Date**: 2026-03-16
**Auditor**: TF-C (Claude Opus 4.6)
**Scope**: Two project databases, intra-project episode-to-episode contradictions only

---

## Project 1: `000__t` (9 episodes, 42,308 chars)

### Project Summary
Investment/regression fiction (투자 회귀물). Protagonist **한시우** (Han Si-woo), age 44, dies in 2024 and regresses to January 2006 at age 26. Third son of **한정호** (Han Jeong-ho), chairman of 대한그룹 (Daehan Group). He leverages 18 years of future knowledge to build an investment empire, starting with WTI crude oil futures.

### Fact Tracking Table

| Fact Category | Detail | First Established | Episode |
|---|---|---|---|
| **Protagonist** | 한시우, male | Ep 1 | Ep 1 |
| **Age (original)** | 44 years old in 2024 | Ep 1 ("44살의 실패한 영혼") | Ep 1 |
| **Age (regressed)** | 26 years old (스물여섯) | Ep 1 | Ep 1 |
| **Regression date** | 2006년 1월 | Ep 1 (달력에 "2006년 1월") | Ep 1 |
| **Regression gap** | 18년 | Ep 1 ("18년 전으로 돌아왔다") | Ep 1 |
| **Career** | 승마 국가대표, 은퇴 | Ep 1 | Ep 1 |
| **Father** | 한정호, 대한그룹 회장 | Ep 2 | Ep 2 |
| **Brothers** | 첫째 형 한태준 (호텔 레저 파트) | Ep 2 | Ep 2 |
| **Initial assets** | ~20억 원 (주식+오피스텔+차+신탁) | Ep 1 ("약 20억 원") | Ep 1 |
| **Company name** | SW인베스트먼트 | Ep 1 | Ep 1 |
| **Lawyer** | 이정훈, 김앤장 법률사무소 | Ep 3 | Ep 3 |
| **Office** | 여의도, 낡은 5층 건물 3층 | Ep 4 | Ep 4 |
| **Phone (personal)** | 폴더폰 (2006년 구형) | Ep 1 | Ep 1 |
| **Phone (new)** | 슬라이드폰 (2006년 최신형) | Ep 4 | Ep 4 |
| **PB** | 박성호, 한미증권 차장 | Ep 5-6 | Ep 5 |
| **Investment** | WTI 원유 6월물 롱, 15억, 3배 레버리지 | Ep 6 | Ep 6 |
| **Account balance (post-asset-sale)** | 1,950,000,000원 | Ep 5 | Ep 5 |
| **Profit (Day 1)** | +87M → +152M → +233M (fluctuating) | Ep 7 | Ep 7 |
| **Profit (Day 2)** | +315,750,000원 (21%+) | Ep 7 | Ep 7 |
| **Target price** | 배럴당 78달러 | Ep 7 | Ep 7 |
| **Next targets** | 금(Gold), 에콰도르 국채 | Ep 7 | Ep 7 |
| **Residence** | 성북동 본가 | Ep 1 | Ep 1 |
| **집사** | 이름 미상, "나이 든 집사" | Ep 1 | Ep 1 |

### Contradictions Found

---

#### M-4-001: 자산 총액 불일치 (20억 vs 19.5억)
- **Type**: M-4 (Ability/asset contradiction)
- **Severity**: IMPORTANT
- **Episodes**: Ep 1, Ep 3, Ep 5
- **Evidence**:
  - Ep 1: "흩어져 있던 모든 자산을 합산하자, 화면에 찍힌 숫자는 **약 20억 원**이었다."
  - Ep 3: "제 명의로 된 주식, 강남의 오피스텔, 그리고 차고에 있는 차까지. 전부 정리하면 **세전 20억 원** 정도는 됩니다."
  - Ep 5: 계좌 잔액 **1,950,000,000원** (19.5억)
  - Ep 6: 초기 예치금 **19억 5천만 원** (법인 계좌 투입)
- **Analysis**: Ep 1과 Ep 3에서 "약 20억"으로 소개된 자산이 Ep 5에서는 19.5억으로 구체화됨. "약 20억"이므로 반올림 범위 내라고 볼 수 있으나, Ep 3에서 아버지 앞에서 "전부 정리하면 세전 20억 원 정도"라고 한 것과 실제 잔액 19.5억 사이에 5000만 원 차이가 존재. 자산 매각 과정에서의 세금이나 수수료를 감안하면 설명 가능하나, 작중에서 명시적 설명이 없음.
- **Verdict**: MINOR -- "약" 20억이라는 표현으로 커버 가능하며, 매각 비용 차이로 자연스럽게 해석됨.

---

#### M-4-002: 투자 금액의 혼동 (15억 vs 전액)
- **Type**: M-4 (Ability/asset contradiction)
- **Severity**: MINOR
- **Episodes**: Ep 5, Ep 6
- **Evidence**:
  - Ep 5: 잔액 19.5억 상태에서 "부모님이 남기신 마지막 유산이자, 내 인생의 마지막 기회. 이 돈을 지키기 위해..."라고 하며 **전액** 투입 뉘앙스
  - Ep 6: 실제 투자는 **15억 원** (19.5억 중), 나머지 4.5억은 유보
- **Analysis**: Ep 5에서는 전액 투입할 것 같은 뉘앙스를 풍기지만, Ep 6에서 한시우는 분명히 "가용 자산 19억 5천만 원 중, 15억 원"이라 명시하며 리스크 관리를 보여줌. 이는 모순이라기보다 서사적 긴장감 조성 후 실제 행동에서의 합리적 판단으로 볼 수 있음.
- **Verdict**: MINOR -- 의도적인 서사 장치로 해석 가능.

---

#### M-1-003: 박성호 직급 혼선 (차장 vs 팀장)
- **Type**: M-1 (Character setting contradiction)
- **Severity**: IMPORTANT
- **Episodes**: Ep 5, Ep 6, Ep 7
- **Evidence**:
  - Ep 5: 한시우가 **의도적으로** "팀장"이라 부름 ("과거의 그는 몇 년 뒤 팀장으로 승진했지만, **지금은 아니었다**. 하지만 나는 의도적으로 그를 '팀장'이라 불렀다.")
  - Ep 5: 박성호 본인도 "아직 팀장은 아닙니다만"이라고 정정
  - Ep 6: 나레이션에서 "박성호 **차장**" 으로 소개
  - Ep 7: 한시우가 계속 "팀장"으로 호칭
- **Analysis**: Ep 5에서 한시우가 의도적으로 미래의 직급인 "팀장"으로 불러 자존심을 자극하는 전략이 명시적으로 설명됨. Ep 6의 나레이터 표기("차장")와 일관됨. Ep 7에서도 한시우는 계속 "팀장"이라 부르는데 이는 이미 확립된 호칭 패턴의 연속. 모순 아님.
- **Verdict**: NOT A CONTRADICTION -- 의도적인 캐릭터 전략으로 명시되어 있음.

---

#### M-6-004: 컴퓨터 장비 변경 (낡은 컴퓨터 → 직접 조립한 컴퓨터)
- **Type**: M-6 (Event continuity)
- **Severity**: MINOR
- **Episodes**: Ep 4, Ep 7
- **Evidence**:
  - Ep 4: 사무실에서 "낡은 노트북의 전원을 연결했다"
  - Ep 7: "직접 조립한 컴퓨터의 전원 버튼을 눌렀다"
- **Analysis**: Ep 4에서 입주 직후 노트북을 사용, Ep 7에서 다음 날 저녁에는 조립 컴퓨터를 사용. 시간 경과 사이에 컴퓨터를 구매/조립한 것으로 해석 가능하나, 그 과정이 언급되지 않음.
- **Verdict**: MINOR -- 합리적 추론 가능하나 설명 부재.

---

#### M-2-005: 아버지와의 대화에서 "부모님이 남기신" 표현
- **Type**: M-5 (Relationship/setting contradiction)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 5
- **Evidence**:
  - Ep 1: "할아버지께서 물려주신 자금을 넣어둔 신탁 계좌" + "스폰서 계약금과 우승 상금"
  - Ep 3: 아버지가 "네가 가진 그 푼돈으로 뭘 하겠다는 거냐. 네놈 앞으로 된 자산이라고 해봐야 **내가, 네 어미가** 쥐여준 것들이 전부다"
  - Ep 5: "**부모님이 남기신** 마지막 유산"
- **Analysis**: Ep 1에서는 자산 출처를 "국가대표 시절의 스폰서 계약금과 우승 상금, 그리고 할아버지께서 물려주신 자금"으로 설명. Ep 3에서 아버지는 "내가, 네 어미가 쥐여준 것들"이라 말하며 출처를 다르게 인식. Ep 5에서는 "부모님이 남기신"이라 표현. 할아버지 유산 vs 부모 제공 자산이라는 미묘한 출처 불일치가 있으나, 실제로는 할아버지 유산 + 부모 증여 + 본인 소득이 합산된 것이므로, 화자에 따라 다른 관점을 반영한 것으로 볼 수 있음.
- **Verdict**: MINOR -- 화자별 인식 차이로 자연스러우나 통일감은 부족.

---

#### M-3-006: 사무실 위치/건물 내부 묘사 변화
- **Type**: M-3 (Location contradiction)
- **Severity**: MINOR
- **Episodes**: Ep 4, Ep 5, Ep 6, Ep 7, Ep 8
- **Evidence**:
  - Ep 4: "엘리베이터도 없는 5층 건물 3층" + "낡은 나무 바닥"
  - Ep 5: "퀴퀴한 먼지와 오래된 서류의 냄새" + "낡은 형광등"
  - Ep 6: "페인트 냄새가 채 가시지 않은 공간"
  - Ep 7: "아직 페인트 냄새도 가시지 않은 공간"
- **Analysis**: Ep 4에서 이미 입주한 사무실이 Ep 6-7에서 "페인트 냄새가 가시지 않은" 것으로 묘사됨. 입주 후 페인트 도색을 했다고 해석할 수 있지만, 그 과정이 묘사되지 않음. 사소한 디테일 불일치.
- **Verdict**: MINOR.

---

#### M-1-007: 집사 vs 하녀 인물 혼선
- **Type**: M-1 (Character setting)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 2
- **Evidence**:
  - Ep 1: "나이 든 집사의 목소리" -- "도련님, 기침하셨습니까?"
  - Ep 2: "나이 든 하녀가 나를 발견하고는 화들짝 놀라며" -- 별개 인물
  - Ep 2: 서재에서 돌아올 때 집사에 대한 언급 없음
- **Analysis**: 집사와 하녀는 별개의 인물이므로 모순 아님. 다만 집사의 이름이 없이 "나이 든 집사"로만 언급됨.
- **Verdict**: NOT A CONTRADICTION.

---

### Project 1 Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| IMPORTANT | 1 (M-4-001, 자산 총액 근사값 차이) |
| MINOR | 4 (M-4-002, M-6-004, M-2-005, M-3-006) |
| NOT A CONTRADICTION | 2 (M-1-003, M-1-007) |

**Overall Assessment**: Project 1 (000__t)은 9화에 걸쳐 매우 높은 내적 일관성을 보여줌. 주인공 설정(26세/44세, 승마 국가대표 출신), 타임라인(2006년 1월 → 이란 핵 문제 → WTI 폭등), 캐릭터 관계(아버지 한정호, 형 한태준, 변호사 이정훈, PB 박성호), 자산 흐름(20억 → 법인 설립 → 15억 투자 → 수익) 모두 일관되게 유지됨. CRITICAL 수준의 모순은 발견되지 않음.

---

## Project 2: `00_test_11_stage34_live_runtime_proof_refresh_20260314` (7 episodes, 31,619 chars)

### Project Summary
동일한 설정의 투자 회귀물. 주인공 한시우가 2024년에서 2006년으로 회귀하여 SW인베스트먼트를 설립하고 원유 선물에 투자하는 이야기. Project 1과 동일 세계관이지만 디테일이 다른 **별도 생성 버전**.

### Fact Tracking Table

| Fact Category | Detail | First Established | Episode |
|---|---|---|---|
| **Protagonist** | 한시우, male | Ep 1 | Ep 1 |
| **Age (original)** | 40대 중반 ("40대 중반의 망가진 육체") | Ep 1 | Ep 1 |
| **Age (regressed)** | 26 years old (스물여섯) | Ep 1 | Ep 1 |
| **Regression date** | 2006년 1월 17일 | Ep 1 (폴더폰 액정) | Ep 1 |
| **Regression gap** | 18년 | Ep 1 | Ep 1 |
| **Death cause** | 빚쟁이 발길질 아래 사망 | Ep 1 | Ep 1 |
| **Career** | 승마 국가대표 | Ep 1 (트로피 묘사) | Ep 1 |
| **Father** | 한정호, 대한그룹 회장 | Ep 1 | Ep 1 |
| **Brothers** | 첫째 형 한태준 (대한그룹 황태자) | Ep 3 | Ep 3 |
| **Kim 집사** | 김기철 (이름 명시) | Ep 1 | Ep 1 |
| **Mother** | "십수 년 전 병으로 돌아가신 어머니" | Ep 1 | Ep 1 |
| **가정부** | 나이 든 가정부 (별개 인물) | Ep 1 | Ep 1 |
| **Initial assets** | 20억 목표 (5억 신탁 + 주식 + 상금 + 애마) | Ep 1 | Ep 1 |
| **애마** | 아퀼라 (Aquila) | Ep 1 | Ep 1 |
| **Final balance** | 2,087,450,000원 (20.87억) | Ep 3 | Ep 3 |
| **Company name** | 주식회사 SW인베스트먼트 | Ep 4 | Ep 4 |
| **Law firm** | 법무법인 제니스 (테헤란로) | Ep 4 | Ep 4 |
| **임시 거처** | 테헤란로 오피스텔 (보증금 1000/월세 80) | Ep 4 | Ep 4 |
| **PB** | 박성호, 한미증권 VIP PB "팀장" | Ep 4-5 | Ep 4 |
| **Investment** | WTI 원유 6월물 롱, 15억, 3배 레버리지 | Ep 6 | Ep 6 |
| **Target** | 금(Gold), 에콰도르 국채 (다음 단계) | Ep 7 | Ep 7 |
| **New phone** | 법무법인 방문 후 24시간 판매점에서 개통 | Ep 4 | Ep 4 |

### Contradictions Found

---

#### M-1-008: 주인공 사망 원인 / 이전 생애 말년 묘사 불일치
- **Type**: M-1 (Character setting)
- **Severity**: IMPORTANT
- **Episodes**: Ep 1, Ep 5
- **Evidence**:
  - Ep 1: "2024년의 겨울, 차갑고 더러운 원룸 바닥에서 **빚쟁이들의 발길질 아래 꺼져가던** 마지막 순간"
  - Ep 7: "전생의 마지막 순간, **이 다리 위에서 뛰어내릴까** 수없이 고민했던 기억이 스쳤다."
- **Analysis**: Ep 1에서는 빚쟁이에게 맞아 죽는 것으로 묘사되었으나, Ep 7에서는 마포대교에서 투신을 고민했던 기억을 언급. 실제로 투신을 실행했다는 의미가 아니라 "고민했던" 기억이므로, 빚쟁이에게 맞아 죽기 전 시점에서 투신을 고민했을 수 있음. 하지만 두 묘사의 뉘앙스가 상충됨 -- 빚쟁이에게 폭행당해 죽은 것과 스스로 투신을 고민한 것은 상당히 다른 심리 상태를 암시.
- **Verdict**: MINOR -- "고민했던" 것이지 실행한 것은 아니므로 직접적 모순은 아니나, 이전 생의 말년 정서 묘사가 일관되지 않음.

---

#### M-1-009: 박성호 직급 불일치 (팀장 vs 비-팀장)
- **Type**: M-1 (Character setting contradiction)
- **Severity**: IMPORTANT
- **Episodes**: Ep 4, Ep 5, Ep 6
- **Evidence**:
  - Ep 4: 한시우가 전화로 "박성호 **팀장**"이라 지칭 (브로커 자동 연결)
  - Ep 5: 한미증권 홈페이지에서 "**박성호 팀장**"으로 표기됨
  - Ep 5: 한시우가 다시 전화해 "VIP 자산관리팀의 **박성호 팀장님** 연결 부탁합니다"
  - Ep 6: 대면 시 "잘 다려진 맞춤 정장에 반짝이는 **명품 시계**를 찬 박성호" -- 직급 별도 언급 없음
- **Contrast with Project 1**: Project 1에서는 2006년 시점에 박성호가 "**차장**"이며 한시우가 의도적으로 미래 직급인 "팀장"으로 불러 자존심을 자극하는 전략이 명시됨. 그러나 Project 2에서는 홈페이지에도 이미 "팀장"으로 표기되어 있어, 현재 직급이 팀장인 것으로 설정됨.
- **Analysis**: Project 2 내부적으로는 일관됨 -- 박성호는 처음부터 "팀장"으로 설정되어 있음. 모순 아님 (intra-project 기준).
- **Verdict**: NOT A CONTRADICTION (intra-project 기준으로 일관됨).

---

#### M-4-010: 자산 총액 세부 불일치
- **Type**: M-4 (Ability/asset contradiction)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 3
- **Evidence**:
  - Ep 1: "어머니가 물려주신 **5억 원짜리 신탁 계좌**. 대한그룹에서 형식적으로 나눠준 비상장주식 몇 주. 각종 승마 대회에서 받은 상금과 모델 활동으로 번 돈" + 애마 아퀼라 → 목표 "20억"
  - Ep 3: 모든 자산 현금화 후 최종 잔액 **2,087,450,000원** (20.87억)
- **Analysis**: 5억 신탁 + 비상장주식 + 상금/모델비 + 스포츠카 + 애마 = 20.87억으로 합산됨. 목표 20억보다 많지만 "목표 금액은 20억"이라 했으므로 초과 달성한 것. 내적으로 일관됨.
- **Verdict**: NOT A CONTRADICTION.

---

#### M-1-011: 어머니 생존 여부
- **Type**: M-1 (Character setting)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 3
- **Evidence**:
  - Ep 1: "**십수 년 전 병으로 돌아가신 어머니**의 목소리는 아니었지만" -- 어머니가 이미 사망했음을 암시
  - Ep 1: "**어머니**가 물려주신 5억 원짜리 신탁 계좌" -- 유산으로 해석 가능
  - Ep 3: "**어머니의 유산**이었던 신탁을 해지하고" (Ep 5에서 언급)
- **Analysis**: 어머니가 2006년 이전에 병사한 것으로 일관됨. "물려주신"은 유산 의미. 모순 없음.
- **Verdict**: NOT A CONTRADICTION.

---

#### M-6-012: 아퀼라 매각 전화 중복
- **Type**: M-6 (Event continuity contradiction)
- **Severity**: IMPORTANT
- **Episodes**: Ep 1, Ep 3
- **Evidence**:
  - Ep 1: 한시우가 박 조교사에게 전화 -- "아퀼라... 요즘 상태는 어떻습니까?" → "아니요, 조만간... **구매자를 찾아봐야겠습니다.**"
  - Ep 3: 한시우가 다시 박 조교사에게 전화 -- "도련님! **오랜만입니다.** 아퀼라 보러 오시는 겁니까?" → "아니. **구매자를 알아봐 줘.**"
- **Analysis**: Ep 1에서 이미 박 조교사에게 전화하여 구매자를 찾겠다고 말했는데, Ep 3에서 박 조교사가 "오랜만입니다"라며 마치 처음 연락하는 것처럼 반응하고, 한시우도 다시 같은 내용의 요청을 함. Ep 1의 전화와 Ep 3의 전화가 중복되는 사건으로, 두 에피소드가 동일한 이벤트를 서로 다르게 서술하고 있음.
- **Verdict**: **CRITICAL** -- 동일 이벤트(아퀼라 매각 의뢰)가 두 번 별도로 발생한 것처럼 묘사됨. Ep 1에서 이미 매각 의사를 전달했다면, Ep 3에서 박 조교사가 "오랜만입니다"라고 하며 처음 듣는 것처럼 반응하는 것은 명확한 사건 연속성 모순.

---

#### M-6-013: 법인 설립 시점/방법 차이
- **Type**: M-6 (Event continuity)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 3, Ep 4
- **Evidence**:
  - Ep 1: 한시우가 자산 청산 시나리오를 계획하며 "SW인베스트먼트"를 구상. "법인 설립이다"라고 결심
  - Ep 3: 모든 자산 현금화 후 "SW인베스트먼트. 첫 단추는 법인 설립이다"라며 검색 시작 직전 한태준 등장
  - Ep 4: 법무법인 '제니스'에서 법인 설립 의뢰
- **Analysis**: 자산 현금화 → 법인 설립의 순서가 자연스럽게 이어짐. 모순 없음.
- **Verdict**: NOT A CONTRADICTION.

---

#### M-2-014: 이란 핵 뉴스 타이밍
- **Type**: M-2 (Timeline)
- **Severity**: MINOR
- **Episodes**: Ep 1, Ep 4, Ep 7
- **Evidence**:
  - Ep 1: "2006년 2월. 이란의 핵 농축 시설 재가동 선언" (기억/계획 단계)
  - Ep 4: [속보] 기사 확인 -- 시점이 명확하지 않으나, 법인 설립+사무실 계약 직후
  - Ep 7: 여전히 "이란의 핵 개발 재개 선언 직후"
- **Analysis**: Ep 4의 속보가 Ep 1에서 회귀한 "2006년 1월 17일"로부터 어느 정도 시간이 경과한 시점. 아버지 면담 → 자산 정리 → 법인 설립 → 사무실 계약의 과정을 거쳤으므로 2월 초-중순경으로 추정. 기억 속 "2006년 2월"과 일치.
- **Verdict**: NOT A CONTRADICTION.

---

#### M-6-015: 전화 vs 새 전화기 순서
- **Type**: M-6 (Event continuity)
- **Severity**: MINOR
- **Episodes**: Ep 3, Ep 4
- **Evidence**:
  - Ep 3: 아버지 면담 후 "구형 폴더폰"으로 김성훈 팀장, 박 조교사에게 전화
  - Ep 4: 법무법인 방문 후 "24시간 휴대폰 판매점"에서 새 번호/기기 개통. "감시의 끈을 완전히 끊어내기 위해, **집에서 쓰던 폴더폰을 버리고** 새로운 번호와 기기가 필요했다"
- **Analysis**: Ep 3에서 이미 폴더폰으로 자산 매각 관련 전화를 여러 통 했는데, 이 통화 기록이 아버지/형 쪽에 노출될 수 있음에도 Ep 4에서야 비로소 "감시의 끈을 끊겠다"며 새 폰 개통. 보안 의식 있는 캐릭터치고는 순서가 역전됨.
- **Verdict**: MINOR -- 서사적으로 아쉬운 부분이나, "감시의 끈"이 통화 기록이 아닌 위치 추적 등을 의미할 수 있으므로 완전한 모순은 아님.

---

#### M-3-016: 사무실 위치 변경 (여의도 → 테헤란로)
- **Type**: M-3 (Location)
- **Severity**: IMPORTANT
- **Episodes**: Ep 4, Ep 5, Ep 6, Ep 7
- **Evidence**:
  - Project 1 (000__t): 사무실이 **여의도**에 위치 (Ep 4: "여의도 사무실 임대" 검색, 5층 건물 3층)
  - Project 2: 임시 거처가 **테헤란로 오피스텔** (Ep 4: "보증금 1000에 월세 80"), 별도의 여의도 사무실은 없음
- **Analysis**: 이것은 cross-project 차이이므로 본 감사 범위(intra-project) 밖. Project 2 내부적으로는 테헤란로 오피스텔이 사무실 겸 거처로 일관됨.
- **Verdict**: NOT A CONTRADICTION (intra-project 기준).

---

#### M-4-017: 법인 계좌 입금액
- **Type**: M-4 (Asset contradiction)
- **Severity**: MINOR
- **Episodes**: Ep 3, Ep 4
- **Evidence**:
  - Ep 3: 최종 잔액 2,087,450,000원 (20.87억)
  - Ep 4: "개인 계좌에 잠들어 있던 20억 8745만 원. 망설임은 없었다. **전액을** 'SW인베스트먼트'의 법인 계좌로 옮겼다."
- **Analysis**: 금액이 정확히 일치함 (2,087,450,000 = 20억 8745만). 일관됨.
- **Verdict**: NOT A CONTRADICTION.

---

### Project 2 Summary

| Severity | Count |
|---|---|
| CRITICAL | 1 (M-6-012, 아퀼라 매각 전화 중복) |
| IMPORTANT | 1 (M-1-008, 사망 원인 뉘앙스 불일치 -- downgraded to MINOR) |
| MINOR | 3 (M-1-008, M-6-015, M-4-010 vicinity) |
| NOT A CONTRADICTION | 5 |

**Overall Assessment**: Project 2는 7화에 걸쳐 대체로 높은 일관성을 보여주나, **CRITICAL 1건**이 발견됨. Ep 1과 Ep 3에서 아퀼라 매각 의뢰 전화가 중복 발생하는 것은 명확한 사건 연속성 모순. 이는 Ep 1에서 자산 청산 계획 수립 시 이미 전화한 내용이 Ep 3의 자산 청산 실행 시 다시 새롭게 발생하는 구조적 문제로, LLM 생성 과정에서 이전 에피소드의 세부 사건을 충분히 참조하지 못한 결과로 판단됨.

---

## Cross-Project Observations (참고용, 감사 범위 외)

두 프로젝트는 동일한 설정(한시우 회귀, SW인베스트먼트, WTI 원유 투자)을 공유하지만 다음과 같은 설정 차이가 존재:

| 항목 | Project 1 (000__t) | Project 2 |
|---|---|---|
| 회귀 날짜 | "2006년 1월" (구체 일자 없음) | "2006년 1월 17일" |
| 사망 원인 | 원룸 바닥에서 사망 (원인 불명확) | 빚쟁이 폭행으로 사망 |
| 어머니 | 생존 여부 불명 | "십수 년 전 병으로 돌아가신" 상태 |
| 애마 | 언급 없음 | 아퀼라 (매각 대상) |
| 김 집사 | 이름 없음 ("나이 든 집사") | 김기철 (이름 명시) |
| 법률 대리인 | 이정훈 (김앤장 법률사무소) | 법무법인 제니스 (변호사 이름 미상) |
| 사무실 | 여의도 낡은 5층 건물 3층 | 테헤란로 오피스텔 |
| 박성호 직급 | 차장 (한시우가 의도적으로 "팀장" 호칭) | 팀장 (실제 직급) |
| 형과의 대면 | 없음 | 한태준이 방으로 찾아와 대치 (Ep 3-4) |
| 아버지 반응 | "마음대로 해봐라" + 경고 | "얼마면 되겠나?" 역제안 |
| 자산 총액 | ~19.5억 | ~20.87억 |

이러한 차이는 동일 블루프린트에서 다른 에피소드 생성 시도의 결과로, 각 프로젝트 내부 일관성이 중요한 감사 대상임.

---

## Final Summary

| | CRITICAL | IMPORTANT | MINOR | Clean |
|---|---|---|---|---|
| **Project 1** (9 eps) | 0 | 1 | 4 | Very Good |
| **Project 2** (7 eps) | 1 | 0 | 3 | Good (1 CRITICAL) |
| **Total** | **1** | **1** | **7** | |

### Key Findings

1. **CRITICAL (1건)**: Project 2, M-6-012 -- 아퀼라 매각 전화가 Ep 1과 Ep 3에서 중복 발생. 박 조교사가 두 번째 전화에서 "오랜만입니다"라고 하며 마치 첫 연락인 것처럼 반응하는 것은 사건 연속성 파괴.

2. **IMPORTANT (1건)**: Project 1, M-4-001 -- 자산 "약 20억"이 실제로는 19.5억으로 구체화됨. 심각한 모순은 아니나 정확한 수치 불일치.

3. **양 프로젝트 모두** 핵심 설정(캐릭터, 타임라인, 투자 전략, 인물 관계)은 높은 수준으로 일관되게 유지됨. 특히 WTI 원유 → 금 → 에콰도르라는 투자 로드맵, 아버지/형과의 갈등 구도, 박성호를 도구로 활용하는 전략 등의 대서사가 흔들림 없이 전개됨.

---

*Audit completed: 2026-03-16 by TF-C (Claude Opus 4.6)*
