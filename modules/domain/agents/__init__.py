# modules/domain/agents/__init__.py
"""
Agent 모듈 패키지

Stage 4 V60.80 Chief Writer 주권주의 아키텍처 포함
"""

# [V65] Architect 삭제 (완전 레거시 — ThreePhaseBlueprintGenerator로 대체됨)
from .analyst import Analyst
from .base_agent import BaseAgent
from .chief_writer import ChiefWriter
from .director import Director
from .manuscript_validator import ManuscriptValidator
from .writer import Writer

__all__ = [
    "BaseAgent",
    "Writer",
    "Director",
    # [V65] 'Architect' 삭제
    "Analyst",
    "ChiefWriter",
    "ManuscriptValidator",
]
