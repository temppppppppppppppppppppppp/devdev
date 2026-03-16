<!-- [추적필요] -->
<\!-- [추적필요] -->
# 원고 모순 전수조사 — 3Pass 감리

> 작성일: 2026-03-16
> 범위: 24개 DB, 109화, 546,661자 전수조사 결과 75건 (CRITICAL 9 / IMPORTANT 29 / MINOR 37)
> 목적: CRITICAL 9건 + 주요 IMPORTANT 패턴을 코드베이스 방어체계와 대조, LLM 한계 vs 코드 개선 여지 판정

---

## Pass 1: 현행 방어체계 매핑

### 1.1 다층 방어 아키텍처 요약

```
[Layer 1] 컨텍스트 주입 (예방)
├── Tier 1: 직전 30화 원문 전체
├── Tier 2: 31~60화 에피소드 요약
├── Tier 3: 61화+ 아크 요약
├── WorldState: 9필드 세계 상태 스냅샷 (50K)
├── FactLedger: 누적 팩트 원장 (25K)
├── ChainLink: 직전 화 핸드오프 (1~2K)
├── ContinuityPacket: 이번 화 관련 NPC 6명 집중 (7K)
└── Dead NPC / Inventory / Item Timeline

[Layer 2] 포스트검증 — 8 Advisory 병렬 (60s/개, 300s 전체)
├── TruthGate: 사망NPC 부활, 미보유 아이템, 파괴 장소, 스킬 중복
├── NpcDriftAdvisor: 상위 8 NPC 속성 표류 (LLM)
├── NumericDriftAdvisor: 5화 주기 수치 드리프트 (LLM)
├── FlashbackVerifier: 회상 오염 (LLM)
├── InfoParadoxChecker: 1인칭 정보 역설 (LLM)
├── RelationshipDriftAdvisor: 관계 역전 (ep≥5, LLM)
├── LongTermRepetitionAdvisor: 장기 반복 (ep≥20, LLM)
└── NumericConsistencyChecker: 수치/직급/산술/중복 이벤트 (Python)

[Layer 3] Director 판정
├── consistency 가중치: 25% (최고)
├── Contradiction Firewall: CRITICAL 1건 or MAJOR 2건 → 자동 REJECT
└── 20개 일관성 체크리스트

[Layer 4] ContinuityManuscript 검증
├── 아이템/장비 연속성
├── 상태 연속성 (부상/기력)
├── 관계 연속성
├── 블루프린트 준수
└── 엔티티 이름 일관성 (5화 윈도우)
```

---

## Pass 2: CRITICAL 9건 — 코드 방어 대조 분석

### C-01: 투자 수익 계산 불일치 (TF-A, M-4)

**현상**: ep9 미실현 ~30억 → ep11 유가 70달러 폭락 → ep12 절반 매도로 50억 실현. 수익 성장 경로 미설명.

**현행 방어**:
- NumericDriftAdvisor: 5화 주기 실행 — ep9→ep12 구간에서 트리거될 수 있으나, 수치를 "드리프트"로만 감지, P&L 정합성은 미검증
- NumericConsistencyChecker: 산술 검증 있으나 "이전 화 수익 + 이번 화 변동 = 현재 잔고" 식의 연쇄 검증 없음
- FactLedger: 숫자 이력 추적하지만 산술적 인과관계 미검증

**판정**: **코드 개선 가능**
- 원인: 금융 P&L 연쇄 검증 로직 부재
- 개선안: NumericConsistencyChecker에 `_check_financial_pl_chain()` 추가
  - FactLedger의 `numbers` 이력에서 `자산`, `투자원금`, `수익` 키워드 추출
  - 직전 화 잔고 + 이번 화 변동 = 현재 잔고 검증
  - 레버리지 배수 × 가격 변동률 → 예상 손익 vs 서술 손익 비교

**난이도**: MEDIUM (FactLedger 인프라 존재, 검증 로직만 추가)

---

### C-02: 박성호 직급 차장→팀장 (TF-A, M-1)

**현상**: ep6-7 "차장" → ep11+ "팀장" 설명 없이 변경

**현행 방어**:
- WorldState: `known_attrs`에 역할 변경 추적 가능 (prev + changed_ep)
- NpcDriftAdvisor: 상위 8 NPC만 검사 — 박성호가 top 8에 안 들면 누락
- NumericConsistencyChecker: `_check_title_progression()` 있으나 주인공 직급만 검사
- ContinuityManuscript: entity_consistency 있으나 직급은 검사 범위 밖

**판정**: **코드 개선 가능**
- 원인: NPC 직급/호칭 변경을 명시적으로 추적하는 전용 검사 없음
- 개선안:
  1. NumericConsistencyChecker `_check_title_progression()`을 NPC까지 확장
  2. FactLedger `characters` 이력에 `title` 필드 명시 추적
  3. NpcDriftAdvisor top 8 제한 완화 또는 "직급 변동 감지" 별도 패스 추가

**난이도**: LOW (기존 인프라에 검사 범위 확장)

---

### C-03: 사무실 시스템 이중 설치 (TF-A, M-6)

**현상**: ep5 "블룸버그 포함 최고 사양 설치" → ep10 "PC방보다 못한 환경" 재구축

**현행 방어**:
- TruthGate: 파괴된 장소 방문 체크 — "시스템 설치"는 장소 파괴/복구가 아님
- FactLedger: 아이템 추적은 하지만 "사무실 시스템"은 아이템으로 분류 안 됨
- WorldState: `active_items`에 "블룸버그 터미널" 등록되지 않으면 추적 불가
- ContinuityManuscript: 5화 윈도우 — ep5→ep10은 윈도우 밖

**판정**: **LLM 한계 + 컨텍스트 윈도우 갭**
- 원인 1: "시스템 설치"는 사건(event)이지 엔티티가 아님 → 추적 체계의 구조적 한계
- 원인 2: ContinuityManuscript 5화 윈도우로 ep5 정보가 ep10 검증 시 누락
- 부분 개선안:
  1. ContinuityManuscript 윈도우를 10화로 확대 (비용 증가)
  2. FactLedger에 "설비/인프라" 카테고리 추가하여 사무실 환경 변화 추적
  3. WorldState `active_items`에 주요 설비 등록 정책 추가

**난이도**: MEDIUM-HIGH (새 카테고리 추가 + 윈도우 확대 비용 검토 필요)

---

### C-04: 자본금 20억 vs 입금 15억 (TF-B, M-4)

**현상**: 아버지에게 20억 선언 → 증권사 입금 15억. 3억 갭 미설명.

**현행 방어**:
- NumericConsistencyChecker: 산술 검증 — 두 수치가 같은 화에 있으면 불일치 탐지 가능
- FactLedger: 숫자 이력 추적 — "자본금"과 "입금액"이 별도 키로 등록되면 연결 안 됨

**판정**: **코드 개선 가능**
- 원인: 동일 자산의 "선언 금액" vs "실행 금액" 교차 검증 없음
- 개선안: NumericConsistencyChecker에 `_check_capital_flow_consistency()` 추가
  - 같은 화 내에서 금액 키워드 쌍 추출 (자본금/투자금/입금/이체 등)
  - 총합 정합성 검증 (선언액 ≥ 사용액 합계)

**난이도**: MEDIUM (금융 도메인 키워드 사전 필요)

---

### C-05: 경주마 매각 이벤트 중복 (TF-C, M-6)

**현상**: ep1 코치 박에게 "아퀼라" 매각 전화 → ep3 박 코치 "오랜만이다!" 첫 연락 반응 반복

**현행 방어**:
- NumericConsistencyChecker: `_check_first_event()` — "처음" 키워드 중복 감지, 그러나 "전화 통화" 같은 일반 사건은 미검사
- WorldState: `resolved_plots`에 "경주마 매각" 등록 가능하지만, 자동 추출 시 이벤트 단위 누락 가능
- FactLedger: items에 "아퀼라" 소유권 변경 추적 가능

**판정**: **코드 개선 가능**
- 원인: "동일 인물에게 동일 요청" 중복 감지 로직 부재
- 개선안:
  1. FactLedger items에 `status: "매각 진행 중"` → `"매각 완료"` 상태 전이 추적 강화
  2. ChainLink에 `pending_transactions` 필드 추가
  3. resolved_plots 자동 추출 정확도 향상 (state_changes에서 거래/연락 이벤트 파싱)

**난이도**: MEDIUM (이벤트 중복 감지는 의미론적 판단 필요 → LLM advisory 추가가 적합)

---

### C-06: 증권사명 미래증권→한미증권 (TF-D, M-1)

**현상**: ep2 "미래증권" → ep5 "한미증권" 설명 없이 변경

**현행 방어**:
- ContinuityManuscript: entity_consistency 검사 있음 (5화 윈도우) — ep2→ep5는 윈도우 내
- WorldState: organizations에 등록 가능
- FactLedger: organizations에 이름+상태 추적

**판정**: **현행 체계로 잡아야 하는데 못 잡음 → 코드 버그 가능성**
- 원인 분석:
  1. "미래증권"이 organization으로 자동 추출되지 않았을 가능성 (state_changes 파싱 누락)
  2. ContinuityManuscript가 entity_consistency를 LLM에 위임 → LLM이 놓침
  3. 5화 윈도우 내이므로 원문은 제공됨 — LLM 판단 실패
- 개선안:
  1. FactLedger organizations 자동 추출에 "증권사/은행/기업" 등 금융기관 키워드 추가
  2. Python 레벨 entity name registry — 전 에피소드 조직명 해시맵 + diff 감지
  3. NumericConsistencyChecker에 `_check_organization_name_consistency()` 추가

**난이도**: LOW (Python 해시맵 비교로 구현 가능)

---

### C-07: 형 이름 한태민→한서준 (TF-F, M-1)

**현상**: 핵심 NPC인 형의 이름이 에피소드 간 완전 변경

**현행 방어**:
- WorldState: alive_npcs에 이름으로 키잉 — 이름이 바뀌면 별개 NPC로 등록
- ContinuityManuscript: entity_consistency — 5화 윈도우 내라면 감지 가능
- TruthGate: NPC role consistency — 같은 역할에 다른 이름이면 감지 가능

**판정**: **현행 체계로 잡아야 하는데 못 잡음 → LLM 생성 단계 문제**
- 원인 분석:
  1. 해당 프로젝트가 2화짜리 → 1→2화 전환 시 WorldState가 아직 얕음
  2. LLM이 생성 시 직전 화 원문을 받았음에도 이름을 변경
  3. TruthGate는 "같은 역할 다른 이름" 감지 가능하지만, "형"이라는 역할이 명시적으로 추출되어야 함
- 개선안:
  1. Python 레벨 핵심 NPC 이름 해시맵 (주인공 가족 = 불변 리스트)
  2. TruthGate에 "가족 관계 NPC 이름 변경 CRITICAL" 규칙 추가
  3. FactLedger characters에 `relationship: "형"` 추적 → 이름 변경 시 Python 경고

**난이도**: LOW (가족 NPC 이름 고정 검사는 단순)

---

### C-08: 기상 장소 저택→고층 아파트 (TF-F, M-3)

**현상**: 기상 장소가 가문 저택에서 고층 아파트로 변경

**현행 방어**:
- ChainLink: `location` 필드로 직전 화 위치 전달
- WorldState: protagonist.current_location 추적
- ContinuityManuscript: 상태 연속성 검사에 위치 포함

**판정**: **현행 체계로 잡아야 하는데 못 잡음 → ChainLink 추출 정확도 문제**
- 원인 분석:
  1. ChainLink location이 정확히 추출되었다면 다음 화 프롬프트에 "저택"이 명시됨
  2. LLM이 ChainLink를 무시하고 다른 장소를 설정했을 가능성
  3. 또는 ChainLink 추출 자체가 실패/부정확했을 가능성
- 개선안:
  1. ChainLink location을 Python 레벨로 검증 (직전 화 원문 마지막 1000자에서 장소 추출 → chain_link 교차 검증)
  2. Stage 4 시작 시 `assert chain_link.location != ""` 가드 추가
  3. ContinuityManuscript에 "기상 장소 = 직전 화 마지막 장소" 명시 규칙

**난이도**: LOW (ChainLink 검증 강화)

---

### C-09: 개인 자산 권한 모순 (TF-F, M-5)

**현상**: 한태민이 시우 개인 자산에 대한 권한 주장 — 설정된 소유권과 모순

**현행 방어**:
- WorldState: relationships 추적 (방향성)
- FactLedger: items 소유권 추적
- RelationshipDriftAdvisor: ep≥5에서만 실행 — 초기 에피소드 미검사

**판정**: **LLM 한계 (의미론적 추론)**
- 원인: "소유권"과 "권한"의 차이는 법적/사회적 맥락에 따른 의미론적 판단
- LLM이 캐릭터의 권한 범위를 정확히 이해하지 못하고 드라마틱 장면을 위해 설정 위반
- 부분 개선안:
  1. WorldState에 `authority_structure` 필드 추가 (가문 내 서열/권한 범위)
  2. WorkGuard에 "자산 소유권 불변 규칙" 커스텀 룰 추가 가능
  3. 근본적으로는 LLM의 맥락 이해도 한계

**난이도**: HIGH (의미론적 규칙 인코딩 난이도 높음)

---

## Pass 3: 종합 판정 + 개선 로드맵

### 3.1 판정 요약표

| # | 모순 | TF | 판정 | 난이도 | 우선순위 |
|---|------|-----|------|--------|----------|
| C-01 | 수익 계산 불일치 | A | **코드 개선 가능** | MEDIUM | P1 |
| C-02 | NPC 직급 변경 | A | **코드 개선 가능** | LOW | P1 |
| C-03 | 시스템 이중 설치 | A | **LLM 한계 + 윈도우 갭** | MEDIUM-HIGH | P3 |
| C-04 | 자본금 갭 | B | **코드 개선 가능** | MEDIUM | P1 |
| C-05 | 이벤트 중복 | C | **코드 개선 가능** | MEDIUM | P2 |
| C-06 | 증권사명 변경 | D | **코드 버그 가능성** | LOW | P0 |
| C-07 | 형 이름 변경 | F | **코드 개선 가능** | LOW | P0 |
| C-08 | 기상 장소 변경 | F | **ChainLink 정확도** | LOW | P1 |
| C-09 | 자산 권한 모순 | F | **LLM 한계** | HIGH | P3 |

### 3.2 분류 통계

| 분류 | 건수 | 비율 |
|------|------|------|
| **코드 개선 가능** (명확한 개선 경로) | 5건 | 56% |
| **코드 버그 가능성** (현행 체계가 잡아야 함) | 1건 | 11% |
| **ChainLink/윈도우 갭** (인프라 확장 필요) | 1건 | 11% |
| **LLM 한계** (구조적 한계, 부분 완화만 가능) | 2건 | 22% |

### 3.3 주요 IMPORTANT 패턴 — 코드 개선 여지

| 패턴 | 빈도 | 현행 방어 | 판정 |
|------|------|-----------|------|
| 에피소드 브릿지 문장 과도 반복 | 다수 TF | `_detect_cross_episode_repetition()` 3화 윈도우 | 윈도우 확대 가능 (LOW) |
| NPC 직급/호칭 미세 변동 | TF-A,B,D | NpcDrift top 8 제한 | 제한 완화 가능 (LOW) |
| 금액 점프 (15억→30억) | TF-A | NumericDrift 5화 주기 | 화간 자산 변동 검증 추가 (MEDIUM) |
| 메타데이터 누출 (`[원고_끝]`) | TF-D | 없음 | Python regex strip 추가 (LOW) |
| 이사회 조건 vs 실제 괴리 | TF-E 4/8 | resolved_plots | 조건문→결과 매칭 검사 추가 (MEDIUM) |

### 3.4 개선 로드맵 (우선순위순)

#### P0 — 즉시 수정 (현행 체계가 잡아야 하는 것)

| ID | 개선 | 대상 파일 | 설명 |
|----|------|-----------|------|
| P0-1 | Python 엔티티명 해시맵 | `numeric_consistency_checker.py` | 전 에피소드 NPC/조직 이름 해시맵 구축 → 이름 변경 시 CRITICAL 경고 |
| P0-2 | 가족 NPC 이름 고정 검사 | `truth_gate.py` | 가족 관계 NPC (부/모/형/제) 이름이 변경되면 즉시 CRITICAL |

#### P1 — 단기 개선 (기존 인프라 확장)

| ID | 개선 | 대상 파일 | 설명 |
|----|------|-----------|------|
| P1-1 | NPC 직급 변경 추적 | `numeric_consistency_checker.py` | `_check_title_progression()` NPC 확장 |
| P1-2 | 금융 P&L 연쇄 검증 | `numeric_consistency_checker.py` | `_check_financial_pl_chain()` — 잔고 + 변동 = 현재 |
| P1-3 | 자본 흐름 정합성 | `numeric_consistency_checker.py` | `_check_capital_flow_consistency()` — 선언액 ≥ 사용액 |
| P1-4 | ChainLink location 검증 | `stage4_context_builder.py` | 직전 화 원문 장소 추출 → chain_link 교차 검증 |
| P1-5 | 메타데이터 누출 strip | `stage4_orchestrator.py` | `[원고_끝]`, `patch_state_updates` 등 메타 태그 정규식 제거 |

#### P2 — 중기 개선 (새 검사 로직 추가)

| ID | 개선 | 대상 파일 | 설명 |
|----|------|-----------|------|
| P2-1 | 이벤트 중복 감지 advisory | 신규 또는 `truth_gate.py` | FactLedger items 상태 전이 + resolved_plots 교차로 동일 이벤트 반복 감지 |
| P2-2 | 브릿지 반복 윈도우 확대 | `stage4_interview_round.py` | `_detect_cross_episode_repetition()` 3화→7화 |
| P2-3 | NpcDrift 검사 확대 | `npc_drift_advisor.py` | top 8 → top 15 또는 "직급 변동 NPC" 전수 |

#### P3 — 장기/구조적 (LLM 한계 완화)

| ID | 개선 | 대상 파일 | 설명 |
|----|------|-----------|------|
| P3-1 | ContinuityManuscript 윈도우 확대 | `continuity_manuscript.py` | 5화→10화 (비용 증가 수반) |
| P3-2 | 설비/인프라 카테고리 | `fact_ledger.py` | FactLedger에 `infrastructure` 카테고리 추가 |
| P3-3 | 권한 구조 모델링 | `world_state.py` | `authority_structure` 필드 — ROI 낮음, 선택적 |

---

## 부록: 방어체계 블라인드스팟 종합

### A. 현행 체계가 강한 영역

| 영역 | 방어 레이어 | 신뢰도 |
|------|------------|--------|
| 사망 NPC 부활 | TruthGate + WorldState | HIGH |
| 미보유 아이템 사용 | TruthGate + Inventory | HIGH |
| 파괴 장소 방문 | TruthGate + WorldState | HIGH |
| 스킬 중복 학습 | TruthGate + NumericConsistency | MEDIUM-HIGH |
| NPC 이름 드리프트 | ContinuityManuscript (5화 내) | MEDIUM |
| 기본 산술 오류 | NumericConsistencyChecker | MEDIUM |

### B. 현행 체계가 약한 영역 (이번 감사로 확인)

| 영역 | 부재 원인 | 개선 가능성 |
|------|-----------|------------|
| 금융 P&L 정합성 | 전용 검증 로직 없음 | HIGH |
| NPC 직급/호칭 추적 | 주인공만 검사 | HIGH |
| 조직/기관명 일관성 | 자동 추출 누락 | HIGH |
| 가족 NPC 이름 고정 | 전용 규칙 없음 | HIGH |
| 이벤트 중복 (전화/거래) | 사건 단위 추적 없음 | MEDIUM |
| 장소 연속성 (5화 초과) | 윈도우 제한 | MEDIUM |
| 설비/환경 변화 추적 | 카테고리 부재 | MEDIUM |
| 소유권/권한 의미론 | LLM 추론 한계 | LOW |

### C. LLM 고유 한계 (코드로 완전 해결 불가)

1. **의미론적 추론**: "소유"와 "통제"의 차이, 사회적 맥락에 따른 권한 범위
2. **암묵적 지식**: 캐릭터가 "알아야 할 것"과 "모르는 것"의 경계
3. **인과적 일관성**: A→B→C 논리 체인의 개연성 판단
4. **장기 기억 퇴화**: 30화+ 이전 디테일의 점진적 망각 (Tier 2/3 요약으로 완화하지만 완전 해결 불가)

---

## 결론

CRITICAL 9건 중 **7건(78%)은 코드 개선으로 방지 가능**하며, 그 중 3건은 난이도 LOW로 즉시 적용 가능합니다. 나머지 2건(22%)은 LLM의 구조적 한계로, 부분 완화만 가능합니다.

가장 효과적인 즉시 조치:
1. **P0-1**: 엔티티명 해시맵 (C-06, C-07 방지)
2. **P0-2**: 가족 NPC 이름 고정 (C-07 방지)
3. **P1-2**: 금융 P&L 검증 (C-01, C-04 방지)

이 3건만 구현해도 CRITICAL의 44%(4/9)를 코드 레벨에서 차단할 수 있습니다.
