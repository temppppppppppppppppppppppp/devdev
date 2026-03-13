# UI 구조개편 SSOT 3-Pass 감리

작성일: 2026-03-12  
대상 문서: `docs/2026-03-12/ui-structure-overhaul-execution-ssot.md`  
감리 방식: 정적 3-pass 문서 감리  
최종 확신도: 95%

## Executive Summary

`ui-structure-overhaul-execution-ssot.md`는 실행 SSOT로 사용 가능하다.

감리 결과는 아래와 같다.

- 핵심 구조 판단은 타당하다.
- 현재 코드 구조와 충돌하는 과장된 요구는 제거됐다.
- 단기응급처치와 중장기 구조개편의 경계가 분명하다.
- 실행 순서도 적절하다.
- 문서의 최종 확신도는 `95%`로 방어 가능하다.

이번 감리에서 retained issue는 없다. 다만 실행 전 주의사항 2건은 observation으로 유지한다.

## 1. 감리 범위

검토 대상:

- `docs/2026-03-12/ui-structure-overhaul-execution-ssot.md`
- `docs/2026-03-12/ui-feedback-response-survey.md`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `main_a.py`
- `modules/core/project_manager.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/api/bridge_server.py`
- `config/models.yaml`

금지사항:

- 코드 수정 없음
- 테스트 실행 없음

## 2. Pass 1. 사실 수집

Pass 1에서는 SSOT 문장이 현재 코드와 실제로 맞물리는지 확인했다.

### 확인된 사실

1. 우측 컬럼 과적재 진단은 맞다.
- `right-col`이 `overflow: hidden`이고, `officePanel` 내부에 분석 surface가 다 들어 있다. `geuldobi-desktop/src/index.html:94`, `geuldobi-desktop/src/index.html:2613`

2. `Artifact Ladder`를 `Quality` surface로 떼자는 판단은 근거가 충분하다.
- 해당 블록은 backend quality dashboard payload의 일부이며 `Office` 고유 기능이 아니다. `modules/api/bridge_server.py:1164`

3. `작품가드` 승격 판단은 맞다.
- 현재는 `설정 > 프로젝트`에만 있지만, backend 연결은 실제 존재한다. `geuldobi-desktop/src/index.html:2997`, `main_a.py:1051`

4. `모델` 탭의 stub 문제 진단도 맞다.
- UI select는 존재하지만 `models.yaml` save/load IPC가 없다. `geuldobi-desktop/src/index.html:2890`, `geuldobi-desktop/src/main.js:380`

5. `Run / Office / Quality / Project / Settings` 5분할은 현재 surface 책임과 잘 맞는다.

## 3. Pass 2. 교차 검증

Pass 2에서는 각 핵심 주장마다 최소 2개 증거층을 붙였다.

### Claim A. 사무실을 별도 surface로 떼는 것이 구조적으로 맞다

증거 1:
- `officePanel` 내부에 `canvas`, `quality-radar`, `artifact-ladder`, `retrieval`, `result summary`, `trend`, `calibration`, `agent board`, `event feed`가 같이 있다. `geuldobi-desktop/src/index.html:2613`

증거 2:
- 기존 답변 문서와 전역 FE audit 모두 이 과적재를 핵심 원인으로 본다. `docs/2026-03-12/ui-feedback-response-survey.md`, `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

판정:
- confirmed

### Claim B. 작품가드는 Project surface로 승격하는 것이 맞다

증거 1:
- 현재 UI 입력 위치는 `설정 > 프로젝트`다. `geuldobi-desktop/src/index.html:2927`

증거 2:
- backend는 실제로 `work_guard.yaml`을 로드해 Guard 체인과 Stage 2/4 컨텍스트에 반영한다. `main_a.py:1051`, `modules/core/stage2_preflight.py:436`, `modules/core/stage4_context_builder.py:798`

판정:
- confirmed

### Claim C. 모델 탭은 실제 wiring 전까지 read-only 또는 stub 명시가 맞다

증거 1:
- UI select와 추천 버튼은 존재한다. `geuldobi-desktop/src/index.html:2890`, `geuldobi-desktop/src/index.html:6877`

증거 2:
- 저장 경로는 `settings.json`, `author_directives`, `work_guard.yaml`뿐이고 model 값은 저장되지 않는다. `geuldobi-desktop/src/index.html:6885`, `geuldobi-desktop/src/main.js:380`

증거 3:
- 실제 런타임 모델은 `config/models.yaml`을 읽어 초기화한다. `main_a.py:1085`, `config/models.yaml:25`

판정:
- confirmed

### Claim D. 실행 패널 기본 접힘은 적절한 국룰이다

증거 1:
- 현재는 독립 토글만 있고 기본 collapsed 정책이 없다. `geuldobi-desktop/src/index.html:7039`

증거 2:
- 좌측 패널은 프로젝트 준비/실행/운영이 모두 기본 펼침이라 밀도가 높다. `geuldobi-desktop/src/index.html:2492`

판정:
- confirmed

## 4. Pass 3. 오탐 제거

Pass 3에서는 과도한 요구와 실행 범위 팽창 요소를 제거했다.

### 제거한 과장

1. `모델 탭을 이번 구조개편에서 반드시 실 editor로 완성해야 한다`
- 제거 이유: 구조개편의 본질이 surface 분리인데, `models.yaml` editor까지 묶으면 설정 인프라 작업으로 범위가 커진다.
- 최종 문서는 `read-only 우선`을 권고안으로 낮췄다.

2. `재료 넣기에서 작품가드를 반드시 파일 import 방식으로만 지원해야 한다`
- 제거 이유: 핵심은 import 방식이 아니라 진입점 승격이다.
- `Project` surface 재배치만으로도 목적을 상당 부분 달성한다.

3. `사무실은 무조건 별도 BrowserWindow여야 한다`
- 제거 이유: 별도 페이지/탭/route/overlay 중 어떤 구현이든 본질은 surface 분리다.
- 문서는 구현 자유도를 남겨 뒀다.

### 남긴 observation

1. 현재 renderer가 단일 대형 파일이라 구조개편 시 자연스럽게 일부 컴포넌트 분할이 필요할 수 있다.
2. `Run`과 `Project`의 경계는 구현 단계에서 한 번 더 미세조정될 수 있다.

둘 다 blocker는 아니다.

## 5. 확정 판정

### 최종 판정

- 실행 SSOT로 사용 가능
- retained finding 없음
- rejected/trimmed overreach 3건 제거 완료
- observation 2건 유지

### 왜 오탐이 아닌가

- 문서 핵심 주장은 모두 현재 코드 구조와 직접 연결된다.
- "사무실 분리", "작품가드 승격", "모델 탭 stub 정리", "실행 패널 기본 접힘"은 전부 코드와 UI 증거가 있다.
- 단순 취향 의견에 머무는 항목은 제거했다.

## 6. 확신도 Ledger

시작점은 70으로 잡는다.

| 항목 | 변화 | 누적 |
|---|---:|---:|
| 조사 버킷 전수 확인 완료 | +70 기준선 | 70 |
| 현재 UI 레이아웃 직접 근거 확보 | +10 | 80 |
| 작품가드 FE-BE wiring 2중 근거 확보 | +5 | 85 |
| 모델 탭 stub 상태 2중 근거 확보 | +5 | 90 |
| 기존 UI 감사 문서와 현재 구조 교차 검증 | +3 | 93 |
| 오탐 제거 및 범위 축소 완료 | +2 | 95 |

차감 항목은 아래 2개를 검토했다.

- 실제 구조개편 구현 후의 체감 UX 품질
- 페이지/탭/route 중 어떤 구현 방식이 가장 좋은지

하지만 이번 문서의 목적은 구현안 SSOT이지 최종 UX 미감 판정서가 아니므로 확신도 차감 사유로 보지 않았다.

최종 확신도는 `95%`다.

## 7. 결론

`ui-structure-overhaul-execution-ssot.md`는 현재 기준으로 방어 가능한 실행 SSOT다.

핵심 결론은 아래 한 줄로 줄일 수 있다.

`사무실은 별도 surface로 분리하고, Quality와 Project를 독립시키며, 모델 탭의 거짓 affordance를 제거하는 것이 이번 구조개편의 정답이다.`
