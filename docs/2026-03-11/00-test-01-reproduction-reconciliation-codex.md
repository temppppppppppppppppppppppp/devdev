# 00_test_01 Reproduction Reconciliation — Codex

> 작성일: 2026-03-11  
> 원문 1: [00-test-01-reproduction-crosscheck-codex.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-01-reproduction-crosscheck-codex.md)  
> 원문 2: [00-test-01-reproduction-crosscheck-report-OPUS.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-01-reproduction-crosscheck-report-OPUS.md)  
> 성격: 원문 수정 없는 reconciliation layer

## 최종 결론
최종 판정은 `재현함`으로 유지한다. 추가로 수행한 `00_test_01` 4편 manual reading 결과 prose-level blocker가 해소되었으므로, reconciliation 기준 최종 확신도는 `95%`로 올린다. OPUS 원문과 OPUS reconciliation 원문은 그대로 두되, Codex reconciliation은 후속 manual reading evidence를 반영한 최신 판정으로 본다.

## 합의 사실

| 항목 | 합의 내용 | 공통 근거 |
|---|---|---|
| 최종 verdict | `00_test_01`은 `00_test_00` Arc 1 baseline을 `재현함` | 두 원문의 최종 한줄 판정 |
| artifact parity | `arc_001`, `blueprint_0001~0004`, `ep_0001~0004`가 모두 존재하고 Arc 1 범위를 완주했다 | 두 원문의 `Artifact Parity`, session log |
| pipeline parity | `Stage 2 -> 3 -> 4`가 모두 PASS로 끝났고 `4화 생산`, `1개 Arc 완료`가 확인된다 | `session_20260311_183911.log`, 두 원문 `Run Summary` |
| DB parity | `episode_quality_labels=4`, `episode_quality_signals=4`, `episode_quality_observations=0`은 baseline과 동일하다 | `project_data.db`, 두 원문 |
| material divergence | `material divergence`는 0건이다 | 두 원문의 `Delta Taxonomy` |
| drift 성격 | retry 횟수, 비용, runtime audit tag 차이는 `acceptable drift` 또는 개선된 observability로 읽는 것이 맞다 | `pass_rate_monitor.json`, `metrics_20260311_183915.json`, `runtime_audit_summary.json`, 두 원문 |

## 해석 차이

| 항목 | Codex 해석 | OPUS 해석 | reconciliation 판단 |
|---|---|---|---|
| 95% 확신도 도달 여부 | artifact/stage/state parity만으로 `95%` 허용 가능 | prose-level manual reading 미수행이라 `92%`, 95% 미달 | 후속 manual reading을 수행한 결과 `hard contradiction`가 없고, 남은 차이가 baseline defect class 범위의 soft drift로 확인되었으므로 현재 reconciliation은 `95%` 채택 |
| baseline fidelity의 경계 | `ep4` 시간축 drift는 baseline도 같은 defect class를 가졌으므로 `acceptable drift` | 같은 결론이지만, prose-level 구조 확인 전까지 confidence를 덜 준다 | 사실 충돌은 없고 confidence policy 차이만 존재 |
| 무엇이 핵심 blocker인가 | `baseline live draft` 부재가 남은 5% | `00_test_01` 4편 manual reading + `00_test_00` pinned score 대조가 blocker | manual reading은 해소되었다. score 대조는 `95%` 필수 blocker가 아니라 보조 검증으로 하향 |

해석 차이의 본질:

- 두 문서는 같은 사실을 보고 있다.
- 원문 단계의 차이는 `reproduction verdict`가 아니라 `95%를 artifact/state parity만으로 줄 수 있느냐`에 있었다.
- 후속 manual reading 이후에는 그 정책 차이가 사실상 해소되었다.

## 편측 발견

| 출처 | 항목 | 내용 | 최종 반영 |
|---|---|---|---|
| Codex | ep4 residual time drift | baseline manual audit의 `약 2주 후 -> 다음 날 오후 -> 일주일 후`와 같은 defect class가 candidate에도 남아 있다고 명시 | 유지. 다만 `acceptable drift`로만 사용 |
| Codex | baseline live draft 부재 | `00_test_00` reset 이후 live draft direct compare가 불가하다는 점을 강하게 강조 | 유지. confidence 상한을 낮추는 보조 사유 |
| Codex | post-reconciliation manual reading | `ep_0001~0004`를 직접 읽은 결과, 4편 모두 blueprint가 요구한 핵심 scene/hook을 유지하고 `hard contradiction`가 없음을 확인 | 유지. `95%` 승격의 직접 근거 |
| OPUS | score consistency | `00_test_01` 4개 에피소드가 모두 `98점 PASS`로 정렬되었다는 관찰 | 유지. 재현 verdict을 강화하지만 95% 단독 근거로는 사용하지 않음 |
| OPUS | D-13 manual reading blocker | prose-level manual reading 없이는 텍스트 수준 재현을 완전히 닫지 않겠다는 기준 제시 | 유지. 다만 후속 manual reading으로 해소됨 |

## 최종 판정에 영향 주는 쟁점

1. `재현 verdict` 자체를 뒤집는 쟁점은 없다.  
   두 원문 모두 `material divergence=0`, `재현함`이다.

2. 원문 시점의 실질 쟁점은 `95% 확신도`뿐이었다.  
   Codex는 오더 문서의 `artifact/stage/state parity`를 더 중시했고, OPUS는 `같은 재료, 같은 방식` 문구를 더 엄격하게 읽어 prose-level manual audit를 요구했다.

3. 최신 reconciliation은 후속 manual reading evidence를 반영해, 원문 간 confidence 차이를 해소한다.  
   이유는 다음과 같다.
   - 더 엄격한 OPUS 기준이 요구한 `manual reading`이 실제로 수행되었다.
   - 그 결과 `hard contradiction`가 없고 `material divergence`도 여전히 0건이다.
   - 남은 차이는 baseline manual audit가 이미 기록한 soft drift class뿐이다.

## 남는 불확실성

1. `00_test_00` reset 이전 live draft와의 direct text compare는 불가능하다.
2. `ep4`의 elapsed-time / 자본금 exact surface form은 baseline defect class와 같은 계열이지만 완전 동일성을 주장하지는 않는다.
3. 이번 판정은 여전히 `technical validation baseline reproduction` 범위이며, `real production`이나 `실프로젝트` 검증으로 확장되지 않는다.

## 다음 스텝

1. 필요 시 `00_test_00` pinned session log의 episode-level score를 보조 대조
2. `95%`는 현재 닫혔으므로, 다음 비교가 필요하면 `real project` 또는 별도 sample reproduction으로 확장

## Close-Out

- 합의 사실: 충분
- 해석 차이: 원문 기준 1건 (`95% confidence policy`)이었으나 후속 manual reading으로 해소
- 편측 발견: verdict를 뒤집을 수준 없음
- reconciliation 판정: `재현함 유지 / 확신도 95% / prose-level blocker 해소`

## 사후 처리: OPUS 편측 발견 응답

| UF-id | 판정 | 근거 한줄 |
|---|---|---|
| UF-1 | 동의 | `00_test_00` live DB 공조회 결과 현재 `manuscripts=0`, `stage_attempts=0`, `director_selections=0`, `llm_calls=528`로 확인되어 OPUS 실증이 맞고 baseline pinned-source 원칙과도 충돌하지 않는다. |
| UF-2 | 동의 | `00_test_01` 세션 로그의 ep3 REJECT 사유가 `[V67] History Conflict`와 `18년의 실패에서 얻은 교훈` vs `운동선수의 반사신경` 동기 역전으로 직접 확인되어 baseline ep1 실패 계열과 원인 축이 다르다는 OPUS 정리가 유효하다. |
| UF-4 | 동의 | `00_test_01/logs/quality_metrics.jsonl`에서 ep1~4 모두 `ced_score=0.0`, `ai_slop_score<=1.0`, 길이/대화 계열 warning noise 패턴이 확인되어 OPUS의 품질 신호 패턴 match 분리는 실질적으로 Codex 해석과 합치한다. |
