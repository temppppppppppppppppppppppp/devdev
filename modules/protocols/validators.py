"""
[B-3] Validator Protocol — 6-Tier 검증 파이프라인 계약.

TierValidator: Tier 1~3 + PreLLM 공통 시그니처 (manuscript + validation_context)
EpisodeAwareValidator: 에피소드 인식 검증자 (current_ep 추가)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TierValidator(Protocol):
    """6-Tier 검증 파이프라인 참여자.

    적합: BlockingValidator, ConsistencyValidator, ScoringValidator,
          AdvisoryValidator, PreLLMValidator
    """

    def validate(self, manuscript: str, validation_context: dict) -> dict: ...


@runtime_checkable
class EpisodeAwareValidator(Protocol):
    """에피소드 인식 검증자 (current_ep 필요).

    적합: ContinuityValidator
    """

    def validate(
        self,
        current_ep: int,
        manuscript: str,
        validation_context: dict,
        **kwargs: object,
    ) -> dict: ...
