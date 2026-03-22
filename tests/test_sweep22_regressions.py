"""[Sweep22] Regression tests for guards and logger consistency."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import modules.core.fact_ledger as fact_ledger_module
import modules.core.world_state as world_state_module
from modules.core.fact_ledger import FactLedger
from modules.core.world_state import WorldStateManager
from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder
from modules.domain.agents.state_extractor import StateExtractor


def test_state_extractor_handles_non_string_tactical_doc():
    extractor = StateExtractor(context=MagicMock(), client=MagicMock())
    extractor.extract_state = MagicMock(return_value={"entity_registry": extractor._empty_entity_registry()})

    arcs = [
        {
            "arc_no": 1,
            "joint_docs": {"physical_inventory": ""},
            "tactical_doc": ["grant-alpha", "grant-beta"],
        }
    ]

    result = extractor.extract_cumulative_state(arcs)
    assert result["cumulative"]["total_arcs_completed"] == 1
    assert isinstance(result["cumulative"]["all_grants_received"], list)


def test_chief_writer_context_npc_frequency_skips_non_dict_master_bible():
    class _ExplodingBible:
        def __bool__(self):
            return True

        def get(self, *_args, **_kwargs):
            raise AssertionError("get() should not be called for non-dict master_bible")

    host = MagicMock()
    host.context = SimpleNamespace(master_bible=_ExplodingBible())
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}

    builder = ChiefWriterContextBuilder(host)
    assert builder.context_packets._get_npc_frequency(ep_num=5, window=5) == {}


def test_world_state_uses_module_logger_for_missing_npc_name(monkeypatch):
    class _DB:
        def load_anchor(self, _name):
            return None

        def save_anchor(self, _name, _payload):
            return None

    def _raise_if_called(*_args, **_kwargs):
        raise AssertionError("root logging.warning should not be called")

    monkeypatch.setattr(world_state_module.logging, "warning", _raise_if_called)

    manager = WorldStateManager(_DB())
    manager.update_from_state_changes(ep_num=1, state_changes={"npc_deaths": [{}]})
    assert manager.get_state_dict()["last_updated_ep"] == 1


def test_fact_ledger_uses_module_logger_for_load_failure(monkeypatch):
    class _BrokenDB:
        def load_anchor(self, _name):
            raise RuntimeError("boom")

        def save_anchor(self, _name, _payload):
            return None

    def _raise_if_called(*_args, **_kwargs):
        raise AssertionError("root logging.warning should not be called")

    monkeypatch.setattr(fact_ledger_module.logging, "warning", _raise_if_called)

    ledger = FactLedger(_BrokenDB())
    assert ledger.last_updated_ep == 0
