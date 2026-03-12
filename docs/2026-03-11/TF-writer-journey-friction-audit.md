# TF-Writer-Journey-Friction-Audit

> 인코딩: UTF-8  
> 작성일: 2026-03-11  
> 상태: 실행 문서  
> 감리: 3-pass 완료  
> 확신도: 96%  
> 목적: `웹소설 작가가 실제로 글도비를 돌린다`는 가정으로, 시스템을 순서대로 관통했을 때의 마찰과 불편을 문서화

---

## 0. 결론

글도비는 `엔진은 강한데, 작가 체감은 아직 운영툴 쪽에 더 가깝다`.

지금 가장 큰 불편은 기술적 성능 부족보다 아래 4개다.

1. `작가가 무엇을 어디에 넣어야 하는지`가 구조화되어 있지 않다.
2. `지금 시스템이 무엇을 기억하고 왜 그렇게 판단했는지`가 충분히 보이지 않는다.
3. `BI -> TR -> Arc -> Blueprint -> Manuscript`의 작업 사슬이 화면에서 한 번에 안 잡힌다.
4. 결과는 보이기 시작했지만, `그래서 다음에 뭘 고치면 되는지`는 아직 덜 친절하다.

즉 지금 글도비는 `생산 엔진`으로는 강하지만, `작가가 덜 머리 아프게 쓰는 제품`으로는 아직 한 단계 남았다.

---

## 1. 조사 범위

이번 감사는 아래 흐름을 기준으로 했다.

1. 앱 실행
2. API 키/모델/프로젝트 설정
3. 프로젝트 생성 및 장르 선택
4. 작가 지시사항 / 작품 가드 입력
5. Stage 0~4 실행
6. 결과 확인
7. 운영/재실행/되돌리기 판단

주요 근거 표면:

- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `modules/api/bridge_server.py`
- `main_a.py`
- `docs/2026-03-10/frontend-backend-connection-check.md`
- `docs/2026-03-10/TF-UX-dashboard-feedback-productization-plan.md`
- `docs/2026-03-10/TF-work-guard-identity-ssot-plan.md`
- `docs/2026-03-10/TF-db-retrieval-consumption-intelligence-plan.md`

---

## 2. 작가 시점 walkthrough

### 2.1 진입

첫 진입에서 보이는 건 강한 운영 콘솔이다.

- `Pipeline`
- `Current Task`
- `Prompt`
- `Last Verdict`
- `Quality Radar`
- `Calibration Desk`
- `Failure Watch`

이건 내부 운영자에겐 좋다.  
하지만 일반 작가에겐 첫인상부터 `무엇부터 해야 하지?`가 생긴다.

핵심 문제:

- 메인 화면은 풍부하지만, `시작 순서`를 잡아주는 온보딩은 약하다.
- Stage 버튼은 보이지만, `이걸 누르면 어떤 산출물이 만들어지는지`가 한 번에 안 보인다.
- `One-Stop`, `Rollback`, `Wipe`, `Reset`, `Rewind` 같은 단어는 강하지만, 초심자 입장에선 부담이 크다.

### 2.2 설정

설정 화면은 기능은 많지만 작가 친화적이진 않다.

좋아진 점:

- `author_directives.txt`
- `work_guard.yaml`

이 둘이 이제 실제 프로젝트 파일에 저장된다.

불편한 점:

- `모델 설정`은 아직 stub 느낌이 강하다.
- `작품 가드 YAML`은 raw textarea 그대로라서, 작가가 직접 YAML을 다뤄야 한다.
- `작가 지시사항`도 자유 텍스트라서, 뭘 얼마나 써야 좋은지 가이드가 약하다.
- `저거 지금 보강하시겠습니까?` 같은 구조화 선택지가 없다.

즉 설정은 `가능`하지만, 체감은 아직 `엔지니어형 입력`에 가깝다.

### 2.3 프로젝트/장르

프로젝트 생성은 디렉토리 생성 수준으로는 충분하다.  
하지만 작가 경험으로 보면 빈약하다.

불편:

- 새 프로젝트 생성 시 템플릿/복제/샘플에서 시작 같은 선택이 없다.
- 장르 선택은 되지만, 실제론 현재 시스템의 강점이 특정 장르에 치우쳐 있다.
- `투자물 셸 위에 작품 개성을 얹어야 하는 경우`를 UI가 설명해주지 않는다.

즉 작가는 `내 작품을 어떤 셸로 넣어야 하는가`를 스스로 판단해야 한다.

### 2.4 기획 입력

여기서 가장 큰 피로가 생긴다.

지금 시스템은 점점 똑똑해지고 있지만, 작가 입장에선 여전히 아래가 어렵다.

- 이 작품의 정체성을 어디까지 적어야 하나
- 무엇을 HUD로 볼 수 있고, 무엇을 별도 레지스트리로 잡아야 하나
- 무엇을 작품 가드에 넣어야 하고, 무엇을 그냥 BI/TR에 두면 되나

특히 복잡한 작품일수록:

- 문파 후배 성장
- 회사별 자산/인재/라인업
- 관계선/은인/소꿉친구/라이벌
- 직업 적합성/예외 조건

이런 걸 어떻게 입력하고 기억시킬지 작가가 먼저 생각해야 한다.

지금은 그걸 `알고 있는 사람은 잘 쓰지만, 모르면 머리가 아픈 구조`다.

### 2.5 실행

Stage 2/3/4는 내부적으로 많이 좋아졌다.

- retrieval intelligence 상승
- work guard 강화
- semantic relation slice
- quality signals
- runtime health

하지만 작가 체감으로는 여전히 이런 질문이 남는다.

- 이번 Arc는 왜 이렇게 나왔지?
- Blueprint는 BI/TR 중 무엇을 많이 따랐지?
- 원고가 지금 어떤 retrieval을 먹고 쓰였지?
- 중요한 관계선이 실제로 들어갔나?

즉 `엔진이 똑똑해진 것`과 `작가가 안심하는 것` 사이엔 아직 간격이 있다.

### 2.6 결과 확인

이 부분은 최근에 꽤 좋아졌다.

- `Quality Radar`
- `Run Result Summary`
- `Episode Trend / Compare`
- `Failure Watch`
- `Calibration Desk`

그래도 아직 부족한 지점:

- 결과가 `운영자용 카드`로는 보이는데, `작가 수정 행동`까지 바로 이어지진 않는다.
- `이번 화가 왜 PASS_WITH_FIX였는지`는 알 수 있어도, `이 문장/이 장면/이 인물선부터 건드려라` 수준까진 안 온다.
- `좋은 retrieval`과 `쓸모없는 retrieval`의 차이가 작가 눈엔 아직 안 보인다.

즉 결과 표면은 좋아졌지만, `수정 UX`로는 아직 덜 진화했다.

---

## 3. 핵심 마찰 8개

### F1. 시작 순서가 제품적으로 안내되지 않는다

현재는 작가가 스스로 순서를 안다고 가정한다.

- 프로젝트 생성
- 장르 선택
- 작가 지시사항
- 작품 가드
- Stage 0
- Stage 2/3/4

이 흐름을 앱이 적극적으로 잡아주진 않는다.

판정:

- `고ROI 개선 포인트`

### F2. 작품 가드 입력이 아직 too raw다

핵심 정체성 SSOT가 중요해졌는데 입력 표면은 여전히 raw YAML textarea다.

작가 입장 불편:

- YAML 문법 부담
- 무엇을 넣어야 좋은지 불명확
- `tracking_slots`, `registry_profiles`, `mandatory_scene_engines`를 직접 설계해야 함

판정:

- `가장 큰 writer friction 중 하나`

### F3. 작품 기억 구조가 내부적으로는 좋아졌지만, 사람에겐 안 보인다

지금 시스템은:

- WorldState
- FactLedger
- StateTracker
- semantic broker
- work focus summary

를 많이 쓴다.

그런데 작가는 아직 아래를 보기 어렵다.

- 지금 무엇이 기억되고 있는가
- 무엇이 이번 화 retrieval에 실제 채택됐는가
- 무엇이 trim되어 죽었는가
- 무엇이 빠져서 품질 저하로 이어졌는가

판정:

- `지능화 대비 체감 표면 부족`

### F4. 산출물 사슬이 한눈에 안 보인다

작가 머릿속 workflow는 보통 이렇다.

- BI
- TR
- Arc
- Blueprint
- Manuscript

그런데 UI는 이걸 `하나의 제작 라인`으로 명확히 안 보여준다.

그래서 생기는 문제:

- 지금 내가 어느 단계 산출물을 보고 있는지 헷갈림
- 이전 단계와 현재 단계가 어떻게 이어졌는지 감이 약함
- `왜 여기서 이런 결과가 나왔는지` 추적하려면 머리를 더 써야 함

판정:

- `작가용 artifact ladder 필요`

### F5. 결과는 보이지만, 다음 행동 추천은 아직 약하다

현재는 `요약`은 있다.  
하지만 작가가 정말 원하는 건 보통 아래다.

- 지금 제일 먼저 고칠 것 3개
- 다음 화에서 특히 조심할 것 1~2개
- 이번 화에서 유지해야 할 강점 1개

즉 `report`는 생겼는데 `editorial action`은 아직 약하다.

판정:

- `즉시 체감 피드백 강화 필요`

### F6. 운영 버튼이 강하고 설명은 약하다

`Rollback / Wipe / Reset / Rewind`는 시스템 운영자에겐 정확하다.  
하지만 작가 입장에선 위험도가 직관적으로 구분되지 않는다.

필요한 것:

- dry-run/preview
- 영향 범위 설명
- 되돌릴 수 있는지 표시

판정:

- `낮은 공수 대비 신뢰도 개선 폭 큼`

### F7. 장르보다 작품 정체성이 중요해졌는데, UI는 아직 장르 중심이다

실제로는:

- investment 셸 유지
- work guard로 작품 개성 보정

이 방향이 점점 맞아가고 있다.

그런데 UI는 여전히 `장르 선택`이 강하고, `작품 정체성 설계`는 약하다.

즉 시스템 철학과 UI 철학이 아직 완전히 일치하지 않는다.

판정:

- `중기 과제`

### F8. 작가가 덜 생각하게 해주는 보강 제안 흐름이 없다

지금은 사용자가 직접 `이거 보강해야 하나?`, `이 라인 기억해야 하나?`를 계속 판단해야 한다.

작가 친화적 제품이라면 앱이 먼저 아래를 제안해야 한다.

- 이 작품은 `tracking_slots` 보강이 필요합니다
- 관계선 retrieval이 반복 누락됩니다
- role fit 경고가 누적됩니다
- work guard에 `mandatory_scene_engines`를 추가하는 편이 좋습니다

판정:

- `머리 부담을 줄이는 핵심 제품화 포인트`

---

## 4. 이미 좋아진 점

이 문서는 불평만 적는 문서가 아니다.  
현재 이미 좋아진 것도 분명하다.

1. `결과가 전혀 안 보이던 상태`는 지났다.
2. `Quality Radar / Result Summary / Failure Watch / Calibration Desk`가 생겼다.
3. `work_guard.yaml`과 `author_directives.txt`가 실제 프로젝트 파일과 연결됐다.
4. retrieval intelligence가 Stage 4 중심에서 Stage 2/3/Director까지 넓어졌다.
5. relation-heavy semantic slice가 실제로 먹기 시작했다.

즉 지금은 `아무것도 없는 상태`가 아니라, `좋은 엔진 위에 writer UX를 얹을 차례`다.

---

## 5. 추천 우선순위

### P1. Writer Setup Wizard

목표:

- raw YAML/자유 텍스트 입력을 구조화 폼으로 바꾼다.

핵심:

- 작품 한 줄 정의
- 주인공 edge
- 반드시 살아야 할 갈등축
- tracking slots
- forbidden flattenings
- role fit 예외

효과:

- 작가가 YAML을 덜 직접 만진다.
- `무엇을 넣어야 하는가`를 앱이 유도한다.

### P2. Artifact Ladder

목표:

- `BI -> TR -> Arc -> Blueprint -> Manuscript`를 한 줄로 보여준다.

효과:

- 지금 어디 단계인지 한 번에 보인다.
- 결과의 인과를 덜 헷갈린다.

### P3. Memory Inspector / Retrieval Inspector

목표:

- 이번 화에 실제로 들어간 기억과 빠진 기억을 사람이 볼 수 있게 한다.

표면:

- selected slots
- relation slice 포함 여부
- trimmed sections
- coverage warnings

효과:

- `왜 이런 결과가 나왔는지` 설명 가능성이 급증한다.

### P4. Run Result to Action

목표:

- 결과 카드를 `수정 행동 카드`까지 끌어올린다.

예:

- 먼저 고칠 것 3개
- 다음 화에 유지할 강점 1개
- 과교정 금지 1개

### P5. Safe Ops UX

목표:

- 운영 버튼을 덜 무섭게 만든다.

예:

- 영향 범위 미리보기
- 되돌릴 수 있음/없음
- 최근 백업 기준선

---

## 6. 추천하지 않는 방향

1. HUD만 계속 키우기  
복잡 작품은 HUD 단독으로 안 잡힌다.

2. 장르를 무한정 늘리기  
지금 병목은 장르 수보다 작품 정체성 입력과 retrieval 소비다.

3. 결과 카드만 더 화려하게 만들기  
핵심은 시각 효과보다 `덜 생각하게 해주는 구조`다.

4. raw YAML을 그대로 두고 도움말만 늘리기  
이건 writer friction을 크게 못 줄인다.

---

## 7. 최종 판단

작가 시점에서 지금 가장 불편한 건 `엔진이 약해서`가 아니다.

정확히는:

- 입력을 구조화해주는 층이 부족하고
- 기억/판단/결과를 사람이 안심하게 읽는 층이 부족하다.

그래서 다음 제품화 방향은 `새 엔진`보다 아래가 맞다.

1. setup wizard
2. artifact ladder
3. retrieval inspector
4. action-oriented result card

이 네 가지가 들어가면 글도비는 `강한 엔진`에서 `덜 머리 아픈 작가용 툴`로 한 단계 올라간다.
