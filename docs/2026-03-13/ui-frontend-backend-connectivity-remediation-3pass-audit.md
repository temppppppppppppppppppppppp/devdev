# UI Frontend-Backend Connectivity Remediation 3PASS Audit

작성일: 2026-03-13
기준 문서:
- [ui-frontend-backend-connectivity-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md)

## Executive Summary

- 판정: `execution-ready`
- 최종 확신도: `95%`
- retained blocker: 없음

## Pass 1

사실 수집 결과:
- 현재 UI의 Stage 0 submenu는 backend 실제 mode와 어긋나 있다.
- backend는 `style cache mode`와 `work_guard library`를 이미 지원한다.
- desktop UI는 현재 그 두 기능을 일급 surface로 노출하지 않는다.
- focused regression도 이 축을 고정하지 못한다.

## Pass 2

교차 검증:
- UI 근거:
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- backend 근거:
  - [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
  - [stage0/__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py)
  - [style_extractor.py](C:/Users/User/Desktop/글도비/modules/core/stage0/style_extractor.py)
  - [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- desktop bridge 근거:
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
  - [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- test gate 근거:
  - [test_frontend_frontier_lag_wiring.py](C:/Users/User/Desktop/글도비/tests/test_frontend_frontier_lag_wiring.py)
  - [test_desktop_contract_refresh.py](C:/Users/User/Desktop/글도비/tests/test_desktop_contract_refresh.py)
  - [test_ui_renderer_sanitization.py](C:/Users/User/Desktop/글도비/tests/test_ui_renderer_sanitization.py)

## Pass 3

오탐 제거:
- `Frontier Lag key 7 dead path`는 현재 범위 아님
  - 이미 이전 remediation에서 닫힘
- `unsafe-inline`/monolith 구조 debt는 이번 실행 범위에서 직접 해결 대상이 아님
  - 이번 오더는 Stage 0 connectivity/UI contract 보강에 집중
- `work_guard raw YAML editor가 있으니 library UI는 불필요` 주장 기각
  - raw YAML 편집은 고급 경로일 뿐, root library 기반 선택형 준비물 흐름을 대체하지 못한다.

## Retained Execution Items

1. `R1` Stage 0 submenu realignment
2. `R2` style cache mode explicit UI/runner wiring
3. `R3` work_guard template library IPC + UI wiring
4. `R4` regression gate refresh

## Confidence Ledger

- `70`: 현행 UI/backend/test surface 인벤토리 완료
- `+10`: Stage 0 submenu drift를 UI/backend 양쪽에서 교차 확인
- `+10`: style cache/work_guard backend capability와 UI 미노출을 코드로 교차 확인
- `+5`: 범위를 Stage 0 connectivity/UI contract로 좁혀 과잉 실행 리스크 제거
- `+5`: 오탐 제거 완료
- `-5`: live desktop Stage 0 runtime을 실제로 끝까지 태운 증거는 아직 없음

최종 확신도: `95%`

## Final Judgment

- 문서는 `execution-ready`다.
- 이번 트랜치는 `프론트-백엔드 연결성` 관점에서 ROI가 높다.
- 수정 후에는 post-fix 3PASS와 전체 테스트 스위트로 닫는 것이 맞다.

