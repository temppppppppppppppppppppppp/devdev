# 00_test_02 / 00_test_03 Frozen Control-vs-Failed-Treatment Cross-Check Order

> 작성일: 2026-03-11
> 상태: 비교군 공용 오더
> 용도: Codex / OPUS 병렬 감리용
> 성격: `frozen control-vs-failed-treatment runtime/cost/quality decision layer`
> 비고: 기존 SSOT와 reproduction 문서를 대체하지 않는다

---

## 0. 목적

이 문서는 `projects/00_test_02`와 `projects/00_test_03`를 같은 재료, 같은 방식의 `1 arc / ep_0001~ep_0004` 범위에서 비교해, 현재 운영 프로파일의 다음 판단을 내리기 위한 공용 오더다.

- `00_test_02`는 `2.5-pro` 중심 control run이다.
- `00_test_03`는 `gemini-3.1-flash-lite-preview` 중심 treatment run이었고, 현재는 **종료된 실패 스냅샷**이다.

이번 비교의 핵심 질문은 아래 네 가지다.

1. `00_test_02`는 현재 accepted 운영 프로파일의 재현성과 비용/시간 개선 효과를 다시 확인하는가
2. `00_test_03`는 왜 실패했는가, 그리고 그 실패를 시스템 코어 결함이 아니라 모델/profile 비적합으로 분리 가능한가
3. `00_test_03`의 실패 패턴은 blueprint/arc 품질과 얼마나 분리되는가
4. 현재 근거만으로 control 권고와 treatment 비채택 권고를 `95%` 확신도로 말할 수 있는가

이 오더의 목적은 `누가 더 그럴듯하게 말하느냐`를 겨루는 것이 아니라, 아래 셋을 분리하는 데 있다.

- 무엇이 **확실한 control 사실**인가
- 무엇이 **확실한 treatment 실패 신호**인가
- 무엇이 **추가 판독 없이는 닫히지 않는 불확실성**인가

두 에이전트는 반드시 **같은 입력**, **같은 taxonomy**, **같은 표 구조**를 사용해야 한다.
다른 해석은 appendix에만 적는다.

---

## 1. 고정 입력과 비교 기준

### 1.1 비교 대상

- control: `projects/00_test_02` (`completed control snapshot`)
- treatment: `projects/00_test_03` (`terminated failed treatment snapshot`)
- 비교 범위: `Arc 1 / ep_0001~ep_0004`

### 1.2 필수 입력

#### control (`00_test_02`)

- `projects/00_test_02/project_data.db`
- `projects/00_test_02/plans/arcs/arc_001.txt`
- `projects/00_test_02/plans/blueprints/`
- `projects/00_test_02/drafts/`
- `projects/00_test_02/logs/session_20260311_200424.log`
- `projects/00_test_02/logs/metrics/metrics_20260311_200432.json`
- `projects/00_test_02/logs/pass_rate_monitor.json`
- `projects/00_test_02/logs/quality_metrics.jsonl`
- `projects/00_test_02/logs/episode_production.jsonl`
- `projects/00_test_02/logs/runtime_audit.jsonl`
- `projects/00_test_02/logs/runtime_audit_summary.json`

현재 상태로 고정되는 사실:

- drafts `ep_0001.txt` ~ `ep_0004.txt` 존재
- `runtime_audit_summary.tag = stage4_complete`

#### treatment (`00_test_03`)

- `projects/00_test_03/project_data.db`
- `projects/00_test_03/plans/arcs/arc_001.txt`
- `projects/00_test_03/plans/blueprints/`
- `projects/00_test_03/drafts/`
- `projects/00_test_03/logs/session_20260311_201731.log`
- `projects/00_test_03/logs/metrics/metrics_20260311_201738.json`
- `projects/00_test_03/logs/pass_rate_monitor.json`
- `projects/00_test_03/logs/quality_metrics.jsonl`
- `projects/00_test_03/logs/episode_production.jsonl`
- `projects/00_test_03/logs/runtime_audit.jsonl`
- `projects/00_test_03/logs/runtime_audit_summary.json`

현재 상태로 고정되는 사실:

- drafts `ep_0001.txt`, `ep_0002.txt`만 존재
- `runtime_audit_summary.tag = stage3_complete`
- Stage 4는 미완주 상태로 종료됨

#### 기준 문서

- `docs/2026-03-11/00-test-01-reproduction-crosscheck-codex.md`
- `docs/2026-03-11/00-test-01-reproduction-reconciliation-codex.md`
- `docs/2026-03-11/ops-runtime-cost-reconciliation-codex.md`
- `docs/2026-03-11/00-test-00-stage234-ssot-3pass.md`

### 1.3 해석 규칙

- `00_test_02`는 `accepted control profile`의 재측정 run으로 해석한다.
- `00_test_03`는 `all-lite cost/perf experiment`의 **종료된 실패 스냅샷**으로 해석한다.
- `00_test_03`는 이번 감리에서 더 이상 “아직 끝나지 않았을 수 있는 live run”으로 해석하지 않는다.
- `00_test_03`의 핵심 질문은 `채택 가능성 탐색`이 아니라 `실패 원인 분해`다.
- `00_test_03`의 `채택 가능` 경로는 이번 감리 범위에서 사실상 닫는다.
- `00_test_03`가 Stage 4 중도 붕괴, 반복 REJECT, ep 미완료, 심각한 drift를 보이면 로그/DB 근거만으로 `채택 불가` 판정이 가능하다.
- 이번 감리는 `Arc 1 / ep_0001~ep_0004`까지만 본다.
- 코드 수정, 추가 런 실행, 대시보드 호출은 포함하지 않는다.

### 1.4 fail-closed 규칙

1. `00_test_02` 또는 `00_test_03`의 필수 입력이 누락되면, 그 누락을 먼저 기록하고 `hypothesis pending` 또는 `failure signal` 후보로 올린다.
2. `00_test_03`의 `채택 가능` 또는 `조건부 가능` 판정은 이번 감리 범위에서 허용하지 않는다.
3. `00_test_03`의 `채택 불가` 판정은 아래 중 하나면 즉시 가능하다.
   - ep_0003 또는 ep_0004 미생산
   - `runtime_audit_summary.tag`가 `stage4_complete`에 도달하지 못함
   - 반복 REJECT 뒤 Stage 4 종료
   - runtime/cost가 control 대비 현저히 악화되면서 quality 신호도 불안정
4. prose 차이만으로는 `failure signal`로 승격하지 않는다.
5. 반대로 stage completeness, artifact completeness, 반복 REJECT, retry 폭증은 문체 차이와 무관하게 `failure signal` 후보다.
6. `00_test_03` manual reading은 `채택 가능성 판단`이 아니라 `실패 원인 분해`용 partial postmortem으로만 사용한다.

---

## 2. 공통 taxonomy

본문에서 허용되는 taxonomy는 아래 네 개뿐이다.

- `confirmed control parity`
- `acceptable drift`
- `failure signal`
- `hypothesis pending`

아래 단어는 본문에서 쓰지 않는다.

- `bug`
- `issue`
- `problem`

반드시 taxonomy 용어만 쓴다.

---

## 3. 공통 작업 명세

두 에이전트는 아래 3-pass를 **동일한 순서**로 수행한다.

### Pass 1. 실행 사실 고정

목표: `00_test_02`와 `00_test_03`가 실제로 어디까지 갔는지 해석 없이 고정한다.

#### 표 A. Run Snapshot

| project | profile | scope | stage2 | stage3 | stage4 | runtime_audit_tag | blueprint_count | draft_count | stage_attempts | director_selections | total_tokens | total_cost_usd | source |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

작성 규칙:

- `profile`은 아래만 허용한다.
  - `control-2.5-pro`
  - `treatment-3.1-flash-lite`
- `scope`는 `Arc 1 / ep_0001~ep_0004`로 고정한다.
- `runtime_audit_tag`는 `stage4_complete`, `stage3_complete`, `missing` 중 하나로 적는다.
- `blueprint_count`, `draft_count`는 실제 파일 존재 수를 적는다.
- `total_tokens`, `total_cost_usd`는 metrics 기준으로 적는다.
- `draft_count`와 `runtime_audit_tag`는 이번 비교의 핵심 판정 축으로 취급한다.

#### 표 B. Artifact / Completion Matrix

| project | artifact | expected | observed | parity | notes | source |
|---|---|---|---|---|---|---|

작성 규칙:

- `artifact`는 최소 아래를 포함한다.
  - `arc_001`
  - `blueprint_0001~0004`
  - `ep_0001~0004`
  - `runtime_audit_summary`
  - `quality_metrics`
  - `episode_production`
- `parity`는 아래만 허용한다.
  - `match`
  - `near-match`
  - `mismatch`
  - `missing`

### Pass 2. 차이 분해

목표: control은 얼마나 안정적으로 재현되었고, treatment는 어디서 실패/성공했는지 분리한다.

#### 표 C. Decision Taxonomy

| id | project | taxonomy | evidence | current interpretation | impact on operating-profile decision | next check point | confidence |
|---|---|---|---|---|---|---|---|

작성 규칙:

- `impact on operating-profile decision`은 아래 중 하나로 적는다.
  - `none`
  - `low`
  - `medium`
  - `high`
- 최소 검토 축:
  - Stage 2/3/4 완료 여부
  - `stage4_complete` 도달 실패 여부
  - blueprint / draft completeness
  - retry 규모 (`stage_attempts`, `director_selections`)
  - 총 비용 / 총 시간
  - `ep3` repeated REJECT cluster
  - `00_test_03`의 manual-reading postmortem 필요 여부
  - `00_test_03`의 failure가 시스템 전반이 아니라 profile 특이인지 여부
  - `profile-induced instability vs blueprint-quality ambiguity`

### Pass 3. 운영 권고 판정

목표: 현재 근거만으로 `00_test_02`와 `00_test_03`에 대한 운영 권고를 고정한다.

#### 표 D. Decision Ladder

| claim | 00_test_02 | 00_test_03 | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|---|

최소 claim:

- `control profile reproducibility`
- `control profile cost/runtime observability`
- `treatment profile viability`
- `treatment profile quality trustworthiness`
- `next operating recommendation`

최종 본문에서는 반드시 아래 형식으로 한 줄 verdict를 낸다.

- `00_test_02`: `[재현함 / 부분 재현함 / 재현 실패]`
- `00_test_03`: `[채택 불가]`

`95%`를 넘겨 말하려면 아래 조건을 모두 만족해야 한다.

- `00_test_02`는 핵심 claim이 모두 `confirmed control parity` 또는 `acceptable drift`
- `00_test_03`는 `채택 불가` 판정의 핵심 근거가 artifact completeness와 종료 상태에서 닫혀 있어야 한다
- `00_test_02`의 `95%`는 control 재현/운영 권고에 대한 확신도이고, `00_test_03`의 `95%`는 실패 판정 확신도로 해석한다
- `hypothesis pending`이 최종 운영 권고를 흔들지 않음

---

## 4. 본문 구조 고정

Codex와 OPUS는 메인 바디를 아래 구조로 **완전히 동일하게** 작성한다.

1. `최종 한줄 판정`
2. `Pass 1. 실행 사실 고정`
3. `Pass 2. 차이 분해`
4. `Pass 3. 운영 권고 판정`
5. `비교용 요약`

`비교용 요약`은 아래 5문항에 대해 한 줄씩 답한다.

- `00_test_02`는 control run으로서 재현되었는가
- `00_test_03`는 왜 채택 불가인가
- 비용/시간 기준에서 treatment의 손해 또는 제한적 이득은 무엇인가
- quality 신뢰성은 어디서 흔들리는가
- 다음 단계는 `P2`, `재측정 추가`, `운영 채택`, `실험 중단` 중 무엇인가

---

## 5. Appendix 규칙

appendix는 독립 허용이다. 다만 섹션명은 반드시 아래 둘만 사용한다.

### Appendix A. Agent-specific observations

- 본문에 넣지 않은 독자 관찰을 적는다.
- 단, 본문 사실과 충돌하는 새 사실은 금지한다.

### Appendix B. 반례 / 이견 / 추가 가설

- 상대 에이전트와 갈릴 수 있는 해석만 적는다.
- treatment 실패 원인을 profile 리스크로 볼지, blueprint/arc 품질 리스크로 볼지의 차이도 여기서만 적는다.
- 근거 없는 추정은 금지한다.

---

## 6. Reconciliation 규칙

Codex와 OPUS 원문이 모두 나오면 reconciliation 문서는 아래 3분류만 사용한다.

- `합의 사실`
- `해석 차이`
- `편측 발견`

reconciliation의 목적은 `누가 이겼는가`가 아니라 아래를 분리하는 데 있다.

- `00_test_02`에 대한 공통 판단
- `00_test_03`에 대한 공통 판단
- `95%` 미달 사유가 진짜 사실 충돌인지, 해석 보수성 차이인지

`00_test_03`에 대해서는 아래 셋을 분리하도록 유도한다.

- `합의 사실`: 미완주, `stage3_complete`, `ep_0001~ep_0002`만 존재
- `해석 차이`: 실패 원인을 profile 리스크로 볼지, blueprint/arc 품질과 섞인 것으로 볼지
- `편측 발견`: 특정 로그 신호나 drift가 추가 확인 후에도 닫히지 않은 항목

편측 발견은 가능하면 같은 턴에 source-level 추가 확인을 끝까지 수행하고, 확인 가능한 항목은 `합의 사실` 또는 `해석 차이`로 이동한다. 끝까지 닫히지 않는 항목만 최종적으로 `편측 발견`으로 남긴다.

---

## 7. 3-Pass 감리 기준

### Pass 1. 오더 문서 자체 감리

아래를 모두 만족해야 한다.

- 입력 파일 목록이 고정되어 있다
- control과 treatment 역할이 고정되어 있다
- 표 헤더가 고정되어 있다
- taxonomy가 4개로 고정되어 있다
- `00_test_03`가 종료된 실패 snapshot이라는 사실이 문서에 박혀 있다
- `00_test_03 채택 가능` 경로가 사실상 닫혀 있다

### Pass 2. 비교 가능성 감리

아래를 모두 만족해야 한다.

- Codex와 OPUS가 같은 표 구조를 쓸 수 있다
- `00_test_02`와 `00_test_03`가 섞이지 않는다
- 사실과 해석이 분리된다
- control 재현과 treatment 실패 postmortem이 다른 질문이라는 점이 드러난다

### Pass 3. 과장 방지 감리

아래를 모두 만족해야 한다.

- `00_test_02 재현 성공`을 곧바로 `00_test_03 채택 가능`으로 승격하지 않는다
- `00_test_03`의 단순 PASS 로그만으로 quality 신뢰를 선언하지 않는다
- manual reading 없이 `00_test_03`를 채택 가능으로 되살리지 않는다
- 반대로 `00_test_03`가 반복 REJECT와 미완주를 보이면 logs만으로 `채택 불가` 판정이 가능함을 명시한다

---

## 8. 수용 기준

최종 결과 문서는 아래를 모두 만족해야 한다.

- 같은 입력 파일 목록을 사용한다
- 메인 바디 표 구조가 동일하다
- `00_test_02 = control`, `00_test_03 = treatment`가 명시되어 있다
- 최소 1개 `Run Snapshot` 표가 있다
- 최소 1개 `Decision Taxonomy` 표가 있다
- 최소 1개 `Decision Ladder` 표가 있다
- `00_test_03`의 종료된 실패 상태가 문서 전반에서 일관되게 유지된다
- `00_test_03`의 채택 여부와 재현 여부를 혼동하지 않는다
- 기존 SSOT / reproduction 문서를 대체하지 않고 `control-treatment decision layer`로만 동작한다

---

## 9. 기본 가정

- 이번 비교는 `00_test_02`와 `00_test_03`의 `Arc 1 / ep_0001~ep_0004`만 대상으로 한다.
- `00_test_02`는 accepted 운영 프로파일 재측정이다.
- `00_test_03`는 all-lite cost/perf 실험이었고, 현재는 종료된 실패 snapshot이다.
- 메인 오더 문서는 한국어로 작성한다.
- appendix에서만 개별 에이전트의 관점 차이를 허용한다.
- 결과 비교의 목적은 우열 판정보다 `control 재현 / treatment 실패 원인 / 남은 불확실성`의 경계를 또렷하게 만드는 데 있다.

---

## 10. 오더 문서 감리 상태

- 최종 상태: 2026-03-11 기준 비교군 공용 오더 확정본
- 감리 수준: 3-pass 오더 감리 완료
- 비고: `00_test_03`는 종료된 실패 snapshot으로 고정되며, 이번 문서는 live treatment 평가가 아니라 failure postmortem 오더로 사용한다
