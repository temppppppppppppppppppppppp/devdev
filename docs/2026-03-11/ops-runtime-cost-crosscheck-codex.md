# 00_test_00 Runtime/Cost Cross-Check

> 작성일: 2026-03-11
> 작성자: Codex
> 성격: `runtime/cost cross-check layer`
> 기준 오더: `docs/2026-03-11/ops-runtime-cost-crosscheck-order.md`
> 범위: `00_test_00` 한 런

## 최종 실행 판정

`2 arc / 2시간급` 체감은 과장이 아니라 방향상 맞다.

- `Arc 1 = acceptance baseline`으로 잘린 구간만 봐도 추정 총 소요는 약 `43.2분`이다.
- `Arc 2+ = overrun evidence` 구간은 `ep_0005~ep_0007 round 2`까지만 관측됐는데도 추정 총 소요가 이미 약 `63.4분`이다.
- 즉 `Arc 1 acceptance + Arc 2 partial overrun`만 합쳐도 약 `106.6분`이 관측된다.
- 여기에 `ep_0007` 후속 정산, `ep_0008` Stage 4, 세션 종료 정산이 빠져 있으므로 `2 arc 완주`는 실제로 `100분 초과`, 보수적으로도 `2시간급`으로 보는 판단이 타당하다.

cutoff는 오더 문서대로 고정한다.

- acceptance 종료 마커: `✅ 요청한 1개 Arc 전부 완료!`
- overrun 시작 마커: `🔄 [OneStop] Arc 2/60 처리 시작`

## Pass 1. 사실 추출

### 기준 입력

- `ops_hardening_rerun_00_test_00.log`
- `projects/00_test_00/project_data.db`
- `projects/00_test_00/logs/metrics/metrics_20260311_112834.json`
- `projects/00_test_00/logs/pass_rate_monitor.json`
- `projects/00_test_00/logs/quality_metrics.jsonl`
- `docs/2026-03-11/00-test-00-stage234-ssot-3pass.md`
- `docs/2026-03-11/00-test-00-manual-reading-audit.md`

### A. Episode x Round Breakdown

주의:

- 이 표는 round-grain 저장소가 충분한 `Stage 4` 중심으로 작성했다.
- `tokens`, `cost_usd`는 round별 직접 저장이 없으면 `n/a`로 두고, 화 단위 완결 비용이 있는 경우에만 적었다.
- `Arc 1 acceptance`와 `Arc 2+ overrun evidence`는 같은 표에 두되 해석은 절대 섞지 않는다.

| arc_no | ep_num | round_num | phase | generation_mode | patch_mode | candidate_count | verdict | score | duration_sec | tokens | cost_usd | source |
|---|---:|---:|---|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | 1 | 1 | stage4 | ensemble | no | 3 | PASS | 96 | 315.1 | 218161 | 0.4398 | `episode_production.jsonl`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 1 | 2 | 1 | stage4 | ensemble | no | 3 | PASS | 98 | 379.6 | 162518 | 0.2903 | `stage_attempts`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 1 | 3 | 1 | stage4 | ensemble | no | 3 | REJECT | 44 | 397.5 | n/a | n/a | `stage_attempts`, `director_selections` |
| 1 | 3 | 2 | stage4 | ensemble | no | 3 | PASS | 98 | 312.9 | n/a | n/a | `episode_production.jsonl`, `director_selections`, `stage_attempts` |
| 1 | 4 | 1 | stage4 | ensemble | no | 3 | PASS | 98 | 450.8 | 198497 | 0.3418 | `stage_attempts`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 2 | 5 | 1 | stage4 | ensemble | no | 3 | REJECT | 90 | 515.5 | n/a | n/a | `stage_attempts`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 2 | 5 | 2 | stage4 | patch | yes | 1 | PASS | 90 | 210.4 | 495092 | 0.8190 | `stage_attempts`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 2 | 6 | 1 | stage4 | ensemble | no | 3 | REJECT | 44 | 567.9 | n/a | n/a | `stage_attempts`, `director_selections` |
| 2 | 6 | 2 | stage4 | ensemble | no | 3 | REJECT | 44 | 447.3 | n/a | n/a | `stage_attempts`, `director_selections` |
| 2 | 6 | 3 | stage4 | ensemble | no | 3 | PASS | 100 | 442.0 | 333294 | 0.7093 | `stage_attempts`, `director_selections`, `ops_hardening_rerun_00_test_00.log` |
| 2 | 7 | 1 | stage4 | ensemble | no | 3 | REJECT | 44 | 652.5 | n/a | n/a | `stage_attempts`, `director_selections` |
| 2 | 7 | 2 | stage4 | patch | yes | 1 | PASS_WITH_FIX | 90 | 183.5 | n/a | n/a | `episode_production.jsonl`, `director_selections` |

### B. Stage Summary

주의:

- `stage2`, `stage3`는 DB에 round-level duration이 직접 남지 않아 `estimated`로 적는다.
- `estimated`는 로그의 visible max API span과 직후 Director/StateExtractor span만 합산한 보수적 추정이다.
- `stage4`는 `stage_attempts`와 `episode_production.jsonl`의 실측 duration을 우선 사용한다.

| stage | scope | attempts | pass_count | reject_count | total_duration_sec | total_tokens | total_cost_usd | notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| stage2 | Arc 1 acceptance | 1 | 1 | 0 | estimated 413.1 | n/a | n/a | Arc 1 tactical design, Director patch cycle 2회 포함 |
| stage3 | Arc 1 acceptance | 4 | 4 | 0 | estimated 320.6 | n/a | n/a | ep1~4 blueprint, retry 없음 |
| stage4 | Arc 1 acceptance | 5 | 4 | 1 | 1856.0 | 887999 | 1.6420 | ep3에서 1회 retry, stage4 비중 약 71.7% |
| stage2 | Arc 2+ overrun evidence | 1 | 1 | 0 | estimated 439.5 | n/a | n/a | Arc 2 tactical design, Director patch cycle 1회 포함 |
| stage3 | Arc 2+ overrun evidence | 4 | 4 | 0 | estimated 345.9 | n/a | n/a | ep5~8 blueprint, retry 없음 |
| stage4 | Arc 2+ overrun evidence | 7 | 3 | 4 | 3019.2 | >=828386 | >=1.5283 | ep5~7 partial only, ep7 round2는 `episode_production.jsonl` 보강, stage4 비중 약 79.4% |

### 관측 요약

- `Arc 1 acceptance` 추정 총 소요: `2589.7초` (`43.2분`)
- `Arc 2+ overrun evidence` 추정 총 소요: `3804.6초` (`63.4분`)
- 관측된 두 구간 합계: `6394.2초` (`106.6분`)
- `Stage 4`가 관측 총시간의 약 `76.2%`를 차지한다.
- `quality_metrics.jsonl` 기준 acceptance 구간은 `retrieval_observation=36`, `validation=29`다.
- 같은 파일 기준 overrun 구간은 `retrieval_observation=15`, `validation=10`이다.

## Pass 2. 원인 분해

### C. Root-Cause Taxonomy

| id | taxonomy | evidence | current interpretation | time/cost impact | next fix point | confidence |
|---|---|---|---|---|---|---|
| RC-1 | confirmed bottleneck | `stage4` single-round도 `315~568초`가 기본값이다. `ep1=315.1s`, `ep4=450.8s`, `ep6 round1=567.9s`. | `CW 3-ensemble + self-critique + Director + advisory` 조합 자체가 round 1회당 5~9분의 고정 비용을 만든다. | high | Stage 4 default fanout 축소 조건, self-critique depth 완화, advisory 병목 절감 | high |
| RC-2 | confirmed bottleneck | `ep5 round1`은 Director 판정이 `PASS 90`인데 실제 round outcome은 `REJECT`이고 `round2 patch`로 다시 갔다. | Director 선택 이후 post-select continuity gate가 full-round 완료 뒤에 발동해, 이미 비싼 round를 통째로 폐기한다. | high | post-select reject를 pre-Director 또는 pre-write 쪽으로 승격, 실패 시 즉시 single-candidate patch로 라우팅 | high |
| RC-3 | confirmed bottleneck | `ep6`은 `44 -> 44 -> 100`, `ep7`은 `44 -> 90`으로 firewall/continuity 계열 reject가 반복됐다. | contradiction firewall과 continuity reject는 값비싼 full ensemble 이후에 발생하고, 같은 failure bucket이 2~3회 반복돼 비용을 증폭한다. | high | failure bucket별 fast-path patch, continuity conflict 전용 retry budget, earlier exact-state gate | high |
| RC-4 | supporting contributor | `stage2+stage3`만으로도 Arc 1은 추정 `733.7초`, Arc 2는 추정 `785.4초`다. | Arc 추가 시 Stage 4 이전에 이미 12~13분 수준의 고정 오버헤드가 한 번 더 붙는다. Stage 4만 줄여도 2-arc 체감은 완전히 사라지지 않는다. | medium | Arc당 fixed overhead를 별도 예산으로 계측하고, Stage 3 parallelism/selection 경량화 검토 | medium |
| RC-5 | false positive / noise | `scene coverage 0%`, `ending hook miss`, `InfoParadox`, `dialogue ratio` 경고가 로그상 반복되지만, Director 자유 리뷰에서 여러 차례 오탐으로 기각됐다. | warning noise가 round 수를 직접 만든 유일 원인은 아니지만, 판정 피로와 analysis cost를 키운다. | medium | advisory-only 규칙 고정, warning UI 분리, blocking 승격 조건 축소 | high |
| RC-6 | supporting contributor | `episode_production.jsonl`는 `ep7 round2 PASS_WITH_FIX`까지 남았지만 `stage_attempts`는 `ep7`을 완결 row로 닫지 못했다. | interrupted session에서는 round 기록 저장소 간 시차가 생겨 runtime/cost 분석 자체가 번거로워진다. | low | per-round persistence order 정렬, interrupted flag 도입 | medium |
| RC-7 | hypothesis pending | current run에서는 PromptLoader 경고가 보이지 않는다. 대신 per-round ChiefWriter 호출 수와 길이 변동이 여전히 크다. | 템플릿 오류는 현 런의 주 원인이 아니고, 남은 지연은 JSON 응답 경로/critique budget/strategy fanout 쪽일 가능성이 크다. | medium | per-call token/cost를 round별로 DB 저장한 뒤 JSON mode 영향 재측정 | medium |

## Pass 3. 개선 우선순위

### D. Improvement Priority

| priority | class | target | expected effect | implementation cost | confidence |
|---|---|---|---|---|---|
| P0 | quick win | post-select continuity reject를 full rerun 대신 single-candidate patch로 직행 | `ep5`류에서 full round 1회 절감. 화당 대략 `300~500초`, `0.2~0.5 USD+` 절약 가능 | medium | high |
| P0 | quick win | contradiction/continuity exact-state gate를 Director 이후가 아니라 더 앞단으로 이동 | `ep6`, `ep7`류 firewall retry를 1회 이상 줄일 가능성이 높다 | medium | high |
| P1 | structural change | Stage 4 default 3-candidate fanout을 상황부 fanout으로 낮추기 | single-round floor 자체를 낮춰 전체 체감 시간을 지속적으로 줄인다 | medium-high | medium |
| P1 | structural change | self-critique/advisory depth를 failure bucket 기반으로 차등화 | 이미 좁혀진 수정 범위에서 불필요한 다중 검사를 줄인다 | medium | medium |
| P2 | needs instrumentation | per-round token/cost를 DB에 저장하고 post-select reject class를 분리 | 다음 감리에서 `시간/비용 증가의 실제 원인`을 더 싸게 고정할 수 있다 | low | high |

## 비교 준비 요약

- 시간은 `Stage 4`에서 가장 많이 소모된다. 관측 구간 기준 약 `74.6%`다.
- 비용도 `Stage 4`가 사실상 본체다. acceptance Arc 1 stage4만 `887,999 tokens / $1.6420`이고, overrun `ep5~6` stage4만으로도 `828,386 tokens / $1.5283`다.
- retry는 `단순 길이 부족`보다 `post-select continuity reject`와 `firewall/continuity bucket 반복`에서 더 크게 증폭됐다.
- warning noise는 분명히 존재하지만, current run 기준 핵심 병목은 아니라는 점이 중요하다.
- 다음 배치에서 가장 싸게 줄일 수 있는 것은 `Director 이후 full rerun`을 `earlier gate + single-candidate patch`로 바꾸는 경로다.

## Appendix A. Agent-specific observations

- historical clean session(`metrics_20260311_112834.json`)의 `1 arc / 63분 59초 / $1.9671`는 여전히 상한선 근거로 유효하다. 다만 current rerun에서는 `Arc 1 acceptance`가 이보다 짧아졌고, 병목의 중심이 `ep1`에서 `Arc 2 continuity/post-select gate` 쪽으로 이동했다.
- current rerun 기준 `2 arc / 2시간급` 체감은 `Arc 1이 너무 느려서`가 아니라 `Arc 2가 Stage 4 retry로 급격히 불어나는 구조` 쪽 설명력이 더 높다.
- `PromptLoader` 경고는 current rerun 로그에서 재현되지 않았다. 이 항목은 현재 causal set의 앞줄에서 내려도 된다.

## Appendix B. 반례 / 이견 / 추가 가설

- `warning noise`를 과대평가하면 current run의 주 병목을 잘못 읽게 된다. 이번 관측에서는 오탐이 많았지만, 실제 시간 팽창은 `ep5~7`의 real continuity reject가 더 크게 만들었다.
- `Stage 4`가 전체 시간을 대부분 먹는다는 판단은 강하다. 다만 현재는 `per-round token/cost`가 DB에 직접 남지 않아, strategy별 비용 차이는 아직 `hypothesis pending`으로 남겨야 한다.
- `runtime_audit_summary`가 `stage3_complete`에서 멈춰 있는 상태는 current rerun이 Stage 4를 끝까지 닫지 못했기 때문에 runtime bottleneck 근거로는 쓰지 않았다. 이 항목은 observability layer에서 따로 다루는 편이 정확하다.
