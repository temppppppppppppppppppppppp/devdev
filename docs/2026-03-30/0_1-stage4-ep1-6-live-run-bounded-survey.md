# 0_1 Stage 4 Live Run Bounded Survey: EP 1-6

Date: 2026-03-30
Status: draft-live-run-pending
Scope: ep_0001 ~ ep_0006 완료분 only (ep7+ 제외)
Project: 0_1 (투자물 골든 카나리아 테스트)
Authority: bounded slice audit — 전체 live run은 진행 중이므로 전역 closure 아님

## 1. Coverage Summary

| Evidence Source | Scope | Covered | ep7+ Excluded |
|---|---|---|---|
| Manuscript txt (drafts/) | ep1-6 | 6/6 전량 읽기 완료 | ep7+ 파일 없음 (drafts에 ep1-6만 존재) |
| Blueprint txt (plans/blueprints/) | bp 1-6 | 6/6 전량 읽기 완료 | bp 7+ 읽었으나 결론 미반영 |
| Stage 4 artifacts (logs/artifacts/stage4/) | ep1-6 dirs | 6/6 전량 탐색 완료 | ep7+ dirs 미참조 |
| episode_production.jsonl | ep1-6 entries | 6건 추출 완료 | ep7+ entries 제외 |
| pass_rate_monitor.json | ep1-6 | 6건 추출 완료 | ep7+ 제외 |
| quality_metrics.jsonl | ep1-6 | 12건 (Stage3+Stage4) 추출 | ep7+ 제외 |
| runtime_audit.jsonl | ep1-6 | 관련 entries 추출 | ep7+ 제외 |
| decisions.jsonl | ep1-6 | Stage2/3/4 decisions 전량 | ep7+ 제외 |
| ui_events.jsonl | ep1-6 | Stage0/2/3/4 events 전량 | ep7+ 제외 |

## 2. Three-Layer Audit Results

### Layer 1: Artifact Truth (파일 실물 검증)

| EP | File | Lines | Chars | Scenes | Valid Prose | Encoding | Placeholder/Meta |
|---|---|---|---|---|---|---|---|
| 1 | ep_0001.txt | 167 | ~5,000 | 4 | Yes | UTF-8 clean | None |
| 2 | ep_0002.txt | 125 | ~5,200 | 4 | Yes | UTF-8 clean | None |
| 3 | ep_0003.txt | 188 | ~5,100 | 4 | Yes | UTF-8 clean | None |
| 4 | ep_0004.txt | 172 | ~4,400 | 4 | Yes | UTF-8 clean | None |
| 5 | ep_0005.txt | 202 | ~7,100 | 4 | Yes | UTF-8 clean | None |
| 6 | ep_0006.txt | 136 | ~5,600 | 4 | Yes | UTF-8 clean | None |

Artifact 파일 상태: **6/6 전량 정상**. placeholder, meta-commentary, format corruption, mojibake, empty section 없음.

Stage 4 artifact directory 구조:

| EP | Attempts | Files | Flow Type |
|---|---|---|---|
| 1 | 1 | final_manuscript__C + selected_candidate__C (동일) | Clean pass |
| 2 | 1 | patched_after_fix__A_InPlace + selected_before_fix__C | In-place patch |
| 3 | 2 | att1: rejected_best__C_narrative + selected__C / att2: final__B + selected__B | Reject + retry |
| 4 | 1 | final_manuscript__B + selected_candidate__B (동일) | Clean pass |
| 5 | 2 | att1: rejected_best__B_narrative + selected__B / att2: final__A + selected__A | Reject + retry |
| 6 | 1 | patched_after_fix__A_InPlace + selected_before_fix__A | In-place patch |

### Layer 2: Metadata Truth (로그-실물 정합성)

#### Stage 4 Production Summary

| EP | Attempts | Rd0 Verdict | Rd0 Score | Final Verdict | Final Score | Gate | Candidate |
|---|---|---|---|---|---|---|---|
| 1 | 1 | PASS | 95 | PASS | 95 | director_primary_pass | C |
| 2 | 1 | PASS_WITH_FIX | 92 | PASS | 90 | patch_reaudit_pass | A (patched from C) |
| 3 | 2 | REJECT (post_select_conflict) | 100 | PASS | 96 | director_primary_pass | B |
| 4 | 1 | PASS | 98 | PASS | 98 | director_primary_pass | B |
| 5 | 2 | REJECT (post_select_conflict) | 96 | PASS | 96 | director_primary_pass | A |
| 6 | 1 | PASS_WITH_FIX | 95 | PASS | 90 | patch_reaudit_pass | A (patched) |

#### Quality Metrics (Final Stage 4)

| EP | Score | AI Slop | CED | Complexity |
|---|---|---|---|---|
| 1 | 95 | 2.0 | 0.0 | 55.94 |
| 2 | 90 | 2.0 | 0.0 | 71.65 |
| 3 | 96 | 1.0 | 0.0 | 50.50 |
| 4 | 98 | 1.0 | 0.0 | 61.83 |
| 5 | 96 | 2.0 | 0.0 | 72.56 |
| 6 | 90 | 3.0 | 0.0 | 65.44 |

CED (Cliche/Error Density) 전원 0.0 — clean.

#### Conflict Detection 이력

**EP 3 (REJECT → retry)**:
- Director score 100이었으나 post_select_conflict gate가 차단
- 원인: EP 2에서 확립된 "신탁 30억 원 해지"와 EP 3 초안의 "150억 원" 수치 충돌
- 해결: attempt 2에서 30억 원 기준으로 재작성, candidate B (score 96) 통과

**EP 5 (REJECT → retry)**:
- Director score 96이었으나 post_select_conflict gate가 차단
- 원인: EP 4에서 잔액 정확히 20억 원으로 확정했으나, EP 5 초안이 블룸버그 비용 차감 없이 증권사 예치금도 20억 원으로 기술
- 추가: candidate B에서 "한성 VVIP 신용카드" 사용 — 한성그룹과 법적 단절 후 불가능
- 해결: attempt 2 candidate A에서 잔액 19억 7,100만 원으로 정확히 계산, VVIP 카드 언급 제거

**로그-실물 정합성 판정**: 모든 PASS/REJECT/PATCH 이력이 artifact 파일 구조와 정확히 일치. patch 적용 이력이 실물에 반영됨 확인.

### Layer 3: Narrative Truth (서사 내용 검증)

#### 자금 추적 (Capital Trail)

| 시점 | 금액 | Source |
|---|---|---|
| 신탁 원금 | 30억 원 | ep1 설정, ep2-3 반복 확인 |
| 위약금 15% | -4.5억 원 | ep3 정밀 계산 |
| 세금 + 스폰서십/연금 정산 후 실수령 | 20억 4천만 원 | ep3 L확인증 |
| 오피스텔 보증금+월세 | -3,200만 원 | ep4 |
| 법인 인수 프리미엄 | -500만 원 | ep4 |
| 노트북 구매 | -300만 원 | ep4 |
| 법인 통장 이체 잔액 | 20억 원 | ep4 씬4 확인 |
| 블룸버그 연간+설치 프리미엄 | -2,900만 원 | ep5 |
| 증권사 예치 증거금 | 19억 7,100만 원 | ep5 |
| WTI 매수 투입 | 15억 원 (×3 레버리지 = 45억 포지션) | ep6 |
| 마진콜 방어 대기 | 4억 7,100만 원 | ep6 |

산술 정합성: **전 구간 정확**. 19.71억 = 15억 + 4.71억 ✓

#### 타임라인 정합성

| EP | 작중 시점 | 일관성 |
|---|---|---|
| 1 | 2024년 12월 (회귀 전) → 2006년 1월 (회귀 후) | 기준점 설정 ✓ |
| 2 | 2006년 1월, 같은 날 오전~정오 | ep1 서재 호출 직결 ✓ |
| 3 | 같은 날 정오~오후 1:50 | ep2 클리프행어 직결 ✓ |
| 4 | 같은 날 오후 2:40 → 다음 날 오후 | 자연스러운 진행 ✓ |
| 5 | ep4 다음 날 계속 ~ 블룸버그 설치 | ep4 마지막 전화 직결 ✓ |
| 6 | ep5 직후 (IAEA 속보 동시) | ep5 마지막 씬 직결 ✓ |

#### 캐릭터/Identity 정합성

| 캐릭터 | 첫 등장 | 일관성 |
|---|---|---|
| 한시우 (주인공) | ep1 | 6화 전체 일관 ✓ |
| 한정호 (회장/아버지) | ep1 | ep1-3 일관 ✓ |
| 한태준 (큰형) | ep1 | ep1-2 일관 ✓ |
| 한태민 (둘째형) | ep1 | ep1-2 언급 일관 ✓ |
| 김 집사 | ep2 (ep1은 "집사") | 동일인, 무모순 ✓ |
| 법무팀장 | ep2 | ep2-3 일관 ✓ |
| 김 팀장 (증권사) | ep5 | ep5-6 일관 ✓ |
| 박성호 PB | ep6 | 신규 등장, 무모순 ✓ |

Name drift, identity confusion 없음.

#### Blueprint 핵심 Beat 반영도

| EP | Blueprint 핵심 Beats | Manuscript 반영 |
|---|---|---|
| 1 | 회귀/데이터 각인/가족 무시/서재 호출 | 4/4 ✓ |
| 2 | 독립 선언/직위 거부/형 조우/서명 직전 조건 | 4/4 ✓ |
| 3 | 선입금 조건/위약금 계산/이체 완료/뇌 과부하 | 4/4 ✓ |
| 4 | 탈출 회복/오피스텔 확보/법인 인수/블룸버그 전화 | 4/4 ✓ |
| 5 | 블룸버그 설치/증권 계좌/IAEA 속보/매수 지시 | 4/4 ✓ |
| 6 | 호가창 진공/PB 전환/15억 매수/급등 클리프행어 | 4/4 ✓ |

**모든 에피소드에서 blueprint 핵심 beat 전량 반영 확인.**

(참고: Stage 4 production log의 "blueprint coverage" 지표는 EP4에서 0%를 기록했으나, 이는 메타데이터 매칭 로직의 한계이며 실물 본문에는 4개 beat 모두 반영되어 있음. 시스템 트랙 메트릭 보정 후보.)

## 3. Findings (Severity Order)

### P1 — Fix-Recommended (1건)

**P1-01: EP5→EP6 주문 금액 서사 모순**
- File: `ep_0005.txt` L174, L186 vs `ep_0006.txt` L44, L50
- EP5 씬4: 한시우가 김 팀장에게 **"증거금 19억 7,100만 원 전액, 최대 레버리지로 전량 매수"** 명시적 지시
- EP5 L186: 김 팀장이 **"증거금 전액 최대 레버리지"** 확인 반복
- EP6 씬2: 박성호 PB에게 **"19억 7,100만 원 중 15억 원, 3배 레버리지"** 지시 (나머지 4.71억은 마진콜 방어)
- 서사적으로 김 팀장→박성호 PB 전환 과정에서 전략을 수정한 것으로 해석 가능하나, **EP5 본문에 "전액"/"전량"이 2회 명시**되어 있어 EP6에서 15억으로 변경되는 것이 독자에게 모순으로 읽힐 수 있음
- Blueprint 0006에서도 이 차이를 인지하고 있었으나 ("differs from the Ep5 setup"), manuscript에 bridging 서술이 없음
- **영향**: 세심한 독자가 "전액이라 했는데 왜 15억?"이라고 혼란할 수 있음. 서사 신뢰도 훼손
- **추천 조치**: `manual repair` — EP5 L174의 "전액" 표현을 "가용 증거금 대부분" 등으로 완화하거나, EP6 초반에 전략 수정 내심 독백 1-2문장 삽입

### P2 — Watchlist (3건)

**P2-01: EP5/EP6 경계 비유 중복**
- File: `ep_0005.txt` L192 vs `ep_0006.txt` L11
- "빛이 닿지 않는 심해에서 거대한 지진이 발생하기 직전..." 거의 동일 문장이 에피소드 경계에서 반복
- 추가로 "객장 정적" 문구도 ep5 L178 / ep6 L7에서 반복
- **영향**: 에피소드 전환 시 리캡 의도로 보이나, 독자가 연속 독서 시 반복감
- **추천**: watchlist — 추후 편집 시 변형 권장

**P2-02: EP1 "18년 치" vs EP2 "20년간" 수치 표현 차이**
- ep1: "18년 치의 미래 경제 데이터" (기억된 데이터 범위: 2006→2024)
- ep2: "앞으로 20년간" (대략적 포부/계획 기간)
- **영향**: 맥락이 다르므로 심각한 모순은 아니나, 향후 에피소드에서 혼용 시 혼란 가능
- **추천**: watchlist — 이후 에피소드에서 "18년" 기준으로 통일 여부 모니터

**P2-03: EP6 씬4 종결부 밀도**
- ep6이 L136에서 "방금..." 박성호의 목소리가 잘게 떨렸다." 로 종료
- 다른 에피소드 대비 에피소드 마무리 beat가 짧음 (다른 ep는 주인공의 내심 독백이나 상황 서술로 완결감 부여)
- Blueprint와 비교: blueprint의 클리프행어 지시("Park's voice comes through, trembling: 'Sir, just now--'")와 일치하므로 의도된 설계
- **영향**: truncation 아님, 의도적 클리프행어이나 완결감이 약함
- **추천**: watchlist — 편집 시 주인공 반응 1문장 추가 검토

### P0 — Blocked: 없음

## 4. Episode Verdict Table

| EP | Verdict | 근거 |
|---|---|---|
| 1 | **clean** | 산문 품질 양호, 수치 정합, beat 전량 반영, 모순 없음 |
| 2 | **clean** | ep1 직결 자연스러움, 인물 일관, 클리프행어 유효 |
| 3 | **clean** | 자금 계산 정밀, 뇌 과부하 패턴 일관, ep2 클리프행어 정확 해소 |
| 4 | **clean** | 운영 세팅 씬 깔끔, 자금 차감 산술 정확, 시대 고증 양호 |
| 5 | **watchlist** | P1-01 (전액 지시)의 시작점, P2-01 (비유 중복)의 시작점 |
| 6 | **watchlist** | P1-01 (15억 변경)의 착지점, P2-01 (비유 중복), P2-03 (종결부 밀도) |

## 5. Log-Manuscript Contract Drift Assessment

| 항목 | 판정 |
|---|---|
| PASS/REJECT 이력과 최종 원고 정합 | **Aligned** — 모든 verdict 이력이 artifact 파일 구조와 일치 |
| patch/fix가 본문에 반영됐는가 | **Yes** — ep2, ep6의 patched_after_fix 파일이 최종 drafts/와 내용 일치 |
| post_select_conflict 차단이 정당했는가 | **Yes** — ep3 (150억→30억 수치 충돌), ep5 (VVIP 카드 + 잔액 불일치) 모두 실제 서사 결함 |
| quality_metrics와 실물 품질 괴리 | **Minor** — blueprint coverage 지표가 ep4에서 0%이나 실물은 beat 전량 반영. 시스템 메트릭 보정 후보 |
| episode_production cost/duration 이상 | **None** — 정상 범위 |

## 6. Stage 5 / 후속 Lane 위험도

| 위험 요소 | 평가 |
|---|---|
| 인코딩/형식 파손으로 Stage 5 진입 실패 | **없음** — 6/6 UTF-8 clean |
| placeholder/미완성 구간 | **없음** |
| 자금 산술 오류 전파 | **없음** — 전 구간 정확 |
| identity/name 혼동 전파 | **없음** |
| P1-01 (전액→15억 모순) 후속 영향 | **낮음** — ep7+에서 포지션 15억 기준으로 이야기가 진행되면 ep5의 "전액"은 사후 수정으로 해결 가능 |
| timeline drift 전파 | **없음** — 2006년 1~2월 범위 내 일관 |

## 7. Recommended Next Move

### **CONTINUE WITH WATCHLIST**

근거:
1. P0 (blocked) 이슈 없음
2. P1 1건은 manual repair로 충분 (ep5 L174 "전액" 표현 완화 또는 ep6 초반 전략 수정 독백 삽입)
3. P1이 후속 에피소드 진행을 차단하지 않음 — ep7+는 15억 포지션 기준으로 진행하면 됨
4. P2 3건은 편집 단계에서 처리 가능한 수준
5. 6/6 에피소드의 실물 산문 품질, 서사 일관성, 자금 정합성 모두 양호

Watchlist:
- [ ] P1-01: EP5 L174 "전액" → 완화 표현 교체 또는 EP6 전략 수정 bridging 삽입
- [ ] P2-01: EP5/EP6 경계 비유 중복 — 편집 시 변형
- [ ] P2-02: "18년 치" vs "20년간" — 이후 에피소드에서 통일 모니터
- [ ] P2-03: EP6 씬4 종결부 — 편집 시 완결감 보강 검토

## 8. Generated Documents

| Document | Path |
|---|---|
| Bounded Survey (this file) | `docs/2026-03-30/0_1-stage4-ep1-6-live-run-bounded-survey.md` |
| Execution SSOT | `docs/2026-03-30/0_1-stage4-ep1-6-fix-execution-ssot.md` |

## Appendix A: Conflict Detection System Effectiveness

Stage 4의 post_select_conflict gate가 ep3과 ep5에서 Director 고득점(100, 96)을 override하고 재작성을 강제한 것은 **정당하고 효과적**이었다:

- EP3: 150억→30억 수치 충돌을 Director가 놓침 → gate가 차단 → 재작성 후 정확한 30억 기준 원고 생성
- EP5: 블룸버그 비용 미차감 + VVIP 카드 설정 위반을 Director가 놓침 → gate가 차단 → 재작성 후 19.71억 정확 계산 원고 생성

이 gate가 없었다면 ep3과 ep5에 심각한 수치/설정 오류가 남았을 것이다.

그러나 **P1-01 (전액→15억 모순)은 이 gate도 잡지 못했다**. 이는 에피소드 간 cross-reference에서 "의미론적 약속" (전액이라 했으므로 다음 화에서도 전액이어야) 수준의 검증이 현재 시스템에 없기 때문이다. 시스템 트랙에서 "cross-episode semantic commitment" 검증 추가를 검토할 수 있으나, 이번 조사의 scope 밖이다.

## Appendix B: System Metric Note

Stage 4 production log의 "blueprint coverage" 지표:
- EP1: 50%, EP2: 75%, EP3: 50%, EP4: 0%, EP5: 50%, EP6: 75%

실물 본문 대비 blueprint beat 반영은 6/6 전량 4/4 (100%)이므로, 이 지표는 **토큰 매칭 로직의 한계**로 실제 coverage를 과소 보고하고 있다. 시스템 트랙에서 blueprint coverage 산정 로직 보정을 검토할 수 있으나, 이번 조사의 scope 밖이다.
