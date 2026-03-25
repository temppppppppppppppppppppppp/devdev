# T2 Dominant Seam Delta — Dissent Note

Date: 2026-03-24
Status: dissent note (NOT merged conclusion)
Author: Terminal 2 independent survey
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
Public Report: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md` (Terminal 1 작성, 수정 없음)
Evidence Ledger: `docs/2026-03-24/opus-live-run-residual/t2-dominant-seam-delta-evidence.md`
Primary Evidence Run: `projects/0324_00_`

---

## 문서 성격

이 문서는 Terminal 1이 작성한 공용 report에 대한 **Terminal 2의 독립 조사 결과 dissent note**이다.
공용 report를 수정하거나 대체하지 않는다.
오퍼레이터가 두 판정을 비교 검토한 뒤 seam classification을 확정한다.

---

## 1. Terminal 1과의 일치점

| 항목 | Terminal 1 | Terminal 2 | 일치 |
|------|-----------|-----------|------|
| Post-select rejects mostly valid | yes | yes | O |
| Execution SSOT 즉시 생성 | no | no | O |
| Old covert-infrastructure seam | CLEARED | CLEARED | O |
| Stage 2 density/ep-count | CLEARED | CLEARED | O |
| PASS_WITH_FIX vs post-select 분리 | 정상 작동 | 정상 작동 | O |
| `_inventory_gaps` net assessment | net-helpful, off-axis | net-neutral, off-axis | O (사실상 동의) |
| Confidence | 88% | 88% | O |
| EP2 attribution | Stage 3 PRIMARY | Stage 3 PRIMARY | O |
| EP7 attribution | Writer PRIMARY (minor) | Blueprint-originated (minor) | ~ (경미) |
| Broad semantic-carryover relapse | PARTIALLY CLEARED | CLEARED for old form | ~ |

---

## 2. 핵심 불일치: Dominant Seam 판정

| | Terminal 1 | Terminal 2 |
|---|---|---|
| **Dominant seam** | **mixed seam** | **stage3 blueprint under-specification** |
| Stage 3 primary count | 1/5 (EP2만) | 6/9 conflicts (67%) |
| Stage 4 writer primary count | 4/5 (EP3,5,6,7) | 3/9 conflicts (33%) |

### 불일치 원인

Terminal 1은 EP5/EP6 blueprint의 prevalidation 결과 `quality_risk=false`, `0 prevalidation issues`를 근거로 blueprint를 "clean"으로 분류하고, 해당 에피소드의 conflicts를 Stage 4 writer invention으로 귀속시켰다.

Terminal 2는 prevalidation의 "clean" 판정이 **syntactic validity**만 검사한다는 점을 지적한다. Prevalidation은 JSON 구조, 필수 필드 존재, scene 개수 등을 검사하지, **cross-episode capital reconciliation**은 검사하지 않는다. Blueprint가 syntactically clean이면서 **semantically wrong**인 것이 EP5/EP6의 핵심 패턴이다.

### 재집계 (Terminal 2 기준)

| Conflict | Blueprint Error | Writer Error | 근거 |
|----------|:-:|:-:|---|
| EP2 provenance (조부 vs 어머니) | **PRIMARY** | — | §3-A |
| EP3 note location (금고 vs 서랍) | — | **PRIMARY** | §3-B |
| EP3 timeline (같은날 vs 다음날) | **PRIMARY** | — | §3-B |
| EP5 capital (5천만원 미차감) | **PRIMARY** | — | §3-C |
| EP5 leverage (198만$ arithmetic) | **PRIMARY** | — | §3-C |
| EP6 capital (전액투입 vs 19.3억 잔존) | **PRIMARY** | — | §3-D |
| EP6 timeline (2월 vs 4월) | — | **PRIMARY** | §3-D |
| EP6 coat (짐가방 vs 부티크) | — | **PRIMARY** | §3-D |
| EP7 phrasing (18년 전) | **PRIMARY** | — | §3-E |

**Stage 3 blueprint PRIMARY: 6/9 (67%)**
**Stage 4 writer PRIMARY: 3/9 (33%)**

---

## 3. 에피소드별 attribution 근거

### 3-A. EP2: 일치 (Stage 3 PRIMARY)

양쪽 모두 동의. Blueprint L60에 "조부 명의의 HMC투자증권 신탁 계좌"로 명시되어 있고, EP1 확정 canon은 "어머니".

File anchor:
- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json` **L60**

### 3-B. EP3: 부분 일치

Terminal 1: "Mixed (Blueprint MAJOR warning + Writer drift)" → Writer PRIMARY
Terminal 2: note location은 Writer PRIMARY (동의), timeline은 Blueprint PRIMARY (불일치)

Blueprint에 PB 방문이 같은 날인지 다음 날인지 **명시하지 않음**. Writer가 같은 날로 압축한 것은 blueprint 공백을 채운 결과이지 적극적 invention이 아님. Blueprint가 day boundary를 명시했다면 발생하지 않았을 conflict.

### 3-C. EP5: 핵심 불일치 — Blueprint-Origin Capital Mismatch

**Terminal 1 판정**: Writer PRIMARY ("Blueprint는 깨끗하나 writer가 원고 확장 시 수치를 drift")
**Terminal 2 판정**: Blueprint PRIMARY

#### 근거 1: Blueprint가 EP4 지출을 반영하지 않은 시작 자본을 명시

EP5 blueprint `integrated_scenario` (L27):
> "계좌 잔고에 찍힌 **1,930,000,000원**을 확인한 한시우는"

EP5 blueprint `scene_2.key_events` (L74):
> "**19억 3천만 원**을 해외 선물용 달러(약 198만 달러)로 환전"

EP4에서 법인 설립 자본금 **5천만 원**을 지출했으므로, EP5 시작 시점의 실제 가용 자본은 **18억 8천만 원**(=19.3억-0.5억)이어야 한다. Blueprint가 19.3억을 그대로 명시한 것은 **Stage 3가 EP4 지출을 cross-reference하지 않은 것**이다.

Writer는 blueprint의 19.3억을 충실히 따랐고, 화면에 19억(=19.3억-보증금3천만)을 표시했다. Post-select가 잡은 "5천만원 미반영"은 blueprint가 이미 잘못된 시작 자본을 명시했기 때문이다.

#### 근거 2: Blueprint의 환전 arithmetic 자체가 부정확

EP5 blueprint L74: "19억 3천만 원 → 약 198만 달러 (환율 970원)"
실제: 1,930,000,000 ÷ 970 = **1,989,690.72** → 약 **199만 달러**, not 198만

이 arithmetic error는 writer가 만든 것이 아니라 **blueprint에 내장된 오류**다.

File anchors:
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json` **L27, L33, L70, L74, L77**

### 3-D. EP6: 핵심 불일치 — Blueprint-Origin Capital Contradiction

**Terminal 1 판정**: Writer PRIMARY ("Blueprint는 깨끗. Writer가 2월→4월 invention")
**Terminal 2 판정**: Capital은 Blueprint PRIMARY, Timeline은 Writer PRIMARY

#### 근거: EP5→EP6 cross-blueprint capital 모순

EP5 blueprint L27 (integrated_scenario):
> "약 198만 달러의 자본이 WTI 롱 포지션에 **쏟아져 들어간다**"

EP5 blueprint L33 (equipment):
> "약 198만 달러가 예치된 **파생상품 계좌**"

→ EP5 종료 시 19.3억 전액이 WTI 롱 포지션에 투입 완료.

EP6 blueprint L32 (equipment):
> "**19억 3천만 원이 예치된 계좌 내역**"

EP6 blueprint L51 (scene_1 content):
> "**19억 3천만 원의 시드머니를 온전히 쏟아부을** 3배 레버리지"

→ EP6 시작 시 19.3억이 아직 계좌에 있고, 이제 3배 레버리지로 투입할 예정.

**이 두 상태는 상호 배타적이다.** EP5에서 전액 WTI에 투입했으면, EP6에서 19.3억이 계좌에 있을 수 없다. Stage 3가 EP5 accepted manuscript의 최종 자본 상태를 EP6 blueprint에 반영하지 않았다.

Terminal 1이 지적한 EP6의 timeline invention (2월→4월)과 coat source (짐가방→부티크)는 writer error가 맞다. 그러나 continuity_firewall을 발동시킨 **핵심 conflict** ("EP5에서 19억원을 전액 WTI에 투입했으므로 가용 현금 20억원 없음")는 blueprint-level capital 모순에서 기인한다.

File anchors:
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json` **L27, L33**
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json` **L32, L51, L52**

### 3-E. EP7: 경미한 불일치

Terminal 1: Writer PRIMARY. Terminal 2: Blueprint-originated (minor).
"18년 전"은 시간 메타포 오류로 양쪽 모두 minor 판정. Attribution 차이가 dominant seam 판정에 영향 없음.

---

## 4. Terminal 1 수치 오류 지적

### EP3 Final Score

| | Terminal 1 Report (§2 Table) | Console 실물 |
|---|---|---|
| EP3 Final Score | **97** | **90** |

Terminal 1 table에서 EP3의 Final Score를 97로 기재했으나, 97은 **rejected Round 1**의 Director score이다. Accepted Round 2의 Director score는 **90**이다.

Terminal 1 report `ep1-ep8-live-run-residual-opus-survey-report.md` L33:
> "| 3 | 2 | PASS | **97** | Leather notebook storage + timeline regression |"

Console evidence (Terminal 2 agent 수집):
> EP3 Round 1: Director Score **97** → REJECT (post_select_conflict)
> EP3 Round 2: Director Score **90** → PASS (director_primary_pass)

---

## 5. Confidence and Limits

### Confidence: 88%

Terminal 1과 동일한 88%이나 근거가 다르다.

**높은 확신 (90%+)**:
- EP5 blueprint가 19.3억을 시작 자본으로 명시한 사실 → blueprint 실물 L27, L74 직접 확인
- EP6 blueprint가 19.3억을 아직 가용으로 명시한 사실 → blueprint 실물 L32, L51 직접 확인
- EP5→EP6 cross-blueprint capital 모순 → 상호 배타적 상태 확인

**제한 (88% 미만 요소)**:
- Arc-level state_constraints 미직접 검사: "전액 투입"이 arc plan에서 온 것인지, Stage 3 blueprint 생성 LLM이 invention한 것인지 미확인
- EP4 blueprint/manuscript 미검사: 5천만원 지출이 EP4 canon에서 어떻게 표현되었는지 미확인
- Stage 3 orchestrator의 이전 에피소드 참조 메커니즘 (`semantic_ctx`, window 기반)의 실제 동작 미추적

### 95% 도달 조건

1. Arc 1 tactical document (`projects/0324_00_/logs/artifacts/stage2/arc_001/`)에서 episode별 capital allocation 명세 확인
2. EP4 accepted manuscript에서 5천만원 지출 장면 확인
3. Stage 3 orchestrator가 blueprint 생성 시 이전 accepted manuscript를 참조하는 code path의 window 크기 및 state extraction 로직 확인

---

## Mandatory Final Lines (Terminal 2 Independent)

- **Dominant seam**: stage3 blueprint under-specification
- **Are the repeated post-select rejects mostly valid**: yes
- **Should Codex open an execution SSOT immediately**: no
