# T04: API / Protocol / Validation 계층

Surveyor: Claude Code (Terminal 4)
Date: 2026-04-19
Scope: `modules/api/`, `modules/protocols/`, `modules/validation/`, `contracts/` — 시스템 경계 계약 이행 / 입력 검증 / 응답 표준화 / 검증 파이프라인 감사

## 1. Executive Summary

- **성숙도 판정**: **Pre-production (영역 가중 평균 약 65/100)**
  - API 계층: Pre-production (70)
  - Protocol 계층: Production-ready (85)
  - Validation 계층: MVP→Pre-production (65)
  - Contracts 계층: POC (40)
- **한줄 요약**: 6-Tier 검증 파이프라인과 16개 typing.Protocol 정의는 견고한 골격을 갖췄지만, **bridge_server의 인증/CORS/Rate-limit 부재 + contracts/ JSON 스키마의 런타임 미검증**이 프로덕션 진입을 막는 핵심 결함이다.
- **핵심 메트릭**: 4계층 합계 약 14,000 LOC / HTTP·WS 엔드포인트 9개 / Protocol 16개 / Validator 클래스 11개 / JSON 스키마 11개 (jsonschema 호출 0건) / `bare except` 0건 / 광범위 `except Exception` 약 53건.

## 2. 강점 (Strengths)

### 2.1 Protocol 구조화 (가장 견고한 영역)

- `modules/protocols/agents.py:60-161` — 8개 Protocol(`PipelineGenerator`, `EnsembleGenerator`, `ArtifactValidator`, `ArtifactCritic`, `Corrector`, `DraftValidator`, `ConstraintCompilerProtocol`, `StateAggregator`)이 `@runtime_checkable` 적용 상태로 표준화.
- `modules/protocols/db_repository.py:16-209` — `DBRepositoryProtocol`이 209개 메서드를 명시적 계약으로 정의 → DB 엔진 교체 시 SRP 검증 가능.
- `modules/protocols/app_services.py:23-242` — UI/Audit/Project/State/Config 5개 서비스 경계 분리.
- `modules/protocols/validators.py:14-37` — `TierValidator`, `EpisodeAwareValidator` 2종 Protocol로 검증 계층 표준화.

### 2.2 응답 envelope 일관성

- `modules/api/bridge_server.py:192-200` — `_accepted/_ok/_err` 헬퍼로 모든 응답이 `{ok, code, message, data, run_id?}` 통일.
- `modules/api/run_validator.py:6-11` + `modules/api/risk_approval.py:7-11` — 에러 코드 분류(`INVALID_KEY`, `RUN_ALREADY_ACTIVE`, `RISK_APPROVAL_REQUIRED`, `RISK_APPROVAL_DUAL_CONTROL_REQUIRED` 등) + HTTP status 정확 매핑.

### 2.3 위험키 2-인 Dual Control

- `modules/api/risk_approval.py:100-180` — `RISK_KEYS = frozenset({"44","77","88","99"})` 대상 approval_id 검증 + 만료 체크 + `approved_by_primary != approved_by_secondary` 강제.
- `modules/api/control_plane_contract.py:1-92` — Authority 역할 3분할(authoritative_sink / companion_snapshot / compatibility_paths) 명시.

### 2.4 6-Tier 검증 파이프라인

- `modules/validation/validation_orchestrator.py` (1,695 LOC) — Tier 0.25 → 0.5 → 1 → 1.5 → 2 → 3 단계화. asyncio 기반 독립 검증 병렬화로 시간 단축.
- `modules/validation/blocking_validator.py:1-221` + 3개 서브모듈(`*_entity_checks.py:491`, `*_scene_checks.py:499`, `*_consistency_checks.py:444`) — NPC 부활/아이템 소유/장소 파괴/길이/Scope overflow 등 14개 명확한 결정적 검사.
- `modules/validation/continuity_validator.py` (1,265 LOC) — 에피소드 간 연속성($0 비용, ep>1에서만 활성화).
- `modules/validation/scoring_validator.py:101-127` — `_sanitize_manuscript()`가 `{}` escape + 제어문자 제거 + `_SANITIZE_MAX_CHARS` 길이 제한 → **prompt injection 방지** 명시 구현.

### 2.5 적응형 임계값 (V59)

- `modules/validation/validation_orchestrator.py:80-189` — 12개 장르 프로파일(`GENRE_THRESHOLD_PROFILES`) + 에피소드 유형 조정(opening +5, climax +3, finale +7) + 연속 결과 조정(5연속 pass −2, 3연속 fail +5).

### 2.6 Exception 분류 패턴

- `modules/validation/blocking_validator.py:187-201` — `(ImportError, TypeError, AttributeError)`는 re-raise, `(ValueError, KeyError, RuntimeError)`은 degraded=True로 안전 fallback. 프로그래밍 오류 vs 데이터 오류 분리는 모범 사례.
- `bare except` 사용 0건 (modules/validation/ 전체).

### 2.7 ProcessRunner 격리 아키텍처

- `modules/api/process_runner.py` (867 LOC) — `main_a.py`를 subprocess로 격리 → bridge_server 크래시가 실행 본체에 전파되지 않음.
- `modules/api/prompt_broker.py:127` — Mode B 인터랙티브 응답을 asyncio queue로 처리, 300초 timeout.

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. SQL 문자열 결합으로 인한 Injection 표면

- **위치**: `modules/api/bridge_server.py:1365-1367`
  ```
  cur = db.cursor.execute("SELECT COUNT(*) AS cnt FROM director_selections WHERE " + stage2_predicate)
  ```
- **설명**: `stage2_predicate`는 현재 내부 호출(`db._director_stage_predicate(2)`) 결과지만, predicate 빌더가 외부 입력에 노출될 경우 즉시 SQL injection. parameterized query로 강제하지 않는 패턴 자체가 결함.
- **영향도**: **High** — 데이터 유출 / 무결성 파괴.
- **권장 조치**: predicate를 named parameter + bind variable로 재작성. 동적 SQL이 불가피하면 화이트리스트 토큰 검증 추가.

### P0-2. 거의 모든 엔드포인트 인증 부재

- **위치**: `modules/api/bridge_server.py:2486-2688` (POST `/run/{run_id}/input`, POST `/stop`, GET `/status`, GET `/quality/summary`, GET `/quality/dashboard`, GET `/safe-ops/preview`, POST `/quality/review`, WS `/events`)
- **설명**: 9개 엔드포인트 중 `/run`만 RISK_KEYS에 한해 dual-control 승인이 적용. read-only 엔드포인트는 물론 **POST `/stop`과 WS `/events`도 익명 호출 가능**.
- **영향도**: **High** — 외부 노출 시 누구나 실행 중지/이벤트 스트림 도청 가능.
- **권장 조치**: API key 또는 mTLS 기반 게이트 미들웨어 추가. read-only도 최소 토큰 강제.

### P0-3. JSON Schema 런타임 검증 미연결

- **위치**: `contracts/` 11개 파일 + 코드베이스 전역
- **설명**: `jsonschema` import 0건. `phase0_design.schema.json`(12 KB), `bi_blockguide.schema.json`(6 KB) 등 핵심 스키마가 정의만 존재하고 런타임 검증이 없음. `POST /run`의 `inputs` dict, `POST /quality/review` body 모두 스키마 비검증 통과.
- **영향도**: **High** — 잘못된 페이로드가 ProcessRunner / DB까지 전파, 검증 책임이 코드 곳곳에 분산.
- **권장 조치**: `jsonschema.validate()` 도입. 우선 `POST /run`/`POST /quality/review`/`POST /run/{run_id}/input`의 body에 스키마 적용.

## 4. 개선 권장 (Major Issues) — P1

### P1-1. CORS 미들웨어 부재

- **위치**: `modules/api/bridge_server.py:2365-2369` (FastAPI 앱 초기화 구간)
- **설명**: `CORSMiddleware` 등록 없음. 데스크톱/Lite 클라이언트 외 브라우저 진입 시 차단 또는 보안정책 위반.
- **영향도**: Medium — 브라우저 통합 불가 / 향후 origin whitelist 누락 시 CSRF 표면 확대.
- **권장 조치**: `allow_origins`를 화이트리스트로 명시, credentials 모드 결정.

### P1-2. Rate Limiting 부재

- **위치**: `modules/api/bridge_server.py` 전체
- **설명**: 미들웨어 / decorator / 토큰버킷 없음.
- **영향도**: Medium — DDoS·abuse·실수 트래픽 폭주 시 ProcessRunner 큐 폭발.
- **권장 조치**: 인메모리 SlidingWindow 또는 redis-based limiter (`slowapi` 등) 적용. 특히 `POST /run`, `POST /quality/review` 우선.

### P1-3. 예외 메시지 정보 누설

- **위치**: `modules/api/bridge_server.py:2452, 2462` 등 `str(exc)` 직반환 패턴
- **설명**: 광범위 `except Exception` 후 메시지를 그대로 envelope에 실어 응답. 내부 경로/스택 단편이 외부로 노출.
- **영향도**: Medium — 정보 누설 → 공격 표면 정보 제공.
- **권장 조치**: 외부 응답엔 `INTERNAL_ERROR` + correlation_id만 반환, 상세는 서버 로그로.

### P1-4. `inputs` dict raw pass-through

- **위치**: `modules/api/bridge_server.py:2392`, `modules/api/run_validator.py:96`
- **설명**: key/sub_key는 화이트리스트 검증되지만 `inputs` dict는 검증 없이 ProcessRunner로 전달.
- **영향도**: Medium — 신뢰되지 않은 페이로드가 main_a.py 환경에 도달.
- **권장 조치**: key별 inputs 스키마 정의 + 검증.

### P1-5. validation_context dict 무검증 사용

- **위치**: `modules/validation/validation_orchestrator.py:345-400`, `modules/validation/continuity_validator.py:147-150`
- **설명**: `validation_context.get("encyclopedia"|"blueprint"|"martial_hud"|"prev_hud")`를 키 존재 가정 하에 직접 사용. 호출자 실수 시 silent KeyError → degraded 처리되어 마스킹.
- **영향도**: Medium — 검증이 통과처럼 보이지만 실제 검증되지 않은 상태.
- **권장 조치**: dataclass / pydantic Model로 context 계약화, 누락 필드는 명시적 예외.

### P1-6. LLM 호출 retry/backoff 미구현

- **위치**: `modules/validation/scoring_validator.py:150`, `modules/validation/advisory_validator.py:151`
- **설명**: `generate_content_via_router` 위임만 있고 exponential backoff 없음. 외부 API 5xx/429 시 단일 실패가 검증 실패로 직결.
- **영향도**: Medium — 운영 안정성 저하, 비용 낭비.
- **권장 조치**: 라우터 레벨에 `tenacity` 또는 자체 backoff(예: 3회 / 1·2·4초 지터) 통일 적용.

### P1-7. Silent degradation 누적

- **위치**: `modules/validation/blocking_validator.py:144-145, 194-201`, `modules/validation/scoring_validator.py:175-177`
- **설명**: 검증 예외 시 `degraded=True, passed=True`로 통과 처리. `_degraded_count` 증가는 있으나 임계 도달 시 차단/알림 없음.
- **영향도**: Medium — 버그 마스킹, 검증 의의 약화.
- **권장 조치**: degraded 누적 임계 도달 시 명시적 BLOCKING 결과로 승급 + 운영 알림.

### P1-8. Orphan JSON 스키마 다수

- **위치**: `contracts/audit_status.schema.json`, `contracts/bi_blockguide.schema.json`, `contracts/bi_wuxguide.schema.json`, `contracts/densification_harness.schema.json`, `contracts/profile_lock.schema.json`, `contracts/sequential_run_status.schema.json`, `contracts/material_bundle_summary.schema.json`
- **설명**: 코드 참조 없음(검증 호출 0건). 계약과 구현의 drift 우려.
- **영향도**: Medium — 의도된 계약이 실제로는 강제되지 않음.
- **권장 조치**: 각 스키마의 owner/사용처 식별 → 검증 활성화 또는 폐기.

## 5. 개선 검토 (Minor Issues) — P2

### P2-1. Protocol 미적합 에이전트 5종 어댑터 미구현

- **위치**: `modules/protocols/agents.py:37-42` 주석 명시
- **설명**: ChiefWriter(`generate_ensemble→list[dict]`), ConsensusValidator(`validate_with_consensus`), Critic(`critique_manuscript`), Director(`audit_manuscript`), StateExtractor(`extract_state`)가 Protocol 시그니처와 불일치.
- **권장 조치**: 어댑터 클래스 도입 → `isinstance(obj, Protocol)` 체크 가능화.

### P2-2. Protocol 검사가 Phase 4 이후에만 적용

- **위치**: 모든 Protocol consumer (코드 전반)
- **설명**: 현재는 duck typing. `runtime_checkable`은 정의됐으나 실제 isinstance 검사 호출 거의 없음.
- **권장 조치**: 외부 경계(에이전트 부트스트랩)에 isinstance 검증 도입.

### P2-3. threshold_profile 미지정 시 fallback

- **위치**: `modules/validation/validation_orchestrator.py:288`
- **설명**: 장르 자동 인식 실패 시 `_default` 사용 → 장르 특화 임계 미적용.
- **권장 조치**: 미지정 시 경고 로그 + 호출자에게 강제.

### P2-4. ProcessRunner subprocess timeout 부재

- **위치**: `modules/api/process_runner.py:412` 부근 (kill 신호만 존재)
- **설명**: 무한 hang 시 외부 timeout 없음.
- **권장 조치**: heartbeat 또는 wallclock budget 추가.

### P2-5. control_plane_contract.py와 contracts/artifact_contracts.json 분리

- **위치**: `modules/api/control_plane_contract.py:1-92` ↔ `contracts/artifact_contracts.json` (926B)
- **설명**: Authority 정의는 Python에, quality gates 정의는 JSON에 분산. 단일 SSOT 부재.
- **권장 조치**: 둘 중 하나로 통일하거나 JSON을 SSOT로 두고 Python이 로드.

### P2-6. 광범위 `except Exception` 분류 미흡

- **위치**: `modules/validation/validation_orchestrator.py` (12건), `modules/validation/scoring_validator.py` (10건) 등 합계 53건
- **설명**: bare except는 없으나 Exception 단일 catch가 다수.
- **권장 조치**: blocking_validator.py:194-201 패턴(programming vs data 분리)을 모든 모듈로 확산.

## 6. 수치 지표 (Metrics)

### 6.1 라인 수 / 파일 수

| 영역 | 파일 수 | LOC |
|------|---------|-----|
| modules/api/ | 7 | 4,333 |
| modules/protocols/ | 5 | ~700 |
| modules/validation/ | 17 | 8,973 |
| contracts/ | 11 | (JSON, ~52 KB) |
| **합계** | **40** | **~14,000** |

### 6.2 API 계층

| 항목 | 값 |
|------|-----|
| HTTP/WS 엔드포인트 | 9 (POST /run, POST /run/{id}/input, POST /stop, GET /status, GET /quality/summary, GET /quality/dashboard, GET /safe-ops/preview, POST /quality/review, WS /events) |
| 인증된 엔드포인트 | 1 (POST /run, RISK_KEYS만) |
| 표준 응답 envelope 적용 | 9/9 |
| CORS 미들웨어 | 0 |
| Rate limiter | 0 |
| 표준 에러 코드 | 11종 (INVALID_KEY, SUB_KEY_REQUIRED, RUN_ALREADY_ACTIVE, RISK_APPROVAL_REQUIRED 등) |

### 6.3 Protocol 계층

| 항목 | 값 |
|------|-----|
| Protocol 정의 | 16 (agents 8 / app_services 5 / db_repository 1 / validators 2) |
| `@runtime_checkable` 적용률 | 100% |
| DBRepositoryProtocol 메서드 | 209 |
| 미적합 에이전트(어댑터 필요) | 5 |

### 6.4 Validation 계층

| 항목 | 값 |
|------|-----|
| Tier 수 | 6 (0.25 / 0.5 / 1 / 1.5 / 2 / 3) |
| Validator 클래스 | 11+ (BlockingValidator, ContinuityValidator, ConsistencyValidator, ScoringValidator, AdvisoryValidator, PreLLMValidator 등) |
| BlockingValidator 검사 항목 | 14 |
| 장르 임계 프로파일 | 12 |
| `bare except` | 0 |
| 광범위 `except Exception` | ~53 |
| LLM retry/backoff | 0 (라우터 위임만) |

### 6.5 Contracts 계층

| 항목 | 값 |
|------|-----|
| 스키마 파일 | 11 |
| jsonschema.validate 호출 | 0 |
| 사용 중 schema (참조 식별) | 3-4 (artifact_contracts, phase0_design, phase0_ready_snapshot, source_manifest) |
| Orphan schema | 7-8 |

## 7. 성숙도 근거 (Maturity Evidence)

### 7.1 영역별 판정

| 영역 | 점수 | 단계 | 핵심 근거 |
|------|------|------|----------|
| API | 70 | Pre-production | envelope 일관·위험키 dual control은 견고하나 인증/CORS/Rate-limit 부재 + SQL concat |
| Protocol | 85 | Production-ready | typing.Protocol 16개 표준화, DB 209 메서드 명시 계약, 미적합 5건만 잔존 |
| Validation | 65 | MVP→Pre-production | 6-Tier·sanitization·degradation 우수, context 미검증·LLM retry 부재 |
| Contracts | 40 | POC | 스키마 정의만 존재, 런타임 검증 0건 |

### 7.2 Production 진입 기준 대비 격차

- **현재 충족**: 검증 Tier 체계, 응답 표준, Protocol 계약, dual-control 승인.
- **현재 미충족**:
  - 인증/인가(거의 모든 엔드포인트 무인증)
  - 입력 스키마 검증(JSON schema 미연결, inputs dict raw)
  - Rate limit / CORS
  - LLM retry/backoff
  - SQL parameterization 강제
  - silent degradation 임계 알림
- **결론**: P0 3건 + P1 8건 해소 시 Pre-production → Production-ready 승급 가능.

## 8. 권장 로드맵 (Recommendations)

### Week 1 — P0 (블로커 제거)

1. `bridge_server.py:1365-1367` SQL concat → bind parameter화. predicate 빌더 코드 점검.
2. API 인증 미들웨어 추가 (모든 엔드포인트 최소 토큰 강제, RISK_KEYS는 dual-control 유지).
3. `jsonschema` 도입 + `POST /run`, `POST /quality/review`, `POST /run/{id}/input` body 검증 활성화. 우선순위 스키마: `phase0_design.schema.json`, `material_bundle_summary.schema.json`.

### Week 2-3 — P1 (안정성/관측성)

4. CORS 미들웨어 + origin whitelist.
5. Rate limiter (`slowapi` 또는 인메모리 SlidingWindow). `POST /run` 우선.
6. `inputs` dict 스키마 + key별 분기 검증.
7. `validation_context`를 dataclass/pydantic으로 계약화.
8. LLM 라우터 레벨에 exponential backoff(3회/1·2·4초) 통일.
9. `str(exc)` 외부 응답 제거 + correlation_id 도입, 상세는 서버 로그.
10. degraded 누적 임계 알림 + 임계 초과 시 BLOCKING 승급.

### Month 2 — P2 (구조 개선)

11. Protocol 미적합 에이전트 5종 어댑터 구현.
12. 외부 경계(에이전트 부트스트랩)에 `isinstance(obj, Protocol)` 검사 도입.
13. Orphan JSON 스키마 7-8개 폐기 또는 검증 연결.
14. ProcessRunner subprocess heartbeat / wallclock timeout.
15. 광범위 `except Exception` 53건을 blocking_validator.py:194-201 패턴(programming vs data)으로 점진 분류.
16. control_plane_contract.py vs contracts/artifact_contracts.json SSOT 통합.

### 운영 문서화

- OpenAPI/Swagger 자동 생성(FastAPI 내장) + 인증 체계 문서화.
- 6-Tier validation 호출 시퀀스 다이어그램.
- JSON 스키마 owner/사용처 매핑 표.

---

**감사 완료일**: 2026-04-19
**감사자**: Claude Code (Terminal 4)
**다음 검토 권장**: P0 3건 해소 후 재검증.
