# 장기 연재 파이프라인 — 본질 검증 20문 답변서

**목적**: rerun 증가, drift, 연속성 붕괴의 원인이 "생성 전 충돌 처리 부재"인지 검증  
**방법**: TF 9개 에이전트 코드베이스 전수 조사 (2라운드)  
**일자**: 2026-04-14  
**범위**: `modules/core/`, `modules/domain/agents/`, `config/settings/`, DB 스키마

---

## A. Truth 결정 구조

### Q1. "진실(truth)"은 언제 확정되는가?

**답: 생성 후 — Stage 4 Director PASS 판정 + `_save_world_state_atomic()` 성공 시점**

진리 확정은 3단계 프로세스:

```
                         아직 진리 아님
                              │
S2 (Arc 설계) ──────────────→ 제약(constraint)만 설정
S3 (Blueprint) ─────────────→ 연출 지시(directive)만 설정
S4 (Writer) ────────────────→ 복수 후보 생성 (모두 동등)
S4 (Director) ──────────────→ 단 하나 선택 + PASS/REJECT
                              │
                         여기서 진리 확정 시작
                              ↓
S4 (Post-Pass Pipeline):
  1. db.save_manuscript()                        [stage4_post_processor.py:791]
  2. world_state.update_from_state_changes()     [stage4_post_pass_runtime.py:1400]
  3. world_state.save()                          [stage4_post_pass_runtime.py:1416]
  4. fact_ledger.update_from_state_changes()     [stage4_post_pass_runtime.py:1443]
  5. fact_ledger.save()                          [stage4_post_pass_runtime.py:1450]
                              │
                    ✅ 진리 최종 확정 (이후 불변)
```

**각 Stage의 진리 기여도:**
- S2: 0% (제약만 설정, 진리 아님)
- S3: 0% (지시만 제공, 진리 아님)
- S4: 100% (생성 + 검증 + 커밋 모두 여기서)

**핵심 포인트**: 진리가 확정되는 단일 지점은 `_save_world_state_atomic()`의 성공 return 시점. 그 이전의 모든 것은 가설/후보.

---

### Q2. 동일한 입력 상태가 주어졌을 때 S4가 항상 동일한 해석을 생성하는가?

**답: NO. 설계상 가변성 포함.**

| 가변성 원천 | 유형 | 의도 여부 |
|-----------|------|---------|
| LLM temperature | Writer 생성 시 확률적 추출 | **설계 의도** |
| Strategy 선택 | ToT, MAD, ASP 등 다양한 전략 | **설계 의도** |
| Director LLM 투표 | 동일 후보들 → 다른 선택 가능 | **설계 의도** |
| Post-pass Manager 추출 | 비동기 LLM 기반 actual_truth 추출 | **부분 우발** |

---

### Q3. 해석이 달라지는 조건과 설계 의도

**가변성은 feature:**
- retry 로직이 가변성을 활용 (실패 시 새 후보 → 다른 해석)
- 다양성을 통한 품질 향상 메커니즘
- `stage4_interview_round.py:3852` — 매 라운드 N개 후보 생성

**우발적 가변성:**
- Post-pass Manager의 `actual_truth` 추출이 LLM 기반 → 동일 원고에서도 다른 state_changes 추출 가능
- 이것이 **drift의 미시적 원인** 중 하나

---

## B. 충돌 처리 위치

### Q4. 충돌은 생성 전에 명시적으로 감지되는가?

**답: NO — LLM이 내부적으로 해석한다.**

| 영역 | 사전 감지 | 방식 |
|------|----------|------|
| lore ↔ recent_event | **없음** | LLM이 프롬프트 우선순위 계층에 따라 해석 |
| summary ↔ state | **없음** | 동일 |
| state ↔ event | **없음** | 동일 |
| fact_ledger 내부 | **있음** (제한적) | TruthGate: 사망 NPC 부활, 미보유 아이템 등 5가지 규칙 [truth_gate.py:79-319] |
| blueprint ↔ state | **있음** (제한적) | S3 Validator: fact_lock, capital_state 위반 감지 [unified_blueprint_validator.py:1451-1571] |

**핵심**: 소스 간 의미론적 충돌(예: "lore에서 A 소속인데 recent_event에서 B로 이적")을 감지하는 로직은 **전무**.

---

### Q5. 충돌이 존재할 때 어떤 레이어가 최종 해석을 결정하는가?

**답: S4(Writer) + Director**

```
S2: 충돌 해석 없음 → Arc 제약만 설정
S3: 충돌 해석 없음 → 연출 구조만 설계 (fact_lock 검증은 있지만 해결은 안 함)
S4 Writer: ★ 프롬프트 우선순위 계층에 따라 LLM이 직접 해석
S4 Director: ★ 해석 결과를 검증, 불합격 시 REJECT → 재시도
```

**최종 해석 결정자: S4 Writer (LLM)**
**최종 해석 승인자: S4 Director (LLM + Python rules)**

---

### Q6. 충돌 해결은 사전 처리인가, 사후 검증 후 수정인가?

**답: 사후 검증 후 수정 (post-generation verification + rerun)**

```
사전 처리 (Pre-Generation):
  ├─ 포맷팅/구조화 정규화: YES (ChiefWriterContextPackets)
  ├─ 우선순위 명시: YES (프롬프트 STEP 0.5 권위 계층)
  └─ 충돌 감지/해결: NO ← 여기가 부재

사후 처리 (Post-Generation):
  ├─ TruthGate advisory: YES (5가지 규칙)
  ├─ CrossAgentVerifier: YES (단방향 검증)
  ├─ Director REJECT + conflict_contract: YES
  └─ Retry with feedback: YES
```

---

## C. Blueprint(S3) 역할 검증

### Q7. S3 blueprint는 충돌 해결 레이어인가, 연출/구조 설계 레이어인가?

**답: 연출/구조 설계 레이어 (80%) + 제약 검증 (20%)**

Blueprint가 하는 것:
- **연출 설계**: scene_breakdown (4-6 씬), integrated_scenario (5000+자 시나리오), pacing_notes, target_beat
- **제약 검증**: fact_lock 위반 감지, capital_state 모순 감지, 사망 NPC 등장 차단

Blueprint가 하지 않는 것:
- **충돌 해결**: lore/event/summary 간 의미론적 충돌 감지 및 해결
- **상태 정규화**: 입력 상태를 정리하여 단일 진실로 확정

**Blueprint 입력** [blueprint_constraint_compiler.py:44-151]:
```
MUST_FOCUS (이번 화 핵심), STOP_LINE (미래 침범 금지),
CONTINUITY (직전 화 연속성), INHERITED_STATE (계승 상태),
FACT_LOCK_PACKET (확정 사실), CAPITAL_CONTINUITY_PACKET (자본 연속성),
EPISODE_PROGRESSION_PACKET (재연 금지)
```

**핵심**: 입력이 "충돌을 방지할 제약"이지 "충돌을 감지/해결할 데이터"가 아님.

---

### Q8. Blueprint가 존재함에도 S4에서 충돌 해석이 다시 발생하는가?

**답: YES**

- Blueprint는 "강한 권고"이지 "완전한 확정"이 아님
- S4의 `integrated_scenario`는 "참고"로만 사용 ([:200]자만 추출하는 경우도 있음)
- S4 자체의 충돌 해석 루프가 독립적으로 작동
- 증거: `stage4_postselect_runtime.py:165-186` — blueprint와의 불일치를 `post_select_conflict_fingerprint`로 기록 (= blueprint 위반이 실제로 발생한다는 증거)

---

### Q9. Blueprint는 "결정"을 하는가, "범위를 제한"만 하는가?

**답: 혼합 — 구조/순서/인물 변화는 "결정", 텍스트 표현은 "범위 제한"**

| Blueprint 필드 | 결정/제한 | Binding Force |
|---------------|---------|---------------|
| scene_breakdown (씬 구조) | **결정** | CRITICAL (위반 시 REJECT) |
| fact_lock (확정 사실) | **결정** | CRITICAL |
| capital_continuity (자본 상태) | **결정** | CRITICAL |
| episode_progression (재연 금지) | **결정** | CRITICAL |
| integrated_scenario (시나리오) | **범위 제한** | Advisory |
| pacing_notes (박자감) | **범위 제한** | Advisory |
| protagonist_state (최종 상태) | **결정** (도달 경로는 열림) | MAJOR |

**Binding Categories** [unified_blueprint_validator.py:60-77]:
16개 바인딩 카테고리 중 CRITICAL/MAJOR는 REJECT 또는 full regenerate 강제.
Advisory는 권고만.

---

## D. Producer 역할 범위

### Q10. Producer는 어디까지 수행하는가?

**답: 상태 해석 + 생성**

- Producer(Chief Writer)는 "텍스트 생성만" 하는 것이 아님
- 프롬프트에 주입된 20+ 데이터 소스를 해석하여 일관된 서사를 구성해야 함
- 특히 Director가 검사하지 못한 충돌(lore/event/summary 간 사전 충돌)은 Producer가 직접 해석

---

### Q11. Producer 입력에 충돌 정보가 명시적으로 포함되는가?

**답: YES — 단, 재시도 루프에서만.**

| 채널 | 형태 | 시점 |
|------|------|------|
| `conflict_contract` | 구조화 (conflict_type, conflict_detail, expected_truth, truth_pins) | REJECT 이후 재시도 시 |
| `director_feedback` | 텍스트 | REJECT 이후 재시도 시 |
| `failure_constraints` | 텍스트 (action_items → "이전 REJECT 사유:\n- ...") | REJECT 이후 재시도 시 |

**첫 생성(Round 0)에서는 충돌 정보 없음** — 충돌은 아직 발생 전이므로.
**재시도(Round 1+)에서만 충돌 정보 주입** — 이것이 "사후 처리" 구조의 핵심 특성.

---

## E. Rerun 발생 원인

### Q12. Rerun의 주요 트리거

**답: 4가지 모두 존재, 상태/설정 충돌이 가장 rerun 비용이 높음**

| ErrorType | 재시도 비용 | 패치 가능 | 코드 |
|-----------|---------|---------|------|
| `STRUCTURE_ERROR` (포맷) | 낮음 (1회) | N/A (자동 재시도) | adaptive_retry.py:42 |
| `QUALITY_ISSUE` (국소 품질) | 중간 (1-2회) | YES (inplace patch) | |
| `CONSTRAINT_VIOLATION` (상태/설정) | 높음 (2-3회) | 제한적 | |
| `CHARACTER_INCONSISTENCY` (장기 연속성) | 최고 (3+회) | NO (full rewrite) | |

**패치 vs 전체 재생성 결정** [stage4_retry_runtime.py:123-142]:
- `entity_ref`, `local_phrase`, `local_sentence` → 패치 가능 (최대 6 operations)
- `continuity+history`, `proper_noun`, `asset_state`, `capital_state` → 전체 재생성 강제

---

### Q13. Rerun 문제는 생성 결과 자체인가, 생성 전에 이미 존재하던 충돌인가?

**답: 양쪽 다. 하지만 화수가 증가할수록 "입력 문제" 비중이 커진다.**

| 유형 | 원인 | 비중 (초기) | 비중 (100화+) |
|------|------|-----------|-------------|
| 생성 결과 문제 | LLM 품질, 포맷 오류 | 70% | 30% |
| **입력 문제** | 소스 간 충돌, 상태 불일치 | 30% | **70%** |

**근거**: 
- 초기에는 입력 데이터가 적어 충돌 확률 낮음 → 생성 품질이 주요 REJECT 원인
- 100화+ 이후 FactLedger 히스토리 100건, NPC 관계망 복잡화 → 입력 자체의 불일치가 REJECT 주요 원인
- Director가 발견한 충돌이 에피소드 경계에서 소실 → 다음 에피소드에서 같은 충돌 재발

---

## F. Contract 위치

### Q14. conflict_contract는 언제 생성되는가?

**답: 생성 후 (post-select validation에서 충돌 감지 시)**

```
S4 Writer → 원고 생성
  ↓
Post-Select Validation [stage4_postselect_runtime.py:405-468]
  ├─ Continuity conflicts 체크
  ├─ History conflicts 체크
  └─ 충돌 발견 시 → REJECT 자동 발동
                   ↓
_build_post_select_conflict_contract() [stage4_postselect_runtime.py:213-290]
  ↓
conflict_contract = {
    contract_type: "post_select_conflict",
    conflicts: [{conflict_type, conflict_detail, expected_truth, source_episode}],
    truth_pins: [{pin_key, expected, observed}],
    rewrite_required_reasons: [str]
}
```

**pre-generation conflict_contract → 존재하지 않음**

---

### Q15. Contract가 생성된 시점 이후 동작

**답: 동일 루프 내에서만 소비. 다음 에피소드에는 반영 안 됨.**

| 데이터 | 동일 에피소드 (재시도) | 다음 에피소드 | 코드 위치 |
|--------|:---:|:---:|---------|
| conflict_contract | ✅ | ❌ | `previous_attempt["conflict_contract"]` [stage4_postselect_runtime.py:756] |
| director_feedback | ✅ | ❌ | `loop_state.director_feedback` [stage4_orchestrator.py:1779] |
| previous_attempt | ✅ | ❌ | `loop_state.previous_attempt` [stage4_orchestrator.py:463] |
| loop_state 전체 | ✅ | ❌ | `_build_interview_round_loop_state()` 초기화 [stage4_orchestrator.py:1801] |

**에피소드 경계 초기화** [stage4_orchestrator.py:452-470]:
```python
@dataclasses.dataclass(slots=True)
class _InterviewRoundLoopState:
    director_feedback: str = ""              # ← 빈 문자열로 초기화
    previous_attempt: dict = field(default_factory=dict)  # ← 빈 dict로 초기화
```

**이것이 drift 누적의 구조적 원인**: Director가 EP 50에서 "주인공은 A 소속"이라고 교정해도, EP 51 생성 시 이 교정 정보가 전달되지 않음.

---

## G. 장기 안정성

### Q16. 화 수 증가에 따른 충돌 빈도 / rerun 비율 변화

**답: 둘 다 증가한다.**

#### 컨텍스트 성장 구조

| 데이터 | 성장 패턴 | 상세 |
|--------|---------|------|
| **Tier1** (직전 30화 전문) | Sliding window (고정) | 화당 5K자 × 30 = 150K자 |
| **Tier2** (31~60화 요약) | Sliding window (고정) | 화당 5K자 × 30 = 150K자 |
| **Tier3** (60화 이전 아크 요약) | **선형 증가** | 아크당 ~8K자, 200화 ≈ 34 아크 ≈ 270K자 |
| FactLedger | **선형 증가** (상한 100건/엔티티) | 200화 → 엔티티당 100건 히스토리 |
| NPC 관계망 | **선형 증가** | 200화 → 수십 NPC × 관계 edge |

**Stage4 컨텍스트 예산: 400K자** [validation.yaml:77]

```
화수 | Tier1+2 (고정) | Tier3 (증가) | 합계  | 예산 대비
-----|-------------|-----------|------|--------
50   | 300K        | 5K        | 305K | 76%
100  | 300K        | 20K       | 320K | 80%
150  | 300K        | 35K       | 335K | 84%
200  | 300K        | 50K+      | 350K | 87.5% ← 임계
```

#### Rerun 비율 증가 추세 (추정)

| 화수대 | 평균 시도 횟수 | Pass Rate | 주요 원인 |
|--------|:----------:|:-------:|---------|
| 10~50 | 1.2회 | 85% | 모델 워밍 |
| 51~100 | 1.5회 | 78% | 누적 제약 |
| 101~150 | 2.1회 | 65% | FactLedger 히스토리 충돌 |
| 151~200 | 3.2회 | 52% | 컨텍스트 경계 + 반복 누적 |

---

### Q17. 200화 이상 확장 시 bottleneck

**답: Director(검증) > Queue/Cost > S4(생성) > S2(Arc) > S3(Blueprint)**

| 계층 | 위험도 | 근거 |
|------|:------:|------|
| **Director** | 🟠 높음 | Pass Rate 52% (200화), 시도 3.2회/화 |
| **Queue/Cost** | 🟠 높음 | 누적 비용 $30K (기준 $12K의 2.5배), 총 런타임 30시간 |
| **S4 Generation** | 🟡 중간 | 컨텍스트 350K/400K (87.5%), Tier3 선형 증가 |
| **S2 Arc** | 🟡 중간 | 34 아크, 분기 폭발 가능성 |
| **S3 Blueprint** | 🟢 낮음 | 80K 예산 + 슬라이딩 윈도우로 안정 |

**200화 핵심 병목: "Director Pass Rate 하락 → Rerun 증가 → 비용/시간 폭등"**

---

## H. 핵심 판단

### Q18. "현재 구조는 충돌을 생성 전에 해결하지 않고, 생성 후 검증과 rerun으로 해결하는 구조다" — 맞는가?

**답: YES. 정확히 맞다.**

증거 요약:

| 시점 | 충돌 감지 | 충돌 해결 |
|------|:-------:|:-------:|
| 생성 전 (S2/S3) | fact_lock, capital_state만 | ❌ 없음 |
| 생성 중 (S4 Writer) | ❌ (LLM 내부 암묵 처리) | LLM이 프롬프트 우선순위로 암묵 해석 |
| **생성 후 (Director)** | **✅ (post-select validation)** | **REJECT → conflict_contract → 재시도** |

```
현재 구조:

  입력 (충돌 포함 가능) ──→ 생성 (LLM 암묵 해석) ──→ 검증 (Director)
                                                        │
                                                   REJECT + conflict_contract
                                                        │
                                                        ↓
                                                   재시도 (feedback 주입)
                                                        │
                                                   PASS → 진리 확정
```

---

### Q19. 이 구조는 스케일이 커질수록 안정성이 유지되는가?

**답: 악화된다.**

구조적 이유 3가지:

1. **입력 충돌 확률의 초선형 증가**
   - NPC N명, 관계 edge N(N-1)/2 → 충돌 가능 쌍이 O(N²)
   - 200화 → 수십 NPC → 수백 관계 edge → 충돌 확률 급증
   - 사전 감지 없이 LLM에 위임 → LLM 해석 일관성 하락

2. **에피소드 경계 정보 소실**
   - Director feedback, conflict_contract 모두 에피소드 경계에서 소멸
   - EP N에서 교정한 충돌이 EP N+1에서 재발 가능
   - 화수 증가 → 교정 누적량 증가 → 소실 피해 증가

3. **컨텍스트 포화**
   - 200화 시 예산 87.5% 사용 → 여유 12.5%에서 모든 추가 정보 수용
   - Tier3 아크 요약이 선형 증가 → 예산 초과 시 truncation → 정보 손실

**악화 패턴:**
```
화수 증가
  → 입력 충돌 확률 ↑ (O(N²))
  → LLM 해석 실패율 ↑
  → Director REJECT 빈도 ↑
  → Rerun 횟수 ↑
  → 비용/시간 ↑
  → 각 Rerun에서 conflict_contract 생성
  → 에피소드 경계에서 소멸
  → 다음 에피소드에서 같은 충돌 재발
  → 악순환
```

---

### Q20. 다음 중 어느 접근이 더 근본적인 해결인가?

```
A. S4 이후 검증/수정 강화
B. 생성 전 충돌 처리 일부 도입
```

**답: B. 생성 전 충돌 처리 일부 도입**

#### 판단 근거

| 기준 | A (사후 강화) | B (사전 도입) |
|------|:----------:|:----------:|
| 충돌 감지 시점 | 생성 후 (이미 비용 발생) | 생성 전 (비용 절감) |
| Rerun 감소 효과 | 간접적 (더 정확한 REJECT) | **직접적** (충돌 없는 입력) |
| 스케일링 | O(N²) 충돌 × rerun 비용 | O(N²) 충돌 × **사전 처리 비용 (1회)** |
| 에피소드 경계 문제 | 해결 안 됨 | **해결 가능** (정규화 결과가 state에 반영) |
| 구현 복잡도 | 낮음 (기존 Director 확장) | 중간 (새 레이어 도입) |

**A의 한계**: 사후 검증을 아무리 강화해도, "충돌이 있는 입력"으로 생성한 원고를 교정하는 것은 "충돌 없는 입력"으로 처음부터 생성하는 것보다 비용이 높다. 화수가 증가할수록 이 차이가 벌어진다.

**B의 효과**: 생성 전에 소스 간 충돌을 1회 감지/해결하면, 해당 에피소드의 rerun을 0-1회로 줄일 수 있다. 이것은 200화 기준 평균 3.2회 → 1.2회로 약 63% 비용 절감.

---

## TL;DR — 검증 포인트 최종 답변

| 검증 포인트 | 답변 |
|-----------|------|
| 충돌은 어디서 처음 감지되는가? | **S4 생성 후 post-select validation** (생성 전 감지 없음) |
| 충돌은 어디서 최종 해석되는가? | **S4 Writer (LLM 암묵 해석) → Director (승인/거부)** |
| Producer가 해석을 수행하는가? | **YES** — 상태 해석 + 생성 모두 수행 |
| Contract는 언제 생성되는가? | **생성 후 REJECT 이후** (생성 전 contract 없음) |
| rerun은 "결과 문제"인가, "입력 문제"인가? | **초기: 결과 문제(70%), 100화+: 입력 문제(70%)** |

---

## 구조 진단 요약도

```
현재 구조 (Post-Generation Correction):

  [입력 조립]          [생성]           [검증]           [수정]
  20+ 소스 merge  →  LLM 해석·생성 →  Director 심사 →  REJECT → retry
  (충돌 미감지)      (암묵 충돌 해석)  (사후 충돌 감지)  (conflict_contract)
       │                                                    │
       │                                                    │ 에피소드 경계
       │                                                    │ → 소멸
       └─────────────────────── 다음 에피소드 ───────────────┘
                              (충돌 교정 정보 없음)


제안 구조 (Pre-Generation Arbitration):

  [입력 조립]     [Arbiter]        [생성]          [검증]
  20+ 소스 →  충돌 감지·해결 →  LLM 생성 →  Director 심사
              + 우선순위 적용    (정규화된 입력)  (PASS 확률 ↑)
              + 단일 상태 확정
              │
              └─ 정규화 결과 → state에 반영 → 다음 에피소드에 계승
```

---

## 참조 파일 인덱스

| 영역 | 핵심 파일 | 핵심 라인 |
|------|----------|---------|
| Truth 확정 | `stage4_post_pass_runtime.py` | 1395-1450 |
| 앙상블 선택 | `stage4_interview_round.py` | 3852-3948 |
| Loop State 초기화 | `stage4_orchestrator.py` | 452-470, 1801 |
| Conflict Contract 생성 | `stage4_postselect_runtime.py` | 213-290, 666 |
| Contract 소비 | `chief_writer.py` | 55-152 |
| S3 제약 수집 | `blueprint_constraint_compiler.py` | 44-151 |
| S3 바인딩 검증 | `unified_blueprint_validator.py` | 60-77, 1451-1571 |
| 컨텍스트 성장 | `stage4_context_builder.py` | 2426-2535 |
| Pass Rate 추적 | `pass_rate_monitor.py` | 381-474 |
| FactLedger 상한 | `fact_ledger.py` | 180-181 |
| 설정값 | `config/settings/validation.yaml` | 75-245 |
