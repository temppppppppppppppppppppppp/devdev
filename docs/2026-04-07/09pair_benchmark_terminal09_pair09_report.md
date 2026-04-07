# Pair Benchmark Terminal 09 — Pair 09 Report

Date: 2026-04-07
Status: complete
Document Type: read-only benchmark audit report
Canonical Path: `docs/2026-04-07/09pair_benchmark_terminal09_pair09_report.md`
Parent Order: `docs/2026-04-07/09pair_production_pair_benchmark_9terminal_opus_order.md`
Benchmark Spec: `material_ssot/00_governance/production-pair-benchmark-spec-v1.md`

## 1. Pair Identity

| Field | Value |
| --- | --- |
| pair id | `09` |
| family | `wuxguide` |
| TR | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` |
| BI | `bible/09_bi_wuxia_heavenly_physician.json` |
| work id | `wuxia_heavenly_physician` |
| protagonist | 진소백(陳小白) |
| total blocks | 70 |
| arcs | 7 |

## 2. P0 Hard Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| 1. first-block visible cider | **PASS** | Block 2: 조건부 공인 의원 자격 획득 (축출 위기 → 공인 진료 허가). Block 5: 의무일체 의식적 발현 첫 성공 + 백무명 스승 후보 접촉. Block 7: 비무 승리 — 침으로 무인 제압. 가시적 보상이 블록 1~7 전역에 분포. |
| 2. protagonist-only proof | **PASS** | Block 1: 의맥(선천 체질) 기반 의무일체 발현으로 형의 끊어진 경맥 봉합 — 소백만 가능. Block 2: 맥진 시연으로 사술이 아님을 실증 (protagonist-first agency). Block 7: 내관혈 침 봉쇄로 비무 승리 — 의무일체 전투 적용은 소백만 가능. `저건 쟤라서 가능했다` 명확. |
| 3. evaluation revision | **PASS** | Block 2: 아버지 진천웅(가주, weight 최상) '축출은 없다' + 공인 진료 허가. Block 6: 아버지 서고 의서 접근권 조건부 허가 (묵인 → 자원 개방). Block 7: 장로회 전원 비무 목격 — '사술인가, 의술인가' 판단 보류로 전환. 명시적이고 weighted. |
| 4. visible reward token | **PASS** | wuxguide 토큰 기준: Block 2 `rank` (조건부 공인 의원), `elder protection` (아버지 축출 거부). Block 5 `manual access` (의무일체 핵심 원리), `inheritance clue` (어머니 연관). Block 6 `manual access` (서고 의서 접근권), `realm step` (7단계 경지 체계 파악). Block 7 `reputation` (가문 내 실력 공인). |
| 5. block 1 → block 2 gate linkage | **PASS** | B1 치료 성공 → B2 공인 의원 → B3~4 마을 순회 진료 기반 → B5 의무일체 원리 → B7 전투 적용 → B8 엽천수 사사. 보상이 다음 게이트를 여는 체인이 깨끗함. |
| 6. BI/TR early conversion alignment | **PASS** | BI `initial_goal`: '형의 경맥을 살려 내고, 가문 공인 의원 자격과 진료 기반을 확보한다.' TR B1~2에서 정확히 실현. BI `CommercialCode.killing_points` (침=무공, 7단계 경지) 전부 B1~7에 씨앗. BI `MartialHUD.realm_history` B01~B10 구간과 TR 전개 정합. |
| opening innocence | **PASS** | 주인공의 개막 불리: 무공 자질 선천 부재, 아버지 냉대. `wrong seat` + `inherited bad frame` (의맥은 어머니 유산). 나태, 무책임, 자초한 실패 없음. |

P0 결과: **전 게이트 PASS. YELLOW/RED ceiling 미적용.**

## 3. Active Cap Rules

| Cap Rule | Status | Evidence |
| --- | --- | --- |
| no visible cider inside block 1 | not triggered | B1~7 전역 가시적 보상 존재 |
| rewardless pain blocks 2 in a row | **borderline** | B28~29 (경맥 손상 → 환자가 된 의원) 및 B38~39 (스승 사망 → 침을 잡지 못하는 날들)이 연속 고통 구간. 그러나 B29는 살침 개념 씨앗 + 아이 치료 복귀, B39도 살침 개념 형성 + 떨리는 손으로 침 복귀. same-block payback이 박하지만 존재. next-block (B30, B40)에서 본격 회복. **triggered 미확정 — 보상 씨앗이 살아 있어 GREEN ceiling 경계선.** |
| no-cider drought 6+ blocks | not triggered | 최장 보상 공백이 2~3블록. 각 아크마다 보상 착지 확인 |
| major defeat without next card | not triggered | B11 아버지 치료 실패 → B12 장풍래 동맹. B28 경맥 손상 → B31 서역행 개시. B38 스승 사망 → B39~40 살침 개념 + 회복. 모두 2~3블록 내 next card |
| BI acts as summary echo only | not triggered | BI `MartialHUD`가 7단계 경지 이력, 비단조 내공 곡선(하락 7회), 부상/회복 추적, NPC 생사 주기, 세력 변동 이력을 구조화. `CommercialCode.do_not_fake` 5항이 서사 밀도를 강제. TR 요약이 아닌 독립적 증폭 |
| early reward is asset-only | not triggered | B2 공인 의원 = status shift. B7 비무 승리 = authority/reputation shift |
| wins rely on stupid opposition | not triggered | 큰형의 경계는 가문 정통성 수호 동기. 장로회의 사술 의심은 시대 합리적. 독문의 독역 확산은 경제적 이권(해독제 독점). 모두 incentive-driven, era-valid |
| domain texture is generic | not triggered | 실제 경혈명(합곡/내관/극천/족삼리), 망문문절 진단법, 보사 법칙, 독역 '내공 높을수록 치명적' 메커니즘, 약침 결합법, 칠성침법 7단계 — 다른 장르로 치환 불가 |
| protagonist stays mostly passive | not triggered | 소백은 전 아크에서 능동적: 치료 시도, 지식 탐색, 비무 참전, 독역 관찰 데이터 수집, 서고 잠입 |

활성 cap rule: **none confirmed. `rewardless pain 2-in-a-row`이 경계선이나, same-block payback(B29 살침 씨앗 + 아이 치료, B39 살침 개념 + 복귀)이 보상 케이던스를 유지하여 GREEN ceiling 미적용으로 판정.**

## 4. P1 Score Table

| Axis | Score | Anchor |
| --- | --- | --- |
| protagonist innocence | 2 | 무공 자질 선천 부재 + 아버지 냉대 = wrong seat + inherited bad frame. protagonist 과실 없음 |
| protagonist-only proof clarity | 2 | 의맥(선천)→의무일체: 소백만 가능한 침 내공 발현. B1 형 치료, B7 비무 혈도 봉쇄, B69 적을 치료하며 이김 |
| evaluation revision visibility | 2 | B2 아버지(가주) '축출 없다' + 공인 진료. B7 장로회 충격. B10 장로회 공식 심판 통과. B24 무림 의선 대회 우승. B50 아버지 '잘했다, 소백아' |
| visible reward token strength | 2 | B2 공인 의원 rank. B5 manual access + inheritance clue. B6 서고 접근권. B7 비무 승리 reputation. B36 무림맹 대의원 임명. B56 차기 가주 추대. 구체적 토큰 전 아크 분포 |
| block1 → block2 linkage | 2 | B1~2 치료→공인→B3~4 마을 진료 기반→B5 의무일체 원리→B7 전투 적용→B8 엽천수 사사. clean next-gate chain |
| rational opposition | 2 | 큰형/장로회: 가문 정통성 수호. 독문: 독역 해독제 경제 이권. 좌천명: 흡독공 야망 + 권력 탈취. 모두 incentive-driven, era-valid |
| domain truth density | 2 | 실제 경혈명 기반, 진단→처방→시술→경과 시퀀스, 독역 내공 비례 메커니즘, 약침 결합법, 활침/살침 이론, 칠성침법 7침 체계. 의술 무협 특유의 도메인 진실이 엔진을 견인 |
| repeatable loop clarity | 2 | 환자 등장 → 진단 → protagonist-only 치료 → 재평가 → 다음 접근권/지위. 가문→마을→무림맹→천하 스케일로 반복. loop 가시적이고 재사용 가능 |
| BI amplification power | 2 | MartialHUD: 7단계 realm 이력 + 비단조 내공 곡선(하락 7회) + injury_log 9건 + kill_count=0 전 블록 비살상 추적. CommercialCode: killing_points 5항 + do_not_fake 5항 + taboo_rules 4항. GenreRules: realm_progression 7아크 defeat_block 추적. TR을 단순 요약하지 않고 구조적으로 증폭 |
| cider drought control | 1 | B28~29, B38~39 구간에서 연속 고통이 2블록 지속. same-block payback(살침 씨앗, 복귀)이 존재하나 박함. next-block(B30~31, B40)에서 본격 회복. 장기 가뭄(6+)은 없으나 고통 밀도가 높은 레인 특성상 weak valley가 존재 |

**Total: 19 / 20**

## 5. Provisional Grade

**GREENPLUS**

근거:
- 전 P0 hard gate PASS
- YELLOW ceiling rule 미적용
- GREEN ceiling rule 미확정 (rewardless pain 2-in-a-row 경계선이나 same-block payback 생존)
- P1 total 19/20 (GREENPLUS 구간 17~20)
- block 1이 `proof → reevaluation → reward → next gate` 체인의 exemplar
- 후반 보상 케이던스가 의도적으로 설계됨 (BI `internal_energy_curve` 하락 7회 + 회복이 arc 구조와 정합)

## 6. Alias Note

이 pair는 benchmark spec §9에서 이미 `high-pain recovery-control benchmark` exemplar로 등재되어 있으며, 현 audit 결과 해당 alias가 정당함을 확인한다.

**잔여 리스크 (residual risk):**

1. **B28~29 / B38~39 연속 고통 경계선**: same-block payback이 '씨앗'과 '떨리는 손 복귀' 수준으로 박함. 향후 TR densification 시 B29 또는 B39에 한 줄이라도 구체적 보상 토큰(예: 매화의 약초 처방이 효과를 거두는 장면, 장풍래의 대의원 지위 보장 서신 등)을 보강하면 GREEN ceiling 경계선 자체가 소멸.

2. **BI `CommercialCode`에 cider/success_device 명시 필드 부재**: BI가 `killing_points`, `do_not_fake`, `taboo_rules`로 서사 밀도를 강제하지만, first-block cider를 명시적으로 선언하는 필드(예: `first_block_cider`, `success_device`)가 없음. 현재는 `CoreIdentity.initial_goal`이 암묵적으로 그 역할을 하고 있으나, 향후 BI 스키마 정비 시 명시화를 권고.

3. **kill_count = 0 전 블록 비살상 원칙**: 서사적으로 강력한 특징이나, 70블록 전투 누적에서 비살상만으로 해결하는 것이 late-block escalation에서 reader 설득력 유지 필요. 현재 TR은 `치료하며 이기다`(B69)로 이를 해결하고 있으며, BI `kill_count_note`가 명시 추적하므로 현 상태에서는 리스크가 아닌 특징으로 분류.

## 7. Concise Rationale

pair `09`는 고통 밀도가 높은 wuxguide 레인에서 보상 케이던스가 살아 있는 희귀한 구조를 보유한다. block 1(B1~B7)에서 `형 치료 → 공인 의원 → 의무일체 원리 습득 → 비무 승리`라는 4단계 전환을 깨끗하게 착지시키며, 각 보상이 다음 게이트를 여는 체인이 exemplar 수준이다. 70블록 전체에서 내공 곡선이 7회 하락을 포함하는 비단조 성장인데도, 매번 2~3블록 내 next card가 착지하여 `고구마` 축적을 방지한다. BI는 MartialHUD를 통해 realm/내공/부상/세력 전 축을 추적하며, `do_not_fake` 5항이 의술 장면의 밀도를 구조적으로 강제한다. 유일한 주의점은 B28~29 및 B38~39의 연속 고통 구간에서 same-block payback이 박하다는 것이며, 이는 한 줄 수준의 densification으로 해소 가능하다. 현 상태에서 `GREENPLUS`로 판정하며, `high-pain recovery-control benchmark` alias를 유지한다.

---

read-only benchmark audit complete; no pair files mutated
