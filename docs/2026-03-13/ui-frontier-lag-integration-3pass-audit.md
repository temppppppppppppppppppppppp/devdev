# UI Frontier Lag Integration 3Pass 감리

작성일: 2026-03-13  
대상 SSOT: `docs/2026-03-13/ui-frontier-lag-integration-execution-ssot.md`

## Executive Summary

- 감리 결과: `execution-ready`
- 핵심 결론:
  - `backend / engine`은 이미 준비되어 있다.
  - 이번 작업의 본질은 `desktop UI semantics` 정렬이다.
  - `build`와 `1.9.0`은 이번 범위에서 빼는 것이 맞다.
- 최종 확신도: `95%`

## Pass 1: 사실 수집

확인한 사실은 아래와 같다.

- `main_a.py`에는 이미 `7`이 있다.
  - `main_a.py:2144`
  - `main_a.py:2177`
- desktop 실행 패널은 아직 `key 6`만 노출한다.
  - `geuldobi-desktop/src/index.html:2776-2777`
- renderer는 `runKey(key, subKey, inputs)`로 key를 그대로 넘긴다.
  - `geuldobi-desktop/src/index.html:6528`
  - `geuldobi-desktop/src/preload.js:10-12`
- process runner는 mode B에서 key를 stdin에 그대로 넣는다.
  - `modules/api/process_runner.py:583-597`
- UI 메타와 pipeline surface는 현재 `one_stop` 하나만 안다.
  - `geuldobi-desktop/src/index.html:3561`
  - `geuldobi-desktop/src/index.html:3578`
  - `geuldobi-desktop/src/index.html:3475`

## Pass 2: 설계 적합성 검증

### 1. bridge 수정 필요 여부

- `불필요`
- 이유:
  - `runKey`가 이미 generic key payload를 전달한다.
  - `process_runner`도 key를 문자열로 그대로 넣는다.
  - 따라서 `7` 지원을 위해 API surface를 추가할 필요가 없다.

### 2. UI action 분리 필요 여부

- `필요`
- 이유:
  - 기능만 보면 `data-key="7"` 한 줄로 실행 가능할 수 있다.
  - 하지만 desktop은 `ACTION_META`, `PIPELINE_ORDER`, `currentStage`, `manager bubble`이 action명을 기준으로 굴러간다.
  - 따라서 action을 `one_stop`로 재사용하면 `Frontier Lag` 실행 중에도 UI는 `One-Stop`으로만 보일 가능성이 높다.

### 3. build / version bump 포함 여부

- `제외가 맞다`
- 이유:
  - 이번 요청은 `우선 오더 문서부터, 문서는 3pass 감리 기준으로 완성`이다.
  - 현재 실제 작업 범위는 UI semantics 연결이다.
  - build/version은 별도 오더로 분리해야 문제 원인과 검증 신호가 흐려지지 않는다.

## Pass 3: 오탐 제거

다음은 이번 문서에서 제외하는 것이 맞다.

- `main_a.py` 기능 변경
  - 이미 구현 완료 상태이므로 UI integration 문서 범위가 아니다.
- `process_runner` API 확장
  - 현재 구조상 필요 없다.
- packaged build / installer smoke
  - 이번 오더 범위 바깥이다.
- `One-Stop key 6` 의미 변경
  - 기존 모드 보존이 SSOT와 합치한다.

## Retained Execution Items

### E-1. 버튼 추가

- retained
- 이유:
  - 현재 사용자는 `7`을 UI에서 누를 수 없다.

### E-2. ACTION_META / pipeline semantics 추가

- retained
- 이유:
  - UI가 `Frontier Lag`를 `One-Stop`와 구분하지 못하면 semantics drift가 생긴다.

### E-3. desktop smoke / regression 추가

- retained
- 이유:
  - 이번 작업은 renderer semantics가 핵심이라, 최소 smoke가 없으면 regressions를 막기 어렵다.

## Rejected Overreach

- `bridge contract 변경`
- `process_runner 새 mode 추가`
- `1.9.0 버전 업`
- `build 실행`

위 네 항목은 현재 SSOT 목적에 비해 과하다.

## Confidence Ledger

- `70`: current UI / bridge / process runner baseline 재확인
- `+10`: `7`이 이미 backend에 구현돼 있고 desktop은 semantics gap만 남았음을 확인
- `+10`: UI action 분리 필요성과 bridge 비수정 원칙을 근거로 고정
- `+5`: build/version 범위를 분리해 과잉 범위를 제거
- 최종: `95`

## Final Judgment

- 현재 문서는 충분히 좁고, 구현 순서도 명확하다.
- 남은 작업은 `index.html` 중심의 UI wiring과 desktop smoke다.
- 따라서 본 문서는 `execution-ready / 95% confidence`로 확정한다.

## Notes

- 이번 턴은 문서화와 3-pass 감리만 수행했다.
- 코드 수정, 테스트 실행, build, 버전 변경은 하지 않았다.
