# 글도비 4월 파일럿 성과 보고서

작성일: 2026-04-27  
분석 기간: 2026-03-05 ~ 2026-04-27  
핵심 비교: 2026-04-06 이전 대비 2026-04-27 현재

## 1. 결론

4월 초의 글도비는 "돌아가기는 하지만 어디서 얼마나 실패하는지 설명하기 어려운 파이프라인"에 가까웠다. 4월 말 현재는 S2, S3, S4를 분리해서 성공률, 재시도율, 실패 원인, 재현 가능성을 말할 수 있는 상태가 되었고, supervised run 기준으로는 거의 자동 생산 단계에 진입했다고 볼 수 있다.

핵심 결론은 다음과 같다.

- S2는 안정화됐다. 4월 초 성공률 80.3%, 성공 1건당 시도 1.246회에서, 4월 27일 현재 성공률 100%, 성공 1건당 시도 1.0회다.
- S3는 중후반 슬럼프에서 회복됐다. 4월 20~24일 성공률 80.0%, 성공 1건당 시도 1.25회였고, 4월 27일 현재 성공률 94.3%, 성공 1건당 시도 1.061회다.
- S4는 아직 병목이지만 명확히 개선됐다. 4월 20~24일 성공률 31.2%, 성공 1건당 시도 3.208회에서, 4월 27일 현재 성공률 43.5%, 성공 1건당 시도 2.3회다.
- S4 기준으로 4월 초 대비 현재 성공률은 +14.1%p, 성공 1건당 시도 수는 32.5% 감소했다.
- 월 200만 원 예산으로 무인 완전 자동화까지 완성했다고 말하기는 이르지만, supervised run 기준으로는 거의 자동 생산이 가능한 수준까지 도달했다.
- 4월 말까지 연속성과 생산성 이슈는 거의 닫혔다. 이제 핵심 과제는 원고 생산 여부가 아니라, 연출 레이어를 쌓아 상업성을 끌어올리는 것이다.
- 현재 단계는 단일 라벨보다 축별로 보는 것이 정확하다. S2/S3는 안정화 후기, S4는 세션메모리와 컨텍스트 캐싱을 통해 최적화 중기 진입, 재료 사이드는 도너 구조와 BI/TR 표준화까지 포함한 생산 체계 구축 단계다.

운영 문장으로 줄이면 이렇다.

> 4월 초에는 실패가 감으로 보였고, 4월 말에는 실패가 지표와 증거로 보인다. 연속성 및 생산성 이슈는 거의 닫혔고, 다음 과제는 연출 레이어와 상업성이다.

## 2. 현재 단계 판정

글도비는 한 단계로 묶어 말하기보다, 원고 런타임과 재료 사이드를 분리해서 보는 편이 정확하다.

| 구분 | 판정 | 근거 |
| --- | --- | --- |
| S2/S3 | 안정화 후기 | S2는 성공률 100% 구간에 들어섰고, S3도 4월 중후반 하락 후 94.3%까지 회복했다. 현재 주요 병목은 S2/S3가 아니다. |
| S4 | 최적화 중기 진입 | S4 성공 1건당 시도 수가 3.408회에서 2.3회로 줄었다. 세션메모리, 컨텍스트 캐싱, cache lineage 보강이 들어가면서 재시도율 2회 수렴을 노릴 수 있는 구간에 들어섰다. |
| 전체 원고 런타임 | 안정화 후기 | S4가 아직 최종 검증을 남겨두고 있으나, 실패 위치가 분해됐고 재시도율이 내려갔다. supervised run 기준으로는 연속 생산과 생산성 문제가 거의 닫힌 상태다. |
| 재료 사이드 | 생산 체계 구축 후기 | 도너 구조, work_guard, material-side SSOT, Stage0/Phase0/TR/BI read order, BI/TR pair 생산 표준화가 마련됐다. 원고 런타임 앞단의 재료 생산 체계는 단순 정리 단계를 넘어 표준 운영 단계에 들어섰다. |
| 고도화 | 초기~중기 전환 | 고도화 요소는 두 축에서 동시에 들어갔다. 런타임은 세션메모리/컨텍스트 캐싱, 재료 사이드는 도너/NAS/BI/TR 표준화가 핵심이다. 다만 상용화 완료 판단은 S4 최종 검증 이후가 적절하다. |

보고용 표현은 다음이 적절하다.

> 글도비는 4월 말 현재 원고 런타임은 안정화 후기, S4는 최적화 중기 진입, 재료 사이드는 생산 체계 구축 후기에 있다. supervised run 기준으로는 거의 자동 생산 단계에 들어섰고, 다음 과제는 연속 생산 자체가 아니라 연출 레이어와 상업성 강화다.

## 3. 분석 범위

이번 분석은 별도 보관한 benchmark 자료와 4월 개발 이력을 기준으로 정리했다.

수집 범위:

- 프로젝트 DB 185개
- DB 및 core log 계열 증거 7,666개
- `logs/metrics` 계열 파일 134개
- raw attempt row 4,638건
- dedup attempt row 1,065건
- S2 dedup attempt 286건
- S3 dedup attempt 393건
- S4 dedup attempt 386건
- historical backup, canary/probe, stress test, named project, numbered project, auto run 포함
- material-side SSOT 파일 5,834개
- treatments 계열 파일 878개
- BI 계열 파일 56개
- work_guard 계열 파일 16개
- 2026년 4월 수정 material-side 파일 426개, treatments 파일 314개, BI 파일 34개, work_guard 파일 16개

벤치마크 재현성 확인:

- `benchmark_index.csv` 9개 row 전부 local record dir, DB snapshot, log, `stage_metrics.csv` 존재 확인
- index 대 `stage_metrics.csv` 재계산 117/117 exact match
- raw source log 대 `stage_metrics.csv` 재계산 189/189 exact match
- GitHub issue #65에 재현성 매트릭스와 broad sweep 결과를 기록

주의할 점도 있다. 이 보고서는 엄밀한 A/B 테스트가 아니라 운영 증거 기반의 전후 비교다. 4월 27일 current window는 S4 attempt 23건, episode unit 11건으로 표본이 아직 작다. 따라서 "완료"가 아니라 "개선 확인 및 남은 병목 특정"으로 읽어야 한다.

## 4. 한눈에 보는 그래프

![Pipeline summary](../outputs/charts/human_facing/pipeline_human_summary.png)

![Stage2 summary](../outputs/charts/human_facing/stage2_human_facing.png)

![Stage3 summary](../outputs/charts/human_facing/stage3_human_facing.png)

![Stage4 summary](../outputs/charts/human_facing/stage4_human_facing.png)

## 5. 4월 초와 4월 말 비교

| 구분 | 4월 초 기준 | 4월 말 현재 | 해석 |
| --- | ---: | ---: | --- |
| S2 성공률 | 80.3% | 100.0% | S2는 현재 병목이 아니다. |
| S2 성공 1건당 시도 | 1.246회 | 1.000회 | 재시도 부담이 사라진 상태다. |
| S3 성공률 | 98.4% | 94.3% | 초반만 보면 낮아 보이나, 4월 중후반 하락 후 회복이 핵심이다. |
| S3 성공 1건당 시도 | 1.016회 | 1.061회 | 현재 거의 1회 수렴에 가깝다. |
| S4 성공률 | 29.3% | 43.5% | 병목이지만 의미 있는 개선이 있다. |
| S4 성공 1건당 시도 | 3.408회 | 2.300회 | 성공까지 필요한 시도 수가 약 32.5% 줄었다. |
| S4 reject rate | 70.7% | 56.5% | 실패율이 약 20.0% 줄었다. |

S3는 "4월 초 대비"만 보면 이미 높았던 수치에서 약간 낮아진 것처럼 보인다. 그러나 운영상 중요한 비교는 4월 20~24일의 하락 구간이다. 이 구간에서 S3는 성공률 80.0%, 성공 1건당 시도 1.25회까지 내려갔고, 4월 27일 현재 94.3%, 1.061회로 회복했다.

S4는 가장 중요한 병목이다. 4월 초 대비 성공률 +14.1%p, 성공 1건당 시도 32.5% 감소가 확인됐다. 4월 20~24일 대비로도 성공률 +12.3%p, 성공 1건당 시도 28.3% 감소다.

이 변화의 의미는 단순히 숫자가 좋아졌다는 데 있지 않다. 4월 초에는 S4가 원고 생산의 불확실성을 크게 만들었지만, 4월 말에는 supervised run 기준으로 실패를 감시하고 재시도시키며 생산을 이어갈 수 있는 형태가 되었다. 즉, 생산성 문제는 상당 부분 닫혔고, 이제 남은 과제는 "계속 생산되는가"보다 "상업적으로 더 잘 팔리는 장면인가"에 가깝다.

## 6. Stage별 진단

### S2

4월 초 S2는 pass-like 171건, reject 42건으로 성공률 80.3%였다. 현재는 7건 모두 pass-like로 성공률 100%다. 표본은 작지만, 4월 중순 이후 S2가 계속 100% 근처로 붙어 있다는 점에서 현재 병목은 S2가 아니다.

실무 의미:

- arc 생성 또는 Stage2 contract가 뒤 단계를 계속 흔드는 문제는 크게 줄었다.
- S2를 더 파는 것보다 S4와 Stage3/4 handoff에 리소스를 쓰는 편이 ROI가 높다.

### S3

S3는 4월 초에는 수치가 높았으나, 4월 중후반에 authority alignment, reroute, blueprint recovery 계열 문제가 드러나며 성공률이 79~80%대로 내려갔다. 4월 27일 현재는 35건 중 33건 pass-like, 성공률 94.3%다.

실무 의미:

- S3는 완전히 무시할 단계는 아니지만, 현재는 회복 흐름이다.
- S4 실패 일부가 S3 handoff나 blueprint lineage와 연결될 수 있으므로 S3는 "보조 병목"으로 감시하면 된다.

### S4

S4는 여전히 글도비의 핵심 병목이지만, 이제는 "생산 가능 여부"를 막는 병목이라기보다 "재시도 비용과 연출 품질"을 조정하는 병목에 가깝다. 4월 초와 비교하면 성공률은 29.3%에서 43.5%로 올랐고, 성공 1건당 시도 수는 3.408회에서 2.3회로 줄었다.

Episode unit 기준으로 보면 4월 27일 현재 S4 episode pass rate는 90.9%다. 다만 current window는 11 episode unit이고, 일부 current run은 아직 최종 검증이 닫히지 않았으므로, 이 수치는 "상용 완료"가 아니라 "수렴성 개선 신호"로 해석해야 한다.

남은 병목:

- POST_SELECT_CONFLICT가 아직 current S4 attempt 23건 중 11건에서 관측된다.
- rejected artifact rehydration, manuscript cache lineage, Director cache lineage guard가 최근까지 집중적으로 보강됐다.
- 최종 검증이 닫히기 전까지 무인 완전 자동화로 표현하면 이르다.
- 다만 supervised run 기준으로는 거의 자동 생산 단계에 진입했다고 볼 수 있다.

## 7. 개발 작업 근거

4월 개발 이력도 함께 확인했다. 기준은 2026-04-01부터 2026-04-27까지의 형상관리 기록이다.

요약:

- 4월 1~27일 작업 단위: 305개
- 변경 파일 수: 19,828개
- 벤치마크/증거 인프라: 77개
- Stage4 원고/재시도 안정화: 74개
- Stage3 블루프린트/복구 안정화: 33개
- Stage2 arc/계약 안정화: 30개
- 테스트/CI 게이트: 24개
- 운영 문서화: 23개

영역별 touch:

| 영역 | 작업 touch | 변경 파일 수 | 의미 |
| --- | ---: | ---: | --- |
| ops docs | 167 | 2,342 | 실행문서, 감리, 증거화 비중이 컸다. |
| tests | 118 | 131 | 회귀 방지와 CI gate가 병행됐다. |
| runtime code | 116 | 151 | 실제 런타임 수정이 문서 작업과 함께 진행됐다. |
| stage3 | 95 | 5,852 | blueprint/recovery 및 산출물 계열 변화가 컸다. |
| stage4 | 81 | 2,037 | manuscript/retry/post-select 병목에 집중 투입됐다. |
| stage2 | 80 | 1,159 | arc/contract 안정화 작업이 누적됐다. |
| benchmark evidence | 66 | 99 | benchmark archive, comparator, proof evidence 작업이 누적됐다. |
| director authority | 66 | 99 | Director/authority/cache lineage 계열 보강이 있었다. |

대표 작업 흐름:

- 4월 초: Stage2/Stage4 contract normalization, Stage4 repair-contract grammar, entity post-select, fixpack canary 조사
- 4월 중순: Stage2 cross-stage authority packet, Stage3 arbiter, prompt envelope, repair router, authority alignment 보강
- 4월 20일 전후: Stage3 reroute recovery, replay plateau loop, failure summary 안정화
- 4월 23~24일: benchmark comparator, archive reproducibility, 운영 보고서, context-cache telemetry, native proof sidecar 보강
- 4월 25일 전후: session memory persistence, authority-run-result truth, Stage4 pass settlement, live-run safety lock, runtime evidence freshness
- 4월 27일: Stage4 rejected artifact rehydration, sessionless hydration guard, post-select retry scope, manuscript cache lineage, Director cache lineage guard 보강

즉, 4월의 git 작업은 단순 기능 추가가 아니라 다음 네 축에 집중됐다.

1. 실패를 볼 수 있게 만드는 증거 인프라
2. S2/S3 contract와 authority alignment 안정화
3. S4 manuscript/retry/post-select 병목 완화
4. cache, session memory, proof, CI gate를 통한 회귀 방지

## 8. 개선 항목별 정리

4월 작업은 단순한 오류 수정이 아니라, 파이프라인이 원고 생산 시스템으로 버티기 위한 기반을 단계적으로 쌓는 작업이었다.

| 개선 항목 | 4월 작업 내용 | 성과 |
| --- | --- | --- |
| 디버깅 | Stage별 실패 로그, retry, hydration, post-select, cache 계열 문제를 분리해 추적 | 실패가 "막연한 품질 저하"가 아니라 S2/S3/S4별 병목으로 분해됨 |
| 권위정렬 | Director 판단, authority packet, result truth, cache lineage, settlement status 보강 | 단계 간 판단 충돌과 stale result 사용 위험을 낮춤 |
| 구조화 | S2/S3/S4 지표 분리, benchmark archive, comparator, 운영 보고서 구성 | 개선 여부를 회고가 아니라 수치로 설명할 수 있게 됨 |
| 계층화 | Stage2 arc, Stage3 blueprint, Stage4 manuscript/retry 흐름을 분리해 관리 | 한 단계의 실패가 전체 실패로 뭉개지는 문제를 줄임 |
| 재료 생산 구축 | material-side, work_guard, project artifact, run artifact 관리 체계 정리 | 작품 재료와 원고 생산 런타임을 분리해 운영할 기반 확보 |
| 도너 구조 도입 | donor review/adoption contract, donor registry, donor doctrine packet, deepclone 기준 샘플 정리 | 신규 작품 생산 시 재료 재사용과 품질 기준화를 위한 기반 확보 |
| NAS/자료 보관 | NAS sample corpus, waiting room, quarantine, root shelf 정리 흐름 반영 | 재료를 개인 작업물 단위가 아니라 재사용 가능한 자료 보관 체계로 이동 |
| BI/TR 생산 표준화 | production-pair schema, benchmark spec, operational registry, TR/BI pair 흐름 정리 | BI/TR 생산을 일회성 수작업이 아니라 반복 가능한 생산 단위로 표준화 |
| 기타 로직 개선 | session memory, context cache, provider fallback, CI gate, UTF-8 hygiene 보강 | 반복 실행 안정성, 회귀 방지, 운영 재현성이 개선됨 |

이 중 4월의 직접 성과는 디버깅, 권위정렬, 구조화, 계층화만이 아니다. 재료 생산 구축, 도너 구조, NAS/자료 보관, BI/TR 생산 표준화도 별도 성과축으로 반영해야 한다. 원고 런타임이 S4 재시도율을 줄이는 동안, 재료 사이드는 "무엇을 넣어 생산할 것인가"를 표준화한 셈이다.

## 9. 재료 사이드 구축 성과

4월 성과는 원고 생성 런타임에만 있지 않다. 재료 사이드는 글도비 파이프라인 앞단의 생산 표준화 작업이며, 이번 달에 별도 성과로 볼 만한 구축이 있었다.

핵심 구축물:

- `material_ssot` stage-axis root 정리
- 공식 단계 체인 정리: 리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성
- donor review/adoption contract 도입
- work_guard를 pre-TR companion artifact로 승격
- production-pair benchmark spec 도입
- production-pair schema standard 도입
- production-pair operational registry 도입
- material-side read order 정리
- 2026-04-20 donor-ready root wave를 waiting room으로 정리
- golden canary deepclone 계열 fullblock baseline 승격

정량 근거:

| 항목 | 수량 |
| --- | ---: |
| material-side SSOT 파일 | 5,834개 |
| 4월 수정 material-side 파일 | 426개 |
| treatments 계열 파일 | 878개 |
| 4월 수정 treatments 파일 | 314개 |
| BI 계열 파일 | 56개 |
| 4월 수정 BI 파일 | 34개 |
| work_guard 파일 | 16개 |
| Phase0 design 파일 | 31개 |
| TR 70-block draft 파일 | 36개 |
| BI JSON 파일 | 43개 |
| source_manifest 보유 preprocess work | 24개 |
| material_bundle_summary 보유 preprocess work | 23개 |
| phase0_ready_snapshot 보유 preprocess work | 23개 |
| 2026-04-20 donor-ready waiting room 파일 | treatments 45개, BI 13개, work_guard 12개 |

이 축의 실무 의미:

- 원고 런타임이 좋아져도 재료가 매번 제각각이면 생산성이 흔들린다.
- 4월에는 재료를 `research -> pitch -> Stage0 -> Phase0 -> TR -> BI`로 넘기는 표준 경로가 생겼다.
- 도너 구조는 새 작품을 완전히 맨땅에서 만들지 않고, 검증된 재료와 구조를 재사용할 수 있게 만든다.
- NAS sample corpus와 waiting room/quarantine 구조는 자료를 흩어진 파일이 아니라 관리 가능한 생산 자산으로 다루기 위한 기반이다.
- BI/TR pair 표준화는 "작품별 감"이 아니라 반복 생산 가능한 납품 전 단계로 가기 위한 핵심 기반이다.

## 10. 200만 원 예산 사용 근거

월 200만 원 예산으로 무인 완전 자동 상용화를 기대하는 것은 현실적이지 않다. 다만 4월 말 현재 글도비는 supervised run 기준으로 거의 자동 생산이 가능한 수준까지 올라왔고, 이 정도 성과는 파일럿 예산 대비 충분히 큰 진전이다. 4월 예산은 불확실한 원고 생산 파이프라인을 계량 가능한 운영 대상으로 바꾸고, 그 앞단의 재료 생산 체계까지 표준화하는 데 쓰였다.

개발 속도와 검증 범위는 투입 예산 및 운영 리소스에 비례한다. 비용 제약이 없다면 여러 장르와 여러 작품에 대해 supervised run을 병렬로 확대할 수 있고, 이 경우 pass율, 재시도율, 장르별 실패 유형, 상업성 편차를 더 빠르게 수집할 수 있다. 따라서 다음 예산 논의의 핵심은 단순 인건비가 아니라, 사업 판단 가능한 검증 표본을 얼마나 빠르게 확보할 것인가다.

확보된 산출물:

- S2/S3/S4를 분리한 성능 지표
- raw 4,638 attempt에서 dedup 1,065 attempt로 정리된 분석 데이터
- canary/probe, numbered project, named project, historical backup까지 포함한 broad sweep
- benchmark archive 재현성 검증
- 사람이 읽을 수 있는 Stage별 그래프
- GitHub issue 기반 benchmark 추적 체계
- 4월 git 작업과 성능 지표를 연결할 수 있는 근거
- 남은 병목이 S4 POST_SELECT_CONFLICT와 최종 검증이라는 구체적 다음 액션
- 도너 기반 재료 재사용 구조
- NAS/sample corpus 기반 자료 보관 흐름
- BI/TR pair 생산 표준화
- work_guard 기반 pre-TR 품질 보조 체계

이 관점에서 200만 원 예산은 "사람이 전혀 보지 않아도 되는 무인 자동화"를 완성한 비용이 아니다. 그러나 supervised run 기준으로는 거의 자동 생산 단계에 도달했고, "어디가 병목인지 모르는 상태"를 "연속 생산은 가능하고, 다음은 연출과 상업성을 높이면 되는 상태"로 바꾼 비용이다. 특히 S4에서 성공 1건당 시도 수가 3.408회에서 2.3회로 줄어든 것은 비용과 시간 양쪽에서 직접적인 운영 개선이다. 이후 고도화 속도는 장르별 supervised run 표본 수, 3아크 연속 실행, 장기기억 proof, 연출 레이어 검증을 얼마나 병렬로 확보할 수 있는지에 달려 있다.

내부 설명용 문장:

> 4월 파일럿 예산 200만 원은 글도비를 supervised run 기준 거의 자동 생산 단계까지 끌어올리고, S4 수렴성을 28~35% 개선하며, 도너/재료/BI/TR 생산 체계를 표준화한 검증 비용으로 쓰였다.

> 비용이 허용되면 장르별 supervised run을 병렬 확대해 고도화 속도를 높일 수 있고, 현재의 주요 제약은 기술 가능성보다 검증 표본과 운영 예산이다.

## 11. 다음 과제: 연출 레이어와 상업성

4월 말까지 연속성 및 생산성 이슈는 거의 닫힌 것으로 보는 편이 맞다. 다음 단계는 "원고가 계속 나오느냐"가 아니라 "그 원고가 플랫폼 독자에게 더 잘 먹히느냐"다.

다음 과제는 연출 레이어다.

- 초반 3화 흡입력
- 회차별 엔딩 훅
- 장면 압축과 정보 배치
- 감정선의 누적과 폭발 지점
- 주인공 보상감의 선명도
- 독자 기대를 끊지 않는 클리프행어
- TR/BI의 상업 장면 지시 강화
- S4 원고에서 문장력, 리듬, 장면 전환감을 끌어올리는 후처리 루프

즉, 4월까지는 "생산 가능한가"를 닫는 달이었다. 5월부터는 "팔릴 만하게 연출되는가"를 쌓는 달로 보는 것이 적절하다.

## 12. 아직 말하면 안 되는 것

아래 표현은 아직 이르다.

- "글도비는 무인 완전 자동 생산 파이프라인으로 완성됐다."
- "S4 문제가 해결됐다."
- "모든 프로젝트 유형에서 동일한 개선이 검증됐다."
- "현재 수치가 장기 평균으로 고정됐다."
- "재료 사이드 표준화가 곧바로 상용 납품 품질을 보장한다."

대신 이렇게 말하는 편이 정확하다.

- "S2는 안정화됐다."
- "S3는 4월 중후반 하락 후 회복됐다."
- "S4는 병목이지만 성공률과 재시도율이 개선됐고, supervised run 기준 거의 자동 생산 단계에 들어섰다."
- "연속성 및 생산성 이슈는 거의 닫혔고, 남은 과제는 연출 레이어와 상업성이다."
- "4월 말 현재, 개선 여부를 말할 수 있는 계측 체계가 만들어졌다."
- "재료 사이드는 도너, work_guard, BI/TR pair 표준화를 통해 생산 체계 구축 후기에 들어섰다."

## 13. 다음 액션

우선순위는 S4다.

1. current 04/27 run의 최종 검증을 닫는다.
2. POST_SELECT_CONFLICT attempt를 episode, blueprint lineage, manuscript cache lineage 기준으로 재분류한다.
3. current window의 S4 표본을 최소 50~100 attempt까지 늘려 신뢰도를 올린다.
4. S3 handoff가 S4 reject를 유발하는 케이스를 별도 라벨링한다.
5. 이번 benchmark 보고서를 issue #62~#65와 연결해 다음 보고 주기의 baseline으로 삼는다.
6. 재료 사이드는 donor-ready root wave와 BI/TR pair registry를 다음 보고 주기 baseline으로 삼는다.
7. NAS/sample corpus 기반 재료가 실제 TR/BI 품질과 S4 재시도율에 미치는 영향을 별도 추적한다.
8. S4 후처리 루프에 연출 평가축을 추가한다.
9. 첫 3화, 엔딩 훅, 보상감, 장면 리듬을 별도 상업성 지표로 분리한다.

## 14. 근거 자료

주요 산출물:

- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\all_attempts_collection_summary.json`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\benchmark_period_summary.json`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\summary_by_window_stage.csv`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\stage4_improvement_estimates.csv`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\stage4_episode_window_summary.csv`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\git_april_activity_summary.json`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\git_april_area_stats.csv`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\git_april_commits.tsv`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\material_side_april_activity_summary.json`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\charts\human_facing\pipeline_human_summary.png`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\charts\human_facing\stage2_human_facing.png`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\charts\human_facing\stage3_human_facing.png`
- `C:\Users\wjjo\Desktop\글도비-benchmark\outputs\charts\human_facing\stage4_human_facing.png`
