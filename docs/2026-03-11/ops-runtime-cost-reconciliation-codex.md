# 00_test_00 Runtime/Cost Reconciliation

> 작성일: 2026-03-11
> 작성자: Codex
> 성격: `reconciliation layer`
> 원본 문서:
> - `docs/2026-03-11/ops-runtime-cost-crosscheck-codex.md`
> - `docs/2026-03-11/ops-runtime-cost-crosscheck-report-OPUS.md`
> 원칙: 원본 두 문서는 수정하지 않고, 공통 사실과 해석 차이만 별도 정리한다.

## 최종 조정 판정

두 보고서는 `핵심 방향`에서는 강하게 합의한다.

- `2 arc / 2시간급` 체감은 과장이 아니라는 점
- 병목의 중심이 `Stage 4`라는 점
- `Arc 2`에서 `Firewall / continuity reject / late-stage retry`가 비용과 시간을 급격히 키운다는 점
- `scene coverage 0%`, `dialogue 0%`, `InfoParadox`류 경고는 현재 런 기준 `false positive / noise`라는 점

차이는 주로 `원인 귀속의 중심`과 `historical evidence를 현재 causal set에 얼마나 올릴 것인가`에 있다.

즉, 이번 reconciliation의 결론은 아래와 같다.

- 공통 결론: `실제 병목은 Stage 4 late reject + retry amplification`
- 차이 지점: `그 late reject의 주원인을 Firewall 자체로 볼지, post-select/early-gate 부재까지 묶어서 볼지`
- 실무 결론: 두 해석은 경쟁 관계가 아니라 `같은 병목의 서로 다른 절단면`으로 병합하는 편이 맞다.

## 합의 사실

| id | 합의 사실 | Codex 근거 | OPUS 근거 | 통합 판단 |
|---|---|---|---|---|
| AF-1 | `Arc 1 = acceptance`, `Arc 2+ = overrun evidence` cutoff는 유지되어야 한다 | Codex `11-16`, `77-80` | OPUS `82-90`, `248`, `301` | 합의 사실 |
| AF-2 | `2 arc / 2시간급` 체감은 유효하다 | Codex `11-16` | OPUS `13`, `89-90` | 숫자 방식은 조금 다르지만 방향은 동일하다 |
| AF-3 | 시간과 비용의 중심은 `Stage 4`다 | Codex `80`, `112-113` | OPUS `143-146` | 합의 사실 |
| AF-4 | `Arc 2`의 retry amplification이 핵심 오버런 원인이다 | Codex `91-92`, `114` | OPUS `100-103`, `149-155` | 합의 사실 |
| AF-5 | `scene coverage 0%`, `ending hook miss`, `dialogue 0%`, `InfoParadox`는 현재 런 기준 병목이 아니라 noise에 가깝다 | Codex `94`, `127` | OPUS `105-106`, `118`, `152` | 합의 사실 |
| AF-6 | per-round observability는 아직 부족하다 | Codex `96`, `108`, `127-128` | OPUS `104`, `119`, `134`, `136` | 합의 사실 |

## 해석 차이

| id | 같은 사실 | Codex 해석 | OPUS 해석 | 조정 결론 |
|---|---|---|---|---|
| ID-1 | `ep5`는 Director 선택 후 뒤집혀 추가 round가 발생했다 | post-select continuity gate가 너무 늦게 발동하는 `pipeline placement` 문제가 핵심이다 | A-3 post-select 자체에 false positive 가능성이 있어 advisory화가 더 중요하다 | 둘 다 유효하다. `late gate`와 `gate quality`를 분리해서 다뤄야 한다 |
| ID-2 | `ep6`, `ep7`에서 `44` 방화벽 REJECT가 반복됐다 | Firewall/continuity bucket이 expensive full ensemble 이후에 반복된다는 점이 핵심이다 | Firewall 자체가 점수를 `44`로 강제 하향하고 full rewrite를 강요하는 구조가 핵심이다 | 두 해석은 충돌하지 않는다. `Firewall trigger timing + Firewall decision policy`를 묶어 수정해야 한다 |
| ID-3 | `Arc 2`의 화당 비용이 `Arc 1`보다 커졌다 | retry amplification이 더 큰 설명력이다. context growth는 보조적이거나 아직 hypothesis다 | context growth가 confirmed contributor이며 구조적 증가분이 존재한다. retry 제거 후에도 일부 상승은 남는다 | 통합 판단은 `둘 다`다. 다만 `즉시 절감 효과`는 retry path 정리가 더 크다 |
| ID-4 | PromptLoader / writing_directive 문제는 과거에 있었고 현재는 안 보인다 | current causal set의 앞줄에서 내려도 된다 | historical context로는 유효하지만 current rerun의 직접 병목은 아니다 | current run 기준 P0에서 제외, historical appendix로만 유지 |
| ID-5 | 숫자와 시간 합계는 문서마다 조금 다르다 | current rerun 중심으로 보수 집계했고 Stage 2/3는 estimated 최소화 | multi-session context까지 포함해 더 넓은 집계를 시도했다 | acceptance/overrun current run 집계는 Codex 쪽이 더 보수적이고, historical context는 OPUS appendix가 더 풍부하다 |

## 편측 발견

| id | 발견 주체 | 내용 | 현행 판단 | 후속 처리 |
|---|---|---|---|---|
| UF-1 | Codex | `stage2+stage3`만으로도 arc당 `12~13분` 수준의 fixed overhead가 남는다 | 유효 | Stage 4만 줄여도 총시간이 완전히 사라지지 않는다는 보조 사실로 유지 |
| UF-2 | Codex | `episode_production.jsonl`와 `stage_attempts` 사이에 interrupted session 저장 시차가 있다 | 유효 | observability backlog로 유지 |
| UF-3 | Codex | historical clean session 대비 current rerun에서는 병목 중심이 `ep1`에서 `Arc 2 continuity/post-select`로 이동했다 | 유효 | 운영 판단 메모로 유지 |
| UF-4 | OPUS | `pass_rate_monitor.json`의 `duration_ms=0`은 계측 누락이다 | 유효 | instrumentation backlog로 승격 가능 |
| UF-5 | OPUS | `llm_calls` 기준 API failure는 0이고, `gemini-2.5-flash` 비용 비중은 매우 낮다 | 유효 | 비용 최적화 우선순위에서 flash가 아니라 pro-heavy Stage 4를 계속 먼저 본다 |
| UF-6 | OPUS | `Session 1/2/3` 분리와 `ep1 9회 retry` historical cause chain(JSON mode, rubric exit 등)을 appendix로 복원했다 | 부분 유효 | current rerun의 직접 병목은 아니므로 appendix 전용으로 유지 |

## 통합 우선순위

| priority | target | 이유 | 통합 판단 |
|---|---|---|---|
| P0 | late reject를 expensive full rerun 대신 `earlier gate + single-candidate patch`로 전환 | 두 보고서 모두 `ep5~7`의 핵심 손실이 여기서 생긴다고 본다 | 최우선 |
| P0 | Firewall REJECT 시 `Director 재확인` 또는 `inplace patch` 경로 허용 | OPUS의 Firewall 정책 문제와 Codex의 late-stage discard 문제가 만나는 지점이다 | 최우선 |
| P1 | Stage 4 default fanout / self-critique depth를 상황부로 낮추기 | single-round floor 자체가 높아, retry를 줄여도 기본비용이 여전히 크다 | 차순위 |
| P1 | post-select / advisory / continuity rule의 blocking 조건 재정의 | 오탐과 진짜 모순을 더 앞단에서 분리해야 한다 | 차순위 |
| P2 | per-round token/cost/duration instrumentation 강화 | 다음 reconciliation에서 `같은 사실` 영역을 더 넓힐 수 있다 | 지속 과제 |

## 통합 결론

이번 reconciliation에서 바로 실행 가능한 공통 메시지는 하나다.

`Stage 4의 기본 round 비용이 높고, Arc 2에서는 그 위에 late reject와 firewall 반복이 붙으면서 2 arc / 2시간급 체감이 만들어진다.`

따라서 다음 배치의 초점은 아래 순서가 맞다.

1. `late reject`를 앞당기거나 patch로 치환
2. `Firewall`이 full rewrite만 강제하지 않도록 재설계
3. `Stage 4` 기본 fanout/self-critique 비용 절감
4. per-round instrumentation 확장

## Reconciliation Audit

### Pass 1. Fact pass

- acceptance와 overrun을 섞지 않았다
- 공통 사실은 두 문서에 모두 있는 주장만 올렸다
- 숫자 차이는 `집계 범위 차이`로 분리하고 억지 합의를 만들지 않았다

### Pass 2. Taxonomy pass

- `합의 사실`
- `해석 차이`
- `편측 발견`

위 3분류만 사용했다.

### Pass 3. Actionability pass

- 최종 섹션에서 통합 우선순위를 다시 닫았다
- 원문을 수정하지 않고 후속 구현 포인트만 남겼다
