# 축 8: 잘 멈추고 (Stopping)

Date: 2026-03-17
Bundle: A
3-Pass Audit: 87% → 94% → 96%
Final Confidence: 96%

## 1. 핵심 질문

시스템이 "이 정도면 충분하다" 또는 "이건 더 해도 안 된다"를 어떻게 판단하는가?

---

## 2. 현황 인벤토리

### 의도적 구현

| # | 구성요소 | 파일 | 멈춤 메커니즘 | 판단 근거 |
|---|---------|------|-------------|----------|
| S1 | Director 3-state verdict | `director_ensemble.py` | PASS: 즉시 출판 / PASS_WITH_FIX: 로컬 수리 후 출판 / REJECT: 재시도 | 6차원 점수 합산 + 등급(A/B/C/D) 매핑 |
| S2 | Score threshold (장르별) | `validation.yaml` | 장르별 통과 임계값 (68~72) | 정적 설정값 — 런타임 적응 없음 |
| S3 | Max rounds (하드 시링) | `validation.yaml` `retry.director_max_attempts` | 5~10 라운드 상한 | 설정값 도달 시 무조건 중단 |
| S4 | Error-type max retries | `adaptive_retry.py` `MAX_RETRIES_BY_TYPE` | CONSTRAINT_VIOLATION: 3 / QUALITY_ISSUE: 2 / STRUCTURE_ERROR: 2 / TIMEOUT: 1 / QUOTA_EXCEEDED: 3 / UNKNOWN: 2 | 에러 유형별 고정 상한 |
| S5 | Score history tracking | `stage4_orchestrator.py` | 라운드별 점수 리스트 축적 | 3연속 하락 감지 → advisory / 2연속 동점(plateau) 감지 → advisory |
| S6 | Reject bucket streak | `stage4_orchestrator.py` [TF-29] | 같은 reject_bucket 3연속 감지 | "원고 수준 수정으로 해결 불가" 판정 → Blueprint 재검토 advisory |
| S7 | Contradiction type convergence | `stage4_orchestrator.py` [A-4] | 같은 모순 유형 2연속 + LOGIC_ERROR 2연속 | "Writer 문제 아닌 Blueprint/Arc 설계 결함" 진단 |
| S8 | Ambiguous zone voting | `director_auditor.py` | 점수 50~60 구간: self-consistency 3회 투표 | 불확실 영역에서 신뢰도 확보용 다수결 |
| S9 | PASS_WITH_FIX + inplace repair | `stage4_interview_round.py` `_inplace_repair_gate()` | fix_scope="inplace": 단일 LLM 호출 수리 | 변경률 ≤30%, 보존률 ≥70% 계약 |
| S10 | V75-D Blueprint inplace patch | `stage4_orchestrator.py` [V75-D] | LOGIC_ERROR N연속 → Blueprint 부분 수정 | threshold=1(quality_risk) 또는 2(일반) |
| S11 | V75-B Blueprint 재생성 | `stage4_orchestrator.py` [V75-B] | LOGIC_ERROR 2연속 + inplace 실패 + 미재생성 | Stage 3 아키텍트 에이전트 호출 → 새 Blueprint |
| S12 | Quality grade escalation | `director_grading.py` | A(≥85)/B(70-84)/C(50-69)/D(<50) → PUBLISH_READY/MINOR_REVISION/MAJOR_REVISION/REWRITE | 등급별 후속 행동 정의 |
| S13 | Patch mode score bands | `validation.yaml` `patch_mode` | rewrite_below: 50 / inplace_below: 60 | 점수 구간별 수리 전략 선택 |

### 부수적 기여

| # | 구성요소 | 파일 | 부수적 멈춤 효과 |
|---|---------|------|-----------------|
| S14 | Inplace success rate | `stage4_interview_round.py` `_get_inplace_success_rate()` | fix_scope별 성공률 진단 — 경제성 판단 보조, 멈춤 판단에는 미연결 |
| S15 | Retry budget axes | `stage4_interview_round.py` | round/repair/strategy/escalation/guidance 축 기록 — 비용 가시화, 멈춤 트리거에는 미연결 |
| S16 | PassRateMonitor.check_alerts() | `pass_rate_monitor.py` | 통과율 트렌드 모니터링 — 운영자 알림용, 자동 멈춤 미연결 |

---

## 3. 갭 식별

### G8-1: "충분히 좋다" vs "더 나아질 수 있다" 구분 부재 — `critical`

**유형**: 완전 부재

**현황**: 현재 멈춤 판단은 **이진적**: PASS(≥임계값) 또는 REJECT(<임계값). "72점이지만 75점까지 갈 수 있을까?"라는 질문을 시스템이 묻지 않음.

**갭**:
- PASS 판정 시 **즉시 멈춤** — "한 번 더 하면 더 좋아질 수 있다"는 판단 경로 없음
- 72점 PASS와 95점 PASS가 동일한 "출판" 경로로 진행
- Director가 "이 원고는 통과지만 아쉬운 점이 있다"를 표현할 구조가 없음 (PASS_WITH_FIX는 "결함 수정"이지 "추가 개선"이 아님)
- 축 7 교차 발견: 학습 효과 측정 부재(G7-5)로 인해, "더 시도하면 나아지는지"의 근거 데이터 자체가 없음

**영향 경로**: PASS 임계값을 겨우 넘긴 원고가 "충분히 좋다"로 확정됨. 임계값 부근의 원고 품질 편차가 시스템적으로 관리되지 않음.

---

### G8-2: 수렴 판단의 advisory 수준 한정 — `significant`

**유형**: 부분 구현

**현황**: S5(score_history)가 3연속 하락과 plateau를 감지하여 **advisory 텍스트를 생성**함. 그러나 이 advisory가 **행동을 바꾸지 않음**.

**갭**:
- Plateau/decline advisory가 Director 프롬프트에 텍스트로 주입되지만, **자동 에스컬레이션 트리거가 아님**
- "3연속 하락인데 max_rounds가 남았으니 계속 시도" — advisory가 무시될 수 있는 구조
- 점수 추이가 "상승 → 정체 → 하락"의 전형적 수렴 곡선을 보이는지 패턴 인식 없음
- S6(bucket streak)과 S7(contradiction convergence)만이 **실제 행동 변화(Blueprint 재설계)**를 트리거 — 이들은 "특정 실패 반복"에만 반응하고 "일반적 수렴"에는 무반응

**증거 경로**: `stage4_orchestrator.py`에서 `_plateau_advisory`가 텍스트 변수로만 존재하며, 루프 탈출(break)이나 에스컬레이션 호출로 이어지지 않음

---

### G8-3: 상류 재설계 자동 트리거의 제한적 조건 — `significant`

**유형**: 부분 구현

**현황**: V75-D와 V75-B가 LOGIC_ERROR 연속 시 Blueprint 재설계를 트리거함. 이는 진전.

**갭**:
- **LOGIC_ERROR만 에스컬레이션 트리거** — QUALITY_ISSUE, PACING_ISSUE 등 다른 실패 유형은 max_rounds까지 같은 조건으로 반복
- reject_bucket streak(S6)은 advisory만 생성하고 자동 재설계를 트리거하지 않음
- Arc 재설계(Stage 2로의 역행)는 **완전 수동** — Stage 3 Blueprint 재설계까지만 자동
- "Blueprint가 아니라 Arc 자체가 문제"인 경우의 자동 감지/에스컬레이션 경로 없음
- V75-B에서 `_blueprint_regenerated = True` 이후 **재재생성 불가** — 한 번만 시도

**증거 경로**: V75-D/V75-B 조건문에서 `_logic_error_streak` 체크만 존재; `_quality_issue_streak`이나 `_pacing_issue_streak` 변수 부재; `_blueprint_regenerated` 플래그가 재설정되지 않음

---

### G8-4: 비용 대비 품질 한계효용 미인식 — `significant`

**유형**: 형식적 존재

**현황**: S14(inplace success rate)와 S15(retry budget axes)가 비용 데이터를 수집하지만, **멈춤 판단에 연결되지 않음**.

**갭**:
- "이미 $0.50 썼는데 1점 올리려고 $0.20 더 쓸 가치가 있나?"라는 판단을 시스템이 하지 않음
- `_get_round_metrics_delta()`가 라운드별 비용을 추적하지만, 이를 멈춤 조건으로 사용하는 코드 없음
- max_rounds(5~10)가 유일한 비용 상한 — 점수 72에서 73으로 올리기 위해 10라운드 소진 가능
- 축 7 교차 발견: Strategy Win Rate가 전략별 성공률을 알지만, 전략별 **비용 대비 성공률**은 모름

**증거 경로**: `_get_round_metrics_delta()` 반환값이 로깅에만 사용; retry 루프 내 비용 기반 break 조건 없음

---

### G8-5: "천장 감지" 후 행동의 제한성 — `nice-to-have`

**유형**: 부분 구현

**현황**: S6(bucket streak 3+)과 S7(contradiction type 2+)이 "천장"을 감지. V75-D/V75-B가 Blueprint 레벨 대응을 제공.

**갭**:
- 천장 감지 → Blueprint 재설계가 **유일한 대안** — 병렬 경로(2등 후보 승격, 전혀 다른 전략 시도) 미제공
- Blueprint 재설계가 1회로 제한(S11 `_blueprint_regenerated` 플래그)되어, 재설계된 Blueprint도 실패하면 더 이상의 대안 없음
- "이 Arc 구조에서는 이 문제가 해결 불가능"이라는 근본 진단에 도달하는 명시적 경로 없음

---

### G8-6: 적응형 임계값의 미구현 — `nice-to-have`

**유형**: 완전 부재

**현황**: 장르별 임계값(S2)은 **정적 YAML 설정**. 런타임에서 에피소드 맥락(Arc 위치, 전환 에피소드 여부 등)에 따라 임계값을 조정하는 로직이 validation_orchestrator에 있으나, 이는 멈춤이 아닌 **채점**에만 영향.

**갭**:
- "전환 에피소드니까 임계값 -3"은 채점 시 적용되지만, Director의 PASS/REJECT 판단에 같은 적응이 적용되는지 불분명
- "클라이맥스 에피소드니까 더 높은 기준을 적용"과 같은 동적 멈춤 기준 부재
- 운영자가 "이번 에피소드는 특히 중요하니 85점 이상만 통과시켜"와 같이 에피소드별 기준을 주입하는 경로 없음

---

## 4. 영향도 추정

| 갭 ID | 갭 명칭 | 직접 영향 | 간접 영향 | 등급 |
|-------|---------|----------|----------|------|
| G8-1 | "충분히 좋다" 판단 부재 | **시스템 천장**: 임계값 부근(72~75) 원고가 개선 가능성 탐색 없이 출판됨. 장기적으로 "겨우 통과" 수준에 품질 천장 형성 | 독자 만족도 편차 확대 | `critical` |
| G8-2 | 수렴 advisory 한정 | 수렴 감지가 행동으로 이어지지 않아 max_rounds까지 무의미한 재시도 발생. 비용 낭비 + 시간 낭비 | 운영자가 수동 개입해야 하는 빈도 증가 | `significant` |
| G8-3 | 상류 재설계 조건 제한 | LOGIC_ERROR 외 유형의 구조적 문제가 max_rounds까지 같은 수준에서 반복. Arc 레벨 문제 미해결 | 전체 파이프라인 처리량(throughput) 저하 | `significant` |
| G8-4 | 비용-품질 한계효용 무시 | 한계 개선(1~2점)을 위해 과도한 비용 투입 가능. 비용 상한이 max_rounds뿐 | 대량 생산 시 비용 예측 불가 | `significant` |
| G8-5 | 천장 후 대안 부재 | Blueprint 재설계 1회 실패 시 출구 없음 — max_rounds 소진까지 반복 | — | `nice-to-have` |
| G8-6 | 적응형 임계값 미구현 | 모든 에피소드에 동일 기준 → 전환 에피소드의 과소 평가, 클라이맥스의 과대 통과 가능 | — | `nice-to-have` |

**시스템 천장 분석**: G8-1이 가장 근본적. 현재 시스템은 **"실패를 멈추는"** 것에는 정교하지만(S5~S7, S10~S11), **"성공의 수준을 높이는"** 방향의 멈춤 판단이 없음. 이는 축 7의 "성공 학습 비대칭"(G7-1)과 동일한 패턴 — 시스템 전체가 **방어적(실패 회피) 모드**에 최적화되어 있고, **공격적(품질 추구) 모드**가 부재.

---

## 5. 방향 스케치

| 갭 ID | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|-------|--------|-------|------------|----------------|-------------|
| G8-1a | **"Stretch round" 메커니즘**: PASS 판정 + 점수 < (임계값+10) 시 1회 추가 시도 허용. 추가 시도 결과가 현재보다 나으면 교체, 아니면 원래 결과 유지 | 소 | 1회/에피소드 | stage4_orchestrator 루프 확장 | 비용 +1 LLM call/marginal PASS; "항상 stretch"로 퇴화 방지 필요 |
| G8-1b | **Director "improvement potential" 신호**: Director verdict에 `improvement_headroom: low/medium/high` 필드 추가. high일 때만 stretch | 소 | 불필요 (기존 Director 호출 내) | director_ensemble 응답 스키마 확장 | Director의 headroom 판단 정확도에 의존 |
| G8-2 | **Advisory → 자동 에스컬레이션 조건화**: plateau advisory 2연속 + 점수 변화 ≤2점 시 자동으로 Blueprint inplace patch 트리거 (현재 LOGIC_ERROR에만 적용되는 V75-D 경로 범용화) | 중 | 불필요 | V75-D 로직 조건 확장 | 과도한 에스컬레이션 방지를 위한 횟수 제한 필요 |
| G8-3 | **다유형 에스컬레이션 맵**: reject_bucket별 에스컬레이션 경로 정의 — QUALITY_ISSUE 3연속 → 프롬프트 전략 변경, PACING_ISSUE 3연속 → Blueprint 구조 변경, etc. | 중 | 불필요 | bucket streak 감지 로직(S6) 확장 | 에스컬레이션 경로 조합 폭발 관리 필요 |
| G8-4 | **비용 ceiling 브레이커**: 누적 비용이 설정 상한(e.g., $1.00/에피소드) 초과 시 현재 최고 점수 결과를 PASS로 강제 확정하거나 운영자 알림 | 소 | 불필요 | retry budget axes + 비용 추적 결합 | "비용 상한 때문에 저품질 통과" 리스크 — 운영자 알림으로 완화 |
| G8-5 | **다경로 천장 탈출**: Blueprint 재설계 실패 시 (1) 2등 후보 승격, (2) 전혀 다른 전략 집합으로 재시도, (3) Arc 축소(씬 수 감소) 중 선택 | 대 | 다수 | 앙상블 인프라 확장 | 복잡도 대폭 증가; 단계적 도입 필요 |
| G8-6 | **에피소드 맥락 기반 동적 임계값**: validation_orchestrator의 adaptive adjustment(+5/-3 등)를 Director 판정에도 적용 | 소 | 불필요 | 기존 adaptive adjustment 로직 | 채점과 판정의 이중 조정 → 예측 어려움 |

**당장 할 수 있는 것**: G8-1a/b, G8-4, G8-6 (소규모 로직 추가)
**설계가 필요한 것**: G8-2, G8-3 (에스컬레이션 정책 설계), G8-5 (아키텍처 변경)

---

## 6. 묶음 내 교차 발견

### 축 7 → 축 8 교차

- **G7-5 → G8-1 연결**: 축 7에서 발견한 "학습 효과 측정 부재"가 축 8의 "충분히 좋다" 판단을 근본적으로 어렵게 만듦. 학습이 행동을 바꾸는지 모르면, "더 시도하면 나아질 것이다"라는 판단의 근거 자체가 부재.
- **G7-1 → G8-1 연결**: "성공에서 배우지 않는" 시스템(G7-1)은 "더 나은 결과를 향해 시도"할 방향 감각이 없음. 방향이 없으면 "더 하라"는 판단은 무작위 재시도일 뿐.
- **공통 패턴 발견 — "방어적 시스템" 편향**: 축 7의 학습도, 축 8의 멈춤도 모두 **"실패를 피하라"**에 최적화. "더 좋아지라"는 공격적 모드가 양 축 모두에서 부재. 이는 시스템 설계의 근본 방향성 문제이며, 축 9(잘 측정하고)의 "좋다의 정의"가 이 편향을 강화하는지 확인 필요.

### → 축 9 전달

- 축 7+8의 "방어적 편향" 패턴이 측정 체계에서도 나타나는지 확인: "좋은 원고"의 정의가 "결함 없는 원고"와 동일시되는지
- G8-4의 비용-품질 트레이드오프는 축 9의 측정 정밀도와 직결: 측정이 1점 단위로 유의미하지 않다면 한계효용 계산 자체가 무의미

---

## 7. 3-Pass 감리 기록

### Pass 1 (사실 정확성) — 87%

- **수정**: S3 `director_max_attempts` 기본값을 validation.yaml에서 확인 — 10으로 설정, 코드 fallback은 5. 문서에 "5~10" 범위로 정정
- **수정**: S8 ambiguous zone을 50~60으로 정정 (초기에 "60~70"으로 오기)
- **수정**: S13 `rewrite_below: 50`, `inplace_below: 60` 확인 — 초기 기술과 일치
- **확인**: V75-D threshold가 quality_risk 시 1, 일반 시 2임을 코드에서 확인
- **확인**: `_blueprint_regenerated` 플래그가 루프 내에서 재설정되지 않음을 확인
- **미해결 → Pass 2**: Director가 adaptive adjustment를 실제로 참조하는 경로 확인 필요

### Pass 2 (논리 정합성) — 94%

- **수정**: G8-1의 "시스템 천장" 주장을 "임계값 부근 원고"로 한정 — 고득점(90+) 원고에는 해당 없음
- **보완**: G8-3에서 "Arc 재설계가 수동"이라는 주장에 Stage 2→4 역행 경로 부재의 코드 근거 추가
- **확인**: G8-2 "advisory가 행동을 바꾸지 않는다"의 근거 — `_plateau_advisory` 변수가 루프 break에 연결되지 않음을 stage4_orchestrator.py에서 확인
- **확인**: G8-4의 비용 데이터 경로가 로깅 전용임을 `_get_round_metrics_delta()` 호출 맥락에서 확인
- **해결**: Director adaptive adjustment는 validation_orchestrator 레벨에서 적용되며, Director 자체의 PASS/REJECT 판단에는 별도 threshold가 사용됨 (분리 확인)

### Pass 3 (완성도) — 96%

- **보완**: 교차 발견 섹션에 "방어적 시스템 편향" 공통 패턴 명시 — 축 7+8의 가장 중요한 합동 발견
- **보완**: 인벤토리에 "부수적 기여" 섹션 추가 (S14~S16)
- **보완**: 방향 스케치에 G8-4(비용 ceiling)의 구체적 접근법 추가
- **확인**: 영향도 등급이 갭의 실질적 영향과 일관됨
- **잔여 불확실성**: G8-6에서 "validation_orchestrator의 adaptive adjustment가 Director에도 전파되는지"에 대한 완전한 추적이 부족 (확신도 96%의 주된 원인)