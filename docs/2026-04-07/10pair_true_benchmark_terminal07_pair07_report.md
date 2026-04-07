# 10pair True Benchmark — Terminal 07 / Pair 07 Report

Date: 2026-04-07
Mode: read-only true benchmark audit (full rewrite against `production-pair-benchmark-spec-v1`)
Scope: canonical pair `07` only (`office_checkup_next_day`)
Spec authority: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`
Prior pass on this report: evidence scouting only — superseded by this rewrite.

## 1. Pair Identity

- pair id: `07`
- slug / title: `office_checkup_next_day` ("검진 다음 날, 터질 게 보인다")
- family: `blockguide`
- WG: `work_guards/07_office_checkup_next_day.yaml`
- TR: `treatments/07_office_checkup_next_day_tr_block_070_draft.json` — total **70 blocks** (`Block 1`~`Block 70`)
- BI: `bible/07_bi_office_checkup_next_day.json`
- canonical resolution: `docs/2026-04-07/01_10_canonical_pair_manifest.md` row `07`
- spec exemplar status: pair `07` is named in spec §9 as the **first-block conversion benchmark exemplar** ("cleanest proof → reevaluation → token chain"). This audit verifies whether the live TR still matches that exemplar claim.

## 2. P0 Hard Gates (6 gates, strict window `TR Block 2~6`)

Each gate cites at least one concrete `TR block` anchor inside `2~6`. `Block 1` and `Block 7+` are NOT used as primary proof for gates `1~4`.

| # | Gate | Verdict | Primary anchor (inside `Block 2~6`) | Evidence |
| --- | --- | --- | --- | --- |
| P0-1 | first-block visible cider | **PASS** | `TR Block 2` (L109) | "전무 박성원이 경영기획팀에 직접 전화 … '한시혁 사원이 올린 자료 봤는데, 누구야?' … Lv1 자료작성권에서 Lv2 배석권으로 첫 점프. 첫 사이다." Reader-countable payback delivered inside `Block 2`. |
| P0-2 | protagonist-only proof | **PASS** | `TR Block 2` (L106–L109) + `TR Block 5` (L411–L417) | `Block 2`의 재분석은 검진 후 시혁의 조감 감각이 자료 한 장에서 병목·숫자·우선순위를 동시에 짚었기 때문에 가능. `Block 5`에서 그룹 최대 투자안 결함을 "유일하게 아는 사람"이라는 것이 명시 — `저건 쟤라서 가능했다`가 텍스트 차원에서 비교 대상 부재로 확정. BI `protagonist_weapon`(WG L6–L9 "결재선·숫자·사람 배치를 동시에 읽는 조감")이 같은 블록에서 텍스트 작동. |
| P0-3 | evaluation revision (weighted) | **PASS** | `TR Block 2` (L109) + `TR Block 3` (L213) | `Block 2`: 한일유통 전무 박성원(임원급, 결재선 최상위)이 시혁 이름을 직접 호명 + 배석 지시 — 가장 무게 있는 평가자가 윈도우 내에서 평가 갱신. `Block 3`: "전무의 메일 CC에 시혁 이름이 조용히 추가" — 동일 평가자에 의한 2차 갱신. WG `observer_tiers` 중 "전무(첫 인정자)" 단계가 윈도우 내 hit. |
| P0-4 | visible reward token (blockguide token list) | **PASS** | `TR Block 2` (L109) + `TR Block 3` (L213) | spec §4.1 blockguide token list 중 `name call`(전무 호명)·`seat`(배석권)·`CC`(메일 CC 추가) 3종이 `Block 2~3`에서 직접 부착. spec §4.2 "first concrete token lands at `TR block 7+`" 캡 발화 조건 미충족 — 첫 토큰은 `Block 2`. |
| P0-5 | block 1 → block 2 gate linkage | **PASS** | `TR Block 6` (L518–L524) → 다운스트림 확인 `TR Block 7` (L631) | `Block 6` reward에서 "대안 문서 완성 … 그 정보를 행동으로 전환할 무기"가 윈도우 내에서 등록. 이 무기가 `Block 7` 임원회의에서 "그룹 핵심 계열사의 최대 투자안이 보류되고 시혁의 대안이 검토 안건으로 채택"되는 다음 게이트를 연다. spec §2.1 단서 그대로: "TR block 7 may confirm this linkage, but cannot supply the first reward token retroactively" — 본 audit에서는 `Block 7`을 retro 백필이 아니라 `Block 6`에서 이미 획득한 token이 다음 게이트를 연다는 다운스트림 확인으로만 사용. |
| P0-6 | BI/TR early conversion alignment (BI 1~3 in TR 1~3) | **PASS** | BI `CommercialCode.cider_point` (BI L25) + `success_device` (BI L26) + `logline` (BI L12) ↔ `TR Block 1~3` | BI `cider_point` "저평가된 자산과 병목을 먼저 읽고 지배력으로 전환하는 역전감" — `Block 1`에서 3년 무명(저평가) 셋업, `Block 2`에서 병목 읽기 → 지배력 전환 시작(전무 직보·배석권), `Block 3`에서 지배력 강화(CC 라인). BI `success_device` "정보 우위와 타이밍" — `Block 2`(검진 후 재분석 타이밍) + `Block 3`(CC 추가 타이밍)에서 직접 작동. BI `logline` "그룹 핵심 계열사의 최대 투자안을 멈춘 건 3년차 말단 사원이었다" — `Block 1`에서 3년차 말단 셋업, `Block 5~6`에서 멈출 무기 적재(윈도우 내), `Block 7`에서 실현(다운스트림 확인). 세 BI 앵커가 `TR Block 1~3` 안에서 텍스트로 살아 있음. |

**P0 종합: 6/6 PASS.** spec §4.2의 "two or more gates fail → default RED review lane" 미발화. spec §4.3 Opening Innocence Rule: 시혁의 3년 투명인간 상태는 본인 책임이 아니라 `wrong seat`(B0 사수 퇴사 후 잡무 잔류) + `inherited bad frame`(오세진 팀장의 공 가로채기 패턴 누적)이므로 acceptable disadvantage. 개막 캡 미발화.

## 3. Full-Block Cider Scan (`has_cider: true/false` per block, same-block payback only)

판정 기준 (spec §2.3): 같은 블록 안에서 reader-countable payback 1종↑ 존재(visible reward token / weighted reevaluation receipt / protection receipt / authority or access shift / recovery asset materially offsetting same-block pain / explicit next-card or next-gate receipt the reader can feel now). 다음은 `false`: setup-only / explanation-only / wait-only / pain-only / humiliation-only / failure-only / "later payoff promise" with no same-block receipt.

- 본 스캔은 reward 필드 literal "없다" 검색이 아니라 **block 본문 + reward + power_shift + relationship_delta + capital_delta + genre_ext** 종합 판단으로 same-block payback 유무를 가린다.

### 3.1 Per-block ledger

| Block | has_cider | 같은 블록 페이백 (또는 사유) | 카운트 사유 (false인 경우) |
| --- | --- | --- | --- |
| 1 | false | 검진 직전 3년 패턴 1회 더 닫힘. opening setup. | setup-only / pain-only |
| 2 | true | 전무 직보 호명 + 배석권(Lv1→Lv2) + "첫 사이다" 명시 | — |
| 3 | true | 배석 연장 + CC 라인 추가 + "두 번째 사이다" | — |
| 4 | true | 배석권 재확보 + 적대축 인식(recovery) | — |
| 5 | true | 정보 비대칭 단독 보유(next-card receipt) | — |
| 6 | true | 대안 문서 완성(weapon) — `Block 7` 진입 카드 등록 | — |
| 7 | true | 임원회의 통합안 보류 + 시혁 대안 채택 | — |
| 8 | true | 보상 4종 동시 발동(실명 메일·TF 간사·12층 자리·CC 변경) + Lv2→Lv4 | — |
| 9 | true | TF 위치 확립 + 최부장·차장 신뢰 + 원본 데이터 요청 회의록 등재 | — |
| 10 | true | 아크 마무리 + Lv4 상신권 + 다음 전장 구도 | — |
| 11 | true | 최부장 협력자 확보 + 윤재환 패턴 역이용 첫 정보 조작 | — |
| 12 | true | 현장 데이터 확보 + 최부장 직접 인정("현장 감각도 있네") | — |
| 13 | true | 오세진 TF 복귀 시도 차단 + 인사평가 방어 논리 확보 | — |
| 14 | true | Lv3 발언권 실증 + 조사 범위 확대 지시 + "핵심 분석관" 인식 전환 | — |
| 15 | true | 분기별 반품 조절 패턴 발견(강력한 간접 증거 = next-card) | — |
| 16 | true | 2개 센터 현장 데이터 + 밀어내기→반품 순환 증거 | — |
| 17 | true | 최부장 단순 협력자 → 같은 편 전환(아군 자산화) | — |
| 18 | true | 인사평가 B0→B+ 등급 상승 + 서정민-유사 외부 인식 누적(약 토큰) | — |
| 19 | true | TF 최종안 대표이사 승인 + "네가 아니었으면 망했다" + 핵심 인력 인식 전환 | — |
| 20 | true | Lv5 예산 발언권 + "하반기 예산 편성 TF에도 들어와" 다음 자리 호명 | — |
| 21 | true | 서정민 재무 차장 아군 확보 + MD 비용이 감사 후보 등재 | — |
| 22 | true | 과거 데이터 백업(protection receipt) | — |
| 23 | true | 재무팀 우회 경로 살아 있음 + 패배 즉시 우회 전환(recovery) | — |
| 24 | true | 정기감사 보고서에 MD 비용 이상 공식 기재(authority shift) | — |
| **25** | **false** | quiet block "조용한 전선" — `capital_delta: 실무 진행(유지)`, `profit_loss: 변동 없음 — 축적 구간`. 외부 토큰·평가 갱신·권한 이동·다음-카드 영수증 없음. | bridge-only / wait-only |
| 26 | true | MD사업부 공식 소명 요청 발동(authority shift) | — |
| 27 | true | 서정민 대조표 등재 + 감사 종결 차단 | — |
| 28 | true | 감사 항목 유보(미세 손해)지만 본부장 약점 인식(next-card) + 다음 분기 재시도 | — |
| 29 | true | MD 내부 균열 인지 + 향후 접점 경로 확보(next-card) | — |
| 30 | true | MD사업부 자체 감사 발동 + 시혁 감사 지원 TF 추가 배치(authority + access) | — |
| 31 | true | 감사 데이터 요청 리스트 전략 배치 완료 + 서정민과 감사 방향 합의 | — |
| **32** | **false** | "읽히지 않는 회의" — 감각이 처음 안 통함. reward = "한계 인정 + 보완 방법을 배운다 + 자문의 시작". 같은 블록 내 외부 토큰·권한 이동·보호 영수증 없음. 서면 세분화는 다음 블록(33)에서 작동. | failure-only with deferred payoff |
| 33 | true | 서면 숫자 불일치 포착 + 감사 보고서 등재(recovery) | — |
| 34 | true | 감사 지속 승인(authority sustained) + 장현태 불안 감지(next-card) | — |
| **35** | **false** | "야근의 무게" — 정밀검사 예약 + "자기 자신을 돌보기로 한 첫 결정". 외부 토큰·평가 갱신·권한 이동 없음. `risk_level: 무위험`, `business_sector: 일상`. 독자가 같은 블록에서 받을 영수증 부재. | setup-only / interior-only |
| 36 | true | 인사 가중치 변경 역추적 + 기여 문서 목록 수집(next-card 탄약) | — |
| 37 | true | 서정민 외부 확인서 1건 확보(외부 증인 토큰) — 패배지만 같은 블록 내 회수 자산 명시 | — |
| 38 | true | 전무 → HR팀장 직접 통화 + S등급 가능성 재개(authority shift) | — |
| 39 | true | 후배 사원이 시혁에게 직접 자료 송부(충성 전환 신호 = reeval receipt) | — |
| 40 | true | S등급 확정 + 오세진 축 정리 + Lv6 TF 실권 진입 | — |
| 41 | true | 계열사 합동 회의 첫 참석(access shift to 그룹 본관) | — |
| 42 | true | 3사 비용 재분류표 TF 공동 산출물 등록 + 그룹 레벨 문서 시혁 이름 첫 등재 | — |
| **43** | **false** | "본사식 브리핑" 패배 블록. reward 명시 "없다 … 시혁이 얻은 것은 그룹 전략 프레임워크 문서 한 부와 교훈뿐". 같은 블록 회의록에서 시혁 이름 탈락(net loss). 다음 블록(44)이 회복. | failure-only with deferred payoff |
| 44 | true | 윤재경 상무 1:1 면담 성사 + 원본 메타데이터 증명 + 인식 업그레이드 | — |
| 45 | true | 이도현 그룹 전략실 협력자 + 템플릿 장착 + 정태호 출처 위조 정보 입수 | — |
| 46 | true | 공동 TF 설계안 검토 안건 채택 + "실행 간사" 후보 공식 언급 | — |
| 47 | true | 두 회사 병목 한 장 조건표 + 식품 부장 영역 방어 해소 + 첫 산출물 제출 | — |
| **48** | **false** | "정태호 사무국장 임명" 패배 블록. reward 명시 "없다 … 출처 위조 카드 온존 + 폭로보다 해결이라는 교훈". 같은 블록 내 외부 토큰·권한 이동 없음. | failure-only |
| 49 | true | 윤재경 "원본 출처 등재" 합리적 조건 인정 + 정태호 갇힘(authority shift) | — |
| 50 | true | 공동 TF 정식 출범 + 실행 간사 발령 + 매월 시혁 이름 등재 + Lv6→Lv7 | — |
| 51 | true | 외부 감사 전면 투입 결정 + 시혁 데이터 제공 인프라 포지션 확보 | — |
| 52 | true | 최수연 변호사 협력 수립 + 법무 룰 학습 | — |
| **53** | **false** | "삭제된 품의서" 패배 블록. reward 명시 "없다 … 원본 사라짐, 잠그는 사람 역할 자각만 남음". 같은 블록 외부 토큰 없음. | failure-only |
| 54 | true | 이사회 감사위원회 배석 + 사외이사 질의 응답 완료(체질 개편으로 판 이동) | — |
| 55 | true | 사전 품의 메일 경로 발견(증거 빈칸 마지막 핵심 = next-card receipt) | — |
| 56 | true | 측근 부장 변호사 선임 → 장현태-측근 균열(구조 무너짐 신호) | — |
| 57 | true | 합의 거절 + 끝까지 가겠다는 선언 + 장현태 합의 카드 소진 | — |
| 58 | true | 인사 재분류안 1건 방어(전략실 관할 이관) + 장현태 카드 전량 소진 확인. half-cider이지만 protection receipt 1건 부착되므로 true. | — |
| 59 | true | 감사팀 최종 보고 완료 + 증거 체인 완성 + 정태호 보고서 자기 모순 무력화 | — |
| 60 | true | 장현태 퇴진 + MD사업부 재편 + 경영기획팀장 직무대행 + Lv7+ 다중 라인 | — |
| 61 | true | 빈 구조 3건 식별(전장 지도 = next-card) | — |
| 62 | true | 그룹 전략실장 강민호 첫 직접 대면 + 정식 조직 제안 수령(access shift) | — |
| **63** | **false** | "승진안의 함정" 패배에 가까운 선택. reward 명시 "없다 … 시혁이 얻은 것은 시간뿐". 같은 블록 외부 토큰 없음. | failure-only / dilemma-only |
| 64 | true | 선택지 C 설계 완료(유통 팀장 + TF 산하 + 그룹 보고 라인 유지) — 다음-카드 등록 | — |
| **65** | **false** | "정밀검사 결과" — "특이 소견 없음 + 내적 전환점 통과". `risk_level: 저 — 내면 블록`, `deal_type: 해당 없음 — 내면 블록`. 외부 토큰·평가 갱신·권한 이동 없음. | interior-only / explanation-only |
| **66** | **false** | "감각의 이름" — 지하철에서 감각에 '조감' 명명 + 선택지 C 제시 순서 정리. `risk_level: 저 — 내적 블록`. 외부 액션은 다음 블록(67). | interior-only / preparation-only |
| 67 | true | 선택지 C 양쪽 제시 완료(강민호 검토, 전무 올려보겠다) + 제안자 포지션 전환 | — |
| 68 | true | 정태호 사무국장 해임 + 출처 위조 축 완결 | — |
| 69 | true | 라인 선택권 확보 + 경영기획팀장 정식 발령 + 그룹 구조조정 TF 실무총괄 + 전략실/대표 동시 보고 | — |
| 70 | true | 경영기획팀장 첫 아침 + "팀장님" 호명 + 결재 시스템 3곳 이름 등재(클로저 토큰) | — |

### 3.2 Scan Aggregates

- 총 블록 수: **70**
- no-cider 블록 수: **10**
- no-cider 블록 번호 (정확): **`Block 1, 25, 32, 35, 43, 48, 53, 63, 65, 66`**
- 가장 긴 no-cider drought (연속 무보상 블록 길이): **2** — `Block 65 → Block 66` 연속 (그 외는 모두 단발)
- 무보상 블록 분포 (윈도우별 카운트, 참고용):
  - `1~10`: 1 (Block 1, opening setup)
  - `11~20`: 0
  - `21~30`: 1 (Block 25)
  - `31~40`: 2 (Block 32, 35 — 비연속)
  - `41~50`: 2 (Block 43, 48 — 비연속)
  - `51~60`: 1 (Block 53)
  - `61~70`: 3 (Block 63, 65, 66 — 65~66 연속)

### 3.3 Prior Pass Carry-Forward

지시받은 대로 prior pass의 `Block 43 / 48 / 53 / 63` 지적은 그대로 유지된다 (모두 spec same-block payback 기준에서도 `false`로 재확인). 본 rewrite는 prior pass가 놓친 6개 — `Block 1, 25, 32, 35, 65, 66` — 를 추가로 식별한다. 추가 6개의 사유는 위 ledger에 명시했다.

## 4. Active Cap Rules (spec §6)

| Cap rule | 발화? | 근거 |
| --- | --- | --- |
| no visible cider inside block 1 (= TR `Block 2~6`) | NO | `Block 2`에서 첫 cider 발화 |
| first concrete token lands at `TR block 7+` | NO | 첫 토큰 = `Block 2`(name call·seat) |
| **any no-cider block in the full-block cider scan** | **YES → YELLOW ceiling** | 10건 무보상 블록 존재 |
| rewardless pain blocks 2 in a row → GREEN ceiling | NO (경계) | 연속 2건은 `Block 65→66` 1쌍이지만 두 블록 모두 `pain`이 아닌 `interior reflection`. spec 문구 "rewardless **pain** blocks 2 in a row"의 문자 해석상 미발화. 해석을 넓혀 "rewardless 2 in a row"로 잡으면 GREEN ceiling 추가 발화 가능 — 본 audit은 spec 문자 해석을 따라 미발화로 두되, 위험 신호로 §8 repair에 반영. |
| no-cider drought 6+ blocks → YELLOW ceiling | NO | 최장 drought = 2 |
| major defeat without next card in same/next block → YELLOW ceiling | NO | `Block 43→44`(윤재경 직접 면담), `Block 48→49`(윤재경 원본 출처 등재 인정), `Block 53→54`(이사회 배석), `Block 63→64`(선택지 C 설계) — 모든 패배 직후 다음 블록에서 우회/회복 카드 부착. WG `custom_rules` "반격 예약 없는 손해 금지" 준수. |
| BI acts as summary echo only → GREEN ceiling | NO | BI `Lv1~Lv8 사다리`·`observer_tiers`·`mandatory_lexicon` 등이 TR을 sharpen (P1 axis 9 참조) |
| early reward asset-only without status/authority | NO | `Block 2~3` 첫 토큰이 status(name call)·authority(배석권·CC) 중심 |
| wins rely on stupid opposition → GREEN ceiling | NO | 오세진(인사 가중치·CC 라인 합리적 견제), 장현태(분기 실적 관리 인센티브), 정태호(본사 언어 권력), 윤재경(회색 지대) 모두 인센티브 기반 |
| domain texture generic → GREEN ceiling | NO | 결재선·CC·TF 간사·예산 코드·실명 메일·인사 가중치·전략 축 KPI 트리 — lane swap 불가 |
| protagonist passive across key arc with weak reward → YELLOW ceiling | NO | 시혁은 `Block 22`(데이터 백업), `Block 26~30`(우회 경로 가동), `Block 36~38`(인사전 정면 돌파)에서 능동 |

**활성 캡: `YELLOW ceiling` (one no-cider block 규칙).** 이것이 본 pair의 유일한 spec-수준 유효 캡이다.

## 5. P1 Score Table (10 axes × 0/1/2 = total 20)

| # | Axis | Score | 근거 (TR block + BI/WG 앵커) |
| --- | --- | --- | --- |
| 1 | protagonist innocence | **2** | `Block 1` 셋업: 사수 퇴사 후 잡무 잔류, B0, 3년 무명. WG `forbidden_flattenings`의 "회개물 스타트" 회피. 본인 책임 없음 — `wrong seat` + `inherited bad frame`. |
| 2 | protagonist-only proof clarity | **2** | `Block 2` 검진 후 재분석 + `Block 5` "유일하게 아는 사람" + `Block 7` 임원회의 한 줄 짚기. WG `protagonist_weapon`의 조감 감각이 시혁 고유로 명시. |
| 3 | evaluation revision visibility | **2** | `Block 2` 전무 직접 호명 + `Block 3` CC 추가 + `Block 7` 대안 채택 + `Block 8` 대표이사 실명 메일 — explicit and weighted, 4단계 누적. |
| 4 | visible reward token strength | **2** | `Block 2`(name call+seat) → `Block 3`(CC) → `Block 7`(ownership) → `Block 8`(보상 4종 동시: 실명 메일+TF 간사+12층 자리+CC 변경) → `Block 20`(Lv5 예산 발언권) → `Block 50`(Lv7 그룹 실행 간사) → `Block 60`(Lv7+) → `Block 69`(라인 선택권). spec §4.1 blockguide token list 거의 전 종류 hit. |
| 5 | block 1 → block 2 gate linkage | **2** | `Block 6` 대안 문서 → `Block 7` 임원회의 폭발 → `Block 8` 보상 4종 + Lv2→Lv4 점프 — clean next-gate opening. WG `custom_rules[5]` "다음 블록은 이전 블록의 보상으로만 열린다" 준수. |
| 6 | rational opposition | **2** | 오세진(인사 가중치·CC 라인 합리적 견제 — `Block 36~37`), 장현태(분기 실적 관리 인센티브 — `Block 15`/`Block 26~30`), 정태호(본사 언어 권력 사용 — `Block 43`), 윤재경(회색 지대 utility-driven — `Block 44`), 강민호(묶어두기 합리 — `Block 62~63`) 모두 era-valid. WG `forbidden_flattenings`의 "오세진·장현태 무능 캐리커처" 회피. |
| 7 | domain truth density | **2** | 결재선 Lv1~Lv8 사다리, 배석권/상신권/CC 라인/TF 실권/예산 발언권/라인 선택권의 한국 그룹 계열사 결재 문화 디테일 + 실명 메일·전사 메일·인사 가중치·전략 축 KPI 트리·외부 감사·법무 라인 — 다른 lane으로 swap 불가. WG `mandatory_lexicon` 10어휘 모두 TR 본문에서 사용. |
| 8 | repeatable loop clarity | **2** | 반복 가능한 loop: `병목 감지 → 우회 경로 설계 → 상위 결재선 우회 상신 → 보상 부착 → 다음 라인 진입`. `Block 2~8`(첫 사이클), `Block 11~20`(2차), `Block 26~40`(3차 감사 사이클), `Block 41~50`(4차 그룹 레벨), `Block 51~60`(5차 결전), `Block 67~70`(6차 클로저)에서 6회 변주 반복. 같은 무기·다른 판. |
| 9 | BI amplification power | **2** | BI는 단순 echo가 아님. BI `FinanceHUD`의 Lv1~Lv8 사다리가 TR의 매 보상에 정확한 단계 부착(예: `Block 8`의 Lv2→Lv4, `Block 50`의 Lv6→Lv7)으로 보상 강도를 quantify. BI `protagonist_evaluation.observer_tiers`(같은 팀 동료→전무→오세진→장현태→대표이사→외부 감사) 6단계가 TR `Block 2`(전무)→`Block 4`(오세진)→`Block 7`(대표이사)→`Block 51`(외부 감사) 순서로 정확히 hit — TR 이 BI 사다리를 쓰면서 promise를 sharpen. |
| 10 | blockwise cider continuity | **0** | spec 정의: "one or more no-cider blocks = 0". 본 스캔에서 10건 무보상 블록 식별 (`Block 1, 25, 32, 35, 43, 48, 53, 63, 65, 66`). 단일 0점이 transversely 캡을 강제. |

**P1 raw total: 9×2 + 1×0 = `18 / 20`**

## 6. Provisional Grade

- P0: **6/6 PASS** (개막 캡·개막 무자격 캡 모두 미발화)
- P1 total: **18/20** (본문 자체 점수는 `GREENPLUS` 밴드 17~20)
- 활성 캡: **`YELLOW ceiling`** (spec §6 "any no-cider block in the full-block cider scan")
- spec §8.3 결정 규칙: "any no-cider block exists → YELLOW"

**Final provisional grade: `YELLOW`**

해석: 본 pair는 spec §9에서 "first-block conversion benchmark exemplar"로 명명된 위상에 P0 6/6 + P1 18/20으로 부합하는 강한 본문이다. `Block 2`의 첫 사이다 사슬은 spec이 모범으로 인용할 만큼 깔끔하다 — 이 부분은 prior pass가 아니라 본 strict rewrite에서도 동일하게 확인된다. 그러나 spec §2.3의 strict house rule "one no-cider block, no grade above YELLOW"가 10건 무보상 블록에 의해 발화되어 캡이 강제된다. 캡이 풀린다고 가정하면 raw 18/20은 GREENPLUS 진입 가능 영역이다. 캡 해제 비용은 본 pair가 다른 YELLOW pair에 비해 상대적으로 낮다 — 무보상 블록이 모두 단발(1쌍 제외) + 모두 직후 블록에서 spec-legal recovery 부착 + reward 필드의 텍스트 양성화·미세 토큰 부착만으로도 다수가 회수 가능하기 때문이다.

## 7. Top 3 Repair Units

`YELLOW`이므로 spec §10에 따라 alias note 대신 repair units 제시. 모두 bounded — full-wave surgery 없음.

### Repair-1 · 연속 무보상 차단 (`Block 65 → Block 66`, 최우선)

- 위치: `TR Block 65` (L5807–L5874) + `TR Block 66` (L5875–L5943)
- 문제: 두 블록 모두 `interior-only`이고 **연속 2 in a row**이다. spec §6의 "rewardless pain blocks 2 in a row → GREEN ceiling" 문자 해석은 `pain` 단어 때문에 미발화이지만, 본문 의도("감각에 끌려다니지 않는 사람으로의 전환")가 강하므로 audit가 보호적으로 캡 미발화 처리한 것이다. 다음 audit 또는 다른 reader가 동일한 strict 해석을 보장하지 않으므로 가장 위험한 risk surface다.
- 수정 폭: reward 양성화로 부족 — 둘 중 하나에 same-block 외부 토큰을 부착해 연속을 끊는다. 권장: `Block 65` 안에 같은 밤 시혁이 정밀검사 결과지를 받고 **다음 날 미팅용 한 줄 메모**(선택지 C의 첫 문장)를 자기 자취방 책상 위에 작성해 두는 액션을 추가 — 이로써 `Block 65`에 "다음 게이트 카드 적재"라는 same-block next-card receipt가 생긴다.
  - 또는 `Block 66`에 출근길 지하철 안에서 **이도현으로부터 짧은 메시지** (예: "강민호 상무님 오늘 일정 비어있어요")를 받는 micro-event를 부착 — same-block 외부 access shift 1건 생성.
- 효과: 연속 2 in a row 차단 → drought 최장값이 2→1로 떨어짐 → `pain` 해석 확장 시에도 GREEN ceiling 해제. 무보상 카운트는 10→9 (1건만 회수).
- 본문 충실성: 두 블록의 핵심 메시지("감각에서 판단으로의 전환")는 손대지 않는다. micro-event만 추가.

### Repair-2 · 패배 블록 4종 same-block micro-token 부착 (`Block 43 / 48 / 53 / 63`, prior pass 지적 carry-forward)

- 위치 (4개 reward 필드):
  - `TR Block 43` reward (L4104) — 본사식 브리핑 패배
  - `TR Block 48` reward (L4493) — 정태호 사무국장 임명
  - `TR Block 53` reward (L4902) — 삭제된 품의서
  - `TR Block 63` reward (L5673) — 승진안의 함정
- 문제: 모두 reward에 "없다" 명시. spec §2.3은 reward 필드 literal 검사가 아니라 same-block payback 검사이지만, 본 4개 블록은 본문 차원에서도 외부 토큰이 비어 있다(회의록 이름 탈락 / 임명 패배 / 원본 사라짐 / 시간만 매수). 4건 모두 "spec-legal defeat with deferred payoff" — 다음 블록에서 회수되므로 spec §6 "major defeat without next card" 캡은 미발화이지만, "any no-cider block" 캡은 발화한다.
- 수정 폭: 본문 변경 없이 reward 필드 한 줄씩 양성화 + 같은 블록에 이미 묻혀 있는 미세 자산을 명시화한다.
  - `Block 43`: 본문에 "그룹 중기 전략 프레임워크 68페이지 다운로드"가 있음 — 이를 reward에 "**다음 판의 사전(辭典) 확보** — 본사 언어를 역공학할 수 있는 원본 문서 1부 입수"로 양성화. setup-only 블록을 next-card receipt 블록으로 reframe.
  - `Block 48`: 본문에 "출처 위조 카드 온존" 명시 — reward에 "**카드 온존 자산** 확보. 폭로 카드는 다음 블록에서도 살아 있다"를 첫 문장으로 등록. spec next-card receipt 충족.
  - `Block 53`: 본문에 "삭제 로그 + '잠그는 사람' 역할 자각" — reward에 "**삭제 로그 확보 + 잠그는 사람 역할 등록** — 결전의 마지막 무기로 등록"을 첫 문장으로 등록. spec next-card receipt 충족.
  - `Block 63`: 본문에 "시간 매수" — reward에 "**제3안 설계 공간** 확보 + 양쪽 제안의 핵심 이해를 비교할 시간 매수"로 양성화. interior-only가 아닌 next-card receipt로 reframe.
- 효과: 무보상 카운트 10→6 (4건 회수). 본문/사건/관계는 변경 없음 — reward 필드 1줄씩만 수정. wave 수술 아님.
- 캡 해제 여부: 6건이 남으므로 캡은 여전히 활성. 그러나 점차적으로 해제 트랙에 진입.

### Repair-3 · quiet/setup 블록 3종 reward 강화 + micro-token (`Block 25 / 32 / 35`)

- 위치 (3개 블록 reward + 본문 1~2 줄 추가):
  - `TR Block 25` reward (L2429) — 조용한 전선 (quiet 축적)
  - `TR Block 32` reward (L3100) — 읽히지 않는 회의 (감각 첫 한계)
  - `TR Block 35` reward (L3386) — 야근의 무게 (정밀검사 예약)
- 문제: 3건 모두 spec §2.3의 false 분류(setup-only / failure-only with deferred payoff / interior-only). 본문 의도는 명확하지만 same-block 외부 토큰이 0이다.
- 수정 폭:
  - `Block 25`: 본문에 시혁이 물류 실무 진행 중인 상태이므로, **현장에서 작은 토큰** 1건 부착 — 예: 용인 센터 현장소장 정기철이 "이번에 한 사원이 정리한 입고 매뉴얼이 현장에서 잘 쓰입니다"라는 한 줄 인정을 최부장을 통해 시혁에게 전달. same-block weighted reevaluation receipt 1건 생성.
  - `Block 32`: 본문 마지막에 시혁이 서정민에게 서면 세분화 전술을 제시하는 장면이 있음 — 이를 same-block deal로 격상해 "서정민이 '좋은 생각'이라며 즉시 감사 데이터 요청서 양식 수정안을 함께 작성" 한 단계를 추가하면 same-block next-card receipt 1건 생성.
  - `Block 35`: 정밀검사 예약 외에 **체력 보강 자원 투입** 1건 부착 — 예: 시혁이 야근 식대를 TF 간사 권한으로 정식 신청해 승인받음(Lv5 예산 발언권의 first 미니 사용). same-block authority shift 1건 생성. 본문 캐릭터 비트("자기 자신도 자산이다")와 정합.
- 효과: 무보상 카운트 6→3 (Repair-1+2 적용 후 기준). spec §2.1은 P0 evidence window 규칙일 뿐 §2.3 full-block cider scan에서 `Block 1`을 면제하지 않으므로, `Block 1` 잔존도 무보상으로 그대로 카운트된다. 잔존 3건 예시 = `Block 1` + (`Block 65` 또는 `66` 잔여) + (그 외 1건).
- 본문 충실성: 모두 본문에 이미 있는 자원·관계의 미세 확장. 새 인물·새 사건 도입 없음.

### Repair 적용 후 기대 등급 (참고)

- 본 audit는 read-only이므로 적용 시뮬레이션은 참고치만 제공.
- Repair 1+2+3 적용 시 무보상 카운트 = 1~2건 수준, drought 최장 = 1. spec §6 "any no-cider block in the full-block cider scan → YELLOW ceiling" 규칙은 무보상이 단 1건이라도 남아 있는 한 발화하므로, **무보상 카운트가 0이 되기 전까지 grade는 `YELLOW` ceiling 그대로 유지된다.** P1 axis 10 점수도 spec §5 정의("one or more no-cider blocks = 0")상 잔존 1~2건 상태에서는 여전히 `0`이며, `1`로 올라가려면 무보상이 0이어야 한다. 따라서 캡 해제와 axis 10 회복은 모두 무보상 0이라는 동일한 조건에 묶여 있다.
- 실용 라우트: spec §10의 "the smallest profitable scope" 원칙에 따라 Repair-1 + Repair-2만 우선 적용 → 다음 audit에서 진행도 재평가. 단, 이 단계에서도 grade는 `YELLOW` 유지이며, `GREEN`/`GREENPLUS` 진입은 10건 전부 회수해 무보상 0을 달성한 뒤에만 가능하다.

## 8. Concise Rationale

- pair `07`은 spec §9 명시 exemplar(첫 블록 컨버전 표준)이고, 본 strict rewrite는 그 위상을 P0 6/6 PASS + P1 18/20으로 텍스트 차원에서 재확인했다. `Block 2`의 전무 직접 호명 + 배석권 + "첫 사이다" 명시는 spec이 §2의 thesis로 요구하는 "block 1 must pay" 조건을 가장 깔끔하게 충족하는 사례 중 하나다. P0 게이트의 모든 일차 앵커가 `Block 2~6` 안에 있고, `Block 7`은 spec §2.1이 허용하는 다운스트림 확인 용도로만 인용했다.
- 본 pair의 실질 약점은 단 하나: spec §2.3의 strict house rule이 발화하는 **`Block 1, 25, 32, 35, 43, 48, 53, 63, 65, 66` 10건의 무보상 블록**이다. 이 중 prior pass가 지적한 4건(`43, 48, 53, 63`)은 strict 기준에서도 그대로 유효하고, 본 rewrite가 추가로 6건을 식별했다(`1, 25, 32, 35, 65, 66`). 추가 6건은 모두 reward 필드 literal 검사가 아니라 본문/`power_shift`/`capital_delta`/`relationship_delta` 종합으로 same-block 외부 토큰 부재를 확인한 결과다.
- spec §2.3 prior pass는 reward 필드의 "없다" literal만 잡았기 때문에 4건만 식별했다. 이번 rewrite는 quiet 블록(25), defeat-with-lesson(32), 자기 관리 블록(35), interior 블록(65, 66)을 spec-strict 기준으로 같이 잡았다.
- spec §6 캡 중 발화한 것은 "any no-cider block" 1건뿐이다. "rewardless pain blocks 2 in a row" 캡은 `Block 65→66` 1쌍이 연속이지만 두 블록 모두 `interior reflection`이라 spec 문구의 `pain` 키워드 문자 해석으로는 미발화 — 본 audit는 spec 문자에 충실하게 미발화 처리하되, Repair-1로 우선 차단할 위험으로 명시했다.
- "major defeat without next card in same/next block" 캡은 4개 패배 블록(43/48/53/63)이 모두 직후 블록에서 즉시 우회/회복 카드 부착으로 spec-legal 처리되어 미발화. 이 점은 본 pair가 WG `custom_rules` "반격 예약 없는 손해 금지"를 작가 차원에서 준수했음을 보여준다 — 약점이 본문 결함이 아니라 reward 표기 방식에 있다는 의미다.
- 최종 라우트: `YELLOW (P1 raw 18, capped by single rule)`. spec §10 "the smallest profitable scope" 원칙으로 Repair-1(연속 2 차단 우선) → Repair-2(패배 블록 4종 reward 양성화) → Repair-3(quiet 3종 micro-token) 순서. 본 audit는 read-only이므로 어떠한 TR/BI/WG 파일도 변경하지 않았고, prior pass의 4건 지적은 그대로 carry-forward되었다.

read-only true benchmark audit complete; no pair files mutated
