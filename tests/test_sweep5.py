"""[Sweep5] Focused tests for logging/async hygiene changes."""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import re
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_warning_semantic_info_logs_removed_in_sample_files():
    """Warning-semantic logs should not remain at info level in key files."""
    sample_files = [
        "modules/core/stage2_preflight.py",
        "modules/domain/agents/chief_writer.py",
        "modules/validation/validation_orchestrator.py",
    ]
    pattern = re.compile(r"logging\.info\([^\n]*(?:⚠️|\[WARNING\]|경고)")

    for rel_path in sample_files:
        assert pattern.search(_read(rel_path)) is None, rel_path


def test_batch_validator_async_uses_running_loop(monkeypatch):
    """Async batch path should call asyncio.get_running_loop."""
    module_path = ROOT / "modules" / "validation" / "batch_validator.py"
    spec = importlib.util.spec_from_file_location("sweep5_batch_validator", module_path)
    bv = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(bv)

    called = {"value": False}
    original = bv.asyncio.get_running_loop

    def _wrapped_running_loop():
        called["value"] = True
        return original()

    monkeypatch.setattr(bv.asyncio, "get_running_loop", _wrapped_running_loop)

    orchestrator = MagicMock()
    orchestrator.validate.return_value = {"ok": True}

    validator = bv.BatchValidator(orchestrator, max_concurrent=1)
    manuscripts = [{"ep_num": 1, "manuscript": "test", "validation_context": {}}]

    results = asyncio.run(validator.validate_batch_async(manuscripts))

    assert called["value"] is True
    assert results[0]["success"] is True


def test_writer_prompt_justification_soft_fail_logs_warning(monkeypatch, caplog):
    """Justification guide load failure should be logged and remain non-blocking."""
    from modules.core import justification_patterns as jp
    from modules.core import writer_prompt_builders as wpb

    def _boom(*args, **kwargs):
        raise RuntimeError("guide failure")

    monkeypatch.setattr(jp, "get_justification_guide", _boom)

    with caplog.at_level(logging.WARNING):
        out = wpb.build_justification_guidance("reputation: 10", "wuxia")

    assert isinstance(out, str)
    assert "[Sweep5-D] justification guide load failed" in caplog.text


def test_writer_prompt_recent_events_soft_fail_logs_warning(caplog):
    """Recent-events extraction failure should log warning and not propagate."""
    from modules.core import writer_prompt_builders as wpb

    class BadDB:
        def load_state_log(self, ep_num):
            raise RuntimeError("db down")

    with caplog.at_level(logging.WARNING):
        out = wpb._extract_recent_events(BadDB(), current_ep=5, n_episodes=3)

    assert out == []
    assert "[Sweep5-D] recent events extraction failed" in caplog.text


def test_writer_prompt_npc_state_soft_fail_logs_warning(caplog):
    """NPC state extraction failure should log warning and not propagate."""
    from modules.core import writer_prompt_builders as wpb

    class BadBible:
        def get(self, *args, **kwargs):
            raise RuntimeError("bible read failure")

    with caplog.at_level(logging.WARNING):
        out = wpb._extract_npc_last_states(BadBible(), current_ep=5)

    assert out == {}
    assert "[Sweep5-D] npc last-state extraction failed" in caplog.text


def test_sweep5_observability_tags_present_in_target_files():
    """Sweep5-D log tags should exist in designated mutation-path files."""
    required = {
        "modules/core/project_manager.py": "[Sweep5-D] sync_status partial update failed",
        "modules/core/stage2_preflight.py": "[Sweep5-D] semantic plot indexing failed",
        "modules/core/stage2_orchestrator.py": "[Sweep5-D] state_extractor cache invalidation failed",
        "modules/core/writer_prompt_builders.py": "[Sweep5-D] recent events extraction failed",
        "main_a.py": "[Sweep5-D] writer cache invalidation failed during rollback",
    }

    for rel_path, marker in required.items():
        assert marker in _read(rel_path), rel_path
