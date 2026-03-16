# project 0_260316 Stage 4 continuity + codebase survey

Date: 2026-03-16
Type: system-track survey
Scope:
- `projects/0_260316`의 Stage 4 실물 원고(현존 ep1~6) 직접 판독
- 인접 Arc/Blueprint 문서와의 연속성 비교
- Stage 4 continuity/state pipeline 코드베이스 조사
Excluded:
- ep7 중단 원인의 live rerun 재현
- 코드 수정/패치 실행
Evidence Basis:
- manuscripts: `projects/0_260316/drafts/ep_0001.txt` ~ `ep_0006.txt`
- arcs: `projects/0_260316/plans/arcs/arc_001.txt` ~ `arc_003.txt`
- blueprints: `projects/0_260316/plans/blueprints/blueprint_0001.txt` ~ `blueprint_0007.txt`
- runtime/code: `main_a.py`, `modules/core/stage4_*`, `modules/validation/*`, `modules/domain/agents/director_continuity.py`, related tests
Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: 1 tracked, 10 untracked; hotspots: projects/0_260316/project_data.db, docs/2026-03-16/*, projects/0_260316/0_temp.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
3-Pass Audit:
- Pass 1 Structure/Scope: completed
- Pass 2 Evidence/Consistency: completed
- Pass 3 Execution/Readability: completed
Estimated Confidence: `96%`

## 1. Executive verdict

현존 Stage 4 원고(ep1~6)는 서로 직접 읽었을 때 큰 연속성 붕괴는 없다. 실물 기준으로는 cliffhanger carry-over가 전반적으로 잘 이어진다.

문제의 중심은 원고 자체보다는 `설계문서/상태문서/검증기` 사이의 권위 불일치다. 특히 아래 두 축이 이번 프로젝트에서 가장 크다.

- `Arc tactical/state 문서가 최종 원고와 드리프트했는데도 Stage 4 컨텍스트에 계속 강하게 주입된다.`
- `장비/상태를 이름 집합 중심으로 저장해 수량·구성 차이를 권위 있게 추적하지 못한다.`

즉, `ep1~6 실물 원고는 대체로 연속적`이지만 `ep7 이후로 갈수록 stale arc state가 다시 끼어들면 흔들릴 구조`다.

## 2. 실물 원고 연속성 조사

### 2.1 잘 이어지는 구간

- ep2 말미 종이 문진 폭행의 상처가 ep3 초반 뺨의 피로 이어진다.
  - `drafts/ep_0003.txt:5`
- ep3 말미 지하 주차장 대치가 ep4 오프닝으로 직접 이어진다.
  - `drafts/ep_0003.txt:137`
  - `drafts/ep_0004.txt:3`
- ep4 후반 테헤란로 사무실 계약 및 장비 설치가 ep5의 사무실 운영 시작으로 자연스럽게 이어진다.
  - `drafts/ep_0004.txt:39`
  - `drafts/ep_0004.txt:71`
  - `drafts/ep_0005.txt:28`
- ep5 마지막 대사 `WTI 원유 거래가 가능한 걸로.`가 ep6 첫 장면으로 직결된다.
  - `drafts/ep_0005.txt:101`
  - `drafts/ep_0006.txt:5`

### 2.2 실물 기준 주요 리스크

#### Finding M1. Arc 1 설계와 ep3~5 실물 원고가 이미 상당히 갈라져 있다

`arc_001.txt`는 ep3~4를 `모친 신탁/시내 은행 VIP 라운지/신축 오피스텔/트레이딩용 컴퓨터 2대/업무용 휴대전화 획득` 축으로 서술한다. 하지만 실물 원고는 다음처럼 다르다.

- ep3 실물은 `박 부장`에게 계약서 17조를 근거로 전화 압박 후 당일 현금화, 이후 지하 주차장 대치로 간다.
  - `drafts/ep_0003.txt:11`
  - `drafts/ep_0003.txt:33`
  - `drafts/ep_0003.txt:137`
- ep4 실물은 `테헤란로 허름한 상가 건물 2층` 사무실 계약과 `PC 세 대 + 모니터 여섯 대` 설치다.
  - `drafts/ep_0004.txt:39`
  - `drafts/ep_0004.txt:71`
- ep5 실물에서 `업무용 휴대전화`는 새 박스에서 꺼내는 물건으로 다시 등장한다.
  - `drafts/ep_0005.txt:35`
  - `drafts/ep_0005.txt:39`

반면 Arc 1 문서는 다음 상태를 주장한다.

- `시내 은행 VIP 라운지`
  - `plans/arcs/arc_001.txt:72`
- `신축 오피스텔`, `트레이딩용 컴퓨터 두 대`
  - `plans/arcs/arc_001.txt:85`
  - `plans/arcs/arc_001.txt:87`
- `업무용 휴대전화 획득`
  - `plans/arcs/arc_001.txt:94`

이건 단순 표현 차이보다 `상태 기반 프롬프트 소스가 이미 stale`하다는 신호다.

#### Finding M2. 컴퓨터 수량은 실물/Blueprint와 Arc 문서가 어긋난다

- ep4 실물: `PC 세 대`, `모니터 여섯 대`
  - `drafts/ep_0004.txt:71`
- blueprint_0007: `컴퓨터 본체 세 대`, `여섯 대의 모니터`
  - `plans/blueprints/blueprint_0007.txt:9`
- arc_002, arc_003: 반복적으로 `트레이딩용 컴퓨터 2대`
  - `plans/arcs/arc_002.txt:67`
  - `plans/arcs/arc_002.txt:89`
  - `plans/arcs/arc_003.txt:23`
  - `plans/arcs/arc_003.txt:51`
  - `plans/arcs/arc_003.txt:81`
  - `plans/arcs/arc_003.txt:112`

즉 실제 전개 축은 `3대` 쪽인데, Arc state는 계속 `2대`를 들고 간다. 이건 후속 회차에서 다시 stale state를 불러오면 재오염될 수 있는 구조다.

#### Finding M3. 위협 스레드는 실물 원고 안에서는 살아 있으나 구조화 상태로는 약하다

- ep4는 형 측 사람들의 직접 위협과 감시 스레드를 강하게 세운다.
  - `drafts/ep_0004.txt:3`
  - `drafts/ep_0004.txt:101`
- ep5~6은 PB/WTI 축으로 급격히 이동한다.
  - `drafts/ep_0005.txt:51`
  - `drafts/ep_0006.txt:7`

실물 읽기만 하면 모순은 아니다. 다만 이후 회차에서 회수하려면 `미해결 위협 상태`가 durable state로 남아 있어야 하는데, 현재 파이프라인은 이 부류를 구조적으로 강하게 저장하는 흔적이 약하다. 이건 코드 조사 결과와 연결된다.

#### Finding M4. `박 부장`과 `박성호 PB`는 실물상 즉시 모순은 아니지만 추적 리스크가 있다

- ep3은 `박 부장`만 등장한다.
  - `drafts/ep_0003.txt:11`
  - `drafts/ep_0003.txt:33`
- ep5~6은 `박성호 PB`와 `박 차장님`이 등장한다.
  - `drafts/ep_0005.txt:51`
  - `drafts/ep_0006.txt:47`
  - `drafts/ep_0006.txt:55`

실물 원고만 보면 다른 인물로 읽는 데 큰 문제는 없다. 다만 메타데이터/상태 추적에서 abbreviated role label과 full-name NPC가 섞이면 drift warning substrate가 생길 수 있다.

#### Finding M5. ep4 제목 메타데이터만 형식이 다르다

- `drafts/ep_0004.txt:1`은 `# 제4화`만 있고 부제가 없다.

연속성 문제는 아니지만 산출물 형식 일관성은 떨어진다.

## 3. 코드베이스 조사

### 3.1 High

#### Finding C1. Stage 4는 stale Arc 문서를 여전히 강하게 mandatory context에 싣는다

`prepare_episode_context()`는 `arc_data["tactical_doc"]`를 바로 `arc_tactical`로 가져온다.

- `modules/core/stage4_context_builder.py:1755-1767`

이후 `build_mandatory_context()`는 `arc_tactical`을 기준으로 anchor retrieval과 work focus를 구성하고, continuity packet, state tracker summary, arc summary, vec retrieval까지 모두 합쳐서 mandatory context를 만든다.

- `modules/core/stage4_context_builder.py:2105-2182`
- `modules/core/stage4_context_builder.py:2288-2407`
- `modules/core/stage4_context_builder.py:2410-2489`
- `modules/core/stage4_context_builder.py:2550-2557`

즉 `실물 원고/블루프린트와 어긋난 Arc tactical`이 있어도, 현재 설계는 이를 약한 참고 자료가 아니라 writer-facing 핵심 문맥의 일부로 계속 재주입한다. 이번 프로젝트의 `컴퓨터 2대 vs 3대`, `신축 오피스텔 vs 허름한 상가`, `업무용 휴대전화 획득 시점` 드리프트와 직접 맞물린다.

#### Finding C2. Director continuity가 받는 `story_context`는 너무 얇고, 진짜 풍부한 상태 문맥은 Writer 측에만 있다

세션의 `story_context`는 Stage 4 준비 시 `장르/주인공/세계 출신/환생 유형/핵심 특성` 정도만 담아 만든다.

- `modules/core/stage4_orchestrator.py:1507-1537`

생성 루프에서는 이 얇은 `story_context`를 그대로 round context에 넣는다.

- `modules/core/stage4_orchestrator.py:640-651`
- `modules/core/stage4_orchestrator.py:860-880`
- `modules/core/stage4_context_builder.py:2667-2706`

반면 풍부한 세계 상태, Arc tactical, continuity packet, summaries, retrieval 결과는 `mandatory_context` 쪽에서 조립된다.

- `modules/core/stage4_orchestrator.py:747-763`
- `modules/core/stage4_context_builder.py:2105-2182`
- `modules/core/stage4_context_builder.py:2555-2557`

Director continuity validator는 `story_context`를 받지만, 이 값 자체가 얇다.

- `modules/domain/agents/director_continuity.py:750-829`

결과적으로 `Chief Writer는 풍부한 혼합 문맥으로 쓰고`, `Director continuity는 얇은 작품 설명 + 최근 원고 캐시` 위주로 본다. 이 권위 비대칭이 state drift를 놓치기 쉬운 구조다.

### 3.2 High-Medium

#### Finding C3. `prev_hud`는 persisted previous snapshot이 아니라 live `sys.hud.pro_root` 의존이다

Interview round의 continuity validator context는 `prev_hud`를 `self.ctx.sys.hud.pro_root`에서 바로 읽는다.

- `modules/core/stage4_interview_round.py:3942-3955`

ContinuityValidator는 이 값이 없으면 즉시 degraded fail-closed로 빠진다.

- `modules/validation/continuity_validator.py:117-145`

즉 연속성 검사가 `직전 화 확정 snapshot`이 아니라 `현재 런타임 HUD 객체가 무엇을 들고 있느냐`에 의존한다. 정상 순차 실행에서는 통과할 수 있어도, 재개 런/부분 재시작/오염된 HUD에서는 품질이 흔들릴 수 있다.

#### Finding C4. 장비/아이템 저장은 이름 집합 중심이라 수량/구성 차이를 구조적으로 잃는다

post processor는 `actual_truth.equipment`와 이전 equipment를 `set()`으로 바꿔 diff를 낸다.

- `modules/core/stage4_post_processor.py:851-875`

그 뒤 `all_new_items`도 `set()`으로 다시 dedupe된다.

- `modules/core/stage4_post_processor.py:990-1004`

WorldState는 `major_items`를 이름별 active item으로만 저장한다.

- `modules/core/world_state.py:237-255`

FactLedger도 `major_items`를 item 이름 단위로만 upsert한다.

- `modules/core/fact_ledger.py:191-202`

Arc terminal state 역시 equipment를 문자열/리스트로만 정규화한다.

- `modules/core/arc_state_utils.py:81-100`

BlockingValidator의 unowned item check도 equipment를 이름 목록으로만 본다.

- `modules/validation/blocking_validator_entity_checks.py:149-179`

따라서 `트레이딩용 컴퓨터 2대 vs 3대`, `모니터 6대`, `동일 장비의 구성 변화` 같은 문제는 현재 파이프라인에서 durable structured fact로 남기기 어렵다.

### 3.3 Medium

#### Finding C5. continuity pin guard의 자동 보정 범위가 너무 좁다

Stage 3/4 handoff용 deterministic pin은 사실상 `고유명사 1건`과 `시간 표면 표현`만 다룬다.

- `modules/core/continuity_pin_guard.py:92-149`

즉 `사무실 위치`, `장비 수량`, `장비 구성`, `지속 위협 상태` 같은 이번 조사 핵심 항목은 자동 pin 대상이 아니다. stale arc tactical이 들어와도 이 계층에서 바로잡히지 않는다.

#### Finding C6. Blueprint preflight는 컴퓨터/모니터 계열 이슈를 의도적으로 low로 낮춘다

Blueprint preflight는 high severity issue라도 `고증`, `해상도`, `모니터`, `컴퓨터`가 들어가면 low로 내린다.

- `modules/core/stage4_orchestrator.py:485-528`

테스트도 이 정책을 고정한다.

- `tests/test_blueprint_preflight.py:371-399`

즉 이번 프로젝트에서 핵심이 된 `사무실 장비 수량/구성 드리프트`는 preflight 관문에서 강하게 막힐 가능성이 낮다. 의도된 false-positive 완화가 투자물 장비 continuity까지 함께 약화시키는 셈이다.

#### Finding C7. 관계/위협 변화 일부는 Episode Bible에는 남아도 durable structured memory로 승격되지 않는다

post processor는 `knowledge_map`와 `karma_matrix`를 바탕으로 `relationship_changes`를 문자열로 조립해 Episode Bible delta에 넣는다.

- `modules/core/stage4_post_processor.py:935-951`
- `modules/core/stage4_post_processor.py:992-1004`

하지만 FactLedger의 `update_from_bible_delta()`는 `new_npcs`, `npc_deaths`, `new_items`, `lost_items`만 반영하고 `relationship_changes`는 반영하지 않는다.

- `modules/core/fact_ledger.py:278-312`

즉 `누가 누구를 목격했고`, `누가 누구를 오해하게 됐고`, `집착/오해 수치가 높아졌다` 같은 위협 스레드는 episode_bible에는 남아도 FactLedger durable state로는 직접 승격되지 않는다. 실물에서 느껴진 `위협 스레드의 잠복 상태`와 구조적으로 맞물린다.

## 4. LLM 한계 조사

이 섹션의 요지는 `LLM 자체의 일반 성능 문제`만이 원인이 아니라는 점이다. 더 정확히는 `긴 자연어 지시 + 부분 샘플링 + 평평한 상태 스키마` 조합이 모델의 약점을 증폭한다는 것이다.

### 4.1 Prompt saturation과 low-salience fact 손실

Chief Writer 메인 프롬프트는 Blueprint, 직전 화 엔딩, HUD, 장비, Arc doc, style guide, 만족도 가이드, 이전 원고 전문 등 다수의 섹션을 한 프롬프트에 합친다.

- `modules/domain/agents/chief_writer_prompts.py:50-149`
- `modules/domain/agents/chief_writer_context.py:455-509`

Prompt 본문 규칙도 이미 매우 많다. 공통 규칙만 16개, 투자물 전용 수치 규칙도 별도로 붙는다.

- `config/prompts/chief_writer.yaml:14-73`

Stage 4 context builder는 이 거대한 문맥을 headroom과 budget에 맞춰 반복적으로 trim한다.

- `modules/core/stage4_context_builder.py:1444-1516`

Director 쪽도 이전 원고 전문을 `smart_truncate()`로 줄이고, `mandatory_context`도 별도 상한으로 잘라 넣는다.

- `modules/domain/agents/director_continuity.py:445-473`
- `modules/domain/agents/director_ensemble.py:902-967`
- `modules/core/constants.py:136-165`

이 구조에서는 `컴퓨터 3대`, `허름한 상가 2층`, `형 측 감시망의 잔존`처럼 중요하지만 저빈도인 사실이 긴 자연어 문맥 속에서 쉽게 salience를 잃는다.

### 4.2 LLM 검증기의 top-k 샘플링 한계

NPC drift 검사는 등장 NPC 중 최대 8명만 골라서, 원고도 4,000자 snippet만 본다.

- `modules/core/npc_drift_advisor.py:30-136`
- `modules/core/stage4_interview_round.py:4288-4324`

Flashback verifier는 최대 5개 marker, marker당 200자 window만 추출한다. retrieval도 앞 3개 질의, 최대 3개 원문 snippet만 쓴다.

- `modules/core/flashback_verifier.py:14-135`
- `modules/core/stage4_interview_round.py:4357-4398`

State-Text verifier는 실제로 설정 파일에서 활성화되어 있지만, 검증 대상 필드를 수치/장비 중심으로 좁히고 원고도 최대 8,000자를 head+tail로만 본다. 게다가 항상 advisory다.

- `config/settings/validation.yaml:172-179`
- `modules/core/state_text_verifier.py:44-140`

즉 이 계층은 본질적으로 `전수 검사`가 아니라 `샘플 검사`다. 회차가 길어지고 인물/위협/소도구가 늘어날수록 recall ceiling이 구조적으로 생긴다.

### 4.3 Manager 1-shot 정산의 단일 실패점

Manager prompt는 `actual_truth`, `knowledge_map`, `new_lore`, `recovered_seeds`, `causal_links`, `NPC HUD`, `equipment` 전체 목록까지 한 번에 요구한다.

- `modules/domain/agents/manager.py:16-119`

실행 경로도 사실상 단일 ask 후 robust parse다.

- `modules/domain/agents/manager.py:205-264`

이 말은 한 번의 LLM 응답에서 장비, 관계, NPC 상태, 복선 회수 중 일부가 빠지거나 엇갈리면, 그 결함이 Episode Bible, WorldState, FactLedger의 입력 원천으로 그대로 번진다는 뜻이다.

### 4.4 Advisory-only 정책이 검출력을 집행력으로 못 바꾼다

Stage 4에는 LLM 기반 경고 모듈이 많지만 다수가 advisory다.

- `modules/core/npc_drift_advisor.py:20-139`
- `modules/core/flashback_verifier.py:18-135`
- `modules/core/state_text_verifier.py:71-140`

특히 State-Text verifier는 mismatch를 찾아도 `blocking=False`이고, correction이 불가능하면 저장을 막지 않는다.

- `modules/core/state_text_verifier.py:88-140`

Blueprint preflight도 `컴퓨터`, `모니터`, `고증`, `해상도`가 들어간 high issue를 low로 낮춘다.

- `modules/core/stage4_orchestrator.py:485-528`
- `tests/test_blueprint_preflight.py:371-399`

따라서 LLM이 뭔가를 알아차려도 그것이 `실제 차단/수정`으로 이어질 가능성은 별개다.

### 4.5 LLM에게 count-sensitive 사실을 count-native schema 없이 맡기는 문제

Manager prompt는 `equipment` 전체 목록을 잘 출력하라고 강하게 지시하지만, downstream 저장 구조는 여전히 평평한 리스트/이름 집합 중심이다.

- `modules/domain/agents/manager.py:32-53`
- `modules/core/stage4_post_processor.py:851-875`
- `modules/core/world_state.py:237-255`
- `modules/core/fact_ledger.py:191-202`

이건 순수 모델 문제라기보다 `모델에게 수량/구성/배치 추론을 시키면서 결과를 count-native schema로 보존하지 않는 문제`다. 그래서 `트레이딩용 컴퓨터 2대 vs 3대` 같은 사실은 LLM이 잠깐 맞게 읽어도 durable system truth로 잘 안 굳는다.

## 5. 개선 아이디어

아래 개선안은 모두 현재 워크스페이스 원칙을 지킨다. 즉 `Python은 수집/구조화`, `LLM은 충돌 여부와 수정 방향을 판정`하는 방향이다.

### 5.1 권위 계층을 프롬프트에서 명시적으로 분리

현재는 Arc tactical, retrieval hit, published manuscript, WorldState가 섞여 들어간다. 이를 다음처럼 계층화해야 한다.

- Tier 1 canonical: `published manuscript`, `world_state`, `fact_ledger`, persisted previous HUD
- Tier 2 operational: `blueprint`, `episode_bible`, `chain_link`
- Tier 3 heuristic: `arc tactical`, vector retrieval, advisory summaries

LLM prompt에도 `Tier 1 is final authority`, `Tier 3 may be stale`를 명시해야 한다. 특히 Arc tactical은 rewrite seed이지 truth authority가 아니라고 못 박는 편이 안전하다.

### 5.2 연속성 검사를 “전체 원고 읽기”에서 “구조화 diff 판정”으로 축소

지금은 LLM에게 긴 원고와 긴 과거 문맥을 한꺼번에 던지는 경우가 많다. 대신 Python이 아래를 수집해 `diff packet`으로 만들고, LLM은 그 packet만 판정하도록 좁히는 것이 낫다.

- 장비 변화 후보
- 위치 변화 후보
- 관계 변화 후보
- unresolved threat carry-over 후보
- 고유명사 alias 후보

즉 `원고 전체를 다시 이해하라`보다 `이 다섯 개 diff가 모순인지 아닌지 판정하라`가 LLM에 더 맞다.

### 5.3 Manager 정산을 단일 거대 호출에서 다중 typed pass로 분해

현재 Manager 1-shot은 한 번의 응답에 너무 많은 책임을 진다. 다음처럼 분해하는 편이 안전하다.

- pass A: protagonist `actual_truth`
- pass B: NPC delta / NPC equipment
- pass C: lore / item / seed recovery
- pass D: causal links / knowledge map

각 pass는 더 작은 JSON schema를 갖고, Python은 그 결과를 모아 병합만 한다. 판단은 여전히 LLM이 하되, 실패점이 분산된다.

### 5.4 count-sensitive 상태를 구조화 스키마로 승격

이번 사례의 직접 대응책이다.

- `equipment`를 문자열 목록이 아니라 `{name, quantity, location, status, owner}` 구조로 승격
- `office asset inventory` 같은 투자물 전용 canonical surface 추가
- `unresolved threats` 혹은 `active pressure vectors` 같은 지속 위협 레지스터 추가

그래야 LLM이 읽어낸 상태가 `사라지지 않는 truth surface`로 남는다.

### 5.5 top-k advisory를 chunked exhaustive audit로 바꾸기

NPC drift, flashback, relation drift는 지금 구조상 recall이 낮다. 개선 방향은 다음이 적절하다.

- 등장 NPC를 8명으로 자르지 말고 chunk로 나눠 모두 검사
- flashback marker를 상한 없이 모으되, chunk batch로 LLM에 넘김
- retrieval hit도 top-k 몇 개가 아니라 `candidate set -> chunk -> merge`로 처리

이때 Python은 chunk 분할과 evidence packing만 하고, drift 여부 판정은 LLM이 맡는다.

### 5.6 advisory를 criticality-based gate로 승격

모든 경고를 blocking으로 바꾸자는 뜻은 아니다. 대신 아래는 gate 승격 후보다.

- canonical inventory count mismatch
- dead/alive state contradiction
- persistent threat thread drop when blueprint requires carry-over
- critical financial number mismatch

특히 투자물에서 `컴퓨터/모니터/HTS/법인 서류`는 단순 고증이 아니라 canonical office state일 수 있으므로, 현재처럼 자동 low downgrade를 일괄 적용하는 정책은 재검토 대상이다.

### 5.7 0_260316를 regression corpus로 고정

이번 프로젝트는 실제 실패/드리프트 패턴이 이미 모여 있다. 최소 아래를 golden regression으로 삼는 것이 좋다.

- `arc_001 vs ep_0004` 사무실/장비 drift
- `ep_0005 -> ep_0006` WTI carry-over
- `박 부장` vs `박성호 PB` alias 분리
- `업무용 휴대전화` 획득 시점
- `형 측 위협 스레드` 지속성

이건 단순 설명 문서보다 가치가 높다. 이후 Stage 4 수정은 이 corpus를 통과해야 “실제 현업 실패 재발 방지”라고 말할 수 있다.

## 6. 테스트 표면 조사

- `박성호 position 추적`은 전용 테스트가 촘촘하게 있다.
  - `tests/test_con2_npc_position_tracking.py`
- 반면 `장비 수량 continuity`를 직접 겨냥한 테스트는 이번 검색 범위에서 찾지 못했다.
- 검색상 장비 관련으로 두드러진 건 preflight의 `모니터/고증 false-positive downgrade` 테스트다.
  - `tests/test_blueprint_preflight.py:371-399`

즉 NPC 직함 표류는 계약이 있지만, 투자물 사무실 장비 수량/구성 continuity는 계약이 약하다.

## 7. 운영상 결론

이번 `0_260316`의 Stage 4 실물 원고는 `지금 당장 깨진 상태`라기보다 `구조적으로 다시 깨질 준비가 된 상태`에 가깝다.

우선순위는 아래가 맞다.

1. `Stage 4 context authority 정리`
   - stale arc tactical/state보다 `published manuscript + blueprint + world_state/fact_ledger`를 우위로 두어야 한다.
2. `equipment를 이름 집합이 아니라 구조화 inventory로 승격`
   - 수량, 구성, 상태, 위치를 다룰 수 있어야 `2대/3대` 문제가 잡힌다.
3. `Director continuity에 writer급 canonical state를 직접 전달`
   - 얇은 story_context만으로는 부족하다.
4. `prev_hud를 live HUD가 아니라 persisted previous snapshot으로 고정`
   - 재개 런/부분 런에서 안정성이 오른다.
5. `투자물 장비 continuity와 위협-state 지속성 테스트 추가`
   - 현재 테스트는 position 쪽에 치우쳐 있다.

## 8. Bottom line

실물 판독 결론은 `ep1~6 자체는 대체로 연속적, 핵심 문제는 코드/상태 파이프라인의 권위 불일치`다.

LLM 관점 결론은 `모델 성능 자체`보다 `과도하게 넓은 자연어 지시`, `부분 샘플링`, `평평한 상태 스키마`, `advisory 위주의 집행 정책`이 더 큰 병목이다.

따라서 다음 조사/작업은 `ep7 재개 가능성 점검`보다 `Stage 4 continuity authority hierarchy와 inventory schema 보강 설계`가 먼저다.
