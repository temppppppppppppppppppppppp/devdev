# [S-T2] 교차 스테이지 루트코즈 심층 감사 보고서

> 작성일: 2026-03-13
> 터미널: Terminal 2
> 범위: Stage 0→2, Stage 2→3, Stage 3→4 handoff / DI context write-back / 기존 미해결 P0·P1 7건 재판정
> 방법: static / read-only / root-cause revalidation / cross-report ledger reconciliation

---

## Executive Summary

이번 심층 감사에서 1차·2차 문서가 "미해결"로 남겨둔 상위 위험군 7건을 현재 트리 기준으로 다시 대조했다. 결과는 다음과 같다.

- **루트코즈 잔존 1건**: `T2-001 plot_roadmap`
- **테스트 갭으로만 잔존 2건**: `T3-003`, `T3-004`
- **현행 코드에서 해소 4건**: `T3-029`, `T4-P1-03`, `T4-P1-04`, `T5-WS-016`

즉, 심층 감사 시점의 핵심은 "미해결 상위위험이 7건 전부 살아 있다"가 아니라, **실제 코드 기준 열린 루트코즈는 크게 줄었고, 남은 핵심은 Stage 0 handoff 구조 하나로 수렴한다**는 점이다.

---

## 확정 발견사항

### [S-T2-001] P2 | `plot_roadmap` handoff는 여전히 생성 경계가 아니라 저장 경계에서만 보장된다

- 파일:
  - `modules/core/stage0/__init__.py:369-404`
  - `modules/core/stage01_helpers.py:566-592`
  - `modules/core/stage2_orchestrator.py:156`
  - `tests/test_stage01_helpers.py:364-397`
- 현상:
  - `StageZeroManager.generate_from_concept()`가 직접 반환하는 Bible은 `plot_roadmap`를 내장하지 않는다.
  - `Stage01Helpers._s0_save_results()`가 save 직전 `_ensure_plot_roadmap()`로 보정한다.
  - Stage 2는 이 필드를 입력 계약으로 직접 사용한다.
- 영향:
  - Stage 0→Stage 2 handoff 계약이 생성기 레이어에서 보장되지 않는다.
  - 정식 저장 흐름은 회귀 테스트로 커버되지만, handoff 자체가 여전히 "save hook dependent contract"다.
- 판정:
  - `T2-001`은 **완전 해소 아님**.
  - 현재 상태는 `resolved`가 아니라 `root-cause remains, caller patch present`다.

---

## 미해결 7건 재판정

| 기존 ID | 원래 성격 | 현재 코드 판정 | 근거 |
|--------|----------|---------------|------|
| `T2-001` | Stage 0→2 `plot_roadmap` 누락 | **root-cause remains** | 생성기 반환엔 없고, `Stage01Helpers` save patch로만 보정 |
| `T3-003` | Blueprint→Manuscript handoff 통합 테스트 부재 | **open as test gap** | 실코드 계약보다 테스트 부재 문제로 수렴 |
| `T3-004` | Advisory 병렬 실행 테스트 부재 | **open as test gap** | `ThreadPoolExecutor` 실경로 직접 테스트 여전히 부족 |
| `T3-029` | continuity pin이 Director PASS 무효화 | **resolved in current code** | 현재는 unresolved를 audit/log로만 남기고 저장 경로 계속 진행 |
| `T4-P1-03` | 단일 Blueprint 후보 Python-only PASS | **resolved in current code** | `director_ensemble.py`가 단일 후보 자동 PASS를 금지하고 REJECT |
| `T4-P1-04` | adaptive decision이 Director PASS를 REJECT로 뒤집음 | **resolved in current code** | 현재는 `CONDITIONAL_PASS`로 하향, 즉시 REJECT 아님 |
| `T5-WS-016` | FactLedger deceased NPC guard 부재 | **resolved in current code** | `npc_injuries/movements/personality/relationship` 섹션에 guard 존재 |

---

## 현재 handoff 맵

### 1. Stage 0 → Stage 2

| 상류 | 하류 | 핵심 필드 | 현재 상태 |
|------|------|----------|----------|
| `StageZeroManager.generate_from_concept()` | `stage2_orchestrator` | `plot_roadmap`, `protagonist_config`, 장르/프리셋 | `plot_roadmap`만 생성기 직접 보장 실패 |

### 2. Stage 2 → Stage 3

| 상류 | 하류 | 핵심 필드 | 현재 상태 |
|------|------|----------|----------|
| `stage2_finalizer` / arcs anchor | `stage3_orchestrator` | `arc_no`, `ep_start`, `ep_end`, `tactical_doc`, `episode_details` | 현행 코드에서 구조적 break 근거 미발견 |

### 3. Stage 3 → Stage 4

| 상류 | 하류 | 핵심 필드 | 현재 상태 |
|------|------|----------|----------|
| `stage3_orchestrator.save_episode_blueprint()` | `stage4_context_builder` / Stage 4 Orchestrator | blueprint JSON, prev text, continuity metadata | 테스트 갭은 남지만 코드상 즉시 불일치 근거는 약화 |

### 4. Stage 4 → DB

| 상류 | 하류 | 핵심 필드 | 현재 상태 |
|------|------|----------|----------|
| `stage4_post_processor` | `DBManager` / sidecars | manuscript, state changes, quality review, logs | write path 자체는 계속 살아 있음 |

### 5. Stage 4 → 다음 에피소드 입력

| 상류 | 하류 | 핵심 필드 | 현재 상태 |
|------|------|----------|----------|
| FactLedger / WorldState / quality metrics | Stage 2 / Stage 3 / Stage 4 retrieval | 인물 상태, relation, warnings, score trend | 현행 코드에서 상위 P1 4건은 상당수 해소 |

---

## DI write-back 상태

| Context | 생성 방식 | 현재 판정 |
|---------|-----------|----------|
| `Stage2Context.from_app()` | app 속성/콜백 직접 포획 + 일부 weakref sync 콜백 | reference-based write-back 유지 |
| `Stage3Context.from_app()` | app 속성/콜백 직접 포획 | callable guard에 많이 의존 |
| `Stage4Context.from_app()` | app 속성/콜백 직접 포획 | quality/fact/state 모듈 직접 배선 유지 |

해석:

- 세 컨텍스트 모두 "명시적 schema handoff"보다 "app 속성 snapshot + optional callback" 패턴에 가깝다.
- 이 구조 때문에 컨텍스트 누락 시 즉시 크래시보다 `callable(...)` guard를 통한 조용한 기능 축소가 더 흔하다.
- 다만 이번 심층 감사에서는 이를 신규 P1/P2로 올릴 정도의 실재 오동작 증거까지는 확보하지 못했다.

---

## 교차 코드 검증 메모

### 해소 확인

- `modules/core/stage3_orchestrator.py:1470-1503`
  - continuity pin unresolved가 `audit_event`와 `_continuity_pin_unresolved`에 남을 뿐, 곧바로 DB 저장 차단으로 이어지지 않는다.
- `modules/domain/agents/director_ensemble.py:471-478`
  - 단일 후보 자동 PASS를 금지한다.
- `modules/domain/agents/director_grading.py:565-579`
  - adaptive decision은 PASS 계열을 `CONDITIONAL_PASS`로 완화한다.
- `modules/validation/validation_orchestrator.py:468-477`, `660-667`
  - Consistency/Retrospective는 advisory + penalty 경로로 수렴한다.
- `modules/core/fact_ledger.py:210-260`
  - deceased NPC guard가 주요 4개 보조 섹션에 존재한다.

### 잔존 확인

- `modules/core/stage0/__init__.py:369-404`
  - `generate_from_concept()` 산출물에는 `plot_roadmap` 직접 보장이 없다.
- `modules/core/stage01_helpers.py:566-592`
  - save-time patch가 handoff 계약을 대신한다.

---

## 3PASS 감리 로그

### PASS 1 — 추적 대상 7건 재열거

- 1차/2차 문서에서 "미해결"로 남은 상위위험 7건을 다시 목록화

### PASS 2 — 현재 코드 대조

- 4건은 현재 트리에서 해소 확인
- 2건은 테스트 갭으로만 존속
- 1건은 생성기 루트코즈 존속

### PASS 3 — 최종 판정

- `PASS1 7건 → PASS2 상태 재분류 → 최종 open root-cause 1건 + test gap 2건 + resolved 4건`

---

## 결론

교차 스테이지 심층 감사의 핵심 결론은 단순하다. 현재 코드 기준으로 상위위험 대부분은 이미 닫혔고, **실제 루트코즈로 남은 것은 `plot_roadmap`가 생성기 산출물에 내장되지 않는 구조**다.

따라서 후속 조치 우선순위는 다음과 같다.

1. `plot_roadmap`를 save hook이 아니라 Stage 0 생성 결과 자체의 계약으로 승격
2. `T3-003`, `T3-004`는 코드 수정보다 handoff/parallel path 테스트 보강으로 닫기
3. 기존 문서의 "미해결 7건" 서술은 현재 트리 기준 상태표로 갱신
