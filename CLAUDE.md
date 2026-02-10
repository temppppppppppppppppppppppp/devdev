# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wuxia Studio V66.3** - AI 기반 다중 장르 웹소설 자동 생성 시스템. Google Gemini API를 사용하여 전문화된 에이전트들이 연재 소설을 생산.

**지원 장르:**
- Wuxia (무협) - 무협 소설
- Hunter (헌터) - 현대 던전/게이트물
- Investment (투자) - 금융 회귀물
- Fantasy (판타지) - 이세계물

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

## 생산 파이프라인 (5단계) - 스테이지별 메인 에이전트

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage   │ 설명                    │ 메인 에이전트              │ 레거시      │
├─────────┼─────────────────────────┼───────────────────────────┼────────────┤
│ Stage 0 │ Bible 생성/역설계        │ StageZeroManager          │ -          │
│ Stage 1 │ Volume Strategy (10권)  │ Analyst                   │ -          │
│ Stage 2 │ Arc Design (50개)       │ FourPhaseArcGenerator     │ Analyst    │
│ Stage 3 │ Episode Blueprint       │ ThreePhaseBlueprintGenerator │ Architect │
│ Stage 4 │ Manuscript 집필         │ ChiefWriter               │ Writer     │
└─────────────────────────────────────────────────────────────────────────────┘

* 레거시 에이전트: 메인 에이전트 실패 시 폴백으로만 사용
* Director: 모든 스테이지에서 품질 검증 담당 (PASS/REJECT 판정권)
```

## 핵심 아키텍처 (V66.3)

```
SovereignApp (main_a.py, 4,090+줄)
├── StudioSystem (modules/core/system.py)
│   ├── ProjectContext → DBManager (SQLite)
│   ├── LoreManager    → 설정집/자산 관리
│   ├── MartialManager → 캐릭터 HUD 상태
│   ├── GenreGuard     → 장르별 검증 규칙 (다형성 run_deep_validation) [V66]
│   ├── PrimitiveGuard → 원시인 금지어 검증 [V60.96]
│   └── KarmaService   → 인과율 추적
├── StateTracker       → NPC 생사/무공/관계/성격/대화스타일 추적 [V66]
│   ├── state_tracker_npc.py   → NPC 전용 (1,820+줄)
│   ├── state_tracker_plots.py → 플롯/아이템/시간선 (650+줄)
│   └── state_tracker_financial.py → 금융 (129줄)
├── Stage2Orchestrator → Arc 생성 오케스트레이션 (1,800+줄) [V64]
├── Stage4Orchestrator → 원고 생성 오케스트레이션 (1,140+줄) [V64]
├── SemanticPlotGuard  → ChromaDB cosine 유사도 플롯 중복 감지 [V66]
├── ForeshadowTracker  → 복선/회수 추적 [V66]
├── PresetRegistry     → 장르별 프리셋 스키마 [V60.95]
├── LongTermMemory     → ChromaDB 벡터 검색
│
└── Agent Orchestra (modules/domain/agents/)
    │
    ├── [Stage 0] modules/core/stage0/
    │   ├── StageZeroManager   → 통합 Stage 0 관리
    │   ├── StoryExpander      → 컨셉 → Bible 생성
    │   ├── ReverseExpander    → 역설계 (원고 → Bible)
    │   └── StyleExtractor     → 톤/문체 추출
    │
    ├── [Stage 2] FourPhaseArcGenerator (메인)
    │   ├── PreflightChecker      → 제약 맵 구축
    │   ├── ArcEnsembleGenerator  → 3개 후보 병렬 생성
    │   ├── UnifiedArcValidator   → Python + LLM 통합 검증
    │   └── (Analyst → 폴백 전용)
    │
    ├── [Stage 3] ThreePhaseBlueprintGenerator (메인)
    │   ├── BlueprintEnsembleGenerator → 3개 후보 병렬 생성
    │   ├── UnifiedBlueprintValidator  → 통합 검증
    │   └── (Architect → 레거시)
    │
    ├── [Stage 4] ChiefWriter (메인, 2,010+줄)
    │   ├── generate_ensemble()    → 3개 후보 병렬 생성 (빈 배열 방어 [V66.3])
    │   ├── ManuscriptValidator    → Python 사전 검증
    │   └── (Writer → 냉동인간, 최후 폴백)
    │
    └── [공통] Director (facade 256줄 + 5 sub-modules) [V64/V66.3]
        ├── director_ensemble.py   → 앙상블 선정 (mandatory_context 수신 [V66.3])
        ├── director_grading.py    → 점수 채점
        ├── director_auditor.py    → 장르/연속성 감사
        ├── director_continuity.py → 연속성 검증
        └── director_caching.py    → 캐싱 관리
```

### 핵심 설계 원칙 (V66.2+)

**"Python 감지 → Director LLM 판단"**: Python 검증기(BlockingValidator, ContinuityValidator 등)는 문제를 **감지**만 하고, 최종 PASS/REJECT **판정**은 Director LLM이 수행. Python이 직접 REJECT하지 않음.

```
mandatory_context (21항목) ──→ ChiefWriter LLM (원고 생성 시 참조)
         │
         └──→ Director LLM (PASS/REJECT 판정 시 참조) [V66.3]
                  ↑
Python 검증 경고 ──┘ (죽은NPC 감지, 성격 모순, 파괴 엔티티 등)
```

## StateTracker & state_changes (V66.3)

Arc 생성 시 `state_changes` 필드로 이벤트를 구조화하여 추출. 16개 필드 E2E 파이프라인 완성:

```json
{
  "arc_no": 5,
  "tactical_doc": "...",
  "state_changes": {
    "npc_deaths": [{"name": "철무련주", "episode": 23, "cause": "주인공에게 패배"}],
    "skill_acquisitions": [{"name": "파천검법", "episode": 24, "source": "비급 습득"}],
    "relationship_changes": [{"npc": "흑도", "from": "적", "to": "중립", "episode": 25}],
    "major_items": [{"name": "용린검", "episode": 24, "action": "획득"}],
    "entity_destructions": [{"name": "조직명", "type": "organization", "cause": "...", "episode": 23}],
    "npc_personality_changes": [{"name": "NPC명", "traits": "성격", "motivation": "동기", "episode": 24}],
    "npc_npc_relationships": [{"npc1": "A", "npc2": "B", "relation": "동맹", "episode": 25}],
    "npc_dialogue_profiles": [{"name": "NPC명", "speech_style": "말투", "catchphrase": "습관 표현", "episode": 24}],
    "npc_injuries": [{"name": "NPC명", "injury": "부상 내용", "episode": 23}],
    "npc_movements": [{"name": "NPC명", "from": "장소A", "to": "장소B", "episode": 24}],
    "time_markers": [{"description": "시간 경과", "episode": 25}],
    "companion_changes": [{"name": "동행자명", "action": "합류/이탈", "episode": 24}],
    "promises_obligations": [{"description": "약속 내용", "episode": 23}],
    "protagonist_emotion": [{"emotion": "감정 상태", "trigger": "원인", "episode": 25}]
  }
}
```

**StateTracker 흐름 (V66.3):**
```
Stage 2 생성 → state_changes 추출 → StateTracker 업데이트
     ↓
mandatory_context 21항목 조립 (Priority 순서)
     ↓
ChiefWriter LLM → 원고 생성 시 참조 (죽은NPC/파괴장소/스킬/관계 등)
     ↓
Python 검증 (BlockingValidator + ContinuityValidator) → 경고 감지
     ↓
Director LLM → mandatory_context + Python 경고 수신 → PASS/REJECT [V66.3]
```

## PrimitiveGuard (V60.96) - 원시인 금지어

`protagonist_config.world_origin == '원시인'`일 때 현대 용어 차단:

| 장르 | 적용 수준 | 차단 대상 |
|------|-----------|-----------|
| 무협 (wuxia) | full | 전체 (~600개 단어) |
| 판타지 (fantasy) | partial | IT/지구브랜드만 (카페/커피 허용) |
| 헌터 (hunter) | none | 제한 없음 |
| 투자물 (investment) | none | 제한 없음 |

**파일 위치:**
- `modules/core/laws/primitive_forbidden.json` - 금지어 DB (~1400개)
- `modules/core/primitive_guard.py` - 검증 유틸리티

## 트리플 데이터베이스

| DB | 위치 | 역할 |
|----|------|------|
| **SQLite** | `projects/{name}/project_data.db` | **진실의 원천** - 원고, 블루프린트, HUD |
| ChromaDB | `projects/{name}/chroma_db/` | 벡터 임베딩 (시맨틱 검색) |
| Files | `projects/{name}/drafts/` | 원고 백업 (가독용) |

**중요:** SQLite DB가 항상 권위적. `bible.json`과 DB가 충돌하면 DB가 우선.

## 에이전트 시스템

모든 에이전트는 `BaseAgent` 상속 (`modules/domain/agents/base_agent.py`):

```python
class BaseAgent:
    API_DELAY = 0.3  # [V60.99] Rate Limit 예방 딜레이

    MODEL_FALLBACK_CHAIN = {
        "gemini-3-pro-preview": "gemini-2.5-pro",
        "gemini-3-flash-preview": "gemini-2.5-flash",
        "gemini-2.0-flash": "gemini-2.5-flash",
        # gemini-2.5-pro는 최종 방어선 (체인 없음)
    }
```

- `ask(prompt, temperature, thinking_level)` - JSON 모드 API 호출
- `_extract_json_robust()` - 자가 치유 JSON 파서 (3단계 폴백)

## 모델 설정

| 에이전트 | 기본 모델 | 비고 |
|---------|----------|------|
| FourPhaseArcGenerator | gemini-3-pro-preview | Stage 2 Arc |
| ThreePhaseBlueprintGenerator | gemini-3-pro-preview | Stage 3 Blueprint |
| ChiefWriter | gemini-3-pro-preview | Stage 4 원고 |
| Director | gemini-3-pro-preview | 품질 검증 |

**폴백 체인:** `gemini-3-pro → gemini-2.5-pro → gemini-2.5-flash`

## 검증 시스템 (8-Tier)

```
TIER -1: Arc Continuity      → Arc간 타임라인 검증 (Stage 2)
TIER  0: Episode Continuity  → 에피소드간 연속성 (Stage 3)
TIER  0.25: PRE_LLM          → Python 사전 검증 (PreLLMValidator)
TIER  0.5: Python Continuity → Python 연속성 체크
TIER  1: BLOCKING            → 필수 통과 (죽은 NPC 부활, 원시인 금지어)
TIER  1.5: CONSISTENCY       → 일관성 검증 (ConsistencyValidator)
TIER  2: SCORING             → 100점 만점, 70점 통과
TIER  3: ADVISORY            → 비차단 제안 (항상 PASS)
```

## 필수 안전 규칙

1. **ChromaDB 파일 삭제 금지** - `chroma.sqlite3`, `*.wal` 절대 삭제 금지
2. **DB 쓰기 후 항상 커밋** - `SovereignApp._safe_commit()` 사용
3. **프롬프트 내 사용자 콘텐츠 이스케이프** - `BaseAgent._escape_braces()`로 `{}` 처리
4. **에피소드 번호 검증** - `DBManager.get_latest_episode_number()` 사용
5. **장르 컨텍스트 확인** - 장르별 로직 전 `self.selected_genre` 확인
6. **원시인 금지어** - `PrimitiveGuard` 통해 장르별 적용

## 주요 파일 맵

| 파일 | 역할 |
|------|------|
| `main_a.py` | 진입점, SovereignApp 오케스트레이터 |
| `modules/core/stage0/` | Stage 0 모듈 (Bible 생성/역설계) |
| `modules/core/primitive_guard.py` | 원시인 금지어 검증 |
| `modules/core/laws/primitive_forbidden.json` | 금지어 DB |
| `modules/domain/agents/base_agent.py` | BaseAgent (API_DELAY 포함) |
| `modules/domain/agents/four_phase_arc_generator.py` | Stage 2 메인 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | Stage 3 메인 |
| `modules/domain/agents/chief_writer.py` | Stage 4 메인 |
| `modules/domain/agents/state_tracker.py` | NPC/무공/관계/성격/대화스타일 추적 (facade + 3 sub-modules) |
| `modules/domain/agents/director.py` | 품질 검증 (facade + 5 sub-modules) [V64] |
| `modules/core/stage2_orchestrator.py` | Stage 2 오케스트레이션 [V64] |
| `modules/core/stage4_orchestrator.py` | Stage 4 오케스트레이션 (mandatory_context 조립) [V64] |
| `modules/domain/agents/analyst.py` | #레거시 (Stage 2 폴백) |
| `modules/domain/agents/architect.py` | #레거시 (Stage 3 미사용) |
| `modules/domain/agents/writer.py` | #레거시 (Stage 4 냉동인간) |

## Stage 2 Arc 생성 흐름 (V61)

```
1. ConstraintCompiler.compile()     → 제약 체크리스트 생성
2. FourPhaseArcGenerator.generate() → 3단계 파이프라인
   ├── Phase 1: Constraint         → Preflight + Compiler + NegativeExamples
   ├── Phase 2: Generate           → ArcEnsemble 3개 병렬 (state_changes 포함)
   └── Phase 3: Validate           → UnifiedArcValidator (Python + LLM)
3. StateTracker.extract_*()        → state_changes 우선 읽기 (Regex 폴백)
4. Director 대면                    → 최종 PASS/REJECT
```

## Stage 3 Blueprint 생성 흐름

```
1. ThreePhaseBlueprintGenerator.generate()
   ├── Phase 1: BlueprintEnsemble  → 3개 후보 병렬 생성
   ├── Phase 2: Python 검증        → 분량/필드/죽은NPC 체크
   └── Phase 3: Director 대면      → 최종 PASS/REJECT
```

## Stage 4 Manuscript 생성 흐름 (V66.3)

```
1. mandatory_context 조립 (21항목, Priority 순서, 25K자 스마트 truncation)
   ├── Priority 1-5:  죽은NPC, 파괴엔티티, 완결플롯, 시간선, 복선
   ├── Priority 6-12: NPC성격, 대화스타일, 관계, 스킬목록, 아이템, 위치
   └── Priority 13-21: Arc요약, 검증경고, 호흡분석, 서사요약
2. ChiefWriter.generate_ensemble() → 3개 후보 병렬 생성 (빈 배열 방어 [V66.3])
   ├── mandatory_context 주입       → 세계 상태 전달
   ├── PrimitiveGuard 주입          → 원시인 금지어 프롬프트
   └── 스타일 가이드 주입           → 톤/문체/대화비율
3. Python 검증 (ManuscriptValidator + BlockingValidator + ContinuityValidator)
4. Director.select_and_judge_ensemble() → mandatory_context + Python 경고 수신 → PASS/REJECT [V66.3]
5. (실패 시) Writer                 → 냉동인간 폴백
```

## 용어 정리

| 용어 | 의미 |
|------|------|
| `anchor` | DB 저장 JSON 데이터 |
| `HUD` | 캐릭터/세계 상태 (Head-Up Display) |
| `tactical_doc` | Arc 전술 계획 문서 |
| `blueprint` | 에피소드 씬별 설계도 |
| `joint_docs` | Arc 종료 시 상태 (위치, 소지품, 세계상태) |
| `state_changes` | Arc 내 이벤트 구조화 (16필드: 사망/습득/관계/파괴/성격/대화 등) |
| `mandatory_context` | Stage 4 LLM에 전달되는 세계 상태 (21항목, Priority 순서) [V66] |
| `validation_context` | Python 검증기에 전달되는 컨텍스트 dict [V66.2] |
| `world_origin` | 주인공 출신 (원시인/현대인) |
| `incarnation_type` | 환생 유형 (회귀자/빙의자/환생자) |

## 데이터베이스 스키마

```sql
-- anchors: 키-값 저장소
bible, volumes, arcs, sys_caches, style_guide

-- blueprints: 에피소드별 씬 계획
ep_num (PK), data (JSON)

-- manuscripts: 최종 원고
ep_num (PK), text, hud_snapshot

-- episode_bibles: 에피소드별 설정 변경
ep_num (PK), new_items, lost_items, relationship_changes, ...
```

## 디버깅

**ChromaDB 잠금 오류 시:**
1. 모든 Python 프로세스 종료
2. `projects/{name}/chroma_db/`에서 `LOCK`, `.db-shm`만 삭제
3. `chroma.sqlite3`, `.db-wal`은 절대 삭제 금지

**흔한 에러 패턴:**
| 에러 | 원인 | 해결 |
|------|------|------|
| KeyError in f-string | `{}` 문자 미이스케이프 | `_escape_braces()` 사용 |
| JSON 파싱 실패 | 잘린 응답 | MAX_TOKENS 연속 확인 |
| 죽은 NPC 부활 | StateTracker 미전달 | state_tracker 파라미터 확인 |
| 원시인 금지어 통과 | PrimitiveGuard 미적용 | 장르 + world_origin 확인 |

## 상수 클래스 (`modules/core/constants.py`)

| 클래스 | 용도 |
|--------|------|
| `GenreTypes` | 장르 타입 상수 (WUXIA, HUNTER, INVESTMENT, FANTASY) |
| `RetryLimits` | 재시도 횟수 |
| `AIModels` | 모델 이름 상수 |
| `BatchSizes` | 배치 크기 |
| `Stage2Limits` | Arc ep_count 범위 (3~7) |
| `WritingLimits` | 집필 제한 |
