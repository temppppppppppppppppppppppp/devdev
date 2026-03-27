from __future__ import annotations

import json

from scripts.probe_claude_vertex_matrix import (
    build_model_candidates,
    build_region_candidates,
    classify_exception,
    extract_model_ids,
)


def test_extract_model_ids_dedupes_and_strips_prefix() -> None:
    payload = [
        {"name": "publishers/anthropic/models/claude-sonnet-4-6"},
        {"name": "publishers/anthropic/models/claude-haiku-4-5"},
        {"name": "publishers/anthropic/models/claude-sonnet-4-6"},
        {"name": "garbage"},
    ]
    assert extract_model_ids(payload) == ["claude-sonnet-4-6", "claude-haiku-4-5"]


def test_classify_exception_buckets_common_live_errors() -> None:
    assert classify_exception(RuntimeError("Your default credentials were not found.")) == "auth"
    assert classify_exception(RuntimeError("Error code: 429 - RESOURCE_EXHAUSTED")) == "rate_limit"
    assert classify_exception(RuntimeError("Error code: 404 - Publisher Model not found")) == "not_found_or_no_access"
    assert classify_exception(RuntimeError("Error code: 403 - Permission denied")) == "permission"
    assert classify_exception(RuntimeError("Error code: 400 - Something else")) == "other"


def test_build_candidates_prefers_explicit_then_env_then_listed() -> None:
    models = build_model_candidates(
        listed_models=["claude-sonnet-4-6", "claude-haiku-4-5"],
        env_model="claude-opus-4-6",
        explicit_models=["claude-sonnet-4"],
    )
    assert models[:4] == [
        "claude-sonnet-4",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    ]

    regions = build_region_candidates(
        env_region="us-east5",
        explicit_regions=["us-central1", "us-east5"],
    )
    assert regions[:3] == ["us-central1", "us-east5", "global"]
