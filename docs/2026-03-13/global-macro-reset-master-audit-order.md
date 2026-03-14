# 전역 전량 전수 조사 마스터 오더 - 거시 구조 리셋판

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty
> Track: System Order
> Scope: 엔진, 스테이지 오케스트레이션, DB/복구, API 브리지, Electron 데스크톱, 테스트/릴리스, 잔존 경로

---

## 1. 발령 목적

3월 13일 기준 세부 전수조사 문서가 이미 다수 누적되어 있다. 그러나 현재 워크트리는 dirty 상태이고, `main_a.py` 중심의 실가동 경로, `modules/api` 제어면, `geuldobi-desktop/` 패키징면, `docs/stage_map/` 계약 문서가 동시에 진화하고 있다.  
이번 오더의 목적은 세부 버그 발굴이 아니라, **지금 이 워크트리에서 실제로 살아 있는 시스템이 무엇인지**를 다시 정의하는 데 있다.

핵심 질문은 다음 네 가지다.

1. 실제 composition root는 어디이며 어떤 경로가 live이고 어떤 경로가 잔존물인가.
2. DB/앵커/블루프린트/원고/로그 중 무엇이 진짜 handoff SSOT인가.
3. CLI형 엔진, FastAPI 브리지, Electron UI가 어떤 계약으로 연결되는가.
4. 지금의 리스크는 개별 함수 버그보다 **구조적 결합, 중복 표면, 드리프트** 중 어디에 더 큰가.

---

## 2. 현재 워크트리 기준선

### 2.1 파일/표면 규모

`rg --files` 기준 현재 주요 표면 규모는 다음과 같다.

| 구분 | 개수 |
|---|---:|
| `modules/` 전체 | 250 |
| `modules/core/` | 174 |
| `modules/domain/agents/` | 46 |
| `tests/` | 317 |
| `geuldobi-desktop/` | 47 |

### 2.2 대형 핫스팟

| 파일 | 줄 수 | 의미 |
|---|---:|---|
| `main_a.py` | 4204 | 앱 조립, 메뉴, Stage 진입, safe-op, one-stop 실행 |
| `modules/core/stage4_interview_round.py` | 4690 | Stage 4 실질 핵심 라운드, advisory/validator/patch 루프 |
| `modules/core/db_manager.py` | 3492 | SQLite SSOT, WAL, table boot, 복구/조회/쓰기 |
| `modules/domain/agents/base_agent.py` | 2046 | LLM 공통 계층, 캐시, 키 순환, router 진입 |
| `modules/core/stage3_orchestrator.py` | 2002 | Stage 3 블루프린트 배치 오케스트레이션 |
| `modules/core/stage4_orchestrator.py` | 1621 | Stage 4 세션/회차 오케스트레이션 |
| `modules/api/bridge_server.py` | 1544 | HTTP/WS 제어면, 데스크톱 백엔드 |
| `modules/core/stage2_orchestrator.py` | 1057 | Stage 2 아크 설계 오케스트레이션 |
| `geuldobi-desktop/src/main.js` | 846 | Electron 메인 프로세스, backend 부팅/종료 |
| `modules/api/process_runner.py` | 781 | `main_a.py` subprocess 래퍼, Mode A/B 입력 브리지 |

### 2.3 현재 확인된 조립 루트

`main_a.py`의 `SovereignApp`이 현재 엔진의 composition root다.

- `boot()` 시작점: `main_a.py:1053`
- 메인 루프: `main_a.py:2250`
- Stage 2 진입: `main_a.py:2754`
- Stage 3 진입: `main_a.py:2983`
- Stage 4 진입: `main_a.py:3557`
- destructive safe-op:
  - rollback: `main_a.py:3288`
  - wipe: `main_a.py:3328`
  - stage2 reset: `main_a.py:3226`
  - stage2 rewind: `main_a.py:3256`
- one-stop 실행:
  - frontier lag: `main_a.py:3697`
  - full one-stop: `main_a.py:3965`

`SovereignApp.__init__()`에서 이미 다음 서비스/오케스트레이터가 결합된다.

- `Stage2Orchestrator`
- `Stage3Orchestrator`
- `Stage4Orchestrator`
- `AuditService`
- `UIService`
- `StateService`
- `ProjectService`

즉, `modules/*`가 충분히 분리되어 있어도, **실행 시점의 live wiring은 여전히 `main_a.py`에 집중**되어 있다.

### 2.4 제어면과 외부 셸

현재 데스크톱 제어면은 다음 구조로 확인된다.

1. `geuldobi-desktop/src/main.js`
   - dev 모드에서는 `python -m uvicorn modules.api.bridge_server:app --port 8300`
   - packaged 모드에서는 `backend.exe` 실행
   - packaged 시 `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`, `GEULDOBI_ENGINE_EXE` 주입
2. `modules/api/bridge_server.py`
   - `POST /run`, `POST /stop`, `GET /status`, `WS /events`
   - `PromptBroker`, `RunValidator`, `RiskApprovalGate`, `ProcessRunner` 결합
3. `modules/api/process_runner.py`
   - `engine.exe` 또는 `python -u main_a.py` 실행
   - Mode A 사전 주입, Mode B 인터랙티브 프롬프트 브리지
4. `geuldobi-desktop/src/preload.js`
   - renderer에 run/stop/status/quality/project/workspace 계약 노출

중요: 현재 시스템은 **처음부터 API-native 엔진이 아니라, 인터랙티브 CLI 엔진을 외부에서 감싼 원격 제어 구조**다.

### 2.5 문서 기준면

현재 문서 기준면은 `docs/stage_map/`이 가장 안정적이다.

- `README.md`: 문서 사용 순서와 우선순위
- `interfaces.md`: stage handoff 계약
- `runbook.md`: destructive safe-op 의미론
- `agent_graph.md`: Stage 2/3/4 live call graph

이번 조사에서는 **코드가 1순위**, `docs/stage_map/*`가 2순위, 기존 상세 finding 문서가 3순위다.

---

## 3. 이번 오더의 핵심 가설

아래는 사실 확정이 아니라, 이번 조사에서 검증해야 할 거시 가설이다.

### G1. `main_a.py`는 아직도 “앱”이 아니라 “시스템 전체의 서비스 로케이터 + 메뉴 셸 + stage dispatcher”다.

분리된 서비스/오케스트레이터가 늘었지만, 실제 실행 경계는 `SovereignApp`에 남아 있다.  
따라서 버그보다 더 큰 리스크는 **live wiring drift**일 수 있다.

### G2. handoff의 진짜 중심은 txt 파일이 아니라 DB다.

`docs/stage_map/interfaces.md`와 `runbook.md` 모두 DB를 durable handoff surface로 본다.  
실제 조사 포인트는 “문서가 그렇게 말하는가”가 아니라, **모든 live 경로가 정말 DB truth를 우선하는가**다.

### G3. 데스크톱은 독립 제품처럼 보이지만, 실제로는 CLI 계약에 깊게 결박되어 있다.

`ProcessRunner`가 menu key, sub_key, pre-fed stdin, prompt broker를 사용한다는 점에서, 데스크톱은 엔진 API를 호출하는 것이 아니라 **엔진의 콘솔 프로토콜을 HTTP/WS로 재포장**한다.

### G4. 중복/잔존 표면이 거시 리스크다.

루트 `main.js`와 `geuldobi-desktop/src/main.js`가 병존하고, `UI/`는 자산 저장소로 보이며, `lite_mode/`, `test_mode/`, `tools/`, `tools2/`도 살아 있다.  
이 상태에서는 기능 버그보다 먼저 **무엇이 공식 경로인지**를 잃기 쉽다.

---

## 4. 조사 원칙

1. 이번 오더는 미시 버그 헌팅보다 거시 경계면 재정의가 우선이다.
2. “무슨 모듈이 있는가”보다 “실행 중 누가 누구를 호출하는가”를 우선 본다.
3. 코드 truth가 문서와 다르면 코드를 기준으로 문서 드리프트를 기록한다.
4. dirty 워크트리이므로 기존 변경을 되돌리거나 정리하지 않는다.
5. `UI/`, 루트 `main.js`, `lite_mode/`, `test_mode/`는 기본적으로 잔존/보조 표면 가설로 보되, 실제 참조 경로가 있으면 live로 승격한다.
6. UTF-8 이상 징후(문자 치환 깨짐)는 별도 drift 항목으로 기록한다.

## 4.1 실행 강제 규칙

1. 모든 산출물은 UTF-8 기준으로 읽고 기록한다.
2. 모든 트랙은 기본적으로 3PASS를 적용한다.
3. PASS 1은 후보 수집, PASS 2는 교차 검증, PASS 3은 오탐 제거와 최종 심각도 확정이다.
4. 컨텍스트가 압축되거나 세션이 길어져도 중단 선언 없이 다음 트랙으로 연속 진행한다.
5. 코드 직접 수정은 금지한다.
6. 필요 시 수정 가능한 대상은 오더 문서와 조사 문서뿐이다.
7. 문서화는 각 트랙 종료 직후 누적하고, 마지막에 통합 문서로 한 번 더 재정리한다.

---

## 5. 전역 거시 조사 트랙

## GMR-A. Composition Root & Live Wiring

### 대상
- `main_a.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `docs/stage_map/agent_graph.md`

### 조사 질문
- `SovereignApp`가 실제로 몇 개의 역할을 동시에 맡고 있는가.
- 분리된 Service/Orchestrator가 실질 분리인지, 단순 위임 껍데기인지.
- lazy import, bootstrap, agent attach가 stage 경계와 얼마나 분리되어 있는가.
- stage entry가 one-stop, safe-op, desktop control path와 어떻게 합류하는가.

### 산출물
- `GMR-A-composition-root-live-wiring-findings.md`

## GMR-B. Persistence, SSOT & Safe-Op Boundary

### 대상
- `modules/core/db_manager.py`
- `modules/core/services/project_service.py`
- `modules/core/runtime_paths.py`
- `docs/stage_map/interfaces.md`
- `docs/stage_map/runbook.md`

### 조사 질문
- DB가 실제로 유일한 durable truth인가.
- `anchors`, `blueprints`, `manuscripts`, `episode_bibles`, `state_logs`의 책임 경계가 명확한가.
- rollback / wipe / reset / rewind가 동일한 보존 규칙을 공유하는가.
- safe-op 이후 runtime cache/state invalidation이 구조적으로 보장되는가.

### 산출물
- `GMR-B-persistence-safeop-boundary-findings.md`

## GMR-C. Stage Contract & Handoff Shape

### 대상
- `docs/stage_map/interfaces.md`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`

### 조사 질문
- Stage 2 -> 3 -> 4 handoff contract가 문서와 코드에서 동일한가.
- degraded contract(`PASS_WITH_FIX`, `PASS_WITH_WARNING`, `None`, repair path`)가 어디서 허용되고 어디서 막히는가.
- txt export가 운용 artifact인지, 숨은 입력 경로인지.
- repair seam이 stage boundary를 흐리게 만드는가.

### 산출물
- `GMR-C-stage-contract-handoff-findings.md`

## GMR-D. Control Plane, Bridge & Desktop Shell

### 대상
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/prompt_broker.py`
- `modules/api/run_validator.py`
- `modules/api/risk_approval.py`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/package.json`

### 조사 질문
- 데스크톱이 어떤 콘솔 계약을 HTTP/WS 계약으로 번역하는가.
- Mode A와 Mode B가 어떤 기능 경계를 가지는가.
- `run_validator`와 `risk_approval`가 실제 destructive operation gate로 충분한가.
- dev 실행, packaged 실행, `engine.exe` fallback, `main_a.py` fallback이 같은 의미론을 유지하는가.

### 산출물
- `GMR-D-control-plane-desktop-findings.md`

## GMR-E. State, Cache, Concurrency & Recovery

### 대상
- `modules/domain/agents/base_agent.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/vec_memory.py`

### 조사 질문
- 클래스 레벨 캐시와 런타임 rollback의 무효화 타이밍이 맞는가.
- ThreadPool/async/subprocess가 공유 상태와 충돌하는 지점이 있는가.
- retry / patch / advisory chain이 fail-open으로 흘러가는 경로가 있는가.
- rollback 후 memory/world/fact/state가 같은 시점으로 복원되는가.

### 산출물
- `GMR-E-state-cache-concurrency-findings.md`

## GMR-F. Observability, Audit & Artifact Provenance

### 대상
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- `modules/core/metrics_collector.py`
- `modules/core/quality_dashboard.py`
- `logs/`
- `docs/stage_map/doc_status.md`

### 조사 질문
- run 하나를 기준으로 UI 이벤트, subprocess 로그, audit summary, DB 기록을 끝까지 추적할 수 있는가.
- packaged 환경과 dev 환경의 진단 정보 품질이 같은가.
- 품질 대시보드, audit log, session log가 같은 사건을 다른 이름으로 중복 기록하는가.
- 지금 부족한 것은 logging quantity가 아니라 **provenance chain**인지 확인한다.

### 산출물
- `GMR-F-observability-provenance-findings.md`

## GMR-G. Live Surface vs Legacy Surface

### 대상
- 루트 `main.js`
- `UI/`
- `lite_mode/`
- `test_mode/`
- `scripts/`
- `tools/`
- `tools2/`
- `docs/2026-03-13/*`

### 조사 질문
- 어떤 경로가 실제 제품 경로이고 어떤 경로가 실험/보조/보관 경로인가.
- 루트 `main.js`와 `geuldobi-desktop/src/main.js`의 관계는 공식 복제본인지 잔존물인지.
- `UI/`는 런타임 코드가 아니라 에셋 저장소인지 확정한다.
- 실가동 경로와 조사 문서가 1:1 대응되지 않는 표면을 식별한다.

### 산출물
- `GMR-G-live-vs-legacy-surface-findings.md`

## GMR-H. Test Envelope & Release Reality

### 대상
- `pyproject.toml`
- `tests/`
- `geuldobi-desktop/package.json`
- `build/`
- `README.md`
- `geuldobi-desktop/DESKTOP-GUIDE.md`

### 조사 질문
- 어떤 테스트가 live contract를 직접 보호하는가.
- 어떤 테스트가 과거 표면을 유지하고 있지만 제품 경로를 보호하지 못하는가.
- 패키징 경로(`backend.exe`, `engine.exe`, `python-embed`)가 개발 경로와 얼마나 다른가.
- README/가이드의 시스템 설명이 현재 코드와 얼마나 동기화되어 있는가.

### 산출물
- `GMR-H-test-release-envelope-findings.md`

---

## 6. 실행 순서

이번 조사는 아래 순서를 강제한다.

1. `GMR-A`로 live wiring을 확정한다.
2. `GMR-B`와 `GMR-C`로 데이터면/계약면을 고정한다.
3. `GMR-D`로 데스크톱 제어면을 고정한다.
4. `GMR-E`로 상태/캐시/복구 리스크를 본다.
5. `GMR-F`로 관측 가능성과 provenance를 검증한다.
6. `GMR-G`로 잔존 표면을 정리한다.
7. `GMR-H`로 테스트/릴리스 현실성을 정리한다.

이 순서를 뒤집으면, 미시 finding은 늘어도 거시 판단 기준이 계속 흔들린다.

---

## 7. finding 작성 규칙

### 우선순위 기준

- `P0`: 시스템 경계 붕괴. 잘못된 surface를 live로 오인하게 만들거나 destructive semantics를 뒤집는 문제.
- `P1`: stage handoff, DB truth, rollback/recovery, desktop bridge 계약을 실제로 어긋나게 만드는 문제.
- `P2`: 관측성/추적성 부족, 중복 표면, live/legacy 혼선.
- `P3`: 문서 드리프트, naming drift, 잔존 dead path 후보.

### finding 필수 필드

1. 제목
2. 심각도
3. 거시 범주
4. 관련 파일
5. 실제 관찰
6. 기대 계약
7. 왜 구조 리스크인지
8. 권장 후속 오더

---

## 8. 즉시 확인된 거시 리스크 후보

아래는 아직 최종 finding이 아니지만, 이번 마스터 오더가 직접 검증해야 할 후보들이다.

1. `main_a.py`가 여전히 너무 많은 live 책임을 가진다.
2. DB truth와 runtime cache truth 사이의 복원 순서가 항상 맞는지 확정되지 않았다.
3. 데스크톱은 API 제품처럼 보여도 실제로는 CLI 프로토콜에 깊게 결박돼 있다.
4. 루트 `main.js`와 `geuldobi-desktop/src/main.js` 병존은 운영 표면 혼선을 만들 수 있다.
5. `docs/stage_map/*`는 비교적 정리되어 있으나, dirty workspace에서는 즉시 드리프트 가능성이 높다.

---

## 9. 이번 오더의 완료 조건

다음 조건을 모두 만족해야 “전역 거시 조사 1차 완료”로 본다.

1. live composition root와 잔존 표면이 구분된다.
2. DB/contract/control-plane/desktop/recovery/test의 상위 구조도가 다시 그려진다.
3. 각 트랙별 후속 세부 조사 문서가 최소 1개 이상 연결된다.
4. 문서가 “이상적 아키텍처”가 아니라 **현재 dirty workspace의 실제 구조**를 설명한다.

---

## 10. 메모

- 이번 오더는 narrative pipeline blockguide 대상이 아니다.
- `docs/stage_map/*`는 참고 문서이지만 최종 truth는 아니다.
- 기존 2026-03-13 상세 cross-cutting 조사 문서는 이 오더의 하위 증거로만 취급한다.
- 코드 수정 오더와 혼합하지 말고, 먼저 구조 판단을 고정한다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
