# TF-7-H: Genre Guard 체인 완전성 — 감사 실행 오더

> **Opus TF-7-H** | 2026-02-23
> **담당**: Opus 에이전트 H
> **출력**: `docs/2026-02-23/opus_tf7_h_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
10종 장르 Guard + WorkGuard + StyleGuard = 총 13개. TF-5-H에서 구현/적용 일관성 HIGH 1건 발견. TF-5 K-3에서 ConsistencyValidator guard 로딩 통합 패치 완료 주장. 13개 Guard 전수 및 체인 순서 감사 미실시.

---

## 실행 순서

### Step 1: BaseGuard 계약 확인
**파일**: `modules/core/genre_guards/base_guard.py`
- Read 도구로 전체 파일 읽기
- `check(manuscript, context)` 메서드 서명 정확히 기록
- 반환 타입: `GuardResult(ok: bool, warnings: list, errors: list)` 또는 dict 확인
- `@abstractmethod` 여부 — 하위 클래스 강제 구현 보장

### Step 2: WorkGuard YAML 로드 안전성
**파일**: `modules/core/genre_guards/work_guard.py`
- Read 도구로 전체 파일 읽기
- YAML 파일 로드 경로: `open()`, `encoding="utf-8"` 여부
- YAML 로드 실패 시: None Guard 반환 vs no-op Guard vs 예외
- 작품별 YAML 파일 경로 구성 — 하드코딩 절대경로 여부

### Step 3: StyleGuard 자동 래핑
**파일**: `modules/core/genre_guards/style_guard.py`
- Read 도구로 전체 파일 읽기
- D-3(자동 생성) 완료 후 StyleGuard 생성 경로
- `style_extractor` 결과가 None/빈 dict일 때 Guard 생성 동작
- `base_guard.check()` 서명과 일치하는지

### Step 4: 10종 장르 Guard 일관성 점검 (병렬 읽기)
각 Guard 파일을 순서대로 읽으며 다음 항목 체크:
- `check()` 메서드가 `base_guard.check()` 서명과 동일한지
- 반환 타입이 일관된지 (dict vs 커스텀 객체)
- 하드코딩 용어 목록 파일(`config/terms/` 또는 인라인) 존재 여부
- 장르 특화 예외 처리

**감사 파일 순서**:
1. `modules/core/genre_guards/alt_history_guard.py`
2. `modules/core/genre_guards/composer_guard.py`
3. `modules/core/genre_guards/medical_guard.py`
4. `modules/core/genre_guards/sports_guard.py`
5. `modules/core/genre_guards/actor_guard.py`
6. `modules/core/genre_guards/cooking_guard.py`
7. `modules/core/genre_guards/wuxia_guard.py`
8. `modules/core/genre_guards/hunter_guard.py`
9. `modules/core/genre_guards/fantasy_guard.py`
10. `modules/core/genre_guards/investment_guard.py`

### Step 5: Guard 체인 호출 경로
**파일**: `modules/validation/consistency_validator.py`
- TF-5 K-3 패치 확인: `create_genre_guard()` 팩토리 함수 사용 여부
- 직접 import vs 팩토리 패턴 비교
- 3종 이상 Guard 로딩 여부 확인

### Step 6: 복합 장르 Guard 활성화
- `stage4_orchestrator.py` 또는 `validation_orchestrator.py`에서 Guard 활성화 로직
- 투자물+무협 복합 시 두 Guard 모두 호출 경로

### Step 7: 사망 NPC Guard 체인 처리
- 각 Guard에서 `deceased=True` NPC가 원고에 등장 시 탐지 로직
- 대원칙 4("사망 캐릭터는 회상/언급만 허용") 구현 위치

---

## Guard 서명 불일치 판정 기준
- `check()` 인수 수, 이름, 반환 타입이 `base_guard.py`와 다르면 MEDIUM 이상

## 출력 파일 구조
```
# TF-7-H 감사 보고서 — Genre Guard 체인 완전성

## 감사 파일 목록
## Guard 서명 일관성 테이블 (13개 Guard × 서명/반환타입)
## 발견 이슈 (총 N건)
### [TF-7-H-1] ...
## [FP] 오탐 목록
## TF-5-H, K-3 패치 회귀 확인
## 요약 테이블
```
