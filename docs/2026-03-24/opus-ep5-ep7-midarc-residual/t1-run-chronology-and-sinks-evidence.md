# T1 Evidence — Run Chronology + Sink Reconciliation

Date: 2026-03-24
Lane: T1

## E-1. Console Timeline Reconstruction (EP5-EP7 Stage 4 Only)

Source: `console.txt`

### EP5 Console Rounds
```
L1157: 📝 제5화 집필 시작 (Arc 2, 위치 1/5)
L1221: 📊 Director 판정: PASS_WITH_FIX (초기: PASS_WITH_FIX, 점수: 92, 선택: 후보 A)
L1234: [A-3] Post-select continuity conflict: 제3화에서 시중은행 소속이었던 박성호 PB가 제5화에서는
       한미증권 소속으로 등장하는 인물 소속 설정 충돌이 발견되었습니다.
L1324: 📊 Director 판정: REJECT (초기: REJECT, 점수: 78, 선택: 후보 A)
L1391: 🔥 [ASP] 레드팀 교정 발동 (재시도 3회차)
L1427: 📊 Director 판정: PASS (초기: PASS, 점수: 95, 선택: 후보 A)
L1458: ✅ 제5화 '제5화: 여의도 입성' 생산 완료! (7172자)
```

### EP6 Console Rounds
```
L1462: 📝 제6화 집필 시작 (Arc 2, 위치 2/5)
L1508: 📊 Director 판정: REJECT (초기: REJECT, 점수: 75, 선택: 후보 C)
L1509: └─ 사유: 직전 화와의 장소 연속성 단절 (시중은행 -> 한미증권)
L1535: [모순 세부] [MAJOR] 상태: 설명 없이 '여의도 한미증권 본점 VIP룸'으로 장소가 변경됨
L1536: [모순 세부] [MINOR] 수학: 15억 원 사용 후 잔액을 5억 원으로 표기함 (정상 산술: 4.7억)
L1576: 📊 Director 판정: PASS (초기: PASS, 점수: 90, 선택: 후보 A)
L1584: 사유: Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭합니다
L1587: ⚠️ [CoVe] 사후검증 경고: 직전 화 아이템(패)이 현재 화에서 언급되지 않음
L1588: ⚠️ [CoVe] LLM 검증 런타임 실패 → Director PASS 유지
L1608: ✅ 제6화 '제6화: 15억의 베팅' 생산 완료! (5896자)
```

### EP7 Console Rounds
```
L1611: 📝 제7화 집필 시작 (Arc 2, 위치 3/5)
L1661: 📊 Director 판정: REJECT (초기: REJECT, 점수: 86, 선택: 후보 C)
L1662: └─ 사유: 직전 화와의 장소 연속성 오류
L1666: 세 후보 모두 Blueprint의 오류를 그대로 수용하여 직전 화의 장소(시중은행 본점)를
       '여의도 한미증권'으로 잘못 기재하는 모순을 범했으나
L1721: 📊 Director 판정: REJECT (초기: REJECT, 점수: 75, 선택: 후보 A)
L1722: └─ 사유: 작품 전체 시점(3인칭) 위반
L1744: [모순 세부] [MAJOR] 상태: 후보 A는 전체가 1인칭 주인공 시점('나는', '내')으로 서술됨
L1774: 🔥 [ASP] 레드팀 교정 발동 (재시도 3회차)
L1812: 📊 Director 판정: PASS (초기: PASS, 점수: 96, 선택: 후보 A)
L1842: ✅ 제7화 '조롱과 확신' 생산 완료! (5109자)
```

## E-2. episode_production.jsonl Raw Entries (EP5-EP7)

Source: `episode_production.jsonl`

### EP5 Blueprint
```json
L26: {"timestamp":"2026-03-24 18:03:13","type":"blueprint_success","data":{"ep_num":5,"arc_no":1,"strategy":"emotion_focused","score":95,"final_verdict":"PASS"}}
```
Note: arc_no=1 is incorrect. Console shows Arc 2.

### EP5 Pathology
```json
L35: {"timestamp":"2026-03-24 18:37:08","type":"stage4_retry_pathology_signal","data":{"ep_num":2,"round_num":1,"pathology_fingerprint":"constraint_violation|contradiction:레버리지계산|fix_pack_ready","gate_basis":"post_select_conflict","score":93}}
L36: {"timestamp":"2026-03-24 18:41:00","type":"stage4_retry_pathology_signal","data":{"ep_num":2,"round_num":2,"pathology_fingerprint":"constraint_violation|contradiction:수치|fix_pack_ready","gate_basis":"post_select_conflict","score":93,"plateau_detected":true}}
```
Note: ep_num=2 in these entries — this is actually EP5 data based on timestamp alignment with quality_metrics EP5 validation events at the same timestamps.

### EP6 Pathology
```json
L37: {"timestamp":"2026-03-24 18:54:40","type":"stage4_retry_pathology_signal","data":{"ep_num":6,"round_num":1,"gate_basis":"director_primary_reject","score":83,"contradiction_type":"타임라인"}}
L38: {"timestamp":"2026-03-24 18:58:25","type":"stage4_retry_pathology_signal","data":{"ep_num":6,"round_num":2,"gate_basis":"continuity_firewall","score":69,"contradiction_type":"자본금정합","firewall_triggered":true,"fix_pack_ready":false}}
```

### EP6 CoVe Advisory
```json
L39: {"timestamp":"2026-03-24 19:03:47","type":"stage4_cove_runtime_advisory","data":{"ep_num":6,"round_num":2,"error_type":"ChainOfVerificationParseError","director_pass_preserved":true}}
```

### EP7
No pathology entries exist for EP7 in episode_production.jsonl.

## E-3. quality_metrics.jsonl Validation Events (EP5-EP7 Stage 4)

Source: `quality_metrics.jsonl`

### EP5 Validation Chain
```
L47: validation REJECT, ep_num=5, stage=4, score=93, ts=18:37:08
L49: validation REJECT, ep_num=5, stage=4, score=93, ts=18:41:00
L51: blueprint_coverage ep_num=5, coverage=100%, ts=18:48:28
L52: validation PASS, ep_num=5, stage=4, score=95, ts=18:48:28
```
Director retrieval observations: 3 (L46: 18:32:49, L48: 18:39:28, L50: 18:45:29)

### EP6 Validation Chain
```
L55: validation REJECT, ep_num=6, stage=4, score=78, ts=18:54:40
L57: validation REJECT, ep_num=6, stage=4, score=44, ts=18:58:25
L59: blueprint_coverage ep_num=6, coverage=60%, ts=19:05:07
L60: validation PASS, ep_num=6, stage=4, score=98, ts=19:05:07
```
Director retrieval observations: 3 (L54: 18:52:19, L56: 18:57:33, L58: 19:02:09)

### EP7 Validation Chain
```
L63: blueprint_coverage ep_num=7, coverage=60%, ts=19:16:44
L64: validation PASS, ep_num=7, stage=4, score=90, ts=19:16:44
```
Director retrieval observations: **1** (L62: 19:09:46)
No validation REJECT entries for EP7.

## E-4. Sink Mismatch Evidence Summary

### EP7 JSONL Blackout — Missing Event Inventory

| Expected Event | Present in Console | Present in quality_metrics | Present in episode_production |
|---|---|---|---|
| EP7 R1 Director retrieval | yes (implicit) | NO | N/A |
| EP7 R1 validation REJECT | yes (L1661, score 86) | NO | NO |
| EP7 R2 Director retrieval | yes (implicit) | NO | N/A |
| EP7 R2 validation REJECT | yes (L1721, score 75) | NO | NO |
| EP7 R3 Director retrieval | yes (implicit) | yes (L62) | N/A |
| EP7 R3 validation PASS | yes (L1812, score 96) | yes (L64, score 90) | NO |

5 of 6 expected EP7 Stage 4 events are missing from JSONL sinks.

### EP6 R2 — Three-Way Disagreement Detail

| Property | Console | quality_metrics | episode_production |
|---|---|---|---|
| Verdict | PASS | REJECT | (pathology: firewall) |
| Score | 90 | 44 | 69 |
| Gate | director_primary_pass | director_reject | continuity_firewall |
| Firewall | not visible | (implied) | firewall_triggered=true |
| CoVe | runtime failure, PASS preserved | (no CoVe entry) | CoVe advisory recorded separately |

### EP5 R1 — Contradiction Type Disagreement

| Property | Console | episode_production |
|---|---|---|
| Contradiction subject | 박성호 PB 소속 (시중은행→한미증권) | 레버리지 배수 vs 진입 계약 수 |
| Contradiction category | NPC affiliation | arithmetic |
| Gate | post_select_conflict | post_select_conflict |
| Score | 92 (PASS_WITH_FIX) | 93 |

Both contradictions are real, but the sinks disagree on which to surface as primary.

## E-5. Blueprint Arc Assignment — Stage 3 to Stage 4 Propagation

```
EP5: Stage 3 blueprint at 18:03:13 → PASS score 95, arc_no=1 (ERROR: should be 2)
EP6: Stage 3 blueprint at 18:09:51 → PASS score 95, arc_no=2
EP7: Stage 3 blueprint at 18:11:22 → PASS score 95, arc_no=2
```

Console confirms all three are Arc 2 episodes:
```
L880: 📐 제5화 Blueprint 생성 중... (Arc 2, 주인공: 한시우)
L894: 📐 제6화 Blueprint 생성 중... (Arc 2, 주인공: 한시우)
L911: 📐 제7화 Blueprint 생성 중... (Arc 2, 주인공: 한시우)
```

EP6 blueprint scored 100 in console (L897: `제6화 Blueprint 결과: PASS (score=100)`) but quality_metrics recorded it as score 95 (L34). Another minor sink mismatch.

## E-6. Common Root Cause — 한미증권 Location Error

The 한미증권 location error appears as a rejection cause in:
- EP5 R1 console: 박성호 PB affiliation (시중은행→한미증권)
- EP6 R1 console: "설명 없이 '여의도 한미증권 본점 VIP룸'으로 장소가 변경됨"
- EP6 R2 console: (implicit — R2 manuscript corrected to 시중은행 per Director feedback)
- EP7 R1 console: "세 후보 모두 Blueprint의 오류를 그대로 수용하여... '여의도 한미증권'으로 잘못 기재"
- EP7 R2 console: (location corrected but POV error introduced)

Director explicitly attributes the error to the Blueprint in both EP6 and EP7:
- L1584: "Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭합니다"
- L1679-1680: "Blueprint에 잘못 기재된 장소(한미증권)를 AI가 그대로 받아들여 발생한 오류입니다"

This points to T3 (Stage 3 Blueprint Truth) as the upstream investigation lane for the content root cause.
