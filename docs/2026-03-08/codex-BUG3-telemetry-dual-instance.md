# Codex — BUG-3 llm_calls Telemetry 이중 인스턴스 근절

> **일시**: 2026-03-08
> **프로젝트**: 전체 파이프라인 (Stage 2/3/4)
> **범위**: `llm_calls` 테이블 `stage`/`ep_num` NULL 근본 원인 전수 조사 + 패치
> **기준**: 3,648 passed

---

## 1. 문제 정의

`base_agent.py`의 `_resolve_stage_number()`/`_resolve_episode_number()`가 `_current_stage`/`_current_ep_num` 속성을 참조하여 `llm_calls` DB 테이블에 stage/ep_num을 기록. 이 속성은 각 Stage 오케스트레이터의 `_set_agent_telemetry_context()`에서 `ctx.agents` dict 순회로 주입.

**근본 원인**: 일부 에이전트(`FourPhaseArcGenerator`, `ThreePhaseBlueprintGenerator`)가 `__init__`에서 서브 에이전트를 **별도 인스턴스로 재생성**. `ctx.agents` dict에 등록된 인스턴스(A)와 실제 LLM 호출을 수행하는 내부 인스턴스(B)가 별개 → setattr가 A에만 적용, B는 `_current_stage=None` → llm_calls에 NULL 기록.

---

## 2. 이중 인스턴스 전수 맵

### 2.1 FourPhaseArcGenerator (Stage 2)

| 서브 에이전트 | 속성명 | BaseAgent 상속 | LLM 호출 | 이전 상태 |
|--------------|--------|---------------|----------|----------|
| `PreflightChecker` | `self.preflight` | O | O | NULL (21건 중 6건) |
| `ArcEnsembleGenerator` | `self.ensemble` | O | O | NULL (21건) |
| `UnifiedArcValidator` | `self.validator` | O | O | NULL (1건) |

### 2.2 ThreePhaseBlueprintGenerator (Stage 3)

| 서브 에이전트 | 속성명 | BaseAgent 상속 | LLM 호출 | 이전 상태 |
|--------------|--------|---------------|----------|----------|
| `BlueprintEnsembleGenerator` | `self.ensemble` | O | O | NULL |
| `UnifiedBlueprintValidator` | `self.validator` | **X** | X (Python-only) | N/A |
| `BlueprintConstraintCompiler` | `self.constraint_compiler` | **X** | X (Python-only) | N/A |

### 2.3 이중 인스턴스 해당 없음 (확인 완료)

| 에이전트 | 서브 컴포넌트 | 사유 |
|----------|-------------|------|
| `Director` | _caching, _grading, _ensemble, _continuity, _auditor | BaseAgent 미상속 (헬퍼 클래스) |
| `ContinuityInspector` | _arc, _blueprint, _manuscript, _tracker | BaseAgent 미상속 (헬퍼 클래스) |
| `ChiefWriter` | context_builder, quality_gate | BaseAgent 미상속 (lazy-init 헬퍼) |
| Advisory 7종 | — | BaseAgent 미상속 (callback 기반) |
| `WritingDirectiveGenerator` | — | BaseAgent 미상속 (유틸리티) |

---

## 3. 패치 내역

### PATCH-1: Stage 2 Orchestrator (P2)

**파일**: `modules/core/stage2_orchestrator.py` L82-116

**변경**: `_set_agent_telemetry_context()`에서 `four_phase` 에이전트의 서브 에이전트 3개를 순회 대상에 추가.

```python
# 서브 에이전트 포함 전체 순회 (four_phase 내부 인스턴스는 agents dict와 별개)
_all_agents = list(agents.values())
_four_phase = agents.get("four_phase")
if _four_phase is not None:
    for _sub_name in ("preflight", "ensemble", "validator"):
        _sub = getattr(_four_phase, _sub_name, None)
        if _sub is not None:
            _all_agents.append(_sub)
```

### PATCH-2: Stage 3 Orchestrator (P2)

**파일**: `modules/core/stage3_orchestrator.py` L54-78

**변경**: `_set_agent_telemetry_context()`에서 `three_phase_bp` 에이전트의 서브 에이전트 1개를 순회 대상에 추가.

```python
# 서브 에이전트 포함 전체 순회
_all_agents = list(agents.values())
_three_phase_bp = agents.get("three_phase_bp")
if _three_phase_bp is not None:
    _sub = getattr(_three_phase_bp, "ensemble", None)
    if _sub is not None:
        _all_agents.append(_sub)
```

### Stage 4: 패치 불필요

- `extra_agents` 파라미터로 ChiefWriter 명시 주입 구조 이미 완비
- Stage 4에서 `three_phase_bp` 참조는 `ctx.agents` dict 공유 인스턴스 사용 (Blueprint InPlace 패치 용도) → 이중 인스턴스 아님

---

## 4. 비이슈 확인 (정상)

| 항목 | 결과 | 방법 |
|------|------|------|
| Advisory 7종 BaseAgent 미상속 | PASS | 클래스 선언 직접 확인 (7파일) |
| WritingDirectiveGenerator BaseAgent 미상속 | PASS | 클래스 선언 직접 확인 |
| UnifiedBlueprintValidator BaseAgent 미상속 | PASS | `class UnifiedBlueprintValidator:` (L42) |
| UnifiedArcValidator BaseAgent 상속 | PASS | `class UnifiedArcValidator(BaseAgent):` (L108) |
| Director 서브매니저 BaseAgent 미상속 | PASS | 5개 모두 헬퍼 클래스 |
| ContinuityInspector 서브검증기 BaseAgent 미상속 | PASS | 4개 모두 헬퍼 클래스 |
| Stage 4 `three_phase_bp` 참조 | PASS | agents dict 공유 인스턴스 (L1017, L1161) |
| `modules/domain/agents/` 추가 이중 인스턴스 | PASS | BaseAgent 상속 21개 클래스 전수 확인, four_phase/three_phase_bp 외 0건 |

---

## 5. 확신도 평가

| 조사 항목 | 결과 | 방법 |
|-----------|------|------|
| 이중 인스턴스 전수 | **확인** | BaseAgent 상속 21개 클래스 __init__ 전수 검색 |
| 속성명 일치 | **확인** | four_phase_arc_generator.py L302-304 / three_phase_blueprint_generator.py L44-47 직접 대조 |
| BaseAgent 비상속 제외 대상 | **확인** | 12개 클래스(Advisory 7+Director 서브 5) 선언 직접 확인 |
| Stage 4 무영향 | **확인** | stage4_orchestrator.py 전문 검색, 이중 인스턴스 없음 |
| 패치 후 테스트 | **확인** | 3,648 passed, 0 failures |

**종합 확신도: 99%** — BaseAgent 상속 21개 클래스 전수 확인, 속성명 1:1 대조, 12개 비대상 클래스 제외 근거 확보, Stage 4 무영향 확인 완료.

---

## 6. 감리 이력 (3회)

| 회차 | 역할 | 판정 | 주요 발견 |
|------|------|------|-----------|
| 1 | 이중 인스턴스 전수 스캔 | 전량 **CORRECT** | FourPhaseArcGenerator 3건 + ThreePhaseBlueprintGenerator 1건 확인, 추가 이중 인스턴스 0건 |
| 2 | Stage 3/4 telemetry 갭 | 전량 **CORRECT** | Stage 3 `three_phase_bp.ensemble` 누락 발견 → PATCH-2로 해소. Stage 4 `extra_agents` 구조 적절 |
| 3 | 패치 정확성 + 누락 검증 | 8/8 **CORRECT** | 속성명 일치, BaseAgent 상속/비상속 전량 확인, Stage 4 `three_phase_bp` 참조는 공유 인스턴스(이중 아님) |

**감리 결과 반영 완료**: PATCH-2(Stage 3) 추가, 문서 항목 8 명확화(재인스턴스화 vs 공유 참조 구분).

---

## 7. 이슈 분류 종합

| 등급 | ID | 내용 | 위치 | 상태 |
|------|-----|------|------|------|
| **P2** | **PATCH-1** | Stage 2 `four_phase` 서브 에이전트 3개 telemetry 누락 | `stage2_orchestrator.py` L82-116 | **PATCHED** |
| **P2** | **PATCH-2** | Stage 3 `three_phase_bp.ensemble` telemetry 누락 | `stage3_orchestrator.py` L54-78 | **PATCHED** |
| **INFO** | — | Stage 4 `extra_agents` 구조 적절, 패치 불필요 | `stage4_orchestrator.py` L232-261 | **OK** |
| **INFO** | — | Advisory 7종 + Director/CI 서브 컴포넌트 = telemetry 대상 외 | 각 파일 | **OK** |

---

## 8. 기존 BUG-3 이력 통합

| 단계 | 패치 | 해소 건수 |
|------|------|----------|
| 1차 (이전 세션) | Stage 2/3/4 오케스트레이터에 `_set_agent_telemetry_context()` 신설 | 48/76건 |
| 2차 (본 코덱스) | Stage 2 `four_phase` 서브 에이전트 3개 추가 | +28건 (잔여 전량) |
| 2차 (본 코덱스) | Stage 3 `three_phase_bp.ensemble` 추가 | Stage 3 미래 NULL 방지 |
| **합계** | | **76/76건 → 0건 NULL** |
