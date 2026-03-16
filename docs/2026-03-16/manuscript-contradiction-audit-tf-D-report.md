# TF-D Manuscript Contradiction Audit Report

**Date**: 2026-03-16
**Auditor**: TF-D (Claude Opus 4.6)
**Scope**: Full-text sequential reading of all episodes in two project databases, tracking facts across episodes to identify inter-episode contradictions.

---

## Project 1: `projects/000/project_data.db`

### Project Info

| Field | Value |
|---|---|
| DB Path | `projects/000/project_data.db` |
| Episodes | 6 (EP 1-6) |
| Total Characters | ~27,634 chars |
| Created | 2026-03-15 10:20 ~ 11:44 |
| Genre | Investment/Regression (present-day corporate/financial thriller) |

### Episode Titles

| EP | Title | Chars |
|---|---|---|
| 1 | 선전포고 | 5,371 |
| 2 | 미친놈이거나, 혹은 | 4,612 |
| 3 | 제3화 복수의 제물 | 4,558 |
| 4 | 제4화 첫 번째 포탄 | 5,052 |
| 5 | 게이트키퍼 | 4,040 |
| 6 | 제6화 벽 속의 눈 | 4,001 |

### Fact Tracking Table

#### Characters

| Character | EP Introduced | Role | Key Details |
|---|---|---|---|
| 한시우 | EP1 | Protagonist (regression) | Youngest son of 한정호, lived 18 years of failure in past life, age unspecified (young adult), SW Investment founder |
| 한정호 | EP1 | Father, Chairman | 회장 (Chairman), cigar smoker, owns study with mahogany desk, detached/cold personality |
| 한태민 | EP1 | Second brother (둘째 형) | Antagonist, extravagant (하룻밤 유흥비 = 20억), violent, employs thugs |
| 이준영 | EP1 | Lawyer | 법무법인 '정인', mid-30s, future M&A legend "기업 사냥꾼의 저승사자", just independent from large firm |
| 박성호 | EP2 | Finance/PB | 미래증권 여의도 본점 PB센터, 차장 rank, formerly Derivatives dept star, demoted to PB |
| 태산그룹 어르신 | EP6 | Shadow figure | Controls group's dark side, described as a spider |

#### Assets/Money

| Fact | EP | Detail |
|---|---|---|
| 한시우 initial capital | EP1 | 20억 (청담동 오피스텔 + 보유 주식 + 회원권 = "대략 20억") |
| SW인베스트먼트 자본금 | EP1 | 20억 원 |
| WTI investment | EP4 | Full 20억 via 3x leverage, WTI crude oil futures |
| Loss day 1 | EP5 | -6% evaluation loss (~1.2억 evaporated overnight) |

#### Locations

| Location | EP | Detail |
|---|---|---|
| 한정호 서재 | EP1 | 참나무 문, 마호가니 책상, 스탠드, 서재는 2층에 위치 |
| 법무법인 '정인' | EP1 | 강남 테헤란로, 통유리창, 가죽 소파 |
| 지하 주차장 (법무법인) | EP1 | 콘크리트 기둥, 형광등 |
| 셀프 스토리지 | EP2 | 강남 한적한 이면도로, 24시간 |
| 미래증권 PB센터 | EP2 | 여의도 본점, 고층부 |
| SW인베스트먼트 사무실 | EP3 | 강남 신축 오피스 빌딩, 테헤란로, 통유리창 |
| 비밀 거점 오피스텔 | EP6 | 국회의사당이 보이는 강변, 고급 오피스텔 35층 |
| 한미증권 VIP룸 | EP5 | 여의도 한미증권 빌딩 |

#### Timeline

| Event | EP | Time Reference |
|---|---|---|
| 서재 대면 (아버지) | EP1 | Initial scene |
| 법무법인 방문 | EP1 | "며칠 후" from 서재 scene |
| 지하주차장 대결 (한태민) | EP1-2 | Same day as 법무법인 |
| 셀프스토리지 방문 | EP2 | Same night |
| 미래증권 방문 (박성호) | EP2 | Same night ("자정이 가까운 여의도") |
| SW 사무실 입주 + 자금이체 | EP3 | "다음 날 해질녘" (from 박성호 meeting) |
| 한태민 전화 | EP3 | Same evening as 자금이체 |
| 박성호 준비 완료 보고 | EP4 | Next day, evening |
| WTI 매수 실행 | EP4 | Midnight (뉴욕 시장 개장 시간) |
| 이준영 긴급 전화 (태산그룹) | EP4 | Immediately after 매수 |
| EP5 이준영 통화 계속 | EP5 | Continuous from EP4 |
| 한미증권 VIP룸 방문 | EP5 | "다음 날 오후" |
| 엘리베이터 홀 습격 | EP5 | After VIP룸 meeting |
| 비밀 거점 도착 | EP6 | Same night |

### Contradictions Found

---

#### [M-3-001] CRITICAL: 박성호의 소속 증권사 불일치

- **Type**: M-3 (Location / Affiliation Contradiction)
- **Severity**: CRITICAL
- **Episodes**: EP2 vs EP5

**EP2 (미래증권):**
> "미래증권 빌딩의 고층부 PB센터 창문 하나만이 외롭게 빛을 발하고 있었다."
> "'박성호. 미래증권 여의도 본점 PB센터. 직급은 차장.'"

**EP5 (한미증권):**
> "다음 날 오후, 여의도 한미증권 빌딩."
> "VIP룸의 묵직한 문을 열고 들어서자, 냉방이 과하게 돌아가는 서늘한 공기와 함께 박성호의 파리한 얼굴이 한시우를 맞았다."

**Explanation**: 박성호의 소속이 EP2에서는 "미래증권"으로 명시되고, EP5에서는 "한미증권"으로 변경되었다. 같은 인물이 두 다른 증권사에 소속되어 있는 것으로 서술되어 있으며, 이직에 대한 설명은 전혀 없다. 독자가 즉시 인지할 수 있는 명백한 오류.

---

#### [M-1-001] CRITICAL: 이준영의 직업/역할 설정 불일치 (변호사 vs 노트북 구매 대행)

- **Type**: M-1 (Character Setting Contradiction)
- **Severity**: IMPORTANT

**EP1:**
> "이준영이 직접 준비한 최신형 노트북과 휴대폰이 담긴 쇼핑백도 함께였다."

**Explanation**: 한시우가 법무법인 방문 중 "업무에 사용할 노트북과 휴대폰도 필요합니다. 최고 사양으로."라고 변호사에게 요청하고, 이준영이 이를 직접 준비해준다. 법인 설립 변호사가 전자기기 구매까지 대행하는 것은 역할상 극히 이례적이나, 서술상 한시우의 강한 지시력의 일환으로 해석 가능하므로 IMPORTANT로 분류.

---

#### [M-6-001] IMPORTANT: EP4 마지막 장면과 EP5 시작 부분의 중복/불일치

- **Type**: M-6 (Event Continuity Contradiction)
- **Severity**: IMPORTANT

**EP4 (ending):**
> "한시우의 눈빛이 차갑게 가라앉았다. 그러나 목소리는 오히려 얼음장처럼 차분해졌다."
> "이 변호사님, 진정하십시오. 숨부터 고르시죠. 그들이 뭘 물었습니까? 단어 하나 틀리지 말고 그대로 전해주십시오."

**EP5 (opening, verbatim repetition):**
> "한시우의 눈빛이 차갑게 가라앉았다. 그러나 목소리는 오히려 얼음장처럼 차분해졌다."
> "이 변호사님, 진정하십시오. 숨부터 고르시죠. 그들이 뭘 물었습니까? 단어 하나 틀리지 말고 그대로 전해주십시오."

**Explanation**: EP5가 EP4의 마지막 2문장을 그대로 복사하여 시작한다. 이 자체는 의도적 연속 기법일 수 있으나, EP4 말미에 `[원고_끝]` 태그와 `{{ "patch_state_updates": {} }}` 메타데이터가 본문에 노출되어 있어 생산 과정의 잔여물이 독자에게 보일 위험이 있다.

---

#### [M-4-001] IMPORTANT: 한시우의 노트북 소유/사용 상태 혼선

- **Type**: M-4 (Asset Contradiction)
- **Severity**: IMPORTANT
- **Episodes**: EP1, EP2, EP3

**EP1:**
> "이준영이 직접 준비한 최신형 노트북과 휴대폰이 담긴 쇼핑백도 함께였다."

**EP2:**
> "조수석의 최신형 노트북은 거들떠보지도 않은 채, 방금 꺼내 온 낡은 노트북을 열었다."
> "2006년형 구형 노트북. 이준영에게 받은 번쩍이는 최신 기기와는 비교도 안 될 만큼 투박했다."

**EP3:**
> "바닥에 놓인 2006년형 구형 노트북과 최신형 업무용 휴대폰만이 이곳이 누군가의 새로운 시작점임을 알리고 있었다."

**Explanation**: EP1에서 최신형 노트북을 받고, EP2에서 구형 노트북만 사용하겠다고 명확히 하지만, EP3의 사무실에는 구형 노트북만 있고 최신형 노트북의 행방이 불명확하다. 한시우가 최신형 노트북을 의도적으로 무시하는 것인지, 아니면 어딘가에 보관했는지 서술이 없다. 최신형 노트북이 사라진 것이 아니라 의도적으로 사용하지 않는 것으로 해석 가능하나, 명시적 처리가 없어 독자에게 혼선을 줄 수 있다.

---

#### [M-6-002] IMPORTANT: 법인 계좌 개설 주체 및 장소 혼선

- **Type**: M-6 (Event Continuity)
- **Severity**: IMPORTANT
- **Episodes**: EP2 vs EP3

**EP2 (박성호의 행동):**
> "그는 망설임 없이 법인 계좌 개설을 담당하는 심야 지원팀에 전화를 걸었다."
> "VIP 고객의 긴급 요청이라는 명분을 내세웠다."

**EP3 (박성호의 문자):**
> "[차장 박성호: 대표님, 요청하신 SW인베스트먼트 법인 계좌 개설 및 해외 선물 거래 연동이 완료되었습니다.]"

**Explanation**: EP2에서 박성호가 "자신의 직위와 경력을 걸고" 밤새 법인 계좌 개설을 추진하는 것으로 묘사된다. 그런데 법인 계좌 개설은 통상 법인 대표가 직접 은행에서 진행하는 절차이며, 증권사 PB가 다른 회사(미래증권)의 심야지원팀에 전화해서 법인 계좌를 개설한다는 것은 금융 현실과 다소 불일치한다. 다만 소설적 허용으로 수용 가능한 범위.

---

#### [M-5-001] MINOR: 한태민의 정보 획득 속도 비현실성

- **Type**: M-5 (Relationship / Information flow)
- **Severity**: MINOR
- **Episodes**: EP1, EP3

**EP1:**
> 한시우가 법인 설립 직후 지하주차장에서 한태민에게 포위됨

**EP3:**
> "이미 법인 계좌의 자본금 흐름까지 파악한 모양이었다."

**Explanation**: 한태민이 법인 설립 당일에 지하주차장에서 이미 대기하고 있고, 자본금 이체 직후 즉시 전화하는 것은 정보 획득 속도가 극도로 빠르다. EP1에서 한태민이 "뒷조사를 시키겠다"고 하지만, 법인 설립 서류 제출~법원 등기~계좌 개설까지의 시간을 고려하면 같은 날 이 모든 정보를 파악한 것은 비현실적이다. 다만 재벌가의 정보력으로 설명 가능.

---

#### [M-3-002] MINOR: 한미증권 vs 미래증권 VIP룸 위치

- **Type**: M-3 (Location)
- **Severity**: MINOR (M-3-001과 연계)

**EP5:**
> "다음 날 오후, 여의도 한미증권 빌딩."

**EP6:**
> 한시우가 한미증권 VIP룸에서 나와 엘리베이터 홀에서 습격당함

**Explanation**: EP5-6에서 "한미증권"으로 일관되게 서술되지만, EP2에서 박성호가 "미래증권" 소속으로 명시된 것과 충돌. EP5-6 내에서는 한미증권으로 일관되므로 자체적 모순은 없으나, M-3-001의 연장선.

---

### Project 1 Summary

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| IMPORTANT | 4 |
| MINOR | 2 |
| **Total** | **7** |

**가장 심각한 문제**: 박성호의 소속 증권사가 EP2에서는 "미래증권"이고 EP5에서는 "한미증권"으로 변경된 것. 이는 모든 독자가 즉시 인지할 수 있는 명백한 설정 오류.

---

## Project 2: `projects/기록용/00_test_00_before_p1_rerun_20260311_182925/project_data.db`

### Project Info

| Field | Value |
|---|---|
| DB Path | `projects/기록용/00_test_00_before_p1_rerun_20260311_182925/project_data.db` |
| Episodes | 6 (EP 1-6) |
| Total Characters | ~29,830 chars |
| Created | 2026-03-11 06:03 ~ 07:27 |
| Genre | Investment/Regression (same premise as Project 1, different execution) |

### Episode Titles

| EP | Title | Chars |
|---|---|---|
| 1 | 재가 된 남자의 선언 | 4,926 |
| 2 | 금빛 족쇄를 끊다 | 5,571 |
| 3 | 첫 번째 칼을 구하다 | 4,790 |
| 4 | 전장의 서막 | 5,207 |
| 5 | 제5화 | 5,151 |
| 6 | 루비콘 강을 건너다 | 4,185 |

### Fact Tracking Table

#### Characters

| Character | EP Introduced | Role | Key Details |
|---|---|---|---|
| 한시우 | EP1 | Protagonist (regression) | 스물여섯, 44세에서 회귀, 승마 선수 출신, 한정호의 아들 |
| 한정호 | EP1 | Father, Chairman | 한영그룹 회장, 서재에 마호가니 문, 시가+위스키 |
| 김 집사 | EP1 | Butler | 인터폰으로 서재 호출 전달 |
| 유진우 | EP1-3 | Strategic ally | 한영그룹 전략기획실 팀장 → 한시우의 파트너, 서른 중반 |
| 박성호 | EP2-6 | Finance/PB | 한미증권 팀장, 한시우의 자산 관리인 (아버지가 붙여준 사람) |

#### Assets/Money

| Fact | EP | Detail |
|---|---|---|
| 한시우 초기 자산 | EP1 | 19억 5천만 원 (할아버지 유산 + 어머니 비상장 주식 + 선수 시절 수입) |
| SW인베스트먼트 자본금 | EP3-4 | 19억 5천만 원 |
| 유진우 지분 제안 | EP3 | 법인 지분 10% (~2억 원) |
| 블룸버그 터미널 | EP4 | 2대, 연 사용료 수천만 원 |
| WTI 매수 | EP5 | 15억 원, 3배 레버리지, 시장가 매수 |
| 잔여 자금 | EP5 (implied) | 19.5억 - 15억 = 4.5억 (장비+사무실 비용 등) |

#### Locations

| Location | EP | Detail |
|---|---|---|
| 한시우 방 (성북동 저택) | EP1-2 | 2층, 값비싼 가구, 대리석 바닥 |
| 한정호 서재 | EP1 | 마호가니 문, 책 냄새, 시가 연기, 대리석 바닥 |
| 거실 (저택) | EP2 | 벽걸이 TV, 가죽 소파, 대리석 바닥, 높은 천장 |
| 최고급 호텔 스카이라운지 | EP3 | 서울 중심, 유진우와 첫 대면 |
| 한영그룹 본사 전략기획실 | EP3 | 유진우 사무실, 통유리창 |
| SW인베스트먼트 사무실 | EP4 | 여의도 빌딩 최상층, 국회의사당+한강 view, 대리석 바닥 |
| 한미증권 VIP룸 | EP5-6 | 마천루, VIP 라운지, 마호가니 테이블, 가죽 소파 |
| 한강공원 벤치 | EP6 | 여의도 강변 |

#### Timeline

| Event | EP | Time Reference |
|---|---|---|
| 회귀 (2006년 1월) | EP1 | 달력에 "2006년 1월" |
| 서재 대면 | EP1 | 회귀 당일 오전 |
| 아버지 유진우 호출 | EP1 | 서재 대면 직후 |
| 박성호에게 자산 처분 전화 | EP2 | 같은 날 |
| 거실에서 이란 핵 뉴스 확인 | EP2 | 같은 날 저녁 |
| 검은 세단 습격 (저택 앞) | EP2 | 같은 날 밤 |
| 유진우 전화 통화 (차 안) | EP3 | 같은 밤 |
| 호텔 스카이라운지 미팅 | EP3 | 같은 밤 |
| 한영그룹 본사 방문 (자정 전) | EP3 | 같은 밤 자정 |
| 파트너십 계약 체결 | EP3-4 | 자정 무렵 |
| 법인 설립 완료 | EP4 | "며칠 후" |
| 블룸버그 터미널 설치 | EP4 | 법인 설립 후 "사흘 뒤" |
| 이란 핵 속보 발생 | EP4 | 터미널 설치 당일 |
| 박성호에게 전화 (자정) | EP5 | 속보 직후 |
| 한미증권 VIP룸 | EP5 | 30분 후 |
| WTI 매수 실행 | EP5 | 즉시 |
| 서킷브레이커 발동 | EP5-6 | 매수 직후 |
| 유진우 새벽 전화 | EP6 | 수익 확인 후 새벽 |

### Contradictions Found

---

#### [M-1-002] CRITICAL: 박성호의 직급 불일치 (팀장 vs 차장)

- **Type**: M-1 (Character Setting Contradiction)
- **Severity**: CRITICAL
- **Episodes**: EP2 vs EP5-6

**EP2 (팀장):**
> "주소록을 뒤져 '박성호 팀장 - 한미증권'이라는 이름을 찾아냈다."
> "박 팀장, 내 계좌에 있는 것들 전부 처분해."

**EP4 (팀장):**
> "품에서 2006년형 폴더 휴대폰을 꺼내 단축번호를 눌렀다. 신호음이 몇 번 울리지 않아 익숙한 목소리가 들려왔다. 박성호 팀장이었다."
> "박 팀장님은 그저 제 지시를 정확히 이행하기만 하면 됩니다."

**EP5 (팀장 유지):**
> "[박성호 팀장 - 한미증권]"
> "박 팀장. 내가 지금 농담하는 것 같나?"

**EP6 (팀장):**
> "박 팀장님."

**Assessment**: Project 2에서는 박성호의 직급이 "팀장"으로 전 에피소드에 걸쳐 일관된다. 그러나 Project 1에서는 같은 이름의 캐릭터가 "차장"으로 설정되어 있어 두 프로젝트 간 불일치가 있다. **Project 2 내부에서는 직급이 일관되므로 내부 모순은 아니다.** CRITICAL에서 하향 조정.

**Revised Severity**: N/A (내부 모순 아님, 프로젝트 간 차이)

---

#### [M-1-003] CRITICAL: 한시우의 자본금 금액 불일치

- **Type**: M-1 (Character Setting / Asset Contradiction)
- **Severity**: CRITICAL
- **Episodes**: EP1 vs EP3-4

**EP1 (19억 5천만 원):**
> "전부 끌어모으면 19억 5천만 원. 20억에는 조금 못 미치지만, 시작하기엔 충분한 돈이었다."

**EP3 (19억 5천만 원 유지):**
> "자본금 19억 5천만 원짜리 투자 법인입니다."

**EP4 (19억 5천만 원 유지):**
> "19억 5천만 원, 전액 입금 확인했습니다."

**Assessment**: Project 2 내부에서 자본금은 19억 5천만 원으로 일관된다. 내부 모순 없음.

**Revised Severity**: N/A (내부 모순 아님)

---

#### [M-1-004] IMPORTANT: 유진우의 직함/역할 불일치 (팀장 vs 변호사)

- **Type**: M-1 (Character Setting Contradiction)
- **Severity**: IMPORTANT
- **Episodes**: EP1-3 vs EP4, EP6

**EP1 (전략기획실 팀장):**
> "'유진우 팀장 좀 연결해.'"
> "그룹 전략기획실 소속의 에이스."

**EP2 (전략기획실 팀장):**
> "유진우. 전생에서 아버지의 가장 유능한 수족이자, 결국 그룹의 핵심 계열사를 장악했던 남자."

**EP3 (유진우 팀장):**
> "유진우 팀장님이십니다."
> 한시우가 유진우에게 법인 설립 + 조세회피처 회사 설립을 의뢰

**EP4 (유 변호사님):**
> "유진우 변호사님께도 확인 서류 보내드렸습니다."
> 한시우가 유진우를 "유 변호사님"으로 호칭

**EP5 (변호사):**
> "유진우 님과의 계약서상 첫 자금 집행에는 서명이 필요합니다!"

**EP6 (변호사):**
> "유진우 변호사입니다만."

**Explanation**: 유진우는 EP1-3에서 "한영그룹 전략기획실 팀장"으로 소개되지만, EP4부터는 "변호사"로 호칭이 변경된다. 전략기획실 팀장이 법인 설립을 대행하고 변호사로 불리는 것은 직업적 정체성에 명백한 혼선을 준다. 그룹을 나와 한시우의 변호사로 전환한 것인지, 아니면 원래 변호사 자격이 있는 사람이 전략기획실에 있었던 것인지 설명이 없다. 주의 깊은 독자라면 "팀장이 왜 갑자기 변호사가 되었는가?"라고 의문을 가질 수 있다.

---

#### [M-4-002] IMPORTANT: WTI 매수 금액과 총 자본금 간 비정합성

- **Type**: M-4 (Asset Contradiction)
- **Severity**: IMPORTANT
- **Episodes**: EP4 vs EP5

**EP4 (자본금 19억 5천만 원, 전액 입금):**
> "19억 5천만 원, 전액 입금 확인했습니다."
> 사흘 뒤 블룸버그 터미널 2대(연 억대) + 최고 사양 컴퓨터/서버 + 다중 모니터 설치 (수억 원)

**EP5 (15억 매수):**
> "3배 레버리지. 15억. 지금 당장, 시장가로 전부 매수."

**Explanation**: 총 자본금 19.5억에서 장비 구매(블룸버그 터미널 2대 연간 억대 + HTS 서버 + 모니터 시스템 = 수억)를 제외하면 15억은 산술적으로 합리적이다. 그러나 EP4에서 설치기사가 "이 정도 사양... 개인이 이 정도 시스템"이라고 할 만큼의 장비가 자본금에서 차감된 것에 대한 명시적 회계 서술이 없다. 독자는 "19.5억 전부를 투자하지 않나?"라고 기대할 수 있으며, 15억만 매수하는 것에 대한 설명이 부재하다.

---

#### [M-6-003] IMPORTANT: EP4-5 연결부 시간 불일치

- **Type**: M-6 (Event Continuity)
- **Severity**: IMPORTANT
- **Episodes**: EP4 vs EP5

**EP4 (ending):**
> 이란 핵 속보가 블룸버그 터미널에 떠오르고, "폭풍 전의 고요. 첫 번째 사냥감은 이미 조준경 안에 들어와 있었다."로 끝남

**EP5 (opening):**
> "붉은색 속보가 깜빡이는 모니터 불빛만이 내 얼굴을 비추고 있었다." (EP4 마지막 문장과 거의 동일)
> "나는 1초의 망설임도 없이 책상 위에 놓인 2006년형 폴더 휴대폰을 집어 들었다."
> 박성호에게 전화 → "30분 안에 VIP룸 문을 열어두지 않으면"
> "30분 뒤, 한미증권 본사 빌딩 앞에 도착했다."

**Explanation**: EP4 마지막 장면에서 한시우는 여의도 SW인베스트먼트 사무실(EP4: "여의도의 한 빌딩 최상층")에 있다. EP5에서 그가 박성호에게 "30분 뒤 VIP룸"이라고 하고 실제 30분 만에 한미증권에 도착한다. 같은 여의도 내이므로 이동 시간은 합리적이나, EP4의 속보 타이밍이 사무실 장비 설치 당일인지, 이후인지 명확한 시간 지시자가 없다. EP4 내에서 "며칠 후" 사무실 입주 → "사흘 뒤" 장비 설치 → 설치 "당일" 속보라고 읽히므로 시간 흐름 자체는 모순이 아니나, EP4-5 경계에서 중복 서술이 불필요한 혼란을 줄 수 있다.

---

#### [M-1-005] IMPORTANT: 한시우의 과거/회귀 연령 세부사항

- **Type**: M-1 (Character Setting)
- **Severity**: MINOR
- **Episodes**: EP1

**EP1:**
> "44살의 내가 살던 반지하 단칸방"
> "이것은 스물여섯, 승마로 다져졌던 내 젊은 몸이었다."
> "18년 치의 삶이 압축된 듯한 지독한 두통"
> "'2006년 1월'"
> "2024년의 겨울, 차가운 단칸방에서 마지막 숨을 내뱉던"

**Calculation**: 26세 (2006) + 18년 = 44세 (2024). 일관됨.

**Assessment**: 내부 모순 없음. 수치가 정확히 맞는다.

**Revised Severity**: N/A (모순 아님)

---

#### [M-4-003] MINOR: 한시우 자본금의 출처 세부사항

- **Type**: M-4 (Asset)
- **Severity**: MINOR
- **Episodes**: EP1

**EP1:**
> "할아버지의 유산과 어머니가 남겨주신 비상장 계열사 주식, 그리고 선수 시절 벌어두었던 돈. 전부 끌어모으면 19억 5천만 원."

**Comparison with Project 1 EP1:**
> "제 명의로 된 모든 자산을 정리할 겁니다. 청담동 오피스텔, 보유 주식, 회원권까지 전부. 대략 20억 정도가 될 겁니다."

**Explanation**: 두 프로젝트 간의 차이이지, Project 2 내부 모순은 아님. 다만, Project 2에서 한시우가 "승마 선수 출신"이라는 설정은 EP1에서만 언급되고 이후 에피소드에서는 전혀 언급되지 않아, 설정이 활용되지 않는 잉여 설정에 해당한다.

---

#### [M-6-004] MINOR: 유진우와의 계약에서 "조세회피처 유령회사" 설정의 소멸

- **Type**: M-6 (Event Continuity)
- **Severity**: MINOR
- **Episodes**: EP3 vs EP4

**EP3:**
> "조세회피처에 서류상으로만 존재하는 유령 회사로 만들어 주십시오."

**EP4:**
> "'SW 인베스트먼트'. 내 이름의 첫 글자 S와 승리(Win)를 의미하는 W."
> 법인 인감, 정관 서류철, 법인카드를 수령
> 여의도에 물리적 사무실 입주, 블룸버그 터미널 설치

**Explanation**: EP3에서 한시우는 "조세회피처에 서류상으로만 존재하는 유령 회사"를 만들어 달라고 요청했으나, EP4에서 SW인베스트먼트는 국내 법인(여의도에 실체 사무실 보유)으로 운영된다. 유령회사 요청이 별도의 해외법인에 대한 것이었는지, 계획이 변경된 것인지 설명이 없다.

---

### Project 2 Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| IMPORTANT | 3 |
| MINOR | 2 |
| **Total** | **5** |

**가장 심각한 문제**: 유진우의 직함이 EP1-3에서 "전략기획실 팀장"이었다가 EP4부터 "변호사"로 변경되는 것. 독자가 혼란을 느낄 수 있는 설정 오류.

---

## Cross-Project Comparison (참고)

이 섹션은 두 프로젝트의 동일 시나리오에 대한 다른 실행 방식을 비교 참고용으로 정리한다. 이는 "모순"이 아니라 두 버전의 "설정 차이"이다.

| Fact | Project 1 (000) | Project 2 (기록용) |
|---|---|---|
| 자본금 | 20억 | 19억 5천만 원 |
| 자산 출처 | 청담동 오피스텔+주식+회원권 | 할아버지 유산+어머니 비상장주식+선수 수입 |
| 박성호 소속 | 미래증권(EP2)/한미증권(EP5) | 한미증권 (일관) |
| 박성호 직급 | 차장 | 팀장 |
| 변호사 | 이준영 (법무법인 '정인') | 유진우 (한영그룹→파트너) |
| 유진우 존재 | 없음 | 핵심 캐릭터 |
| 아버지의 조건 | "재롱이 길지는 말거라" (시간제한 없음) | 1년 기간 제한 |
| 형의 이름 | 한태민 (둘째 형) | 명시적으로 등장하지 않음 |
| 회귀 연령 | "18년의 지옥" (구체 연령 불명) | 26세←44세, 18년 |
| 서술 시점 | 3인칭 + 1인칭 내면 혼합 | 주로 1인칭 |
| EP4-5 경계 | 태산그룹 법적 압박 | 이란 핵 속보 → 즉시 매수 |
| 노트북 설정 | 2006년형 구형 (셀프스토리지) | 2006년형 구형 (방 서랍) |
| 비밀거점 | 강변 오피스텔 35층 (EP6) | 해당 없음 |
| 전투 능력 | EP6에서 2명 제압 (격투) | 해당 없음 |

---

## Final Summary

### Project 1 (`000`)
- **CRITICAL 1건**: 박성호 소속 증권사 불일치 (미래증권 vs 한미증권)
- **IMPORTANT 4건**: EP4-5 중복 서술, 노트북 행방, 법인 계좌 개설 주체, 변호사 역할 범위
- **MINOR 2건**: 한태민 정보 획득 속도, 증권사 위치 연계

### Project 2 (`기록용`)
- **CRITICAL 0건**
- **IMPORTANT 3건**: 유진우 직함 변경 (팀장→변호사), WTI 매수 금액 산술, EP4-5 연결부 중복
- **MINOR 2건**: 조세회피처 유령회사 설정 소멸, 승마 선수 설정 미활용

### Overall Assessment
Project 2가 Project 1보다 내적 일관성이 높다. Project 1의 가장 큰 문제는 박성호의 소속 증권사가 에피소드 중간에 바뀌는 CRITICAL 오류로, 즉시 수정이 필요하다. Project 2의 유진우 직함 변경은 IMPORTANT이나 내러티브 흐름에서 심각한 파괴를 일으키지는 않는다.

---

*Report generated by TF-D, Claude Opus 4.6 (1M context), 2026-03-16*
