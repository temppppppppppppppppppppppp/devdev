# Stage 4 9화 로그 전수조사 3PASS 최종 감리 보고서

작성일: 2026-03-13  
대상 런: `projects/000__t` Stage 4 episode 1-9  
조사 원칙: 읽기 전용, 코드 수정 금지, 테스트 실행 금지  
연계 실행 문서:

- [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md)
- [stage4-director-cw-feedback-loop-remediation-5pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-5pass-audit.md)

최종 판정: `runtime success`, retained `P1 1건`, retained `P2 2건`, `Observation 3건`, 확신도 `95%`

## Executive Summary

이번 Stage 4 9화 런은 멈추지 않았다. [runtime_audit_summary.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 기준 `stage4_complete`로 종료됐고, [drafts](/C:/Users/User/Desktop/글도비/projects/000__t/drafts) 기준 `ep_0001.txt`부터 `ep_0009.txt`까지 9편이 모두 생성됐다. [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) 기준 `stage_attempts(stage=4)=13`, `director_selections(stage=4)=13`도 서로 맞는다.

다만 `clean run`으로 닫을 수는 없다.

- `P1`: 8화는 Blueprint/직전 화 연속성 충돌 때문에 5회 시도와 2회 `Contradiction Firewall`을 거친 뒤에야 PASS로 회복됐다.
- `P2`: Director 피드백과 orchestration advisory가 실제 reject reason 문자열에서 섞여 기록된다.
- `P2`: `stage_attempts` sink는 여전히 얇아서 DB 단독으로는 Director-CW rationale을 복원할 수 없다.

반대로 기각한 것도 분명하다.

- 런타임 crash, artifact missing, sink alignment mismatch, mojibake는 확인되지 않았다.
- 기존 `candidate/artifact lineage drift` 류 문제는 이번 런에서 재발하지 않았다.
- 이번 런은 `PASS_WITH_FIX -> PASS_WITH_FIX` 재심사 루프를 직접 밟지 않았기 때문에, 그 retained code-path를 runtime으로 닫거나 반증하지는 못한다.

## Scope

이번 조사 범위는 아래 8개로 고정했다.

1. Stage 4 종료 여부와 draft/artifact/DB 정합성
2. `episode_production.jsonl`와 `pass_rate_monitor.json`의 시도 기록
3. `director_selections`와 `stage_attempts`의 attempt-level observability
4. 8화 다회 reject와 최종 회복 경로
5. 9화 첫-pass 성공 경로
6. Director fallback, firewall, consistency skip 경고의 실제 영향
7. Director-CW feedback loop remediation SSOT와의 직접 연결
8. 오탐 제거와 실행 우선순위 재판정

주요 증거는 아래에서 수집했다.

- [session_20260313_000215.log](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log)
- [pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl)
- [runtime_audit_summary.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json)
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db)
- [ep_0008.txt](/C:/Users/User/Desktop/글도비/projects/000__t/drafts/ep_0008.txt)
- [ep_0009.txt](/C:/Users/User/Desktop/글도비/projects/000__t/drafts/ep_0009.txt)
- [patched_after_fix__A_inplace_patch.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0008/attempt_05/patched_after_fix__A_inplace_patch.txt)
- [final_manuscript__A.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A.txt)

## 조사 Pass 1. 사실 수집

### 1. 런타임은 정상 종료됐다

- [runtime_audit_summary.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 에 `tag=stage4_complete`
- [drafts](/C:/Users/User/Desktop/글도비/projects/000__t/drafts) 에 9개 원고 존재
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) 에 `stage_attempts(stage=4)=13`
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) 에 `director_selections(stage=4)=13`

즉 `9화까지 생산 실패`, `중간 중단`, `sink 누락` 같은 blocker는 없다.

### 2. 8화만 집중적으로 흔들렸다

[pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json) 기준 Stage 4 요약은 아래와 같다.

- 1화~7화: 각 1회 시도 후 PASS
- 8화: 5회 시도, 4회 REJECT, 1회 PASS
- 9화: 1회 시도 후 PASS

8화 누적 비용도 압도적이다.

- 시도 수: `5`
- 누적 duration: `1,804,936 ms`
- 누적 token_cost: `1.660193`

다른 화는 대부분 `0.4~0.73` 수준이다. 즉 8화는 단순 잡음이 아니라, 별도 원인군이 있는 outlier다.

### 3. attempt lineage는 깨끗하다

`stage_attempts`, `director_selections`, `episode_production.jsonl`을 attempt_key로 맞대면 13/13/13 전부 대응된다. 이번 런에서는 과거 canary에서 보인 sink alignment drift가 재발하지 않았다.

- `attempt_key` 누락된 4행은 `TF49b_PREFLIGHT` 이벤트 row일 뿐이며, attempt row corruption이 아니다.
- attempt row 13건의 `candidate_key`, `artifact_path`, `selection_artifact_path`는 서로 논리적으로 맞는다.

즉 `lineage drift`는 이번 런의 retained finding이 아니다.

## 조사 Pass 2. 교차 검증

### 1. 8화의 4회 reject는 LLM 일반론이 아니라 연속성 충돌로 수렴한다

로그와 structured sink가 같은 이야기를 한다.

- [session_20260313_000215.log#L6361](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6361) 에서 8화 3차 면담은 `Contradiction Firewall: CRITICAL 1건`으로 강제 REJECT
- [session_20260313_000215.log#L6362](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6362) 는 7화에서 이미 끝난 사건 순서를 8화가 다시 밟는다고 적시
- [session_20260313_000215.log#L6828](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6828) 와 [session_20260313_000215.log#L6829](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6829) 도 같은 취지의 재충돌을 보여준다
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl) 의 8화 3차/4차 row `open_review`는 Blueprint 자체가 직전 7화 엔딩과 충돌한다고 명시한다
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) 의 `director_selections(stage=4, ep=8)`도 3차와 4차에서 `firewall_triggered=1`

이건 `CW가 멋대로 못 썼다`보다 `상류 blueprint frontier가 7화 엔딩과 겹쳤다`에 더 가깝다.

### 2. 8화는 patch path로 회복됐다

- [session_20260313_000215.log#L6986](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6986) 에서 8화 5차 시도는 PASS 98
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl) 의 8화 최종 row는 `candidate_key=A|inplace_patch`
- [pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json) 의 같은 시도는 `generation_method=patch`, `is_patch=true`
- [patched_after_fix__A_inplace_patch.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0008/attempt_05/patched_after_fix__A_inplace_patch.txt) 와 [ep_0008.txt](/C:/Users/User/Desktop/글도비/projects/000__t/drafts/ep_0008.txt) 가 대응한다

즉 회복은 우연한 candidate 교체가 아니라, patch 기반 재정렬이다.

### 3. 9화는 첫 시도 PASS지만 warning 해석은 조심해야 한다

- [session_20260313_000215.log#L7540](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L7540) 에서 9화는 첫 Director 판정 PASS 96
- [final_manuscript__A.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A.txt) 길이는 `4024`
- [ep_0009.txt](/C:/Users/User/Desktop/글도비/projects/000__t/drafts/ep_0009.txt) 길이도 `4038`

그런데 [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl) 의 9화 최종 row `warnings`에는 `3176자`, `4개 씬 중 0개 감지` 같은 rejected candidate성 경고가 함께 들어 있다. 즉 이 `warnings` 배열은 final manuscript 전용 defect list가 아니라 candidate aggregate에 가깝다.

### 4. Stage 4 DB 관측성은 아직 얇다

`attempt_key` 정합성은 깨끗하지만, [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) 의 `stage_attempts(stage=4)`는 여전히 아래 필드가 `null`이다.

- `selection_reason`
- `verdict_reason`

반면 같은 attempt_key의 [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) `director_selections(stage=4)` 와 [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl) 에는 rationale이 있다.

즉 `DB 단독 포렌식`은 아직 안 된다. 이건 [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) 의 `E-3 loop observability 보강`이 여전히 유효하다는 증거다.

### 5. Director feedback provenance도 여전히 hybrid다

[pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json) 의 8화 reject_reason은 아래가 한 blob으로 붙는다.

- Director action items
- `[자유 리뷰]`
- `[R0/R1/R2 이전 지시]`
- `[Advisory 핵심 요약 - 재시도 시 반영]`

즉 runtime에서도 `Director-origin feedback`과 `orchestrator-injected advisory`가 분리 저장되지 않는다. 이 역시 [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) 의 `E-2 provenance 분리`가 그대로 살아 있는 이유다.

## 조사 Pass 3. 오탐 제거

### 기각 1. 런타임 crash

기각. [runtime_audit_summary.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/runtime_audit_summary.json) 는 정상 종료이고, 조사한 범위에서 `Traceback` 기반 미복구 예외는 보지 못했다.

### 기각 2. sink alignment 재파손

기각. 13개 attempt_key가 세 sink에서 모두 대응했고 candidate/artifact mismatch가 없다.

### 기각 3. mojibake

기각. 이번 조사에서 읽은 draft, artifact, JSON, DB 기반 문자열은 UTF-8로 정상 판독됐다.

### 기각 4. `full_fallback` 자체를 실패로 해석

기각. `full_fallback`은 13회 모두 발생했지만, 9화 중 8개 화가 첫 시도 PASS고 8화도 최종 회복했다. 현재 증거로는 `degrade path`이지 failure 근거가 아니다.

## 감리 Pass 1. retained finding 정리

### P1. 8화는 Blueprint frontier 연속성 충돌 때문에 Stage 4에서 4회 reject를 소모했다

근거:

- [session_20260313_000215.log#L6361](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6361)
- [session_20260313_000215.log#L6828](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6828)
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl)
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db)

판단:

- 이건 `Stage 4 엔진 붕괴`가 아니라 `상류 blueprint/frontier debt가 runtime에서 폭발`한 경우다.
- 그래도 실제 비용은 크다. 8화 단독으로 `5 attempts / 1.80M ms / 1.66 token_cost`를 썼다.
- 따라서 severity는 `P1`로 두는 게 맞다.

비고:

- 이 finding은 다음 실행 문서인 [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) 의 직접 범위 밖이다.
- 즉 Director-CW loop remediation만으로는 닫히지 않는다.

### P2. Director feedback provenance가 reject_reason에서 여전히 혼합 기록된다

근거:

- [pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)
- 8화 attempt 2~4 reject_reason blob

판단:

- 실제 runtime에서도 `Director review`, `이전 지시`, `Advisory 요약`이 한 문자열로 저장된다.
- CW 입력 provenance와 postmortem 가독성을 모두 해친다.
- 이 finding은 다음 실행 문서의 `E-2`와 정확히 연결된다.

### P2. `stage_attempts`는 여전히 thin sink라 DB 단독 포렌식이 안 된다

근거:

- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) `stage_attempts(stage=4)`
- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db) `director_selections(stage=4)`
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl)

판단:

- `attempt_key` 정합성은 clean이다.
- 하지만 `selection_reason`, `verdict_reason`가 `stage_attempts`에 없어서 DB 단독 조사면 절반만 보인다.
- 이 finding은 다음 실행 문서의 `E-3`와 정확히 연결된다.

## 감리 Pass 2. Observation 정리

### Observation 1. `episode_production.warnings`는 final manuscript defect list가 아니다

근거:

- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl) 9화 최종 row
- [final_manuscript__A.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A.txt)

판단:

- final PASS row에도 rejected candidate 경고가 같이 섞인다.
- 현재는 `경고 해석 주의` 수준으로 두고, 별도 blocker로 올리지는 않는다.

### Observation 2. `full_fallback`은 13/13이지만 실패 증거는 아니다

근거:

- [session_20260313_000215.log](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log)

판단:

- prompt size가 큰 Stage 4에서 fallback 빈도는 높다.
- 지금 증거로는 `성능/비용 문제`이지 `정합성 결함`은 아니다.

### Observation 3. `I-04` skipped context 경고는 반복되지만 런타임을 막지 않았다

근거:

- [session_20260313_000215.log](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log) 에 `I-04` 37회

판단:

- context coverage gap 신호로는 의미가 있다.
- 하지만 이 런에서는 reject root cause보다 보조 경고에 가까웠다.

## 감리 Pass 3. 실행 문서 적합성 재판정

현재 retained 중 다음 실행 문서와 직접 연결되는 것은 2건이다.

- `P2 provenance 혼합` -> [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) `E-2`
- `P2 thin sink` -> [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) `E-3`

반대로 8화 `P1`은 다음 실행 문서의 범위를 넘어선다. 이건 blueprint/frontier continuity remediation 쪽으로 따로 다뤄야 한다.

또 한 가지 중요하다. 이번 런은 `PASS_WITH_FIX -> PASS_WITH_FIX` 재심사 루프를 직접 밟지 않았다. 따라서 다음 실행 문서의 `E-1`을 runtime으로 반증하지는 못했다. `E-1`은 여전히 code-level retained target으로 남는다.

## 재감리와 확신도 Ledger

- `70`: session log, JSONL, DB, draft, artifact, runtime summary 전량 수집 완료
- `+10`: `attempt_key` 기준 13/13/13 sink alignment 확인
- `+5`: 8화 reject root cause를 log/JSONL/DB 세 계층으로 교차검증
- `+5`: 실행 문서 `E-2`, `E-3`와 runtime 증거 연결 완료
- `+5`: `full_fallback`, mojibake, sink corruption 오탐 제거 완료
- `-0`: 현재 조사 범위에서 추가 blocker 없음
- `-0`: 남은 불확실성은 `E-1` code-path 미실행이라는 runtime-only 한계뿐이며, 이번 보고서의 retained 판정과 직접 충돌하지 않음

최종 확신도: `95%`

## 최종 결론

이 Stage 4 9화 런은 `문제가 전혀 없는 clean run`은 아니다. 그러나 `런타임 실패`도 아니다.

- production 자체는 성공했다.
- 8화에서 상류 blueprint/frontier debt가 크게 드러났다.
- Director-CW remediation 범위로는 provenance 혼합과 thin sink가 runtime에서도 살아 있다.
- 다음 실행 오더는 여전히 [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md) 와 [stage4-director-cw-feedback-loop-remediation-5pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-5pass-audit.md) 가 맞다.
- 다만 그 문서들만으로는 8화에서 드러난 상류 continuity debt를 닫지 못한다.

즉 이번 보고서의 결론은 한 줄로 이렇다.

`Stage 4 9화 런은 성공했지만, Director-CW loop remediation은 여전히 필요하고, 8화 continuity debt는 별도 축으로 처리해야 한다.`
