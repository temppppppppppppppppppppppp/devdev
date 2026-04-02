# 글도비 기술 기법 인벤토리 및 개발자 Q&A 메모

Date: 2026-04-02
Status: final
Audience: 발표자 / 비개발 실무자 / 개발자 질의 대비
Confidence: 0.96

## 1. 목적

이 문서는 글도비에서 실제로 쓰이는 기술 기법을 `문서상 표현`과 `실제 런타임 배선` 기준으로 구분해 정리한 메모다.

핵심 목적은 세 가지다.

1. 발표 중 기술 용어를 과장 없이 설명한다.
2. 개발자가 찌를 만한 지점을 미리 안다.
3. `항상 켜진 핵심 구조`와 `조건부 보조 기법`을 분리해서 말한다.

---

## 2. 한 줄 요약

글도비는 `단일 RAG`나 `프롬프트 한 방` 구조가 아니라, `Stage별 앙상블 + Director 판정 + 상태 저장소(WorldState/FactLedger) + Smart Retrieval + Advisory Chain + PASS_WITH_FIX patch loop`로 운영되는 장편 생산 파이프라인이다.

정확히 말하면:

- 주 구조: 앙상블, Director 판정, 상태 저장소, retrieval, advisory chain, patch/retry
- 보조 강화: Self-Reflection, Retrospective, Reflexion, ToT, MAD, Adversarial Self-Play, CoVe
- 품질 신호: CED, AI Slop, style-target drift, open_review

---

## 3. 실제로 쓰이는 핵심 구조

### 3.1 앙상블

글도비는 Stage 2, 3, 4 모두에서 후보를 여러 개 생성하고 Director가 선택하는 구조를 사용한다.

- Stage 2 Arc 앙상블: `modules/domain/agents/arc_ensemble.py`
- Stage 3 Blueprint 앙상블: `modules/domain/agents/blueprint_ensemble.py`
- Stage 4 Chief Writer 앙상블: `modules/domain/agents/chief_writer.py`
- 관련 설명: `docs/poc/why_this_system.md`

안전한 설명:

`각 단계는 단일 초안 1개를 바로 확정하지 않고, 후보를 병렬 생성한 뒤 Director가 비교 선택하는 구조다.`

근거:

- `docs/poc/why_this_system.md:108`
- `modules/domain/agents/arc_ensemble.py:409`
- `modules/domain/agents/blueprint_ensemble.py:531`
- `modules/domain/agents/chief_writer.py:627`

### 3.2 Director 판정 및 PASS_WITH_FIX

글도비의 최종 품질 결정권은 Director에 있다. Director는 `PASS / PASS_WITH_FIX / REJECT`를 내리고, 필요하면 `fix_scope=inplace|partial|full`로 수정 범위를 지시한다.

안전한 설명:

`후보 생성과 별개로, 최종 합격 여부와 수정 범위는 Director가 결정한다.`

근거:

- `docs/poc/why_this_system.md:124`
- `modules/domain/agents/director_ensemble.py:1366`
- `modules/domain/agents/director_ensemble.py:1499`
- `modules/core/stage4_retry_runtime.py:86`

### 3.3 상태 저장소: WorldState + FactLedger

장기 기억의 뼈대는 프롬프트 내부가 아니라 바깥 상태 저장소다.

- `WorldState`: 생존/사망, 관계, 아이템, 파괴 엔티티, 플롯, 시간, 세계 법칙
- `FactLedger`: 개체/수치/사실 이력

안전한 설명:

`장기 기억은 RAG만으로 유지하는 게 아니라, 상태 저장소를 SSOT로 두고 retrieval은 보조로 쓴다.`

근거:

- `docs/poc/why_this_system.md:131`
- `docs/poc/why_this_system.md:134`
- `modules/core/world_state.py:121`
- `modules/core/fact_ledger.py:119`

### 3.4 Smart Retrieval / Hybrid Retrieval

retrieval은 Stage별로 `ContextAdvisor`가 슬롯을 계획하고, `VecMemory`가 Dense + FTS5 + RRF 하이브리드 검색을 수행한다.

안전한 설명:

`글도비의 retrieval은 범용 RAG가 아니라, stage-aware slot planning과 hybrid retrieval의 조합이다.`

근거:

- `docs/poc/why_this_system.md:187`
- `docs/poc/why_this_system.md:190`
- `config/settings/validation.yaml:178`
- `config/settings/validation.yaml:192`
- `modules/core/context_advisor.py:348`
- `modules/core/vec_memory.py:637`

### 3.5 7-Stage Advisory Chain

문서상 `7-Stage Advisory Chain`은 실제로는 `TruthGate + 6개 전문 advisory`를 뜻한다.

- TruthGate
- NpcDriftAdvisor
- NumericDriftAdvisor
- FlashbackVerifier
- InfoParadoxChecker
- RelationshipDriftAdvisor
- LongTermRepetitionAdvisor

중요한 점은 대부분 `advisory-only`이고, 최종 block 권한은 Director에게 있다는 점이다.

안전한 설명:

`구조화된 상태 검증과 장기 표류 감지를 advisory chain으로 수행하고, 최종 판정은 Director가 맡는다.`

근거:

- `docs/poc/why_this_system.md:125`
- `docs/poc/why_this_system.md:141`
- `modules/core/truth_gate.py:16`
- `modules/core/npc_drift_advisor.py:63`
- `modules/core/numeric_drift_advisor.py:21`
- `modules/core/flashback_verifier.py:18`
- `modules/core/info_paradox_checker.py:20`
- `modules/core/relationship_drift_advisor.py:20`
- `modules/core/long_term_repetition_advisor.py:41`

---

## 4. 실제로 배선된 추론 강화 기법

### 4.1 Self-Consistency

설정상 활성화되어 있으며, 구현은 `항상 3회`가 아니라 `애매한 점수 구간에서만 추가 투표`하는 조건부 다수결이다.

안전한 설명:

`자기일관성 투표는 항상 3배 호출이 아니라, 경계 점수대에서만 확장되는 조건부 다수결이다.`

근거:

- `config/settings/validation.yaml:164`
- `config/settings/validation.yaml:165`
- `modules/validation/validation_orchestrator.py:946`

### 4.2 Consensus Validator

Stage 2에는 별도의 `Consensus 3-LLM` 검증이 있다. 이는 self-consistency와 완전히 같은 개념은 아니고, Arc 후보에 대한 별도 합의 검증이다.

안전한 설명:

`Stage 2는 self-consistency 외에 Arc용 3-LLM consensus 검증이 한 번 더 있다.`

근거:

- `modules/core/stage2_validation_pipeline.py:358`
- `modules/domain/agents/consensus_validator.py:175`

### 4.3 Self-Reflection

생성 후 자기 비평을 수행하는 모듈이 있다. Stage 2 validation에서 실제 호출된다.

안전한 설명:

`생성 직후 같은 계열의 모델이 자기 비평을 한 번 더 수행하는 self-reflection 경로가 있다.`

근거:

- `modules/core/self_reflection.py:2`
- `modules/core/stage2_validation_pipeline.py:312`

### 4.4 Retrospective

장기 일관성 검증용 retrospective가 설정상 활성화되어 있고, 최근 화를 lookback해 장기 위반을 advisory로 남긴다.

안전한 설명:

`retrospective는 최근 화를 되돌아보며 장기 일관성 위반을 재검토하는 회고형 검증이다.`

근거:

- `config/settings/validation.yaml:158`
- `modules/validation/validation_orchestrator.py:730`

### 4.5 Reflexion

실패 패턴을 저장하고 다음 시도에 반영하는 memory 계열 보조장치다.

안전한 설명:

`reflexion은 실패 패턴을 누적해 다음 시도 프롬프트에 반영하는 보조 메모리다.`

근거:

- `config/settings/validation.yaml:168`
- `modules/core/reflexion_manager.py:2`
- `modules/core/stage4_interview_round.py:1367`

### 4.6 ToT

Tree of Thoughts 모듈은 실제 존재한다. 다만 핵심 메인 루프가 아니라 Stage 4 reject path에서 `structure_error` 버킷일 때 보조적으로 붙는다.

안전한 설명:

`ToT는 주 생산 경로의 기본 엔진이라기보다, 구조 오류 reject에 대한 보조 탐색기다.`

근거:

- `modules/core/tree_of_thoughts.py:2`
- `modules/core/stage4_reject_runtime.py:646`

### 4.7 MAD

Multi-Agent Deliberation도 실제 존재한다. Stage 4 reject path에서 `constraint_violation`일 때 보조적으로 붙는다.

안전한 설명:

`MAD는 항상-on 3자 토론이 아니라, 제약 위반 reject를 다시 풀기 위한 보조 deliberation이다.`

근거:

- `modules/core/multi_agent_deliberation.py:1`
- `modules/core/stage4_reject_runtime.py:663`

### 4.8 Adversarial Self-Play

모듈 자체는 존재하고 adaptive retry에서 `필살기` 후보로 다뤄진다. 다만 메인 런타임의 항상-on 증거보다 `보조 강화기법` 성격이 더 강하다.

안전한 설명:

`ASP는 기본 구조라기보다, 내부 Director 비판을 시뮬레이션하는 추가 강화기법이다.`

근거:

- `modules/core/adversarial_self_play.py:2`
- `modules/core/adaptive_retry.py:29`

### 4.9 Chain-of-Verification (CoVe)

CoVe는 생성 후 사실/설정 모순을 다시 검토하는 사후 검증 체인이다. Stage 4 post-pass에서 quick verify 후 필요 시 LLM verification으로 이어진다.

안전한 설명:

`CoVe는 산출 후 사후 검증 체인으로, 통과본의 모순을 한 번 더 훑는 safety net이다.`

근거:

- `modules/core/chain_of_verification.py:2`
- `modules/core/stage4_outcome_runtime.py:108`

---

## 5. 프롬프트 강화 계열

### 5.1 CoT

CoT는 주로 프롬프트/컨텍스트 설계 표현으로 등장한다. 즉 `독립적인 CoT 오케스트레이터`라기보다 `사고 과정 유도형 prompt design` 쪽에 가깝다.

근거:

- `modules/domain/agents/chief_writer.py:118`
- `modules/domain/agents/chief_writer_context.py:161`

### 5.2 Contrastive CoT

네거티브 예시 기반의 `이렇게 쓰지 마라` 스타일 prompt injection이 실제 구현되어 있다.

근거:

- `modules/core/narrative_diversity.py:3`

### 5.3 Few-shot / Anti-pattern Injection

우수 예시와 안티패턴 회피를 프롬프트에 주입하는 모듈이 실제 존재한다.

근거:

- `modules/core/agent_intelligence.py:1`
- `modules/core/constitutional_checker.py:375`

### 5.4 Constitutional Injection

헌법형 체크리스트와 reject 사례를 stage별로 injection한다.

근거:

- `modules/core/constitutional_checker.py:560`
- `modules/core/stage2_preflight_runtime.py:272`

---

## 6. 품질 신호 및 운영 관측

글도비에는 전통적 verdict 외에 별도 품질 신호 레이어가 있다.

- `CED`
- `AI Slop`
- `compression_ratio`
- `burstiness`
- `complexity`
- `dialogue/style-target drift`
- `open_review`

이들은 대체로 `관측/경고/advisory`로 쓰이며, 곧바로 hard gate라고 말하면 과장이다.

안전한 설명:

`품질 신호는 별도 메트릭 레이어로 수집되며, 현재는 calibration과 advisory에 더 가깝다.`

근거:

- `modules/core/quality_signal_metrics.py:153`
- `modules/core/quality_signal_metrics.py:178`
- `modules/core/stage4_interview_round.py:5962`
- `modules/domain/agents/chief_writer_quality.py:842`
- `config/prompts/director.yaml:122`

---

## 7. 문서에는 크지만 런타임 핵심이라고 말하면 위험한 것

### 7.1 Taxonomy

이 단어는 문서, 로드맵, 제안서에서 자주 나오지만 현재 런타임 핵심 객체명으로 강하게 잡히지는 않는다.

의미:

`오류 유형이나 품질 축을 분류하는 체계`

발표 시 권장 표현:

`taxonomy는 주로 오류 분류/분석 체계 쪽 표현이다.`

근거:

- `docs/roadmap-v2.md:574`
- `docs/제안서_0318/프로젝트승인요청서_3차.md:594`

### 7.2 Ontology

현재 코드/설정에서 런타임 핵심 개념으로는 잘 보이지 않는다.

발표 시 주의:

`ontology를 핵심 엔진처럼 말하면 개발자가 어디에 모델링돼 있냐고 물을 수 있다.`

### 7.3 ToT / MAD / ASP의 위상

이 셋은 `있다`가 맞지만, `항상 모든 화에 본선으로 돈다`고 말하면 과장이다.

더 정확한 표현:

`특정 실패 버킷이나 강화 경로에서 붙는 보조 기법이다.`

---

## 8. 개발자가 바로 물을 만한 공격 포인트

### 8.1 항상 켜지는 구조인지 여부

가장 중요한 공격 포인트다.

정답:

`아니다. 핵심 구조와 보조 기법이 분리돼 있다. 앙상블, Director, retrieval, state SSOT, advisory chain은 주 구조고, ToT/MAD/ASP는 조건부 보조 경로다.`

### 8.2 Self-consistency의 비용 증폭 여부

정답:

`항상 3표가 아니라 애매한 점수대에서만 다중 투표로 확장된다.`

근거:

- `modules/validation/validation_orchestrator.py:946`

### 8.3 LLM이 LLM을 평가하는 순환 구조 지적

정답:

`맞다. 그래서 글도비는 LLM 재심사만 두지 않고, WorldState/FactLedger/TruthGate/python precheck/fix_scope 계약을 같이 둔다.`

### 8.4 advisory-only 검사의 실제 강제력

정답:

`많은 검사는 advisory-only다. 실제 block은 Director verdict와 stage retry/patch gate가 담당한다.`

### 8.5 RAG만으로 충분한지 여부

정답:

`아니다. retrieval은 보조고, 장기 기억의 뼈대는 WorldState와 FactLedger다.`

### 8.6 taxonomy / ontology의 실제 위치

정답:

`taxonomy는 주로 문서상의 분류 체계다. ontology는 현재 핵심 런타임 용어로 밀기 어렵다.`

### 8.7 PASS_WITH_FIX의 복잡도 문제

정답:

`맞다. fix_scope, patch/retry, 재심사, budget 관리가 걸려 있어서 지금 운영 리스크의 핵심 축 중 하나다.`

### 8.8 품질 신호의 verdict 직접 반영 여부

정답:

`일부는 Director evidence로 들어가지만, CED와 AI Slop은 현재는 hard reject보다는 advisory/calibration 성격이 강하다.`

---

## 9. 발표 시 안전한 표현과 위험한 표현

### 9.1 안전한 표현

- `글도비는 stage별 앙상블과 Director 판정을 중심으로 돌아간다.`
- `장기 기억은 상태 저장소와 retrieval의 조합으로 관리한다.`
- `Self-consistency, retrospective, reflexion은 보조 강화기법이다.`
- `ToT/MAD는 특정 reject bucket에서 붙는 구조다.`
- `CED, AI Slop 같은 품질 신호는 현재 관측과 drift 경고에 가깝다.`

### 9.2 위험한 표현

- `글도비는 ontology 기반 시스템이다.`
- `ToT와 MAD가 메인 엔진이다.`
- `모든 화에서 self-consistency 3표를 돈다.`
- `advisory chain이 자동으로 다 막아준다.`
- `품질 메트릭이 이미 완전 자동 판정한다.`

---

## 10. 발표자용 초압축 답변 10개

1. `글도비는 단일 RAG가 아니라 stage별 앙상블과 상태 저장소 중심 구조입니다.`
2. `장기 기억은 WorldState와 FactLedger를 SSOT로 두고 retrieval을 보조로 씁니다.`
3. `Director가 최종 verdict와 fix_scope를 결정합니다.`
4. `PASS_WITH_FIX는 국소 수정과 재심사를 자동화한 루프입니다.`
5. `Self-consistency는 조건부 다수결이지 항상 3배 호출은 아닙니다.`
6. `ToT와 MAD는 항상-on 메인이 아니라 특정 reject bucket 보조 경로입니다.`
7. `TruthGate와 advisory chain은 경고와 evidence를 만들고, 최종 차단은 Director가 맡습니다.`
8. `CED와 AI Slop은 현재 hard gate보다는 품질 신호에 가깝습니다.`
9. `taxonomy는 분류 체계 쪽 표현이고, ontology는 현재 핵심 런타임 용어로 밀기 어렵습니다.`
10. `핵심은 좋은 프롬프트 하나가 아니라, 후보 생성-심사-상태 반영-재시도까지 묶인 생산 공정입니다.`

---

## 11. 핵심 근거 파일

- `docs/poc/why_this_system.md`
- `config/settings/validation.yaml`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/truth_gate.py`
- `modules/core/context_advisor.py`
- `modules/core/vec_memory.py`
- `modules/core/self_reflection.py`
- `modules/core/reflexion_manager.py`
- `modules/core/tree_of_thoughts.py`
- `modules/core/multi_agent_deliberation.py`
- `modules/core/adversarial_self_play.py`
- `modules/core/chain_of_verification.py`
- `modules/core/quality_signal_metrics.py`
- `modules/core/stage4_interview_round.py`

---

## 12. 최종 정리

글도비에서 기술적으로 가장 자신 있게 말할 수 있는 축은 다음이다.

- Stage별 앙상블
- Director verdict + fix_scope
- WorldState + FactLedger 기반 장기 상태 관리
- Smart Retrieval + hybrid search
- TruthGate + advisory chain
- PASS_WITH_FIX patch/retry loop

반대로 조심해서 말해야 하는 축은 다음이다.

- taxonomy / ontology
- ToT / MAD / ASP의 위상
- quality signal의 hard-gate화 정도
- advisory-only 검사의 실제 강제력

발표에서 가장 안전한 문장 하나만 고르면 이 문장이다.

`글도비는 앙상블, Director 판정, 상태 저장소, retrieval, advisory chain, PASS_WITH_FIX 루프로 구성된 장편 생산 파이프라인이며, ToT/MAD/ASP 같은 것은 그 위에 붙는 조건부 보조 강화기법이다.`
