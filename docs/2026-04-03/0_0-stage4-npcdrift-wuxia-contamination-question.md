# NpcDrift 무협 장르 오염 의혹 — 코덱스 확인 요청

Date: 2026-04-03
Status: question-for-codex
Source: `0_0-stage4-npcdrift-relation-semantics-prompt-conflict-bounded-survey.md` 서베이 중 운영자 관찰

---

## 의혹

`NpcDriftAdvisor`가 무협 장르 기본값으로 하드코딩되어 있고, 장르별 분기 없이 전 장르에 동일 검사를 적용하고 있을 가능성.

## 근거

### 1. 검사 대상 필드가 무협 중심

`npc_drift_advisor.py:181-184` 프롬프트:

> 검사 대상: 역할, 관계(relation_to_protag), **무장**, **실력**, 성격, **부상 상태(injury)**, 현재 위치(location), **영구 부상(permanent_injuries)**, 지식시대(knowledge_era), 전문영역(expertise_domain), 비밀 인지(secrets_known), **이중 정체(dual_identity)**

투자/현대물에서 `무장`, `실력`, `영구 부상`, `이중 정체`는 의미가 없거나 다른 의미를 가짐.

### 2. exclude 목록이 무협 어휘

`npc_drift_advisor.py:17`:

> `_EXCLUDE_WORDS = frozenset(["주인공", "적", "자신", "상대", "아군", "동료", "스승", "제자", "장로", "문주"])`

`스승`, `제자`, `장로`, `문주`는 무협 전용 호칭. 현대물에서는 `회장`, `비서`, `형`, `동생` 등이 필요.

### 3. 관계 태그 해석 프레임

`오해 대상`이라는 태그를 NpcDrift LLM이 양방향 오해(무협에서 흔한 "원수인 줄 알았더니 은인" 류)로 읽는 경향이 있음. 투자/회귀물에서는 일방향(NPC→주인공)이 자연스러운데 검사기가 그 프레임을 갖고 있지 않음.

## 코덱스에게 묻는 것

Lane 1 확장(relation semantics 수정) 전에 확인 필요:

1. NpcDrift 검사 필드셋과 프롬프트가 장르별로 분기되는 경로가 있는가?
2. 아니면 무협 하드코딩 단일 경로인가?
3. 후자라면, relation semantics만 고쳐도 다른 장르에서 같은 류의 오탐(장르 부적합 필드 검사, 장르 부적합 해석 프레임)이 반복되지 않는가?

이 답에 따라 Lane 1의 스코프가 달라질 수 있음.
