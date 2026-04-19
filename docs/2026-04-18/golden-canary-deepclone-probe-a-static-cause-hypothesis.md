# Golden Canary Deepclone Probe A Static Cause Hypothesis

Date: 2026-04-18
Status: final
Scope: `canonical 골든 카나리아` vs `golden_canary_deepclone_probe_a` bounded canary evidence를 바탕으로, 왜 `Probe A`가 Stage2/Stage3에서 더 잘 먹혔는지에 대한 정적 원인 가설 정리
Source Anchors:
- [canonical Stage3 ep2 summary](C:\Users\PC\Desktop\글도비\projects\_canary\canonical_stage34ab_ep12_r2\logs\stage3_canary_summary.json:1)
- [hook-only Stage3 ep2 summary](C:\Users\PC\Desktop\글도비\projects\_canary\canonical_stage3_hookaudit_ep2_r2\logs\stage3_canary_summary.json:1)
- [Probe A Stage3 ep2 summary](C:\Users\PC\Desktop\글도비\projects\_canary\probe_a_stage34ab_ep12_r2\logs\stage3_canary_summary.json:1)
- [canonical opening blueprint](C:\Users\PC\Desktop\글도비\projects\_canary\canonical_stage34ab_ep12_r2\plans\blueprints\blueprint_0001.txt:1)
- [Probe A opening blueprint](C:\Users\PC\Desktop\글도비\projects\_canary\probe_a_stage34ab_ep12_r2\plans\blueprints\blueprint_0001.txt:1)
- [canonical work_guard](C:\Users\PC\Desktop\글도비\projects\_canary\canonical_stage34ab_ep12_r2\config\work_guard.yaml:1)
- [Probe A work_guard](C:\Users\PC\Desktop\글도비\projects\_canary\probe_a_stage34ab_ep12_r2\config\work_guard.yaml:1)
- [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:719)
- [stage_cross_stage_contract.py](C:\Users\PC\Desktop\글도비\modules\core\stage_cross_stage_contract.py:263)

## Executive Verdict

현재 가장 보수적인 정적 결론은 아래와 같다.

- `Probe A`의 효과는 `0`이 아니다.
- 하지만 효과의 본체는 `좋은 ending_hook 하나`가 아니다.
- 더 가능성 높은 설명은 `재료 계약 sharpen -> retrieval anchor 증가 -> 합법적인 브리지 surface 증가 -> 구조 자산 receipt 고정`의 bundle effect다.

즉 이번 bounded evidence는 `hook 단독 개선`보다 `search-space shaping 개선` 쪽에 더 가깝다.

## What The Runs Say

핵심 런타임 사실은 단순하다.

- canonical `ep2`는 `FAILED`, `45 calls`, `4 retries`, 약 `4065s`
- hook-only canonical `ep2`도 `FAILED`, `75 calls`, `5 retries`, 약 `5942s`
- Probe A `ep2`는 `PASS(92)`, `13 calls`, `0 retries`, 약 `423s`

따라서 `직전 화 ending_hook만 Probe A식으로 바꾸면 canonical도 통과할 것`이라는 가설은 현재 evidence상 기각된다.

## Static Hypothesis

### 1. Probe A는 목표함수를 더 촘촘하게 고정한다

canonical의 opening reward는 상대적으로 `수익`, `재평가`, `다음 판 암시`에 머무는 편이다.

반면 Probe A는 처음부터 아래를 강하게 못 박는다.

- `private receipt`
- `named seat`
- `우선 응답권`
- `예외 계좌`
- `access shift`

이 차이는 [Probe A work_guard](C:\Users\PC\Desktop\글도비\projects\_canary\probe_a_stage34ab_ep12_r2\config\work_guard.yaml:5)와 [canonical work_guard](C:\Users\PC\Desktop\글도비\projects\_canary\canonical_stage34ab_ep12_r2\config\work_guard.yaml:5)의 `one_line_truth`, `tracking_slots`, `mandatory_scene_engines`, `custom_rules` 비교에서 바로 보인다.

현재 가설은, 이 sharper한 목표함수 덕분에 모델이 `돈을 번다`에서 멈추지 않고 `돈을 구조 자산으로 환전한다`까지 더 빨리 달리게 된다는 쪽이다.

### 2. Probe A는 retrieval source pack에 걸리기 좋은 명사를 더 많이 만든다

Stage3의 Context Advisor는 구조상 아래 slot들을 source pack에 넣을 수 있다.

- `similar_blueprint`
- `npc_history`
- `continuity_hook`
- `work_tracking_slot_*`
- `work_scene_engine_*`

근거는 [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:719), [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:729), [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:743), [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:788), [context_advisor.py](C:\Users\PC\Desktop\글도비\modules\core\context_advisor.py:799)다.

Probe A 재료는 `PB센터`, `박성호`, `private receipt`, `named seat`, `우선 응답권` 같은 구체 명사가 opening부터 많다. 그래서 retrieval이 추상 감정보다 `기관/인물/권한` anchor를 더 쉽게 잡고, 다음 화 candidate도 더 구체적인 실무 표면으로 미끄러질 가능성이 높다.

### 3. Probe A는 stop line을 깨지 않으면서 전진하는 브리지 동작을 더 잘 만든다

Stage3는 replay 금지와 reserved beat 금지가 강하다. 너무 보수적이면 직전 화 replay로 죽고, 너무 공격적이면 다음 화 사건 선소비로 죽는다.

opening continuity 판정도 [stage_cross_stage_contract.py](C:\Users\PC\Desktop\글도비\modules\core\stage_cross_stage_contract.py:263) 기준으로 빡빡하다.

- 같은 위치이고 time shift가 없으면 `direct_continuation`
- 같은 구역 이동이나 장면 전환 cue가 있으면 `explicit_transition`
- 아니면 `jump_opening`

Probe A opening은 `PB에게 내일 방문을 통보` 같은 식으로, 실제 `방문/유동화/실행`은 뒤 화에 남겨두고도 현재 화에서 합법적으로 전진한다.

즉 현재 가설상 Probe A의 장점은 `센 훅` 자체보다 `reserved beat를 먹지 않는 중간 행동`을 더 잘 제공하는 데 있다.

### 4. 구조 자산은 현금/감정보다 cross-stage carryover에 더 잘 남는다

`감정적 각성`, `계획 수립 완료`, `수익 발생` 같은 상태는 의미상 맞아도 다음 화 generator가 다시 꺼내 쓰기에는 약한 편이다.

반면 `예외 계좌`, `VIP 전담 라인`, `named seat`, `priority response list` 같은 구조 자산은:

- 명사형으로 저장되기 쉽고
- continuity anchor로 재호출하기 쉽고
- 다음 화 목표 surface로 이어지기 쉽다

즉 Probe A는 reward를 `숫자`보다 `제도/접근권`으로 저장하게 만들어 파이프라인 친화도가 높아진 것으로 보인다.

## Why Hook-Only Was Not Enough

`hook-only` 실험은 두 가지를 분명히 보여줬다.

- `continuity hook`이 전혀 무의미한 것은 아니다
- 하지만 그것만으로는 canonical failure mode를 못 뒤집는다

실험 `r2`에서는 훅이 실제 Stage3 prompt까지 들어갔다. 그럼에도 canonical `ep2`는 그대로 `replay/authority/구조 계약 미달` 루프에 갇혔다.

따라서 현재 더 타당한 설명은:

`ending_hook 1개`의 문제가 아니라, upstream material contract와 retrieval topology 전체가 달라서 생긴 차이다.

## Working Model

지금 시점의 working model은 아래로 고정한다.

`Probe A improvement = better material contract + richer retrieval anchors + safer bridge surfaces + more persistent structural receipts`

즉 `좋은 문장`보다는 `좋은 탐색 공간` 쪽의 개선으로 본다.

## Operating Consequence

운영 결론은 지금 고정해도 된다.

- `Probe A`는 유의미한 실효가 있다
- 단일 hook 효과는 약하다
- 효과의 본체는 bundle effect다
- 큰 wave는 여전히 금지하고 `small tranche only`로 간다

연구 결론은 아직 닫지 않는다.

가장 값진 다음 질문은 여전히 이것이다.

- `continuity_hook + npc_history`만 바꿔도 비슷한 개선이 나는가
- 아니면 `work_guard / tracking_slot / scene_engine` sharpen이 본체인가

## Residual Uncertainty

- 현재 표본은 한 작품, opening family, bounded tranche 기준이다
- `ep3+`에서도 같은 우위가 유지되는지는 아직 미확정이다
- Stage4까지 포함한 end-to-end 우위 결론은 아직 이르다

## Pass 1

- 문서 타입: `static cause hypothesis`로 요청과 일치
- scope: `왜 좋아졌는가`에만 한정
- side-effect coverage: 코드 변경 없음, temp mirror 비적용

## Pass 2

- 모든 핵심 주장은 bounded canary summary, opening blueprint, work_guard, code slot topology에 묶었다
- `hook-only` 실패 사실을 명시해 과잉 결론을 막았다
- `전면 채택`이나 `완전 인과 증명`은 주장하지 않았다

## Pass 3

- 운영 결론과 연구 결론을 분리해 다음 reader가 바로 사용할 수 있게 했다
- 다음 질문을 `ablation` 단위로 축소했다
- 과도한 세계관 해석이나 stylistic praise는 제거했다

Confidence: 96/100
