# [D-T2] 미열거 에이전트 & 모델 계층 디테일 감사 보고서

> **터미널**: Terminal 2
> **작성일**: 2026-03-13
> **범위**: 미열거 Domain Agents 6개 + 모델 계층 5개 + base_agent.py Context Caching 디테일
> **방법**: 자체 3PASS 감리 (PASS1 초벌 → PASS2 교차검증 → PASS3 확정)

---

## 확정 발견사항

---

### [D-T2-01] P2 — Critic 에이전트: 인스턴스화만 되고 호출 없음 (Dead Agent)

**파일**: `modules/domain/agents/critic.py` (715줄)
**인스턴스화**: `main_a.py:1497`
```python
"critic": Critic(self.current_project, self.sys.api_client, model_tier=_SUMMARY_MODEL),
```

**증거**:
- `agents["critic"]` — 프로덕션 코드 전체 0건 (grep 확인)
- `critique_manuscript`, `deep_review`, `hybrid_review`, `generate_revision_feedback` 메서드 — 프로덕션 호출 0건
- 호출처: `critic.py` 자체 + `tests/test_protocols.py` + `modules/protocols/agents.py` (프로토콜 정의)만

**영향**:
- 불필요한 BaseAgent 인스턴스 1개가 매 실행마다 생성 (LLM 클라이언트, 모델 설정 등 초기화)
- 메모리 낭비 + agents dict 오염
- Critic의 기능(Python 패턴 매칭 비평)은 `chief_writer_quality.py` Self-Critique 15개 체크로 완전 대체된 것으로 추정

**수정안**: `main_a.py:1497` 삭제 또는 주석 처리. 테스트/프로토콜 참조도 정리.

---

### [D-T2-02] P2 — ArcCritic 에이전트: 인스턴스화만 되고 호출 없음 (Dead Agent)

**파일**: `modules/domain/agents/arc_critic.py`
**인스턴스화**: `main_a.py:1522`
```python
"arc_critic": ArcCritic(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
```

**증거**:
- `agents["arc_critic"]` — 프로덕션 모듈 전체 0건 (grep `modules/` 범위, tests 제외)
- `modules/core/` 및 `modules/domain/agents/` (agents 자체 제외) 어디에서도 호출 없음
- 호출처: tests (`test_sweep28.py`, `test_sweep31.py`, `test_protocols.py`) + `config_manager.py` (모델명 정의)만

**영향**: D-T2-01과 동일. 불필요한 LLM 에이전트 인스턴스.
- ArcCritic의 기능(Arc 품질 비평)은 `unified_arc_validator.py` + `consensus_validator.py` 앙상블로 완전 대체된 것으로 추정

**수정안**: `main_a.py:1522` 삭제 또는 주석 처리.

---

### [D-T2-03] P2 — RelationshipChange 모델: model_config 이중 선언

**파일**: `modules/models/arc.py:52, 61`
```python
class RelationshipChange(BaseModel):
    model_config = ConfigDict(extra="allow")          # L52 — 첫 번째 선언

    target: str = ""
    from_state: str = Field(default="", alias="from")
    to_state: str = Field(default="", alias="to")
    trigger: str = ""
    justification: str = ""

    model_config = ConfigDict(extra="allow", populate_by_name=True)  # L61 — 두 번째 선언 (이것이 실효)
```

**증거**:
- Python 클래스 속성은 후속 선언이 이전을 덮어쓴다
- L52의 `ConfigDict(extra="allow")`는 dead code — L61의 `ConfigDict(extra="allow", populate_by_name=True)`가 실효
- `populate_by_name=True`는 `alias="from"` 필드에서 `from_state`로도 접근 가능하게 하는 필수 설정

**영향**:
- 현재 동작에는 문제 없음 (L61이 올바른 설정)
- 단, 후임자가 L52만 보고 수정하면 L61이 여전히 덮어쓰므로 혼동 유발

**수정안**: L52 삭제 (L61만 유지)

---

### [D-T2-04] P3 — validate_npc_entry: 프로덕션 미사용

**파일**: `modules/models/npc.py:37-44`
```python
def validate_npc_entry(raw: dict) -> dict:
    try:
        npc = NPCEntry.model_validate(raw)
        return npc.model_dump()
    except Exception as e:
        logger.warning("[Pydantic] NPCEntry 검증 실패 — 원본 유지: %s", e)
        return raw
```

**증거**:
- 프로덕션 코드 import 0건 (grep 확인)
- 호출처: `tests/test_integrity.py:549,562` + `tests/test_pydantic_models.py:392,397`만
- NPCEntry 모델 자체는 정의되어 있지만, NPC 엔트리 검증 경로에서 이 함수를 거치지 않음
- NPC 데이터는 `state_tracker.py create_npc_entry()`에서 bare dict로 직접 생성

**영향**: 코드 부채. Pydantic 모델이 존재하나 ingress 검증이 연결되지 않음.
**수정안**: 향후 NPC 엔트리 생성 경로에 validate_npc_entry() 삽입 검토, 또는 사용하지 않을 시 명시적 주석.

---

### [D-T2-05] P3 — validate_blueprint_arc: 프로덕션 미사용

**파일**: `modules/models/arc.py:279-288`

**증거**:
- 프로덕션 코드 import 0건 (grep 확인)
- 호출처: `tests/test_pydantic_models.py:408,413`만
- Blueprint 경로에서 Arc의 StateConstraints만 검증하는 용도이나, 실제 Blueprint 파이프라인(`three_phase_blueprint_generator.py`)에서는 `validate_blueprint()`만 사용

**영향**: D-T2-04와 동일. 의도된 검증 함수이나 파이프라인에 미연결.

---

### [D-T2-06] P3 — Weaver: Gemini 전용 types 직접 사용 (멀티프로바이더 비호환)

**파일**: `modules/domain/agents/weaver.py:25, 59-69`
```python
from google.genai import types  # L25 (메서드 내 local import)

response = generate_content_via_router(
    client=self.client,
    model=self.primary_model,
    contents=dynamic_prompt,
    config=types.GenerateContentConfig(
        cached_content=self.cache_name,  # Gemini-only 파라미터
        temperature=0.5,
        ...
    ),
)
```

**증거**:
- `types.GenerateContentConfig(cached_content=...)` 는 Gemini API 전용
- 다른 에이전트들은 `BaseAgent.ask()` 또는 `_ask_with_cached_context()`를 통해 추상화됨
- Weaver만 `generate_content_via_router`에 직접 Gemini config를 전달

**오탐 검토**: CLAUDE.md "기본값: gemini=true, 나머지 false" — 현재 Gemini-only 운영이므로 즉각적 문제 없음.
**영향**: 멀티프로바이더 전환 시 Weaver가 깨질 수 있음. 향후 과제.

---

## 에이전트 생존 현황 요약

| 에이전트 | 인스턴스화 | 프로덕션 호출 | 상태 |
|---------|----------|-------------|------|
| ConsensusValidator | main_a.py:1524 | stage2 검증 파이프라인 | ✅ 활성 |
| ConstraintCompiler | main_a.py:1536, four_phase_arc_generator.py:438 | Arc 제약 컴파일 | ✅ 활성 |
| **Critic** | main_a.py:1497 | **없음** | ❌ Dead |
| Manager | main_a.py:1484 | stage4_post_processor.py:797,824 | ✅ 활성 |
| PreflightChecker | main_a.py:1518, four_phase_arc_generator.py:422 | stage2_preflight.py | ✅ 활성 |
| Weaver | main_a.py:1486 | stage2_preflight.py:512 | ✅ 활성 |
| **ArcCritic** | main_a.py:1522 | **없음** | ❌ Dead |

---

## 모델 계층 검증 현황

| 모델 | 정의 | validate 함수 | 프로덕션 사용 |
|------|------|-------------|-------------|
| ArcData | arc.py | validate_arc() | ✅ stage2_finalizer.py, four_phase_arc_generator.py |
| Blueprint | blueprint.py | validate_blueprint() | ✅ three_phase_blueprint_generator.py |
| ManuscriptCandidate | manuscript.py | validate_manuscript_candidate() | ✅ chief_writer.py:584 |
| NPCEntry | npc.py | validate_npc_entry() | ❌ 테스트만 |
| StateConstraints | arc.py | validate_blueprint_arc() | ❌ 테스트만 |

---

## 모델 스키마 ↔ DB ↔ LLM 3자 대응 검사

### ArcData 필드 대응 (핵심)
- `arc_no` / `ep_start` / `ep_end` → DB `arcs` 테이블 PK 대응 ✅
- `tactical_doc: str | dict` → LLM 응답에서 str 또는 dict 양쪽 수용 (`json.dumps` 폴백) ✅
- `state_constraints: dict` → Pydantic `StateConstraints` 모델로 하위 검증 가능하나 ingress에서 dict로 수용 ✅
- `protagonist_items` vs `items_acquired`: StateConstraints 모델에서 양쪽 모두 정의 (`protagonist_items: list[str]`, `items_acquired: list | None = None`) — CLAUDE.md 14파일 21곳 폴백 패턴과 일치 ✅
- `episode_details`: TF10-1-1 추가 필드, list[dict] 기본값 빈 리스트 ✅

### NPCEntry 필드 대응
- `name: str` (필수), `status: str = "alive"`, `deceased: bool = False`
- `death_arc: int | None` — 대원칙 4 (사망 캐릭터) 지원
- `last_arc: int = 0` — NPC 최근 등장 Arc 추적
- DB `npc_registry` 테이블과 정합 ✅

---

## base_agent.py Context Caching 디테일 분석

### 정상 동작 확인 항목
1. **캐시 무효화**: TTL 만료 시 로컬 dict에서 삭제 (L1788-1790) ✅
2. **Lock 보호**: `_cache_lock`으로 `_context_caches` 읽기/쓰기 보호 (L1781, L1814) ✅
3. **TOCTOU 방지**: `.get()` + `.pop()` 패턴으로 KeyError 방지 [I-20] ✅
4. **캐시 크기 제한**: `_CONTEXT_CACHE_MAX` 초과 시 LRU 삭제 (L1822-1826) ✅
5. **최소 콘텐츠 요건**: `_MIN_CACHE_CONTENT`(50,000자) 미달 시 캐싱 스킵 (L1795) ✅
6. **폴백**: 캐시 실패 시 비차단 + 캐시 없이 직접 진행 (L1832-1842) ✅
7. **키 전환**: 429/quota 감지 시 `_key_rotation_pending` 예약 (L1836-1839) ✅

### 캐시 삭제 수학 검증 (PASS2에서 오탐 확인)
```
조건: len > MAX (예: 51 > 50)
삭제: snapshot[:51-50] = snapshot[:1] → 1개 삭제 → 50개 남음 = MAX → 정확
```
오탐: off-by-one 없음.

### 잠재 비효율 (P3 수준, 수정 불요)
- Gemini API 캐시 생성이 Lock 밖에서 수행되어 동일 content에 대해 2개 thread가 동시에 캐시를 생성할 수 있음 → API 호출 낭비 가능
- 하지만 두 번째 thread의 결과가 metadata를 덮어쓰므로 데이터 정합성은 유지됨
- Gemini API 캐시는 TTL 만료 시 자동 삭제되므로 API 리소스 누수 없음

---

## constraint_compiler ↔ blueprint_constraint_compiler 역할 구분

| 항목 | ConstraintCompiler | BlueprintConstraintCompiler |
|------|-------------------|---------------------------|
| 파일 | constraint_compiler.py | blueprint_constraint_compiler.py |
| 범위 | **Arc 레벨** — 이전 Arc 전체의 아이템/수여물/상태 | **에피소드 레벨** — tactical_doc에서 해당 화 섹션 |
| 입력 | prev_arcs: list[dict] | arc_data: dict, ep_num: int |
| 출력 | MUST NOT DO / MUST DO / INHERITED STATE 텍스트 | MUST_FOCUS / STOP_LINE / CONTINUITY dict |
| 호출 | main_a.py, four_phase_arc_generator | three_phase_blueprint_generator |

**결론**: 역할 명확히 분리됨, 중복 없음 ✅

---

## Critic ↔ ArcCritic 역할 구분

| 항목 | Critic | ArcCritic |
|------|--------|-----------|
| 대상 | **원고** (manuscript) | **Arc** (arc design) |
| 방법 | Python 패턴 매칭 + 선택적 LLM | LLM 기반 비평 |
| 기능 | Show-Don't-Tell, 클리셰, 문장 다양성 등 6개 비평 | 아이템/위치/상태 연속성 + 구조 + 서사 10점 채점 |
| 상태 | **Dead** (Self-Critique로 대체) | **Dead** (앙상블 검증으로 대체) |

---

## 오탐 제거 로그

| ID | PASS1 후보 | PASS2 결과 | 사유 코드 |
|----|----------|----------|---------|
| FP-1 | Cache eviction off-by-one | **제거** | FP-2: 수학 검증으로 정확 확인 |
| FP-2 | Race condition causing invalid cache names | **제거** | FP-3: 호출자 추적 결과 두 thread 모두 유효한 cache name 생성 |
| FP-3 | Gemini API caches not deleted on eviction | **제거** | FP-1: TTL 자동 만료 설계 (CLAUDE.md "Context Caching TTL" 참조) |
| FP-4 | Error swallowing in cache creation | **제거** | FP-1: 비차단 진행 의도적 설계 (CLAUDE.md "비차단 갱신" 원칙) |
| FP-5 | Silent DB logging exceptions | **제거** | FP-5: V64.P4 에러 처리 정책 준수 |
| FP-6 | Weaver Gemini-only types usage | **P3으로 유지** | 현재 Gemini-only 운영이나 멀티프로바이더 전환 시 리스크 |
| FP-7 | ConstraintCompiler ↔ BlueprintConstraintCompiler 중복 | **제거** | FP-4: Arc 레벨 vs 에피소드 레벨, 역할 명확히 분리 |
| FP-8 | _SYSTEM_CFG YAML 타입 미검증 | **제거** | FP-2: 테스트 3,847건 통과 상태에서 안정 동작 확인 |

---

## 감리 통계

**PASS1**: 14건 후보 발견
**PASS2**: 8건 오탐 제거 (FP-1~FP-8)
**PASS3**: **6건 확정** (P2: 3건, P3: 3건)

- P0: 0건
- P1: 0건
- P2: 3건 (D-T2-01 Critic dead, D-T2-02 ArcCritic dead, D-T2-03 model_config 중복)
- P3: 3건 (D-T2-04 validate_npc_entry 미사용, D-T2-05 validate_blueprint_arc 미사용, D-T2-06 Weaver Gemini 전용)
