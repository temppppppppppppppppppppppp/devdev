# OPUS TF 5-Terminal 심층 조사 마스터 오더 (3차)

> **작성일**: 2026-03-13
> **목적**: 1차(거시 건강성) + 2차(미열거 디테일)에서 **실제로 조사되지 않은** 영역 전량 심층 감사
> **배경**:
> - 1차 T1~T5 보고서 합산: P0=1, P1=13, P2=86, P3=165, 총 265건
> - 실제 감사 범위 완성도: T1 75%, T2 70%, T3 60%, T4 65%, T5 55% (평균 65%)
> - 나머지 35%: Stage 0 메뉴 플로우, 교차 스테이지 통합, Lite Mode, Tools, API 심층, 보안·성능
> - **미해결 P0 1건 + P1 13건** 중 핵심 7건 추적 조사 필요
> **방법**: 각 터미널 자체 3PASS 감리 후 보고

---

## 0. 1~3차 마스터 오더 계보

| 차수 | 초점 | 결과 |
|------|------|------|
| 1차 | 핵심 프로덕션 모듈 239개 (거시 건강성) | 265건 발견, 평균 65% 커버 |
| 2차 | 1차 미열거 파일 (디테일 영역) | 미열거 모듈 23개 + 테스트 229개 + Config 23+ 배정 |
| **3차 (본 문서)** | **실제 미조사 영역 + 미해결 P1 추적 + 완전 미감사 시스템** | 아래 5개 터미널 |

---

## 1. 자체 3PASS 감리 프로토콜 (전 터미널 공통)

> 2차와 동일 프로토콜 적용. 핵심만 재기술.

### PASS 1 — 초벌 스캔 (발견)
- 담당 범위 전 파일·전 메서드 읽기, 후보 목록 + 확신도 `HIGH/MED/LOW`

### PASS 2 — 교차 검증 (검증)
- 코드 증거 재확인 + CLAUDE.md 대조 + 기존 T1~T5 보고서 대조
- **1차 보고서에서 이미 발견된 항목은 중복 보고 금지** — 신규 발견만 보고
- 오탐 판정: FP-1(의도적 설계), FP-2(테스트 검증), FP-3(호출자 추적), FP-4(교차 확인), FP-5(스타일 차이)

### PASS 3 — 최종 확정 (확정)
- 확정 항목만 `[S-TN-SEQ]` 형식 (S = Deep-dive의 S)
- 보고서 말미: `PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정`

---

## 2. 터미널 영역 분할

```
┌───────────────────────────────────────────────────────────────────────┐
│           3차 심층 감사 — 5개 터미널 영역 지도                          │
├──────────────┬──────────────┬──────────────┬──────────────┬───────────┤
│  Terminal 1  │  Terminal 2  │  Terminal 3  │  Terminal 4  │ Terminal 5│
│ ★ Stage 0   │  교차 스테이지 │ Lite Mode   │ API 심층    │ 보안·성능  │
│  세부 메뉴   │  통합 + P1   │ & Tools     │ & Desktop   │ & 대규모  │
│  & UI 플로우  │  미해결 추적  │ (완전 미감사) │  통합       │  시나리오  │
│  ~5.4K lines │  ~교차 추적   │ ~32+26 files│ ~2.5K lines │  ~횡단    │
└──────────────┴──────────────┴──────────────┴──────────────┴───────────┘
```

---

## 3. Terminal 1 — ★ Stage 0 세부 메뉴 & UI 플로우 (전량)

### 미조사 배경

1차 T2는 Stage 0 모듈을 "파일 단위"로 열거만 하고, **메뉴 인터랙션 로직·모드별 분기·사용자 입력 검증**은 디테일 미검사.
실제 T2 보고서에서도 Stage 0 내부 메뉴 플로우는 조사 범위 밖으로 명시.

### 담당 범위

**StageZeroManager 메뉴 시스템** (`modules/core/stage0/__init__.py`, 774줄)
| 메서드 | 줄 범위 (추정) | 역할 |
|--------|---------------|------|
| `show_menu()` | L212-238 | 메인 메뉴 디스패치 (7+ 옵션) |
| `show_genre_menu()` | L240-260 | 10개 장르 선택 UI |
| `show_protagonist_config_menu()` | L262-331 | POV/전생타입/세계관출신 설정 |
| ├ 세계관 출신 | L271-281 | 하위 메뉴 |
| ├ 캐릭터 타입 | L284-294 | 하위 메뉴 |
| ├ 시점(POV) | L297-307 | 하위 메뉴 |
| └ 외부 시점 삽입 정책 | L309-329 | 하위 메뉴 (mojibake 이슈 존재) |
| `manage_work_guard()` | L136-206 | 워크가드 관리 메뉴 |
| ├ library import | L161-177 | YAML 가져오기 |
| ├ default init | L179-181 | 기본값 초기화 |
| ├ preview | L184-196 | 미리보기 |
| └ delete | L198-204 | 삭제 |
| `run_new_project_flow()` | L337-367 | Stage 0 전체 플로우 오케스트레이션 |
| `generate_from_concept()` | L369-408+ | 컨셉→바이블 파이프라인 |

**Stage 0 서브모듈 내부 로직** (1차에서 파일만 열거, 내부 미검사)
| 파일 | 줄수 | 검사 초점 |
|------|------|----------|
| `stage0/reverse_expander.py` | 1,178 | 역추출 상태머신, 다중 패스 분석, 입력 검증 |
| `stage0/style_extractor.py` | 1,143 | 스타일 DNA 추출, StyleGuide 조립, 참조원고 파싱 |
| `stage0/story_expander.py` | 600 | 컨셉 분석, 장르 자동감지, 바이블 생성, 2-모델 폴백 |
| `stage0/preset_registry.py` | 739 | 필드 프리셋, 장르별 기본값, 동적 플레이스홀더 |
| `stage0/spinner.py` | 666 | 스피너 상태관리, 진행 표시 |

**Stage 01 헬퍼 6-모드 디스패처** (`modules/core/stage01_helpers.py`, 740줄)
| 모드 | 메뉴 옵션 | 역할 |
|------|----------|------|
| Mode 1 | 옵션 2 | Concept → Bible 생성 |
| Mode 2 | 옵션 3 | Reverse Expander (역추출) |
| Mode 3 | 옵션 4 | Bible JSON Import |
| Mode 4 | 옵션 5 | Block Expansion (블록 확장) |
| Mode 5 | 옵션 6 | Style Reference Analysis (문체 분석) |
| Mode 6 | 옵션 7 | Work Guard Setup |

**SovereignApp Stage 0 관련 메뉴** (`main_a.py` 내)
| 메서드 | 역할 |
|--------|------|
| `_select_genre()` | 장르 선택 메뉴 (멀티키 지원) |
| `_select_project()` | 프로젝트 선택 (`/projects` 디렉토리) |
| `_ui_select_bible()` | 바이블 파일 선택 |
| `_ui_select_treatment()` | 트리트먼트 파일 선택 |
| `_run_main_process()` | 메인 메뉴 디스패치 (11+ 옵션) |
| `_show_resume_status()` | 크래시 후 진행상태 표시 |

**관련 테스트**
- `tests/test_stage0_fixes.py`, `tests/test_stage0_pov.py`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_reverse_expander_g2.py`
- `tests/test_stage01_helpers.py`
- `tests/test_process_runner_stage0_inputs.py`
- `tests/test_frontend_stage0_connectivity.py`

### 핵심 검사 포인트

1. **메뉴 입력 검증**: 모든 `input()` / UI 선택에서 범위 외 입력, 빈 입력, 한글/특수문자 입력 처리
2. **6-모드 분기 정합성**: `stage_0_extended(mode)` 6개 분기가 각각 올바른 서브모듈을 호출하는가
3. **장르 선택 → 전파 체인**: `show_genre_menu()` 선택 결과가 Stage 2까지 정확히 전달되는가
4. **POV 선택 → 전파 체인**: POV/전생타입/세계관출신 설정이 Stage 4 ChiefWriter까지 도달하는가
5. **Work Guard 관리**: import/init/preview/delete 4개 액션의 파일 I/O 안전성, 경로 검증
6. **Reverse Expander 상태머신**: 다중 패스 분석의 상태 전이 정확성, 실패 시 복구
7. **Style Extractor → StyleGuard 체인**: 추출된 스타일 DNA가 StyleGuard에 정확히 주입되는가
8. **Story Expander 2-모델 폴백**: Pro→Flash 폴백 시 데이터 손실 없는가
9. **Preset Registry 장르별 기본값**: 10개 장르의 기본값이 빠짐없이 정의되고 로드되는가
10. **Concept→Bible 무결성**: `generate_from_concept()` 출력 스키마가 Stage 2 입력과 정합하는가
11. **T2-001 P0 후속**: `plot_roadmap` 미주입 문제가 메뉴 플로우의 어느 지점에서 발생하는가 (루트코즈 추적)

---

## 4. Terminal 2 — 교차 스테이지 통합 & 미해결 P1 추적

### 미조사 배경

1차 T1~T5는 각자 범위 내만 검사. **스테이지 간 데이터 핸드오프**와 **기존 P0/P1 미해결 건의 루트코즈**는 조사 범위 밖.
특히 T3-003(Blueprint→Manuscript 계약 미검증), T3-029(Director 주권 침해), T4-P1-03/04(자동 PASS/REJECT) 등이 미해결.

### 담당 범위

**미해결 P0/P1 추적 (7건)**

| ID | Sev | 내용 | 원 터미널 | 추적 필요 |
|----|-----|------|----------|----------|
| T2-001 | **P0** | Concept flow `plot_roadmap` 미주입 → Stage 2 빈 리스트 | T2 | 루트코즈: 어느 함수에서 누락? 수정 영향 범위? |
| T3-003 | P1 | Blueprint→Manuscript 스키마 계약 테스트 부재 | T3 | 실제 필드 매핑 전수 대조 |
| T3-004 | P1 | Advisory Chain 병렬 실행 실제 테스트 부재 | T3 | ThreadPoolExecutor 실동작 경로 추적 |
| T3-029 | P1 | `continuity_pins` → Director PASS 오버라이드 (대원칙 3 위반) | T3 | 코드 경로 추적, 위반 범위 확정 |
| T4-P1-03 | P1 | 단일 Blueprint 후보 → Director LLM 우회, Python-only PASS | T4 | 코드 경로 확인, 대원칙 3 위반 여부 |
| T4-P1-04 | P1 | `apply_adaptive_decision` → Director PASS를 REJECT으로 변경 | T4 | 코드 경로 확인, 대원칙 3 위반 여부 |
| T5-WS-016 | P1 | FactLedger에 deceased NPC guard 부재 (대원칙 4 위반) | T5 | 5개 섹션 중 guard 삽입 지점 확정 |

**교차 스테이지 데이터 핸드오프 (미조사)**

| 핸드오프 | 상류 | 하류 | 검증 내용 |
|----------|------|------|----------|
| Stage 0 → Stage 2 | `stage0/` 출력 | `stage2_orchestrator` 입력 | 바이블/NPC/장르/스타일 전량 전달 여부 |
| Stage 2 → Stage 3 | `stage2_finalizer` 출력 | `stage3_orchestrator` 입력 | Arc 스키마 + 메타데이터 완전성 |
| Stage 3 → Stage 4 | `stage3_orchestrator` 출력 | `stage4_orchestrator` 입력 | Blueprint 스키마 전 필드 매핑 (**T3-003**) |
| Stage 4 후처리 → DB | `stage4_post_processor` | `db_manager` | WorldState/FactLedger/ChainLink 갱신 완전성 |
| Stage 4 → 다음 에피소드 | DB 저장 | 다음 에피소드 Stage 2 | 연속성 데이터 전달 누수 없는가 |

**DI Context 쓰기-되돌림 (Write-back) 검증**

| Context | 방향 | 검증 |
|---------|------|------|
| Stage2Context → app | 단방향 스냅샷 | Stage 2 종료 후 StateTracker 등 write-back 누락 없는가 |
| Stage3Context → app | lazy init | Stage 3 종료 후 동기화 3줄 정확한가 |
| Stage4Context → app | 단방향 스냅샷 | Stage 4 종료 후 write-back 전량 확인 |

### 핵심 검사 포인트

1. **T2-001 루트코즈**: `plot_roadmap` 필드가 `generate_from_concept()` → Bible JSON → Stage 2 입력 경로 중 어디서 소실되는가
2. **T3-003 실제 매핑**: Blueprint JSON의 전 필드를 열거하고, Stage 4가 읽는 필드와 1:1 대조
3. **T3-029 코드 추적**: `continuity_pins`가 Director PASS를 오버라이드하는 정확한 코드 경로 (파일, 라인)
4. **T4-P1-03/04 대원칙 3 확정**: 두 건 모두 대원칙 3 위반이 맞는지 CLAUDE.md와 최종 대조
5. **T5-WS-016 guard 설계**: FactLedger 5개 섹션 중 deceased guard 삽입 지점 및 구현 방향
6. **Write-back 누수**: DI Context 3개의 write-back 경로 전수 확인
7. **에피소드 연속성**: episode N 종료 → episode N+1 시작 시 전달되는 데이터 전수 목록

---

## 5. Terminal 3 — Lite Mode & Tools (완전 미감사)

### 미조사 배경

1차·2차 마스터 오더 모두에서 완전히 배제된 시스템. `lite_mode/` 32개 파일과 `tools/` 12개 + `tools2/` 2개 + `main_tools/` 1개.
프로덕션 파이프라인과 별도이나, **프로덕션 모듈을 import하여 직접 실행**하므로 정합성 검증 필요.

### 담당 범위

**Lite Mode** (`lite_mode/`, ~32개 파일)
| 경로/파일 | 역할 (추정) |
|-----------|------------|
| `lite_mode/main_lite.py` | 독립 진입점 |
| `lite_mode/bridge/gemini_driver.py` | Gemini API 직접 드라이버 |
| `lite_mode/bridge/runner.py` | 프로세스 실행 브릿지 |
| `lite_mode/bridge/ui_discovery.py` | UI 인터랙션 디스커버리 |
| `lite_mode/bridge/state_ledger.py` | 상태 관리 |
| `lite_mode/bridge/prompt_builder.py` | 간소화 프롬프트 생성 |
| `lite_mode/test_*.py` (~15개) | Lite Mode 전용 테스트 |
| `lite_mode/run_*.py`, `inspect_*.py` | 프로젝트별 실행 스크립트 |

**Tools** (`tools/`, 12개 스크립트)
| 파일 | 역할 (추정) |
|------|------------|
| `tools/story_expander.py` | 구버전 스토리 확장기 (Stage 0 버전과 다름) |
| `tools/treatment_extractor.py` | 트리트먼트 추출기 |
| `tools/bible_builder.py` | 바이블 구축 유틸 |
| `tools/treatment_builder.py` | 트리트먼트 블록 생성 |
| `tools/genre_library_builder.py` | 장르별 템플릿 빌더 |
| `tools/db_porter.py` | DB 마이그레이션/포팅 |
| `tools/normalize_arcs_db.py` | Arc DB 정규화 |
| `tools/fix_future_items.py` | 미래 아이템 수정기 |
| `tools/blueprint_name_fixer.py` | 블루프린트 이름 수정기 |
| `tools/concat_txt.py` | 텍스트 결합 |
| `tools/0_json만들기.py` | JSON 생성 유틸 |
| (기타) | |

**Tools2** (`tools2/`, 2개)
| 파일 | 역할 |
|------|------|
| `tools2/automate_snack.py` | 자동화 헬퍼 |
| `tools2/studio_dashboard.py` | 대시보드 유틸 |

**Blueprint Editor** (`main_tools/blueprint_editor.py`, ~200줄)
- `get_project_list()` — DB 직접 프로젝트 열거
- `load_blueprint()` / `save_blueprint()` — SQLite 직접 조작
- `delete_blueprint()` — DB 뮤테이션
- `open_in_editor()` — 외부 에디터 (플랫폼별)

### 핵심 검사 포인트

1. **Lite Mode 생존 여부**: 현재 프로덕션 코드와 호환 가능한가, 아니면 완전히 부패했는가
2. **Lite Mode import 정합성**: 프로덕션 모듈을 import하는 경로가 현재 시그니처와 일치하는가
3. **Lite Mode gemini_driver**: 프로덕션 `llm_router`를 우회하는 직접 API 호출 — 보안·비용 위험
4. **Tools ↔ 프로덕션 코드 분기**: `tools/story_expander.py` vs `stage0/story_expander.py` 차이점, 혼용 위험
5. **DB 직접 조작 위험**: `db_porter.py`, `normalize_arcs_db.py`, `blueprint_editor.py`가 프로덕션 DB를 직접 수정 시 무결성 위험
6. **Dead 코드 판정**: 각 tool이 실제 사용되는가, 완전히 레거시인가
7. **보안**: `blueprint_editor.py`의 `open_in_editor()` — 커맨드 인젝션 가능성
8. **데이터 손실 위험**: 삭제/수정 기능이 있는 도구의 안전장치 존재 여부

---

## 6. Terminal 4 — API 심층 & Desktop 통합

### 미조사 배경

1차 T5에서 `bridge_server.py`를 파일 단위로 열거했지만, **엔드포인트별 요청/응답 검증, WebSocket 프로토콜, 이벤트 브로드캐스팅**은 미검사.
Desktop Electron도 파일 열거만. T5 보고서에서 API 계약 불일치 3건(T5-API-03~05) 발견했지만 심층 조사 미실시.

### 담당 범위

**Bridge Server 엔드포인트별 심층 검사** (`modules/api/bridge_server.py`, ~1,549줄)
| 엔드포인트 | 라인 (추정) | 검사 내용 |
|-----------|------------|----------|
| `POST /run` | L1265 | 요청 검증, 프로세스 생성, 에러 응답 |
| `POST /run/{run_id}/input` | L1372 | stdin 파이핑, run_id 검증 |
| `POST /stop` | L1402 | 프로세스 Kill, 정리 |
| `GET /status` | L1420 | 상태 조회, race condition |
| `GET /quality/summary` | L1438 | 품질 메트릭 조회 |
| `GET /quality/dashboard` | L1455 | 대시보드 데이터 |
| `POST /quality/review` | L1485 | 품질 리뷰 제출 |
| `GET /safe-ops/preview` | L1469 | 오퍼레이션 프리뷰 |
| `WS /events` | L1532 | WebSocket 이벤트 스트리밍 |

**WebSocket Manager** (`bridge_server.py` 내, L97-143)
- 연결 관리, 브로드캐스팅, 에러 복구

**Process Runner 큐/이벤트 모델** (`modules/api/process_runner.py`, ~676줄)
- `ProcessRunner` 클래스: 큐 관리, 백그라운드 실행, stdin/stdout 파이핑, 에러 복구

**보조 API 모듈**
| 파일 | 줄수 | 역할 |
|------|------|------|
| `modules/api/risk_approval.py` | 215 | 위험 승인 플로우 |
| `modules/api/prompt_broker.py` | 184 | 프롬프트 라우팅·캐싱 |
| `modules/api/prompt_classifier.py` | 144 | 프롬프트 분류 |
| `modules/api/run_validator.py` | 89 | 실행 검증 |

**Desktop Electron 심층** (`geuldobi-desktop/`)
| 파일 | 검사 내용 |
|------|----------|
| `src/main.js` (843줄) | Electron main process: 윈도우/메뉴/IPC, 프로세스 라이프사이클 |
| `src/preload.js` (54줄) | `contextBridge.exposeInMainWorld()` 화이트리스트 |
| `src/index.html` | inline script, CSP, XSS 방어 |
| `main.js` (758줄) | geuldobi-desktop 루트 — src/main.js와 역할 분리? 중복? |
| `package.json` | 의존성 버전, 알려진 취약점 |
| `src/splash/splash.js` | 스플래시 스크린 |
| `src/splash/lucide.js` | 아이콘 라이브러리 |

**API Contract**
| 파일 | 대조 대상 |
|------|----------|
| `docs/implementation/api-contract-v1.yaml` | bridge_server.py 전 엔드포인트 |
| `docs/implementation/prompt-map-v1.json` | prompt_broker.py 라우팅 |

**기존 미해결 (T5 보고서)**
- T5-API-03: 포트 8000 vs 실제 8300 불일치
- T5-API-04: 에러 코드 3개 누락
- T5-API-05: 엔드포인트 4개 누락

### 핵심 검사 포인트

1. **엔드포인트 입력 검증**: 모든 POST 엔드포인트의 요청 바디 검증 (필수 필드 누락, 타입 오류, 악의적 입력)
2. **WebSocket 안정성**: 연결 끊김, 재연결, 메시지 순서 보장, 백프레셔
3. **Process Runner 동시성**: 동시 실행 요청 처리, 큐 오버플로, stdin 경합
4. **Race Condition**: `/status` 조회와 `/stop` 동시 호출 시 상태 불일치
5. **T5-API-03~05 루트코즈**: 포트·에러코드·엔드포인트 불일치의 근본 원인과 수정 영향 범위
6. **Electron 보안 3대 항목**: `nodeIntegration: false`, `contextIsolation: true`, `webSecurity: true` 확인
7. **Preload 화이트리스트**: `contextBridge`에 노출된 API가 최소 권한 원칙을 준수하는가
8. **Desktop↔Backend 프로토콜**: HTTP + WS 메시지 형식이 양쪽에서 동일하게 처리되는가
9. **이중 main.js**: 루트 `main.js` vs `geuldobi-desktop/main.js` vs `src/main.js` 3개의 역할과 실행 흐름
10. **package.json 의존성**: `npm audit` 수준의 알려진 취약점 존재 여부

---

## 7. Terminal 5 — 보안·성능·대규모 시나리오

### 미조사 배경

1차~2차 감사는 **정적 코드 분석** 중심. 런타임 조건(보안 공격, 대규모 데이터, 성능 병목, 동시성)은 전혀 미검사.
T1~T5 보고서에서 관련 이슈가 일부 플래그되었지만 심층 조사 미실시.

### 담당 범위 (횡단 감사 — 전 모듈 대상)

**보안 감사**
| 공격 벡터 | 검사 대상 파일 | 검사 내용 |
|-----------|--------------|----------|
| 프롬프트 인젝션 | NPC 이름/아이템/설명 → LLM 프롬프트 | NPC 이름에 인젝션 페이로드 삽입 시 LLM 동작 변조 가능성 |
| SQL 인젝션 | `db_manager.py` 전 쿼리, `blueprint_editor.py` | parameterized query 사용 여부, 사용자 입력 직접 삽입 |
| 경로 조작 | 프로젝트 경로, 파일 선택 메뉴, Work Guard YAML 로딩 | `../` 등 path traversal 방어 |
| JSON 역직렬화 | LLM 응답 파싱 (`_extract_json_robust`), Config 로딩 | 악의적 JSON 구조 (깊은 중첩, 거대 배열) |
| XSS | Desktop `index.html`, bridge_server 응답 | HTML 이스케이프, CSP 헤더 |

**성능 병목 분석**
| 영역 | 검사 대상 | 검사 내용 |
|------|----------|----------|
| DB 쿼리 | `db_manager.py` 185+ cursor 사용 | N+1 쿼리, 인덱스 미사용, 대량 데이터 풀스캔 |
| LLM 비용 | Stage 2 앙상블 10+ 재시도 | 최악의 경우 비용 상한, 조기 종료 조건 |
| Advisory 병렬 | ThreadPoolExecutor(8), 60s timeout | 8개 전부 timeout 시 총 300s, 부분 실패 복구 |
| 캐시 효율 | Context Caching TTL 600s/1800s | TTL 만료 후 재생성 비용, 캐시 적중률 |
| 메모리 | VecMemory, 대량 NPC, 100+ 에피소드 | 메모리 누수, 무한 성장 구조 |

**대규모 시나리오 분석**
| 시나리오 | 검사 내용 |
|----------|----------|
| 100+ 에피소드 | FactLedger `MAX_HISTORY=10` eviction 정확성, WorldState 비대화 |
| 50+ NPC | StateTracker NPC 관리 스케일링, 관계도 O(N²) |
| Volume 전환 | `volume_summary` → `series_summary` 계층 정합성 |
| 동시 프로젝트 | 싱글톤 오염: SemanticItemRegistry, QualityDashboard, LLMRouter |
| 장기 실행 | 12시간+ 세션: 메모리 누수, DB 커넥션 풀 고갈, 파일 핸들 |

**동시성 안전성**
| 영역 | 검사 내용 |
|------|----------|
| DB | 공유 커서 185+개, 스레드 안전성 |
| ThreadPoolExecutor | Advisory 8병렬 + DB 동시 접근 |
| WebSocket | 다중 클라이언트 동시 연결 |
| 파일 I/O | Work Guard YAML / 프로젝트 파일 동시 읽기/쓰기 |

**기존 플래그 항목 (심층 추적)**
| ID | 내용 |
|----|------|
| T1-07 P2 | DB 공유 커서 아키텍처 취약 |
| T1-22 P3 | LLMRouter 싱글톤 스레드 안전성 |
| T2-032 P3 | 한국어 숫자 파싱 ("1.5억") 에지 케이스 |
| T5-NAR-17 P2 | SemanticItemRegistry 교차 프로젝트 오염 |
| T5-API-01/T4-P2-Q05 P2 | QualityDashboard 인스턴스 공유 |

### 핵심 검사 포인트

1. **SQL 인젝션 전수**: `db_manager.py` 전 쿼리에서 parameterized query 사용 확인, 사용자 입력 직접 삽입 0건 확인
2. **프롬프트 인젝션 경로**: NPC 이름/아이템 설명이 LLM 프롬프트에 삽입되는 전 경로 추적, 이스케이프/샌드박싱 확인
3. **경로 조작**: 프로젝트 경로 + 파일 선택에서 `..` traversal 방어 코드 존재 확인
4. **N+1 쿼리**: 루프 안 DB 조회 패턴 식별, 배치 쿼리로 대체 가능한 지점
5. **100+ 에피소드 시뮬레이션**: FactLedger/WorldState/ChainLink의 데이터량 증가 시 성능 추정
6. **싱글톤 오염**: 3개 싱글톤(SemanticItemRegistry, QualityDashboard, LLMRouter)의 프로젝트 전환 시 격리 검증
7. **Advisory 전체 timeout**: 8개 advisory 전부 60s timeout 시 Stage 4 전체 실패 처리 경로
8. **한국어 숫자 파싱**: "1.5억", "3000만원", "10조" 등 에지 케이스 전수 확인

---

## 8. 각 터미널에 내릴 오더

### Terminal 1 오더

```
OPUS TF — Deep-dive Terminal 1: Stage 0 세부 메뉴 & UI 플로우 전량 심층 조사

너는 글도비 시스템의 Stage 0 메뉴·UI 플로우 전담 OPUS TF다.
1~2차 감사에서 "파일 열거만" 되고 내부 메뉴 로직이 미검사된 Stage 0 전역을 심층 조사한다.

■ 범위:
  - modules/core/stage0/__init__.py (774줄) — StageZeroManager 메뉴 시스템 전체
    · show_menu(), show_genre_menu(), show_protagonist_config_menu() (4개 하위 메뉴)
    · manage_work_guard() (4개 액션: import/init/preview/delete)
    · run_new_project_flow(), generate_from_concept()
  - modules/core/stage0/reverse_expander.py (1,178줄) — 역추출 상태머신 내부 로직
  - modules/core/stage0/style_extractor.py (1,143줄) — 스타일 DNA 추출 내부 로직
  - modules/core/stage0/story_expander.py (600줄) — 컨셉 분석, 장르 자동감지, 2-모델 폴백
  - modules/core/stage0/preset_registry.py (739줄) — 필드 프리셋, 장르별 기본값
  - modules/core/stage0/spinner.py (666줄) — 스피너 상태관리
  - modules/core/stage01_helpers.py (740줄) — 6-모드 디스패처 (Mode 1~6 전체)
  - main_a.py 중 Stage 0 관련 메서드: _select_genre(), _select_project(),
    _ui_select_bible(), _ui_select_treatment(), _run_main_process() Stage 0 분기
  - 관련 테스트 6개: test_stage0_fixes, test_stage0_pov, test_stage0_work_guard_style_cache,
    test_reverse_expander_g2, test_stage01_helpers, test_process_runner_stage0_inputs

■ 임무 (6-Point Inspection + 자체 3PASS):
1. 메뉴 입력 검증: 모든 input()/UI 선택의 범위 외·빈·특수문자 입력 처리
2. 6-모드 분기: stage_0_extended(mode) 6개 분기가 올바른 서브모듈을 호출하는가
3. 장르 선택 → Stage 2 전파: show_genre_menu() 결과가 파이프라인 끝까지 도달하는가
4. POV 선택 → Stage 4 전파: POV/전생타입/세계관출신이 ChiefWriter까지 도달하는가
5. Work Guard 관리: 4개 액션의 파일 I/O 안전성, 경로 검증
6. Reverse Expander 상태머신: 다중 패스 상태 전이 정확성, 실패 복구
7. Style Extractor → StyleGuard: 추출 결과가 정확히 주입되는가
8. Story Expander 폴백: Pro→Flash 전환 시 데이터 손실 없는가
9. Preset Registry: 10개 장르 기본값 전량 정의·로드 확인
10. T2-001(P0) 후속: plot_roadmap 미주입의 Stage 0 측 루트코즈 추적
11. 관련 테스트 6개: 핵심 분기 커버 여부 확인

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 메서드 초벌 스캔, 후보 + 확신도(HIGH/MED/LOW)
  - PASS 2: 코드 증거 재확인 + CLAUDE.md 대조 + 기존 T2 보고서 대조 → 중복·오탐 제거
  - PASS 3: 최종 확정 + Severity + 오탐 로그

■ 보고: [S-T1-{SEQ}] 형식. Severity P0~P3.
  보고서 말미: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md, 1차 T2 보고서 (OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md)
```

### Terminal 2 오더

```
OPUS TF — Deep-dive Terminal 2: 교차 스테이지 통합 & P1 미해결 추적

너는 글도비 시스템의 교차 스테이지 통합 추적 담당 OPUS TF다.
1차 T1~T5에서 발견된 P0 1건 + 핵심 P1 6건의 루트코즈를 추적하고,
스테이지 간 데이터 핸드오프의 빈틈을 전수 검증한다.

■ 범위:
  미해결 P0/P1 7건:
  - T2-001 (P0): plot_roadmap 미주입 → Stage 2 빈 리스트
  - T3-003 (P1): Blueprint→Manuscript 스키마 계약 테스트 부재
  - T3-029 (P1): continuity_pins → Director PASS 오버라이드 (대원칙 3)
  - T4-P1-03 (P1): 단일 Blueprint → Director LLM 우회
  - T4-P1-04 (P1): apply_adaptive_decision → Director PASS→REJECT
  - T5-WS-016 (P1): FactLedger deceased guard 부재 (대원칙 4)
  - T3-004 (P1): Advisory Chain 병렬 테스트 부재

  교차 핸드오프 5개:
  - Stage 0 → Stage 2 (바이블/NPC/장르/스타일)
  - Stage 2 → Stage 3 (Arc + 메타데이터)
  - Stage 3 → Stage 4 (Blueprint 전 필드)
  - Stage 4 → DB (후처리 갱신)
  - DB → 다음 에피소드 Stage 2 (연속성)

  DI Context Write-back 3개:
  - Stage2Context → app, Stage3Context → app, Stage4Context → app

■ 임무 (자체 3PASS):
1. T2-001: generate_from_concept() → Bible JSON → Stage 2 입력 경로에서 plot_roadmap 소실 지점 확정
2. T3-003: Blueprint JSON 전 필드 열거 → Stage 4가 읽는 필드 1:1 대조표 작성
3. T3-029: continuity_pins 오버라이드 코드 경로 (파일:라인) 확정, 대원칙 3 위반 여부 최종 판정
4. T4-P1-03/04: 각각 코드 경로 확정, CLAUDE.md 대원칙 3과 최종 대조
5. T5-WS-016: FactLedger 5개 섹션 열거, deceased guard 삽입 지점 확정
6. T3-004: ThreadPoolExecutor(8) 실행 경로 추적, timeout/cancel/exception 전 분기
7. 핸드오프 5개: 상류 출력 스키마 ↔ 하류 입력 스키마 필드 전수 대조
8. Write-back 3개: Stage 종료 후 app에 동기화되는 데이터 전수 확인

■ 자체 3PASS 감리 필수:
  - PASS 1: 7건 추적 + 5개 핸드오프 + 3개 write-back 초벌 조사
  - PASS 2: 코드 증거 재확인, 1차 보고서 원문과 대조, 오탐 제거
  - PASS 3: 최종 확정, 각 P0/P1의 "확정 루트코즈" + "수정 영향 범위" 명시

■ 보고: [S-T2-{SEQ}] 형식. Severity P0~P3.
  보고서 말미: "미해결 7건 중 X건 루트코즈 확정, Y건 오탐 확인"
  추가: "핸드오프 대조표" 별도 섹션
■ 금지: 직접 코드 수정. 루트코즈 확정과 수정 방향 제안만.
■ 참조: CLAUDE.md, 1차 T2/T3/T4/T5 보고서 전량
```

### Terminal 3 오더

```
OPUS TF — Deep-dive Terminal 3: Lite Mode & Tools 완전 감사

너는 글도비 시스템의 Lite Mode & Tools 담당 OPUS TF다.
1~2차 감사에서 완전히 배제된 보조 시스템을 처음으로 전량 감사한다.

■ 범위:
  - lite_mode/ 하위 전량 (~32개 파일): main_lite.py, bridge/*, test_*, run_*, inspect_*
  - tools/ 하위 전량 (~12개 스크립트)
  - tools2/ 하위 전량 (2개)
  - main_tools/blueprint_editor.py (~200줄)

■ 임무 (자체 3PASS):
1. Lite Mode 생존 여부: 현재 프로덕션 코드와 호환 가능한가, import 에러 없이 실행 가능한가
2. Lite Mode gemini_driver: 프로덕션 llm_router를 우회하는 직접 API 호출 — 보안·비용 위험
3. Lite Mode state_ledger: 프로덕션 db_manager와 스키마 호환성
4. Tools 분기 확인: tools/story_expander.py vs stage0/story_expander.py 차이, 혼용 위험
5. DB 직접 조작: db_porter, normalize_arcs_db, blueprint_editor의 무결성 위험
6. Dead 코드 판정: 각 tool의 실제 사용 여부, 레거시 여부
7. 보안: blueprint_editor open_in_editor() 커맨드 인젝션, 경로 검증
8. 데이터 손실: 삭제/수정 기능의 안전장치 존재 여부
9. Lite Mode 테스트: test_* 파일이 실행 가능하고 의미 있는가

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 스캔, 생존/dead/위험 후보 기록
  - PASS 2: import 추적 + 프로덕션 코드 대조 → dead 코드 확정, 위험도 재평가
  - PASS 3: 최종 확정 + "삭제 권고" vs "수정 필요" vs "정상" 3분류

■ 보고: [S-T3-{SEQ}] 형식. Severity P0~P3.
  보고서 말미: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "삭제 권고 목록" + "레거시 판정 목록" 별도 섹션
■ 금지: 파일 직접 삭제/수정.
■ 참조: CLAUDE.md, 프로덕션 모듈 시그니처 (import 정합성 확인용)
```

### Terminal 4 오더

```
OPUS TF — Deep-dive Terminal 4: API 심층 & Desktop 통합 감사

너는 글도비 시스템의 API/Desktop 통합 담당 OPUS TF다.
1차에서 파일 열거만 된 API 레이어와 Desktop을 엔드포인트/메시지 단위로 심층 감사한다.

■ 범위:
  - modules/api/bridge_server.py (1,549줄) — 전 엔드포인트 (9개 라우트 + WebSocket)
  - modules/api/process_runner.py (676줄) — 큐/이벤트 모델
  - modules/api/risk_approval.py (215줄)
  - modules/api/prompt_broker.py (184줄)
  - modules/api/prompt_classifier.py (144줄)
  - modules/api/run_validator.py (89줄)
  - geuldobi-desktop/main.js (758줄) — Electron main process
  - geuldobi-desktop/src/main.js (843줄) — renderer 로직
  - geuldobi-desktop/src/preload.js (54줄) — IPC 보안 브릿지
  - geuldobi-desktop/src/index.html — UI 구조
  - geuldobi-desktop/package.json — 의존성
  - geuldobi-desktop/src/splash/* — 스플래시
  - docs/implementation/api-contract-v1.yaml — API 계약
  - 기존 미해결: T5-API-03(포트), T5-API-04(에러코드), T5-API-05(엔드포인트)

■ 임무 (자체 3PASS):
1. 엔드포인트 입력 검증: 9개 라우트 각각의 요청 바디 검증 (필수 필드, 타입, 악의적 입력)
2. WebSocket 안정성: 연결 끊김, 재연결, 메시지 순서, 백프레셔
3. Process Runner 동시성: 동시 실행 요청, 큐 오버플로, stdin 경합
4. Race Condition: /status + /stop 동시 호출 상태 불일치
5. T5-API-03~05 루트코즈: 포트·에러코드·엔드포인트 불일치 근본 원인
6. Electron 보안: nodeIntegration, contextIsolation, webSecurity
7. Preload 화이트리스트: contextBridge 노출 API 최소 권한 확인
8. Desktop↔Backend 프로토콜: HTTP+WS 메시지 형식 양쪽 동일 처리 확인
9. 이중 main.js: 3개 파일(루트/geuldobi-desktop/src) 역할·실행 흐름 확정
10. package.json: 알려진 취약점 버전 존재 여부

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 엔드포인트·전 IPC 메시지 초벌 스캔, 후보 기록
  - PASS 2: 양쪽(Backend/Frontend) 코드 교차 대조, api-contract.yaml 대조
  - PASS 3: 최종 확정 + "프로토콜 불일치 대조표" 첨부

■ 보고: [S-T4-{SEQ}] 형식. Severity P0~P3.
  보고서 말미: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "엔드포인트 대조표" + "IPC 메시지 대조표" 별도 섹션
■ 금지: 코드 직접 수정, 패키지 업데이트 실행.
■ 참조: CLAUDE.md, api-contract-v1.yaml, 1차 T5 보고서 (T5-API 섹션)
```

### Terminal 5 오더

```
OPUS TF — Deep-dive Terminal 5: 보안·성능·대규모 시나리오 횡단 감사

너는 글도비 시스템의 보안·성능·스케일링 담당 OPUS TF다.
1~2차의 정적 코드 분석에서 다루지 못한 런타임 조건을 횡단 감사한다.

■ 범위 (횡단 — 전 모듈 대상):
  보안:
  - SQL 인젝션: db_manager.py 전 쿼리 (185+ cursor), blueprint_editor.py
  - 프롬프트 인젝션: NPC 이름/아이템 → LLM 프롬프트 삽입 전 경로
  - 경로 조작: 프로젝트 경로, 파일 선택, Work Guard YAML 로딩
  - JSON 역직렬화: _extract_json_robust(), Config 로딩
  - XSS: Desktop index.html, bridge_server 응답

  성능:
  - DB N+1 쿼리: 루프 안 DB 조회 패턴
  - LLM 비용 상한: Stage 2 앙상블 최악 비용
  - Advisory 전체 timeout: 8개 전부 60s timeout 시 처리
  - 캐시 적중률: Context Caching TTL 효과
  - 메모리: VecMemory, 대량 NPC, 100+ 에피소드

  대규모 시나리오:
  - 100+ 에피소드: FactLedger MAX_HISTORY=10, WorldState 비대화
  - 50+ NPC: StateTracker 스케일링, 관계도 O(N²)
  - 동시 프로젝트: 싱글톤 오염 3개 (SemanticItemRegistry, QualityDashboard, LLMRouter)
  - 장기 실행: 12시간+ 세션 메모리 누수, 커넥션 풀

  기존 플래그:
  - T1-07(DB 커서), T1-22(LLMRouter 스레드), T2-032(한국어 숫자),
    T5-NAR-17(SemanticItemRegistry), T5-API-01/T4-P2-Q05(QualityDashboard)

■ 임무 (자체 3PASS):
1. SQL 인젝션: db_manager.py 전 쿼리에서 parameterized query 확인, 직접 삽입 0건 확인
2. 프롬프트 인젝션: NPC 이름/아이템이 LLM 프롬프트에 삽입되는 전 경로 추적
3. 경로 조작: 프로젝트 경로 + 파일 선택에서 path traversal 방어 확인
4. N+1 쿼리: 루프 안 DB 조회 패턴 5건 이상 식별
5. 100+ 에피소드: FactLedger/WorldState/ChainLink 데이터량 증가 시 성능 영향 추정
6. 싱글톤 오염: 3개 싱글톤의 프로젝트 전환 시 격리 검증
7. Advisory 전체 timeout: 8개 전부 실패 시 Stage 4 처리 경로 확인
8. 한국어 숫자 파싱: "1.5억", "3000만원", "10조" 에지 케이스 전수

■ 자체 3PASS 감리 필수:
  - PASS 1: 공격 벡터별·병목별 초벌 스캔, 후보 + 확신도
  - PASS 2: 실제 코드 경로 추적 + 기존 보안 장치 확인 → 방어됨=오탐 제거
  - PASS 3: 최종 확정 + "즉시 수정" vs "모니터링" vs "수용 가능" 3분류

■ 보고: [S-T5-{SEQ}] 형식. Severity P0~P3.
  보고서 말미: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "보안 취약점 요약표" + "성능 병목 Top 5" + "스케일링 한계점" 별도 섹션
■ 금지: 직접 코드 수정, 실제 공격 실행, DB 수정.
■ 참조: CLAUDE.md, 1차 T1~T5 보고서 전량 (기존 플래그 항목)
```

---

## 9. 취합 프로세스

### 9.1 개별 터미널 완료 후

1. **P0 즉시 에스컬레이션**: 보안 취약점(SQL 인젝션, XSS 등) P0 발견 시 즉시 보고
2. **1차 보고서 중복 제거**: 기존 265건과 대조하여 신규 발견만 채택
3. **교차 검증**: T1(Stage 0) ↔ T2(교차 핸드오프) 경계, T4(API) ↔ T5(보안) 경계 대조
4. **P1 추적 결과 통합**: T2의 미해결 7건 추적 결과를 마스터에 반영

### 9.2 최종 마스터 보고서

- **파일명**: `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-consolidated-findings.md`
- **구성**:
  - Section A: 미해결 P0/P1 추적 결과 (T2)
  - Section B: 신규 발견 P0→P3 순 (T1/T3/T4/T5)
  - Section C: 보안 취약점 요약표 (T5)
  - Section D: 성능 병목 + 스케일링 한계점 (T5)
  - Section E: 삭제/레거시 권고 (T3)
  - Section F: 프로토콜 대조표 (T4)
- **오탐 통계**: 전 터미널 합산

---

## 10. 마스터 3PASS 감리 기록

### PASS 1 — 미조사 영역 커버리지 (완료)
- [x] Stage 0 메뉴 시스템 (774줄 + 서브모듈 5개 + 6-모드 디스패처) → T1 전담 배정
- [x] 교차 스테이지 핸드오프 5개 + 미해결 P0/P1 7건 → T2 배정
- [x] Lite Mode 32개 + Tools 12개 + Tools2 2개 + Blueprint Editor 1개 → T3 배정
- [x] API 9개 엔드포인트 + WebSocket + Desktop 통합 → T4 배정
- [x] 보안(5개 벡터) + 성능(5개 병목) + 대규모(4개 시나리오) + 동시성 → T5 횡단 배정
- [x] 1차 T1~T5 265건과의 중복 방지 지침 명시
- **수정**: T1에 "T2-001 Stage 0 측 루트코즈 추적" 추가 (T2와 양방향 연계)

### PASS 2 — 오더 정합성 (완료)
- [x] 5개 터미널 모두 범위·임무·3PASS·보고·금지·참조 6요소 완비
- [x] 보고 형식 `[S-TN-SEQ]`로 1차 `[TN-SEQ]` 및 2차 `[D-TN-SEQ]`와 구별
- [x] T1 오더에 Stage 0 서브모듈 5개(reverse_expander/style_extractor/story_expander/preset_registry/spinner) 명시
- [x] T2 오더에 미해결 7건 각각의 ID + Severity + 추적 목표 명시
- [x] T3 오더에 Lite Mode + Tools + Tools2 + main_tools 전량 명시
- [x] T4 오더에 기존 T5-API-03~05 미해결 건 포함
- [x] T5 오더에 기존 플래그 6건(T1-07/T1-22/T2-032/T5-NAR-17/T5-API-01/T4-P2-Q05) 포함
- **수정**: T2에 "DI Context Write-back 3개" 검사 추가 (교차 핸드오프의 일부)

### PASS 3 — 최종 점검 (완료)
- [x] 1차 감사 평균 65% 커버 → 3차에서 나머지 35% 중 핵심 영역 전량 배정 확인
- [x] Stage 0 세부 메뉴가 T1 전담 (사용자 요구사항 반영)
- [x] Stage 0 __init__.py 774줄의 메서드별 줄 범위가 T1 범위 테이블에 명시
- [x] stage01_helpers 6-모드 각각의 역할이 T1에 테이블로 명시
- [x] 미해결 P0 1건(T2-001)이 T1(Stage 0 측) + T2(전체 경로) 양쪽에서 추적
- [x] Lite Mode 존재 자체가 처음으로 감사 대상에 포함 (T3)
- [x] 보안 감사가 처음으로 독립 터미널 배정 (T5)
- [x] 취합 보고서에 6개 섹션(A~F) 구조 명시
- **최종 확인**: Stage 0 전담 T1 + 미해결 추적 T2 + 완전 미감사 T3 + API/Desktop 심층 T4 + 보안/성능 횡단 T5 — 미조사 35% 전량 커버 완비
