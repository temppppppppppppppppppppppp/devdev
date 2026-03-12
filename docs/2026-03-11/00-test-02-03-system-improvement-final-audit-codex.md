# 00_test_02 / 00_test_03 System Improvement Final Audit — Codex

> 작성일: 2026-03-11  
> 기준 문서 1: [00-test-02-03-control-treatment-crosscheck-codex.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-codex.md)  
> 기준 문서 2: [00-test-02-03-control-treatment-crosscheck-report-OPUS.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md)  
> 기준 문서 3: [TF-IPG-inplace-patch-guard.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/TF-IPG-inplace-patch-guard.md)  
> 성격: `system improvement reconciliation + code audit layer`  
> 원칙: 문서 안팎을 가리지 않고, 현재 worktree / 테스트 / 재현 스크립트까지 포함해 최종 판단한다.

## 최종 판정

현재 최종 판단은 아래로 고정한다.

- `00_test_02`는 accepted control profile의 재현 run으로 유지한다.
- `00_test_03`는 all-lite treatment의 종료된 실패 스냅샷이며, 비채택 판단을 유지한다.
- OPUS의 `TF-IPG` 수정은 **대체로 정당한 hardening**이며, 실제 코드에도 반영되어 있다.
- 다만 감리 중 TF-IPG와 별개로 **실패 런도 `stage4_complete`로 기록될 수 있는 correctness regression**을 발견했고, 현재 worktree에서 이를 수정했다.
- 따라서 이번 최종 문서의 운영 결론은 `TF-IPG는 채택`, `summary/tag semantics는 수정 완료`, `그 외 P0/P1/P2 변경은 분리 검증`이다.

현재 감리 확신도는 `95%`다. 남은 5%는 live rerun 미실행, feature-flag 분리 전 behavior-changing 변경의 실제 상호작용, 문서 바깥 변경의 merge 단위 미정리에서 온다.

## 감리 입력과 추가 검증

이번 최종 감리는 세 문서만 읽고 끝내지 않았다. 아래 증거를 추가로 사용했다.

- 현재 worktree의 `git diff --stat`
- TF-IPG에 언급된 실제 코드 경로 diff
- `Stage4Orchestrator`의 `stage4_complete` 기록 경로 직접 재현
- `stage4_complete` summary semantics 패치 적용
- 관련 테스트 재실행

실행한 검증:

1. `pytest -q tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_chief_writer_quality.py`  
   결과: `235 passed in 46.06s`

2. `pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_chief_writer_quality.py tests/test_cost_tracking.py tests/test_bridge_quality_summary.py tests/test_quality_sidecar_bootstrap.py tests/test_continuity_pin_guard.py tests/test_v75c_contradiction_firewall.py`  
   결과: `230 passed in 4.26s`

3. `Stage4Orchestrator._run_interview_loop()`를 강제로 `True`로 돌린 synthetic check  
   결과: early return이어도 `_write_audit_summary("stage4_complete")`가 호출됨. 즉, 현재 구현은 실패/중단 경로를 성공 summary로 오염시킬 수 있다.

4. `pytest -q tests/test_stage4_orchestrator.py`  
   결과: `47 passed in 1.94s`

5. `pytest -q tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_chief_writer.py`  
   결과: `204 passed in 45.99s`

6. `pytest -q tests/test_stage4_orchestrator.py`  
   결과: `48 passed in 1.86s`

7. `pytest -q tests/test_stage4_interview_round.py`  
   결과: `50 passed in 2.51s`

8. `pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py`  
   결과: `100 passed in 3.19s`

## 1. 합의점

세 문서와 현재 코드가 강하게 합의하는 사실은 아래다.

| 항목 | 합의 내용 | 최종 판단 |
|---|---|---|
| 최종 verdict | `00_test_02 = 재현함`, `00_test_03 = 채택 불가` | 합의 |
| 핵심 failure chain | `00_test_03 ep_0003`는 `86 -> 90 -> 50 -> 50 -> 43`로 무너졌고 `ep_0004`에 도달하지 못했다 | 합의 |
| Stage 분리 | `00_test_03` 실패는 주로 Stage 4에 집중돼 있고 Stage 2/3은 통과했다 | 합의 |
| chronic length shortfall | treatment는 `3085`, `3293~3763`, `2769`, `3211`자 등 반복적 분량 미달을 보였다 | 합의 |
| InPlace 축소 패턴 | `PASS_WITH_FIX -> InPlace patch -> 2,769자 축소 -> REJECT`는 실제 failure path다 | 합의 |
| TF-IPG 구현 | `chief_writer.py`, `stage4_interview_round.py`, `stage2_preflight.py`, `stage4_orchestrator.py`, `constants.py`, `chief_writer.yaml`, `validation.yaml`에 대응 수정이 실제 존재한다 | 합의 |

실무적으로 중요한 합의는 하나다.

`TF-IPG는 00_test_03에서 드러난 retry 낭비 패턴을 줄이는 유효한 방어선이다.`

## 2. 불일치와 조정

세 문서는 같은 failure를 보고 있지만, 해석 강도와 artifact 판정 기준은 다르다.

| 항목 | Codex 문서 | OPUS cross-check | TF-IPG 문서 | 최종 조정 |
|---|---|---|---|---|
| 실패 원인 귀속 | `profile instability`가 우세하지만 `blueprint_0003` seam 때문에 일부 `hypothesis pending` 유지 | `profile 비적합` 쪽으로 더 강하게 기운다 | `근본 원인 = preserve guard 부재`로 더 강하게 말한다 | 최종 조정은 `profile-dominant failure + blueprint seam ambiguity + preserve guard gap` |
| `runtime_audit_summary` 판정 | `00_test_03`는 `stage3_complete`라서 내용 기준 `mismatch` | 파일 존재 기준 `match`로 표기 | 직접 다루지 않음 | 최종 기준은 `파일 존재`가 아니라 `tag 의미`다. Codex 기준 채택 |
| TF-IPG의 causal weight | `supporting contributor` | `failure chain을 악화시킨 high-signal gap` | `근본 원인` | 최종 기준은 `retry-amplifying guard gap`이다. `sole cause`로 승격하지 않음 |
| 분량 감소 해석 | `과도한 축소`가 문제이며 국소 삭제 자체는 오류가 아님 | ep3의 `5,000자+ → 2,769자` 급축소를 failure signal로 해석 | TF-IPG 원문 프롬프트는 `절대 축소 금지`로 더 강했지만, 현재 worktree prompt는 `요약성 대폭 축소 금지`로 정렬됨 | 최종 기준은 `any deletion 금지`가 아니라 `요약성 대폭 축소 금지`다 |
| 다음 운영 단계 | control 유지, treatment 비채택, 필요 시 partial postmortem | control 유지, all-lite 단독 운영 중단, hybrid 가능성 언급 | preserve guard / prompt hardening 우선 | 최종은 `P0 correctness -> P1 observability -> P2 optional hybrid` 순서 |

가장 큰 조정 포인트는 이것이다.

`TF-IPG는 맞는 수정이지만, 00_test_03 실패를 그 한 가지로 설명하면 과장이다.`

그 이유:

- `ep_0002 ending -> blueprint_0003 scene_1` 사이 continuity seam이 실제로 있다.
- treatment는 `ep1`, `ep2`, `ep3` 전반에서 chronic length shortfall을 반복했다.
- `ep_0003` later rounds는 preserve guard 하나만으로 설명되지 않는 `scene-order`, `ending continuity`, `keyword`, `본가 재시작` 후퇴를 보였다.
- 실제 코드 guard도 `분량 감소 전부 금지`가 아니라 `원본 대비 70% 미만 축소 차단`이다. 즉, 일부 문장 삭제 같은 국소 수정은 허용 범주다.

이 점에서 OPUS를 이렇게 나누어 보는 편이 정확하다.

- 맞는 부분: `5,000자+ → 2,769자` 같은 급격한 축소를 실패 신호로 본 것
- 과한 부분: TF-IPG 원문 문서/초기 프롬프트가 이를 `절대 축소 금지` 또는 `근본 원인`으로 너무 넓게 표현한 것
- 현재 상태: worktree의 `chief_writer.yaml` PATCH_MODE_PROMPT는 `요약성 대폭 축소 금지`로 조정되어 코드 semantics와 맞춰졌다

따라서 최종 causal stack은 아래처럼 정리하는 편이 가장 안전하다.

1. primary: `flash-lite`의 Stage 4 복합 제약 비수렴
2. secondary: `blueprint_0003` continuity seam
3. tertiary: InPlace preserve guard 부재로 인한 retry 예산 낭비

## 3. OPUS 코드 수정 상태

### 3.1 TF-IPG 수정 반영 여부

아래 항목은 **코드 반영 확인**이 끝났다.

| 항목 | 상태 | 근거 |
|---|---|---|
| extracted manuscript `<2000` 차단 | 반영됨 | `modules/domain/agents/chief_writer.py` |
| `[원고_끝]` marker 검증/제거 | 반영됨 | `modules/domain/agents/chief_writer.py`, `config/prompts/chief_writer.yaml` |
| `original_char_count`, `min_char_target` 주입 | 반영됨 | `modules/domain/agents/chief_writer.py`, `config/prompts/chief_writer.yaml` |
| PASS_WITH_FIX preserve guard | 반영됨 | `modules/core/stage4_interview_round.py` |
| REJECT retry preserve guard | 반영됨 | `modules/core/stage4_interview_round.py` |
| `inplace_min_preserve_ratio: 0.70` | 반영됨 | `config/settings/validation.yaml` |
| patch diff + char delta logging | 반영됨 | `modules/core/constants.py`, `modules/core/stage2_preflight.py`, `modules/core/stage4_orchestrator.py` |

판정:

- TF-IPG 본문이 주장한 GAP-1~6은 현재 코드 기준으로 대부분 닫혔다.
- 관련 테스트 묶음도 현재 통과한다.
- 따라서 TF-IPG 자체를 사고로 보기는 어렵다.

### 3.2 TF-IPG와 섞여 들어온 추가 변경

현재 worktree에는 TF-IPG 외에도 아래 성격의 변경이 섞여 있다.

- `reject_bucket`, `selection_reason`, `verdict_reason` 보존
- `strategy_budget="reduced"` 기반 retry fanout 축소
- per-round cost/tokens/calls 기록 강화
- `episode_production.jsonl`의 `selection_reason` / `verdict_reason` 분리 보존
- `continuity_pin_guard`
- `quality_sidecar_bootstrap` / bridge health inspection

이들은 TF-IPG 문서의 직접 범위를 넘는다. 즉, TF-IPG는 이미 `guard + prompt` hardening 문서인데, 실제 코드 배치는 그보다 넓다.

최종 판정:

- `observability 확장`은 대체로 유효하다.
- `behavior-changing retry policy`는 유효 가능성이 높지만, TF-IPG와 한 배치로 묶어 승인할 성격은 아니다.

## 4. 문서 밖 추가 발견

이번 감리에서 가장 중요한 추가 발견은 아래다.

### 4.1 `stage4_complete` summary semantics regression 발견 및 조치

감리 시점에 `modules/core/stage4_orchestrator.py`는 아래 순서로 동작했다.

1. `_run_interview_loop(session)` 실행
2. 반환값과 무관하게 `_write_audit_summary("stage4_complete")`
3. 그 뒤에 `_should_return`이면 return

이 구조 때문에 `_run_interview_loop()`가 실패/중단/인간 검토 필요를 의미하는 `True`를 반환해도 `stage4_complete`가 기록될 수 있었다.

직접 재현 결과:

- `_run_interview_loop = MagicMock(return_value=True)`로 강제
- `stage_4_v2_chief_writer()` 실행
- `_write_audit_summary("stage4_complete")` 호출 확인

현재 조치:

- `_run_interview_loop()`가 `True`면 즉시 return
- 정상 완주(`False`)일 때만 `_write_audit_summary("stage4_complete")` 호출
- `tests/test_stage4_orchestrator.py`에 아래 회귀 테스트 추가
- early return 시 summary 미기록
- failed exhaustion / human review 필요 경로 시 summary 미기록
- `KeyboardInterrupt` 시 summary 미기록

판정:

- 이 이슈는 TF-IPG보다 심각한 **correctness regression**이었고, 현재 worktree 기준으로는 조치가 들어갔다.
- 이유는 `runtime_audit_summary.tag`가 두 cross-check 문서 모두에서 핵심 source of truth로 쓰이기 때문이다.
- 남은 리스크는 live rerun 미실행이지, source-level semantics는 현재 테스트로 잠겼다.

### 4.2 테스트 공백

현재 테스트 공백은 source-level P0 기준으로 사실상 닫혔다.

- failed exhaustion 시 summary 미기록은 추가 완료
- PASS_WITH_FIX 경로의 preserve ratio 70% 하한 직접 검증은 추가 완료
- REJECT retry 경로의 preserve ratio 70% 하한 직접 검증은 추가 완료
- `[원고_끝]` marker 제거 / marker 없음 warn-only / extracted manuscript `<2000` 경로는 추가 완료

판정:

- 현재 남은 P0 공백은 live rerun 미실행 쪽이지, source-level regression test 공백은 아니다.
- TF-IPG 핵심 guard는 source-level 구현뿐 아니라 regression test로도 잠겼다.

## 5. 시스템 개선 권고

이번 최종 문서의 목적은 `누가 맞았나`가 아니라 `무엇을 고쳐야 하나`를 닫는 것이다. 우선순위는 아래로 고정한다.

### P0. Correctness

1. `stage4_complete`는 진짜 성공 완주에서만 기록
   상태: 현재 worktree에서 조치 완료, 회귀 테스트 추가
2. TF-IPG는 유지
3. TF-IPG의 causal wording은 문서에서 낮춤
4. `runtime_audit_summary`를 source-of-truth로 쓰는 문서들은 `tag 의미 우선`으로 통일

### P1. Observability

1. `episode_production.jsonl`의 per-round metrics 유지
   상태: round cost/tokens/calls + `selection_reason` / `verdict_reason` 분리 기록까지 현재 worktree에서 반영
2. `strategy_budget`, `strategy_count`, `reject_bucket` 유지
   상태: 현재 worktree와 회귀 테스트에서 반영
3. interrupted session에서 `episode_production`, `pass_rate_monitor`, `runtime_audit_summary`의 의미를 맞춤
   상태: 아직 live rerun 전 단계. source-level 기준으로는 non-success summary semantics를 닫았고, reasoning split도 보존했으며, `episode_production` write 실패가 나도 DB/PassRate 기록은 유지되는 비차단 경로를 회귀 테스트로 확인
4. 실패/REJECT/PASS_WITH_FIX 원문 snapshot 보존을 후속 backlog로 승격

### P2. Behavior change

1. firewall REJECT의 patch routing
2. reduced fanout retry
3. continuity pin guard
4. hybrid profile 실험

P2는 바로 상시 ON이 아니라 flag 뒤에서 검증하는 편이 맞다. 이유는 이 묶음이 runtime 개선과 correctness 개선이 아니라 **행동 자체를 바꾸는 배치**이기 때문이다.

## 6. 기타 사항

| 항목 | 내용 | 최종 메모 |
|---|---|---|
| merge 단위 | 현재 worktree는 TF-IPG, P0, P1, sidecar, continuity 변경이 한 덩어리다 | 그대로 합치면 회귀 원인 분리가 어려움 |
| hybrid 실험 | OPUS는 가능성을 열어뒀지만 현재는 시기상조 | `P0/P1 green` 이후 shadow 실험으로만 검토 |
| 문서 신뢰도 | OPUS cross-check는 failure chain 정리에는 강하지만 artifact matrix에서 파일 존재와 의미를 섞는 부분이 있다 | 최종 문서는 `의미 기준`을 채택 |
| current verdict | `00_test_03` 비채택은 변하지 않는다 | 이번 문서는 채택성 재평가 문서가 아니라 시스템 개선 문서 |

## 7. 95% 확신도 근거

이번 최종 문서가 `95%`를 허용하는 이유는 아래다.

1. 세 문서가 core verdict와 core failure chain에서 합의한다.
2. TF-IPG 핵심 수정은 실제 코드에 존재한다.
3. 관련 테스트 묶음이 현재 통과한다.
4. 문서 밖 correctness regression 하나를 source-level로 직접 재현해 닫았다.
5. 남은 불확실성은 `live rerun 미실행`과 `P2 behavior change의 실전 상호작용` 쪽이지, 현재 문서의 최종 방향을 뒤집는 성질이 아니다.

남은 5%:

- live rerun으로 `summary/tag semantics`를 다시 실측하지 않았다.
- behavior-changing 변경을 feature-flag 분리하지 않은 현재 worktree는 merge risk가 남아 있다.
- `00_test_03` partial manual reading을 아직 추가하지 않았다.

## Close-Out

- 합의점: 충분하다.
- 불일치: 조정 가능 수준이며, 핵심은 causal weight 차이다.
- OPUS 코드 수정 상태: TF-IPG는 반영 확인, 정당한 hardening으로 채택 가능.
- 시스템 개선 핵심: `TF-IPG 유지 + stage4_complete semantics fix 완료 + P2 변경 분리 검증`.
- 최종 운영 판단: `control 유지`, `all-lite 단독 운영 중단`, `system hardening 우선`.
