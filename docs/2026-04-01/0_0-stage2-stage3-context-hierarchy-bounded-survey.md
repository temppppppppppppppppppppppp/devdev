Date: 2026-04-01
Status: final (3-pass audited)
Confidence: 96%
Canonical Path: `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
Scope: `0_0` Stage2/Stage3 context hierarchy audit
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `0_0 runtime logs/db/artifacts active; Stage2/3 remediation code already landed; temp roadmap mirror dirty; user log file 0_temp.txt dirty`

# 0_0 Stage2/3 Context Hierarchy Bounded Survey

## Answer-First

결론부터 말하면, `Stage2와 Stage3 컨텍스트는 완전 마구잡이는 아니다`. 둘 다 hierarchy를 만들려는 구조는 있다. 하지만 `Stage2는 hierarchy intent 대비 flattening이 심하고`, `Stage3는 Stage2보다 훨씬 계층적이지만 여전히 bulk context와 consumer-specific formatter 때문에 완전히 정규화된 계층 구조라고 보긴 어렵다`.

한 줄 판정:

- `Stage2`: `partially hierarchical, operationally flattened`
- `Stage3`: `hierarchical by design, but still mixed by payload mass and duplicated formatters`

가장 중요한 실물 근거는 `Arc2/EP5`다. `Stage2 arc_002`의 구조화 필드(`constraint_summary`, `episode_details`, `semantic_carryover`)는 얕고 좁은데, 실제 의미는 대부분 `tactical_doc` 장문에 실려 있다. 그 결과 Stage3 original `blueprint_0005`는 Stage2 tactical authority에 없는 `불량배 난입/물리 위협` subplot을 발명했다. 즉 `Stage2 -> Stage3` handoff가 충분히 계층적으로 lock되지 않았다는 뜻이다.

## Hard Conclusions

### 1. Stage2는 상위 레이어를 만들지만, 실제 prompt 표면은 평평해진다

`Stage2`는 제약을 아예 안 세우는 구조가 아니다. 생성 직전 `full_constraint_block`를 따로 만들고, prompt 최상단에도 `prohibition_summary`를 둔다. 근거는 `four_phase_arc_runtime.py:718-737`, `arc_ensemble.py:972-1045`, `config/prompts/ensemble.yaml:16-20`, `config/prompts/ensemble.yaml:37-55`다.

하지만 flattening이 강하다.

- `full_constraint_block` 자체가 `preflight`, `hard constraints`, `negative examples`, `self-check`를 한 문자열로 이어 붙인다. `modules/domain/agents/four_phase_arc_runtime.py:718-737`
- `prev_arc_context`는 `carryover -> execution -> quality -> advisory` 순으로 쌓이지만, 마지막 advisory 섹션에서 이전 Arc 전술서 전문을 최대 `ContextLimits.MAX_CONTEXT_CHARS`까지 붙인다. `modules/domain/agents/four_phase_arc_generator.py:1225-1236`, `modules/domain/agents/four_phase_arc_generator.py:1508-1604`
- `curr_block`는 별도 구조화 packet이 아니라 raw JSON dump로 prompt에 주입된다. `modules/domain/agents/arc_ensemble.py:1011-1045`

즉 `Stage2`는 "순서"는 있으나, 실제 컨텍스트 체감은 `강한 상위 규칙 + 매우 큰 혼합 payload` 구조다.

### 2. Stage3는 Stage2보다 명시적으로 계층적이다

`Stage3`는 `constraint_block`를 구조화 dict로 만든 뒤, consumer가 이를 밴드별로 재구성한다.

- compiler는 `must_focus`, `stop_line`, `continuity`, `inherited_state`, `arc_constraint_summary`, `state_changes_summary`, `semantic_carryover`, `immutable_fact_carryover`, `fact_lock_packet`, `capital_continuity_packet`를 별도 필드로 구성한다. `modules/domain/agents/blueprint_constraint_compiler.py:44-136`
- runtime은 이 `constraint_block`를 generation과 validation 양쪽에 공통 전달한다. `modules/domain/agents/three_phase_blueprint_runtime.py:247-286`, `modules/domain/agents/three_phase_blueprint_runtime.py:1444-1516`
- actual generator consumer인 `BlueprintEnsemble._format_constraints()`는 `IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY`를 명시적으로 선언한다. `modules/domain/agents/blueprint_ensemble.py:898-1091`
- prompt 최상단도 `Stage3 장면 권위 계약`, `안티 HUD`, `안티 크로스 장르 오염`을 먼저 박는다. `config/prompts/ensemble.yaml:267-282`

따라서 `Stage3`는 최소한 generator-facing surface에서는 `hierarchy-aware`다.

### 3. 그래도 Stage3가 완전히 정규화된 계층 구조는 아니다

명시적 hierarchy가 있어도, 운영상은 아직 섞이는 부분이 남아 있다.

- `BlueprintConstraintCompiler.compile_to_prompt()`는 예쁘게 순서를 세운 formatter지만 실제 live consumer가 아니다. repo 내 호출이 없다. 실제 generation path는 `BlueprintEnsemble._format_constraints()`를 사용한다. `modules/domain/agents/blueprint_constraint_compiler.py:138-275`, `modules/domain/agents/blueprint_ensemble.py:301-325`
- Stage3 prompt order는 `arc_focus -> constraints -> strategy_directive -> prev_info -> hud_context`다. 즉 "이번 화 미션"이 hard constraints보다 먼저 온다. `modules/domain/agents/blueprint_ensemble.py:692-760`, `config/prompts/ensemble.yaml:294-306`
- `prev_info_expanded`는 직전 blueprint 요약 외에도 `이전 blueprint 전문` 최대 400K, `직전 원고 말미`, `이전 원고 전문` 최대 400K를 붙인다. 우선순위 설명은 있지만, payload mass 자체는 hierarchy를 희석시킬 수 있다. `modules/domain/agents/blueprint_ensemble.py:1362-1414`
- `_prepare_blueprint_ensemble_context()`의 캐시용 `shared_context`도 `arc_focus + constraints + prev_info + hud_context`의 단순 연결이다. `modules/domain/agents/blueprint_ensemble.py:301-325`

즉 `Stage3`는 내부 규칙은 계층적이지만, context packaging 자체는 여전히 `large mixed packet`에 가깝다.

### 4. 실물 artifact는 Stage2 structured contract가 아직 약하다는 쪽을 지지한다

`projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json` 기준:

- `constraint_summary`는 사실상 `아이템 재획득 금지` 중심의 좁은 문자열이다. `...final_arc__balanced.json:79`
- `semantic_carryover`는 비어 있다. `...final_arc__balanced.json:136`
- `episode_details`는 화당 1문장 수준의 얇은 사건 요약이다. `...final_arc__balanced.json:83-114`
- 반면 핵심 의미와 전술 디테일은 대부분 `tactical_doc` 장문에만 있다. `projects/0_0/plans/arcs/arc_002.txt`

이 상태에서 original Stage3 `blueprint_0005`는 `불량배 난입`, `쇠파이프`, `물리 제압`을 만들어냈다. `projects/0_0/plans/blueprints/blueprint_0005.txt`

즉 실제 handoff는

- `Stage2 structured fields`가 충분히 authoritative하게 잠기지 않고
- `Stage3`가 tactical prose를 semantic하게 재해석하는 비중이 크며
- 그 해석 여지 때문에 off-arc invention이 가능해졌던 구조다

라는 쪽이 더 정확하다.

## Pass 1 Inventory

### Stage2 context assembly

- constraint envelope assembly: `modules/domain/agents/four_phase_arc_runtime.py:718-737`
- previous-arc context assembly root: `modules/domain/agents/four_phase_arc_generator.py:1225-1236`
- carryover block: `modules/domain/agents/four_phase_arc_generator.py:1239-1290`
- execution-truth block: `modules/domain/agents/four_phase_arc_generator.py:1292-1392`
- quality/advisory/history block: `modules/domain/agents/four_phase_arc_generator.py:1394-1604`
- prompt bundle assembly: `modules/domain/agents/arc_ensemble.py:906-970`, `modules/domain/agents/arc_ensemble.py:972-1045`
- prompt template: `config/prompts/ensemble.yaml:4-60`

### Stage3 context assembly

- constraint block compile: `modules/domain/agents/blueprint_constraint_compiler.py:44-136`
- runtime constraint resolution: `modules/domain/agents/three_phase_blueprint_runtime.py:247-286`
- prompt context assembly: `modules/domain/agents/blueprint_ensemble.py:301-325`
- actual prompt bundle assembly: `modules/domain/agents/blueprint_ensemble.py:692-760`
- actual banded constraint formatter: `modules/domain/agents/blueprint_ensemble.py:898-1091`
- previous-info expansion: `modules/domain/agents/blueprint_ensemble.py:1097-1414`
- validation-side hierarchy enforcement: `modules/domain/agents/unified_blueprint_validator.py:972-1057`, `modules/domain/agents/unified_blueprint_validator.py:1707-1765`
- prompt template: `config/prompts/ensemble.yaml:264-433`

### Artifact truth checked

- `projects/0_0/plans/arcs/arc_002.txt`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/0_0/plans/blueprints/blueprint_0005.txt`

## Pass 2 Semantic Classification

### Stage2

- `top-level intent`: hierarchical
- `runtime packaging`: mixed
- `dominant weakness`: large prose and advisory mass overwhelms structured authority
- `net verdict`: not random, but not cleanly hierarchical enough

### Stage3

- `top-level intent`: clearly hierarchical
- `runtime packaging`: mixed but better controlled than Stage2
- `dominant weakness`: duplicated formatters and huge previous-text payloads
- `net verdict`: hierarchy exists and is usable, but not fully canonicalized

## Pass 3 Operational Meaning

이 질문을 `Stage4 readiness` 관점에서 해석하면 다음과 같다.

1. `Stage2`만 믿고 보면 아직 부족하다.
   structured authority보다 `tactical_doc 장문` 의존이 크다.

2. `Stage3`는 hierarchy를 보강하는 역할을 실제로 수행한다.
   특히 `constraint_block`, banded constraints, validator binding이 그 역할이다.

3. 하지만 `Stage3`가 Stage2의 약한 구조를 완전히 상쇄하진 못한다.
   그래서 `EP5 intrusion` 같은 semantic drift가 발생했다.

4. 따라서 `Stage2/3는 완전 마구잡이`라는 진단은 과장이다.
   더 정확한 진단은 `Stage2는 구조가 약하고, Stage3가 이를 보정하지만 payload mass와 duplicated consumers 때문에 아직 완전한 계층 구조로 수렴하지 못했다`이다.

## Recommended Reading Of The Result

- `Stage2 context는 계층적이냐?`
  - `부분적으로만 예`
- `Stage3 context는 계층적이냐?`
  - `상당 부분 예`
- `둘을 합치면 Stage4를 안정적으로 받을 정도로 계층적이냐?`
  - `이전보다 좋아졌지만, 아직 parent lane closure를 바로 선언할 정도로 깔끔한 single-authority stack은 아님`

## Non-Goals

- 이번 문서는 `새 execution SSOT`를 만들지 않는다.
- 이번 문서는 `Stage4 재개`를 승인하지 않는다.
- 이번 문서는 `Stage2/3 전체가 실패`라고 과장하지 않는다.

## Final Verdict

`Stage2/3 컨텍스트는 무질서하게 뒤섞인 시스템은 아니다.`

하지만 현재 형태는:

- `Stage2`: hierarchy를 표방하지만 structured authority보다 긴 prose와 mixed advisory 비중이 더 큰 상태
- `Stage3`: hierarchy를 실제로 쓰지만, large previous-text packet과 formatter duplication 때문에 완전한 canonical stack은 아닌 상태

즉 operator 관점의 최종 판정은:

`hierarchical by intent, partially flattened in operation`
