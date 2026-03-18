# 글도비 코드베이스 전수조사 보고서

Date: 2026-03-18
Status: **final** (3pass 감리 완료, 확신도 95%)
Canonical Path: `docs/2026-03-18/geuldobi-codebase-full-survey-2026-03-18.md`
Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
Baseline Dirty Summary: `M: response_schemas.py, base_agent.py, blueprint_ensemble.py, three_phase_blueprint_generator.py, test_base_agent.py, test_blueprint_patch_mode.py, test_legacy_reentry_reaudit.py + SSOT doc delta + doc deletes/adds + untracked: docs/OPUS/, projects/0_260318/`
Survey Mode: ROL 전수조사 (survey-only, 코드 수정 없음)

---

## 1. 코드베이스 규모 개요

| 항목 | 수치 |
|------|------|
| **소스 Python 파일** (`modules/`) | ~244개, ~145,000 LOC |
| **테스트 파일** (`tests/`) | 323개, ~82,000 LOC |
| **스크립트** (`scripts/`) | 38개, ~18,000 LOC |
| **에이전트** (`modules/domain/agents/`) | 47개 |
| **장르 설정** (`config/genres/`) | 10개 YAML |
| **프롬프트 설정** (`config/prompts/`) | 9개 YAML + JSON 라이브러리 |
| **주 엔트리포인트** | `main_a.py` (4,833 LOC) |
| **활성 프로젝트 DB** | `projects/0_260318/project_data.db` (14MB WAL) |

### 디렉토리별 LOC 분포

| 디렉토리 | 파일 수 | LOC |
|----------|--------|-----|
| `modules/core/` | 161 | ~91,000 |
| `modules/domain/` | 48 | ~40,000 |
| `modules/api/` | 8 | ~3,750 |
| `modules/validation/` | 17 | ~8,700 |
| `modules/models/` | 5 | ~490 |
| `modules/protocols/` | 5 | ~690 |
| `tests/` | 323 | ~82,000 |
| `scripts/` | 38 | ~18,000 |
| `tools/` + `tools2/` | 32 | ~12,800 |

---

## 2. Dirty State 분석 (d4e96804 이후)

### 2.1 수정 파일 (7개) — 단일 이슈 수정

**근본 원인**: Gemini API가 JSON 스키마의 `additionalProperties`를 지원하지 않아 Blueprint 생성 시 `schema_incompatible` 에러 발생. 이전에는 `UNKNOWN` 에러로 분류되어 10회 전부 리트라이 소진.

**4계층 수정**:

| 계층 | 파일 | 변경 내용 | LOC |
|------|------|----------|-----|
| **1. 스키마 수정** | `modules/core/response_schemas.py` | `additionalProperties` → 명시적 `scene_1..scene_5` 키 + 새 필드(title, tension_level, protagonist_state, ending_state) 추가 | +71/-71 |
| **2. 에러 분류** | `modules/domain/agents/base_agent.py` | `SCHEMA_INCOMPATIBLE` 에러 타입 추가 + 분류 로직 + 한국어 복구 힌트 | +4 |
| **3. 빠른 실패** | `modules/domain/agents/three_phase_blueprint_generator.py` | `SCHEMA_INCOMPATIBLE` 감지 시 리트라이 즉시 중단 + emergency fallback 우회 | +21/-1 |
| **4. 상태 리셋** | `modules/domain/agents/blueprint_ensemble.py` | `last_error_type = None` 리셋 (stale state 방지) | +1 |

**테스트 커버리지**:

| 파일 | 새 테스트 | 내용 |
|------|----------|------|
| `tests/test_base_agent.py` | +1 | `SCHEMA_INCOMPATIBLE` 에러 분류 검증 |
| `tests/test_blueprint_patch_mode.py` | +2 | 리트라이 즉시 중단 + emergency fallback 차단 검증 |
| `tests/test_legacy_reentry_reaudit.py` | 수정 | 스키마 구조 검증을 새 구조에 맞게 갱신 |

**테스트 결과**: 94 passed, 0 failed (1.85s)

### 2.2 문서 변경

| 파일 | 변경 |
|------|------|
| `docs/2026-03-18/geuldobi-v2-stage23-director-advisory-fidelity-escalation-execution-ssot.md` | Resume Commit 갱신 + §15 Post-Closure Delta Re-Audit 추가 (스키마 호환성 문제는 별도 SSOT로 분리됨을 명시) |
| `docs/2026-03-18/geuldobi-v2-llm-model-selection-report.md` | OPUS/ 하위로 이동 (원본 삭제) |
| `docs/2026-03-18/OPUS/geuldobi-v2-llm-model-selection-report.md` | 5Pass 보강판 (398→829줄) |

### 2.3 삭제 파일

| 파일 | 사유 |
|------|------|
| `docs/2026-03-11/프로젝트 승인 요청서.pdf` | staged delete |
| `docs/2026-03-11/프로젝트승인요청서-글도비.md` | unstaged delete |
| `docs/2026-03-11/프로젝트승인요청서-글도비.pdf` | unstaged delete |
| `docs/2026-03-18/geuldobi-v2-llm-model-selection-report.md` | OPUS/로 이동 |

### 2.4 미추적 파일

| 파일/디렉토리 | 내용 |
|-------------|------|
| `docs/2026-03-11/프로젝트승인요청서_2차.pdf` | 2차 승인 요청서 |
| `docs/2026-03-18/OPUS/` | LLM 모델 선정 보고서 5Pass 보강판 |
| `docs/2026-03-18/[업무기안]구글 Ads 디스플레이 광고 진행의 건_*.html` | 업무 기안 |
| `docs/2026-03-18/[업무기안]글도비 운영 전환 1단계 예산 승인의 건_*.md` | 예산 승인 기안 |
| `docs/2026-03-18/stage3-blueprint-failure-deepdive-investigation.md` | Stage 3 장애 심층 조사 |
| `docs/2026-03-18/stage3-blueprint-schema-compatibility-execution-ssot.md` | 스키마 호환성 실행 SSOT |
| `docs/2026-03-18/전자결재 - 키다리스튜디오.pdf` | 전자결재 |
| `projects/0_260318/` | 새 프로젝트 (DB 14MB WAL, config, drafts, logs, plans, memory, stage0_output) |

---

## 3. Pass 1 — 전체 인벤토리

### 3.1 런타임 아키텍처

```
main_a.py (4,833 LOC)
├── Stage 0: 작품 기획 (preset_registry, story_expander, reverse_expander)
├── Stage 1: 기초 설정 (Bible/팩트시트/NPC 생성)
├── Stage 2: Arc 설계 (four_phase_arc_generator, state_locked_arc_generator)
│   ├── Arc Critic → Consensus Validator → Unified Arc Validator
│   └── Director Advisory Chain (8-9 병렬)
├── Stage 3: Blueprint 설계
│   ├── three_phase_blueprint_generator.py (오케스트레이터)
│   ├── blueprint_ensemble.py (3전략 병렬: action/emotion/dialogue)
│   ├── blueprint_constraint_compiler.py
│   └── Unified Blueprint Validator + Director 검증
└── Stage 4: 원고 생산
    ├── chief_writer.py (창작)
    ├── director.py (품질 검증)
    ├── continuity_inspector.py (연속성)
    ├── weaver.py + writer.py (최종 원고)
    └── Advisory Chain (critic, manager, analyst, block_enricher 등)
```

### 3.2 에이전트 매핑 (22개 활성)

**Pro 급 (7+1개)**:
- `chief_writer` — 원고 창작 핵심
- `director` — 최종 품질 결정 (내각제 주권)
- `analyst` — 서사 분석
- `continuity_inspector` — 연속성 검증
- `four_phase_arc_generator` — 4단계 Arc 설계
- `three_phase_blueprint_generator` — 3단계 Blueprint 오케스트레이션
- `blueprint_ensemble` — 3전략 병렬 Blueprint 생성
- `state_locked_arc_generator` — 상태 고정 Arc 생성

**Flash 급 (10+개)**:
- `manager`, `block_enricher`, `preflight_checker`, `state_extractor`
- `arc_corrector`, `arc_critic`, `consensus_validator`
- `unified_arc_validator`, `unified_blueprint_validator`
- `critic`, `weaver`, `writer`

### 3.3 설정 체계

| 설정 파일 | 역할 |
|----------|------|
| `config/models.yaml` | LLM 모델 라우팅 (pro/flash, fallback chain) |
| `config/system.yaml` | 글로벌 시스템 설정 (timeout, thinking budget, caching) |
| `config/settings.json` | 런타임 설정 |
| `config/genres/*.yaml` (10개) | 장르별 스타일/제약 |
| `config/prompts/*.yaml` (9개) | 에이전트별 프롬프트 템플릿 |
| `config/settings/validation.yaml` | 검증 규칙 |

### 3.4 데이터 레이어

| 항목 | 경로 | 상태 |
|------|------|------|
| 활성 프로젝트 DB | `projects/0_260318/project_data.db` | 14MB WAL, 오늘 생성 |
| 이전 프로젝트 DB | `projects/0_260316/project_data.db` | 존재 |
| 아카이브 | `projects/기록용/` | ~29 DB |
| 테스트 자료 | `test_material/material_bank.db` | 참조용 |
| 벡터 DB | `tests/stage4_v2_test/project/chroma_db/` | ChromaDB |

### 3.5 로깅 체계

| 로그 | 경로 | 용도 |
|------|------|------|
| 에피소드 생산 | `{project}/logs/episode_production.jsonl` | 생산 이력 |
| 품질 지표 | `{project}/logs/quality_metrics.jsonl` | 점수/통계 |
| 런타임 감사 | `{project}/logs/runtime_audit.jsonl` | 시스템 감사 |
| 소프트 실패 | `{project}/logs/soft_failures.jsonl` | 경고/복구 |
| 세션 결정 | `{project}/logs/session/decisions.jsonl` | LLM 판단 |
| LLM I/O | `{project}/logs/session/llm_io.jsonl` | 입출력 기록 |
| 상태 변경 | `{project}/logs/session/state_changes.jsonl` | 상태 추적 |
| 컨트롤 플레인 | `logs/control-plane-provenance.jsonl` | 시스템 레벨 |
| 리스크 승인 | `logs/risk-approval-log.jsonl` | 승인 이력 |

---

## 4. Pass 2 — 시맨틱 분류

### 4.1 현재 Dirty State의 영향 범위

```
[SCHEMA FIX] response_schemas.py ← Blueprint JSON 스키마 정의
      │
      ▼
[ERROR CLASSIFICATION] base_agent.py ← 모든 에이전트의 베이스 클래스
      │
      ▼
[FAST FAIL] three_phase_blueprint_generator.py ← Stage 3 오케스트레이터
      │
      ▼
[STATE RESET] blueprint_ensemble.py ← Stage 3 병렬 생성기
```

**영향 범위**: Stage 3 Blueprint 생성 파이프라인 전체. Stage 2 (Arc)와 Stage 4 (Manuscript)는 직접 영향 없음.

**간접 영향**: `base_agent.py`의 `AgentErrorType` 변경은 모든 22개 에이전트에 새 에러 타입을 노출하지만, 기존 에러 분류 로직에 영향 없음 (새 `elif` 분기 추가만).

### 4.2 사이드이펙트 분류

| 카테고리 | 해당 여부 | 세부 |
|----------|----------|------|
| 파일 쓰기/아티팩트 생성 | **해당** | Blueprint JSON 스키마 변경 → 생성되는 Blueprint 구조 변경 (scene_1..5 명시적 키, 새 필드) |
| DB 쓰기 | **비해당** | 스키마 변경은 LLM 응답 포맷만 영향, DB 스키마 불변 |
| JSONL/로그 쓰기 | **해당** | `pipeline_result`에 `error_type`/`failure_reason` 새 키 추가 → `episode_production.jsonl` 등에 기록 |
| 콘솔/UI 출력 | **비해당** | |
| Rollback/Recovery | **해당** | `SCHEMA_INCOMPATIBLE` 시 리트라이 즉시 중단 → emergency fallback 우회 (이전: 10회 리트라이 후 fallback) |
| 캐시/글로벌 상태 | **해당** | `self.last_error_type` 리셋 로직 추가 → stale state 방지 |
| Config/Env mutation | **비해당** | |
| Bootstrap fallback | **비해당** | |

### 4.3 위험 핫스팟

| 파일 | LOC | 위험도 | 근거 |
|------|-----|--------|------|
| `base_agent.py` | ~2,000+ | **HIGH** | 22개 에이전트의 공통 베이스. 에러 분류 변경은 전체 시스템 영향 |
| `response_schemas.py` | ~500+ | **HIGH** | Gemini API 호환성 직결. 스키마 오류 시 전체 Stage 3 실패 |
| `three_phase_blueprint_generator.py` | ~800+ | **MEDIUM** | Stage 3 오케스트레이터. 리트라이/fallback 로직 변경 |
| `blueprint_ensemble.py` | ~400+ | **LOW** | 1줄 리셋만 추가 |

---

## 5. Pass 3 — 건전성 평가 + 잔여 리스크

### 5.1 코드 품질 검증

| 항목 | 결과 |
|------|------|
| AST 파싱 (4개 수정 파일) | **ALL OK** |
| 테스트 실행 (3개 수정 테스트) | **94 passed, 0 failed** (1.85s) |
| 미사용 import | **없음** |
| 죽은 코드 | **없음** |
| UTF-8/모지바케 | **없음** |
| TODO/FIXME 잔여 | **없음** |
| 플레이스홀더 문자 | **없음** |

### 5.2 설계 관찰

| 항목 | 관찰 | 영향도 |
|------|------|--------|
| **Scene 하드코딩** | `scene_1..scene_5` (range(1,6)) — 향후 6장면 이상 필요 시 스키마 수정 필요 | LOW (의도적 설계 제약) |
| **에러 분류 순서** | `MALFORMED_RESPONSE`가 `SCHEMA_INCOMPATIBLE`보다 먼저 매칭 — "parse" AND "not supported" AND "schema" 에러 시 MALFORMED로 분류됨 | LOW (additionalProperties 키워드로 구분 충분) |
| **LLM 모델 선정** | 현행 Gemini 2.5 Pro/Flash → Opus 4.6 전환 논의 중 (별도 보고서) | INFO |
| **프로젝트 0_260318** | 오늘 생성, 14MB WAL — Stage 0 완료, 활성 생산 중 | INFO |

### 5.3 코드베이스 건전성 요약

| 영역 | 상태 | 비고 |
|------|------|------|
| **Stage 0** (기획) | HEALTHY | `stage0/` 5개 파일, 13개 장르 가드 |
| **Stage 2** (Arc) | HEALTHY | `four_phase_arc_generator`, `state_locked_arc_generator` + validator chain |
| **Stage 3** (Blueprint) | **PATCHING** | 스키마 호환성 수정 진행 중 (dirty state) |
| **Stage 4** (원고) | HEALTHY | `chief_writer` + `director` + `continuity_inspector` + advisory chain |
| **Base Infrastructure** | HEALTHY | `base_agent.py` 에러 분류 확장 (하위 호환) |
| **DB Layer** | HEALTHY | SQLite + JSONL 듀얼 기록 |
| **테스트** | HEALTHY | 323개 파일, 수정 영역 94 passed |
| **Config** | HEALTHY | YAML/JSON 체계 정상 |
| **로깅** | HEALTHY | 7-layer JSONL 체계 |
| **Ops Governance** | HEALTHY | Init harness → survey harness → 3pass 체계 가동 |

### 5.4 잔여 리스크

| # | 리스크 | 심각도 | 상태 |
|---|--------|--------|------|
| 1 | **수정 파일 미커밋** | MEDIUM | 7개 파일 + docs 변경 미커밋. 커밋 권장. |
| 2 | **전체 테스트 미실행** | LOW | 수정 영역 94 passed이나 전체 323 파일 미실행. Stage 3 관련 e2e/integration 추가 검증 권장. |
| 3 | **프로젝트 0_260318 WAL 크기** | LOW | 14MB WAL — 활성 생산 중이면 정상이나, 장기간 체크포인트 미수행 시 WAL 누적 가능 |
| 4 | **삭제 파일 정리** | LOW | `docs/2026-03-11/` 3개 파일 삭제 상태 — 의도적이면 커밋으로 확정 필요 |
| 5 | **LLM 모델 전환 미실행** | INFO | LLM 모델 선정 보고서 완료 → Pilot-First 조건부 전환 권고 상태 |
| 6 | **CRLF 혼재 잠재 이슈** | LOW | `.gitattributes` 부재 + `.editorconfig`에 `end_of_line` 미지정 → Windows에서 LF/CRLF 혼재 가능. `git diff` 시 CRLF 경고 8건 관찰. |

---

## 6. 확신도

| 항목 | 확신도 |
|------|--------|
| Dirty state 분석 완전성 | **98%** (git diff + AST + test 검증 완료) |
| 코드베이스 구조 파악 | **95%** (에이전트 탐색 + 디렉토리 순회) |
| 사이드이펙트 커버리지 | **95%** (8개 카테고리 전수 점검) |
| 런타임 건전성 | **90%** (전체 테스트 미실행, 수정 영역만 검증) |
| **종합 확신도** | **95%** |

---

## 7. 권고사항

1. **즉시**: 7개 수정 파일 커밋 (스키마 호환성 수정 + 테스트 + SSOT 갱신)
2. **권장**: Stage 3 관련 e2e 테스트 실행 (`tests/e2e/stage3_smoke*`, `tests/stage3_isolated_test/`)
3. **선택**: 전체 테스트 스위트 순차 shard 실행 (메모리 보수 모드)
4. **참조**: LLM 모델 전환은 `docs/2026-03-18/OPUS/geuldobi-v2-llm-model-selection-report.md` 5Pass 보강판 기준 Pilot-First 진행
5. **저우선**: `.gitattributes` 추가 (`* text=auto eol=lf`) 고려 — CRLF 혼재 방지

---

## 8. 3Pass 감리 이력

| Pass | 수행 내용 | 결과 |
|------|----------|------|
| Pass 1 | 수치 재검증 (파일 수, LOC, DB 크기, 테스트 결과) | 모든 수치 일치 확인 |
| Pass 2 | 누락/오류 점검 | CRLF 혼재 잠재 이슈 발견 → §5.4 #6으로 추가 |
| Pass 3 | 구조 완전성 + 확신도 최종 점검 | 8개 사이드이펙트 카테고리 전수, 확신도 95% 확인 |
