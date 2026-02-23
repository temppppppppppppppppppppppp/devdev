# Stage 0-4 코드 전수 조사 보고서 (2026-02-21)

## 1) 조사 범위와 방식
- 조사 일자: 2026-02-21
- 범위: Stage 0~4 실행 경로와 관련 모듈 전체
- 방식: `rg`는 파일 탐색/네비게이션에만 사용, 근거는 대상 파일 수동 열람으로만 확보
- 검증: 아래 validator 3개 모두 PASS
  - `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --allow-empty`
  - `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100`
  - `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`

## 2) 구조 파악 (진입점 -> Stage 오케스트레이션)
- 메뉴 분기와 Stage 호출 진입점
  - `main_a.py:1837` 메뉴 구성, `main_a.py:1852`~`main_a.py:1869` Stage 0~4 분기
- Stage별 thin delegate
  - Stage 0/1: `main_a.py:2108`, `main_a.py:2116`
  - Stage 2: `main_a.py:2184` (DI 주입 `main_a.py:2189`~`main_a.py:2192`)
  - Stage 3: `main_a.py:2418` (DI 주입 `main_a.py:2423`~`main_a.py:2427`)
  - Stage 4: `main_a.py:2894` (DI 주입 `main_a.py:2955`~`main_a.py:2989`)
- 오케스트레이터 생성
  - `main_a.py:189`~`main_a.py:191`에서 Stage2/3/4 orchestrator 인스턴스 보유

## 3) 라운드별 수동 조사 기록

### Round 1: Stage 0/1
- 대상 파일
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage0/preset_registry.py`
  - `modules/core/stage0/reverse_expander.py`
  - `modules/core/stage0/story_expander.py`
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage0/spinner.py`
- 수동 근거
  - Stage 0 dispatcher가 모드별 핸들러를 명시적으로 분기하고 결과 저장을 단일 경로로 모읍니다 (`modules/core/stage01_helpers.py:278`~`modules/core/stage01_helpers.py:320`).
  - Stage 1은 skip/진행 분기를 갖고, `plot_roadmap` 복구 시도 후 volume planning 루프로 들어갑니다 (`modules/core/stage01_helpers.py:498`~`modules/core/stage01_helpers.py:577`).
  - StageZeroManager가 Stage0 개념생성/역설계/임포트/스타일분석을 통합 관리합니다 (`modules/core/stage0/__init__.py:39`~`modules/core/stage0/__init__.py:289`).
- Bug-vs-intent 판단
  - Stage0/1 분기와 저장 흐름은 의도적으로 분리/위임된 구조로 보이며, 즉시 결함으로 확정할 로직 충돌은 확인되지 않았습니다.

### Round 2: Stage 2
- 대상 파일
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_optimizer.py`
- 수동 근거
  - Stage2는 preflight/validation/finalizer를 lazy submodule로 분리해 orchestration 본문에서 조립 호출합니다 (`modules/core/stage2_orchestrator.py:56`~`modules/core/stage2_orchestrator.py:80`, `modules/core/stage2_orchestrator.py:397`, `modules/core/stage2_orchestrator.py:490`, `modules/core/stage2_orchestrator.py:517`).
  - 배치 처리 루프에서 enrichment 실패 복구, 재시도, 수동개입 분기까지 포함해 안전장치를 둡니다 (`modules/core/stage2_orchestrator.py:267`~`modules/core/stage2_orchestrator.py:333`, `modules/core/stage2_orchestrator.py:591`~`modules/core/stage2_orchestrator.py:757`).
- Bug-vs-intent 판단
  - 재시도/복구/수동개입은 명시적 의도(안전 중심)로 보이며, 설계와 구현 사이의 직접 충돌 결함은 본 라운드에서 확정하지 않았습니다.

### Round 3: Stage 3
- 대상 파일
  - `modules/core/stage3_context.py`
  - `modules/core/stage3_orchestrator.py`
- 수동 근거
  - Stage3는 DI context + lazy init(state_tracker/world_state/fact_ledger) 후 episode loop를 수행합니다 (`modules/core/stage3_orchestrator.py:56`~`modules/core/stage3_orchestrator.py:91`, `modules/core/stage3_context.py:87`~`modules/core/stage3_context.py:111`).
  - 단일 에피소드 처리에서 arc context 검증 -> blueprint 생성 -> 성공/실패 핸들러로 닫는 구조입니다 (`modules/core/stage3_orchestrator.py:238`~`modules/core/stage3_orchestrator.py:329`, `modules/core/stage3_orchestrator.py:397`~`modules/core/stage3_orchestrator.py:461`, `modules/core/stage3_orchestrator.py:466`~`modules/core/stage3_orchestrator.py:574`).
- Bug-vs-intent 판단
  - 아래 `BUG-01`은 호출 계약(caller-callee) 불일치가 확인되어 버그로 분류했습니다.

### Round 4: Stage 4
- 대상 파일
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/stage4_types.py`
- 수동 근거
  - Stage4는 context_builder/interview_round/post_processor를 lazy init으로 분리하고, 메인 loop에서 순차 조립 실행합니다 (`modules/core/stage4_orchestrator.py:195`~`modules/core/stage4_orchestrator.py:217`, `modules/core/stage4_orchestrator.py:274`~`modules/core/stage4_orchestrator.py:515`).
  - interview round는 생성 -> Python 검증 체인 -> Director 판정 -> PASS/REJECT 후속처리를 단일 메서드에서 닫습니다 (`modules/core/stage4_interview_round.py:15`~`modules/core/stage4_interview_round.py:790`).
  - PASS 후처리는 DB 저장/커밋, HUD 업데이트, Episode Bible 및 메타 동기화를 수행합니다 (`modules/core/stage4_post_processor.py:99`~`modules/core/stage4_post_processor.py:645`).
- Bug-vs-intent 판단
  - 아래 `BUG-02`는 입력 경계 계약 위반이 확인되어 버그로 분류했습니다.

### Round 5: 상위 통합(main_a)
- 대상 파일
  - `main_a.py`
  - `modules/core/services/ui_service.py`
- 수동 근거
  - Stage3/4 진입 전 사용자 입력 범위를 main_a/오케스트레이터가 결정하고, 실제 검증은 UIService에 위임합니다 (`main_a.py:2418`~`main_a.py:2427`, `main_a.py:2894`~`main_a.py:2989`).
  - UIService 입력 함수는 빈 입력 시 min/max 검증 없이 default를 즉시 반환합니다 (`modules/core/services/ui_service.py:116`~`modules/core/services/ui_service.py:117`).
- Bug-vs-intent 판단
  - min/max 역전 상황을 호출자가 만들 수 있고, 수신자가 이를 방어하지 않으므로 계약 결함으로 판단했습니다.

## 4) 확정 이슈

### BUG-01 (Major): Stage 3 목표 입력 범위 역전 가능
- 증거
  - Caller: `modules/core/stage3_orchestrator.py:113`~`modules/core/stage3_orchestrator.py:118`
    - `min_val=production_head + 1`, `max_val=total_planned_ep`
  - Callee: `modules/core/services/ui_service.py:116`~`modules/core/services/ui_service.py:117`
    - 빈 입력 시 범위 검증 없이 `default` 즉시 반환
- 계약 추적
  - `Stage3Orchestrator.stage_3_batch_blueprinting()` -> `ctx.get_int_input(...)` -> `UIService.get_int_input(...)`
- 영향
  - `production_head >= total_planned_ep`인 경우 사용자에게 역전 범위(min > max) 프롬프트가 제시될 수 있습니다.
  - 결과적으로 의도와 다르게 0회 루프 종료/혼란스러운 UX가 발생할 수 있습니다.
- 버그 판정 근거
  - "완료 상태면 조기 종료" 또는 "입력 범위 정상화" 둘 중 하나가 필요하지만 현재 둘 다 보장되지 않습니다.

### BUG-02 (Major): Stage 4 limit mode에서 target 입력 범위 역전 가능
- 증거
  - Caller: `modules/core/stage4_orchestrator.py:702`, `modules/core/stage4_orchestrator.py:706`~`modules/core/stage4_orchestrator.py:712`
    - `total_planned_ep = get_latest_blueprint_number()` 기반으로 `min_val=1`, `max_val=total_planned_ep`
  - Callee: `modules/core/services/ui_service.py:116`~`modules/core/services/ui_service.py:117`
    - 동일하게 빈 입력 시 범위 검증 생략
- 계약 추적
  - `Stage4Orchestrator._prepare_stage4_session(limit_mode=True)` -> `ctx.get_int_input(...)` -> `UIService.get_int_input(...)`
- 영향
  - 블루프린트가 0개일 때(`total_planned_ep == 0`) 입력 범위가 역전되고 UX/흐름이 불안정해집니다.
- 버그 판정 근거
  - 호출부가 역전 범위를 만들 수 있고 수신부가 이를 방어하지 않으므로 명확한 입력 계약 결함입니다.

## 5) 리스크 (의도 확인 필요)

### RISK-01: StateTracker 초기화 경로가 Stage2/3/4에 분산
- 근거
  - Stage2: `modules/core/stage2_orchestrator.py:163`~`modules/core/stage2_orchestrator.py:179`
  - Stage3: `modules/core/stage3_orchestrator.py:175`~`modules/core/stage3_orchestrator.py:196`
  - Stage4: `main_a.py:2903`~`main_a.py:2918`
- 리스크 설명
  - 정상 순차 실행에서는 큰 문제 없지만, 개별 Stage 진입/테스트 시 초기화 경로가 분산되어 상태 일관성 추적 난도가 올라갑니다.
- 오픈 질문
  - Stage별 독립 실행을 공식 지원하는지 여부에 따라 리팩터링 우선순위가 달라집니다.

### RISK-02: Stage2 async 루프 내부의 동기 `input()`
- 근거
  - `modules/core/stage2_orchestrator.py:691`, `modules/core/stage2_orchestrator.py:720`
- 리스크 설명
  - 대화형 CLI에서는 의도일 수 있으나, 비대화형/자동화 실행 환경에서는 event loop block 원인이 될 수 있습니다.

## 6) 전수 조사 파일 목록
- `main_a.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/preset_registry.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/stage0/spinner.py`
- `modules/core/stage0/story_expander.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_types.py`
- `modules/core/services/ui_service.py`

## 7) 요약
- Stage 0~4 구조/호출 체인은 정상적으로 분리되어 있으며, Stage2/3/4는 DI context 기반 orchestrator 구조가 명확합니다.
- 확정 버그는 입력 범위 계약 관련 2건(BUG-01, BUG-02)입니다.
- 코드 수정은 이번 턴에서 적용하지 않고, 조사 결과만 문서화했습니다.
