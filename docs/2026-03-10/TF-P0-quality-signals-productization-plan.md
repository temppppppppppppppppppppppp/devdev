# TF-P0 Quality Signals + Productization Plan

> 작성일: 2026-03-10
> 인코딩: UTF-8
> 상태: 실행 계획서
> 범위: `CED`, `AI Slop`, `gzip 압축률`, `Burstiness/Complexity` + 사용자 가시화 레이어

---

## 1. 목표

이번 배치는 두 축을 같이 처리한다.

1. `P0 품질 지표 4개 축`을 **Python-only signal**로 도입한다.
2. 그 지표를 사용자가 바로 체감할 수 있도록 **Desktop UI 제품화 레이어**에 노출한다.

핵심 원칙:

- Director 판정 로직은 건드리지 않는다.
- LLM 호출은 추가하지 않는다.
- 새 지표는 `평가 주권`이 아니라 `관측성/추세` 역할로 둔다.
- UI는 "예뻐 보이는 장식"이 아니라, 현재 프로젝트 품질 상태를 빠르게 읽게 해 주는 `quality radar` 역할을 해야 한다.

---

## 2. 왜 지금 하는가

현재 글도비는 엔진 자체는 강하지만, 외부 툴 대비 `겉으로 보이는 품질 가시화`가 약하다.

이미 갖고 있는 것:

- Stage 4 `episode_quality_labels` 저장
- `quality_dashboard` 점수/회귀 추세
- `pacing_records` 저장
- Director verdict / score / consistency checklist

아직 약한 것:

- 구조적 반복성
- AI 상투어
- 문장 길이 리듬
- 품질 추세를 사용자가 한눈에 보는 UI

즉, 이번 배치는 **엔진 강화 + 제품화 가시화**를 동시에 닫는 작업이다.

---

## 3. 현재 구조 기준 진단

### 이미 있는 것

- `episode_quality_labels` sidecar 테이블
- `quality_dashboard.record_validation()` / `get_summary()`
- `pacing_analyzer`와 `pacing_records`
- UI `office-dashboard` / `mission-card` / `live-feed`

### 이미 부분 구현된 것

- 대화 비율 체크:
  - `modules/core/pre_director_manuscript_checker.py`
  - `modules/domain/agents/chief_writer_quality.py`
  - `modules/core/pacing_analyzer.py`
- 능력/자원 관련 경고:
  - `modules/validation/blocking_validator_consistency_checks.py`
  - `modules/domain/agents/state_tracker_npc.py`
  - `modules/core/pre_director_narrative_checker.py`

따라서 이번 배치는 `대화 비율 25~35%` 같은 추가 규칙을 넣는 것이 아니라, **새로운 품질 신호 4개를 별도 계층으로 도입**하는 것이 맞다.

---

## 4. 이번 배치 확정 범위

### 포함

1. `CED`
2. `AI Slop`
3. `gzip 압축률`
4. `Burstiness/Complexity` 묶음
5. 위 신호들을 저장하는 sidecar
6. 프로젝트별 최근 품질 요약 API/IPC
7. Desktop UI `Quality Radar` 카드

### 제외

- `대화 비율 25~35%` 절대 타깃화
- `CheckEval` 이진 분해
- `Causeless Effects`
- `능력/자원` 심화 추적
- `Gemini logprobs` 기반 엔트로피
- Director prompt 수정

즉, 이번 턴은 `P0 관측성 + 제품화`까지만 한다.

---

## 5. 저장 설계

### 5.1 신규 저장면

기존 `episode_quality_labels`에 억지로 컬럼을 붙이지 않고, 별도 sidecar를 둔다.

제안:

- 테이블명: `episode_quality_signals`
- 키: `ep_num INTEGER PRIMARY KEY`
- 필드:
  - `ced_score REAL`
  - `ai_slop_score REAL`
  - `ai_slop_hits TEXT`
  - `compression_ratio REAL`
  - `burstiness REAL`
  - `complexity REAL`
  - `signal_summary TEXT`
  - `created_at TEXT DEFAULT (datetime('now'))`

이유:

- Director 결과물(`episode_quality_labels`)과 Python-only signal을 분리할 수 있다.
- 이후 P1/P2에서 추가 signal을 넣어도 schema 오염이 덜하다.
- UI/대시보드가 읽기 쉽다.

### 5.2 저장 타이밍

- Stage 4 `PASS` / `PASS_WITH_FIX` 확정 후 저장
- 저장 지점: `stage4_post_processor.py`

이유:

- 최종 원고 기준으로 계산해야 의미가 있다.
- Director 주권을 해치지 않는다.
- 재시도 중간 후보가 아니라 `확정 원고` 기준으로 축적된다.

---

## 6. 메트릭 정의

## 6.1 CED v1

정의:

- `CED = structured_error_count / max(len(manuscript) / 10000, 1.0)`

`structured_error_count` 구성:

- `consistency_checklist`에서 `ISSUE` 개수
- Stage 4 확정 시점의 structured warning count
- Python pre-check warning count가 Stage 4 PASS payload에 안전하게 전달되는 경우만 추가

초기 원칙:

- `CED v1`은 **현재 PASS 시점에 안정적으로 얻을 수 있는 structured signal만 사용**
- unavailable 데이터는 억지로 복원하지 않는다

주의:

- ConStory-Bench의 원 정의를 완전 복제하려는 것이 아니다.
- 글도비의 현재 structured outputs에 맞춘 `CED v1`이다.
- 용도는 `게이트`가 아니라 `추세/비교`다.

## 6.2 AI Slop

정의:

- 한국어 상투어/자동생성 냄새 표현 YAML 기반 카운트
- 단순 raw count만 쓰지 않고 `1만 자당 밀도`도 함께 계산

저장값:

- `ai_slop_score`
- `ai_slop_hits` (상위 hit 목록)

원칙:

- REJECT 자동화 금지
- self-critique advisory + UI 노출 용도

## 6.3 gzip 압축률

정의:

- `len(gzip.compress(text.encode("utf-8"))) / max(len(text.encode("utf-8")), 1)`

의미:

- 높거나 낮다고 단독 판정하지 않는다.
- 최근 5화 median 대비 현재 화가 얼마나 이탈하는지를 본다.

원칙:

- 절대 임계값보다 `프로젝트 내 상대 추세`를 우선한다.

## 6.4 Burstiness

정의:

- 문장 길이 분포의 표준편차 기반 리듬 신호

입력:

- 문장 단위 분리
- 각 문장 길이(문자 수 또는 토큰 근사 길이)

목적:

- 너무 균일한 문장 리듬 탐지

## 6.5 Complexity

정의:

- 평균 문장 길이 + 장문 비율 기반 단순 복잡도 지표

주의:

- `AutoCrit 2.0-3.0` 같은 외부 절대값을 그대로 쓰지 않는다.
- 현재 프로젝트 recent window 대비 `단순/균형/밀도 높음` 정도의 구간 표시만 한다.

---

## 7. 백엔드 구현 계획

### Phase A. Signal 계산기

대상 파일:

- `modules/domain/agents/chief_writer_quality.py`
- 신규 `modules/core/quality_signal_metrics.py`

역할:

- `compute_ai_slop(text)`
- `compute_compression_ratio(text)`
- `compute_burstiness(text)`
- `compute_complexity(text)`
- `compute_ced(...)`

원칙:

- 계산 로직은 가능한 한 순수 함수로 분리
- UI나 DB 로직과 섞지 않음

### Phase B. DB 저장면

대상 파일:

- `modules/core/db_manager.py`
- `modules/protocols/db_repository.py`

작업:

- `episode_quality_signals` 생성
- `save_episode_quality_signal()`
- `get_episode_quality_signal()`
- `get_recent_episode_quality_signals()`
- `get_quality_signal_summary()`

### Phase C. Stage 4 wiring

대상 파일:

- `modules/core/stage4_post_processor.py`

작업:

- 확정 원고에서 signal 계산
- DB 저장
- `quality_dashboard.record_validation()`에 metric snapshot도 함께 전달

주의:

- Director verdict / selection_reason / checklist 저장 로직은 그대로 둔다.

### Phase D. QualityDashboard 보강

대상 파일:

- `modules/core/quality_dashboard.py`

작업:

- validation record에 optional `quality_signals` 허용
- recent window signal summary 생성
- UI/브리지에서 바로 쓸 `get_quality_signal_snapshot()` 제공

---

## 8. 제품화 레이어 계획

### 8.1 노출 방식

새 패널을 기존 `office-dashboard`에 추가한다.

이름:

- `Quality Radar`

보여줄 것:

- 최근 화 기준 `CED`
- `AI Slop`
- `Compression`
- `Rhythm` (Burstiness)
- `Complexity`
- 최근 5화 기준 상승/하락/안정 배지

### 8.2 UI 원칙

- 숫자만 보여주지 말고 `읽을 수 있는 상태`를 보여준다.
- 예:
  - `CED 낮음`
  - `AI Slop 경미`
  - `리듬 안정`
  - `문장 밀도 높음`

### 8.3 업데이트 시점

- 앱 진입 시
- 프로젝트 변경 시
- Stage 4 PASS 후
- 수동 새로고침 버튼 허용 가능

### 8.4 전달 경로

권장:

- Python bridge에 read-only 요약 endpoint 추가
- Electron main/preload를 통해 renderer에 노출

제안 경로:

- `GET /quality/summary?project=<name>&lookback=5`
- IPC:
  - `bridge:get-quality-summary`

이유:

- 별도 Node sqlite 의존성 없이 Python 측 DB 코드를 재사용 가능
- 현재 브리지 구조와 자연스럽게 맞는다

---

## 9. 파일 단위 변경 예정

### 백엔드

- `modules/core/db_manager.py`
- `modules/protocols/db_repository.py`
- `modules/core/quality_dashboard.py`
- `modules/core/stage4_post_processor.py`
- `modules/api/bridge_server.py`
- 신규 `modules/core/quality_signal_metrics.py`

### 프론트/IPC

- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/index.html`

### 테스트

- 신규 `tests/test_quality_signal_metrics.py`
- 신규 `tests/test_quality_signal_db.py`
- 신규 `tests/test_quality_signal_api.py`
- 필요 시 `tests/test_stage4_post_processor.py` 확장

---

## 10. 수용 기준

### 기능

- Stage 4 PASS 시 품질 신호 4개 축이 저장된다.
- 최근 5화 기준 품질 요약을 프로젝트별로 읽을 수 있다.
- UI에서 `Quality Radar`가 정상 노출된다.
- 데이터가 없는 신규 프로젝트에서도 UI가 깨지지 않는다.

### 안전성

- LLM 호출 0회 추가
- Director 점수/판정 로직 불변
- 기존 `episode_quality_labels` 저장 불변
- 신규 저장 실패 시 전체 파이프라인 비차단

### 제품화

- 사용자가 "최근 작품 품질 상태"를 5초 안에 읽을 수 있어야 한다.
- 숫자 + 상태 텍스트 + 추세 배지가 함께 있어야 한다.

---

## 11. 리스크와 대응

### 리스크 1. 절대 임계값 오남용

대응:

- 초기 버전은 최근 5화 median/avg 대비 상대 비교만 사용
- 절대 점수 게이팅 금지

### 리스크 2. 지표가 Director 주권을 침범

대응:

- 모든 지표는 advisory / dashboard 전용
- verdict 변경 로직과 분리

### 리스크 3. UI가 수치만 많고 읽기 어려움

대응:

- 4~5개 핵심 signal만 카드화
- 색/상태/짧은 설명으로 요약

### 리스크 4. DB schema 혼합 오염

대응:

- `episode_quality_labels`와 별도 sidecar 분리

---

## 12. 권장 작업 순서

1. `quality_signal_metrics.py` 순수 계산 함수 작성
2. DB sidecar + CRUD 추가
3. Stage 4 post-process 저장 배선
4. `quality_dashboard` snapshot 보강
5. bridge read-only summary endpoint 추가
6. Electron IPC 연결
7. `index.html` `Quality Radar` 추가
8. 단위 테스트
9. UI smoke + frontend-backend 연결 재확인

---

## 13. 이번 문서 기준 최종 권고

이 배치는 진행 가치가 높다.

이유:

- `P0 4개`는 LLM 비용을 늘리지 않는다.
- 지금 부족한 `제품 가시성`을 빠르게 끌어올린다.
- Director 주권/대원칙을 깨지 않는다.
- 나중에 `CheckEval`, `FailureAnalyzer cluster`, `CED trend dashboard`로 자연 확장된다.

권장 실행 방식:

- **한 배치로 진행 가능**
- 다만 구현 순서는 반드시 `backend signal -> storage -> read-only summary -> UI` 순으로 간다.

---

## 14. 1차 감리 메모

- `대화 비율`은 이번 배치에서 제외하는 판단이 맞다.
- `능력/자원 미커버 0%` 같은 과장 서술은 이번 계획에 포함하지 않는다.
- 외부 벤치마크의 효과 수치는 구현 기대효과가 아니라 `아이디어 출처`로만 취급한다.
