# 0_1 Stage 4 EP1-6 Fix Execution SSOT

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: docs/2026-03-30/0_1-stage4-ep1-6-fix-execution-ssot.md
Temp Mirror Path: (없음 — 이번 턴 docs/temp 수정 금지)
Source Survey: docs/2026-03-30/0_1-stage4-ep1-6-live-run-bounded-survey.md

## Scope

EP1-6 bounded survey에서 도출된 P1 actionable issue 1건의 manual repair 지침.
코드 수정/Stage 4 실행 제어를 포함하지 않음.
대상은 `project_data.db`의 authoritative manuscript payload와 `drafts/ep_*.txt` export sync이다.

Authority contract:
- manuscript truth는 DB `manuscripts` 테이블이 우선
- `drafts/ep_0005.txt`, `drafts/ep_0006.txt`는 export mirror로 취급
- 따라서 txt-only 수술 금지

## Items

### ITEM-01: EP5→EP6 주문 금액 서사 모순 (P1)

**문제 요약**:
- EP5 씬4 (L174): 한시우가 김 팀장에게 "증거금 19억 7,100만 원 **전액**, 최대 레버리지로 **전량 매수**" 지시
- EP5 씬4 (L186): 김 팀장이 "증거금 **전액 최대 레버리지**" 확인 반복
- EP6 씬2 (L44): 박성호 PB에게 "19억 7,100만 원 중 **15억 원**, 3배 레버리지" 지시
- EP6 씬2 (L50): "나머지 **4억 7,100만 원**은 마진콜 방어용 대기"

**모순 구조**:
EP5에서 "전액/전량" 2회 명시 → EP6에서 "15억/4.71억 분할" 변경. 서사적 bridging 없음.

**수정 옵션 (택 1)**:

**Option A: EP5 완화 (최소 침습)**
- EP5 L174: "전액" → "가용 증거금 대부분" 또는 "증거금의 상당 부분"으로 교체
- EP5 L186: "전액 최대 레버리지" → "최대 레버리지"로 축약 (전액 반복 제거)
- 장점: EP6 무수정, 변경 범위 최소
- 단점: EP5 씬4의 극적 긴장감("전액 올인") 약화

**Option B: EP6 bridging 삽입 (서사 보강)**
- EP6 씬1 또는 씬2 초반에 한시우의 내심 독백 1-2문장 삽입
- 예시: "김 팀장에게는 전액 진입을 명했지만, 본사 데스크로 넘어가는 사이 냉정이 돌아왔다. 마진콜 한 번에 전멸하는 구조는 18년 치 기억이 보여준 수많은 실패자들의 전형이었다. 증거금의 4분의 1은 방패로 남겨야 한다."
- 장점: 전략 수정 과정이 캐릭터 성장/냉정함의 증거가 됨, EP5 긴장감 유지
- 단점: EP6에 2-3문장 추가 필요

**추천**: **Option B** — 서사 가치가 더 높고, EP5의 "전액 올인" 긴장감을 유지하면서 EP6에서 "냉정한 전략가"로서의 캐릭터 깊이를 추가할 수 있음.

**삽입 위치**: EP6 L34 (씬2 시작부) 직후, 박성호 PB 소개 후 한시우의 주문 지시(L44) 전 사이.

**실행 시점**: live run 완료 후 편집 단계 또는 운영자 판단에 따라 즉시.

**수정 순서**:
1. `project_data.db`의 manuscript row authoritative repair
2. `drafts/ep_0005.txt`, `drafts/ep_0006.txt` export sync
3. DB read-back과 txt read-back 정합 검증

## Watchlist (P2, 편집 단계 처리)

| ID | 내용 | 위치 | 추천 |
|---|---|---|---|
| W-01 | "심해 지진" 비유 중복 | ep5 L192 / ep6 L11 | 편집 시 ep6 측 비유 변형 |
| W-02 | "18년 치" vs "20년간" | ep1 / ep2 | 이후 ep에서 통일 모니터 |
| W-03 | EP6 씬4 종결부 밀도 | ep6 L128-136 | 편집 시 주인공 반응 1문장 추가 검토 |

## Execution Constraints

- 코드 수정 금지
- DB authoritative repair만 허용
- Stage 4 재실행 금지 (manual repair only)
- 수정 시 UTF-8 인코딩 유지
- 수정 후 자금 산술 재검증 필수 (19.71억 = 15억 + 4.71억 불변)
- txt-only repair 금지
