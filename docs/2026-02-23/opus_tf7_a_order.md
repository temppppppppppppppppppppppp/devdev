# TF-7-A: Stage0 모듈 교차 버그 — 감사 실행 오더

> **Opus TF-7-A** | 2026-02-23
> **담당**: Opus 에이전트 A
> **출력**: `docs/2026-02-23/opus_tf7_a_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / UTF-8 주의 / 근거 필수

---

## 실행 순서

### Step 1: StageZeroManager 진입점 분석
**파일**: `modules/core/stage0/__init__.py`
- Read 도구로 전체 파일 읽기
- `StageZeroManager.__init__` 메서드 찾기
- 서브모듈 초기화 순서 기록: preset_registry → style_extractor → reverse_expander → story_expander 순서인지
- `__init__`에서 각 서브모듈을 `self.X = X(...)` 형태로 생성하는지 확인
- `db` 또는 `conn` 인자가 서브모듈에 올바르게 전달되는지

**기록할 것**:
- 각 서브모듈 초기화 줄 번호
- 서브모듈 간 의존 순서(A가 B를 필요로 한다면 B가 먼저 초기화되어야 함)
- `bind_db()` 또는 유사 메서드 존재 여부

### Step 2: PresetRegistry 계약 점검
**파일**: `modules/core/stage0/preset_registry.py`
- Read 도구로 전체 파일 읽기
- `get_preset(genre)` 또는 `get_active_presets()` 반환 타입 확인
- 존재하지 않는 장르 키 요청 시 반환값: `None`, `{}`, `KeyError` 중 무엇인가
- `activate_preset()` 또는 유사 메서드에서 중복 활성화 방어 여부
- 프리셋 키 충돌(동일 필드명이 common + genre에 모두 정의된 경우) 처리 로직
- 인코딩: 한글 장르명/필드명이 포함된 경우 `ensure_ascii=False` 직렬화 경로

### Step 3: StyleExtractor LLM 응답 처리
**파일**: `modules/core/stage0/style_extractor.py`
- Read 도구로 전체 파일 읽기
- LLM 응답 파싱 경로: `json.loads()` 예외 처리
- 파싱 실패 시 폴백 스키마 반환 여부 (아니면 None/예외?)
- `StyleGuard` 생성 실패 시 (`style_guard.py`와의 연동) None Guard가 등록되는 경로
- 원고 파일 읽기 경로에 `encoding="utf-8"` 명시 여부 (`open(..., encoding="utf-8")`)

### Step 4: ReverseExpander 입출력 안전성
**파일**: `modules/core/stage0/reverse_expander.py`
- Read 도구로 전체 파일 읽기 (1131줄이므로 두 번에 나눠 읽어도 됨)
  - 1~600줄 → 601~1131줄
- 원고 파일 읽기 경로: `open(path, ...)` 호출에서 `encoding` 인자 확인
- Arc/Blueprint 역추출 스킵 로직: 스킵 조건이 명확히 코드에 표현됐는지
- DB 저장 트랜잭션: `with db.transaction():` 보호 여부
- 에러 발생 시 부분 결과(Bible은 성공, NPC 등록 실패)가 커밋되는 경로

### Step 5: StoryExpander NPC 등록 경로
**파일**: `modules/core/stage0/story_expander.py`
- Read 도구로 전체 파일 읽기
- NPC 등록 시 `deceased` 필드 기본값 확인: `"deceased": False` 명시 여부
- LLM 응답에 `deceased` 키가 없을 때 기본값 처리
- Bible 구조체 생성 후 필수 키 검증: `MasterBible`, `Characters`, `WorldSettings` 존재 여부
- NPC 등록이 트랜잭션 내에서 배치로 처리되는지, 아니면 개별 커밋인지

### Step 6: 교차 연동 확인
- `StageZeroManager`에서 `style_extractor` → `StyleGuard` → `work_guard.py` 연동 코드 확인
- `reverse_expander`의 결과가 `preset_registry`를 통해 Stage2로 전달되는 경로 추적
- `story_expander`의 Bible 결과가 `__init__.py`에서 올바르게 DB에 저장되는지

---

## 이슈 등록 기준
- CRITICAL: Stage0 초기화 실패 시 전체 파이프라인 불가
- HIGH: NPC deceased 누락, 트랜잭션 없는 DB 쓰기, 한글 인코딩 오류
- MEDIUM: None 반환 미검사, 폴백 미문서화, 키 충돌 미처리
- FP: 정상 동작하나 스타일 개선이 필요한 수준

---

## 출력 파일 구조
```
# TF-7-A 감사 보고서 — Stage0 모듈 교차 버그

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-A-1] ...
...
## [FP] 오탐 목록
## 요약 테이블
```
