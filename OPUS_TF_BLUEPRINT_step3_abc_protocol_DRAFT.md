# Step 3. ABC/Protocol 인터페이스 — 참고 청사진 (DRAFT)

> **상태**: 참고용 사전 조사 — Step 2 (Pydantic) 구현 후 확정 예정
> **위험도**: RISKY — 에이전트 21개 전체에 영향
> **전제**: Step 2 완료 후 `ArcModel`, `BlueprintModel` 등 사용 가능

---

## 1. 현재 상태 (문제)

### BaseAgent (1210줄)
- **순수 인프라만 제공**: `ask()`, `_extract_json_robust()`, 폴백 체인, API 키 순환
- **도메인 추상 메서드: 0개**
- 하위 클래스 **21개**가 각자 다른 시그니처로 마음대로 메서드 정의
- 공통 계약(Contract)이 없어 IDE/정적 분석 불가

### 에이전트 목록 (21개, BaseAgent 상속)

| # | 에이전트 | 파일 | 줄수 | 역할 |
|---|---------|------|:---:|------|
| 1 | `Analyst` | `analyst.py` | 1477 | Arc 설계 (레거시 폴백) |
| 2 | `FourPhaseArcGenerator` | `four_phase_arc_generator.py` | 511 | Arc 파이프라인 (주력) |
| 3 | `ArcEnsembleGenerator` | `arc_ensemble.py` | ~600 | Arc 앙상블 생성 |
| 4 | `StateLockedArcGenerator` | `state_locked_arc_generator.py` | ~300 | 상태 고정 Arc 생성 |
| 5 | `ThreePhaseBlueprintGenerator` | `three_phase_blueprint_generator.py` | 302 | Blueprint 파이프라인 |
| 6 | `BlueprintEnsembleGenerator` | `blueprint_ensemble.py` | ~700 | Blueprint 앙상블 생성 |
| 7 | `ChiefWriter` | `chief_writer.py` | 2130 | 원고 앙상블 생성 (주력) |
| 8 | `Writer` | `writer.py` | 501 | 원고 폴백 (냉동인간) |
| 9 | `Weaver` | `weaver.py` | 145 | 욕망 드라이브 설계 |
| 10 | `BlockEnricher` | `block_enricher.py` | 862 | Treatment 블록 농축 |
| 11 | `Director` | `director.py` | 266 | 품질 검증 총괄 (Facade) |
| 12 | `UnifiedArcValidator` | `unified_arc_validator.py` | ~400 | Arc 통합 검증 |
| 13 | `ConsensusValidator` | `consensus_validator.py` | ~300 | 3-LLM 합의 검증 |
| 14 | `ContinuityInspector` | `continuity_inspector.py` | ~200 | 연속성 검사 |
| 15 | `PreflightChecker` | `preflight_checker.py` | ~300 | 사전 분석 |
| 16 | `Critic` | `critic.py` | 709 | 적대적 비평 |
| 17 | `ArcCritic` | `arc_critic.py` | ~300 | Arc 비평 |
| 18 | `ArcCorrector` | `arc_corrector.py` | ~200 | Arc 자동 수정 |
| 19 | `Manager` | `manager.py` | 166 | 에피소드 정산 |
| 20 | `StateExtractor` | `state_extractor.py` | ~300 | 누적 상태 추출 |
| 21 | `Director` (response_schemas) | `response_schemas.py` L629 | ~300 | ⚠️ 중복 정의! |

### 비-BaseAgent 상태 관리자 (별개 계층)

| 클래스 | 파일 | 비고 |
|--------|------|------|
| `StateTracker` | `state_tracker.py` (1356줄) | Facade: NPC/Financial/Plots 서브모듈 위임 |
| `StateTrackerNPC` | `state_tracker_npc.py` | NPC 레지스트리 관리 |
| `StateTrackerPlots` | `state_tracker_plots.py` | 플롯 추적 |
| `StateTrackerFinancial` | `state_tracker_financial.py` | 재무 이벤트 |

---

## 2. 역할 패턴 분류

### 2-A. 생성자 (Generator)

**공통 시그니처 패턴**: `generate(...) → (결과_dict, pipeline_result_dict)`

| 에이전트 | 메서드 | 입력 패턴 | 출력 패턴 |
|---------|--------|----------|----------|
| `FourPhaseArcGenerator` | `generate()` | `arc_no, ep_start, curr_block, prev_arcs, ...` | `(Optional[dict], dict)` |
| `ThreePhaseBlueprintGenerator` | `generate()` | `ep_num, arc_data, prev_blueprint, ...` | `(Optional[dict], dict)` |
| `ChiefWriter` | `generate_ensemble()` | `ep_num, blueprint, prev_manuscript, ...` | `list[dict]` |
| `ArcEnsembleGenerator` | `generate_ensemble()` | `arc_no, ep_start, ...` | `(dict, list[dict])` |
| `BlueprintEnsembleGenerator` | `generate_ensemble()` | `ep_num, arc_data, ...` | `(dict, list[dict])` |
| `Writer` | `write_v20_manuscript()` | `ep_num, breakdown_doc, ...` | `str` |
| `Weaver` | `generate_arc_drive()` | `current_arc_dna, lack_report, ...` | `dict` |
| `BlockEnricher` | `enrich_block()` / `enrich_all_blocks()` | `block, reference, ...` | `dict` / `dict` |
| `Manager` | `update_state_and_lore_v20()` | `ep_num, manuscript, ...` | `dict` |

> [!WARNING]
> 반환 타입이 에이전트마다 완전히 다름 — `(Optional[dict], dict)`, `list[dict]`, `str`, `dict` 등 혼재.
> Protocol 설계 시 반환 타입을 통일할지 vs 역할별 별도 Protocol로 분리할지 결정 필요.

### 2-B. 검증자 (Validator)

**공통 시그니처 패턴**: `validate/audit(...) → (verdict: str, result: dict)`

| 에이전트 | 메서드 | PASS/REJECT 패턴 |
|---------|--------|:---:|
| `Director` | `audit_manuscript()`, `audit_strategic_plan()` | ✅ |
| `UnifiedArcValidator` | `validate()` | ✅ |
| `ConsensusValidator` | `validate_with_consensus()` | ✅ |
| `ContinuityInspector` | (연속성 검사) | ✅ |
| `PreflightChecker` | `analyze()` | ⚠️ PASS/REJECT 아닌 분석 결과 |
| `Critic` | `critique_manuscript()` / `deep_review()` | ⚠️ 점수 기반 |
| `ArcCritic` | (Arc 비평) | ⚠️ |
| `ArcCorrector` | (Arc 수정) | ⚠️ 수정 결과 반환 |

### 2-C. 분석자 (Analyzer)

| 에이전트 | 메서드 | 비고 |
|---------|--------|------|
| `StateExtractor` | `extract_cumulative_state()` | 상태 추출 전용 |
| `Analyst` | `get_lack_report()`, `analyze_context()` | 순수 분석 (Python) |
| `PreflightChecker` | `analyze()` | 사전 분석 |

---

## 3. Protocol 설계안 (초안)

### 3-A. 후보 Protocol 구조

```python
from typing import Protocol, runtime_checkable, Optional

# ──────────────────────────────────────────
# Protocol 1: 파이프라인 생성자
# ──────────────────────────────────────────
@runtime_checkable
class PipelineGenerator(Protocol):
    """Stage 2/3 파이프라인 (FourPhase, ThreePhase)"""
    def generate(self, **kwargs) -> tuple[Optional[dict], dict]:
        """(결과, pipeline_result) 반환"""
        ...

# ──────────────────────────────────────────
# Protocol 2: 앙상블 생성자
# ──────────────────────────────────────────
@runtime_checkable
class EnsembleGenerator(Protocol):
    """앙상블 후보 생성 (ArcEnsemble, BlueprintEnsemble, ChiefWriter)"""
    def generate_ensemble(self, **kwargs) -> tuple[dict, list[dict]]:
        """(best, all_candidates) 반환"""
        ...

# ──────────────────────────────────────────
# Protocol 3: 검증자
# ──────────────────────────────────────────
@runtime_checkable
class ArtifactValidator(Protocol):
    """PASS/REJECT 판정 (Director, UnifiedArcValidator, ConsensusValidator)"""
    def validate(self, **kwargs) -> tuple[str, dict]:
        """(verdict, result) 반환"""
        ...

# ──────────────────────────────────────────
# Protocol 4: 비평자
# ──────────────────────────────────────────
@runtime_checkable
class ArtifactCritic(Protocol):
    """점수 기반 비평 (Critic, ArcCritic)"""
    def critique(self, content: str, **kwargs) -> dict:
        """{'score': int, 'issues': list, 'recommendations': list}"""
        ...
```

> [!IMPORTANT]
> **Step 2 의존**: 위 `dict` 반환 타입들이 Step 2의 `ArcModel`, `BlueprintModel`, `ManuscriptCandidate` 등으로 교체될 수 있음.
> Step 2 완료 후 Protocol 시그니처를 확정해야 함.

### 3-B. ABC 전환 가능 영역 (BaseAgent 분할)

현재 `BaseAgent` (1210줄)을 분할:

```
BaseAgent (현재 1210줄, 인프라 전체)
    ├── LLMInfra (ABC)         → ask(), _extract_json_robust(), 폴백, 키순환
    ├── CachingMixin           → 컨텍스트 캐시 관리
    └── MetricsMixin           → 비용 추적, 성능 측정
```

> [!WARNING]
> `BaseAgent`를 분할하면 **21개 에이전트 + response_schemas.py의 Director** 모두 import가 변경됨.
> 기능적으로 동작은 동일하지만 위험이 높음.

---

## 4. Director 위임 패턴 (이미 진행 중)

Director는 이미 Facade 패턴으로 분해됨:

```
Director (266줄, Facade)
    ├── DirectorCachingManager
    ├── DirectorGradingSystem
    ├── DirectorEnsembleSelector
    ├── DirectorContinuityValidator
    ├── DirectorQualityAuditor
    ├── DirectorFormatter
    └── director_prompts.py
```

이 패턴이 ABC/Protocol 도입의 **모범 사례**. 다른 대형 에이전트(ChiefWriter 2130줄, Analyst 1477줄)도 유사하게 분해 가능.

---

## 5. 주요 발견 사항

### 5-1. `Director` 중복 정의 ⚠️
- `modules/domain/agents/director.py` L17: `class Director(BaseAgent)`
- `modules/core/response_schemas.py` L629: `class Director(BaseAgent)`
- **동일 이름, 다른 클래스** — `main_a.py`에서 어느 것을 import하는지 확인 필요

### 5-2. `StateTracker`는 BaseAgent 아님
- `StateTracker`는 `BaseAgent`를 상속하지 않음 (독립 클래스)
- Facade 패턴으로 3개 서브모듈 위임 (NPC/Financial/Plots)
- Protocol 도입 시 별개 계층으로 설계

### 5-3. `Writer`는 냉동인간
- `ChiefWriter` 3회 실패 시에만 호출되는 최후 폴백
- `ChiefWriter`와 공통 인터페이스(`ManuscriptWriter` Protocol) 추출 가능

### 5-4. `kwargs` 지옥
- 에이전트 메서드의 파라미터가 10~20개 — Protocol 시그니처 정의 어려움
- 해결: `**kwargs`로 Protocol 정의 + docstring 명세 vs Config 객체 도입

---

## 6. Step 2와의 관계

| Step 2 산출물 | Step 3에서 사용하는 곳 |
|--------------|---------------------|
| `ArcModel` | `PipelineGenerator.generate()` 반환 타입 |
| `BlueprintModel` | `PipelineGenerator.generate()` 반환 타입 |
| `ManuscriptCandidate` | `EnsembleGenerator.generate_ensemble()` 반환 타입 |
| `NpcRegistryEntry` | `StateTracker` Protocol 필드 타입 |

→ **Step 2가 구현되지 않으면 Protocol의 타입힌트가 `dict`으로 남아 의미 반감**

---

## 7. 구현 순서 (안)

Step 2 완료 후:

1. **Phase A**: Protocol 정의 (`modules/protocols/`)
   - `PipelineGenerator`, `EnsembleGenerator`, `ArtifactValidator`, `ArtifactCritic`
   - 반환 타입에 Pydantic 모델 사용

2. **Phase B**: BaseAgent 분할
   - `LLMInfra` + Mixin 분리
   - 21개 에이전트 import 수정

3. **Phase C**: 대형 에이전트 분해
   - `ChiefWriter` → Facade 패턴 (Director처럼)
   - `Analyst` → 역할별 분리

4. **Phase D**: 검증
   - 기존 테스트 통과 확인
   - 타입 체커(`mypy`) 돌려서 Protocol 준수 확인

---

## 8. 지금은 확인 불가한 사항

| 항목 | 이유 | 대기 |
|------|------|------|
| Protocol 반환 타입 확정 | Step 2 모델 구현 필요 | Step 2 후 |
| BaseAgent 분할 범위 | 1210줄 중 어디까지 인프라인지 정밀 분류 필요 | Step 2 후 |
| `kwargs` 처리 전략 | Config 객체 도입 여부 결정 필요 | Step 2 후 |
| `response_schemas.py` Director 중복 해결 | Step 7 (God Object 분해) 범위 | Step 7 |
