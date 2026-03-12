# UI 문의사항 답변 및 FE-BE 연계 전수조사

작성일: 2026-03-12

## 범위

- 화면 증거: `C:\Users\User\Desktop\글도비\00000000000.png`
- 프론트엔드: `geuldobi-desktop/src/index.html`, `geuldobi-desktop/src/main.js`, `geuldobi-desktop/src/preload.js`
- 브리지/백엔드: `modules/api/bridge_server.py`, `main_a.py`, `modules/core/genre_guards/work_guard.py`, `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_interview_round.py`, `modules/core/project_manager.py`, `config/models.yaml`
- 이번 문서는 답변 문서다. 코드 수정은 하지 않았다.

## Executive Summary

1. `Artifact Ladder` 하단이 안 보이는 문제는 실제 구조 문제다.
   `Artifact Ladder`가 `사무실` 패널 내부 하단에 붙어 있는데, 우측 컬럼과 페이지 전체가 `overflow: hidden`이고 `사무실` 패널 자체 스크롤이 없다. 로그를 접어도 우측 컬럼 전체를 스크롤할 수 없어서 아래쪽이 잘린다.

2. `사무실`이 세로로 짧고 못생겨진 이유도 확인됐다.
   현재 `사무실` 캔버스 하나가 아니라, 캔버스 + 미션 카드 + Quality Radar + Artifact Ladder + Retrieval + Result Summary + Trend + Agent Board + Event Feed가 모두 같은 패널에 세로 적층돼 있다. 그래서 캔버스가 먹는 높이가 줄어든다.

3. 모델 기본값에 대한 질문에는 이렇게 답할 수 있다.
   백엔드 실제 기본값은 `chief_writer`, `director`, `analyst` 모두 `gemini-2.5-pro`가 맞다. 다만 UI 모델 탭은 현재 런타임에 연결되지 않았다. 즉 "표시는 맞는데, UI에서 바꿔도 실제 적용은 안 되는 상태"다.

4. 작품가드(`work_guard.yaml`) 입력 기회는 현재 "있긴 있다". 하지만 위치가 좋지 않다.
   `재료 넣기` 패널에는 없고, `설정 > 프로젝트` 탭에서만 편집 가능하다. 백엔드는 그 파일을 실제로 읽고 Stage 2/3/4 컨텍스트와 Guard 체인에 반영한다. 따라서 "백엔드는 wired, 프론트 노출 위치는 부적절"이 현재 판정이다.

5. 가장 ROI 높은 개선은 UI 개편이 아니라 구조 개편이다.
   우선순위는 `우측 컬럼 스크롤/분리`, `사무실 접기/전체화면화`, `실행 패널 기본 접힘`, `작품가드 입력 진입점 상향`, `모델 탭 wiring 또는 read-only화` 순이 타당하다.

## 1. Artifact Ladder가 밑에 안 보이는 문제

### 현재 사실

- 페이지 전체가 `height: 100dvh` + `overflow: hidden`이다. `geuldobi-desktop/src/index.html:27`
- 메인 레이아웃의 우측 컬럼도 `overflow: hidden`이다. `geuldobi-desktop/src/index.html:94`
- `Artifact Ladder`는 독립 페이지가 아니라 `사무실` 패널 내부의 `quality-insight-grid` 첫 블록이다. `geuldobi-desktop/src/index.html:2660`
- `Artifact Ladder` 카드는 기본 5열이고, 각 카드가 `min-height: 128px`다. `geuldobi-desktop/src/index.html:534`
- 로그 패널 접기는 로그 영역만 숨긴다. 우측 컬럼이나 `사무실` 패널에 스크롤을 추가하지는 않는다. `geuldobi-desktop/src/index.html:1330`, `geuldobi-desktop/src/index.html:6393`

### 판단

- 문제는 재현 가능하고 구조적으로 확인된다.
- 원인은 `Artifact Ladder` 자체가 아니라 "우측 메인 영역이 스크롤 불가인 상태에서 너무 많은 블록이 한 패널에 몰려 있는 설계"다.
- 따라서 로그만 접는 것으로는 해결되지 않는다.

### 권장 방향

우선순위는 아래 순서가 맞다.

1. `우측 컬럼` 또는 `사무실 패널 본문`에 내부 세로 스크롤을 준다.
2. `Artifact Ladder`를 `사무실` 내부 공존 패널로 두지 말고, 최소한 독립 섹션으로 분리한다.
3. 더 강하게 가려면 `Office / Quality / Ops`를 별도 페이지 또는 상단 탭으로 분리한다.

내 판단으로는 단기 해법은 `우측 컬럼 스크롤 + 접기`, 중기 해법은 `별도 페이지/탭 분리`다.

## 2. 사무실 높이가 짧아지고 못생겨진 문제

### 현재 사실

- `사무실` 패널은 `canvas-wrap` 하나만 있는 구조가 아니다. `canvas` 아래에 `office-dashboard` 전체가 연속으로 붙어 있다. `geuldobi-desktop/src/index.html:2613`
- `canvas-wrap`은 `flex: 1`이지만 `min-height: 200px`만 보장한다. `geuldobi-desktop/src/index.html:185`
- 같은 패널 안에 `mission-grid`, `pipeline-strip`, `quality-radar`, `quality-insight-grid`, `agent-board`, `live-feed`가 모두 들어 있다. `geuldobi-desktop/src/index.html:2625`

### 판단

- 사용자가 느낀 "사무실 세로 길이가 짧아졌다"는 인상이 맞다.
- 원인은 캔버스 자체 퀄리티보다, `사무실`이 더 이상 "대표 비주얼 패널"이 아니라 "우측 전체 대시보드 컨테이너"로 변했기 때문이다.

### 권장 방향

사용자 제안 중에서는 아래가 가장 타당하다.

1. `사무실`은 기본 접힘
2. 펼치면 나머지 우측 정보를 덮는 확장형 뷰
3. 접힌 상태에서는 우측 정보 섹션을 세로로 더 많이 노출
4. 우측 컬럼은 스크롤 가능

추가로, 별도 페이지안도 충분히 타당하다.

- `Run` 페이지: 실행 패널 + 로그
- `Office` 페이지: 사무실 캔버스 몰입형
- `Quality` 페이지: Artifact Ladder / Retrieval / Result Summary / Trend
- `Ops` 페이지: Safe Ops / Wipe / Reset / Rollback

내 판단은 `사무실 오버레이/확장형`이 단기적으로 가장 싸고, `별도 페이지화`가 장기적으로 가장 깔끔하다.

## 3. 모델 기본값이 전부 2.5 pro인지 재확인

### 현재 사실

- 실제 백엔드 설정 파일에서 다음 3개는 모두 `gemini-2.5-pro`다.
  - `analyst`: `config/models.yaml:26`
  - `chief_writer`: `config/models.yaml:28`
  - `director`: `config/models.yaml:37`
- UI 모델 탭도 이 셋을 모두 `gemini-2.5-pro` 선택 상태로 렌더링한다. `geuldobi-desktop/src/index.html:2890`
- 추천 설정 버튼도 셋 다 `pro`로 고정한다. `geuldobi-desktop/src/index.html:6877`

### 중요한 보정

- 시스템 전체가 "전부 2.5 pro"는 아니다.
- 예를 들어 `manager`, `critic`, `block_enricher`, `state_extractor` 등은 `gemini-2.5-flash`다. `config/models.yaml:27`, `config/models.yaml:32`, `config/models.yaml:33`, `config/models.yaml:43`

### 더 중요한 판정

- UI 모델 탭은 현재 `config/models.yaml`을 실제로 수정하지 않는다.
- 저장 로직은 `apiKey`, `slackWebhook`, timeout류, `author_directives`, `work_guard.yaml`만 저장한다. 모델 셀렉터 값은 저장 payload에 들어가지 않는다. `geuldobi-desktop/src/index.html:6885`
- Electron main/preload에도 `models.yaml` 저장/로드 IPC가 없다. `geuldobi-desktop/src/preload.js:27`, `geuldobi-desktop/src/main.js:380`
- 실제 런타임은 `config/models.yaml`을 읽어 에이전트를 초기화한다. `main_a.py:1085`, `main_a.py:1478`

### 결론

- 질문에 대한 직접 답: `analyst`도 실제 기본값은 `gemini-2.5-pro`가 맞다.
- 단, 현재 UI 모델 탭은 "실제 제어판"이 아니라 사실상 표시용 stub에 가깝다.
- 따라서 이 탭은 두 방향 중 하나가 필요하다.
  - 진짜 `models.yaml` 편집기로 연결
  - 아니면 read-only 상태로 명확히 표기

## 4. 작품가드 입력 기회가 현재 어디서 주어지는지 전수조사

### 프론트엔드 입력면

- `재료 넣기` 패널은 `bible`과 `treatments`만 다룬다. `geuldobi-desktop/src/index.html:2497`, `geuldobi-desktop/src/main.js:428`
- `material:list-files`, `material:import-file`, `material:delete-file` IPC 모두 허용 폴더가 `bible`, `treatments`뿐이다. `geuldobi-desktop/src/main.js:428`, `geuldobi-desktop/src/main.js:450`, `geuldobi-desktop/src/main.js:489`
- 반면 `설정 > 프로젝트` 탭에는 `작품 정체성 도우미`와 raw `작품 가드 YAML` 입력창이 있다. `geuldobi-desktop/src/index.html:2937`, `geuldobi-desktop/src/index.html:2997`
- 이 값은 실제로 `{project}/config/work_guard.yaml`에 저장된다. `geuldobi-desktop/src/main.js:536`, `geuldobi-desktop/src/main.js:606`

### 백엔드 소비 경로

- 프로젝트 시작 시 엔진은 `{project}/config/work_guard.yaml`이 있으면 `GenreGuard` 위에 `WorkGuard`를 래핑한다. `main_a.py:1050`
- `WorkGuard`는 `work_identity`, `tracking_slots`, `mandatory_scene_engines`, `registry_profiles`, `role_fit_constraints` 등을 로드한다. `modules/core/genre_guards/work_guard.py:247`
- Stage 2는 `select_retrieval_focus()`를 호출해 work identity 기반 슬롯 요약을 만든다. `modules/core/stage2_preflight.py:436`
- Stage 4 Writer 컨텍스트도 같은 방식으로 work focus를 뽑아 mandatory context에 삽입한다. `modules/core/stage4_context_builder.py:798`, `modules/core/stage4_context_builder.py:2097`
- Stage 4 Director 쪽도 work focus 요약을 따로 만든다. `modules/core/stage4_interview_round.py:255`
- UI 품질 대시보드의 `Artifact Ladder` support chip에도 `work_guard.yaml` 존재 여부가 반영된다. `modules/api/bridge_server.py:512`

### 판단

- 작품가드는 현재 "백엔드에 연결되어 있다".
- 하지만 "입력 기회가 재료 넣기 플로우에 붙어 있느냐"에 대해서는 아니라고 봐야 한다.
- 즉 현재 상태는 아래와 같다.

| 항목 | 판정 |
|---|---|
| 백엔드 적용 여부 | 적용됨 |
| 프로젝트 파일 저장 여부 | 저장됨 |
| Stage 2/3/4 컨텍스트 소비 여부 | 소비됨 |
| 재료 넣기 패널에서 바로 입력 가능 여부 | 불가 |
| 세부 실행 버튼 근처에서 입력 기회 제공 여부 | 사실상 불가 |

### 결론

- "작품가드를 선택적으로 넣을 수 있게 해야 한다"는 문제 제기는 타당하다.
- 다만 현재도 완전 부재는 아니다. 위치가 `설정 > 프로젝트` 탭으로 밀려 있을 뿐이다.
- UX 기준으로는 `재료 넣기` 영역에 `+ Work Guard 추가`가 있어야 자연스럽다.
- 최소한 다음 둘 중 하나는 필요하다.
  - `재료 넣기`에 `Work Guard` 파일 import/quick-create 추가
  - `Stage 0 / 장르설정` 근처에 `작품가드 설정` 진입 버튼 추가

## 5. 추가 개선 아이디어

### A. 가장 먼저 손봐야 할 것

1. 우측 컬럼을 스크롤 가능하게 만들기
2. `사무실` 섹션을 기본 접힘으로 두기
3. 실행 패널의 `재료 넣기 / 상품 생산 / 운영`을 모두 기본 접힘으로 두기

현재 아코디언은 독립 토글이지만 기본은 펼침 상태다. `geuldobi-desktop/src/index.html:7039`

### B. 구조상 꼭 필요한 것

4. `Artifact Ladder`, `Retrieval Inspector`, `Run Result Summary`를 `사무실`에서 분리
5. `Quality` 전용 페이지 또는 탭 신설
6. `사무실`은 "축소 카드"와 "전체화면 보기" 2단 구조로 분리

### C. 설정 UX 쪽 개선

7. 모델 탭은 실제 저장/적용 wiring을 붙이거나, 아니면 read-only badge를 붙이기
8. `작가 지시사항`과 `작품 가드`를 `재료 넣기`와 더 가깝게 재배치
9. `Artifact Ladder` 카드 path는 ellipsis만 두지 말고 클릭 시 전체 경로/미리보기 모달 제공

### D. 운영 UX 개선

10. 로그 패널뿐 아니라 `Quality` 패널들도 기본 접힘 지원
11. `실행 패널`은 기본 collapsed, 마지막 사용한 섹션만 복원
12. 프로젝트별 레이아웃 기억 기능 추가

## 권장 실행 우선순위

1. `우측 컬럼 스크롤`과 `실행 패널 기본 접힘`
2. `사무실 기본 접힘 + 확장형/오버레이`
3. `Artifact Ladder / Quality 영역 분리`
4. `작품가드` 입력 진입점 상향
5. `모델 탭` wiring 또는 read-only 정리

## 최종 답변 요약

- `Artifact Ladder`가 안 보이는 것은 실제 버그성 레이아웃 문제다.
- `사무실`이 못생겨진 것도 실제 구조 문제다.
- `analyst` 기본값은 실제로도 `gemini-2.5-pro`가 맞다.
- 다만 UI 모델 탭은 현재 실제 적용이 안 된다.
- 작품가드는 현재도 넣을 수 있지만 `설정 > 프로젝트`에만 있어서 진입성이 나쁘다.
- 다음 UI 개선은 미관보다 `레이아웃 분리 + 스크롤/접기 구조 재설계 + 입력 진입점 재배치`가 우선이다.
