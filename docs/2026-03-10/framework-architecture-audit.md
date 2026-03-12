# 글도비 워크프레임 아키텍처 감사

> 일자: 2026-03-10
> 방법: 6영역 에이전트 스캔 → 3-pass 감리 (수치 팩트체크 + 주장 검증 + 오탐 제거)
> 코드 수정: **없음** (읽기 전용 조사)
> 확신도: 95%

---

## 1. 프레임워크 정체성

**"코리안 숏헤어 워크프레임"** — 순종이 아닌 혼합 타입 시스템 기반의 실용주의 프레임워크.

### 타입 시스템 구성

| 타입 체계 | 건수 | 파일 수 | 역할 |
|-----------|------|---------|------|
| **Pydantic v2** | ~20 클래스 | 4 (modules/models/) | LLM 응답 경계 검증, `extra="allow"` 관용 |
| **@dataclass** | 69건 | 46 | 내부 데이터 구조 (LLMRequest, RetrievalPlan 등) |
| **Protocol** | 16 클래스 | 4 (modules/protocols/) | 구조적 서브타이핑 계약 |
| **__slots__** | 99 슬롯 | 3 (DI Context) | Stage2(48) + Stage3(22) + Stage4(29) |
| **bare dict** | 전체 파이프라인 | - | LLM 응답 네이티브 포맷, 스테이지 간 전달 |

**핵심 특징**: dict-native 파이프라인 + Pydantic 경계 검증 + graceful degradation (검증 실패 시 원본 dict 반환).

```python
# modules/models/arc.py L266-276 — 대표 패턴
def validate_arc(raw: dict) -> dict:
    try:
        arc = ArcData.model_validate(raw)
        return arc.model_dump()  # → dict
    except Exception:
        return raw  # graceful fallback
```

---

## 2. 데이터 흐름

### 스테이지 간 전달 포맷

```
Stage 0 (바이블/NPC/문체)
    ↓ dict (master_bible, volumes, genre)
Stage 2 (Arc 생성)
    ↓ (None, valid_candidates: list[dict]) → Director 선택
Stage 3 (Blueprint 생성)
    ↓ (blueprint: dict|None, result: dict) → Director 심사
Stage 4 (원고 생산)
    ↓ (manuscript: dict|None, verdicts: dict)
    ↓ commit_episode_factory() → All-or-nothing DB 커밋
```

### LLM 응답 처리 체인

```
Gemini API 원시 문자열
    → response_mime_type="application/json" (Gemini 강제)
    → _extract_json_robust() (JSON 파싱 → regex 추출 → preamble strip → 폴백 dict)
    → response_schemas.py (JSON Schema, Pydantic 아님)
    → Pydantic validate (해당 시, 실패→원본 dict 유지)
    → 다운스트림 소비
```

### 상태 축적 (에피소드 간)

| 저장소 | 패턴 | 용도 |
|--------|------|------|
| **WorldState** | DB anchor `'world_state'` (~5KB JSON), 매화 갱신 | 13키 (주인공/NPC/관계/아이템/플롯/법칙/동기/약속/시간) |
| **FactLedger** | DB anchor `'fact_ledger'` (~50KB JSON max), append-only | 6섹션 (생존/보유/분실/장소/조직/수치) |
| **NPC History** | `npc_history` 테이블, append-only + rollback 시 DELETE | 필드별 변경 이력 (old→new, reason) |
| **Episode Bibles** | `episode_bibles` 테이블, per-episode | reveals, 스냅샷, known_attrs 델타 |

---

## 3. 확장 패턴

### 3-1. 장르 추가

```
base_guard.py (추상 BaseGuard)
    → wuxia_guard.py / hunter_guard.py / ... (10종 구체 Guard)
    → work_guard.py (작품별 YAML, 선택적)
    → style_guard.py (문체 Guard, 선택적)
```

- **확장 방법**: `class MyGenreGuard(BaseGuard)` + `config/genres/mygenre.yaml`
- **장르 규칙 100% YAML 외부화**: 금기어, 필수 개념, 캐릭터 제약 전부 YAML

### 3-2. Advisory 추가

- `stage4_interview_round.py` `_run_advisory_chain()`: `ThreadPoolExecutor(max_workers=8)`
- **추가 방법**: `def _advisory_mycheck(self, ...) -> list[str]` + executor.submit 등록
- **티어 분류**: CRITICAL(3) / MAJOR(2) / INFO(1) — `_classify_advisory_tier()` 패턴 매칭
- **충돌 해소**: `_suppress_conflicting_advisories()` — 상위 티어와 주제 공유 시 하위 제거 (logging.info 기록)

### 3-3. LLM 프로바이더 전환

| 파일 | 역할 | 상태 |
|------|------|------|
| `llm_provider.py` | Provider Protocol 정의 (`generate()` 인터페이스) | ✅ |
| `llm_router.py` | 모델명→프로바이더 라우팅 | ✅ |
| `providers/gemini_provider.py` | Gemini 구현체 | ✅ 활성 |
| `providers/anthropic_provider.py` | Anthropic 스텁 | ⚠️ 미완 |
| `providers/openai_provider.py` | OpenAI 스텁 | ⚠️ 미완 |
| `providers/vertex_provider.py` | Vertex 스텁 | ⚠️ 미완 |

- **현재 Gemini 결합도**: 165건/62파일 (genai 참조)
- **전환 예상 작업량**: 3-5일 (TF-MULTI Phase 2 계획 존재)

### 3-4. 설정 외부화 현황

| 카테고리 | 파일 수 | 내용 |
|----------|---------|------|
| **프롬프트 YAML** | 22 | analyst, director, chief_writer 등 9개 주요 + 11개 라이브러리 + 2개 규칙 JSON |
| **장르 YAML** | 10 | 장르별 Guard 설정 |
| **설정 YAML** | 2 | validation.yaml (95개 설정), models.yaml (모델 SSOT) |
| **합계** | **34** | |

- **외부화 비율**: ~60% YAML (프롬프트 + 검증 임계값), ~40% Python 상수 (constants.py, `_LazyThreshold` 패턴)

---

## 4. 동시성 & 라이프사이클

### 스레딩 모델

| 위치 | 메커니즘 | 용도 |
|------|----------|------|
| `db_manager.py:65` | `threading.RLock()` | 전 DB 연산 보호 (재진입 가능) |
| `base_agent.py:1623` | `threading.Lock()` | Context Cache dict 접근 보호 |
| `adaptive_retry.py:437` | `threading.Lock()` | 싱글톤 초기화 이중 검사 |
| `session_logger.py:55` | `threading.Lock()` | JSONL 파일 인터리브 방지 |
| `stage4_interview_round.py` | `ThreadPoolExecutor(8)` | Advisory 8개 병렬 (per-advisory 60s, overall 300s) |
| `stage4_interview_round.py` | `ThreadPoolExecutor(2)` | Post-selection 2개 병렬 |

**비동기 없음**: asyncio 0건. 전량 동기 + ThreadPoolExecutor.

### 객체 라이프사이클

```
SovereignApp.__init__()
    → Lazy module loading (STAGE0_AVAILABLE, _lazy_load_*)
    → Core bootstrap (UI, Logger, Gemini Client, PromptBuilder)
    → Service injection (Audit, UI, State, Project)
    → 20+ agents/trackers = None (지연 초기화)
    → atexit.register() ×2 (faulthandler, audit flush)

Stage 실행 시:
    → StageNContext.from_app(app) — 스냅샷 DI
    → StageNOrchestrator(ctx) — 스테이지 로직
    → 종료 후 app에 write-back (Stage2 StateTracker 동기화 등)

Cleanup:
    → db_manager.close(): pending transaction rollback + conn=None
```

### 에러 복구

| 패턴 | 위치 | 동작 |
|------|------|------|
| **Adaptive Retry** | `adaptive_retry.py` | 5종 에러 분류 (timeout/quota/malformed/network/unknown) + 백오프 |
| **DB Transaction** | `db_manager.py:2110-2149` | @contextmanager, 중첩 감지, IntegrityError→rollback+raise |
| **Advisory 비치명** | `stage4_interview_round.py` | 타임아웃/예외 시 로깅만, 파이프라인 계속 |
| **Fail-closed** | NPC LLM 검증 등 | 실패 시 보수적 판정 (빈 응답 = 위반 없음 처리 아님) |

---

## 5. 계약 & 경계

### Protocol 계약 현황

| 파일 | Protocol 수 | 메서드 수 | 역할 |
|------|-------------|----------|------|
| `db_repository.py` | 1 | 59 | DB 전체 CRUD 계약 |
| `app_services.py` | 5 | 69 | UI/Audit/Project/State/Config 서비스 |
| `agents.py` | 8 | 12 | Pipeline/Ensemble/Validator/Critic/Corrector |
| `validators.py` | 2 | 2 | Tier/Episode-aware 검증기 |
| **합계** | **16** | **142** | |

- **DB 계약 준수**: `db_repository.py` 59 메서드 ↔ `db_manager.py` 59 구현 — **100% 일치**

### 신뢰 경계

| 영역 | 신뢰 수준 | 검증 |
|------|----------|------|
| Python 내부 코드 | 신뢰 | Protocol + type hint |
| LLM JSON 응답 | 제한 신뢰 | response_mime_type 강제 + _extract_json_robust + Pydantic 경계 검증 |
| LLM 자유 텍스트 | 불신뢰 | 로깅만, 실행 불가 |
| 사용자 입력 | 불신뢰 | enum 체크 (장르), Path 검증, regex (프로젝트명) |

---

## 6. 고유 패턴 (vs LangChain/CrewAI/AutoGen)

### 진정으로 고유한 것

| 패턴 | 설명 | 근거 |
|------|------|------|
| **Director 주권주의** | Python이 REJECT 강제 불가. QualityGate는 PASS→REJECT 전환만 (PWF bypass). Director가 최종 결정 | `stage4_interview_round.py:1995-2001` |
| **3-tier 패치 라우팅** | Director가 fix_scope(inplace/partial/full) 지정 → Python이 분기 실행. 패치 이력 DB 추적 | `stage4_interview_round.py:2388-2449` |
| **Advisory 비구속 병렬 체인** | 8개 advisory 동시 실행 → 티어별 충돌 해소 → Director MC 주입 (참고만, 강제 아님) | `stage4_interview_round.py:2726-2759` |
| **SC 온도 변조 투표** | Director 다중 투표 (0.1+i×0.05 온도) → 다수결. PWF=PASS 계산 | `director_auditor.py:1010-1078` |
| **Python 수집 / LLM 판단 분리** | Python은 데이터 수집·포맷·전달만. 품질 판정·팩트 수정·REJECT 결정은 LLM만 | 대원칙 1, 전체 파이프라인 |
| **Append-only 이력** | NPC 변경·관계·Director 선택 전부 append-only. Rollback은 `DELETE WHERE ep >= N` | `db_manager.py:2188` |
| **Context Caching 선택적 적용** | 5개 에이전트만 (50K 임계값, 600s/1800s TTL). 전체 적용이 아닌 ROI 기반 | `base_agent.py:1599-1820` |

### 표준 관행 (고유하지 않음)

- YAML 프롬프트 외부화
- 검증 파이프라인 (tier별 검증)
- Retry 루프
- SQLite 상태 저장
- ThreadPoolExecutor 병렬화

---

## 7. 갭 & 기술 부채

### 아키텍처 수준 갭

| # | 갭 | 현재 상태 | 영향 | 우선순위 |
|---|------|----------|------|----------|
| 1 | **main_a.py 규모** | 3,626줄. Stage2/3/4 분리 완료했으나 35+ self 속성 잔존. 완전한 god object 해체 미완 | DI 복잡도 상승 | 낮음 (기능 영향 없음) |
| 2 | **타입 안전성 갭** | dict 기반 파이프라인에서 `.get()` 폴백 의존. LLM 응답 구조 변경 시 silent 실패 가능 | 디버깅 난이도 | 중간 |
| 3 | **단일 프로세스/사용자** | asyncio 없음, 동시 세션 미지원, SQLite 단일 파일 | 확장성 천장 | 낮음 (단일 사용자 대상) |
| 4 | **Gemini 결합** | 165건/62파일. Provider 추상화 스텁 존재하나 활성화 미완 | 프로바이더 전환 3-5일 | 중간 |
| 5 | **설정 표면적** | 34개 YAML + constants.py. Director.yaml 4곳 체크리스트 키 중복 | 유지보수 비용 | 낮음 |

### 의도적 NO-GO (기술 부채 아님)

| 항목 | 이유 | 재검토 조건 |
|------|------|------------|
| FTS5 한국어 형태소 | re.split 97% 처리, OR 5키워드 recall 충분 | 검색 recall < 90% 시 |
| 동적 장르 확장 | 16-20 하드코딩 위치, 10개 장르로 충분 | 20+ 장르 필요 시 |
| Async 통일 (R4) | ThreadPoolExecutor 충분, ASGI 재설계 필요 | 동시 사용자 > 10 시 |
| 캐시 최적화 | 11 HIT/에피소드 전량 커버, Gemini 임계값 미달 | API 임계값 하향 시 |

---

## 8. 3-pass 감리 오탐 제거 결과

| 에이전트 주장 | 검증 결과 | 근거 |
|-------------|----------|------|
| @dataclass 150+건 | **오탐** → 69건 | `grep -c @dataclass modules/` = 69 |
| YAML 24개 | **오탐** → 34개 | prompts(22) + genres(10) + settings(2) |
| Protocol 17개 | **경미 오차** → 16개 | `grep "class.*Protocol" modules/protocols/` = 16 |
| Advisory suppression silent | **오탐** | L539 `logging.info("[QI-SNR-3] advisory suppress: ...")` 존재 |
| NPC history no cascade delete | **오탐** | `reset_after()` L2188 `DELETE FROM npc_history WHERE episode_no >= ?` 존재 |
| genai 160건 | **허용 오차** | 실제 165건/62파일 |
| main_a.py 3,626줄 | **정확** | `wc -l` 확인 |
| Director verdict inversion | **부분 정확** | QualityGate PASS→REJECT는 사실이나, PWF bypass로 Director 주권 존중. "inversion"은 과장 |
| Vote aggregation by count only | **정확** | 가중치 없이 다수결, 설계 의도 (SC 표준 관행) |
| Single-candidate score cap 90 | **정확** | `director_ensemble.py:696` SCM 로직 확인 |

### 오탐 원인 분석

1. **코드 위치 혼동** (2건): 삭제 로직이 다른 메서드에 있음에도 "없음"으로 판정
2. **로깅 존재 미확인** (1건): logging.info를 "silent"으로 오판
3. **수치 과장** (2건): 69→150+, 34→24 — 정밀 카운트 없이 추정

---

## 9. 사용자가 생각 못 했을 수 있는 부분

### 9-1. Graceful Degradation 전략

Pydantic 검증 실패 시 원본 dict를 그대로 통과시키는 패턴. 엄격한 타입 체계가 아닌 **관용적 경계 검증**. 장점은 LLM 응답 변동에 강하다는 것, 단점은 타입 오류가 다운스트림에서 지연 발현될 수 있다는 것.

### 9-2. DI Context __slots__ 패턴

Stage별 DI Context가 `__slots__` 기반이라 일반 클래스보다 메모리 효율적이고, 오타 속성 접근 시 즉시 AttributeError 발생. `from_app(cls, app)` 팩토리로 main_a.py 의존성을 스냅샷 분리.

### 9-3. Context Caching ROI 기반 선택적 적용

5개 에이전트만 캐싱 (50K 이상 반복 컨텍스트 보유 에이전트). 전체 적용이 아닌 비용-효과 기반. Gemini API 캐시 생성 25% 할인, 읽기 90% 할인.

### 9-4. ThreadPoolExecutor 이중 레이어

Advisory 8병렬(max_workers=8) + Post-selection 2병렬(max_workers=2). 전체 asyncio 전환 없이 병목 구간만 선택적 병렬화.

### 9-5. Append-only + Rollback 하이브리드

이력은 append-only로 축적하되, 롤백 시 `DELETE WHERE episode_no >= N`으로 정밀 절삭. 진정한 이벤트 소싱은 아니나, 실용적 수준의 감사 추적 + 복구 기능.

### 9-6. Director MC Parts 구조

Director가 최종 판정할 때 받는 정보가 10+ 블록으로 구조화됨: Advisory(티어별), WritingDirective, 참고 전용 블록([참고 — 판정 무관] 래핑), 핵심 판정 블록 분리. 이 구조가 Director LLM의 판정 정확도에 직접 영향.

### 9-7. 프레임워크 vs 애플리케이션 경계

현재 글도비는 **애플리케이션**이지 **프레임워크**는 아님. GenreGuard 확장점, Advisory 플러그인, Provider 추상화 등 프레임워크적 요소가 있으나, `import geuldobi` 형태의 재사용 가능한 라이브러리는 아님. 프레임워크로 전환하려면 main_a.py SovereignApp의 완전 분리 + 설정 주입 표준화 + pip 패키지화가 필요.

---

## 10. 한 줄 요약

**dict-native 파이프라인 + Pydantic 경계 검증 + Protocol 계약 + __slots__ DI의 혼합 타입 시스템. Director 주권주의·3-tier 패치·병렬 Advisory 등 LLM 오케스트레이션 고유 패턴 보유. 프레임워크가 아닌 애플리케이션이나, 확장점은 충분히 정비됨.**
