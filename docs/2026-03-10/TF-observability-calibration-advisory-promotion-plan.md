# TF Observability / Calibration / Advisory Promotion Plan

작성일: 2026-03-10  
인코딩: UTF-8  
상태: Phase 1 구현 완료 / Phase 2 관측 진행 전  
판정: GO  
확신도: 97%

## 0. 결론

다음 스텝은 `새 plumbing 추가`가 아니라 `운영 관측 -> 캘리브레이션 -> 약한 advisory 승격`이다.

지금 글도비는 이미 아래를 갖고 있다.

- `episode_quality_signals`
- `Quality Radar / Run Result Summary / Episode Trend / Failure Watch`
- `Calibration Desk`
- `runtime_health`
- `run_failed` 진단 payload
- Stage 3/4 및 Director의 기존 품질/클리셰/AI 티 방어선

따라서 지금 바로 hard gate를 늘리는 건 과하고, 먼저 `실데이터 10~20화 관측`으로 신호의 신뢰도를 확인하는 게 맞다.

## 1. 현재 위치

### 이미 있는 관측 표면

- `modules/core/quality_signal_metrics.py`
  - `CED / AI Slop / compression / burstiness / complexity`
- `modules/core/stage4_post_processor.py`
  - Stage 4 PASS 후 품질 신호 저장
- `modules/core/quality_dashboard.py`
  - `record_validation()`, `get_score_trend_summary()`, `get_failure_patterns()`
- `modules/api/bridge_server.py`
  - `/quality/summary`, `/quality/dashboard`, `/quality/review`, `runtime_health`
- `geuldobi-desktop/src/index.html`
  - `Quality Radar`, `Run Result Summary`, `Episode Trend / Compare`, `Failure Watch`, `Calibration Desk`
- `modules/core/soft_failure.py`
  - 비차단 실패 구조화 기록
- `episode_quality_observations`
  - 운영자 수기 판정 sidecar

### 이미 있는 AI 티 방어선

- `modules/domain/agents/blueprint_ensemble.py`
  - Stage 3 blueprint anti-AI-tell guardrail
- `modules/domain/agents/chief_writer_quality.py`
  - self-critique의 클리셰/반복/대화 자연성/문장 스타터 반복 점검
- `modules/domain/agents/chief_writer_prompts.py`
  - anti-trope 지시 강화
- `config/prompts/director.yaml`
  - `scene_variety`, `dialogue_naturalness`, `emotional_authenticity` 및 AI 티 명시 감리

### 아직 아닌 것

- 새 품질 신호 5종은 아직 `CW/Director`가 직접 소비하지 않는다.
- 현재는 `사후 HIL/운영 관측` 전제다.
- 따라서 지금 단계의 핵심은 `제어`가 아니라 `검증`이다.

## 2. 왜 바로 hard gate로 올리면 안 되는가

이유는 세 가지다.

1. `gzip / burstiness / complexity`는 장르, 회차, 장면에 따라 편차가 크다.
2. `AI Slop`도 좋은 문장과 나쁜 문장을 기계적으로 가르지 못한다.
3. `CED`는 현재 유용하지만, 곧바로 rejection 축으로 쓰면 Python warning 과민 반응 위험이 있다.

즉 지금은 `운영 지표`이지, 아직 `검증된 제어 신호`는 아니다.

## 3. 실행 목표

이번 문서의 목표는 세 가지다.

1. 어떤 신호가 실제로 유효한지 운영 관측으로 검증한다.
2. 노이즈가 많은 신호는 임계값과 표현 방식을 조정한다.
3. 검증된 항목만 `advisory-only`로 Stage 3/4와 Director에 약하게 승격한다.

비목표:

- hard reject 추가
- Director score schema 변경
- 새 LLM 호출 추가
- 새로운 품질 신호 추가 발명

## 4. Phase 1. 운영 관측

### 범위

- 최근 실제 프로젝트 기준 `10~20화`
- 가능하면 장르/화수 성격이 다른 구간 혼합
  - 초반
  - 중반
  - 전환부
  - arc finale

### 봐야 할 것

- `CED`
  - 실제 continuity/validator warning 증가와 상관이 있는가
- `AI Slop`
  - 사람이 보기에 "AI 티" 나는 화와 같이 올라가는가
- `compression`
  - 지나치게 낮거나 높을 때 실제 체감과 연결되는가
- `burstiness`
  - 리듬이 좋은 화/단조로운 화를 구분하는가
- `complexity`
  - 밀도와 난삽함을 구분하지 못하고 섞어 버리지는 않는가
- `runtime_health`
  - 어떤 soft failure가 반복되는가
- `run_failed`
  - 새 payload가 실제 원인 추적 시간을 줄이는가

### 기록 단위

- episode 번호
- verdict
- score
- signal 5종
- 사람이 본 한줄 판정
  - `좋음`
  - `경계`
  - `AI 티`
  - `지나친 단조`
  - `과잉 설명`
- 비차단 실패 유무

## 5. Phase 2. 캘리브레이션

### 기본 원칙

- 숫자를 먼저 믿지 말고 `실제 원고 체감`을 우선한다.
- 절대 기준보다 `프로젝트/최근 5~10화 median 대비 상대 변화`를 우선한다.
- 신호 하나만으로 결론 내리지 않는다.

### 권장 조정 방식

#### C1. CED

- 유지 방향: `유효`
- 조정 포인트:
  - warning 종류를 더 잘 쪼갤 필요가 있는지
  - checklist issue와 python warning 비중이 과한지

#### C2. AI Slop

- 유지 방향: `유효 가능성 높음`
- 조정 포인트:
  - hit 사전에서 과잉 탐지되는 표현 제거
  - 장르 필수 표현은 예외 목록 검토

#### C3. compression

- 유지 방향: `보조 지표`
- 조정 포인트:
  - 단독 경고 금지
  - `AI Slop` 또는 `complexity`와 같이 볼 때만 의미 부여

#### C4. burstiness

- 유지 방향: `보조 지표`
- 조정 포인트:
  - 전투/대화 집중 회차에 대한 예외 감안
  - 절대 alert보다 `급격한 변화` 중심으로 해석

#### C5. complexity

- 유지 방향: `보조 지표`
- 조정 포인트:
  - 복잡함과 난삽함을 구분 못 하는 경우 watch 단계로 낮춤
  - 설명문 비중이 높은 장르/회차에서 과민한지 확인

## 6. Phase 3. advisory-only 승격

승격은 `hard gate`가 아니라 아래 순서로만 간다.

### 3-1. Stage 4 CW retry feedback

가장 먼저 붙일 위치:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`

형태:

- `최근 품질 신호 경고`
- `이번 화에서 유독 튄 항목 1~2개`
- `행동 문장` 중심

예:

- `AI Slop이 최근 median보다 높음 — 상투적 반응구 반복을 줄일 것`
- `Rhythm 변동이 낮음 — 문장 시작과 길이 리듬을 더 벌릴 것`

금지:

- score 직접 감점
- retry 강제

### 3-2. Director open_review 보조

다음 위치:

- `config/prompts/director.yaml`
- 필요 시 Director feedback 조립부

형태:

- `수치 그대로`가 아니라 `참고 메모`
- `quality signal advisory` 1블록 추가

예:

- `참고: 최근 대비 AI Slop / Compression 경고`

금지:

- Director verdict 강제
- Python이 PASS/REJECT 판단 대체

### 3-3. Stage 3 blueprint advisory

가장 마지막:

- `modules/domain/agents/blueprint_ensemble.py`

형태:

- Stage 4에서 반복적으로 잡힌 `AI 티 패턴`만 Stage 3 anti-pattern으로 환류

예:

- 장면 말미 기계적 요약 반복
- 유사한 감정 반응구 반복
- 같은 opening/ending hook 리듬 반복

조건:

- 최소 10화 이상에서 반복 확인된 패턴만 올린다.

## 7. 승격 조건

아래 조건을 만족할 때만 advisory-only로 올린다.

1. 최근 `10~20화`에서 사람이 본 체감과 같은 방향으로 움직인다.
2. 오탐 사례가 적어도 설명 가능하다.
3. 장르/전환부/전투부 예외가 정리된다.
4. 단독 지표보다 묶음 지표로 더 잘 작동한다.

권장 우선순위:

1. `AI Slop`
2. `CED`
3. `burstiness`
4. `compression`
5. `complexity`

## 8. 보류 기준

아래면 보류한다.

- 좋은 화에서도 자주 경고가 뜬다.
- 장르에 따라 판정 방향이 자주 바뀐다.
- 운영자가 봐도 설명이 불가능하다.
- retry feedback에 넣었더니 오히려 문장이 과교정된다.

즉 `맞는 것만 올리고, 애매하면 계속 관측`이 원칙이다.

## 9. 테스트 / 검증

문서 기준 최소 검증은 아래다.

- `python -m pytest tests/ -q`
- `python -m pytest --collect-only -q tests`
- `npm run start:spike`

운영 검증은 아래다.

- 실제 프로젝트 10~20화 관측
- `quality/dashboard` 결과 캡처
- `run_failed` 상세 payload 샘플 확인
- `soft_failures.jsonl` 최근 창 확인

## 10. 3-Pass 감리 메모

### Pass 1. 정합성

오탐 제거:

- `새 품질 신호를 아직 에이전트가 먹고 있다`고 쓰지 않음
- `AI 티 방어선이 없다`고 쓰지 않음
- `곧바로 hard gate로 올리자`고 쓰지 않음

### Pass 2. 안전성

안전 원칙:

- Director 주권 유지
- 새 LLM 호출 없음
- hard gate 없음
- 먼저 관측, 다음 캘리브레이션, 마지막 advisory-only 승격

### Pass 3. 완전성

이번 문서는 아래 3축을 모두 포함한다.

1. 운영 관측 계획
2. 신호 캘리브레이션 기준
3. advisory 승격 조건

따라서 다음 단계 실행 문서로 충분하다.

## 11. 최종 판정

이 문서는 `바로 실행 가능`하다.  
다음 배치는 새 기능 추가보다 `운영 관측 + 캘리브레이션`이 우선이다.

한 줄 요약:

`지금은 품질 신호를 더 세게 휘두를 때가 아니라, 실제 데이터로 어느 신호가 진짜 먹히는지 검증할 때다.`
