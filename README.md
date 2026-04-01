# 글도비 — AI 웹소설 자동 생성 시스템

> LLM 기반 다단계 파이프라인으로 장편 웹소설을 자동 생성하는 시스템.
> 세계관 설정부터 Arc 설계, 에피소드 블루프린트, 원고 집필, 품질 심사까지 전 공정을 자동화한다.

---

## 시스템 개요

글도비는 **"AI 에이전트 50개 모듈이 협업하여 장편 웹소설을 생산하는 파이프라인"**이다.

사람이 세계관(Bible)과 플롯 로드맵(Treatment)만 제공하면, 시스템이 Arc 단위로 전술 설계 → 회차별 블루프린트 → 원고 집필 → 품질 심사를 반복하며 연재 분량의 소설을 생성한다. 각 단계마다 **3개 후보를 병렬 생성**하고 **Director 에이전트가 최종 판정**하는 앙상블 + 내각제 구조를 채택했다.

### 핵심 수치

| 항목 | 수치 |
|------|------|
| 소스 코드 | 175,275 LOC (273 파일) |
| 테스트 코드 | 121,799 LOC (417 파일) |
| 테스트 통과 | 6,052 passed |
| LLM 에이전트 | 50개 모듈 (47 클래스) |
| 검증기 | 16개 (6-Tier 파이프라인) |
| Advisory Chain | 9개 (7 LLM + 2 Python-only, 병렬 실행) |
| 장르 가드 | 13개 (10 장르 + base/style/work) |
| 지원 장르 | 10개 |
| 외부화 설정 | 50 파일 (YAML/JSON) |

---

## 아키텍처

### 파이프라인 흐름

```
Stage 0                    Stage 2                    Stage 3                   Stage 4
세계관 초기화               Arc 전술 설계               에피소드 블루프린트         원고 집필
───────────────────────────────────────────────────────────────────────────────────────────
Bible/Treatment 입력   →   Analyst 분석              →  Blueprint 3후보 생성   →  원고 3후보 생성
NPC 등록                   Arc 3후보 병렬 생성           Director 비교 선택         Director 비교 선택
문체 DNA 추출              Director 심사·패치            검증 파이프라인             6-Tier 검증
                           ConstraintDB 누적            DB 저장                    PASS_WITH_FIX 패치
                                                                                  Memory 저장
```

### 설계 원칙

1. **Director 주권주의 (내각제)** — Director가 최종 품질 결정권을 갖는다. Chief Writer, Analyst 등은 초안을 제출할 뿐이고, 합격/불합격/수정 지시는 Director가 내린다.

2. **Python은 수집만, 판단은 LLM이** — Python 코드는 데이터 수집·포맷팅·전달만 담당한다. "이 원고에 오류가 있는가?", "수정해야 하는가?" 같은 판단은 LLM 에이전트가 내린다. Python은 REJECT 금지, warnings로 Director에 전달.

3. **앙상블 생성 + 경쟁 선택** — 매 단계마다 서로 다른 전략(conservative/balanced/creative)으로 3개 후보를 병렬 생성하고, Director가 비교 심사하여 최적 후보를 선택한다.

4. **자동 품질 루프** — Director가 PASS_WITH_FIX 판정을 내리면 시스템이 자동으로 패치하고 재심사한다. 사람 개입 없이 품질이 수렴한다.

5. **DI Context 패턴** — Stage 2/3/4 오케스트레이터는 God Object(SovereignApp) 직접 참조 대신 `StageNContext` 경량 DI 컨테이너를 주입받는다. `__slots__` 기반으로 필수·확장·콜백 슬롯을 분리하고, `from_app()` 팩토리로 생성한다.

6. **Facade + Sub-module 분해** — Director(391줄 facade + 6 서브모듈), ChiefWriter(2,246줄 + 5 서브모듈), StateTracker(3 서브모듈) 등 대형 클래스는 facade 패턴으로 분해한다.

### 에이전트 구조

```
                         ┌─────────────────┐
                         │    Director      │  최종 판정 (PASS / REJECT / PASS_WITH_FIX)
                         │  (품질 게이트)   │  3후보 비교 선택 + 점수 부여
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
     ┌────────▼──────┐  ┌────────▼──────┐  ┌────────▼──────┐
     │   Analyst     │  │  Blueprint    │  │ Chief Writer  │
     │ (Arc 설계)    │  │  Ensemble     │  │ (원고 집필)   │
     │ 3전략 병렬    │  │  3전략 병렬   │  │ 3전략 병렬    │
     └───────────────┘  └───────────────┘  └───────────────┘
              │                   │                   │
     ┌────────▼──────────────────▼───────────────────▼──────┐
     │                 Advisory Chain (9, 병렬)                  │
     │  TruthGate · NpcDrift · NumericDrift · Flashback      │
     │  · InfoParadox · RelDrift · Repetition · NumConsist   │
     │  · StyleSignal                                        │
     └──────────────────────────────────────────────────────┘
              │
     ┌────────▼──────────────────────────────────────────────┐
     │              6-Tier Validation Pipeline                │
     │  PreLLM → Continuity → Blocking → Consistency        │
     │  → Scoring(6차원) → Advisory                          │
     └──────────────────────────────────────────────────────┘
```

---

## 각 Stage 상세

### Stage 0: 세계관 초기화

입력 방식 4가지를 제공한다:

| 모드 | 설명 |
|------|------|
| Bible/Treatment 선택 | 준비된 JSON 파일을 로드 |
| 컨셉 → Bible 생성 | 1줄 컨셉에서 AI가 세계관을 확장 |
| 역설계 | 기존 원고에서 Bible + 스타일 가이드를 역추출 |
| 스타일 레퍼런스 분석 | 참조 원고에서 문체 DNA 9항목 추출 |

**출력물**: Bible(세계관·NPC·관계도), Treatment(50개 서사 블록), StyleGuide(문체 프로파일)

### Stage 2: Arc 전술 설계

하나의 Arc는 2~6화 분량의 서사 단위이다.

1. **Block 농축** — Treatment의 서사 블록을 LLM으로 풍부화
2. **Preflight 분석** — arc_drive(동기), 연속성 제약, 상태 스냅샷을 병렬 수집
3. **앙상블 생성** — conservative(T=0.3) / balanced(T=0.5) / creative(T=0.7) 3개 후보 병렬 생성
4. **ArcValidator** — LLM 기반 모순 검사 (CRITICAL/MAJOR 분류)
5. **Director 심사** — 최적 후보 선택 + PASS/REJECT/PASS_WITH_FIX 판정
6. **PASS_WITH_FIX 패치** — inplace(국소 수정) / partial(1후보 재생성) / full(전면 재생성) 3-tier 라우팅, 최대 3회 재심사

**출력물**: Arc 전술서(tactical_doc), 상태 제약(state_constraints), 관계 변화, 타임라인

### Stage 3: 에피소드 블루프린트

Arc 내 각 회차의 장면 설계도를 생성한다.

1. **제약 수집** — Arc 전술서에서 해당 화 섹션 추출 + 이전 화 종료 상태
2. **앙상블 생성** — action_focused / emotion_focused / dialogue_focused 3개 후보 병렬 생성
3. **Director 비교 선택** — 3개 후보 중 최적 선택 + 점수 부여

**출력물**: scene_breakdown(장면별 위치·시간·참여자·행동), integrated_scenario(통합 블루프린트)

### Stage 4: 원고 집필

블루프린트를 바탕으로 실제 원고(목표 5,000자, 상한 15,000자)를 생성한다.

1. **컨텍스트 빌드** — 블루프린트 + 이전 원고 + NPC 상태 + 세계관 정보 조합
2. **앙상블 생성** — Chief Writer가 3개 전략으로 원고 병렬 생성
3. **Advisory Chain** — TruthGate(메모리 오염) · NPC 표류 · 수치 표류 · 회상 오염 · 정보 역설 · 관계 표류 · 장기 반복 · 수치 일관성 · 스타일 시그널 (9개 자문, 병렬 실행)
4. **6-Tier 검증** — PreLLM → Continuity → Blocking → Consistency → Scoring(6차원) → Advisory
5. **Director 최종 판정** — PASS/REJECT/PASS_WITH_FIX
6. **패치 루프** — PASS_WITH_FIX 시 자동 수정 + 재심사 (최대 3회)

**출력물**: 원고 본문, 상태 업데이트(NPC 변경, 아이템, 관계도), 검증 결과

---

## 품질 보증 시스템

### 6-Tier 검증 파이프라인

```
[Tier 0.25] PreLLM Validator        Python, 무비용    10개 검사 (어휘 다양성, 시점 일관성 등)
     ↓
[Tier 0.50] Continuity Validator    Python, 무비용    에피소드 간 상태 연속성 (아이템, 부상, 위치)
     ↓
[Tier 1.00] Blocking Validator      Python, 무비용    Hard Stop (사망 NPC 행동, 미소지 아이템 사용 등)
     ↓
[Tier 1.50] Consistency Validator   Python, 무비용    장르별 규칙 적용 (Genre Guard 연동)
     ↓
[Tier 2.00] Scoring Validator       LLM 호출         6차원 채점 (캐릭터·감정·대사·상업성·다양성·만족도)
     ↓
[Tier 3.00] Advisory Validator      LLM 호출         클리셰 감지, 페이싱 분석 (항상 통과, 조언만)
```

### 9단계 Advisory Chain (Stage 4, 병렬 실행)

`ThreadPoolExecutor(max_workers=9)`로 9개 어드바이저 동시 실행 (순차 대비 ~4-5x 속도 향상).

| 순서 | 모듈 | 검사 대상 | 방식 |
|------|------|-----------|------|
| 1 | TruthGate | 사망 NPC 부활, 제거된 아이템 재등장, 세계 법칙 위배 등 7개 | LLM |
| 2 | NpcDriftAdvisor | 원고 속 NPC 묘사 vs DB 스냅샷 불일치 | LLM |
| 3 | NumericDriftAdvisor | FactLedger 수치 누적 표류 (5화 단위 이력) | LLM |
| 4 | FlashbackVerifier | 회상 장면의 과거 사실 오염 (14개 마커 + 원문 대조) | LLM |
| 5 | InfoParadoxChecker | 1인칭 시점에서 주인공이 모르는 정보 사용 | LLM |
| 6 | RelationshipDriftAdvisor | NPC 관계도 장기 표류 | LLM |
| 7 | LongTermRepetitionAdvisor | 20화+ 장기 반복 패턴 (씬 유형 2-gram) | LLM |
| 8 | NumericConsistencyChecker | 수치 일관성 검사 | Python |
| 9 | StyleSignalAdvisor | AI slop / CED / 문체 목표 표류 감지 | Python |

### PASS_WITH_FIX 자동 수정 시스템

Director가 "거의 합격이지만 소수 수정 필요"로 판단하면 PASS_WITH_FIX를 발행한다.

```
fix_scope = "inplace"  →  LLM 1회 국소 수정 → Director 재심사
fix_scope = "partial"  →  최고 후보 1개만 집중 재생성 → 재심사
fix_scope = "full"     →  3후보 전면 재생성 → 재심사
                          (최대 3회 반복)
```

실제 동작 예시 (투자물 Arc 1):
```
Director 1차: PASS_WITH_FIX (95점) — "4화 통장 잔고 불일치"
  → InPlace 패치 #1 → 재심사: PASS_WITH_FIX (95점) — "잔고 표기 미세 오류"
  → InPlace 패치 #2 → 재심사: PASS (100점) — 확정
```

---

## 장르 시스템

10개 장르를 지원하며, 장르별로 독립된 Guard·HUD·프롬프트 스키마를 갖는다.

| 장르 | 핵심 시스템 | Guard |
|------|------------|-------|
| 무협 (Wuxia) | 내공/경지, 무림 세력 | WuxiaGuard |
| 헌터 (Hunter) | 각성/던전, 길드 | HunterGuard |
| 투자 (Investment) | 자본금/포트폴리오, 시장 | InvestmentGuard |
| 판타지 (Fantasy) | 마법/마나, 종족 | FantasyGuard |
| 작곡가 (Composer) | 작곡/프로듀싱 | ComposerGuard |
| 요리 (Cooking) | 셰프 등급/식당 경영 | CookingGuard |
| 대체역사 (Alt History) | 관직/당파/신분 | AltHistoryGuard |
| 배우물 (Actor) | 연예계/오디션 | ActorGuard |
| 스포츠 (Sports) | 선수 성장/경기 | SportsGuard |
| 의학 (Medical) | 의사 성장/수술 | MedicalGuard |

장르 분기 방식: `genre_schema_builder.py`의 Central Schema Builder가 HUD의 `get_critical_keys()`를 기반으로 장르별 프롬프트 스키마를 자동 생성한다. 무협은 기존 하드코딩 경로를 100% 보존하고, 비무협은 동적 생성 경로를 사용한다.

---

## 장기연재 모순 방지 (4대 시스템)

장편 연재(30화+)에서 발생하는 세계관 모순을 방지하는 4개의 독립 시스템:

| 시스템 | 모듈 | 역할 |
|--------|------|------|
| WorldStateManager | `world_state.py` | 세계 상태 문서 — 9개 필드 자동 갱신 |
| Episode Chain Links | chain_link 캐시 | 에피소드 간 연결고리 — 종료 상태 → 다음 화 시작 상태 |
| Volume/Series Summary | 요약 피라미드 | 계층적 요약 — 에피소드 → 볼륨 → 시리즈 |
| FactLedger | `fact_ledger.py` | 누적 팩트 원장 — 엔티티별 100건 이력, 수치 일관성 |

---

## 데이터 관리

### 단일 DB (SSOT)

모든 프로젝트 데이터는 `project_data.db` (SQLite + WAL) 한 파일에 저장된다.

| 테이블 | 용도 |
|--------|------|
| `episodes` | 원고 + 벡터 임베딩 |
| `episode_bibles` | 회차별 세계관 스냅샷 |
| `npc_history` | NPC 속성 변경 이력 (append-only) |
| `npc_relationship_history` | NPC 관계도 변경 이력 (append-only) |
| `fact_ledger` | 수치 팩트 누적 이력 |
| `manuscripts` | 최종 원고 + HUD 스냅샷 |
| `director_selections` | Director 판정 이력 (전략 승률 분석용) |

### 벡터 검색

sqlite-vec 기반 하이브리드 검색 (Dense + FTS5 + RRF):
- Dense: `gemini-embedding-001` (3072차원) KNN k=20
- Sparse: FTS5 전문 검색 k=10
- Hybrid: Reciprocal Rank Fusion (k=60)

---

## 안정성

### API 장애 대응

```
Primary (gemini-3.1-pro-preview)
  ↓ 429/Quota Exhausted
Fallback 1 (gemini-2.5-pro)
  ↓
Fallback 2 (gemini-2.5-flash)
```

멀티 프로바이더 지원: Gemini, Anthropic, OpenAI, Vertex AI (config/models.yaml).

- 네트워크 오류: 지수 백오프 최대 22회 재시도 (야간 무인 운영 대응)
- Rate Limit: 선형 백오프 3회 → 모델 폴백
- Quota 소진: 세션 캐시 (1시간 TTL), 소진 모델 자동 우회
- API Key 로테이션: 다중 키 지원, 스레드 안전 순환

### DB 안정성

- WAL 모드: 읽기/쓰기 동시성 + 크래시 복구
- 무결성 검사: `PRAGMA integrity_check` → 실패 시 자동 격리 + 재생성
- 트랜잭션 보호: RLock + 중첩 감지 + 롤백 보장
- 종료 시점 보호: 미완료 트랜잭션 강제 롤백

### 크래시 복구

- `faulthandler` 활성화 → `crash_dump.log` (segfault 포함)
- Bible-first 저장: 크래시 시 핵심 데이터 복구 가능
- OneStop 파이프라인: Arc 단위 체크포인트, Stage 4 예외 시 다음 Arc로 계속

### Gemini Context Caching

대형 컨텍스트(50,000자+)를 반복 전송하는 에이전트 5개에 Gemini Context Caching을 적용한다.

| 에이전트 | TTL | 절감 |
|----------|-----|------|
| ChiefWriter | 600s | 캐시 읽기 90% 할인 |
| ArcEnsemble | 600s | 캐시 읽기 90% 할인 |
| BlueprintEnsemble | 600s | 캐시 읽기 90% 할인 |
| DirectorEnsemble | 600s | 캐시 읽기 90% 할인 |
| DirectorContinuity | 1800s | cross-episode 재활용 |

---

## 설치 및 실행

### 요구사항

- Python >= 3.11
- Google Gemini API Key

### 설치

```bash
pip install -r requirements.txt
```

### 환경 설정

```bash
# .env 파일 생성
GOOGLE_API_KEY=your_google_api_key_here
# 선택: 다중 키 로테이션
GOOGLE_API_KEY_2=your_second_key
GOOGLE_API_KEY_3=your_third_key
```

### 실행

```bash
python main_a.py
```

메뉴에서 장르 선택 → 프로젝트 선택/생성 → Stage 0(초기화) → OneStop(자동 파이프라인) 순서로 진행한다.

Routed narrative-family entrypoints were moved to `README.narrative-router.md` to reduce merge-conflict surface in the root README.

### 주요 메뉴

| 명령 | 기능 |
|------|------|
| 0 | Stage 0: Bible/Treatment/스타일 설정 |
| 1 | Stage 1: Volume Strategy (선택) |
| 2 | Stage 2: Arc 전술 설계 |
| 3 | Stage 3: 에피소드 블루프린트 |
| 4 | Stage 4: 원고 집필 |
| 6 | OneStop: Arc 단위 자동 파이프라인 |
| 44 | Stage 4 회차별 롤백 |
| 88 | Stage 2 전체 초기화 |
| 99 | Stage 2 정밀 되감기 |

### 테스트

```bash
pytest tests/ -q
```

---

## 설정

`config/settings/validation.yaml`에서 전체 파이프라인 동작을 제어한다.

| 카테고리 | 주요 파라미터 | 기본값 |
|----------|-------------|--------|
| 원고 분량 | min_length / target / max | 4,000 / 5,000 / 15,000자 |
| 품질 게이트 | quality_gate_score | 90 |
| 장르별 임계값 | wuxia / investment 등 | 68~72 |
| 컨텍스트 예산 | Stage4 / Director | 300K / 300K 자 |
| 재시도 | director_max_attempts | 10 |
| API 타임아웃 | api_timeout_seconds | 300초 |
| 검색 모드 | retrieval_mode | hybrid |
| 세션 로깅 | session_logging.enabled | true |

---

## 프로젝트 구조

```
글도비/
├── main_a.py                          # 진입점 SovereignApp (4,788줄)
├── config/
│   ├── prompts/                       # 외부화된 프롬프트 9개 (YAML)
│   ├── settings/validation.yaml       # 파이프라인 설정 (244줄)
│   ├── models.yaml                    # LLM 모델 매핑
│   └── genres/, terms/, smart_retrieval/
├── modules/
│   ├── core/                          # 오케스트레이터, 어드바이저, DB (108K LOC)
│   │   ├── stage0/                    #   Stage 0 초기화
│   │   ├── stage2_orchestrator.py     #   Stage 2 Arc 설계 (1,731줄)
│   │   ├── stage3_orchestrator.py     #   Stage 3 Blueprint (2,859줄)
│   │   ├── stage4_orchestrator.py     #   Stage 4 원고 (2,556줄 + 서브모듈)
│   │   ├── genre_guards/              #   장르 가드 13종
│   │   ├── truth_gate.py              #   메모리 오염 검증 (7개 검사)
│   │   ├── genre_schema_builder.py    #   장르별 동적 스키마 생성
│   │   ├── db_manager.py              #   SQLite DB 매니저
│   │   └── vec_memory.py              #   벡터 메모리 (sqlite-vec)
│   ├── domain/agents/                 # LLM 에이전트 50개 모듈 (47K LOC)
│   │   ├── base_agent.py              #   베이스 (재시도, 폴백, 컨텍스트 캐싱)
│   │   ├── analyst.py                 #   Analyst (Arc 분석)
│   │   ├── arc_ensemble.py            #   Arc 앙상블 생성기
│   │   ├── blueprint_ensemble.py      #   Blueprint 앙상블 생성기
│   │   ├── chief_writer.py            #   Chief Writer (원고 집필)
│   │   ├── director.py                #   Director facade + 6 서브모듈
│   │   └── director_ensemble.py       #   Director 앙상블 선택기
│   ├── validation/                    # 검증기 16종
│   ├── models/                        # 데이터 모델
│   ├── protocols/                     # 추상 프로토콜
│   └── ui/                            # CLI/Rich 콘솔
├── tests/                             # 테스트 417파일 (122K LOC)
│   ├── chaos/                         #   카오스 테스트
│   ├── e2e/                           #   End-to-End 통합
│   ├── integration/                   #   통합 테스트
│   └── property/                      #   Property-based (hypothesis)
├── geuldobi-desktop/                  # Electron 데스크톱 앱 (Windows)
├── projects/                          # 프로젝트별 DB + 출력물
├── libraries/                         # 장르별 아키타입 라이브러리
└── docs/                              # 설계 문서
```

---

## 제한사항

- **속도**: Arc 1개당 40~60분 소요 (품질 우선 설계). 3개 Arc ≈ 2~3시간.
- **LLM 의존**: Google Gemini API 기본. Anthropic/OpenAI/Vertex AI 프로바이더 설정 가능하나 Gemini 중심 최적화.
- **인터페이스**: CLI + Electron 데스크톱 앱 (`geuldobi-desktop/`). 웹 UI 없음.
- **언어**: 한국어 웹소설 전용 (프롬프트·검증 규칙 모두 한국어 기준).

---

## 라이선스

Private repository. All rights reserved.
