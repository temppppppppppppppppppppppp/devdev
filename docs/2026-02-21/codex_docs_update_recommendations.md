# Codex Documentation Audit Report (Post Stage 0-4 Updates)

**작성일**: 2026-02-21
**목적**: 최근 진행된 Stage 0~4 아키텍처 개선(비동기 컨텍스트 안정화, 의존성 Lazy Init, Event Loop 블로킹 제거, 오류 복구 로직 강화 등) 사항이 기존에 작성된 `codex_*_plan.md` 기획안들과 충돌하거나 업데이트가 필요한 부분을 식별합니다.

---

## 1. `codex_canon_os_v2_plan.md` (Canon OS V2 기획안)
**분석 결과**: **수정 필요 (Minor)**
- **이슈 사항**: 
  - 최근 Stage 0/1 계층에서 `ui_service.py`와 같은 추상화 계층을 거치지 않는 직접적인 `input()` 블로킹 리스크가 식별되었습니다.
  - V2 기획안의 **"6. 검증/판단 파이프라인"** 및 **"10. 롤아웃"** 섹션에서, Director의 판단(`fix_text`, `accept_change`, `override_with_reason`)을 입력받거나 예외 상황 시 개입하는 인터페이스에 대한 명세가 부족합니다.
- **권장 업데이트**:
  - 사용자 개입이 필요한 모든 Canon 룰 위반 처리(Director Override 등)는 `aioconsole` 등 비동기 표준 입력 추상화 계층을 통하도록 명시하는 조항 추가 필요.

## 2. `codex_stage_canon_memory_plan.md` (Stage별 메모리 유지 플랜)
**분석 결과**: **수정 필요 (Major)**
- **이슈 사항**:
  - 기획안의 **"Runtime Flow"** 에서는 시작 시 스냅샷을 로드하고, Stage 4에서 커밋하는 구조를 명시합니다.
  - 하지만 최근 Stage 3 오디트에서 `_entity_cache_arc_idx`를 확인하여 낡은 캐시(Stale Cache)를 사용할 수 있는 위험(RISK-01)이 발견되었습니다.
- **권장 업데이트**:
  - **"Context Compaction Guard"** 조항에 "수동 개입/패치로 인해 Arc 데이터가 변경되었을 경우, 메모리 상의 Entity Registry 및 Cache를 즉각 강제 무효화(Invalidate)해야 한다"는 설계 원칙을 반드시 추가해야 함.

## 3. `codex_patch_retry_extension_plan.md` (패치 재시도 확장 플랜)
**분석 결과**: **수정 필요 (Critical)**
- **이슈 사항**:
  - 본 문서의 핵심은 실패 시 즉각 폴백 대신 최대 3회의 추가 패치를 시도하는 루프를 Stage 2/3/4에 넣는 것입니다.
  - 그러나 최근 오디트에서 **"Stage 2 분기에서의 Event Loop 블로킹(BUG-01)"**이 발견되었습니다. 패치 실패로 인한 사용자 개입이나 재시도 프롬프트 입력 시, 동기식 `input()`이 이 루프 안에서 돌게 되면 시스템이 완전히 프리징됩니다.
- **권장 업데이트**:
  - **"2.5 Stage 2 구조적 문제"** 및 **"3. Stage별 수정 전략"** 섹션에 경고문(`> [!CAUTION]`)을 추가하고, 패치 재시도 중 발생하는 모든 I/O 및 사용자 입력 대기는 `asyncio.to_thread` 또는 비동기 래퍼를 사용해야만 한다는 구조적 제약을 최우선으로 반영해야 함.

## 4. `codex_resume_replay_idempotency_sweep100_plan.md` (재개/재실행 멱등성 테스트 플랜)
**분석 결과**: **수정 필요 (Minor)**
- **이슈 사항**: 
  - 중단 후 재개(Resume) 시점을 검증하는 테스트입니다.
  - Lazy Init 구조(최근 개선됨)가 완전히 로드되기 전에 재개 시점이 물리면 객체 상실 오류가 날 수 있습니다.
- **권장 업데이트**:
  - **"Phase 2 (R11-R20): Stage별 재개 정확도"** 세부 항목에 "지연 초기화(Lazy Initialization) 객체들이 재개(Resume) 시점에도 누락 없이 정상적으로 메모리에 올라오는지 검증" 하는 항목을 추가할 것.

---

### 총평 (Executive Summary)
기존 Codex 문서들은 **"비동기 동시성(Concurrency)과 캐시 일관성(Cache Consistency)"**에 대한 최근의 안티그래비티 관점 발견 사항들이 전혀 반영되어 있지 않습니다. 

특히 패치 루프와 Canon 검증 파이프라인을 그대로 구현할 경우, 이벤트 루프 정지 버그나 구형 데이터 참조 버그가 그대로 전이될 위험이 높으므로, 각 문서의 설계 원칙 모듈에 본 리포트의 권장 사항을 즉각 패치해야 합니다.
