# TF-7-B: Context Advisor / Smart Retrieval 계약 — 감사 실행 오더

> **Opus TF-7-B** | 2026-02-23
> **담당**: Opus 에이전트 B
> **출력**: `docs/2026-02-23/opus_tf7_b_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / UTF-8 주의 / 근거 필수

---

## 배경
SC-0~6(Smart Context Retrieval)은 2026-02-22 완료. TF-5/6에서 SC 슬롯 관련 부분 이슈 발견됐으나 `context_advisor.py` 자체 내부 + 소비자 간 계약은 미감사. TF-6 TF-G-1 패치로 `slot_max_chars` 외부화 완료됐으나 소비자에서의 실제 적용 확인 필요.

---

## 실행 순서

### Step 1: ContextAdvisor 내부 계약 분석
**파일**: `modules/core/context_advisor.py` (675줄)
- Read 도구로 전체 파일 읽기
- `RetrievalPlan`, `Slot`, `Sources` 클래스/dataclass 정의 찾기
- `plan()` 메서드 반환 타입: 항상 `RetrievalPlan`인지, `None`/예외 가능한지
- 슬롯 목록이 비어 있을 때 반환 처리
- `Sources` 데이터가 DB 조회 실패 시 빈 리스트 vs 예외 중 어느 쪽인가
- 캐시(`_plan_cache` 또는 유사) 존재 여부 + 무효화 트리거 조건
- `slot.max_chars` 기본값 설정 경로 (TF-6 G-1 이후 YAML에서 읽는지 하드코딩 잔존인지)

### Step 2: Stage4 Context Builder SC 소비
**파일**: `modules/core/stage4_context_builder.py` (570줄)
- Read 도구로 전체 파일 읽기
- `context_advisor.plan()` 호출 위치 찾기
- 반환값이 None일 때 분기 확인
- 빈 슬롯 목록 처리
- `source.content`가 빈 문자열일 때 컨텍스트에 포함 여부
- `Slot.max_chars`가 0이거나 미설정일 때 컨텍스트 길이 제한 동작

### Step 3: Stage4 Interview Round SC 소비
**파일**: `modules/core/stage4_interview_round.py` (554줄)
- Read 도구로 전체 파일 읽기
- TF-6 G-1 패치 확인: `_DEFAULT_SLOT_MAX`, `_MAX_NPCS_PER_SLOT` 변수가 `_threshold()`로 읽는지
- `stage4_context_builder`와 독립적으로 `plan()`을 재호출하는지, 또는 공유 결과를 받는지
- 중복 호출 시 성능·정합성 문제

### Step 4: DI 컨텍스트 SC 배선 확인
**파일**: `modules/core/stage2_context.py` (먼저 줄 수 확인 후 읽기)
**파일**: `modules/core/stage3_context.py`
**파일**: `modules/core/stage4_context.py`
- 각 파일에서 `context_advisor` 슬롯 정의 위치 찾기
- `lazy_init` 패턴 확인: 두 번 호출 시 중복 초기화 방어(`if self._X is None` 패턴)
- 슬롯 초기화 순서 의존성: SC 슬롯이 DB 슬롯보다 나중에 초기화되는지

### Step 5: 캐시 무효화 크로스컷
- `context_advisor.py`의 캐시가 `project_manager.py` 프로젝트 전환 시 클리어되는지
- Stage4가 새 에피소드를 시작할 때 이전 에피소드의 SC 캐시가 재사용되지 않는지

---

## 출력 파일 구조
```
# TF-7-B 감사 보고서 — Context Advisor / Smart Retrieval

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-B-1] ...
## [FP] 오탐 목록
## TF-6 G-1 패치 확인 결과
## 요약 테이블
```
