# Terminal 6 Lane: Stage 4 Carryover Consumption — Blueprint Artifact Cross-Verification

Date: 2026-03-24
Terminal: 6
Status: lane findings (proposal — merge owner 판정 대기)
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
Primary Evidence Run: `projects/0324_00_`
Scope: Stage 4 carryover 관점에서 blueprint 본문↔원고 직접 대조. V2 attribution에 대한 correction proposal.

---

## 1. Lane Summary

터미널 6은 V2 report의 "Stage 4 writer drift/invention" attribution 3건(EP3, EP6, EP7)에 대해 **blueprint artifact 본문을 원고와 직접 대조**했다. 결과:

- **EP3**: Blueprint Scene 2가 "서랍 깊숙이 보관"을 명시 → writer는 blueprint 충실 추종
- **EP7**: Blueprint ending hook이 "18년 전"을 명시 → writer는 hook 충실 재현
- **EP6**: Blueprint equipment에 "19억 3천만 원이 예치된 계좌 내역" 기재 → EP5에서 전액 WTI 투입 완료 → stale state

이 3건에서 writer가 독자적으로 drift/invention한 것이 아니라 **blueprint가 제공한 잘못된/stale 정보를 충실히 소비**한 것으로 판단된다.

**이 판단은 proposal**이다. V2와의 attribution 가중치 차이에 대한 final 판정은 Codex merge owner에게 남긴다.

---

## 2. Correction Proposal 3건

### Proposal A: EP3 "서랍" — Blueprint Authority Error

**V2 기술**: "Writer가 가죽 노트 보관 위치를 '금고'에서 '서랍'으로 drift"
**T6 대조 결과**: EP3 blueprint Scene 2 원문이 "서랍 깊숙이 보관"을 명시

| 항목 | V2 판단 | T6 대조 |
|------|---------|---------|
| Blueprint 원문 | 미대조 (quality_risk=true만 확인) | Scene 2: "방으로 돌아와 18년 치 거시경제 지표 노트를 **서랍 깊숙이** 보관" |
| Writer 행동 | "금고→서랍 drift" | Blueprint "서랍" 지시 충실 추종 |
| Post-select rejection | writer drift | blueprint 지시 vs EP2 확정 원고 "금고" 간 모순 |
| Attribution proposal | Writer PRIMARY → **Blueprint PRIMARY** | Writer는 SECONDARY (3:35pm timestamp만 자체 배정) |

**추가 발견**: EP3 blueprint의 "오후 4시 은행 마감 전 처리 요구" 시간 제약은 EP2 서재 독대 종료 시점(4:35pm)과 양립 불가. Blueprint가 같은 날 은행 방문을 전제한 것이 timeline regression의 구조적 원인.

**Evidence**: `t6-stage4-carryover-consumption-evidence.md` §A

### Proposal B: EP7 "18년 전" — Blueprint Ending Hook Error

**V2 기술**: "Stage 4 Writer Manuscript Invention (minor)"
**T6 대조 결과**: EP7 blueprint ending hook 원문이 "18년 전"을 명시

| 항목 | V2 판단 | T6 대조 |
|------|---------|---------|
| Blueprint 원문 | "clean" (prevalidation=0) | Ending hook: "18년 전 나를 짓눌렀던 파산의 환상통" |
| Writer 행동 | "시간 메타포 오류 invention" | Blueprint ending hook 충실 재현 |
| PASS_WITH_FIX target | Writer가 잘못 쓴 표현 | Blueprint가 잘못 명시한 표현 |
| Attribution proposal | Writer PRIMARY → **Blueprint PRIMARY** | Writer는 hook 충실 추종만 |

**코드 근거**: PASS_WITH_FIX는 원고를 수정하지만, 근원은 blueprint ending hook. Blueprint prevalidation이 ending hook 시간 표현을 검증하지 않음.

**Evidence**: `t6-stage4-carryover-consumption-evidence.md` §B

### Proposal C: EP6 Equipment "19.3억 예치" — Blueprint Stale State

**V2 기술**: "Blueprint (dialogue_focused, attempt_03)는 clean"
**T6 대조 결과**: Blueprint equipment에 "19억 3천만 원이 예치된 계좌 내역" 기재되어 있으나, EP5에서 이 자금은 전액 달러 환전 → WTI 480계약 증거금으로 투입 완료

| 항목 | V2 판단 | T6 대조 |
|------|---------|---------|
| Blueprint equipment | "clean" | "19억 3천만 원이 예치된 계좌 내역" — stale (이미 WTI 증거금) |
| Writer 행동 | "20억 법인 자금 invention" | Stale equipment 기반으로 가용 현금 존재를 전제 → 20억 발명 |
| 날짜 변경 (2월→4월) | Writer invention | Writer invention (이 축은 V2 정확) |
| Attribution proposal | Writer PRIMARY(100%) → **Writer CO-PRIMARY(60%) + Blueprint SECONDARY(40%)** | 날짜=writer, 자본=blueprint stale state가 enabling factor |

**코드 근거**: Blueprint schema `protagonist_state`에 구조화된 금융 필드 없음. Equipment string으로 금융 상태를 전달하므로 "예치"와 "증거금 투입"의 구별 불가.

**Evidence**: `t6-stage4-carryover-consumption-evidence.md` §C

---

## 3. V2 오판 원인 (T6 관점)

V2는 blueprint prevalidation flag에 의존하여 "clean" 판정 후 conflict를 writer에 귀속했다:

1. **Prevalidation은 blueprint-vs-previous-manuscript 사실 일관성을 검사하지 않음** → EP3 "서랍" 통과
2. **Prevalidation은 ending hook 시간 표현을 검증하지 않음** → EP7 "18년 전" 통과
3. **Equipment 필드의 금융 상태 정확성은 prevalidation 범위 밖** → EP6 stale "19.3억 예치" 통과

Blueprint "clean" ≠ Blueprint "correct". Prevalidation flag만으로는 blueprint 본문의 사실 정확성을 보장할 수 없다.

---

## 4. Attribution Rebalance Proposal

| 축 | V2 가중치 | T6 proposal | Delta 근거 |
|----|----------|-------------|-----------|
| Stage 3 blueprint primary/co-primary | ~25% | **~55%** | EP3·EP7 → blueprint primary, EP6 → blueprint secondary 추가 |
| Stage 4 writer primary/co-primary | ~65% | **~30%** | EP3·EP7의 "writer drift"가 실제로는 blueprint 충실 추종 |
| Cross-stage gap | ~10% | **~15%** | EP5 법인설립비: 양측 모두 미추적 |

**이 rebalance는 proposal**이다. Final 판정은 Codex merge owner가 다른 터미널 lane 결과와 병합하여 결정.

---

## 5. Stage 4 Carryover System 정상 작동 확인 사항

V2 conclusion과 일치하는 확인 사항 (correction 아님):

1. **Post-select conflict detection**: 전 에피소드에서 정확 작동. 잡아야 할 것을 잡고 있음.
2. **PASS_WITH_FIX ↔ post-select 우선순위**: Post-select가 항상 먼저 실행, conflict 시 REJECT override. 코드 확인 완료 (`stage4_interview_round.py` L3635-3799, L4000-4049).
3. **Continuity firewall**: EP6 R2에서 정확 발동 (score 44). Capital consistency violation 정확 감지.
4. **Retry escalation**: post_select_conflict → fix_scope="full" → full rewrite. 정상 작동.
5. **Carryover packet 4-channel 구조**: prev_ending(2,500자) + prev_digest(regex) + carryover_ceiling + IFC — 모두 정상 전달 확인.

---

## 6. 근본 구조적 발견

Stage 3 blueprint schema (`BLUEPRINT_PROTAGONIST_STATE_SCHEMA`)에 구조화된 금융/시간/provenance 필드가 없다:
- 현재 schema: `mood` (string), `injuries` (string), `equipment` (string)
- 금융 수치: equipment string 또는 scene description 산문에 비구조화 포함
- Cross-episode 정합성: prevalidation 범위 밖

금융 상태는 Stage 4 carryover pipeline (prev_digest regex + carryover_ceiling + IFC)이 보완하지만, **blueprint가 직접 잘못된 수치를 명시하면 carryover의 정확한 수치와 blueprint의 stale 수치가 충돌**하는 구조.

Writer는 authority priority (blueprint > carryover)에 따라 blueprint를 우선 추종하므로, blueprint의 stale state가 carryover의 정확한 state를 override하는 역설이 발생.

---

## 7. Mandatory Final Lines

- **T6 lane dominant finding**: V2의 EP3·EP7·EP6 writer attribution에 blueprint artifact 본문 대조 기반 correction proposal 3건
- **Proposed attribution rebalance**: Stage 3 ~55% / Stage 4 ~30% / cross-stage ~15% (V2: 25/65/10)
- **This is a proposal, not a merged conclusion**: Final 판정은 Codex merge owner에게 남김
- **Post-select rejects mostly valid**: yes (V2와 일치)
- **Execution SSOT**: no (V2와 일치)
