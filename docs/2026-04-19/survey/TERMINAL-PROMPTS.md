# 10 터미널 병렬 실행 프롬프트

각 프롬프트를 새 Claude Code 터미널에 **그대로** 복사-붙여넣기 한다.
모든 출력은 `docs/2026-04-19/survey/` 아래에 고정된다.

---

## Terminal 1

```
글도비 전역 서베이 T01 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T01 트랙(main_a.py 모놀리스 분석)을 수행해.

조사 대상: main_a.py (약 220K lines)
핵심 질문: 이 파일이 왜 220K인가? 분리 가능한 책임 단위는? God Object 패턴이 있는가?

조사 항목:
- 클래스/함수 목록과 라인 수 분포 (상위 20개)
- 책임 영역 분류 (UI, 비즈니스 로직, DB, API, 상태 관리 등)
- 순환 의존성, 밀결합 패턴
- 글로벌 상태 사용 패턴
- 중복 코드 블록
- 에러 핸들링 일관성
- 분리 후보 모듈 식별 (구체적 라인 범위)

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T01-monolith.md에 저장해.
```

---

## Terminal 2

```
글도비 전역 서베이 T02 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T02 트랙(modules/core/ 핵심 엔진 심층 조사)을 수행해.

조사 대상: modules/core/ (166 files)
핵심 질문: 핵심 엔진의 설계 품질은? Dead code는? 모듈 간 결합도는?

조사 항목:
- 모듈별 책임 매핑 (SRP 준수 여부)
- 공통 디자인 패턴 식별 (Factory, Strategy, Observer 등)
- Dead code / 미사용 모듈 탐지
- 에러 전파 체인 품질
- bare except 패턴 현황 및 위치
- 타입 힌트 커버리지
- DB 접근 패턴 일관성
- 스레드 안전성 (Lock, atomic 사용)

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T02-core-engine.md에 저장해.
```

---

## Terminal 3

```
글도비 전역 서베이 T03 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T03 트랙(Agent 아키텍처 조사)을 수행해.

조사 대상: modules/domain/agents/ (56 files)
핵심 질문: 에이전트 시스템의 설계 패턴은 일관적인가? 책임이 명확한가?

조사 항목:
- base_agent.py → 파생 에이전트 상속 구조 맵
- 에이전트 간 통신 패턴 (직접 호출? 메시지? 이벤트?)
- 프롬프트 구성 패턴 (하드코딩 vs 템플릿 vs YAML)
- LLM 호출 래핑 패턴 일관성
- 에이전트별 라인 수와 복잡도 분포
- 캐싱 전략 일관성
- 에이전트 오케스트레이션 흐름 (누가 누구를 호출하는가)

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T03-agents.md에 저장해.
```

---

## Terminal 4

```
글도비 전역 서베이 T04 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T04 트랙(API / Protocol / Validation 계층)을 수행해.

조사 대상: modules/api/ (7 files), modules/protocols/ (5 files), modules/validation/ (17 files), contracts/ 디렉토리
핵심 질문: 시스템 경계의 계약 이행이 견고한가? 검증 누락은?

조사 항목:
- API 엔드포인트 목록과 인증/인가 패턴
- 프로토콜 정의와 실제 구현 일치 여부
- 입력 검증 커버리지 (시스템 경계에서)
- contracts/ 디렉토리의 계약 이행 감사
- 에러 응답 표준화
- Rate limiting / retry 패턴

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T04-api-protocol.md에 저장해.
```

---

## Terminal 5

```
글도비 전역 서베이 T05 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T05 트랙(테스트 스위트 품질 감사)을 수행해.

조사 대상: tests/ (424 files), conftest.py, pytest 설정
핵심 질문: 테스트 커버리지는 충분한가? 테스트 품질은?

조사 항목:
- 테스트 파일 수 대비 소스 파일 수 비율
- 커버리지 갭 식별 (테스트 없는 핵심 모듈 top 10)
- 테스트 패턴 분포: unit / integration / e2e / property / chaos
- Mock 사용 패턴과 품질 (over-mocking 여부)
- Flaky test 패턴 (sleep, 시간 의존, 네트워크 의존)
- conftest.py fixture 설계 품질
- xfail / skip 마커 현황과 이유
- 테스트 네이밍 컨벤션 일관성

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T05-test-quality.md에 저장해.
```

---

## Terminal 6

```
글도비 전역 서베이 T06 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T06 트랙(장르 시스템 무결성)을 수행해.

조사 대상: modules/core/genre_guards/, config/ 하위 장르별 설정, 장르 관련 코드 전역
지원 장르 9개: 무협, 헌터, 투자, 작곡가, 요리, 대체역사, 배우물, 스포츠, 의학
핵심 질문: 9개 장르가 일관적으로 구현되었는가? 오염 방지는 견고한가?

조사 항목 — 아래 16개 체크포인트를 9개 장르 전량 교차 감사:
1. constants.py (GenreTypes/HUDKeys/NPCHUDKeys)
2. preset_registry.py (GENRE_PRESETS/NPC_GENRE_PRESETS)
3. genre_guards/ (guard 존재 + __init__.py factory)
4. genre_hud_manager.py (HUDManager + factory)
5. genre_stage_prompts.py (STAGE2/3 prompts + dicts)
6. analyst_libraries JSON (narrative archetypes)
7. strategies/ (strategy + genre_manager.py) — 또는 삭제 여부
8. main_a.py (_select_genre + npc_hud_keys + genre_fallback_keys)
9. director.py (scoring + genre-specific validation)
10. analyst.py (genre_library_map + _detect_genre)
11. chief_writer.py (emotion patterns + scene keywords + genre_code_map)
12. state_tracker.py (_SKILL_LOG_LABEL)
13. story_expander.py + reverse_expander.py (genre lists)
14. primitive_forbidden.json (genre_rules)
15. narrative_diversity.py (CONTRASTIVE_EXAMPLES)
16. stage0/__init__.py (SUPPORTED_GENRES)

누락된 장르 등록이 있으면 정확한 위치를 기록해.
코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T06-genre-integrity.md에 저장해.
```

---

## Terminal 7

```
글도비 전역 서베이 T07 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T07 트랙(Stage 파이프라인 흐름 분석)을 수행해.

조사 대상: modules/core/stage0/, stage 관련 오케스트레이터, main_a.py 내 stage 진입점
핵심 질문: Stage0→1→2→3→4 파이프라인의 상태 전이가 안전한가? 에러 복구 경로는?

조사 항목:
- Stage0→1→2→3→4 전이 흐름 전체 매핑
- 각 Stage의 진입 조건 / 종료 조건
- Stage 간 데이터 핸드오프 계약 (어떤 데이터가 넘어가는가)
- 에피소드 경계 처리 (번호 관리, 연속성 보장)
- 실패 시 복구/재시도 로직
- Stage별 LLM 호출 패턴과 비용 포인트
- Arc 시스템과 Stage 파이프라인의 교차점
- rollback 메커니즘

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T07-stage-pipeline.md에 저장해.
```

---

## Terminal 8

```
글도비 전역 서베이 T08 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T08 트랙(Config / Data / Contract 계층)을 수행해.

조사 대상: config/, contracts/, datasets/, libraries/, YAML/JSON 파일 전체
핵심 질문: 설정/데이터 파일이 체계적으로 관리되는가? 스키마 검증이 있는가?

조사 항목:
- config/ 하위 구조 전체 매핑 (디렉토리 트리)
- YAML/JSON 파일 전량 목록과 용도 분류
- 스키마 정의 존재 여부 (pydantic model, jsonschema 등)
- 설정 로딩 패턴 (fail-safe? fail-fast?)
- 환경별 설정 분리 (dev/prod/test 구분 여부)
- 하드코딩된 설정값 vs 외부화된 설정 (매직 넘버 탐지)
- .env / .env.example 일치 여부
- contracts/ 디렉토리 구조와 계약 형식

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T08-config-data.md에 저장해.
```

---

## Terminal 9

```
글도비 전역 서베이 T09 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T09 트랙(Lite Mode / Desktop / Bridge 주변 시스템)을 수행해.

조사 대상: lite_mode/ (25 files), geuldobi-desktop/, modules/api/bridge_server.py, visual_lab/, test_mode/
핵심 질문: 주변 시스템의 성숙도는? 코어와의 통합 품질은?

조사 항목:
- lite_mode: Selenium 자동화 안정성, 에러 핸들링, state_ledger 설계
- geuldobi-desktop: Electron 앱 구조, IPC 패턴, 빌드 설정, main.js
- bridge_server: API 설계, 보안 (인증 여부), 동시성 처리
- visual_lab: 이미지 생성 파이프라인 완성도
- 코어 시스템과의 결합도 / 의존 방향 (import 분석)
- test_mode/와 lite_mode/의 중복 코드

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T09-peripherals.md에 저장해.
```

---

## Terminal 10

```
글도비 전역 서베이 T10 실행.

docs/2026-04-19/survey/SURVEY-ORDER.md를 읽고 T10 트랙(보안 / 성능 / 운영 관점)을 수행해.

조사 대상: 전역 크로스컷 조사 (모든 Python 파일 대상)
핵심 질문: 프로덕션 운영에 필요한 보안/성능/관측 수준을 갖추고 있는가?

조사 항목:
- API 키 관리: .env 사용 패턴, 하드코딩 여부 (grep "api_key", "secret", "password"), 키 로테이션
- SQL Injection: raw SQL 사용 패턴, 파라미터 바인딩 여부
- Command Injection: subprocess/os.system 사용 패턴
- 인코딩: UTF-8 일관성, encode/decode 호출 패턴
- DB: 커넥션 풀링, 트랜잭션 관리, WAL 모드 사용
- 로깅: 레벨 분류, 구조화 여부, 민감정보 로깅 여부
- 리소스 해제: with 문 사용, 파일 핸들 / DB 커넥션 close 패턴
- 메모리: 대형 문자열 누적, 리스트 무한 성장 패턴
- 재시도: 백오프 전략, 무한 루프 방지
- 비용 추적: LLM API 호출 비용 모니터링
- 크래시 복구: crash_dump.log 사용, 복구 메커니즘

코드를 수정하지 마. 읽기만 해.
출력 형식은 SURVEY-ORDER.md의 공통 출력 스키마를 따르고, 결과를 docs/2026-04-19/survey/T10-security-ops.md에 저장해.
```

---

## 감리 실행 (10개 완료 후)

```
글도비 전역 서베이 감리 실행.

docs/2026-04-19/survey/ 디렉토리의 T01~T10 문서 10개를 전부 읽고 통합 감리 보고서를 작성해.

감리 항목:
1. 10개 트랙 성숙도 판정 종합 (가중 합산)
2. 트랙 간 교차 검증: 모순 / 중복 발견 식별
3. P0 이슈 통합 목록 (전 트랙)
4. P1 이슈 통합 목록 (전 트랙)
5. 전체 성숙도 최종 판정: POC / MVP / Pre-production / Production-ready
6. Top 10 개선 우선순위 (ROI 기반 정렬)
7. 아키텍처 레벨 권장사항

결과를 docs/2026-04-19/survey/AUDIT-REPORT.md에 저장해.
```
