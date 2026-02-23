# TF-7-K: Stage0 Preset ↔ Stage2 StateTracker 연동 — 감사 실행 오더

> **Opus TF-7-K** | 2026-02-23
> **담당**: Opus 에이전트 K
> **출력**: `docs/2026-02-23/opus_tf7_k_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
MEMORY.md에 "Stage 0 ↔ Stage 2 연동" 완료 기록. StateTracker가 PresetRegistry 참조, 동적 EpisodeState, NPC 프리셋 기반 추적 13개 → 17~19개 필드 증가. 그러나 세부 계약(반환 타입, DB 지속성, 소급 적용) 미검증.

---

## 실행 순서

### Step 1: PresetRegistry 인터페이스 재확인
**파일**: `modules/core/stage0/preset_registry.py` (714줄)
- TF-7-A Step 2에서 이미 읽었으면 메모 참조 (중복 읽기 최소화)
- 핵심 확인:
  - `get_active_presets()` 반환 타입 정확히 확인: `list[str]`, `list[dict]`, `dict[str, dict]` 중
  - `activate_preset(genre: str)` 메서드 시그니처와 부작용(state mutation)
  - DB 저장 여부: `INSERT INTO presets...` 또는 인메모리 only

### Step 2: StageZeroManager → Stage2 전달 경로
**파일**: `modules/core/stage0/__init__.py` (581줄)
- TF-7-A Step 1에서 이미 읽었으면 해당 섹션 참조
- 프리셋 활성화 결과를 Stage2에 전달하는 메서드 찾기
  - `get_stage2_preset_data()` 또는 DB를 통한 간접 전달
  - 반환값이 Stage2 컨텍스트(`stage2_context.py`)에서 어떻게 소비되는지

### Step 3: StateTracker PresetRegistry 참조
**파일**: `modules/domain/agents/state_tracker.py`
- 전체 읽기 대신 `preset_registry`, `presets`, `active_presets` 키워드가 포함된 줄 집중
- 직접 객체 참조: `self.preset_registry = preset_registry` 형태인지
  - 직접 참조라면 순환 의존 (`state_tracker` → `preset_registry` → ?) 위험 평가
- 문자열 목록 수신: `self.active_presets: list[str]` 형태인지
- NPC 추적 필드 17~19개 구현 확인: `extra_fields` 또는 유사 동적 필드

### Step 4: Stage2 Preflight 프리셋 활용
**파일**: `modules/core/stage2_preflight.py` (637줄)
- Read 도구로 전체 파일 읽기
- 프리셋 데이터 소비 경로: `self.app.preset_registry` 또는 DI 주입
- 프리셋 기반 검증 조건: `if "wuxia" in active_presets` 형태의 장르별 분기
- preflight 분석에서 프리셋이 없을 때 기본 동작(폴백 공통 프리셋)

### Step 5: 동적 프리셋 추가 소급 적용
- `stage2_orchestrator.py` 또는 `stage2_preflight.py`에서 Block 30 이후 새 장르 프리셋 추가 시
- 이미 생성된 Arc/Blueprint를 수정하는 메커니즘 존재 여부
- 소급 적용 없으면: 설계 의도(적용 없음)인지 미구현인지 코드/주석으로 확인

### Step 6: 프리셋 DB 지속성
- 세션 재시작 후 프리셋 복원: `project._load_from_db()`에서 프리셋 로드 경로
- 복원 실패 시 기본 프리셋(common) 폴백 여부

---

## 출력 파일 구조
```
# TF-7-K 감사 보고서 — Stage0 Preset ↔ Stage2 StateTracker 연동

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-K-1] ...
## 프리셋 데이터 흐름 다이어그램 (Stage0 → StateTracker → Stage2Preflight)
## [FP] 오탐 목록
## 요약 테이블
```
