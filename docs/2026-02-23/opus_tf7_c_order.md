# TF-7-C: Director 체인 완전성 — 감사 실행 오더

> **Opus TF-7-C** | 2026-02-23
> **담당**: Opus 에이전트 C
> **출력**: `docs/2026-02-23/opus_tf7_c_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / UTF-8 주의 / 근거 필수

---

## 배경
TF-5-E에서 Director 판정 경계 결함 1건 HIGH 발견 후 패치됨. `director_grading.py`(680줄), `director_auditor.py`(1063줄), `director_caching.py`(175줄), `director_ensemble.py`(534줄), `director_continuity.py`는 종합 감사 미실시.

---

## 실행 순서

### Step 1: Director Grading 수치 안전성
**파일**: `modules/domain/agents/director_grading.py` (680줄)
- Read 도구로 전체 파일 읽기
- 점수 계산 메서드 찾기: `calculate_score()`, `grade()` 또는 유사
- NaN/inf 방어: `math.isnan()`, `math.isinf()` 또는 try/except 존재 여부
- `scores` dict에서 예상 외 키 접근 시 `.get(key, 0)` vs `[key]` 직접 접근 비율
- 분모 0 방어: 평균 계산 시 `len() == 0` 체크
- 점수 범위 클램핑: 0~100 범위 초과 시 처리

### Step 2: Director Auditor 병렬 Future 처리
**파일**: `modules/domain/agents/director_auditor.py` (1063줄)
- 1~550줄 읽기
- 551~1063줄 읽기
- `ThreadPoolExecutor` 사용 위치 찾기
- `as_completed()` 루프에서 `future.exception()` 확인 여부
- 예외 발생한 Future 처리 — 조용히 무시 vs 로그 기록 vs 재시도
- `executor.shutdown(wait=True)` 또는 `cancel_futures=True` 사용 여부

### Step 3: Director Caching 키 충돌
**파일**: `modules/domain/agents/director_caching.py` (175줄)
- Read 도구로 전체 파일 읽기 (짧으므로 한 번에)
- 캐시 키 생성 로직: 에피소드 번호 + Arc 번호 + 전략명 조합
- 키에 충분한 구분자가 있는지 (e.g., `f"{ep}_{arc}_{strategy}"`)
- 캐시 만료/TTL 정책 또는 크기 상한 존재 여부
- 캐시 히트 시 반환되는 객체가 mutable이면 참조 공유 위험 — deepcopy 여부

### Step 4: Director Ensemble 전략 실패 처리
**파일**: `modules/domain/agents/director_ensemble.py` (534줄)
- Read 도구로 전체 파일 읽기
- 앙상블 후보 전부 REJECT 시 반환값: `None`인지 빈 dict인지 예외인지
- `selected_candidate` 키가 None인 채로 반환되는 경로 확인
- 소비자(`stage4_interview_round`)에서 None 검사 여부 (TF-5 B-1 크로스컷 연관)
- 전략 가중치 계산에서 `sum(weights) == 0` 방어

### Step 5: Director Continuity Context Caching
**파일**: `modules/domain/agents/director_continuity.py` (파일 존재 여부 먼저 확인)
- Read 도구로 전체 파일 읽기
- `_get_or_create_context_cache` 호출 경로 확인
- 캐시 항목 만료 감지: Gemini API가 캐시 만료를 알리는 방식 + 코드에서 재생성 트리거
- 만료 감지 실패 시 stale 캐시로 LLM 호출하는 경로

### Step 6: Director 체인 순서 일관성
- `stage4_orchestrator.py`의 Director 호출 순서 확인 (grading → auditor → ensemble → director 결정)
- `stage4_interview_round.py`에서 Director 판정 흐름 재확인

---

## 출력 파일 구조
```
# TF-7-C 감사 보고서 — Director 체인 완전성

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-C-1] ...
## [FP] 오탐 목록
## TF-5-E 패치 회귀 확인
## 요약 테이블
```
