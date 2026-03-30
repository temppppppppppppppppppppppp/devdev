# T1 Blockguide Calibration Lane — Protagonist-First TR-BI Pair Survey

Date: 2026-03-30
Lane: T1
Family: blockguide
Reviewer: Terminal 1
Status: final (3-pass audited)

---

## Work 1: `chaebol_ent_empire`

### TR Survey

**Windows inspected:**
- Blocks 1-10 (초기 출발~청산 위기 탈출)
- Blocks 30-32 (middle stress: 첫 업계전쟁 결산)
- Blocks 61-70 (권력전~산업 표준 완성)

#### R1. Protagonist Reward Visibility — GREEN

매 블록 성취 직후 가시적 보상이 존재한다.
- Block 1: 120억 조건부 자본과 결정권 확보. 비웃음 속에서도 "판을 처음 손에 쥔다"로 마감.
- Block 3: 미수금 회수 후 자본 +8억. 오지혁의 인정 전환("직접 뛰는 인간").
- Block 30: 업계가 세령컬처웍스를 "불편한 신흥 세력"으로 인정, 서민재의 전략 파트너 확정.
- Block 68: 폭로 후 자본 +1062억. 한도윤 명분 붕괴.
- Block 70: 6800억. 업계 표준.

성취 후 인정/보상이 빠진 블록을 찾지 못했다.

#### R2. Reward Dwell Time — GREEN

보상을 받은 뒤 일정 구간 활용/향유가 허락된다.
- Block 7-8 쇼케이스 성공 → Block 9-10에서 투자 유치 및 청산 보류까지 이어짐. 보상이 즉시 박탈되지 않음.
- Block 30 업계전쟁 승리 → Block 31-32에서 그 위세로 라이브/포맷 실험을 여는 확장 구간.
- Block 68 시장 폭로 대역전 → Block 69 자체 플랫폼 런칭까지 승기를 이어감.

**유일한 긴장 지점:** Block 4 "첫 패배"에서 15억 손실. 그러나 이 패배조차 태하에게 "누군가 설계한 흐름"이라는 인사이트를 선물하고, Block 5에서 곧바로 학습→재기 패턴으로 전환. 순수 박탈이 아니라 "알고 보면 성장 재료"형 고통.

#### R3. Pain Aesthetic — GREEN

고통은 있으나 항상 aspirational/cool/growth-bearing.
- Block 4: 파일럿 실패 → 감각만으론 부족하다는 배움. 멋있는 패배("누군가 설계한 흐름"이라는 첫 의심).
- Block 63: 경영권 탈취 → 처참하지만 "개인이 아니라 구조에 대한 복수"로 목표가 격상. 무기력/모욕에 머무르지 않고 즉시 반격 동기로 전환.
- Block 55 (pyrrhic victory): 글로벌 성공의 대가로 마커스 리 독점 → 이 역시 구조적 교훈으로 전환, Block 57-58에서 독점 탈피.

helpless나 bleak에 머무르는 블록이 없다.

#### R4. Vector Direction — GREEN

겉보기 punitive 상황의 deeper vector가 항상 보호적/전략적/역전 준비형.
- Block 1: 쓰레기통 회사 떠넘기기 → 알고 보면 태하에게 자기 이름으로 판을 열 최초 기회.
- Block 63: 빼앗기는 날 → 같은 블록 reward에서 "구조를 상대로 복수해야 한다는 명확한 인식" 획득. frustration만으로 끝나지 않음.
- Block 61-62: 축하가 끝난 자리의 긴장감 → 태하가 먼저 구조를 읽고 방어를 시작하는 주도성.

독자의 dominant emotion이 pure frustration으로 남는 블록이 없다.

#### R5. Exclusive Protagonist Engine — GREEN

"스타 감지" — 사람의 터질 타이밍을 읽고 맞는 자리에 배치하는 선천적 감각. 이 능력은 권태하만이 가진 unique engine이며 전 블록에서 일관되게 작동한다.
- 초기: 강이현, 윤서아 발굴
- 중기: 다중 자산 조합 설계(Block 30)
- 후기: 산업 구조의 방향을 읽는 힘으로 확장(Block 70)

다른 인물이 이 engine을 대체할 수 없다.

#### R6. Genre Contract Stability — GREEN

"no-romance / business-power / 엔터 IP 성장물" 계약을 Block 70까지 일관되게 유지.
- 로맨스 라인 zero.
- 모든 갈등이 사업/권력/구조적 축으로 처리됨.
- 마지막도 "인정이 아니라 표준"으로 마감. 개인 화해가 아닌 산업 변혁.

#### R7. BI Amplification — 판정 아래

### BI Survey

**Sections inspected:**
- `ProjectData.CoreIdentity`
- `protagonist_config`
- `FinanceHUD.Protagonist.actual_truth` + `public_reputation`
- `GenreRules`
- `plot_roadmap` sample (Block 1, Block 30, Block 70 aligned)
- `AssetLibrary.KeyNPCs`
- `npc_timeline`
- `portfolio_history`

#### BI Protagonist-First Encoding — GREEN

CoreIdentity:
- `edge`: "스타 감지 — 사람의 터질 타이밍을 읽고 맞는 자리에 배치하는 선천적 감각"으로 protagonist engine을 정확히 명시.
- `desire`: "시장이 따라 하는 구조를 남긴다"로 최종 목표를 protagonist-only 승리로 인코딩.
- `evolution`: 7 phase에 걸친 protagonist power progression이 명확.

FinanceHUD:
- 120억 → 6800억까지 `portfolio_history`로 자본 궤적을 12개 milestone로 추적. TR 블록과 1:1 정합.
- `actual_truth`에 ip_assets, business_lines를 구체적으로 열거.

GenreRules:
- `rule_no_regression_mechanic: true` — TR과 일치.
- `rule_talent_discovery_drives_plot`, `rule_defeat_creates_structure_upgrade` 등 protagonist engine을 규칙 수준에서 보장.

KeyNPCs:
- 13명 전원이 protagonist과의 관계와 final_state가 개별화되어 있음.
- `npc_timeline`에서 entry/turning/final block이 명시.

plot_roadmap:
- TR 본문을 거의 동일하게 반영. Block 1, Block 30, Block 70의 content/reward가 TR과 일치.

**단점:** `plot_roadmap`이 TR 블록을 상당히 그대로 복제한 구조. BI 고유의 추가적 protagonist leverage 인코딩(예: 블록별 protagonist power tier, 누적 reward balance 등)은 plot_roadmap 밖에서 `portfolio_history`와 `evolution`으로 커버되지만, roadmap 자체는 TR mirror에 가까움.

#### R7. BI Amplification — YELLOW-GREEN

BI는 TR을 단순 echo하지 않는다. `FinanceHUD`, `portfolio_history`, `npc_timeline`, `evolution`, `GenreRules`에서 protagonist engine을 TR 이상으로 구조화한다. 그러나 `plot_roadmap` 섹션 자체는 TR block body의 고충실 복사에 가까워, BI 고유의 roadmap-level protagonist power tracking(예: 블록 구간별 "현재 protagonist leverage tier")은 부재. 전체적으로 TR protagonist-first를 강하게 강화하나 roadmap 구간에서 약간의 thin-echo 성격이 남는다.

### TR Verdict: GREEN

- R1-R6 전항목 GREEN.
- 70블록 전구간에서 protagonist reward visibility, dwell, aesthetic, vector, engine, contract가 일관.

### BI Verdict: GREEN

- CoreIdentity, FinanceHUD, GenreRules, KeyNPCs, npc_timeline에서 protagonist engine을 TR 이상으로 구조화.
- plot_roadmap의 thin-echo 경향은 존재하나 나머지 섹션에서 충분히 보상.

### Pair Verdict: GREEN

- TR이 protagonist-first를 70블록 내내 유지하고, BI가 그것을 재무/NPC/규칙 레벨에서 재확인하며 물질적으로 강화.
- 가장 약한 지점(Block 63 경영권 탈취)조차 같은 블록 내에서 반격 동기 부여로 전환. 순수 처벌 zero.

### Strongest Confirming Evidence

Block 68 "시장을 움직이는 폭로" — 장부/법무/IR/팬덤 여론을 한 타이밍에 묶어 공신 라인을 무너뜨리는 설계된 역전. capital +1062억. 가장 극적인 고통(Block 63 경영권 탈취) 이후 가장 극적인 보상. 둥기둥기 FIRST의 교과서적 실현.

### Strongest Violating Evidence

Block 4 "첫 패배" — 파일럿 실패로 15억 손실, 윤서아 공포 회귀. 성취 직후 패배가 오는 유일한 블록. 그러나 같은 블록의 reward에서 "우연이 아니라 설계된 흐름이라는 첫 의심"이라는 인사이트 보상이 주어지고, Block 5에서 즉시 회복 경로가 열린다. 순수 처벌로 끝나지 않으므로 drift로 분류하지 않음.

---

## Work 2: `투자물_골든_카나리아 테스트`

### TR Survey

**Windows inspected:**
- Blocks 1-10 (회귀 선언~카운트다운)
- Blocks 30-31 (middle stress: 비트코인 정점 + 크립토 윈터)
- Blocks 55-60 (ETF 승인~골든 루트 해피엔딩)

#### R1. Protagonist Reward Visibility — GREEN

매 블록 성취 후 가시적 보상이 명확.
- Block 1: 20억 자산 정리 + 법인 설립. 가족 무관심이 "레이더 밖"이라는 전략적 이점으로 전환.
- Block 2: WTI 롱 진입 → 이란 핵 발표 → 15억→18억. PB 박성호의 태도 전환.
- Block 30: BTC 고점 당일 10조 익절. 아버지 수술비 50억 → 아버지의 "시우야... 고맙다." 첫 진지한 인정.
- Block 55: ETF 승인 직후 부분 익절 → 102조.
- Block 60: 135조. 가족과 함께 새해. "게임 클리어."

보상이 빠지거나 지연되는 블록이 단 하나도 없다.

#### R2. Reward Dwell Time — GREEN

이 작품은 보상 체류가 극도로 강함.
- Block 30 익절 10조 → Block 31 크립토 윈터에서 현금 10조를 쥐고 "포식자의 인내"로 기다리는 구간. 보상이 박탈되지 않고 다음 공격의 실탄으로 변환.
- Block 55 ETF 승인 익절 → Block 56 정점에서 추가 35조 익절 → 64조 현금으로 다시 재무장. 보상이 빼앗기지 않고 누적.
- Block 59-60: 135조를 유지하며 가족과 함께하는 마감. 최종 보상이 충분히 체류.

#### R3. Pain Aesthetic — GREEN

고통이 거의 없다는 것이 이 작품의 특성. 존재하는 고통은 전부 aspirational.
- Block 30: 아버지 심근경색 → 이것조차 한시우가 50억 수술비를 낸다는 "가진 자의 구원" 패턴. 고통이 아니라 인정 획득 기회.
- Block 47 (제이슨 배신): 조사 대상에서 확인 → 중반 tension이지만 한시우의 판단 정확성을 재확인하는 장치.
- 전반적으로 protagonist이 심각하게 고통받는 블록이 없음. 회귀 지식 덕에 거의 모든 위험을 사전 회피.

#### R4. Vector Direction — GREEN

punitive surface 자체가 극히 드물고, 있을 때도 deeper vector는 항상 역전 준비.
- 가족 무관심 → "레이더 밖에서 움직이는 게 유리하니까" (Block 1)
- 크립토 윈터의 공포 → "포식자의 인내" (Block 31)
- 형들의 가문 몰락 → 한시우의 방화벽과 독립이 빛나는 배경 (Block 40-59)

독자가 frustration/unfairness를 느낄 지점이 없다.

#### R5. Exclusive Protagonist Engine — GREEN

"18년치 경제 캘린더 기억 + 출구 설계 감각 + 통제권 집착" — 회귀 지식을 기반으로 한 protagonist-only engine.
- WTI, 리먼 CDS, 비트코인, 테슬라, 엔비디아, ETF까지 전 구간에서 작동.
- 다른 인물이 대체 불가. 마이클 첸, 박성호, 제이슨 모두 한시우의 지시를 따르는 위치.
- regression_ext가 매 블록 인코딩되어 engine의 source(전생 기억)와 정확도가 일관.

#### R6. Genre Contract Stability — GREEN

"투자 + 회귀 + 패밀리오피스 통제권 장악물" 계약을 Block 60까지 완벽 유지.
- 로맨스 zero.
- 모든 갈등이 자본/시장/가족 통제권 축.
- 마지막 Block 60도 "돈이 아니라 반복을 끊어낸 것"이라는 투자물 고유의 closure.

#### R7. BI Amplification — 판정 아래

### BI Survey

**Sections inspected:**
- `ProjectData.CoreIdentity`
- `protagonist_config`
- `FinanceHUD.Protagonist.actual_truth` + `public_reputation`
- `GenreRules`
- `plot_roadmap` sample (Block 1, Block 30, Block 60 aligned)
- `WorldState`
- `KarmaMatrix`

#### BI Protagonist-First Encoding — GREEN

CoreIdentity:
- `edge`: "18년치 경제 캘린더 기억 + 과열과 붕괴에서 출구를 먼저 설계하는 감각 + 가족 부실을 조건부로만 받는 통제권 집착" — TR engine과 정확히 일치.
- `desire`: "남의 실패를 대신 갚지 않는 자기 제국" — protagonist-only 목표.

FinanceHUD:
- 20억 → 135조까지 `portfolio_history`로 10개 milestone 추적. TR과 1:1 정합.
- `investment_style`, `risk_tolerance`, `governance_doctrine`이 protagonist 성격을 재무 규칙으로 인코딩.

GenreRules:
- `reward_rule`: "승리는 현금 증가, exit 정확도, 외부 인정, 통제권 강화의 네 층위로 측정" — protagonist reward를 4축으로 구조화.
- `must_include`에 "자본 변화와 통제권 변화가 매 블록마다 읽혀야 한다" 명시.
- `forbidden`에 "이유 없는 자선이나 손해 감수로 주인공을 미화하는 전개" — protagonist-first reward logic 보호.

WorldState + KarmaMatrix:
- 13명의 NPC relation_score와 final_state가 개별화.
- `economic_context`에 현재 시장 상태와 locked_in_advantages가 protagonist 입장에서 정리.

plot_roadmap:
- TR 본문의 고충실 반영. Block 1, 30, 60의 content/reward가 TR과 동일.

#### R7. BI Amplification — GREEN

chaebol_ent_empire보다 BI amplification이 강하다.
- `GenreRules.reward_rule`이 protagonist reward를 4축(현금/exit/인정/통제권)으로 명시적으로 인코딩 — TR에는 없는 BI 고유의 구조적 가치.
- `GenreRules.forbidden`이 protagonist-first 위반 패턴을 5개 명시적으로 차단.
- `governance_doctrine`, `secrecy_rule`이 protagonist edge를 규칙 레벨에서 보호.
- `KarmaMatrix`가 protagonist과 전 NPC의 관계를 점수화하여 power 위치를 즉시 파악 가능.
- plot_roadmap은 TR mirror이나, 나머지 섹션에서의 protagonist-first 구조화가 chaebol보다 한 단계 더 두텁다.

### TR Verdict: GREEN

- R1-R6 전항목 GREEN.
- 60블록 전구간에서 protagonist reward가 단 한 번도 빠지지 않음.
- 고통 자체가 극히 적고, 있을 때도 aspirational/growth-bearing.

### BI Verdict: GREEN

- GenreRules.reward_rule 4축, forbidden 5항, governance_doctrine, secrecy_rule이 protagonist engine을 TR 이상으로 강하게 인코딩.
- KarmaMatrix의 NPC 관계 점수화가 protagonist power position을 구조적으로 보장.

### Pair Verdict: GREEN

- TR이 60블록 전구간에서 protagonist reward를 빠짐없이 제공하고, BI가 그것을 규칙/4축 reward/forbidden 리스트로 제도적으로 강화.
- 가장 약한 지점을 찾는 것 자체가 어려울 만큼 protagonist-first가 강고.

### Strongest Confirming Evidence

Block 30 "정점" — BTC 고점 당일 10조 익절 + 아버지 수술비 50억 + "시우야... 고맙다." 돈(10조 익절), 인정(아버지의 첫 진지한 감사), 통제(고점에서 파는 완벽한 타이밍), 관계(형들을 씁쓸하게 만드는 역전)가 한 블록에서 동시 달성. `GenreRules.reward_rule`의 4축이 한 블록에서 전부 실현되는 교과서적 장면.

### Strongest Violating Evidence

없음. protagonist-first drift로 분류할 블록을 찾지 못했다. 가장 가까운 후보는 Block 47 제이슨 배신이나, 이 역시 한시우의 판단 정확성과 통제력을 재확인하는 장치로 기능하며 protagonist에게 실질적 피해가 없다.

---

## Comparison Note

| 항목 | chaebol_ent_empire | 골든_카나리아 |
|------|-------------------|-------------|
| TR protagonist-first 일관성 | GREEN (극히 강함) | GREEN (극히 강함) |
| 고통의 존재/질 | Block 4, 63 등에서 의미 있는 패배가 존재하나 모두 growth-bearing | 고통 자체가 극히 적음. 회귀 지식이 거의 모든 위험을 사전 제거 |
| Reward Dwell | 보상 후 확장/활용 구간이 잘 배치됨 | 보상이 빼앗기지 않고 끊임없이 누적되는 구조 |
| BI Amplification | FinanceHUD/NPC timeline 강함, plot_roadmap은 TR mirror 경향 | GenreRules.reward_rule 4축 + forbidden 5항이 추가로 protagonist engine을 제도적으로 보호 |
| Protagonist engine | "스타 감지" — 선천적 감각 기반, 비회귀 | "회귀 캘린더 + 출구 설계" — 회귀 지식 기반 |
| Genre contract | 엔터 IP 성장물 계약 70블록 유지 | 투자 + 회귀 + 통제권 계약 60블록 유지 |

**어느 pair가 protagonist-first를 더 잘 보존하는가?**

둘 다 GREEN이지만, 질이 다르다.
- `chaebol_ent_empire`는 의미 있는 패배(Block 4, 63)를 포함하면서도 protagonist-first를 지키는 더 어려운 과제를 성공적으로 수행. Pain aesthetic과 vector direction에서 더 풍부한 증명을 보여줌.
- `골든_카나리아`는 protagonist-first 위반 가능성 자체를 구조적으로 차단한 설계. 회귀 지식으로 위험을 사전 제거하므로 drift가 발생할 여지가 극히 적음. BI의 GenreRules에서 protagonist reward를 4축으로 명시한 것은 더 강한 제도적 보호.

**reference pair 관점에서:**
- `골든_카나리아`가 "protagonist-first를 위반하기 가장 어려운 구조"의 reference로 적합.
- `chaebol_ent_empire`가 "고통이 있는 서사에서도 protagonist-first를 지키는 방법"의 reference로 적합.

---

## Flat Verdict Blocks

```
lane: T1
work_id: chaebol_ent_empire
family: blockguide
TR verdict: green
BI verdict: green
pair verdict: green
strongest confirming evidence: Block 68 시장 폭로 — 장부/법무/IR/팬덤을 한 타이밍에 묶은 설계된 역전. capital +1062억. Block 63 경영권 탈취 후 가장 극적인 보상. 둥기둥기 FIRST 교과서적 실현.
strongest violating evidence: Block 4 첫 패배 — 파일럿 실패 15억 손실. 그러나 같은 블록에서 "설계된 흐름"이라는 인사이트 보상이 주어지고 Block 5에서 회복 경로 개방. 순수 처벌 아님.
reference pair candidate: yes
```

```
lane: T1
work_id: 투자물_골든_카나리아 테스트
family: blockguide
TR verdict: green
BI verdict: green
pair verdict: green
strongest confirming evidence: Block 30 정점 — BTC 고점 당일 10조 익절 + 아버지 수술 50억 + "시우야... 고맙다." 돈/인정/통제/관계 4축이 한 블록에서 동시 달성. GenreRules.reward_rule의 완벽한 실현.
strongest violating evidence: 없음. protagonist-first drift 블록을 찾지 못함.
reference pair candidate: yes
```

## 3-Pass Self Audit

### Pass 1. Scope Audit

- 본 리포트는 live TR + BI pair survey만 수행했다.
- 코드, 런타임, member authority, patch, promotion, queue, roadmap 어느 것도 건드리지 않았다.
- "주인공 둥기둥기 first" alignment가 유일한 질문이며 그 질문에만 답했다.

### Pass 2. Evidence Audit

- chaebol: blocks 1-10, 30-32, 61-70 TR windows + BI CoreIdentity/FinanceHUD/GenreRules/NPC/plot_roadmap 직접 열독.
- 골든 카나리아: blocks 1-10, 30-31, 55-60 TR windows + BI CoreIdentity/FinanceHUD/GenreRules/WorldState/KarmaMatrix/plot_roadmap 직접 열독.
- rubric R1-R7 전항목을 live JSON body에서 직접 증거를 채취하여 판정.
- stale audit text나 filename reputation에 의존하지 않았다.

### Pass 3. Integrity Audit

- UTF-8 only.
- `docs/2026-03-30/opus-protagonist-first-pair-survey/` 아래 저장.
- queue/temp/execution SSOT/roadmap 어느 것도 생성하지 않았다.
- 두 작품의 verdict를 평균하지 않고 각각 독립 판정 후 comparison note를 추가했다.
