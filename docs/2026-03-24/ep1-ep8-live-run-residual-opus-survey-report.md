# EP1-EP8 Live-Run Residual Opus Survey Report

Date: 2026-03-24
Status: survey-only (final, V2 — fresh Opus re-survey merged)
Canonical Path: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md`
Primary Evidence Run: `projects/0324_00_`
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
Baseline Commit: `f61a35c8`
V2 Note: V1 결론은 본질적으로 정확. V2에서 Stage 4:Stage 3 attribution 가중치 정밀화, _inventory_gaps 부재 발견, EP5→7 자금 흐름 불일치 추가, 코드 메커니즘 교차 확인 반영.

---

## 1. Executive Summary

8화 live run 전량 조사 결과, 기존 Stage 2→3 경계 수정과 Stage 4 carryover-expansion 수정 이후에도 잔류하는 **dominant seam은 mixed seam**이다.

두 개의 구분되는 failure family가 공존하며, V2 재조사로 가중치가 비대칭임이 확인되었다:

1. **Stage 4 writer carryover consumption failure (4/5 troubled ep, ~65%)** — EP3, EP5, EP6, EP7. Blueprint는 깨끗하나 ChiefWriter LLM이 carryover packet을 충실히 소비하지 못하고 수치/시간/아이템위치를 drift하여 post-select 또는 Director에서 잡힘
2. **Stage 3 blueprint authority error (1/5 troubled ep, ~25%)** — EP2. Blueprint가 EP1 확정 사실과 다른 신탁 출처를 명시하여 writer가 이를 충실히 따라가다가 3라운드 소비
3. **잔여 10%**: EP5의 레버리지 산술은 blueprint gap과 writer 누락이 혼합된 사례

Post-select conflict detection 시스템 자체는 정상 작동하고 있으며, 잡아야 할 것을 잡고 있다. 문제는 **conflict가 발생하는 근원**이 Stage 4 primary / Stage 3 secondary로 분산되어 있으나, Stage 4 consumption 강화가 최우선 ROI라는 점이다.

---

## 2. Run Outcome Snapshot

| Episode | Rounds | Final | Score | Primary Conflict | Gate Basis |
|---------|--------|-------|-------|------------------|------------|
| 1 | 1 | PASS | 95 | — | director_primary_pass |
| 2 | 4 | PASS | 96 | Trust provenance flip (grandfather→mother) | post_select_conflict ×3 → pass |
| 3 | 2 | PASS | 97 | Leather notebook storage + timeline regression | post_select_conflict ×1 → pass |
| 4 | 1 | PASS | 96 | — | director_primary_pass |
| 5 | 3 | PASS | 95 | Capital accounting (5천만 법인설립비 누락) + leverage arithmetic | post_select_conflict ×2 → pass |
| 6 | 3 | PASS | 98 | Timeline invention (2월→4월) + location/item drift | director_reject + continuity_firewall → pass |
| 7 | 1 | PASS | 94 | "18년 전" phrasing (PASS_WITH_FIX patched) | director_pass_with_fix → pass |
| 8 | 1 | PASS | 98 | — | director_primary_pass |

**총 생산 라운드**: 16 (ep1~8 합산)
**1라운드 완료율**: 4/8 (50%) — ep1, ep4, ep7 (PASS_WITH_FIX→patch→PASS), ep8
**2라운드 이내 완료율**: 5/8 (62.5%) — + ep3
**최다 라운드**: ep2 (4회), ep5 (3회), ep6 (3회)

---

## 3. Episode-by-Episode Conflict Ledger

### EP2: Trust Provenance Authority Conflict

**Conflict Origin: Stage 3 Blueprint**

Blueprint (dialogue_focused, attempt_02)는 신탁 출처를 **"조부 명의 HMC투자증권 신탁"**으로 명시했다. 그러나 EP1 확정 원고에서 해당 신탁은 **"어머니가 남겨준 20억 원 신탁"**으로 확립되었다.

- **Round 1**: Writer가 blueprint를 충실히 따라 "조부 명의 신탁" 작성 → post-select history conflict → REJECT
- **Round 2**: Writer가 부분 수정 시도하나 설정 불일치 잔류 → post-select history conflict → REJECT
- **Round 3**: Timeline mismatch 잔류 (오전 10시 vs 늦은 오후) → post-select → REJECT
- **Round 4**: Provenance를 "어머니" 기준으로 완전 정규화 + timeline 정합 → PASS

**First hard conflict**: Blueprint authority (Stage 3이 EP1 확정 사실과 다른 provenance를 명시)

**부가 신호**:
- [V66.1] "이미 소유한 '가죽 노트'를 다시 획득하려 함" — valid signal (아이템 이중 획득 감지)
- [TF-49] "18년 치 거시경제 지표 노트" — correct advisory (아직 물리적 획득 장면 미확보)

### EP3: Item Storage + Timeline Regression

**Conflict Origin: Mixed (Blueprint MAJOR warning + Writer drift)**

Blueprint (emotion_focused, attempt_01)는 MAJOR continuity warning을 포함: "서재 앞→본가 2층 복도" location discontinuity. Blueprint 자체에 quality_risk=true 플래그.

- **Round 1**: Writer가 가죽 노트 보관 위치를 "금고"에서 "서랍"으로 drift + 시간선 역행 (4:35 PM → 3:35 PM) → post-select continuity conflict → REJECT
- **Round 2**: 보관 위치 "금고" 유지 + 시간선 "오후 4시 35분 이후" 정합 → PASS

**First hard conflict**: Writer manuscript expansion (Blueprint warning 존재했으나 writer가 다른 축에서 drift)

**부가 신호**:
- Blueprint의 MAJOR location warning은 실제 rejection 사유가 아님 (writer가 자체 해결)
- 실제 rejection은 아이템 보관 위치와 시간 앵커 — blueprint에 명시되지 않은 디테일

### EP5: Capital Accounting + Leverage Arithmetic

**Conflict Origin: Stage 4 Writer Manuscript Invention**

Blueprint (emotion_focused, attempt_01)는 clean (0 prevalidation issues, quality_risk=false). 1.933B₩→1.98M USD 변환, WTI long entry 명시.

- **Round 1**: Director gives PASS_WITH_FIX (score 93) for leverage arithmetic ("3배 레버리지" 독백 vs 실제 480계약=15배). 그러나 post-select에서 별도 capital accounting conflict 감지 — EP4의 5천만 원 법인설립비가 EP5 잔고에 미반영 → REJECT
- **Round 2**: Leverage 수정되었으나 capital accounting 잔류 → post-select → REJECT
- **Round 3**: 잔고 정합 + leverage 정합 → PASS

**First hard conflict**: Writer manuscript expansion (EP4에서 지출한 5천만 원이 EP5 잔고에 반영 안 됨)

**핵심 관찰**: PASS_WITH_FIX (Director)와 post-select conflict (validator)가 **같은 라운드, 다른 축**에서 동시 발화. Director는 leverage 표현을, post-select는 capital 수치를 각각 잡음. 이 두 시스템은 **분리된 검출 축**으로 정상 작동.

### EP6: Timeline Invention + Continuity Firewall

**Conflict Origin: Stage 4 Writer Manuscript Invention**

Blueprint (dialogue_focused, attempt_03)는 clean. "2006년 2월 하순" 배경, 박성호 PB 조우, B등급 펀드 논파.

- **Round 1**: Writer가 배경 시간을 **"2006년 4월 18일"**로 invention → 2+ 개월 점프 → Director REJECT (score 78). 추가: 사무실→오피스텔 명칭 drift, 코트 획득 경로 불일치
- **Round 2**: 시간선 부분 수정했으나 continuity firewall rejection (score 44) → REJECT
- **Round 3**: "2006년 2월 하순" 정규화 + 위치/아이템 정합 → PASS (score 98)

**First hard conflict**: Writer manuscript expansion (blueprint "2월 하순"을 writer가 "4월 18일"로 변경)

**특이점**: Round 2에서 continuity_firewall gate가 발동 (score 44). 이는 post-select 이전에 Director/firewall 단에서 잡힌 경우로, EP6이 유일하게 Director primary reject를 받은 에피소드.

### EP7: Temporal Metaphor Phrasing

**Conflict Origin: Stage 4 Writer Manuscript Invention (minor)**

Blueprint (emotion_focused, attempt_01)는 clean.

- **Round 1**: Director gives PASS_WITH_FIX (score 94). "18년 전 파산의 환상통" → 2006년 기준 18년 전은 1988년이지만, 주인공 파산은 2024년(미래). 수정: "18년 전" → "전생에". Patch 성공 → PASS

**First hard conflict**: Writer manuscript expansion (시간 메타포 오류)

**특이점**: PASS_WITH_FIX가 정상 작동한 사례. inplace fix_scope + 명확한 patch_target으로 1라운드 내 해결.

### EP8: Baseline Comparison (Clean)

Blueprint (action_focused, attempt_01)는 clean. Director PASS score 98. 1라운드 통과.

EP8은 EP7 직후 연속 시퀀스 (margin pressure 지속)로, 서사적으로 새로운 상태 전이가 적어 conflict 발생 확률이 낮았다.

---

## 4. Stage Attribution Ledger

| Episode | Blueprint 기여 | Writer-Packet 기여 | Writer Invention | Post-Select Validator | Director |
|---------|---------------|-------------------|-----------------|----------------------|----------|
| EP2 | **PRIMARY** (provenance 오류) | 정상 전달 | Blueprint 충실 추종 | 3회 정확 감지 | 미감지 (PASS 부여) |
| EP3 | SECONDARY (MAJOR warning 존재) | 정상 전달 | **PRIMARY** (storage + timeline drift) | 1회 정확 감지 | 미감지 |
| EP5 | 정상 | 정상 전달 | **PRIMARY** (capital accounting + leverage) | 2회 정확 감지 | PASS_WITH_FIX (leverage만) |
| EP6 | 정상 | 정상 전달 | **PRIMARY** (timeline 2월→4월) | N/A (Director reject) | 정확 감지 |
| EP7 | 정상 | 정상 전달 | **PRIMARY** (temporal metaphor) | N/A | PASS_WITH_FIX 정확 |

**Stage 3 primary attribution**: 1/5 (EP2만) — V2 확인: Stage 3은 secondary source
**Stage 4 writer primary attribution**: 4/5 (EP3, EP5, EP6, EP7) — V2 확인: Stage 4 consumption이 dominant (~65%)
**Validator/Director 정확도**: 전 에피소드에서 conflict를 정확히 감지하고 REJECT/FIX 부여
**V2 추가 발견: EP5→EP7 자금 불일치**: EP5 blueprint는 19.3억 전액 WTI 진입 명시, EP7 blueprint는 15억만 WTI 투입으로 기술. 이 cross-blueprint 자금 흐름 불일치는 Stage 3이 누적 자금 상태를 정밀 추적하지 못함을 시사

---

## 5. `_inventory_gaps` Assessment

### 발화 이력

| Episode | TF-49 경고 | 내용 |
|---------|-----------|------|
| EP2 | 1건 | "18년 치 거시경제 지표 노트 (방에 보관 중)" |
| EP3 | 2건 | 노트 + "19억 3천만 원 계좌 통장/휴대폰" |
| EP4 | 3건 | 계좌 + 사무실 열쇠 + 임대차 계약서 |
| EP5 | 4건 | 계좌 + 열쇠 + 파생상품 계좌 + 다중 모니터 PC |
| EP6 | 2건 | 계좌 내역 + 로로피아나 코트 |
| EP7 | 1건 | WTI 매수 체결 확인서 |
| EP8 | 1건 | WTI 체결 확인서 (minor reference) |

### Net Assessment: **Net-Helpful, but off-axis**

**Helping**:
- EP2의 "이미 소유한 가죽 노트 재획득" 경고는 valid signal로 V66.1 continuity validator와 연동
- 아이템 추적은 물리적 소유 상태를 정확히 반영

**Off-axis**:
- 실제 rejection을 유발한 conflict들은 아이템이 아닌 **자본 수치, 시간선, provenance** 영역
- inventory_gaps는 물리적 아이템만 추적하며, capital state / timeline anchor는 coverage 밖
- "계좌에 19억 원" 같은 금융 자산을 inventory_gap으로 추적하는 것은 범주 혼동 (금융 잔고는 아이템이 아님)

**결론**: inventory_gaps는 현재 범위 내에서 올바르게 작동하지만, **dominant conflict family (capital state, timeline)에는 기여하지 못한다**. 유해하지는 않으나 residual seam 해결에 직접 기여도는 낮다.

---

## 6. `PASS_WITH_FIX` vs Post-Select Conflict Assessment

### 구조적 분리

두 시스템은 설계상 **다른 검출 축**을 담당한다:

| 시스템 | 실행 시점 | 검출 대상 | 수정 경로 |
|--------|----------|----------|----------|
| PASS_WITH_FIX | Director 판정 시 | 표현/산술/phrasing 오류 (inplace 수정 가능) | Patch loop (max 3회) |
| Post-select conflict | Director 판정 후 | Cross-episode 상태 모순 (provenance, timeline, history) | Full retry (new generation) |

### EP5 공존 사례 분석

EP5 Round 1에서 동시 발화:
- Director: "3배 레버리지 독백 vs 480계약 실제 레버리지 불일치" → PASS_WITH_FIX
- Post-select: "EP4 법인설립비 5천만 원이 잔고에 미반영" → REJECT override

이 공존은 **정상적인 separation of concerns**이다. Director는 원고 내부 산술 일관성을 보고, post-select는 cross-episode 상태 전이 일관성을 본다. 두 축이 겹치지 않아 공존이 아키텍처적으로 올바르다.

### 잠재 문제점

PASS_WITH_FIX patch loop는 Director-flagged 이슈만 수정한다. Post-select conflict가 동시 존재하면 patch 결과와 무관하게 REJECT로 override된다. 이 경우 patch loop의 작업이 낭비될 수 있다.

**개선 가능 경로** (survey scope 외, 기록만):
- Post-select check를 PASS_WITH_FIX eligibility 판정 이전에 실행하여, post-select conflict 존재 시 patch loop를 건너뛰고 바로 full retry로 진입

---

## 7. Cleared Non-Culprits

### 확실히 downgrade된 이전 의심 원인

1. **Old covert-infrastructure invention seam** — CLEARED
   - 8화 전체에서 burner phone, offshore broker, paper company 등 covert infrastructure invention 증거 0건
   - EP6 rejected version에서 "법인 자금 20억" 언급이 있었으나 이는 기존 인물의 자금이지 신규 infrastructure가 아님
   - Final version에서 제거됨. 재발 징후 없음

2. **Stage 2 density / allocation 문제** — CLEARED
   - Arc 1이 Director score 100으로 1회 통과
   - 5화 단위 arc 구조가 정상 작동
   - 에피소드별 밀도 불균형 증거 없음

3. **Stage 2 ep-count ownership 문제** — CLEARED
   - Arc 1: ep 1-5, 정상 할당
   - Arc 설계 단계에서 episode ownership conflict 없음

4. **Broad semantic-carryover relapse** — PARTIALLY CLEARED
   - EP1 "overconsumption → EP3/4 collapse" 패턴은 완전 해소
   - 그러나 **specific provenance carryover** (신탁 출처)와 **numeric state carryover** (잔고 계산)는 잔류
   - "broad" relapse는 아니지만 "narrow, targeted" carryover drift는 존재

---

## 8. Best Current Interpretation

### Dominant Pattern

잔류 seam은 **two-source mixed seam**이다:

**Source A: Stage 3 Blueprint State Authority (EP2)**
- Blueprint가 이전 에피소드 확정 사실을 올바르게 상속받지 못함
- EP2 blueprint가 "조부 신탁"을 명시한 것은 EP1 확정 원고의 "어머니 신탁"과 모순
- Blueprint 생성 시 이전 에피소드 확정 원고의 핵심 상태 (provenance, capital figures)를 충분히 참조하지 않음
- **Code-level 근거**: Stage 3 blueprint 생성 시 이전 원고는 `semantic_ctx` (2,176자)와 window 기반으로 참조. 핵심 상태 (누구의 신탁인지)가 이 window에 포함되지 않았을 가능성

**Source B: Stage 4 Writer Numeric/Temporal Drift (EP3, EP5, EP6, EP7)**
- Blueprint는 깨끗하나 writer가 원고 확장 시 상태를 drift
- 주요 drift 축: capital accounting (EP5), timeline anchor (EP6), item storage location (EP3), temporal metaphor (EP7)
- **Code-level 근거**: Writer carryover packet의 `prev_ending`은 마지막 2,500자만 전달. 핵심 수치 (잔고, 시간)가 이 window에 빠질 수 있음. `prev_digest`가 존재하지만 요약 과정에서 수치 정확성 손실 가능

### Risk Ranking

1. **Account/provenance state carryover** — TOP RISK
   - EP2 신탁 출처, EP5 잔고 계산이 가장 많은 라운드를 소비 (각 4회, 3회)
   - 금융 장르의 핵심 정합성이므로 1건의 drift가 전체 서사 신뢰도를 위협

2. **Time-anchor carryover** — SECONDARY RISK
   - EP6의 2월→4월 invention이 가장 심각한 단일 drift
   - 그러나 Director가 1차에서 잡아 firewall까지 발동, 체계적 대응 확인

3. **Item/location carryover** — TERTIARY RISK
   - EP3 가죽 노트 보관 위치가 유일 사례
   - 기존 continuity validator + inventory_gaps가 이미 coverage

4. **Cross-surface contract drift** — LATENT RISK
   - Blueprint authority error (Source A)와 writer drift (Source B)가 같은 에피소드에서 동시 발생하면 rescue 난이도 급증
   - EP2가 이 패턴의 약한 사례 (blueprint error → writer 충실 추종 → post-select 4회)
   - EP3은 blueprint warning + writer drift 동시 존재했으나 각각 다른 축

---

## 9. Recommended Next Step

### Immediate: Survey 유지 (execution SSOT 미생성)

**이유**:
- Dominant seam이 단일 root cause가 아닌 two-source mixed seam
- Source A (blueprint authority)와 Source B (writer drift)는 수정 경로가 다름
- Source A 수정: Stage 3 blueprint 생성 시 이전 확정 원고의 핵심 상태 (provenance, capital, timeline) 명시적 주입 강화
- Source B 수정: Writer carryover packet에 numeric state snapshot 또는 확정 사실 summary 추가
- 두 수정 모두 별도 설계가 필요하며, 현재 evidence만으로 95% 확신도의 단일 execution SSOT를 작성할 수 없음

### 권장 후속 조치 (우선순위)

1. **[SURVEY-EXTEND]** EP2 blueprint 생성 시 실제로 주입된 이전 에피소드 컨텍스트를 artifact 수준에서 추적하여, "조부 신탁"이 blueprint에 들어간 정확한 경로 특정
2. **[SURVEY-EXTEND]** EP5 writer에게 전달된 carryover packet 내용을 artifact에서 추출하여, 법인설립비 5천만 원 정보가 packet에 포함되었는지 여부 확인
3. **[DESIGN]** 위 두 조사 완료 후, Source A/B 각각에 대한 bounded patch 설계 → 개별 execution SSOT 또는 단일 통합 SSOT 작성 판단

---

## 10. Confidence and Limits

### Confidence: 88%

**높은 확신 영역**:
- Run outcome snapshot: 95%+ (production JSONL + console + artifact 삼중 대조)
- Episode-by-episode conflict attribution: 90%+ (rejected vs final manuscript 직접 비교)
- Post-select conflict detection 정상 작동 판정: 95%+
- Cleared non-culprits: 90%+

**제한 영역**:
- EP2 blueprint에 "조부 신탁"이 들어간 정확한 code path: 미확인 (Stage 3 orchestrator의 이전 에피소드 참조 메커니즘 artifact-level 추적 필요)
- EP5 writer carryover packet 내 법인설립비 포함 여부: 미확인 (packet artifact 미존재)
- 8화 이후 extended run에서의 seam 누적 효과: 미확인

### 95% 미달 사유

Two-source mixed seam의 각 source에 대한 정확한 code-level injection point를 artifact 수준에서 확인하지 못했다. Blueprint authority error (Source A)가 Stage 3의 어떤 컨텍스트 윈도우 한계에서 비롯되는지, writer drift (Source B)가 carryover packet의 어떤 truncation에서 비롯되는지를 **추정**은 가능하나 **증명**은 미완료.

---

## Mandatory Final Lines

- **Dominant seam**: mixed seam (Stage 3 blueprint authority error + Stage 4 writer numeric/temporal drift)
- **Are the repeated post-select rejects mostly valid**: yes
- **Should Codex open an execution SSOT immediately**: no
