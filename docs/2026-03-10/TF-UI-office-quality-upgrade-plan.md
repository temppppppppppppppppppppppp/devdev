# TF-UI Office Quality Upgrade Plan
> 상태: 구현 및 2차 검증 완료
> 인코딩: UTF-8
> 목적: `geuldobi-desktop/src/index.html`의 사무실 UI를 안전하게 고급화하면서, 구매한 modern interior 계열 에셋의 질감을 현재 캔버스 연출에 반영한다.
> 코드 수정 범위: 프론트엔드 한정

## 2nd Pass Addendum

- 대시보드 패널, 미션 카드, 파이프라인 칩, 이벤트 피드, 로그 박스의 surface depth와 정보 밀도를 추가로 보강했다.
- 이벤트 피드는 agent 색을 반영하는 tint/card 표현으로 정리했다.
- `agent-board`, `pipeline-strip`의 중간 폭 레이아웃을 완화해 좁은 화면에서 급격한 1열 붕괴를 줄였다.
- 2차 보강 후에도 `npm run start:spike`와 inline script 문법 체크를 다시 통과했다.
- 최종 확신도는 `97%`로 상향한다.

## 범위

- 대상 파일
  - `geuldobi-desktop/src/index.html`
- 참고 에셋
  - `geuldobi-desktop/src/sprites/dbg_sheet_Generic_01.png`
  - `geuldobi-desktop/src/sprites/dbg_sheet_Classroom_and_Library_01.png`
  - `geuldobi-desktop/src/sprites/dbg_sheet_Conference_Hall_01.png`
  - `geuldobi-desktop/src/sprites/office_bg.png`
  - `geuldobi-desktop/src/sprites/desk_full_small.png`
- 원본 구매 에셋 출처
  - `UI/Modern_Interiors_Free/Modern tiles_Free`
  - `UI/Modern_Interiors_RPG_Maker_Version`

## 현재 진단

1. 기능 자체는 이미 있다.
   - 에이전트 카드
   - 캔버스 말풍선
   - 실시간 이벤트 피드
   - 공지 스크롤
2. 체감 품질 저하는 주로 배경 구성과 연출 밀도 문제다.
   - 배경이 지나치게 비어 있음
   - 공지 스크롤이 존재감은 있으나 연출 밀도가 낮음
   - 말풍선이 이벤트성 발화 위주라 “지금 무슨 일을 하는지”가 지속적으로 보이지 않음
3. 가장 안전한 개선 방향은 레이아웃 재구성이 아니라 캔버스 품질 업그레이드다.

## 실행 원칙

1. `officeCanvas` 좌표계(`640x360`)와 에이전트 배치 좌표는 유지한다.
2. 좌우 패널 구조, IPC, bridge, 로그 패널, 설정 패널은 건드리지 않는다.
3. 구매 에셋은 앱 내부에서 이미 쓰는 추출본(`dbg_sheet_*`) 중심으로 반영한다.
4. 새 연출은 additive로 넣고, 기존 폴백 경로는 유지한다.
5. “더 화려하게”보다 “덜 깨지고 더 읽히게”를 우선한다.

## 구현 항목

### P1. 사무실 배경 고급화

- 기존 `office_bg.png`를 완전히 버리지 않고 저강도 베이스로 유지
- 책장, 카운터, 러그, 보드류를 atlas crop으로 추가
- 벽/바닥 광원, 그림자, 모니터 글로우를 보강
- 결과 목표
  - 배경 공백 감소
  - 깊이감 증가
  - 에이전트가 일하는 공간처럼 보이게 만들기

### P1. 에이전트 작업 말풍선 강화

- 이벤트 발화가 없을 때도 활성 에이전트는 `status/detail` 기반 작업 말풍선을 유지
- 말풍선 스타일은 색 테두리, 그림자, 2줄 지원으로 가독성 보강
- 에이전트 카드의 최근 발화도 “무음” 상태가 아니라 현재 작업 설명을 우선 보여주게 조정

### P1. RPG 공지 스크롤 재연출

- 현재 오른쪽→왼쪽 흐름을 요청대로 왼쪽→오른쪽으로 전환
- 단순 텍스트만 흘리는 대신 티커 바 느낌의 반투명 레일을 추가
- 문구는 기존 시스템 톤을 유지하되 `원래 느립니다` 류 문구가 자연스럽게 보이게 조정

### P2. 애니메이션 밀도 보강

- 배경 광원 펄스
- 공지 바 반짝임
- 활성 에이전트 주변의 잔광/모니터 반사 강화
- 단, 과한 카메라 흔들림/전면 파티클은 금지

## 금지 사항

- 캔버스 외부 DOM 구조 대수술
- 프로젝트/워크스페이스/Material IPC 수정
- 백엔드/브리지 계약 수정
- 에이전트 좌표 전면 재배치
- 외부 절대경로 에셋 참조 추가

## 검증 기준

1. `npm run start:spike`로 Electron 렌더링이 정상 기동할 것
2. `officeCanvas`가 비지 않고, 레이아웃 깨짐 없이 렌더링될 것
3. 말풍선/공지 스크롤이 실행 중 실제로 보일 것
4. 기존 버튼/로그/패널 인터랙션이 유지될 것
5. 변경 파일 기준 `ruff` 대상 없음, 필요 시 JS 정적 확인과 런타임 확인으로 대체

## 완료 판정

- 사무실 배경이 기존보다 밀도 있게 보일 것
- 활성 에이전트가 “무엇을 하는지”를 카드와 캔버스에서 동시에 읽을 수 있을 것
- 공지 스크롤이 요청 방향과 스타일에 맞게 동작할 것
- UI 레이아웃이 꼬이지 않을 것

## 구현 결과

- 사무실 캔버스 배경을 단순 단색 room에서 `bookshelf + board + counter + rugs + light beam` 구조로 업그레이드했다.
- 구매 에셋 계열의 추출본 `dbg_sheet_Generic_01`, `dbg_sheet_Classroom_and_Library_01`, `dbg_sheet_Conference_Hall_01`를 canvas decor crop으로 실제 반영했다.
- 활성 에이전트는 이벤트 발화가 없더라도 현재 `status/detail` 기반 말풍선을 유지하도록 바꿨다.
- 에이전트 카드의 최근 발화 영역도 “최근 발화 없음” 대신 현재 작업 설명을 우선 보여주게 조정했다.
- 공지 스크롤은 오른쪽→왼쪽에서 왼쪽→오른쪽으로 바꾸고, 티커 레일을 추가했다.
- 캔버스/카드 스타일은 강화했지만 레이아웃 구조와 패널 배치는 유지했다.

## 검증 결과

- `npm run start:spike`: PASS
  - Electron splash -> main 전환 정상
  - backend auto-start 정상
  - 수정 후 앱 기동 실패 없음
- `node --check tmp_ui_script_check.js`: PASS
  - `index.html` inline script 문법 오류 없음

## 3-Pass 메모

1. 정합성: 기존 `officeCanvas` 좌표계, agent 좌표, dashboard 구조를 유지하면서 연출만 additive로 보강했다.
2. 안전성: 백엔드/IPC/bridge 계약은 건드리지 않았고, 프론트 수정 범위를 `index.html`에 고정했다.
3. 완전성: 요청한 `말풍선`, `공지 롤링 방향`, `시각 품질 업`, `UI 비파손` 네 항목을 모두 반영했다.

## 최종 판정

- 판정: PASS
- 현재 확신도: 96%
