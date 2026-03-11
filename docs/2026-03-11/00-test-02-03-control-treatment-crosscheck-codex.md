# 00_test_02 / 00_test_03 Control-Treatment Cross-Check - Codex

> 작성일: 2026-03-11
> 작성자: Codex
> 오더 문서: `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-order.md`
> 성격: `control-vs-treatment decision layer`
> 비고: 기존 SSOT / reproduction 문서를 대체하지 않음

## 최종 한줄 판정

- `00_test_02`: **재현함**. `runtime_audit_summary.tag=stage4_complete`, draft `4/4`, `stage_attempts=10`, `director_selections=6`, `total_tokens=880,936`, `total_cost_usd=1.6364`.
- `00_test_03`: **채택 불가**. `runtime_audit_summary.tag=stage3_complete`, draft `2/4`, `ep_0003` 5회 REJECT 후 종료, `ep_0004` 미도달. 현재 근거만으로 비채택 판정은 `95%`를 넘긴다.

## Pass 1. 실행 사실 고정

### 표 A. Run Snapshot

| project | profile | scope | stage2 | stage3 | stage4 | runtime_audit_tag | blueprint_count | draft_count | stage_attempts | director_selections | total_tokens | total_cost_usd | source |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `00_test_02` | `control-2.5-pro` | `Arc 1 / ep_0001~ep_0004` | `1 PASS_WITH_FIX` | `4 PASS` | `4 PASS + 1 REJECT` | `stage4_complete` | 4 | 4 | 10 | 6 | 880,936 | 1.6364 | `project_data.db`, `metrics_20260311_200432.json`, `runtime_audit_summary.json`, `pass_rate_monitor.json` |
| `00_test_03` | `treatment-3.1-flash-lite` | `Arc 1 / ep_0001~ep_0004` | `1 PASS` | `4 PASS` | `2 PASS + 7 REJECT` | `stage3_complete` | 4 | 2 | 14 | 10 | 1,169,027 | 0.8872 | `project_data.db`, `metrics_20260311_201738.json`, `runtime_audit_summary.json`, `pass_rate_monitor.json` |

고정 사실:

- `00_test_02`는 `2026-03-11 20:55:28` 기준 `Stage 4 원고 완료 (4화 생산)`과 `요청한 1개 Arc 전부 완료!`가 함께 확인된다.
- `00_test_03`는 `2026-03-11 21:24:39`에 `KeyboardInterrupt()` 이후 `사용자 중단 요청. 저장 후 종료합니다.`가 기록되고, 최종 `runtime_audit_summary.tag`는 끝까지 `stage3_complete`에 머문다.
- `00_test_03` 세션 로그에는 `원고 완료 (2화 생산)`과 `요청한 1개 Arc 전부 완료!`가 찍히지만, 이번 감리에서는 `draft_count`, `runtime_audit_tag`, `stage_attempts`를 우선 소스로 본다.

### 표 B. Artifact / Completion Matrix

| project | artifact | expected | observed | parity | notes | source |
|---|---|---|---|---|---|---|
| `00_test_02` | `arc_001` | 1 | 1 | `match` | Arc 1 범위 고정 | `plans/arcs/arc_001.txt` |
| `00_test_02` | `blueprint_0001~0004` | 4 | 4 | `match` | Stage 3 `4 PASS`, 점수 `100/100/100/100` | `plans/blueprints/`, `quality_metrics.jsonl` |
| `00_test_02` | `ep_0001~0004` | 4 | 4 | `match` | draft `4/4` 존재, `ep_0003`만 1회 REJECT 후 수렴 | `drafts/`, `pass_rate_monitor.json`, `quality_metrics.jsonl` |
| `00_test_02` | `runtime_audit_summary` | `stage4_complete` | `stage4_complete` | `match` | 총 11 events | `runtime_audit_summary.json` |
| `00_test_02` | `quality_metrics` | Stage 2/3/4 validation trail | 24 lines | `match` | validation summary = `stage2 PASS 1`, `stage3 PASS 4`, `stage4 PASS 4`, `stage4 REJECT 1` | `quality_metrics.jsonl` |
| `00_test_02` | `episode_production` | Arc 1 round trace | 5 lines | `near-match` | ep1~4 라운드와 ep3 retry는 보이지만, 최종 완료 판정은 `stage_attempts`와 함께 읽어야 함 | `episode_production.jsonl`, `project_data.db` |
| `00_test_03` | `arc_001` | 1 | 1 | `match` | Arc 문서는 존재하나, 3화 beat가 법인 설립과 PB 거래를 한 화 안에 묶음 | `plans/arcs/arc_001.txt` |
| `00_test_03` | `blueprint_0001~0004` | 4 | 4 | `match` | Stage 3 `4 PASS`, 점수 `90/95/92/90` | `plans/blueprints/`, `quality_metrics.jsonl` |
| `00_test_03` | `ep_0001~0004` | 4 | 2 | `mismatch` | `ep_0001`, `ep_0002`만 존재. `ep_0003`, `ep_0004` 부재 | `drafts/` |
| `00_test_03` | `runtime_audit_summary` | `stage4_complete` | `stage3_complete` | `mismatch` | 최종 tag가 Stage 4에 도달하지 못함 | `runtime_audit_summary.json` |
| `00_test_03` | `quality_metrics` | Stage 2/3/4 validation trail | 32 lines | `near-match` | validation summary = `stage2 PASS 1`, `stage3 PASS 4`, `stage4 PASS 2`, `stage4 REJECT 7` | `quality_metrics.jsonl` |
| `00_test_03` | `episode_production` | Arc 1 round trace | 10 lines | `near-match` | ep1~3 라운드 흔적은 남았지만 ep4 round trace는 없음 | `episode_production.jsonl` |

## Pass 2. 차이 분해

### 표 C. Decision Taxonomy

| id | project | taxonomy | evidence | current interpretation | impact on operating-profile decision | next check point | confidence |
|---|---|---|---|---|---|---|---|
| C1 | `00_test_02` | `confirmed control parity` | `runtime_audit_summary.tag=stage4_complete`, draft `4/4`, `stage4 PASS 4 + REJECT 1`, `episode_quality_labels=4`, `episode_quality_signals=4` | Arc 1 완주와 핵심 산출물 계층이 control 기준으로 닫혔다 | `none` | 없음 | `97%` |
| C2 | `00_test_02` | `confirmed control parity` | `00_test_01` 기준 문서의 `stage_attempts=11`, `director_selections=7`, `tokens=907,316`, `cost=$1.6636` 대비 현재 run은 `10`, `6`, `880,936`, `$1.6364` | accepted control profile의 재측정 run으로 읽기에 충분하며, cost/runtime 관측도 더 나빠지지 않았다 | `none` | 없음 | `95%` |
| C3 | `00_test_02` | `acceptable drift` | Stage 2 `PASS_WITH_FIX` 1회, Stage 4 `ep_0003` 1회 REJECT 후 round 2 PASS 90 | 단일 correction과 단일 retry는 control 안정성을 뒤집는 신호가 아니라 운영 가능한 drift에 가깝다 | `low` | 다음 rerun에서도 같은 폭으로 유지되는지 확인 | `93%` |
| T1 | `00_test_03` | `failure signal` | draft `2/4`, `runtime_audit_summary.tag=stage3_complete`, `episode_quality_labels=2`, `ep_0004` 미도달 | fail-closed 규칙만으로도 비채택이 닫힌다. 이번 스냅샷은 live run이 아니라 종료된 실패 스냅샷이다 | `high` | 없음 | `99%` |
| T2 | `00_test_03` | `failure signal` | Stage 4 validation = `PASS 2`, `REJECT 7`; `ep_0003` stage4 attempts = `5`, 점수 `86 -> 90 -> 50 -> 50 -> 43` | retry가 누적될수록 수렴보다 붕괴 쪽으로 기울었다. Stage 4 writer/profile 조합의 안정성이 부족하다 | `high` | 없음 | `98%` |
| T3 | `00_test_03` | `failure signal` | 총량은 `68.26분 / 190 calls / 1,169,027 tokens / $0.8872`, 산출은 draft 2편뿐. draft 기준으로는 `95.0 calls`, `584,513.5 tokens`, `$0.4436` per draft로 control의 `33.8`, `220,234`, `$0.4091`보다 모두 열세 | 절대 비용만 낮고, 완주 기준 효율은 닫히지 않는다. 시간과 토큰은 control 대비 명확히 악화됐다 | `high` | 없음 | `96%` |
| T4 | `00_test_03` | `acceptable drift` | Stage 2 `PASS 1`, Stage 3 `PASS 4`, blueprint `4/4` 생성 | 실패가 파이프라인 전구간이 아니라 Stage 4에 집중된다는 점은 분리 가능하다 | `medium` | 없음 | `92%` |
| T5 | `00_test_03` | `hypothesis pending` | `ep_0002` draft 종료는 `여의도 한미증권 로비`, `blueprint_0003` scene_1은 `법무사 사무소`, scene_2는 `한미증권 VIP 상담실` | 3화 설계 자체에 continuity seam이 있어 blueprint/arc 기여분이 0이라고는 못 한다 | `medium` | `ep_0002` 종료 상태와 `blueprint_0003` line-by-line seam audit | `76%` |
| T6 | `00_test_03` | `failure signal` | continuity feedback와 scene-order feedback 뒤에도 later attempts가 `2769자`, `3211자`, `다시 본가 시작`, `운명 미반영`으로 후퇴 | blueprint seam이 있더라도, explicit feedback 이후 길이/연속성/키워드 제약을 동시에 못 지킨 쪽이 더 강한 실패 신호다 | `high` | 없음 | `95%` |
| T7 | `00_test_03` | `hypothesis pending` | `ep_0001`, `ep_0002`는 PASS 90/92로 남아 있으나 이번 감리에서 manual reading을 하지 않았다 | 완료된 2편의 prose 판독은 partial postmortem 정밀도를 높일 수 있지만, 비채택 판정을 다시 열지는 않는다 | `low` | 필요 시 `ep_0001`, `ep_0002` partial manual reading | `84%` |

정리:

- `00_test_02`는 현재 accepted control profile의 재현 및 재측정 run으로 읽기에 충분하다.
- `00_test_03`의 비채택은 `artifact completeness`, `runtime_audit_tag`, `stage4 reject cluster`만으로 닫힌다.
- `00_test_03`의 실패 원인은 Stage 4 writer/profile 불안정 쪽이 더 강하지만, `blueprint_0003`의 continuity seam 때문에 `blueprint-quality ambiguity`가 완전히 0이라고 말하진 않는다.
- 다만 그 ambiguity는 `채택 불가`를 뒤집는 수준이 아니라, partial postmortem 정밀도에만 영향을 준다.

## Pass 3. 운영 권고 판정

### 표 D. Decision Ladder

| claim | 00_test_02 | 00_test_03 | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|---|
| `control profile reproducibility` | `stage4_complete`, draft `4/4`, `00_test_01 -> 00_test_02`로 retry/cost 소폭 개선 | `N/A` | 없음 | `95%` | `95%` |
| `control profile cost/runtime observability` | `51.06분`, `880,936 tokens`, `$1.6364`, `failed_calls=0` | `N/A` | 없음 | `95%` | `95%` |
| `treatment profile viability` | `N/A` | `stage3_complete`, draft `2/4`, `ep_0003` 5회 REJECT, `ep_0004` 미도달로 `채택 불가` | 없음 | `97%` | `97%` |
| `treatment profile quality trustworthiness` | `N/A` | 완료된 `ep_0001`, `ep_0002`만으로는 닫히지 않음. Stage 4 결과 해석에는 partial postmortem이 남아 있음 | `ep_0001`, `ep_0002` partial manual reading + `ep_0002 -> blueprint_0003` seam audit | `70%` | `85%` |
| `next operating recommendation` | 현행 `2.5-pro` control 유지 | `3.1-flash-lite` all-lite 단독 운영 비채택 | 없음. 남은 `hypothesis pending`은 postmortem 범위 | `95%` | `95%` |

현재 `95%`를 허용하는 이유:

- `00_test_02` 쪽 핵심 claim은 모두 `confirmed control parity` 또는 `acceptable drift` 범위에 머문다.
- `00_test_03` 쪽 비채택 판단은 `ep_0003`/`ep_0004` 미완료와 `stage3_complete` 종료만으로 이미 fail-closed가 가능하다.
- 남아 있는 `hypothesis pending`은 `왜 그렇게 실패했는가`를 더 잘 가르는 postmortem 층위이지, `채택 불가` 자체를 흔드는 층위가 아니다.

## 비교용 요약

1. `00_test_02`는 control run으로서 재현되었는가  
   재현되었다. `stage4_complete`, draft `4/4`, `stage_attempts=10`, `director_selections=6`, `$1.6364`로 `00_test_01` 대비 동등 이상이다.

2. `00_test_03`는 왜 `채택 불가`인가  
   종료 시점이 `stage3_complete`에 머물렀고, draft가 `2/4`뿐이며, `ep_0003`가 5회 REJECT 뒤 끝내 닫히지 않았기 때문이다.

3. 비용/시간 기준에서 treatment의 이득 또는 손해는 무엇인가  
   절대 비용은 낮지만 완주가 닫히지 않아 운영 판단 기준으로는 이득으로 볼 수 없다. 시간, calls, tokens, draft당 비용은 모두 control보다 불리하다.

4. quality 신뢰성은 어디서 흔들리는가  
   핵심은 `ep_0003`에서 length, continuity, scene-order, keyword 제약을 함께 못 지킨 점이다. 여기에 `blueprint_0003`의 continuity seam이 일부 ambiguity를 남긴다.

5. 다음 단계는 무엇인가  
   현재 운영은 `control 유지`, `all-lite 단독 운영 비채택`이 맞다. 후속으로 한다면 `00_test_03`는 채택 탐색이 아니라 `partial postmortem`으로만 다뤄야 한다.

## Appendix A. Agent-specific observations

- `episode_production.jsonl`은 round trace에는 유용하지만, 최종 완료 판정 소스로는 단독 사용이 어렵다. 예를 들어 `00_test_02 ep_0003 round 0`, `00_test_03 ep_0003 round 1`은 `episode_production`에서 각각 `PASS`, `PASS_WITH_FIX`로 보이지만, `stage_attempts`와 `pass_rate_monitor`에서는 최종적으로 REJECT 경로에 포함된다.
- 따라서 completion 판정의 source priority는 `drafts/` 실파일, `runtime_audit_summary.json`, `stage_attempts`, `pass_rate_monitor.json` 순서로 두는 편이 안전하다.
- `00_test_03` 세션 로그의 `사용자 중단 요청. 저장 후 종료합니다.`와 `원고 완료 (2화 생산)`은 종료 스냅샷을 설명하는 데는 유효하지만, Stage 4 completeness 증거로 쓰면 안 된다.

## Appendix B. 반론 / 한계 / 추가 가설

- `00_test_03`의 `ep_0002` 종료 상태와 `blueprint_0003` scene order 사이에는 분명한 seam이 있다. 그래서 `blueprint-quality ambiguity`를 완전히 제거하진 않는다.
- 다만 이후 round들에서 드러난 `분량 하락`, `본가 시작 회귀`, `키워드 미반영`, `explicit feedback 미수렴`은 seam 하나만으로 설명하기 어렵다. 현재로서는 `profile-induced instability` 쪽 설명력이 더 높다.
- `ep_0001`, `ep_0002` partial manual reading과 `arc_001 -> blueprint_0003 -> ep_0002 ending`의 line-by-line 대조를 추가하면 원인 분해 확신도는 더 올라갈 수 있다. 그래도 이번 감리의 `채택 불가` 판정은 그대로 유지된다.
