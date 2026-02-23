# TF-7-C 감사 보고서 — Director 체인 완전성

## 감사 파일 목록
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_grading.py`
- `modules/domain/agents/director_auditor.py`
- `modules/domain/agents/director_caching.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_continuity.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/base_agent.py`
- `main_a.py`

## 발견 이슈 (총 1건)

### [TF-7-C-1] Director Self-Consistency 타임아웃이 하드 타임아웃을 보장하지 못해 Stage2가 장시간 블로킹될 수 있음 (HIGH)
**근거 파일/줄**
- `modules/domain/agents/director_auditor.py:845`~`modules/domain/agents/director_auditor.py:853`  
  Self-Consistency 병렬 투표용 `VOTE_ENSEMBLE_TIMEOUT=150`, `SINGLE_VOTE_TIMEOUT=90` 선언.
- `modules/domain/agents/director_auditor.py:873`  
  `with ThreadPoolExecutor(...) as executor:` 컨텍스트 사용.
- `modules/domain/agents/director_auditor.py:878`~`modules/domain/agents/director_auditor.py:893`  
  `as_completed(..., timeout=VOTE_ENSEMBLE_TIMEOUT)` timeout 처리.
- `modules/domain/agents/director_auditor.py:895`~`modules/domain/agents/director_auditor.py:897`  
  timeout 이후 미완료 future에 대해 `f.cancel()`만 수행.
- `modules/domain/agents/director_auditor.py:856`  
  각 vote task는 `self._d.ask(...)`를 호출.
- `modules/domain/agents/base_agent.py:405`~`modules/domain/agents/base_agent.py:457`  
  `ask()` 내부에 API 재시도/네트워크 재시도 루프가 있어 개별 호출이 장시간 점유될 수 있음.
- `modules/core/stage2_finalizer.py:133`  
  Stage2 파이프라인이 `director.audit_strategic_plan(...)`을 동기 호출.

**문제**
- 코드 주석은 timeout으로 “무한 대기 방지”를 의도하지만, `with ThreadPoolExecutor(...)`는 블록 종료 시 기본 `wait=True`로 shutdown된다.
- `f.cancel()`은 실행 중 task를 중단하지 못하므로, 장기 블로킹 중인 vote task가 있으면 컨텍스트 종료 시점에 다시 대기한다.
- 결과적으로 `VOTE_ENSEMBLE_TIMEOUT`은 “집계 루프 timeout”일 뿐, 함수 전체의 하드 타임아웃을 보장하지 못한다.

**영향**
- Stage2 `audit_strategic_plan()` 호출이 장시간 붙잡혀 Arc 생성 파이프라인 전체가 정체될 수 있다.
- 운영상 “Director 타임아웃 150초”로 기대해도 실제 체감 지연이 그보다 크게 늘어날 수 있다.

**Caller→Callee 계약 추적**
- Caller: `modules/core/stage2_finalizer.py:133` (`Director.audit_strategic_plan`)
- Callee: `modules/domain/agents/director.py:176` → `modules/domain/agents/director_auditor.py:677` → `modules/domain/agents/director_auditor.py:794`
- 하위 계약: Self-Consistency timeout이 파이프라인 상위 호출의 지연 상한을 실질적으로 제어해야 함.

**Bug-vs-intent 근거**
- `director_auditor.py` 내부 주석은 timeout 기반 무중단 운영을 명시한다.
- 실제 구현은 running future를 강제 종료하지 못하므로 “timeout으로 대기 상한 보장”이라는 의도와 불일치한다.

**권장 수정 방향**
- `with ThreadPoolExecutor(...)` 대신 명시적 `executor = ThreadPoolExecutor(...)` + `shutdown(wait=False, cancel_futures=True)`로 종료 경로 제어.
- vote task 내부 `ask()`에 독립적인 하드 타임아웃/단축 재시도 정책 적용.
- Self-Consistency 경로 전용으로 네트워크 재시도 상한(`MAX_NETWORK_RETRIES`)을 더 낮게 분기.

## Risk (총 2건)

### [TF-7-C-R1] `director_grading.py`는 NaN/inf/이상치 score sanitize가 없어 품질 리포트 점수가 비정상 값으로 오염될 위험이 있음 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/domain/agents/director_grading.py:155`~`modules/domain/agents/director_grading.py:163`  
  `score`, `max_score`를 직접 연산하며 `isnan/isinf` 검사 없음.
- `modules/domain/agents/director_grading.py:128`~`modules/domain/agents/director_grading.py:131`  
  `weighted_total`을 그대로 `round(...)`해 반환.
- `modules/domain/agents/director_grading.py:533`~`modules/domain/agents/director_grading.py:534`  
  adaptive threshold는 clamp하지만 grading score 자체 clamp는 없음.

**Risk 판단 근거**
- 현재 경로에서 대체로 정상 숫자가 들어오면 문제없지만, 검증 결과 타입 오염 시 점수 리포트가 비정상 값으로 퍼질 가능성이 있다.
- 즉시 크래시 경로는 아니므로 Risk로 분류.

### [TF-7-C-R2] Continuity 캐시 재사용 키가 `ep_num` 중심이라 동일 에피소드 내 외부 데이터 변경 시 stale 스냅샷을 재사용할 위험이 있음 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/domain/agents/director_continuity.py:589`~`modules/domain/agents/director_continuity.py:604`  
  blueprint continuity 캐시 갱신/재사용 판단이 `_cached_blueprint_ep != ep_num`.
- `modules/domain/agents/director_continuity.py:701`~`modules/domain/agents/director_continuity.py:717`  
  manuscript continuity 캐시도 `_cached_manuscript_ep != ep_num` 기준.
- `modules/domain/agents/director.py:104`~`modules/domain/agents/director.py:112`  
  강제 무효화 API는 존재.
- `main_a.py:2800`~`main_a.py:2804`  
  rollback 시 무효화는 수행.

**Risk 판단 근거**
- 정상 운영(롤백/전환 훅)에서는 크게 문제되지 않지만, 동일 ep 내 수동 DB 조작/외부 변형이 들어오면 stale 가능성이 있다.
- 현재 관찰 범위에서는 즉시 오동작 증거가 부족해 Risk로 분류.

## [FP] 오탐 목록

### [FP-1] Director REJECT에서 `selected_candidate=None`이 그대로 Stage4로 전파되어 None dereference가 발생한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/director_ensemble.py:264`~`modules/domain/agents/director_ensemble.py:273`  
    후보 부족 시 dict 형태 fallback 후보를 채운다.
  - `modules/domain/agents/director_ensemble.py:423`~`modules/domain/agents/director_ensemble.py:473`  
    반환 `selected_candidate`는 후보 dict를 사용.
  - `modules/core/stage4_interview_round.py:687`, `modules/core/stage4_interview_round.py:843`~`modules/core/stage4_interview_round.py:845`  
    소비자 측도 `or {}`/dict 타입 방어를 이미 수행.

### [FP-2] `director_grading.py`는 예상 외 키 접근 시 KeyError로 즉시 깨진다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/director_grading.py:90`, `modules/domain/agents/director_grading.py:152`, `modules/domain/agents/director_grading.py:159`~`modules/domain/agents/director_grading.py:160`  
    핵심 score 접근은 `.get(..., default)` 기반.
  - `modules/domain/agents/director_grading.py:163`  
    관련 score가 없으면 기본값 `50`으로 반환.

### [FP-3] Context cache 만료 감지가 없어 만료 후에도 무조건 stale 캐시를 재사용한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/domain/agents/base_agent.py:1189`~`modules/domain/agents/base_agent.py:1195`  
    내부 cache map에서 TTL 경과 시 엔트리를 제거한다.
  - `modules/domain/agents/base_agent.py:1209`~`modules/domain/agents/base_agent.py:1215`  
    새 캐시 생성 시 TTL을 명시적으로 부여한다.

## TF-5-E 패치 회귀 확인

| 점검 항목 | 결과 | 근거 |
|---|---|---|
| E-1 단일 위치 불연속이 `PASS`로 누락되던 경계 | 회귀 없음 (PASS→WARNING으로 개선 유지) | `modules/domain/agents/director_continuity.py:645` |
| E-2 Director REJECT 시 선택 후보 누락(`selected_blueprint=None`) | 회귀 없음 (선택 후보 반환 유지) | `modules/domain/agents/director_ensemble.py:172`, `modules/domain/agents/unified_blueprint_validator.py:114`~`modules/domain/agents/unified_blueprint_validator.py:126`, `modules/domain/agents/three_phase_blueprint_generator.py:349`~`modules/domain/agents/three_phase_blueprint_generator.py:350` |

## 요약 테이블

| 분류 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-C-1` |
| Risk | 2 | `TF-7-C-R1`, `TF-7-C-R2` |
| FP | 3 | `FP-1~3` |
