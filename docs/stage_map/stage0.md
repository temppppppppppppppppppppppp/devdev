# Stage 0 Map

## Scope
- Define what Stage 0 is responsible for.
  - 신규 프로젝트의 컨셉을 분석해 Bible + Treatment를 생성한다.
  - 기존 원고를 역설계해 Bible, episode_bibles, style_guide를 추출하고 DB 시작점을 복원한다.
  - 기존 Bible JSON을 임포트하고 `preset_state`/`protagonist_config`를 현재 프로젝트에 동기화한다.
  - 기존 Treatment를 블록 단위로 확장하고, 확장 결과를 `MasterBible.plot_roadmap`에 주입한다.
  - 장르별 레퍼런스 원고를 분석해 `StyleGuide`와 `reference_excerpt`를 생성한다.
  - 스타일 분석은 최대 `1,000,000자` 샘플링, `6배치/2회` LLM 심층 분석, `50,000자` 상한 `reference_excerpt` 생성을 포함한다.
- Out of scope:
  - 권 전략 설계(Stage 1 책임).
  - 실제 Arc 설계(Stage 2 책임).
  - 실제 Blueprint 생성(Stage 3 책임).
  - 실제 원고 생성(Stage 4 책임).
  - Stage 0 역설계가 만드는 Arc/Blueprint는 운영용 완제품이 아니라 stub/복구용 시작점이다.

## Why
- 왜 Stage 0를 분리하는가? 이후 Stage 1~4가 기대하는 Bible, preset, style guide, 역설계 복구 데이터의 계약을 먼저 확정해야 하기 때문이다.
- 왜 역설계가 DB까지 채우는가? 기존 원고가 있는 프로젝트를 Stage 2/3/4 재생성 지점까지 빠르게 복구하기 위해서다.
- 왜 스타일 레퍼런스 분석을 Stage 0에서 하느냐? `style_guide`와 `reference_excerpt`는 이후 Stage 4 Chief Writer 공통 컨텍스트의 일부이기 때문이다.
- 왜 스타일 캐시를 두는가? 장르 레퍼런스 분석은 대용량 텍스트 + LLM 호출이 들어가므로, `config/style_references/{genre}/style_guide.json` 재사용으로 비용과 지연을 줄이기 위해서다.

## Entry Points
- Primary:
  - `main_a.py` 메인 메뉴 `choice == "0"` → `_phase_0_recovery()` → `Stage01Helpers.phase_0_recovery()`
  - `Stage01Helpers.stage_0_extended(mode)` (`mode=1..6`)
    - `1`: 컨셉 → Bible/Treatment 생성
    - `2`: 역설계
    - `3`: Bible 임포트
    - `4`: Block 확장
    - `5`: 스타일 레퍼런스 분석
    - `6`: 작품가드 설정(선택)
- Secondary:
  - `StageZeroManager.run_new_project_flow()`
  - `StageZeroManager.run_reverse_engineering_flow()`
  - `StageZeroManager.import_bible()`
  - `StageZeroManager.run_reference_analysis()`
  - `Stage01Helpers.extend_blocks()`
- Notes:
  - `StageZeroManager.show_menu()` 자체는 블록 확장을 직접 노출하지 않는다. 블록 확장은 `phase_0_recovery()`/`stage_0_extended(mode=4)` 경로에서만 진입한다.

## Inputs
- Required:
  - 컨셉 기반 생성: 멀티라인 컨셉 텍스트.
  - 역설계: 원고 파일 또는 폴더 경로.
  - Bible 임포트: `.json` 파일 경로.
  - 스타일 분석: 장르 코드 + `config/style_references/{genre}/...` 레퍼런스 폴더.
- Optional:
  - 장르 선택 또는 자동 감지.
  - 주인공 설정: `world_origin`, `incarnation_type`, `pov`.
  - Block 확장 방향 힌트 / 배치별 승인 입력.
  - 작품가드 소스 YAML (`work_guards/**/*.yaml`) 또는 프로젝트별 `{project}/config/work_guard.yaml`
  - VecMemory 인스턴스 (`persist_to_vectordb()` 외부 주입).

## Outputs
- Files:
  - `stage0_output/bible.json`
  - `stage0_output/treatment.json`
  - `stage0_output/episode_bibles.json`
  - `stage0_output/style_guide.json`
  - `stage0_output/preset_state.json`
  - `stage0_output/stage0_state.json` (`StageZeroManager.save_state()` 경로)
  - `{project}/config/work_guard.yaml` (선택)
  - 프로젝트 루트: `treatment_generated.json`, `treatment_extended.json`
- DB updates:
  - `save_v20_anchor("bible", bible)`
    - `Seeds` → `sync_seeds()`
    - `AssetLibrary` → `update_lore_items_batch()`
    - `MartialHUD.Protagonist.actual_truth` 존재 시 `martial_tracker` 조건부 동기화
  - `save_v20_anchor("preset_state", ...)`
  - `save_v20_anchor("style_guide", ...)`
  - 역설계 DB 저장(`ReverseExpander.persist_to_db()`):
    - `manuscripts`
    - `state_logs`
    - `episode_bibles`
    - `blueprints` (stub)
    - `anchors["arcs"]` (stub + enrich)
  - 선택적 VecMemory 저장(`ReverseExpander.persist_to_vectordb()`)
- In-memory state:
  - `StageZeroManager.genre`, `preset_registry`, `bible`, `treatment`, `episode_bibles`, `style_guide`
  - `app.current_project.master_bible`
  - `app.preset_registry`
  - `StageZeroManager._reverse_expander` (역설계 후 벡터화/DB 저장용 보관)
- Downstream contract:
  - `style_guide` 앵커는 `reference_excerpt`, `anti_ai_patterns`, `exemplary_passages`, `genre`를 포함할 수 있고, Stage 4가 이를 불러 Chief Writer 공통 컨텍스트로 사용한다.
  - `reference_excerpt`는 최대 `50,000자`이며 `style_guide.to_prompt()` 출력과 별도로 전달된다.
  - 스타일 캐시 파일은 `analysis_version`, `sampling_policy`, `prompt_contract_hash`, `reference_manifest_hash` 같은 provenance 메타를 담지만, Stage 4가 직접 소비하는 live contract는 `style_guide` 앵커와 `reference_excerpt` 본문이다.

## Dependencies
- Internal modules:
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage0/story_expander.py`
  - `modules/core/stage0/reverse_expander.py`
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage0/preset_registry.py`
  - `modules/core/project_manager.py`
  - `modules/core/db_manager.py`
- External services/models:
  - `StoryExpander` / `ReverseExpander`: Gemini 계열 LLM 호출 (`AIModels.SUMMARY_MODEL`, `AIModels.V50_MODULE_MODEL` 폴백 체인)
  - `StyleExtractor`: Gemini 계열 LLM 호출 (`AIModels.TIER_1_ARCHITECT`, `AIModels.EMERGENCY_FALLBACK`, `AIModels.SUMMARY_MODEL`)
  - optional VecMemory (`modules/core/vec_memory.py`)

## State and Cache
- Persistent state:
  - DB anchors: `bible`, `preset_state`, `style_guide`, `arcs`
  - 역설계 DB 테이블: `manuscripts`, `state_logs`, `episode_bibles`, `blueprints`
  - `stage0_output/*.json`은 export/복구용 사본이다. DB 저장 이후 운영 중 primary source는 DB anchors / tables 쪽이다.
- Runtime cache:
  - `StyleExtractor` 장르 캐시: `config/style_references/{genre}/style_guide.json`
  - `ReverseExpander.raw_drafts`, `episode_bibles`, `style_guide`
  - `StageZeroManager.load_state()` 로드 결과
- Invalidation rules:
  - 스타일 캐시는 `reference_manifest_hash`, `analysis_version`, `model_id`, `sampling_policy`, `prompt_contract_hash` 중 하나라도 달라지면 무효화된다.
  - Stage 0 스타일 분석은 `캐시 사용 / 캐시 무시 후 재분석 / 장르 캐시 삭제 후 재분석` 3모드를 가진다.
  - Stage 0 재실행 시 `bible`, `preset_state`, `style_guide` 앵커는 새 값으로 덮어쓴다.
  - `treatment_generated.json` / `treatment_extended.json`은 자동 무효화 메커니즘 없이 최신 실행 결과로 덮어쓴다.
  - 역설계 Arc stub은 기존 `arcs` anchor에 병합되며, 없는 `arc_no`만 append 후 stub enrich가 수행된다.

## Failure and Recovery
- Common failure patterns:
  - 컨셉/경로/JSON 미입력 또는 잘못된 입력.
  - LLM 호출 실패 또는 JSON 파싱 실패.
  - 비 UTF-8 원고 입력.
  - 역설계 DB 저장 트랜잭션 실패.
  - 스타일 캐시 로드 실패 또는 레퍼런스 폴더 부재.
- Recovery flow:
  - `StoryExpander` / `ReverseExpander`:
    - 2모델 폴백
    - 재시도 가능한 오류(429/503/timeout 등)에 한해 최대 3회 지수 백오프
  - `StyleExtractor`:
    - 3모델 폴백
    - `API_DELAY=0.5s`, 모델 간 1초 대기
    - per-model 지수 백오프 재시도는 없다
  - 역설계 파일 로딩:
    - `utf-8` → `cp949`
    - 둘 다 실패하면 `errors="replace"`로 진행하지 않고 조기 중단한다
  - `persist_to_db()`:
    - `begin()` → 다중 저장 → `commit()`
    - 실패 시 `rollback()`
- Fallback behavior:
  - Bible 생성 실패 시 Treatment 생성으로 진행하지 않고 조기 종료한다.
  - episode_bible 단건 추출 실패 시 최소 스키마(`hud_snapshot={}`, `changes=[]`, `new_npcs=[]`, `key_events=[]`)로 폴백 저장한다.
  - 스타일 레퍼런스 분석에서 LLM이 없으면 Python 통계/큐레이션 중심으로 축소 분석한다.
  - 레퍼런스 캐시 로드 실패 시 캐시를 버리고 재분석으로 진행한다.

## Manual Intervention Points
- User prompts:
  - `phase_0_recovery()` 서브메뉴 선택.
  - Stage 0 확장 메뉴 선택.
  - 장르 선택 / 자동 감지 여부.
  - 주인공 설정(`world_origin`, `incarnation_type`, `pov`).
  - 스타일 분석 시작 확인(`y/n`).
  - 블록 확장 개수 / 방향 힌트 / 배치 계속 여부.
  - 각 플로우 종료 후 `[Enter]` 복귀 입력.
- Approvals:
  - 별도 승인 시스템은 없고, 대부분 `input()` 기반 사용자 확인으로 분기한다.
- Operator checks:
  - 역설계 후 다음 시작점(`next_arc`, `next_blueprint`, `next_episode`) 로그.
  - 스타일 분석 후 `source_episode_count`, `source_char_count`, `reference_works`, `anti_ai_patterns` 개수 확인.
  - Bible 저장 후 `preset_state`, `style_guide` 앵커 저장 로그 확인.

## Metrics
- Throughput:
  - StoryExpander: 생성된 Treatment 블록 수, 저장 경로 로그.
  - ReverseExpander: 로드된 에피소드 수, 벡터화 성공 수, DB 저장 건수 로그.
  - StyleExtractor: 분석 회차 수 / 총 문자 수 / 샘플링 문자 수 로그.
- Error rate:
  - 전용 대시보드 없음.
  - 경고 로그 + `persist_to_db()` 결과 카운트 + 저장 실패 로그로 확인.
- Latency:
  - Story/Reverse 경로는 Spinner / ProgressBar로 진행률 표시.
  - StyleExtractor는 5단계(`통계`, `샘플 큐레이션`, `리듬`, `LLM 심층 분석`, `Anti-AI`) 로그를 출력한다.
  - 전용 PerfTimer나 집계형 latency baseline은 없다.

## Tests
- Unit:
  - `tests/test_stage0_fixes.py`
  - `tests/test_stage0_pov.py`
  - `tests/test_reverse_expander_g2.py`
  - `tests/test_sweep28.py`
- Integration:
  - `tests/test_stage01_helpers.py`
  - `tests/test_process_runner.py` (Stage 0 subkey contract)
- Regression:
  - `tests/test_stage01_fixes.py`

## Open Risks
- Risk 1:
  - Stage 0는 여전히 `input()` 중심 CLI 플로우라 비대화형 자동화나 API orchestration에 직접 연결하기 어렵다.
- Risk 2:
  - `reference_excerpt`는 Stage 0에서 최대 50,000자로 제한되지만, Stage 4 Chief Writer 공통 프롬프트에서는 이 필드만을 위한 별도 추가 절삭이 없다. 큰 레퍼런스는 downstream context pressure를 키울 수 있다.
- Risk 3:
  - 역설계가 저장하는 Arc/Blueprint는 stub 기반 복구 데이터다. Stage 2/3 재생성 없이 바로 운영 품질을 보장하지 않는다.
- Risk 4:
  - 작품 설정 / POV / preset 관련 UI가 `StageZeroManager`와 `Stage01Helpers.phase_0_recovery()` 경로에 나뉘어 있다. 한쪽만 바뀌면 operator-facing drift가 다시 생길 수 있다.
- Risk 5:
  - style provenance 메타와 operator-facing POV / style artifact가 동시에 갱신되지 않으면, 실제 Stage 4가 읽는 입력과 사람이 보는 Stage 0 결과가 어긋날 수 있다.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
