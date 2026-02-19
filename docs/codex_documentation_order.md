# Codex 오더: 글도비 시스템 상세 문서 작성

> 이 문서는 Codex에게 "신규 개발자용 시스템 문서"를 작성시키기 위한 **프롬프트/지시서**입니다.
> Codex에게 이 파일을 통째로 전달하세요.

---

## 목적

이 코드베이스(`글도비`)는 **AI 웹소설 자동 생성 시스템**입니다.
신규 개발자가 코드를 이해하고 수정할 수 있도록, 시스템 전체를 설명하는 **상세 기술 문서**를 작성하세요.

**대상 독자**: Python 중급 이상, LLM API 경험 있음, 이 프로젝트는 처음 보는 개발자

---

## 출력 요구사항

- 파일명: `docs/시스템_아키텍처_상세.md`
- 분량: 제한 없음 (충분히 상세하게)
- 언어: 한국어 (코드/변수명은 원문 유지)
- 다이어그램: Mermaid 문법 사용

---

## 반드시 읽어야 할 파일 (우선순위순)

### Tier 1 — 필독 (구조 파악)
| 파일 | 읽는 이유 |
|------|-----------|
| `CLAUDE.md` | 프로젝트 전체 현황, 대원칙, 파일 맵 |
| `참고자료.md` | 아키텍처 상세, 버그 패턴, 개선 아이디어 |
| `main_a.py` (전체) | 진입점, SovereignApp 클래스, Stage 0/2/4 호출 흐름 |
| `modules/core/stage2_orchestrator.py` | Arc 생성 파이프라인 |
| `modules/core/stage4_orchestrator.py` | 원고 생성 파이프라인 |
| `modules/core/stage3_orchestrator.py` | Blueprint 파이프라인 |

### Tier 2 — 핵심 모듈
| 파일 | 읽는 이유 |
|------|-----------|
| `modules/domain/agents/director.py` + `director_*.py` 5개 | Director 에이전트 (최종 결정권자) |
| `modules/domain/agents/chief_writer.py` + `chief_writer_*.py` 2개 | 원고 생성 엔진 |
| `modules/domain/agents/analyst.py` | Arc 분석/설계 에이전트 |
| `modules/domain/agents/base_agent.py` | 모든 에이전트의 부모 클래스 |
| `modules/core/prompt_builder.py` | 프롬프트 조립기 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 |
| `modules/core/db_manager.py` | SQLite DB 매니저 |

### Tier 3 — 검증/가드 시스템
| 파일 | 읽는 이유 |
|------|-----------|
| `modules/validation/validation_orchestrator.py` | 검증 파이프라인 총괄 |
| `modules/validation/scoring_validator.py` | 점수 기반 합격 판정 |
| `modules/validation/continuity_validator.py` | 연속성 검증 |
| `modules/validation/blocking_validator_entity_checks.py` | 엔티티 차단 검증 |
| `modules/core/genre_guards/base_guard.py` | 장르 가드 베이스 |
| `modules/core/genre_guards/wuxia_guard.py` | 무협 장르 가드 (대표 구현) |
| `modules/core/genre_guards/work_guard.py` | 작품별 커스텀 가드 |

### Tier 4 — 상태/연속성 시스템
| 파일 | 읽는 이유 |
|------|-----------|
| `modules/domain/agents/state_tracker.py` + `state_tracker_*.py` | NPC/아이템/플롯 상태 추적 |
| `modules/domain/agents/state_extractor.py` | Arc에서 상태 추출 |
| `modules/core/world_state.py` | 세계 상태 관리자 |
| `modules/core/fact_ledger.py` | 누적 팩트 원장 |
| `modules/domain/agents/continuity_inspector.py` | 연속성 검사기 |

### Tier 5 — DI/컨텍스트 시스템
| 파일 | 읽는 이유 |
|------|-----------|
| `modules/core/stage2_context.py` | Stage 2 DI 컨텍스트 (44 슬롯) |
| `modules/core/stage3_context.py` | Stage 3 DI 컨텍스트 (19 슬롯) |
| `modules/core/stage4_context.py` | Stage 4 DI 컨텍스트 (24 슬롯) |

### Tier 6 — 설정/프롬프트
| 파일 | 읽는 이유 |
|------|-----------|
| `config/settings/validation.yaml` | 검증 임계값 설정 |
| `config/prompts/` (아무 yaml 3~4개) | 프롬프트 외부화 패턴 이해 |
| `pyproject.toml` | 프로젝트 설정, ruff, pytest |

### Tier 7 — 테스트
| 파일 | 읽는 이유 |
|------|-----------|
| `tests/` 디렉토리 구조 (`ls`) | 테스트 구성 파악 |
| 아무 테스트 파일 2~3개 | 테스트 패턴 이해 |

---

## 문서 구조 (이 순서대로 작성)

### 1. 시스템 개요 (1페이지)
- 글도비가 뭔지 한 문단 설명
- 입력(사용자가 주는 것)과 출력(시스템이 만드는 것)
- 기술 스택: Python, Gemini API, SQLite, sqlite-vec

### 2. 4대 원칙 (0.5페이지)
- CLAUDE.md의 4대 원칙을 **왜 그런 원칙이 필요한지** 배경과 함께 설명
- 각 원칙을 위반하면 어떤 버그가 생기는지 실제 사례

### 3. 파이프라인 전체 흐름 (2~3페이지)
- **Mermaid 시퀀스 다이어그램** 필수
- Stage 0 → Stage 2 → Stage 3 → Stage 4 각각:
  - 입력/출력
  - 주요 에이전트
  - 검증 단계
  - 실패 시 재시도 로직
- 에피소드 1개 생성의 전체 데이터 흐름을 추적

### 4. 에이전트 시스템 (2~3페이지)
- `base_agent.py`의 핵심 메서드: `ask()`, `_extract_json_robust()`, Context Caching
- Director의 역할과 권한 (내각제 비유)
- Chief Writer의 3-후보 앙상블 전략
- Analyst의 Arc 설계 과정
- 에이전트 간 데이터 전달 방식
- **에이전트 목록 전체** (이름, 파일, 한 줄 역할)

### 5. 검증 파이프라인 (2페이지)
- ValidationOrchestrator의 체인 순서
- 각 Validator의 역할:
  - Pre-LLM Validator (Python 룰 기반)
  - Blocking Validator (엔티티 체크)
  - Continuity Validator (연속성)
  - Scoring Validator (점수 합산)
  - Consensus Validator (다수결)
- 합격/불합격 판정 기준
- adaptive threshold 메커니즘

### 6. 장르 가드 시스템 (1페이지)
- Guard 체인: GenreGuard → WorkGuard → StyleGuard
- 각 장르(무협/헌터/투자/판타지 + 확장 6개)의 검증 항목
- WorkGuard YAML 스키마
- 새 장르 추가하는 법

### 7. 상태 관리 (2페이지)
- StateTracker: NPC/아이템/플롯 추적
- WorldStateManager: 세계 상태 문서
- FactLedger: 누적 팩트 원장
- Episode Chain Links: 에피소드 연결고리
- Volume/Series Summary: 계층적 요약 피라미드
- NPC Registry: NPC 등록/이력 관리
- 상태 동기화 문제 (DI ctx 스냅샷 → app write-back)

### 8. DI 컨텍스트 패턴 (1페이지)
- 왜 DI를 도입했는지 (God Object 문제)
- StageNContext 클래스 구조 (`__slots__`, `from_app()`)
- 콜백 패턴 (`self.app._private` → `self.ctx.public`)
- lazy init 패턴 (Stage 3)
- **주의사항**: ctx는 스냅샷이므로 Stage 종료 후 app에 write-back 필수

### 9. 데이터베이스 스키마 (1페이지)
- `db_manager.py`의 테이블 목록과 컬럼
- 주요 쿼리 패턴
- JSON 컬럼 사용 규칙
- sqlite-vec 벡터 검색 (`vec_memory.py`)

### 10. 프롬프트 시스템 (1페이지)
- `config/prompts/*.yaml` 구조
- `PromptLoader` 싱글톤 패턴
- `PromptBuilder`의 프롬프트 조립 로직
- 프롬프트 변수 치환 규칙

### 11. 설정 시스템 (0.5페이지)
- `validation.yaml` 임계값
- `threshold_helper.py`의 `_threshold()` 패턴
- 설정 변경이 영향을 미치는 범위

### 12. 파일/디렉토리 구조 (1페이지)
- 트리 형태로 전체 구조
- 각 디렉토리의 역할 한 줄 설명
- 핵심 파일 Top 20 + 역할

### 13. 개발 가이드 (1페이지)
- 환경 설정 (Python 버전, 의존성)
- 테스트 실행법 (`PYTHONIOENCODING=utf-8` 필수 등)
- pre-commit 훅 (ruff + ruff-format)
- 커밋 컨벤션
- 코드 패턴 (V64 위임 패턴, 에러 핸들링 정책 등)

### 14. 자주 하는 작업 가이드 (1페이지)
- 새 에이전트 추가하는 법
- 새 장르 가드 추가하는 법
- 새 Validator 추가하는 법
- 프롬프트 수정하는 법
- 테스트 작성 패턴

### 15. 알려진 패턴과 주의사항 (1페이지)
- LLM 응답 타입 불확실성 (dict/list/string)
- `_safe_int()`, `_ikey()` 패턴
- MagicMock 전파 주의 (테스트)
- 캐시 무효화 규칙

---

## 품질 기준

1. **코드 레벨에서 설명할 것** — "Stage 2에서 Arc를 만듭니다"가 아니라 "`stage2_orchestrator.py`의 `run()` 메서드가 `analyst.analyze()`를 호출하여..." 수준
2. **실제 코드 인용** — 핵심 로직은 코드 블록으로 인용 (파일명:라인 표기)
3. **왜(Why) 설명** — 단순히 "이렇게 되어 있다"가 아니라 "이렇게 한 이유는..."
4. **다이어그램 필수** — 최소 3개: 전체 파이프라인, 에이전트 관계, 검증 체인
5. **예제 기반** — "에피소드 1개가 생성되는 과정"을 처음부터 끝까지 추적하는 예제 포함

---

## Codex 실행 설정 권장

```
모델: o3 또는 o4-mini
라운드: 제한 없음 (자동 완료)
컨텍스트: 이 파일 + 코드베이스 전체
출력: docs/시스템_아키텍처_상세.md
```

---

## 주의사항

- `참고자료.md`는 2000줄+ 문서이므로 반드시 읽을 것
- `main_a.py`는 4200줄+이므로 구조 파악 후 주요 메서드만 상세 읽기
- Stage 1은 사용하지 않음 (0→2→3→4)
- `memory_engine.py`는 삭제됨 — `vec_memory.py`가 단일 벡터 경로
- `writer.py`의 `write_v20_manuscript`는 외부 진입점용으로만 유지됨
