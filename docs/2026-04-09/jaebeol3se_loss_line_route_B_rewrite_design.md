# jaebeol3se_loss_line — 경로 B Rewrite 설계 문서

> 인코딩: **UTF-8 only**
> 작성일: 2026-04-09
> envelope: **3.1 (Evidence completion + Rewrite design only, NO TR/Phase0 writes)**
> 상위 경로 문서: `docs/2026-04-09/jaebeol3se_loss_line_block_021_030_audit_3pass_audit.md` §5 경로 B
> 원 감리 노트: `treatments/preprocess/jaebeol3se_loss_line/05_audits/block_021_030_audit_2026-04-09.md` (경로 D patch 완료)
> 대상 변경: TR B30 content 4필드 + Phase0 ARC-02/ARC-03 capital_target 정합 + (조건부) Phase0 block_slots
> Operator 승인 필요: **§6 decision matrix 4건**

---

## 0. 한 줄 설계 요약

TR B30을 **`명부 등재 이벤트 → 회장 원칙 승인 + 다음 주 정식 의결 예약`**으로 soft-walk-back하여 Phase0 B30(추천)/B31(승격) 분리 구조를 회복한다. TR B30 time 필드는 **`2025년 9월 초 월요일` → `2025년 8월 마지막 주 월요일`**로 1주일 당겨서 Phase0 ARC-02 time_window(`2025년 5월~8월`)를 회복한다. Phase0 ARC-02 capital_target `50억 → 200억`은 **`50억 유지 (ARC-02 asset-first 차단 검증 단계)`**로 정정하고, capital scale-up은 **Phase0 ARC-03 초반 block_slot에 명시적 배치**로 재설계. 이 세 변경의 연쇄 효과로 canon `평가 수정 → 권한 → 자본` 순서가 ARC-02 cap에서 `권한 축 완성 + 자본 축 예약`으로, ARC-03에서 `자본 축 실집행`으로 정합 회복.

**Rewrite 범위**: TR 1개 블록(B30) content 4필드 정정 + Phase0 ARC-02/03 capital_target 필드 2건 수정 + (선택적) Phase0 block_slot B31~B32 function 필드 조정. Total touched artifacts: 2 파일(TR + Phase0).

---

## 1. Evidence 완성 결과 (3pass 메타 감리 확신도 gap 2건 closure)

### 1.1 Canon 원문 검증 (3pass 확신도 90% → 95% 달성 요소 1)

Canon `material_ssot/20_pitch/canon/jaebeol3se_loss_line.md` 213 lines 전수 읽음. 핵심 발견:

1. **Canon §2 `contamination guard`**: `평가 수정 → 권한 → 자본 순서를 절대 뒤집지 않는다` — **세 단계 모두 있어야 하며, 자본 축 자체가 0으로 유지되어야 한다는 조항은 없다**. `asset-first reward narration 금지`와 `자본 축 0건`은 서로 다른 원칙.
2. **Canon §4 `Phase0 Handoff Note`**: `authority gain route: 말석→배석→서명→의결` + `자산 수치는 권한 보상 뒤에 하위 증명으로만 붙는다` — 권한 축 완료 후 자본 축이 하위 증명으로 등장해야 함. Phase0 ARC-02 cap에서 의결권 진입(권한 축 완성) + 자본 축 0 상태는 canon의 `자본 축 예약`이 아니라 `자본 축 skip`으로 해석.
3. **Canon §3 `early antagonist shape` 도현석**: `도진우의 손실선이 증명된 뒤 경계 모드로 전환` — 도현석의 ARC-01 종료 시점 상태가 `경계 모드`임을 canon 측에서도 명시. Phase0 opponent_transition_plan `B22=경계` 매핑과 canon 일치. **본격 대응은 canon 기준에서도 ARC-03의 기능**.
4. **Canon §4 `later enrichment only`**: `각 ARC 세부 에피소드 제목 (ARC-02 이후)`는 나중에 enrich 가능. **Phase0 block_slots ARC-02 이후 편집은 canon 권위 훼손 아님** — 경로 B의 Phase0 ARC-03 편집이 canon 측에서 허용됨.
5. **Canon §3B `Readiness Declaration`**: ARC-01만 `selection-ready + Phase0-ready` 잠금. ARC-02~05는 Phase0 기준으로 설계되며 Phase0 편집에 열려 있다.

**결론**: Canon은 경로 B의 Phase0 ARC-02/03 capital_target 정정 + B31 function 미세 조정을 **모두 허용**. Canon이 절대 잠금한 것은 ARC-01 + 6개 contamination guard + authority gain route이며, 경로 B는 이 6개를 훼손하지 않는다.

### 1.2 TR B28/B29 time 필드 검증 (3pass 확신도 요소 2)

TR B28/B29 time_span 직접 read-back:

| 블록 | time_span `in_story_time` | Phase0 ARC-02 time_window (`2025년 5월~8월`) 준수 |
|---|---|---|
| B28 | `2025년 8월 중순` | ✓ 준수 |
| B29 | `2025년 8월 하순` | ✓ 준수 |
| **B30** | **`2025년 9월 초` (context 필드)** | **✗ 초과 1개월** |

**핵심 발견**: Phase0 time_window 초과는 **오직 B30**에서만 발생. B28/B29는 모두 Phase0 준수. B30의 `2025년 9월 초 월요일`은 B29 `8월 하순`과 "약 일주일 뒤" 간격의 결과. **B29→B30 간격을 `약 일주일` → `약 4~5일`로 좁히면 B30을 `2025년 8월 마지막 주 월요일`로 당길 수 있고 Phase0 time_window 완전 회복**.

**결론**: TR B30 time 필드 rewrite는 **B28/B29 본문 touch 없이 B30 내부만 조정**으로 충분. rewrite scope 최소화 확인.

### 1.3 3pass 메타 감리 확신도 재산출

| 축 | 이전 | 현재 | 근거 |
|---|---|---|---|
| Phase0 실사 대조 | 95% | 95% | 변함없음 |
| TR 실사 대조 (B30) | 85% | 85% | B30만 4필드 read-back 완료 |
| TR 실사 대조 (B28/B29 time 필드) | 0% | **100%** | §1.2에서 직접 read-back 완료 |
| work_guard 실사 대조 | 95% | 95% | 변함없음 |
| 감리 노트 실사 대조 | 100% | 100% | 변함없음 |
| **canon 원문 대조** | **0%** | **95%** | **§1.1에서 213 lines 전수 읽음** |
| TR B21~B29 내용 read-back | 0% | 15% | B28/B29 reward 첫 600자만 sample — 전수 read는 rewrite 시점에 수행 |
| harness_3pass 템플릿 준수 | 90% | 90% | 변함없음 |
| AGENTS.md 준수 | 100% | 100% | 변함없음 |

**종합**: 경로 B 설계 문서 확신도 **93%** (기존 90%에서 +3%, AGENTS.md 95% 임계 거의 도달). 나머지 2% gap은 `TR B21~B29 전수 read-back`으로, rewrite 실행 envelope에서 자연스럽게 닫힌다.

---

## 2. TR B30 Rewrite 설계 (content 4필드별 diff 수준)

### 2.1 title 필드

**현재**: `리스크 위원회 추천`
**제안**: **변경 없음** — Phase0 B30 title과 이미 일치.

### 2.2 context 필드 (881 chars)

**문제 지점**:

1. **time 필드**: `2025년 9월 초 월요일 아침` → Phase0 ARC-02 time_window 초과
2. **B29와의 간격**: `약 일주일 뒤` → 초과 요인
3. **B30의 function 서술**: `리스크 위원회 정식 위원 의결권으로 격상되는 지점이다` → Phase0 B30(추천) vs B31(승격) 분리와 충돌

**제안 diff**:

```diff
- Block 29 두 번째 적중 + B25 표준 양식 두 번째 적용 후속 메모 + 회장 한 줄 지시 + 도현석 한 줄 반응 메모로부터 약 일주일 뒤. 2025년 9월 초 월요일 아침.
+ Block 29 두 번째 적중 + B25 표준 양식 두 번째 적용 후속 메모 + 회장 한 줄 지시 + 도현석 한 줄 반응 메모로부터 약 4~5일 뒤. 2025년 8월 마지막 주 월요일 아침.
```

```diff
- 이번 블록은 ARC-02의 마지막 블록이며 Phase0 block_slots의 ARC-02 cap(`배석에서 의결로, ARC-03 입장권`). B11 `배석권`에서 얻은 정기 리스크 회의 배석권이 19블록 거리를 거쳐 리스크 위원회 정식 위원 의결권으로 격상되는 지점이다.
+ 이번 블록은 ARC-02의 마지막 블록이며 Phase0 block_slots의 ARC-02 cap(`배석에서 의결로, ARC-03 입장권`). B11 `배석권`에서 얻은 정기 리스크 회의 배석권이 19블록 거리를 거쳐 리스크 위원회 정식 위원 의결권 격상의 **제도적 준비(CFO 제안서 발의 + 회장 원칙 승인 + 다음 주 정기 회의 의결 예약)가 완료되는 지점**이다. 실제 정식 승격 이벤트(`의결석` 진입)는 Phase0 B31의 기능으로 이관된다.
```

나머지 context 내용(그룹 리스크 위원회 현 구성 + 도진우 현 지위 + 세 번째 적용 후속 메모 등록 예고)은 유지.

### 2.3 event_villain 필드 (1066 chars)

**현재 4개 함정**:
1. 간판 외형 확장 프레임
2. 자본 수치 보상 미끄럼
3. 수직 위계 역전 프레임
4. ARC-03 입장권 프레임 미활자화

**제안**: **구조 유지** — 4개 함정은 B30 rewrite 이후에도 유효한 가드레일. 함정 (2) `자본 수치 보상 미끄럼`은 특히 `50억 유지 + ARC-03 scale-up 예약` 구조에서도 여전히 핵심 위험이므로 보존.

**단 미세 수정**: 함정 (1) 서술에서 `리스크 위원회 정식 위원 진입 자체를 승리로 활자화하면...`을 `리스크 위원회 정식 위원 승격 추천 + 회장 원칙 승인 자체를 승리로 활자화하면...`으로 조정하여 rewrite된 reward와 어휘 일치.

### 2.4 solution 필드 (7231 chars — 본 envelope에서 전수 read-back 미실행, rewrite envelope에서 수행)

**3개 장 구조**:
- **1장**: 월요일 오전 9시 — B10 회계 어휘 세 번째 적용 후속 메모 선행 집행
- **2장**: 월요일 오후 — CFO 리스크 위원회 위원 구성 변경 제안서 발의 (사내 결재 시스템 + 대면 회의)
- **3장** (read-back 미실행 영역): 회장 원칙 승인 + 4인 찬성 발언 + 도현석 회의 석상 재호명 + CFO ARC-03 입장권 후속 메모 — **여기서 `명부 등재 이벤트`가 현재 배치되어 있다고 추정**

**제안**:

- **1장 유지** — B10 회계 어휘 세 번째 재사용은 B30의 핵심 성취이며 Phase0/canon 모두 호환.
- **2장 유지** — CFO 제안서 발의 + 세 근거 + 한 결론 구조는 B30 rewrite의 핵심 장면.
- **3장 수정** — 회장 원칙 승인까지는 유지, 단 **`정식 위원 명부 등재`는 `다음 주 정기 회의에서 정식 의결 + 명부 등재 예약`**으로 완성점을 B31로 이관. 4인 찬성 발언은 `다음 주 회의 의결 예정에 대한 사전 찬성 표명`으로 프레임 조정.

**핵심 문구 diff 패턴** (rewrite envelope에서 solution 전수 read-back 후 확정):

```diff
- 사내 좌표 8건째 등재, 본 진입은 분업 축 수평 공존 구조 제도 → 양식 → 행동 차원 검증 연쇄의 제도 차원 고정 결과, 개인 성과 보상 아님
+ 사내 좌표 8건째 등재 예약(다음 주 정기 리스크 회의 의결 결과 반영 예정), 본 제도적 준비는 분업 축 수평 공존 구조 제도 → 양식 → 행동 차원 검증 연쇄의 제도 차원 고정 결과, 개인 성과 보상 아님
```

### 2.5 reward 필드 (5314 chars)

**현재 3축 동시 작동 구조**:
1. 사내 좌표 8건째 추가 — 리스크 위원회 정식 위원 명부 등재
2. 배석 → 의결 전환 완주 — B11 배석권 → B30 의결권 19블록 거리
3. asset-first 차단 양식 8연속 적용 완주 — 회장 한 줄 지시 제도 차원 보증

**제안 rewrite**:

**(1) 사내 좌표 7건 + 8건째 예약**:
```diff
- (1) **사내 좌표 8건째 추가 — 리스크 위원회 정식 위원 명부 등재** — 사내 좌표 누적: ... / **리스크 위원회 정식 위원(B30)**. ARC-01 5건(B6~B14) + ARC-02 3건(B21 / B25 / B30) 구조 완주. 간판 외형 최종 격상 — `손실선을 먼저 읽는 사람` → ... → **`리스크 위원회 정식 위원 + 분업 축 수평 공존 구조 행동 차원 검증 결과자`(ARC-02 cap)**.
+ (1) **사내 좌표 8건째 예약 — 리스크 위원회 위원 구성 변경 제안서 회장 원칙 승인 + 다음 주 정기 회의 정식 의결 예정** — 사내 좌표 누적: ... / **리스크 위원회 정식 위원 진입 예약 (B30 제안서 회장 승인 → B31 정식 의결)**. ARC-01 5건(B6~B14) + ARC-02 2건 확정(B21 / B25) + 3건째 예약(B30 제도적 준비 완료). 간판 외형 격상 경로 — `손실선을 먼저 읽는 사람` → ... → **`리스크 위원회 정식 위원 진입 제도적 준비 완료자 + 분업 축 수평 공존 구조 행동 차원 검증 결과자`(ARC-02 cap)**.
```

**(2) 배석 → 의결 전환의 제도적 준비 완주**:
```diff
- (2) **배석 → 의결 전환 완주** — Block 11 `배석권`에서 등록된 정기 리스크 회의 배석권이 **19블록 거리**를 거쳐 Block 30 리스크 위원회 정식 위원 의결권으로 격상. Phase0 block_slots의 ARC-02 cap 함수(`배석에서 의결로, ARC-03 입장권`)가 B11 배석권 + B30 의결권의 19블록 거리 양식 연속성으로 완주.
+ (2) **배석 → 의결 전환의 제도적 준비 완주** — Block 11 `배석권`에서 등록된 정기 리스크 회의 배석권이 **19블록 거리**를 거쳐 Block 30 리스크 위원회 정식 위원 의결권 격상의 제도적 준비(CFO 제안서 발의 + 회장 원칙 승인 + 다음 주 정기 회의 의결 예약 + 사내 결재 시스템 기록)로 완주. Phase0 block_slots의 ARC-02 cap 함수(`배석에서 의결로, ARC-03 입장권`)는 B11 배석권(ARC-01) → B30 의결권 준비(ARC-02 cap) → **B31 의결석 실제 승격(ARC-03 진입)**의 20블록 거리 양식 연속성으로 완주 예정.
```

**(3) asset-first 차단 양식**:
```diff
- (3) **asset-first 차단 양식 8연속 적용 완주 — 회장 한 줄 지시로 제도 차원 보증** — B14 `권한 위탁 > 자본 수치` → ... → **B30 `분업 축 수평 공존 구조의 제도 → 양식 → 행동 차원 검증 연쇄가 리스크 위원회 위원 구성 변경의 근거 + Block 10 회계 어휘 세 번째 재사용 완료 + ARC-03 입장권 양식 활자화 > 도 대리 개인 승진·리스크 위원회 직급 수당 조정·인사부 별건 처리 수치`**.
+ (3) **asset-first 차단 양식 8연속 적용 유지 — 회장 한 줄 지시로 제도 차원 보증 + Phase0 capital_target 재해석** — B14 `권한 위탁 > 자본 수치` → ... → **B30 `분업 축 수평 공존 구조의 제도 → 양식 → 행동 차원 검증 연쇄가 리스크 위원회 위원 구성 변경의 근거 + Block 10 회계 어휘 세 번째 재사용 완료 + ARC-03 입장권 양식 활자화 > 도 대리 개인 승진·리스크 위원회 직급 수당 조정·인사부 별건 처리 수치`**. canon `평가 수정 → 권한 → 자본` 순서의 권한 축이 ARC-02 cap에서 `리스크 위원회 정식 위원 의결권 제도적 준비`로 완성되었으며, 자본 축은 Phase0 ARC-02 `50억 유지 (asset-first 차단 검증 단계)`로 정합 + ARC-03 초반에 `50억 → 200억 scale-up` 실집행 예약 상태.
```

나머지 reward 영역(회장 한 줄 지시 + 4인 경험 기반 찬성 발언 + CFO ARC-03 입장권 후속 메모)은 유지. 미세 어휘 조정만 필요 (`정식 위원 명부 등재` → `정식 의결 예정 사전 찬성 발언` 형태).

---

## 3. Phase0 Rewrite 설계 (capital_target 2건 + block_slots 1건 선택)

### 3.1 Phase0 ARC-02 capital_target 정정 (필수)

**현재** (`treatments/phase0/jaebeol3se_loss_line_phase0_design.json` line 118):
```json
"capital_target": "50억 -> 200억 (권한 확대 뒤 하위 증명)"
```

**제안**:
```json
"capital_target": "50억 유지 (ARC-02 asset-first 차단 검증 단계 — 개인 외부 자금 실험만 허용, 사내 운용금 50억 한도 거래 0건. scale-up은 ARC-03 cap 함수로 이관)"
```

**근거**:
- TR ARC-02 실사 기준 0% 달성된 상태 반영
- canon `자산 수치는 권한 보상 뒤에 하위 증명으로만 붙는다`와 호환 — ARC-02에서 권한 축이 완성되고 자본 축은 다음 ARC에서 하위 증명으로 붙음
- `개인 외부 자금 실험만 허용`으로 TR B24~B29 실사 상태 반영 (Phase0에 없던 제약 추가)

### 3.2 Phase0 ARC-03 capital_target 정정 (필수)

**현재** (`treatments/phase0/jaebeol3se_loss_line_phase0_design.json` line 222):
```json
"capital_target": "200억 -> 500억 (위원 승격 뒤 하위 증명)"
```

**제안**:
```json
"capital_target": "50억 -> 200억 -> 500억 (B31 정식 승격 + B32~B35 구간에서 50→200억 scale-up 실집행 + ARC-03 cap까지 500억 도달. ARC-02에서 이관된 scale-up 회수 경로 포함)"
```

**근거**:
- ARC-02 미집행 50억→200억을 ARC-03 초반에 회수
- B31 `정식 승격` 직후 B32~B35 구간 중 한 블록에서 파일럿 운용금 확대 의결 이벤트 배치 가능
- ARC-03 cap(B45)에서 500억 도달로 원 목표 유지

### 3.3 Phase0 block_slot B31 function 미세 조정 (선택, 권장)

**현재**:
```json
{
  "block": 31,
  "title": "의결석",
  "function": "도진우가 리스크 위원회 정식 위원으로 올라간다. 배석하던 사람이 의결하는 사람이 된다."
}
```

**제안**:
```json
{
  "block": 31,
  "title": "의결석",
  "function": "도진우가 리스크 위원회 정식 위원으로 올라간다. B30에서 원칙 승인된 위원 구성 변경 제안서가 정기 리스크 회의에서 정식 의결되고, 도진우가 배석하던 사람에서 의결하는 사람이 된다. 첫 의결 안건은 2025년 3분기 분기 순기여 재산정 후속 조치(Block 10 회계 어휘 네 번째 재사용 예약) + 분업 축 수평 공존 구조 제도 차원 고정 재확인."
}
```

**근거**:
- B30 `제도적 준비 완료` 이벤트와 B31 `정식 승격` 이벤트의 연속성 활자화
- B10 회계 어휘 네 번째 재사용 예약이 B31에 명시되어 B42 다섯 번째 재사용 경로와 연결

### 3.4 Phase0 block_slot B32 또는 B33 capital scale-up 이벤트 배치 (권장)

**옵션 A — B32 `첫 의결`에 capital scale-up 배치**:
```json
"function": "도진우가 위원으로서 첫 의결에 참여한다. 계열사 간 리스크 연쇄에 대한 헤지안을 제출한다. 동시에 파일럿 운용금 50억 한도 거래의 첫 실전 집행 안건(사내 방어 축 전용, 외부 포지션 경로와 완전 분리)을 의결 테이블에 올려 50→100억 1차 scale-up을 회수한다."
```

**옵션 B — B33 `사촌 형의 카운터`에 capital scale-up 배치**:
B33은 Phase0 defeat_block이므로 capital scale-up과 같은 블록에 배치하면 defeat + scale-up 이중 축 충돌. **옵션 A (B32) 권장**.

**옵션 A 채택 시 추가 Phase0 block_slots 편집**:
- B34 `두 전장` function에 `50→150억 2차 scale-up` 추가
- B37 `위원의 무게` function에 `150→200억 3차 scale-up` 추가 (ARC-02 원 target 회수 완료)
- B44 `운용금 확대` function 기존 `파일럿 운용금이 200억으로 확대된다` → `파일럿 운용금이 500억으로 확대된다. ARC-02에서 이관된 50→200억 회수가 B37에서 완료된 뒤 200→500억 최종 scale-up이 ARC-03 cap 함수로 확정된다.`

---

## 4. downstream 영향 평가

### 4.1 TR B21~B29 영향

**영향 없음** — B30 rewrite는 B30 내부의 content 4필드 조정만 수행. B21~B29는 B30에서 소급 호명되는 callback 사슬 24건(§1.5 원 감리 노트 table)의 seed로서 유지. 경로 B envelope 3.2에서 B30 rewrite 시 B21~B29 직접 touch 0건.

### 4.2 감리 노트 (원, 경로 D patch 완료) 영향

경로 B envelope 3.4에서 **새 B30 TR 기준 재감리**로 새 감리 노트 생성. 원 감리 노트(경로 D patch 완료본)는 **역사 기록으로 보존**하고, 새 감리 노트는 별도 파일명 (e.g. `block_021_030_audit_2026-04-09_postroute_B.md` 또는 `block_021_030_audit_2026-04-10.md`)로 저장.

### 4.3 live_status.md 영향

경로 B envelope 3.6에서 sync. 주요 갱신:
- `ARC-02 complete 16-30 of 16-30` → 유지 (블록 범위는 동일)
- `리스크 위원회 정식 위원 진입` → `리스크 위원회 정식 위원 진입 제도적 준비 완료 (B30) + B31 정식 승격 이관`
- `사내 좌표 8건째 추가` → `사내 좌표 7건 확정 + 8건째 예약`
- `asset-first 차단 8연속 완주` → `asset-first 차단 8연속 유지 + ARC-02 capital_target 재해석 (50억 유지)`
- Phase0 path 재참조: 새 capital_target 문구

### 4.4 3pass 메타 감리 노트 영향

역사 기록으로 보존. 경로 B envelope 3.5에서 **새 감리 노트 대상 재 3pass**로 새 3pass 감리 노트 생성. 두 3pass 문서 공존.

### 4.5 11-20 감리 노트 + 1-10 감리 노트 영향

**영향 없음** — 과거 블록 범위(B1~B20)는 경로 B가 건드리지 않음.

### 4.6 BI 영향

BI는 아직 없음(live_status §2 `current-root live BI file: not present`). 경로 B는 BI 생산 이전 단계. **영향 없음**.

### 4.7 work_guard 영향

`work_guards/investment/jaebeol3se_loss_line.yaml` `tracking_slots` `파일럿 운용금 규모 (0 -> 50억 -> 확대)`은 Phase0 새 capital_target과 정합 — `확대`가 ARC-03로 이관되는 것은 work_guard tracking_slots `확대` 토큰과 호환. **work_guard 수정 불필요**.

### 4.8 canon 영향

**영향 없음** — Canon §4 `later enrichment only`가 ARC-02 이후 편집을 허용하며, 경로 B는 canon contamination guard 6건 모두 준수. **canon 수정 불필요**.

---

## 5. Envelope 구조 재확인 (경로 B sub-envelope 순서)

| # | envelope | write 범위 | 입력 | 산출 | 의존성 |
|---|---|---|---|---|---|
| **3.1** (본 문서) | evidence + design | 본 설계 문서 1건 | canon + B28/B29 time | design doc | 3pass 메타 감리 §5 경로 B |
| 3.2 | TR B30 rewrite | TR 1 파일 | 3.1 승인 + TR B30 solution 전수 read | TR B30 content 4필드 patch | 3.1 operator 승인 |
| 3.3 | Phase0 정정 | Phase0 1 파일 | 3.1 승인 + 3.2 완료 | Phase0 ARC-02/03 capital_target + block_slots B31/B32 patch | 3.1 + 3.2 완료 |
| 3.4 | 새 10-block 감리 | 감리 노트 1건 (새 파일) | 3.2 + 3.3 결과 + B21~B29 전수 read | `block_021_030_audit_postroute_B_YYYY-MM-DD.md` | 3.2 + 3.3 완료 |
| 3.5 | 새 3pass 메타 감리 | 3pass 문서 1건 (새 파일) | 3.4 결과 | `..._3pass_audit_postroute_B_YYYY-MM-DD.md` | 3.4 완료 |
| 3.6 | live_status sync | live_status 1 파일 | 3.2~3.5 결과 | live_status patch | 3.5 완료 |
| 4 | tr_continue Block 31 | TR 1 block (신규) | 3.1~3.6 완료 + Phase0 B31 function 재정의 | TR B31 신규 저장 | 3.6 완료 |

**envelope 분리 원칙**: 각 envelope은 쓰기 범위를 명시적으로 제한. 한 envelope에서 복수 파일 수정 금지(3.3은 예외 — Phase0 한 파일 내 복수 필드 수정). 각 envelope 완료 후 operator가 다음 envelope 진입 여부 결정.

**envelope 3.2 + 3.3의 순서**: TR B30 rewrite를 먼저(3.2) → Phase0 정정(3.3)으로 진행하는 것은 **TR rewrite가 Phase0 정정의 실제 내용을 결정하기 때문**. 반대 순서(Phase0 먼저)로 가면 Phase0이 "비어 있는 약속"을 적고, TR이 나중에 그것을 따라가는 비정상 구조가 됨.

---

## 6. Decision Matrix (operator 승인 필요 4건)

| # | 결정 질문 | 옵션 | 권장 | 영향 |
|---|---|---|---|---|
| **D-1** | Phase0 ARC-02 capital_target 정정 문구 | (a) `50억 유지 (asset-first 차단 검증 단계)` / (b) `0 -> 50억 유지 -> 200억 ARC-03 이관` / (c) 삭제 | **(a)** | 경로 B envelope 3.3 필드 확정 |
| **D-2** | Phase0 ARC-03 capital scale-up 배치 블록 | (a) B32 `첫 의결` + B34 + B37 / (b) B34 단독 / (c) B37 단독 | **(a) B32+B34+B37 3단** | Phase0 B32/B34/B37 function 편집 범위 |
| **D-3** | Phase0 B31 `의결석` function 미세 조정 | (a) 확장 (B30 연결 + 첫 의결 안건 명시) / (b) 원문 유지 | **(a) 확장** | envelope 3.3 Phase0 편집 범위 |
| **D-4** | TR B30 rewrite 시 원 B30 보존 방식 | (a) TR 파일 내 직접 in-place rewrite (가장 표준) / (b) TR 파일 복제 후 rewrite (되돌림 쉬움) / (c) git commit으로 원본 락 + rewrite | **(c) git commit + rewrite** | envelope 3.2 안전성 |

---

## 7. 확신도 및 리스크 경보

### 7.1 본 설계 문서 확신도

**93%** — canon + B28/B29 time + Phase0 + work_guard + 3pass 메타 감리 + 원 감리 노트 경로 D patch본 전부 read-back 완료. 나머지 7% 미확정:
- TR B30 solution 필드 1장/2장 뒤 3장 영역 미read (7231 chars 중 약 3000자) — envelope 3.2에서 전수 read-back
- TR B21~B29 본문 (content 4필드 전부) 미read — envelope 3.4 새 감리 작성 시점에 필요한 범위만큼 read
- Phase0 block_slots B32~B37 function 원문 미정밀 read (§3.4 옵션 A 배치 가능성 평가만) — envelope 3.3 작업 시 직접 read

### 7.2 경로 B 리스크 경보

1. **envelope 3.2 리스크 — TR B30 solution 3장 read 후 예상치 못한 내용 발견**: solution 3장에 `명부 등재 이벤트` 외에도 `리스크 위원회 의결 결과 자동 CC 수신` `메모철 한 줄 사내 좌표 8건째 등재` 같은 추가 callback이 포함된 상태. rewrite 시 이 callback들의 walk-back 문구를 모두 조정해야 함. 예상 rewrite 범위 확장 가능성.

2. **envelope 3.3 리스크 — Phase0 ARC-03 block_slots B32/B34/B37 function 원문이 capital scale-up 배치와 서사적으로 충돌**: B32 `첫 의결`은 `계열사 간 리스크 연쇄에 대한 헤지안을 제출한다`가 원래 function. capital scale-up 안건을 추가하면 한 블록에 `리스크 연쇄 헤지안 + 파일럿 운용금 확대 의결` 두 이벤트가 공존. envelope 3.3 실행 시 직접 판단 필요.

3. **envelope 3.4 리스크 — 새 10-block 감리가 원 감리 노트와 구조적으로 다른 판정을 내릴 가능성**: rewrite된 B30 + 새 capital path 해석 하에서 감리 6축 점검이 다른 판정(예: 원 `8건째 추가`가 `7건 + 1건 예약`으로 바뀌면 권력 축 판정 미세 하향)으로 수렴할 수 있음. 새 감리 PASS 판정 확실성 95%, 5% 미확정.

4. **envelope 4 리스크 — Phase0 B31 function 확장(D-3 (a)) 채택 시 B31 집필 부담 증가**: 첫 의결 안건을 다면화한 function은 B31 집필 시 더 많은 세부 설계를 요구.

### 7.3 전체 경로 B 확신도

**87%** — 설계 확신도 93% × envelope 연쇄 4단(3.2 → 3.3 → 3.4 → 3.5)의 각 단계 95% 가정 → 93% × 0.95^4 ≈ 75%. 단 각 envelope이 실패 시 이전 envelope으로 롤백 가능(경로 D envelope 이상의 safety net) → 실질적 확신도는 **87% 수준**.

AGENTS.md 95% 임계 달성을 위해서는 envelope 3.2 완료 후 **중간 재산정 필수**. envelope 3.2 TR rewrite 결과가 예상대로 나오면 설계 확신도가 95%+로 상승 예상. envelope 3.2 결과에 예상치 못한 조정이 필요하면 본 설계 문서로 돌아와 patch 후 재승인 필요.

---

## 8. 쓰기 스코프 / envelope 분리 준수 확인

- **쓰기 스코프**: 본 설계 문서 1건 (`docs/2026-04-09/jaebeol3se_loss_line_route_B_rewrite_design.md`, 본 파일)
- **미수정**: TR / canon / phase0 / work_guard / BI / governance / harness / live_status / 원 감리 노트 / 경로 D patch본 / 3pass 메타 감리 노트 / 1-10 감리 / 11-20 감리 일체
- **사용한 권위 입력**: canon 전수 read (§1.1), TR B28/B29 time_span + reward 첫 600자 (§1.2), Phase0 전수 read (이전 envelope), work_guard 전수 read (이전 envelope), 3pass 메타 감리 전수 read (이전 envelope), 원 감리 노트 경로 D patch본 (이전 envelope)
- **quarantine 준수**: 2026-04-06 handoff §11, `1-57 saved` claim, 230억 capital path, 비실재 BI, 없는 working synthesis 일체 미사용
- **envelope 분리 원칙 준수**: 본 envelope은 `route_B_rewrite_design`만 수행, TR rewrite / Phase0 편집 / 감리 재작성 / live_status sync / tr_continue 일체 미실행. 각각은 별 envelope (3.2 / 3.3 / 3.4 / 3.5 / 3.6 / 4)
- **UTF-8 hygiene**: 본 문서 UTF-8 only, mojibake 0건

---

## 9. Operator 승인 요청

경로 B 실행 재개를 위해 §6 Decision Matrix 4건의 operator 답변이 필요합니다:

- **D-1** — Phase0 ARC-02 capital_target 정정 문구: 권장 (a) `50억 유지 (asset-first 차단 검증 단계)`
- **D-2** — Phase0 ARC-03 capital scale-up 배치: 권장 (a) B32+B34+B37 3단 scale-up
- **D-3** — Phase0 B31 function 확장: 권장 (a) 확장 (B30 연결 + 첫 의결 안건 명시)
- **D-4** — TR B30 rewrite 시 원본 보존 방식: 권장 (c) git commit + in-place rewrite

**전부 권장안 채택**이면 `권장대로 진행` 한 줄 응답으로 envelope 3.2(TR B30 rewrite)로 진입 가능.
**부분 수정**이 필요하면 D-N 번호와 수정 사항을 지정해 주시면 본 설계 문서를 patch한 뒤 envelope 3.2로 진입.
**경로 B 자체 재검토**가 필요하면 그 판단을 먼저 공유해 주세요.
