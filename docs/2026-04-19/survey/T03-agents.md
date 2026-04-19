# T03: Agent 아키텍처 조사

Surveyor: Claude Code (Terminal 3)
Date: 2026-04-19
Scope: `modules/domain/agents/` (56 파일, 55,660 LOC) — 상속 구조, 프롬프트 구성, LLM 호출 패턴, 캐싱 전략, 오케스트레이션 일관성

## 1. Executive Summary

- **성숙도 판정: Pre-production**
- 한줄 요약: **LLM 호출 스택(키 순환·쿼터 폴백·JSON 복구)은 프로덕션급으로 단단하나, BaseAgent God Object(2,500 LOC)와 이중 LLM 호출 경로·프롬프트 이중 관리가 일관성을 해치는 "부분 성숙" 상태다.**

구조적 강점(단단한 `ask()` 인프라, ThreadPoolExecutor 앙상블 팬아웃, Director God Object 분해 V64 P2-1)과 구조적 약점(BaseAgent 비대화, LLM 호출 경로 이중화, 프롬프트 YAML/인라인 혼재)이 공존. Stage 2/3/4 파이프라인은 이 레이어를 안정적으로 이용하지만, 에이전트 신규 추가 시 학습 곡선이 급격히 치솟는다.

## 2. 강점 (Strengths)

1. **프로덕션급 LLM 호출 복원력** — `base_agent.py:684-1087` `ask()` 메서드가 (a) 키 순환, (b) 쿼터 폴백 체인, (c) 네트워크 재시도, (d) MAX_TOKENS continuation, (e) JSON 자가복구, (f) 백업 모델 복구를 한 스택에 결합. 세 층의 Lock(`_rotation_lock`, `_quota_lock`, `_cache_lock`)으로 스레드 안전성 보장.
2. **앙상블 팬아웃 일관성** — `arc_ensemble.py:1085`, `blueprint_ensemble.py:674`, `chief_writer.py:727`, `consensus_validator.py:219`, `director_auditor.py:1182`, `block_enricher.py:816` 모두 동일한 `ThreadPoolExecutor + as_completed + FutureTimeoutError` 패턴 사용. timeout은 `system.yaml ensemble_timeouts.*` SSOT로 외부화(`arc_ensemble.py:775-778`, `blueprint_ensemble.py:429`).
3. **Director God Object 분해 (V64 P2-1)** — `director.py:22-391`이 얇은 파사드로 재편되었고, 다섯 개 협력자(`DirectorCachingManager`, `DirectorGradingSystem`, `DirectorEnsembleSelector`, `DirectorContinuityValidator`, `DirectorQualityAuditor`)로 책임 분리 (`director.py:63-75`). ContinuityInspector도 동일한 파사드 패턴(`continuity_inspector.py:40-64`).
4. **bare except 제거 완료** — agents/ 디렉토리 전체에서 `except:` 단독 패턴 0건 (grep 검증). BaseAgent의 분류 체계(`AgentErrorType`, `base_agent.py:48-55`)를 통해 TIMEOUT/QUOTA/NETWORK/MALFORMED/SCHEMA 5개 유형으로 분류·복구 전략 결정.
5. **Gemini Context Caching 통합** — `base_agent.py:2179-2440` `_get_or_create_context_cache` + `_ask_with_cached_context`가 `hashlib.md5` content_hash 기반 TTL 캐시(기본 1800s). 50KB 미만(`_MIN_CACHE_CONTENT=50000`, line 2177)은 자동 스킵 — 비용·쿼터 방어 논리 내장.
6. **SessionLogger + MetricsCollector 이원 telemetry** — `base_agent.py:950-988` 각 LLM 호출마다 DB 영속화(`_log_llm_call_to_db`)와 세션 로그 두 경로로 기록. input/output/cached/thinking 토큰까지 분해되어 저장(`base_agent.py:471-502`).
7. **프롬프트 크기 사전 게이트** — `base_agent.py:327-352` `_apply_prompt_size_gate`가 API 호출 전에 `ContextLimits.MAX_CONTEXT_CHARS` 초과 시 `smart_truncate` + human-intervention 플래그. 네트워크 비용 낭비 방지.

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. BaseAgent God Object (2,500 LOC 단일 클래스)
- **파일:라인**: `base_agent.py:158-2500`
- **설명**: `BaseAgent` 단일 클래스가 API 키 관리·쿼터 폴백·프롬프트 게이트·JSON 파싱·백업 복구·컨텍스트 캐싱·telemetry·response validation·통신 연결 체크를 모두 책임. 20개 자식 클래스가 이 한 덩어리를 통째로 상속.
- **영향도**: 신규 에이전트 추가 시 2,500 줄 기저 클래스를 이해해야 함. 단일 책임 원칙(SRP) 위반. 단위 테스트 격리 어렵다(한 메서드를 테스트하려면 전체 클래스를 인스턴스화해야).
- **권장 조치**: V64 P2-1 패턴을 BaseAgent에 적용 — `_ApiKeyRotator`, `_QuotaFallbackManager`, `_JsonResponseRepair`, `_ContextCacheManager`, `_AgentTelemetry` 믹스인/컴포지션으로 분해. `ask()`만 파사드 유지.

### P0-2. LLM 호출 경로 이중화 — `self.ask()` vs `generate_content_via_router` 혼재
- **파일:라인**:
  - `self.ask()` 사용: 24개 파일, 52회 호출(`analyst.py:1`, `chief_writer.py:3`, `director_auditor.py:5`, `director_ensemble.py:5` 등)
  - `generate_content_via_router()` 직접 사용: `writer.py:277`, `weaver.py:59`, `analyst.py:906`, `director_continuity.py:791`, `manuscript_validator.py:637`, `state_tracker_npc.py:808,2269` — 7개 지점
- **설명**: 캐시 히트 경로는 `generate_content_via_router`로 우회하여 BaseAgent의 복원력 스택(키 순환, 쿼터 폴백, JSON 복구, telemetry)을 **모두 우회**. `weaver.py:57-95`, `writer.py:272-306`가 대표 사례 — try/except 실패 시 `ask()` fallback으로 넘어가지만, 성공 경로는 관측되지 않음.
- **영향도**: 캐시 경로 LLM 호출이 DB/세션 로그·비용 추적·에러 분류 체계에 기록되지 않음 → 비용/실패율 분석 누수. 개별 호출자가 개별적으로 `response.text` 접근·`_extract_json_robust` 호출해야 하므로 로직 중복.
- **권장 조치**: `BaseAgent._ask_with_cached_context`로 단일화. `generate_content_via_router` 직접 호출을 전부 제거하고 캐시된 경로도 `ask()` 파이프라인을 통과하도록 통합.

### P0-3. 프롬프트 이중 관리 — YAML SSOT vs 인라인 상수 혼재
- **파일:라인**:
  - YAML SSOT 완전 전환: `chief_writer_prompts.py:11`("인라인 상수 제거 — YAML이 SSOT"), `analyst_prompt_api.py:65-84`(fallback 본문 제거)
  - 인라인 상수 잔류: `manager.py:16` `UPDATE_STATE_PROMPT_V25`(104 줄), `block_enricher.py:30,109,142`(3개 대형 프롬프트), `continuity_arc.py:21,165`, `continuity_blueprint.py:19`, `continuity_manuscript.py:20`, `arc_corrector.py:46`, `arc_critic.py:22`, `state_extractor.py:28,68`, `state_locked_arc_generator.py:105,133,181`, `preflight_checker.py:22`, `consensus_validator.py:103`, `unified_arc_validator.py:35`, `director_prompts.py:21,179,231` (`_INLINE_*` 명시적 fallback)
  - `analyst_prompts.py:7,33,119,198,541` — 5개 레거시 인라인 (analyst.yaml로 마이그레이트됐으나 Python 파일 상주)
- **설명**: 14개 파일이 여전히 대형(`"""…"""`) 프롬프트 상수를 Python에 보관. YAML SSOT 마이그레이션이 절반만 완료.
- **영향도**: 동일 프롬프트가 YAML과 Python 양쪽에서 drift할 수 있음. 프롬프트 tuning 시 어디가 실제로 쓰이는지 식별 비용 ↑.
- **권장 조치**: `modules/core/prompt_loader.py`가 이미 있으므로 잔여 14개 파일의 프롬프트를 `config/prompts/*.yaml`로 옮기고 `_INLINE_*` 패턴을 전량 제거. `director_prompts.py`의 `_INLINE_*`는 `load_director_prompt` fallback 용도로 남아있으나, YAML이 정착했으므로 삭제 가능.

### P0-4. 캐시 경로 `response_schema` 보장 불일치
- **파일:라인**: `weaver.py:59-69`, `writer.py:277-287`
- **설명**: `generate_content_via_router` 직접 호출 시 `response_schema`를 전달하지 않음 → JSON Schema 강제가 캐시 경로에서 사라짐. `base_agent.py:2273`의 `_ask_with_cached_context`는 `response_schema`를 지원(`:2321-2323`)하지만 사용자(직접 호출자)들이 활용 안 함.
- **영향도**: 캐시 히트 시 JSON 스키마 drift 가능성 → `_extract_json_robust`의 정규식 복구 경로(`base_agent.py:2033-2054`)에 부담 가중.
- **권장 조치**: `BaseAgent._ask_with_cached_context`로 일원화하고 스키마 전달을 필수화.

## 4. 개선 권장 (Major Issues) — P1

### P1-1. `agents/` 디렉토리 내 비-에이전트 클래스 다수
- **파일:라인**: 
  - 순수 데이터클래스/엔벨로프: `four_phase_arc_runtime.py:45-156`(10개 `_XxxEnvelope`), `three_phase_blueprint_runtime.py:85-216`(10개 유사), `director_ensemble.py:1123-1145`(4개)
  - 서비스 클래스(BaseAgent 미상속): `ConstraintCompiler`, `BlueprintConstraintCompiler`, `UnifiedBlueprintValidator`, `Stage3ValidationBoundary`, `Stage3RetryCoordinator`, `ContinuityArcValidator`, `ContinuityBlueprintValidator`, `ContinuityManuscriptValidator`, `ChiefWriterContextBuilder`, `ChiefWriterContextPackets`, `ChiefWriterQualityGate`, `DirectorAuditor`, `DirectorCachingManager`, `DirectorContinuityValidator`, `DirectorEnsembleSelector`, `DirectorGradingSystem`, `StateTracker`, `StateTrackerNPC`, `StateTrackerPlots`, `StateTrackerFinancial`, `NegativeExampleInjector`, `ManuscriptValidator`, `ArcDraftValidator` — 약 30개
- **설명**: 56개 파일 중 20개만이 BaseAgent 자식. 나머지 36개는 (a) 에이전트의 내부 컴포넌트, (b) 데이터 컨테이너, (c) 검증자, (d) 오케스트레이션 런타임. `agents/`라는 디렉토리 이름과 실체가 불일치.
- **영향도**: 디렉토리 의미가 흐려짐. 신규 개발자가 "에이전트란 무엇인가?" 경계 파악 어렵다.
- **권장 조치**: 서브디렉토리 분리 제안 — `agents/` (BaseAgent 상속만), `agents/runtime/` (runtime 클래스), `agents/components/` (director_*, chief_writer_*, continuity_*), `agents/validators/` (ManuscriptValidator, ArcDraftValidator 등).

### P1-2. `__init__.py` export vs 실사용 괴리
- **파일:라인**: `modules/domain/agents/__init__.py:9-24`
- **설명**: `__init__.py`가 6개만 export(`BaseAgent`, `Writer`, `Director`, `Analyst`, `ChiefWriter`, `ManuscriptValidator`). 실제 `main_a.py:205-223`는 19개 에이전트를 하위 모듈에서 직접 import.
- **영향도**: 공개 API 계약 없음. 외부 호출자가 어느 클래스가 "공식" 에이전트인지 파악 불가.
- **권장 조치**: `__init__.py`에서 사용 중인 전체 20개 에이전트를 export하거나, 아니면 직접 import를 강제.

### P1-3. Gemini-specific 로직이 "provider-neutral" 추상화에 누수
- **파일:라인**: `base_agent.py:1440-1541` `_extract_and_merge_response`
  - Line 1460: `response.text if response.text else ""` (모든 provider 공통)
  - Line 1466-1476: `response.candidates[0].content.parts` + `getattr(_p, "thought", False)` — **Gemini 전용**
  - Line 1511: `candidate.finish_reason in ["MAX_TOKENS", "LENGTH"]` — Gemini/OpenAI 이름
  - Line 1506 주석: "non-Gemini raw responses lack .candidates — skip continuation logic" — 명시적 인정
- **설명**: `LLMRouter`/`LLMRequest`/`LLMResponse`(`modules.core.llm_provider`) 도입으로 multi-provider 추상화를 시도했으나, `_extract_and_merge_response` 내부는 Gemini 응답 구조에 강하게 커플링.
- **영향도**: Claude/OpenAI provider를 도입하면 thinking extraction·continuation 로직이 동작 안 함 → 응답 잘림 미감지 리스크.
- **권장 조치**: `LLMResponse`에 `thinking_parts: list[str]`, `is_truncated: bool` 필드 추가. provider별 `extract_thinking` / `is_max_tokens` 책임을 Provider 클래스로 이관.

### P1-4. 에이전트 라인 수 극단 분포
- **파일:라인**: 
  - `three_phase_blueprint_runtime.py:3186`, `director_ensemble.py:2874`, `unified_blueprint_validator.py:2786`, `chief_writer.py:2601`, `base_agent.py:2500`, `blueprint_ensemble.py:2336`, `state_tracker_npc.py:2316`, `blueprint_constraint_compiler.py:2245`, `arc_ensemble.py:2180`, `analyst.py:1946`
  - 소규모: `weaver.py:144`, `state_tracker_financial.py:124`, `stage3_prompt_envelope.py:102`, `analyst_prompt_api.py:101`, `scene_cardinality_contract.py:71`
- **설명**: 상위 10개 파일이 전체 LOC의 ~45%(24,970/55,660). 개별 클래스가 너무 비대해서 단위 탐색/테스트가 어렵다.
- **영향도**: `chief_writer.py` 단독이 Writer 레거시 기능 흡수(`chief_writer.py:8-14` 주석에 명시), 2,601 LOC. `_self_critique`, `_check_hud_consistency`, `_check_cliche_overuse` 등 20+ 내부 메서드(line 2475-2496 위임자 목록)가 별도 모듈로 분리되지 않음.
- **권장 조치**: `three_phase_blueprint_runtime.py`와 `director_ensemble.py`의 추가 분할 — runtime 내 `_Stage3RepairRouter`(line 216) 등은 독립 파일로 분리 가능.

### P1-5. 인라인 f-string 프롬프트 (prompt YAML 외부화 미완료 파생)
- **파일:라인**: 
  - `block_enricher.py:930,991`, `critic.py:415`, `director_continuity.py:246,765`, `director_auditor.py:143`, `director_ensemble.py:2827` — 동적 f-string prompt 7건
  - `writer.py:216-269` 전체 `_build_writer_dynamic_prompt` 메서드는 ~54줄의 f-string
  - `manager.py:273-279` 주석에 직접 명시: "[TF-6-10 P2] 현재 인라인 f-string — 향후 prompt YAML 이전 고려"
- **설명**: 대형 정적 프롬프트는 YAML로 이전 중이나, 동적 조립 프롬프트는 여전히 Python 내부에 상주.
- **영향도**: 프롬프트 엔지니어가 Python을 읽어야 프롬프트 구조 파악 가능. A/B 실험·다국어화 어려움.
- **권장 조치**: 동적 프롬프트도 YAML 템플릿 + `.format_map(_SafeDict)` 패턴으로 이전(`analyst_prompt_api.py:29-63` 패턴 재활용).

### P1-6. `response_schema` 활용 불균등
- **파일:라인**: 
  - 적극 사용: `base_agent.py`(25개 참조), `analyst.py`(6), `blueprint_ensemble.py`(4), `arc_ensemble.py`(2)
  - 미사용: `director.py`, `chief_writer.py`, `manager.py`, `writer.py`, `weaver.py`, `critic.py` 등 14개 BaseAgent 자식 클래스
- **설명**: Gemini Structured Output 스키마 강제가 일부 에이전트에만 적용. `analyst.py:49-54`는 `ARC_DESIGN_SCHEMA` import를 try/except로 감싸 fallback 허용.
- **영향도**: JSON 복구 정규식(`base_agent.py:2033-2054`)에 의존해 타입 안정성을 뒷받침하는 에이전트가 다수 → LLM 출력 편차 시 `_extract_json_robust`가 "repaired"=True 폴백으로 진입.
- **권장 조치**: 핵심 생성 에이전트(ChiefWriter, Director, Manager) 전부에 `response_schema` 필수 적용. `modules.core.response_schemas`에 스키마 추가.

### P1-7. Exception 핸들러 밀도 높음 (221건 / 40개 파일)
- **파일:라인**: `grep "except Exception"` 기준 상위 — `base_agent.py:33`, `four_phase_arc_generator.py:16`, `chief_writer.py:16`, `state_tracker.py:13`, `analyst.py:13`, `blueprint_ensemble.py:12`
- **설명**: bare `except:`는 0건이지만 광범위한 `except Exception`이 많음. 많은 경우 DB 로깅·metrics 등 "optional" 경로로 마커(`[V64.P4] OPTIONAL`)가 있어 의도적. 그러나 일부는 근본 원인 은폐 위험.
- **영향도**: LLM 출력 파싱 실패·네트워크 에러·스키마 불일치가 광범위한 `except Exception`에 흡수되어 서비스 로직에서 조용히 fallback으로 전환 가능.
- **권장 조치**: 계속 개선 중인 것으로 보임(`[V64.P4]` 주석 다수 = specific exception types로 좁혀가는 중). `base_agent.py:2113`, `arc_ensemble.py:1165` 등의 광역 `except Exception`은 구체 타입으로 좁히는 PR 계속 진행.

## 5. 개선 검토 (Minor Issues) — P2

### P2-1. `_extract_json_robust`·`_escape_braces` 재호출 빈도
- **파일:라인**: 300회 호출 / 31개 파일
- **설명**: 모든 LLM 응답 처리자가 명시적으로 `self._extract_json_robust(text)`를 호출. `ask()`가 이미 연속 호출/백업 경로에서 사용하지만, 반환값은 raw string이라 호출자가 한 번 더 실행.
- **권장 조치**: `ask()`의 새 signature `ask_json(prompt, schema) -> dict`를 도입해 파싱까지 일괄 처리 검토.

### P2-2. "레거시 태그" 주석 다수
- **파일:라인**: `analyst.py:1-14` ("#레거시 에이전트 - Analyst"), `writer.py:1-15` ("[V64] Thin Fallback Agent — 원래 2,580줄 → 500줄 이하로 경량화"), `director.py:22` V0128/V59/V61 주석 층층
- **설명**: 실질적 레거시(deprecated)인지, 활성 fallback인지 읽기 어렵다. `__init__.py`에서는 여전히 export.
- **권장 조치**: 상태 명확화 — `@deprecated` 데코레이터 혹은 `Writer.__init__`에서 `warnings.warn(DeprecationWarning)` 채택.

### P2-3. `cache_name` 필드 주입 타이밍
- **파일:라인**: `weaver.py:21`, `writer.py:42`, `director.py:110-118` (명시적 invalidate_caches)
- **설명**: `cache_name`을 `__init__`에서 `None`으로 초기화 후 `main_a.py`가 나중에 주입(주석에 "main_a.py에서 주입됨"). 생성자 계약이 불명확.
- **권장 조치**: `set_cache(cache_name)` 명시적 메서드 도입, 혹은 `cache_name`을 생성자 kwarg로 승격.

### P2-4. 상수 하드코딩 산재
- **파일:라인**: `base_agent.py:1376` `model_stack[quota_retry_count]`, `:705` `max_continuations = 5`, `:706` `warn_threshold = 3`, `:710` `max_rate_limit_retries = 3`
- **설명**: `_SYSTEM_CFG`(system.yaml)로 대부분 외부화되었으나 상기 4개는 여전히 하드코딩.
- **권장 조치**: `system.yaml retry.*`에 추가 이전.

### P2-5. `_cache_lock.clear()` 의미 모호
- **파일:라인**: `base_agent.py:229-231`, `:258-260`
- **설명**: key rotation 시 `_context_caches.clear()` 실행 → API 키별 캐시 격리 의도이나, 주석이 없으면 다른 에이전트의 30분 캐시까지 날리는 부작용이 비가시.
- **권장 조치**: 라인 229에 "새 API 키 = 새 Gemini 캐시 공간, 기존 캐시 이름 무효" 주석 추가.

### P2-6. Weaver의 이중 fallback 경로 중복
- **파일:라인**: `weaver.py:86-95`(1차 fallback), `weaver.py:129-134`(2차 fallback), `weaver.py:139-144`(3차 error)
- **설명**: 3개 거의 동일한 dict 리터럴(`short_term_objective`, `mid_term_objective`, `status`, `fallback_reason`).
- **권장 조치**: `_default_drive(reason: str, status: str)` 유틸 함수로 통합.

## 6. 수치 지표 (Metrics)

| 항목 | 수치 |
|------|------|
| 파일 수 | 56 |
| 총 LOC | 55,660 |
| BaseAgent 자식 클래스 | 20 |
| 비-에이전트 클래스 (서비스/데이터) | ~30 |
| 최대 단일 클래스 LOC (BaseAgent) | 2,500 |
| ThreadPoolExecutor 사용 파일 | 6 |
| PromptLoader(YAML) 사용 파일 | 22 |
| 인라인 `_PROMPT = """..."""` 잔존 파일 | 14 |
| `self.ask()` 호출 사이트 | 52 / 24 파일 |
| `generate_content_via_router` 직접 호출 | 7 / 7 파일 |
| `response_schema` 사용 파일 | 6 / 20 에이전트 |
| `_extract_json_robust` 사용 빈도 | 300 / 31 파일 |
| bare `except:` 발견 | 0 |
| `except Exception` 발견 | 221 |
| YAML 프롬프트 총 LOC | 2,806 (9 파일) |
| Director 파사드 서브모듈 | 5 (caching/grading/ensemble/continuity/auditor) |
| ContinuityInspector 파사드 서브모듈 | 4 (arc/blueprint/manuscript/tracker) |
| `__init__.py` export 수 | 6 (실사용 20) |
| 에이전트 간 직접 호출 import | `four_phase_arc_generator` → 6, `director` → 7, `chief_writer` → 5 |

## 7. 성숙도 근거 (Maturity Evidence)

### 왜 "Pre-production"인가 (MVP가 아닌 이유)
- **관측성·telemetry 완비**: `base_agent.py:592-682`의 `_log_llm_call_to_db`가 모델·프롬프트·응답·토큰·비용·에러유형·재시도·continuation count를 모두 DB 저장. `SessionLogger`가 병렬 기록.
- **비용 추적**: `MetricsCollector`(`base_agent.py:37-41`)가 per-agent, per-model 비용 추적. `_session_token_cost_kwargs`(`:504-533`)로 캐시 토큰까지 분해.
- **복원력 검증됨**: 22회 네트워크 재시도(`:296`), 3회 rate limit 재시도, 모델 폴백 체인(primary → backup → 2.5-pro), key rotation(3개 키 지원), 30분 쿼터 캐시 — 야간 무인 운영 전제.
- **테스트 흔적**: MEMORY.md 기준 3,170 테스트 통과, ruff 0 violations.

### 왜 "Production-ready"가 아닌가
- **BaseAgent God Object** (P0-1) — SRP 위반으로 향후 유지보수 리스크.
- **LLM 호출 경로 이중화** (P0-2) — 캐시 경로가 telemetry 바이패스.
- **프롬프트 이중 관리** (P0-3) — YAML SSOT 마이그레이션 미완.
- **`response_schema` 불균등** (P1-6) — 타입 안정성 계약이 일부 에이전트에만.
- **Gemini 커플링** (P1-3) — LLMRouter 추상화가 응답 처리에서 깨짐.

## 8. 권장 로드맵 (Recommendations)

### 단기 (1~2주 / 품질 보강)
1. **P0-2 해결** — `generate_content_via_router` 직접 호출 7개 지점 전부 `BaseAgent._ask_with_cached_context`로 치환. telemetry/비용 추적 일원화.
2. **P0-3 해결** — `manager.py`, `block_enricher.py`, `arc_corrector.py` 등 14개 잔존 인라인 prompt를 YAML로 이전. `_INLINE_*` fallback 제거.
3. **P1-6 해결** — ChiefWriter, Director, Manager에 `response_schema` 필수 적용(각각의 state_updates/audit_result/ensemble_result 스키마 정의).

### 중기 (2~4주 / 구조 개선)
4. **P0-1 해결** — BaseAgent를 5개 믹스인으로 분해:
   - `_ApiLifecycleMixin` (키 순환, 쿼터 폴백, 네트워크 재시도)
   - `_ResponseParserMixin` (`_extract_json_robust`, `_parse_and_repair_hard`, `_validate_response`)
   - `_PromptSafetyMixin` (`_escape_braces`, `_apply_prompt_size_gate`)
   - `_TelemetryMixin` (`_log_llm_call_to_db`, `_build_metric_usage_payload`)
   - `_ContextCacheMixin` (`_get_or_create_context_cache`, `_ask_with_cached_context`)
5. **P1-1 해결** — `agents/runtime/`, `agents/components/`, `agents/validators/` 서브디렉토리 분리.
6. **P1-3 해결** — `LLMResponse`에 provider-agnostic `thinking_parts`, `truncated`, `finish_reason_enum` 추가. `_extract_and_merge_response` 내부에서 Gemini-specific 접근자 제거.

### 장기 (1~3개월 / 전략적)
7. **P1-4 해결** — `three_phase_blueprint_runtime.py`(3,186) · `director_ensemble.py`(2,874) · `unified_blueprint_validator.py`(2,786) · `chief_writer.py`(2,601) 추가 분해. runtime 내 router/coordinator/bootstrap을 각자 파일로.
8. **에이전트 카탈로그 문서화** — 20개 BaseAgent 자식 + 30개 서비스 클래스의 책임·호출 관계를 `docs/agents/CATALOG.md`로. 신규 개발자 온보딩 비용 절감.
9. **단위 테스트 강화** — 현재 BaseAgent가 거대해서 mocking 비용이 높음. 믹스인 분해 후(단계 4) 각 믹스인을 독립 테스트.
10. **성능 프로파일링** — 앙상블 팬아웃 6개 지점의 실제 p50/p95 latency 수집. `_TIMEOUTS`(각 300s) 값이 실측 기반인지 검증.
