# Stage 0 Map

## Scope
- 프로젝트 초기 설정을 담당한다: 컨셉 기반 Bible/Treatment 생성, 기존 원고 역설계(Bible/episode_bibles/style), Bible JSON 임포트, 스타일 레퍼런스 분석.
- Stage1/2/3/4 진입 전 기본 데이터(Bible, preset, style guide, 역설계 stub)를 DB에 동기화한다.
- Out of scope: Arc 설계(Stage2), Blueprint 생성(Stage3), 원고 집필(Stage4).

## Entry Points
- Primary:
  - `main_a.py` 메인 메뉴 `choice == "0"` → `_phase_0_recovery()` → `Stage01Helpers.phase_0_recovery()`
  - `Stage01Helpers.stage_0_extended(mode)` (mode 1~5: 컨셉/역설계/임포트/블록확장/스타일분석)
- Secondary:
  - `StageZeroManager.run_new_project_flow()`
  - `StageZeroManager.run_reverse_engineering_flow()`
  - `StageZeroManager.import_bible()`
  - `StageZeroManager.run_reference_analysis()`

## Inputs
- Required:
  - 컨셉 텍스트(신규 생성) 또는 원고 파일/폴더 경로(역설계)
  - 장르 선택(또는 자동 감지), 주인공 설정(`world_origin`, `incarnation_type`, `pov`)
- Optional:
  - Bible JSON 파일 경로(임포트)
  - 스타일 레퍼런스 폴더(`config/style_references/{genre}/...`)
  - Block 확장 시 방향 힌트 / 배치 확인 입력

## Outputs
- Files:
  - `stage0_output/bible.json`, `treatment.json`, `episode_bibles.json`, `style_guide.json`, `preset_state.json`
  - `treatment_generated.json`, `treatment_extended.json` (Stage0 확장 경로)
- DB updates:
  - anchors: `bible`, `preset_state`, `style_guide` (`save_v20_anchor`)
  - Bible 저장 시 하위 동기화:
    - `seeds` 테이블 (`sync_seeds`)
    - `encyclopedia` 테이블 (`update_lore_items_batch`, KeyNPCs 포함)
    - `martial_tracker` (latest ep 기반 HUD 동기화 조건부)
  - 역설계 DB 저장(`ReverseExpander.persist_to_db`):
    - `manuscripts`, `state_logs`, `episode_bibles`, `blueprints`(stub), `anchors["arcs"]`(stub)
- In-memory state:
  - `StageZeroManager`의 `bible/treatment/episode_bibles/style_guide/preset_registry`
  - `current_project.master_bible`, `app.preset_registry`, 선택 장르/주인공 설정

## Dependencies
- Internal modules:
  - `modules/core/stage0`: `StageZeroManager`, `StoryExpander`, `ReverseExpander`, `StyleExtractor`, `PresetRegistry`
  - `modules/core/stage01_helpers.py` (main menu Stage0/1 orchestration)
  - `ProjectManager.save_v20_anchor()` / `DBManager` 저장 루틴
- External services/models:
  - Google GenAI LLM 호출 (`StoryExpander`/`ReverseExpander`/`StyleExtractor`)
  - 선택적 VecMemory 저장(`ReverseExpander.persist_to_vectordb`)

## State and Cache
- Persistent state:
  - DB anchors + stage0_output JSON 파일
  - 역설계 시 DB 테이블(stub 포함)까지 채워 Stage2~4 시작점 구성
- Runtime cache:
  - `StyleExtractor` 캐시: `config/style_references/{genre}/style_guide.json`
  - `ReverseExpander` 내부 raw draft/episode bible 집계 상태
- Invalidation rules:
  - 스타일 캐시는 레퍼런스 `.txt` 최신 mtime이 캐시보다 새로우면 재분석
  - Stage0 상태는 `StageZeroManager.load_state()`로 재로딩 가능

## Failure and Recovery
- Common failure patterns:
  - LLM 호출/파싱 실패, 입력 경로/JSON 파일 오류, 인코딩 오류(UTF-8 실패)
  - 역설계 DB 저장 중 트랜잭션 실패
- Recovery flow:
  - LLM 호출은 다중 모델 폴백 + 지수 백오프 재시도(최대 3회)
  - 파일 읽기 인코딩 폴백(UTF-8 → cp949 → replace)
  - 역설계 `persist_to_db`는 begin/commit, 실패 시 rollback
- Fallback behavior:
  - Bible/NPC 생성 실패 시 빈 구조 또는 조기 반환으로 다음 단계 오염 방지
  - episode_bible 단건 추출 실패 시 기본 스키마로 대체 저장

## Manual Intervention Points
- User prompts:
  - Stage0 서브메뉴 선택(컨셉/역설계/임포트/확장/스타일)
  - 장르/주인공 설정/시점 입력, 컨셉 멀티라인 입력
  - 스타일 분석 실행 확인(`y/n`), block 확장 배치 승인
- Approvals:
  - 자동 승인 단계는 없고, 대부분 입력 기반 분기
- Operator checks:
  - Stage0 완료 후 저장 로그(anchors/treatment/style)와 역설계 요약(다음 시작 Arc/ep) 확인

## Metrics
- Throughput:
  - 전용 집계 시스템 없음 (로그 기반 확인)
- Error rate:
  - 전용 대시보드 없음 (경고/예외 로그 기반)
- Latency:
  - 전용 타이머 없음 (LLM 호출/배치 처리 로그 기반)

## Tests
- Unit:
  - `tests/test_stage0_fixes.py`
  - `tests/test_stage0_pov.py`
  - `tests/test_reverse_expander_g2.py`
- Integration:
  - `tests/test_stage01_helpers.py`
- Regression:
  - `tests/test_stage01_fixes.py`
  - `tests/test_style_guard.py`

## Open Risks
- Risk 1: Stage0 흐름이 `input()` 중심이라 비대화형 자동화 실행에서 중단 지점이 많다.
- Risk 2: 역설계 stub(blueprint/arc)은 원고 기반 근사치이므로 Stage2/3에서 추가 보정 없이는 품질 편차가 발생할 수 있다.

## Last Verified
- Date: 2026-02-25
- Commit: `f99119d`
- Code Sync (Yes/No): Yes
- Verified By: Codex

