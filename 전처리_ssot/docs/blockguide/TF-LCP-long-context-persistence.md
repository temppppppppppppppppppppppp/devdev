# TF-LCP: 토큰 한계 중장기 프로젝트 연속 진행 전략

<!-- utf8-hygiene: allow-file rationale: this persistence note intentionally includes literal stop-gate tokens and source URLs with query strings as reference examples. -->

> 상태: **CONFIRMED** (3-Pass 감리 완료 2026-03-12)
> 감리 결과: P1 3건 수정, P2 2건 수정, MINOR 1건 수용
> 트리거: TF-OBP 작성 중 "컨텍스트 윈도우 근인"에 대한 구조적 대응 필요성 도출
> 범위: 글도비 SSOT 블록 생산뿐 아니라, LLM 기반 중장기 프로젝트 전반

---

## 0. 글도비 파이프라인 구조

```
┌─────────────────────────────────────────────────────┐
│  전처리 (수동 LLM 대화, Python 파이프라인 밖)           │
│  ─────────────────────────────────────                │
│  컨셉기획.md → Phase 0 설계 → TR 70블록 + BI 블록      │
│  (사람 + LLM이 대화하며 생산)                           │
│                                                       │
│  산출물:                                               │
│   treatments/ → TR JSON (시놉시스 블록)                 │
│   bible/      → BI JSON (세계관·설정 블록)              │
└──────────────────────┬──────────────────────────────┘
                       ↓ 전처리 산출물이 본 파이프라인의 입력
┌─────────────────────────────────────────────────────┐
│  본 파이프라인 (Python 자동화, main_a.py)               │
│  ──────────────────────────                           │
│  BI/TR 읽기 → Bible 파싱(NPC 등록, 세계관 추출, 문체)   │
│            → Arc (Analyst → 앙상블 → 검증)              │
│            → Blueprint (Stage 3)                       │
│            → Manuscripts (ChiefWriter → Director 심사)  │
└─────────────────────────────────────────────────────┘
```

**전체 흐름 한 줄 요약:** `BI, TR (전처리) → Bible → Arc → Blueprint → Manuscripts (본 파이프라인)`

**핵심 구분:**
- **전처리(TR/BI 생산):** LLM과 사람이 대화하며 수동 생산. SSOT 하네스가 규칙을 정의하지만, 실행은 대화형 LLM이 담당. **이 문서(TF-LCP)의 주 대상.**
- **본 파이프라인(Bible→Arc→Blueprint→Manuscripts):** Python이 자동 실행. 컨텍스트 캐싱, RAG, 계층적 요약 등이 코드로 구현됨. 토큰 관리가 이미 내장되어 있어 이 문서의 대상이 아님.

**토큰 문제가 발생하는 곳:** 전처리 단계. TR 70블록 + BI를 한 세션에서 순차 생산할 때 출력 상한과 컨텍스트 윈도우 양쪽에서 병목이 발생한다.

---

## 1. 문제 정의: 두 가지 토큰 병목

| | 출력 상한 (Output Limit) | 컨텍스트 윈도우 (Context Window) |
|---|---|---|
| 제약 | 한 응답에 쓸 수 있는 토큰 | 입력+출력 전체 기억 용량 |
| 증상 | 응답 중간에 끊김 | 앞쪽 규칙/블록을 잊어버림 |
| 위험 | auto-run 위반 (멈춤) | SSOT 규칙 망각, 블록 품질 저하, 일관성 붕괴 |
| 해결 문서 | **TF-OBP** (작성 완료) | **이 문서 (TF-LCP)** |
| 근본 해결 | 불가 (모델 물리 한계) | 불가 (모델 물리 한계) |
| 우회 전략 | state 파일 + 자동 재개 | 아래 §2~§5 참조 |

---

## 2. 현재 활용 가능한 전략 (2026-03 기준)

### 2.1 Gemini 컨텍스트 캐싱

**두 가지 모드:**

| | Explicit Caching | Implicit Caching |
|---|---|---|
| 설정 | `client.caches.create()` + TTL | 자동 (코드 변경 없음) |
| 최소 크기 | 32K 토큰 | Flash 1,024 / Pro 2,048 토큰 |
| 비용 할인 | 읽기 90% (Gemini 2.5) | 동일 |
| 제어 | TTL 수동 연장 가능 | 불가 |
| 적합 용도 | 바이블/세계관 등 고정 컨텍스트 | 반복 prefix 자동 절감 |

**글도비 본 파이프라인:** 5개 에이전트에서 Explicit Caching 사용 중 (600s/1800s TTL). Implicit은 기본 활성화.
**전처리 적용 가능성:** 전처리는 대화형 LLM 세션이므로 API 캐싱과 무관. 다만 Gemini API로 전처리를 자동화할 경우(§2.6) Explicit Caching이 유효.

**참고:** 컨텍스트 캐싱은 **비용 절감** 도구이지 **컨텍스트 윈도우 확장** 도구가 아님. 캐시된 토큰도 윈도우를 점유한다.

### 2.2 계층적 요약 압축 (Hierarchical Summarization)

```
최근 블록 (3~5개)   → 원문 그대로 유지
중간 블록 (6~20개)  → 블록당 1~2줄 요약
초반 블록 (21개+)   → 아크 단위 3줄 요약
SSOT 규칙           → 항상 원문 유지 (압축 대상 아님)
```

**핵심 원칙:** "무엇을 넣느냐"가 아니라 "무엇을 버리느냐"가 품질을 결정.

**글도비 본 파이프라인:** ChainLink → VolumeSummary → SeriesSummary 3계층 요약 피라미드가 Stage 4에서 자동 동작.
**전처리 적용:** 전처리에서는 LLM이 직접 이 압축을 수행해야 함. §4 Document & Clear에서 state 파일이 이 역할을 대신한다.

### 2.3 Document & Clear 패턴 (대화형 LLM용)

수동 블록 생산(TR/BI) 시 가장 실전적인 패턴:

```
1. 블록 N개 생산
2. 현재 상태를 state 파일에 기록 (production_state.json)
3. /clear 또는 새 세션 시작
4. 새 세션에서 state 파일 + SSOT + 직전 블록만 로드
5. 블록 N+1부터 재개
```

**장점:** 컨텍스트 윈도우를 매번 깨끗하게 리셋. SSOT 규칙이 항상 "가까이" 있어 망각 없음.
**단점:** 세션 전환 오버헤드. 자동화 어려움 (채팅 환경).
**적용처:** Claude Code(`/clear`), Gemini Web UI, ChatGPT 등 대화형 인터페이스.

### 2.4 서브에이전트 위임 (Claude Code 전용)

```
메인 세션: SSOT 규칙 + 지휘만 유지
서브에이전트 1: Block 1~10 생산 → 결과 파일만 반환
서브에이전트 2: Block 11~20 생산 → 결과 파일만 반환
...
```

**장점:** 메인 세션 컨텍스트가 오염되지 않음. 병렬화 가능.
**단점:** 서브에이전트 간 연속성 보장이 어려움 (NPC 추적, 복선 관리). 서브에이전트도 동일한 토큰 한계를 가짐.
**적합 조건:** 블록 간 의존성이 낮은 작업 (예: 독립적 BI 블록 생산). TR은 순차 의존성이 높아 부적합.

### 2.5 RAG + 압축 하이브리드

```
고정 컨텍스트 (SSOT 규칙, 바이블)  → 항상 주입
가변 컨텍스트 (이전 블록, NPC 상태) → RAG 검색으로 필요분만 주입
Tool 출력 (감리 결과, 차이 행렬)    → 인라인 압축
```

**글도비 본 파이프라인:** Smart Context Retrieval(`context_advisor.py`)이 Stage 4에서 수행.
**전처리 적용:** 전처리에서는 LLM이 Phase 0 설계 + 직전 블록만 참조하면 되므로 RAG가 불필요. state 파일의 NPC/복선 추적이 충분.

### 2.6 상태 머신 (State Machine) 패턴

```python
# 개념적 구조
state = load_state("production_state.json")
while state.next_block <= 70:
    if state.blocks_in_current_order >= 5:
        break  # fresh order required
    prompt = build_prompt(ssot_rules, state, last_block)
    response = llm.generate(prompt)
    block = parse_block(response)
    save_block(block)
    state.advance(block)
    save_state(state)
```

**장점:** 각 LLM 호출이 독립적. 컨텍스트 윈도우 문제 원천 제거.
**단점:** "대화의 흐름" 없이 매번 cold start. 블록 간 톤/스타일 일관성 저하 가능.
**프레임워크:** LangGraph (체크포인트 + 그래프 기반), llmstatemachine (경량).

---

## 3. 전략별 적합성 평가 (전처리 TR/BI 수동 생산 기준)

| 전략 | 전처리 구현 난이도 | 연속성 보장 | 자동화 가능 | 전처리 ROI |
|------|-------------------|------------|------------|-----------|
| 2.1 컨텍스트 캐싱 | 해당 없음 (API용) | 비용만 절감 | — | 전처리 무관 |
| 2.2 계층적 요약 | state 파일로 대체 | ⭐⭐⭐ | 수동 | state 파일이 담당 |
| **2.3 Document & Clear** | **낮음** | **⭐⭐⭐⭐** | **반자동** | **★ 최고** |
| 2.4 서브에이전트 | 중간 | ⭐⭐ | ✅ | TR 부적합 |
| 2.5 RAG 하이브리드 | 해당 없음 (API용) | ⭐⭐⭐ | — | 전처리 무관 |
| 2.6 상태 머신 | 높음 | ⭐⭐⭐⭐⭐ | ✅ | 과잉 |

**결론:**
- **본 파이프라인(Stage 0→2→4):** 2.1/2.2/2.5가 이미 코드로 구현됨. 추가 조치 불필요.
- **전처리(TR/BI 수동 생산):** **2.3 Document & Clear**가 유일한 실전 대응. 나머지는 이미 적용됐거나 과잉이거나 부적합.

---

## 4. Document & Clear 실행 규약

### 4.1 언제 Clear하는가

- **Claude Code:** 컨텍스트 사용량 60% 초과 시 (자동 compaction 전에 선제 clear)
- **채팅 UI:** 같은 운영 오더에서 5블록 생산 후 또는 그 이전 아크 경계에서
- **판단 기준:** "SSOT 규칙을 아직 기억하고 있는가?" — 기억 못 하면 즉시 clear

### 4.2 Clear 전 저장할 것

`production_state.json` (TF-OBP §3.1과 동일 포맷) + 아래 추가:

```json
{
  "clear_reason": "context_60pct",
  "ssot_rules_hash": "sha256 of SSOT docs (integrity check)",
  "critical_rules_reminder": [
    "auto-run: 정지 게이트 아닌 한 멈추지 않음",
    "1턴 1단위: 블록 1개 + 감리 1회",
    "정지 게이트 7개: UTF-8/???/P0/연속성/감리부재/seed혼동/사용자정지"
  ]
}
```

### 4.3 Clear 후 새 세션 시작 프롬프트

```
다음 파일을 읽고 {work_name} TR 블록 생산을 재개하라:
1. 전처리_ssot/docs/blockguide/SSOT_blockguide-integrated-order.md (전체 규칙)
2. 전처리_ssot/docs/blockguide/treatment-production-harness-v2.md (생산 하네스)
3. treatments/{work_id}_production_state.json (현재 상태)
4. treatments/{work_id}_block_{last}_candidate.json (직전 블록)
5. treatments/{work_id}_phase0_design.json (Phase 0 설계)

상태 파일의 next_block부터 즉시 생산 시작. 단, 같은 운영 오더의 5블록 창이 이미 소진됐으면 fresh order를 먼저 받는다. "계속할까요?" 금지.
```

### 4.4 Claude Code 전용: 컨텍스트 관리

**`/compact` vs `/clear` 구분:**
- `/compact`: 대화를 요약 압축. 세션 유지. SSOT 규칙이 요약 과정에서 손실될 수 있음.
- `/clear`: 세션 완전 리셋. SSOT 규칙 손실 없음 (새 세션에서 재로드).

**권장:** 전처리 블록 생산에서는 **`/clear` + 재로드**(§4.3)를 사용. `/compact`는 SSOT 규칙 변형 위험이 있어 비권장.

```
# CLAUDE.md 규칙 예시:
# "TR/BI 수동 생산 중 컨텍스트 60% 초과 시:
#  1. production_state.json 저장
#  2. /clear 실행
#  3. §4.3 프롬프트로 state 파일 + SSOT + 직전 블록 재로드
#  4. 즉시 재개"
```

---

## 5. Google Workspace 활용 가능성 평가

### 5.1 Google Apps Script CLI (clasp)

**결론: 부적합.**
- 실행 시간 제한 6분 (Enterprise도 30분)
- PropertiesService 500KB 저장 한계
- LLM 오케스트레이션 도구가 아니라 배포 도구

### 5.2 Google Workspace Studio (2025.11~)

**결론: 관찰 단계.**
- 코드 없이 AI 에이전트 생성 가능한 플랫폼
- Gemini 3 Pro 통합, Gmail/Calendar/Drive 연동
- 글도비 파이프라인과의 접점: 생산된 블록을 Google Docs로 자동 내보내기, 감리 결과를 Sheets에 기록 등 **후처리 자동화**에 한정
- 블록 생산 자체의 토큰 문제 해결과는 무관

### 5.3 Gemini API 직접 활용 (상태 머신)

**결론: ROI 미확정.**
- Gemini 1M+ 컨텍스트면 TR 70블록 전체 히스토리를 넣을 수 있음
- 그러나 글도비 TR 생산은 Python 자동화 대상이 아닌 **수동 LLM 대화** 영역
- 자동화하려면 상태 머신 + API 호출 파이프라인 신규 개발 필요 → 과잉

---

## 6. 에이전트 프레임워크 비교 (참고)

| 프레임워크 | 상태 관리 | 체크포인트 | 글도비 적합성 |
|---|---|---|---|
| **LangGraph** | State + Reducer + Graph | 매 스텝 자동 + DB 영속 | 가장 유사하나 마이그레이션 비용 과대 |
| **CrewAI** | 역할 기반 메모리 | RAG 기반 | 프로토타이핑용, 프로덕션 부적합 |
| **AutoGen** | 대화 히스토리 | 벡터 스토어 | 멀티에이전트 대화에 특화, 순차 생산 부적합 |
| **Google ADK** | Gemini 네이티브 | 미확인 | 2026 신규, 아직 성숙도 낮음 |

**글도비 본 파이프라인:** Stage2Context/Stage3Context/Stage4Context DI 패턴이 LangGraph State와 유사한 역할 수행. SQLite SSOT(`project_data.db`)가 사실상의 체크포인트.
**전처리:** 이 프레임워크들은 전처리(수동 대화)에 적용할 수 없음. 전처리의 상태 관리는 `production_state.json` + 블록 JSON 파일이 담당.

---

## 7. 최종 권고

### 즉시 적용 (비용 0)
1. **TF-OBP** 적용 — 출력 상한 대응 (이미 완료)
2. **Document & Clear** 규약 — 수동 생산 시 §4.3 프롬프트 사용

### 본 파이프라인 중기 검토 (전처리와 무관, ROI 미확정)
3. Gemini Implicit Caching 효과 측정 — `cached_content_token_count` 모니터링
4. Analyst 에이전트 Explicit Caching 적용 (OPT-1, MEMORY.md 기록됨)

### NO-GO (과잉)
5. ~~LangGraph 마이그레이션~~ — 글도비 자체 DI + SQLite가 이미 동등 기능
6. ~~Google Workspace CLI(clasp) 통합~~ — 실행 시간 제한 + 목적 불일치
7. ~~상태 머신 API 자동화~~ — TR 수동 생산의 자동화 ROI 불명확

---

## 부록: 출처

### 영문
- [Gemini Context Caching (Google)](https://ai.google.dev/gemini-api/docs/caching)
- [Gemini Long Context Guide](https://ai.google.dev/gemini-api/docs/long-context)
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [5 Approaches to Solve LLM Token Limits (Deepchecks)](https://www.deepchecks.com/5-approaches-to-solve-llm-token-limits/)
- [Overcoming Output Token Limits (Medium)](https://medium.com/@gopidurgaprasad762/overcoming-output-token-limits)
- [Context Engineering for AI Agents (Weaviate)](https://weaviate.io/blog/context-engineering)
- [Claude Code Tasks (VentureBeat)](https://venturebeat.com/orchestration/claude-codes-tasks-update)
- [StateFlow Paper (arXiv)](https://arxiv.org/html/2403.11322v1)
- [clasp GitHub](https://github.com/google/clasp)

### 한국어
- [LLM 토큰 예산 운영 (Articul8)](https://www.mfitlab.com/articul8/blog-post/llm-token-budget-operations)
- [RAG 청킹 전략 2026 (youngju.dev)](https://www.youngju.dev/blog/llm/2026-03-04-llm-rag-chunking-embedding-optimization-2026)
- [AI 웹소설 요약집 패턴 (DC갤러리)](https://gall.dcinside.com/mgallery/board/view/?id=aiwriter&no=3708)
- [구글 워크스페이스 스튜디오 (AI타임스)](https://www.aitimes.com/news/articleView.html?idxno=204509)
- [Claude Code 대화 길이 해결 7가지 (retn.kr)](https://retn.kr/blog/claude-maximum-conversation-length/)
- [LLM Agent Framework 비교 2026 (youngju.dev)](https://www.youngju.dev/blog/llm/2026-03-09-llm-agent-framework-autogen-crewai-langgraph-comparison)
- [멀티턴 컨텍스트 압축 전략 2026 (youngju.dev)](https://www.youngju.dev/blog/chatbot/2026-03-04-chatbot-multi-turn-context-management-2026)
