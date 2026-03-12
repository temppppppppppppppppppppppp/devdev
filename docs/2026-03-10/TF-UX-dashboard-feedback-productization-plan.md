# TF-UX Dashboard Feedback Productization Plan

> 작성일: 2026-03-10
> 인코딩: UTF-8
> 상태: P1 구현 완료
> 범위: 상품성 있는 UX/UI 완성도, 정량 품질 메트릭 표면화, 대시보드/비교표/가시화, 즉각적 체감 피드백
> 최종 판정: 실행 가능
> 현재 확신도: 96%
> 구현 메모: `Quality Radar 2.0`, `Run Result Summary`, `Episode Trend / Compare`, `Failure Watch`, `Artifact Ladder`, `Retrieval Inspector`, `Run Result to Action` 반영 완료
> 검증 기준선: `pytest tests/ -q -> 3842 passed, 16 skipped, 1 warning`, `pytest --collect-only -q tests -> 3858 collected`, `npm run start:spike -> PASS`

---

## 1. 목적

이번 문서의 목표는 엔진 자체를 더 똑똑하게 만드는 것이 아니라, 이미 있는 엔진 품질을 사용자가 바로 읽고 체감하게 만드는 `제품화 레이어`를 정리하는 것이다.

핵심 질문은 네 가지다.

1. UI가 지금 상용 툴처럼 보이는가
2. 품질 메트릭이 사용자 눈앞에 충분히 드러나는가
3. 비교표/추세/가시화가 즉시 읽히는가
4. 사용자가 "지금 왜 좋고 왜 나쁜지"를 즉각 체감하는가

---

## 2. 현재 위치 요약

현재 글도비는 아래처럼 보는 게 맞다.

- 엔진/파이프라인: 강함
- 제품화 UI/대시보드/즉시 피드백: 1차 제품화 완료, 2차 상용화 미완

체감 등급으로 요약하면:

- 엔진/검증/연속성: `4/5`
- 제품화 UI/대시보드/즉시 피드백: `2.5~3/5`

즉, 프로토타입은 이미 벗어났지만 상용 글쓰기 툴 수준의 체감 UX는 아직 한 단계 남아 있다.

---

## 3. 오탐 제거용 현재 구현 확인

이 문서는 아래 항목이 `이미 존재한다`는 전제 위에서 쓴다.

### 3.1 이미 구현된 UI 표면

- `office dashboard`
  - `Pipeline / Current Task / Prompt / Last Verdict`
  - 위치: `geuldobi-desktop/src/index.html`
- `Quality Radar`
  - `CED / AI Slop / gzip / Rhythm / Density`
  - 최근 5화 median 대비 상대 위치 표시
  - 위치: `geuldobi-desktop/src/index.html`
- `agent board`
  - 에이전트별 상태/디테일/말풍선
  - 위치: `geuldobi-desktop/src/index.html`
- `live feed`
  - 최근 이벤트 5건 표시
  - 위치: `geuldobi-desktop/src/index.html`
- `RPG ticker`
  - 공지 스크롤 존재
  - 위치: `geuldobi-desktop/src/index.html`

### 3.2 이미 구현된 백엔드/데이터 표면

- `episode_quality_signals` 저장
  - 위치: `modules/core/db_manager.py`
- `quality_signal_summary` 조회
  - 위치: `modules/core/db_manager.py`
- `/quality/summary` 브리지 엔드포인트
  - 위치: `modules/api/bridge_server.py`
- `QualityDashboard`
  - `stage stats`
  - `common violations`
  - `episode trend`
  - `failure patterns`
  - 위치: `modules/core/quality_dashboard.py`

### 3.3 이미 있는 즉각 피드백

- `run_started / prompt_request / prompt_resolved / run_completed / run_failed` 이벤트 기반 UI 반영
- Verdict 카드 색상/점수 반영
- 에이전트 말풍선과 최근 이벤트 피드 반영

따라서 이 문서는 "UI가 아무것도 없다"는 가정 위에 있지 않다.

---

## 4. 실제 갭

### G1. 상품성 있는 UX/UI 완성도는 아직 `조합 수준`이다

현재는 필요한 조각이 존재하지만, 상용 툴처럼 하나의 정보 흐름으로 정리되지는 않았다.

실제 갭:

- `Quality Radar`, `Verdict`, `Live Feed`, `Agent Board`가 서로 느슨하게 놓여 있음
- 사용자가 `무엇이 문제인지 -> 어디를 봐야 하는지 -> 다음에 무엇을 해야 하는지`를 한 번에 못 읽음
- 설정 탭 중 일부는 아직 `stub-notice` 수준으로 남아 있음
- 프로젝트/품질/실행 결과가 "하나의 작업 화면"으로 응집되지 않음

판정:

- 시각적 매력은 1차 확보
- 정보 구조 완성도는 아직 부족

### G2. 정량 품질 메트릭 표면화는 `요약 1장` 수준이다

현재 보이는 것은:

- 최근 5화 기준 signal 5종
- median 대비 상대 위치
- 최신 slop hit 일부

아직 안 보이는 것:

- 회차별 추세선
- signal 변화의 원인 설명
- Director 품질 라벨과의 결합
- Stage별 품질 추세
- 경고/위반 타입 빈도
- "이번 화가 왜 alert인지" 설명 카드

판정:

- 메트릭은 존재
- 표면화는 아직 최소 버전

### G3. 외부 툴처럼 바로 보이는 대시보드/비교표/가시화가 부족하다

백엔드에는 이미 아래 데이터가 있다.

- `stage_stats`
- `common_violations`
- `get_episode_trend()`
- `get_failure_patterns()`
- `quality_signal_history`

하지만 현재 프론트는 이 대부분을 쓰지 않는다.

실제 갭:

- 회차별 스파크라인 없음
- 최근 N화 비교표 없음
- Stage 2/3/4 품질 통계 패널 없음
- `PASS/PWF/REJECT` 비율 가시화 없음
- 주요 실패 패턴 랭킹 노출 없음
- 전략/모델/프로바이더 비교는 전혀 없음

판정:

- 데이터 계층은 부분 준비
- 대시보드 계층은 아직 초기 버전

### G4. 상용 글쓰기 툴이 잘하는 즉각적 체감 피드백이 아직 약하다

현재도 즉시 피드백은 있다.

- 실시간 이벤트
- 말풍선
- prompt 대기
- 최근 verdict

하지만 아직 부족한 부분:

- `왜 PASS/PWF/REJECT인지` 한눈에 안 보임
- `이번 화에서 가장 큰 문제 3개`가 바로 안 뜸
- `다음 행동`이 CTA처럼 안 보임
- `어떤 신호가 나빠졌는지` run 종료 직후 강조되지 않음
- 품질 경고가 "보기 좋은 카드"는 있어도 "수정 행동"으로 연결되지 않음

판정:

- 상태 피드백은 있음
- 행동 피드백은 약함

---

## 5. 이번 실행 문서의 원칙

1. Director 주권을 깨지 않는다.
2. 새 품질 신호를 hard gate로 승격하지 않는다.
3. LLM 호출을 추가하지 않는다.
4. 기존 Electron-FastAPI-IPC 구조를 유지한다.
5. 먼저 `read-only productization`을 끝내고, 나중에 `advisory CTA`를 붙인다.

---

## 6. 우선순위

### P1. 당장 체감이 큰 것

1. `Quality Radar 2.0`
2. `Run Result Summary 카드`
3. `Episode Trend / Compare Table`
4. `Failure Pattern Dashboard`

### P2. 다음 단계

1. `Project Health 패널`
2. `Stage별 pass rate / avg score 시각화`
3. `품질 신호 설명 tooltip / glossary`
4. `recent action CTA`

### P3. 후순위

1. 모델/전략/프로바이더 비교
2. 프로젝트 간 비교
3. 팀/운영 히스토리 뷰

---

## 7. 실행 계획

## Phase 1. Quality Radar 2.0

목표:

- 지금 있는 `Quality Radar`를 "숫자 5장"에서 "추세 + 설명" 패널로 올린다.

작업:

- `recent` 5화 데이터를 카드만이 아니라 소형 스파크라인으로 표시
- 현재값, median, delta 외에 `좋아짐/악화 이유` 한 줄 추가
- `latest_ai_slop_hits`를 단순 문자열이 아니라 상위 hit chip으로 표시
- signal별 상태 색을 더 명확히 분리

대상 파일:

- `modules/core/db_manager.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/index.html`

검증:

- 기존 `/quality/summary` 호환 유지
- 프론트 fallback 유지
- `npm run start:spike` 통과

## Phase 2. Run Result Summary

목표:

- 사용자가 run 종료 직후 `왜 이런 결과가 났는지` 바로 보게 만든다.

작업:

- `run_completed` 또는 verdict 반영 직후 `Result Summary` 패널 표시
- 포함 정보:
  - verdict
  - score
  - top 3 warning/issues
  - latest quality signal delta
  - 다음 행동 추천 1줄
- Director `open_review`, `selection_reason`, `consistency_checklist` 일부를 요약 노출

대상 파일:

- `modules/core/db_manager.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/index.html`

주의:

- 전문 전체를 노출하지 말고 `요약 카드`로 제한
- hard reject 로직은 추가하지 않음

## Phase 3. Episode Trend / Compare Table

목표:

- 외부 툴처럼 `최근 N화 비교`를 바로 보이게 한다.

작업:

- 최근 10~20화 표 추가
- 컬럼 예시:
  - ep_num
  - verdict
  - score
  - CED
  - AI Slop
  - gzip
  - Rhythm
  - Density
- trend row 또는 sparkline 추가
- 행 클릭 시 해당 화 요약 카드 확장

근거:

- `QualityDashboard.get_episode_trend()`는 이미 존재
- `episode_quality_signals` recent row도 이미 존재

## Phase 4. Failure Pattern Dashboard

목표:

- "요즘 왜 자주 깨지는지"를 운영자가 한눈에 알게 한다.

작업:

- `common_violations`
- `failure_patterns.by_type`
- `stage_stats`
- `avg_blueprint_coverage`
- `hud_anomaly_rate`

를 read-only 대시보드로 노출

대상:

- `modules/core/quality_dashboard.py`
- 신규 브리지 summary endpoint
- `index.html`

주의:

- 운영자용 섹션으로 두고 메인 생성 흐름을 방해하지 않음

---

## 8. 명시적 비포함

이번 문서 범위에서 하지 않는 것:

- 새 LLM 심사자 추가
- 품질 신호를 Director score에 직접 합산
- CW/Director prompt에 정량 signal 직접 주입
- 모델별 A/B 결과 자동 비교
- 대화 비율 절대 타깃 강제

즉, 이번 제품화는 `가시화와 체감 강화`이지 `판정 엔진 개편`이 아니다.

---

## 9. 권장 구현 순서

1. `bridge read-only summary 확장`
2. `Quality Radar 2.0`
3. `Run Result Summary`
4. `Episode Compare Table`
5. `Failure Pattern Dashboard`

이 순서가 맞는 이유:

- 기존 구조를 가장 덜 깨고
- 사용자가 가장 빨리 체감하고
- 데이터 구조를 재활용할 수 있기 때문이다.

---

## 10. 파일별 작업 후보

### 백엔드

- `modules/core/db_manager.py`
  - quality summary payload 확장
- `modules/core/quality_dashboard.py`
  - trend/failure snapshot 제공 함수 정리
- `modules/api/bridge_server.py`
  - read-only summary endpoint 추가/확장

### Electron main/preload

- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`

### Renderer

- `geuldobi-desktop/src/index.html`

---

## 11. 테스트/검증 계획

### 백엔드

- `tests/test_bridge_quality_summary.py`
- `tests/test_quality_signal_metrics.py`
- `tests/test_db_manager.py`
- 필요 시 신규
  - `tests/test_quality_dashboard.py`

### 프론트

- `npm run start:spike`
- inline script syntax check
- 기존 frontend-backend connection baseline 재확인

### 회귀 기준

- 브리지 fallback 유지
- 프로젝트 미선택/신호 없음 상태 유지
- 기존 run/prompt/event 흐름 비파손

---

## 12. 3-Pass 감리 메모

### Pass 1. 정합성

- `Quality Radar`, `Agent Board`, `Live Feed`, `Ticker`는 이미 구현돼 있음
- `quality signal`, `summary endpoint`, `quality dashboard`도 이미 구현돼 있음
- 따라서 이 문서는 "신규 구축" 문서가 아니라 "2차 제품화" 문서다

### Pass 2. 안전성

- 기존 판정 로직, Director schema, CW 생성 루프를 건드리지 않는 방향으로 제한했다
- read-only summary, UI drilldown, 시각화 강화 중심으로 좁혀 리스크를 낮췄다

### Pass 3. 완전성

- 요청한 4개 축
  - UX/UI 완성도
  - 정량 메트릭 표면화
  - 대시보드/비교표/가시화
  - 즉각 체감 피드백
  를 각각 현재 상태와 개선 단계로 분리해 정리했다

---

## 13. 최종 판정

- 판정: `GO`
- 성격: `실행 문서`
- 이유: 이미 있는 기능과 없는 기능을 분리했고, 다음 배치를 `가시화/체감 강화` 중심으로 좁혀 오탐을 제거했기 때문이다.
