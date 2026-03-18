# S1: 아키텍처 개관 SSOT

> 최종 갱신: 2026-03-18
> 소스: geuldobi-codebase-full-survey-2026-03-18.md
> 감리: static-improvement-discovery 3-pass + evidence-manifest 교차검증

---

## 1. 개관

글도비 v2는 AI 기반 장편 웹소설 자동 생성 시스템으로, Python 백엔드(FastAPI + SQLite + Gemini API) + Electron 프론트엔드로 구성된다. 5단계 파이프라인(Stage 0-4)에서 47개 LLM 에이전트와 6단계 검증 체인이 협업하여 250+화 연재 원고를 생산한다.

---

## 2. 프로젝트 규모

| 카테고리 | 파일 수 | LOC (approx.) | 비고 |
|----------|---------|---------------|------|
| modules/ (source) | ~244 | ~145,000 | core + domain + api + validation + models + protocols |
| tests/ | ~323 | ~74,654 | 4,129 test functions (evidence-manifest 기준) |
| scripts/ | 38 | ~18,000 | 빌드/배포/유틸리티 |
| main_a.py | 1 | ~4,891 | FastAPI 엔트리포인트 |
| Frontend | — | 8,266 | index.html 단일 파일 (CSS+HTML+JS) |

**총계**: ~573+ files, ~246,000+ LOC (테스트 포함)

---

## 2. 디렉토리 구조

```
글도비/
├── main_a.py                    # ~4,891 LOC — FastAPI app, 파이프라인 오케스트레이션
├── modules/
│   ├── core/                    # 161 files, ~91,000 LOC — 핵심 엔진
│   │   ├── orchestrator.py      #   파이프라인 상태 머신
│   │   ├── prompt_engine.py     #   프롬프트 조립
│   │   ├── quality_*.py         #   품질 검사 체계
│   │   ├── state_tracker.py     #   상태 추적 (state_changes 필드)
│   │   ├── response_schemas.py  #   LLM 응답 스키마
│   │   └── ...
│   ├── domain/                  # 48 files, ~40,000 LOC — 도메인 에이전트
│   │   ├── agents/              #   에이전트 구현체
│   │   ├── presets/             #   장르 프리셋 로직
│   │   └── ...
│   ├── api/                     # 8 files, ~3,750 LOC — REST/WS 엔드포인트
│   ├── validation/              # 17 files, ~8,700 LOC — 입출력 검증
│   ├── models/                  # 5 files, ~490 LOC — 데이터 모델
│   └── protocols/               # 5 files, ~690 LOC — 타입 프로토콜
├── tests/                       # ~316 files, ~74,654 LOC
├── scripts/                     # 38 files, ~18,000 LOC
├── tools/ + tools2/             # 32 files, ~12,800 LOC — 개발 도구
├── frontend/                    # Electron 앱
│   ├── main.js                  #   1,010 lines — Main process
│   ├── preload.js               #   97 lines — Context bridge
│   └── index.html               #   8,266 lines — Renderer (monolith)
├── config/
│   ├── models.yaml              #   LLM 모델 매핑
│   ├── system.yaml              #   시스템 설정
│   ├── settings.json            #   런타임 설정
│   ├── genres/                  #   10 YAML — 장르 프리셋
│   └── prompts/                 #   9+ YAML/JSON — 프롬프트 템플릿
└── docs/                        # 문서, 감리 기록
```

데이터: 프로젝트별 SQLite DB (`project_data.db`), JSONL 로그, ChromaDB 벡터 인덱스. 활성 프로젝트: `0_260318` (14MB WAL).

---

## 3. 기술 스택

### 3.1 Backend
- **Python 3.11+** — 타입 힌트 전면 사용
- **FastAPI** — REST + WebSocket 이중 전송
- **SQLite** — 에피소드/프로젝트 영속 저장
- **google-genai SDK** — Gemini API 연동 (직접 호출)

### 3.2 Frontend
- **Electron 40.8.0** — 데스크톱 셸
- **Vanilla JS** — 프레임워크 없는 단일 HTML 모놀리스
- **Lucide Icons** — 아이콘 번들
- **electron-builder + NSIS** — Windows 패키징/인스톨러

### 3.3 LLM
- **Gemini 2.5 Pro** — Pro-tier 에이전트 (품질 중심)
- **Gemini 2.5 Flash** — Flash-tier 에이전트 (속도/비용 중심)
- 상세 모델 매핑 및 선정 근거 → **S4 (LLM 통합 SSOT)** 참조

### 3.4 인프라
- 로컬 실행 (서버리스 아님)
- FastAPI dev/prod 모드, Electron에서 자동 기동
- Backend 비정상 종료 시 auto-restart (최대 2회)

---

## 4. 파이프라인 개관

```
Stage 0 (프로젝트 초기화: Bible/Treatment/Style)
  → Stage 1 (Volume Strategy: 권 단위 전략)
    → Stage 2 (Arc Tactical Design: 3전략 앙상블 + Director 판정)
      → Stage 3 (Blueprint 생성: 에피소드 씬 분해)
        → Stage 4 (원고 생성: ChiefWriter + 6단 검증 + Director 최종 판정)
```

| 스테이지 | 핵심 역할 | 주요 에이전트 | 상세 SSOT |
|----------|-----------|--------------|-----------|
| Stage 0 | 프로젝트 초기화 (Bible/Treatment/Style/Preset) | StoryExpander, ReverseExpander, StyleExtractor, PresetRegistry | S5 |
| Stage 1 | Volume Strategy (권 단위 전략 설계) | Analyst | S5 |
| Stage 2 | Arc Tactical Design (전술적 Arc 설계) | FourPhaseArcGenerator, ArcEnsemble, ArcCritic, ArcCorrector | S5 |
| Stage 3 | Blueprint 생성 (에피소드 씬 분해) | ThreePhaseBlueprintGenerator, BlueprintEnsemble | S6 |
| Stage 4 | 원고 생성 + 6단 검증 | ChiefWriter, DirectorAuditor, ValidationOrchestrator | S6 |

- 각 스테이지 내부 상세 → **S5 (Stage 0-2 내부)**, **S6 (Stage 3-4 내부)** 참조

---

## 5. 설정 체계

### 5.1 모델 설정 (config/models.yaml)
- 에이전트별 LLM 모델 매핑
- tier (pro/flash), temperature, max_tokens 등

### 5.2 시스템 설정 (config/system.yaml)
- 파이프라인 파라미터, 재시도 정책, 타임아웃

### 5.3 런타임 설정 (config/settings.json)
- 사용자 조정 가능 설정 (UI에서 변경)

### 5.4 장르 프리셋 (config/genres/)
- 10개 YAML 파일: 장르별 톤, 문체, 구조 가이드
- 동적 조합 지원 (다중 장르 블렌딩)

### 5.5 프롬프트 템플릿 (config/prompts/)
- 9+ YAML/JSON 파일
- 에이전트별 시스템 프롬프트 + 태스크 프롬프트

---

## 6. 로깅 체계 (7-Layer JSONL + 2 보조)

| 레이어 | 파일/경로 | 용도 |
|--------|-----------|------|
| 1 | episode_production | 에피소드 단위 생산 로그 |
| 2 | quality_metrics | 품질 점수/지표 |
| 3 | runtime_audit | 런타임 감사 추적 |
| 4 | soft_failures | 비치명 실패 기록 |
| 5 | session/decisions | 의사결정 기록 |
| 6 | session/llm_io | LLM 입출력 전문 |
| 7 | session/state_changes | 상태 변경 추적 |
| +α | control-plane-provenance | 제어 평면 출처 추적 |
| +β | risk-approval-log | 위험 승인 기록 |

- 모든 로그: JSONL 포맷, 타임스탬프 + 세션 ID 포함
- state_changes 기반 추출 정확도: ~98% (StateTracker 구조화)

---

## 7. 에이전트 인벤토리

### 7.1 Pro-tier (Gemini 2.5 Pro) — 7-8개
- 품질 민감 태스크: 블루프린트 생성, 앙상블 검증, 품질 감사 등
- 높은 토큰 예산, 낮은 temperature

### 7.2 Flash-tier (Gemini 2.5 Flash) — 10+개
- 속도/비용 최적화 태스크: 초고 집필, 패치, 보조 분석 등
- 빠른 응답, 높은 처리량

### 7.3 에이전트 공통 구조
- `BaseAgent` 상속 → 표준 인터페이스
- 응답 스키마 검증 (response_schemas.py)
- 재시도 + 폴백 정책 내장
- 상세 에이전트 목록 및 역할 → **S4** 참조

---

## 8. 코드베이스 상태 (서베이 시점)

| 영역 | 상태 | 비고 |
|------|------|------|
| Stage 0 | HEALTHY | 안정 |
| Stage 1 | HEALTHY | 안정 |
| Stage 2 | HEALTHY | 안정 |
| Stage 3 | PATCHING | 서베이 시점 패칭 진행 중 |
| Stage 4 | HEALTHY | 안정 |
| Frontend | HEALTHY | 보안 이슈 일부 잔존 (→ S3) |
| BE-FE 연결 | HEALTHY | bridgeFetch 프로토콜 안정 (→ S2) |
| LLM 통합 | HEALTHY | 모델 매핑 안정 (→ S4) |

잔여 이슈: `.gitattributes` 부재 + `.editorconfig`에 `end_of_line` 미지정 → Windows LF/CRLF 혼재 가능. `git diff` 시 CRLF 경고 8건.

서베이 시점 Stage 3 패칭: Gemini API `additionalProperties` 미지원 → `schema_incompatible` 에러. 4계층 수정: 스키마(+71/-71 LOC) + 에러 분류(+4 LOC) + 빠른 실패(+21/-1 LOC) + 상태 리셋(+1 LOC). 테스트: 94 passed, 0 failed.

---

## 9. 수치 요약표

| 지표 | 수치 |
|------|------|
| 소스 파일 (modules/) | ~244개, ~145,000 LOC |
| 테스트 파일 (tests/) | ~323개, ~74,654 LOC, 4,129 함수 |
| 스크립트 (scripts/) | 38개, ~18,000 LOC |
| 메인 엔트리 (main_a.py) | ~4,891 LOC |
| 프론트엔드 (index.html) | 8,266행 |
| 장르 프리셋 | 10개 YAML |
| LLM 에이전트 | 47개 (Pro 7-8, Flash 10+) |
| 파이프라인 스테이지 | 5 (Stage 0-4) |
| 로깅 계층 | 7+2 JSONL/JSON |

---

## 10. 발견 사항

### 10.1 잔여 이슈
- `.gitattributes` 부재 → CRLF 경고 8건
- Stage 3 서베이 시점 패칭 (Gemini `additionalProperties`, 4계층 수정)
- 테스트 파일 수 불일치 (evidence-manifest vs 실측: 290 vs 323 — 카운팅 기준 차이)

### 10.2 상세 SSOT 참조 맵
| 영역 | SSOT |
|------|------|
| BE-FE 연결 | → S2 |
| 프론트엔드 | → S3 |
| LLM 통합 | → S4 |
| Stage 0-2 내부 | → S5 |
| Stage 3-4 + 교차 계층 | → S6 |
| ROL + 정적 개선 | → S7 |

---

## [부록 A] 감리 이력

3PASS 감리 + 적대적 3PASS 수행. S1은 구조가 가장 간결하여 PASS 1 사실 확인 중심 검증.

---

## [부록 B] 근거 파일

| SSOT 시트 | 주 근거 문서 | 보조 근거 |
|-----------|-------------|-----------|
| S1 (본 문서) | geuldobi-codebase-full-survey-2026-03-18.md | static-improvement-discovery-evidence-manifest.md |
| S2 | be-fe-connectivity-deepdive-full-survey.md | frontend-improvement-survey.md |
| S3 | frontend-deepdive-3pass-audit.md | adversarial-3pass-audit R1/R2 |
| S4 | llm-integration-deepdive-3pass-audit.md | llm-deepdive-final-6pass-verdict.md, llm-model-selection-report.md |
| S5 | stage0-2-hidden-internals-deepdive-full-survey.md | adversarial-audit R1/R2 |
| S6 | stage34-deep-dive-underexplored-areas-3pass-audit.md | stage3-blueprint-failure-deepdive-investigation.md |

---

*끝 — S1 아키텍처 개관 SSOT*
