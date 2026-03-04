# 독자 워크프레임 안정성 검토
## — LangGraph / LangChain 대비 비교 분석

> 작성일: 2026-03-04
> 대상: 글도비 커스텀 AI 파이프라인
> 목적: 유명 워크프레임 대비 독자 구현의 타당성·안정성 평가

---

## 1. 요약 결론

**결론: 독자 워크프레임이 글도비 요구사항에 더 적합하다. 단, 특정 영역에서 인지 비용이 높다.**

| 기준 | LangChain | LangGraph | 글도비 |
|------|-----------|-----------|--------|
| 도메인 적합성 | ▲ 범용 | ▲ 범용 | ★ 특화 |
| 상태 일관성 (200화+) | △ 약함 | ○ 보통 | ★ 강함 |
| 에러 복구 | △ 호출자 책임 | ○ 보통 | ★ 내장 3-tier |
| 롤백 | △ 없음 | △ 부분 | ★ 전체 체인 |
| Director 주권 | ✗ 없음 | △ 조건문 | ★ 설계 원칙 |
| 생태계·커뮤니티 | ★ 매우 넓음 | ★ 넓음 | ✗ 없음 |
| 초기 학습 비용 | ○ 낮음 | ○ 낮음 | △ 높음 |
| 외부 의존성 리스크 | △ 높음 | △ 높음 | ★ 없음 |

---

## 2. 비교 대상 개요

### 2.1 LangChain

- **패러다임**: Chain = 선형 컴포넌트 연결. `PromptTemplate | LLM | Parser` 파이프 연산자.
- **강점**: 방대한 integrations(100+ LLM, 벡터DB, 툴), 커뮤니티, 공식 문서.
- **약점**: 상태 관리 미약(Memory 컴포넌트가 보조적), 복잡한 분기 흐름 구현이 어색함, 버전 변경이 잦아 Breaking Change 빈발.

### 2.2 LangGraph

- **패러다임**: StateGraph = 노드(함수) + 엣지(전이). 유한 상태 기계(FSM) 방식.
- **강점**: 사이클(루프) 허용, 체크포인트 저장, Human-in-the-loop 지원.
- **약점**: 상태 = Message list 위주 (도메인 엔티티 추적이 별도 구현 필요), 대규모 멀티에이전트 오케스트레이션에서 그래프 복잡도 폭발.

### 2.3 글도비 독자 워크프레임

- **패러다임**: Stage(오케스트레이터) + Agent(LLM 전문가) + DI Context(슬롯 기반).
- **근간**: "Python은 수집만, 판단은 LLM이" + "Director 주권주의".
- **검증 규모**: 3,213 passed, PBT 46개, E2E smoke 33개 (2026-03-04 기준).

---

## 3. 핵심 비교 항목

### 3.1 상태 관리

웹소설 200화 이상의 장기연재에서 상태 일관성은 가장 중요한 요소다.

**LangGraph 방식**:
```python
# 상태 = 메시지 리스트. 도메인 엔티티는 직접 추가해야 함.
class State(TypedDict):
    messages: list[BaseMessage]
    # 장편 소설 월드 상태? 직접 구현해야 함.
```

**글도비 방식**:
```python
# WorldState: 세계관 전체를 단일 JSON으로 추적
# FactLedger: 수치 누적 (자산, 부상, 무기 내구도 등)
# NPC 이력: append-only 테이블 (롤백 보호)
# npc_relationship_history: 관계도 장기 추적

world_state.cumulative_elapsed  # 누적 경과 시간 (TF-F)
fact_ledger.get_history("asset_value")  # 5화 단위 수치 이력
npc_history.get_snapshot(ep_num)  # 특정 화의 NPC 속성 스냅샷
```

**판정**: 글도비 우위. LangGraph로 동등한 기능을 구현하려면 수천 줄의 커스텀 상태 관리 코드가 추가된다.

---

### 3.2 에러 복구

Gemini API는 Rate Limit(429), Quota 고갈(403), 네트워크 타임아웃이 실운영에서 빈번하게 발생한다.

**LangGraph/LangChain 방식**:
- 에러 처리는 호출자 책임. 재시도 라이브러리(tenacity 등) 별도 연동.
- 모델 폴백은 명시적 코드 작성 필요.

**글도비 방식 (BaseAgent 내장)**:
```
Tier 1: Rate Limit (429) → 같은 모델 재시도 (최대 3회, 1→2→4초)
Tier 2: Quota (403)      → 모델 스택 순환 (Primary → Backup → Flash)
Tier 3: Network timeout  → API 키 순환 + 지수 백오프 (최대 22회)
```

모든 에이전트가 BaseAgent를 상속하므로, 에러 처리 로직을 20+ 에이전트에 반복 작성할 필요가 없다.

**판정**: 글도비 우위. 장시간(수 시간) 파이프라인 실행 환경에서 핵심적인 차이.

---

### 3.3 롤백

**LangGraph**: 체크포인트 저장은 지원하나, NPC 이력·WorldState·FactLedger 연계 롤백은 없음.

**글도비**:
```python
db_manager.reset_after(target_ep=15)
# → manuscripts: 15화 이후 삭제
# → npc_history: 15화 이후 NPC 변경 삭제
# → npc_relationship_history: 15화 이후 관계 변경 삭제
# → world_state: 15화 시점으로 복원
# → fact_ledger: 15화 시점으로 복원
# → vec_memory: 15화 이후 임베딩 삭제
# SQLite WAL + integrity_check 보호
```

**판정**: 글도비 압도적 우위. LangGraph로 동등 구현 시 수백 줄 추가 필요.

---

### 3.4 도메인 특화 기능

LangGraph/LangChain은 범용 워크프레임이므로 다음 기능들이 없다:

| 기능 | LangGraph | 글도비 |
|------|-----------|--------|
| WritingDirective (직전 N화 패턴 → 지시 생성) | ✗ | ★ TF-54 |
| PASS_WITH_FIX verdict (국소 수정 허용) | ✗ | ★ TF-27~34 |
| NPC 속성 표류 감지 (LLM advisory) | ✗ | ★ LM-B |
| 수치 누적 표류 감지 (지수 성장 탐지) | ✗ | ★ LM-C |
| 1인칭 정보 역설 감지 | ✗ | ★ LM-F |
| 세계법칙 위반 TruthGate | ✗ | ★ LM-A |
| Director 주권주의 (합격/불합 권한 분리) | ✗ | ★ 설계 원칙 |
| 장르별 동적 스키마 (비무협 오염 방지) | ✗ | ★ TF-45 |

이 기능들은 LangGraph 위에서도 구현 가능하나, 결국 독자 코드로 구현해야 한다. 즉, LangGraph를 쓰더라도 실질적인 로직 복잡도는 동일하다.

---

### 3.5 검증 파이프라인

**LangGraph**: 노드 간 조건부 엣지로 검증 흐름 구성. 단순 분기는 편리하나 6-Tier 검증 같은 복합 구조에서 그래프가 난잡해진다.

**글도비 6-Tier 검증**:
```
Tier 0.25: PreLLMValidator (Python, LLM 0회)  ← 명백한 오류 조기 차단
Tier 0.5:  ContinuityValidator               ← 에피소드 간 연속성
Tier 1:    BlockingValidator (LLM)           ← 논리 오류 심사
Tier 2:    ConsistencyValidator              ← 세계관 일관성
Tier 3:    ScoringValidator                  ← 품질 점수 (rubric)
Tier 4:    Advisory 7종                      ← NPC표류·수치표류·관계표류·
                                                회상오염·정보역설·장기반복
```

각 Tier는 독립 클래스로 분리되어 단위 테스트 가능. LangGraph 노드로 표현할 수도 있으나 상태 전달 방식이 복잡해진다.

---

### 3.6 외부 의존성 리스크

**LangChain**: v0.1 → v0.2 → v0.3 Breaking Change 잦음. 커뮤니티 이슈에서 "버전 맞추는 데 하루 날렸다"는 사례 다수.

**LangGraph**: LangChain 위에서 구축되므로 동일한 위험.

**글도비**: 외부 AI 워크프레임 의존성 없음. Python 표준 라이브러리 + SQLite + Gemini API. 외부 라이브러리 업그레이드로 인한 Breaking Change 리스크 없음.

---

## 4. 안정성 평가

### 4.1 코드 안정성

| 지표 | 현황 |
|------|------|
| 테스트 통과 | 3,213 passed + 0 xfailed |
| Property-based tests | 46개 (hypothesis) |
| E2E smoke tests | 33개 (파이프라인 통합) |
| Ruff violations | 0건 |
| Silent Pass YELLOW | 0건 |
| 전수조사 | 6회 완료 (P0 0건 잔존) |

### 4.2 운영 안정성

- **API 키 순환**: 멀티키 환경에서 429 발생 시 무중단 전환
- **WAL 저널링**: SQLite 손상 방지 (PRAGMA journal_mode=WAL, synchronous=FULL)
- **롤백 체인**: 에피소드 단위 완전 복구 (6개 데이터 소스 연계)
- **실파이프라인 검증**: 투자물 장르 실제 파이프라인 완주 확인 (2026-03-04)

### 4.3 유지보수 안정성

- **SSOT 완료**: models.yaml (LLM 모델명), validation.yaml (임계값), prompts/*.yaml (43개)
- **DI 컨텍스트**: Stage2 43슬롯, Stage3 19슬롯, Stage4 24슬롯 (명시적 의존성 관리)
- **모듈 분할 완료**: stage4(-64%), chief_writer(-62%), stage2(-66%) — 파일당 900줄 이하

---

## 5. 독자 워크프레임의 취약점

LangGraph/LangChain 대비 실질적으로 불리한 점도 있다.

### 5.1 생태계 없음

- 커뮤니티 지원, Stack Overflow 답변, 서드파티 통합이 없다.
- 신규 기여자 온보딩 비용이 높다.
- 버그 발생 시 전적으로 내부 디버깅.

**완화**: CLAUDE.md + 참고자료.md + 상세한 코드 주석으로 인수인계 문서화 유지.

### 5.2 async/await 혼용

- Stage 2: asyncio 기반
- Stage 3/4: 동기 (threading)
- 혼용으로 인한 GIL 경합, 데드락 위험 잠재

**현황**: TF-7R 카오스 테스트 38개로 검증. 실운영에서 문제 미발생.

### 5.3 DI 컨텍스트 슬롯 수

- Stage2Context 43슬롯은 단위 테스트에서 mock 구성 비용이 높다.
- IDE 자동완성 지원이 LangChain의 typed 인터페이스 대비 약함.

**완화**: `__slots__` 사용으로 오타 방지, `from_app()` 팩토리 메서드로 구성 일관성 유지.

---

## 6. "LangGraph로 교체한다면?" 시나리오

만약 LangGraph로 교체한다면 어떤 비용이 발생하는가?

### 필수 재구현 항목

1. **WorldState / FactLedger** (장편 상태 추적): LangGraph State에 통합. 수백 줄 추가.
2. **NPC 이력 DB + 롤백 체인**: LangGraph 체크포인트 위에 별도 구현.
3. **BaseAgent 에러 복구 3-tier**: tenacity 등 라이브러리 조합 또는 재작성.
4. **6-Tier 검증 파이프라인**: LangGraph 노드로 표현 가능하나 상태 전달 복잡.
5. **Director 주권주의**: 조건부 엣지로 구현 가능하나 설계 철학 유지 어려움.
6. **도메인 특화 Advisory 7종**: LangGraph와 무관, 독자 구현 그대로 유지.

**결론**: 교체 후에도 글도비 고유의 비즈니스 로직은 독자 구현이 필수다. LangGraph는 "파이프라인 연결 레이어"만 담당하게 되므로, 추가 의존성 대비 실질적 이득이 없다.

---

## 7. 언제 LangGraph/LangChain을 선택해야 하는가

다음 조건이라면 LangGraph/LangChain이 유리하다:

- **단기 프로토타입**: 빠르게 개념 증명 필요 시
- **다양한 LLM 벤더 통합**: OpenAI + Anthropic + Gemini 동시 사용
- **Human-in-the-loop 표준화**: 중간 검토 포인트가 핵심인 워크플로우
- **팀 규모 대형**: 신규 개발자가 빠르게 온보딩해야 하는 환경

글도비는 위 조건에 해당하지 않는다. 단일 LLM 벤더(Gemini), 장편 상태 추적, 도메인 특화 검증이 핵심이다.

---

## 8. 최종 평가

**독자 워크프레임을 유지하는 것이 맞다.**

근거:

1. **도메인 특화 로직이 워크프레임보다 복잡하다.** LangGraph를 쓰더라도 글도비 고유 코드는 그대로다. 외부 프레임워크는 얇은 연결 레이어만 담당하게 된다.

2. **안정성 지표가 입증되어 있다.** 3,213개 테스트 통과, 6회 전수조사, 실파이프라인 검증 완료. LangGraph로 교체하면 이 안정성을 다시 증명해야 한다.

3. **외부 의존성 리스크 없음.** LangChain Breaking Change 이력을 고려하면, 의존성 추가 자체가 새로운 리스크다.

4. **유일한 실질적 약점은 생태계 부재다.** 이는 문서화(CLAUDE.md, 참고자료.md)와 테스트 커버리지로 완화 가능하다.

---

---

## 9. 독자 프레임워크의 실제 척할 (선례 사례)

"우리만 이러는 거 아닌가?" — 답은 **아니다**. 업계에서 LangChain/LangGraph를 버리고 독자 구현을 선택한 선례는 명확하게 존재한다.

---

### 9.1 Octomind — "우리가 LangChain을 더 이상 쓰지 않는 이유"

> HackerNews 480포인트, 업계에서 가장 많이 인용되는 탈-LangChain 사례

**회사**: Octomind (AI 테스트 자동화)
**결정**: LangChain 전면 제거 → 직접 API 호출 + 커스텀 오케스트레이션
**이유**:
- "작은 변경 하나에 5겹의 추상화를 뚫어야 한다"
- 표준 사용 케이스를 벗어나는 순간 복잡성이 폭발
- 디버깅 불가: 자체 스택을 매번 역공학해야 하는 상황

**결과**: 직접 API 호출 + 80줄 커스텀 코드로 필요한 기능 전부 대체. 프롬프트 엔지니어링 집중으로 품질 향상.

---

### 9.2 Klarna — 2.3백만 건 처리, 커스텀 AI 스택

**회사**: Klarna (핀테크, 스웨덴)
**결정**: 자체 AI 고객지원 파이프라인 구축 (LangChain 미사용)
**성과** (2024):
- 첫 달 고객지원 채팅의 2/3 자동 처리
- 2.3백만 건 대화 처리
- 평균 해결 시간: 11분 → 2분 이하
- 효과: FTE 700명분 업무 대체, 연간 $40M 이익 개선

**시사점**: 금융 도메인의 도메인 특화 요구사항 (규정 준수, 감사 추적, 상태 일관성)은 범용 프레임워크로 해결 불가능. 도메인 최적화 스택이 우월.

---

### 9.3 Intercom Fin — 평균 51% 자동 해결율, 자체 오케스트레이터

**회사**: Intercom (SaaS 고객지원)
**결정**: Fin AI Agent — 자체 멀티스텝 오케스트레이션 구현
**성과**:
- 평균 자동 해결율 51%
- Synthesia 사례: 6개월 1,300+ 지원 시간 절감, 6,000+ 대화 자동 처리
- 690% 트래픽 급등 시 98.3% 사용자 자체 해결

**시사점**: 장기 세션 추적, 장애 복원성, 엔터프라이즈 SLA 준수는 LangGraph로도 부족. 자체 구현이 필수.

---

### 9.4 엔터프라이즈 일반 — "커스텀이 더 싸다"

업계 분석(Ampcome, 2025):

> *"Banks, insurance firms, and healthcare giants rarely stick with LangChain for mission-critical systems. Enterprises often save millions over 3–5 years by eating the upfront custom engineering costs."*

이유:
- **프레임워크 오버헤드**: 모든 요청이 필요 없는 미들웨어·래퍼를 거침
- **벤더 락인**: LangChain이 특정 API에 의존하면 마이그레이션 비용 폭발
- **Breaking Change 누적**: LangChain v0.1→v0.2→v0.3 마이그레이션에 팀 전체가 수주를 소비한 사례 다수

---

### 9.5 엔지니어 컨센서스 — "그냥 Python이 낫다"

HackerNews 토론에서 수백 명의 엔지니어가 동의한 요점:

> *"LLM 앱의 본질은 문자열 처리 + API 호출 + 루프 + 벡터DB. Python 기본 기능으로 충분하다."*

구체적 맥락에서 커스텀이 우월한 경우:
- 에이전트 수가 적고 실행 흐름이 예측 가능한 파이프라인
- 에러 처리·재시도·타임아웃에 대한 완전한 제어가 필요한 경우
- 의존성 업그레이드 없이 장기 운영해야 하는 프로덕션 시스템

---

### 9.6 글도비의 위치 (척할 대비 평가)

| 기준 | Octomind | Klarna | 글도비 |
|------|----------|--------|--------|
| 탈-LangChain 이유 | 과도한 추상화 | 도메인 특화 | 도메인 특화 + 장편 상태 |
| 커스텀 코드 규모 | 소형 (80줄~) | 대형 (ML팀) | 중형 (3,213 테스트) |
| 검증 체계 | 미공개 | 미공개 | 공개 (6-Tier + PBT) |
| 롤백 | 미공개 | 미공개 | 명시적 (6소스 연계) |
| 도메인 특화 기능 | 테스트 자동화 | 금융 지원 | 웹소설 생성 |

**결론**: 글도비는 독자 프레임워크를 선택한 선례들과 동일한 이유(도메인 특화, 프레임워크 오버헤드 회피)로 커스텀 구현을 택했다. 오히려 검증 체계와 롤백 메커니즘은 알려진 선례보다 더 체계화되어 있다.

---

### 9.7 "서드파티 지원을 받고 싶다면"

독자 프레임워크의 유일한 실질적 약점인 생태계 부재를 완화하는 현실적 방법:

**지금 당장 적용 가능:**
1. **Pydantic** — 이미 사용 중. 스키마 검증의 업계 표준.
2. **SQLite + WAL** — 이미 적용. 프로덕션 검증된 스토리지.
3. **hypothesis (PBT)** — 이미 46개. 서드파티 검증 라이브러리 활용 중.
4. **pytest** — 이미 3,213개. 업계 표준 테스트 인프라.

**필요 시 점진적 도입 가능:**
- **Prometheus + Grafana**: 3-Obs에서 계측 포인트 이미 구현됨 → 메트릭 수출만 추가하면 됨.
- **OpenTelemetry**: BaseAgent ask() 호출에 trace_id 삽입으로 분산 추적 가능.
- **Temporal.io**: 장기 실행 워크플로우 상태 관리 (현재 SQLite로 충분하나 스케일업 시 선택지).

**LangGraph를 부분 도입하는 절충안:**
- Stage 2 Arc 생성의 `async` 루프를 LangGraph StateGraph로 교체 가능 (나머지 도메인 로직은 그대로).
- 이득: LangGraph의 체크포인트·Human-in-the-loop.
- 손실: 현재 WorldState/FactLedger SSOT와의 정합성 유지 비용 추가.
- **권고**: 현 단계에서는 ROI 없음. 팀 규모 확장 시 재검토.

---

*참고 파일*:
- `modules/domain/agents/base_agent.py` — 에러 복구 3-tier
- `modules/core/stage4_orchestrator.py` — 오케스트레이터 패턴
- `modules/core/stage2_context.py` / `stage4_context.py` — DI 컨텍스트
- `config/settings/validation.yaml` — 검증 임계값 SSOT
- `CLAUDE.md` — 대원칙 및 현황

---

*외부 참고*:
- [Why we no longer use LangChain for building our AI agents (HN)](https://news.ycombinator.com/item?id=40739982)
- [LangChain vs Custom Workflows — AI Agents Guide 2025](https://www.ampcome.com/post/langchain-vs-custom-workflows-ai-agents-2025)
- [The Langchain Dilemma: An AI Engineer's Perspective](https://medium.com/@neeldevenshah/the-langchain-dilemma-an-ai-engineers-perspective-on-production-readiness-bc21dd61de34)
- [AI Agents in Production 2025: Enterprise Trends](https://cleanlab.ai/ai-agents-in-production-2025/)
