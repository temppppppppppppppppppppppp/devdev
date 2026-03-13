# 기본 POV + 타자 시점 삽입 정책 보강 Post-Fix 3PASS Closure

작성일: 2026-03-13  
기준 SSOT: `docs/2026-03-13/viewpoint-primary-pov-external-insert-remediation-execution-ssot.md`  
선행 감리: `docs/2026-03-13/viewpoint-primary-pov-external-insert-remediation-2pass-audit.md`

## Executive Summary

- 판정: `closed`
- 최종 확신도: `95%`
- 구현 범위:
  - `primary_pov`와 `external_pov_insert_policy` 분리 입력
  - Stage 0 style guide provenance 정리
  - planning / validation / observability 연결
- retained `P0 / P1 / P2`: 없음
- 남은 항목: `runtime-only observation` 1건

## Implemented Changes

### 1. Stage 0 POV taxonomy 분리

- Stage 0 주인공 설정에서 `pov`와 `external_pov_insert_policy`를 별도 입력하도록 보강했다.
- legacy Stage 0 흐름도 같은 정책을 저장하도록 맞췄다.
- 관련 파일:
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage01_helpers.py`

### 2. Style guide provenance 정리

- `StyleGuide`와 style cache meta에 아래 필드를 추가했다.
  - `extracted_pov`
  - `selected_primary_pov`
  - `effective_primary_pov`
  - `external_pov_insert_policy`
- cache key도 POV 계약 변화에 반응하도록 확장했다.
- 관련 파일:
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/project_support.py`

### 3. Planning / validation 연결

- Blueprint planning이 `primary_pov`와 `external_pov_insert_policy`를 함께 읽어 외부 시점 프리셋 사용 범위를 제어하도록 보강했다.
- Validation / Stage 2 preflight / prompt context도 새 정책을 읽게 맞췄다.
- 관련 파일:
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/core/prompt_builder.py`
  - `modules/core/stage2_preflight.py`

### 4. Stage 3 / 4 observability 보강

- Stage 3 summary와 Stage 4 episode summary에 아래 POV provenance를 남기도록 보강했다.
  - `primary_pov`
  - `external_pov_insert_policy`
  - `style_guide_extracted_pov`
  - `effective_pov`
- Director mandatory context에도 `타자 시점 삽입 정책`을 넣었다.
- 관련 파일:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/stage4_interview_round.py`

## Pass 1

- SSOT 기준으로 구현 범위를 대조했다.
- `혼합 POV 일반화`가 아니라 `기본 POV + 외부 시점 삽입 정책` 분리라는 핵심 의도가 코드에 반영됐는지 확인했다.
- Stage 0 입력, style guide artifact, planning contract, summary/log surface까지 한 체인으로 연결된 것을 확인했다.

## Pass 2

- 파일 간 교차 검증을 수행했다.
- Stage 0 입력값이 style cache meta로 들어가고, 그 provenance가 Stage 3/4 로그까지 이어지는지 확인했다.
- planning 계층에서 `1인칭 / 3인칭 / 혼합`과 `금지 / 제한적 허용 / 적극 허용`이 별도 축으로 취급되는지 확인했다.

## Pass 3

- 오탐과 과잉 구현 여부를 제거했다.
- `external_pov_segments_count`는 신뢰 가능한 계산 원천이 아직 없어 억지 숫자를 넣지 않았다.
- 대신 provenance 4종(`primary / policy / extracted / effective`)을 구조적으로 남기는 쪽으로 닫았다.
- 따라서 남은 항목은 기능 결함이 아니라 `runtime-only observation`으로 분류했다.

## Verification

- `python -m py_compile`
  - `modules/core/project_support.py`
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage01_helpers.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/core/prompt_builder.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
- focused regression 1차
  - `pytest -q tests/test_stage0_pov.py tests/test_stage01_helpers.py tests/test_stage0_work_guard_style_cache.py tests/test_project_support.py tests/test_viewpoint_primary_external_policy.py tests/test_stage4_interview_round.py tests/test_stage3_orchestrator.py tests/test_stage4_post_processor.py`
  - 결과: `222 passed`
- focused regression 2차
  - `pytest -q tests/test_stage3_orchestrator.py tests/test_stage4_post_processor.py tests/test_stage0_pov.py tests/test_stage01_helpers.py tests/test_stage0_work_guard_style_cache.py tests/test_project_support.py tests/test_viewpoint_primary_external_policy.py tests/test_stage4_interview_round.py tests/test_stage2_preflight.py tests/test_prompt_builder.py`
  - 결과: `290 passed`

## Residual Risk

- `runtime-only observation` 1건
  - `external_pov_segments_count`는 아직 실로그에 구조적으로 찍히지 않는다.
  - 현재는 신뢰 가능한 계산 원천이 없어 보수적으로 제외했다.
  - 따라서 숫자를 잘못 찍는 리스크는 없지만, 실제 런타임에서 외부 시점 삽입 빈도를 자동 집계하는 단계는 후속 tranche로 남는다.

## Confidence Ledger

- `70`: SSOT 범위 전체 구현 완료
- `+10`: Stage 0 입력 / style cache / planning / Stage 3/4 summary 체인 연결 확인
- `+10`: focused regression 290 passed
- `+5`: legacy Stage 0 흐름까지 같은 POV 정책 저장 규칙으로 정렬
- `+5`: provenance 4종 로그 반영으로 artifact drift 제거
- `-5`: `external_pov_segments_count`는 runtime-only observation으로 잔존
- 최종: `95`

## Final Judgment

- 이번 수정으로 `혼합 POV`와 `타자 시점 삽입`을 같은 개념으로 다루던 drift는 정리됐다.
- 현재 기준으로는 `기본 POV + 외부 시점 삽입 정책` 모델이 코드, artifact, summary 로그까지 일관되게 이어진다.
- 따라서 이번 remediation 범위는 `closed`로 본다.
