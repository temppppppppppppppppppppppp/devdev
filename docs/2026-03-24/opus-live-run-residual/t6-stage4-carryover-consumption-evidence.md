# Terminal 6 Evidence Ledger: Blueprint↔Manuscript Cross-Verification

Date: 2026-03-24
Terminal: 6
Status: lane evidence (raw artifact excerpts)
Supports: `t6-stage4-carryover-consumption.md`

---

## §A. EP3 — Blueprint "서랍" vs EP2 확정 "금고"

### A-1. EP3 Blueprint Scene 2 원문

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`

Scene 2 "온실을 나서는 짐싸기":
- Plot: "방으로 돌아와 **18년 치 거시경제 지표 노트를 서랍 깊숙이 보관**. 과거와 결별."
- Tension: 4
- Location: 한시우의 방

### A-2. EP2 Final Manuscript 관련 부분

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_04/final_manuscript__A.txt`

- Room items listed: "두꺼운 가죽 노트 (18년치 경제 로드맵), **소형 금고**, 수천만 원짜리 명품 시계들"
- EP2 rejected version (attempt_01): "소형 금고에 몇 개의 수천만 원짜리 명품 시계들" — 금고는 시계 보관용으로 사용
- 노트는 별도 아이템으로 기재. "금고에 보관"이 명시되진 않으나 post-select validator가 "금고 vs 서랍" conflict를 감지

### A-3. Post-Select Rejection Evidence

Source: `docs/2026-03-24/console.txt` L1110-1117

- "[A-3] post-select conflict: 가죽 노트의 보관 위치(금고 vs 서랍)"
- "[A-3] post-select conflict: 서재 독대 시간(오후 4시 35분) 이후 증권사 방문 시간(오후 3시 35분)이 과거로 역행하는 치명적 타임라인 오류"

### A-4. EP3 Blueprint Temporal Constraint

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`

- Scene 4 "신탁 해지": "오후 4시 은행 마감 전 처리 요구"
- Time flow: "늦은 오후 (2006년 1월의 늦은 오후, **은행 마감 직후**)"
- EP2 서재 독대 종료: 4:35pm (EP2 final manuscript 확정)
- 모순: 4:35pm 이후 출발 → 오후 4시 전 은행 도착 = 시간적으로 불가능

### A-5. Fix Evidence

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt`

- "그리고 **다음 날 오후**" 삽입 — same-day 방문을 next-day로 변경하여 timeline 해소
- "금고" 보관 유지 — blueprint의 "서랍" 지시를 무시하고 EP2 확정 사실에 맞춤

**결론**: Writer의 Round 2 수정이 blueprint 지시(서랍)를 EP2 확정 사실(금고)로 override한 것은, writer가 blueprint보다 이전 확정 원고를 우선한 사례. 이는 blueprint가 잘못되었음을 반증.

---

## §B. EP7 — Blueprint Ending Hook "18년 전"

### B-1. EP7 Blueprint Ending Hook 원문

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`

Ending hook 전문:
> "손끝에 닿은 빳빳한 매수 체결 확인서. **18년 전** 나를 짓눌렀던 파산의 환상통이 미세하게 손목을 훑고 지나갔다."

### B-2. EP7 Selected Manuscript (Before Fix)

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__B.txt`

- Blueprint ending hook의 "18년 전" 표현이 원고에 충실히 재현됨
- 원고 마지막 문단에 "18년 전" 또는 동일 시간 표현 포함

### B-3. PASS_WITH_FIX Verdict

Source: `docs/2026-03-24/console.txt` L2185-2203, `projects/0324_00_/logs/episode_production.jsonl` line 26

- Director PASS_WITH_FIX (score=94)
- Fix instruction: "'18년 전'을 '전생에' 또는 '미래에'로 수정"
- 시간 산술: 2006년 기준 18년 전 = 1988년. 주인공 파산은 2024년(미래/전생). 완전한 시간축 반전.

### B-4. Patched Manuscript

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt`

- "18년 전" → "전생에" 수정 완료
- unchanged_ratio=0.9995 (극소 변경)
- 재심사 PASS (score=90)

### B-5. Blueprint Prevalidation Status

- prevalidation_issues: 0
- quality_risk: false

**결론**: Prevalidation은 ending hook 내의 시간 표현 정확성을 검증하지 않음. "18년 전"이라는 명백한 시간축 오류가 prevalidation을 통과하여 blueprint에 남았고, writer가 이를 충실히 재현.

---

## §C. EP6 — Blueprint Equipment "19.3억 예치" (Stale State)

### C-1. EP6 Blueprint Equipment 원문

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`

Protagonist state equipment:
> "**19억 3천만 원이 예치된 계좌 내역**, 로로피아나 캐시미어 코트"

### C-2. EP5 Blueprint — 전액 투입 확정

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`

- Scene 2: "계좌 잔고 **1,930,000,000원** 확인. 전액 달러 환전: 환율 970원 적용 → **약 198만 달러**. 파생상품 계좌에 예치."
- Scene 5: "약 198만 달러 WTI 롱 포지션 진입 완료"
- Equipment: "**약 198만 달러가 예치된 파생상품 계좌**, 다중 모니터가 세팅된 PC"

EP5에서 19.3억은 전액 달러 환전 → 파생상품 계좌 → WTI 롱 포지션으로 전환 완료. "예치된 계좌"가 아닌 "WTI 증거금으로 묶인 자금".

### C-3. EP6 Rejected Manuscript — Writer의 자금 해석

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt`

- "확보해 둔 **20억 원의 법인 자금**을 3배 레버리지" — blueprint의 "19.3억 예치" → writer가 "가용 현금 20억"으로 round-up
- "**법인 인감, 해외 선물 법인 계좌 OTP, 법인 통장 20억 원**" — blueprint에 없는 아이템을 발명
- 날짜: "[2006년 **4월 18일** 밤 11시]" — blueprint "2월 하순"을 무시

### C-4. EP6 Final Manuscript — 자본 모순 해결

Source: `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`

- "2006년 **2월 하순**의 심야" — 날짜 정규화
- "지금 내 전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다" — 자금 상태 정확히 인식
- "내 수중에 현금 15억이 있다고? 웃기는 소리." — 허세/미끼로 자본 모순 해결

### C-5. Continuity Firewall Evidence

Source: `projects/0324_00_/logs/episode_production.jsonl` line 23

- Round 2: firewall_triggered=true, error_category=LOGIC_ERROR, score=69→44
- "자본금 모순: EP 5에서 19억 원을 전액 WTI 선물에 투입했으므로, 가용 현금 20억 원은 없다"

### C-6. Cross-Blueprint 자금 흐름 불일치

| Episode | Blueprint 자금 기술 | 실제 상태 |
|---------|-------------------|----------|
| EP5 | "계좌 잔고 1,930,000,000원" → 전액 WTI 투입 | 현금 0, WTI 포지션 ~198만 달러 |
| EP6 | Equipment "19억 3천만 원이 **예치된** 계좌 내역" | 현금 아님, WTI 증거금으로 묶임 |
| EP7 | "15억 원 3배 레버리지" 추가 투입 | 19.3억 중 15억만? 나머지 4.3억의 소재 불명 |

**결론**: Blueprint equipment이 EP5의 전액 투입 사실을 반영하지 못하고 "예치"로 기재. Writer가 이를 가용 현금으로 해석한 것은 blueprint의 stale state가 enabling factor. 날짜 변경(2월→4월)과 금액 round-up(19.3→20억)은 writer invention.

---

## §D. 코드 메커니즘 교차 확인

### D-1. Blueprint Schema 금융 필드 부재

Source: `modules/core/response_schemas.py` L579-591

`BLUEPRINT_PROTAGONIST_STATE_SCHEMA`:
- `mood` (string)
- `injuries` (string)
- `equipment` (string or array of strings)

**구조화된 금융/자본/provenance 필드 없음**. 금융 수치는 equipment string에 비구조화 포함.

### D-2. Inventory Gaps 메커니즘

Source: `modules/core/stage3_orchestrator.py` L2383-2447

- `_detect_inventory_gaps()`: blueprint 참조 아이템 vs 현재 소유 아이템 gap 검출
- 물리적 아이템만 추적. 금융 잔고의 정확성은 검증하지 않음.
- "계좌 내역"이 inventory_gap에 포함될 수 있으나, **금액이 정확한지는 확인 안 됨**.

### D-3. Writer Carryover 4-Channel 구조

Source: `modules/domain/agents/chief_writer_context_packets.py`

| Channel | Source | 금융 상태 coverage |
|---------|--------|-------------------|
| prev_ending (2,500자) | 이전 원고 마지막 2,500자 | 마지막 부분에 금융 수치가 있을 때만 |
| prev_digest (regex) | 이전 원고 전체 regex 스캔 | "잔고/자본/현금/자산/예수금" 패턴 매칭 → "확정 자본: X억Y만원" |
| carryover_ceiling | 이전 원고 keyword 매칭 | WTI/원유/시드머니/수익 등 금융 키워드 문장 추출 |
| IFC (Immutable Fact Contract) | fact_ledger + world_state | 금융 키워드 ("억", "만원", "달러") → 불변 사실 |

**문제**: Blueprint authority가 carryover authority보다 높으므로, blueprint의 stale 수치가 carryover의 정확한 수치를 override할 수 있음.

### D-4. Post-Select / PASS_WITH_FIX 실행 순서

Source: `modules/core/stage4_interview_round.py` L3635-3799, L4000-4049

1. Director verdict (PASS / PASS_WITH_FIX / REJECT)
2. **Post-select checks (최우선)** — conflict 발견 시 verdict → REJECT, fix_scope → "full"
3. PASS_WITH_FIX loop — post-select 통과 후에만 실행

두 시스템은 동시 공존 불가. Post-select가 항상 우선.

### D-5. Continuity Firewall 발동 조건

Source: `modules/domain/agents/director_ensemble.py` L1023-1089

- Trigger: `critical_count >= 1 OR major_count >= 2`
- Hard reject mode: score cap = **44**
- Fixable mode (PASS_WITH_FIX): score cap = 97, requires all contradictions fixable + score >= 80

EP6 R2: critical_count=1 (자본금정합) → hard reject → score 44.

---

## §E. EP5→EP7 Cross-Blueprint 자금 추적 불일치 (V2 발견 보강)

| EP | Blueprint 자금 기술 | 실제 누적 상태 | Gap |
|----|-------------------|-------------|-----|
| EP3 | "수수료 3.5% 공제 후 19억 3천만 원" | 19.3억 현금 | 정확 |
| EP4 | 법인 설립 (5천만 원 지출) | 19.3억 - 0.5억 = 18.8억 | **EP5가 19.3억으로 기재** |
| EP5 | "계좌 잔고 1,930,000,000원" + 전액 WTI | 현금 0, WTI ~198만 달러 | 법인설립비 0.5억 미공제 |
| EP6 | Equipment "19.3억 예치" | 현금 0 (WTI 묶임) | **"예치" ≠ 실제** |
| EP7 | "15억 원 3배 레버리지" | 15억 추가 투입 | 19.3억 vs 15억 gap 미설명 |

Stage 3 blueprint는 에피소드 간 누적 자금 상태를 정밀 추적하지 못함. Equipment string이 금융 상태의 유일한 전달 경로이며, 정확성 검증 없음.
