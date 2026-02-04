# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wuxia Studio V60** - AI 기반 다중 장르 웹소설 자동 생성 시스템. Google Gemini API를 사용하여 전문화된 에이전트들이 연재 소설을 생산.

**지원 장르:**
- Wuxia (무협) - 무협 소설
- Hunter (헌터) - 현대 던전/게이트물
- Investment (투자) - 금융 회귀물

## 실행 명령어

```bash
# 의존성 설치
pip install google-generativeai google-genai chromadb python-dotenv rich

# 대시보드 UI (선택)
pip install streamlit

# 환경 설정
echo "GOOGLE_API_KEY=your_key_here" > .env

# 메인 애플리케이션 실행
python main_a.py

# 대시보드 실행 (선택)
streamlit run tools2/studio_dashboard.py

# 프로젝트 리셋 (DB/ChromaDB 초기화)
python RESET.py

# 테스트 실행
pytest tests/                          # 전체 테스트
pytest tests/test_db_manager.py -v     # 단일 모듈 테스트
pytest tests/ -k "test_name" -v        # 특정 테스트만
```

## 유틸리티 도구

| 위치 | 파일 | 용도 |
|------|------|------|
| `tools/` | `concat_txt.py` | 에피소드 텍스트 파일 병합 |
| `tools/` | `db_porter.py` | DB 마이그레이션 |
| `tools/` | `normalize_arcs_db.py` | Arc 데이터 정규화 |
| `tools2/` | `studio_dashboard.py` | Streamlit 대시보드 |
| `tools2/` | `arc_dashboard.py` | Arc 분석 대시보드 |
| `tools2/` | `cost_calculation.py` | API 비용 계산 |
| root | `RESET.py` | 프로젝트 선택적 리셋 |
| root | `make_md.py` | 원고 → 마크다운 변환 |

## 생산 파이프라인 (5단계)

```
Phase 0: Bible Recovery    → 설정집 로드, SQLite 동기화
Stage 1: Volume Strategy   → 10권 전략 계획 (기존 존재 시 스킵 가능)
Stage 2: Arc Design        → 50개 Arc 전술 설계 (권당 5개)
Stage 3: Episode Blueprint → 씬별 설계도 생성
Stage 4: Manuscript        → 최종 원고 작성
```

## 핵심 아키텍처

```
SovereignApp (main_a.py)
├── StudioSystem (modules/core/system.py)
│   ├── ProjectContext → DBManager (SQLite)
│   ├── LoreManager    → 설정집/자산 관리
│   ├── MartialManager → 캐릭터 HUD 상태
│   ├── GenreGuard     → 장르별 검증 규칙
│   └── KarmaService   → 인과율 추적
├── LongTermMemory     → ChromaDB 벡터 검색
└── Agent Orchestra (modules/domain/agents/)
    ├── Core Agents:
    │   ├── Analyst      → 전략 계획 (Stage 1-2)
    │   ├── Architect    → 블루프린트 생성 (Stage 3)
    │   ├── Writer       → 원고 작성 (Stage 4)
    │   └── Director     → 품질 검증
    └── Stage 2 Specialized Agents:
        ├── FourPhaseArcGenerator → 4단계 Arc 파이프라인 조율
        ├── ConstraintCompiler    → 제약 체크리스트 생성
        ├── PreflightChecker      → 생성 전 제약 맵 구축
        ├── ArcEnsembleGenerator  → 3개 후보 병렬 생성
        ├── ArcCritic             → 즉시 비평 + 자동 수정
        ├── ArcCorrector          → Arc 부분 수정
        ├── ConsensusValidator    → 3-LLM 합의 검증
        ├── ContinuityInspector   → 연속성 검증 (Arc/Episode/Manuscript)
        └── ArcDraftValidator     → Python 사전 검증 (무료)
```

## 트리플 데이터베이스

| DB | 위치 | 역할 |
|----|------|------|
| **SQLite** | `projects/{name}/project_data.db` | **진실의 원천** - 원고, 블루프린트, HUD |
| ChromaDB | `projects/{name}/chroma_db/` | 벡터 임베딩 (시맨틱 검색) |
| Files | `projects/{name}/drafts/` | 원고 백업 (가독용) |

**중요:** SQLite DB가 항상 권위적. `bible.json`과 DB가 충돌하면 DB가 우선.

## 에이전트 시스템

모든 에이전트는 `BaseAgent` 상속 (`modules/domain/agents/base_agent.py`):

- `ask(prompt, temperature)` - JSON 모드 API 호출, MAX_TOKENS 시 자동 연속
- `_extract_json_robust()` - 자가 치유 JSON 파서 (3단계 폴백)

**JSON 파싱 폴백 체인:**
1. `json.loads(strict=False)`
2. `ast.literal_eval()` (작은따옴표 처리)
3. 정규식 필드 추출
4. 부분 데이터 + `"parsing_error": True` 반환

## 검증 시스템 (7-Tier)

```
TIER -1: Arc Continuity      → Arc간 타임라인 검증 (Stage 2)
TIER  0: Episode Continuity  → 에피소드간 연속성 (Stage 3)
TIER  0.1: Manuscript Check  → 원고-블루프린트 일치 (Stage 4)
TIER  0.5: Python Continuity → 무료 Python 체크
TIER  1: BLOCKING            → 즉시 REJECT (죽은 NPC 부활 등)
TIER  2: SCORING             → 100점 만점, 70점 통과
TIER  3: ADVISORY            → 비차단 제안 (항상 PASS)
```

## 모델 설정

기본 모델 설정은 `config/settings.json`에서 관리:

| 에이전트 | 기본 모델 | 비고 |
|---------|----------|------|
| Architect | gemini-3-pro-preview | Stage 3 블루프린트 생성 |
| Writer | gemini-3-pro-preview | Stage 4 원고 작성 |
| Analyst | gemini-3-pro-preview | Stage 1-2 전략/Arc |
| Director | gemini-2.5-pro | 품질 검증 |

**폴백 체인 (`base_agent.py`):** 할당량 초과 시 자동 폴백
- `gemini-3-pro-preview` → `gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.0-flash`

## 필수 안전 규칙

1. **ChromaDB 파일 삭제 금지** - `chroma.sqlite3`, `*.wal` 절대 삭제 금지. `LOCK`, `*-shm`만 삭제 가능
2. **DB 쓰기 후 항상 커밋** - `SovereignApp._safe_commit()` (동기) 또는 `_safe_commit_async()` (비동기) 사용. 이 메서드는 `main_a.py`의 `SovereignApp` 클래스에 정의됨
3. **프롬프트 내 사용자 콘텐츠 이스케이프** - `EscapeUtils` (`modules/core/escape_utils.py`) 또는 `BaseAgent._escape_braces()`로 `{}` 문자 처리
4. **에피소드 번호 검증** - `DBManager.get_latest_episode_number()` 또는 `ProjectContext` 메서드 사용, 가정 금지
5. **장르 컨텍스트 확인** - 장르별 로직 전 `self.selected_genre` 확인
6. **Windows UTF-8** - `main_a.py` 5-11줄에서 이미 처리됨. 재래핑 금지
7. **모델 폴백 자동 진행** - 할당량 초과 시 `BaseAgent.MODEL_FALLBACK_CHAIN`이 자동으로 다음 모델로 폴백

## 장르 추가 방법

1. `modules/core/genre_guards/{genre}_guard.py` 생성 (BaseGuard 상속)
2. `modules/core/genre_hud_manager.py`에 HUD 클래스 추가
3. `constants.py:GenreTypes`에 등록
4. `modules/core/laws/{genre}.json` 생성
5. `main_a.py:_select_genre()` 메뉴 업데이트

## 에이전트 동작 수정

프롬프트는 `config/prompts/{agent}_rules.json`에서 로드:
- `analyst_libraries.json` - 전략 라이브러리
- `architect_rules.json` - 블루프린트 규칙
- `writer_rules.json` - 작문 매니페스토

**캐시 무효화:** 앱 재시작 또는 `RESET.py` 실행

## 데이터베이스 스키마

```sql
-- anchors: 키-값 저장소
bible, volumes, arcs, sys_caches

-- blueprints: 에피소드별 씬 계획
ep_num (PK), data (JSON)

-- manuscripts: 최종 원고
ep_num (PK), text, hud_snapshot

-- episode_bibles: 에피소드별 설정 변경
ep_num (PK), new_items, lost_items, relationship_changes, ...
```

## 디버깅

**콘솔 UI:** `StudioVisualizer` (Rich 라이브러리)
- `ui.log(message)` - 일반 로그
- `ui.error(message)` - 에러 표시

**ChromaDB 잠금 오류 시:**
1. 모든 Python 프로세스 종료
2. `projects/{name}/chroma_db/`에서 `LOCK`, `.db-shm`만 삭제
3. `chroma.sqlite3`, `.db-wal`은 절대 삭제 금지

**흔한 에러 패턴:**
| 에러 | 원인 | 해결 |
|------|------|------|
| KeyError in f-string | `{}` 문자 미이스케이프 | `_escape_braces()` 사용 |
| JSON 파싱 실패 | 잘린 응답 | MAX_TOKENS 연속 확인 |
| HUD 상태 불일치 | 스냅샷 누락 | `MartialManager.snapshot()` 확인 |

## 주요 파일 맵

| 파일 | 역할 |
|------|------|
| `main_a.py` | 진입점, SovereignApp 오케스트레이터 (~9000줄) |
| `modules/core/project_manager.py` | ProjectContext - 모든 데이터 I/O |
| `modules/core/db_manager.py` | DBManager - SQLite 연산, 스키마 정의 |
| `modules/core/constants.py` | 전역 상수 (GenreTypes, RetryLimits, AIModels, BatchSizes 등) |
| `modules/core/escape_utils.py` | EscapeUtils - 중괄호 이스케이프 유틸리티 |
| `modules/domain/agents/base_agent.py` | BaseAgent - API 호출, JSON 자가치유, 모델 폴백 |
| `modules/domain/agents/four_phase_arc_generator.py` | Stage 2 Arc 생성 4단계 파이프라인 |
| `modules/domain/agents/continuity_inspector.py` | 연속성 검증 (Arc/Episode/Manuscript) |
| `config/settings.json` | 모델 설정, 검증 임계값 |
| `tests/conftest.py` | pytest fixtures (mock API, DB, contexts) |

## 용어 정리

| 용어 | 의미 |
|------|------|
| `anchor` | DB 저장 JSON 데이터 |
| `HUD` | 캐릭터/세계 상태 (Head-Up Display) |
| `tactical_doc` | Arc 전술 계획 문서 |
| `blueprint` | 에피소드 씬별 설계도 |
| `joint_docs` | Arc 종료 시 상태 (위치, 소지품, 세계상태) |

## Stage 2 Arc 생성 흐름 (V60+)

```
1. ConstraintCompiler.compile()     → 제약 체크리스트 생성
2. FourPhaseArcGenerator.generate() → 4단계 파이프라인
   ├── Phase 1: PreflightChecker    → 제약 맵 구축
   ├── Phase 2: ArcEnsembleGenerator → 3개 후보 병렬 생성
   ├── Phase 3: ArcCritic           → 즉시 비평 + 자동 수정
   └── Phase 4: ConsensusValidator  → 3-LLM 합의 검증
3. ArcDraftValidator.validate()     → Python 사전 검증 (무료)
4. ContinuityInspector.inspect_arc() → LLM 심층 검증
```

## 비동기/동기 패턴

```python
# 동기 컨텍스트 (SovereignApp 메서드 내)
self._safe_commit()

# 비동기 컨텍스트 (SovereignApp 메서드 내)
await self._safe_commit_async()

# DBManager 직접 사용 시
self.current_project.db.conn.commit()
```

**주의:** SQLite는 동기지만 비동기 컨텍스트에서 호출될 수 있음. `asyncio.to_thread()` 사용.

## 상수 클래스 (`modules/core/constants.py`)

| 클래스 | 용도 |
|--------|------|
| `GenreTypes` | 장르 타입 상수 (WUXIA, HUNTER, INVESTMENT) |
| `RetryLimits` | 재시도 횟수 (DIRECTOR_MAX_ATTEMPTS, WRITER_MAX_ATTEMPTS 등) |
| `AIModels` | 모델 이름 상수 (TIER_1_WRITER, EMERGENCY_FALLBACK 등) |
| `BatchSizes` | 배치 크기 (ARC_BATCH_SIZE, EPISODE_BATCH_SIZE) |
| `WritingLimits` | 집필 제한 (MAX_RETRY_PER_EPISODE, MAX_FAILURE_STREAK) |
