"""
[Step 3 + Phase 4A + B-3] Protocol 인터페이스

구조적 서브타이핑(structural subtyping) 기반 — 기존 코드 수정 없이 적용.
runtime_checkable로 isinstance() 런타임 검증 가능.

Step 3: Agent Protocol 5종
Phase 4A: Service Protocol 5종 + DB Repository Protocol 1종
B-3: Validator Protocol 2종
"""

from modules.protocols.agents import (
    ArtifactCritic,
    ArtifactValidator,
    ConstraintCompilerProtocol,
    Corrector,
    DraftValidator,
    EnsembleGenerator,
    PipelineGenerator,
    StateAggregator,
)
from modules.protocols.app_services import (
    AuditServiceProtocol,
    ConfigServiceProtocol,
    ProjectRepositoryProtocol,
    StateServiceProtocol,
    UIServiceProtocol,
)
from modules.protocols.db_repository import DBRepositoryProtocol
from modules.protocols.validators import EpisodeAwareValidator, TierValidator

__all__ = [
    # Step 3 — Agent Protocol
    "PipelineGenerator",
    "EnsembleGenerator",
    "ArtifactValidator",
    "ArtifactCritic",
    "Corrector",
    # B-2 — Protocol adapters
    "DraftValidator",
    "ConstraintCompilerProtocol",
    "StateAggregator",
    # B-3 — Validator Protocol
    "TierValidator",
    "EpisodeAwareValidator",
    # Phase 4A — Service Protocol
    "UIServiceProtocol",
    "AuditServiceProtocol",
    "ProjectRepositoryProtocol",
    "StateServiceProtocol",
    "ConfigServiceProtocol",
    # Phase 4A — DB Protocol
    "DBRepositoryProtocol",
]
