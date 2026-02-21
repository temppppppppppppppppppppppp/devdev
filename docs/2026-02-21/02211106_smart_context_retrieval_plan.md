# Smart Context Retrieval 설계 문서

> 작성일: 2026-02-21 11:06 (rev.2 — Codex TF 피드백 반영)
> 상태: 설계 완료, 구현 대기
> 기준 커밋: `2a8a158` (2026-02-21, `feat(context): Gemini 컨텍스트 활용률 대폭 확대`)
> 선행 조건: Memory ROI P0-4 (검색 개수 상향)
> 테스트 기준: CI 최신 기준 (CLAUDE.md 기록: 2,114 passed + 68 xfailed)

---

## 1. 배경

현재 시스템은 컨텍스트를 대부분 **정적으로 조립**한다.

| Stage | 현재 벡터 검색 | 문제점 |
|-------|---------------|--------|
| Stage 2 (Arc 기획) | `block_theme` 단일 쿼리 (`stage2_preflight.py` L466) | 테마 하나로만 검색, NPC/플롯 맥락 누락 |
| Stage 4 (원고 집필) | prev_ending + NPC names + arc_tactical + 장르 키워드 (`stage4_context_builder.py` L418-456) | 기존 다중 쿼리 있으나 우선순위/예산 없음 |
| Director (감리) | **벡터 검색 없음** | 연속성 검사 시 벡터 메모리 미활용 |

컨텍스트 예산(80,000자) 대비 **~38%만 사용 중**이어서 62%의 여유가 있다.

**목표**: 에이전트가 현재 상황(에피소드, 아크, NPC, 장면)에 맞게 **알아서** 필요한 과거 정보를 가져오도록 만들기.

---

## 2. 이미 완료된 항목 (중복 작업 방지)

| 항목 | 코드 위치 | 상태 |
|------|----------|------|
| P0-1 distance-first selection | `vec_memory.py:369` | **구현 완료** |
| P0-2 keyword fallback | `vec_memory.py:315, 359` | **구현 완료** |
| P0-3 4-slot 요약 정규화 | `stage4_post_processor.py:171-192` | **구현 완료** (사건\|인물\|장소\|결말) |
| B3 arc bonus | `vec_memory.py:372-377` | **구현 완료** (×0.9 거리 보너스) |
| B5 similarity score exposure | `vec_memory.py:397` | **구현 완료** |
| Director 연속성 검사 (LLM) | `director_continuity.py:664` + `stage4_interview_round.py:416, 458` | **기존 작동 중** |

---

## 3. 아키텍처: 하이브리드 ContextAdvisor

### 핵심 설계 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 기본 엔진 | **Python 휴리스틱** | $0, <5ms, 결정론적 |
| 특수 상황 | **LLM (Gemini Flash)** | arc 경계/NPC 5+/REJECT 재시도에서만 |
| 신규 모듈 vs 기존 확장 | **새 모듈** + 기존 경로 확장 | Director는 기존 경로에 컨텍스트 주입, Stage 2/4는 기존 쿼리 체계화 |
| 설정 위치 | `validation.yaml` | 기존 `_threshold()` 패턴 |

### 데이터 모델

```python
@dataclass
class RetrievalSlot:
    category: str       # "npc_history", "scene_context", "arc_continuation", ...
    query: str          # 실제 검색 텍스트
    source: str         # "vec_memory" | "db_npc_history" | "reference_anchor"
    priority: int       # 1=필수, 2=중요, 3=있으면 좋음
    max_chars: int      # 이 슬롯의 결과 최대 길이

@dataclass
class RetrievalPlan:
    stage: str
    episode_num: int
    slots: list[RetrievalSlot]
    total_budget_chars: int
    used_llm: bool      # LLM 판단 사용 여부 (관측용)
```

### 클래스 구조

```python
class ContextAdvisor:
    # 공개 API
    def plan_stage2_retrieval(self, arc_data, current_ep, npc_roster) -> RetrievalPlan
    def plan_stage4_retrieval(self, arc_data, blueprint, prev_ending, current_ep, npc_roster, genre) -> RetrievalPlan
    def plan_director_retrieval(self, manuscript, blueprint, current_ep, npc_roster) -> RetrievalPlan

    # 내부 하이브리드 엔진
    def _heuristic_plan(self, stage, context_data) -> RetrievalPlan   # Python 규칙 (기본)
    def _llm_enrich_plan(self, base_plan, context_data) -> RetrievalPlan  # LLM 보강 (특수)
    def _should_use_llm(self, stage, context_data) -> bool  # LLM 필요 판단

class ContextBudgetTracker:
    def register_section(self, name: str, content: str) -> None
    def get_usage_report(self) -> dict
    def get_compression_targets(self) -> list[str]
```

### LLM 호출 트리거 조건 (`_should_use_llm`)

조건부만. "항상"은 없음:

1. **Arc 전환점** (첫/마지막 에피소드): 복선 회수/설정 집중 구간
2. **NPC 5명 이상 동시 등장**: 복잡한 관계 그래프
3. **이전 에피소드 REJECT 후 재작성**: 실패 원인 맞춤 쿼리 필요
4. **Director 감리도 위 3조건 해당 시만** (기존 LLM 연속성 검사와 중복 방지)

**LLM 사양**: Gemini Flash (~$0.005/call), 10초 타임아웃, JSON 응답, 실패 시 Python 폴백 보장

---

## 4. Phase별 구현 계획

### Phase SC-0: Memory ROI 잔여분 (0.5일)

**SC-0a: P0-3 테스트 보강** (구현은 완료됨)
- `stage4_post_processor.py` L171-192에 4-slot 요약 이미 구현
- 할 일: 엣지 케이스 테스트 추가 (빈 blueprint, entity 없음 등)
- `tests/test_stage4_post_processor.py`

**SC-0b: P0-4 검색 개수 상향**
- `config/settings/validation.yaml` L63-64:
  - `vector_max_results_s4`: 12 → 16
  - `vector_max_results_s2`: 8 → 12

---

### Phase SC-1: ContextAdvisor 코어 — 하이브리드 (1.5일)

**새 파일**: `modules/core/context_advisor.py` (~400줄)

**Stage 4 쿼리 계획화**:
- 기존 다중 쿼리(`stage4_context_builder.py` L418-456)를 RetrievalSlot으로 래핑 + 우선순위/예산 할당
- 추가 슬롯 (기존에 없는 것만):
  1. **장면별 쿼리**: blueprint `scene_breakdown`에서 장면 목표 키워드 추출
  2. **NPC 이력 쿼리**: 등장 NPC별 최근 행적 (SC-2의 `retrieve_npc_context` 활용)
  3. **미해결 복선 쿼리**: state_tracker의 plot_suspension 관련 에피소드
  4. **관계 변화 쿼리**: relationship_changes에서 해당 NPC 쌍의 과거

**Stage 2 쿼리** (기존 1개 → 최대 5개):
1. `block_theme` (기존)
2. 과거 Arc 유사 테마
3. 배정 NPC들의 최근 등장 에피소드
4. 미해결 플롯 관련 에피소드
5. Arc tactical 키워드

**Director 쿼리** (기존 0개 → 최대 5개):
1. 원고 내 NPC → 과거 에피소드
2. 사건 주장 → 검증
3. 관계 상태 일관성
4. 위치/아이템 일관성
5. blueprint vs 원고 연결

**설정 추가** (`validation.yaml`):
```yaml
smart_retrieval:
  enabled: true
  stage2_enabled: true
  stage4_enabled: true
  director_enabled: true
  max_queries_per_plan: 8
  stage4_total_budget: 50000
  stage2_total_budget: 20000
  director_total_budget: 20000
```

**테스트**: `tests/test_context_advisor.py` (~200줄)

---

### Phase SC-2: NPC-Aware Retrieval (0.5일)

**`vec_memory.py`** — 새 메서드:
```python
def retrieve_npc_context(self, npc_names: list[str], current_ep: int, max_results: int = 5) -> str:
```
- `episode_meta.entity_names`에서 NPC 이름 LIKE 검색 + 벡터 결합

**`db_manager.py`** — 새 메서드:
```python
def get_npc_recent_episodes(self, npc_name: str, before_ep: int, limit: int = 5) -> list[int]:
```

---

### Phase SC-3: Stage 4 통합 (1일)

**`stage4_context_builder.py`** L418-456 교체:
- `_execute_retrieval_plan(plan)` 메서드 — RetrievalSlot별 소스 디스패치
- **폴백**: `if self.ctx.context_advisor` → advisor 없으면 기존 코드 그대로

**`stage4_context.py`** — `__slots__`에 `"context_advisor"` 추가 + `from_app()` (L128)에 `context_advisor=getattr(app, "context_advisor", None)` 추출 라인 추가
  > 참고: `from_app()`은 context 클래스의 classmethod. 오케스트레이터(`stage4_orchestrator.py:184`)는 `Stage4Context.from_app(self.app)`을 호출만 하므로 변경 불필요.

**ContextBudgetTracker** 통합:
- 예산 초과 시 `ContextCompressor._smart_trim()` 적용 (기존 dormant 모듈 활성화)
- 로그: `[SC] Context budget: {used}/{total} ({pct}%)`

---

### Phase SC-4: Stage 2 통합 (0.5일)

**`stage2_preflight.py`** L463-472 교체:
- 기존 단일 `retrieve_high_res_context()` → ContextAdvisor plan 기반
- 폴백: advisor 없으면 기존 코드

**`stage2_context.py`** — `__slots__`에 `"context_advisor"` 추가 + `from_app()` (L200)에 `context_advisor=getattr(app, "context_advisor", None)` 추출 라인 추가
  > 참고: Stage 4와 동일 패턴. 오케스트레이터(`stage2_orchestrator.py:48`)는 `Stage2Context.from_app(self.app)` 호출만 하므로 변경 불필요.

---

### Phase SC-5: Director 기존 경로에 벡터 메모리 주입 (0.5일)

**신규 패스 추가 아님 — 기존 경로 확장.**

`stage4_interview_round.py` L416, L458에서 이미 연속성/히스토리 충돌 검사가 LLM 기반으로 돌고 있음. 새 메서드를 만들면 LLM 호출 중복.

**접근**: 기존 `check_manuscript_continuity_with_cache()`에 벡터 검색 결과를 컨텍스트로 주입.

- **`director_continuity.py`** L664 — optional `memory_context: str = ""` 파라미터 추가
- 기존 LLM 프롬프트에 `[벡터 메모리 참고]\n{memory_context}` 섹션 추가 (있을 때만)
- **LLM 호출 횟수 변화 없음** — 기존 1회 호출에 컨텍스트만 풍부해짐

- **`stage4_interview_round.py`** L416 부근 — 연속성 검사 전 벡터 검색 결과 조립 + `memory_context`로 전달
- ContextAdvisor `_should_use_llm()` → Director도 조건부만: arc 경계 / REJECT 재시도 / NPC 5+

---

### Phase SC-6: 관측성 + 피처 플래그 (0.5일)

- `validation.yaml`의 `smart_retrieval.enabled` 마스터 스위치
- 모든 통합 지점에 `_threshold("smart_retrieval.enabled", False)` 폴백
- 메트릭 로깅: 쿼리 수, 결과 수, 예산 사용률, 압축 여부, LLM 사용 여부

---

## 5. 의존 관계

```
SC-0 (P0 잔여)
  ↓
SC-1 (ContextAdvisor 코어)
  ↓
SC-2 (NPC-Aware) ─────────────────┐
  ↓                                ↓
SC-3 (Stage4 통합) ──────→ SC-6 (관측성+플래그)
  ↓
SC-4 (Stage2 통합)
  ↓
SC-5 (Director 검색)
```

**총 예상**: ~5일

---

## 6. 수정 파일 목록

| 파일 | 변경 | Phase |
|------|------|-------|
| **CREATE** `modules/core/context_advisor.py` | ContextAdvisor + BudgetTracker (~400줄) | SC-1 |
| **CREATE** `tests/test_context_advisor.py` | 단위 테스트 (~200줄) | SC-1 |
| `modules/core/vec_memory.py` | `retrieve_npc_context()` 추가 (~50줄) | SC-2 |
| `modules/core/db_manager.py` | `get_npc_recent_episodes()` 추가 (~20줄) | SC-2 |
| `modules/core/stage4_context_builder.py` | L418-456 교체 + `_execute_retrieval_plan()` | SC-3 |
| `modules/core/stage4_context.py` | `__slots__` + `from_app()`에 `context_advisor` 추가 (L128) | SC-3 |
| `modules/core/stage2_preflight.py` | L463-472 교체 | SC-4 |
| `modules/core/stage2_context.py` | `__slots__` + `from_app()`에 `context_advisor` 추가 (L200) | SC-4 |
| 앱 초기화 코드 | `app.context_advisor = ContextAdvisor(...)` 등록 | SC-3 |
| `modules/domain/agents/director_continuity.py` | `memory_context` 파라미터 추가 (~20줄) | SC-5 |
| `modules/core/stage4_interview_round.py` | 벡터 검색 결과 조립 + 전달 (~15줄) | SC-5 |
| `config/settings/validation.yaml` | `smart_retrieval` 섹션 + P0-4 상향 | SC-0, SC-6 |
| `tests/test_stage4_post_processor.py` | P0-3 엣지 케이스 테스트 보강 | SC-0 |

---

## 7. 리스크 완화

| 리스크 | 대책 |
|--------|------|
| 쿼리 증가 → 지연 | 최대 8쿼리 캡 + ThreadPoolExecutor 병렬 |
| 컨텍스트 비용 증가 | BudgetTracker + ContextCompressor 자동 트리밍 |
| Director 오경고 | advisory only — 자동 REJECT 안 함 (Director 주권) |
| Director LLM 중복 호출 | 기존 `check_manuscript_continuity_with_cache()` 확장, 신규 패스 없음 |
| 회귀 테스트 깨짐 | 모든 통합점 `if advisor else 기존코드` 폴백 + feature flag off |
| LLM Advisor 비용 | Flash ~$0.005/call, 조건부만 → 에피소드 평균 ~$0.003 추가 |
| LLM 응답 파싱 실패 | `_safe_json_loads` + 10초 타임아웃 → Python 폴백 |

---

## 8. 검증 방법

1. `pytest tests/test_context_advisor.py tests/test_vec_memory.py -v`
2. `pytest tests/ -q` — 2,114 passed + 68 xfailed 유지 (기준: `2a8a158`, CLAUDE.md 기록)
3. `smart_retrieval.enabled: false`로 전환 → 기존 동작 확인
4. Stage2→4 1에피소드 생성 → `[SC]` 로그로 쿼리 수/예산 사용률 확인
5. `ruff check modules/core/context_advisor.py` — 0 violations

---

## 9. 후속 계획과의 연계

| 계획 | 관계 |
|------|------|
| **Hybrid Retrieval** (`codex_hybrid_retrieval_refactor_plan.md`) | SC 완료 후 후속. `_execute_retrieval_plan()`에서 `retrieve_hybrid_context()`로 1줄 전환 가능 |
| **Canon OS v2** (`codex_canon_os_v2_plan.md`) | 장기 백로그. 현재 NPC history + ContextAdvisor로 80% 커버 |
| **Memory ROI D1~D5** (`codex_memory_roi_boost_plan.md`) | D1(hybrid)은 후속, D4(budget-aware)는 SC-6 BudgetTracker로 흡수 |
