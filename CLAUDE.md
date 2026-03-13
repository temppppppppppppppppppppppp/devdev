# 글도비 — 후임 에이전트 인수인계

> AI 웹소설 자동 생성 시스템. Python + Gemini API (멀티 프로바이더 대응 완료 — Anthropic/OpenAI/Vertex AI readiness).
> 검토 문서: `docs/2026-03-04/명세-행동 정합성 감사.md`, `docs/2026-03-04/stage3-blueprint-logic-error-analysis.md`
> 파이프라인 점검: `docs/2026-03-06/TF-57-arc-quality-gate-hardening.md`

---

## ⚖️ 대원칙 (절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python은 데이터 수집·포맷팅·전달만. "오류인가?", "수정할까?" 같은 판단은 LLM 에이전트가 담당.
2. **팩트시트 수정 권한은 LLM만** — NPC 속성, 세계관 설정, 관계도를 수정하는 건 LLM뿐. Python이 자동으로 팩트를 덮어쓰면 안 됨.
3. **디렉터 주권주의 (내각제)** — Director가 최종 품질 결정권. Chief Writer·Analyst 등은 초안 제출만, 합격/불합격/수정 지시는 Director가 내림. Director를 우회하면 안 됨.
4. **사망 캐릭터는 회상/언급만 허용** — `deceased=True` NPC가 행동/대사로 등장하면 REJECT. 회상·과거 장면·타인 언급은 허용.

---

## 파이프라인

```
Stage 0 (초기 설정)  →  Stage 2 (Arc/Blueprint)  →  Stage 4 (원고)
세계관 바이블 추출       Analyst → Arc → Blueprint     Chief Writer → Director 심사
NPC 등록                앙상블 + 검증 체인              합격/불합 → 재작성 루프
문체 분석                연속성 검사                    카카오/네이버 포맷 출력
```

---

## 현재 상태 (2026-03-12)

- **작동함**: Stage 0→2→4 정상 동작 (투자물 장르 실파이프라인 검증 완료)
- **테스트 기준선**: **3,847 collected** (last verified 2026-03-10). 3,831 passed, 16 skipped.
- **Ruff**: 0 violations
- **DI 전환**: Stage2(44슬롯) + Stage3(19슬롯) + Stage4(24슬롯) 전량 완료
- **코드 분할 완료**: stage4 orch -64%, chief_writer -62%, stage2 orch -66%, interview_round run() -48%
- **완료된 주요 작업군** (150건+ 전량 완료, 개별 이력은 git log 참조):
  - 인프라: DI 전환, DB-SSOT, Ruff 0, Protocol 표준화, God Object 해체 3차
  - 품질: NC-1~3(수치 정합성), NS-1~4(수치 자기검증), WritingDirective, Self-Critique 17개 체크
  - 장기기억: LM-A~I(7개 advisory), TruthGate, Smart Context Retrieval
  - 수정전략: PASS_WITH_FIX 3-tier(inplace/partial/full), fix_scope 라우팅
  - 멀티프로바이더: LLMProvider Protocol + Router + 4 Provider (Gemini only 운영)
  - 감사: 1~10차 전수조사, TF-FINAL, TF-BE 백엔드 전수조사 (P0 0건, P1 0건)
- **폐기/NO-GO 확정**:
  - ~~FTS5 한국어 형태소~~ → ROI 낮음 (Python re.split 97% 처리)
  - ~~동적 장르 확장~~ → 폐기 (템플릿 복제 방식 10개 장르 검증 완료)
  - ~~캐시 최적화~~ → NO-GO (Gemini API 임계값 하향 전까지 불가)

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `main_a.py` | 진입점, SovereignApp (4,200+ lines) |
| **Stage 2** | |
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 (907줄, 서브모듈 3개 위임) |
| `modules/core/stage2_validation_pipeline.py` | Stage2 검증 파이프라인 |
| `modules/core/stage2_finalizer.py` | Stage2 Finalizer |
| `modules/core/stage2_preflight.py` | Stage2 Preflight 분석 |
| **Stage 3** | |
| `modules/core/stage3_orchestrator.py` | Blueprint 오케스트레이터 (DI 완료, 19슬롯) |
| **Stage 4** | |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 (883줄, 서브모듈 3개 위임) |
| `modules/core/stage4_post_processor.py` | Stage4 PASS 후처리 |
| `modules/core/stage4_context_builder.py` | Stage4 컨텍스트 빌더 |
| `modules/core/stage4_interview_round.py` | Stage4 인터뷰 라운드 (run 686줄, 12개 메서드) |
| **에이전트** | |
| `modules/domain/agents/base_agent.py` | AI 에이전트 베이스 (Context Caching 포함) |
| `modules/domain/agents/chief_writer.py` | Chief Writer (854줄 + context/quality 서브모듈) |
| `modules/domain/agents/chief_writer_context.py` | CW 컨텍스트 빌더 (1,074줄) |
| `modules/domain/agents/chief_writer_quality.py` | CW 품질 게이트 (465줄, self-critique 17개 체크) |
| **Advisory 체인** (Stage4, ThreadPoolExecutor 8병렬) | |
| `modules/core/truth_gate.py` | 메모리 오염 방지 (7개 검사) |
| `modules/core/npc_drift_advisor.py` | NPC 속성 표류 LLM advisory |
| `modules/core/numeric_drift_advisor.py` | FactLedger 수치 표류 LLM advisory |
| `modules/core/relationship_drift_advisor.py` | NPC 관계도 표류 LLM advisory |
| `modules/core/flashback_verifier.py` | 회상/플래시백 오염 감지 |
| `modules/core/info_paradox_checker.py` | 1인칭 정보 역설 감지 |
| `modules/core/long_term_repetition_advisor.py` | 장기 반복 패턴 감지 (20화+) |
| `modules/core/numeric_consistency_checker.py` | 수치 정합성 Python-only (9개 검사, LLM 0회) |
| **핵심 모듈** | |
| `modules/core/db_manager.py` | SQLite DB 매니저 (`project_data.db` SSOT) |
| `modules/core/failure_analyzer.py` | 실패 패턴 분석 (11개 메서드) |
| `modules/core/pattern_tracker.py` | 표현·은유·결말 패턴 추적 (LLM 0회) |
| `modules/core/writing_directive_generator.py` | WritingDirective 생성 (Flash 1회) |
| `modules/core/context_advisor.py` | Smart Context Retrieval |
| `modules/core/narrative_context_formatter.py` | 서사 구조 컨텍스트 포맷터 |
| `modules/core/genre_schema_builder.py` | 장르별 동적 스키마 (비무협 오염 방지) |
| **LLM 추상화** | |
| `modules/core/llm_provider.py` | LLMProvider Protocol + Request/Response |
| `modules/core/llm_router.py` | LLMProviderRouter (shared singleton) |
| `modules/core/llm_generate.py` | `generate_content_via_router()` 공용 헬퍼 |
| `modules/core/llm_schema.py` | Provider-neutral schema adapter |
| `modules/core/providers/*.py` | Gemini/Anthropic/OpenAI/Vertex AI Provider |
| **설정** | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 43개 |
| `config/models.yaml` | 모델 설정 SSOT |
| `config/settings/validation.yaml` | 검증 임계값 |
| `modules/core/genre_guards/*.py` | 장르 가드 10종 + WorkGuard + StyleGuard |
| **DI Context** | |
| `modules/core/stage2_context.py` | Stage2Context (44 슬롯) |
| `modules/core/stage3_context.py` | Stage3Context (19 슬롯) |
| `modules/core/stage4_context.py` | Stage4Context (24 슬롯) |

---

## ⚠️ 주의사항

### 모델 설정
- **SSOT**: `config/models.yaml` 단일 참조. `constants.py` `_load_model_from_yaml()` import-time 로드.
- **fallback chain**: `gemini-2.5-pro → gemini-2.5-flash` 2단계만 유지.
- **멀티 프로바이더**: 4 provider 구현체. `models.yaml` `providers:` 섹션에서 enabled/disabled 제어. **기본값: gemini=true, 나머지 false**.
- **direct generate_content() 잔류**: `gemini_provider.py`(합법) + `vertex_provider.py`(합법) + `response_schemas.py` L769(독스트링 예제)만 허용.

### PASS_WITH_FIX 수정 전략
- **3-tier 라우팅**: fix_scope 기반 — inplace(LLM 1회 국소), partial(1후보 재생성), full(3후보 전면)
- **QualityGate**: PASS일 때만 score < 90 → REJECT. **PASS_WITH_FIX는 bypass** (Director 주권 존중)
- **InPlace 보호**: 30KB 초과 → return None (full 폴백), rfind position 0 보호, JSON 파싱 1단계, 1-depth deep merge

### Advisory 체인 (Stage4)
- TruthGate → NpcDrift → NumericDrift → Flashback → InfoParadox → RelDrift → LongTermRep → NumericConsistency → SceneSimilarity → Timeline
- **ThreadPoolExecutor(max_workers=8)** 병렬 실행, per-advisory timeout 60s
- 전부 `_director_mc_parts`에 주입, Director 최종 판정
- **우선순위 헤더**: TruthGate=CRITICAL, Drift/Flashback/InfoParadox=MAJOR, 나머지=INFO

### NC-1/NC-3 규칙
- **NC-1 numeric_consistency_review**: 선택사항, 자동감점 없음 (대원칙 3 준수)
- **NC-3 consistency_checklist**: 20개 카테고리 OK/ISSUE 체크, 미작성 시 감점 없음
- **NC-3B**: score_breakdown 합산 ≠ score → breakdown 우선 자동 교정

### DB / 메모리
- `memory_engine.py` 삭제됨. VecMemory(`vec_memory.py`)가 DBManager 커넥션 공유. `project_data.db` 단일 SSOT.
- NPC 속성 변경 → `npc_history` 테이블 (append-only, reason 컬럼 포함)
- NPC 관계 변경 → `npc_relationship_history` 테이블 (append-only, sorted key)
- HUD Anomaly → `manuscripts` 테이블 `hud_snapshot` 컬럼
- Context Caching: 5개 에이전트(chief_writer, arc_ensemble, blueprint_ensemble, director_ensemble, director_continuity)

### 비무협 장르 오염 방지
- `genre_schema_builder.py` 장르별 동적 스키마 생성 (TF-45)
- `analyst.py _build_genre_placeholders()` → 무협이면 원본, 비무협이면 대체
- 4th wall 메타용어 3단계 방어: chief_writer.yaml 규칙14 → self-critique 10번째 → truth_gate(P2)

### Stage2 Director Selection (TF-S2)
- Python 자동선택 제거, Director가 `compare_and_select_arc()`에서 최종 선택
- `STRUCTURAL_MIN_SCORE = 50` 소프트필터 (최소 1개 보장)

### 주요 필드명 주의
- `protagonist_items` vs `items_acquired`: API 스키마가 `protagonist_items` 강제. 현재 코드 기준 19파일 39곳에 우선-폴백 소비 패턴 적용됨.
- `cumulative_elapsed`: WorldState 필드, 한국어 시간 파서 `_parse_elapsed_days()`

### Self-Critique 체크 (17개)
1~4: 기본(사망NPC/분량/대사비율/씬전환), 5: 동기약속 방치, 6: WritingDirective 준수, 7: 표현 신선도, 8: AI-tell 패턴, 9: ending_hook, 10: 산술 일관성, 11: 메타용어 노출, 12: 엔딩 참신성, 13: 시간 논리, 14: 문단 구조, 15: 톤 일관성, 16: POV 일관성, 17: 씬 전환 마커

### DB Advisory (Python 자동감지, 참고용)
- Stage4 Director: DB-1(pacing), DB-2(satisfaction), DB-6(reveals), DB-8(reflexion)
- Stage2 Finalizer: DB-3(arc_dependencies), DB-7(character_voice)
- Stage3: DB-4(stale seeds), FactLedger 수치
