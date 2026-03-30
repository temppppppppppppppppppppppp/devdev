# T3. Wuxia Heavenly Physician Live Lane — Protagonist-First TR-BI Pair Survey

Date: 2026-03-30
Status: final (3-pass audited)
Lane: T3
Reviewer: Opus 4.6 (Terminal 3)
Scope: `wuxia_heavenly_physician` TR-BI pair protagonist-first alignment survey

## 1. Target Pair

| Field | Value |
| --- | --- |
| work_id | `wuxia_heavenly_physician` |
| family | `wuxguide` |
| TR path | `treatments/wuxia_heavenly_physician_tr_block_070_draft.json` |
| BI path | `bible/0_bi_wuxia_heavenly_physician.json` |

## 2. Survey Method

### 2.1 TR Windows Inspected

- **Blocks 1-10** (opening arc): Full read of blocks 1-5, structural scan of 6-10
- **Middle stress window: Blocks 38-43** (스승 사망 → 살침 개안): Selected because this is the deepest protagonist suffering/trauma zone — B38 drops accuracy to 0%, B39 continues incapacity, B40-43 recover through new capability
- **Blocks 61-70** (final arc): Full read of all 10 blocks

### 2.2 BI Sections Inspected

- `ProjectData.CoreIdentity`
- `protagonist_config`
- `MartialHUD.Protagonist.actual_truth` (realm_history, martial_arts, injury_log, faction_status, kill_count_note)
- `MartialHUD.Protagonist.public_reputation`
- `GenreRules` (realm_system, realm_progression, taboo_rules, do_not_fake)
- `plot_roadmap` sample windows aligned to TR windows (blocks 1, 38, 65, 69)

## 3. Rubric Findings

### R1. Protagonist Reward Visibility — GREEN

Every meaningful protagonist success is followed by visible recognition, reward, or leverage.

**Confirming evidence:**

- **B01**: 형 소풍의 경맥 치료 성공 → 의무일체 첫 발현 자각, 소풍이 아군으로 전환, 백무명이 접촉 준비. "사술 의심"이라는 부정적 반응이 있으나, 이것 자체가 주인공의 능력에 대한 인정의 뒤집힌 형태이며, 소풍/혜란이라는 구체적 아군 확보로 보상이 가시적.
- **B10**: 장로회 심판에서 사술 규정을 뒤집고 의무일체를 가문에 인정받음 → 침의 완성 → 혈의 입문. 경지 전환이라는 가시적 보상.
- **B24**: 무림 의선 대회 우승 → "천하 명의의 반열" 진입. 강호 전체에 이름이 알려짐.
- **B46**: 활살일체 통합 → 의성 완성. 살침+활침이라는 이원화 모순 해결.
- **B50**: 아버지 치료 성공 → "잘했다, 소백아." 시리즈 최대 감정 보상. 의신 입문 확정.
- **B66**: 천의 개안 → 침 없이 의념만으로 10명 동시 치료. 1,000명 범위.
- **B69**: 적을 치료하며 승리 → 천의무쌍. 칠성침법 7침 완성.
- **B70**: 천하 유랑 의원. 의무일체 전수. 매화와 함께. 어머니의 유언 성취.

모든 주요 성공 후 보상이 가시적이고 구체적이다.

### R2. Reward Dwell Time — GREEN

보상이 즉시 박탈되지 않고, 최소한의 향유/활용 시간이 보장된다.

**Confirming evidence:**

- **B01 의무일체 발현 → B02-B04**: 3블록에 걸쳐 기초 침술 체화, 매화 파트너 확보, 마을 의원 활동. 첫 발현의 보상이 3블록간 안정적으로 활용됨.
- **B10 침의 완성 → B11 아버지 병**: 경지 전환 직후 1블록은 달성감을 유지하면서 새 위기 진입. 보상이 즉시 박탈되지 않음 — B10에서의 가문 인정이 유지된 채 새 위기.
- **B24 의선 대회 우승 → B25-26**: 명의 반열 진입 후 2블록 동안 명성 활용 (B25 가문 정치에서 위상 활용, B26 약왕곡 쟁탈전에서 명의 지위 활용).
- **B50 아버지 화해 → B51-52**: 아버지와의 화해가 2블록 지속. B51에서도 아버지와의 관계가 안정적으로 유지.
- **B66 천의 개안 → B67-70**: 천의 경지가 4블록간 안정적으로 활용되며 최종전과 에필로그까지 이어짐.

**주의할 점:**

- **B28 과로 경맥 손상, B38 스승 사망, B53 독 중독**: 이 세 지점에서 보상이 급격히 박탈되나, 각각의 박탈에는 서사적 필연성이 있고, 박탈 전에 충분한 dwell time(최소 2-3블록)이 보장됨.

### R3. Pain Aesthetic — GREEN

주인공의 고통이 모두 성장 지향적이며 무협적 미학을 유지한다.

**Confirming evidence:**

- **B01 탈진**: 형을 살리기 위해 자신을 소진 → 의무일체 자각의 대가. 무력한 희생이 아니라 능력 발현의 부작용.
- **B13 아버지 치료 실패**: "내공이 부족하다"는 명확한 성장 방향 제시. 좌절이 아니라 한계 자각.
- **B28 경맥 3개 손상**: 과로의 대가 — 너무 많은 환자를 치료한 결과. "쉬지 않는 의원"이라는 영웅적 과부하.
- **B38 스승 사망**: 가장 고통스러운 블록이나, 엽천수의 유언 "살리는 것만이 의술이 아니다"가 살침 개안의 씨앗. 고통이 성장의 촉매로 기능.
- **B39 침을 잡지 못하는 날들**: 2주간의 불능 상태이나, 매화/소풍/아버지의 지지 속에서 회복. "비참한 무력감"이 아니라 "깊은 상실 후 재기".
- **B43 살침 내공 역류**: 새 기술의 대가. 위험하지만 성장의 동력.
- **B53 좌천명 독 중독**: 적의 함정에 걸렸으나, 화독위공이라는 새 기법 발현의 계기.
- **B63 7침 실패 경맥 파열**: 최종 기술 도전의 실패. 그러나 "내공이 아닌 다른 것"이라는 깨달음의 단서.

모든 고통이 aspirational / growth-bearing. 주인공이 단순히 구타당하거나 모욕당하는 장면 없음. 비살상 원칙(kill_count = 0)이 의원 정체성을 일관되게 유지.

### R4. Vector Direction — GREEN

표면적 좌절의 심층 벡터가 모두 보호적/전략적/반전 준비형이다.

**Confirming evidence:**

- **B02 사술 의심/감시**: 표면=부정적. 벡터=소풍/혜란 아군 확보, 장로회 체계 내에서 생존 전략 학습.
- **B13 아버지 치료 실패**: 표면=좌절. 벡터=독역의 핵심 메커니즘 이해, 치료 동기 극대화.
- **B38-39 스승 사망/불능**: 표면=최대 고통. 벡터=살침 개안의 씨앗. "의술은 살리는 것만이 아니다"라는 경지 전환의 열쇠.
- **B45 큰형 전사/백무명 퇴장**: 표면=상실. 벡터=활살일체 통합의 감정적 연료 (B46).
- **B53 독 중독**: 표면=적에게 당함. 벡터=화독위공 발현, 내공 재도약의 근간.
- **B63 7침 실패**: 표면=최악의 부상. 벡터=정(情)의 침 깨달음의 직접 촉매 (B65).

독자 감정이 "억울함/부당함"으로 끝나는 블록이 없다. 모든 좌절 블록이 2-3블록 내에 반전/보상으로 연결됨.

### R5. Exclusive Protagonist Engine — GREEN

주인공만의 고유한 이점/정보 격차/전환 엔진이 견고하다.

**Confirming evidence:**

- **의맥(醫脈)**: 어머니에게 이식받은 선천적 기반. 침술로 내공을 발현하는 유일한 체질. 다른 인물로 대체 불가.
- **의무일체 경지 체계**: 침의→혈의→맥의→신의→의성→의신→천의. 7단계 경지가 모두 주인공의 고유 특성(의맥+의념)에 기반. 타인이 동일 경로를 걸을 수 없음(백무명 제외, 그러나 백무명은 B45에서 퇴장).
- **독역 치료 독점**: 독역은 내공이 높을수록 치명적 → 일반 무인/의원으로는 치료 불가 → 의무일체만이 독역을 근본 치료 가능. 세계관 위기가 주인공 고유 능력과 완벽하게 맞물림.
- **비살상 전투 철학**: kill_count = 0. "적을 치료하며 이기다"(B69). 이 철학 자체가 주인공만의 전투 방식이며, 최종전의 승리 조건.
- **정(情)의 침**: 천의 개안의 열쇠가 "감정"이라는 점에서, 70블록에 걸친 주인공의 모든 관계와 경험이 최종 기술의 재료. 타인이 대체 불가.

주인공을 빼면 이야기가 완전히 붕괴함. 엔진 독점도 극도로 높음.

### R6. Genre Contract Stability — GREEN

무협/의술 무협이라는 장르 계약을 70블록간 일관되게 유지한다.

**Confirming evidence:**

- **경지 체계**: 무협 고유의 경지 상승 구조를 의술로 변환 (침의→천의). 무협 독자가 기대하는 "레벨업" 카타르시스가 의술 경지로 완벽 제공.
- **경혈/침술 구체성**: 합곡, 내관, 극천, 중완, 단중, 족삼리 등 실제 경혈명 사용. do_not_fake 계약 준수.
- **문파/세력 정치**: 진가장 내부 정치(B02, B10, B25), 무림맹 정치(B36, B40, B51-54), 마교 동맹(B55). 강호 세계관이 살아있음.
- **적대자 교체**: 가문 내 경쟁자(B01-10) → 독역/사마련(B11-42) → 좌천명(B43-69). 적대자 레벨이 경지 상승과 함께 자연스럽게 확대.
- **비급/보물**: 칠성침법(B22), 고대 의서, 약왕곡 약재, 해약도 약재 등 무협 고유의 비급/보물 구조 유지.
- **의술 비무(醫鬪)**: B42 의독대결 등 의술 특화 전투 장면으로 장르 차별화 유지.

로맨스 서브플롯(매화)이 존재하나, 장르 계약을 약화시키지 않고 오히려 강화함 (약침 파트너, 천의 개안의 감정적 기반).

### R7. BI Amplification — GREEN

BI가 TR의 주인공 우선 엔진을 실질적으로 강화한다.

**Confirming evidence:**

- **MartialHUD.Protagonist.actual_truth**: realm_history가 30개 이상의 경지 변화 포인트를 블록별로 추적. 단순 블록 요약이 아니라, 정확도 퍼센트까지 포함하여 주인공의 성장 곡선을 정밀하게 인코딩.
- **martial_arts 리스트**: 6개 기술의 origin, block_acquired, evolution을 상세 기록. 의무일체 기본 침법 → 칠성침법 → 살침 → 약침 → 화독위공 → 의념치료. 각 기술이 어떤 블록에서 어떻게 진화했는지 추적.
- **injury_log**: 9개 부상 이벤트와 회복 블록을 매핑. 주인공의 고통-회복 사이클을 정량적으로 추적.
- **faction_status.faction_history**: 5단계 세력 내 위치 변화 (무시받는 막내 → 의술 인정 → 핵심 전력 → 가주 추대 → 천하 의원). 주인공의 사회적 상승을 인코딩.
- **public_reputation**: "천의 경지 — 의념만으로 치료. 침 없이도 백 명 동시 치료." 주인공의 최종 위상을 명확히 기록.
- **GenreRules.realm_progression**: 7개 대단원별 경지 시작/종료/돌파/패배 블록을 구조화. TR에서 흩어져 있는 성장 곡선을 한눈에 파악 가능하게 증폭.
- **kill_count_note**: "전 블록 kill_count=0. 진소백은 한 명도 죽이지 않음. 비살상 원칙." — 주인공 엔진의 핵심 철학을 BI가 명시적으로 선언.

BI가 TR 본문의 블록 요약을 넘어서, 주인공의 성장 궤적/기술 진화/부상 사이클/세력 변동/평판 상승을 구조적으로 인코딩하여 protagonist-first engine을 실질적으로 강화하고 있다.

## 4. Potential Drift Points — 검토 및 기각

### D1. B38-39 2블록간 불능 상태 — drift인가?

아니다. 이 구간은 스승 상실 후 트라우마이며, 매화/소풍의 지지 속에서 회복한다. "비참한 무력감"이 아니라 "깊은 상실 후 재기"의 패턴. B40에서 트라우마 돌파가 시작되고 B43에서 살침 개안으로 귀결. 2블록의 고통이 5블록 뒤의 경지 전환(의성 입문)의 직접적 촉매. Pain aesthetic이 유지됨.

### D2. B28 과로 경맥 손상 — 보상 박탈인가?

아니다. B24-26에서 3블록간 의선 대회 우승의 보상이 충분히 활용된 후 발생. 과로의 원인이 "너무 많은 환자를 치료했기 때문"이라는 점에서 의원 정체성과 정합. 회복이 서역 천축행(B31-33)이라는 새로운 모험/성장으로 연결됨.

### D3. B53 좌천명 독 중독 — 순수 처벌 패턴인가?

아니다. 독 중독이 화독위공 발현(독을 내공으로 전환하는 기법)의 계기. "적에게 당함 → 그 피해 자체를 역전시키는 기술 획득"이라는 전형적 무협 반전 구조. 벡터가 보호적.

### D4. BI plot_roadmap이 블록 요약에 그치는가?

plot_roadmap 개별 엔트리가 summary 수준으로 간결하나, MartialHUD의 realm_history, martial_arts, injury_log, faction_history가 plot_roadmap을 대폭 보완하여 주인공 엔진을 구조적으로 인코딩. 블록 요약 이상의 가치를 제공.

## 5. Focus Questions Answered

### 무협 적합 보상 형태인가, 단순 블록 생존인가?

**무협 적합 보상.** 경지 상승, 비급 획득, 세력 내 지위 변동, 강호 평판 상승, 기술 진화가 모든 보상의 축. "살아남았다"로 끝나는 블록 없음.

### 의료/무술 고통이 미학적 상승형인가, 비하형인가?

**상승형.** 의원의 고통 = 환자를 살리지 못한 좌절(B13, B38) 또는 과도한 치료의 대가(B28). 모든 고통에 "의원으로서의 한계 자각 → 한계 돌파"라는 성장 벡터가 부착. 비하/모욕 없음.

### BI가 주인공의 고유 정보/치료/무술 엔진을 명확히 보존하는가?

**보존함.** MartialHUD의 realm_history(30+ 포인트), martial_arts(6개 기술 진화 추적), 비살상 원칙(kill_count=0) 명시, 금기 규칙과 서사 기능 연결, 경지 체계 7단계 구조화. TR에 흩어진 엔진 정보를 BI가 체계적으로 집약.

## 6. 3-Pass Self Audit

### Pass 1. Scope

- 대상이 live TR+BI pair survey only로 한정됨
- 코드/런타임/멤버 감사로 drift하지 않음
- 핵심 질문("주인공 둥기둥기 first")에 집중

### Pass 2. Evidence Quality

- 모든 판정에 블록 번호와 구체적 내용 인용
- BI 구조적 필드명을 anchor로 사용
- 다른 lane의 보고서를 참조하거나 덮어쓰지 않음
- 확신도: 97% — 중간 스트레스 구간에서 drift 가능성을 검토했으나 기각할 충분한 근거 확보

### Pass 3. Integrity

- 파일명/경로/stale 라벨에 의존한 판정 없음
- "순수 처벌 긴장"과 "좋은 시련"을 구분하여 판정
- 가문 특화 의미론(의술 경지, 비살상 원칙)을 drift로 오판하지 않음

## 7. Verdict

```
lane: T3
work_id: wuxia_heavenly_physician
family: wuxguide
TR verdict: green
BI verdict: green
pair verdict: green
strongest confirming evidence: B69 칠성침법 7침 — 적을 "치료"하며 승리. 70블록간 비살상 원칙(kill_count=0) 유지. 주인공의 고유 엔진(의무일체/의맥)으로만 가능한 승리 방식이며, 모든 블록의 고통·성장·보상이 이 최종 장면으로 수렴. BI MartialHUD가 이 엔진을 realm_history 30+포인트, martial_arts 6개 진화 추적, 비살상 원칙 명시로 구조적으로 인코딩.
strongest violating evidence: B38-39 스승 사망 후 2블록간 침술 정확도 0% 불능 상태. 주인공이 가장 무력한 구간이나, 매화/소풍의 지지 + 살침 개안의 서사적 필연성으로 "순수 처벌"이 아닌 "성장 촉매"로 기능. drift로 판정하기에는 벡터가 명확히 보호적.
reference pair candidate: yes
```
