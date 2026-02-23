# TF-7-D: Validation Orchestrator 완전성 — 감사 실행 오더

> **Opus TF-7-D** | 2026-02-23
> **담당**: Opus 에이전트 D
> **출력**: `docs/2026-02-23/opus_tf7_d_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / UTF-8 주의 / 근거 필수

---

## 배경
TF-5-K에서 `required_scenes` 최소치 오류(HIGH), ConsistencyValidator guard 3종 제한(HIGH) 발견 → TF-5 패치 완료 여부 확인 필요. `validation_orchestrator.py`(1522줄)는 TF에서 부분만 다뤘고 전체 파이프라인 감사 미실시.

---

## 실행 순서

### Step 1: Validation Orchestrator 전체 흐름
**파일**: `modules/validation/validation_orchestrator.py` (1522줄)
- 1~760줄 읽기
- 761~1522줄 읽기
- 검증 모듈 호출 순서: advisory → blocking → continuity → scoring 순서인지
- Advisory 결과가 Blocking 입력에 영향 주는지 확인
- 각 검증기 반환값 수집 방식: `results.append(validator.check(...))` 패턴
- 검증기가 None을 반환할 때 집계 코드의 `.get()` vs `[]` 접근 패턴
- `stage=4` 파라미터로 `quality_dashboard.record_validation()` 호출 여부 (TF-5 L-1 패치 확인)

### Step 2: Advisory Validator 반환 스키마
**파일**: `modules/validation/advisory_validator.py` (211줄)
- Read 도구로 전체 파일 읽기
- 반환값 구조: `{"warnings": [...]}` 인지, `{"issues": [...]}` 인지, 단순 `list`인지
- 소비자가 기대하는 키 이름과 일치하는지 (`validation_orchestrator.py`에서의 소비 코드와 대조)
- 항상 dict 반환 보장 여부: 내부 예외 시 `{}` 반환 vs 예외 전파

### Step 3: Blocking Validator 서브모듈 예외 격리
**파일**: `modules/validation/blocking_validator.py` (211줄)
- Read 도구로 전체 파일 읽기
- 3개 서브모듈 호출 방식: 순차인지, 하나 실패 시 나머지 실행 여부
- 각 서브모듈(`consistency_checks`, `entity_checks`, `scene_checks`) import 방식
- `blueprint=None` 시 `scene_checks`의 동작: PASS 폴백인지 예외인지 (X-1 크로스컷 연관)

**파일**: `modules/validation/blocking_validator_scene_checks.py`
- `blueprint`가 None/빈 dict일 때 분기 확인

### Step 4: Pre-LLM Validator V70 POV 활성화
**파일**: `modules/validation/pre_llm_validator.py` (494줄)
- Read 도구로 전체 파일 읽기
- V70 POV 일관성 체크 메서드 찾기
- `validation_orchestrator.py`에서 V70 호출 경로 확인 (D-1 완료 후 배선됐는지)
- POV 체크 비활성화 조건 (설정 플래그 등)

### Step 5: Scoring Validator 수치 안전성
**파일**: `modules/validation/scoring_validator.py` (1271줄)
- 1~640줄 읽기
- 641~1271줄 읽기
- TF-6 G-3 패치 확인: `_threshold()` 기반 외부화된 상수 변수들 존재 여부
- 점수 합산 시 분모 0 방어: `len(items) == 0` → `0` 또는 `N/A` 반환
- `sanitize_max_chars` 적용 경로

### Step 6: Continuity Validator Episode 1 처리
**파일**: `modules/validation/continuity_validator.py` (993줄)
- 1~500줄 읽기
- 501~993줄 읽기
- Episode 1 (이전 데이터 없음) 분기 확인: `if prev_episode is None`
- None vs 빈 dict 혼용 여부
- ConsistencyValidator 내부 guard 로딩 — `create_genre_guard()` 통합 여부 (TF-5 K-3 패치 확인)

---

## 출력 파일 구조
```
# TF-7-D 감사 보고서 — Validation Orchestrator 완전성

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-D-1] ...
## [FP] 오탐 목록
## TF-5-K 패치 회귀 확인 (K-1, K-2, K-3)
## TF-5-L 패치 회귀 확인 (L-1: quality_dashboard stage=4 배선)
## 요약 테이블
```
