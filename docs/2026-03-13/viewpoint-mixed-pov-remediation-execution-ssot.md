# 시점·혼합 시점 보강 실행 SSOT

작성일: 2026-03-13  
기준 문서: `viewpoint-mixed-pov-full-survey-3pass-final-audit.md`  
상태: `execution-ready`

## Summary
- 목표는 `시점 체계를 깨지 않고`, 특히 `혼합 시점`을 Stage 0~4 전 구간에서 SSOT로 정리하는 것이다.
- 이번 수정 범위는 retained finding만 친다.
- 비목표는 `전 작품 프롬프트 전면 개편`, `문체 철학 재정의`, `혼합 시점 강제 기본값화`다.

## 해결 대상

### R-1. Stage 0 POV SSOT hardening
- 목표:
  - 사용자 선택 POV가 `Stage 0 artifact`에 명시적으로 남게 한다.
  - reference-derived POV와 user-selected POV를 섞어 쓰지 않는다.
- 구현 방향:
  - `style_guide.json`에 최소 `selected_pov`, `extracted_pov`, `effective_pov` 3층을 구분
  - 또는 raw `pov`를 effective POV로 승격하고, extracted POV는 별도 meta 필드로 보존
  - 스타일 캐시 메타에 `requested_pov`를 포함하여 동일 장르 cache라도 POV drift를 숨기지 않게 한다
- 수용 기준:
  - 전지적/3인칭/혼합 프로젝트를 만들어도 `stage0_output/style_guide.json`이 전부 1인칭으로 찍히지 않는다
  - Stage 4 runtime override warning은 정상 mismatch 상황에서만 뜬다

### R-2. 혼합 시점 planning contract 명시화
- 목표:
  - `혼합` POV를 planning 계층에서 독립 규칙으로 다룬다.
- 구현 방향:
  - `modules/domain/agents/blueprint_ensemble.py`에 `_pov == "혼합"` 전용 분기 추가
  - 규칙은 최소 아래를 포함
    - 씬 단위 전환 허용
    - 동일 씬 내 POV 혼합 금지
    - `villain_scheme`/`side_glimpse`/`omniscient_hint`의 사용 조건 명시
    - protagonist scene, side character scene, omniscient hint의 경계 정의
  - `config/prompts/ensemble.yaml`과 planning prompt도 이 규칙과 충돌하지 않게 맞춘다
- 수용 기준:
  - mixed POV 프로젝트는 planning 단계부터 scene-level switching contract를 받는다
  - non-mixed 프로젝트는 불필요한 시점 전환 프리셋에 덜 노출된다

### R-3. 혼합 시점 위반 escalation
- 목표:
  - `same-scene mixed POV`가 warning만 남기고 지나가지 않게 한다.
- 구현 방향:
  - `PreLLMValidator`와 `ChiefWriterQualityGate`의 mixed POV 위반을 configurable escalation 대상으로 승격
  - 최소한 `동일 씬 블록 내 1인칭/3인칭 혼재`는 `PASS_WITH_FIX` 또는 reject candidate로 연결
  - Director review에도 `POV violation`을 별도 라벨로 노출
- 수용 기준:
  - mixed POV 작품에서 `씬 구분자 없음 + 1/3인칭 혼재`가 더 이상 advisory-only로 끝나지 않는다

### R-4. Observability 보강
- 목표:
  - 나중에 POV 문제가 나왔을 때, 로그와 산출물만으로 원인을 복원할 수 있게 한다.
- 구현 방향:
  - episode/attempt summary에 `selected_pov`, `style_guide_pov`, `effective_pov`, `pov_warning_count`를 남긴다
  - mixed POV violation은 `validator`/`Director`/`final summary`에서 같은 라벨을 공유한다
- 수용 기준:
  - DB/로그만 읽어도 `어떤 시점을 의도했고`, `어떤 시점이 실제 적용됐는지` 복원 가능

## 제외 범위
- `1인칭/3인칭/전지적` 전체 prompt 철학 재정의
- Stage 4 원고 톤 전체 개편
- 레퍼런스 corpus 교체 자체
- UI surface 변경  
  단, backend 필드가 바뀌면 후속 UI 반영은 별도 tranche로 처리

## Public APIs / Interfaces / Types
- 외부 API를 깨지 않는 방향이 기본이다.
- 허용되는 내부 계약 추가:
  - style guide meta에 POV provenance 필드 추가
  - validator/advisory payload에 POV violation code 추가
  - episode summary/log에 POV provenance 필드 추가

## Verification Scenarios
- `혼합` 프로젝트 생성 -> Stage 0 완료 -> `stage0_output/style_guide.json`이 1인칭으로 고정되지 않는지
- `3인칭` 프로젝트 생성 -> Stage 0 완료 -> `effective_pov=3인칭`으로 정합한지
- mixed POV blueprint planning에서 `scene-level switching` 규칙이 prompt/plan에 반영되는지
- mixed POV manuscript에서
  - `***` 없는 혼합 -> escalation
  - `***` 있는 scene-level switching -> 통과
- Stage 4 로그/summary에서 selected/style/effective POV가 모두 복원 가능한지

## Assumptions
- 작품별 POV 선택은 계속 `선택형`이다
- `혼합 시점`은 유지 대상이지 제거 대상이 아니다
- reference-derived POV는 보조 근거일 뿐, 사용자 선택 POV보다 상위 SSOT가 아니다
