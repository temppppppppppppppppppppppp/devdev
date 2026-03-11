# 00_test_00 Runtime/Cost Cross-Check Order

> 작성일: 2026-03-11
> 상태: 비교군 공용 오더
> 용도: Codex / OPUS 병렬 감리용
> 성격: `runtime/cost cross-check layer`
> 비고: 기존 SSOT를 대체하지 않는다

---

## 0. 목적

이 문서는 `projects/00_test_00`의 현재 실행 기록을 기준으로, 왜 `1 arc`는 acceptance baseline으로 충분했지만 `2 arc` 수준에서는 체감상 `2시간급 오버런`으로 불어나는지를 **로그 / DB / metrics 전수조사**로 설명하기 위한 공용 오더다.

비교 목적은 `누가 맞나`를 가르는 것이 아니라 아래 둘을 분리하는 것이다.

- 무엇이 **확실한 사실**인가
- 무엇이 **해석 차이 / 추가 가설**인가

두 에이전트는 반드시 **같은 입력**, **같은 taxonomy**, **같은 표 구조**를 사용해야 한다.  
다른 해석이나 반례는 본문이 아니라 appendix에만 적는다.

---

## 1. 고정 입력과 해석 규칙

### 1.1 필수 입력

두 에이전트는 아래 입력만 사용한다.

- `ops_hardening_rerun_00_test_00.log`
- `projects/00_test_00/project_data.db`
- `projects/00_test_00/logs/metrics/*.json`
- `projects/00_test_00/logs/pass_rate_monitor.json`
- `projects/00_test_00/logs/quality_metrics.jsonl`
- `docs/2026-03-11/00-test-00-stage234-ssot-3pass.md`
- `docs/2026-03-11/00-test-00-manual-reading-audit.md`

필요하면 보조 입력으로 아래를 참고할 수 있다.

- `docs/2026-03-11/pipeline-run-audit-00_test_00.md`
- `docs/2026-03-11/director-quality-audit-00_test_00.md`

### 1.2 cutoff 규칙

해석 기준은 아래로 고정한다.

- `acceptance baseline`은 `Arc 1 / ep_0001~ep_0004`까지만 사용한다.
- `Arc 2+`는 acceptance 증거가 아니라 `runtime/cost overrun evidence`로만 사용한다.
- 로그 기준 cutoff marker는 아래 두 줄이다.
  - acceptance 종료: `✅ 요청한 1개 Arc 전부 완료!`
  - overrun 시작: `🔄 [OneStop] Arc 2/60 처리 시작`

즉, `Arc 2`는 “성공했는가”를 판정하는 근거가 아니라 “왜 길어졌는가”를 설명하는 근거다.

### 1.3 행위 제약

- 이 오더 수행은 **read-only 조사**로 제한한다.
- 코드 수정, 문서 수정, 추가 런 실행은 포함하지 않는다.
- 숫자는 반드시 원천 파일을 붙여 적고, 추정치는 `estimated`로 명시한다.

---

## 2. 공통 작업 명세

두 에이전트는 아래 3-pass를 **동일한 순서**로 수행한다.

### Pass 1. 사실 추출

목표: 시간/비용/재시도 구조를 해석 없이 고정한다.

필수 산출 표 2개를 작성한다.

#### 표 A. Episode x Round Breakdown

아래 헤더를 그대로 사용한다.

| arc_no | ep_num | round_num | phase | generation_mode | patch_mode | candidate_count | verdict | score | duration_sec | tokens | cost_usd | source |
|---|---:|---:|---|---|---|---:|---|---:|---:|---:|---:|---|

작성 규칙:

- 최소 단위는 `episode x round`다.
- `phase`는 `stage2`, `stage3`, `stage4` 중 하나만 쓴다.
- `generation_mode`는 `ensemble`, `patch`, `patch_fallback`, `unknown`만 허용한다.
- `patch_mode`는 `yes/no`만 쓴다.
- `tokens`, `cost_usd`, `duration_sec`를 round 단위로 직접 산출할 수 없으면 `estimated`라고 표기하고 근거 source를 붙인다.
- source는 반드시 로그/DB 파일명을 적는다.

#### 표 B. Stage Summary

아래 헤더를 그대로 사용한다.

| stage | scope | attempts | pass_count | reject_count | total_duration_sec | total_tokens | total_cost_usd | notes |
|---|---|---:|---:|---:|---:|---:|---:|---|

작성 규칙:

- `scope`는 `Arc 1 acceptance` 또는 `Arc 2+ overrun evidence`만 허용한다.
- acceptance와 overrun을 한 줄에 섞지 않는다.

### Pass 2. 원인 분해

목표: 병목을 taxonomy로 고정하고, 사실과 해석을 분리한다.

허용 taxonomy는 아래 네 개뿐이다.

- `confirmed bottleneck`
- `supporting contributor`
- `false positive / noise`
- `hypothesis pending`

필수 산출 표는 아래 하나다.

#### 표 C. Root-Cause Taxonomy

아래 헤더를 그대로 사용한다.

| id | taxonomy | evidence | current interpretation | time/cost impact | next fix point | confidence |
|---|---|---|---|---|---|---|

작성 규칙:

- `evidence`에는 반드시 파일/로그/DB 근거를 적는다.
- `current interpretation`은 한 문장으로 쓴다.
- `time/cost impact`는 가능하면 정량으로 적고, 불가능하면 `low/medium/high`로 적는다.
- `confidence`는 `high/medium/low`만 허용한다.

필수 검토 축:

- CW 3-ensemble + self-critique
- auto-length reject
- contradiction firewall 후 patch 라우팅
- advisory noise
- telemetry misread
- PromptLoader 경고

### Pass 3. 개선 우선순위

목표: 다음 배치에서 가장 싸게 줄일 수 있는 병목을 고정한다.

필수 산출 표는 아래 하나다.

#### 표 D. Improvement Priority

아래 헤더를 그대로 사용한다.

| priority | class | target | expected effect | implementation cost | confidence |
|---|---|---|---|---|---|

작성 규칙:

- `class`는 아래 세 개만 허용한다.
  - `quick win`
  - `structural change`
  - `needs instrumentation`
- `priority`는 `P0`, `P1`, `P2`만 허용한다.
- `expected effect`는 반드시 시간/비용/오탐 중 무엇을 줄이는지 적는다.

---

## 3. 본문 구조 고정

Codex와 OPUS는 메인 바디를 아래 구조로 **완전히 동일하게** 작성한다.

1. `최종 한줄 판정`
2. `Pass 1. 사실 추출`
3. `Pass 2. 원인 분해`
4. `Pass 3. 개선 우선순위`
5. `비교용 요약`

`비교용 요약`은 아래 5문항에 대해 한 줄씩 답한다.

- 시간은 어디서 가장 많이 소모되는가
- 비용은 어디서 가장 많이 소모되는가
- retry는 어느 규칙/경로에서 가장 크게 증폭되는가
- 실제 병목과 오탐은 어디서 갈리는가
- 다음 배치에서 가장 싸게 줄일 수 있는 병목은 무엇인가

본문에서는 아래 단어를 쓰지 않는다.

- `bug`
- `issue`
- `problem`

반드시 taxonomy 용어만 쓴다.

---

## 4. Appendix 규칙

appendix는 독립 허용이다. 다만 섹션명은 반드시 아래 둘만 사용한다.

### Appendix A. Agent-specific observations

- 각 에이전트가 본문에 넣지 않은 독자 관찰을 적는다.
- 단, 본문 사실과 충돌하는 새 사실을 적으면 안 된다.

### Appendix B. 반례 / 이견 / 추가 가설

- 상대 에이전트와 갈릴 가능성이 있는 해석만 적는다.
- 본문 taxonomy를 뒤집는 주장은 여기서만 허용한다.
- 단, 근거 없는 추정은 금지한다.

---

## 5. 3-Pass 감리 기준

### Pass 1. 오더 문서 자체 감리

아래를 모두 만족해야 한다.

- 입력 파일 목록이 고정되어 있다
- cutoff 규칙이 고정되어 있다
- 표 헤더가 고정되어 있다
- taxonomy가 4개로 고정되어 있다
- implementer가 추가 결정을 할 여지가 없다

### Pass 2. 비교 가능성 감리

아래를 모두 만족해야 한다.

- Codex와 OPUS가 같은 표 구조를 쓸 수 있다
- acceptance와 overrun evidence가 섞이지 않는다
- 사실 표와 해석 표가 분리되어 있다
- 같은 질문에 다른 답을 내도 갈리는 지점이 바로 보인다

### Pass 3. 편향/오탐 방지 감리

아래를 모두 만족해야 한다.

- `Arc 1 성공`과 `Arc 2 과주행`을 다른 축으로 적는다
- 오탐 후보는 반드시 `false positive / noise`로만 적는다
- 아래 예시는 `confirmed bottleneck`으로 승격하지 않는다
  - `dialogue 0%`
  - `scene coverage 0%`
  - `ending hook miss`
  - `InfoParadox`

---

## 6. 수용 기준

최종 결과 문서는 아래를 모두 만족해야 한다.

- 같은 입력 파일 목록을 사용한다
- 메인 바디 표 구조가 동일하다
- `Arc 1 = acceptance`, `Arc 2+ = overrun evidence`가 명시되어 있다
- 최소 1개 `Episode x Round Breakdown` 표가 있다
- 최소 1개 `Root-Cause Taxonomy` 표가 있다
- 비교 시 “같은 사실, 다른 해석”이 바로 보인다
- 기존 SSOT와 충돌하지 않는다
- 이 문서의 결과는 SSOT를 대체하지 않고 `runtime/cost cross-check layer`로만 동작한다

---

## 7. 기본 가정

- 이번 비교는 `00_test_00` 한 런만 대상으로 한다.
- `Arc 2`는 acceptance 증거가 아니라 병목 분석 증거다.
- 메인 오더 문서는 한국어로 작성한다.
- appendix에서만 개별 에이전트의 관점 차이를 허용한다.
- 결과 비교의 목적은 우열 판정보다 `사실 / 해석 / 가설`의 경계를 또렷하게 만드는 데 있다.
