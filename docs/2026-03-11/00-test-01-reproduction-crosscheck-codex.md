# 00_test_01 Reproduction Cross-Check — Codex

> 작성일: 2026-03-11  
> 범위: `projects/00_test_01`의 `Arc 1 / ep_0001~ep_0004`  
> 기준선: `00_test_00` live tree가 아니라 [00-test-00-stage234-ssot-3pass.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-00-stage234-ssot-3pass.md), [00-test-00-manual-reading-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-00-manual-reading-audit.md), `session_20260311_112831.log`, `metrics_20260311_112834.json`  
> 성격: `technical validation baseline` 재현 감리. `real production baseline` 승격 판정 아님.

## 최종 한줄 판정
현재 판정: `00_test_01`은 `00_test_00`의 Arc 1 technical validation baseline을 `재현함`. 현재 확신도는 `95%`이며, 남은 5%는 `baseline live draft 직접 대조 불가`, `exact surface form 수준의 시간/자본금 표현 차이`, `실프로젝트 미검증`에 한정된다.

## Pass 1. 재현 사실 고정

### 표 A. Artifact Parity

| layer | baseline_00_test_00 | candidate_00_test_01 | parity | source |
|---|---|---|---|---|
| arc | `arc_001` 존재, Arc 1 완료 기록 | `arc_001.txt` 존재, 9,618 bytes | `match` | SSOT, `plans/arcs/arc_001.txt` |
| blueprint | `blueprint_0001~0004` 존재, 4화 설계 완료 | `blueprint_0001~0004` 존재, 4화 설계 완료 | `match` | SSOT, `plans/blueprints/*.txt` |
| draft | `ep_0001~0004` 존재, 4화 집필 완료 | `ep_0001~0004` 존재, 4화 집필 완료 | `match` | SSOT, `drafts/*.txt`, session log |
| db_rows | `episode_quality_labels=4`, `signals=4`, `observations=0` | `episode_quality_labels=4`, `signals=4`, `observations=0` | `match` | SSOT, `project_data.db` |
| db_rows | `director_selections=14`, `stage_attempts=18` | `director_selections=7`, `stage_attempts=11` | `near-match` | SSOT, `project_data.db`, `pass_rate_monitor.json` |
| metrics | `total_calls=169`, `tokens=1,027,179`, `cost=$1.9671` | `total_calls=139`, `tokens=907,316`, `cost=$1.6636` | `near-match` | pinned metrics, candidate metrics |
| runtime_audit | baseline run은 SSOT상 Stage 4 summary 반영 누락 | `runtime_audit_summary.tag=stage4_complete` | `near-match` | SSOT, `runtime_audit_summary.json` |

### 표 B. Run Summary

| project | scope | stage2 | stage3 | stage4 | artifacts_complete | major_counts | notes | source |
|---|---|---|---|---|---|---|---|---|
| `00_test_00` | Arc 1 / ep_0001~0004 | PASS | PASS | PASS | yes | `labels=4`, `signals=4`, `director_selections=14`, `stage_attempts=18` | baseline은 reset 이후 live tree가 아니라 SSOT/pinned log 기준으로 해석 | SSOT, pinned logs |
| `00_test_01` | Arc 1 / ep_0001~ep_0004 | PASS | PASS | PASS | yes | `labels=4`, `signals=4`, `director_selections=7`, `stage_attempts=11` | `17/17` 필수 입력 존재, `runtime_audit_summary.tag=stage4_complete` 확인 | candidate logs, DB |

고정 사실:

- `00_test_01` 필수 입력은 `17/17` 존재한다.
- `00_test_01` baseline 비교 입력은 `7/7` 존재한다.
- session log 기준 `제1화`~`제4화` 저장 완료, `Stage 4 집필 세션 종료`, `원고 완료 (4화 생산)`, `요청한 1개 Arc 전부 완료!`가 모두 확인된다.
- `00_test_01` Stage 4는 `ep3`만 다중 라운드였고, 최종적으로 `PASS`로 수렴했다.

## Pass 2. 차이 분해

### 표 C. Delta Taxonomy

| id | taxonomy | evidence | current interpretation | impact on reproduction claim | next check point | confidence |
|---|---|---|---|---|---|---|
| D1 | `confirmed reproduction` | `arc_001`, `blueprint_0001~0004`, `ep_0001~0004`가 모두 존재 | Arc 1 산출물 계층 자체는 baseline과 동일하게 재현됐다 | `none` | 없음 | high |
| D2 | `confirmed reproduction` | session log에 `Stage 2 PASS`, `Stage 3 완료`, `Stage 4 원고 완료 (4화 생산)`, `요청한 1개 Arc 전부 완료!` 존재 | `Stage 2 -> 3 -> 4` 파이프라인 완주가 baseline과 동일하게 재현됐다 | `none` | 없음 | high |
| D3 | `confirmed reproduction` | DB에서 `episode_quality_labels=4`, `episode_quality_signals=4`, `episode_quality_observations=0` | 품질 sidecar 핵심 row 패턴은 baseline과 동일하다 | `none` | 없음 | high |
| D4 | `acceptable drift` | baseline `director_selections=14`, `stage_attempts=18`; candidate `director_selections=7`, `stage_attempts=11`; candidate Stage 4 시도는 `6회` | retry profile은 크게 줄었지만, 이는 P0/P1 이후 hardening 효과로 읽는 편이 맞다. 산출물/완주 자체를 뒤집는 차이는 아니다 | `low` | 후속 실측 시 runtime/cost 개선 효과로 별도 판정 | high |
| D5 | `acceptable drift` | baseline run은 SSOT상 `runtime audit summary`가 Stage 4를 반영하지 못했다. candidate는 `stage4_complete` | observability는 candidate가 baseline보다 개선됐다. 이는 재현 실패가 아니라 개선된 계측 drift다 | `low` | 후속 comparative rerun에서 same-format metrics 비교 | high |
| D6 | `acceptable drift` | baseline manual audit는 `약 2주 후 -> 다음 날 오후 -> 일주일 후` residual drift를 기록. candidate `blueprint_0004`, `ep_0004`는 `다음 날 오후`를 유지 | ep4 시간축은 candidate도 여전히 soft drift 계열이다. 다만 baseline도 동일한 defect class를 갖고 있어, baseline fidelity를 뒤집는 `material divergence`로 보긴 어렵다 | `medium` | 실전 재측정 시 elapsed-time ledger 추가 점검 | medium |
| D7 | `acceptable drift` | 수동 판독 결과, `ep_0001`은 죽음→회귀→경제 데이터 기록→문 열림 훅, `ep_0002`는 한정호 호출→독립 선언→수정 문진 위협, `ep_0003`는 문진 포착→자산 정리→법인 의뢰→감시자 훅, `ep_0004`는 감시 회피 탈출→여의도 사무실→박성호 접촉→WTI 첫 베팅 방해를 유지한다. 텍스트 기준 `hard contradiction`는 없고, residual drift는 `arc_001`의 `사흘/20억 780만 원/2주 후`가 draft에서 `20억/다음 날 오후`로 압축되는 정도다 | prose-level 구조 재현은 manual reading으로 닫혔다. 남은 것은 baseline manual audit가 이미 기록한 결함 계열과 같은 soft drift뿐이며 `material divergence`로 승격할 수준은 아니다 | `low` | exact surface form parity가 꼭 필요하면 후속 appendix로만 관리 | high |

정리:

- `material divergence`는 현재 없다.
- `00_test_01`의 차이는 대부분 `더 적은 retry`, `더 나은 observability`, `동일 defect class의 residual soft drift`로 정리된다.
- 수동 판독 결과 `00_test_01` 4편 최종 원고에는 이번 범위에서 확인되는 `hard contradiction`가 없다.
- residual soft drift는 `ep4`의 elapsed-time 압축(`2주 후 -> 다음 날 오후`)과 자본금 exact form 압축(`20억 780만 원 -> 20억`) 정도이며, baseline manual audit가 이미 기록한 defect class 범위를 넘지 않는다.
- 문체와 제목 차이는 존재하지만, 오더 문서 기준으로 prose 동일성은 요구사항이 아니다.

## Pass 3. 확신도 판정

### 표 D. Confidence Ladder

| claim | current status | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|
| Arc 1 artifact reproduction | `confirmed reproduction` | 없음 | 95% | 95% |
| Stage 2->3->4 pipeline reproduction | `confirmed reproduction` | 없음 | 95% | 95% |
| operator-readable observability parity | `acceptable drift` | 없음. candidate가 baseline보다 개선된 계측을 가짐 | 95% | 95% |
| `00_test_00` 대비 baseline fidelity | `acceptable drift` | 없음. 수동 판독 완료로 prose-level blocker는 해소되었고, 남은 것은 exact surface form drift뿐 | 95% | 95% |

현재 95%를 허용한 이유:

- 핵심 claim이 모두 `confirmed reproduction` 또는 `acceptable drift`다.
- `material divergence`가 없다.
- `00_test_01` 4편에 대한 수동 판독에서 `hard contradiction`가 발견되지 않았다.
- prose-level 불확실성은 해소되었고, 남은 차이는 baseline manual audit가 이미 기록한 defect class와 같은 soft drift뿐이다.

남은 5% 불확실성:

1. `00_test_00` live draft를 reset 이전 상태로 직접 대조하지 못한다.
2. `ep4` elapsed-time / 자본금 표현은 baseline defect class와 같은 계열이지만 exact surface form까지 일치한다고는 말하지 않는다.
3. 이번 판정은 여전히 `technical validation baseline` 범위다. `real production`이나 `실제 프로젝트` 검증으로 확장되지 않는다.

## 비교용 요약

1. `00_test_01`은 `00_test_00`를 어디까지 재현했는가  
   Arc 1 산출물 계층, Stage 2->3->4 완주, 품질 row 패턴, 운영 로그 관측까지 재현했다.

2. 핵심 parity는 어디서 확인되는가  
   `arc_001`, `blueprint_0001~0004`, `ep_0001~0004`, session log의 4화 완료 기록, DB의 `labels/signals/observations`에서 확인된다.

3. 허용 가능한 drift는 무엇인가  
   retry 수 감소, `runtime_audit_summary.tag=stage4_complete`, ep4 residual time/capital drift, 제목/문체 차이.

4. reproduction verdict를 흔드는 `material divergence`가 있는가  
   현재 없다.

5. 현재 근거로 확신도 95%에 도달하는가  
   도달한다. 다만 이는 `technical validation baseline reproduction`에 한정된 95%다.

## Audit Notes

- baseline source-of-truth는 `00_test_00` live tree가 아니라 [00-test-00-stage234-ssot-3pass.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-00-stage234-ssot-3pass.md), [00-test-00-manual-reading-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-00-manual-reading-audit.md), pinned session/metrics log다.
- `projects/00_test_00/logs/runtime_audit_summary.json`의 현재 live 값은 reset 이후 오염 가능성이 있어 baseline 판정에 사용하지 않았다.
- `00_test_01` 수동 판독 기준:
  - `ep_0001.txt:14,84`는 회귀 시점과 문 열림 훅을 유지한다.
  - `ep_0002.txt:3,85-95`는 한정호 대면과 수정 문진 위협을 유지한다.
  - `ep_0003.txt:3,47,88,147,158`은 문진 포착, 자산 정리, 법인 의뢰, 감시자 훅을 유지한다.
  - `ep_0004.txt:33,47,68,70,76`은 여의도 사무실, 박성호 압박 질문, 20억 계좌, WTI 첫 베팅, 폭력적 방해 훅을 유지한다.
- 본 문서는 `reproduction verification + delta audit layer`이며, 기존 SSOT를 대체하지 않는다.
