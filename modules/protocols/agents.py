"""
[Step 3] Agent Protocol 정의

구조적 서브타이핑(structural subtyping) — 기존 에이전트가 Protocol 메서드를
이미 보유하면 코드 수정 없이 자동 적합.

설계 원칙:
- Protocol 메서드명은 기존 에이전트의 실제 메서드명과 정확히 일치
- **kwargs로 파라미터 다양성 흡수 (에이전트마다 10~25개 파라미터 상이)
- 반환 타입은 실제 코드에서 관찰된 패턴 기반

적합 에이전트 (코드 수정 없이 isinstance 통과):
┌─────────────────────┬───────────────────────────────────────────┐
│ Protocol            │ 적합 에이전트                              │
├─────────────────────┼───────────────────────────────────────────┤
│ PipelineGenerator   │ FourPhaseArcGenerator                     │
│                     │ ThreePhaseBlueprintGenerator              │
├─────────────────────┼───────────────────────────────────────────┤
│ EnsembleGenerator   │ ArcEnsembleGenerator                      │
│                     │ BlueprintEnsembleGenerator                │
├─────────────────────┼───────────────────────────────────────────┤
│ ArtifactValidator   │ UnifiedArcValidator                       │
├─────────────────────┼───────────────────────────────────────────┤
│ ArtifactCritic      │ ArcCritic                                 │
├─────────────────────┼───────────────────────────────────────────┤
│ Corrector           │ ArcCorrector                              │
└─────────────────────┴───────────────────────────────────────────┘

미적합 에이전트 (메서드명 불일치 — 향후 어댑터 필요):
- ChiefWriter: generate_ensemble() 반환 list[dict] (tuple 아님)
- ConsensusValidator: validate_with_consensus() (validate 아님)
- Critic: critique_manuscript() (critique 아님)
- Director: audit_manuscript/audit_strategic_plan (validate 아님)
- StateExtractor: extract_state/extract_cumulative_state (analyze 아님)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PipelineGenerator(Protocol):
    """Stage 2/3 파이프라인 생성자

    generate() → (결과_dict | None, pipeline_result_dict)

    적합:
    - FourPhaseArcGenerator.generate()
    - ThreePhaseBlueprintGenerator.generate()
    """

    def generate(self, **kwargs: object) -> tuple[dict | None, dict]: ...


@runtime_checkable
class EnsembleGenerator(Protocol):
    """앙상블 후보 생성자

    generate_ensemble() → (best_dict | None, all_candidates_list)

    적합:
    - ArcEnsembleGenerator.generate_ensemble()
    - BlueprintEnsembleGenerator.generate_ensemble()

    NOTE: ChiefWriter.generate_ensemble()는 list[dict]를 반환하므로 미적합.
    향후 어댑터로 래핑 시 적합 가능.
    """

    def generate_ensemble(self, **kwargs: object) -> tuple[dict | None, list[dict]]: ...


@runtime_checkable
class ArtifactValidator(Protocol):
    """PASS/REJECT 판정 검증자

    validate() → result_dict (verdict 키 포함)

    적합:
    - UnifiedArcValidator.validate()

    NOTE: ConsensusValidator는 validate_with_consensus() 사용 — 미적합.
    Director는 audit_manuscript() 사용 — 미적합.
    """

    def validate(self, **kwargs: object) -> dict: ...


@runtime_checkable
class ArtifactCritic(Protocol):
    """점수 기반 비평자

    critique() → result_dict (score/issues 키 포함)

    적합:
    - ArcCritic.critique()

    NOTE: Critic은 critique_manuscript() 사용 — 미적합.
    """

    def critique(self, **kwargs: object) -> dict: ...


@runtime_checkable
class Corrector(Protocol):
    """산출물 자동 수정자

    can_correct() → 수정 가능 여부 판정
    correct() → (수정된_dict | None, result_dict)

    적합:
    - ArcCorrector.can_correct() + correct()
    """

    def can_correct(self, **kwargs: object) -> tuple[bool, list[dict], list[dict]]: ...

    def correct(self, **kwargs: object) -> tuple[dict | None, dict]: ...
