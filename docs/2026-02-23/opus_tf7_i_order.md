# TF-7-I: Adaptive Retry / Feedback / Failure Learning 피드백 루프 — 감사 실행 오더

> **Opus TF-7-I** | 2026-02-23
> **담당**: Opus 에이전트 I
> **출력**: `docs/2026-02-23/opus_tf7_i_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
TF-5 R30에서 `adaptive_retry._failures` 무한 성장 발견 → 패치 여부 확인. 피드백 루프가 단방향(기록만)인지 실제로 행동 수정에 연결되는지 미검증. `pass_rate_monitor`의 전략 통과율이 Director 선택에 실제로 영향을 주는지 D-4 완료 이후 배선 확인.

---

## 실행 순서

### Step 1: AdaptiveRetry 크기 제한 및 Backoff
**파일**: `modules/core/adaptive_retry.py` (858줄)
- 1~430줄 읽기
- 431~858줄 읽기
- TF-5 R30 패치 확인: `_failures` 리스트에 크기 상한(`maxlen` deque 또는 슬라이싱) 적용 여부
- Backoff 계산: `2**n` 계산에서 `n`이 무한 증가 방어 (`min(n, MAX_N)` 패턴)
- 재시도 종료 조건: 최대 재시도 횟수 또는 총 시간 상한
- 모델 fallback: `_quota_exhausted_models` 딕셔너리 무잠금 접근 경쟁 (TF-5 R23 확인)

### Step 2: FeedbackSystem 피드백 연결
**파일**: `modules/core/feedback_system.py` (853줄)
- 1~430줄 읽기
- 431~853줄 읽기
- 피드백 기록 후 소비자에게 전달하는 경로 확인
  - `get_feedback_for(agent)` 또는 유사 메서드 존재 여부
  - 소비자(`base_agent.py`, `chief_writer.py` 등)에서 `feedback_system` 참조 여부
- 피드백 로그 상한: TF-6 B-3(`data_collector.py`) 패치와 유사한 상한 여부
- 특정 에이전트에만 전달 vs 전역 피드백 여부

### Step 3: FailureLearning 학습 결과 활용
**파일**: `modules/core/failure_learning.py` (367줄)
- Read 도구로 전체 파일 읽기
- 학습된 패턴을 어디서 읽는지: `adaptive_retry`에서 `failure_learning.get_patterns()` 호출 여부
- 학습 결과 DB 저장 여부 — 세션 재시작 후 재사용 가능한지
- 학습 데이터 크기 제한

### Step 4: ReflexionManager 루프 종료 조건
**파일**: `modules/core/reflexion_manager.py` (225줄)
- Read 도구로 전체 파일 읽기 (짧으므로 한 번에)
- Reflexion 루프 최대 반복 횟수 제한
- 개선 없을 때 조기 종료 조건: 점수 델타 임계값
- `failure_learning`과의 연동 — Reflexion 결과를 학습 데이터로 전달하는지

### Step 5: PassRateMonitor → Director 배선
**파일**: `modules/core/pass_rate_monitor.py` (550줄)
- Read 도구로 전체 파일 읽기
- D-4 완료 이후 전략별 통과율 → Director 전략 선택 영향 경로
- `director_ensemble.py` 또는 `stage4_orchestrator.py`에서 `pass_rate_monitor.get_rate(strategy)` 호출 여부
- 초기 에피소드(1~3화) 샘플 부족 시 기본값 처리

---

## 출력 파일 구조
```
# TF-7-I 감사 보고서 — Adaptive Retry / Feedback / Failure Learning

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-I-1] ...
## [FP] 오탐 목록
## TF-5 R30 패치 확인 (_failures 상한)
## 피드백 루프 완결성 다이어그램
## 요약 테이블
```
