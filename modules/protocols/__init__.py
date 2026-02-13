"""
[Step 3] Agent Protocol 인터페이스

구조적 서브타이핑(structural subtyping) 기반 — 기존 에이전트 코드 수정 없이 적용.
runtime_checkable로 isinstance() 런타임 검증 가능.
"""

from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    Corrector,
    EnsembleGenerator,
    PipelineGenerator,
)

__all__ = [
    "PipelineGenerator",
    "EnsembleGenerator",
    "ArtifactValidator",
    "ArtifactCritic",
    "Corrector",
]
