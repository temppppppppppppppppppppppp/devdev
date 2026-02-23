# TF-7-L: Quality Dashboard / Metrics / Pass Rate 피드백 루프 — 감사 실행 오더

> **Opus TF-7-L** | 2026-02-23
> **담당**: Opus 에이전트 L
> **출력**: `docs/2026-02-23/opus_tf7_l_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
TF-5 L-1: Stage4 결과가 `quality_dashboard`에 기록되지 않아 경보 체인 공회전 → HIGH 이슈. TF-5 패치 완료 주장. 본 TF에서 패치 적용 여부 확인 + 전체 피드백 루프 완결성 재감사.

---

## 실행 순서

### Step 1: QualityDashboard 전체 구조
**파일**: `modules/core/quality_dashboard.py` (1100줄)
- 1~550줄 읽기
- 551~1100줄 읽기
- `record_validation(stage, result)` 메서드 시그니처 확인
- `stage=4` 파라미터 처리 분기 존재 여부
- 경보(alert) 발동 임계값: 하드코딩인지 `_threshold()` 기반 외부화인지
- Stage별 집계: `stage=1`, `=2`, `=3`, `=4` 모두 지원하는지

### Step 2: Stage4 Post Processor 배선 확인
**파일**: `modules/core/stage4_post_processor.py` (543줄)
- Read 도구로 전체 파일 읽기
- TF-5 L-1 패치 확인: PASS/REJECT 확정 지점에서 `quality_dashboard.record_validation(stage=4, ...)` 호출 여부
- 호출 위치의 정확한 줄 번호 기록
- 호출이 없으면: HIGH 이슈 재등록

### Step 3: Stage2 Finalizer 배선 확인
**파일**: `modules/core/stage2_finalizer.py` (535줄)
- Read 도구로 전체 파일 읽기
- `quality_dashboard` 배선 여부: Stage2 Arc 합격/불합 결과 기록
- Stage3 오케스트레이터도 확인: `stage3_orchestrator.py`에서 `quality_dashboard` 참조

### Step 4: MetricsCollector 중복 기록
**파일**: `modules/core/metrics_collector.py` (478줄)
- Read 도구로 전체 파일 읽기
- `quality_dashboard`와 중복 기록하는 이벤트 타입 파악
- 동일 이벤트가 두 모듈 모두에 기록되면 집계 오류 가능성
- `metrics_collector`에서 수집하는 지표 목록 확인 — 읽히지 않는 "dead metric" 식별

### Step 5: PassRateMonitor 경보 연동
**파일**: `modules/core/pass_rate_monitor.py` (550줄)
- TF-7-I에서 이미 읽었으면 해당 메모 참조
- `quality_dashboard`와의 연동: 통과율 급락 시 경보를 `quality_dashboard`에 기록하는 경로
- 독립 운영 여부 확인

### Step 6: 피드백 루프 완결성 다이어그램 작성
감사 결과 기반으로 다음 다이어그램 초안 작성:
```
Stage4 결과 → [stage4_post_processor] → quality_dashboard
                                       ↓
                                    alert 발동?
                                       ↓
                              pass_rate_monitor ←→ director_ensemble
```
- 각 화살표가 실제 코드로 구현됐는지 Yes/No 표기

---

## 출력 파일 구조
```
# TF-7-L 감사 보고서 — Quality Dashboard / Metrics / Pass Rate

## 감사 파일 목록
## TF-5 L-1 패치 확인 결과 (YES/NO + 증거 줄 번호)
## 발견 이슈 (총 N건)
### [TF-7-L-1] ...
## 피드백 루프 완결성 다이어그램 (구현 여부 표기)
## [FP] 오탐 목록
## 요약 테이블
```
