# Stage 4 Context Contract Full Survey 3-Pass Audit
작성일: 2026-03-12  
상태: final  
가정: `Stage 4 canary 성공`을 전제로 한 정적 감사다. 실행 로그 재판독은 이번 문서 범위에 포함하지 않는다.  
금지사항 준수: 코드 수정 없음, 테스트 실행 없음, 문서화만 수행.

## Executive Summary

이번 감리의 핵심 결론은 세 가지다.

1. `CW`와 `Director`는 같은 상위 목표를 공유한다. 다만 같은 프롬프트를 받는 구조가 아니라, 같은 작품 계약을 서로 다른 역할용 컨텍스트로 받는다.
2. `CW`는 `master_bible + mandatory_context + directive + history` 중심의 생성 컨텍스트를 받고, `Director`는 `story_context + blueprint + episode_digest + prev_manuscripts + advisory-augmented mandatory_context` 중심의 판정 컨텍스트를 받는다.
3. retained finding은 2건이다.
   - `P2`: `PASS_WITH_FIX`의 `inplace patch` 루프가 `fix_scope_reasoning`과 `open_review`를 충분히 보존하지 못한 채 `action_items` 중심으로만 축약된다.
   - `P2`: `Stage 4` 재감리 루프는 `Stage 2`와 달리 누적 패치 이력을 `story_context`에 주입하지 않는다.

최종 확신도는 `95%`다. 이 값은 정적 코드/프롬프트/읽기 전용 테스트 근거로 방어 가능한 상한이며, live prompt body 재현성까지는 닫지 못했다.

## 조사 범위 / 금지사항

- 포함:
  - Stage 4 오케스트레이션/컨텍스트 조립
  - `ChiefWriter`, `Director`, advisory sidecar LLM 경로
  - 관련 프롬프트
  - 읽기 전용 테스트
  - 모델 라우팅 SSOT
- 제외:
  - 실제 canary 로그 재판독
  - 코드 수정
  - 테스트 실행
  - full/live rerun

## 조사 대상

- 오케스트레이션/컨텍스트
  - [stage4_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
  - [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py)
  - [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
  - [stage4_types.py](C:/Users/User/Desktop/글도비/modules/core/stage4_types.py)
- 에이전트/프롬프트
  - [chief_writer.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py)
  - [chief_writer_context.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py)
  - [director.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director.py)
  - [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
  - [director_prompts.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_prompts.py)
  - [director.yaml](C:/Users/User/Desktop/글도비/config/prompts/director.yaml)
  - [truth_gate.py](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py)
- 라우팅/모델
  - [models.yaml](C:/Users/User/Desktop/글도비/config/models.yaml)
  - [base_agent.py](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py)
  - [llm_router.py](C:/Users/User/Desktop/글도비/modules/core/llm_router.py)
- 읽기 전용 테스트
  - [test_stage4_interview_round.py](C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py)
  - [test_stage4_context_builder.py](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py)
  - [test_pass_with_fix.py](C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py)
  - [test_a2_open_review_cw.py](C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py)
  - [test_chief_writer.py](C:/Users/User/Desktop/글도비/tests/test_chief_writer.py)
  - [test_truth_gate.py](C:/Users/User/Desktop/글도비/tests/test_truth_gate.py)
  - [test_work_identity_director_prompt.py](C:/Users/User/Desktop/글도비/tests/test_work_identity_director_prompt.py)

## Pass 1. 사실 수집

### 1. 주요 LLM/에이전트 지도

| 주체 | 모델/라우팅 | 실제 역할 | 핵심 입력 |
|---|---|---|---|
| `ChiefWriter` | `gemini-2.5-pro` via `BaseAgent -> LLMProviderRouter` | 원고 생성 | `common_context`, 전략별 instruction, director feedback |
| `Director` | `gemini-2.5-pro` via `BaseAgent -> LLMProviderRouter` | 후보 비교, 판정, `PASS_WITH_FIX` 지시 | `stable_context + variable_prompt + mandatory_context` |
| `TruthGate` 등 advisory sidecar | 별도 모델 SSOT 없음. `_truth_gate_llm_ask()`가 `director.ask()`를 저온으로 호출 | 사실 검증/드리프트 advisory | 축약된 검사용 prompt |

근거:

- [models.yaml#L28](C:/Users/User/Desktop/글도비/config/models.yaml#L28), [models.yaml#L37](C:/Users/User/Desktop/글도비/config/models.yaml#L37)
- [base_agent.py#L104](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py#L104), [base_agent.py#L284](C:/Users/User/Desktop/글도비/modules/domain/agents/base_agent.py#L284)
- [llm_router.py#L66](C:/Users/User/Desktop/글도비/modules/core/llm_router.py#L66)
- [stage4_interview_round.py#L88](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L88)

해석:

- 현재 활성 provider는 사실상 `gemini`뿐이다. `anthropic/openai/vertex_ai`는 `config/models.yaml`상 disabled다.
- 따라서 이번 Stage 4의 “주요 LLM 간 provider 차이”는 현재 설정에서는 거의 휴면 상태다.

### 2. Stage 4 공통 handoff 객체

`_RoundContext`는 Stage 4의 공통 handoff 계약이다.

- `story_context`
- `reference_anchor_prompt`
- `mandatory_context`
- `justification_prompt`
- `reflexion_prompt`
- `preflight_advisory`
- `prev_manuscripts_text`
- `world_state_summary`

근거:

- [stage4_types.py#L52](C:/Users/User/Desktop/글도비/modules/core/stage4_types.py#L52)
- [stage4_context_builder.py#L2528](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2528)

### 3. `story_context`는 어디서 오고 누구에게 가는가

`story_context`는 Stage 4 session 준비 시 오케스트레이터가 조립한다.

- 장르
- 주인공 이름
- 세계 출신
- 환생/빙의/회귀 타입
- core traits

근거:

- [stage4_orchestrator.py#L1356](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1356)

중요한 사실:

- 이 `story_context`는 [stage4_interview_round.py#L1488](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1488)에서 `Director`에게 직접 전달된다.
- 반면 `CW`는 `story_context` 문자열을 직접 받지 않는다.

### 4. `CW`는 실제로 무엇을 받는가

`ChiefWriter.generate_ensemble()`는 별도 `common_context`를 조립한다.

근거:

- [chief_writer.py#L370](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L370)
- [chief_writer.py#L638](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L638)

`common_context`의 구성 요소:

- `master_bible` 기반 핵심 정체성/주인공 설정
- `world_origin`, `incarnation_type`별 지시
- `director_feedback`
- 실패 제약
- `WritingDirective`
- `character_voice`
- `reference_anchor_prompt`
- `mandatory_context`
- `anti_trope`, `justification`, `reflexion`
- `world_state_summary`
- `prev_manuscripts_text`
- `HUD/NPC equipment` 요약

근거:

- [chief_writer_context.py#L176](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L176)
- [chief_writer_context.py#L244](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L244)
- [chief_writer_context.py#L304](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L304)
- [chief_writer_context.py#L378](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L378)
- [chief_writer_context.py#L456](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L456)

정리:

- `CW`는 `story_context` literal은 직접 받지 않지만, 같은 성격의 설정 정보를 `master_bible` 기반 조립 경로로 받는다.
- 따라서 “CW가 작품 정체성 입력을 못 받는다”는 주장은 사실이 아니다.

### 5. `mandatory_context`는 어떻게 만들어지는가

`Stage4ContextBuilder.build_mandatory_context()`는 `mandatory_context`에 아래 계열의 블록을 합친다.

- writer mandatory context
- work identity slot summary
- condensed world state / fact ledger / timeline
- canonical constraints
- `Treatment genre_ext`
- continuity packet
- NPC boundary block
- state tracker summaries
- retrieval/vector memory
- extended lookback
- foreshadow / semantic plot guard / pacing / narrative summary

근거:

- [stage4_context_builder.py#L2019](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2019)
- [stage4_context_builder.py#L2095](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2095)
- [stage4_context_builder.py#L2316](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2316)
- [stage4_context_builder.py#L2462](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2462)

추가로 work identity 계열은 별도 보호 장치가 있다.

- tracking slots
- mandatory scene engines
- registry profiles
- relation slice
- coverage warnings

근거:

- [stage4_context_builder.py#L820](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L820)
- [stage4_context_builder.py#L2466](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2466)
- [test_stage4_context_builder.py#L752](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L752)
- [test_stage4_context_builder.py#L814](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L814)
- [test_stage4_context_builder.py#L848](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L848)

### 6. `Director`는 실제로 무엇을 받는가

`DirectorEnsembleSelector`는 `stable_context`와 `variable_prompt`를 분리해 쓴다.

- stable:
  - `story_context`
  - `blueprint`
  - `episode_digest`
  - `previous_ending`
  - `prev_manuscripts_text`
- variable:
  - 후보 A/B/C 원고
  - 후보별 Python warnings
- extra:
  - advisory가 누적된 `mandatory_context`

근거:

- [director_ensemble.py#L752](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L752)
- [director_ensemble.py#L779](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L779)
- [director.yaml#L8](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L8)
- [director.yaml#L35](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L35)

추가 사실:

- `Director`의 `mandatory_context`는 원래 `mandatory_context`에:
  - WritingDirective summary
  - POV block
  - TruthGate/NpcDrift/NumericDrift 등 advisory
  - timeline / scene similarity / diversity / preflight
  - candidate별 Python warning
  - DB-derived advisory
  - work review advisory
  를 누적한 값이다.

근거:

- [stage4_interview_round.py#L1255](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1255)
- [stage4_interview_round.py#L1486](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1486)
- [test_stage4_interview_round.py#L390](C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L390)

### 7. advisory LLM은 본심을 대체하는가

아니다.

- `TruthGate`는 `blocking=False`인 advisory validator다.
- `stage4_interview_round._truth_gate_llm_ask()`는 `director.ask()`를 저온으로 호출해 world-law 점검에만 쓴다.
- `director.yaml`은 advisory를 참고자료로 취급하고, `CRITICAL TruthGate`만 자동 reject 사유로 둔다.

근거:

- [truth_gate.py#L16](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py#L16)
- [truth_gate.py#L24](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py#L24)
- [stage4_interview_round.py#L88](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L88)
- [stage4_interview_round.py#L3425](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3425)
- [director.yaml#L165](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L165)

## Pass 2. 교차 검증

### 1. `CW`와 `Director`는 같은 목적을 향하는가

판정: `확인함`

- `Director` 프롬프트는 상위 철학을 “Blueprint를 토대로 양질의 원고를 연속성 있게 생산”으로 둔다.
- `CW`는 같은 blueprint/history/directive 기반으로 원고를 생성한다.
- `WritingDirective`는 두 경로 모두에 주입된다.
- `Director.open_review`는 full regenerate 경로에서 다시 `CW`에게 명시 전달된다.

근거:

- [director.yaml#L8](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L8)
- [chief_writer_context.py#L313](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L313)
- [stage4_interview_round.py#L1276](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1276)
- [chief_writer.py#L851](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L851)
- [test_a2_open_review_cw.py#L24](C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py#L24)

결론:

- 둘은 “같은 상위 품질 계약 + 다른 역할”이다.
- `CW = 생성 최적화`, `Director = 판정/교정 최적화`다.

### 2. `CW`와 `Director`가 같은 자료를 보는가

판정: `부분적으로 확인함`

확인된 공통점:

- 동일 `blueprint`
- 동일 `prev_manuscripts_text`
- 동일 `mandatory_context`의 기저 본문
- 동일 `episode_digest`
- 동일 project/master_bible 기반 설정

차이점:

- `CW`는 `common_context`를 별도로 조립한다.
- `Director`는 `story_context`와 advisory-augmented `mandatory_context`를 받는다.

이 차이는 drift가 아니라 설계상 역할 분리다.

근거:

- [chief_writer.py#L370](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L370)
- [director_ensemble.py#L752](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L752)
- [stage4_interview_round.py#L1488](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1488)

### 3. work identity / relation context는 실제로 살아남는가

판정: `확인함`

- `Stage4ContextBuilder`는 work slot summary와 relation slice를 만들고,
- coverage warning과 observation 메타를 남기며,
- 테스트가 예산 하에서도 보호 보존을 검증한다.

근거:

- [stage4_context_builder.py#L2097](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2097)
- [stage4_context_builder.py#L2479](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2479)
- [director.yaml#L113](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L113)
- [test_stage4_context_builder.py#L752](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L752)
- [test_work_identity_director_prompt.py#L4](C:/Users/User/Desktop/글도비/tests/test_work_identity_director_prompt.py#L4)

### 4. retry/patch 과정에서 컨텍스트가 좁아지는가

판정: `확인함`

full regenerate 경로:

- `ChiefWriter.regenerate_with_feedback()`는
  - score breakdown
  - validation warnings
  - `fix_scope_reasoning`
  - `open_review`
  - prior attempt history
  를 `enhanced_feedback`에 넣는다.

근거:

- [chief_writer.py#L853](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L853)
- [chief_writer.py#L876](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L876)
- [chief_writer.py#L880](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L880)

local patch 경로:

- `Stage4InterviewRound._extract_fix_feedback()`는
  - `action_items`
  - 없으면 `feedback.issues`
  만 사용한다.

근거:

- [stage4_interview_round.py#L3816](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3816)

추가 교차 근거:

- `DirectorEnsembleSelector`는 `open_review`를 `feedback.issues`에 붙여 보존하려고 한다.
- 하지만 `_extract_fix_feedback()`는 `action_items`가 있으면 즉시 반환하므로, 이 경우 `open_review`는 patch feedback에서 탈락할 수 있다.

근거:

- [director_ensemble.py#L1128](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1128)

## Pass 3. 감리 / 오탐 제거

### Retained Findings

#### P2. `PASS_WITH_FIX` local patch 루프가 Director 피드백을 과도 축약한다

상태: `확인함`

깨진 계약:

- full regenerate 경로는 `fix_scope_reasoning`과 `open_review`까지 `CW`에게 전달한다.
- 그러나 `PASS_WITH_FIX -> inplace patch` 경로는 `_extract_fix_feedback()`로 `action_items` 우선 축약을 수행한다.

직접 근거:

- [chief_writer.py#L876](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L876)
- [chief_writer.py#L880](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L880)
- [stage4_interview_round.py#L3816](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3816)
- [director_ensemble.py#L1128](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1128)

반대 근거 검토:

- `Director` 재감리 루프가 다시 돈다.
- `open_review`는 previous_attempt에는 보존된다.
- full retry 경로에서는 open_review 전달이 테스트로 보장된다.

왜 오탐이 아닌가:

- 문제는 “최종적으로 완전히 유실되느냐”가 아니라 “local patch 시점의 입력이 좁아지느냐”다.
- 해당 시점의 입력 축약은 코드 레벨로 확인된다.

영향:

- `work identity drift`, `AI smell`, 정서선 급변처럼 `open_review`에 실리기 쉬운 항목이 local patch 시점에 약화될 수 있다.
- 결과적으로 같은 문제를 다시 `Director`가 재지적하는 루프 비용이 늘 수 있다.

canary blocker 여부:

- `아니오`

문서/코드 불일치 여부:

- `부분적 예`
  - full regenerate 경로가 더 풍부한 피드백을 보존하는 반면, local patch 경로는 같은 수준을 보장하지 않는다.

런타임 검증 없이는 더 못 올리는지:

- `아니오`
  - 정적 코드 근거로 충분히 확인된다.

#### P2. `Stage 4` 재감리 루프는 누적 패치 이력을 `story_context`에 주입하지 않는다

상태: `확인함`

깨진 계약:

- `Stage 2`는 `PASS_WITH_FIX` 재감리 시 `[이미 적용된 패치]`를 `story_context`에 붙여 재심사한다.
- `Stage 4`는 재감리 시 패치된 원고만 넘기고, `story_context`는 원본 그대로 재사용한다.

직접 근거:

- [stage2_finalizer.py#L743](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L743)
- [stage2_finalizer.py#L762](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L762)
- [stage4_interview_round.py#L2420](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2420)
- [stage4_interview_round.py#L2432](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2432)
- [test_pass_with_fix.py#L740](C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py#L740)

반대 근거 검토:

- Stage 4는 `patch_trace`를 별도로 기록한다.
- `state_updates` merge도 테스트로 보장된다.

왜 오탐이 아닌가:

- 비교 대상 Stage 2에 동일 문제를 막는 패턴이 실제 존재한다.
- Stage 4 재감리 호출은 `story_context=round_ctx.story_context` 그대로다.

영향:

- 반복 patch 루프에서 `Director`가 이전에 이미 적용된 수정의 provenance를 직접 문맥으로 보지 못한다.
- 동일 이슈의 재지적 또는 patch lineage 해석 비용 증가 가능성이 있다.

canary blocker 여부:

- `아니오`

문서/코드 불일치 여부:

- `예`
  - cross-stage parity 관점에서 Stage 4가 더 약하다.

런타임 검증 없이는 더 못 올리는지:

- `아니오`

### Observations

#### O1. exact prompt-body replayability는 낮다

상태: `확인함`

- `ChiefWriter`는 `common_context`를 캐시에 올리지만, 본문 전체를 runtime audit summary에 남기지 않는다.
- `AuditService.write_audit_summary()`는 count/recent events 중심이다.
- `Stage4ContextBuilder`는 retrieval observation 메타는 남기지만 final body text 전체를 영속화하지 않는다.

근거:

- [chief_writer.py#L411](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L411)
- [audit_service.py#L72](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py#L72)
- [stage4_context_builder.py#L2479](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2479)

판정:

- 실질 이슈는 맞지만, 이번 감사에서는 품질 계약 위반보다 `사후 재현성/디버깅 품질` 이슈에 가깝다.
- 따라서 `Observation`으로 둔다.

### Rejected Hypotheses

#### R1. `CW`와 `Director`는 서로 다른 상위 목표를 가진다

기각 사유:

- 상위 목표는 공유한다.
- 역할이 다를 뿐이다.

근거:

- [director.yaml#L8](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L8)
- [chief_writer.py#L370](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L370)

#### R2. `CW`는 `story_context`를 직접 안 받으므로 작품 설정을 못 받는다

기각 사유:

- `CW`는 `master_bible` 기반으로 protagonist/world_origin/incarnation_type/genre guard를 직접 조립한다.

근거:

- [chief_writer_context.py#L176](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L176)
- [chief_writer_context.py#L211](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L211)

#### R3. work identity drift는 Director prompt에 반영되지 않는다

기각 사유:

- prompt와 builder와 테스트가 모두 존재한다.

근거:

- [director.yaml#L113](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L113)
- [stage4_context_builder.py#L2097](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2097)
- [test_work_identity_director_prompt.py#L4](C:/Users/User/Desktop/글도비/tests/test_work_identity_director_prompt.py#L4)

#### R4. advisory LLM이 본심을 대체한다

기각 사유:

- advisory는 참고자료로 설계되어 있고, 코드상 `TruthGate`도 advisory-only다.

근거:

- [truth_gate.py#L24](C:/Users/User/Desktop/글도비/modules/core/truth_gate.py#L24)
- [director.yaml#L165](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L165)

## Confidence Ledger

- `70` 전수 인벤토리 완료
- `+10` 코드/프롬프트/읽기 전용 테스트 3계층 교차 근거 확보
- `+10` `CW ↔ Director ↔ advisory` handoff와 목표 정렬성 확인
- `+5` work identity / relation slice / budget protection까지 교차 검증
- `+5` false positive 4건 기각 완료
- `-5` live prompt body replay와 active canary 산출물 재판독 미포함

최종 확신도: `95%`

해석:

- 이번 문서는 “Stage 4 context contract를 정적으로 어디까지 닫을 수 있는가” 기준의 `95%`다.
- `100%`로 올리려면 live run에서 실제 prompt/body lineage를 재구성하는 별도 증거가 필요하다.

## Evidence Index

| ID | claim | evidence |
|---|---|---|
| E-01 | `_RoundContext`가 Stage 4 handoff 계약이다 | [stage4_types.py#L52](C:/Users/User/Desktop/글도비/modules/core/stage4_types.py#L52), [stage4_context_builder.py#L2528](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2528) |
| E-02 | `story_context`는 orchestrator가 조립하고 Director에 직접 간다 | [stage4_orchestrator.py#L1356](C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1356), [stage4_interview_round.py#L1488](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1488) |
| E-03 | `CW`는 `common_context`를 별도로 조립한다 | [chief_writer.py#L370](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L370), [chief_writer_context.py#L176](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context.py#L176) |
| E-04 | `mandatory_context`는 work identity / retrieval / canonical blocks를 포함한다 | [stage4_context_builder.py#L2019](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2019), [stage4_context_builder.py#L2466](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L2466) |
| E-05 | `Director`는 stable/variable prompt split을 사용한다 | [director_ensemble.py#L752](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L752), [director.yaml#L8](C:/Users/User/Desktop/글도비/config/prompts/director.yaml#L8) |
| E-06 | advisory LLM은 Director 저온 호출을 sidecar로 사용한다 | [stage4_interview_round.py#L88](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L88), [stage4_interview_round.py#L3425](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3425) |
| E-07 | open_review는 full regenerate에서 CW로 전달된다 | [chief_writer.py#L880](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L880), [test_a2_open_review_cw.py#L24](C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py#L24) |
| E-08 | patch loop는 `_extract_fix_feedback()`로 피드백을 축약한다 | [stage4_interview_round.py#L3816](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3816), [director_ensemble.py#L1128](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1128) |
| E-09 | Stage 2는 patch history를 story_context에 넣지만 Stage 4는 넣지 않는다 | [stage2_finalizer.py#L743](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L743), [stage4_interview_round.py#L2420](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2420) |
| E-10 | work identity / relation slice는 테스트로 보호된다 | [test_stage4_context_builder.py#L752](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L752), [test_stage4_context_builder.py#L848](C:/Users/User/Desktop/글도비/tests/test_stage4_context_builder.py#L848), [test_work_identity_director_prompt.py#L4](C:/Users/User/Desktop/글도비/tests/test_work_identity_director_prompt.py#L4) |
| E-11 | active provider 차이는 현재 설정상 작다 | [models.yaml#L1](C:/Users/User/Desktop/글도비/config/models.yaml#L1), [llm_router.py#L66](C:/Users/User/Desktop/글도비/modules/core/llm_router.py#L66) |
| E-12 | runtime audit는 body보다 메타 중심이다 | [audit_service.py#L72](C:/Users/User/Desktop/글도비/modules/core/services/audit_service.py#L72), [chief_writer.py#L411](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L411) |

## Final Verdict

- `CW`와 `Director`는 같은 목적을 향해 있다. 다만 같은 prompt를 받는 구조가 아니라, 같은 작품 계약을 역할별로 다르게 소화하는 구조다.
- 이번 감사에서 실제 retained context-contract 문제는 `PASS_WITH_FIX local patch feedback 축약`과 `Stage 4 patch provenance story_context 미주입` 두 건이다.
- 그 외 `story_context 비대칭`, `work identity 미감리`, `advisory 전권화`는 근거상 기각된다.
