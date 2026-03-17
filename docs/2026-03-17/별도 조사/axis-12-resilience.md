# 축 12: 잘 흐르고 (Resilience)

Date: 2026-03-17
Bundle: B (아키텍처 효율)
3-Pass Audit: 89% → 94% → 96%
Final Confidence: 96%

## 1. 핵심 질문

파이프라인이 실패 시 유연하게 대응하는가, 아니면 경직된 컨베이어벨트인가?

---

## 2. 현황 인벤토리

### 2.1 의도적 구현

| # | 파일/모듈 | 능력 | 상세 |
|---|----------|------|------|
| 1 | `adaptive_retry.py` `AdaptiveRetryStrategy` | 에러 타입별 재시도 전략 | 8개 ErrorType × 개별 전략 (temperature 조정, 제약 주입, 스키마 강제 등). 타입별 max_retries (1~3회). CONSTRAINT_VIOLATION: temp -0.1 + 금지 항목 주입. QUALITY_ISSUE: temp +0.1. STRUCTURE_ERROR: temp -0.2 + 스키마 강제 |
| 2 | `adaptive_retry.py` `AdaptiveRetryManager` (V54.3) | 실패 패턴 학습 + 필살기 권장 | 에이전트별 실패 통계, 연속 실패 에스컬레이션(3단계), FailureLearner 연동. `should_trigger_ultimate()` → ToT/ASP/MAD 권장 |
| 3 | `stage4_orchestrator.py` (L952) | 라운드 루프 | `retry.director_max_attempts` 설정 기반 최대 라운드(기본 5). PASS/PASS_WITH_FIX 시 즉시 탈출. REJECT 시 피드백과 함께 재시도 |
| 4 | `stage4_interview_round.py` `_set_retry_budget_axes()` | 재시도 예산 축 | 5축 예산 관리: round(initial/retry_N), repair(inplace/partial/full), strategy, escalation(none/tot/mad), guidance(baseline/augmented) |
| 5 | `stage4_interview_round.py` `_build_retry_feedback_provenance()` | 재시도 피드백 구조화 | system_feedback + evidence_summary + director_feedback + 이전 지시 + runtime_advisory를 계층적으로 병합 |
| 6 | `director_ensemble.py` `_log_director_frame()` | 판정 3-state | PASS / PASS_WITH_FIX / REJECT 3단계 verdict. fix_scope: inplace(국소수정) / partial(일부씬재작성) / full(전면재설계) |
| 7 | `stage4_interview_round.py` PASS_WITH_FIX 계약 | 로컬 수리 | PASS_WITH_FIX verdict → inplace fix_scope로 제한 → 국소 수정만 허용. non-local fix_scope면 REJECT으로 다운그레이드 |
| 8 | `failure_learning.py` `FailureLearner` | 실패 패턴 수집 | 13개 FailureCategory, 최대 500 레코드, `generate_constraint_prompt()` — 학습된 제약을 프롬프트에 주입 |
| 9 | `dynamic_prompt_weighting.py` | 실패 기반 프롬프트 강화 | 10개 PromptCategory, 최근 50건 실패 분석 → 가중 지시문(CRITICAL/HIGH/MEDIUM) |
| 10 | `pass_rate_monitor.py` | 성공률 추적 + 알림 | 25-field AttemptRecord, stage별 통계, trend 분석, 15%+ 하락 시 alert |
| 11 | `soft_failure.py` | 비차단 오류 보고 | 구조화된 JSONL 로깅 + 60초 스로틀링. component별 비차단 오류 영속화 |
| 12 | `base_agent.py` MODEL_FALLBACK_CHAIN | API 모델 폴백 | 1차 모델 실패 시 backup_model → fallback_chain으로 자동 전환 |
| 13 | `models/blueprint.py`, `arc.py`, `manuscript.py` | Graceful degradation | 검증 실패 시 원본 dict 그대로 반환 (데이터 손실 방지) |
| 14 | `stage4_orchestrator.py` 수렴/정체 감지 | 반복 패턴 감지 | `_prev_reject_bucket` + `_bucket_streak`: 동일 reject_bucket 연속 감지. `_prev_dominant_contradiction` + `_contradiction_type_streak`: 모순 유형 수렴 추적. `_score_history` + `_plateau_advisory_emitted`: 점수 정체 감지 |
| 15 | `adversarial_self_play.py` | ASP 필살기 | 2라운드 자기 대전 수정. max_rounds=2. 마지막 수단으로 사용 |
| 16 | `constants.py` `MAX_RETRY_PER_EPISODE = 10` | 하드 리밋 | 에피소드당 절대 최대 재시도 횟수 [TF-23b] |

### 2.2 부수적 기여

| # | 파일/모듈 | 부수적 기여 |
|---|----------|----------|
| 1 | `validation_orchestrator.py` `_UNCONDITIONAL_PASS_FLOOR = 85` | 85점 이상이면 무조건 PASS — 불필요한 재시도 방지 |
| 2 | `validation_orchestrator.py` 적응형 임계값 | 연속 실패 시 임계값 상향(+3~+5) — 더 엄격해지며, 이는 의도적으로 "포기하라"는 신호가 아니라 "더 잘 써라"는 신호 |
| 3 | `api/process_runner.py` graceful terminate | 프로세스 종료 시 graceful → 5초 대기 → force kill |

---

## 3. 갭 식별

### G12-1: 2등 후보 승격 경로 완전 부재

**유형**: 완전 부재

**증거**:

- `director_ensemble.py`에서 앙상블 선택 시 `selected_index`만 반환한다. 나머지 2후보는 **즉시 폐기**된다.
- 1등 후보가 REJECT되면 **동일 조건으로 3후보를 다시 생성**한다 (stage4_orchestrator.py L957~967 루프).
- 이전 라운드의 2등/3등 후보를 다음 라운드에서 재활용하거나, 1등이 REJECT된 경우 2등을 시도해보는 경로가 없다.
- `comparison_notes`만 240자로 기록되고, 후보 원고 자체는 영속화되지 않는다 (단, `snapshot_logged_artifact()`로 아티팩트 경로는 기록될 수 있음).

**갭의 구체적 비용**: 후보 A가 "모순 1건"으로 REJECT되고 후보 B가 "모순 0건 but 밀도 부족"이었을 때, A를 inplace로 수정하는 것보다 B를 밀도 보강하는 것이 더 쉬울 수 있지만, 이 판단 경로가 없다.

### G12-2: 부분 재생성 (씬 단위) 불가

**유형**: 완전 부재

**증거**:

- REJECT 시 재시도는 **원고 전체를 다시 생성**한다. 특정 씬만 재생성하는 경로가 없다.
- `fix_scope`가 "inplace"/"partial"/"full"로 분류되지만, 실제 실행은:
  - `inplace`: CW에게 "이 부분만 고쳐라"는 프롬프트와 함께 **전체 원고 재생성** 요청 (patch_mode).
  - `partial`: "일부 씬 재작성"이라는 의미지만, 실행은 역시 전체 재생성.
  - `full`: 전면 재생성.
- Blueprint의 `scene_breakdown`이 씬 단위로 구조화되어 있어 이론적으로 씬 단위 재생성이 가능하지만, 이를 활용하는 코드 경로가 없다.

### G12-3: 상류 재설계(Stage 3/2) 자동 트리거 부재

**유형**: 완전 부재

**증거**:

- Stage 4에서 `_max_rounds`(기본 5) 모두 REJECT되면, 파이프라인은 **해당 에피소드를 실패로 기록**하고 다음 에피소드로 넘어간다.
- "Blueprint 자체가 문제여서 아무리 원고를 재생성해도 안 된다"는 판단 → Stage 3 재실행 자동 트리거가 없다.
- "Arc 설계가 문제여서 Blueprint도 원고도 안 된다"는 판단 → Stage 2 재실행 자동 트리거가 없다.
- `stage4_orchestrator.py`의 `_blueprint_regenerated` 플래그가 있지만 (L942), 이는 Stage 4 **내에서** Blueprint를 다시 읽는 것이지 Stage 3를 재실행하는 것이 아니다.
- 수동 운영에서는 사용자가 개입하여 상류 재설계를 할 수 있지만, 시스템이 "이건 상류 문제다"라고 판단하고 자동으로 재설계를 트리거하는 메커니즘이 없다.

### G12-4: 병렬 경로 탐색 (A안 수리 + B안 재생성 동시) 부재

**유형**: 완전 부재

**증거**:

- 재시도는 **순차 단일 경로**로만 진행된다.
- "1등 후보를 inplace 수정하면서 동시에 새 3후보를 생성"하는 병렬 경로가 없다.
- CW 앙상블 생성 자체는 ThreadPoolExecutor로 **병렬** (3후보 동시 생성)이지만, 재시도 라운드는 직렬이다.
- 비용 이슈: 병렬 경로는 LLM 호출이 2배가 되므로, 비용-품질 트레이드오프 판단이 필요하다.

### G12-5: Graceful degradation 전략 부재

**유형**: 부분 구현

**증거**:

- `models/blueprint.py`, `arc.py`, `manuscript.py`에서 데이터 모델 수준의 graceful degradation은 존재 (검증 실패 → 원본 dict 반환).
- `base_agent.py`의 MODEL_FALLBACK_CHAIN으로 API 모델 폴백은 존재.
- 그러나 **시스템 수준**의 graceful degradation이 없다:
  - API quota 소진 시 → 단순 대기 후 재시도(WAIT_TIME_BY_TYPE[QUOTA_EXCEEDED] = 30초). "quota가 부족하니 검증 단계를 줄이자"는 전략이 없다.
  - context budget 초과 시 → 큰 섹션부터 절삭. "context가 너무 크니 검증기 일부를 생략하자"는 전략이 없다.
  - 연속 실패 시 → 임계값 상향(더 엄격해짐). 이는 "포기"가 아니라 "더 잘 써라"이므로, 실패 심화를 초래할 수 있다. "5회 연속 실패면 임계값을 낮추고 경고와 함께 PASS"하는 safety valve가 없다.

### G12-6: 천장 감지 — 같은 조건으로 반복해도 개선 안 될 때 인지

**유형**: 부분 구현

**증거**:

- `stage4_orchestrator.py`의 `_score_history` + `_plateau_advisory_emitted`가 점수 정체를 감지한다.
- `_prev_reject_bucket` + `_bucket_streak`가 동일 reject 유형 반복을 감지한다.
- `_prev_dominant_contradiction` + `_contradiction_type_streak`가 같은 모순 유형 반복을 감지한다.
- **그러나**: 감지 후 대응이 **advisory 발행 + 로깅**에 그친다. "천장에 도달했으니 상류를 재설계하라" 또는 "이 에피소드는 포기하고 다음으로 넘어가라"는 적극적 대응이 없다.
- `should_trigger_ultimate()`이 필살기(ToT/ASP/MAD)를 권장하지만, 이것은 "같은 Stage 4에서 더 비싼 기법을 쓰자"이지 "문제가 Stage 3에 있으니 거기로 돌아가자"는 판단이 아니다.

### G12-7: 에러 복구 — API 실패, 타임아웃, OOM 시 복구 경로

**유형**: 부분 구현

**증거**:

- `AdaptiveRetryStrategy.WAIT_TIME_BY_TYPE`이 에러 타입별 대기 시간을 정의 (TIMEOUT: 2초, QUOTA_EXCEEDED: 30초).
- `base_agent.py`의 MODEL_FALLBACK_CHAIN이 모델 레벨 폴백을 처리.
- `soft_failure.py`가 비차단 오류를 구조화 로깅.
- **그러나**: OOM 복구, 네트워크 단절 복구, 부분 응답 복구 등의 시스템 레벨 복구는 Python 표준 예외 처리에 의존한다. 전용 circuit breaker나 retry-with-jitter 패턴은 없다.

---

## 4. 영향도 추정

| 갭 ID | 갭 | 직접 영향 | 간접 영향 | 등급 |
|-------|------|---------|---------|------|
| G12-1 | 2등 후보 승격 부재 | REJECT 후 3후보 재생성 비용 (기존 후보 낭비) | 동일 조건 재시도 → 유사 결과 반복 가능 | **significant** |
| G12-2 | 부분 재생성 불가 | 한 씬의 문제로 5,000자 전체 재생성 → 비용 + 레이턴시 | 좋은 부분이 재생성에서 사라질 수 있음 | **significant** |
| G12-3 | 상류 자동 재설계 부재 | Blueprint 문제 시 Stage 4에서 몇 번이든 실패 → 비용 낭비 | 장기 연재에서 특정 에피소드 영구 실패 위험 | **critical** |
| G12-4 | 병렬 경로 탐색 부재 | 재시도 시간 = N × 단일 라운드 시간 (직렬) | 긴급 생산 시 시간 압박 | **nice-to-have** |
| G12-5 | Graceful degradation 부재 | 자원 부족 시 전체 파이프라인 정지 | 운영 안정성 저하, 야간 배치 실패 위험 | **significant** |
| G12-6 | 천장 감지 후 적극적 대응 부재 | 감지는 하지만 대응 없음 → 비용 낭비 지속 | 사용자가 수동 개입해야 함 → 운영 부담 | **significant** |
| G12-7 | 시스템 에러 복구 한계 | API 실패 시 단순 재시도만 → 복구 실패 시 전체 중단 | 야간 무인 운영 신뢰도 저하 | **nice-to-have** |

---

## 5. 방향 스케치

| # | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|---|--------|--------|-------------|----------------|-------------|
| 1 | **2등 후보 보관 + 승격 경로** — Director 선택 시 1등이 REJECT되면 2등을 자동 평가. 후보 원고를 라운드 간 보존. | 중 | 1회 추가 (2등 평가) | `director_ensemble.py` 확장, 아티팩트 캐싱 | 메모리 사용 증가 (원고 3개 보존) |
| 2 | **씬 단위 재생성** — REJECT 피드백에서 문제 씬을 특정 → 해당 씬만 재생성 → 원본에 병합. | 대 | 추가 (씬 생성 + 병합 검증) | `scene_breakdown` 구조 활용 | 씬 경계 연결 품질 저하 위험, 구현 복잡도 높음 |
| 3 | **상류 재설계 자동 트리거** — Stage 4에서 N회 연속 실패 + 동일 모순 유형 반복 시 → Stage 3 Blueprint 재생성 자동 트리거. | 중 | Stage 3 재실행 비용 | `_contradiction_type_streak` 기반 트리거 조건 | Stage 3 재실행 비용 + 루프 무한 반복 위험 → 반드시 재설계 상한 설정 필요 |
| 4 | **안전 밸브(Safety Valve)** — N회 연속 실패 시 임계값을 임시로 낮추고 경고 태그와 함께 PASS. 사후 인간 리뷰 큐에 등록. | 소 | 불필요 | `ValidationOrchestrator` 적응형 임계값 확장 | "낮은 품질 원고가 통과"할 위험 → 반드시 리뷰 큐 연동 |
| 5 | **비용 기반 전략 선택** — 재시도 시 이전 시도 비용 누적을 추적하고, 누적 비용이 임계값을 넘으면 경로 변경 (전략 변경, 상류 재설계, 또는 포기). | 중 | 불필요 | `_get_round_metrics_delta()` 확장 | 비용 임계값 설정이 주관적 |
| 6 | **Circuit breaker 패턴** — API 연속 실패 시 일정 시간 호출 차단 → 복구 후 자동 재개. | 소 | 불필요 | `AdaptiveRetryStrategy` 확장 | 생산 지연 |
| 7 | **Graceful degradation 모드** — 자원 부족 감지 시 검증 tier를 축소 (예: Advisory + Retrospective 생략, Scoring만 유지). | 중 | 호출 수 감소 | `ValidationOrchestrator` 조건부 tier 생략 | 품질 검증 약화 |

**당장 할 수 있는 것**: #4 (안전 밸브), #6 (circuit breaker)
**설계가 필요한 것**: #1 (2등 승격), #2 (씬 단위), #3 (상류 재설계), #5 (비용 기반), #7 (degradation 모드)

---

## 6. 묶음 내 교차 발견

**축 10(잘 읽고)에서 온 발견**:

- G10-5("무시 vs 미제공" 구분 불가)는 REJECT 후 피드백의 정확성을 떨어뜨린다 → 재시도가 잘못된 방향으로 갈 수 있다. 이는 G12-6(천장 감지)의 근본 원인 중 하나 — "같은 실수를 반복하는 것"인지 "다른 실수를 하는 것"인지 구분이 어렵다.
- G10-3(context 비대)은 장기 연재에서 Stage 4 재시도 비용을 누적적으로 증가시킨다 → G12-5(graceful degradation) 필요성 강화.

**축 11(잘 조율하고)에서 온 발견**:

- G11-5의 Director 단일 게이트 병목은 resilience 관점에서 SPOF다 — Director LLM 호출이 실패하면 `_fallback_first_candidate()`가 작동하지만, 이 폴백 자체가 "Director LLM 미호출 상태의 자동 PASS 금지" 정책(director_ensemble.py:781~787)에 의해 REJECT된다. 즉, Director 불능 = 무조건 REJECT.
- G11-4의 핸드오프 정보 유실은 G12-3(상류 재설계)을 어렵게 만든다 — Stage 4에서 "Blueprint가 문제다"라고 판단해도, Blueprint의 어떤 부분이 문제인지를 Stage 3에 전달할 정보가 구조화되어 있지 않다.
- G11-2의 검증 중복은 G12-1(2등 승격)의 비용을 높인다 — 2등 후보를 재평가하면 9개 검증기를 다시 돌려야 하므로, 검증 통합이 선행되면 2등 승격 비용이 줄어든다.

---

## 7. 3-Pass 감리 기록

### Pass 1: 사실 정확성 (89%)

- **수정**: 초기 draft에서 "REJECT 후 같은 조건으로 재생성"이라고 기술했으나, 실제로는 `_build_retry_feedback_provenance()`가 Director 피드백을 구조화하여 다음 라운드에 주입하므로 "같은 조건"이 아니다. "동일 Stage/구조에서 피드백 반영 재생성"으로 교정.
- **수정**: "patch_mode에서 전체 원고 재생성"이라는 표현이 부정확 → 실제로 patch_mode는 CW에게 원본 원고 + 수정 지침을 함께 전달하여 **교정된 원고를 생성**하도록 한다. 완전한 재생성은 아니지만 LLM이 전체 텍스트를 다시 출력하므로, "전체 출력 재생성"이 맞다. 표현을 명확히.
- **확인**: `MAX_RETRY_PER_EPISODE = 10` (constants.py:230) 확인.
- **확인**: `retry.director_max_attempts` 기본값 5 (stage4_orchestrator.py:952) 확인.
- **확인**: `_UNCONDITIONAL_PASS_FLOOR = 85` (validation_orchestrator.py:174) 확인.
- 확신도: 89% (patch_mode의 정확한 실행 경로는 main_a.py 참조 필요하나, 코드 크기 제약으로 일부 추정)

### Pass 2: 논리 정합성 (94%)

- **검증**: G12-3 → critical 판단 — "Blueprint가 문제인데 원고만 재생성"하는 시나리오는 논리적으로 무한 비용 낭비. 반론: "Stage 4에서 5회면 충분히 다양한 원고를 시도할 수 있다" → 그러나 Blueprint의 구조적 문제(씬 배치, 핵심 사건 누락)는 원고 수준에서 해결 불가. critical 유지.
- **검증**: G12-6 → significant 판단 — 감지 메커니즘이 이미 존재하므로 "완전 부재"보다는 "부분 구현". 대응 부재가 실질적 영향. 등급 적절.
- **수정**: G12-1에서 "후보 원고가 영속화되지 않는다"고 기술했으나, `snapshot_logged_artifact()` (artifact_logging.py)에 의해 아티팩트 경로는 기록될 수 있음. 다만 이것은 **로깅 목적**이지 재활용 인프라가 아님. 표현 교정.
- **추가**: 교차 발견에서 G11-5(Director SPOF)의 구체적 폴백 실패 경로 추가 — `_fallback_first_candidate()`가 Director LLM 미호출 정책에 의해 REJECT되는 것이 핵심.
- 확신도: 94%

### Pass 3: 완성도 (96%)

- **보완**: 인벤토리에 #14 (수렴/정체 감지) 추가 — `_score_history`, `_bucket_streak`, `_contradiction_type_streak`가 G12-6의 "부분 구현" 근거.
- **보완**: 인벤토리에 #15 (ASP 필살기) 추가 — 마지막 수단으로서의 adversarial_self_play.
- **보완**: 방향 스케치 #7 "Graceful degradation 모드" 추가 — G12-5에 대한 구체적 방향이 누락되어 있었음.
- **확인**: 모든 갭-영향도-방향 간 논리 연결 재확인 완료. G12-3이 "당장 할 수 있는 것"이 아닌 "설계가 필요한 것"인 이유 재확인 (Stage 간 역행 경로는 파이프라인 구조 변경 필요).
- 확신도: 96%
