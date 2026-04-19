# 글도비 전역 코드베이스 서베이 마스터 오더

Date: 2026-04-19
Status: active
Tracks: 10 (병렬 독립 실행)
Output Dir: `docs/2026-04-19/survey/`

## 목적

글도비 코드베이스의 현재 성숙도 수준(MVP/POC/Pre-production/Production)을 판정하고,
전 영역에 걸쳐 개선점, 기술 부채, 아키텍처 리스크, 품질 갭을 식별한다.

## 코드베이스 규모 요약

| 항목 | 수치 |
|------|------|
| Python 파일 수 | 959 |
| 총 LOC (Python) | ~103,000 |
| main_a.py 단독 | ~220,000 lines |
| 테스트 파일 | 424 |
| 핵심 모듈 (modules/core) | 166 files |
| 에이전트 (modules/domain/agents) | 56 files |
| 장르 수 | 9 (무협/헌터/투자/작곡가/요리/대체역사/배우물/스포츠/의학) |

## 실행 규칙

1. 각 트랙은 **독립적**이다. 다른 트랙 결과에 의존하지 않는다.
2. 출력 파일명: `T{N}-{slug}.md` (예: `T01-monolith.md`)
3. 출력 경로: `docs/2026-04-19/survey/T{N}-{slug}.md`
4. 각 트랙 문서는 아래 **공통 출력 스키마**를 따른다.
5. 코드를 **읽기만** 한다. 수정하지 않는다.
6. 발견 사항은 반드시 **파일 경로 + 라인 번호** 근거를 포함한다.

## 공통 출력 스키마

```markdown
# T{N}: {트랙 제목}

Surveyor: Claude Code (Terminal {N})
Date: 2026-04-19
Scope: {조사 범위 1줄 요약}

## 1. Executive Summary
- 성숙도 판정: MVP / POC / Pre-production / Production-ready
- 한줄 요약

## 2. 강점 (Strengths)
- 항목별 근거 포함

## 3. 개선 필수 (Critical Issues) — P0
- 즉시 수정 필요. 프로덕션 블로커.
- 각 항목: 파일:라인, 설명, 영향도, 권장 조치

## 4. 개선 권장 (Major Issues) — P1
- 기술 부채. 중기 로드맵에 반영 필요.
- 각 항목: 파일:라인, 설명, 영향도, 권장 조치

## 5. 개선 검토 (Minor Issues) — P2
- nice-to-have. 리팩토링 기회.
- 각 항목: 파일:라인, 설명, 권장 조치

## 6. 수치 지표 (Metrics)
- 트랙별 관련 정량 지표

## 7. 성숙도 근거 (Maturity Evidence)
- 이 트랙 관점에서의 성숙도 판정 근거

## 8. 권장 로드맵 (Recommendations)
- 우선순위별 개선 로드맵
```

---

## 10개 트랙 정의

### T01 — main_a.py 모놀리스 분석
- **파일**: `main_a.py` (~220K lines)
- **슬러그**: `T01-monolith`
- **핵심 질문**: 이 파일이 왜 220K인가? 분리 가능한 책임 단위는? God Object 패턴이 있는가?
- **조사 항목**:
  - 클래스/함수 목록과 라인 수 분포
  - 책임 영역 분류 (UI, 비즈니스 로직, DB, API, 상태 관리 등)
  - 순환 의존성, 밀결합 패턴
  - 글로벌 상태 사용 패턴
  - 중복 코드 블록
  - 에러 핸들링 일관성
  - 분리 후보 모듈 식별

### T02 — modules/core/ 핵심 엔진 심층 조사
- **파일**: `modules/core/` (166 files)
- **슬러그**: `T02-core-engine`
- **핵심 질문**: 핵심 엔진의 설계 품질은? Dead code는? 모듈 간 결합도는?
- **조사 항목**:
  - 모듈별 책임 매핑 (SRP 준수 여부)
  - 공통 디자인 패턴 식별 (Factory, Strategy, Observer 등)
  - Dead code / 미사용 모듈 탐지
  - 에러 전파 체인 품질
  - bare except 패턴 현황
  - 타입 힌트 커버리지
  - DB 접근 패턴 일관성
  - 스레드 안전성 (Lock, atomic 사용)

### T03 — Agent 아키텍처 조사
- **파일**: `modules/domain/agents/` (56 files)
- **슬러그**: `T03-agents`
- **핵심 질문**: 에이전트 시스템의 설계 패턴은 일관적인가? 책임이 명확한가?
- **조사 항목**:
  - base_agent.py → 파생 에이전트 상속 구조
  - 에이전트 간 통신 패턴 (직접 호출? 메시지? 이벤트?)
  - 프롬프트 구성 패턴 (하드코딩 vs 템플릿 vs YAML)
  - LLM 호출 래핑 패턴 일관성
  - 에이전트별 라인 수와 복잡도 분포
  - 캐싱 전략 일관성
  - 에이전트 오케스트레이션 흐름

### T04 — API / Protocol / Validation 계층
- **파일**: `modules/api/`, `modules/protocols/`, `modules/validation/`, `contracts/`
- **슬러그**: `T04-api-protocol`
- **핵심 질문**: 시스템 경계의 계약 이행이 견고한가? 검증 누락은?
- **조사 항목**:
  - API 엔드포인트 목록과 인증/인가 패턴
  - 프로토콜 정의와 실제 구현 일치 여부
  - 입력 검증 커버리지 (시스템 경계에서)
  - contracts/ 디렉토리의 계약 이행 감사
  - 에러 응답 표준화
  - Rate limiting / retry 패턴

### T05 — 테스트 스위트 품질 감사
- **파일**: `tests/` (424 files)
- **슬러그**: `T05-test-quality`
- **핵심 질문**: 테스트 커버리지는 충분한가? 테스트 품질은?
- **조사 항목**:
  - 테스트 파일 수 대비 소스 파일 수 비율
  - 커버리지 갭 식별 (테스트 없는 핵심 모듈)
  - 테스트 패턴: unit / integration / e2e / property / chaos 분포
  - Mock 사용 패턴과 품질
  - Flaky test 패턴 (sleep, 시간 의존, 네트워크 의존)
  - conftest.py fixture 설계 품질
  - xfail / skip 마커 현황
  - 테스트 실행 시간 추정

### T06 — 장르 시스템 무결성
- **파일**: `modules/core/genre_guards/`, `config/`, genre 관련 전역 코드
- **슬러그**: `T06-genre-integrity`
- **핵심 질문**: 9개 장르 시스템이 일관적으로 구현되었는가? 오염 방지는 견고한가?
- **조사 항목**:
  - Genre Checklist 16항목 전량 감사 (MEMORY.md 참조)
  - 장르별 Guard 구현 일관성
  - HUD Manager 구현 일관성
  - 장르 간 용어 오염 방지 (크로스 장르 guard 테스트)
  - config/ 하 장르별 설정 파일 완전성
  - primitive_forbidden.json 규칙 완전성
  - 장르 추가 시 필요한 작업량 평가

### T07 — Stage 파이프라인 (Stage0~4) 흐름 분석
- **파일**: `modules/core/stage0/`, stage 관련 오케스트레이터, main_a.py 내 stage 진입점
- **슬러그**: `T07-stage-pipeline`
- **핵심 질문**: 5단계 파이프라인의 상태 전이가 안전한가? 에러 복구 경로는?
- **조사 항목**:
  - Stage0→1→2→3→4 전이 흐름 매핑
  - 각 Stage의 진입 조건 / 종료 조건
  - Stage 간 데이터 핸드오프 계약
  - 에피소드 경계 처리 (에피소드 번호 관리, 연속성)
  - 실패 시 복구/재시도 로직
  - Stage별 LLM 호출 패턴과 비용 최적화
  - Arc 시스템과 Stage 파이프라인의 교차점

### T08 — Config / Data / Contract 계층
- **파일**: `config/`, `contracts/`, `datasets/`, `libraries/`, YAML/JSON 전체
- **슬러그**: `T08-config-data`
- **핵심 질문**: 설정/데이터 파일이 체계적으로 관리되는가? 스키마 검증이 있는가?
- **조사 항목**:
  - YAML/JSON 파일 전량 목록과 용도 분류
  - 스키마 정의 존재 여부 (pydantic, jsonschema 등)
  - 설정 로딩 패턴 (fail-safe? fail-fast?)
  - 환경별 설정 분리 (dev/prod/test)
  - 하드코딩된 설정값 vs 외부화된 설정
  - .env 관리 패턴
  - config/ 하위 디렉토리 구조 논리성

### T09 — Lite Mode / Desktop / Bridge 주변 시스템
- **파일**: `lite_mode/`, `geuldobi-desktop/`, `modules/api/bridge_server.py`, `visual_lab/`
- **슬러그**: `T09-peripherals`
- **핵심 질문**: 주변 시스템의 성숙도는? 코어와의 통합 품질은?
- **조사 항목**:
  - lite_mode: Selenium 자동화 안정성, 에러 핸들링
  - geuldobi-desktop: Electron 앱 구조, IPC, 빌드 파이프라인
  - bridge_server: API 설계, 보안, 동시성 처리
  - visual_lab: 이미지 생성 파이프라인 완성도
  - 코어 시스템과의 결합도 / 의존 방향
  - test_mode/와 lite_mode/의 중복 코드

### T10 — 보안 / 성능 / 운영 관점
- **파일**: 전역 (크로스컷 조사)
- **슬러그**: `T10-security-ops`
- **핵심 질문**: 프로덕션 운영에 필요한 보안/성능/관측 수준을 갖추고 있는가?
- **조사 항목**:
  - API 키 관리 (.env, 하드코딩 여부, 키 로테이션)
  - SQL Injection / Command Injection 패턴
  - 인코딩 처리 일관성 (UTF-8)
  - DB 패턴: 커넥션 풀링, 트랜잭션, WAL
  - 로깅 레벨 / 구조화 로깅 여부
  - 리소스 해제 (파일 핸들, DB 커넥션)
  - 메모리 사용 패턴 (대형 문자열, 리스트 누적)
  - 재시도/백오프 전략
  - 비용 추적 (LLM API 호출 비용)
  - 크래시 덤프 / 복구 메커니즘

---

## 실행 방법

각 터미널에서 아래 프롬프트를 복사하여 Claude Code에 입력한다:

```
T{N}번 조사 실행 — docs/2026-04-19/survey/SURVEY-ORDER.md 참조
```

## 감리 (Audit) 절차

10개 트랙 문서가 모두 완성되면, 마스터 터미널에서:

1. 10개 T{N} 문서를 전부 읽는다
2. 교차 검증: 트랙 간 모순 / 중복 발견 식별
3. 성숙도 종합 판정 (각 트랙 판정의 가중 합산)
4. 통합 보고서 작성: `docs/2026-04-19/survey/AUDIT-REPORT.md`

성숙도 판정 기준:
| 등급 | 기준 |
|------|------|
| POC | 개념 검증 수준. 프로덕션 불가. |
| MVP | 핵심 기능 동작. 제한적 사용 가능. 주요 갭 존재. |
| Pre-production | 대부분 기능 완성. 안정성/보안/운영 보강 필요. |
| Production-ready | 실 서비스 투입 가능. 모니터링/복구 체계 구비. |
