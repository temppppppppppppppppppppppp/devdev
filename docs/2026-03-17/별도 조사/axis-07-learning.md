# 축 7: 잘 배우고 (Learning)

Date: 2026-03-17
Bundle: A
3-Pass Audit: 88% → 93% → 96%
Final Confidence: 96%

## 1. 핵심 질문

시스템이 생산 경험에서 무엇을 축적하고, 축적된 것이 다음 생산에 어떻게 반영되는가?

---

## 2. 현황 인벤토리

### 의도적 구현

| # | 구성요소 | 파일 | 학습 대상 | 학습 방식 | 소비처 |
|---|---------|------|----------|----------|--------|
| L1 | FailureLearner | `modules/core/failure_learning.py` | REJECT 사유 17개 카테고리 | 정규식 분류 → LearnedConstraint 생성 (빈도 ≥ threshold) | Stage 2 preflight, Stage 4 Director 프롬프트 |
| L2 | DynamicPromptWeighter | `modules/core/dynamic_prompt_weighting.py` | 최근 50개 실패의 키워드 | 키워드→10개 PromptCategory 매핑 → 가중치 정규화 | CW/Director 프롬프트에 urgency 주입 |
| L3 | PassRateMonitor | `modules/core/pass_rate_monitor.py` | 전 스테이지 시도 결과 | AttemptRecord 축적 (reject_reason 포함) → 통계/트렌드 산출 | 대시보드, alert, 패치 유효성 분석 |
| L4 | Strategy Win Rate | `modules/core/db_manager.py` (`get_strategy_win_rates`) | PASS 판정 시 선택된 전략 | director_selections 테이블 lookback=20 쿼리 | ChiefWriter `_load_strategy_bias()`, ArcEnsemble, Stage4InterviewRound |
| L5 | FailureAnalyzer.top_success_patterns | `modules/core/failure_analyzer.py` | 90점 이상 에피소드 | score_breakdown + consistency_checklist + selection_reason 키워드 추출 | FourPhaseArcGenerator (Arc 생성 시 advisory) |
| L6 | episode_production.jsonl | `projects/*/logs/` | 에피소드별 시도 전체 기록 | JSONL append (verdict, score, feedback_provenance 등) | 사후 분석용 (시스템 자동 소비 경로 제한적) |

### 부수적 기여

| # | 구성요소 | 파일 | 부수적 학습 효과 |
|---|---------|------|-----------------|
| L7 | Stage 4 score_history | `modules/core/stage4_orchestrator.py` | 라운드별 점수 추이 추적 (plateau/decline 감지) — 학습이 아닌 즉시 멈춤 판단용 |
| L8 | Retry budget axes | `modules/core/stage4_interview_round.py` | round/repair/strategy/escalation/guidance 축 기록 — 비용 추적용이나 학습에 미활용 |
| L9 | Inplace success rate | `stage4_interview_round.py` `_get_inplace_success_rate()` | fix_scope별 성공률 진단 — 경제성 판단용, 학습 피드백 루프 없음 |

---

## 3. 갭 식별

### G7-1: 성공에서 배우는 메커니즘의 구조적 비대칭 — `significant`

**유형**: 부분 구현

**현황**: L5 `top_success_patterns`가 유일한 성공 학습 경로. 90점 이상 에피소드의 score_breakdown과 키워드를 추출하여 Arc 생성 시 advisory로 표시.

**갭**:
- 성공 학습이 Arc 생성(Stage 2)에만 도달하고, **CW 프롬프트(Stage 4)에는 주입되지 않음**
- 실패 학습은 FailureLearner(17카테고리) + DynamicPromptWeighter(10카테고리) + Strategy Win Rate의 3중 경로로 CW까지 도달하는 반면, 성공 학습은 단일 경로(Arc advisory)
- "왜 잘 됐는지"의 학습 깊이가 "왜 실패했는지"의 1/3 수준
- 성공 키워드 추출이 selection_reason + open_review 필드 의존 — LLM이 자유 텍스트로 쓴 필드라 구조화 정도 낮음

**증거 경로**: `failure_learning.py` (368줄, 17카테고리, 정규식 분류) vs `failure_analyzer.py` `top_success_patterns()` (단일 함수, 키워드 추출만)

---

### G7-2: 장르별/Arc위치별 학습 분화 부재 — `significant`

**유형**: 완전 부재

**현황**: FailureLearner는 stage별(2,3,4)로 실패를 분류하지만, **장르별·Arc위치별 분화가 없음**. `FailureRecord`에 `arc` 필드는 있으나 `genre` 필드가 없고, 학습 제약 생성 시 장르 필터링 미구현.

**갭**:
- 무협(wuxia) 1화에서 빈번한 "경지 인플레이션"과 요리(cooking) 3화에서 빈번한 "레시피 연속성 오류"가 같은 풀에 축적됨
- Arc 초반(설정)과 후반(클라이맥스)의 실패 패턴이 본질적으로 다르나 구분 없이 혼합
- Strategy Win Rate도 lookback=20으로 전체 풀에서 계산 — 장르별 전략 적합도 차이 무시

**증거 경로**: `FailureRecord` 필드 목록에 `genre` 없음; `generate_constraint_prompt(stage)` 시그니처에 장르 파라미터 없음; `get_strategy_win_rates(lookback=20)` 시그니처에 장르 파라미터 없음

---

### G7-3: 낙선 후보의 탈락 사유 학습 미반영 — `significant`

**유형**: 완전 부재

**현황**: 앙상블(Arc/Blueprint/Manuscript)에서 3후보 생성 후 Director가 1개를 선택. 낙선 2후보는 **즉시 폐기되며 탈락 사유가 구조화되지 않음**.

**갭**:
- Director의 `comparison_notes`가 240자로 절삭됨 (explainability 축과 교차) — 탈락 사유의 정보량 부족
- 낙선 후보의 실제 내용(원고 텍스트)이 영속되지 않아 사후 분석 불가
- "A후보가 B후보보다 나은 이유"가 학습 데이터로 변환되지 않음
- 현재 Strategy Win Rate는 "이긴 전략"만 기록 — "진 전략이 왜 졌는지"는 기록하지 않음

**증거 경로**: `blueprint_ensemble.py` — 3후보 생성 후 best 선택, runner-up 미영속; `director_ensemble.py` `comparison_notes` 240자 절삭; `director_selections` 테이블에 `selected_strategy`만 기록, rejected strategies의 reason 없음

---

### G7-4: 학습 데이터 decay 정책의 조잡함 — `nice-to-have`

**유형**: 부분 구현

**현황**:
- FailureLearner: max_records=500, FIFO 축출 (시간 기반 TTL 없음)
- PassRateMonitor: 최근 1000개 스냅샷 저장
- DB: 무한 축적 + lookback 윈도우(20)로 recency 편향

**갭**:
- FIFO는 "오래된 것 = 덜 중요한 것"을 가정하지만, **장르 변경 시 이전 장르의 학습이 새 장르를 오염**시킬 수 있음
- 프로젝트 초기의 높은 실패율이 FIFO로 밀려나면 "시스템이 초기에 어떤 실수를 반복했는지"의 구조적 패턴 소실
- 시간 기반 decay 없이 count 기반만 사용 → 장기 미실행 프로젝트 재개 시 stale 데이터 잔존

---

### G7-5: 학습이 행동을 바꾸는 증거 경로의 불투명성 — `nice-to-have`

**유형**: 형식적 존재

**현황**: FailureLearner → `generate_constraint_prompt()` → CW 프롬프트에 "[V51.4] 과거 실패에서 학습된 제약" 블록 주입. DynamicPromptWeighter → urgency 태그(CRITICAL/HIGH) 주입.

**갭**:
- 주입은 확인되지만, **LLM이 해당 제약을 실제로 준수했는지** 측정하는 피드백 루프가 없음
- "이 제약을 주입했는데 같은 유형의 실패가 재발했다"를 감지하는 메커니즘 부재
- 학습 효과(제약 주입 전후의 해당 카테고리 실패율 변화) 측정 미구현
- 제약 수가 누적되면 프롬프트가 길어져 LLM의 attention 분산을 야기할 수 있으나, 제약 수 상한 관리가 context cap(12000자)뿐

---

## 4. 영향도 추정

| 갭 ID | 갭 명칭 | 직접 영향 | 간접 영향 | 등급 |
|-------|---------|----------|----------|------|
| G7-1 | 성공 학습 비대칭 | 성공 패턴 미활용으로 "좋았던 것을 반복"하는 능력 제한. 실패 회피에만 집중하면 방어적 글쓰기로 수렴 가능 | — | `significant` |
| G7-2 | 장르/위치별 분화 부재 | 다장르 운영 시 장르 간 학습 오염. Arc 초반/후반 구분 없는 제약이 부적절한 맥락에서 활성화 | 장르 전환 시 실패율 일시 상승 예상 | `significant` |
| G7-3 | 낙선 후보 학습 미반영 | 앙상블의 "2등"이 가진 장점이 소실. 비교 학습(contrastive learning) 기회 상실 | 앙상블 비용(3배 생성)의 정보 효율 저하 | `significant` |
| G7-4 | Decay 정책 조잡함 | 단기: 영향 미미. 장기/다장르: 학습 오염 누적 | 디버깅 시 "왜 이 제약이 활성화됐나" 추적 어려움 | `nice-to-have` |
| G7-5 | 학습 효과 측정 부재 | 비효과적 제약이 계속 주입되어 프롬프트 비대화. 학습 ROI 불명 | 학습 시스템 자체의 개선이 데이터 없이 감(感)에 의존 | `nice-to-have` |

**시스템 천장 분석**: G7-1~G7-3의 복합 효과로, 현재 학습 시스템은 **"같은 실수를 반복하지 않는"** 수준까지는 작동하지만, **"점점 더 잘 쓰는"** 수준의 양성 피드백 루프에는 미달. 이는 축 8(잘 멈추고)의 "충분히 좋다" 판단과 축 9(잘 측정하고)의 "좋다의 정의"에 직접 연결.

---

## 5. 방향 스케치

| 갭 ID | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|-------|--------|-------|------------|----------------|-------------|
| G7-1 | **성공 패턴을 CW 프롬프트에 주입**: `top_success_patterns()`의 출력을 DynamicPromptWeighter와 동일한 경로로 Stage 4에 전달. "이전 성공작에서 높은 점수를 받은 요소" 섹션 추가 | 소 | 불필요 | FailureAnalyzer + stage4_context_builder 확장 | 프롬프트 길이 증가; 성공 패턴이 "안전한 반복"으로 고착될 위험 |
| G7-2a | **FailureRecord에 genre 필드 추가 + 장르 필터링**: `generate_constraint_prompt(stage, genre=)` 시그니처 확장. win rate 쿼리에도 장르 필터 추가 | 소 | 불필요 | DB 스키마 + FailureLearner 확장 | 장르별 데이터 부족 시 학습 효과 감소 (cold start) |
| G7-2b | **Arc 위치 태그 추가**: episode_in_arc 정보를 FailureRecord에 포함, 위치별 제약 분리 | 소 | 불필요 | arc_data에서 위치 정보 이미 가용 | 세분화 과잉 시 데이터 희소성 |
| G7-3a | **낙선 후보 comparison_notes 확장**: 240자 → 800자 + 구조화 (strong_points, weak_points 필드) | 소 | 불필요 (기존 Director 호출 내) | director_ensemble.py 파싱 로직 | Director 응답 파싱 복잡도 증가 |
| G7-3b | **Contrastive learning 데이터 축적**: 당선/낙선 쌍을 별도 테이블에 저장, 차이점 요약을 학습 데이터로 활용 | 중 | 1회/비교 (요약용) | DB + 신규 테이블 | LLM 비용 증가; 요약 품질에 의존 |
| G7-4 | **장르 전환 시 decay + TTL 정책**: 장르 변경 감지 시 이전 장르 제약에 decay 가중치 적용; 30일 미사용 제약 자동 비활성 | 소 | 불필요 | FailureLearner 확장 | 장르 재방문 시 재학습 비용 |
| G7-5 | **제약 효과 추적**: 제약 주입 후 해당 카테고리 실패 재발 여부를 FailureLearner에서 자동 비교; 효과 없는 제약의 우선순위 하향 | 중 | 불필요 | FailureLearner + 신규 메트릭 | 인과관계 ≠ 상관관계 — 효과 귀인의 정확도 한계 |

**당장 할 수 있는 것**: G7-1, G7-2a, G7-3a (소규모, 기존 인프라, LLM 호출 증가 없음)
**설계가 필요한 것**: G7-3b, G7-5 (데이터 모델 설계, 효과 측정 로직 필요)

---

## 6. 묶음 내 교차 발견

(축 7이 묶음 A의 첫 번째 축이므로 선행 교차 발견 없음. 후속 축 8, 9에 전달할 발견사항:)

- **→ 축 8 전달**: G7-5 "학습 효과 측정 부재"는 축 8의 "수렴 판단"과 직접 관련. 학습된 제약이 실제로 멈춤 기준을 개선하는지 모른다는 것은, 멈춤 판단 자체의 근거가 약하다는 의미.
- **→ 축 9 전달**: G7-1 "성공 학습 비대칭"은 축 9의 "좋다의 정의"와 연결. "좋은 원고"의 특성이 학습되지 않으면, 측정 체계가 "좋다"를 정의해도 그 정의가 생산에 피드백되는 경로가 약함.
- **→ 축 8, 9 공통**: 학습 시스템이 "실패 회피" 편향이면, 멈춤 기준(축 8)도 "실패 없음 = 충분"으로 수렴하고, 측정(축 9)도 "결함 없음 = 좋음"으로 수렴할 위험.

---

## 7. 3-Pass 감리 기록

### Pass 1 (사실 정확성) — 88%

- **수정**: L1의 `generate_constraint_prompt` 파라미터를 `stage` 단독으로 정정 (초기에 `stage, genre` 포함으로 오기)
- **수정**: L4 Strategy Win Rate의 lookback 기본값을 20으로 정정 (초기에 10으로 오기)
- **수정**: FailureRecord 필드에 `genre` 없음을 코드에서 재확인 — 정확히 `category, stage, episode, arc, reason, details, timestamp`만 존재
- **수정**: `comparison_notes` 절삭 길이를 240자로 확인 (director_ensemble.py에서 `[:240]` 슬라이싱 확인)
- **확인**: episode_production.jsonl 구조의 feedback_provenance 내 runtime_advisory 필드 확인
- **미해결 → Pass 2**: top_success_patterns의 정확한 min_score 기본값 재확인 필요

### Pass 2 (논리 정합성) — 93%

- **수정**: G7-2 영향도에서 "장르 간 학습 오염"의 구체적 시나리오 추가 (다장르 운영 시)
- **수정**: G7-3 증거 경로에 `director_selections` 테이블의 스키마 근거 추가
- **확인**: G7-1 → G7-5의 논리 체인이 "실패 회피 편향 → 방어적 글쓰기 수렴"으로 일관되게 연결됨
- **확인**: 방향 스케치의 난이도/리스크 평가가 현실적임
- **보완**: 시스템 천장 분석에 축 8, 9와의 연결 명시 (교차 발견 섹션 보강)
- **해결**: top_success_patterns의 min_score=90 확인 완료

### Pass 3 (완성도) — 96%

- **보완**: 인벤토리에 "부수적 기여" 섹션 추가 (L7~L9) — 학습이 아닌 즉시 판단용이지만 학습 잠재력이 있는 구성요소
- **보완**: 교차 발견에 "축 8, 9 공통" 전달 사항 추가 (실패 회피 편향의 측정/멈춤에 대한 시스템적 함의)
- **확인**: 갭 유형 태그(완전 부재/부분 구현/형식적 존재)가 일관되게 적용됨
- **확인**: 방향 스케치의 "당장 할 수 있는 것" vs "설계 필요한 것" 분리가 명확
- **잔여 불확실성**: L6 episode_production.jsonl의 "시스템 자동 소비 경로 제한적"이라는 판단은 모든 import 경로를 추적한 것은 아님 (확신도 96%의 주된 원인)