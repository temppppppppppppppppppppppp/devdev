# Antigravity's Stage 0-4 Code Audit Report (2026-02-21)

## 1) 조사 목표 및 범위
- **조사 목적**: 기존 작성된 Codex의 전수조사 리포트와 병행하여, Antigravity만의 독립적인 관점(비동기 컨텍스트 안정성, 캐시/상태 일관성, API 계약 보장)에서 잠재적 버그와 개선점을 발굴합니다.
- **조사 대상**: Stage 0 ~ 4 로직 캡슐화 모듈들
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`

## 2) 구조적 아키텍처 리뷰 (Architecture & Modularity)
- **Lazy Initialization 도입**: Stage 2, 3, 4 모두 하위 모듈(`Stage2ValidationPipeline`, `Stage4PostProcessor` 등)과 의존성(`StateTracker`, `WorldStateManager`)을 필요 시점에 초기화(Lazy init)하여 메모리 풋프린트를 최적화하고 있습니다.
- **Robust Exception Handling**: 각 Stage는 LLM 호출 및 검증 시 발생하는 Exception을 비차단(Non-blocking) 형태로 잡은 후, `failure_report`를 기록하거나 fallback 기본값을 제공함으로써 파이프라인의 강건성을 유지합니다 (예: Stage 4의 `_extract_chain_link` 복구 로직).

## 3) 발굴된 주요 버그 및 리스크 (Antigravity's Findings)

### 🔴 BUG-01 [Critical in Async Context]: Stage 2 Async Event Loop Blocking
- **발생 위치**: `modules/core/stage2_orchestrator.py` 내 `stage_2_arcs_async_logic` (비동기 함수)
- **증거 코드**: 
  - L691: `user_choice = input("   선택 (기본: 2): ").strip()`
  - L720: `manual_input = input("   준비되면 [Enter]로 재시도... ").strip().lower()`
- **문제점**: `stage_2_arcs_async_logic`는 비동기 함수(`async def`)입니다. 내부에서 병렬 처리를 위해 `asyncio.gather` 등을 활용하지만, 에러 상황 복구 등의 시나리오에서 동기식 내장 함수인 `input()`을 직접 호출합니다. 
- **영향**: 표준 `input()`은 스레드를 블로킹하므로, 사용자 입력을 기다리는 동안 단일 스레드로 동작하는 Python **Asyncio Event Loop 전체가 정지(Freeze)됩니다**. 이는 백그라운드에서 돌고 있을 다른 비동기 작업(예: 알림, 로그 전송, 다른 워커)까지 모두 멈추게 만드는 치명적 안티 패턴입니다.
- **해결책 권장**: `aioconsole.ainput`을 사용하거나, `asyncio.to_thread(input, ...)` 형태로 래핑하여 이벤트 루프 블로킹을 우회해야 합니다.

### 🟠 RISK-01: Stage 3 Entity Registry 캐시 무효화 불발 위험 (Cache Stale Risk)
- **발생 위치**: `modules/core/stage3_orchestrator.py` 내 `_get_entity_registry`
- **증거 코드**: 
  - L338: `if self._entity_cache_arc_idx != arc_idx:` 일 때만 상태를 추출.
- **문제점**: 이 메서드는 O(N)의 무거운 누적 상태 추출을 피하고자 `self._cached_entity_registry`에 상태를 캐싱합니다. 하지만 동일한 `arc_idx`를 가진 Arc에 대해 수동 개입/패치가 이뤄질 경우 캐시를 강제 무효화하는 장치가 루프 밖에서는 불명확해 보입니다.
- **영향**: 이전 단계에서 엔티티 설정을 조정하고 다시 Stage 3로 들어올 때, 메모리 상에 `_entity_cache_arc_idx`가 유지되고 있다면 낡은(Stale) 엔티티 정보를 사용하여 설계도를 만들 가능성이 존재합니다.

### 🟡 RISK-02: Stage 0/1 직접 입력 인터페이스 의존도
- **발생 위치**: `modules/core/stage01_helpers.py`
- **문제점**: 모듈 여러 곳에서 콘솔 `input()`을 통한 분기 선택이나 Y/N 옵션 결정을 수행합니다 (L90, L104, L115 등). `ui_service.py`와 같은 추상화된 UI 계층이나 `get_int_input`을 거치지 않는 곳이 존재합니다.
- **영향**: 향후 GUI로의 마이그레이션이나 완전 자동화(Headless) 런타임 환경으로 전환할 때, 곳곳에 산재한 원시 `input()` 코드들이 전환을 가로막는 병목이 됩니다.

## 4) Codex 리포트 결과와의 비교 및 결론
- Codex가 발견한 `입력 범위 역전(BUG-01, BUG-02)`에 전적으로 동의하며, API 계약 위반(UI Service) 측면에 집중한 좋은 통찰입니다.
- **Antigravity 추가 결론**: Antigravity의 시선에서는 제어 흐름(Control Flow)과 동시성(Concurrency) 측면의 결함을 찾아냈습니다. 특히 **Stage 2 분기에서의 Event Loop 블로킹(Antigravity BUG-01)**은 시스템 확장성과 안정성 면에서 치명적이므로, UI 입력 인터페이스를 비동기 호환 구조(`to_thread`)나 추상화 계층으로 완전히 Refactoring 하는 작업을 최우선으로 고려해야 합니다.
