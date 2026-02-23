# TF-7-K 감사 보고서 — Stage0 Preset ↔ Stage2 StateTracker 연동

## 감사 파일 목록
- `modules/core/stage0/preset_registry.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_manager.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/state_tracker.py`
- `modules/validation/validation_orchestrator.py`
- `main_a.py`

## 발견 이슈 (총 1건)

### [TF-7-K-1] `preset_state`는 저장되지만 프로젝트 재로드/롤백 시 복원 계약이 끊겨 있음 (HIGH)
**증거 파일/라인**
- `modules/core/stage01_helpers.py:467`
- `modules/core/stage01_helpers.py:468`
- `modules/core/project_manager.py:142`
- `modules/core/project_manager.py:143`
- `modules/core/project_manager.py:144`
- `modules/core/stage2_context.py:212`
- `main_a.py:2734`

**수동 근거**
- Stage0 완료 시 `preset_state` anchor를 DB에 저장한다.
- 프로젝트 `_load_from_db()`는 `bible`, `volumes`, `arcs`만 로드하며 preset 복원 경로가 없다.
- Stage2 컨텍스트는 `app.preset_registry`를 그대로 참조한다.
- 앱 장르 선택 시 `PresetRegistry(base_genre=...)`를 새로 생성한다.

**Caller-callee 계약 추적**
- Caller(저장): `stage01_helpers._s0_save_results()` → `save_v20_anchor("preset_state", ...)`
- Caller(소비): `Stage2Context.from_app()`가 `app.preset_registry`를 전달
- 누락된 callee: 프로젝트 DB 로드 시 `preset_state`를 다시 `app.preset_registry`로 복원하는 경로

**Bug-vs-intent 판단**
- 저장 경로가 명시적으로 존재하는데 재기동/롤백 경로에서 복원이 빠져 있어 계약 불일치다.
- `StageZeroManager.load_state()`의 파일 기반 preset 복원(`stage0/__init__.py:538`~`modules/core/stage0/__init__.py:547`)은 존재하지만, 런타임 DB 재로드 경로와 분리되어 있어 intent 충족으로 보기 어렵다.

## 프리셋 데이터 흐름 다이어그램 (Stage0 → StateTracker → Stage2Preflight)

```text
Stage0 완료
  └─ stage01_helpers._s0_save_results
      ├─ app.preset_registry = stage0_manager.preset_registry
      └─ save_v20_anchor("preset_state", ...)

Stage2 시작
  └─ Stage2Context.from_app
      └─ preset_registry=getattr(app, "preset_registry", None)
          └─ Stage2Orchestrator: StateTracker(preset_registry=...)

실행 중 동적 장르
  └─ stage2_preflight -> state_tracker.check_and_expand_genre()
      └─ preset activate + tracking_fields refresh
```

## Risk (추가 확인 필요)

### [TF-7-K-R1] 동적 프리셋 확장 시 Guard/Validator 체인 즉시 재초기화 경로가 확인되지 않음 (MEDIUM, Risk)
**증거 파일/라인**
- `modules/core/stage2_preflight.py:978`
- `modules/core/stage2_preflight.py:981`
- `modules/domain/agents/state_tracker.py:309`
- `modules/domain/agents/state_tracker.py:312`
- `modules/validation/validation_orchestrator.py:190`
- `modules/validation/validation_orchestrator.py:214`

**수동 근거**
- 동적 장르 감지 후 수행되는 동작은 preset 활성화 + tracking 필드 refresh다.
- ValidationOrchestrator는 생성 시점 genre로 ConsistencyValidator를 구성한다.
- 동적 확장 직후 validator/guard 재구성 호출은 현재 추적 범위에서 확인되지 않았다.

## [FP] 오탐 목록

### [FP-1] PresetRegistry는 직렬화가 불가능하다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/stage0/preset_registry.py:689` (`to_json`)
  - `modules/core/stage0/preset_registry.py:700` (`from_json`)

### [FP-2] Stage2에서 preset_registry를 전달하지 않는다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/stage2_context.py:212`
  - `modules/core/stage2_orchestrator.py:153`

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-K-1` |
| Risk | 1 | `TF-7-K-R1` |
| FP | 2 | `FP-1`, `FP-2` |

