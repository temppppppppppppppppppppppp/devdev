import re
from pathlib import Path

import modules.core.semantic_plot_guard as semantic_plot_guard_module
from modules.core.constants import ManuscriptLimits
from modules.core.feedback_system import FeedbackSystem
from modules.domain.agents.state_tracker import EpisodeState


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_preset_registry_get_field_value_uses_deepcopy_for_default_return():
    src = _read("modules/core/stage0/preset_registry.py")
    section = src[src.index("def _enforce_type") : src.index("def _parse_korean_number")]
    assert section.count("copy.deepcopy(field_def.default)") >= 2


def test_episode_state_to_dict_deepcopies_extra_fields():
    state = EpisodeState(
        ep_num=1,
        extra_fields={
            "stats": {"strength": 10, "agility": 8},
            "tags": ["alpha"],
        },
    )

    out = state.to_dict()
    out["stats"]["strength"] = 999
    out["tags"].append("beta")

    assert state.extra_fields["stats"]["strength"] == 10
    assert state.extra_fields["tags"] == ["alpha"]


def test_feedback_system_quantified_shortage_allocation_has_no_rounding_loss():
    fs = FeedbackSystem()
    content_length = ManuscriptLimits.WARNING_LENGTH - 1
    shortage = max(0, ManuscriptLimits.TARGET_LENGTH - content_length)

    quantified = fs.quantify_reject_feedback("", content_length, {})
    first = next((q for q in quantified if q.get("type") == "QUANTIFIED"), {})
    suggestion = str(first.get("suggestion", ""))

    values = [int(v) for v in re.findall(r"\+(\d+)", suggestion)]
    assert len(values) >= 3
    assert values[0] + values[1] + values[2] == shortage


def test_semantic_plot_guard_retry_counter_source_guards_present():
    src = _read("modules/core/semantic_plot_guard.py")
    assert "self._retry_count = 0" in src
    assert "self._max_retries = 1" in src
    assert "if self._retry_count > self._max_retries:" in src
    assert "if not self._client and self._retry_count <= self._max_retries:" in src


def test_semantic_plot_guard_does_not_retry_forever(monkeypatch):
    calls = {"count": 0}

    class _FakeGenAI:
        @staticmethod
        def Client(api_key):
            calls["count"] += 1
            raise RuntimeError("init fail")

    monkeypatch.setattr(semantic_plot_guard_module, "_GENAI_AVAILABLE", True)
    monkeypatch.setattr(semantic_plot_guard_module, "genai", _FakeGenAI)

    guard = semantic_plot_guard_module.SemanticPlotGuard(api_key="dummy")
    assert calls["count"] == 1

    guard._embed_text("a")
    assert calls["count"] == 2

    guard._embed_text("a")
    assert calls["count"] == 2
