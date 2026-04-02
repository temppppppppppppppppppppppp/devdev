# 글도비 기술 기법 1장 치트시트

Date: 2026-04-02
Status: final
Audience: 발표자 / 개발자 질의 대비
Confidence: 0.97

## 한 줄 요약

글도비는 `단일 RAG`가 아니라, `Stage별 앙상블 + Director 판정 + 상태 저장소(WorldState/FactLedger) + Smart Retrieval + Advisory Chain + PASS_WITH_FIX patch loop`로 돌아가는 장편 생산 파이프라인이다.

## 실제로 메인이라고 말해도 되는 것

- `앙상블`: Stage 2, 3, 4에서 후보를 병렬 생성하고 Director가 비교 선택한다.
- `Director verdict`: 최종 합격 여부와 수정 범위는 Director가 결정한다.
- `PASS_WITH_FIX`: `inplace / partial / full`로 수정 범위를 나눠 patch/retry를 건다.
- `WorldState + FactLedger`: 장기 기억의 뼈대는 프롬프트 안이 아니라 상태 저장소다.
- `Smart Retrieval`: ContextAdvisor가 stage별 슬롯을 짜고, VecMemory가 hybrid retrieval을 수행한다.
- `TruthGate + Advisory Chain`: 구조 오류와 장기 표류를 감지해 Director evidence로 넘긴다.

## 실제로 있긴 하지만 보조라고 말해야 하는 것

- `Self-consistency`: 항상 3번 도는 게 아니라 애매한 점수대에서만 다수결로 확장된다.
- `Consensus`: Stage 2 Arc용 3-LLM 합의 검증이 따로 있다.
- `Self-Reflection`: 생성 후 자기 비평을 한 번 더 수행한다.
- `Retrospective / Reflexion`: 장기 회고와 실패 패턴 기억을 보조로 쓴다.
- `ToT`: Stage 4에서 구조 오류 reject일 때 붙는 보조 탐색기다.
- `MAD`: Stage 4에서 제약 위반 reject일 때 붙는 보조 deliberation이다.
- `ASP`: adaptive retry에서 쓰는 강화기법이지 항상-on 메인 구조는 아니다.
- `CoVe`: 통과본에 대해 한 번 더 도는 사후 검증 체인이다.

## 조심해서 말해야 하는 것

- `taxonomy`: 주로 문서/분류 체계 쪽 표현이다. 핵심 런타임 객체처럼 말하면 위험하다.
- `ontology`: 현재 핵심 런타임 용어로 밀기 어렵다.
- `ToT/MAD`: 있다. 하지만 메인 엔진처럼 말하면 과장이다.
- `CED / AI Slop`: 현재는 품질 신호와 advisory에 가깝다. hard gate라고 말하면 위험하다.
- `advisory chain`: 많은 검사가 advisory-only다. 최종 차단은 Director verdict가 한다.

## 제일 자주 나올 질문과 1줄 답변

- `이거 다 항상 켜져 있나?`
  아니다. 주 구조와 보조 강화기법이 분리돼 있다.
- `RAG 시스템 아닌가?`
  retrieval은 보조고, 장기 기억의 뼈대는 WorldState와 FactLedger다.
- `LLM이 LLM 평가하는 구조 아닌가?`
  맞다. 그래서 상태 저장소, python precheck, TruthGate, fix_scope 계약을 같이 둔다.
- `ToT/MAD가 핵심인가?`
  핵심 본선이라기보다 특정 reject bucket에서 붙는 보조 경로다.
- `품질 신호가 verdict를 직접 바꾸나?`
  일부는 evidence로 들어가지만, CED와 AI Slop은 현재 advisory 성격이 더 강하다.
- `가장 중요한 기술 축이 뭐냐?`
  앙상블, Director 판정, 상태 저장소, retrieval, advisory chain, PASS_WITH_FIX 루프다.

## 발표 때 제일 안전한 문장

`글도비는 앙상블, Director 판정, 상태 저장소, retrieval, advisory chain, PASS_WITH_FIX 루프로 구성된 장편 생산 파이프라인이고, ToT/MAD/ASP 같은 것은 그 위에 붙는 조건부 보조 강화기법입니다.`

## 핵심 근거

- `docs/poc/why_this_system.md`
- `config/settings/validation.yaml`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/context_advisor.py`
- `modules/core/vec_memory.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
