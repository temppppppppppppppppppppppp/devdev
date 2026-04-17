# modern_fantasy 딥클로닝 대응 레이어 survey + adversarial 3-pass report

Date: 2026-04-17
Status: final
Scope: `chaebol_allowance_zero` 계열 modern-fantasy deep-cloning 우려에 대한 정적 아이디어 survey와 추천안

## 0. Executive Recommendation

추천안은 `작품 가드(work_guard + profile_lock) -> profile-aware runtime adapter -> Stage3 profile-aware surface adapter` 순입니다.

- `작품 가드`가 **주 owner**여야 한다.
- `장르 가드`는 broad modern-fantasy guard 확장이 아니라 **profile-aware adapter**가 되어야 한다.
- `Stage3`는 **부분 owner / downstream safety net**이어야 한다.

한 줄로 줄이면:

`현대판타지 딥클로닝`은 broad 장르 가드를 더 키울 문제가 아니라, 이미 잠긴 작품/프로파일 truth가 runtime과 Stage3까지 제대로 전달되지 않는 문제로 보는 쪽이 가장 맞다.

## 1. Context Fix

요청하신 정확한 파일명 `bulhaeng-chaebol-ep0052-0101-session-context.md`는 현재 워크스페이스에서 찾지 못했다.

이번 survey는 아래를 가장 가까운 대체 컨텍스트로 사용했다.

- `docs/재료 만들다가 만 것/chaebol-allowance-zero-density-rewrite-session-context.md`
- `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/prompt.md`
- `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json`
- `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/fixed.json`

이 대체 컨텍스트 기준으로 보면, 현재 `Block 52`의 live surface는 이미 `추적/잠입/액션`이 아니다.

- block goal은 `열두 도시의 청소, 세탁, 급식 단가를 한 표로 바꾸자 지역 사장들이 처음 같은 숫자로 말하기 시작한다.` 쪽이다. `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/prompt.md:10`
- 실제 candidate/fixed도 `전국 운영사 화상회의실`, `정산 포털`, `지역 사장 네트워크`, `표준단가 계약`, `운영권/정산권` 축이다. `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json:5`, `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json:7`, `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json:53`

즉 이번 질문은 “현재 block 52 산출물이 이미 액션물처럼 망가졌다”기보다, “다른 데서 generic 현대판타지 습관이 섞여도 이 작품이 그런 쪽으로 끌려가지 않게 어느 레이어에서 막아야 하냐”로 읽는 게 맞다.

## 2. Baseline Truth

이 작품의 upstream identity는 이미 꽤 강하게 잠겨 있다.

- `profile_lock.json`은 `business_growth_profile + office_power_profile`를 고정하고, `deal_type`를 계약 구조 변경, 외주 재편, 승인권 확보, 공급망 장악, 정산선 통합 같은 사업 액션으로 읽게 한다. `treatments/preprocess/chaebol_allowance_zero/profile_lock.json:2`, `treatments/preprocess/chaebol_allowance_zero/profile_lock.json:42`
- `work_guard`는 generic operations flattening, pure stock/investment drift, abstract charisma-power talk, free family bailout 등을 금지하고, 이 작품 고유 엔진을 `누수/병목 감지 -> 즉시 개입 -> 반복 현금흐름/권한 회수`로 고정한다. `work_guards/02_chaebol_allowance_zero.yaml:37`, `work_guards/02_chaebol_allowance_zero.yaml:58`, `work_guards/02_chaebol_allowance_zero.yaml:110`
- blockguide SSOT도 modern-fantasy를 broad genre 하나로 읽지 않고 `공통 코어 + 장르 프로파일`로 읽으라고 못박고 있다. `docs/blockguide/SSOT_blockguide-integrated-order.md:13`, `docs/blockguide/SSOT_blockguide-integrated-order.md:53`
- `chaebol_allowance_zero`의 canonical profile mapping도 이미 `business_growth_profile + office_power_profile`다. `docs/blockguide/bi-production-harness-v1.md:493`

따라서 작품 truth 자체가 약한 것은 아니다. 문제는 이 truth가 downstream까지 동일한 해석 강도로 전달되느냐이다.

## 3. Parallel Survey

### 3.1 작품 가드 / profile lock

판정: **primary owner**

이 레이어가 제일 강한 이유는, 여기서 이미 “이 작품이 무엇을 전장으로 삼는지”가 잠겨 있기 때문이다.

- `profile_lock`은 작품을 어떤 장르 프로파일로 읽을지 잠그는 정식 파일이다. `전처리_ssot/docs/stage0_profile_lock_harness.md:12`
- 같은 harness는 `resource/power/control/payoff/failure/hud_interpretation`까지 작품 단위로 잠가야 한다고 말한다. `전처리_ssot/docs/stage0_profile_lock_harness.md:57`
- `modern_fantasy_material_harness`도 동일하게 `primary_profile / secondary_profile` 잠금과 `source_manifest` 수동 감리를 요구한다. `docs/blockguide/modern_fantasy_material_harness.md:46`, `docs/blockguide/modern_fantasy_material_harness.md:100`

이건 broad 장르보다 훨씬 좁고, `urban_power_profile`식 추적/잠입/레이드 감각이 끼어드는 걸 upstream에서 가장 잘 막는다.

다만 한계도 있다.

- `work_guard`는 AGENTS 기준으로 “global material-side standard companion artifact”이지 consumer hard gate는 아니다. `AGENTS.md:8`
- 즉 semantic owner로는 가장 강하지만, runtime이 이 truth를 실제로 소비하지 않으면 혼자서 실행력을 만들지는 못한다.

### 3.2 장르 가드 / runtime guard

판정: **broad genre guard는 부적합, profile-aware adapter가 적합**

이 레이어에서 지금 필요한 건 “현대판타지 guard를 더 크게”가 아니다.

- blockguide SSOT는 broad genre보다 `profile` 재해석이 본질이라고 이미 선언한다. `docs/blockguide/SSOT_blockguide-integrated-order.md:53`
- Stage 0 코드도 profile별 HUD defaults와 `hud_interpretation`을 다룰 준비가 있다. `modules/core/reference_selection_stage0.py:48`, `modules/core/reference_selection_stage0.py:747`, `modules/core/stage0_phase0_seed.py:240`
- 그런데 runtime 쪽 guard construction은 아직 broad genre 문자열 위주다. `main_a.py:1344`, `modules/core/genre_guards/__init__.py:22`, `modules/core/constants.py:47`, `modules/core/constants.py:417`
- 현재 `InvestmentGuard`는 금융 특화 guard라서, modern-fantasy 공통 guard처럼 쓰면 finance/business 쪽으로 과적합된다. `modules/core/genre_guards/investment_guard.py:17`, `modules/core/genre_guards/investment_guard.py:198`, `modules/core/genre_guards/investment_guard.py:613`
- Writer/Director도 coarse genre는 보지만 profile context는 직접 모른다. `modules/domain/agents/writer.py:149`, `modules/domain/agents/writer.py:338`, `modules/domain/agents/director.py:97`

즉 정답은:

- `새 broad genre guard` 아님
- `investment_guard.py 내부 분기 추가` 아님
- `profile_lock -> runtime guard / prompt / HUD interpretation`를 연결하는 **profile-aware adapter**

### 3.3 Stage3 generator

판정: **partial owner / downstream safety net**

Stage3가 필요한 이유는 replay-collapse와 wrong-surface basin을 여기서 실제로 맞닥뜨리기 때문이다.

- runtime은 genre를 bootstrap하고 constraint compiler로 넘긴다. `modules/domain/agents/three_phase_blueprint_runtime.py:1278`, `modules/domain/agents/three_phase_blueprint_runtime.py:1327`
- 그런데 `episode_progression_packet`과 `surface_guidance`는 실제로 genre/profile semantics를 거의 반영하지 않는다. `modules/domain/agents/blueprint_constraint_compiler.py:345`, `modules/domain/agents/blueprint_constraint_compiler.py:1241`
- `BlueprintEnsemble`은 여전히 `action/emotion/dialogue`류 generic strategy를 쓰고, genre-specific branch도 무협 internal-energy, hunter/fantasy system-ui 허용 정도로 좁다. `modules/domain/agents/blueprint_ensemble.py:53`, `modules/domain/agents/blueprint_ensemble.py:1722`
- validator의 replay 판정도 location + character overlap 중심이라 genre-semantic family 판정이 아니다. `modules/domain/agents/unified_blueprint_validator.py:2196`, `modules/domain/agents/unified_blueprint_validator.py:2273`

그래서 Stage3는 “같은 장소/인물 재탕 방지”는 일부 맡을 수 있지만, 작품의 장르/프로파일 truth 전체를 주 owner로 들고 가기에는 늦다.

다만 이 레이어는 분명 필요하다.

- `stage3-generator-genre-aware-surface-diversification-context.md`가 정리했듯, 방향은 `common substrate + genre adapters`가 맞다. `docs/2026-04-17/stage3-generator-genre-aware-surface-diversification-context.md:47`, `docs/2026-04-17/stage3-generator-genre-aware-surface-diversification-context.md:114`
- 여기서 더 정확히는 `genre adapter`보다도 `profile-aware surface adapter`에 가깝다.

## 4. Adversarial 3-Pass Audit

### Pass 1. 작품 가드만으로 충분한가

공격 질문:
`work_guard/profile_lock이 이미 있는데 왜 또 다른 레이어가 필요하냐`

판정:
**불충분하다.**

이유:

- `work_guard`는 semantic owner지만 hard gate가 아니다. `AGENTS.md:8`
- runtime guard / Writer / Director / Stage3가 profile truth를 직접 먹지 않으면 upstream truth가 downstream에서 희석된다.

결론:
`작품 가드만으로 충분`은 false.

### Pass 2. broad 장르 가드를 키우면 되지 않나

공격 질문:
`그냥 현대판타지 guard를 더 똑똑하게 만들면 되는 것 아닌가`

판정:
**비추천이다.**

이유:

- modern-fantasy umbrella 자체가 `business_growth`, `office_power`, `investment_market`, `urban_power` 등을 함께 받는다. `docs/blockguide/SSOT_blockguide-integrated-order.md:32`
- broad guard를 키우면 결국 제일 일반적인 현대판타지 관성, 또는 기존 `investment`/`urban_power` 쪽 표현이 다시 세지기 쉽다.
- 지금 문제도 정확히 그런 broadness 때문에 생긴다.

결론:
`broad modern-fantasy guard 강화`는 false.

### Pass 3. Stage3만 고치면 되지 않나

공격 질문:
`surface diversification을 잘하면 결국 해결되지 않나`

판정:
**부분만 맞다.**

이유:

- Stage3는 replay-collapse 대응에는 적합하다.
- 하지만 upstream에서 `must_focus`, `hud`, `deal_type`, `arena` 해석이 profile-aware하게 좁혀지지 않으면, Stage3는 그저 “다르게 보이는 잘못된 surface”를 더 잘 만들 뿐이다.
- 현재도 compiled `surface_guidance`가 투자/절차 계열 wording으로 기울 수 있다는 점이 그 증거다. `docs/2026-04-17/stage3-generator-genre-aware-surface-diversification-context.md:72`, `docs/2026-04-17/stage3-generator-genre-aware-surface-diversification-context.md:146`

결론:
`Stage3 only`는 false.

## 5. Recommended Ownership Model

### 5.1 Primary owner

`work_guard + profile_lock`

역할:

- 이 작품이 무엇을 전장으로 삼는지
- 어떤 액션이 `deal_type`인지
- 어떤 failure/payoff/control axis를 갖는지
- 무엇이 generic drift인지

를 작품 단위로 잠근다.

### 5.2 Secondary owner

`profile-aware runtime adapter`

역할:

- `profile_lock`과 `work_guard`를 runtime guard / Writer / Director / HUD interpretation에 전달한다.
- broad genre string만 넘기는 현재 handoff를 `profile-aware handoff`로 바꾼다.

정확히는 “장르 가드 추가”보다 `adapter/bridge layer`가 맞다.

### 5.3 Tertiary owner

`Stage3 profile-aware surface adapter`

역할:

- episode progression / replay reroute / diversification를 profile-aware하게 좁힌다.
- owner는 `BlueprintEnsemble`보다 `BlueprintConstraintCompiler` 쪽이 더 자연스럽다.

이 레이어는 작품 truth의 원천이 아니라, downstream에서 wrong-lane replay를 줄이는 safety net으로 둔다.

## 6. What This Means for `chaebol_allowance_zero`

이 작품에서 “똑똑한 다음 surface”는 보통 아래 계열이지, 추적/잠입/액션이 아니다.

- 누수 감지 / 병목 판독
- 현장 실측 / 증빙 확보
- 표준단가표 / 장부 대조
- 정산 포털 / 구매 코드 / 승인 도장
- 계약 문장 재작성
- 지역 운영사 네트워크 정렬
- 결재선 전환 / 운영권 / 정산권 회수

실제 block 52도 이미 그 축에 있다. `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json:5`, `treatments/preprocess/chaebol_allowance_zero/03_tr_blocks/block_052/candidate.json:7`

따라서 이 작품에서 “현대판타지니까 추적/잠입/액션도 되지 않나”는 broad family 차원의 오해에 가깝다. 이 작품은 modern-fantasy umbrella 안에서도 `support-system cashflow + business_growth + office_power`로 읽어야 한다.

## 7. Recommended Next Order

구현 우선순위는 아래가 가장 낫다.

1. `profile_lock/work_guard`의 작품 truth를 runtime에서 소비할 수 있게 `profile-aware adapter` 설계
2. Writer / Director / guard construction / HUD interpretation handoff를 broad genre only에서 profile-aware handoff로 보정
3. Stage3 `BlueprintConstraintCompiler`에 `profile-aware surface-family adapter` 추가
4. 마지막에 validator replay semantics를 profile-aware하게 정교화

하지 말 것:

- broad modern-fantasy guard를 하나 더 크게 키우기
- `InvestmentGuard`에 케이스를 계속 덧붙여 범용화하려 하기
- Stage3만으로 작품 truth까지 책임지게 만들기
- validator를 먼저 느슨하게 풀기

## 8. Final Verdict

추천안은 아래와 같다.

- **주 owner:** `work_guard + profile_lock`
- **실행 owner:** `profile-aware runtime adapter`
- **보조 owner:** `Stage3 profile-aware surface adapter`

즉:

`작품 가드로 truth를 잠그고 -> runtime이 그 truth를 profile-aware하게 전달하고 -> Stage3는 그 truth를 벗어난 wrong-lane replay만 막는 구조`

이게 지금 질문에 가장 똑똑한 방향이다.
